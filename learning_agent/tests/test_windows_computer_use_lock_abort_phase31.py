import json  # 新增代码+Phase31ComputerUseLockAbortEvidence: 导入 JSON 工具用于检查落盘审计是否泄露敏感文本；如果没有这行代码，测试无法把结果统一序列化检查。
import tempfile  # 新增代码+Phase31ComputerUseLockAbortEvidence: 导入临时目录工具隔离锁和审计文件；如果没有这行代码，测试可能污染真实运行 memory 目录。
import unittest  # 新增代码+Phase31ComputerUseLockAbortEvidence: 导入 unittest 框架承载 Phase 31 红灯测试；如果没有这行代码，自动化测试发现不了这些验收标准。
from pathlib import Path  # 新增代码+Phase31ComputerUseLockAbortEvidence: 导入 Path 统一处理 Windows 路径；如果没有这行代码，临时目录路径拼接会更容易写错。
from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase31ComputerUseLockAbortEvidence: 导入 /computer 终端命令入口；如果没有这行代码，真实终端状态 UI 无法被单元测试覆盖。
from learning_agent.computer_use.audit import ComputerUseAuditStore  # 新增代码+Phase31ComputerUseLockAbortEvidence: 导入 Phase 31 审计落盘仓库；如果没有这行代码，动作 evidence chain 无法保存到磁盘。
from learning_agent.computer_use.controller import ComputerUseController, MemoryComputerUseBackend  # 新增代码+Phase31ComputerUseLockAbortEvidence: 导入控制器和内存后端作为被测对象；如果没有这行代码，测试无法验证动作链路。
from learning_agent.computer_use.lock import ComputerUseLockManager  # 新增代码+Phase31ComputerUseLockAbortEvidence: 导入锁管理器验证串行控制和陈旧锁恢复；如果没有这行代码，Phase 31 的锁能力无法被测试。

