import json  # 新增代码+OpenAIAuthAttemptTest：解析 bridge JSON 响应；如果没有这行代码，HTTP 合同只能比较原始字节。
import tempfile  # 新增代码+OpenAIAuthAttemptTest：创建隔离临时工作区；如果没有这行代码，测试会污染真实项目。
import threading  # 新增代码+OpenAIAuthAttemptTest：后台运行 GUI bridge server；如果没有这行代码，HTTP 测试会被 serve_forever 阻塞。
import unittest  # 新增代码+OpenAIAuthAttemptTest：使用项目现有 unittest 风格；如果没有这行代码，测试类不会被标准 runner 发现。
import urllib.parse  # 新增代码+OpenAIAuthAttemptTest：构造 status query string；如果没有这行代码，attempt_id 里的特殊字符可能让 URL 错误。
import urllib.request  # 新增代码+OpenAIAuthAttemptTest：使用标准库请求本地 bridge；如果没有这行代码，测试需要额外依赖。
from pathlib import Path  # 新增代码+OpenAIAuthAttemptTest：用 Path 管理临时 workspace；如果没有这行代码，Windows 路径拼接容易出错。


class GuiProviderAuthAttemptsContractTests(unittest.TestCase):  # 新增代码+OpenAIAuthAttemptTest：测试类段开始，锁定 OpenAI mock auth-attempt 状态机；如果没有这个类，browser/headless 连接流程可能只有静态 UI。
    def _start_server(self, workspace: Path):  # 新增代码+OpenAIAuthAttemptTest：helper 段开始，启动带 token 的测试 bridge；如果没有这个 helper，每个 HTTP 测试都要重复端口和线程逻辑。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+OpenAIAuthAttemptTest：导入 GUI bridge server 工厂；如果没有这行代码，测试无法启动真实路由。

        server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+OpenAIAuthAttemptTest：绑定随机端口并固定 token；如果没有这行代码，测试容易端口冲突或 token 不稳定。
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+OpenAIAuthAttemptTest：创建后台服务线程；如果没有这行代码，HTTP 请求无法同时发出。
        thread.start()  # 新增代码+OpenAIAuthAttemptTest：启动 server 线程；如果没有这行代码，urllib 会连接失败。
        return server, thread  # 新增代码+OpenAIAuthAttemptTest：返回 server 和线程；如果没有这行代码，调用方无法关闭资源。
    # 新增代码+OpenAIAuthAttemptTest：helper 段结束，_start_server 到此结束；如果没有边界说明，初学者不易看出它只负责启动服务。

    def _url(self, server, path: str) -> str:  # 新增代码+OpenAIAuthAttemptTest：helper 段开始，拼接随机端口 URL；如果没有这段，端口读取会散落在测试里。
        host, port = server.server_address  # 新增代码+OpenAIAuthAttemptTest：读取真实监听地址；如果没有这行代码，端口 0 场景无法请求。
        return f"http://{host}:{port}{path}"  # 新增代码+OpenAIAuthAttemptTest：返回完整 URL；如果没有这行代码，urllib 没有目标地址。
    # 新增代码+OpenAIAuthAttemptTest：helper 段结束，_url 到此结束；如果没有边界说明，初学者不易看出它只负责拼 URL。

    def _get_json(self, server, path: str) -> dict[str, object]:  # 新增代码+OpenAIAuthAttemptTest：helper 段开始，发送带 token 的 GET；如果没有这段，路由测试会重复 header 写法。
        request = urllib.request.Request(self._url(server, path), headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+OpenAIAuthAttemptTest：构造认证 GET 请求；如果没有这行代码，安全门禁会返回 401。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+OpenAIAuthAttemptTest：发送 GET 请求；如果没有这行代码，测试不会真正触发 bridge 路由。
            return json.loads(response.read().decode("utf-8"))  # 新增代码+OpenAIAuthAttemptTest：解析 JSON 响应；如果没有这行代码，断言无法读取字段。
    # 新增代码+OpenAIAuthAttemptTest：helper 段结束，_get_json 到此结束；如果没有边界说明，初学者不易看出它只负责 GET。

    def _post_json(self, server, path: str, payload: dict[str, object]) -> dict[str, object]:  # 新增代码+OpenAIAuthAttemptTest：helper 段开始，发送带 token 的 JSON POST；如果没有这段，mutation 测试会重复编码和 header。
        raw_body = json.dumps(payload).encode("utf-8")  # 新增代码+OpenAIAuthAttemptTest：把 payload 编码成 UTF-8 JSON；如果没有这行代码，POST body 无法被 bridge 解析。
        request = urllib.request.Request(self._url(server, path), data=raw_body, method="POST", headers={"Content-Type": "application/json", "X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+OpenAIAuthAttemptTest：构造认证 POST 请求；如果没有这行代码，安全门禁会拒绝 mutation。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+OpenAIAuthAttemptTest：发送 POST 请求；如果没有这行代码，测试不会真正触发写入路由。
            return json.loads(response.read().decode("utf-8"))  # 新增代码+OpenAIAuthAttemptTest：解析 JSON 响应；如果没有这行代码，断言无法读取 mutation 结果。
    # 新增代码+OpenAIAuthAttemptTest：helper 段结束，_post_json 到此结束；如果没有边界说明，初学者不易看出它只负责 POST。

    def test_mock_auth_attempt_lifecycle_completes_without_real_secret(self) -> None:  # 新增代码+OpenAIAuthAttemptTest：测试段开始，验证 mock attempt 生命周期和安全落盘；如果没有这段，mock complete 可能写入真实 token 字段。
        from learning_agent.app.gui_provider_auth_attempts import complete_provider_auth_attempt, get_provider_auth_attempt_status, start_provider_auth_attempt  # 新增代码+OpenAIAuthAttemptTest：导入待测状态机函数；如果没有这行代码，测试没有被测目标。
        from learning_agent.app.gui_provider_settings import build_provider_settings_payload, provider_settings_file  # 新增代码+OpenAIAuthAttemptTest：导入 provider catalog 和设置文件路径；如果没有这行代码，无法验证 complete 后 catalog 和落盘内容。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+OpenAIAuthAttemptTest：创建临时 workspace；如果没有这行代码，状态机会污染真实项目。
            workspace = Path(directory)  # 新增代码+OpenAIAuthAttemptTest：保存 Path workspace；如果没有这行代码，后续路径会重复转换。
            started = start_provider_auth_attempt(workspace, "openai", "chatgpt-headless")  # 新增代码+OpenAIAuthAttemptTest：启动 OpenAI headless mock attempt；如果没有这行代码，状态机没有初始状态。
            attempt_id = str(started["attempt"]["attempt_id"])  # 新增代码+OpenAIAuthAttemptTest：读取 attempt id；如果没有这行代码，status/complete 无法定位同一次尝试。
            pending = get_provider_auth_attempt_status(attempt_id)  # 新增代码+OpenAIAuthAttemptTest：读取 pending 状态；如果没有这行代码，start 后状态无法验证。
            completed = complete_provider_auth_attempt(workspace, attempt_id)  # 新增代码+OpenAIAuthAttemptTest：完成 mock attempt；如果没有这行代码，complete 状态和 mock catalog 无法验证。
            catalog = build_provider_settings_payload(workspace)  # 新增代码+OpenAIAuthAttemptTest：读取 complete 后 provider catalog；如果没有这行代码，UI 刷新结果无法验证。
            settings_text = provider_settings_file(workspace).read_text(encoding="utf-8")  # 新增代码+OpenAIAuthAttemptTest：读取主设置文件；如果没有这行代码，落盘安全字段无法扫描。

        serialized = json.dumps([started, pending, completed, catalog], ensure_ascii=False)  # 新增代码+OpenAIAuthAttemptTest：序列化所有响应做泄露扫描；如果没有这行代码，嵌套 token 泄露可能漏过。
        openai = next(provider for provider in catalog["providers"] if provider["id"] == "openai")  # 新增代码+OpenAIAuthAttemptTest：取出 OpenAI provider；如果没有这行代码，无法确认 complete 后状态。
        self.assertEqual(started["attempt"]["status"], "pending")  # 新增代码+OpenAIAuthAttemptTest：确认 start 后进入 pending；如果没有这行代码，前端轮询没有稳定初态。
        self.assertEqual(started["attempt"]["display_code_kind"], "device_code")  # 新增代码+OpenAIAuthAttemptTest：确认 headless 使用设备码展示；如果没有这行代码，前端无法选择正确说明。
        self.assertTrue(started["attempt"]["display_code_copyable"])  # 新增代码+OpenAIAuthAttemptTest：确认设备码可复制；如果没有这行代码，用户无法方便输入授权码。
        self.assertEqual(pending["attempt"]["status"], "pending")  # 新增代码+OpenAIAuthAttemptTest：确认 status 返回 pending；如果没有这行代码，轮询可能拿到错误终态。
        self.assertEqual(completed["attempt"]["status"], "complete")  # 新增代码+OpenAIAuthAttemptTest：确认 mock complete 成功；如果没有这行代码，UI 无法进入完成态。
        self.assertIs(openai["connected"], True)  # 新增代码+OpenAIAuthAttemptTest：确认 mock complete 后 catalog 可显示连接状态；如果没有这行代码，完成后 UI 刷新仍像没连接。
        self.assertEqual(openai["source"], "mock")  # 新增代码+OpenAIAuthAttemptTest：确认连接来源明确为 mock；如果没有这行代码，用户可能误以为是真实 OAuth。
        self.assertNotIn("refresh_token", serialized)  # 新增代码+OpenAIAuthAttemptTest：确认响应不含 refresh token；如果没有这行代码，长期凭据泄露可能漏过。
        self.assertNotIn("access_token", serialized)  # 新增代码+OpenAIAuthAttemptTest：确认响应不含 access token；如果没有这行代码，短期凭据泄露可能漏过。
        self.assertNotIn("id_token", serialized)  # 新增代码+OpenAIAuthAttemptTest：确认响应不含 id token；如果没有这行代码，身份 token 泄露可能漏过。
        self.assertNotIn("secret_ref", serialized.lower())  # 新增代码+OpenAIAuthAttemptTest：确认响应不含 secret_ref；如果没有这行代码，renderer 可能拿到后端密钥定位信息。
        self.assertNotIn("refresh_token", settings_text)  # 新增代码+OpenAIAuthAttemptTest：确认主配置不落真实 refresh token；如果没有这行代码，mock flow 会违反稳定 V1 安全边界。
        self.assertNotIn("secret_ref", settings_text)  # 新增代码+OpenAIAuthAttemptTest：确认 mock auth 不写 secret_ref；如果没有这行代码，mock 连接可能伪装成真实 secret。
    # 新增代码+OpenAIAuthAttemptTest：测试段结束，mock 生命周期安全合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_bridge_auth_attempt_start_status_and_cancel_routes(self) -> None:  # 新增代码+OpenAIAuthAttemptTest：测试段开始，验证 bridge auth-attempt 路由；如果没有这段，前端只能调用不存在的端点。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+OpenAIAuthAttemptTest：创建临时 workspace；如果没有这行代码，HTTP 测试会污染真实项目。
            server, thread = self._start_server(Path(directory))  # 新增代码+OpenAIAuthAttemptTest：启动真实 GUI bridge；如果没有这行代码，测试没有目标服务。
            try:  # 新增代码+OpenAIAuthAttemptTest：确保 server 最终关闭；如果没有这行代码，失败时端口会泄漏。
                started = self._post_json(server, "/v2/gui/provider-settings/auth-attempt/start", {"provider_id": "openai", "auth_method_id": "chatgpt-browser"})  # 新增代码+OpenAIAuthAttemptTest：调用 start 路由；如果没有这行代码，前端无法启动 browser flow。
                attempt_id = str(started["attempt"]["attempt_id"])  # 新增代码+OpenAIAuthAttemptTest：读取 attempt id；如果没有这行代码，status/cancel 无法定位尝试。
                status_path = "/v2/gui/provider-settings/auth-attempt/status?" + urllib.parse.urlencode({"attempt_id": attempt_id})  # 新增代码+OpenAIAuthAttemptTest：构造 status URL；如果没有这行代码，GET route 无法带参数。
                pending = self._get_json(server, status_path)  # 新增代码+OpenAIAuthAttemptTest：调用 status 路由；如果没有这行代码，前端无法轮询。
                cancelled = self._post_json(server, "/v2/gui/provider-settings/auth-attempt/cancel", {"attempt_id": attempt_id})  # 新增代码+OpenAIAuthAttemptTest：调用 cancel 路由；如果没有这行代码，关闭 wizard 不会取消 attempt。
            finally:  # 新增代码+OpenAIAuthAttemptTest：清理 server；如果没有这行代码，后台线程和 socket 可能残留。
                server.shutdown()  # 新增代码+OpenAIAuthAttemptTest：停止 serve_forever；如果没有这行代码，测试进程可能挂住。
                server.server_close()  # 新增代码+OpenAIAuthAttemptTest：释放 socket；如果没有这行代码，Windows 端口可能短时间占用。
                thread.join(timeout=5)  # 新增代码+OpenAIAuthAttemptTest：等待后台线程退出；如果没有这行代码，测试结束时可能仍有线程。

        self.assertEqual(started["attempt"]["status"], "pending")  # 新增代码+OpenAIAuthAttemptTest：确认 start 路由返回 pending；如果没有这行代码，UI 没有等待态。
        self.assertEqual(started["attempt"]["display_code_kind"], "browser_instruction")  # 新增代码+OpenAIAuthAttemptTest：确认 browser flow 显示浏览器说明；如果没有这行代码，UI 会把 browser 误当设备码。
        self.assertEqual(pending["attempt"]["status"], "pending")  # 新增代码+OpenAIAuthAttemptTest：确认 status 路由返回 pending；如果没有这行代码，轮询无法正常工作。
        self.assertEqual(cancelled["attempt"]["status"], "expired")  # 新增代码+OpenAIAuthAttemptTest：确认 cancel 统一变为 expired；如果没有这行代码，状态 enum 会多出 cancel 分支。
        self.assertEqual(cancelled["attempt"]["message"], "cancelled_by_user")  # 新增代码+OpenAIAuthAttemptTest：确认取消原因稳定；如果没有这行代码，前端无法显示明确取消状态。
    # 新增代码+OpenAIAuthAttemptTest：测试段结束，bridge auth-attempt 路由合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


if __name__ == "__main__":  # 新增代码+OpenAIAuthAttemptTest：允许直接运行本测试文件；如果没有这行代码，手动调试需要记住 unittest 命令。
    unittest.main()  # 新增代码+OpenAIAuthAttemptTest：启动 unittest runner；如果没有这行代码，直接 python 文件不会执行测试。
