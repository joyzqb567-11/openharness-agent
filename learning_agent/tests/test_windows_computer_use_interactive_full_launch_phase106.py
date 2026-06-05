import tempfile  # 新增代码+Phase106InteractiveFullLaunch：导入临时目录工具隔离命令状态；如果没有这行代码，测试会把 full mode token 写进真实项目 memory。
import unittest  # 新增代码+Phase106InteractiveFullLaunch：导入 unittest 测试框架；如果没有这行代码，项目测试发现器无法执行本文件。
from pathlib import Path  # 新增代码+Phase106InteractiveFullLaunch：导入 Path 统一处理 Windows 路径；如果没有这行代码，临时 workspace 路径拼接容易出错。

from learning_agent.app.interactive import PHASE106_INTERACTIVE_FULL_LAUNCH_MARKER, PHASE106_INTERACTIVE_FULL_LAUNCH_OK_TOKEN, run_computer_terminal_command  # 新增代码+Phase106InteractiveFullLaunch：导入即将实现的 Phase106 交互命令合同；如果没有这行代码，测试无法锁定用户命令入口。


class WindowsComputerUseInteractiveFullLaunchPhase106Tests(unittest.TestCase):  # 新增代码+Phase106InteractiveFullLaunch：类段开始，集中验证用户交互命令如何接入 full-mode 受控启动；如果没有这个类，Phase106 缺少回归保护。
    def _confirmation_token(self, request_output: str) -> str:  # 新增代码+Phase106InteractiveFullLaunch：函数段开始，从 `/computer use --full` 输出提取确认 token；如果没有这段函数，测试只能硬编码动态 token。
        for line in request_output.splitlines():  # 新增代码+Phase106InteractiveFullLaunch：逐行扫描终端输出；如果没有这行代码，测试无法兼容多行状态面板。
            if line.startswith("- confirmation_token="):  # 新增代码+Phase106InteractiveFullLaunch：识别 token 所在行；如果没有这行代码，测试可能误取其它字段。
                return line.split("=", 1)[1].strip()  # 新增代码+Phase106InteractiveFullLaunch：返回等号后的 token；如果没有这行代码，确认 full mode 会失败。
        self.fail("missing confirmation token in /computer use --full output")  # 新增代码+Phase106InteractiveFullLaunch：明确报告 token 缺失；如果没有这行代码，测试失败会变成难懂的空 token 问题。
    # 新增代码+Phase106InteractiveFullLaunch：函数段结束，_confirmation_token 到此结束；如果没有这个边界说明，初学者不容易看出 token 提取范围。

    def _confirm_full_mode(self, workspace: Path) -> None:  # 新增代码+Phase106InteractiveFullLaunch：函数段开始，用真实命令流程确认 full mode；如果没有这段函数，测试会绕过用户必须确认的安全设计。
        request_output = run_computer_terminal_command(workspace, "/computer use --full")  # 新增代码+Phase106InteractiveFullLaunch：先申请 full mode token；如果没有这行代码，后续确认没有合法 token。
        token = self._confirmation_token(request_output)  # 新增代码+Phase106InteractiveFullLaunch：从申请输出里读取 token；如果没有这行代码，确认命令无法构造。
        confirm_output = run_computer_terminal_command(workspace, f"/computer use --full-confirm {token}")  # 新增代码+Phase106InteractiveFullLaunch：按真实用户命令确认 full mode；如果没有这行代码，launch 命令应该继续被拒绝。
        self.assertIn("full_mode=true", confirm_output)  # 新增代码+Phase106InteractiveFullLaunch：断言 full mode 已真正打开；如果没有这行代码，后续启动测试的前置条件可能是假的。
    # 新增代码+Phase106InteractiveFullLaunch：函数段结束，_confirm_full_mode 到此结束；如果没有这个边界说明，初学者不容易看出确认流程范围。

    def test_launch_notepad_command_blocks_before_full_confirmation(self) -> None:  # 新增代码+Phase106InteractiveFullLaunch：函数段开始，验证未确认 full 前用户启动命令必须被拦截；如果没有这段测试，普通状态可能误触真实桌面。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase106InteractiveFullLaunch：创建临时 workspace 隔离状态文件；如果没有这行代码，测试会污染真实用户会话。
            output = run_computer_terminal_command(Path(temp_dir), "/computer launch notepad")  # 新增代码+Phase106InteractiveFullLaunch：直接执行用户风格启动命令；如果没有这行代码，测试无法覆盖交互入口。
        self.assertIn(PHASE106_INTERACTIVE_FULL_LAUNCH_MARKER, output)  # 新增代码+Phase106InteractiveFullLaunch：断言输出有稳定 Phase106 marker；如果没有这行代码，验收器无法定位结果。
        self.assertNotIn(PHASE106_INTERACTIVE_FULL_LAUNCH_OK_TOKEN, output)  # 新增代码+Phase106InteractiveFullLaunch：断言未授权时没有 OK token；如果没有这行代码，失败也可能被验收误判为成功。
        self.assertIn("decision=blocked_by_mode_session", output)  # 新增代码+Phase106InteractiveFullLaunch：断言被 mode session 拦截；如果没有这行代码，拒绝原因可能漂移。
        self.assertIn("full_mode_session_used=false", output)  # 新增代码+Phase106InteractiveFullLaunch：断言没有使用 full session；如果没有这行代码，用户看不出为什么被拦。
        self.assertIn("real_desktop_touched=false", output)  # 新增代码+Phase106InteractiveFullLaunch：断言没有触碰真实桌面；如果没有这行代码，安全默认值不可见。
    # 新增代码+Phase106InteractiveFullLaunch：函数段结束，test_launch_notepad_command_blocks_before_full_confirmation 到此结束；如果没有这个边界说明，初学者不容易看出拒绝测试范围。

    def test_launch_notepad_command_reaches_phase105_default_off_after_full_confirmation(self) -> None:  # 新增代码+Phase106InteractiveFullLaunch：函数段开始，验证 full 确认后命令会进入 Phase105 默认关闭桥；如果没有这段测试，功能可能仍停在合同函数里。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase106InteractiveFullLaunch：创建临时 workspace 隔离状态文件；如果没有这行代码，测试会污染真实项目 memory。
            workspace = Path(temp_dir)  # 新增代码+Phase106InteractiveFullLaunch：保存临时 workspace 路径；如果没有这行代码，后续命令路径不统一。
            self._confirm_full_mode(workspace)  # 新增代码+Phase106InteractiveFullLaunch：先按用户命令确认 full mode；如果没有这行代码，启动命令应被安全门拒绝。
            output = run_computer_terminal_command(workspace, "/computer launch notepad")  # 新增代码+Phase106InteractiveFullLaunch：执行 Phase106 用户启动命令；如果没有这行代码，测试无法证明交互入口接到 Phase105。
        self.assertIn(PHASE106_INTERACTIVE_FULL_LAUNCH_MARKER, output)  # 新增代码+Phase106InteractiveFullLaunch：断言输出包含稳定 marker；如果没有这行代码，可见终端验收没有锚点。
        self.assertIn(PHASE106_INTERACTIVE_FULL_LAUNCH_OK_TOKEN, output)  # 新增代码+Phase106InteractiveFullLaunch：断言 full 确认后的安全默认路径通过；如果没有这行代码，验收无法区分成功与普通日志。
        self.assertIn("full_mode_session_used=true", output)  # 新增代码+Phase106InteractiveFullLaunch：断言真正使用 full session；如果没有这行代码，命令可能绕过用户授权状态。
        self.assertIn("controlled_launch_candidate_ready=true", output)  # 新增代码+Phase106InteractiveFullLaunch：断言 Phase105 受控候选已接入；如果没有这行代码，功能可能没有到最后一跳。
        self.assertIn("controlled_real_launch_gate_passed=false", output)  # 新增代码+Phase106InteractiveFullLaunch：断言默认没有放开真实启动门；如果没有这行代码，full 模式可能被误解成无限权限。
        self.assertIn("real_full_launch_attempted=false", output)  # 新增代码+Phase106InteractiveFullLaunch：断言默认安全测试不真实打开 Notepad；如果没有这行代码，自动测试可能误触桌面。
        self.assertIn("real_desktop_touched=false", output)  # 新增代码+Phase106InteractiveFullLaunch：断言默认安全路径没有触碰桌面；如果没有这行代码，安全边界不可见。
        self.assertIn("uncontrolled_actions_expanded=false", output)  # 新增代码+Phase106InteractiveFullLaunch：断言没有扩张成任意应用控制；如果没有这行代码，通用模式可能变成不可控风险。
    # 新增代码+Phase106InteractiveFullLaunch：函数段结束，test_launch_notepad_command_reaches_phase105_default_off_after_full_confirmation 到此结束；如果没有这个边界说明，初学者不容易看出正向默认关闭测试范围。

    def test_launch_notepad_command_blocks_after_computer_stop(self) -> None:  # 新增代码+Phase106InteractiveFullLaunch：函数段开始，验证 `/computer stop` 后启动命令必须再次被拦截；如果没有这段测试，停止命令可能无法收回 full 权限。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase106InteractiveFullLaunch：创建临时 workspace 隔离状态文件；如果没有这行代码，测试会污染真实用户状态。
            workspace = Path(temp_dir)  # 新增代码+Phase106InteractiveFullLaunch：保存临时 workspace 路径；如果没有这行代码，三条命令可能写到不同位置。
            self._confirm_full_mode(workspace)  # 新增代码+Phase106InteractiveFullLaunch：先打开 full mode；如果没有这行代码，stop 后拒绝无法证明是权限被收回。
            run_computer_terminal_command(workspace, "/computer stop")  # 新增代码+Phase106InteractiveFullLaunch：执行真实停止命令；如果没有这行代码，full mode 仍应保持可用。
            output = run_computer_terminal_command(workspace, "/computer launch notepad")  # 新增代码+Phase106InteractiveFullLaunch：停止后再次尝试启动；如果没有这行代码，测试无法覆盖权限回收。
        self.assertIn(PHASE106_INTERACTIVE_FULL_LAUNCH_MARKER, output)  # 新增代码+Phase106InteractiveFullLaunch：断言输出仍有 Phase106 marker；如果没有这行代码，失败报告难以定位。
        self.assertNotIn(PHASE106_INTERACTIVE_FULL_LAUNCH_OK_TOKEN, output)  # 新增代码+Phase106InteractiveFullLaunch：断言 stop 后没有 OK token；如果没有这行代码，权限回收失败可能被误判为成功。
        self.assertIn("real_action_blocked_decision=computer_use_stopped", output)  # 新增代码+Phase106InteractiveFullLaunch：断言拒绝原因是已停止；如果没有这行代码，stop 合同不可验证。
        self.assertIn("real_desktop_touched=false", output)  # 新增代码+Phase106InteractiveFullLaunch：断言停止后没有触碰真实桌面；如果没有这行代码，收权安全性不可见。
    # 新增代码+Phase106InteractiveFullLaunch：函数段结束，test_launch_notepad_command_blocks_after_computer_stop 到此结束；如果没有这个边界说明，初学者不容易看出 stop 测试范围。
# 新增代码+Phase106InteractiveFullLaunch：类段结束，WindowsComputerUseInteractiveFullLaunchPhase106Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase106InteractiveFullLaunch：文件入口段开始，允许初学者直接运行本测试；如果没有这行代码，直接执行文件不会跑测试。
    unittest.main()  # 新增代码+Phase106InteractiveFullLaunch：启动 unittest；如果没有这行代码，脚本入口不会执行任何断言。
# 新增代码+Phase106InteractiveFullLaunch：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出入口范围。
