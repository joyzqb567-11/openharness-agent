import json  # 新增代码+DesktopGUIBrowserWorkbenchTest：解析 HTTP 响应 JSON；如果没有这行，路由测试无法检查 payload。
import tempfile  # 新增代码+DesktopGUIBrowserWorkbenchTest：创建隔离工作区；如果没有这行，测试会污染真实 memory。
import threading  # 新增代码+DesktopGUIBrowserWorkbenchTest：后台启动 bridge server；如果没有这行，HTTP 测试会阻塞当前线程。
import unittest  # 新增代码+DesktopGUIBrowserWorkbenchTest：使用 unittest 承载后端合同测试；如果没有这行，测试不会被 unittest 收集。
import urllib.request  # 新增代码+DesktopGUIBrowserWorkbenchTest：使用标准库请求本地 HTTP route；如果没有这行，无法验证真实 bridge 端点。
from pathlib import Path  # 新增代码+DesktopGUIBrowserWorkbenchTest：使用 Path 管理临时目录；如果没有这行，路径拼接不清楚。

from learning_agent.app.gui_browser_control import build_gui_browser_action_payload, build_gui_browser_collection_payload, build_gui_browser_workbench_payload  # 新增代码+DesktopGUIBrowserWorkbenchTest：导入 Browser GUI 适配器；如果没有这行，测试没有被测目标。
from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DesktopGUIBrowserWorkbenchTest：复用真实状态事件 store；如果没有这行，console/network 摘要只能靠假对象。


