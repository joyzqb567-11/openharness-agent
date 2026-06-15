"""工具搜索和按需加载的真实实现模块。"""  # 新增代码+AgentPyPhaseBToolSearch: 把 tool_search 能力从 agent.py 拆到 tools 层；若没有这个文件，主 agent 仍会继续承载搜索细节。

from __future__ import annotations  # 新增代码+AgentPyPhaseBToolSearch: 延迟解析类型注解；若没有这行代码，脚本模式下 Any 等注解解析更容易受导入顺序影响。

from typing import Any  # 新增代码+AgentPyPhaseBToolSearch: 使用 Any 表示传入的 agent 和工具元数据对象；若没有这行代码，新模块无法给薄边界写清楚类型。


try:  # 修改代码+AgentPyPhaseHMcpToolRuntime: 包运行模式下导入工具目录和策略运行时；若没有这行代码，tool_search 会继续通过 agent.py 薄包装访问 catalog。
    import learning_agent.tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 读取 catalog_runtime 的真实工具目录、查找和策略函数；若没有这行代码，tool_search 的真实实现归属会继续分裂。
except ModuleNotFoundError as error:  # 修改代码+AgentPyPhaseHMcpToolRuntime: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致导入失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.catalog_runtime"}:  # 修改代码+AgentPyPhaseHMcpToolRuntime: 只允许路径模式差异进入 fallback；若没有这行代码，catalog_runtime 内部真实错误会被误吞。
        raise  # 修改代码+AgentPyPhaseHMcpToolRuntime: 重新抛出真实导入错误；若没有这行代码，排查工具搜索问题会被 fallback 遮住根因。
    import tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下读取同一个工具目录和策略运行时；若没有这行代码，bat 入口调用 tool_search 会断开。


def capability_pack_tools(agent: Any, pack_name: str) -> list[Any]:  # 新增代码+AgentPyPhaseBToolSearch: 函数段开始，按能力包名称查找 catalog 工具；若没有这段函数，select_pack 需要重复遍历和过滤逻辑。
    normalized_pack_name = pack_name.strip().lower().replace("-", "_")  # 新增代码+AgentPyPhaseBToolSearch: 规范化用户传入的包名；若没有这行代码，real-chrome 和 real_chrome 这类写法无法兼容。
    if not normalized_pack_name:  # 新增代码+AgentPyPhaseBToolSearch: 防御空包名请求；若没有这行代码，空 select_pack 可能返回所有无包工具或模糊失败。
        return []  # 新增代码+AgentPyPhaseBToolSearch: 空包名直接返回空列表；若没有这行代码，调用方还要额外处理 None。
    return [tool for tool in catalog_runtime_from_tools.tool_catalog(agent) if tool.capability_pack.lower().replace("-", "_") == normalized_pack_name]  # 修改代码+AgentPyPhaseHMcpToolRuntime: 直连 catalog_runtime 返回匹配能力包的工具列表；若没有这行代码，能力包查找仍依赖 agent.py 薄包装。
# 新增代码+AgentPyPhaseBToolSearch: 函数段结束，capability_pack_tools 到此结束；若没有这个边界说明，用户不容易看出能力包查找范围。


