import tempfile  # 新增代码+Phase102FullModeExecutionGate：导入临时目录隔离 full 模式状态；如果没有这行代码，测试会污染真实 memory 目录。
import unittest  # 新增代码+Phase102FullModeExecutionGate：导入 unittest 沿用项目现有测试框架；如果没有这行代码，标准测试发现机制找不到本文件。
from pathlib import Path  # 新增代码+Phase102FullModeExecutionGate：导入 Path 统一拼接 Windows 路径；如果没有这行代码，临时目录路径会更脆弱。

from learning_agent.computer_use.mode_session import ComputerUseModeSessionStore  # 新增代码+Phase102FullModeExecutionGate：导入 mode session store 用真实 token 流程进入 full；如果没有这行代码，测试无法覆盖 `/computer use --full-confirm` 后的状态。
from learning_agent.computer_use.universal_live_execution import UniversalWindowsLiveExecutionGate  # 新增代码+Phase102FullModeExecutionGate：导入通用 live execution gate；如果没有这行代码，测试只能测底层 store 而不能证明执行入口接入 full。


class WindowsComputerUseFullModeExecutionPhase102Tests(unittest.TestCase):  # 新增代码+Phase102FullModeExecutionGate：类段开始，集中验证 full 模式接入通用执行入口；如果没有这个类，`/computer use --full` 可能停留在状态显示。
    def _confirmed_full_store(self, root: Path) -> ComputerUseModeSessionStore:  # 新增代码+Phase102FullModeExecutionGate：函数段开始，创建并确认 full mode store；如果没有这段函数，每个测试都要重复 token 流程且容易漏确认。
        store = ComputerUseModeSessionStore(base_dir=root / "mode_sessions")  # 新增代码+Phase102FullModeExecutionGate：创建隔离 mode store；如果没有这行代码，full 状态会写入真实项目 memory。
        request = store.request_full_mode(reason="Phase102 test requests full mode")  # 新增代码+Phase102FullModeExecutionGate：按真实流程先请求 full token；如果没有这行代码，测试会绕过强确认。
        confirmed = store.confirm_full_mode(request["confirmation_token"], reason="Phase102 test confirms full mode")  # 新增代码+Phase102FullModeExecutionGate：用 token 确认 full；如果没有这行代码，后续执行入口仍处于 off 或 normal。
        self.assertTrue(confirmed["full_mode"])  # 新增代码+Phase102FullModeExecutionGate：断言确认后确实进入 full；如果没有这行代码，后面的放行测试可能在错误前置条件下运行。
        return store  # 新增代码+Phase102FullModeExecutionGate：返回已确认的 store；如果没有这行代码，调用方拿不到 full 状态对象。
    # 新增代码+Phase102FullModeExecutionGate：函数段结束，_confirmed_full_store 到此结束；如果没有这个边界说明，读者不容易看出 helper 范围。

    def test_normal_mode_blocks_launch_app_prompt_without_fake_grant(self) -> None:  # 新增代码+Phase102FullModeExecutionGate：函数段开始，验证 normal 模式不能执行 full 专属启动动作；如果没有这段测试，普通模式可能被误放宽成 full。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase102FullModeExecutionGate：创建临时目录；如果没有这行代码，运行报告和 mode 状态会污染真实项目。
            root = Path(temp_dir)  # 新增代码+Phase102FullModeExecutionGate：保存临时根目录；如果没有这行代码，后续路径会重复构造且容易出错。
            mode_store = ComputerUseModeSessionStore(base_dir=root / "mode_sessions")  # 新增代码+Phase102FullModeExecutionGate：创建隔离 mode store；如果没有这行代码，无法控制 normal 状态。
            mode_store.open_mode(mode="normal", reason="Phase102 normal mode launch should stay blocked")  # 新增代码+Phase102FullModeExecutionGate：打开 normal 模式；如果没有这行代码，拒绝可能只是 off 状态导致而不是 full 专属动作导致。
            runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "live_gate", mode_store=mode_store)  # 新增代码+Phase102FullModeExecutionGate：创建注入 mode store 的 live gate；如果没有这行代码，执行入口不会使用当前 normal 状态。
            report = runtime.run_prompt("请启动一个普通 Windows 应用，只做记录型合同，不要真实打开。", request_real_actions=True)  # 新增代码+Phase102FullModeExecutionGate：运行真实用户风格启动 prompt；如果没有这行代码，launch_app 路径不会被覆盖。
        acted_reports = [event["action_result"] for event in report["loop"]["events"] if event.get("state") == "acted"]  # 新增代码+Phase102FullModeExecutionGate：提取动作事件报告；如果没有这行代码，无法确认动作层是否把启动当成 full 专属动作。
        self.assertTrue(report["mode_session_used"])  # 新增代码+Phase102FullModeExecutionGate：断言执行入口经过 mode session；如果没有这行代码，旧授权路径可能混入。
        self.assertIn("full_mode_session_used", report)  # 新增代码+Phase102FullModeExecutionGate：先断言报告必须声明 full 状态字段；如果没有这行代码，缺字段会变成 KeyError 而不是清晰红灯。
        self.assertIn("full_mode_action_ready", report)  # 新增代码+Phase102FullModeExecutionGate：先断言报告必须声明 full 动作就绪字段；如果没有这行代码，缺字段会变成难读异常。
        self.assertFalse(report["full_mode_session_used"])  # 新增代码+Phase102FullModeExecutionGate：断言 normal 不是 full；如果没有这行代码，报告可能把 normal 和 full 混淆。
        self.assertFalse(report["full_mode_action_ready"])  # 新增代码+Phase102FullModeExecutionGate：断言 normal 下 full 专属动作不可就绪；如果没有这行代码，普通模式可能偷偷放行启动。
        self.assertEqual(report["real_action_decision"], "blocked_by_mode_session")  # 新增代码+Phase102FullModeExecutionGate：断言总报告显示 mode 阻断；如果没有这行代码，用户不知道为什么没有执行。
        self.assertEqual(report["real_action_blocked_decision"], "action_class_not_allowed_by_mode")  # 新增代码+Phase102FullModeExecutionGate：断言底层原因是动作超出 normal；如果没有这行代码，full 权限缺口无法定位。
        self.assertEqual(report["low_level_event_count"], 0)  # 新增代码+Phase102FullModeExecutionGate：断言没有低层事件；如果没有这行代码，拒绝路径可能仍误触真实桌面。
        self.assertTrue(any(action.get("action_class") == "launch_app" for action in acted_reports))  # 新增代码+Phase102FullModeExecutionGate：断言动作层确实识别启动动作；如果没有这行代码，硬编码 click 也可能误通过。
    # 新增代码+Phase102FullModeExecutionGate：函数段结束，test_normal_mode_blocks_launch_app_prompt_without_fake_grant 到此结束；如果没有这个边界说明，读者不容易看出 normal launch 拒绝范围。

    def test_full_mode_allows_launch_app_recording_path_without_physical_dispatch(self) -> None:  # 新增代码+Phase102FullModeExecutionGate：函数段开始，验证 full 模式放行启动类记录型动作；如果没有这段测试，`/computer use --full` 不能证明更宽动作面。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase102FullModeExecutionGate：创建临时目录；如果没有这行代码，full 状态和报告会污染真实项目。
            root = Path(temp_dir)  # 新增代码+Phase102FullModeExecutionGate：保存临时根目录；如果没有这行代码，后续路径会重复且容易写错。
            mode_store = self._confirmed_full_store(root)  # 新增代码+Phase102FullModeExecutionGate：获取已确认 full store；如果没有这行代码，执行入口没有 full 前置条件。
            runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "live_gate", mode_store=mode_store)  # 新增代码+Phase102FullModeExecutionGate：创建共享 full store 的 live gate；如果没有这行代码，运行时读不到确认状态。
            report = runtime.run_prompt("请使用 full 模式启动一个普通 Windows 应用，只做记录型合同，不要真实打开。", request_real_actions=True)  # 新增代码+Phase102FullModeExecutionGate：运行 full 用户风格 prompt；如果没有这行代码，full 专属动作没有执行入口证据。
        acted_reports = [event["action_result"] for event in report["loop"]["events"] if event.get("state") == "acted"]  # 新增代码+Phase102FullModeExecutionGate：提取动作报告；如果没有这行代码，无法检查动作类别和记录型事件。
        self.assertTrue(report["mode_session_used"])  # 新增代码+Phase102FullModeExecutionGate：断言经过 mode session；如果没有这行代码，full 可能没有接到执行入口。
        self.assertIn("full_mode_session_used", report)  # 新增代码+Phase102FullModeExecutionGate：先断言报告必须声明 full 状态字段；如果没有这行代码，缺字段会变成 KeyError 而不是清晰红灯。
        self.assertIn("full_mode_action_ready", report)  # 新增代码+Phase102FullModeExecutionGate：先断言报告必须声明 full 动作就绪字段；如果没有这行代码，缺字段会变成难读异常。
        self.assertTrue(report["full_mode_session_used"])  # 新增代码+Phase102FullModeExecutionGate：断言执行入口看见 full 状态；如果没有这行代码，报告无法证明 `/computer use --full-confirm` 生效。
        self.assertTrue(report["full_mode_action_ready"])  # 新增代码+Phase102FullModeExecutionGate：断言 full 专属动作就绪；如果没有这行代码，full 模式和 normal 模式没有行为差异。
        self.assertTrue(report["authorized_recording_loop_ready"])  # 新增代码+Phase102FullModeExecutionGate：断言记录型闭环就绪；如果没有这行代码，full 可能只在边界层放行但没进动作层。
        self.assertEqual(report["real_action_decision"], "authorized_recording_only")  # 新增代码+Phase102FullModeExecutionGate：断言仍是记录型授权而非物理派发；如果没有这行代码，测试可能误操作桌面。
        self.assertFalse(report["real_dispatch_performed"])  # 新增代码+Phase102FullModeExecutionGate：断言没有物理派发；如果没有这行代码，自动化测试可能触碰本地电脑。
        self.assertEqual(report["low_level_event_count"], 0)  # 新增代码+Phase102FullModeExecutionGate：断言低层事件为零；如果没有这行代码，full 测试可能扩大真实输入范围。
        self.assertTrue(any(action.get("action_class") == "launch_app" and action.get("acted") for action in acted_reports))  # 新增代码+Phase102FullModeExecutionGate：断言 full 记录型动作使用 launch_app；如果没有这行代码，硬编码 click 仍可能误报成功。
        self.assertTrue(any(action.get("safety_decision", {}).get("mode_decision", {}).get("decision") == "allowed_by_computer_use_mode" for action in acted_reports))  # 新增代码+Phase102FullModeExecutionGate：断言放行来自 full mode；如果没有这行代码，旧 per-app grant 可能掩盖问题。
    # 新增代码+Phase102FullModeExecutionGate：函数段结束，test_full_mode_allows_launch_app_recording_path_without_physical_dispatch 到此结束；如果没有这个边界说明，读者不容易看出 full launch 正例范围。
# 新增代码+Phase102FullModeExecutionGate：类段结束，WindowsComputerUseFullModeExecutionPhase102Tests 到此结束；如果没有这个边界说明，读者不容易看出 Phase102 测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase102FullModeExecutionGate：文件入口段开始，允许直接运行测试文件；如果没有这行代码，小白用户必须记完整 unittest 命令。
    unittest.main()  # 新增代码+Phase102FullModeExecutionGate：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
# 新增代码+Phase102FullModeExecutionGate：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，读者不容易看出脚本入口范围。
