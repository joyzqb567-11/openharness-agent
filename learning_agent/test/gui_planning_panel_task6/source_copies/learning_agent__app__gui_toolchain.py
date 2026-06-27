"""Desktop GUI toolchain inventory payload helpers."""  # 新增代码+DesktopGUIToolchain：说明本模块只负责 GUI 工具链清单；如果没有这行，维护者容易把它和工具执行逻辑混在一起。

from __future__ import annotations  # 新增代码+DesktopGUIToolchain：启用延迟类型解析；如果没有这行，后续类型注解在旧运行环境里更容易出错。

import json  # 新增代码+DesktopGUIPlanning：读取 todo_state.json；如果没有这行，计划面板无法复用 todo_read 的持久状态。
from collections import Counter  # 新增代码+DesktopGUIPlanning：统计 task 状态数量；如果没有这行，计划面板只能显示明细不能显示总览。
from datetime import UTC, datetime  # 新增代码+DesktopGUIToolchain：生成稳定 UTC 时间戳；如果没有这行，GUI 无法知道清单刷新时间。
from pathlib import Path  # 新增代码+DesktopGUIToolchain：标注 workspace 路径类型；如果没有这行，函数签名会退回不清楚的 Any。
from typing import Any  # 新增代码+DesktopGUIToolchain：标注通用 JSON payload；如果没有这行，返回结构边界不清楚。

from learning_agent.app.gui_protocol import GUI_V2_SCHEMA_VERSION  # 新增代码+DesktopGUIToolchain：复用 GUI V2 协议版本；如果没有这行，工具链端点可能和其它 V2 payload 漂移。
from learning_agent.runtime.task_registry import TaskRegistry  # 新增代码+DesktopGUIPlanning：复用持久任务登记表；如果没有这行，GUI 会被迫自己扫 memory/tasks JSON。
from learning_agent.runtime.team_registry import TeamRegistry  # 新增代码+DesktopGUIPlanning：复用持久 team 登记表；如果没有这行，GUI 看不到 list_peers/read_peer_messages 的真实状态。
from learning_agent.tools.catalog import build_builtin_tool_catalog  # 新增代码+DesktopGUIToolchain：复用已有内置工具目录；如果没有这行，GUI 会被迫硬编码一份工具清单。
from learning_agent.tools.types import AgentTool  # 新增代码+DesktopGUIToolchain：复用工具元数据类型；如果没有这行，helper 无法用清晰字段读取目录。


TOOLCHAIN_GROUP_LABELS: dict[str, str] = {  # 新增代码+DesktopGUIToolchain：分组中文/英文标签表开始；如果没有这段，GUI 只能显示机器化 capability id。
    "core": "Core Tools",  # 新增代码+DesktopGUIToolchain：标记核心读写编辑工具；如果没有这行，基础工具会落入不友好的 unknown 分组。
    "file_operations": "File Operations",  # 新增代码+DesktopGUIToolchain：标记文件操作工具；如果没有这行，文件读写能力无法被用户快速识别。
    "memory": "Memory",  # 新增代码+DesktopGUIToolchain：标记记忆工具；如果没有这行，append_memory 会混在普通工具里。
    "planning": "Planning",  # 新增代码+DesktopGUIToolchain：标记计划工具；如果没有这行，todo/plan 能力不会形成产品化分区。
    "execution": "Execution",  # 新增代码+DesktopGUIToolchain：标记执行工具；如果没有这行，后台命令能力不会进入清晰分组。
    "notebook": "Notebook",  # 新增代码+DesktopGUIToolchain：标记 Notebook 工具；如果没有这行，notebook_read/edit 会缺少分区。
    "mcp": "MCP",  # 新增代码+DesktopGUIToolchain：标记 MCP 工具；如果没有这行，资源/提示/stream 能力不容易被发现。
    "delegation": "Delegation",  # 新增代码+DesktopGUIToolchain：标记子任务和 team 工具；如果没有这行，多 agent 能力会被埋在列表里。
    "diagnostics": "Diagnostics",  # 新增代码+DesktopGUIToolchain：标记诊断工具；如果没有这行，LSP/REPL 能力缺少入口感。
    "long_running_work": "Long Running Work",  # 新增代码+DesktopGUIToolchain：标记长任务工具；如果没有这行，cron/session/status 等能力不易扫描。
    "computer_use": "Computer Use",  # 新增代码+DesktopGUIToolchain：标记桌面控制工具；如果没有这行，Computer Use 工具链不会被产品化强调。
}  # 新增代码+DesktopGUIToolchain：分组标签表结束；如果没有这行，Python 字典语法不完整。

TOOLCHAIN_GROUP_ORDER: list[str] = [  # 新增代码+DesktopGUIToolchain：分组排序表开始；如果没有这段，GUI 顺序会随字典或工具顺序漂移。
    "core",  # 新增代码+DesktopGUIToolchain：核心工具排第一；如果没有这行，用户可能先看到低频工具。
    "file_operations",  # 新增代码+DesktopGUIToolchain：文件工具紧跟核心工具；如果没有这行，开发常用能力不够靠前。
    "planning",  # 新增代码+DesktopGUIToolchain：计划能力靠前；如果没有这行，长任务不跑偏相关工具不明显。
    "execution",  # 新增代码+DesktopGUIToolchain：执行能力靠前；如果没有这行，后台命令链路不易发现。
    "long_running_work",  # 新增代码+DesktopGUIToolchain：长任务能力靠前；如果没有这行，harness 相关能力不够突出。
    "computer_use",  # 新增代码+DesktopGUIToolchain：桌面控制能力靠前；如果没有这行，用户看不出 GUI 已接入真实桌面工具。
    "mcp",  # 新增代码+DesktopGUIToolchain：MCP 能力随后展示；如果没有这行，外部工具生态缺少固定位置。
    "delegation",  # 新增代码+DesktopGUIToolchain：委派能力随后展示；如果没有这行，子 agent 工具会散在后面。
    "diagnostics",  # 新增代码+DesktopGUIToolchain：诊断能力随后展示；如果没有这行，排查工具不易找到。
    "notebook",  # 新增代码+DesktopGUIToolchain：Notebook 能力随后展示；如果没有这行，notebook 工具可能漂移。
    "memory",  # 新增代码+DesktopGUIToolchain：记忆能力最后展示；如果没有这行，低频 append_memory 可能插入其它分组。
]  # 新增代码+DesktopGUIToolchain：分组排序表结束；如果没有这行，Python 列表语法不完整。

