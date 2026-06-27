"""Desktop GUI Computer Use workbench adapter."""  # 新增代码+DesktopGUIComputerUseWorkbench：说明本文件只负责 GUI 操作台适配；如果没有这行，维护者容易把它误当新的桌面控制 runtime。

from __future__ import annotations  # 新增代码+DesktopGUIComputerUseWorkbench：启用延迟类型解析；如果没有这行，复杂返回类型在导入时更容易互相牵连。

from pathlib import Path  # 新增代码+DesktopGUIComputerUseWorkbench：使用 Path 规范化 Windows 路径；如果没有这行，workspace 下的 memory 目录容易拼错。
from typing import Any  # 新增代码+DesktopGUIComputerUseWorkbench：payload 是通用 JSON；如果没有这行，函数边界无法清楚表达。

from learning_agent.app.gui_protocol import GUI_V2_SCHEMA_VERSION  # 新增代码+DesktopGUIComputerUseWorkbench：复用 GUI V2 协议版本；如果没有这行，Computer Use 响应版本会和其它 GUI endpoint 分裂。
from learning_agent.computer_use_mcp_v2.windows_runtime.mode_session import ComputerUseModeSessionStore  # 新增代码+DesktopGUIComputerUseWorkbench：复用现有 Computer Use 模式 store；如果没有这行，GUI 会重新造一套权限模式状态。
from learning_agent.computer_use_mcp_v2.windows_runtime.request_access_tool import request_computer_use_access  # 新增代码+DesktopGUIComputerUseWorkbench：复用现有 request_access 只读申请工具；如果没有这行，GUI 授权申请会绕开成熟安全过滤。
from learning_agent.computer_use_mcp_v2.windows_runtime.session_context import DEFAULT_SESSION_CONTEXT_ID, ComputerUseSessionContextStore  # 新增代码+DesktopGUIComputerUseWorkbench：复用 session context/AppState 事实源；如果没有这行，目标应用和最近动作会继续藏在终端状态里。
from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DesktopGUIComputerUseWorkbench：复用统一状态事件流；如果没有这行，GUI 点击不会出现在右侧时间线。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+DesktopGUIComputerUseWorkbench：复用统一状态快照；如果没有这行，last observation 会旁路现有状态系统。


GUI_COMPUTER_USE_CONTROL_SOURCE = "learning_agent.computer_use_mcp_v2"  # 新增代码+DesktopGUIComputerUseWorkbench：声明能力来自现有 Computer Use v2；如果没有这行，前端和文档无法说明复用了哪个模块。
GUI_COMPUTER_USE_SAFE_ERROR = "Computer Use 状态暂时不可读。"  # 新增代码+DesktopGUIComputerUseWorkbench：统一安全错误文案；如果没有这行，异常路径可能把本机路径显示到 GUI。
GUI_COMPUTER_USE_ACTIONS = {"request-access", "observe", "abort"}  # 新增代码+DesktopGUIComputerUseWorkbench：集中列出 GUI 允许的安全动作；如果没有这行，路由分发容易接受未知动作。
GUI_COMPUTER_USE_OBSERVATION_TYPES = {"computer_use_observe", "computer_use_status", "computer_use_request_access", "computer_use_mcp_v2_tool", "gui_computer_use_action"}  # 新增代码+DesktopGUIComputerUseWorkbench：集中列出观察类事件；如果没有这行，最近观察会被普通日志污染。
GUI_COMPUTER_USE_ACTION_TYPES = {"computer_use_action", "tool_result_seen", "tool_call_completed", "computer_use_mcp_v2_tool", "gui_computer_use_action"}  # 新增代码+DesktopGUIComputerUseWorkbench：集中列出动作结果类事件；如果没有这行，最近动作结果无法稳定查找。


def _workspace_path(workspace: str | Path) -> Path:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，规范化 workspace；如果没有这段，不同调用点会读写不同相对目录。
    return Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIComputerUseWorkbench：返回绝对路径；如果没有这行，memory/computer_use 可能落到当前 shell 目录。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_workspace_path 到此结束；如果没有边界说明，用户不容易看出它只负责路径规范化。


