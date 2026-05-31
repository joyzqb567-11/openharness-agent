"""工具执行分发器。"""  # 新增代码+ToolsExecutorSplit: 把 _execute_tool 的守卫和分发表从主入口拆出；若没有这个文件，执行层问题仍要翻 LearningAgent 大类。

from __future__ import annotations  # 新增代码+ToolsExecutorSplit: 延迟解析类型注解；若没有这行代码，脚本模式下导入顺序会更脆弱。

from typing import Any, Callable  # 新增代码+ToolsExecutorSplit: 执行器需要通用 agent 对象和 handler 回调类型；若没有这行代码，类型边界不清楚。

try:  # 新增代码+ToolsExecutorSplit: 包运行模式下导入工具调用数据结构；若没有这行代码，执行器无法读取 tool_call.name 和 arguments。
    from learning_agent.core.messages import ToolCall  # 新增代码+ToolsExecutorSplit: 导入统一 ToolCall 类型；若没有这行代码，执行器会和主循环使用不同调用对象。
except ModuleNotFoundError as error:  # 新增代码+ToolsExecutorSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages"}:  # 新增代码+ToolsExecutorSplit: 只允许目标包路径缺失时 fallback；若没有这行代码，core 内部真实 bug 会被误吞。
        raise  # 新增代码+ToolsExecutorSplit: 重新抛出真实导入错误；若没有这行代码，排查 executor 问题会很困难。
    from core.messages import ToolCall  # 新增代码+ToolsExecutorSplit: 脚本模式下导入 ToolCall；若没有这行代码，直接执行时工具执行器无法工作。


ToolHandler = Callable[[dict[str, Any]], str]  # 新增代码+ToolsExecutorSplit: 定义具体工具 handler 的统一签名；若没有这行代码，分发表类型会难以阅读。


