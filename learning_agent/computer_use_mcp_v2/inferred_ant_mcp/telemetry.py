"""Computer Use MCP v2 trace 和验收事件工具。"""  # 新增代码+ComputerUseMcpV2：说明本文件集中处理证据链；如果没有这行代码，trace 写入会散落。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型引用可能提前求值。

from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，事件 payload 类型不清楚。

from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入 v2 上下文；如果没有这行代码，trace helper 拿不到回调字段。


def record_trace(context: ComputerUseMcpV2Context, phase: str, payload: dict[str, Any]) -> None:  # 新增代码+ComputerUseMcpV2：函数段开始，写入 v2 runtime trace；如果没有这段函数，每个工具都要重复判断回调是否存在。
    event = {"runtime": "computer_use_mcp_v2", "phase": str(phase), "payload": dict(payload)}  # 新增代码+ComputerUseMcpV2：构造稳定 trace 事件；如果没有这行代码，新旧执行路径无法通过事件区分。
    if callable(context.record_runtime_trace):  # 新增代码+ComputerUseMcpV2：检查调用方是否提供 trace 回调；如果没有这行代码，None 回调会导致异常。
        context.record_runtime_trace(event)  # 新增代码+ComputerUseMcpV2：把事件交回 agent 或测试；如果没有这行代码，trace_events 不会记录 v2 执行证据。
# 新增代码+ComputerUseMcpV2：函数段结束，record_trace 到此结束；如果没有这个边界说明，用户不容易看出 trace 写入范围。


def emit_acceptance(context: ComputerUseMcpV2Context, event_name: str, payload: dict[str, Any]) -> None:  # 新增代码+ComputerUseMcpV2：函数段开始，写入真实终端验收事件；如果没有这段函数，可见验收链缺少统一出口。
    if callable(context.emit_acceptance_event):  # 新增代码+ComputerUseMcpV2：检查是否存在验收事件回调；如果没有这行代码，独立 stdio 场景会因缺回调崩溃。
        context.emit_acceptance_event(str(event_name), dict(payload))  # 新增代码+ComputerUseMcpV2：发送验收事件；如果没有这行代码，用户无法在终端验收日志中区分 v2 动作。
# 新增代码+ComputerUseMcpV2：函数段结束，emit_acceptance 到此结束；如果没有这个边界说明，用户不容易看出验收事件范围。

