import io  # 新增代码+FullMaturityMatrix：导入内存文本缓冲区捕获 Phase115 输出；如果没有这一行，测试无法检查一键验收打印的最终 token。
import tempfile  # 新增代码+FullMaturityMatrix：导入临时目录隔离 `/computer` 命令状态；如果没有这一行，测试会污染用户真实 full 模式记录。
import unittest  # 新增代码+FullMaturityMatrix：导入 unittest 测试框架；如果没有这一行，标准测试命令无法发现本文件。
from contextlib import redirect_stdout  # 新增代码+FullMaturityMatrix：导入 stdout 重定向工具；如果没有这一行，测试会把大量验收输出直接刷到控制台。
from pathlib import Path  # 新增代码+FullMaturityMatrix：导入 Path 统一处理 Windows 路径；如果没有这一行，临时 workspace 传参会更脆弱。

from learning_agent.app.interactive import phase115_main, run_computer_terminal_command  # 新增代码+FullMaturityMatrix：导入真实 `/computer` 终端命令入口和最终验收入口；如果没有这一行，测试会绕开用户实际输入路径。
from learning_agent.computer_use.full_maturity_matrix import computer_use_full_maturity_cli_line, run_computer_use_full_maturity_matrix  # 新增代码+FullMaturityMatrix：导入最终成熟矩阵 API；如果没有这一行，红测会证明 Task7 模块尚未实现。


