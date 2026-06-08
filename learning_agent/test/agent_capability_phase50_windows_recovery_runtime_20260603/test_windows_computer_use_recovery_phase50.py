import json  # 新增代码+Phase50WindowsRecovery: 导入 JSON 工具用于读取验收场景和写入旧锁状态；如果没有这行代码，测试无法确认场景 token 和模拟陈旧锁。
import tempfile  # 新增代码+Phase50WindowsRecovery: 导入临时目录隔离锁、审计和通知状态；如果没有这行代码，测试可能污染真实用户 Computer Use 状态。
import unittest  # 新增代码+Phase50WindowsRecovery: 导入 unittest 测试框架；如果没有这行代码，自动化命令无法发现 Phase50 断言。
from pathlib import Path  # 新增代码+Phase50WindowsRecovery: 导入 Path 统一处理 Windows 路径；如果没有这行代码，测试路径拼接会变脆弱。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase50WindowsRecovery: 导入真实 `/computer` 终端命令入口；如果没有这行代码，Phase50 只能测试底层而不能覆盖用户入口。
from learning_agent.computer_use.audit import ComputerUseAuditStore  # 新增代码+Phase50WindowsRecovery: 导入审计仓库用于构造 action journal；如果没有这行代码，最近动作回放没有持久事件来源。
from learning_agent.computer_use.lock import ComputerUseLockManager  # 新增代码+Phase50WindowsRecovery: 导入 durable lock 管理器用于模拟崩溃残留锁；如果没有这行代码，stale recovery 无法测试。
from learning_agent.computer_use.session_runtime import PHASE50_WINDOWS_RECOVERY_MARKER, PHASE50_WINDOWS_RECOVERY_OK_TOKEN, WindowsComputerUseSessionRuntime, phase50_cli_line, run_phase50_recovery_contract  # 新增代码+Phase50WindowsRecovery: 导入预期新增的 Phase50 恢复合同入口；如果没有这行代码，红灯会证明恢复层尚未实现。
from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase50WindowsRecovery: 导入原子 JSON 写入用于构造陈旧锁文件；如果没有这行代码，测试可能写出半个锁状态。


