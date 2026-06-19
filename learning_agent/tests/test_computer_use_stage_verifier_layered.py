from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import DesktopTaskPlan, StagePlan, StageResult  # 新增代码+LayeredVerifierTest：导入阶段模型；如果没有这行代码，测试无法构造分层计划和阶段结果。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_verifier import UniversalStageVerifier  # 新增代码+LayeredVerifierTest：导入通用阶段验证器；如果没有这行代码，测试无法验证 false-success 门禁。
from learning_agent.core.convergence_controller import assess_final_answer_for_desktop_task  # 新增代码+LayeredVerifierTest：导入最终回答备份门禁；如果没有这行代码，Next desktop action 文本回归无法覆盖。


def _plan(task_kind: str = "text_entry", criteria: tuple[str, ...] = ()) -> DesktopTaskPlan:  # 新增代码+LayeredVerifierTest：函数段开始，构造含成功标准的测试计划；如果没有这段函数，多个测试会重复样板。
    return DesktopTaskPlan(objective="sample desktop task", task_kind=task_kind, targets=({"target_id": "target-a"},), success_criteria=criteria, stages=())  # 新增代码+LayeredVerifierTest：返回最小桌面任务计划；如果没有这行代码，verifier 没有 intent 成功标准输入。
# 新增代码+LayeredVerifierTest：函数段结束，_plan 到此结束；如果没有这个边界说明，用户不容易看出计划构造范围。


def _stage(stage_kind: str = "perform_content_work", verifier: dict | None = None) -> StagePlan:  # 新增代码+LayeredVerifierTest：函数段开始，构造测试阶段；如果没有这段函数，测试会重复阶段字段。
    return StagePlan(stage_id="stage-a", stage_kind=stage_kind, target_ref="target-a", observation_policy="before_and_after_stage", verifier=dict(verifier or {"requested_text": "hello everyone"}))  # 新增代码+LayeredVerifierTest：返回绑定目标的阶段；如果没有这行代码，verifier 无法知道阶段类型和文本目标。
# 新增代码+LayeredVerifierTest：函数段结束，_stage 到此结束；如果没有这个边界说明，用户不容易看出阶段构造范围。


def _execution(status: str = "completed", decision: str = "batch_completed") -> StageResult:  # 新增代码+LayeredVerifierTest：函数段开始，构造执行结果；如果没有这段函数，测试会重复低层事件证据。
    return StageResult(status=status, stage_id="stage-a", evidence={"decision": decision, "low_level_event_count": 6, "successful_action_count": 2})  # 新增代码+LayeredVerifierTest：返回带执行证据的阶段结果；如果没有这行代码，verifier 缺少动作层输入。
# 新增代码+LayeredVerifierTest：函数段结束，_execution 到此结束；如果没有这个边界说明，用户不容易看出执行结果构造范围。


def test_text_stage_cannot_complete_when_required_text_is_missing() -> None:  # 新增代码+LayeredVerifierTest：函数段开始，验证文本缺失不能成功；如果没有这个测试，低层键盘事件可能被误当输入完成。
    result = UniversalStageVerifier().verify_stage(_plan("text_entry"), _stage(), {}, {"visible_text_summary": ""}, _execution())  # 新增代码+LayeredVerifierTest：用空文本观察执行验证；如果没有这行代码，无法触发缺文本场景。
    assert result.status == "needs_repair"  # 新增代码+LayeredVerifierTest：确认缺文本需要修复；如果没有这行代码，未完成文本任务可能 final。
    assert result.evidence["decision"] == "text_not_visible_after_batch"  # 新增代码+LayeredVerifierTest：确认原因码明确；如果没有这行代码，反思层无法知道修复文本输入。


