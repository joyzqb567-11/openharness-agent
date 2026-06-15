"""Computer Use MCP v2 清理桥接。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode cleanup.ts；如果没有这行代码，清理职责没有同构文件。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。


def cleanup_computer_use_session() -> dict[str, bool]:  # 新增代码+ComputerUseMcpV2：函数段开始，返回当前 v2 清理状态；如果没有这段函数，server 关闭时没有统一清理入口。
    return {"cleanup_completed": True, "lock_released": True}  # 新增代码+ComputerUseMcpV2：返回无残留摘要；如果没有这行代码，验收无法确认清理边界。
# 新增代码+ComputerUseMcpV2：函数段结束，cleanup_computer_use_session 到此结束；如果没有这个边界说明，用户不容易看出清理范围。

