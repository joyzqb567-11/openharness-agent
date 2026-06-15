"""Computer Use MCP v2 独占锁桥接。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode computerUseLock.ts；如果没有这行代码，锁职责没有固定位置。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

COMPUTER_USE_LOCK_NAME = "openharness_computer_use_mcp_v2"  # 新增代码+ComputerUseMcpV2：定义 v2 锁名；如果没有这行代码，后续加真实锁时缺少稳定标识。

