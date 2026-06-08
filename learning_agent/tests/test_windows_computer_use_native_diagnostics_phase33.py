import json  # 新增代码+Phase33WindowsNativeDiagnostics: 导入 JSON 用来检查验收场景结构；如果没有这行代码，测试无法读取 scenario 文件内容。
import unittest  # 新增代码+Phase33WindowsNativeDiagnostics: 导入 unittest 框架承载 Phase33 测试；如果没有这行代码，自动化测试无法发现诊断能力回归。
from pathlib import Path  # 新增代码+Phase33WindowsNativeDiagnostics: 导入 Path 统一定位项目文件；如果没有这行代码，测试会依赖脆弱的字符串路径。

from learning_agent.computer_use.controller import WindowsComputerUseBackend  # 新增代码+Phase33WindowsNativeDiagnostics: 导入 Windows 后端验证状态透传；如果没有这行代码，测试无法证明 backend.status 能暴露诊断信息。
from learning_agent.computer_use.native_helper import NativeWindowCaptureResult, NativeWindowTextResult, WindowsNativeWindowObservationHelper  # 新增代码+Phase33WindowsNativeDiagnostics: 导入 Phase32 helper 和结果类型作为 Phase33 诊断入口；如果没有这行代码，测试无法覆盖 native helper 状态。
from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase33WindowsNativeDiagnostics: 导入静态窗口 inventory 避免读取真实桌面；如果没有这行代码，测试可能误触碰用户本机窗口。


class Phase33FakeCaptureProvider:  # 新增代码+Phase33WindowsNativeDiagnostics: 定义假截图 provider；如果没有这个类，测试只能依赖真实 Windows 截图能力。
    def status(self) -> dict[str, object]:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，返回假截图 provider 状态；如果没有这段函数，诊断层无法读取 active capture provider。
        return {"backend": "visible_fake_capture", "available": True, "reason": "phase33 fake capture"}  # 新增代码+Phase33WindowsNativeDiagnostics: 返回可用的假截图状态；如果没有这行代码，诊断测试无法断言 active provider 名称。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，Phase33FakeCaptureProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态函数范围。

    def capture_window(self, hwnd: int) -> NativeWindowCaptureResult:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，返回假截图结果；如果没有这段函数，helper.observe_window 无法在测试中完成截图路径。
        return NativeWindowCaptureResult(captured=True, screenshot_bytes=b"phase33-diagnostics-bmp", screenshot_format="bmp", screenshot_width=333, screenshot_height=144, backend="visible_fake_capture", reason=f"captured {hwnd}")  # 新增代码+Phase33WindowsNativeDiagnostics: 返回稳定截图结果；如果没有这行代码，窗口状态落盘无法证明诊断 provider 参与流程。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，Phase33FakeCaptureProvider.capture_window 到此结束；如果没有这个边界说明，读者不容易看出截图函数范围。


class Phase33FakeTextProvider:  # 新增代码+Phase33WindowsNativeDiagnostics: 定义假文本 provider；如果没有这个类，测试只能依赖真实 UI Automation 或 Win32 文本。
    def status(self) -> dict[str, object]:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，返回假文本 provider 状态；如果没有这段函数，诊断层无法读取 active text provider。
        return {"backend": "visible_fake_text", "available": True, "reason": "phase33 fake text"}  # 新增代码+Phase33WindowsNativeDiagnostics: 返回可用的假文本状态；如果没有这行代码，诊断测试无法断言 active text provider 名称。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，Phase33FakeTextProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态函数范围。

    def read_window_text(self, hwnd: int) -> NativeWindowTextResult:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，返回假窗口文本；如果没有这段函数，helper.observe_window 无法在测试中完成文本路径。
        return NativeWindowTextResult(captured=True, accessibility_text="安全文本", focused_element=f"edit {hwnd}", selected_text="", document_text="安全文档", backend="visible_fake_text", reason=f"text {hwnd}")  # 新增代码+Phase33WindowsNativeDiagnostics: 返回稳定文本结果；如果没有这行代码，窗口状态无法证明文本 provider 参与流程。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，Phase33FakeTextProvider.read_window_text 到此结束；如果没有这个边界说明，读者不容易看出文本函数范围。


