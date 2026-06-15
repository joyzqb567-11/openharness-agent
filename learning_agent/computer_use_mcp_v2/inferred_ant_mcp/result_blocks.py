"""Computer Use MCP v2 结果包装工具。"""  # 新增代码+ComputerUseMcpV2：说明本文件统一成功结果形状；如果没有这行代码，工具输出会不稳定。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，导入阶段类型求值可能产生噪音。

import json  # 新增代码+ComputerUseMcpV2：导入 JSON 用于生成 MCP 文本结果；如果没有这行代码，server 无法稳定返回 content 文本。
from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，结果 payload 边界不清楚。


def success_result(tool_name: str, payload: dict[str, Any] | None = None, *, legacy_adapter_used: bool = False) -> dict[str, Any]:  # 修改代码+ComputerUseMcpV2HostAdapter：函数段开始，生成统一成功结果并允许透出旧成熟 adapter 使用证据；如果没有这段函数，每个工具都会手写 ok/runtime 字段且审计无法看到真实执行来源。
    return {"ok": True, "runtime": "computer_use_mcp_v2", "legacy_adapter_used": bool(legacy_adapter_used), "tool_name": str(tool_name), "payload": dict(payload or {})}  # 修改代码+ComputerUseMcpV2HostAdapter：返回 v2 成功结果和 adapter 来源标记；如果没有这行代码，走了旧成熟链路也会被顶层误报为 False。
# 修改代码+ComputerUseMcpV2HostAdapter：函数段结束，success_result 到此结束；如果没有这个边界说明，用户不容易看出成功结果格式。


def mcp_content_from_result(result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，把 runtime 结果转成 MCP content；如果没有这段函数，stdio server 会重复写包装逻辑。
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, sort_keys=True)}], "isError": not bool(result.get("ok", False))}  # 新增代码+ComputerUseMcpV2：返回标准 MCP 工具结果；如果没有这行代码，MCP client 无法稳定读取工具输出。
# 新增代码+ComputerUseMcpV2：函数段结束，mcp_content_from_result 到此结束；如果没有这个边界说明，用户不容易看出 MCP 包装范围。