PLANNING_TOOL_NAMES: list[str] = [  # 新增代码+DesktopGUIPlanning：声明计划/委派面板关注的工具名；如果没有这段，GUI 不知道哪些工具属于计划协作控制中心。
    "todo_read",  # 新增代码+DesktopGUIPlanning：展示读取 todo 状态的工具；如果没有这行，用户看不出 GUI 复用了 todo_read。
    "todo_write",  # 新增代码+DesktopGUIPlanning：展示写 todo 的工具但本阶段只读；如果没有这行，用户看不出后续 mutation 能接到哪里。
    "enter_plan_mode",  # 新增代码+DesktopGUIPlanning：展示进入计划模式工具；如果没有这行，计划模式能力会藏在工具清单里。
    "exit_plan_mode",  # 新增代码+DesktopGUIPlanning：展示退出计划模式工具；如果没有这行，确认计划的主链路不可见。
    "verify_plan_execution",  # 新增代码+DesktopGUIPlanning：展示计划验收工具；如果没有这行，长任务收尾门禁不可见。
    "task",  # 新增代码+DesktopGUIPlanning：展示启动子 agent 任务工具；如果没有这行，多 agent 启动入口会被漏掉。
    "task_list",  # 新增代码+DesktopGUIPlanning：展示任务列表工具；如果没有这行，GUI 任务区和工具目录对不上。
    "task_get",  # 新增代码+DesktopGUIPlanning：展示任务详情工具；如果没有这行，后续详情抽屉没有明确复用目标。
    "task_output",  # 新增代码+DesktopGUIPlanning：展示任务输出工具；如果没有这行，长输出读取链路不可见。
    "task_update",  # 新增代码+DesktopGUIPlanning：展示任务更新工具；如果没有这行，用户看不出状态可被 agent 管理。
    "task_stop",  # 新增代码+DesktopGUIPlanning：展示任务停止工具；如果没有这行，未来 GUI 停止子任务会缺少能力提示。
    "team_create",  # 新增代码+DesktopGUIPlanning：展示创建 peer 工具；如果没有这行，团队协作入口不可见。
    "team_start_task",  # 新增代码+DesktopGUIPlanning：展示把 peer 绑定后台任务的工具；如果没有这行，team 到 task 的关键链路不可见。
    "send_message",  # 新增代码+DesktopGUIPlanning：展示给 peer 发消息工具；如果没有这行，协作消息链路不可见。
    "list_peers",  # 新增代码+DesktopGUIPlanning：展示读取 peer 列表工具；如果没有这行，GUI peer 区和工具目录对不上。
    "read_peer_messages",  # 新增代码+DesktopGUIPlanning：展示读取 peer inbox 工具；如果没有这行，GUI 消息区和工具目录对不上。
    "ack_peer_message",  # 新增代码+DesktopGUIPlanning：展示确认 peer 消息工具；如果没有这行，未来 GUI 确认按钮缺少能力提示。
    "team_delete",  # 新增代码+DesktopGUIPlanning：展示删除 peer 工具；如果没有这行，高风险团队 mutation 不会被用户看见。
]  # 新增代码+DesktopGUIPlanning：计划/委派工具名表结束；如果没有这行，Python 列表语法不完整。

ACTIVE_TASK_STATUSES: set[str] = {"pending", "queued", "running", "needs_input"}  # 新增代码+DesktopGUIPlanning：集中定义仍需关注的 task 状态；如果没有这行，active_task_count 会散落硬编码。


def _tool_group_id(tool: AgentTool) -> str:  # 新增代码+DesktopGUIToolchain：函数段开始，计算工具所属 GUI 分组；如果没有这段，工具分组逻辑会散落在 payload 构建里。
    return tool.capability_pack.strip() or "core"  # 新增代码+DesktopGUIToolchain：优先使用已有 capability_pack，空值归入 core；如果没有这行，未映射工具会丢失分组。
# 新增代码+DesktopGUIToolchain：函数段结束，_tool_group_id 到此结束；如果没有边界说明，初学者不易看出分组规则。


def _tool_status(tool: AgentTool) -> str:  # 新增代码+DesktopGUIToolchain：函数段开始，把工具元数据转成 GUI 状态；如果没有这段，前端只能靠布尔值猜工具可见性。
    if tool.always_load:  # 新增代码+DesktopGUIToolchain：判断工具是否首轮常驻；如果没有这行，核心工具和延迟工具无法区分。
        return "ready"  # 新增代码+DesktopGUIToolchain：常驻工具标记 ready；如果没有这行，GUI 无法显示核心能力已就绪。
    if tool.should_defer:  # 新增代码+DesktopGUIToolchain：判断工具是否延迟加载；如果没有这行，低频工具会被误认为已首轮暴露。
        return "deferred"  # 新增代码+DesktopGUIToolchain：延迟工具标记 deferred；如果没有这行，用户看不出工具可通过 tool_search 激活。
    return "available"  # 新增代码+DesktopGUIToolchain：其它工具标记 available；如果没有这行，函数可能返回 None。
# 新增代码+DesktopGUIToolchain：函数段结束，_tool_status 到此结束；如果没有边界说明，初学者不易看出状态映射范围。


