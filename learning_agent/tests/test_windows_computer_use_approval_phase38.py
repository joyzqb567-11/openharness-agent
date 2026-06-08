import json  # 新增代码+Phase38WindowsComputerApproval: 导入 JSON 工具用于检查 CLI 合同输出和场景 token；如果没有这行代码，测试无法稳定验证验收文本。
import tempfile  # 新增代码+Phase38WindowsComputerApproval: 导入临时目录工具隔离 lock 文件；如果没有这行代码，测试可能污染真实 Computer Use 锁目录。
import unittest  # 新增代码+Phase38WindowsComputerApproval: 导入 unittest 框架承载 Phase38 自动化测试；如果没有这行代码，测试文件不会被标准测试命令执行。
from pathlib import Path  # 新增代码+Phase38WindowsComputerApproval: 导入 Path 用于定位项目场景文件和临时路径；如果没有这行代码，路径拼接会变得脆弱。
from learning_agent.computer_use.approval import PHASE38_WINDOWS_COMPUTER_APPROVAL_MARKER, PHASE38_WINDOWS_COMPUTER_APPROVAL_OK_TOKEN, WindowsComputerUseApprovalModel, phase38_cli_line, run_phase38_approval_contract  # 新增代码+Phase38WindowsComputerApproval: 导入预期新增的 approval 模块入口；如果没有这行代码，红灯会证明 Phase38 尚未实现。
from learning_agent.computer_use.controller import ComputerUseController, MemoryComputerUseBackend  # 新增代码+Phase38WindowsComputerApproval: 导入控制器和内存后端用于验证审批模型接入链路；如果没有这行代码，测试只能覆盖孤立 approval 模块。
from learning_agent.computer_use.lock import ComputerUseLockManager  # 新增代码+Phase38WindowsComputerApproval: 导入桌面锁管理器用于通过 Phase30 安全门；如果没有这行代码，controller 测试会提前失败在缺锁门禁。
from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase38WindowsComputerApproval: 导入真实终端 `/computer` 命令入口用于验证 approval 状态可见；如果没有这行代码，Phase38 只会改底层模型而不会让用户在终端看到状态。


