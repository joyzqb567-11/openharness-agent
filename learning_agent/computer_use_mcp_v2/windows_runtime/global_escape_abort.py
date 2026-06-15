"""Global Escape abort controller for Windows Computer Use."""  # 新增代码+Phase5GlobalEscapeAbort：说明本文件负责全局 Escape 急停控制；如果没有这一行，读者不容易知道这个模块和普通 abort fallback 的区别。
from __future__ import annotations  # 新增代码+Phase5GlobalEscapeAbort：启用延迟类型解析；如果没有这一行，类型注解在旧导入顺序下更容易出错。
from typing import Any, Callable  # 新增代码+Phase5GlobalEscapeAbort：导入通用值和回调类型；如果没有这一行，热键后端和控制器接口边界不清楚。
try:  # 新增代码+Phase5GlobalEscapeAbort：优先按包路径导入锁管理器；如果没有这一段，单元测试和生产模块会重复写导入兼容逻辑。
    from learning_agent.computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager  # 新增代码+Phase5GlobalEscapeAbort：导入 durable abort 事实源；如果没有这一行，用户按 Escape 后只能停在内存里。
except ModuleNotFoundError as error:  # 新增代码+Phase5GlobalEscapeAbort：兼容 start_oauth_agent.bat 直接脚本运行模式；如果没有这一段，真实终端入口可能因包前缀不同失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.lock"}:  # 新增代码+Phase5GlobalEscapeAbort：只对包路径缺失兜底；如果没有这一行，真实内部依赖错误会被误吞。
        raise  # 新增代码+Phase5GlobalEscapeAbort：重新抛出非路径类导入错误；如果没有这一行，底层 bug 会变得难以定位。
    from computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager  # type: ignore  # 新增代码+Phase5GlobalEscapeAbort：脚本模式导入锁管理器；如果没有这一行，bat 入口无法写入 abort flag。
PHASE5_GLOBAL_ESCAPE_ABORT_MODEL = "phase5_global_escape_abort"  # 新增代码+Phase5GlobalEscapeAbort：定义 Phase5 能力模型名；如果没有这一行，状态面板和矩阵无法区分全局 Escape 急停版本。
PHASE5_GLOBAL_ESCAPE_ABORT_MARKER = "PHASE5_GLOBAL_ESCAPE_ABORT_READY"  # 新增代码+Phase5GlobalEscapeAbort：定义稳定 marker；如果没有这一行，终端和测试不容易定位 Phase5 输出。


def _phase5_positive_count(value: Any) -> int:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，把外部 count 规整为正整数；如果没有这段函数，坏输入可能让期望 Escape 计数变成负数。
    try:  # 新增代码+Phase5GlobalEscapeAbort：尝试把输入转成整数；如果没有这一行，字符串数字无法作为 count 使用。
        return max(0, int(value))  # 新增代码+Phase5GlobalEscapeAbort：返回非负整数；如果没有这一行，负数会破坏“下一次 Escape 是计划内”的语义。
    except (TypeError, ValueError):  # 新增代码+Phase5GlobalEscapeAbort：捕获空值或非数字；如果没有这一行，坏参数会让热键控制器崩溃。
        return 0  # 新增代码+Phase5GlobalEscapeAbort：坏输入视为 0；如果没有这一行，调用方无法安全传入可选 count。
# 新增代码+Phase5GlobalEscapeAbort：函数段结束，_phase5_positive_count 到此结束；如果没有这个边界说明，初学者不容易看出计数规范化范围。


def _phase5_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，把任意返回值规整成字典；如果没有这段函数，后端返回 None 会污染报告结构。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase5GlobalEscapeAbort：只有字典才复制返回；如果没有这一行，字符串或列表可能让报告字段崩溃。
# 新增代码+Phase5GlobalEscapeAbort：函数段结束，_phase5_dict 到此结束；如果没有这个边界说明，初学者不容易看出后端返回值清洗范围。