def _tool_payload(tool: AgentTool) -> dict[str, Any]:  # 新增代码+DesktopGUIToolchain：函数段开始，把 AgentTool 转成 GUI 安全字段；如果没有这段，前端会直接依赖内部 dataclass。
    return {  # 新增代码+DesktopGUIToolchain：返回单个工具 payload；如果没有这行，函数无法输出 JSON 对象。
        "name": tool.name,  # 新增代码+DesktopGUIToolchain：暴露工具名；如果没有这行，GUI 列表没有主键。
        "description": tool.description,  # 新增代码+DesktopGUIToolchain：暴露工具说明；如果没有这行，用户不知道工具用途。
        "category": _tool_group_id(tool),  # 新增代码+DesktopGUIToolchain：暴露能力分组；如果没有这行，前端无法做筛选和徽标。
        "source": tool.source,  # 新增代码+DesktopGUIToolchain：暴露内置/MCP 来源；如果没有这行，用户看不出工具来自哪里。
        "available": True,  # 新增代码+DesktopGUIToolchain：标记工具在目录中可用；如果没有这行，前端无法统一渲染状态灯。
        "status": _tool_status(tool),  # 新增代码+DesktopGUIToolchain：暴露 ready/deferred/available 状态；如果没有这行，延迟加载语义不可见。
        "risk_level": tool.risk_level,  # 新增代码+DesktopGUIToolchain：暴露风险级别；如果没有这行，GUI 无法提示危险工具。
        "read_only": tool.is_read_only,  # 新增代码+DesktopGUIToolchain：暴露只读属性；如果没有这行，用户无法区分读取和写入工具。
        "destructive": tool.is_destructive,  # 新增代码+DesktopGUIToolchain：暴露破坏性属性；如果没有这行，危险写入工具不够显眼。
        "permission_mode": tool.permission_mode,  # 新增代码+DesktopGUIToolchain：暴露权限模式；如果没有这行，GUI 无法解释工具是否需要确认。
        "reuse_module": "learning_agent.tools.catalog",  # 新增代码+DesktopGUIToolchain：标记复用模块；如果没有这行，用户无法确认 GUI 没有重写工具链。
    }  # 新增代码+DesktopGUIToolchain：单工具 payload 结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIToolchain：函数段结束，_tool_payload 到此结束；如果没有边界说明，初学者不易看出字段白名单。


def _group_sort_key(group_id: str) -> tuple[int, str]:  # 新增代码+DesktopGUIToolchain：函数段开始，给工具组排序；如果没有这段，GUI 分组顺序不稳定。
    if group_id in TOOLCHAIN_GROUP_ORDER:  # 新增代码+DesktopGUIToolchain：判断是否有预设排序；如果没有这行，index 查询可能抛异常。
        return (TOOLCHAIN_GROUP_ORDER.index(group_id), group_id)  # 新增代码+DesktopGUIToolchain：返回预设顺序和名称；如果没有这行，核心分组无法靠前。
    return (len(TOOLCHAIN_GROUP_ORDER), group_id)  # 新增代码+DesktopGUIToolchain：未知分组排在最后并按名称稳定排序；如果没有这行，新能力包顺序会漂移。
# 新增代码+DesktopGUIToolchain：函数段结束，_group_sort_key 到此结束；如果没有边界说明，初学者不易看出排序规则。


def _safe_planning_text(value: Any, fallback: str = "", max_chars: int = 240) -> str:  # 新增代码+DesktopGUIPlanning：函数段开始，把未知 planning 字段转成短文本；如果没有这段，长 prompt 或坏类型会撑破 GUI。
    text = str(value if value is not None else fallback).replace("\r", " ").replace("\n", " ").strip()  # 新增代码+DesktopGUIPlanning：把 None、多行和空白收敛成单行；如果没有这行，右侧面板可能出现不可控换行。
    if not text:  # 新增代码+DesktopGUIPlanning：处理空文本；如果没有这行，空字段会绕过 fallback。
        text = fallback  # 新增代码+DesktopGUIPlanning：使用兜底文本；如果没有这行，空状态会显示空白。
    return text[:max_chars]  # 新增代码+DesktopGUIPlanning：限制文本长度；如果没有这行，任务 prompt 或消息正文可能让 payload 和 UI 过大。
# 新增代码+DesktopGUIPlanning：函数段结束，_safe_planning_text 到此结束；如果没有边界说明，用户不易看出文本脱敏范围。


def _todo_payload(todo: Any, index: int) -> dict[str, Any]:  # 新增代码+DesktopGUIPlanning：函数段开始，把 todo 条目白名单化；如果没有这段，未知字段或 secret 可能进入 GUI。
    todo_record = todo if isinstance(todo, dict) else {}  # 新增代码+DesktopGUIPlanning：只信任对象形状；如果没有这行，字符串 todo 会导致字段读取异常。
    return {  # 新增代码+DesktopGUIPlanning：返回单条 todo 安全摘要；如果没有这行，函数没有 JSON 输出。
        "id": _safe_planning_text(todo_record.get("id", f"todo_{index}"), f"todo_{index}", 120),  # 新增代码+DesktopGUIPlanning：生成稳定条目 id；如果没有这行，前端列表 key 不稳定。
        "content": _safe_planning_text(todo_record.get("content", ""), "未命名任务", 220),  # 新增代码+DesktopGUIPlanning：显示任务内容摘要；如果没有这行，todo 列表没有主体文本。
        "status": _safe_planning_text(todo_record.get("status", "pending"), "pending", 40),  # 新增代码+DesktopGUIPlanning：显示 pending/in_progress/completed 状态；如果没有这行，用户无法判断进度。
        "priority": _safe_planning_text(todo_record.get("priority", "medium"), "medium", 40),  # 新增代码+DesktopGUIPlanning：显示优先级；如果没有这行，计划面板缺少排序线索。
    }  # 新增代码+DesktopGUIPlanning：todo 安全摘要结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIPlanning：函数段结束，_todo_payload 到此结束；如果没有边界说明，用户不易看出 todo 白名单范围。


