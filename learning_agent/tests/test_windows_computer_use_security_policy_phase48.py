import json  # 新增代码+Phase48WindowsSecurityPolicy: 导入 JSON 工具用于读取验收场景；如果没有这行代码，测试无法确认真实终端 token 被写进场景文件。
import tempfile  # 新增代码+Phase48WindowsSecurityPolicy: 导入临时目录工具隔离 /computer 状态测试；如果没有这行代码，测试可能污染真实 Computer Use 运行目录。
import unittest  # 新增代码+Phase48WindowsSecurityPolicy: 导入标准测试框架承载 Phase48 测试；如果没有这行代码，自动化命令无法发现这些安全策略断言。
from pathlib import Path  # 新增代码+Phase48WindowsSecurityPolicy: 导入 Path 便于稳定定位项目文件；如果没有这行代码，场景路径拼接会变脆弱。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase48WindowsSecurityPolicy: 导入真实终端命令渲染入口；如果没有这行代码，Phase48 无法证明拒绝原因能被用户读懂。
from learning_agent.computer_use.approval import WindowsComputerUseApprovalModel  # 新增代码+Phase48WindowsSecurityPolicy: 导入现有审批模型验证策略接入；如果没有这行代码，测试只能覆盖孤立策略类。
from learning_agent.computer_use.security_policy import PHASE48_WINDOWS_SECURITY_POLICY_MARKER, PHASE48_WINDOWS_SECURITY_POLICY_OK_TOKEN, WindowsComputerUseSecurityPolicy, phase48_cli_line, run_phase48_security_policy_contract  # 新增代码+Phase48WindowsSecurityPolicy: 导入 Phase48 期望新增的策略入口；如果没有这行代码，红测会证明安全策略模块尚未实现。


