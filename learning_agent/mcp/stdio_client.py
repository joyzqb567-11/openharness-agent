"""stdio MCP client 入口。"""  # 新增代码+McpSplit: 这个模块集中导出本地 stdio MCP client；若没有这个文件，本地 MCP server 问题难快速定位。

from .runtime import McpStdioClient  # 新增代码+McpSplit: 从 MCP runtime 导出 stdio client；若没有这行代码，计划要求的 stdio_client 模块路径不可用。

__all__ = ["McpStdioClient"]  # 新增代码+McpSplit: 明确本模块公开对象；若没有这行代码，stdio client 的公共边界不清楚。
