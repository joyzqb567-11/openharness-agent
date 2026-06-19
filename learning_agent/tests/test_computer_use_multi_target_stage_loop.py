from learning_agent.computer_use_mcp_v2.windows_runtime.capability_profile import AppCapabilityProfile  # 新增代码+MultiTargetStageLoopTest：导入通用能力画像；如果没有这行代码，测试无法让多目标阶段编译成写批。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import ActionBatch, StageResult  # 新增代码+MultiTargetStageLoopTest：导入批和结果模型；如果没有这行代码，fake 执行器无法返回标准结果。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_planner import UniversalDesktopStagePlanner  # 新增代码+MultiTargetStageLoopTest：导入通用阶段 planner；如果没有这行代码，无法验证多目标计划。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_task_loop import UniversalStageTaskLoop  # 新增代码+MultiTargetStageLoopTest：导入阶段任务循环；如果没有这行代码，无法验证运行时目标映射。


class MultiTargetRuntime:  # 新增代码+MultiTargetStageLoopTest：类段开始，模拟两个安全目标 session；如果没有这个类，测试会打开真实应用。
    def __init__(self, preexisting: bool = False, granted: bool = False) -> None:  # 新增代码+MultiTargetStageLoopTest：函数段开始，配置是否模拟已有窗口；如果没有这段函数，旧窗口阻断路径不可控。
        self.preexisting = preexisting  # 新增代码+MultiTargetStageLoopTest：保存是否已有窗口；如果没有这行代码，open_target_session 无法返回旧窗口事实。
        self.granted = granted  # 新增代码+MultiTargetStageLoopTest：保存是否授权已有窗口；如果没有这行代码，测试无法区分阻断和授权。
        self.sequence = 0  # 新增代码+MultiTargetStageLoopTest：保存 session 序号；如果没有这行代码，两个目标会拿到相同 hwnd。
    # 新增代码+MultiTargetStageLoopTest：函数段结束，MultiTargetRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出配置范围。

    def open_target_session(self, raw_target: str, candidates: list | None = None) -> dict:  # 新增代码+MultiTargetStageLoopTest：函数段开始，模拟建立目标 session；如果没有这段函数，stage loop 无法绑定 target_ref。
        self.sequence += 1  # 新增代码+MultiTargetStageLoopTest：推进窗口序号；如果没有这行代码，多目标窗口无法区分。
        return {"session_ready": True, "target_ref": str(raw_target), "target_window": {"rect": {"width": 900, "height": 600}, "hwnd": 9000 + self.sequence}, "target_identity_bound": True, "target_window_existed_before_launch": self.preexisting, "user_granted_existing_window": self.granted}  # 新增代码+MultiTargetStageLoopTest：返回稳定 session；如果没有这行代码，运行时没有目标身份事实。
    # 新增代码+MultiTargetStageLoopTest：函数段结束，MultiTargetRuntime.open_target_session 到此结束；如果没有这个边界说明，初学者不容易看出 session 范围。

    def verify_before_action(self, session: dict, current_window: dict) -> dict:  # 新增代码+MultiTargetStageLoopTest：函数段开始，模拟动作前目标复核；如果没有这段函数，默认执行器无法通过目标身份门禁。
        return {"allowed": True, "target_identity_verified": True, "current_window": dict(current_window)}  # 新增代码+MultiTargetStageLoopTest：返回允许结果；如果没有这行代码，批执行会被阻断。
    # 新增代码+MultiTargetStageLoopTest：函数段结束，MultiTargetRuntime.verify_before_action 到此结束；如果没有这个边界说明，初学者不容易看出复核范围。


class MultiTargetObservation:  # 新增代码+MultiTargetStageLoopTest：类段开始，提供多目标阶段完成观察；如果没有这个类，verifier 没有后置事实。
    def observe(self, target_hint: str = "", real_desktop_touched: bool = False, target_window: dict | None = None) -> dict:  # 新增代码+MultiTargetStageLoopTest：函数段开始，返回通用观察帧；如果没有这段函数，stage loop 无法构造能力画像。
        return {"target_hint": target_hint, "target_window": dict(target_window or {"rect": {"width": 900, "height": 600}}), "target_identity_verified": True, "visible_text": "sample collected text", "saved_resource_exists": True}  # 新增代码+MultiTargetStageLoopTest：返回完成证据；如果没有这行代码，多目标 verifier 无法完成。
    # 新增代码+MultiTargetStageLoopTest：函数段结束，MultiTargetObservation.observe 到此结束；如果没有这个边界说明，初学者不容易看出观察范围。


