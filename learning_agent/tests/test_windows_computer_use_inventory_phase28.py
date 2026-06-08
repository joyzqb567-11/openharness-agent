import unittest  # 新增代码+Phase28ComputerUse: 引入 unittest 测试框架；如果没有这行代码，本文件无法定义和运行 Phase 28 自动化测试。

from learning_agent.computer_use.controller import COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR, ComputerUseController, WindowsComputerUseBackend, build_default_computer_use_backend  # 修改代码+Phase28ComputerUse: 导入只读观察开关和默认后端工厂；如果没有这行代码，测试无法验证用户如何只启用 observe。
from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase28ComputerUse: 导入静态窗口 inventory；如果没有这行代码，测试无法在不碰真实桌面的情况下模拟 Windows 窗口。


class WindowsComputerUseInventoryPhase28Tests(unittest.TestCase):  # 新增代码+Phase28ComputerUse: 定义 Phase 28 的只读 Windows inventory 测试集合；如果没有这个类，unittest 不会发现本阶段测试。
    def _raw_windows(self) -> list[dict[str, object]]:  # 新增代码+Phase28ComputerUse: 准备静态窗口输入数据；如果没有这段函数，每个测试都要重复构造窗口记录。
        return [  # 新增代码+Phase28ComputerUse: 返回模拟窗口列表；如果没有这行代码，测试没有可观察的窗口样本。
            {"hwnd": 12345, "pid": 100, "process_name": "notepad.exe", "class_name": "Notepad", "title": "记事本 - Phase28", "rect": {"left": 10, "top": 20, "right": 310, "bottom": 220}},  # 新增代码+Phase28ComputerUse: 提供一个安全可枚举窗口；如果没有这行代码，list_windows 没有正向样本。
            {"hwnd": 67890, "pid": 200, "process_name": "powershell.exe", "class_name": "ConsoleWindowClass", "title": "Windows PowerShell", "rect": {"left": 0, "top": 0, "right": 640, "bottom": 480}},  # 新增代码+Phase28ComputerUse: 提供一个应被过滤的终端窗口；如果没有这行代码，禁止目标过滤不会被测试覆盖。
            {"hwnd": 77777, "pid": 300, "process_name": "empty.exe", "class_name": "Empty", "title": "", "rect": {"left": 0, "top": 0, "right": 10, "bottom": 10}},  # 新增代码+Phase28ComputerUse: 提供一个空标题窗口；如果没有这行代码，无效窗口过滤不会被测试覆盖。
        ]  # 新增代码+Phase28ComputerUse: 结束模拟窗口列表；如果没有这行代码，Python 列表语法不完整。

    def test_static_inventory_lists_safe_windows_and_groups_apps(self) -> None:  # 新增代码+Phase28ComputerUse: 验证只读 inventory 能列出安全窗口并按 app 分组；如果没有这个测试，窗口发现协议可能返回终端等禁止目标。
        inventory = StaticWindowsWindowInventory(raw_windows=self._raw_windows(), captured_at="2026-06-02T00:00:00Z")  # 新增代码+Phase28ComputerUse: 用静态 inventory 模拟 Windows 枚举；如果没有这行代码，测试会依赖真实桌面状态。
        backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False)  # 新增代码+Phase28ComputerUse: 创建只读 Windows 后端；如果没有这行代码，测试无法证明 inventory 不会启用鼠标键盘。
        controller = ComputerUseController(backend=backend)  # 新增代码+Phase28ComputerUse: 使用统一控制器执行 observe；如果没有这行代码，测试会绕过审计和动作枚举。
        windows_result = controller.observe({"action": "list_windows"})  # 新增代码+Phase28ComputerUse: 读取安全窗口列表；如果没有这行代码，无法验证窗口过滤和字段。
        apps_result = controller.observe({"action": "list_apps"})  # 新增代码+Phase28ComputerUse: 读取 app 分组列表；如果没有这行代码，无法验证 list_apps 结果。

        self.assertTrue(windows_result.ok)  # 新增代码+Phase28ComputerUse: 断言窗口观察成功；如果没有这行代码，后端失败不会暴露。
        self.assertEqual(len(windows_result.data["windows"]), 1)  # 新增代码+Phase28ComputerUse: 断言只剩一个安全窗口；如果没有这行代码，终端或空标题窗口可能混入结果。
        self.assertEqual(windows_result.data["filtered_count"], 2)  # 新增代码+Phase28ComputerUse: 断言过滤数量可见；如果没有这行代码，用户不知道为什么有些窗口不显示。
        self.assertEqual(windows_result.data["windows"][0]["app_id"], "notepad.exe")  # 新增代码+Phase28ComputerUse: 断言 app_id 来自进程名；如果没有这行代码，窗口身份可能不稳定。
        self.assertEqual(windows_result.data["windows"][0]["window_id"], "hwnd:12345")  # 新增代码+Phase28ComputerUse: 断言 window_id 稳定表达窗口句柄；如果没有这行代码，动作前校验无法引用窗口。
        self.assertEqual(apps_result.data["apps"][0]["app_id"], "notepad.exe")  # 新增代码+Phase28ComputerUse: 断言 app 列表包含安全应用；如果没有这行代码，list_apps 可能和 list_windows 不一致。
        self.assertEqual(apps_result.data["apps"][0]["window_count"], 1)  # 新增代码+Phase28ComputerUse: 断言 app 分组窗口数量正确；如果没有这行代码，模型无法知道应用下有几个窗口。

    def test_get_window_state_returns_window_relative_geometry_placeholders(self) -> None:  # 新增代码+Phase28ComputerUse: 验证窗口状态包含相对截图几何占位；如果没有这个测试，Phase 29 的截图/UIA 字段会缺稳定位置。
        inventory = StaticWindowsWindowInventory(raw_windows=self._raw_windows(), captured_at="2026-06-02T00:00:00Z")  # 新增代码+Phase28ComputerUse: 准备静态 inventory；如果没有这行代码，测试会依赖真实 Windows 枚举。
        backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False)  # 新增代码+Phase28ComputerUse: 创建只读 Windows 后端；如果没有这行代码，状态读取可能意外启用动作。
        controller = ComputerUseController(backend=backend)  # 新增代码+Phase28ComputerUse: 通过控制器执行 observe；如果没有这行代码，审计路径不会覆盖。
        window = controller.observe({"action": "list_windows"}).data["windows"][0]  # 新增代码+Phase28ComputerUse: 先读取可信窗口引用；如果没有这行代码，get_window_state 没有合法目标。
        state_result = controller.observe({"action": "get_window_state", "window": window})  # 新增代码+Phase28ComputerUse: 读取指定窗口状态；如果没有这行代码，无法验证状态合同。
        state = state_result.data["state"]  # 新增代码+Phase28ComputerUse: 取出状态对象；如果没有这行代码，后续断言目标不清楚。

        self.assertTrue(state_result.ok)  # 新增代码+Phase28ComputerUse: 断言窗口状态读取成功；如果没有这行代码，未知窗口或状态失败不会被发现。
        self.assertEqual(state["screenshot_width"], 300)  # 新增代码+Phase28ComputerUse: 断言窗口宽度由 rect 计算；如果没有这行代码，截图几何可能错误。
        self.assertEqual(state["screenshot_height"], 200)  # 新增代码+Phase28ComputerUse: 断言窗口高度由 rect 计算；如果没有这行代码，窗口相对坐标缺少正确尺寸。
        self.assertEqual(state["screenshot_origin"], {"x": 10, "y": 20})  # 新增代码+Phase28ComputerUse: 断言窗口原点稳定返回；如果没有这行代码，后续坐标转换缺基础数据。
        self.assertIn("Phase 29", state["accessibility_excerpt"])  # 新增代码+Phase28ComputerUse: 断言 UIA 文本仍是后续阶段占位；如果没有这行代码，本阶段可能误报已经实现 UI Automation。

    def test_read_only_windows_backend_rejects_desktop_actions(self) -> None:  # 新增代码+Phase28ComputerUse: 验证只读 Windows 后端不执行鼠标键盘动作；如果没有这个测试，Phase 28 可能越界扩大真实动作。
        inventory = StaticWindowsWindowInventory(raw_windows=self._raw_windows(), captured_at="2026-06-02T00:00:00Z")  # 新增代码+Phase28ComputerUse: 准备静态 inventory；如果没有这行代码，动作拒绝测试没有已知窗口。
        backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False)  # 新增代码+Phase28ComputerUse: 创建只读后端；如果没有这行代码，测试无法覆盖 real_actions_enabled=false。
        controller = ComputerUseController(backend=backend)  # 新增代码+Phase28ComputerUse: 通过控制器执行高风险动作；如果没有这行代码，确认门禁和窗口校验不会参与。
        window = controller.observe({"action": "list_windows"}).data["windows"][0]  # 新增代码+Phase28ComputerUse: 先获取可信窗口引用；如果没有这行代码，动作拒绝可能失败在未知窗口而不是只读后端。
        result = controller.execute({"action": "click", "confirm_desktop_control": True, "window": window, "x": 1, "y": 1})  # 新增代码+Phase28ComputerUse: 尝试对已知窗口执行点击；如果没有这行代码，无法证明只读后端拒绝动作。

        self.assertFalse(result.ok)  # 新增代码+Phase28ComputerUse: 断言点击被拒绝；如果没有这行代码，只读后端可能执行真实动作。
        self.assertIn("只读", result.message)  # 新增代码+Phase28ComputerUse: 断言拒绝原因说明只读边界；如果没有这行代码，模型不知道为什么动作失败。

    def test_windows_backend_status_explains_helper_boundary(self) -> None:  # 新增代码+Phase28ComputerUse: 验证真实后端状态说明 helper 边界；如果没有这个测试，用户会误以为 Phase 28 已有完整 native helper。
        inventory = StaticWindowsWindowInventory(raw_windows=self._raw_windows(), captured_at="2026-06-02T00:00:00Z")  # 新增代码+Phase28ComputerUse: 准备静态 inventory；如果没有这行代码，状态测试无法稳定报告 inventory 来源。
        backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False)  # 新增代码+Phase28ComputerUse: 创建只读 Windows 后端；如果没有这行代码，状态无法表达 read-only 模式。
        status = backend.status()  # 新增代码+Phase28ComputerUse: 读取后端状态；如果没有这行代码，后续断言没有状态数据。

        self.assertFalse(status["real_actions_enabled"])  # 新增代码+Phase28ComputerUse: 断言真实动作关闭；如果没有这行代码，Phase 28 可能误开鼠标键盘。
        self.assertTrue(status["read_only_inventory_enabled"])  # 新增代码+Phase28ComputerUse: 断言只读 inventory 已启用；如果没有这行代码，状态无法区分观察和动作。
        self.assertFalse(status["native_helper_available"])  # 新增代码+Phase28ComputerUse: 断言 C# native helper 尚未接入；如果没有这行代码，用户可能误解为已有 Windows.Graphics.Capture/UIA。
        self.assertIn("Phase 28", status["native_helper_reason"])  # 新增代码+Phase28ComputerUse: 断言状态说明当前阶段边界；如果没有这行代码，后续排查不知道 helper 何时接入。

    def test_default_backend_status_mentions_read_only_observe_gate(self) -> None:  # 新增代码+Phase28ComputerUse: 验证默认关闭状态也说明只读观察开关；如果没有这个测试，用户不知道如何安全启用窗口 inventory。
        backend = build_default_computer_use_backend(environ={})  # 新增代码+Phase28ComputerUse: 用空环境创建默认后端；如果没有这行代码，测试可能受真实环境变量污染。
        status = backend.status()  # 新增代码+Phase28ComputerUse: 读取默认状态；如果没有这行代码，无法断言状态提示字段。

        self.assertEqual(status["observe_opt_in_env_var"], COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR)  # 新增代码+Phase28ComputerUse: 断言状态暴露只读观察环境变量；如果没有这行代码，用户只能看到高风险动作开关。
        self.assertFalse(status["read_only_inventory_enabled"])  # 新增代码+Phase28ComputerUse: 断言默认只读窗口 inventory 未启用；如果没有这行代码，默认安全边界可能被误改。


if __name__ == "__main__":  # 新增代码+Phase28ComputerUse: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase28ComputerUse: 启动 unittest 主函数；如果没有这行代码，直接运行文件不会执行任何测试。
