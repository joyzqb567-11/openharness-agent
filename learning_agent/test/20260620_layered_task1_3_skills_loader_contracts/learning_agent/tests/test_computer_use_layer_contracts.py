from learning_agent.computer_use_mcp_v2.windows_runtime.layer_contracts import GENERIC_FAILURE_CLASSES, GENERIC_STAGE_KINDS, GENERIC_TASK_KINDS, IntentUnderstandingResult, ObservationFacts, ReflectionLearningResult, StagePlanningResult, StageVerificationResult  # 新增代码+LayerContractsTest：导入所有层契约；如果没有这行代码，JSON round-trip 和 enum 安全无法测试。


def test_intent_understanding_result_round_trip() -> None:  # 新增代码+LayerContractsTest：函数段开始，验证 intent 契约可 JSON 往返；如果没有这段测试，planner 可能无法消费落盘 intent。
    result = IntentUnderstandingResult(objective="create text", task_kind="text_entry", target_app_hints=("text editor",), required_targets=({"target_ref": "target_1"},), content_payloads=("hello",), artifact_requests=({"location": "desktop"},), success_criteria=("text_saved",), requires_fresh_resource=True, layer_skill_metadata={"layer_name": "intent_understanding"})  # 新增代码+LayerContractsTest：构造代表性 intent；如果没有这行代码，round-trip 没有输入。
    restored = IntentUnderstandingResult.from_dict(result.to_dict())  # 新增代码+LayerContractsTest：执行序列化再反序列化；如果没有这行代码，无法证明 JSON 兼容。
    assert restored == result  # 新增代码+LayerContractsTest：确认往返后相等；如果没有这行断言，字段丢失不会被发现。
    # 新增代码+LayerContractsTest：函数段结束，test_intent_understanding_result_round_trip 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_observation_facts_round_trip() -> None:  # 新增代码+LayerContractsTest：函数段开始，验证观察事实可 JSON 往返；如果没有这段测试，stage loop 无法可靠保存 facts。
    facts = ObservationFacts(active_target_ref="target_1", target_identity_verified=True, target_window_freshness="fresh_agent_owned_window", editable_regions=({"id": "edit_1"},), canvas_regions=({"id": "canvas_1"},), save_dialog_state={"open": False}, capability_profile={"has_text_input": True})  # 新增代码+LayerContractsTest：构造代表性观察事实；如果没有这行代码，round-trip 没有输入。
    restored = ObservationFacts.from_dict(facts.to_dict())  # 新增代码+LayerContractsTest：执行序列化再恢复；如果没有这行代码，无法验证 JSON 兼容。
    assert restored == facts  # 新增代码+LayerContractsTest：确认恢复一致；如果没有这行断言，区域或能力字段丢失不会被发现。
    # 新增代码+LayerContractsTest：函数段结束，test_observation_facts_round_trip 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_stage_planning_result_round_trip() -> None:  # 新增代码+LayerContractsTest：函数段开始，验证阶段规划结果可 JSON 往返；如果没有这段测试，阶段计划无法稳定落盘。
    result = StagePlanningResult(objective="draw shape", task_kind="drawing", stages=({"stage_id": "stage_001", "stage_kind": "perform_canvas_work", "target_ref": "target_1"},), success_criteria=("canvas_changed",), layer_skill_metadata={"layer_name": "stage_planning"})  # 新增代码+LayerContractsTest：构造代表性规划结果；如果没有这行代码，round-trip 没有输入。
    restored = StagePlanningResult.from_dict(result.to_dict())  # 新增代码+LayerContractsTest：执行序列化再恢复；如果没有这行代码，无法验证 JSON 兼容。
    assert restored == result  # 新增代码+LayerContractsTest：确认恢复一致；如果没有这行断言，阶段字段丢失不会被发现。
    # 新增代码+LayerContractsTest：函数段结束，test_stage_planning_result_round_trip 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_stage_verification_result_round_trip() -> None:  # 新增代码+LayerContractsTest：函数段开始，验证验证结果可 JSON 往返；如果没有这段测试，final gate 不能稳定读取 verifier 输出。
    result = StageVerificationResult(verified=False, missing_requirements=("resource_commit_verified",), next_required_stage="stage_004_commit_resource", needs_reflection=True, evidence_summary="save not verified", layer_skill_metadata={"layer_name": "verification"})  # 新增代码+LayerContractsTest：构造代表性 verifier 结果；如果没有这行代码，round-trip 没有输入。
    restored = StageVerificationResult.from_dict(result.to_dict())  # 新增代码+LayerContractsTest：执行序列化再恢复；如果没有这行代码，无法验证 JSON 兼容。
    assert restored == result  # 新增代码+LayerContractsTest：确认恢复一致；如果没有这行断言，缺失要求可能丢失。
    # 新增代码+LayerContractsTest：函数段结束，test_stage_verification_result_round_trip 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_reflection_learning_result_round_trip() -> None:  # 新增代码+LayerContractsTest：函数段开始，验证反思学习结果可 JSON 往返；如果没有这段测试，失败经验无法稳定保存。
    result = ReflectionLearningResult(failure_class="batch_too_small", evidence_summary="only one primitive action", repair_strategy="compile_larger_stage_batch", replan_required=True, learning_candidate={"count": 2}, layer_skill_metadata={"layer_name": "reflection_learning"})  # 新增代码+LayerContractsTest：构造代表性 reflection 结果；如果没有这行代码，round-trip 没有输入。
    restored = ReflectionLearningResult.from_dict(result.to_dict())  # 新增代码+LayerContractsTest：执行序列化再恢复；如果没有这行代码，无法验证 JSON 兼容。
    assert restored == result  # 新增代码+LayerContractsTest：确认恢复一致；如果没有这行断言，学习候选可能丢失。
    # 新增代码+LayerContractsTest：函数段结束，test_reflection_learning_result_round_trip 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_core_contract_terms_do_not_contain_app_specific_names() -> None:  # 新增代码+LayerContractsTest：函数段开始，验证核心 enum 不含具体软件名；如果没有这段测试，通用 Computer Use 会退回单软件特判。
    forbidden = {"notepad", "paint", "mspaint", "wechat", "chrome", "edge", "wps", "word"}  # 新增代码+LayerContractsTest：列出禁止进入核心词表的软件名；如果没有这行代码，测试缺判断目标。
    all_terms = set(GENERIC_TASK_KINDS) | set(GENERIC_STAGE_KINDS) | set(GENERIC_FAILURE_CLASSES)  # 新增代码+LayerContractsTest：收集核心通用词表；如果没有这行代码，不能统一扫描。
    lowered_blob = " ".join(sorted(all_terms)).lower()  # 新增代码+LayerContractsTest：拼成小写文本便于包含判断；如果没有这行代码，大小写可能影响结果。
    assert not any(name in lowered_blob for name in forbidden)  # 新增代码+LayerContractsTest：确认没有具体软件名；如果没有这行断言，应用名可能悄悄进入核心 contract。
    # 新增代码+LayerContractsTest：函数段结束，test_core_contract_terms_do_not_contain_app_specific_names 到此结束；如果没有这个边界说明，用户不容易看出测试范围。
