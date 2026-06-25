"""OpenHarness Desktop Provider 设置合同。"""  # 新增代码+ProviderSettings：说明本模块负责桌面 provider 设置 payload；如果没有这行，维护者容易把它和真实模型运行时混在一起。

from __future__ import annotations  # 新增代码+ProviderSettings：启用延迟类型解析；如果没有这行，dataclass 和 helper 类型引用更脆弱。

import json  # 新增代码+ProviderSettings：读写 provider 设置 JSON；如果没有这行，自定义 provider 无法持久化。
import threading  # 新增代码+ProviderSettings：保护 provider 设置并发写入；如果没有这行，快速切换模型可见性可能写坏配置。
import time  # 新增代码+ProviderSettings：生成损坏设置文件归档时间戳；如果没有这行，坏 JSON 备份文件名不稳定。
from dataclasses import asdict, dataclass  # 新增代码+ProviderSettings：定义 provider/auth/model 结构；如果没有这行，catalog 字段会散成难维护的 dict。
from pathlib import Path  # 新增代码+ProviderSettings：规范化 workspace 和 memory 路径；如果没有这行，Windows 路径容易出错。
from typing import Any  # 新增代码+ProviderSettings：标注未知 JSON 对象；如果没有这行，payload 清洗边界不清楚。

from learning_agent.app.gui_provider_secret_store import DevJsonSecretStore, safe_secret_ref  # 新增代码+ProviderSettings：复用 secret store 和引用格式；如果没有这行，主配置可能保存 raw key。


PROVIDER_SETTINGS_SCHEMA_VERSION = 2  # 新增代码+ProviderSettings：声明 Provider Settings 合同版本；如果没有这行，前后端无法判断 payload 兼容性。
BUILT_IN_PROVIDER_IDS = ("github-copilot", "openai", "google", "openrouter", "vercel")  # 新增代码+ProviderSettings：集中定义内置 provider id；如果没有这行，验证和 catalog 会各自维护列表。
_PROVIDER_SETTINGS_LOCK = threading.Lock()  # 新增代码+ProviderSettings：锁住 provider 设置文件写入；如果没有这行，并发 mutation 可能互相覆盖。


@dataclass  # 新增代码+ProviderSettings：自动生成 auth method 字典字段；如果没有这行，to_dict 需要手写重复代码。
class GuiAuthMethodInfo:  # 新增代码+ProviderSettings：类段开始，描述一个 Provider 认证方式；如果没有这个类，Copilot unsupported 和 API key 可用状态会散落。
    id: str  # 新增代码+ProviderSettings：认证方式 id；如果没有这行，前端无法提交选择的认证方式。
    label: str  # 新增代码+ProviderSettings：认证方式显示名；如果没有这行，设置页只能显示机器码。
    enabled: bool  # 新增代码+ProviderSettings：认证方式是否可用；如果没有这行，前端会误把 Copilot 当作可连接。
    status: str  # 新增代码+ProviderSettings：认证方式状态；如果没有这行，UI 无法显示 unsupported_v1 等原因。
    fields: list[str]  # 新增代码+ProviderSettings：认证表单字段代号；如果没有这行，connect dialog 无法知道要收集什么。
    help_text: str  # 新增代码+ProviderSettings：认证帮助文案；如果没有这行，用户不知道该提供哪种凭据。
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
    return asdict(GuiAuthMethodInfo(id="api-key", label="API 密钥", enabled=enabled, status=status, fields=["secret"], help_text="使用 API 密钥连接"))  # 新增代码+ProviderSettings：返回不含 api_key 字段名的安全合同；如果没有这行，renderer 响应会长期持有敏感字段语义。
# 新增代码+ProviderSettings：函数段结束，_api_key_auth_method 到此结束；如果没有边界说明，初学者不易看出它只生成认证元数据。


def _unsupported_auth_method(method_id: str, label: str, help_text: str) -> dict[str, Any]:  # 新增代码+ProviderSettings：函数段开始，生成 V1 未支持认证方法；如果没有这段，Copilot 可能被误渲染成可连接。
    return asdict(GuiAuthMethodInfo(id=method_id, label=label, enabled=False, status="unsupported_v1", fields=[], help_text=help_text))  # 新增代码+ProviderSettings：返回 disabled auth method；如果没有这行，前端无法显示暂未支持。
# 新增代码+ProviderSettings：函数段结束，_unsupported_auth_method 到此结束；如果没有边界说明，初学者不易看出它只负责 unsupported 元数据。


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
    providers: list[GuiProviderInfo] = []  # 新增代码+ProviderSettings：准备 provider 列表；如果没有这行，后续无法累积 catalog。
    built_ins = [  # 新增代码+ProviderSettings：集中声明内置 provider 元数据；如果没有这段，display name 和模型会散落。
        ("github-copilot", "GitHub Copilot", "使用 Copilot 或 API 密钥连接", [_unsupported_auth_method("device-code", "设备码", "V1 只展示入口，不执行 Copilot 登录。")], []),  # 新增代码+ProviderSettings：声明 Copilot V1 暂未支持；如果没有这行，UI 会误导用户连接。
        ("openai", "OpenAI", "使用 ChatGPT Pro/Plus 或 API 密钥连接", [_api_key_auth_method()], [_model("openai", "gpt-4.1", "GPT-4.1", _visibility(settings, "openai", "gpt-4.1", True), True, True)]),  # 新增代码+ProviderSettings：声明 OpenAI provider；如果没有这行，最常用 provider 不会出现。
        ("google", "Google", "使用 Google 账号或 API 密钥连接", [_api_key_auth_method()], [_model("google", "gemini-2.5-pro", "Gemini 2.5 Pro", _visibility(settings, "google", "gemini-2.5-pro", True), True, True)]),  # 新增代码+ProviderSettings：声明 Google provider；如果没有这行，Gemini 实验入口缺失。
        ("openrouter", "OpenRouter", "使用 OpenRouter 账号或 API 密钥连接", [_api_key_auth_method()], [_model("openrouter", "openrouter/auto", "OpenRouter Auto", _visibility(settings, "openrouter", "openrouter/auto", True), True, True)]),  # 新增代码+ProviderSettings：声明 OpenRouter provider；如果没有这行，多模型路由入口缺失。
        ("vercel", "Vercel AI Gateway", "使用 Vercel 账号或 API 密钥连接", [_api_key_auth_method()], [_model("vercel", "vercel/auto", "Vercel Gateway Auto", _visibility(settings, "vercel", "vercel/auto", True), True, True)]),  # 新增代码+ProviderSettings：声明 Vercel provider；如果没有这行，AI Gateway 入口缺失。
    ]  # 新增代码+ProviderSettings：内置 provider 元数据结束；如果没有这行，Python 列表语法不完整。
    for provider_id, display_name, description, auth_methods, models in built_ins:  # 新增代码+ProviderSettings：遍历内置 provider；如果没有这行，元数据不会变成 payload。
        auth_record = auth.get(provider_id, {}) if isinstance(auth.get(provider_id, {}), dict) else {}  # 新增代码+ProviderSettings：读取当前 provider 认证记录；如果没有这行，connected 无法计算。
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
