import tempfile  # 新增代码+Phase60PersistentGrants: 导入临时目录隔离持久 grant 状态；如果没有这行代码，测试会污染真实用户授权。
import unittest  # 新增代码+Phase60PersistentGrants: 导入 unittest 承载 Phase60 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase60PersistentGrants: 导入 Path 用于临时路径和场景文件；如果没有这行代码，Windows 路径拼接更脆弱。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase60PersistentGrants: 导入真实终端 /computer 命令入口；如果没有这行代码，测试无法证明 approve/grants/revoke 可见。
from learning_agent.computer_use.persistent_grants import PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, PHASE60_WINDOWS_PERSISTENT_GRANTS_OK_TOKEN, WindowsComputerUsePersistentGrantStore, phase60_cli_line, run_phase60_persistent_grants_contract  # 新增代码+Phase60PersistentGrants: 导入预期 Phase60 持久授权入口；如果没有这行代码，红灯会证明生产模块尚未实现。


class WindowsComputerUsePersistentGrantsPhase60Tests(unittest.TestCase):  # 新增代码+Phase60PersistentGrants: 类段开始，集中验证持久授权、过期、撤销和高风险默认拒绝；如果没有这个类，Phase60 没有自动化门禁。
    def _safe_window(self) -> dict[str, object]:  # 新增代码+Phase60PersistentGrants: 函数段开始，提供安全窗口样本；如果没有这段函数，每个测试都要重复构造目标窗口。
        return {"app_id": "notepad.exe", "process_name": "notepad.exe", "window_id": "hwnd:6001", "title_preview": "Phase60 Notepad", "display_id": "DISPLAY1"}  # 新增代码+Phase60PersistentGrants: 返回带 app/window/display 的安全目标；如果没有这行代码，grant 评估缺少目标字段。
    # 新增代码+Phase60PersistentGrants: 函数段结束，_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出安全样本范围。

    def test_approve_allows_matching_app_window_display_and_scope(self) -> None:  # 新增代码+Phase60PersistentGrants: 函数段开始，验证完整作用域 grant 能放行匹配动作；如果没有这个测试，approve 可能只写文件不参与评估。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase60PersistentGrants: 使用临时目录隔离状态；如果没有这行代码，测试会修改真实 grants。
            store = WindowsComputerUsePersistentGrantStore(base_dir=Path(temp_dir))  # 新增代码+Phase60PersistentGrants: 创建持久 grant store；如果没有这行代码，无法记录授权。
            approval = store.approve(session_id="phase60", app="notepad.exe", window_id="hwnd:6001", display_id="DISPLAY1", action_scope=["click", "type_text"], ttl_seconds=60, reason="unit test", grant_flags={"desktopAction": True})  # 新增代码+Phase60PersistentGrants: 写入带 app/window/display/action_scope/ttl/reason 的授权；如果没有这行代码，评估没有正例。
            decision = store.evaluate(session_id="phase60", action="click", arguments={"window": self._safe_window()})  # 新增代码+Phase60PersistentGrants: 评估匹配授权的点击动作；如果没有这行代码，无法证明授权会生效。
            self.assertTrue(approval["approved"])  # 新增代码+Phase60PersistentGrants: 断言授权写入成功；如果没有这行代码，失败授权也可能继续参与评估。
            self.assertTrue(decision["allowed"])  # 新增代码+Phase60PersistentGrants: 断言匹配动作被允许；如果没有这行代码，approve 可能没有接入 evaluate。
            self.assertEqual(decision["decision"], "allowed_by_persistent_grant")  # 新增代码+Phase60PersistentGrants: 断言允许原因稳定；如果没有这行代码，审计无法区分授权来源。
            self.assertEqual(decision["grant_id"], approval["grant_id"])  # 新增代码+Phase60PersistentGrants: 断言动作和授权 id 关联；如果没有这行代码，事后无法追溯。
    # 新增代码+Phase60PersistentGrants: 函数段结束，test_approve_allows_matching_app_window_display_and_scope 到此结束；如果没有这个边界说明，初学者不容易看出 approve 正例范围。

    def test_unauthorized_expired_and_revoked_grants_are_denied(self) -> None:  # 新增代码+Phase60PersistentGrants: 函数段开始，验证未授权、过期和撤销都拒绝；如果没有这个测试，持久授权可能无法收回。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase60PersistentGrants: 使用临时目录隔离状态；如果没有这行代码，测试会修改真实 grants。
            store = WindowsComputerUsePersistentGrantStore(base_dir=Path(temp_dir))  # 新增代码+Phase60PersistentGrants: 创建持久 grant store；如果没有这行代码，无法记录和评估授权。
            unauthorized = store.evaluate(session_id="phase60", action="click", arguments={"window": self._safe_window()})  # 新增代码+Phase60PersistentGrants: 未授权时直接评估；如果没有这行代码，requires_approval 路径没有证据。
            expired_grant = store.approve(session_id="phase60", app="notepad.exe", action_scope=["click"], ttl_seconds=-1, reason="expired", grant_flags={"desktopAction": True})  # 新增代码+Phase60PersistentGrants: 写入已过期授权；如果没有这行代码，过期拒绝没有样本。
            expired = store.evaluate(session_id="phase60", action="click", arguments={"window": self._safe_window()})  # 新增代码+Phase60PersistentGrants: 评估已过期授权；如果没有这行代码，过期逻辑不会运行。
            live_grant = store.approve(session_id="phase60", app="notepad.exe", action_scope=["type_text"], ttl_seconds=60, reason="revoke", grant_flags={"desktopAction": True})  # 新增代码+Phase60PersistentGrants: 写入可撤销授权；如果没有这行代码，revoke 没有目标。
            revoke = store.revoke(session_id="phase60", grant_id=live_grant["grant_id"], reason="unit revoke")  # 新增代码+Phase60PersistentGrants: 撤销授权；如果没有这行代码，撤销路径没有动作。
            revoked = store.evaluate(session_id="phase60", action="type_text", arguments={"window": self._safe_window()})  # 新增代码+Phase60PersistentGrants: 评估撤销后的动作；如果没有这行代码，revoke 后拒绝无法证明。
            self.assertFalse(unauthorized["allowed"])  # 新增代码+Phase60PersistentGrants: 断言未授权拒绝；如果没有这行代码，默认放行风险不会被发现。
            self.assertEqual(unauthorized["decision"], "requires_approval")  # 新增代码+Phase60PersistentGrants: 断言未授权原因稳定；如果没有这行代码，用户无法知道要 approve。
            self.assertFalse(expired["allowed"])  # 新增代码+Phase60PersistentGrants: 断言过期授权拒绝；如果没有这行代码，TTL 可能不生效。
            self.assertEqual(expired["decision"], "grant_expired")  # 新增代码+Phase60PersistentGrants: 断言过期原因稳定；如果没有这行代码，状态 UI 无法解释过期。
            self.assertTrue(revoke["revoked"])  # 新增代码+Phase60PersistentGrants: 断言撤销动作成功；如果没有这行代码，后续拒绝可能来自其他原因。
            self.assertFalse(revoked["allowed"])  # 新增代码+Phase60PersistentGrants: 断言撤销后拒绝；如果没有这行代码，revoke 后仍可操作不会暴露。
            self.assertEqual(revoked["decision"], "grant_revoked")  # 新增代码+Phase60PersistentGrants: 断言撤销原因稳定；如果没有这行代码，审计无法区分未授权和已撤销。
            self.assertEqual(expired["grant_id"], expired_grant["grant_id"])  # 新增代码+Phase60PersistentGrants: 断言过期拒绝关联原授权；如果没有这行代码，用户无法定位哪个 grant 过期。
    # 新增代码+Phase60PersistentGrants: 函数段结束，test_unauthorized_expired_and_revoked_grants_are_denied 到此结束；如果没有这个边界说明，初学者不容易看出拒绝路径范围。

    def test_high_risk_grants_require_explicit_flags(self) -> None:  # 新增代码+Phase60PersistentGrants: 函数段开始，验证剪贴板和系统键默认拒绝；如果没有这个测试，高风险权限可能被普通 approve 放行。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase60PersistentGrants: 使用临时目录隔离状态；如果没有这行代码，测试会修改真实 grants。
            store = WindowsComputerUsePersistentGrantStore(base_dir=Path(temp_dir))  # 新增代码+Phase60PersistentGrants: 创建持久 grant store；如果没有这行代码，无法测试高风险授权。
            denied = store.approve(session_id="phase60", app="notepad.exe", action_scope=["press_key"], ttl_seconds=60, reason="danger", grant_flags={"desktopAction": True})  # 新增代码+Phase60PersistentGrants: 尝试未显式 systemKeyCombos 的系统键授权；如果没有这行代码，高风险默认拒绝没有输入。
            allowed = store.approve(session_id="phase60", app="notepad.exe", action_scope=["press_key"], ttl_seconds=60, reason="explicit", grant_flags={"desktopAction": True, "systemKeyCombos": True})  # 新增代码+Phase60PersistentGrants: 显式授权系统键；如果没有这行代码，高风险显式开启路径没有证据。
            self.assertFalse(denied["approved"])  # 新增代码+Phase60PersistentGrants: 断言默认拒绝高风险授权；如果没有这行代码，危险 grant 可能写入。
            self.assertEqual(denied["decision"], "high_risk_requires_explicit_grant")  # 新增代码+Phase60PersistentGrants: 断言拒绝原因稳定；如果没有这行代码，用户不知道为什么不能 approve。
            self.assertIn("systemKeyCombos", denied["missing_grant_flags"])  # 新增代码+Phase60PersistentGrants: 断言缺少系统键 flag；如果没有这行代码，用户不知道要显式开启哪项。
            self.assertTrue(allowed["approved"])  # 新增代码+Phase60PersistentGrants: 断言显式授权后允许写入；如果没有这行代码，高风险永远无法被用户明确批准。
    # 新增代码+Phase60PersistentGrants: 函数段结束，test_high_risk_grants_require_explicit_flags 到此结束；如果没有这个边界说明，初学者不容易看出高风险 grant 范围。

    def test_terminal_commands_and_cli_tokens_are_stable(self) -> None:  # 新增代码+Phase60PersistentGrants: 函数段开始，验证终端命令、CLI 和场景 token；如果没有这个测试，真实用户可能看不懂当前授权状态。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase60PersistentGrants: 使用临时目录隔离终端命令状态；如果没有这行代码，测试会读写真实 workspace grants。
            approve_output = run_computer_terminal_command(Path(temp_dir), "/computer approve notepad.exe desktopAction ttl=60 scope=click reason=unit")  # 新增代码+Phase60PersistentGrants: 运行真实终端 approve 命令；如果没有这行代码，approve UX 无法被测试。
            grants_output = run_computer_terminal_command(Path(temp_dir), "/computer grants")  # 新增代码+Phase60PersistentGrants: 运行真实终端 grants 命令；如果没有这行代码，用户可读状态无法被测试。
            revoke_output = run_computer_terminal_command(Path(temp_dir), "/computer revoke notepad.exe")  # 新增代码+Phase60PersistentGrants: 运行真实终端 revoke 命令；如果没有这行代码，撤销 UX 无法被测试。
            report = run_phase60_persistent_grants_contract(base_dir=Path(temp_dir) / "learning_agent" / "memory" / "computer_use" / "persistent_grants_contract")  # 新增代码+Phase60PersistentGrants: 运行隔离合同自检；如果没有这行代码，CLI token 没有报告来源。
        cli_line = phase60_cli_line(report)  # 新增代码+Phase60PersistentGrants: 生成稳定 CLI token 行；如果没有这行代码，场景匹配无法验证。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase60_persistent_grants.json")  # 新增代码+Phase60PersistentGrants: 定位 Phase60 真实终端场景；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase60PersistentGrants: 读取场景文本；如果没有这行代码，token 漏配无法检测。
        expected_tokens = {PHASE60_WINDOWS_PERSISTENT_GRANTS_MARKER, PHASE60_WINDOWS_PERSISTENT_GRANTS_OK_TOKEN, "approve=true", "unauthorized_denied=true", "expired_denied=true", "revoked_denied=true", "high_risk_default=true", "terminal_status=true", "actions_expanded=false"}  # 新增代码+Phase60PersistentGrants: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        self.assertIn("approve_recorded=true", approve_output)  # 新增代码+Phase60PersistentGrants: 断言终端 approve 成功可见；如果没有这行代码，用户不知道授权是否记录。
        self.assertIn("Computer Persistent Grants", grants_output)  # 新增代码+Phase60PersistentGrants: 断言 grants 面板可见；如果没有这行代码，当前授权状态不可读。
        self.assertIn("revoked=true", revoke_output)  # 新增代码+Phase60PersistentGrants: 断言终端 revoke 成功可见；如果没有这行代码，用户不知道撤销是否生效。
        for token in expected_tokens:  # 新增代码+Phase60PersistentGrants: 遍历稳定 token；如果没有这行代码，断言会重复且易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase60PersistentGrants: 断言 CLI 包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase60PersistentGrants: 断言场景包含 token；如果没有这行代码，真实终端验收可能漏检。
    # 新增代码+Phase60PersistentGrants: 函数段结束，test_terminal_commands_and_cli_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出终端和 CLI 测试范围。
# 新增代码+Phase60PersistentGrants: 类段结束，WindowsComputerUsePersistentGrantsPhase60Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase60PersistentGrants: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase60PersistentGrants: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
