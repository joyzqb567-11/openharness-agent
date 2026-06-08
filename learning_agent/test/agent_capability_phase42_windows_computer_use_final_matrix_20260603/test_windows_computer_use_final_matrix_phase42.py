import json  # 新增代码+Phase42WindowsFinalMatrix: 导入 JSON 工具读取最终矩阵文件；如果没有这行代码，测试无法验证矩阵结构。
import unittest  # 新增代码+Phase42WindowsFinalMatrix: 导入 unittest 测试框架；如果没有这行代码，本阶段测试不会被自动发现。
from pathlib import Path  # 新增代码+Phase42WindowsFinalMatrix: 导入 Path 处理矩阵和场景路径；如果没有这行代码，路径断言会变成脆弱字符串。

from learning_agent.computer_use.final_matrix import PHASE42_WINDOWS_COMPUTER_USE_FINAL_MARKER, PHASE42_WINDOWS_COMPUTER_USE_FINAL_OK_TOKEN, load_phase42_final_matrix, phase42_cli_line, run_phase42_final_matrix_contract  # 新增代码+Phase42WindowsFinalMatrix: 导入 Phase42 最终矩阵合同入口；如果没有这行代码，红灯无法证明最终矩阵模块尚未实现。


class WindowsComputerUseFinalMatrixPhase42Tests(unittest.TestCase):  # 新增代码+Phase42WindowsFinalMatrix: 定义 Phase42 最终矩阵测试集合；如果没有这个类，unittest 不会执行本阶段验收。
    def test_final_matrix_json_lists_phase35_to_phase41_contracts(self) -> None:  # 新增代码+Phase42WindowsFinalMatrix: 验证矩阵文件覆盖 Phase35-41；如果没有这个测试，最终验收可能漏掉前面某个阶段。
        matrix = load_phase42_final_matrix()  # 新增代码+Phase42WindowsFinalMatrix: 读取生产矩阵 JSON；如果没有这行代码，测试无法验证真实文件。
        phases = [entry["phase"] for entry in matrix["phases"]]  # 新增代码+Phase42WindowsFinalMatrix: 提取阶段编号；如果没有这行代码，断言目标不清楚。
        markers = {entry["marker"] for entry in matrix["phases"]}  # 新增代码+Phase42WindowsFinalMatrix: 提取所有阶段 marker；如果没有这行代码，无法确认各阶段验收锚点。
        checks = {entry["check"] for entry in matrix["safe_e2e_checks"]}  # 新增代码+Phase42WindowsFinalMatrix: 提取 E2E 检查项；如果没有这行代码，无法验证覆盖 observe/evidence 等关键能力。

        self.assertEqual(phases, [35, 36, 37, 38, 39, 40, 41])  # 新增代码+Phase42WindowsFinalMatrix: 断言矩阵按顺序覆盖 Phase35-41；如果没有这行代码，漏项或乱序会被忽略。
        self.assertEqual(matrix["acceptance_marker"], PHASE42_WINDOWS_COMPUTER_USE_FINAL_MARKER)  # 新增代码+Phase42WindowsFinalMatrix: 断言矩阵 marker 与模块常量一致；如果没有这行代码，场景可能等待错误标记。
        self.assertIn("PHASE41_WINDOWS_IMAGE_RESULTS_READY", markers)  # 新增代码+Phase42WindowsFinalMatrix: 断言 Phase41 图片结果进入矩阵；如果没有这行代码，artifact visibility 可能被漏掉。
        self.assertIn("observe", checks)  # 新增代码+Phase42WindowsFinalMatrix: 断言矩阵覆盖只读观察；如果没有这行代码，最终验收可能只测自检 token。
        self.assertIn("evidence", checks)  # 新增代码+Phase42WindowsFinalMatrix: 断言矩阵覆盖 evidence；如果没有这行代码，截图/metadata 可能不在最终门禁里。
        self.assertIn("approval", checks)  # 新增代码+Phase42WindowsFinalMatrix: 断言矩阵覆盖 approval；如果没有这行代码，权限模型可能不在最终门禁里。
        self.assertIn("gated_refusal", checks)  # 新增代码+Phase42WindowsFinalMatrix: 断言矩阵覆盖门禁拒绝；如果没有这行代码，高风险动作拒绝可能漏验。
        self.assertIn("safe_action", checks)  # 新增代码+Phase42WindowsFinalMatrix: 断言矩阵覆盖安全假执行动作；如果没有这行代码，SendInput 合同可能只看状态不看执行器。
        self.assertIn("abort_cleanup", checks)  # 新增代码+Phase42WindowsFinalMatrix: 断言矩阵覆盖 abort/cleanup；如果没有这行代码，运行时安全层可能不在最终门禁里。
        self.assertIn("artifact_visibility", checks)  # 新增代码+Phase42WindowsFinalMatrix: 断言矩阵覆盖 artifact 可见性；如果没有这行代码，Phase41 成果可能不在最终门禁里。
        self.assertFalse(any(entry["actions_expanded"] for entry in matrix["phases"]))  # 新增代码+Phase42WindowsFinalMatrix: 断言所有阶段都不扩大真实动作面；如果没有这行代码，安全边界可能被误改。

    def test_phase42_contract_runs_all_safe_phase_contracts(self) -> None:  # 新增代码+Phase42WindowsFinalMatrix: 验证 Phase42 合同串起所有安全自检；如果没有这个测试，最终矩阵可能只是静态 JSON。
        report = run_phase42_final_matrix_contract()  # 新增代码+Phase42WindowsFinalMatrix: 运行最终矩阵合同；如果没有这行代码，动态 E2E 条件不会被验证。
        report_text = json.dumps(report, ensure_ascii=False)  # 新增代码+Phase42WindowsFinalMatrix: 序列化报告用于泄露检查；如果没有这行代码，嵌套敏感值不好断言。

        self.assertEqual(report["phase_count"], 7)  # 新增代码+Phase42WindowsFinalMatrix: 断言动态合同覆盖七个阶段；如果没有这行代码，少跑阶段也可能过。
        self.assertTrue(report["matrix_ready"])  # 新增代码+Phase42WindowsFinalMatrix: 断言矩阵文件通过结构检查；如果没有这行代码，JSON 缺项不会失败。
        self.assertTrue(report["observe"])  # 新增代码+Phase42WindowsFinalMatrix: 断言只读观察链路成立；如果没有这行代码，最终 E2E 不覆盖 observe。
        self.assertTrue(report["evidence"])  # 新增代码+Phase42WindowsFinalMatrix: 断言 evidence 链路成立；如果没有这行代码，截图和 metadata 可能缺失。
        self.assertTrue(report["approval"])  # 新增代码+Phase42WindowsFinalMatrix: 断言 approval 合同成立；如果没有这行代码，会话授权模型可能失效。
        self.assertTrue(report["gated_refusal"])  # 新增代码+Phase42WindowsFinalMatrix: 断言门禁拒绝成立；如果没有这行代码，禁止目标或未授权动作可能漏拦。
        self.assertTrue(report["safe_action"])  # 新增代码+Phase42WindowsFinalMatrix: 断言安全假执行动作成立；如果没有这行代码，执行器合同可能只是空状态。
        self.assertTrue(report["abort_cleanup"])  # 新增代码+Phase42WindowsFinalMatrix: 断言 abort/cleanup 成立；如果没有这行代码，运行时清理安全层可能漏验。
        self.assertTrue(report["artifact_visibility"])  # 新增代码+Phase42WindowsFinalMatrix: 断言 artifact visibility 成立；如果没有这行代码，图片结果可能未进入 active_artifacts。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase42WindowsFinalMatrix: 断言最终矩阵没有扩大真实动作面；如果没有这行代码，最终验收可能误报成熟。
        self.assertNotIn("phase41-secret-must-not-leak", report_text)  # 新增代码+Phase42WindowsFinalMatrix: 断言最终报告不泄露 Phase41 敏感文本；如果没有这行代码，安全回归可能漏掉。

    def test_phase42_cli_line_and_visible_terminal_scenario_tokens(self) -> None:  # 新增代码+Phase42WindowsFinalMatrix: 验证 CLI 行和可见终端场景 token；如果没有这个测试，真实终端验收可能缺固定断言。
        report = run_phase42_final_matrix_contract()  # 新增代码+Phase42WindowsFinalMatrix: 运行最终矩阵合同；如果没有这行代码，CLI 行没有输入报告。
        cli_line = phase42_cli_line(report)  # 新增代码+Phase42WindowsFinalMatrix: 生成终端可复制的一行结果；如果没有这行代码，断言无法检查最终输出格式。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase42_windows_computer_use_final_matrix.json")  # 新增代码+Phase42WindowsFinalMatrix: 指向 Phase42 可见终端场景；如果没有这行代码，测试无法确认验收入口存在。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase42WindowsFinalMatrix: 读取场景文本；如果没有这行代码，无法检查 token 是否写入 prompt。

        self.assertIn(PHASE42_WINDOWS_COMPUTER_USE_FINAL_MARKER, cli_line)  # 新增代码+Phase42WindowsFinalMatrix: 断言 CLI 行包含最终 marker；如果没有这行代码，真实终端无法等待完成。
        self.assertIn(PHASE42_WINDOWS_COMPUTER_USE_FINAL_OK_TOKEN, cli_line)  # 新增代码+Phase42WindowsFinalMatrix: 断言 CLI 行包含 OK token；如果没有这行代码，最终回答无法证明自检成功。
        self.assertIn("phase_count=7", cli_line)  # 新增代码+Phase42WindowsFinalMatrix: 断言 CLI 行显示七阶段覆盖；如果没有这行代码，少跑阶段可能被忽略。
        self.assertIn("artifact_visibility=true", cli_line)  # 新增代码+Phase42WindowsFinalMatrix: 断言 CLI 行显示 artifact visibility；如果没有这行代码，Phase41 成果可能不在最终输出里。
        self.assertIn("actions_expanded=false", cli_line)  # 新增代码+Phase42WindowsFinalMatrix: 断言 CLI 行显示动作面未扩大；如果没有这行代码，安全边界不透明。
        self.assertIn(PHASE42_WINDOWS_COMPUTER_USE_FINAL_MARKER, scenario_text)  # 新增代码+Phase42WindowsFinalMatrix: 断言场景包含最终 marker；如果没有这行代码，controller 无法稳定验收。
        self.assertIn(PHASE42_WINDOWS_COMPUTER_USE_FINAL_OK_TOKEN, scenario_text)  # 新增代码+Phase42WindowsFinalMatrix: 断言场景包含 OK token；如果没有这行代码，debug log 检查缺成功锚点。
        self.assertIn("artifact_visibility=true", scenario_text)  # 新增代码+Phase42WindowsFinalMatrix: 断言场景检查 artifact visibility；如果没有这行代码，图片结果不会进入终端门禁。


if __name__ == "__main__":  # 新增代码+Phase42WindowsFinalMatrix: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase42WindowsFinalMatrix: 启动 unittest 主函数；如果没有这行代码，直接运行文件不会执行任何测试。
