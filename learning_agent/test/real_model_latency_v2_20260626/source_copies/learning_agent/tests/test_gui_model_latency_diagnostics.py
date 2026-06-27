import threading  # 新增代码+ModelLatencyDiagnosticsTest：导入事件同步工具；如果没有这一行，非阻塞刷新测试只能靠 sleep 猜时间。
import time  # 新增代码+ModelLatencyDiagnosticsTest：导入计时工具；如果没有这一行，测试无法证明 get_snapshot 没有同步阻塞。
import unittest  # 新增代码+ModelLatencyDiagnosticsTest：使用 unittest 承载诊断缓存契约；如果没有这一行，pytest 无法自动收集本文件。


class ManualClock:  # 新增代码+ModelLatencyDiagnosticsTest：类段开始，提供可控时间；如果没有这个类，TTL 过期测试会依赖真实等待 5 分钟。
    def __init__(self, value: float = 1000.0) -> None:  # 新增代码+ModelLatencyDiagnosticsTest：函数段开始，初始化当前时间；如果没有这段，测试无法设置初始时间。
        self.value = float(value)  # 新增代码+ModelLatencyDiagnosticsTest：保存当前模拟时间；如果没有这一行，时钟没有状态。
    # 新增代码+ModelLatencyDiagnosticsTest：函数段结束，ManualClock.__init__ 到此结束；如果没有边界说明，用户不容易看出时间状态范围。

    def __call__(self) -> float:  # 新增代码+ModelLatencyDiagnosticsTest：函数段开始，让实例可作为 clock 回调；如果没有这段，缓存不能直接调用 ManualClock。
        return self.value  # 新增代码+ModelLatencyDiagnosticsTest：返回当前模拟时间；如果没有这一行，TTL 判断没有输入。
    # 新增代码+ModelLatencyDiagnosticsTest：函数段结束，ManualClock.__call__ 到此结束；如果没有边界说明，用户不容易看出时钟读取范围。

    def advance(self, seconds: float) -> None:  # 新增代码+ModelLatencyDiagnosticsTest：函数段开始，推进模拟时间；如果没有这段，测试不能制造过期缓存。
        self.value += float(seconds)  # 新增代码+ModelLatencyDiagnosticsTest：增加当前时间；如果没有这一行，TTL 不会变化。
    # 新增代码+ModelLatencyDiagnosticsTest：函数段结束，ManualClock.advance 到此结束；如果没有边界说明，用户不容易看出时间推进范围。
# 新增代码+ModelLatencyDiagnosticsTest：类段结束，ManualClock 到此结束；如果没有边界说明，用户不容易看出测试时钟范围。


