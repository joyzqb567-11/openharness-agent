"""Computer Use MCP v2 agent-side 会话绑定。"""  # 修改代码+ClaudeCodeLockParity：说明本文件负责把 agent 主循环能力和锁生命周期绑定进 v2 context；如果没有这一行，读者不容易知道 ask_permission/trace/lock 从哪里进入 v2。
from __future__ import annotations  # 修改代码+ClaudeCodeLockParity：延迟解析类型注解；如果没有这一行，导入阶段更容易被循环类型引用影响。

from typing import Any  # 修改代码+ClaudeCodeLockParity：导入 Any 用于 duck-typing agent/runtime；如果没有这一行，函数签名无法表达这里接收多种 agent/fake agent。

from .legacy_ports import build_legacy_host_adapter  # 新增代码+ComputerUseMcpV2HostAdapter：导入 v2 内部旧成熟 host 构造器；如果没有这一行，bind_session_context 只能继续把旧 controller 错当 v2 host。
from .types import ComputerUseMcpV2Context  # 修改代码+ClaudeCodeLockParity：导入 v2 上下文数据结构；如果没有这一行，绑定函数无法创建共享 context。

try:  # 修改代码+ClaudeCodeLockParity：优先导入项目内安全 observation helper；如果没有这一段，v2 只能尝试调用 agent 私有方法。
    from learning_agent.core import run_helpers as run_helpers_from_core  # 修改代码+ClaudeCodeLockParity：导入 safe_record_observation；如果没有这一行，fake agent 或字段缺失时 observation 写入可能崩溃。
except ModuleNotFoundError as error:  # 修改代码+ClaudeCodeLockParity：兼容 start_oauth_agent.bat 脚本模式；如果没有这一行，直接脚本启动时可能因包名前缀不同失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.run_helpers"}:  # 修改代码+ClaudeCodeLockParity：只允许路径差异进入 fallback；如果没有这一行，真实导入错误会被误吞。
        raise  # 修改代码+ClaudeCodeLockParity：重新抛出非路径类错误；如果没有这一行，排查 core helper bug 会很难。
    from core import run_helpers as run_helpers_from_core  # type: ignore  # 修改代码+ClaudeCodeLockParity：脚本模式导入 safe_record_observation；如果没有这一行，bat 模式 v2 observation 无法写回 agent。

try:  # 修改代码+ClaudeCodeLockParity：优先导入正式验收事件写入器；如果没有这一段，v2 工具执行不会进入验收事件流。
    from learning_agent.observability.acceptance_events import emit_acceptance_event as default_emit_acceptance_event  # 修改代码+ClaudeCodeLockParity：导入默认验收事件函数；如果没有这一行，真实终端验收难以区分 v2 控制动作。
except ModuleNotFoundError as error:  # 修改代码+ClaudeCodeLockParity：兼容脚本模式路径；如果没有这一行，bat 模式可能因包名前缀不同失败。
    if error.name not in {"learning_agent", "learning_agent.observability", "learning_agent.observability.acceptance_events"}:  # 修改代码+ClaudeCodeLockParity：只允许路径差异 fallback；如果没有这一行，验收模块内部错误会被误吞。
        raise  # 修改代码+ClaudeCodeLockParity：重新抛出真实导入错误；如果没有这一行，验收事件链 bug 会被隐藏。
    from observability.acceptance_events import emit_acceptance_event as default_emit_acceptance_event  # type: ignore  # 修改代码+ClaudeCodeLockParity：脚本模式导入默认验收事件函数；如果没有这一行，bat 模式缺少事件桥。


def _ensure_runtime_trace_events(agent: Any) -> list[dict[str, Any]]:  # 修改代码+ComputerUseMcpV2：函数段开始，确保 agent 有可写 trace 列表；如果没有这段函数，record_runtime_trace 可能把事件 append 到临时列表后丢失。
    events = getattr(agent, "computer_use_runtime_trace_events", None)  # 修改代码+ComputerUseMcpV2：读取 agent 当前 trace 列表；如果没有这一行，无法判断是否需要初始化。
    if isinstance(events, list):  # 修改代码+ComputerUseMcpV2：确认已有字段是列表；如果没有这一行，非列表字段会导致 append 失败。
        return events  # 修改代码+ComputerUseMcpV2：复用已有 trace 列表；如果没有这一行，历史 trace 会被覆盖。
    events = []  # 修改代码+ComputerUseMcpV2：创建新的 trace 列表；如果没有这一行，缺字段 agent 无法记录 v2 执行证据。
    setattr(agent, "computer_use_runtime_trace_events", events)  # 修改代码+ComputerUseMcpV2：把新列表写回 agent；如果没有这一行，后续工具调用仍然读不到同一份 trace。
    return events  # 修改代码+ComputerUseMcpV2：返回可写 trace 列表；如果没有这一行，调用方拿不到容器。
