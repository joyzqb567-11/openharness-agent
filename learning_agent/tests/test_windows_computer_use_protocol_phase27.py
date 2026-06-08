import unittest  # 新增代码+Phase27ComputerUse: 引入 unittest 测试框架；如果没有这行代码，本文件无法定义和运行 Phase 27 自动化测试。

from learning_agent.computer_use.controller import ComputerUseController, MemoryComputerUseBackend  # 新增代码+Phase27ComputerUse: 导入控制器和内存后端；如果没有这行代码，测试无法安全验证 Computer Use 协议。
from learning_agent.tools.catalog import build_builtin_tool_catalog  # 新增代码+Phase27ComputerUse: 导入工具目录构建函数；如果没有这行代码，测试无法确认只读观察工具的风险元数据。
from learning_agent.tools.schemas import TOOL_SCHEMAS  # 新增代码+Phase27ComputerUse: 导入内置工具 schema；如果没有这行代码，测试无法确认模型可见的 computer_observe 定义。


class WindowsComputerUseProtocolPhase27Tests(unittest.TestCase):  # 新增代码+Phase27ComputerUse: 定义 Phase 27 的 Windows Computer Use 协议测试集合；如果没有这个类，unittest 不会发现这些新增验收条件。
    def test_schema_exposes_read_only_computer_observe_tool(self) -> None:  # 新增代码+Phase27ComputerUse: 验证 schema 暴露只读观察工具；如果没有这个测试，模型可能永远看不到 observe 协议入口。
        schemas_by_name = {schema["function"]["name"]: schema for schema in TOOL_SCHEMAS}  # 新增代码+Phase27ComputerUse: 按工具名索引 schema；如果没有这行代码，后续断言无法快速定位目标工具。
        observe_schema = schemas_by_name["computer_observe"]["function"]["parameters"]  # 新增代码+Phase27ComputerUse: 读取 computer_observe 参数 schema；如果没有这行代码，测试无法确认 observe 形状是否受约束。
        action_enum = observe_schema["properties"]["action"]["enum"]  # 新增代码+Phase27ComputerUse: 读取只读观察动作枚举；如果没有这行代码，测试无法防止 observe 变成松散字符串。

        self.assertIn("computer_observe", schemas_by_name)  # 新增代码+Phase27ComputerUse: 确认模型可见 computer_observe；如果没有这行代码，新增工具缺失不会被发现。
        self.assertIn("list_windows", action_enum)  # 新增代码+Phase27ComputerUse: 确认 observe 支持列出窗口；如果没有这行代码，模型无法先发现可控制目标。
        self.assertIn("get_window_state", action_enum)  # 新增代码+Phase27ComputerUse: 确认 observe 支持读取窗口状态；如果没有这行代码，模型无法在动作前观察目标。
        self.assertNotIn("click", action_enum)  # 新增代码+Phase27ComputerUse: 确认 observe 不能混入写动作；如果没有这行代码，只读工具可能意外承载高风险动作。

    def test_catalog_marks_computer_observe_as_read_only_concurrency_safe(self) -> None:  # 新增代码+Phase27ComputerUse: 验证 catalog 把 observe 标成低风险只读；如果没有这个测试，权限层可能把观察工具当高风险动作。
        catalog = {tool.name: tool for tool in build_builtin_tool_catalog()}  # 新增代码+Phase27ComputerUse: 构建并索引内置工具目录；如果没有这行代码，测试无法读取 AgentTool 元数据。
        observe_tool = catalog["computer_observe"]  # 新增代码+Phase27ComputerUse: 取出只读观察工具；如果没有这行代码，后续断言没有目标对象。

        self.assertEqual(observe_tool.risk_level, "low")  # 新增代码+Phase27ComputerUse: 断言 observe 是低风险；如果没有这行代码，只读观察可能被错误升级或降级。
        self.assertTrue(observe_tool.is_read_only)  # 新增代码+Phase27ComputerUse: 断言 observe 是只读；如果没有这行代码，权限层无法自动区分观察和动作。
        self.assertTrue(observe_tool.is_concurrency_safe)  # 新增代码+Phase27ComputerUse: 断言 observe 可以并发读取；如果没有这行代码，状态观察会不必要地阻塞长任务。
        self.assertFalse(observe_tool.requires_user_interaction)  # 新增代码+Phase27ComputerUse: 断言 observe 不需要用户交互确认；如果没有这行代码，只读窗口状态也可能弹权限框。

    def test_controller_observe_lists_memory_windows_without_desktop_confirmation(self) -> None:  # 新增代码+Phase27ComputerUse: 验证只读观察无需 confirm_desktop_control；如果没有这个测试，观察工具会被高风险动作门禁误挡。
        backend = MemoryComputerUseBackend(windows=[{"app_id": "notepad", "window_id": "win-1", "title": "记事本"}])  # 新增代码+Phase27ComputerUse: 准备一个已知内存窗口；如果没有这行代码，测试没有可列出的窗口目标。
        controller = ComputerUseController(backend=backend)  # 新增代码+Phase27ComputerUse: 把内存后端交给控制器；如果没有这行代码，observe 无法走统一安全层。
        result = controller.observe({"action": "list_windows"})  # 新增代码+Phase27ComputerUse: 调用只读窗口列表观察；如果没有这行代码，测试无法证明 observe 不需要桌面控制确认。

        self.assertTrue(result.ok)  # 新增代码+Phase27ComputerUse: 断言只读观察成功；如果没有这行代码，observe 被拒绝不会暴露。
        self.assertEqual(result.data["windows"][0]["window_id"], "win-1")  # 新增代码+Phase27ComputerUse: 断言返回已知窗口 id；如果没有这行代码，窗口身份可能丢失。
        self.assertEqual(controller.status()["audit"]["event_count"], 1)  # 新增代码+Phase27ComputerUse: 断言只读观察也有审计事件；如果没有这行代码，窗口观察无法追踪。

    def test_controller_rejects_action_targeting_unknown_window(self) -> None:  # 新增代码+Phase27ComputerUse: 验证写动作不能指向未知窗口；如果没有这个测试，模型可能对错误窗口或伪造窗口执行动作。
        backend = MemoryComputerUseBackend(windows=[{"app_id": "notepad", "window_id": "win-1", "title": "记事本"}])  # 新增代码+Phase27ComputerUse: 准备唯一可信窗口；如果没有这行代码，测试无法区分已知和未知目标。
        controller = ComputerUseController(backend=backend)  # 新增代码+Phase27ComputerUse: 创建带窗口目录的控制器；如果没有这行代码，动作校验没有后端上下文。
        result = controller.execute({"action": "click", "confirm_desktop_control": True, "window": {"app_id": "notepad", "window_id": "ghost"}, "x": 1, "y": 2})  # 新增代码+Phase27ComputerUse: 故意把点击发给不存在的窗口；如果没有这行代码，未知窗口拒绝路径不会被覆盖。

        self.assertFalse(result.ok)  # 新增代码+Phase27ComputerUse: 断言未知窗口目标被拒绝；如果没有这行代码，安全校验失效不会被发现。
        self.assertIn("未知窗口", result.message)  # 新增代码+Phase27ComputerUse: 断言错误信息说清楚窗口未知；如果没有这行代码，模型不知道应先 observe 发现窗口。
        self.assertEqual(len(backend.actions), 0)  # 新增代码+Phase27ComputerUse: 断言后端没有收到危险动作；如果没有这行代码，拒绝后仍执行的回归无法发现。


if __name__ == "__main__":  # 新增代码+Phase27ComputerUse: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase27ComputerUse: 启动 unittest 主函数；如果没有这行代码，直接运行文件不会执行任何测试。
