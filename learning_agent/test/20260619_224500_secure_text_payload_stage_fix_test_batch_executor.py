from learning_agent.computer_use_mcp_v2.windows_runtime.batch_executor import UniversalActionBatchExecutor  # 新增代码+BatchExecutorTest：导入批执行器；如果没有这行代码，测试无法验证阶段批执行。
from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_physical_sendinput import WindowsControlledPhysicalSendInputSender  # 新增代码+SecureTextChannelTest：导入受控物理 sender；如果没有这行代码，测试无法覆盖真实文本最后一跳合同。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import ActionBatch  # 新增代码+BatchExecutorTest：导入动作批模型；如果没有这行代码，测试无法构造批输入。
from learning_agent.computer_use_mcp_v2.windows_runtime.universal_action_dsl import UniversalActionDslRuntime  # 新增代码+SecureTextChannelTest：导入通用动作 DSL；如果没有这行代码，测试无法覆盖批执行真实文本通道。


class FakeTargetRuntime:  # 新增代码+BatchExecutorTest：类段开始，提供可控目标复核 fake；如果没有这个类，测试只能触碰真实窗口。
    def __init__(self, allowed: bool = True) -> None:  # 新增代码+BatchExecutorTest：函数段开始，初始化复核结果；如果没有这段函数，测试无法切换漂移场景。
        self.allowed = allowed  # 新增代码+BatchExecutorTest：保存是否允许动作；如果没有这行代码，漂移测试无开关。
        self.verify_count = 0  # 新增代码+BatchExecutorTest：保存复核次数；如果没有这行代码，测试无法确认批前复核。
    # 新增代码+BatchExecutorTest：函数段结束，FakeTargetRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def verify_before_action(self, session: dict, current_window: dict) -> dict:  # 新增代码+BatchExecutorTest：函数段开始，模拟目标身份复核；如果没有这段函数，执行器无法走安全门禁。
        self.verify_count += 1  # 新增代码+BatchExecutorTest：记录复核次数；如果没有这行代码，批复核是否发生不可见。
        return {"allowed": self.allowed, "target_identity_verified": self.allowed, "current_window": dict(current_window)}  # 新增代码+BatchExecutorTest：返回复核报告；如果没有这行代码，执行器拿不到允许或阻断事实。
    # 新增代码+BatchExecutorTest：函数段结束，FakeTargetRuntime.verify_before_action 到此结束；如果没有这个边界说明，初学者不容易看出复核范围。


class FakeActionRuntime:  # 新增代码+BatchExecutorTest：类段开始，提供可控动作 runtime；如果没有这个类，测试会调用真实 SendInput。
    def __init__(self, target_runtime: FakeTargetRuntime, fail_at: int | None = None) -> None:  # 新增代码+BatchExecutorTest：函数段开始，初始化 fake 动作层；如果没有这段函数，测试无法模拟动作失败。
        self.target_runtime = target_runtime  # 新增代码+BatchExecutorTest：暴露目标 runtime；如果没有这行代码，执行器无法读取目标复核能力。
        self.fail_at = fail_at  # 新增代码+BatchExecutorTest：保存失败动作序号；如果没有这行代码，失败测试无法控制。
        self.dispatched: list[dict] = []  # 新增代码+BatchExecutorTest：保存已分发动作；如果没有这行代码，测试无法确认剩余动作被停止。
    # 新增代码+BatchExecutorTest：函数段结束，FakeActionRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def dispatch(self, session: dict, action: dict, current_window: dict | None = None) -> dict:  # 新增代码+BatchExecutorTest：函数段开始，模拟单个 primitive 分发；如果没有这段函数，批执行器无法执行动作。
        self.dispatched.append(dict(action))  # 新增代码+BatchExecutorTest：记录本次动作；如果没有这行代码，测试无法统计动作数量。
        if self.fail_at is not None and len(self.dispatched) == self.fail_at:  # 新增代码+BatchExecutorTest：检查是否到达指定失败序号；如果没有这行代码，失败场景不会触发。
            return {"ok": False, "decision": "fake_failure", "low_level_event_count": 0}  # 新增代码+BatchExecutorTest：返回失败结果；如果没有这行代码，执行器不会进入中止路径。
        return {"ok": True, "decision": "sent_to_low_level_sender", "low_level_event_count": 2, "current_window": dict(current_window or {})}  # 新增代码+BatchExecutorTest：返回成功结果；如果没有这行代码，执行器没有成功事实。
    # 新增代码+BatchExecutorTest：函数段结束，FakeActionRuntime.dispatch 到此结束；如果没有这个边界说明，初学者不容易看出分发范围。


