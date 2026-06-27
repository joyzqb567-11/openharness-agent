import json  # 新增代码+ProviderSettingsContractTest：解析 GUI bridge JSON 响应；如果没有这行代码，HTTP 合同只能比较原始字节。
import http.server  # 新增代码+ProviderSettingsContractTest：启动本地假 OpenAI-compatible /models 服务；如果没有这行代码，连接探针测试只能 mock 而不能真实 HTTP。
import os  # 新增代码+CodexLoginCatalogTest：临时设置官方 Codex CLI 登录模式；如果没有这行，测试无法验证 env 驱动的 provider catalog。
import tempfile  # 新增代码+ProviderSettingsContractTest：创建隔离临时工作区；如果没有这行代码，测试会污染真实项目目录。
import threading  # 新增代码+ProviderSettingsContractTest：后台运行 HTTP server；如果没有这行代码，测试请求会被 serve_forever 阻塞。
import unittest  # 新增代码+ProviderSettingsContractTest：使用项目现有 unittest 风格；如果没有这行代码，测试类不会被标准 runner 发现。
import urllib.error  # 新增代码+ProviderSettingsContractTest：读取结构化 HTTP 错误响应；如果没有这行代码，非法 provider 测试无法断言错误码。
import urllib.request  # 新增代码+ProviderSettingsContractTest：使用标准库请求本地 bridge；如果没有这行代码，测试需要额外依赖。
from pathlib import Path  # 新增代码+ProviderSettingsContractTest：用 Path 管理临时 workspace；如果没有这行代码，Windows 路径拼接容易出错。
from unittest import mock  # 新增代码+CodexLoginCatalogTest：替换 CodexAuthBridge 避免调用真实 CLI；如果没有这行，测试会依赖用户本机登录状态。


class _FakeModelsHandler(http.server.BaseHTTPRequestHandler):  # 新增代码+ProviderSettingsContractTest：类段开始，提供本地 /v1/models 测试服务；如果没有这个类，test-connection 无法做真实 HTTP 探针。
    def log_message(self, format: str, *args: object) -> None:  # 新增代码+ProviderSettingsContractTest：函数段开始，关闭测试 HTTP 日志；如果没有这段，pytest 输出会被请求日志污染。
        return  # 新增代码+ProviderSettingsContractTest：静默访问日志；如果没有这行代码，测试输出噪声会变多。
    # 新增代码+ProviderSettingsContractTest：函数段结束，log_message 到此结束；如果没有边界说明，初学者不易看出它只负责降噪。

    def do_GET(self) -> None:  # 新增代码+ProviderSettingsContractTest：函数段开始，响应 /v1/models；如果没有这段，连接探针会收到 404。
        if self.path != "/v1/models":  # 新增代码+ProviderSettingsContractTest：只允许模型列表路径；如果没有这行代码，错误路径也会误成功。
            self.send_response(404)  # 新增代码+ProviderSettingsContractTest：返回路径不存在；如果没有这行代码，探针无法验证路径拼接。
            self.end_headers()  # 新增代码+ProviderSettingsContractTest：结束 404 header；如果没有这行代码，HTTP 响应不完整。
            return  # 新增代码+ProviderSettingsContractTest：404 后停止；如果没有这行代码，后续会继续写成功响应。
        raw_body = json.dumps({"data": [{"id": "local-model"}]}).encode("utf-8")  # 新增代码+ProviderSettingsContractTest：构造 OpenAI-compatible models 响应；如果没有这行代码，探针无法统计模型数量。
        self.send_response(200)  # 新增代码+ProviderSettingsContractTest：返回成功状态；如果没有这行代码，探针会判定网络失败。
        self.send_header("Content-Type", "application/json")  # 新增代码+ProviderSettingsContractTest：声明 JSON 类型；如果没有这行代码，客户端仍可读但合同不完整。
        self.send_header("Content-Length", str(len(raw_body)))  # 新增代码+ProviderSettingsContractTest：声明 body 长度；如果没有这行代码，urllib 可能等待连接关闭。
        self.end_headers()  # 新增代码+ProviderSettingsContractTest：结束响应头；如果没有这行代码，响应体不会发送。
        self.wfile.write(raw_body)  # 新增代码+ProviderSettingsContractTest：写出 JSON body；如果没有这行代码，探针读不到模型数据。
    # 新增代码+ProviderSettingsContractTest：函数段结束，do_GET 到此结束；如果没有边界说明，初学者不易看出它只模拟 /models。


