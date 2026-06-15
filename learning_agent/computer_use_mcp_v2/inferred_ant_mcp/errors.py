"""Computer Use MCP v2 错误结果工具。"""  # 新增代码+ComputerUseMcpV2：说明本文件集中生成失败结果；如果没有这行代码，错误格式会散落在动作、观察和批量模块。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，部分运行方式可能在导入阶段提前求值类型。

from typing import Any  # 新增代码+ComputerUseMcpV2：引入通用 JSON 类型；如果没有这行代码，错误结果函数的输入输出边界不清楚。


def error_result(tool_name: str, reason: str, *, error_class: str = "computer_use_mcp_v2_error") -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，生成统一失败结果；如果没有这段函数，各模块会手写不同失败形状。
    return {"ok": False, "runtime": "computer_use_mcp_v2", "legacy_adapter_used": False, "tool_name": str(tool_name), "reason": str(reason), "error_class": str(error_class)}  # 新增代码+ComputerUseMcpV2：返回稳定失败字段；如果没有这行代码，模型和测试无法统一判断失败原因。
# 新增代码+ComputerUseMcpV2：函数段结束，error_result 到此结束；如果没有这个边界说明，用户不容易看出错误生成范围。

