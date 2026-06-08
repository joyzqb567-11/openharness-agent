import tempfile  # 新增代码+Phase61AbortStreamingHooks: 导入临时目录隔离 abort/cleanup/streaming 状态；如果没有这行代码，测试会污染真实用户运行状态。
import unittest  # 新增代码+Phase61AbortStreamingHooks: 导入 unittest 承载 Phase61 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase61AbortStreamingHooks: 导入 Path 管理 Windows 路径；如果没有这行代码，临时锁和场景路径更容易拼错。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase61AbortStreamingHooks: 导入真实 `/computer` 终端命令入口；如果没有这行代码，测试无法证明 abort hooks 状态可见。
from learning_agent.computer_use.abort_streaming_hooks import PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER, PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_OK_TOKEN, WindowsComputerUseAbortStreamingHooks, phase61_cli_line, run_phase61_abort_streaming_hooks_contract  # 新增代码+Phase61AbortStreamingHooks: 导入预期 Phase61 abort/streaming hooks 入口；如果没有这行代码，红灯会证明生产模块尚未实现。
from learning_agent.computer_use.lock import ComputerUseLockManager  # 新增代码+Phase61AbortStreamingHooks: 导入 durable lock 管理器；如果没有这行代码，测试无法触发真实 abort flag。
from learning_agent.computer_use.real_sendinput_guard import Phase58RecordingLowLevelSender, Phase58StaticSafeWindowObserver, WindowsRealSendInputGuardRuntime  # 新增代码+Phase61AbortStreamingHooks: 复用 Phase58 安全 sender/runtime；如果没有这行代码，无法证明 abort 后下一次真实动作层发送 0 事件。
from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase61AbortStreamingHooks: 导入静态窗口 inventory；如果没有这行代码，测试会依赖用户真实桌面。


