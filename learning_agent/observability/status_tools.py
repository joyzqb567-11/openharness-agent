"""agent 状态查询类工具实现。"""  # 新增代码+AgentPyPhaseDStatusTools: 把状态查询工具从 agent.py 拆到 observability 层；若没有这个文件，主 agent 仍会承载状态读取和渲染细节。

from __future__ import annotations  # 新增代码+AgentPyPhaseDStatusTools: 延迟解析类型注解；若没有这行代码，脚本模式下复杂注解更容易受导入顺序影响。

import json  # 新增代码+AgentPyPhaseDStatusTools: 状态工具需要返回 JSON 文本；若没有这行代码，json 输出格式无法生成。
from typing import Any  # 新增代码+AgentPyPhaseDStatusTools: 用 Any 表示传入的 agent 对象；若没有这行代码，本模块会为了类型注解反向导入 agent.py。

try:  # 新增代码+AgentPyPhaseDStatusTools: 包运行模式下导入状态工具依赖；若没有这行代码，python -m 运行时无法读取统一状态源。
    from learning_agent.app.status_renderer import render_status_snapshot  # 新增代码+AgentPyPhaseDStatusTools: 导入人类可读状态渲染器；若没有这行代码，status_snapshot text 格式无法输出。
    from learning_agent.core.resume_loader import ResumeLoader  # 新增代码+AgentPyPhaseDStatusTools: 导入恢复上下文加载器；若没有这行代码，session_resume/compact_status/resume_report 无法工作。
    from learning_agent.core.session import SessionStore  # 新增代码+AgentPyPhaseDStatusTools: 导入 session 摘要存储；若没有这行代码，session_list 无法读取最近会话。
    from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+AgentPyPhaseDStatusTools: 导入状态事件 store；若没有这行代码，event_tail 无法读取事件流。
    from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+AgentPyPhaseDStatusTools: 导入统一状态聚合器；若没有这行代码，状态工具会和 CLI/SDK 分叉。
except ModuleNotFoundError as error:  # 新增代码+AgentPyPhaseDStatusTools: 捕获 start_oauth_agent.bat 直接脚本模式下的包路径差异；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.app", "learning_agent.app.status_renderer", "learning_agent.core", "learning_agent.core.resume_loader", "learning_agent.core.session", "learning_agent.runtime", "learning_agent.runtime.status_events", "learning_agent.runtime.status_snapshot"}:  # 新增代码+AgentPyPhaseDStatusTools: 只允许目标路径缺失时 fallback；若没有这行代码，内部真实导入错误会被误吞。
        raise  # 新增代码+AgentPyPhaseDStatusTools: 重新抛出真正的导入错误；若没有这行代码，排查状态工具问题会看不到根因。
    from app.status_renderer import render_status_snapshot  # 新增代码+AgentPyPhaseDStatusTools: 脚本模式下导入状态渲染器；若没有这行代码，bat 入口 status_snapshot text 格式会断开。
    from core.resume_loader import ResumeLoader  # 新增代码+AgentPyPhaseDStatusTools: 脚本模式下导入恢复上下文加载器；若没有这行代码，bat 入口无法读取 session resume。
    from core.session import SessionStore  # 新增代码+AgentPyPhaseDStatusTools: 脚本模式下导入 session store；若没有这行代码，bat 入口无法列出 session。
    from runtime.status_events import StatusEventStore  # 新增代码+AgentPyPhaseDStatusTools: 脚本模式下导入状态事件 store；若没有这行代码，bat 入口无法读取 event_tail。
    from runtime.status_snapshot import build_status_snapshot  # 新增代码+AgentPyPhaseDStatusTools: 脚本模式下导入统一状态聚合器；若没有这行代码，bat 入口状态工具会和 CLI/SDK 分裂。


