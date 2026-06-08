import json  # 新增代码+Phase52WindowsProductionMatrix: 导入 JSON 工具读取场景文件；如果没有这行代码，测试无法检查验收 token。
import unittest  # 新增代码+Phase52WindowsProductionMatrix: 导入 unittest 框架；如果没有这行代码，自动化命令无法发现 Phase52 测试。
from pathlib import Path  # 新增代码+Phase52WindowsProductionMatrix: 导入 Path 定位场景文件；如果没有这行代码，路径拼接会变脆弱。

from learning_agent.computer_use.production_matrix import PHASE52_WINDOWS_PRODUCTION_MATRIX_MARKER, PHASE52_WINDOWS_PRODUCTION_MATRIX_OK_TOKEN, phase52_cli_line, run_phase52_production_matrix_contract  # 新增代码+Phase52WindowsProductionMatrix: 导入预期新增的生产总验收矩阵；如果没有这行代码，红灯会证明 Phase52 尚未实现。


class WindowsComputerUseProductionMatrixPhase52Tests(unittest.TestCase):  # 新增代码+Phase52WindowsProductionMatrix: 类段开始，验证 Phase43-51 总验收矩阵；如果没有这个类，unittest 不会组织 Phase52 验收。
    def test_phase52_contract_covers_phase43_to_phase51(self) -> None:  # 新增代码+Phase52WindowsProductionMatrix: 函数段开始，验证总矩阵覆盖九个阶段；如果没有这个测试，最终阶段可能漏掉某一层。
        report = run_phase52_production_matrix_contract()  # 新增代码+Phase52WindowsProductionMatrix: 运行 Phase52 总合同；如果没有这行代码，动态总验收不会执行。
        self.assertEqual(report["phase_count"], 9)  # 新增代码+Phase52WindowsProductionMatrix: 断言覆盖 Phase43-51 九阶段；如果没有这行代码，少跑阶段也可能误过。
        self.assertTrue(report["native_capability"])  # 新增代码+Phase52WindowsProductionMatrix: 断言 Phase43 原生能力矩阵通过；如果没有这行代码，诊断层可能漏验。
        self.assertTrue(report["native_host"])  # 新增代码+Phase52WindowsProductionMatrix: 断言 Phase44 native host 通过；如果没有这行代码，host 协议可能漏验。
        self.assertTrue(report["screenshot_runtime"])  # 新增代码+Phase52WindowsProductionMatrix: 断言 Phase45 截图运行时通过；如果没有这行代码，capture 层可能漏验。
        self.assertTrue(report["uia_tree"])  # 新增代码+Phase52WindowsProductionMatrix: 断言 Phase46 UIA tree 通过；如果没有这行代码，控件树观察可能漏验。
        self.assertTrue(report["sendinput_dispatcher"])  # 新增代码+Phase52WindowsProductionMatrix: 断言 Phase47 dispatcher 通过；如果没有这行代码，动作执行边界可能漏验。
        self.assertTrue(report["security_policy"])  # 新增代码+Phase52WindowsProductionMatrix: 断言 Phase48 安全策略通过；如果没有这行代码，高风险默认拒绝可能漏验。
        self.assertTrue(report["tool_surface"])  # 新增代码+Phase52WindowsProductionMatrix: 断言 Phase49 工具面通过；如果没有这行代码，兼容入口可能漏验。
        self.assertTrue(report["recovery_runtime"])  # 新增代码+Phase52WindowsProductionMatrix: 断言 Phase50 恢复 runtime 通过；如果没有这行代码，stale/cleanup/journal 可能漏验。
        self.assertTrue(report["status_ui"])  # 新增代码+Phase52WindowsProductionMatrix: 断言 Phase51 状态 UI 通过；如果没有这行代码，终端 UI 可能漏验。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase52WindowsProductionMatrix: 断言总矩阵仍未扩大真实动作面；如果没有这行代码，安全边界变化不会被发现。
        self.assertTrue(report["passed"])  # 新增代码+Phase52WindowsProductionMatrix: 断言总报告通过；如果没有这行代码，失败报告可能仍被后续流程误用。
    # 新增代码+Phase52WindowsProductionMatrix: 函数段结束，test_phase52_contract_covers_phase43_to_phase51 到此结束；如果没有这个边界说明，读者不容易看出总矩阵范围。

    def test_phase52_cli_line_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase52WindowsProductionMatrix: 函数段开始，验证 CLI 行和场景 token；如果没有这个测试，真实终端总验收可能缺少固定断言。
        report = run_phase52_production_matrix_contract()  # 新增代码+Phase52WindowsProductionMatrix: 运行总合同；如果没有这行代码，CLI 行没有真实报告来源。
        line = phase52_cli_line(report)  # 新增代码+Phase52WindowsProductionMatrix: 生成稳定单行 token；如果没有这行代码，场景验收需要解析复杂 JSON。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase52_windows_production_matrix.json")  # 新增代码+Phase52WindowsProductionMatrix: 定位 Phase52 场景文件；如果没有这行代码，测试无法确认验收入口存在。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase52WindowsProductionMatrix: 读取场景 JSON；如果没有这行代码，场景漏 token 不会被发现。
        expected_tokens = {PHASE52_WINDOWS_PRODUCTION_MATRIX_MARKER, PHASE52_WINDOWS_PRODUCTION_MATRIX_OK_TOKEN, "phase_count=9", "native_capability=true", "native_host=true", "screenshot_runtime=true", "uia_tree=true", "sendinput_dispatcher=true", "security_policy=true", "tool_surface=true", "recovery_runtime=true", "status_ui=true", "actions_expanded=false"}  # 新增代码+Phase52WindowsProductionMatrix: 列出最终必须稳定输出的 token；如果没有这行代码，总验收标准会散落。
        for token in expected_tokens:  # 新增代码+Phase52WindowsProductionMatrix: 遍历所有关键 token；如果没有这行代码，只能重复写多个断言。
            self.assertIn(token, line)  # 新增代码+Phase52WindowsProductionMatrix: 断言 CLI 行包含 token；如果没有这行代码，总验收输出漂移不会被发现。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase52WindowsProductionMatrix: 断言 debug log 检查包含 token；如果没有这行代码，真实验收可能漏查阶段。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase52WindowsProductionMatrix: 断言最终回答检查包含 token；如果没有这行代码，用户可见结果可能缺证据。
    # 新增代码+Phase52WindowsProductionMatrix: 函数段结束，test_phase52_cli_line_and_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，读者不容易看出 CLI/场景范围。


if __name__ == "__main__":  # 新增代码+Phase52WindowsProductionMatrix: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式单独验证 Phase52。
    unittest.main()  # 新增代码+Phase52WindowsProductionMatrix: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行断言。
