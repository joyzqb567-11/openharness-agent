import json  # 新增代码+Phase34WindowsUIAProvider: 导入 JSON 用于读取 evidence metadata 和验收场景；如果没有这行代码，测试无法确认脱敏和场景断言。
import tempfile  # 新增代码+Phase34WindowsUIAProvider: 导入临时目录用于隔离 evidence 文件；如果没有这行代码，测试会污染真实 memory 目录。
import unittest  # 新增代码+Phase34WindowsUIAProvider: 导入 unittest 框架承载 Phase34 测试；如果没有这行代码，自动化测试无法发现 UIA provider 回归。
from pathlib import Path  # 新增代码+Phase34WindowsUIAProvider: 导入 Path 统一处理文件路径；如果没有这行代码，metadata 和场景定位会变脆。

from learning_agent.computer_use.controller import ComputerUseController, WindowsComputerUseBackend  # 新增代码+Phase34WindowsUIAProvider: 导入 controller/backend 验证 UIA 文本能进入窗口状态；如果没有这行代码，测试只能停留在 provider 层。
from learning_agent.computer_use.evidence import ComputerUseEvidenceStore  # 新增代码+Phase34WindowsUIAProvider: 导入 evidence store 验证 UIA 文本脱敏；如果没有这行代码，敏感文本泄露无法被自动化发现。
from learning_agent.computer_use.native_helper import FallbackNativeWindowTextProvider, NativeWindowCaptureResult, NativeWindowTextResult, WindowsNativeWindowObservationHelper, WindowsUiautomationTextProvider  # 新增代码+Phase34WindowsUIAProvider: 导入 Phase34 期望的新 provider；如果没有这行代码，红灯会证明生产入口尚未实现。
from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase34WindowsUIAProvider: 导入静态 inventory 避免读取真实桌面；如果没有这行代码，测试可能触碰用户本机窗口。


class FakeUiaControl:  # 新增代码+Phase34WindowsUIAProvider: 定义 fake UIA 控件节点；如果没有这个类，测试只能依赖真实 UIAutomationClient。
    def __init__(self, name: str, role: str, automation_id: str = "", class_name: str = "", children: list["FakeUiaControl"] | None = None) -> None:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，初始化 fake 控件；如果没有这段函数，测试无法构造稳定控件树。
        self.Name = name  # 新增代码+Phase34WindowsUIAProvider: 保存控件名称；如果没有这行代码，UIA provider 无法读取 name 字段。
        self.ControlTypeName = role  # 新增代码+Phase34WindowsUIAProvider: 保存控件角色；如果没有这行代码，UIA provider 无法读取 role 字段。
        self.AutomationId = automation_id  # 新增代码+Phase34WindowsUIAProvider: 保存自动化 id；如果没有这行代码，诊断文本缺少稳定定位线索。
        self.ClassName = class_name  # 新增代码+Phase34WindowsUIAProvider: 保存 class name；如果没有这行代码，诊断文本缺少窗口类线索。
        self._children = list(children or [])  # 新增代码+Phase34WindowsUIAProvider: 保存子控件副本；如果没有这行代码，树遍历无法展开。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，FakeUiaControl.__init__ 到此结束；如果没有这个边界说明，读者不容易看出 fake 控件初始化范围。

    def GetChildren(self) -> list["FakeUiaControl"]:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，模拟 uiautomation 的 GetChildren；如果没有这段函数，provider 无法遍历 fake 控件树。
        return list(self._children)  # 新增代码+Phase34WindowsUIAProvider: 返回子控件副本；如果没有这行代码，调用方可能改写原始树。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，FakeUiaControl.GetChildren 到此结束；如果没有这个边界说明，读者不容易看出子控件读取范围。


class FakeUiaModule:  # 新增代码+Phase34WindowsUIAProvider: 定义 fake UIA 模块；如果没有这个类，provider 测试需要安装真实 uiautomation 依赖。
    def __init__(self, root: FakeUiaControl) -> None:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，初始化 fake 模块根控件；如果没有这段函数，模块不知道从哪个根节点返回。
        self.root = root  # 新增代码+Phase34WindowsUIAProvider: 保存根控件；如果没有这行代码，ControlFromHandle 无法返回稳定对象。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，FakeUiaModule.__init__ 到此结束；如果没有这个边界说明，读者不容易看出模块初始化范围。

    def ControlFromHandle(self, hwnd: int) -> FakeUiaControl:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，模拟 uiautomation.ControlFromHandle；如果没有这段函数，provider 无法从 hwnd 获取根控件。
        return self.root  # 新增代码+Phase34WindowsUIAProvider: 返回根控件；如果没有这行代码，UIA provider 没有遍历入口。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，FakeUiaModule.ControlFromHandle 到此结束；如果没有这个边界说明，读者不容易看出 hwnd 映射范围。


