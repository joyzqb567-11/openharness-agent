"""Computer Use 调试模式只读诊断工具。"""  # 新增代码+ComputerUseDebugTools: 说明本文件只负责 Computer Use debug 模式的状态读取；如果没有这一行，读者容易把这些工具误认为顶层 read/write/edit。
from __future__ import annotations  # 新增代码+ComputerUseDebugTools: 延迟解析类型注解；如果没有这一行，脚本模式导入时类型顺序更容易出问题。

import json  # 新增代码+ComputerUseDebugTools: 用 JSON 稳定返回调试结果文本；如果没有这一行，模型难以机器读取诊断输出。
from typing import Any  # 新增代码+ComputerUseDebugTools: 用 Any 表达 LearningAgent 的 duck type；如果没有这一行，本模块会被迫反向导入核心 agent。


# 新增代码+ComputerUseDebugTools: 函数段开始，_json_text 把 payload 转成人和模型都能读的 JSON；如果没有这段函数，每个工具会重复序列化逻辑。
def _json_text(payload: dict[str, Any]) -> str:  # 新增代码+ComputerUseDebugTools: 声明 JSON 文本输出入口；如果没有这一行，executor 无法直接返回调试文本。
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)  # 新增代码+ComputerUseDebugTools: 保留中文并稳定排序输出；如果没有这一行，调试结果顺序和中文显示会不稳定。
# 新增代码+ComputerUseDebugTools: 函数段结束，_json_text 到此结束；如果没有这个边界说明，用户不容易看出统一输出范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，_safe_list 把 agent 上的动态字段整理为列表快照；如果没有这段函数，None 或异常对象会让调试工具崩溃。
def _safe_list(value: Any) -> list[Any]:  # 新增代码+ComputerUseDebugTools: 声明列表兜底入口；如果没有这一行，每个读取工具都要重复类型判断。
    if isinstance(value, list):  # 新增代码+ComputerUseDebugTools: 优先接受已经是列表的事件流；如果没有这一行，正常 observation_events 会被错误丢弃。
        return list(value)  # 新增代码+ComputerUseDebugTools: 返回浅拷贝避免遍历时被外部追加影响；如果没有这一行，长任务事件追加可能让结果不稳定。
    if isinstance(value, tuple):  # 新增代码+ComputerUseDebugTools: 兼容测试里传入元组快照；如果没有这一行，轻量测试对象可能读不到事件。
        return list(value)  # 新增代码+ComputerUseDebugTools: 把元组转成列表；如果没有这一行，下游切片逻辑不统一。
    return []  # 新增代码+ComputerUseDebugTools: 其他类型按空事件处理；如果没有这一行，坏状态会导致 AttributeError 或 TypeError。
# 新增代码+ComputerUseDebugTools: 函数段结束，_safe_list 到此结束；如果没有这个边界说明，用户不容易看出列表容错范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，_safe_dict 把未知对象整理为字典；如果没有这段函数，坏事件 payload 会影响调试结果。
def _safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+ComputerUseDebugTools: 声明字典兜底入口；如果没有这一行，事件读取代码会到处写 isinstance。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+ComputerUseDebugTools: 只复制字典，其他类型返回空字典；如果没有这一行，字符串或列表 payload 会让 get 调用失败。
# 新增代码+ComputerUseDebugTools: 函数段结束，_safe_dict 到此结束；如果没有这个边界说明，用户不容易看出字典容错范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，_safe_limit 解析返回条数限制；如果没有这段函数，模型传大数或坏值会撑爆上下文。
def _safe_limit(raw_value: Any, default: int = 20, maximum: int = 200) -> int:  # 新增代码+ComputerUseDebugTools: 声明 limit 解析入口；如果没有这一行，read_trace 等工具没有统一数量上限。
    try:  # 新增代码+ComputerUseDebugTools: 捕获无法转整数的模型输入；如果没有这一行，字符串或对象 limit 会让工具失败。
        value = int(raw_value) if raw_value is not None else default  # 新增代码+ComputerUseDebugTools: 有值就转整数，没有值用默认；如果没有这一行，无参数调用没有合理默认值。
    except (TypeError, ValueError, OverflowError):  # 新增代码+ComputerUseDebugTools: 处理类型、格式和超大数异常；如果没有这一行，坏参数会冒泡成工具异常。
        value = default  # 新增代码+ComputerUseDebugTools: 非法输入回退默认值；如果没有这一行，调试工具无法自恢复。
    return max(1, min(value, maximum))  # 新增代码+ComputerUseDebugTools: 把 limit 限制在 1 到 maximum；如果没有这一行，0 或超大值会导致空结果或上下文爆炸。
