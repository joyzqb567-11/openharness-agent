"""Desktop GUI background command console payload helpers."""  # 新增代码+DesktopGUICommandConsole：说明本模块只负责把后台命令状态整理给桌面 GUI；如果没有这行，维护者容易把它和真实进程控制混在一起。

from __future__ import annotations  # 新增代码+DesktopGUICommandConsole：启用延迟类型解析；如果没有这行，类型注解在导入顺序变化时更容易出错。

import re  # 新增代码+DesktopGUICommandConsole：用于脱敏命令里的 token、api key 和 Authorization 片段；如果没有这行，命令文本可能把密钥显示到 GUI。
from datetime import UTC, datetime  # 新增代码+DesktopGUICommandConsole：生成统一 UTC 刷新时间；如果没有这行，用户不知道命令面板数据是否新鲜。
from pathlib import Path  # 新增代码+DesktopGUICommandConsole：用 Path 规范化 workspace 和输出目录；如果没有这行，Windows 路径处理会更脆弱。
from typing import Any  # 新增代码+DesktopGUICommandConsole：标注通用 JSON payload；如果没有这行，函数边界会退化成不清楚的动态对象。

from learning_agent.app.gui_protocol import GUI_V2_SCHEMA_VERSION  # 新增代码+DesktopGUICommandConsole：复用 GUI V2 协议版本；如果没有这行，命令端点会和其它 V2 payload 版本漂移。
from learning_agent.runtime.task_registry import TaskRecord, TaskRegistry  # 新增代码+DesktopGUICommandConsole：复用持久任务登记表；如果没有这行，GUI 会被迫重写后台任务读取逻辑。


COMMAND_TERMINAL_STATUSES: set[str] = {"completed", "failed", "stopped", "cancelled"}  # 新增代码+DesktopGUICommandConsole：集中定义命令终态；如果没有这行，停止按钮和统计会散落硬编码。
COMMAND_ACTIVE_STATUSES: set[str] = {"pending", "queued", "running", "needs_input"}  # 新增代码+DesktopGUICommandConsole：集中定义仍需关注的命令状态；如果没有这行，running 统计可能和其它面板不一致。
COMMAND_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (  # 新增代码+DesktopGUICommandConsole：命令脱敏规则表开始；如果没有这段，密钥可能从命令行参数进入 GUI。
    (re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s\"']+"), r"\1[REDACTED]"),  # 新增代码+DesktopGUICommandConsole：脱敏 Authorization Bearer；如果没有这行，HTTP 头里的 token 可能泄漏。
    (re.compile(r"(?i)(bearer\s+)[^\s\"']+"), r"\1[REDACTED]"),  # 新增代码+DesktopGUICommandConsole：脱敏裸 Bearer token；如果没有这行，CLI 参数中的 bearer 值可能泄漏。
    (re.compile(r"(?i)(openai_api_key\s*=\s*)[^\s\"']+"), r"\1[REDACTED]"),  # 新增代码+DesktopGUICommandConsole：脱敏 OPENAI_API_KEY=...；如果没有这行，环境变量形式的密钥会直接显示。
    (re.compile(r"(?i)(api[_-]?key\s*=\s*)[^\s\"']+"), r"\1[REDACTED]"),  # 新增代码+DesktopGUICommandConsole：脱敏 api_key=...；如果没有这行，通用 key 赋值会进入面板。
    (re.compile(r"(?i)(--api-key\s+)[^\s\"']+"), r"\1[REDACTED]"),  # 新增代码+DesktopGUICommandConsole：脱敏 --api-key 参数；如果没有这行，常见 CLI key 参数会泄漏。
    (re.compile(r"(?i)(token\s*=\s*)[^\s\"'&]+"), r"\1[REDACTED]"),  # 新增代码+DesktopGUICommandConsole：脱敏 query 或参数 token=...；如果没有这行，URL token 可能暴露。
)  # 新增代码+DesktopGUICommandConsole：命令脱敏规则表结束；如果没有这行，Python 元组语法不完整。


