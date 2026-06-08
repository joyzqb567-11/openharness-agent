import tempfile  # 新增代码+Phase72RealAppSafetyBoundary: 导入临时目录隔离持久授权状态；如果没有这行代码，测试会污染真实用户授权文件。
import unittest  # 新增代码+Phase72RealAppSafetyBoundary: 导入 unittest 承载 Phase72 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase72RealAppSafetyBoundary: 导入 Path 统一处理 Windows 路径；如果没有这行代码，场景文件和临时目录拼接更脆弱。

from learning_agent.computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANT_SESSION_ID, WindowsComputerUsePersistentGrantStore  # 新增代码+Phase72RealAppSafetyBoundary: 导入 Phase60 持久授权 store；如果没有这行代码，Phase72 无法验证真实授权事实源。
from learning_agent.computer_use.real_app_safety_boundary import PHASE72_CONTROLLED_ACTIONS_EXPANSION, PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER, PHASE72_REAL_APP_SAFETY_BOUNDARY_OK_TOKEN, PHASE72_UNCONTROLLED_ACTIONS_EXPANDED, Phase72RecordingAbortGate, WindowsRealAppSafetyBoundary, phase72_cli_line, run_phase72_real_app_safety_boundary_contract  # 新增代码+Phase72RealAppSafetyBoundary: 导入预期 Phase72 安全边界入口；如果没有这行代码，红灯会证明生产模块尚未实现。


