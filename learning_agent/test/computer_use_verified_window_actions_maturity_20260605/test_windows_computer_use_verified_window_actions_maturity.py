import unittest  # 新增代码+VerifiedWindowActionsMaturity：导入 unittest 测试框架；如果没有这一行，项目测试运行器无法执行本文件。

from learning_agent.computer_use.generic_control_actions import Phase70RecordingHighLevelTool, WindowsGenericControlActionRuntime  # 新增代码+VerifiedWindowActionsMaturity：导入通用点击/输入动作 runtime；如果没有这一行，测试无法覆盖动作层是否要求验证窗口。
from learning_agent.computer_use.generic_input_actions import Phase71RecordingInputSender, WindowsGenericInputActionRuntime  # 新增代码+VerifiedWindowActionsMaturity：导入通用热键/输入事件 runtime；如果没有这一行，测试无法覆盖安全热键是否要求验证窗口。
from learning_agent.computer_use.target_identity import build_owned_target_identity, verify_owned_target_identity  # 新增代码+VerifiedWindowActionsMaturity：导入 Task3 目标身份绑定工具；如果没有这一行，测试无法生成真实形状的 OwnedTargetIdentity。


class WindowsComputerUseVerifiedWindowActionsMaturityTests(unittest.TestCase):  # 新增代码+VerifiedWindowActionsMaturity：类段开始，集中验收 Task6 通用动作必须绑定已验证窗口；如果没有这个类，动作层可能继续对漂移窗口派发。
    def _window(self) -> dict[str, object]:  # 新增代码+VerifiedWindowActionsMaturity：函数段开始，构造稳定的自有窗口样本；如果没有这段函数，每个测试会重复手写窗口字段。
        return {"pid": 1142, "hwnd": 11420, "window_id": "hwnd:11420", "process_name": "Obsidian.exe", "process_path": r"C:\Apps\Obsidian\Obsidian.exe", "title_preview": "Vault - Obsidian", "app_id": "Obsidian.exe", "safe_to_target": True}  # 新增代码+VerifiedWindowActionsMaturity：返回 pid/hwnd/title 都稳定的窗口记录；如果没有这一行，身份绑定缺少窗口侧事实。
    # 新增代码+VerifiedWindowActionsMaturity：函数段结束，_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口样本范围。

    def _owned_identity(self):  # 新增代码+VerifiedWindowActionsMaturity：函数段开始，构造自有目标身份；如果没有这段函数，每个测试无法复用同一身份凭证。
        launch_result = {"process_id": 1142, "process_executable": "Obsidian.exe", "process_path": r"C:\Apps\Obsidian\Obsidian.exe", "owned_process_registered": True, "cleanup_registered": True}  # 新增代码+VerifiedWindowActionsMaturity：构造 agent 自己启动的进程记录；如果没有这一行，目标身份会被当成用户已有窗口保护。
        return build_owned_target_identity(launch_result, self._window())  # 新增代码+VerifiedWindowActionsMaturity：返回进程和窗口绑定后的 OwnedTargetIdentity；如果没有这一行，动作层没有可信身份输入。
    # 新增代码+VerifiedWindowActionsMaturity：函数段结束，_owned_identity 到此结束；如果没有这个边界说明，初学者不容易看出身份构造范围。

    def _verified_context(self) -> dict[str, object]:  # 新增代码+VerifiedWindowActionsMaturity：函数段开始，构造动作层需要的验证上下文；如果没有这段函数，测试参数会散落且容易漏字段。
        owned = self._owned_identity()  # 新增代码+VerifiedWindowActionsMaturity：读取自有目标身份；如果没有这一行，后续无法生成 window_identity 和 verification。
        verification = verify_owned_target_identity(owned, self._window())  # 新增代码+VerifiedWindowActionsMaturity：对稳定窗口做动作前验证；如果没有这一行，测试无法证明 same target 正例。
        return {"session_id": "phase114-session", "window_identity": owned.window.to_report(), "target_identity_verification": verification.to_report()}  # 新增代码+VerifiedWindowActionsMaturity：返回动作层成熟 API 需要的三件事；如果没有这一行，动作层接线要求不可验证。
    # 新增代码+VerifiedWindowActionsMaturity：函数段结束，_verified_context 到此结束；如果没有这个边界说明，初学者不容易看出验证上下文范围。

    def _drift_verification(self) -> dict[str, object]:  # 新增代码+VerifiedWindowActionsMaturity：函数段开始，构造漂移验证报告；如果没有这段函数，漂移阻断测试没有坏窗口样本。
        owned = self._owned_identity()  # 新增代码+VerifiedWindowActionsMaturity：读取期望自有目标；如果没有这一行，漂移没有比较基准。
        drifted_window = dict(self._window(), pid=9999, hwnd=11421, window_id="hwnd:11421")  # 新增代码+VerifiedWindowActionsMaturity：构造同标题不同 pid/hwnd 的漂移窗口；如果没有这一行，漂移阻断没有真实风险样本。
        return verify_owned_target_identity(owned, drifted_window).to_report()  # 新增代码+VerifiedWindowActionsMaturity：返回漂移验证报告；如果没有这一行，动作层无法收到 target_drift_blocks_action。
    # 新增代码+VerifiedWindowActionsMaturity：函数段结束，_drift_verification 到此结束；如果没有这个边界说明，初学者不容易看出漂移样本范围。

    def _observation(self) -> dict[str, object]:  # 新增代码+VerifiedWindowActionsMaturity：函数段开始，构造包含按钮和输入框的观察；如果没有这段函数，click/type 测试无法命中控件。
        return {"fingerprint": "phase114-before", "flat_nodes": [{"node_id": "0.1", "name": "Message box", "role": "Edit", "automation_id": "Phase114Message", "bounds": {"left": 10, "top": 10, "right": 210, "bottom": 40, "width": 200, "height": 30}, "enabled": True, "clickable": True, "editable": True}, {"node_id": "0.2", "name": "Save button", "role": "Button", "automation_id": "Phase114Save", "bounds": {"left": 220, "top": 10, "right": 300, "bottom": 40, "width": 80, "height": 30}, "enabled": True, "clickable": True, "editable": False}]}  # 新增代码+VerifiedWindowActionsMaturity：返回可被 Phase57 locator 命中的最小 UIA 观察；如果没有这一行，正例会因为找不到控件而失败。
    # 新增代码+VerifiedWindowActionsMaturity：函数段结束，_observation 到此结束；如果没有这个边界说明，初学者不容易看出观察样本范围。

    def test_click_requires_verified_owned_window(self) -> None:  # 新增代码+VerifiedWindowActionsMaturity：函数段开始，验证点击必须收到已验证窗口身份；如果没有这段测试，点击可能继续对漂移窗口动作。
        tool = Phase70RecordingHighLevelTool()  # 新增代码+VerifiedWindowActionsMaturity：创建记录型高层工具；如果没有这一行，测试可能触碰真实桌面。
        runtime = WindowsGenericControlActionRuntime(high_level_tool=tool)  # 新增代码+VerifiedWindowActionsMaturity：创建通用控制动作 runtime；如果没有这一行，测试没有被测对象。
        context = self._verified_context()  # 新增代码+VerifiedWindowActionsMaturity：读取已验证身份上下文；如果没有这一行，正例动作缺少身份凭证。
        blocked = runtime.click_by_visual_point(self._window(), {"x": 50, "y": 25}, "missing identity", require_verified_identity=True)  # 新增代码+VerifiedWindowActionsMaturity：缺身份时要求阻断；如果没有这一行，动作层是否强制身份不可见。
        allowed = runtime.click_by_visual_point(self._window(), {"x": 50, "y": 25}, "verified click", require_verified_identity=True, **context)  # 新增代码+VerifiedWindowActionsMaturity：带已验证身份执行点击；如果没有这一行，正例无法证明 mature API 可用。
        self.assertTrue(blocked["blocked"])  # 新增代码+VerifiedWindowActionsMaturity：断言缺身份会被阻断；如果没有这一行，未验证窗口可能继续动作。
        self.assertFalse(allowed["blocked"])  # 新增代码+VerifiedWindowActionsMaturity：断言已验证目标不会被阻断；如果没有这一行，成熟 API 只有拒绝没有可用正例。
        self.assertTrue(allowed["same_target"])  # 新增代码+VerifiedWindowActionsMaturity：断言动作前后仍是同一目标；如果没有这一行，漂移风险无法量化。
        self.assertIn("before_identity", allowed)  # 新增代码+VerifiedWindowActionsMaturity：断言报告包含动作前身份；如果没有这一行，动作审计缺少前态证据。
        self.assertIn("after_identity", allowed)  # 新增代码+VerifiedWindowActionsMaturity：断言报告包含动作后身份；如果没有这一行，动作审计缺少后态证据。
        self.assertEqual(allowed["low_level_event_count"], 0)  # 新增代码+VerifiedWindowActionsMaturity：断言记录型测试仍零低层事件；如果没有这一行，安全自动化可能误触本机。
    # 新增代码+VerifiedWindowActionsMaturity：函数段结束，test_click_requires_verified_owned_window 到此结束；如果没有这个边界说明，初学者不容易看出点击身份测试范围。

    def test_type_text_requires_verified_owned_window(self) -> None:  # 新增代码+VerifiedWindowActionsMaturity：函数段开始，验证输入文本必须收到已验证窗口身份；如果没有这段测试，文本可能输到错误窗口。
        tool = Phase70RecordingHighLevelTool()  # 新增代码+VerifiedWindowActionsMaturity：创建记录型高层工具；如果没有这一行，测试可能触碰真实输入。
        runtime = WindowsGenericControlActionRuntime(high_level_tool=tool)  # 新增代码+VerifiedWindowActionsMaturity：创建通用控制动作 runtime；如果没有这一行，测试没有被测对象。
        context = self._verified_context()  # 新增代码+VerifiedWindowActionsMaturity：读取已验证身份上下文；如果没有这一行，输入正例缺少身份凭证。
        blocked = runtime.type_by_query(self._window(), self._observation(), "Message", "hello", require_verified_identity=True)  # 新增代码+VerifiedWindowActionsMaturity：缺身份时要求输入阻断；如果没有这一行，未验证窗口可能接收文本。
        allowed = runtime.type_by_query(self._window(), self._observation(), "Message", "hello", require_verified_identity=True, **context)  # 新增代码+VerifiedWindowActionsMaturity：带已验证身份执行输入；如果没有这一行，正例无法证明输入路径可用。
        self.assertTrue(blocked["blocked"])  # 新增代码+VerifiedWindowActionsMaturity：断言缺身份输入会阻断；如果没有这一行，输入风险不可见。
        self.assertFalse(allowed["blocked"])  # 新增代码+VerifiedWindowActionsMaturity：断言已验证身份输入可继续；如果没有这一行，成熟 API 会只拒绝不执行。
        self.assertTrue(allowed["same_target"])  # 新增代码+VerifiedWindowActionsMaturity：断言输入前后同目标；如果没有这一行，输入可能落到漂移窗口。
        self.assertEqual(allowed["low_level_event_count"], 0)  # 新增代码+VerifiedWindowActionsMaturity：断言测试路径零低层事件；如果没有这一行，自动测试可能误触真实键盘。
    # 新增代码+VerifiedWindowActionsMaturity：函数段结束，test_type_text_requires_verified_owned_window 到此结束；如果没有这个边界说明，初学者不容易看出输入身份测试范围。

    def test_safe_hotkey_requires_verified_owned_window(self) -> None:  # 新增代码+VerifiedWindowActionsMaturity：函数段开始，验证安全热键也必须绑定已验证窗口；如果没有这段测试，Ctrl+S 可能发到错误窗口。
        sender = Phase71RecordingInputSender()  # 新增代码+VerifiedWindowActionsMaturity：创建记录型 sender；如果没有这一行，测试可能触碰真实键盘。
        runtime = WindowsGenericInputActionRuntime(sender=sender)  # 新增代码+VerifiedWindowActionsMaturity：创建通用输入动作 runtime；如果没有这一行，测试没有被测对象。
        context = self._verified_context()  # 新增代码+VerifiedWindowActionsMaturity：读取已验证身份上下文；如果没有这一行，热键正例缺少身份凭证。
        blocked = runtime.send_hotkey(self._window(), ["ctrl", "s"], require_verified_identity=True)  # 新增代码+VerifiedWindowActionsMaturity：缺身份时要求热键阻断；如果没有这一行，热键可能盲发。
        allowed = runtime.send_hotkey(self._window(), ["ctrl", "s"], require_verified_identity=True, **context)  # 新增代码+VerifiedWindowActionsMaturity：带已验证身份记录安全热键；如果没有这一行，正例无法证明成熟热键可用。
        self.assertTrue(blocked["blocked"])  # 新增代码+VerifiedWindowActionsMaturity：断言缺身份热键会阻断；如果没有这一行，未验证窗口可收到热键。
        self.assertFalse(allowed["blocked"])  # 新增代码+VerifiedWindowActionsMaturity：断言已验证身份热键可继续；如果没有这一行，成熟 API 没有可用热键路径。
        self.assertTrue(allowed["same_target"])  # 新增代码+VerifiedWindowActionsMaturity：断言热键前后同目标；如果没有这一行，热键漂移无法检测。
        self.assertGreater(allowed["input_event_count"], 0)  # 新增代码+VerifiedWindowActionsMaturity：断言安全热键生成记录事件；如果没有这一行，正例可能只是空报告。
        self.assertEqual(allowed["low_level_event_count"], 0)  # 新增代码+VerifiedWindowActionsMaturity：断言记录型测试零低层事件；如果没有这一行，自动测试可能误触真实键盘。
    # 新增代码+VerifiedWindowActionsMaturity：函数段结束，test_safe_hotkey_requires_verified_owned_window 到此结束；如果没有这个边界说明，初学者不容易看出热键身份测试范围。

    def test_target_drift_blocks_low_level_dispatch(self) -> None:  # 新增代码+VerifiedWindowActionsMaturity：函数段开始，验证目标漂移会阻断派发；如果没有这段测试，同标题不同 pid 的窗口可能被误控。
        tool = Phase70RecordingHighLevelTool()  # 新增代码+VerifiedWindowActionsMaturity：创建记录型高层工具；如果没有这一行，无法统计是否发生委托。
        runtime = WindowsGenericControlActionRuntime(high_level_tool=tool)  # 新增代码+VerifiedWindowActionsMaturity：创建通用控制动作 runtime；如果没有这一行，测试没有被测对象。
        context = self._verified_context()  # 新增代码+VerifiedWindowActionsMaturity：读取基础身份上下文；如果没有这一行，漂移上下文缺少 session/window_identity。
        context["target_identity_verification"] = self._drift_verification()  # 新增代码+VerifiedWindowActionsMaturity：替换成漂移验证报告；如果没有这一行，测试不会触发 target_drift_blocks_action。
        result = runtime.click_by_visual_point(self._window(), {"x": 50, "y": 25}, "drifted click", require_verified_identity=True, **context)  # 新增代码+VerifiedWindowActionsMaturity：尝试对漂移目标点击；如果没有这一行，漂移阻断没有动作层证据。
        self.assertTrue(result["blocked"])  # 新增代码+VerifiedWindowActionsMaturity：断言漂移会阻断；如果没有这一行，错误窗口可能继续动作。
        self.assertFalse(result["same_target"])  # 新增代码+VerifiedWindowActionsMaturity：断言漂移后不是同一目标；如果没有这一行，报告无法解释为什么阻断。
        self.assertEqual(result["decision"], "target_drift_blocks_action")  # 新增代码+VerifiedWindowActionsMaturity：断言决策码稳定；如果没有这一行，最终矩阵无法识别漂移门禁。
        self.assertEqual(result["low_level_event_count"], 0)  # 新增代码+VerifiedWindowActionsMaturity：断言漂移阻断零低层事件；如果没有这一行，阻断仍可能有副作用。
        self.assertEqual(len(tool.events), 0)  # 新增代码+VerifiedWindowActionsMaturity：断言未委托高层工具；如果没有这一行，可能先动作后发现漂移。
    # 新增代码+VerifiedWindowActionsMaturity：函数段结束，test_target_drift_blocks_low_level_dispatch 到此结束；如果没有这个边界说明，初学者不容易看出漂移阻断范围。

    def test_abort_before_dispatch_produces_zero_low_level_events(self) -> None:  # 新增代码+VerifiedWindowActionsMaturity：函数段开始，验证 abort 会在派发前阻断；如果没有这段测试，急停可能晚于动作执行。
        sender = Phase71RecordingInputSender()  # 新增代码+VerifiedWindowActionsMaturity：创建记录型 sender；如果没有这一行，无法统计是否发生输入事件。
        runtime = WindowsGenericInputActionRuntime(sender=sender)  # 新增代码+VerifiedWindowActionsMaturity：创建通用输入 runtime；如果没有这一行，测试没有被测对象。
        result = runtime.send_hotkey(self._window(), ["ctrl", "s"], require_verified_identity=True, abort_requested=True, **self._verified_context())  # 新增代码+VerifiedWindowActionsMaturity：带已验证身份但模拟 abort；如果没有这一行，急停前置门没有动作层证据。
        self.assertTrue(result["blocked"])  # 新增代码+VerifiedWindowActionsMaturity：断言 abort 会阻断；如果没有这一行，急停可能失效。
        self.assertEqual(result["decision"], "abort_before_dispatch")  # 新增代码+VerifiedWindowActionsMaturity：断言决策码稳定；如果没有这一行，终端难以解释为什么未执行。
        self.assertEqual(result["low_level_event_count"], 0)  # 新增代码+VerifiedWindowActionsMaturity：断言 abort 阻断零低层事件；如果没有这一行，急停仍可能产生输入。
        self.assertEqual(len(sender.events), 0)  # 新增代码+VerifiedWindowActionsMaturity：断言 sender 未收到事件；如果没有这一行，可能先发事件再报告 abort。
    # 新增代码+VerifiedWindowActionsMaturity：函数段结束，test_abort_before_dispatch_produces_zero_low_level_events 到此结束；如果没有这个边界说明，初学者不容易看出 abort 阻断范围。
# 新增代码+VerifiedWindowActionsMaturity：类段结束，WindowsComputerUseVerifiedWindowActionsMaturityTests 到此结束；如果没有这个边界说明，初学者不容易看出 Task6 测试集合范围。


if __name__ == "__main__":  # 新增代码+VerifiedWindowActionsMaturity：文件入口段开始，允许直接运行本测试文件；如果没有这一行，初学者必须记完整 unittest 命令。
    unittest.main()  # 新增代码+VerifiedWindowActionsMaturity：启动 unittest；如果没有这一行，直接运行文件不会执行测试。
# 新增代码+VerifiedWindowActionsMaturity：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出入口范围。
