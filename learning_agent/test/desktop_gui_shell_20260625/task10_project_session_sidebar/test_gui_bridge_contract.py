import tempfile  # 新增代码+DesktopGUIBridgeTest: 使用标准库创建临时工作区；如果没有这行代码，unittest 无法获得 pytest 的 tmp_path fixture。
import json  # 新增代码+DesktopGUIBridgeTest: 解析 HTTP 响应 JSON；如果没有这行代码，测试只能比较原始字符串。
import threading  # 新增代码+DesktopGUIBridgeTest: 后台运行标准库 HTTP server；如果没有这行代码，请求会阻塞。
import unittest  # 新增代码+DesktopGUIBridgeTest: 使用 unittest.TestCase 让计划中的 unittest 命令能发现测试；如果没有这行代码，测试函数不会被 unittest 收集。
import urllib.request  # 新增代码+DesktopGUIBridgeTest: 使用标准库请求本地 bridge；如果没有这行代码，测试需要额外依赖。
from pathlib import Path  # 新增代码+DesktopGUIBridgeTest: 使用 Path 构造临时工作区；如果没有这行代码，测试无法用统一路径对象。


class GuiBridgeContractTests(unittest.TestCase):  # 新增代码+DesktopGUIBridgeTest: 测试类段开始，承载 GUI bridge 合同；如果没有这个类，unittest 不会执行合同检查。
    def test_gui_bootstrap_payload_contains_snapshot_and_flags(self) -> None:  # 新增代码+DesktopGUIBridgeTest: 验证 GUI 启动所需字段；如果没有这段测试，桌面壳可能拿不到状态和功能开关。
        from learning_agent.app.gui_bridge import build_gui_bootstrap_payload  # 新增代码+DesktopGUIBridgeTest: 导入计划新增的 bridge helper；如果没有这行代码，测试无法锁定后端合同。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIBridgeTest: 创建自动清理的临时目录；如果没有这行代码，测试会污染真实项目目录。
            workspace = Path(directory)  # 新增代码+DesktopGUIBridgeTest: 把临时目录转换成 Path；如果没有这行代码，合同无法验证路径规范化。
            payload = build_gui_bootstrap_payload(workspace)  # 新增代码+DesktopGUIBridgeTest: 生成 GUI bootstrap 响应；如果没有这行代码，无法验证结构。

        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIBridgeTest: 确认 bridge 返回成功；如果没有这行断言，失败 payload 可能误过。
        self.assertEqual(payload["workspace"], str(workspace.resolve()))  # 新增代码+DesktopGUIBridgeTest: 确认工作区路径可展示；如果没有这行断言，GUI 可能显示错误项目。
        self.assertEqual(payload["app"]["schema_version"], 1)  # 新增代码+DesktopGUIBridgeTest: 锁定响应协议版本；如果没有这行断言，前端无法安全兼容。
        self.assertIn("snapshot", payload)  # 新增代码+DesktopGUIBridgeTest: 确认包含统一状态快照；如果没有这行断言，GUI 需要旁路读状态。
        self.assertIs(payload["feature_flags"]["event_polling"], True)  # 新增代码+DesktopGUIBridgeTest: 确认事件轮询可用；如果没有这行断言，前端无法知道刷新方式。
    # 新增代码+DesktopGUIBridgeTest: 测试方法结束；如果没有这个边界说明，初学者不容易看出 bootstrap 合同测试范围。

    def test_gui_bridge_http_bootstrap_route(self) -> None:  # 新增代码+DesktopGUIBridgeTest: 验证 GUI bridge HTTP 端点；如果没有这段测试，Electron 无法可靠启动首屏。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIBridgeTest: 导入计划新增的 HTTP server 构造器；如果没有这行代码，测试无法启动 bridge。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIBridgeTest: 创建临时工作区；如果没有这行代码，测试会污染真实项目目录。
            server = create_gui_bridge_server(workspace=Path(directory), host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUIBridgeTest: 使用随机端口启动 server 对象；如果没有这行代码，测试可能端口冲突。
            try:  # 新增代码+DesktopGUIBridgeTest: 保护 server 清理；如果没有这行代码，测试失败会泄漏监听端口。
                thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIBridgeTest: 创建 daemon 线程；如果没有这行代码，测试无法同时请求 server。
                thread.start()  # 新增代码+DesktopGUIBridgeTest: 启动 HTTP server；如果没有这行代码，urllib 会连接失败。
                host, port = server.server_address  # 新增代码+DesktopGUIBridgeTest: 读取真实随机端口；如果没有这行代码，请求不知道地址。
                request = urllib.request.Request(f"http://{host}:{port}/v1/gui/bootstrap", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUIBridgeTest: 构造带 token 的 bootstrap 请求；如果没有这行代码，安全合同会拒绝请求。
                with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUIBridgeTest: 请求 bootstrap 端点；如果没有这行代码，无法验证 HTTP 路由。
                    payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIBridgeTest: 解析响应 JSON；如果没有这行代码，无法断言字段。
                self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIBridgeTest: 确认 HTTP 返回成功；如果没有这行断言，坏响应可能误过。
                self.assertEqual(payload["app"]["name"], "OpenHarness Desktop")  # 新增代码+DesktopGUIBridgeTest: 确认返回 GUI 应用名；如果没有这行断言，前端首屏品牌可能丢失。
            finally:  # 新增代码+DesktopGUIBridgeTest: 无论断言是否失败都关闭 server；如果没有这行代码，测试环境会残留端口。
                server.shutdown()  # 新增代码+DesktopGUIBridgeTest: 请求 server 退出；如果没有这行代码，后台线程可能继续运行。
                server.server_close()  # 新增代码+DesktopGUIBridgeTest: 释放 socket；如果没有这行代码，Windows 上端口可能短时间占用。
    # 新增代码+DesktopGUIBridgeTest: 测试方法结束；如果没有这个边界说明，用户不容易看出 HTTP bootstrap 合同范围。
# 新增代码+DesktopGUIBridgeTest: 测试类段结束，GuiBridgeContractTests 到此结束；如果没有这个边界说明，用户不容易看出本文件只测 GUI bridge 合同。


    def test_gui_sessions_payload_uses_status_snapshot_sessions(self) -> None:  # 新增代码+DesktopGUISessionsTest：测试方法开始，验证 GUI sessions payload 复用统一状态快照；如果没有这段测试，侧栏可能再次走静态假数据。
        from learning_agent.app.gui_bridge import build_gui_sessions_payload  # 新增代码+DesktopGUISessionsTest：导入 sessions payload helper；如果没有这行代码，测试无法锁定新端点合同。
        from learning_agent.core.session import SessionRecord, SessionStore  # 新增代码+DesktopGUISessionsTest：导入真实 session store；如果没有这行代码，测试只能验证空列表，发现不了真实会话读取失败。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUISessionsTest：创建临时 workspace；如果没有这行代码，测试会污染真实 memory/sessions。
            workspace = Path(directory)  # 新增代码+DesktopGUISessionsTest：规范化临时 workspace；如果没有这行代码，store 路径会分散成字符串拼接。
            SessionStore(workspace / "memory" / "sessions").save_summary(SessionRecord(session_id="session_visible", user_input="请继续这个会话"))  # 新增代码+DesktopGUISessionsTest：写入一个真实 session 摘要；如果没有这行代码，payload 测试无法证明 sessions 来自真实 store。
            payload = build_gui_sessions_payload(workspace)  # 新增代码+DesktopGUISessionsTest：生成 sessions payload；如果没有这行代码，无法验证 helper 输出。
        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUISessionsTest：确认响应成功；如果没有这行断言，失败 payload 可能误过。
        self.assertEqual(payload["sessions"], ["session_visible"])  # 新增代码+DesktopGUISessionsTest：确认真实 session id 透出；如果没有这行断言，侧栏无法可靠显示最近会话。
        self.assertIsInstance(payload["resume"], dict)  # 新增代码+DesktopGUISessionsTest：确认 resume 是对象；如果没有这行断言，前端类型合同可能漂移。
    # 新增代码+DesktopGUISessionsTest：测试方法结束；如果没有这个边界说明，初学者不容易看出 sessions payload 合同范围。

    def test_gui_bridge_http_sessions_route(self) -> None:  # 新增代码+DesktopGUISessionsTest：测试方法开始，验证 HTTP sessions 路由；如果没有这段测试，Electron 可能拿不到侧栏会话列表。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUISessionsTest：导入 HTTP server 构造器；如果没有这行代码，测试无法启动真实 bridge。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUISessionsTest：创建临时 workspace；如果没有这行代码，HTTP 测试会污染真实项目。
            server = create_gui_bridge_server(workspace=Path(directory), host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUISessionsTest：使用随机端口创建 server；如果没有这行代码，测试可能端口冲突。
            try:  # 新增代码+DesktopGUISessionsTest：保护 server 清理；如果没有这行代码，失败测试会留下监听端口。
                thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUISessionsTest：创建后台 server 线程；如果没有这行代码，urllib 请求会阻塞。
                thread.start()  # 新增代码+DesktopGUISessionsTest：启动 HTTP server；如果没有这行代码，sessions 请求会连接失败。
                host, port = server.server_address  # 新增代码+DesktopGUISessionsTest：读取随机端口；如果没有这行代码，请求不知道发到哪里。
                request = urllib.request.Request(f"http://{host}:{port}/v1/gui/sessions", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUISessionsTest：构造带 token 的 sessions 请求；如果没有这行代码，安全合同会拒绝请求。
                with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUISessionsTest：请求 sessions 端点；如果没有这行代码，无法验证 HTTP 路由。
                    payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUISessionsTest：解析响应 JSON；如果没有这行代码，无法断言字段。
                self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUISessionsTest：确认 HTTP 响应成功；如果没有这行断言，错误页可能误过。
                self.assertIn("sessions", payload)  # 新增代码+DesktopGUISessionsTest：确认包含 sessions 字段；如果没有这行断言，前端侧栏会缺数据。
                self.assertIn("resume", payload)  # 新增代码+DesktopGUISessionsTest：确认包含 resume 字段；如果没有这行断言，恢复状态无法同屏展示。
            finally:  # 新增代码+DesktopGUISessionsTest：无论断言是否失败都关闭 server；如果没有这行代码，测试环境会残留端口。
                server.shutdown()  # 新增代码+DesktopGUISessionsTest：请求 server 退出；如果没有这行代码，后台线程可能继续运行。
                server.server_close()  # 新增代码+DesktopGUISessionsTest：释放 socket；如果没有这行代码，Windows 上端口可能短时间占用。
    # 新增代码+DesktopGUISessionsTest：测试方法结束；如果没有这个边界说明，初学者不容易看出 HTTP sessions 合同范围。

if __name__ == "__main__":  # 新增代码+DesktopGUIBridgeTest: 允许直接运行本测试文件；如果没有这行代码，手动调试时只能通过模块方式启动。
    unittest.main()  # 新增代码+DesktopGUIBridgeTest: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