def _redact_command_text(value: Any, fallback: str = "", max_chars: int = 600) -> str:  # 新增代码+DesktopGUICommandConsole：函数段开始，把未知命令文本收敛成脱敏短文本；如果没有这段，GUI 可能显示超长或含密钥命令。
    text = str(value if value is not None else fallback).replace("\r", " ").replace("\n", " ").strip()  # 新增代码+DesktopGUICommandConsole：把 None 和多行命令变成单行；如果没有这行，命令卡片可能撑破布局。
    if not text:  # 新增代码+DesktopGUICommandConsole：检查命令文本是否为空；如果没有这行，空字符串不会进入 fallback。
        text = fallback  # 新增代码+DesktopGUICommandConsole：使用兜底文本；如果没有这行，空命令会在 GUI 上不可理解。
    for pattern, replacement in COMMAND_SECRET_PATTERNS:  # 新增代码+DesktopGUICommandConsole：逐条应用脱敏规则；如果没有这行，规则表不会生效。
        text = pattern.sub(replacement, text)  # 新增代码+DesktopGUICommandConsole：替换敏感片段；如果没有这行，密钥仍会留在输出中。
    return text[:max_chars]  # 新增代码+DesktopGUICommandConsole：限制命令文本长度；如果没有这行，超长命令会让 payload 和 UI 过大。
# 新增代码+DesktopGUICommandConsole：函数段结束，_redact_command_text 到此结束；如果没有边界说明，用户不易看出文本脱敏范围。


def _safe_command_text(value: Any, fallback: str = "", max_chars: int = 240) -> str:  # 新增代码+DesktopGUICommandConsole：函数段开始，把普通字段转成短文本；如果没有这段，坏 JSON 字段可能拖垮面板。
    text = str(value if value is not None else fallback).replace("\r", " ").replace("\n", " ").strip()  # 新增代码+DesktopGUICommandConsole：把 None、多行和空白收敛成单行；如果没有这行，卡片元信息可能错位。
    if not text:  # 新增代码+DesktopGUICommandConsole：检查字段是否为空；如果没有这行，fallback 不会覆盖空字符串。
        text = fallback  # 新增代码+DesktopGUICommandConsole：使用兜底文本；如果没有这行，GUI 会出现无意义空白。
    return text[:max_chars]  # 新增代码+DesktopGUICommandConsole：限制文本长度；如果没有这行，标签或路径可能撑破右侧栏。
# 新增代码+DesktopGUICommandConsole：函数段结束，_safe_command_text 到此结束；如果没有边界说明，用户不易看出普通文本清洗范围。


def _safe_output_tail(value: Any, max_chars: int = 1200) -> str:  # 新增代码+DesktopGUICommandConsole：函数段开始，整理命令输出尾部；如果没有这段，输出可能过长或携带不可控回车。
    text = str(value if value is not None else "").replace("\r\n", "\n").replace("\r", "\n")  # 新增代码+DesktopGUICommandConsole：统一换行格式；如果没有这行，Windows 输出在 pre 里可能显示混乱。
    for pattern, replacement in COMMAND_SECRET_PATTERNS:  # 新增代码+DesktopGUICommandConsole：输出里也应用同一套脱敏规则；如果没有这行，命令回显可能泄漏 token。
        text = pattern.sub(replacement, text)  # 新增代码+DesktopGUICommandConsole：替换输出中的敏感片段；如果没有这行，tail 仍可能暴露密钥。
    return text[-max_chars:] if len(text) > max_chars else text  # 新增代码+DesktopGUICommandConsole：只保留尾部窗口；如果没有这行，长任务输出会让 payload 过大。
# 新增代码+DesktopGUICommandConsole：函数段结束，_safe_output_tail 到此结束；如果没有边界说明，用户不易看出输出截断范围。


def _safe_relative_workspace_path(workspace_path: Path, raw_path: Any) -> str:  # 新增代码+DesktopGUICommandConsole：函数段开始，把 cwd 显示成相对路径；如果没有这段，GUI 可能暴露完整本机目录。
    path_text = _safe_command_text(raw_path, "", 260)  # 新增代码+DesktopGUICommandConsole：先把未知路径字段收敛成文本；如果没有这行，Path 会收到坏类型。
    if not path_text:  # 新增代码+DesktopGUICommandConsole：处理空路径；如果没有这行，空 cwd 会进入 Path 解析。
        return ""  # 新增代码+DesktopGUICommandConsole：空路径直接返回空；如果没有这行，首次运行可能显示误导性路径。
    try:  # 新增代码+DesktopGUICommandConsole：保护路径解析；如果没有这行，奇怪路径字符串会让 endpoint 失败。
        resolved_path = Path(path_text).expanduser().resolve()  # 新增代码+DesktopGUICommandConsole：规范化 cwd；如果没有这行，无法判断是否位于 workspace 内。
        relative_path = resolved_path.relative_to(workspace_path)  # 新增代码+DesktopGUICommandConsole：尝试转成相对工作区路径；如果没有这行，用户看到的都是绝对路径。
        return "." if str(relative_path) == "." else str(relative_path).replace("\\", "/")  # 新增代码+DesktopGUICommandConsole：返回短路径并统一斜杠；如果没有这行，Windows 反斜杠可读性较差。
    except Exception:  # 新增代码+DesktopGUICommandConsole：处理路径不在 workspace 或不可解析；如果没有这行，外部 cwd 会导致 500。
        return "[outside-workspace]"  # 新增代码+DesktopGUICommandConsole：外部路径只给安全占位；如果没有这行，本机绝对路径可能进入 GUI。
