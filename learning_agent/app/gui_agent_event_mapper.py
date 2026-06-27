"""把 core/agent.py 的 AgentEvent 安全转换为 Desktop GUI V2 事件。"""  # 新增代码+RealHarnessEventMapper：本模块只做事件映射；如果没有这一行，读者很难知道它不是运行 agent 的地方。

from __future__ import annotations  # 新增代码+RealHarnessEventMapper：启用延迟类型解析；如果没有这一行，AgentEvent 等类型标注更容易受导入顺序影响。

import copy  # 新增代码+RealHarnessEventMapper：复制事件 payload 后再脱敏；如果没有这一行，脱敏过程可能改到原始 AgentEvent。
from pathlib import Path  # 新增代码+RealHarnessEventMapper：规范化 workspace 路径用于脱敏；如果没有这一行，Windows 路径替换会更脆弱。
from typing import Any  # 新增代码+RealHarnessEventMapper：表达递归 JSON-like payload；如果没有这一行，脱敏函数类型边界不清楚。

from learning_agent.app.gui_protocol import make_event  # 新增代码+RealHarnessEventMapper：复用 GUI V2 事件工厂；如果没有这一行，事件形状会和协议模块分裂。
from learning_agent.core.events import AgentEvent  # 新增代码+RealHarnessEventMapper：读取 core 主循环的标准事件对象；如果没有这一行，映射器只能处理松散 dict。


SENSITIVE_KEY_MARKERS = ("token", "secret", "authorization", "password", "api_key", "apikey", "bearer", "credential")  # 新增代码+RealHarnessEventMapper：集中列出敏感键片段；如果没有这一行，access_token 等字段可能漏进 GUI。
SENSITIVE_VALUE_PREFIXES = ("sk-", "sess-", "Bearer ")  # 新增代码+RealHarnessEventMapper：集中列出敏感值前缀；如果没有这一行，常见密钥字符串可能以普通文本泄露。
REDACTED_VALUE = "[redacted]"  # 新增代码+RealHarnessEventMapper：统一脱敏占位；如果没有这一行，测试和 GUI 难以稳定判断字段已被遮蔽。
WORKSPACE_VALUE = "[workspace]"  # 新增代码+RealHarnessEventMapper：统一工作区占位；如果没有这一行，本机绝对路径可能进入前端事件。
MAX_PAYLOAD_TEXT_CHARS = 1000  # 新增代码+RealHarnessTraceCap：限制单个字符串进入 GUI 事件的长度；如果没有这一行，长 stdout/stderr 可能撑爆事件流和前端面板。


def _truncate_visible_text(value: str) -> str:  # 新增代码+RealHarnessTraceCap：函数段开始，截断过长可见文本；如果没有这段，工具输出会把 GUI trace 变得不可用。
    clean_value = str(value)  # 新增代码+RealHarnessTraceCap：把输入收敛为字符串；如果没有这一行，长度判断可能遇到非字符串对象。
    if len(clean_value) <= MAX_PAYLOAD_TEXT_CHARS:  # 新增代码+RealHarnessTraceCap：短文本直接保留；如果没有这一行，所有文本都会被无意义追加截断标记。
        return clean_value  # 新增代码+RealHarnessTraceCap：返回未截断文本；如果没有这一行，正常短消息会丢失。
    return clean_value[:MAX_PAYLOAD_TEXT_CHARS] + "...[truncated]"  # 新增代码+RealHarnessTraceCap：截断并保留可识别标记；如果没有这一行，用户不知道工具输出被裁剪。
# 新增代码+RealHarnessTraceCap：函数段结束，_truncate_visible_text 到此结束；如果没有这个边界说明，用户不容易看出它只负责长度保护。


def _safe_workspace_text(workspace: str | Path) -> str:  # 新增代码+RealHarnessEventMapper：函数段开始，规范化 workspace 字符串；如果没有这段，路径脱敏会受相对路径影响。
    if not workspace:  # 新增代码+RealHarnessEventMapper：空 workspace 不需要处理；如果没有这一行，Path("") 可能变成当前目录并误脱敏。
        return ""  # 新增代码+RealHarnessEventMapper：返回空字符串表示没有 workspace；如果没有这一行，调用方会继续处理无意义路径。
    try:  # 新增代码+RealHarnessEventMapper：保护路径 resolve；如果没有这一行，坏路径可能打断事件映射。
        return str(Path(workspace).expanduser().resolve())  # 新增代码+RealHarnessEventMapper：返回绝对路径文本；如果没有这一行，大小写或相对路径可能漏掉。
    except (OSError, RuntimeError):  # 新增代码+RealHarnessEventMapper：处理非法路径或解析失败；如果没有这一行，GUI 事件会因脱敏失败而丢失。
        return str(workspace)  # 新增代码+RealHarnessEventMapper：回退原始文本用于 best-effort 替换；如果没有这一行，无法继续脱敏。