# 新增代码+ComputerUseDebugTools: 函数段结束，_safe_limit 到此结束；如果没有这个边界说明，用户不容易看出数量限制范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，_event_kind 读取 observation kind 或 trace phase；如果没有这段函数，不同事件结构无法统一过滤。
def _event_kind(event: Any) -> str:  # 新增代码+ComputerUseDebugTools: 声明事件类型读取入口；如果没有这一行，kind/phase 兼容逻辑会散落。
    event_dict = _safe_dict(event)  # 新增代码+ComputerUseDebugTools: 先把事件整理为字典；如果没有这一行，坏事件会让 get 调用失败。
    return str(event_dict.get("kind") or event_dict.get("phase") or "")  # 新增代码+ComputerUseDebugTools: 优先读取 observation kind，其次 trace phase；如果没有这一行，trace 事件无法被同一套过滤处理。
# 新增代码+ComputerUseDebugTools: 函数段结束，_event_kind 到此结束；如果没有这个边界说明，用户不容易看出事件类型兼容范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，_event_payload 读取事件 payload；如果没有这段函数，调试工具无法统一拿到工具名、结果和详情。
def _event_payload(event: Any) -> dict[str, Any]:  # 新增代码+ComputerUseDebugTools: 声明事件载荷读取入口；如果没有这一行，payload 读取会重复且脆弱。
    event_dict = _safe_dict(event)  # 新增代码+ComputerUseDebugTools: 先把事件整理为字典；如果没有这一行，坏事件类型会破坏调试工具。
    payload = event_dict.get("payload", {})  # 新增代码+ComputerUseDebugTools: 从标准事件结构读取 payload；如果没有这一行，工具名和结果内容没有来源。
    return _safe_dict(payload)  # 新增代码+ComputerUseDebugTools: payload 也必须兜底成字典；如果没有这一行，非字典 payload 会让后续判断失败。
# 新增代码+ComputerUseDebugTools: 函数段结束，_event_payload 到此结束；如果没有这个边界说明，用户不容易看出 payload 兼容范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，_event_tool_name 尽量从多种事件结构里提取工具名；如果没有这段函数，最近动作结果无法按工具筛选。
def _event_tool_name(event: Any) -> str:  # 新增代码+ComputerUseDebugTools: 声明工具名提取入口；如果没有这一行，assert_last_action 无法判断 expected_tool。
    event_dict = _safe_dict(event)  # 新增代码+ComputerUseDebugTools: 读取事件字典；如果没有这一行，坏事件会触发异常。
    payload = _event_payload(event_dict)  # 新增代码+ComputerUseDebugTools: 读取事件 payload；如果没有这一行，嵌套工具名会丢失。
    return str(event_dict.get("tool_name") or payload.get("tool_name") or payload.get("mcp_tool_name") or payload.get("tool") or "")  # 新增代码+ComputerUseDebugTools: 兼容工具名字段；如果没有这一行，不同工具结果会筛不出来。