def _mode_root(root: Path) -> Path:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，定位 GUI 专用 mode store；如果没有这段，GUI 测试可能污染真实终端 mode 状态。
    return root / "memory" / "computer_use" / "mode_sessions" / "gui"  # 新增代码+DesktopGUIComputerUseWorkbench：复用旧 GUI mode_sessions/gui 目录；如果没有这行，现有状态面板和新 workbench 会读两套状态。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_mode_root 到此结束；如果没有边界说明，用户不容易看出 mode 状态目录策略。


def _session_context_root(root: Path) -> Path:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，定位 GUI 专用 session context；如果没有这段，目标应用状态会散落到包默认目录。
    return root / "memory" / "computer_use" / "session_state" / "gui"  # 新增代码+DesktopGUIComputerUseWorkbench：把 AppState 放在当前 workspace 下；如果没有这行，多个项目会共享同一份桌面上下文。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_session_context_root 到此结束；如果没有边界说明，用户不容易看出 session context 目录策略。


def _status_store(root: Path) -> StatusEventStore:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，定位统一状态事件 store；如果没有这段，GUI 动作不会进入事件流。
    return StatusEventStore(root / "memory" / "status")  # 新增代码+DesktopGUIComputerUseWorkbench：沿用 status_snapshot 的 memory/status 目录；如果没有这行，右侧状态页读不到 Computer Use 动作。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_status_store 到此结束；如果没有边界说明，用户不容易看出它只负责事件目录。


def _mode_store(root: Path) -> ComputerUseModeSessionStore:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，创建现有模式 store；如果没有这段，多个函数会重复硬编码 base_dir。
    return ComputerUseModeSessionStore(base_dir=_mode_root(root))  # 新增代码+DesktopGUIComputerUseWorkbench：把 GUI 模式请求交给成熟 store；如果没有这行，request/abort 会变成临时内存状态。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_mode_store 到此结束；如果没有边界说明，用户不容易看出它只负责 store 构造。


def _context_store(root: Path) -> ComputerUseSessionContextStore:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，创建现有 session context store；如果没有这段，目标状态读取会重复路径逻辑。
    return ComputerUseSessionContextStore(base_dir=_session_context_root(root))  # 新增代码+DesktopGUIComputerUseWorkbench：复用成熟 AppState store；如果没有这行，GUI 看不到 allowed apps、display 和 last_action。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_context_store 到此结束；如果没有边界说明，用户不容易看出它只负责 context store 构造。


def _as_dict(value: Any) -> dict[str, Any]:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，把未知值收敛为 dict；如果没有这段，坏 JSON 会让 GUI endpoint 崩溃。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+DesktopGUIComputerUseWorkbench：只复制普通字典，其它返回空对象；如果没有这行，字符串或列表会被当成对象访问。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_as_dict 到此结束；如果没有边界说明，用户不容易看出类型防护范围。


def _as_list(value: Any) -> list[Any]:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，把未知值收敛为 list；如果没有这段，坏事件列表会让遍历失败。
    return list(value) if isinstance(value, list) else []  # 新增代码+DesktopGUIComputerUseWorkbench：只接受列表并复制；如果没有这行，None 或对象会污染扫描逻辑。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_as_list 到此结束；如果没有边界说明，用户不容易看出列表防护范围。