# 新增代码+RealHarnessEventMapper：函数段结束，_safe_workspace_text 到此结束；如果没有这个边界说明，用户不容易看出它只负责路径文本。


def _key_is_sensitive(key: str) -> bool:  # 新增代码+RealHarnessEventMapper：函数段开始，判断字段名是否敏感；如果没有这段，递归脱敏会到处重复条件。
    lowered_key = str(key).casefold()  # 新增代码+RealHarnessEventMapper：字段名转小写；如果没有这一行，Access_Token 这类大小写变化会漏判。
    return any(marker in lowered_key for marker in SENSITIVE_KEY_MARKERS)  # 新增代码+RealHarnessEventMapper：命中任一敏感片段就脱敏；如果没有这一行，函数没有判定结果。
# 新增代码+RealHarnessEventMapper：函数段结束，_key_is_sensitive 到此结束；如果没有这个边界说明，用户不容易看出它只判断键名。


def _string_is_sensitive(value: str) -> bool:  # 新增代码+RealHarnessEventMapper：函数段开始，判断字符串值是否像密钥；如果没有这段，裸 Bearer token 可能漏出。
    clean_value = str(value or "")  # 新增代码+RealHarnessEventMapper：把未知输入收敛成字符串；如果没有这一行，None 或对象会让 startswith 出错。
    return any(clean_value.startswith(prefix) for prefix in SENSITIVE_VALUE_PREFIXES)  # 新增代码+RealHarnessEventMapper：常见密钥前缀命中就脱敏；如果没有这一行，函数没有输出。
# 新增代码+RealHarnessEventMapper：函数段结束，_string_is_sensitive 到此结束；如果没有这个边界说明，用户不容易看出它只判断值。


def redact_gui_agent_payload(value: Any, workspace: str | Path = "") -> Any:  # 新增代码+RealHarnessEventMapper：函数段开始，递归脱敏 AgentEvent payload；如果没有这段，真实 core 事件可能把路径或 token 写入 GUI。
    workspace_text = _safe_workspace_text(workspace)  # 新增代码+RealHarnessEventMapper：准备待替换的 workspace 文本；如果没有这一行，字符串值无法隐藏本机目录。
    if isinstance(value, dict):  # 新增代码+RealHarnessEventMapper：处理对象 payload；如果没有这一行，嵌套字段无法按键名脱敏。
        redacted: dict[str, Any] = {}  # 新增代码+RealHarnessEventMapper：准备输出对象；如果没有这一行，递归结果没有容器。
        for raw_key, raw_item in value.items():  # 新增代码+RealHarnessEventMapper：逐个字段处理；如果没有这一行，对象内容不会被复制。
            key = str(raw_key)  # 新增代码+RealHarnessEventMapper：把字段名收敛为字符串；如果没有这一行，非字符串键无法安全比较。
            redacted[key] = REDACTED_VALUE if _key_is_sensitive(key) else redact_gui_agent_payload(raw_item, workspace_text)  # 新增代码+RealHarnessEventMapper：敏感键直接遮蔽，否则递归处理；如果没有这一行，脱敏规则不会生效。
        return redacted  # 新增代码+RealHarnessEventMapper：返回脱敏对象；如果没有这一行，调用方拿不到结果。
    if isinstance(value, list):  # 新增代码+RealHarnessEventMapper：处理数组 payload；如果没有这一行，工具列表或消息列表无法递归脱敏。
        return [redact_gui_agent_payload(item, workspace_text) for item in value]  # 新增代码+RealHarnessEventMapper：递归处理每个元素；如果没有这一行，列表内容会原样泄露。
    if isinstance(value, str):  # 新增代码+RealHarnessEventMapper：处理字符串 payload；如果没有这一行，路径和裸 token 无法遮蔽。
        if _string_is_sensitive(value):  # 新增代码+RealHarnessEventMapper：检查字符串是否像密钥；如果没有这一行，Bearer 字符串会进入 GUI。
            return REDACTED_VALUE  # 新增代码+RealHarnessEventMapper：密钥值返回遮蔽占位；如果没有这一行，密钥仍会显示。
        redacted_text = value.replace(workspace_text, WORKSPACE_VALUE) if workspace_text else value  # 修改代码+RealHarnessTraceCap：先替换本机 workspace 绝对路径；如果没有这一行，事件会泄露用户磁盘路径。
        return _truncate_visible_text(redacted_text)  # 新增代码+RealHarnessTraceCap：再限制可见字符串长度；如果没有这一行，超长工具输出仍会进入 GUI。
    return value  # 新增代码+RealHarnessEventMapper：普通数字/布尔/None 原样返回；如果没有这一行，非容器值会丢失。
