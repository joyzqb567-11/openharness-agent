import json  # 新增代码+Phase32WindowsNativeHelper: 导入 JSON 用于检查 metadata 是否包含 native helper 证据；如果没有这行代码，测试无法读取落盘证据内容。
import tempfile  # 新增代码+Phase32WindowsNativeHelper: 导入临时目录工具隔离 evidence 文件；如果没有这行代码，测试会污染真实 memory 目录。
import unittest  # 新增代码+Phase32WindowsNativeHelper: 导入 unittest 框架承载 Phase32 测试；如果没有这行代码，自动化测试无法发现 native helper 回归。
from pathlib import Path  # 新增代码+Phase32WindowsNativeHelper: 导入 Path 统一处理 Windows 路径；如果没有这行代码，证据路径检查会更脆弱。
from unittest import mock  # 新增代码+Phase32WindowsNativeHelper: 导入 mock 用于模拟 Windows 平台开关；如果没有这行代码，默认后端 opt-in 测试会依赖真实机器环境。

from learning_agent.computer_use.controller import COMPUTER_USE_NATIVE_OBSERVE_OPT_IN_ENV_VAR, COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR, ComputerUseController, WindowsComputerUseBackend, build_default_computer_use_backend  # 新增代码+Phase32WindowsNativeHelper: 导入后端、控制器和 Phase32 opt-in 常量；如果没有这行代码，测试无法覆盖生产入口。
from learning_agent.computer_use.evidence import ComputerUseEvidenceStore  # 新增代码+Phase32WindowsNativeHelper: 导入 evidence store；如果没有这行代码，测试无法验证 native helper 输出会落盘。
from learning_agent.computer_use.native_helper import NativeWindowCaptureResult, NativeWindowTextResult, WindowsNativeWindowObservationHelper, parse_hwnd_from_window  # 新增代码+Phase32WindowsNativeHelper: 导入 Phase32 native helper 期望接口；如果没有这行代码，红灯无法证明模块缺失。
from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase32WindowsNativeHelper: 导入静态 inventory 避免读取真实桌面；如果没有这行代码，测试会依赖本机窗口。


class FakeCaptureProvider:  # 新增代码+Phase32WindowsNativeHelper: 定义假的截图 provider；如果没有这个类，测试只能触碰真实 Windows 截图 API。
    def status(self) -> dict[str, object]:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，返回 fake 截图 provider 状态；如果没有这段函数，helper.status 无法展示截图来源。
        return {"backend": "fake_capture", "available": True, "reason": "unit test capture"}  # 新增代码+Phase32WindowsNativeHelper: 返回稳定 fake 状态；如果没有这行代码，测试无法断言 provider 状态进入 helper。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，FakeCaptureProvider.status 到此结束；如果没有这个边界说明，初学者不容易看出状态函数范围。

    def capture_window(self, hwnd: int) -> NativeWindowCaptureResult:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，返回 fake 截图结果；如果没有这段函数，helper 无法生成截图 payload。
        return NativeWindowCaptureResult(captured=True, screenshot_bytes=b"phase32-native-bmp", screenshot_format="bmp", screenshot_width=222, screenshot_height=111, backend="fake_capture", reason=f"captured hwnd {hwnd}")  # 新增代码+Phase32WindowsNativeHelper: 返回带尺寸和字节的截图结果；如果没有这行代码，evidence store 无法证明 native 截图合同。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，FakeCaptureProvider.capture_window 到此结束；如果没有这个边界说明，读者不容易看出截图 fake 范围。


