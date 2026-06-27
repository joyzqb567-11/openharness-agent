"""OpenHarness Desktop Provider 设置合同。"""  # 新增代码+ProviderSettings：说明本模块负责桌面 provider 设置 payload；如果没有这行，维护者容易把它和真实模型运行时混在一起。

from __future__ import annotations  # 新增代码+ProviderSettings：启用延迟类型解析；如果没有这行，dataclass 和 helper 类型引用更脆弱。

import json  # 新增代码+ProviderSettings：读写 provider 设置 JSON；如果没有这行，自定义 provider 无法持久化。
import os  # 新增代码+CodexLoginCatalog：读取官方 Codex CLI 登录模式环境变量；如果没有这行，catalog 无法从启动配置切换到真实登录桥。
import re  # 新增代码+ProviderSettings：校验自定义 provider id；如果没有这行，非法 id 可能写入配置。
import threading  # 新增代码+ProviderSettings：保护 provider 设置并发写入；如果没有这行，快速切换模型可见性可能写坏配置。
import time  # 新增代码+ProviderSettings：生成损坏设置文件归档时间戳；如果没有这行，坏 JSON 备份文件名不稳定。
import urllib.error  # 新增代码+ProviderSettings：识别连接探针 HTTP/网络错误；如果没有这行，认证失败和网络失败无法分类。
import urllib.request  # 新增代码+ProviderSettings：执行标准库 HTTP /models 探针；如果没有这行，test-connection 无法真实验证 provider。
from dataclasses import asdict, dataclass  # 新增代码+ProviderSettings：定义 provider/auth/model 结构；如果没有这行，catalog 字段会散成难维护的 dict。
from pathlib import Path  # 新增代码+ProviderSettings：规范化 workspace 和 memory 路径；如果没有这行，Windows 路径容易出错。
from typing import Any  # 新增代码+ProviderSettings：标注未知 JSON 对象；如果没有这行，payload 清洗边界不清楚。

from learning_agent.app.gui_codex_auth_bridge import CodexAuthBridge  # 新增代码+CodexLoginCatalog：查询官方 Codex CLI 登录状态；如果没有这行，OpenAI provider 无法显示真实 ChatGPT 登录态。
from learning_agent.app.gui_provider_secret_store import DevJsonSecretStore, safe_secret_ref  # 新增代码+ProviderSettings：复用 secret store 和引用格式；如果没有这行，主配置可能保存 raw key。


PROVIDER_SETTINGS_SCHEMA_VERSION = 3  # 修改代码+OpenAIConnectCatalog：声明 OpenAI 三方法 catalog 的合同版本；如果没有这行，前端会按旧单 API key 合同解析新方法选择器。
BUILT_IN_PROVIDER_IDS = ("github-copilot", "openai", "google", "openrouter", "vercel")  # 新增代码+ProviderSettings：集中定义内置 provider id；如果没有这行，验证和 catalog 会各自维护列表。
RESERVED_PROVIDER_IDS = set(BUILT_IN_PROVIDER_IDS) | {"custom", "custom-provider-cta"}  # 新增代码+ProviderSettings：集中定义自定义 provider 禁用 id；如果没有这行，CTA 或内置 provider 可能被覆盖。
CUSTOM_PROVIDER_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")  # 新增代码+ProviderSettings：定义自定义 provider id 格式；如果没有这行，非法文件键可能进入配置。
OPENAI_COMPATIBLE_BASE_URLS = {"openai": "https://api.openai.com/v1", "openrouter": "https://openrouter.ai/api/v1", "vercel": "https://ai-gateway.vercel.sh/v1"}  # 新增代码+ProviderSettings：定义内置 OpenAI-compatible 探针 URL；如果没有这行，连接测试无法知道内置 provider 目标。
_PROVIDER_SETTINGS_LOCK = threading.Lock()  # 新增代码+ProviderSettings：锁住 provider 设置文件写入；如果没有这行，并发 mutation 可能互相覆盖。


class GuiProviderSettingsError(Exception):  # 新增代码+ProviderSettings：类段开始，承载 Provider 设置结构化错误；如果没有这个类，bridge 只能返回泛化 500。
    def __init__(self, status: int, code: str, message: str) -> None:  # 新增代码+ProviderSettings：函数段开始，初始化 HTTP 状态和错误码；如果没有这段，handler 无法构造稳定错误响应。
        super().__init__(message)  # 新增代码+ProviderSettings：把 message 交给 Exception；如果没有这行，调试时异常文本为空。
        self.status = status  # 新增代码+ProviderSettings：保存 HTTP 状态码；如果没有这行，bridge 无法返回 400/404。
        self.code = code  # 新增代码+ProviderSettings：保存机器可读错误码；如果没有这行，前端无法显示具体校验错误。
        self.message = message  # 新增代码+ProviderSettings：保存用户可读错误；如果没有这行，前端只能显示泛化失败。
    # 新增代码+ProviderSettings：函数段结束，GuiProviderSettingsError.__init__ 到此结束；如果没有边界说明，初学者不易看出错误字段范围。
# 新增代码+ProviderSettings：类段结束，GuiProviderSettingsError 到此结束；如果没有边界说明，初学者不易看出它只负责错误传递。


@dataclass  # 新增代码+ProviderSettings：自动生成 auth method 字典字段；如果没有这行，to_dict 需要手写重复代码。
class GuiAuthMethodInfo:  # 新增代码+ProviderSettings：类段开始，描述一个 Provider 认证方式；如果没有这个类，Copilot unsupported 和 API key 可用状态会散落。
    id: str  # 新增代码+ProviderSettings：认证方式 id；如果没有这行，前端无法提交选择的认证方式。
    label: str  # 新增代码+ProviderSettings：认证方式显示名；如果没有这行，设置页只能显示机器码。
    enabled: bool  # 新增代码+ProviderSettings：认证方式是否可用；如果没有这行，前端会误把 Copilot 当作可连接。
    status: str  # 新增代码+ProviderSettings：认证方式状态；如果没有这行，UI 无法显示 unsupported_v1 等原因。
    type: str  # 新增代码+OpenAIConnectCatalog：认证方式大类，api 表示密钥表单、oauth 表示授权流程；如果没有这行，前端无法决定渲染哪种连接界面。
    mode: str  # 新增代码+OpenAIConnectCatalog：认证方式交互模式，form 表示表单、auto 表示 attempt 轮询；如果没有这行，前端会把 OAuth 和 API key 混在同一个弹窗里。
    fields: list[str]  # 新增代码+ProviderSettings：认证表单字段代号；如果没有这行，connect dialog 无法知道要收集什么。
    help_text: str  # 新增代码+ProviderSettings：认证帮助文案；如果没有这行，用户不知道该提供哪种凭据。
    experimental: bool = False  # 新增代码+OpenAIConnectCatalog：标记该方法是否仍是实验路径；如果没有这行，mock OAuth 会被误解为稳定真实能力。
    # 新增代码+ProviderSettings：类段结束，GuiAuthMethodInfo 到此结束；如果没有边界说明，初学者不易看出字段范围。


@dataclass  # 新增代码+ProviderSettings：自动生成 model 字典字段；如果没有这行，模型列表会重复手写。
class GuiModelInfo:  # 新增代码+ProviderSettings：类段开始，描述设置页可展示模型；如果没有这个类，模型页无法稳定分组。
    id: str  # 新增代码+ProviderSettings：模型 id；如果没有这行，后端无法保存可见性。
    display_name: str  # 新增代码+ProviderSettings：模型显示名；如果没有这行，UI 只能显示技术 id。
    provider_id: str  # 新增代码+ProviderSettings：所属 provider id；如果没有这行，模型页无法分组。
    visible: bool = True  # 新增代码+ProviderSettings：模型是否显示；如果没有这行，用户无法隐藏不想用的模型。
    supports_tools: bool = False  # 新增代码+ProviderSettings：是否支持工具调用；如果没有这行，后续 runtime 选择无法提示能力。
    supports_vision: bool = False  # 新增代码+ProviderSettings：是否支持视觉输入；如果没有这行，后续模型能力 UI 没有基础。
    # 新增代码+ProviderSettings：类段结束，GuiModelInfo 到此结束；如果没有边界说明，初学者不易看出模型字段范围。


