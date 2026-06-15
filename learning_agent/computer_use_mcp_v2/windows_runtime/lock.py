"""Windows Computer Use durable lock 和 abort flag 管理器。"""  # 修改代码+Phase31ComputerUseLockAbortEvidence: 说明本文件集中管理桌面控制锁、陈旧锁恢复和急停标记；如果没有这个文件，多个 agent 会话可能同时操作同一台电脑。
from __future__ import annotations  # 修改代码+Phase31ComputerUseLockAbortEvidence: 启用延迟类型解析；如果没有这行代码，旧运行路径下 Path 等前向类型更容易出错。
import os  # 修改代码+Phase31ComputerUseLockAbortEvidence: 读取当前进程号写入锁证据；如果没有这行代码，锁文件无法说明由哪个进程创建。
import calendar  # 修改代码+Phase31ComputerUseLockAbortEvidence: 按 UTC 解析锁文件时间戳；如果没有这行代码，东八区会把新锁误判成 8 小时前的陈旧锁。
import time  # 修改代码+Phase31ComputerUseLockAbortEvidence: 生成 UTC 时间戳和判断陈旧锁年龄；如果没有这行代码，锁无法过期恢复。
from pathlib import Path  # 修改代码+Phase31ComputerUseLockAbortEvidence: 用 Path 管理 Windows 路径；如果没有这行代码，字符串拼路径更容易写错。
from typing import Any  # 修改代码+Phase31ComputerUseLockAbortEvidence: 描述 JSON metadata 的通用类型；如果没有这行代码，接口边界不清楚。

try:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 包运行模式下导入 runtime 文件工具；如果没有这行代码，锁状态无法复用已有原子写入能力。
    from learning_agent.runtime.files import FileLock, atomic_write_json, read_json_or_default  # 修改代码+Phase31ComputerUseLockAbortEvidence: 导入文件互斥锁、原子 JSON 写入和容错读取；如果没有这行代码，并发写锁状态可能损坏。
except ModuleNotFoundError as error:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 兼容 start_oauth_agent.bat 直接脚本模式；如果没有这行代码，脚本模式下包路径变化会导入失败。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 只对目标包路径缺失做 fallback；如果没有这行代码，真实内部错误会被误吞。
        raise  # 修改代码+Phase31ComputerUseLockAbortEvidence: 重新抛出非目标导入错误；如果没有这行代码，排查 runtime.files 内部问题会很困难。
    from runtime.files import FileLock, atomic_write_json, read_json_or_default  # 修改代码+Phase31ComputerUseLockAbortEvidence: 脚本模式下导入同目录 runtime 工具；如果没有这行代码，bat 入口无法加载锁管理器。

DEFAULT_COMPUTER_USE_LOCK_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "locks"  # 修改代码+Phase31ComputerUseLockAbortEvidence: 定义默认锁目录；如果没有这行代码，生产运行不知道把锁状态保存到哪里。

# 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，phase30_lock_timestamp 用于生成审计时间；如果没有这段函数，锁和 abort 记录会重复手写时间格式，作者意图是让磁盘状态更容易排序和阅读。
def phase30_lock_timestamp() -> str:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 定义 UTC 时间戳 helper；如果没有这行代码，调用方需要重复 time.strftime 写法。
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # 修改代码+Phase31ComputerUseLockAbortEvidence: 返回 ISO 风格 UTC 时间；如果没有这行代码，锁状态缺少可读时间。
# 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，phase30_lock_timestamp 到此结束；如果没有这个结束标记，初学者不容易看出时间 helper 的边界。

