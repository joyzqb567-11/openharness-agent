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
        self.assertEqual(payload["app"]["schema_version"], 2)  # 修改代码+GuiV2Protocol：锁定响应协议版本已升级到 V2；如果没有这行断言，bridge 可能继续暴露旧 V1 合同。
        self.assertIn("snapshot", payload)  # 新增代码+DesktopGUIBridgeTest: 确认包含统一状态快照；如果没有这行断言，GUI 需要旁路读状态。
        self.assertIs(payload["feature_flags"]["event_polling"], True)  # 新增代码+DesktopGUIBridgeTest: 确认事件轮询可用；如果没有这行断言，前端无法知道刷新方式。
    # 新增代码+DesktopGUIBridgeTest: 测试方法结束；如果没有这个边界说明，初学者不容易看出 bootstrap 合同测试范围。

    def test_gui_bootstrap_payload_degrades_when_snapshot_fails(self) -> None:  # 新增代码+DesktopGUIBootstrapDegradeTest：测试方法开始，验证首屏快照失败时降级；如果没有这段测试，Windows 文件锁异常可能再次让 GUI 白屏。
        from unittest.mock import patch  # 新增代码+DesktopGUIBootstrapDegradeTest：导入 patch 临时替换快照函数；如果没有这行代码，测试无法稳定制造 PermissionError。
        from learning_agent.app.gui_bridge import build_gui_bootstrap_payload  # 新增代码+DesktopGUIBootstrapDegradeTest：导入 bootstrap helper；如果没有这行代码，测试没有被测函数。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIBootstrapDegradeTest：创建临时 workspace；如果没有这行代码，测试路径会污染真实项目。
            with patch("learning_agent.app.gui_bridge.build_status_snapshot", side_effect=PermissionError("H:/secret/commands.lock")):  # 新增代码+DesktopGUIBootstrapDegradeTest：模拟快照读取失败；如果没有这行代码，降级分支无法稳定覆盖。
                payload = build_gui_bootstrap_payload(Path(directory))  # 新增代码+DesktopGUIBootstrapDegradeTest：生成降级 bootstrap payload；如果没有这行代码，无法断言响应形状。
        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIBootstrapDegradeTest：确认降级仍返回成功 payload；如果没有这行代码，前端首屏可能中断。
        self.assertIs(payload["snapshot_degraded"], True)  # 新增代码+DesktopGUIBootstrapDegradeTest：确认显式标记降级；如果没有这行代码，诊断时看不出快照来自兜底。
        self.assertNotIn("secret", json.dumps(payload, ensure_ascii=False))  # 新增代码+DesktopGUIBootstrapDegradeTest：确认不泄露本机路径片段；如果没有这行代码，错误信息可能暴露用户磁盘路径。
    # 新增代码+DesktopGUIBootstrapDegradeTest：测试方法结束；如果没有这个边界说明，初学者不容易看出 bootstrap 降级合同范围。

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

    def test_gui_sessions_payload_degrades_when_snapshot_fails(self) -> None:  # 新增代码+DesktopGUISessionDegradeTest：测试方法开始，验证 sessions 快照失败时降级；如果没有这段测试，旧 helper 复用时可能重新 traceback。
        from unittest.mock import patch  # 新增代码+DesktopGUISessionDegradeTest：导入 patch 临时替换快照函数；如果没有这行代码，测试无法稳定制造 PermissionError。
        from learning_agent.app.gui_bridge import build_gui_sessions_payload  # 新增代码+DesktopGUISessionDegradeTest：导入 sessions helper；如果没有这行代码，测试没有被测函数。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUISessionDegradeTest：创建临时 workspace；如果没有这行代码，测试路径会污染真实项目。
            with patch("learning_agent.app.gui_bridge.build_status_snapshot", side_effect=PermissionError("H:/secret/commands.lock")):  # 新增代码+DesktopGUISessionDegradeTest：模拟快照读取失败；如果没有这行代码，降级分支无法稳定覆盖。
                payload = build_gui_sessions_payload(Path(directory))  # 新增代码+DesktopGUISessionDegradeTest：生成降级 sessions payload；如果没有这行代码，无法断言响应形状。
        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUISessionDegradeTest：确认降级仍返回成功 payload；如果没有这行代码，前端侧栏可能中断。
        self.assertEqual(payload["sessions"], [])  # 新增代码+DesktopGUISessionDegradeTest：确认 sessions 兜底为空数组；如果没有这行代码，前端可能收到坏类型。
        self.assertIs(payload["resume"]["degraded"], True)  # 新增代码+DesktopGUISessionDegradeTest：确认 resume 显式标记降级；如果没有这行代码，诊断时看不出数据来自兜底。
        self.assertNotIn("secret", json.dumps(payload, ensure_ascii=False))  # 新增代码+DesktopGUISessionDegradeTest：确认不泄露本机路径片段；如果没有这行代码，错误信息可能暴露用户磁盘路径。
    # 新增代码+DesktopGUISessionDegradeTest：测试方法结束；如果没有这个边界说明，初学者不容易看出 sessions 降级合同范围。

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

    def test_gui_browser_providers_payload_uses_status_snapshot(self) -> None:  # 新增代码+DesktopGUIBrowserPanelTest：测试方法开始，验证浏览器 provider payload 复用统一状态快照；如果没有这段测试，右栏可能显示一套旁路假状态。
        from learning_agent.app.gui_bridge import build_gui_browser_providers_payload  # 新增代码+DesktopGUIBrowserPanelTest：导入浏览器 provider helper；如果没有这行代码，测试无法锁定新端点合同。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIBrowserPanelTest：创建临时 workspace；如果没有这行代码，测试会污染真实浏览器状态目录。
            payload = build_gui_browser_providers_payload(Path(directory))  # 新增代码+DesktopGUIBrowserPanelTest：生成浏览器 provider payload；如果没有这行代码，无法验证 helper 输出。
        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIBrowserPanelTest：确认响应成功；如果没有这行断言，失败 payload 可能误过。
        self.assertIsInstance(payload["provider_status"], dict)  # 新增代码+DesktopGUIBrowserPanelTest：确认 provider_status 是对象；如果没有这行断言，前端类型合同可能漂移。
        self.assertIsInstance(payload["browser"], dict)  # 新增代码+DesktopGUIBrowserPanelTest：确认 browser 是对象；如果没有这行断言，右栏拿不到浏览器总览。
        self.assertIn("providers", payload["provider_status"])  # 新增代码+DesktopGUIBrowserPanelTest：确认 provider 集合存在；如果没有这行断言，BrowserPanel 无法列出轨道。
    # 新增代码+DesktopGUIBrowserPanelTest：测试方法结束；如果没有这个边界说明，初学者不容易看出浏览器 provider payload 合同范围。

    def test_gui_browser_providers_payload_degrades_when_snapshot_fails(self) -> None:  # 新增代码+DesktopGUIProviderDegradeTest：测试方法开始，验证浏览器状态快照失败时降级；如果没有这段测试，Windows 文件锁异常可能再次打崩 HTTP handler。
        from unittest.mock import patch  # 新增代码+DesktopGUIProviderDegradeTest：导入 patch 临时替换快照函数；如果没有这行代码，测试无法稳定制造 PermissionError。
        from learning_agent.app.gui_bridge import build_gui_browser_providers_payload  # 新增代码+DesktopGUIProviderDegradeTest：导入浏览器 provider helper；如果没有这行代码，测试没有被测函数。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIProviderDegradeTest：创建临时 workspace；如果没有这行代码，测试路径会污染真实项目。
            with patch("learning_agent.app.gui_bridge.build_status_snapshot", side_effect=PermissionError("H:/secret/commands.lock")):  # 新增代码+DesktopGUIProviderDegradeTest：模拟快照读取被 Windows 拒绝；如果没有这行代码，降级分支无法稳定覆盖。
                payload = build_gui_browser_providers_payload(Path(directory))  # 新增代码+DesktopGUIProviderDegradeTest：生成降级 payload；如果没有这行代码，无法断言失败时的响应形状。
        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIProviderDegradeTest：确认降级仍返回成功 payload；如果没有这行代码，前端轮询可能因异常中断。
        self.assertIs(payload["degraded"], True)  # 新增代码+DesktopGUIProviderDegradeTest：确认显式标记降级；如果没有这行代码，前端无法区分空状态和读取失败。
        self.assertEqual(payload["provider_status"]["providers"], {})  # 新增代码+DesktopGUIProviderDegradeTest：确认 providers 兜底为空对象；如果没有这行代码，浏览器面板可能收到坏类型。
        self.assertNotIn("secret", json.dumps(payload, ensure_ascii=False))  # 新增代码+DesktopGUIProviderDegradeTest：确认不泄露本机路径片段；如果没有这行代码，错误信息可能把用户磁盘路径暴露给前端。
    # 新增代码+DesktopGUIProviderDegradeTest：测试方法结束；如果没有这个边界说明，初学者不容易看出 provider 降级合同范围。

    def test_gui_bridge_http_browser_providers_route(self) -> None:  # 新增代码+DesktopGUIBrowserPanelTest：测试方法开始，验证 HTTP 浏览器 provider 路由；如果没有这段测试，Electron 可能拿不到浏览器状态。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIBrowserPanelTest：导入 HTTP server 构造器；如果没有这行代码，测试无法启动真实 bridge。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIBrowserPanelTest：创建临时 workspace；如果没有这行代码，HTTP 测试会污染真实项目。
            server = create_gui_bridge_server(workspace=Path(directory), host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUIBrowserPanelTest：使用随机端口创建 server；如果没有这行代码，测试可能端口冲突。
            try:  # 新增代码+DesktopGUIBrowserPanelTest：保护 server 清理；如果没有这行代码，失败测试会留下监听端口。
                thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIBrowserPanelTest：创建后台 server 线程；如果没有这行代码，urllib 请求会阻塞。
                thread.start()  # 新增代码+DesktopGUIBrowserPanelTest：启动 HTTP server；如果没有这行代码，provider 请求会连接失败。
                host, port = server.server_address  # 新增代码+DesktopGUIBrowserPanelTest：读取随机端口；如果没有这行代码，请求不知道发到哪里。
                request = urllib.request.Request(f"http://{host}:{port}/v1/gui/browser/providers", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUIBrowserPanelTest：构造带 token 的浏览器 provider 请求；如果没有这行代码，安全合同会拒绝请求。
                with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUIBrowserPanelTest：请求浏览器 provider 端点；如果没有这行代码，无法验证 HTTP 路由。
                    payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIBrowserPanelTest：解析响应 JSON；如果没有这行代码，无法断言字段。
                self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIBrowserPanelTest：确认 HTTP 响应成功；如果没有这行断言，错误页可能误过。
                self.assertIn("provider_status", payload)  # 新增代码+DesktopGUIBrowserPanelTest：确认包含 provider_status 字段；如果没有这行断言，右栏会缺数据。
                self.assertIn("browser", payload)  # 新增代码+DesktopGUIBrowserPanelTest：确认包含 browser 字段；如果没有这行断言，右栏无法展示总览。
            finally:  # 新增代码+DesktopGUIBrowserPanelTest：无论断言是否失败都关闭 server；如果没有这行代码，测试环境会残留端口。
                server.shutdown()  # 新增代码+DesktopGUIBrowserPanelTest：请求 server 退出；如果没有这行代码，后台线程可能继续运行。
                server.server_close()  # 新增代码+DesktopGUIBrowserPanelTest：释放 socket；如果没有这行代码，Windows 上端口可能短时间占用。
    # 新增代码+DesktopGUIBrowserPanelTest：测试方法结束；如果没有这个边界说明，初学者不容易看出 HTTP 浏览器 provider 合同范围。

if __name__ == "__main__":  # 新增代码+DesktopGUIBridgeTest: 允许直接运行本测试文件；如果没有这行代码，手动调试时只能通过模块方式启动。
    unittest.main()  # 新增代码+DesktopGUIBridgeTest: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