@dataclass  # 新增代码+ProviderSettings：自动生成 provider 字典字段；如果没有这行，catalog 构造会变成散乱 dict。
class GuiProviderInfo:  # 新增代码+ProviderSettings：类段开始，描述 Provider 设置页一行数据；如果没有这个类，前端契约字段容易漂移。
    id: str  # 新增代码+ProviderSettings：稳定配置 id；如果没有这行，mutation 不知道操作哪个 provider。
    display_name: str  # 新增代码+ProviderSettings：用户可见名称；如果没有这行，UI 只能显示机器 id。
    kind: str  # 新增代码+ProviderSettings：built_in/custom 分类；如果没有这行，UI 无法区分系统和自定义 provider。
    source: str  # 新增代码+ProviderSettings：none/config/env/custom 来源；如果没有这行，UI 无法显示来源 badge。
    connected: bool  # 新增代码+ProviderSettings：连接状态；如果没有这行，UI 无法切换连接/断开按钮。
    masked_key: str  # 新增代码+ProviderSettings：脱敏密钥摘要；如果没有这行，用户无法确认已保存凭据。
    auth_methods: list[dict[str, Any]]  # 新增代码+ProviderSettings：认证方式列表；如果没有这行，连接弹窗无法判断可用方式。
    description: str  # 新增代码+ProviderSettings：中文连接说明；如果没有这行，用户不知道 provider 用途。
    models: list[dict[str, Any]]  # 新增代码+ProviderSettings：模型列表；如果没有这行，模型页无法显示 provider 分组。
    # 新增代码+ProviderSettings：类段结束，GuiProviderInfo 到此结束；如果没有边界说明，初学者不易看出 provider 字段范围。


def provider_settings_dir(workspace: str | Path) -> Path:  # 新增代码+ProviderSettings：函数段开始，定位 Provider 设置目录；如果没有这段，多个 helper 会重复硬编码路径。
    return Path(workspace).expanduser().resolve() / "memory" / "gui_provider_settings"  # 新增代码+ProviderSettings：返回 workspace 内设置目录；如果没有这行，测试和真实配置会混用状态。
# 新增代码+ProviderSettings：函数段结束，provider_settings_dir 到此结束；如果没有边界说明，初学者不易看出它只负责路径。


def provider_settings_file(workspace: str | Path) -> Path:  # 新增代码+ProviderSettings：函数段开始，定位主 provider 设置 JSON；如果没有这段，读写路径会不一致。
    return provider_settings_dir(workspace) / "providers.json"  # 新增代码+ProviderSettings：返回 providers.json 路径；如果没有这行，配置无法稳定落盘。
# 新增代码+ProviderSettings：函数段结束，provider_settings_file 到此结束；如果没有边界说明，初学者不易看出它只负责文件路径。


def load_provider_settings(workspace: str | Path) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，安全读取 provider 设置；如果没有这段，catalog 无法合并用户配置。
    settings_path = provider_settings_file(workspace)  # 新增代码+ProviderSettings：定位设置文件；如果没有这行，读取不知道目标路径。
    if not settings_path.exists():  # 新增代码+ProviderSettings：处理首次使用无配置；如果没有这行，首次打开设置页会报错。
        return {"auth": {}, "custom_providers": {}, "model_visibility": {}}  # 新增代码+ProviderSettings：返回空配置骨架；如果没有这行，调用方要到处判空。
    try:  # 新增代码+ProviderSettings：保护 JSON 解析；如果没有这行，坏文件会让 bridge 500。
        raw = json.loads(settings_path.read_text(encoding="utf-8"))  # 新增代码+ProviderSettings：读取并解析配置；如果没有这行，用户保存的状态无法恢复。
    except json.JSONDecodeError:  # 新增代码+ProviderSettings：捕获损坏 JSON；如果没有这行，坏配置不能自动隔离。
        corrupt_path = settings_path.with_name(f"providers.json.corrupt-{int(time.time())}")  # 新增代码+ProviderSettings：生成损坏文件备份名；如果没有这行，原始坏文件可能被静默覆盖。
        settings_path.replace(corrupt_path)  # 新增代码+ProviderSettings：移动损坏文件；如果没有这行，下次读取仍会失败。
        return {"auth": {}, "custom_providers": {}, "model_visibility": {}}  # 新增代码+ProviderSettings：损坏后使用空配置继续；如果没有这行，GUI 无法自恢复。
    if not isinstance(raw, dict):  # 新增代码+ProviderSettings：防御非对象 JSON；如果没有这行，数组或字符串会污染配置。
        return {"auth": {}, "custom_providers": {}, "model_visibility": {}}  # 新增代码+ProviderSettings：非对象视为空配置；如果没有这行，后续 get() 可能失败。
    return {"auth": raw.get("auth", {}) if isinstance(raw.get("auth", {}), dict) else {}, "custom_providers": raw.get("custom_providers", {}) if isinstance(raw.get("custom_providers", {}), dict) else {}, "model_visibility": raw.get("model_visibility", {}) if isinstance(raw.get("model_visibility", {}), dict) else {}}  # 新增代码+ProviderSettings：只保留已知配置区块；如果没有这行，未知字段可能进入 payload。
# 新增代码+ProviderSettings：函数段结束，load_provider_settings 到此结束；如果没有边界说明，初学者不易看出它会忽略未知字段。


def save_provider_settings(workspace: str | Path, data: dict[str, Any]) -> None:  # 新增代码+ProviderSettings：函数段开始，原子保存 provider 设置；如果没有这段，后续 mutation 无法安全落盘。
    settings_path = provider_settings_file(workspace)  # 新增代码+ProviderSettings：定位目标文件；如果没有这行，保存不知道写到哪里。
    with _PROVIDER_SETTINGS_LOCK:  # 新增代码+ProviderSettings：锁住写入全过程；如果没有这行，并发 mutation 会互相覆盖。
        settings_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+ProviderSettings：确保目录存在；如果没有这行，首次保存会失败。
        temp_path = settings_path.with_suffix(".tmp")  # 新增代码+ProviderSettings：准备临时文件；如果没有这行，无法先完整写入再替换。
        temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")  # 新增代码+ProviderSettings：写入格式化 JSON；如果没有这行，设置不会持久化。
        temp_path.replace(settings_path)  # 新增代码+ProviderSettings：原子替换目标文件；如果没有这行，崩溃时可能留下半写文件。
# 新增代码+ProviderSettings：函数段结束，save_provider_settings 到此结束；如果没有边界说明，初学者不易看出它只负责安全写配置。


def _api_key_auth_method(enabled: bool = True, status: str = "available") -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，生成 API 密钥认证方法；如果没有这段，多个 provider 会重复手写 auth_methods。
    return asdict(GuiAuthMethodInfo(id="api-key", label="API 密钥", enabled=enabled, status=status, type="api", mode="form", fields=["secret"], help_text="使用 API 密钥连接", experimental=False))  # 修改代码+OpenAIConnectCatalog：返回稳定 API key 表单方法且不含 api_key 字段名；如果没有这行，renderer 响应会长期持有敏感字段语义。
# 新增代码+ProviderSettings：函数段结束，_api_key_auth_method 到此结束；如果没有边界说明，初学者不易看出它只生成认证元数据。


def _unsupported_auth_method(method_id: str, label: str, help_text: str) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，生成 V1 未支持认证方法；如果没有这段，Copilot 可能被误渲染成可连接。
    return asdict(GuiAuthMethodInfo(id=method_id, label=label, enabled=False, status="unsupported_v1", type="oauth", mode="auto", fields=[], help_text=help_text, experimental=True))  # 修改代码+OpenAIConnectCatalog：返回 disabled OAuth method 并标记实验/未支持；如果没有这行，前端无法显示暂未支持。
# 新增代码+ProviderSettings：函数段结束，_unsupported_auth_method 到此结束；如果没有边界说明，初学者不易看出它只负责 unsupported 元数据。


def _openai_oauth_auth_method(method_id: str, label: str, help_text: str, status: str = "mock_available", experimental: bool = True) -> dict[str, Any]:  # 修改代码+CodexLoginCatalog：函数段开始，生成 OpenAI ChatGPT OAuth 方法并允许官方 Codex 状态覆盖；如果没有这段，browser/headless 会和 API key 混成同一种表单。
    return asdict(GuiAuthMethodInfo(id=method_id, label=label, enabled=True, status=status, type="oauth", mode="auto", fields=[], help_text=help_text, experimental=experimental))  # 修改代码+CodexLoginCatalog：返回 OAuth 方法并保留状态/实验标记；如果没有这行，前端无法区分 mock OAuth 和官方 Codex 登录。
# 新增代码+OpenAIConnectCatalog：函数段结束，_openai_oauth_auth_method 到此结束；如果没有边界说明，初学者不易看出它只负责 OpenAI OAuth 元数据。