# 新增代码+ComputerUseDebugTools: 函数段结束，_event_tool_name 到此结束；如果没有这个边界说明，用户不容易看出工具名提取范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，_event_ok 尽量判断一个结果事件是否成功；如果没有这段函数，断言工具无法检查 expected_ok。
def _event_ok(event: Any) -> bool | None:  # 新增代码+ComputerUseDebugTools: 声明成功状态读取入口；如果没有这一行，assert_last_action 只能做字符串包含检查。
    event_dict = _safe_dict(event)  # 新增代码+ComputerUseDebugTools: 读取事件字典；如果没有这一行，坏事件会触发异常。
    payload = _event_payload(event_dict)  # 新增代码+ComputerUseDebugTools: 读取事件 payload；如果没有这一行，ok 字段可能漏掉。
    if isinstance(event_dict.get("ok"), bool):  # 新增代码+ComputerUseDebugTools: 支持事件顶层 ok 字段；如果没有这一行，直接结果对象无法判断。
        return bool(event_dict.get("ok"))  # 新增代码+ComputerUseDebugTools: 返回顶层 ok；如果没有这一行，状态会丢失。
    if isinstance(payload.get("ok"), bool):  # 新增代码+ComputerUseDebugTools: 支持 payload.ok 字段；如果没有这一行，MCP JSON 结果无法判断。
        return bool(payload.get("ok"))  # 新增代码+ComputerUseDebugTools: 返回 payload ok；如果没有这一行，状态会丢失。
    if isinstance(payload.get("result"), dict) and isinstance(payload["result"].get("ok"), bool):  # 新增代码+ComputerUseDebugTools: 支持 payload.result.ok 嵌套结构；如果没有这一行，部分工具包装结果无法判断。
        return bool(payload["result"].get("ok"))  # 新增代码+ComputerUseDebugTools: 返回嵌套 ok；如果没有这一行，成功状态会误报未知。
    if str(payload.get("state", "")).lower() == "completed":  # 新增代码+ComputerUseDebugTools: MCP progress completed 视为成功；如果没有这一行，已完成外部调用会显示未知状态。
        return True  # 新增代码+ComputerUseDebugTools: 返回成功；如果没有这一行，completed 状态无法通过断言。
    if str(payload.get("state", "")).lower() in {"failed", "permission_denied", "permission_denied_cached"}:  # 新增代码+ComputerUseDebugTools: 失败/拒绝状态视为失败；如果没有这一行，拒绝事件可能被误当未知。
        return False  # 新增代码+ComputerUseDebugTools: 返回失败；如果没有这一行，断言无法检查失败预期。
    return None  # 新增代码+ComputerUseDebugTools: 没有明确状态时返回未知；如果没有这一行，函数没有稳定返回值。
# 新增代码+ComputerUseDebugTools: 函数段结束，_event_ok 到此结束；如果没有这个边界说明，用户不容易看出成功状态推断范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，_event_matches_kind 判断事件是否命中过滤 kind；如果没有这段函数，read_last_observation 的 kind 参数不会生效。
def _event_matches_kind(event: Any, kind_filter: str) -> bool:  # 新增代码+ComputerUseDebugTools: 声明 kind 过滤判断入口；如果没有这一行，事件过滤无法复用。
    requested_kind = str(kind_filter or "").strip()  # 新增代码+ComputerUseDebugTools: 清理用户传入的 kind；如果没有这一行，空格会影响匹配。
    if not requested_kind:  # 新增代码+ComputerUseDebugTools: 没有过滤条件时全部匹配；如果没有这一行，无参数调用会拿不到事件。
        return True  # 新增代码+ComputerUseDebugTools: 返回匹配；如果没有这一行，默认读取最近事件会失败。
    return _event_kind(event) == requested_kind  # 新增代码+ComputerUseDebugTools: 精确匹配事件 kind/phase；如果没有这一行，过滤条件不会真正生效。
# 新增代码+ComputerUseDebugTools: 函数段结束，_event_matches_kind 到此结束；如果没有这个边界说明，用户不容易看出 kind 过滤范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，_is_action_like_event 判断事件是否像 Computer Use 动作结果；如果没有这段函数，最近动作读取会被普通状态事件污染。
def _is_action_like_event(event: Any) -> bool:  # 新增代码+ComputerUseDebugTools: 声明动作事件判断入口；如果没有这一行，read_last_action_result 无法筛掉普通事件。
    kind = _event_kind(event)  # 新增代码+ComputerUseDebugTools: 读取事件类型；如果没有这一行，无法按 kind/phase 判断。
    tool_name = _event_tool_name(event)  # 新增代码+ComputerUseDebugTools: 读取工具名；如果没有这一行，无法识别 mcp__computer-use__ 开头的工具。
    payload = _event_payload(event)  # 新增代码+ComputerUseDebugTools: 读取事件 payload；如果没有这一行，无法检查 action 字段。
    if "computer_use" in kind or "computer-use" in kind or kind in {"tool_result", "mcp_call_progress"}:  # 新增代码+ComputerUseDebugTools: 事件类型命中桌面/工具结果语义；如果没有这一行，很多真实结果会被漏掉。
        return True  # 新增代码+ComputerUseDebugTools: 返回动作相关；如果没有这一行，最近结果会读不到。
    if tool_name.startswith("computer_") or tool_name.startswith("computer-") or tool_name.startswith("mcp__computer-use__"):  # 新增代码+ComputerUseDebugTools: 工具名命中 Computer Use 表面；如果没有这一行，MCP 原子工具结果会被漏掉。
        return True  # 新增代码+ComputerUseDebugTools: 返回动作相关；如果没有这一行，最近结果会读不到。
    return bool(payload.get("action") or payload.get("controller_action"))  # 新增代码+ComputerUseDebugTools: 有 action/controller_action 字段也视为动作；如果没有这一行，controller 包装结果可能被漏掉。