class GuiModelLatencyDiagnosticsTest(unittest.TestCase):  # 新增代码+ModelLatencyDiagnosticsTest：测试类段开始，锁定异步 transport 诊断缓存；如果没有这段，send-message 可能重新被 doctor 阻塞。
    def test_parse_transport_diagnostics_detects_websocket_timeout_and_http_fallback(self) -> None:  # 新增代码+ModelLatencyDiagnosticsTest：测试 parser 能识别慢 fallback；如果没有这段，stderr 证据无法变成 GUI 字段。
        from learning_agent.app.gui_model_latency_diagnostics import parse_transport_diagnostics  # 新增代码+ModelLatencyDiagnosticsTest：导入被测 parser；如果没有这一行，测试没有执行对象。

        raw_text = "Responses WebSocket timed out\nHTTPS fallback may still work\nhttps://chatgpt.com/backend-api/ reachable\n"  # 新增代码+ModelLatencyDiagnosticsTest：构造计划要求的 doctor 文本；如果没有这一行，parser 没有输入样本。
        snapshot = parse_transport_diagnostics(raw_text, checked_at=123.0).to_dict()  # 新增代码+ModelLatencyDiagnosticsTest：解析并转字典；如果没有这一行，后续断言没有结果。
        self.assertEqual(False, snapshot["websocket_ok"])  # 新增代码+ModelLatencyDiagnosticsTest：确认 WebSocket 超时被识别；如果没有这一行，慢调用根因可能丢失。
        self.assertEqual(True, snapshot["http_reachable"])  # 新增代码+ModelLatencyDiagnosticsTest：确认 HTTP fallback 可达；如果没有这一行，GUI 不知道 fallback 是否还能工作。
        self.assertEqual(True, snapshot["expected_slow_fallback"])  # 新增代码+ModelLatencyDiagnosticsTest：确认预期慢 fallback；如果没有这一行，用户仍会以为 GUI 假死。
    # 新增代码+ModelLatencyDiagnosticsTest：测试函数结束，test_parse_transport_diagnostics_detects_websocket_timeout_and_http_fallback 到此结束；如果没有边界说明，用户不容易看出 parser 覆盖范围。

    def test_no_cache_returns_unknown_immediately_and_starts_background_refresh(self) -> None:  # 新增代码+ModelLatencyDiagnosticsTest：测试首次无缓存不阻塞发送；如果没有这段，doctor 可能同步卡住用户 prompt。
        from learning_agent.app.gui_model_latency_diagnostics import TransportDiagnosticsCache  # 新增代码+ModelLatencyDiagnosticsTest：导入被测缓存；如果没有这一行，测试没有执行对象。

        release_runner = threading.Event()  # 新增代码+ModelLatencyDiagnosticsTest：创建阻塞 runner 的事件；如果没有这一行，无法证明 get_snapshot 不等待 runner 完成。
        runner_started = threading.Event()  # 新增代码+ModelLatencyDiagnosticsTest：创建 runner 已启动信号；如果没有这一行，测试无法确认后台刷新确实启动。

        def slow_runner() -> str:  # 新增代码+ModelLatencyDiagnosticsTest：函数段开始，模拟很慢的 doctor；如果没有这段，非阻塞行为没有压力样本。
            runner_started.set()  # 新增代码+ModelLatencyDiagnosticsTest：通知后台线程已经启动；如果没有这一行，测试无法确认刷新发生。
            release_runner.wait(timeout=5)  # 新增代码+ModelLatencyDiagnosticsTest：阻塞直到测试释放；如果没有这一行，get_snapshot 是否等待不明显。
            return "https://chatgpt.com/backend-api/ reachable"  # 新增代码+ModelLatencyDiagnosticsTest：返回成功诊断；如果没有这一行，刷新后没有 ready 状态。
        # 新增代码+ModelLatencyDiagnosticsTest：函数段结束，slow_runner 到此结束；如果没有边界说明，用户不容易看出慢 doctor 范围。

        cache = TransportDiagnosticsCache(slow_runner)  # 新增代码+ModelLatencyDiagnosticsTest：创建诊断缓存；如果没有这一行，被测对象不存在。
        started_at = time.monotonic()  # 新增代码+ModelLatencyDiagnosticsTest：记录调用开始时间；如果没有这一行，无法判断是否阻塞。
        snapshot = cache.get_snapshot()  # 新增代码+ModelLatencyDiagnosticsTest：首次读取无缓存状态；如果没有这一行，被测行为不会发生。
        elapsed_ms = int((time.monotonic() - started_at) * 1000)  # 新增代码+ModelLatencyDiagnosticsTest：计算调用耗时；如果没有这一行，非阻塞没有证据。
        self.assertLess(elapsed_ms, 500)  # 新增代码+ModelLatencyDiagnosticsTest：确认立即返回；如果没有这一行，同步 doctor 回归会漏掉。
        self.assertEqual("diagnostic_unknown", snapshot.status)  # 新增代码+ModelLatencyDiagnosticsTest：确认无缓存返回 unknown；如果没有这一行，首次状态可能误报 ready。
        self.assertTrue(snapshot.refresh_in_progress)  # 新增代码+ModelLatencyDiagnosticsTest：确认后台刷新已标记；如果没有这一行，UI 不知道诊断正在更新。
        self.assertTrue(runner_started.wait(timeout=2))  # 新增代码+ModelLatencyDiagnosticsTest：确认 runner 在后台启动；如果没有这一行，可能只是返回 unknown 不刷新。
        release_runner.set()  # 新增代码+ModelLatencyDiagnosticsTest：释放慢 runner；如果没有这一行，后台线程会一直阻塞。
        self.assertTrue(cache.wait_for_refresh(timeout=2))  # 新增代码+ModelLatencyDiagnosticsTest：等待后台刷新完成；如果没有这一行，后续断言可能抢跑。
        refreshed = cache.get_snapshot()  # 新增代码+ModelLatencyDiagnosticsTest：读取刷新后的缓存；如果没有这一行，无法证明后台结果落入缓存。
        self.assertEqual("diagnostic_ready", refreshed.status)  # 新增代码+ModelLatencyDiagnosticsTest：确认刷新后变 ready；如果没有这一行，后台刷新可能没有写缓存。
    # 新增代码+ModelLatencyDiagnosticsTest：测试函数结束，test_no_cache_returns_unknown_immediately_and_starts_background_refresh 到此结束；如果没有边界说明，用户不容易看出 no-cache 非阻塞范围。

    def test_expired_cache_returns_last_known_value_and_refreshes_in_background(self) -> None:  # 新增代码+ModelLatencyDiagnosticsTest：测试过期缓存返回旧值并后台刷新；如果没有这段，过期时可能同步阻塞发送。
        from learning_agent.app.gui_model_latency_diagnostics import TransportDiagnosticsCache  # 新增代码+ModelLatencyDiagnosticsTest：导入被测缓存；如果没有这一行，测试没有执行对象。

        clock = ManualClock()  # 新增代码+ModelLatencyDiagnosticsTest：创建可控时钟；如果没有这一行，TTL 过期测试不稳定。
        outputs = iter(["https://chatgpt.com/backend-api/ reachable", "Responses WebSocket timed out\nHTTPS fallback may still work\n"])  # 新增代码+ModelLatencyDiagnosticsTest：准备两次诊断输出；如果没有这一行，无法证明后台刷新替换旧值。
        cache = TransportDiagnosticsCache(lambda: next(outputs), clock=clock, ttl_seconds=300.0)  # 新增代码+ModelLatencyDiagnosticsTest：创建使用序列输出的缓存；如果没有这一行，被测对象不存在。
        first = cache.get_snapshot()  # 新增代码+ModelLatencyDiagnosticsTest：首次读取触发后台刷新；如果没有这一行，缓存没有初始值。
        self.assertEqual("diagnostic_unknown", first.status)  # 新增代码+ModelLatencyDiagnosticsTest：确认首次返回 unknown；如果没有这一行，no-cache 行为可能漂移。
        self.assertTrue(cache.wait_for_refresh(timeout=2))  # 新增代码+ModelLatencyDiagnosticsTest：等待第一次刷新；如果没有这一行，后续读取可能仍是 unknown。
        fresh = cache.get_snapshot()  # 新增代码+ModelLatencyDiagnosticsTest：读取新鲜缓存；如果没有这一行，无法确认初始刷新结果。
        self.assertFalse(fresh.stale)  # 新增代码+ModelLatencyDiagnosticsTest：确认新鲜缓存不标 stale；如果没有这一行，TTL 内也可能误报过期。
        clock.advance(301.0)  # 新增代码+ModelLatencyDiagnosticsTest：推进到 TTL 外；如果没有这一行，过期分支不会触发。
        expired = cache.get_snapshot()  # 新增代码+ModelLatencyDiagnosticsTest：读取过期缓存；如果没有这一行，被测行为不会发生。
        self.assertTrue(expired.stale)  # 新增代码+ModelLatencyDiagnosticsTest：确认旧值被标记过期；如果没有这一行，用户可能误信旧诊断。
        self.assertEqual(True, expired.http_reachable)  # 新增代码+ModelLatencyDiagnosticsTest：确认仍返回最后已知值；如果没有这一行，过期时可能丢掉有用诊断。
        self.assertTrue(expired.refresh_in_progress)  # 新增代码+ModelLatencyDiagnosticsTest：确认后台刷新已启动；如果没有这一行，过期值不会自动更新。
        self.assertTrue(cache.wait_for_refresh(timeout=2))  # 新增代码+ModelLatencyDiagnosticsTest：等待第二次刷新；如果没有这一行，后续断言可能抢跑。
        refreshed = cache.get_snapshot()  # 新增代码+ModelLatencyDiagnosticsTest：读取第二次刷新结果；如果没有这一行，无法证明过期刷新生效。
        self.assertEqual(False, refreshed.websocket_ok)  # 新增代码+ModelLatencyDiagnosticsTest：确认新诊断替换旧值；如果没有这一行，后台刷新可能没有写入缓存。
    # 新增代码+ModelLatencyDiagnosticsTest：测试函数结束，test_expired_cache_returns_last_known_value_and_refreshes_in_background 到此结束；如果没有边界说明，用户不容易看出过期缓存范围。

    def test_doctor_timeout_records_unknown_without_throwing_to_user_turn(self) -> None:  # 新增代码+ModelLatencyDiagnosticsTest：测试 doctor 超时只记录 unknown；如果没有这段，诊断超时可能错误中断用户消息。
        from learning_agent.app.gui_model_latency_diagnostics import TransportDiagnosticsCache  # 新增代码+ModelLatencyDiagnosticsTest：导入被测缓存；如果没有这一行，测试没有执行对象。

        cache = TransportDiagnosticsCache(lambda: (_ for _ in ()).throw(TimeoutError("doctor timeout")))  # 新增代码+ModelLatencyDiagnosticsTest：创建会抛 TimeoutError 的缓存；如果没有这一行，timeout 分支无法覆盖。
        first = cache.get_snapshot()  # 新增代码+ModelLatencyDiagnosticsTest：首次读取触发后台刷新；如果没有这一行，被测行为不会发生。
        self.assertEqual("diagnostic_unknown", first.status)  # 新增代码+ModelLatencyDiagnosticsTest：确认首次仍立即 unknown；如果没有这一行，timeout 可能同步冒泡。
        self.assertTrue(cache.wait_for_refresh(timeout=2))  # 新增代码+ModelLatencyDiagnosticsTest：等待后台 timeout 被捕获；如果没有这一行，后续断言可能抢跑。
        timeout_snapshot = cache.get_snapshot()  # 新增代码+ModelLatencyDiagnosticsTest：读取 timeout 后缓存；如果没有这一行，无法确认错误被记录。
        self.assertEqual("diagnostic_unknown", timeout_snapshot.status)  # 新增代码+ModelLatencyDiagnosticsTest：确认 timeout 仍是 unknown 状态；如果没有这一行，诊断错误可能伪装 ready。
        self.assertEqual("doctor_timeout", timeout_snapshot.error_kind)  # 新增代码+ModelLatencyDiagnosticsTest：确认低敏错误类别；如果没有这一行，超时不可统计。
    # 新增代码+ModelLatencyDiagnosticsTest：测试函数结束，test_doctor_timeout_records_unknown_without_throwing_to_user_turn 到此结束；如果没有边界说明，用户不容易看出 timeout 范围。
# 新增代码+ModelLatencyDiagnosticsTest：测试类段结束，GuiModelLatencyDiagnosticsTest 到此结束；如果没有边界说明，用户不容易看出本文件测试范围。


if __name__ == "__main__":  # 新增代码+ModelLatencyDiagnosticsTest：允许直接运行测试文件；如果没有这一行，手动排查时不会自动启动 unittest。
    unittest.main()  # 新增代码+ModelLatencyDiagnosticsTest：启动 unittest；如果没有这一行，直接 python 文件不会执行测试。