class FakeCaptureProvider:  # 新增代码+Phase34WindowsUIAProvider: 定义假截图 provider；如果没有这个类，backend evidence 测试会触发真实截图。
    def status(self) -> dict[str, object]:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，返回 fake 截图状态；如果没有这段函数，helper.status 无法展示截图 provider。
        return {"backend": "phase34_fake_capture", "available": True, "reason": "phase34 fake capture"}  # 新增代码+Phase34WindowsUIAProvider: 返回稳定 fake 状态；如果没有这行代码，测试无法断言 helper 可用。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，FakeCaptureProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态函数范围。

    def capture_window(self, hwnd: int) -> NativeWindowCaptureResult:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，返回 fake 截图；如果没有这段函数，get_window_state 无法落盘截图 artifact。
        return NativeWindowCaptureResult(captured=True, screenshot_bytes=b"phase34-bmp", screenshot_format="bmp", screenshot_width=344, screenshot_height=122, backend="phase34_fake_capture", reason=f"captured {hwnd}")  # 新增代码+Phase34WindowsUIAProvider: 返回稳定截图结果；如果没有这行代码，evidence 测试无法检查截图路径。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，FakeCaptureProvider.capture_window 到此结束；如果没有这个边界说明，读者不容易看出截图函数范围。


class FailingTextProvider:  # 新增代码+Phase34WindowsUIAProvider: 定义失败的 primary 文本 provider；如果没有这个类，fallback 行为无法被稳定测试。
    def status(self) -> dict[str, object]:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，返回失败 provider 状态；如果没有这段函数，fallback 状态无法说明 primary 不可用。
        return {"backend": "uiautomation_client", "available": False, "reason": "missing dependency"}  # 新增代码+Phase34WindowsUIAProvider: 返回 primary 不可用状态；如果没有这行代码，测试无法确认 fallback 原因。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，FailingTextProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态函数范围。

    def read_window_text(self, hwnd: int) -> NativeWindowTextResult:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，模拟 primary 读取失败；如果没有这段函数，fallback provider 没有失败输入。
        return NativeWindowTextResult(captured=False, backend="uiautomation_client", reason="missing dependency")  # 新增代码+Phase34WindowsUIAProvider: 返回失败结果；如果没有这行代码，fallback 逻辑不会触发。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，FailingTextProvider.read_window_text 到此结束；如果没有这个边界说明，读者不容易看出失败路径范围。


class SuccessfulFallbackTextProvider:  # 新增代码+Phase34WindowsUIAProvider: 定义成功 fallback 文本 provider；如果没有这个类，fallback 成功路径无法被测试。
    def status(self) -> dict[str, object]:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，返回 fallback 状态；如果没有这段函数，组合 provider 无法说明 fallback 可用。
        return {"backend": "win32_window_text", "available": True, "reason": "fallback ready"}  # 新增代码+Phase34WindowsUIAProvider: 返回 fallback 可用状态；如果没有这行代码，组合状态会缺少 fallback 细节。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，SuccessfulFallbackTextProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态函数范围。

    def read_window_text(self, hwnd: int) -> NativeWindowTextResult:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，模拟 fallback 读取成功；如果没有这段函数，组合 provider 无法完成降级。
        return NativeWindowTextResult(captured=True, accessibility_text="fallback text", focused_element="fallback", document_text="fallback text", backend="win32_window_text", reason="fallback captured")  # 新增代码+Phase34WindowsUIAProvider: 返回 fallback 成功结果；如果没有这行代码，测试无法证明降级可用。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，SuccessfulFallbackTextProvider.read_window_text 到此结束；如果没有这个边界说明，读者不容易看出 fallback 读取范围。