def _openai_auth_mode() -> str:  # 新增代码+CodexLoginCatalog：函数段开始，读取 OpenAI provider 登录模式；如果没有这段，catalog/auth-attempt 会各自解析环境变量。
    return str(os.environ.get("OPENHARNESS_OPENAI_AUTH_MODE", "mock") or "mock").strip().lower()  # 新增代码+CodexLoginCatalog：返回小写模式并默认 mock；如果没有这行，未设置环境变量时官方登录可能误开启。
# 新增代码+CodexLoginCatalog：函数段结束，_openai_auth_mode 到此结束；如果没有边界说明，初学者不易看出它只负责读取模式。


def _openai_auth_methods(auth_mode: str | None = None) -> list[dict[str, Any]]:  # 修改代码+CodexLoginCatalog：函数段开始，集中声明 OpenAI 三种连接方式并支持官方 Codex 模式；如果没有这段，OpenAI catalog 顺序会在多处重复维护。
    clean_auth_mode = (auth_mode or _openai_auth_mode()).strip().lower()  # 新增代码+CodexLoginCatalog：规范化认证模式；如果没有这行，大小写或空白会让 codex_cli 判断失效。
    if clean_auth_mode == "codex_cli":  # 修改代码+DirectOAuthCatalog：官方 Codex CLI 模式使用 Codex 登录桥文案；如果没有这行代码，direct OAuth 和 codex_cli 会混成同一种状态。
        browser_help = "使用官方 Codex CLI 打开 ChatGPT OAuth 登录；OpenHarness 不读取 Codex token。"  # 修改代码+DirectOAuthCatalog：说明官方路径不读取 token；如果没有这行代码，用户会误以为 OpenHarness 直接保存 Codex 凭据。
        browser_status = "available"  # 修改代码+DirectOAuthCatalog：官方模式下 browser 方法可启动；如果没有这行代码，前端会继续标成 mock。
        browser_experimental = False  # 修改代码+DirectOAuthCatalog：Codex CLI 桥是当前稳定推荐路径；如果没有这行代码，UI 会把稳定路径误标实验。
    elif clean_auth_mode == "direct_oauth":  # 新增代码+DirectOAuthCatalog：experimental direct OAuth 模式使用 OpenHarness 自有授权文案；如果没有这行代码，用户无法看出正在走真实 direct OAuth。
        browser_help = "使用 OpenHarness experimental direct OAuth 登录 ChatGPT；token 只保存到 OS 加密存储。"  # 新增代码+DirectOAuthCatalog：说明 direct OAuth 的安全边界；如果没有这行代码，用户不知道 token 是否会暴露给前端。
        browser_status = "experimental_available"  # 新增代码+DirectOAuthCatalog：把 browser 方法标成实验可用；如果没有这行代码，前端不能区分 direct OAuth 和 mock。
        browser_experimental = True  # 新增代码+DirectOAuthCatalog：明确 direct OAuth 仍是实验路径；如果没有这行代码，用户可能误以为它已经是稳定发布能力。
    else:  # 修改代码+DirectOAuthCatalog：默认仍走 mock 可视化验证路径；如果没有这行代码，未配置环境时 browser 文案会缺失。
        browser_help = "使用浏览器登录 ChatGPT Pro/Plus；稳定 V1 使用 mock auth-attempt 验证界面和状态机。"  # 修改代码+DirectOAuthCatalog：说明默认 mock 行为；如果没有这行代码，用户会误以为默认已真实联网。
        browser_status = "mock_available"  # 修改代码+DirectOAuthCatalog：默认 browser 方法是 mock；如果没有这行代码，前端状态会误导用户。
        browser_experimental = True  # 修改代码+DirectOAuthCatalog：默认 mock OAuth 属于实验演示；如果没有这行代码，UI 会误判成熟度。
    return [  # 新增代码+OpenAIConnectCatalog：开始返回 OpenCode 风格方法列表；如果没有这行，Python 无法组成有序 auth_methods。
        _openai_oauth_auth_method("chatgpt-browser", "ChatGPT Pro/Plus (browser)", browser_help, browser_status, browser_experimental),  # 修改代码+CodexLoginCatalog：声明 browser 登录方法并按模式切换文案；如果没有这行，用户看不到官方 Codex 登录入口。
        _openai_oauth_auth_method("chatgpt-headless", "ChatGPT Pro/Plus (headless)", "使用设备码登录 ChatGPT Pro/Plus；稳定 V1 使用 mock auth-attempt 验证界面和状态机。"),  # 新增代码+OpenAIConnectCatalog：声明 headless 登录方法；如果没有这行，用户看不到 OpenCode 同款设备码入口。
        _api_key_auth_method(),  # 新增代码+OpenAIConnectCatalog：保留稳定 API key 真实路径；如果没有这行，用户无法通过 OpenAI API key 真实连接后端。
    ]  # 新增代码+OpenAIConnectCatalog：结束 OpenAI 方法列表；如果没有这行，Python 列表语法不完整。
# 新增代码+OpenAIConnectCatalog：函数段结束，_openai_auth_methods 到此结束；如果没有边界说明，初学者不易看出它只负责 OpenAI 方法排序。


def _model(provider_id: str, model_id: str, display_name: str, visible: bool = True, tools: bool = False, vision: bool = False) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，生成模型字典；如果没有这段，模型字段容易不一致。
    return asdict(GuiModelInfo(id=model_id, display_name=display_name, provider_id=provider_id, visible=visible, supports_tools=tools, supports_vision=vision))  # 新增代码+ProviderSettings：返回稳定模型对象；如果没有这行，模型页无法统一渲染。
# 新增代码+ProviderSettings：函数段结束，_model 到此结束；如果没有边界说明，初学者不易看出它只负责模型对象。


def _visibility(settings: dict[str, Any], provider_id: str, model_id: str, default: bool = True) -> bool:  # 新增代码+ProviderSettings：函数段开始，读取模型可见性覆盖；如果没有这段，隐藏模型不会持久生效。
    visibility = settings.get("model_visibility", {})  # 新增代码+ProviderSettings：读取可见性区块；如果没有这行，无法应用用户选择。
    key = f"{provider_id}:{model_id}"  # 新增代码+ProviderSettings：生成可见性键；如果没有这行，不同 provider 同名模型会冲突。
    return bool(visibility.get(key, default)) if isinstance(visibility, dict) else default  # 新增代码+ProviderSettings：返回用户覆盖或默认值；如果没有这行，坏配置会拖垮 catalog。
# 新增代码+ProviderSettings：函数段结束，_visibility 到此结束；如果没有边界说明，初学者不易看出它只负责 model_visibility。


