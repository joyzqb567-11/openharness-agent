"""当前工具池和策略决策辅助函数。"""  # 新增代码+ToolsPoolSplit: 把工具可见性计算从主循环拆出；若没有这个文件，工具池 bug 仍要翻 LearningAgent 大类。

from __future__ import annotations  # 新增代码+ToolsPoolSplit: 延迟解析类型注解；若没有这行代码，工具策略类型导入顺序会更脆弱。

from typing import Any, Callable  # 新增代码+ToolsPoolSplit: 工具池 helper 需要通用策略对象和回调类型；若没有这行代码，类型边界不清楚。

try:  # 新增代码+ToolsPoolSplit: 包运行模式下导入工具元数据和策略决策类型；若没有这行代码，pool 无法复用正式类型。
    from learning_agent.tool_policy import ToolPolicyDecision  # 新增代码+ToolsPoolSplit: 导入策略决策结果类型；若没有这行代码，真实 Chrome 阻断无法返回统一决策对象。
    from learning_agent.tools.types import AgentTool  # 新增代码+ToolsPoolSplit: 导入工具元数据类型；若没有这行代码，pool 只能处理裸字典。
except ModuleNotFoundError as error:  # 新增代码+ToolsPoolSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tool_policy", "learning_agent.tools", "learning_agent.tools.types"}:  # 新增代码+ToolsPoolSplit: 只允许目标包路径缺失时 fallback；若没有这行代码，内部真实 bug 会被误吞。
        raise  # 新增代码+ToolsPoolSplit: 重新抛出真实导入错误；若没有这行代码，排查 pool 问题会很困难。
    from tool_policy import ToolPolicyDecision  # 新增代码+ToolsPoolSplit: 脚本模式下导入策略决策结果类型；若没有这行代码，直接执行时策略阻断无法统一。
    from tools.types import AgentTool  # 新增代码+ToolsPoolSplit: 脚本模式下导入 AgentTool；若没有这行代码，直接执行时工具池 helper 无法工作。


def decide_tool_policy(tool: AgentTool, *, tool_policy: Any, tool_policy_context: Any, allowed_tool_names: set[str] | None, loaded_tool_names: set[str], real_chrome_blocked: bool) -> ToolPolicyDecision:  # 新增代码+ToolsPoolSplit: 统一计算工具策略决策；若没有这行代码，主类会继续手写 loaded 和 workflow 逻辑。
    if real_chrome_blocked:  # 新增代码+ToolsPoolSplit: 先处理真实 Chrome workflow 对独立浏览器工具的硬拦截；若没有这行代码，用户要求真实浏览器时仍可能误走独立 Chromium。
        return ToolPolicyDecision(state="needs_workflow", visible=False, selectable=False, executable=False, reason="real chrome requested; run browser_profile_status and browser_connect_real_chrome first")  # 新增代码+ToolsPoolSplit: 返回统一策略对象表达前置流程缺失；若没有这行代码，搜索、展示和执行层会出现不一致阻断。
    allowed_tool_loaded = allowed_tool_names is not None and tool.name in allowed_tool_names  # 新增代码+ToolsPoolSplit: 显式 allowed_tools 中的延迟工具视为已授权加载；若没有这行代码，子 agent 白名单工具会被首轮隐藏策略挡住。
    loaded = tool.name in loaded_tool_names or tool.always_load or allowed_tool_loaded  # 新增代码+ToolsPoolSplit: 按 select、always_load 或子 agent 白名单计算 loaded；若没有这行代码，deferred 工具无法正确区分未加载和已授权加载。
    return tool_policy.decide(tool, tool_policy_context, loaded=loaded)  # 新增代码+ToolsPoolSplit: 调用统一策略入口；若没有这行代码，deny/skill/workflow/deferred 状态不会统一生效。


def current_tool_pool(catalog: list[AgentTool], decision_for_tool: Callable[[AgentTool], ToolPolicyDecision]) -> list[AgentTool]:  # 新增代码+ToolsPoolSplit: 从完整目录计算当前可见工具池；若没有这行代码，LearningAgent 仍要在主类里过滤工具。
    current_pool: list[AgentTool] = []  # 新增代码+ToolsPoolSplit: 准备累积当前可见工具；若没有这行代码，循环没有地方保存过滤后的工具。
    for tool in catalog:  # 新增代码+ToolsPoolSplit: 遍历完整 catalog 决定哪些工具进入当前池；若没有这行代码，pool 无法从目录派生。
        decision = decision_for_tool(tool)  # 新增代码+ToolsPoolSplit: 为当前工具读取策略决策；若没有这行代码，工具池无法尊重 deny/skill/workflow 状态。
        if not decision.visible:  # 新增代码+ToolsPoolSplit: 只让策略判定 visible 的工具进入模型工具池；若没有这行代码，blocked/needs_skill/needs_workflow 工具可能泄露给模型。
            continue  # 新增代码+ToolsPoolSplit: 不把不可见工具加入当前 pool；若没有这行代码，隐藏工具会继续暴露。
        current_pool.append(tool)  # 新增代码+ToolsPoolSplit: 保存当前可见工具；若没有这行代码，模型会看不到应该可用的工具。
    return current_pool  # 新增代码+ToolsPoolSplit: 返回当前可见工具池；若没有这行代码，schema 构建没有输入来源。


