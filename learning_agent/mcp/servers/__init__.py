"""OpenHarness 内置 MCP server 包。"""  # 新增代码+ComputerUseMCP：说明本目录保存可独立启动的 MCP server；如果没有这行代码，读者难以理解 servers 包用途。

__all__ = ["computer_use_server"]  # 新增代码+ComputerUseMCP：声明当前公开的 server 模块；如果没有这行代码，包导出边界不清楚。
