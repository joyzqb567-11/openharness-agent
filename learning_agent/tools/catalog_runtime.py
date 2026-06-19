"""工具目录、工具池和策略运行时。"""  # 新增代码+AgentPyPhaseHMcpToolRuntime: 把 catalog/pool/policy helper 从 agent.py 移到 tools 层；若没有这个文件，主类会继续承载工具可见性细节。

from __future__ import annotations  # 新增代码+AgentPyPhaseHMcpToolRuntime: 延迟解析类型注解，降低直接脚本运行时的导入顺序风险；若没有这行代码，部分注解可能提前求值失败。

import json  # 新增代码+AgentPyPhaseHMcpToolRuntime: tool_denial_key 需要稳定序列化工具参数；若没有这行代码，MCP 拒绝去重无法生成可复现 key。
from typing import Any  # 新增代码+AgentPyPhaseHMcpToolRuntime: 用 Any 表示传入的 agent duck type；若没有这行代码，本模块会为了注解反向导入 LearningAgent。

try:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 包运行模式下导入 MCP lifecycle、catalog 和 pool 依赖；若没有这行代码，tools 层无法独立承接真实实现。
    import learning_agent.mcp.agent_lifecycle as mcp_agent_lifecycle_from_mcp  # 新增代码+AgentPyPhaseHMcpToolRuntime: 导入 MCP 通知刷新实现；若没有这行代码，catalog 重建前无法消费 list_changed。
    from learning_agent.tool_policy import ToolPolicyDecision  # 新增代码+AgentPyPhaseHMcpToolRuntime: 导入策略决策类型；若没有这行代码，tool_policy_decision 的返回边界不清楚。
    from learning_agent.tools.catalog import build_builtin_tool_catalog  # 新增代码+AgentPyPhaseHMcpToolRuntime: 导入内置工具目录构建函数；若没有这行代码，catalog_runtime 无法构建基础工具目录。
    from learning_agent.tools.pool import available_tool_schemas as pool_available_tool_schemas  # 新增代码+AgentPyPhaseHMcpToolRuntime: 导入工具池转 schema helper；若没有这行代码，available_tool_schemas 会重复实现映射逻辑。
    from learning_agent.tools.pool import available_responses_tool_schemas as pool_available_responses_tool_schemas  # 新增代码+OAuthNativeToolsRuntimeEntry: 导入 Responses native 工具池转换 helper；如果没有这一行，OAuth native 模式无法从 filteredTools 当前快照生成顶层 tools。
    from learning_agent.tools.pool import filteredTools as pool_filteredTools  # 修改代码+FilteredTools删除旧名：导入和 ClaudeCode 同名的当前可用工具过滤 helper；如果没有这行代码，运行时链路就没有统一的工具过滤入口。
    from learning_agent.tools.pool import decide_tool_policy as pool_decide_tool_policy  # 新增代码+AgentPyPhaseHMcpToolRuntime: 导入统一策略决策 helper；若没有这行代码，loaded/allowed/workflow 规则会重新散落。
    from learning_agent.tools.pool import filter_allowed_tool_schemas as pool_filter_allowed_tool_schemas  # 新增代码+AgentPyPhaseHMcpToolRuntime: 导入 allowed_tools 白名单过滤 helper；若没有这行代码，子 agent 工具边界会重复实现。
    from learning_agent.tools.pool import tool_schema_names as pool_tool_schema_names  # 新增代码+AgentPyPhaseHMcpToolRuntime: 导入 schema 工具名提取 helper；若没有这行代码，日志工具名解析会留在主类。
    import learning_agent.tools.tool_scope as tool_scope_from_tools  # 新增代码+ClaudeCodeToolSurface：导入模式化工具池过滤层；如果没有这行代码，catalog_runtime 无法按代码/桌面/debug 模式统一裁剪工具。
    from learning_agent.tools.types import AgentTool  # 新增代码+AgentPyPhaseHMcpToolRuntime: 导入工具元数据类型；若没有这行代码，catalog helper 类型边界不清楚。
