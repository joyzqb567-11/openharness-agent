import importlib  # 新增代码+InteractiveGenericLaunchMaturity：导入动态模块工具；如果没有这一行，红测无法在 Phase113 还没实现时清楚指出缺失入口。
import tempfile  # 新增代码+InteractiveGenericLaunchMaturity：导入临时目录工具隔离 `/computer` 状态；如果没有这一行，测试会污染用户真实 full 模式记录。
import unittest  # 新增代码+InteractiveGenericLaunchMaturity：导入 unittest 测试框架；如果没有这一行，项目测试运行器找不到本文件的断言。
from pathlib import Path  # 新增代码+InteractiveGenericLaunchMaturity：导入 Path 统一处理 Windows 路径；如果没有这一行，临时 workspace 路径拼接会更脆弱。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+InteractiveGenericLaunchMaturity：导入真实 `/computer` 终端命令入口；如果没有这一行，测试会绕开用户实际输入路径。


class Phase113RecordingProductionBackend:  # 新增代码+InteractiveGenericLaunchMaturity：类段开始，用不碰桌面的假生产后端证明显式真实门会到达 production 后端形状；如果没有这个类，测试可能不得不真的打开本机应用。
    def __init__(self) -> None:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，初始化后端调用记录；如果没有这段函数，测试无法确认后端被调用几次。
        self.launches: list[dict[str, object]] = []  # 新增代码+InteractiveGenericLaunchMaturity：保存收到的启动请求摘要；如果没有这一行，显式门是否真的到达后端无法被断言。
    # 新增代码+InteractiveGenericLaunchMaturity：函数段结束，Phase113RecordingProductionBackend.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch(self, request_like: object) -> dict[str, object]:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，模拟 production 后端但保持零真实桌面副作用；如果没有这段函数，显式门测试会缺少安全替身。
        module = importlib.import_module("learning_agent.computer_use.generic_launch_backend")  # 新增代码+InteractiveGenericLaunchMaturity：读取 Phase110 请求构造器；如果没有这一行，假后端可能和真实后端的 request 形状漂移。
        request = module.build_generic_launch_request(request_like)  # 新增代码+InteractiveGenericLaunchMaturity：把输入统一成 GenericLaunchRequest；如果没有这一行，argv 和授权字段无法稳定检查。
        request_report = request.to_report()  # 新增代码+InteractiveGenericLaunchMaturity：生成可断言的请求摘要；如果没有这一行，测试看不到后端收到的是 argv 不是 shell 字符串。
        self.launches.append(request_report)  # 新增代码+InteractiveGenericLaunchMaturity：记录本次后端调用；如果没有这一行，测试无法证明显式门只调用了一次后端。
        return {"ok": True, "decision": "generic_launch_production_backend_started_owned_process", "backend": "phase110_production_generic_launch_backend", "backend_launch_performed": True, "backend_launch_reaches_launcher": True, "process_started": True, "process_id": 113001, "process_executable": request.executable, "argv": request.argv(), "command_shape": "argv_no_shell", "uses_shell_string": False, "real_desktop_touched": False, "cleanup_registered": True, "owned_process_registered": True, "low_level_event_count": 0}  # 新增代码+InteractiveGenericLaunchMaturity：返回 production 形状的成功报告但不碰桌面；如果没有这一行，显式门无法安全证明最后一跳已接通。
    # 新增代码+InteractiveGenericLaunchMaturity：函数段结束，Phase113RecordingProductionBackend.launch 到此结束；如果没有这个边界说明，初学者不容易看出安全假后端范围。
# 新增代码+InteractiveGenericLaunchMaturity：类段结束，Phase113RecordingProductionBackend 到此结束；如果没有这个边界说明，初学者不容易看出假后端范围。


