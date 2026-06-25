"""Desktop GUI V2 event stream helpers."""  # 新增代码+GuiV2Stream：说明本模块只负责 V2 GUI 事件选择和 SSE 编码；如果没有这一行，维护者容易把 stream 逻辑散进 HTTP handler。

from __future__ import annotations  # 新增代码+GuiV2Stream：启用未来注解语法；如果没有这一行，类型标注在旧 Python 行为下可能不一致。

import json  # 新增代码+GuiV2Stream：把 V2 事件编码进 SSE data 行；如果没有这一行，EventSource 收不到结构化 JSON。
from pathlib import Path  # 新增代码+GuiV2Stream：用 Path 定位 workspace 状态目录；如果没有这一行，路径拼接容易在 Windows 上出错。
from typing import Any  # 新增代码+GuiV2Stream：标注通用 JSON payload；如果没有这一行，事件转换边界不清楚。

from learning_agent.app.gui_protocol import make_event  # 新增代码+GuiV2Stream：复用 V2 事件生成 helper；如果没有这一行，stream 事件形状会和协议测试分裂。
from learning_agent.runtime.status_events import StatusEvent, StatusEventStore  # 新增代码+GuiV2Stream：读取统一状态事件事实源；如果没有这一行，GUI stream 会旁路真实运行事件。


_STATUS_TO_GUI_V2_KIND = {  # 新增代码+GuiV2Stream：映射段开始，把当前 status event 转成 V2 GUI kind；如果没有这段，前端 V2 状态机无法消费旧事件名。
    "gui_turn_running": "turn_started",  # 新增代码+GuiV2Stream：把 GUI turn 运行事件映射为 turn_started；如果没有这一项，启动态无法进入 V2 流。
    "gui_turn_completed": "message_completed",  # 新增代码+GuiV2Stream：把完成事件映射为 message_completed；如果没有这一项，消息完成态无法进入 V2 流。
    "gui_turn_failed": "turn_failed",  # 新增代码+GuiV2Stream：把失败事件映射为 turn_failed；如果没有这一项，失败态无法进入 V2 流。
    "gui_turn_cancelled": "turn_cancelled",  # 新增代码+GuiV2Stream：把取消事件映射为 turn_cancelled；如果没有这一项，取消态无法进入 V2 流。
    "gui_turn_cancelling": "turn_cancelled",  # 新增代码+GuiV2Stream：把取消中事件暂时映射为取消类事件；如果没有这一项，取消按钮状态无法从 V2 流更新。
    "permission_required": "permission_requested",  # 新增代码+GuiV2Stream：把旧权限请求映射为 V2 权限请求；如果没有这一项，权限弹窗无法接收旧事实源。
    "computer_use_permission_required": "permission_requested",  # 新增代码+GuiV2Stream：把 Computer Use 权限请求映射为 V2 权限请求；如果没有这一项，桌面权限不会进入 V2 流。
    "gui_turn_needs_permission": "permission_requested",  # 新增代码+GuiV2Stream：把 GUI needs_permission 映射为权限请求；如果没有这一项，权限等待状态无法进入 V2 流。
    "permission_answered": "permission_answered",  # 新增代码+GuiV2Stream：保留权限已回答事件；如果没有这一项，权限弹窗无法闭合。
    "gui_permission_answered": "permission_answered",  # 新增代码+GuiV2Stream：把 GUI 权限回答映射为 V2 权限回答；如果没有这一项，后端审计结果不会进入 V2 流。
}  # 新增代码+GuiV2Stream：映射段结束；如果没有这一行，Python 字典语法不完整。


def _clean_sse_text(text: str) -> str:  # 新增代码+GuiV2Stream：函数段开始，清理 SSE comment 文本；如果没有这段，换行可能注入额外 SSE 字段。
    return text.replace("\r", " ").replace("\n", " ")  # 新增代码+GuiV2Stream：把换行替换为空格；如果没有这一行，注释文本可能破坏 event-stream 帧。
# 新增代码+GuiV2Stream：函数段结束，_clean_sse_text 到此结束；如果没有这个边界说明，用户不容易看出清理范围。


