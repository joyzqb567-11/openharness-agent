import json  # 新增代码+Phase46WindowsUiaTree: 导入 JSON 用于检查结构化树和场景 token；如果没有这行代码，测试无法确认敏感文本没有泄露。
import unittest  # 新增代码+Phase46WindowsUiaTree: 导入 unittest 框架承载 Phase46 测试；如果没有这行代码，自动化回归不会运行本阶段验收。
from pathlib import Path  # 新增代码+Phase46WindowsUiaTree: 导入 Path 稳定定位场景文件；如果没有这行代码，Windows 路径拼接会更脆。

from learning_agent.computer_use.native_host import InProcessWindowsNativeHostClient, WindowsComputerUseNativeHost  # 新增代码+Phase46WindowsUiaTree: 导入 native host 验证 UIA 树可通过 observe 消息返回；如果没有这行代码，Phase46 只停留在单模块自测。
from learning_agent.computer_use.uia_tree import PHASE46_WINDOWS_UIA_TREE_MARKER, PHASE46_WINDOWS_UIA_TREE_OK_TOKEN, WindowsUiaControlTreeRuntime, phase46_cli_line, run_phase46_uia_tree_contract  # 新增代码+Phase46WindowsUiaTree: 导入 Phase46 期望的新 UIA 树运行时；如果没有这行代码，红灯会证明结构化控件树尚未实现。


class FakePhase46Rect:  # 新增代码+Phase46WindowsUiaTree: 定义 fake UIA 矩形对象；如果没有这个类，测试无法覆盖真实 UIA 常见 BoundingRectangle 形态。
    def __init__(self, left: int, top: int, right: int, bottom: int) -> None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，保存矩形四边；如果没有这段函数，fake 控件没有边界框。
        self.Left = left  # 新增代码+Phase46WindowsUiaTree: 保存左边界；如果没有这行代码，runtime 无法读取控件 x 起点。
        self.Top = top  # 新增代码+Phase46WindowsUiaTree: 保存上边界；如果没有这行代码，runtime 无法读取控件 y 起点。
        self.Right = right  # 新增代码+Phase46WindowsUiaTree: 保存右边界；如果没有这行代码，runtime 无法计算控件宽度。
        self.Bottom = bottom  # 新增代码+Phase46WindowsUiaTree: 保存下边界；如果没有这行代码，runtime 无法计算控件高度。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，FakePhase46Rect.__init__ 到此结束；如果没有这个边界说明，读者不容易看出矩形样本范围。


class FakePhase46Control:  # 新增代码+Phase46WindowsUiaTree: 定义 fake UIA 控件节点；如果没有这个类，测试只能依赖用户机器真实 UIA。
    def __init__(self, name: str, role: str, automation_id: str = "", class_name: str = "", rect: FakePhase46Rect | None = None, children: list["FakePhase46Control"] | None = None, enabled: bool = True) -> None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，初始化 fake 控件；如果没有这段函数，测试无法构造稳定控件树。
        self.Name = name  # 新增代码+Phase46WindowsUiaTree: 保存控件名称；如果没有这行代码，runtime 无法提取可见文本。
        self.ControlTypeName = role  # 新增代码+Phase46WindowsUiaTree: 保存控件角色；如果没有这行代码，runtime 无法判断按钮或输入框语义。
        self.AutomationId = automation_id  # 新增代码+Phase46WindowsUiaTree: 保存 automation id；如果没有这行代码，控件定位线索会丢失。
        self.ClassName = class_name  # 新增代码+Phase46WindowsUiaTree: 保存 class name；如果没有这行代码，调试时缺少窗口类线索。
        self.BoundingRectangle = rect or FakePhase46Rect(0, 0, 0, 0)  # 新增代码+Phase46WindowsUiaTree: 保存边界框；如果没有这行代码，树节点无法返回坐标。
        self.IsEnabled = enabled  # 新增代码+Phase46WindowsUiaTree: 保存可用状态；如果没有这行代码，runtime 无法告诉用户控件是否禁用。
        self._children = list(children or [])  # 新增代码+Phase46WindowsUiaTree: 保存子控件副本；如果没有这行代码，树遍历没有下一层。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，FakePhase46Control.__init__ 到此结束；如果没有这个边界说明，读者不容易看出 fake 控件初始化范围。

    def GetChildren(self) -> list["FakePhase46Control"]:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，模拟 uiautomation 的子控件读取；如果没有这段函数，runtime 无法展开 fake 树。
        return list(self._children)  # 新增代码+Phase46WindowsUiaTree: 返回子控件副本；如果没有这行代码，调用方可能改写测试原始树。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，FakePhase46Control.GetChildren 到此结束；如果没有这个边界说明，读者不容易看出子控件接口范围。


