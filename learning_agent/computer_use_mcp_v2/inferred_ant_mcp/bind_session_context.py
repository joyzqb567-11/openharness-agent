"""Computer Use MCP v2 agent-side 会话绑定。"""  # 修改代码+ComputerUseMcpV2：说明本文件负责把 agent 主循环能力绑定进 v2 context；如果没有这一行，读者不容易知道 ask_permission/trace 从哪里进入 v2。
from __future__ import annotations  # 修改代码+ComputerUseMcpV2：延迟解析类型注解；如果没有这一行，导入阶段更容易被循环类型引用影响。

from typing import Any  # 修改代码+ComputerUseMcpV2：导入 Any 用于 duck-typing agent；如果没有这一行，函数签名无法表达这里接收多种 agent/fake agent。

from .legacy_ports import build_legacy_host_adapter  # 新增代码+ComputerUseMcpV2HostAdapter：导入 v2 内部旧成熟 host 构造器；如果没有这一行，bind_session_context 只能继续把旧 controller 错当 v2 host。
from .types import ComputerUseMcpV2Context  # 修改代码+ComputerUseMcpV2：导入 v2 上下文数据结构；如果没有这一行，绑定函数无法创建共享 context。

try:  # 修改代码+ComputerUseMcpV2：优先导入项目内安全 observation helper；如果没有这一段，v2 只能尝试调用 agent 私有方法。
    from learning_agent.core import run_helpers as run_helpers_from_core  # 修改代码+ComputerUseMcpV2：导入 safe_record_observation；如果没有这一行，fake agent 或字段缺失时 observation 写入可能崩溃。
except ModuleNotFoundError as error:  # 修改代码+ComputerUseMcpV2：兼容 start_oauth_agent.bat 脚本模式；如果没有这一行，直接脚本启动时可能因包名前缀不同失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.run_helpers"}:  # 修改代码+ComputerUseMcpV2：只允许路径差异进入 fallback；如果没有这一行，真实导入错误会被误吞。
        raise  # 修改代码+ComputerUseMcpV2：重新抛出非路径类错误；如果没有这一行，排查 core helper bug 会很难。
    from core import run_helpers as run_helpers_from_core  # type: ignore  # 修改代码+ComputerUseMcpV2：脚本模式导入 safe_record_observation；如果没有这一行，bat 模式 v2 observation 无法写回 agent。

try:  # 修改代码+ComputerUseMcpV2：优先导入正式验收事件写入器；如果没有这一段，v2 工具执行不会进入验收事件流。
    from learning_agent.observability.acceptance_events import emit_acceptance_event as default_emit_acceptance_event  # 修改代码+ComputerUseMcpV2：导入默认验收事件函数；如果没有这一行，真实终端验收难以区分 v2 控制动作。
except ModuleNotFoundError as error:  # 修改代码+ComputerUseMcpV2：兼容脚本模式路径；如果没有这一行，bat 模式可能因包名前缀不同失败。
    if error.name not in {"learning_agent", "learning_agent.observability", "learning_agent.observability.acceptance_events"}:  # 修改代码+ComputerUseMcpV2：只允许路径差异 fallback；如果没有这一行，验收模块内部错误会被误吞。
        raise  # 修改代码+ComputerUseMcpV2：重新抛出真实导入错误；如果没有这一行，验收事件链 bug 会被隐藏。
    from observability.acceptance_events import emit_acceptance_event as default_emit_acceptance_event  # type: ignore  # 修改代码+ComputerUseMcpV2：脚本模式导入默认验收事件函数；如果没有这一行，bat 模式缺少事件桥。


# 修改代码+ComputerUseMcpV2：函数段开始，_ensure_runtime_trace_events 确保 agent 有可写 trace 列表；如果没有这段函数，record_runtime_trace 可能把事件 append 到临时列表后丢失。
def _ensure_runtime_trace_events(agent: Any) -> list[dict[str, Any]]:  # 修改代码+ComputerUseMcpV2：声明 trace 列表保障入口；如果没有这一行，绑定函数会重复写 getattr/setattr 细节。
    events = getattr(agent, "computer_use_runtime_trace_events", None)  # 修改代码+ComputerUseMcpV2：读取 agent 当前 trace 列表；如果没有这一行，无法判断是否需要初始化。
    if isinstance(events, list):  # 修改代码+ComputerUseMcpV2：确认已有字段是列表；如果没有这一行，非列表字段会导致 append 失败。
        return events  # 修改代码+ComputerUseMcpV2：复用已有 trace 列表；如果没有这一行，历史 trace 会被覆盖。
    events = []  # 修改代码+ComputerUseMcpV2：创建新的 trace 列表；如果没有这一行，缺字段 agent 无法记录 v2 执行证据。
    setattr(agent, "computer_use_runtime_trace_events", events)  # 修改代码+ComputerUseMcpV2：把新列表写回 agent；如果没有这一行，后续工具调用仍然读不到同一份 trace。
    return events  # 修改代码+ComputerUseMcpV2：返回可写 trace 列表；如果没有这一行，调用方拿不到容器。
