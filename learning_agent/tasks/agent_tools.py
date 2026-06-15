"""Task/team/cron/monitor tool entrypoints extracted from LearningAgent."""  # 新增代码+TaskAgentToolsSplit: 说明本文件承接 agent.py 的任务、团队、定时和监控工具细节；若没有这行说明，代码小白很难知道这个模块为什么存在。

from __future__ import annotations  # 新增代码+TaskAgentToolsSplit: 允许类型注解延迟解析；若没有这行代码，某些前向类型在导入时可能提前求值。

import secrets  # 新增代码+TaskAgentToolsSplit: 生成 task、team、cron、monitor 的短随机 id；若没有这行代码，新记录无法获得稳定唯一编号。
import threading  # 新增代码+TaskAgentToolsSplit: 后台 task 需要启动子线程；若没有这行代码，background=true 的子任务无法异步运行。
import time  # 新增代码+TaskAgentToolsSplit: 记录创建、完成、删除、确认等时间；若没有这行代码，任务和团队记录缺少可审计时间。
from typing import Any  # 新增代码+TaskAgentToolsSplit: 使用 Any 描述传入的 LearningAgent 对象和模型参数；若没有这行代码，类型注解会找不到 Any。

try:  # 新增代码+TaskAgentToolsSplit: 包运行模式下优先从 learning_agent 包导入依赖；若没有这行代码，正常包导入路径会失效。
    from learning_agent.core.config import parse_max_turns_value  # 新增代码+TaskAgentToolsSplit: 复用主配置里的轮次解析规则；若没有这行代码，task.max_turns 会和主 agent 语义不一致。
    from learning_agent.runtime.background_commands import parse_max_chars_value  # 修改代码+AgentPySplitPhase15B2: 导入不依赖 agent.py 的输出长度解析函数；若没有这行代码，task 工具仍要反向调用 agent.旧输出长度薄包装。
    from learning_agent.tasks.cron_monitor import CronRecord, MonitorRecord, cron_monitor_max_results, cron_monitor_state, format_cron_record, format_monitor_record, monitor_result_status  # 新增代码+TaskAgentToolsSplit: 导入 Cron/Monitor 数据结构和格式化 helper；若没有这行代码，cron/monitor 工具无法创建或展示记录。
    from learning_agent.tasks.task_runs import BLOCKED_TASK_TOOL_NAMES, TaskRun, task_background_enabled, task_child_prompt  # 新增代码+TaskAgentToolsSplit: 导入 task 记录、后台开关和子 prompt helper；若没有这行代码，子任务生命周期无法复用现有小模块。
    from learning_agent.tasks.team import TeamMessage, TeamPeer, peer_status_from_pending_count  # 新增代码+TaskAgentToolsSplit: 导入 team 消息、peer 记录和状态 helper；若没有这行代码，团队通信工具无法保存和统计消息。
    import learning_agent.tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 导入工具目录和工具池运行时；若没有这行代码，task allowed_tools 仍会通过 agent.py 薄包装判断。
    import learning_agent.tools.search as search_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL2: 直接导入工具搜索 helper；若没有这行代码，任务和团队列表数量限制还要绕回 agent.py 旧包装。
except ModuleNotFoundError as error:  # 新增代码+TaskAgentToolsSplit: 兼容 start_oauth_agent.bat 这类脚本模式路径；若没有这行代码，直接运行入口可能因为包名前缀不同而失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.config", "learning_agent.runtime", "learning_agent.runtime.background_commands", "learning_agent.tasks", "learning_agent.tasks.cron_monitor", "learning_agent.tasks.task_runs", "learning_agent.tasks.team", "learning_agent.tools", "learning_agent.tools.catalog_runtime", "learning_agent.tools.search"}:  # 修改代码+AgentPyCompatWrapperRemovalL2: 允许 search helper 路径差异进入 fallback；若没有这行代码，bat 入口会把路径差异误判成真实导入失败。
        raise  # 新增代码+TaskAgentToolsSplit: 重新抛出真实导入错误；若没有这行代码，内部依赖坏了也会被 fallback 掩盖。
    from core.config import parse_max_turns_value  # 新增代码+TaskAgentToolsSplit: 脚本模式下从同级 core 包导入轮次解析；若没有这行代码，bat 入口无法解析 task.max_turns。
    from runtime.background_commands import parse_max_chars_value  # 修改代码+AgentPySplitPhase15B2: 脚本模式下导入公共输出长度解析函数；若没有这行代码，bat 入口执行 task 输出读取会找不到解析函数。
    from tasks.cron_monitor import CronRecord, MonitorRecord, cron_monitor_max_results, cron_monitor_state, format_cron_record, format_monitor_record, monitor_result_status  # 新增代码+TaskAgentToolsSplit: 脚本模式下导入 Cron/Monitor helper；若没有这行代码，直接运行时 cron/monitor 工具会找不到记录类。
    from tasks.task_runs import BLOCKED_TASK_TOOL_NAMES, TaskRun, task_background_enabled, task_child_prompt  # 新增代码+TaskAgentToolsSplit: 脚本模式下导入 task helper；若没有这行代码，直接运行时 task 工具会找不到生命周期对象。
    from tasks.team import TeamMessage, TeamPeer, peer_status_from_pending_count  # 新增代码+TaskAgentToolsSplit: 脚本模式下导入 team helper；若没有这行代码，直接运行时 team 工具会找不到消息和 peer 类型。
    import tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入工具目录和工具池运行时；若没有这行代码，bat 入口 task allowed_tools 会断开。
    import tools.search as search_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL2: 脚本模式下导入工具搜索 helper；若没有这行代码，直接运行时任务和团队列表仍会依赖 agent.py 旧包装。

