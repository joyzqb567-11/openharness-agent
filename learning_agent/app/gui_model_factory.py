"""Desktop GUI 真实 agent 模型工厂。"""  # 新增代码+GuiModelFactory：本模块负责从 GUI provider 设置创建 ChatModel；如果没有这一行，读者会把模型选择逻辑误放进 bridge。

from __future__ import annotations  # 新增代码+GuiModelFactory：启用延迟类型解析；如果没有这一行，跨模块类型标注更容易循环导入。

import os  # 新增代码+GuiModelFactory：读取测试和默认模型环境变量；如果没有这一行，离线 probe 无法用假模型稳定运行。
import time  # 新增代码+GuiModelFactory：为缺失过期时间的 GUI OAuth token 提供保守时间戳；如果没有这一行，token store 无法兼容旧配置。
from pathlib import Path  # 新增代码+GuiModelFactory：规范化 workspace 路径；如果没有这一行，provider settings 和 secret store 路径可能漂移。
from typing import Any, Callable  # 新增代码+GuiModelFactory：标注模型工厂和 JSON-like 配置；如果没有这一行，注入边界不清楚。

from learning_agent.app.gui_agent_adapter import GuiAgentRunRequest  # 新增代码+GuiModelFactory：读取 GUI run 请求字段；如果没有这一行，工厂无法知道 provider/model/workspace。
from learning_agent.app.gui_provider_secret_store import make_provider_secret_store, safe_secret_ref  # 新增代码+GuiModelFactory：复用 GUI provider secret store；如果没有这一行，真实 token 会绕过设置页事实源。
from learning_agent.app.gui_provider_settings import load_provider_settings, save_provider_settings  # 新增代码+GuiModelFactory：复用 provider settings 读写；如果没有这一行，模型工厂无法识别 OpenAI 是否已连接。
from learning_agent.core.messages import ModelMessage, ToolCall  # 修改代码+GuiModelFactoryVisibleToolTrace：同时导入 ToolCall，方便离线假模型生成工具调用；如果没有这一行，GUI 肉眼验收看不到 read_file 工具轨迹。
from learning_agent.models.adapters import CodexOAuthChatModel, CodexOAuthTokens  # 新增代码+GuiModelFactory：复用现有 Codex OAuth ChatModel；如果没有这一行，GUI 会重复实现 Responses 调用。
from learning_agent.models.base import ChatModel  # 新增代码+GuiModelFactory：声明返回值是 core 可用模型；如果没有这一行，adapter 和测试无法统一类型。
from learning_agent.models.fake import ToolCallingFakeModel  # 新增代码+GuiModelFactory：提供离线测试模型；如果没有这一行，单元测试会依赖真实 OpenAI。


GuiChatModelFactory = Callable[[GuiAgentRunRequest], ChatModel]  # 新增代码+GuiModelFactory：定义可注入模型工厂类型；如果没有这一行，RealHarness adapter 的测试替换点不清楚。
TEST_MODEL_ENV = "OPENHARNESS_GUI_AGENT_TEST_MODEL"  # 新增代码+GuiModelFactory：集中定义离线测试模型开关；如果没有这一行，测试和文档容易写错环境变量。
DEFAULT_CODEX_MODEL = "gpt-5.5"  # 新增代码+GuiModelFactory：集中定义 Codex OAuth 默认模型；如果没有这一行，空模型选择会散落到多处。


class GuiModelFactoryError(RuntimeError):  # 新增代码+GuiModelFactory：类段开始，承载模型工厂结构化失败；如果没有这个类，adapter 只能把未连接和不可用都当普通异常。
    def __init__(self, code: str, message: str, event_kind: str = "turn_failed") -> None:  # 新增代码+GuiModelFactory：函数段开始，保存错误码、说明和建议 GUI 事件；如果没有这段，调用方无法分类失败。
        super().__init__(message)  # 新增代码+GuiModelFactory：把可读说明交给 RuntimeError；如果没有这一行，日志里异常文本会为空。
        self.code = code  # 新增代码+GuiModelFactory：保存机器可读错误码；如果没有这一行，前端无法稳定处理 provider_not_connected。
        self.message = message  # 新增代码+GuiModelFactory：保存用户可读错误；如果没有这一行，adapter 需要依赖 str(error)。
        self.event_kind = event_kind  # 新增代码+GuiModelFactory：保存首个 GUI 诊断事件类型；如果没有这一行，adapter 无法发出 provider_not_connected 等一等事件。
    # 新增代码+GuiModelFactory：函数段结束，GuiModelFactoryError.__init__ 到此结束；如果没有边界说明，用户不容易看出错误字段范围。
