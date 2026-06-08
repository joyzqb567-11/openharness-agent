import tempfile  # 新增代码+Phase62HighLevelTools: 导入临时目录隔离高层工具状态；如果没有这行代码，测试会污染真实用户的 Computer Use memory。
import unittest  # 新增代码+Phase62HighLevelTools: 导入 unittest 承载 Phase62 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase62HighLevelTools: 导入 Path 管理 Windows 路径；如果没有这行代码，artifact 和 scenario 路径更容易拼错。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase62HighLevelTools: 导入真实 `/computer` 终端命令入口；如果没有这行代码，测试无法证明高层工具状态可见。
from learning_agent.computer_use.abort_streaming_hooks import WindowsComputerUseAbortStreamingHooks  # 新增代码+Phase62HighLevelTools: 导入 Phase61 hooks；如果没有这行代码，高层工具无法验证 abort-aware streaming 链路。
from learning_agent.computer_use.high_level_tools import PHASE62_SUPPORTED_OPERATIONS, PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_OK_TOKEN, WindowsHighLevelComputerToolRuntime, phase62_cli_line, run_phase62_high_level_tools_contract  # 新增代码+Phase62HighLevelTools: 导入预期高层工具 API；如果没有这行代码，红灯会证明 Phase62 生产模块尚未实现。
from learning_agent.computer_use.lock import ComputerUseLockManager  # 新增代码+Phase62HighLevelTools: 导入桌面锁管理器；如果没有这行代码，测试无法证明只读和写动作锁边界。
from learning_agent.computer_use.persistent_grants import WindowsComputerUsePersistentGrantStore  # 新增代码+Phase62HighLevelTools: 导入持久授权 store；如果没有这行代码，写动作无法验证 approve -> action 链路。
from learning_agent.computer_use.real_sendinput_guard import Phase58RecordingLowLevelSender  # 新增代码+Phase62HighLevelTools: 导入记录型低层 sender；如果没有这行代码，测试会触碰真实鼠标键盘。