def tool_search_select_pack(agent: Any, requested_pack: str) -> str:  # 新增代码+AgentPyPhaseBToolSearch: 函数段开始，处理 tool_search 的 select_pack:<pack> 请求；若没有这段函数，模型只能逐个 select 工具。
    pack_tools = capability_pack_tools(agent, requested_pack)  # 新增代码+AgentPyPhaseBToolSearch: 查找请求能力包下的所有工具；若没有这行代码，无法知道要加载哪些工具。
    if not pack_tools:  # 新增代码+AgentPyPhaseBToolSearch: 处理未知或空能力包；若没有这行代码，未知 pack 可能被误报成功。
        return f"tool_search 失败：没有找到能力包 {requested_pack!r}，请先用 tool_search 搜索相关能力。"  # 新增代码+AgentPyPhaseBToolSearch: 返回可恢复的失败说明；若没有这行代码，模型不知道应重新搜索能力名。
    loaded_names: list[str] = []  # 新增代码+AgentPyPhaseBToolSearch: 保存本次成功加入工具池的工具名；若没有这行代码，输出无法说明加载了哪些工具。
    blocked_lines: list[str] = []  # 新增代码+AgentPyPhaseBToolSearch: 保存因策略未加载的工具说明；若没有这行代码，部分失败会被静默吞掉。
    for tool in pack_tools:  # 新增代码+AgentPyPhaseBToolSearch: 遍历能力包内每个工具；若没有这行代码，无法批量加载整包工具。
        decision = catalog_runtime_from_tools.tool_policy_decision(agent, tool)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 直连 catalog_runtime 判断工具是否可选择；若没有这行代码，select_pack 仍会反向依赖 agent.py 策略薄包装。
        if not decision.selectable:  # 新增代码+AgentPyPhaseBToolSearch: 跳过当前不可选择的工具；若没有这行代码，blocked 或 needs_skill 工具可能被错误加载。
            blocked_lines.append(f"- {tool.name}: state={decision.state}; reason={decision.reason or '(无)'}")  # 新增代码+AgentPyPhaseBToolSearch: 记录未加载原因；若没有这行代码，模型无法知道下一步该补 skill 还是 workflow。
            continue  # 新增代码+AgentPyPhaseBToolSearch: 继续处理同包其他工具；若没有这行代码，一个 gated 工具会阻断整个能力包。
        if agent.defer_tool_select_until_next_turn:  # 新增代码+AgentPyPhaseBToolSearch: run 同一批 tool_calls 中延迟加载生效；若没有这行代码，select_pack 会破坏既有下一轮才可见语义。
            agent.pending_loaded_tool_names.add(tool.name)  # 新增代码+AgentPyPhaseBToolSearch: 把工具名放入 pending 集合；若没有这行代码，下一轮工具池看不到刚选择的整包工具。
        else:  # 新增代码+AgentPyPhaseBToolSearch: 非 run 批处理场景允许立即加载；若没有这行代码，单元测试和手动调试需要额外提交 pending 状态。
            agent.loaded_tool_names.add(tool.name)  # 新增代码+AgentPyPhaseBToolSearch: 把工具名加入已加载集合；若没有这行代码，select_pack 返回成功但工具池不会变化。
        loaded_names.append(tool.name)  # 新增代码+AgentPyPhaseBToolSearch: 记录成功加载的工具名；若没有这行代码，输出无法展示加载结果。
    if not loaded_names:  # 新增代码+AgentPyPhaseBToolSearch: 处理整包都被策略阻断的情况；若没有这行代码，空加载也可能返回成功。
        return "tool_search 失败：能力包 " + requested_pack + " 没有可加载工具。\n" + "\n".join(blocked_lines)  # 新增代码+AgentPyPhaseBToolSearch: 返回所有阻断原因；若没有这行代码，模型不知道为什么整包加载失败。
    timing_text = "将在下一轮工具池加载" if agent.defer_tool_select_until_next_turn else "已加载到当前工具池"  # 新增代码+AgentPyPhaseBToolSearch: 根据运行状态说明生效时机；若没有这行代码，模型可能误以为同一批调用已经能用。
    lines = [f"tool_search 成功：能力包 {requested_pack} {timing_text}。"]  # 新增代码+AgentPyPhaseBToolSearch: 构造成功标题；若没有这行代码，输出缺少明确状态。
    lines.append("已加载工具：" + ", ".join(loaded_names))  # 新增代码+AgentPyPhaseBToolSearch: 列出成功加载的工具；若没有这行代码，用户无法确认包内实际加载范围。
    lines.append(f"建议：如需详细流程，请调用 skill_load，name={requested_pack!r}。")  # 新增代码+AgentPyPhaseBToolSearch: 引导模型读取对应 skill；若没有这行代码，模型可能只加载 schema 而不读取操作规程。
    if blocked_lines:  # 新增代码+AgentPyPhaseBToolSearch: 如果同包有部分工具没加载；若没有这行代码，部分阻断信息会丢失。
        lines.append("未加载工具：")  # 新增代码+AgentPyPhaseBToolSearch: 添加未加载分组标题；若没有这行代码，成功和失败条目会混在一起。
        lines.extend(blocked_lines)  # 新增代码+AgentPyPhaseBToolSearch: 追加阻断明细；若没有这行代码，gate 状态无法反馈给模型。
    return "\n".join(lines)  # 新增代码+AgentPyPhaseBToolSearch: 返回完整 select_pack 结果；若没有这行代码，工具调用没有输出。
# 新增代码+AgentPyPhaseBToolSearch: 函数段结束，tool_search_select_pack 到此结束；若没有这个边界说明，用户不容易看出整包加载范围。