# 新增代码+DesktopGUICommandConsole：函数段结束，_safe_relative_workspace_path 到此结束；如果没有边界说明，用户不易看出路径脱敏范围。


def _exit_code_from_record(record: TaskRecord) -> int | None:  # 新增代码+DesktopGUICommandConsole：函数段开始，从任务记录推断退出码；如果没有这段，GUI 只能显示泛化状态。
    raw_exit_code = record.metadata.get("exit_code") if isinstance(record.metadata, dict) else None  # 新增代码+DesktopGUICommandConsole：优先读取 metadata.exit_code；如果没有这行，未来真实退出码无法显示。
    if isinstance(raw_exit_code, int):  # 新增代码+DesktopGUICommandConsole：接受整数退出码；如果没有这行，正确字段也不会被渲染。
        return raw_exit_code  # 新增代码+DesktopGUICommandConsole：返回真实退出码；如果没有这行，函数会继续误判。
    if record.status == "completed":  # 新增代码+DesktopGUICommandConsole：完成状态通常代表退出码 0；如果没有这行，成功命令会缺少 exit 0。
        return 0  # 新增代码+DesktopGUICommandConsole：返回成功退出码；如果没有这行，用户无法快速看出成功。
    return None  # 新增代码+DesktopGUICommandConsole：未知退出码返回空；如果没有这行，调用方会收到未定义值。
# 新增代码+DesktopGUICommandConsole：函数段结束，_exit_code_from_record 到此结束；如果没有边界说明，用户不易看出退出码推断范围。


def _is_background_command_record(record: TaskRecord) -> bool:  # 新增代码+DesktopGUICommandConsole：函数段开始，判断任务是否属于后台命令；如果没有这段，GUI 可能把普通 agent 子任务混进命令面板。
    return record.kind == "background_shell" or bool(record.background and str(record.task_id).startswith("bg_"))  # 新增代码+DesktopGUICommandConsole：兼容 background_shell 和旧 bg_ 记录；如果没有这行，历史后台命令可能不可见。
# 新增代码+DesktopGUICommandConsole：函数段结束，_is_background_command_record 到此结束；如果没有边界说明，用户不易看出命令筛选规则。


