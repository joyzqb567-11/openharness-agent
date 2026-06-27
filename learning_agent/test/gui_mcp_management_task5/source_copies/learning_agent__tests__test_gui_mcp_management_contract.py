import json  # 新增代码+DesktopGUIMcpTest：用于把 payload 序列化后检查是否泄漏密钥；如果没有这行，测试无法覆盖完整 JSON 输出。
import tempfile  # 新增代码+DesktopGUIMcpTest：用于创建隔离工作区；如果没有这行，测试会污染真实项目目录。
import threading  # 新增代码+DesktopGUIMcpTest：用于启动真实 GUI bridge HTTP server；如果没有这行，路由测试无法并发响应。
import unittest  # 新增代码+DesktopGUIMcpTest：使用标准库测试框架；如果没有这行，测试类无法运行。
import urllib.request  # 新增代码+DesktopGUIMcpTest：用于真实请求本地 HTTP endpoint；如果没有这行，路由接线不会被验证。
from pathlib import Path  # 新增代码+DesktopGUIMcpTest：用于规范化临时工作区路径；如果没有这行，测试传参会退化为字符串。
from unittest.mock import patch  # 新增代码+DesktopGUIMcpTest：用于替换 MCP runtime 为可控 fake；如果没有这行，测试可能启动真实外部 MCP 进程。

from learning_agent.mcp.runtime import McpServerConfig  # 新增代码+DesktopGUIMcpTest：复用真实 MCP server 配置类型；如果没有这行，测试无法证明 GUI adapter 接受原 runtime 配置。


