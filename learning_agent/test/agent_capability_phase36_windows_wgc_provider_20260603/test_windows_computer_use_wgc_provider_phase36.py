import json  # 新增代码+Phase36WindowsWGCProvider: 导入 JSON 用来读取验收场景；如果没有这行代码，测试无法确认真实终端场景检查哪些稳定标记。
import unittest  # 新增代码+Phase36WindowsWGCProvider: 导入 unittest 框架承载 Phase36 测试；如果没有这行代码，自动化回归发现不了 WGC provider 合同问题。
from pathlib import Path  # 新增代码+Phase36WindowsWGCProvider: 导入 Path 稳定定位项目文件；如果没有这行代码，测试会依赖脆弱字符串路径。

from learning_agent.computer_use.native_diagnostics import WindowsNativeObservationDiagnostics  # 新增代码+Phase36WindowsWGCProvider: 导入 native diagnostics 验证 WGC 合同进入诊断链；如果没有这行代码，状态页对齐不会被测试覆盖。
from learning_agent.computer_use.native_helper import NativeWindowCaptureResult  # 新增代码+Phase36WindowsWGCProvider: 导入统一截图结果合同；如果没有这行代码，WGC provider 可能返回和 GDI 不兼容的结构。
from learning_agent.computer_use.wgc_capture import PHASE36_WINDOWS_WGC_PROVIDER_MARKER, PHASE36_WINDOWS_WGC_PROVIDER_OK_TOKEN, WindowsGraphicsCaptureProvider, phase36_dependency_status  # 新增代码+Phase36WindowsWGCProvider: 导入 Phase36 预期入口；如果没有这行代码，红灯测试无法证明 WGC provider 尚未实现。


class Phase36FakeTextProvider:  # 新增代码+Phase36WindowsWGCProvider: 定义 fake 文本 provider 用于 diagnostics；如果没有这个类，诊断测试需要真实 UIA 文本依赖。
    def status(self) -> dict[str, object]:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，返回 fake 文本状态；如果没有这段函数，diagnostics 无法构造 active text provider。
        return {"backend": "phase36_fake_text", "available": True, "reason": "phase36 fake text"}  # 新增代码+Phase36WindowsWGCProvider: 返回稳定 fake 文本状态；如果没有这行代码，诊断测试会混入真实文本 provider 状态。
    # 新增代码+Phase36WindowsWGCProvider: 函数段结束，Phase36FakeTextProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态函数范围。