class WindowsComputerUseNativeDiagnosticsPhase33Tests(unittest.TestCase):  # 新增代码+Phase33WindowsNativeDiagnostics: 定义 Phase33 测试集合；如果没有这个类，unittest 不会组织 native diagnostics 测试。
    def _helper(self) -> WindowsNativeWindowObservationHelper:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，构造带 fake provider 的 helper；如果没有这段函数，每个测试都要重复搭建对象。
        return WindowsNativeWindowObservationHelper(capture_provider=Phase33FakeCaptureProvider(), text_provider=Phase33FakeTextProvider(), platform="win32")  # 新增代码+Phase33WindowsNativeDiagnostics: 返回模拟 Windows helper；如果没有这行代码，测试可能触发真实 Windows API。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，_helper 到此结束；如果没有这个边界说明，读者不容易看出 helper 构造范围。

    def test_helper_status_exposes_phase33_provider_diagnostics(self) -> None:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，验证 helper.status 暴露 provider 诊断；如果没有这个测试，Phase33 状态可能继续停留在 Phase32 粗略说明。
        status = self._helper().status()  # 新增代码+Phase33WindowsNativeDiagnostics: 读取 helper 状态；如果没有这行代码，测试无法拿到诊断对象。
        diagnostics = status["diagnostics"]  # 新增代码+Phase33WindowsNativeDiagnostics: 读取 Phase33 diagnostics 字段；如果没有这行代码，缺失诊断字段不会被明确发现。
        capture_names = [provider["name"] for provider in diagnostics["capture"]["providers"]]  # 新增代码+Phase33WindowsNativeDiagnostics: 收集截图 provider 链名称；如果没有这行代码，测试无法确认 WGC 被纳入优先级认知。
        text_names = [provider["name"] for provider in diagnostics["text"]["providers"]]  # 新增代码+Phase33WindowsNativeDiagnostics: 收集文本 provider 链名称；如果没有这行代码，测试无法确认 UI Automation 被纳入优先级认知。
        self.assertEqual(diagnostics["diagnostics_version"], "phase33_windows_native_diagnostics")  # 新增代码+Phase33WindowsNativeDiagnostics: 断言诊断版本稳定；如果没有这行代码，后续状态消费者无法区分 Phase32/Phase33。
        self.assertIn("windows_graphics_capture", capture_names)  # 新增代码+Phase33WindowsNativeDiagnostics: 断言 WGC 进入截图能力链；如果没有这行代码，agent 不知道首选截图能力缺口。
        self.assertIn("win32_gdi_printwindow", capture_names)  # 新增代码+Phase33WindowsNativeDiagnostics: 断言 GDI fallback 仍可见；如果没有这行代码，用户不知道当前 fallback 来源。
        self.assertIn("uiautomation_client", text_names)  # 新增代码+Phase33WindowsNativeDiagnostics: 断言 UI Automation 进入文本能力链；如果没有这行代码，agent 不知道完整控件树缺口。
        self.assertIn("win32_window_text", text_names)  # 新增代码+Phase33WindowsNativeDiagnostics: 断言 Win32 文本 fallback 仍可见；如果没有这行代码，用户不知道当前文本 fallback 来源。
        self.assertEqual(diagnostics["capture"]["active_provider"], "visible_fake_capture")  # 新增代码+Phase33WindowsNativeDiagnostics: 断言 active 截图 provider 被识别；如果没有这行代码，状态只会说可用但不知道谁可用。
        self.assertEqual(diagnostics["text"]["active_provider"], "visible_fake_text")  # 新增代码+Phase33WindowsNativeDiagnostics: 断言 active 文本 provider 被识别；如果没有这行代码，状态只会说可用但不知道谁可用。
        self.assertTrue(diagnostics["safe_observe_only"])  # 新增代码+Phase33WindowsNativeDiagnostics: 断言 Phase33 仍是只读观察；如果没有这行代码，诊断增强可能误扩大动作能力。
        self.assertFalse(diagnostics["real_input_actions_expanded"])  # 新增代码+Phase33WindowsNativeDiagnostics: 断言没有新增真实输入动作；如果没有这行代码，Phase33 边界可能被误解。
        self.assertEqual(diagnostics["native_observe_opt_in_env_var"], "LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE")  # 新增代码+Phase33WindowsNativeDiagnostics: 断言状态说明 native opt-in 开关；如果没有这行代码，用户不知道如何安全启用诊断链。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，test_helper_status_exposes_phase33_provider_diagnostics 到此结束；如果没有这个边界说明，读者不容易看出诊断测试范围。

    def test_windows_backend_status_exposes_phase33_diagnostics(self) -> None:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，验证 Windows 后端状态透传 diagnostics；如果没有这个测试，/computer 状态可能看不到 Phase33 信息。
        raw_windows = [{"hwnd": 3301, "pid": 1, "process_name": "notepad.exe", "class_name": "Notepad", "title": "Phase33", "rect": {"left": 1, "top": 2, "right": 301, "bottom": 202}}]  # 新增代码+Phase33WindowsNativeDiagnostics: 准备静态窗口样本；如果没有这行代码，后端测试会读取真实桌面。
        inventory = StaticWindowsWindowInventory(raw_windows=raw_windows, captured_at="2026-06-03T00:00:00Z")  # 新增代码+Phase33WindowsNativeDiagnostics: 创建静态 inventory；如果没有这行代码，backend.status 无法在测试中稳定运行。
        backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False, observation_helper=self._helper())  # 新增代码+Phase33WindowsNativeDiagnostics: 创建只读 Windows 后端并注入 helper；如果没有这行代码，状态透传无法被覆盖。
        status = backend.status()  # 新增代码+Phase33WindowsNativeDiagnostics: 读取后端状态；如果没有这行代码，测试无法检查 native_observation_diagnostics。
        diagnostics = status["native_observation_diagnostics"]  # 新增代码+Phase33WindowsNativeDiagnostics: 读取后端透传的诊断对象；如果没有这行代码，缺失透传不会被明确发现。
        self.assertEqual(diagnostics["diagnostics_version"], "phase33_windows_native_diagnostics")  # 新增代码+Phase33WindowsNativeDiagnostics: 断言后端透传的诊断版本正确；如果没有这行代码，状态消费者可能拿到旧结构。
        self.assertEqual(diagnostics["capture"]["active_provider"], "visible_fake_capture")  # 新增代码+Phase33WindowsNativeDiagnostics: 断言后端保留 active 截图 provider；如果没有这行代码，透传可能丢失具体 provider。
        self.assertFalse(diagnostics["real_input_actions_expanded"])  # 新增代码+Phase33WindowsNativeDiagnostics: 断言后端状态没有扩大真实输入动作；如果没有这行代码，用户可能误以为 Phase33 加了鼠标键盘。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，test_windows_backend_status_exposes_phase33_diagnostics 到此结束；如果没有这个边界说明，读者不容易看出后端状态测试范围。

    def test_phase33_visible_terminal_scenario_documents_diagnostics_markers(self) -> None:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，验证真实终端验收场景包含 Phase33 标记；如果没有这个测试，场景漏掉关键断言也不容易发现。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase33WindowsNativeDiagnostics: 定位项目根目录；如果没有这行代码，测试无法稳定找到 scenario 文件。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase33_windows_native_diagnostics.json"  # 新增代码+Phase33WindowsNativeDiagnostics: 定位 Phase33 验收场景；如果没有这行代码，测试可能检查错文件。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase33WindowsNativeDiagnostics: 读取并解析场景 JSON；如果没有这行代码，JSON 格式错误不会被发现。
        prompt_text = " ".join(scenario["prompt_lines"])  # 新增代码+Phase33WindowsNativeDiagnostics: 合并 prompt 便于检查命令内容；如果没有这行代码，测试要逐行重复查找。
        expected_tokens = {"PHASE33_WINDOWS_NATIVE_DIAGNOSTICS_OK", "phase=phase33_windows_native_diagnostics", "wgc_known=true", "uia_known=true", "active_capture=visible_fake_capture", "active_text=visible_fake_text", "actions_expanded=false"}  # 新增代码+Phase33WindowsNativeDiagnostics: 列出验收必须出现的 token；如果没有这行代码，场景可能只有空成功标记。
        self.assertIn("diagnostics", prompt_text)  # 新增代码+Phase33WindowsNativeDiagnostics: 断言场景命令真正检查 diagnostics；如果没有这行代码，验收可能绕过 Phase33 能力。
        for token in expected_tokens:  # 新增代码+Phase33WindowsNativeDiagnostics: 遍历必须检查的 token；如果没有这行代码，断言会散落且容易漏项。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase33WindowsNativeDiagnostics: 断言 debug log 检查包含 token；如果没有这行代码，终端日志可能漏验证。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase33WindowsNativeDiagnostics: 断言最终回答检查包含 token；如果没有这行代码，用户可见答案可能漏证据。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，test_phase33_visible_terminal_scenario_documents_diagnostics_markers 到此结束；如果没有这个边界说明，读者不容易看出场景测试范围。


if __name__ == "__main__":  # 新增代码+Phase33WindowsNativeDiagnostics: 允许直接运行本测试文件；如果没有这行代码，初学者无法单独执行 Phase33 测试。
    unittest.main()  # 新增代码+Phase33WindowsNativeDiagnostics: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
