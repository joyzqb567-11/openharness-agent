"""OpenHarness Desktop Provider 设置合同。"""  # 新增代码+ProviderSettings：说明本模块负责桌面 provider 设置 payload；如果没有这行，维护者容易把它和真实模型运行时混在一起。

from __future__ import annotations  # 新增代码+ProviderSettings：启用延迟类型解析；如果没有这行，dataclass 和 helper 类型引用更脆弱。

import json  # 新增代码+ProviderSettings：读写 provider 设置 JSON；如果没有这行，自定义 provider 无法持久化。
import os  # 新增代码+CodexLoginCatalog：读取官方 Codex CLI 登录模式环境变量；如果没有这行，catalog 无法从启动配置切换到真实登录桥。
import re  # 新增代码+ProviderSettings：校验自定义 provider id；如果没有这行，非法 id 可能写入配置。
import subprocess  # 新增代码+CodexOAuthModels：调用 codex debug models 读取真实可选模型；如果没有这行，OpenAI OAuth 模型列表只能继续硬编码。
import threading  # 新增代码+ProviderSettings：保护 provider 设置并发写入；如果没有这行，快速切换模型可见性可能写坏配置。
import time  # 新增代码+ProviderSettings：生成损坏设置文件归档时间戳；如果没有这行，坏 JSON 备份文件名不稳定。
import urllib.error  # 新增代码+ProviderSettings：识别连接探针 HTTP/网络错误；如果没有这行，认证失败和网络失败无法分类。
import urllib.request  # 新增代码+ProviderSettings：执行标准库 HTTP /models 探针；如果没有这行，test-connection 无法真实验证 provider。
from dataclasses import asdict, dataclass  # 新增代码+ProviderSettings：定义 provider/auth/model 结构；如果没有这行，catalog 字段会散成难维护的 dict。
from pathlib import Path  # 新增代码+ProviderSettings：规范化 workspace 和 memory 路径；如果没有这行，Windows 路径容易出错。
from typing import Any  # 新增代码+ProviderSettings：标注未知 JSON 对象；如果没有这行，payload 清洗边界不清楚。

from learning_agent.app.gui_codex_auth_bridge import CodexAuthBridge  # 新增代码+CodexLoginCatalog：查询官方 Codex CLI 登录状态；如果没有这行，OpenAI provider 无法显示真实 ChatGPT 登录态。
from learning_agent.app.gui_provider_oauth_token_store import default_oauth_token_store  # 新增代码+ProviderDisconnect：读取 direct OAuth token store；如果没有这行，断开 OpenAI 时只能删 catalog 引用而无法清理本机 token。
from learning_agent.app.gui_provider_secret_store import DevJsonSecretStore, safe_secret_ref  # 新增代码+ProviderSettings：复用 secret store 和引用格式；如果没有这行，主配置可能保存 raw key。


PROVIDER_SETTINGS_SCHEMA_VERSION = 4  # 修改代码+ModelFailureState：提升 Provider 设置合同版本；如果没有这行，前端无法知道模型最近失败字段已经进入 catalog。
BUILT_IN_PROVIDER_IDS = ("github-copilot", "openai", "google", "openrouter", "vercel")  # 新增代码+ProviderSettings：集中定义内置 provider id；如果没有这行，验证和 catalog 会各自维护列表。
RESERVED_PROVIDER_IDS = set(BUILT_IN_PROVIDER_IDS) | {"custom", "custom-provider-cta"}  # 新增代码+ProviderSettings：集中定义自定义 provider 禁用 id；如果没有这行，CTA 或内置 provider 可能被覆盖。
CUSTOM_PROVIDER_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")  # 新增代码+ProviderSettings：定义自定义 provider id 格式；如果没有这行，非法文件键可能进入配置。
OPENAI_COMPATIBLE_BASE_URLS = {"openai": "https://api.openai.com/v1", "openrouter": "https://openrouter.ai/api/v1", "vercel": "https://ai-gateway.vercel.sh/v1"}  # 新增代码+ProviderSettings：定义内置 OpenAI-compatible 探针 URL；如果没有这行，连接测试无法知道内置 provider 目标。
CODEX_CHATGPT_OAUTH_FALLBACK_MODELS = (("gpt-5.5", "GPT-5.5"), ("gpt-5.4", "GPT-5.4"), ("gpt-5.4-mini", "GPT-5.4-Mini"), ("gpt-5.3-codex-spark", "GPT-5.3-Codex-Spark"))  # 新增代码+CodexOAuthModels：提供 Codex ChatGPT OAuth 可见模型兜底列表；如果没有这行，codex debug models 临时失败时 GUI 会没有真实可选模型。
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
    recent_failure: dict[str, Any] | None = None  # 新增代码+ModelFailureState：保存最近一次模型级失败摘要；如果没有这行，底部模型菜单无法标记刚被 OAuth 拒绝的模型。
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


def _empty_provider_settings() -> dict[str, Any]:  # 新增代码+ModelFailureState：函数段开始，生成 provider 设置空骨架；如果没有这段，新增 model_failures 时多个兜底返回容易漏字段。
    return {"auth": {}, "custom_providers": {}, "model_visibility": {}, "model_failures": {}}  # 新增代码+ModelFailureState：返回所有已知配置区块；如果没有这行，首次启动或坏配置恢复时无法保存模型失败状态。
# 新增代码+ModelFailureState：函数段结束，_empty_provider_settings 到此结束；如果没有边界说明，初学者不易看出它只是配置骨架。