class WindowsComputerUseUiaProviderPhase34Tests(unittest.TestCase):  # 新增代码+Phase34WindowsUIAProvider: 定义 Phase34 测试集合；如果没有这个类，unittest 不会组织 UIA provider 测试。
    def _uia_module(self) -> FakeUiaModule:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，构造 fake UIA 树；如果没有这段函数，每个测试都要重复搭建控件树。
        child = FakeUiaControl("Save Button", "ButtonControl", automation_id="save", class_name="Button")  # 新增代码+Phase34WindowsUIAProvider: 创建按钮子节点；如果没有这行代码，树遍历无法证明子控件读取。
        secret = FakeUiaControl("password: hidden", "EditControl", automation_id="secret", class_name="Edit")  # 新增代码+Phase34WindowsUIAProvider: 创建敏感文本节点；如果没有这行代码，evidence 脱敏测试没有目标。
        root = FakeUiaControl("Root Window", "WindowControl", automation_id="root", class_name="Window", children=[child, secret])  # 新增代码+Phase34WindowsUIAProvider: 创建根窗口节点；如果没有这行代码，UIA provider 没有树入口。
        return FakeUiaModule(root)  # 新增代码+Phase34WindowsUIAProvider: 返回 fake UIA 模块；如果没有这行代码，provider 无法从 hwnd 获取 root。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，_uia_module 到此结束；如果没有这个边界说明，读者不容易看出 fake 树范围。

    def test_uia_provider_reads_bounded_fake_control_tree(self) -> None:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，验证 UIA provider 能读取 fake 控件树；如果没有这个测试，Phase34 可能只新增空壳。
        provider = WindowsUiautomationTextProvider(platform="win32", uia_module=self._uia_module(), max_depth=3, max_nodes=10)  # 新增代码+Phase34WindowsUIAProvider: 构造注入 fake 模块的 UIA provider；如果没有这行代码，测试会依赖真实 UIA。
        result = provider.read_window_text(3401)  # 新增代码+Phase34WindowsUIAProvider: 执行一次 UIA 文本读取；如果没有这行代码，测试无法观察 provider 输出。
        self.assertTrue(result.captured)  # 新增代码+Phase34WindowsUIAProvider: 断言读取成功；如果没有这行代码，空结果也可能误通过。
        self.assertEqual(result.backend, "uiautomation_client")  # 新增代码+Phase34WindowsUIAProvider: 断言结果来源是 UIA provider；如果没有这行代码，Win32 fallback 可能冒充成功。
        self.assertIn("Root Window", result.accessibility_text)  # 新增代码+Phase34WindowsUIAProvider: 断言根窗口文本进入摘要；如果没有这行代码，根节点可能丢失。
        self.assertIn("Save Button", result.accessibility_text)  # 新增代码+Phase34WindowsUIAProvider: 断言子控件文本进入摘要；如果没有这行代码，树遍历可能没有发生。
        self.assertIn("role=ButtonControl", result.accessibility_text)  # 新增代码+Phase34WindowsUIAProvider: 断言控件角色进入摘要；如果没有这行代码，模型缺少语义定位信息。
        self.assertEqual(result.focused_element, "Root Window")  # 新增代码+Phase34WindowsUIAProvider: 断言焦点摘要使用根名称；如果没有这行代码，窗口上下文不稳定。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，test_uia_provider_reads_bounded_fake_control_tree 到此结束；如果没有这个边界说明，读者不容易看出 UIA 成功测试范围。

    def test_uia_provider_refuses_non_windows_and_bad_hwnd(self) -> None:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，验证 UIA provider 的安全拒绝路径；如果没有这个测试，非 Windows 或坏句柄可能触发真实 API。
        non_windows = WindowsUiautomationTextProvider(platform="linux", uia_module=self._uia_module()).read_window_text(3401)  # 新增代码+Phase34WindowsUIAProvider: 模拟非 Windows 平台读取；如果没有这行代码，跨平台拒绝不会被覆盖。
        bad_hwnd = WindowsUiautomationTextProvider(platform="win32", uia_module=self._uia_module()).read_window_text(0)  # 新增代码+Phase34WindowsUIAProvider: 模拟坏 hwnd 读取；如果没有这行代码，0 句柄拒绝不会被覆盖。
        self.assertFalse(non_windows.captured)  # 新增代码+Phase34WindowsUIAProvider: 断言非 Windows 不读取；如果没有这行代码，provider 可能跨平台误调用。
        self.assertFalse(bad_hwnd.captured)  # 新增代码+Phase34WindowsUIAProvider: 断言坏 hwnd 不读取；如果没有这行代码，provider 可能把 0 传给 UIA。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，test_uia_provider_refuses_non_windows_and_bad_hwnd 到此结束；如果没有这个边界说明，读者不容易看出拒绝测试范围。

    def test_fallback_text_provider_uses_win32_when_uia_is_unavailable(self) -> None:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，验证 UIA 失败时走 Win32 fallback；如果没有这个测试，默认 helper 可能在缺依赖时完全没文本。
        provider = FallbackNativeWindowTextProvider(primary_provider=FailingTextProvider(), fallback_provider=SuccessfulFallbackTextProvider())  # 新增代码+Phase34WindowsUIAProvider: 构造失败 primary 和成功 fallback；如果没有这行代码，降级路径无法触发。
        result = provider.read_window_text(3401)  # 新增代码+Phase34WindowsUIAProvider: 执行组合读取；如果没有这行代码，测试无法观察 fallback 输出。
        self.assertTrue(result.captured)  # 新增代码+Phase34WindowsUIAProvider: 断言最终读取成功；如果没有这行代码，降级失败也可能误通过。
        self.assertEqual(result.backend, "win32_window_text")  # 新增代码+Phase34WindowsUIAProvider: 断言实际结果来自 fallback；如果没有这行代码，primary 失败原因可能被隐藏。
        self.assertIn("primary=uiautomation_client:missing dependency", result.reason)  # 新增代码+Phase34WindowsUIAProvider: 断言原因包含 primary 失败；如果没有这行代码，排查缺依赖会困难。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，test_fallback_text_provider_uses_win32_when_uia_is_unavailable 到此结束；如果没有这个边界说明，读者不容易看出 fallback 测试范围。

    def test_default_helper_uses_uia_first_text_provider(self) -> None:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，验证默认 helper 使用 UIA 优先组合 provider；如果没有这个测试，Phase34 可能没有接入生产默认路径。
        helper = WindowsNativeWindowObservationHelper(capture_provider=FakeCaptureProvider(), platform="win32")  # 新增代码+Phase34WindowsUIAProvider: 构造未注入 text_provider 的默认 helper；如果没有这行代码，测试无法覆盖默认策略。
        status = helper.status()  # 新增代码+Phase34WindowsUIAProvider: 读取 helper 状态；如果没有这行代码，测试无法检查默认文本 provider。
        self.assertEqual(status["text"]["backend"], "uiautomation_client_with_win32_fallback")  # 新增代码+Phase34WindowsUIAProvider: 断言默认文本 provider 是 UIA 优先组合；如果没有这行代码，生产默认路径可能仍停在纯 Win32。
        self.assertEqual(status["diagnostics"]["text"]["active_provider"], "uiautomation_client_with_win32_fallback")  # 新增代码+Phase34WindowsUIAProvider: 断言诊断透出组合 provider；如果没有这行代码，/computer 状态看不到 Phase34 接入。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，test_default_helper_uses_uia_first_text_provider 到此结束；如果没有这个边界说明，读者不容易看出默认 helper 测试范围。

    def test_backend_evidence_filters_sensitive_uia_text(self) -> None:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，验证 UIA 文本进入 evidence 后仍脱敏；如果没有这个测试，控件树可能泄露 password 文本。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase34WindowsUIAProvider: 创建临时 evidence 目录；如果没有这行代码，测试会污染真实证据目录。
            raw_windows = [{"hwnd": 3401, "pid": 1, "process_name": "notepad.exe", "class_name": "Notepad", "title": "Phase34", "rect": {"left": 1, "top": 2, "right": 301, "bottom": 202}}]  # 新增代码+Phase34WindowsUIAProvider: 准备静态窗口；如果没有这行代码，后端会读取真实桌面。
            inventory = StaticWindowsWindowInventory(raw_windows=raw_windows, captured_at="2026-06-03T00:00:00Z")  # 新增代码+Phase34WindowsUIAProvider: 创建静态 inventory；如果没有这行代码，controller.observe 没有可信窗口。
            store = ComputerUseEvidenceStore(evidence_root=Path(temp_dir))  # 新增代码+Phase34WindowsUIAProvider: 创建临时 evidence store；如果没有这行代码，metadata 无法被安全检查。
            text_provider = WindowsUiautomationTextProvider(platform="win32", uia_module=self._uia_module(), max_depth=3, max_nodes=10)  # 新增代码+Phase34WindowsUIAProvider: 创建 fake UIA 文本 provider；如果没有这行代码，测试无法稳定产生敏感文本。
            helper = WindowsNativeWindowObservationHelper(capture_provider=FakeCaptureProvider(), text_provider=text_provider, platform="win32")  # 新增代码+Phase34WindowsUIAProvider: 创建注入 UIA provider 的 helper；如果没有这行代码，后端不会使用 UIA 文本。
            backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False, evidence_store=store, observation_helper=helper)  # 新增代码+Phase34WindowsUIAProvider: 创建只读后端；如果没有这行代码，controller 无法保存窗口状态。
            controller = ComputerUseController(backend=backend)  # 新增代码+Phase34WindowsUIAProvider: 通过统一 controller 执行 observe；如果没有这行代码，测试会绕过生产安全入口。
            window = controller.observe({"action": "list_windows"}).data["windows"][0]  # 新增代码+Phase34WindowsUIAProvider: 获取可信窗口引用；如果没有这行代码，get_window_state 会使用伪造窗口。
            state = controller.observe({"action": "get_window_state", "window": window}).data["state"]  # 新增代码+Phase34WindowsUIAProvider: 读取窗口状态并触发 evidence 保存；如果没有这行代码，UIA 文本不会进入证据链。
            metadata = json.loads(Path(state["evidence_path"]).read_text(encoding="utf-8"))  # 新增代码+Phase34WindowsUIAProvider: 读取 metadata 检查脱敏；如果没有这行代码，磁盘泄露无法被发现。
            self.assertNotIn("password", state["accessibility_excerpt"].lower())  # 新增代码+Phase34WindowsUIAProvider: 断言响应摘要不含敏感词；如果没有这行代码，模型可见输出可能泄露。
            self.assertNotIn("password", json.dumps(metadata, ensure_ascii=False).lower())  # 新增代码+Phase34WindowsUIAProvider: 断言落盘 metadata 不含敏感词；如果没有这行代码，磁盘 artifact 可能泄露。
            self.assertEqual(state["helper_name"], "windows_native_observation")  # 新增代码+Phase34WindowsUIAProvider: 断言 helper 来源稳定；如果没有这行代码，证据来源可能不清楚。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，test_backend_evidence_filters_sensitive_uia_text 到此结束；如果没有这个边界说明，读者不容易看出 evidence 测试范围。

    def test_phase34_visible_terminal_scenario_documents_uia_markers(self) -> None:  # 新增代码+Phase34WindowsUIAProvider: 函数段开始，验证 Phase34 验收场景包含关键标记；如果没有这个测试，场景漏检不容易发现。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase34WindowsUIAProvider: 定位项目根目录；如果没有这行代码，测试无法稳定找到 scenario。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase34_windows_uia_text_provider.json"  # 新增代码+Phase34WindowsUIAProvider: 定位 Phase34 场景；如果没有这行代码，测试可能检查错文件。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase34WindowsUIAProvider: 读取并解析场景 JSON；如果没有这行代码，场景格式错误不会被发现。
        prompt_text = " ".join(scenario["prompt_lines"])  # 新增代码+Phase34WindowsUIAProvider: 合并 prompt 文本；如果没有这行代码，关键命令检查会重复。
        expected_tokens = {"PHASE34_WINDOWS_UIA_TEXT_PROVIDER_OK", "uia=true", "fallback=true", "raw_text_hidden=true", "actions_expanded=false"}  # 新增代码+Phase34WindowsUIAProvider: 列出验收必须出现的 token；如果没有这行代码，场景可能只有空成功标记。
        self.assertIn("WindowsUiautomationTextProvider", prompt_text)  # 新增代码+Phase34WindowsUIAProvider: 断言场景实际覆盖 UIA provider；如果没有这行代码，验收可能绕过 Phase34 能力。
        for token in expected_tokens:  # 新增代码+Phase34WindowsUIAProvider: 遍历必须检查的 token；如果没有这行代码，断言会散落且容易漏项。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase34WindowsUIAProvider: 断言 debug log 检查包含 token；如果没有这行代码，日志可能漏验证。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase34WindowsUIAProvider: 断言最终回答检查包含 token；如果没有这行代码，用户可见答案可能漏证据。
    # 新增代码+Phase34WindowsUIAProvider: 函数段结束，test_phase34_visible_terminal_scenario_documents_uia_markers 到此结束；如果没有这个边界说明，读者不容易看出场景测试范围。


if __name__ == "__main__":  # 新增代码+Phase34WindowsUIAProvider: 允许直接运行本测试文件；如果没有这行代码，初学者无法单独执行 Phase34 测试。
    unittest.main()  # 新增代码+Phase34WindowsUIAProvider: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