def test_verify_stage_reports_missing_requirements_from_success_criteria() -> None:  # 新增代码+LayeredVerifierTest：函数段开始，验证最终阶段按 intent 成功标准检查缺失项；如果没有这个测试，observe 成功会掩盖业务未完成。
    plan = _plan("text_entry", ("requested_text_visible", "resource_commit_verified"))  # 新增代码+LayeredVerifierTest：构造要求文本可见且资源已保存的计划；如果没有这行代码，missing_requirements 无输入。
    stage = _stage("verify_result", {"requested_text": "hello everyone"})  # 新增代码+LayeredVerifierTest：构造最终验证阶段；如果没有这行代码，verifier 不会走 final criteria 分支。
    after = {"visible_text_summary": "hello everyone", "save_dialog_state": {"completed": False}}  # 新增代码+LayeredVerifierTest：构造文本已见但保存未完成的观察事实；如果没有这行代码，无法验证缺保存标准。
    result = UniversalStageVerifier().verify_stage(plan, stage, {}, after, _execution())  # 新增代码+LayeredVerifierTest：执行最终阶段验证；如果没有这行代码，无法读取缺失标准结果。
    assert result.status == "needs_repair"  # 新增代码+LayeredVerifierTest：确认最终阶段不能完成；如果没有这行代码，未保存任务可能被误 final。
    assert result.evidence["decision"] == "missing_requirements"  # 新增代码+LayeredVerifierTest：确认机器可读缺失原因；如果没有这行代码，final gate 和反思层难以识别。
    assert "resource_commit_verified" in result.evidence["missing_requirements"]  # 新增代码+LayeredVerifierTest：确认缺失项指向保存要求；如果没有这行代码，修复策略无法定位保存阶段。


def test_save_verification_missing_returns_needs_repair_not_success() -> None:  # 新增代码+LayeredVerifierTest：函数段开始，验证保存缺证据不能完成；如果没有这个测试，Ctrl+S 触发但未保存可能误过。
    result = UniversalStageVerifier().verify_stage(_plan("text_entry", ("resource_commit_verified",)), _stage("commit_resource"), {}, {"save_dialog_state": {"completed": False}}, _execution())  # 新增代码+LayeredVerifierTest：用未完成保存状态验证提交阶段；如果没有这行代码，无法触发保存缺证据。
    assert result.status == "needs_repair"  # 新增代码+LayeredVerifierTest：确认保存阶段需要修复；如果没有这行代码，未保存结果可能进入最终回答。
    assert result.evidence["decision"] == "resource_commit_not_verified"  # 新增代码+LayeredVerifierTest：确认保存缺失原因码；如果没有这行代码，后续修复不知道要处理保存。


def test_final_gate_blocks_next_desktop_action_text_without_stage_evidence() -> None:  # 新增代码+LayeredVerifierTest：函数段开始，验证 Next desktop action 文本不能当最终回答；如果没有这个测试，模型可能把待执行动作说成结束。
    decision = assess_final_answer_for_desktop_task("Next desktop action: draw the missing opposite diagonal line.", {})  # 新增代码+LayeredVerifierTest：评估带下一步动作语义的回答；如果没有这行代码，备份门禁没有输入。
    assert decision.allow_final_answer is False  # 新增代码+LayeredVerifierTest：确认最终回答被阻断；如果没有这行代码，复杂桌面任务会早停。
    assert decision.reason == "desktop_task_incomplete_text_marker"  # 新增代码+LayeredVerifierTest：确认原因是未完成文本信号；如果没有这行代码，失败复盘无法定位最终门禁。


def test_final_gate_blocks_success_claim_when_stage_counts_are_incomplete() -> None:  # 新增代码+LayeredVerifierTest：函数段开始，验证结构化阶段未完成时成功话术被挡；如果没有这个测试，模型可能在一半阶段后输出 OK。
    runtime_state = {"computer_use_stage_evidence": {"desktop_task_incomplete": True, "desktop_task_completed": False, "stage_count": 5, "completed_stage_count": 3}}  # 新增代码+LayeredVerifierTest：构造未完成阶段证据；如果没有这行代码，final gate 缺少结构化事实。
    decision = assess_final_answer_for_desktop_task("OPENHARNESS_LAYERED_TEXT_OK saved_to_desktop=true", runtime_state)  # 新增代码+LayeredVerifierTest：评估虚假成功回答；如果没有这行代码，无法检查成功话术门禁。
    assert decision.allow_final_answer is False  # 新增代码+LayeredVerifierTest：确认未完成结构化证据阻断成功回答；如果没有这行代码，false-success 会回归。
    assert decision.reason == "desktop_task_incomplete"  # 新增代码+LayeredVerifierTest：确认原因码稳定；如果没有这行代码，日志难以统计未完成阻断。
