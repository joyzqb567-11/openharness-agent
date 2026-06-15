"""Computer Use MCP v2 输入后端加载桥接。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode inputLoader.ts；如果没有这行代码，输入后端加载职责没有固定位置。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。


def input_backend_name() -> str:  # 新增代码+ComputerUseMcpV2：函数段开始，返回当前输入后端名称；如果没有这段函数，状态页无法说明 v2 使用哪类输入层。
    return "windows_native_or_bound_host"  # 新增代码+ComputerUseMcpV2：返回 Windows/native host 后端摘要；如果没有这行代码，排查时不知道输入从哪里来。
# 新增代码+ComputerUseMcpV2：函数段结束，input_backend_name 到此结束；如果没有这个边界说明，用户不容易看出后端名称范围。