except ModuleNotFoundError as error:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致启动失败。
    if error.name not in {"learning_agent", "learning_agent.mcp", "learning_agent.mcp.agent_lifecycle", "learning_agent.tool_policy", "learning_agent.tools", "learning_agent.tools.catalog", "learning_agent.tools.pool", "learning_agent.tools.tool_scope", "learning_agent.tools.types"}:  # 修改代码+ClaudeCodeToolSurface：允许 tool_scope 路径差异进入脚本 fallback；如果没有这行代码，bat 入口会把包路径差异误报为导入失败。
        raise  # 新增代码+AgentPyPhaseHMcpToolRuntime: 重新抛出真正的导入错误；若没有这行代码，排查工具策略问题会看不到根因。
    import mcp.agent_lifecycle as mcp_agent_lifecycle_from_mcp  # 新增代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入 MCP 通知刷新实现；若没有这行代码，bat 入口工具目录刷新会断开。
    from tool_policy import ToolPolicyDecision  # 新增代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入策略决策类型；若没有这行代码，工具策略返回值无法统一。
    from tools.catalog import build_builtin_tool_catalog  # 新增代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入内置 catalog 构建函数；若没有这行代码，bat 入口没有基础工具目录。
    from tools.pool import available_tool_schemas as pool_available_tool_schemas  # 新增代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入工具池 schema helper；若没有这行代码，bat 入口无法生成模型工具 schema。
    from tools.pool import available_responses_tool_schemas as pool_available_responses_tool_schemas  # 新增代码+OAuthNativeToolsRuntimeEntry: 脚本模式下导入 Responses native 工具池转换 helper；如果没有这一行，start_oauth_agent.bat 无法生成 native tools。
    from tools.pool import filteredTools as pool_filteredTools  # 修改代码+FilteredTools删除旧名：脚本模式下导入同名过滤 helper；如果没有这行代码，start_oauth_agent.bat 运行路径下会找不到过滤入口。
    from tools.pool import decide_tool_policy as pool_decide_tool_policy  # 新增代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入策略决策 helper；若没有这行代码，bat 入口策略状态会断开。
    from tools.pool import filter_allowed_tool_schemas as pool_filter_allowed_tool_schemas  # 新增代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入 allowed_tools helper；若没有这行代码，子 agent 白名单会断开。
    from tools.pool import tool_schema_names as pool_tool_schema_names  # 新增代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入工具名提取 helper；若没有这行代码，终端日志工具名会断开。
    import tools.tool_scope as tool_scope_from_tools  # 新增代码+ClaudeCodeToolSurface：脚本模式下导入同一个模式化工具池过滤层；如果没有这行代码，start_oauth_agent.bat 不会执行 scope 规则。
    from tools.types import AgentTool  # 新增代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入 AgentTool 类型；若没有这行代码，目录 helper 无法工作。


def refresh_mcp_lifecycle_notifications(agent: Any) -> None:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段开始，转发 MCP lifecycle 刷新；若没有这段函数，agent.py 兼容入口需要直接导入 mcp 层。
    mcp_agent_lifecycle_from_mcp.refresh_mcp_lifecycle_notifications(agent)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 调用 MCP 层真实刷新实现；若没有这行代码，catalog_runtime 不会同步外部工具变化。
# 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段结束，refresh_mcp_lifecycle_notifications 到此结束；若没有这个边界说明，用户不容易看出这里只有转发职责。