def _safe_text(value: Any, fallback: str = "", max_chars: int = 220) -> str:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，把任意值转成短文本；如果没有这段，长异常或路径可能撑破 GUI。
    text = str(value or fallback or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+DesktopGUIComputerUseWorkbench：把多行值压成单行；如果没有这行，面板布局可能被换行打散。
    return text[:max_chars]  # 新增代码+DesktopGUIComputerUseWorkbench：限制最大长度；如果没有这行，截图路径或模型输出可能挤爆右栏。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_safe_text 到此结束；如果没有边界说明，用户不容易看出文本脱敏压缩范围。


def _safe_public_mode_status(mode_status: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，裁剪 mode store 输出；如果没有这段，state_path 可能泄漏到 GUI。
    allowed_actions = _as_list(mode_status.get("allowed_action_classes", []))  # 新增代码+DesktopGUIComputerUseWorkbench：读取现有 store 的动作分类；如果没有这行，面板不知道 observe/full 允许什么。
    return {"mode": _safe_text(mode_status.get("mode"), "off", 80), "full_mode": bool(mode_status.get("full_mode", False)), "stopped": bool(mode_status.get("stopped", False)), "expired": bool(mode_status.get("expired", False)), "ttl_seconds": int(mode_status.get("ttl_seconds", 0) or 0), "allowed_action_classes": [str(action) for action in allowed_actions if str(action or "").strip()]}  # 新增代码+DesktopGUIComputerUseWorkbench：只返回 GUI 需要的安全字段；如果没有这行，前端可能收到本机状态文件路径。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_safe_public_mode_status 到此结束；如果没有边界说明，用户不容易看出 mode 字段裁剪范围。


def _safe_public_context(context: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，裁剪 session context 输出；如果没有这段，state_path 等内部字段会进入 GUI。
    display = _as_dict(context.get("selected_display", {}))  # 新增代码+DesktopGUIComputerUseWorkbench：读取显示器摘要；如果没有这行，多屏状态无法显示。
    dims = _as_dict(context.get("last_screenshot_dims", {}))  # 新增代码+DesktopGUIComputerUseWorkbench：读取最后截图尺寸；如果没有这行，观察证据缺少尺寸上下文。
    last_action = _as_dict(context.get("last_action", {}))  # 新增代码+DesktopGUIComputerUseWorkbench：读取最近动作摘要；如果没有这行，操作台无法解释刚做了什么。
    last_error = _as_dict(context.get("last_error", {}))  # 新增代码+DesktopGUIComputerUseWorkbench：读取最近错误摘要；如果没有这行，失败状态缺少排查入口。
    return {"session_id": _safe_text(context.get("session_id"), DEFAULT_SESSION_CONTEXT_ID, 120), "allowed_app_count": len(_as_list(context.get("allowed_apps", []))), "hidden_window_count": len(_as_list(context.get("hidden_windows", []))), "selected_display": _safe_text(display.get("display_id"), "", 120), "last_screenshot": {"width": int(dims.get("width", 0) or 0), "height": int(dims.get("height", 0) or 0)}, "display_pinned": bool(context.get("display_pinned", False)), "host_windows_hidden": bool(context.get("host_windows_hidden", False)), "cleanup_completed": bool(context.get("cleanup_completed", False)), "last_action": {"action": _safe_text(last_action.get("action"), "", 120), "ok": bool(last_action.get("ok", False)) if "ok" in last_action else None}, "last_error": {"code": _safe_text(last_error.get("code"), "", 120), "message": _safe_text(last_error.get("message"), "", 160)}}  # 新增代码+DesktopGUIComputerUseWorkbench：返回脱敏 AppState 摘要；如果没有这行，小白用户看不到目标/截图/cleanup 事实。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_safe_public_context 到此结束；如果没有边界说明，用户不容易看出 context 字段裁剪范围。


def _event_payload(event: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，安全读取事件 payload；如果没有这段，不同事件形状会重复写防御逻辑。
    return _as_dict(event.get("payload", {}))  # 新增代码+DesktopGUIComputerUseWorkbench：只返回 dict payload；如果没有这行，坏事件会拖垮摘要扫描。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_event_payload 到此结束；如果没有边界说明，用户不容易看出 payload 读取范围。


def _event_tool_name(event: dict[str, Any]) -> str:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，从事件中提取工具名；如果没有这段，最近动作结果无法说明来自哪个工具。
    payload = _event_payload(event)  # 新增代码+DesktopGUIComputerUseWorkbench：读取事件正文；如果没有这行，嵌套工具名字段会丢失。
    return _safe_text(event.get("tool_name") or payload.get("tool_name") or payload.get("mcp_tool_name") or payload.get("tool") or payload.get("action"), "", 140)  # 新增代码+DesktopGUIComputerUseWorkbench：兼容多种工具字段；如果没有这行，MCP/内置工具结果会显示未知。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_event_tool_name 到此结束；如果没有边界说明，用户不容易看出工具名提取范围。


def _event_ok(event: dict[str, Any]) -> bool | None:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，推断事件成功状态；如果没有这段，最近动作结果只能显示原始机器码。
    payload = _event_payload(event)  # 新增代码+DesktopGUIComputerUseWorkbench：读取事件正文；如果没有这行，ok/state 字段可能漏掉。
    if isinstance(event.get("ok"), bool):  # 新增代码+DesktopGUIComputerUseWorkbench：优先使用事件顶层 ok；如果没有这行，直接结果事件无法显示成功失败。
        return bool(event.get("ok"))  # 新增代码+DesktopGUIComputerUseWorkbench：返回顶层成功状态；如果没有这行，函数会继续误判。
    if isinstance(payload.get("ok"), bool):  # 新增代码+DesktopGUIComputerUseWorkbench：其次使用 payload.ok；如果没有这行，工具结果包装状态会漏掉。
        return bool(payload.get("ok"))  # 新增代码+DesktopGUIComputerUseWorkbench：返回 payload 成功状态；如果没有这行，GUI 会显示未知。
    state = _safe_text(payload.get("state") or payload.get("status") or event.get("event_type"), "", 80).casefold()  # 新增代码+DesktopGUIComputerUseWorkbench：读取状态文本；如果没有这行，completed/failed 无法归一。
    if state in {"completed", "ok", "accepted", "observed", "stopped"}:  # 新增代码+DesktopGUIComputerUseWorkbench：把成功状态归一为 True；如果没有这行，observe/abort 成功也会显示未知。
        return True  # 新增代码+DesktopGUIComputerUseWorkbench：返回成功；如果没有这行，状态分支没有结果。
    if state in {"failed", "error", "permission_denied", "denied", "aborted"}:  # 新增代码+DesktopGUIComputerUseWorkbench：把失败/拒绝状态归一为 False；如果没有这行，失败动作可能被误读。
        return False  # 新增代码+DesktopGUIComputerUseWorkbench：返回失败；如果没有这行，失败状态没有结果。
    return None  # 新增代码+DesktopGUIComputerUseWorkbench：没有明确状态时返回未知；如果没有这行，函数会隐式返回不清楚。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_event_ok 到此结束；如果没有边界说明，用户不容易看出状态推断范围。


def _safe_event_summary(event: dict[str, Any] | None) -> dict[str, Any] | None:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，把事件裁剪成 GUI 摘要；如果没有这段，原始 payload 可能泄漏路径或撑爆面板。
    if not isinstance(event, dict):  # 新增代码+DesktopGUIComputerUseWorkbench：处理没有事件的空态；如果没有这行，None 会继续访问字段。
        return None  # 新增代码+DesktopGUIComputerUseWorkbench：没有事件时返回空；如果没有这行，前端无法区分无事件和坏事件。
    payload = _event_payload(event)  # 新增代码+DesktopGUIComputerUseWorkbench：读取事件正文；如果没有这行，摘要无法提取 message/action。
    return {"sequence": int(event.get("sequence", 0) or 0), "timestamp": _safe_text(event.get("timestamp"), "", 120), "event_type": _safe_text(event.get("event_type") or event.get("kind"), "", 120), "tool_name": _event_tool_name(event), "action": _safe_text(payload.get("action") or payload.get("controller_action"), "", 120), "ok": _event_ok(event), "message": _safe_text(payload.get("message") or payload.get("summary") or payload.get("status") or payload.get("decision"), "", 180), "low_level_event_count": int(payload.get("low_level_event_count", 0) or 0)}  # 新增代码+DesktopGUIComputerUseWorkbench：只返回安全摘要字段；如果没有这行，GUI 可能展示完整敏感 payload。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_safe_event_summary 到此结束；如果没有边界说明，用户不容易看出事件脱敏范围。


def _event_mentions_computer_use(event: dict[str, Any]) -> bool:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，判断事件是否属于 Computer Use；如果没有这段，普通状态事件会污染 workbench。
    payload = _event_payload(event)  # 新增代码+DesktopGUIComputerUseWorkbench：读取事件正文；如果没有这行，工具名和动作字段无法参与判断。
    text = " ".join([_safe_text(event.get("event_type"), "", 120), _safe_text(event.get("kind"), "", 120), _event_tool_name(event), _safe_text(payload.get("action"), "", 120), _safe_text(payload.get("tool_name"), "", 120)]).casefold()  # 新增代码+DesktopGUIComputerUseWorkbench：拼接少量机器字段用于匹配；如果没有这行，事件归类只能看单一字段。
    return "computer_use" in text or "computer-use" in text or "mcp__computer-use__" in text  # 新增代码+DesktopGUIComputerUseWorkbench：命中 Computer Use 标识时返回真；如果没有这行，MCP v2 工具事件会被漏掉。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_event_mentions_computer_use 到此结束；如果没有边界说明，用户不容易看出事件归类范围。


def _latest_matching_event(events: list[dict[str, Any]], preferred_types: set[str]) -> dict[str, Any] | None:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，从事件尾巴找最近匹配项；如果没有这段，last observation/result 会重复扫描逻辑。
    for event in reversed(events):  # 新增代码+DesktopGUIComputerUseWorkbench：从最新事件往前找；如果没有这行，GUI 会显示旧动作而不是最新动作。
        event_type = _safe_text(event.get("event_type") or event.get("kind"), "", 120)  # 新增代码+DesktopGUIComputerUseWorkbench：读取事件类型；如果没有这行，preferred_types 无法生效。
        if event_type in preferred_types and (event_type not in {"tool_result_seen", "tool_call_completed"} or _event_mentions_computer_use(event)):  # 修改代码+DesktopGUIComputerUseWorkbench：泛用工具结果必须提到 Computer Use 才能命中；如果没有这行，普通工具结果会污染最近动作。
            return event  # 修改代码+DesktopGUIComputerUseWorkbench：返回严格匹配的最近事件；如果没有这行，真正的 Computer Use 事件会被跳过。
        if _event_mentions_computer_use(event):  # 新增代码+DesktopGUIComputerUseWorkbench：允许其它 Computer Use 字段命中的事件进入摘要；如果没有这行，MCP v2 不同事件名会被漏掉。
            return event  # 新增代码+DesktopGUIComputerUseWorkbench：返回最近匹配事件；如果没有这行，调用方拿不到结果。
    return None  # 新增代码+DesktopGUIComputerUseWorkbench：找不到时返回空；如果没有这行，函数隐式返回不清楚。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_latest_matching_event 到此结束；如果没有边界说明，用户不容易看出最近事件查找范围。


def _events_from_snapshot(root: Path, snapshot: dict[str, Any] | None) -> list[dict[str, Any]]:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，从快照或 store 读取事件；如果没有这段，workbench 会依赖调用方一定传 snapshot。
    if isinstance(snapshot, dict):  # 新增代码+DesktopGUIComputerUseWorkbench：优先复用 runtime panels 已读快照；如果没有这行，同一次请求会重复读磁盘。
        return [event for event in _as_list(snapshot.get("status_events", [])) if isinstance(event, dict)]  # 新增代码+DesktopGUIComputerUseWorkbench：返回快照里的事件字典；如果没有这行，坏事件会进入摘要。
    return [event.to_dict() for event in _status_store(root).list_events(limit=80)]  # 新增代码+DesktopGUIComputerUseWorkbench：无快照时从统一事件 store 读取最近 80 条；如果没有这行，独立动作 endpoint 刷新不到最新结果。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_events_from_snapshot 到此结束；如果没有边界说明，用户不容易看出事件来源优先级。


def build_gui_computer_use_workbench_payload(workspace: str | Path, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，构建 GUI Computer Use workbench payload；如果没有这段，前端只能看到旧状态摘要。
    root = _workspace_path(workspace)  # 新增代码+DesktopGUIComputerUseWorkbench：规范化工作区；如果没有这行，mode/context/status 会读错目录。
    degraded = False  # 新增代码+DesktopGUIComputerUseWorkbench：默认状态不降级；如果没有这行，异常分支外变量未定义。
    safe_error = ""  # 新增代码+DesktopGUIComputerUseWorkbench：默认没有错误；如果没有这行，payload 字段会不稳定。
    try:  # 新增代码+DesktopGUIComputerUseWorkbench：保护 mode/context/status 读取；如果没有这行，坏 JSON 会让整个 GUI 面板断线。
        mode_status = _safe_public_mode_status(_mode_store(root).status())  # 新增代码+DesktopGUIComputerUseWorkbench：读取现有 mode store 状态并裁剪；如果没有这行，mode/full/allowed actions 没有事实源。
        context_status = _safe_public_context(_context_store(root).snapshot(DEFAULT_SESSION_CONTEXT_ID))  # 新增代码+DesktopGUIComputerUseWorkbench：读取现有 AppState 并裁剪；如果没有这行，目标和最后动作状态不可见。
        events = _events_from_snapshot(root, snapshot)  # 新增代码+DesktopGUIComputerUseWorkbench：读取现有状态事件；如果没有这行，last observation/result 没有来源。
    except Exception:  # 新增代码+DesktopGUIComputerUseWorkbench：捕获状态读取异常；如果没有这行，临时锁文件或坏 JSON 会导致 500。
        mode_status = {"mode": "off", "full_mode": False, "stopped": False, "expired": False, "ttl_seconds": 0, "allowed_action_classes": []}  # 新增代码+DesktopGUIComputerUseWorkbench：提供安全 off 兜底；如果没有这行，前端会收到缺字段对象。
        context_status = {"session_id": DEFAULT_SESSION_CONTEXT_ID, "allowed_app_count": 0, "hidden_window_count": 0, "selected_display": "", "last_screenshot": {"width": 0, "height": 0}, "display_pinned": False, "host_windows_hidden": False, "cleanup_completed": False, "last_action": {"action": "", "ok": None}, "last_error": {"code": "", "message": ""}}  # 新增代码+DesktopGUIComputerUseWorkbench：提供安全 AppState 兜底；如果没有这行，目标状态空态不稳定。
        events = []  # 新增代码+DesktopGUIComputerUseWorkbench：失败时不返回可能不可信事件；如果没有这行，后续扫描变量未定义。
        degraded = True  # 新增代码+DesktopGUIComputerUseWorkbench：标记 workbench 降级；如果没有这行，GUI 会假装状态可信。
        safe_error = GUI_COMPUTER_USE_SAFE_ERROR  # 新增代码+DesktopGUIComputerUseWorkbench：使用脱敏错误文案；如果没有这行，异常细节可能泄露本机路径。
    last_observation = _safe_event_summary(_latest_matching_event(events, GUI_COMPUTER_USE_OBSERVATION_TYPES))  # 新增代码+DesktopGUIComputerUseWorkbench：提取最近观察摘要；如果没有这行，用户无法判断 GUI 看到的最后桌面事实。
    last_action_result = _safe_event_summary(_latest_matching_event(events, GUI_COMPUTER_USE_ACTION_TYPES))  # 新增代码+DesktopGUIComputerUseWorkbench：提取最近动作结果摘要；如果没有这行，用户点击后看不到后端反馈。
    return {"mode": mode_status["mode"], "permission_mode": "manual", "allowed_action_classes": mode_status["allowed_action_classes"], "last_observation": last_observation, "last_action_result": last_action_result, "target_app_state": context_status, "abort_available": True, "degraded": degraded, "status_degraded": degraded, "safe_error": safe_error, "full_mode": mode_status["full_mode"], "stopped": mode_status["stopped"], "expired": mode_status["expired"], "ttl_seconds": mode_status["ttl_seconds"], "lock": {"locked": False, "owner": "", "safe_state": "unlocked"}, "abort": {"requested": mode_status["stopped"], "global_hotkey_registered": False, "terminal_abort_fallback": True}, "control_source": GUI_COMPUTER_USE_CONTROL_SOURCE}  # 新增代码+DesktopGUIComputerUseWorkbench：返回稳定 workbench 字段；如果没有这行，前端无法渲染授权、观察、中止和证据状态。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，build_gui_computer_use_workbench_payload 到此结束；如果没有边界说明，用户不容易看出 payload 生成范围。


def _append_action_event(root: Path, action: str, status: str, message: str, extra: dict[str, Any] | None = None) -> int:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，记录 GUI Computer Use 动作事件；如果没有这段，点击按钮后时间线没有证据。
    payload = {"action": action, "status": status, "message": message, "low_level_event_count": 0, "control_source": GUI_COMPUTER_USE_CONTROL_SOURCE}  # 新增代码+DesktopGUIComputerUseWorkbench：构造统一事件 payload；如果没有这行，审计无法证明没有低层鼠标键盘事件。
    payload.update(extra or {})  # 新增代码+DesktopGUIComputerUseWorkbench：追加动作专属摘要；如果没有这行，request_access 报告和 stop 结果无法进入事件。
    event = _status_store(root).append("gui_computer_use_action", payload)  # 新增代码+DesktopGUIComputerUseWorkbench：写入统一状态事件；如果没有这行，右侧状态页不会刷新动作结果。
    return max(0, event.sequence - 1)  # 新增代码+DesktopGUIComputerUseWorkbench：返回前端继续轮询的游标；如果没有这行，GUI 可能错过刚写入的事件。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_append_action_event 到此结束；如果没有边界说明，用户不容易看出事件记录范围。


def _base_action_payload(action: str, status: str, message: str, workspace: Path, events_after_sequence: int, safe_error: str = "") -> dict[str, Any]:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，组装 action 响应；如果没有这段，三个 POST endpoint 字段会漂移。
    return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": action, "status": status, "message": message, "safe_error": safe_error, "events_after_sequence": events_after_sequence, "low_level_event_count": 0, "computer_use": build_gui_computer_use_workbench_payload(workspace)}  # 新增代码+DesktopGUIComputerUseWorkbench：返回统一响应并刷新 workbench；如果没有这行，前端按钮点击后无法立即更新面板。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，_base_action_payload 到此结束；如果没有边界说明，用户不容易看出 action 响应范围。


def build_gui_computer_use_action_payload(action: str, workspace: str | Path, body: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+DesktopGUIComputerUseWorkbench：函数段开始，执行 GUI 允许的安全 Computer Use 动作；如果没有这段，bridge POST 只能返回 404。
    root = _workspace_path(workspace)  # 新增代码+DesktopGUIComputerUseWorkbench：规范化工作区；如果没有这行，动作会写错 mode/context/status 目录。
    request_body = _as_dict(body)  # 新增代码+DesktopGUIComputerUseWorkbench：收敛请求体；如果没有这行，坏 JSON 字段会污染后续逻辑。
    if action not in GUI_COMPUTER_USE_ACTIONS:  # 新增代码+DesktopGUIComputerUseWorkbench：拒绝未知动作；如果没有这行，非法 action 可能落入默认成功。
        sequence = _append_action_event(root, action, "unsupported", "未知 Computer Use GUI 动作。")  # 新增代码+DesktopGUIComputerUseWorkbench：记录未知动作；如果没有这行，排查错误按钮没有证据。
        return _base_action_payload(action, "unsupported", "未知 Computer Use GUI 动作。", root, sequence, safe_error="unsupported")  # 新增代码+DesktopGUIComputerUseWorkbench：返回结构化不支持；如果没有这行，前端无法稳定展示错误。
    if action == "request-access":  # 新增代码+DesktopGUIComputerUseWorkbench：处理申请权限动作；如果没有这行，申请按钮没有后端路径。
        access_report = request_computer_use_access({"apps": request_body.get("apps", ["Notepad"]), "reason": _safe_text(request_body.get("reason"), "Desktop GUI request access", 180), "max_results": request_body.get("max_results", 6), "session_id": DEFAULT_SESSION_CONTEXT_ID})  # 新增代码+DesktopGUIComputerUseWorkbench：复用只读 request_access 生成申请报告；如果没有这行，GUI 会绕开安全候选和危险应用过滤。
        mode_result = _mode_store(root).open_mode("observe", reason="Desktop GUI request-access opens observe-only mode")  # 新增代码+DesktopGUIComputerUseWorkbench：只打开 observe 模式；如果没有这行，申请后仍没有可见模式变化。
        message = "已申请只读观察权限，未执行鼠标、键盘或窗口控制。"  # 新增代码+DesktopGUIComputerUseWorkbench：准备用户可读说明；如果没有这行，小白用户会误以为已获得完整控制。
        sequence = _append_action_event(root, action, "accepted", message, {"request_access": {"access_request_created": bool(access_report.get("access_request_created")), "grant_created": bool(access_report.get("grant_created")), "denied_requested_apps": _as_list(access_report.get("denied_requested_apps", [])), "safe_hint_count": len(_as_list(access_report.get("safe_app_hints", [])))}, "mode": _safe_public_mode_status(mode_result)})  # 新增代码+DesktopGUIComputerUseWorkbench：记录申请和 observe 模式结果；如果没有这行，时间线无法证明低层事件为 0。
        return _base_action_payload(action, "accepted", message, root, sequence)  # 新增代码+DesktopGUIComputerUseWorkbench：返回申请响应；如果没有这行，前端拿不到最新 workbench。
    if action == "observe":  # 新增代码+DesktopGUIComputerUseWorkbench：处理观察动作；如果没有这行，观察按钮没有后端路径。
        mode_result = _mode_store(root).open_mode("observe", reason="Desktop GUI observe requested")  # 新增代码+DesktopGUIComputerUseWorkbench：复用 mode store 进入只读观察模式；如果没有这行，观察请求不会改变可见状态。
        try:  # 新增代码+DesktopGUIComputerUseWorkbench：保护状态快照读取；如果没有这行，坏状态文件会让“观察”按钮直接 500。
            snapshot = build_status_snapshot(root)  # 新增代码+DesktopGUIComputerUseWorkbench：复用统一状态快照读取现有观察事实；如果没有这行，observe endpoint 不能刷新最后事件摘要。
        except Exception:  # 新增代码+DesktopGUIComputerUseWorkbench：捕获快照读取异常；如果没有这行，GUI 无法用安全错误继续反馈。
            snapshot = {"status_events": []}  # 新增代码+DesktopGUIComputerUseWorkbench：失败时给空事件兜底；如果没有这行，后续事件数量计算会访问未定义变量。
        message = "已刷新只读观察状态，未触发任何低层桌面动作。"  # 新增代码+DesktopGUIComputerUseWorkbench：准备用户可读说明；如果没有这行，用户会担心按钮已经控制电脑。
        sequence = _append_action_event(root, action, "observed", message, {"mode": _safe_public_mode_status(mode_result), "snapshot_event_count": len(_as_list(_as_dict(snapshot).get("status_events", [])))})  # 新增代码+DesktopGUIComputerUseWorkbench：记录只读观察请求；如果没有这行，面板没有点击反馈。
        return _base_action_payload(action, "observed", message, root, sequence)  # 新增代码+DesktopGUIComputerUseWorkbench：返回观察响应；如果没有这行，前端无法更新 last observation。
    stop_result = _mode_store(root).stop(reason="Desktop GUI abort requested")  # 新增代码+DesktopGUIComputerUseWorkbench：处理 abort 并复用 mode store stop；如果没有这行，中止按钮无法阻断后续 Computer Use 模式。
    message = "Computer Use 已中止，后续低层动作会被停止状态挡住。"  # 新增代码+DesktopGUIComputerUseWorkbench：准备中止说明；如果没有这行，用户不知道中止结果是什么。
    sequence = _append_action_event(root, action, "stopped", message, {"stop_result": {"stopped": bool(stop_result.get("stopped", False)), "marker": _safe_text(stop_result.get("marker"), "", 120)}})  # 新增代码+DesktopGUIComputerUseWorkbench：记录中止事件；如果没有这行，状态页无法审计急停。
    return _base_action_payload(action, "stopped", message, root, sequence)  # 新增代码+DesktopGUIComputerUseWorkbench：返回中止响应；如果没有这行，前端按钮点击后没有最新状态。
# 新增代码+DesktopGUIComputerUseWorkbench：函数段结束，build_gui_computer_use_action_payload 到此结束；如果没有边界说明，用户不容易看出三个安全动作范围。


__all__ = ["build_gui_computer_use_action_payload", "build_gui_computer_use_workbench_payload"]  # 新增代码+DesktopGUIComputerUseWorkbench：声明公开 API；如果没有这行，bridge 未来可能误用内部 helper。
