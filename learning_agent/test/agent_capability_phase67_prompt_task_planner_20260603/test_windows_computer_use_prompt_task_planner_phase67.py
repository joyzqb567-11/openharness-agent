import json  # 新增代码+Phase67PromptTaskPlanner: 导入 JSON 用来校验真实终端验收场景；如果没有这行代码，场景格式错误只能等 controller 运行时才暴露。
import unittest  # 新增代码+Phase67PromptTaskPlanner: 导入 unittest 承载 Phase67 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase67PromptTaskPlanner: 导入 Path 处理 Windows 场景文件路径；如果没有这行代码，路径拼接容易在不同工作目录下失败。

from learning_agent.computer_use.prompt_task_planner import PHASE67_PROMPT_TASK_PLANNER_MARKER, PHASE67_PROMPT_TASK_PLANNER_OK_TOKEN, WindowsPromptTaskPlanner, classify_risk, phase67_cli_line, run_phase67_prompt_task_planner_contract  # 新增代码+Phase67PromptTaskPlanner: 导入 Phase67 prompt 任务规划 API；如果没有这行代码，红灯测试无法证明生产模块尚未实现。


class WindowsComputerUsePromptTaskPlannerPhase67Tests(unittest.TestCase):  # 新增代码+Phase67PromptTaskPlanner: 类段开始，集中验证 Phase67 从 prompt 到通用任务步骤的规划能力；如果没有这个类，Phase67 没有自动化门禁。
    def test_phase67_contract_reports_required_planner_capabilities(self) -> None:  # 新增代码+Phase67PromptTaskPlanner: 函数段开始，验证 Phase67 合同必须包含步骤、预期结果、风险和检查点；如果没有这个测试，后续执行器可能拿到空规划。
        report = run_phase67_prompt_task_planner_contract()  # 新增代码+Phase67PromptTaskPlanner: 运行 Phase67 合同自检；如果没有这行代码，测试没有真实报告来源。
        self.assertEqual(report["marker"], PHASE67_PROMPT_TASK_PLANNER_MARKER)  # 新增代码+Phase67PromptTaskPlanner: 断言 ready marker 稳定；如果没有这行代码，真实终端验收可能匹配不到 Phase67 输出。
        self.assertEqual(report["ok_token"], PHASE67_PROMPT_TASK_PLANNER_OK_TOKEN)  # 新增代码+Phase67PromptTaskPlanner: 断言 OK token 稳定；如果没有这行代码，用户无法一眼判断本阶段是否通过。
        self.assertTrue(report["prompt_task_plan"])  # 新增代码+Phase67PromptTaskPlanner: 断言 prompt 能生成任务计划；如果没有这行代码，规划器可能只输出 token 没有真实结构。
        self.assertTrue(report["expected_result_per_step"])  # 新增代码+Phase67PromptTaskPlanner: 断言每一步都有预期结果；如果没有这行代码，闭环执行器无法判断动作后是否成功。
        self.assertTrue(report["risk_level_per_step"])  # 新增代码+Phase67PromptTaskPlanner: 断言每一步都有风险级别；如果没有这行代码，高风险动作可能混入普通流程。
        self.assertTrue(report["checkpoint_per_step"])  # 新增代码+Phase67PromptTaskPlanner: 断言每一步都有检查点；如果没有这行代码，失败恢复没有观测锚点。
        self.assertTrue(report["paint_pikachu_prompt"])  # 新增代码+Phase67PromptTaskPlanner: 断言画图皮卡丘 prompt 被识别；如果没有这行代码，用户新增代表性场景可能被漏掉。
        self.assertTrue(report["high_risk_confirmation"])  # 新增代码+Phase67PromptTaskPlanner: 断言高风险 prompt 会要求确认；如果没有这行代码，支付、密码、管理员等动作可能被直接计划。
        self.assertTrue(report["deterministic_rule_planner"])  # 新增代码+Phase67PromptTaskPlanner: 断言单测合同使用确定性规则规划器；如果没有这行代码，测试可能误调用 LLM 造成不稳定。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase67PromptTaskPlanner: 断言 Phase67 不扩展真实桌面动作；如果没有这行代码，规划层可能被误用成执行层。
    # 新增代码+Phase67PromptTaskPlanner: 函数段结束，test_phase67_contract_reports_required_planner_capabilities 到此结束；如果没有这个边界说明，初学者不容易看出合同测试范围。

    def test_phase67_paint_pikachu_prompt_produces_representative_generic_steps(self) -> None:  # 新增代码+Phase67PromptTaskPlanner: 函数段开始，验证 Paint 皮卡丘 prompt 会生成代表性绘图步骤；如果没有这个测试，Phase74 目标可能无法从 prompt 进入任务计划。
        plan = WindowsPromptTaskPlanner().plan("打开画图软件，画一个简化皮卡丘并保存")  # 新增代码+Phase67PromptTaskPlanner: 规划用户的真实 Paint 皮卡丘需求；如果没有这行代码，测试无法覆盖用户新增代表场景。
        operations = {str(step.get("operation", "")) for step in plan["steps"]}  # 新增代码+Phase67PromptTaskPlanner: 收集步骤操作名便于断言；如果没有这行代码，检查步骤需要重复遍历。
        self.assertEqual(plan["app"], "mspaint")  # 新增代码+Phase67PromptTaskPlanner: 断言目标应用识别为画图；如果没有这行代码，规划器可能把绘图 prompt 当通用文本任务。
        self.assertTrue(plan["prompt_task_plan"])  # 新增代码+Phase67PromptTaskPlanner: 断言输出是任务计划；如果没有这行代码，plan 可能只是普通分类结果。
        self.assertTrue(plan["representative_scenario"])  # 新增代码+Phase67PromptTaskPlanner: 断言这是代表性 E2E 场景；如果没有这行代码，Phase74 矩阵无法识别 Paint Pikachu。
        self.assertFalse(plan["per_app_script"])  # 新增代码+Phase67PromptTaskPlanner: 断言不是每个应用硬编码脚本；如果没有这行代码，设计会偏离通用拟人操作目标。
        self.assertIn("launch_app", operations)  # 新增代码+Phase67PromptTaskPlanner: 断言计划包含启动应用意图；如果没有这行代码，后续无法打开 Paint。
        self.assertIn("identify_canvas", operations)  # 新增代码+Phase67PromptTaskPlanner: 断言计划包含识别画布意图；如果没有这行代码，后续绘图可能变成盲坐标点击。
        self.assertIn("select_color", operations)  # 新增代码+Phase67PromptTaskPlanner: 断言计划包含选择颜色意图；如果没有这行代码，皮卡丘黄色/红色/黑色元素无法计划。
        self.assertIn("draw_body", operations)  # 新增代码+Phase67PromptTaskPlanner: 断言计划包含绘制主体意图；如果没有这行代码，皮卡丘图形缺少核心主体。
        self.assertIn("draw_tail", operations)  # 新增代码+Phase67PromptTaskPlanner: 断言计划包含绘制闪电尾巴意图；如果没有这行代码，皮卡丘代表性元素会漏掉。
        self.assertIn("save_artifact", operations)  # 新增代码+Phase67PromptTaskPlanner: 断言计划包含保存证据意图；如果没有这行代码，E2E 无法留下可验收结果。
        self.assertTrue(all("expected_result" in step for step in plan["steps"]))  # 新增代码+Phase67PromptTaskPlanner: 断言每一步都有预期结果；如果没有这行代码，执行器无法做后置校验。
        self.assertTrue(all("risk_level" in step for step in plan["steps"]))  # 新增代码+Phase67PromptTaskPlanner: 断言每一步都有风险级别；如果没有这行代码，安全边界无法逐步评估。
        self.assertTrue(all("checkpoint" in step for step in plan["steps"]))  # 新增代码+Phase67PromptTaskPlanner: 断言每一步都有检查点；如果没有这行代码，恢复流程没有观察节点。
    # 新增代码+Phase67PromptTaskPlanner: 函数段结束，test_phase67_paint_pikachu_prompt_produces_representative_generic_steps 到此结束；如果没有这个边界说明，初学者不容易看出 Paint 测试范围。

    def test_phase67_notepad_prompt_produces_text_workflow_steps(self) -> None:  # 新增代码+Phase67PromptTaskPlanner: 函数段开始，验证记事本文本 prompt 会生成通用文本工作流步骤；如果没有这个测试，planner 可能只覆盖 Paint。
        plan = WindowsPromptTaskPlanner().plan("打开记事本，输入 hello phase67，然后保存")  # 新增代码+Phase67PromptTaskPlanner: 规划一个普通文本编辑任务；如果没有这行代码，通用办公类应用路径没有覆盖。
        operations = [str(step.get("operation", "")) for step in plan["steps"]]  # 新增代码+Phase67PromptTaskPlanner: 收集有序操作名；如果没有这行代码，无法判断保存和校验步骤是否存在。
        self.assertEqual(plan["app"], "notepad")  # 新增代码+Phase67PromptTaskPlanner: 断言目标应用识别为记事本；如果没有这行代码，文本 prompt 可能被错分。
        self.assertFalse(plan["representative_scenario"])  # 新增代码+Phase67PromptTaskPlanner: 断言普通记事本任务不是 Paint 代表场景；如果没有这行代码，矩阵统计会混乱。
        self.assertFalse(plan["per_app_script"])  # 新增代码+Phase67PromptTaskPlanner: 断言仍然不是应用专用脚本；如果没有这行代码，普通文本任务可能退回硬编码操作。
        self.assertIn("launch_app", operations)  # 新增代码+Phase67PromptTaskPlanner: 断言计划包含启动应用；如果没有这行代码，后续执行无法打开记事本。
        self.assertIn("focus_text_area", operations)  # 新增代码+Phase67PromptTaskPlanner: 断言计划包含定位文本区；如果没有这行代码，输入可能盲打到错误位置。
        self.assertIn("type_text", operations)  # 新增代码+Phase67PromptTaskPlanner: 断言计划包含输入文本；如果没有这行代码，文本任务没有核心动作。
        self.assertIn("save_document", operations)  # 新增代码+Phase67PromptTaskPlanner: 断言计划包含保存文档；如果没有这行代码，用户保存需求会被漏掉。
        self.assertIn("verify_result", operations)  # 新增代码+Phase67PromptTaskPlanner: 断言计划包含结果校验；如果没有这行代码，闭环执行器无法确认保存成功。
    # 新增代码+Phase67PromptTaskPlanner: 函数段结束，test_phase67_notepad_prompt_produces_text_workflow_steps 到此结束；如果没有这个边界说明，初学者不容易看出记事本测试范围。

    def test_phase67_high_risk_prompt_requires_confirmation_before_action(self) -> None:  # 新增代码+Phase67PromptTaskPlanner: 函数段开始，验证高风险 prompt 会进入确认门禁；如果没有这个测试，密码、支付、管理员等场景可能被直接计划执行。
        risk = classify_risk("用管理员权限打开支付页面并输入密码")  # 新增代码+Phase67PromptTaskPlanner: 对高风险 prompt 做风险分类；如果没有这行代码，风险分类函数没有直接测试。
        plan = WindowsPromptTaskPlanner().plan("用管理员权限打开支付页面并输入密码")  # 新增代码+Phase67PromptTaskPlanner: 规划高风险 prompt；如果没有这行代码，高风险计划边界没有覆盖。
        self.assertEqual(risk["risk_level"], "high")  # 新增代码+Phase67PromptTaskPlanner: 断言风险级别为 high；如果没有这行代码，高风险分类可能失效。
        self.assertTrue(risk["requires_confirmation"])  # 新增代码+Phase67PromptTaskPlanner: 断言高风险需要确认；如果没有这行代码，危险动作可能绕过用户确认。
        self.assertTrue(plan["requires_confirmation"])  # 新增代码+Phase67PromptTaskPlanner: 断言计划层也要求确认；如果没有这行代码，分类和计划可能脱节。
        self.assertTrue(plan["high_risk_confirmation"])  # 新增代码+Phase67PromptTaskPlanner: 断言高风险确认 token 成立；如果没有这行代码，真实终端验收无法检查安全边界。
        self.assertEqual(plan["steps"][0]["operation"], "request_user_confirmation")  # 新增代码+Phase67PromptTaskPlanner: 断言第一步是请求确认；如果没有这行代码，危险动作可能排在确认前。
        self.assertTrue(all(step["risk_level"] == "high" for step in plan["steps"]))  # 新增代码+Phase67PromptTaskPlanner: 断言高风险计划步骤都标 high；如果没有这行代码，后续执行器可能错把某步当普通动作。
        self.assertFalse(plan["actions_expanded"])  # 新增代码+Phase67PromptTaskPlanner: 断言 planner 不执行动作；如果没有这行代码，规划器可能被误用成执行器。
    # 新增代码+Phase67PromptTaskPlanner: 函数段结束，test_phase67_high_risk_prompt_requires_confirmation_before_action 到此结束；如果没有这个边界说明，初学者不容易看出高风险测试范围。

    def test_phase67_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase67PromptTaskPlanner: 函数段开始，验证 CLI 行和真实终端场景 token 稳定；如果没有这个测试，controller 场景可能和模块输出脱节。
        report = run_phase67_prompt_task_planner_contract()  # 新增代码+Phase67PromptTaskPlanner: 运行合同报告作为 CLI 输出来源；如果没有这行代码，token 测试没有结构化来源。
        cli_line = phase67_cli_line(report)  # 新增代码+Phase67PromptTaskPlanner: 生成稳定 CLI token 行；如果没有这行代码，真实终端最终回答需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase67_prompt_task_planner.json")  # 新增代码+Phase67PromptTaskPlanner: 定位 Phase67 真实终端验收场景；如果没有这行代码，场景缺失不会被测试发现。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase67PromptTaskPlanner: 读取场景文本；如果没有这行代码，场景 token 漏配无法被发现。
        json.loads(scenario_text)  # 新增代码+Phase67PromptTaskPlanner: 校验场景是合法 JSON；如果没有这行代码，controller 运行时才会暴露格式错误。
        expected_tokens = {PHASE67_PROMPT_TASK_PLANNER_MARKER, PHASE67_PROMPT_TASK_PLANNER_OK_TOKEN, "prompt_task_plan=true", "expected_result_per_step=true", "risk_level_per_step=true", "checkpoint_per_step=true", "paint_pikachu_prompt=true", "high_risk_confirmation=true", "actions_expanded=false"}  # 新增代码+Phase67PromptTaskPlanner: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase67PromptTaskPlanner: 遍历每个关键 token；如果没有这行代码，重复断言容易遗漏。
            self.assertIn(token, cli_line)  # 新增代码+Phase67PromptTaskPlanner: 断言 CLI 输出包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase67PromptTaskPlanner: 断言真实终端场景也包含 token；如果没有这行代码，自动测试和真实验收可能不一致。
    # 新增代码+Phase67PromptTaskPlanner: 函数段结束，test_phase67_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 token 测试范围。
# 新增代码+Phase67PromptTaskPlanner: 类段结束，WindowsComputerUsePromptTaskPlannerPhase67Tests 到此结束；如果没有这个边界说明，初学者不容易看出 Phase67 测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase67PromptTaskPlanner: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase67PromptTaskPlanner: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