def load_provider_settings(workspace: str | Path) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，安全读取 provider 设置；如果没有这段，catalog 无法合并用户配置。
    settings_path = provider_settings_file(workspace)  # 新增代码+ProviderSettings：定位设置文件；如果没有这行，读取不知道目标路径。
    if not settings_path.exists():  # 新增代码+ProviderSettings：处理首次使用无配置；如果没有这行，首次打开设置页会报错。
        return _empty_provider_settings()  # 修改代码+ModelFailureState：返回包含模型失败区块的空配置；如果没有这行，首次启动无法记录不支持模型。
    try:  # 新增代码+ProviderSettings：保护 JSON 解析；如果没有这行，坏文件会让 bridge 500。
        raw = json.loads(settings_path.read_text(encoding="utf-8"))  # 新增代码+ProviderSettings：读取并解析配置；如果没有这行，用户保存的状态无法恢复。
    except json.JSONDecodeError:  # 新增代码+ProviderSettings：捕获损坏 JSON；如果没有这行，坏配置不能自动隔离。
        corrupt_path = settings_path.with_name(f"providers.json.corrupt-{int(time.time())}")  # 新增代码+ProviderSettings：生成损坏文件备份名；如果没有这行，原始坏文件可能被静默覆盖。
        settings_path.replace(corrupt_path)  # 新增代码+ProviderSettings：移动损坏文件；如果没有这行，下次读取仍会失败。
        return _empty_provider_settings()  # 修改代码+ModelFailureState：损坏后使用完整空配置继续；如果没有这行，恢复后的 catalog 会缺模型失败区块。
    if not isinstance(raw, dict):  # 新增代码+ProviderSettings：防御非对象 JSON；如果没有这行，数组或字符串会污染配置。
        return _empty_provider_settings()  # 修改代码+ModelFailureState：非对象视为完整空配置；如果没有这行，后续 get() 可能失败且失败状态会缺失。
    return {"auth": raw.get("auth", {}) if isinstance(raw.get("auth", {}), dict) else {}, "custom_providers": raw.get("custom_providers", {}) if isinstance(raw.get("custom_providers", {}), dict) else {}, "model_visibility": raw.get("model_visibility", {}) if isinstance(raw.get("model_visibility", {}), dict) else {}, "model_failures": raw.get("model_failures", {}) if isinstance(raw.get("model_failures", {}), dict) else {}}  # 修改代码+ModelFailureState：只保留已知配置区块并带上模型失败区块；如果没有这行，模型不支持记录不会被 catalog 读取。
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


def _model(provider_id: str, model_id: str, display_name: str, visible: bool = True, tools: bool = False, vision: bool = False, recent_failure: dict[str, Any] | None = None) -> dict[str, Any]:  # 修改代码+ModelFailureState：函数段开始，生成模型字典并携带最近失败摘要；如果没有这段，模型字段容易不一致且菜单无法提示不可用模型。
    return asdict(GuiModelInfo(id=model_id, display_name=display_name, provider_id=provider_id, visible=visible, supports_tools=tools, supports_vision=vision, recent_failure=recent_failure))  # 修改代码+ModelFailureState：返回稳定模型对象并包含最近失败；如果没有这行，模型页和 Composer 菜单无法统一渲染失败标记。
# 新增代码+ProviderSettings：函数段结束，_model 到此结束；如果没有边界说明，初学者不易看出它只负责模型对象。


def _visibility(settings: dict[str, Any], provider_id: str, model_id: str, default: bool = True) -> bool:  # 新增代码+ProviderSettings：函数段开始，读取模型可见性覆盖；如果没有这段，隐藏模型不会持久生效。
    visibility = settings.get("model_visibility", {})  # 新增代码+ProviderSettings：读取可见性区块；如果没有这行，无法应用用户选择。
    key = f"{provider_id}:{model_id}"  # 新增代码+ProviderSettings：生成可见性键；如果没有这行，不同 provider 同名模型会冲突。
    return bool(visibility.get(key, default)) if isinstance(visibility, dict) else default  # 新增代码+ProviderSettings：返回用户覆盖或默认值；如果没有这行，坏配置会拖垮 catalog。
# 新增代码+ProviderSettings：函数段结束，_visibility 到此结束；如果没有边界说明，初学者不易看出它只负责 model_visibility。


def _model_failure_key(provider_id: str, model_id: str) -> str:  # 新增代码+ModelFailureState：函数段开始，生成 provider+model 的失败记录键；如果没有这段，同名模型在不同 provider 下会互相污染。
    return f"{provider_id}:{model_id}"  # 新增代码+ModelFailureState：返回稳定复合键；如果没有这行，失败记录无法按 provider 和模型精确定位。
# 新增代码+ModelFailureState：函数段结束，_model_failure_key 到此结束；如果没有边界说明，初学者不易看出它只负责 key。


def _recent_model_failure(settings: dict[str, Any], provider_id: str, model_id: str) -> dict[str, Any] | None:  # 新增代码+ModelFailureState：函数段开始，读取某个模型最近失败摘要；如果没有这段，catalog 构造时要重复解析 model_failures。
    failures = settings.get("model_failures", {}) if isinstance(settings.get("model_failures", {}), dict) else {}  # 新增代码+ModelFailureState：安全读取失败区块；如果没有这行，坏配置会拖垮 provider catalog。
    failure = failures.get(_model_failure_key(provider_id, model_id), {}) if isinstance(failures, dict) else {}  # 新增代码+ModelFailureState：读取指定模型失败记录；如果没有这行，模型行拿不到最近失败。
    return dict(failure) if isinstance(failure, dict) and failure.get("error_kind") else None  # 新增代码+ModelFailureState：只返回带 error_kind 的有效记录；如果没有这行，空对象会被误显示成失败。
