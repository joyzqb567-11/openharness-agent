import json  # 新增代码+GuiV2StreamContractTest：解析 V2 事件 fallback JSON 和 SSE data；如果没有这一行，测试只能看原始字节。
import tempfile  # 新增代码+GuiV2StreamContractTest：创建隔离工作区；如果没有这一行，事件测试会污染真实 memory/status。
import threading  # 新增代码+GuiV2StreamContractTest：后台启动本地 HTTP bridge；如果没有这一行，urllib 请求会阻塞。
import unittest  # 新增代码+GuiV2StreamContractTest：使用 unittest 承载蓝图指定测试；如果没有这一行，测试不会被标准命令发现。
import urllib.request  # 新增代码+GuiV2StreamContractTest：使用标准库请求本地 bridge；如果没有这一行，测试需要额外 HTTP 依赖。
from pathlib import Path  # 新增代码+GuiV2StreamContractTest：用 Path 构造临时 workspace；如果没有这一行，状态目录拼接容易出错。


class GuiV2StreamContractTest(unittest.TestCase):  # 新增代码+GuiV2StreamContractTest：测试类段开始，锁定桌面 GUI V2 事件流合同；如果没有这个类，SSE 和断线恢复不会被自动验证。
    def _start_server(self, workspace: Path):  # 新增代码+GuiV2StreamContractTest：helper 段开始，启动带 token 的 GUI bridge；如果没有这个 helper，每个 HTTP 测试都要重复线程代码。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+GuiV2StreamContractTest：导入 bridge server 工厂；如果没有这一行，测试无法启动真实路由。

        server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+GuiV2StreamContractTest：用随机端口启动测试 server；如果没有这一行，测试容易端口冲突。
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+GuiV2StreamContractTest：创建后台 server 线程；如果没有这一行，HTTP 请求无法和 server 同时运行。
        thread.start()  # 新增代码+GuiV2StreamContractTest：启动后台 server；如果没有这一行，后续请求会连接失败。
        return server  # 新增代码+GuiV2StreamContractTest：返回 server 供测试读取端口和关闭；如果没有这一行，调用方无法清理。
    # 新增代码+GuiV2StreamContractTest：helper 段结束，_start_server 到此结束；如果没有这个边界说明，用户不容易看出启动范围。

    def _url(self, server, path: str) -> str:  # 新增代码+GuiV2StreamContractTest：helper 段开始，拼接随机端口 URL；如果没有这段，测试会重复读取 server_address。
        host, port = server.server_address  # 新增代码+GuiV2StreamContractTest：读取 server 实际监听地址；如果没有这一行，随机端口无法用于请求。
        return f"http://{host}:{port}{path}"  # 新增代码+GuiV2StreamContractTest：返回完整 URL；如果没有这一行，urllib 无法请求目标路由。
    # 新增代码+GuiV2StreamContractTest：helper 段结束，_url 到此结束；如果没有这个边界说明，用户不容易看出 URL 拼接范围。

    def test_sse_format_helpers_use_event_stream_wire_format(self) -> None:  # 新增代码+GuiV2StreamContractTest：函数段开始，验证 SSE 字节格式；如果没有这段测试，前端 EventSource 可能读不到事件。
        from learning_agent.app.gui_stream import format_sse_comment, format_sse_event  # 新增代码+GuiV2StreamContractTest：导入待实现 SSE helper；如果没有这一行，测试没有被测对象。

        event = {"event_id": "event_1", "kind": "heartbeat", "payload": {"status": "idle"}}  # 新增代码+GuiV2StreamContractTest：构造最小 V2 事件；如果没有这一行，SSE helper 没有输入样本。
        self.assertEqual(b": hello\n\n", format_sse_comment("hello"))  # 新增代码+GuiV2StreamContractTest：确认 comment 使用 SSE 冒号格式和真实换行；如果没有这一行，保活注释可能被浏览器当坏数据。
        raw_event = format_sse_event(event).decode("utf-8")  # 新增代码+GuiV2StreamContractTest：把 SSE 事件字节转成文本；如果没有这一行，后续无法检查字段。
        self.assertIn("id: event_1", raw_event)  # 新增代码+GuiV2StreamContractTest：确认 SSE id 存在；如果没有这一行，重连时浏览器无法带 Last-Event-ID 语义。
        self.assertIn("event: heartbeat", raw_event)  # 新增代码+GuiV2StreamContractTest：确认 SSE event 名存在；如果没有这一行，前端无法按事件类型监听。
        self.assertIn("data: ", raw_event)  # 新增代码+GuiV2StreamContractTest：确认 SSE data 行存在；如果没有这一行，EventSource message 没有 JSON 内容。
    # 新增代码+GuiV2StreamContractTest：函数段结束，test_sse_format_helpers_use_event_stream_wire_format 到此结束；如果没有这个边界说明，用户不容易看出格式测试范围。

    def test_select_events_after_returns_heartbeat_when_no_business_event_exists(self) -> None:  # 新增代码+GuiV2StreamContractTest：函数段开始，验证空事件流也会有 heartbeat；如果没有这段测试，GUI 断线后可能一直静默。
        from learning_agent.app.gui_stream import select_events_after  # 新增代码+GuiV2StreamContractTest：导入事件选择 helper；如果没有这一行，测试无法验证空流行为。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiV2StreamContractTest：创建临时 workspace；如果没有这一行，状态读取会碰真实项目。
            events = select_events_after(Path(directory), since_sequence=10, limit=25)  # 新增代码+GuiV2StreamContractTest：在无事件目录中读取增量事件；如果没有这一行，后续没有 heartbeat 样本。
        self.assertEqual(1, len(events))  # 新增代码+GuiV2StreamContractTest：确认空流返回一条 heartbeat；如果没有这一行，UI 可能看起来卡死。
        self.assertEqual("heartbeat", events[0]["kind"])  # 新增代码+GuiV2StreamContractTest：确认事件类型是 heartbeat；如果没有这一行，前端无法区分业务事件和保活。
        self.assertEqual(10, events[0]["sequence"])  # 新增代码+GuiV2StreamContractTest：确认 heartbeat 不越过 last seen sequence；如果没有这一行，重连可能跳过真实业务事件。
    # 新增代码+GuiV2StreamContractTest：函数段结束，test_select_events_after_returns_heartbeat_when_no_business_event_exists 到此结束；如果没有这个边界说明，用户不容易看出 heartbeat 合同范围。

    def test_v2_events_fallback_reconnects_after_last_seen_sequence(self) -> None:  # 新增代码+GuiV2StreamContractTest：函数段开始，验证 `/v2/gui/events` fallback 从游标后恢复；如果没有这段测试，断线重连会重复旧事件。
        from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+GuiV2StreamContractTest：导入真实事件 store；如果没有这一行，测试无法准备可过滤事件。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiV2StreamContractTest：创建临时 workspace；如果没有这一行，测试会污染真实状态流。
            workspace = Path(directory)  # 新增代码+GuiV2StreamContractTest：转换成 Path；如果没有这一行，状态路径语义不清楚。
            store = StatusEventStore(workspace / "memory" / "status")  # 新增代码+GuiV2StreamContractTest：创建临时状态事件 store；如果没有这一行，bridge 没有事件可读。
            first = store.append("gui_turn_running", {"status": "running"}, session_id="session_a", run_id="run_a", turn_id="turn_a")  # 新增代码+GuiV2StreamContractTest：写入第一条事件；如果没有这一行，游标过滤没有基准。
            second = store.append("gui_turn_completed", {"answer": "done"}, session_id="session_a", run_id="run_a", turn_id="turn_a")  # 新增代码+GuiV2StreamContractTest：写入第二条事件；如果没有这一行，重连没有目标事件。
            server = self._start_server(workspace)  # 新增代码+GuiV2StreamContractTest：启动 bridge；如果没有这一行，无法测试 HTTP fallback。
            try:  # 新增代码+GuiV2StreamContractTest：保护 server 清理；如果没有这一行，失败时端口会残留。
                request = urllib.request.Request(self._url(server, f"/v2/gui/events?since_sequence={first.sequence}&limit=10"), headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+GuiV2StreamContractTest：构造带 since_sequence 的 V2 fallback 请求；如果没有这一行，无法验证断线恢复。
                with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+GuiV2StreamContractTest：请求 fallback 端点；如果没有这一行，无法得到 HTTP 响应。
                    payload = json.loads(response.read().decode("utf-8"))  # 新增代码+GuiV2StreamContractTest：解析 JSON 响应；如果没有这一行，无法断言事件字段。
            finally:  # 新增代码+GuiV2StreamContractTest：清理 server；如果没有这一行，后台线程可能残留。
                server.shutdown()  # 新增代码+GuiV2StreamContractTest：停止 server；如果没有这一行，测试进程可能等待。
                server.server_close()  # 新增代码+GuiV2StreamContractTest：释放 socket；如果没有这一行，端口可能残留占用。
        self.assertIs(payload["ok"], True)  # 新增代码+GuiV2StreamContractTest：确认 fallback 响应成功；如果没有这一行，错误响应可能误过。
        self.assertEqual([second.sequence], [event["sequence"] for event in payload["events"]])  # 新增代码+GuiV2StreamContractTest：确认只返回 last seen 后的事件；如果没有这一行，重连会重复旧消息。
        self.assertEqual("message_completed", payload["events"][0]["kind"])  # 新增代码+GuiV2StreamContractTest：确认旧 status 事件被映射成 V2 kind；如果没有这一行，前端 V2 状态机无法消费。
    # 新增代码+GuiV2StreamContractTest：函数段结束，test_v2_events_fallback_reconnects_after_last_seen_sequence 到此结束；如果没有这个边界说明，用户不容易看出 fallback 合同范围。

    def test_v2_stream_route_returns_sse_with_query_token_for_eventsource(self) -> None:  # 新增代码+GuiV2StreamContractTest：函数段开始，验证 SSE route 支持 query token；如果没有这段测试，EventSource 无法携带认证。
        from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+GuiV2StreamContractTest：导入真实事件 store；如果没有这一行，stream route 没有业务事件样本。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiV2StreamContractTest：创建临时 workspace；如果没有这一行，测试会污染真实事件流。
            workspace = Path(directory)  # 新增代码+GuiV2StreamContractTest：转换成 Path；如果没有这一行，状态路径不清楚。
            StatusEventStore(workspace / "memory" / "status").append("gui_turn_running", {"status": "running"}, session_id="session_a", run_id="run_a", turn_id="turn_a")  # 新增代码+GuiV2StreamContractTest：写入可流式返回的事件；如果没有这一行，stream 只能返回 heartbeat。
            server = self._start_server(workspace)  # 新增代码+GuiV2StreamContractTest：启动 bridge；如果没有这一行，无法测试 SSE route。
            try:  # 新增代码+GuiV2StreamContractTest：保护 server 清理；如果没有这一行，失败时端口会残留。
                with urllib.request.urlopen(self._url(server, "/v2/gui/events/stream?since_sequence=0&token=test-token"), timeout=5) as response:  # 新增代码+GuiV2StreamContractTest：用 query token 请求 SSE；如果没有这一行，无法模拟 EventSource 限制。
                    content_type = response.getheader("Content-Type")  # 新增代码+GuiV2StreamContractTest：读取响应类型；如果没有这一行，无法确认 text/event-stream。
                    raw_text = response.read().decode("utf-8")  # 新增代码+GuiV2StreamContractTest：读取 SSE 响应体；如果没有这一行，无法检查事件内容。
            finally:  # 新增代码+GuiV2StreamContractTest：清理 server；如果没有这一行，后台线程可能残留。
                server.shutdown()  # 新增代码+GuiV2StreamContractTest：停止 server；如果没有这一行，测试进程可能等待。
                server.server_close()  # 新增代码+GuiV2StreamContractTest：释放 socket；如果没有这一行，端口可能残留占用。
        self.assertIn("text/event-stream", content_type)  # 新增代码+GuiV2StreamContractTest：确认 SSE content type；如果没有这一行，浏览器不会按事件流处理。
        self.assertIn("event: turn_started", raw_text)  # 新增代码+GuiV2StreamContractTest：确认 stream 返回 V2 事件名；如果没有这一行，前端监听不到事件。
        self.assertIn('"turn_id": "turn_a"', raw_text)  # 新增代码+GuiV2StreamContractTest：确认 SSE data 保留 turn_id；如果没有这一行，前端无法关联消息。
    # 新增代码+GuiV2StreamContractTest：函数段结束，test_v2_stream_route_returns_sse_with_query_token_for_eventsource 到此结束；如果没有这个边界说明，用户不容易看出 SSE route 合同范围。
# 新增代码+GuiV2StreamContractTest：测试类段结束，GuiV2StreamContractTest 到此结束；如果没有这个边界说明，用户不容易看出本文件只测 V2 stream 合同。


if __name__ == "__main__":  # 新增代码+GuiV2StreamContractTest：允许直接运行测试文件；如果没有这一行，手动排查时不会启动 unittest。
    unittest.main()  # 新增代码+GuiV2StreamContractTest：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行测试。
