"""Windows Computer Use session runtime for abort, cleanup, and notifications."""  # 新增代码+Phase40WindowsAbortCleanup: 说明本文件负责 Phase40 会话运行时；如果没有这行代码，读者不知道 abort、cleanup 和通知为什么被放到一个模块。
from __future__ import annotations  # 新增代码+Phase40WindowsAbortCleanup: 启用延迟类型解析；如果没有这行代码，旧解释顺序下前向类型标注更容易出错。
import tempfile  # 新增代码+Phase40WindowsAbortCleanup: 导入临时目录工具用于 CLI 合同自检；如果没有这行代码，自检会污染真实锁和通知目录。
from pathlib import Path  # 新增代码+Phase40WindowsAbortCleanup: 导入 Path 统一处理 Windows 路径；如果没有这行代码，通知文件路径拼接更容易写错。
from typing import Any  # 新增代码+Phase40WindowsAbortCleanup: 导入 Any 描述 JSON 风格结构；如果没有这行代码，公开接口类型边界不清楚。
try:  # 新增代码+Phase40WindowsAbortCleanup: 优先按包模式导入锁和文件工具；如果没有这行代码，正常 `python -m` 入口无法复用既有 durable 文件能力。
    from learning_agent.computer_use.lock import ComputerUseLockManager, phase30_lock_timestamp  # 新增代码+Phase40WindowsAbortCleanup: 导入 durable lock 管理器和 UTC 时间戳；如果没有这行代码，runtime 无法写 abort/cleanup 状态。
    from learning_agent.runtime.files import atomic_write_json, read_json_or_default  # 新增代码+Phase40WindowsAbortCleanup: 导入安全 JSON 写入和读取；如果没有这行代码，通知文件可能被半写损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase40WindowsAbortCleanup: 兼容 start_oauth_agent.bat 脚本模式导入；如果没有这行代码，真实可见终端可能因为包路径不同而失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.lock", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase40WindowsAbortCleanup: 只对预期包路径缺失做 fallback；如果没有这行代码，真实内部错误会被误吞。
        raise  # 新增代码+Phase40WindowsAbortCleanup: 非预期导入错误继续抛出；如果没有这行代码，排查 runtime.files 内部错误会很困难。
    from computer_use.lock import ComputerUseLockManager, phase30_lock_timestamp  # 新增代码+Phase40WindowsAbortCleanup: 脚本模式导入 durable lock 管理器；如果没有这行代码，bat 入口无法执行 `/computer cleanup`。
    from runtime.files import atomic_write_json, read_json_or_default  # 新增代码+Phase40WindowsAbortCleanup: 脚本模式导入 JSON 文件工具；如果没有这行代码，bat 入口无法持久化通知。

PHASE40_WINDOWS_ABORT_CLEANUP_MARKER = "PHASE40_WINDOWS_ABORT_CLEANUP_READY"  # 新增代码+Phase40WindowsAbortCleanup: 定义 Phase40 稳定 marker；如果没有这行代码，真实终端验收无法可靠匹配阶段完成。
PHASE40_WINDOWS_ABORT_CLEANUP_OK_TOKEN = "PHASE40_WINDOWS_ABORT_CLEANUP_OK"  # 新增代码+Phase40WindowsAbortCleanup: 定义 Phase40 自检 OK token；如果没有这行代码，验收无法区分普通输出和合同通过。
PHASE40_SESSION_RUNTIME_MODEL = "phase40_windows_abort_cleanup_runtime"  # 新增代码+Phase40WindowsAbortCleanup: 定义会话运行时模型版本；如果没有这行代码，状态输出无法说明当前使用哪套 cleanup/notification 规则。
PHASE40_DEFAULT_SESSION_ID = "learning-agent-default-session"  # 新增代码+Phase40WindowsAbortCleanup: 定义终端 cleanup 默认释放的会话 id；如果没有这行代码，用户输入 `/computer cleanup` 时不知道清理哪一轮。
PHASE40_ACTIONS_EXPANDED = False  # 新增代码+Phase40WindowsAbortCleanup: 明确 Phase40 不扩大真实动作面；如果没有这行代码，用户可能误以为新增了更多桌面自动化动作。


def _bool_token(value: Any) -> str:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，把布尔值转成验收友好的小写文本；如果没有这段函数，CLI token 大小写可能漂移。
    return str(bool(value)).lower()  # 新增代码+Phase40WindowsAbortCleanup: 返回 true/false 文本；如果没有这行代码，场景 JSON 很难稳定匹配布尔值。