def _built_in_provider_catalog(settings: dict[str, Any], secret_store: DevJsonSecretStore) -> list[dict[str, Any]]:  # 新增代码+ProviderSettings：函数段开始，构造内置 provider catalog；如果没有这段，GET 路由没有核心数据。
    auth = settings.get("auth", {}) if isinstance(settings.get("auth", {}), dict) else {}  # 新增代码+ProviderSettings：读取认证配置；如果没有这行，connected 状态无法来自配置。
    openai_auth_mode = _openai_auth_mode()  # 新增代码+CodexLoginCatalog：读取 OpenAI 当前认证模式；如果没有这行，OpenAI 行无法切到官方 Codex CLI 登录状态。
    providers: list[GuiProviderInfo] = []  # 新增代码+ProviderSettings：准备 provider 列表；如果没有这行，后续无法累积 catalog。
    built_ins = [  # 新增代码+ProviderSettings：集中声明内置 provider 元数据；如果没有这段，display name 和模型会散落。
        ("github-copilot", "GitHub Copilot", "使用 Copilot 或 API 密钥连接", [_unsupported_auth_method("device-code", "设备码", "V1 只展示入口，不执行 Copilot 登录。")], []),  # 新增代码+ProviderSettings：声明 Copilot V1 暂未支持；如果没有这行，UI 会误导用户连接。
        ("openai", "OpenAI", "使用 ChatGPT Pro/Plus 或 API 密钥连接", _openai_auth_methods(openai_auth_mode), [_model("openai", "gpt-4.1", "GPT-4.1", _visibility(settings, "openai", "gpt-4.1", True), True, True)]),  # 修改代码+CodexLoginCatalog：声明 OpenAI provider 三种连接方式并按模式切换 browser 文案；如果没有这行，最常用 provider 仍只有 mock/API key 入口。
        ("google", "Google", "使用 Google 账号或 API 密钥连接", [_api_key_auth_method()], [_model("google", "gemini-2.5-pro", "Gemini 2.5 Pro", _visibility(settings, "google", "gemini-2.5-pro", True), True, True)]),  # 新增代码+ProviderSettings：声明 Google provider；如果没有这行，Gemini 实验入口缺失。
        ("openrouter", "OpenRouter", "使用 OpenRouter 账号或 API 密钥连接", [_api_key_auth_method()], [_model("openrouter", "openrouter/auto", "OpenRouter Auto", _visibility(settings, "openrouter", "openrouter/auto", True), True, True)]),  # 新增代码+ProviderSettings：声明 OpenRouter provider；如果没有这行，多模型路由入口缺失。
        ("vercel", "Vercel AI Gateway", "使用 Vercel 账号或 API 密钥连接", [_api_key_auth_method()], [_model("vercel", "vercel/auto", "Vercel Gateway Auto", _visibility(settings, "vercel", "vercel/auto", True), True, True)]),  # 新增代码+ProviderSettings：声明 Vercel provider；如果没有这行，AI Gateway 入口缺失。
    ]  # 新增代码+ProviderSettings：内置 provider 元数据结束；如果没有这行，Python 列表语法不完整。
    for provider_id, display_name, description, auth_methods, models in built_ins:  # 新增代码+ProviderSettings：遍历内置 provider；如果没有这行，元数据不会变成 payload。
        if provider_id == "openai" and openai_auth_mode == "codex_cli":  # 新增代码+CodexLoginCatalog：官方模式下 OpenAI 状态来自 Codex CLI；如果没有这行，catalog 仍会读取 mock/API key 配置。
            codex_status = CodexAuthBridge().login_status()  # 新增代码+CodexLoginCatalog：调用官方 status 命令查询登录态；如果没有这行，provider 无法知道 ChatGPT 是否已登录。
            codex_connected = bool(codex_status.available and codex_status.connected)  # 新增代码+CodexLoginCatalog：只有 CLI 可用且已登录才算 connected；如果没有这行，CLI 缺失或未登录会被误判。
            codex_source = "codex_cli_missing" if not codex_status.available else "codex_cli"  # 新增代码+CodexLoginCatalog：区分 CLI 缺失和官方模式未连接；如果没有这行，用户不知道是缺安装还是未登录。
            codex_masked = "Codex ChatGPT login" if codex_connected else ""  # 新增代码+CodexLoginCatalog：已连接时显示安全摘要；如果没有这行，用户无法识别连接来源。
            providers.append(GuiProviderInfo(id=provider_id, display_name=display_name, kind="built_in", source=codex_source, connected=codex_connected, masked_key=codex_masked, auth_methods=auth_methods, description=description, models=models))  # 新增代码+CodexLoginCatalog：加入官方 Codex provider payload；如果没有这行，设置页看不到真实登录状态。
            continue  # 新增代码+CodexLoginCatalog：官方模式不再读取 OpenHarness secret 或 mock 状态；如果没有这行，mock/API key 会覆盖 Codex CLI 事实。
        auth_record = auth.get(provider_id, {}) if isinstance(auth.get(provider_id, {}), dict) else {}  # 新增代码+ProviderSettings：读取当前 provider 认证记录；如果没有这行，connected 无法计算。
        auth_type = str(auth_record.get("type", ""))  # 新增代码+OpenAIAuthAttempt：读取认证记录类型；如果没有这行，mock OAuth 状态无法和 API key secret_ref 区分。
        if auth_type == "oauth_mock":  # 新增代码+OpenAIAuthAttempt：处理稳定 V1 的 mock OAuth 完成状态；如果没有这行，mock complete 后 catalog 仍显示未连接。
            providers.append(GuiProviderInfo(id=provider_id, display_name=display_name, kind="built_in", source="mock", connected=True, masked_key="Mock ChatGPT auth", auth_methods=auth_methods, description=description, models=models))  # 新增代码+OpenAIAuthAttempt：加入 mock 来源 provider payload；如果没有这行，UI 无法看到 mock 授权完成。
            continue  # 新增代码+OpenAIAuthAttempt：mock auth 不再读取 secret_ref；如果没有这行，后续 secret_store 逻辑会把 mock 状态当未连接。
        if auth_type == "oauth_direct":  # 新增代码+DirectOAuthCatalog：处理 experimental direct OAuth 连接状态；如果没有这行代码，真实 ChatGPT OAuth 登录后 catalog 仍显示未连接。
            token_ref = str(auth_record.get("token_ref", "")).strip()  # 新增代码+DirectOAuthCatalog：读取非敏感 token 引用；如果没有这行代码，无法判断 OS 加密 token 是否有关联记录。
            providers.append(GuiProviderInfo(id=provider_id, display_name=display_name, kind="built_in", source="direct_oauth_experimental", connected=bool(token_ref), masked_key="ChatGPT OAuth token" if token_ref else "", auth_methods=auth_methods, description=description, models=models))  # 新增代码+DirectOAuthCatalog：加入 direct OAuth 安全摘要且不暴露 token_ref；如果没有这行代码，renderer 可能拿不到正确来源或误看到内部引用。
            continue  # 新增代码+DirectOAuthCatalog：direct OAuth 不走 API key secret_store 逻辑；如果没有这行代码，catalog 会把 token_ref 当成 api key secret_ref。
        secret_ref = str(auth_record.get("secret_ref", ""))  # 新增代码+ProviderSettings：读取 secret_ref；如果没有这行，catalog 无法显示 masked_key。
        connected = bool(secret_ref and secret_store.get_secret(secret_ref))  # 新增代码+ProviderSettings：确认 secret 真实存在才算连接；如果没有这行，孤儿 secret_ref 会误显示已连接。
        source = "config" if connected else "none"  # 新增代码+ProviderSettings：设置来源 badge；如果没有这行，UI 无法区分未连接和配置连接。
        masked_key = secret_store.mask_secret(secret_ref) if connected else ""  # 新增代码+ProviderSettings：生成安全密钥摘要；如果没有这行，已连接状态没有可读提示。
        providers.append(GuiProviderInfo(id=provider_id, display_name=display_name, kind="built_in", source=source, connected=connected, masked_key=masked_key, auth_methods=auth_methods, description=description, models=models))  # 新增代码+ProviderSettings：加入 provider payload；如果没有这行，catalog 会缺少当前 provider。
    return [asdict(provider) for provider in providers]  # 新增代码+ProviderSettings：返回普通 dict 列表；如果没有这行，JSON 序列化会收到 dataclass 对象。
# 新增代码+ProviderSettings：函数段结束，_built_in_provider_catalog 到此结束；如果没有边界说明，初学者不易看出它只构造内置 provider。


def _custom_provider_catalog(settings: dict[str, Any], secret_store: DevJsonSecretStore) -> list[dict[str, Any]]:  # 新增代码+ProviderSettings：函数段开始，构造自定义 provider catalog；如果没有这段，保存的 OpenAI-compatible provider 不会显示。
    custom_providers = settings.get("custom_providers", {}) if isinstance(settings.get("custom_providers", {}), dict) else {}  # 新增代码+ProviderSettings：读取自定义 provider 区块；如果没有这行，catalog 无法加载用户 provider。
    result: list[dict[str, Any]] = []  # 新增代码+ProviderSettings：准备输出列表；如果没有这行，后续无法累积自定义 provider。
    for provider_id, record in sorted(custom_providers.items()):  # 新增代码+ProviderSettings：稳定遍历自定义 provider；如果没有这行，自定义列表顺序会抖动。
        if not isinstance(record, dict):  # 新增代码+ProviderSettings：跳过坏记录；如果没有这行，坏配置会拖垮整个 catalog。
            continue  # 新增代码+ProviderSettings：忽略坏 provider；如果没有这行，后续字段读取会报错。
        secret_ref = str(record.get("secret_ref", safe_secret_ref(str(provider_id), "api_key")))  # 新增代码+ProviderSettings：读取 secret_ref 或生成默认引用；如果没有这行，旧配置无法显示 masked_key。
        connected = bool(secret_store.get_secret(secret_ref))  # 新增代码+ProviderSettings：确认 secret 存在才算连接；如果没有这行，空引用会误显示已连接。
        raw_models = record.get("models", []) if isinstance(record.get("models", []), list) else []  # 新增代码+ProviderSettings：读取模型行；如果没有这行，自定义 provider 模型无法显示。
        models = [  # 新增代码+ProviderSettings：开始清洗自定义模型列表；如果没有这行，坏模型行可能进入前端。
            _model(str(provider_id), str(item.get("id", "")), str(item.get("display_name", item.get("name", item.get("id", "")))), bool(item.get("visible", True)), True, True)  # 新增代码+ProviderSettings：把单条模型转为稳定 payload；如果没有这行，自定义模型字段会不一致。
            for item in raw_models  # 新增代码+ProviderSettings：遍历用户配置里的模型行；如果没有这行，自定义 provider 没有模型可显示。
            if isinstance(item, dict) and str(item.get("id", "")).strip()  # 新增代码+ProviderSettings：只保留带 id 的对象行；如果没有这行，空行或坏类型会污染模型列表。
        ]  # 新增代码+ProviderSettings：结束自定义模型清洗；如果没有这行，Python 列表语法不完整。
        result.append(asdict(GuiProviderInfo(id=str(provider_id), display_name=str(record.get("display_name", record.get("name", provider_id))), kind="custom", source="custom", connected=connected, masked_key=secret_store.mask_secret(secret_ref) if connected else "", auth_methods=[_api_key_auth_method()], description="通过基础 URL 添加的 OpenAI 兼容提供商", models=models)))  # 新增代码+ProviderSettings：加入自定义 provider payload；如果没有这行，保存后的 provider 不会显示。
    return result  # 新增代码+ProviderSettings：返回自定义 provider 列表；如果没有这行，catalog 只会有内置 provider。
