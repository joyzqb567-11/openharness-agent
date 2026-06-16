from __future__ import annotations  # 新增代码+ClaudeCodeDynamicToolsListTests：延迟类型注解解析；如果没有这行代码，测试导入时类型注解可能提前求值。
import time  # 新增代码+ClaudeCodeDynamicToolsListTests：用于模拟慢 inventory loader；如果没有这行代码，timeout 分支没有真实等待输入。
import unittest  # 新增代码+ClaudeCodeDynamicToolsListTests：使用标准 unittest 框架；如果没有这行代码，测试类不会被发现和执行。
from unittest.mock import patch  # 新增代码+ClaudeCodeDynamicToolsListTests：用于替换动态 inventory loader；如果没有这行代码，tools/list 测试会依赖真实 Windows 环境。

from learning_agent.computer_use_mcp_v2.claudecode_bridge import mcpServer  # 新增代码+ClaudeCodeDynamicToolsListTests：导入真实 MCP server 模块；如果没有这行代码，无法测试 tools/list JSON-RPC 接线。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import computer_use_mcp_tools  # 新增代码+ClaudeCodeDynamicToolsListTests：导入工具 schema 构造器；如果没有这行代码，无法单测 request_access 描述注入。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import ComputerUseMcpV2Context  # 新增代码+ClaudeCodeDynamicToolsListTests：导入真实 context；如果没有这行代码，tools/list trace 回调没有容器。


def _request_access_description(tools: list[dict[str, object]]) -> str:  # 新增代码+ClaudeCodeDynamicToolsListTests：函数段开始，从工具列表里取 request_access 描述；如果没有这段函数，每个测试都要重复遍历。
    request_tools = [tool for tool in tools if tool.get("name") == "request_access"]  # 新增代码+ClaudeCodeDynamicToolsListTests：筛选 request_access 工具；如果没有这行代码，断言无法定位目标工具。
    assert request_tools, "request_access tool missing"  # 新增代码+ClaudeCodeDynamicToolsListTests：确保目标工具存在；如果没有这行代码，后续索引会给出不清楚错误。
    return str(request_tools[0].get("description", ""))  # 新增代码+ClaudeCodeDynamicToolsListTests：返回描述文本；如果没有这行代码，调用方拿不到断言对象。
# 新增代码+ClaudeCodeDynamicToolsListTests：函数段结束，_request_access_description 到此结束；如果没有这个边界说明，用户不容易看出工具描述读取范围。


