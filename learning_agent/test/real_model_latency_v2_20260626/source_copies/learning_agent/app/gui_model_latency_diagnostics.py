from __future__ import annotations  # 新增代码+ModelLatencyDiagnostics：启用延迟类型注解；如果没有这一行，类方法类型引用在旧解释顺序下更脆弱。

import threading  # 新增代码+ModelLatencyDiagnostics：导入后台线程工具；如果没有这一行，diagnostics 只能同步阻塞发送路径。
import time  # 新增代码+ModelLatencyDiagnostics：导入时间函数用于 TTL 和耗时；如果没有这一行，缓存无法判断是否过期。
from dataclasses import dataclass  # 新增代码+ModelLatencyDiagnostics：导入 dataclass 管理快照；如果没有这一行，诊断状态只能用松散字典传来传去。
from typing import Callable  # 新增代码+ModelLatencyDiagnostics：导入回调类型；如果没有这一行，doctor_runner 和 clock 的契约不清楚。


DiagnosticRunner = Callable[[], str]  # 新增代码+ModelLatencyDiagnostics：定义诊断命令回调类型；如果没有这一行，缓存不知道后台刷新应调用什么。
Clock = Callable[[], float]  # 新增代码+ModelLatencyDiagnostics：定义时钟回调类型；如果没有这一行，TTL 测试只能依赖真实时间。


@dataclass(frozen=True)  # 新增代码+ModelLatencyDiagnostics：让诊断快照不可变；如果没有这一行，返回给 GUI 的状态可能被外部误改。
class TransportDiagnosticsSnapshot:  # 新增代码+ModelLatencyDiagnostics：类段开始，承载低敏 transport 诊断摘要；如果没有这段，状态字段会散落在多个 dict 里。
    status: str  # 新增代码+ModelLatencyDiagnostics：保存诊断状态，例如 diagnostic_unknown 或 diagnostic_ready；如果没有这一行，前端无法判断诊断可信度。
    websocket_ok: bool | None  # 新增代码+ModelLatencyDiagnostics：保存 WebSocket 是否可用；如果没有这一行，慢 fallback 的根因不可见。
    http_reachable: bool | None  # 新增代码+ModelLatencyDiagnostics：保存 HTTP 后端是否可达；如果没有这一行，用户不知道 fallback 是否可能成功。
    expected_slow_fallback: bool  # 新增代码+ModelLatencyDiagnostics：保存是否预期慢 fallback；如果没有这一行，GUI 无法解释等待不是假死。
    checked_at: float | None  # 新增代码+ModelLatencyDiagnostics：保存实际诊断完成时间；如果没有这一行，TTL 和 stale 提示没有依据。
    stale: bool  # 新增代码+ModelLatencyDiagnostics：保存当前返回值是否过期；如果没有这一行，用户无法区分旧诊断和新诊断。
    refresh_in_progress: bool  # 新增代码+ModelLatencyDiagnostics：保存后台刷新是否正在跑；如果没有这一行，UI 无法提示“正在更新诊断”。
    error_kind: str = ""  # 新增代码+ModelLatencyDiagnostics：保存低敏错误类别；如果没有这一行，doctor 超时只能显示模糊失败。
    message: str = ""  # 新增代码+ModelLatencyDiagnostics：保存低敏说明；如果没有这一行，诊断状态对用户不够可读。

    def to_dict(self) -> dict[str, object]:  # 新增代码+ModelLatencyDiagnostics：函数段开始，把快照转成 JSON 友好字典；如果没有这段，HTTP/GUI 层不能直接序列化。
        return {  # 新增代码+ModelLatencyDiagnostics：返回稳定字段集合；如果没有这一行，前端字段会随实现漂移。
            "status": self.status,  # 新增代码+ModelLatencyDiagnostics：写入诊断状态；如果没有这一行，前端无法判断 unknown/ready。
            "websocket_ok": self.websocket_ok,  # 新增代码+ModelLatencyDiagnostics：写入 WebSocket 状态；如果没有这一行，transport 根因会丢失。
            "http_reachable": self.http_reachable,  # 新增代码+ModelLatencyDiagnostics：写入 HTTP 可达性；如果没有这一行，fallback 可行性会丢失。
            "expected_slow_fallback": self.expected_slow_fallback,  # 新增代码+ModelLatencyDiagnostics：写入慢 fallback 预期；如果没有这一行，UI 无法解释慢等待。
            "checked_at": self.checked_at,  # 新增代码+ModelLatencyDiagnostics：写入完成时间；如果没有这一行，stale 判断无法展示。
            "stale": self.stale,  # 新增代码+ModelLatencyDiagnostics：写入是否过期；如果没有这一行，用户可能误信旧状态。
            "refresh_in_progress": self.refresh_in_progress,  # 新增代码+ModelLatencyDiagnostics：写入后台刷新状态；如果没有这一行，用户不知道诊断是否正在更新。
            "error_kind": self.error_kind,  # 新增代码+ModelLatencyDiagnostics：写入低敏错误类别；如果没有这一行，timeout 等原因无法统计。
            "message": self.message,  # 新增代码+ModelLatencyDiagnostics：写入低敏说明；如果没有这一行，前端只能显示生硬状态码。
        }  # 新增代码+ModelLatencyDiagnostics：字典结束；如果没有这一行，Python 语法不完整。
    # 新增代码+ModelLatencyDiagnostics：函数段结束，TransportDiagnosticsSnapshot.to_dict 到此结束；如果没有边界说明，用户不容易看出序列化范围。