def tool_catalog(agent: Any) -> list[AgentTool]:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段开始，返回完整工具目录；若没有这段函数，agent 只能看到当前工具池而无法保留 deferred 工具。
    refresh_mcp_lifecycle_notifications(agent)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 先处理 MCP list_changed 再复用或重建 catalog；若没有这行代码，外部 server 动态工具变化不会进入 ToolSearch。
    if agent._tool_catalog_cache is not None:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 如果本 agent 已经构建过 catalog 就复用同一批 AgentTool 对象；若没有这行代码，运行时 gate 修改会在下一次查找时丢失。
        return list(agent._tool_catalog_cache)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 返回缓存列表的浅拷贝以保护列表容器；若没有这行代码，调用方可能直接增删内部缓存列表。
    catalog = build_builtin_tool_catalog()  # 新增代码+AgentPyPhaseHMcpToolRuntime: 先把所有内置工具包装进 catalog；若没有这行代码，read/write/edit/bash 和 tool_search 等核心能力会从目录消失。
    if not agent.mcp_tools_enabled:  # 新增代码+AgentPyPhaseHMcpToolRuntime: MCP 未启用、启动失败或被拒绝时停止追加外部工具；若没有这行代码，未授权或不可用的 MCP 工具会泄露进 catalog。
        agent._tool_catalog_cache = catalog  # 新增代码+AgentPyPhaseHMcpToolRuntime: 缓存仅内置工具目录供后续策略判断复用；若没有这行代码，同一 agent 内对 catalog 工具的门禁修改不会稳定保留。
        return list(agent._tool_catalog_cache)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 返回缓存目录的浅拷贝；若没有这行代码，外部代码可能直接替换内部工具列表。
    agent_tools_method = getattr(agent.mcp_tool_registry, "agent_tools", None)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 读取 registry 的 AgentTool catalog 入口并兼容旧测试替身；若没有这行代码，缺少 agent_tools 的 registry 会让工具查询崩溃。
    if callable(agent_tools_method):  # 新增代码+AgentPyPhaseHMcpToolRuntime: 只有 registry 真提供 agent_tools 时才追加 MCP 目录；若没有这行代码，非函数属性会被误调用。
        catalog.extend(agent_tools_method())  # 新增代码+AgentPyPhaseHMcpToolRuntime: 把已发现的 MCP AgentTool 条目加入完整 catalog；若没有这行代码，后续加载机制找不到 deferred MCP 工具。
    agent._tool_catalog_cache = catalog  # 新增代码+AgentPyPhaseHMcpToolRuntime: 缓存完整目录对象让 find_catalog_tool 返回可持续修改的 AgentTool；若没有这行代码，select 前设置 skill_gate 的变更会被新对象覆盖。
    return list(agent._tool_catalog_cache)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 返回完整缓存目录的浅拷贝；若没有这行代码，调用方可能直接增删内部缓存列表。
# 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段结束，tool_catalog 到此结束；若没有这个边界说明，用户不容易看出完整 catalog 构建范围。


def find_catalog_tool(agent: Any, tool_name: str) -> AgentTool | None:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段开始，按名称从完整工具目录查找工具；若没有这段函数，select 和执行层只能重复手写遍历逻辑。
    requested_name = tool_name.strip()  # 新增代码+AgentPyPhaseHMcpToolRuntime: 清理调用方传入的工具名前后空白；若没有这行代码，select:mcp__x 后面带空格会误报找不到。
    if not requested_name:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 防御空工具名请求；若没有这行代码，空字符串会进入 catalog 遍历并返回模糊失败。
        return None  # 新增代码+AgentPyPhaseHMcpToolRuntime: 空名称直接表示没有找到；若没有这行代码，调用方无法用统一 None 处理失败。
    for tool in tool_catalog(agent):  # 新增代码+AgentPyPhaseHMcpToolRuntime: 遍历完整 catalog 而不是当前工具池；若没有这行代码，deferred MCP 工具仍然无法被 select 找到。
        if tool.name == requested_name:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 用模型可调用的工具名做精确匹配；若没有这行代码，select 可能错误加载相似但不同的工具。
            return tool  # 新增代码+AgentPyPhaseHMcpToolRuntime: 返回命中的 AgentTool 元数据；若没有这行代码，调用方无法知道应加载哪个工具。
    return None  # 新增代码+AgentPyPhaseHMcpToolRuntime: 遍历完仍未命中时返回 None；若没有这行代码，未知工具名会导致隐式返回不清晰。