def _builtin_tool_handlers(agent: Any) -> dict[str, ToolHandler]:  # 新增代码+ToolsExecutorSplit: 构建内置工具名到 agent 方法的分发表；若没有这行代码，execute_tool 只能继续写长 if 链。
    return {  # 新增代码+ToolsExecutorSplit: 返回新的分发表字典；若没有这行代码，执行器没有路由依据。
        "read": agent._read_atom,  # 新增代码+ToolsExecutorSplit: 四原子 read 路由到读取实现；若没有这行代码，首轮 read 会变成未知工具。
        "write": agent._write_atom,  # 新增代码+ToolsExecutorSplit: 四原子 write 路由到写入实现；若没有这行代码，首轮 write 会变成未知工具。
        "edit": agent._edit_atom,  # 新增代码+ToolsExecutorSplit: 四原子 edit 路由到定点编辑实现；若没有这行代码，首轮 edit 会变成未知工具。
        "bash": agent._bash_atom,  # 新增代码+ToolsExecutorSplit: 四原子 bash 路由到命令实现；若没有这行代码，首轮 bash 会变成未知工具。
        "read_file": agent._read_file,  # 新增代码+ToolsExecutorSplit: 兼容旧读文件工具；若没有这行代码，已加载文件能力包无法读取文件。
        "write_file": agent._write_file,  # 新增代码+ToolsExecutorSplit: 兼容旧写文件工具；若没有这行代码，已加载文件能力包无法写文件。
        "append_memory": agent._append_memory,  # 新增代码+ToolsExecutorSplit: 路由长期记忆追加工具；若没有这行代码，模型无法保存用户允许的记忆。
        "todo_read": agent._todo_read,  # 新增代码+ToolsExecutorSplit: 路由任务清单读取工具；若没有这行代码，长任务无法恢复 todo 状态。
        "todo_write": agent._todo_write,  # 新增代码+ToolsExecutorSplit: 路由任务清单写入工具；若没有这行代码，长任务无法更新 todo 状态。
        "start_background_command": agent._start_background_command,  # 新增代码+ToolsExecutorSplit: 路由后台命令启动工具；若没有这行代码，长任务无法启动服务或测试。
        "read_background_command": agent._read_background_command,  # 新增代码+ToolsExecutorSplit: 路由后台命令读取工具；若没有这行代码，长任务无法观察后台输出。
        "stop_background_command": agent._stop_background_command,  # 新增代码+ToolsExecutorSplit: 路由后台命令停止工具；若没有这行代码，后台进程可能无法收束。
        "notebook_read": agent._notebook_read,  # 新增代码+ToolsExecutorSplit: 路由 notebook 读取工具；若没有这行代码，模型无法读取 .ipynb cell 摘要。
        "notebook_edit": agent._notebook_edit,  # 新增代码+ToolsExecutorSplit: 路由 notebook 编辑工具；若没有这行代码，模型无法安全替换 cell source。
        "tool_search": agent._tool_search,  # 新增代码+ToolsExecutorSplit: 路由工具搜索和 select 工具；若没有这行代码，deferred 工具无法按需加载。
        "prompt_surface_report": agent._prompt_surface_report,  # 新增代码+ToolsExecutorSplit: 路由提示词表面报告工具；若没有这行代码，用户无法审计 prompt block。
        "token_budget_report": agent._token_budget_report,  # 新增代码+ToolsExecutorSplit: 路由 token 预算报告工具；若没有这行代码，用户无法审计上下文体积。
        "list_mcp_resources": agent._list_mcp_resources,  # 新增代码+ToolsExecutorSplit: 路由 MCP resource 列表工具；若没有这行代码，模型无法发现外部资源。
        "read_mcp_resource": agent._read_mcp_resource,  # 新增代码+ToolsExecutorSplit: 路由 MCP resource 读取工具；若没有这行代码，模型无法读取外部资源正文。
        "list_mcp_prompts": agent._list_mcp_prompts,  # 新增代码+ToolsExecutorSplit: 路由 MCP prompt 列表工具；若没有这行代码，模型无法发现外部 prompt。
        "read_mcp_prompt": agent._read_mcp_prompt,  # 新增代码+ToolsExecutorSplit: 路由 MCP prompt 读取工具；若没有这行代码，模型无法读取 prompt 正文。
        "listen_mcp_stream": agent._listen_mcp_stream,  # 新增代码+ToolsExecutorSplit: 路由 MCP stream 监听工具；若没有这行代码，模型无法读取流式外部状态。
        "skill_list": agent._skill_list,  # 新增代码+ToolsExecutorSplit: 路由本地 skill 列表工具；若没有这行代码，模型无法发现本地说明书。
        "skill_load": agent._skill_load,  # 新增代码+ToolsExecutorSplit: 路由本地 skill 加载工具；若没有这行代码，模型无法读取 skill 说明内容。
        "ask_user_question": agent._ask_user_question,  # 新增代码+ToolsExecutorSplit: 路由结构化提问工具；若没有这行代码，模型无法输出稳定澄清问题。
        "task": agent._task,  # 新增代码+ToolsExecutorSplit: 路由子 agent 委派工具；若没有这行代码，主 agent 无法拆分复杂任务。
        "task_output": agent._task_output,  # 新增代码+ToolsExecutorSplit: 路由子任务输出读取工具；若没有这行代码，主 agent 无法二次查询子任务结果。
        "task_stop": agent._task_stop,  # 新增代码+ToolsExecutorSplit: 路由子任务停止工具；若没有这行代码，主 agent 无法取消子任务。
        "task_list": agent._task_list,  # 新增代码+ToolsExecutorSplit: 路由子任务列表工具；若没有这行代码，主 agent 无法管理多个子任务。
        "task_get": agent._task_get,  # 新增代码+ToolsExecutorSplit: 路由子任务详情工具；若没有这行代码，主 agent 无法追溯任务边界。
        "task_update": agent._task_update,  # 新增代码+ToolsExecutorSplit: 路由子任务元信息更新工具；若没有这行代码，主 agent 无法为任务补标签或备注。
        "team_create": agent._team_create,  # 新增代码+ToolsExecutorSplit: 路由 peer 创建工具；若没有这行代码，教学版团队协作无法登记成员。
        "send_message": agent._send_message,  # 新增代码+ToolsExecutorSplit: 路由 peer 消息发送工具；若没有这行代码，团队消息队列无法建立。
        "list_peers": agent._list_peers,  # 新增代码+ToolsExecutorSplit: 路由 peer 列表工具；若没有这行代码，主 agent 无法查看团队成员。
        "read_peer_messages": agent._read_peer_messages,  # 新增代码+ToolsExecutorSplit: 路由 peer inbox 读取工具；若没有这行代码，主 agent 无法读取团队消息。
        "ack_peer_message": agent._ack_peer_message,  # 新增代码+ToolsExecutorSplit: 路由 peer 消息确认工具；若没有这行代码，消息状态无法标记已处理。
        "team_delete": agent._team_delete,  # 新增代码+ToolsExecutorSplit: 路由 peer 删除工具；若没有这行代码，主 agent 无法回收成员记录。
        "team_start_task": agent._team_start_task,  # 新增代码+ToolsExecutorSplit: 路由团队任务启动工具；若没有这行代码，peer 无法绑定后台子任务。
        "enter_plan_mode": agent._enter_plan_mode,  # 新增代码+ToolsExecutorSplit: 路由进入计划模式工具；若没有这行代码，模型无法保存计划状态。
        "exit_plan_mode": agent._exit_plan_mode,  # 新增代码+ToolsExecutorSplit: 路由退出计划模式工具；若没有这行代码，模型无法输出待确认计划。
        "verify_plan_execution": agent._verify_plan_execution,  # 新增代码+ToolsExecutorSplit: 路由计划执行验证工具；若没有这行代码，模型无法输出结构化验收摘要。
        "enter_worktree": agent._enter_worktree,  # 新增代码+ToolsExecutorSplit: 路由进入 worktree 隔离工具；若没有这行代码，模型无法保存隔离上下文。
        "exit_worktree": agent._exit_worktree,  # 新增代码+ToolsExecutorSplit: 路由退出 worktree 隔离工具；若没有这行代码，模型无法交接隔离工作结果。
        "lsp_symbols": agent._lsp_symbols,  # 新增代码+ToolsExecutorSplit: 路由符号读取工具；若没有这行代码，模型无法获得文件结构轮廓。
        "lsp_definition": agent._lsp_definition,  # 新增代码+ToolsExecutorSplit: 路由定义定位工具；若没有这行代码，模型无法跳到指定符号行。
        "lsp_diagnostics": agent._lsp_diagnostics,  # 新增代码+ToolsExecutorSplit: 路由语法诊断工具；若没有这行代码，模型无法先检查 SyntaxError。
        "repl": agent._repl,  # 新增代码+ToolsExecutorSplit: 路由安全批量 REPL 工具；若没有这行代码，模型无法合并多个只读查询。
        "cron_create": agent._cron_create,  # 新增代码+ToolsExecutorSplit: 路由定时任务创建工具；若没有这行代码，长期检查任务无法登记。
        "cron_list": agent._cron_list,  # 新增代码+ToolsExecutorSplit: 路由定时任务列表工具；若没有这行代码，长期任务记录无法查询。
        "cron_delete": agent._cron_delete,  # 新增代码+ToolsExecutorSplit: 路由定时任务删除工具；若没有这行代码，不需要的长期记录无法清理。
        "monitor": agent._monitor,  # 新增代码+ToolsExecutorSplit: 路由监控记录工具；若没有这行代码，监控登记、列出、删除和记录结果无法执行。
    }  # 新增代码+ToolsExecutorSplit: 分发表结束；若没有这行代码，Python 字典语法不完整。