# 新增代码+GuiModelFactory：类段结束，GuiModelFactoryError 到此结束；如果没有边界说明，用户不容易看出它只负责模型工厂失败。


def _workspace_path(workspace: str | Path) -> Path:  # 新增代码+GuiModelFactory：函数段开始，规范化工作区；如果没有这段，provider 设置和 secret store 可能读写不同目录。
    return Path(workspace or ".").expanduser().resolve()  # 新增代码+GuiModelFactory：返回绝对 Path；如果没有这一行，相对路径会跟随当前终端变化。
# 新增代码+GuiModelFactory：函数段结束，_workspace_path 到此结束；如果没有边界说明，用户不容易看出它只做路径清理。


def _test_model_enabled(request: GuiAgentRunRequest) -> bool:  # 新增代码+GuiModelFactory：函数段开始，判断是否使用离线假模型；如果没有这段，测试需要真实 OAuth。
    env_enabled = os.environ.get(TEST_MODEL_ENV, "").strip().casefold() in {"1", "true", "yes", "on", "enabled"}  # 新增代码+GuiModelFactory：读取环境开关；如果没有这一行，自动化测试无法稳定选择假模型。
    provider_is_test = request.provider_id.strip().casefold() in {"test", "test-fake", "fake"}  # 新增代码+GuiModelFactory：允许测试 provider id 触发假模型；如果没有这一行，合同测试要污染全局环境。
    return env_enabled or provider_is_test  # 新增代码+GuiModelFactory：任一条件命中就用假模型；如果没有这一行，函数没有输出。
# 新增代码+GuiModelFactory：函数段结束，_test_model_enabled 到此结束；如果没有边界说明，用户不容易看出它是测试入口。


def _build_test_model(request: GuiAgentRunRequest) -> ChatModel:  # 新增代码+GuiModelFactory：函数段开始，构造离线 probe 假模型；如果没有这段，Phase 0/1 无法在无网络环境验证主循环。
    if "READ_ONLY_TOOL_TRACE" in request.prompt:  # 新增代码+GuiModelFactoryVisibleToolTrace：识别只读工具轨迹烟测 prompt；如果没有这一行，可见 GUI 验收只能看到纯文本回答，看不到真实工具循环。
        read_call = ToolCall(name="read_file", arguments={"path": "AGENTS.md"}, call_id="gui_read_only_smoke")  # 新增代码+GuiModelFactoryVisibleToolTrace：让假模型请求读取项目说明文件；如果没有这一行，core agent 不会进入工具调用分支。
        return ToolCallingFakeModel([ModelMessage(tool_calls=[read_call]), ModelMessage(text="READ_ONLY_TOOL_TRACE_OK")])  # 新增代码+GuiModelFactoryVisibleToolTrace：安排先工具调用再最终回答；如果没有这一行，GUI 工具面板无法显示完整开始、完成、回答闭环。
    answer = "AGENT_HARNESS_SMOKE_OK" if "AGENT_HARNESS_SMOKE" in request.prompt else f"真实 agent 主循环已接入 GUI：{request.prompt}"  # 新增代码+GuiModelFactory：根据 smoke prompt 返回稳定文本；如果没有这一行，测试无法断言最终回答。
    return ToolCallingFakeModel([ModelMessage(text=answer)])  # 新增代码+GuiModelFactory：返回一次性假模型；如果没有这一行，LearningAgent 无法获得模型回复。
# 新增代码+GuiModelFactory：函数段结束，_build_test_model 到此结束；如果没有边界说明，用户不容易看出它只服务离线测试。


def _auth_record(settings: dict[str, Any], provider_id: str) -> dict[str, Any]:  # 新增代码+GuiModelFactory：函数段开始，读取 provider auth 记录；如果没有这段，后续会重复检查 dict 类型。
    auth = settings.get("auth", {}) if isinstance(settings.get("auth", {}), dict) else {}  # 新增代码+GuiModelFactory：安全读取 auth 区块；如果没有这一行，坏配置会抛异常。
    record = auth.get(provider_id, {}) if isinstance(auth.get(provider_id, {}), dict) else {}  # 新增代码+GuiModelFactory：安全读取指定 provider 记录；如果没有这一行，未知 provider 会出错。
    return record if isinstance(record, dict) else {}  # 新增代码+GuiModelFactory：保证返回 dict；如果没有这一行，调用方要再次防御。
