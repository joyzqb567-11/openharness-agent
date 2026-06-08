import json  # 新增代码+Phase40WindowsAbortCleanup: 导入 JSON 工具检查场景文件和结构化输出；如果没有这行代码，测试无法确认验收 token 是否写进真实场景。
import tempfile  # 新增代码+Phase40WindowsAbortCleanup: 导入临时目录工具隔离锁和通知文件；如果没有这行代码，测试可能污染真实 Computer Use 运行状态。
import unittest  # 新增代码+Phase40WindowsAbortCleanup: 导入 unittest 框架承载 Phase40 红绿灯测试；如果没有这行代码，自动化测试命令不会发现这些验收标准。
from pathlib import Path  # 新增代码+Phase40WindowsAbortCleanup: 导入 Path 统一处理 Windows 路径；如果没有这行代码，临时 workspace 和锁目录拼接更容易写错。
from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase40WindowsAbortCleanup: 导入真实终端 `/computer` 命令入口；如果没有这行代码，Phase40 无法验证用户可见状态 UI。
from learning_agent.computer_use.lock import ComputerUseLockManager  # 新增代码+Phase40WindowsAbortCleanup: 导入已有 durable lock 管理器；如果没有这行代码，测试无法证明 cleanup 会释放当前会话锁。
from learning_agent.computer_use.session_runtime import PHASE40_WINDOWS_ABORT_CLEANUP_MARKER, PHASE40_WINDOWS_ABORT_CLEANUP_OK_TOKEN, WindowsComputerUseSessionRuntime, phase40_cli_line, run_phase40_abort_cleanup_contract  # 新增代码+Phase40WindowsAbortCleanup: 导入预期新增的 Phase40 会话运行时入口；如果没有这行代码，红灯会证明 runtime 层尚未实现。


