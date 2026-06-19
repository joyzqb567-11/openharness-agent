import json  # 新增代码+StageAcceptanceScenarioTest：导入 JSON 解析器；如果没有这行代码，场景合法性无法测试。
from pathlib import Path  # 新增代码+StageAcceptanceScenarioTest：导入 Path 处理场景路径；如果没有这行代码，测试路径拼接会脆弱。


SCENARIO_NAMES = (  # 新增代码+StageAcceptanceScenarioTest：列出本轮新增的三个通用场景；如果没有这段代码，测试可能漏掉某个场景。
    "computer_use_universal_text_task_stage_batch_visible_terminal.json",  # 新增代码+StageAcceptanceScenarioTest：文本任务场景文件名；如果没有这行代码，文本验收 schema 不会被覆盖。
    "computer_use_universal_drawing_task_stage_batch_visible_terminal.json",  # 新增代码+StageAcceptanceScenarioTest：绘图任务场景文件名；如果没有这行代码，绘图验收 schema 不会被覆盖。
    "computer_use_universal_multi_app_stage_batch_visible_terminal.json",  # 新增代码+StageAcceptanceScenarioTest：多应用任务场景文件名；如果没有这行代码，多目标验收 schema 不会被覆盖。
)  # 新增代码+StageAcceptanceScenarioTest：结束场景文件名元组；如果没有这行代码，Python 语法无法闭合。


def _scenario_root() -> Path:  # 新增代码+StageAcceptanceScenarioTest：函数段开始，定位 acceptance 场景目录；如果没有这段函数，多个测试会重复路径逻辑。
    return Path(__file__).resolve().parents[1] / "acceptance_controller" / "scenarios"  # 新增代码+StageAcceptanceScenarioTest：返回场景目录；如果没有这行代码，测试找不到 JSON 文件。
# 新增代码+StageAcceptanceScenarioTest：函数段结束，_scenario_root 到此结束；如果没有这个边界说明，初学者不容易看出路径来源。


def _load_scenario(name: str) -> dict:  # 新增代码+StageAcceptanceScenarioTest：函数段开始，读取一个场景 JSON；如果没有这段函数，测试会重复打开文件。
    return json.loads((_scenario_root() / name).read_text(encoding="utf-8"))  # 新增代码+StageAcceptanceScenarioTest：解析并返回场景字典；如果没有这行代码，JSON 错误不会在测试中暴露。
# 新增代码+StageAcceptanceScenarioTest：函数段结束，_load_scenario 到此结束；如果没有这个边界说明，初学者不容易看出读取范围。


def test_universal_stage_acceptance_scenarios_are_valid_json_and_full_mode() -> None:  # 新增代码+StageAcceptanceScenarioTest：函数段开始，验证 JSON 和 full mode 入口；如果没有这个测试，场景可能不能被 controller 读取。
    for name in SCENARIO_NAMES:  # 新增代码+StageAcceptanceScenarioTest：逐个检查新增场景；如果没有这行代码，只会验证一个样本。
        scenario = _load_scenario(name)  # 新增代码+StageAcceptanceScenarioTest：读取场景；如果没有这行代码，后续断言没有输入。
        assert scenario["visible_terminal_gate"] is True  # 新增代码+StageAcceptanceScenarioTest：确认是真实可见终端门禁；如果没有这行代码，场景可能退化成非可见自动化。
        assert scenario["prompt_lines"][0] == "/computer use --full"  # 新增代码+StageAcceptanceScenarioTest：确认第一步进入 full mode；如果没有这行代码，Computer Use 工具包可能没有加载。
        assert scenario["environment"]["LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS"] == "1"  # 新增代码+StageAcceptanceScenarioTest：确认仅场景环境自动同意权限；如果没有这行代码，手工反复输入 Y 的问题会复发。


def test_universal_stage_acceptance_scenarios_forbid_direct_artifact_shortcuts() -> None:  # 新增代码+StageAcceptanceScenarioTest：函数段开始，验证 prompt 禁止脚本成品绕路；如果没有这个测试，压力验收可能被文件直写假成功污染。
    for name in SCENARIO_NAMES:  # 新增代码+StageAcceptanceScenarioTest：逐个检查新增场景；如果没有这行代码，某个场景可能漏掉防作弊约束。
        scenario = _load_scenario(name)  # 新增代码+StageAcceptanceScenarioTest：读取场景；如果没有这行代码，后续无法检查 prompt。
        prompt_text = "\n".join(scenario["prompt_lines"])  # 新增代码+StageAcceptanceScenarioTest：合并多行 prompt；如果没有这行代码，防作弊文本可能跨行漏判。
        assert "不要使用 PowerShell" in prompt_text  # 新增代码+StageAcceptanceScenarioTest：确认明确禁止 PowerShell；如果没有这行代码，agent 可能用命令行伪造完成。
        assert "不要使用 PowerShell、Python" in prompt_text  # 新增代码+StageAcceptanceScenarioTest：确认明确禁止 Python；如果没有这行代码，图片/文件可能被脚本直接生成。
        assert "请使用 PowerShell" not in prompt_text  # 新增代码+StageAcceptanceScenarioTest：确认没有要求使用 PowerShell；如果没有这行代码，场景可能自相矛盾。
        assert "请使用 Python" not in prompt_text  # 新增代码+StageAcceptanceScenarioTest：确认没有要求使用 Python；如果没有这行代码，场景可能鼓励直接脚本生成。


def test_universal_stage_acceptance_scenarios_check_stage_evidence_markers() -> None:  # 新增代码+StageAcceptanceScenarioTest：函数段开始，验证成功标记依赖 stage evidence；如果没有这个测试，最终 prose 可能伪造成功。
    for name in SCENARIO_NAMES:  # 新增代码+StageAcceptanceScenarioTest：逐个检查新增场景；如果没有这行代码，某个场景可能只检查普通文字。
        scenario = _load_scenario(name)  # 新增代码+StageAcceptanceScenarioTest：读取场景；如果没有这行代码，后续无法检查 marker。
        answer_markers = "\n".join(scenario.get("event_answer_contains", []))  # 新增代码+StageAcceptanceScenarioTest：合并最终回答 marker；如果没有这行代码，断言要重复遍历。
        payload_markers = "\n".join(scenario.get("event_payload_contains", []))  # 新增代码+StageAcceptanceScenarioTest：合并 payload marker；如果没有这行代码，无法确认 stage 字段进入事件。
        assert "desktop_task_completed=true" in answer_markers  # 新增代码+StageAcceptanceScenarioTest：确认最终答案检查完成字段；如果没有这行代码，场景可能只看 OK 字符串。
        assert "batch_execution_used=true" in answer_markers  # 新增代码+StageAcceptanceScenarioTest：确认最终答案检查批执行；如果没有这行代码，primitive 循环可能伪装通过。
        assert "universal_stage_task_loop_used" in payload_markers  # 新增代码+StageAcceptanceScenarioTest：确认事件 payload 检查阶段循环；如果没有这行代码，新 runtime 未接入也可能通过。
        assert "desktop_task_plan_created" in payload_markers  # 新增代码+StageAcceptanceScenarioTest：确认事件 payload 检查阶段计划；如果没有这行代码，模型即兴动作可能被误判为阶段规划。