def _read_gui_todos(workspace_path: Path) -> tuple[list[dict[str, Any]], str, str]:  # 新增代码+DesktopGUIPlanning：函数段开始，读取 todo_state.json；如果没有这段，GUI 无法展示 todo_read 的持久状态。
    todo_path = workspace_path / "todo_state.json"  # 新增代码+DesktopGUIPlanning：复用 LearningAgent.todo_path 的固定文件名；如果没有这行，GUI 会读错 todo 位置。
    if not todo_path.exists():  # 新增代码+DesktopGUIPlanning：处理首次运行没有 todo 文件；如果没有这行，空状态会被误报成错误。
        return [], "empty", ""  # 新增代码+DesktopGUIPlanning：返回正常空态；如果没有这行，前端不知道暂无数据是正常情况。
    try:  # 新增代码+DesktopGUIPlanning：保护 JSON 读取；如果没有这行，坏 todo 文件会让整个 planning endpoint 500。
        payload = json.loads(todo_path.read_text(encoding="utf-8"))  # 新增代码+DesktopGUIPlanning：读取并解析 todo_state.json；如果没有这行，todo 列表没有事实源。
    except Exception:  # 新增代码+DesktopGUIPlanning：捕获读取或解析异常；如果没有这行，用户看不到安全降级信息。
        return [], "failed", "todo_state.json 暂时不可读或格式不正确。"  # 新增代码+DesktopGUIPlanning：返回脱敏错误；如果没有这行，异常细节可能泄漏路径或栈信息。
    raw_todos = payload.get("todos", []) if isinstance(payload, dict) else []  # 新增代码+DesktopGUIPlanning：只从对象 payload 读取 todos；如果没有这行，坏结构会让后续遍历出错。
    if not isinstance(raw_todos, list):  # 新增代码+DesktopGUIPlanning：校验 todos 必须是数组；如果没有这行，字符串 todos 会被逐字渲染。
        return [], "failed", "todo_state.json 中的 todos 必须是数组。"  # 新增代码+DesktopGUIPlanning：返回结构错误；如果没有这行，用户不知道该修正哪里。
    todos = [_todo_payload(todo, index) for index, todo in enumerate(raw_todos)]  # 新增代码+DesktopGUIPlanning：白名单化每条 todo；如果没有这行，未知字段可能直接进 GUI。
    return todos, "ready" if todos else "empty", ""  # 新增代码+DesktopGUIPlanning：返回 todo 列表和状态；如果没有这行，调用方拿不到读取结果。
# 新增代码+DesktopGUIPlanning：函数段结束，_read_gui_todos 到此结束；如果没有边界说明，用户不易看出 todo 读取范围。


def _task_record_payload(record: Any) -> dict[str, Any]:  # 新增代码+DesktopGUIPlanning：函数段开始，把 TaskRecord 收敛成 GUI 摘要；如果没有这段，前端会直接依赖 runtime dataclass 全字段。
    metadata = getattr(record, "metadata", {})  # 新增代码+DesktopGUIPlanning：读取任务扩展字段；如果没有这行，label 等摘要会丢失。
    metadata = metadata if isinstance(metadata, dict) else {}  # 新增代码+DesktopGUIPlanning：防御坏 metadata 类型；如果没有这行，下面 get 会崩溃。
    output = _safe_planning_text(getattr(record, "output", ""), "", 260)  # 新增代码+DesktopGUIPlanning：截断输出摘要；如果没有这行，长输出会撑爆右侧面板。
    error = _safe_planning_text(getattr(record, "error", ""), "", 220)  # 新增代码+DesktopGUIPlanning：截断错误摘要；如果没有这行，失败原因可能过长。
    return {  # 新增代码+DesktopGUIPlanning：返回任务安全摘要；如果没有这行，函数没有 JSON 输出。
        "task_id": _safe_planning_text(getattr(record, "task_id", ""), "task", 120),  # 新增代码+DesktopGUIPlanning：显示任务 id；如果没有这行，用户无法定位 task_get/task_output 目标。
        "label": _safe_planning_text(metadata.get("label", ""), "", 120),  # 新增代码+DesktopGUIPlanning：显示任务短标签；如果没有这行，多任务列表不易扫描。
        "kind": _safe_planning_text(getattr(record, "kind", "agent"), "agent", 80),  # 新增代码+DesktopGUIPlanning：显示任务类型；如果没有这行，后台 shell 和 agent 任务不可区分。
        "status": _safe_planning_text(getattr(record, "status", "unknown"), "unknown", 60),  # 新增代码+DesktopGUIPlanning：显示任务状态；如果没有这行，任务区没有核心进度。
        "prompt_summary": _safe_planning_text(getattr(record, "prompt", ""), "无任务目标", 260),  # 新增代码+DesktopGUIPlanning：显示任务目标摘要；如果没有这行，用户不知道任务在做什么。
        "output_summary": output,  # 新增代码+DesktopGUIPlanning：显示短输出；如果没有这行，完成任务没有结果预览。
        "error_summary": error,  # 新增代码+DesktopGUIPlanning：显示短错误；如果没有这行，失败任务没有原因。
        "background": bool(getattr(record, "background", False)),  # 新增代码+DesktopGUIPlanning：显示是否后台运行；如果没有这行，用户无法区分同步/异步任务。
        "has_output_file": bool(_safe_planning_text(getattr(record, "output_path", ""), "", 20)),  # 新增代码+DesktopGUIPlanning：只暴露是否有输出文件；如果没有这行，GUI 可能泄漏本机完整路径。
        "owner_run_id": _safe_planning_text(getattr(record, "owner_run_id", ""), "", 120),  # 新增代码+DesktopGUIPlanning：显示所属 run；如果没有这行，子任务难以和 harness run 对齐。
        "created_at": _safe_planning_text(getattr(record, "created_at", ""), "", 120),  # 新增代码+DesktopGUIPlanning：显示创建时间；如果没有这行，任务时间线缺起点。
        "updated_at": _safe_planning_text(getattr(record, "updated_at", ""), "", 120),  # 新增代码+DesktopGUIPlanning：显示更新时间；如果没有这行，用户不知道状态是否新鲜。
        "completed_at": _safe_planning_text(getattr(record, "completed_at", ""), "", 120),  # 新增代码+DesktopGUIPlanning：显示完成时间；如果没有这行，终态任务缺收束时间。
    }  # 新增代码+DesktopGUIPlanning：任务安全摘要结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIPlanning：函数段结束，_task_record_payload 到此结束；如果没有边界说明，用户不易看出任务白名单范围。