class WindowsComputerUseSessionRuntimePhase40Tests(unittest.TestCase):  # 新增代码+Phase40WindowsAbortCleanup: 定义 Phase40 测试集合；如果没有这个类，unittest 不会组织 abort、cleanup 和通知运行时测试。
    def test_global_abort_records_notification_and_status(self) -> None:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，验证全局 abort 会写入 durable abort flag 并生成通知；如果没有这个测试，abort 可能仍只是底层锁状态而没有用户可见通知。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase40WindowsAbortCleanup: 创建隔离临时目录；如果没有这行代码，测试会写到真实项目 memory 目录。
            lock_manager = ComputerUseLockManager(base_dir=Path(temp_dir))  # 新增代码+Phase40WindowsAbortCleanup: 创建隔离 lock manager；如果没有这行代码，runtime 没有 durable abort 文件可写。
            runtime = WindowsComputerUseSessionRuntime(lock_manager=lock_manager, session_id="phase40-session")  # 新增代码+Phase40WindowsAbortCleanup: 创建 Phase40 session runtime；如果没有这行代码，测试无法触发新运行时能力。
            result = runtime.request_global_abort("phase40-test-abort", source="unit-test")  # 新增代码+Phase40WindowsAbortCleanup: 请求全局 abort；如果没有这行代码，通知和 abort 状态不会产生。
            status_lines = "\n".join(runtime.terminal_status_lines())  # 新增代码+Phase40WindowsAbortCleanup: 获取终端可见运行时摘要；如果没有这行代码，测试无法确认用户能看到 Phase40 状态。
            self.assertTrue(result["abort_requested"])  # 新增代码+Phase40WindowsAbortCleanup: 断言 abort flag 已经开启；如果没有这行代码，写入失败也可能被漏掉。
            self.assertEqual(result["notification"]["event"], "computer_use_abort_requested")  # 新增代码+Phase40WindowsAbortCleanup: 断言通知事件类型稳定；如果没有这行代码，后续 UI 和验收器无法可靠匹配。
            self.assertIn("phase40-test-abort", result["notification"]["message"])  # 新增代码+Phase40WindowsAbortCleanup: 断言通知保留人类可读原因；如果没有这行代码，用户无法知道为什么被急停。
            self.assertIn(f"runtime_model={runtime.model}", status_lines)  # 新增代码+Phase40WindowsAbortCleanup: 断言终端摘要显示运行时模型；如果没有这行代码，用户看不到当前 Phase40 runtime 版本。
            self.assertIn(PHASE40_WINDOWS_ABORT_CLEANUP_MARKER, status_lines)  # 新增代码+Phase40WindowsAbortCleanup: 断言终端摘要显示阶段 marker；如果没有这行代码，真实终端验收无法稳定定位 Phase40。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，test_global_abort_records_notification_and_status 到此结束；如果没有这个边界说明，初学者不容易看出 abort 通知测试范围。

    def test_cleanup_turn_releases_owned_lock_and_records_notification(self) -> None:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，验证 turn cleanup 会释放当前会话锁并记录通知；如果没有这个测试，锁可能在一轮结束后残留。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase40WindowsAbortCleanup: 创建隔离临时目录；如果没有这行代码，cleanup 测试会影响真实锁文件。
            lock_manager = ComputerUseLockManager(base_dir=Path(temp_dir))  # 新增代码+Phase40WindowsAbortCleanup: 创建隔离 lock manager；如果没有这行代码，cleanup 无法读写当前 owner。
            lock_manager.acquire("phase40-session", owner_label="unit-test")  # 新增代码+Phase40WindowsAbortCleanup: 让当前会话先持有锁；如果没有这行代码，cleanup 无法证明会释放 owned lock。
            runtime = WindowsComputerUseSessionRuntime(lock_manager=lock_manager, session_id="phase40-session")  # 新增代码+Phase40WindowsAbortCleanup: 创建与锁 owner 一致的 runtime；如果没有这行代码，cleanup 不知道该释放哪个 session。
            result = runtime.cleanup_turn(reason="unit-test-cleanup")  # 新增代码+Phase40WindowsAbortCleanup: 执行 turn cleanup；如果没有这行代码，锁不会释放也不会生成通知。
            status = lock_manager.status()  # 新增代码+Phase40WindowsAbortCleanup: 读取 cleanup 后锁状态；如果没有这行代码，测试无法确认释放效果。
            self.assertTrue(result["cleanup_completed"])  # 新增代码+Phase40WindowsAbortCleanup: 断言 cleanup 流程完成；如果没有这行代码，异常路径可能被误认为成功。
            self.assertTrue(result["lock_released"])  # 新增代码+Phase40WindowsAbortCleanup: 断言当前会话锁被释放；如果没有这行代码，残留锁风险会漏检。
            self.assertFalse(status["locked"])  # 新增代码+Phase40WindowsAbortCleanup: 断言 durable lock 状态已经变为未锁定；如果没有这行代码，只看返回值可能掩盖文件未更新。
            self.assertEqual(result["notification"]["event"], "computer_use_turn_cleanup_completed")  # 新增代码+Phase40WindowsAbortCleanup: 断言 cleanup 通知事件稳定；如果没有这行代码，终端 UI 无法可靠解释 cleanup。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，test_cleanup_turn_releases_owned_lock_and_records_notification 到此结束；如果没有这个边界说明，读者不容易看出 cleanup 测试范围。

    def test_computer_terminal_command_exposes_cleanup_and_notifications(self) -> None:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，验证真实终端命令能显示 runtime、通知和 cleanup；如果没有这个测试，底层 runtime 可能无法被用户使用。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase40WindowsAbortCleanup: 创建临时 workspace；如果没有这行代码，终端命令会写真实 workspace 状态。
            workspace = Path(temp_dir)  # 新增代码+Phase40WindowsAbortCleanup: 保存临时 workspace 路径；如果没有这行代码，后续命令路径会重复构造且不清楚。
            lock_root = workspace / "learning_agent" / "memory" / "computer_use" / "locks"  # 新增代码+Phase40WindowsAbortCleanup: 计算 `/computer` 命令使用的 lock 根目录；如果没有这行代码，测试无法预置同一把锁。
            ComputerUseLockManager(base_dir=lock_root).acquire("learning-agent-default-session", owner_label="terminal-test")  # 新增代码+Phase40WindowsAbortCleanup: 预置默认会话锁；如果没有这行代码，`/computer cleanup` 无法证明会释放默认 owner。
            abort_output = run_computer_terminal_command(workspace, "/computer abort phase40-terminal")  # 新增代码+Phase40WindowsAbortCleanup: 通过终端命令触发 abort；如果没有这行代码，真实用户入口不会被覆盖。
            cleanup_output = run_computer_terminal_command(workspace, "/computer cleanup")  # 新增代码+Phase40WindowsAbortCleanup: 通过终端命令触发 cleanup；如果没有这行代码，真实用户入口不会释放 turn 锁。
            notifications_output = run_computer_terminal_command(workspace, "/computer notifications")  # 新增代码+Phase40WindowsAbortCleanup: 通过终端命令查看通知；如果没有这行代码，通知队列可能不可见。
            self.assertIn("Computer Runtime", abort_output)  # 新增代码+Phase40WindowsAbortCleanup: 断言 abort 输出包含 runtime 面板；如果没有这行代码，用户看不到 Phase40 新层。
            self.assertIn("notification_event=computer_use_abort_requested", abort_output)  # 新增代码+Phase40WindowsAbortCleanup: 断言 abort 输出显示通知事件；如果没有这行代码，急停只会静默改变状态。
            self.assertIn("cleanup_completed=true", cleanup_output)  # 新增代码+Phase40WindowsAbortCleanup: 断言 cleanup 输出显示完成；如果没有这行代码，终端无法证明 cleanup 成功。
            self.assertIn("notification_event=computer_use_turn_cleanup_completed", cleanup_output)  # 新增代码+Phase40WindowsAbortCleanup: 断言 cleanup 输出显示通知事件；如果没有这行代码，turn 清理不可追踪。
            self.assertIn("computer_use_abort_requested", notifications_output)  # 新增代码+Phase40WindowsAbortCleanup: 断言通知列表保留 abort 事件；如果没有这行代码，跨命令查看通知会丢失。
            self.assertIn("computer_use_turn_cleanup_completed", notifications_output)  # 新增代码+Phase40WindowsAbortCleanup: 断言通知列表保留 cleanup 事件；如果没有这行代码，cleanup 事件无法复盘。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，test_computer_terminal_command_exposes_cleanup_and_notifications 到此结束；如果没有这个边界说明，读者不容易看出终端测试范围。

    def test_phase40_cli_contract_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，验证 CLI 合同和真实终端场景 token 稳定；如果没有这个测试，验收脚本可能缺少关键断言。
        report = run_phase40_abort_cleanup_contract()  # 新增代码+Phase40WindowsAbortCleanup: 运行 Phase40 合同自检；如果没有这行代码，CLI token 没有结构化依据。
        line = phase40_cli_line(report)  # 新增代码+Phase40WindowsAbortCleanup: 生成稳定单行输出；如果没有这行代码，场景断言很难匹配。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase40WindowsAbortCleanup: 定位项目根目录；如果没有这行代码，场景路径可能随运行目录漂移。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase40_windows_abort_cleanup.json"  # 新增代码+Phase40WindowsAbortCleanup: 定位 Phase40 真实终端场景；如果没有这行代码，测试无法保证验收文件存在。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase40WindowsAbortCleanup: 读取并解析场景 JSON；如果没有这行代码，场景格式错误不会被发现。
        expected_tokens = {PHASE40_WINDOWS_ABORT_CLEANUP_MARKER, PHASE40_WINDOWS_ABORT_CLEANUP_OK_TOKEN, "abort=true", "cleanup=true", "notifications=true", "terminal_status=true", "actions_expanded=false"}  # 新增代码+Phase40WindowsAbortCleanup: 定义必须出现在 CLI 和场景中的 token；如果没有这行代码，场景可能漏检关键能力。
        for token in expected_tokens:  # 新增代码+Phase40WindowsAbortCleanup: 遍历每个关键 token；如果没有这行代码，断言会散落重复且容易漏。
            self.assertIn(token, line)  # 新增代码+Phase40WindowsAbortCleanup: 断言 CLI 行包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase40WindowsAbortCleanup: 断言 debug log 检查包含 token；如果没有这行代码，真实终端 verifier 可能不查该能力。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase40WindowsAbortCleanup: 断言最终回答检查包含 token；如果没有这行代码，用户可见答案可能漏掉证据。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，test_phase40_cli_contract_and_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，读者不容易看出 CLI/场景测试范围。


if __name__ == "__main__":  # 新增代码+Phase40WindowsAbortCleanup: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式单独验证 Phase40。
    unittest.main()  # 新增代码+Phase40WindowsAbortCleanup: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行任何测试。