class RecordingTargetBatchExecutor:  # 新增代码+MultiTargetStageLoopTest：类段开始，记录批和 session target_ref；如果没有这个类，无法证明写批没有打到错误目标。
    def __init__(self) -> None:  # 新增代码+MultiTargetStageLoopTest：函数段开始，初始化记录列表；如果没有这段函数，测试无法读取执行历史。
        self.records: list[tuple[str, str, str]] = []  # 新增代码+MultiTargetStageLoopTest：保存 session_ref、batch_ref、batch_kind；如果没有这行代码，多目标断言没有事实来源。
    # 新增代码+MultiTargetStageLoopTest：函数段结束，RecordingTargetBatchExecutor.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def execute_batch(self, session: dict, batch: ActionBatch) -> StageResult:  # 新增代码+MultiTargetStageLoopTest：函数段开始，模拟批执行并验证 target_ref；如果没有这段函数，stage loop 无法推进。
        session_ref = str(session.get("target_ref", ""))  # 新增代码+MultiTargetStageLoopTest：读取 session 的 target_ref；如果没有这行代码，无法发现目标错配。
        self.records.append((session_ref, batch.target_ref, batch.batch_kind))  # 新增代码+MultiTargetStageLoopTest：记录执行事实；如果没有这行代码，测试无法审计一对一绑定。
        status = "completed" if session_ref == batch.target_ref else "blocked"  # 新增代码+MultiTargetStageLoopTest：target_ref 不一致时阻断；如果没有这行代码，错误窗口写入会被测试放过。
        return StageResult(status=status, stage_id=str(batch.guardrails.get("stage_id", batch.batch_id)), evidence={"primitive_action_count": len(batch.actions), "successful_action_count": len(batch.actions), "low_level_event_count": len(batch.actions)})  # 新增代码+MultiTargetStageLoopTest：返回标准阶段结果；如果没有这行代码，stage loop 无法汇总动作计数。
    # 新增代码+MultiTargetStageLoopTest：函数段结束，RecordingTargetBatchExecutor.execute_batch 到此结束；如果没有这个边界说明，初学者不容易看出执行范围。


def _text_capability(_: dict) -> AppCapabilityProfile:  # 新增代码+MultiTargetStageLoopTest：函数段开始，给测试目标提供文本能力；如果没有这段函数，perform 阶段会退回 probe_batch。
    return AppCapabilityProfile(has_text_input=True, supports_keyboard_shortcuts_likely=True, evidence=("test:text_input",))  # 新增代码+MultiTargetStageLoopTest：返回文本能力画像；如果没有这行代码，多目标写批不会生成。
# 新增代码+MultiTargetStageLoopTest：函数段结束，_text_capability 到此结束；如果没有这个边界说明，初学者不容易看出能力 fake 范围。


def test_planner_represents_two_targets_for_multi_app_task() -> None:  # 新增代码+MultiTargetStageLoopTest：函数段开始，验证 planner 能表达两个目标；如果没有这个测试，多窗口任务可能被压成单窗口。
    plan = UniversalDesktopStagePlanner().plan("请同时使用两个普通应用窗口，把一个窗口的信息整理到另一个窗口。")  # 新增代码+MultiTargetStageLoopTest：生成多目标计划；如果没有这行代码，测试没有计划事实。
    assert plan.task_kind == "multi_app"  # 新增代码+MultiTargetStageLoopTest：确认任务类型是多应用；如果没有这行代码，多目标可能未识别。
    assert len(plan.targets) >= 2  # 新增代码+MultiTargetStageLoopTest：确认至少两个目标描述；如果没有这行代码，一对一窗口绑定无从实现。


def test_multi_target_batches_keep_one_target_ref_and_switch_with_prepare_stages() -> None:  # 新增代码+MultiTargetStageLoopTest：函数段开始，验证多目标批一对一绑定；如果没有这个测试，跨窗口写入可能混到一个窗口。
    executor = RecordingTargetBatchExecutor()  # 新增代码+MultiTargetStageLoopTest：创建记录执行器；如果没有这行代码，无法检查批目标。
    report = UniversalStageTaskLoop(observation_runtime=MultiTargetObservation(), target_runtime=MultiTargetRuntime(), capability_profile_builder=_text_capability, batch_executor=executor).run_desktop_task("请同时使用两个普通应用窗口，把一个窗口的信息整理到另一个窗口。")  # 新增代码+MultiTargetStageLoopTest：运行多目标任务；如果没有这行代码，无法获得阶段报告。
    assert report["target_ref_one_to_one"] is True  # 新增代码+MultiTargetStageLoopTest：确认 target_ref 唯一；如果没有这行代码，重复目标键可能漏过。
    assert any(stage["stage_kind"] == "prepare_target" and stage["target_ref"] == "target_2" for stage in report["desktop_task_plan"]["stages"])  # 新增代码+MultiTargetStageLoopTest：确认切换到第二目标前有准备阶段；如果没有这行代码，多窗口切换可能缺 focus/观察。
    assert all(session_ref == batch_ref for session_ref, batch_ref, _ in executor.records)  # 新增代码+MultiTargetStageLoopTest：确认每个批只在对应 session 执行；如果没有这行代码，target A 写到 target B 不会失败。


def test_user_owned_existing_window_requires_explicit_grant_before_reuse() -> None:  # 新增代码+MultiTargetStageLoopTest：函数段开始，验证未授权已有窗口阻断；如果没有这个测试，单实例应用旧窗口会被默认接管。
    report = UniversalStageTaskLoop(observation_runtime=MultiTargetObservation(), target_runtime=MultiTargetRuntime(preexisting=True, granted=False), capability_profile_builder=_text_capability, batch_executor=RecordingTargetBatchExecutor()).run_desktop_task("请输入 hello everyone")  # 新增代码+MultiTargetStageLoopTest：运行旧窗口未授权场景；如果没有这行代码，无法触发阻断。
    assert report["desktop_task_incomplete"] is True  # 新增代码+MultiTargetStageLoopTest：确认任务未完成；如果没有这行代码，旧窗口阻断可能被误当成功。
    assert report["needs_user"] is True  # 新增代码+MultiTargetStageLoopTest：确认需要用户动作；如果没有这行代码，final gate 无法请求用户关闭或授权。
    assert report["run_state"]["blocked_target_refs"] == ["target_1"]  # 新增代码+MultiTargetStageLoopTest：确认阻断目标进入 run state；如果没有这行代码，后续无法避免重复动作。
