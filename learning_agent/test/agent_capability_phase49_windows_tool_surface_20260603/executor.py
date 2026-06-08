"""工具执行分发器。"""  # 新增代码+ToolsExecutorSplit: 把 _execute_tool 的守卫和分发表从主入口拆出；若没有这个文件，执行层问题仍要翻 LearningAgent 大类。

from __future__ import annotations  # 新增代码+ToolsExecutorSplit: 延迟解析类型注解；若没有这行代码，脚本模式下导入顺序会更脆弱。

from typing import Any, Callable  # 新增代码+ToolsExecutorSplit: 执行器需要通用 agent 对象和 handler 回调类型；若没有这行代码，类型边界不清楚。

try:  # 新增代码+ToolsExecutorSplit: 包运行模式下导入工具调用数据结构；若没有这行代码，执行器无法读取 tool_call.name 和 arguments。
    from learning_agent.core.messages import ToolCall  # 新增代码+ToolsExecutorSplit: 导入统一 ToolCall 类型；若没有这行代码，执行器会和主循环使用不同调用对象。
except ModuleNotFoundError as error:  # 新增代码+ToolsExecutorSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages"}:  # 新增代码+ToolsExecutorSplit: 只允许目标包路径缺失时 fallback；若没有这行代码，core 内部真实 bug 会被误吞。
        raise  # 新增代码+ToolsExecutorSplit: 重新抛出真实导入错误；若没有这行代码，排查 executor 问题会很困难。
    from core.messages import ToolCall  # 新增代码+ToolsExecutorSplit: 脚本模式下导入 ToolCall；若没有这行代码，直接执行时工具执行器无法工作。

try:  # 新增代码+Stage15E: 包运行模式下导入工具 hook 管理器和事件；若没有这行代码，executor v2 无法运行 pre/post/denied/error hook。
    from learning_agent.tools.hooks import ToolHookEvent, ToolHookManager  # 新增代码+Stage15E: 导入 hook 事件和管理器；若没有这行代码，执行器只能记录文本而不能运行扩展点。
except ModuleNotFoundError as error:  # 新增代码+Stage15E: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.hooks"}:  # 新增代码+Stage15E: 只允许目标包路径缺失时 fallback；若没有这行代码，hook 内部真实错误会被误吞。
        raise  # 新增代码+Stage15E: 重新抛出真实导入错误；若没有这行代码，排查 hook 问题会很困难。
    from tools.hooks import ToolHookEvent, ToolHookManager  # 新增代码+Stage15E: 脚本模式下从同目录 tools 包导入 hook 类型；若没有这行代码，直接执行 learning_agent.py 时 hook 不可用。

try:  # 新增代码+Stage15E: 包运行模式下导入统一权限决策函数；若没有这行代码，executor v2 无法产生结构化 permission_decided 事件。
    from learning_agent.tools.permissions import ToolPermissionDecision, decide_tool_permission  # 新增代码+Stage15E: 导入权限决策对象和 helper；若没有这行代码，执行器无法统一判断 allow/deny/ask。
except ModuleNotFoundError as error:  # 新增代码+Stage15E: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.permissions"}:  # 新增代码+Stage15E: 只允许目标包路径缺失时 fallback；若没有这行代码，permissions 内部真实错误会被误吞。
        raise  # 新增代码+Stage15E: 重新抛出真实导入错误；若没有这行代码，排查权限模块问题会很困难。
    from tools.permissions import ToolPermissionDecision, decide_tool_permission  # 新增代码+Stage15E: 脚本模式下导入权限 helper；若没有这行代码，直接执行时 executor v2 权限层不可用。


ToolHandler = Callable[[dict[str, Any]], str]  # 新增代码+ToolsExecutorSplit: 定义具体工具 handler 的统一签名；若没有这行代码，分发表类型会难以阅读。


def _record_executor_observation(agent: Any, kind: str, payload: dict[str, Any]) -> None:  # 新增代码+Stage15E: 安全写入执行器观察事件；若没有这行代码，fake agent 或老调用方缺少 _record_observation 时会崩溃。
    recorder = getattr(agent, "_record_observation", None)  # 新增代码+Stage15E: 动态读取观察记录函数；若没有这行代码，执行器会强依赖 LearningAgent 具体实现。
    if callable(recorder):  # 新增代码+Stage15E: 只有真实可调用时才记录；若没有这行代码，None 或非函数属性会被误调用。
        recorder(kind, payload)  # 新增代码+Stage15E: 写入结构化 observation；若没有这行代码，权限和 hook 生命周期不可审计。


