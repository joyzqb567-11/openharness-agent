# 新增代码+模块化重构: mcp 包用于承载 MCP 配置、transport client、registry、auth 和 doctor；如果没有这个包，MCP 故障仍要翻 learning_agent.py。
from .auth import McpAuthChallenge, McpAuthenticationRequired  # 修改代码+McpSplit: 导出 MCP 鉴权挑战对象；若没有这行代码，调用方无法从 mcp 包顶层定位 auth 边界。
from .config import McpServerConfig, format_mcp_startup_status, load_mcp_server_configs, mcp_server_config_path  # 修改代码+McpSplit: 导出 MCP 配置解析入口；若没有这行代码，调用方无法从 mcp 包顶层加载配置。
from .doctor import run_mcp_doctor  # 修改代码+McpSplit: 导出 MCP Doctor 入口；若没有这行代码，诊断命令无法复用新模块。
from .http_client import McpHttpClient, McpHttpStreamEvent, McpHttpStreamState, McpSessionExpired  # 修改代码+McpSplit: 导出 HTTP transport 和流状态对象；若没有这行代码，远程 MCP client 边界不清楚。
from .registry import McpToolRegistry  # 修改代码+McpSplit: 导出 MCP 工具注册表；若没有这行代码，外部工具发现入口不清楚。
from .sse_client import McpSseClient  # 修改代码+McpSplit: 导出 legacy SSE client；若没有这行代码，SSE transport 边界不清楚。
from .stdio_client import McpStdioClient  # 修改代码+McpSplit: 导出 stdio client；若没有这行代码，本地 MCP server 入口不清楚。

__all__ = [  # 修改代码+McpSplit: 明确 mcp 包顶层公开对象；若没有这行代码，架构索引无法快速列出 MCP 层 API。
    "McpAuthChallenge",  # 修改代码+McpSplit: 公开鉴权挑战数据类；若没有这行代码，顶层导出不完整。
    "McpAuthenticationRequired",  # 修改代码+McpSplit: 公开鉴权专用异常；若没有这行代码，顶层导出不完整。
    "McpHttpClient",  # 修改代码+McpSplit: 公开 HTTP MCP client；若没有这行代码，顶层导出不完整。
    "McpHttpStreamEvent",  # 修改代码+McpSplit: 公开 HTTP/SSE 事件数据类；若没有这行代码，顶层导出不完整。
    "McpHttpStreamState",  # 修改代码+McpSplit: 公开 HTTP/SSE 流状态数据类；若没有这行代码，顶层导出不完整。
    "McpServerConfig",  # 修改代码+McpSplit: 公开 MCP server 配置类；若没有这行代码，顶层导出不完整。
    "McpSessionExpired",  # 修改代码+McpSplit: 公开 session 过期异常；若没有这行代码，顶层导出不完整。
    "McpSseClient",  # 修改代码+McpSplit: 公开 legacy SSE client；若没有这行代码，顶层导出不完整。
    "McpStdioClient",  # 修改代码+McpSplit: 公开 stdio MCP client；若没有这行代码，顶层导出不完整。
    "McpToolRegistry",  # 修改代码+McpSplit: 公开 MCP registry；若没有这行代码，顶层导出不完整。
    "format_mcp_startup_status",  # 修改代码+McpSplit: 公开启动状态格式化函数；若没有这行代码，顶层导出不完整。
    "load_mcp_server_configs",  # 修改代码+McpSplit: 公开配置加载函数；若没有这行代码，顶层导出不完整。
    "mcp_server_config_path",  # 修改代码+McpSplit: 公开配置路径函数；若没有这行代码，顶层导出不完整。
    "run_mcp_doctor",  # 修改代码+McpSplit: 公开 doctor 函数；若没有这行代码，顶层导出不完整。
]  # 修改代码+McpSplit: 结束公开对象列表；若没有这行代码，Python 列表语法不完整。