def available_tool_schemas(tool_pool: list[AgentTool]) -> list[dict[str, Any]]:  # 新增代码+ToolsPoolSplit: 把当前工具池转换为模型 schema；若没有这行代码，主类仍要自己做 schema 映射。
    return [tool.to_model_schema() for tool in tool_pool]  # 新增代码+ToolsPoolSplit: 每个工具生成独立 OpenAI-compatible schema 副本；若没有这行代码，模型无法收到当前工具定义。


def filter_allowed_tool_schemas(tool_schemas: list[dict[str, Any]], allowed_tool_names: set[str] | None) -> list[dict[str, Any]]:  # 新增代码+ToolsPoolSplit: 根据子 agent 白名单过滤工具 schema；若没有这行代码，allowed_tools 规则会散在主类里。
    if allowed_tool_names is None:  # 新增代码+ToolsPoolSplit: None 表示当前 agent 不限制工具；若没有这行代码，主 agent 也会被误过滤。
        return tool_schemas  # 新增代码+ToolsPoolSplit: 主 agent 直接返回完整工具列表；若没有这行代码，无白名单场景会继续走多余过滤逻辑。
    filtered_schemas: list[dict[str, Any]] = []  # 新增代码+ToolsPoolSplit: 准备保存白名单命中的工具 schema；若没有这行代码，无处累积过滤结果。
    for schema in tool_schemas:  # 新增代码+ToolsPoolSplit: 遍历当前可见的每个工具 schema；若没有这行代码，无法逐个判断工具名。
        function_schema = schema.get("function", {}) if isinstance(schema, dict) else {}  # 新增代码+ToolsPoolSplit: 读取 OpenAI-compatible function 字段；若没有这行代码，畸形 schema 可能导致过滤时报错。
        tool_name = function_schema.get("name") if isinstance(function_schema, dict) else None  # 新增代码+ToolsPoolSplit: 读取工具名；若没有这行代码，无法和 allowed_tool_names 做匹配。
        if isinstance(tool_name, str) and tool_name in allowed_tool_names:  # 新增代码+ToolsPoolSplit: 只有白名单包含的工具才保留；若没有这行代码，子 agent 会看到未授权工具。
            filtered_schemas.append(schema)  # 新增代码+ToolsPoolSplit: 保存允许暴露给子 agent 的工具；若没有这行代码，白名单工具也会丢失。
    return filtered_schemas  # 新增代码+ToolsPoolSplit: 返回过滤后的工具 schema；若没有这行代码，子 agent 拿不到最终工具列表。


def tool_schema_names(tool_schemas: list[dict[str, Any]]) -> list[str]:  # 新增代码+ToolsPoolSplit: 从模型 schema 中提取工具名；若没有这行代码，日志和测试仍要在主类里解析 schema。
    names: list[str] = []  # 新增代码+ToolsPoolSplit: 准备保存工具名称；若没有这行代码，后续无法累积并返回工具名列表。
    for schema in tool_schemas:  # 新增代码+ToolsPoolSplit: 遍历指定工具 schema；若没有这行代码，无法逐个读取工具名。
        function = schema.get("function", {})  # 新增代码+ToolsPoolSplit: 取出 function 字段；若没有这行代码，无法定位 OpenAI-compatible schema 中真正的工具名。
        if isinstance(function, dict) and isinstance(function.get("name"), str):  # 新增代码+ToolsPoolSplit: 确认 function.name 存在且是字符串；若没有这行代码，畸形 schema 可能导致日志构造时报错。
            names.append(function["name"])  # 新增代码+ToolsPoolSplit: 把工具名加入结果列表；若没有这行代码，返回列表会缺少模型可见的工具名。
    return names  # 新增代码+ToolsPoolSplit: 返回工具名列表；若没有这行代码，调用方拿不到可用于日志和测试断言的结果。