class _FakeMcpRegistry:  # 新增代码+DesktopGUIMcpTest：fake registry 类段开始，模拟真实 McpToolRegistry；如果没有这段，测试会依赖真实 MCP server。
    def __init__(self) -> None:  # 新增代码+DesktopGUIMcpTest：初始化 fake registry；如果没有这段，测试无法记录 close 是否执行。
        self.closed = False  # 新增代码+DesktopGUIMcpTest：记录 registry 是否关闭；如果没有这行，无法防止连接泄漏回归。
        self.started = False  # 新增代码+DesktopGUIMcpTest：记录 registry 是否启动；如果没有这行，无法确认 helper 复用了启动流程。
    # 新增代码+DesktopGUIMcpTest：fake registry 初始化段结束；如果没有边界说明，初学者不易看出字段用途。

    def start(self) -> None:  # 新增代码+DesktopGUIMcpTest：方法段开始，模拟 registry.start；如果没有这段，被测 helper 会缺少启动路径。
        self.started = True  # 新增代码+DesktopGUIMcpTest：标记已启动；如果没有这行，断言无法证明 helper 调用了 start。
    # 新增代码+DesktopGUIMcpTest：start 方法段结束；如果没有边界说明，fake 行为范围不清楚。

    def server_names(self) -> list[str]:  # 新增代码+DesktopGUIMcpTest：方法段开始，返回 runtime 管理的 server 名；如果没有这段，被测 helper 无法合并 registry server。
        return ["alpha", "remote"]  # 新增代码+DesktopGUIMcpTest：返回两个 server；如果没有这行，测试覆盖不到可用和失败两类状态。
    # 新增代码+DesktopGUIMcpTest：server_names 方法段结束；如果没有边界说明，fake 行为范围不清楚。

    def start_errors(self) -> dict[str, str]:  # 新增代码+DesktopGUIMcpTest：方法段开始，模拟启动错误；如果没有这段，失败 server 脱敏没有覆盖。
        return {"remote": "Authorization Bearer SECRET failed"}  # 新增代码+DesktopGUIMcpTest：返回包含敏感词的错误；如果没有这行，测试无法证明错误脱敏。
    # 新增代码+DesktopGUIMcpTest：start_errors 方法段结束；如果没有边界说明，fake 行为范围不清楚。

    def stream_state(self, server_name: str) -> dict[str, object]:  # 新增代码+DesktopGUIMcpTest：方法段开始，模拟 stream 状态；如果没有这段，stream_state 脱敏没有覆盖。
        if server_name == "alpha":  # 新增代码+DesktopGUIMcpTest：识别可用 server；如果没有这行，两个 server 会返回同一种状态。
            return {"connected": True, "token": "SECRET"}  # 新增代码+DesktopGUIMcpTest：返回含 secret 的 stream 字段；如果没有这行，stream 脱敏没有覆盖。
        return {"status": "failed", "secret": "SECRET"}  # 新增代码+DesktopGUIMcpTest：返回失败 stream 状态；如果没有这行，失败状态脱敏没有覆盖。
    # 新增代码+DesktopGUIMcpTest：stream_state 方法段结束；如果没有边界说明，fake 行为范围不清楚。

    def list_resources(self, server_name: str | None = None) -> list[dict[str, str]]:  # 新增代码+DesktopGUIMcpTest：方法段开始，模拟资源枚举；如果没有这段，resource_count 无法测试。
        if server_name == "remote":  # 新增代码+DesktopGUIMcpTest：让 remote 资源枚举失败；如果没有这行，降级路径没有覆盖。
            raise RuntimeError("remote token=SECRET bad")  # 新增代码+DesktopGUIMcpTest：抛出含 secret 的错误；如果没有这行，资源错误脱敏没有覆盖。
        return [{"name": "Repo Docs", "uri": "file://repo", "mimeType": "text/plain", "description": "safe"}]  # 新增代码+DesktopGUIMcpTest：返回一个资源；如果没有这行，资源列表会为空。
    # 新增代码+DesktopGUIMcpTest：list_resources 方法段结束；如果没有边界说明，fake 行为范围不清楚。

    def list_prompts(self, server_name: str | None = None) -> list[dict[str, object]]:  # 新增代码+DesktopGUIMcpTest：方法段开始，模拟 prompt 枚举；如果没有这段，prompt_count 无法测试。
        if server_name == "alpha":  # 新增代码+DesktopGUIMcpTest：只给 alpha 返回 prompt；如果没有这行，prompt 归属无法验证。
            return [{"name": "Review", "description": "Review prompt", "arguments": [{"name": "path", "required": True}]}]  # 新增代码+DesktopGUIMcpTest：返回一个 prompt；如果没有这行，prompt 列表会为空。
        return []  # 新增代码+DesktopGUIMcpTest：remote 没有 prompt；如果没有这行，方法可能返回 None 破坏 helper。
    # 新增代码+DesktopGUIMcpTest：list_prompts 方法段结束；如果没有边界说明，fake 行为范围不清楚。

    def close(self) -> None:  # 新增代码+DesktopGUIMcpTest：方法段开始，模拟 registry.close；如果没有这段，helper finally 可能报错。
        self.closed = True  # 新增代码+DesktopGUIMcpTest：标记已关闭；如果没有这行，测试无法验证连接释放。
    # 新增代码+DesktopGUIMcpTest：close 方法段结束；如果没有边界说明，fake 行为范围不清楚。


def _fake_configs() -> list[McpServerConfig]:  # 新增代码+DesktopGUIMcpTest：函数段开始，生成带敏感字段的 MCP 配置；如果没有这段，两个测试会重复配置。
    return [  # 新增代码+DesktopGUIMcpTest：返回配置列表；如果没有这行，函数没有输出。
        McpServerConfig(name="alpha", command="python", args=["--token=SECRET"], transport="stdio"),  # 新增代码+DesktopGUIMcpTest：stdio 配置带敏感参数；如果没有这行，args 脱敏没有覆盖。
        McpServerConfig(name="remote", command="", args=[], transport="http", url="https://example.com/mcp?token=SECRET", headers={"Authorization": "Bearer SECRET"}),  # 新增代码+DesktopGUIMcpTest：HTTP 配置带敏感 query/header；如果没有这行，URL/header 脱敏没有覆盖。
    ]  # 新增代码+DesktopGUIMcpTest：配置列表结束；如果没有这行，Python 列表语法不完整。
