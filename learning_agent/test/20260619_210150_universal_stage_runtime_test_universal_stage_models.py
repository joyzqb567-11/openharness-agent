import pytest  # 新增代码+UniversalStageModelsTest：导入 pytest 用于断言异常；如果没有这行代码，模型非法状态无法被测试捕获。

from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import (  # 新增代码+UniversalStageModelsTest：导入待验证的通用阶段模型；如果没有这段导入，测试无法证明数据层存在。
    ActionBatch,  # 新增代码+UniversalStageModelsTest：导入动作批模型；如果没有这行代码，测试无法验证 target_ref 门禁。
    DesktopTaskPlan,  # 新增代码+UniversalStageModelsTest：导入桌面任务计划模型；如果没有这行代码，测试无法验证计划可序列化。
    StagePlan,  # 新增代码+UniversalStageModelsTest：导入阶段计划模型；如果没有这行代码，测试无法验证 stage_id 必填。
    StageResult,  # 新增代码+UniversalStageModelsTest：导入阶段结果模型；如果没有这行代码，测试无法验证状态枚举。
    desktop_task_plan_from_dict,  # 新增代码+UniversalStageModelsTest：导入反序列化 helper；如果没有这行代码，测试无法证明 JSON 证据可恢复。
    desktop_task_plan_to_dict,  # 新增代码+UniversalStageModelsTest：导入序列化 helper；如果没有这行代码，测试无法证明计划可落盘。
    stage_result_to_dict,  # 新增代码+UniversalStageModelsTest：导入阶段结果序列化 helper；如果没有这行代码，测试无法证明 verifier 结果可审计。
)  # 新增代码+UniversalStageModelsTest：导入段结束；如果没有这行代码，Python 语法不完整。


def test_desktop_task_plan_round_trips_json_safe_dict() -> None:  # 新增代码+UniversalStageModelsTest：函数段开始，验证任务计划可 JSON 往返；如果没有这个测试，后续 acceptance 证据可能不可落盘。
    batch = ActionBatch(batch_id="batch-1", batch_kind="text_entry_batch", target_ref="target-a", actions=({"type": "focus_window"},))  # 新增代码+UniversalStageModelsTest：构造带目标的文本批；如果没有这行代码，计划缺少可执行阶段样本。
    stage = StagePlan(stage_id="stage_001_write", stage_kind="perform_content_work", target_ref="target-a", observation_policy="before_and_after_stage", batch=batch)  # 新增代码+UniversalStageModelsTest：构造写入阶段；如果没有这行代码，计划无法覆盖嵌套批序列化。
    plan = DesktopTaskPlan(objective="write text", task_kind="text_entry", targets=({"target_id": "target-a"},), resources=(), success_criteria=("text visible",), stages=(stage,))  # 新增代码+UniversalStageModelsTest：构造完整桌面任务计划；如果没有这行代码，helper 没有输入。
    payload = desktop_task_plan_to_dict(plan)  # 新增代码+UniversalStageModelsTest：把计划转成 dict；如果没有这行代码，无法验证 JSON 安全结构。
    restored = desktop_task_plan_from_dict(payload)  # 新增代码+UniversalStageModelsTest：从 dict 恢复计划；如果没有这行代码，无法验证证据可重放。
    assert payload["stages"][0]["batch"]["target_ref"] == "target-a"  # 新增代码+UniversalStageModelsTest：确认嵌套 target_ref 未丢；如果没有这行代码，一对一窗口绑定可能被序列化丢失。
    assert restored.stages[0].batch is not None  # 新增代码+UniversalStageModelsTest：确认批对象恢复存在；如果没有这行代码，反序列化可能只剩 dict。
    assert restored.stages[0].batch.actions[0]["type"] == "focus_window"  # 新增代码+UniversalStageModelsTest：确认动作内容恢复；如果没有这行代码，批执行层可能拿不到 primitive。


def test_stage_plan_requires_stable_stage_id() -> None:  # 新增代码+UniversalStageModelsTest：函数段开始，验证阶段 id 必填；如果没有这个测试，失败修复无法定位阶段。
    with pytest.raises(ValueError, match="stage_id"):  # 新增代码+UniversalStageModelsTest：期待空阶段 id 抛错；如果没有这行代码，非法阶段可能静默进入运行时。
        StagePlan(stage_id="", stage_kind="prepare_target", target_ref="", observation_policy="before_stage")  # 新增代码+UniversalStageModelsTest：构造非法阶段；如果没有这行代码，异常路径无法触发。


def test_action_batch_requires_target_ref_for_write_batches() -> None:  # 新增代码+UniversalStageModelsTest：函数段开始，验证写批必须绑定目标；如果没有这个测试，通用 Computer Use 可能写到错误窗口。
    with pytest.raises(ValueError, match="target_ref"):  # 新增代码+UniversalStageModelsTest：期待缺 target_ref 抛错；如果没有这行代码，测试不会检查安全边界。
        ActionBatch(batch_id="batch-unsafe", batch_kind="text_entry_batch", target_ref="", actions=({"type": "type_text"},))  # 新增代码+UniversalStageModelsTest：构造缺目标写批；如果没有这行代码，无法验证门禁。


def test_stage_result_status_is_explicit_and_serializable() -> None:  # 新增代码+UniversalStageModelsTest：函数段开始，验证阶段结果状态集合；如果没有这个测试，最终门禁可能读到乱状态。
    result = StageResult(status="completed", stage_id="stage_001", evidence={"desktop_task_completed": True})  # 新增代码+UniversalStageModelsTest：构造完成结果；如果没有这行代码，序列化 helper 没有输入。
    payload = stage_result_to_dict(result)  # 新增代码+UniversalStageModelsTest：序列化结果；如果没有这行代码，无法验证输出字段。
    assert payload["status"] == "completed"  # 新增代码+UniversalStageModelsTest：确认状态保留；如果没有这行代码，最终门禁无法判断完成。
    assert payload["evidence"]["desktop_task_completed"] is True  # 新增代码+UniversalStageModelsTest：确认证据保留；如果没有这行代码，验收字段可能丢失。
    with pytest.raises(ValueError, match="status"):  # 新增代码+UniversalStageModelsTest：期待非法状态抛错；如果没有这行代码，错误状态可能进入报告。
        StageResult(status="done-ish", stage_id="stage_bad")  # 新增代码+UniversalStageModelsTest：构造非法状态；如果没有这行代码，异常路径无法覆盖。
