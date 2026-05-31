"""MCP 配置入口。"""  # 新增代码+McpSplit: 这个模块集中导出 mcp_servers.json 配置相关对象；若没有这个文件，配置问题仍只能去 runtime 或主入口里找。

from .runtime import McpServerConfig, format_mcp_startup_status, load_mcp_server_configs, mcp_server_config_path  # 新增代码+McpSplit: 从 MCP runtime 导出配置数据类和解析函数；若没有这行代码，计划要求的 config 模块路径不可用。

__all__ = ["McpServerConfig", "format_mcp_startup_status", "load_mcp_server_configs", "mcp_server_config_path"]  # 新增代码+McpSplit: 明确本模块公开对象；若没有这行代码，架构索引不容易判断配置层 API。
