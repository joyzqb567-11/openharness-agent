import json  # 新增代码+Phase35WindowsRealUIASmoke: 导入 JSON 用来读取验收场景；如果没有这行代码，测试无法确认可见终端验收会检查哪些固定标记。
import unittest  # 新增代码+Phase35WindowsRealUIASmoke: 导入 unittest 框架承载 Phase35 测试；如果没有这行代码，自动化测试发现不了真实 UIA smoke 的回归问题。
from pathlib import Path  # 新增代码+Phase35WindowsRealUIASmoke: 导入 Path 统一定位项目文件；如果没有这行代码，测试会依赖脆弱的字符串路径。

from learning_agent.computer_use.native_helper import NativeWindowTextResult  # 新增代码+Phase35WindowsRealUIASmoke: 复用真实文本 provider 的返回合同；如果没有这行代码，Phase35 测试会自造一套不一致的结果结构。
from learning_agent.computer_use.real_uia_smoke import PHASE35_REAL_UIA_SMOKE_MARKER, PHASE35_REAL_UIA_SMOKE_OK_TOKEN, Phase35SafeWindowTarget, run_phase35_real_uia_smoke  # 新增代码+Phase35WindowsRealUIASmoke: 导入 Phase35 预期入口；如果没有这行代码，红灯测试无法证明模块尚未实现。


class Phase35FakeLauncher:  # 新增代码+Phase35WindowsRealUIASmoke: 定义假的安全窗口启动器；如果没有这个类，单元测试会真的启动桌面窗口。
    def __init__(self) -> None:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，初始化 fake launcher 状态；如果没有这段函数，测试无法确认 cleanup 是否被调用。
        self.cleaned_up = False  # 新增代码+Phase35WindowsRealUIASmoke: 记录是否清理过安全窗口；如果没有这行代码，窗口生命周期门禁无法被测试覆盖。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，Phase35FakeLauncher.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch(self) -> Phase35SafeWindowTarget:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，返回一个假的安全窗口目标；如果没有这段函数，smoke harness 无法被隔离测试。
        return Phase35SafeWindowTarget(title_hint="Phase35-Safe-Window", cleanup=self.cleanup)  # 新增代码+Phase35WindowsRealUIASmoke: 返回带标题和清理函数的目标；如果没有这行代码，Phase35 无法知道只查找自己创建的窗口。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，Phase35FakeLauncher.launch 到此结束；如果没有这个边界说明，读者不容易看出启动目标的范围。

    def cleanup(self) -> None:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，模拟关闭安全窗口；如果没有这段函数，测试无法验证异常路径也会清理资源。
        self.cleaned_up = True  # 新增代码+Phase35WindowsRealUIASmoke: 标记清理已发生；如果没有这行代码，资源清理断言会失去依据。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，Phase35FakeLauncher.cleanup 到此结束；如果没有这个边界说明，读者不容易看出清理范围。


class Phase35FakeInventory:  # 新增代码+Phase35WindowsRealUIASmoke: 定义假的窗口 inventory；如果没有这个类，单元测试会读取用户真实桌面窗口。
    def __init__(self, windows: list[dict[str, object]]) -> None:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，保存测试窗口列表；如果没有这段函数，fake inventory 无法注入不同桌面状态。
        self.windows = windows  # 新增代码+Phase35WindowsRealUIASmoke: 保存窗口列表；如果没有这行代码，snapshot 返回时没有可检查的数据。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，Phase35FakeInventory.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def snapshot(self) -> object:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，返回最小 snapshot 对象；如果没有这段函数，Phase35 harness 无法复用现有 inventory 合同。
        return type("Phase35Snapshot", (), {"windows": self.windows})()  # 新增代码+Phase35WindowsRealUIASmoke: 返回带 windows 字段的对象；如果没有这行代码，测试会要求完整真实快照对象而变复杂。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，Phase35FakeInventory.snapshot 到此结束；如果没有这个边界说明，读者不容易看出快照范围。


class Phase35FakeTextProvider:  # 新增代码+Phase35WindowsRealUIASmoke: 定义假的 UIA 文本 provider；如果没有这个类，单元测试会依赖本机安装 UIA 依赖。
    def read_window_text(self, hwnd: int) -> NativeWindowTextResult:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，模拟读取窗口控件树文本；如果没有这段函数，真实 UIA 成功路径无法被稳定覆盖。
        return NativeWindowTextResult(captured=True, accessibility_text=f"Phase35 real UIA text from {hwnd}", focused_element="Phase35-Safe-Window", document_text="Phase35 document", backend="uiautomation_client", reason="fake provider contract only")  # 新增代码+Phase35WindowsRealUIASmoke: 返回与真实 provider 相同结构的成功结果；如果没有这行代码，harness 无法判断 UIA 是否读到内容。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，Phase35FakeTextProvider.read_window_text 到此结束；如果没有这个边界说明，读者不容易看出文本读取范围。