def _command_record_payload(workspace_path: Path, registry: TaskRegistry, record: TaskRecord, max_tail_chars: int = 1200) -> dict[str, Any]:  # 新增代码+DesktopGUICommandConsole：函数段开始，把 TaskRecord 转成 GUI 安全命令卡片；如果没有这段，前端需要理解 TaskRegistry 内部字段。
    metadata = record.metadata if isinstance(record.metadata, dict) else {}  # 新增代码+DesktopGUICommandConsole：只接受对象 metadata；如果没有这行，坏 metadata 会导致字段读取异常。
    tail_text = _safe_output_tail(registry.output_store.tail(record.task_id, max_chars=max_tail_chars), max_chars=max_tail_chars)  # 新增代码+DesktopGUICommandConsole：读取任务输出尾部并脱敏；如果没有这行，用户看不到长任务终端输出。
    command_text = _redact_command_text(record.prompt, record.task_id, 600)  # 新增代码+DesktopGUICommandConsole：脱敏命令文本；如果没有这行，命令行参数可能泄漏密钥。
    status = _safe_command_text(record.status, "unknown", 80)  # 新增代码+DesktopGUICommandConsole：读取命令状态；如果没有这行，前端要直接消费内部字段。
    stop_supported = False  # 新增代码+DesktopGUICommandConsole：默认不声明可停；如果没有这行，GUI 可能误启用无法真实停止的按钮。
    stop_reason = "GUI bridge 当前只能读取持久任务记录，没有原 LearningAgent 的 live process 句柄；请通过 core agent 的 stop_background_command 停止。"  # 新增代码+DesktopGUICommandConsole：解释停止不可用原因；如果没有这行，用户会误以为按钮坏了。
    return {  # 新增代码+DesktopGUICommandConsole：返回命令卡片 payload；如果没有这行，函数没有 JSON 输出。
        "command_id": _safe_command_text(record.task_id, "", 160),  # 新增代码+DesktopGUICommandConsole：暴露命令 id；如果没有这行，前端无法 key 和请求 tail/stop。
        "command_text": command_text,  # 新增代码+DesktopGUICommandConsole：暴露脱敏命令文本；如果没有这行，用户不知道运行的是什么命令。
        "command_summary": command_text[:160],  # 新增代码+DesktopGUICommandConsole：暴露短摘要；如果没有这行，紧凑视图缺少短文本。
        "label": _safe_command_text(metadata.get("label", ""), "", 120),  # 新增代码+DesktopGUICommandConsole：暴露启动命令时记录的 label；如果没有这行，dev server 等命令缺少友好名称。
        "cwd_display": _safe_relative_workspace_path(workspace_path, metadata.get("cwd", "")),  # 新增代码+DesktopGUICommandConsole：显示脱敏工作目录；如果没有这行，用户不知道命令在哪运行。
        "status": status,  # 新增代码+DesktopGUICommandConsole：暴露状态；如果没有这行，前端无法判断运行中或完成。
        "kind": _safe_command_text(record.kind, "background_shell", 80),  # 新增代码+DesktopGUICommandConsole：暴露任务类型；如果没有这行，排查历史记录来源困难。
        "background": bool(record.background),  # 新增代码+DesktopGUICommandConsole：暴露后台标记；如果没有这行，GUI 无法解释该记录为什么在命令台。
        "created_at": _safe_command_text(record.created_at, "", 120),  # 新增代码+DesktopGUICommandConsole：暴露创建时间；如果没有这行，用户不知道命令何时启动。
        "updated_at": _safe_command_text(record.updated_at, "", 120),  # 新增代码+DesktopGUICommandConsole：暴露更新时间；如果没有这行，用户无法判断输出是否新鲜。
        "completed_at": _safe_command_text(record.completed_at, "", 120),  # 新增代码+DesktopGUICommandConsole：暴露完成时间；如果没有这行，终态命令缺少收束时间。
        "exit_code": _exit_code_from_record(record),  # 新增代码+DesktopGUICommandConsole：暴露退出码；如果没有这行，用户要从输出里猜成功失败。
        "tail": tail_text,  # 新增代码+DesktopGUICommandConsole：暴露输出尾部；如果没有这行，命令台看不到终端证据。
        "tail_line_count": len([line for line in tail_text.splitlines() if line.strip()]),  # 新增代码+DesktopGUICommandConsole：暴露输出行数；如果没有这行，空输出和有输出不易区分。
        "has_output_file": bool(record.output_path),  # 新增代码+DesktopGUICommandConsole：只暴露是否有输出文件；如果没有这行，GUI 可能显示完整本机路径。
        "last_offset": int(record.last_offset or 0),  # 新增代码+DesktopGUICommandConsole：暴露当前输出 offset；如果没有这行，后续增量 tail 没有位置线索。
        "can_stop": stop_supported and status not in COMMAND_TERMINAL_STATUSES,  # 新增代码+DesktopGUICommandConsole：只有真实支持且非终态才允许停止；如果没有这行，按钮可能产生假停止。
        "stop_supported": stop_supported,  # 新增代码+DesktopGUICommandConsole：暴露后端真实停止能力；如果没有这行，前端无法禁用不可用按钮。
        "stop_unavailable_reason": "" if stop_supported else stop_reason,  # 新增代码+DesktopGUICommandConsole：暴露不可用原因；如果没有这行，禁用按钮没有解释。
    }  # 新增代码+DesktopGUICommandConsole：命令卡片 payload 结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUICommandConsole：函数段结束，_command_record_payload 到此结束；如果没有边界说明，用户不易看出 TaskRecord 白名单范围。


