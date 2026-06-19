import pytest  # 新增代码+LayeredHarnessContextTest：导入 pytest 验证异常路径；如果没有这行代码，缺 target_ref 的安全门禁无法测试。

from learning_agent.computer_use_mcp_v2.windows_runtime.harness_context import ComputerUseHarnessSnapshot, ComputerUsePermissionState, ComputerUseTaskContext, ComputerUseToolUseContext  # 新增代码+LayeredHarnessContextTest：导入待测上下文模型；如果没有这行代码，测试无法覆盖新 harness 契约。


def test_task_context_has_stable_task_id_when_stage_changes() -> None:  # 新增代码+LayeredHarnessContextTest：函数段开始，验证阶段切换不改变任务 id；如果没有这段测试，长任务可能被拆成多个无关任务。
    context = ComputerUseTaskContext(current_stage_id="stage_001")  # 新增代码+LayeredHarnessContextTest：创建初始任务上下文；如果没有这行代码，测试没有原始 task_id。
    moved = context.with_stage("stage_002")  # 新增代码+LayeredHarnessContextTest：切换到下一阶段；如果没有这行代码，无法证明 task_id 稳定。
    assert context.task_id == moved.task_id  # 新增代码+LayeredHarnessContextTest：确认同一任务 id 被保留；如果没有这行断言，回归不会被发现。
    assert moved.current_stage_id == "stage_002"  # 新增代码+LayeredHarnessContextTest：确认当前阶段已更新；如果没有这行断言，with_stage 可能没有效果。
    # 新增代码+LayeredHarnessContextTest：函数段结束，test_task_context_has_stable_task_id_when_stage_changes 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_task_context_records_targets_permission_verifier_and_reflection() -> None:  # 新增代码+LayeredHarnessContextTest：函数段开始，验证上下文保存关键 harness 状态；如果没有这段测试，权限和验证状态可能丢失。
    permission = ComputerUsePermissionState(full_mode_enabled=True, request_access_granted=True, allowed_target_refs=("target_1",), allowed_action_classes=("type_text",))  # 新增代码+LayeredHarnessContextTest：构造授权状态；如果没有这行代码，测试不能覆盖 permission_state。
    context = ComputerUseTaskContext(current_stage_id="stage_003", allowed_target_refs=("target_1",), permission_state=permission, verifier_state={"verified": False, "missing_requirements": ["save"]}, reflection_state={"failure_class": "save_dialog_unhandled"})  # 新增代码+LayeredHarnessContextTest：构造完整任务上下文；如果没有这行代码，测试不能覆盖 verifier/reflection。
    payload = context.to_dict()  # 新增代码+LayeredHarnessContextTest：序列化上下文；如果没有这行代码，无法检查 JSON 形状。
    assert payload["current_stage_id"] == "stage_003"  # 新增代码+LayeredHarnessContextTest：确认阶段 id 被记录；如果没有这行断言，阶段状态可能丢失。
    assert payload["allowed_target_refs"] == ["target_1"]  # 新增代码+LayeredHarnessContextTest：确认 allowed target refs 被记录；如果没有这行断言，目标约束可能丢失。
    assert payload["permission_state"]["full_mode_enabled"] is True  # 新增代码+LayeredHarnessContextTest：确认 full mode 状态被记录；如果没有这行断言，权限状态可能丢失。
    assert payload["verifier_state"]["missing_requirements"] == ["save"]  # 新增代码+LayeredHarnessContextTest：确认 verifier 状态被记录；如果没有这行断言，验证缺口无法反馈。
    assert payload["reflection_state"]["failure_class"] == "save_dialog_unhandled"  # 新增代码+LayeredHarnessContextTest：确认 reflection 状态被记录；如果没有这行断言，失败学习无法反馈。
    # 新增代码+LayeredHarnessContextTest：函数段结束，test_task_context_records_targets_permission_verifier_and_reflection 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_context_json_excludes_raw_screenshots_and_private_text() -> None:  # 新增代码+LayeredHarnessContextTest：函数段开始，验证上下文 JSON 不保存敏感原始数据；如果没有这段测试，隐私边界可能回归。
    context = ComputerUseTaskContext(verifier_state={"raw_screenshot": "base64", "safe": "ok"}, reflection_state={"raw_private_text": "secret", "failure_class": "wrong_region"})  # 新增代码+LayeredHarnessContextTest：构造含敏感字段的上下文；如果没有这行代码，无法验证脱敏。
    tool_context = ComputerUseToolUseContext(tool_use_id="tool_1", stage_id="stage_1", target_ref="target_1", action_class="type_text", metadata={"raw_prompt": "private", "decision": "ok"})  # 新增代码+LayeredHarnessContextTest：构造含敏感元数据的工具上下文；如果没有这行代码，工具层脱敏无法覆盖。
    snapshot = ComputerUseHarnessSnapshot(task_context=context, tool_use_context=tool_context, evidence={"screenshot_bytes": "bytes", "summary": "safe"})  # 新增代码+LayeredHarnessContextTest：构造含敏感 evidence 的快照；如果没有这行代码，快照脱敏无法验证。
    payload = snapshot.to_dict()  # 新增代码+LayeredHarnessContextTest：序列化快照；如果没有这行代码，无法检查输出内容。
    assert "raw_screenshot" not in payload["task_context"]["verifier_state"]  # 新增代码+LayeredHarnessContextTest：确认原始截图被移除；如果没有这行断言，截图可能进入日志。
    assert "raw_private_text" not in payload["task_context"]["reflection_state"]  # 新增代码+LayeredHarnessContextTest：确认私密文本被移除；如果没有这行断言，用户内容可能泄露。
    assert "raw_prompt" not in payload["tool_use_context"]["metadata"]  # 新增代码+LayeredHarnessContextTest：确认原始 prompt 被移除；如果没有这行断言，工具上下文可能保存私密输入。
    assert "screenshot_bytes" not in payload["evidence"]  # 新增代码+LayeredHarnessContextTest：确认截图字节被移除；如果没有这行断言，快照 evidence 会绕过脱敏。
    assert payload["evidence"]["summary"] == "safe"  # 新增代码+LayeredHarnessContextTest：确认低敏摘要保留；如果没有这行断言，脱敏可能过度删除可用证据。
    # 新增代码+LayeredHarnessContextTest：函数段结束，test_context_json_excludes_raw_screenshots_and_private_text 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_write_batch_without_target_ref_is_refused() -> None:  # 新增代码+LayeredHarnessContextTest：函数段开始，验证写动作必须绑定 target_ref；如果没有这段测试，真实桌面动作可能默认接管旧窗口。
    with pytest.raises(ValueError):  # 新增代码+LayeredHarnessContextTest：期待安全门禁抛错；如果没有这行代码，异常路径不会被检查。
        ComputerUseToolUseContext(tool_use_id="tool_2", stage_id="stage_1", action_class="type_text")  # 新增代码+LayeredHarnessContextTest：构造缺 target_ref 的写动作；如果没有这行代码，门禁没有触发条件。
    # 新增代码+LayeredHarnessContextTest：函数段结束，test_write_batch_without_target_ref_is_refused 到此结束；如果没有这个边界说明，用户不容易看出测试范围。