def task(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TaskAgent: 执行内置 task 工具并启动同进程子 agent；若省略: 主 agent 无法委派子任务
    prompt = str(arguments.get("prompt", "") or "").strip()  # 新增代码+TaskAgent: 读取并清理子任务 prompt；若省略: 子 agent 不知道要执行什么任务
    if not prompt:  # 新增代码+TaskAgent: 检查 prompt 是否为空；若省略: 空子任务会浪费模型调用并产生模糊结果
        return "task 失败：缺少非空 prompt 参数。"  # 新增代码+TaskAgent: 返回清楚缺参错误；若省略: 模型难以修正 task 调用
    allowed_tool_names = task_allowed_tool_names(agent, arguments.get("allowed_tools"))  # 新增代码+TaskAgent: 解析子 agent 工具白名单；若省略: 子 agent 无法被限制工具范围
    if isinstance(allowed_tool_names, str):  # 新增代码+TaskAgent: 字符串返回值表示白名单解析失败；若省略: 错误字符串会被当作工具集合使用
        return allowed_tool_names  # 新增代码+TaskAgent: 直接返回可读失败信息；若省略: 模型看不到 allowed_tools 的具体错误
    max_turns = task_max_turns(arguments.get("max_turns"))  # 新增代码+TaskAgent: 解析子 agent 最大轮次；若省略: 子任务可能无界运行或无法控制执行长度
    if isinstance(max_turns, str):  # 新增代码+TaskAgent: 字符串返回值表示 max_turns 解析失败；若省略: 错误字符串会被当作轮次数值使用
        return max_turns  # 新增代码+TaskAgent: 直接返回可读失败信息；若省略: 模型看不到 max_turns 的具体错误
    background = task_background_enabled_for_agent(arguments.get("background"))  # 新增代码+AsyncTask: 解析 background 开关；若省略: task 无法区分同步执行和后台执行
    stop_event = threading.Event() if background else None  # 新增代码+AsyncTask: 后台任务创建取消信号，同步任务保持 None；若省略: task_stop 无法通知后台子 agent
    task_id = f"task_{secrets.token_hex(6)}"  # 新增代码+TaskLifecycle: 生成短且唯一的子任务 id；若省略: task_output/task_stop 无法引用这次子任务
    task_record = TaskRun(task_id=task_id, prompt=prompt, allowed_tool_names=allowed_tool_names, max_turns=max_turns, status="running", created_at=time.strftime("%Y-%m-%d %H:%M:%S"), background=background, stop_event=stop_event)  # 修改代码+AsyncTask: 创建运行中任务记录并保存后台/取消信息；若省略 background/stop_event: task_output/task_stop 无法管理后台子任务
    agent.task_runs[task_id] = task_record  # 新增代码+TaskLifecycle: 把任务记录放入 agent 内存表；若省略: task_id 返回后也无法被 task_output/task_stop 找到
    agent.task_registry.create_task(task_id=task_id, prompt=prompt, kind="agent", status="running", allowed_tool_names=sorted(allowed_tool_names), max_turns=max_turns, background=background)  # 新增代码+DurableTaskRegistry: 同步创建持久 task 记录；若没有这行代码，新 agent 实例无法恢复或审计这个子任务。
    child_prompt = task_child_prompt_for_agent(prompt)  # 新增代码+TaskAgent: 构造给子 agent 的专用提示；若省略: 子 agent 缺少“返回摘要给主 agent”的执行边界
    child_agent = agent.__class__(  # 新增代码+TaskAgent: 创建同进程子 agent；若省略: task 只能返回文本而不能真正执行子任务
        model=agent.model,  # 新增代码+TaskAgent: 子 agent 复用当前模型客户端；若省略: 子任务无法调用同一个后端模型
        workspace=agent.workspace,  # 新增代码+TaskAgent: 子 agent 使用同一工作区；若省略: 子任务无法读取主项目文件
        ask_permission=agent.ask_permission,  # 新增代码+TaskAgent: 子 agent 复用同一权限确认函数；若省略: 子任务写入或外部调用会绕过用户确认
        debug_log_path=agent.debug_log_path,  # 新增代码+TaskAgent: 子 agent 写入同一调试日志；若省略: 子任务执行过程不易追踪
        debug_enabled=agent.debug_enabled,  # 新增代码+TaskAgent: 子 agent 继承调试开关；若省略: 用户关闭日志后子任务仍可能写日志
        mcp_tool_registry=agent.mcp_tool_registry,  # 修改代码+TaskAgent: 子 agent 复用父 agent 已有 MCP registry；若省略: 子 agent 无法继承已启动的外部工具
        allowed_tool_names=allowed_tool_names,  # 新增代码+TaskAgent: 把工具白名单交给子 agent；若省略: allowed_tools 参数不会生效
        inherited_mcp_tools_enabled=agent.mcp_tools_enabled,  # 新增代码+TaskAgent: 继承父 agent 的 MCP 启用状态且不重复启动 server；若省略: 子 agent 可能重复请求启动 MCP
        inherited_mcp_start_error=agent.mcp_start_error,  # 新增代码+TaskAgent: 继承父 agent 的 MCP 启动错误；若省略: 子 agent 无法解释 MCP 不可用原因
        stop_event=stop_event,  # 新增代码+AsyncTask: 把取消信号传给子 agent；若省略: task_stop 只能改状态而不能让子 agent 协作停止
    )  # 新增代码+TaskAgent: 子 agent 构造结束；若省略: Python 调用语法不完整
    child_agent.tool_policy_context.allow_rules = list(agent.tool_policy_context.allow_rules)  # 新增代码+ToolPolicyV2: 子 agent 继承父 agent 的 allow rules；若没有这行代码，父任务显式允许的工具策略不会传给子任务
    child_agent.tool_policy_context.deny_rules = list(agent.tool_policy_context.deny_rules)  # 新增代码+ToolPolicyV2: 子 agent 继承父 agent 的 deny rules；若没有这行代码，子任务可能绕过父 agent 已禁止的工具
    child_agent.tool_policy_context.loaded_skills = set(agent.tool_policy_context.loaded_skills)  # 新增代码+ToolPolicyV2: 子 agent 继承父 agent 已加载的 skills；若没有这行代码，子任务可能误以为 skill 未加载并错误隐藏可用工具
    child_agent.tool_policy_context.completed_workflows = set(agent.tool_policy_context.completed_workflows)  # 新增代码+ToolPolicyV2: 子 agent 继承父 agent 已完成的 workflows；若没有这行代码，子任务可能重复要求已经完成的前置流程
    child_agent.loaded_tool_names.update(agent.loaded_tool_names & allowed_tool_names)  # 新增代码+ToolArchitectureV2: 只把父 agent 已经 select 且被 allowed_tools 允许的 deferred 工具继承给子 agent；若没有这行代码，子 agent 会拿不到父 agent 已加载的 MCP 工具池
    if background:  # 新增代码+AsyncTask: 后台模式走线程启动并立即返回；若省略: background=true 仍会阻塞主 agent
        task_thread = threading.Thread(target=run_task_record, args=(agent, task_record, child_agent, child_prompt), daemon=True)  # 新增代码+AsyncTask: 创建后台子 agent 线程；若省略: 子任务无法异步运行
        task_record.thread = task_thread  # 新增代码+AsyncTask: 把线程对象写回任务记录；若省略: task_output/test 无法观察后台线程
        task_thread.start()  # 新增代码+AsyncTask: 真正启动后台子 agent；若省略: task 只会返回 task_id 但任务不会执行
        return f"task 成功：子 agent 已后台启动。\ntask_id={task_id}\nstatus=running\nbackground=true\n允许工具：{', '.join(sorted(allowed_tool_names)) or '(无工具)'}"  # 新增代码+AsyncTask: 立即返回后台任务 id 和状态；若省略: 主 agent 无法继续用 task_output/task_stop 管理任务
    run_task_record(agent, task_record, child_agent, child_prompt)  # 新增代码+AsyncTask: 同步模式复用统一执行记录逻辑；若省略: 同步 task 和后台 task 的状态写回会分叉
    if task_record.status == "failed":  # 新增代码+AsyncTask: 如果统一执行逻辑记录失败；若省略: 同步子任务异常会被包装成成功输出
        return f"task 失败：task_id={task_id}\n子 agent 执行失败：{task_record.error}"  # 新增代码+AsyncTask: 返回带 task_id 的失败信息；若省略: 主 agent 无法继续查询失败记录
    if task_record.status == "stopped":  # 新增代码+AsyncTask: 如果同步执行期间收到取消；若省略: stopped 状态可能继续按 completed 输出
        return f"task 成功：子 agent 已停止。\ntask_id={task_id}\n原因：{task_record.error or '(未提供)'}"  # 新增代码+AsyncTask: 返回停止结果给模型；若省略: 主 agent 看不到子任务取消原因
    child_answer = task_record.output  # 新增代码+AsyncTask: 从任务记录读取统一保存的输出；若省略: 同步返回逻辑拿不到子 agent 结果
    return f"task 成功：子 agent 已完成。\ntask_id={task_id}\n允许工具：{', '.join(sorted(allowed_tool_names)) or '(无工具)'}\n子任务结果：\n{child_answer}"  # 修改代码+TaskAgentToolsSplit: 返回同步子任务完成结果；若没有这行代码，主 agent 收不到子 agent 的最终摘要。

def run_task_record(agent: Any, task_record: TaskRun, child_agent: Any, child_prompt: str) -> None:  # 新增代码+AsyncTask: 统一执行子 agent 并写回任务记录；若省略: 同步/后台两条路径会重复且容易状态不一致
    try:  # 新增代码+AsyncTask: 捕获子 agent 执行异常并写回任务记录；若省略: 后台线程异常会静默丢失且 task_output 看不到失败原因
        child_answer = child_agent.run(child_prompt, max_turns=task_record.max_turns)  # 新增代码+AsyncTask: 执行子 agent 并获得最终回答；若省略: 子任务不会真正运行
    except Exception as error:  # 新增代码+AsyncTask: 处理子 agent 运行时异常；若省略: 失败任务不会被记录为 failed
        if task_record.status != "stopped":  # 新增代码+AsyncTask: 如果任务尚未被 stop 标记；若省略: stop 后的异常可能覆盖用户取消状态
            task_record.status = "failed"  # 新增代码+AsyncTask: 标记子任务失败；若省略: task_output 会误以为任务仍在 running
            task_record.error = str(error)  # 新增代码+AsyncTask: 保存失败原因；若省略: 用户无法知道子任务为什么失败
            task_record.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+AsyncTask: 保存失败结束时间；若省略: 查询结果缺少任务结束时间
            agent.task_registry.fail_task(task_record.task_id, task_record.error)  # 新增代码+DurableTaskRegistry: 把失败状态写入持久任务登记表并通知主循环；若没有这行代码，后台子任务失败只会留在内存。
        return  # 新增代码+AsyncTask: 异常处理结束后退出执行函数；若省略: 后续会继续按成功路径写状态
    if task_record.stop_event is not None and task_record.stop_event.is_set():  # 新增代码+AsyncTask: 如果子任务结束时已经收到取消信号；若省略: 后台 stop 后可能被完成结果覆盖
        task_record.stop_requested = True  # 新增代码+AsyncTask: 记录取消意图；若省略: task_output 无法反映任务确实收到了停止请求
        task_record.status = "stopped"  # 新增代码+AsyncTask: 保持停止状态；若省略: task_stop 的 stopped 状态可能被 completed 覆盖
        task_record.error = task_record.error or "任务已停止：收到取消请求。"  # 新增代码+AsyncTask: 保存默认停止说明；若省略: task_output 可能只显示空输出
        task_record.completed_at = task_record.completed_at or time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+AsyncTask: 如果 stop 尚未写结束时间则补齐；若省略: 停止任务可能显示未完成
        agent.task_registry.stop_task(task_record.task_id, task_record.error)  # 新增代码+DurableTaskRegistry: 把停止状态写入持久任务登记表并通知主循环；若没有这行代码，新 agent 实例看不到停止结果。
        return  # 新增代码+AsyncTask: 停止路径不再保存成功输出；若省略: 被取消任务会误显示为完成
    task_record.status = "completed"  # 新增代码+AsyncTask: 标记子任务完成；若省略: task_output 会误以为任务仍在 running
    task_record.output = child_answer  # 新增代码+AsyncTask: 保存子 agent 最终回答；若省略: task_output 无法读回任务结果
    task_record.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+AsyncTask: 保存完成时间；若省略: 查询结果缺少任务结束时间
    agent.task_registry.complete_task(task_record.task_id, output=child_answer, usage={})  # 修改代码+TaskAgentToolsSplit: 把成功结果写入持久任务登记表；若没有这行代码，跨实例状态页看不到子任务完成输出。

def task_output(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TaskLifecycle: 执行 task_output 工具并读取任务记录；若省略: 模型无法二次查询子任务结果
    task_id = str(arguments.get("task_id", "") or "").strip()  # 新增代码+TaskLifecycle: 读取并清理 task_id 参数；若省略: 工具不知道要查询哪个子任务
    if not task_id:  # 新增代码+TaskLifecycle: 检查 task_id 是否为空；若省略: 空查询会产生模糊未知任务错误
        return "task_output 失败：缺少 task_id 参数。"  # 新增代码+TaskLifecycle: 返回清楚缺参错误；若省略: 模型难以修正 task_output 调用
    task_record = agent.task_runs.get(task_id)  # 新增代码+TaskLifecycle: 从内存表查找任务记录；若省略: 工具无法定位任务状态和输出
    if task_record is None:  # 新增代码+TaskLifecycle: 处理未知 task_id；若省略: 访问 None 会抛异常
        try:  # 新增代码+DurableTaskRegistry: 内存表找不到时尝试读取持久登记表；若没有这行代码，重启后的 agent 无法查询旧 task。
            persisted_record = agent.task_registry.get_task(task_id)  # 新增代码+DurableTaskRegistry: 从磁盘恢复任务记录；若没有这行代码，task_output 只能依赖当前进程。
        except KeyError:  # 新增代码+DurableTaskRegistry: 持久登记表也没有该任务时返回旧错误；若没有这行代码，未知 id 会抛异常。
            return f"task_output 失败：未知 task_id：{task_id}"  # 修改代码+DurableTaskRegistry: 返回清楚未知任务错误；若省略: 模型难以判断是否需要重新创建任务
        max_chars = parse_max_chars_value(arguments.get("max_chars"))  # 修改代码+AgentPySplitPhase15B2: 直接使用公共解析函数，不再依赖 agent.py 薄包装；若没有这行代码，删除 `旧输出长度薄包装` 后持久 task_output 会断开。
        output_text = persisted_record.output or persisted_record.error or agent.task_registry.output_store.tail(task_id, max_chars=max_chars) or "(暂无输出)"  # 新增代码+DurableTaskRegistry: 优先读取登记表摘要并兜底输出文件；若没有这行代码，持久任务结果可能为空。
        truncated_output = output_text[:max_chars]  # 新增代码+DurableTaskRegistry: 按 max_chars 截断持久输出；若没有这行代码，长输出不可控。
        if len(output_text) > max_chars:  # 新增代码+DurableTaskRegistry: 判断持久输出是否被截断；若没有这行代码，模型不知道结果是否完整。
            truncated_output += "\n...[task 输出过长，已截断]..."  # 新增代码+DurableTaskRegistry: 添加截断提示；若没有这行代码，模型可能误以为拿到完整输出。
        return f"task_output 成功：task_id={task_id}\nstatus={persisted_record.status}\nbackground={'true' if persisted_record.background else 'false'}\ncreated_at={persisted_record.created_at}\ncompleted_at={persisted_record.completed_at or '(未完成)'}\nallowed_tools={', '.join(sorted(persisted_record.allowed_tool_names)) or '(无工具)'}\nmax_turns={persisted_record.max_turns}\noutput_path={persisted_record.output_path or '(无)'}\n输出：\n{truncated_output}"  # 新增代码+DurableTaskRegistry: 返回持久任务状态和输出；若没有这行代码，跨进程 task_output 不可用。
    max_chars = parse_max_chars_value(arguments.get("max_chars"))  # 修改代码+AgentPySplitPhase15B2: 直接使用公共解析函数，不再依赖 agent.py 薄包装；若没有这行代码，删除 `旧输出长度薄包装` 后内存 task_output 会断开。
    output_text = task_record.output or task_record.error or "(暂无输出)"  # 新增代码+TaskLifecycle: 选择任务输出、错误或空输出占位；若省略: 未完成任务会返回空白难以理解
    truncated_output = output_text[:max_chars]  # 新增代码+TaskLifecycle: 按 max_chars 截断输出；若省略: 长输出不可控
    if len(output_text) > max_chars:  # 新增代码+TaskLifecycle: 判断输出是否被截断；若省略: 模型不知道结果是否完整
        truncated_output += "\n...[task 输出过长，已截断]..."  # 新增代码+TaskLifecycle: 添加截断提示；若省略: 模型可能误以为拿到完整输出
    return f"task_output 成功：task_id={task_id}\nstatus={task_record.status}\nbackground={'true' if task_record.background else 'false'}\ncreated_at={task_record.created_at}\ncompleted_at={task_record.completed_at or '(未完成)'}\nallowed_tools={', '.join(sorted(task_record.allowed_tool_names)) or '(无工具)'}\nmax_turns={task_record.max_turns}\n输出：\n{truncated_output}"  # 修改代码+TaskAgentToolsSplit: 返回任务状态和截断后的输出；若没有这行代码，模型无法读取子任务结果。

def task_stop(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TaskLifecycle: 执行 task_stop 工具并更新任务状态；若省略: 模型无法表达停止子任务的请求
    task_id = str(arguments.get("task_id", "") or "").strip()  # 新增代码+TaskLifecycle: 读取并清理 task_id 参数；若省略: 工具不知道要停止哪个子任务
    if not task_id:  # 新增代码+TaskLifecycle: 检查 task_id 是否为空；若省略: 空停止请求会产生模糊未知任务错误
        return "task_stop 失败：缺少 task_id 参数。"  # 新增代码+TaskLifecycle: 返回清楚缺参错误；若省略: 模型难以修正 task_stop 调用
    task_record = agent.task_runs.get(task_id)  # 新增代码+TaskLifecycle: 从内存表查找任务记录；若省略: 工具无法定位任务状态
    if task_record is None:  # 新增代码+TaskLifecycle: 处理未知 task_id；若省略: 访问 None 会抛异常
        try:  # 新增代码+DurableTaskRegistry: 内存表没有时尝试停止持久任务；若没有这行代码，重启后的 agent 无法收束旧任务。
            persisted_record = agent.task_registry.stop_task(task_id, "任务已请求停止。原因：(持久任务恢复停止)")  # 新增代码+DurableTaskRegistry: 标记持久任务 stopped；若没有这行代码，旧 running 状态会一直存在。
        except KeyError:  # 新增代码+DurableTaskRegistry: 持久登记表也找不到时返回旧错误；若没有这行代码，未知 id 会抛异常。
            return f"task_stop 失败：未知 task_id：{task_id}"  # 修改代码+DurableTaskRegistry: 返回清楚未知任务错误；若省略: 模型难以判断是否需要重新创建任务
        return f"task_stop 成功：task_id={task_id} 已标记为 {persisted_record.status}。\n原因：{persisted_record.error or '(未提供)'}"  # 新增代码+DurableTaskRegistry: 返回持久任务停止结果；若没有这行代码，跨进程 stop 没有可读反馈。
    reason = str(arguments.get("reason", "") or "").strip()  # 新增代码+TaskLifecycle: 读取可选停止原因；若省略: 停止记录缺少用户或模型意图
    if task_record.status == "completed":  # 新增代码+TaskLifecycle: 已完成任务无需停止；若省略: 可能把完成任务错误改成 stopped
        return f"task_stop 成功：task_id={task_id} 已经完成，无需停止。\n输出可用 task_output 查看。"  # 新增代码+TaskLifecycle: 返回已完成边界说明；若省略: 用户不知道 stop 没有改变任务
    if task_record.status in {"failed", "stopped"}:  # 新增代码+TaskLifecycle: 已失败或已停止任务无需重复停止；若省略: 重复停止会让状态语义混乱
        return f"task_stop 成功：task_id={task_id} 当前状态为 {task_record.status}，无需重复停止。"  # 新增代码+TaskLifecycle: 返回幂等停止说明；若省略: 模型可能继续重复调用 stop
    if task_record.stop_event is not None:  # 新增代码+AsyncTask: 如果这是带取消信号的后台任务；若省略: task_stop 无法通知后台子 agent 协作停止
        task_record.stop_event.set()  # 新增代码+AsyncTask: 置位取消信号；若省略: 后台子 agent 只能等自然结束
    task_record.stop_requested = True  # 新增代码+TaskLifecycle: 记录停止请求；若省略: task_output 无法反映用户取消意图
    task_record.status = "stopped"  # 新增代码+TaskLifecycle: 把未完成任务标记为 stopped；若省略: 任务会继续显示 running/pending
    task_record.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+TaskLifecycle: 保存停止时间；若省略: 查询结果缺少停止发生时间
    task_record.error = f"任务已请求停止。原因：{reason or '(未提供)'}"  # 新增代码+TaskLifecycle: 保存停止原因到错误/状态文本；若省略: task_output 看不到为什么停止
    agent.task_registry.stop_task(task_id, task_record.error)  # 新增代码+DurableTaskRegistry: 同步把停止状态写入持久登记表；若没有这行代码，新 agent 实例仍会看到旧 running 状态。
    return f"task_stop 成功：task_id={task_id} 已标记为 stopped。\n原因：{reason or '(未提供)'}"  # 修改代码+TaskAgentToolsSplit: 返回停止成功说明；若没有这行代码，模型不知道停止请求是否生效。

def task_list(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TaskManagement: 执行 task_list 工具并返回子任务总览；若省略: 模型无法查看多个子任务的统一列表
    raw_status = str(arguments.get("status", "") or "").strip().lower()  # 新增代码+TaskManagement: 读取并标准化可选状态筛选；若省略: running/completed 等筛选无法生效
    allowed_statuses = {"all", "pending", "running", "completed", "failed", "stopped"}  # 新增代码+TaskManagement: 定义允许筛选的任务状态；若省略: 模型传错状态时无法给出清楚边界
    if raw_status and raw_status not in allowed_statuses:  # 新增代码+TaskManagement: 检查状态筛选是否有效；若省略: 拼写错误会默默返回空列表
        return f"task_list 失败：未知 status：{raw_status}，可选值为 all/pending/running/completed/failed/stopped。"  # 新增代码+TaskManagement: 返回可恢复的状态错误；若省略: 模型难以修正筛选参数
    max_results = search_tools_from_tools.tool_search_max_results(arguments.get("max_results"))  # 修改代码+AgentPyCompatWrapperRemovalL2: 直接复用 tools.search 的 1 到 20 结果数限制；若没有这行代码，删除 agent.py 旧包装后 task_list 会断开
    persisted_records = agent.task_registry.list_tasks()  # 修改代码+DurableTaskTools: 优先从持久 task registry 读取任务；若没有这行代码，重启后的 agent 会看不到旧任务。
    persisted_ids = {record.task_id for record in persisted_records}  # 新增代码+DurableTaskTools: 记录已经从磁盘恢复的 task_id；若没有这行代码，内存和磁盘任务可能重复显示。
    memory_only_records = [record for record in agent.task_runs.values() if record.task_id not in persisted_ids]  # 新增代码+DurableTaskTools: 只补充尚未落盘的内存任务；若没有这行代码，极端内存任务会从列表里消失。
    all_records = [*persisted_records, *memory_only_records]  # 修改代码+DurableTaskTools: 合并持久任务和内存兜底任务；若没有这行代码，task_list 无法同时兼容重启恢复和当前进程缓存。
    if not all_records:  # 新增代码+TaskManagement: 处理尚未创建任何 task 的情况；若省略: 空列表会返回不清楚的标题
        return "task_list 成功：当前没有子任务记录。"  # 新增代码+TaskManagement: 明确说明没有任务；若省略: 模型可能误以为工具失败
    selected_records = [record for record in all_records if not raw_status or raw_status == "all" or record.status == raw_status]  # 新增代码+TaskManagement: 按状态筛选任务；若省略: status 参数不会影响结果
    if not selected_records:  # 新增代码+TaskManagement: 处理筛选后没有匹配任务的情况；若省略: 空筛选结果难以和无任务区分
        return f"task_list 成功：共有 {len(all_records)} 个子任务，但没有 status={raw_status} 的记录。"  # 新增代码+TaskManagement: 返回筛选为空的可读说明；若省略: 模型不知道是筛选太窄还是任务不存在
    visible_records = selected_records[:max_results]  # 新增代码+TaskManagement: 截取允许返回的任务数量；若省略: 多任务列表可能过长
    filter_text = raw_status or "all"  # 新增代码+TaskManagement: 生成用于标题展示的筛选文本；若省略: 返回标题无法说明当前筛选条件
    lines = [f"task_list 成功：共有 {len(all_records)} 个子任务，status={filter_text} 匹配 {len(selected_records)} 个，显示前 {len(visible_records)} 个。"]  # 新增代码+TaskManagement: 构造列表标题；若省略: 模型不知道总数、筛选数和截断情况
    for index, task_record in enumerate(visible_records, start=1):  # 新增代码+TaskManagement: 逐条格式化任务摘要；若省略: 任务记录无法变成人类和模型可读文本
        prompt_preview = " ".join(task_record.prompt.split())  # 新增代码+TaskManagement: 把多行 prompt 压成单行摘要；若省略: 列表输出会被长 prompt 撑乱
        if len(prompt_preview) > 80:  # 新增代码+TaskManagement: 判断 prompt 摘要是否过长；若省略: 长任务目标会让列表难以扫描
            prompt_preview = prompt_preview[:80] + "..."  # 新增代码+TaskManagement: 截断过长 prompt 摘要；若省略: 列表可能占用过多上下文
        task_metadata = getattr(task_record, "metadata", {}) if isinstance(getattr(task_record, "metadata", {}), dict) else {}  # 新增代码+DurableTaskTools: 读取持久任务 metadata；若没有这行代码，重启后的 label/notes 没有来源。
        task_label = getattr(task_record, "label", "") or str(task_metadata.get("label", ""))  # 新增代码+DurableTaskTools: 同时兼容内存 TaskRun 和持久 TaskRecord 标签；若没有这行代码，task_list 会因对象字段不同而崩溃。
        lines.append(f"{index}. task_id={task_record.task_id} status={task_record.status} background={'true' if task_record.background else 'false'} label={task_label or '(无标签)'}")  # 修改代码+DurableTaskTools: 输出任务 id、状态、后台标记和持久标签；若没有这行代码，模型无法快速选择跨实例任务。
        lines.append(f"   prompt={prompt_preview or '(无 prompt)'}")  # 新增代码+TaskManagement: 输出任务目标摘要；若省略: 任务列表只能看到 id 而不知任务内容
        lines.append(f"   created_at={task_record.created_at} completed_at={task_record.completed_at or '(未完成)'}")  # 新增代码+TaskManagement: 输出创建和完成时间；若省略: 模型难以判断任务新旧和是否结束
    return "\n".join(lines)  # 修改代码+TaskAgentToolsSplit: 返回完整任务列表文本；若没有这行代码，task_list 没有可读输出。

def task_get(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TaskManagement: 执行 task_get 工具并返回单个子任务详情；若省略: 模型无法读取任务管理元信息
    task_id = str(arguments.get("task_id", "") or "").strip()  # 新增代码+TaskManagement: 读取并清理 task_id 参数；若省略: 工具不知道要查询哪个任务
    if not task_id:  # 新增代码+TaskManagement: 检查 task_id 是否为空；若省略: 空查询会产生模糊未知任务错误
        return "task_get 失败：缺少 task_id 参数。"  # 新增代码+TaskManagement: 返回清楚缺参错误；若省略: 模型难以修正 task_get 调用
    task_record = agent.task_runs.get(task_id)  # 新增代码+TaskManagement: 从内存表查找任务记录；若省略: 工具无法定位任务详情
    if task_record is None:  # 新增代码+TaskManagement: 处理未知 task_id；若省略: 访问 None 会抛异常
        try:  # 修改代码+DurableTaskTools: 内存没有时读取持久 task registry；若没有这行代码，重启后的 task_get 会误报未知任务。
            task_record = agent.task_registry.get_task(task_id)  # 新增代码+DurableTaskTools: 从磁盘恢复目标任务；若没有这行代码，旧任务详情无法跨进程读取。
        except KeyError:  # 新增代码+DurableTaskTools: 持久 registry 也没有该任务时才返回未知；若没有这行代码，真实未知 id 会抛出底层异常。
            return f"task_get 失败：未知 task_id：{task_id}"  # 修改代码+DurableTaskTools: 返回清楚未知任务错误；若没有这行代码，模型难以判断是否需要先 task_list。
    max_chars = parse_max_chars_value(arguments.get("max_chars"))  # 修改代码+AgentPySplitPhase15B2: 直接使用公共解析函数，不再依赖 agent.py 薄包装；若没有这行代码，删除 `旧输出长度薄包装` 后 task_get 会断开。
    task_metadata = getattr(task_record, "metadata", {}) if isinstance(getattr(task_record, "metadata", {}), dict) else {}  # 新增代码+DurableTaskTools: 读取持久任务 metadata；若没有这行代码，label/notes/stop_requested 跨实例不可见。
    task_label = getattr(task_record, "label", "") or str(task_metadata.get("label", ""))  # 新增代码+DurableTaskTools: 兼容内存 TaskRun 和持久 TaskRecord 标签；若没有这行代码，task_get 会因为字段差异失败。
    task_notes = getattr(task_record, "notes", "") or str(task_metadata.get("notes", ""))  # 新增代码+DurableTaskTools: 兼容内存 TaskRun 和持久 TaskRecord 备注；若没有这行代码，跨实例交接说明会丢失。
    stop_requested = bool(getattr(task_record, "stop_requested", False) or task_metadata.get("stop_requested", False))  # 新增代码+DurableTaskTools: 兼容两种任务对象的停止标记；若没有这行代码，持久任务详情会因缺字段崩溃。
    output_text = task_record.output or task_record.error or agent.task_registry.output_store.tail(task_id, max_chars=max_chars) or "(暂无输出)"  # 修改代码+DurableTaskTools: 优先读摘要并兜底输出文件；若没有这行代码，持久任务的大输出可能显示为空。
    truncated_output = output_text[:max_chars]  # 新增代码+TaskManagement: 按 max_chars 截断输出；若省略: 长输出不可控
    if len(output_text) > max_chars:  # 新增代码+TaskManagement: 判断输出是否被截断；若省略: 模型不知道结果是否完整
        truncated_output += "\n...[task 输出过长，已截断]..."  # 新增代码+TaskManagement: 添加截断提示；若省略: 模型可能误以为拿到完整输出
    lines = [f"task_get 成功：task_id={task_id}"]  # 新增代码+TaskManagement: 构造详情标题；若省略: 返回文本缺少目标任务 id
    lines.append(f"status={task_record.status}")  # 新增代码+TaskManagement: 输出任务状态；若省略: 模型无法判断任务是否完成
    lines.append(f"background={'true' if task_record.background else 'false'}")  # 新增代码+TaskManagement: 输出后台标记；若省略: 模型无法判断任务是否可能异步更新
    lines.append(f"label={task_label or '(无标签)'}")  # 修改代码+DurableTaskTools: 输出内存或持久标签；若没有这行代码，重启后的 task_update 标签无法被读回。
    lines.append(f"notes={task_notes or '(无备注)'}")  # 修改代码+DurableTaskTools: 输出内存或持久备注；若没有这行代码，重启后的 task_update 备注无法被读回。
    lines.append(f"prompt={task_record.prompt}")  # 新增代码+TaskManagement: 输出原始任务 prompt；若省略: 主 agent 无法追溯子任务目标
    lines.append(f"created_at={task_record.created_at}")  # 新增代码+TaskManagement: 输出创建时间；若省略: 任务详情缺少时间线起点
    lines.append(f"completed_at={task_record.completed_at or '(未完成)'}")  # 新增代码+TaskManagement: 输出完成时间或未完成占位；若省略: 模型难以区分 running 和没有时间字段
    lines.append(f"allowed_tools={', '.join(sorted(task_record.allowed_tool_names)) or '(无工具)'}")  # 新增代码+TaskManagement: 输出子 agent 工具边界；若省略: 审查子任务权限范围会更困难
    lines.append(f"max_turns={task_record.max_turns}")  # 新增代码+TaskManagement: 输出子 agent 最大轮次；若省略: 模型无法知道子任务执行约束
    lines.append(f"stop_requested={'true' if stop_requested else 'false'}")  # 修改代码+DurableTaskTools: 输出兼容持久任务的停止标记；若没有这行代码，TaskRecord 没有 stop_requested 字段时会崩溃。
    lines.append(f"输出：\n{truncated_output}")  # 新增代码+TaskManagement: 输出任务结果或错误摘要；若省略: 详情读取仍要再调用 task_output 才有结果
    return "\n".join(lines)  # 修改代码+TaskAgentToolsSplit: 返回完整任务详情文本；若没有这行代码，task_get 没有可读输出。

def task_update(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TaskManagement: 执行 task_update 工具并更新任务管理元信息；若省略: 模型无法为任务补标签或备注
    task_id = str(arguments.get("task_id", "") or "").strip()  # 新增代码+TaskManagement: 读取并清理 task_id 参数；若省略: 工具不知道要更新哪个任务
    if not task_id:  # 新增代码+TaskManagement: 检查 task_id 是否为空；若省略: 空更新会产生模糊未知任务错误
        return "task_update 失败：缺少 task_id 参数。"  # 新增代码+TaskManagement: 返回清楚缺参错误；若省略: 模型难以修正 task_update 调用
    task_record = agent.task_runs.get(task_id)  # 新增代码+TaskManagement: 从内存表查找任务记录；若省略: 工具无法定位任务
    persisted_record = None  # 新增代码+DurableTaskTools: 准备保存持久任务记录引用；若没有这行代码，跨实例更新无法区分是否从磁盘恢复。
    if task_record is None:  # 新增代码+TaskManagement: 处理未知 task_id；若省略: 访问 None 会抛异常
        try:  # 修改代码+DurableTaskTools: 内存没有时尝试读取持久 task registry；若没有这行代码，重启后的 task_update 会误报未知任务。
            persisted_record = agent.task_registry.get_task(task_id)  # 新增代码+DurableTaskTools: 从磁盘恢复目标任务；若没有这行代码，旧任务元信息不能跨实例修改。
        except KeyError:  # 新增代码+DurableTaskTools: 持久 registry 也没有该任务时才返回未知；若没有这行代码，真实未知 id 会抛底层异常。
            return f"task_update 失败：未知 task_id：{task_id}"  # 修改代码+DurableTaskTools: 返回清楚未知任务错误；若没有这行代码，模型难以判断是否需要先 task_list。
    has_label = "label" in arguments  # 新增代码+TaskManagement: 判断调用是否显式提供 label；若省略: 无法区分省略字段和清空标签
    has_notes = "notes" in arguments  # 新增代码+TaskManagement: 判断调用是否显式提供 notes；若省略: 无法区分省略字段和清空备注
    if not has_label and not has_notes:  # 新增代码+TaskManagement: 要求至少更新一个管理字段；若省略: 空更新会返回成功但什么也没做
        return "task_update 失败：请至少提供 label 或 notes。"  # 新增代码+TaskManagement: 返回清楚空更新错误；若省略: 模型难以知道必须补哪个字段
    if persisted_record is not None:  # 新增代码+DurableTaskTools: 处理重启后只存在于持久 registry 的任务；若没有这行代码，跨实例更新仍无法落盘。
        if has_label:  # 新增代码+DurableTaskTools: 调用方提供 label 时才更新持久标签；若没有这行代码，无法区分不改和清空标签。
            persisted_record.metadata["label"] = str(arguments.get("label", "") or "").strip()  # 新增代码+DurableTaskTools: 把 label 写入 metadata；若没有这行代码，TaskRecord 没有 label 字段会无法保存标签。
        if has_notes:  # 新增代码+DurableTaskTools: 调用方提供 notes 时才更新持久备注；若没有这行代码，无法区分不改和清空备注。
            persisted_record.metadata["notes"] = str(arguments.get("notes", "") or "").strip()  # 新增代码+DurableTaskTools: 把 notes 写入 metadata；若没有这行代码，TaskRecord 没有 notes 字段会无法保存备注。
        agent.task_registry.save_task(persisted_record)  # 新增代码+DurableTaskTools: 保存持久任务元信息；若没有这行代码，更新只在本次调用对象里生效。
        return f"task_update 成功：task_id={task_id}\nlabel={persisted_record.metadata.get('label') or '(无标签)'}\nnotes={persisted_record.metadata.get('notes') or '(无备注)'}"  # 新增代码+DurableTaskTools: 返回持久更新结果；若没有这行代码，模型无法确认跨实例更新是否生效。
    if has_label:  # 新增代码+TaskManagement: 如果调用提供了 label 字段；若省略: 标签更新不会执行
        task_record.label = str(arguments.get("label", "") or "").strip()  # 新增代码+TaskManagement: 写入清理后的标签，空字符串表示清空；若省略: 任务列表无法显示新标签
    if has_notes:  # 新增代码+TaskManagement: 如果调用提供了 notes 字段；若省略: 备注更新不会执行
        task_record.notes = str(arguments.get("notes", "") or "").strip()  # 新增代码+TaskManagement: 写入清理后的备注，空字符串表示清空；若省略: 任务详情无法显示新备注
    try:  # 新增代码+DurableTaskTools: 同步更新内存任务对应的持久记录；若没有这行代码，同一实例更新后重启会丢失 label/notes。
        registry_record = agent.task_registry.get_task(task_id)  # 新增代码+DurableTaskTools: 读取持久任务记录；若没有这行代码，无法把内存元信息写回磁盘。
        if has_label:  # 新增代码+DurableTaskTools: 只同步调用方显式提供的 label；若没有这行代码，可能误覆盖已有持久标签。
            registry_record.metadata["label"] = task_record.label  # 新增代码+DurableTaskTools: 把内存标签写入持久 metadata；若没有这行代码，task_list 重启后看不到标签。
        if has_notes:  # 新增代码+DurableTaskTools: 只同步调用方显式提供的 notes；若没有这行代码，可能误覆盖已有持久备注。
            registry_record.metadata["notes"] = task_record.notes  # 新增代码+DurableTaskTools: 把内存备注写入持久 metadata；若没有这行代码，task_get 重启后看不到备注。
        agent.task_registry.save_task(registry_record)  # 新增代码+DurableTaskTools: 保存持久任务记录；若没有这行代码，更新不会跨进程保留。
    except KeyError:  # 新增代码+DurableTaskTools: 兼容极端内存任务尚未落盘的情况；若没有这行代码，老测试或手工记录会被打断。
        pass  # 新增代码+DurableTaskTools: 没有持久记录时只保留内存更新；若没有这行代码，except 分支语法不完整。
    return f"task_update 成功：task_id={task_id}\nlabel={task_record.label or '(无标签)'}\nnotes={task_record.notes or '(无备注)'}"  # 修改代码+TaskAgentToolsSplit: 返回更新后的任务标签和备注；若没有这行代码，模型无法确认元信息是否保存。

def team_create(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TeamCommunication: 执行 team_create 工具并登记教学版 peer；若省略: 模型无法创建团队成员记录
    name = str(arguments.get("name", "") or "").strip()  # 新增代码+TeamCommunication: 读取并清理 peer 名称；若省略: peer 记录缺少可读名称
    if not name:  # 新增代码+TeamCommunication: 检查名称是否为空；若省略: 空名称 peer 会让 list_peers 难以阅读
        return "team_create 失败：缺少非空 name 参数。"  # 新增代码+TeamCommunication: 返回清楚缺参错误；若省略: 模型难以修正 team_create 调用
    role = str(arguments.get("role", "") or "peer").strip() or "peer"  # 新增代码+TeamCommunication: 读取角色并在省略时使用 peer；若省略: 成员职责字段可能为空
    notes = str(arguments.get("notes", "") or "").strip()  # 新增代码+TeamCommunication: 读取可选备注；若省略: team_create 无法保存职责边界说明
    peer_id = f"peer_{secrets.token_hex(6)}"  # 新增代码+TeamCommunication: 生成短且唯一的 peer id；若省略: send_message/list_peers 无法稳定引用成员
    peer_record = TeamPeer(peer_id=peer_id, name=name, role=role, status="idle", notes=notes, created_at=time.strftime("%Y-%m-%d %H:%M:%S"))  # 新增代码+TeamCommunication: 创建 peer 记录并标记为空闲；若省略: team_create 只会返回文本但不会留下状态
    agent.team_peers[peer_id] = peer_record  # 新增代码+TeamCommunication: 把 peer 记录放入当前 agent 进程内登记表；若省略: 后续 send_message/list_peers 找不到这个 peer
    agent.team_registry.save_peer(peer_record)  # 新增代码+DurableTeamRegistry: 把 peer 同步写入持久登记表；若没有这行代码，新 agent 实例无法列出这个 peer。
    return f"team_create 成功：已创建教学版 peer。\npeer_id={peer_id}\nname={peer_record.name}\nrole={peer_record.role}\nstatus={peer_record.status}\nnotes={peer_record.notes or '(无备注)'}"  # 修改代码+TaskAgentToolsSplit: 返回新 peer 的关键信息；若没有这行代码，模型无法继续引用 peer_id。

def send_message(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TeamCommunication: 执行 send_message 工具并把消息放入 peer inbox；若省略: peer 之间无法建立教学版通信记录
    peer_id = str(arguments.get("peer_id", "") or "").strip()  # 新增代码+TeamCommunication: 读取并清理目标 peer_id；若省略: 工具不知道要发给谁
    if not peer_id:  # 新增代码+TeamCommunication: 检查 peer_id 是否为空；若省略: 空目标会产生模糊未知 peer 错误
        return "send_message 失败：缺少 peer_id 参数。"  # 新增代码+TeamCommunication: 返回清楚缺参错误；若省略: 模型难以修正 send_message 调用
    peer_record = agent.team_peers.get(peer_id)  # 新增代码+TeamCommunication: 从登记表查找目标 peer；若省略: 工具无法定位收件箱
    if peer_record is None:  # 新增代码+TeamCommunication: 处理未知 peer_id；若省略: 访问 None 会抛异常
        try:  # 修改代码+DurableTeamRegistry: 内存没有时尝试从持久 team registry 恢复；若没有这行代码，重启后的 send_message 会误报未知 peer。
            peer_record = agent.team_registry.get_peer(peer_id)  # 新增代码+DurableTeamRegistry: 从磁盘恢复 peer；若没有这行代码，旧 peer 无法继续接收消息。
            agent.team_peers[peer_id] = peer_record  # 新增代码+DurableTeamRegistry: 把恢复的 peer 放回内存缓存；若没有这行代码，本次后续操作还会反复读磁盘。
        except KeyError:  # 新增代码+DurableTeamRegistry: 持久 registry 也没有该 peer 时才返回未知；若没有这行代码，真实未知 id 会抛底层异常。
            return f"send_message 失败：未知 peer_id：{peer_id}，请先调用 team_create 或 list_peers。"  # 修改代码+DurableTeamRegistry: 返回可恢复建议；若没有这行代码，模型不知道该先创建或查看 peer。
    message = str(arguments.get("message", arguments.get("content", "")) or "").strip()  # 修改代码+DurableTeamRegistry: 同时兼容 message 和 content 参数；若没有这行代码，控制器或模型使用 content 会被误判缺参。
    if not message:  # 新增代码+TeamCommunication: 检查消息正文是否为空；若省略: 空消息会污染 peer inbox
        return "send_message 失败：缺少非空 message 参数。"  # 新增代码+TeamCommunication: 返回清楚缺参错误；若省略: 模型难以修正消息内容
    sender = str(arguments.get("sender", "") or "main").strip() or "main"  # 新增代码+TeamCommunication: 读取发送者并默认使用 main；若省略: 消息来源字段可能为空
    message_id = f"msg_{secrets.token_hex(6)}"  # 新增代码+TeamCommunication: 生成短且唯一的消息 id；若省略: 用户无法审计具体消息
    peer_record.inbox.append(TeamMessage(message_id=message_id, sender=sender, content=message, created_at=time.strftime("%Y-%m-%d %H:%M:%S")))  # 新增代码+TeamCommunication: 把消息追加到目标 peer inbox；若省略: send_message 不会留下任何可查询记录
    peer_record.status = "active"  # 新增代码+TeamCommunication: 收到消息后把 peer 标记为 active；若省略: list_peers 无法反映该 peer 已有待处理消息
    agent.team_registry.save_peer(peer_record)  # 新增代码+DurableTeamRegistry: 保存新增消息和 active 状态；若没有这行代码，重启后 peer inbox 会丢失。
    return f"send_message 成功：消息已进入 peer inbox。\npeer_id={peer_id}\nmessage_id={message_id}\ninbox_count={len(peer_record.inbox)}"  # 修改代码+TaskAgentToolsSplit: 返回消息 id 和 inbox 数量；若没有这行代码，模型无法确认消息是否送达。

def list_peers(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TeamCommunication: 执行 list_peers 工具并返回 peer 总览；若省略: 模型无法查看当前团队成员
    role_filter = str(arguments.get("role", "") or "").strip().lower()  # 新增代码+TeamCommunication: 读取并标准化可选角色筛选；若省略: role 参数不会影响列表
    status_filter = str(arguments.get("status", "") or "").strip().lower()  # 新增代码+TeamCommunication: 读取并标准化可选状态筛选；若省略: status 参数不会影响列表
    max_results = search_tools_from_tools.tool_search_max_results(arguments.get("max_results"))  # 修改代码+AgentPyCompatWrapperRemovalL2: 直接复用 tools.search 的 1 到 20 结果数限制；若没有这行代码，删除 agent.py 旧包装后 list_peers 会断开
    persisted_peers = agent.team_registry.list_peers()  # 修改代码+DurableTeamRegistry: 优先从持久 team registry 读取 peer；若没有这行代码，重启后的 list_peers 会看不到旧成员。
    persisted_peer_ids = {peer.peer_id for peer in persisted_peers}  # 新增代码+DurableTeamRegistry: 记录已经从磁盘恢复的 peer_id；若没有这行代码，内存和磁盘 peer 可能重复显示。
    memory_only_peers = [peer for peer in agent.team_peers.values() if peer.peer_id not in persisted_peer_ids]  # 新增代码+DurableTeamRegistry: 只补充还没落盘的内存 peer；若没有这行代码，极端临时 peer 会从列表里消失。
    all_peers = [*persisted_peers, *memory_only_peers]  # 修改代码+DurableTeamRegistry: 合并持久 peer 和内存兜底 peer；若没有这行代码，team 视图无法兼容恢复和当前进程缓存。
    if not all_peers:  # 新增代码+TeamCommunication: 处理尚未创建 peer 的情况；若省略: 空列表会返回不清楚的标题
        return "list_peers 成功：当前没有 peer 记录。"  # 新增代码+TeamCommunication: 明确说明没有成员；若省略: 模型可能误以为工具失败
    selected_peers = [peer for peer in all_peers if (not role_filter or peer.role.lower() == role_filter) and (not status_filter or peer.status.lower() == status_filter)]  # 新增代码+TeamCommunication: 按角色和状态筛选 peer；若省略: 筛选参数不会生效
    if not selected_peers:  # 新增代码+TeamCommunication: 处理筛选后没有匹配 peer 的情况；若省略: 空筛选结果难以和无 peer 区分
        return f"list_peers 成功：共有 {len(all_peers)} 个 peer，但没有匹配 role={role_filter or 'all'} status={status_filter or 'all'} 的记录。"  # 新增代码+TeamCommunication: 返回筛选为空说明；若省略: 模型不知道是筛选太窄还是成员不存在
    visible_peers = selected_peers[:max_results]  # 新增代码+TeamCommunication: 截取允许返回的 peer 数量；若省略: 多成员列表可能过长
    lines = [f"list_peers 成功：共有 {len(all_peers)} 个 peer，匹配 {len(selected_peers)} 个，显示前 {len(visible_peers)} 个。"]  # 新增代码+TeamCommunication: 构造列表标题；若省略: 模型不知道总数、筛选数和截断情况
    for index, peer in enumerate(visible_peers, start=1):  # 新增代码+TeamCommunication: 逐条格式化 peer 摘要；若省略: peer 记录无法变成人类和模型可读文本
        pending_count = sum(1 for message in peer.inbox if not message.acknowledged_at)  # 新增代码+TeamCommunicationLifecycle: 统计未确认消息数量；若省略: 主 agent 无法判断 peer inbox 还有多少待处理消息
        bound_task_id = peer.bound_task_id or "(无)"  # 新增代码+TeamTaskBinding: 生成 peer 绑定 task id 的展示文本；若省略: list_peers 无法显示 peer 正在承接哪个后台任务
        bound_task_record = agent.task_runs.get(peer.bound_task_id) if peer.bound_task_id else None  # 新增代码+TeamTaskBinding: 从内存任务表读取绑定 task 当前记录；若省略: team 视图无法动态反映当前进程 task 状态
        if bound_task_record is None and peer.bound_task_id:  # 新增代码+DurableTeamRegistry: 内存找不到绑定任务时尝试持久 task registry；若没有这行代码，重启后 team 绑定任务会显示 missing。
            try:  # 新增代码+DurableTeamRegistry: 持久任务查询可能找不到目标；若没有这行代码，旧 peer 绑定坏 task 会让列表失败。
                bound_task_record = agent.task_registry.get_task(peer.bound_task_id)  # 新增代码+DurableTeamRegistry: 从磁盘读取绑定 task 状态；若没有这行代码，team 视图无法跨实例反映 task 状态。
            except KeyError:  # 新增代码+DurableTeamRegistry: 绑定任务确实不存在时保持 missing；若没有这行代码，异常会打断 list_peers。
                bound_task_record = None  # 新增代码+DurableTeamRegistry: 明确保持未找到状态；若没有这行代码，后续变量语义不清楚。
        task_status = bound_task_record.status if bound_task_record is not None else ("missing" if peer.bound_task_id else "(无)")  # 新增代码+TeamTaskBinding: 计算绑定 task 当前状态或缺失占位；若省略: 用户无法判断 peer 任务是否 running/stopped/completed
        latest_message = peer.inbox[-1].content if peer.inbox else "(无消息)"  # 新增代码+TeamCommunication: 读取最新消息摘要或空占位；若省略: list_peers 无法提示最近通信内容
        latest_preview = " ".join(latest_message.split())  # 新增代码+TeamCommunication: 把最新消息压成单行摘要；若省略: 多行消息会打乱列表格式
        if len(latest_preview) > 80:  # 新增代码+TeamCommunication: 判断消息摘要是否过长；若省略: 长消息会让列表难以扫描
            latest_preview = latest_preview[:80] + "..."  # 新增代码+TeamCommunication: 截断过长消息摘要；若省略: 列表可能占用过多上下文
        lines.append(f"{index}. peer_id={peer.peer_id} name={peer.name} role={peer.role} status={peer.status} inbox_count={len(peer.inbox)} pending_count={pending_count} bound_task_id={bound_task_id} task_status={task_status}")  # 修改代码+TeamTaskBinding: 输出 peer 核心元信息、消息数和绑定任务状态；若省略: 模型无法从 team 视图追踪 peer 的后台 task
        lines.append(f"   notes={peer.notes or '(无备注)'}")  # 新增代码+TeamCommunication: 输出 peer 职责备注；若省略: 主 agent 难以理解成员边界
        lines.append(f"   created_at={peer.created_at}")  # 新增代码+TeamCommunication: 输出 peer 创建时间；若省略: 多 peer 场景缺少时间线
        lines.append(f"   latest_message={latest_preview}")  # 新增代码+TeamCommunication: 输出最新消息摘要；若省略: 模型需要额外工具才能知道 inbox 大致内容
    return "\n".join(lines)  # 修改代码+TaskAgentToolsSplit: 返回完整 peer 列表文本；若没有这行代码，list_peers 没有可读输出。

def read_peer_messages(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TeamCommunicationLifecycle: 执行 read_peer_messages 工具并读取 peer inbox；若省略: 模型无法查看 peer 收到的消息详情
    peer_id = str(arguments.get("peer_id", "") or "").strip()  # 新增代码+TeamCommunicationLifecycle: 读取并清理目标 peer_id；若省略: 工具不知道要读取哪个 peer
    if not peer_id:  # 新增代码+TeamCommunicationLifecycle: 检查 peer_id 是否为空；若省略: 空目标会产生模糊未知 peer 错误
        return "read_peer_messages 失败：缺少 peer_id 参数。"  # 新增代码+TeamCommunicationLifecycle: 返回清楚缺参错误；若省略: 模型难以修正 read_peer_messages 调用
    peer_record = agent.team_peers.get(peer_id)  # 新增代码+TeamCommunicationLifecycle: 从登记表查找目标 peer；若省略: 工具无法定位 inbox
    if peer_record is None:  # 新增代码+TeamCommunicationLifecycle: 处理未知 peer_id；若省略: 访问 None 会抛异常
        try:  # 修改代码+DurableTeamRegistry: 内存没有时尝试从持久 registry 恢复；若没有这行代码，重启后的 read_peer_messages 会误报未知 peer。
            peer_record = agent.team_registry.get_peer(peer_id)  # 新增代码+DurableTeamRegistry: 从磁盘恢复 peer 和 inbox；若没有这行代码，旧消息无法跨实例读取。
            agent.team_peers[peer_id] = peer_record  # 新增代码+DurableTeamRegistry: 把恢复的 peer 放回内存缓存；若没有这行代码，本次后续操作会反复读磁盘。
        except KeyError:  # 新增代码+DurableTeamRegistry: 持久 registry 也没有该 peer 时才返回未知；若没有这行代码，真实未知 id 会抛底层异常。
            return f"read_peer_messages 失败：未知 peer_id：{peer_id}，请先调用 team_create 或 list_peers。"  # 修改代码+DurableTeamRegistry: 返回可恢复建议；若没有这行代码，模型不知道该先创建或查看 peer。
    include_acknowledged = arguments.get("include_acknowledged") is True  # 新增代码+TeamCommunicationLifecycle: 仅在显式 true 时包含已确认消息；若省略: 默认读取会混入已处理历史
    max_results = search_tools_from_tools.tool_search_max_results(arguments.get("max_results"))  # 修改代码+AgentPyCompatWrapperRemovalL2: 直接复用 tools.search 的 1 到 20 结果数限制；若没有这行代码，删除 agent.py 旧包装后 read_peer_messages 会断开
    pending_count = sum(1 for message in peer_record.inbox if not message.acknowledged_at)  # 新增代码+TeamCommunicationLifecycle: 统计当前待确认消息数；若省略: 读取结果缺少处理压力摘要
    selected_messages = [message for message in peer_record.inbox if include_acknowledged or not message.acknowledged_at]  # 新增代码+TeamCommunicationLifecycle: 按是否包含已确认历史筛选消息；若省略: include_acknowledged 参数不会生效
    visible_messages = selected_messages[:max_results]  # 新增代码+TeamCommunicationLifecycle: 截取允许返回的消息数量；若省略: 消息太多会让输出过长
    if not visible_messages:  # 新增代码+TeamCommunicationLifecycle: 处理筛选后没有消息的情况；若省略: 空结果难以和工具失败区分
        return f"read_peer_messages 成功：peer_id={peer_id} inbox_count={len(peer_record.inbox)} pending_count={pending_count}，没有匹配消息。"  # 新增代码+TeamCommunicationLifecycle: 返回空结果摘要；若省略: 模型不知道 inbox 是否为空或只是筛选为空
    lines = [f"read_peer_messages 成功：peer_id={peer_id} inbox_count={len(peer_record.inbox)} pending_count={pending_count} 显示前 {len(visible_messages)} 条。"]  # 新增代码+TeamCommunicationLifecycle: 构造读取结果标题；若省略: 模型不知道返回数量和待处理数量
    for index, message_record in enumerate(visible_messages, start=1):  # 新增代码+TeamCommunicationLifecycle: 逐条格式化消息；若省略: 消息记录无法变成人类和模型可读文本
        message_preview = " ".join(message_record.content.split())  # 新增代码+TeamCommunicationLifecycle: 把消息正文压成单行摘要；若省略: 多行消息会打乱列表格式
        if len(message_preview) > 200:  # 新增代码+TeamCommunicationLifecycle: 判断消息正文是否过长；若省略: 长消息会让读取结果难以扫描
            message_preview = message_preview[:200] + "..."  # 新增代码+TeamCommunicationLifecycle: 截断过长消息正文；若省略: 单条消息可能占用过多上下文
        acknowledged_text = "true" if message_record.acknowledged_at else "false"  # 新增代码+TeamCommunicationLifecycle: 把确认状态转成人类可读布尔文本；若省略: 模型难以判断消息是否已处理
        lines.append(f"{index}. message_id={message_record.message_id} sender={message_record.sender} created_at={message_record.created_at} acknowledged={acknowledged_text}")  # 新增代码+TeamCommunicationLifecycle: 输出消息元信息；若省略: 模型无法选择要确认的 message_id
        lines.append(f"   content={message_preview}")  # 新增代码+TeamCommunicationLifecycle: 输出消息正文摘要；若省略: 读取 inbox 看不到真正消息内容
        if message_record.acknowledged_at:  # 新增代码+TeamCommunicationLifecycle: 如果消息已经确认；若省略: 已确认消息缺少处理时间和备注
            lines.append(f"   acknowledged_at={message_record.acknowledged_at}")  # 新增代码+TeamCommunicationLifecycle: 输出确认时间；若省略: 用户无法审计消息何时处理
            lines.append(f"   ack_note={message_record.ack_note or '(无备注)'}")  # 新增代码+TeamCommunicationLifecycle: 输出确认备注；若省略: 用户无法看到处理说明
    return "\n".join(lines)  # 修改代码+TaskAgentToolsSplit: 返回完整 peer 消息列表文本；若没有这行代码，read_peer_messages 没有可读输出。

def ack_peer_message(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TeamCommunicationLifecycle: 执行 ack_peer_message 工具并确认一条消息；若省略: peer 消息无法标记已处理
    peer_id = str(arguments.get("peer_id", "") or "").strip()  # 新增代码+TeamCommunicationLifecycle: 读取并清理目标 peer_id；若省略: 工具不知道要操作哪个 peer
    if not peer_id:  # 新增代码+TeamCommunicationLifecycle: 检查 peer_id 是否为空；若省略: 空目标会产生模糊未知 peer 错误
        return "ack_peer_message 失败：缺少 peer_id 参数。"  # 新增代码+TeamCommunicationLifecycle: 返回清楚缺参错误；若省略: 模型难以修正 ack_peer_message 调用
    peer_record = agent.team_peers.get(peer_id)  # 新增代码+TeamCommunicationLifecycle: 从登记表查找目标 peer；若省略: 工具无法定位 inbox
    if peer_record is None:  # 新增代码+TeamCommunicationLifecycle: 处理未知 peer_id；若省略: 访问 None 会抛异常
        try:  # 修改代码+DurableTeamRegistry: 内存没有时尝试从持久 registry 恢复；若没有这行代码，重启后的 ack_peer_message 会误报未知 peer。
            peer_record = agent.team_registry.get_peer(peer_id)  # 新增代码+DurableTeamRegistry: 从磁盘恢复 peer 和 inbox；若没有这行代码，旧消息无法跨实例确认。
            agent.team_peers[peer_id] = peer_record  # 新增代码+DurableTeamRegistry: 把恢复的 peer 放回内存缓存；若没有这行代码，本次后续操作会反复读磁盘。
        except KeyError:  # 新增代码+DurableTeamRegistry: 持久 registry 也没有该 peer 时才返回未知；若没有这行代码，真实未知 id 会抛底层异常。
            return f"ack_peer_message 失败：未知 peer_id：{peer_id}，请先调用 team_create 或 list_peers。"  # 修改代码+DurableTeamRegistry: 返回可恢复建议；若没有这行代码，模型不知道该先创建或查看 peer。
    message_id = str(arguments.get("message_id", "") or "").strip()  # 新增代码+TeamCommunicationLifecycle: 读取并清理 message_id；若省略: 工具不知道要确认哪条消息
    if not message_id:  # 新增代码+TeamCommunicationLifecycle: 检查 message_id 是否为空；若省略: 空消息目标会导致确认语义模糊
        return "ack_peer_message 失败：缺少 message_id 参数。"  # 新增代码+TeamCommunicationLifecycle: 返回清楚缺参错误；若省略: 模型难以修正 message_id
    message_record = next((message for message in peer_record.inbox if message.message_id == message_id), None)  # 新增代码+TeamCommunicationLifecycle: 在 inbox 中查找目标消息；若省略: 工具无法定位具体消息
    if message_record is None:  # 新增代码+TeamCommunicationLifecycle: 处理未知 message_id；若省略: 访问 None 会抛异常
        return f"ack_peer_message 失败：peer_id={peer_id} 中没有 message_id={message_id}。"  # 新增代码+TeamCommunicationLifecycle: 返回清楚未知消息错误；若省略: 模型难以判断是否需要先 read_peer_messages
    note = str(arguments.get("note", "") or "").strip()  # 新增代码+TeamCommunicationLifecycle: 读取确认备注；若省略: 用户无法保存处理说明
    if not message_record.acknowledged_at:  # 新增代码+TeamCommunicationLifecycle: 只在尚未确认时写入确认时间；若省略: 重复确认会覆盖首次处理时间
        message_record.acknowledged_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+TeamCommunicationLifecycle: 保存首次确认时间；若省略: 审计时不知道消息何时处理
    if note:  # 新增代码+TeamCommunicationLifecycle: 如果调用提供了确认备注；若省略: 备注更新不会执行
        message_record.ack_note = note  # 新增代码+TeamCommunicationLifecycle: 保存确认备注；若省略: 用户提供的处理说明会丢失
    pending_count = sum(1 for message in peer_record.inbox if not message.acknowledged_at)  # 新增代码+TeamCommunicationLifecycle: 重新统计待确认消息数；若省略: 返回结果无法说明剩余处理量
    peer_record.status = peer_status_from_pending_count(pending_count)  # 修改代码+TasksSplit: 委托 tasks.team 根据待确认消息数计算 peer 状态；若没有这行代码，peer 状态规则仍会散在主文件。
    agent.team_registry.save_peer(peer_record)  # 新增代码+DurableTeamRegistry: 保存 ack 状态和 peer 状态；若没有这行代码，消息确认在重启后会丢失。
    return f"ack_peer_message 成功：peer_id={peer_id}\nmessage_id={message_id}\nacknowledged_at={message_record.acknowledged_at}\npending_count={pending_count}"  # 修改代码+TaskAgentToolsSplit: 返回确认结果和剩余待处理数量；若没有这行代码，模型无法知道消息是否已处理。

def team_delete(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TeamCommunicationLifecycle: 执行 team_delete 工具并删除教学版 peer；若省略: peer 记录无法回收
    peer_id = str(arguments.get("peer_id", "") or "").strip()  # 新增代码+TeamCommunicationLifecycle: 读取并清理目标 peer_id；若省略: 工具不知道要删除哪个 peer
    if not peer_id:  # 新增代码+TeamCommunicationLifecycle: 检查 peer_id 是否为空；若省略: 空目标会产生模糊未知 peer 错误
        return "team_delete 失败：缺少 peer_id 参数。"  # 新增代码+TeamCommunicationLifecycle: 返回清楚缺参错误；若省略: 模型难以修正 team_delete 调用
    if arguments.get("confirm_delete") is not True:  # 新增代码+TeamCommunicationLifecycle: 要求显式 true 才执行删除；若省略: 模型可能在没有明确确认时删除 peer
        return "team_delete 失败：删除 peer 会丢弃该 peer 的进程内 inbox，请显式传入 confirm_delete=true。"  # 新增代码+TeamCommunicationLifecycle: 返回确认要求；若省略: 模型不知道如何安全重试删除
    peer_record = agent.team_peers.pop(peer_id, None)  # 新增代码+TeamCommunicationLifecycle: 从登记表删除目标 peer；若省略: team_delete 只会返回文本但不会真正移除 peer
    if peer_record is None:  # 新增代码+TeamCommunicationLifecycle: 处理未知 peer_id；若省略: 删除不存在目标会被误认为成功
        try:  # 修改代码+DurableTeamRegistry: 内存没有时尝试删除持久 registry 里的 peer；若没有这行代码，重启后的 team_delete 会误报未知 peer。
            peer_record = agent.team_registry.delete_peer(peer_id)  # 新增代码+DurableTeamRegistry: 从磁盘删除并返回 peer；若没有这行代码，旧 peer 无法跨实例清理。
        except KeyError:  # 新增代码+DurableTeamRegistry: 持久 registry 也没有该 peer 时才返回未知；若没有这行代码，真实未知 id 会抛底层异常。
            return f"team_delete 失败：未知 peer_id：{peer_id}，请先调用 list_peers。"  # 修改代码+DurableTeamRegistry: 返回可恢复建议；若没有这行代码，模型难以判断目标是否已经被删。
    else:  # 新增代码+DurableTeamRegistry: 内存里存在 peer 时也要同步删除磁盘记录；若没有这行代码，team_delete 后重启会把 peer 又恢复出来。
        try:  # 新增代码+DurableTeamRegistry: 持久记录可能已不存在，需要容错；若没有这行代码，内存删除会被磁盘缺失异常打断。
            agent.team_registry.delete_peer(peer_id)  # 新增代码+DurableTeamRegistry: 删除持久 peer 文件；若没有这行代码，team_delete 只会删除当前进程缓存。
        except KeyError:  # 新增代码+DurableTeamRegistry: 兼容只有内存没有磁盘的旧状态；若没有这行代码，迁移前的临时 peer 不能删除。
            pass  # 新增代码+DurableTeamRegistry: 磁盘无记录时忽略；若没有这行代码，except 分支语法不完整。
    return f"team_delete 成功：已删除教学版 peer。\npeer_id={peer_id}\nname={peer_record.name}\ndropped_message_count={len(peer_record.inbox)}"  # 修改代码+TaskAgentToolsSplit: 返回删除的 peer 和丢弃消息数；若没有这行代码，模型无法审计删除影响。

def team_start_task(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+TeamTaskBinding: 执行 team_start_task 并把 peer 绑定到后台 task；若省略: team 成员无法承接真实可查询子任务
    peer_id = str(arguments.get("peer_id", "") or "").strip()  # 新增代码+TeamTaskBinding: 读取并清理目标 peer_id；若省略: 工具不知道要让哪个 peer 启动任务
    if not peer_id:  # 新增代码+TeamTaskBinding: 检查 peer_id 是否为空；若省略: 空目标会产生模糊未知 peer 错误
        return "team_start_task 失败：缺少 peer_id 参数。"  # 新增代码+TeamTaskBinding: 返回清楚缺参错误；若省略: 模型难以修正 team_start_task 调用
    peer_record = agent.team_peers.get(peer_id)  # 新增代码+TeamTaskBinding: 从登记表查找目标 peer；若省略: 工具无法定位要绑定的团队成员
    if peer_record is None:  # 新增代码+TeamTaskBinding: 处理未知 peer_id；若省略: 访问 None 会抛异常
        try:  # 修改代码+DurableTeamRegistry: 内存没有时尝试从持久 registry 恢复；若没有这行代码，重启后的 team_start_task 会误报未知 peer。
            peer_record = agent.team_registry.get_peer(peer_id)  # 新增代码+DurableTeamRegistry: 从磁盘恢复 peer；若没有这行代码，旧 peer 无法继续绑定后台任务。
            agent.team_peers[peer_id] = peer_record  # 新增代码+DurableTeamRegistry: 把恢复的 peer 放回内存缓存；若没有这行代码，本次绑定后续逻辑不方便复用。
        except KeyError:  # 新增代码+DurableTeamRegistry: 持久 registry 也没有该 peer 时才返回未知；若没有这行代码，真实未知 id 会抛底层异常。
            return f"team_start_task 失败：未知 peer_id：{peer_id}，请先调用 team_create 或 list_peers。"  # 修改代码+DurableTeamRegistry: 返回可恢复建议；若没有这行代码，模型不知道该先创建或查看 peer。
    prompt = str(arguments.get("prompt", "") or "").strip()  # 新增代码+TeamTaskBinding: 读取并清理子任务目标；若省略: 后台 task 没有可执行目标
    if not prompt:  # 新增代码+TeamTaskBinding: 检查 prompt 是否为空；若省略: 空任务会浪费子 agent 运行并产生模糊结果
        return "team_start_task 失败：缺少非空 prompt 参数。"  # 新增代码+TeamTaskBinding: 返回清楚缺参错误；若省略: 模型难以修正子任务目标
    existing_task = agent.task_runs.get(peer_record.bound_task_id) if peer_record.bound_task_id else None  # 新增代码+TeamTaskBinding: 查找该 peer 已绑定的旧内存 task；若省略: 可能给同一 peer 重复启动多个未完成任务
    if existing_task is None and peer_record.bound_task_id:  # 新增代码+DurableTeamRegistry: 内存找不到旧 task 时尝试持久 registry；若没有这行代码，重启后可能重复启动同一 peer 的任务。
        try:  # 新增代码+DurableTeamRegistry: 持久任务可能不存在，需要容错；若没有这行代码，坏绑定会打断新任务启动。
            existing_task = agent.task_registry.get_task(peer_record.bound_task_id)  # 新增代码+DurableTeamRegistry: 从磁盘读取旧绑定任务；若没有这行代码，team_start_task 无法跨实例保护运行中任务。
        except KeyError:  # 新增代码+DurableTeamRegistry: 旧绑定任务丢失时允许继续；若没有这行代码，历史坏状态会阻塞新任务。
            existing_task = None  # 新增代码+DurableTeamRegistry: 明确旧任务不存在；若没有这行代码，后续判断语义不清楚。
    if existing_task is not None and existing_task.status in {"pending", "running"}:  # 新增代码+TeamTaskBinding: 阻止同一 peer 同时绑定多个未完成任务；若省略: ownership 会变混乱
        return f"team_start_task 失败：peer_id={peer_id} 已绑定运行中的 task_id={existing_task.task_id}，请先 task_output 或 task_stop。"  # 新增代码+TeamTaskBinding: 返回旧任务 id 方便用户接管；若省略: 模型不知道该如何恢复
    task_arguments: dict[str, Any] = {"prompt": prompt, "background": True}  # 新增代码+TeamTaskBinding: 构造底层 task 参数并强制后台运行；若省略: team_start_task 可能阻塞主 agent
    if "allowed_tools" in arguments:  # 新增代码+TeamTaskBinding: 只有调用方提供工具白名单时才向底层 task 透传；若省略: 无法按 peer 职责收窄工具权限
        task_arguments["allowed_tools"] = arguments.get("allowed_tools")  # 新增代码+TeamTaskBinding: 透传 allowed_tools 给底层 task 校验和执行；若省略: team_start_task 的白名单参数不会生效
    if "max_turns" in arguments:  # 新增代码+TeamTaskBinding: 只有调用方提供轮次上限时才向底层 task 透传；若省略: 无法针对绑定任务调整执行长度
        task_arguments["max_turns"] = arguments.get("max_turns")  # 新增代码+TeamTaskBinding: 透传 max_turns 给底层 task 校验和执行；若省略: team_start_task 的轮次参数不会生效
    task_output = task(agent, task_arguments)  # 新增代码+TeamTaskBinding: 复用现有 task 生命周期实现启动后台子 agent；若省略: 会重复造任务系统且 task_output/task_stop 接不上
    if not task_output.startswith("task 成功"):  # 新增代码+TeamTaskBinding: 检查底层 task 是否启动成功；若省略: 失败 task 也可能被误绑定到 peer
        return f"team_start_task 失败：后台 task 启动失败。\n{task_output}"  # 新增代码+TeamTaskBinding: 把底层失败原因带回；若省略: 模型无法知道 allowed_tools/max_turns 等参数哪里错
    task_id_line = next((line for line in task_output.splitlines() if line.startswith("task_id=")), "")  # 新增代码+TeamTaskBinding: 从底层 task 输出提取 task_id 行；若省略: peer 记录无法保存可查询任务 id
    if not task_id_line:  # 新增代码+TeamTaskBinding: 防御底层 task 成功文本缺少 task_id 的异常情况；若省略: split 后可能得到空 id 并污染 peer 记录
        return f"team_start_task 失败：后台 task 已返回成功但缺少 task_id。\n{task_output}"  # 新增代码+TeamTaskBinding: 返回完整底层输出方便排查；若省略: 用户不知道失败发生在绑定阶段
    task_id = task_id_line.split("=", 1)[1].strip()  # 新增代码+TeamTaskBinding: 提取 task_id 字符串用于绑定 peer；若省略: 后续 task_output/task_stop 无法定位任务
    task_record = agent.task_runs.get(task_id)  # 新增代码+TeamTaskBinding: 读取刚启动的任务记录以取得当前状态；若省略: 返回结果无法反映真实任务表状态
    task_status = task_record.status if task_record is not None else "running"  # 新增代码+TeamTaskBinding: 选择任务当前状态并用 running 兜底；若省略: 绑定成功文本缺少可读状态
    peer_record.bound_task_id = task_id  # 新增代码+TeamTaskBinding: 把后台 task id 写入 peer 记录；若省略: list_peers 无法展示 peer 与 task 的连接
    peer_record.bound_task_started_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+TeamTaskBinding: 记录绑定任务启动时间；若省略: 用户无法审计 peer 何时开始工作
    peer_record.status = "active"  # 新增代码+TeamTaskBinding: 把承接任务的 peer 标记为 active；若省略: list_peers 可能显示正在执行任务的 peer 仍然 idle
    agent.team_registry.save_peer(peer_record)  # 新增代码+DurableTeamRegistry: 保存 peer 与后台 task 的绑定关系；若没有这行代码，重启后 team 视图会丢失绑定。
    return f"team_start_task 成功：peer 已绑定后台 task。\npeer_id={peer_id}\ntask_id={task_id}\nstatus={task_status}\nbackground=true\nbound_task_started_at={peer_record.bound_task_started_at}"  # 修改代码+TaskAgentToolsSplit: 返回 peer 绑定的后台任务信息；若没有这行代码，模型无法用 task_id 继续查询任务。

def task_background_enabled_for_agent(raw_background: Any) -> bool:  # 新增代码+AsyncTask: 统一解析 task.background 参数；若省略: 模型传入布尔或字符串时语义可能不一致
    return task_background_enabled(raw_background)  # 修改代码+TaskAgentToolsSplit: 复用 task_runs 中的后台开关解析；若没有这行代码，background 参数规则会重复分叉。

def task_allowed_tool_names(agent: Any, raw_allowed_tools: Any) -> set[str] | str:  # 修改代码+ToolPolicyV2: 解析 task allowed_tools 时区分默认继承和显式白名单；若没有这行代码，显式 MCP 工具可能被父 visible 过滤提前清空
    blocked_task_tool_names = set(BLOCKED_TASK_TOOL_NAMES)  # 修改代码+TasksSplit: 从 tasks.task_runs 读取禁止子 agent 继承的任务工具集合；若没有这行代码，递归 task 风险清单仍会散在主文件。
    default_tool_names = set(catalog_runtime_from_tools.tool_schema_names(agent))  # 修改代码+AgentPyPhaseHMcpToolRuntime: 默认省略 allowed_tools 时直连 catalog_runtime 继承父当前可见工具池；若没有这行代码，task 模块仍会反向依赖 agent.py 薄包装。
    default_tool_names.difference_update(blocked_task_tool_names)  # 修改代码+ToolPolicyV2: 默认继承时移除 task 管理工具；若没有这行代码，省略 allowed_tools 的子 agent 可能递归建 task 或操作父任务
    if raw_allowed_tools is None:  # 修改代码+ToolPolicyV2: 省略 allowed_tools 时走父当前 visible 工具池边界；若没有这行代码，默认场景会和显式白名单混在一起导致越权
        return default_tool_names  # 修改代码+ToolPolicyV2: 返回默认可继承工具集合；若没有这行代码，省略 allowed_tools 的子 agent 没有稳定权限边界
    if not isinstance(raw_allowed_tools, list):  # 新增代码+TaskAgent: allowed_tools 必须是列表；若省略: 字符串会被逐字符误解析
        return "task 失败：allowed_tools 必须是工具名字符串数组。"  # 新增代码+TaskAgent: 返回清楚类型错误；若省略: 模型难以修正 allowed_tools 参数
    cleaned_tool_names = {str(tool_name).strip() for tool_name in raw_allowed_tools if str(tool_name).strip()}  # 新增代码+TaskAgent: 清理白名单工具名并丢弃空字符串；若省略: 空白工具名会进入过滤集合
    cleaned_tool_names.difference_update(blocked_task_tool_names)  # 修改代码+ToolPolicyV2: 显式白名单中也移除 task 管理工具；若没有这行代码，模型传入 task 可能造成递归委派或父任务越权
    catalog_tool_names = {tool.name for tool in catalog_runtime_from_tools.tool_catalog(agent)}  # 修改代码+AgentPyPhaseHMcpToolRuntime: 显式 allowed_tools 直连完整 catalog 判断工具是否存在；若没有这行代码，白名单校验仍会依赖 agent.py 薄包装。
    explicit_allowed_tool_names = catalog_tool_names | set(agent.loaded_tool_names)  # 新增代码+ToolPolicyV2: 显式 allowed_tools 额外允许父 agent 已加载 deferred 工具名；若没有这行代码，已 select 的外部工具可能无法传入子 agent
    explicit_allowed_tool_names.difference_update(blocked_task_tool_names)  # 新增代码+ToolPolicyV2: 完整 catalog 合法集合也移除递归和任务管理工具；若没有这行代码，显式白名单可能绕过禁止 task 规则
    return cleaned_tool_names & explicit_allowed_tool_names  # 修改代码+TaskAgentToolsSplit: 返回显式白名单和当前工具池的交集；若没有这行代码，子 agent 可能拿到不可见工具。

def task_max_turns(raw_max_turns: Any) -> int | str:  # 新增代码+TaskAgent: 解析 task max_turns 参数；若省略: 子 agent 轮次规则会重复且不清晰
    if raw_max_turns is None:  # 新增代码+TaskAgent: 省略 max_turns 时使用保守默认值；若省略: 子 agent 可能默认无固定上限
        return 3  # 新增代码+TaskAgent: 默认允许 3 轮模型-工具循环；若省略: 子任务可能太早停止或运行过久
    try:  # 新增代码+TaskAgent: 捕获 max_turns 非法值；若省略: parse_max_turns_value 的异常会中断 agent
        parsed_max_turns = parse_max_turns_value(raw_max_turns, "task.max_turns")  # 新增代码+TaskAgent: 复用已有轮次解析规则；若省略: task 和主 agent 的轮次语义会不一致
    except ValueError as error:  # 新增代码+TaskAgent: 处理非法 max_turns；若省略: 用户会看到底层异常
        return f"task 失败：{error}"  # 新增代码+TaskAgent: 返回可读失败信息；若省略: 模型难以修正轮次参数
    if parsed_max_turns is None:  # 新增代码+TaskAgent: task 不接受无限制子 agent；若省略: 子任务可能无界运行
        return "task 失败：max_turns 必须是大于等于 1 的整数，task 子 agent 暂不接受无限制轮次。"  # 新增代码+TaskAgent: 明确拒绝无限制轮次；若省略: 模型不知道为什么 none 不被接受
    return parsed_max_turns  # 修改代码+TaskAgentToolsSplit: 返回合法轮次数；若没有这行代码，task 子 agent 无法知道最多运行几轮。

def task_child_prompt_for_agent(prompt: str) -> str:  # 新增代码+TaskAgent: 构造子 agent 专用 prompt；若省略: 子 agent 缺少统一执行边界说明
    return task_child_prompt(prompt)  # 修改代码+TaskAgentToolsSplit: 复用 task_runs 中的子任务提示词构造；若没有这行代码，子 agent 缺少统一执行边界。

def cron_create(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 创建教学版进程内定时任务记录；若省略: cron_create schema 暴露后仍没有实际行为
    name = str(arguments.get("name", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理定时任务名称；若省略: 列表中无法显示可读名称
    schedule = str(arguments.get("schedule", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理定时说明；若省略: 记录不知道何时复查
    prompt = str(arguments.get("prompt", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理到点任务说明；若省略: 记录没有实际检查内容
    stop_condition = str(arguments.get("stop_condition", "") or "").strip()  # 新增代码+CronMonitor: 读取可选停止条件；若省略: 长期任务缺少收束边界
    if not name:  # 新增代码+CronMonitor: 校验名称不能为空；若省略: 用户难以区分多个无名定时任务
        return "cron_create 失败：缺少非空 name 参数。"  # 新增代码+CronMonitor: 返回清楚的名称缺失错误；若省略: 模型难以修正参数
    if not schedule:  # 新增代码+CronMonitor: 校验定时说明不能为空；若省略: 可能登记没有触发时间的定时记录
        return "cron_create 失败：缺少非空 schedule 参数。"  # 新增代码+CronMonitor: 返回清楚的 schedule 缺失错误；若省略: 模型难以修正参数
    if not prompt:  # 新增代码+CronMonitor: 校验任务说明不能为空；若省略: 可能登记没有工作内容的定时记录
        return "cron_create 失败：缺少非空 prompt 参数。"  # 新增代码+CronMonitor: 返回清楚的 prompt 缺失错误；若省略: 模型难以修正参数
    cron_id = f"cron_{secrets.token_hex(6)}"  # 新增代码+CronMonitor: 生成短且唯一的定时任务 id；若省略: cron_list/delete 无法引用具体记录
    created_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+CronMonitor: 记录创建时间；若省略: 用户无法判断记录登记顺序
    record = CronRecord(cron_id=cron_id, name=name, schedule=schedule, prompt=prompt, stop_condition=stop_condition, state="active", created_at=created_at)  # 新增代码+CronMonitor: 构造进程内定时任务记录；若省略: 后续列表和删除没有数据源
    agent.cron_records[cron_id] = record  # 新增代码+CronMonitor: 把记录保存到当前 agent 实例；若省略: 创建后无法被 cron_list 找回
    return "\n".join([  # 新增代码+CronMonitor: 返回结构化创建结果；若省略: 模型拿不到 cron_id 和边界说明
        "cron_create 成功：已登记教学版进程内定时任务记录。",  # 新增代码+CronMonitor: 输出成功前缀；若省略: 调用方难以判断工具是否成功
        f"cron_id={cron_id}",  # 新增代码+CronMonitor: 输出定时任务 id；若省略: 后续 cron_list/delete 难以引用
        "state=active",  # 新增代码+CronMonitor: 输出当前记录状态；若省略: 用户不知道记录是否有效
        f"name={name}",  # 新增代码+CronMonitor: 输出任务名称；若省略: 用户需要从 prompt 猜记录含义
        f"schedule={schedule}",  # 新增代码+CronMonitor: 输出触发时间说明；若省略: 用户无法审计计划何时复查
        f"prompt={prompt}",  # 新增代码+CronMonitor: 输出任务内容；若省略: 用户不知道到点要做什么
        f"stop_condition={stop_condition or '(未设置)'}",  # 新增代码+CronMonitor: 输出停止条件或占位；若省略: 收束边界不透明
        "边界：不执行真实定时任务，不创建系统定时器，不跨进程常驻，不发送通知。",  # 新增代码+CronMonitor: 明确教学版边界；若省略: 模型可能误以为真实调度已经启动
    ])  # 修改代码+TaskAgentToolsSplit: 返回创建后的 cron 记录文本；若没有这行代码，cron_create 无法把新记录交回模型。

def cron_list(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 列出教学版进程内定时任务记录；若省略: 模型无法查看已登记 Cron 记录
    state = cron_monitor_state_for_agent(arguments.get("state"))  # 新增代码+CronMonitor: 解析 active/deleted/all 筛选状态；若省略: 列表筛选逻辑会散落在方法里
    max_results = cron_monitor_max_results_for_agent(arguments.get("max_results"))  # 新增代码+CronMonitor: 解析最大返回记录数；若省略: 大量记录可能撑爆上下文
    records = [record for record in agent.cron_records.values() if state == "all" or record.state == state]  # 新增代码+CronMonitor: 按状态筛选定时记录；若省略: 删除记录和有效记录会混在一起
    limited_records = records[:max_results]  # 新增代码+CronMonitor: 按 max_results 截断输出记录；若省略: 长列表可能占用过多上下文
    lines = [  # 新增代码+CronMonitor: 准备结构化列表输出；若省略: 列表结果无法稳定阅读
        "cron_list 成功：已读取教学版进程内定时任务记录。",  # 新增代码+CronMonitor: 输出成功前缀；若省略: 调用方难以判断工具是否成功
        f"state_filter={state}",  # 新增代码+CronMonitor: 输出筛选状态；若省略: 用户不知道列表是否过滤过
        f"record_count={len(limited_records)}",  # 新增代码+CronMonitor: 输出本次返回数量；若省略: 用户需要手动数记录
        f"total_matching={len(records)}",  # 新增代码+CronMonitor: 输出匹配总数；若省略: 用户不知道是否被 max_results 截断
        "记录：",  # 新增代码+CronMonitor: 添加记录标题；若省略: 元信息和列表项容易混在一起
    ]  # 新增代码+CronMonitor: 列表输出基础行结束；若省略: 后续追加没有容器
    if not limited_records:  # 新增代码+CronMonitor: 如果没有匹配记录；若省略: 空列表会只显示标题而不清楚
        lines.append("(无记录)")  # 新增代码+CronMonitor: 明确说明没有记录；若省略: 用户可能误以为输出被截断
    for record in limited_records:  # 新增代码+CronMonitor: 逐条格式化定时任务记录；若省略: 列表不会显示具体内容
        lines.append(format_cron_record_for_agent(record))  # 新增代码+CronMonitor: 使用统一格式输出记录；若省略: 多处输出格式容易不一致
    return "\n".join(lines)  # 修改代码+TaskAgentToolsSplit: 返回完整 cron 列表文本；若没有这行代码，cron_list 没有可读输出。

def cron_delete(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 删除教学版进程内定时任务记录；若省略: cron_delete schema 暴露后仍没有实际行为
    cron_id = str(arguments.get("cron_id", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理目标 cron_id；若省略: 工具不知道要删除哪条记录
    if not cron_id:  # 新增代码+CronMonitor: 校验 cron_id 是否为空；若省略: 空删除请求会进入记录查询
        return "cron_delete 失败：缺少非空 cron_id 参数。"  # 新增代码+CronMonitor: 返回清楚的缺参错误；若省略: 模型难以修正删除调用
    if arguments.get("confirm_delete") is not True:  # 新增代码+CronMonitor: 要求显式确认删除；若省略: 模型可能误删定时记录
        return "cron_delete 失败：删除定时任务记录需要 confirm_delete=true。"  # 新增代码+CronMonitor: 返回确认要求；若省略: 模型不知道如何安全重试
    record = agent.cron_records.get(cron_id)  # 新增代码+CronMonitor: 查找目标定时记录；若省略: 无法判断 id 是否存在
    if record is None:  # 新增代码+CronMonitor: 如果没有找到记录；若省略: 后续访问 None 会崩溃
        return f"cron_delete 失败：没有找到 cron_id={cron_id} 的定时任务记录。"  # 新增代码+CronMonitor: 返回清楚的不存在错误；若省略: 用户不知道删除失败原因
    record.state = "deleted"  # 新增代码+CronMonitor: 标记记录已删除而不是创建系统副作用；若省略: cron_list active 仍会显示该记录
    record.deleted_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+CronMonitor: 保存删除时间用于审计；若省略: 用户无法知道记录何时被回收
    return "\n".join([  # 新增代码+CronMonitor: 返回结构化删除结果；若省略: 模型拿不到删除确认
        "cron_delete 成功：已删除教学版进程内定时任务记录。",  # 新增代码+CronMonitor: 输出成功前缀；若省略: 调用方难以判断删除是否成功
        f"cron_id={cron_id}",  # 新增代码+CronMonitor: 输出被删除记录 id；若省略: 用户无法核对目标
        "state=deleted",  # 新增代码+CronMonitor: 输出删除后状态；若省略: 用户不知道记录是否仍 active
        "边界：本工具只删除进程内记录；此前也没有创建过系统定时器。",  # 新增代码+CronMonitor: 明确删除边界；若省略: 用户可能误以为系统任务也被处理
    ])  # 修改代码+TaskAgentToolsSplit: 返回删除后的 cron 记录文本；若没有这行代码，cron_delete 无法确认删除结果。

def monitor(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 管理教学版进程内监控记录；若省略: monitor schema 暴露后仍没有实际行为
    action = str(arguments.get("action", "") or "").strip().lower()  # 新增代码+CronMonitor: 读取并清理 monitor 动作；若省略: 多动作工具无法判断执行分支
    if action == "create":  # 新增代码+CronMonitor: 如果请求创建监控记录；若省略: create 动作无法执行
        return monitor_create(agent, arguments)  # 新增代码+CronMonitor: 调用监控创建分支；若省略: 创建逻辑会混在主分发里
    if action == "list":  # 新增代码+CronMonitor: 如果请求列出监控记录；若省略: list 动作无法执行
        return monitor_list(agent, arguments)  # 新增代码+CronMonitor: 调用监控列表分支；若省略: 列表逻辑会混在主分发里
    if action == "delete":  # 新增代码+CronMonitor: 如果请求删除监控记录；若省略: delete 动作无法执行
        return monitor_delete(agent, arguments)  # 新增代码+CronMonitor: 调用监控删除分支；若省略: 删除逻辑会混在主分发里
    if action == "record_result":  # 新增代码+CronMonitor: 如果请求记录最近观察结果；若省略: 监控无法保存检查证据
        return monitor_record_result(agent, arguments)  # 新增代码+CronMonitor: 调用结果记录分支；若省略: 结果更新逻辑会混在主分发里
    return "monitor 失败：action 必须是 create、list、delete 或 record_result。"  # 修改代码+TaskAgentToolsSplit: 返回 monitor action 白名单错误；若没有这行代码，模型不知道可用动作范围。

def monitor_create(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 创建教学版进程内监控记录；若省略: monitor create 动作没有实际行为
    name = str(arguments.get("name", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理监控名称；若省略: 多个监控记录难以区分
    target = str(arguments.get("target", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理监控目标；若省略: 记录不知道观察什么
    condition = str(arguments.get("condition", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理触发条件；若省略: 记录不知道什么情况算命中
    check_interval = str(arguments.get("check_interval", "") or "").strip() or "manual"  # 新增代码+CronMonitor: 读取检查频率并默认 manual；若省略: 监控节奏不清楚
    stop_condition = str(arguments.get("stop_condition", "") or "").strip()  # 新增代码+CronMonitor: 读取可选停止条件；若省略: 监控缺少收束边界
    if not name:  # 新增代码+CronMonitor: 校验名称不能为空；若省略: 用户难以区分无名监控记录
        return "monitor 失败：action=create 时缺少非空 name 参数。"  # 新增代码+CronMonitor: 返回名称缺失错误；若省略: 模型难以修正参数
    if not target:  # 新增代码+CronMonitor: 校验监控目标不能为空；若省略: 可能创建不知道观察对象的记录
        return "monitor 失败：action=create 时缺少非空 target 参数。"  # 新增代码+CronMonitor: 返回目标缺失错误；若省略: 模型难以修正参数
    if not condition:  # 新增代码+CronMonitor: 校验触发条件不能为空；若省略: 可能创建没有判断标准的监控记录
        return "monitor 失败：action=create 时缺少非空 condition 参数。"  # 新增代码+CronMonitor: 返回条件缺失错误；若省略: 模型难以修正参数
    monitor_id = f"mon_{secrets.token_hex(6)}"  # 新增代码+CronMonitor: 生成短且唯一的监控 id；若省略: 后续动作无法引用具体记录
    created_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+CronMonitor: 记录创建时间；若省略: 用户无法判断监控登记顺序
    record = MonitorRecord(monitor_id=monitor_id, name=name, target=target, condition=condition, check_interval=check_interval, stop_condition=stop_condition, state="active", created_at=created_at)  # 新增代码+CronMonitor: 构造进程内监控记录；若省略: 后续列表和结果记录没有数据源
    agent.monitor_records[monitor_id] = record  # 新增代码+CronMonitor: 保存监控记录到当前 agent 实例；若省略: 创建后无法被 monitor list 找回
    return "\n".join([  # 新增代码+CronMonitor: 返回结构化创建结果；若省略: 模型拿不到 monitor_id 和边界说明
        "monitor 成功：action=create",  # 新增代码+CronMonitor: 输出成功前缀和动作；若省略: 调用方难以判断动作是否成功
        f"monitor_id={monitor_id}",  # 新增代码+CronMonitor: 输出监控 id；若省略: 后续 record_result/delete 难以引用
        "state=active",  # 新增代码+CronMonitor: 输出当前状态；若省略: 用户不知道记录是否有效
        f"name={name}",  # 新增代码+CronMonitor: 输出监控名称；若省略: 用户需要从目标猜含义
        f"target={target}",  # 新增代码+CronMonitor: 输出观察目标；若省略: 用户无法审计监控对象
        f"condition={condition}",  # 新增代码+CronMonitor: 输出触发条件；若省略: 用户无法审计命中标准
        f"check_interval={check_interval}",  # 新增代码+CronMonitor: 输出检查频率说明；若省略: 用户不知道复查节奏
        f"stop_condition={stop_condition or '(未设置)'}",  # 新增代码+CronMonitor: 输出停止条件或占位；若省略: 收束边界不透明
        "边界：不启动真实监控，不自动检查，不常驻后台，不发送通知。",  # 新增代码+CronMonitor: 明确教学版边界；若省略: 模型可能误以为真实监控已经运行
    ])  # 修改代码+TaskAgentToolsSplit: 返回创建后的 monitor 记录文本；若没有这行代码，monitor_create 无法把新记录交回模型。

def monitor_list(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 列出教学版进程内监控记录；若省略: monitor list 动作没有实际行为
    state = cron_monitor_state_for_agent(arguments.get("state"))  # 新增代码+CronMonitor: 解析 active/deleted/all 筛选状态；若省略: 列表筛选逻辑会重复
    max_results = cron_monitor_max_results_for_agent(arguments.get("max_results"))  # 新增代码+CronMonitor: 解析最大返回记录数；若省略: 大量记录可能撑爆上下文
    records = [record for record in agent.monitor_records.values() if state == "all" or record.state == state]  # 新增代码+CronMonitor: 按状态筛选监控记录；若省略: 删除记录和有效记录会混在一起
    limited_records = records[:max_results]  # 新增代码+CronMonitor: 按 max_results 截断输出记录；若省略: 长列表可能占用过多上下文
    lines = [  # 新增代码+CronMonitor: 准备结构化列表输出；若省略: monitor list 结果无法稳定阅读
        "monitor 成功：action=list",  # 新增代码+CronMonitor: 输出成功前缀和动作；若省略: 调用方难以判断动作是否成功
        f"state_filter={state}",  # 新增代码+CronMonitor: 输出筛选状态；若省略: 用户不知道列表是否过滤过
        f"record_count={len(limited_records)}",  # 新增代码+CronMonitor: 输出本次返回数量；若省略: 用户需要手动数记录
        f"total_matching={len(records)}",  # 新增代码+CronMonitor: 输出匹配总数；若省略: 用户不知道是否被 max_results 截断
        "记录：",  # 新增代码+CronMonitor: 添加记录标题；若省略: 元信息和列表项容易混在一起
    ]  # 新增代码+CronMonitor: 列表输出基础行结束；若省略: 后续追加没有容器
    if not limited_records:  # 新增代码+CronMonitor: 如果没有匹配记录；若省略: 空列表会只显示标题而不清楚
        lines.append("(无记录)")  # 新增代码+CronMonitor: 明确说明没有记录；若省略: 用户可能误以为输出被截断
    for record in limited_records:  # 新增代码+CronMonitor: 逐条格式化监控记录；若省略: 列表不会显示具体内容
        lines.append(format_monitor_record_for_agent(record))  # 新增代码+CronMonitor: 使用统一格式输出记录；若省略: 多处输出格式容易不一致
    return "\n".join(lines)  # 修改代码+TaskAgentToolsSplit: 返回完整 monitor 列表文本；若没有这行代码，monitor_list 没有可读输出。

def monitor_delete(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 删除教学版进程内监控记录；若省略: monitor delete 动作没有实际行为
    monitor_id = str(arguments.get("monitor_id", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理目标 monitor_id；若省略: 工具不知道要删除哪条记录
    if not monitor_id:  # 新增代码+CronMonitor: 校验 monitor_id 是否为空；若省略: 空删除请求会进入记录查询
        return "monitor 失败：action=delete 时缺少非空 monitor_id 参数。"  # 新增代码+CronMonitor: 返回清楚的缺参错误；若省略: 模型难以修正删除调用
    if arguments.get("confirm_delete") is not True:  # 新增代码+CronMonitor: 要求显式确认删除；若省略: 模型可能误删监控记录
        return "monitor 失败：删除监控记录需要 confirm_delete=true。"  # 新增代码+CronMonitor: 返回确认要求；若省略: 模型不知道如何安全重试
    record = agent.monitor_records.get(monitor_id)  # 新增代码+CronMonitor: 查找目标监控记录；若省略: 无法判断 id 是否存在
    if record is None:  # 新增代码+CronMonitor: 如果没有找到记录；若省略: 后续访问 None 会崩溃
        return f"monitor 失败：没有找到 monitor_id={monitor_id} 的监控记录。"  # 新增代码+CronMonitor: 返回清楚的不存在错误；若省略: 用户不知道删除失败原因
    record.state = "deleted"  # 新增代码+CronMonitor: 标记记录已删除而不触发外部副作用；若省略: monitor list active 仍会显示该记录
    record.deleted_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+CronMonitor: 保存删除时间用于审计；若省略: 用户无法知道记录何时被回收
    return "\n".join([  # 新增代码+CronMonitor: 返回结构化删除结果；若省略: 模型拿不到删除确认
        "monitor 成功：action=delete",  # 新增代码+CronMonitor: 输出成功前缀和动作；若省略: 调用方难以判断删除是否成功
        f"monitor_id={monitor_id}",  # 新增代码+CronMonitor: 输出被删除监控 id；若省略: 用户无法核对目标
        "state=deleted",  # 新增代码+CronMonitor: 输出删除后状态；若省略: 用户不知道记录是否仍 active
        "边界：本工具只删除进程内记录；此前也没有启动过真实监控服务。",  # 新增代码+CronMonitor: 明确删除边界；若省略: 用户可能误以为系统监控也被处理
    ])  # 修改代码+TaskAgentToolsSplit: 返回删除后的 monitor 记录文本；若没有这行代码，monitor_delete 无法确认删除结果。

def monitor_record_result(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+CronMonitor: 给监控记录写入最近一次观察结果；若省略: monitor 无法保存检查证据
    monitor_id = str(arguments.get("monitor_id", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理目标 monitor_id；若省略: 工具不知道更新哪条记录
    result = str(arguments.get("result", "") or "").strip()  # 新增代码+CronMonitor: 读取并清理观察结果文本；若省略: 监控记录没有证据内容
    result_status = monitor_result_status_for_agent(arguments.get("result_status"))  # 新增代码+CronMonitor: 解析最近观察状态；若省略: 状态标准化逻辑会散落在方法里
    if not monitor_id:  # 新增代码+CronMonitor: 校验 monitor_id 是否为空；若省略: 空更新请求会进入记录查询
        return "monitor 失败：action=record_result 时缺少非空 monitor_id 参数。"  # 新增代码+CronMonitor: 返回清楚的缺参错误；若省略: 模型难以修正调用
    if not result:  # 新增代码+CronMonitor: 校验观察结果不能为空；若省略: 可能写入没有证据的监控结果
        return "monitor 失败：action=record_result 时缺少非空 result 参数。"  # 新增代码+CronMonitor: 返回清楚的 result 缺失错误；若省略: 模型难以补充证据
    record = agent.monitor_records.get(monitor_id)  # 新增代码+CronMonitor: 查找目标监控记录；若省略: 无法判断 id 是否存在
    if record is None:  # 新增代码+CronMonitor: 如果没有找到记录；若省略: 后续访问 None 会崩溃
        return f"monitor 失败：没有找到 monitor_id={monitor_id} 的监控记录。"  # 新增代码+CronMonitor: 返回清楚的不存在错误；若省略: 用户不知道更新失败原因
    if record.state != "active":  # 新增代码+CronMonitor: 已删除记录不能继续更新结果；若省略: 删除后的监控仍会被误用
        return f"monitor 失败：monitor_id={monitor_id} 当前 state={record.state}，不能记录新结果。"  # 新增代码+CronMonitor: 返回状态不允许错误；若省略: 模型不知道为什么更新被拒绝
    record.last_result = result  # 新增代码+CronMonitor: 保存最近观察结果正文；若省略: monitor list 无法展示最新证据
    record.last_status = result_status  # 新增代码+CronMonitor: 保存最近观察状态；若省略: 用户无法快速判断是否触发条件
    record.last_checked_at = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+CronMonitor: 保存最近检查时间；若省略: 用户无法判断结果是否新鲜
    return "\n".join([  # 新增代码+CronMonitor: 返回结构化结果记录输出；若省略: 模型拿不到更新后的状态
        "monitor 成功：action=record_result",  # 新增代码+CronMonitor: 输出成功前缀和动作；若省略: 调用方难以判断更新是否成功
        f"monitor_id={monitor_id}",  # 新增代码+CronMonitor: 输出被更新监控 id；若省略: 用户无法核对目标
        f"last_status={record.last_status}",  # 新增代码+CronMonitor: 输出最近状态；若省略: 用户无法快速判断监控是否命中
        f"last_checked_at={record.last_checked_at}",  # 新增代码+CronMonitor: 输出检查时间；若省略: 结果新鲜度不透明
        f"last_result={record.last_result}",  # 新增代码+CronMonitor: 输出最近结果正文；若省略: 监控结果缺少证据
    ])  # 修改代码+TaskAgentToolsSplit: 返回记录观察结果后的 monitor 文本；若没有这行代码，monitor_record_result 无法确认保存结果。

def cron_monitor_state_for_agent(raw_value: Any) -> str:  # 新增代码+CronMonitor: 解析 Cron/Monitor 列表筛选状态；若省略: active/deleted/all 处理会重复
    return cron_monitor_state(raw_value)  # 修改代码+TaskAgentToolsSplit: 复用 cron_monitor 中的状态筛选解析；若没有这行代码，active/deleted/all 规则会分叉。

def cron_monitor_max_results_for_agent(raw_value: Any) -> int:  # 新增代码+CronMonitor: 解析 Cron/Monitor 列表最大返回数；若省略: 输出长度控制会重复
    return cron_monitor_max_results(raw_value)  # 修改代码+TaskAgentToolsSplit: 复用 cron_monitor 中的结果数量限制；若没有这行代码，列表长度控制会分叉。

def monitor_result_status_for_agent(raw_value: Any) -> str:  # 新增代码+CronMonitor: 解析 monitor 最近观察状态；若省略: 状态标准化会散落在结果记录逻辑里
    return monitor_result_status(raw_value)  # 修改代码+TaskAgentToolsSplit: 复用 cron_monitor 中的结果状态解析；若没有这行代码，monitor 状态值会不统一。

def format_cron_record_for_agent(record: CronRecord) -> str:  # 新增代码+CronMonitor: 把定时任务记录格式化成稳定多字段文本；若省略: 创建和列表输出格式容易不一致
    return format_cron_record(record)  # 修改代码+TaskAgentToolsSplit: 复用 cron 记录格式化 helper；若没有这行代码，cron 输出格式会不统一。

def format_monitor_record_for_agent(record: MonitorRecord) -> str:  # 新增代码+CronMonitor: 把监控记录格式化成稳定多字段文本；若省略: 列表输出格式容易不一致
    return format_monitor_record(record)  # 修改代码+TaskAgentToolsSplit: 复用 monitor 记录格式化 helper；若没有这行代码，monitor 输出格式会不统一。


