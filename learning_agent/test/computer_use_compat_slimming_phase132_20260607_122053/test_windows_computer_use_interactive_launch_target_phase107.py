import tempfile  # 新增代码+Phase107InteractiveLaunchTarget：导入临时目录隔离 `/computer` 命令状态；如果没有这行代码，测试会污染真实 memory。
import unittest  # 新增代码+Phase107InteractiveLaunchTarget：导入 unittest 框架；如果没有这行代码，测试发现器无法执行本文件。
from pathlib import Path  # 新增代码+Phase107InteractiveLaunchTarget：导入 Path 处理 Windows 路径；如果没有这行代码，临时 workspace 路径拼接容易出错。

from learning_agent.app.interactive import PHASE106_INTERACTIVE_FULL_LAUNCH_OK_TOKEN, run_computer_terminal_command  # 新增代码+Phase107InteractiveLaunchTarget：导入真实 `/computer` 命令入口；如果没有这行代码，测试会绕过用户交互路径。
from learning_agent.computer_use.windows_launch_resolver import PHASE107_INTERACTIVE_LAUNCH_TARGET_MARKER, PHASE107_INTERACTIVE_LAUNCH_TARGET_OK_TOKEN, resolve_interactive_launch_target  # 新增代码+Phase107InteractiveLaunchTarget：导入即将实现的 Phase107 目标解析器；如果没有这行代码，测试无法锁定新合同。


