"""计划模式、计划验收和轻量 worktree 状态工具的真实运行时实现。"""  # 新增代码+AgentPyPhaseEPlanRuntime: 把 plan/worktree 能力从 agent.py 拆到 core 层；若没有这个文件，主 agent 仍会承载计划闸门和隔离状态细节。

from __future__ import annotations  # 新增代码+AgentPyPhaseEPlanRuntime: 延迟解析类型注解；若没有这行代码，脚本模式下复杂注解更容易受导入顺序影响。

import time  # 新增代码+AgentPyPhaseEPlanRuntime: 计划确认需要记录确认时间；若没有这行代码，confirmed_at 无法生成。
from typing import Any  # 新增代码+AgentPyPhaseEPlanRuntime: 用 Any 表示传入 agent、tool_call 和 catalog_tool；若没有这行代码，本模块会为了类型注解反向导入 agent.py。

try:  # 新增代码+AgentPyPhaseEPlanRuntime: 包运行模式下导入运行观察 helper；若没有这行代码，python -m 运行时无法记录 plan_confirmed 事件。
    import learning_agent.core.run_helpers as run_helpers_from_core  # 新增代码+AgentPyPhaseEPlanRuntime: 导入 observation 记录 helper；若没有这行代码，计划确认事件无法进入审计流。
    import learning_agent.tools.atom_tools as atom_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL6: 直接导入 atom_tools 的路径安全解析；若没有这行代码，删除 旧路径包装 后 worktree 路径边界会断开。
except ModuleNotFoundError as error:  # 新增代码+AgentPyPhaseEPlanRuntime: 捕获 start_oauth_agent.bat 直接脚本模式下的包路径差异；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.run_helpers", "learning_agent.tools", "learning_agent.tools.atom_tools"}:  # 修改代码+AgentPyCompatWrapperRemovalL6: 允许 atom_tools 在脚本模式 fallback；若没有这行代码，bat 入口会把路径差异误判为真实导入错误。
        raise  # 新增代码+AgentPyPhaseEPlanRuntime: 重新抛出真正的导入错误；若没有这行代码，排查 plan runtime 问题会看不到根因。
    import core.run_helpers as run_helpers_from_core  # 新增代码+AgentPyPhaseEPlanRuntime: 脚本模式下导入 observation helper；若没有这行代码，bat 入口确认计划后无法记录事件。
    import tools.atom_tools as atom_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL6: 脚本模式下导入同一个路径安全模块；若没有这行代码，worktree 工具会找不到 workspace 边界实现。