# 新增代码+ProviderSettings：函数段结束，_custom_provider_catalog 到此结束；如果没有边界说明，初学者不易看出它只负责自定义 provider。


def redact_provider_payload(value: Any) -> Any:  # 新增代码+ProviderSettings：函数段开始，递归移除 provider payload 中的危险字段；如果没有这段，后端 bug 可能把 raw key 送进 renderer。
    unsafe_keys = {"api_key", "apikey", "authorization", "bearer", "headers", "header_value"}  # 新增代码+ProviderSettings：定义禁止返回字段；如果没有这行，递归清洗没有判断依据。
    if isinstance(value, dict):  # 新增代码+ProviderSettings：处理对象；如果没有这行，嵌套 dict 无法清洗。
        return {key: redact_provider_payload(item) for key, item in value.items() if str(key).lower() not in unsafe_keys}  # 新增代码+ProviderSettings：过滤危险键并递归；如果没有这行，raw secret 字段可能漏出。
    if isinstance(value, list):  # 新增代码+ProviderSettings：处理列表；如果没有这行，嵌套数组无法清洗。
        return [redact_provider_payload(item) for item in value]  # 新增代码+ProviderSettings：递归清洗列表元素；如果没有这行，列表里的危险对象会漏出。
    return value  # 新增代码+ProviderSettings：普通值原样返回；如果没有这行，字符串和布尔值会丢失。
# 新增代码+ProviderSettings：函数段结束，redact_provider_payload 到此结束；如果没有边界说明，初学者不易看出它是最后安全网。


def build_provider_settings_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，生成 Provider Settings V1 catalog；如果没有这段，bridge GET 路由没有稳定响应。
    settings = load_provider_settings(workspace)  # 新增代码+ProviderSettings：读取用户 provider 设置；如果没有这行，连接和自定义 provider 状态无法合并。
    secret_store = DevJsonSecretStore(workspace)  # 新增代码+ProviderSettings：创建后端密钥存储；如果没有这行，catalog 无法判断 connected 或 masked_key。
    providers = _built_in_provider_catalog(settings, secret_store) + _custom_provider_catalog(settings, secret_store)  # 新增代码+ProviderSettings：合并内置和自定义 provider；如果没有这行，catalog 不完整。
    payload = {"ok": True, "schema_version": PROVIDER_SETTINGS_SCHEMA_VERSION, "secret_store": secret_store.info(), "providers": providers, "custom_provider_cta": {"id": "custom-provider-cta", "display_name": "自定义提供商", "description": "通过基础 URL 添加与 OpenAI 兼容的提供商。"}, "default_provider_id": str(settings.get("default_provider_id", "")), "default_model_id": str(settings.get("default_model_id", ""))}  # 新增代码+ProviderSettings：构造完整 catalog payload；如果没有这行，前端缺少 provider、CTA 和默认选择。
    return redact_provider_payload(payload)  # 新增代码+ProviderSettings：返回前做安全清洗；如果没有这行，未来字段变更可能意外泄密。
# 新增代码+ProviderSettings：函数段结束，build_provider_settings_payload 到此结束；如果没有边界说明，初学者不易看出它是 GET catalog 入口。


def validate_provider_id(value: Any, settings: dict[str, Any]) -> str:  # 新增代码+ProviderSettings：函数段开始，校验 mutation 指向的 provider；如果没有这段，写入接口可能操作不存在 provider。
    provider_id = str(value or "").strip()  # 新增代码+ProviderSettings：把未知输入收敛成 provider id；如果没有这行，None 或数字会造成后续异常。
    custom_providers = settings.get("custom_providers", {}) if isinstance(settings.get("custom_providers", {}), dict) else {}  # 新增代码+ProviderSettings：读取已保存自定义 provider；如果没有这行，自定义 provider 无法被 mutation 找到。
    if provider_id in BUILT_IN_PROVIDER_IDS or provider_id in custom_providers:  # 新增代码+ProviderSettings：允许内置或已保存自定义 provider；如果没有这行，合法 mutation 会被拒绝。
        return provider_id  # 新增代码+ProviderSettings：返回规范 id；如果没有这行，调用方拿不到可写入键。
    raise GuiProviderSettingsError(400, "invalid_provider_id", "Provider ID 不存在。")  # 新增代码+ProviderSettings：返回非法 provider 错误；如果没有这行，未知 id 可能创建脏配置。
# 新增代码+ProviderSettings：函数段结束，validate_provider_id 到此结束；如果没有边界说明，初学者不易看出它验证 mutation 目标。


def validate_custom_provider_id(value: Any) -> str:  # 新增代码+ProviderSettings：函数段开始，校验自定义 provider id；如果没有这段，保留 id 或坏字符可能写入配置。
    provider_id = str(value or "").strip()  # 新增代码+ProviderSettings：清理输入 id；如果没有这行，隐藏空白会生成难删除 provider。
    if provider_id in RESERVED_PROVIDER_IDS:  # 新增代码+ProviderSettings：拒绝内置和虚拟 CTA id；如果没有这行，自定义 provider 可能覆盖系统入口。
        raise GuiProviderSettingsError(400, "reserved_provider_id", "Provider ID 已被系统保留。")  # 新增代码+ProviderSettings：返回保留 id 错误；如果没有这行，前端无法显示准确提示。
    if not CUSTOM_PROVIDER_ID_PATTERN.match(provider_id):  # 新增代码+ProviderSettings：检查 id 格式；如果没有这行，路径危险字符可能进入配置。
        raise GuiProviderSettingsError(400, "invalid_provider_id", "Provider ID 只能使用小写字母、数字和短横线。")  # 新增代码+ProviderSettings：返回格式错误；如果没有这行，前端无法区分格式和保留冲突。
    return provider_id  # 新增代码+ProviderSettings：返回合法 id；如果没有这行，调用方无法写入 custom_providers。
# 新增代码+ProviderSettings：函数段结束，validate_custom_provider_id 到此结束；如果没有边界说明，初学者不易看出它只验证自定义 id。


def validate_base_url(value: Any) -> str:  # 新增代码+ProviderSettings：函数段开始，校验 OpenAI-compatible base URL；如果没有这段，危险或无效协议可能进入连接探针。
    base_url = str(value or "").strip().rstrip("/")  # 新增代码+ProviderSettings：清理 URL 并去掉末尾斜杠；如果没有这行，同一个 URL 会生成不同配置。
    if not (base_url.startswith("http://") or base_url.startswith("https://")):  # 新增代码+ProviderSettings：只允许 HTTP/HTTPS；如果没有这行，file/ftp 等协议可能被请求。
        raise GuiProviderSettingsError(400, "invalid_base_url", "Base URL 必须以 http:// 或 https:// 开头。")  # 新增代码+ProviderSettings：返回 URL 错误；如果没有这行，前端无法显示准确提示。
    return base_url  # 新增代码+ProviderSettings：返回规范 URL；如果没有这行，调用方无法保存清理后的配置。
# 新增代码+ProviderSettings：函数段结束，validate_base_url 到此结束；如果没有边界说明，初学者不易看出它只负责 URL 校验。


