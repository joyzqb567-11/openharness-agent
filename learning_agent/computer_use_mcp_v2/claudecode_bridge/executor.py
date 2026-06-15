"""Computer Use MCP v2 ClaudeCode 风格执行桥接。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode executor.ts；如果没有这行代码，执行入口没有同构文件。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型引用可能提前求值。

from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用类型；如果没有这行代码，执行函数参数边界不清楚。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import ComputerUseMcpV2Context, dispatch_computer_use_mcp_v2_tool  # 新增代码+ComputerUseMcpV2：导入 v2 runtime；如果没有这行代码，桥接执行器没有真实分发。


def execute_tool(tool_name: str, arguments: dict[str, Any] | None = None, context: ComputerUseMcpV2Context | None = None) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，执行 v2 工具；如果没有这段函数，mcpServer/wrapper 不能共享执行入口。
    return dispatch_computer_use_mcp_v2_tool(tool_name, arguments or {}, context)  # 新增代码+ComputerUseMcpV2：委托统一 runtime；如果没有这行代码，桥接层和推断包会分裂。
# 新增代码+ComputerUseMcpV2：函数段结束，execute_tool 到此结束；如果没有这个边界说明，用户不容易看出执行桥接范围。