# 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，parse_lock_timestamp 把锁文件里的 UTC 时间转成秒；如果没有这段函数，陈旧锁无法判断年龄，作者意图是让崩溃遗留锁可自动恢复。
def parse_lock_timestamp(timestamp: Any) -> float:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 定义锁时间解析 helper；如果没有这行代码，acquire 里会散落易错的时间解析逻辑。
    try:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 捕获坏时间戳；如果没有这行代码，损坏锁文件会导致整个锁管理器崩溃。
        return float(calendar.timegm(time.strptime(str(timestamp or ""), "%Y-%m-%dT%H:%M:%SZ")))  # 修改代码+Phase31ComputerUseLockAbortEvidence: 按 UTC 把时间字符串解析成秒；如果没有这行代码，Windows 本地时区会把新锁误判为陈旧。
    except (TypeError, ValueError):  # 新增代码+Phase31ComputerUseLockAbortEvidence: 处理空值或格式错误；如果没有这行代码，坏锁状态无法容错。
        return 0.0  # 新增代码+Phase31ComputerUseLockAbortEvidence: 坏时间戳视为很旧；如果没有这行代码，损坏锁可能永久占用桌面控制权。
# 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，parse_lock_timestamp 到此结束；如果没有这个边界说明，读者不容易看出时间解析范围。

