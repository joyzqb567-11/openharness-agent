"""OpenHarness Desktop OpenAI provider 运行态摘要。"""  # 新增代码+OpenAIProviderState：说明本模块只输出安全 runtime state；如果没有这行，维护者容易把 token 值加入诊断。

from __future__ import annotations  # 新增代码+OpenAIProviderState：启用延迟类型解析；如果没有这行，类型注解在旧解释顺序下更脆弱。

from dataclasses import asdict, dataclass  # 新增代码+OpenAIProviderState：定义状态对象并安全序列化；如果没有这行，字段会散成手写 dict。
from datetime import datetime, timezone  # 新增代码+OpenAIProviderState：生成 UTC 更新时间；如果没有这行，状态时间缺少稳定格式。
from pathlib import Path  # 新增代码+OpenAIProviderState：标注 workspace 路径类型；如果没有这行，Windows 路径语义不清楚。
from typing import Any  # 新增代码+OpenAIProviderState：标注 JSON-like 设置对象；如果没有这行，动态配置边界不清楚。

from learning_agent.app.gui_provider_openai_models import build_openai_model_catalog_rows, load_openai_model_registry  # 修改代码+OpenAIModelRegistry：复用统一 OpenAI 模型注册表和 LKG 缓存；如果没有这行，runtime state 会和设置页模型不一致。
from learning_agent.app.gui_provider_settings import load_provider_settings  # 新增代码+OpenAIProviderState：读取 provider settings；如果没有这行，runtime state 无法来自真实连接状态。


@dataclass(frozen=True)  # 新增代码+OpenAIProviderState：生成不可变状态对象；如果没有这行，序列化前字段可能被意外改写。
class OpenAIProviderRuntimeState:  # 新增代码+OpenAIProviderState：类段开始，描述 OpenAI provider 可公开运行态；如果没有这个类，诊断字段会漂移。
    provider_id: str  # 新增代码+OpenAIProviderState：保存 provider id；如果没有这行，前端无法确认状态属于 OpenAI。
    auth_type: str  # 新增代码+OpenAIProviderState：保存认证类型；如果没有这行，UI 无法区分 oauth_real、oauth_mock、api_key。
    runtime: str  # 新增代码+OpenAIProviderState：保存目标运行时；如果没有这行，诊断看不出 direct_sse 是否启用。
    direct_route_status: str  # 新增代码+OpenAIProviderState：保存直连路径状态；如果没有这行，用户不知道是否需要重连或选账号。
    account_id: str | None  # 新增代码+OpenAIProviderState：保存安全账号 id；如果没有这行，多账号状态无法关联。
    account_label: str  # 新增代码+OpenAIProviderState：保存脱敏账号标签；如果没有这行，UI 无法提示当前连接。
    selected_model_id: str | None  # 新增代码+OpenAIProviderState：保存当前模型选择；如果没有这行，Direct SSE 无法说明路由目标。
    available_models: list[str]  # 新增代码+OpenAIProviderState：保存当前可见模型列表；如果没有这行，模型菜单没有安全后端来源。
    last_known_good_models: list[str]  # 新增代码+OpenAIProviderState：保存最后成功模型缓存；如果没有这行，后续探针失败时无法回退显示。
    oauth_client_source: str  # 新增代码+OpenAIProviderState：保存 OAuth client id 来源；如果没有这行，用户不知道是否使用 OpenCode 观察参考。
    needs_reconnect: bool  # 新增代码+OpenAIProviderState：保存是否需要重连；如果没有这行，UI 无法提示连接状态。
    updated_at: str  # 新增代码+OpenAIProviderState：保存 UTC 更新时间；如果没有这行，诊断无法判断状态新旧。
    # 新增代码+OpenAIProviderState：类段结束，OpenAIProviderRuntimeState 到此结束；如果没有边界说明，初学者不易看出字段范围。


def _utc_now_iso() -> str:  # 新增代码+OpenAIProviderState：函数段开始，生成稳定 UTC 时间；如果没有这段，状态时间格式会散落。
    return datetime.now(timezone.utc).isoformat()  # 新增代码+OpenAIProviderState：返回 ISO 格式 UTC 时间；如果没有这行，前端难以排序或展示更新时间。
# 新增代码+OpenAIProviderState：函数段结束，_utc_now_iso 到此结束；如果没有边界说明，初学者不易看出它只负责时间。


def _openai_visible_models(workspace: str | Path, settings: dict[str, Any]) -> list[str]:  # 修改代码+OpenAIModelRegistry：函数段开始，从统一注册表收集 OpenAI 可见模型；如果没有这段，runtime state 只能返回空模型。
    rows = build_openai_model_catalog_rows(workspace, settings)  # 新增代码+OpenAIModelRegistry：读取静态、探针和 last-known-good 模型行；如果没有这行，状态面板不会反映真实账号模型。
    return [str(row.get("id", "")) for row in rows if bool(row.get("visible", True)) and str(row.get("id", "")).strip()]  # 修改代码+OpenAIModelRegistry：只返回可见模型 id；如果没有这行，隐藏模型或空模型会进入 runtime state。
# 新增代码+OpenAIProviderState：函数段结束，_openai_visible_models 到此结束；如果没有边界说明，初学者不易看出它只做安全模型摘要。


