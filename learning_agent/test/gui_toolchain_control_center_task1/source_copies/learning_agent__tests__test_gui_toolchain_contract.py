import json  # 新增代码+DesktopGUIToolchainTest：解析 HTTP 响应 JSON；如果没有这行代码，测试无法检查工具链 payload 字段。
import tempfile  # 新增代码+DesktopGUIToolchainTest：创建隔离工作区；如果没有这行代码，测试会污染真实项目目录。
import threading  # 新增代码+DesktopGUIToolchainTest：后台启动 GUI bridge；如果没有这行代码，HTTP 路由测试会阻塞当前线程。
import unittest  # 新增代码+DesktopGUIToolchainTest：使用 unittest 承载后端合同测试；如果没有这行代码，测试不会被项目现有命令收集。
import urllib.request  # 新增代码+DesktopGUIToolchainTest：使用标准库请求本地 bridge；如果没有这行代码，HTTP route 无法被自动验证。
from pathlib import Path  # 新增代码+DesktopGUIToolchainTest：使用 Path 表示临时 workspace；如果没有这行代码，路径处理会退回易错字符串。


class GuiToolchainContractTests(unittest.TestCase):  # 新增代码+DesktopGUIToolchainTest：测试类段开始，锁定 GUI 工具链清单 contract；如果没有这个类，unittest 不会执行这些断言。
    def test_toolchain_payload_groups_existing_builtin_tools(self) -> None:  # 新增代码+DesktopGUIToolchainTest：测试方法开始，验证 payload 复用已有工具目录；如果没有这段测试，GUI 可能硬编码一份假工具表。
        from learning_agent.app.gui_toolchain import build_gui_toolchain_payload  # 新增代码+DesktopGUIToolchainTest：导入计划新增 helper；如果没有这行代码，测试无法锁定后端薄适配入口。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIToolchainTest：创建临时 workspace；如果没有这行代码，payload 构建可能读写真实项目状态。
            payload = build_gui_toolchain_payload(Path(directory))  # 新增代码+DesktopGUIToolchainTest：生成工具链清单 payload；如果没有这行代码，后续断言没有被测数据。

        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIToolchainTest：确认 payload 是成功响应；如果没有这行断言，错误响应可能误过。
        self.assertEqual(payload["schema_version"], 2)  # 新增代码+DesktopGUIToolchainTest：确认沿用 GUI V2 schema；如果没有这行断言，前后端版本可能漂移。
        self.assertGreater(payload["tool_count"], 10)  # 新增代码+DesktopGUIToolchainTest：确认不是少量硬编码工具；如果没有这行断言，清单可能没有复用完整目录。
        groups = {group["id"]: group for group in payload["groups"]}  # 新增代码+DesktopGUIToolchainTest：按 group id 建索引；如果没有这行代码，断言要反复遍历列表。
        self.assertIn("computer_use", groups)  # 新增代码+DesktopGUIToolchainTest：确认 Computer Use 能力包可见；如果没有这行断言，GUI 仍看不见桌面控制工具组。
        self.assertIn("planning", groups)  # 新增代码+DesktopGUIToolchainTest：确认 Planning 能力包可见；如果没有这行断言，todo/plan 类工具可能继续隐藏。
        self.assertIn("execution", groups)  # 新增代码+DesktopGUIToolchainTest：确认 Execution 能力包可见；如果没有这行断言，后台命令工具不会进入总地图。
        computer_tool_names = {tool["name"] for tool in groups["computer_use"]["tools"]}  # 新增代码+DesktopGUIToolchainTest：提取 Computer Use 工具名集合；如果没有这行代码，无法验证具体工具来自 schema。
        self.assertIn("read_last_observation", computer_tool_names)  # 新增代码+DesktopGUIToolchainTest：确认调试观察工具进入 GUI 清单；如果没有这行断言，Computer Use 面板后续缺事实来源。
        read_group_tools = [tool for group in payload["groups"] for tool in group["tools"] if tool["name"] == "read"]  # 新增代码+DesktopGUIToolchainTest：查找内核 read 工具；如果没有这行代码，无法确认基础工具没有丢失。
        self.assertEqual(read_group_tools[0]["source"], "builtin")  # 新增代码+DesktopGUIToolchainTest：确认工具来源标记来自内置目录；如果没有这行断言，GUI 无法区分内置和 MCP。
        self.assertIn("learning_agent.tools", read_group_tools[0]["reuse_module"])  # 新增代码+DesktopGUIToolchainTest：确认 payload 标记复用模块；如果没有这行断言，用户看不出不是重写工具链。
    # 新增代码+DesktopGUIToolchainTest：测试方法结束，test_toolchain_payload_groups_existing_builtin_tools 到此结束；如果没有这个边界说明，初学者不易看出合同范围。

    def test_toolchain_http_route_requires_token_and_returns_groups(self) -> None:  # 新增代码+DesktopGUIToolchainTest：测试方法开始，验证 HTTP 路由；如果没有这段测试，Electron 可能拿不到工具链清单。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIToolchainTest：导入现有 bridge 构造器；如果没有这行代码，测试无法启动真实本地 HTTP handler。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIToolchainTest：创建临时 workspace；如果没有这行代码，HTTP 测试会污染真实状态。
            server = create_gui_bridge_server(workspace=Path(directory), host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUIToolchainTest：用随机端口启动 bridge；如果没有这行代码，测试可能端口冲突。
            try:  # 新增代码+DesktopGUIToolchainTest：保护 server 清理；如果没有这行代码，断言失败会留下监听端口。
                thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIToolchainTest：创建后台服务线程；如果没有这行代码，请求会卡住当前线程。
                thread.start()  # 新增代码+DesktopGUIToolchainTest：启动 HTTP server；如果没有这行代码，urllib 会连接失败。
                host, port = server.server_address  # 新增代码+DesktopGUIToolchainTest：读取随机端口；如果没有这行代码，请求不知道目标地址。
                request = urllib.request.Request(f"http://{host}:{port}/v2/gui/toolchain", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUIToolchainTest：构造带 token 的 toolchain 请求；如果没有这行代码，无法验证安全路由。
                with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUIToolchainTest：请求工具链清单端点；如果没有这行代码，HTTP contract 没有被执行。
                    payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIToolchainTest：解析响应 JSON；如果没有这行代码，无法断言 payload 字段。
            finally:  # 新增代码+DesktopGUIToolchainTest：无论成功失败都关闭 server；如果没有这行代码，测试环境会残留后台线程。
                server.shutdown()  # 新增代码+DesktopGUIToolchainTest：停止 serve_forever；如果没有这行代码，后台线程可能继续运行。
                server.server_close()  # 新增代码+DesktopGUIToolchainTest：释放 socket；如果没有这行代码，Windows 上端口可能短时间占用。
        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIToolchainTest：确认 HTTP payload 成功；如果没有这行断言，错误页可能误过。
        self.assertIn("groups", payload)  # 新增代码+DesktopGUIToolchainTest：确认包含工具分组；如果没有这行断言，前端面板没有列表来源。
        self.assertGreater(payload["tool_count"], 10)  # 新增代码+DesktopGUIToolchainTest：确认 HTTP route 返回完整清单；如果没有这行断言，路由可能只返回空壳。
    # 新增代码+DesktopGUIToolchainTest：测试方法结束，test_toolchain_http_route_requires_token_and_returns_groups 到此结束；如果没有这个边界说明，初学者不易看出 HTTP 合同范围。
# 新增代码+DesktopGUIToolchainTest：测试类段结束，GuiToolchainContractTests 到此结束；如果没有这个边界说明，用户不容易看出本文件只测工具链清单。


if __name__ == "__main__":  # 新增代码+DesktopGUIToolchainTest：允许直接运行本文件；如果没有这行代码，手动调试时不会进入 unittest。
    unittest.main()  # 新增代码+DesktopGUIToolchainTest：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
