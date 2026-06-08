import unittest  # 新增代码+OSComputerUse: 引入 unittest 测试框架；若没有这行代码，本文件无法定义和运行测试用例。

from learning_agent.computer_use.controller import ComputerUseController, MemoryComputerUseBackend  # 新增代码+OSComputerUse: 导入 Computer Use 控制器和测试后端；若没有这行代码，测试无法验证新能力入口。
from learning_agent.tools.catalog import build_builtin_tool_catalog  # 新增代码+OSComputerUse: 导入工具目录构建函数；若没有这行代码，测试无法确认工具元数据是否进入 catalog。
from learning_agent.tools.schemas import TOOL_SCHEMAS  # 新增代码+OSComputerUse: 导入内置工具 schema；若没有这行代码，测试无法确认模型可见工具定义存在。


class OsComputerUseStage17Tests(unittest.TestCase):  # 新增代码+OSComputerUse: 定义 Phase 5 的 OS Computer Use 测试集合；若没有这段代码，新增能力没有自动化验收。
    def test_schema_exposes_status_and_action_tools(self) -> None:  # 新增代码+OSComputerUse: 验证 schema 暴露两个新工具；若没有这段测试，模型可能看不到 Computer Use 入口仍被误判通过。
        names = {schema["function"]["name"] for schema in TOOL_SCHEMAS}  # 新增代码+OSComputerUse: 收集所有内置工具名称；若没有这行代码，断言无法定位新工具是否注册。
        self.assertIn("computer_status", names)  # 新增代码+OSComputerUse: 确认只读状态工具存在；若没有这行代码，状态入口缺失不会被发现。
        self.assertIn("computer_action", names)  # 新增代码+OSComputerUse: 确认桌面动作工具存在；若没有这行代码，动作入口缺失不会被发现。

    def test_catalog_marks_computer_action_as_high_risk_interactive(self) -> None:  # 新增代码+OSComputerUse: 验证工具目录给桌面动作正确风险元数据；若没有这段测试，高风险动作可能被错误并发或自动允许。
        catalog = {tool.name: tool for tool in build_builtin_tool_catalog()}  # 新增代码+OSComputerUse: 构建内置工具目录并按名称索引；若没有这行代码，断言无法读取 AgentTool 元数据。
        action_tool = catalog["computer_action"]  # 新增代码+OSComputerUse: 取出桌面动作工具；若没有这行代码，后续断言没有目标对象。
        self.assertEqual(action_tool.risk_level, "high")  # 新增代码+OSComputerUse: 桌面动作必须是高风险；若没有这行代码，安全级别降低不会被发现。
        self.assertTrue(action_tool.requires_user_interaction)  # 新增代码+OSComputerUse: 桌面动作必须标记依赖用户可见环境；若没有这行代码，调度器可能错误并发执行。
        self.assertFalse(action_tool.is_concurrency_safe)  # 新增代码+OSComputerUse: 桌面动作不能并发；若没有这行代码，多个鼠标键盘动作可能乱序。

    def test_controller_rejects_action_without_explicit_confirmation(self) -> None:  # 新增代码+OSComputerUse: 验证动作必须带显式确认字段；若没有这段测试，模型可能绕过桌面控制确认。
        controller = ComputerUseController(backend=MemoryComputerUseBackend())  # 新增代码+OSComputerUse: 使用内存后端避免真实控制桌面；若没有这行代码，测试可能产生系统副作用。
        result = controller.execute({"action": "click"})  # 新增代码+OSComputerUse: 故意不传 confirm_desktop_control；若没有这行代码，无法触发安全拒绝路径。
        self.assertFalse(result.ok)  # 新增代码+OSComputerUse: 未确认动作必须失败；若没有这行代码，安全拒绝不会被验证。
        self.assertIn("confirm_desktop_control", result.message)  # 新增代码+OSComputerUse: 错误说明必须告诉模型如何修正；若没有这行代码，失败信息可能不可操作。

    def test_memory_backend_records_confirmed_action(self) -> None:  # 新增代码+OSComputerUse: 验证测试后端能记录已确认动作；若没有这段测试，后端协议可能只会拒绝无法证明执行路径。
        backend = MemoryComputerUseBackend()  # 新增代码+OSComputerUse: 创建不会碰真实桌面的内存后端；若没有这行代码，测试无法安全观察动作记录。
        controller = ComputerUseController(backend=backend)  # 新增代码+OSComputerUse: 把内存后端挂到控制器；若没有这行代码，execute 无法到达后端。
        result = controller.execute({"action": "click", "confirm_desktop_control": True, "x": 10, "y": 20})  # 新增代码+OSComputerUse: 执行一次已确认点击；若没有这行代码，无法验证成功路径。
        self.assertTrue(result.ok)  # 新增代码+OSComputerUse: 已确认且后端可用的动作应成功；若没有这行代码，成功路径坏掉不会被发现。
        self.assertEqual(backend.actions[0]["action"], "click")  # 新增代码+OSComputerUse: 确认后端记录点击动作；若没有这行代码，动作名可能被传错。
        self.assertEqual(backend.actions[0]["x"], 10)  # 新增代码+OSComputerUse: 确认 x 坐标被保留；若没有这行代码，坐标参数丢失不会被发现。


if __name__ == "__main__":  # 新增代码+OSComputerUse: 允许直接运行本测试文件；若没有这行代码，初学者无法用 python 文件方式启动测试。
    unittest.main()  # 新增代码+OSComputerUse: 启动 unittest 主函数；若没有这行代码，直接运行文件不会执行测试。