def sanitize_model_rows(rows: Any) -> list[dict[str, Any]]:  # 新增代码+ProviderSettings：函数段开始，清洗自定义 provider 模型行；如果没有这段，空模型或坏类型会进入前端。
    raw_rows = rows if isinstance(rows, list) else []  # 新增代码+ProviderSettings：只接受数组模型行；如果没有这行，字符串或对象会让遍历语义不清。
    models: list[dict[str, Any]] = []  # 新增代码+ProviderSettings：准备清洗后模型列表；如果没有这行，后续无法累积结果。
    for row in raw_rows:  # 新增代码+ProviderSettings：遍历每一行模型；如果没有这行，用户填写的模型不会保存。
        if not isinstance(row, dict):  # 新增代码+ProviderSettings：跳过非对象行；如果没有这行，坏类型会导致 get() 异常。
            continue  # 新增代码+ProviderSettings：忽略坏行；如果没有这行，后续字段读取会失败。
        model_id = str(row.get("id", "")).strip()  # 新增代码+ProviderSettings：读取模型 id；如果没有这行，保存键不稳定。
        display_name = str(row.get("display_name", row.get("name", ""))).strip()  # 新增代码+ProviderSettings：读取模型显示名；如果没有这行，UI 只能显示空文本。
        if model_id and display_name:  # 新增代码+ProviderSettings：只保存完整模型行；如果没有这行，空行会进入模型页。
            models.append({"id": model_id, "display_name": display_name, "visible": bool(row.get("visible", True))})  # 新增代码+ProviderSettings：保存稳定模型字段；如果没有这行，自定义模型不会持久化。
    if not models:  # 新增代码+ProviderSettings：要求至少一个模型；如果没有这行，自定义 provider 会保存成不可用空壳。
        raise GuiProviderSettingsError(400, "missing_model", "至少填写一个模型。")  # 新增代码+ProviderSettings：返回缺模型错误；如果没有这行，前端无法提示用户补模型。
    return models  # 新增代码+ProviderSettings：返回清洗后模型；如果没有这行，调用方拿不到结果。
# 新增代码+ProviderSettings：函数段结束，sanitize_model_rows 到此结束；如果没有边界说明，初学者不易看出它只清洗模型行。


def sanitize_header_rows(rows: Any, secret_store: DevJsonSecretStore, provider_id: str) -> str:  # 新增代码+ProviderSettings：函数段开始，把自定义 header 值存入 secret store；如果没有这段，header 值可能明文落进主配置。
    raw_rows = rows if isinstance(rows, list) else []  # 新增代码+ProviderSettings：只接受数组 header 行；如果没有这行，非数组输入会导致遍历异常。
    headers: dict[str, str] = {}  # 新增代码+ProviderSettings：准备 header 字典；如果没有这行，后续无法累积清洗结果。
    for row in raw_rows:  # 新增代码+ProviderSettings：遍历用户填写的 header 行；如果没有这行，header 配置不会保存。
        if not isinstance(row, dict):  # 新增代码+ProviderSettings：跳过非对象行；如果没有这行，坏类型会导致 get() 异常。
            continue  # 新增代码+ProviderSettings：忽略坏行；如果没有这行，后续字段读取会失败。
        key = str(row.get("key", "")).strip()  # 新增代码+ProviderSettings：读取 header key；如果没有这行，空白 key 会进入配置。
        value = str(row.get("value", ""))  # 新增代码+ProviderSettings：读取 header value；如果没有这行，header 值无法保存。
        if key and "\n" not in key and "\r" not in key and value:  # 新增代码+ProviderSettings：只接受非空且无换行 key；如果没有这行，恶意 header key 可能污染请求。
            headers[key] = value  # 新增代码+ProviderSettings：保存清洗后 header；如果没有这行，合法 header 会丢失。
    if not headers:  # 新增代码+ProviderSettings：处理没有 header 的常见场景；如果没有这行，会创建无意义 secret_ref。
        return ""  # 新增代码+ProviderSettings：无 header 时返回空引用；如果没有这行，主配置会误以为有 header secret。
    headers_ref = safe_secret_ref(provider_id, "headers")  # 新增代码+ProviderSettings：生成 header secret 引用；如果没有这行，主配置只能保存明文 header。
    secret_store.set_secret(headers_ref, json.dumps(headers, ensure_ascii=False, sort_keys=True))  # 新增代码+ProviderSettings：把 header 值作为 secret 写入开发 store；如果没有这行，连接探针无法读取 header。
    return headers_ref  # 新增代码+ProviderSettings：返回 header secret 引用；如果没有这行，主配置无法指向 header secret。
# 新增代码+ProviderSettings：函数段结束，sanitize_header_rows 到此结束；如果没有边界说明，初学者不易看出它会写 secret store。


def _api_key_from_fields(fields: Any) -> str:  # 新增代码+ProviderSettings：函数段开始，从提交字段读取 API key；如果没有这段，auth/custom 两个入口会重复字段兼容逻辑。
    safe_fields = fields if isinstance(fields, dict) else {}  # 新增代码+ProviderSettings：只接受对象字段；如果没有这行，字符串字段会导致 get() 异常。
    api_key = str(safe_fields.get("api_key", safe_fields.get("secret", ""))).strip()  # 新增代码+ProviderSettings：兼容 api_key 请求和 secret 请求；如果没有这行，前端表单提交无法保存。
    if not api_key:  # 新增代码+ProviderSettings：要求密钥非空；如果没有这行，空密钥会被误标记为已连接。
        raise GuiProviderSettingsError(400, "missing_secret", "请填写 API 密钥。")  # 新增代码+ProviderSettings：返回缺密钥错误；如果没有这行，前端无法显示准确提示。
    return api_key  # 新增代码+ProviderSettings：返回密钥给后端 secret store；如果没有这行，调用方无法写入 secret。
# 新增代码+ProviderSettings：函数段结束，_api_key_from_fields 到此结束；如果没有边界说明，初学者不易看出它只在后端内部处理 raw secret。


def set_provider_auth(workspace: str | Path, provider_id: Any, auth_method_id: Any, fields: Any) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，保存内置或自定义 provider 认证；如果没有这段，连接按钮没有后端效果。
    settings = load_provider_settings(workspace)  # 新增代码+ProviderSettings：读取当前设置；如果没有这行，新认证会覆盖已有配置。
    clean_provider_id = validate_provider_id(provider_id, settings)  # 新增代码+ProviderSettings：校验目标 provider；如果没有这行，未知 provider 会写进配置。
    clean_auth_method = str(auth_method_id or "").strip().replace("-", "_")  # 新增代码+ProviderSettings：规范化认证方式 id；如果没有这行，api-key/api_key 兼容会失败。
    if clean_provider_id == "github-copilot" or clean_auth_method != "api_key":  # 新增代码+ProviderSettings：拒绝 V1 不支持的认证方式；如果没有这行，Copilot 会被误连接。
        raise GuiProviderSettingsError(400, "unsupported_auth_method", "该提供商的认证方式 V1 暂未支持。")  # 新增代码+ProviderSettings：返回未支持错误；如果没有这行，前端无法显示暂未支持。
    api_key = _api_key_from_fields(fields)  # 新增代码+ProviderSettings：读取 raw API key；如果没有这行，secret store 没有可写入值。
    secret_store = DevJsonSecretStore(workspace)  # 新增代码+ProviderSettings：创建密钥存储；如果没有这行，raw key 可能被写入主配置。
    secret_ref = secret_store.set_secret(safe_secret_ref(clean_provider_id, "api_key"), api_key)  # 新增代码+ProviderSettings：把 raw key 写入 secret store 并取得引用；如果没有这行，后续连接探针无法认证。
    auth = settings.setdefault("auth", {})  # 新增代码+ProviderSettings：获取 auth 区块；如果没有这行，主配置无法记录连接状态。
    auth[clean_provider_id] = {"type": "api_key", "secret_ref": secret_ref, "updated_at": time.time()}  # 新增代码+ProviderSettings：主配置只保存 secret_ref；如果没有这行，重启后无法识别已连接。
    save_provider_settings(workspace, settings)  # 新增代码+ProviderSettings：保存主配置；如果没有这行，连接状态只在内存里存在。
    return build_provider_settings_payload(workspace)  # 新增代码+ProviderSettings：返回脱敏 catalog；如果没有这行，前端无法刷新连接状态。
# 新增代码+ProviderSettings：函数段结束，set_provider_auth 到此结束；如果没有边界说明，初学者不易看出它保存 auth 并返回 catalog。


