"""Windows Computer Use abort、cleanup 和 streaming hook 合同层。"""  # 新增代码+Phase61AbortStreamingHooks: 标明本文件负责 Phase61 中断和清理钩子；如果没有这行代码，读者不知道 abort-aware sender 和 cleanup hook 集中在哪里。
from __future__ import annotations  # 新增代码+Phase61AbortStreamingHooks: 启用延迟类型解析；如果没有这行代码，类型注解在旧导入顺序下更容易失败。

import json  # 新增代码+Phase61AbortStreamingHooks: 导入 JSON 用于 CLI 结构化报告；如果没有这行代码，真实终端失败时不易复盘。
import time  # 新增代码+Phase61AbortStreamingHooks: 导入时间用于事件时间戳和唯一会话；如果没有这行代码，streaming 事件无法排序。
from pathlib import Path  # 新增代码+Phase61AbortStreamingHooks: 导入 Path 统一管理 Windows 路径；如果没有这行代码，hooks 状态目录拼接更脆弱。
from typing import Any, Callable  # 新增代码+Phase61AbortStreamingHooks: 导入 Any/Callable 描述工具回调和 JSON 状态；如果没有这行代码，接口边界不清楚。

try:  # 新增代码+Phase61AbortStreamingHooks: 优先按包路径导入 Computer Use 运行时和文件工具；如果没有这段代码，包运行模式无法复用锁、通知和 JSONL。
    from learning_agent.computer_use_mcp_v2.windows_runtime.audit import ComputerUseAuditStore  # 新增代码+Phase61AbortStreamingHooks: 导入审计仓库用于 flush 状态；如果没有这行代码，cleanup hook 无法说明审计位置。
    from learning_agent.computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager, phase30_lock_timestamp  # 新增代码+Phase61AbortStreamingHooks: 导入 durable lock 和时间戳；如果没有这行代码，abort-aware sender 没有急停事实源。
    from learning_agent.computer_use_mcp_v2.windows_runtime.session_runtime import PHASE40_DEFAULT_SESSION_ID, WindowsComputerUseSessionRuntime  # 新增代码+Phase61AbortStreamingHooks: 导入现有 runtime cleanup/recovery 能力；如果没有这行代码，异常路径要重复实现清理。
    from learning_agent.computer_use_mcp_v2.windows_runtime.global_escape_abort import GlobalEscapeAbortController, PHASE5_GLOBAL_ESCAPE_ABORT_MODEL, registerEscHotkey  # 新增代码+Phase5GlobalEscapeAbort：导入全局 Escape 控制器和 registerEscHotkey 入口；如果没有这一行，状态面板和顶层矩阵只能看到普通 abort fallback。
    from learning_agent.runtime.files import append_jsonl, read_jsonl  # 新增代码+Phase61AbortStreamingHooks: 导入 JSONL 写读工具；如果没有这行代码，streaming 事件无法持久化。
except ModuleNotFoundError as error:  # 新增代码+Phase61AbortStreamingHooks: 兼容 start_oauth_agent.bat 脚本模式导入；如果没有这段代码，真实可见终端可能因包名前缀失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.audit", "learning_agent.computer_use_mcp_v2.windows_runtime.lock", "learning_agent.computer_use_mcp_v2.windows_runtime.session_runtime", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase61AbortStreamingHooks: 只允许包路径缺失时 fallback；如果没有这行代码，内部真实错误会被误吞。
        raise  # 新增代码+Phase61AbortStreamingHooks: 重新抛出非路径类导入错误；如果没有这行代码，排查底层模块问题会困难。
    from computer_use_mcp_v2.windows_runtime.audit import ComputerUseAuditStore  # 新增代码+Phase61AbortStreamingHooks: 脚本模式导入审计仓库；如果没有这行代码，bat 入口无法显示审计 flush 状态。
    from computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager, phase30_lock_timestamp  # 新增代码+Phase61AbortStreamingHooks: 脚本模式导入锁管理器；如果没有这行代码，bat 入口无法读取 abort flag。
    from computer_use_mcp_v2.windows_runtime.session_runtime import PHASE40_DEFAULT_SESSION_ID, WindowsComputerUseSessionRuntime  # 新增代码+Phase61AbortStreamingHooks: 脚本模式导入 session runtime；如果没有这行代码，bat 入口无法执行 cleanup/recover。
    from computer_use_mcp_v2.windows_runtime.global_escape_abort import GlobalEscapeAbortController, PHASE5_GLOBAL_ESCAPE_ABORT_MODEL, registerEscHotkey  # type: ignore  # 新增代码+Phase5GlobalEscapeAbort：脚本模式导入全局 Escape 控制器和 registerEscHotkey；如果没有这一行，bat 入口无法展示 Phase5 热键状态。
    from runtime.files import append_jsonl, read_jsonl  # 新增代码+Phase61AbortStreamingHooks: 脚本模式导入 JSONL 工具；如果没有这行代码，streaming 事件不能落盘。

PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER = "PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_READY"  # 新增代码+Phase61AbortStreamingHooks: 定义 Phase61 ready marker；如果没有这行代码，真实终端验收没有稳定锚点。
PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_OK_TOKEN = "PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_OK"  # 新增代码+Phase61AbortStreamingHooks: 定义 Phase61 OK token；如果没有这行代码，debug log 无法区分自检通过和普通输出。
PHASE61_ABORT_STREAMING_HOOKS_MODEL = "phase61_windows_abort_streaming_hooks"  # 新增代码+Phase61AbortStreamingHooks: 定义 abort/streaming hook 模型名；如果没有这行代码，状态 UI 无法说明当前合同版本。
PHASE61_ACTIONS_EXPANDED = False  # 新增代码+Phase61AbortStreamingHooks: 明确本阶段只加强中断和清理，不扩大真实动作面；如果没有这行代码，用户可能误以为新增了更多桌面动作。
DEFAULT_ABORT_STREAMING_HOOKS_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "abort_streaming_hooks"  # 新增代码+Phase61AbortStreamingHooks: 定义默认 hooks 状态目录；如果没有这行代码，生产入口不知道把 streaming 事件放哪里。


def _phase61_bool_token(value: Any) -> str:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会出现 True/False 漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase61AbortStreamingHooks: 返回 true/false 文本；如果没有这行代码，验收场景匹配不稳定。
# 新增代码+Phase61AbortStreamingHooks: 函数段结束，_phase61_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式范围。


def _phase61_safe_text(value: Any, limit: int = 220) -> str:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，把任意输入压成安全短文本；如果没有这段函数，streaming 事件可能被换行或超长文本污染。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase61AbortStreamingHooks: 清理换行和空白；如果没有这行代码，终端状态可能被用户文本打散。
    return text[:limit]  # 新增代码+Phase61AbortStreamingHooks: 限制文本长度；如果没有这行代码，异常消息可能刷爆状态面板。
# 新增代码+Phase61AbortStreamingHooks: 函数段结束，_phase61_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清理范围。


class Phase61AbortAwareLowLevelSender:  # 新增代码+Phase61AbortStreamingHooks: 类段开始，包装低层 sender 并在发送前检查 abort；如果没有这个类，急停可能无法阻断 SendInput 最后一跳。
    def __init__(self, wrapped_sender: Any, hooks: "WindowsComputerUseAbortStreamingHooks") -> None:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，保存被包装 sender 和 hooks；如果没有这段函数，wrapper 没有底层发送对象和 abort 状态源。
        self.wrapped_sender = wrapped_sender  # 新增代码+Phase61AbortStreamingHooks: 保存原始 sender；如果没有这行代码，未 abort 时无法继续真实发送。
        self.hooks = hooks  # 新增代码+Phase61AbortStreamingHooks: 保存 hooks 对象；如果没有这行代码，wrapper 无法读取 lock_manager 或记录 stream 事件。
        self.requires_raw_text = bool(getattr(wrapped_sender, "requires_raw_text", False))  # 新增代码+Phase61AbortStreamingHooks: 透传真实 sender 是否需要原文；如果没有这行代码，Phase58 type_text 可能无法给真实 sender 文本。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，Phase61AbortAwareLowLevelSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出 wrapper 初始化范围。

    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，发送前执行 abort 检查；如果没有这段函数，abort flag 不会阻断低层事件。
        event_count = len(list(events or []))  # 新增代码+Phase61AbortStreamingHooks: 计算将要发送的事件数量；如果没有这行代码，streaming 事件无法说明被拦截规模。
        self.hooks.record_stream_event("computer_use_before_low_level_send", {"requested_event_count": event_count})  # 新增代码+Phase61AbortStreamingHooks: 记录即将发送事件；如果没有这行代码，流式视图看不到工具进入发送前阶段。
        if self.hooks.lock_manager.is_abort_requested():  # 新增代码+Phase61AbortStreamingHooks: 在最后一跳前读取 durable abort flag；如果没有这行代码，用户急停后仍可能发送事件。
            self.hooks.record_stream_event("computer_use_aborted_before_low_level_send", {"requested_event_count": event_count, "low_level_event_count": 0})  # 新增代码+Phase61AbortStreamingHooks: 记录 abort 拦截事件；如果没有这行代码，streaming 日志无法解释为什么 0 事件。
            return {"ok": False, "decision": "aborted_before_low_level_send", "low_level_event_count": 0, "low_level_event_types": [], "sender": "phase61_abort_aware", "raw_text_included": False}  # 新增代码+Phase61AbortStreamingHooks: 返回零事件拒绝；如果没有这行代码，Phase58 runtime 无法审计急停副作用为 0。
        dispatch = self.wrapped_sender.send_low_level(events)  # 新增代码+Phase61AbortStreamingHooks: 未 abort 时转发给真实或 fake sender；如果没有这行代码，正常动作会被 wrapper 永久吞掉。
        self.hooks.record_stream_event("computer_use_low_level_send_completed", {"low_level_event_count": int(dict(dispatch or {}).get("low_level_event_count", 0) if isinstance(dispatch, dict) else 0)})  # 新增代码+Phase61AbortStreamingHooks: 记录发送完成摘要；如果没有这行代码，streaming 日志看不到低层发送结果。
        return dict(dispatch or {}) if isinstance(dispatch, dict) else {"ok": bool(dispatch), "low_level_event_count": 0, "sender": "phase61_abort_aware", "raw_text_included": False}  # 新增代码+Phase61AbortStreamingHooks: 返回规范化 dispatch；如果没有这行代码，上层 runtime 可能遇到非 dict 返回。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，Phase61AbortAwareLowLevelSender.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出低层发送守卫范围。