# 修改代码+ComputerUseMcpV2：函数段结束，_ensure_runtime_trace_events 到此结束；如果没有这个边界说明，用户不容易看出 trace 初始化范围。


# 修改代码+ComputerUseMcpV2：函数段开始，bind_session_context 从 agent 构建或复用 v2 context；如果没有这段函数，agent-side wrapper 会重复拼装回调并丢失状态。
def bind_session_context(agent: Any) -> ComputerUseMcpV2Context:  # 修改代码+ComputerUseMcpV2：声明 v2 context 绑定入口；如果没有这一行，wrapper 无法拿到统一会话上下文。
    existing = getattr(agent, "_computer_use_mcp_v2_context", None)  # 修改代码+ComputerUseMcpV2：读取已有 v2 context；如果没有这一行，每次工具调用都会重建授权和剪贴板状态。
    if isinstance(existing, ComputerUseMcpV2Context):  # 修改代码+ComputerUseMcpV2：确认已有对象类型正确；如果没有这一行，污染字段可能被误用。
        return existing  # 修改代码+ComputerUseMcpV2：复用已有 context；如果没有这一行，跨工具状态无法保留。
    _ensure_runtime_trace_events(agent)  # 修改代码+ComputerUseMcpV2StateLoop：确保 agent trace 字段先存在但不捕获旧列表对象；如果没有这一行，轻量 fake agent 可能缺少 trace 容器。
    record_observation = lambda kind, payload: run_helpers_from_core.safe_record_observation(agent, kind, payload)  # 修改代码+ComputerUseMcpV2：绑定安全 observation 写入；如果没有这一行，observe/screenshot 证据不能回到主循环。
    def record_runtime_trace(event: dict[str, Any]) -> None:  # 修改代码+ComputerUseMcpV2StateLoop：函数段开始，每次从 agent 当前 trace 字段写入 v2 事件；如果没有这段函数，旧 mature trace recorder 替换列表后 v2 tool_completed 会写丢。
        current_events = _ensure_runtime_trace_events(agent)  # 修改代码+ComputerUseMcpV2StateLoop：读取 agent 上最新的 trace 列表；如果没有这行代码，回调可能继续写入已经被旧 recorder 替换掉的旧列表。
        current_events.append(dict(event))  # 修改代码+ComputerUseMcpV2StateLoop：追加 v2 runtime 事件副本；如果没有这行代码，tool_started/tool_completed 无法进入长任务审计。
        setattr(agent, "computer_use_runtime_trace_events", current_events[-300:])  # 修改代码+ComputerUseMcpV2StateLoop：把裁剪后的最新列表写回 agent；如果没有这行代码，长期 Computer Use 任务可能无限累积 trace 或写回丢失。
    # 修改代码+ComputerUseMcpV2StateLoop：函数段结束，record_runtime_trace 到此结束；如果没有这个边界说明，用户不容易看出 v2 trace 写入会跟随 agent 当前列表。
    ask_permission = getattr(agent, "ask_permission", None)  # 修改代码+ComputerUseMcpV2：读取 agent 权限回调；如果没有这一行，request_access 无法请求用户确认。
    emit_acceptance = getattr(agent, "emit_acceptance_event", None) or default_emit_acceptance_event  # 修改代码+ComputerUseMcpV2：优先使用 agent 自带验收事件，否则使用默认事件桥；如果没有这一行，可见终端验收缺少事件记录。
    explicit_host = getattr(agent, "computer_use_mcp_v2_host", None)  # 新增代码+ComputerUseMcpV2HostAdapter：读取显式 v2 host，单测和未来原生 v2 后端可直接接管；如果没有这一行，fake host 会被旧 adapter 覆盖。
    legacy_host = None if explicit_host is not None else build_legacy_host_adapter(agent, emit_acceptance)  # 新增代码+ComputerUseMcpV2HostAdapter：没有显式 v2 host 时才构造旧成熟 adapter host；如果没有这一行，旧 controller 会继续接口错配或 fake host 会被污染。
    host = explicit_host or legacy_host  # 修改代码+ComputerUseMcpV2HostAdapter：最终 host 只可能是 v2 host 或旧 session adapter host；如果没有这一行，context 无法拿到正确执行对象。
    context = ComputerUseMcpV2Context(host=host, ask_permission=ask_permission, record_observation=record_observation, record_runtime_trace=record_runtime_trace, emit_acceptance_event=emit_acceptance)  # 修改代码+ComputerUseMcpV2：创建绑定主循环能力的 v2 context；如果没有这一行，v2 工具只能孤立运行。
    setattr(agent, "_computer_use_mcp_v2_context", context)  # 修改代码+ComputerUseMcpV2：把 context 写回 agent 供后续复用；如果没有这一行，授权、剪贴板和 trace 状态不能跨调用保留。
    return context  # 修改代码+ComputerUseMcpV2：返回绑定完成的 context；如果没有这一行，wrapper 拿不到执行对象。
# 修改代码+ComputerUseMcpV2：函数段结束，bind_session_context 到此结束；如果没有这个边界说明，用户不容易看出 agent-side 绑定范围。
