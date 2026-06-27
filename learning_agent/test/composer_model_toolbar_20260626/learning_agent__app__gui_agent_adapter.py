"""Desktop GUI agent adapter boundary."""  # 新增代码+GuiAgentAdapter：说明本模块隔离 GUI 与真实 agent/harness；如果没有这一行，后续容易把模型运行时直接导入 GUI bridge。

from __future__ import annotations  # 新增代码+GuiAgentAdapter：启用未来注解语法；如果没有这一行，Protocol 和 dataclass 类型标注在旧行为下更容易出问题。

import json  # 新增代码+GuiAgentAdapter：读取 golden trace fixture；如果没有这一行，fake adapter 无法回放固定事件语料。
import os  # 新增代码+DirectOAuthModelFactory：读取 direct OAuth 和 Codex 模型环境变量；如果没有这行代码，默认真实模型工厂无法按运行模式选择后端。
from dataclasses import dataclass, field  # 新增代码+GuiAgentAdapter：定义 adapter 请求和结果数据结构；如果没有这一行，边界会变成松散 dict。
from pathlib import Path  # 新增代码+GuiAgentAdapter：定位 repo 内 golden trace fixture；如果没有这一行，路径拼接容易在 Windows 上出错。
from typing import Any, Callable, Protocol  # 修改代码+真实模型GUI适配器：补充 Any 用来描述注入模型对象；如果没有这一行，真实模型 factory 的类型标注会不清楚。

from learning_agent.app.gui_protocol import make_event  # 新增代码+GuiAgentAdapter：复用 V2 事件生成 helper；如果没有这一行，adapter 事件形状会和协议模块分裂。


GuiEventEmitter = Callable[[dict[str, object]], None]  # 新增代码+GuiAgentAdapter：定义事件发射回调类型；如果没有这一行，adapter 不知道如何把事件交给 bridge。
GuiCancelChecker = Callable[[], bool]  # 新增代码+GuiAgentAdapter：定义取消检查回调类型；如果没有这一行，adapter 无法和 GUI cancel 按钮协作。
RealModelFactory = Callable[[], Any]  # 新增代码+真实模型GUI适配器：定义创建真实模型对象的回调类型；如果没有这一行，测试和 bridge 不容易注入模型实现。
ProviderConnectionReader = Callable[[], bool]  # 新增代码+真实模型GUI适配器：定义读取提供商连接状态的回调类型；如果没有这一行，adapter 会直接耦合设置存储。


@dataclass  # 新增代码+GuiAgentAdapter：自动生成请求对象初始化方法；如果没有这一行，请求字段要手写构造器。
class GuiAgentRunRequest:  # 新增代码+GuiAgentAdapter：请求类段开始，描述一次 GUI run；如果没有这个类，adapter 入参会散成多个字符串。
    session_id: str  # 新增代码+GuiAgentAdapter：保存会话 id；如果没有这一行，adapter 事件无法归属会话。
    turn_id: str  # 新增代码+GuiAgentAdapter：保存 turn id；如果没有这一行，事件无法关联消息。
    run_id: str  # 新增代码+GuiAgentAdapter：保存 run id；如果没有这一行，状态面板无法按运行聚合。
    prompt: str  # 新增代码+GuiAgentAdapter：保存用户 prompt；如果没有这一行，adapter 没有任务输入。
    trace_id: str = ""  # 新增代码+GuiAgentAdapter：可选 golden trace id；如果没有这一行，fake adapter 无法回放指定 GT 场景。
    mode: str = "fake"  # 新增代码+GuiAgentAdapter：保存请求模式；如果没有这一行，后续 real/fake 切换没有显式语义。
    provider_id: str = ""  # 新增代码+ComposerModelToolbar：保存 GUI 本轮选择的 provider；如果没有这一行，adapter 无法知道 prompt 来自哪个模型提供商。
    model_id: str = ""  # 新增代码+ComposerModelToolbar：保存 GUI 本轮选择的模型；如果没有这一行，真实模型路由无法消费用户的模型选择。
    reasoning_effort: str = ""  # 新增代码+ComposerModelToolbar：保存 GUI 本轮选择的推理强度；如果没有这一行，adapter 无法审计用户选择的是低/中/高/超高。
    permission_mode: str = ""  # 新增代码+ComposerModelToolbar：保存 GUI 本轮选择的权限模式；如果没有这一行，后端运行时不知道本轮是否为完全访问。
# 新增代码+GuiAgentAdapter：请求类段结束，GuiAgentRunRequest 到此结束；如果没有这个边界说明，用户不容易看出请求字段范围。


@dataclass  # 新增代码+GuiAgentAdapter：自动生成结果对象初始化方法；如果没有这一行，结果字段要手写构造器。
class GuiAgentRunResult:  # 新增代码+GuiAgentAdapter：结果类段开始，描述 adapter 终态；如果没有这个类，bridge 只能猜事件是否完成。
    status: str  # 新增代码+GuiAgentAdapter：保存 completed/failed/cancelled 等终态；如果没有这一行，bridge 不知道怎么同步消息状态。
    final_text: str = ""  # 新增代码+GuiAgentAdapter：保存最终文本；如果没有这一行，完成消息无法写回 session。
    error_code: str = ""  # 新增代码+GuiAgentAdapter：保存稳定错误码；如果没有这一行，前端无法机器处理 adapter 失败。
    error_message: str = ""  # 新增代码+GuiAgentAdapter：保存可读错误；如果没有这一行，用户只能看到泛化失败。
    events: list[dict[str, object]] = field(default_factory=list)  # 新增代码+GuiAgentAdapter：保存本次 run 事件副本；如果没有这一行，测试和诊断无法复盘 adapter 输出。