def format_sse_comment(text: str) -> bytes:  # 新增代码+GuiV2Stream：函数段开始，生成 SSE comment 字节；如果没有这段，长连接保活没有标准格式。
    return f": {_clean_sse_text(text)}\n\n".encode("utf-8")  # 新增代码+GuiV2Stream：返回 `: comment` 格式；如果没有这一行，浏览器不会把它当合法 SSE 注释。
# 新增代码+GuiV2Stream：函数段结束，format_sse_comment 到此结束；如果没有这个边界说明，用户不容易看出 comment 编码范围。


def format_sse_event(event: dict[str, object]) -> bytes:  # 新增代码+GuiV2Stream：函数段开始，把 V2 事件编码成 SSE 帧；如果没有这段，EventSource 无法消费后端事件。
    event_id = str(event.get("event_id", ""))  # 新增代码+GuiV2Stream：读取事件 id；如果没有这一行，SSE id 行没有来源。
    event_kind = str(event.get("kind", "message"))  # 新增代码+GuiV2Stream：读取事件类型；如果没有这一行，SSE event 行没有来源。
    data = json.dumps(event, ensure_ascii=False, separators=(",", ": "))  # 新增代码+GuiV2Stream：把完整事件编码成一行 JSON；如果没有这一行，前端拿不到事件详情。
    return f"id: {event_id}\nevent: {event_kind}\ndata: {data}\n\n".encode("utf-8")  # 新增代码+GuiV2Stream：返回标准 SSE 帧；如果没有这一行，浏览器不会触发事件回调。
# 新增代码+GuiV2Stream：函数段结束，format_sse_event 到此结束；如果没有这个边界说明，用户不容易看出 event 编码范围。


def _safe_limit(limit: int) -> int:  # 新增代码+GuiV2Stream：函数段开始，限制一次 stream/fallback 返回数量；如果没有这段，超大 limit 可能拖慢 GUI。
    return max(1, min(200, int(limit)))  # 新增代码+GuiV2Stream：把 limit 限制在 1 到 200；如果没有这一行，0 或超大值会造成不稳定行为。
# 新增代码+GuiV2Stream：函数段结束，_safe_limit 到此结束；如果没有这个边界说明，用户不容易看出限制规则。


def _heartbeat_event(sequence: int, degraded: bool = False) -> dict[str, object]:  # 新增代码+GuiV2Stream：函数段开始，生成 V2 heartbeat 事件；如果没有这段，空事件流会让 UI 误以为断线。
    payload: dict[str, object] = {"status": "idle"}  # 新增代码+GuiV2Stream：默认 heartbeat 表示空闲保活；如果没有这一行，前端无法显示安全的空状态。
    if degraded:  # 新增代码+GuiV2Stream：判断是否是降级 heartbeat；如果没有这一行，读取失败和正常空闲无法区分。
        payload = {"status": "degraded", "degraded": True, "message": "GUI event stream is temporarily unavailable."}  # 新增代码+GuiV2Stream：使用不含本机路径的降级信息；如果没有这一行，错误可能泄露本地文件路径。
    return make_event("heartbeat", max(0, int(sequence)), payload)  # 新增代码+GuiV2Stream：返回不推进业务游标的 heartbeat；如果没有这一行，重连可能跳过真实事件。
# 新增代码+GuiV2Stream：函数段结束，_heartbeat_event 到此结束；如果没有这个边界说明，用户不容易看出 heartbeat 规则。


def _event_payload(raw_event: StatusEvent) -> dict[str, Any]:  # 新增代码+GuiV2Stream：函数段开始，构造 V2 事件 payload；如果没有这段，source event 信息会丢失。
    raw = raw_event.to_dict()  # 新增代码+GuiV2Stream：把 StatusEvent 转成 dict；如果没有这一行，后续无法读取 timestamp 和顶层身份字段。
    payload = raw.get("payload", {}) if isinstance(raw.get("payload", {}), dict) else {}  # 新增代码+GuiV2Stream：安全读取原始 payload；如果没有这一行，坏事件载荷会拖垮 stream。
    return {"source_event_type": raw_event.event_type, **payload}  # 新增代码+GuiV2Stream：保留原始事件类型并合并业务 payload；如果没有这一行，诊断时不知道 V2 kind 来源。