# 新增代码+Phase40WindowsAbortCleanup: 函数段结束，_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


class WindowsComputerUseSessionRuntime:  # 新增代码+Phase40WindowsAbortCleanup: 定义 Windows Computer Use 会话运行时；如果没有这个类，abort、cleanup 和通知会继续散落在终端命令和锁管理器里。
    def __init__(self, lock_manager: ComputerUseLockManager | None = None, session_id: str = PHASE40_DEFAULT_SESSION_ID, notification_limit: int = 20) -> None:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，初始化锁管理器、会话 id 和通知队列；如果没有这段函数，调用方无法创建可复用 runtime。
        self.lock_manager = lock_manager if lock_manager is not None else ComputerUseLockManager()  # 新增代码+Phase40WindowsAbortCleanup: 保存或创建 durable lock 管理器；如果没有这行代码，runtime 没有底层 abort/cleanup 状态源。
        self.session_id = str(session_id or PHASE40_DEFAULT_SESSION_ID)  # 新增代码+Phase40WindowsAbortCleanup: 保存当前 runtime 会话 id；如果没有这行代码，cleanup 不知道应该释放哪个 owner。
        self.notification_limit = max(1, int(notification_limit))  # 新增代码+Phase40WindowsAbortCleanup: 限制通知队列长度至少为 1；如果没有这行代码，坏参数可能让通知全部丢失或无限增长。
        self.notification_path = Path(self.lock_manager.base_dir) / "session_runtime_notifications.json"  # 新增代码+Phase40WindowsAbortCleanup: 把通知文件放在同一个 Computer Use lock 根目录；如果没有这行代码，跨命令 `/computer notifications` 看不到历史通知。
        self.model = PHASE40_SESSION_RUNTIME_MODEL  # 新增代码+Phase40WindowsAbortCleanup: 保存 runtime 模型名供测试和终端输出读取；如果没有这行代码，状态输出需要硬编码常量。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def _read_notifications(self) -> list[dict[str, Any]]:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，读取持久化通知队列；如果没有这段函数，通知只能停留在内存里跨命令丢失。
        notifications = read_json_or_default(self.notification_path, [])  # 新增代码+Phase40WindowsAbortCleanup: 容错读取通知 JSON；如果没有这行代码，首次运行或半写文件会导致状态页崩溃。
        return [dict(item) for item in notifications if isinstance(item, dict)] if isinstance(notifications, list) else []  # 新增代码+Phase40WindowsAbortCleanup: 规范化通知列表并丢弃坏项；如果没有这行代码，损坏数据可能污染终端输出。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，_read_notifications 到此结束；如果没有这个边界说明，读者不容易看出通知读取范围。

    def _write_notifications(self, notifications: list[dict[str, Any]]) -> None:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，写入裁剪后的通知队列；如果没有这段函数，通知文件会无限增长或写入不安全。
        trimmed = list(notifications)[-self.notification_limit:]  # 新增代码+Phase40WindowsAbortCleanup: 只保留最近 N 条通知；如果没有这行代码，长期运行会让通知文件越来越大。
        atomic_write_json(self.notification_path, trimmed)  # 新增代码+Phase40WindowsAbortCleanup: 原子写入通知文件；如果没有这行代码，进程中断可能留下半个 JSON。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，_write_notifications 到此结束；如果没有这个边界说明，读者不容易看出通知写入范围。

    def _record_notification(self, event: str, message: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，追加一条 runtime 通知；如果没有这段函数，abort 和 cleanup 事件无法被用户复盘。
        notifications = self._read_notifications()  # 新增代码+Phase40WindowsAbortCleanup: 读取已有通知；如果没有这行代码，新通知会覆盖旧通知。
        notification = {"sequence": len(notifications) + 1, "event": str(event or ""), "message": str(message or ""), "metadata": dict(metadata or {}), "session_id": self.session_id, "model": self.model, "created_at": phase30_lock_timestamp()}  # 新增代码+Phase40WindowsAbortCleanup: 构造结构化通知；如果没有这行代码，终端只能显示零散字符串且无法审计。
        notifications.append(notification)  # 新增代码+Phase40WindowsAbortCleanup: 把新通知追加到队列；如果没有这行代码，通知不会被保存。
        self._write_notifications(notifications)  # 新增代码+Phase40WindowsAbortCleanup: 持久化更新后的通知队列；如果没有这行代码，跨命令通知会消失。
        return notification  # 新增代码+Phase40WindowsAbortCleanup: 返回新通知供调用方展示；如果没有这行代码，abort/cleanup 输出无法显示 notification_event。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，_record_notification 到此结束；如果没有这个边界说明，读者不容易看出通知追加范围。

    def notifications(self) -> list[dict[str, Any]]:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，公开读取通知队列；如果没有这段函数，终端 `/computer notifications` 无法复用同一事实源。
        return self._read_notifications()  # 新增代码+Phase40WindowsAbortCleanup: 返回已规范化通知列表；如果没有这行代码，调用方需要知道内部通知文件路径。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，notifications 到此结束；如果没有这个边界说明，读者不容易看出通知公开读取范围。

    def request_global_abort(self, reason: str, source: str = "runtime") -> dict[str, Any]:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，请求全局 abort 并记录通知；如果没有这段函数，abort 只有底层 flag 而没有 ClaudeCode 风格的用户可见事件。
        status = self.lock_manager.request_abort(reason, requested_by=source)  # 新增代码+Phase40WindowsAbortCleanup: 写入 durable abort flag；如果没有这行代码，下一次桌面动作不会被阻断。
        notification = self._record_notification("computer_use_abort_requested", f"Computer Use abort requested: {reason}", {"source": source, "abort_requested": True})  # 新增代码+Phase40WindowsAbortCleanup: 记录 abort 通知；如果没有这行代码，用户事后不知道谁触发了急停。
        notifications = self._read_notifications()  # 新增代码+Phase40WindowsAbortCleanup: 读取通知数量用于返回摘要；如果没有这行代码，输出无法显示 notification_count。
        return {"model": self.model, "marker": PHASE40_WINDOWS_ABORT_CLEANUP_MARKER, "abort_requested": bool(status.get("abort_requested")), "status": status, "notification": notification, "notification_count": len(notifications), "actions_expanded": PHASE40_ACTIONS_EXPANDED}  # 新增代码+Phase40WindowsAbortCleanup: 返回结构化 abort 结果；如果没有这行代码，终端和测试无法统一读取结果。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，request_global_abort 到此结束；如果没有这个边界说明，读者不容易看出全局 abort 范围。

    def cleanup_turn(self, session_id: str | None = None, reason: str = "turn cleanup") -> dict[str, Any]:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，清理一轮 Computer Use 控制状态；如果没有这段函数，崩溃或结束后的锁可能残留。
        target_session_id = str(session_id or self.session_id or PHASE40_DEFAULT_SESSION_ID)  # 新增代码+Phase40WindowsAbortCleanup: 确定要释放的会话 id；如果没有这行代码，cleanup 不知道释放哪个 owner。
        release_result = self.lock_manager.release(target_session_id)  # 新增代码+Phase40WindowsAbortCleanup: 尝试释放该会话持有的桌面锁；如果没有这行代码，cleanup 只会打印状态不会实际清理。
        lock_released = bool(release_result.get("released"))  # 新增代码+Phase40WindowsAbortCleanup: 规范化释放结果；如果没有这行代码，终端输出无法稳定显示 true/false。
        notification = self._record_notification("computer_use_turn_cleanup_completed", f"Computer Use cleanup completed for {target_session_id}", {"reason": reason, "lock_released": lock_released})  # 新增代码+Phase40WindowsAbortCleanup: 记录 cleanup 通知；如果没有这行代码，turn 清理没有可见轨迹。
        status = self.lock_manager.status()  # 新增代码+Phase40WindowsAbortCleanup: 读取 cleanup 后的最新锁状态；如果没有这行代码，返回值可能仍是释放前状态。
        notifications = self._read_notifications()  # 新增代码+Phase40WindowsAbortCleanup: 读取通知数量用于返回摘要；如果没有这行代码，调用方看不到累计通知数量。
        return {"model": self.model, "marker": PHASE40_WINDOWS_ABORT_CLEANUP_MARKER, "cleanup_completed": True, "session_id": target_session_id, "lock_released": lock_released, "release": release_result, "status": status, "notification": notification, "notification_count": len(notifications), "actions_expanded": PHASE40_ACTIONS_EXPANDED}  # 新增代码+Phase40WindowsAbortCleanup: 返回结构化 cleanup 结果；如果没有这行代码，终端和测试无法统一判断 cleanup。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，cleanup_turn 到此结束；如果没有这个边界说明，读者不容易看出 turn cleanup 范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，汇总 runtime、lock 和通知状态；如果没有这段函数，终端状态 UI 仍要自己拼多个来源。
        lock_status = self.lock_manager.status()  # 新增代码+Phase40WindowsAbortCleanup: 读取 durable lock 和 abort 状态；如果没有这行代码，runtime status 不知道当前是否急停。
        notifications = self._read_notifications()  # 新增代码+Phase40WindowsAbortCleanup: 读取持久化通知；如果没有这行代码，status 看不到最近 abort/cleanup 事件。
        cleanup_count = sum(1 for item in notifications if item.get("event") == "computer_use_turn_cleanup_completed")  # 新增代码+Phase40WindowsAbortCleanup: 统计 cleanup 通知数量；如果没有这行代码，用户无法判断本轮是否发生过 cleanup。
        last_notification = notifications[-1] if notifications else {}  # 新增代码+Phase40WindowsAbortCleanup: 取最后一条通知作为状态摘要；如果没有这行代码，状态 UI 只能显示总数不显示最新原因。
        return {"model": self.model, "marker": PHASE40_WINDOWS_ABORT_CLEANUP_MARKER, "session_id": self.session_id, "lock": lock_status, "abort_requested": bool(lock_status.get("abort_requested")), "notification_count": len(notifications), "cleanup_count": cleanup_count, "last_notification": dict(last_notification), "notification_path": str(self.notification_path), "actions_expanded": PHASE40_ACTIONS_EXPANDED}  # 新增代码+Phase40WindowsAbortCleanup: 返回统一 runtime 状态；如果没有这行代码，终端、SDK 和验收器会各自猜测状态。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，status 到此结束；如果没有这个边界说明，读者不容易看出 runtime 状态汇总范围。

    def terminal_status_lines(self) -> list[str]:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，生成终端可见 runtime 摘要；如果没有这段函数，用户无法像 `/chrome` 那样快速看 Computer Use 状态。
        status = self.status()  # 新增代码+Phase40WindowsAbortCleanup: 获取统一状态；如果没有这行代码，终端输出可能和底层状态不一致。
        last_notification = dict(status.get("last_notification", {}))  # 新增代码+Phase40WindowsAbortCleanup: 取最新通知用于渲染；如果没有这行代码，后续格式化要反复做类型判断。
        return ["Computer Runtime", f"- runtime_model={status.get('model', '')}", f"- marker={status.get('marker', '')}", f"- session_id={status.get('session_id', '')}", f"- abort_requested={_bool_token(status.get('abort_requested'))}", f"- notification_count={status.get('notification_count', 0)}", f"- cleanup_count={status.get('cleanup_count', 0)}", f"- last_notification_event={last_notification.get('event', '')}", f"- last_notification_message={last_notification.get('message', '')}", f"- actions_expanded={_bool_token(status.get('actions_expanded'))}"]  # 新增代码+Phase40WindowsAbortCleanup: 返回稳定多行状态；如果没有这行代码，真实终端验收无法确认 runtime 层可见。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，terminal_status_lines 到此结束；如果没有这个边界说明，读者不容易看出终端状态渲染范围。

    def terminal_notification_lines(self) -> list[str]:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，生成最近通知列表；如果没有这段函数，`/computer notifications` 无法给用户查看历史事件。
        notifications = self._read_notifications()  # 新增代码+Phase40WindowsAbortCleanup: 读取通知队列；如果没有这行代码，通知列表没有数据来源。
        lines = ["Computer Notifications", f"- notification_count={len(notifications)}", f"- marker={PHASE40_WINDOWS_ABORT_CLEANUP_MARKER}"]  # 新增代码+Phase40WindowsAbortCleanup: 初始化通知输出标题和计数；如果没有这行代码，用户无法判断这是通知面板。
        for item in notifications[-5:]:  # 新增代码+Phase40WindowsAbortCleanup: 只展示最近五条通知；如果没有这行代码，长任务终端可能被历史通知刷屏。
            lines.append(f"- notification_event={item.get('event', '')} message={item.get('message', '')}")  # 新增代码+Phase40WindowsAbortCleanup: 渲染通知事件和消息；如果没有这行代码，通知列表只剩数字没有复盘价值。
        return lines  # 新增代码+Phase40WindowsAbortCleanup: 返回可打印行；如果没有这行代码，终端命令拿不到通知文本。
    # 新增代码+Phase40WindowsAbortCleanup: 函数段结束，terminal_notification_lines 到此结束；如果没有这个边界说明，读者不容易看出通知渲染范围。


def format_phase40_runtime_action(action: str, result: dict[str, Any]) -> str:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，格式化 abort/cleanup runtime 动作输出；如果没有这段函数，终端命令会重复拼接通知字段。
    notification = dict(result.get("notification", {})) if isinstance(result.get("notification"), dict) else {}  # 新增代码+Phase40WindowsAbortCleanup: 取出通知对象并容错；如果没有这行代码，缺通知时格式化可能崩溃。
    lines = ["Computer Runtime"]  # 新增代码+Phase40WindowsAbortCleanup: 输出固定 runtime 标题；如果没有这行代码，真实终端验收无法确认进入 Phase40 面板。
    lines.append(f"- action={action}")  # 新增代码+Phase40WindowsAbortCleanup: 显示当前 runtime 动作；如果没有这行代码，用户分不清 abort、cleanup 还是 status。
    lines.append(f"- runtime_model={result.get('model', PHASE40_SESSION_RUNTIME_MODEL)}")  # 新增代码+Phase40WindowsAbortCleanup: 显示模型版本；如果没有这行代码，后续升级难以排查当前 runtime。
    lines.append(f"- marker={result.get('marker', PHASE40_WINDOWS_ABORT_CLEANUP_MARKER)}")  # 新增代码+Phase40WindowsAbortCleanup: 显示 Phase40 marker；如果没有这行代码，验收器无法稳定匹配。
    lines.append(f"- abort_requested={_bool_token(result.get('abort_requested', result.get('status', {}).get('abort_requested') if isinstance(result.get('status'), dict) else False))}")  # 新增代码+Phase40WindowsAbortCleanup: 显示 abort 状态；如果没有这行代码，用户不知道后续动作是否会被阻断。
    lines.append(f"- cleanup_completed={_bool_token(result.get('cleanup_completed', False))}")  # 新增代码+Phase40WindowsAbortCleanup: 显示 cleanup 是否完成；如果没有这行代码，用户无法确认 turn 清理结果。
    lines.append(f"- lock_released={_bool_token(result.get('lock_released', False))}")  # 新增代码+Phase40WindowsAbortCleanup: 显示锁是否被释放；如果没有这行代码，残留锁风险不可见。
    lines.append(f"- notification_event={notification.get('event', '')}")  # 新增代码+Phase40WindowsAbortCleanup: 显示通知事件名；如果没有这行代码，abort/cleanup 通知无法被简单匹配。
    lines.append(f"- notification_message={notification.get('message', '')}")  # 新增代码+Phase40WindowsAbortCleanup: 显示通知消息；如果没有这行代码，用户不知道事件原因。
    lines.append(f"- notification_count={result.get('notification_count', 0)}")  # 新增代码+Phase40WindowsAbortCleanup: 显示通知总数；如果没有这行代码，用户看不到是否有历史事件。
    lines.append(f"- actions_expanded={_bool_token(result.get('actions_expanded', PHASE40_ACTIONS_EXPANDED))}")  # 新增代码+Phase40WindowsAbortCleanup: 显示动作面未扩大；如果没有这行代码，Phase40 容易被误解成新增真实控制动作。
    return "\n".join(lines) + "\n"  # 新增代码+Phase40WindowsAbortCleanup: 返回完整 runtime 动作文本；如果没有这行代码，终端命令无法打印结果。
# 新增代码+Phase40WindowsAbortCleanup: 函数段结束，format_phase40_runtime_action 到此结束；如果没有这个边界说明，读者不容易看出 runtime 动作格式范围。


def run_phase40_abort_cleanup_contract() -> dict[str, Any]:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，运行 Phase40 合同自检；如果没有这段函数，真实终端只能依赖单元测试而不能打印稳定 token。
    with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase40WindowsAbortCleanup: 使用临时目录隔离自检状态；如果没有这行代码，自检会污染真实用户锁。
        lock_manager = ComputerUseLockManager(base_dir=Path(temp_dir))  # 新增代码+Phase40WindowsAbortCleanup: 创建自检专用 lock manager；如果没有这行代码，自检没有 durable 状态源。
        lock_manager.acquire("phase40-session", owner_label="contract")  # 新增代码+Phase40WindowsAbortCleanup: 预置当前会话锁；如果没有这行代码，cleanup 无法证明释放流程。
        runtime = WindowsComputerUseSessionRuntime(lock_manager=lock_manager, session_id="phase40-session")  # 新增代码+Phase40WindowsAbortCleanup: 创建自检 runtime；如果没有这行代码，abort/cleanup 合同无法执行。
        abort_result = runtime.request_global_abort("phase40-contract-abort", source="contract")  # 新增代码+Phase40WindowsAbortCleanup: 触发全局 abort；如果没有这行代码，abort 合同无法验证。
        cleanup_result = runtime.cleanup_turn(reason="phase40-contract-cleanup")  # 新增代码+Phase40WindowsAbortCleanup: 执行 turn cleanup；如果没有这行代码，cleanup 合同无法验证。
        notifications = runtime.notifications()  # 新增代码+Phase40WindowsAbortCleanup: 读取通知队列；如果没有这行代码，通知合同无法验证。
        terminal_status = "\n".join(runtime.terminal_status_lines())  # 新增代码+Phase40WindowsAbortCleanup: 渲染终端状态文本；如果没有这行代码，terminal_status 合同无法验证。
        return {"marker": PHASE40_WINDOWS_ABORT_CLEANUP_MARKER, "abort": bool(abort_result.get("abort_requested") and lock_manager.is_abort_requested()), "cleanup": bool(cleanup_result.get("cleanup_completed") and cleanup_result.get("lock_released") and not lock_manager.status().get("locked")), "notifications": bool(any(item.get("event") == "computer_use_abort_requested" for item in notifications) and any(item.get("event") == "computer_use_turn_cleanup_completed" for item in notifications)), "terminal_status": bool(PHASE40_WINDOWS_ABORT_CLEANUP_MARKER in terminal_status and PHASE40_SESSION_RUNTIME_MODEL in terminal_status), "actions_expanded": PHASE40_ACTIONS_EXPANDED}  # 新增代码+Phase40WindowsAbortCleanup: 返回自检摘要；如果没有这行代码，CLI 无法生成稳定成功行。
# 新增代码+Phase40WindowsAbortCleanup: 函数段结束，run_phase40_abort_cleanup_contract 到此结束；如果没有这个边界说明，读者不容易看出合同自检范围。


def phase40_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，把自检报告转成单行 token；如果没有这段函数，真实终端断言会依赖复杂 JSON。
    return f"{PHASE40_WINDOWS_ABORT_CLEANUP_OK_TOKEN} abort={_bool_token(report.get('abort'))} cleanup={_bool_token(report.get('cleanup'))} notifications={_bool_token(report.get('notifications'))} terminal_status={_bool_token(report.get('terminal_status'))} actions_expanded={_bool_token(report.get('actions_expanded'))} marker={PHASE40_WINDOWS_ABORT_CLEANUP_MARKER}"  # 新增代码+Phase40WindowsAbortCleanup: 返回固定顺序 token；如果没有这行代码，acceptance scenario 容易因输出漂移失败。
# 新增代码+Phase40WindowsAbortCleanup: 函数段结束，phase40_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 文本范围。


def main() -> int:  # 新增代码+Phase40WindowsAbortCleanup: 函数段开始，提供 `python -m`/`python -c` 可调用入口；如果没有这段函数，真实终端场景无法直接打印 Phase40 token。
    print(PHASE40_WINDOWS_ABORT_CLEANUP_MARKER)  # 新增代码+Phase40WindowsAbortCleanup: 先打印阶段 ready marker；如果没有这行代码，验收器可能只看到 OK token 看不到阶段名。
    print(phase40_cli_line(run_phase40_abort_cleanup_contract()))  # 新增代码+Phase40WindowsAbortCleanup: 打印稳定自检行；如果没有这行代码，真实终端不会出现 Phase40 验收 token。
    return 0  # 新增代码+Phase40WindowsAbortCleanup: 返回成功退出码；如果没有这行代码，脚本调用方无法稳定判断命令成功。
# 新增代码+Phase40WindowsAbortCleanup: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出 CLI 入口范围。


if __name__ == "__main__":  # 新增代码+Phase40WindowsAbortCleanup: 允许直接运行模块文件；如果没有这行代码，初学者无法用 python 文件方式自检 Phase40。
    raise SystemExit(main())  # 新增代码+Phase40WindowsAbortCleanup: 用 main 的返回码退出；如果没有这行代码，直接运行模块不会执行合同自检。