def disconnect_provider(workspace: str | Path, provider_id: Any) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，断开 provider 并清理密钥；如果没有这段，断开按钮不会真正删除 secret。
    settings = load_provider_settings(workspace)  # 新增代码+ProviderSettings：读取当前设置；如果没有这行，无法找到 secret_ref。
    clean_provider_id = validate_provider_id(provider_id, settings)  # 新增代码+ProviderSettings：校验目标 provider；如果没有这行，未知 provider 删除可能污染配置。
    secret_store = DevJsonSecretStore(workspace)  # 新增代码+ProviderSettings：创建密钥存储；如果没有这行，无法删除 raw secret。
    auth = settings.setdefault("auth", {})  # 新增代码+ProviderSettings：读取 auth 区块；如果没有这行，删除状态无法写回。
    auth_record = auth.pop(clean_provider_id, {}) if isinstance(auth, dict) else {}  # 新增代码+ProviderSettings：移除认证记录；如果没有这行，catalog 仍会显示 connected。
    secret_ref = str(auth_record.get("secret_ref", safe_secret_ref(clean_provider_id, "api_key"))) if isinstance(auth_record, dict) else safe_secret_ref(clean_provider_id, "api_key")  # 新增代码+ProviderSettings：读取待删除 secret_ref；如果没有这行，secret store 会留下旧 key。
    secret_store.delete_secret(secret_ref)  # 新增代码+ProviderSettings：删除 provider API key；如果没有这行，断开后 raw key 仍在磁盘。
    custom_providers = settings.get("custom_providers", {}) if isinstance(settings.get("custom_providers", {}), dict) else {}  # 新增代码+ProviderSettings：读取自定义 provider 区块；如果没有这行，custom provider 自带 secret_ref 无法清理。
    if clean_provider_id in custom_providers and isinstance(custom_providers[clean_provider_id], dict):  # 新增代码+ProviderSettings：处理自定义 provider 记录；如果没有这行，自定义密钥可能残留。
        custom_secret_ref = str(custom_providers[clean_provider_id].get("secret_ref", safe_secret_ref(clean_provider_id, "api_key")))  # 新增代码+ProviderSettings：读取自定义 provider secret_ref；如果没有这行，无法清理自定义密钥。
        secret_store.delete_secret(custom_secret_ref)  # 新增代码+ProviderSettings：删除自定义 provider 密钥；如果没有这行，自定义断开后仍有 raw key。
    save_provider_settings(workspace, settings)  # 新增代码+ProviderSettings：保存断开后的主配置；如果没有这行，重启后仍显示连接。
    return build_provider_settings_payload(workspace)  # 新增代码+ProviderSettings：返回脱敏 catalog；如果没有这行，前端无法刷新断开状态。
# 新增代码+ProviderSettings：函数段结束，disconnect_provider 到此结束；如果没有边界说明，初学者不易看出它清理 secret 和 auth。