class FakeTextProvider:  # 新增代码+Phase32WindowsNativeHelper: 定义假的文本 provider；如果没有这个类，测试只能依赖真实 UIAutomationClient 或 Win32 文本。
    def status(self) -> dict[str, object]:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，返回 fake 文本 provider 状态；如果没有这段函数，helper.status 无法展示文本来源。
        return {"backend": "fake_text", "available": True, "reason": "unit test text"}  # 新增代码+Phase32WindowsNativeHelper: 返回稳定 fake 文本状态；如果没有这行代码，测试无法断言 provider 状态进入 helper。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，FakeTextProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态函数范围。

    def read_window_text(self, hwnd: int) -> NativeWindowTextResult:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，返回 fake 文本结果；如果没有这段函数，helper 无法生成 UI 摘要 payload。
        return NativeWindowTextResult(captured=True, accessibility_text="标题 安全文本\npassword: hidden\n按钮 确定", focused_element=f"hwnd {hwnd} edit", selected_text="安全选择", document_text="安全文档", backend="fake_text", reason="fake text captured")  # 新增代码+Phase32WindowsNativeHelper: 返回含敏感行的文本以验证后续脱敏；如果没有这行代码，测试无法覆盖文本过滤。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，FakeTextProvider.read_window_text 到此结束；如果没有这个边界说明，读者不容易看出文本 fake 范围。


