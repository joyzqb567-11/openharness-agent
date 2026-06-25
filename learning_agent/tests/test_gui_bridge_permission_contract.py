import json  # 新增代码+DesktopGUIPermissionsTest：解析 HTTP JSON 响应；如果没有这行，测试只能比较原始字节。
import tempfile  # 新增代码+DesktopGUIPermissionsTest：创建临时工作区；如果没有这行，权限测试会污染真实项目 memory。
import threading  # 新增代码+DesktopGUIPermissionsTest：后台运行标准库 HTTP server；如果没有这行，测试无法同时发请求。
import unittest  # 新增代码+DesktopGUIPermissionsTest：使用 unittest 合同测试；如果没有这行，蓝图要求的 unittest 命令无法发现测试。
import urllib.error  # 新增代码+DesktopGUIPermissionsTest：捕获 HTTPError；如果没有这行，404/409 合同无法断言响应体。
import urllib.request  # 新增代码+DesktopGUIPermissionsTest：发送本地 HTTP 请求；如果没有这行，测试需要额外网络依赖。
from pathlib import Path  # 新增代码+DesktopGUIPermissionsTest：使用 Path 管理临时 workspace；如果没有这行，状态 store 路径拼接更脆弱。


class GuiBridgePermissionContractTests(unittest.TestCase):  # 新增代码+DesktopGUIPermissionsTest：测试类段开始，承载 GUI bridge 权限合同；如果没有这个类，unittest 不会执行权限测试。
    def _post_json(self, url: str, token: str, payload: dict[str, object]) -> dict[str, object]:  # 新增代码+DesktopGUIPermissionsTest：辅助函数开始，发送带 token 的 JSON POST；如果没有这段，每个测试都要重复构造请求。
        raw_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # 新增代码+DesktopGUIPermissionsTest：编码 JSON body；如果没有这行，中文 reason 无法稳定传输。
        request = urllib.request.Request(url, data=raw_body, method="POST", headers={"Content-Type": "application/json", "X-OpenHarness-Desktop-Token": token})  # 新增代码+DesktopGUIPermissionsTest：构造带认证的 POST 请求；如果没有这行，bridge 会拒绝权限决策。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUIPermissionsTest：发送请求并读取响应；如果没有这行，无法验证真实 HTTP 路由。
            return json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIPermissionsTest：返回解析后的 JSON；如果没有这行，调用方无法断言字段。
    # 新增代码+DesktopGUIPermissionsTest：辅助函数结束，_post_json 到此结束；如果没有这个边界，初学者不易看出它只负责 HTTP POST。

    def _start_server(self, workspace: Path):  # 新增代码+DesktopGUIPermissionsTest：辅助函数开始，启动 GUI bridge server；如果没有这段，HTTP 测试无法复用启动逻辑。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIPermissionsTest：导入 server 构造器；如果没有这行，测试无法启动真实 bridge。
        server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUIPermissionsTest：使用随机端口创建 server；如果没有这行，测试可能端口冲突。
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIPermissionsTest：创建后台 server 线程；如果没有这行，urlopen 会阻塞等待 server。
        thread.start()  # 新增代码+DesktopGUIPermissionsTest：启动 server；如果没有这行，测试请求会连接失败。
        return server  # 新增代码+DesktopGUIPermissionsTest：返回 server 供测试登记权限和清理；如果没有这行，调用方拿不到端口。
    # 新增代码+DesktopGUIPermissionsTest：辅助函数结束，_start_server 到此结束；如果没有这个边界，初学者不易看出它只负责启动 server。

    def _permission_url(self, server: object, request_id: str) -> str:  # 新增代码+DesktopGUIPermissionsTest：辅助函数开始，构造权限决策 URL；如果没有这段，测试会重复拼动态路径。
        host, port = server.server_address  # 新增代码+DesktopGUIPermissionsTest：读取随机监听地址；如果没有这行，请求不知道发到哪里。
        return f"http://{host}:{port}/v1/gui/permissions/{request_id}/decision"  # 新增代码+DesktopGUIPermissionsTest：返回权限决策 endpoint；如果没有这行，调用方无法请求目标路由。
    # 新增代码+DesktopGUIPermissionsTest：辅助函数结束，_permission_url 到此结束；如果没有这个边界，初学者不易看出它只负责 URL 拼接。

    def _error_payload(self, error: urllib.error.HTTPError) -> dict[str, object]:  # 新增代码+DesktopGUIPermissionsTest：辅助函数开始，解析结构化错误响应；如果没有这段，404/409 只能断言状态码。
        return json.loads(error.read().decode("utf-8"))  # 新增代码+DesktopGUIPermissionsTest：解析错误响应体；如果没有这行，无法断言 code 字段。
    # 新增代码+DesktopGUIPermissionsTest：辅助函数结束，_error_payload 到此结束；如果没有这个边界，初学者不易看出它只负责错误解析。

    def test_permission_required_event_becomes_gui_turn_needs_permission(self) -> None:  # 新增代码+DesktopGUIPermissionsTest：测试方法开始，验证权限请求转成 GUI needs_permission 事件；如果没有这段测试，前端可能看不到权限等待状态。
        from learning_agent.app.gui_bridge import GuiRunManager  # 新增代码+DesktopGUIPermissionsTest：导入 run manager；如果没有这行，测试无法直接触发权限登记。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIPermissionsTest：创建临时 workspace；如果没有这行，事件会写进真实 memory。
            workspace = Path(directory)  # 新增代码+DesktopGUIPermissionsTest：转成 Path；如果没有这行，状态路径拼接不清楚。
            manager = GuiRunManager(workspace)  # 新增代码+DesktopGUIPermissionsTest：创建权限管理对象；如果没有这行，测试没有被测后端逻辑。
            payload = manager.record_permission_required("perm_visible", turn_id="turn_test", app_name="PowerShell", reason="需要运行命令", risk_summary="可能访问本机文件")  # 新增代码+DesktopGUIPermissionsTest：登记权限请求；如果没有这行，事件流不会产生权限事件。
            events = manager.event_store.list_events()  # 新增代码+DesktopGUIPermissionsTest：读取事件流；如果没有这行，无法确认 GUI 事件。
        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIPermissionsTest：确认登记成功；如果没有这行，失败 payload 可能误过。
        self.assertIn("gui_turn_needs_permission", [event.event_type for event in events])  # 新增代码+DesktopGUIPermissionsTest：确认生成 GUI needs_permission 事件；如果没有这行，权限请求无法驱动 GUI 状态。
        self.assertIn("permission_required", [event.event_type for event in events])  # 新增代码+DesktopGUIPermissionsTest：确认保留通用 permission_required 事件；如果没有这行，PermissionDialog 解析不到请求。
    # 新增代码+DesktopGUIPermissionsTest：测试方法结束；如果没有这个边界，初学者不易看出权限请求转换合同范围。

    def test_permission_decision_endpoint_accepts_approve(self) -> None:  # 新增代码+DesktopGUIPermissionsTest：测试方法开始，验证 approve 决策；如果没有这段测试，允许按钮可能只是前端假动作。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIPermissionsTest：创建临时 workspace；如果没有这行，HTTP 测试会污染真实状态。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUIPermissionsTest：启动 bridge server；如果没有这行，无法验证真实 endpoint。
            try:  # 新增代码+DesktopGUIPermissionsTest：保护 server 清理；如果没有这行，测试失败会泄漏端口。
                server.run_manager.record_permission_required("perm_approve", app_name="Chrome", reason="需要打开网页", risk_summary="低风险")  # 新增代码+DesktopGUIPermissionsTest：预置 pending 权限请求；如果没有这行，approve 会变成 unknown 404。
                payload = self._post_json(self._permission_url(server, "perm_approve"), "test-token", {"decision": "approve", "reason": "用户在 GUI 中点击允许"})  # 新增代码+DesktopGUIPermissionsTest：发送 approve 决策；如果没有这行，无法验证 endpoint 成功路径。
            finally:  # 新增代码+DesktopGUIPermissionsTest：清理 server；如果没有这行，后台线程可能继续运行。
                server.shutdown()  # 新增代码+DesktopGUIPermissionsTest：请求 server 退出；如果没有这行，测试结束后端口仍占用。
                server.server_close()  # 新增代码+DesktopGUIPermissionsTest：释放 socket；如果没有这行，Windows 上端口可能短时间占用。
        self.assertEqual(payload["decision"], "approve")  # 新增代码+DesktopGUIPermissionsTest：确认 approve 透传；如果没有这行，允许按钮合同不完整。
        self.assertEqual(payload["status"], "approved")  # 新增代码+DesktopGUIPermissionsTest：确认后端状态变为 approved；如果没有这行，重复回答检查没有事实基础。
    # 新增代码+DesktopGUIPermissionsTest：测试方法结束；如果没有这个边界，初学者不易看出 approve 合同范围。

    def test_permission_decision_endpoint_accepts_deny(self) -> None:  # 新增代码+DesktopGUIPermissionsTest：测试方法开始，验证 deny 决策；如果没有这段测试，拒绝按钮可能无法进入后端审计。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIPermissionsTest：创建临时 workspace；如果没有这行，HTTP 测试会污染真实状态。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUIPermissionsTest：启动 bridge server；如果没有这行，无法验证真实 endpoint。
            try:  # 新增代码+DesktopGUIPermissionsTest：保护 server 清理；如果没有这行，测试失败会泄漏端口。
                server.run_manager.record_permission_required("perm_deny", app_name="PowerShell", reason="需要执行命令", risk_summary="中风险")  # 新增代码+DesktopGUIPermissionsTest：预置 pending 权限请求；如果没有这行，deny 会变成 unknown 404。
                payload = self._post_json(self._permission_url(server, "perm_deny"), "test-token", {"decision": "deny", "reason": "用户在 GUI 中点击拒绝"})  # 新增代码+DesktopGUIPermissionsTest：发送 deny 决策；如果没有这行，无法验证拒绝路径。
            finally:  # 新增代码+DesktopGUIPermissionsTest：清理 server；如果没有这行，后台线程可能继续运行。
                server.shutdown()  # 新增代码+DesktopGUIPermissionsTest：请求 server 退出；如果没有这行，测试结束后端口仍占用。
                server.server_close()  # 新增代码+DesktopGUIPermissionsTest：释放 socket；如果没有这行，Windows 上端口可能短时间占用。
        self.assertEqual(payload["decision"], "deny")  # 新增代码+DesktopGUIPermissionsTest：确认 deny 透传；如果没有这行，拒绝按钮合同不完整。
        self.assertEqual(payload["status"], "denied")  # 新增代码+DesktopGUIPermissionsTest：确认后端状态变为 denied；如果没有这行，重复回答检查没有事实基础。
    # 新增代码+DesktopGUIPermissionsTest：测试方法结束；如果没有这个边界，初学者不易看出 deny 合同范围。

    def test_unknown_permission_request_returns_structured_404(self) -> None:  # 新增代码+DesktopGUIPermissionsTest：测试方法开始，验证未知 request_id 的 404；如果没有这段测试，前端无法区分请求过期和网络失败。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIPermissionsTest：创建临时 workspace；如果没有这行，HTTP 测试会污染真实状态。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUIPermissionsTest：启动 bridge server；如果没有这行，无法验证真实 endpoint。
            try:  # 新增代码+DesktopGUIPermissionsTest：保护 server 清理；如果没有这行，测试失败会泄漏端口。
                with self.assertRaises(urllib.error.HTTPError) as context:  # 新增代码+DesktopGUIPermissionsTest：期待 HTTPError；如果没有这行，404 会让测试直接失败。
                    self._post_json(self._permission_url(server, "missing_perm"), "test-token", {"decision": "approve", "reason": "test"})  # 新增代码+DesktopGUIPermissionsTest：请求未知权限；如果没有这行，无法触发 404 合同。
                payload = self._error_payload(context.exception)  # 新增代码+DesktopGUIPermissionsTest：解析错误响应；如果没有这行，无法断言 code 字段。
            finally:  # 新增代码+DesktopGUIPermissionsTest：清理 server；如果没有这行，后台线程可能继续运行。
                server.shutdown()  # 新增代码+DesktopGUIPermissionsTest：请求 server 退出；如果没有这行，测试结束后端口仍占用。
                server.server_close()  # 新增代码+DesktopGUIPermissionsTest：释放 socket；如果没有这行，Windows 上端口可能短时间占用。
        self.assertEqual(context.exception.code, 404)  # 新增代码+DesktopGUIPermissionsTest：确认 HTTP 状态码；如果没有这行，错误类型可能漂移。
        self.assertEqual(payload["code"], "permission_not_found")  # 新增代码+DesktopGUIPermissionsTest：确认结构化错误码；如果没有这行，前端无法稳定分支处理。
    # 新增代码+DesktopGUIPermissionsTest：测试方法结束；如果没有这个边界，初学者不易看出未知请求合同范围。

    def test_duplicate_permission_decision_returns_structured_409(self) -> None:  # 新增代码+DesktopGUIPermissionsTest：测试方法开始，验证重复回答的 409；如果没有这段测试，双击按钮可能改写审计结果。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIPermissionsTest：创建临时 workspace；如果没有这行，HTTP 测试会污染真实状态。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUIPermissionsTest：启动 bridge server；如果没有这行，无法验证真实 endpoint。
            try:  # 新增代码+DesktopGUIPermissionsTest：保护 server 清理；如果没有这行，测试失败会泄漏端口。
                server.run_manager.record_permission_required("perm_twice", app_name="Chrome", reason="需要点击网页", risk_summary="低风险")  # 新增代码+DesktopGUIPermissionsTest：预置 pending 权限请求；如果没有这行，重复测试没有目标。
                self._post_json(self._permission_url(server, "perm_twice"), "test-token", {"decision": "approve", "reason": "first"})  # 新增代码+DesktopGUIPermissionsTest：第一次回答成功；如果没有这行，第二次不会触发重复状态。
                with self.assertRaises(urllib.error.HTTPError) as context:  # 新增代码+DesktopGUIPermissionsTest：期待第二次 HTTPError；如果没有这行，409 会让测试直接失败。
                    self._post_json(self._permission_url(server, "perm_twice"), "test-token", {"decision": "deny", "reason": "second"})  # 新增代码+DesktopGUIPermissionsTest：第二次回答同一请求；如果没有这行，无法验证冲突合同。
                payload = self._error_payload(context.exception)  # 新增代码+DesktopGUIPermissionsTest：解析错误响应；如果没有这行，无法断言 code 字段。
            finally:  # 新增代码+DesktopGUIPermissionsTest：清理 server；如果没有这行，后台线程可能继续运行。
                server.shutdown()  # 新增代码+DesktopGUIPermissionsTest：请求 server 退出；如果没有这行，测试结束后端口仍占用。
                server.server_close()  # 新增代码+DesktopGUIPermissionsTest：释放 socket；如果没有这行，Windows 上端口可能短时间占用。
        self.assertEqual(context.exception.code, 409)  # 新增代码+DesktopGUIPermissionsTest：确认 HTTP 状态码；如果没有这行，重复回答可能不是冲突错误。
        self.assertEqual(payload["code"], "permission_already_answered")  # 新增代码+DesktopGUIPermissionsTest：确认结构化错误码；如果没有这行，前端无法提示已处理。
    # 新增代码+DesktopGUIPermissionsTest：测试方法结束；如果没有这个边界，初学者不易看出重复回答合同范围。

    def test_permission_decision_writes_status_audit_event(self) -> None:  # 新增代码+DesktopGUIPermissionsTest：测试方法开始，验证每次权限决策写审计事件；如果没有这段测试，状态时间线可能看不到允许/拒绝。
        from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DesktopGUIPermissionsTest：导入状态事件 store；如果没有这行，测试无法读取审计事件。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIPermissionsTest：创建临时 workspace；如果没有这行，事件会写进真实 memory。
            workspace = Path(directory)  # 新增代码+DesktopGUIPermissionsTest：转成 Path；如果没有这行，状态 store 路径不清楚。
            server = self._start_server(workspace)  # 新增代码+DesktopGUIPermissionsTest：启动 bridge server；如果没有这行，无法验证真实 HTTP 决策写事件。
            try:  # 新增代码+DesktopGUIPermissionsTest：保护 server 清理；如果没有这行，测试失败会泄漏端口。
                server.run_manager.record_permission_required("perm_audit", app_name="PowerShell", reason="需要执行命令", risk_summary="中风险")  # 新增代码+DesktopGUIPermissionsTest：预置 pending 权限请求；如果没有这行，决策没有目标。
                self._post_json(self._permission_url(server, "perm_audit"), "test-token", {"decision": "deny", "reason": "用户拒绝"})  # 新增代码+DesktopGUIPermissionsTest：发送 deny 决策；如果没有这行，不会产生回答事件。
                events = StatusEventStore(workspace / "memory" / "status").list_events()  # 新增代码+DesktopGUIPermissionsTest：读取状态事件；如果没有这行，无法验证审计。
            finally:  # 新增代码+DesktopGUIPermissionsTest：清理 server；如果没有这行，后台线程可能继续运行。
                server.shutdown()  # 新增代码+DesktopGUIPermissionsTest：请求 server 退出；如果没有这行，测试结束后端口仍占用。
                server.server_close()  # 新增代码+DesktopGUIPermissionsTest：释放 socket；如果没有这行，Windows 上端口可能短时间占用。
        answered_events = [event for event in events if event.event_type == "permission_answered"]  # 新增代码+DesktopGUIPermissionsTest：筛选权限回答事件；如果没有这行，断言要手工遍历。
        self.assertEqual(len(answered_events), 1)  # 新增代码+DesktopGUIPermissionsTest：确认正好写入一次回答审计；如果没有这行，可能漏写或重复写。
        self.assertEqual(answered_events[0].payload["decision"], "deny")  # 新增代码+DesktopGUIPermissionsTest：确认审计记录用户决策；如果没有这行，时间线无法解释允许/拒绝。
    # 新增代码+DesktopGUIPermissionsTest：测试方法结束；如果没有这个边界，初学者不易看出权限审计合同范围。


if __name__ == "__main__":  # 新增代码+DesktopGUIPermissionsTest：允许直接运行本测试文件；如果没有这行，手动调试只能通过模块方式启动。
    unittest.main()  # 新增代码+DesktopGUIPermissionsTest：启动 unittest；如果没有这行，直接运行文件不会执行测试。