class WindowsComputerUseApprovalPhase38Tests(unittest.TestCase):  # 新增代码+Phase38WindowsComputerApproval: 定义 Phase38 审批模型测试集合；如果没有这个类，unittest 不会组织这些审批行为测试。
    def _safe_window(self) -> dict[str, object]:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，提供安全 Notepad 窗口样本；如果没有这段函数，每个测试都要重复构造可信窗口。
        return {"app_id": "notepad.exe", "window_id": "hwnd:3801", "title_preview": "Phase38 Notepad", "process_name": "notepad.exe", "rect": {"left": 20, "top": 30, "right": 420, "bottom": 260}}  # 新增代码+Phase38WindowsComputerApproval: 返回带身份和矩形的安全窗口；如果没有这行代码，审批和 controller 都没有正常目标。
    # 新增代码+Phase38WindowsComputerApproval: 函数段结束，_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出样本 helper 范围。

    def _forbidden_window(self) -> dict[str, object]:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，提供高风险终端窗口样本；如果没有这段函数，禁止目标测试缺少稳定输入。
        return {"app_id": "powershell.exe", "window_id": "hwnd:3802", "title_preview": "Administrator: Windows PowerShell", "process_name": "powershell.exe", "rect": {"left": 40, "top": 50, "right": 500, "bottom": 280}}  # 新增代码+Phase38WindowsComputerApproval: 返回终端类窗口；如果没有这行代码，审批模型无法证明会拦截 shell 目标。
    # 新增代码+Phase38WindowsComputerApproval: 函数段结束，_forbidden_window 到此结束；如果没有这个边界说明，读者不容易分清安全样本和禁止样本。

    def test_approval_model_blocks_forbidden_terminal_targets(self) -> None:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，验证终端类目标会被审批模型拒绝；如果没有这个测试，高风险 shell 窗口可能被误放行。
        model = WindowsComputerUseApprovalModel()  # 新增代码+Phase38WindowsComputerApproval: 创建默认审批模型；如果没有这行代码，无法验证默认安全策略。
        decision = model.evaluate("click", {"window": self._forbidden_window()})  # 新增代码+Phase38WindowsComputerApproval: 对终端窗口点击做审批评估；如果没有这行代码，禁止目标规则不会被触发。
        self.assertFalse(decision["allowed"])  # 新增代码+Phase38WindowsComputerApproval: 断言审批拒绝终端窗口；如果没有这行代码，测试无法发现误放行。
        self.assertEqual(decision["decision"], "denied_forbidden_target")  # 新增代码+Phase38WindowsComputerApproval: 断言拒绝原因稳定；如果没有这行代码，后续状态 UI 难以解释拒绝。
        self.assertEqual(decision["sentinel_category"], "shell")  # 新增代码+Phase38WindowsComputerApproval: 断言终端目标被归类为 shell；如果没有这行代码，风险分类可能丢失。
        self.assertIn("PowerShell", decision["target_summary"]["title_preview"])  # 新增代码+Phase38WindowsComputerApproval: 断言目标摘要保留可读标题预览；如果没有这行代码，用户不知道被拒绝的是哪个窗口。
    # 新增代码+Phase38WindowsComputerApproval: 函数段结束，test_approval_model_blocks_forbidden_terminal_targets 到此结束；如果没有这个边界说明，读者不容易看出禁止目标测试范围。

    def test_session_grant_allows_safe_app_and_reports_terminal_status(self) -> None:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，验证会话 grant 可允许安全 app；如果没有这个测试，approval 只能拒绝不能授权。
        model = WindowsComputerUseApprovalModel()  # 新增代码+Phase38WindowsComputerApproval: 创建审批模型；如果没有这行代码，无法授予会话权限。
        grant = model.grant_for_session([self._safe_window()], {"systemKeyCombos": False}, reason="unit-test-safe-app")  # 新增代码+Phase38WindowsComputerApproval: 给安全窗口所在 app 创建会话授权；如果没有这行代码，安全 app 仍会被缺授权拒绝。
        decision = model.evaluate("click", {"window": self._safe_window()})  # 新增代码+Phase38WindowsComputerApproval: 对安全 app 点击做审批评估；如果没有这行代码，无法证明 grant 生效。
        status_text = "\n".join(model.terminal_status_lines())  # 新增代码+Phase38WindowsComputerApproval: 生成终端状态摘要文本；如果没有这行代码，无法验证类似 ClaudeCode 的审批状态提示。
        self.assertTrue(decision["allowed"])  # 新增代码+Phase38WindowsComputerApproval: 断言已授权安全 app 被允许；如果没有这行代码，grant 可能没有生效。
        self.assertEqual(decision["decision"], "allowed_by_session_grant")  # 新增代码+Phase38WindowsComputerApproval: 断言允许原因稳定；如果没有这行代码，审计无法区分自动允许和会话授权。
        self.assertEqual(decision["grant_id"], grant["grant_id"])  # 新增代码+Phase38WindowsComputerApproval: 断言动作和会话 grant 关联；如果没有这行代码，事后无法追踪授权来源。
        self.assertIn("approval_granted_app_count=1", status_text)  # 新增代码+Phase38WindowsComputerApproval: 断言终端状态显示授权 app 数；如果没有这行代码，用户看不到当前授权范围。
    # 新增代码+Phase38WindowsComputerApproval: 函数段结束，test_session_grant_allows_safe_app_and_reports_terminal_status 到此结束；如果没有这个边界说明，读者不容易看出授权测试范围。

    def test_grant_flags_block_system_key_combos_until_explicitly_enabled(self) -> None:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，验证危险快捷键 flag 需要显式授权；如果没有这个测试，系统级组合键可能被误放行。
        model = WindowsComputerUseApprovalModel()  # 新增代码+Phase38WindowsComputerApproval: 创建审批模型；如果没有这行代码，无法测试 flags。
        model.grant_for_session([self._safe_window()], {"systemKeyCombos": False}, reason="no-system-keys")  # 新增代码+Phase38WindowsComputerApproval: 授权安全 app 但不授权系统组合键；如果没有这行代码，缺 flag 场景无法建立。
        denied = model.evaluate("press_key", {"window": self._safe_window(), "key": "ctrl+alt+delete"})  # 新增代码+Phase38WindowsComputerApproval: 评估危险系统组合键；如果没有这行代码，flag 门禁不会被触发。
        model.grant_for_session([self._safe_window()], {"systemKeyCombos": True}, reason="system-keys-ok")  # 新增代码+Phase38WindowsComputerApproval: 显式授权系统组合键；如果没有这行代码，无法验证 flag 放行路径。
        allowed = model.evaluate("press_key", {"window": self._safe_window(), "key": "ctrl+alt+delete"})  # 新增代码+Phase38WindowsComputerApproval: 再次评估同一组合键；如果没有这行代码，无法证明显式 flag 生效。
        self.assertFalse(denied["allowed"])  # 新增代码+Phase38WindowsComputerApproval: 断言缺 flag 时拒绝；如果没有这行代码，危险键可能被误允许。
        self.assertEqual(denied["decision"], "missing_grant_flags")  # 新增代码+Phase38WindowsComputerApproval: 断言拒绝原因是缺 grant flag；如果没有这行代码，错误原因可能不清楚。
        self.assertTrue(allowed["allowed"])  # 新增代码+Phase38WindowsComputerApproval: 断言显式授权后允许；如果没有这行代码，用户授权也无法生效。
        self.assertIn("systemKeyCombos", allowed["grant_flags"])  # 新增代码+Phase38WindowsComputerApproval: 断言结果暴露已授权 flag；如果没有这行代码，审计看不到危险权限来源。
    # 新增代码+Phase38WindowsComputerApproval: 函数段结束，test_grant_flags_block_system_key_combos_until_explicitly_enabled 到此结束；如果没有这个边界说明，读者不容易看出 flag 测试范围。

    def test_controller_rejects_unapproved_window_before_backend_execute(self) -> None:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，验证 controller 会在后端执行前调用 approval；如果没有这个测试，approval 可能只是孤立模块。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase38WindowsComputerApproval: 创建临时目录隔离锁状态；如果没有这行代码，测试会污染真实锁文件。
            forbidden_window = self._forbidden_window()  # 新增代码+Phase38WindowsComputerApproval: 准备终端类禁止窗口；如果没有这行代码，后端没有目标窗口。
            backend = MemoryComputerUseBackend(windows=[forbidden_window])  # 新增代码+Phase38WindowsComputerApproval: 创建内存后端并登记该窗口；如果没有这行代码，动作会提前失败在未知窗口而不是 approval。
            lock_manager = ComputerUseLockManager(base_dir=Path(temp_dir))  # 新增代码+Phase38WindowsComputerApproval: 创建测试锁管理器；如果没有这行代码，动作会因缺锁提前失败。
            lock_manager.acquire("phase38-session", owner_label="unit-test")  # 新增代码+Phase38WindowsComputerApproval: 让当前会话持锁；如果没有这行代码，approval 拒绝路径无法被执行到。
            controller = ComputerUseController(backend=backend, lock_manager=lock_manager, owner_session_id="phase38-session", approval_model=WindowsComputerUseApprovalModel())  # 新增代码+Phase38WindowsComputerApproval: 注入审批模型到控制器；如果没有这行代码，controller 不会执行 Phase38 审批。
            result = controller.execute({"action": "click", "confirm_desktop_control": True, "window": forbidden_window, "x": 6, "y": 9})  # 新增代码+Phase38WindowsComputerApproval: 尝试点击终端窗口；如果没有这行代码，审批拒绝链路没有行为证据。
            self.assertFalse(result.ok)  # 新增代码+Phase38WindowsComputerApproval: 断言动作被拒绝；如果没有这行代码，测试无法发现误执行。
            self.assertEqual(backend.actions, [])  # 新增代码+Phase38WindowsComputerApproval: 断言后端没有收到动作；如果没有这行代码，表面拒绝但实际执行不会被发现。
            self.assertEqual(result.data["approval"]["decision"], "denied_forbidden_target")  # 新增代码+Phase38WindowsComputerApproval: 断言拒绝来自 approval；如果没有这行代码，controller 可能走错拒绝路径。
    # 新增代码+Phase38WindowsComputerApproval: 函数段结束，test_controller_rejects_unapproved_window_before_backend_execute 到此结束；如果没有这个边界说明，读者不容易看出 controller 接入测试范围。

    def test_phase38_cli_contract_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，验证 CLI 合同和真实终端场景 token；如果没有这个测试，验收脚本可能缺关键断言。
        report = run_phase38_approval_contract()  # 新增代码+Phase38WindowsComputerApproval: 运行 Phase38 合同自检；如果没有这行代码，CLI token 没有报告来源。
        line = phase38_cli_line(report)  # 新增代码+Phase38WindowsComputerApproval: 生成稳定 CLI 单行；如果没有这行代码，场景很难解析完整 JSON。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase38WindowsComputerApproval: 定位项目根目录；如果没有这行代码，场景文件路径不稳定。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase38_windows_computer_approval.json"  # 新增代码+Phase38WindowsComputerApproval: 定位 Phase38 真实终端场景；如果没有这行代码，测试可能检查错文件。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase38WindowsComputerApproval: 读取并解析场景 JSON；如果没有这行代码，场景格式错误不会被发现。
        expected_tokens = {PHASE38_WINDOWS_COMPUTER_APPROVAL_MARKER, PHASE38_WINDOWS_COMPUTER_APPROVAL_OK_TOKEN, "allowlist=true", "forbidden_blocked=true", "grant_flags=true", "terminal_status=true", "actions_expanded=false"}  # 新增代码+Phase38WindowsComputerApproval: 列出 Phase38 必须暴露的验收 token；如果没有这行代码，测试会遗漏成功标准。
        self.assertIn(PHASE38_WINDOWS_COMPUTER_APPROVAL_MARKER, line)  # 新增代码+Phase38WindowsComputerApproval: 断言 CLI 行包含阶段 marker；如果没有这行代码，最终回答可能无法匹配阶段。
        self.assertTrue(report["allowlist"])  # 新增代码+Phase38WindowsComputerApproval: 断言 allowlist 合同成立；如果没有这行代码，报告可能没有授权能力。
        self.assertTrue(report["forbidden_blocked"])  # 新增代码+Phase38WindowsComputerApproval: 断言禁止目标被拦截；如果没有这行代码，shell 目标风险可能漏检。
        self.assertTrue(report["grant_flags"])  # 新增代码+Phase38WindowsComputerApproval: 断言 grant flags 门禁成立；如果没有这行代码，危险 flag 可能不可见。
        for token in expected_tokens:  # 新增代码+Phase38WindowsComputerApproval: 遍历所有应出现在场景里的 token；如果没有这行代码，场景断言可能漏项。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase38WindowsComputerApproval: 断言 debug log 检查包含 token；如果没有这行代码，工具输出证据可能没有被 verifier 复核。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase38WindowsComputerApproval: 断言最终回答检查包含 token；如果没有这行代码，用户可见回答可能漏掉关键证据。
    # 新增代码+Phase38WindowsComputerApproval: 函数段结束，test_phase38_cli_contract_and_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，读者不容易看出 CLI/场景测试范围。

    def test_computer_terminal_status_includes_phase38_approval_summary(self) -> None:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，验证 `/computer status` 会显示 approval 摘要；如果没有这个测试，真实终端 UI 可能看不到 Phase38 新能力。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase38WindowsComputerApproval: 使用临时目录隔离锁文件；如果没有这行代码，测试可能读写真实 workspace 的 Computer Use 状态。
            output = run_computer_terminal_command(Path(temp_dir), "/computer status")  # 新增代码+Phase38WindowsComputerApproval: 执行真实终端命令渲染逻辑；如果没有这行代码，无法证明 `/computer` 状态入口包含 approval。
        self.assertIn("approval_model=phase38_windows_computer_approval", output)  # 新增代码+Phase38WindowsComputerApproval: 断言终端状态暴露 approval 模型名；如果没有这行代码，用户可能不知道当前审批模型是什么。
        self.assertIn("actions_expanded=false", output)  # 新增代码+Phase38WindowsComputerApproval: 断言终端状态说明动作面没有扩张；如果没有这行代码，Phase38 可能被误解为放大了真实控制范围。
    # 新增代码+Phase38WindowsComputerApproval: 函数段结束，test_computer_terminal_status_includes_phase38_approval_summary 到此结束；如果没有这个边界说明，读者不容易看出终端状态测试范围。


if __name__ == "__main__":  # 新增代码+Phase38WindowsComputerApproval: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式单独验证 Phase38。
    unittest.main()  # 新增代码+Phase38WindowsComputerApproval: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行任何测试。