class WindowsComputerUseAbortStreamingHooksPhase61Tests(unittest.TestCase):  # 新增代码+Phase61AbortStreamingHooks: 类段开始，集中验证 abort、cleanup、streaming hook 和热键降级；如果没有这个类，Phase61 没有自动化门禁。
    def _safe_window(self) -> dict[str, object]:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，提供 Phase58 自有安全窗口样本；如果没有这段函数，每个测试都要重复构造目标窗口。
        return {"app_id": "phase58_safe_app", "process_name": "phase58_safe_app", "window_id": "hwnd:6101", "hwnd": 6101, "title_preview": "LearningAgent-Phase58-RealSendInputGuardSmoke", "rect": {"left": 100, "top": 120, "right": 740, "bottom": 520}, "safe_to_target": True}  # 新增代码+Phase61AbortStreamingHooks: 返回满足 Phase58 目标守卫的安全窗口；如果没有这行代码，abort wrapper 无法进入低层 sender 测试。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出安全样本范围。

    def test_abort_before_low_level_sender_sends_zero_events(self) -> None:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，验证 abort 后下一次低层发送为 0；如果没有这个测试，急停可能只改状态不阻断真实动作层。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase61AbortStreamingHooks: 使用临时目录隔离锁和 stream 事件；如果没有这行代码，测试会修改真实 abort flag。
            root = Path(temp_dir)  # 新增代码+Phase61AbortStreamingHooks: 保存临时根目录；如果没有这行代码，后续路径会重复转换。
            lock_manager = ComputerUseLockManager(base_dir=root / "locks")  # 新增代码+Phase61AbortStreamingHooks: 创建隔离锁管理器；如果没有这行代码，abort flag 没有事实源。
            hooks = WindowsComputerUseAbortStreamingHooks(lock_manager=lock_manager, base_dir=root / "hooks")  # 新增代码+Phase61AbortStreamingHooks: 创建 Phase61 hooks；如果没有这行代码，sender 无法读取 abort 状态。
            raw_sender = Phase58RecordingLowLevelSender()  # 新增代码+Phase61AbortStreamingHooks: 创建记录型 sender；如果没有这行代码，测试无法确认底层事件数组为空。
            wrapped_sender = hooks.wrap_low_level_sender(raw_sender)  # 新增代码+Phase61AbortStreamingHooks: 用 Phase61 abort wrapper 包住低层 sender；如果没有这行代码，abort 无法拦截发送前一刻。
            window = self._safe_window()  # 新增代码+Phase61AbortStreamingHooks: 获取安全窗口；如果没有这行代码，Phase58 runtime 没有目标。
            runtime = WindowsRealSendInputGuardRuntime(platform="win32", inventory=StaticWindowsWindowInventory([window]), low_level_sender=wrapped_sender, observer=Phase58StaticSafeWindowObserver(before_text="before", after_text="after"))  # 新增代码+Phase61AbortStreamingHooks: 创建带 abort-aware sender 的 Phase58 runtime；如果没有这行代码，测试无法覆盖真实动作入口。
            lock_manager.request_abort("phase61 unit abort", requested_by="unit-test")  # 新增代码+Phase61AbortStreamingHooks: 在动作前触发 durable abort；如果没有这行代码，wrapper 不会进入拒绝路径。
            result = runtime.execute_safe_action(window, "click", {"x": 12, "y": 34})  # 新增代码+Phase61AbortStreamingHooks: 尝试执行点击；如果没有这行代码，零事件门禁没有动作输入。
            self.assertFalse(result["ok"])  # 新增代码+Phase61AbortStreamingHooks: 断言动作未成功；如果没有这行代码，abort 后仍可能被当成成功。
            self.assertEqual(result["low_level_event_count"], 0)  # 新增代码+Phase61AbortStreamingHooks: 断言低层发送计数为 0；如果没有这行代码，急停副作用不会被发现。
            self.assertEqual(raw_sender.low_level_events, [])  # 新增代码+Phase61AbortStreamingHooks: 直接确认原始 sender 没收到事件；如果没有这行代码，结果字段可能撒谎。
            self.assertEqual(result["dispatch"]["decision"], "aborted_before_low_level_send")  # 新增代码+Phase61AbortStreamingHooks: 断言拒绝原因稳定；如果没有这行代码，用户不知道是 abort 拦截。
            self.assertTrue(any(event.get("event_type") == "computer_use_aborted_before_low_level_send" for event in hooks.stream_events()))  # 新增代码+Phase61AbortStreamingHooks: 断言 streaming 事件记录 abort；如果没有这行代码，流式面板看不到中断原因。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，test_abort_before_low_level_sender_sends_zero_events 到此结束；如果没有这个边界说明，初学者不容易看出 abort 零事件测试范围。

    def test_exception_cleanup_and_stale_lock_recovery_are_hooked(self) -> None:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，验证异常退出会 cleanup 且 stale lock 可恢复；如果没有这个测试，中断路径可能留下锁。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase61AbortStreamingHooks: 使用临时目录隔离锁和事件；如果没有这行代码，测试会污染真实状态。
            root = Path(temp_dir)  # 新增代码+Phase61AbortStreamingHooks: 保存临时根目录；如果没有这行代码，后续路径表达重复。
            lock_manager = ComputerUseLockManager(base_dir=root / "locks", stale_after_seconds=0)  # 新增代码+Phase61AbortStreamingHooks: 创建立即可恢复的锁管理器；如果没有这行代码，stale recovery 测试要等待真实 TTL。
            hooks = WindowsComputerUseAbortStreamingHooks(lock_manager=lock_manager, session_id="phase61-session", base_dir=root / "hooks")  # 新增代码+Phase61AbortStreamingHooks: 创建 hooks 并绑定会话；如果没有这行代码，cleanup 不知道释放哪个 owner。
            lock_manager.acquire("phase61-session", owner_label="unit-test")  # 新增代码+Phase61AbortStreamingHooks: 让当前会话持锁；如果没有这行代码，异常 cleanup 无法证明 release。
            cleanup = hooks.run_with_cleanup("phase61-exception", lambda: (_ for _ in ()).throw(RuntimeError("phase61 boom")))  # 新增代码+Phase61AbortStreamingHooks: 用回调模拟工具异常；如果没有这行代码，异常中断路径没有输入。
            lock_manager.acquire("crashed-session", owner_label="crashed")  # 新增代码+Phase61AbortStreamingHooks: 写入陈旧旧 owner；如果没有这行代码，stale recovery 没有目标。
            recovered = hooks.recover_stale_lock(owner_label="phase61-recovery")  # 新增代码+Phase61AbortStreamingHooks: 执行 stale recovery；如果没有这行代码，恢复路径不会被测试。
            self.assertTrue(cleanup["exception_handled"])  # 新增代码+Phase61AbortStreamingHooks: 断言异常被 hook 捕获并处理；如果没有这行代码，异常可能直接绕过 cleanup。
            self.assertTrue(cleanup["cleanup_completed"])  # 新增代码+Phase61AbortStreamingHooks: 断言 cleanup 已完成；如果没有这行代码，锁残留风险会漏检。
            self.assertFalse(lock_manager.status()["locked"] and lock_manager.status()["owner_session_id"] == "phase61-session")  # 新增代码+Phase61AbortStreamingHooks: 断言原会话锁不再持有；如果没有这行代码，cleanup 可能只是写通知。
            self.assertTrue(recovered["stale_recovered"])  # 新增代码+Phase61AbortStreamingHooks: 断言陈旧锁被恢复；如果没有这行代码，崩溃恢复能力可能失效。
            self.assertTrue(any(event.get("event_type") == "computer_use_exception_cleanup_completed" for event in hooks.stream_events()))  # 新增代码+Phase61AbortStreamingHooks: 断言 streaming 记录异常 cleanup；如果没有这行代码，流式事件缺少中断证据。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，test_exception_cleanup_and_stale_lock_recovery_are_hooked 到此结束；如果没有这个边界说明，初学者不容易看出 cleanup/recovery 测试范围。

    def test_hotkey_fallback_and_terminal_status_are_visible(self) -> None:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，验证全局热键未注册时诚实降级且终端可见；如果没有这个测试，系统可能假装热键成功。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase61AbortStreamingHooks: 使用临时 workspace；如果没有这行代码，终端状态会读真实项目 memory。
            hooks = WindowsComputerUseAbortStreamingHooks(base_dir=Path(temp_dir) / "hooks")  # 新增代码+Phase61AbortStreamingHooks: 创建 hooks 读取 hotkey 方案；如果没有这行代码，测试没有状态对象。
            status = hooks.status()  # 新增代码+Phase61AbortStreamingHooks: 读取 hook 状态；如果没有这行代码，无法检查热键降级。
            output = run_computer_terminal_command(Path(temp_dir), "/computer abort-hooks")  # 新增代码+Phase61AbortStreamingHooks: 通过真实终端命令查看 Phase61 状态；如果没有这行代码，用户入口没有被覆盖。
            self.assertFalse(status["global_hotkey_registered"])  # 新增代码+Phase61AbortStreamingHooks: 断言默认不假装注册全局热键；如果没有这行代码，安全边界可能被误报。
            self.assertTrue(status["terminal_abort_fallback"])  # 新增代码+Phase61AbortStreamingHooks: 断言终端/controller abort 作为降级路径；如果没有这行代码，用户不知道可用替代方案。
            self.assertIn("Computer Abort Streaming Hooks", output)  # 新增代码+Phase61AbortStreamingHooks: 断言终端状态标题可见；如果没有这行代码，Phase61 状态不可发现。
            self.assertIn(PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER, output)  # 新增代码+Phase61AbortStreamingHooks: 断言终端输出 marker；如果没有这行代码，验收器无法稳定匹配。
            self.assertIn("terminal_abort_fallback=true", output)  # 新增代码+Phase61AbortStreamingHooks: 断言降级说明可见；如果没有这行代码，用户会误以为没有 abort 入口。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，test_hotkey_fallback_and_terminal_status_are_visible 到此结束；如果没有这个边界说明，初学者不容易看出热键降级测试范围。

    def test_phase61_cli_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，验证 CLI 和场景 token 稳定；如果没有这个测试，真实终端验收可能漏检 abort during action。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase61AbortStreamingHooks: 使用临时目录隔离合同状态；如果没有这行代码，测试会污染真实 memory。
            report = run_phase61_abort_streaming_hooks_contract(base_dir=Path(temp_dir))  # 新增代码+Phase61AbortStreamingHooks: 运行 Phase61 合同自检；如果没有这行代码，CLI token 没有结构化来源。
        cli_line = phase61_cli_line(report)  # 新增代码+Phase61AbortStreamingHooks: 生成稳定 CLI 行；如果没有这行代码，场景匹配无法验证。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase61_abort_streaming_hooks.json")  # 新增代码+Phase61AbortStreamingHooks: 定位 Phase61 真实终端场景；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase61AbortStreamingHooks: 读取场景文本；如果没有这行代码，token 漏配无法检测。
        expected_tokens = {PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER, PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_OK_TOKEN, "abort_zero_events=true", "exception_cleanup=true", "stale_recovered=true", "streaming_hooks=true", "hotkey_fallback=true", "terminal_status=true", "actions_expanded=false"}  # 新增代码+Phase61AbortStreamingHooks: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase61AbortStreamingHooks: 遍历关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase61AbortStreamingHooks: 断言 CLI 包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase61AbortStreamingHooks: 断言场景包含 token；如果没有这行代码，真实终端验收可能漏检。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，test_phase61_cli_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景测试范围。
# 新增代码+Phase61AbortStreamingHooks: 类段结束，WindowsComputerUseAbortStreamingHooksPhase61Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase61AbortStreamingHooks: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase61AbortStreamingHooks: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