# 新增代码+GuiModelFactory：函数段结束，_auth_record 到此结束；如果没有边界说明，用户不容易看出它只读配置。


def _selected_model_id(request: GuiAgentRunRequest, settings: dict[str, Any]) -> str:  # 新增代码+GuiModelFactory：函数段开始，确定真实模型 id；如果没有这段，空模型选择会导致远端请求失败。
    requested_model = request.model_id.strip()  # 新增代码+GuiModelFactory：优先使用前端传入模型；如果没有这一行，用户选择不会生效。
    selected_openai_model = str(settings.get("selected_openai_model_id", "") or "").strip()  # 新增代码+GuiModelFactory：读取 OpenAI 当前选择模型；如果没有这一行，重启后的选择无法恢复。
    default_model = str(settings.get("default_model_id", "") or "").strip()  # 新增代码+GuiModelFactory：读取通用默认模型；如果没有这一行，设置页默认值无法进入运行时。
    env_model = os.environ.get("CODEX_MODEL", "").strip()  # 新增代码+GuiModelFactory：兼容已有 CODEX_MODEL；如果没有这一行，老用户环境配置不会生效。
    return requested_model or selected_openai_model or default_model or env_model or DEFAULT_CODEX_MODEL  # 新增代码+GuiModelFactory：按优先级返回模型；如果没有这一行，工厂没有模型名。
# 新增代码+GuiModelFactory：函数段结束，_selected_model_id 到此结束；如果没有边界说明，用户不容易看出模型优先级。