# 新增代码+DesktopGUIMcpTest：函数段结束，_fake_configs 到此结束；如果没有边界说明，测试配置来源不清楚。


class GuiMcpManagementContractTest(unittest.TestCase):  # 新增代码+DesktopGUIMcpTest：测试类段开始，验证 GUI MCP 管理合同；如果没有这段，Task 5 后端合同没有自动化保护。
    def test_mcp_inventory_reuses_runtime_and_redacts_secrets(self) -> None:  # 新增代码+DesktopGUIMcpTest：测试方法开始，验证 payload 复用 runtime 且不泄漏 secret；如果没有这段，脱敏回归难以及时发现。
        from learning_agent.app.gui_mcp_control import build_gui_mcp_inventory_payload  # 新增代码+DesktopGUIMcpTest：导入被测 helper；如果没有这行，测试没有目标函数。
        fake_registry = _FakeMcpRegistry()  # 新增代码+DesktopGUIMcpTest：创建 fake registry；如果没有这行，patch 无法返回可检查对象。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIMcpTest：创建临时工作区；如果没有这行，测试会污染真实文件。
            with patch("learning_agent.app.gui_mcp_control.load_mcp_server_configs", return_value=_fake_configs()):  # 新增代码+DesktopGUIMcpTest：替换配置加载；如果没有这行，测试会依赖真实 mcp_servers.json。
                with patch("learning_agent.app.gui_mcp_control.McpToolRegistry.from_configs", return_value=fake_registry):  # 新增代码+DesktopGUIMcpTest：替换 registry 创建；如果没有这行，测试可能启动真实 MCP 进程。
                    payload = build_gui_mcp_inventory_payload(Path(directory))  # 新增代码+DesktopGUIMcpTest：生成 MCP 管理 payload；如果没有这行，后续断言没有输入。
        serialized = json.dumps(payload, ensure_ascii=False)  # 新增代码+DesktopGUIMcpTest：序列化完整 payload；如果没有这行，深层字段泄漏不易检查。
        self.assertTrue(fake_registry.started)  # 新增代码+DesktopGUIMcpTest：确认调用了 registry.start；如果没有这行，GUI 可能只读静态配置。
        self.assertTrue(fake_registry.closed)  # 新增代码+DesktopGUIMcpTest：确认调用了 registry.close；如果没有这行，刷新可能泄漏 MCP 子进程。
        self.assertTrue(payload["ok"])  # 新增代码+DesktopGUIMcpTest：确认响应成功；如果没有这行，payload 形状可能错误。
        self.assertEqual(payload["server_count"], 2)  # 新增代码+DesktopGUIMcpTest：确认 server 数量；如果没有这行，配置合并可能漏 server。
        self.assertEqual(payload["resource_count"], 1)  # 新增代码+DesktopGUIMcpTest：确认资源数量；如果没有这行，resource 枚举可能失效。
        self.assertEqual(payload["prompt_count"], 1)  # 新增代码+DesktopGUIMcpTest：确认 prompt 数量；如果没有这行，prompt 枚举可能失效。
        self.assertIn("learning_agent.mcp.runtime", serialized)  # 新增代码+DesktopGUIMcpTest：确认 payload 标注复用模块；如果没有这行，用户无法验收是否复用原代码。
        self.assertNotIn("SECRET", serialized)  # 新增代码+DesktopGUIMcpTest：确认明文 secret 不存在；如果没有这行，密钥泄漏可能回归。
        self.assertNotIn("Bearer", serialized)  # 新增代码+DesktopGUIMcpTest：确认 bearer 文案不泄漏；如果没有这行，authorization 错误可能泄漏。
        self.assertNotIn("Authorization", serialized)  # 新增代码+DesktopGUIMcpTest：确认 header 名不暴露；如果没有这行，header 配置可能进入 GUI。
        self.assertNotIn("token=SECRET", serialized)  # 新增代码+DesktopGUIMcpTest：确认 URL query 不泄漏；如果没有这行，远程 MCP URL secret 可能进入 GUI。
    # 新增代码+DesktopGUIMcpTest：test_mcp_inventory_reuses_runtime_and_redacts_secrets 方法段结束；如果没有边界说明，测试范围不清楚。

    def test_mcp_bridge_routes_return_safe_collections(self) -> None:  # 新增代码+DesktopGUIMcpTest：测试方法开始，验证三个 HTTP endpoint；如果没有这段，bridge 路由接线可能漏测。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIMcpTest：导入真实 bridge server；如果没有这行，无法测试 HTTP 路由。
        fake_registry = _FakeMcpRegistry()  # 新增代码+DesktopGUIMcpTest：创建 fake registry；如果没有这行，HTTP 路由可能启动真实 MCP。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIMcpTest：创建临时工作区；如果没有这行，测试会污染真实项目。
            with patch("learning_agent.app.gui_mcp_control.load_mcp_server_configs", return_value=_fake_configs()):  # 新增代码+DesktopGUIMcpTest：替换配置加载；如果没有这行，路由会读真实配置。
                with patch("learning_agent.app.gui_mcp_control.McpToolRegistry.from_configs", return_value=fake_registry):  # 新增代码+DesktopGUIMcpTest：替换 registry 创建；如果没有这行，路由可能启动真实外部进程。
                    server = create_gui_bridge_server(workspace=Path(directory), host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUIMcpTest：启动随机端口 bridge；如果没有这行，HTTP 请求没有目标。
                    thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIMcpTest：创建后台服务线程；如果没有这行，urlopen 会连接不到 server。
                    thread.start()  # 新增代码+DesktopGUIMcpTest：启动服务线程；如果没有这行，路由不会响应。
                    try:  # 新增代码+DesktopGUIMcpTest：确保 server 最终关闭；如果没有这行，测试失败时端口可能残留。
                        host, port = server.server_address  # 新增代码+DesktopGUIMcpTest：读取随机端口；如果没有这行，请求 URL 无法构造。
                        for path, kind in [("/v2/gui/mcp/servers", "servers"), ("/v2/gui/mcp/resources", "resources"), ("/v2/gui/mcp/prompts", "prompts")]:  # 新增代码+DesktopGUIMcpTest：遍历三个 endpoint；如果没有这行，只会覆盖其中一个路由。
                            request = urllib.request.Request(f"http://{host}:{port}{path}", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUIMcpTest：构造带 token 的 GET 请求；如果没有这行，安全门禁会拒绝。
                            with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUIMcpTest：发送请求并读取响应；如果没有这行，路由接线不会执行。
                                payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIMcpTest：解析 JSON 响应；如果没有这行，后续无法断言字段。
                            self.assertEqual(payload["kind"], kind)  # 新增代码+DesktopGUIMcpTest：确认 endpoint 返回正确集合名；如果没有这行，路径解析可能错误。
                            self.assertIn("data", payload)  # 新增代码+DesktopGUIMcpTest：确认集合 data 字段存在；如果没有这行，前端按需刷新会失败。
                            self.assertEqual(payload["server_count"], 2)  # 新增代码+DesktopGUIMcpTest：确认路由返回总览字段；如果没有这行，MCP 面板会缺 server 概览。
                    finally:  # 新增代码+DesktopGUIMcpTest：清理 HTTP server；如果没有这行，测试进程可能不退出。
                        server.shutdown()  # 新增代码+DesktopGUIMcpTest：停止 server；如果没有这行，后台线程会继续占端口。
                        server.server_close()  # 新增代码+DesktopGUIMcpTest：关闭监听 socket；如果没有这行，Windows 可能短时间占用端口。
    # 新增代码+DesktopGUIMcpTest：test_mcp_bridge_routes_return_safe_collections 方法段结束；如果没有边界说明，测试范围不清楚。


if __name__ == "__main__":  # 新增代码+DesktopGUIMcpTest：允许直接运行本测试文件；如果没有这行，手动调试需要记 unittest 模块参数。
    unittest.main()  # 新增代码+DesktopGUIMcpTest：启动 unittest；如果没有这行，直接运行文件不会执行测试。