# 新增代码+ComputerUseDebugTools: 函数段结束，_is_action_like_event 到此结束；如果没有这个边界说明，用户不容易看出动作事件筛选范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，_latest_action_event 从 observation 和 trace 中找最近动作结果；如果没有这段函数，读取和断言最近动作会各写一套逻辑。
def _latest_action_event(agent: Any, tool_name_filter: str = "") -> dict[str, Any] | None:  # 新增代码+ComputerUseDebugTools: 声明最近动作结果查找入口；如果没有这一行，两个调试工具无法共享查找逻辑。
    observations = _safe_list(getattr(agent, "observation_events", []))  # 新增代码+ComputerUseDebugTools: 读取 observation 事件快照；如果没有这一行，工具无法查看 executor/MCP 记录。
    traces = _safe_list(getattr(agent, "computer_use_runtime_trace_events", []))  # 新增代码+ComputerUseDebugTools: 读取 Computer Use runtime trace 快照；如果没有这一行，模型请求/工具结果证据会被漏掉。
    requested_tool = str(tool_name_filter or "").strip()  # 新增代码+ComputerUseDebugTools: 清理可选工具名过滤；如果没有这一行，空格会导致误筛选。
    for event in list(observations) + list(traces):  # 新增代码+ComputerUseDebugTools: 合并两个事件源保持整体可扫描；如果没有这一行，后续 reversed 没有候选。
        _safe_dict(event)  # 新增代码+ComputerUseDebugTools: 触发轻量类型兜底，保证坏事件不会中断；如果没有这一行，混入坏事件时后续逻辑风险更高。
    for event in reversed(list(observations) + list(traces)):  # 新增代码+ComputerUseDebugTools: 从最近事件往前找；如果没有这一行，会返回最旧结果而不是最新结果。
        if not _is_action_like_event(event):  # 新增代码+ComputerUseDebugTools: 跳过非动作事件；如果没有这一行，普通状态事件会污染最近动作结果。
            continue  # 新增代码+ComputerUseDebugTools: 继续找下一条候选；如果没有这一行，函数会过早返回无关事件。
        if requested_tool and _event_tool_name(event) != requested_tool:  # 新增代码+ComputerUseDebugTools: 如果指定工具名就必须精确匹配；如果没有这一行，连续动作场景可能读错工具结果。
            continue  # 新增代码+ComputerUseDebugTools: 当前工具名不匹配则继续向前找；如果没有这一行，过滤条件不会生效。
        return _safe_dict(event)  # 新增代码+ComputerUseDebugTools: 返回最近动作事件字典；如果没有这一行，调用方拿不到结果。
    return None  # 新增代码+ComputerUseDebugTools: 找不到动作事件时返回 None；如果没有这一行，函数会隐式返回不清楚。