class WindowsComputerUseRealAppSafetyBoundaryPhase72Tests(unittest.TestCase):  # 新增代码+Phase72RealAppSafetyBoundary: 类段开始，集中验证真实应用安全边界；如果没有这个类，Phase72 没有自动化门禁。
    def _normal_window(self) -> dict[str, object]:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，提供普通真实应用窗口样本；如果没有这段函数，每个测试都要重复构造安全目标。
        return {"app_id": "notepad.exe", "process_name": "notepad.exe", "window_id": "hwnd:7201", "title_preview": "Untitled - Notepad", "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase72RealAppSafetyBoundary: 返回 Notepad 普通窗口样本；如果没有这行代码，授权正例没有稳定 app/window/display。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_normal_window 到此结束；如果没有这个边界说明，初学者不容易看出普通窗口样本范围。

    def _terminal_window(self) -> dict[str, object]:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，提供终端窗口危险样本；如果没有这段函数，终端默认拒绝没有固定测试目标。
        return {"app_id": "powershell.exe", "process_name": "powershell.exe", "window_id": "hwnd:7202", "title_preview": "Windows PowerShell", "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase72RealAppSafetyBoundary: 返回 PowerShell 样本；如果没有这行代码，模型可能误把终端当普通应用。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_terminal_window 到此结束；如果没有这个边界说明，初学者不容易看出终端样本范围。

    def _codex_window(self) -> dict[str, object]:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，提供 Codex UI 危险样本；如果没有这段函数，自我控制界面拒绝没有固定测试目标。
        return {"app_id": "codex.exe", "process_name": "codex.exe", "window_id": "hwnd:7203", "title_preview": "Codex - Learning Agent", "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase72RealAppSafetyBoundary: 返回 Codex 窗口样本；如果没有这行代码，agent 可能控制自己的调试界面。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_codex_window 到此结束；如果没有这个边界说明，初学者不容易看出 Codex 样本范围。

    def _auth_window(self) -> dict[str, object]:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，提供登录/验证码/支付危险样本；如果没有这段函数，高风险业务窗口默认拒绝没有固定测试目标。
        return {"app_id": "chrome.exe", "process_name": "chrome.exe", "window_id": "hwnd:7204", "title_preview": "Login password captcha payment verification", "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase72RealAppSafetyBoundary: 返回带敏感关键词的浏览器窗口；如果没有这行代码，密码验证码支付页可能被误放行。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，_auth_window 到此结束；如果没有这个边界说明，初学者不容易看出敏感窗口样本范围。

    def test_authorized_real_app_actions_require_persistent_grants(self) -> None:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，验证普通应用必须有 Phase60 持久授权才放行；如果没有这个测试，安全边界可能只看 safe_to_target 就执行。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase72RealAppSafetyBoundary: 使用临时目录隔离 grant 状态；如果没有这行代码，测试会读写真实授权。
            store = WindowsComputerUsePersistentGrantStore(base_dir=Path(temp_dir) / "grants")  # 新增代码+Phase72RealAppSafetyBoundary: 创建隔离持久授权 store；如果没有这行代码，Phase72 没有授权事实源。
            boundary = WindowsRealAppSafetyBoundary()  # 新增代码+Phase72RealAppSafetyBoundary: 创建安全边界对象；如果没有这行代码，无法评估动作是否可进入低层发送。
            denied = boundary.evaluate(self._normal_window(), "click", store, DEFAULT_PERSISTENT_GRANT_SESSION_ID)  # 新增代码+Phase72RealAppSafetyBoundary: 未授权先评估普通点击；如果没有这行代码，默认拒绝路径没有证据。
            store.approve(session_id=DEFAULT_PERSISTENT_GRANT_SESSION_ID, app="notepad.exe", window_id="hwnd:7201", display_id="DISPLAY1", action_scope=["click", "type_text", "scroll", "drag"], ttl_seconds=60, reason="phase72 unit", grant_flags={"desktopAction": True})  # 新增代码+Phase72RealAppSafetyBoundary: 写入普通应用可控动作授权；如果没有这行代码，正例没有合法放行条件。
            allowed = boundary.evaluate(self._normal_window(), "click", store, DEFAULT_PERSISTENT_GRANT_SESSION_ID)  # 新增代码+Phase72RealAppSafetyBoundary: 授权后再次评估点击；如果没有这行代码，无法证明持久授权能放行普通应用。
            self.assertFalse(denied["allowed"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言未授权普通应用拒绝；如果没有这行代码，默认放行风险不会暴露。
            self.assertEqual(denied["decision"], "requires_persistent_grant")  # 新增代码+Phase72RealAppSafetyBoundary: 断言拒绝原因稳定；如果没有这行代码，用户不知道要先 approve。
            self.assertEqual(denied["low_level_event_count"], 0)  # 新增代码+Phase72RealAppSafetyBoundary: 断言拒绝时低层事件为 0；如果没有这行代码，安全边界可能拒绝后仍发送动作。
            self.assertTrue(allowed["allowed"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言授权普通应用可放行；如果没有这行代码，Phase72 会只会拒绝不能实际控制。
            self.assertEqual(allowed["decision"], "allowed_by_persistent_grant")  # 新增代码+Phase72RealAppSafetyBoundary: 断言放行来源稳定；如果没有这行代码，审计无法追溯授权依据。
            self.assertTrue(allowed["controlled_actions_expansion"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言受控动作扩展为真；如果没有这行代码，Phase72 的可控动作边界无法被验证。
            self.assertFalse(allowed["uncontrolled_actions_expanded"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言未扩大无边界动作；如果没有这行代码，安全策略可能被误解成任意动作放行。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，test_authorized_real_app_actions_require_persistent_grants 到此结束；如果没有这个边界说明，初学者不容易看出授权正反例范围。

    def test_high_risk_windows_are_refused_with_zero_events(self) -> None:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，验证终端、Codex 和敏感窗口默认拒绝且 0 事件；如果没有这个测试，危险窗口可能被拟人动作误控。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase72RealAppSafetyBoundary: 使用临时目录隔离授权状态；如果没有这行代码，测试会污染真实 grants。
            store = WindowsComputerUsePersistentGrantStore(base_dir=Path(temp_dir) / "grants")  # 新增代码+Phase72RealAppSafetyBoundary: 创建授权 store；如果没有这行代码，边界无法完成统一接口评估。
            boundary = WindowsRealAppSafetyBoundary()  # 新增代码+Phase72RealAppSafetyBoundary: 创建安全边界；如果没有这行代码，危险窗口没有评估入口。
            for window in [self._terminal_window(), self._codex_window(), self._auth_window()]:  # 新增代码+Phase72RealAppSafetyBoundary: 遍历三类危险窗口；如果没有这行代码，测试覆盖会只剩一种危险类型。
                result = boundary.evaluate(window, "click", store, DEFAULT_PERSISTENT_GRANT_SESSION_ID)  # 新增代码+Phase72RealAppSafetyBoundary: 对危险窗口尝试点击评估；如果没有这行代码，默认拒绝没有动作输入。
                self.assertFalse(result["allowed"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言危险窗口不允许；如果没有这行代码，终端或验证码页误控不会被发现。
                self.assertEqual(result["decision"], "high_risk_window_refused")  # 新增代码+Phase72RealAppSafetyBoundary: 断言危险拒绝原因稳定；如果没有这行代码，审计难以区分授权缺失和风险拒绝。
                self.assertEqual(result["low_level_event_count"], 0)  # 新增代码+Phase72RealAppSafetyBoundary: 断言危险拒绝 0 事件；如果没有这行代码，拒绝路径可能仍触发真实输入。
                self.assertTrue(result["high_risk_default_refusal"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言高风险默认拒绝标志；如果没有这行代码，验收 token 无法证明安全策略。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，test_high_risk_windows_are_refused_with_zero_events 到此结束；如果没有这个边界说明，初学者不容易看出高风险拒绝范围。

    def test_abort_gate_blocks_authorized_action_before_low_level_send(self) -> None:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，验证授权动作在 abort 后仍必须拦截；如果没有这个测试，用户急停可能输给已通过授权的动作。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase72RealAppSafetyBoundary: 使用临时目录隔离授权状态；如果没有这行代码，测试会污染真实 grants。
            store = WindowsComputerUsePersistentGrantStore(base_dir=Path(temp_dir) / "grants")  # 新增代码+Phase72RealAppSafetyBoundary: 创建授权 store；如果没有这行代码，abort 测试没有合法正例前置。
            store.approve(session_id=DEFAULT_PERSISTENT_GRANT_SESSION_ID, app="notepad.exe", window_id="hwnd:7201", display_id="DISPLAY1", action_scope=["click"], ttl_seconds=60, reason="phase72 abort", grant_flags={"desktopAction": True})  # 新增代码+Phase72RealAppSafetyBoundary: 写入点击授权；如果没有这行代码，拒绝可能只是因为没授权而不是 abort。
            boundary = WindowsRealAppSafetyBoundary(abort_gate=Phase72RecordingAbortGate(aborted=True))  # 新增代码+Phase72RealAppSafetyBoundary: 注入已触发急停的 gate；如果没有这行代码，无法证明发送前急停会拦截。
            result = boundary.evaluate(self._normal_window(), "click", store, DEFAULT_PERSISTENT_GRANT_SESSION_ID)  # 新增代码+Phase72RealAppSafetyBoundary: 对已授权动作执行安全评估；如果没有这行代码，abort_before_low_level_send 没有证据。
            self.assertFalse(result["allowed"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言急停后不允许动作；如果没有这行代码，abort 可能不生效。
            self.assertEqual(result["decision"], "abort_before_low_level_send")  # 新增代码+Phase72RealAppSafetyBoundary: 断言拒绝发生在低层发送前；如果没有这行代码，安全审计无法说明拦截位置。
            self.assertEqual(result["low_level_event_count"], 0)  # 新增代码+Phase72RealAppSafetyBoundary: 断言急停后 0 事件；如果没有这行代码，用户急停仍可能有副作用。
            self.assertTrue(result["abort_before_low_level_send"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言急停 token 字段为真；如果没有这行代码，CLI 无法稳定汇总。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，test_abort_gate_blocks_authorized_action_before_low_level_send 到此结束；如果没有这个边界说明，初学者不容易看出 abort 门禁范围。

    def test_approval_bypass_marker_does_not_replace_persistent_grant(self) -> None:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，验证窗口自带绕过字段不能替代 Phase60 授权；如果没有这个测试，伪造 safe/approval 字段可能直接放行。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase72RealAppSafetyBoundary: 使用临时目录隔离授权状态；如果没有这行代码，测试会污染真实 grants。
            store = WindowsComputerUsePersistentGrantStore(base_dir=Path(temp_dir) / "grants")  # 新增代码+Phase72RealAppSafetyBoundary: 创建空授权 store；如果没有这行代码，绕过测试没有真实授权缺失状态。
            window = dict(self._normal_window(), approval_bypass=True, previous_approval={"allowed": True})  # 新增代码+Phase72RealAppSafetyBoundary: 构造带绕过暗示的普通窗口；如果没有这行代码，approval_bypass_blocked 没有输入。
            result = WindowsRealAppSafetyBoundary().evaluate(window, "click", store, DEFAULT_PERSISTENT_GRANT_SESSION_ID)  # 新增代码+Phase72RealAppSafetyBoundary: 评估绕过字段是否会放行；如果没有这行代码，绕过风险不会被验证。
            self.assertFalse(result["allowed"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言绕过字段不允许动作；如果没有这行代码，伪造 approval 可能被当成真实授权。
            self.assertEqual(result["decision"], "approval_bypass_blocked")  # 新增代码+Phase72RealAppSafetyBoundary: 断言绕过拒绝原因稳定；如果没有这行代码，用户不知道为何 previous_approval 无效。
            self.assertTrue(result["approval_bypass_blocked"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言绕过拦截字段为真；如果没有这行代码，合同报告无法证明防绕过。
            self.assertEqual(result["low_level_event_count"], 0)  # 新增代码+Phase72RealAppSafetyBoundary: 断言绕过拒绝 0 事件；如果没有这行代码，拒绝后仍可能误发输入。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，test_approval_bypass_marker_does_not_replace_persistent_grant 到此结束；如果没有这个边界说明，初学者不容易看出防绕过范围。

    def test_phase72_cli_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase72RealAppSafetyBoundary: 函数段开始，验证 CLI 和真实终端场景 token 稳定；如果没有这个测试，验收器可能漏检核心安全字段。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase72RealAppSafetyBoundary: 使用临时目录隔离合同状态；如果没有这行代码，合同会读写真实 memory。
            report = run_phase72_real_app_safety_boundary_contract(base_dir=Path(temp_dir))  # 新增代码+Phase72RealAppSafetyBoundary: 运行 Phase72 合同自检；如果没有这行代码，CLI token 没有结构化来源。
        cli_line = phase72_cli_line(report)  # 新增代码+Phase72RealAppSafetyBoundary: 生成稳定 CLI 行；如果没有这行代码，场景匹配无法验证。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase72_real_app_safety_boundary.json")  # 新增代码+Phase72RealAppSafetyBoundary: 定位 Phase72 真实终端场景；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase72RealAppSafetyBoundary: 读取场景文本；如果没有这行代码，token 漏配无法检测。
        expected_tokens = {PHASE72_REAL_APP_SAFETY_BOUNDARY_MARKER, PHASE72_REAL_APP_SAFETY_BOUNDARY_OK_TOKEN, "authorized_real_app_actions=true", "unauthorized_window_zero_events=true", "high_risk_default_refusal=true", "abort_before_low_level_send=true", "approval_bypass_blocked=true", "controlled_actions_expansion=true", "uncontrolled_actions_expanded=false"}  # 新增代码+Phase72RealAppSafetyBoundary: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        self.assertTrue(report["authorized_real_app_actions"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言授权普通应用可控；如果没有这行代码，核心正例可能失败但 CLI 被忽略。
        self.assertTrue(report["unauthorized_window_zero_events"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言未授权拒绝 0 事件；如果没有这行代码，默认拒绝副作用不会暴露。
        self.assertTrue(report["high_risk_default_refusal"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言高风险默认拒绝；如果没有这行代码，终端/验证码风险可能漏过。
        self.assertTrue(report["abort_before_low_level_send"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言 abort 前置拦截；如果没有这行代码，急停安全性无法证明。
        self.assertTrue(report["approval_bypass_blocked"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言绕过被阻断；如果没有这行代码，伪造 approval 风险不会暴露。
        self.assertTrue(report["controlled_actions_expansion"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言受控扩展存在；如果没有这行代码，Phase72 可能没有真正补齐可控普通应用。
        self.assertFalse(report["uncontrolled_actions_expanded"])  # 新增代码+Phase72RealAppSafetyBoundary: 断言未扩展无边界动作；如果没有这行代码，安全边界可能被误解。
        self.assertTrue(PHASE72_CONTROLLED_ACTIONS_EXPANSION)  # 新增代码+Phase72RealAppSafetyBoundary: 断言模块常量声明受控动作扩展；如果没有这行代码，报告和模块边界可能不一致。
        self.assertFalse(PHASE72_UNCONTROLLED_ACTIONS_EXPANDED)  # 新增代码+Phase72RealAppSafetyBoundary: 断言模块常量声明未扩展无边界动作；如果没有这行代码，生产声明可能漂移。
        for token in expected_tokens:  # 新增代码+Phase72RealAppSafetyBoundary: 遍历关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase72RealAppSafetyBoundary: 断言 CLI 包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase72RealAppSafetyBoundary: 断言场景包含 token；如果没有这行代码，真实终端验收可能漏检。
    # 新增代码+Phase72RealAppSafetyBoundary: 函数段结束，test_phase72_cli_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景测试范围。
# 新增代码+Phase72RealAppSafetyBoundary: 类段结束，WindowsComputerUseRealAppSafetyBoundaryPhase72Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase72RealAppSafetyBoundary: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase72RealAppSafetyBoundary: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
