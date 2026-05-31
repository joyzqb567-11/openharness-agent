"""Streamable HTTP MCP client 入口。"""  # 新增代码+McpSplit: 这个模块集中导出 HTTP transport 和流状态对象；若没有这个文件，远程 MCP 问题会混在主入口里。

from .runtime import McpHttpClient, McpHttpStreamEvent, McpHttpStreamState, McpSessionExpired  # 新增代码+McpSplit: 从 MCP runtime 导出 HTTP client、SSE event/state 和 session 过期异常；若没有这行代码，计划要求的 http_client 模块路径不可用。

__all__ = ["McpHttpClient", "McpHttpStreamEvent", "McpHttpStreamState", "McpSessionExpired"]  # 新增代码+McpSplit: 明确本模块公开对象；若没有这行代码，HTTP MCP 层导出边界不清楚。