def _background_command_records(registry: TaskRegistry) -> list[TaskRecord]:  # 新增代码+DesktopGUICommandConsole：函数段开始，读取并筛选后台命令记录；如果没有这段，列表端点会重复筛选逻辑。
    records = [record for record in registry.list_tasks() if _is_background_command_record(record)]  # 新增代码+DesktopGUICommandConsole：只保留后台命令记录；如果没有这行，普通 agent 任务会混进命令控制台。
    return sorted(records, key=lambda item: _safe_command_text(item.updated_at, item.created_at, 120), reverse=True)[:50]  # 新增代码+DesktopGUICommandConsole：按更新时间倒序并限制数量；如果没有这行，长期项目会让面板过载。
# 新增代码+DesktopGUICommandConsole：函数段结束，_background_command_records 到此结束；如果没有边界说明，用户不易看出列表范围。


def build_gui_command_console_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUICommandConsole：函数段开始，构建后台命令控制台总览；如果没有这段，GUI 无法读取后台命令事实源。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUICommandConsole：规范化工作区路径；如果没有这行，任务目录定位会不稳定。
    registry = TaskRegistry(workspace_path / "memory" / "tasks")  # 新增代码+DesktopGUICommandConsole：复用 LearningAgent.task_registry 的持久目录；如果没有这行，GUI 会读不到后台命令记录。
    status_degraded = False  # 新增代码+DesktopGUICommandConsole：默认状态未降级；如果没有这行，异常分支前变量未定义。
    safe_error = ""  # 新增代码+DesktopGUICommandConsole：默认没有安全错误；如果没有这行，payload 字段不稳定。
    try:  # 新增代码+DesktopGUICommandConsole：保护任务登记表读取；如果没有这行，坏 JSON 会让 HTTP endpoint 直接 500。
        records = _background_command_records(registry)  # 新增代码+DesktopGUICommandConsole：读取后台命令记录；如果没有这行，payload 没有主体数据。
    except Exception:  # 新增代码+DesktopGUICommandConsole：捕获登记表读取异常；如果没有这行，用户看不到降级说明。
        records = []  # 新增代码+DesktopGUICommandConsole：读取失败时返回空列表；如果没有这行，后续变量未定义。
        status_degraded = True  # 新增代码+DesktopGUICommandConsole：标记读取降级；如果没有这行，前端会误信空列表正常。
        safe_error = "后台命令登记表暂时不可读。"  # 新增代码+DesktopGUICommandConsole：暴露脱敏错误；如果没有这行，用户不知道为何没有命令。
    commands = [_command_record_payload(workspace_path, registry, record) for record in records]  # 新增代码+DesktopGUICommandConsole：白名单化命令记录；如果没有这行，前端会直接依赖 TaskRecord。
    running_command_count = sum(1 for item in commands if str(item.get("status", "")) in COMMAND_ACTIVE_STATUSES)  # 新增代码+DesktopGUICommandConsole：统计仍在运行或排队的命令；如果没有这行，标题区无法快速判断活跃状态。
    stop_supported_count = sum(1 for item in commands if item.get("stop_supported") is True)  # 新增代码+DesktopGUICommandConsole：统计可真实停止的命令；如果没有这行，用户看不出当前停止能力边界。
    return {  # 新增代码+DesktopGUICommandConsole：返回完整控制台 payload；如果没有这行，HTTP route 没有响应体。
        "ok": True,  # 新增代码+DesktopGUICommandConsole：标记成功响应；如果没有这行，前端无法区分错误 payload。
        "schema_version": GUI_V2_SCHEMA_VERSION,  # 新增代码+DesktopGUICommandConsole：暴露 V2 schema；如果没有这行，前端无法做合同兼容。
        "workspace": str(workspace_path),  # 新增代码+DesktopGUICommandConsole：暴露当前 workspace；如果没有这行，用户无法确认命令来源。
        "generated_at": datetime.now(UTC).isoformat(),  # 新增代码+DesktopGUICommandConsole：暴露生成时间；如果没有这行，用户不知道状态是否新鲜。
        "reuse_module": "learning_agent.runtime.task_registry;learning_agent.runtime.task_output;learning_agent.runtime.background_commands",  # 新增代码+DesktopGUICommandConsole：声明复用模块；如果没有这行，用户无法验收 GUI 没有另造命令系统。
        "storage": {"tasks": "memory/tasks", "outputs": "memory/tasks/outputs"},  # 新增代码+DesktopGUICommandConsole：暴露相对存储位置；如果没有这行，用户不容易理解 GUI 读的是哪里。
        "command_count": len(commands),  # 新增代码+DesktopGUICommandConsole：暴露命令总数；如果没有这行，摘要栏缺少规模信息。
        "running_command_count": running_command_count,  # 新增代码+DesktopGUICommandConsole：暴露活跃命令数量；如果没有这行，用户要逐条判断是否还在跑。
        "stop_supported_count": stop_supported_count,  # 新增代码+DesktopGUICommandConsole：暴露可停止数量；如果没有这行，GUI 能力边界不明显。
        "commands": commands,  # 新增代码+DesktopGUICommandConsole：暴露命令列表；如果没有这行，命令面板没有主体数据。
        "status_degraded": status_degraded,  # 新增代码+DesktopGUICommandConsole：暴露整体降级状态；如果没有这行，前端无法提示数据可信度。
        "safe_error": safe_error,  # 新增代码+DesktopGUICommandConsole：暴露脱敏错误；如果没有这行，读取失败没有可见原因。
    }  # 新增代码+DesktopGUICommandConsole：完整控制台 payload 结束；如果没有这行，Python 字典语法不完整。
