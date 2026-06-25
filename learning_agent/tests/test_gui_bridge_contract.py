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


if __name__ == "__main__":  # 新增代码+DesktopGUIBridgeTest: 允许直接运行本测试文件；如果没有这行代码，手动调试时只能通过模块方式启动。
    unittest.main()  # 新增代码+DesktopGUIBridgeTest: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