def save_custom_provider(workspace: str | Path, payload: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，保存自定义 OpenAI-compatible provider；如果没有这段，添加自定义提供商没有后端效果。
    settings = load_provider_settings(workspace)  # 新增代码+ProviderSettings：读取当前设置；如果没有这行，新 provider 会覆盖旧配置。
    provider_id = validate_custom_provider_id(payload.get("provider_id"))  # 新增代码+ProviderSettings：校验自定义 provider id；如果没有这行，保留 id 可能进入配置。
    display_name = str(payload.get("display_name", payload.get("name", provider_id))).strip() or provider_id  # 新增代码+ProviderSettings：读取显示名并兜底 id；如果没有这行，UI 可能显示空标题。
    base_url = validate_base_url(payload.get("base_url"))  # 新增代码+ProviderSettings：校验 base URL；如果没有这行，危险协议可能进入配置。
    models = sanitize_model_rows(payload.get("models", []))  # 新增代码+ProviderSettings：清洗模型行；如果没有这行，自定义 provider 可能没有可用模型。
    secret_store = DevJsonSecretStore(workspace)  # 新增代码+ProviderSettings：创建密钥存储；如果没有这行，raw key 和 header 值没有安全位置。
    api_key = _api_key_from_fields(payload.get("fields", {}))  # 新增代码+ProviderSettings：读取 API key；如果没有这行，自定义 provider 无法连接。
    secret_ref = secret_store.set_secret(safe_secret_ref(provider_id, "api_key"), api_key)  # 新增代码+ProviderSettings：把自定义 provider API key 写入 secret store；如果没有这行，主配置只能保存 raw key。
    headers_ref = sanitize_header_rows(payload.get("headers", []), secret_store, provider_id)  # 新增代码+ProviderSettings：把 header 值写入 secret store；如果没有这行，自定义 header 可能明文落盘。
    custom_providers = settings.setdefault("custom_providers", {})  # 新增代码+ProviderSettings：获取自定义 provider 区块；如果没有这行，配置无法保存多个 provider。
    custom_providers[provider_id] = {"display_name": display_name, "base_url": base_url, "secret_ref": secret_ref, "headers_ref": headers_ref, "models": models}  # 新增代码+ProviderSettings：主配置只保存引用和非敏感字段；如果没有这行，自定义 provider 重启后会丢失。
    auth = settings.setdefault("auth", {})  # 新增代码+ProviderSettings：获取 auth 区块；如果没有这行，custom provider connected 状态无法统一。
    auth[provider_id] = {"type": "api_key", "secret_ref": secret_ref, "updated_at": time.time()}  # 新增代码+ProviderSettings：记录自定义 provider auth 引用；如果没有这行，断开和 catalog 状态不一致。
    save_provider_settings(workspace, settings)  # 新增代码+ProviderSettings：保存主配置；如果没有这行，自定义 provider 只在内存存在。
    return build_provider_settings_payload(workspace)  # 新增代码+ProviderSettings：返回脱敏 catalog；如果没有这行，前端无法刷新新增 provider。
# 新增代码+ProviderSettings：函数段结束，save_custom_provider 到此结束；如果没有边界说明，初学者不易看出它保存配置和 secret。


def set_model_visibility(workspace: str | Path, provider_id: Any, model_id: Any, visible: Any) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，保存模型可见性；如果没有这段，模型页开关不会持久。
    settings = load_provider_settings(workspace)  # 新增代码+ProviderSettings：读取当前设置；如果没有这行，修改会覆盖其它配置。
    clean_provider_id = str(provider_id or "").strip()  # 新增代码+ProviderSettings：清理 provider id；如果没有这行，隐藏空白会生成不同键。
    clean_model_id = str(model_id or "").strip()  # 新增代码+ProviderSettings：清理 model id；如果没有这行，隐藏空白会生成不同键。
    if not clean_provider_id or not clean_model_id:  # 新增代码+ProviderSettings：要求 provider 和模型都存在；如果没有这行，空 key 会污染配置。
        raise GuiProviderSettingsError(400, "invalid_model_visibility", "Provider ID 和 Model ID 不能为空。")  # 新增代码+ProviderSettings：返回可见性输入错误；如果没有这行，前端无法显示明确失败。
    visibility = settings.setdefault("model_visibility", {})  # 新增代码+ProviderSettings：获取可见性区块；如果没有这行，无法写入开关状态。
    visibility[f"{clean_provider_id}:{clean_model_id}"] = bool(visible)  # 新增代码+ProviderSettings：保存模型可见性；如果没有这行，开关不会持久。
    save_provider_settings(workspace, settings)  # 新增代码+ProviderSettings：保存设置；如果没有这行，重启后可见性会丢失。
    return build_provider_settings_payload(workspace)  # 新增代码+ProviderSettings：返回更新后的脱敏 catalog；如果没有这行，前端无法刷新模型页。
# 新增代码+ProviderSettings：函数段结束，set_model_visibility 到此结束；如果没有边界说明，初学者不易看出它只改 model_visibility。


def build_probe_result(provider_id: str, status: str, message: str, models_count: int = 0) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，生成连接探针响应；如果没有这段，各失败分支会返回不同形状。
    return {"ok": status == "ok", "schema_version": PROVIDER_SETTINGS_SCHEMA_VERSION, "provider_id": provider_id, "status": status, "message": message, "models_count": int(models_count)}  # 新增代码+ProviderSettings：返回不含 secret/header 的结果；如果没有这行，前端无法稳定渲染测试结果。
# 新增代码+ProviderSettings：函数段结束，build_probe_result 到此结束；如果没有边界说明，初学者不易看出它只负责响应形状。


def _headers_from_ref(secret_store: DevJsonSecretStore, headers_ref: str) -> dict[str, str]:  # 新增代码+ProviderSettings：函数段开始，从 secret store 读取自定义 header；如果没有这段，探针无法使用用户配置 header。
    if not headers_ref:  # 新增代码+ProviderSettings：处理没有 header 的常见场景；如果没有这行，空引用会触发无意义读取。
        return {}  # 新增代码+ProviderSettings：无 header 返回空字典；如果没有这行，调用方要自己判空。
    try:  # 新增代码+ProviderSettings：保护 header JSON 解析；如果没有这行，坏 header secret 会让连接探针 500。
        raw = json.loads(secret_store.get_secret(headers_ref) or "{}")  # 新增代码+ProviderSettings：读取 header secret 并解析；如果没有这行，header 值无法进入探针请求。
    except json.JSONDecodeError:  # 新增代码+ProviderSettings：处理损坏 header secret；如果没有这行，坏 secret 会抛异常。
        return {}  # 新增代码+ProviderSettings：坏 header 时安全忽略；如果没有这行，用户无法打开设置页测试其它 provider。
    return {str(key): str(value) for key, value in raw.items()} if isinstance(raw, dict) else {}  # 新增代码+ProviderSettings：只返回字符串 header 字典；如果没有这行，坏类型会污染请求。
# 新增代码+ProviderSettings：函数段结束，_headers_from_ref 到此结束；如果没有边界说明，初学者不易看出它只在后端内部读取 header secret。


def probe_openai_compatible_models(base_url: str, api_key: str, headers: dict[str, str], timeout_seconds: float) -> tuple[str, str, int]:  # 新增代码+ProviderSettings：函数段开始，执行 OpenAI-compatible /models 探针；如果没有这段，test-connection 只能保存 key 不能验证可用性。
    probe_url = f"{base_url.rstrip('/')}/models"  # 新增代码+ProviderSettings：拼接 models endpoint；如果没有这行，探针不知道请求哪个路径。
    request_headers = dict(headers)  # 新增代码+ProviderSettings：复制自定义 header；如果没有这行，后续添加 Authorization 会修改调用方对象。
    request_headers["Authorization"] = f"Bearer {api_key}"  # 新增代码+ProviderSettings：加入认证 header；如果没有这行，需要鉴权的 /models 会失败。
    request = urllib.request.Request(probe_url, headers=request_headers)  # 新增代码+ProviderSettings：构造 GET 请求；如果没有这行，urllib 无法发送 headers。
    try:  # 新增代码+ProviderSettings：捕获 HTTP 和网络异常；如果没有这行，连接失败会变成 bridge 500。
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # 新增代码+ProviderSettings：发送 /models 请求；如果没有这行，探针不会真正验证 provider。
            raw_body = response.read().decode("utf-8")  # 新增代码+ProviderSettings：读取响应文本；如果没有这行，无法统计模型数量。
    except urllib.error.HTTPError as error:  # 新增代码+ProviderSettings：处理 HTTP 错误状态；如果没有这行，401/403 无法归类为认证失败。
        if error.code in {401, 403}:  # 新增代码+ProviderSettings：识别常见认证失败；如果没有这行，用户会看到误导性的网络失败。
            return "auth_failed", "认证失败", 0  # 新增代码+ProviderSettings：返回认证失败状态；如果没有这行，前端无法提示检查 key。
        return "network_failed", "网络不可达", 0  # 新增代码+ProviderSettings：其它 HTTP 错误收敛为网络/服务失败；如果没有这行，错误细节可能泄露。
    except (urllib.error.URLError, TimeoutError, OSError):  # 新增代码+ProviderSettings：处理连接拒绝、DNS、超时等错误；如果没有这行，网络失败会抛到 handler。
        return "network_failed", "网络不可达", 0  # 新增代码+ProviderSettings：返回稳定网络失败状态；如果没有这行，前端错误文案不稳定。
    try:  # 新增代码+ProviderSettings：保护 JSON 解析；如果没有这行，非 JSON 响应会导致 500。
        payload = json.loads(raw_body)  # 新增代码+ProviderSettings：解析 models 响应；如果没有这行，无法统计模型数量。
    except json.JSONDecodeError:  # 新增代码+ProviderSettings：处理非 JSON 响应；如果没有这行，错误 HTML 会让探针异常。
        return "invalid_config", "配置无效", 0  # 新增代码+ProviderSettings：返回配置无效；如果没有这行，前端无法区分网络通但格式错。
    models = payload.get("data", []) if isinstance(payload, dict) else []  # 新增代码+ProviderSettings：读取 OpenAI-compatible data 数组；如果没有这行，模型数量无法计算。
    models_count = len(models) if isinstance(models, list) else 0  # 新增代码+ProviderSettings：统计模型数量；如果没有这行，前端无法显示探针发现多少模型。
    return "ok", "连接测试通过", models_count  # 新增代码+ProviderSettings：返回成功状态；如果没有这行，HTTP 200 场景仍没有结果。
# 新增代码+ProviderSettings：函数段结束，probe_openai_compatible_models 到此结束；如果没有边界说明，初学者不易看出它只做 metadata probe。


def test_provider_connection(workspace: str | Path, provider_id: Any) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，测试 provider 连接但不切换真实 runtime；如果没有这段，设置页无法区分“已保存 key”和“连接可用”。
    settings = load_provider_settings(workspace)  # 新增代码+ProviderSettings：读取 provider 设置；如果没有这行，探针无法找到 base_url 和 secret_ref。
    clean_provider_id = validate_provider_id(provider_id, settings)  # 新增代码+ProviderSettings：校验目标 provider；如果没有这行，未知 id 可能触发错误路径请求。
    if clean_provider_id in {"github-copilot", "google"}:  # 新增代码+ProviderSettings：处理 V1 未支持探针的 provider；如果没有这行，Copilot/Google 可能被误当 OpenAI-compatible。
        return build_probe_result(clean_provider_id, "unsupported", "暂不支持测试", 0)  # 新增代码+ProviderSettings：返回未支持状态；如果没有这行，前端无法显示准确原因。
    secret_store = DevJsonSecretStore(workspace)  # 新增代码+ProviderSettings：创建 secret store；如果没有这行，探针无法读取 API key。
    auth = settings.get("auth", {}) if isinstance(settings.get("auth", {}), dict) else {}  # 新增代码+ProviderSettings：读取 auth 区块；如果没有这行，内置 provider 无法找到 secret_ref。
    custom_providers = settings.get("custom_providers", {}) if isinstance(settings.get("custom_providers", {}), dict) else {}  # 新增代码+ProviderSettings：读取自定义 provider 区块；如果没有这行，自定义 provider 无法找到 base_url。
    custom_record = custom_providers.get(clean_provider_id, {}) if isinstance(custom_providers.get(clean_provider_id, {}), dict) else {}  # 新增代码+ProviderSettings：读取目标自定义 provider 记录；如果没有这行，自定义和内置无法区分。
    base_url = str(custom_record.get("base_url", OPENAI_COMPATIBLE_BASE_URLS.get(clean_provider_id, ""))).strip()  # 新增代码+ProviderSettings：选择自定义或内置 base URL；如果没有这行，探针没有目标。
    if not base_url:  # 新增代码+ProviderSettings：处理缺 base URL；如果没有这行，空 URL 会让 urllib 抛不清楚异常。
        return build_probe_result(clean_provider_id, "invalid_config", "配置无效", 0)  # 新增代码+ProviderSettings：返回配置无效；如果没有这行，前端无法提示用户修配置。
    auth_record = auth.get(clean_provider_id, {}) if isinstance(auth.get(clean_provider_id, {}), dict) else {}  # 新增代码+ProviderSettings：读取 auth 记录；如果没有这行，secret_ref 无法定位。
    secret_ref = str(custom_record.get("secret_ref", auth_record.get("secret_ref", safe_secret_ref(clean_provider_id, "api_key"))))  # 新增代码+ProviderSettings：读取 secret_ref 并兼容默认引用；如果没有这行，旧配置无法测试连接。
    api_key = secret_store.get_secret(secret_ref)  # 新增代码+ProviderSettings：读取后端内部 API key；如果没有这行，探针无法认证。
    if not api_key:  # 新增代码+ProviderSettings：处理未连接状态；如果没有这行，缺密钥会误报网络失败。
        return build_probe_result(clean_provider_id, "missing_secret", "缺少密钥", 0)  # 新增代码+ProviderSettings：返回缺密钥状态；如果没有这行，用户不知道要先连接。
    headers = _headers_from_ref(secret_store, str(custom_record.get("headers_ref", "")))  # 新增代码+ProviderSettings：读取自定义 headers；如果没有这行，gateway 场景可能缺必需 header。
    status, message, models_count = probe_openai_compatible_models(base_url, api_key, headers, timeout_seconds=5.0)  # 新增代码+ProviderSettings：执行 OpenAI-compatible metadata probe；如果没有这行，test-connection 不会真正测试网络。
    return build_probe_result(clean_provider_id, status, message, models_count)  # 新增代码+ProviderSettings：返回安全探针结果；如果没有这行，bridge 无法响应前端。
# 新增代码+ProviderSettings：函数段结束，test_provider_connection 到此结束；如果没有边界说明，初学者不易看出它不改真实 runtime。