def _get_tool_hook_manager(agent: Any) -> ToolHookManager | None:  # 新增代码+Stage15E: 读取 agent 上挂载的 hook 管理器；若没有这行代码，执行器无法支持可选 hook。
    manager = getattr(agent, "tool_hooks", None)  # 新增代码+Stage15E: 从 agent 取 hook 管理器；若没有这行代码，调用方无法注入自定义 hook。
    return manager if isinstance(manager, ToolHookManager) else None  # 新增代码+Stage15E: 只接受正确类型的管理器；若没有这行代码，错误对象可能在 run_hooks 处崩溃。


def _run_tool_hooks(agent: Any, hook_name: str, event: ToolHookEvent) -> str | None:  # 新增代码+Stage15E: 统一记录并运行某个阶段的 hook；若没有这行代码，pre/post/denied/error 会各写各的异常处理。
    _record_executor_observation(agent, hook_name, event.to_payload())  # 新增代码+Stage15E: 先记录 hook 阶段事件；若没有这行代码，即使没有注册 hook 也看不到生命周期节点。
    manager = _get_tool_hook_manager(agent)  # 新增代码+Stage15E: 获取可选 hook 管理器；若没有这行代码，注册的 hook 不会执行。
    if manager is None:  # 新增代码+Stage15E: 没有 hook 管理器时正常跳过；若没有这行代码，默认 agent 会因为未注册 hook 而失败。
        return None  # 新增代码+Stage15E: 无 hook 错误时返回 None；若没有这行代码，调用方无法区分正常和失败。
    errors = manager.run_hooks(hook_name, event)  # 新增代码+Stage15E: 运行该阶段全部 hook；若没有这行代码，扩展点只记录不执行。
    if not errors:  # 新增代码+Stage15E: 没有 hook 错误时继续执行；若没有这行代码，正常 hook 会被误判失败。
        return None  # 新增代码+Stage15E: 返回 None 表示无错误；若没有这行代码，调用方会收到空错误文本。
    error_text = "; ".join(errors)  # 新增代码+Stage15E: 合并多个 hook 错误；若没有这行代码，多个失败原因无法展示。
    _record_executor_observation(agent, "tool_error", {"tool_name": event.tool_name, "call_id": event.call_id, "hook_name": hook_name, "error": error_text})  # 新增代码+Stage15E: 把 hook 异常转成工具错误事件；若没有这行代码，hook 报错缺少审计证据。
    return f"{event.tool_name} tool hook 失败：{hook_name}: {error_text}"  # 新增代码+Stage15E: 返回可读错误给模型；若没有这行代码，hook 异常可能变成裸 Python 错误。


def _record_permission_decision(agent: Any, tool_call: ToolCall, decision: ToolPermissionDecision) -> None:  # 新增代码+Stage15E: 统一记录权限决策事件；若没有这行代码，权限判断缺少结构化审计。
    _record_executor_observation(agent, "permission_decided", {"tool_name": tool_call.name, "call_id": tool_call.call_id, "status": decision.status, "allowed": decision.allowed, "reason": decision.reason})  # 新增代码+Stage15E: 写入 allow/deny/ask/auto_allow 决策；若没有这行代码，后续无法复盘工具为何执行或拒绝。


def _permission_denied_message(agent: Any, tool_call: ToolCall, decision: ToolPermissionDecision) -> str:  # 新增代码+Stage15E: 统一处理权限拒绝事件和返回文本；若没有这行代码，每个拒绝分支会格式不一致。
    event = ToolHookEvent(tool_name=tool_call.name, call_id=tool_call.call_id, arguments=tool_call.arguments, permission_status=decision.status, error_text=decision.reason)  # 新增代码+Stage15E: 构造权限拒绝 hook 事件；若没有这行代码，permission_denied hook 看不到上下文。
    _run_tool_hooks(agent, "permission_denied", event)  # 新增代码+Stage15E: 记录并运行拒绝 hook；若没有这行代码，权限拒绝无法触发审计或 UI 扩展。
    return f"{tool_call.name} 权限拒绝：{decision.reason}"  # 新增代码+Stage15E: 返回清楚拒绝说明；若没有这行代码，模型不知道工具没有执行的原因。


