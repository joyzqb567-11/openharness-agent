"""MCP 到 AgentTool 的临时适配入口。"""  # 新增代码+McpSplit: 这个模块承接阶段 4 到阶段 5 之间的工具层临时依赖；若没有这个文件，MCP registry 对工具目录的依赖会没有索引。

from .runtime import agent_tool_from_schema, builtin_tool_capability_pack  # 新增代码+McpSplit: 导出 runtime 中的临时代理函数；若没有这行代码，阶段 5 前 MCP 工具无法继续包装成 AgentTool。

__all__ = ["agent_tool_from_schema", "builtin_tool_capability_pack"]  # 新增代码+McpSplit: 明确本模块公开对象；若没有这行代码，临时适配边界不清楚。