# 新增代码+ComputerUseDebugTools: 函数段结束，_latest_action_event 到此结束；如果没有这个边界说明，用户不容易看出最近动作查找范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，read_trace 读取最近 Computer Use trace；如果没有这段函数，debug 模式看不到模型请求和工具结果链路。
def read_trace(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+ComputerUseDebugTools: 声明 read_trace 工具实现；如果没有这一行，schema 有工具名但 executor 无法执行。
    limit = _safe_limit(arguments.get("limit"), default=20, maximum=200)  # 新增代码+ComputerUseDebugTools: 读取并限制返回条数；如果没有这一行，trace 可能一次输出太多。
    events = _safe_list(getattr(agent, "computer_use_runtime_trace_events", []))  # 新增代码+ComputerUseDebugTools: 读取 agent 的 runtime trace；如果没有这一行，工具没有数据来源。
    return _json_text({"ok": True, "tool_name": "read_trace", "limit": limit, "event_count": len(events), "events": events[-limit:]})  # 新增代码+ComputerUseDebugTools: 返回最近 trace 事件；如果没有这一行，模型拿不到诊断结果。
# 新增代码+ComputerUseDebugTools: 函数段结束，read_trace 到此结束；如果没有这个边界说明，用户不容易看出 trace 读取范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，read_state 读取 Computer Use 当前状态摘要；如果没有这段函数，debug 模式无法快速判断工具池和上下文。
def read_state(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+ComputerUseDebugTools: 声明 read_state 工具实现；如果没有这一行，schema 有工具名但 executor 无法执行。
    observations = _safe_list(getattr(agent, "observation_events", []))  # 新增代码+ComputerUseDebugTools: 读取 observation 事件快照；如果没有这一行，状态摘要缺少审计数量。
    traces = _safe_list(getattr(agent, "computer_use_runtime_trace_events", []))  # 新增代码+ComputerUseDebugTools: 读取 trace 事件快照；如果没有这一行，状态摘要缺少 trace 数量。
    include_events = bool(arguments.get("include_events", False))  # 新增代码+ComputerUseDebugTools: 读取是否附带最近事件；如果没有这一行，模型无法控制输出详细程度。
    payload: dict[str, Any] = {"ok": True, "tool_name": "read_state", "desktop_task_context": _safe_dict(getattr(agent, "desktop_task_context", {})), "tool_scope_mode": str(getattr(agent, "tool_scope_mode", "")), "loaded_tool_names": sorted(str(name) for name in _safe_list(list(getattr(agent, "loaded_tool_names", [])))), "mcp_tools_enabled": bool(getattr(agent, "mcp_tools_enabled", False)), "active_artifacts": list(getattr(agent, "active_artifacts", []) or []), "observation_event_count": len(observations), "trace_event_count": len(traces)}  # 新增代码+ComputerUseDebugTools: 构造状态摘要；如果没有这一行，debug 模式只能靠分散日志判断状态。
    if include_events:  # 新增代码+ComputerUseDebugTools: 只有用户要求时才展开最近事件；如果没有这一行，状态工具默认会太长。
        payload["recent_observations"] = observations[-5:]  # 新增代码+ComputerUseDebugTools: 附带最近 5 条 observation；如果没有这一行，调试时无法快速看最近审计事件。
        payload["recent_trace_events"] = traces[-5:]  # 新增代码+ComputerUseDebugTools: 附带最近 5 条 trace；如果没有这一行，调试时无法快速看模型/工具链路。
    return _json_text(payload)  # 新增代码+ComputerUseDebugTools: 返回状态 JSON 文本；如果没有这一行，模型拿不到状态结果。
# 新增代码+ComputerUseDebugTools: 函数段结束，read_state 到此结束；如果没有这个边界说明，用户不容易看出状态读取范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，read_last_observation 读取最近 observation；如果没有这段函数，debug 模式无法按 kind 快速查看审计事件。
def read_last_observation(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+ComputerUseDebugTools: 声明 read_last_observation 工具实现；如果没有这一行，schema 有工具名但 executor 无法执行。
    kind_filter = str(arguments.get("kind", "") or "").strip()  # 新增代码+ComputerUseDebugTools: 读取可选 kind 过滤；如果没有这一行，用户传入 kind 不会生效。
    observations = _safe_list(getattr(agent, "observation_events", []))  # 新增代码+ComputerUseDebugTools: 读取 observation 事件快照；如果没有这一行，工具没有数据来源。
    matching_events = [event for event in observations if _event_matches_kind(event, kind_filter)]  # 新增代码+ComputerUseDebugTools: 过滤匹配事件；如果没有这一行，kind 参数不会影响结果。
    last_event = _safe_dict(matching_events[-1]) if matching_events else None  # 新增代码+ComputerUseDebugTools: 取最近匹配事件；如果没有这一行，模型无法看到最后一条 observation。
    return _json_text({"ok": last_event is not None, "tool_name": "read_last_observation", "kind": kind_filter, "matched_count": len(matching_events), "event": last_event})  # 新增代码+ComputerUseDebugTools: 返回最近 observation 或空结果；如果没有这一行，模型拿不到查询结果。
# 新增代码+ComputerUseDebugTools: 函数段结束，read_last_observation 到此结束；如果没有这个边界说明，用户不容易看出 observation 读取范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，read_last_action_result 读取最近动作结果；如果没有这段函数，debug 模式无法验证上一动作是否成功。
def read_last_action_result(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+ComputerUseDebugTools: 声明 read_last_action_result 工具实现；如果没有这一行，schema 有工具名但 executor 无法执行。
    tool_name_filter = str(arguments.get("tool_name", "") or "").strip()  # 新增代码+ComputerUseDebugTools: 读取可选工具名过滤；如果没有这一行，连续动作时不能指定目标工具。
    event = _latest_action_event(agent, tool_name_filter)  # 新增代码+ComputerUseDebugTools: 查找最近动作事件；如果没有这一行，工具没有结果来源。
    return _json_text({"ok": event is not None, "tool_name": "read_last_action_result", "filter_tool_name": tool_name_filter, "event": event, "event_ok": _event_ok(event) if event is not None else None})  # 新增代码+ComputerUseDebugTools: 返回最近动作事件和成功状态；如果没有这一行，模型拿不到动作结果。
# 新增代码+ComputerUseDebugTools: 函数段结束，read_last_action_result 到此结束；如果没有这个边界说明，用户不容易看出动作结果读取范围。


# 新增代码+ComputerUseDebugTools: 函数段开始，assert_last_action 对最近动作结果做结构化断言；如果没有这段函数，debug 验收只能靠模型口头判断。
def assert_last_action(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+ComputerUseDebugTools: 声明 assert_last_action 工具实现；如果没有这一行，schema 有工具名但 executor 无法执行。
    expected_tool = str(arguments.get("expected_tool", "") or "").strip()  # 新增代码+ComputerUseDebugTools: 读取期望工具名；如果没有这一行，不能检查最近结果属于哪个工具。
    expected_ok = arguments.get("expected_ok") if isinstance(arguments.get("expected_ok"), bool) else None  # 新增代码+ComputerUseDebugTools: 读取期望成功状态；如果没有这一行，不能结构化检查成功/失败。
    contains_text = str(arguments.get("contains", "") or "")  # 新增代码+ComputerUseDebugTools: 读取期望包含文本；如果没有这一行，不能检查 marker 或错误类别。
    event = _latest_action_event(agent, expected_tool)  # 新增代码+ComputerUseDebugTools: 按期望工具名查最近事件；如果没有这一行，断言没有目标事件。
    checks: list[dict[str, Any]] = []  # 新增代码+ComputerUseDebugTools: 准备保存每条断言结果；如果没有这一行，返回结果无法解释失败原因。
    if event is None:  # 新增代码+ComputerUseDebugTools: 没找到事件时直接记录失败；如果没有这一行，后续会访问 None。
        checks.append({"name": "event_exists", "passed": False, "detail": "没有找到最近动作结果"})  # 新增代码+ComputerUseDebugTools: 记录事件不存在；如果没有这一行，模型不知道失败原因。
    if event is not None and expected_tool:  # 新增代码+ComputerUseDebugTools: 有事件且用户要求工具名时检查；如果没有这一行，expected_tool 参数不会生效。
        checks.append({"name": "expected_tool", "passed": _event_tool_name(event) == expected_tool, "expected": expected_tool, "actual": _event_tool_name(event)})  # 新增代码+ComputerUseDebugTools: 记录工具名断言；如果没有这一行，工具错配不会被发现。
    if event is not None and expected_ok is not None:  # 新增代码+ComputerUseDebugTools: 有事件且用户要求 ok 时检查；如果没有这一行，expected_ok 参数不会生效。
        checks.append({"name": "expected_ok", "passed": _event_ok(event) == expected_ok, "expected": expected_ok, "actual": _event_ok(event)})  # 新增代码+ComputerUseDebugTools: 记录 ok 断言；如果没有这一行，成功/失败预期无法验证。
    if event is not None and contains_text:  # 新增代码+ComputerUseDebugTools: 有事件且用户要求包含文本时检查；如果没有这一行，contains 参数不会生效。
        event_text = json.dumps(event, ensure_ascii=False, sort_keys=True)  # 新增代码+ComputerUseDebugTools: 把事件转成 JSON 文本用于包含判断；如果没有这一行，复杂嵌套结果无法统一搜索。
        checks.append({"name": "contains", "passed": contains_text in event_text, "expected": contains_text})  # 新增代码+ComputerUseDebugTools: 记录包含断言；如果没有这一行，marker 或错误类别检查无法返回。
    passed = bool(checks) and all(bool(check.get("passed")) for check in checks)  # 新增代码+ComputerUseDebugTools: 汇总所有断言是否通过；如果没有这一行，工具没有最终 ok。
    return _json_text({"ok": passed, "tool_name": "assert_last_action", "checks": checks, "event": event})  # 新增代码+ComputerUseDebugTools: 返回断言结果和原始事件；如果没有这一行，模型无法继续根据失败原因修正。
# 新增代码+ComputerUseDebugTools: 函数段结束，assert_last_action 到此结束；如果没有这个边界说明，用户不容易看出动作断言范围。