# 新增代码+ModelLatencyDiagnostics：类段结束，TransportDiagnosticsSnapshot 到此结束；如果没有边界说明，用户不容易看出快照范围。


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:  # 新增代码+ModelLatencyDiagnostics：函数段开始，统一做大小写不敏感匹配；如果没有这段，parser 会重复写易错字符串判断。
    lowered = text.lower()  # 新增代码+ModelLatencyDiagnostics：把输入转成小写；如果没有这一行，大小写变化会导致诊断解析失败。
    return any(needle.lower() in lowered for needle in needles)  # 新增代码+ModelLatencyDiagnostics：任一关键词命中即返回真；如果没有这一行，调用方无法复用匹配逻辑。
# 新增代码+ModelLatencyDiagnostics：函数段结束，_contains_any 到此结束；如果没有边界说明，用户不容易看出匹配范围。


def parse_transport_diagnostics(raw_text: str, *, checked_at: float | None = None) -> TransportDiagnosticsSnapshot:  # 新增代码+ModelLatencyDiagnostics：函数段开始，把 doctor 文本解析成低敏快照；如果没有这段，GUI 只能展示原始日志且可能泄露信息。
    text = str(raw_text or "")  # 新增代码+ModelLatencyDiagnostics：把未知输入收敛为字符串；如果没有这一行，None 会让解析器抛异常。
    websocket_timeout = _contains_any(text, ("Responses WebSocket timed out", "websocket timed out", "stream disconnected"))  # 新增代码+ModelLatencyDiagnostics：识别 WebSocket 超时或断流；如果没有这一行，慢调用根因不会被标出。
    websocket_ok = False if websocket_timeout else (True if _contains_any(text, ("websocket ok", "websocket reachable")) else None)  # 新增代码+ModelLatencyDiagnostics：推导 WebSocket 状态；如果没有这一行，状态只能停在未知。
    http_reachable = True if _contains_any(text, ("backend-api/ reachable", "backend api reachable", "https fallback may still work", "http reachable")) else None  # 新增代码+ModelLatencyDiagnostics：推导 HTTP 可达性；如果没有这一行，fallback 能否继续无法显示。
    if _contains_any(text, ("backend-api/ unreachable", "http unreachable", "https fallback failed")):  # 新增代码+ModelLatencyDiagnostics：识别 HTTP 不可达；如果没有这一行，失败 fallback 可能被误判可用。
        http_reachable = False  # 新增代码+ModelLatencyDiagnostics：明确 HTTP 不可达；如果没有这一行，用户会误以为 HTTPS fallback 可继续。
    expected_slow_fallback = bool(websocket_timeout and http_reachable is not False)  # 新增代码+ModelLatencyDiagnostics：WebSocket 超时且 HTTP 未失败时预期慢 fallback；如果没有这一行，GUI 无法解释为何继续等待。
    status = "diagnostic_ready" if text.strip() else "diagnostic_unknown"  # 新增代码+ModelLatencyDiagnostics：有文本就表示诊断完成；如果没有这一行，空诊断和正常诊断无法区分。
    message = "WebSocket 超时，可能正在走较慢 HTTPS fallback。" if expected_slow_fallback else "Transport 诊断已更新。"  # 新增代码+ModelLatencyDiagnostics：生成低敏说明；如果没有这一行，前端需要理解底层字段组合。
    return TransportDiagnosticsSnapshot(status=status, websocket_ok=websocket_ok, http_reachable=http_reachable, expected_slow_fallback=expected_slow_fallback, checked_at=checked_at, stale=False, refresh_in_progress=False, message=message)  # 新增代码+ModelLatencyDiagnostics：返回解析后的快照；如果没有这一行，调用方拿不到诊断结果。
