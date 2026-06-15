"""Computer Use MCP v2 主执行路径与诊断路径验收测试。"""  # 新增代码+ComputerUseMcpV2PrimaryPath：说明本文件只验证 agent-side 主路径和 stdio 诊断路径；如果没有这行代码，后续维护者不容易看懂这个测试文件的职责。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2PrimaryPath：延迟解析类型注解，避免测试导入阶段因类型前置求值失败；如果没有这行代码，旧 Python 环境可能提前解析类型而报错。

import json  # 新增代码+ComputerUseMcpV2PrimaryPath：用于解析工具返回的 JSON 文本；如果没有这行代码，测试只能靠不可靠的字符串包含判断。
import tempfile  # 新增代码+ComputerUseMcpV2PrimaryPath：用于创建隔离的临时 workspace；如果没有这行代码，fake agent 测试可能污染真实项目目录。
import unittest  # 新增代码+ComputerUseMcpV2PrimaryPath：使用标准 unittest 框架发现和运行测试；如果没有这行代码，本文件不会被测试系统正常执行。
from pathlib import Path  # 新增代码+ComputerUseMcpV2PrimaryPath：用 Path 表示临时目录路径；如果没有这行代码，fake agent 的 workspace 类型会和真实代码不一致。

from learning_agent.computer_use_mcp_v2.claudecode_bridge.mcpServer import handle_json_rpc_message  # 新增代码+ComputerUseMcpV2PrimaryPath：直接调用 v2 stdio server 的 JSON-RPC 分发函数；如果没有这行代码，测试无法验证 stdio tools/call 的诊断标记。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2PrimaryPath：创建最小 v2 runtime 上下文；如果没有这行代码，server 分发函数没有执行环境。
from learning_agent.core.messages import ToolCall  # 新增代码+ComputerUseMcpV2PrimaryPath：使用真实工具调用对象模拟模型请求；如果没有这行代码，测试无法覆盖 agent 顶层入口。
from learning_agent.mcp.agent_adapter import execute_mcp_tool  # 新增代码+ComputerUseMcpV2PrimaryPath：导入真实 agent-side MCP 执行函数；如果没有这行代码，主路径测试只能测底层函数而不是顶层路由。
from learning_agent.tests.test_computer_use_mcp_agent_side_binding import _FakeAgent  # 新增代码+ComputerUseMcpV2PrimaryPath：复用已有阻断 registry 的 fake agent；如果没有这行代码，测试需要重复造假对象且更容易和真实入口脱节。


class ComputerUseMcpV2PrimaryPathTests(unittest.TestCase):  # 新增代码+ComputerUseMcpV2PrimaryPath：函数段开始，集中验证 agent-side wrapper 是主执行路径；如果没有这段测试，外部 registry 回归抢占 Computer Use 工具时不容易被发现。
    def test_agent_side_list_granted_applications_bypasses_registry_call_tool(self) -> None:  # 新增代码+ComputerUseMcpV2PrimaryPath：验证只读工具也必须绕过外部 registry.call_tool；如果没有这行测试，只测 request_access 会留下发现链路空洞。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseMcpV2PrimaryPath：创建临时目录隔离 fake agent 状态；如果没有这行代码，测试可能写入真实 workspace。
            agent = _FakeAgent(Path(raw_dir))  # 新增代码+ComputerUseMcpV2PrimaryPath：创建带阻断 registry 的 fake agent；如果没有这行代码，就无法证明 registry.call_tool 没被触发。
            output = execute_mcp_tool(agent, ToolCall(name="mcp__computer-use__list_granted_applications", arguments={}))  # 新增代码+ComputerUseMcpV2PrimaryPath：通过模型可见工具名调用 v2 工具；如果没有这行代码，测试无法覆盖真实 agent 顶层路由。
            payload = json.loads(output)  # 新增代码+ComputerUseMcpV2PrimaryPath：把返回文本解析成结构化 JSON；如果没有这行代码，测试只能做脆弱的字符串判断。
            self.assertTrue(payload["ok"], payload)  # 新增代码+ComputerUseMcpV2PrimaryPath：确认工具执行成功；如果没有这行代码，失败结果也可能被误认为走通了路由。
            self.assertEqual("computer_use_mcp_v2", payload["runtime"])  # 新增代码+ComputerUseMcpV2PrimaryPath：确认结果来自 v2 runtime；如果没有这行代码，旧 adapter 或假返回可能混进来。
            self.assertEqual(agent.mcp_tool_registry.calls, [])  # 新增代码+ComputerUseMcpV2PrimaryPath：确认外部 registry.call_tool 完全没有被调用；如果没有这行代码，最关键的主路径约束无法被自动发现。
            self.assertIn("completed", [event["state"] for event in agent.mcp_call_progress_events])  # 新增代码+ComputerUseMcpV2PrimaryPath：确认 agent 顶层仍记录 MCP 调用完成状态；如果没有这行代码，绕过 registry 时可能也绕过审计链。

    def test_standalone_stdio_tools_call_marks_diagnostic_channel(self) -> None:  # 新增代码+ComputerUseMcpV2PrimaryPath：验证独立 stdio server 的 tools/call 会标记诊断通道；如果没有这行测试，stdio callTool 很容易被误认为生产主路径。
        response = handle_json_rpc_message({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "list_granted_applications", "arguments": {}}}, ComputerUseMcpV2Context())  # 新增代码+ComputerUseMcpV2PrimaryPath：直接构造最小 JSON-RPC 工具调用；如果没有这行代码，测试无法稳定覆盖 stdio server 分发逻辑。
        response_text = json.dumps(response, ensure_ascii=False, sort_keys=True)  # 新增代码+ComputerUseMcpV2PrimaryPath：把响应转成可搜索文本；如果没有这行代码，嵌套 content 结构里的标记不好断言。
        self.assertIn("standalone_stdio_diagnostic", response_text)  # 新增代码+ComputerUseMcpV2PrimaryPath：要求 stdio callTool 明确声明自己只是诊断通道；如果没有这行代码，后续会再次混淆主路径和独立 server 调试路径。
    # 新增代码+ComputerUseMcpV2PrimaryPath：函数段结束，ComputerUseMcpV2PrimaryPathTests 到此结束；如果没有这个边界说明，用户不容易看出本类只覆盖主路径和诊断路径。


if __name__ == "__main__":  # 新增代码+ComputerUseMcpV2PrimaryPath：允许直接运行本测试文件；如果没有这行代码，手动调试只能通过模块名运行。
    unittest.main()  # 新增代码+ComputerUseMcpV2PrimaryPath：启动 unittest 主程序；如果没有这行代码，直接运行文件不会执行测试。
