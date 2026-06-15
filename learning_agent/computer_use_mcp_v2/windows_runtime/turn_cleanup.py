"""Turn-end cleanup lifecycle for Windows Computer Use host windows."""  # 新增代码+Phase4TurnCleanup：说明本文件负责一轮 Computer Use 后的 host unhide 和状态清理；如果没有这一行，读者不知道 cleanup 生命周期集中在哪里。
from __future__ import annotations  # 新增代码+Phase4TurnCleanup：启用延迟类型解析；如果没有这一行，类型注解在旧解释顺序下更容易失败。

from typing import Any, Callable  # 新增代码+Phase4TurnCleanup：导入通用类型和回调类型；如果没有这一行，manager 接口边界不清楚。

try:  # 新增代码+Phase4TurnCleanup：优先使用包路径导入 session store 和 lock manager；如果没有这一段，单元测试和模块运行会重复写导入逻辑。
    from learning_agent.computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager  # 新增代码+Phase4TurnCleanup：导入 durable lock 管理器；如果没有这一行，turn cleanup 无法释放桌面锁或清 abort。
    from learning_agent.computer_use_mcp_v2.windows_runtime.session_context import ComputerUseSessionContextStore  # 新增代码+Phase4TurnCleanup：导入统一 session context store；如果没有这一行，host hidden 状态无法持久化。
except ModuleNotFoundError as error:  # 新增代码+Phase4TurnCleanup：兼容 start_oauth_agent.bat 的脚本模式；如果没有这一段，真实终端入口可能因包路径不同失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime"}:  # 新增代码+Phase4TurnCleanup：只对包根缺失做兜底；如果没有这一行，真实依赖错误会被误吞。
        raise  # 新增代码+Phase4TurnCleanup：重新抛出非路径类导入错误；如果没有这一行，内部 bug 会被隐藏。
    from computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager  # type: ignore  # 新增代码+Phase4TurnCleanup：脚本模式导入同一 lock manager；如果没有这一行，bat 入口无法清理锁。
    from computer_use_mcp_v2.windows_runtime.session_context import ComputerUseSessionContextStore  # type: ignore  # 新增代码+Phase4TurnCleanup：脚本模式导入同一 session store；如果没有这一行，bat 入口无法清理 host 状态。

PHASE4_TURN_CLEANUP_MODEL = "phase4_host_hide_cleanup_unhide"  # 新增代码+Phase4TurnCleanup：定义 Phase4 cleanup 模型名；如果没有这一行，报告无法说明 cleanup 规则版本。


def _phase4_bool(value: Any) -> bool:  # 新增代码+Phase4TurnCleanup：函数段开始，把外部值规范成布尔；如果没有这段函数，字符串/空值会让报告漂移。
    return bool(value)  # 新增代码+Phase4TurnCleanup：返回 Python 布尔值；如果没有这一行，调用方拿不到稳定判断。
# 新增代码+Phase4TurnCleanup：函数段结束，_phase4_bool 到此结束；如果没有这个边界说明，用户不容易看出布尔规范范围。


def _phase4_list_of_dicts(value: Any) -> list[dict[str, Any]]:  # 新增代码+Phase4TurnCleanup：函数段开始，规范化 host window 列表；如果没有这段函数，坏窗口项会污染 cleanup。
    return [dict(item) for item in list(value or []) if isinstance(item, dict)] if isinstance(value, list) else []  # 新增代码+Phase4TurnCleanup：只保留 dict 窗口并复制；如果没有这一行，字符串或坏对象会让 unhide 崩溃。
# 新增代码+Phase4TurnCleanup：函数段结束，_phase4_list_of_dicts 到此结束；如果没有这个边界说明，用户不容易看出窗口列表清理范围。