class WindowsComputerUseSecurityPolicyPhase48Tests(unittest.TestCase):  # 新增代码+Phase48WindowsSecurityPolicy: 类段开始，集中验证 Phase48 权限审批和安全策略；如果没有这个类，Phase48 的安全边界不会被 unittest 组织运行。
    def _safe_window(self) -> dict[str, object]:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，提供安全 Notepad 窗口样本；如果没有这段函数，每个测试都要重复拼安全窗口输入。
        return {"app_id": "notepad.exe", "window_id": "hwnd:4801", "title_preview": "Phase48 Notepad", "process_name": "notepad.exe", "rect": {"left": 20, "top": 30, "right": 420, "bottom": 260}}  # 新增代码+Phase48WindowsSecurityPolicy: 返回带窗口身份和矩形的安全目标；如果没有这行代码，策略无法评估 app 授权场景。
    # 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出安全样本范围。

    def test_policy_distinguishes_observe_action_system_key_and_clipboard_grants(self) -> None:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，验证授权类别被细分；如果没有这个测试，observe/action/system_key/clipboard 可能继续混在一起。
        policy = WindowsComputerUseSecurityPolicy()  # 新增代码+Phase48WindowsSecurityPolicy: 创建安全策略实例；如果没有这行代码，后续无法计算每类动作需要的 grant。
        observe = policy.evaluate("observe:get_window_state", {"window": self._safe_window()}, grant_flags={"observe": True}, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 评估只读观察动作；如果没有这行代码，测试无法证明 observe grant 独立存在。
        action = policy.evaluate("click", {"window": self._safe_window()}, grant_flags={"desktopAction": True}, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 评估普通桌面动作；如果没有这行代码，测试无法证明 action grant 独立存在。
        system_key = policy.evaluate("press_key", {"window": self._safe_window(), "key": "ctrl+alt+delete"}, grant_flags={"desktopAction": True, "systemKeyCombos": True}, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 评估系统组合键动作；如果没有这行代码，测试无法证明 system_key 需要单独 grant。
        clipboard = policy.evaluate("clipboard_read", {"window": self._safe_window()}, grant_flags={"clipboardRead": True}, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 评估剪贴板读取动作；如果没有这行代码，测试无法证明 clipboard grant 独立存在。
        self.assertTrue(observe["allowed"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言只读观察被 observe grant 放行；如果没有这行代码，错误拒绝 observe 不会被发现。
        self.assertEqual(observe["grant_scope"], "observe")  # 新增代码+Phase48WindowsSecurityPolicy: 断言观察动作归类稳定；如果没有这行代码，终端 UI 无法按类别解释权限。
        self.assertTrue(action["allowed"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言普通动作被 desktopAction grant 放行；如果没有这行代码，普通点击授权退化不会被发现。
        self.assertEqual(action["grant_scope"], "action")  # 新增代码+Phase48WindowsSecurityPolicy: 断言普通动作归类为 action；如果没有这行代码，策略可能把点击误归为高风险动作。
        self.assertTrue(system_key["allowed"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言系统组合键在显式授权后才能放行；如果没有这行代码，开启 systemKeyCombos 后的路径没有证据。
        self.assertEqual(system_key["grant_scope"], "system_key")  # 新增代码+Phase48WindowsSecurityPolicy: 断言系统组合键归类稳定；如果没有这行代码，拒绝原因可能不够清楚。
        self.assertTrue(clipboard["allowed"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言剪贴板读取在显式授权后放行；如果没有这行代码，剪贴板权限无法被验证。
        self.assertEqual(clipboard["grant_scope"], "clipboard")  # 新增代码+Phase48WindowsSecurityPolicy: 断言剪贴板动作归类稳定；如果没有这行代码，剪贴板风险会混进普通动作。
    # 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，test_policy_distinguishes_observe_action_system_key_and_clipboard_grants 到此结束；如果没有这个边界说明，读者不容易看出权限类别测试范围。

    def test_high_risk_actions_are_denied_by_default_with_readable_reasons(self) -> None:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，验证高风险动作默认拒绝；如果没有这个测试，危险权限可能因为 app 已授权而误放行。
        policy = WindowsComputerUseSecurityPolicy()  # 新增代码+Phase48WindowsSecurityPolicy: 创建策略实例；如果没有这行代码，无法验证默认高风险拒绝。
        system_key = policy.evaluate("press_key", {"window": self._safe_window(), "key": "ctrl+alt+delete"}, grant_flags={"desktopAction": True}, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 只授予普通动作但不授予系统键；如果没有这行代码，高风险默认拒绝没有输入样本。
        clipboard_write = policy.evaluate("clipboard_write", {"window": self._safe_window(), "text": "secret"}, grant_flags={"desktopAction": True}, app_granted=True)  # 新增代码+Phase48WindowsSecurityPolicy: 只授予普通动作但不授予剪贴板写；如果没有这行代码，剪贴板高风险默认拒绝没有样本。
        self.assertFalse(system_key["allowed"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言系统组合键默认不允许；如果没有这行代码，危险键误放行不会失败。
        self.assertEqual(system_key["decision"], "denied_high_risk_default")  # 新增代码+Phase48WindowsSecurityPolicy: 断言拒绝原因明确说明高风险默认拒绝；如果没有这行代码，用户只会看到模糊失败。
        self.assertIn("systemKeyCombos", system_key["missing_grant_flags"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言缺失权限包含系统组合键；如果没有这行代码，用户不知道该开哪个 grant。
        self.assertIn("系统组合键", system_key["readable_reason"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言中文可读原因解释系统键风险；如果没有这行代码，真实终端拒绝原因不够友好。
        self.assertFalse(clipboard_write["allowed"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言剪贴板写默认不允许；如果没有这行代码，剪贴板写入误放行不会失败。
        self.assertEqual(clipboard_write["decision"], "denied_high_risk_default")  # 新增代码+Phase48WindowsSecurityPolicy: 断言剪贴板写拒绝原因稳定；如果没有这行代码，验收器无法匹配高风险拒绝。
        self.assertIn("clipboardWrite", clipboard_write["missing_grant_flags"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言缺失权限包含剪贴板写；如果没有这行代码，用户不知道要授权哪项剪贴板能力。
        self.assertIn("剪贴板", clipboard_write["readable_reason"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言中文可读原因解释剪贴板风险；如果没有这行代码，终端拒绝信息不够清楚。
    # 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，test_high_risk_actions_are_denied_by_default_with_readable_reasons 到此结束；如果没有这个边界说明，读者不容易看出高风险拒绝测试范围。

    def test_approval_model_uses_policy_without_breaking_safe_click_grants(self) -> None:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，验证 Phase38 审批模型接入 Phase48 策略；如果没有这个测试，新策略可能只是孤立模块。
        model = WindowsComputerUseApprovalModel(security_policy=WindowsComputerUseSecurityPolicy())  # 新增代码+Phase48WindowsSecurityPolicy: 创建带策略的审批模型；如果没有这行代码，controller 使用的审批链路不会覆盖 Phase48。
        model.grant_for_session([self._safe_window()], {"desktopAction": True, "systemKeyCombos": False}, reason="phase48-safe-click")  # 新增代码+Phase48WindowsSecurityPolicy: 授权安全 app 的普通桌面动作；如果没有这行代码，后续点击会因为 app 未授权而提前失败。
        click = model.evaluate("click", {"window": self._safe_window()})  # 新增代码+Phase48WindowsSecurityPolicy: 评估安全点击；如果没有这行代码，无法确认新策略没有破坏普通点击。
        system_key = model.evaluate("press_key", {"window": self._safe_window(), "key": "ctrl+alt+delete"})  # 新增代码+Phase48WindowsSecurityPolicy: 评估未显式授权的系统组合键；如果没有这行代码，无法确认新策略接管高风险拒绝。
        self.assertTrue(click["allowed"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言安全点击仍然允许；如果没有这行代码，Phase48 可能回归破坏 Phase38。
        self.assertEqual(click["policy"]["grant_scope"], "action")  # 新增代码+Phase48WindowsSecurityPolicy: 断言允许结果携带策略归类；如果没有这行代码，审计时无法知道策略如何判定。
        self.assertFalse(system_key["allowed"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言未授权系统组合键被拒绝；如果没有这行代码，高风险默认拒绝不会覆盖审批模型。
        self.assertEqual(system_key["decision"], "denied_high_risk_default")  # 新增代码+Phase48WindowsSecurityPolicy: 断言拒绝原因来自 Phase48 策略；如果没有这行代码，旧的模糊 missing_grant_flags 会继续暴露。
        self.assertIn("系统组合键", system_key["readable_reason"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言审批模型把中文拒绝原因透传给 controller；如果没有这行代码，真实终端用户仍看不懂为什么拒绝。
    # 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，test_approval_model_uses_policy_without_breaking_safe_click_grants 到此结束；如果没有这个边界说明，读者不容易看出审批接入测试范围。

    def test_phase48_cli_contract_terminal_status_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase48WindowsSecurityPolicy: 函数段开始，验证 CLI、终端状态和验收场景 token；如果没有这个测试，真实验收可能缺少稳定证据。
        report = run_phase48_security_policy_contract()  # 新增代码+Phase48WindowsSecurityPolicy: 运行 Phase48 无副作用合同自检；如果没有这行代码，CLI token 没有报告来源。
        line = phase48_cli_line(report)  # 新增代码+Phase48WindowsSecurityPolicy: 生成稳定单行 CLI 输出；如果没有这行代码，验收器需要解析完整 JSON。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase48WindowsSecurityPolicy: 定位项目根目录；如果没有这行代码，场景文件路径会依赖当前工作目录。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase48_windows_security_policy.json"  # 新增代码+Phase48WindowsSecurityPolicy: 定位 Phase48 验收场景；如果没有这行代码，测试无法确认场景包含新 token。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase48WindowsSecurityPolicy: 读取并解析验收场景；如果没有这行代码，场景 token 漏写不会被发现。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase48WindowsSecurityPolicy: 创建临时目录隔离真实终端状态渲染；如果没有这行代码，测试可能读写生产锁状态。
            output = run_computer_terminal_command(Path(temp_dir), "/computer status")  # 新增代码+Phase48WindowsSecurityPolicy: 渲染 /computer status；如果没有这行代码，无法证明用户在终端能看到 Phase48 策略摘要。
        expected_tokens = {PHASE48_WINDOWS_SECURITY_POLICY_MARKER, PHASE48_WINDOWS_SECURITY_POLICY_OK_TOKEN, "grant_classes=true", "high_risk_default=true", "clipboard=true", "controller_policy=true", "terminal_status=true", "actions_expanded=false"}  # 新增代码+Phase48WindowsSecurityPolicy: 列出 Phase48 必须稳定输出的 token；如果没有这行代码，成功标准会散落在多个断言里。
        self.assertIn(PHASE48_WINDOWS_SECURITY_POLICY_MARKER, line)  # 新增代码+Phase48WindowsSecurityPolicy: 断言 CLI 行包含 ready marker；如果没有这行代码，阶段完成信号可能缺失。
        self.assertTrue(report["grant_classes"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言授权类别细分合同成立；如果没有这行代码，策略分类退化不会被发现。
        self.assertTrue(report["high_risk_default"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言高风险默认拒绝合同成立；如果没有这行代码，危险动作默认放行不会被发现。
        self.assertIn("security_policy=phase48_windows_security_policy", output)  # 新增代码+Phase48WindowsSecurityPolicy: 断言终端状态展示安全策略名称；如果没有这行代码，用户看不到当前策略层。
        self.assertIn("grant_classes=observe,desktopAction,systemKeyCombos,clipboardRead,clipboardWrite", output)  # 新增代码+Phase48WindowsSecurityPolicy: 断言终端状态展示授权类别；如果没有这行代码，用户不知道可以区分哪些 grant。
        for token in expected_tokens:  # 新增代码+Phase48WindowsSecurityPolicy: 遍历场景必须包含的 token；如果没有这行代码，某些验收关键词可能漏检。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言 debug log 检查包含 token；如果没有这行代码，调试日志证据可能缺失。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase48WindowsSecurityPolicy: 断言最终回答检查包含 token；如果没有这行代码，用户可见回答可能没有证据。
    # 新增代码+Phase48WindowsSecurityPolicy: 函数段结束，test_phase48_cli_contract_terminal_status_and_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，读者不容易看出 CLI/场景测试范围。


if __name__ == "__main__":  # 新增代码+Phase48WindowsSecurityPolicy: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式单独验证 Phase48。
    unittest.main()  # 新增代码+Phase48WindowsSecurityPolicy: 启动 unittest 主入口；如果没有这行代码，直接运行测试文件不会执行任何断言。