class GuiBrowserWorkbenchContractTests(unittest.TestCase):  # 新增代码+DesktopGUIBrowserWorkbenchTest：测试类段开始，锁定 Browser 工作台 contract；如果没有这个类，Task 4 后端 payload 可能漂移。
    def _snapshot(self) -> dict[str, object]:  # 修改代码+DesktopGUIBrowserWorkbenchTest：helper 段开始，构造包含 browser provider 的快照；如果没有这段，测试会重复复杂字典。
        return {  # 修改代码+DesktopGUIBrowserWorkbenchTest：返回完整快照根对象；如果没有这行，后端 payload 没有测试输入。
            "browser": {  # 修改代码+DesktopGUIBrowserWorkbenchTest：放置 browser 快照区；如果没有这行，provider/tabs/recordings 层级会不清楚。
                "provider_status": {  # 修改代码+DesktopGUIBrowserWorkbenchTest：放置 provider_status 区；如果没有这行，GUI 轨道状态没有事实来源。
                    "providers": {  # 修改代码+DesktopGUIBrowserWorkbenchTest：放置 provider 集合；如果没有这行，可用轨道无法被断言。
                        "visible_chromium": {"available": True, "reason": "ready"},  # 修改代码+DesktopGUIBrowserWorkbenchTest：模拟可用 visible Chromium；如果没有这行，provider chip 断言没有对象。
                    },  # 修改代码+DesktopGUIBrowserWorkbenchTest：provider 集合结束；如果没有这行，字典语法不完整。
                    "chrome_extension": {"connected": True, "pending_command_count": 2},  # 修改代码+DesktopGUIBrowserWorkbenchTest：模拟扩展已连接和待命令数；如果没有这行，扩展摘要无法测试。
                    "native_host": {"connected": True},  # 修改代码+DesktopGUIBrowserWorkbenchTest：模拟 native host 已连接；如果没有这行，native host 字段无法测试。
                    "tabs": {  # 修改代码+DesktopGUIBrowserWorkbenchTest：放置 tab 摘要；如果没有这行，tab_count 和 active_tab 无法测试。
                        "tab_count": 2,  # 修改代码+DesktopGUIBrowserWorkbenchTest：模拟两个标签页；如果没有这行，tab 数量断言没有输入。
                        "active_tab": {"title": "OpenHarness", "url": "https://example.com/app", "url_host": "example.com"},  # 修改代码+DesktopGUIBrowserWorkbenchTest：模拟当前活跃 tab；如果没有这行，active target 兜底无法测试。
                        "tabs": [{"title": "OpenHarness", "url": "https://example.com/app", "active": True, "page_id": "page_1"}],  # 修改代码+DesktopGUIBrowserWorkbenchTest：模拟可显示 tab 列表；如果没有这行，tabs collection 没有列表输入。
                    },  # 修改代码+DesktopGUIBrowserWorkbenchTest：tab 摘要结束；如果没有这行，字典语法不完整。
                    "active_target": {"kind": "tab", "title": "OpenHarness", "url_host": "example.com"},  # 修改代码+DesktopGUIBrowserWorkbenchTest：模拟后端活跃目标；如果没有这行，active_target 断言没有输入。
                },  # 修改代码+DesktopGUIBrowserWorkbenchTest：provider_status 区结束；如果没有这行，browser 层级会闭合错误。
                "recordings": {"recording_count": 1, "latest": {"recording_id": "rec_a"}},  # 修改代码+DesktopGUIBrowserWorkbenchTest：把录制证据放在 browser 内；如果没有这行，replay/recording 摘要无法测试。
            },  # 修改代码+DesktopGUIBrowserWorkbenchTest：browser 区结束；如果没有这行，快照根字典会不完整。
            "status_events": [  # 修改代码+DesktopGUIBrowserWorkbenchTest：放置事件尾巴；如果没有这行，console/network/downloads 摘要没有来源。
                {"sequence": 7, "event_type": "tool_result_seen", "payload": {"tool_name": "mcp__browser_automation__browser_console", "message": "console error: boom", "entry_count": 3, "error_count": 1}},  # 修改代码+DesktopGUIBrowserWorkbenchTest：模拟 console 工具结果；如果没有这行，console 错误数无法断言。
                {"sequence": 8, "event_type": "tool_result_seen", "payload": {"tool_name": "mcp__browser_automation__browser_network", "message": "network 500 error", "entry_count": 4, "error_count": 2}},  # 修改代码+DesktopGUIBrowserWorkbenchTest：模拟 network 工具结果；如果没有这行，network 错误数无法断言。
                {"sequence": 9, "event_type": "tool_result_seen", "payload": {"tool_name": "mcp__browser_automation__browser_downloads", "message": "browser_downloads 最近 1 条记录", "count": 1}},  # 修改代码+DesktopGUIBrowserWorkbenchTest：模拟 downloads 工具结果；如果没有这行，下载记录数无法断言。
            ],  # 修改代码+DesktopGUIBrowserWorkbenchTest：事件列表结束；如果没有这行，列表语法不完整。
        }  # 修改代码+DesktopGUIBrowserWorkbenchTest：返回稳定快照；如果没有这行，payload 测试没有输入。
    # 新增代码+DesktopGUIBrowserWorkbenchTest：helper 段结束，_snapshot 到此结束；如果没有边界说明，用户不容易看出测试数据范围。

    def test_workbench_payload_contains_provider_tabs_console_network_downloads_and_replay(self) -> None:  # 新增代码+DesktopGUIBrowserWorkbenchTest：测试正常 workbench 字段；如果没有这段，GUI 可能只剩 provider 旧摘要。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIBrowserWorkbenchTest：创建临时 workspace；如果没有这行，测试可能读取真实项目事件。
            payload = build_gui_browser_workbench_payload(Path(directory), snapshot=self._snapshot())  # 新增代码+DesktopGUIBrowserWorkbenchTest：生成 Browser 工作台 payload；如果没有这行，后续没有断言对象。
        self.assertEqual(payload["providers"]["visible_chromium"]["available"], True)  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认 provider 状态保留；如果没有这行，浏览器轨道丢失不会被发现。
        self.assertEqual(payload["tabs"]["tab_count"], 2)  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认 tab 数量保留；如果没有这行，tabs summary 可能坏掉。
        self.assertEqual(payload["active_target"]["host"], "example.com")  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认活跃目标 host 可见；如果没有这行，用户难以诊断当前页面。
        self.assertEqual(payload["console"]["error_count"], 1)  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认 console 错误数可见；如果没有这行，console 摘要可能只显示空态。
        self.assertEqual(payload["network"]["error_count"], 2)  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认 network 错误数可见；如果没有这行，网络排查入口可能缺失。
        self.assertEqual(payload["downloads"]["entry_count"], 1)  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认 downloads 记录数可见；如果没有这行，下载摘要可能缺失。
        self.assertEqual(payload["recordings"]["recording_count"], 1)  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认录制证据摘要可见；如果没有这行，视觉回放证据可能丢失。
        self.assertEqual(payload["replay"]["mode"], "dry_run_only")  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认 replay 安全边界可见；如果没有这行，用户可能误以为回放会直接操作网页。
    # 新增代码+DesktopGUIBrowserWorkbenchTest：测试方法结束；如果没有边界说明，正常 payload 合同范围不清楚。

    def test_actions_record_safe_events_without_direct_browser_side_effects(self) -> None:  # 新增代码+DesktopGUIBrowserWorkbenchTest：测试 GUI 动作只记录安全事件；如果没有这段，open 可能绕过权限策略。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIBrowserWorkbenchTest：创建临时 workspace；如果没有这行，事件会落到真实项目。
            workspace = Path(directory)  # 新增代码+DesktopGUIBrowserWorkbenchTest：转换成 Path；如果没有这行，后续路径语义不清楚。
            refresh_payload = build_gui_browser_action_payload("refresh-status", workspace)  # 新增代码+DesktopGUIBrowserWorkbenchTest：执行刷新动作；如果没有这行，刷新响应没有覆盖。
            invalid_payload = build_gui_browser_action_payload("open", workspace, {"url": "javascript:alert(1)"})  # 新增代码+DesktopGUIBrowserWorkbenchTest：执行危险 URL 请求；如果没有这行，URL 校验没有覆盖。
            valid_payload = build_gui_browser_action_payload("open", workspace, {"url": "https://example.com/path?token=secret"})  # 新增代码+DesktopGUIBrowserWorkbenchTest：执行合法 URL 请求；如果没有这行，脱敏 origin 记录没有覆盖。
            events = [event.to_dict() for event in StatusEventStore(workspace / "memory" / "status").list_events()]  # 新增代码+DesktopGUIBrowserWorkbenchTest：读取真实事件流；如果没有这行，无法证明动作被审计。
        serialized = json.dumps(events, ensure_ascii=False)  # 新增代码+DesktopGUIBrowserWorkbenchTest：序列化事件用于查敏感 query；如果没有这行，泄漏断言要重复转换。
        self.assertEqual(refresh_payload["status"], "refreshed")  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认刷新状态；如果没有这行，刷新可能默默失败。
        self.assertEqual(invalid_payload["status"], "invalid_url")  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认危险 URL 被拒绝；如果没有这行，javascript URL 风险不会被发现。
        self.assertEqual(valid_payload["status"], "recorded")  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认合法 URL 只被记录；如果没有这行，GUI open 的安全边界不清楚。
        self.assertIn("https://example.com", serialized)  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认 origin 被审计；如果没有这行，用户无法复盘请求目标。
        self.assertNotIn("token=secret", serialized)  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认 query 未泄漏；如果没有这行，URL token 可能进入事件流。
    # 新增代码+DesktopGUIBrowserWorkbenchTest：测试方法结束；如果没有边界说明，动作安全合同范围不清楚。

    def test_collection_payload_and_http_routes_return_v2_shapes(self) -> None:  # 新增代码+DesktopGUIBrowserWorkbenchTest：测试 collection helper 和 bridge 路由；如果没有这段，前端可能收到 404 或字段漂移。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIBrowserWorkbenchTest：创建临时 workspace；如果没有这行，HTTP 测试会污染真实状态。
            workspace = Path(directory)  # 新增代码+DesktopGUIBrowserWorkbenchTest：转换成 Path；如果没有这行，请求构造不清楚。
            tabs_payload = build_gui_browser_collection_payload("tabs", workspace)  # 新增代码+DesktopGUIBrowserWorkbenchTest：直接验证 tabs helper；如果没有这行，collection helper 没有覆盖。
            from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIBrowserWorkbenchTest：导入 bridge server；如果没有这行，无法测试真实 HTTP 路由。
            server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUIBrowserWorkbenchTest：随机端口启动 server；如果没有这行，测试可能端口冲突。
            try:  # 新增代码+DesktopGUIBrowserWorkbenchTest：保护 server 清理；如果没有这行，失败时会残留端口。
                thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIBrowserWorkbenchTest：创建后台 server 线程；如果没有这行，urllib 会阻塞。
                thread.start()  # 新增代码+DesktopGUIBrowserWorkbenchTest：启动 HTTP server；如果没有这行，请求会连接失败。
                host, port = server.server_address  # 新增代码+DesktopGUIBrowserWorkbenchTest：读取随机端口；如果没有这行，测试不知道 URL。
                request = urllib.request.Request(f"http://{host}:{port}/v2/gui/browser/tabs", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUIBrowserWorkbenchTest：构造 tabs GET 请求；如果没有这行，GET 路由未覆盖。
                with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUIBrowserWorkbenchTest：发送 tabs 请求；如果没有这行，无法验证 HTTP payload。
                    http_tabs = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIBrowserWorkbenchTest：解析 tabs JSON；如果没有这行，断言没有对象。
                post_request = urllib.request.Request(f"http://{host}:{port}/v2/gui/browser/refresh-status", data=b"{}", method="POST", headers={"X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json"})  # 新增代码+DesktopGUIBrowserWorkbenchTest：构造刷新 POST 请求；如果没有这行，POST 路由未覆盖。
                with urllib.request.urlopen(post_request, timeout=5) as response:  # 新增代码+DesktopGUIBrowserWorkbenchTest：发送刷新请求；如果没有这行，无法验证动作路由。
                    http_refresh = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIBrowserWorkbenchTest：解析刷新 JSON；如果没有这行，断言没有对象。
            finally:  # 新增代码+DesktopGUIBrowserWorkbenchTest：无论断言是否失败都关闭 server；如果没有这行，后台线程可能残留。
                server.shutdown()  # 新增代码+DesktopGUIBrowserWorkbenchTest：停止 serve_forever；如果没有这行，测试进程可能挂住。
                server.server_close()  # 新增代码+DesktopGUIBrowserWorkbenchTest：释放 socket；如果没有这行，Windows 端口可能短时间占用。
        self.assertEqual(tabs_payload["kind"], "tabs")  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认 helper kind；如果没有这行，collection 形状可能漂移。
        self.assertEqual(http_tabs["schema_version"], 2)  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认 GET 路由为 V2；如果没有这行，前端兼容判断缺依据。
        self.assertEqual(http_refresh["action"], "refresh-status")  # 新增代码+DesktopGUIBrowserWorkbenchTest：确认 POST 动作名；如果没有这行，按钮响应可能错配。
    # 新增代码+DesktopGUIBrowserWorkbenchTest：测试方法结束；如果没有边界说明，HTTP 合同范围不清楚。
# 新增代码+DesktopGUIBrowserWorkbenchTest：测试类段结束，GuiBrowserWorkbenchContractTests 到此结束；如果没有边界说明，本文件职责不清楚。


if __name__ == "__main__":  # 新增代码+DesktopGUIBrowserWorkbenchTest：允许直接运行本文件；如果没有这行，手动调试时不会启动 unittest。
    unittest.main()  # 新增代码+DesktopGUIBrowserWorkbenchTest：启动 unittest；如果没有这行，直接运行文件不会执行测试。