def _guard_tool_execution(agent: Any, tool_call: ToolCall) -> str | None:  # 新增代码+ToolsExecutorSplit: 执行具体工具前统一做权限和策略守卫；若没有这行代码，守卫逻辑会留在主类大方法中。
    if agent.allowed_tool_names is not None and tool_call.name not in agent.allowed_tool_names:  # 新增代码+ToolsExecutorSplit: 执行期再次检查当前 agent 的 allowed_tools 边界；若没有这行代码，模型伪造隐藏工具名仍能绕过展示层过滤。
        return f"{tool_call.name} 失败：不在当前 agent 的 allowed_tools 范围内。"  # 新增代码+ToolsExecutorSplit: 直接拒绝越权工具调用；若没有这行代码，未授权工具可能继续写文件、跑命令或调用 MCP。
    catalog_tool = agent._find_catalog_tool(tool_call.name)  # 新增代码+ToolsExecutorSplit: 执行前从完整 catalog 查找工具元数据；若没有这行代码，blocked/needs_skill/needs_workflow 工具会绕过策略层。
    if catalog_tool is not None:  # 新增代码+ToolsExecutorSplit: 只对 catalog 中存在的工具做策略二次校验；若没有这行代码，未知工具会在访问决策属性前报错。
        decision = agent._tool_policy_decision(catalog_tool)  # 新增代码+ToolsExecutorSplit: 复用统一 ToolPolicy 决策；若没有这行代码，执行层会和工具池、select 的策略结果不一致。
        if not decision.executable and decision.state != "deferred":  # 新增代码+ToolsExecutorSplit: 非 deferred 的策略阻断必须在具体工具分发前停止；若没有这行代码，blocked/needs_skill/needs_workflow 工具仍可能进入权限弹窗。
            agent._record_observation("policy_blocked_tool", {"tool_name": tool_call.name, "state": decision.state, "reason": decision.reason})  # 新增代码+ToolsExecutorSplit: 记录策略阻断事件；若没有这行代码，审计无法解释工具为什么没执行。
            return f"{tool_call.name} 失败：policy 阻断，state={decision.state}，原因：{decision.reason}"  # 新增代码+ToolsExecutorSplit: 返回清晰策略阻断原因；若没有这行代码，模型不知道应处理 deny rule、skill gate 还是 workflow gate。
    if agent._plan_mode_blocks_tool_call(tool_call, catalog_tool):  # 新增代码+ToolsExecutorSplit: 在具体分发前拦截未确认计划期间的副作用工具；若没有这行代码，模型可能 exit_plan_mode 后马上写文件或跑命令。
        agent._record_observation("plan_mode_blocked_tool", {"tool_name": tool_call.name, "plan_state": dict(agent.plan_mode_state)})  # 新增代码+ToolsExecutorSplit: 记录计划闸门阻断事件；若没有这行代码，审计时看不到副作用为何没执行。
        return f"{tool_call.name} 失败：plan mode 阻断，当前计划尚未确认，不能执行写入、删除、命令、外部操作或其他副作用工具。"  # 新增代码+ToolsExecutorSplit: 返回清晰阻断说明；若没有这行代码，模型不知道需要等待用户确认计划。
    if agent._is_unloaded_deferred_tool(tool_call.name):  # 新增代码+ToolsExecutorSplit: 在具体工具分发之前拦截未加载的 deferred 工具；若没有这行代码，模型直接写出隐藏 MCP 工具名仍能绕过 select。
        return f'{tool_call.name} 失败：该工具尚未通过 tool_search select 加载。请先调用 tool_search，query="select:{tool_call.name}"。'  # 新增代码+ToolsExecutorSplit: 返回清楚加载指引并拒绝执行；若没有这行代码，用户看不到为什么工具被拒绝。
    return None  # 新增代码+ToolsExecutorSplit: 没有守卫阻断时返回 None；若没有这行代码，调用方无法区分阻断和放行。


