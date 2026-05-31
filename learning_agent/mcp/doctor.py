"""MCP Doctor 诊断入口。"""  # 新增代码+McpSplit: 这个模块集中导出 MCP 诊断命令；若没有这个文件，CLI doctor 入口仍会绑在主文件实现里。

from .runtime import run_mcp_doctor  # 新增代码+McpSplit: 从 MCP runtime 导出 doctor 函数；若没有这行代码，计划要求的诊断入口不可用。

__all__ = ["run_mcp_doctor"]  # 新增代码+McpSplit: 明确本模块公开对象；若没有这行代码，诊断层导出边界不清楚。
