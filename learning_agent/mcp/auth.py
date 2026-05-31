"""MCP 鉴权边界入口。"""  # 新增代码+McpSplit: 这个模块集中导出远程 MCP 鉴权挑战对象；若没有这个文件，401/auth 恢复问题难定位。

from .runtime import McpAuthChallenge, McpAuthenticationRequired  # 新增代码+McpSplit: 从 MCP runtime 导出鉴权挑战和专用异常；若没有这行代码，计划要求的 auth 模块路径不可用。

__all__ = ["McpAuthChallenge", "McpAuthenticationRequired"]  # 新增代码+McpSplit: 明确本模块公开对象；若没有这行代码，后续文档和测试难判断导出边界。