class ComputerUseMcpV2DynamicToolsListTests(unittest.TestCase):  # 新增代码+ClaudeCodeDynamicToolsListTests：类段开始，锁定 ClaudeCode-style tools/list 动态 app inventory；如果没有这段类，动态提示回归没有自动化保护。
    def test_build_tools_injects_app_inventory_hint_into_request_access_description(self) -> None:  # 新增代码+ClaudeCodeDynamicToolsListTests：函数段开始，验证 build_tools 支持注入动态 hint；如果没有这段测试，schema 构造器可能只能返回静态描述。
        hint = "Available desktop application candidates: Notepad [app_name=notepad]."  # 新增代码+ClaudeCodeDynamicToolsListTests：准备安全应用候选提示；如果没有这行代码，注入路径没有输入。
        description = _request_access_description(computer_use_mcp_tools(app_inventory_hint=hint))  # 新增代码+ClaudeCodeDynamicToolsListTests：构造带 hint 的工具列表并读取描述；如果没有这行代码，无法验证描述合并。
        self.assertIn("请求受控桌面应用访问权限", description)  # 修改代码+ClaudeCodeDynamicToolsListTests：断言静态授权说明仍存在；如果没有这行代码，动态 hint 可能覆盖基础 request_access 文案。
        self.assertIn("Notepad", description)  # 新增代码+ClaudeCodeDynamicToolsListTests：断言安全应用名进入描述；如果没有这行代码，动态 app inventory 缺失不会失败。
        self.assertIn("apps/reason/grantFlags", description)  # 新增代码+ClaudeCodeDynamicToolsListTests：断言静态 ClaudeCode 字段说明仍保留；如果没有这行代码，动态注入可能覆盖基础 schema 文案。
    # 新增代码+ClaudeCodeDynamicToolsListTests：函数段结束，test_build_tools_injects_app_inventory_hint_into_request_access_description 到此结束；如果没有这个边界说明，用户不容易看出 build_tools 注入测试范围。

    def test_tools_list_injects_windows_app_inventory_hint_and_records_trace(self) -> None:  # 新增代码+ClaudeCodeDynamicToolsListTests：函数段开始，验证 JSON-RPC tools/list 会动态注入 app inventory；如果没有这段测试，server 接线可能只在 helper 层通过。
        events: list[dict[str, object]] = []  # 新增代码+ClaudeCodeDynamicToolsListTests：准备 trace 事件容器；如果没有这行代码，无法验证 debug trace。
        context = ComputerUseMcpV2Context(record_runtime_trace=lambda event: events.append(dict(event)))  # 新增代码+ClaudeCodeDynamicToolsListTests：创建带 trace 回调的 context；如果没有这行代码，tools/list inventory 状态不可观测。
        fake_inventory = {"hint": "Available desktop application candidates: Paint [app_name=mspaint].", "debug": {"status": "ok", "elapsed_seconds": 0.01}}  # 新增代码+ClaudeCodeDynamicToolsListTests：准备 fake inventory 结果；如果没有这行代码，测试会依赖真实系统应用。
        with patch.object(mcpServer, "_load_windows_app_inventory_hint", return_value=fake_inventory):  # 新增代码+ClaudeCodeDynamicToolsListTests：替换 inventory loader；如果没有这行代码，测试无法稳定控制 tools/list 输出。
            response = mcpServer.handle_json_rpc_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, context)  # 新增代码+ClaudeCodeDynamicToolsListTests：执行真实 JSON-RPC tools/list；如果没有这行代码，server 分支没有被覆盖。
        tools = response["result"]["tools"]  # 新增代码+ClaudeCodeDynamicToolsListTests：读取返回工具列表；如果没有这行代码，后续断言没有对象。
        description = _request_access_description(tools)  # 新增代码+ClaudeCodeDynamicToolsListTests：读取 request_access 描述；如果没有这行代码，无法检查动态候选。
        self.assertIn("Paint", description)  # 新增代码+ClaudeCodeDynamicToolsListTests：断言动态安全应用名进入 tools/list；如果没有这行代码，ClaudeCode 动态 appNames 行为没有对齐。
        self.assertEqual("ok", events[0]["status"])  # 新增代码+ClaudeCodeDynamicToolsListTests：断言 trace 记录成功状态；如果没有这行代码，成功路径不可审计。
        self.assertEqual("computer_use_tools_list_app_inventory", events[0]["event"])  # 新增代码+ClaudeCodeDynamicToolsListTests：断言 trace 事件名稳定；如果没有这行代码，后续排查无法定位 tools/list inventory。
    # 新增代码+ClaudeCodeDynamicToolsListTests：函数段结束，test_tools_list_injects_windows_app_inventory_hint_and_records_trace 到此结束；如果没有这个边界说明，用户不容易看出 JSON-RPC 注入测试范围。

    def test_inventory_hint_loader_times_out_and_returns_empty_hint(self) -> None:  # 新增代码+ClaudeCodeDynamicToolsListTests：函数段开始，验证慢 inventory 不会卡住 tools/list；如果没有这段测试，1 秒预算可能失效。
        def slow_loader() -> str:  # 新增代码+ClaudeCodeDynamicToolsListTests：函数段开始，模拟慢 Windows inventory；如果没有这段函数，timeout helper 没有慢输入。
            time.sleep(0.05)  # 新增代码+ClaudeCodeDynamicToolsListTests：睡眠超过测试超时预算；如果没有这行代码，timeout 分支不会触发。
            return "late inventory"  # 新增代码+ClaudeCodeDynamicToolsListTests：返回本不应被主线程等待到的文本；如果没有这行代码，worker 成功路径不完整。
        # 新增代码+ClaudeCodeDynamicToolsListTests：函数段结束，slow_loader 到此结束；如果没有这个边界说明，用户不容易看出慢 loader 范围。
        result = mcpServer._load_windows_app_inventory_hint(timeout_seconds=0.001, loader=slow_loader)  # 新增代码+ClaudeCodeDynamicToolsListTests：用极短预算执行 helper；如果没有这行代码，timeout 行为没有被调用。
        self.assertEqual("", result["hint"])  # 新增代码+ClaudeCodeDynamicToolsListTests：断言超时时不注入任何 hint；如果没有这行代码，过期结果可能污染 schema。
        self.assertEqual("timeout", result["debug"]["status"])  # 新增代码+ClaudeCodeDynamicToolsListTests：断言 debug 标明 timeout；如果没有这行代码，超时无法审计。
    # 新增代码+ClaudeCodeDynamicToolsListTests：函数段结束，test_inventory_hint_loader_times_out_and_returns_empty_hint 到此结束；如果没有这个边界说明，用户不容易看出 timeout 测试范围。

    def test_tools_list_falls_back_to_static_schema_when_inventory_fails(self) -> None:  # 新增代码+ClaudeCodeDynamicToolsListTests：函数段开始，验证 inventory 异常时 tools/list 不崩溃；如果没有这段测试，动态注入可能破坏工具发现。
        events: list[dict[str, object]] = []  # 新增代码+ClaudeCodeDynamicToolsListTests：准备 trace 事件容器；如果没有这行代码，无法检查错误状态是否记录。
        context = ComputerUseMcpV2Context(record_runtime_trace=lambda event: events.append(dict(event)))  # 新增代码+ClaudeCodeDynamicToolsListTests：创建带 trace 回调的 context；如果没有这行代码，异常回退不可观测。
        with patch.object(mcpServer, "_load_windows_app_inventory_hint", side_effect=RuntimeError("inventory failed")):  # 新增代码+ClaudeCodeDynamicToolsListTests：模拟 helper 级异常；如果没有这行代码，异常回退路径没有输入。
            response = mcpServer.handle_json_rpc_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, context)  # 新增代码+ClaudeCodeDynamicToolsListTests：执行 tools/list；如果没有这行代码，server 回退分支没有被覆盖。
        tools = response["result"]["tools"]  # 新增代码+ClaudeCodeDynamicToolsListTests：读取工具列表；如果没有这行代码，无法确认 schema 仍返回。
        description = _request_access_description(tools)  # 新增代码+ClaudeCodeDynamicToolsListTests：读取 request_access 描述；如果没有这行代码，无法检查是否静态回退。
        self.assertIn("request_access", {tool["name"] for tool in tools})  # 新增代码+ClaudeCodeDynamicToolsListTests：断言 request_access 仍存在；如果没有这行代码，工具发现崩溃不会失败。
        self.assertNotIn("Paint [app_name=mspaint]", description)  # 新增代码+ClaudeCodeDynamicToolsListTests：断言失败时没有注入 fake 候选；如果没有这行代码，错误状态可能带入旧 hint。
        self.assertEqual("error", events[0]["status"])  # 新增代码+ClaudeCodeDynamicToolsListTests：断言错误状态被 trace 记录；如果没有这行代码，失败原因无法审计。
    # 新增代码+ClaudeCodeDynamicToolsListTests：函数段结束，test_tools_list_falls_back_to_static_schema_when_inventory_fails 到此结束；如果没有这个边界说明，用户不容易看出回退测试范围。
# 新增代码+ClaudeCodeDynamicToolsListTests：类段结束，ComputerUseMcpV2DynamicToolsListTests 到此结束；如果没有这个边界说明，用户不容易看出 dynamic tools/list 测试范围。


if __name__ == "__main__":  # 新增代码+ClaudeCodeDynamicToolsListTests：允许直接运行本测试文件；如果没有这行代码，手动调试不方便。
    unittest.main()  # 新增代码+ClaudeCodeDynamicToolsListTests：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