class WindowsComputerUseRecoveryPhase50Tests(unittest.TestCase):  # 新增代码+Phase50WindowsRecovery: 类段开始，集中验证全局 abort、cleanup、锁恢复和 action journal；如果没有这个类，unittest 不会组织 Phase50 验收。
    def test_cleanup_releases_lock_and_clears_abort_state(self) -> None:  # 新增代码+Phase50WindowsRecovery: 函数段开始，验证 cleanup 会释放锁并清掉 abort；如果没有这个测试，cleanup 可能只释放锁却让急停永久残留。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase50WindowsRecovery: 创建隔离临时目录；如果没有这行代码，测试会写入真实 Computer Use lock 文件。
            lock_manager = ComputerUseLockManager(base_dir=Path(temp_dir))  # 新增代码+Phase50WindowsRecovery: 创建隔离 lock manager；如果没有这行代码，runtime 没有 durable 状态可清理。
            lock_manager.acquire("phase50-session", owner_label="unit-test")  # 新增代码+Phase50WindowsRecovery: 让当前会话持锁；如果没有这行代码，cleanup 无法证明释放 owner。
            lock_manager.request_abort("phase50 cleanup abort", requested_by="unit-test")  # 新增代码+Phase50WindowsRecovery: 预置 abort flag；如果没有这行代码，无法证明 cleanup 会清掉急停状态。
            runtime = WindowsComputerUseSessionRuntime(lock_manager=lock_manager, session_id="phase50-session")  # 新增代码+Phase50WindowsRecovery: 创建 Phase50 运行时；如果没有这行代码，测试无法调用升级后的 cleanup。
            result = runtime.cleanup_turn(reason="phase50 cleanup test")  # 新增代码+Phase50WindowsRecovery: 执行 cleanup；如果没有这行代码，锁和 abort 状态不会变化。
            status = lock_manager.status()  # 新增代码+Phase50WindowsRecovery: 读取 cleanup 后状态；如果没有这行代码，测试只能相信返回值而不能核对磁盘事实。
            self.assertTrue(result["cleanup_completed"])  # 新增代码+Phase50WindowsRecovery: 断言 cleanup 流程完成；如果没有这行代码，异常路径可能被误认为成功。
            self.assertTrue(result["lock_released"])  # 新增代码+Phase50WindowsRecovery: 断言当前会话锁已释放；如果没有这行代码，崩溃残留锁风险会漏检。
            self.assertTrue(result["abort_cleared"])  # 新增代码+Phase50WindowsRecovery: 断言 abort 被 cleanup 清掉；如果没有这行代码，急停可能永久阻断后续安全测试。
            self.assertFalse(status["locked"])  # 新增代码+Phase50WindowsRecovery: 断言 durable lock 文件处于未锁定；如果没有这行代码，释放只可能停留在内存返回里。
            self.assertFalse(status["abort_requested"])  # 新增代码+Phase50WindowsRecovery: 断言 durable abort flag 已关闭；如果没有这行代码，cleanup state 不完整。
    # 新增代码+Phase50WindowsRecovery: 函数段结束，test_cleanup_releases_lock_and_clears_abort_state 到此结束；如果没有这个边界说明，读者不容易看出 cleanup 恢复范围。

    def test_recover_stale_lock_records_previous_owner(self) -> None:  # 新增代码+Phase50WindowsRecovery: 函数段开始，验证陈旧锁可被显式恢复；如果没有这个测试，崩溃 owner 可能永久阻塞桌面控制。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase50WindowsRecovery: 创建隔离临时目录；如果没有这行代码，陈旧锁模拟会污染真实项目。
            lock_manager = ComputerUseLockManager(base_dir=Path(temp_dir), stale_after_seconds=0)  # 新增代码+Phase50WindowsRecovery: 创建立即陈旧的 lock manager；如果没有这行代码，测试需要等待真实 TTL。
            lock_manager.acquire("crashed-session", owner_label="old-owner")  # 新增代码+Phase50WindowsRecovery: 先让旧会话持锁；如果没有这行代码，新会话没有可恢复对象。
            runtime = WindowsComputerUseSessionRuntime(lock_manager=lock_manager, session_id="phase50-session")  # 新增代码+Phase50WindowsRecovery: 创建新会话 runtime；如果没有这行代码，恢复动作没有 owner 身份。
            result = runtime.recover_stale_lock(owner_label="phase50-recovery")  # 新增代码+Phase50WindowsRecovery: 执行显式 stale lock 恢复；如果没有这行代码，恢复能力不会触发。
            self.assertTrue(result["acquired"])  # 新增代码+Phase50WindowsRecovery: 断言新会话获得锁；如果没有这行代码，恢复可能只返回通知但未持锁。
            self.assertTrue(result["stale_recovered"])  # 新增代码+Phase50WindowsRecovery: 断言本次确实恢复了旧 owner；如果没有这行代码，普通 acquire 会误装成恢复。
            self.assertEqual(result["status"]["owner_session_id"], "phase50-session")  # 新增代码+Phase50WindowsRecovery: 断言当前 owner 已切到新会话；如果没有这行代码，锁状态可能没有更新。
            self.assertEqual(result["status"]["recovered_stale_owner_session_id"], "crashed-session")  # 新增代码+Phase50WindowsRecovery: 断言旧 owner 被记录；如果没有这行代码，事故复盘不知道谁崩溃遗留锁。
            self.assertEqual(result["notification"]["event"], "computer_use_stale_lock_recovered")  # 新增代码+Phase50WindowsRecovery: 断言恢复通知事件稳定；如果没有这行代码，终端 UI 无法可靠显示恢复。
    # 新增代码+Phase50WindowsRecovery: 函数段结束，test_recover_stale_lock_records_previous_owner 到此结束；如果没有这个边界说明，读者不容易看出 stale recovery 范围。

    def test_action_journal_replays_recent_audit_chain_summary(self) -> None:  # 新增代码+Phase50WindowsRecovery: 函数段开始，验证 action journal 可回放最近动作链路；如果没有这个测试，用户无法从恢复层看到最近桌面动作证据。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase50WindowsRecovery: 创建隔离临时目录；如果没有这行代码，审计回放测试会读写真实审计目录。
            audit_store = ComputerUseAuditStore(base_dir=Path(temp_dir) / "audit")  # 新增代码+Phase50WindowsRecovery: 创建隔离审计仓库；如果没有这行代码，journal 没有持久化事件来源。
            audit_store.record_event({"audit_id": "phase50-audit-1", "action": "click", "allowed": True, "reason": "unit-test", "argument_summary": {"x": 1, "y": 2}}, {"before_evidence": {"captured": True}, "after_evidence": {"captured": True}})  # 新增代码+Phase50WindowsRecovery: 写入一条带 before/after chain 的审计事件；如果没有这行代码，journal 无法证明链路摘要。
            runtime = WindowsComputerUseSessionRuntime(lock_manager=ComputerUseLockManager(base_dir=Path(temp_dir) / "locks"), audit_store=audit_store, session_id="phase50-session")  # 新增代码+Phase50WindowsRecovery: 创建带审计仓库的 runtime；如果没有这行代码，action_journal 不会读取测试审计。
            journal = runtime.action_journal(limit=3)  # 新增代码+Phase50WindowsRecovery: 读取最近动作回放；如果没有这行代码，测试没有 journal 输出可断言。
            self.assertTrue(journal["journal_available"])  # 新增代码+Phase50WindowsRecovery: 断言 journal 可用；如果没有这行代码，空实现可能通过后续弱断言。
            self.assertEqual(journal["recent_action_count"], 1)  # 新增代码+Phase50WindowsRecovery: 断言回放出一条动作；如果没有这行代码，读取事件数量可能错误。
            self.assertEqual(journal["recent_actions"][0]["audit_id"], "phase50-audit-1")  # 新增代码+Phase50WindowsRecovery: 断言 journal 保留 audit_id；如果没有这行代码，动作和证据链无法关联。
            self.assertTrue(journal["recent_actions"][0]["chain_available"])  # 新增代码+Phase50WindowsRecovery: 断言链路文件可被识别；如果没有这行代码，journal 可能只看事件不看 before/after。
            self.assertTrue(journal["recent_actions"][0]["has_before_evidence"])  # 新增代码+Phase50WindowsRecovery: 断言 before evidence 被识别；如果没有这行代码，动作前证据缺失不会被发现。
            self.assertTrue(journal["recent_actions"][0]["has_after_evidence"])  # 新增代码+Phase50WindowsRecovery: 断言 after evidence 被识别；如果没有这行代码，动作后证据缺失不会被发现。
    # 新增代码+Phase50WindowsRecovery: 函数段结束，test_action_journal_replays_recent_audit_chain_summary 到此结束；如果没有这个边界说明，读者不容易看出 journal 范围。

    def test_computer_terminal_command_exposes_recover_cleanup_and_journal(self) -> None:  # 新增代码+Phase50WindowsRecovery: 函数段开始，验证真实终端 `/computer` 子命令暴露恢复能力；如果没有这个测试，底层恢复合同可能用户用不到。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase50WindowsRecovery: 创建临时 workspace；如果没有这行代码，终端命令会写入真实 workspace。
            workspace = Path(temp_dir)  # 新增代码+Phase50WindowsRecovery: 保存临时 workspace；如果没有这行代码，后续路径重复拼接且难读。
            lock_root = workspace / "learning_agent" / "memory" / "computer_use" / "locks"  # 新增代码+Phase50WindowsRecovery: 计算终端命令使用的 lock 根目录；如果没有这行代码，测试预置锁和命令不会指向同一位置。
            audit_store = ComputerUseAuditStore(base_dir=workspace / "learning_agent" / "memory" / "computer_use" / "audit")  # 新增代码+Phase50WindowsRecovery: 创建终端命令会读取的审计仓库；如果没有这行代码，`/computer journal` 看不到动作。
            atomic_write_json(lock_root / "desktop_control_lock.json", {"locked": True, "owner_session_id": "crashed-terminal", "owner_label": "old", "owner_pid": 0, "acquired_at": "2000-01-01T00:00:00Z"})  # 新增代码+Phase50WindowsRecovery: 写入足够旧的锁状态；如果没有这行代码，`/computer recover` 无法证明接管崩溃锁。
            audit_store.record_event({"audit_id": "phase50-terminal-audit", "action": "click", "allowed": True, "reason": "terminal-test"}, {"before_evidence": {"captured": True}, "after_evidence": {"captured": True}})  # 新增代码+Phase50WindowsRecovery: 写入终端 journal 可读取的动作链；如果没有这行代码，journal 输出会为空。
            recover_output = run_computer_terminal_command(workspace, "/computer recover")  # 新增代码+Phase50WindowsRecovery: 通过真实终端命令执行恢复；如果没有这行代码，用户入口没有被覆盖。
            cleanup_output = run_computer_terminal_command(workspace, "/computer cleanup")  # 新增代码+Phase50WindowsRecovery: 通过真实终端命令执行 cleanup；如果没有这行代码，恢复后的释放入口没有被覆盖。
            journal_output = run_computer_terminal_command(workspace, "/computer journal")  # 新增代码+Phase50WindowsRecovery: 通过真实终端命令读取动作 journal；如果没有这行代码，用户无法复盘最近动作。
            self.assertIn(PHASE50_WINDOWS_RECOVERY_MARKER, recover_output)  # 新增代码+Phase50WindowsRecovery: 断言 recover 输出包含 Phase50 marker；如果没有这行代码，终端验收无法稳定识别阶段。
            self.assertIn("stale_recovered=true", recover_output)  # 新增代码+Phase50WindowsRecovery: 断言 recover 显示陈旧锁已恢复；如果没有这行代码，用户不知道是否接管旧 owner。
            self.assertIn("cleanup_completed=true", cleanup_output)  # 新增代码+Phase50WindowsRecovery: 断言 cleanup 完成；如果没有这行代码，终端无法证明状态释放。
            self.assertIn("journal_available=true", journal_output)  # 新增代码+Phase50WindowsRecovery: 断言 journal 可用；如果没有这行代码，终端 journal 可能只是空面板。
            self.assertIn("phase50-terminal-audit", journal_output)  # 新增代码+Phase50WindowsRecovery: 断言 journal 显示审计 id；如果没有这行代码，用户无法打开对应证据链。
    # 新增代码+Phase50WindowsRecovery: 函数段结束，test_computer_terminal_command_exposes_recover_cleanup_and_journal 到此结束；如果没有这个边界说明，读者不容易看出终端恢复命令范围。

    def test_phase50_cli_contract_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase50WindowsRecovery: 函数段开始，验证 CLI 合同和验收场景 token；如果没有这个测试，真实终端验收可能漏查恢复能力。
        report = run_phase50_recovery_contract()  # 新增代码+Phase50WindowsRecovery: 运行 Phase50 合同自检；如果没有这行代码，CLI token 没有结构化来源。
        line = phase50_cli_line(report)  # 新增代码+Phase50WindowsRecovery: 生成稳定单行输出；如果没有这行代码，验收器需要解析复杂 JSON。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase50WindowsRecovery: 定位项目根目录；如果没有这行代码，场景路径会依赖当前工作目录。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase50_windows_recovery_runtime.json"  # 新增代码+Phase50WindowsRecovery: 定位 Phase50 场景文件；如果没有这行代码，测试无法确认验收配置存在。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase50WindowsRecovery: 读取并解析场景 JSON；如果没有这行代码，场景漏 token 不会被发现。
        expected_tokens = {PHASE50_WINDOWS_RECOVERY_MARKER, PHASE50_WINDOWS_RECOVERY_OK_TOKEN, "stale_recovered=true", "cleanup_state=true", "action_journal=true", "terminal_commands=true", "actions_expanded=false"}  # 新增代码+Phase50WindowsRecovery: 列出 Phase50 必须稳定输出的 token；如果没有这行代码，成功标准会散落且容易漏。
        for token in expected_tokens:  # 新增代码+Phase50WindowsRecovery: 遍历所有关键 token；如果没有这行代码，只能重复写多个断言。
            self.assertIn(token, line)  # 新增代码+Phase50WindowsRecovery: 断言 CLI 行包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase50WindowsRecovery: 断言 debug log 检查包含 token；如果没有这行代码，真实验收可能不看恢复证据。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase50WindowsRecovery: 断言用户可见回答检查包含 token；如果没有这行代码，最终回答可能漏掉恢复证据。
    # 新增代码+Phase50WindowsRecovery: 函数段结束，test_phase50_cli_contract_and_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，读者不容易看出 CLI/场景范围。


if __name__ == "__main__":  # 新增代码+Phase50WindowsRecovery: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式单独验证 Phase50。
    unittest.main()  # 新增代码+Phase50WindowsRecovery: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行断言。
