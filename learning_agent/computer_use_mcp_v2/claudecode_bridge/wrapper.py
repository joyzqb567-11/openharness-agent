"""Computer Use MCP v2 agent-side wrapper 桥接。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode wrapper.tsx；如果没有这行代码，agent-side 绑定入口没有同构位置。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

import json  # 新增代码+ComputerUseMcpV2：导入 JSON 用于返回模型可读文本；如果没有这行代码，wrapper 无法稳定输出。
from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用类型；如果没有这行代码，agent 和 ToolCall duck typing 边界不清楚。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.bind_session_context import bind_session_context  # 新增代码+ComputerUseMcpV2：导入 agent-side 上下文绑定；如果没有这行代码，wrapper 拿不到主循环回调。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import dispatch_computer_use_mcp_v2_tool  # 新增代码+ComputerUseMcpV2：导入统一 runtime；如果没有这行代码，wrapper 无法执行工具。


def execute_agent_side_tool(agent: Any, tool_name: str, arguments: dict[str, Any]) -> str:  # 新增代码+ComputerUseMcpV2：函数段开始，在 agent 主循环内执行 v2 工具；如果没有这段函数，mcp__computer-use__ 仍会走旧 adapter。
    context = bind_session_context(agent)  # 新增代码+ComputerUseMcpV2：绑定或复用 agent 回调上下文；如果没有这行代码，v2 工具拿不到权限、trace 和观察回调。
    result = dispatch_computer_use_mcp_v2_tool(tool_name, arguments, context)  # 新增代码+ComputerUseMcpV2：执行 v2 runtime；如果没有这行代码，工具不会真正运行。
    return json.dumps(result, ensure_ascii=False, sort_keys=True)  # 新增代码+ComputerUseMcpV2：返回模型可读 JSON 文本；如果没有这行代码，agent executor 拿不到字符串结果。
# 新增代码+ComputerUseMcpV2：函数段结束，execute_agent_side_tool 到此结束；如果没有这个边界说明，用户不容易看出 wrapper 执行范围。