class WindowsComputerUseLockAbortPhase31Tests(unittest.TestCase):  # 新增代码+Phase31ComputerUseLockAbortEvidence: 定义 Phase 31 测试集合；如果没有这个类，unittest 不会组织这些锁、abort 和 evidence chain 测试。
    def _window(self) -> dict[str, object]:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，提供稳定的测试窗口样本；如果没有这段函数，每个测试都要重复手写窗口字段且容易不一致。
        return {"app_id": "notepad.exe", "window_id": "hwnd:3101", "title_preview": "Phase31 Notepad", "rect": {"left": 30, "top": 40, "right": 330, "bottom": 240}}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回带身份和矩形的可信窗口；如果没有这行代码，动作前后证据无法绑定具体窗口。
    # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，_window 到此结束；如果没有这个边界说明，初学者不容易看出样本 helper 的范围。

    def test_stale_lock_can_be_recovered_by_new_session(self) -> None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，验证陈旧 owner 不会永久霸占桌面锁；如果没有这个测试，崩溃进程留下的锁会长期堵住后续控制。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 创建临时锁目录；如果没有这行代码，陈旧锁测试会写入真实 memory 目录。
            lock_manager = ComputerUseLockManager(base_dir=Path(temp_dir), stale_after_seconds=0)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 创建立即视为陈旧的锁管理器；如果没有这行代码，测试无法稳定触发恢复路径。
            first_result = lock_manager.acquire("old-session", owner_label="crashed-test")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 先让旧会话持有锁；如果没有这行代码，新会话没有可恢复的旧 owner。
            second_result = lock_manager.acquire("new-session", owner_label="recovery-test")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 再让新会话尝试恢复陈旧锁；如果没有这行代码，恢复能力不会被触发。
            self.assertTrue(first_result["acquired"])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言旧会话确实先拿到锁；如果没有这行代码，后续恢复断言没有前提。
            self.assertTrue(second_result["acquired"])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言新会话可以接管陈旧锁；如果没有这行代码，测试无法证明陈旧锁恢复成功。
            self.assertEqual(second_result["status"]["owner_session_id"], "new-session")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言当前 owner 已切换到新会话；如果没有这行代码，恢复可能只是返回成功但状态没变。
            self.assertEqual(second_result["status"]["recovered_stale_owner_session_id"], "old-session")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言状态保留被恢复的旧 owner；如果没有这行代码，事后审计不知道谁被接管。
    # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，test_stale_lock_can_be_recovered_by_new_session 到此结束；如果没有这个边界说明，读者不容易看出陈旧锁测试范围。

    def test_action_writes_before_after_evidence_chain_and_disk_audit(self) -> None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，验证动作前后证据链和审计落盘；如果没有这个测试，动作成功后仍可能没有可复盘证据。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 创建临时目录隔离审计和锁文件；如果没有这行代码，测试会污染真实审计日志。
            root = Path(temp_dir)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 保存临时根路径便于复用；如果没有这行代码，后续路径会重复构造更难读。
            window = self._window()  # 新增代码+Phase31ComputerUseLockAbortEvidence: 生成可信窗口样本；如果没有这行代码，控制器会因缺少窗口目标而拒绝动作。
            backend = MemoryComputerUseBackend(windows=[window])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 创建不触碰真实桌面的内存后端；如果没有这行代码，测试可能误用真实 Windows 后端。
            lock_manager = ComputerUseLockManager(base_dir=root / "locks")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 创建隔离的桌面锁管理器；如果没有这行代码，控制器无法验证当前会话持锁。
            audit_store = ComputerUseAuditStore(base_dir=root / "audit")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 创建隔离的审计仓库；如果没有这行代码，动作事件不会落盘保存。
            controller = ComputerUseController(backend=backend, lock_manager=lock_manager, audit_store=audit_store, owner_session_id="phase31-session")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 注入后端、锁和审计仓库；如果没有这行代码，测试无法覆盖完整 Phase 31 链路。
            lock_manager.acquire("phase31-session", owner_label="unit-test")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 让当前会话先持有锁；如果没有这行代码，动作会在执行前被缺锁门禁拒绝。
            result = controller.execute({"action": "click", "confirm_desktop_control": True, "window": window, "x": 4, "y": 8})  # 新增代码+Phase31ComputerUseLockAbortEvidence: 执行一次带窗口目标的点击；如果没有这行代码，证据链不会产生。
            evidence = result.data["action_evidence"]  # 新增代码+Phase31ComputerUseLockAbortEvidence: 取出动作证据 envelope；如果没有这行代码，后续断言会重复索引难以阅读。
            stored_events = audit_store.read_events()  # 新增代码+Phase31ComputerUseLockAbortEvidence: 读取落盘审计事件；如果没有这行代码，测试只检查内存结果无法证明磁盘审计存在。
            chain_path = Path(evidence["chain_path"])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 读取 evidence chain 文件路径；如果没有这行代码，测试无法确认链路文件真实存在。
            self.assertTrue(result.ok)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言动作成功；如果没有这行代码，后续证据断言可能在失败路径上误判。
            self.assertEqual(evidence["before_evidence"]["audit_id"], result.data["audit_id"])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言动作前证据绑定同一个 audit_id；如果没有这行代码，before 证据可能无法追溯。
            self.assertEqual(evidence["after_evidence"]["audit_id"], result.data["audit_id"])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言动作后证据绑定同一个 audit_id；如果没有这行代码，after 证据可能无法追溯。
            self.assertEqual(evidence["before_evidence"]["phase"], "before")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言前证据标明 before 阶段；如果没有这行代码，读者无法区分动作前后状态。
            self.assertEqual(evidence["after_evidence"]["phase"], "after")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言后证据标明 after 阶段；如果没有这行代码，动作后状态无法被明确识别。
            self.assertTrue(chain_path.exists())  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言证据链文件已经落盘；如果没有这行代码，内存结果可能掩盖持久化缺失。
            self.assertGreaterEqual(len(stored_events), 1)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言至少有一个审计事件落盘；如果没有这行代码，审计仓库可能没有实际写入。
            self.assertEqual(stored_events[-1]["audit_id"], result.data["audit_id"])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言最后一条审计事件与动作结果一致；如果没有这行代码，落盘事件可能和结果断链。
    # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，test_action_writes_before_after_evidence_chain_and_disk_audit 到此结束；如果没有这个边界说明，读者不容易看出证据链测试范围。

    def test_disk_audit_does_not_store_raw_sensitive_text(self) -> None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，验证落盘审计不保存原始敏感文本；如果没有这个测试，密码或 token 可能进入磁盘日志。
        secret_text = "phase31-secret-password-456"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 准备敏感文本样本；如果没有这行代码，脱敏测试没有明确泄露目标。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 创建临时目录隔离审计文件；如果没有这行代码，敏感文本测试会污染真实运行目录。
            root = Path(temp_dir)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 保存临时根路径；如果没有这行代码，路径表达会重复且不清楚。
            window = self._window()  # 新增代码+Phase31ComputerUseLockAbortEvidence: 生成可信窗口样本；如果没有这行代码，type_text 会因缺少目标窗口被拒绝。
            backend = MemoryComputerUseBackend(windows=[window])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 创建内存后端；如果没有这行代码，测试可能触碰真实桌面。
            lock_manager = ComputerUseLockManager(base_dir=root / "locks")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 创建隔离锁管理器；如果没有这行代码，动作无法通过持锁门禁。
            audit_store = ComputerUseAuditStore(base_dir=root / "audit")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 创建隔离审计仓库；如果没有这行代码，无法检查落盘脱敏。
            controller = ComputerUseController(backend=backend, lock_manager=lock_manager, audit_store=audit_store, owner_session_id="phase31-session")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 创建带审计仓库的控制器；如果没有这行代码，测试无法跑完整执行链路。
            lock_manager.acquire("phase31-session", owner_label="unit-test")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 获取当前会话锁；如果没有这行代码，type_text 会被缺锁拒绝。
            result = controller.execute({"action": "type_text", "confirm_desktop_control": True, "window": window, "text": secret_text})  # 新增代码+Phase31ComputerUseLockAbortEvidence: 执行文本输入动作；如果没有这行代码，审计脱敏不会被触发。
            serialized_disk = json.dumps({"events": audit_store.read_events(), "chains": audit_store.read_chains()}, ensure_ascii=False)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 序列化所有落盘审计和证据链；如果没有这行代码，检查范围可能遗漏某个文件。
            self.assertTrue(result.ok)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言文本动作成功；如果没有这行代码，脱敏测试可能只覆盖失败路径。
            self.assertNotIn(secret_text, serialized_disk)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言敏感原文没有进入磁盘；如果没有这行代码，落盘审计可能泄露秘密。
            self.assertIn("text_sha256_16", serialized_disk)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言落盘审计保留短哈希用于关联；如果没有这行代码，完全脱敏后也会失去可追溯性。
    # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，test_disk_audit_does_not_store_raw_sensitive_text 到此结束；如果没有这个边界说明，读者不容易看出脱敏测试范围。

    def test_computer_terminal_command_can_show_abort_and_clear_status(self) -> None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，验证 /computer 终端状态 UI 可请求和清除 abort；如果没有这个测试，真实用户无法在终端中中断桌面控制。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 创建临时 workspace；如果没有这行代码，终端命令会写到真实 memory 目录。
            workspace = Path(temp_dir)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 保存临时 workspace 路径；如果没有这行代码，终端命令路径不清晰。
            abort_output = run_computer_terminal_command(workspace, "/computer abort phase31-test")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 通过 /computer 请求 abort；如果没有这行代码，终端中断入口不会被验证。
            clear_output = run_computer_terminal_command(workspace, "/computer clear-abort")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 通过 /computer 清除 abort；如果没有这行代码，恢复入口不会被验证。
            self.assertIn("Computer Action", abort_output)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言输出属于 /computer 动作面板；如果没有这行代码，命令可能返回了错误文本。
            self.assertIn("abort_requested=true", abort_output)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言 abort 请求已经生效；如果没有这行代码，终端状态可能没有真正写入 abort flag。
            self.assertIn("abort_requested=false", clear_output)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言 abort 已被清除；如果没有这行代码，清除命令可能只是打印但未修改状态。
    # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，test_computer_terminal_command_can_show_abort_and_clear_status 到此结束；如果没有这个边界说明，读者不容易看出终端命令测试范围。

    def test_phase31_visible_terminal_scenario_documents_success_markers(self) -> None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，验证真实终端验收场景包含 Phase31 关键断言；如果没有这个测试，场景文件被删或漏断言也不容易发现。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase31ComputerUseLockAbortEvidence: 定位 OpenHarness-main 根目录；如果没有这行代码，测试无法稳定找到场景文件。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase31_windows_lock_abort_evidence.json"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 定位 Phase31 真实终端场景；如果没有这行代码，测试可能检查错文件。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase31ComputerUseLockAbortEvidence: 读取并解析场景 JSON；如果没有这行代码，场景格式错误不会被发现。
        prompt_text = " ".join(scenario["prompt_lines"])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 合并 prompt 便于查找关键命令；如果没有这行代码，断言需要逐行重复搜索。
        expected_tokens = {"PHASE31_WINDOWS_LOCK_ABORT_EVIDENCE_OK", "recovered=true", "chain=true", "before=true", "after=true", "abort_blocked=true", "raw_text_hidden=true", "terminal_abort=true", "terminal_clear=true", "coord=34,48"}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 列出场景必须覆盖的成功证据；如果没有这行代码，场景可能只剩空成功标记。
        self.assertIn("run_computer_terminal_command", prompt_text)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言真实终端场景会覆盖 /computer 命令入口；如果没有这行代码，终端 UI 可能缺少验收。
        for token in expected_tokens:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 遍历每个关键成功 token；如果没有这行代码，断言会散落且容易漏。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言日志检查包含该 token；如果没有这行代码，终端命令输出可能没有被 verifier 检查。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 断言最终回答检查包含该 token；如果没有这行代码，用户可见答案可能少复制关键证据。
    # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，test_phase31_visible_terminal_scenario_documents_success_markers 到此结束；如果没有这个边界说明，读者不容易看出场景检查范围。

if __name__ == "__main__":  # 新增代码+Phase31ComputerUseLockAbortEvidence: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式单独验证 Phase 31。
    unittest.main()  # 新增代码+Phase31ComputerUseLockAbortEvidence: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行任何测试。