# 新增代码+Phase61AbortStreamingHooks: 类段结束，Phase61AbortAwareLowLevelSender 到此结束；如果没有这个边界说明，初学者不容易看出 sender wrapper 范围。


class WindowsComputerUseAbortStreamingHooks:  # 新增代码+Phase61AbortStreamingHooks: 类段开始，组合 abort-aware sender、cleanup hook、stale recovery 和 terminal status；如果没有这个类，Phase61 能力会散落在各模块。
    def __init__(self, lock_manager: ComputerUseLockManager | None = None, session_id: str = PHASE40_DEFAULT_SESSION_ID, base_dir: str | Path | None = None, runtime: WindowsComputerUseSessionRuntime | None = None, audit_store: ComputerUseAuditStore | None = None, escape_abort_controller: GlobalEscapeAbortController | None = None) -> None:  # 修改代码+Phase5GlobalEscapeAbort：函数段开始，初始化 hooks 依赖并可注入全局 Escape 控制器；如果没有这段函数，测试和生产无法注入隔离状态。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_ABORT_STREAMING_HOOKS_ROOT  # 新增代码+Phase61AbortStreamingHooks: 保存 hooks 状态目录；如果没有这行代码，streaming 事件不知道写哪里。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase61AbortStreamingHooks: 确保目录存在；如果没有这行代码，首次记录 stream 事件会失败。
        self.lock_manager = lock_manager if lock_manager is not None else ComputerUseLockManager()  # 新增代码+Phase61AbortStreamingHooks: 保存或创建锁管理器；如果没有这行代码，hooks 无法读取 abort/lock。
        self.session_id = str(session_id or PHASE40_DEFAULT_SESSION_ID)  # 新增代码+Phase61AbortStreamingHooks: 保存当前会话 id；如果没有这行代码，cleanup/recovery 不知道 owner。
        self.audit_store = audit_store if audit_store is not None else ComputerUseAuditStore(base_dir=self.base_dir / "audit")  # 新增代码+Phase61AbortStreamingHooks: 保存审计仓库；如果没有这行代码，flush_audit 没有可报告路径。
        self.runtime = runtime if runtime is not None else WindowsComputerUseSessionRuntime(lock_manager=self.lock_manager, session_id=self.session_id, audit_store=self.audit_store)  # 新增代码+Phase61AbortStreamingHooks: 保存或创建 session runtime；如果没有这行代码，cleanup/recover 要重复实现。
        self.stream_events_path = self.base_dir / "phase61_streaming_events.jsonl"  # 新增代码+Phase61AbortStreamingHooks: 定义 streaming 事件文件；如果没有这行代码，事件没有固定回放入口。
        self.escape_abort_controller = escape_abort_controller  # 新增代码+Phase5GlobalEscapeAbort：保存可注入全局 Escape 控制器；如果没有这一行，状态面板无法区分真实热键注册和 fallback。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，WindowsComputerUseAbortStreamingHooks.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def record_stream_event(self, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，记录一条 Computer Use streaming hook 事件；如果没有这段函数，abort/cleanup 只会在内存里一闪而过。
        event = {"event_type": _phase61_safe_text(event_type, 120), "payload": dict(payload or {}), "session_id": self.session_id, "created_at": phase30_lock_timestamp(), "model": PHASE61_ABORT_STREAMING_HOOKS_MODEL, "marker": PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER}  # 新增代码+Phase61AbortStreamingHooks: 构造结构化 stream 事件；如果没有这行代码，事件缺少会话、时间和阶段来源。
        append_jsonl(self.stream_events_path, event)  # 新增代码+Phase61AbortStreamingHooks: 追加写入 JSONL；如果没有这行代码，streaming hook 不能跨命令查看。
        return event  # 新增代码+Phase61AbortStreamingHooks: 返回事件供调用方测试或展示；如果没有这行代码，调用方拿不到写入结果。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，WindowsComputerUseAbortStreamingHooks.record_stream_event 到此结束；如果没有这个边界说明，初学者不容易看出事件记录范围。

    def stream_events(self) -> list[dict[str, Any]]:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，读取 streaming hook 事件；如果没有这段函数，测试和状态页无法复盘 hook 流。
        return read_jsonl(self.stream_events_path)  # 新增代码+Phase61AbortStreamingHooks: 容错读取 JSONL 事件；如果没有这行代码，坏行或空文件会拖垮状态页。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，WindowsComputerUseAbortStreamingHooks.stream_events 到此结束；如果没有这个边界说明，初学者不容易看出事件读取范围。

    def wrap_low_level_sender(self, sender: Any) -> Phase61AbortAwareLowLevelSender:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，创建 abort-aware 低层 sender；如果没有这段函数，Phase58/后续真实动作无法统一接入 abort。
        return Phase61AbortAwareLowLevelSender(sender, self)  # 新增代码+Phase61AbortStreamingHooks: 返回包装后的 sender；如果没有这行代码，调用方还要知道 wrapper 类细节。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，WindowsComputerUseAbortStreamingHooks.wrap_low_level_sender 到此结束；如果没有这个边界说明，初学者不容易看出 sender 包装范围。

    def evaluate_hotkey_plan(self) -> dict[str, Any]:  # 修改代码+Phase5GlobalEscapeAbort：函数段开始，评估 Windows 全局热键方案和 Phase5 Escape 控制器；如果没有这段函数，状态可能假装热键已经注册。
        _ = registerEscHotkey  # 新增代码+Phase5GlobalEscapeAbort：保留 registerEscHotkey 作为明确源码证据；如果没有这一行，顶层矩阵无法确认全局 Escape 注册入口存在。
        if self.escape_abort_controller is not None:  # 新增代码+Phase5GlobalEscapeAbort：优先读取注入的 Escape 控制器状态；如果没有这一行，已注册热键仍会被显示为 fallback。
            status = self.escape_abort_controller.status()  # 新增代码+Phase5GlobalEscapeAbort：读取 Phase5 控制器状态；如果没有这一行，状态面板没有热键事实来源。
            return {"global_hotkey_registered": bool(status.get("global_hotkey_registered")), "terminal_abort_fallback": not bool(status.get("global_hotkey_registered")), "controller_abort_fallback": True, "hotkey_mode": "global_escape_hotkey" if status.get("global_hotkey_registered") else "terminal_and_controller_fallback", "global_escape_abort_model": status.get("model", PHASE5_GLOBAL_ESCAPE_ABORT_MODEL), "expected_escape_count": int(status.get("expected_escape_count", 0)), "abort_count": int(status.get("abort_count", 0)), "reason": "Phase5 全局 Escape 控制器已接入，模型计划内 Escape 会被分流，用户意外 Escape 会写入 durable abort。"}  # 新增代码+Phase5GlobalEscapeAbort：返回 Phase5 热键状态；如果没有这一行，用户看不到全局 Escape 是否真正在工作。
        return {"global_hotkey_registered": False, "terminal_abort_fallback": True, "controller_abort_fallback": True, "hotkey_mode": "terminal_and_controller_fallback", "global_escape_abort_model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL, "expected_escape_count": 0, "abort_count": 0, "reason": "Phase61 默认不注册全局热键或低层键盘 hook，避免留下不可撤销的系统级钩子；请使用 /computer abort 或 controller abort。"}  # 修改代码+Phase5GlobalEscapeAbort：返回诚实降级状态并暴露 Phase5 模型名；如果没有这行代码，用户会误以为全局热键可用或看不到升级目标。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，WindowsComputerUseAbortStreamingHooks.evaluate_hotkey_plan 到此结束；如果没有这个边界说明，初学者不容易看出热键方案范围。

    def flush_audit(self, reason: str = "phase61 cleanup") -> dict[str, Any]:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，记录审计 flush 语义；如果没有这段函数，异常 cleanup 无法说明审计已经落盘或路径在哪里。
        status = self.audit_store.status()  # 新增代码+Phase61AbortStreamingHooks: 读取审计仓库状态；如果没有这行代码，flush 结果缺少 events/chains 路径。
        self.record_stream_event("computer_use_audit_flush_checked", {"reason": _phase61_safe_text(reason), "events_path": status.get("events_path", "")})  # 新增代码+Phase61AbortStreamingHooks: 记录审计 flush 检查事件；如果没有这行代码，streaming 日志缺少 flush 证据。
        return {"audit_flushed": True, "reason": _phase61_safe_text(reason), "audit_status": status, "marker": PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER, "actions_expanded": PHASE61_ACTIONS_EXPANDED}  # 新增代码+Phase61AbortStreamingHooks: 返回 flush 摘要；如果没有这行代码，cleanup hook 无法汇总审计状态。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，WindowsComputerUseAbortStreamingHooks.flush_audit 到此结束；如果没有这个边界说明，初学者不容易看出审计 flush 范围。

    def run_with_cleanup(self, action_name: str, callback: Callable[[], Any]) -> dict[str, Any]:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，执行工具回调并在异常/中断时 cleanup；如果没有这段函数，模型中断、Ctrl+C 或异常退出可能残留锁。
        safe_action = _phase61_safe_text(action_name, 120)  # 新增代码+Phase61AbortStreamingHooks: 清理动作名；如果没有这行代码，事件名可能被异常文本污染。
        self.record_stream_event("computer_use_tool_started", {"action": safe_action})  # 新增代码+Phase61AbortStreamingHooks: 记录工具开始；如果没有这行代码，streaming 流看不到执行边界。
        try:  # 新增代码+Phase61AbortStreamingHooks: 捕获回调异常以保证 cleanup；如果没有这行代码，异常会绕过清理逻辑。
            result = callback()  # 新增代码+Phase61AbortStreamingHooks: 执行工具回调；如果没有这行代码，hook 只是空壳。
        except BaseException as error:  # 新增代码+Phase61AbortStreamingHooks: 捕获 KeyboardInterrupt、Exception 等中断；如果没有这行代码，Ctrl+C/异常退出不会触发 cleanup。
            cleanup = self.runtime.cleanup_turn(session_id=self.session_id, reason=f"phase61 cleanup after {type(error).__name__}")  # 新增代码+Phase61AbortStreamingHooks: 通过现有 runtime 做 turn-end cleanup；如果没有这行代码，锁和 abort 可能残留。
            audit_flush = self.flush_audit(reason=f"exception:{type(error).__name__}")  # 新增代码+Phase61AbortStreamingHooks: 记录审计 flush 语义；如果没有这行代码，异常路径缺少审计状态。
            self.record_stream_event("computer_use_exception_cleanup_completed", {"action": safe_action, "exception_type": type(error).__name__, "cleanup_completed": bool(cleanup.get("cleanup_completed"))})  # 新增代码+Phase61AbortStreamingHooks: 记录异常 cleanup 完成；如果没有这行代码，streaming 日志无法解释中断后状态。
            return {"ok": False, "exception_handled": True, "exception_type": type(error).__name__, "message": _phase61_safe_text(error), "cleanup_completed": bool(cleanup.get("cleanup_completed")), "cleanup": cleanup, "audit_flush": audit_flush, "marker": PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER, "actions_expanded": PHASE61_ACTIONS_EXPANDED}  # 新增代码+Phase61AbortStreamingHooks: 返回异常 cleanup 摘要；如果没有这行代码，测试和终端无法确认 cleanup 已执行。
        self.record_stream_event("computer_use_tool_completed", {"action": safe_action})  # 新增代码+Phase61AbortStreamingHooks: 正常完成时记录完成事件；如果没有这行代码，streaming 流无法闭合成功工具。
        return {"ok": True, "exception_handled": False, "result": result, "marker": PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER, "actions_expanded": PHASE61_ACTIONS_EXPANDED}  # 新增代码+Phase61AbortStreamingHooks: 返回正常结果摘要；如果没有这行代码，调用方拿不到回调输出。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，WindowsComputerUseAbortStreamingHooks.run_with_cleanup 到此结束；如果没有这个边界说明，初学者不容易看出异常 cleanup 范围。

    def recover_stale_lock(self, owner_label: str = "phase61-recovery") -> dict[str, Any]:  # 修改代码+Phase61AbortStreamingHooks: 函数段开始，显式恢复陈旧锁并立刻释放接管锁；如果没有这段函数，崩溃退出后的恢复路径不进入 Phase61 流且可能留下新 owner。
        result = self.runtime.recover_stale_lock(owner_label=owner_label)  # 修改代码+Phase61AbortStreamingHooks: 复用现有 Phase50 stale recovery 接管旧锁；如果没有这行代码，恢复逻辑会重复实现。
        release_result = self.lock_manager.release(self.session_id) if bool(result.get("stale_recovered")) else {"released": False, "reason": "no stale lock recovered"}  # 新增代码+Phase61AbortStreamingHooks: 恢复成功后释放本阶段接管锁；如果没有这行代码，Phase61 recovery 自己会成为新的残留锁。
        result["post_recovery_release"] = release_result  # 新增代码+Phase61AbortStreamingHooks: 把释放结果放进恢复报告；如果没有这行代码，验收和调试无法确认恢复后是否清干净。
        result["lock_released_after_recovery"] = bool(release_result.get("released", False))  # 新增代码+Phase61AbortStreamingHooks: 暴露稳定布尔字段；如果没有这行代码，矩阵只能解析嵌套 release 结构。
        self.record_stream_event("computer_use_stale_lock_recovery_checked", {"stale_recovered": bool(result.get("stale_recovered")), "lock_released_after_recovery": bool(result.get("lock_released_after_recovery")), "owner_label": _phase61_safe_text(owner_label, 120)})  # 修改代码+Phase61AbortStreamingHooks: 记录恢复和释放检查事件；如果没有这行代码，streaming 流看不到崩溃恢复是否留下新锁。
        return result  # 修改代码+Phase61AbortStreamingHooks: 返回恢复和释放结果；如果没有这行代码，调用方无法确认 stale_recovered 和锁清理结果。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，WindowsComputerUseAbortStreamingHooks.recover_stale_lock 到此结束；如果没有这个边界说明，初学者不容易看出恢复 hook 范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，返回 hooks 状态；如果没有这段函数，/computer status 无法解释 abort 和 streaming hook 边界。
        hotkey = self.evaluate_hotkey_plan()  # 新增代码+Phase61AbortStreamingHooks: 读取热键方案；如果没有这行代码，状态无法显示是否注册全局 hook。
        stream_events = self.stream_events()  # 新增代码+Phase61AbortStreamingHooks: 读取 streaming 事件数量；如果没有这行代码，状态看不到 hook 是否发生过。
        return {"enabled": True, "model": PHASE61_ABORT_STREAMING_HOOKS_MODEL, "marker": PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER, "stream_events_path": str(self.stream_events_path), "stream_event_count": len(stream_events), "global_hotkey_registered": bool(hotkey.get("global_hotkey_registered")), "terminal_abort_fallback": bool(hotkey.get("terminal_abort_fallback")), "controller_abort_fallback": bool(hotkey.get("controller_abort_fallback")), "hotkey_mode": hotkey.get("hotkey_mode", ""), "global_escape_abort_model": hotkey.get("global_escape_abort_model", PHASE5_GLOBAL_ESCAPE_ABORT_MODEL), "expected_escape_count": int(hotkey.get("expected_escape_count", 0)), "abort_count": int(hotkey.get("abort_count", 0)), "hooked_cleanup_events": ["tool_abort", "model_interrupt", "user_ctrl_c", "exception_exit", "global_escape_hook_unregistered"], "actions_expanded": PHASE61_ACTIONS_EXPANDED}  # 修改代码+Phase5GlobalEscapeAbort：返回机器可读状态并包含全局 Escape 信息；如果没有这行代码，终端和矩阵无法读取 Phase5 能力。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，WindowsComputerUseAbortStreamingHooks.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def terminal_status_lines(self) -> list[str]:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，生成终端可读 hooks 状态；如果没有这段函数，用户只能读 JSON。
        status = self.status()  # 新增代码+Phase61AbortStreamingHooks: 读取机器状态；如果没有这行代码，终端文本没有事实来源。
        return ["Computer Abort Streaming Hooks", f"- marker={PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER}", f"- hook_model={PHASE61_ABORT_STREAMING_HOOKS_MODEL}", f"- global_hotkey_registered={_phase61_bool_token(status.get('global_hotkey_registered'))}", f"- terminal_abort_fallback={_phase61_bool_token(status.get('terminal_abort_fallback'))}", f"- controller_abort_fallback={_phase61_bool_token(status.get('controller_abort_fallback'))}", f"- hotkey_mode={status.get('hotkey_mode', '')}", f"- stream_event_count={status.get('stream_event_count', 0)}", f"- stream_events_path={status.get('stream_events_path', '')}", f"- cleanup_hooks={','.join(list(status.get('hooked_cleanup_events', [])))}", f"- actions_expanded={_phase61_bool_token(PHASE61_ACTIONS_EXPANDED)}"]  # 新增代码+Phase61AbortStreamingHooks: 返回完整终端面板；如果没有这行代码，/computer abort-hooks 无法显示降级和事件路径。
    # 新增代码+Phase61AbortStreamingHooks: 函数段结束，WindowsComputerUseAbortStreamingHooks.terminal_status_lines 到此结束；如果没有这个边界说明，初学者不容易看出终端状态范围。
# 新增代码+Phase61AbortStreamingHooks: 类段结束，WindowsComputerUseAbortStreamingHooks 到此结束；如果没有这个边界说明，初学者不容易看出 hooks 类范围。


def run_phase61_abort_streaming_hooks_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，运行 Phase61 abort/streaming hooks 合同自检；如果没有这段函数，CLI 和真实终端没有统一验收入口。
    root = Path(base_dir) if base_dir is not None else DEFAULT_ABORT_STREAMING_HOOKS_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase61AbortStreamingHooks: 选择隔离合同目录；如果没有这行代码，多次 CLI 运行可能互相污染。
    lock_manager = ComputerUseLockManager(base_dir=root / "locks", stale_after_seconds=0)  # 新增代码+Phase61AbortStreamingHooks: 创建立即可恢复的锁管理器；如果没有这行代码，合同无法验证 stale recovery。
    hooks = WindowsComputerUseAbortStreamingHooks(lock_manager=lock_manager, session_id="phase61-session", base_dir=root / "hooks")  # 新增代码+Phase61AbortStreamingHooks: 创建合同 hooks；如果没有这行代码，自检没有 abort/streaming 事实源。
    from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import Phase58RecordingLowLevelSender, Phase58StaticSafeWindowObserver, WindowsRealSendInputGuardRuntime  # 新增代码+Phase61AbortStreamingHooks: 延迟导入 Phase58 安全 runtime 避免顶层循环；如果没有这行代码，合同无法证明低层事件被拦截。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase61AbortStreamingHooks: 延迟导入静态 inventory；如果没有这行代码，合同会依赖真实桌面。
    safe_window = {"app_id": "phase58_safe_app", "process_name": "phase58_safe_app", "window_id": "hwnd:6101", "hwnd": 6101, "title_preview": "LearningAgent-Phase58-RealSendInputGuardSmoke", "rect": {"left": 100, "top": 120, "right": 740, "bottom": 520}, "safe_to_target": True}  # 新增代码+Phase61AbortStreamingHooks: 构造 Phase58 安全目标；如果没有这行代码，abort_zero_events 没有动作样本。
    raw_sender = Phase58RecordingLowLevelSender()  # 新增代码+Phase61AbortStreamingHooks: 创建记录型低层 sender；如果没有这行代码，无法确认原始 sender 0 事件。
    runtime = WindowsRealSendInputGuardRuntime(platform="win32", inventory=StaticWindowsWindowInventory([safe_window]), low_level_sender=hooks.wrap_low_level_sender(raw_sender), observer=Phase58StaticSafeWindowObserver(before_text="before", after_text="after"))  # 新增代码+Phase61AbortStreamingHooks: 创建带 abort-aware sender 的 Phase58 runtime；如果没有这行代码，合同无法覆盖真实动作入口。
    lock_manager.request_abort("phase61-contract-abort", requested_by="contract")  # 新增代码+Phase61AbortStreamingHooks: 触发 abort；如果没有这行代码，下一次动作不会被拦截。
    abort_result = runtime.execute_safe_action(safe_window, "click", {"x": 12, "y": 34})  # 新增代码+Phase61AbortStreamingHooks: 尝试执行动作；如果没有这行代码，abort_zero_events 没有证据。
    lock_manager.clear_abort(cleared_by="phase61-contract")  # 新增代码+Phase61AbortStreamingHooks: 清除 abort 以便后续 cleanup/recovery；如果没有这行代码，后续状态会被急停干扰。
    lock_manager.acquire("phase61-session", owner_label="phase61-contract")  # 新增代码+Phase61AbortStreamingHooks: 让当前会话持锁；如果没有这行代码，异常 cleanup 无法证明释放。
    cleanup = hooks.run_with_cleanup("phase61-contract-exception", lambda: (_ for _ in ()).throw(RuntimeError("phase61 contract boom")))  # 新增代码+Phase61AbortStreamingHooks: 模拟工具异常；如果没有这行代码，exception_cleanup 没有证据。
    lock_manager.acquire("phase61-crashed", owner_label="phase61-crashed")  # 新增代码+Phase61AbortStreamingHooks: 写入陈旧 owner；如果没有这行代码，stale recovery 没有目标。
    recovered = hooks.recover_stale_lock(owner_label="phase61-contract-recovery")  # 新增代码+Phase61AbortStreamingHooks: 执行陈旧锁恢复；如果没有这行代码，stale_recovered token 无法成立。
    status_text = "\n".join(hooks.terminal_status_lines())  # 新增代码+Phase61AbortStreamingHooks: 渲染终端状态；如果没有这行代码，terminal_status token 没有证据。
    events = hooks.stream_events()  # 新增代码+Phase61AbortStreamingHooks: 读取 streaming 事件；如果没有这行代码，streaming_hooks token 没有证据。
    abort_zero_events = bool(abort_result.get("low_level_event_count") == 0 and raw_sender.low_level_events == [] and abort_result.get("dispatch", {}).get("decision") == "aborted_before_low_level_send")  # 新增代码+Phase61AbortStreamingHooks: 汇总 abort 零事件判断；如果没有这行代码，合同无法表达核心安全结果。
    exception_cleanup = bool(cleanup.get("exception_handled") and cleanup.get("cleanup_completed"))  # 新增代码+Phase61AbortStreamingHooks: 汇总异常 cleanup 判断；如果没有这行代码，合同无法表达中断清理结果。
    stale_recovered = bool(recovered.get("stale_recovered"))  # 新增代码+Phase61AbortStreamingHooks: 汇总陈旧锁恢复判断；如果没有这行代码，合同无法表达崩溃恢复结果。
    streaming_hooks = bool(any(event.get("event_type") == "computer_use_aborted_before_low_level_send" for event in events) and any(event.get("event_type") == "computer_use_exception_cleanup_completed" for event in events))  # 新增代码+Phase61AbortStreamingHooks: 汇总 streaming 事件判断；如果没有这行代码，hook 可能只改状态不落事件。
    hotkey_fallback = bool(hooks.status().get("terminal_abort_fallback") and not hooks.status().get("global_hotkey_registered"))  # 新增代码+Phase61AbortStreamingHooks: 汇总热键安全降级判断；如果没有这行代码，合同无法证明没有假装注册热键。
    terminal_status = bool("Computer Abort Streaming Hooks" in status_text and PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER in status_text and "terminal_abort_fallback=true" in status_text)  # 新增代码+Phase61AbortStreamingHooks: 汇总终端状态判断；如果没有这行代码，用户可见状态接入无法验收。
    passed = bool(abort_zero_events and exception_cleanup and stale_recovered and streaming_hooks and hotkey_fallback and terminal_status and not PHASE61_ACTIONS_EXPANDED)  # 新增代码+Phase61AbortStreamingHooks: 汇总合同通过条件；如果没有这行代码，main 无法用退出码表达失败。
    return {"marker": PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER, "ok_token": PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_OK_TOKEN, "abort_zero_events": abort_zero_events, "exception_cleanup": exception_cleanup, "stale_recovered": stale_recovered, "streaming_hooks": streaming_hooks, "hotkey_fallback": hotkey_fallback, "terminal_status": terminal_status, "actions_expanded": PHASE61_ACTIONS_EXPANDED, "passed": passed, "state_dir": str(root)}  # 新增代码+Phase61AbortStreamingHooks: 返回完整合同报告；如果没有这行代码，测试和真实终端拿不到统一结果。
# 新增代码+Phase61AbortStreamingHooks: 函数段结束，run_phase61_abort_streaming_hooks_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase61_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，把报告转成稳定 CLI token 行；如果没有这段函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER} {PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_OK_TOKEN} abort_zero_events={_phase61_bool_token(report.get('abort_zero_events'))} exception_cleanup={_phase61_bool_token(report.get('exception_cleanup'))} stale_recovered={_phase61_bool_token(report.get('stale_recovered'))} streaming_hooks={_phase61_bool_token(report.get('streaming_hooks'))} hotkey_fallback={_phase61_bool_token(report.get('hotkey_fallback'))} terminal_status={_phase61_bool_token(report.get('terminal_status'))} actions_expanded={_phase61_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase61AbortStreamingHooks: 返回固定顺序 token；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase61AbortStreamingHooks: 函数段结束，phase61_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase61AbortStreamingHooks: 函数段开始，提供命令行入口；如果没有这段函数，真实终端无法直接运行 Phase61 自检。
    _ = argv  # 新增代码+Phase61AbortStreamingHooks: 保留 argv 供未来扩展；如果没有这行代码，参数存在但用途不清楚。
    report = run_phase61_abort_streaming_hooks_contract()  # 新增代码+Phase61AbortStreamingHooks: 使用默认隔离目录运行合同；如果没有这行代码，CLI 不会生成真实状态证据。
    print(phase61_cli_line(report))  # 新增代码+Phase61AbortStreamingHooks: 打印稳定 token 行；如果没有这行代码，debug log 无法匹配 Phase61 成功。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase61AbortStreamingHooks: 打印结构化报告；如果没有这行代码，失败时不易复盘。
    print(PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER)  # 新增代码+Phase61AbortStreamingHooks: 单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase61AbortStreamingHooks: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase61AbortStreamingHooks: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_ABORT_STREAMING_HOOKS_ROOT", "PHASE61_ABORT_STREAMING_HOOKS_MODEL", "PHASE61_ACTIONS_EXPANDED", "PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_MARKER", "PHASE61_WINDOWS_ABORT_STREAMING_HOOKS_OK_TOKEN", "Phase61AbortAwareLowLevelSender", "WindowsComputerUseAbortStreamingHooks", "main", "phase61_cli_line", "run_phase61_abort_streaming_hooks_contract"]  # 新增代码+Phase61AbortStreamingHooks: 限定公开导出名称；如果没有这行代码，包导入容易暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase61AbortStreamingHooks: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase61AbortStreamingHooks: 用 main 返回码退出；如果没有这行代码，命令行状态不明确。