def _phase4_call_backend_method(backend: Any, method_name: str, fallback: dict[str, Any], *args: Any) -> dict[str, Any]:  # 新增代码+Phase4TurnCleanup：函数段开始，安全调用可注入 host backend 方法；如果没有这段函数，测试 fake 和真实后端错误处理会重复。
    method = getattr(backend, method_name, None) if backend is not None else None  # 新增代码+Phase4TurnCleanup：读取后端方法；如果没有这一行，没有后端时会直接报错。
    if not callable(method):  # 新增代码+Phase4TurnCleanup：检查方法是否可调用；如果没有这一行，缺方法后端会触发 TypeError。
        return dict(fallback)  # 新增代码+Phase4TurnCleanup：没有方法时返回兜底报告；如果没有这一行，纯状态测试无法运行。
    result = method(*args)  # 新增代码+Phase4TurnCleanup：调用后端方法；如果没有这一行，hide/unhide/release_transient_inputs 不会真正执行。
    return dict(result or {}) if isinstance(result, dict) else dict(fallback)  # 新增代码+Phase4TurnCleanup：规范化返回值；如果没有这一行，坏后端返回会污染 cleanup 报告。
# 新增代码+Phase4TurnCleanup：函数段结束，_phase4_call_backend_method 到此结束；如果没有这个边界说明，用户不容易看出后端调用范围。


def record_hidden_host_windows(store: ComputerUseSessionContextStore, session_id: Any, host_windows: Any, host_backend: Any = None) -> dict[str, Any]:  # 新增代码+Phase4TurnCleanup：函数段开始，隐藏并记录宿主窗口；如果没有这段函数，cleanup 不知道一轮开始时隐藏了哪些窗口。
    windows = _phase4_list_of_dicts(host_windows)  # 新增代码+Phase4TurnCleanup：规范化待隐藏 host 窗口；如果没有这一行，坏输入会落入 context。
    hide_report = _phase4_call_backend_method(host_backend, "hide_host_windows", {"host_windows_hidden": bool(windows), "hidden_window_count": len(windows)}, windows)  # 新增代码+Phase4TurnCleanup：调用可注入隐藏后端；如果没有这一行，真实宿主窗口不会被隐藏或测试无法观察调用。
    hidden = bool(hide_report.get("host_windows_hidden", bool(windows)))  # 新增代码+Phase4TurnCleanup：规范化隐藏结果；如果没有这一行，后端返回字段差异会导致状态不稳定。
    context = store.bind_context(session_id, hidden_windows=windows, host_windows_hidden=hidden)  # 新增代码+Phase4TurnCleanup：把隐藏窗口写入 session context；如果没有这一行，异常 cleanup 找不到 unhide 目标。
    return {"host_windows_hidden": hidden, "hidden_window_count": len(windows), "hidden_windows": windows, "hide_report": hide_report, "context": context, "cleanup_model": PHASE4_TURN_CLEANUP_MODEL}  # 新增代码+Phase4TurnCleanup：返回隐藏摘要；如果没有这一行，调用方无法审计 hide 阶段。
# 新增代码+Phase4TurnCleanup：函数段结束，record_hidden_host_windows 到此结束；如果没有这个边界说明，用户不容易看出 host hide 记录范围。