class WindowsComputerUseInteractiveGenericLaunchMaturityTests(unittest.TestCase):  # 新增代码+InteractiveGenericLaunchMaturity：类段开始，集中验收 Task5 交互通用启动成熟接线；如果没有这个类，蓝图第 5 项没有红绿灯保护。
    def assert_contains_all(self, output: str, expected_parts: list[str]) -> None:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，复用多 token 断言；如果没有这段函数，测试会重复大量 assertIn 噪声。
        for expected_part in expected_parts:  # 新增代码+InteractiveGenericLaunchMaturity：逐个检查输出片段；如果没有这一行，测试只能检查一个字段而漏掉成熟合同。
            self.assertIn(expected_part, output)  # 新增代码+InteractiveGenericLaunchMaturity：断言当前片段存在；如果没有这一行，缺字段也可能误通过。
    # 新增代码+InteractiveGenericLaunchMaturity：函数段结束，assert_contains_all 到此结束；如果没有这个边界说明，初学者不容易看出断言 helper 范围。

    def _confirmation_token(self, request_output: str) -> str:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，从 full 请求输出读取确认 token；如果没有这段函数，测试只能硬编码一次性 token。
        for line in request_output.splitlines():  # 新增代码+InteractiveGenericLaunchMaturity：逐行扫描终端输出；如果没有这一行，多行状态面板中的 token 无法稳定定位。
            if line.startswith("- confirmation_token="):  # 新增代码+InteractiveGenericLaunchMaturity：识别 token 所在行；如果没有这一行，测试可能误读其它字段。
                return line.split("=", 1)[1].strip()  # 新增代码+InteractiveGenericLaunchMaturity：返回等号后的 token 文本；如果没有这一行，full-confirm 命令无法构造。
        self.fail("missing confirmation token in /computer use --full output")  # 新增代码+InteractiveGenericLaunchMaturity：明确报告 token 缺失；如果没有这一行，测试会用空 token 继续误导排查。
    # 新增代码+InteractiveGenericLaunchMaturity：函数段结束，_confirmation_token 到此结束；如果没有这个边界说明，初学者不容易看出 token 解析范围。

    def _confirm_full_mode(self, workspace: Path) -> None:  # 修改代码+FullNaturalUserFlow：函数段开始，用真实用户的一行命令打开 full 模式；如果没有这段函数，测试会继续模拟动态 token 流程。
        full_output = run_computer_terminal_command(workspace, "/computer use --full")  # 修改代码+FullNaturalUserFlow：直接执行用户会输入的 full 命令；如果没有这一行，launch 命令应该仍被权限门拦截。
        self.assertIn("full_mode=true", full_output)  # 修改代码+FullNaturalUserFlow：断言 full 模式确实打开；如果没有这一行，后续启动测试的前置条件可能是假的。
        self.assertNotIn("/computer use --full-confirm", full_output)  # 新增代码+FullNaturalUserFlow：断言测试 helper 不再依赖 full-confirm；如果没有这一行，旧流程可能回归。
    # 修改代码+FullNaturalUserFlow：函数段结束，_confirm_full_mode 到此结束；如果没有这个边界说明，初学者不容易看出自然 full 打开范围。

    def _phase113_module(self):  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，动态读取 Phase113 所在模块；如果没有这段函数，缺实现时错误信息不够集中。
        return importlib.import_module("learning_agent.computer_use.universal_live_execution")  # 新增代码+InteractiveGenericLaunchMaturity：返回 Universal live execution 模块；如果没有这一行，测试拿不到交互通用启动桥。
    # 新增代码+InteractiveGenericLaunchMaturity：函数段结束，_phase113_module 到此结束；如果没有这个边界说明，初学者不容易看出模块读取范围。

    def test_computer_launch_obsidian_reaches_generic_backend_default_off(self) -> None:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，验证 `/computer launch obsidian` 在 full 模式接到通用后端且默认关闭；如果没有这段测试，交互入口可能停在 Phase109 候选。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+InteractiveGenericLaunchMaturity：创建临时 workspace 隔离状态；如果没有这一行，full 模式记录会污染真实项目。
            workspace = Path(temp_dir)  # 新增代码+InteractiveGenericLaunchMaturity：保存 workspace 路径供多条命令共用；如果没有这一行，确认和 launch 可能写到不同目录。
            self._confirm_full_mode(workspace)  # 新增代码+InteractiveGenericLaunchMaturity：先按真实流程打开 full 模式；如果没有这一行，launch 输出会被权限门拦截。
            output = run_computer_terminal_command(workspace, "/computer launch obsidian")  # 新增代码+InteractiveGenericLaunchMaturity：执行用户自然会输入的普通应用启动命令；如果没有这一行，测试无法覆盖真实交互入口。
        self.assert_contains_all(output, ["PHASE113_INTERACTIVE_GENERIC_LAUNCH_READY", "generic_launch_backend_ready=true", "generic_real_launch_candidate_ready=true", "real_full_launch_attempted=false", "backend_launch_performed=false", "default_off_backend_not_called=true", "real_desktop_touched=false", "uncontrolled_actions_expanded=false"])  # 新增代码+InteractiveGenericLaunchMaturity：断言默认关闭但通用后端已接线；如果没有这一行，Task5 可能只显示旧 Phase109 证据。
    # 新增代码+InteractiveGenericLaunchMaturity：函数段结束，test_computer_launch_obsidian_reaches_generic_backend_default_off 到此结束；如果没有这个边界说明，初学者不容易看出默认关闭测试范围。

    def test_explicit_real_gate_reaches_production_backend_without_desktop_touch_in_test(self) -> None:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，验证显式真实门会到达 production 后端形状；如果没有这段测试，Phase113 可能永远只跑 recording。
        module = self._phase113_module()  # 新增代码+InteractiveGenericLaunchMaturity：读取被测 Universal 模块；如果没有这一行，后续无法调用 Phase113 桥。
        backend = Phase113RecordingProductionBackend()  # 新增代码+InteractiveGenericLaunchMaturity：创建零副作用 production 形状后端；如果没有这一行，测试可能触碰真实桌面。
        report = module.run_phase113_interactive_generic_launch_bridge(raw_target="Obsidian", request_real_launch=True, allow_real_gate=True, launch_backend=backend)  # 新增代码+InteractiveGenericLaunchMaturity：显式请求并允许真实门但注入安全后端；如果没有这一行，最后一跳接线没有直接证据。
        self.assertEqual(report["marker"], "PHASE113_INTERACTIVE_GENERIC_LAUNCH_READY")  # 新增代码+InteractiveGenericLaunchMaturity：断言 ready marker 稳定；如果没有这一行，真实终端验收无法定位 Task5 输出。
        self.assertTrue(report["explicit_real_launch_gate_passed"])  # 新增代码+InteractiveGenericLaunchMaturity：断言显式门通过；如果没有这一行，生产后端可能是默认偶然被调用。
        self.assertTrue(report["generic_real_launch_enabled_when_authorized"])  # 新增代码+InteractiveGenericLaunchMaturity：断言授权后真实启动路径可达；如果没有这一行，Phase110 后端可能没接上。
        self.assertTrue(report["backend_launch_reaches_launcher"])  # 新增代码+InteractiveGenericLaunchMaturity：断言到达 launcher 后端；如果没有这一行，报告可能只停在前置计划。
        self.assertEqual(report["backend_name"], "phase110_production_generic_launch_backend")  # 新增代码+InteractiveGenericLaunchMaturity：断言后端形状是 production；如果没有这一行，显式门可能仍偷偷使用 recording 后端。
        self.assertEqual(len(backend.launches), 1)  # 新增代码+InteractiveGenericLaunchMaturity：断言只调用一次后端；如果没有这一行，重复启动风险无法发现。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+InteractiveGenericLaunchMaturity：断言测试替身没有触碰真实桌面；如果没有这一行，自动化测试可能误导用户安全边界。
    # 新增代码+InteractiveGenericLaunchMaturity：函数段结束，test_explicit_real_gate_reaches_production_backend_without_desktop_touch_in_test 到此结束；如果没有这个边界说明，初学者不容易看出显式门测试范围。

    def test_computer_launch_powershell_still_refuses_before_generic_backend(self) -> None:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，验证 PowerShell 仍被高风险拒绝；如果没有这段测试，通用启动可能误放开危险目标。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+InteractiveGenericLaunchMaturity：创建临时 workspace 隔离 full 状态；如果没有这一行，测试会污染真实 mode session。
            workspace = Path(temp_dir)  # 新增代码+InteractiveGenericLaunchMaturity：保存 workspace 路径；如果没有这一行，多条命令不能共享同一授权状态。
            self._confirm_full_mode(workspace)  # 新增代码+InteractiveGenericLaunchMaturity：先打开 full 模式；如果没有这一行，无法证明高风险拒绝不是普通未授权拒绝。
            output = run_computer_terminal_command(workspace, "/computer launch powershell")  # 新增代码+InteractiveGenericLaunchMaturity：执行用户可能输入的危险目标；如果没有这一行，拒绝路径没有交互覆盖。
        self.assertIn("high_risk_refused=true", output)  # 新增代码+InteractiveGenericLaunchMaturity：断言危险目标被识别；如果没有这一行，PowerShell 可能被当普通应用处理。
        self.assertIn("real_full_launch_attempted=false", output)  # 新增代码+InteractiveGenericLaunchMaturity：断言没有尝试真实启动；如果没有这一行，高风险拒绝缺少零副作用证据。
        self.assertNotIn("backend_launch_performed=true", output)  # 新增代码+InteractiveGenericLaunchMaturity：断言未进入后端执行；如果没有这一行，危险目标可能先触发后端再拒绝。
    # 新增代码+InteractiveGenericLaunchMaturity：函数段结束，test_computer_launch_powershell_still_refuses_before_generic_backend 到此结束；如果没有这个边界说明，初学者不容易看出高风险拒绝范围。

    def test_computer_stop_reports_owned_resource_cleanup(self) -> None:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，验证 `/computer stop` 暴露 owned resource cleanup 结果；如果没有这段测试，用户无法确认自有资源已收尾。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+InteractiveGenericLaunchMaturity：创建临时 workspace 隔离 stop 状态；如果没有这一行，测试会影响真实用户会话。
            workspace = Path(temp_dir)  # 新增代码+InteractiveGenericLaunchMaturity：保存 workspace 路径供三条命令共用；如果没有这一行，stop 读不到 launch 所在 session。
            self._confirm_full_mode(workspace)  # 新增代码+InteractiveGenericLaunchMaturity：先打开 full 模式；如果没有这一行，stop 清理路径缺少活动模式上下文。
            run_computer_terminal_command(workspace, "/computer launch obsidian")  # 新增代码+InteractiveGenericLaunchMaturity：先走一次通用默认关闭启动入口；如果没有这一行，stop 清理不会覆盖 Task5 交互路径。
            stop_output = run_computer_terminal_command(workspace, "/computer stop")  # 新增代码+InteractiveGenericLaunchMaturity：执行真实停止命令；如果没有这一行，测试无法覆盖用户手动收尾入口。
        self.assert_contains_all(stop_output, ["stopped=true", "owned_resource_cleanup_completed=true", "residual_owned_process=false", "real_desktop_touched=false"])  # 新增代码+InteractiveGenericLaunchMaturity：断言 stop 输出包含清理完成和无残留；如果没有这一行，cleanup 成熟字段可能不会出现在真实终端。
    # 新增代码+InteractiveGenericLaunchMaturity：函数段结束，test_computer_stop_reports_owned_resource_cleanup 到此结束；如果没有这个边界说明，初学者不容易看出 stop 清理测试范围。
# 新增代码+InteractiveGenericLaunchMaturity：类段结束，WindowsComputerUseInteractiveGenericLaunchMaturityTests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+InteractiveGenericLaunchMaturity：文件入口段开始，允许直接运行本测试文件；如果没有这一行，初学者必须记住完整 unittest 命令。
    unittest.main()  # 新增代码+InteractiveGenericLaunchMaturity：启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+InteractiveGenericLaunchMaturity：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出入口范围。
