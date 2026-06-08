import json  # 新增代码+Phase45WindowsScreenshotRuntime: 导入 JSON 用来检查验收场景；如果没有这行代码，测试无法确认真实终端场景写入了稳定 token。
import tempfile  # 新增代码+Phase45WindowsScreenshotRuntime: 导入临时目录工具隔离截图 evidence；如果没有这行代码，测试会污染真实 memory 目录。
import unittest  # 新增代码+Phase45WindowsScreenshotRuntime: 导入 unittest 框架承载 Phase45 测试；如果没有这行代码，自动化回归不会发现截图运行时问题。
from pathlib import Path  # 新增代码+Phase45WindowsScreenshotRuntime: 导入 Path 稳定处理 Windows 路径；如果没有这行代码，artifact 路径检查会变脆。

from learning_agent.computer_use.native_helper import NativeWindowCaptureResult  # 新增代码+Phase45WindowsScreenshotRuntime: 复用已有截图结果合同；如果没有这行代码，Phase45 可能创造和 GDI/WGC 不兼容的新结构。
from learning_agent.computer_use.native_host import InProcessWindowsNativeHostClient, WindowsComputerUseNativeHost  # 新增代码+Phase45WindowsScreenshotRuntime: 导入 Phase44 host 验证 capture 接入；如果没有这行代码，native host 和截图运行时可能割裂。
from learning_agent.computer_use.screenshot_runtime import PHASE45_WINDOWS_SCREENSHOT_RUNTIME_MARKER, PHASE45_WINDOWS_SCREENSHOT_RUNTIME_OK_TOKEN, WindowsScreenshotCaptureRuntime, phase45_cli_line, run_phase45_screenshot_runtime_contract  # 新增代码+Phase45WindowsScreenshotRuntime: 导入 Phase45 期望的新截图运行时；如果没有这行代码，红灯会证明生产截图层尚未实现。


class FakePhase45CaptureProvider:  # 新增代码+Phase45WindowsScreenshotRuntime: 定义可控 fake provider；如果没有这个类，测试只能触碰真实桌面截图 API。
    def __init__(self, backend: str, captured: bool, reason: str = "fake") -> None:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，初始化 fake provider；如果没有这段代码，测试无法模拟首选失败和 fallback 成功。
        self.backend = backend  # 新增代码+Phase45WindowsScreenshotRuntime: 保存 provider 名称；如果没有这行代码，运行时无法报告谁成功截图。
        self.captured = captured  # 新增代码+Phase45WindowsScreenshotRuntime: 保存是否截图成功；如果没有这行代码，测试无法切换成功/失败路径。
        self.reason = reason  # 新增代码+Phase45WindowsScreenshotRuntime: 保存 provider 原因；如果没有这行代码，失败诊断不稳定。
        self.calls: list[int] = []  # 新增代码+Phase45WindowsScreenshotRuntime: 记录调用过的 hwnd；如果没有这行代码，测试无法证明 fallback 顺序。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，FakePhase45CaptureProvider.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def status(self) -> dict[str, object]:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，返回 provider 状态；如果没有这段代码，运行时 status 无法展示 provider 链。
        return {"backend": self.backend, "available": True, "reason": self.reason, "contract_ready": True}  # 新增代码+Phase45WindowsScreenshotRuntime: 返回稳定状态；如果没有这行代码，状态测试没有输入。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，FakePhase45CaptureProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态范围。

    def capture_window(self, hwnd: int) -> NativeWindowCaptureResult:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，模拟截图调用；如果没有这段代码，运行时无法测试 provider 链。
        self.calls.append(int(hwnd))  # 新增代码+Phase45WindowsScreenshotRuntime: 记录 hwnd；如果没有这行代码，fallback 顺序无法被断言。
        if not self.captured:  # 新增代码+Phase45WindowsScreenshotRuntime: 模拟 provider 失败；如果没有这行代码，测试无法覆盖 GDI fallback。
            return NativeWindowCaptureResult(captured=False, backend=self.backend, reason=f"{self.backend} refused")  # 新增代码+Phase45WindowsScreenshotRuntime: 返回失败结果；如果没有这行代码，失败 provider 可能伪装成功。
        return NativeWindowCaptureResult(captured=True, screenshot_bytes=f"{self.backend}-bytes".encode("utf-8"), screenshot_format="png", screenshot_width=450, screenshot_height=245, backend=self.backend, reason=f"{self.backend} captured {hwnd}")  # 新增代码+Phase45WindowsScreenshotRuntime: 返回成功截图结果；如果没有这行代码，evidence store 没有图片 bytes 可写。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，FakePhase45CaptureProvider.capture_window 到此结束；如果没有这个边界说明，读者不容易看出截图 fake 范围。