# 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段结束，find_catalog_tool 到此结束；若没有这个边界说明，用户不容易看出目录查找范围。


def is_unloaded_deferred_tool(agent: Any, tool_name: str) -> bool:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段开始，判断工具是否仍处于未加载 deferred 状态；若没有这段函数，执行层无法统一拦截隐藏 MCP 工具。
    tool = find_catalog_tool(agent, tool_name)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 先用完整 catalog 查找工具元数据；若没有这行代码，隐藏 MCP 工具不会被执行层识别出来。
    if tool is None:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 未知工具不按 deferred 处理；若没有这行代码，后续访问属性会报错。
        return False  # 新增代码+AgentPyPhaseHMcpToolRuntime: 找不到工具时返回 False 交给原有未知工具逻辑；若没有这行代码，普通未知工具会被误判为延迟工具。
    if tool_scope_from_tools.tool_scope_forces_visible_agent_tool(agent, tool):  # 新增代码+ClaudeCodeToolSurface：Computer Use 操作/debug 模式会把原子工具强制加载；如果没有这行代码，executor 会把已按 scope 暴露的工具误拦为未 select。
        return False  # 新增代码+ClaudeCodeToolSurface：scope 强制可见的工具不再视为未加载 deferred；如果没有这行代码，模型看到工具后仍无法执行。
    return tool.source == "mcp" and tool.should_defer and tool.name not in agent.loaded_tool_names and not tool.always_load  # 新增代码+AgentPyPhaseHMcpToolRuntime: 只对外部 MCP deferred 工具执行硬拦截；若没有这行代码，内置工具测试会因模型可见性优化而无法直接验证工具函数。
# 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段结束，is_unloaded_deferred_tool 到此结束；若没有这个边界说明，用户不容易看出 deferred 判定范围。


def real_chrome_request_blocks_independent_browser(agent: Any, tool: AgentTool) -> bool:  # 修改代码+AgentPyPhaseHMcpToolRuntime: 函数段开始，工具策略直连浏览器 workflow 判断真实 Chrome 阻断；若没有这段函数，catalog_runtime 会通过 agent.py 兼容包装回跳。
    try:  # 修改代码+AgentPyPhaseHMcpToolRuntime: 包运行模式下延迟导入 browser workflow，避免模块顶层形成循环导入；若没有这行代码，tools 与 browser 互相导入时启动更脆弱。
        import learning_agent.browser.agent_workflow as browser_agent_workflow_from_browser  # 修改代码+AgentPyPhaseHMcpToolRuntime: 读取浏览器 workflow 的真实阻断实现；若没有这行代码，真实 Chrome 路线会缺少独立浏览器拦截规则。
    except ModuleNotFoundError as error:  # 修改代码+AgentPyPhaseHMcpToolRuntime: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致策略判断失败。
        if error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.agent_workflow"}:  # 修改代码+AgentPyPhaseHMcpToolRuntime: 只允许路径模式差异进入 fallback；若没有这行代码，browser workflow 内部真实错误会被误吞。
            raise  # 修改代码+AgentPyPhaseHMcpToolRuntime: 重新抛出真实导入错误；若没有这行代码，排查真实 Chrome 策略问题会看不到根因。
        import browser.agent_workflow as browser_agent_workflow_from_browser  # 修改代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下读取同一个浏览器 workflow 实现；若没有这行代码，bat 入口真实 Chrome 阻断判断会断开。
    return browser_agent_workflow_from_browser.real_chrome_request_blocks_independent_browser(agent, tool)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 返回浏览器 workflow 的真实阻断结果；若没有这行代码，策略层无法区分真实 Chrome 和独立浏览器工具。
# 修改代码+AgentPyPhaseHMcpToolRuntime: 函数段结束，real_chrome_request_blocks_independent_browser 到此结束；若没有这个边界说明，用户不容易看出浏览器阻断职责仍在 browser 层。


