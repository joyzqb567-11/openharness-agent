"""Computer Use MCP v2 门禁桥接。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode gates.ts；如果没有这行代码，门禁职责没有同构位置。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。


def gate_allows_tool(raw_name: str) -> bool:  # 新增代码+ComputerUseMcpV2：函数段开始，判断工具是否允许进入 v2；如果没有这段函数，桥接层没有门禁入口。
    from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import COMPUTER_USE_MCP_TOOL_NAMES  # 新增代码+ComputerUseMcpV2：延迟导入允许工具清单；如果没有这行代码，门禁无法匹配工具面。
    return str(raw_name or "").removeprefix("mcp__computer-use__") in COMPUTER_USE_MCP_TOOL_NAMES  # 新增代码+ComputerUseMcpV2：返回是否属于 v2 清单；如果没有这行代码，未知工具可能进入执行层。
# 新增代码+ComputerUseMcpV2：函数段结束，gate_allows_tool 到此结束；如果没有这个边界说明，用户不容易看出门禁范围。