# 修改代码+ComputerUseMcpV2：函数段结束，_ensure_runtime_trace_events 到此结束；如果没有这个边界说明，用户不容易看出 trace 初始化范围。


def _computer_use_lock_runtime(agent: Any) -> Any | None:  # 新增代码+ClaudeCodeLockParity：函数段开始，获取或创建与 agent 主循环一致的 Computer Use session runtime；如果没有这段函数，v2 MCP 锁可能写到另一套目录。
    runtime_factory = getattr(agent, "_computer_use_cleanup_runtime", None)  # 新增代码+ClaudeCodeLockParity：优先读取 agent 已有 cleanup runtime 工厂；如果没有这行代码，绑定层会绕开主循环现成锁目录规则。
    if callable(runtime_factory):  # 新增代码+ClaudeCodeLockParity：确认工厂可调用；如果没有这行代码，非函数字段会被误调用。
        return runtime_factory()  # 新增代码+ClaudeCodeLockParity：复用主循环 runtime；如果没有这行代码，finally cleanup 和工具取锁可能不在同一事实源。
    existing_runtime = getattr(agent, "computer_use_turn_cleanup_runtime", None)  # 新增代码+ClaudeCodeLockParity：读取外部注入 runtime；如果没有这行代码，单元测试或宿主注入对象会被忽略。
    if existing_runtime is not None:  # 新增代码+ClaudeCodeLockParity：已有 runtime 时直接使用；如果没有这行代码，注入依赖会被新建对象覆盖。
        return existing_runtime  # 新增代码+ClaudeCodeLockParity：返回注入 runtime；如果没有这行代码，绑定层拿不到锁管理器。
    try:  # 新增代码+ClaudeCodeLockParity：没有 agent 工厂时尝试创建默认 v2 Windows runtime；如果没有这段代码，轻量 agent 无法获得 lock callbacks。
        from learning_agent.computer_use_mcp_v2.windows_runtime.session_runtime import WindowsComputerUseSessionRuntime  # 新增代码+ClaudeCodeLockParity：包模式导入 session runtime；如果没有这行代码，无法创建默认锁运行时。
    except ModuleNotFoundError as error:  # 新增代码+ClaudeCodeLockParity：兼容 start_oauth_agent.bat 脚本模式；如果没有这行代码，脚本路径下导入可能失败。
        if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.session_runtime"}:  # 新增代码+ClaudeCodeLockParity：只允许包路径差异 fallback；如果没有这行代码，真实内部错误会被误吞。
            raise  # 新增代码+ClaudeCodeLockParity：重新抛出真实导入错误；如果没有这行代码，session_runtime 内部 bug 会被隐藏。
        from computer_use_mcp_v2.windows_runtime.session_runtime import WindowsComputerUseSessionRuntime  # type: ignore  # 新增代码+ClaudeCodeLockParity：脚本模式导入 session runtime；如果没有这行代码，bat 入口无法绑定锁回调。
    runtime = WindowsComputerUseSessionRuntime()  # 新增代码+ClaudeCodeLockParity：创建默认 session runtime；如果没有这行代码，stdio/轻量 agent 没有锁后端。
    setattr(agent, "computer_use_turn_cleanup_runtime", runtime)  # 新增代码+ClaudeCodeLockParity：缓存 runtime 供后续 cleanup 复用；如果没有这行代码，多次绑定可能创建多套锁对象。
    return runtime  # 新增代码+ClaudeCodeLockParity：返回可用 runtime；如果没有这行代码，绑定函数拿不到 runtime。
# 新增代码+ClaudeCodeLockParity：函数段结束，_computer_use_lock_runtime 到此结束；如果没有这个边界说明，用户不容易看出锁 runtime 获取范围。


