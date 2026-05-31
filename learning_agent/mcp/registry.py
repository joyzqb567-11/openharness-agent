"""MCP 工具注册表入口。"""  # 新增代码+McpSplit: 这个模块集中导出 tools/list 到模型工具 schema 的注册表；若没有这个文件，MCP 工具路由问题仍难定位。

from .runtime import McpToolRegistry  # 新增代码+McpSplit: 从 MCP runtime 导出工具注册表；若没有这行代码，计划要求的 registry 模块路径不可用。

__all__ = ["McpToolRegistry"]  # 新增代码+McpSplit: 明确本模块公开对象；若没有这行代码，registry 公共边界不清楚。