def tool_search_select(agent: Any, requested_name: str) -> str:  # 新增代码+AgentPyPhaseBToolSearch: 函数段开始，处理 tool_search 的 select:<tool_name> 加载请求；若没有这段函数，模型发现 deferred 工具后仍无法把它加入后续工具池。
    tool = catalog_runtime_from_tools.find_catalog_tool(agent, requested_name)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 直连 catalog_runtime 查找用户请求加载的工具；若没有这行代码，select 仍会依赖 agent.py 兼容入口。
    if tool is None:  # 新增代码+AgentPyPhaseBToolSearch: 判断请求的工具名是否存在；若没有这行代码，未知工具名会继续进入加载集合造成假成功。
        return f"tool_search 失败：没有找到工具 {requested_name!r}，请先用 tool_search 搜索完整工具名。"  # 新增代码+AgentPyPhaseBToolSearch: 返回清晰失败原因和修正方向；若没有这行代码，模型不知道应该重新搜索还是换名称。
    decision = catalog_runtime_from_tools.tool_policy_decision(agent, tool)  # 修改代码+AgentPyPhaseHMcpToolRuntime: select 前直连 catalog_runtime 读取统一策略决策；若没有这行代码，blocked 或缺 skill 的工具可能绕过统一归属。
    if not decision.selectable:  # 新增代码+AgentPyPhaseBToolSearch: 判断当前策略是否允许通过 select 加载；若没有这行代码，needs_skill/needs_workflow/blocked 工具无法被拦在加载前。
        reason_text = f"；阻断原因：{decision.reason}" if decision.reason else ""  # 新增代码+AgentPyPhaseBToolSearch: 把策略原因转换成人类可读后缀；若没有这行代码，失败输出只有状态但缺少解释。
        skill_hint = "；需要先加载 skill" if decision.state == "needs_skill" else ""  # 新增代码+AgentPyPhaseBToolSearch: 给缺 skill 的场景补一句直接提示；若没有这行代码，用户可能不知道 needs_skill 应该怎么处理。
        return f"tool_search 失败：工具 {tool.name} 当前不可选择，state={decision.state}{reason_text}{skill_hint}。"  # 新增代码+AgentPyPhaseBToolSearch: 返回包含 state 和 reason 的 select 失败；若没有这行代码，模型会误以为 select 失败只是工具不存在。
    if agent.defer_tool_select_until_next_turn:  # 新增代码+AgentPyPhaseBToolSearch: run 正在处理同一批 tool_calls 时先延迟 select 生效；若没有这行代码，同批后续 MCP 调用会绕过下一轮工具池边界。
        agent.pending_loaded_tool_names.add(tool.name)  # 新增代码+AgentPyPhaseBToolSearch: 把工具名放入 pending 集合等待批次结束合并；若没有这行代码，select 结果会丢失或立刻生效。
        return f"tool_search 成功：已选择 {tool.name}，将在下一轮工具池加载。"  # 新增代码+AgentPyPhaseBToolSearch: 返回下一轮才加载的清楚提示；若没有这行代码，模型会误以为同一批后续调用已经可用。
    agent.loaded_tool_names.add(tool.name)  # 新增代码+AgentPyPhaseBToolSearch: 普通直接调用 select 时继续立即加入已加载集合；若没有这行代码，现有单元测试和手动调试会失去便利。
    return f"tool_search 成功：已加载 {tool.name}，后续工具池可以使用该工具。"  # 新增代码+AgentPyPhaseBToolSearch: 返回包含“已加载”的成功文本；若没有这行代码，调用方无法确认策略允许后的 select 是否生效。
# 新增代码+AgentPyPhaseBToolSearch: 函数段结束，tool_search_select 到此结束；若没有这个边界说明，用户不容易看出单工具加载范围。


