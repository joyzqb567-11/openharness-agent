"""工具层包入口。"""  # 修改代码+ToolsSplit: 说明 tools 包已经开始承载工具类型和目录；若没有这行代码，用户看包入口时会误以为仍只是空骨架。

try:  # 修改代码+ToolsSplit: 包运行模式下从正式包路径重导出工具 API；若没有这行代码，测试和外部包导入无法走稳定路径。
    from learning_agent.tools.catalog import agent_tool_from_schema, build_builtin_tool_catalog, builtin_tool_capability_pack  # 修改代码+ToolsSplit: 重导出工具 schema 包装和 catalog 构建函数；若没有这行代码，外部调用方需要知道内部文件名。
    from learning_agent.tools.types import AgentTool  # 修改代码+ToolsSplit: 重导出工具元数据类型；若没有这行代码，外部调用方无法从 tools 包入口获取核心类型。
except ModuleNotFoundError as error:  # 修改代码+ToolsSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.catalog", "learning_agent.tools.types"}:  # 修改代码+ToolsSplit: 只允许目标包路径缺失时 fallback；若没有这行代码，tools 内部真实 bug 会被误吞。
        raise  # 修改代码+ToolsSplit: 重新抛出真实导入错误；若没有这行代码，排查 tools 包问题会很困难。
    from tools.catalog import agent_tool_from_schema, build_builtin_tool_catalog, builtin_tool_capability_pack  # 修改代码+ToolsSplit: 脚本模式下重导出 catalog 函数；若没有这行代码，直接执行 learning_agent.py 时 tools 包入口会失败。
    from tools.types import AgentTool  # 修改代码+ToolsSplit: 脚本模式下重导出 AgentTool 类型；若没有这行代码，直接执行时外部模块找不到工具类型。

__all__ = ["AgentTool", "agent_tool_from_schema", "build_builtin_tool_catalog", "builtin_tool_capability_pack"]  # 新增代码+ToolsSplit: 明确 tools 包公开 API；若没有这行代码，后续重构时容易无意暴露临时 helper。