# 新增代码+DesktopGUICommandConsole：函数段结束，build_gui_command_console_payload 到此结束；如果没有边界说明，用户不易看出只读总览范围。


def build_gui_command_tail_payload(workspace: str | Path, command_id: str, max_chars: int = 4000) -> dict[str, Any]:  # 新增代码+DesktopGUICommandConsole：函数段开始，构建单条命令 tail payload；如果没有这段，前端无法按需刷新长输出。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUICommandConsole：规范化工作区路径；如果没有这行，任务目录定位会不稳定。
    registry = TaskRegistry(workspace_path / "memory" / "tasks")  # 新增代码+DesktopGUICommandConsole：打开真实任务登记表；如果没有这行，tail 端点没有事实源。
    safe_command_id = _safe_command_text(command_id, "", 180)  # 新增代码+DesktopGUICommandConsole：清洗命令 id；如果没有这行，响应可能回显奇怪值。
    try:  # 新增代码+DesktopGUICommandConsole：保护单任务读取；如果没有这行，不存在 id 会变成 500。
        record = registry.get_task(safe_command_id)  # 新增代码+DesktopGUICommandConsole：读取命令对应任务记录；如果没有这行，tail 无法确认状态。
    except KeyError:  # 新增代码+DesktopGUICommandConsole：处理命令不存在；如果没有这行，用户拿不到结构化 not_found。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "command_id": safe_command_id, "status": "not_found", "tail": "", "line_count": 0, "next_offset": 0, "command": {}, "safe_error": "没有找到这个后台命令。"}  # 新增代码+DesktopGUICommandConsole：返回未找到 payload；如果没有这行，前端要处理异常路径。
    except Exception:  # 新增代码+DesktopGUICommandConsole：处理登记表读取异常；如果没有这行，坏记录会让 HTTP 500。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "command_id": safe_command_id, "status": "failed", "tail": "", "line_count": 0, "next_offset": 0, "command": {}, "safe_error": "后台命令输出暂时不可读。"}  # 新增代码+DesktopGUICommandConsole：返回脱敏失败 payload；如果没有这行，前端缺少可见错误。
    if not _is_background_command_record(record):  # 新增代码+DesktopGUICommandConsole：确认目标确实是后台命令；如果没有这行，普通 agent 任务可被命令 tail 端点误读。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "command_id": safe_command_id, "status": "not_background_command", "tail": "", "line_count": 0, "next_offset": int(record.last_offset or 0), "command": {}, "safe_error": "这个任务不是后台命令。"}  # 新增代码+DesktopGUICommandConsole：返回类型不匹配 payload；如果没有这行，前端会显示误导性输出。
    tail_text = _safe_output_tail(registry.output_store.tail(record.task_id, max_chars=max_chars), max_chars=max_chars)  # 新增代码+DesktopGUICommandConsole：读取并脱敏输出尾部；如果没有这行，tail 端点没有输出内容。
    command_payload = _command_record_payload(workspace_path, registry, record, max_tail_chars=min(max_chars, 1200))  # 新增代码+DesktopGUICommandConsole：附带命令摘要；如果没有这行，前端刷新 tail 后缺少状态。
    return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "command_id": safe_command_id, "status": "ready", "tail": tail_text, "line_count": len([line for line in tail_text.splitlines() if line.strip()]), "next_offset": int(record.last_offset or 0), "command": command_payload, "safe_error": ""}  # 新增代码+DesktopGUICommandConsole：返回 tail payload；如果没有这行，HTTP route 没有响应体。