class WindowsComputerUseScreenshotRuntimePhase45Tests(unittest.TestCase):  # 新增代码+Phase45WindowsScreenshotRuntime: 定义 Phase45 测试集合；如果没有这个类，unittest 不会组织截图运行时验收。
    def _window(self) -> dict[str, object]:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，提供稳定窗口输入；如果没有这段代码，各测试会重复拼接 window dict。
        return {"window_id": "hwnd:4501", "hwnd": 4501, "title": "Phase45 Window", "rect": {"left": 10, "top": 20, "right": 460, "bottom": 265}}  # 新增代码+Phase45WindowsScreenshotRuntime: 返回带 hwnd 和 rect 的窗口；如果没有这行代码，运行时无法生成 evidence metadata。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，_window 到此结束；如果没有这个边界说明，读者不容易看出窗口样本范围。

    def test_screenshot_runtime_uses_first_successful_provider_and_writes_evidence(self) -> None:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，验证首个成功 provider 会落盘 evidence；如果没有这个测试，运行时可能只返回内存 bytes。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase45WindowsScreenshotRuntime: 创建临时 evidence 目录；如果没有这行代码，测试会污染真实证据目录。
            preferred = FakePhase45CaptureProvider("windows_graphics_capture", True)  # 新增代码+Phase45WindowsScreenshotRuntime: 构造成功的首选 provider；如果没有这行代码，无法验证不走 fallback 的路径。
            fallback = FakePhase45CaptureProvider("win32_gdi_printwindow", True)  # 新增代码+Phase45WindowsScreenshotRuntime: 构造备用 provider；如果没有这行代码，无法断言首选成功时不会调用 fallback。
            runtime = WindowsScreenshotCaptureRuntime(providers=[preferred, fallback], evidence_root=Path(raw_dir), platform="win32")  # 新增代码+Phase45WindowsScreenshotRuntime: 创建截图运行时；如果没有这行代码，被测对象不存在。
            result = runtime.capture_window(self._window())  # 新增代码+Phase45WindowsScreenshotRuntime: 执行窗口截图；如果没有这行代码，断言没有实际输入。
            self.assertTrue(result["captured"])  # 新增代码+Phase45WindowsScreenshotRuntime: 断言截图成功；如果没有这行代码，空结果也可能误过。
            self.assertEqual(result["provider"], "windows_graphics_capture")  # 新增代码+Phase45WindowsScreenshotRuntime: 断言使用首选 provider；如果没有这行代码，fallback 顺序可能悄悄错误。
            self.assertEqual(fallback.calls, [])  # 新增代码+Phase45WindowsScreenshotRuntime: 断言首选成功时不调用 fallback；如果没有这行代码，运行时可能浪费或重复截图。
            self.assertTrue(Path(result["screenshot_path"]).exists())  # 新增代码+Phase45WindowsScreenshotRuntime: 断言截图 artifact 落盘；如果没有这行代码，模型可能拿到不存在的路径。
            self.assertEqual(result["screenshot_bytes_included"], False)  # 新增代码+Phase45WindowsScreenshotRuntime: 断言 JSON 不携带原始 bytes；如果没有这行代码，截图内容可能被塞进响应。
            self.assertEqual(result["image_result_count"], 1)  # 新增代码+Phase45WindowsScreenshotRuntime: 断言生成模型可见图片块；如果没有这行代码，截图可能落盘但模型不可引用。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，test_screenshot_runtime_uses_first_successful_provider_and_writes_evidence 到此结束；如果没有这个边界说明，读者不容易看出 evidence 测试范围。

    def test_screenshot_runtime_falls_back_after_preferred_failure(self) -> None:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，验证首选失败时自动 fallback；如果没有这个测试，GDI 保底路径可能不可用。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase45WindowsScreenshotRuntime: 创建临时 evidence 目录；如果没有这行代码，fallback artifact 会污染真实目录。
            preferred = FakePhase45CaptureProvider("windows_graphics_capture", False)  # 新增代码+Phase45WindowsScreenshotRuntime: 构造失败首选 provider；如果没有这行代码，fallback 路径无法触发。
            fallback = FakePhase45CaptureProvider("win32_gdi_printwindow", True)  # 新增代码+Phase45WindowsScreenshotRuntime: 构造成功 fallback provider；如果没有这行代码，运行时无法证明保底可用。
            runtime = WindowsScreenshotCaptureRuntime(providers=[preferred, fallback], evidence_root=Path(raw_dir), platform="win32")  # 新增代码+Phase45WindowsScreenshotRuntime: 创建带两级 provider 的运行时；如果没有这行代码，断言没有对象。
            result = runtime.capture_window(self._window())  # 新增代码+Phase45WindowsScreenshotRuntime: 执行截图；如果没有这行代码，fallback 不会运行。
            self.assertTrue(result["captured"])  # 新增代码+Phase45WindowsScreenshotRuntime: 断言最终截图成功；如果没有这行代码，fallback 失败也可能误过。
            self.assertEqual(result["provider"], "win32_gdi_printwindow")  # 新增代码+Phase45WindowsScreenshotRuntime: 断言 fallback provider 成为结果来源；如果没有这行代码，错误 provider 名可能污染审计。
            self.assertEqual(preferred.calls, [4501])  # 新增代码+Phase45WindowsScreenshotRuntime: 断言首选 provider 被尝试；如果没有这行代码，顺序可能绕过 WGC。
            self.assertEqual(fallback.calls, [4501])  # 新增代码+Phase45WindowsScreenshotRuntime: 断言 fallback provider 被调用；如果没有这行代码，保底路径可能没执行。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，test_screenshot_runtime_falls_back_after_preferred_failure 到此结束；如果没有这个边界说明，读者不容易看出 fallback 测试范围。

    def test_native_host_capture_can_use_screenshot_runtime_without_raw_bytes(self) -> None:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，验证 Phase44 host 可接入 Phase45 runtime；如果没有这个测试，host capture 仍停留 helper 摘要。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase45WindowsScreenshotRuntime: 创建临时 evidence 目录；如果没有这行代码，host capture 测试会污染真实目录。
            runtime = WindowsScreenshotCaptureRuntime(providers=[FakePhase45CaptureProvider("win32_gdi_printwindow", True)], evidence_root=Path(raw_dir), platform="win32")  # 新增代码+Phase45WindowsScreenshotRuntime: 创建只含 fallback 的截图运行时；如果没有这行代码，host 没有真实截图来源。
            client = InProcessWindowsNativeHostClient(WindowsComputerUseNativeHost(platform="win32", screenshot_runtime=runtime))  # 新增代码+Phase45WindowsScreenshotRuntime: 把 runtime 注入 native host；如果没有这行代码，测试无法覆盖 host 集成。
            response = client.request({"op": "capture", "window": self._window()})  # 新增代码+Phase45WindowsScreenshotRuntime: 通过 host capture 消息触发截图；如果没有这行代码，集成路径不会执行。
            self.assertTrue(response["ok"])  # 新增代码+Phase45WindowsScreenshotRuntime: 断言 host capture 成功；如果没有这行代码，host 错误可能被忽略。
            self.assertTrue(response["result"]["captured"])  # 新增代码+Phase45WindowsScreenshotRuntime: 断言 capture 结果是真的截图成功；如果没有这行代码，空摘要可能误过。
            self.assertFalse(response["result"]["screenshot_bytes_included"])  # 新增代码+Phase45WindowsScreenshotRuntime: 断言 host 响应不带原始 bytes；如果没有这行代码，IPC 响应可能泄露图片内容。
            self.assertEqual(response["result"]["provider"], "win32_gdi_printwindow")  # 新增代码+Phase45WindowsScreenshotRuntime: 断言 host 保留 provider 来源；如果没有这行代码，排查不知道截图来自哪里。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，test_native_host_capture_can_use_screenshot_runtime_without_raw_bytes 到此结束；如果没有这个边界说明，读者不容易看出 host 集成范围。

    def test_phase45_cli_contract_and_visible_terminal_scenario_tokens(self) -> None:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，验证 CLI 和真实终端场景 token；如果没有这个测试，Phase45 可能无法被最终验收。
        report = run_phase45_screenshot_runtime_contract()  # 新增代码+Phase45WindowsScreenshotRuntime: 运行安全自检合同；如果没有这行代码，CLI 行没有真实输入。
        cli_line = phase45_cli_line(report)  # 新增代码+Phase45WindowsScreenshotRuntime: 生成稳定 token 行；如果没有这行代码，场景无法复用同一格式。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase45_windows_screenshot_runtime.json")  # 新增代码+Phase45WindowsScreenshotRuntime: 定位 Phase45 场景文件；如果没有这行代码，测试无法确认真实终端配置。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase45WindowsScreenshotRuntime: 读取场景文本；如果没有这行代码，场景缺失不会暴露。
        expected_tokens = {PHASE45_WINDOWS_SCREENSHOT_RUNTIME_MARKER, PHASE45_WINDOWS_SCREENSHOT_RUNTIME_OK_TOKEN, "capture=true", "artifact=true", "fallback=true", "host_capture=true", "raw_bytes_hidden=true", "actions_expanded=false"}  # 新增代码+Phase45WindowsScreenshotRuntime: 定义 CLI 和场景都必须包含的 token；如果没有这行代码，验收标准会漂移。
        for token in expected_tokens:  # 新增代码+Phase45WindowsScreenshotRuntime: 遍历关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase45WindowsScreenshotRuntime: 断言 CLI 行包含 token；如果没有这行代码，自检输出可能不稳定。
            self.assertIn(token, scenario_text)  # 新增代码+Phase45WindowsScreenshotRuntime: 断言场景包含 token；如果没有这行代码，真实终端验收可能漏检。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，test_phase45_cli_contract_and_visible_terminal_scenario_tokens 到此结束；如果没有这个边界说明，读者不容易看出场景测试范围。


if __name__ == "__main__":  # 新增代码+Phase45WindowsScreenshotRuntime: 允许直接运行本测试文件；如果没有这行代码，初学者无法单独启动 Phase45 测试。
    unittest.main()  # 新增代码+Phase45WindowsScreenshotRuntime: 启动 unittest；如果没有这行代码，直接运行文件不会执行任何测试。