class WindowsComputerUseWgcProviderPhase36Tests(unittest.TestCase):  # 新增代码+Phase36WindowsWGCProvider: 定义 Phase36 测试集合；如果没有这个类，unittest 不会组织 WGC provider 合同测试。
    def test_dependency_status_reports_missing_wgc_bindings(self) -> None:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，验证缺少 WGC 绑定时诚实报告；如果没有这个测试，缺依赖可能被误报为可截图。
        status = phase36_dependency_status(module_available=lambda name: False, platform="win32")  # 新增代码+Phase36WindowsWGCProvider: 模拟 Windows 但缺少 WGC 绑定；如果没有这行代码，缺依赖路径不会被覆盖。
        self.assertTrue(status["dependency_reported"])  # 新增代码+Phase36WindowsWGCProvider: 断言依赖状态已报告；如果没有这行代码，验收无法区分没检查和缺依赖。
        self.assertFalse(status["dependency_available"])  # 新增代码+Phase36WindowsWGCProvider: 断言 WGC 依赖不可用；如果没有这行代码，测试可能误过可用路径。
        self.assertEqual(status["preferred_binding"], "winrt.windows.graphics.capture|winsdk.windows.graphics.capture")  # 新增代码+Phase36WindowsWGCProvider: 断言依赖名称稳定；如果没有这行代码，用户不知道该补哪类绑定。
    # 新增代码+Phase36WindowsWGCProvider: 函数段结束，test_dependency_status_reports_missing_wgc_bindings 到此结束；如果没有这个边界说明，读者不容易看出依赖测试范围。

    def test_provider_refuses_missing_dependency_without_fake_capture(self) -> None:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，验证缺依赖时不伪造截图；如果没有这个测试，provider 可能用假图冒充 WGC。
        provider = WindowsGraphicsCaptureProvider(platform="win32", module_available=lambda name: False)  # 新增代码+Phase36WindowsWGCProvider: 构造缺依赖 WGC provider；如果没有这行代码，测试无法观察 provider 状态。
        status = provider.status()  # 新增代码+Phase36WindowsWGCProvider: 读取 provider 状态；如果没有这行代码，断言没有输入。
        result = provider.capture_window(3601)  # 新增代码+Phase36WindowsWGCProvider: 尝试截图以覆盖拒绝路径；如果没有这行代码，缺依赖时 capture_window 逻辑不会被测试。
        self.assertEqual(status["backend"], "windows_graphics_capture")  # 新增代码+Phase36WindowsWGCProvider: 断言 provider 名称稳定；如果没有这行代码，诊断链可能识别错后端。
        self.assertTrue(status["contract_ready"])  # 新增代码+Phase36WindowsWGCProvider: 断言合同入口已建立；如果没有这行代码，Phase36 可能只是诊断文字。
        self.assertFalse(status["available"])  # 新增代码+Phase36WindowsWGCProvider: 断言缺依赖时不可用；如果没有这行代码，真实截图能力会被虚报。
        self.assertFalse(result.captured)  # 新增代码+Phase36WindowsWGCProvider: 断言没有返回伪造截图；如果没有这行代码，fake 截图可能污染 evidence。
        self.assertEqual(result.backend, "windows_graphics_capture")  # 新增代码+Phase36WindowsWGCProvider: 断言失败结果仍保留后端名；如果没有这行代码，排查不知道失败来自哪里。
    # 新增代码+Phase36WindowsWGCProvider: 函数段结束，test_provider_refuses_missing_dependency_without_fake_capture 到此结束；如果没有这个边界说明，读者不容易看出拒绝路径范围。

    def test_provider_uses_injected_capture_impl_when_dependency_exists(self) -> None:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，验证依赖存在且注入实现时可返回统一截图结果；如果没有这个测试，WGC 合同成功路径不稳定。
        def capture_impl(hwnd: int) -> dict[str, object]:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，模拟真实 WGC 截图实现；如果没有这段函数，单元测试只能依赖本机 WGC 绑定。
            return {"captured": True, "screenshot_bytes": b"phase36-wgc-png", "screenshot_format": "png", "screenshot_width": 640, "screenshot_height": 360, "reason": f"captured {hwnd}"}  # 新增代码+Phase36WindowsWGCProvider: 返回可转换的截图 dict；如果没有这行代码，provider 转换逻辑无法被覆盖。
        # 新增代码+Phase36WindowsWGCProvider: 函数段结束，capture_impl 到此结束；如果没有这个边界说明，读者不容易看出 fake 截图实现范围。
        provider = WindowsGraphicsCaptureProvider(platform="win32", module_available=lambda name: True, capture_impl=capture_impl)  # 新增代码+Phase36WindowsWGCProvider: 构造依赖可用并注入实现的 provider；如果没有这行代码，成功路径无法被触发。
        result = provider.capture_window(3602)  # 新增代码+Phase36WindowsWGCProvider: 执行一次截图合同调用；如果没有这行代码，结果转换不会发生。
        self.assertTrue(result.captured)  # 新增代码+Phase36WindowsWGCProvider: 断言截图成功；如果没有这行代码，空结果也可能误过。
        self.assertEqual(result.screenshot_format, "png")  # 新增代码+Phase36WindowsWGCProvider: 断言格式来自实现；如果没有这行代码，artifact 后缀可能不稳定。
        self.assertEqual(result.screenshot_width, 640)  # 新增代码+Phase36WindowsWGCProvider: 断言宽度进入统一合同；如果没有这行代码，窗口状态可能拿不到尺寸。
        self.assertEqual(result.backend, "windows_graphics_capture")  # 新增代码+Phase36WindowsWGCProvider: 断言后端名被统一覆盖；如果没有这行代码，注入实现名称可能污染诊断。
    # 新增代码+Phase36WindowsWGCProvider: 函数段结束，test_provider_uses_injected_capture_impl_when_dependency_exists 到此结束；如果没有这个边界说明，读者不容易看出成功路径范围。

    def test_native_diagnostics_exposes_phase36_wgc_contract(self) -> None:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，验证 WGC provider 合同进入 diagnostics；如果没有这个测试，/computer 状态可能仍停留 Phase33 文案。
        provider = WindowsGraphicsCaptureProvider(platform="win32", module_available=lambda name: False)  # 新增代码+Phase36WindowsWGCProvider: 构造当前环境缺依赖的 WGC provider；如果没有这行代码，diagnostics 没有 Phase36 capture provider。
        diagnostics = WindowsNativeObservationDiagnostics(capture_provider=provider, text_provider=Phase36FakeTextProvider(), platform="win32").status()  # 新增代码+Phase36WindowsWGCProvider: 构造并读取诊断状态；如果没有这行代码，WGC 合同是否可见无法断言。
        wgc = next(item for item in diagnostics["capture"]["providers"] if item["name"] == "windows_graphics_capture")  # 新增代码+Phase36WindowsWGCProvider: 找到 WGC provider 项；如果没有这行代码，后续断言不知道检查哪个 provider。
        self.assertEqual(diagnostics["capture"]["active_provider"], "windows_graphics_capture")  # 新增代码+Phase36WindowsWGCProvider: 断言 active capture 已是 Phase36 WGC provider；如果没有这行代码，默认仍可能只显示 GDI fallback。
        self.assertEqual(wgc["contract"], "phase36_windows_graphics_capture_provider")  # 新增代码+Phase36WindowsWGCProvider: 断言诊断项暴露 Phase36 合同；如果没有这行代码，状态消费者无法区分 Phase33 占位和 Phase36 provider。
        self.assertTrue(wgc["dependency_reported"])  # 新增代码+Phase36WindowsWGCProvider: 断言 WGC 依赖状态进入诊断；如果没有这行代码，用户不知道缺口在哪里。
        self.assertTrue(wgc["fallback_required"])  # 新增代码+Phase36WindowsWGCProvider: 断言当前环境需要 fallback；如果没有这行代码，缺依赖可能被误当可用。
    # 新增代码+Phase36WindowsWGCProvider: 函数段结束，test_native_diagnostics_exposes_phase36_wgc_contract 到此结束；如果没有这个边界说明，读者不容易看出 diagnostics 测试范围。

    def test_phase36_visible_terminal_scenario_documents_wgc_markers(self) -> None:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，验证真实终端场景包含 Phase36 标记；如果没有这个测试，场景漏检不会自动暴露。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase36WindowsWGCProvider: 定位项目根目录；如果没有这行代码，测试无法稳定找到 scenario。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase36_windows_wgc_provider.json"  # 新增代码+Phase36WindowsWGCProvider: 定位 Phase36 场景文件；如果没有这行代码，测试可能检查错场景。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase36WindowsWGCProvider: 读取 JSON 场景；如果没有这行代码，场景格式错误不会被发现。
        prompt_text = " ".join(scenario["prompt_lines"])  # 新增代码+Phase36WindowsWGCProvider: 合并 prompt 文本便于检查命令；如果没有这行代码，断言会重复处理列表。
        expected_tokens = {PHASE36_WINDOWS_WGC_PROVIDER_MARKER, PHASE36_WINDOWS_WGC_PROVIDER_OK_TOKEN, "dependency_reported=true", "capture_contract_ready=true", "fallback_required=true", "actions_expanded=false"}  # 新增代码+Phase36WindowsWGCProvider: 定义必须出现的验收 token；如果没有这行代码，场景可能只检查空泛成功。
        self.assertIn("learning_agent.computer_use.wgc_capture", prompt_text)  # 新增代码+Phase36WindowsWGCProvider: 断言场景调用 Phase36 模块；如果没有这行代码，验收可能绕过新 provider。
        for token in expected_tokens:  # 新增代码+Phase36WindowsWGCProvider: 遍历必需 token；如果没有这行代码，断言会分散且容易漏项。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase36WindowsWGCProvider: 断言 debug log 检查包含 token；如果没有这行代码，工具输出可能漏验。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase36WindowsWGCProvider: 断言最终回答检查包含 token；如果没有这行代码，用户可见结果可能漏证据。
    # 新增代码+Phase36WindowsWGCProvider: 函数段结束，test_phase36_visible_terminal_scenario_documents_wgc_markers 到此结束；如果没有这个边界说明，读者不容易看出场景测试范围。


if __name__ == "__main__":  # 新增代码+Phase36WindowsWGCProvider: 允许直接运行本测试文件；如果没有这行代码，初学者无法单独执行 Phase36 测试。
    unittest.main()  # 新增代码+Phase36WindowsWGCProvider: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