def status_snapshot(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseDStatusTools: 函数段开始，生成统一状态快照工具输出；若没有这段函数，模型无法主动查看 run/task/queue/session 状态。
    output_format = str(arguments.get("format", "text")).strip().lower()  # 新增代码+AgentPyPhaseDStatusTools: 读取输出格式参数；若没有这行代码，模型无法选择 text 或 json。
    snapshot = build_status_snapshot(agent.workspace)  # 新增代码+AgentPyPhaseDStatusTools: 从当前工作区读取统一快照；若没有这行代码，工具不知道查看哪个项目。
    if output_format == "json":  # 新增代码+AgentPyPhaseDStatusTools: 支持机器可读 JSON；若没有这行代码，外部 agent 难以结构化解析状态。
        return json.dumps(snapshot, ensure_ascii=False, indent=2)  # 新增代码+AgentPyPhaseDStatusTools: 返回格式化 JSON；若没有这行代码，json 格式参数不会生效。
    return render_status_snapshot(snapshot)  # 新增代码+AgentPyPhaseDStatusTools: 默认返回人类可读状态页；若没有这行代码，用户看不到友好文本。
# 新增代码+AgentPyPhaseDStatusTools: 函数段结束，status_snapshot 到此结束；若没有这个边界说明，用户不容易看出状态快照逻辑已迁出 agent.py。


def task_status(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseDStatusTools: 函数段开始，查询持久任务状态；若没有这段函数，模型只能手动调用多个 task 工具。
    task_id = str(arguments.get("task_id", "")).strip()  # 新增代码+AgentPyPhaseDStatusTools: 读取可选 task_id；若没有这行代码，工具无法过滤单个任务。
    max_results = max(1, min(50, int(arguments.get("max_results", 20))))  # 新增代码+AgentPyPhaseDStatusTools: 限制返回任务数量；若没有这行代码，大量任务会撑爆上下文。
    tasks = build_status_snapshot(agent.workspace).get("tasks", [])  # 新增代码+AgentPyPhaseDStatusTools: 从快照读取任务列表；若没有这行代码，任务状态无数据源。
    filtered_tasks = [task for task in tasks if not task_id or str(task.get("task_id", "")) == task_id]  # 新增代码+AgentPyPhaseDStatusTools: 按 task_id 过滤；若没有这行代码，单任务查询仍会返回全部任务。
    visible_tasks = filtered_tasks[:max_results]  # 新增代码+AgentPyPhaseDStatusTools: 应用最大数量限制；若没有这行代码，max_results 参数无效。
    if not visible_tasks:  # 新增代码+AgentPyPhaseDStatusTools: 处理无匹配任务；若没有这行代码，模型会看到空标题不知原因。
        return "task_status：没有找到匹配任务。"  # 新增代码+AgentPyPhaseDStatusTools: 返回清楚空结果；若没有这行代码，调用方难以恢复。
    lines = ["Task Status"]  # 新增代码+AgentPyPhaseDStatusTools: 创建任务状态标题；若没有这行代码，输出缺少明确用途。
    for task in visible_tasks:  # 新增代码+AgentPyPhaseDStatusTools: 遍历可见任务；若没有这行代码，任务不会输出。
        lines.append(f"- task_id={task.get('task_id', '')} status={task.get('status', '')} kind={task.get('kind', '')} output_path={task.get('output_path', '')} output={(task.get('output', '') or task.get('error', ''))}")  # 新增代码+AgentPyPhaseDStatusTools: 输出任务关键字段；若没有这行代码，模型无法判断任务完成或失败。
    return "\n".join(lines)  # 新增代码+AgentPyPhaseDStatusTools: 返回任务状态文本；若没有这行代码，工具没有输出。
# 新增代码+AgentPyPhaseDStatusTools: 函数段结束，task_status 到此结束；若没有这个边界说明，用户不容易看出任务状态逻辑已迁出 agent.py。


def session_list(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseDStatusTools: 函数段开始，列出最近可恢复 session；若没有这段函数，模型不知道有哪些 session 可 resume。
    limit = max(1, min(50, int(arguments.get("limit", 20))))  # 新增代码+AgentPyPhaseDStatusTools: 读取并限制 session 数量；若没有这行代码，大量历史会刷屏。
    sessions = SessionStore(agent.workspace / "memory" / "sessions").list_recent_sessions(limit=limit)  # 新增代码+AgentPyPhaseDStatusTools: 从 session store 读取最近会话；若没有这行代码，工具没有数据源。
    if not sessions:  # 新增代码+AgentPyPhaseDStatusTools: 处理无 session；若没有这行代码，空列表不易理解。
        return "session_list：暂无可恢复 session。"  # 新增代码+AgentPyPhaseDStatusTools: 返回空结果说明；若没有这行代码，调用方不知道是没数据还是失败。
    return "Session List\n" + "\n".join(f"- session_id={session_id}" for session_id in sessions)  # 新增代码+AgentPyPhaseDStatusTools: 返回 session 列表；若没有这行代码，模型无法复制 session_id。
# 新增代码+AgentPyPhaseDStatusTools: 函数段结束，session_list 到此结束；若没有这个边界说明，用户不容易看出 session 列表逻辑已迁出 agent.py。


def session_resume(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseDStatusTools: 函数段开始，加载指定 session 的恢复上下文；若没有这段函数，模型无法审计 resume 内容。
    session_id = str(arguments.get("session_id", "")).strip()  # 新增代码+AgentPyPhaseDStatusTools: 读取 session_id 参数；若没有这行代码，恢复目标不明确。
    if not session_id:  # 新增代码+AgentPyPhaseDStatusTools: 校验必填参数；若没有这行代码，空 session 会变成难懂文件错误。
        return "session_resume 失败：缺少 session_id。"  # 新增代码+AgentPyPhaseDStatusTools: 返回清楚缺参错误；若没有这行代码，模型不知道如何修正。
    context = ResumeLoader(agent.workspace / "memory" / "sessions").load(session_id)  # 新增代码+AgentPyPhaseDStatusTools: 读取恢复上下文；若没有这行代码，工具无法返回恢复信息。
    return json.dumps(context.to_dict(), ensure_ascii=False, indent=2)  # 新增代码+AgentPyPhaseDStatusTools: 返回结构化恢复上下文；若没有这行代码，边界和一致性信息会丢失。
# 新增代码+AgentPyPhaseDStatusTools: 函数段结束，session_resume 到此结束；若没有这个边界说明，用户不容易看出 session 恢复读取逻辑已迁出 agent.py。


def compact_status(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseDStatusTools: 函数段开始，查看 compact/resume 状态；若没有这段函数，模型无法知道是否发生 compact。
    session_id = str(arguments.get("session_id", "")).strip()  # 新增代码+AgentPyPhaseDStatusTools: 读取可选 session_id；若没有这行代码，工具不能查看单个 session。
    store = SessionStore(agent.workspace / "memory" / "sessions")  # 新增代码+AgentPyPhaseDStatusTools: 打开 session store；若没有这行代码，工具无法列 session。
    session_ids = [session_id] if session_id else store.list_recent_sessions(limit=10)  # 新增代码+AgentPyPhaseDStatusTools: 决定要检查哪些 session；若没有这行代码，空参数时没有默认行为。
    loader = ResumeLoader(agent.workspace / "memory" / "sessions")  # 新增代码+AgentPyPhaseDStatusTools: 创建恢复器；若没有这行代码，边界读取逻辑会重复。
    lines = ["Compact Status"]  # 新增代码+AgentPyPhaseDStatusTools: 创建输出标题；若没有这行代码，输出用途不清楚。
    for current_session_id in session_ids:  # 新增代码+AgentPyPhaseDStatusTools: 遍历目标 session；若没有这行代码，状态不会输出。
        context = loader.load(current_session_id)  # 新增代码+AgentPyPhaseDStatusTools: 加载恢复上下文；若没有这行代码，无法读取 last_boundary。
        boundary = context.last_boundary  # 新增代码+AgentPyPhaseDStatusTools: 读取最后 compact 边界；若没有这行代码，后续字段会重复访问。
        if boundary is None:  # 新增代码+AgentPyPhaseDStatusTools: 处理未 compact 的 session；若没有这行代码，None 会导致属性错误。
            lines.append(f"- session_id={current_session_id} compacted=false message_count={context.consistency.get('message_count', 0)}")  # 新增代码+AgentPyPhaseDStatusTools: 输出未压缩状态；若没有这行代码，用户不知道该 session 没 compact。
        else:  # 新增代码+AgentPyPhaseDStatusTools: 处理已经 compact 的 session；若没有这行代码，边界信息不会展示。
            lines.append(f"- session_id={current_session_id} compacted=true boundary_uuid={boundary.boundary_uuid} removed={boundary.removed_message_count} retained={boundary.retained_message_count} reason={boundary.reason}")  # 新增代码+AgentPyPhaseDStatusTools: 输出 compact 边界摘要；若没有这行代码，用户无法审计压缩范围。
    return "\n".join(lines)  # 新增代码+AgentPyPhaseDStatusTools: 返回 compact 状态文本；若没有这行代码，工具没有输出。
# 新增代码+AgentPyPhaseDStatusTools: 函数段结束，compact_status 到此结束；若没有这个边界说明，用户不容易看出 compact 状态逻辑已迁出 agent.py。


def event_tail(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseDStatusTools: 函数段开始，读取状态事件尾巴；若没有这段函数，模型无法增量观察状态生态。
    limit = max(1, min(100, int(arguments.get("limit", 20))))  # 新增代码+AgentPyPhaseDStatusTools: 限制事件数量；若没有这行代码，长事件流会刷屏。
    since_sequence_raw = arguments.get("since_sequence")  # 新增代码+AgentPyPhaseDStatusTools: 读取可选增量起点；若没有这行代码，工具无法做增量查询。
    since_sequence = int(since_sequence_raw) if since_sequence_raw is not None else None  # 新增代码+AgentPyPhaseDStatusTools: 规范化增量起点；若没有这行代码，字符串参数会导致比较失败。
    events = StatusEventStore(agent.workspace / "memory" / "status").list_events(since_sequence=since_sequence, limit=limit)  # 新增代码+AgentPyPhaseDStatusTools: 读取状态事件；若没有这行代码，工具无数据源。
    return json.dumps([event.to_dict() for event in events], ensure_ascii=False, indent=2)  # 新增代码+AgentPyPhaseDStatusTools: 返回 JSON 事件列表；若没有这行代码，调用方难以结构化解析。
# 新增代码+AgentPyPhaseDStatusTools: 函数段结束，event_tail 到此结束；若没有这个边界说明，用户不容易看出事件尾部逻辑已迁出 agent.py。


def resume_report(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseDStatusTools: 函数段开始，返回精简恢复审计报告；若没有这段函数，模型只能读取很大的 session_resume 全量上下文。
    session_id = str(arguments.get("session_id", "")).strip()  # 新增代码+AgentPyPhaseDStatusTools: 读取目标 session_id；若没有这行代码，工具不知道审计哪个会话。
    if not session_id:  # 新增代码+AgentPyPhaseDStatusTools: 校验 session_id 是否缺失；若没有这行代码，空查询会产生难懂文件错误。
        return "resume_report 失败：缺少 session_id。"  # 新增代码+AgentPyPhaseDStatusTools: 返回可修正的缺参提示；若没有这行代码，模型不知道下一步该传什么。
    context = ResumeLoader(agent.workspace / "memory" / "sessions").load(session_id)  # 新增代码+AgentPyPhaseDStatusTools: 加载真实恢复上下文；若没有这行代码，报告没有 repair/tombstone 证据。
    report = {"session_id": session_id, "consistency": context.consistency, "repair_report": context.repair_report.to_dict(), "last_boundary": context.last_boundary.to_dict() if context.last_boundary is not None else None}  # 新增代码+AgentPyPhaseDStatusTools: 只返回恢复决策所需字段；若没有这行代码，模型会被全量消息淹没。
    return json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+AgentPyPhaseDStatusTools: 返回结构化 JSON；若没有这行代码，模型无法稳定判断 resume_safe/needs_review。
# 新增代码+AgentPyPhaseDStatusTools: 函数段结束，resume_report 到此结束；若没有这个边界说明，用户不容易看出恢复报告逻辑已迁出 agent.py。


def run_status(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseDStatusTools: 函数段开始，查询当前或指定 run 状态；若没有这段函数，模型无法直接判断长任务阶段位置。
    run_id = str(arguments.get("run_id", "")).strip()  # 新增代码+AgentPyPhaseDStatusTools: 读取可选 run_id；若没有这行代码，工具不能过滤指定 run。
    snapshot = build_status_snapshot(agent.workspace)  # 新增代码+AgentPyPhaseDStatusTools: 构建当前状态快照；若没有这行代码，run_status 没有数据源。
    runs = snapshot.get("runs", []) if isinstance(snapshot.get("runs", []), list) else []  # 新增代码+AgentPyPhaseDStatusTools: 安全读取 run 列表；若没有这行代码，坏快照会导致工具崩溃。
    selected_runs = [run for run in runs if not run_id or str(run.get("run_id", "")) == run_id]  # 新增代码+AgentPyPhaseDStatusTools: 按 run_id 过滤；若没有这行代码，指定 run 查询仍返回全量。
    payload = {"current_run": snapshot.get("current_run", {}), "current_turn": snapshot.get("current_turn", {}), "runs": selected_runs[:10]}  # 新增代码+AgentPyPhaseDStatusTools: 组合 run 和 turn 状态；若没有这行代码，模型需要再调用 status_snapshot 拼信息。
    return json.dumps(payload, ensure_ascii=False, indent=2)  # 新增代码+AgentPyPhaseDStatusTools: 返回 JSON 状态；若没有这行代码，调用方无法结构化读取。
# 新增代码+AgentPyPhaseDStatusTools: 函数段结束，run_status 到此结束；若没有这个边界说明，用户不容易看出 run 状态逻辑已迁出 agent.py。


def health_status(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPyPhaseDStatusTools: 函数段开始，查询 health/resume/verifier 风险状态；若没有这段函数，模型无法自查是否应该继续或暂停。
    snapshot = build_status_snapshot(agent.workspace)  # 新增代码+AgentPyPhaseDStatusTools: 构建当前状态快照；若没有这行代码，工具没有健康输入。
    payload = {"health": snapshot.get("health", {}), "resume": snapshot.get("resume", {}), "verifiers": snapshot.get("verifiers", {}), "current_run": snapshot.get("current_run", {})}  # 新增代码+AgentPyPhaseDStatusTools: 返回判断继续任务所需状态；若没有这行代码，模型要自己解析完整快照。
    return json.dumps(payload, ensure_ascii=False, indent=2)  # 新增代码+AgentPyPhaseDStatusTools: 返回结构化健康报告；若没有这行代码，模型无法稳定读取 warnings。
# 新增代码+AgentPyPhaseDStatusTools: 函数段结束，health_status 到此结束；若没有这个边界说明，用户不容易看出健康状态逻辑已迁出 agent.py。
