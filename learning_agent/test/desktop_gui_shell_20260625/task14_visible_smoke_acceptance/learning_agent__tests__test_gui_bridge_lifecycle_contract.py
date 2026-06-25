import json  # 新增代码+DesktopGUILifecycleTest：解析 GUI bridge JSON 响应；如果没有这行，测试只能比较原始字节。
import tempfile  # 新增代码+DesktopGUILifecycleTest：创建隔离工作区；如果没有这行，测试会污染真实项目 memory。
import threading  # 新增代码+DesktopGUILifecycleTest：后台运行 HTTP server；如果没有这行，测试请求会被 serve_forever 阻塞。
import time  # 新增代码+DesktopGUILifecycleTest：等待后台 turn 状态事件；如果没有这行，异步 worker 测试无法轮询结果。
import unittest  # 新增代码+DesktopGUILifecycleTest：使用 unittest 让蓝图命令能发现测试；如果没有这行，测试不会被标准 runner 执行。
import urllib.error  # 新增代码+DesktopGUILifecycleTest：捕获 HTTPError；如果没有这行，409 busy 场景无法读取结构化错误。
import urllib.request  # 新增代码+DesktopGUILifecycleTest：使用标准库请求本地 bridge；如果没有这行，测试需要额外依赖。
from pathlib import Path  # 新增代码+DesktopGUILifecycleTest：使用 Path 管理临时工作区；如果没有这行，路径拼接容易出错。