class WindowsComputerUseFullMaturityMatrixTests(unittest.TestCase):  # 新增代码+FullMaturityMatrix：类段开始，集中验收 `/computer use --full` 最终成熟矩阵；如果没有这个类，蓝图 Task7 没有自动化边界。
    def assert_contains_all(self, output: str, expected_parts: list[str]) -> None:  # 新增代码+FullMaturityMatrix：函数段开始，复用多 token 断言；如果没有这段函数，测试会重复大量 assertIn 噪声。
        for expected_part in expected_parts:  # 新增代码+FullMaturityMatrix：逐个检查输出片段；如果没有这一行，测试只会覆盖一个字段而漏掉成熟合同。
            self.assertIn(expected_part, output)  # 新增代码+FullMaturityMatrix：断言当前片段存在；如果没有这一行，缺字段也可能误通过。
    # 新增代码+FullMaturityMatrix：函数段结束，assert_contains_all 到此结束；如果没有这个边界说明，初学者不容易看出断言 helper 范围。

    def _required_tokens(self) -> list[str]:  # 新增代码+FullMaturityMatrix：函数段开始，集中列出最终矩阵必须输出的 token；如果没有这段函数，多个测试的成熟字段容易漂移。
        return ["COMPUTER_USE_FULL_MATURE_READY", "COMPUTER_USE_FULL_MATURE_OK", "product_contract=true", "generic_discovery=true", "generic_real_launch=true", "verified_window_actions=true", "cleanup_recovery=true", "high_risk_refused=true", "visible_terminal_acceptance=true", "hardcoded_app_whitelist_required=false", "per_app_patch_required=false", "uncontrolled_actions_expanded=false"]  # 新增代码+FullMaturityMatrix：返回蓝图要求的固定 token 列表；如果没有这一行，最终矩阵可能漏掉用户最关心的通用性字段。
    # 新增代码+FullMaturityMatrix：函数段结束，_required_tokens 到此结束；如果没有这个边界说明，初学者不容易看出最终 token 范围。

    def test_full_maturity_matrix_reports_required_fields(self) -> None:  # 新增代码+FullMaturityMatrix：函数段开始，验证结构化矩阵和 CLI 行都包含蓝图最终字段；如果没有这段测试，矩阵可能只输出部分阶段事实。
        report = run_computer_use_full_maturity_matrix()  # 新增代码+FullMaturityMatrix：运行最终成熟矩阵；如果没有这一行，断言没有结构化来源。
        cli_line = computer_use_full_maturity_cli_line(report)  # 新增代码+FullMaturityMatrix：把矩阵转成真实终端 token 行；如果没有这一行，场景验收不能复用稳定格式。
        self.assertTrue(report["passed"])  # 新增代码+FullMaturityMatrix：断言矩阵整体通过；如果没有这一行，单项字段为真但总体失败会被忽略。
        self.assertTrue(report["product_contract"])  # 新增代码+FullMaturityMatrix：断言产品契约已冻结；如果没有这一行，full 模式边界可能再次漂移。
        self.assertTrue(report["generic_discovery"])  # 新增代码+FullMaturityMatrix：断言通用发现已就绪；如果没有这一行，项目可能退回逐应用白名单。
        self.assertTrue(report["generic_real_launch"])  # 新增代码+FullMaturityMatrix：断言通用启动后端已就绪；如果没有这一行，launch 能力可能停在候选层。
        self.assertTrue(report["verified_window_actions"])  # 新增代码+FullMaturityMatrix：断言动作需要 verified window；如果没有这一行，动作可能落到漂移窗口。
        self.assertTrue(report["cleanup_recovery"])  # 新增代码+FullMaturityMatrix：断言清理恢复已就绪；如果没有这一行，真实启动后可能留下残留进程。
        self.assertTrue(report["high_risk_refused"])  # 新增代码+FullMaturityMatrix：断言高风险目标仍拒绝；如果没有这一行，full 可能被误解成无限权限。
        self.assertTrue(report["visible_terminal_acceptance"])  # 新增代码+FullMaturityMatrix：断言最终可见终端验收项进入矩阵；如果没有这一行，自动测试可能被误当最终交付。
        self.assertFalse(report["hardcoded_app_whitelist_required"])  # 新增代码+FullMaturityMatrix：断言不需要硬编码应用白名单；如果没有这一行，用户指出的设计问题会复发。
        self.assertFalse(report["per_app_patch_required"])  # 新增代码+FullMaturityMatrix：断言不需要逐应用补丁；如果没有这一行，项目会继续无止境堆 phase。
        self.assertFalse(report["uncontrolled_actions_expanded"])  # 新增代码+FullMaturityMatrix：断言没有扩张未受控动作面；如果没有这一行，安全边界可能被误放宽。
        self.assert_contains_all(cli_line, self._required_tokens())  # 新增代码+FullMaturityMatrix：断言 CLI 行包含所有最终 token；如果没有这一行，真实终端验收可能漏字段。
    # 新增代码+FullMaturityMatrix：函数段结束，test_full_maturity_matrix_reports_required_fields 到此结束；如果没有这个边界说明，初学者不容易看出矩阵字段测试范围。

    def test_computer_maturity_command_prints_matrix_without_desktop_touch(self) -> None:  # 新增代码+FullMaturityMatrix：函数段开始，验证 `/computer maturity` 只读输出最终矩阵；如果没有这段测试，用户无法直接查看蓝图收敛结果。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+FullMaturityMatrix：创建临时 workspace 隔离状态；如果没有这一行，maturity 命令会写入真实项目 memory。
            output = run_computer_terminal_command(Path(temp_dir), "/computer maturity")  # 新增代码+FullMaturityMatrix：执行用户会输入的最终成熟矩阵命令；如果没有这一行，测试无法覆盖真实交互入口。
        self.assert_contains_all(output, self._required_tokens())  # 新增代码+FullMaturityMatrix：断言 maturity 输出包含所有最终 token；如果没有这一行，命令可能漏掉关键成熟字段。
        self.assert_contains_all(output, ["real_desktop_touched=false", "low_level_event_count=0"])  # 新增代码+FullMaturityMatrix：断言矩阵查询不碰真实桌面；如果没有这一行，只读状态命令可能引入副作用。
    # 新增代码+FullMaturityMatrix：函数段结束，test_computer_maturity_command_prints_matrix_without_desktop_touch 到此结束；如果没有这个边界说明，初学者不容易看出 maturity 命令测试范围。

    def test_computer_use_full_request_includes_maturity_preview_without_activation(self) -> None:  # 新增代码+FullMaturityMatrix：函数段开始，验证 `/computer use --full` 请求同时展示成熟矩阵预览且不直接提权；如果没有这段测试，用户申请 full 时看不到最终边界。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+FullMaturityMatrix：创建临时 workspace 隔离 pending token；如果没有这一行，full 请求会污染真实状态。
            output = run_computer_terminal_command(Path(temp_dir), "/computer use --full")  # 新增代码+FullMaturityMatrix：执行真实 full 请求命令；如果没有这一行，测试无法覆盖用户入口。
        self.assert_contains_all(output, ["Computer Use Full Request", "strong_confirmation_required=true", "full_mode=false", "opened=false"])  # 新增代码+FullMaturityMatrix：断言 full 请求仍只是强确认预览；如果没有这一行，命令可能一步打开高风险模式。
        self.assert_contains_all(output, self._required_tokens())  # 新增代码+FullMaturityMatrix：断言 full 请求也展示最终成熟矩阵；如果没有这一行，用户看不到 full 成熟边界。
        self.assert_contains_all(output, ["real_desktop_touched=false", "low_level_event_count=0"])  # 新增代码+FullMaturityMatrix：断言请求阶段不触碰真实桌面；如果没有这一行，申请权限本身可能产生副作用。
    # 新增代码+FullMaturityMatrix：函数段结束，test_computer_use_full_request_includes_maturity_preview_without_activation 到此结束；如果没有这个边界说明，初学者不容易看出 full 请求矩阵测试范围。

    def test_phase115_main_runs_final_command_sequence(self) -> None:  # 新增代码+FullMaturityMatrix：函数段开始，验证最终可见终端入口会跑完整命令序列并打印成熟 token；如果没有这段测试，场景可能只看矩阵不跑 launch/refusal/stop。
        buffer = io.StringIO()  # 新增代码+FullMaturityMatrix：创建输出缓冲区；如果没有这一行，测试无法读取 phase115_main 打印内容。
        with redirect_stdout(buffer):  # 新增代码+FullMaturityMatrix：捕获 phase115_main 的打印输出；如果没有这一行，断言只能依赖退出码。
            exit_code = phase115_main([])  # 新增代码+FullMaturityMatrix：运行最终验收入口；如果没有这一行，测试无法覆盖 controller 将要调用的函数。
        output = buffer.getvalue()  # 新增代码+FullMaturityMatrix：读取捕获输出；如果没有这一行，后续 token 断言没有文本来源。
        self.assertEqual(0, exit_code)  # 新增代码+FullMaturityMatrix：断言最终入口返回成功；如果没有这一行，打印 token 但退出失败也会被忽略。
        self.assert_contains_all(output, self._required_tokens())  # 新增代码+FullMaturityMatrix：断言最终入口输出成熟矩阵 token；如果没有这一行，Task8 最终 answer 可能缺核心字段。
        self.assert_contains_all(output, ["Computer Use Full Maturity", "PHASE108_GENERIC_APP_DISCOVERY_READY", "high_risk_refused=true", "Computer Use Stop", "stopped=true", "real_desktop_touched=false", "low_level_event_count=0"])  # 新增代码+FullMaturityMatrix：断言完整命令序列覆盖 maturity、普通 app、高风险拒绝和 stop；如果没有这一行，最终验收可能只测了一个命令。
    # 新增代码+FullMaturityMatrix：函数段结束，test_phase115_main_runs_final_command_sequence 到此结束；如果没有这个边界说明，初学者不容易看出最终入口测试范围。
# 新增代码+FullMaturityMatrix：类段结束，WindowsComputerUseFullMaturityMatrixTests 到此结束；如果没有这个边界说明，初学者不容易看出 Task7 测试集合范围。


if __name__ == "__main__":  # 新增代码+FullMaturityMatrix：文件入口段开始，允许直接运行本测试文件；如果没有这一行，初学者必须记住完整 unittest 命令。
    unittest.main()  # 新增代码+FullMaturityMatrix：启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+FullMaturityMatrix：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出入口范围。