# 新增代码+GuiV2Stream：函数段结束，_event_payload 到此结束；如果没有这个边界说明，用户不容易看出 payload 转换范围。


def _to_gui_v2_event(raw_event: StatusEvent) -> dict[str, object]:  # 新增代码+GuiV2Stream：函数段开始，把 StatusEvent 转成 GUI V2 event；如果没有这段，stream/fallback 会返回旧事件形状。
    raw = raw_event.to_dict()  # 新增代码+GuiV2Stream：读取原始事件 dict；如果没有这一行，无法保留 timestamp。
    kind = _STATUS_TO_GUI_V2_KIND.get(raw_event.event_type, "heartbeat")  # 新增代码+GuiV2Stream：把旧事件类型映射成 V2 kind；如果没有这一行，前端 V2 类型无法收窄。
    event = make_event(kind, raw_event.sequence, _event_payload(raw_event), run_id=raw_event.run_id, turn_id=raw_event.turn_id)  # 新增代码+GuiV2Stream：生成标准 V2 事件；如果没有这一行，字段形状会和协议合同不一致。
    event["event_id"] = f"status_{raw_event.sequence}"  # 新增代码+GuiV2Stream：用 status sequence 生成稳定事件 id；如果没有这一行，重连去重会变得随机。
    event["created_at"] = str(raw.get("timestamp", event["created_at"]))  # 新增代码+GuiV2Stream：复用原始事件时间；如果没有这一行，历史事件会显示为转换时间。
    return event  # 新增代码+GuiV2Stream：返回 V2 事件；如果没有这一行，调用方拿不到转换结果。
# 新增代码+GuiV2Stream：函数段结束，_to_gui_v2_event 到此结束；如果没有这个边界说明，用户不容易看出事件转换范围。


def select_events_after(workspace: Path, since_sequence: int | None, limit: int) -> list[dict[str, object]]:  # 新增代码+GuiV2Stream：函数段开始，读取 since_sequence 后的 V2 事件；如果没有这段，SSE 和 fallback 会重复读取逻辑。
    safe_since = int(since_sequence) if since_sequence is not None else None  # 新增代码+GuiV2Stream：规范化游标；如果没有这一行，StatusEventStore 可能收到字符串或空值。
    try:  # 新增代码+GuiV2Stream：保护事件读取；如果没有这一行，Windows 文件锁或坏状态会让 stream 路由泄露异常。
        store = StatusEventStore(Path(workspace).expanduser().resolve() / "memory" / "status")  # 新增代码+GuiV2Stream：定位统一 status store；如果没有这一行，stream 会读取错误目录。
        raw_events = store.list_events(since_sequence=safe_since, limit=_safe_limit(limit))  # 新增代码+GuiV2Stream：读取增量事件；如果没有这一行，stream 没有业务数据来源。
    except Exception:  # 新增代码+GuiV2Stream：捕获读取失败；如果没有这一行，本地路径异常可能变成 HTTP 500 正文。
        return [_heartbeat_event(safe_since or 0, degraded=True)]  # 新增代码+GuiV2Stream：返回低敏降级 heartbeat；如果没有这一行，前端会静默或看到本机路径。
    if not raw_events:  # 新增代码+GuiV2Stream：处理没有新事件的情况；如果没有这一行，UI 会长时间无任何信号。
        return [_heartbeat_event(safe_since or 0)]  # 新增代码+GuiV2Stream：返回不推进游标的 heartbeat；如果没有这一行，重连可能误以为空闲即结束。
    return [_to_gui_v2_event(event) for event in raw_events]  # 新增代码+GuiV2Stream：返回所有转换后的 V2 事件；如果没有这一行，调用方拿不到业务事件。
# 新增代码+GuiV2Stream：函数段结束，select_events_after 到此结束；如果没有这个边界说明，用户不容易看出事件选择范围。
