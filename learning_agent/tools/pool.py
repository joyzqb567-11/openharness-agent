"""当前工具池和策略决策辅助函数。"""  # 新增代码+ToolsPoolSplit: 把工具可见性计算从主循环拆出；若没有这个文件，工具池 bug 仍要翻 LearningAgent 大类。

from __future__ import annotations  # 新增代码+ToolsPoolSplit: 延迟解析类型注解；若没有这行代码，工具策略类型导入顺序会更脆弱。

from typing import Any, Callable  # 新增代码+ToolsPoolSplit: 工具池 helper 需要通用策略对象和回调类型；若没有这行代码，类型边界不清楚。

try:  # 新增代码+ToolsPoolSplit: 包运行模式下导入工具元数据和策略决策类型；若没有这行代码，pool 无法复用正式类型。
    from learning_agent.tool_policy import ToolPolicyDecision  # 新增代码+ToolsPoolSplit: 导入策略决策结果类型；若没有这行代码，真实 Chrome 阻断无法返回统一决策对象。
    from learning_agent.tools.types import AgentTool, toolToAPISchema  # 修改代码+ToolToAPISchema命名入口：同时导入 ClaudeCode 同名 schema 转换入口；如果没有这行代码，当前工具池转换仍只能直接调用内部方法，用户不容易对照 ClaudeCode。
except ModuleNotFoundError as error:  # 新增代码+ToolsPoolSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tool_policy", "learning_agent.tools", "learning_agent.tools.types"}:  # 新增代码+ToolsPoolSplit: 只允许目标包路径缺失时 fallback；若没有这行代码，内部真实 bug 会被误吞。
        raise  # 新增代码+ToolsPoolSplit: 重新抛出真实导入错误；若没有这行代码，排查 pool 问题会很困难。
    from tool_policy import ToolPolicyDecision  # 新增代码+ToolsPoolSplit: 脚本模式下导入策略决策结果类型；若没有这行代码，直接执行时策略阻断无法统一。
    from tools.types import AgentTool, toolToAPISchema  # 修改代码+ToolToAPISchema命名入口：脚本模式下也导入同名 schema 转换入口；如果没有这行代码，start_oauth_agent.bat 路径下会找不到新命名入口。


def decide_tool_policy(tool: AgentTool, *, tool_policy: Any, tool_policy_context: Any, allowed_tool_names: set[str] | None, loaded_tool_names: set[str], real_chrome_blocked: bool) -> ToolPolicyDecision:  # 新增代码+ToolsPoolSplit: 统一计算工具策略决策；若没有这行代码，主类会继续手写 loaded 和 workflow 逻辑。
    if real_chrome_blocked:  # 新增代码+ToolsPoolSplit: 先处理真实 Chrome workflow 对独立浏览器工具的硬拦截；若没有这行代码，用户要求真实浏览器时仍可能误走独立 Chromium。
        return ToolPolicyDecision(state="needs_workflow", visible=False, selectable=False, executable=False, reason="real chrome requested; run browser_profile_status and browser_connect_real_chrome first")  # 新增代码+ToolsPoolSplit: 返回统一策略对象表达前置流程缺失；若没有这行代码，搜索、展示和执行层会出现不一致阻断。
    allowed_tool_loaded = allowed_tool_names is not None and tool.name in allowed_tool_names  # 新增代码+ToolsPoolSplit: 显式 allowed_tools 中的延迟工具视为已授权加载；若没有这行代码，子 agent 白名单工具会被首轮隐藏策略挡住。
    loaded = tool.name in loaded_tool_names or tool.always_load or allowed_tool_loaded  # 新增代码+ToolsPoolSplit: 按 select、always_load 或子 agent 白名单计算 loaded；若没有这行代码，deferred 工具无法正确区分未加载和已授权加载。
    return tool_policy.decide(tool, tool_policy_context, loaded=loaded)  # 新增代码+ToolsPoolSplit: 调用统一策略入口；若没有这行代码，deny/skill/workflow/deferred 状态不会统一生效。


def filteredTools(catalog: list[AgentTool], decision_for_tool: Callable[[AgentTool], ToolPolicyDecision]) -> list[AgentTool]:  # 修改代码+FilteredTools删除旧名：函数段开始，提供和 ClaudeCode 同名的当前可用工具过滤入口；如果没有这段函数，代码小白就没有一个唯一清楚的工具过滤入口。
    filtered_tools: list[AgentTool] = []  # 新增代码+FilteredTools命名入口：准备累积当前真正可见的工具；如果没有这行代码，循环没有地方保存过滤后的工具。
    for tool in catalog:  # 新增代码+FilteredTools命名入口：遍历完整 catalog 决定哪些工具进入当前池；如果没有这行代码，过滤入口无法从完整目录派生当前工具集合。
        decision = decision_for_tool(tool)  # 新增代码+FilteredTools命名入口：为当前工具读取策略决策；如果没有这行代码，工具池无法尊重 deny、skill、workflow 和 deferred 状态。
        if not decision.visible:  # 新增代码+FilteredTools命名入口：只让策略判定 visible 的工具进入模型工具池；如果没有这行代码，被阻断或延迟的工具可能泄露给模型。
            continue  # 新增代码+FilteredTools命名入口：跳过不可见工具；如果没有这行代码，隐藏工具会继续被追加到模型可见列表。
        filtered_tools.append(tool)  # 新增代码+FilteredTools命名入口：保存当前可见工具；如果没有这行代码，模型会看不到应该直接可用的工具。
    return filtered_tools  # 新增代码+FilteredTools命名入口：返回当前过滤后的可见工具池；如果没有这行代码，schema 构建没有输入来源。