class FakeRawTextBackend:  # 新增代码+SecureTextChannelTest：类段开始，模拟真实后端需要明文才能发送 Unicode；如果没有这个类，测试无法复现 secure_plaintext_text_channel_missing。
    requires_raw_text = True  # 新增代码+SecureTextChannelTest：声明后端需要短生命周期明文；如果没有这行代码，Phase95 不会走真实文本通道分支。

    def __init__(self) -> None:  # 新增代码+SecureTextChannelTest：函数段开始，初始化接收事件列表；如果没有这段函数，测试无法检查后端实际收到什么。
        self.events: list[dict] = []  # 新增代码+SecureTextChannelTest：保存后端收到的事件；如果没有这行代码，无法证明文本只在最后一跳出现。
    # 新增代码+SecureTextChannelTest：函数段结束，FakeRawTextBackend.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def send_low_level(self, events: list[dict]) -> dict:  # 新增代码+SecureTextChannelTest：函数段开始，模拟真实后端发送；如果没有这段函数，Phase95 没有可调用最后一跳。
        self.events.extend(dict(event) for event in events)  # 新增代码+SecureTextChannelTest：保存事件副本；如果没有这行代码，测试无法断言后端拿到明文。
        return {"ok": True, "sender": "fake_raw_text_backend", "low_level_event_count": len(events), "raw_text_included": False}  # 新增代码+SecureTextChannelTest：返回脱敏成功摘要；如果没有这行代码，上层会把 fake 结果当失败。
    # 新增代码+SecureTextChannelTest：函数段结束，FakeRawTextBackend.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出后端范围。


def _batch(actions: tuple[dict, ...] = ({"type": "focus_window"}, {"type": "type_text"})) -> ActionBatch:  # 新增代码+BatchExecutorTest：函数段开始，构造标准测试批；如果没有这段函数，多个测试会重复样板。
    return ActionBatch(batch_id="batch-a", batch_kind="text_entry_batch", target_ref="target-a", actions=actions, guardrails={"stage_id": "stage-a"})  # 新增代码+BatchExecutorTest：返回带 target_ref 的写批；如果没有这行代码，执行器没有批输入。
# 新增代码+BatchExecutorTest：函数段结束，_batch 到此结束；如果没有这个边界说明，初学者不容易看出批构造范围。


def test_batch_executor_verifies_target_once_before_stable_batch() -> None:  # 新增代码+BatchExecutorTest：函数段开始，验证批前目标复核；如果没有这个测试，批执行可能绕过一对一窗口门禁。
    target_runtime = FakeTargetRuntime()  # 新增代码+BatchExecutorTest：创建允许复核 fake；如果没有这行代码，执行器没有目标门禁。
    runtime = FakeActionRuntime(target_runtime)  # 新增代码+BatchExecutorTest：创建 fake 动作 runtime；如果没有这行代码，执行器无法分发。
    result = UniversalActionBatchExecutor(runtime).execute_batch({"target_ref": "target-a", "target_window": {"hwnd": 1}}, _batch())  # 新增代码+BatchExecutorTest：执行批；如果没有这行代码，无法断言结果。
    assert result.status == "completed"  # 新增代码+BatchExecutorTest：确认稳定批完成；如果没有这行代码，成功路径不可见。
    assert target_runtime.verify_count == 1  # 新增代码+BatchExecutorTest：确认批前复核一次；如果没有这行代码，批可能每步重复观察或完全不验。


def test_batch_executor_refuses_target_drift_before_dispatch() -> None:  # 新增代码+BatchExecutorTest：函数段开始，验证漂移时零动作；如果没有这个测试，错误窗口可能收到输入。
    target_runtime = FakeTargetRuntime(allowed=False)  # 新增代码+BatchExecutorTest：创建拒绝复核 fake；如果没有这行代码，漂移场景无法触发。
    runtime = FakeActionRuntime(target_runtime)  # 新增代码+BatchExecutorTest：创建 fake 动作 runtime；如果没有这行代码，执行器无法运行。
    result = UniversalActionBatchExecutor(runtime).execute_batch({"target_ref": "target-a", "target_window": {"hwnd": 2}}, _batch())  # 新增代码+BatchExecutorTest：执行漂移批；如果没有这行代码，无法断言拒绝。
    assert result.status == "blocked"  # 新增代码+BatchExecutorTest：确认漂移被阻断；如果没有这行代码，安全门禁不可见。
    assert len(runtime.dispatched) == 0  # 新增代码+BatchExecutorTest：确认没有 primitive 被发出；如果没有这行代码，零事件安全无法证明。