# 新增代码+ModelFailureState：函数段结束，_recent_model_failure 到此结束；如果没有边界说明，初学者不易看出它只读失败摘要。


def _clear_model_failures_in_settings(settings: dict[str, Any], provider_id: str | None = None) -> None:  # 新增代码+ModelFailureState：函数段开始，按 provider 清理模型失败记录；如果没有这段，重连后旧失败会继续吓唬用户。
    failures = settings.setdefault("model_failures", {})  # 新增代码+ModelFailureState：读取或创建失败区块；如果没有这行，清理时可能没有目标容器。
    if not isinstance(failures, dict):  # 新增代码+ModelFailureState：处理坏类型失败区块；如果没有这行，字符串/数组配置会导致删除异常。
        settings["model_failures"] = {}  # 新增代码+ModelFailureState：坏类型直接重置为空 dict；如果没有这行，后续 catalog 仍会反复碰到坏数据。
        return  # 新增代码+ModelFailureState：重置后直接返回；如果没有这行，下面会继续把坏对象当 dict 使用。
    if provider_id is None:  # 新增代码+ModelFailureState：处理全量清理场景；如果没有这行，catalog refresh 无法一次清掉所有失败。
        failures.clear()  # 新增代码+ModelFailureState：清空所有失败记录；如果没有这行，全量刷新后仍显示旧失败。
        return  # 新增代码+ModelFailureState：全量清理完成后返回；如果没有这行，会继续执行 provider 前缀逻辑。
    prefix = f"{provider_id}:"  # 新增代码+ModelFailureState：生成 provider 前缀；如果没有这行，无法只清理目标 provider 的失败。
    for failure_key in [key for key in failures if str(key).startswith(prefix)]:  # 新增代码+ModelFailureState：复制目标键列表再删除；如果没有这行，遍历时修改 dict 会报错。
        failures.pop(failure_key, None)  # 新增代码+ModelFailureState：删除单条失败记录；如果没有这行，目标 provider 的旧失败不会消失。
# 新增代码+ModelFailureState：函数段结束，_clear_model_failures_in_settings 到此结束；如果没有边界说明，初学者不易看出它只修改传入 settings。


def record_model_failure(workspace: str | Path, provider_id: Any, model_id: Any, error_kind: str, message: str) -> dict[str, Any]:  # 新增代码+ModelFailureState：函数段开始，记录真实模型调用中的模型级失败；如果没有这段，OAuth 拒绝模型后前端下拉框没有记忆。
    settings = load_provider_settings(workspace)  # 新增代码+ModelFailureState：读取当前 provider 设置；如果没有这行，写入会覆盖已有连接和可见性。
    clean_provider_id = str(provider_id or "").strip()  # 新增代码+ModelFailureState：清理 provider id；如果没有这行，空格会生成不同失败键。
    clean_model_id = str(model_id or "").strip()  # 新增代码+ModelFailureState：清理 model id；如果没有这行，空格会生成不同失败键。
    if not clean_provider_id or not clean_model_id:  # 新增代码+ModelFailureState：要求 provider 和 model 都存在；如果没有这行，空键会污染配置。
        return build_provider_settings_payload(workspace)  # 新增代码+ModelFailureState：缺上下文时只返回当前 catalog；如果没有这行，异常会遮蔽原始模型错误。
    failures = settings.setdefault("model_failures", {})  # 新增代码+ModelFailureState：获取失败区块；如果没有这行，无法写入最近失败。
    if not isinstance(failures, dict):  # 新增代码+ModelFailureState：处理坏类型失败区块；如果没有这行，旧坏配置会导致写入异常。
        failures = {}  # 新增代码+ModelFailureState：用新的 dict 替换坏数据；如果没有这行，后续赋值无法安全进行。
        settings["model_failures"] = failures  # 新增代码+ModelFailureState：把修复后的失败区块放回 settings；如果没有这行，清理结果不会保存。
    failures[_model_failure_key(clean_provider_id, clean_model_id)] = {"provider_id": clean_provider_id, "model_id": clean_model_id, "error_kind": str(error_kind or "model_failed"), "message": str(message or ""), "failed_at": time.time()}  # 新增代码+ModelFailureState：保存模型失败摘要且不含任何 token；如果没有这行，前端无法知道哪个模型刚失败。
    save_provider_settings(workspace, settings)  # 新增代码+ModelFailureState：持久化失败记录；如果没有这行，刷新设置页后标记会丢失。
    return build_provider_settings_payload(workspace)  # 新增代码+ModelFailureState：返回更新后的 catalog；如果没有这行，调用方无法立即刷新 UI。
# 新增代码+ModelFailureState：函数段结束，record_model_failure 到此结束；如果没有边界说明，初学者不易看出它只写低敏失败摘要。


def clear_provider_model_failures(workspace: str | Path, provider_id: Any | None = None) -> dict[str, Any]:  # 新增代码+ModelFailureState：函数段开始，对外清理模型失败记录；如果没有这段，重连或 catalog 刷新没有统一清理入口。
    settings = load_provider_settings(workspace)  # 新增代码+ModelFailureState：读取当前 provider 设置；如果没有这行，清理会丢失其它配置。
    clean_provider_id = str(provider_id or "").strip() if provider_id is not None else None  # 新增代码+ModelFailureState：清理可选 provider id；如果没有这行，空白 provider 会误删全部或删不到。
    _clear_model_failures_in_settings(settings, clean_provider_id)  # 新增代码+ModelFailureState：执行实际清理；如果没有这行，函数只是读取不修改。
    save_provider_settings(workspace, settings)  # 新增代码+ModelFailureState：保存清理后的设置；如果没有这行，刷新后失败标记会回来。
    return build_provider_settings_payload(workspace)  # 新增代码+ModelFailureState：返回最新 catalog；如果没有这行，调用方需要重复请求。