class WindowsComputerUseNativeHelperPhase32Tests(unittest.TestCase):  # 新增代码+Phase32WindowsNativeHelper: 定义 Phase32 测试集合；如果没有这个类，unittest 不会组织 native helper 测试。
    def _raw_windows(self) -> list[dict[str, object]]:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，提供稳定窗口样本；如果没有这段函数，每个测试都要重复写窗口字段。
        return [{"hwnd": 3201, "pid": 100, "process_name": "notepad.exe", "class_name": "Notepad", "title": "Phase32 Notepad", "rect": {"left": 50, "top": 60, "right": 350, "bottom": 260}}]  # 新增代码+Phase32WindowsNativeHelper: 返回安全静态窗口；如果没有这行代码，native helper 证据无法绑定可信窗口。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，_raw_windows 到此结束；如果没有这个边界说明，读者不容易看出窗口样本范围。

    def _native_helper(self) -> WindowsNativeWindowObservationHelper:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，构造带 fake provider 的 native helper；如果没有这段函数，测试搭建会重复且容易漏配置。
        return WindowsNativeWindowObservationHelper(capture_provider=FakeCaptureProvider(), text_provider=FakeTextProvider(), platform="win32")  # 新增代码+Phase32WindowsNativeHelper: 返回模拟 Windows 可用 helper；如果没有这行代码，测试会触碰真实 API。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，_native_helper 到此结束；如果没有这个边界说明，读者不容易看出 helper 构造范围。

    def test_parse_hwnd_from_window_accepts_hwnd_window_id(self) -> None:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，验证窗口 id 能解析成 hwnd；如果没有这个测试，native helper 可能不知道要观察哪个窗口句柄。
        self.assertEqual(parse_hwnd_from_window({"window_id": "hwnd:3201"}), 3201)  # 新增代码+Phase32WindowsNativeHelper: 断言标准 hwnd 字符串可解析；如果没有这行代码，Phase28 window_id 合同可能无法复用。
        self.assertEqual(parse_hwnd_from_window({"hwnd": 3202}), 3202)  # 新增代码+Phase32WindowsNativeHelper: 断言原始 hwnd 字段也可解析；如果没有这行代码，真实/静态 raw 窗口不能直接观察。
        self.assertEqual(parse_hwnd_from_window({"window_id": "bad"}), 0)  # 新增代码+Phase32WindowsNativeHelper: 断言坏 id 返回 0；如果没有这行代码，坏窗口可能触发真实 API 调用。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，test_parse_hwnd_from_window_accepts_hwnd_window_id 到此结束；如果没有这个边界说明，读者不容易看出解析测试范围。

    def test_native_helper_uses_injected_capture_and_text_providers(self) -> None:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，验证 native helper 合并截图和文本 provider；如果没有这个测试，helper 可能只接截图或只接文本。
        payload = self._native_helper().observe_window({"window_id": "hwnd:3201"})  # 新增代码+Phase32WindowsNativeHelper: 执行一次 fake native 观察；如果没有这行代码，无法触发 provider 合并逻辑。
        self.assertTrue(payload.helper_available)  # 新增代码+Phase32WindowsNativeHelper: 断言 helper 可用；如果没有这行代码，status 可能误报不可用。
        self.assertEqual(payload.helper_name, "windows_native_observation")  # 新增代码+Phase32WindowsNativeHelper: 断言 helper 名称稳定；如果没有这行代码，状态和 evidence 来源不可追踪。
        self.assertEqual(payload.screenshot_bytes, b"phase32-native-bmp")  # 新增代码+Phase32WindowsNativeHelper: 断言截图字节来自 provider；如果没有这行代码，截图保存链路可能为空。
        self.assertEqual(payload.screenshot_format, "bmp")  # 新增代码+Phase32WindowsNativeHelper: 断言截图格式来自 provider；如果没有这行代码，evidence 文件后缀可能错误。
        self.assertEqual(payload.screenshot_width, 222)  # 新增代码+Phase32WindowsNativeHelper: 断言截图宽度来自 provider；如果没有这行代码，窗口状态可能继续使用 rect 占位。
        self.assertEqual(payload.screenshot_height, 111)  # 新增代码+Phase32WindowsNativeHelper: 断言截图高度来自 provider；如果没有这行代码，窗口状态可能继续使用 rect 占位。
        self.assertIn("password", payload.accessibility_text.lower())  # 新增代码+Phase32WindowsNativeHelper: 断言原始 provider 文本进入 payload 后仍交给 evidence store 过滤；如果没有这行代码，后续过滤测试失去目标。
        self.assertIn("fake_capture", payload.helper_reason)  # 新增代码+Phase32WindowsNativeHelper: 断言截图 provider 原因进入 helper_reason；如果没有这行代码，排查截图来源会困难。
        self.assertIn("fake_text", payload.helper_reason)  # 新增代码+Phase32WindowsNativeHelper: 断言文本 provider 原因进入 helper_reason；如果没有这行代码，排查文本来源会困难。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，test_native_helper_uses_injected_capture_and_text_providers 到此结束；如果没有这个边界说明，读者不容易看出 provider 合并测试范围。

    def test_native_helper_refuses_non_windows_or_invalid_hwnd(self) -> None:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，验证 helper 在非 Windows 或坏 hwnd 时不触碰系统 API；如果没有这个测试，跨平台运行可能崩溃。
        non_windows = WindowsNativeWindowObservationHelper(capture_provider=FakeCaptureProvider(), text_provider=FakeTextProvider(), platform="linux").observe_window({"window_id": "hwnd:3201"})  # 新增代码+Phase32WindowsNativeHelper: 模拟非 Windows 平台观察；如果没有这行代码，平台拒绝路径不会被覆盖。
        invalid_hwnd = self._native_helper().observe_window({"window_id": "not-a-hwnd"})  # 新增代码+Phase32WindowsNativeHelper: 使用坏窗口 id 观察；如果没有这行代码，坏 hwnd 拒绝路径不会被覆盖。
        self.assertFalse(non_windows.helper_available)  # 新增代码+Phase32WindowsNativeHelper: 断言非 Windows helper 不可用；如果没有这行代码，非 Windows 可能误报可捕获。
        self.assertFalse(invalid_hwnd.helper_available)  # 新增代码+Phase32WindowsNativeHelper: 断言坏 hwnd helper 不可用；如果没有这行代码，真实 API 可能收到 0 句柄。
        self.assertEqual(non_windows.screenshot_bytes, b"")  # 新增代码+Phase32WindowsNativeHelper: 断言非 Windows 不返回截图；如果没有这行代码，跨平台 fake 可能掩盖真实不可用。
        self.assertEqual(invalid_hwnd.accessibility_text, "")  # 新增代码+Phase32WindowsNativeHelper: 断言坏 hwnd 不返回文本；如果没有这行代码，错误目标可能产生误导证据。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，test_native_helper_refuses_non_windows_or_invalid_hwnd 到此结束；如果没有这个边界说明，读者不容易看出拒绝测试范围。

    def test_windows_backend_saves_native_helper_artifacts_and_filters_text(self) -> None:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，验证 Windows 后端能把 native helper 输出落盘；如果没有这个测试，helper 可能没有接入 get_window_state。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase32WindowsNativeHelper: 创建临时 evidence 目录；如果没有这行代码，测试会污染真实 memory 目录。
            inventory = StaticWindowsWindowInventory(raw_windows=self._raw_windows(), captured_at="2026-06-03T00:00:00Z")  # 新增代码+Phase32WindowsNativeHelper: 创建静态窗口 inventory；如果没有这行代码，测试会读取真实桌面窗口。
            store = ComputerUseEvidenceStore(evidence_root=Path(temp_dir))  # 新增代码+Phase32WindowsNativeHelper: 创建证据仓库；如果没有这行代码，native 输出不会落到可检查文件。
            backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False, evidence_store=store, observation_helper=self._native_helper())  # 新增代码+Phase32WindowsNativeHelper: 创建只读后端并注入 native helper；如果没有这行代码，get_window_state 仍会使用空 helper。
            controller = ComputerUseController(backend=backend)  # 新增代码+Phase32WindowsNativeHelper: 用统一控制器执行 observe；如果没有这行代码，测试会绕过审计入口。
            window = controller.observe({"action": "list_windows"}).data["windows"][0]  # 新增代码+Phase32WindowsNativeHelper: 获取可信窗口引用；如果没有这行代码，状态查询会使用伪造窗口。
            state = controller.observe({"action": "get_window_state", "window": window}).data["state"]  # 新增代码+Phase32WindowsNativeHelper: 调用窗口状态观察；如果没有这行代码，native helper 输出不会保存。
            metadata = json.loads(Path(state["evidence_path"]).read_text(encoding="utf-8"))  # 新增代码+Phase32WindowsNativeHelper: 读取 metadata 检查脱敏；如果没有这行代码，只能检查内存响应。
            self.assertTrue(Path(state["screenshot_path"]).exists())  # 新增代码+Phase32WindowsNativeHelper: 断言 native 截图 artifact 落盘；如果没有这行代码，截图缺失不会失败。
            self.assertEqual(state["helper_name"], "windows_native_observation")  # 新增代码+Phase32WindowsNativeHelper: 断言状态标记 native helper 来源；如果没有这行代码，用户不知道证据来自 native 桥。
            self.assertTrue(state["helper_available"])  # 新增代码+Phase32WindowsNativeHelper: 断言 native helper 可用；如果没有这行代码，后端状态可能误报。
            self.assertEqual(state["screenshot_width"], 222)  # 新增代码+Phase32WindowsNativeHelper: 断言截图宽度使用 native provider；如果没有这行代码，旧几何尺寸可能误通过。
            self.assertNotIn("password", state["accessibility_excerpt"].lower())  # 新增代码+Phase32WindowsNativeHelper: 断言响应过滤敏感文本；如果没有这行代码，native 文本可能泄露。
            self.assertNotIn("password", json.dumps(metadata, ensure_ascii=False).lower())  # 新增代码+Phase32WindowsNativeHelper: 断言 metadata 也过滤敏感文本；如果没有这行代码，磁盘 artifact 可能泄露。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，test_windows_backend_saves_native_helper_artifacts_and_filters_text 到此结束；如果没有这个边界说明，读者不容易看出落盘测试范围。

    def test_default_backend_requires_native_helper_opt_in(self) -> None:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，验证生产默认只读观察不会自动启用 native 截图文本；如果没有这个测试，用户只开 inventory 就可能泄露屏幕。
        with mock.patch("learning_agent.computer_use.controller.sys.platform", "win32"), mock.patch("learning_agent.computer_use.native_helper.sys.platform", "win32"):  # 新增代码+Phase32WindowsNativeHelper: 模拟 Windows 平台；如果没有这行代码，非 Windows CI 无法覆盖默认工厂逻辑。
            without_native = build_default_computer_use_backend({COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR: "1"}).status()  # 新增代码+Phase32WindowsNativeHelper: 只启用窗口观察不启用 native helper；如果没有这行代码，无法证明默认安全关闭。
            with_native = build_default_computer_use_backend({COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR: "1", COMPUTER_USE_NATIVE_OBSERVE_OPT_IN_ENV_VAR: "1"}).status()  # 新增代码+Phase32WindowsNativeHelper: 显式启用 native helper；如果没有这行代码，无法证明 opt-in 生效。
        self.assertFalse(without_native["observation_helper_available"])  # 新增代码+Phase32WindowsNativeHelper: 断言没有 native opt-in 时 helper 不可用；如果没有这行代码，只读 inventory 可能过度读取屏幕。
        self.assertEqual(without_native["observation_helper"], "none")  # 新增代码+Phase32WindowsNativeHelper: 断言默认仍是空 helper；如果没有这行代码，Phase29 安全边界可能被破坏。
        self.assertTrue(with_native["observation_helper_available"])  # 新增代码+Phase32WindowsNativeHelper: 断言显式 opt-in 后 native helper 可用；如果没有这行代码，用户无法开启只读 native 证据。
        self.assertEqual(with_native["observation_helper"], "windows_native_observation")  # 新增代码+Phase32WindowsNativeHelper: 断言 opt-in 后 helper 名称正确；如果没有这行代码，状态 UI 无法指导用户。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，test_default_backend_requires_native_helper_opt_in 到此结束；如果没有这个边界说明，读者不容易看出 opt-in 测试范围。

    def test_phase32_visible_terminal_scenario_documents_native_helper_markers(self) -> None:  # 新增代码+Phase32WindowsNativeHelper: 函数段开始，验证真实终端场景包含 Phase32 关键断言；如果没有这个测试，场景文件漏检也不容易发现。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase32WindowsNativeHelper: 定位 OpenHarness-main 根目录；如果没有这行代码，测试无法稳定找到场景 JSON。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase32_windows_native_helper.json"  # 新增代码+Phase32WindowsNativeHelper: 定位 Phase32 真实终端场景；如果没有这行代码，测试可能检查错文件。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase32WindowsNativeHelper: 读取并解析场景 JSON；如果没有这行代码，场景格式错误不会被发现。
        prompt_text = " ".join(scenario["prompt_lines"])  # 新增代码+Phase32WindowsNativeHelper: 合并 prompt 便于检查关键命令；如果没有这行代码，断言需要逐行重复查找。
        expected_tokens = {"PHASE32_WINDOWS_NATIVE_HELPER_OK", "screenshot=true", "raw_text_hidden=true", "helper=windows_native_observation", "helper_available=true", "optin_guard=true", "parsed=true", "width=222"}  # 新增代码+Phase32WindowsNativeHelper: 列出场景必须覆盖的成功证据；如果没有这行代码，场景可能只剩空成功标记。
        self.assertIn("WindowsNativeWindowObservationHelper", prompt_text)  # 新增代码+Phase32WindowsNativeHelper: 断言场景会覆盖 native helper 入口；如果没有这行代码，真实终端验收可能绕过 Phase32 模块。
        self.assertIn("FakeCapture", prompt_text)  # 新增代码+Phase32WindowsNativeHelper: 断言场景使用 fake provider 而非真实桌面；如果没有这行代码，验收可能读取真实屏幕。
        for token in expected_tokens:  # 新增代码+Phase32WindowsNativeHelper: 遍历关键成功 token；如果没有这行代码，断言会散落且容易漏。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase32WindowsNativeHelper: 断言日志检查包含该 token；如果没有这行代码，终端命令输出可能没有被 verifier 检查。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase32WindowsNativeHelper: 断言最终回答检查包含该 token；如果没有这行代码，用户可见答案可能漏关键证据。
    # 新增代码+Phase32WindowsNativeHelper: 函数段结束，test_phase32_visible_terminal_scenario_documents_native_helper_markers 到此结束；如果没有这个边界说明，读者不容易看出场景检查范围。


if __name__ == "__main__":  # 新增代码+Phase32WindowsNativeHelper: 允许直接运行本测试文件；如果没有这行代码，初学者无法单独验证 Phase32。
    unittest.main()  # 新增代码+Phase32WindowsNativeHelper: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
