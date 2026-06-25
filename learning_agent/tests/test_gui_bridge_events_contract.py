import json  # 新增代码+DesktopGUIEventsTest: 解析 HTTP 事件响应；如果没有这行代码，测试无法断言事件字段。
import tempfile  # 新增代码+DesktopGUIEventsTest: 创建临时工作区；如果没有这行代码，测试会污染真实 status 目录。
import threading  # 新增代码+DesktopGUIEventsTest: 后台启动 HTTP server；如果没有这行代码，事件端点请求会阻塞。
import unittest  # 新增代码+DesktopGUIEventsTest: 使用 unittest 让计划命令能发现测试；如果没有这行代码，事件合同不会执行。
import urllib.request  # 新增代码+DesktopGUIEventsTest: 使用标准库请求本地 bridge；如果没有这行代码，测试需要额外依赖。
from pathlib import Path  # 新增代码+DesktopGUIEventsTest: 使用 Path 构造临时工作区；如果没有这行代码，测试无法创建状态目录。


class GuiBridgeEventsContractTests(unittest.TestCase):  # 新增代码+DesktopGUIEventsTest: 测试类段开始，锁定 GUI 事件轮询合同；如果没有这个类，unittest 不会运行事件测试。
    def test_gui_events_payload_uses_status_event_store(self) -> None:  # 新增代码+DesktopGUIEventsTest: 验证 GUI 事件来自统一事件源；如果没有这段测试，前端可能读取旁路日志。
        from learning_agent.app.gui_bridge import build_gui_events_payload  # 新增代码+DesktopGUIEventsTest: 导入计划新增事件 helper；如果没有这行代码，测试无法锁定接口。
        from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DesktopGUIEventsTest: 使用真实状态事件 store；如果没有这行代码，测试不能证明复用事实源。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIEventsTest: 创建临时工作区；如果没有这行代码，事件会落到真实项目目录。
            workspace = Path(directory)  # 新增代码+DesktopGUIEventsTest: 转成 Path 工作区；如果没有这行代码，路径拼接会不清晰。
            store = StatusEventStore(workspace / "memory" / "status")  # 新增代码+DesktopGUIEventsTest: 创建临时事件 store；如果没有这行代码，事件没有落盘位置。
            store.append("status_probe", {"message": "hello"}, session_id="session_a", run_id="run_a", turn_id="turn_a")  # 新增代码+DesktopGUIEventsTest: 写入一条真实事件；如果没有这行代码，payload 只能返回空列表。

            payload = build_gui_events_payload(workspace, since_sequence=0, limit=10)  # 新增代码+DesktopGUIEventsTest: 读取 GUI 事件 payload；如果没有这行代码，无法验证事件接口。

        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIEventsTest: 确认响应成功；如果没有这行断言，失败响应可能误过。
        self.assertEqual(len(payload["events"]), 1)  # 新增代码+DesktopGUIEventsTest: 确认读到真实事件；如果没有这行断言，GUI 可能永远无进度。
        self.assertEqual(payload["events"][0]["event_type"], "status_probe")  # 新增代码+DesktopGUIEventsTest: 确认事件类型保留；如果没有这行断言，前端无法分类渲染。
        self.assertEqual(payload["events"][0]["turn_id"], "turn_a")  # 新增代码+DesktopGUIEventsTest: 确认 turn_id 顶层可见；如果没有这行断言，消息和事件无法关联。
    # 新增代码+DesktopGUIEventsTest: 测试方法结束；如果没有这个边界说明，用户不容易看出事件 helper 合同范围。

    def test_gui_events_http_route_reads_query(self) -> None:  # 新增代码+DesktopGUIEventsTest: 验证 HTTP 事件端点读取 query；如果没有这段测试，前端无法增量轮询。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIEventsTest: 导入 GUI bridge server；如果没有这行代码，测试无法启动事件端点。
        from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DesktopGUIEventsTest: 使用真实事件 store；如果没有这行代码，HTTP 测试无法准备事件。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIEventsTest: 创建临时工作区；如果没有这行代码，测试会污染真实项目。
            workspace = Path(directory)  # 新增代码+DesktopGUIEventsTest: 转成 Path 工作区；如果没有这行代码，事件路径不清楚。
            store = StatusEventStore(workspace / "memory" / "status")  # 新增代码+DesktopGUIEventsTest: 创建事件 store；如果没有这行代码，HTTP 端点没有测试数据。
            store.append("status_probe", {"message": "one"}, session_id="session_a", run_id="run_a", turn_id="turn_a")  # 新增代码+DesktopGUIEventsTest: 写入第一条事件；如果没有这行代码，since_sequence 无法过滤。
            second = store.append("status_probe", {"message": "two"}, session_id="session_a", run_id="run_a", turn_id="turn_b")  # 新增代码+DesktopGUIEventsTest: 写入第二条事件；如果没有这行代码，HTTP 响应没有目标事件。
            server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUIEventsTest: 启动随机端口 server；如果没有这行代码，测试可能端口冲突。
            try:  # 新增代码+DesktopGUIEventsTest: 确保 server 被关闭；如果没有这行代码，失败时端口会泄漏。
                thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIEventsTest: 创建后台线程；如果没有这行代码，urllib 请求会阻塞。
                thread.start()  # 新增代码+DesktopGUIEventsTest: 启动 server；如果没有这行代码，后续连接会失败。
                host, port = server.server_address  # 新增代码+DesktopGUIEventsTest: 读取真实地址；如果没有这行代码，请求不知道端口。
                request = urllib.request.Request(f"http://{host}:{port}/v1/gui/events?since_sequence=1&limit=50", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUIEventsTest: 构造事件请求；如果没有这行代码，无法验证 query 和 token。
                with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUIEventsTest: 请求事件端点；如果没有这行代码，无法验证 HTTP 路由。
                    payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIEventsTest: 解析响应 JSON；如果没有这行代码，无法断言字段。
            finally:  # 新增代码+DesktopGUIEventsTest: 清理 server；如果没有这行代码，后台线程可能残留。
                server.shutdown()  # 新增代码+DesktopGUIEventsTest: 停止 server；如果没有这行代码，测试进程可能等待。
                server.server_close()  # 新增代码+DesktopGUIEventsTest: 释放 socket；如果没有这行代码，端口可能残留占用。

        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIEventsTest: 确认 HTTP 事件响应成功；如果没有这行断言，错误响应可能误过。
        self.assertEqual(payload["events"][0]["sequence"], second.sequence)  # 新增代码+DesktopGUIEventsTest: 确认 since_sequence 过滤生效；如果没有这行断言，前端会重复旧事件。
        self.assertEqual(payload["since_sequence"], 1)  # 新增代码+DesktopGUIEventsTest: 确认游标回显；如果没有这行断言，前端无法记录轮询位置。
        self.assertEqual(payload["limit"], 50)  # 新增代码+DesktopGUIEventsTest: 确认 limit 回显；如果没有这行断言，前端无法确认服务端限制。
    # 新增代码+DesktopGUIEventsTest: 测试方法结束；如果没有这个边界说明，用户不容易看出 HTTP 事件合同范围。
# 新增代码+DesktopGUIEventsTest: 测试类段结束，GuiBridgeEventsContractTests 到此结束；如果没有这个边界说明，用户不容易看出本文件只测 GUI 事件合同。


if __name__ == "__main__":  # 新增代码+DesktopGUIEventsTest: 允许直接运行本测试文件；如果没有这行代码，手动调试时不会执行测试。
    unittest.main()  # 新增代码+DesktopGUIEventsTest: 启动 unittest；如果没有这行代码，直接运行文件不会进入测试 runner。