def _peer_message_payload(peer: Any, message: Any) -> dict[str, Any]:  # 新增代码+DesktopGUIPlanning：函数段开始，把 peer inbox 消息白名单化；如果没有这段，消息对象内部字段可能直接进 GUI。
    acknowledged_at = _safe_planning_text(getattr(message, "acknowledged_at", ""), "", 120)  # 新增代码+DesktopGUIPlanning：读取确认时间；如果没有这行，pending/ack 状态无法判断。
    return {  # 新增代码+DesktopGUIPlanning：返回消息安全摘要；如果没有这行，函数没有 JSON 输出。
        "peer_id": _safe_planning_text(getattr(peer, "peer_id", ""), "peer", 120),  # 新增代码+DesktopGUIPlanning：显示消息归属 peer id；如果没有这行，消息无法回到具体团队成员。
        "peer_name": _safe_planning_text(getattr(peer, "name", ""), "peer", 120),  # 新增代码+DesktopGUIPlanning：显示消息归属 peer 名称；如果没有这行，消息列表不易读。
        "message_id": _safe_planning_text(getattr(message, "message_id", ""), "message", 120),  # 新增代码+DesktopGUIPlanning：显示消息 id；如果没有这行，未来 ack 按钮无法定位。
        "sender": _safe_planning_text(getattr(message, "sender", ""), "peer", 120),  # 新增代码+DesktopGUIPlanning：显示发送方；如果没有这行，用户不知道消息来源。
        "content_summary": _safe_planning_text(getattr(message, "content", ""), "空消息", 260),  # 新增代码+DesktopGUIPlanning：显示消息摘要；如果没有这行，消息区没有主体内容。
        "created_at": _safe_planning_text(getattr(message, "created_at", ""), "", 120),  # 新增代码+DesktopGUIPlanning：显示创建时间；如果没有这行，消息时间线不可见。
        "acknowledged_at": acknowledged_at,  # 新增代码+DesktopGUIPlanning：显示确认时间；如果没有这行，ack 状态没有证据。
        "ack_note": _safe_planning_text(getattr(message, "ack_note", ""), "", 180),  # 新增代码+DesktopGUIPlanning：显示确认备注摘要；如果没有这行，用户看不到处理说明。
        "status": "acknowledged" if acknowledged_at else "pending",  # 新增代码+DesktopGUIPlanning：把确认时间转成状态；如果没有这行，前端要重复推导 pending。
    }  # 新增代码+DesktopGUIPlanning：消息安全摘要结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIPlanning：函数段结束，_peer_message_payload 到此结束；如果没有边界说明，用户不易看出消息白名单范围。


def _peer_payload(peer: Any) -> dict[str, Any]:  # 新增代码+DesktopGUIPlanning：函数段开始，把 TeamPeer 收敛成 GUI 摘要；如果没有这段，前端会直接依赖 team dataclass。
    inbox = getattr(peer, "inbox", [])  # 新增代码+DesktopGUIPlanning：读取 peer inbox；如果没有这行，消息计数没有输入。
    inbox = inbox if isinstance(inbox, list) else []  # 新增代码+DesktopGUIPlanning：防御坏 inbox 类型；如果没有这行，遍历可能崩溃。
    pending_messages = [message for message in inbox if not _safe_planning_text(getattr(message, "acknowledged_at", ""), "", 120)]  # 新增代码+DesktopGUIPlanning：统计未确认消息；如果没有这行，GUI 无法显示待处理数。
    latest_message = inbox[-1] if inbox else None  # 新增代码+DesktopGUIPlanning：取最近一条消息；如果没有这行，peer 卡片缺少最新上下文。
    return {  # 新增代码+DesktopGUIPlanning：返回 peer 安全摘要；如果没有这行，函数没有 JSON 输出。
        "peer_id": _safe_planning_text(getattr(peer, "peer_id", ""), "peer", 120),  # 新增代码+DesktopGUIPlanning：显示 peer id；如果没有这行，后续 send/read/ack 无法定位。
        "name": _safe_planning_text(getattr(peer, "name", ""), "peer", 120),  # 新增代码+DesktopGUIPlanning：显示 peer 名称；如果没有这行，团队列表不可读。
        "role": _safe_planning_text(getattr(peer, "role", ""), "peer", 120),  # 新增代码+DesktopGUIPlanning：显示 peer 角色；如果没有这行，分工不可见。
        "status": _safe_planning_text(getattr(peer, "status", "idle"), "idle", 80),  # 新增代码+DesktopGUIPlanning：显示 peer 状态；如果没有这行，用户不知道 peer 是否空闲。
        "notes": _safe_planning_text(getattr(peer, "notes", ""), "", 220),  # 新增代码+DesktopGUIPlanning：显示 peer 备注摘要；如果没有这行，协作上下文会丢失。
        "message_count": len(inbox),  # 新增代码+DesktopGUIPlanning：显示 inbox 总数；如果没有这行，消息规模不可见。
        "pending_message_count": len(pending_messages),  # 新增代码+DesktopGUIPlanning：显示待确认消息数；如果没有这行，用户不知道哪里需要处理。
        "latest_message_summary": _safe_planning_text(getattr(latest_message, "content", ""), "", 220) if latest_message else "",  # 新增代码+DesktopGUIPlanning：显示最近消息摘要；如果没有这行，peer 卡片缺少最新动态。
        "bound_task_id": _safe_planning_text(getattr(peer, "bound_task_id", ""), "", 120),  # 新增代码+DesktopGUIPlanning：显示绑定任务 id；如果没有这行，peer 到 task 的链路不可见。
        "bound_task_started_at": _safe_planning_text(getattr(peer, "bound_task_started_at", ""), "", 120),  # 新增代码+DesktopGUIPlanning：显示绑定任务开始时间；如果没有这行，用户不知道 peer 何时开始工作。
        "created_at": _safe_planning_text(getattr(peer, "created_at", ""), "", 120),  # 新增代码+DesktopGUIPlanning：显示创建时间；如果没有这行，团队时间线缺起点。
    }  # 新增代码+DesktopGUIPlanning：peer 安全摘要结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIPlanning：函数段结束，_peer_payload 到此结束；如果没有边界说明，用户不易看出 peer 白名单范围。