class WindowsComputerUseHighLevelToolsPhase62Tests(unittest.TestCase):  # 新增代码+Phase62HighLevelTools: 类段开始，集中验证高层 Computer Tool API、streaming 和安全链；如果没有这个类，Phase62 没有自动化门禁。
    def _safe_window(self) -> dict[str, object]:  # 新增代码+Phase62HighLevelTools: 函数段开始，提供 Phase58 自有安全窗口样本；如果没有这段函数，每个测试都要重复构造目标窗口。
        return {"app_id": "phase58_safe_app", "process_name": "phase58_safe_app", "window_id": "hwnd:6201", "hwnd": 6201, "title_preview": "LearningAgent-Phase58-HighLevelToolsSmoke", "rect": {"left": 80, "top": 90, "right": 680, "bottom": 430}, "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase62HighLevelTools: 返回满足 Phase58 目标守卫的窗口；如果没有这行代码，写动作无法进入安全 sender 链。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出安全窗口样本范围。

    def _controls(self) -> list[dict[str, object]]:  # 新增代码+Phase62HighLevelTools: 函数段开始，提供合同用 UIA 控件候选；如果没有这段函数，find/click/type 测试会依赖真实桌面 UIA。
        return [{"node_id": "0", "name": "Phase62 root", "role": "Window", "automation_id": "Phase62Root", "class_name": "Window", "bounds": {"left": 80, "top": 90, "right": 680, "bottom": 430, "width": 600, "height": 340}, "enabled": True, "clickable": False, "editable": False}, {"node_id": "0.1", "name": "Search box", "role": "Edit", "automation_id": "Phase62SearchBox", "class_name": "TextBox", "bounds": {"left": 110, "top": 130, "right": 430, "bottom": 170, "width": 320, "height": 40}, "enabled": True, "clickable": True, "editable": True}, {"node_id": "0.2", "name": "Run action", "role": "Button", "automation_id": "Phase62RunButton", "class_name": "Button", "bounds": {"left": 450, "top": 130, "right": 560, "bottom": 170, "width": 110, "height": 40}, "enabled": True, "clickable": True, "editable": False}]  # 新增代码+Phase62HighLevelTools: 返回扁平控件列表；如果没有这行代码，高层工具没有可解释 locator 样本。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_controls 到此结束；如果没有这个边界说明，初学者不容易看出控件样本范围。

    def _runtime(self, root: Path, sender: Phase58RecordingLowLevelSender | None = None) -> WindowsHighLevelComputerToolRuntime:  # 新增代码+Phase62HighLevelTools: 函数段开始，创建隔离的高层工具 runtime；如果没有这段函数，测试会重复拼装 locks/grants/hooks。
        lock_manager = ComputerUseLockManager(base_dir=root / "locks")  # 新增代码+Phase62HighLevelTools: 创建隔离桌面锁；如果没有这行代码，测试可能读写真正运行锁。
        grant_store = WindowsComputerUsePersistentGrantStore(base_dir=root / "grants")  # 新增代码+Phase62HighLevelTools: 创建隔离持久授权 store；如果没有这行代码，测试可能污染真实授权。
        hooks = WindowsComputerUseAbortStreamingHooks(lock_manager=lock_manager, session_id="phase62-session", base_dir=root / "hooks")  # 新增代码+Phase62HighLevelTools: 创建 abort/streaming hooks；如果没有这行代码，写动作无法验证 Phase61 集成。
        return WindowsHighLevelComputerToolRuntime(base_dir=root / "high_level", lock_manager=lock_manager, grant_store=grant_store, abort_hooks=hooks, session_id="phase62-session", low_level_sender=sender or Phase58RecordingLowLevelSender())  # 新增代码+Phase62HighLevelTools: 返回高层 runtime；如果没有这行代码，每个测试都无法复用同一安全链。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_runtime 到此结束；如果没有这个边界说明，初学者不容易看出 runtime 组装范围。

    def test_supported_operations_and_read_only_batch_do_not_take_write_lock(self) -> None:  # 新增代码+Phase62HighLevelTools: 函数段开始，验证高层操作清单和只读批量不占写锁；如果没有这个测试，只读 observe 可能阻塞桌面动作。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase62HighLevelTools: 使用临时目录隔离状态；如果没有这行代码，测试会修改真实 memory。
            root = Path(temp_dir)  # 新增代码+Phase62HighLevelTools: 保存临时根目录；如果没有这行代码，后续路径会重复转换。
            runtime = self._runtime(root)  # 新增代码+Phase62HighLevelTools: 创建高层 runtime；如果没有这行代码，测试没有被测对象。
            lock_manager = runtime.lock_manager  # 新增代码+Phase62HighLevelTools: 取出同一锁管理器；如果没有这行代码，无法检查读写锁状态。
            lock_manager.acquire("external-writer", owner_label="unit-test-writer")  # 新增代码+Phase62HighLevelTools: 模拟另一个写动作正在持锁；如果没有这行代码，无法证明只读不被写锁阻塞。
            result = runtime.run_read_only_batch([{"operation": "observe_screen", "arguments": {"window": self._safe_window(), "controls": self._controls()}}, {"operation": "find_control", "arguments": {"window": self._safe_window(), "controls": self._controls(), "query": {"automation_id": "Phase62SearchBox"}}}])  # 新增代码+Phase62HighLevelTools: 执行只读批量观察和定位；如果没有这行代码，只读并发合同没有证据。
            lock_status = lock_manager.status()  # 新增代码+Phase62HighLevelTools: 读取锁状态；如果没有这行代码，无法确认原写锁未被高层工具改写。
            lock_manager.release("external-writer")  # 新增代码+Phase62HighLevelTools: 释放模拟写锁；如果没有这行代码，临时状态会残留到后续断言。
            self.assertEqual(set(PHASE62_SUPPORTED_OPERATIONS), {"observe_screen", "find_control", "click_control", "type_into_control", "wait_for_change", "verify_screen"})  # 新增代码+Phase62HighLevelTools: 断言高层操作集合完整；如果没有这行代码，模型可调用能力可能缺项。
            self.assertTrue(result["ok"])  # 新增代码+Phase62HighLevelTools: 断言只读批量成功；如果没有这行代码，失败结果可能被误忽略。
            self.assertTrue(result["read_only_parallel"])  # 新增代码+Phase62HighLevelTools: 断言只读批量标记并发安全；如果没有这行代码，status 无法说明只读边界。
            self.assertEqual(lock_status["owner_session_id"], "external-writer")  # 新增代码+Phase62HighLevelTools: 断言只读操作没有抢走写锁；如果没有这行代码，只读污染写锁不会被发现。
            self.assertTrue(Path(result["results"][0]["artifact_path"]).exists())  # 新增代码+Phase62HighLevelTools: 断言 observe 生成 artifact；如果没有这行代码，最终 artifact 能力可能是假字段。
            self.assertTrue(any(event.get("stage") == "operation_completed" for event in runtime.progress_events()))  # 新增代码+Phase62HighLevelTools: 断言 streaming progress 已落盘；如果没有这行代码，高层工具可能没有进度事件。
    # 新增代码+Phase62HighLevelTools: 函数段结束，test_supported_operations_and_read_only_batch_do_not_take_write_lock 到此结束；如果没有这个边界说明，初学者不容易看出只读锁测试范围。

    def test_find_control_returns_uia_candidate_summary(self) -> None:  # 新增代码+Phase62HighLevelTools: 函数段开始，验证 find_control 返回可解释 UIA 候选摘要；如果没有这个测试，高层 locator 可能只返回裸控件。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase62HighLevelTools: 使用临时目录隔离 progress/artifact；如果没有这行代码，测试会污染真实路径。
            runtime = self._runtime(Path(temp_dir))  # 新增代码+Phase62HighLevelTools: 创建高层 runtime；如果没有这行代码，测试没有 locator 入口。
            result = runtime.run("find_control", {"window": self._safe_window(), "controls": self._controls(), "query": {"text": "Search", "role": "Edit"}})  # 新增代码+Phase62HighLevelTools: 执行语义控件定位；如果没有这行代码，候选摘要没有输入。
            summary = result["uia_candidate_summary"]  # 新增代码+Phase62HighLevelTools: 取出候选摘要；如果没有这行代码，断言会重复访问嵌套字段。
            self.assertTrue(result["ok"])  # 新增代码+Phase62HighLevelTools: 断言定位成功；如果没有这行代码，失败定位可能仍继续后续动作。
            self.assertTrue(summary["matched"])  # 新增代码+Phase62HighLevelTools: 断言摘要标记匹配；如果没有这行代码，模型不知道控件是否可信。
            self.assertGreaterEqual(summary["candidate_count"], 1)  # 新增代码+Phase62HighLevelTools: 断言至少有候选；如果没有这行代码，locator 可能没有解释空间。
            self.assertEqual(summary["control"]["automation_id"], "Phase62SearchBox")  # 新增代码+Phase62HighLevelTools: 断言定位到输入框；如果没有这行代码，点击和输入可能落到错误控件。
    # 新增代码+Phase62HighLevelTools: 函数段结束，test_find_control_returns_uia_candidate_summary 到此结束；如果没有这个边界说明，初学者不容易看出 locator 摘要测试范围。

    def test_write_actions_use_grants_abort_hooks_and_serial_lock(self) -> None:  # 新增代码+Phase62HighLevelTools: 函数段开始，验证写动作走授权、abort-aware sender 和串行锁；如果没有这个测试，高层 click/type 可能绕过底层安全链。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase62HighLevelTools: 使用临时目录隔离锁和授权；如果没有这行代码，测试会污染真实状态。
            root = Path(temp_dir)  # 新增代码+Phase62HighLevelTools: 保存临时根目录；如果没有这行代码，后续路径难以复用。
            sender = Phase58RecordingLowLevelSender()  # 新增代码+Phase62HighLevelTools: 创建记录型 sender；如果没有这行代码，测试可能触碰真实鼠标键盘。
            runtime = self._runtime(root, sender=sender)  # 新增代码+Phase62HighLevelTools: 创建带记录 sender 的 runtime；如果没有这行代码，无法检查低层事件。
            runtime.grant_store.approve(session_id="phase62-session", app="phase58_safe_app", action_scope=["click", "type_text"], ttl_seconds=60, reason="unit", grant_flags={"desktopAction": True})  # 新增代码+Phase62HighLevelTools: 写入点击和输入授权；如果没有这行代码，写动作应该被默认拒绝。
            click_result = runtime.run("click_control", {"window": self._safe_window(), "controls": self._controls(), "query": {"automation_id": "Phase62RunButton"}})  # 新增代码+Phase62HighLevelTools: 执行高层点击；如果没有这行代码，授权和写锁链路没有正例。
            runtime.lock_manager.acquire("other-session", owner_label="unit-lock")  # 新增代码+Phase62HighLevelTools: 模拟其他写动作持锁；如果没有这行代码，串行拒绝路径没有样本。
            blocked_result = runtime.run("type_into_control", {"window": self._safe_window(), "controls": self._controls(), "query": {"automation_id": "Phase62SearchBox"}, "text": "phase62 secret text"})  # 新增代码+Phase62HighLevelTools: 尝试在锁被占用时输入；如果没有这行代码，写动作并发污染无法暴露。
            runtime.lock_manager.release("other-session")  # 新增代码+Phase62HighLevelTools: 清理模拟锁；如果没有这行代码，后续测试可能被锁阻塞。
            self.assertTrue(click_result["ok"])  # 新增代码+Phase62HighLevelTools: 断言点击成功；如果没有这行代码，后续低层事件断言没有意义。
            self.assertTrue(click_result["grant_allowed"])  # 新增代码+Phase62HighLevelTools: 断言来自持久授权放行；如果没有这行代码，写动作可能绕过审批。
            self.assertTrue(click_result["write_lock_acquired"])  # 新增代码+Phase62HighLevelTools: 断言写动作获取了锁；如果没有这行代码，写动作可能并发污染桌面。
            self.assertGreater(click_result["low_level_event_count"], 0)  # 新增代码+Phase62HighLevelTools: 断言低层事件发生在记录 sender；如果没有这行代码，高层工具可能只返回文案。
            self.assertGreater(len(sender.low_level_events), 0)  # 新增代码+Phase62HighLevelTools: 直接检查原始记录 sender；如果没有这行代码，结果字段可能撒谎。
            self.assertFalse(blocked_result["ok"])  # 新增代码+Phase62HighLevelTools: 断言锁占用时写动作失败；如果没有这行代码，多个 agent 可能同时控制桌面。
            self.assertEqual(blocked_result["decision"], "write_lock_busy")  # 新增代码+Phase62HighLevelTools: 断言串行拒绝原因稳定；如果没有这行代码，用户不知道为什么动作未执行。
            self.assertEqual(blocked_result["low_level_event_count"], 0)  # 新增代码+Phase62HighLevelTools: 断言锁冲突时 0 事件；如果没有这行代码，拒绝路径也可能发出副作用。
            self.assertTrue(any(event.get("stage") == "write_lock_acquired" for event in runtime.progress_events()))  # 新增代码+Phase62HighLevelTools: 断言锁获取进入 progress；如果没有这行代码，终端看不到写动作生命周期。
            self.assertTrue(any(event.get("stage") == "write_lock_released" for event in runtime.progress_events()))  # 新增代码+Phase62HighLevelTools: 断言锁释放进入 progress；如果没有这行代码，长任务无法复盘锁是否清理。
    # 新增代码+Phase62HighLevelTools: 函数段结束，test_write_actions_use_grants_abort_hooks_and_serial_lock 到此结束；如果没有这个边界说明，初学者不容易看出写动作安全链测试范围。

    def test_abort_before_write_sends_zero_low_level_events(self) -> None:  # 新增代码+Phase62HighLevelTools: 函数段开始，验证 abort 后高层写动作发送 0 个低层事件；如果没有这个测试，急停可能只保护 Phase58 直接入口。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase62HighLevelTools: 使用临时目录隔离 abort 状态；如果没有这行代码，测试会触发真实 abort flag。
            root = Path(temp_dir)  # 新增代码+Phase62HighLevelTools: 保存临时根目录；如果没有这行代码，路径无法复用。
            sender = Phase58RecordingLowLevelSender()  # 新增代码+Phase62HighLevelTools: 创建记录型 sender；如果没有这行代码，无法证明原始 sender 没收到事件。
            runtime = self._runtime(root, sender=sender)  # 新增代码+Phase62HighLevelTools: 创建高层 runtime；如果没有这行代码，测试没有被测对象。
            runtime.grant_store.approve(session_id="phase62-session", app="phase58_safe_app", action_scope=["click"], ttl_seconds=60, reason="unit", grant_flags={"desktopAction": True})  # 新增代码+Phase62HighLevelTools: 写入点击授权；如果没有这行代码，失败可能来自未授权而不是 abort。
            runtime.lock_manager.request_abort("phase62 abort", requested_by="unit-test")  # 新增代码+Phase62HighLevelTools: 触发 durable abort；如果没有这行代码，高层写动作不会走零事件急停路径。
            result = runtime.run("click_control", {"window": self._safe_window(), "controls": self._controls(), "query": {"automation_id": "Phase62RunButton"}})  # 新增代码+Phase62HighLevelTools: 执行高层点击；如果没有这行代码，abort wrapper 没有动作样本。
            self.assertFalse(result["ok"])  # 新增代码+Phase62HighLevelTools: 断言 abort 后动作失败；如果没有这行代码，急停可能被误报成功。
            self.assertEqual(result["low_level_event_count"], 0)  # 新增代码+Phase62HighLevelTools: 断言低层发送为 0；如果没有这行代码，急停安全性无法确认。
            self.assertEqual(sender.low_level_events, [])  # 新增代码+Phase62HighLevelTools: 断言原始 sender 未收到事件；如果没有这行代码，结果字段可能不可信。
            self.assertEqual(result["dispatch"]["decision"], "aborted_before_low_level_send")  # 新增代码+Phase62HighLevelTools: 断言拒绝来自 Phase61 abort-aware sender；如果没有这行代码，无法证明 hooks 被接入高层 API。
    # 新增代码+Phase62HighLevelTools: 函数段结束，test_abort_before_write_sends_zero_low_level_events 到此结束；如果没有这个边界说明，初学者不容易看出 abort 零事件测试范围。

    def test_phase62_cli_terminal_status_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase62HighLevelTools: 函数段开始，验证 CLI、终端状态和真实验收场景 token 稳定；如果没有这个测试，真实终端验收可能漏检高层工具。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase62HighLevelTools: 使用临时目录隔离合同状态；如果没有这行代码，自检会污染真实 memory。
            report = run_phase62_high_level_tools_contract(base_dir=Path(temp_dir) / "contract")  # 新增代码+Phase62HighLevelTools: 运行 Phase62 合同自检；如果没有这行代码，CLI token 没有结构化来源。
            output = run_computer_terminal_command(Path(temp_dir), "/computer high-level-tools")  # 新增代码+Phase62HighLevelTools: 通过真实终端命令查看高层工具状态；如果没有这行代码，用户入口不可见。
        cli_line = phase62_cli_line(report)  # 新增代码+Phase62HighLevelTools: 生成稳定 CLI token 行；如果没有这行代码，场景匹配无法验证。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase62_high_level_tools.json")  # 新增代码+Phase62HighLevelTools: 定位 Phase62 真实终端场景；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase62HighLevelTools: 读取场景文本；如果没有这行代码，token 漏配无法检测。
        expected_tokens = {PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_OK_TOKEN, "high_level_ops=true", "read_only_parallel=true", "write_serial=true", "streaming_progress=true", "image_artifact=true", "uia_candidates=true", "abort_zero_events=true", "actions_expanded=false"}  # 新增代码+Phase62HighLevelTools: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        self.assertIn("Computer High-Level Tools", output)  # 新增代码+Phase62HighLevelTools: 断言终端状态标题可见；如果没有这行代码，用户无法发现高层工具入口。
        self.assertIn(PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, output)  # 新增代码+Phase62HighLevelTools: 断言终端输出 marker；如果没有这行代码，验收器无法稳定匹配。
        for token in expected_tokens:  # 新增代码+Phase62HighLevelTools: 遍历关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase62HighLevelTools: 断言 CLI 包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase62HighLevelTools: 断言场景包含 token；如果没有这行代码，真实终端验收可能漏检。
    # 新增代码+Phase62HighLevelTools: 函数段结束，test_phase62_cli_terminal_status_and_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景测试范围。
# 新增代码+Phase62HighLevelTools: 类段结束，WindowsComputerUseHighLevelToolsPhase62Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase62HighLevelTools: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase62HighLevelTools: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