class WindowsComputerUseInteractiveLaunchTargetPhase107Tests(unittest.TestCase):  # 新增代码+Phase107InteractiveLaunchTarget：类段开始，验证 Phase107 交互启动目标解析；如果没有这个类，别名识别和高风险拒绝没有回归保护。
    def _confirmation_token(self, request_output: str) -> str:  # 新增代码+Phase107InteractiveLaunchTarget：函数段开始，从 full 请求输出提取 token；如果没有这段函数，测试只能硬编码动态 token。
        for line in request_output.splitlines():  # 新增代码+Phase107InteractiveLaunchTarget：逐行扫描终端输出；如果没有这行代码，多行面板无法解析。
            if line.startswith("- confirmation_token="):  # 新增代码+Phase107InteractiveLaunchTarget：识别确认 token 行；如果没有这行代码，可能误读其他字段。
                return line.split("=", 1)[1].strip()  # 新增代码+Phase107InteractiveLaunchTarget：返回 token 文本；如果没有这行代码，full-confirm 命令无法构造。
        self.fail("missing confirmation token in /computer use --full output")  # 新增代码+Phase107InteractiveLaunchTarget：明确报告 token 缺失；如果没有这行代码，失败原因会变成空 token。
    # 新增代码+Phase107InteractiveLaunchTarget：函数段结束，_confirmation_token 到此结束；如果没有这个边界说明，初学者不容易看出 token 解析范围。

    def _confirm_full_mode(self, workspace: Path) -> None:  # 修改代码+FullNaturalUserFlow：函数段开始，按真实用户的一行命令打开 full mode；如果没有这段函数，测试会继续模拟动态 token 流程。
        full_output = run_computer_terminal_command(workspace, "/computer use --full")  # 修改代码+FullNaturalUserFlow：直接执行用户会输入的 full 命令；如果没有这行代码，后续 launch 应被拒绝。
        self.assertIn("full_mode=true", full_output)  # 修改代码+FullNaturalUserFlow：断言 full 已打开；如果没有这行代码，后续测试前置条件可能是假的。
        self.assertNotIn("/computer use --full-confirm", full_output)  # 新增代码+FullNaturalUserFlow：断言测试 helper 不再依赖 full-confirm；如果没有这行代码，旧流程可能回归。
    # 修改代码+FullNaturalUserFlow：函数段结束，_confirm_full_mode 到此结束；如果没有这个边界说明，初学者不容易看出自然 full 打开范围。

    def test_resolver_maps_chinese_notepad_alias_to_supported_target(self) -> None:  # 新增代码+Phase107InteractiveLaunchTarget：函数段开始，验证中文记事本别名可解析；如果没有这段测试，中文用户命令可能被误拒绝。
        result = resolve_interactive_launch_target("记事本")  # 新增代码+Phase107InteractiveLaunchTarget：解析中文目标；如果没有这行代码，新解析器没有被直接覆盖。
        self.assertTrue(result["interactive_target_resolved"])  # 新增代码+Phase107InteractiveLaunchTarget：断言目标被解析；如果没有这行代码，别名可能只是返回空默认值。
        self.assertEqual(result["canonical_target"], "notepad")  # 新增代码+Phase107InteractiveLaunchTarget：断言规范目标是 notepad；如果没有这行代码，后续真实链路无法复用 Phase105。
        self.assertTrue(result["safe_known_ordinary_app"])  # 新增代码+Phase107InteractiveLaunchTarget：断言属于普通安全应用；如果没有这行代码，目标可能被错误标高风险。
        self.assertTrue(result["real_launch_supported"])  # 新增代码+Phase107InteractiveLaunchTarget：断言 Notepad 是当前唯一真实启动支持目标；如果没有这行代码，Phase107 边界不可见。
        self.assertFalse(result["high_risk_refused"])  # 新增代码+Phase107InteractiveLaunchTarget：断言没有高风险拒绝；如果没有这行代码，中文 Notepad 可能被误拦截。
    # 新增代码+Phase107InteractiveLaunchTarget：函数段结束，test_resolver_maps_chinese_notepad_alias_to_supported_target 到此结束；如果没有这个边界说明，初学者不容易看出别名测试范围。

    def test_launch_calc_is_recognized_but_real_launch_stays_disabled(self) -> None:  # 新增代码+Phase107InteractiveLaunchTarget：函数段开始，验证 calc 能识别但默认不真实启动；如果没有这段测试，Phase107 可能过早打开新应用。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase107InteractiveLaunchTarget：创建临时 workspace；如果没有这行代码，测试会污染真实用户状态。
            workspace = Path(temp_dir)  # 新增代码+Phase107InteractiveLaunchTarget：保存 workspace 路径；如果没有这行代码，多条命令可能写到不同目录。
            self._confirm_full_mode(workspace)  # 新增代码+Phase107InteractiveLaunchTarget：先按真实流程确认 full；如果没有这行代码，launch 命令应该被 mode gate 拒绝。
            output = run_computer_terminal_command(workspace, "/computer launch calc")  # 新增代码+Phase107InteractiveLaunchTarget：执行用户风格 calc 启动命令；如果没有这行代码，交互路径没有覆盖。
        self.assertIn(PHASE107_INTERACTIVE_LAUNCH_TARGET_MARKER, output)  # 新增代码+Phase107InteractiveLaunchTarget：断言输出包含 Phase107 marker；如果没有这行代码，验收器无法定位解析结果。
        self.assertIn(PHASE107_INTERACTIVE_LAUNCH_TARGET_OK_TOKEN, output)  # 新增代码+Phase107InteractiveLaunchTarget：断言安全识别路径成功；如果没有这行代码，解析成功和失败无法区分。
        self.assertIn(PHASE106_INTERACTIVE_FULL_LAUNCH_OK_TOKEN, output)  # 新增代码+Phase107InteractiveLaunchTarget：断言命令整体安全完成；如果没有这行代码，用户不知道 calc 默认关闭是否算成功处理。
        self.assertIn("canonical_target=calc", output)  # 新增代码+Phase107InteractiveLaunchTarget：断言 calc 被规范化；如果没有这行代码，输出无法证明解析对象。
        self.assertIn("safe_known_ordinary_app=true", output)  # 新增代码+Phase107InteractiveLaunchTarget：断言 calc 被识别为普通应用；如果没有这行代码，后续扩展无法区分普通和高风险目标。
        self.assertIn("real_launch_supported=false", output)  # 新增代码+Phase107InteractiveLaunchTarget：断言 calc 暂不支持真实启动；如果没有这行代码，用户可能误以为已经打开计算器。
        self.assertIn("real_full_launch_attempted=false", output)  # 新增代码+Phase107InteractiveLaunchTarget：断言没有尝试真实启动；如果没有这行代码，自动测试可能误触桌面。
        self.assertIn("real_desktop_touched=false", output)  # 新增代码+Phase107InteractiveLaunchTarget：断言没有触碰桌面；如果没有这行代码，安全边界不可见。
    # 新增代码+Phase107InteractiveLaunchTarget：函数段结束，test_launch_calc_is_recognized_but_real_launch_stays_disabled 到此结束；如果没有这个边界说明，初学者不容易看出 calc 默认关闭测试范围。

    def test_launch_powershell_is_refused_before_any_real_action(self) -> None:  # 新增代码+Phase107InteractiveLaunchTarget：函数段开始，验证 powershell 高风险目标被零副作用拒绝；如果没有这段测试，命令可能打开终端类高风险应用。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase107InteractiveLaunchTarget：创建临时 workspace；如果没有这行代码，测试会污染真实状态。
            workspace = Path(temp_dir)  # 新增代码+Phase107InteractiveLaunchTarget：保存 workspace 路径；如果没有这行代码，full 和 launch 状态可能分裂。
            self._confirm_full_mode(workspace)  # 新增代码+Phase107InteractiveLaunchTarget：确认 full 后再测高风险拒绝；如果没有这行代码，拒绝可能只是 mode gate 造成的。
            output = run_computer_terminal_command(workspace, "/computer launch powershell")  # 新增代码+Phase107InteractiveLaunchTarget：执行高风险目标命令；如果没有这行代码，拒绝路径没有覆盖。
        self.assertIn(PHASE107_INTERACTIVE_LAUNCH_TARGET_MARKER, output)  # 新增代码+Phase107InteractiveLaunchTarget：断言输出包含 Phase107 marker；如果没有这行代码，拒绝报告难以定位。
        self.assertNotIn(PHASE106_INTERACTIVE_FULL_LAUNCH_OK_TOKEN, output)  # 新增代码+Phase107InteractiveLaunchTarget：断言高风险拒绝没有 Phase106 成功 token；如果没有这行代码，失败可能被误判成功。
        self.assertIn("decision=windows_app_high_risk_target_refused", output)  # 修改代码+CompatSlimming：断言统一 resolver 给出高风险拒绝原因；如果没有这行代码，高风险边界不可验收。
        self.assertIn("high_risk_refused=true", output)  # 新增代码+Phase107InteractiveLaunchTarget：断言高风险字段为真；如果没有这行代码，策略报告不完整。
        self.assertIn("real_full_launch_attempted=false", output)  # 新增代码+Phase107InteractiveLaunchTarget：断言没有尝试真实启动；如果没有这行代码，拒绝路径可能仍触碰后端。
        self.assertIn("real_desktop_touched=false", output)  # 新增代码+Phase107InteractiveLaunchTarget：断言没有触碰桌面；如果没有这行代码，高风险拒绝不可证明安全。
        self.assertIn("uncontrolled_actions_expanded=false", output)  # 新增代码+Phase107InteractiveLaunchTarget：断言没有扩大无边界动作；如果没有这行代码，full 模式风险不可见。
    # 新增代码+Phase107InteractiveLaunchTarget：函数段结束，test_launch_powershell_is_refused_before_any_real_action 到此结束；如果没有这个边界说明，初学者不容易看出高风险拒绝测试范围。
# 新增代码+Phase107InteractiveLaunchTarget：类段结束，WindowsComputerUseInteractiveLaunchTargetPhase107Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase107InteractiveLaunchTarget：文件入口段开始，允许直接运行测试文件；如果没有这行代码，初学者必须记完整 unittest 命令。
    unittest.main()  # 新增代码+Phase107InteractiveLaunchTarget：启动 unittest；如果没有这行代码，直接执行文件不会跑测试。
# 新增代码+Phase107InteractiveLaunchTarget：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出入口范围。
