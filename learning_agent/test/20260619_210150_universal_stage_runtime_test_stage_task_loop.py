from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import ActionBatch, DesktopTaskPlan, StagePlan, StageResult  # 新增代码+StageTaskLoopTest：导入阶段循环所需模型；如果没有这行代码，测试无法构造计划和结果。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_task_loop import UniversalStageTaskLoop  # 新增代码+StageTaskLoopTest：导入通用阶段任务循环；如果没有这行代码，测试无法验证主运行时。


class FakeTargetRuntime:  # 新增代码+StageTaskLoopTest：类段开始，提供安全目标 session fake；如果没有这个类，测试会启动真实应用。
    def open_target_session(self, raw_target: str, candidates: list | None = None) -> dict:  # 新增代码+StageTaskLoopTest：函数段开始，模拟建立目标 session；如果没有这段函数，循环无法绑定 target_ref。
        return {"session_ready": True, "target_ref": str(raw_target), "target_window": {"rect": {"width": 800, "height": 500}, "hwnd": 100}, "target_identity_bound": True}  # 新增代码+StageTaskLoopTest：返回稳定目标 session；如果没有这行代码，阶段执行没有目标窗口。
    # 新增代码+StageTaskLoopTest：函数段结束，FakeTargetRuntime.open_target_session 到此结束；如果没有这个边界说明，初学者不容易看出 session 范围。

    def verify_before_action(self, session: dict, current_window: dict) -> dict:  # 新增代码+StageTaskLoopTest：函数段开始，模拟动作前目标复核；如果没有这段函数，默认批执行器无法证明 target_ref 安全。
        return {"allowed": True, "target_identity_verified": True, "current_window": dict(current_window)}  # 新增代码+StageTaskLoopTest：返回允许结果；如果没有这行代码，测试会卡在目标门禁。
    # 新增代码+StageTaskLoopTest：函数段结束，FakeTargetRuntime.verify_before_action 到此结束；如果没有这个边界说明，初学者不容易看出复核范围。


class BoundaryObservationRuntime:  # 新增代码+StageTaskLoopTest：类段开始，记录观察次数并返回完成证据；如果没有这个类，测试无法确认不是每个 primitive 都观察。
    def __init__(self) -> None:  # 新增代码+StageTaskLoopTest：函数段开始，初始化观察计数；如果没有这段函数，测试无法读取观察次数。
        self.count = 0  # 新增代码+StageTaskLoopTest：保存观察次数；如果没有这行代码，边界观察无法断言。
    # 新增代码+StageTaskLoopTest：函数段结束，BoundaryObservationRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def observe(self, target_hint: str = "", real_desktop_touched: bool = False, target_window: dict | None = None) -> dict:  # 新增代码+StageTaskLoopTest：函数段开始，模拟观察帧；如果没有这段函数，循环无法观察。
        self.count += 1  # 新增代码+StageTaskLoopTest：累计观察次数；如果没有这行代码，测试无法判断观察粒度。
        return {"target_hint": target_hint, "target_window": dict(target_window or {"rect": {"width": 800, "height": 500}}), "target_identity_verified": True, "visible_text": "hello everyone", "saved_resource_exists": True, "canvas_changed_after_actions": True, "visual_primitives": ["outline", "color_block"]}  # 新增代码+StageTaskLoopTest：返回通用完成证据；如果没有这行代码，verifier 无法完成阶段。
    # 新增代码+StageTaskLoopTest：函数段结束，BoundaryObservationRuntime.observe 到此结束；如果没有这个边界说明，初学者不容易看出观察范围。


