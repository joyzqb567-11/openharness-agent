"""Computer Use MCP v2 工具结果渲染桥接。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode toolRendering.tsx；如果没有这行代码，结果渲染职责没有同构位置。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

import json  # 新增代码+ComputerUseMcpV2：导入 JSON 用于渲染简短文本；如果没有这行代码，结果无法稳定序列化。
from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用类型；如果没有这行代码，渲染函数参数边界不清楚。


def render_tool_result(result: dict[str, Any]) -> str:  # 新增代码+ComputerUseMcpV2：函数段开始，把工具结果渲染为文本；如果没有这段函数，UI 和日志会各自序列化。
    return json.dumps(result, ensure_ascii=False, sort_keys=True)  # 新增代码+ComputerUseMcpV2：返回稳定 JSON 文本；如果没有这行代码，工具结果显示顺序会漂移。
# 新增代码+ComputerUseMcpV2：函数段结束，render_tool_result 到此结束；如果没有这个边界说明，用户不容易看出渲染范围。