def tool_search(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseBToolSearch: 函数段开始，搜索完整工具 catalog 并支持 select 加载 deferred 工具；若没有这段函数，模型无法发现或启用延迟工具。
    query = str(arguments.get("query", "")).strip()  # 新增代码+AgentPyPhaseBToolSearch: 读取并清理搜索关键词或 select 指令；若没有这行代码，空白或缺参会导致搜索意图不明确。
    if not query:  # 新增代码+AgentPyPhaseBToolSearch: 检查 query 是否为空；若没有这行代码，空搜索可能返回大量无意义工具。
        return "tool_search 失败：缺少 query 参数。"  # 新增代码+AgentPyPhaseBToolSearch: 返回清楚缺参错误；若没有这行代码，模型难以修正工具调用参数。
    if query.startswith("select:"):  # 新增代码+AgentPyPhaseBToolSearch: 识别 select:<tool_name> 加载指令；若没有这行代码，select 会被当成普通关键词搜索而不会加载工具。
        return tool_search_select(agent, query.removeprefix("select:").strip())  # 新增代码+AgentPyPhaseBToolSearch: 把 select 后面的工具名交给加载函数；若没有这行代码，deferred 工具无法进入后续工具池。
    if query.startswith("select_pack:"):  # 新增代码+AgentPyPhaseBToolSearch: 识别 select_pack:<pack> 加载指令；若没有这行代码，模型无法批量加载能力包工具。
        return tool_search_select_pack(agent, query.removeprefix("select_pack:").strip())  # 新增代码+AgentPyPhaseBToolSearch: 把包名交给能力包加载函数；若没有这行代码，select_pack 只会被当成普通搜索。
    max_results = tool_search_max_results(arguments.get("max_results"))  # 新增代码+AgentPyPhaseBToolSearch: 解析最大结果数并限制范围；若没有这行代码，搜索结果可能撑爆上下文。
    terms = tool_search_terms(query)  # 新增代码+AgentPyPhaseBToolSearch: 把搜索词拆成可匹配的小写关键词；若没有这行代码，多词搜索和大小写匹配会不稳定。
    scored_results: list[tuple[int, Any, str, Any, str]] = []  # 新增代码+AgentPyPhaseBToolSearch: 保存分数、工具、来源、策略决策和参数文本；若没有这行代码，搜索结果无法展示 blocked/needs_skill 等统一状态。
    for tool in catalog_runtime_from_tools.tool_catalog(agent):  # 修改代码+AgentPyPhaseHMcpToolRuntime: 遍历 catalog_runtime 的完整工具目录而不是当前工具池；若没有这行代码，tool_search 仍通过 agent.py 薄包装发现 deferred 工具。
        if not tool.name:  # 新增代码+AgentPyPhaseBToolSearch: 跳过没有名称的异常工具条目；若没有这行代码，坏 catalog 数据可能污染搜索结果。
            continue  # 新增代码+AgentPyPhaseBToolSearch: 继续处理其他工具；若没有这行代码，单个坏工具会阻断搜索。
        properties = tool.input_schema.get("properties", {}) if isinstance(tool.input_schema, dict) else {}  # 新增代码+AgentPyPhaseBToolSearch: 从 AgentTool.input_schema 读取参数字段定义；若没有这行代码，搜索无法按参数名匹配也无法展示参数。
        parameter_names = [str(name) for name in properties.keys()] if isinstance(properties, dict) else []  # 新增代码+AgentPyPhaseBToolSearch: 把参数字段名转成字符串列表；若没有这行代码，模型找到工具后仍不知道主要入参。
        pack_aliases = tool.aliases + ([tool.capability_pack] if tool.capability_pack else [])  # 新增代码+AgentPyPhaseBToolSearch: 把能力包名也作为搜索别名；若没有这行代码，用户搜 file_operations 可能找不到包内工具。
        pack_search_hint = " ".join(part for part in [tool.search_hint, tool.capability_pack] if part)  # 新增代码+AgentPyPhaseBToolSearch: 把能力包名加入搜索提示；若没有这行代码，自然语言搜能力包的召回会变弱。
        score = tool_search_score(terms, tool.name, tool.description, parameter_names, pack_search_hint, pack_aliases)  # 新增代码+AgentPyPhaseBToolSearch: 把 pack 名纳入相关度计算；若没有这行代码，工具搜索无法按能力包名召回。
        if score <= 0:  # 新增代码+AgentPyPhaseBToolSearch: 过滤没有任何命中的工具；若没有这行代码，搜索会返回大量无关工具。
            continue  # 新增代码+AgentPyPhaseBToolSearch: 跳过不相关工具；若没有这行代码，无关工具会污染结果。
        source_parts = [tool.source]  # 新增代码+AgentPyPhaseBToolSearch: 准备展示工具来源字段；若没有这行代码，输出缺少 source 信息。
        if tool.server_name:  # 新增代码+AgentPyPhaseBToolSearch: MCP 工具通常带有 server 名；若没有这行代码，外部工具来源会缺少具体 server。
            source_parts.append(f"server={tool.server_name}")  # 新增代码+AgentPyPhaseBToolSearch: 把 server 名追加到来源文本；若没有这行代码，用户和模型难以区分不同 MCP server。
        source_text = ", ".join(source_parts)  # 新增代码+AgentPyPhaseBToolSearch: 合并来源片段成可读文本；若没有这行代码，输出 source 字段无法直接展示。
        decision = catalog_runtime_from_tools.tool_policy_decision(agent, tool)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 直连 catalog_runtime 生成搜索状态；若没有这行代码，tool_search 的策略来源仍与执行器分裂。
        if decision.state == "scope_blocked":  # 新增代码+ClaudeCodeToolSurface：模式化工具池隐藏的工具不进入搜索结果；如果没有这行代码，模型仍会在代码模式搜到被隐藏的桌面工具。
            continue  # 新增代码+ClaudeCodeToolSurface：跳过当前 scope 不允许发现的工具；如果没有这行代码，tool_search 会泄露另一种模式的工具名。
        parameter_text = ", ".join(parameter_names) if parameter_names else "(无参数)"  # 新增代码+AgentPyPhaseBToolSearch: 把参数名合并成可读文本；若没有这行代码，输出里参数展示不清楚。
        scored_results.append((score, tool, source_text, decision, parameter_text))  # 新增代码+AgentPyPhaseBToolSearch: 保存包含策略决策的 catalog 命中结果；若没有这行代码，格式化阶段拿不到 state 和 reason。
    scored_results.sort(key=lambda item: (-item[0], item[1].name))  # 新增代码+AgentPyPhaseBToolSearch: 按分数降序和工具名升序排序；若没有这行代码，搜索结果顺序不稳定且不够相关。
    visible_results = scored_results[:max_results]  # 新增代码+AgentPyPhaseBToolSearch: 截取最多 max_results 条结果；若没有这行代码，大量 MCP 工具会撑爆上下文。
    if not visible_results:  # 新增代码+AgentPyPhaseBToolSearch: 处理没有命中的情况；若没有这行代码，空结果会返回只有标题的模糊文本。
        return f"tool_search 成功：没有找到匹配 query={query!r} 的工具。"  # 新增代码+AgentPyPhaseBToolSearch: 明确告诉模型没有结果；若没有这行代码，模型可能误以为工具搜索失败。
    lines = [f"tool_search 成功：query={query!r}，找到 {len(scored_results)} 个相关工具，显示前 {len(visible_results)} 个。"]  # 新增代码+AgentPyPhaseBToolSearch: 构造结果标题；若没有这行代码，模型不知道结果数量和截断情况。
    for index, (_, tool, source_text, decision, parameter_text) in enumerate(visible_results, start=1):  # 新增代码+AgentPyPhaseBToolSearch: 逐条格式化带策略决策的 catalog 命中结果；若没有这行代码，命中结果无法展示 state/reason。
        lines.append(f"{index}. {tool.name}")  # 新增代码+AgentPyPhaseBToolSearch: 输出工具名；若没有这行代码，模型不知道后续应调用或 select 哪个工具。
        lines.append(f"   source/来源：{source_text}")  # 新增代码+AgentPyPhaseBToolSearch: 输出 source 字段并保留中文来源提示；若没有这行代码，模型无法区分内置工具和外部 MCP 工具。
        lines.append(f"   state：{decision.state}")  # 新增代码+AgentPyPhaseBToolSearch: 输出 ToolPolicyDecision.state；若没有这行代码，模型不知道工具是 loaded、deferred、blocked 还是缺少 gate。
        lines.append(f"   参数：{parameter_text}")  # 新增代码+AgentPyPhaseBToolSearch: 输出参数名；若没有这行代码，模型找到工具后还可能传错参数。
        if tool.aliases:  # 新增代码+AgentPyPhaseBToolSearch: 只有工具声明了 aliases 时才展示别名；若没有这行代码，模型看不到可用于搜索和理解的替代名称。
            lines.append(f"   aliases：{', '.join(tool.aliases)}")  # 新增代码+AgentPyPhaseBToolSearch: 输出工具别名列表；若没有这行代码，别名命中后仍缺少可解释的结果依据。
        if tool.search_hint:  # 新增代码+AgentPyPhaseBToolSearch: 只有工具声明了 search_hint 时才展示搜索提示；若没有这行代码，MCP 提供的语义线索不会出现在搜索结果里。
            lines.append(f"   search_hint：{tool.search_hint}")  # 新增代码+AgentPyPhaseBToolSearch: 输出搜索提示文本；若没有这行代码，模型不知道该工具为什么被召回。
        if tool.capability_pack:  # 新增代码+AgentPyPhaseBToolSearch: 只有工具声明了能力包时才展示包名；若没有这行代码，模型不知道可以用哪个 select_pack 批量加载。
            lines.append(f"   capability_pack：{tool.capability_pack}")  # 新增代码+AgentPyPhaseBToolSearch: 输出能力包名称；若没有这行代码，搜索结果缺少批量加载入口。
        lines.append(f"   说明：{tool.description or '(无说明)'}")  # 新增代码+AgentPyPhaseBToolSearch: 输出工具说明；若没有这行代码，模型缺少选择工具的语义依据。
        if decision.reason:  # 新增代码+AgentPyPhaseBToolSearch: 只有策略提供原因时才展示阻断说明；若没有这行代码，blocked 或 gate 工具只显示状态而缺少人话解释。
            lines.append(f"   阻断原因：{decision.reason}")  # 新增代码+AgentPyPhaseBToolSearch: 输出清楚的策略原因；若没有这行代码，用户不知道工具为什么不可见或不可选。
        if decision.state == "deferred":  # 新增代码+AgentPyPhaseBToolSearch: 只给 deferred 工具显示加载提示；若没有这行代码，blocked/needs_skill 工具可能出现误导性的 select 提示。
            lines.append(f"   加载提示：select:{tool.name}")  # 新增代码+AgentPyPhaseBToolSearch: 保留单工具加载提示兼容旧流程；若没有这行代码，已有测试和模型习惯可能找不到精确 select 语法。
            if tool.capability_pack:  # 新增代码+AgentPyPhaseBToolSearch: 只有存在能力包时才追加整包加载提示；若没有这行代码，无包工具会出现空 pack 指令。
                lines.append(f"   能力包加载提示：select_pack:{tool.capability_pack}")  # 新增代码+AgentPyPhaseBToolSearch: 输出批量加载指令；若没有这行代码，模型不知道可以一次加载整组工具。
    return "\n".join(lines)  # 新增代码+AgentPyPhaseBToolSearch: 返回完整搜索结果文本；若没有这行代码，工具搜索无法把结果交回模型。
# 新增代码+AgentPyPhaseBToolSearch: 函数段结束，tool_search 到此结束；若没有这个边界说明，用户不容易看出完整搜索流程。


def tool_search_max_results(raw_value: Any) -> int:  # 新增代码+AgentPyPhaseBToolSearch: 函数段开始，把 max_results 转成 1 到 20 的整数；若没有这段函数，模型可能传入字符串、空值或过大数字。
    try:  # 新增代码+AgentPyPhaseBToolSearch: 捕获模型传入非数字值的情况；若没有这行代码，int() 异常会中断工具调用。
        value = int(raw_value) if raw_value is not None else 10  # 新增代码+AgentPyPhaseBToolSearch: None 使用默认 10，否则尝试转整数；若没有这行代码，省略 max_results 时没有默认值。
    except (TypeError, ValueError):  # 新增代码+AgentPyPhaseBToolSearch: 处理无法转成整数的参数；若没有这行代码，坏参数会让工具崩溃。
        value = 10  # 新增代码+AgentPyPhaseBToolSearch: 非法 max_results 回退默认值；若没有这行代码，模型一次传错参数就无法继续搜索。
    return max(1, min(value, 20))  # 新增代码+AgentPyPhaseBToolSearch: 把结果数限制在 1 到 20；若没有这行代码，0 或超大值会导致结果为空或撑爆上下文。
# 新增代码+AgentPyPhaseBToolSearch: 函数段结束，tool_search_max_results 到此结束；若没有这个边界说明，用户不容易看出数量限制逻辑。


def tool_search_terms(query: str) -> list[str]:  # 新增代码+AgentPyPhaseBToolSearch: 函数段开始，把用户查询拆成小写关键词；若没有这段函数，多词查询和下划线工具名匹配会变差。
    normalized = query.replace("_", " ").replace("-", " ").lower()  # 新增代码+AgentPyPhaseBToolSearch: 把下划线和连字符转为空格并统一小写；若没有这行代码，mcp 工具名片段不容易被匹配。
    terms = [term for term in normalized.split() if term]  # 新增代码+AgentPyPhaseBToolSearch: 按空白拆词并去掉空项；若没有这行代码，多余空格会产生无意义关键词。
    return terms or [query.lower()]  # 新增代码+AgentPyPhaseBToolSearch: 没有拆出词时保留原始小写查询；若没有这行代码，中文或特殊查询可能变成空搜索。
# 新增代码+AgentPyPhaseBToolSearch: 函数段结束，tool_search_terms 到此结束；若没有这个边界说明，用户不容易看出关键词拆分范围。


def tool_schema_name(schema: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseBToolSearch: 函数段开始，从 OpenAI-compatible schema 中取 function.name；若没有这段函数，搜索无法识别工具名称。
    function = schema.get("function", {}) if isinstance(schema, dict) else {}  # 新增代码+AgentPyPhaseBToolSearch: 安全读取 function 字段；若没有这行代码，畸形 schema 可能触发异常。
    if not isinstance(function, dict):  # 新增代码+AgentPyPhaseBToolSearch: 检查 function 是否为字典；若没有这行代码，非对象 function 会让 get 调用失败。
        return ""  # 新增代码+AgentPyPhaseBToolSearch: 坏 schema 返回空名并交给上层跳过；若没有这行代码，搜索会被单个坏 schema 打断。
    return str(function.get("name", "")).strip()  # 新增代码+AgentPyPhaseBToolSearch: 返回清理后的工具名；若没有这行代码，工具名前后空白会影响匹配和展示。
# 新增代码+AgentPyPhaseBToolSearch: 函数段结束，tool_schema_name 到此结束；若没有这个边界说明，用户不容易看出 schema 名称读取范围。


def tool_schema_description(schema: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseBToolSearch: 函数段开始，从 schema 中取工具说明；若没有这段函数，搜索无法利用自然语言说明。
    function = schema.get("function", {}) if isinstance(schema, dict) else {}  # 新增代码+AgentPyPhaseBToolSearch: 安全读取 function 字段；若没有这行代码，畸形 schema 可能触发异常。
    if not isinstance(function, dict):  # 新增代码+AgentPyPhaseBToolSearch: 检查 function 是否为字典；若没有这行代码，非对象 function 会让 get 调用失败。
        return ""  # 新增代码+AgentPyPhaseBToolSearch: 坏 schema 返回空说明；若没有这行代码，搜索会因为坏 schema 中断。
    return str(function.get("description", "")).strip()  # 新增代码+AgentPyPhaseBToolSearch: 返回清理后的说明文本；若没有这行代码，说明里的空白会污染输出。
# 新增代码+AgentPyPhaseBToolSearch: 函数段结束，tool_schema_description 到此结束；若没有这个边界说明，用户不容易看出 schema 说明读取范围。


def tool_schema_parameter_names(schema: dict[str, Any]) -> list[str]:  # 新增代码+AgentPyPhaseBToolSearch: 函数段开始，从工具参数 schema 中提取参数名；若没有这段函数，搜索无法按参数名匹配。
    function = schema.get("function", {}) if isinstance(schema, dict) else {}  # 新增代码+AgentPyPhaseBToolSearch: 安全读取 function 字段；若没有这行代码，畸形 schema 可能触发异常。
    if not isinstance(function, dict):  # 新增代码+AgentPyPhaseBToolSearch: 检查 function 是否为字典；若没有这行代码，非对象 function 会让 get 调用失败。
        return []  # 新增代码+AgentPyPhaseBToolSearch: 坏 schema 返回空参数；若没有这行代码，搜索会被异常中断。
    parameters = function.get("parameters", {})  # 新增代码+AgentPyPhaseBToolSearch: 读取 JSON Schema 参数对象；若没有这行代码，无法进入 properties。
    if not isinstance(parameters, dict):  # 新增代码+AgentPyPhaseBToolSearch: 检查 parameters 是否为字典；若没有这行代码，畸形参数 schema 会导致异常。
        return []  # 新增代码+AgentPyPhaseBToolSearch: 坏参数 schema 返回空列表；若没有这行代码，单个坏工具会破坏搜索。
    properties = parameters.get("properties", {})  # 新增代码+AgentPyPhaseBToolSearch: 读取参数字段定义；若没有这行代码，无法枚举参数名。
    if not isinstance(properties, dict):  # 新增代码+AgentPyPhaseBToolSearch: 检查 properties 是否为字典；若没有这行代码，非对象 properties 会导致 items 调用失败。
        return []  # 新增代码+AgentPyPhaseBToolSearch: 坏 properties 返回空列表；若没有这行代码，搜索健壮性降低。
    return [str(name) for name in properties.keys()]  # 新增代码+AgentPyPhaseBToolSearch: 返回所有参数名字符串；若没有这行代码，输出和搜索都看不到参数字段。
# 新增代码+AgentPyPhaseBToolSearch: 函数段结束，tool_schema_parameter_names 到此结束；若没有这个边界说明，用户不容易看出 schema 参数读取范围。


def tool_schema_source(tool_name: str) -> str:  # 新增代码+AgentPyPhaseBToolSearch: 函数段开始，根据工具名判断内置或 MCP 来源；若没有这段函数，用户和模型难以区分工具边界。
    parts = tool_name.split("__")  # 新增代码+AgentPyPhaseBToolSearch: 按 MCP 命名约定拆分工具名；若没有这行代码，无法提取 server 名。
    if len(parts) >= 3 and parts[0] == "mcp":  # 新增代码+AgentPyPhaseBToolSearch: 识别 mcp__server__tool 格式；若没有这行代码，MCP 工具会被误标为内置。
        return f"MCP server：{parts[1]}"  # 新增代码+AgentPyPhaseBToolSearch: 返回 MCP server 来源；若没有这行代码，搜索结果缺少外部来源信息。
    return "内置工具"  # 新增代码+AgentPyPhaseBToolSearch: 非 MCP 前缀默认视为内置工具；若没有这行代码，内置工具没有来源说明。
# 新增代码+AgentPyPhaseBToolSearch: 函数段结束，tool_schema_source 到此结束；若没有这个边界说明，用户不容易看出来源判断范围。


def tool_search_score(terms: list[str], tool_name: str, description: str, parameter_names: list[str], search_hint: str = "", aliases: list[str] | None = None) -> int:  # 新增代码+AgentPyPhaseBToolSearch: 函数段开始，根据名称、说明、参数名、搜索提示和别名计算匹配分数；若没有这段函数，searchHint/aliases 元数据只保存但不参与发现。
    name_text = tool_name.lower()  # 新增代码+AgentPyPhaseBToolSearch: 工具名转小写便于大小写无关匹配；若没有这行代码，Notebook/notebook 这类大小写差异会漏匹配。
    description_text = description.lower()  # 新增代码+AgentPyPhaseBToolSearch: 说明转小写便于匹配；若没有这行代码，英文说明大小写可能影响结果。
    parameter_text = " ".join(parameter_names).lower()  # 新增代码+AgentPyPhaseBToolSearch: 参数名合并并转小写；若没有这行代码，无法按 query/url/path 这类参数名搜索。
    search_hint_text = search_hint.lower()  # 新增代码+AgentPyPhaseBToolSearch: 把 MCP searchHint 转小写后参与匹配；若没有这行代码，服务端提供的搜索语义不会影响召回。
    alias_text = " ".join(aliases or []).lower()  # 新增代码+AgentPyPhaseBToolSearch: 把 aliases 合并转小写后参与匹配；若没有这行代码，别名不会真正帮助模型发现工具。
    score = 0  # 新增代码+AgentPyPhaseBToolSearch: 初始化相关度分数；若没有这行代码，后续无法累加命中权重。
    for term in terms:  # 新增代码+AgentPyPhaseBToolSearch: 遍历每个查询关键词；若没有这行代码，多词查询只会处理整体字符串。
        if term in name_text:  # 新增代码+AgentPyPhaseBToolSearch: 工具名命中权重最高；若没有这行代码，精确工具名搜索排序会变差。
            score += 6  # 新增代码+AgentPyPhaseBToolSearch: 给工具名命中较高分；若没有这行代码，名称相关工具可能排在说明偶然命中的工具后面。
        if term in alias_text:  # 新增代码+AgentPyPhaseBToolSearch: 别名命中说明用户或模型使用了替代称呼；若没有这行代码，aliases 只能展示不能搜索。
            score += 5  # 新增代码+AgentPyPhaseBToolSearch: 给别名命中接近工具名的高分；若没有这行代码，别名匹配可能排在不相关说明命中之后。
        if term in search_hint_text:  # 新增代码+AgentPyPhaseBToolSearch: searchHint 命中说明 MCP server 主动给了语义线索；若没有这行代码，外部工具发现能力不如 ClaudeCode 风格 catalog。
            score += 4  # 新增代码+AgentPyPhaseBToolSearch: 给 searchHint 命中较高分；若没有这行代码，服务端提示无法有效提升排序。
        if term in parameter_text:  # 新增代码+AgentPyPhaseBToolSearch: 参数名命中说明模型可能正在找某类入参；若没有这行代码，query/url/path 这类搜索效果变差。
            score += 3  # 新增代码+AgentPyPhaseBToolSearch: 给参数名命中中等分；若没有这行代码，参数相关性无法影响排序。
        if term in description_text:  # 新增代码+AgentPyPhaseBToolSearch: 说明命中用于自然语言能力发现；若没有这行代码，“天气/Notebook”等描述词无法召回工具。
            score += 2  # 新增代码+AgentPyPhaseBToolSearch: 给说明命中基础分；若没有这行代码，自然语言搜索结果排序不稳定。
    return score  # 新增代码+AgentPyPhaseBToolSearch: 返回最终相关度；若没有这行代码，调用方无法判断是否命中。
# 新增代码+AgentPyPhaseBToolSearch: 函数段结束，tool_search_score 到此结束；若没有这个边界说明，用户不容易看出相关度计算范围。
