"""Computer Use MCP v2 坐标处理。"""  # 新增代码+ComputerUseMcpV2：说明本文件集中处理坐标清洗；如果没有这行代码，坐标转换会重复出现。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用类型；如果没有这行代码，坐标输入边界不清楚。


def int_coordinate(value: Any, default: int = 0) -> int:  # 新增代码+ComputerUseMcpV2：函数段开始，把模型坐标安全转成整数；如果没有这段函数，坏坐标可能导致动作崩溃。
    try:  # 新增代码+ComputerUseMcpV2：捕获无法转换的值；如果没有这行代码，空字符串和 None 会中断工具。
        return int(value)  # 新增代码+ComputerUseMcpV2：返回整数坐标；如果没有这行代码，动作模块拿不到可用坐标。
    except (TypeError, ValueError):  # 新增代码+ComputerUseMcpV2：处理类型和值错误；如果没有这行代码，容错路径不可用。
        return int(default)  # 新增代码+ComputerUseMcpV2：返回默认坐标；如果没有这行代码，失败时没有稳定兜底。
# 新增代码+ComputerUseMcpV2：函数段结束，int_coordinate 到此结束；如果没有这个边界说明，用户不容易看出坐标清洗范围。

