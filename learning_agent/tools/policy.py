"""工具策略模块兼容入口。"""  # 新增代码+ToolsPoolSplit: 把已有 ToolPolicy 暴露到 tools 层命名空间；若没有这个文件，阶段 5 的工具层结构会缺少 policy 入口。

try:  # 新增代码+ToolsPoolSplit: 包运行模式下复用既有策略实现；若没有这行代码，外部无法从 learning_agent.tools.policy 导入策略类。
    from learning_agent.tool_policy import ToolPolicy, ToolPolicyContext, ToolPolicyDecision, ToolPolicyRule  # 新增代码+ToolsPoolSplit: 重导出策略核心对象；若没有这行代码，策略层会在新旧路径之间断裂。
except ModuleNotFoundError as error:  # 新增代码+ToolsPoolSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tool_policy"}:  # 新增代码+ToolsPoolSplit: 只允许目标包路径缺失时 fallback；若没有这行代码，策略模块内部真实 bug 会被误吞。
        raise  # 新增代码+ToolsPoolSplit: 重新抛出真实导入错误；若没有这行代码，排查 policy 问题会很困难。
    from tool_policy import ToolPolicy, ToolPolicyContext, ToolPolicyDecision, ToolPolicyRule  # 新增代码+ToolsPoolSplit: 脚本模式下重导出策略核心对象；若没有这行代码，直接执行时新 tools.policy 入口不可用。

__all__ = ["ToolPolicy", "ToolPolicyContext", "ToolPolicyDecision", "ToolPolicyRule"]  # 新增代码+ToolsPoolSplit: 明确 policy 公开 API；若没有这行代码，后续重构容易暴露临时名字。