class GuiProviderSettingsContractTests(unittest.TestCase):  # 新增代码+ProviderSettingsContractTest：测试类段开始，锁定 Provider Settings V1 后端合同；如果没有这个类，Provider 设置页可能接到不安全 payload。
    def _start_server(self, workspace: Path):  # 新增代码+ProviderSettingsContractTest：helper 段开始，启动带 token 的测试 bridge；如果没有这个 helper，每个 HTTP 测试都要重复端口和线程逻辑。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+ProviderSettingsContractTest：导入 GUI bridge server 工厂；如果没有这行代码，测试无法启动真实路由。

        server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+ProviderSettingsContractTest：绑定随机端口并固定 token；如果没有这行代码，测试容易端口冲突或 token 不稳定。
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+ProviderSettingsContractTest：创建后台服务线程；如果没有这行代码，HTTP 请求无法同时发出。
        thread.start()  # 新增代码+ProviderSettingsContractTest：启动 server 线程；如果没有这行代码，urllib 会连接失败。
        return server, thread  # 新增代码+ProviderSettingsContractTest：返回 server 和线程；如果没有这行代码，调用方无法关闭资源。
    # 新增代码+ProviderSettingsContractTest：helper 段结束，_start_server 到此结束；如果没有边界说明，初学者不易看出它只负责启动服务。

    def _url(self, server, path: str) -> str:  # 新增代码+ProviderSettingsContractTest：helper 段开始，拼接随机端口 URL；如果没有这段，端口读取会散落在测试里。
        host, port = server.server_address  # 新增代码+ProviderSettingsContractTest：读取真实监听地址；如果没有这行代码，端口 0 场景无法请求。
        return f"http://{host}:{port}{path}"  # 新增代码+ProviderSettingsContractTest：返回完整 URL；如果没有这行代码，urllib 没有目标地址。
    # 新增代码+ProviderSettingsContractTest：helper 段结束，_url 到此结束；如果没有边界说明，初学者不易看出它只负责拼 URL。

    def _get_json(self, server, path: str) -> dict[str, object]:  # 新增代码+ProviderSettingsContractTest：helper 段开始，发送带 token 的 GET；如果没有这段，路由测试会重复 header 写法。
        request = urllib.request.Request(self._url(server, path), headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+ProviderSettingsContractTest：构造认证 GET 请求；如果没有这行代码，安全门禁会返回 401。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+ProviderSettingsContractTest：发送 GET 请求；如果没有这行代码，测试不会真正触发 bridge 路由。
            return json.loads(response.read().decode("utf-8"))  # 新增代码+ProviderSettingsContractTest：解析 JSON 响应；如果没有这行代码，断言无法读取字段。
    # 新增代码+ProviderSettingsContractTest：helper 段结束，_get_json 到此结束；如果没有边界说明，初学者不易看出它只负责 GET。

    def _post_json(self, server, path: str, payload: dict[str, object]) -> dict[str, object]:  # 新增代码+ProviderSettingsContractTest：helper 段开始，发送带 token 的 JSON POST；如果没有这段，mutation 测试会重复编码和 header。
        raw_body = json.dumps(payload).encode("utf-8")  # 新增代码+ProviderSettingsContractTest：把 payload 编码成 UTF-8 JSON；如果没有这行代码，POST body 无法被 bridge 解析。
        request = urllib.request.Request(self._url(server, path), data=raw_body, method="POST", headers={"Content-Type": "application/json", "X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+ProviderSettingsContractTest：构造认证 POST 请求；如果没有这行代码，安全门禁会拒绝 mutation。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+ProviderSettingsContractTest：发送 POST 请求；如果没有这行代码，测试不会真正触发写入路由。
            return json.loads(response.read().decode("utf-8"))  # 新增代码+ProviderSettingsContractTest：解析 JSON 响应；如果没有这行代码，断言无法读取 mutation 结果。
    # 新增代码+ProviderSettingsContractTest：helper 段结束，_post_json 到此结束；如果没有边界说明，初学者不易看出它只负责 POST。

    def _post_json_error(self, server, path: str, payload: dict[str, object]) -> dict[str, object]:  # 新增代码+ProviderSettingsContractTest：helper 段开始，发送预期失败的 JSON POST；如果没有这段，非法输入测试无法读取错误 payload。
        raw_body = json.dumps(payload).encode("utf-8")  # 新增代码+ProviderSettingsContractTest：把错误场景 payload 编码成 JSON；如果没有这行代码，bridge 无法解析请求。
        request = urllib.request.Request(self._url(server, path), data=raw_body, method="POST", headers={"Content-Type": "application/json", "X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+ProviderSettingsContractTest：构造认证 POST 请求；如果没有这行代码，测试会因未授权而不是输入错误失败。
        try:  # 新增代码+ProviderSettingsContractTest：捕获预期 HTTPError；如果没有这行代码，400 响应会直接让测试中断。
            urllib.request.urlopen(request, timeout=5)  # 新增代码+ProviderSettingsContractTest：发出预期失败请求；如果没有这行代码，非法输入不会真正经过 handler。
        except urllib.error.HTTPError as error:  # 新增代码+ProviderSettingsContractTest：读取 bridge 结构化错误；如果没有这行代码，无法断言错误 code。
            return json.loads(error.read().decode("utf-8"))  # 新增代码+ProviderSettingsContractTest：返回错误 JSON；如果没有这行代码，调用方只能看到状态码。
        self.fail("Expected provider settings mutation to fail.")  # 新增代码+ProviderSettingsContractTest：如果请求意外成功则失败；如果没有这行代码，非法输入被接受也会误过。
    # 新增代码+ProviderSettingsContractTest：helper 段结束，_post_json_error 到此结束；如果没有边界说明，初学者不易看出它只负责错误 POST。

    def _start_fake_models_server(self):  # 新增代码+ProviderSettingsContractTest：helper 段开始，启动本地 OpenAI-compatible models 服务；如果没有这段，每个探针测试都要重复 server 线程逻辑。
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _FakeModelsHandler)  # 新增代码+ProviderSettingsContractTest：绑定随机端口；如果没有这行代码，测试可能端口冲突。
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+ProviderSettingsContractTest：创建后台线程；如果没有这行代码，HTTP 请求无法同时发送。
        thread.start()  # 新增代码+ProviderSettingsContractTest：启动假服务；如果没有这行代码，探针会连接失败。
        return server, thread  # 新增代码+ProviderSettingsContractTest：返回 server 和线程；如果没有这行代码，调用方无法关闭资源。
    # 新增代码+ProviderSettingsContractTest：helper 段结束，_start_fake_models_server 到此结束；如果没有边界说明，初学者不易看出它只负责假服务。

    def test_provider_settings_catalog_route_returns_redacted_catalog(self) -> None:  # 新增代码+ProviderSettingsContractTest：测试段开始，验证 Provider catalog HTTP 路由；如果没有这段测试，前端设置页可能拿到不完整或泄密 catalog。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+ProviderSettingsContractTest：创建临时 workspace；如果没有这行代码，HTTP 测试会污染真实项目。
            server, thread = self._start_server(Path(directory))  # 新增代码+ProviderSettingsContractTest：启动真实 GUI bridge；如果没有这行代码，测试没有目标服务。
            try:  # 新增代码+ProviderSettingsContractTest：确保 server 最终关闭；如果没有这行代码，失败时端口会泄漏。
                payload = self._get_json(server, "/v2/gui/provider-settings/providers")  # 新增代码+ProviderSettingsContractTest：请求 Provider catalog；如果没有这行代码，无法验证新增 GET 路由。
            finally:  # 新增代码+ProviderSettingsContractTest：清理 server；如果没有这行代码，后台线程和 socket 可能残留。
                server.shutdown()  # 新增代码+ProviderSettingsContractTest：停止 serve_forever；如果没有这行代码，测试进程可能挂住。
                server.server_close()  # 新增代码+ProviderSettingsContractTest：释放 socket；如果没有这行代码，Windows 端口可能短时间占用。
                thread.join(timeout=5)  # 新增代码+ProviderSettingsContractTest：等待后台线程退出；如果没有这行代码，测试结束时可能仍有线程。

        serialized = json.dumps(payload, ensure_ascii=False)  # 新增代码+ProviderSettingsContractTest：序列化整包做泄露扫描；如果没有这行代码，嵌套字段泄露可能漏过。
        provider_ids = {str(item["id"]) for item in payload["providers"] if isinstance(item, dict)}  # 新增代码+ProviderSettingsContractTest：收集真实 provider ids；如果没有这行代码，后续断言无法检查 catalog 覆盖。
        self.assertTrue(payload["ok"])  # 新增代码+ProviderSettingsContractTest：确认路由返回成功；如果没有这行代码，错误 payload 也可能误过。
        self.assertEqual(payload["schema_version"], 4)  # 修改代码+ModelFailureStateTest：确认 Provider catalog 使用 V4 schema；如果没有这行代码，前端无法区分旧模型列表和带最近失败字段的新合同。
        self.assertTrue({"github-copilot", "openai", "google", "openrouter", "vercel"}.issubset(provider_ids))  # 新增代码+ProviderSettingsContractTest：确认五个内置 provider 都存在；如果没有这行代码，设置页会缺常用入口。
        self.assertNotIn("custom", provider_ids)  # 新增代码+ProviderSettingsContractTest：确认 custom 不是真实 provider id；如果没有这行代码，多自定义 provider 语义会混乱。
        self.assertEqual(payload["custom_provider_cta"]["id"], "custom-provider-cta")  # 新增代码+ProviderSettingsContractTest：确认自定义入口是虚拟 CTA；如果没有这行代码，前端可能把 CTA 当成 provider 保存。
        openai = next(item for item in payload["providers"] if item["id"] == "openai")  # 新增代码+OpenAIConnectCatalogTest：取出 OpenAI provider；如果没有这行代码，下面只能笼统检查列表而不能锁定 OpenAI 连接入口。
        openai_methods = openai["auth_methods"]  # 新增代码+OpenAIConnectCatalogTest：读取 OpenAI 认证方法列表；如果没有这行代码，方法顺序和字段无法被明确断言。
        self.assertEqual([method["id"] for method in openai_methods], ["chatgpt-browser", "chatgpt-headless", "api-key"])  # 新增代码+OpenAIConnectCatalogTest：锁定 OpenCode 风格方法顺序；如果没有这行代码，前端方法选择器可能出现错误顺序或缺项。
        browser_method = openai_methods[0]  # 新增代码+OpenAIConnectCatalogTest：取 browser 登录方法；如果没有这行代码，无法确认浏览器登录是自动 OAuth 类方法。
        headless_method = openai_methods[1]  # 新增代码+OpenAIConnectCatalogTest：取 headless 登录方法；如果没有这行代码，无法确认设备码登录是自动 OAuth 类方法。
        api_key_method = openai_methods[2]  # 新增代码+OpenAIConnectCatalogTest：取 API key 登录方法；如果没有这行代码，无法确认真实密钥路径仍保留。
        self.assertEqual(browser_method["type"], "oauth")  # 新增代码+OpenAIConnectCatalogTest：确认 browser 方法属于 OAuth 类型；如果没有这行代码，前端可能把它渲染成普通表单。
        self.assertEqual(browser_method["mode"], "auto")  # 新增代码+OpenAIConnectCatalogTest：确认 browser 方法使用自动 attempt flow；如果没有这行代码，前端无法进入等待授权页。
        self.assertTrue(browser_method["experimental"])  # 新增代码+OpenAIConnectCatalogTest：确认 browser 方法带实验标记；如果没有这行代码，用户会误以为真实 OAuth 已稳定完成。
        self.assertEqual(headless_method["type"], "oauth")  # 新增代码+OpenAIConnectCatalogTest：确认 headless 方法属于 OAuth 类型；如果没有这行代码，前端可能把设备码 flow 渲染错。
        self.assertEqual(headless_method["mode"], "auto")  # 新增代码+OpenAIConnectCatalogTest：确认 headless 方法使用自动 attempt flow；如果没有这行代码，状态轮询不会被触发。
        self.assertTrue(headless_method["experimental"])  # 新增代码+OpenAIConnectCatalogTest：确认 headless 方法带实验标记；如果没有这行代码，mock 状态机边界会变模糊。
        self.assertEqual(api_key_method["type"], "api")  # 新增代码+OpenAIConnectCatalogTest：确认 API key 方法属于 API 类型；如果没有这行代码，真实密钥保存表单会缺少类型依据。
        self.assertEqual(api_key_method["mode"], "form")  # 新增代码+OpenAIConnectCatalogTest：确认 API key 方法使用表单模式；如果没有这行代码，前端可能错误启动 OAuth attempt。
        self.assertFalse(api_key_method["experimental"])  # 新增代码+OpenAIConnectCatalogTest：确认 API key 是稳定路径；如果没有这行代码，用户会误以为真实 API key 也只是实验能力。
        self.assertEqual(api_key_method["fields"], ["secret"])  # 新增代码+OpenAIConnectCatalogTest：确认 API key 只请求通用 secret 字段；如果没有这行代码，renderer 可能暴露敏感字段名。
        for provider in payload["providers"]:  # 新增代码+ProviderSettingsContractTest：遍历每个 provider 验证稳定字段；如果没有这行代码，字段缺失可能只在 UI 运行时暴露。
            self.assertIn("connected", provider)  # 新增代码+ProviderSettingsContractTest：确认连接状态字段存在；如果没有这行代码，按钮无法判断显示连接还是断开。
            self.assertIn("source", provider)  # 新增代码+ProviderSettingsContractTest：确认来源字段存在；如果没有这行代码，UI 无法显示 env/config/custom badge。
            self.assertIn("auth_methods", provider)  # 新增代码+ProviderSettingsContractTest：确认认证方法字段存在；如果没有这行代码，连接按钮无法知道是否启用。
            self.assertIn("models", provider)  # 新增代码+ProviderSettingsContractTest：确认模型字段存在；如果没有这行代码，模型页无法分组。
            for model in provider["models"]:  # 新增代码+ModelFailureStateTest：遍历 provider 模型确认最近失败字段；如果没有这行代码，schema 4 可能只升版本但漏字段。
                self.assertIn("recent_failure", model)  # 新增代码+ModelFailureStateTest：确认模型带 recent_failure；如果没有这行代码，Composer 下拉无法标记刚失败的 OAuth 模型。
        copilot = next(item for item in payload["providers"] if item["id"] == "github-copilot")  # 新增代码+ProviderSettingsContractTest：取出 Copilot provider；如果没有这行代码，无法验证 V1 不误导登录。
        self.assertFalse(any(method["enabled"] for method in copilot["auth_methods"]))  # 新增代码+ProviderSettingsContractTest：确认 Copilot V1 无可用认证；如果没有这行代码，用户会以为 API key 登录可用。
        self.assertNotIn("unit-test-secret-value", serialized)  # 新增代码+ProviderSettingsContractTest：确认测试密钥不在响应里；如果没有这行代码，raw secret 泄露可能漏过。
        self.assertNotIn("api_key", serialized.lower())  # 新增代码+ProviderSettingsContractTest：确认响应不暴露 API key 字段名；如果没有这行代码，renderer 会长期持有敏感字段语义。
        self.assertNotIn("authorization", serialized.lower())  # 新增代码+ProviderSettingsContractTest：确认响应不暴露授权 header；如果没有这行代码，自定义 header 可能泄露。
        self.assertNotIn("bearer", serialized.lower())  # 新增代码+ProviderSettingsContractTest：确认响应不暴露 bearer token；如果没有这行代码，诊断和截图可能泄露凭据。
        self.assertNotIn("secret_ref", serialized.lower())  # 新增代码+OpenAIConnectCatalogTest：确认 catalog 不把后端 secret 引用发给 renderer；如果没有这行代码，前端可能间接泄露密钥定位信息。
    # 新增代码+ProviderSettingsContractTest：测试段结束，Provider catalog HTTP 合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_openai_provider_uses_codex_cli_source_when_codex_login_connected(self) -> None:  # 新增代码+CodexLoginCatalogTest：测试段开始，验证官方 Codex 登录成功会驱动 OpenAI provider connected；如果没有这段，设置页可能仍显示 mock 或未连接。
        from learning_agent.app.gui_codex_auth_bridge import CodexAuthStatus  # 新增代码+CodexLoginCatalogTest：导入登录状态对象；如果没有这行，fake bridge 无法返回真实结构。
        from learning_agent.app.gui_provider_settings import build_provider_settings_payload  # 新增代码+CodexLoginCatalogTest：导入 catalog 构造入口；如果没有这行，测试无法观察 provider 行。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+CodexLoginCatalogTest：创建临时 workspace；如果没有这行，测试会污染真实 provider 设置。
            with mock.patch.dict(os.environ, {"OPENHARNESS_OPENAI_AUTH_MODE": "codex_cli"}, clear=False):  # 新增代码+CodexLoginCatalogTest：临时开启官方 Codex CLI 模式；如果没有这行，catalog 仍会走默认 mock 模式。
                with mock.patch("learning_agent.app.gui_provider_settings.CodexAuthBridge") as bridge_class:  # 新增代码+CodexLoginCatalogTest：替换真实 Codex bridge；如果没有这行，测试会调用用户本机 codex 命令。
                    bridge_class.return_value.login_status.return_value = CodexAuthStatus(available=True, connected=True, message="Logged in with ChatGPT")  # 新增代码+CodexLoginCatalogTest：模拟 Codex 已登录；如果没有这行，catalog 无法进入 connected 分支。
                    fake_models = {"models": [{"slug": "gpt-5.5", "display_name": "GPT-5.5", "visibility": "list"}, {"slug": "gpt-4.1", "display_name": "GPT-4.1", "visibility": "hidden"}]}  # 新增代码+CodexOAuthModelsTest：模拟 Codex catalog 只展示 ChatGPT OAuth 可用模型；如果没有这行，测试会依赖用户本机 Codex 版本。
                    fake_completed = mock.Mock(returncode=0, stdout=json.dumps(fake_models), stderr="")  # 新增代码+CodexOAuthModelsTest：构造 subprocess.run 返回对象；如果没有这行，动态模型解析没有稳定输入。
                    with mock.patch("learning_agent.app.gui_provider_settings.subprocess.run", return_value=fake_completed):  # 新增代码+CodexOAuthModelsTest：替换 codex debug models 命令；如果没有这行，单元测试会真实启动 Codex CLI。
                        payload = build_provider_settings_payload(Path(directory))  # 新增代码+CodexLoginCatalogTest：构造 provider catalog；如果没有这行，后续没有断言对象。
        serialized = json.dumps(payload, ensure_ascii=False).lower()  # 新增代码+CodexLoginCatalogTest：序列化响应做安全扫描；如果没有这行，嵌套 token 字段可能漏过。
        openai = next(provider for provider in payload["providers"] if provider["id"] == "openai")  # 新增代码+CodexLoginCatalogTest：取出 OpenAI provider；如果没有这行，断言只能笼统看列表。
        browser_method = next(method for method in openai["auth_methods"] if method["id"] == "chatgpt-browser")  # 新增代码+CodexLoginCatalogTest：取 browser 方法；如果没有这行，无法确认帮助文案进入官方登录语义。
        self.assertIs(openai["connected"], True)  # 新增代码+CodexLoginCatalogTest：确认 Codex 已登录时 provider 显示已连接；如果没有这行，主聊天不会切真实模型。
        self.assertEqual("codex_cli", openai["source"])  # 新增代码+CodexLoginCatalogTest：确认来源是官方 Codex CLI；如果没有这行，UI 可能把它和 mock 混淆。
        self.assertEqual("Codex ChatGPT login", openai["masked_key"])  # 新增代码+CodexLoginCatalogTest：确认显示安全摘要而不是 token；如果没有这行，用户无法识别连接来源。
        self.assertEqual(["gpt-5.5"], [model["id"] for model in openai["models"]])  # 新增代码+CodexOAuthModelsTest：确认 Codex OAuth catalog 只暴露 Codex 可见模型；如果没有这行，GUI 可能再次显示 ChatGPT 账号不支持的模型。
        self.assertIn("官方 Codex CLI", browser_method["help_text"])  # 新增代码+CodexLoginCatalogTest：确认方法文案说明官方登录；如果没有这行，用户不知道 OpenHarness 不读取 token。
        self.assertNotIn("access_token", serialized)  # 新增代码+CodexLoginCatalogTest：确认 catalog 不含 access token；如果没有这行，renderer 截图可能泄露敏感字段。
        self.assertNotIn("refresh_token", serialized)  # 新增代码+CodexLoginCatalogTest：确认 catalog 不含 refresh token；如果没有这行，长期凭据语义可能进入 UI。
    # 新增代码+CodexLoginCatalogTest：测试段结束，test_openai_provider_uses_codex_cli_source_when_codex_login_connected 到此结束；如果没有边界说明，用户不易看出已登录覆盖范围。

    def test_openai_codex_cli_connection_probe_uses_login_status(self) -> None:  # 新增代码+CodexLoginProbeTest：测试段开始，验证测试连接按钮在 Codex CLI 模式下使用登录状态；如果没有这段，GUI 会再次出现“已连接但缺少密钥”的回归。
        from learning_agent.app.gui_codex_auth_bridge import CodexAuthStatus  # 新增代码+CodexLoginProbeTest：导入登录状态对象；如果没有这行，fake bridge 无法返回官方登录事实。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+CodexLoginProbeTest：创建隔离 workspace；如果没有这行，测试可能污染真实 provider 设置。
            workspace = Path(directory)  # 新增代码+CodexLoginProbeTest：保存 Path workspace；如果没有这行，后续启动 bridge 会重复转换路径。
            with mock.patch.dict(os.environ, {"OPENHARNESS_OPENAI_AUTH_MODE": "codex_cli"}, clear=False):  # 新增代码+CodexLoginProbeTest：临时开启 Codex CLI 模式；如果没有这行，测试连接仍会走默认 API key 探针。
                with mock.patch("learning_agent.app.gui_provider_settings.CodexAuthBridge") as bridge_class:  # 新增代码+CodexLoginProbeTest：替换真实 Codex bridge；如果没有这行，测试会依赖用户本机登录状态。
                    bridge_class.return_value.login_status.return_value = CodexAuthStatus(available=True, connected=True, message="Logged in with ChatGPT")  # 新增代码+CodexLoginProbeTest：模拟 Codex 已登录；如果没有这行，probe 无法进入成功分支。
                    server, thread = self._start_server(workspace)  # 新增代码+CodexLoginProbeTest：启动真实 GUI bridge 路由；如果没有这行，无法覆盖前端按钮实际调用的 HTTP endpoint。
                    try:  # 新增代码+CodexLoginProbeTest：保护 server 清理；如果没有这行，失败时端口和线程可能残留。
                        probe = self._post_json(server, "/v2/gui/provider-settings/test-connection", {"provider_id": "openai"})  # 新增代码+CodexLoginProbeTest：调用 OpenAI 测试连接路由；如果没有这行，bug 不会被复现。
                    finally:  # 新增代码+CodexLoginProbeTest：无论断言前是否异常都清理 server；如果没有这行，后台线程可能影响后续测试。
                        server.shutdown()  # 新增代码+CodexLoginProbeTest：停止 GUI bridge；如果没有这行，测试进程可能挂住。
                        server.server_close()  # 新增代码+CodexLoginProbeTest：释放 socket；如果没有这行，Windows 端口可能短时间占用。
                        thread.join(timeout=5)  # 新增代码+CodexLoginProbeTest：等待线程退出；如果没有这行，测试结束时可能仍有后台线程。
        serialized = json.dumps(probe, ensure_ascii=False).lower()  # 新增代码+CodexLoginProbeTest：序列化 probe 做泄露扫描；如果没有这行，嵌套敏感字段可能漏过。
        self.assertIs(probe["ok"], True)  # 新增代码+CodexLoginProbeTest：确认 Codex 已登录时测试连接通过；如果没有这行，GUI 可能继续显示缺少密钥。
        self.assertEqual("ok", probe["status"])  # 新增代码+CodexLoginProbeTest：确认状态码是成功；如果没有这行，前端无法显示“连接测试通过”。
        self.assertIn("Codex", probe["message"])  # 新增代码+CodexLoginProbeTest：确认成功消息说明来源；如果没有这行，用户不知道通过的是 Codex 登录状态。
        self.assertNotIn("access_token", serialized)  # 新增代码+CodexLoginProbeTest：确认 probe 不含 access token；如果没有这行，测试连接可能泄露短期凭据。
        self.assertNotIn("refresh_token", serialized)  # 新增代码+CodexLoginProbeTest：确认 probe 不含 refresh token；如果没有这行，长期凭据可能进入 UI。
        self.assertNotIn("api_key", serialized)  # 新增代码+CodexLoginProbeTest：确认 probe 不要求 API key 字段；如果没有这行，Codex 登录路径会被错误混入密钥语义。
    # 新增代码+CodexLoginProbeTest：测试段结束，test_openai_codex_cli_connection_probe_uses_login_status 到此结束；如果没有边界说明，用户不容易看出它覆盖的是测试连接按钮。

    def test_openai_direct_oauth_connection_probe_uses_token_ref(self) -> None:  # 新增代码+DirectOAuthProbeTest：测试段开始，验证 direct OAuth 模式下测试连接使用 token_ref 而不是 API key；如果没有这段，真实 OAuth 登录后仍会显示缺少密钥。
        from learning_agent.app.gui_provider_auth_attempts import save_direct_oauth_provider_connection  # 新增代码+DirectOAuthProbeTest：导入 direct OAuth 连接记录 helper；如果没有这行，测试无法写入真实 catalog 连接状态。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectOAuthProbeTest：创建隔离 workspace；如果没有这行，测试会污染真实 provider 设置。
            workspace = Path(directory)  # 新增代码+DirectOAuthProbeTest：保存 Path workspace；如果没有这行，后续 helper 和 bridge 调用会重复转换路径。
            save_direct_oauth_provider_connection(workspace, token_ref="provider_oauth:openai", auth_method_id="chatgpt-browser")  # 新增代码+DirectOAuthProbeTest：写入非敏感 token_ref 连接记录；如果没有这行，probe 无法模拟 OAuth 已完成。
            with mock.patch.dict(os.environ, {"OPENHARNESS_OPENAI_AUTH_MODE": "direct_oauth"}, clear=False):  # 新增代码+DirectOAuthProbeTest：临时开启 direct OAuth 模式；如果没有这行，测试连接会走普通 API key 探针。
                server, thread = self._start_server(workspace)  # 新增代码+DirectOAuthProbeTest：启动真实 GUI bridge 路由；如果没有这行，无法覆盖前端按钮实际调用链。
                try:  # 新增代码+DirectOAuthProbeTest：保护 server 清理；如果没有这行，失败时端口和线程可能残留。
                    probe = self._post_json(server, "/v2/gui/provider-settings/test-connection", {"provider_id": "openai"})  # 新增代码+DirectOAuthProbeTest：调用 OpenAI 测试连接路由；如果没有这行，direct OAuth probe 回归不会被发现。
                finally:  # 新增代码+DirectOAuthProbeTest：无论请求是否成功都清理 server；如果没有这行，后台线程可能影响后续测试。
                    server.shutdown()  # 新增代码+DirectOAuthProbeTest：停止 GUI bridge；如果没有这行，测试进程可能挂住。
                    server.server_close()  # 新增代码+DirectOAuthProbeTest：释放 socket；如果没有这行，Windows 端口可能短时间占用。
                    thread.join(timeout=5)  # 新增代码+DirectOAuthProbeTest：等待线程退出；如果没有这行，测试结束时可能仍有后台线程。
        serialized = json.dumps(probe, ensure_ascii=False).lower()  # 新增代码+DirectOAuthProbeTest：序列化 probe 做泄露扫描；如果没有这行，嵌套 token 字段可能漏过。
        self.assertIs(probe["ok"], True)  # 新增代码+DirectOAuthProbeTest：确认 direct OAuth token_ref 存在时测试连接通过；如果没有这行，GUI 会误报缺少密钥。
        self.assertEqual("ok", probe["status"])  # 新增代码+DirectOAuthProbeTest：确认状态码是成功；如果没有这行，前端无法显示“连接测试通过”。
        self.assertIn("OAuth", probe["message"])  # 新增代码+DirectOAuthProbeTest：确认成功消息说明来源；如果没有这行，用户不知道通过的是 OAuth token 引用。
        self.assertNotIn("access_token", serialized)  # 新增代码+DirectOAuthProbeTest：确认 probe 不含 access token；如果没有这行，短期凭据可能进入 UI。
        self.assertNotIn("refresh_token", serialized)  # 新增代码+DirectOAuthProbeTest：确认 probe 不含 refresh token；如果没有这行，长期凭据可能进入 UI。
        self.assertNotIn("provider_oauth:openai", serialized)  # 新增代码+DirectOAuthProbeTest：确认 probe 不暴露 token_ref；如果没有这行，前端可能知道内部凭据定位。
    # 新增代码+DirectOAuthProbeTest：测试段结束，test_openai_direct_oauth_connection_probe_uses_token_ref 到此结束；如果没有边界说明，用户不容易看出它覆盖的是 direct OAuth 测试连接。

    def test_openai_provider_reports_codex_cli_missing_when_official_mode_unavailable(self) -> None:  # 新增代码+CodexLoginCatalogTest：测试段开始，验证官方模式下 CLI 缺失会显示缺失来源；如果没有这段，用户会以为已进入真实连接。
        from learning_agent.app.gui_codex_auth_bridge import CodexAuthStatus  # 新增代码+CodexLoginCatalogTest：导入登录状态对象；如果没有这行，fake bridge 无法返回不可用状态。
        from learning_agent.app.gui_provider_settings import build_provider_settings_payload  # 新增代码+CodexLoginCatalogTest：导入 catalog 构造入口；如果没有这行，测试无法观察 provider 行。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+CodexLoginCatalogTest：创建临时 workspace；如果没有这行，测试会污染真实 provider 设置。
            with mock.patch.dict(os.environ, {"OPENHARNESS_OPENAI_AUTH_MODE": "codex_cli"}, clear=False):  # 新增代码+CodexLoginCatalogTest：临时开启官方 Codex CLI 模式；如果没有这行，catalog 不会检查 CLI 状态。
                with mock.patch("learning_agent.app.gui_provider_settings.CodexAuthBridge") as bridge_class:  # 新增代码+CodexLoginCatalogTest：替换真实 Codex bridge；如果没有这行，测试会依赖本机环境。
                    bridge_class.return_value.login_status.return_value = CodexAuthStatus(available=False, connected=False, message="codex_cli_not_found")  # 新增代码+CodexLoginCatalogTest：模拟 Codex CLI 缺失；如果没有这行，catalog 无法进入 missing 分支。
                    payload = build_provider_settings_payload(Path(directory))  # 新增代码+CodexLoginCatalogTest：构造 provider catalog；如果没有这行，后续没有断言对象。
        openai = next(provider for provider in payload["providers"] if provider["id"] == "openai")  # 新增代码+CodexLoginCatalogTest：取出 OpenAI provider；如果没有这行，无法断言 source。
        self.assertIs(openai["connected"], False)  # 新增代码+CodexLoginCatalogTest：确认 CLI 缺失不能显示 connected；如果没有这行，真实模型会误启动。
        self.assertEqual("codex_cli_missing", openai["source"])  # 新增代码+CodexLoginCatalogTest：确认来源明确提示 CLI 缺失；如果没有这行，UI 无法给用户正确修复方向。
        self.assertEqual("", openai["masked_key"])  # 新增代码+CodexLoginCatalogTest：确认缺失状态不显示假摘要；如果没有这行，用户会误以为登录存在。
    # 新增代码+CodexLoginCatalogTest：测试段结束，test_openai_provider_reports_codex_cli_missing_when_official_mode_unavailable 到此结束；如果没有边界说明，用户不易看出 CLI 缺失覆盖范围。

    def test_openai_codex_cli_disconnect_persists_local_disabled_override(self) -> None:  # 新增代码+ProviderDisconnectTest：测试段开始，验证 Codex CLI 已登录时断开会在 OpenHarness 本地保持未连接；如果没有这段，断开后 catalog 会立刻被外部登录态拉回已连接。
        from learning_agent.app.gui_codex_auth_bridge import CodexAuthStatus  # 新增代码+ProviderDisconnectTest：导入 Codex 登录状态对象；如果没有这行，测试无法模拟已登录的真实 CLI 状态。
        from learning_agent.app.gui_provider_settings import build_provider_settings_payload, disconnect_provider, load_provider_settings  # 新增代码+ProviderDisconnectTest：导入 catalog、断开和配置读取入口；如果没有这行，测试无法覆盖完整断开链路。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+ProviderDisconnectTest：创建隔离 workspace；如果没有这行，测试会污染真实 provider 设置。
            workspace = Path(directory)  # 新增代码+ProviderDisconnectTest：把临时目录转成 Path；如果没有这行，后续路径调用会重复转换。
            with mock.patch.dict(os.environ, {"OPENHARNESS_OPENAI_AUTH_MODE": "codex_cli"}, clear=False):  # 新增代码+ProviderDisconnectTest：开启官方 Codex CLI 模式；如果没有这行，catalog 不会进入外部登录态分支。
                with mock.patch("learning_agent.app.gui_provider_settings.CodexAuthBridge") as bridge_class:  # 新增代码+ProviderDisconnectTest：替换真实 Codex CLI 调用；如果没有这行，测试会依赖本机登录状态。
                    bridge_class.return_value.login_status.return_value = CodexAuthStatus(available=True, connected=True, message="logged_in")  # 新增代码+ProviderDisconnectTest：模拟 Codex CLI 已登录；如果没有这行，无法复现用户看到的已连接状态。
                    connected_payload = build_provider_settings_payload(workspace)  # 新增代码+ProviderDisconnectTest：先读取连接前 catalog；如果没有这行，测试无法证明断开前确实是已连接。
                    disconnected_payload = disconnect_provider(workspace, "openai")  # 新增代码+ProviderDisconnectTest：执行用户点击断开的后端动作；如果没有这行，测试没有覆盖 mutation。
                    refreshed_payload = build_provider_settings_payload(workspace)  # 新增代码+ProviderDisconnectTest：重新读取 catalog；如果没有这行，测试无法发现“刷新后又连上”的回归。
                    persisted_settings = load_provider_settings(workspace)  # 新增代码+ProviderDisconnectTest：读取持久配置；如果没有这行，无法确认本地 disabled 覆盖是否落盘。

        openai_connected = next(provider for provider in connected_payload["providers"] if provider["id"] == "openai")  # 新增代码+ProviderDisconnectTest：取出断开前 OpenAI 行；如果没有这行，断言无法定位目标 provider。
        openai_disconnected = next(provider for provider in disconnected_payload["providers"] if provider["id"] == "openai")  # 新增代码+ProviderDisconnectTest：取出断开响应里的 OpenAI 行；如果没有这行，无法验证 mutation 返回状态。
        openai_refreshed = next(provider for provider in refreshed_payload["providers"] if provider["id"] == "openai")  # 新增代码+ProviderDisconnectTest：取出刷新后的 OpenAI 行；如果没有这行，无法验证断开状态是否持久。
        self.assertIs(openai_connected["connected"], True)  # 新增代码+ProviderDisconnectTest：确认测试起点是已连接；如果没有这行，测试可能在错误前提下通过。
        self.assertEqual("codex_cli", openai_connected["source"])  # 新增代码+ProviderDisconnectTest：确认连接来自 Codex CLI；如果没有这行，测试可能误覆盖 API key 路径。
        self.assertIs(openai_disconnected["connected"], False)  # 新增代码+ProviderDisconnectTest：确认断开响应立即显示未连接；如果没有这行，用户点击后界面不会变化。
        self.assertEqual("none", openai_disconnected["source"])  # 新增代码+ProviderDisconnectTest：确认断开后来源清空；如果没有这行，UI 可能仍误显示 Codex CLI 来源。
        self.assertIs(openai_refreshed["connected"], False)  # 新增代码+ProviderDisconnectTest：确认重新刷新仍保持未连接；如果没有这行，用户会看到断开后又自动连回。
        self.assertEqual("disabled", persisted_settings["auth"]["openai"]["type"])  # 新增代码+ProviderDisconnectTest：确认本地 disabled 覆盖已落盘；如果没有这行，重启后断开状态会丢失。
    # 新增代码+ProviderDisconnectTest：测试段结束，test_openai_codex_cli_disconnect_persists_local_disabled_override 到此结束；如果没有边界说明，用户不易看出它锁住的是 Codex CLI 断开语义。

    def test_openai_direct_oauth_disconnect_deletes_token_store_record(self) -> None:  # 新增代码+ProviderDisconnectTest：测试段开始，验证 direct OAuth 断开会删除 token store；如果没有这段，用户断开后 raw token 文件可能继续留在本机。
        from learning_agent.app.gui_provider_oauth_token_store import make_fake_token_store  # 新增代码+ProviderDisconnectTest：导入 fake token store；如果没有这行，测试会依赖真实 Windows DPAPI。
        from learning_agent.app.gui_provider_settings import disconnect_provider, save_provider_settings  # 新增代码+ProviderDisconnectTest：导入断开和设置保存入口；如果没有这行，测试无法构造 direct OAuth 已连接状态。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+ProviderDisconnectTest：创建隔离 workspace；如果没有这行，测试会污染真实 provider 设置。
            workspace = Path(directory)  # 新增代码+ProviderDisconnectTest：把临时目录转成 Path；如果没有这行，后续路径拼接不清晰。
            token_store = make_fake_token_store(workspace / "oauth_tokens")  # 新增代码+ProviderDisconnectTest：创建隔离 fake token store；如果没有这行，测试无法检查 token 文件删除。
            token_store.set_tokens("openai", {"access_token": "unit-access", "refresh_token": "unit-refresh", "account_id": "acct", "expires_at": 1})  # 新增代码+ProviderDisconnectTest：写入 fake OAuth token；如果没有这行，断开删除没有目标可验证。
            save_provider_settings(workspace, {"auth": {"openai": {"type": "oauth_direct", "token_ref": token_store.token_ref_for("openai"), "updated_at": 1}}, "custom_providers": {}, "model_visibility": {}})  # 新增代码+ProviderDisconnectTest：保存 direct OAuth 连接记录；如果没有这行，disconnect_provider 不知道 OpenAI 是 OAuth 连接。
            with mock.patch("learning_agent.app.gui_provider_settings.default_oauth_token_store", return_value=token_store, create=True):  # 新增代码+ProviderDisconnectTest：让断开逻辑使用 fake token store；如果没有这行，测试会访问真实用户 token 目录。
                disconnect_provider(workspace, "openai")  # 新增代码+ProviderDisconnectTest：执行断开动作；如果没有这行，token store 不会触发清理。
            self.assertFalse(token_store.path_for("openai").exists())  # 新增代码+ProviderDisconnectTest：确认 token 文件已删除；如果没有这行，断开可能只清 catalog 不清真实凭据。
    # 新增代码+ProviderDisconnectTest：测试段结束，test_openai_direct_oauth_disconnect_deletes_token_store_record 到此结束；如果没有边界说明，用户不易看出它覆盖的是 direct OAuth 凭据清理。

    def test_provider_settings_mutations_persist_redacted_state(self) -> None:  # 新增代码+ProviderSettingsContractTest：测试段开始，验证 auth/disconnect/custom/model visibility 写入合同；如果没有这段测试，设置页按钮可能只有前端假状态。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+ProviderSettingsContractTest：创建临时 workspace；如果没有这行代码，mutation 会污染真实项目。
            workspace = Path(directory)  # 新增代码+ProviderSettingsContractTest：保存 Path workspace；如果没有这行代码，后续路径断言会重复转换。
            server, thread = self._start_server(workspace)  # 新增代码+ProviderSettingsContractTest：启动真实 GUI bridge；如果没有这行代码，mutation 路由没有目标服务。
            try:  # 新增代码+ProviderSettingsContractTest：确保 server 最终关闭；如果没有这行代码，失败时端口会泄漏。
                auth_payload = self._post_json(server, "/v2/gui/provider-settings/auth", {"provider_id": "openai", "auth_method_id": "api-key", "fields": {"secret": "unit-test-secret-value"}})  # 修改代码+OpenAIConnectApiKeyTest：用新方法 id 和通用 secret 字段保存 OpenAI 测试密钥；如果没有这行代码，无法验证 API key 真实路径。
                hidden_payload = self._post_json(server, "/v2/gui/provider-settings/model-visibility", {"provider_id": "openai", "model_id": "gpt-4.1", "visible": False})  # 新增代码+ProviderSettingsContractTest：隐藏 OpenAI 模型；如果没有这行代码，无法验证模型可见性持久化。
                custom_payload = self._post_json(server, "/v2/gui/provider-settings/custom-provider", {"provider_id": "local-openai-compatible", "display_name": "Local OpenAI Compatible", "base_url": "http://127.0.0.1:11434/v1", "auth_method_id": "api_key", "fields": {"api_key": "unit-test-secret-value"}, "headers": [{"key": "X-Test-Header", "value": "unit-test-header-value"}], "models": [{"id": "local-model", "display_name": "Local Model", "visible": True}]})  # 新增代码+ProviderSettingsContractTest：保存自定义 OpenAI-compatible provider；如果没有这行代码，自定义 provider 合同不会被覆盖。
                reserved_error = self._post_json_error(server, "/v2/gui/provider-settings/custom-provider", {"provider_id": "custom", "display_name": "Bad", "base_url": "http://127.0.0.1:1/v1", "models": [{"id": "x", "display_name": "X"}]})  # 新增代码+ProviderSettingsContractTest：提交保留 provider id；如果没有这行代码，custom CTA 可能被误保存成 provider。
                bad_url_error = self._post_json_error(server, "/v2/gui/provider-settings/custom-provider", {"provider_id": "bad-local", "display_name": "Bad URL", "base_url": "ftp://127.0.0.1/v1", "models": [{"id": "x", "display_name": "X"}]})  # 新增代码+ProviderSettingsContractTest：提交非法 base URL；如果没有这行代码，后续连接探针可能收到危险协议。
                disconnect_payload = self._post_json(server, "/v2/gui/provider-settings/disconnect", {"provider_id": "openai"})  # 新增代码+ProviderSettingsContractTest：断开 OpenAI；如果没有这行代码，disconnect 合同不会被验证。
            finally:  # 新增代码+ProviderSettingsContractTest：清理 server；如果没有这行代码，后台线程和 socket 可能残留。
                server.shutdown()  # 新增代码+ProviderSettingsContractTest：停止 serve_forever；如果没有这行代码，测试进程可能挂住。
                server.server_close()  # 新增代码+ProviderSettingsContractTest：释放 socket；如果没有这行代码，Windows 端口可能短时间占用。
                thread.join(timeout=5)  # 新增代码+ProviderSettingsContractTest：等待后台线程退出；如果没有这行代码，测试结束时可能仍有线程。

            settings_text = (workspace / "memory" / "gui_provider_settings" / "providers.json").read_text(encoding="utf-8")  # 新增代码+ProviderSettingsContractTest：读取主 provider 设置文件；如果没有这行代码，无法确认 raw key 没有落入主配置。
            secrets_text = (workspace / "memory" / "gui_provider_settings" / "secrets.dev.json").read_text(encoding="utf-8")  # 新增代码+ProviderSettingsContractTest：读取开发密钥文件；如果没有这行代码，无法确认测试 secret 只存在于 secret store。
            restarted_server, restarted_thread = self._start_server(workspace)  # 新增代码+ProviderSettingsContractTest：用同一 workspace 重启 server；如果没有这行代码，无法验证可见性跨进程持久化。
            try:  # 新增代码+ProviderSettingsContractTest：确保重启 server 关闭；如果没有这行代码，失败时端口会泄漏。
                restarted_catalog = self._get_json(restarted_server, "/v2/gui/provider-settings/providers")  # 新增代码+ProviderSettingsContractTest：重启后读取 catalog；如果没有这行代码，无法验证配置重新加载。
            finally:  # 新增代码+ProviderSettingsContractTest：清理重启 server；如果没有这行代码，后台线程可能残留。
                restarted_server.shutdown()  # 新增代码+ProviderSettingsContractTest：停止重启 server；如果没有这行代码，测试进程可能挂住。
                restarted_server.server_close()  # 新增代码+ProviderSettingsContractTest：释放重启 server socket；如果没有这行代码，Windows 端口可能短时间占用。
                restarted_thread.join(timeout=5)  # 新增代码+ProviderSettingsContractTest：等待重启线程退出；如果没有这行代码，测试结束时可能仍有线程。

        auth_serialized = json.dumps(auth_payload, ensure_ascii=False)  # 新增代码+ProviderSettingsContractTest：序列化 auth 响应；如果没有这行代码，嵌套字段泄露可能漏过。
        custom_ids = {provider["id"] for provider in custom_payload["providers"]}  # 新增代码+ProviderSettingsContractTest：收集自定义保存后的 provider id；如果没有这行代码，无法验证 provider 是否进入 catalog。
        openai_after_disconnect = next(provider for provider in disconnect_payload["providers"] if provider["id"] == "openai")  # 新增代码+ProviderSettingsContractTest：读取断开后的 OpenAI 行；如果没有这行代码，无法验证 connected false。
        openai_after_restart = next(provider for provider in restarted_catalog["providers"] if provider["id"] == "openai")  # 新增代码+ProviderSettingsContractTest：读取重启后的 OpenAI 行；如果没有这行代码，无法验证模型可见性持久化。
        gpt_after_restart = next(model for model in openai_after_restart["models"] if model["id"] == "gpt-4.1")  # 新增代码+ProviderSettingsContractTest：读取重启后的 GPT 模型；如果没有这行代码，无法断言 visible false。
        self.assertIn("masked_key", auth_serialized)  # 新增代码+ProviderSettingsContractTest：确认 auth 响应包含脱敏摘要；如果没有这行代码，UI 无法显示已连接状态。
        self.assertNotIn("unit-test-secret-value", auth_serialized)  # 新增代码+ProviderSettingsContractTest：确认 auth 响应不含 raw key；如果没有这行代码，renderer 可能泄露密钥。
        self.assertIn("secret_ref", settings_text)  # 新增代码+ProviderSettingsContractTest：确认主配置只保存引用；如果没有这行代码，后续连接无法找到 secret。
        self.assertNotIn("unit-test-secret-value", settings_text)  # 新增代码+ProviderSettingsContractTest：确认主配置不保存 raw key；如果没有这行代码，真实 API key 会明文落盘。
        self.assertIn("unit-test-secret-value", secrets_text)  # 新增代码+ProviderSettingsContractTest：确认开发 secret store 是唯一 raw key 存放点；如果没有这行代码，secret store 可能没有保存。
        self.assertIn("local-openai-compatible", custom_ids)  # 新增代码+ProviderSettingsContractTest：确认自定义 provider 进入 catalog；如果没有这行代码，自定义保存可能无效。
        self.assertEqual(reserved_error["code"], "reserved_provider_id")  # 新增代码+ProviderSettingsContractTest：确认保留 id 被拒绝；如果没有这行代码，custom CTA 语义会损坏。
        self.assertEqual(bad_url_error["code"], "invalid_base_url")  # 新增代码+ProviderSettingsContractTest：确认非法 URL 被拒绝；如果没有这行代码，危险协议可能进入配置。
        self.assertIs(openai_after_disconnect["connected"], False)  # 新增代码+ProviderSettingsContractTest：确认断开后 connected 为 false；如果没有这行代码，断开按钮可能无效。
        self.assertIs(hidden_payload["ok"], True)  # 新增代码+ProviderSettingsContractTest：确认模型可见性 mutation 成功；如果没有这行代码，失败响应可能误过。
        self.assertIs(gpt_after_restart["visible"], False)  # 新增代码+ProviderSettingsContractTest：确认模型隐藏跨 server 持久；如果没有这行代码，重启后可见性会丢失。
    # 新增代码+ProviderSettingsContractTest：测试段结束，mutation 持久化合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_provider_connection_probe_returns_safe_statuses(self) -> None:  # 新增代码+ProviderSettingsContractTest：测试段开始，验证连接探针状态合同；如果没有这段测试，保存 key 会被误认为模型可用。
        fake_models_server, fake_models_thread = self._start_fake_models_server()  # 新增代码+ProviderSettingsContractTest：启动本地 /models 服务；如果没有这行代码，ok 探针没有真实 HTTP 目标。
        fake_host, fake_port = fake_models_server.server_address  # 新增代码+ProviderSettingsContractTest：读取假服务端口；如果没有这行代码，custom provider 无法指向本地服务。
        try:  # 新增代码+ProviderSettingsContractTest：确保假服务最终关闭；如果没有这行代码，失败时端口会泄漏。
            with tempfile.TemporaryDirectory() as directory:  # 新增代码+ProviderSettingsContractTest：创建临时 workspace；如果没有这行代码，探针配置会污染真实项目。
                workspace = Path(directory)  # 新增代码+ProviderSettingsContractTest：保存 Path workspace；如果没有这行代码，后续路径会重复转换。
                server, thread = self._start_server(workspace)  # 新增代码+ProviderSettingsContractTest：启动 GUI bridge；如果没有这行代码，test-connection 路由没有目标服务。
                try:  # 新增代码+ProviderSettingsContractTest：确保 GUI bridge 关闭；如果没有这行代码，失败时端口会泄漏。
                    self._post_json(server, "/v2/gui/provider-settings/custom-provider", {"provider_id": "local-probe", "display_name": "Local Probe", "base_url": f"http://{fake_host}:{fake_port}/v1", "auth_method_id": "api_key", "fields": {"api_key": "unit-test-secret-value"}, "models": [{"id": "local-model", "display_name": "Local Model"}]})  # 新增代码+ProviderSettingsContractTest：保存指向假服务的自定义 provider；如果没有这行代码，ok 探针没有配置。
                    self._post_json(server, "/v2/gui/provider-settings/custom-provider", {"provider_id": "bad-network", "display_name": "Bad Network", "base_url": "http://127.0.0.1:1/v1", "auth_method_id": "api_key", "fields": {"api_key": "unit-test-secret-value"}, "models": [{"id": "bad-model", "display_name": "Bad Model"}]})  # 新增代码+ProviderSettingsContractTest：保存无法连接的自定义 provider；如果没有这行代码，network_failed 状态无法验证。
                    ok_probe = self._post_json(server, "/v2/gui/provider-settings/test-connection", {"provider_id": "local-probe"})  # 新增代码+ProviderSettingsContractTest：测试本地 fake /models；如果没有这行代码，ok 状态不会被覆盖。
                    copilot_probe = self._post_json(server, "/v2/gui/provider-settings/test-connection", {"provider_id": "github-copilot"})  # 新增代码+ProviderSettingsContractTest：测试 Copilot unsupported；如果没有这行代码，未支持 provider 可能误发请求。
                    missing_secret_probe = self._post_json(server, "/v2/gui/provider-settings/test-connection", {"provider_id": "openrouter"})  # 新增代码+ProviderSettingsContractTest：测试缺密钥状态；如果没有这行代码，未连接 provider 可能误判网络失败。
                    network_probe = self._post_json(server, "/v2/gui/provider-settings/test-connection", {"provider_id": "bad-network"})  # 新增代码+ProviderSettingsContractTest：测试网络失败状态；如果没有这行代码，连接失败文案无法验证。
                finally:  # 新增代码+ProviderSettingsContractTest：清理 GUI bridge；如果没有这行代码，后台线程和 socket 可能残留。
                    server.shutdown()  # 新增代码+ProviderSettingsContractTest：停止 GUI bridge；如果没有这行代码，测试进程可能挂住。
                    server.server_close()  # 新增代码+ProviderSettingsContractTest：释放 GUI bridge socket；如果没有这行代码，Windows 端口可能短时间占用。
                    thread.join(timeout=5)  # 新增代码+ProviderSettingsContractTest：等待 GUI bridge 线程退出；如果没有这行代码，测试结束时可能仍有线程。
        finally:  # 新增代码+ProviderSettingsContractTest：清理 fake models server；如果没有这行代码，假服务可能残留。
            fake_models_server.shutdown()  # 新增代码+ProviderSettingsContractTest：停止 fake models server；如果没有这行代码，后台线程会继续监听。
            fake_models_server.server_close()  # 新增代码+ProviderSettingsContractTest：释放 fake models socket；如果没有这行代码，Windows 端口可能短时间占用。
            fake_models_thread.join(timeout=5)  # 新增代码+ProviderSettingsContractTest：等待 fake models 线程退出；如果没有这行代码，测试结束时可能仍有线程。

        serialized = json.dumps([ok_probe, copilot_probe, missing_secret_probe, network_probe], ensure_ascii=False)  # 新增代码+ProviderSettingsContractTest：序列化探针结果做泄露扫描；如果没有这行代码，嵌套泄露可能漏过。
        self.assertEqual(ok_probe["status"], "ok")  # 新增代码+ProviderSettingsContractTest：确认本地 /models 探针通过；如果没有这行代码，保存 key 和可用模型无法区分。
        self.assertEqual(ok_probe["models_count"], 1)  # 新增代码+ProviderSettingsContractTest：确认模型数量来自响应；如果没有这行代码，探针可能只判断 HTTP 200。
        self.assertEqual(copilot_probe["status"], "unsupported")  # 新增代码+ProviderSettingsContractTest：确认 Copilot V1 不执行探针；如果没有这行代码，未支持 provider 可能误导用户。
        self.assertEqual(missing_secret_probe["status"], "missing_secret")  # 新增代码+ProviderSettingsContractTest：确认未连接 provider 返回缺密钥；如果没有这行代码，用户无法知道要先连接。
        self.assertEqual(network_probe["status"], "network_failed")  # 新增代码+ProviderSettingsContractTest：确认无法连接时返回网络失败；如果没有这行代码，错误文案会不稳定。
        self.assertNotIn("unit-test-secret-value", serialized)  # 新增代码+ProviderSettingsContractTest：确认探针结果不包含 raw key；如果没有这行代码，测试连接可能泄露凭据。
        self.assertNotIn("authorization", serialized.lower())  # 新增代码+ProviderSettingsContractTest：确认探针结果不包含授权 header；如果没有这行代码，自定义 header 可能进入 UI。
    # 新增代码+ProviderSettingsContractTest：测试段结束，连接探针合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


if __name__ == "__main__":  # 新增代码+ProviderSettingsContractTest：允许直接运行本测试文件；如果没有这行代码，手动调试需要记住 unittest 命令。
    unittest.main()  # 新增代码+ProviderSettingsContractTest：启动 unittest runner；如果没有这行代码，直接 python 文件不会执行测试。