# 新增代码+ModelFailureState：函数段结束，clear_provider_model_failures 到此结束；如果没有边界说明，初学者不易看出它是 mutation helper。


def _codex_chatgpt_oauth_model_rows(settings: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+CodexOAuthModels：函数段开始，生成 Codex ChatGPT OAuth 真实可选模型；如果没有这段，GUI 可能继续显示 ChatGPT 账号不支持的模型。
    model_pairs = _codex_visible_model_pairs() or list(CODEX_CHATGPT_OAUTH_FALLBACK_MODELS)  # 新增代码+CodexOAuthModels：优先使用 codex 本机 catalog，失败时使用已验证兜底；如果没有这行，模型列表无法兼顾真实和稳定。
    return [_model("openai", model_id, display_name, _visibility(settings, "openai", model_id, True), True, True, _recent_model_failure(settings, "openai", model_id)) for model_id, display_name in model_pairs]  # 修改代码+ModelFailureState：把模型元数据和最近失败一起转换成 catalog 行；如果没有这行，Composer 底部菜单拿不到失败标记。
# 新增代码+CodexOAuthModels：函数段结束，_codex_chatgpt_oauth_model_rows 到此结束；如果没有边界说明，用户不易看出它只负责 OpenAI OAuth 模型行。


def _openai_model_rows(settings: dict[str, Any], auth_mode: str) -> list[dict[str, Any]]:  # 新增代码+CodexOAuthModels：函数段开始，按 OpenAI 认证模式选择模型列表；如果没有这段，API key 和 ChatGPT OAuth 会混用不兼容模型。
    clean_auth_mode = auth_mode.strip().lower()  # 新增代码+CodexOAuthModels：规范化认证模式；如果没有这行，大小写差异会让模型列表选错。
    if clean_auth_mode in {"codex_cli", "direct_oauth"}:  # 新增代码+CodexOAuthModels：ChatGPT OAuth 类路径使用 Codex 可见模型；如果没有这行，GUI 可能显示 ChatGPT 账号不支持的 gpt-4.1。
        return _codex_chatgpt_oauth_model_rows(settings)  # 新增代码+CodexOAuthModels：返回 Codex/ChatGPT OAuth 模型行；如果没有这行，真实 OAuth 模型无法进入底部菜单。
    return [_model("openai", "gpt-4.1", "GPT-4.1", _visibility(settings, "openai", "gpt-4.1", True), True, True, _recent_model_failure(settings, "openai", "gpt-4.1"))]  # 修改代码+ModelFailureState：API key/mock 路径继续展示普通 OpenAI API 模型并带失败摘要；如果没有这行，失败标记在模式切换后会丢失。
# 新增代码+CodexOAuthModels：函数段结束，_openai_model_rows 到此结束；如果没有边界说明，用户不易看出它只负责模式分流。


def _codex_visible_model_pairs() -> list[tuple[str, str]]:  # 新增代码+CodexOAuthModels：函数段开始，读取 Codex CLI 当前可见模型；如果没有这段，OpenHarness 无法像 Codex 一样跟随本机模型目录。
    codex_command = os.environ.get("CODEX_COMMAND", "codex").strip() or "codex"  # 新增代码+CodexOAuthModels：允许测试或用户覆盖 codex 可执行文件；如果没有这行，便携安装或 mock 测试无法工作。
    try:  # 新增代码+CodexOAuthModels：捕获 codex 不存在、超时或 JSON 损坏；如果没有这行，设置页会因为模型目录读取失败而 500。
        completed = subprocess.run([codex_command, "debug", "models"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5, check=False)  # 修改代码+CodexOAuthModels：用 UTF-8 安全读取官方 Codex 模型目录；如果没有这行，Windows GBK 环境可能把 catalog 解码成后台警告。
    except (OSError, subprocess.SubprocessError):  # 新增代码+CodexOAuthModels：处理进程启动和超时异常；如果没有这行，codex 临时异常会拖垮 GUI。
        return []  # 新增代码+CodexOAuthModels：失败时交给兜底模型列表；如果没有这行，调用方无法安全降级。
    if completed.returncode != 0:  # 新增代码+CodexOAuthModels：识别 codex debug models 命令失败；如果没有这行，stderr 错误可能被当 JSON 解析。
        return []  # 新增代码+CodexOAuthModels：命令失败时返回空列表触发兜底；如果没有这行，设置页可能暴露内部错误。
    try:  # 新增代码+CodexOAuthModels：保护 JSON 解析；如果没有这行，Codex 输出格式变化会让 GUI 崩溃。
        payload = json.loads(completed.stdout or "{}")  # 新增代码+CodexOAuthModels：把 codex 输出转成 Python 对象；如果没有这行，无法筛选真实模型。
    except json.JSONDecodeError:  # 新增代码+CodexOAuthModels：捕获非 JSON 输出；如果没有这行，警告或损坏输出会中断设置页。
        return []  # 新增代码+CodexOAuthModels：解析失败时使用兜底；如果没有这行，用户会看到 provider 加载失败。
    models = payload.get("models", []) if isinstance(payload, dict) else []  # 新增代码+CodexOAuthModels：只接受 dict.models 数组；如果没有这行，异常结构会污染后续循环。
    pairs: list[tuple[str, str]] = []  # 新增代码+CodexOAuthModels：准备保存可见模型 id 和名称；如果没有这行，无法稳定构造返回值。
    for item in models if isinstance(models, list) else []:  # 新增代码+CodexOAuthModels：遍历 Codex 返回的每个模型；如果没有这行，动态模型目录不会生效。
        if not isinstance(item, dict) or item.get("visibility") != "list":  # 新增代码+CodexOAuthModels：只保留 Codex 自己展示在列表里的模型；如果没有这行，隐藏或内部模型可能误进 GUI。
            continue  # 新增代码+CodexOAuthModels：跳过不该显示的模型；如果没有这行，后续可能保存空 id。
        model_id = str(item.get("slug", "")).strip()  # 新增代码+CodexOAuthModels：读取 Codex 模型 slug；如果没有这行，真实调用没有可传给 CLI 的模型 id。
        display_name = str(item.get("display_name", model_id)).strip() or model_id  # 新增代码+CodexOAuthModels：读取用户可见名称并兜底 slug；如果没有这行，模型菜单可能显示空白。
        if model_id:  # 新增代码+CodexOAuthModels：只加入非空模型 id；如果没有这行，空 id 会破坏可见性和请求参数。
            pairs.append((model_id, display_name))  # 新增代码+CodexOAuthModels：保存模型条目；如果没有这行，返回列表会一直为空。
    return pairs  # 新增代码+CodexOAuthModels：返回动态模型对；如果没有这行，调用方拿不到 Codex 可见模型。
# 新增代码+CodexOAuthModels：函数段结束，_codex_visible_model_pairs 到此结束；如果没有边界说明，用户不易看出它只负责读取 Codex catalog。


def _auth_record_for(settings: dict[str, Any], provider_id: str) -> dict[str, Any]:  # 新增代码+ProviderDisconnect：函数段开始，安全读取单个 provider 的 auth 记录；如果没有这段，catalog 和断开逻辑会重复处理坏 JSON。
    auth = settings.get("auth", {}) if isinstance(settings.get("auth", {}), dict) else {}  # 新增代码+ProviderDisconnect：只接受 dict 类型 auth 区块；如果没有这行，坏配置可能导致 get 调用异常。
    record = auth.get(provider_id, {}) if isinstance(auth.get(provider_id, {}), dict) else {}  # 新增代码+ProviderDisconnect：只接受 dict 类型单 provider 记录；如果没有这行，字符串记录会污染状态机。
    return record  # 新增代码+ProviderDisconnect：返回安全记录或空 dict；如果没有这行，调用方拿不到统一形状。
# 新增代码+ProviderDisconnect：函数段结束，_auth_record_for 到此结束；如果没有边界说明，用户不容易看出它只负责读 auth 记录。


def _provider_auth_type(settings: dict[str, Any], provider_id: str) -> str:  # 新增代码+ProviderDisconnect：函数段开始，读取 provider auth 类型；如果没有这段，disabled/api_key/oauth_direct 判断会散落多处。
    return str(_auth_record_for(settings, provider_id).get("type", "")).strip()  # 新增代码+ProviderDisconnect：返回清理后的 type 字符串；如果没有这行，空白或缺失类型会破坏分支判断。
# 新增代码+ProviderDisconnect：函数段结束，_provider_auth_type 到此结束；如果没有边界说明，用户不容易看出它只读非敏感类型。


def _disconnected_provider_info(provider_id: str, display_name: str, description: str, auth_methods: list[dict[str, Any]], models: list[dict[str, Any]]) -> GuiProviderInfo:  # 新增代码+ProviderDisconnect：函数段开始，构造本地断开 provider 行；如果没有这段，Codex CLI disabled 分支会重复手写字段。
    return GuiProviderInfo(id=provider_id, display_name=display_name, kind="built_in", source="none", connected=False, masked_key="", auth_methods=auth_methods, description=description, models=models)  # 新增代码+ProviderDisconnect：返回未连接且无来源的 provider；如果没有这行，断开后 UI 会继续显示旧来源或旧摘要。
# 新增代码+ProviderDisconnect：函数段结束，_disconnected_provider_info 到此结束；如果没有边界说明，用户不容易看出它只生成 catalog 行。


def clear_provider_disabled_override(workspace: str | Path, provider_id: Any) -> None:  # 新增代码+ProviderReconnect：函数段开始，清理本地 disabled 覆盖；如果没有这段，用户断开后即使重新完成 Codex 登录也会一直显示未连接。
    settings = load_provider_settings(workspace)  # 新增代码+ProviderReconnect：读取当前 provider 设置；如果没有这行，无法知道是否存在 disabled 覆盖。
    clean_provider_id = validate_provider_id(provider_id, settings)  # 新增代码+ProviderReconnect：校验 provider id；如果没有这行，坏 id 可能改写 auth 配置。
    auth = settings.setdefault("auth", {})  # 新增代码+ProviderReconnect：读取或创建 auth 区块；如果没有这行，无法删除 disabled 记录。
    auth_record = auth.get(clean_provider_id, {}) if isinstance(auth.get(clean_provider_id, {}), dict) else {}  # 新增代码+ProviderReconnect：读取当前 provider auth 记录；如果没有这行，无法判断是否真的 disabled。
    if str(auth_record.get("type", "")).strip() == "disabled":  # 新增代码+ProviderReconnect：只清理由断开生成的 disabled 覆盖；如果没有这行，API key 或 OAuth 记录可能被误删。
        auth.pop(clean_provider_id, None)  # 新增代码+ProviderReconnect：删除 disabled 覆盖；如果没有这行，catalog 会继续优先显示未连接。
        _clear_model_failures_in_settings(settings, clean_provider_id)  # 新增代码+ModelFailureState：重新连接时清除该 provider 旧模型失败；如果没有这行，重连后模型菜单仍会显示过期失败。
        save_provider_settings(workspace, settings)  # 新增代码+ProviderReconnect：持久化清理结果；如果没有这行，刷新或重启后 disabled 仍然存在。
# 新增代码+ProviderReconnect：函数段结束，clear_provider_disabled_override 到此结束；如果没有边界说明，用户不容易看出它只清本地覆盖不碰 token。


def _built_in_provider_catalog(settings: dict[str, Any], secret_store: DevJsonSecretStore) -> list[dict[str, Any]]:  # 新增代码+ProviderSettings：函数段开始，构造内置 provider catalog；如果没有这段，GET 路由没有核心数据。
    auth = settings.get("auth", {}) if isinstance(settings.get("auth", {}), dict) else {}  # 新增代码+ProviderSettings：读取认证配置；如果没有这行，connected 状态无法来自配置。
    openai_auth_mode = _openai_auth_mode()  # 新增代码+CodexLoginCatalog：读取 OpenAI 当前认证模式；如果没有这行，OpenAI 行无法切到官方 Codex CLI 登录状态。
    providers: list[GuiProviderInfo] = []  # 新增代码+ProviderSettings：准备 provider 列表；如果没有这行，后续无法累积 catalog。
    built_ins = [  # 新增代码+ProviderSettings：集中声明内置 provider 元数据；如果没有这段，display name 和模型会散落。
        ("github-copilot", "GitHub Copilot", "使用 Copilot 或 API 密钥连接", [_unsupported_auth_method("device-code", "设备码", "V1 只展示入口，不执行 Copilot 登录。")], []),  # 新增代码+ProviderSettings：声明 Copilot V1 暂未支持；如果没有这行，UI 会误导用户连接。
        ("openai", "OpenAI", "使用 ChatGPT Pro/Plus 或 API 密钥连接", _openai_auth_methods(openai_auth_mode), _openai_model_rows(settings, openai_auth_mode)),  # 修改代码+CodexOAuthModels：声明 OpenAI provider 并按认证模式选择模型；如果没有这行，GUI 会给 ChatGPT OAuth 账号显示不支持的 gpt-4.1。
        ("google", "Google", "使用 Google 账号或 API 密钥连接", [_api_key_auth_method()], [_model("google", "gemini-2.5-pro", "Gemini 2.5 Pro", _visibility(settings, "google", "gemini-2.5-pro", True), True, True, _recent_model_failure(settings, "google", "gemini-2.5-pro"))]),  # 修改代码+ModelFailureState：声明 Google provider 并携带模型失败摘要；如果没有这行，Gemini 实验入口缺失且失败标记无法显示。
        ("openrouter", "OpenRouter", "使用 OpenRouter 账号或 API 密钥连接", [_api_key_auth_method()], [_model("openrouter", "openrouter/auto", "OpenRouter Auto", _visibility(settings, "openrouter", "openrouter/auto", True), True, True, _recent_model_failure(settings, "openrouter", "openrouter/auto"))]),  # 修改代码+ModelFailureState：声明 OpenRouter provider 并携带模型失败摘要；如果没有这行，多模型路由入口缺失且失败标记无法显示。
        ("vercel", "Vercel AI Gateway", "使用 Vercel 账号或 API 密钥连接", [_api_key_auth_method()], [_model("vercel", "vercel/auto", "Vercel Gateway Auto", _visibility(settings, "vercel", "vercel/auto", True), True, True, _recent_model_failure(settings, "vercel", "vercel/auto"))]),  # 修改代码+ModelFailureState：声明 Vercel provider 并携带模型失败摘要；如果没有这行，AI Gateway 入口缺失且失败标记无法显示。
    ]  # 新增代码+ProviderSettings：内置 provider 元数据结束；如果没有这行，Python 列表语法不完整。
    for provider_id, display_name, description, auth_methods, models in built_ins:  # 新增代码+ProviderSettings：遍历内置 provider；如果没有这行，元数据不会变成 payload。
        auth_record = _auth_record_for(settings, provider_id)  # 新增代码+ProviderDisconnect：先读取 provider auth 记录；如果没有这行，disabled 覆盖无法优先于外部登录态生效。
        auth_type = str(auth_record.get("type", ""))  # 新增代码+ProviderDisconnect：读取认证记录类型；如果没有这行，disabled/api_key/oauth_direct 分支无法统一判断。
        if auth_type == "disabled":  # 新增代码+ProviderDisconnect：处理用户在 OpenHarness 本地断开的 provider；如果没有这行，Codex CLI 登录态会把 OpenAI 自动拉回已连接。
            providers.append(_disconnected_provider_info(provider_id, display_name, description, auth_methods, models))  # 新增代码+ProviderDisconnect：加入明确未连接的 provider 行；如果没有这行，断开后刷新仍可能显示旧连接。
            continue  # 新增代码+ProviderDisconnect：本地 disabled 覆盖后跳过外部状态和 secret 检查；如果没有这行，后续分支会覆盖断开结果。
        if provider_id == "openai" and openai_auth_mode == "codex_cli":  # 新增代码+CodexLoginCatalog：官方模式下 OpenAI 状态来自 Codex CLI；如果没有这行，catalog 仍会读取 mock/API key 配置。
            codex_status = CodexAuthBridge().login_status()  # 新增代码+CodexLoginCatalog：调用官方 status 命令查询登录态；如果没有这行，provider 无法知道 ChatGPT 是否已登录。
            codex_connected = bool(codex_status.available and codex_status.connected)  # 新增代码+CodexLoginCatalog：只有 CLI 可用且已登录才算 connected；如果没有这行，CLI 缺失或未登录会被误判。
            codex_source = "codex_cli_missing" if not codex_status.available else "codex_cli"  # 新增代码+CodexLoginCatalog：区分 CLI 缺失和官方模式未连接；如果没有这行，用户不知道是缺安装还是未登录。
            codex_masked = "Codex ChatGPT login" if codex_connected else ""  # 新增代码+CodexLoginCatalog：已连接时显示安全摘要；如果没有这行，用户无法识别连接来源。
            providers.append(GuiProviderInfo(id=provider_id, display_name=display_name, kind="built_in", source=codex_source, connected=codex_connected, masked_key=codex_masked, auth_methods=auth_methods, description=description, models=models))  # 新增代码+CodexLoginCatalog：加入官方 Codex provider payload；如果没有这行，设置页看不到真实登录状态。
            continue  # 新增代码+CodexLoginCatalog：官方模式不再读取 OpenHarness secret 或 mock 状态；如果没有这行，mock/API key 会覆盖 Codex CLI 事实。
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
            _model(str(provider_id), str(item.get("id", "")), str(item.get("display_name", item.get("name", item.get("id", "")))), bool(item.get("visible", True)), True, True, _recent_model_failure(settings, str(provider_id), str(item.get("id", ""))))  # 修改代码+ModelFailureState：把单条模型转为稳定 payload 并附带失败摘要；如果没有这行，自定义模型字段会不一致且菜单无失败标记。
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
    _clear_model_failures_in_settings(settings, clean_provider_id)  # 新增代码+ModelFailureState：API key 重连后清掉该 provider 的旧模型失败；如果没有这行，用户修好连接后仍会看到旧失败标记。
    save_provider_settings(workspace, settings)  # 新增代码+ProviderSettings：保存主配置；如果没有这行，连接状态只在内存里存在。
    return build_provider_settings_payload(workspace)  # 新增代码+ProviderSettings：返回脱敏 catalog；如果没有这行，前端无法刷新连接状态。
# 新增代码+ProviderSettings：函数段结束，set_provider_auth 到此结束；如果没有边界说明，初学者不易看出它保存 auth 并返回 catalog。


def disconnect_provider(workspace: str | Path, provider_id: Any) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，断开 provider 并清理密钥；如果没有这段，断开按钮不会真正删除 secret。
    settings = load_provider_settings(workspace)  # 新增代码+ProviderSettings：读取当前设置；如果没有这行，无法找到 secret_ref。
    clean_provider_id = validate_provider_id(provider_id, settings)  # 新增代码+ProviderSettings：校验目标 provider；如果没有这行，未知 provider 删除可能污染配置。
    secret_store = DevJsonSecretStore(workspace)  # 新增代码+ProviderSettings：创建密钥存储；如果没有这行，无法删除 raw secret。
    auth = settings.setdefault("auth", {})  # 新增代码+ProviderSettings：读取 auth 区块；如果没有这行，删除状态无法写回。
    auth_record = auth.pop(clean_provider_id, {}) if isinstance(auth, dict) else {}  # 新增代码+ProviderSettings：移除认证记录；如果没有这行，catalog 仍会显示 connected。
    auth_type = str(auth_record.get("type", "")).strip() if isinstance(auth_record, dict) else ""  # 新增代码+ProviderDisconnect：读取断开前认证类型；如果没有这行，OAuth token 和 Codex CLI disabled 覆盖无法正确处理。
    secret_ref = str(auth_record.get("secret_ref", safe_secret_ref(clean_provider_id, "api_key"))) if isinstance(auth_record, dict) else safe_secret_ref(clean_provider_id, "api_key")  # 新增代码+ProviderSettings：读取待删除 secret_ref；如果没有这行，secret store 会留下旧 key。
    secret_store.delete_secret(secret_ref)  # 新增代码+ProviderSettings：删除 provider API key；如果没有这行，断开后 raw key 仍在磁盘。
    if clean_provider_id == "openai" and auth_type == "oauth_direct":  # 新增代码+ProviderDisconnect：识别 direct OAuth 连接；如果没有这行，断开只会清 token_ref 而不会删除本机 OAuth token。
        default_oauth_token_store().delete_tokens("openai")  # 新增代码+ProviderDisconnect：删除 direct OAuth token 文件；如果没有这行，用户点击断开后 refresh token 可能继续留在本机。
    if clean_provider_id == "openai" and _openai_auth_mode() == "codex_cli":  # 新增代码+ProviderDisconnect：识别官方 Codex CLI 模式；如果没有这行，外部 Codex 登录态会在断开后立刻把 OpenAI 显示为已连接。
        auth[clean_provider_id] = {"type": "disabled", "disabled_source": "codex_cli", "updated_at": time.time()}  # 新增代码+ProviderDisconnect：写入 OpenHarness 本地 disabled 覆盖；如果没有这行，刷新或重启后断开状态无法保持。
    custom_providers = settings.get("custom_providers", {}) if isinstance(settings.get("custom_providers", {}), dict) else {}  # 新增代码+ProviderSettings：读取自定义 provider 区块；如果没有这行，custom provider 自带 secret_ref 无法清理。
    if clean_provider_id in custom_providers and isinstance(custom_providers[clean_provider_id], dict):  # 新增代码+ProviderSettings：处理自定义 provider 记录；如果没有这行，自定义密钥可能残留。
        custom_secret_ref = str(custom_providers[clean_provider_id].get("secret_ref", safe_secret_ref(clean_provider_id, "api_key")))  # 新增代码+ProviderSettings：读取自定义 provider secret_ref；如果没有这行，无法清理自定义密钥。
        secret_store.delete_secret(custom_secret_ref)  # 新增代码+ProviderSettings：删除自定义 provider 密钥；如果没有这行，自定义断开后仍有 raw key。
    _clear_model_failures_in_settings(settings, clean_provider_id)  # 新增代码+ModelFailureState：断开 provider 时清掉旧模型失败；如果没有这行，重新连接前后会残留不再有意义的失败标记。
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
    _clear_model_failures_in_settings(settings, provider_id)  # 新增代码+ModelFailureState：保存自定义 provider 时清掉旧模型失败；如果没有这行，更新模型 catalog 后仍可能显示旧失败。
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


def probe_openai_codex_cli_login() -> tuple[str, str, int]:  # 新增代码+CodexLoginProbe：函数段开始，测试 OpenAI 的 Codex CLI 登录状态；如果没有这段，设置页已连接时测试连接仍会误读 API key。
    codex_status = CodexAuthBridge().login_status()  # 新增代码+CodexLoginProbe：调用官方 Codex 登录状态桥；如果没有这行，probe 无法知道 ChatGPT OAuth 是否真的完成。
    if not codex_status.available:  # 新增代码+CodexLoginProbe：处理 Codex CLI 不可用；如果没有这行，缺 CLI 会被误说成认证失败或缺密钥。
        return "unsupported", "Codex CLI 不可用，暂不能测试 ChatGPT 登录。", 0  # 新增代码+CodexLoginProbe：返回暂不支持状态；如果没有这行，前端无法给出正确修复方向。
    if not codex_status.connected:  # 新增代码+CodexLoginProbe：处理 Codex CLI 可用但未登录；如果没有这行，未登录会被误判为通过。
        return "auth_failed", "Codex CLI 尚未完成 ChatGPT 登录。", 0  # 新增代码+CodexLoginProbe：返回认证失败状态；如果没有这行，用户不知道需要重新登录。
    return "ok", "Codex ChatGPT login 可用。", 0  # 新增代码+CodexLoginProbe：返回成功且不暴露 token；如果没有这行，真实 GUI 测试连接会继续显示缺少密钥。
# 新增代码+CodexLoginProbe：函数段结束，probe_openai_codex_cli_login 到此结束；如果没有边界说明，初学者不易看出它只检查登录状态。


def probe_openai_direct_oauth_record(settings: dict[str, Any]) -> tuple[str, str, int]:  # 新增代码+DirectOAuthProbe：函数段开始，测试 OpenAI direct OAuth 的非敏感连接记录；如果没有这段，direct OAuth 成功后测试连接仍会误读 API key。
    auth = settings.get("auth", {}) if isinstance(settings.get("auth", {}), dict) else {}  # 新增代码+DirectOAuthProbe：读取 auth 区块；如果没有这行，无法找到 direct OAuth 的 token_ref 记录。
    auth_record = auth.get("openai", {}) if isinstance(auth.get("openai", {}), dict) else {}  # 新增代码+DirectOAuthProbe：读取 OpenAI 认证记录；如果没有这行，其它 provider 配置可能被误用。
    auth_type = str(auth_record.get("type", "")).strip()  # 新增代码+DirectOAuthProbe：读取记录类型；如果没有这行，API key 和 OAuth token_ref 会混在一起。
    token_ref = str(auth_record.get("token_ref", "")).strip()  # 新增代码+DirectOAuthProbe：读取非敏感 token 引用；如果没有这行，无法判断 direct OAuth 是否完成。
    if auth_type != "oauth_direct" or not token_ref:  # 新增代码+DirectOAuthProbe：要求 direct OAuth 类型和 token_ref 同时存在；如果没有这行，空记录会误显示成功。
        return "missing_secret", "缺少 ChatGPT OAuth token 连接记录。", 0  # 新增代码+DirectOAuthProbe：返回缺少凭据状态但不说 API key；如果没有这行，用户会被错误引导去填密钥。
    return "ok", "ChatGPT OAuth token 连接记录可用。", 0  # 新增代码+DirectOAuthProbe：返回成功且不暴露 token_ref；如果没有这行，direct OAuth GUI 测试连接会继续失败。
# 新增代码+DirectOAuthProbe：函数段结束，probe_openai_direct_oauth_record 到此结束；如果没有边界说明，初学者不易看出它不读取 raw token。


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
    openai_auth_mode = _openai_auth_mode()  # 新增代码+OAuthProbeBranch：读取 OpenAI 当前认证模式；如果没有这行，probe 无法区分 API key、Codex CLI 和 direct OAuth。
    if clean_provider_id == "openai" and openai_auth_mode == "codex_cli":  # 新增代码+CodexLoginProbe：Codex CLI 模式走登录状态探针；如果没有这行，已连接状态会被 API key 缺失覆盖。
        status, message, models_count = probe_openai_codex_cli_login()  # 新增代码+CodexLoginProbe：执行 Codex 登录状态检查；如果没有这行，测试连接按钮没有事实来源。
        return build_probe_result(clean_provider_id, status, message, models_count)  # 新增代码+CodexLoginProbe：返回脱敏 probe 结果；如果没有这行，前端无法显示连接测试通过。
    if clean_provider_id == "openai" and openai_auth_mode == "direct_oauth":  # 新增代码+DirectOAuthProbe：direct OAuth 模式走 token_ref 记录探针；如果没有这行，OAuth 登录后仍会被当成缺 API key。
        status, message, models_count = probe_openai_direct_oauth_record(settings)  # 新增代码+DirectOAuthProbe：检查非敏感 token_ref 连接记录；如果没有这行，测试连接不知道 OAuth 是否完成。
        return build_probe_result(clean_provider_id, status, message, models_count)  # 新增代码+DirectOAuthProbe：返回脱敏 probe 结果；如果没有这行，前端无法显示 direct OAuth 测试通过。
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
