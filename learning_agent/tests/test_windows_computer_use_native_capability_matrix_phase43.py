import json  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 导入 JSON 工具检查场景文件；如果没有这行代码，测试无法验证真实终端验收配置。
import tempfile  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 导入临时目录隔离 /computer status 锁文件；如果没有这行代码，测试可能污染真实 Computer Use 状态。
import unittest  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 导入 unittest 框架承载 Phase43 测试；如果没有这行代码，自动化测试无法发现本阶段回归。
from pathlib import Path  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 导入 Path 统一定位场景和临时工作区；如果没有这行代码，路径拼接会变成脆弱字符串。

from learning_agent.app.interactive import run_computer_terminal_command  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 导入真实终端 /computer 命令入口；如果没有这行代码，测试无法证明状态 UI 已显示能力矩阵。
from learning_agent.computer_use.controller import WindowsComputerUseBackend  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 导入 Windows 后端验证 status 透传；如果没有这行代码，矩阵可能只存在于独立模块没有接入后端。
from learning_agent.computer_use.native_diagnostics import PHASE43_WINDOWS_NATIVE_CAPABILITY_MARKER, PHASE43_WINDOWS_NATIVE_CAPABILITY_OK_TOKEN, build_phase43_native_capability_matrix, format_phase43_capability_matrix_lines, phase43_cli_line, run_phase43_native_capability_matrix_contract  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 导入 Phase43 期望的新合同入口；如果没有这行代码，红灯会证明能力矩阵尚未实现。
from learning_agent.computer_use.native_helper import NativeWindowCaptureResult, NativeWindowTextResult, WindowsNativeWindowObservationHelper  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 导入 helper 和统一结果类型；如果没有这行代码，后端接入测试无法安全构造 fake provider。
from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 导入静态 inventory 避免读取真实桌面；如果没有这行代码，单测会依赖用户当前窗口。


class Phase43FakeCaptureProvider:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 定义 fake 截图 provider；如果没有这个类，测试只能依赖真实 Windows 截图能力。
    def status(self) -> dict[str, object]:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，返回 fake WGC 状态；如果没有这段函数，diagnostics 无法识别 active capture provider。
        return {"backend": "windows_graphics_capture", "available": True, "reason": "phase43 fake WGC provider"}  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回可用截图状态；如果没有这行代码，矩阵无法覆盖 enabled=true 路径。
    # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，Phase43FakeCaptureProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态函数范围。

    def capture_window(self, hwnd: int) -> NativeWindowCaptureResult:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，返回 fake 截图结果；如果没有这段函数，helper.observe_window 无法形成截图 payload。
        return NativeWindowCaptureResult(captured=True, screenshot_bytes=b"phase43-fake-bmp", screenshot_format="bmp", screenshot_width=43, screenshot_height=43, backend="windows_graphics_capture", reason=f"captured {hwnd}")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回稳定 fake 截图；如果没有这行代码，后端状态测试无法证明 provider 参与观察链。
    # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，Phase43FakeCaptureProvider.capture_window 到此结束；如果没有这个边界说明，读者不容易看出截图函数范围。


class Phase43FakeTextProvider:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 定义 fake UIA 文本 provider；如果没有这个类，测试只能依赖真实 UIA 依赖。
    def status(self) -> dict[str, object]:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，返回 fake UIA 状态；如果没有这段函数，矩阵无法覆盖 UIA enabled=true 路径。
        return {"backend": "uiautomation_client", "available": True, "reason": "phase43 fake UIA provider"}  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回可用 UIA 状态；如果没有这行代码，诊断只会显示 fallback。
    # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，Phase43FakeTextProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态函数范围。

    def read_window_text(self, hwnd: int) -> NativeWindowTextResult:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，返回 fake UIA 文本；如果没有这段函数，helper.observe_window 无法形成文本 payload。
        return NativeWindowTextResult(captured=True, accessibility_text="button: OK", focused_element=f"root {hwnd}", selected_text="", document_text="button: OK", backend="uiautomation_client", reason=f"text {hwnd}")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回稳定 fake UIA 文本；如果没有这行代码，后端观察链缺少文本结果。
    # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，Phase43FakeTextProvider.read_window_text 到此结束；如果没有这个边界说明，读者不容易看出文本函数范围。