# 新增代码+ModelLatencyDiagnostics：函数段结束，parse_transport_diagnostics 到此结束；如果没有边界说明，用户不容易看出解析范围。


def unknown_transport_diagnostics(*, refresh_in_progress: bool = False, error_kind: str = "", message: str = "Transport 诊断暂时未知。") -> TransportDiagnosticsSnapshot:  # 新增代码+ModelLatencyDiagnostics：函数段开始，创建 unknown 快照；如果没有这段，no-cache 和 timeout 会重复拼字典。
    return TransportDiagnosticsSnapshot(status="diagnostic_unknown", websocket_ok=None, http_reachable=None, expected_slow_fallback=False, checked_at=None, stale=True, refresh_in_progress=refresh_in_progress, error_kind=error_kind, message=message)  # 新增代码+ModelLatencyDiagnostics：返回未知状态；如果没有这一行，无缓存时可能误报 ready。
# 新增代码+ModelLatencyDiagnostics：函数段结束，unknown_transport_diagnostics 到此结束；如果没有边界说明，用户不容易看出未知状态范围。


class TransportDiagnosticsCache:  # 新增代码+ModelLatencyDiagnostics：类段开始，管理异步 transport 诊断缓存；如果没有这段，send-message 可能同步运行 doctor 而变慢。
    def __init__(self, doctor_runner: DiagnosticRunner, *, ttl_seconds: float = 300.0, clock: Clock | None = None) -> None:  # 新增代码+ModelLatencyDiagnostics：函数段开始，配置后台诊断运行器和 TTL；如果没有这段，缓存没有刷新来源和过期策略。
        self._doctor_runner = doctor_runner  # 新增代码+ModelLatencyDiagnostics：保存真实或测试 doctor runner；如果没有这一行，后台线程不知道该执行什么。
        self._ttl_seconds = float(ttl_seconds)  # 新增代码+ModelLatencyDiagnostics：保存缓存有效期；如果没有这一行，过期判断没有依据。
        self._clock = clock or time.time  # 新增代码+ModelLatencyDiagnostics：保存时钟回调；如果没有这一行，测试无法稳定推进时间。
        self._lock = threading.Lock()  # 新增代码+ModelLatencyDiagnostics：保护快照和刷新状态；如果没有这一行，并发 send 可能启动多个 doctor。
        self._snapshot: TransportDiagnosticsSnapshot | None = None  # 新增代码+ModelLatencyDiagnostics：保存最近诊断结果；如果没有这一行，缓存每次都像首次运行。
        self._refresh_thread: threading.Thread | None = None  # 新增代码+ModelLatencyDiagnostics：保存当前后台刷新线程；如果没有这一行，无法避免重复刷新。
    # 新增代码+ModelLatencyDiagnostics：函数段结束，TransportDiagnosticsCache.__init__ 到此结束；如果没有边界说明，用户不容易看出缓存字段范围。

    def _is_refreshing_unlocked(self) -> bool:  # 新增代码+ModelLatencyDiagnostics：函数段开始，在锁内判断是否已有后台刷新；如果没有这段，get_snapshot 会重复创建线程。
        return self._refresh_thread is not None and self._refresh_thread.is_alive()  # 新增代码+ModelLatencyDiagnostics：返回线程存活状态；如果没有这一行，刷新去重无法工作。
    # 新增代码+ModelLatencyDiagnostics：函数段结束，TransportDiagnosticsCache._is_refreshing_unlocked 到此结束；如果没有边界说明，用户不容易看出刷新判断范围。

    def _snapshot_is_fresh_unlocked(self, snapshot: TransportDiagnosticsSnapshot) -> bool:  # 新增代码+ModelLatencyDiagnostics：函数段开始，在锁内判断快照是否新鲜；如果没有这段，TTL 逻辑会散落在 get_snapshot。
        if snapshot.checked_at is None:  # 新增代码+ModelLatencyDiagnostics：没有完成时间的快照永远不算新鲜；如果没有这一行，unknown 可能被长期当成有效缓存。
            return False  # 新增代码+ModelLatencyDiagnostics：返回不新鲜；如果没有这一行，过期判断会继续计算 None。
        return (self._clock() - snapshot.checked_at) <= self._ttl_seconds  # 新增代码+ModelLatencyDiagnostics：比较当前时间和 TTL；如果没有这一行，缓存不会过期。
    # 新增代码+ModelLatencyDiagnostics：函数段结束，TransportDiagnosticsCache._snapshot_is_fresh_unlocked 到此结束；如果没有边界说明，用户不容易看出 TTL 判断范围。

    def _with_runtime_flags(self, snapshot: TransportDiagnosticsSnapshot, *, stale: bool, refresh_in_progress: bool) -> TransportDiagnosticsSnapshot:  # 新增代码+ModelLatencyDiagnostics：函数段开始，复制快照并覆盖运行态标记；如果没有这段，返回 stale 状态会修改原缓存。
        return TransportDiagnosticsSnapshot(status=snapshot.status, websocket_ok=snapshot.websocket_ok, http_reachable=snapshot.http_reachable, expected_slow_fallback=snapshot.expected_slow_fallback, checked_at=snapshot.checked_at, stale=stale, refresh_in_progress=refresh_in_progress, error_kind=snapshot.error_kind, message=snapshot.message)  # 新增代码+ModelLatencyDiagnostics：返回带运行态的新快照；如果没有这一行，调用方拿不到正确 stale/refresh 标记。
    # 新增代码+ModelLatencyDiagnostics：函数段结束，TransportDiagnosticsCache._with_runtime_flags 到此结束；如果没有边界说明，用户不容易看出快照复制范围。

    def _refresh_worker(self) -> None:  # 新增代码+ModelLatencyDiagnostics：函数段开始，后台执行 doctor 并更新缓存；如果没有这段，异步刷新线程没有工作内容。
        try:  # 新增代码+ModelLatencyDiagnostics：保护 doctor 调用；如果没有这一行，timeout 或外部错误会杀死线程且不更新缓存。
            raw_text = self._doctor_runner()  # 新增代码+ModelLatencyDiagnostics：运行诊断命令；如果没有这一行，缓存永远不会获得真实诊断。
            snapshot = parse_transport_diagnostics(raw_text, checked_at=self._clock())  # 新增代码+ModelLatencyDiagnostics：解析低敏诊断结果；如果没有这一行，原始日志可能进入 GUI。
        except TimeoutError:  # 新增代码+ModelLatencyDiagnostics：把 doctor 超时归类为未知诊断；如果没有这一行，超时会被误当用户 turn 失败。
            snapshot = unknown_transport_diagnostics(error_kind="doctor_timeout", message="Transport 诊断超时，已保留为未知状态。")  # 新增代码+ModelLatencyDiagnostics：生成 timeout unknown 快照；如果没有这一行，用户看不到低敏超时原因。
        except Exception:  # 新增代码+ModelLatencyDiagnostics：兜底捕获诊断异常；如果没有这一行，后台异常会泄露实现细节且缓存不更新。
            snapshot = unknown_transport_diagnostics(error_kind="diagnostic_error", message="Transport 诊断失败，已保留为未知状态。")  # 新增代码+ModelLatencyDiagnostics：生成安全失败快照；如果没有这一行，诊断错误可能影响用户消息发送。
        with self._lock:  # 新增代码+ModelLatencyDiagnostics：锁住缓存写入；如果没有这一行，并发读取可能看到半更新状态。
            self._snapshot = snapshot  # 新增代码+ModelLatencyDiagnostics：保存最新快照；如果没有这一行，后台刷新结果不会生效。
    # 新增代码+ModelLatencyDiagnostics：函数段结束，TransportDiagnosticsCache._refresh_worker 到此结束；如果没有边界说明，用户不容易看出后台刷新范围。

    def _start_refresh_unlocked(self) -> None:  # 新增代码+ModelLatencyDiagnostics：函数段开始，在锁内按需启动后台刷新；如果没有这段，no-cache 和 expired 分支会重复写线程逻辑。
        if self._is_refreshing_unlocked():  # 新增代码+ModelLatencyDiagnostics：已有刷新时不重复启动；如果没有这一行，高频发送会同时跑多个 doctor。
            return  # 新增代码+ModelLatencyDiagnostics：直接返回；如果没有这一行，刷新去重不会生效。
        self._refresh_thread = threading.Thread(target=self._refresh_worker, name="openharness-transport-diagnostics", daemon=True)  # 新增代码+ModelLatencyDiagnostics：创建后台线程；如果没有这一行，刷新仍会同步阻塞。
        self._refresh_thread.start()  # 新增代码+ModelLatencyDiagnostics：启动后台刷新；如果没有这一行，cache 永远停在 unknown。
    # 新增代码+ModelLatencyDiagnostics：函数段结束，TransportDiagnosticsCache._start_refresh_unlocked 到此结束；如果没有边界说明，用户不容易看出线程启动范围。

    def get_snapshot(self) -> TransportDiagnosticsSnapshot:  # 新增代码+ModelLatencyDiagnostics：函数段开始，立即返回缓存并必要时后台刷新；如果没有这段，send-message 没有非阻塞读取入口。
        with self._lock:  # 新增代码+ModelLatencyDiagnostics：锁住快照读取和刷新判断；如果没有这一行，并发读写会产生竞态。
            refreshing = self._is_refreshing_unlocked()  # 新增代码+ModelLatencyDiagnostics：记录当前是否正在刷新；如果没有这一行，返回值无法带 refresh_in_progress。
            if self._snapshot is None:  # 新增代码+ModelLatencyDiagnostics：处理首次无缓存；如果没有这一行，首次发送会尝试同步运行 doctor。
                self._start_refresh_unlocked()  # 新增代码+ModelLatencyDiagnostics：启动后台刷新但不等待；如果没有这一行，无缓存状态不会自动更新。
                return unknown_transport_diagnostics(refresh_in_progress=True)  # 新增代码+ModelLatencyDiagnostics：立即返回未知状态；如果没有这一行，发送路径会被诊断阻塞。
            fresh = self._snapshot_is_fresh_unlocked(self._snapshot)  # 新增代码+ModelLatencyDiagnostics：判断缓存是否仍在 TTL 内；如果没有这一行，过期状态无法触发刷新。
            if fresh:  # 新增代码+ModelLatencyDiagnostics：新鲜缓存直接返回；如果没有这一行，健康状态也会反复刷新。
                return self._with_runtime_flags(self._snapshot, stale=False, refresh_in_progress=refreshing)  # 新增代码+ModelLatencyDiagnostics：返回新鲜快照；如果没有这一行，前端无法拿到 cached ready 状态。
            self._start_refresh_unlocked()  # 新增代码+ModelLatencyDiagnostics：过期缓存启动后台刷新；如果没有这一行，旧状态永远不会更新。
            return self._with_runtime_flags(self._snapshot, stale=True, refresh_in_progress=True)  # 新增代码+ModelLatencyDiagnostics：立即返回旧值并标记 stale；如果没有这一行，过期时会阻塞等待新诊断。
    # 新增代码+ModelLatencyDiagnostics：函数段结束，TransportDiagnosticsCache.get_snapshot 到此结束；如果没有边界说明，用户不容易看出非阻塞读取范围。

    def wait_for_refresh(self, timeout: float = 5.0) -> bool:  # 新增代码+ModelLatencyDiagnostics：函数段开始，测试专用等待后台刷新；如果没有这段，单元测试只能 sleep 猜时间。
        with self._lock:  # 新增代码+ModelLatencyDiagnostics：读取当前刷新线程；如果没有这一行，线程引用可能被并发修改。
            thread = self._refresh_thread  # 新增代码+ModelLatencyDiagnostics：复制线程引用；如果没有这一行，锁外 join 可能拿不到目标线程。
        if thread is None:  # 新增代码+ModelLatencyDiagnostics：没有线程时说明无需等待；如果没有这一行，join None 会报错。
            return True  # 新增代码+ModelLatencyDiagnostics：返回已完成；如果没有这一行，调用方无法区分无刷新。
        thread.join(timeout=timeout)  # 新增代码+ModelLatencyDiagnostics：等待后台刷新结束；如果没有这一行，测试无法稳定观察最终缓存。
        return not thread.is_alive()  # 新增代码+ModelLatencyDiagnostics：返回是否完成；如果没有这一行，测试无法断言没有卡住。
    # 新增代码+ModelLatencyDiagnostics：函数段结束，TransportDiagnosticsCache.wait_for_refresh 到此结束；如果没有边界说明，用户不容易看出测试等待范围。
# 新增代码+ModelLatencyDiagnostics：类段结束，TransportDiagnosticsCache 到此结束；如果没有边界说明，用户不容易看出缓存职责范围。