class GuiBridgeLifecycleContractTests(unittest.TestCase):  # 新增代码+DesktopGUILifecycleTest：测试类段开始，锁定 GUI turn 生命周期；如果没有这个类，unittest 不会执行这些合同。
    def _start_server(self, workspace: Path):  # 新增代码+DesktopGUILifecycleTest：helper 段开始，启动带 token 的测试 server；如果没有这个 helper，每个测试都要重复端口和线程逻辑。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUILifecycleTest：导入 GUI bridge server 工厂；如果没有这行，测试无法启动被测服务。

        server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUILifecycleTest：绑定随机端口并固定 token；如果没有这行，测试容易端口冲突或 token 不稳定。
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUILifecycleTest：创建后台服务线程；如果没有这行，HTTP 请求无法同时发出。
        thread.start()  # 新增代码+DesktopGUILifecycleTest：启动 server 线程；如果没有这行，urllib 会连接失败。
        return server  # 新增代码+DesktopGUILifecycleTest：返回 server 供测试拼 URL 和关闭；如果没有这行，调用方拿不到端口。
    # 新增代码+DesktopGUILifecycleTest：helper 段结束，_start_server 到此结束；如果没有边界说明，初学者不易看出它只负责启动服务。

    def _url(self, server, path: str) -> str:  # 新增代码+DesktopGUILifecycleTest：helper 段开始，拼接 server URL；如果没有这段，随机端口读取会散落各处。
        host, port = server.server_address  # 新增代码+DesktopGUILifecycleTest：读取真实监听地址；如果没有这行，端口 0 场景无法请求。
        return f"http://{host}:{port}{path}"  # 新增代码+DesktopGUILifecycleTest：返回完整 URL；如果没有这行，urllib 没有目标地址。
    # 新增代码+DesktopGUILifecycleTest：helper 段结束，_url 到此结束；如果没有边界说明，初学者不易看出它只负责拼 URL。

    def _post_json(self, server, path: str, payload: dict[str, object]) -> dict[str, object]:  # 新增代码+DesktopGUILifecycleTest：helper 段开始，发送 JSON POST；如果没有这段，每个测试都要重复编码和 header。
        request = urllib.request.Request(self._url(server, path), data=json.dumps(payload).encode("utf-8"), method="POST", headers={"Content-Type": "application/json", "X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUILifecycleTest：构造带 token 的 JSON 请求；如果没有这行，安全门禁会拒绝请求。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUILifecycleTest：发送请求并读取响应；如果没有这行，测试不会真正触发 endpoint。
            return json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUILifecycleTest：返回 JSON 对象；如果没有这行，断言无法检查字段。
    # 新增代码+DesktopGUILifecycleTest：helper 段结束，_post_json 到此结束；如果没有边界说明，初学者不易看出它只负责 POST。

    def _get_json(self, server, path: str) -> dict[str, object]:  # 新增代码+DesktopGUILifecycleTest：helper 段开始，发送带 token 的 GET；如果没有这段，事件和 resume 请求会重复写法。
        request = urllib.request.Request(self._url(server, path), headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUILifecycleTest：构造带 token 的 GET 请求；如果没有这行，安全 endpoint 会返回 401。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUILifecycleTest：发送 GET 请求；如果没有这行，测试不会读取 bridge 状态。
            return json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUILifecycleTest：解析 JSON 响应；如果没有这行，断言无法读取字段。
    # 新增代码+DesktopGUILifecycleTest：helper 段结束，_get_json 到此结束；如果没有边界说明，初学者不易看出它只负责 GET。

    def _wait_for_event(self, server, event_type: str, turn_id: str, timeout_seconds: float = 3.0) -> dict[str, object]:  # 新增代码+DesktopGUILifecycleTest：helper 段开始，等待异步事件出现；如果没有这段，测试会和后台 worker 抢时序。
        deadline = time.time() + timeout_seconds  # 新增代码+DesktopGUILifecycleTest：计算等待截止时间；如果没有这行，失败测试可能无限等待。
        while time.time() < deadline:  # 新增代码+DesktopGUILifecycleTest：在超时前循环轮询；如果没有这行，异步事件可能还没写入就断言失败。
            payload = self._get_json(server, "/v1/gui/events?since_sequence=0&limit=100")  # 新增代码+DesktopGUILifecycleTest：读取事件流；如果没有这行，测试无法观察后台状态。
            for event in payload["events"]:  # 新增代码+DesktopGUILifecycleTest：遍历事件列表；如果没有这行，无法找到目标事件。
                if event["event_type"] == event_type and event["turn_id"] == turn_id:  # 新增代码+DesktopGUILifecycleTest：匹配事件类型和 turn；如果没有这行，其他 turn 的事件可能误过。
                    return event  # 新增代码+DesktopGUILifecycleTest：返回目标事件；如果没有这行，调用方拿不到证据。
            time.sleep(0.03)  # 新增代码+DesktopGUILifecycleTest：短暂等待再轮询；如果没有这行，测试会空转占用 CPU。
        self.fail(f"等待事件失败：{event_type} turn={turn_id}")  # 新增代码+DesktopGUILifecycleTest：超时后明确失败；如果没有这行，测试会静默返回 None。
    # 新增代码+DesktopGUILifecycleTest：helper 段结束，_wait_for_event 到此结束；如果没有边界说明，初学者不易看出它只负责等待事件。

    def test_message_busy_cancel_retry_and_resume_lifecycle(self) -> None:  # 新增代码+DesktopGUILifecycleTest：测试段开始，覆盖发送、busy、取消、重试和恢复；如果没有这段，GUI 核心 run 生命周期没有合同保护。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUILifecycleTest：创建临时工作区；如果没有这行，测试会写入真实 memory。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUILifecycleTest：启动 GUI bridge；如果没有这行，测试没有目标服务。
            try:  # 新增代码+DesktopGUILifecycleTest：确保 server 最终关闭；如果没有这行，失败时端口会泄漏。
                first = self._post_json(server, "/v1/gui/messages", {"conversation_id": "default", "prompt": "请分析当前项目", "client_request_id": "client_a"})  # 新增代码+DesktopGUILifecycleTest：发送第一条 GUI prompt；如果没有这行，无法创建 turn。
                self.assertIs(first["ok"], True)  # 新增代码+DesktopGUILifecycleTest：确认提交成功；如果没有这行，失败响应可能误过。
                self.assertEqual(first["status"], "queued")  # 新增代码+DesktopGUILifecycleTest：确认初始状态为 queued；如果没有这行，生命周期起点可能漂移。
                self.assertIn("events_after_sequence", first)  # 新增代码+DesktopGUILifecycleTest：确认返回事件游标；如果没有这行，前端无法从正确位置轮询。
                turn_id = str(first["turn_id"])  # 新增代码+DesktopGUILifecycleTest：保存 turn_id；如果没有这行，后续取消和事件匹配没有目标。

                with self.assertRaises(urllib.error.HTTPError) as busy_error:  # 新增代码+DesktopGUILifecycleTest：断言第二个并发请求被拒；如果没有这行，bridge 可能无限排队。
                    self._post_json(server, "/v1/gui/messages", {"conversation_id": "default", "prompt": "第二个任务"})  # 新增代码+DesktopGUILifecycleTest：运行中再次提交；如果没有这行，无法验证 agent_busy。
                busy_payload = json.loads(busy_error.exception.read().decode("utf-8"))  # 新增代码+DesktopGUILifecycleTest：读取 busy JSON；如果没有这行，无法确认错误码。
                self.assertEqual(busy_error.exception.code, 409)  # 新增代码+DesktopGUILifecycleTest：确认 HTTP 409；如果没有这行，前端无法可靠识别忙碌。
                self.assertEqual(busy_payload["code"], "agent_busy")  # 新增代码+DesktopGUILifecycleTest：确认结构化错误码；如果没有这行，UI 无法给出明确提示。

                cancel = self._post_json(server, f"/v1/gui/turns/{turn_id}/cancel", {})  # 新增代码+DesktopGUILifecycleTest：请求取消当前 turn；如果没有这行，无法验证 cancel endpoint。
                self.assertEqual(cancel["status"], "cancelling")  # 新增代码+DesktopGUILifecycleTest：确认取消请求进入 cancelling；如果没有这行，按钮状态可能不准。
                self.assertIn("events_after_sequence", cancel)  # 新增代码+DesktopGUILifecycleTest：确认取消响应也有事件游标；如果没有这行，前端无法继续轮询。
                self._wait_for_event(server, "gui_turn_cancel_requested", turn_id)  # 新增代码+DesktopGUILifecycleTest：确认取消请求事件写入；如果没有这行，时间线看不到用户动作。
                self._wait_for_event(server, "gui_turn_cancelled", turn_id)  # 新增代码+DesktopGUILifecycleTest：确认取消终态事件写入；如果没有这行，GUI 可能永远显示 cancelling。

                retry = self._post_json(server, f"/v1/gui/turns/{turn_id}/retry", {})  # 新增代码+DesktopGUILifecycleTest：重试已取消 turn；如果没有这行，无法验证 retry endpoint。
                self.assertIs(retry["ok"], True)  # 新增代码+DesktopGUILifecycleTest：确认重试成功；如果没有这行，错误响应可能误过。
                self.assertNotEqual(retry["turn_id"], turn_id)  # 新增代码+DesktopGUILifecycleTest：确认重试创建新 turn；如果没有这行，事件可能和旧 turn 混在一起。
                self.assertIn("events_after_sequence", retry)  # 新增代码+DesktopGUILifecycleTest：确认重试响应有事件游标；如果没有这行，前端无法增量读取新 turn。
                retry_turn_id = str(retry["turn_id"])  # 新增代码+DesktopGUILifecycleTest：保存新 turn id；如果没有这行，后续完成事件无法匹配。
                self._wait_for_event(server, "gui_turn_retried", retry_turn_id)  # 新增代码+DesktopGUILifecycleTest：确认重试事件写入；如果没有这行，时间线无法解释新 turn 来源。
                self._wait_for_event(server, "gui_turn_completed", retry_turn_id)  # 新增代码+DesktopGUILifecycleTest：确认重试最终完成；如果没有这行，GUI 无法展示最终回答。
                sidebar = self._get_json(server, "/v1/gui/sessions")  # 新增代码+DesktopGUISessionListTest：读取 GUI 侧栏会话列表；如果没有这行代码，最近对话是否来自真实 GUI 会话无法验证。
                self.assertGreaterEqual(len(sidebar["sessions"]), 1)  # 新增代码+DesktopGUISessionListTest：确认至少有一条 GUI 会话；如果没有这行代码，侧栏空列表回归不会被发现。
                self.assertEqual(sidebar["sessions"][0]["session_id"], "default")  # 新增代码+DesktopGUISessionListTest：确认默认会话进入侧栏；如果没有这行代码，恢复入口可能指向错误会话。
                self.assertIn("请分析当前项目", sidebar["sessions"][0]["title"])  # 新增代码+DesktopGUISessionListTest：确认用户 prompt 变成可读标题；如果没有这行代码，侧栏仍可能显示难懂 id。

                resume = self._post_json(server, "/v1/gui/sessions/default/resume", {})  # 新增代码+DesktopGUILifecycleTest：恢复默认 session；如果没有这行，无法验证窗口重启后的会话恢复合同。
                self.assertIs(resume["ok"], True)  # 新增代码+DesktopGUILifecycleTest：确认恢复成功；如果没有这行，失败响应可能误过。
                self.assertEqual(resume["session_id"], "default")  # 新增代码+DesktopGUILifecycleTest：确认恢复目标 session；如果没有这行，UI 可能恢复错会话。
                self.assertGreaterEqual(len(resume["messages"]), 2)  # 新增代码+DesktopGUILifecycleTest：确认恢复包含历史消息；如果没有这行，重启后对话会丢失。
                self.assertIn("events_after_sequence", resume)  # 新增代码+DesktopGUILifecycleTest：确认恢复响应有事件游标；如果没有这行，前端恢复后不知道从哪继续轮询。
            finally:  # 新增代码+DesktopGUILifecycleTest：清理 server；如果没有这行，后台线程和端口可能残留。
                server.shutdown()  # 新增代码+DesktopGUILifecycleTest：停止 serve_forever；如果没有这行，测试进程可能挂住。
                server.server_close()  # 新增代码+DesktopGUILifecycleTest：释放 socket；如果没有这行，Windows 端口可能短时间占用。
    # 新增代码+DesktopGUILifecycleTest：测试段结束，核心生命周期合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_tool_smoke_prompt_emits_visible_tool_card_event(self) -> None:  # 新增代码+DesktopGUIToolSmokeTest：测试方法开始，验证 GUI 工具卡片 smoke hook；如果没有这段测试，主线程工具卡片可能退化成无法稳定验收。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIToolSmokeTest：创建隔离工作区；如果没有这行代码，工具事件测试会污染真实项目 memory。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUIToolSmokeTest：启动带 token 的 GUI bridge；如果没有这行代码，测试无法走真实 HTTP 生命周期。
            try:  # 新增代码+DesktopGUIToolSmokeTest：保护 server 清理；如果没有这行代码，失败时后台端口可能残留。
                first = self._post_json(server, "/v1/gui/messages", {"conversation_id": "default", "prompt": "__tool__ 请显示一个工具事件卡片"})  # 新增代码+DesktopGUIToolSmokeTest：提交工具 smoke prompt；如果没有这行代码，后端不会产生 tool_call_started。
                turn_id = str(first["turn_id"])  # 新增代码+DesktopGUIToolSmokeTest：保存 turn id；如果没有这行代码，事件和本轮运行无法对齐。
                tool_event = self._wait_for_event(server, "tool_call_started", turn_id)  # 新增代码+DesktopGUIToolSmokeTest：等待工具事件；如果没有这行代码，测试只验证了提交成功而没验证工具卡片来源。
                completed_event = self._wait_for_event(server, "gui_turn_completed", turn_id)  # 新增代码+DesktopGUIToolSmokeTest：等待最终完成；如果没有这行代码，工具 hook 可能破坏正常完成路径。
            finally:  # 新增代码+DesktopGUIToolSmokeTest：清理 server；如果没有这行代码，测试失败会留下后台服务。
                server.shutdown()  # 新增代码+DesktopGUIToolSmokeTest：停止 serve_forever；如果没有这行代码，测试进程可能挂住。
                server.server_close()  # 新增代码+DesktopGUIToolSmokeTest：释放 socket；如果没有这行代码，Windows 端口可能短时间占用。
        self.assertEqual(tool_event["payload"]["tool_name"], "smoke_tool")  # 新增代码+DesktopGUIToolSmokeTest：确认工具名可供 ThreadView 渲染；如果没有这行代码，工具卡片标题可能为空。
        self.assertEqual(tool_event["payload"]["summary"], "GUI 可见验收工具事件已写入。")  # 新增代码+DesktopGUIToolSmokeTest：确认工具摘要可读；如果没有这行代码，工具卡片正文可能没有人话说明。
        self.assertEqual(completed_event["payload"]["status"], "completed")  # 新增代码+DesktopGUIToolSmokeTest：确认工具 smoke 后仍正常完成；如果没有这行代码，工具事件可能误伤生命周期。
    # 新增代码+DesktopGUIToolSmokeTest：测试方法结束，工具卡片 smoke 合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_permission_prompt_emits_permission_event_and_deny_stays_failed(self) -> None:  # 新增代码+DesktopGUIPermissionSmokeTest：测试方法开始，验证 GUI prompt 触发权限弹窗事件和拒绝终态；如果没有这段测试，__permission__ smoke hook 可能退化成假 UI。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIPermissionSmokeTest：创建隔离工作区；如果没有这行代码，权限 smoke 测试会污染真实项目 memory。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUIPermissionSmokeTest：启动带 token 的 GUI bridge；如果没有这行代码，测试无法走真实 HTTP 生命周期。
            try:  # 新增代码+DesktopGUIPermissionSmokeTest：保护 server 清理；如果没有这行代码，失败时后台端口可能残留。
                first = self._post_json(server, "/v1/gui/messages", {"conversation_id": "default", "prompt": "__permission__ __permission_fast__ 请触发一个 GUI 权限请求"})  # 新增代码+DesktopGUIPermissionSmokeTest：提交权限 smoke prompt；如果没有这行代码，后端不会产生可见权限事件。
                turn_id = str(first["turn_id"])  # 新增代码+DesktopGUIPermissionSmokeTest：保存 turn id；如果没有这行代码，事件和决策请求无法定位同一轮。
                permission_event = self._wait_for_event(server, "permission_required", turn_id)  # 新增代码+DesktopGUIPermissionSmokeTest：等待真实权限请求事件；如果没有这行代码，测试只验证了提交成功而没验证弹窗来源。
                request_id = str(permission_event["payload"]["request_id"])  # 新增代码+DesktopGUIPermissionSmokeTest：读取权限 request id；如果没有这行代码，后续 deny endpoint 无法命中目标请求。
                denial = self._post_json(server, f"/v1/gui/permissions/{request_id}/decision", {"turn_id": turn_id, "decision": "deny", "reason": "测试拒绝 GUI 权限"})  # 新增代码+DesktopGUIPermissionSmokeTest：通过真实权限 endpoint 提交拒绝；如果没有这行代码，deny 按钮合同不会被覆盖。
                failed_event = self._wait_for_event(server, "gui_turn_failed", turn_id)  # 新增代码+DesktopGUIPermissionSmokeTest：等待拒绝后的 failed 事件；如果没有这行代码，worker 覆盖终态的问题可能漏检。
                events = self._get_json(server, "/v1/gui/events?since_sequence=0&limit=100")["events"]  # 新增代码+DesktopGUIPermissionSmokeTest：读取完整事件列表；如果没有这行代码，无法确认同一 turn 没有被改回 completed。
            finally:  # 新增代码+DesktopGUIPermissionSmokeTest：清理 server；如果没有这行代码，测试失败会留下后台服务。
                server.shutdown()  # 新增代码+DesktopGUIPermissionSmokeTest：停止 serve_forever；如果没有这行代码，测试进程可能挂住。
                server.server_close()  # 新增代码+DesktopGUIPermissionSmokeTest：释放 socket；如果没有这行代码，Windows 端口可能短时间占用。
        self.assertEqual(denial["status"], "denied")  # 新增代码+DesktopGUIPermissionSmokeTest：确认拒绝状态写入后端；如果没有这行代码，权限决策可能没有持久结果。
        self.assertEqual(failed_event["payload"]["status"], "failed")  # 新增代码+DesktopGUIPermissionSmokeTest：确认 failed 事件 payload 正确；如果没有这行代码，前端状态映射可能缺少事实。
        self.assertNotIn("gui_turn_completed", [event["event_type"] for event in events if event["turn_id"] == turn_id])  # 新增代码+DesktopGUIPermissionSmokeTest：确认拒绝后没有被覆盖成 completed；如果没有这行代码，治本修复可能退化。
    # 新增代码+DesktopGUIPermissionSmokeTest：测试方法结束，权限 smoke 合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


if __name__ == "__main__":  # 新增代码+DesktopGUILifecycleTest：允许直接运行本文件；如果没有这行，手动调试只能用模块命令。
    unittest.main()  # 新增代码+DesktopGUILifecycleTest：启动 unittest runner；如果没有这行，直接运行文件不会执行测试。
