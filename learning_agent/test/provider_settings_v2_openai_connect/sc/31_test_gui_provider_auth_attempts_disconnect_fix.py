import json  # 新增代码+OpenAIAuthAttemptTest：解析 bridge JSON 响应；如果没有这行代码，HTTP 合同只能比较原始字节。
import os  # 新增代码+CodexLoginAttemptTest：临时设置官方 Codex CLI 登录模式；如果没有这行，auth-attempt 测试无法切换模式。
import socket  # 新增代码+DirectOAuthCallbackTest：寻找随机可用 callback 端口；如果没有这行代码，测试可能撞上真实 1455 服务。
import tempfile  # 新增代码+OpenAIAuthAttemptTest：创建隔离临时工作区；如果没有这行代码，测试会污染真实项目。
import threading  # 新增代码+OpenAIAuthAttemptTest：后台运行 GUI bridge server；如果没有这行代码，HTTP 测试会被 serve_forever 阻塞。
import time  # 新增代码+OpenAIAuthAttemptTailTest：构造过期 attempt 时间；如果没有这行代码，过期尾部行为只能靠慢等待。
import unittest  # 新增代码+OpenAIAuthAttemptTest：使用项目现有 unittest 风格；如果没有这行代码，测试类不会被标准 runner 发现。
import urllib.parse  # 新增代码+OpenAIAuthAttemptTest：构造 status query string；如果没有这行代码，attempt_id 里的特殊字符可能让 URL 错误。
import urllib.request  # 新增代码+OpenAIAuthAttemptTest：使用标准库请求本地 bridge；如果没有这行代码，测试需要额外依赖。
from pathlib import Path  # 新增代码+OpenAIAuthAttemptTest：用 Path 管理临时 workspace；如果没有这行代码，Windows 路径拼接容易出错。
from unittest import mock  # 新增代码+CodexLoginAttemptTest：替换 CodexAuthBridge 避免打开真实浏览器；如果没有这行，测试会影响用户本机登录状态。


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

    def test_start_chatgpt_browser_in_codex_cli_mode_returns_codex_login_attempt(self) -> None:  # 新增代码+CodexLoginAttemptTest：测试段开始，验证官方 Codex 模式下 browser 方法启动 codex login；如果没有这段，OpenAI 连接仍会停留在 mock。
        from learning_agent.app.gui_codex_auth_bridge import CodexAuthStatus  # 新增代码+CodexLoginAttemptTest：导入 Codex 登录状态对象；如果没有这行，fake bridge 无法返回未登录状态。
        from learning_agent.app.gui_provider_auth_attempts import start_provider_auth_attempt  # 新增代码+CodexLoginAttemptTest：导入 auth-attempt 启动入口；如果没有这行，测试没有被测函数。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+CodexLoginAttemptTest：创建临时 workspace；如果没有这行，测试会污染真实 provider 状态。
            with mock.patch.dict(os.environ, {"OPENHARNESS_OPENAI_AUTH_MODE": "codex_cli"}, clear=False):  # 新增代码+CodexLoginAttemptTest：临时启用官方 Codex CLI 模式；如果没有这行，start 会继续返回 mock attempt。
                with mock.patch("learning_agent.app.gui_provider_auth_attempts.CodexAuthBridge") as bridge_class:  # 新增代码+CodexLoginAttemptTest：替换真实 Codex bridge；如果没有这行，测试会打开真实浏览器。
                    bridge_class.return_value.start_login.return_value = {"ok": True, "mode": "codex_cli_login", "message": "Codex login started."}  # 新增代码+CodexLoginAttemptTest：模拟官方登录进程启动成功；如果没有这行，测试无法验证 pending 等待页。
                    bridge_class.return_value.login_status.return_value = CodexAuthStatus(available=True, connected=False, message="not logged in")  # 新增代码+CodexLoginAttemptTest：模拟启动后仍等待用户浏览器授权；如果没有这行，attempt 状态无法稳定为 pending。
                    payload = start_provider_auth_attempt(Path(directory), "openai", "chatgpt-browser")  # 新增代码+CodexLoginAttemptTest：启动 OpenAI browser auth-attempt；如果没有这行，后续没有响应可断言。
        serialized = json.dumps(payload, ensure_ascii=False).lower()  # 新增代码+CodexLoginAttemptTest：序列化响应做安全扫描；如果没有这行，嵌套敏感字段可能漏过。
        attempt = payload["attempt"]  # 新增代码+CodexLoginAttemptTest：取出 attempt 主体；如果没有这行，后续断言会重复索引。
        self.assertEqual("codex_cli_login", attempt["mode"])  # 新增代码+CodexLoginAttemptTest：确认 mode 是官方 Codex 登录；如果没有这行，前端无法渲染正确等待页。
        self.assertEqual("openai", attempt["provider_id"])  # 新增代码+CodexLoginAttemptTest：确认 provider id 保持 OpenAI；如果没有这行，status/cancel 可能无法归属。
        self.assertEqual("chatgpt-browser", attempt["auth_method_id"])  # 新增代码+CodexLoginAttemptTest：确认方法 id 保持 browser；如果没有这行，前端无法知道用户选择。
        self.assertEqual("pending", attempt["status"])  # 新增代码+CodexLoginAttemptTest：确认未登录时进入 pending；如果没有这行，等待页可能立即关闭。
        self.assertEqual("", attempt["url"])  # 新增代码+CodexLoginAttemptTest：确认官方 CLI 模式不需要前端 URL；如果没有这行，UI 可能要求无意义链接。
        self.assertEqual("browser_instruction", attempt["display_code_kind"])  # 新增代码+CodexLoginAttemptTest：确认展示类型是浏览器说明；如果没有这行，前端可能渲染成设备码。
        self.assertFalse(attempt["display_code_copyable"])  # 新增代码+CodexLoginAttemptTest：确认说明不可复制；如果没有这行，UI 会显示无意义复制按钮。
        self.assertNotIn("access_token", serialized)  # 新增代码+CodexLoginAttemptTest：确认响应不含 access token；如果没有这行，短期凭据可能进前端。
        self.assertNotIn("refresh_token", serialized)  # 新增代码+CodexLoginAttemptTest：确认响应不含 refresh token；如果没有这行，长期凭据可能进截图。
    # 新增代码+CodexLoginAttemptTest：测试段结束，test_start_chatgpt_browser_in_codex_cli_mode_returns_codex_login_attempt 到此结束；如果没有边界说明，用户不易看出官方登录启动覆盖范围。

    def test_codex_cli_reconnect_clears_local_disabled_override(self) -> None:  # 新增代码+ProviderReconnectTest：测试段开始，验证断开后主动重新连接会解除本地 disabled 覆盖；如果没有这段，用户断开 OpenAI 后可能无法再连回。
        from learning_agent.app.gui_codex_auth_bridge import CodexAuthStatus  # 新增代码+ProviderReconnectTest：导入 Codex 登录状态对象；如果没有这行，测试无法模拟 Codex CLI 状态。
        from learning_agent.app.gui_provider_auth_attempts import start_provider_auth_attempt  # 新增代码+ProviderReconnectTest：导入 auth-attempt 启动入口；如果没有这行，测试没有触发重新连接的动作。
        from learning_agent.app.gui_provider_settings import load_provider_settings, save_provider_settings  # 新增代码+ProviderReconnectTest：导入配置读写入口；如果没有这行，测试无法构造和确认 disabled 覆盖。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+ProviderReconnectTest：创建隔离 workspace；如果没有这行，测试会污染真实 provider 设置。
            workspace = Path(directory)  # 新增代码+ProviderReconnectTest：保存 Path workspace；如果没有这行，后续调用会重复转换路径。
            save_provider_settings(workspace, {"auth": {"openai": {"type": "disabled", "disabled_source": "codex_cli", "updated_at": 1}}, "custom_providers": {}, "model_visibility": {}})  # 新增代码+ProviderReconnectTest：先写入本地 disabled 覆盖；如果没有这行，测试无法证明重新连接会清理它。
            with mock.patch.dict(os.environ, {"OPENHARNESS_OPENAI_AUTH_MODE": "codex_cli"}, clear=False):  # 新增代码+ProviderReconnectTest：开启官方 Codex CLI 模式；如果没有这行，start 会走 mock 路径而不是官方登录。
                with mock.patch("learning_agent.app.gui_provider_auth_attempts.CodexAuthBridge") as bridge_class:  # 新增代码+ProviderReconnectTest：替换真实 Codex CLI；如果没有这行，测试可能打开真实浏览器。
                    bridge_class.return_value.start_login.return_value = {"ok": True, "mode": "codex_cli_login", "message": "Codex login started."}  # 新增代码+ProviderReconnectTest：模拟启动登录成功；如果没有这行，测试会进入 failed 分支。
                    bridge_class.return_value.login_status.return_value = CodexAuthStatus(available=True, connected=False, message="pending")  # 新增代码+ProviderReconnectTest：模拟登录仍在 pending；如果没有这行，无法确认 pending 也会清 disabled。
                    payload = start_provider_auth_attempt(workspace, "openai", "chatgpt-browser")  # 新增代码+ProviderReconnectTest：启动重新连接；如果没有这行，disabled 覆盖不会被触发清理。
            settings_after_reconnect = load_provider_settings(workspace)  # 新增代码+ProviderReconnectTest：读取重新连接后的配置；如果没有这行，无法确认 disabled 是否消失。

        self.assertEqual("pending", payload["attempt"]["status"])  # 新增代码+ProviderReconnectTest：确认测试覆盖 pending 连接过程；如果没有这行，测试可能只覆盖已完成的简单路径。
        self.assertNotIn("openai", settings_after_reconnect.get("auth", {}))  # 新增代码+ProviderReconnectTest：确认 disabled 覆盖已被移除；如果没有这行，重新连接后 catalog 仍会显示断开。
    # 新增代码+ProviderReconnectTest：测试段结束，test_codex_cli_reconnect_clears_local_disabled_override 到此结束；如果没有边界说明，用户不易看出它覆盖断开后的重连语义。

    def test_tail_behaviors_keep_auth_attempts_idempotent_and_non_secret(self) -> None:  # 新增代码+OpenAIAuthAttemptTailTest：测试段开始，覆盖重复 start、重复 cancel、未知 status、过期和重复 complete；如果没有这段，边缘状态可能在真实 GUI 中卡住。
        from learning_agent.app.gui_provider_auth_attempts import _ATTEMPTS, _ATTEMPT_LOCK, cancel_provider_auth_attempt, complete_provider_auth_attempt, get_provider_auth_attempt_status, start_provider_auth_attempt  # 新增代码+OpenAIAuthAttemptTailTest：导入状态机和受控测试入口；如果没有这行代码，测试无法精确制造尾部状态。
        from learning_agent.app.gui_provider_settings import provider_settings_file  # 新增代码+OpenAIAuthAttemptTailTest：导入 provider settings 文件路径；如果没有这行代码，重复 complete 是否二次写入无法验证。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+OpenAIAuthAttemptTailTest：创建隔离 workspace；如果没有这行代码，测试会污染真实 provider 配置。
            workspace = Path(directory)  # 新增代码+OpenAIAuthAttemptTailTest：保存 Path workspace；如果没有这行代码，后续函数需要重复转换。
            first = start_provider_auth_attempt(workspace, "openai", "chatgpt-headless")  # 新增代码+OpenAIAuthAttemptTailTest：启动第一个 pending attempt；如果没有这行代码，重复 start 没有旧对象可顶替。
            first_id = str(first["attempt"]["attempt_id"])  # 新增代码+OpenAIAuthAttemptTailTest：保存第一个 attempt id；如果没有这行代码，无法回查旧状态。
            second = start_provider_auth_attempt(workspace, "openai", "chatgpt-browser")  # 新增代码+OpenAIAuthAttemptTailTest：启动第二个同 provider attempt；如果没有这行代码，旧 pending 自动过期行为无法验证。
            first_after_second = get_provider_auth_attempt_status(first_id)  # 新增代码+OpenAIAuthAttemptTailTest：回查第一个 attempt；如果没有这行代码，旧 pending 是否收敛不可见。
            second_id = str(second["attempt"]["attempt_id"])  # 新增代码+OpenAIAuthAttemptTailTest：保存第二个 attempt id；如果没有这行代码，后续 cancel 无法定位。
            first_cancel = cancel_provider_auth_attempt(second_id)  # 新增代码+OpenAIAuthAttemptTailTest：第一次取消第二个 attempt；如果没有这行代码，重复 cancel 没有初始终态。
            second_cancel = cancel_provider_auth_attempt(second_id)  # 新增代码+OpenAIAuthAttemptTailTest：第二次取消同一个 attempt；如果没有这行代码，cancel 幂等性无法验证。
            unknown_status = get_provider_auth_attempt_status("auth_attempt_missing_tail")  # 新增代码+OpenAIAuthAttemptTailTest：读取未知 attempt 状态；如果没有这行代码，前端旧轮询可能收到 404 而不是 expired。
            expiring = start_provider_auth_attempt(workspace, "openai", "chatgpt-headless")  # 新增代码+OpenAIAuthAttemptTailTest：启动用于过期测试的 attempt；如果没有这行代码，无法制造超时状态。
            expiring_id = str(expiring["attempt"]["attempt_id"])  # 新增代码+OpenAIAuthAttemptTailTest：保存过期 attempt id；如果没有这行代码，无法修改对应对象。
            with _ATTEMPT_LOCK:  # 新增代码+OpenAIAuthAttemptTailTest：锁住 registry 修改测试时间；如果没有这行代码，状态机并发访问可能读到半更新对象。
                _ATTEMPTS[expiring_id].expires_at = time.time() - 1.0  # 新增代码+OpenAIAuthAttemptTailTest：把 attempt 人为设为已过期；如果没有这行代码，测试要等真实 10 分钟。
            expired = get_provider_auth_attempt_status(expiring_id)  # 新增代码+OpenAIAuthAttemptTailTest：读取过期 attempt 状态；如果没有这行代码，自动过期行为没有断言对象。
            completing = start_provider_auth_attempt(workspace, "openai", "chatgpt-headless")  # 新增代码+OpenAIAuthAttemptTailTest：启动用于重复 complete 的 attempt；如果没有这行代码，无法验证完成写入只发生一次。
            completing_id = str(completing["attempt"]["attempt_id"])  # 新增代码+OpenAIAuthAttemptTailTest：保存完成 attempt id；如果没有这行代码，complete 无法定位。
            completed_once = complete_provider_auth_attempt(workspace, completing_id)  # 新增代码+OpenAIAuthAttemptTailTest：第一次完成 mock attempt；如果没有这行代码，settings 不会写入 mock 连接。
            settings_after_first_complete = provider_settings_file(workspace).read_text(encoding="utf-8")  # 新增代码+OpenAIAuthAttemptTailTest：读取第一次 complete 后设置文件；如果没有这行代码，无法比较重复 complete 是否改写。
            completed_twice = complete_provider_auth_attempt(workspace, completing_id)  # 新增代码+OpenAIAuthAttemptTailTest：第二次完成同一个 attempt；如果没有这行代码，重复 complete 幂等性无法验证。
            settings_after_second_complete = provider_settings_file(workspace).read_text(encoding="utf-8")  # 新增代码+OpenAIAuthAttemptTailTest：读取第二次 complete 后设置文件；如果没有这行代码，无法确认没有二次写入。

        serialized = json.dumps([first_after_second, second, first_cancel, second_cancel, unknown_status, expired, completed_once, completed_twice], ensure_ascii=False)  # 新增代码+OpenAIAuthAttemptTailTest：序列化尾部响应做安全扫描；如果没有这行代码，嵌套敏感字段可能漏过。
        self.assertEqual(first_after_second["attempt"]["status"], "expired")  # 新增代码+OpenAIAuthAttemptTailTest：确认重复 start 会让旧 pending 过期；如果没有这行代码，旧等待页可能一直轮询。
        self.assertEqual(first_after_second["attempt"]["message"], "superseded_by_new_attempt")  # 新增代码+OpenAIAuthAttemptTailTest：确认旧 pending 过期原因稳定；如果没有这行代码，排查无法区分被替代和超时。
        self.assertEqual(second["attempt"]["status"], "pending")  # 新增代码+OpenAIAuthAttemptTailTest：确认新 attempt 仍是 pending；如果没有这行代码，重复 start 可能错误取消新对象。
        self.assertEqual(first_cancel["attempt"]["status"], "expired")  # 新增代码+OpenAIAuthAttemptTailTest：确认第一次 cancel 收敛为 expired；如果没有这行代码，前端关闭弹窗后可能残留 pending。
        self.assertEqual(second_cancel["attempt"]["status"], "expired")  # 新增代码+OpenAIAuthAttemptTailTest：确认第二次 cancel 仍返回 expired；如果没有这行代码，重复取消会让前端看到异常。
        self.assertEqual(second_cancel["attempt"]["message"], "cancelled_by_user")  # 新增代码+OpenAIAuthAttemptTailTest：确认重复 cancel 保留用户取消原因；如果没有这行代码，UI 可能显示不稳定消息。
        self.assertEqual(unknown_status["attempt"]["status"], "expired")  # 新增代码+OpenAIAuthAttemptTailTest：确认未知 attempt 以 expired 占位返回；如果没有这行代码，旧轮询可能因为 404 中断。
        self.assertEqual(unknown_status["attempt"]["message"], "auth_attempt_not_found")  # 新增代码+OpenAIAuthAttemptTailTest：确认未知 attempt 原因稳定；如果没有这行代码，排查不知道是旧 id 还是超时。
        self.assertEqual(expired["attempt"]["status"], "expired")  # 新增代码+OpenAIAuthAttemptTailTest：确认超时 pending 自动 expired；如果没有这行代码，等待页可能永久显示。
        self.assertEqual(expired["attempt"]["message"], "expired")  # 新增代码+OpenAIAuthAttemptTailTest：确认超时原因稳定；如果没有这行代码，用户不知道授权已经过期。
        self.assertEqual(completed_once["attempt"]["status"], "complete")  # 新增代码+OpenAIAuthAttemptTailTest：确认第一次 complete 成功；如果没有这行代码，mock 连接无法刷新。
        self.assertEqual(completed_twice["attempt"]["status"], "complete")  # 新增代码+OpenAIAuthAttemptTailTest：确认第二次 complete 仍保持 complete；如果没有这行代码，重复 complete 可能退化。
        self.assertEqual(settings_after_first_complete, settings_after_second_complete)  # 新增代码+OpenAIAuthAttemptTailTest：确认重复 complete 不二次写入 updated_at；如果没有这行代码，重复请求会制造不必要配置漂移。
        self.assertNotIn("refresh_token", serialized)  # 新增代码+OpenAIAuthAttemptTailTest：确认尾部响应不含 refresh token；如果没有这行代码，长期凭据泄露可能漏过。
        self.assertNotIn("access_token", serialized)  # 新增代码+OpenAIAuthAttemptTailTest：确认尾部响应不含 access token；如果没有这行代码，短期凭据可能进入 GUI。
        self.assertNotIn("id_token", serialized)  # 新增代码+OpenAIAuthAttemptTailTest：确认尾部响应不含 id token；如果没有这行代码，身份 token 可能进入截图。
        self.assertNotIn("secret_ref", serialized.lower())  # 新增代码+OpenAIAuthAttemptTailTest：确认尾部响应不含 secret_ref；如果没有这行代码，renderer 可能拿到后端密钥定位。
    # 新增代码+OpenAIAuthAttemptTailTest：测试段结束，尾部状态机合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_direct_oauth_attempt_returns_authorize_url_without_tokens(self) -> None:  # 新增代码+DirectOAuthAttemptTest：测试段开始，验证 direct OAuth start 返回授权 URL 且不泄露 token；如果没有这段，V1C 可能仍走 mock 或暴露凭据。
        from learning_agent.app.gui_provider_auth_attempts import start_provider_auth_attempt  # 新增代码+DirectOAuthAttemptTest：导入 auth-attempt 启动入口；如果没有这行代码，测试没有被测目标。

        env = {"OPENHARNESS_OPENAI_AUTH_MODE": "direct_oauth", "OPENHARNESS_OPENAI_EXPERIMENTAL": "1", "OPENHARNESS_PROVIDER_SECRET_STORE": "os_encrypted", "OPENHARNESS_OPENAI_CLIENT_ID": "openharness-local-test"}  # 新增代码+DirectOAuthAttemptTest：构造满足 direct OAuth 门禁的环境；如果没有这行代码，配置 helper 会硬拦截。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectOAuthAttemptTest：创建隔离 workspace；如果没有这行代码，测试会污染真实 provider 配置。
            with mock.patch.dict(os.environ, env, clear=False):  # 新增代码+DirectOAuthAttemptTest：临时启用 direct OAuth；如果没有这行代码，start 会继续返回 mock/codex 模式。
                payload = start_provider_auth_attempt(Path(directory), "openai", "chatgpt-browser")  # 新增代码+DirectOAuthAttemptTest：启动 OpenAI browser direct OAuth attempt；如果没有这行代码，后续没有响应可断言。

        serialized = json.dumps(payload, ensure_ascii=False).lower()  # 新增代码+DirectOAuthAttemptTest：序列化响应做泄露扫描；如果没有这行代码，嵌套敏感字段可能漏过。
        attempt = payload["attempt"]  # 新增代码+DirectOAuthAttemptTest：取出 attempt 主体；如果没有这行代码，后续断言会重复索引。
        self.assertEqual(attempt["mode"], "direct_oauth_browser")  # 新增代码+DirectOAuthAttemptTest：确认进入 direct OAuth browser 模式；如果没有这行代码，前端无法使用真实授权等待页。
        self.assertEqual(attempt["status"], "pending")  # 新增代码+DirectOAuthAttemptTest：确认 start 后等待浏览器授权；如果没有这行代码，UI 可能立即误完成。
        self.assertIn("https://auth.openai.com/oauth/authorize", attempt["url"])  # 新增代码+DirectOAuthAttemptTest：确认 URL 指向 OpenAI 授权页；如果没有这行代码，用户可能打开 mock 链接。
        self.assertIn("originator=openharness", attempt["url"])  # 新增代码+DirectOAuthAttemptTest：确认 originator 为 OpenHarness；如果没有这行代码，审计无法区分发起方。
        self.assertIn("client_id=openharness-local-test", attempt["url"])  # 新增代码+DirectOAuthAttemptTest：确认使用显式 client id；如果没有这行代码，可能误用 OpenCode client。
        self.assertNotIn("access_token", serialized)  # 新增代码+DirectOAuthAttemptTest：确认响应不含 access token 字段；如果没有这行代码，短期凭据可能进入前端。
        self.assertNotIn("refresh_token", serialized)  # 新增代码+DirectOAuthAttemptTest：确认响应不含 refresh token 字段；如果没有这行代码，长期凭据可能进入前端。
        self.assertNotIn('"id_token"', serialized)  # 修改代码+DirectOAuthAttemptTest：只扫描 raw id_token 字段而允许授权 URL 的 id_token_add_organizations 参数；如果没有这行代码，测试会把合法 OAuth 参数误判成凭据泄露。
    # 新增代码+DirectOAuthAttemptTest：测试段结束，direct OAuth start 合同到此结束；如果没有边界说明，用户不容易看出这里只启动授权不保存 token。

    def test_direct_oauth_connection_record_writes_only_token_ref_and_updates_catalog(self) -> None:  # 新增代码+DirectOAuthAttemptTest：测试段开始，验证 direct OAuth 完成后只落 token_ref 摘要；如果没有这段，主配置可能写入 raw token。
        from learning_agent.app.gui_provider_auth_attempts import save_direct_oauth_provider_connection  # 新增代码+DirectOAuthAttemptTest：导入 direct OAuth 连接记录 helper；如果没有这行代码，测试没有被测目标。
        from learning_agent.app.gui_provider_settings import build_provider_settings_payload, provider_settings_file  # 新增代码+DirectOAuthAttemptTest：导入 catalog 和设置路径；如果没有这行代码，无法验证落盘和 UI payload。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectOAuthAttemptTest：创建隔离 workspace；如果没有这行代码，测试会污染真实 provider 配置。
            workspace = Path(directory)  # 新增代码+DirectOAuthAttemptTest：保存 workspace 路径；如果没有这行代码，函数调用会重复转换。
            save_direct_oauth_provider_connection(workspace, token_ref="provider_oauth:openai", auth_method_id="chatgpt-browser")  # 新增代码+DirectOAuthAttemptTest：写入 direct OAuth 非敏感连接记录；如果没有这行代码，catalog 没有 direct 来源可显示。
            settings_text = provider_settings_file(workspace).read_text(encoding="utf-8")  # 新增代码+DirectOAuthAttemptTest：读取主设置文件；如果没有这行代码，落盘安全字段无法扫描。
            catalog = build_provider_settings_payload(workspace)  # 新增代码+DirectOAuthAttemptTest：读取 provider catalog；如果没有这行代码，UI 来源无法验证。

        serialized = json.dumps(catalog, ensure_ascii=False).lower()  # 新增代码+DirectOAuthAttemptTest：序列化 catalog 做泄露扫描；如果没有这行代码，嵌套敏感字段可能漏过。
        openai = next(provider for provider in catalog["providers"] if provider["id"] == "openai")  # 新增代码+DirectOAuthAttemptTest：取出 OpenAI provider；如果没有这行代码，无法确认 direct 状态。
        self.assertTrue(openai["connected"])  # 新增代码+DirectOAuthAttemptTest：确认 direct OAuth 记录让 provider connected；如果没有这行代码，登录成功后 UI 仍显示未连接。
        self.assertEqual(openai["source"], "direct_oauth_experimental")  # 新增代码+DirectOAuthAttemptTest：确认来源明确标成实验 direct OAuth；如果没有这行代码，用户会误以为是稳定 API key。
        self.assertEqual(openai["masked_key"], "ChatGPT OAuth token")  # 新增代码+DirectOAuthAttemptTest：确认只显示安全摘要；如果没有这行代码，UI 可能暴露 token_ref 或 raw token。
        self.assertIn("token_ref", settings_text)  # 新增代码+DirectOAuthAttemptTest：确认主配置只保存 token 引用；如果没有这行代码，后端无法关联加密 token store。
        self.assertNotIn("access_token", settings_text.lower())  # 新增代码+DirectOAuthAttemptTest：确认主配置不含 access token；如果没有这行代码，短期凭据可能落盘到 workspace。
        self.assertNotIn("refresh_token", settings_text.lower())  # 新增代码+DirectOAuthAttemptTest：确认主配置不含 refresh token；如果没有这行代码，长期凭据可能落盘到 workspace。
        self.assertNotIn("id_token", settings_text.lower())  # 新增代码+DirectOAuthAttemptTest：确认主配置不含 id token；如果没有这行代码，身份凭据可能落盘到 workspace。
        self.assertNotIn("access_token", serialized)  # 新增代码+DirectOAuthAttemptTest：确认 catalog 不含 access token 字段；如果没有这行代码，renderer 可能拿到短期凭据。
        self.assertNotIn("refresh_token", serialized)  # 新增代码+DirectOAuthAttemptTest：确认 catalog 不含 refresh token 字段；如果没有这行代码，renderer 可能拿到长期凭据。
        self.assertNotIn("id_token", serialized)  # 新增代码+DirectOAuthAttemptTest：确认 catalog 不含 id token 字段；如果没有这行代码，renderer 可能拿到身份凭据。
    # 新增代码+DirectOAuthAttemptTest：测试段结束，direct OAuth 连接记录合同到此结束；如果没有边界说明，用户不容易看出 raw token 不进入主配置。

    def test_direct_oauth_callback_server_completes_attempt_and_catalog(self) -> None:  # 新增代码+DirectOAuthCallbackTest：测试段开始，验证 direct OAuth callback server 能完成连接；如果没有这段，真实浏览器授权回来可能无人接收。
        from learning_agent.app.gui_provider_auth_attempts import get_provider_auth_attempt_status, start_provider_auth_attempt  # 新增代码+DirectOAuthCallbackTest：导入 start/status 状态机入口；如果没有这行代码，测试没有被测流程。
        from learning_agent.app.gui_provider_oauth_token_store import make_fake_token_store  # 新增代码+DirectOAuthCallbackTest：导入 fake token store；如果没有这行代码，测试会依赖真实 DPAPI。
        from learning_agent.app.gui_provider_settings import build_provider_settings_payload  # 新增代码+DirectOAuthCallbackTest：导入 provider catalog；如果没有这行代码，无法确认 callback 后 UI 状态。

        port_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 新增代码+DirectOAuthCallbackTest：创建临时 socket 寻找空闲端口；如果没有这行代码，测试只能硬编码端口。
        port_socket.bind(("127.0.0.1", 0))  # 新增代码+DirectOAuthCallbackTest：绑定随机空闲端口；如果没有这行代码，无法避开 1455 冲突。
        callback_port = int(port_socket.getsockname()[1])  # 新增代码+DirectOAuthCallbackTest：读取随机端口；如果没有这行代码，env 无法告诉后端监听哪里。
        port_socket.close()  # 新增代码+DirectOAuthCallbackTest：释放端口给 callback server；如果没有这行代码，后端绑定会失败。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectOAuthCallbackTest：创建隔离 workspace；如果没有这行代码，provider 设置会污染真实项目。
            workspace = Path(directory)  # 新增代码+DirectOAuthCallbackTest：保存 Path workspace；如果没有这行代码，后续路径调用会重复转换。
            fake_store = make_fake_token_store(workspace / "oauth_tokens")  # 新增代码+DirectOAuthCallbackTest：创建 fake OAuth token store；如果没有这行代码，callback 成功无法保存测试 token。
            env = {"OPENHARNESS_OPENAI_AUTH_MODE": "direct_oauth", "OPENHARNESS_OPENAI_EXPERIMENTAL": "1", "OPENHARNESS_PROVIDER_SECRET_STORE": "os_encrypted", "OPENHARNESS_OPENAI_CLIENT_ID": "openharness-local-test", "OPENHARNESS_OPENAI_OAUTH_CALLBACK_PORT": str(callback_port)}  # 新增代码+DirectOAuthCallbackTest：构造满足 direct OAuth 门禁且使用随机端口的环境；如果没有这行代码，start 会被配置层拦截或撞端口。
            with mock.patch.dict(os.environ, env, clear=False):  # 新增代码+DirectOAuthCallbackTest：临时启用 direct OAuth；如果没有这行代码，start 会继续走 mock。
                with mock.patch("learning_agent.app.gui_provider_openai_oauth.default_oauth_token_store", return_value=fake_store):  # 新增代码+DirectOAuthCallbackTest：让 OAuth attempt 使用 fake store；如果没有这行代码，测试会触碰真实加密凭据。
                    with mock.patch("learning_agent.app.gui_provider_openai_oauth.exchange_code_for_tokens", return_value={"access_token": "access-callback", "refresh_token": "refresh-callback", "expires_at": 1782500000000, "account_id": "acct-callback", "id_token": "id-callback"}):  # 新增代码+DirectOAuthCallbackTest：替换真实 token endpoint；如果没有这行代码，测试会访问网络。
                        started = start_provider_auth_attempt(workspace, "openai", "chatgpt-browser")  # 新增代码+DirectOAuthCallbackTest：启动 direct OAuth attempt 和本地 callback server；如果没有这行代码，后续没有回调目标。
                        attempt = started["attempt"]  # 新增代码+DirectOAuthCallbackTest：取出 attempt payload；如果没有这行代码，后续解析 URL 会重复索引。
                        params = urllib.parse.parse_qs(urllib.parse.urlparse(str(attempt["url"])).query)  # 新增代码+DirectOAuthCallbackTest：解析授权 URL query；如果没有这行代码，无法取 state。
                        callback_url = f"http://127.0.0.1:{callback_port}/auth/callback?" + urllib.parse.urlencode({"code": "callback-code", "state": params["state"][0]})  # 新增代码+DirectOAuthCallbackTest：构造模拟浏览器回调 URL；如果没有这行代码，callback server 不会收到 code/state。
                        with urllib.request.urlopen(callback_url, timeout=5) as response:  # 新增代码+DirectOAuthCallbackTest：访问 callback server；如果没有这行代码，授权完成路径不会运行。
                            callback_page = response.read().decode("utf-8")  # 新增代码+DirectOAuthCallbackTest：读取浏览器成功页；如果没有这行代码，无法确认用户可见页面。
                        status_payload = get_provider_auth_attempt_status(str(attempt["attempt_id"]))  # 新增代码+DirectOAuthCallbackTest：读取 callback 后 attempt 状态；如果没有这行代码，前端轮询结果无法验证。
                        catalog = build_provider_settings_payload(workspace)  # 新增代码+DirectOAuthCallbackTest：读取 provider catalog；如果没有这行代码，设置页 connected 状态无法验证。
                        stored_tokens = fake_store.get_tokens("openai") or {}  # 新增代码+DirectOAuthCallbackTest：读取 fake token store；如果没有这行代码，无法确认 token 保存到了后端 store。
        openai = next(provider for provider in catalog["providers"] if provider["id"] == "openai")  # 新增代码+DirectOAuthCallbackTest：取出 OpenAI provider；如果没有这行代码，无法断言 direct 来源。
        serialized = json.dumps([started, status_payload, catalog], ensure_ascii=False).lower()  # 新增代码+DirectOAuthCallbackTest：序列化 renderer 可见 payload 做泄露扫描；如果没有这行代码，嵌套 token 字段可能漏过。
        self.assertIn("Authorization Successful", callback_page)  # 新增代码+DirectOAuthCallbackTest：确认浏览器看到成功页；如果没有这行代码，真实用户不知道可以回 GUI。
        self.assertEqual("complete", status_payload["attempt"]["status"])  # 新增代码+DirectOAuthCallbackTest：确认 attempt 状态完成；如果没有这行代码，前端会继续等待。
        self.assertTrue(openai["connected"])  # 新增代码+DirectOAuthCallbackTest：确认 provider catalog 显示 connected；如果没有这行代码，设置页仍会显示未连接。
        self.assertEqual("direct_oauth_experimental", openai["source"])  # 新增代码+DirectOAuthCallbackTest：确认 provider 来源是 direct OAuth；如果没有这行代码，真实连接来源会被混淆。
        self.assertEqual("access-callback", stored_tokens.get("access_token"))  # 新增代码+DirectOAuthCallbackTest：确认 token 保存在后端 store；如果没有这行代码，模型层无法读取登录。
        self.assertNotIn("access_token", serialized)  # 新增代码+DirectOAuthCallbackTest：确认 renderer payload 不含 access_token；如果没有这行代码，短期 token 可能进前端。
        self.assertNotIn("refresh_token", serialized)  # 新增代码+DirectOAuthCallbackTest：确认 renderer payload 不含 refresh_token；如果没有这行代码，长期 token 可能泄露。
        self.assertNotIn('"id_token"', serialized)  # 新增代码+DirectOAuthCallbackTest：确认 renderer payload 不含 raw id_token 字段；如果没有这行代码，身份 token 可能进入截图。
    # 新增代码+DirectOAuthCallbackTest：测试段结束，direct OAuth callback server 合同到此结束；如果没有边界说明，用户不容易看出覆盖的是真实浏览器回调链路。


if __name__ == "__main__":  # 新增代码+OpenAIAuthAttemptTest：允许直接运行本测试文件；如果没有这行代码，手动调试需要记住 unittest 命令。
    unittest.main()  # 新增代码+OpenAIAuthAttemptTest：启动 unittest runner；如果没有这行代码，直接 python 文件不会执行测试。
