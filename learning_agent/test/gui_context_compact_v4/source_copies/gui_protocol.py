"""Desktop GUI V2 protocol helpers."""  # 新增代码+GuiV2Protocol：说明本模块集中放桌面 GUI V2 协议常量和 helper；如果没有这一行，维护者容易继续把协议散落在 bridge 里。

from __future__ import annotations  # 新增代码+GuiV2Protocol：启用未来注解语法；如果没有这一行，类型标注在旧 Python 行为下可能不一致。

import uuid  # 新增代码+GuiV2Protocol：生成 event_id；如果没有这一行，事件无法获得稳定去重标识。
from datetime import datetime, timezone  # 新增代码+GuiV2Protocol：生成 UTC created_at；如果没有这一行，事件时间只能靠调用方临时拼。
from typing import Any  # 新增代码+GuiV2Protocol：标注 JSON-like payload；如果没有这一行，helper 输入输出边界不清楚。


GUI_V2_SCHEMA_VERSION = 2  # 新增代码+GuiV2Protocol：声明桌面 GUI V2 schema 版本；如果没有这一行，前后端无法判断是否进入 V2 合同。
GUI_V2_TOKEN_HEADER = "X-OpenHarness-Desktop-Token"  # 新增代码+GuiV2Protocol：集中声明本地 bridge token header；如果没有这一行，后端、Electron main 和前端可能写出不同字段名。
GUI_V2_EVENT_KINDS = {  # 新增代码+GuiV2Protocol：集合段开始，列出 V2 主事件类型；如果没有这段，事件状态机没有协议白名单。
    "turn_started",  # 新增代码+GuiV2Protocol：表示一次 turn 已开始；如果没有这一项，前端无法识别运行起点。
    "message_delta",  # 新增代码+GuiV2Protocol：表示助手消息流式增量；如果没有这一项，流式输出没有标准事件。
    "message_completed",  # 新增代码+GuiV2Protocol：表示助手消息完成；如果没有这一项，前端无法稳定进入完成态。
    "runtime_path",  # 新增代码+DirectSseAdapter：表示本轮真实模型运行路径；如果没有这一项，Direct SSE 的第一条诊断事件会被协议门禁拒绝。
    "provider_not_connected",  # 新增代码+DirectSseAdapter：表示所选 provider 尚未连接；如果没有这一项，未连接 OpenAI 会变成后台异常。
    "model_not_available",  # 新增代码+DirectSseAdapter：表示所选模型不适用于当前账号；如果没有这一项，模型菜单无法给出明确失败原因。
    "connect_timeout",  # 新增代码+DirectSseAdapter：表示连接阶段超时；如果没有这一项，慢连接无法分类诊断。
    "first_byte_timeout",  # 新增代码+DirectSseAdapter：表示首包等待超时；如果没有这一项，用户无法区分无响应和流中断。
    "idle_stream_timeout",  # 新增代码+DirectSseAdapter：表示 SSE 流空闲超时或无 completion；如果没有这一项，运行会以泛化失败收场。
    "total_turn_timeout",  # 新增代码+DirectSseAdapter：表示整轮 Direct SSE 超时；如果没有这一项，慢回复问题无法进入可见诊断。
    "endpoint_drift_detected",  # 新增代码+DirectSseAdapter：表示 ChatGPT Codex SSE 协议形状变化；如果没有这一项，端点漂移会被吞成普通失败。
    "request_failed",  # 新增代码+DirectSseAdapter：表示 Direct SSE 请求失败但未归入更细 timeout；如果没有这一项，网络错误无法显示。
    "reactive_compact_completed",  # 新增代码+ReactiveDirectSseCompact：表示 Direct SSE 因上下文超限完成一次压缩恢复；如果没有这一项，adapter 的合法恢复事件会被协议白名单拒绝。
    "direct_sse_route_selected",  # 新增代码+DirectSSEPayload：表示本轮选择了 direct SSE 路由；如果没有这一项，V3 诊断事件会被协议 helper 拒绝。
    "direct_sse_completed",  # 新增代码+DirectSSEPayload：表示 direct SSE 响应已完成；如果没有这一项，V3 完成诊断事件会被协议 helper 拒绝。
    "tool_started",  # 新增代码+GuiV2Protocol：表示工具调用开始；如果没有这一项，TracePanel 无法显示工具运行起点。
    "tool_finished",  # 新增代码+GuiV2Protocol：表示工具调用结束；如果没有这一项，TracePanel 无法显示工具成功或失败。
    "permission_requested",  # 新增代码+GuiV2Protocol：表示后端请求用户权限；如果没有这一项，权限弹窗没有标准事件来源。
    "permission_answered",  # 新增代码+GuiV2Protocol：表示权限请求已回答；如果没有这一项，权限弹窗无法闭合到后端事实。
    "safety_refusal",  # 新增代码+GuiV2Protocol：表示安全拒绝；如果没有这一项，拒绝可能只落在状态栏而不是助手消息。
    "turn_failed",  # 新增代码+GuiV2Protocol：表示 turn 失败；如果没有这一项，失败态无法统一渲染。
    "turn_cancelled",  # 新增代码+GuiV2Protocol：表示 turn 被取消；如果没有这一项，取消按钮无法进入终态。
    "heartbeat",  # 新增代码+GuiV2Protocol：表示长任务保活；如果没有这一项，前端无法区分沉默和仍在运行。
}  # 新增代码+GuiV2Protocol：集合段结束；如果没有这一行，Python 集合语法不完整。
GUI_V2_MESSAGE_PART_KINDS = {  # 新增代码+GuiV2Protocol：集合段开始，列出 V2 消息片段类型；如果没有这段，消息内容无法统一表达文本、拒绝、工具和错误。
    "text_delta",  # 新增代码+GuiV2Protocol：表示流式文本增量；如果没有这一项，边打字边显示没有标准片段。
    "final_text",  # 新增代码+GuiV2Protocol：表示最终文本；如果没有这一项，完成态消息没有标准正文。
    "refusal",  # 新增代码+GuiV2Protocol：表示安全拒绝正文；如果没有这一项，拒绝无法作为一等消息片段。
    "tool_call",  # 新增代码+GuiV2Protocol：表示工具调用请求；如果没有这一项，工具卡片无法从消息流中生成。
    "tool_result",  # 新增代码+GuiV2Protocol：表示工具调用结果；如果没有这一项，工具卡片无法显示完成结果。
    "error",  # 新增代码+GuiV2Protocol：表示可读错误片段；如果没有这一项，失败消息只能依赖外层状态。
}  # 新增代码+GuiV2Protocol：集合段结束；如果没有这一行，Python 集合语法不完整。