class RecordingBatchExecutor:  # 新增代码+StageTaskLoopTest：类段开始，记录执行过的批；如果没有这个类，测试无法确认批执行。
    def __init__(self, status: str = "completed") -> None:  # 新增代码+StageTaskLoopTest：函数段开始，初始化批执行 fake；如果没有这段函数，测试无法切换执行状态。
        self.status = status  # 新增代码+StageTaskLoopTest：保存返回状态；如果没有这行代码，失败场景不可控。
        self.batches: list[ActionBatch] = []  # 新增代码+StageTaskLoopTest：保存执行批列表；如果没有这行代码，测试无法检查批内容。
    # 新增代码+StageTaskLoopTest：函数段结束，RecordingBatchExecutor.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def execute_batch(self, session: dict, batch: ActionBatch) -> StageResult:  # 新增代码+StageTaskLoopTest：函数段开始，模拟批执行；如果没有这段函数，循环无法推进阶段。
        self.batches.append(batch)  # 新增代码+StageTaskLoopTest：记录批；如果没有这行代码，测试无法确认 pointer_path_batch。
        return StageResult(status=self.status, stage_id=str(batch.guardrails.get("stage_id", batch.batch_id)), evidence={"primitive_action_count": len(batch.actions), "successful_action_count": len(batch.actions), "low_level_event_count": len(batch.actions) * 2})  # 新增代码+StageTaskLoopTest：返回执行结果；如果没有这行代码，循环没有执行证据。
    # 新增代码+StageTaskLoopTest：函数段结束，RecordingBatchExecutor.execute_batch 到此结束；如果没有这个边界说明，初学者不容易看出执行范围。


class NeedsRepairVerifier:  # 新增代码+StageTaskLoopTest：类段开始，模拟永远需要修复；如果没有这个类，bounded repair 难以稳定测试。
    def verify_stage(self, plan: DesktopTaskPlan, stage: StagePlan, before_frame: dict, after_frame: dict, execution_result: StageResult) -> StageResult:  # 新增代码+StageTaskLoopTest：函数段开始，返回需要修复；如果没有这段函数，循环不会进入修复分支。
        return StageResult(status="needs_repair", stage_id=stage.stage_id, evidence={"forced": True})  # 新增代码+StageTaskLoopTest：返回需要修复状态；如果没有这行代码，修复预算无法测试。
    # 新增代码+StageTaskLoopTest：函数段结束，NeedsRepairVerifier.verify_stage 到此结束；如果没有这个边界说明，初学者不容易看出修复范围。


class NeedsUserVerifier:  # 新增代码+StageTaskLoopTest：类段开始，模拟需要用户介入；如果没有这个类，用户阻断路径无法稳定测试。
    def verify_stage(self, plan: DesktopTaskPlan, stage: StagePlan, before_frame: dict, after_frame: dict, execution_result: StageResult) -> StageResult:  # 新增代码+StageTaskLoopTest：函数段开始，返回需要用户；如果没有这段函数，循环不会进入用户停止分支。
        return StageResult(status="needs_user", stage_id=stage.stage_id, evidence={"reason": "manual_authorization_required"})  # 新增代码+StageTaskLoopTest：返回需要用户状态；如果没有这行代码，工具停止条件无法测试。
    # 新增代码+StageTaskLoopTest：函数段结束，NeedsUserVerifier.verify_stage 到此结束；如果没有这个边界说明，初学者不容易看出用户阻断范围。


def test_text_task_observes_at_stage_boundaries_not_per_primitive() -> None:  # 新增代码+StageTaskLoopTest：函数段开始，验证阶段边界观察；如果没有这个测试，循环可能继续每个 primitive 观察。
    observation = BoundaryObservationRuntime()  # 新增代码+StageTaskLoopTest：创建记录观察 runtime；如果没有这行代码，无法统计观察次数。
    report = UniversalStageTaskLoop(observation_runtime=observation, target_runtime=FakeTargetRuntime()).run_desktop_task("请输入 hello everyone 并保存")  # 新增代码+StageTaskLoopTest：运行文本任务；如果没有这行代码，无法获得阶段报告。
    assert report["desktop_task_completed"] is True  # 新增代码+StageTaskLoopTest：确认任务完成；如果没有这行代码，成功路径不可见。
    assert report["stage_boundary_observation_used"] is True  # 新增代码+StageTaskLoopTest：确认使用阶段边界观察；如果没有这行代码，观察策略不可见。
    assert report["observation_frame_count"] <= report["stage_count"] * 2  # 新增代码+StageTaskLoopTest：确认未按 primitive 过度观察；如果没有这行代码，用户体感慢的问题会复发。