class Phase5InMemoryEscHotkeyBackend:  # 新增代码+Phase5GlobalEscapeAbort：类段开始，提供无副作用的内存热键后端；如果没有这个类，测试会被迫注册真实 Windows 全局热键。
    def __init__(self) -> None:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，初始化内存热键状态；如果没有这段函数，后端没有地方保存 handler 和计数。
        self.handler: Callable[..., dict[str, Any]] | None = None  # 新增代码+Phase5GlobalEscapeAbort：保存 Escape 回调；如果没有这一行，trigger_escape 无法模拟用户按键。
        self.token: str = ""  # 新增代码+Phase5GlobalEscapeAbort：保存注册 token；如果没有这一行，注销时无法确认注销的是哪次注册。
        self.register_count = 0  # 新增代码+Phase5GlobalEscapeAbort：记录注册次数；如果没有这一行，测试无法发现重复注册或漏注册。
        self.unregister_count = 0  # 新增代码+Phase5GlobalEscapeAbort：记录注销次数；如果没有这一行，cleanup 是否真的释放 hook 无法被验证。
        self.triggered_events: list[dict[str, Any]] = []  # 新增代码+Phase5GlobalEscapeAbort：保存触发历史；如果没有这一行，调试时无法复盘 Escape 如何被处理。
    # 新增代码+Phase5GlobalEscapeAbort：函数段结束，Phase5InMemoryEscHotkeyBackend.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出后端状态范围。
    def registerEscHotkey(self, handler: Callable[..., dict[str, Any]]) -> str:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，模拟注册 Escape 全局热键；如果没有这段函数，顶层矩阵无法看到 ClaudeCode 风格热键注册入口。
        self.register_count += 1  # 新增代码+Phase5GlobalEscapeAbort：累计注册次数；如果没有这一行，重复注册问题无法被观察。
        self.handler = handler  # 新增代码+Phase5GlobalEscapeAbort：保存回调；如果没有这一行，后续 Escape 无法进入控制器。
        self.token = f"phase5-esc-hotkey-{self.register_count}"  # 新增代码+Phase5GlobalEscapeAbort：生成稳定 token；如果没有这一行，注销调用无法引用注册记录。
        return self.token  # 新增代码+Phase5GlobalEscapeAbort：返回 token；如果没有这一行，控制器不知道注册是否成功。
    # 新增代码+Phase5GlobalEscapeAbort：函数段结束，Phase5InMemoryEscHotkeyBackend.registerEscHotkey 到此结束；如果没有这个边界说明，初学者不容易看出注册范围。
    def unregisterEscHotkey(self, token: Any) -> dict[str, Any]:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，模拟注销 Escape 全局热键；如果没有这段函数，cleanup 无法释放热键后端。
        was_registered = bool(self.handler is not None and self.token and str(token or "") == self.token)  # 新增代码+Phase5GlobalEscapeAbort：确认当前 token 是否匹配；如果没有这一行，错误 token 也会清掉真实注册。
        if was_registered:  # 新增代码+Phase5GlobalEscapeAbort：只在确实注册时清理；如果没有这一行，幂等 cleanup 会错误修改计数。
            self.unregister_count += 1  # 新增代码+Phase5GlobalEscapeAbort：累计真实注销次数；如果没有这一行，测试无法确认 cleanup 只注销一次。
            self.handler = None  # 新增代码+Phase5GlobalEscapeAbort：清空回调；如果没有这一行，注销后 Escape 仍会触发 abort。
            self.token = ""  # 新增代码+Phase5GlobalEscapeAbort：清空 token；如果没有这一行，旧 token 可能被重复使用。
        return {"unregistered": was_registered, "token": str(token or ""), "global_hotkey_registered": bool(self.handler is not None), "model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL}  # 新增代码+Phase5GlobalEscapeAbort：返回注销报告；如果没有这一行，cleanup 无法判断 hook 是否已释放。
    # 新增代码+Phase5GlobalEscapeAbort：函数段结束，Phase5InMemoryEscHotkeyBackend.unregisterEscHotkey 到此结束；如果没有这个边界说明，初学者不容易看出注销范围。
    def trigger_escape(self, source: str = "keyboard") -> dict[str, Any]:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，模拟一次 Escape 触发；如果没有这段函数，测试无法无副作用验证全局热键语义。
        if not callable(self.handler):  # 新增代码+Phase5GlobalEscapeAbort：先确认 handler 是否存在；如果没有这一行，未注册时触发 Escape 会抛异常。
            return {"abort_requested": False, "expected_escape_consumed": False, "reason": "escape_hotkey_not_registered", "source": str(source or ""), "model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL}  # 新增代码+Phase5GlobalEscapeAbort：返回未注册报告；如果没有这一行，测试无法区分未注册和未取消。
        event = _phase5_dict(self.handler(source=source))  # 新增代码+Phase5GlobalEscapeAbort：调用控制器回调并规范化；如果没有这一行，Escape 不会进入分流逻辑。
        self.triggered_events.append(event)  # 新增代码+Phase5GlobalEscapeAbort：记录触发结果；如果没有这一行，调试时无法复盘处理历史。
        return event  # 新增代码+Phase5GlobalEscapeAbort：返回控制器事件；如果没有这一行，测试拿不到 abort 结果。
    # 新增代码+Phase5GlobalEscapeAbort：函数段结束，Phase5InMemoryEscHotkeyBackend.trigger_escape 到此结束；如果没有这个边界说明，初学者不容易看出模拟触发范围。
# 新增代码+Phase5GlobalEscapeAbort：类段结束，Phase5InMemoryEscHotkeyBackend 到此结束；如果没有这个边界说明，初学者不容易看出内存后端范围。


def registerEscHotkey(backend: Any, handler: Callable[..., dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，注册 Escape 热键的统一入口；如果没有这段函数，矩阵无法确认不是普通 abort fallback。
    method = getattr(backend, "registerEscHotkey", None) if backend is not None else None  # 新增代码+Phase5GlobalEscapeAbort：读取后端注册方法；如果没有这一行，缺后端时会直接崩溃。
    if not callable(method):  # 新增代码+Phase5GlobalEscapeAbort：确认注册方法可调用；如果没有这一行，错误后端会触发 TypeError。
        return {"global_hotkey_registered": False, "token": "", "reason": "registerEscHotkey_backend_missing", "model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL}  # 新增代码+Phase5GlobalEscapeAbort：返回未注册报告；如果没有这一行，系统可能假装注册成功。
    token = method(handler)  # 新增代码+Phase5GlobalEscapeAbort：调用真实或内存后端注册；如果没有这一行，Escape hook 不会生效。
    return {"global_hotkey_registered": bool(token), "token": str(token or ""), "reason": "registered" if token else "empty_token", "model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL}  # 新增代码+Phase5GlobalEscapeAbort：返回注册结果；如果没有这一行，上层无法知道 hook 是否可用。
# 新增代码+Phase5GlobalEscapeAbort：函数段结束，registerEscHotkey 到此结束；如果没有这个边界说明，初学者不容易看出热键注册入口范围。


def unregisterEscHotkey(backend: Any, token: Any) -> dict[str, Any]:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，注销 Escape 热键的统一入口；如果没有这段函数，cleanup 需要知道每种后端细节。
    method = getattr(backend, "unregisterEscHotkey", None) if backend is not None else None  # 新增代码+Phase5GlobalEscapeAbort：读取后端注销方法；如果没有这一行，缺后端时会直接崩溃。
    if not callable(method):  # 新增代码+Phase5GlobalEscapeAbort：确认注销方法可调用；如果没有这一行，错误后端会触发 TypeError。
        return {"unregistered": True, "escape_hook_unregistered": True, "global_hotkey_registered": False, "reason": "unregisterEscHotkey_backend_missing", "model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL}  # 新增代码+Phase5GlobalEscapeAbort：缺后端时视为无 hook 残留；如果没有这一行，幂等 cleanup 会失败。
    report = _phase5_dict(method(token))  # 新增代码+Phase5GlobalEscapeAbort：调用后端注销并规范化报告；如果没有这一行，真实 hook 可能残留。
    return {"unregistered": bool(report.get("unregistered", True)), "escape_hook_unregistered": bool(report.get("unregistered", True)), "global_hotkey_registered": bool(report.get("global_hotkey_registered", False)), "token": str(token or ""), "backend_report": report, "model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL}  # 新增代码+Phase5GlobalEscapeAbort：返回统一注销结果；如果没有这一行，cleanup 无法形成稳定字段。
# 新增代码+Phase5GlobalEscapeAbort：函数段结束，unregisterEscHotkey 到此结束；如果没有这个边界说明，初学者不容易看出热键注销入口范围。


class GlobalEscapeAbortController:  # 新增代码+Phase5GlobalEscapeAbort：类段开始，管理计划内 Escape 与用户全局急停；如果没有这个类，模型按 Esc 和用户按 Esc 会被混在一起。
    def __init__(self, backend: Any = None, lock_manager: ComputerUseLockManager | None = None, session_id: str = "learning-agent-default-session") -> None:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，初始化控制器依赖；如果没有这段函数，上层无法注入测试后端和锁管理器。
        self.backend = backend if backend is not None else Phase5InMemoryEscHotkeyBackend()  # 新增代码+Phase5GlobalEscapeAbort：保存或创建热键后端；如果没有这一行，控制器没有注册/注销目标。
        self.lock_manager = lock_manager if lock_manager is not None else ComputerUseLockManager()  # 新增代码+Phase5GlobalEscapeAbort：保存或创建 durable lock 管理器；如果没有这一行，用户急停无法落盘。
        self.session_id = str(session_id or "learning-agent-default-session")  # 新增代码+Phase5GlobalEscapeAbort：保存会话 id；如果没有这一行，报告无法说明是哪个会话注册了 hook。
        self._registered = False  # 新增代码+Phase5GlobalEscapeAbort：记录是否已注册；如果没有这一行，重复注册和状态输出无法判断。
        self._registration_token = ""  # 新增代码+Phase5GlobalEscapeAbort：记录后端 token；如果没有这一行，cleanup 不能准确注销当前 hook。
        self._expected_escape_count = 0  # 新增代码+Phase5GlobalEscapeAbort：记录模型计划内 Escape 次数；如果没有这一行，模型按 Esc 会被误判为用户取消。
        self._abort_count = 0  # 新增代码+Phase5GlobalEscapeAbort：记录意外 Escape 触发的 abort 次数；如果没有这一行，状态面板无法展示急停发生次数。
        self._last_event: dict[str, Any] = {}  # 新增代码+Phase5GlobalEscapeAbort：保存最近一次 Escape 事件；如果没有这一行，调试时无法快速看到最后一次分流结果。
    # 新增代码+Phase5GlobalEscapeAbort：函数段结束，GlobalEscapeAbortController.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出控制器状态范围。
    def register(self) -> dict[str, Any]:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，注册全局 Escape hook；如果没有这段函数，上层无法启用用户急停键。
        if self._registered:  # 新增代码+Phase5GlobalEscapeAbort：先处理重复注册；如果没有这一行，重复调用会堆叠多个热键监听。
            return {"global_hotkey_registered": True, "token": self._registration_token, "idempotent": True, "model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL}  # 新增代码+Phase5GlobalEscapeAbort：重复注册返回幂等成功；如果没有这一行，上层 cleanup 生命周期会变得脆弱。
        report = registerEscHotkey(self.backend, self.handle_escape)  # 新增代码+Phase5GlobalEscapeAbort：通过统一入口注册 Escape；如果没有这一行，矩阵和控制器不会共享同一语义。
        self._registered = bool(report.get("global_hotkey_registered"))  # 新增代码+Phase5GlobalEscapeAbort：保存注册状态；如果没有这一行，状态面板不知道 hook 是否可用。
        self._registration_token = str(report.get("token", ""))  # 新增代码+Phase5GlobalEscapeAbort：保存注册 token；如果没有这一行，cleanup 不能引用正确 hook。
        return {**report, "idempotent": False, "marker": PHASE5_GLOBAL_ESCAPE_ABORT_MARKER}  # 新增代码+Phase5GlobalEscapeAbort：返回完整注册报告；如果没有这一行，调用方拿不到 marker 和幂等状态。
    # 新增代码+Phase5GlobalEscapeAbort：函数段结束，GlobalEscapeAbortController.register 到此结束；如果没有这个边界说明，初学者不容易看出注册生命周期范围。
    def mark_expected_escape(self, reason: str = "model_sent_escape", count: Any = 1) -> dict[str, Any]:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，声明接下来的 Escape 是模型计划动作；如果没有这段函数，模型无法安全关闭菜单或对话框。
        normalized_count = _phase5_positive_count(count)  # 新增代码+Phase5GlobalEscapeAbort：规范化 count；如果没有这一行，负数或坏输入会破坏计数。
        self._expected_escape_count += normalized_count  # 新增代码+Phase5GlobalEscapeAbort：累加计划内 Escape；如果没有这一行，下一次模型 Escape 仍会触发 abort。
        return {"expected_escape_count": self._expected_escape_count, "added": normalized_count, "reason": str(reason or ""), "model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL}  # 新增代码+Phase5GlobalEscapeAbort：返回当前计划内计数；如果没有这一行，调用方无法确认声明已生效。
    # 新增代码+Phase5GlobalEscapeAbort：函数段结束，GlobalEscapeAbortController.mark_expected_escape 到此结束；如果没有这个边界说明，初学者不容易看出计划 Escape 声明范围。
    def handle_escape(self, source: str = "keyboard") -> dict[str, Any]:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，处理一次 Escape 触发；如果没有这段函数，全局热键触发后没有分流逻辑。
        safe_source = str(source or "keyboard")  # 新增代码+Phase5GlobalEscapeAbort：规范化事件来源；如果没有这一行，报告可能出现 None 或换行污染。
        if self._expected_escape_count > 0:  # 新增代码+Phase5GlobalEscapeAbort：优先消耗模型计划内 Escape；如果没有这一行，模型发出的 Escape 会误触用户取消。
            self._expected_escape_count -= 1  # 新增代码+Phase5GlobalEscapeAbort：消耗一次计划内 Escape；如果没有这一行，所有后续 Escape 都可能被错当计划内。
            self._last_event = {"abort_requested": False, "expected_escape_consumed": True, "source": safe_source, "remaining_expected_escape_count": self._expected_escape_count, "model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL}  # 新增代码+Phase5GlobalEscapeAbort：记录计划内事件；如果没有这一行，状态面板无法解释为什么没有急停。
            return dict(self._last_event)  # 新增代码+Phase5GlobalEscapeAbort：返回计划内事件；如果没有这一行，后端拿不到处理结果。
        abort_report = self.lock_manager.request_abort("global_escape_abort", requested_by=f"global_escape_hotkey:{self.session_id}")  # 新增代码+Phase5GlobalEscapeAbort：把用户 Escape 写入 durable abort；如果没有这一行，下一次桌面动作不会被拦下。
        self._abort_count += 1  # 新增代码+Phase5GlobalEscapeAbort：累计急停次数；如果没有这一行，状态面板无法展示用户取消发生过。
        self._last_event = {"abort_requested": True, "expected_escape_consumed": False, "source": safe_source, "abort_count": self._abort_count, "abort_report": abort_report, "model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL}  # 新增代码+Phase5GlobalEscapeAbort：记录意外 Escape 事件；如果没有这一行，调试时无法确认 durable abort 写入结果。
        return dict(self._last_event)  # 新增代码+Phase5GlobalEscapeAbort：返回意外 Escape 事件；如果没有这一行，后端无法反馈用户取消已生效。
    # 新增代码+Phase5GlobalEscapeAbort：函数段结束，GlobalEscapeAbortController.handle_escape 到此结束；如果没有这个边界说明，初学者不容易看出 Escape 分流范围。
    def unregister(self) -> dict[str, Any]:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，注销全局 Escape hook；如果没有这段函数，系统级监听可能在一轮结束后残留。
        if not self._registered:  # 新增代码+Phase5GlobalEscapeAbort：处理未注册或已注销情况；如果没有这一行，幂等 cleanup 会误报失败。
            return {"unregistered": True, "escape_hook_unregistered": True, "global_hotkey_registered": False, "idempotent": True, "model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL}  # 新增代码+Phase5GlobalEscapeAbort：无 hook 时返回幂等成功；如果没有这一行，重复 cleanup 会失败。
        report = unregisterEscHotkey(self.backend, self._registration_token)  # 新增代码+Phase5GlobalEscapeAbort：通过统一入口注销热键；如果没有这一行，真实后端 hook 可能残留。
        self._registered = bool(report.get("global_hotkey_registered", False))  # 新增代码+Phase5GlobalEscapeAbort：根据后端报告更新注册状态；如果没有这一行，状态面板可能显示旧状态。
        if not self._registered:  # 新增代码+Phase5GlobalEscapeAbort：确认已注销后清理 token；如果没有这一行，旧 token 会残留。
            self._registration_token = ""  # 新增代码+Phase5GlobalEscapeAbort：清空注册 token；如果没有这一行，下次注册/注销可能混用旧 token。
        return {**report, "idempotent": False, "marker": PHASE5_GLOBAL_ESCAPE_ABORT_MARKER}  # 新增代码+Phase5GlobalEscapeAbort：返回注销报告；如果没有这一行，cleanup 无法拿到 hook 释放证据。
    # 新增代码+Phase5GlobalEscapeAbort：函数段结束，GlobalEscapeAbortController.unregister 到此结束；如果没有这个边界说明，初学者不容易看出注销生命周期范围。
    def cleanup(self) -> dict[str, Any]:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，提供 turn cleanup 可调用入口；如果没有这段函数，统一 cleanup 需要知道内部注销细节。
        return self.unregister()  # 新增代码+Phase5GlobalEscapeAbort：复用注销逻辑；如果没有这一行，cleanup 和手动 unregister 可能出现语义分叉。
    # 新增代码+Phase5GlobalEscapeAbort：函数段结束，GlobalEscapeAbortController.cleanup 到此结束；如果没有这个边界说明，初学者不容易看出 cleanup 入口范围。
    def status(self) -> dict[str, Any]:  # 新增代码+Phase5GlobalEscapeAbort：函数段开始，返回全局 Escape 控制器状态；如果没有这段函数，终端状态面板无法解释急停是否启用。
        return {"enabled": True, "model": PHASE5_GLOBAL_ESCAPE_ABORT_MODEL, "marker": PHASE5_GLOBAL_ESCAPE_ABORT_MARKER, "session_id": self.session_id, "global_hotkey_registered": self._registered, "token": self._registration_token, "expected_escape_count": self._expected_escape_count, "abort_count": self._abort_count, "last_event": dict(self._last_event)}  # 新增代码+Phase5GlobalEscapeAbort：返回机器可读状态；如果没有这一行，hooks 和矩阵无法读取 Phase5 能力。
    # 新增代码+Phase5GlobalEscapeAbort：函数段结束，GlobalEscapeAbortController.status 到此结束；如果没有这个边界说明，初学者不容易看出状态输出范围。
# 新增代码+Phase5GlobalEscapeAbort：类段结束，GlobalEscapeAbortController 到此结束；如果没有这个边界说明，初学者不容易看出控制器实现范围。


__all__ = ["GlobalEscapeAbortController", "PHASE5_GLOBAL_ESCAPE_ABORT_MARKER", "PHASE5_GLOBAL_ESCAPE_ABORT_MODEL", "Phase5InMemoryEscHotkeyBackend", "registerEscHotkey", "unregisterEscHotkey"]  # 新增代码+Phase5GlobalEscapeAbort：声明稳定公开 API；如果没有这一行，后续模块不清楚哪些名称可依赖。