def _direct_route_status(auth_type: str, auth_record: dict[str, Any]) -> str:  # 新增代码+OpenAIProviderState：函数段开始，推导 direct route 状态；如果没有这段，状态字段会散落。
    if auth_type == "":  # 新增代码+OpenAIProviderState：识别未连接状态；如果没有这行，未连接也可能显示 not_probed。
        return "not_connected"  # 新增代码+OpenAIProviderState：返回未连接；如果没有这行，UI 无法提示先连接。
    if str(auth_record.get("account_selection_status", "")) == "account_selection_required":  # 新增代码+OpenAIProviderState：识别账号选择需求；如果没有这行，多账号失败无法反馈。
        return "account_selection_required"  # 新增代码+OpenAIProviderState：返回需要账号选择；如果没有这行，UI 无法引导用户。
    return "not_probed"  # 新增代码+OpenAIProviderState：已连接但未探针时返回 not_probed；如果没有这行，状态会被误报 healthy。
# 新增代码+OpenAIProviderState：函数段结束，_direct_route_status 到此结束；如果没有边界说明，初学者不易看出它只做状态映射。


def build_openai_provider_runtime_state(workspace: str | Path) -> OpenAIProviderRuntimeState:  # 新增代码+OpenAIProviderState：函数段开始，构造安全 OpenAI runtime state；如果没有这段，前端无法显示真实连接诊断。
    settings = load_provider_settings(workspace)  # 新增代码+OpenAIProviderState：读取 provider settings；如果没有这行，状态无法反映连接和模型选择。
    auth = settings.get("auth", {}) if isinstance(settings.get("auth", {}), dict) else {}  # 新增代码+OpenAIProviderState：读取 auth 区块；如果没有这行，无法判断 OpenAI 是否连接。
    auth_record = auth.get("openai", {}) if isinstance(auth.get("openai", {}), dict) else {}  # 新增代码+OpenAIProviderState：读取 OpenAI 认证记录；如果没有这行，状态字段没有来源。
    auth_type = str(auth_record.get("type", ""))  # 新增代码+OpenAIProviderState：读取认证类型；如果没有这行，OAuth/API key 状态无法区分。
    selected_model = str(settings.get("selected_openai_model_id", "") or settings.get("default_model_id", "") or "")  # 新增代码+OpenAIProviderState：读取当前模型选择；如果没有这行，Direct SSE 目标不明确。
    account_id = str(auth_record.get("account_id", settings.get("selected_openai_account_id", "")) or "")  # 新增代码+OpenAIProviderState：读取安全账号 id；如果没有这行，账号状态无法显示。
    account_label = str(auth_record.get("account_label", settings.get("selected_openai_account_label", "")) or "")  # 新增代码+OpenAIProviderState：读取脱敏账号标签；如果没有这行，UI 看不到当前账号。
    registry = load_openai_model_registry(workspace)  # 新增代码+OpenAIModelRegistry：读取 last-known-good 模型缓存；如果没有这行，runtime state 的成功模型列表会永远为空。
    last_known_good = [str(model_id) for model_id in registry.get("last_known_good_models", []) if str(model_id).strip()]  # 新增代码+OpenAIModelRegistry：清洗成功模型列表；如果没有这行，坏缓存可能进入诊断 payload。
    state = OpenAIProviderRuntimeState(provider_id="openai", auth_type=auth_type, runtime="direct_sse", direct_route_status=_direct_route_status(auth_type, auth_record), account_id=account_id or None, account_label=account_label, selected_model_id=selected_model or None, available_models=_openai_visible_models(workspace, settings), last_known_good_models=last_known_good, oauth_client_source=str(auth_record.get("oauth_client_source", "")), needs_reconnect=auth_type == "", updated_at=_utc_now_iso())  # 修改代码+OpenAIModelRegistry：组装不含 token/secret_ref 的状态对象并使用统一模型注册表；如果没有这行，前端只能读取危险原始 settings。
    return state  # 新增代码+OpenAIProviderState：返回状态对象；如果没有这行，调用方拿不到 runtime state。
# 新增代码+OpenAIProviderState：函数段结束，build_openai_provider_runtime_state 到此结束；如果没有边界说明，初学者不易看出它是主入口。


def serialize_openai_provider_runtime_state(state: OpenAIProviderRuntimeState) -> dict[str, Any]:  # 新增代码+OpenAIProviderState：函数段开始，把 runtime state 转成 JSON dict；如果没有这段，测试和 bridge 会各自调用 asdict。
    payload = asdict(state)  # 新增代码+OpenAIProviderState：把 dataclass 转成普通 dict；如果没有这行，JSON 序列化会收到 dataclass 对象。
    payload.pop("secret_refs", None)  # 新增代码+OpenAIProviderState：防御性移除 secret_refs；如果没有这行，未来字段误加可能泄露密钥定位。
    return payload  # 新增代码+OpenAIProviderState：返回安全 payload；如果没有这行，调用方拿不到可序列化对象。
# 新增代码+OpenAIProviderState：函数段结束，serialize_openai_provider_runtime_state 到此结束；如果没有边界说明，初学者不易看出它是序列化安全网。