def _planning_tool_payload(name: str, tool_map: dict[str, AgentTool]) -> dict[str, Any]:  # 新增代码+DesktopGUIPlanning：函数段开始，生成计划工具可用性摘要；如果没有这段，前端无法解释某个工具为何不可见。
    tool = tool_map.get(name)  # 新增代码+DesktopGUIPlanning：从已有工具目录查找工具；如果没有这行，GUI 会和真实 catalog 分裂。
    if tool is None:  # 新增代码+DesktopGUIPlanning：处理目录没有该工具；如果没有这行，缺失工具会触发 None 访问。
        return {"name": name, "category": "planning", "available": False, "status": "unavailable", "read_only": False, "destructive": False, "risk_level": "unknown", "safe_unavailable_reason": "当前工具目录没有注册该工具。", "reuse_module": "learning_agent.tools.catalog"}  # 新增代码+DesktopGUIPlanning：返回安全不可用原因；如果没有这行，前端无法显示缺失状态。
    payload = _tool_payload(tool)  # 新增代码+DesktopGUIPlanning：复用已有工具 payload 白名单；如果没有这行，计划面板会复制一套元数据逻辑。
    payload["safe_unavailable_reason"] = ""  # 新增代码+DesktopGUIPlanning：可用工具没有不可用原因；如果没有这行，前端字段不稳定。
    return payload  # 新增代码+DesktopGUIPlanning：返回工具摘要；如果没有这行，函数没有输出。
# 新增代码+DesktopGUIPlanning：函数段结束，_planning_tool_payload 到此结束；如果没有边界说明，用户不易看出工具可用性范围。