class WindowsComputerUseNativeCapabilityMatrixPhase43Tests(unittest.TestCase):  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 定义 Phase43 测试集合；如果没有这个类，unittest 不会组织本阶段测试。
    def _backend_status_sample(self) -> dict[str, object]:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，构造后端状态样本；如果没有这段函数，每个测试都要重复一大段状态字典。
        return {"available": True, "platform": "win32", "read_only_inventory_enabled": True, "observation_helper_available": True, "native_observation_diagnostics": {"capture": {"preferred_provider": "windows_graphics_capture", "active_provider": "win32_gdi_printwindow", "providers": [{"name": "windows_graphics_capture", "available": False, "active": False, "reason": "missing binding", "next_step": "wire WGC"}, {"name": "win32_gdi_printwindow", "available": True, "active": True, "reason": "fallback", "next_step": "keep fallback"}]}, "text": {"preferred_provider": "uiautomation_client", "active_provider": "uiautomation_client", "providers": [{"name": "uiautomation_client", "available": True, "active": True, "reason": "uia ready", "next_step": "use UIA"}, {"name": "win32_window_text", "available": True, "active": False, "reason": "fallback", "next_step": "keep fallback"}]}}, "action_executor": {"backend": "windows_sendinput", "available": False, "real_input_enabled": False, "implementation_available": False, "reason": "missing impl"}}  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回覆盖 WGC 缺失、GDI 可用、UIA 可用、SendInput 未启用的样本；如果没有这行代码，矩阵关键分支缺少输入。
    # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，_backend_status_sample 到此结束；如果没有这个边界说明，读者不容易看出样本范围。

    def test_phase43_matrix_normalizes_available_enabled_reason_and_next_step(self) -> None:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，验证矩阵字段完整；如果没有这个测试，status 可能继续只给粗略 diagnostics。
        matrix = build_phase43_native_capability_matrix(self._backend_status_sample())  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 构建 Phase43 能力矩阵；如果没有这行代码，测试没有被测对象。
        capabilities = {item["name"]: item for item in matrix["capabilities"]}  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 按能力名建立索引；如果没有这行代码，断言会反复遍历列表。

        self.assertEqual(matrix["marker"], PHASE43_WINDOWS_NATIVE_CAPABILITY_MARKER)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言矩阵 marker 稳定；如果没有这行代码，真实终端场景可能等错标记。
        self.assertFalse(matrix["actions_expanded"])  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言 Phase43 不扩大真实动作面；如果没有这行代码，诊断阶段可能被误解成动作阶段。
        self.assertIn("windows_graphics_capture", capabilities)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言 WGC 能力进入矩阵；如果没有这行代码，截图首选缺口不可见。
        self.assertIn("win32_gdi_printwindow", capabilities)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言 GDI fallback 进入矩阵；如果没有这行代码，用户看不到当前保底截图能力。
        self.assertIn("uiautomation_client", capabilities)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言 UIA 能力进入矩阵；如果没有这行代码，控件树缺口不可见。
        self.assertIn("windows_sendinput", capabilities)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言 SendInput 能力进入矩阵；如果没有这行代码，动作层缺口不可见。
        for capability in capabilities.values():  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 遍历所有能力项；如果没有这行代码，字段完整性只能抽样验证。
            for key in ("name", "category", "available", "enabled", "reason", "next_step"):  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 定义每个能力必须有的字段；如果没有这行代码，测试目标不清楚。
                self.assertIn(key, capability)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言字段存在；如果没有这行代码，状态消费者仍可能拿到不完整 dict。
            self.assertTrue(str(capability["reason"]))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言原因非空；如果没有这行代码，用户只看到 true/false 不知道为什么。
            self.assertTrue(str(capability["next_step"]))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言下一步非空；如果没有这行代码，用户不知道如何补齐能力。
        self.assertFalse(capabilities["windows_graphics_capture"]["enabled"])  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言缺绑定 WGC 没有被误启用；如果没有这行代码，诊断可能虚报截图成熟。
        self.assertTrue(capabilities["win32_gdi_printwindow"]["enabled"])  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言 active fallback 被标记为启用；如果没有这行代码，用户看不到当前实际截图来源。
        self.assertTrue(capabilities["uiautomation_client"]["enabled"])  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言 active UIA 被标记为启用；如果没有这行代码，UIA 成功路径不可见。
        self.assertFalse(capabilities["windows_sendinput"]["enabled"])  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言 SendInput 未启用；如果没有这行代码，默认禁用边界可能被破坏。
    # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，test_phase43_matrix_normalizes_available_enabled_reason_and_next_step 到此结束；如果没有这个边界说明，读者不容易看出矩阵测试范围。

    def test_windows_backend_status_exposes_phase43_capability_matrix(self) -> None:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，验证后端状态透传能力矩阵；如果没有这个测试，矩阵可能不会进入 computer_status。
        raw_windows = [{"hwnd": 4301, "pid": 1, "process_name": "notepad.exe", "class_name": "Notepad", "title": "Phase43", "rect": {"left": 1, "top": 2, "right": 301, "bottom": 202}}]  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 构造安全静态窗口；如果没有这行代码，后端测试会读取真实桌面。
        inventory = StaticWindowsWindowInventory(raw_windows=raw_windows, captured_at="2026-06-03T00:00:00Z")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 创建静态 inventory；如果没有这行代码，Windows 后端没有可用观察源。
        helper = WindowsNativeWindowObservationHelper(capture_provider=Phase43FakeCaptureProvider(), text_provider=Phase43FakeTextProvider(), platform="win32")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 创建 fake native helper；如果没有这行代码，测试会依赖真实 WGC/UIA。
        backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False, observation_helper=helper)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 创建只读 Windows 后端；如果没有这行代码，无法验证 status 集成。
        status = backend.status()  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取后端状态；如果没有这行代码，测试没有状态数据。
        matrix = status["native_capability_matrix"]  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取 Phase43 矩阵字段；如果没有这行代码，缺失透传不会被发现。
        capability_names = {item["name"] for item in matrix["capabilities"]}  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 收集能力名便于断言；如果没有这行代码，测试重复遍历列表。

        self.assertEqual(matrix["marker"], PHASE43_WINDOWS_NATIVE_CAPABILITY_MARKER)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言后端状态携带正确 marker；如果没有这行代码，status 可能返回旧结构。
        self.assertIn("windows_graphics_capture", capability_names)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言截图首选能力透传；如果没有这行代码，status 看不到 WGC 缺口。
        self.assertIn("uiautomation_client", capability_names)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言 UIA 能力透传；如果没有这行代码，status 看不到控件树能力。
        self.assertIn("windows_sendinput", capability_names)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言动作能力透传；如果没有这行代码，status 看不到真实动作层缺口。
    # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，test_windows_backend_status_exposes_phase43_capability_matrix 到此结束；如果没有这个边界说明，读者不容易看出 status 集成范围。

    def test_computer_terminal_status_includes_phase43_matrix_lines(self) -> None:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，验证 /computer status 显示能力矩阵；如果没有这个测试，用户仍只能看到锁和 runtime。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 创建临时工作区；如果没有这行代码，/computer status 会写入真实项目锁目录。
            output = run_computer_terminal_command(Path(temp_dir), "/computer status")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 运行真实终端状态命令；如果没有这行代码，测试无法证明 UI 输出已接入。
        self.assertIn("Computer Native Capability Matrix", output)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言终端有能力矩阵标题；如果没有这行代码，状态 UI 仍不够直观。
        self.assertIn(PHASE43_WINDOWS_NATIVE_CAPABILITY_MARKER, output)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言终端输出包含 marker；如果没有这行代码，真实验收无法稳定匹配。
        self.assertIn("windows_graphics_capture", output)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言终端展示 WGC；如果没有这行代码，用户不知道截图首选缺口。
        self.assertIn("windows_sendinput", output)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言终端展示 SendInput；如果没有这行代码，用户不知道动作层状态。
    # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，test_computer_terminal_status_includes_phase43_matrix_lines 到此结束；如果没有这个边界说明，读者不容易看出终端状态测试范围。

    def test_phase43_cli_line_and_visible_terminal_scenario_tokens(self) -> None:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，验证 CLI 行和真实终端场景 token；如果没有这个测试，Phase43 可能缺少可见验收入口。
        report = run_phase43_native_capability_matrix_contract(backend_status=self._backend_status_sample())  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 运行 Phase43 合同自检；如果没有这行代码，CLI 行没有真实报告。
        cli_line = phase43_cli_line(report)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 生成稳定 CLI 验收行；如果没有这行代码，场景 token 无法复用。
        lines = format_phase43_capability_matrix_lines(report["matrix"])  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 生成终端矩阵行；如果没有这行代码，格式化函数没有覆盖。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase43_windows_native_capability_matrix.json")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 定位 Phase43 场景；如果没有这行代码，测试无法确认真实终端验收配置。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取场景 JSON；如果没有这行代码，场景格式错误不会暴露。
        scenario_text = json.dumps(scenario, ensure_ascii=False)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 序列化场景便于 token 检查；如果没有这行代码，断言要遍历多个字段。

        expected_tokens = {PHASE43_WINDOWS_NATIVE_CAPABILITY_MARKER, PHASE43_WINDOWS_NATIVE_CAPABILITY_OK_TOKEN, "capability_matrix=true", "status_fields=true", "actions_expanded=false"}  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 定义 CLI 和场景都必须包含的 token；如果没有这行代码，验收标准容易漂移。
        self.assertIn("Computer Native Capability Matrix", "\n".join(lines))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言格式化输出有标题；如果没有这行代码，终端面板不可读。
        for token in expected_tokens:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 遍历所有关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言 CLI 行包含 token；如果没有这行代码，命令行验收可能不稳定。
            self.assertIn(token, scenario_text)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 断言场景包含 token；如果没有这行代码，真实可见终端验收可能漏检。
    # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，test_phase43_cli_line_and_visible_terminal_scenario_tokens 到此结束；如果没有这个边界说明，读者不容易看出场景 token 测试范围。


if __name__ == "__main__":  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行任何测试。
