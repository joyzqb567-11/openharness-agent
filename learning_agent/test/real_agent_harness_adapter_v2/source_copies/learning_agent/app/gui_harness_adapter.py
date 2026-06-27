"""把 Desktop GUI 请求接入 core LearningAgent 主循环。"""  # 新增代码+RealHarnessAdapter：本模块是 GUI 到真实 agent 的最小适配层；如果没有这一行，读者会难以区分它和 fake adapter。

from __future__ import annotations  # 新增代码+RealHarnessAdapter：启用延迟类型解析；如果没有这一行，类型注解更容易产生循环导入问题。

import threading  # 新增代码+RealHarnessAdapter：创建 stop_event 让 GUI cancel 能传进 core agent；如果没有这一行，真实主循环无法协作取消。
from pathlib import Path  # 新增代码+RealHarnessAdapter：规范化 workspace；如果没有这一行，LearningAgent 的工作区路径可能不稳定。
from typing import Callable  # 新增代码+RealHarnessAdapter：声明注入回调类型；如果没有这一行，模型工厂和权限回调边界不清楚。

from learning_agent.app.gui_agent_adapter import GuiAgentRunRequest, GuiAgentRunResult, GuiCancelChecker, GuiEventEmitter  # 新增代码+RealHarnessAdapter：复用 GUI adapter 合同对象；如果没有这一行，真实 adapter 会另起一套请求/结果结构。
from learning_agent.app.gui_agent_event_mapper import agent_event_to_gui_events  # 新增代码+RealHarnessAdapter：复用 AgentEvent 到 GUI 事件映射；如果没有这一行，adapter 会手写易漂移的事件转换。
from learning_agent.app.gui_context import responses_input_to_compact_messages  # 新增代码+RealHarnessAdapter：把 GUI Responses input 反转成 core 可读 role/content 历史；如果没有这一行，LearningAgent 会丢失 GUI 历史。
from learning_agent.app.gui_model_factory import GuiChatModelFactory, GuiModelFactoryError, build_chat_model_for_gui_request  # 新增代码+RealHarnessAdapter：复用模型工厂；如果没有这一行，adapter 会直接读 token 和 provider 设置。
from learning_agent.app.gui_protocol import make_event  # 新增代码+RealHarnessAdapter：复用 GUI V2 事件工厂；如果没有这一行，runtime_path 和失败事件形状会分裂。
from learning_agent.core.events import AgentEvent  # 新增代码+RealHarnessAdapter：标注 event_callback 入参；如果没有这一行，映射回调类型不清楚。


GuiPermissionRequester = Callable[[GuiAgentRunRequest, str], bool]  # 新增代码+RealHarnessAdapter：定义可注入权限请求回调；如果没有这一行，Phase 4 无法把 GUI 权限弹窗接进来。
REAL_HARNESS_RUNTIME = "agent_harness"  # 新增代码+RealHarnessAdapter：集中声明真实运行路径名称；如果没有这一行，runtime_path 文案会在多处重复。


def _workspace_path(workspace: str) -> Path:  # 新增代码+RealHarnessAdapter：函数段开始，规范化 workspace；如果没有这段，LearningAgent 和事件脱敏可能使用不同路径。
    return Path(workspace or ".").expanduser().resolve()  # 新增代码+RealHarnessAdapter：返回绝对 Path；如果没有这一行，相对 workspace 会依赖当前终端。
# 新增代码+RealHarnessAdapter：函数段结束，_workspace_path 到此结束；如果没有这个边界说明，用户不容易看出路径清理范围。


