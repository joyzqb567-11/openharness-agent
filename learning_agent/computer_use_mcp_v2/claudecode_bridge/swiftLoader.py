"""Computer Use MCP v2 Windows native loader，保留 ClaudeCode swiftLoader 文件名。"""  # 新增代码+ComputerUseMcpV2：说明 Windows 版本保留文件名但不使用 Swift；如果没有这行代码，后续对照 ClaudeCode 时会误以为缺 Swift。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。


def native_loader_name() -> str:  # 新增代码+ComputerUseMcpV2：函数段开始，返回 Windows native loader 名；如果没有这段函数，桥接层无法解释 swiftLoader 在 Windows 的含义。
    return "windows_native_loader"  # 新增代码+ComputerUseMcpV2：返回 Windows native loader 摘要；如果没有这行代码，状态诊断缺少说明。
# 新增代码+ComputerUseMcpV2：函数段结束，native_loader_name 到此结束；如果没有这个边界说明，用户不容易看出 loader 范围。

