"""Desktop GUI agent adapter boundary."""  # 新增代码+GuiAgentAdapter：说明本模块隔离 GUI 与真实 agent/harness；如果没有这一行，后续容易把模型运行时直接导入 GUI bridge。

from __future__ import annotations  # 新增代码+GuiAgentAdapter：启用未来注解语法；如果没有这一行，Protocol 和 dataclass 类型标注在旧行为下更容易出问题。

import json  # 新增代码+GuiAgentAdapter：读取 golden trace fixture；如果没有这一行，fake adapter 无法回放固定事件语料。
from dataclasses import dataclass, field  # 新增代码+GuiAgentAdapter：定义 adapter 请求和结果数据结构；如果没有这一行，边界会变成松散 dict。
from pathlib import Path  # 新增代码+GuiAgentAdapter：定位 repo 内 golden trace fixture；如果没有这一行，路径拼接容易在 Windows 上出错。
from typing import Callable, Protocol  # 新增代码+GuiAgentAdapter：定义 adapter 接口和回调类型；如果没有这一行，fake/real adapter 合同不清楚。

from learning_agent.app.gui_protocol import make_event  # 新增代码+GuiAgentAdapter：复用 V2 事件生成 helper；如果没有这一行，adapter 事件形状会和协议模块分裂。


GuiEventEmitter = Callable[[dict[str, object]], None]  # 新增代码+GuiAgentAdapter：定义事件发射回调类型；如果没有这一行，adapter 不知道如何把事件交给 bridge。
GuiCancelChecker = Callable[[], bool]  # 新增代码+GuiAgentAdapter：定义取消检查回调类型；如果没有这一行，adapter 无法和 GUI cancel 按钮协作。


@dataclass  # 新增代码+GuiAgentAdapter：自动生成请求对象初始化方法；如果没有这一行，请求字段要手写构造器。
class GuiAgentRunRequest:  # 新增代码+GuiAgentAdapter：请求类段开始，描述一次 GUI run；如果没有这个类，adapter 入参会散成多个字符串。
    session_id: str  # 新增代码+GuiAgentAdapter：保存会话 id；如果没有这一行，adapter 事件无法归属会话。
    turn_id: str  # 新增代码+GuiAgentAdapter：保存 turn id；如果没有这一行，事件无法关联消息。
    run_id: str  # 新增代码+GuiAgentAdapter：保存 run id；如果没有这一行，状态面板无法按运行聚合。
    prompt: str  # 新增代码+GuiAgentAdapter：保存用户 prompt；如果没有这一行，adapter 没有任务输入。
    trace_id: str = ""  # 新增代码+GuiAgentAdapter：可选 golden trace id；如果没有这一行，fake adapter 无法回放指定 GT 场景。
    mode: str = "fake"  # 新增代码+GuiAgentAdapter：保存请求模式；如果没有这一行，后续 real/fake 切换没有显式语义。
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