# 修改代码+FilteredTools删除旧名：函数段结束，filteredTools 到此结束；如果没有这个边界说明，用户不容易看出它就是对齐 ClaudeCode 的唯一过滤入口。


def available_tool_schemas(tool_pool: list[AgentTool]) -> list[dict[str, Any]]:  # 新增代码+ToolsPoolSplit: 把当前工具池转换为模型 schema；若没有这行代码，主类仍要自己做 schema 映射。
    return [toolToAPISchema(tool) for tool in tool_pool]  # 修改代码+ToolToAPISchema命名入口：当前工具池统一通过 ClaudeCode 同名入口生成 API schema；如果没有这行代码，新入口不会出现在真实发送 OpenAI API 的链路里。


def available_responses_tool_schemas(tool_pool: list[AgentTool]) -> list[dict[str, Any]]:  # 新增代码+OAuthNativeToolsRuntimeEntry: 函数段开始，把当前工具池转换为 Responses native 顶层 tools；如果没有这段函数，OAuth native 模式无法复用 filteredTools 后的工具池。
    try:  # 新增代码+OAuthNativeToolsRuntimeEntry: 包运行模式下导入 Responses native schema builder；如果没有这一行，工具池无法生成 namespace/tool_search 形状。
        from learning_agent.models.responses_native import build_hosted_tool_search_tools_by_namespace  # 新增代码+OAuthNativeToolsRuntimeEntry: 导入多 namespace 构造器；如果没有这一行，Computer Use 无法独立分组。
        from learning_agent.models.responses_native import default_responses_namespace_descriptions  # 新增代码+OAuthNativeToolsRuntimeEntry: 导入默认 namespace 说明；如果没有这一行，模型看到的分组说明会缺失。
        from learning_agent.models.responses_native import default_responses_namespace_for_tool_name  # 新增代码+OAuthNativeToolsRuntimeEntry: 导入默认工具名分组规则；如果没有这一行，Computer Use 工具无法稳定进入 computer_use namespace。
    except ModuleNotFoundError as error:  # 新增代码+OAuthNativeToolsRuntimeEntry: 兼容 start_oauth_agent.bat 脚本模式下包名前缀不同；如果没有这一行，真实终端入口可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.models", "learning_agent.models.responses_native"}:  # 新增代码+OAuthNativeToolsRuntimeEntry: 只允许目标包路径缺失进入 fallback；如果没有这一行，responses_native 内部 bug 会被误吞。
            raise  # 新增代码+OAuthNativeToolsRuntimeEntry: 重新抛出真实导入错误；如果没有这一行，排查 native schema 失败会很困难。
        from models.responses_native import build_hosted_tool_search_tools_by_namespace  # 新增代码+OAuthNativeToolsRuntimeEntry: 脚本模式导入多 namespace 构造器；如果没有这一行，bat 入口无法生成 native tools。
        from models.responses_native import default_responses_namespace_descriptions  # 新增代码+OAuthNativeToolsRuntimeEntry: 脚本模式导入默认 namespace 说明；如果没有这一行，bat 入口 namespace 说明会缺失。
        from models.responses_native import default_responses_namespace_for_tool_name  # 新增代码+OAuthNativeToolsRuntimeEntry: 脚本模式导入默认分组规则；如果没有这一行，bat 入口 Computer Use 分组会断开。
    chat_completion_schemas = available_tool_schemas(tool_pool)  # 新增代码+OAuthNativeToolsRuntimeEntry: 先复用旧稳定 schema 转换入口；如果没有这一行，新协议会重复实现 toolToAPISchema。
    deferred_tool_names = {tool.name for tool in tool_pool if tool.should_defer and not tool.always_load}  # 新增代码+OAuthNativeToolsRuntimeEntry: 从当前工具池计算应延迟加载的工具名；如果没有这一行，defer_loading 无法跟随每轮工具状态。
    computer_use_tool_names = {tool.name for tool in tool_pool if default_responses_namespace_for_tool_name(tool.name) == "computer_use"}  # 新增代码+OAuthNativeComputerUseNamespace: 把当前 Computer Use 工具也纳入延迟加载集合；如果没有这一行，桌面工具可能首轮 eager 暴露。
    deferred_tool_names.update(computer_use_tool_names)  # 新增代码+OAuthNativeComputerUseNamespace: 合并 Computer Use 延迟规则；如果没有这一行，权限/观察类工具可能缺少 defer_loading。
    return build_hosted_tool_search_tools_by_namespace(  # 新增代码+OAuthNativeToolsRuntimeEntry: 返回 Responses native 顶层 tools；如果没有这一行，OAuth adapter 拿不到 namespace/tool_search payload。
        chat_completion_schemas,  # 新增代码+OAuthNativeToolsRuntimeEntry: 传入旧格式 schema 列表供 builder 转换；如果没有这一行，builder 没有工具输入。
        deferred_tool_names=deferred_tool_names,  # 新增代码+OAuthNativeToolsRuntimeEntry: 传入每轮动态计算的 deferred 工具名；如果没有这一行，defer_loading 不会生效。
        namespace_for_tool=default_responses_namespace_for_tool_name,  # 新增代码+OAuthNativeToolsRuntimeEntry: 传入默认 namespace 分组规则；如果没有这一行，Computer Use namespace 无法生成。
        namespace_descriptions=default_responses_namespace_descriptions(),  # 新增代码+OAuthNativeToolsRuntimeEntry: 传入 namespace 说明；如果没有这一行，模型缺少分组语义。
    )  # 新增代码+OAuthNativeToolsRuntimeEntry: 结束 builder 调用；如果没有这一行，Python 调用语法不完整。
# 新增代码+OAuthNativeToolsRuntimeEntry: 函数段结束，available_responses_tool_schemas 到此结束；如果没有这个边界说明，用户不容易看出 native schema 入口范围。


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