def _lock_callbacks_from_runtime(runtime: Any) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParity：函数段开始，从 session runtime 构造 context 锁回调；如果没有这段函数，bind_session_context 会充满重复 lambda 和字段判断。
    lock_manager = getattr(runtime, "lock_manager", None)  # 新增代码+ClaudeCodeLockParity：读取底层 lock manager；如果没有这行代码，无法调用 status/acquire/release/has_lock。
    session_id = str(getattr(runtime, "session_id", "computer-use-mcp-v2-session") or "computer-use-mcp-v2-session")  # 新增代码+ClaudeCodeLockParity：读取 runtime 会话 id；如果没有这行代码，锁 owner 会话不稳定。
    if lock_manager is None:  # 新增代码+ClaudeCodeLockParity：没有 lock manager 时不绑定真实回调；如果没有这行代码，后续 getattr None 会崩溃。
        return {"computer_use_session_id": session_id}  # 新增代码+ClaudeCodeLockParity：至少返回 session id；如果没有这行代码，context 会丢失会话标识。
    def check_lock(tool_name: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParity：函数段开始，request_access/list_granted 只读取锁状态；如果没有这段函数，查询类工具会错误取锁。
        status = dict(lock_manager.status())  # 新增代码+ClaudeCodeLockParity：读取锁状态；如果没有这行代码，check 回调没有事实来源。
        status.update({"ok": True, "checked": True, "lock_backend": "windows_runtime", "tool_name": str(tool_name)})  # 新增代码+ClaudeCodeLockParity：补充 runtime 可读字段；如果没有这行代码，runtime 无法稳定判断检查成功。
        return status  # 新增代码+ClaudeCodeLockParity：返回检查结果；如果没有这行代码，调用方拿不到锁状态。
    # 新增代码+ClaudeCodeLockParity：函数段结束，check_lock 到此结束；如果没有这个边界说明，用户不容易看出检查锁回调范围。
    def acquire_lock(tool_name: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParity：函数段开始，为动作/观察获取桌面锁；如果没有这段函数，真实桌面动作无法独占控制权。
        acquire_result = dict(lock_manager.acquire(session_id, owner_label=f"computer-use-mcp-v2:{tool_name}", metadata={"tool_name": str(tool_name), "runtime": "computer_use_mcp_v2"}) or {})  # 新增代码+ClaudeCodeLockParity：调用 durable acquire；如果没有这行代码，工具不会真正持锁。
        acquire_result["lock_backend"] = "windows_runtime"  # 新增代码+ClaudeCodeLockParity：标记锁后端来源；如果没有这行代码，debug 无法说明用了 Windows runtime。
        return acquire_result  # 新增代码+ClaudeCodeLockParity：返回取锁结果；如果没有这行代码，runtime 无法判断是否继续执行。
    # 新增代码+ClaudeCodeLockParity：函数段结束，acquire_lock 到此结束；如果没有这个边界说明，用户不容易看出取锁回调范围。
    def release_lock(reason: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParity：函数段开始，释放本 session 桌面锁；如果没有这段函数，轻量 cleanup 无法释放锁。
        release_result = dict(lock_manager.release(session_id) or {})  # 新增代码+ClaudeCodeLockParity：调用 durable release；如果没有这行代码，turn cleanup 可能留下锁。
        release_result.update({"lock_backend": "windows_runtime", "reason": str(reason)})  # 新增代码+ClaudeCodeLockParity：补充后端和原因；如果没有这行代码，释放结果缺少可审计上下文。
        return release_result  # 新增代码+ClaudeCodeLockParity：返回释放结果；如果没有这行代码，cleanup helper 无法判断释放是否成功。
    # 新增代码+ClaudeCodeLockParity：函数段结束，release_lock 到此结束；如果没有这个边界说明，用户不容易看出释放锁回调范围。
    def cleanup_after_turn(reason: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeLockParity：函数段开始，调用完整 session cleanup；如果没有这段函数，abort 清理和通知可能被绕过。
        cleanup_method = getattr(runtime, "cleanup_turn", None)  # 新增代码+ClaudeCodeLockParity：读取 runtime cleanup 方法；如果没有这行代码，坏 runtime 会触发属性错误。
        if callable(cleanup_method):  # 新增代码+ClaudeCodeLockParity：只有方法可调用时才执行完整 cleanup；如果没有这行代码，非标准 runtime 会崩溃。
            return dict(cleanup_method(reason=str(reason)) or {})  # 新增代码+ClaudeCodeLockParity：执行完整 cleanup；如果没有这行代码，turn end 不会释放锁/清 abort/写通知。
        fallback = release_lock(reason)  # 新增代码+ClaudeCodeLockParity：缺完整 cleanup 时退回 release；如果没有这行代码，轻量 runtime 无法收尾。
        return {"cleanup_completed": True, "lock_released": bool(fallback.get("released", True)), "release": fallback, "reason": str(reason)}  # 新增代码+ClaudeCodeLockParity：返回 fallback cleanup 摘要；如果没有这行代码，调用方看不到释放结果。
    # 新增代码+ClaudeCodeLockParity：函数段结束，cleanup_after_turn 到此结束；如果没有这个边界说明，用户不容易看出完整 cleanup 回调范围。
    def is_lock_held_locally(_tool_name: str) -> bool:  # 新增代码+ClaudeCodeLockParity：函数段开始，判断当前 session 是否持锁；如果没有这段函数，runtime debug 无法显示本地锁状态。
        has_lock = getattr(lock_manager, "has_lock", None)  # 新增代码+ClaudeCodeLockParity：读取 lock manager 判断方法；如果没有这行代码，非标准 lock manager 会崩溃。
        return bool(has_lock(session_id)) if callable(has_lock) else False  # 新增代码+ClaudeCodeLockParity：返回本 session 是否持锁；如果没有这行代码，debug 只能猜测。
    # 新增代码+ClaudeCodeLockParity：函数段结束，is_lock_held_locally 到此结束；如果没有这个边界说明，用户不容易看出本地持锁回调范围。
    return {"computer_use_session_id": session_id, "check_computer_use_lock": check_lock, "acquire_computer_use_lock": acquire_lock, "release_computer_use_lock": release_lock, "cleanup_after_turn": cleanup_after_turn, "is_lock_held_locally": is_lock_held_locally}  # 新增代码+ClaudeCodeLockParity：返回 context 可直接展开的锁回调；如果没有这行代码，绑定层无法把 runtime 接到 v2 context。
# 新增代码+ClaudeCodeLockParity：函数段结束，_lock_callbacks_from_runtime 到此结束；如果没有这个边界说明，用户不容易看出锁回调构造范围。


def bind_session_context(agent: Any) -> ComputerUseMcpV2Context:  # 修改代码+ClaudeCodeLockParity：函数段开始，从 agent 构建或复用 v2 context；如果没有这段函数，agent-side wrapper 会重复拼装回调并丢失状态。
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
    lock_runtime = _computer_use_lock_runtime(agent)  # 新增代码+ClaudeCodeLockParity：获取与主循环一致的 Computer Use lock runtime；如果没有这行代码，v2 工具无法接入真实锁生命周期。
    lock_callbacks = _lock_callbacks_from_runtime(lock_runtime) if lock_runtime is not None else {}  # 新增代码+ClaudeCodeLockParity：把 runtime 转成 context 回调；如果没有这行代码，context 缺少 check/acquire/release/cleanup。
    explicit_host = getattr(agent, "computer_use_mcp_v2_host", None)  # 新增代码+ComputerUseMcpV2HostAdapter：读取显式 v2 host，单测和未来原生 v2 后端可直接接管；如果没有这一行，fake host 会被旧 adapter 覆盖。
    legacy_host = None if explicit_host is not None else build_legacy_host_adapter(agent, emit_acceptance)  # 新增代码+ComputerUseMcpV2HostAdapter：没有显式 v2 host 时才构造旧成熟 adapter host；如果没有这一行，旧 controller 会继续接口错配或 fake host 会被污染。
    host = explicit_host or legacy_host  # 修改代码+ComputerUseMcpV2HostAdapter：最终 host 只可能是 v2 host 或旧 session adapter host；如果没有这一行，context 无法拿到正确执行对象。
    context = ComputerUseMcpV2Context(host=host, ask_permission=ask_permission, record_observation=record_observation, record_runtime_trace=record_runtime_trace, emit_acceptance_event=emit_acceptance, **lock_callbacks)  # 修改代码+ClaudeCodeLockParity：创建绑定主循环能力和锁生命周期的 v2 context；如果没有这一行，v2 工具只能孤立运行且不会按 ClaudeCode 锁语义执行。
    setattr(agent, "_computer_use_mcp_v2_context", context)  # 修改代码+ComputerUseMcpV2：把 context 写回 agent 供后续复用；如果没有这一行，授权、剪贴板、锁和 trace 状态不能跨调用保留。
    return context  # 修改代码+ComputerUseMcpV2：返回绑定完成的 context；如果没有这一行，wrapper 拿不到执行对象。
# 修改代码+ClaudeCodeLockParity：函数段结束，bind_session_context 到此结束；如果没有这个边界说明，用户不容易看出 agent-side 绑定范围。