def make_error_response(code: str, message: str, request_id: str = "") -> dict[str, object]:  # 新增代码+GuiV2Protocol：函数段开始，生成 V2 结构化错误响应；如果没有这段，前端只能解析不稳定错误形状。
    return {  # 新增代码+GuiV2Protocol：返回错误 payload 字典；如果没有这一行，调用方拿不到响应对象。
        "ok": False,  # 新增代码+GuiV2Protocol：显式标记失败；如果没有这一行，前端无法用统一字段判断失败。
        "code": code,  # 新增代码+GuiV2Protocol：保留机器可读错误码；如果没有这一行，GUI 无法区分 busy、not_found、unauthorized。
        "message": message,  # 新增代码+GuiV2Protocol：保留人类可读错误；如果没有这一行，界面只能显示泛化失败。
        "error": message,  # 新增代码+GuiV2Protocol：保留 V1 错误别名；如果没有这一行，现有读取 error 字段的 UI 会突然失去失败正文。
        "request_id": request_id,  # 新增代码+GuiV2Protocol：保留请求关联 id；如果没有这一行，日志和前端提示无法对应同一次请求。
    }  # 新增代码+GuiV2Protocol：错误 payload 结束；如果没有这一行，Python 字典语法不完整。
# 新增代码+GuiV2Protocol：函数段结束，make_error_response 到此结束；如果没有这个边界说明，用户不容易看出错误响应生成范围。


def make_event(kind: str, sequence: int, payload: dict[str, object], run_id: str = "", turn_id: str = "") -> dict[str, object]:  # 新增代码+GuiV2Protocol：函数段开始，生成 V2 GUI 事件；如果没有这段，事件字段会继续散落且不一致。
    if kind not in GUI_V2_EVENT_KINDS:  # 新增代码+GuiV2Protocol：拒绝未知事件类型；如果没有这一行，拼错 kind 会悄悄进入前端状态机。
        raise ValueError(f"unsupported GUI V2 event kind: {kind}")  # 新增代码+GuiV2Protocol：给出可读协议错误；如果没有这一行，调用方不知道是哪种事件非法。
    return {  # 新增代码+GuiV2Protocol：返回事件 payload 字典；如果没有这一行，调用方拿不到事件对象。
        "sequence": sequence,  # 新增代码+GuiV2Protocol：写入事件序号；如果没有这一行，前端无法稳定排序和增量回放。
        "event_id": f"event_{uuid.uuid4().hex}",  # 新增代码+GuiV2Protocol：写入唯一事件 id；如果没有这一行，React key 和事件去重不稳定。
        "kind": kind,  # 新增代码+GuiV2Protocol：写入事件类型；如果没有这一行，前端状态机不知道如何处理。
        "created_at": datetime.now(timezone.utc).isoformat(),  # 新增代码+GuiV2Protocol：写入 UTC 创建时间；如果没有这一行，诊断时间线缺少时间依据。
        "run_id": run_id,  # 新增代码+GuiV2Protocol：写入 run id；如果没有这一行，状态面板无法按运行聚合。
        "turn_id": turn_id,  # 新增代码+GuiV2Protocol：写入 turn id；如果没有这一行，事件无法关联消息卡。
        "payload": payload,  # 新增代码+GuiV2Protocol：写入业务载荷；如果没有这一行，事件只剩外壳没有内容。
    }  # 新增代码+GuiV2Protocol：事件 payload 结束；如果没有这一行，Python 字典语法不完整。
# 新增代码+GuiV2Protocol：函数段结束，make_event 到此结束；如果没有这个边界说明，用户不容易看出事件生成范围。


def make_message_part(kind: str, payload: dict[str, Any]) -> dict[str, object]:  # 新增代码+GuiV2Protocol：函数段开始，生成 V2 消息片段；如果没有这段，流式文本、拒绝、工具和错误会各自定义形状。
    if kind not in GUI_V2_MESSAGE_PART_KINDS:  # 新增代码+GuiV2Protocol：拒绝未知消息片段类型；如果没有这一行，前端渲染器可能收到无法处理的 kind。
        raise ValueError(f"unsupported GUI V2 message part kind: {kind}")  # 新增代码+GuiV2Protocol：给出可读协议错误；如果没有这一行，调用方难以定位非法 part。
    return {"kind": kind, "payload": payload}  # 新增代码+GuiV2Protocol：返回统一消息片段；如果没有这一行，调用方拿不到标准 part 形状。
# 新增代码+GuiV2Protocol：函数段结束，make_message_part 到此结束；如果没有这个边界说明，用户不容易看出消息片段生成范围。