def _dispatch_tool_call(agent: Any, tool_call: ToolCall) -> str:  # 新增代码+Stage15E: 把具体工具分发从 executor v2 生命周期中拆出；若没有这行代码，hook 包裹逻辑和分发表会混在一起。
    handler = _builtin_tool_handlers(agent).get(tool_call.name)  # 新增代码+Stage15E: 从内置分发表查找工具实现；若没有这行代码，内置工具无法分发。
    if handler is not None:  # 新增代码+Stage15E: 命中内置工具时执行；若没有这行代码，找到 handler 后仍会落到未知工具。
        return handler(tool_call.arguments)  # 新增代码+Stage15E: 把模型参数传给具体工具实现；若没有这行代码，内置工具不会真正运行。
    if tool_call.name.startswith("mcp__") and not agent.mcp_tools_enabled:  # 新增代码+Stage15E: MCP 被拒绝或启动失败时拦截所有 MCP 前缀工具；若没有这行代码，旧 registry route 可能绕过启动权限继续调用。
        detail = agent.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+Stage15E: 选择最清楚的不可用原因；若没有这行代码，返回信息会缺少排查线索。
        return f"MCP 工具不可用：{detail}"  # 新增代码+Stage15E: 返回可读不可用结果给模型；若没有这行代码，模型会把禁用 MCP 误解为未知工具。
    if agent.mcp_tool_registry.has_tool(tool_call.name):  # 新增代码+Stage15E: 内置工具优先后再检查 MCP 工具名；若没有这行代码，模型选择 MCP 工具时会被当作未知工具。
        return agent._execute_mcp_tool(tool_call)  # 新增代码+Stage15E: 把 MCP 工具调用交给专门方法处理权限和异常；若没有这行代码，外部工具调用缺少权限保护和错误兜底。
    _record_executor_observation(agent, "tool_error", {"tool_name": tool_call.name, "call_id": tool_call.call_id, "error": "unknown tool"})  # 新增代码+Stage15E: 记录未知工具错误事件；若没有这行代码，未知工具失败不可审计。
    return f"未知工具：{tool_call.name}"  # 新增代码+Stage15E: 未知工具返回错误给模型；若没有这行代码，模型无法知道工具名写错。


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
        "status_snapshot": agent._status_snapshot,  # 新增代码+StatusTools: 路由统一状态快照工具；若没有这行代码，schema 中的 status_snapshot 会变成未知工具。
        "task_status": agent._task_status,  # 新增代码+StatusTools: 路由任务状态查询工具；若没有这行代码，模型无法通过工具查看持久任务。
        "session_list": agent._session_list,  # 新增代码+StatusTools: 路由 session 列表工具；若没有这行代码，模型无法发现可恢复会话。
        "session_resume": agent._session_resume,  # 新增代码+StatusTools: 路由 session 恢复工具；若没有这行代码，模型无法审计恢复上下文。
        "compact_status": agent._compact_status,  # 新增代码+StatusTools: 路由 compact 状态工具；若没有这行代码，模型无法查看压缩边界状态。
        "event_tail": agent._event_tail,  # 新增代码+StatusTools: 路由状态事件尾部工具；若没有这行代码，模型无法增量观察运行事件。
        "resume_report": agent._resume_report,  # 新增代码+StatusToolsV2: 路由精简恢复审计报告工具；若没有这行代码，schema 中的 resume_report 会变成未知工具。
        "run_status": agent._run_status,  # 新增代码+StatusToolsV2: 路由 run 状态工具；若没有这行代码，模型无法直接查询阶段运行状态。
        "health_status": agent._health_status,  # 新增代码+StatusToolsV2: 路由健康状态工具；若没有这行代码，模型无法自查 warning/verifier 风险。
        "computer_status": agent._computer_status,  # 新增代码+OSComputerUse: 路由 OS Computer Use 状态工具；若没有这行代码，schema 中的 computer_status 会变成未知工具。
        "computer_observe": agent._computer_observe,  # 新增代码+Phase27ComputerUse: 路由 OS Computer Use 只读观察工具；如果没有这行代码，schema 中的 computer_observe 会变成未知工具。
        "computer_action": agent._computer_action,  # 新增代码+OSComputerUse: 路由 OS Computer Use 动作工具；若没有这行代码，schema 中的 computer_action 会变成未知工具。
        "computer_use": agent._computer_use_compat,  # 新增代码+Phase49ComputerUseToolSurface: 路由下划线统一兼容工具；如果没有这行代码，computer_use schema 会变成未知工具。
        "computer-use": agent._computer_use_compat,  # 新增代码+Phase49ComputerUseToolSurface: 路由 ClaudeCode 风格连字符兼容工具；如果没有这行代码，computer-use schema 会变成未知工具。
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
    catalog_tool = agent._find_catalog_tool(tool_call.name)  # 新增代码+Stage15E: 读取工具目录元数据供权限层使用；若没有这行代码，permission_mode 无法影响执行器。
    permission_decision = decide_tool_permission(agent, tool_call, catalog_tool)  # 新增代码+Stage15E: 生成统一权限决策；若没有这行代码，allow/deny/ask/auto_allow 不会进入执行流程。
    _record_permission_decision(agent, tool_call, permission_decision)  # 新增代码+Stage15E: 记录权限决策 observation；若没有这行代码，审计看不到工具为什么被允许或拒绝。
    if not permission_decision.allowed:  # 新增代码+Stage15E: 权限拒绝时禁止继续执行；若没有这行代码，deny 决策可能只被记录但仍执行工具。
        return _permission_denied_message(agent, tool_call, permission_decision)  # 新增代码+Stage15E: 返回拒绝文本并运行拒绝 hook；若没有这行代码，权限拒绝没有统一出口。
    pre_event = ToolHookEvent(tool_name=tool_call.name, call_id=tool_call.call_id, arguments=tool_call.arguments, permission_status=permission_decision.status)  # 新增代码+Stage15E: 构造执行前 hook 事件；若没有这行代码，pre_tool_use hook 没有上下文。
    pre_hook_error = _run_tool_hooks(agent, "pre_tool_use", pre_event)  # 新增代码+Stage15E: 运行执行前 hook；若没有这行代码，工具执行前无法插入审计和拦截点。
    if pre_hook_error is not None:  # 新增代码+Stage15E: pre hook 报错时停止执行工具；若没有这行代码，坏 hook 后工具仍可能继续产生副作用。
        return pre_hook_error  # 新增代码+Stage15E: 返回 hook 错误给模型；若没有这行代码，调用方拿不到可恢复反馈。
    try:  # 新增代码+Stage15E: 捕获具体工具执行异常；若没有这行代码，单个工具异常会中断整个 agent。
        result_text = _dispatch_tool_call(agent, tool_call)  # 新增代码+Stage15E: 调用真正的工具分发；若没有这行代码，hook 生命周期没有实际工具执行。
    except Exception as error:  # 新增代码+Stage15E: 把工具异常转换成可读文本和事件；若没有这行代码，用户会看到裸堆栈或 agent 直接崩溃。
        error_text = str(error)  # 新增代码+Stage15E: 保存错误摘要；若没有这行代码，后续事件和返回文本没有具体原因。
        error_event = ToolHookEvent(tool_name=tool_call.name, call_id=tool_call.call_id, arguments=tool_call.arguments, error_text=error_text, permission_status=permission_decision.status)  # 新增代码+Stage15E: 构造工具错误 hook 事件；若没有这行代码，tool_error hook 看不到失败上下文。
        _run_tool_hooks(agent, "tool_error", error_event)  # 新增代码+Stage15E: 记录并运行工具错误 hook；若没有这行代码，异常缺少统一审计点。
        return f"{tool_call.name} 工具执行失败：{error_text}"  # 新增代码+Stage15E: 返回可读执行失败文本；若没有这行代码，模型无法根据错误继续恢复。
    post_event = ToolHookEvent(tool_name=tool_call.name, call_id=tool_call.call_id, arguments=tool_call.arguments, result_text=result_text, permission_status=permission_decision.status)  # 新增代码+Stage15E: 构造执行后 hook 事件；若没有这行代码，post_tool_use hook 拿不到结果。
    post_hook_error = _run_tool_hooks(agent, "post_tool_use", post_event)  # 新增代码+Stage15E: 运行执行后 hook；若没有这行代码，工具成功后无法插入审计和结果处理点。
    if post_hook_error is not None:  # 新增代码+Stage15E: post hook 报错时返回可恢复错误；若没有这行代码，hook 异常可能被吞掉。
        return post_hook_error  # 新增代码+Stage15E: 返回 hook 错误文本；若没有这行代码，模型不知道后处理失败。
    return result_text  # 新增代码+Stage15E: 返回真实工具结果；若没有这行代码，工具成功输出无法回填给模型。