def build_gui_planning_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIPlanning：函数段开始，构建计划/委派只读状态；如果没有这段，GUI 只能靠聊天文本猜 todo 和子任务状态。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIPlanning：规范化 workspace 路径；如果没有这行，registry 和 todo 读取位置不稳定。
    tools = build_builtin_tool_catalog()  # 新增代码+DesktopGUIPlanning：读取真实内置工具目录；如果没有这行，计划工具可用性会变成硬编码假状态。
    tool_map = {tool.name: tool for tool in tools}  # 新增代码+DesktopGUIPlanning：按名称建立工具索引；如果没有这行，每个工具查找都要重复遍历。
    planning_tools = [_planning_tool_payload(name, tool_map) for name in PLANNING_TOOL_NAMES]  # 新增代码+DesktopGUIPlanning：生成计划/委派工具摘要；如果没有这行，GUI 不知道哪些能力可用。
    todos, todo_status, todo_error = _read_gui_todos(workspace_path)  # 新增代码+DesktopGUIPlanning：读取 todo_state.json；如果没有这行，todo 区没有真实数据。
    status_degraded = bool(todo_error)  # 新增代码+DesktopGUIPlanning：todo 读取失败时标记降级；如果没有这行，前端会把坏文件误认为正常空态。
    safe_errors: list[str] = [todo_error] if todo_error else []  # 新增代码+DesktopGUIPlanning：准备安全错误列表；如果没有这行，多个读取失败无法合并展示。
    try:  # 新增代码+DesktopGUIPlanning：保护 task registry 读取；如果没有这行，坏任务文件可能让整个 endpoint 失败。
        task_records = TaskRegistry(workspace_path / "memory" / "tasks").list_tasks()  # 新增代码+DesktopGUIPlanning：复用 LearningAgent.task_registry 的持久目录；如果没有这行，GUI 不会看到 task_list 的事实源。
        task_status = "ready" if task_records else "empty"  # 新增代码+DesktopGUIPlanning：给任务区生成读取状态；如果没有这行，前端无法区分正常空态和错误。
    except Exception:  # 新增代码+DesktopGUIPlanning：捕获任务 registry 异常；如果没有这行，坏 JSON 或锁错误会让 HTTP 500。
        task_records = []  # 新增代码+DesktopGUIPlanning：任务读取失败时返回空列表；如果没有这行，后续变量未定义。
        task_status = "failed"  # 新增代码+DesktopGUIPlanning：标记任务读取失败；如果没有这行，前端无法显示降级。
        status_degraded = True  # 新增代码+DesktopGUIPlanning：把任务读取失败计入整体降级；如果没有这行，用户会误信任务数据完整。
        safe_errors.append("任务登记表暂时不可读。")  # 新增代码+DesktopGUIPlanning：记录脱敏错误；如果没有这行，用户不知道降级来源。
    task_payloads = [_task_record_payload(record) for record in sorted(task_records, key=lambda item: _safe_planning_text(getattr(item, "updated_at", ""), "", 120), reverse=True)]  # 新增代码+DesktopGUIPlanning：按更新时间倒序输出任务摘要；如果没有这行，任务列表顺序会漂移。
    task_status_counts = Counter(_safe_planning_text(getattr(record, "status", "unknown"), "unknown", 60) for record in task_records)  # 新增代码+DesktopGUIPlanning：统计任务状态；如果没有这行，标题区无法显示运行中规模。
    active_task_count = sum(1 for record in task_records if _safe_planning_text(getattr(record, "status", "unknown"), "unknown", 60) in ACTIVE_TASK_STATUSES)  # 新增代码+DesktopGUIPlanning：统计仍需关注的任务；如果没有这行，用户要逐条判断 active。
    try:  # 新增代码+DesktopGUIPlanning：保护 team registry 读取；如果没有这行，坏 peer 文件会拖垮 planning endpoint。
        peers = TeamRegistry(workspace_path / "memory" / "team").list_peers()  # 新增代码+DesktopGUIPlanning：复用 LearningAgent.team_registry 的持久目录；如果没有这行，GUI 不会看到 list_peers 的事实源。
        team_status = "ready" if peers else "empty"  # 新增代码+DesktopGUIPlanning：给团队区生成读取状态；如果没有这行，前端无法区分正常空态和错误。
    except Exception:  # 新增代码+DesktopGUIPlanning：捕获 team registry 异常；如果没有这行，坏 peer JSON 会导致 HTTP 500。
        peers = []  # 新增代码+DesktopGUIPlanning：team 读取失败时返回空列表；如果没有这行，后续变量未定义。
        team_status = "failed"  # 新增代码+DesktopGUIPlanning：标记团队读取失败；如果没有这行，前端无法显示降级。
        status_degraded = True  # 新增代码+DesktopGUIPlanning：把团队读取失败计入整体降级；如果没有这行，用户会误信团队数据完整。
        safe_errors.append("团队登记表暂时不可读。")  # 新增代码+DesktopGUIPlanning：记录脱敏错误；如果没有这行，用户不知道降级来源。
    peer_payloads = [_peer_payload(peer) for peer in peers]  # 新增代码+DesktopGUIPlanning：白名单化 peer 列表；如果没有这行，前端会直接依赖 TeamPeer 对象。
    peer_messages = [_peer_message_payload(peer, message) for peer in peers for message in (getattr(peer, "inbox", []) if isinstance(getattr(peer, "inbox", []), list) else [])]  # 新增代码+DesktopGUIPlanning：展开 peer inbox 消息；如果没有这行，消息区无法显示 read_peer_messages 的状态。
    peer_messages = sorted(peer_messages, key=lambda item: str(item.get("created_at", "")), reverse=True)[:50]  # 新增代码+DesktopGUIPlanning：只保留最近 50 条消息；如果没有这行，长期协作 inbox 会让 payload 过大。
    pending_peer_message_count = sum(1 for message in peer_messages if message.get("status") == "pending")  # 新增代码+DesktopGUIPlanning：统计未确认消息；如果没有这行，摘要栏看不到协作待办。
    available_tool_count = sum(1 for item in planning_tools if item.get("available") is True)  # 新增代码+DesktopGUIPlanning：统计可用工具数量；如果没有这行，标题区无法显示接入完成度。
    return {  # 新增代码+DesktopGUIPlanning：返回完整 planning payload；如果没有这行，HTTP route 没有响应体。
        "ok": True,  # 新增代码+DesktopGUIPlanning：标记成功响应；如果没有这行，前端无法区分错误 payload。
        "schema_version": GUI_V2_SCHEMA_VERSION,  # 新增代码+DesktopGUIPlanning：暴露 GUI V2 schema；如果没有这行，前端无法做合同兼容。
        "workspace": str(workspace_path),  # 新增代码+DesktopGUIPlanning：暴露当前 workspace；如果没有这行，用户无法确认数据来源。
        "generated_at": datetime.now(UTC).isoformat(),  # 新增代码+DesktopGUIPlanning：暴露生成时间；如果没有这行，用户不知道数据是否新鲜。
        "reuse_module": "learning_agent.tools.catalog;learning_agent.runtime.task_registry;learning_agent.runtime.team_registry",  # 新增代码+DesktopGUIPlanning：声明复用模块；如果没有这行，用户无法验收 GUI 没有另造工具链。
        "storage": {"todo": "todo_state.json", "tasks": "memory/tasks", "team": "memory/team"},  # 新增代码+DesktopGUIPlanning：暴露相对存储位置；如果没有这行，用户不容易理解 GUI 读的是哪里。
        "tool_count": len(planning_tools),  # 新增代码+DesktopGUIPlanning：暴露计划工具总数；如果没有这行，面板无法显示覆盖规模。
        "available_tool_count": available_tool_count,  # 新增代码+DesktopGUIPlanning：暴露可用计划工具数；如果没有这行，缺工具状态不易发现。
        "tools": planning_tools,  # 新增代码+DesktopGUIPlanning：暴露计划工具摘要；如果没有这行，工具可用性区没有数据。
        "todo_status": todo_status,  # 新增代码+DesktopGUIPlanning：暴露 todo 读取状态；如果没有这行，空态和失败不可区分。
        "todo_count": len(todos),  # 新增代码+DesktopGUIPlanning：暴露 todo 数量；如果没有这行，摘要栏缺少计划规模。
        "todos": todos,  # 新增代码+DesktopGUIPlanning：暴露 todo 条目；如果没有这行，计划清单无法显示。
        "task_status": task_status,  # 新增代码+DesktopGUIPlanning：暴露 task registry 读取状态；如果没有这行，任务空态和失败不可区分。
        "task_count": len(task_payloads),  # 新增代码+DesktopGUIPlanning：暴露任务总数；如果没有这行，摘要栏缺少子任务规模。
        "active_task_count": active_task_count,  # 新增代码+DesktopGUIPlanning：暴露活动任务数；如果没有这行，用户无法快速判断是否还有后台工作。
        "task_status_counts": dict(task_status_counts),  # 新增代码+DesktopGUIPlanning：暴露任务状态分布；如果没有这行，任务健康需要逐条读。
        "tasks": task_payloads,  # 新增代码+DesktopGUIPlanning：暴露任务摘要；如果没有这行，任务区没有主体数据。
        "team_status": team_status,  # 新增代码+DesktopGUIPlanning：暴露 team registry 读取状态；如果没有这行，团队空态和失败不可区分。
        "peer_count": len(peer_payloads),  # 新增代码+DesktopGUIPlanning：暴露 peer 数量；如果没有这行，摘要栏缺少团队规模。
        "active_peer_count": sum(1 for peer in peer_payloads if str(peer.get("status", "")) not in {"idle", "deleted"}),  # 新增代码+DesktopGUIPlanning：暴露活跃 peer 数量；如果没有这行，用户要逐条判断团队状态。
        "peer_message_count": len(peer_messages),  # 新增代码+DesktopGUIPlanning：暴露消息数量；如果没有这行，摘要栏缺少协作消息规模。
        "pending_peer_message_count": pending_peer_message_count,  # 新增代码+DesktopGUIPlanning：暴露待确认消息数量；如果没有这行，用户不知道是否要处理消息。
        "peers": peer_payloads,  # 新增代码+DesktopGUIPlanning：暴露 peer 摘要；如果没有这行，团队区没有主体数据。
        "peer_messages": peer_messages,  # 新增代码+DesktopGUIPlanning：暴露最近 peer 消息；如果没有这行，协作消息区无法显示。
        "status_degraded": status_degraded,  # 新增代码+DesktopGUIPlanning：暴露整体降级状态；如果没有这行，前端无法提示数据可信度。
        "safe_error": "；".join(item for item in safe_errors if item),  # 新增代码+DesktopGUIPlanning：暴露脱敏错误合集；如果没有这行，读取失败没有可见原因。
    }  # 新增代码+DesktopGUIPlanning：完整 planning payload 结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIPlanning：函数段结束，build_gui_planning_payload 到此结束；如果没有边界说明，用户不易看出它只做只读适配。


