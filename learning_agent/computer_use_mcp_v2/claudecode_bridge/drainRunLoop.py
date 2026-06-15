"""Computer Use MCP v2 事件循环等待桥接。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode drainRunLoop.ts；如果没有这行代码，等待职责没有固定位置。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

import time  # 新增代码+ComputerUseMcpV2：导入时间模块用于短暂等待；如果没有这行代码，drain_run_loop 无法模拟 UI 稳定等待。


def drain_run_loop(seconds: float = 0.05) -> None:  # 新增代码+ComputerUseMcpV2：函数段开始，短暂等待 UI 事件稳定；如果没有这段函数，动作后观察可能过早发生。
    time.sleep(max(0.0, min(float(seconds), 1.0)))  # 新增代码+ComputerUseMcpV2：限制并执行等待；如果没有这行代码，等待可能过长或无效。
# 新增代码+ComputerUseMcpV2：函数段结束，drain_run_loop 到此结束；如果没有这个边界说明，用户不容易看出等待范围。

