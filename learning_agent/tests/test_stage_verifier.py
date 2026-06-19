from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import DesktopTaskPlan, StagePlan, StageResult  # 新增代码+StageVerifierTest：导入通用模型；如果没有这行代码，测试无法构造计划、阶段和执行结果。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_verifier import UniversalStageVerifier  # 新增代码+StageVerifierTest：导入阶段验收器；如果没有这行代码，测试无法验证完成判断。


def _plan(task_kind: str, criteria: tuple[str, ...] = ()) -> DesktopTaskPlan:  # 新增代码+StageVerifierTest：函数段开始，构造测试计划；如果没有这段函数，多测试会重复样板。
    return DesktopTaskPlan(objective="sample", task_kind=task_kind, targets=({"target_id": "target-a"},), success_criteria=criteria, stages=())  # 新增代码+StageVerifierTest：返回最小计划；如果没有这行代码，verifier 没有任务类型输入。
# 新增代码+StageVerifierTest：函数段结束，_plan 到此结束；如果没有这个边界说明，初学者不容易看出计划构造范围。


def _stage(stage_kind: str = "perform_content_work") -> StagePlan:  # 新增代码+StageVerifierTest：函数段开始，构造测试阶段；如果没有这段函数，测试会重复阶段字段。
    return StagePlan(stage_id="stage-a", stage_kind=stage_kind, target_ref="target-a", observation_policy="before_and_after_stage", verifier={"requested_text": "hello everyone"})  # 新增代码+StageVerifierTest：返回最小阶段；如果没有这行代码，verifier 没有阶段输入。
# 新增代码+StageVerifierTest：函数段结束，_stage 到此结束；如果没有这个边界说明，初学者不容易看出阶段构造范围。


def _execution(status: str = "completed") -> StageResult:  # 新增代码+StageVerifierTest：函数段开始，构造执行结果；如果没有这段函数，测试会重复事件证据。
    return StageResult(status=status, stage_id="stage-a", evidence={"low_level_event_count": 4, "successful_action_count": 2})  # 新增代码+StageVerifierTest：返回带事件计数的结果；如果没有这行代码，verifier 没有执行事实。
# 新增代码+StageVerifierTest：函数段结束，_execution 到此结束；如果没有这个边界说明，初学者不容易看出执行结果范围。


def test_text_stage_verifies_from_post_observation_text() -> None:  # 新增代码+StageVerifierTest：函数段开始，验证文本任务靠观察文本完成；如果没有这个测试，事件发送可能被误当成功。
    after = {"visible_text": "hello everyone", "target_identity_verified": True}  # 新增代码+StageVerifierTest：构造含目标文本的后置观察；如果没有这行代码，verifier 没有完成证据。
    result = UniversalStageVerifier().verify_stage(_plan("text_entry"), _stage(), {}, after, _execution())  # 新增代码+StageVerifierTest：执行验收；如果没有这行代码，无法断言状态。
    assert result.status == "completed"  # 新增代码+StageVerifierTest：确认文本阶段完成；如果没有这行代码，文本观察路径不可见。


def test_drawing_stage_verifies_from_canvas_change_and_visual_structure() -> None:  # 新增代码+StageVerifierTest：函数段开始，验证绘图任务靠画布变化和视觉结构完成；如果没有这个测试，单纯事件计数可能误过。
    after = {"canvas_changed_after_actions": True, "visual_primitives": ["outline", "color_block"], "target_identity_verified": True}  # 新增代码+StageVerifierTest：构造画布变化证据；如果没有这行代码，绘图验收没有观察事实。
    result = UniversalStageVerifier().verify_stage(_plan("drawing"), _stage(), {}, after, _execution())  # 新增代码+StageVerifierTest：执行绘图验收；如果没有这行代码，无法读取结果。
    assert result.status == "completed"  # 新增代码+StageVerifierTest：确认绘图阶段完成；如果没有这行代码，复杂绘图会继续被误判未完成。


def test_save_stage_verifies_from_resource_commit_evidence() -> None:  # 新增代码+StageVerifierTest：函数段开始，验证保存阶段靠保存证据完成；如果没有这个测试，保存可能只按了快捷键就算成功。
    after = {"saved_resource_exists": True, "target_identity_verified": True}  # 新增代码+StageVerifierTest：构造资源保存证据；如果没有这行代码，保存验收没有事实。
    result = UniversalStageVerifier().verify_stage(_plan("text_entry", ("resource_commit_verified",)), _stage("commit_resource"), {}, after, _execution())  # 新增代码+StageVerifierTest：执行保存验收；如果没有这行代码，无法断言保存状态。
    assert result.status == "completed"  # 新增代码+StageVerifierTest：确认保存阶段完成；如果没有这行代码，提交资源验收不可见。


def test_incomplete_stage_returns_needs_repair_not_success() -> None:  # 新增代码+StageVerifierTest：函数段开始，验证缺观察证据时需要修复；如果没有这个测试，事件数可能误导 final gate。
    result = UniversalStageVerifier().verify_stage(_plan("drawing"), _stage(), {}, {"target_identity_verified": True}, _execution())  # 新增代码+StageVerifierTest：执行缺画布证据验收；如果没有这行代码，无法触发未完成路径。
    assert result.status == "needs_repair"  # 新增代码+StageVerifierTest：确认返回需要修复；如果没有这行代码，未完成任务可能被最终回答。


def test_ambiguous_target_blocks_or_needs_user() -> None:  # 新增代码+StageVerifierTest：函数段开始，验证目标不明确不继续成功；如果没有这个测试，多窗口漂移可能误过。
    result = UniversalStageVerifier().verify_stage(_plan("text_entry"), _stage(), {}, {"target_ambiguous": True}, _execution())  # 新增代码+StageVerifierTest：执行目标不明确验收；如果没有这行代码，无法触发阻断路径。
    assert result.status in {"blocked", "needs_user"}  # 新增代码+StageVerifierTest：确认不会成功；如果没有这行代码，错误窗口可能被继续操作。