def test_batch_executor_dispatches_all_primitives_and_counts_events() -> None:  # 新增代码+BatchExecutorTest：函数段开始，验证批内动作全部执行和计数；如果没有这个测试，批执行可能只执行第一步。
    runtime = FakeActionRuntime(FakeTargetRuntime())  # 新增代码+BatchExecutorTest：创建稳定 fake runtime；如果没有这行代码，执行器没有依赖。
    result = UniversalActionBatchExecutor(runtime).execute_batch({"target_ref": "target-a", "target_window": {"hwnd": 3}}, _batch())  # 新增代码+BatchExecutorTest：执行标准批；如果没有这行代码，无法获得结果。
    assert result.evidence["primitive_action_count"] == 2  # 新增代码+BatchExecutorTest：确认 primitive 总数；如果没有这行代码，批规模不可见。
    assert result.evidence["successful_action_count"] == 2  # 新增代码+BatchExecutorTest：确认成功动作数；如果没有这行代码，部分失败可能被误报完成。
    assert result.evidence["low_level_event_count"] == 4  # 新增代码+BatchExecutorTest：确认低层事件累计；如果没有这行代码，真实动作规模不可见。


def test_batch_executor_stops_remaining_actions_after_failure() -> None:  # 新增代码+BatchExecutorTest：函数段开始，验证失败后停止剩余动作；如果没有这个测试，批执行可能继续污染窗口。
    runtime = FakeActionRuntime(FakeTargetRuntime(), fail_at=2)  # 新增代码+BatchExecutorTest：创建第二步失败 fake runtime；如果没有这行代码，失败场景不可控。
    actions = ({"type": "focus_window"}, {"type": "type_text"}, {"type": "press_key", "key": "ENTER"})  # 新增代码+BatchExecutorTest：准备三步动作；如果没有这行代码，无法证明第三步被停止。
    result = UniversalActionBatchExecutor(runtime).execute_batch({"target_ref": "target-a", "target_window": {"hwnd": 4}}, _batch(actions))  # 新增代码+BatchExecutorTest：执行失败批；如果没有这行代码，无法获得失败结果。
    assert result.status == "failed"  # 新增代码+BatchExecutorTest：确认批失败；如果没有这行代码，失败可能被误判完成。
    assert len(runtime.dispatched) == 2  # 新增代码+BatchExecutorTest：确认第三步未执行；如果没有这行代码，失败后污染风险不可见。


def test_universal_action_dsl_uses_secure_text_channel_for_real_text_backend() -> None:  # 新增代码+SecureTextChannelTest：函数段开始，验证文本批能通过短生命周期明文通道执行；如果没有这个测试，真实 Stage 文本输入会一直失败。
    backend = FakeRawTextBackend()  # 新增代码+SecureTextChannelTest：创建需要明文的 fake 后端；如果没有这行代码，无法证明最后一跳收到文本。
    sender = WindowsControlledPhysicalSendInputSender(low_level_backend=backend, platform="win32", default_enable_physical_dispatch=True)  # 新增代码+SecureTextChannelTest：创建受控物理 sender 并显式开启 fake 发送；如果没有这行代码，真实派发默认关闭会阻断测试。
    runtime = UniversalActionDslRuntime(target_runtime=FakeTargetRuntime(), low_level_sender=sender)  # 新增代码+SecureTextChannelTest：把通用 DSL 接到受控 sender；如果没有这行代码，测试不会覆盖 Stage 批真实路径。
    session = {"target_ref": "target-a", "target_window": {"hwnd": 5, "window_id": "hwnd:5", "app_id": "generic-editor.exe", "process_name": "generic-editor.exe", "title_preview": "Untitled - Generic Editor"}}  # 新增代码+SecureTextChannelTest：构造普通安全目标窗口；如果没有这行代码，Phase95 目标门禁会拒绝。
    result = runtime.dispatch(session, {"type": "type_text", "text": "hello everyone"}, current_window=session["target_window"])  # 新增代码+SecureTextChannelTest：发送通用文本动作；如果没有这行代码，无法复现 Stage 批文本输入路径。
    text_events = [event for event in backend.events if event.get("type") == "unicode_text"]  # 修改代码+SecureTextChannelTest：只挑出真实文本事件，跳过自动聚焦事件；如果没有这行代码，断言可能误看 set_foreground。
    assert result["ok"] is True  # 新增代码+SecureTextChannelTest：确认动作成功；如果没有这行代码，测试不会发现 secure channel 仍缺失。
    assert text_events[0]["text"] == "hello everyone"  # 修改代码+SecureTextChannelTest：确认明文只到达 fake 后端的文本事件；如果没有这行代码，短通道可能没有真正传递文本。
    assert "hello everyone" not in str(result)  # 新增代码+SecureTextChannelTest：确认公开结果不泄露原文；如果没有这行代码，隐私门禁可能被破坏。
# 新增代码+SecureTextChannelTest：函数段结束，test_universal_action_dsl_uses_secure_text_channel_for_real_text_backend 到此结束；如果没有这个边界说明，初学者不容易看出测试范围。