class GuiOpenAIProviderTokenStore:  # 新增代码+GuiModelFactory：类段开始，让 CodexOAuthChatModel 读取 GUI provider secret store；如果没有这个类，真实 agent 会和设置页连接状态分裂。
    def __init__(self, workspace: str | Path) -> None:  # 新增代码+GuiModelFactory：函数段开始，保存 workspace；如果没有这段，token store 不知道从哪里读取 settings。
        self.workspace = _workspace_path(workspace)  # 新增代码+GuiModelFactory：保存规范化 workspace；如果没有这一行，读写路径可能变化。
    # 新增代码+GuiModelFactory：函数段结束，GuiOpenAIProviderTokenStore.__init__ 到此结束；如果没有边界说明，用户不容易看出初始化范围。

    def _settings_and_record(self) -> tuple[dict[str, Any], dict[str, Any]]:  # 新增代码+GuiModelFactory：函数段开始，读取 settings 和 OpenAI auth record；如果没有这段，load/save 会重复逻辑。
        settings = load_provider_settings(self.workspace)  # 新增代码+GuiModelFactory：读取 provider settings；如果没有这一行，store 不知道当前 OpenAI 是否连接。
        return settings, _auth_record(settings, "openai")  # 新增代码+GuiModelFactory：返回整体配置和 OpenAI 记录；如果没有这一行，调用方拿不到 record。
    # 新增代码+GuiModelFactory：函数段结束，_settings_and_record 到此结束；如果没有边界说明，用户不容易看出它只读配置。

    def load(self) -> CodexOAuthTokens | None:  # 新增代码+GuiModelFactory：函数段开始，按 CodexOAuthChatModel 期待的接口读取 token；如果没有这段，真实模型无法复用现有 OAuth adapter。
        settings, record = self._settings_and_record()  # 新增代码+GuiModelFactory：读取配置和认证记录；如果没有这一行，后续没有 secret_refs 来源。
        del settings  # 新增代码+GuiModelFactory：说明 load 当前不需要整体 settings；如果没有这一行，静态检查会提示未使用变量。
        if str(record.get("type", "")) != "oauth_real":  # 新增代码+GuiModelFactory：只接受真实 OAuth 连接；如果没有这一行，mock/API key 会被误当 ChatGPT OAuth。
            return None  # 新增代码+GuiModelFactory：非真实 OAuth 返回未登录；如果没有这一行，后续会读不存在字段。
        secret_refs = record.get("secret_refs", {}) if isinstance(record.get("secret_refs", {}), dict) else {}  # 新增代码+GuiModelFactory：读取 token 引用组；如果没有这一行，无法定位 access/refresh token。
        secret_store = make_provider_secret_store(self.workspace)  # 新增代码+GuiModelFactory：创建当前 secret store；如果没有这一行，os_encrypted/dev_json 无法统一读取。
        access_token = secret_store.get_secret(str(secret_refs.get("access_token", ""))) if secret_refs.get("access_token") else ""  # 新增代码+GuiModelFactory：读取 access token；如果没有这一行，模型请求无法鉴权。
        refresh_token = secret_store.get_secret(str(secret_refs.get("refresh_token", ""))) if secret_refs.get("refresh_token") else ""  # 新增代码+GuiModelFactory：读取 refresh token；如果没有这一行，过期后无法刷新。
        id_token = secret_store.get_secret(str(secret_refs.get("id_token", ""))) if secret_refs.get("id_token") else ""  # 新增代码+GuiModelFactory：读取 id token；如果没有这一行，刷新保存后账号上下文可能丢失。
        if not access_token:  # 新增代码+GuiModelFactory：access token 是最低可用条件；如果没有这一行，空 token 会进入 Authorization header。
            return None  # 新增代码+GuiModelFactory：缺 token 视为未连接；如果没有这一行，远端会返回更模糊的鉴权失败。
        fallback_expires_at = int((time.time() + 3600) * 1000)  # 新增代码+GuiModelFactory：旧 GUI 设置未存 expires_at 时给一小时保守窗口；如果没有这一行，模型会立刻尝试网页登录刷新。
        expires_at = int(record.get("expires_at", fallback_expires_at) or fallback_expires_at)  # 新增代码+GuiModelFactory：读取或补足过期时间；如果没有这一行，CodexOAuthChatModel 可能无法比较过期时间。
        return CodexOAuthTokens(access_token=access_token, refresh_token=refresh_token, expires_at=expires_at, account_id=str(record.get("account_id", "")) or None, id_token=id_token)  # 新增代码+GuiModelFactory：返回 OAuth token 对象；如果没有这一行，真实模型拿不到认证材料。
    # 新增代码+GuiModelFactory：函数段结束，GuiOpenAIProviderTokenStore.load 到此结束；如果没有边界说明，用户不容易看出读取范围。

    def save(self, tokens: CodexOAuthTokens) -> None:  # 新增代码+GuiModelFactory：函数段开始，刷新 token 后写回 GUI provider secret store；如果没有这段，刷新成功只在内存有效。
        settings, record = self._settings_and_record()  # 新增代码+GuiModelFactory：读取当前配置和认证记录；如果没有这一行，保存会覆盖其它 provider 设置。
        auth = settings.setdefault("auth", {})  # 新增代码+GuiModelFactory：确保 auth 区块存在；如果没有这一行，后续无法写 openai 记录。
        secret_store = make_provider_secret_store(self.workspace)  # 新增代码+GuiModelFactory：创建 secret store；如果没有这一行，新 token 无法落盘。
        secret_refs = dict(record.get("secret_refs", {}) if isinstance(record.get("secret_refs", {}), dict) else {})  # 新增代码+GuiModelFactory：复制旧 secret_refs；如果没有这一行，refresh/id token 引用可能丢失。
        secret_refs["access_token"] = secret_store.set_secret(secret_refs.get("access_token", safe_secret_ref("openai", "access_token")), tokens.access_token)  # 新增代码+GuiModelFactory：保存 access token 并复用旧引用；如果没有这一行，刷新后的 access token 不会进入 GUI。
        if tokens.refresh_token:  # 新增代码+GuiModelFactory：只有存在 refresh token 时才保存；如果没有这一行，空值会覆盖可用旧 token。
            secret_refs["refresh_token"] = secret_store.set_secret(secret_refs.get("refresh_token", safe_secret_ref("openai", "refresh_token")), tokens.refresh_token)  # 新增代码+GuiModelFactory：保存 refresh token；如果没有这一行，下次过期无法继续刷新。
        if tokens.id_token:  # 新增代码+GuiModelFactory：只有存在 id token 时才保存；如果没有这一行，空 id token 会覆盖旧记录。
            secret_refs["id_token"] = secret_store.set_secret(secret_refs.get("id_token", safe_secret_ref("openai", "id_token")), tokens.id_token)  # 新增代码+GuiModelFactory：保存 id token；如果没有这一行，账号信息可能丢失。
        auth["openai"] = {**record, "type": "oauth_real", "secret_refs": secret_refs, "account_id": tokens.account_id or record.get("account_id", ""), "expires_at": tokens.expires_at, "updated_at": time.time()}  # 新增代码+GuiModelFactory：更新不含明文 token 的认证记录；如果没有这一行，settings 不知道 token 已刷新。
        save_provider_settings(self.workspace, settings)  # 新增代码+GuiModelFactory：保存 provider settings；如果没有这一行，刷新记录重启后会丢失。
    # 新增代码+GuiModelFactory：函数段结束，GuiOpenAIProviderTokenStore.save 到此结束；如果没有边界说明，用户不容易看出写回范围。
