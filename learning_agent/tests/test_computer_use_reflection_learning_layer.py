import json  # 新增代码+ReflectionLearningTest：导入 JSON 用于检查 JSONL 内容；如果没有这行代码，测试无法解析学习文件。

from learning_agent.computer_use_mcp_v2.windows_runtime.reflection_learning_layer import ReflectionLearningLayer  # 新增代码+ReflectionLearningTest：导入反思学习层；如果没有这行代码，测试无法验证失败分类和脱敏落盘。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import StageResult  # 新增代码+ReflectionLearningTest：导入阶段结果模型；如果没有这行代码，测试无法构造 verifier/action 结果。


def _result(decision: str, low_level_event_count: int = 6, primitive_action_count: int = 3) -> StageResult:  # 新增代码+ReflectionLearningTest：函数段开始，构造测试阶段结果；如果没有这段函数，多测试会重复证据样板。
    return StageResult(status="needs_repair", stage_id="stage-a", evidence={"decision": decision, "low_level_event_count": low_level_event_count, "primitive_action_count": primitive_action_count})  # 新增代码+ReflectionLearningTest：返回带决策码和动作规模的结果；如果没有这行代码，反思层没有分类输入。
# 新增代码+ReflectionLearningTest：函数段结束，_result 到此结束；如果没有这个边界说明，用户不容易看出阶段结果构造范围。


def _action(low_level_event_count: int = 6, primitive_action_count: int = 3, decision: str = "batch_completed") -> StageResult:  # 新增代码+ReflectionLearningTest：函数段开始，构造动作执行结果；如果没有这段函数，批大小测试缺少输入。
    return StageResult(status="completed", stage_id="stage-a", evidence={"decision": decision, "low_level_event_count": low_level_event_count, "primitive_action_count": primitive_action_count})  # 新增代码+ReflectionLearningTest：返回动作层结果；如果没有这行代码，反思层无法判断低层事件规模。
# 新增代码+ReflectionLearningTest：函数段结束，_action 到此结束；如果没有这个边界说明，用户不容易看出动作结果构造范围。


def test_reflection_classifies_wrong_region(tmp_path) -> None:  # 新增代码+ReflectionLearningTest：函数段开始，验证区域错误分类；如果没有这个测试，点错画布/输入区会被误归因。
    layer = ReflectionLearningLayer(patterns_path=tmp_path / "patterns.jsonl")  # 新增代码+ReflectionLearningTest：创建独立学习层；如果没有这行代码，测试会污染真实 runtime_learning。
    reflection = layer.reflect_stage_failure("stage-a", _result("wrong_region_selected"), {"region": "wrong"}, _action())  # 新增代码+ReflectionLearningTest：输入区域错误证据；如果没有这行代码，无法触发 wrong_region。
    assert reflection.failure_class == "wrong_region"  # 新增代码+ReflectionLearningTest：确认失败分类；如果没有这行代码，修复策略可能错误。
    assert reflection.repair_strategy == "reobserve_and_recompile_batch"  # 新增代码+ReflectionLearningTest：确认修复策略要求重新观察和编译；如果没有这行代码，下一轮可能继续点错区域。


def test_reflection_classifies_target_drift(tmp_path) -> None:  # 新增代码+ReflectionLearningTest：函数段开始，验证目标漂移分类；如果没有这个测试，窗口错绑可能被盲目重试。
    layer = ReflectionLearningLayer(patterns_path=tmp_path / "patterns.jsonl")  # 新增代码+ReflectionLearningTest：创建独立学习层；如果没有这行代码，测试路径不隔离。
    reflection = layer.reflect_stage_failure("stage-a", _result("target_identity_failed"), {"wrong_target_visible": True}, _action())  # 新增代码+ReflectionLearningTest：输入目标身份失败证据；如果没有这行代码，无法触发 target_drift。
    assert reflection.failure_class == "target_drift"  # 新增代码+ReflectionLearningTest：确认目标漂移分类；如果没有这行代码，错误窗口风险无法被定位。
    assert reflection.replan_required is True  # 新增代码+ReflectionLearningTest：确认目标漂移需要重新规划或重新获取目标；如果没有这行代码，循环可能继续写错窗口。


def test_reflection_classifies_batch_too_small(tmp_path) -> None:  # 新增代码+ReflectionLearningTest：函数段开始，验证批规模过小分类；如果没有这个测试，复杂绘图只画一条线的问题会复发。
    layer = ReflectionLearningLayer(patterns_path=tmp_path / "patterns.jsonl")  # 新增代码+ReflectionLearningTest：创建独立学习层；如果没有这行代码，学习记录会污染真实文件。
    reflection = layer.reflect_stage_failure("stage-a", _result("drawing_visual_evidence_incomplete", low_level_event_count=1, primitive_action_count=1), {}, _action(low_level_event_count=1, primitive_action_count=1))  # 新增代码+ReflectionLearningTest：输入低事件低 primitive 证据；如果没有这行代码，无法触发 batch_too_small。
    assert reflection.failure_class == "batch_too_small"  # 新增代码+ReflectionLearningTest：确认批太小分类；如果没有这行代码，修复策略不会扩大动作批。
    assert reflection.repair_strategy == "compile_larger_stage_batch"  # 新增代码+ReflectionLearningTest：确认修复策略是扩大批；如果没有这行代码，复杂任务仍会太慢太碎。