class FakePhase46UiaModule:  # 新增代码+Phase46WindowsUiaTree: 定义 fake UIA 模块；如果没有这个类，runtime 测试需要安装真实 uiautomation 包。
    def __init__(self, root: FakePhase46Control) -> None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，保存 fake 根控件；如果没有这段函数，模块不知道从哪个控件开始。
        self.root = root  # 新增代码+Phase46WindowsUiaTree: 保存根控件；如果没有这行代码，ControlFromHandle 无法返回树入口。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，FakePhase46UiaModule.__init__ 到此结束；如果没有这个边界说明，读者不容易看出模块初始化范围。

    def ControlFromHandle(self, hwnd: int) -> FakePhase46Control:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，模拟从 hwnd 获取控件；如果没有这段函数，runtime 没有根节点入口。
        return self.root  # 新增代码+Phase46WindowsUiaTree: 返回 fake 根控件；如果没有这行代码，树观察会失败。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，FakePhase46UiaModule.ControlFromHandle 到此结束；如果没有这个边界说明，读者不容易看出句柄映射范围。


class WindowsComputerUseUiaTreePhase46Tests(unittest.TestCase):  # 新增代码+Phase46WindowsUiaTree: 定义 Phase46 测试集合；如果没有这个类，unittest 不会组织 UIA 树测试。
    def _window(self) -> dict[str, object]:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，提供稳定窗口引用；如果没有这段函数，测试会重复拼窗口 dict。
        return {"window_id": "hwnd:4601", "hwnd": 4601, "title": "Phase46 Window", "rect": {"left": 10, "top": 20, "right": 500, "bottom": 320}}  # 新增代码+Phase46WindowsUiaTree: 返回带 hwnd 和 rect 的窗口；如果没有这行代码，runtime 无法定位目标窗口。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，_window 到此结束；如果没有这个边界说明，读者不容易看出窗口样本范围。

    def _tree_module(self) -> FakePhase46UiaModule:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，构造含按钮和输入框的 fake 控件树；如果没有这段函数，每个测试都要重复搭树。
        save = FakePhase46Control("Save", "ButtonControl", automation_id="save", class_name="Button", rect=FakePhase46Rect(24, 60, 124, 92))  # 新增代码+Phase46WindowsUiaTree: 创建按钮节点；如果没有这行代码，clickable 摘要没有测试对象。
        editor = FakePhase46Control("Document", "EditControl", automation_id="editor", class_name="Edit", rect=FakePhase46Rect(24, 110, 460, 280))  # 新增代码+Phase46WindowsUiaTree: 创建输入节点；如果没有这行代码，editable 摘要没有测试对象。
        root = FakePhase46Control("Root Window", "WindowControl", automation_id="root", class_name="Window", rect=FakePhase46Rect(10, 20, 500, 320), children=[save, editor])  # 新增代码+Phase46WindowsUiaTree: 创建根窗口节点；如果没有这行代码，树没有入口。
        return FakePhase46UiaModule(root)  # 新增代码+Phase46WindowsUiaTree: 返回 fake UIA 模块；如果没有这行代码，runtime 不能从 hwnd 获取根控件。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，_tree_module 到此结束；如果没有这个边界说明，读者不容易看出树样本范围。

    def test_uia_tree_runtime_returns_structured_nodes_bounds_and_hints(self) -> None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，验证结构化控件树、边界框和动作提示；如果没有这个测试，Phase46 可能退化成纯文本摘要。
        runtime = WindowsUiaControlTreeRuntime(platform="win32", uia_module=self._tree_module(), max_depth=4, max_nodes=10)  # 新增代码+Phase46WindowsUiaTree: 创建注入 fake UIA 模块的 runtime；如果没有这行代码，测试会依赖真实桌面。
        result = runtime.observe_window(self._window())  # 新增代码+Phase46WindowsUiaTree: 执行一次控件树观察；如果没有这行代码，断言没有实际输入。
        self.assertTrue(result["captured"])  # 新增代码+Phase46WindowsUiaTree: 断言控件树读取成功；如果没有这行代码，失败结构也可能误通过。
        self.assertEqual(result["node_count"], 3)  # 新增代码+Phase46WindowsUiaTree: 断言根、按钮、输入框都被读取；如果没有这行代码，树遍历可能缺层级。
        self.assertEqual(result["tree"]["name"], "Root Window")  # 新增代码+Phase46WindowsUiaTree: 断言根节点名称稳定；如果没有这行代码，模型无法知道窗口上下文。
        self.assertEqual(result["tree"]["bounds"]["left"], 10)  # 新增代码+Phase46WindowsUiaTree: 断言根节点边界框被读取；如果没有这行代码，坐标能力可能缺失。
        self.assertTrue(result["flat_nodes"][1]["clickable"])  # 新增代码+Phase46WindowsUiaTree: 断言按钮节点可点击；如果没有这行代码，动作提示可能无效。
        self.assertTrue(result["flat_nodes"][2]["editable"])  # 新增代码+Phase46WindowsUiaTree: 断言输入节点可编辑；如果没有这行代码，输入提示可能无效。
        self.assertEqual(result["actions_expanded"], False)  # 新增代码+Phase46WindowsUiaTree: 断言本阶段仍不扩大真实动作面；如果没有这行代码，安全边界可能漂移。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，test_uia_tree_runtime_returns_structured_nodes_bounds_and_hints 到此结束；如果没有这个边界说明，读者不容易看出结构化树测试范围。

    def test_uia_tree_runtime_redacts_sensitive_text_and_limits_nodes(self) -> None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，验证敏感节点脱敏和节点上限；如果没有这个测试，UIA 树可能泄露密码或无限输出。
        secret = FakePhase46Control("password: phase46-secret", "EditControl", automation_id="secret", class_name="Edit", rect=FakePhase46Rect(1, 1, 20, 20))  # 新增代码+Phase46WindowsUiaTree: 创建敏感节点；如果没有这行代码，脱敏测试没有目标。
        extra = FakePhase46Control("Extra", "ButtonControl", automation_id="extra", class_name="Button", rect=FakePhase46Rect(2, 2, 30, 30))  # 新增代码+Phase46WindowsUiaTree: 创建超过上限的节点；如果没有这行代码，truncated 标记无法被测试。
        root = FakePhase46Control("Root", "WindowControl", children=[secret, extra])  # 新增代码+Phase46WindowsUiaTree: 创建根节点；如果没有这行代码，敏感节点无法挂到树里。
        runtime = WindowsUiaControlTreeRuntime(platform="win32", uia_module=FakePhase46UiaModule(root), max_depth=4, max_nodes=2)  # 新增代码+Phase46WindowsUiaTree: 设置节点上限为 2；如果没有这行代码，节点截断路径不会触发。
        result = runtime.observe_window(self._window())  # 新增代码+Phase46WindowsUiaTree: 执行控件树观察；如果没有这行代码，脱敏和截断都不会发生。
        encoded = json.dumps(result, ensure_ascii=False).lower()  # 新增代码+Phase46WindowsUiaTree: 序列化结果用于全局泄露检查；如果没有这行代码，只检查单字段可能漏掉泄露。
        self.assertTrue(result["captured"])  # 新增代码+Phase46WindowsUiaTree: 断言读取成功；如果没有这行代码，失败结果可能绕过脱敏断言。
        self.assertTrue(result["truncated"])  # 新增代码+Phase46WindowsUiaTree: 断言节点上限触发截断；如果没有这行代码，大树可能无限输出。
        self.assertGreaterEqual(result["sensitive_text_filtered"], 1)  # 修改代码+Phase46WindowsUiaTree: 断言至少发生一次敏感字段过滤；如果没有这行代码，automation_id 等额外敏感字段被过滤时测试会误判更安全的行为为失败。
        self.assertNotIn("phase46-secret", encoded)  # 新增代码+Phase46WindowsUiaTree: 断言具体敏感值没有泄露；如果没有这行代码，UIA 树可能把密码写进日志。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，test_uia_tree_runtime_redacts_sensitive_text_and_limits_nodes 到此结束；如果没有这个边界说明，读者不容易看出脱敏测试范围。

    def test_native_host_observe_can_use_uia_tree_runtime(self) -> None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，验证 native host observe 可接入 UIA 树；如果没有这个测试，Phase46 和 Phase44 host 可能割裂。
        runtime = WindowsUiaControlTreeRuntime(platform="win32", uia_module=self._tree_module(), max_depth=4, max_nodes=10)  # 新增代码+Phase46WindowsUiaTree: 创建 fake UIA tree runtime；如果没有这行代码，host 没有结构化观察来源。
        host = WindowsComputerUseNativeHost(platform="win32", uia_tree_runtime=runtime)  # 新增代码+Phase46WindowsUiaTree: 把 UIA 树 runtime 注入 native host；如果没有这行代码，observe 仍只返回旧文本摘要。
        response = InProcessWindowsNativeHostClient(host).request({"op": "observe", "window": self._window()})  # 新增代码+Phase46WindowsUiaTree: 通过 host observe 消息读取树；如果没有这行代码，集成路径不会执行。
        self.assertTrue(response["ok"])  # 新增代码+Phase46WindowsUiaTree: 断言 host 响应成功；如果没有这行代码，host 错误可能被忽略。
        self.assertTrue(response["result"]["captured"])  # 新增代码+Phase46WindowsUiaTree: 断言 host 返回 UIA 树成功；如果没有这行代码，空响应也可能误通过。
        self.assertEqual(response["result"]["node_count"], 3)  # 新增代码+Phase46WindowsUiaTree: 断言 host 保留节点数量；如果没有这行代码，树结构可能在 host 脱敏时丢失。
        self.assertFalse(response["result"]["actions_expanded"])  # 新增代码+Phase46WindowsUiaTree: 断言 host observe 不扩大动作面；如果没有这行代码，安全边界不可见。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，test_native_host_observe_can_use_uia_tree_runtime 到此结束；如果没有这个边界说明，读者不容易看出 host 集成范围。

    def test_phase46_cli_contract_and_visible_terminal_scenario_tokens(self) -> None:  # 新增代码+Phase46WindowsUiaTree: 函数段开始，验证 CLI 和真实终端场景 token；如果没有这个测试，验收配置可能漏掉关键条件。
        report = run_phase46_uia_tree_contract()  # 新增代码+Phase46WindowsUiaTree: 运行安全自检合同；如果没有这行代码，CLI 行没有真实输入。
        cli_line = phase46_cli_line(report)  # 新增代码+Phase46WindowsUiaTree: 生成稳定 token 行；如果没有这行代码，场景无法复用同一格式。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase46_windows_uia_tree.json")  # 新增代码+Phase46WindowsUiaTree: 定位 Phase46 场景文件；如果没有这行代码，测试无法确认真实终端配置。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase46WindowsUiaTree: 读取场景文本；如果没有这行代码，场景缺失不会暴露。
        expected_tokens = {PHASE46_WINDOWS_UIA_TREE_MARKER, PHASE46_WINDOWS_UIA_TREE_OK_TOKEN, "tree=true", "bounds=true", "controls=true", "redacted=true", "host_observe=true", "actions_expanded=false"}  # 新增代码+Phase46WindowsUiaTree: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准会漂移。
        for token in expected_tokens:  # 新增代码+Phase46WindowsUiaTree: 遍历关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase46WindowsUiaTree: 断言 CLI 行包含 token；如果没有这行代码，自检输出可能不稳定。
            self.assertIn(token, scenario_text)  # 新增代码+Phase46WindowsUiaTree: 断言场景包含 token；如果没有这行代码，真实终端验收可能漏检。
    # 新增代码+Phase46WindowsUiaTree: 函数段结束，test_phase46_cli_contract_and_visible_terminal_scenario_tokens 到此结束；如果没有这个边界说明，读者不容易看出场景测试范围。


if __name__ == "__main__":  # 新增代码+Phase46WindowsUiaTree: 允许直接运行本测试文件；如果没有这行代码，初学者无法单独启动 Phase46 测试。
    unittest.main()  # 新增代码+Phase46WindowsUiaTree: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