# 新增代码+GuiModelFactory：类段结束，GuiOpenAIProviderTokenStore 到此结束；如果没有边界说明，用户不容易看出它是 token store 适配器。


def build_chat_model_for_gui_request(request: GuiAgentRunRequest) -> ChatModel:  # 新增代码+GuiModelFactory：函数段开始，根据 GUI request 创建 core ChatModel；如果没有这段，真实 harness adapter 不知道调用哪个模型。
    if _test_model_enabled(request):  # 新增代码+GuiModelFactory：离线测试优先走假模型；如果没有这一行，自动化 probe 会依赖真实账号。
        return _build_test_model(request)  # 新增代码+GuiModelFactory：返回测试模型；如果没有这一行，Phase 0 smoke 无法稳定完成。
    provider_id = request.provider_id.strip() or "openai"  # 新增代码+GuiModelFactory：默认 provider 是 OpenAI；如果没有这一行，前端未传 provider 时会失败。
    if provider_id != "openai":  # 新增代码+GuiModelFactory：Phase 1 只接 OpenAI ChatGPT OAuth；如果没有这一行，其它 provider 会被误走 Codex OAuth。
        raise GuiModelFactoryError("provider_not_connected", f"当前真实 agent harness 只支持 OpenAI ChatGPT OAuth，暂不支持 provider：{provider_id}", "provider_not_connected")  # 新增代码+GuiModelFactory：返回明确 provider 未接入；如果没有这一行，用户会看到泛化失败。
    workspace = _workspace_path(request.workspace)  # 新增代码+GuiModelFactory：规范化 workspace；如果没有这一行，settings 和 secret store 读取路径不稳定。
    settings = load_provider_settings(workspace)  # 新增代码+GuiModelFactory：读取 provider settings；如果没有这一行，无法判断 OpenAI 是否已连接。
    record = _auth_record(settings, "openai")  # 新增代码+GuiModelFactory：读取 OpenAI auth 记录；如果没有这一行，后续无法检查 oauth_real。
    if str(record.get("type", "")) != "oauth_real":  # 新增代码+GuiModelFactory：真实 harness 需要真实 ChatGPT OAuth；如果没有这一行，mock OAuth 会被误认为可调用模型。
        raise GuiModelFactoryError("provider_not_connected", "OpenAI ChatGPT OAuth 尚未真实连接，请先在 GUI Provider 设置中完成真实 OAuth。", "provider_not_connected")  # 新增代码+GuiModelFactory：返回稳定未连接错误；如果没有这一行，adapter 会尝试弹网页登录。
    if GuiOpenAIProviderTokenStore(workspace).load() is None:  # 新增代码+GuiModelFactory：确认 secret store 里确实能解出 token；如果没有这一行，孤儿 secret_refs 会造成远端 401。
        raise GuiModelFactoryError("provider_not_connected", "OpenAI OAuth token 不可用或已被清理，请重新连接 Provider。", "provider_not_connected")  # 新增代码+GuiModelFactory：返回稳定 token 缺失错误；如果没有这一行，用户无法知道需要重连。
    model_id = _selected_model_id(request, settings)  # 新增代码+GuiModelFactory：确定模型名；如果没有这一行，CodexOAuthChatModel 没有目标模型。
    return CodexOAuthChatModel(model=model_id, token_store=GuiOpenAIProviderTokenStore(workspace), login_callback=lambda: (_raise_login_required()))  # 新增代码+GuiModelFactory：返回复用 GUI token store 的真实模型；如果没有这一行，真实 agent 主循环无法请求模型。
# 新增代码+GuiModelFactory：函数段结束，build_chat_model_for_gui_request 到此结束；如果没有边界说明，用户不容易看出模型构造范围。


def _raise_login_required() -> CodexOAuthTokens:  # 新增代码+GuiModelFactory：函数段开始，阻止模型层私自弹网页登录；如果没有这段，GUI 运行中可能突然打开浏览器破坏可控验收。
    raise GuiModelFactoryError("provider_not_connected", "GUI 真实 agent 运行时不会自动弹网页登录；请先通过 Provider 设置完成 OAuth 连接。", "provider_not_connected")  # 新增代码+GuiModelFactory：抛出结构化未连接错误；如果没有这一行，模型层可能走旧交互式 OAuth。
# 新增代码+GuiModelFactory：函数段结束，_raise_login_required 到此结束；如果没有边界说明，用户不容易看出它是登录门禁。