def test_reflection_classifies_save_dialog_unhandled(tmp_path) -> None:  # 新增代码+ReflectionLearningTest：函数段开始，验证保存对话框失败分类；如果没有这个测试，保存失败可能被误当内容缺失。
    layer = ReflectionLearningLayer(patterns_path=tmp_path / "patterns.jsonl")  # 新增代码+ReflectionLearningTest：创建独立学习层；如果没有这行代码，测试无法安全落盘。
    reflection = layer.reflect_stage_failure("stage-a", _result("resource_commit_not_verified"), {"save_dialog_state": {"visible": True}}, _action())  # 新增代码+ReflectionLearningTest：输入保存未完成证据；如果没有这行代码，无法触发 save_dialog_unhandled。
    assert reflection.failure_class == "save_dialog_unhandled"  # 新增代码+ReflectionLearningTest：确认保存对话框分类；如果没有这行代码，保存弹窗不会被正确处理。
    assert reflection.repair_strategy == "handle_save_dialog_or_request_user"  # 新增代码+ReflectionLearningTest：确认修复策略处理保存弹窗或请求用户；如果没有这行代码，保存阶段可能无限重试 Ctrl+S。


def test_reflection_classifies_missing_content(tmp_path) -> None:  # 新增代码+ReflectionLearningTest：函数段开始，验证内容缺失分类；如果没有这个测试，文本/绘图未完成可能被错误归为能力未知。
    layer = ReflectionLearningLayer(patterns_path=tmp_path / "patterns.jsonl")  # 新增代码+ReflectionLearningTest：创建独立学习层；如果没有这行代码，测试无法隔离状态。
    reflection = layer.reflect_stage_failure("stage-a", _result("text_not_visible_after_batch", low_level_event_count=8, primitive_action_count=4), {"visible_text_summary": ""}, _action(low_level_event_count=8, primitive_action_count=4))  # 新增代码+ReflectionLearningTest：输入文本未出现但动作规模充足的证据；如果没有这行代码，无法触发 missing_content。
    assert reflection.failure_class == "missing_content"  # 新增代码+ReflectionLearningTest：确认内容缺失分类；如果没有这行代码，修复策略不会重新编译内容批。
    assert reflection.repair_strategy == "reobserve_and_recompile_content_batch"  # 新增代码+ReflectionLearningTest：确认修复策略围绕内容重新观察和编译；如果没有这行代码，下一轮可能重复同样失败。


def test_repeated_failure_patterns_are_sanitized_before_storage(tmp_path) -> None:  # 新增代码+ReflectionLearningTest：函数段开始，验证重复失败才脱敏落盘；如果没有这个测试，单次失败或敏感路径可能污染学习库。
    patterns_path = tmp_path / "patterns.jsonl"  # 新增代码+ReflectionLearningTest：准备临时学习文件；如果没有这行代码，测试会写入真实 runtime_learning。
    layer = ReflectionLearningLayer(patterns_path=patterns_path, repeated_threshold=2)  # 新增代码+ReflectionLearningTest：创建两次重复才记录的学习层；如果没有这行代码，阈值行为无法验证。
    sensitive_stage = "C:\\Users\\joyzq\\Desktop\\secret.txt"  # 新增代码+ReflectionLearningTest：构造像本机私有路径的 stage_id；如果没有这行代码，脱敏路径无法被测试。
    layer.reflect_stage_failure(sensitive_stage, _result("text_not_visible_after_batch", low_level_event_count=8, primitive_action_count=4), {"prompt": "secret prompt", "clipboard": "secret clipboard"}, _action(low_level_event_count=8, primitive_action_count=4))  # 新增代码+ReflectionLearningTest：第一次失败不应落盘；如果没有这行代码，无法验证重复阈值。
    assert patterns_path.exists() is False  # 新增代码+ReflectionLearningTest：确认单次失败不写文件；如果没有这行代码，偶发失败污染不会被发现。
    layer.reflect_stage_failure(sensitive_stage, _result("text_not_visible_after_batch", low_level_event_count=8, primitive_action_count=4), {"prompt": "secret prompt", "clipboard": "secret clipboard"}, _action(low_level_event_count=8, primitive_action_count=4))  # 新增代码+ReflectionLearningTest：第二次同类失败应落盘；如果没有这行代码，重复学习无法验证。
    rows = [json.loads(line) for line in patterns_path.read_text(encoding="utf-8").splitlines() if line.strip()]  # 新增代码+ReflectionLearningTest：读取 JSONL 行；如果没有这行代码，无法检查落盘内容。
    serialized = json.dumps(rows, ensure_ascii=False)  # 新增代码+ReflectionLearningTest：把学习记录转成文本便于敏感词断言；如果没有这行代码，检查敏感泄露不方便。
    assert len(rows) == 1  # 新增代码+ReflectionLearningTest：确认只写入第二次重复失败；如果没有这行代码，学习阈值可能失效。
    assert rows[0]["failure_class"] == "missing_content"  # 新增代码+ReflectionLearningTest：确认写入的是通用失败分类；如果没有这行代码，学习记录可能不可复用。
    assert "secret prompt" not in serialized and "secret clipboard" not in serialized  # 新增代码+ReflectionLearningTest：确认 prompt 和剪贴板未落盘；如果没有这行代码，敏感数据泄露无法被发现。
    assert "C:\\Users\\joyzq\\Desktop\\secret.txt" not in serialized  # 新增代码+ReflectionLearningTest：确认本机路径未落盘；如果没有这行代码，用户私有路径可能泄露到经验库。