class WindowsComputerUseRealUiaSmokePhase35Tests(unittest.TestCase):  # 新增代码+Phase35WindowsRealUIASmoke: 定义 Phase35 测试集合；如果没有这个类，unittest 不会组织真实 UIA smoke 测试。
    def test_dependency_missing_is_reported_without_fake_success(self) -> None:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，验证缺少 uiautomation 依赖时诚实报告；如果没有这个测试，项目可能把缺依赖误说成已验证。
        result = run_phase35_real_uia_smoke(module_available=lambda name: False, platform="win32")  # 新增代码+Phase35WindowsRealUIASmoke: 模拟 Windows 但缺少 UIA 依赖；如果没有这行代码，缺依赖路径不会被覆盖。
        data = result.to_dict()  # 新增代码+Phase35WindowsRealUIASmoke: 转成字典便于断言；如果没有这行代码，测试会依赖 dataclass 内部细节。
        self.assertTrue(data["completed"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言诊断流程完成；如果没有这行代码，半途中断也可能误过。
        self.assertFalse(data["dependency_available"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言依赖确实被报告为缺失；如果没有这行代码，缺依赖会被掩盖。
        self.assertFalse(data["real_uia_attempted"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言没有依赖时不尝试真实桌面 UIA；如果没有这行代码，环境不满足时可能误触桌面。
        self.assertFalse(data["real_uia_verified"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言没有把缺依赖说成已验证；如果没有这行代码，成熟度报告会虚高。
        self.assertFalse(data["fake_provider_used"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言默认 smoke 不使用 fake provider 冒充真实结果；如果没有这行代码，验收可能被假数据污染。
        self.assertEqual(data["marker"], PHASE35_REAL_UIA_SMOKE_MARKER)  # 新增代码+Phase35WindowsRealUIASmoke: 断言固定阶段标记稳定；如果没有这行代码，可见终端验收无法可靠匹配。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，test_dependency_missing_is_reported_without_fake_success 到此结束；如果没有这个边界说明，读者不容易看出缺依赖测试范围。

    def test_dependency_available_uses_safe_window_and_real_provider_contract(self) -> None:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，验证有依赖时只针对安全窗口走 provider 合同；如果没有这个测试，Phase35 可能扫描任意用户窗口。
        launcher = Phase35FakeLauncher()  # 新增代码+Phase35WindowsRealUIASmoke: 创建 fake 安全窗口启动器；如果没有这行代码，清理路径无法被断言。
        inventory = Phase35FakeInventory([{"window_id": "hwnd:3501", "title_preview": "Phase35-Safe-Window", "app_id": "notepad.exe", "rect": {"left": 1, "top": 1, "right": 400, "bottom": 200}}])  # 新增代码+Phase35WindowsRealUIASmoke: 准备只包含安全窗口的 fake inventory；如果没有这行代码，harness 找不到目标窗口。
        result = run_phase35_real_uia_smoke(module_available=lambda name: True, platform="win32", inventory_factory=lambda: inventory, text_provider_factory=lambda: Phase35FakeTextProvider(), launcher=launcher)  # 新增代码+Phase35WindowsRealUIASmoke: 执行注入依赖的成功路径；如果没有这行代码，安全窗口 UIA 路径不会被验证。
        data = result.to_dict()  # 新增代码+Phase35WindowsRealUIASmoke: 转成字典便于检查字段；如果没有这行代码，断言会变得分散。
        self.assertTrue(data["dependency_available"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言依赖可用路径被识别；如果没有这行代码，测试可能仍走缺依赖路径。
        self.assertTrue(data["real_uia_attempted"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言真实 UIA smoke 被尝试；如果没有这行代码，Phase35 可能只做状态检查。
        self.assertTrue(data["real_uia_verified"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言 provider 合同读取成功；如果没有这行代码，读不到文本也可能误过。
        self.assertTrue(data["safe_window_found"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言只找到自己创建的安全窗口；如果没有这行代码，目标窗口保护无法验证。
        self.assertEqual(data["hwnd"], 3501)  # 新增代码+Phase35WindowsRealUIASmoke: 断言 hwnd 解析正确；如果没有这行代码，后续 provider 可能读错窗口。
        self.assertEqual(data["backend"], "uiautomation_client")  # 新增代码+Phase35WindowsRealUIASmoke: 断言结果来自 UIA provider 合同；如果没有这行代码，fallback 或空结果可能冒充成功。
        self.assertTrue(data["cleaned_up"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言安全窗口被清理；如果没有这行代码，smoke 可能留下测试窗口。
        self.assertTrue(launcher.cleaned_up)  # 新增代码+Phase35WindowsRealUIASmoke: 断言 fake launcher 的 cleanup 被调用；如果没有这行代码，资源生命周期没有外部证据。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，test_dependency_available_uses_safe_window_and_real_provider_contract 到此结束；如果没有这个边界说明，读者不容易看出成功路径测试范围。

    def test_safe_window_missing_does_not_claim_real_uia_verified(self) -> None:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，验证找不到安全窗口时不能假装成功；如果没有这个测试，窗口定位失败可能被说成已完成。
        launcher = Phase35FakeLauncher()  # 新增代码+Phase35WindowsRealUIASmoke: 创建 fake launcher；如果没有这行代码，清理断言没有目标。
        inventory = Phase35FakeInventory([])  # 新增代码+Phase35WindowsRealUIASmoke: 准备空窗口列表；如果没有这行代码，缺窗口路径无法被覆盖。
        result = run_phase35_real_uia_smoke(module_available=lambda name: True, platform="win32", inventory_factory=lambda: inventory, text_provider_factory=lambda: Phase35FakeTextProvider(), launcher=launcher, timeout_seconds=0.1, poll_interval_seconds=0.01)  # 修改代码+Phase35WindowsRealUIASmoke: 用短超时执行找不到窗口的路径；如果没有这行代码，定位失败处理会拖慢全量回归。
        data = result.to_dict()  # 新增代码+Phase35WindowsRealUIASmoke: 转换结果便于断言；如果没有这行代码，失败原因字段不易检查。
        self.assertTrue(data["real_uia_attempted"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言已经进入真实 smoke 尝试阶段；如果没有这行代码，失败原因可能混同为缺依赖。
        self.assertFalse(data["safe_window_found"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言安全窗口确实没找到；如果没有这行代码，错误定位不会暴露。
        self.assertFalse(data["real_uia_verified"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言没找到窗口不能声明 UIA 验证成功；如果没有这行代码，成熟度报告会虚高。
        self.assertTrue(data["cleaned_up"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言失败路径也会清理资源；如果没有这行代码，异常路径可能留下窗口或临时文件。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，test_safe_window_missing_does_not_claim_real_uia_verified 到此结束；如果没有这个边界说明，读者不容易看出失败路径测试范围。

    def test_phase35_visible_terminal_scenario_documents_real_uia_markers(self) -> None:  # 新增代码+Phase35WindowsRealUIASmoke: 函数段开始，验证真实终端验收场景包含 Phase35 固定标记；如果没有这个测试，场景漏检不会被自动发现。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase35WindowsRealUIASmoke: 定位 OpenHarness-main 根目录；如果没有这行代码，测试无法稳定找到 scenario 文件。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase35_windows_real_uia_smoke.json"  # 新增代码+Phase35WindowsRealUIASmoke: 定位 Phase35 可见终端场景；如果没有这行代码，测试可能检查错文件。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase35WindowsRealUIASmoke: 读取并解析 JSON 场景；如果没有这行代码，场景格式错误不会被发现。
        prompt_text = " ".join(scenario["prompt_lines"])  # 新增代码+Phase35WindowsRealUIASmoke: 合并 prompt 便于检查命令内容；如果没有这行代码，断言会重复访问列表。
        expected_tokens = {PHASE35_REAL_UIA_SMOKE_MARKER, PHASE35_REAL_UIA_SMOKE_OK_TOKEN, "dependency_reported=true", "fake_provider_used=false", "actions_expanded=false", "safe_window_only=true"}  # 新增代码+Phase35WindowsRealUIASmoke: 定义验收必须出现的稳定 token；如果没有这行代码，可见终端验收可能只检查空泛成功。
        self.assertIn("learning_agent.computer_use.real_uia_smoke", prompt_text)  # 新增代码+Phase35WindowsRealUIASmoke: 断言场景会调用真实 Phase35 模块；如果没有这行代码，验收可能绕过新实现。
        for token in expected_tokens:  # 新增代码+Phase35WindowsRealUIASmoke: 遍历每个必须检查的 token；如果没有这行代码，断言会分散且容易漏项。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言日志检查包含 token；如果没有这行代码，终端命令输出可能没有被 verifier 检查。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase35WindowsRealUIASmoke: 断言最终回答检查包含 token；如果没有这行代码，用户可见结果可能漏掉证据。
    # 新增代码+Phase35WindowsRealUIASmoke: 函数段结束，test_phase35_visible_terminal_scenario_documents_real_uia_markers 到此结束；如果没有这个边界说明，读者不容易看出场景测试范围。


if __name__ == "__main__":  # 新增代码+Phase35WindowsRealUIASmoke: 允许直接运行本测试文件；如果没有这行代码，初学者无法单独执行 Phase35 测试。
    unittest.main()  # 新增代码+Phase35WindowsRealUIASmoke: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