class ComputerUseLockManager:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 定义桌面控制锁管理器；如果没有这个类，controller 无法判断当前会话是否有权操作系统桌面。
    def __init__(self, base_dir: str | Path | None = None, timeout_seconds: float = 5.0, stale_after_seconds: float | None = 900.0) -> None:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，初始化锁目录、文件路径和陈旧锁 TTL；如果没有这段函数，调用方无法创建独立锁空间。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_COMPUTER_USE_LOCK_ROOT  # 修改代码+Phase31ComputerUseLockAbortEvidence: 保存锁根目录并允许测试注入临时目录；如果没有这行代码，测试会污染真实运行状态。
        self.timeout_seconds = float(timeout_seconds)  # 修改代码+Phase31ComputerUseLockAbortEvidence: 保存底层文件互斥锁等待时间；如果没有这行代码，锁竞争时没有明确等待边界。
        self.stale_after_seconds = None if stale_after_seconds is None else float(stale_after_seconds)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 保存陈旧锁 TTL；如果没有这行代码，崩溃遗留锁无法自动恢复。
        self.state_path = self.base_dir / "desktop_control_lock.json"  # 修改代码+Phase31ComputerUseLockAbortEvidence: 保存当前桌面控制 owner 的 JSON 文件路径；如果没有这行代码，持锁状态无法持久化。
        self.abort_path = self.base_dir / "abort_flag.json"  # 修改代码+Phase31ComputerUseLockAbortEvidence: 保存急停标记的 JSON 文件路径；如果没有这行代码，用户中断无法跨调用生效。
        self.mutex_path = self.base_dir / ".desktop_control_lock.mutex"  # 修改代码+Phase31ComputerUseLockAbortEvidence: 保存内部写入互斥锁路径；如果没有这行代码，两个进程可能同时改同一个状态文件。
        self.quarantine_dir = self.base_dir / "quarantine"  # 修改代码+Phase31ComputerUseLockAbortEvidence: 保存损坏 JSON 的隔离目录；如果没有这行代码，坏状态文件无法留证。
    # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，__init__ 到此结束；如果没有这个结束标记，读者不容易看出初始化边界。

    def _read_lock_state(self) -> dict[str, Any]:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，读取当前锁状态；如果没有这段函数，所有调用点都要重复容错读取逻辑。
        state = read_json_or_default(self.state_path, {}, quarantine_dir=self.quarantine_dir)  # 修改代码+Phase31ComputerUseLockAbortEvidence: 容错读取锁 JSON；如果没有这行代码，半写入文件会让桌面控制入口崩溃。
        return dict(state) if isinstance(state, dict) else {}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 确保返回字典；如果没有这行代码，坏类型状态可能污染后续判断。
    # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，_read_lock_state 到此结束；如果没有这个结束标记，读者不容易看出读取 helper 的边界。

    def _read_abort_state(self) -> dict[str, Any]:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，读取 abort 状态；如果没有这段函数，急停判断会重复容错读取逻辑。
        state = read_json_or_default(self.abort_path, {}, quarantine_dir=self.quarantine_dir)  # 修改代码+Phase31ComputerUseLockAbortEvidence: 容错读取 abort JSON；如果没有这行代码，损坏 abort 文件会阻断所有动作。
        return dict(state) if isinstance(state, dict) else {}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 确保返回字典；如果没有这行代码，错误类型会让 bool 判断不稳定。
    # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，_read_abort_state 到此结束；如果没有这个结束标记，读者不容易看出 abort 读取边界。

    def _lock_age_seconds(self, lock_state: dict[str, Any]) -> float:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，计算锁年龄；如果没有这段函数，陈旧锁判断会散落在 status 和 acquire 里。
        acquired_seconds = parse_lock_timestamp(lock_state.get("acquired_at"))  # 新增代码+Phase31ComputerUseLockAbortEvidence: 解析锁获取时间；如果没有这行代码，无法知道锁已经存在多久。
        if acquired_seconds <= 0:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 检查时间戳是否有效；如果没有这行代码，坏时间戳可能得到误导年龄。
            return float("inf")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 无效时间戳视为无限旧；如果没有这行代码，损坏锁可能无法被恢复。
        return max(0.0, time.time() - acquired_seconds)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回非负锁年龄；如果没有这行代码，系统时间差异可能产生负数。
    # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，_lock_age_seconds 到此结束；如果没有这个边界说明，读者不容易看出年龄计算范围。

    def _is_stale_locked_state(self, lock_state: dict[str, Any]) -> bool:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，判断锁状态是否陈旧；如果没有这段函数，崩溃 owner 无法被新会话接管。
        if self.stale_after_seconds is None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 允许关闭陈旧恢复；如果没有这行代码，特殊测试或严格模式无法禁用自动接管。
            return False  # 新增代码+Phase31ComputerUseLockAbortEvidence: TTL 关闭时永不视为陈旧；如果没有这行代码，None 会参与数值比较出错。
        if not lock_state.get("locked") or not lock_state.get("owner_session_id"):  # 新增代码+Phase31ComputerUseLockAbortEvidence: 只有真实持锁状态才判断陈旧；如果没有这行代码，空锁也会被当成陈旧恢复。
            return False  # 新增代码+Phase31ComputerUseLockAbortEvidence: 未锁定状态不陈旧；如果没有这行代码，状态页会误报。
        return self._lock_age_seconds(lock_state) >= self.stale_after_seconds  # 新增代码+Phase31ComputerUseLockAbortEvidence: 比较锁年龄和 TTL；如果没有这行代码，陈旧锁恢复不会触发。
    # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，_is_stale_locked_state 到此结束；如果没有这个边界说明，读者不容易看出陈旧判断范围。

    def status(self) -> dict[str, Any]:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，返回锁和 abort 当前状态；如果没有这段函数，computer_status 无法解释为什么动作被允许或拒绝。
        lock_state = self._read_lock_state()  # 修改代码+Phase31ComputerUseLockAbortEvidence: 读取当前锁 owner；如果没有这行代码，状态页不知道谁持锁。
        abort_state = self._read_abort_state()  # 修改代码+Phase31ComputerUseLockAbortEvidence: 读取当前 abort flag；如果没有这行代码，状态页不知道是否处于急停。
        locked = bool(lock_state.get("locked") and lock_state.get("owner_session_id"))  # 修改代码+Phase31ComputerUseLockAbortEvidence: 规范化判断是否真的有 owner；如果没有这行代码，空 owner 可能被误认为已持锁。
        is_stale = self._is_stale_locked_state(lock_state)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 判断当前锁是否陈旧；如果没有这行代码，状态页无法提示可恢复风险。
        return {"enabled": True, "locked": locked, "stale": bool(is_stale), "stale_after_seconds": self.stale_after_seconds, "lock_age_seconds": self._lock_age_seconds(lock_state) if locked else 0.0, "owner_session_id": str(lock_state.get("owner_session_id", "")), "owner_label": str(lock_state.get("owner_label", "")), "owner_pid": lock_state.get("owner_pid"), "acquired_at": str(lock_state.get("acquired_at", "")), "recovered_stale_owner_session_id": str(lock_state.get("recovered_stale_owner_session_id", "")), "recovered_stale_acquired_at": str(lock_state.get("recovered_stale_acquired_at", "")), "recovered_at": str(lock_state.get("recovered_at", "")), "abort_requested": bool(abort_state.get("requested", False)), "abort_reason": str(abort_state.get("reason", "")), "abort_requested_at": str(abort_state.get("requested_at", "")), "state_path": str(self.state_path), "abort_path": str(self.abort_path)}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 返回结构化状态；如果没有这行代码，调用方只能猜测锁、陈旧和 abort 当前状态。
    # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，status 到此结束；如果没有这个结束标记，读者不容易看出状态输出范围。

    def acquire(self, session_id: str, owner_label: str = "", metadata: dict[str, Any] | None = None) -> dict[str, Any]:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，尝试为某个会话获取桌面控制锁；如果没有这段函数，两个会话可能同时拥有桌面控制权。
        requested_session_id = str(session_id or "").strip()  # 修改代码+Phase31ComputerUseLockAbortEvidence: 清理调用方传入的会话 id；如果没有这行代码，空白 id 会写入锁文件。
        if not requested_session_id:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 检查会话 id 是否有效；如果没有这行代码，无名会话可能占用全局桌面锁。
            return {"acquired": False, "reason": "session_id 不能为空。", "status": self.status()}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 返回明确失败原因；如果没有这行代码，调用方不知道如何修正。
        with FileLock(self.mutex_path, timeout_seconds=self.timeout_seconds):  # 修改代码+Phase31ComputerUseLockAbortEvidence: 用文件互斥锁保护读改写；如果没有这行代码，并发 acquire 可能同时成功。
            current_state = self._read_lock_state()  # 修改代码+Phase31ComputerUseLockAbortEvidence: 在互斥区读取最新 owner；如果没有这行代码，判断会基于旧状态。
            current_owner = str(current_state.get("owner_session_id", ""))  # 修改代码+Phase31ComputerUseLockAbortEvidence: 读取当前 owner 会话；如果没有这行代码，无法判断是否被别人持有。
            current_locked = bool(current_state.get("locked") and current_owner)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 规范化当前是否锁定；如果没有这行代码，后续条件会重复且易错。
            recovered_stale_owner = ""  # 新增代码+Phase31ComputerUseLockAbortEvidence: 初始化被恢复 owner 为空；如果没有这行代码，非恢复路径会缺少稳定字段来源。
            recovered_stale_acquired_at = ""  # 新增代码+Phase31ComputerUseLockAbortEvidence: 初始化被恢复锁时间为空；如果没有这行代码，非恢复路径可能引用未定义变量。
            recovered_at = ""  # 新增代码+Phase31ComputerUseLockAbortEvidence: 初始化恢复时间为空；如果没有这行代码，状态构造可能引用未定义变量。
            if current_locked and current_owner != requested_session_id:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 处理锁被其他会话持有的情况；如果没有这行代码，两个 session 会同时控制桌面。
                if not self._is_stale_locked_state(current_state):  # 新增代码+Phase31ComputerUseLockAbortEvidence: 非陈旧锁仍拒绝抢占；如果没有这行代码，新会话会错误抢走活跃会话的锁。
                    return {"acquired": False, "reason": f"desktop control lock 已由 {current_owner} 持有。", "status": self.status()}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 返回被谁占用；如果没有这行代码，用户无法排查锁冲突。
                recovered_stale_owner = current_owner  # 新增代码+Phase31ComputerUseLockAbortEvidence: 记录被恢复的旧 owner；如果没有这行代码，事后审计不知道谁被接管。
                recovered_stale_acquired_at = str(current_state.get("acquired_at", ""))  # 新增代码+Phase31ComputerUseLockAbortEvidence: 记录旧锁获取时间；如果没有这行代码，无法判断旧锁残留多久。
                recovered_at = phase30_lock_timestamp()  # 新增代码+Phase31ComputerUseLockAbortEvidence: 记录恢复发生时间；如果没有这行代码，状态无法说明何时接管。
            next_state = {"locked": True, "owner_session_id": requested_session_id, "owner_label": str(owner_label or ""), "owner_pid": os.getpid(), "acquired_at": phase30_lock_timestamp(), "metadata": dict(metadata or {}), "recovered_stale_owner_session_id": recovered_stale_owner, "recovered_stale_acquired_at": recovered_stale_acquired_at, "recovered_at": recovered_at}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 构造新的 owner 状态并保留陈旧恢复证据；如果没有这行代码，锁文件缺少可审计信息。
            atomic_write_json(self.state_path, next_state)  # 修改代码+Phase31ComputerUseLockAbortEvidence: 原子写入锁状态；如果没有这行代码，崩溃时可能留下半个 JSON。
            reason = "desktop control lock 已从陈旧 owner 恢复并获取。" if recovered_stale_owner else "desktop control lock 已获取。"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 根据是否恢复生成清晰原因；如果没有这行代码，调用方无法区分普通取锁和恢复取锁。
            return {"acquired": True, "reason": reason, "status": self.status()}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 返回获取成功和最新状态；如果没有这行代码，调用方无法确认锁已生效。
    # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，acquire 到此结束；如果没有这个结束标记，读者不容易看出持锁流程边界。

    def release(self, session_id: str) -> dict[str, Any]:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，释放当前会话持有的桌面控制锁；如果没有这段函数，锁会长期残留阻塞后续安全动作。
        requested_session_id = str(session_id or "").strip()  # 修改代码+Phase31ComputerUseLockAbortEvidence: 清理释放者会话 id；如果没有这行代码，空白释放请求可能误操作状态。
        with FileLock(self.mutex_path, timeout_seconds=self.timeout_seconds):  # 修改代码+Phase31ComputerUseLockAbortEvidence: 用文件互斥锁保护释放流程；如果没有这行代码，释放和获取可能交错造成 owner 丢失。
            current_state = self._read_lock_state()  # 修改代码+Phase31ComputerUseLockAbortEvidence: 读取当前锁状态；如果没有这行代码，无法判断谁持锁。
            current_owner = str(current_state.get("owner_session_id", ""))  # 修改代码+Phase31ComputerUseLockAbortEvidence: 提取当前 owner；如果没有这行代码，无法防止别人释放你的锁。
            if current_state.get("locked") and current_owner and current_owner != requested_session_id:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 拒绝非 owner 释放；如果没有这行代码，另一个会话可以偷释放桌面锁。
                return {"released": False, "reason": f"desktop control lock 由 {current_owner} 持有，当前会话不能释放。", "status": self.status()}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 返回释放失败原因；如果没有这行代码，锁冲突难以定位。
            atomic_write_json(self.state_path, {"locked": False, "owner_session_id": "", "released_at": phase30_lock_timestamp(), "released_by": requested_session_id})  # 修改代码+Phase31ComputerUseLockAbortEvidence: 原子写入释放状态；如果没有这行代码，后续 session 会继续看到旧 owner。
            return {"released": True, "reason": "desktop control lock 已释放。", "status": self.status()}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 返回释放成功；如果没有这行代码，调用方无法确认释放结果。
    # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，release 到此结束；如果没有这个结束标记，读者不容易看出释放流程边界。

    def has_lock(self, session_id: str) -> bool:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，判断某会话是否当前持锁；如果没有这段函数，controller 要手写易错的状态字段判断。
        status = self.status()  # 修改代码+Phase31ComputerUseLockAbortEvidence: 读取规范化锁状态；如果没有这行代码，判断可能绕过 abort 或坏状态容错。
        return bool(status.get("locked") and status.get("owner_session_id") == str(session_id or "").strip() and not status.get("stale"))  # 修改代码+Phase31ComputerUseLockAbortEvidence: 返回是否由指定会话持有且未陈旧；如果没有这行代码，陈旧 owner 仍可能被视为有效控制者。
    # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，has_lock 到此结束；如果没有这个结束标记，读者不容易看出持锁判断边界。

    def request_abort(self, reason: str, requested_by: str = "") -> dict[str, Any]:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，写入急停标记；如果没有这段函数，用户或验收无法阻止下一次桌面动作。
        with FileLock(self.mutex_path, timeout_seconds=self.timeout_seconds):  # 修改代码+Phase31ComputerUseLockAbortEvidence: 用同一互斥锁保护 abort 写入；如果没有这行代码，abort 和 lock 写入可能交错损坏。
            abort_state = {"requested": True, "reason": str(reason or ""), "requested_by": str(requested_by or ""), "requested_at": phase30_lock_timestamp()}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 构造急停状态；如果没有这行代码，abort 文件缺少原因和时间。
            atomic_write_json(self.abort_path, abort_state)  # 修改代码+Phase31ComputerUseLockAbortEvidence: 原子写入 abort 文件；如果没有这行代码，急停标记可能半写入。
            return self.status()  # 修改代码+Phase31ComputerUseLockAbortEvidence: 返回包含 abort 的最新状态；如果没有这行代码，调用方无法确认急停已生效。
    # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，request_abort 到此结束；如果没有这个结束标记，读者不容易看出急停写入边界。

    def clear_abort(self, cleared_by: str = "") -> dict[str, Any]:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，清除急停标记；如果没有这段函数，abort 一旦触发就无法恢复动作测试或人工控制。
        with FileLock(self.mutex_path, timeout_seconds=self.timeout_seconds):  # 修改代码+Phase31ComputerUseLockAbortEvidence: 用互斥锁保护清除过程；如果没有这行代码，清除和写入可能互相覆盖。
            atomic_write_json(self.abort_path, {"requested": False, "reason": "", "cleared_by": str(cleared_by or ""), "cleared_at": phase30_lock_timestamp()})  # 修改代码+Phase31ComputerUseLockAbortEvidence: 写入已清除状态；如果没有这行代码，controller 会继续认为 abort 仍有效。
            return self.status()  # 修改代码+Phase31ComputerUseLockAbortEvidence: 返回最新状态；如果没有这行代码，调用方无法确认急停已清除。
    # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，clear_abort 到此结束；如果没有这个结束标记，读者不容易看出清除边界。

    def abort_status(self) -> dict[str, Any]:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，读取急停状态摘要；如果没有这段函数，controller 需要知道 abort 文件内部格式。
        status = self.status()  # 修改代码+Phase31ComputerUseLockAbortEvidence: 复用统一状态输出；如果没有这行代码，abort 摘要可能和 status 不一致。
        return {"requested": bool(status.get("abort_requested")), "reason": str(status.get("abort_reason", "")), "requested_at": str(status.get("abort_requested_at", ""))}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 返回最小 abort 信息；如果没有这行代码，controller 难以构造清晰拒绝原因。
    # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，abort_status 到此结束；如果没有这个结束标记，读者不容易看出急停摘要边界。

    def is_abort_requested(self) -> bool:  # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，判断是否处于急停状态；如果没有这段函数，controller 会重复读取和解释 abort 状态。
        return bool(self.abort_status().get("requested"))  # 修改代码+Phase31ComputerUseLockAbortEvidence: 返回 abort 是否已请求；如果没有这行代码，下一次动作无法快速判断是否该阻断。
    # 修改代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，is_abort_requested 到此结束；如果没有这个结束标记，读者不容易看出急停判断边界。