def test_drawing_task_executes_one_batch_with_multiple_pointer_paths() -> None:  # 新增代码+StageTaskLoopTest：函数段开始，验证绘图阶段批内多路径；如果没有这个测试，复杂图形会退回单线。
    executor = RecordingBatchExecutor()  # 新增代码+StageTaskLoopTest：创建记录批执行器；如果没有这行代码，无法检查批类型。
    report = UniversalStageTaskLoop(observation_runtime=BoundaryObservationRuntime(), target_runtime=FakeTargetRuntime(), batch_executor=executor).run_desktop_task("请绘制一个彩色人物并保存")  # 新增代码+StageTaskLoopTest：运行绘图任务；如果没有这行代码，无法生成绘图批。
    pointer_batches = [batch for batch in executor.batches if batch.batch_kind == "pointer_path_batch"]  # 新增代码+StageTaskLoopTest：提取指针路径批；如果没有这行代码，无法断言绘图批。
    assert report["batch_execution_used"] is True  # 新增代码+StageTaskLoopTest：确认批执行启用；如果没有这行代码，循环可能仍逐步执行。
    assert pointer_batches and sum(1 for action in pointer_batches[0].actions if action["type"] == "drag_path") >= 3  # 新增代码+StageTaskLoopTest：确认单个绘图批含多条路径；如果没有这行代码，复杂绘图无法一次阶段完成。


def test_failed_stage_uses_bounded_repair_then_reports_incomplete() -> None:  # 新增代码+StageTaskLoopTest：函数段开始，验证有限修复；如果没有这个测试，失败阶段可能无限循环。
    report = UniversalStageTaskLoop(observation_runtime=BoundaryObservationRuntime(), target_runtime=FakeTargetRuntime(), stage_verifier=NeedsRepairVerifier(), max_stage_repairs=1).run_desktop_task("请输入 hello everyone")  # 新增代码+StageTaskLoopTest：运行强制修复任务；如果没有这行代码，无法触发修复预算。
    assert report["desktop_task_incomplete"] is True  # 新增代码+StageTaskLoopTest：确认任务未完成；如果没有这行代码，未完成可能 final。
    assert report["max_stage_repairs_reached"] is True  # 新增代码+StageTaskLoopTest：确认修复预算用尽；如果没有这行代码，bounded repair 不可见。


def test_needs_user_stage_stops_tool_execution() -> None:  # 新增代码+StageTaskLoopTest：函数段开始，验证需要用户时停止；如果没有这个测试，旧窗口授权类问题可能继续工具调用。
    report = UniversalStageTaskLoop(observation_runtime=BoundaryObservationRuntime(), target_runtime=FakeTargetRuntime(), stage_verifier=NeedsUserVerifier()).run_desktop_task("请使用未知软件完成操作")  # 新增代码+StageTaskLoopTest：运行需要用户任务；如果没有这行代码，无法触发 needs_user。
    assert report["desktop_task_incomplete"] is True  # 新增代码+StageTaskLoopTest：确认任务未完成；如果没有这行代码，needs_user 可能误成功。
    assert report["needs_user"] is True  # 新增代码+StageTaskLoopTest：确认报告需要用户；如果没有这行代码，最终回答无法提示用户。


def test_completed_and_incomplete_flags_are_mutually_clear() -> None:  # 新增代码+StageTaskLoopTest：函数段开始，验证完成/未完成标记；如果没有这个测试，final gate 可能读到矛盾状态。
    report = UniversalStageTaskLoop(observation_runtime=BoundaryObservationRuntime(), target_runtime=FakeTargetRuntime()).run_desktop_task("请输入 hello everyone")  # 新增代码+StageTaskLoopTest：运行正常任务；如果没有这行代码，无法读取完成标记。
    assert report["desktop_task_completed"] is True  # 新增代码+StageTaskLoopTest：确认完成为真；如果没有这行代码，成功标记不可见。
    assert report["desktop_task_incomplete"] is False  # 新增代码+StageTaskLoopTest：确认未完成为假；如果没有这行代码，final gate 可能被误挡。
