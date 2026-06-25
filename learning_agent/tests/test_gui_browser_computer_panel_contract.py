import json  # 新增代码+DesktopRuntimePanelsTest：解析 HTTP 响应 JSON；如果没有这行代码，测试无法检查 V2 panels payload。
import tempfile  # 新增代码+DesktopRuntimePanelsTest：创建隔离工作区；如果没有这行代码，测试会污染真实项目 memory。
import threading  # 新增代码+DesktopRuntimePanelsTest：后台启动 HTTP server；如果没有这行代码，路由测试会阻塞当前线程。
import unittest  # 新增代码+DesktopRuntimePanelsTest：使用 unittest 承载蓝图要求的后端合同测试；如果没有这行代码，测试不会被 unittest 收集。
import urllib.request  # 新增代码+DesktopRuntimePanelsTest：使用标准库请求本地 bridge；如果没有这行代码，HTTP 路由无法被自动验证。
from pathlib import Path  # 新增代码+DesktopRuntimePanelsTest：使用 Path 管理临时工作区；如果没有这行代码，路径拼接会变得脆弱。
from unittest.mock import patch  # 新增代码+DesktopRuntimePanelsTest：替换 status snapshot 构造稳定输入；如果没有这行代码，测试会依赖真实浏览器状态。


class GuiBrowserComputerPanelContractTests(unittest.TestCase):  # 新增代码+DesktopRuntimePanelsTest：测试类段开始，锁定 V2 浏览器和 Computer Use 成熟面板合同；如果没有这个类，panel payload 可能漂移。
    def _snapshot_with_browser_and_permission(self) -> dict[str, object]:  # 新增代码+DesktopRuntimePanelsTest：helper 段开始，构造包含浏览器和权限事件的快照；如果没有这段，多个测试会重复复杂字典。
        return {  # 新增代码+DesktopRuntimePanelsTest：返回测试用快照；如果没有这行代码，patch 后没有稳定事实源。
            "browser": {  # 新增代码+DesktopRuntimePanelsTest：提供 browser 区块；如果没有这行代码，payload 无法验证浏览器面板。
                "provider_status": {  # 新增代码+DesktopRuntimePanelsTest：提供 provider_status 区块；如果没有这行代码，BrowserPanel 没有轨道来源。
                    "providers": {  # 新增代码+DesktopRuntimePanelsTest：提供 provider 集合；如果没有这行代码，测试无法验证 visible Chromium。
                        "visible_chromium": {"available": True, "reason": "ready"},  # 新增代码+DesktopRuntimePanelsTest：模拟可见 Chromium 可用；如果没有这行代码，成熟面板可能丢掉可用轨道。
                        "real_chrome_cdp": {"available": False, "reason": "cdp offline"},  # 新增代码+DesktopRuntimePanelsTest：模拟 CDP 降级；如果没有这行代码，降级 provider 形态没有覆盖。
                        "chrome_extension": {"available": True, "reason": "paired"},  # 新增代码+DesktopRuntimePanelsTest：模拟扩展已配对；如果没有这行代码，extension host 状态没有覆盖。
                    },  # 新增代码+DesktopRuntimePanelsTest：provider 集合结束；如果没有这行代码，Python 字典语法不完整。
                    "chrome_extension": {"connected": True, "pending_command_count": 1},  # 新增代码+DesktopRuntimePanelsTest：模拟扩展连接摘要；如果没有这行代码，前端无法展示扩展队列。
                    "tabs": {"tab_count": 2, "active_title": "OpenHarness"},  # 新增代码+DesktopRuntimePanelsTest：模拟标签页摘要；如果没有这行代码，面板缺少 active target 数据。
                    "active_target": {"kind": "tab", "title": "OpenHarness", "url_host": "localhost"},  # 新增代码+DesktopRuntimePanelsTest：模拟活跃目标；如果没有这行代码，浏览器面板无法展示当前目标。
                },  # 新增代码+DesktopRuntimePanelsTest：provider_status 区块结束；如果没有这行代码，Python 字典语法不完整。
            },  # 新增代码+DesktopRuntimePanelsTest：browser 区块结束；如果没有这行代码，Python 字典语法不完整。
            "status_events": [  # 新增代码+DesktopRuntimePanelsTest：提供权限事件尾巴；如果没有这行代码，permissions 摘要没有输入。
                {"event_type": "permission_required", "turn_id": "turn_a", "payload": {"request_id": "perm_a", "tool_name": "browser.open", "risk_summary": "needs confirmation"}},  # 新增代码+DesktopRuntimePanelsTest：模拟待确认权限；如果没有这行代码，permissions pending_count 无法验证。
            ],  # 新增代码+DesktopRuntimePanelsTest：状态事件列表结束；如果没有这行代码，Python 列表语法不完整。
        }  # 新增代码+DesktopRuntimePanelsTest：测试快照结束；如果没有这行代码，helper 没有返回值。
    # 新增代码+DesktopRuntimePanelsTest：helper 段结束，_snapshot_with_browser_and_permission 到此结束；如果没有这个边界说明，初学者不易看出快照范围。

    def test_runtime_panels_payload_contains_browser_computer_use_permissions(self) -> None:  # 新增代码+DesktopRuntimePanelsTest：测试方法开始，验证正常 V2 panel payload；如果没有这段测试，后端可能只返回旧 browser provider 片段。
        from learning_agent.app.gui_bridge import build_gui_runtime_panels_payload  # 新增代码+DesktopRuntimePanelsTest：导入计划新增 helper；如果没有这行代码，测试无法锁定 V2 合同。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopRuntimePanelsTest：创建临时 workspace；如果没有这行代码，Computer Use 状态会污染真实目录。
            with patch("learning_agent.app.gui_bridge.build_status_snapshot", return_value=self._snapshot_with_browser_and_permission()):  # 新增代码+DesktopRuntimePanelsTest：固定 status snapshot；如果没有这行代码，测试会依赖本机浏览器状态。
                payload = build_gui_runtime_panels_payload(Path(directory))  # 新增代码+DesktopRuntimePanelsTest：生成 V2 runtime panels payload；如果没有这行代码，无法断言响应合同。
        self.assertIs(payload["ok"], True)  # 新增代码+DesktopRuntimePanelsTest：确认 payload 成功；如果没有这行断言，错误 payload 可能误过。
        self.assertIn("browser", payload)  # 新增代码+DesktopRuntimePanelsTest：确认浏览器面板存在；如果没有这行断言，V2 右侧浏览器页签缺数据。
        self.assertIn("computer_use", payload)  # 新增代码+DesktopRuntimePanelsTest：确认 Computer Use 面板存在；如果没有这行断言，用户看不到桌面自动化安全状态。
        self.assertIn("permissions", payload)  # 新增代码+DesktopRuntimePanelsTest：确认权限摘要存在；如果没有这行断言，权限状态仍散落在事件流。
        self.assertIs(payload["status_degraded"], False)  # 新增代码+DesktopRuntimePanelsTest：确认正常快照不标记降级；如果没有这行断言，前端会误显示告警。
        self.assertEqual(payload["browser"]["providers"]["visible_chromium"]["available"], True)  # 新增代码+DesktopRuntimePanelsTest：确认可见 Chromium 状态保留；如果没有这行断言，真实浏览器轨道可能丢失。
        self.assertEqual(payload["browser"]["extension"]["connected"], True)  # 新增代码+DesktopRuntimePanelsTest：确认扩展 host 状态保留；如果没有这行断言，扩展连接不可见。
        self.assertEqual(payload["browser"]["active_target"]["title"], "OpenHarness")  # 新增代码+DesktopRuntimePanelsTest：确认 active target 摘要保留；如果没有这行断言，浏览器页签只剩 provider chips。
        self.assertIn("lock", payload["computer_use"])  # 新增代码+DesktopRuntimePanelsTest：确认 Computer Use lock 摘要存在；如果没有这行断言，锁状态不可诊断。
        self.assertIn("abort", payload["computer_use"])  # 新增代码+DesktopRuntimePanelsTest：确认 Computer Use abort 摘要存在；如果没有这行断言，急停状态不可诊断。
        self.assertIn("mode", payload["computer_use"])  # 新增代码+DesktopRuntimePanelsTest：确认 Computer Use 模式存在；如果没有这行断言，面板无法显示 full/off/observe。
        self.assertEqual(payload["permissions"]["pending_count"], 1)  # 新增代码+DesktopRuntimePanelsTest：确认待确认权限计数；如果没有这行断言，权限入口无法提醒用户。
    # 新增代码+DesktopRuntimePanelsTest：测试方法结束；如果没有这个边界说明，初学者不易看出正常 payload 合同范围。

    def test_runtime_panels_payload_degrades_without_path_leak(self) -> None:  # 新增代码+DesktopRuntimePanelsTest：测试方法开始，验证快照失败时安全降级；如果没有这段测试，Windows 文件锁错误可能泄露路径。
        from learning_agent.app.gui_bridge import build_gui_runtime_panels_payload  # 新增代码+DesktopRuntimePanelsTest：导入 V2 panel helper；如果没有这行代码，测试没有被测目标。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopRuntimePanelsTest：创建临时 workspace；如果没有这行代码，降级测试会污染真实项目。
            with patch("learning_agent.app.gui_bridge.build_status_snapshot", side_effect=PermissionError("C:/Users/joyzq/secret/status.lock")):  # 新增代码+DesktopRuntimePanelsTest：模拟包含本机路径的快照错误；如果没有这行代码，脱敏分支无法稳定覆盖。
                payload = build_gui_runtime_panels_payload(Path(directory))  # 新增代码+DesktopRuntimePanelsTest：生成降级 payload；如果没有这行代码，无法断言安全输出。
        serialized = json.dumps(payload, ensure_ascii=False)  # 新增代码+DesktopRuntimePanelsTest：序列化 payload 方便查泄漏；如果没有这行代码，路径泄漏断言会重复转换。
        self.assertIs(payload["ok"], True)  # 新增代码+DesktopRuntimePanelsTest：确认降级仍返回成功形状；如果没有这行断言，前端可能白屏。
        self.assertIs(payload["status_degraded"], True)  # 新增代码+DesktopRuntimePanelsTest：确认显式标记降级；如果没有这行断言，用户不知道数据来自兜底。
        self.assertEqual(payload["safe_error"], "状态快照暂时不可读。")  # 新增代码+DesktopRuntimePanelsTest：确认错误文案安全；如果没有这行断言，原始异常可能显示到 GUI。
        self.assertEqual(payload["browser"]["providers"], {})  # 新增代码+DesktopRuntimePanelsTest：确认浏览器 provider 安全兜底为空；如果没有这行断言，前端可能收到坏类型。
        self.assertIn("computer_use", payload)  # 新增代码+DesktopRuntimePanelsTest：确认降级时仍返回 Computer Use 摘要；如果没有这行断言，右侧页签可能崩溃。
        self.assertNotIn("joyzq", serialized)  # 新增代码+DesktopRuntimePanelsTest：确认不泄露用户名；如果没有这行断言，本机路径可能进入 GUI。
        self.assertNotIn("secret", serialized)  # 新增代码+DesktopRuntimePanelsTest：确认不泄露敏感路径片段；如果没有这行断言，异常详情可能进入 GUI。
    # 新增代码+DesktopRuntimePanelsTest：测试方法结束；如果没有这个边界说明，初学者不易看出降级合同范围。

    def test_runtime_panels_http_route_requires_token_and_returns_v2_payload(self) -> None:  # 新增代码+DesktopRuntimePanelsTest：测试方法开始，验证 V2 runtime panels HTTP 路由；如果没有这段测试，Electron 可能拿不到聚合面板数据。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopRuntimePanelsTest：导入 bridge server 构造器；如果没有这行代码，测试无法启动真实 HTTP handler。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopRuntimePanelsTest：创建临时 workspace；如果没有这行代码，HTTP 测试会污染真实状态。
            server = create_gui_bridge_server(workspace=Path(directory), host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopRuntimePanelsTest：使用随机端口启动 server；如果没有这行代码，测试可能端口冲突。
            try:  # 新增代码+DesktopRuntimePanelsTest：保护 server 清理；如果没有这行代码，失败时会残留监听端口。
                thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopRuntimePanelsTest：创建后台服务线程；如果没有这行代码，urllib 请求会阻塞。
                thread.start()  # 新增代码+DesktopRuntimePanelsTest：启动 HTTP server；如果没有这行代码，请求会连接失败。
                host, port = server.server_address  # 新增代码+DesktopRuntimePanelsTest：读取随机端口；如果没有这行代码，请求不知道目标地址。
                request = urllib.request.Request(f"http://{host}:{port}/v2/gui/runtime/panels", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopRuntimePanelsTest：构造 V2 panels 请求；如果没有这行代码，无法验证路由和 token。
                with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopRuntimePanelsTest：请求 V2 panels 端点；如果没有这行代码，无法验证 HTTP 路由。
                    payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopRuntimePanelsTest：解析响应 JSON；如果没有这行代码，无法断言字段。
            finally:  # 新增代码+DesktopRuntimePanelsTest：无论断言是否失败都关闭 server；如果没有这行代码，测试环境会残留端口。
                server.shutdown()  # 新增代码+DesktopRuntimePanelsTest：停止 serve_forever；如果没有这行代码，后台线程可能继续运行。
                server.server_close()  # 新增代码+DesktopRuntimePanelsTest：释放 socket；如果没有这行代码，Windows 端口可能短时间占用。
        self.assertIs(payload["ok"], True)  # 新增代码+DesktopRuntimePanelsTest：确认 HTTP payload 成功；如果没有这行断言，错误页可能误过。
        self.assertIn("browser", payload)  # 新增代码+DesktopRuntimePanelsTest：确认 HTTP payload 包含浏览器面板；如果没有这行断言，前端浏览器页签会缺数据。
        self.assertIn("computer_use", payload)  # 新增代码+DesktopRuntimePanelsTest：确认 HTTP payload 包含 Computer Use 面板；如果没有这行断言，桌面自动化状态不可见。
    # 新增代码+DesktopRuntimePanelsTest：测试方法结束；如果没有这个边界说明，初学者不易看出 HTTP 路由合同范围。
# 新增代码+DesktopRuntimePanelsTest：测试类段结束，GuiBrowserComputerPanelContractTests 到此结束；如果没有这个边界说明，初学者不易看出本文件只测 runtime panels。


if __name__ == "__main__":  # 新增代码+DesktopRuntimePanelsTest：允许直接运行本文件；如果没有这行代码，手动调试时不会进入 unittest。
    unittest.main()  # 新增代码+DesktopRuntimePanelsTest：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