# 新增代码+GuiAgentAdapter：结果类段结束，GuiAgentRunResult 到此结束；如果没有这个边界说明，用户不容易看出结果字段范围。


class GuiAgentAdapter(Protocol):  # 新增代码+GuiAgentAdapter：接口段开始，定义 GUI adapter 必须实现的 run 方法；如果没有这个接口，fake 和 real adapter 容易分叉。
    def run(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+GuiAgentAdapter：声明 adapter run 合同；如果没有这一行，bridge 无法统一调用不同 adapter。
        ...  # 新增代码+GuiAgentAdapter：Protocol 方法占位；如果没有这一行，Python 语法不完整。
    # 新增代码+GuiAgentAdapter：接口方法段结束，run 到此结束；如果没有这个边界说明，用户不容易看出 adapter 主入口。
# 新增代码+GuiAgentAdapter：接口段结束，GuiAgentAdapter 到此结束；如果没有这个边界说明，用户不容易看出 fake/real 共同合同。


def _repo_root() -> Path:  # 新增代码+GuiAgentAdapter：函数段开始，定位仓库根目录；如果没有这段，golden fixture 路径会依赖当前工作目录。
    return Path(__file__).resolve().parents[2]  # 新增代码+GuiAgentAdapter：从 learning_agent/app 回到 repo 根；如果没有这一行，测试从别处运行会找不到 fixture。
# 新增代码+GuiAgentAdapter：函数段结束，_repo_root 到此结束；如果没有这个边界说明，用户不容易看出路径定位范围。


def _golden_fixture_path() -> Path:  # 新增代码+GuiAgentAdapter：函数段开始，返回 golden trace fixture 路径；如果没有这段，fake adapter 回放路径会散落。
    return _repo_root() / "apps" / "desktop" / "tests" / "fixtures" / "gui-v2-golden-events.json"  # 新增代码+GuiAgentAdapter：拼接 fixture 路径；如果没有这一行，GT 回放无法找到数据。
# 新增代码+GuiAgentAdapter：函数段结束，_golden_fixture_path 到此结束；如果没有这个边界说明，用户不容易看出 fixture 来源。


class GuiDirectOAuthCodexTokenStoreAdapter:  # 新增代码+DirectOAuthModelFactory：类段开始，把 GUI token store 适配成 CodexOAuthChatModel 需要的 load/save 协议；如果没有这个类，direct OAuth token 刷新不能写回 OpenHarness 加密存储。
    def __init__(self, token_store: Any | None = None, provider_id: str = "openai") -> None:  # 新增代码+DirectOAuthModelFactory：函数段开始，注入 GUI token store 和 provider id；如果没有这段代码，测试无法使用 fake store，真实运行也不知道读取哪个 provider。
        if token_store is None:  # 新增代码+DirectOAuthModelFactory：未注入时使用真实默认 token store；如果没有这行代码，真实 GUI direct OAuth 运行时没有 token 来源。
            from learning_agent.app.gui_provider_oauth_token_store import default_oauth_token_store  # 新增代码+DirectOAuthModelFactory：延迟导入默认 OS 加密 token store；如果没有这行代码，模块导入会提前触碰 Windows DPAPI 相关逻辑。

            token_store = default_oauth_token_store()  # 新增代码+DirectOAuthModelFactory：创建真实 OS 加密 token store；如果没有这行代码，适配器无法读取用户登录后的 token。
        self.token_store = token_store  # 新增代码+DirectOAuthModelFactory：保存底层 GUI token store；如果没有这行代码，load/save 无法访问实际存储。
        self.provider_id = str(provider_id or "openai").strip() or "openai"  # 新增代码+DirectOAuthModelFactory：保存 provider id 并兜底 openai；如果没有这行代码，空 provider 会导致 token 路径不稳定。
    # 新增代码+DirectOAuthModelFactory：函数段结束，GuiDirectOAuthCodexTokenStoreAdapter.__init__ 到此结束；如果没有边界说明，用户不容易看出初始化不读取 raw token。

    def load(self) -> Any | None:  # 新增代码+DirectOAuthModelFactory：函数段开始，按 CodexOAuthChatModel 协议读取 token；如果没有这段代码，模型调用前无法拿到 access/refresh token。
        from learning_agent.models.adapters import CodexOAuthTokens  # 新增代码+DirectOAuthModelFactory：延迟导入 token 数据对象避免 GUI 层启动时加载模型大模块；如果没有这行代码，load 无法返回模型期望类型。

        payload = self.token_store.get_tokens(self.provider_id)  # 新增代码+DirectOAuthModelFactory：从 GUI token store 读取后端 raw token；如果没有这行代码，direct OAuth 登录状态无法进入模型请求。
        if not payload:  # 新增代码+DirectOAuthModelFactory：处理未登录或损坏 token；如果没有这行代码，后续字段读取会抛异常。
            return None  # 新增代码+DirectOAuthModelFactory：未登录返回 None 让模型决定是否重新登录；如果没有这行代码，空 token 会被误当有效。
        return CodexOAuthTokens(access_token=str(payload.get("access_token", "")), refresh_token=str(payload.get("refresh_token", "")), expires_at=int(payload.get("expires_at") or 0), account_id=payload.get("account_id") or None, id_token=str(payload.get("id_token", "")))  # 新增代码+DirectOAuthModelFactory：把 GUI token dict 转成 Codex token 对象；如果没有这行代码，模型无法构造鉴权 header 或刷新 token。
    # 新增代码+DirectOAuthModelFactory：函数段结束，GuiDirectOAuthCodexTokenStoreAdapter.load 到此结束；如果没有边界说明，用户不容易看出 raw token 只留在后端内存。

    def save(self, tokens: Any) -> None:  # 新增代码+DirectOAuthModelFactory：函数段开始，按 CodexOAuthChatModel 协议保存刷新后的 token；如果没有这段代码，access token 刷新后不会持久化。
        self.token_store.set_tokens(self.provider_id, {"access_token": str(getattr(tokens, "access_token", "")), "refresh_token": str(getattr(tokens, "refresh_token", "")), "expires_at": int(getattr(tokens, "expires_at", 0) or 0), "account_id": getattr(tokens, "account_id", None), "id_token": str(getattr(tokens, "id_token", ""))})  # 新增代码+DirectOAuthModelFactory：把模型 token 对象写回 GUI token store；如果没有这行代码，刷新结果会丢失且下次仍用旧 token。
    # 新增代码+DirectOAuthModelFactory：函数段结束，GuiDirectOAuthCodexTokenStoreAdapter.save 到此结束；如果没有边界说明，用户不容易看出保存仍然不经过 renderer。
# 新增代码+DirectOAuthModelFactory：类段结束，GuiDirectOAuthCodexTokenStoreAdapter 到此结束；如果没有边界说明，用户不容易看出它只是协议桥。


def _int_env(name: str, default: int, minimum: int) -> int:  # 新增代码+DirectOAuthModelFactory：函数段开始，安全读取整数环境变量；如果没有这段代码，timeout 配置错误会让 GUI 启动失败。
    raw_value = os.environ.get(name, str(default)).strip()  # 新增代码+DirectOAuthModelFactory：读取原始字符串并兜底默认值；如果没有这行代码，空变量会进入 int 转换。
    try:  # 新增代码+DirectOAuthModelFactory：捕获非法数字；如果没有这行代码，用户填错环境变量会抛到 GUI。
        return max(int(raw_value), int(minimum))  # 新增代码+DirectOAuthModelFactory：返回不低于下限的整数；如果没有这行代码，超短 timeout 会制造假失败。
    except ValueError:  # 新增代码+DirectOAuthModelFactory：处理非数字配置；如果没有这行代码，错误配置无法回退。
        return int(default)  # 新增代码+DirectOAuthModelFactory：非法值回到默认值；如果没有这行代码，GUI 无法稳态启动。
# 新增代码+DirectOAuthModelFactory：函数段结束，_int_env 到此结束；如果没有边界说明，用户不容易看出它只读环境变量。


def _default_direct_oauth_model_factory() -> Any:  # 新增代码+DirectOAuthModelFactory：函数段开始，创建 direct OAuth 的 CodexOAuthChatModel；如果没有这段代码，direct OAuth 已连接后主聊天仍不能调用真实模型。
    from learning_agent.app.gui_provider_openai_auth_config import build_openai_auth_config  # 新增代码+DirectOAuthModelFactory：复用 direct OAuth 三重门禁和显式 client id；如果没有这行代码，模型层可能绕过安全配置。
    from learning_agent.models.adapters import CodexOAuthChatModel  # 新增代码+DirectOAuthModelFactory：延迟导入 Codex OAuth 模型；如果没有这行代码，工厂无法创建真实模型对象。

    config = build_openai_auth_config()  # 新增代码+DirectOAuthModelFactory：读取并校验 direct OAuth 配置；如果没有这行代码，缺 client id 或非 OS 加密也可能继续运行。
    model_name = os.environ.get("CODEX_MODEL", "gpt-5.5").strip() or "gpt-5.5"  # 新增代码+DirectOAuthModelFactory：读取用户配置模型名；如果没有这行代码，direct OAuth 路径无法选择目标模型。
    oauth_timeout_seconds = _int_env("CODEX_OAUTH_TIMEOUT_SECONDS", 300, 60)  # 新增代码+DirectOAuthModelFactory：读取 OAuth 等待超时；如果没有这行代码，重新登录等待时间无法配置。
    sse_timeout_seconds = _int_env("CODEX_OAUTH_SSE_READ_TIMEOUT_SECONDS", 240, 30)  # 新增代码+DirectOAuthModelFactory：读取 Codex SSE 总超时；如果没有这行代码，真实模型流式读取可能无限等待。
    token_store = GuiDirectOAuthCodexTokenStoreAdapter()  # 新增代码+DirectOAuthModelFactory：创建 GUI token store 适配器；如果没有这行代码，模型无法读取 direct OAuth 登录 token。
    return CodexOAuthChatModel(model=model_name, token_store=token_store, oauth_timeout_seconds=oauth_timeout_seconds, sse_read_timeout_seconds=sse_timeout_seconds, client_id=config.client_id)  # 新增代码+DirectOAuthModelFactory：返回绑定 OpenHarness client id 的 Codex OAuth 模型；如果没有这行代码，refresh/token exchange 可能误用 OpenCode client id。
# 新增代码+DirectOAuthModelFactory：函数段结束，_default_direct_oauth_model_factory 到此结束；如果没有边界说明，用户不容易看出它只创建模型不发请求。


def _default_real_model_factory() -> Any:  # 新增代码+真实模型GUI适配器：函数段开始，创建默认 Codex CLI 模型桥；如果没有这段，真实 adapter 只能靠测试注入模型。
    if os.environ.get("OPENHARNESS_OPENAI_AUTH_MODE", "mock").strip().lower() == "direct_oauth":  # 新增代码+DirectOAuthModelFactory：direct OAuth 模式下切到 CodexOAuthChatModel；如果没有这行代码，GUI 登录成功后仍会尝试 Codex CLI。
        return _default_direct_oauth_model_factory()  # 新增代码+DirectOAuthModelFactory：返回 direct OAuth 模型；如果没有这行代码，token store 适配器不会进入真实运行时。
    from learning_agent.models.adapters import CodexCliChatModel  # 新增代码+真实模型GUI适配器：延迟导入 CodexCliChatModel；如果没有这一行，默认真实模式无法调用官方 Codex CLI。

    return CodexCliChatModel.from_env(cwd=_repo_root())  # 新增代码+真实模型GUI适配器：使用仓库根目录创建模型；如果没有这一行，真实模型调用没有稳定工作目录。
# 新增代码+真实模型GUI适配器：函数段结束，_default_real_model_factory 到此结束；如果没有这个边界说明，用户不容易看出默认模型来源。


def _looks_like_safety_refusal_prompt(prompt: str) -> bool:  # 新增代码+GuiSafetyRefusal：函数段开始，识别 GUI 可见验收里的高风险请求；如果没有这段，真实用户式安全拒绝 prompt 只能靠隐藏 trace_id 触发。
    lowered_prompt = prompt.casefold()  # 新增代码+GuiSafetyRefusal：把英文提示转成大小写无关文本；如果没有这一行，Unsafe/BYPASS 这类写法可能漏判。
    refusal_markers = (  # 新增代码+GuiSafetyRefusal：集中维护安全拒绝触发词；如果没有这一段，判断条件会散落在 run 主流程里。
        "绕过本机权限",  # 新增代码+GuiSafetyRefusal：覆盖中文“绕过权限”场景；如果没有这一行，用户常见中文验收 prompt 不会触发拒绝。
        "绕过权限",  # 新增代码+GuiSafetyRefusal：覆盖较短中文表达；如果没有这一行，稍微简写的中文请求会被当成普通回答。
        "高风险操作",  # 新增代码+GuiSafetyRefusal：覆盖中文高风险操作表达；如果没有这一行，危险动作验收不能稳定出现安全拒绝。
        "直接控制系统",  # 新增代码+GuiSafetyRefusal：覆盖请求直接接管系统的中文表达；如果没有这一行，桌面控制越权语义可能漏判。
        "unsafe",  # 新增代码+GuiSafetyRefusal：覆盖英文 unsafe 触发词；如果没有这一行，英文安全拒绝验收不稳定。
        "bypass permission",  # 新增代码+GuiSafetyRefusal：覆盖英文绕过权限表达；如果没有这一行，英文用户 prompt 不能触发同一 GUI 路径。
        "bypass local permission",  # 新增代码+GuiSafetyRefusal：覆盖更具体的英文绕过本机权限表达；如果没有这一行，桌面权限绕过请求可能被误答。
    )  # 新增代码+GuiSafetyRefusal：触发词元组结束；如果没有这一行，Python 元组语法不完整。
    return any(marker in lowered_prompt for marker in refusal_markers)  # 新增代码+GuiSafetyRefusal：只要命中一个触发词就拒绝；如果没有这一行，函数不会输出判定结果。
# 新增代码+GuiSafetyRefusal：函数段结束，_looks_like_safety_refusal_prompt 到此结束；如果没有这个边界说明，用户不容易看出安全拒绝判定范围。


class FakeStreamingGuiAgentAdapter:  # 新增代码+GuiAgentAdapter：类段开始，提供 deterministic fake streaming adapter；如果没有这个类，V2-Core 会被真实模型不确定性污染。
    def _emit(self, events: list[dict[str, object]], emit_event: GuiEventEmitter, event: dict[str, object]) -> None:  # 新增代码+GuiAgentAdapter：函数段开始，统一记录并发射事件；如果没有这段，测试和 bridge 看到的事件可能不一致。
        events.append(event)  # 新增代码+GuiAgentAdapter：保存事件副本；如果没有这一行，GuiAgentRunResult 无法复盘事件。
        emit_event(event)  # 新增代码+GuiAgentAdapter：把事件交给 bridge 或测试；如果没有这一行，UI 收不到 adapter 输出。
    # 新增代码+GuiAgentAdapter：函数段结束，FakeStreamingGuiAgentAdapter._emit 到此结束；如果没有这个边界说明，用户不容易看出发射逻辑。

    def _replay_trace(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+GuiAgentAdapter：函数段开始，回放 golden trace；如果没有这段，前端和 bridge 测试无法共享固定事件语料。
        traces = json.loads(_golden_fixture_path().read_text(encoding="utf-8"))  # 新增代码+GuiAgentAdapter：读取 JSON fixture；如果没有这一行，adapter 无法获得 GT 场景。
        trace = next((item for item in traces if item.get("id") == request.trace_id), None)  # 新增代码+GuiAgentAdapter：按 trace_id 查找场景；如果没有这一行，无法选择指定 GT。
        if not isinstance(trace, dict):  # 新增代码+GuiAgentAdapter：处理未知 trace；如果没有这一行，后续访问会报错。
            failed_event = make_event("turn_failed", 1, {"error_code": "trace_not_found", "error": f"Golden trace not found: {request.trace_id}"}, run_id=request.run_id, turn_id=request.turn_id)  # 新增代码+GuiAgentAdapter：构造 trace 缺失失败事件；如果没有这一行，未知 GT 会静默失败。
            emit_event(failed_event)  # 新增代码+GuiAgentAdapter：发出失败事件；如果没有这一行，UI 不知道回放失败。
            return GuiAgentRunResult(status="failed", error_code="trace_not_found", error_message=str(failed_event["payload"]))  # 新增代码+GuiAgentAdapter：返回失败结果；如果没有这一行，bridge 不知道终态。
        events: list[dict[str, object]] = []  # 新增代码+GuiAgentAdapter：保存回放事件；如果没有这一行，结果无法复盘。
        for raw_event in trace.get("events", []):  # 新增代码+GuiAgentAdapter：按 fixture 顺序遍历事件；如果没有这一行，回放不会发出事件。
            if is_cancelled():  # 新增代码+GuiAgentAdapter：每个事件前检查取消；如果没有这一行，回放无法响应取消。
                cancel_event = make_event("turn_cancelled", int(raw_event.get("sequence", 0)), {"status": "cancelled"}, run_id=request.run_id, turn_id=request.turn_id)  # 新增代码+GuiAgentAdapter：构造取消事件；如果没有这一行，取消没有终态事件。
                self._emit(events, emit_event, cancel_event)  # 新增代码+GuiAgentAdapter：发出取消事件；如果没有这一行，UI 无法进入取消态。
                return GuiAgentRunResult(status="cancelled", events=events)  # 新增代码+GuiAgentAdapter：返回取消结果；如果没有这一行，bridge 会继续当完成。
            event = make_event(str(raw_event.get("kind", "heartbeat")), int(raw_event.get("sequence", 0)), raw_event.get("payload", {}) if isinstance(raw_event.get("payload", {}), dict) else {}, run_id=request.run_id, turn_id=request.turn_id)  # 新增代码+GuiAgentAdapter：把 fixture 事件转成当前 run 身份；如果没有这一行，事件会带旧 turn/run。
            self._emit(events, emit_event, event)  # 新增代码+GuiAgentAdapter：发出回放事件；如果没有这一行，前端收不到 GT 事件。
        final_event = events[-1] if events else {}  # 新增代码+GuiAgentAdapter：读取最后事件；如果没有这一行，final_text 提取没有来源。
        final_payload = final_event.get("payload", {}) if isinstance(final_event.get("payload", {}), dict) else {}  # 新增代码+GuiAgentAdapter：安全读取最后 payload；如果没有这一行，坏 fixture 会拖垮回放。
        return GuiAgentRunResult(status="completed", final_text=str(final_payload.get("final_text", "")), events=events)  # 新增代码+GuiAgentAdapter：返回完成结果；如果没有这一行，bridge 不知道回放完成。
    # 新增代码+GuiAgentAdapter：函数段结束，FakeStreamingGuiAgentAdapter._replay_trace 到此结束；如果没有这个边界说明，用户不容易看出回放范围。

    def run(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+GuiAgentAdapter：函数段开始，执行 deterministic fake streaming；如果没有这段，V2-Core 没有稳定 adapter。
        if request.trace_id:  # 新增代码+GuiAgentAdapter：优先处理 golden trace 回放；如果没有这一行，指定 trace_id 会被普通回答忽略。
            return self._replay_trace(request, emit_event, is_cancelled)  # 新增代码+GuiAgentAdapter：执行 fixture 回放；如果没有这一行，GT 测试无法通过。
        events: list[dict[str, object]] = []  # 新增代码+GuiAgentAdapter：保存本次 fake 事件；如果没有这一行，结果无法复盘。
        try:  # 新增代码+GuiAgentAdapter：捕获 deterministic fake 异常；如果没有这一行，失败会变成线程崩溃。
            if "__adapter_fail__" in request.prompt or "__fail__" in request.prompt:  # 修改代码+GuiAgentAdapter：识别 fake 专用和旧生命周期失败触发词；如果没有这一行，默认 V2 路径会漏掉旧失败验收。
                raise RuntimeError("deterministic fake adapter failure")  # 新增代码+GuiAgentAdapter：抛出可控异常；如果没有这一行，失败路径没有实际异常。
            self._emit(events, emit_event, make_event("turn_started", 1, {"status": "running"}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiAgentAdapter：发出 turn_started；如果没有这一行，前端看不到运行起点。
            delta_text = f"OpenHarness Desktop 正在处理：{request.prompt}"  # 新增代码+GuiAgentAdapter：构造 deterministic delta 文本；如果没有这一行，message_delta 没有内容。
            self._emit(events, emit_event, make_event("message_delta", 2, {"text_delta": delta_text}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiAgentAdapter：发出流式文本增量；如果没有这一行，GUI 无法测试打字式输出。
            if _looks_like_safety_refusal_prompt(request.prompt):  # 新增代码+GuiSafetyRefusal：在普通流式开头后拦截高风险请求；如果没有这一行，安全拒绝不会进入真实可见 GUI 消息流。
                refusal_text = "我不能绕过本机权限或执行高风险操作；可以改为说明安全边界、权限确认流程，或生成低风险的模拟验收步骤。"  # 新增代码+GuiSafetyRefusal：构造可见安全拒绝正文；如果没有这一行，用户只会看到空的拒绝事件。
                self._emit(events, emit_event, make_event("safety_refusal", 3, {"text": refusal_text, "policy": "desktop_permission_safety"}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiSafetyRefusal：发出一等安全拒绝事件；如果没有这一行，前端无法显示拒绝标签。
                return GuiAgentRunResult(status="completed", final_text=refusal_text, events=events)  # 新增代码+GuiSafetyRefusal：以完成态结束拒绝轮次；如果没有这一行，bridge 不会释放 active turn。
            if is_cancelled():  # 新增代码+GuiAgentAdapter：delta 后检查取消；如果没有这一行，取消会等到完成后才生效。
                self._emit(events, emit_event, make_event("turn_cancelled", 3, {"status": "cancelled"}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiAgentAdapter：发出取消终态；如果没有这一行，前端无法进入 cancelled。
                return GuiAgentRunResult(status="cancelled", events=events)  # 新增代码+GuiAgentAdapter：返回取消结果；如果没有这一行，bridge 会误写 completed。
            final_text = f"OpenHarness Desktop 已完成 fake streaming 回答：{request.prompt}"  # 新增代码+GuiAgentAdapter：构造 deterministic final_text；如果没有这一行，完成消息没有正文。
            self._emit(events, emit_event, make_event("message_completed", 3, {"final_text": final_text}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiAgentAdapter：发出完成事件；如果没有这一行，前端无法进入 completed。
            return GuiAgentRunResult(status="completed", final_text=final_text, events=events)  # 新增代码+GuiAgentAdapter：返回完成结果；如果没有这一行，bridge 不知道 final_text。
        except Exception as error:  # 新增代码+GuiAgentAdapter：捕获 fake adapter 失败；如果没有这一行，异常不会变成 turn_failed。
            failed_event = make_event("turn_failed", len(events) + 1, {"status": "failed", "error_code": "adapter_failed", "error": str(error)}, run_id=request.run_id, turn_id=request.turn_id)  # 新增代码+GuiAgentAdapter：构造结构化失败事件；如果没有这一行，GUI 无法显示失败原因。
            self._emit(events, emit_event, failed_event)  # 新增代码+GuiAgentAdapter：发出失败事件；如果没有这一行，前端状态机不会进入 failed。
            return GuiAgentRunResult(status="failed", error_code="adapter_failed", error_message=str(error), events=events)  # 新增代码+GuiAgentAdapter：返回失败结果；如果没有这一行，bridge 不知道终态。
    # 新增代码+GuiAgentAdapter：函数段结束，FakeStreamingGuiAgentAdapter.run 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行范围。
# 新增代码+GuiAgentAdapter：类段结束，FakeStreamingGuiAgentAdapter 到此结束；如果没有这个边界说明，用户不容易看出 fake adapter 范围。


class RealModelGuiAgentAdapter:  # 新增代码+真实模型GUI适配器：类段开始，把 GUI run 接到真实模型接口；如果没有这个类，桌面外壳只能继续 fake streaming。
    def __init__(self, model_factory: RealModelFactory | None = None, connected_provider_reader: ProviderConnectionReader | None = None, delta_chunk_size: int = 600) -> None:  # 新增代码+真实模型GUI适配器：函数段开始，注入模型工厂和连接状态读取器；如果没有这段，真实 adapter 很难测试和替换后端。
        self.model_factory = model_factory or _default_real_model_factory  # 新增代码+真实模型GUI适配器：保存模型工厂；如果没有这一行，adapter 不知道如何创建 CodexCliChatModel。
        self.connected_provider_reader = connected_provider_reader or (lambda: False)  # 新增代码+真实模型GUI适配器：保存连接门禁读取器；如果没有这一行，未授权状态也可能触发模型调用。
        self.delta_chunk_size = max(1, int(delta_chunk_size))  # 新增代码+真实模型GUI适配器：保存流式切片大小且保证至少为 1；如果没有这一行，切片大小为 0 会导致循环异常。
    # 新增代码+真实模型GUI适配器：函数段结束，RealModelGuiAgentAdapter.__init__ 到此结束；如果没有这个边界说明，用户不容易看出依赖注入范围。

    def _emit(self, events: list[dict[str, object]], emit_event: GuiEventEmitter, event: dict[str, object]) -> None:  # 新增代码+真实模型GUI适配器：函数段开始，统一记录并发射真实模型事件；如果没有这段，结果 events 和 GUI 收到的事件可能不一致。
        events.append(event)  # 新增代码+真实模型GUI适配器：保存事件副本；如果没有这一行，GuiAgentRunResult 无法复盘真实模型输出。
        emit_event(event)  # 新增代码+真实模型GUI适配器：把事件交给 bridge 或测试；如果没有这一行，前端收不到真实模型事件。
    # 新增代码+真实模型GUI适配器：函数段结束，RealModelGuiAgentAdapter._emit 到此结束；如果没有这个边界说明，用户不容易看出发射逻辑。

    def _text_chunks(self, text: str) -> list[str]:  # 新增代码+真实模型GUI适配器：函数段开始，把最终文本拆成 GUI 可显示的 delta；如果没有这段，真实模型只能一次性完成没有流式体验。
        if not text:  # 新增代码+真实模型GUI适配器：处理空文本回答；如果没有这一行，空回答不会产生 message_delta，前端可能缺少中间态。
            return [""]  # 新增代码+真实模型GUI适配器：为空文本保留一个空 delta；如果没有这一行，事件顺序会少掉 message_delta。
        return [text[index : index + self.delta_chunk_size] for index in range(0, len(text), self.delta_chunk_size)]  # 新增代码+真实模型GUI适配器：按固定长度切片；如果没有这一行，长回答会变成单个巨大事件。
    # 新增代码+真实模型GUI适配器：函数段结束，RealModelGuiAgentAdapter._text_chunks 到此结束；如果没有这个边界说明，用户不容易看出流式切片范围。

    def _fail(self, request: GuiAgentRunRequest, events: list[dict[str, object]], emit_event: GuiEventEmitter, sequence: int, error_code: str, message: str) -> GuiAgentRunResult:  # 新增代码+真实模型GUI适配器：函数段开始，统一返回结构化失败；如果没有这段，错误事件和结果错误码容易不一致。
        failed_event = make_event("turn_failed", sequence, {"status": "failed", "error_code": error_code, "error": message}, run_id=request.run_id, turn_id=request.turn_id)  # 新增代码+真实模型GUI适配器：构造失败事件；如果没有这一行，前端无法展示真实模型失败原因。
        self._emit(events, emit_event, failed_event)  # 新增代码+真实模型GUI适配器：发出失败事件；如果没有这一行，GUI 状态机不会进入 failed。
        return GuiAgentRunResult(status="failed", error_code=error_code, error_message=message, events=events)  # 新增代码+真实模型GUI适配器：返回失败结果；如果没有这一行，bridge 不知道真实模型轮次已经失败。
    # 新增代码+真实模型GUI适配器：函数段结束，RealModelGuiAgentAdapter._fail 到此结束；如果没有这个边界说明，用户不容易看出失败封装范围。

    def _cancel(self, request: GuiAgentRunRequest, events: list[dict[str, object]], emit_event: GuiEventEmitter, sequence: int) -> GuiAgentRunResult:  # 新增代码+真实模型GUI适配器：函数段开始，统一返回取消终态；如果没有这段，取消事件和结果状态容易分裂。
        self._emit(events, emit_event, make_event("turn_cancelled", sequence, {"status": "cancelled"}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型GUI适配器：发出取消事件；如果没有这一行，前端取消按钮不会产生可见终态。
        return GuiAgentRunResult(status="cancelled", events=events)  # 新增代码+真实模型GUI适配器：返回取消结果；如果没有这一行，bridge 可能误写 completed。
    # 新增代码+真实模型GUI适配器：函数段结束，RealModelGuiAgentAdapter._cancel 到此结束；如果没有这个边界说明，用户不容易看出取消封装范围。

    def run(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+真实模型GUI适配器：函数段开始，执行一次真实模型 GUI 轮次；如果没有这段，桌面外壳无法真正通过模型生成回答。
        events: list[dict[str, object]] = []  # 新增代码+真实模型GUI适配器：保存本次真实模型事件；如果没有这一行，结果无法复盘。
        self._emit(events, emit_event, make_event("turn_started", 1, {"status": "running", "mode": "real"}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型GUI适配器：发出真实模式启动事件；如果没有这一行，前端看不到运行起点。
        if is_cancelled():  # 新增代码+真实模型GUI适配器：模型调用前检查取消；如果没有这一行，用户取消后仍可能调用模型。
            return self._cancel(request, events, emit_event, 2)  # 新增代码+真实模型GUI适配器：返回取消终态；如果没有这一行，取消不会立即生效。
        try:  # 新增代码+真实模型GUI适配器：捕获连接读取和模型调用异常；如果没有这一行，真实模型错误会让后台线程崩溃。
            if not self.connected_provider_reader():  # 新增代码+真实模型GUI适配器：检查 OpenAI/Codex 登录状态；如果没有这一行，未连接时也会把 prompt 发给模型层。
                return self._fail(request, events, emit_event, 2, "real_model_not_connected", "OpenAI provider is not connected for real model mode.")  # 新增代码+真实模型GUI适配器：返回未连接失败；如果没有这一行，用户会看到假成功而不是去设置里连接。
            model = self.model_factory()  # 新增代码+真实模型GUI适配器：创建真实模型对象；如果没有这一行，adapter 没有后端可调用。
            model_message = model.chat([{"role": "user", "content": request.prompt}], [])  # 新增代码+真实模型GUI适配器：把用户 prompt 交给模型接口；如果没有这一行，真实模型不会参与回答。
            if is_cancelled():  # 新增代码+真实模型GUI适配器：模型返回后再次检查取消；如果没有这一行，长调用结束后可能覆盖用户取消。
                return self._cancel(request, events, emit_event, 2)  # 新增代码+真实模型GUI适配器：返回取消终态；如果没有这一行，取消轮次可能继续写完成。
            tool_calls = getattr(model_message, "tool_calls", [])  # 新增代码+真实模型GUI适配器：读取模型请求的工具调用；如果没有这一行，未接线工具会被误当作普通回答。
            if tool_calls:  # 新增代码+真实模型GUI适配器：V1A 先显式拒绝工具调用；如果没有这一行，模型工具调用可能被静默丢弃。
                return self._fail(request, events, emit_event, 2, "real_model_tools_not_connected", "Real model requested tool calls, but GUI tool execution is not connected yet.")  # 新增代码+真实模型GUI适配器：返回工具未接线失败；如果没有这一行，用户会以为工具已经执行。
            final_text = str(getattr(model_message, "text", ""))  # 新增代码+真实模型GUI适配器：读取模型文本并转成字符串；如果没有这一行，最终回答可能不是前端可显示文本。
            sequence = 2  # 新增代码+真实模型GUI适配器：初始化后续事件序号；如果没有这一行，事件顺序会不稳定。
            for text_delta in self._text_chunks(final_text):  # 新增代码+真实模型GUI适配器：逐块发出文本增量；如果没有这一行，GUI 不会显示真实模型流式过程。
                if is_cancelled():  # 新增代码+真实模型GUI适配器：每个 delta 前检查取消；如果没有这一行，用户取消后仍会继续刷文本。
                    return self._cancel(request, events, emit_event, sequence)  # 新增代码+真实模型GUI适配器：返回取消终态；如果没有这一行，取消后的事件流可能继续。
                self._emit(events, emit_event, make_event("message_delta", sequence, {"text_delta": text_delta}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型GUI适配器：发出模型文本增量；如果没有这一行，前端看不到真实回答内容。
                sequence += 1  # 新增代码+真实模型GUI适配器：递增事件序号；如果没有这一行，多个事件会共享 sequence。
            self._emit(events, emit_event, make_event("message_completed", sequence, {"final_text": final_text}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+真实模型GUI适配器：发出完成事件；如果没有这一行，前端不会进入 completed。
            return GuiAgentRunResult(status="completed", final_text=final_text, events=events)  # 新增代码+真实模型GUI适配器：返回完成结果；如果没有这一行，bridge 不知道最终文本。
        except Exception as error:  # 新增代码+真实模型GUI适配器：把真实模型异常转换为稳定失败；如果没有这一行，线程异常会让 GUI 看不到原因。
            return self._fail(request, events, emit_event, len(events) + 1, "real_model_failed", str(error))  # 新增代码+真实模型GUI适配器：返回真实模型失败；如果没有这一行，异常无法进入事件流和状态面板。
    # 新增代码+真实模型GUI适配器：函数段结束，RealModelGuiAgentAdapter.run 到此结束；如果没有这个边界说明，用户不容易看出真实模型主流程。
# 新增代码+真实模型GUI适配器：类段结束，RealModelGuiAgentAdapter 到此结束；如果没有这个边界说明，用户不容易看出真实 adapter 范围。


class DefaultHarnessGuiAgentAdapter:  # 新增代码+GuiAgentAdapter：类段开始，真实 harness adapter 的 feature-flagged shell；如果没有这个类，调用方无法显式请求真实模式并得到稳定失败。
    def __init__(self, enabled: bool = False) -> None:  # 新增代码+GuiAgentAdapter：函数段开始，保存真实 adapter 是否启用；如果没有这段，真实入口可能被误用。
        self.enabled = enabled  # 新增代码+GuiAgentAdapter：保存 feature flag；如果没有这一行，禁用状态无法判断。
    # 新增代码+GuiAgentAdapter：函数段结束，DefaultHarnessGuiAgentAdapter.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def run(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, _is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+GuiAgentAdapter：函数段开始，真实 harness adapter 暂不接线；如果没有这段，显式真实模式没有稳定响应。
        if not self.enabled:  # 新增代码+GuiAgentAdapter：真实 adapter 未启用时拒绝；如果没有这一行，V2-Core 可能误入真实 runtime。
            message = "Default harness GUI adapter is not enabled in V2-Core."  # 新增代码+GuiAgentAdapter：构造低敏错误信息；如果没有这一行，用户看不到为什么不可用。
            emit_event(make_event("turn_failed", 1, {"status": "failed", "error_code": "adapter_unavailable", "error": message}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiAgentAdapter：发出 adapter_unavailable 失败事件；如果没有这一行，前端无法显示真实模式被禁用。
            return GuiAgentRunResult(status="failed", error_code="adapter_unavailable", error_message=message)  # 新增代码+GuiAgentAdapter：返回稳定失败结果；如果没有这一行，bridge 不知道终态。
        message = "Default harness GUI adapter real entry point is intentionally deferred."  # 新增代码+GuiAgentAdapter：构造启用但未实现的错误；如果没有这一行，真实 adapter 仍不清楚为何失败。
        emit_event(make_event("turn_failed", 1, {"status": "failed", "error_code": "adapter_unavailable", "error": message}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+GuiAgentAdapter：发出未实现失败事件；如果没有这一行，前端无法显示真实 adapter 未完成。
        return GuiAgentRunResult(status="failed", error_code="adapter_unavailable", error_message=message)  # 新增代码+GuiAgentAdapter：返回未实现失败结果；如果没有这一行，调用方会误以为成功。
    # 新增代码+GuiAgentAdapter：函数段结束，DefaultHarnessGuiAgentAdapter.run 到此结束；如果没有这个边界说明，用户不容易看出真实 adapter shell 范围。
# 新增代码+GuiAgentAdapter：类段结束，DefaultHarnessGuiAgentAdapter 到此结束；如果没有这个边界说明，用户不容易看出真实 adapter 仍未接线。