def tool_policy_decision(agent: Any, tool: AgentTool) -> ToolPolicyDecision:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段开始，统一计算工具策略决策；若没有这段函数，工具池、搜索和 select 会继续各自手写状态判断。
    real_chrome_blocked = real_chrome_request_blocks_independent_browser(agent, tool)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 直连浏览器 workflow 的真实 Chrome 阻断判断；若没有这行代码，catalog_runtime 会依赖 agent.py 兼容包装。
    base_decision = pool_decide_tool_policy(tool, tool_policy=agent.tool_policy, tool_policy_context=agent.tool_policy_context, allowed_tool_names=agent.allowed_tool_names, loaded_tool_names=agent.loaded_tool_names, real_chrome_blocked=real_chrome_blocked)  # 修改代码+ClaudeCodeToolSurface：先计算原有 loaded/deferred/workflow 策略；如果没有这行代码，scope 层会丢失原本的权限和 gate 判断。
    return tool_scope_from_tools.tool_scope_policy_decision(agent, tool, base_decision)  # 新增代码+ClaudeCodeToolSurface：再叠加模式化工具池过滤层；如果没有这行代码，Computer Use 模式只能靠提示词隐藏 read/write/edit/bash。
# 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段结束，tool_policy_decision 到此结束；若没有这个边界说明，用户不容易看出策略决策范围。