def build_gui_toolchain_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIToolchain：函数段开始，构建 GUI 工具链清单；如果没有这段，前端无法读取统一工具地图。
    workspace_path = Path(workspace).resolve()  # 新增代码+DesktopGUIToolchain：规范化 workspace 路径；如果没有这行，payload 无法说明清单对应哪个项目。
    tools = build_builtin_tool_catalog()  # 新增代码+DesktopGUIToolchain：从已有内置工具目录读取工具；如果没有这行，GUI 会退回硬编码列表。
    grouped_tools: dict[str, list[dict[str, Any]]] = {}  # 新增代码+DesktopGUIToolchain：准备按能力包聚合工具；如果没有这行，后续没有容器保存分组。
    for tool in tools:  # 新增代码+DesktopGUIToolchain：遍历已有工具目录；如果没有这行，payload 会没有任何工具。
        group_id = _tool_group_id(tool)  # 新增代码+DesktopGUIToolchain：计算当前工具分组；如果没有这行，工具无法进入正确能力包。
        grouped_tools.setdefault(group_id, []).append(_tool_payload(tool))  # 新增代码+DesktopGUIToolchain：追加工具 payload；如果没有这行，分组会一直为空。
    groups = [  # 新增代码+DesktopGUIToolchain：构造前端可直接渲染的分组列表；如果没有这行，前端要自己处理字典排序。
        {  # 新增代码+DesktopGUIToolchain：单个分组 payload 开始；如果没有这行，列表项不是 JSON 对象。
            "id": group_id,  # 新增代码+DesktopGUIToolchain：暴露分组 id；如果没有这行，前端无法稳定 key。
            "label": TOOLCHAIN_GROUP_LABELS.get(group_id, group_id.replace("_", " ").title()),  # 新增代码+DesktopGUIToolchain：暴露可读标签；如果没有这行，用户只能看到机器名。
            "status": "available" if grouped_tools[group_id] else "empty",  # 新增代码+DesktopGUIToolchain：暴露分组状态；如果没有这行，空分组和可用分组不可区分。
            "tool_count": len(grouped_tools[group_id]),  # 新增代码+DesktopGUIToolchain：暴露分组工具数量；如果没有这行，面板无法显示规模。
            "reuse_module": "learning_agent.tools.catalog",  # 新增代码+DesktopGUIToolchain：标记分组来自工具目录；如果没有这行，用户看不出复用来源。
            "tools": sorted(grouped_tools[group_id], key=lambda item: str(item["name"])),  # 新增代码+DesktopGUIToolchain：按工具名稳定排序；如果没有这行，刷新后列表可能跳动。
        }  # 新增代码+DesktopGUIToolchain：单个分组 payload 结束；如果没有这行，Python 字典语法不完整。
        for group_id in sorted(grouped_tools, key=_group_sort_key)  # 新增代码+DesktopGUIToolchain：按预设顺序遍历分组；如果没有这行，列表推导没有数据来源。
    ]  # 新增代码+DesktopGUIToolchain：分组列表结束；如果没有这行，Python 列表语法不完整。
    return {  # 新增代码+DesktopGUIToolchain：返回完整 payload；如果没有这行，函数没有输出给 HTTP route。
        "ok": True,  # 新增代码+DesktopGUIToolchain：标记响应成功；如果没有这行，前端无法区分错误响应。
        "schema_version": GUI_V2_SCHEMA_VERSION,  # 新增代码+DesktopGUIToolchain：暴露 V2 schema；如果没有这行，前端无法做版本兼容。
        "workspace": str(workspace_path),  # 新增代码+DesktopGUIToolchain：暴露当前工作区；如果没有这行，用户不知道清单属于哪个项目。
        "generated_at": datetime.now(UTC).isoformat(),  # 新增代码+DesktopGUIToolchain：暴露生成时间；如果没有这行，用户不知道数据是否新鲜。
        "tool_count": len(tools),  # 新增代码+DesktopGUIToolchain：暴露总工具数量；如果没有这行，面板无法显示总体规模。
        "group_count": len(groups),  # 新增代码+DesktopGUIToolchain：暴露分组数量；如果没有这行，诊断无法快速确认分组规模。
        "groups": groups,  # 新增代码+DesktopGUIToolchain：暴露工具分组；如果没有这行，前端没有核心渲染数据。
        "status_degraded": False,  # 新增代码+DesktopGUIToolchain：标记清单未降级；如果没有这行，前端无法统一显示健康状态。
        "safe_error": "",  # 新增代码+DesktopGUIToolchain：保留安全错误字段；如果没有这行，错误状态 contract 不完整。
    }  # 新增代码+DesktopGUIToolchain：完整 payload 结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUIToolchain：函数段结束，build_gui_toolchain_payload 到此结束；如果没有边界说明，初学者不易看出它只负责清单构建。
