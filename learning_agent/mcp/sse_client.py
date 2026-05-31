"""legacy SSE MCP client 边界入口。"""  # 新增代码+McpSplit: 这个模块集中导出旧 SSE transport 的边界 client；若没有这个文件，SSE 配置会和 stdio/http 混在一起。

from .runtime import McpSseClient  # 新增代码+McpSplit: 从 MCP runtime 导出 SSE client；若没有这行代码，计划要求的 sse_client 模块路径不可用。

__all__ = ["McpSseClient"]  # 新增代码+McpSplit: 明确本模块公开对象；若没有这行代码，legacy SSE 边界不清楚。