def execute_tool(agent: Any, tool_call: ToolCall) -> str:  # 新增代码+ToolsExecutorSplit: 根据工具名称分发到具体工具函数；若没有这行代码，主入口仍要维护长 if 链。
    guard_message = _guard_tool_execution(agent, tool_call)  # 新增代码+ToolsExecutorSplit: 先运行 allowed_tools、policy、plan mode 和 deferred 守卫；若没有这行代码，安全边界会被分发表绕过。
    if guard_message is not None:  # 新增代码+ToolsExecutorSplit: 检查守卫是否返回阻断文本；若没有这行代码，阻断结果不会提前返回。
        return guard_message  # 新增代码+ToolsExecutorSplit: 返回守卫阻断说明；若没有这行代码，被拒绝工具仍可能继续执行。
    handler = _builtin_tool_handlers(agent).get(tool_call.name)  # 新增代码+ToolsExecutorSplit: 从内置分发表查找工具实现；若没有这行代码，内置工具无法分发。
    if handler is not None:  # 新增代码+ToolsExecutorSplit: 命中内置工具时直接执行；若没有这行代码，找到 handler 后仍会落到未知工具。
        return handler(tool_call.arguments)  # 新增代码+ToolsExecutorSplit: 把模型参数传给具体工具实现；若没有这行代码，内置工具不会真正运行。
    if tool_call.name.startswith("mcp__") and not agent.mcp_tools_enabled:  # 新增代码+ToolsExecutorSplit: MCP 被拒绝或启动失败时拦截所有 MCP 前缀工具；若没有这行代码，旧 registry route 可能绕过启动权限继续调用。
        detail = agent.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+ToolsExecutorSplit: 选择最清楚的不可用原因；若没有这行代码，返回信息会缺少排查线索。
        return f"MCP 工具不可用：{detail}"  # 新增代码+ToolsExecutorSplit: 返回可读不可用结果给模型；若没有这行代码，模型会把禁用 MCP 误解为未知工具。
    if agent.mcp_tool_registry.has_tool(tool_call.name):  # 新增代码+ToolsExecutorSplit: 内置工具优先后再检查 MCP 工具名；若没有这行代码，模型选择 MCP 工具时会被当作未知工具。
        return agent._execute_mcp_tool(tool_call)  # 新增代码+ToolsExecutorSplit: 把 MCP 工具调用交给专门方法处理权限和异常；若没有这行代码，外部工具调用缺少权限保护和错误兜底。
    return f"未知工具：{tool_call.name}"  # 新增代码+ToolsExecutorSplit: 未知工具返回错误给模型；若没有这行代码，模型无法知道工具名写错。
