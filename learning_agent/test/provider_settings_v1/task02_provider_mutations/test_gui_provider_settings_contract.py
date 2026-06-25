import json  # 新增代码+ProviderSettingsContractTest：解析 GUI bridge JSON 响应；如果没有这行代码，HTTP 合同只能比较原始字节。
import tempfile  # 新增代码+ProviderSettingsContractTest：创建隔离临时工作区；如果没有这行代码，测试会污染真实项目目录。
import threading  # 新增代码+ProviderSettingsContractTest：后台运行 HTTP server；如果没有这行代码，测试请求会被 serve_forever 阻塞。
import unittest  # 新增代码+ProviderSettingsContractTest：使用项目现有 unittest 风格；如果没有这行代码，测试类不会被标准 runner 发现。
import urllib.error  # 新增代码+ProviderSettingsContractTest：读取结构化 HTTP 错误响应；如果没有这行代码，非法 provider 测试无法断言错误码。
import urllib.request  # 新增代码+ProviderSettingsContractTest：使用标准库请求本地 bridge；如果没有这行代码，测试需要额外依赖。
from pathlib import Path  # 新增代码+ProviderSettingsContractTest：用 Path 管理临时 workspace；如果没有这行代码，Windows 路径拼接容易出错。


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
        self.assertEqual(payload["schema_version"], 2)  # 新增代码+ProviderSettingsContractTest：确认 V2 schema；如果没有这行代码，前端无法稳定解析。
        self.assertTrue({"github-copilot", "openai", "google", "openrouter", "vercel"}.issubset(provider_ids))  # 新增代码+ProviderSettingsContractTest：确认五个内置 provider 都存在；如果没有这行代码，设置页会缺常用入口。
        self.assertNotIn("custom", provider_ids)  # 新增代码+ProviderSettingsContractTest：确认 custom 不是真实 provider id；如果没有这行代码，多自定义 provider 语义会混乱。
        self.assertEqual(payload["custom_provider_cta"]["id"], "custom-provider-cta")  # 新增代码+ProviderSettingsContractTest：确认自定义入口是虚拟 CTA；如果没有这行代码，前端可能把 CTA 当成 provider 保存。
        for provider in payload["providers"]:  # 新增代码+ProviderSettingsContractTest：遍历每个 provider 验证稳定字段；如果没有这行代码，字段缺失可能只在 UI 运行时暴露。
            self.assertIn("connected", provider)  # 新增代码+ProviderSettingsContractTest：确认连接状态字段存在；如果没有这行代码，按钮无法判断显示连接还是断开。
            self.assertIn("source", provider)  # 新增代码+ProviderSettingsContractTest：确认来源字段存在；如果没有这行代码，UI 无法显示 env/config/custom badge。
            self.assertIn("auth_methods", provider)  # 新增代码+ProviderSettingsContractTest：确认认证方法字段存在；如果没有这行代码，连接按钮无法知道是否启用。
            self.assertIn("models", provider)  # 新增代码+ProviderSettingsContractTest：确认模型字段存在；如果没有这行代码，模型页无法分组。
        copilot = next(item for item in payload["providers"] if item["id"] == "github-copilot")  # 新增代码+ProviderSettingsContractTest：取出 Copilot provider；如果没有这行代码，无法验证 V1 不误导登录。
        self.assertFalse(any(method["enabled"] for method in copilot["auth_methods"]))  # 新增代码+ProviderSettingsContractTest：确认 Copilot V1 无可用认证；如果没有这行代码，用户会以为 API key 登录可用。
        self.assertNotIn("unit-test-secret-value", serialized)  # 新增代码+ProviderSettingsContractTest：确认测试密钥不在响应里；如果没有这行代码，raw secret 泄露可能漏过。
        self.assertNotIn("api_key", serialized.lower())  # 新增代码+ProviderSettingsContractTest：确认响应不暴露 API key 字段名；如果没有这行代码，renderer 会长期持有敏感字段语义。
        self.assertNotIn("authorization", serialized.lower())  # 新增代码+ProviderSettingsContractTest：确认响应不暴露授权 header；如果没有这行代码，自定义 header 可能泄露。
        self.assertNotIn("bearer", serialized.lower())  # 新增代码+ProviderSettingsContractTest：确认响应不暴露 bearer token；如果没有这行代码，诊断和截图可能泄露凭据。
    # 新增代码+ProviderSettingsContractTest：测试段结束，Provider catalog HTTP 合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_provider_settings_mutations_persist_redacted_state(self) -> None:  # 新增代码+ProviderSettingsContractTest：测试段开始，验证 auth/disconnect/custom/model visibility 写入合同；如果没有这段测试，设置页按钮可能只有前端假状态。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+ProviderSettingsContractTest：创建临时 workspace；如果没有这行代码，mutation 会污染真实项目。
            workspace = Path(directory)  # 新增代码+ProviderSettingsContractTest：保存 Path workspace；如果没有这行代码，后续路径断言会重复转换。
            server, thread = self._start_server(workspace)  # 新增代码+ProviderSettingsContractTest：启动真实 GUI bridge；如果没有这行代码，mutation 路由没有目标服务。
            try:  # 新增代码+ProviderSettingsContractTest：确保 server 最终关闭；如果没有这行代码，失败时端口会泄漏。
                auth_payload = self._post_json(server, "/v2/gui/provider-settings/auth", {"provider_id": "openai", "auth_method_id": "api_key", "fields": {"api_key": "unit-test-secret-value"}})  # 新增代码+ProviderSettingsContractTest：保存 OpenAI 测试密钥；如果没有这行代码，无法验证 auth mutation。
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


if __name__ == "__main__":  # 新增代码+ProviderSettingsContractTest：允许直接运行本测试文件；如果没有这行代码，手动调试需要记住 unittest 命令。
    unittest.main()  # 新增代码+ProviderSettingsContractTest：启动 unittest runner；如果没有这行代码，直接 python 文件不会执行测试。