# 新增代码+DesktopGUICommandConsole：函数段结束，build_gui_command_tail_payload 到此结束；如果没有边界说明，用户不易看出 tail 只读范围。


def build_gui_command_stop_payload(workspace: str | Path, command_id: str) -> dict[str, Any]:  # 新增代码+DesktopGUICommandConsole：函数段开始，构建后台命令停止响应；如果没有这段，停止按钮无法得到诚实能力反馈。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUICommandConsole：规范化工作区路径；如果没有这行，任务目录定位会不稳定。
    registry = TaskRegistry(workspace_path / "memory" / "tasks")  # 新增代码+DesktopGUICommandConsole：打开真实任务登记表；如果没有这行，停止端点无法确认命令是否存在。
    safe_command_id = _safe_command_text(command_id, "", 180)  # 新增代码+DesktopGUICommandConsole：清洗命令 id；如果没有这行，响应可能回显奇怪值。
    try:  # 新增代码+DesktopGUICommandConsole：保护单任务读取；如果没有这行，不存在 id 会变成 500。
        record = registry.get_task(safe_command_id)  # 新增代码+DesktopGUICommandConsole：读取命令任务记录；如果没有这行，停止端点无法区分 not_found 和 unavailable。
    except KeyError:  # 新增代码+DesktopGUICommandConsole：处理命令不存在；如果没有这行，用户拿不到结构化 not_found。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": "stop", "command_id": safe_command_id, "supported": False, "status": "not_found", "message": "没有找到这个后台命令。", "safe_error": "", "command": {}}  # 新增代码+DesktopGUICommandConsole：返回未找到响应；如果没有这行，前端只能显示泛化失败。
    except Exception:  # 新增代码+DesktopGUICommandConsole：处理登记表读取异常；如果没有这行，坏记录会让 HTTP 500。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": "stop", "command_id": safe_command_id, "supported": False, "status": "failed", "message": "后台命令登记表暂时不可读。", "safe_error": "后台命令登记表暂时不可读。", "command": {}}  # 新增代码+DesktopGUICommandConsole：返回脱敏失败响应；如果没有这行，前端缺少可见错误。
    command_payload = _command_record_payload(workspace_path, registry, record)  # 新增代码+DesktopGUICommandConsole：构建命令摘要；如果没有这行，按钮反馈缺少目标上下文。
    if not _is_background_command_record(record):  # 新增代码+DesktopGUICommandConsole：确认目标确实是后台命令；如果没有这行，普通任务可能被误停止。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": "stop", "command_id": safe_command_id, "supported": False, "status": "not_background_command", "message": "这个任务不是后台命令。", "safe_error": "", "command": command_payload}  # 新增代码+DesktopGUICommandConsole：返回类型不匹配响应；如果没有这行，前端会误导用户。
    if record.status in COMMAND_TERMINAL_STATUSES:  # 新增代码+DesktopGUICommandConsole：终态命令不需要停止；如果没有这行，已完成命令会显示无法停止为错误。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": "stop", "command_id": safe_command_id, "supported": False, "status": "already_terminal", "message": "这个后台命令已经结束，不需要停止。", "safe_error": "", "command": command_payload}  # 新增代码+DesktopGUICommandConsole：返回已终态响应；如果没有这行，用户无法区分已结束和不支持。
    return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": "stop", "command_id": safe_command_id, "supported": False, "status": "unavailable", "message": "GUI bridge 当前没有原 LearningAgent 的 live process 句柄，不能安全地真实停止该进程。请通过 core agent 的 stop_background_command 执行停止。", "safe_error": "", "command": command_payload}  # 新增代码+DesktopGUICommandConsole：返回诚实不可用响应；如果没有这行，GUI 可能制造假停止状态。
# 新增代码+DesktopGUICommandConsole：函数段结束，build_gui_command_stop_payload 到此结束；如果没有边界说明，用户不易看出这里不做假停止。