# 新增代码+RealHarnessEventMapper：函数段结束，redact_gui_agent_payload 到此结束；如果没有这个边界说明，用户不容易看出脱敏范围。


def _agent_event_base_payload(agent_event: AgentEvent, workspace: str | Path) -> dict[str, Any]:  # 新增代码+RealHarnessEventMapper：函数段开始，构造每个 GUI 事件都携带的来源摘要；如果没有这段，前端无法追溯原始 core 事件。
    payload = redact_gui_agent_payload(copy.deepcopy(agent_event.payload), workspace)  # 新增代码+RealHarnessEventMapper：复制并脱敏原始 payload；如果没有这一行，敏感字段可能进入 GUI 或污染原事件。
    return {"source_event_type": agent_event.event_type, "agent_run_id": agent_event.run_id, "agent_sequence": agent_event.sequence, "agent_session_id": agent_event.session_id, **(payload if isinstance(payload, dict) else {})}  # 新增代码+RealHarnessEventMapper：合并来源和业务字段；如果没有这一行，GUI 事件缺少核心上下文。
# 新增代码+RealHarnessEventMapper：函数段结束，_agent_event_base_payload 到此结束；如果没有这个边界说明，用户不容易看出来源字段范围。


def _tool_payload(base_payload: dict[str, Any]) -> dict[str, Any]:  # 新增代码+RealHarnessEventMapper：函数段开始，提取工具事件常用字段；如果没有这段，tool_started/tool_finished 字段会不稳定。
    tool_call = base_payload.get("tool_call", {}) if isinstance(base_payload.get("tool_call", {}), dict) else {}  # 新增代码+RealHarnessEventMapper：安全读取 tool_call；如果没有这一行，坏 payload 会让映射器异常。
    tool_name = str(tool_call.get("name", tool_call.get("tool_name", base_payload.get("tool_name", ""))))  # 修改代码+RealHarnessReadOnlyTraceFix：兼容 core 事件里的 tool_name 字段；如果没有这一行，真实 read_file 工具开始事件会显示空工具名。
    return {"tool_name": tool_name, "tool_call_id": str(tool_call.get("call_id", base_payload.get("call_id", ""))), "arguments": redact_gui_agent_payload(tool_call.get("arguments", {})), **base_payload}  # 修改代码+RealHarnessReadOnlyTraceFix：返回工具卡片需要的稳定字段；如果没有这一行，TracePanel 很难渲染工具名。
# 新增代码+RealHarnessEventMapper：函数段结束，_tool_payload 到此结束；如果没有这个边界说明，用户不容易看出工具字段抽取范围。