def run_turn_cleanup(store: ComputerUseSessionContextStore, session_id: Any, *, host_backend: Any = None, lock_manager: ComputerUseLockManager | None = None, escape_controller: Any = None, reason: str = "turn cleanup") -> dict[str, Any]:  # 修改代码+Phase5GlobalEscapeAbort：函数段开始，执行一轮结束清理并可注销全局 Escape hook；如果没有这段函数，成功/失败/abort/异常路径会各自写散乱清理代码且可能残留按键监听。
    context_before = store.snapshot(session_id)  # 新增代码+Phase4TurnCleanup：读取 cleanup 前 context；如果没有这一行，函数不知道是否有隐藏宿主窗口。
    hidden_windows = _phase4_list_of_dicts(context_before.get("hidden_windows", []))  # 新增代码+Phase4TurnCleanup：读取待恢复 host 窗口；如果没有这一行，unhide 没有目标。
    was_already_clean = bool(context_before.get("cleanup_completed") and not hidden_windows and not context_before.get("host_windows_hidden"))  # 新增代码+Phase4TurnCleanup：判断是否已清理过；如果没有这一行，重复 cleanup 会反复恢复同一 host。
    transient_report = _phase4_call_backend_method(host_backend, "release_transient_inputs", {"transient_inputs_released": True})  # 新增代码+Phase4TurnCleanup：释放按键/鼠标等临时状态；如果没有这一行，异常退出后可能留下卡住的输入状态。
    escape_cleanup = {"escape_hook_unregistered": True, "global_hotkey_registered": False, "reason": "escape_controller_not_provided"}  # 新增代码+Phase5GlobalEscapeAbort：预置 Escape hook 清理报告；如果没有这一行，无控制器场景会缺少稳定字段。
    if escape_controller is not None:  # 新增代码+Phase5GlobalEscapeAbort：只在传入控制器时注销热键；如果没有这一行，普通 cleanup 会尝试调用不存在的 hook 对象。
        escape_cleanup = _phase4_call_backend_method(escape_controller, "cleanup", {"escape_hook_unregistered": False, "global_hotkey_registered": True, "reason": "escape_cleanup_method_missing"})  # 新增代码+Phase5GlobalEscapeAbort：调用控制器 cleanup 注销热键；如果没有这一行，全局 Escape hook 可能在轮次结束后残留。
    if hidden_windows:  # 新增代码+Phase4TurnCleanup：只有存在隐藏窗口时才执行 unhide；如果没有这一行，幂等 cleanup 会重复触碰窗口。
        unhide_report = _phase4_call_backend_method(host_backend, "unhide_host_windows", {"host_windows_restored": True, "unhidden_window_count": len(hidden_windows)}, hidden_windows)  # 新增代码+Phase4TurnCleanup：调用可注入恢复后端；如果没有这一行，宿主窗口可能一直隐藏。
    else:  # 新增代码+Phase4TurnCleanup：没有隐藏窗口时走幂等兜底；如果没有这一行，后续 unhide_report 可能未定义。
        unhide_report = {"host_windows_restored": True, "unhidden_window_count": 0, "idempotent": was_already_clean}  # 新增代码+Phase4TurnCleanup：返回无需恢复但成功的报告；如果没有这一行，第二次 cleanup 会被误判失败。
    lock_release = {"released": False, "reason": "lock_manager_not_provided"}  # 新增代码+Phase4TurnCleanup：预置锁释放报告；如果没有这一行，没有 lock manager 时返回字段不稳定。
    abort_clear = {"abort_requested": False, "reason": "lock_manager_not_provided"}  # 新增代码+Phase4TurnCleanup：预置 abort 清理报告；如果没有这一行，没有 lock manager 时返回字段不稳定。
    abort_was_requested = False  # 新增代码+Phase4TurnCleanup：预置 abort 前状态；如果没有这一行，后续 abort_cleared 可能引用未定义。
    if lock_manager is not None:  # 新增代码+Phase4TurnCleanup：只有传入 lock manager 才释放锁和清 abort；如果没有这一行，无 lock 场景会报错。
        abort_was_requested = bool(lock_manager.status().get("abort_requested", False))  # 新增代码+Phase4TurnCleanup：读取 cleanup 前急停状态；如果没有这一行，无法证明 abort 被清除。
        lock_release = lock_manager.release(str(session_id or ""))  # 新增代码+Phase4TurnCleanup：释放当前 session 的桌面锁；如果没有这一行，下一轮可能被旧 owner 卡住。
        abort_clear = lock_manager.clear_abort(cleared_by=f"turn-cleanup:{session_id}") if abort_was_requested else lock_manager.status()  # 新增代码+Phase4TurnCleanup：清除旧 abort 或读取状态；如果没有这一行，急停可能永久残留。
    host_windows_restored = bool(unhide_report.get("host_windows_restored", True))  # 新增代码+Phase4TurnCleanup：规范化 host 恢复结果；如果没有这一行，cleanup_completed 无法判断窗口恢复。
    transient_released = bool(transient_report.get("transient_inputs_released", True))  # 新增代码+Phase4TurnCleanup：规范化临时输入释放结果；如果没有这一行，cleanup_completed 无法判断输入状态释放。
    lock_released = bool(lock_release.get("released", False)) if lock_manager is not None else False  # 新增代码+Phase4TurnCleanup：规范化锁释放结果；如果没有这一行，报告字段可能是字符串或缺失。
    abort_cleared = bool(not abort_was_requested or not abort_clear.get("abort_requested", False))  # 新增代码+Phase4TurnCleanup：规范化 abort 是否已清除；如果没有这一行，abort 路径缺少验收事实。
    escape_hook_unregistered = bool(escape_cleanup.get("escape_hook_unregistered", escape_cleanup.get("unregistered", True)))  # 新增代码+Phase5GlobalEscapeAbort：规范化 Escape hook 是否已注销；如果没有这一行，cleanup_completed 无法覆盖全局热键生命周期。
    cleanup_completed = bool(host_windows_restored and transient_released and abort_cleared and escape_hook_unregistered)  # 修改代码+Phase5GlobalEscapeAbort：汇总 cleanup 是否完成并包含 Escape hook 注销；如果没有这一行，调用方只能自己解读多个子报告且可能漏掉 hook 残留。
    context_after = store.update_app_state(session_id, hidden_windows=[], host_windows_hidden=False, last_action={"action": "turn_cleanup", "reason": str(reason or ""), "cleanup_model": PHASE4_TURN_CLEANUP_MODEL}, cleanup_completed=cleanup_completed, cleanup_reason=str(reason or ""))  # 新增代码+Phase4TurnCleanup：把 cleanup 后状态归零并落盘；如果没有这一行，后续状态仍会显示宿主窗口隐藏。
    return {"cleanup_completed": cleanup_completed, "idempotent": was_already_clean, "session_id": context_after["session_id"], "reason": str(reason or ""), "host_windows_restored": host_windows_restored, "unhide_report": unhide_report, "transient_inputs_released": transient_released, "transient_report": transient_report, "escape_hook_unregistered": escape_hook_unregistered, "escape_cleanup": escape_cleanup, "lock_released": lock_released, "release": lock_release, "abort_cleared": abort_cleared, "abort_clear": abort_clear, "context": context_after, "cleanup_model": PHASE4_TURN_CLEANUP_MODEL}  # 修改代码+Phase5GlobalEscapeAbort：返回完整清理报告并暴露 Escape hook 清理证据；如果没有这一行，测试和真实终端无法统一检查 cleanup。