def tool_denial_key(tool_call: Any) -> str:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段开始，为 MCP 工具调用生成稳定拒绝记忆 key；若没有这段函数，无法按同一工具和参数去重用户拒绝。
    safe_arguments = json.dumps(tool_call.arguments, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 把清洗后参数转成排序 JSON；若没有这行代码，相同参数不同顺序会被误当成不同请求。
    return f"{tool_call.name}:{safe_arguments}"  # 新增代码+AgentPyPhaseHMcpToolRuntime: 拼接工具名和参数 JSON 作为唯一指纹；若没有这行代码，不同工具的相同参数可能互相污染拒绝记录。
# 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段结束，tool_denial_key 到此结束；若没有这个边界说明，用户不容易看出去重 key 生成范围。


def commit_pending_loaded_tool_names(agent: Any) -> None:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段开始，把本批 tool_calls 中延迟生效的 select 结果合并到 loaded 集合；若没有这段函数，pending 工具不会进入下一轮工具池。
    if not agent.pending_loaded_tool_names:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 没有待合并工具时直接返回；若没有这行代码，每轮都会做无意义集合更新。
        return  # 新增代码+AgentPyPhaseHMcpToolRuntime: 空 pending 不需要处理；若没有这行代码，函数会继续执行但没有实际工作。
    agent.loaded_tool_names.update(agent.pending_loaded_tool_names)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 批次结束后才让 select 工具正式 loaded；若没有这行代码，下一轮模型 schema 仍看不到已选择工具。
    agent.pending_loaded_tool_names.clear()  # 新增代码+AgentPyPhaseHMcpToolRuntime: 清空 pending 避免下一批重复合并旧工具；若没有这行代码，状态会残留并增加排查难度。
# 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段结束，commit_pending_loaded_tool_names 到此结束；若没有这个边界说明，用户不容易看出 pending 提交范围。


def filteredTools(agent: Any) -> list[AgentTool]:  # 新增代码+FilteredTools命名入口：函数段开始，返回当前真正暴露给模型的工具池；如果没有这段函数，agent 运行链路里仍看不到 ClaudeCode 同名 filteredTools 入口。
    return pool_filteredTools(tool_catalog(agent), lambda tool: tool_policy_decision(agent, tool))  # 新增代码+FilteredTools命名入口：委托 tools.pool 从完整目录过滤当前可见工具；如果没有这行代码，工具池过滤逻辑会重新散落到运行时模块。
# 新增代码+FilteredTools命名入口：函数段结束，filteredTools 到此结束；如果没有这个边界说明，用户不容易看出当前工具池范围。


def filter_allowed_tool_schemas(agent: Any, tool_schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段开始，根据 allowed_tool_names 过滤工具 schema；若没有这段函数，子 agent 无法执行工具白名单策略。
    return pool_filter_allowed_tool_schemas(tool_schemas, agent.allowed_tool_names)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 委托 tools.pool 执行 allowed_tools 白名单过滤；若没有这行代码，子 agent 工具边界逻辑仍散在主类。
# 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段结束，filter_allowed_tool_schemas 到此结束；若没有这个边界说明，用户不容易看出白名单过滤范围。


def available_tool_schemas(agent: Any) -> list[dict[str, Any]]:  # 修改代码+FilteredTools命名入口：函数段开始，返回 filteredTools 对应的模型 schema；如果没有这段函数，模型无法按 loaded/deferred 状态接收工具。
    all_tool_schemas = pool_available_tool_schemas(filteredTools(agent))  # 修改代码+FilteredTools命名入口：先用 ClaudeCode 同名 filteredTools 过滤当前可见工具，再转成 API schema；如果没有这行代码，schema 链路里看不出 filteredTools 的位置。
    return filter_allowed_tool_schemas(agent, all_tool_schemas)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 在当前工具池基础上继续应用子 agent 白名单；若没有这行代码，allowed_tools 参数不会真正限制模型可见工具。
# 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段结束，available_tool_schemas 到此结束；若没有这个边界说明，用户不容易看出 schema 生成范围。


def available_responses_tool_schemas(agent: Any) -> list[dict[str, Any]]:  # 新增代码+OAuthNativeToolsRuntimeEntry: 函数段开始，每轮从 filteredTools 当前快照生成 Responses native 顶层 tools；如果没有这段函数，OAuth native 模式会绕开当前工具策略。
    current_tools = filteredTools(agent)  # 新增代码+OAuthNativeToolsRuntimeEntry: 先按当前 agent 状态重新计算可见工具池；如果没有这一行，native tools 可能只按旧缓存或首轮状态生成。
    if agent.allowed_tool_names is not None:  # 新增代码+OAuthNativeToolsRuntimeEntry: 子 agent 白名单存在时继续收窄工具池；如果没有这一行，native tools 会绕过旧协议已有的 allowed_tools 边界。
        current_tools = [tool for tool in current_tools if tool.name in agent.allowed_tool_names]  # 新增代码+OAuthNativeToolsRuntimeEntry: 只保留白名单工具；如果没有这一行，子 agent 可能看到未授权工具。
    native_tool_schemas = pool_available_responses_tool_schemas(current_tools)  # 新增代码+OAuthNativeToolsRuntimeEntry: 把当前工具池转成 namespace/tool_search 形状；如果没有这一行，OAuth adapter 拿不到 Responses native tools。
    return native_tool_schemas  # 新增代码+OAuthNativeToolsRuntimeEntry: 返回本轮 native tools 快照；如果没有这一行，调用方无法发送顶层 tools。
# 新增代码+OAuthNativeToolsRuntimeEntry: 函数段结束，available_responses_tool_schemas 到此结束；如果没有这个边界说明，用户不容易看出 native 工具池生成范围。


def tool_schema_names(agent: Any, tools: list[dict[str, Any]] | None = None) -> list[str]:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段开始，从工具 schema 提取工具名；若没有这段函数，日志无法准确显示某一轮真实工具集合。
    selected_tools = tools if tools is not None else available_tool_schemas(agent)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 优先使用调用方指定工具列表，否则读取本轮可用工具；若没有这行代码，旧调用和动态工具调用无法同时兼容。
    return pool_tool_schema_names(selected_tools)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 委托 tools.pool 从 schema 提取工具名；若没有这行代码，日志和测试解析逻辑仍留在主类。
# 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段结束，tool_schema_names 到此结束；若没有这个边界说明，用户不容易看出工具名提取范围。