def agent_event_to_gui_events(agent_event: AgentEvent, run_id: str, turn_id: str, sequence_start: int = 1, workspace: str | Path = "", user_cancelled: bool = False) -> list[dict[str, object]]:  # 新增代码+RealHarnessEventMapper：函数段开始，把一个 AgentEvent 转成一个或多个 GUI V2 event；如果没有这段，真实 core 主循环无法进入桌面时间线。
    base_payload = _agent_event_base_payload(agent_event, workspace)  # 新增代码+RealHarnessEventMapper：准备脱敏基础 payload；如果没有这一行，每个分支都要重复清洗。
    event_type = agent_event.event_type  # 新增代码+RealHarnessEventMapper：保存原始事件类型；如果没有这一行，后续分支会反复访问属性。
    sequence = int(sequence_start)  # 新增代码+RealHarnessEventMapper：保存 GUI 局部事件序号；如果没有这一行，make_event 可能收到非整数。
    if event_type == "model_request_started":  # 新增代码+RealHarnessEventMapper：模型请求开始映射到 GUI 状态条；如果没有这一行，真实模型调用不可见。
        return [make_event("model_call_started", sequence, base_payload, run_id=run_id, turn_id=turn_id)]  # 新增代码+RealHarnessEventMapper：发出 model_call_started；如果没有这一行，GUI 不知道 core 已开始请求模型。
    if event_type == "model_message_delta":  # 新增代码+RealHarnessEventMapper：模型文本增量映射到助手流式文本；如果没有这一行，真实 agent 没有打字效果。
        return [make_event("message_delta", sequence, {"text_delta": str(base_payload.get("text_delta", "")), **base_payload}, run_id=run_id, turn_id=turn_id)]  # 新增代码+RealHarnessEventMapper：发出 message_delta；如果没有这一行，前端看不到增量文本。
    if event_type in {"model_message_completed", "model_response_completed"}:  # 新增代码+RealHarnessEventMapper：模型消息完成映射到模型状态完成；如果没有这一行，状态条会一直显示请求中。
        return [make_event("model_call_completed", sequence, base_payload, run_id=run_id, turn_id=turn_id)]  # 新增代码+RealHarnessEventMapper：发出 model_call_completed；如果没有这一行，GUI 缺少模型完成证据。
    if event_type in {"tool_use_seen", "tool_call_started"}:  # 新增代码+RealHarnessEventMapper：工具意图或开始映射到工具卡片开始；如果没有这一行，工具运行不会出现在 TracePanel。
        return [make_event("tool_started", sequence, _tool_payload(base_payload), run_id=run_id, turn_id=turn_id)]  # 新增代码+RealHarnessEventMapper：发出 tool_started；如果没有这一行，GUI 无法显示工具起点。
    if event_type in {"tool_result_seen", "tool_call_completed"}:  # 新增代码+RealHarnessEventMapper：工具结果映射到工具卡片完成；如果没有这一行，工具卡片会停在 running。
        return [make_event("tool_finished", sequence, _tool_payload(base_payload), run_id=run_id, turn_id=turn_id)]  # 新增代码+RealHarnessEventMapper：发出 tool_finished；如果没有这一行，GUI 无法显示工具结果。
    if event_type == "run_completed":  # 新增代码+RealHarnessEventMapper：core run 完成映射到 GUI 终态；如果没有这一行，bridge 不知道最终文本。
        final_text = str(base_payload.get("text", base_payload.get("final_text", "")))  # 新增代码+RealHarnessEventMapper：读取最终文本；如果没有这一行，message_completed 可能为空。
        if user_cancelled or str(base_payload.get("reason", "")) == "stop_requested":  # 新增代码+RealHarnessEventMapper：把 core 的 stop_requested 视为 GUI 取消；如果没有这一行，取消会被误显示为完成。
            return [make_event("turn_cancelled", sequence, {"final_text": final_text, **base_payload}, run_id=run_id, turn_id=turn_id)]  # 新增代码+RealHarnessEventMapper：发出 turn_cancelled；如果没有这一行，取消按钮没有终态事件。
        return [make_event("message_completed", sequence, {"final_text": final_text, **base_payload}, run_id=run_id, turn_id=turn_id)]  # 新增代码+RealHarnessEventMapper：发出 message_completed；如果没有这一行，助手消息不会完成。
    if event_type == "run_failed":  # 新增代码+RealHarnessEventMapper：core run 失败映射到 GUI 失败；如果没有这一行，异常会变成未知诊断事件。
        return [make_event("turn_failed", sequence, {"status": "failed", "error_code": "agent_run_failed", **base_payload}, run_id=run_id, turn_id=turn_id)]  # 新增代码+RealHarnessEventMapper：发出 turn_failed；如果没有这一行，GUI 无法进入 failed。
    return [make_event("agent_diagnostic", sequence, base_payload, run_id=run_id, turn_id=turn_id)]  # 新增代码+RealHarnessEventMapper：其它 core 事件进入诊断流；如果没有这一行，task_state/compact 等证据会丢失。
# 新增代码+RealHarnessEventMapper：函数段结束，agent_event_to_gui_events 到此结束；如果没有这个边界说明，用户不容易看出映射责任。