# 新增代码+Phase4TurnCleanup：函数段结束，run_turn_cleanup 到此结束；如果没有这个边界说明，用户不容易看出 turn cleanup 范围。


class ComputerUseTurnCleanupManager:  # 新增代码+Phase4TurnCleanup：类段开始，组合回调执行和 finally cleanup；如果没有这个类，调用方要手写 try/except/cleanup。
    def __init__(self, store: ComputerUseSessionContextStore | None = None, session_id: Any = "learning-agent-default-session", host_backend: Any = None, lock_manager: ComputerUseLockManager | None = None, escape_controller: Any = None) -> None:  # 修改代码+Phase5GlobalEscapeAbort：函数段开始，保存 cleanup 所需依赖并可接入 Escape 控制器；如果没有这段函数，manager 无法复用同一 session、后端和热键清理对象。
        self.store = store if store is not None else ComputerUseSessionContextStore()  # 新增代码+Phase4TurnCleanup：保存或创建 session store；如果没有这一行，manager 没有统一事实源。
        self.session_id = session_id  # 新增代码+Phase4TurnCleanup：保存当前 session id；如果没有这一行，cleanup 不知道清理哪一轮。
        self.host_backend = host_backend  # 新增代码+Phase4TurnCleanup：保存可注入 host backend；如果没有这一行，manager 无法隐藏/恢复宿主窗口。
        self.lock_manager = lock_manager  # 新增代码+Phase4TurnCleanup：保存可注入 lock manager；如果没有这一行，manager 无法释放锁或清 abort。
        self.escape_controller = escape_controller  # 新增代码+Phase5GlobalEscapeAbort：保存可注入全局 Escape 控制器；如果没有这一行，manager 无法在 finally cleanup 中注销热键。
    # 新增代码+Phase4TurnCleanup：函数段结束，ComputerUseTurnCleanupManager.__init__ 到此结束；如果没有这个边界说明，用户不容易看出依赖初始化范围。

    def run_with_cleanup(self, callback: Callable[[], Any], reason: str = "turn cleanup") -> dict[str, Any]:  # 新增代码+Phase4TurnCleanup：函数段开始，执行回调并确保 cleanup；如果没有这段函数，成功/失败/异常路径很容易漏掉 unhide。
        callback_result: Any = None  # 新增代码+Phase4TurnCleanup：预置回调结果；如果没有这一行，异常路径返回时变量可能不存在。
        exception_payload: dict[str, Any] = {}  # 新增代码+Phase4TurnCleanup：预置异常摘要；如果没有这一行，非异常路径字段不稳定。
        try:  # 新增代码+Phase4TurnCleanup：进入受保护执行区；如果没有这一行，异常会直接跳过 cleanup。
            callback_result = callback()  # 新增代码+Phase4TurnCleanup：执行调用方回调；如果没有这一行，manager 只会清理不会执行业务动作。
        except BaseException as error:  # 新增代码+Phase4TurnCleanup：捕获异常和中断以保证 cleanup；如果没有这一行，异常退出时 host 可能一直隐藏。
            exception_payload = {"exception_handled": True, "exception_type": type(error).__name__, "message": str(error)}  # 新增代码+Phase4TurnCleanup：记录异常摘要但不泄露堆栈；如果没有这一行，调用方不知道发生了什么异常。
        cleanup = run_turn_cleanup(self.store, self.session_id, host_backend=self.host_backend, lock_manager=self.lock_manager, escape_controller=self.escape_controller, reason=reason)  # 修改代码+Phase5GlobalEscapeAbort：无论回调结果如何都执行 cleanup 并注销 Escape hook；如果没有这一行，Phase4 的核心保证和 Phase5 热键释放都不存在。
        return {"callback_result": callback_result, "cleanup": cleanup, "cleanup_completed": bool(cleanup.get("cleanup_completed")), **exception_payload, "cleanup_model": PHASE4_TURN_CLEANUP_MODEL}  # 新增代码+Phase4TurnCleanup：返回回调结果、cleanup 和异常摘要；如果没有这一行，测试和终端无法统一判断四种路径。
    # 新增代码+Phase4TurnCleanup：函数段结束，ComputerUseTurnCleanupManager.run_with_cleanup 到此结束；如果没有这个边界说明，用户不容易看出 finally cleanup 范围。
# 新增代码+Phase4TurnCleanup：类段结束，ComputerUseTurnCleanupManager 到此结束；如果没有这个边界说明，用户不容易看出 manager 范围。


__all__ = ["PHASE4_TURN_CLEANUP_MODEL", "ComputerUseTurnCleanupManager", "record_hidden_host_windows", "run_turn_cleanup"]  # 新增代码+Phase4TurnCleanup：导出 Phase4 稳定 API；如果没有这一行，测试和后续生产控制层不知道哪些入口可用。
