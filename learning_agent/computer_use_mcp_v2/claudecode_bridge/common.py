"""Computer Use MCP v2 ClaudeCode 桥接通用常量。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode common.ts；如果没有这行代码，对照源码时缺少入口。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，导入阶段类型求值可能出错。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import COMPUTER_USE_MCP_READY_MARKER, COMPUTER_USE_MCP_SERVER_NAME  # 新增代码+ComputerUseMcpV2：重导出 v2 server 常量；如果没有这行代码，桥接层和推断包常量可能分裂。