class RealHarnessGuiAgentAdapter:  # 新增代码+RealHarnessAdapter：类段开始，把 GUI run 转给 LearningAgent；如果没有这个类，DefaultHarness shell 无法真正接入 core/agent.py。
    def __init__(self, enabled: bool = True, model_factory: GuiChatModelFactory | None = None, permission_requester: GuiPermissionRequester | None = None, max_turns: int = 1, allowed_tool_names: set[str] | None = None) -> None:  # 新增代码+RealHarnessAdapter：函数段开始，保存真实 adapter 依赖；如果没有这段，测试无法注入假模型或权限。
        self.enabled = enabled  # 新增代码+RealHarnessAdapter：保存 feature flag；如果没有这一行，禁用状态无法给出稳定失败。
        self.model_factory = model_factory or build_chat_model_for_gui_request  # 新增代码+RealHarnessAdapter：保存模型工厂；如果没有这一行，adapter 不知道如何创建 ChatModel。
        self.permission_requester = permission_requester  # 新增代码+RealHarnessAdapter：保存权限回调；如果没有这一行，后续 Phase 4 没有接入点。
        self.max_turns = max(int(max_turns), 1)  # 新增代码+RealHarnessAdapter：限制至少一轮模型循环；如果没有这一行，0 会让 agent 不请求模型直接安全停止。
        self.allowed_tool_names = set() if allowed_tool_names is None else allowed_tool_names  # 新增代码+RealHarnessAdapter：Phase 1 默认无工具；如果没有这一行，真实模型可能首轮看到全部工具并触发副作用。
    # 新增代码+RealHarnessAdapter：函数段结束，RealHarnessGuiAgentAdapter.__init__ 到此结束；如果没有边界说明，用户不容易看出初始化范围。

    def _emit(self, events: list[dict[str, object]], emit_event: GuiEventEmitter, event: dict[str, object]) -> None:  # 新增代码+RealHarnessAdapter：函数段开始，统一保存并发射 GUI 事件；如果没有这段，结果 events 和 bridge 收到的事件可能不一致。
        events.append(event)  # 新增代码+RealHarnessAdapter：保存事件副本；如果没有这一行，GuiAgentRunResult 无法复盘真实主循环。
        emit_event(event)  # 新增代码+RealHarnessAdapter：把事件交给 bridge；如果没有这一行，GUI 看不到真实 agent 进展。
    # 新增代码+RealHarnessAdapter：函数段结束，_emit 到此结束；如果没有边界说明，用户不容易看出事件发射范围。

    def _runtime_payload(self, request: GuiAgentRunRequest) -> dict[str, object]:  # 新增代码+RealHarnessAdapter：函数段开始，构造 runtime_path 诊断；如果没有这段，用户无法确认本轮走的是 core agent。
        return {"runtime": REAL_HARNESS_RUNTIME, "transport": "in_process_learning_agent", "provider_id": request.provider_id or "openai", "model_id": request.model_id, "reasoning_effort": request.reasoning_effort, "permission_mode": request.permission_mode, "tools_enabled": bool(self.allowed_tool_names)}  # 新增代码+RealHarnessAdapter：返回低敏路由摘要；如果没有这一行，GUI 诊断缺少真实接入证据。
    # 新增代码+RealHarnessAdapter：函数段结束，_runtime_payload 到此结束；如果没有边界说明，用户不容易看出它只做诊断。

    def _ask_permission(self, request: GuiAgentRunRequest, text: str) -> bool:  # 新增代码+RealHarnessAdapter：函数段开始，桥接 core agent 的 ask_permission；如果没有这段，Phase 4 无法接 GUI 权限。
        if self.permission_requester is None:  # 新增代码+RealHarnessAdapter：没有 GUI 权限回调时默认拒绝副作用；如果没有这一行，真实工具可能无确认执行。
            return False  # 新增代码+RealHarnessAdapter：保守拒绝权限；如果没有这一行，无权限回调时行为不安全。
        return bool(self.permission_requester(request, text))  # 新增代码+RealHarnessAdapter：委托调用方决定权限；如果没有这一行，GUI approve/deny 无法影响 core。
    # 新增代码+RealHarnessAdapter：函数段结束，_ask_permission 到此结束；如果没有边界说明，用户不容易看出权限来源。

    def _emit_factory_error(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, events: list[dict[str, object]], error: GuiModelFactoryError, sequence: int) -> GuiAgentRunResult:  # 新增代码+RealHarnessAdapter：函数段开始，把模型工厂失败变成 GUI 事件；如果没有这段，未连接 provider 会成为线程异常。
        diagnostic_event = make_event(error.event_kind, sequence, {"status": "failed", "error_code": error.code, "error": error.message, **self._runtime_payload(request)}, run_id=request.run_id, turn_id=request.turn_id)  # 新增代码+RealHarnessAdapter：构造 provider/model 诊断事件；如果没有这一行，前端无法显示未连接类型。
        self._emit(events, emit_event, diagnostic_event)  # 新增代码+RealHarnessAdapter：发出诊断事件；如果没有这一行，GUI 事件流缺少失败原因。
        failed_event = make_event("turn_failed", sequence + 1, {"status": "failed", "error_code": error.code, "error": error.message, **self._runtime_payload(request)}, run_id=request.run_id, turn_id=request.turn_id)  # 新增代码+RealHarnessAdapter：构造终态失败事件；如果没有这一行，bridge 可能不知道本轮已结束。
        self._emit(events, emit_event, failed_event)  # 新增代码+RealHarnessAdapter：发出终态失败；如果没有这一行，GUI 可能停在 running。
        return GuiAgentRunResult(status="failed", error_code=error.code, error_message=error.message, events=events)  # 新增代码+RealHarnessAdapter：返回结构化失败结果；如果没有这一行，worker 无法同步消息状态。
    # 新增代码+RealHarnessAdapter：函数段结束，_emit_factory_error 到此结束；如果没有边界说明，用户不容易看出工厂失败处理范围。

    def run(self, request: GuiAgentRunRequest, emit_event: GuiEventEmitter, is_cancelled: GuiCancelChecker) -> GuiAgentRunResult:  # 新增代码+RealHarnessAdapter：函数段开始，执行真实 core agent 主循环；如果没有这段，GUI 不会真正调用 core/agent.py。
        events: list[dict[str, object]] = []  # 新增代码+RealHarnessAdapter：保存本次 GUI 事件副本；如果没有这一行，测试和诊断无法复盘。
        if not self.enabled:  # 新增代码+RealHarnessAdapter：禁用时稳定失败；如果没有这一行，feature flag 失效会误调用真实模型。
            message = "Real harness GUI adapter is disabled."  # 新增代码+RealHarnessAdapter：准备禁用说明；如果没有这一行，用户不知道为什么真实模式不可用。
            self._emit(events, emit_event, make_event("turn_failed", 1, {"status": "failed", "error_code": "adapter_unavailable", "error": message}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+RealHarnessAdapter：发出禁用失败事件；如果没有这一行，GUI 看不到终态。
            return GuiAgentRunResult(status="failed", error_code="adapter_unavailable", error_message=message, events=events)  # 新增代码+RealHarnessAdapter：返回禁用失败；如果没有这一行，worker 无法同步失败。
        next_sequence = 1  # 新增代码+RealHarnessAdapter：初始化 adapter 局部事件序号；如果没有这一行，事件顺序无法稳定。
        self._emit(events, emit_event, make_event("runtime_path", next_sequence, self._runtime_payload(request), run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+RealHarnessAdapter：先发真实运行路径；如果没有这一行，验收无法确认走 core agent。
        next_sequence += 1  # 新增代码+RealHarnessAdapter：推进序号；如果没有这一行，下一事件会重复 sequence。
        if is_cancelled():  # 新增代码+RealHarnessAdapter：模型创建前检查取消；如果没有这一行，已取消 turn 仍可能请求模型。
            self._emit(events, emit_event, make_event("turn_cancelled", next_sequence, {"status": "cancelled", **self._runtime_payload(request)}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+RealHarnessAdapter：发出取消终态；如果没有这一行，GUI 会停在 running。
            return GuiAgentRunResult(status="cancelled", events=events)  # 新增代码+RealHarnessAdapter：返回取消结果；如果没有这一行，worker 会继续当失败或完成。
        try:  # 新增代码+RealHarnessAdapter：捕获模型工厂错误；如果没有这一行，未连接 provider 会冒泡成线程异常。
            model = self.model_factory(request)  # 新增代码+RealHarnessAdapter：创建 ChatModel；如果没有这一行，LearningAgent 没有模型可运行。
        except GuiModelFactoryError as error:  # 新增代码+RealHarnessAdapter：处理结构化工厂失败；如果没有这一行，provider_not_connected 无法单独显示。
            return self._emit_factory_error(request, emit_event, events, error, next_sequence)  # 新增代码+RealHarnessAdapter：把工厂失败转事件并结束；如果没有这一行，后续会使用不存在的 model。
        stop_event = threading.Event()  # 新增代码+RealHarnessAdapter：创建 core agent 取消信号；如果没有这一行，GUI cancel 不能进入 LearningAgent。
        workspace_path = _workspace_path(request.workspace)  # 新增代码+RealHarnessAdapter：规范化工作区；如果没有这一行，LearningAgent 读写 memory 路径可能不稳定。
        from learning_agent.core.agent import LearningAgent  # 修改代码+RealHarnessAdapter：只在真实 run path 中懒加载 core 主循环；如果没有这一行，GUI 普通路径会提前接触 core/agent.py。
        agent = LearningAgent(model=model, workspace=workspace_path, ask_permission=lambda text: self._ask_permission(request, text), stop_event=stop_event, allowed_tool_names=self.allowed_tool_names)  # 新增代码+RealHarnessAdapter：创建真实 LearningAgent；如果没有这一行，GUI 仍只是 fake shell。
        final_text = ""  # 新增代码+RealHarnessAdapter：保存 run() 返回的最终文本；如果没有这一行，fallback 完成事件没有文本来源。
        terminal_event_seen = False  # 新增代码+RealHarnessAdapter：记录 mapper 是否已发终态事件；如果没有这一行，adapter 可能重复 message_completed。
        def event_callback(agent_event: AgentEvent) -> None:  # 新增代码+RealHarnessAdapter：回调段开始，接收 core 主循环事件；如果没有这段，GUI 无法看到真实 agent 内部进展。
            nonlocal next_sequence, terminal_event_seen  # 新增代码+RealHarnessAdapter：允许回调推进序号和终态标记；如果没有这一行，事件顺序和终态检测无法更新。
            if is_cancelled():  # 新增代码+RealHarnessAdapter：每个 core 事件到来时检查 GUI cancel；如果没有这一行，取消只能等下一轮主循环。
                stop_event.set()  # 新增代码+RealHarnessAdapter：通知 LearningAgent 协作停止；如果没有这一行，core 主循环不知道用户已取消。
            mapped_events = agent_event_to_gui_events(agent_event, run_id=request.run_id, turn_id=request.turn_id, sequence_start=next_sequence, workspace=workspace_path, user_cancelled=is_cancelled())  # 新增代码+RealHarnessAdapter：把 core 事件转 GUI 事件；如果没有这一行，真实主循环事件不能进入 GUI。
            for event in mapped_events:  # 新增代码+RealHarnessAdapter：逐个发出映射结果；如果没有这一行，多事件映射会丢失。
                if str(event.get("kind", "")) in {"message_completed", "turn_cancelled", "turn_failed"}:  # 新增代码+RealHarnessAdapter：识别终态事件；如果没有这一行，后续 fallback 可能重复完成。
                    terminal_event_seen = True  # 新增代码+RealHarnessAdapter：记录已见终态；如果没有这一行，run 返回后无法判断是否补事件。
                self._emit(events, emit_event, event)  # 新增代码+RealHarnessAdapter：发出单个 GUI 事件；如果没有这一行，bridge 收不到事件。
            next_sequence += len(mapped_events)  # 新增代码+RealHarnessAdapter：按实际发出数量推进序号；如果没有这一行，后续事件 sequence 会重复。
        # 新增代码+RealHarnessAdapter：回调段结束，event_callback 到此结束；如果没有边界说明，用户不容易看出 core 事件如何进入 GUI。
        try:  # 新增代码+RealHarnessAdapter：保护真实主循环；如果没有这一行，core 异常会让 GUI worker 静默崩溃。
            final_text = agent.run(request.prompt, max_turns=self.max_turns, event_callback=event_callback, conversation_history=responses_input_to_compact_messages(request.messages))  # 修改代码+RealHarnessAdapter：执行 core agent 主循环并传入普通 role/content 历史；如果没有这一行，GUI Responses 分片会被 core 当成空历史。
            if is_cancelled():  # 新增代码+RealHarnessAdapter：run 返回后再检查取消；如果没有这一行，尾部取消可能显示为完成。
                stop_event.set()  # 新增代码+RealHarnessAdapter：保持 stop_event 与 GUI cancel 一致；如果没有这一行，状态不一致。
            if not terminal_event_seen:  # 新增代码+RealHarnessAdapter：mapper 没有发终态时补一个；如果没有这一行，异常边界或旧 core 事件会让 GUI 悬挂。
                kind = "turn_cancelled" if is_cancelled() else "message_completed"  # 新增代码+RealHarnessAdapter：根据取消状态选择终态；如果没有这一行，取消 fallback 会被误当完成。
                payload = {"final_text": final_text, **self._runtime_payload(request)}  # 新增代码+RealHarnessAdapter：构造 fallback 终态 payload；如果没有这一行，终态缺少文本和路径。
                self._emit(events, emit_event, make_event(kind, next_sequence, payload, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+RealHarnessAdapter：发出 fallback 终态；如果没有这一行，GUI 可能停在 running。
            return GuiAgentRunResult(status="cancelled" if is_cancelled() else "completed", final_text=final_text, events=events)  # 新增代码+RealHarnessAdapter：返回最终状态；如果没有这一行，worker 无法写回消息。
        except Exception as error:  # 新增代码+RealHarnessAdapter：捕获真实主循环异常；如果没有这一行，失败不会变成可见 turn_failed。
            error_text = str(error)  # 新增代码+RealHarnessAdapter：保存错误文本；如果没有这一行，事件 payload 没有可读说明。
            self._emit(events, emit_event, make_event("turn_failed", next_sequence, {"status": "failed", "error_code": "real_harness_failed", "error": error_text, **self._runtime_payload(request)}, run_id=request.run_id, turn_id=request.turn_id))  # 新增代码+RealHarnessAdapter：发出真实 harness 失败事件；如果没有这一行，GUI 无法进入 failed。
            return GuiAgentRunResult(status="failed", error_code="real_harness_failed", error_message=error_text, events=events)  # 新增代码+RealHarnessAdapter：返回失败结果；如果没有这一行，worker 可能误判完成。
    # 新增代码+RealHarnessAdapter：函数段结束，RealHarnessGuiAgentAdapter.run 到此结束；如果没有边界说明，用户不容易看出真实主循环生命周期。
# 新增代码+RealHarnessAdapter：类段结束，RealHarnessGuiAgentAdapter 到此结束；如果没有边界说明，用户不容易看出本类是 Phase 1 接入点。
