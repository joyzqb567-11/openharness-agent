import io  # 新增代码+URG6FinalMatrix：导入内存输出缓冲区；如果没有这一行，测试无法捕获 CLI 最终 token。
import unittest  # 新增代码+URG6FinalMatrix：导入标准测试框架；如果没有这一行，本测试不会被 unittest 发现。
from contextlib import redirect_stdout  # 新增代码+URG6FinalMatrix：导入 stdout 重定向工具；如果没有这一行，main 打印内容无法断言。
from learning_agent.computer_use.universal_final_maturity_matrix import UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER, main, phase121_universal_final_maturity_cli_line, run_phase121_universal_final_maturity_matrix  # 新增代码+URG6FinalMatrix：导入 URG-6 预期公开 API；如果没有这一行，红灯无法证明最终矩阵缺失。


class UniversalRealGuiComputerUseFinalMatrixTests(unittest.TestCase):  # 新增代码+URG6FinalMatrix：测试类段开始，集中验证跨应用最终成熟度矩阵；如果没有这个类，URG-6 没有自动护栏。
    def _required_tokens(self) -> list[str]:  # 新增代码+URG6FinalMatrix：函数段开始，集中列出蓝图要求的最终 token；如果没有这段函数，多处断言容易漂移。
        return ["UNIVERSAL_REAL_GUI_COMPUTER_USE_READY", "single_universal_real_gui_loop=true", "per_app_controller_required=false", "hardcoded_app_whitelist_required=false", "ordinary_apps_controlled_by_generic_runtime=true", "representative_apps_are_acceptance_only=true", "real_window_observation=true", "real_uia_or_vision_targeting=true", "real_sendinput_dispatch=true", "target_identity_rechecked_before_each_action=true", "observe_plan_act_verify_loop=true", "paint_pikachu_real_acceptance=true", "notepad_real_acceptance=true", "calculator_real_acceptance=true", "browser_real_acceptance=true", "script_artifact_route_blocked=true", "real_desktop_execution_mature=true", "uncontrolled_high_risk_actions_allowed=false"]  # 新增代码+URG6FinalMatrix：返回固定 token 列表；如果没有这一行，最终矩阵可能漏字段仍过测。
    # 新增代码+URG6FinalMatrix：函数段结束，_required_tokens 到此结束；如果没有这个边界说明，初学者不容易看出 token 范围。

    def test_final_matrix_reports_all_blueprint_tokens(self) -> None:  # 新增代码+URG6FinalMatrix：函数段开始，验证结构化矩阵和 CLI 行；如果没有这段测试，最终输出可能只覆盖部分应用。
        report = run_phase121_universal_final_maturity_matrix()  # 新增代码+URG6FinalMatrix：运行 URG-6 最终矩阵；如果没有这一行，断言没有事实来源。
        cli_line = phase121_universal_final_maturity_cli_line(report)  # 新增代码+URG6FinalMatrix：把报告转成最终固定行；如果没有这一行，真实终端场景无法复用。
        self.assertTrue(report["passed"])  # 新增代码+URG6FinalMatrix：断言整体通过；如果没有这一行，局部字段成功可能掩盖整体失败。
        self.assertTrue(report["paint_pikachu_real_acceptance"])  # 新增代码+URG6FinalMatrix：断言 Paint/Pikachu 代表验收进入矩阵；如果没有这一行，用户核心场景可能漏掉。
        self.assertTrue(report["notepad_real_acceptance"])  # 新增代码+URG6FinalMatrix：断言 Notepad 代表验收进入矩阵；如果没有这一行，文本输入类应用可能漏掉。
        self.assertTrue(report["calculator_real_acceptance"])  # 新增代码+URG6FinalMatrix：断言 Calculator 代表验收进入矩阵；如果没有这一行，按键/结果观察类应用可能漏掉。
        self.assertTrue(report["browser_real_acceptance"])  # 新增代码+URG6FinalMatrix：断言 Browser 代表验收进入矩阵；如果没有这一行，普通第三方/浏览器点击观察类应用可能漏掉。
        for token in self._required_tokens():  # 新增代码+URG6FinalMatrix：遍历所有必需 token；如果没有这一行，只会检查少量字段。
            self.assertIn(token, cli_line)  # 新增代码+URG6FinalMatrix：断言 token 出现在最终行；如果没有这一行，字段漏输出不会被发现。
    # 新增代码+URG6FinalMatrix：函数段结束，test_final_matrix_reports_all_blueprint_tokens 到此结束；如果没有这个边界说明，初学者不容易看出矩阵测试范围。

    def test_main_prints_final_marker(self) -> None:  # 新增代码+URG6FinalMatrix：函数段开始，验证命令行入口输出最终 marker；如果没有这段测试，可见终端场景可能没有锚点。
        buffer = io.StringIO()  # 新增代码+URG6FinalMatrix：创建输出缓冲；如果没有这一行，main 输出无法读取。
        with redirect_stdout(buffer):  # 新增代码+URG6FinalMatrix：捕获标准输出；如果没有这一行，断言只能看退出码。
            exit_code = main([])  # 新增代码+URG6FinalMatrix：运行 URG-6 命令行入口；如果没有这一行，真实终端入口没有自动化覆盖。
        output = buffer.getvalue()  # 新增代码+URG6FinalMatrix：读取输出文本；如果没有这一行，后续 token 断言没有对象。
        self.assertEqual(0, exit_code)  # 新增代码+URG6FinalMatrix：断言入口成功退出；如果没有这一行，失败输出可能被误判。
        self.assertIn(UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER, output)  # 新增代码+URG6FinalMatrix：断言最终 marker 出现；如果没有这一行，用户看不到终局标识。
        self.assertIn("real_desktop_execution_mature=true", output)  # 新增代码+URG6FinalMatrix：断言成熟字段出现；如果没有这一行，最终状态不可见。
    # 新增代码+URG6FinalMatrix：函数段结束，test_main_prints_final_marker 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 测试范围。
# 新增代码+URG6FinalMatrix：测试类段结束，UniversalRealGuiComputerUseFinalMatrixTests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+URG6FinalMatrix：文件入口段开始，允许直接运行本测试；如果没有这一行，初学者需要记完整命令。
    unittest.main()  # 新增代码+URG6FinalMatrix：启动 unittest；如果没有这一行，直接运行文件不会执行测试。
# 新增代码+URG6FinalMatrix：文件入口段结束，本测试文件到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