def maybe_confirm_plan_from_user_input(agent: Any, user_input: str) -> None:  # 新增代码+AgentPyPhaseEPlanRuntime: 函数段开始，让用户自然语言确认计划后解除副作用闸门；若没有这段函数，计划确认无法从下一轮用户输入进入执行状态。
    if not agent.plan_mode_state.get("awaiting_confirmation"):  # 新增代码+AgentPyPhaseEPlanRuntime: 只有等待确认时才解析确认文本；若没有这行代码，普通“确认一下”会误改计划状态。
        return  # 新增代码+AgentPyPhaseEPlanRuntime: 非等待确认状态直接退出；若没有这行代码，后续会做无意义字符串匹配。
    lowered_input = user_input.lower()  # 新增代码+AgentPyPhaseEPlanRuntime: 统一英文大小写以匹配 confirm/approved；若没有这行代码，英文确认大小写会漏判。
    confirm_keywords = ["确认", "同意", "按计划", "继续执行", "开始执行", "执行吧", "confirm", "approved", "go ahead"]  # 新增代码+AgentPyPhaseEPlanRuntime: 定义明确确认词；若没有这行代码，计划闸门无法知道哪些用户输入算授权。
    if not any(keyword in lowered_input for keyword in confirm_keywords):  # 新增代码+AgentPyPhaseEPlanRuntime: 没有确认词时继续保持等待；若没有这行代码，任何下一轮输入都可能错误解锁副作用工具。
        return  # 新增代码+AgentPyPhaseEPlanRuntime: 用户还没确认就直接退出；若没有这行代码，后续会错误修改状态。
    agent.plan_mode_state["awaiting_confirmation"] = False  # 新增代码+AgentPyPhaseEPlanRuntime: 取消等待确认标记；若没有这行代码，副作用工具仍会被计划闸门拦截。
    agent.plan_mode_state["confirmed"] = True  # 新增代码+AgentPyPhaseEPlanRuntime: 记录该计划已被用户确认；若没有这行代码，审计时无法区分未计划和已确认计划。
    agent.plan_mode_state["confirmed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+AgentPyPhaseEPlanRuntime: 保存确认时间；若没有这行代码，后续日志无法说明确认发生在何时。
    run_helpers_from_core.record_observation(agent, "plan_confirmed", {"user_input": user_input[:500]})  # 新增代码+AgentPyPhaseEPlanRuntime: 把确认事件写入结构化观察；若没有这行代码，Phase 6 审计看不到计划解锁依据。
# 新增代码+AgentPyPhaseEPlanRuntime: 函数段结束，maybe_confirm_plan_from_user_input 到此结束；若没有这个边界说明，用户不容易看出计划确认逻辑已迁出 agent.py。


def plan_mode_blocks_tool_call(agent: Any, tool_call: Any, catalog_tool: Any | None) -> bool:  # 新增代码+AgentPyPhaseEPlanRuntime: 函数段开始，判断当前工具调用是否被计划模式副作用闸门拦截；若没有这段函数，执行入口会塞满难维护的条件判断。
    if not agent.plan_mode_state.get("active") and not agent.plan_mode_state.get("awaiting_confirmation"):  # 新增代码+AgentPyPhaseEPlanRuntime: 只有计划中或等待确认时才启用闸门；若没有这行代码，普通任务会被错误拦截。
        return False  # 新增代码+AgentPyPhaseEPlanRuntime: 不在计划闸门状态时直接放行；若没有这行代码，后续副作用判断会误伤正常流程。
    if agent.plan_mode_state.get("confirmed"):  # 新增代码+AgentPyPhaseEPlanRuntime: 用户确认过计划后允许执行；若没有这行代码，确认状态不会真正解锁工具。
        return False  # 新增代码+AgentPyPhaseEPlanRuntime: 已确认计划不再阻断；若没有这行代码，后续实现阶段无法运行工具。
    if tool_call.name in plan_mode_safe_tool_names():  # 新增代码+AgentPyPhaseEPlanRuntime: 计划相关和只读观察工具允许继续使用；若没有这行代码，模型无法读文件或输出计划。
        return False  # 新增代码+AgentPyPhaseEPlanRuntime: 安全工具直接放行；若没有这行代码，计划模式会把自身工具也锁死。
    return tool_call_has_side_effect(tool_call, catalog_tool)  # 新增代码+AgentPyPhaseEPlanRuntime: 只拦截真正可能有副作用的工具；若没有这行代码，计划模式会过度阻止无害查询。
# 新增代码+AgentPyPhaseEPlanRuntime: 函数段结束，plan_mode_blocks_tool_call 到此结束；若没有这个边界说明，用户不容易看出计划闸门逻辑已迁出 agent.py。


def plan_mode_safe_tool_names() -> set[str]:  # 新增代码+AgentPyPhaseEPlanRuntime: 函数段开始，返回计划模式期间允许的内置工具名；若没有这段函数，安全例外没有统一来源。
    return {  # 新增代码+AgentPyPhaseEPlanRuntime: 用 set 保存可快速匹配的工具名；若没有这行代码，后续判断会更慢更乱。
        "read_file",  # 新增代码+AgentPyPhaseEPlanRuntime: 计划阶段必须允许读取文件证据；若没有这项，模型无法先读后计划。
        "todo_read",  # 新增代码+AgentPyPhaseEPlanRuntime: 读取任务清单没有副作用；若没有这项，模型无法恢复当前计划上下文。
        "tool_search",  # 新增代码+AgentPyPhaseEPlanRuntime: 搜索工具目录没有副作用；若没有这项，模型无法发现只读或计划工具。
        "list_mcp_resources",  # 新增代码+AgentPyPhaseEPlanRuntime: 列外部资源是只读发现动作；若没有这项，MCP 资源计划无法展开。
        "read_mcp_resource",  # 新增代码+AgentPyPhaseEPlanRuntime: 读取 MCP resource 用于收集证据；若没有这项，计划前上下文会不足。
        "list_mcp_prompts",  # 新增代码+AgentPyPhaseEPlanRuntime: 列 MCP prompt 是只读发现动作；若没有这项，模型无法发现可用 prompt。
        "read_mcp_prompt",  # 新增代码+AgentPyPhaseEPlanRuntime: 读取 MCP prompt 用于规划；若没有这项，prompt workflow 无法先审阅。
        "listen_mcp_stream",  # 新增代码+AgentPyPhaseEPlanRuntime: 监听 stream 用于观察外部状态；若没有这项，长任务诊断信息可能拿不到。
        "skill_list",  # 新增代码+AgentPyPhaseEPlanRuntime: 列 skill 是只读发现动作；若没有这项，模型无法按流程加载说明。
        "skill_load",  # 新增代码+AgentPyPhaseEPlanRuntime: 加载 skill 只读取说明书且会更新策略上下文；若没有这项，skill gate 无法在计划阶段准备好。
        "ask_user_question",  # 新增代码+AgentPyPhaseEPlanRuntime: 澄清问题没有本地副作用；若没有这项，模型无法在计划阶段向用户补信息。
        "enter_plan_mode",  # 新增代码+AgentPyPhaseEPlanRuntime: 允许重复说明计划入口状态；若没有这项，计划模式工具会被自己锁住。
        "exit_plan_mode",  # 新增代码+AgentPyPhaseEPlanRuntime: 允许输出待确认计划；若没有这项，模型无法结束计划阶段。
        "verify_plan_execution",  # 新增代码+AgentPyPhaseEPlanRuntime: 验证计划是审计动作；若没有这项，模型无法收尾计划执行证据。
        "lsp_symbols",  # 新增代码+AgentPyPhaseEPlanRuntime: 符号读取是只读代码理解；若没有这项，计划前无法快速理解文件结构。
        "lsp_definition",  # 新增代码+AgentPyPhaseEPlanRuntime: 定义定位是只读代码理解；若没有这项，计划前无法定位修改点。
        "lsp_diagnostics",  # 新增代码+AgentPyPhaseEPlanRuntime: 语法诊断是只读检查；若没有这项，计划前无法确认当前错误。
        "read_background_command",  # 新增代码+AgentPyPhaseEPlanRuntime: 读取后台输出是观察动作；若没有这项，模型无法检查已有长任务状态。
        "task_output",  # 新增代码+AgentPyPhaseEPlanRuntime: 读取子任务输出是观察动作；若没有这项，模型无法汇总已有子任务证据。
        "task_list",  # 新增代码+AgentPyPhaseEPlanRuntime: 列子任务是观察动作；若没有这项，模型无法查看当前任务状态。
        "task_get",  # 新增代码+AgentPyPhaseEPlanRuntime: 读取子任务详情是观察动作；若没有这项，模型无法审计子任务边界。
    }  # 新增代码+AgentPyPhaseEPlanRuntime: 安全工具集合结束；若没有这行代码，Python set 语法不完整。
# 新增代码+AgentPyPhaseEPlanRuntime: 函数段结束，plan_mode_safe_tool_names 到此结束；若没有这个边界说明，用户不容易看出安全工具集合已迁出 agent.py。


def tool_call_has_side_effect(tool_call: Any, catalog_tool: Any | None) -> bool:  # 新增代码+AgentPyPhaseEPlanRuntime: 函数段开始，统一判断工具是否可能改变文件、进程、浏览器或外部系统；若没有这段函数，副作用判断会在多个分支重复。
    side_effect_builtin_tools = {  # 新增代码+AgentPyPhaseEPlanRuntime: 列出已知内置副作用工具；若没有这行代码，写文件和命令执行无法被计划闸门识别。
        "write",  # 新增代码+AgentPyPhaseEPlanRuntime: write 会修改工作区文件；若没有这项，未确认计划仍可能通过四原子工具写文件。
        "edit",  # 新增代码+AgentPyPhaseEPlanRuntime: edit 会修改工作区文件；若没有这项，未确认计划仍可能通过四原子工具做定点替换。
        "bash",  # 新增代码+AgentPyPhaseEPlanRuntime: bash 会执行本机命令；若没有这项，未确认计划仍可能通过四原子工具运行副作用命令。
        "write_file",  # 新增代码+AgentPyPhaseEPlanRuntime: 写文件会修改工作区；若没有这项，未确认计划仍可能写入文件。
        "append_memory",  # 新增代码+AgentPyPhaseEPlanRuntime: 追加长期记忆会修改持久状态；若没有这项，未确认计划可能污染记忆。
        "todo_write",  # 新增代码+AgentPyPhaseEPlanRuntime: 写任务清单会修改状态文件；若没有这项，未确认计划可能改动任务状态。
        "start_background_command",  # 新增代码+AgentPyPhaseEPlanRuntime: 启动后台命令会产生进程副作用；若没有这项，未确认计划可能运行命令。
        "stop_background_command",  # 新增代码+AgentPyPhaseEPlanRuntime: 停止后台命令会改变进程状态；若没有这项，未确认计划可能终止任务。
        "notebook_edit",  # 新增代码+AgentPyPhaseEPlanRuntime: 编辑 notebook 会修改文件；若没有这项，未确认计划可能改 notebook。
        "task",  # 新增代码+AgentPyPhaseEPlanRuntime: 启动子 agent 会产生额外执行流程；若没有这项，未确认计划可能委派副作用。
        "task_stop",  # 新增代码+AgentPyPhaseEPlanRuntime: 停止子任务会改变任务生命周期；若没有这项，未确认计划可能终止子 agent。
        "task_update",  # 新增代码+AgentPyPhaseEPlanRuntime: 更新任务元信息会修改管理状态；若没有这项，未确认计划可能改任务记录。
        "team_create",  # 新增代码+AgentPyPhaseEPlanRuntime: 创建 peer 会修改团队状态；若没有这项，未确认计划可能改变协作结构。
        "send_message",  # 新增代码+AgentPyPhaseEPlanRuntime: 发送消息会修改 inbox；若没有这项，未确认计划可能产生协作消息。
        "ack_peer_message",  # 新增代码+AgentPyPhaseEPlanRuntime: 确认消息会改变消息状态；若没有这项，未确认计划可能误标已处理。
        "team_delete",  # 新增代码+AgentPyPhaseEPlanRuntime: 删除 peer 会修改团队状态；若没有这项，未确认计划可能删除协作记录。
        "team_start_task",  # 新增代码+AgentPyPhaseEPlanRuntime: 启动团队任务会产生子任务副作用；若没有这项，未确认计划可能后台执行。
        "enter_worktree",  # 新增代码+AgentPyPhaseEPlanRuntime: 进入隔离上下文改变执行边界状态；若没有这项，未确认计划可能切换工作上下文。
        "exit_worktree",  # 新增代码+AgentPyPhaseEPlanRuntime: 退出隔离上下文改变执行边界状态；若没有这项，未确认计划可能关闭隔离状态。
        "repl",  # 新增代码+AgentPyPhaseEPlanRuntime: REPL 会批量执行工具，需要在计划确认后才允许；若没有这项，未确认计划可能通过 REPL 绕过闸门。
        "cron_create",  # 新增代码+AgentPyPhaseEPlanRuntime: 创建定时记录会修改状态；若没有这项，未确认计划可能登记长期任务。
        "cron_delete",  # 新增代码+AgentPyPhaseEPlanRuntime: 删除定时记录会修改状态；若没有这项，未确认计划可能删记录。
        "monitor",  # 新增代码+AgentPyPhaseEPlanRuntime: 监控工具可能登记、删除或写结果；若没有这项，未确认计划可能改变监控状态。
    }  # 新增代码+AgentPyPhaseEPlanRuntime: 内置副作用集合结束；若没有这行代码，Python set 语法不完整。
    if tool_call.name in side_effect_builtin_tools:  # 新增代码+AgentPyPhaseEPlanRuntime: 命中已知内置副作用工具就拦截；若没有这行代码，内置写入命令无法被计划保护。
        return True  # 新增代码+AgentPyPhaseEPlanRuntime: 返回有副作用；若没有这行代码，调用方无法拦截。
    if catalog_tool is None:  # 新增代码+AgentPyPhaseEPlanRuntime: 未知工具交给后续未知工具分支处理；若没有这行代码，访问 catalog 元数据会报错。
        return False  # 新增代码+AgentPyPhaseEPlanRuntime: 未知工具暂不在计划闸门判定里处理；若没有这行代码，未知工具可能被错误分类。
    if catalog_tool.source == "mcp" and not catalog_tool.is_read_only:  # 新增代码+AgentPyPhaseEPlanRuntime: MCP 非只读工具默认视为外部副作用；若没有这行代码，外部写入、浏览器和网络操作可能绕过计划确认。
        return True  # 新增代码+AgentPyPhaseEPlanRuntime: 返回有副作用；若没有这行代码，外部工具会继续执行。
    return catalog_tool.is_destructive or catalog_tool.is_open_world  # 新增代码+AgentPyPhaseEPlanRuntime: 破坏性或开放世界工具也按副作用处理；若没有这行代码，高风险 MCP metadata 不会影响计划闸门。
# 新增代码+AgentPyPhaseEPlanRuntime: 函数段结束，tool_call_has_side_effect 到此结束；若没有这个边界说明，用户不容易看出副作用判断已迁出 agent.py。


def enter_worktree(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseEPlanRuntime: 函数段开始，执行进入轻量 worktree 隔离状态工具；若没有这段函数，agent 只有工具 schema 没有实际状态切换。
    if agent.worktree_state.get("active"):  # 新增代码+AgentPyPhaseEPlanRuntime: 检查是否已经处于隔离状态；若没有这行代码，模型可能嵌套进入多个隔离上下文导致边界混乱。
        return "enter_worktree 失败：当前已经处于工作区隔离状态，请先调用 exit_worktree 退出。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回清楚的重复进入错误；若没有这行代码，模型难以修正调用顺序。
    reason = str(arguments.get("reason", "") or "").strip()  # 新增代码+AgentPyPhaseEPlanRuntime: 读取并清理进入隔离状态原因；若没有这行代码，用户看不到为什么需要隔离。
    goal = str(arguments.get("goal", "") or "").strip()  # 新增代码+AgentPyPhaseEPlanRuntime: 读取并清理隔离工作目标；若没有这行代码，后续退出时缺少核对方向。
    raw_worktree_path = str(arguments.get("worktree_path", "") or "").strip()  # 新增代码+AgentPyPhaseEPlanRuntime: 读取并清理隔离目录路径；若没有这行代码，工具无法知道隔离上下文指向哪里。
    if not reason:  # 新增代码+AgentPyPhaseEPlanRuntime: 检查 reason 是否为空；若没有这行代码，模型可能用空原因进入隔离状态。
        return "enter_worktree 失败：缺少非空 reason 参数。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回清楚缺参错误；若没有这行代码，模型难以修正进入隔离状态参数。
    if not goal:  # 新增代码+AgentPyPhaseEPlanRuntime: 检查 goal 是否为空；若没有这行代码，模型可能在没有目标时进入隔离状态。
        return "enter_worktree 失败：缺少非空 goal 参数。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回清楚缺参错误；若没有这行代码，模型难以修正进入隔离状态参数。
    if not raw_worktree_path:  # 新增代码+AgentPyPhaseEPlanRuntime: 检查 worktree_path 是否为空；若没有这行代码，隔离状态会缺少路径边界。
        return "enter_worktree 失败：缺少非空 worktree_path 参数。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回清楚缺参错误；若没有这行代码，模型难以补充隔离目录。
    resolved_worktree_path = atom_tools_from_tools.resolve_workspace_path(agent, raw_worktree_path)  # 修改代码+AgentPyCompatWrapperRemovalL6: 直接通过 atom_tools 解析并限制隔离目录；若没有这行代码，删除 旧路径包装 后 enter_worktree 会断开或允许越界路径。
    if resolved_worktree_path is None:  # 新增代码+AgentPyPhaseEPlanRuntime: 恢复 worktree 路径越界检查；若没有这行代码，越界路径会继续进入状态记录。
        return "enter_worktree 失败：worktree_path 必须位于工作区内。"  # 新增代码+AgentPyPhaseEPlanRuntime: 对越界路径返回可读失败；若没有这行代码，模型不知道如何修正 worktree_path。
    relative_worktree_path = resolved_worktree_path.relative_to(agent.workspace).as_posix()  # 新增代码+AgentPyPhaseEPlanRuntime: 恢复工作区相对路径展示值；若没有这行代码，后续输出和状态会引用未定义变量。
    fallback_reason = "当前 learning_agent 教学版只记录隔离上下文，未创建真实 git worktree。"  # 新增代码+AgentPyPhaseEPlanRuntime: 恢复状态型 fallback 原因；若没有这行代码，用户看不到当前隔离强度边界。
    agent.worktree_state = {"active": True, "reason": reason, "goal": goal, "worktree_path": relative_worktree_path, "mode": "state_only_fallback", "fallback_reason": fallback_reason}  # 新增代码+AgentPyPhaseEPlanRuntime: 恢复进入 worktree 时的状态写入；若没有这行代码，exit_worktree 无法知道当前隔离上下文。
    lines = [  # 新增代码+AgentPyPhaseEPlanRuntime: 准备返回给模型和用户看的状态文本；若没有这行代码，工具结果缺少关键上下文。
        "enter_worktree 成功：已进入轻量工作区隔离状态。",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出成功前缀；若没有这行代码，调用方难以判断工具是否成功。
        "mode=state_only_fallback",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出当前模式是状态记录 fallback；若没有这行代码，模型难以判断隔离强度。
        f"fallback_reason={fallback_reason}",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出为什么没有创建真实 git worktree；若没有这行代码，用户看不到 Phase 5 的明确边界。
        f"reason={reason}",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出进入隔离状态原因；若没有这行代码，用户看不到隔离动机。
        f"goal={goal}",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出隔离工作目标；若没有这行代码，后续工作缺少目标锚点。
        f"worktree_path={relative_worktree_path}",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出隔离目录相对路径；若没有这行代码，用户无法确认隔离上下文位置。
        "边界：该工具只记录状态，不创建真实 git worktree，不创建目录，也不执行命令。",  # 新增代码+AgentPyPhaseEPlanRuntime: 明确工具没有真实副作用；若没有这行代码，模型可能误以为目录已经创建。
    ]  # 新增代码+AgentPyPhaseEPlanRuntime: 完成返回文本列表；若没有这行代码，后续 join 没有内容来源。
    return "\n".join(lines)  # 新增代码+AgentPyPhaseEPlanRuntime: 返回完整进入隔离状态结果；若没有这行代码，工具无法把状态交回模型。
# 新增代码+AgentPyPhaseEPlanRuntime: 函数段结束，enter_worktree 到此结束；若没有这个边界说明，用户不容易看出 worktree 入口逻辑已迁出 agent.py。


def exit_worktree(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseEPlanRuntime: 函数段开始，执行退出轻量 worktree 隔离状态工具；若没有这段函数，agent 无法结构化结束隔离上下文。
    if not agent.worktree_state.get("active"):  # 新增代码+AgentPyPhaseEPlanRuntime: 确认已经先进入隔离状态；若没有这行代码，模型可以绕过 enter_worktree 直接退出。
        return "exit_worktree 失败：请先调用 enter_worktree 进入工作区隔离状态，再调用 exit_worktree 退出。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回清楚顺序错误；若没有这行代码，模型难以修正调用顺序。
    summary = str(arguments.get("summary", "") or "").strip()  # 新增代码+AgentPyPhaseEPlanRuntime: 读取并清理退出总结；若没有这行代码，用户看不到隔离工作结果。
    if not summary:  # 新增代码+AgentPyPhaseEPlanRuntime: 检查 summary 是否为空；若没有这行代码，空交接可能被当作成功。
        return "exit_worktree 失败：缺少非空 summary 参数。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回清楚缺参错误；若没有这行代码，模型难以补充退出总结。
    open_items = plan_verification_optional_items(arguments.get("open_items"))  # 新增代码+AgentPyPhaseEPlanRuntime: 复用数组清理逻辑解析未完成事项；若没有这行代码，风险项输出会重复实现且易错。
    result_text = str(arguments.get("result", "") or "").strip().lower()  # 新增代码+AgentPyPhaseEPlanRuntime: 读取模型自评结论并统一成小写；若没有这行代码，blocked/failed 等状态无法参与判断。
    incomplete_markers = {"incomplete", "blocked", "failed", "missing", "partial"}  # 新增代码+AgentPyPhaseEPlanRuntime: 定义会强制判为未完成的状态词；若没有这行代码，明确失败结果可能仍被误判为 finished。
    status = "incomplete" if open_items or result_text in incomplete_markers else (result_text or "finished")  # 新增代码+AgentPyPhaseEPlanRuntime: 根据风险项和自评结论计算退出状态；若没有这行代码，用户无法快速判断隔离工作是否收尾。
    previous_reason = str(agent.worktree_state.get("reason", "") or "")  # 新增代码+AgentPyPhaseEPlanRuntime: 读取进入隔离状态时保存的原因；若没有这行代码，退出输出缺少前后衔接。
    previous_goal = str(agent.worktree_state.get("goal", "") or "")  # 新增代码+AgentPyPhaseEPlanRuntime: 读取进入隔离状态时保存的目标；若没有这行代码，退出输出缺少目标上下文。
    previous_path = str(agent.worktree_state.get("worktree_path", "") or "")  # 新增代码+AgentPyPhaseEPlanRuntime: 读取进入隔离状态时保存的路径；若没有这行代码，退出输出缺少隔离上下文位置。
    previous_mode = str(agent.worktree_state.get("mode", "") or "state_only_fallback")  # 新增代码+AgentPyPhaseEPlanRuntime: 读取进入隔离状态时的隔离模式；若没有这行代码，退出摘要无法保留真实 worktree 与 fallback 的区别。
    agent.worktree_state = {"active": False, "last_reason": previous_reason, "last_goal": previous_goal, "last_worktree_path": previous_path, "last_mode": previous_mode, "summary": summary, "status": status, "open_items": open_items}  # 新增代码+AgentPyPhaseEPlanRuntime: 退出时保存最后隔离模式；若没有这行代码，后续审计无法知道上次隔离只是状态型 fallback。
    lines = [  # 新增代码+AgentPyPhaseEPlanRuntime: 准备结构化退出摘要行；若没有这行代码，工具无法输出可审计结果。
        "exit_worktree 成功：已退出轻量工作区隔离状态。",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出成功前缀；若没有这行代码，调用方难以判断工具是否成功。
        f"status={status}",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出最终状态；若没有这行代码，用户无法快速判断隔离工作结论。
        f"worktree_path={previous_path}",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出隔离目录相对路径；若没有这行代码，用户无法知道退出的是哪个上下文。
        f"reason={previous_reason}",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出进入原因；若没有这行代码，退出结果缺少背景。
        f"goal={previous_goal}",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出进入目标；若没有这行代码，退出结果缺少目标核对。
        "总结：",  # 新增代码+AgentPyPhaseEPlanRuntime: 添加总结标题；若没有这行代码，summary 和字段行容易混在一起。
        summary,  # 新增代码+AgentPyPhaseEPlanRuntime: 输出隔离工作总结；若没有这行代码，用户不知道隔离上下文做了什么。
    ]  # 新增代码+AgentPyPhaseEPlanRuntime: 完成基础退出摘要列表；若没有这行代码，后续追加内容没有容器。
    if open_items:  # 新增代码+AgentPyPhaseEPlanRuntime: 如果存在未完成或风险项；若没有这行代码，无法决定是否输出风险详情。
        lines.append("未完成/风险项：")  # 新增代码+AgentPyPhaseEPlanRuntime: 添加风险项标题；若没有这行代码，风险内容语义不清楚。
        lines.extend(f"{index}. {item}" for index, item in enumerate(open_items, start=1))  # 新增代码+AgentPyPhaseEPlanRuntime: 编号输出每个遗漏或风险项；若没有这行代码，用户不知道具体还缺什么。
    else:  # 新增代码+AgentPyPhaseEPlanRuntime: 如果没有遗漏或风险项；若没有这行代码，用户可能不确定 open_items 为空是否代表没有风险。
        lines.append("未完成/风险项：(无)")  # 新增代码+AgentPyPhaseEPlanRuntime: 明确说明没有遗漏项；若没有这行代码，退出摘要缺少关闭语义。
    return "\n".join(lines)  # 新增代码+AgentPyPhaseEPlanRuntime: 返回完整退出隔离状态结果；若没有这行代码，工具无法把交接结果交回模型。
# 新增代码+AgentPyPhaseEPlanRuntime: 函数段结束，exit_worktree 到此结束；若没有这个边界说明，用户不容易看出 worktree 退出逻辑已迁出 agent.py。


def enter_plan_mode(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseEPlanRuntime: 函数段开始，执行进入计划模式工具并保存上下文；若没有这段函数，agent 只有工具 schema 没有实际状态切换。
    reason = str(arguments.get("reason", "") or "").strip()  # 新增代码+AgentPyPhaseEPlanRuntime: 读取并清理进入计划模式原因；若没有这行代码，用户看不到模型为什么需要先计划。
    goal = str(arguments.get("goal", "") or "").strip()  # 新增代码+AgentPyPhaseEPlanRuntime: 读取并清理计划目标；若没有这行代码，后续计划缺少明确目标。
    if not reason:  # 新增代码+AgentPyPhaseEPlanRuntime: 检查 reason 是否为空；若没有这行代码，模型可能用空原因进入计划模式。
        return "enter_plan_mode 失败：缺少非空 reason 参数。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回清楚缺参错误；若没有这行代码，模型难以修正进入计划模式参数。
    if not goal:  # 新增代码+AgentPyPhaseEPlanRuntime: 检查 goal 是否为空；若没有这行代码，模型可能在没有目标时进入计划模式。
        return "enter_plan_mode 失败：缺少非空 goal 参数。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回清楚缺参错误；若没有这行代码，模型难以修正进入计划模式参数。
    steps = plan_mode_steps(arguments.get("steps"))  # 新增代码+AgentPyPhaseEPlanRuntime: 恢复进入计划模式时的初步步骤解析；若没有这行代码，后续状态写入会引用未定义变量。
    agent.plan_mode_state = {"active": True, "reason": reason, "goal": goal, "steps": steps}  # 新增代码+AgentPyPhaseEPlanRuntime: 保存当前计划模式状态；若没有这行代码，exit_plan_mode 无法确认已进入计划模式。
    lines = ["enter_plan_mode 成功：已进入计划模式。", f"原因：{reason}", f"目标：{goal}"]  # 新增代码+AgentPyPhaseEPlanRuntime: 准备返回给模型和用户看的状态文本；若没有这行代码，工具结果缺少关键上下文。
    if steps:  # 新增代码+AgentPyPhaseEPlanRuntime: 如果模型提供了初步步骤；若没有这行代码，初步步骤无法显示。
        lines.append("初步步骤：")  # 新增代码+AgentPyPhaseEPlanRuntime: 添加步骤标题；若没有这行代码，步骤列表语义不清楚。
        lines.extend(f"{index}. {step}" for index, step in enumerate(steps, start=1))  # 新增代码+AgentPyPhaseEPlanRuntime: 恢复初步步骤编号输出；若没有这行代码，进入计划模式的步骤会被静默丢掉。
    lines.append("请继续分析并形成计划；在调用 exit_plan_mode 输出计划并等待用户确认前，不要执行写入、删除、命令执行或外部副作用工具。")  # 新增代码+AgentPyPhaseEPlanRuntime: 明确计划模式边界；若没有这行代码，模型可能进入计划模式后仍继续执行副作用工具。
    return "\n".join(lines)  # 新增代码+AgentPyPhaseEPlanRuntime: 返回完整进入计划模式结果；若没有这行代码，工具无法把状态交回模型。
# 新增代码+AgentPyPhaseEPlanRuntime: 函数段结束，enter_plan_mode 到此结束；若没有这个边界说明，用户不容易看出计划入口逻辑已迁出 agent.py。


def exit_plan_mode(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseEPlanRuntime: 函数段开始，执行退出计划模式工具并输出待确认计划；若没有这段函数，agent 无法结束计划阶段。
    if not agent.plan_mode_state.get("active"):  # 新增代码+AgentPyPhaseEPlanRuntime: 确认已经先进入计划模式；若没有这行代码，模型可以绕过 enter_plan_mode 直接输出计划。
        return "exit_plan_mode 失败：请先调用 enter_plan_mode 进入计划模式，再调用 exit_plan_mode 输出计划。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回清楚顺序错误；若没有这行代码，模型难以修正调用顺序。
    plan = str(arguments.get("plan", "") or "").strip()  # 新增代码+AgentPyPhaseEPlanRuntime: 读取并清理最终计划正文；若没有这行代码，用户看不到要确认的计划。
    if not plan:  # 新增代码+AgentPyPhaseEPlanRuntime: 检查 plan 是否为空；若没有这行代码，空计划可能被当作成功。
        return "exit_plan_mode 失败：缺少非空 plan 参数。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回清楚缺参错误；若没有这行代码，模型难以修正退出计划模式参数。
    steps = plan_mode_steps(arguments.get("steps"))  # 新增代码+AgentPyPhaseEPlanRuntime: 解析可选最终步骤列表；若没有这行代码，steps 参数会被忽略。
    previous_reason = str(agent.plan_mode_state.get("reason", "") or "")  # 新增代码+AgentPyPhaseEPlanRuntime: 读取进入计划模式时保存的原因；若没有这行代码，最终输出缺少前后衔接。
    previous_goal = str(agent.plan_mode_state.get("goal", "") or "")  # 新增代码+AgentPyPhaseEPlanRuntime: 读取进入计划模式时保存的目标；若没有这行代码，最终输出缺少计划目标。
    agent.plan_mode_state = {"active": False, "awaiting_confirmation": True, "reason": previous_reason, "goal": previous_goal, "plan": plan, "steps": steps}  # 新增代码+AgentPyPhaseEPlanRuntime: 标记计划模式结束并等待用户确认；若没有这行代码，agent 无法记录确认前状态。
    lines = ["exit_plan_mode 成功：已输出计划，等待用户确认。", f"原始原因：{previous_reason}", f"计划目标：{previous_goal}", "最终计划：", plan]  # 新增代码+AgentPyPhaseEPlanRuntime: 准备返回最终计划文本；若没有这行代码，用户无法看到计划内容。
    if steps:  # 新增代码+AgentPyPhaseEPlanRuntime: 如果模型提供了最终步骤；若没有这行代码，最终步骤无法显示。
        lines.append("最终步骤：")  # 新增代码+AgentPyPhaseEPlanRuntime: 添加最终步骤标题；若没有这行代码，步骤列表语义不清楚。
        lines.extend(f"{index}. {step}" for index, step in enumerate(steps, start=1))  # 新增代码+AgentPyPhaseEPlanRuntime: 把最终步骤编号输出；若没有这行代码，多步骤计划不易阅读。
    lines.append("等待用户确认：用户确认前不要执行写入、删除、命令执行或外部副作用工具。")  # 新增代码+AgentPyPhaseEPlanRuntime: 明确下一步必须等待确认；若没有这行代码，模型可能计划后立刻执行。
    return "\n".join(lines)  # 新增代码+AgentPyPhaseEPlanRuntime: 返回完整退出计划模式结果；若没有这行代码，工具无法把待确认计划交回模型。
# 新增代码+AgentPyPhaseEPlanRuntime: 函数段结束，exit_plan_mode 到此结束；若没有这个边界说明，用户不容易看出计划出口逻辑已迁出 agent.py。


def verify_plan_execution(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseEPlanRuntime: 函数段开始，执行计划验证工具并生成审计摘要；若没有这段函数，工具 schema 存在但没有实际行为。
    plan = str(arguments.get("plan", "") or "").strip()  # 新增代码+AgentPyPhaseEPlanRuntime: 读取并清理显式传入的计划正文；若没有这行代码，用户传入的验证对象会被忽略。
    if not plan:  # 新增代码+AgentPyPhaseEPlanRuntime: 如果调用方没有显式传 plan；若没有这行代码，无法回退到最近 exit_plan_mode 保存的计划。
        plan = str(agent.plan_mode_state.get("plan", "") or "").strip()  # 新增代码+AgentPyPhaseEPlanRuntime: 使用最近保存的计划作为验证对象；若没有这行代码，exit_plan_mode 后调用验证仍会缺少计划。
    if not plan:  # 新增代码+AgentPyPhaseEPlanRuntime: 检查是否仍然没有可验证计划；若没有这行代码，空计划可能被当成成功验证。
        return "verify_plan_execution 失败：缺少非空 plan 参数，且当前没有 exit_plan_mode 保存的计划。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回清楚缺参错误；若没有这行代码，模型难以修正验证参数。
    executed_steps = plan_verification_items(arguments.get("executed_steps"), "executed_steps")  # 新增代码+AgentPyPhaseEPlanRuntime: 解析已执行步骤列表；若没有这行代码，工具无法统计实际完成步骤。
    if isinstance(executed_steps, str):  # 新增代码+AgentPyPhaseEPlanRuntime: 检查已执行步骤解析是否失败；若没有这行代码，错误文本会被当作列表继续处理。
        return executed_steps  # 新增代码+AgentPyPhaseEPlanRuntime: 直接返回解析错误给模型；若没有这行代码，模型不知道 executed_steps 参数有问题。
    evidence_items = plan_verification_items(arguments.get("evidence"), "evidence")  # 新增代码+AgentPyPhaseEPlanRuntime: 解析验证证据列表；若没有这行代码，工具无法统计验证依据。
    if isinstance(evidence_items, str):  # 新增代码+AgentPyPhaseEPlanRuntime: 检查证据解析是否失败；若没有这行代码，错误文本会被当作列表继续处理。
        return evidence_items  # 新增代码+AgentPyPhaseEPlanRuntime: 直接返回解析错误给模型；若没有这行代码，模型不知道 evidence 参数有问题。
    open_items = plan_verification_optional_items(arguments.get("open_items"))  # 新增代码+AgentPyPhaseEPlanRuntime: 解析可选遗漏和风险项；若没有这行代码，未完成事项无法进入验证状态判断。
    result_text = str(arguments.get("result", "") or "").strip().lower()  # 新增代码+AgentPyPhaseEPlanRuntime: 读取模型自评结论并统一成小写；若没有这行代码，blocked/failed 等状态无法参与判断。
    incomplete_markers = {"incomplete", "blocked", "failed", "missing", "partial"}  # 新增代码+AgentPyPhaseEPlanRuntime: 定义会强制判为未完成的状态词；若没有这行代码，明确失败结果可能仍被误判为 verified。
    status = "incomplete" if open_items or result_text in incomplete_markers else "verified"  # 新增代码+AgentPyPhaseEPlanRuntime: 根据遗漏项和自评结论计算最终状态；若没有这行代码，用户无法快速区分完成和未完成。
    lines = [  # 新增代码+AgentPyPhaseEPlanRuntime: 准备结构化验证摘要行；若没有这行代码，工具无法输出可审计结果。
        "verify_plan_execution 成功：已生成计划执行验证摘要。",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出成功前缀；若没有这行代码，调用方难以判断工具是否成功执行。
        f"status={status}",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出最终状态；若没有这行代码，用户无法快速判断验证结论。
        f"executed_step_count={len(executed_steps)}",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出已执行步骤数量；若没有这行代码，用户需要逐行数步骤。
        f"evidence_count={len(evidence_items)}",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出证据数量；若没有这行代码，用户无法快速评估证据充分性。
        f"open_item_count={len(open_items)}",  # 新增代码+AgentPyPhaseEPlanRuntime: 输出遗漏项数量；若没有这行代码，用户无法快速判断剩余风险。
        "计划：",  # 新增代码+AgentPyPhaseEPlanRuntime: 添加计划标题；若没有这行代码，计划正文和后续列表容易混在一起。
        plan,  # 新增代码+AgentPyPhaseEPlanRuntime: 输出被验证的计划正文；若没有这行代码，验证摘要缺少对象。
        "已执行步骤：",  # 新增代码+AgentPyPhaseEPlanRuntime: 添加已执行步骤标题；若没有这行代码，步骤列表语义不清楚。
    ]  # 新增代码+AgentPyPhaseEPlanRuntime: 完成基础摘要列表；若没有这行代码，后续追加内容没有容器。
    lines.extend(f"{index}. {step}" for index, step in enumerate(executed_steps, start=1))  # 新增代码+AgentPyPhaseEPlanRuntime: 编号输出每个已执行步骤；若没有这行代码，多步骤审计不易阅读。
    lines.append("验证证据：")  # 新增代码+AgentPyPhaseEPlanRuntime: 添加证据标题；若没有这行代码，证据列表语义不清楚。
    lines.extend(f"{index}. {item}" for index, item in enumerate(evidence_items, start=1))  # 新增代码+AgentPyPhaseEPlanRuntime: 编号输出每条证据；若没有这行代码，用户无法逐条核验证据。
    if open_items:  # 新增代码+AgentPyPhaseEPlanRuntime: 如果存在未完成或风险项；若没有这行代码，无法决定是否输出遗漏详情。
        lines.append("未完成/风险项：")  # 新增代码+AgentPyPhaseEPlanRuntime: 添加遗漏项标题；若没有这行代码，遗漏内容语义不清楚。
        lines.extend(f"{index}. {item}" for index, item in enumerate(open_items, start=1))  # 新增代码+AgentPyPhaseEPlanRuntime: 编号输出每个遗漏或风险项；若没有这行代码，用户不知道具体还缺什么。
    else:  # 新增代码+AgentPyPhaseEPlanRuntime: 如果没有遗漏或风险项；若没有这行代码，用户可能不确定 open_item_count=0 是否代表没有风险。
        lines.append("未完成/风险项：(无)")  # 新增代码+AgentPyPhaseEPlanRuntime: 明确说明没有遗漏项；若没有这行代码，验证摘要缺少关闭语义。
    return "\n".join(lines)  # 新增代码+AgentPyPhaseEPlanRuntime: 返回完整验证摘要；若没有这行代码，工具无法把审计结果交回模型。
# 新增代码+AgentPyPhaseEPlanRuntime: 函数段结束，verify_plan_execution 到此结束；若没有这个边界说明，用户不容易看出计划验证逻辑已迁出 agent.py。


def plan_verification_items(raw_items: Any, field_name: str) -> list[str] | str:  # 新增代码+AgentPyPhaseEPlanRuntime: 函数段开始，解析必填验证数组字段；若没有这段函数，executed_steps/evidence 校验逻辑会重复且易错。
    if not isinstance(raw_items, list):  # 新增代码+AgentPyPhaseEPlanRuntime: 必填字段必须是数组；若没有这行代码，字符串可能被误当成多个字符步骤。
        return f"verify_plan_execution 失败：{field_name} 必须是非空字符串数组。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回字段类型错误；若没有这行代码，模型不知道该字段需要数组。
    items = [str(item).strip() for item in raw_items if item is not None and str(item).strip()]  # 新增代码+AgentPyPhaseEPlanRuntime: 清理数组项并丢弃空项；若没有这行代码，空白证据或步骤会污染审计结果。
    if not items:  # 新增代码+AgentPyPhaseEPlanRuntime: 检查清理后是否还有有效项；若没有这行代码，空数组也可能通过验证。
        return f"verify_plan_execution 失败：{field_name} 必须至少包含一项。"  # 新增代码+AgentPyPhaseEPlanRuntime: 返回字段为空错误；若没有这行代码，模型难以补足必填验证内容。
    return items  # 新增代码+AgentPyPhaseEPlanRuntime: 返回清理后的有效数组；若没有这行代码，调用方拿不到可输出的步骤或证据。
# 新增代码+AgentPyPhaseEPlanRuntime: 函数段结束，plan_verification_items 到此结束；若没有这个边界说明，用户不容易看出必填数组解析已迁出 agent.py。


def plan_verification_optional_items(raw_items: Any) -> list[str]:  # 新增代码+AgentPyPhaseEPlanRuntime: 函数段开始，解析可选遗漏项数组；若没有这段函数，open_items 容错逻辑会散落在主方法里。
    if not isinstance(raw_items, list):  # 新增代码+AgentPyPhaseEPlanRuntime: 非数组遗漏项按未提供处理；若没有这行代码，None 或字符串会导致后续遍历语义混乱。
        return []  # 新增代码+AgentPyPhaseEPlanRuntime: 可选字段缺失时返回空列表；若没有这行代码，调用方需要额外处理 None。
    return [str(item).strip() for item in raw_items if item is not None and str(item).strip()]  # 新增代码+AgentPyPhaseEPlanRuntime: 清理遗漏项并丢弃空项；若没有这行代码，空白风险会污染输出。
# 新增代码+AgentPyPhaseEPlanRuntime: 函数段结束，plan_verification_optional_items 到此结束；若没有这个边界说明，用户不容易看出可选数组解析已迁出 agent.py。


def plan_mode_steps(raw_steps: Any) -> list[str]:  # 新增代码+AgentPyPhaseEPlanRuntime: 函数段开始，把模型传入的 steps 统一清理成字符串列表；若没有这段函数，enter/exit 两个工具会重复解析逻辑。
    if raw_steps is None:  # 新增代码+AgentPyPhaseEPlanRuntime: 允许模型省略 steps；若没有这行代码，None 会被当成不可迭代对象。
        return []  # 新增代码+AgentPyPhaseEPlanRuntime: 省略 steps 时返回空列表；若没有这行代码，调用方需要额外判断 None。
    if not isinstance(raw_steps, list):  # 新增代码+AgentPyPhaseEPlanRuntime: 只接受数组形式的步骤；若没有这行代码，字符串会被逐字符拆开。
        return []  # 新增代码+AgentPyPhaseEPlanRuntime: 非数组步骤按空列表处理；若没有这行代码，错误类型可能污染计划输出。
    return [str(step).strip() for step in raw_steps if str(step).strip()]  # 新增代码+AgentPyPhaseEPlanRuntime: 清理每个步骤并丢弃空步骤；若没有这行代码，输出里可能出现空白或非字符串步骤。
# 新增代码+AgentPyPhaseEPlanRuntime: 函数段结束，plan_mode_steps 到此结束；若没有这个边界说明，用户不容易看出计划步骤解析已迁出 agent.py。
