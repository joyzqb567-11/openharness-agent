import json  # 新增代码+DirectOAuthModelFactoryTest：构造 fake Codex responses 的结构化输出文本；如果没有这行代码，模型 chat 测试无法返回可解析 JSON。
import os  # 新增代码+DirectOAuthModelFactoryTest：临时设置模型和 OAuth 模式环境变量；如果没有这行代码，测试无法覆盖 direct_oauth 工厂选择。
import tempfile  # 新增代码+DirectOAuthModelFactoryTest：创建隔离 token store 目录；如果没有这行代码，测试会污染用户真实 OAuth token。
import unittest  # 新增代码+DirectOAuthModelFactoryTest：使用标准库测试框架；如果没有这行代码，pytest 无法收集这个测试类。
from pathlib import Path  # 新增代码+DirectOAuthModelFactoryTest：用 Path 管理临时目录；如果没有这行代码，Windows 路径拼接更容易出错。
from unittest import mock  # 新增代码+DirectOAuthModelFactoryTest：替换 bridge/provider payload 和环境变量；如果没有这行代码，测试会访问真实设置和登录态。


class GuiDirectOAuthModelFactoryTests(unittest.TestCase):  # 新增代码+DirectOAuthModelFactoryTest：测试类段开始，锁定 direct OAuth 到真实模型工厂的合同；如果没有这个类，GUI 登录成功后仍可能 fake 或走错模型。
    def test_token_store_adapter_loads_and_saves_codex_oauth_tokens(self) -> None:  # 新增代码+DirectOAuthModelFactoryTest：测试段开始，验证 GUI token store 能适配 CodexOAuthChatModel 协议；如果没有这段，refresh 保存可能写不到 OS 加密 store。
        from learning_agent.app.gui_agent_adapter import GuiDirectOAuthCodexTokenStoreAdapter  # 新增代码+DirectOAuthModelFactoryTest：导入待实现 token store 适配器；如果没有这行代码，测试没有被测目标。
        from learning_agent.app.gui_provider_oauth_token_store import make_fake_token_store  # 新增代码+DirectOAuthModelFactoryTest：导入 fake token store；如果没有这行代码，测试会依赖真实 Windows DPAPI。
        from learning_agent.models.adapters import CodexOAuthTokens  # 新增代码+DirectOAuthModelFactoryTest：导入 CodexOAuthChatModel 期望的 token 数据对象；如果没有这行代码，无法验证协议形状。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectOAuthModelFactoryTest：创建隔离目录；如果没有这行代码，token 文件会污染真实用户目录。
            fake_store = make_fake_token_store(Path(directory))  # 新增代码+DirectOAuthModelFactoryTest：创建明文 fake store；如果没有这行代码，测试无法直接读回 token 字段。
            adapter = GuiDirectOAuthCodexTokenStoreAdapter(token_store=fake_store)  # 新增代码+DirectOAuthModelFactoryTest：用 fake store 创建协议适配器；如果没有这行代码，CodexOAuthChatModel 不能复用 GUI token store。
            self.assertIsNone(adapter.load())  # 新增代码+DirectOAuthModelFactoryTest：确认空 store 返回 None；如果没有这行代码，未登录场景可能被误判为已连接。
            fake_store.set_tokens("openai", {"access_token": "access-a", "refresh_token": "refresh-a", "expires_at": 123456, "account_id": "acct-a", "id_token": "id-a"})  # 新增代码+DirectOAuthModelFactoryTest：写入一组 fake token；如果没有这行代码，load 路径没有样本。
            loaded = adapter.load()  # 新增代码+DirectOAuthModelFactoryTest：通过 Codex 协议读取 token；如果没有这行代码，无法验证字段转换。
            self.assertEqual("access-a", loaded.access_token if loaded else "")  # 新增代码+DirectOAuthModelFactoryTest：确认 access_token 被正确读取；如果没有这行代码，请求头会缺鉴权 token。
            self.assertEqual("refresh-a", loaded.refresh_token if loaded else "")  # 新增代码+DirectOAuthModelFactoryTest：确认 refresh_token 被正确读取；如果没有这行代码，过期后无法刷新。
            self.assertEqual(123456, loaded.expires_at if loaded else 0)  # 新增代码+DirectOAuthModelFactoryTest：确认 expires_at 被正确读取；如果没有这行代码，刷新时机可能错误。
            self.assertEqual("acct-a", loaded.account_id if loaded else "")  # 新增代码+DirectOAuthModelFactoryTest：确认 account_id 被正确读取；如果没有这行代码，ChatGPT-Account-Id 头可能缺失。
            adapter.save(CodexOAuthTokens(access_token="access-b", refresh_token="refresh-b", expires_at=654321, account_id="acct-b", id_token="id-b"))  # 新增代码+DirectOAuthModelFactoryTest：通过 Codex 协议保存刷新后的 token；如果没有这行代码，refresh 后写回路径无法验证。
            raw = fake_store.get_tokens("openai") or {}  # 新增代码+DirectOAuthModelFactoryTest：读取 fake store 原始记录；如果没有这行代码，无法确认 save 写回 GUI token store。
        self.assertEqual("access-b", raw.get("access_token"))  # 新增代码+DirectOAuthModelFactoryTest：确认新 access_token 已保存；如果没有这行代码，刷新结果可能只停留在内存。
        self.assertEqual("refresh-b", raw.get("refresh_token"))  # 新增代码+DirectOAuthModelFactoryTest：确认新 refresh_token 已保存；如果没有这行代码，下一次启动仍会用旧 token。
        self.assertEqual("acct-b", raw.get("account_id"))  # 新增代码+DirectOAuthModelFactoryTest：确认 account_id 已保存；如果没有这行代码，后续请求可能缺账号头。
    # 新增代码+DirectOAuthModelFactoryTest：测试段结束，test_token_store_adapter_loads_and_saves_codex_oauth_tokens 到此结束；如果没有边界说明，用户不容易看出覆盖的是 token 协议适配。

    def test_default_real_model_factory_uses_codex_oauth_model_for_direct_oauth_mode(self) -> None:  # 新增代码+DirectOAuthModelFactoryTest：测试段开始，验证 direct_oauth 模式创建 CodexOAuthChatModel；如果没有这段，GUI direct 登录后仍可能调用 Codex CLI。
        from learning_agent.app.gui_agent_adapter import GuiDirectOAuthCodexTokenStoreAdapter, _default_real_model_factory  # 新增代码+DirectOAuthModelFactoryTest：导入默认真实模型工厂和 token 适配器；如果没有这行代码，测试无法锁住默认选择。
        from learning_agent.models.adapters import CodexOAuthChatModel  # 新增代码+DirectOAuthModelFactoryTest：导入 Codex OAuth 模型类型；如果没有这行代码，无法确认工厂产物。

        env = {"OPENHARNESS_OPENAI_AUTH_MODE": "direct_oauth", "OPENHARNESS_OPENAI_EXPERIMENTAL": "1", "OPENHARNESS_PROVIDER_SECRET_STORE": "os_encrypted", "OPENHARNESS_OPENAI_CLIENT_ID": "openharness-client-test", "CODEX_MODEL": "gpt-direct-test"}  # 修改代码+DirectOAuthModelFactoryTest：构造满足 direct OAuth 门禁的模型环境；如果没有这行代码，默认工厂会因缺安全条件而拒绝运行。
        with mock.patch.dict(os.environ, env, clear=False):  # 新增代码+DirectOAuthModelFactoryTest：临时启用 direct OAuth；如果没有这行代码，测试会受外部环境影响。
            model = _default_real_model_factory()  # 新增代码+DirectOAuthModelFactoryTest：调用默认真实模型工厂；如果没有这行代码，没有产物可断言。
        self.assertIsInstance(model, CodexOAuthChatModel)  # 新增代码+DirectOAuthModelFactoryTest：确认 direct OAuth 使用 CodexOAuthChatModel；如果没有这行代码，运行时可能仍通过 CLI 绕路。
        self.assertEqual("gpt-direct-test", model._model)  # 新增代码+DirectOAuthModelFactoryTest：确认模型名来自 CODEX_MODEL；如果没有这行代码，用户配置的模型会被忽略。
        self.assertEqual("openharness-client-test", model._client_id)  # 新增代码+DirectOAuthModelFactoryTest：确认模型 refresh/token exchange 使用 OpenHarness 显式 client id；如果没有这行代码，代码可能偷偷回落到 OpenCode client id。
        self.assertIsInstance(model._token_store, GuiDirectOAuthCodexTokenStoreAdapter)  # 新增代码+DirectOAuthModelFactoryTest：确认使用 GUI direct OAuth token store 适配器；如果没有这行代码，模型刷新不会写回 OpenHarness token store。
    # 新增代码+DirectOAuthModelFactoryTest：测试段结束，test_default_real_model_factory_uses_codex_oauth_model_for_direct_oauth_mode 到此结束；如果没有边界说明，用户不容易看出覆盖的是默认模型工厂。

    def test_default_real_model_factory_uses_selected_gui_model_before_env_model(self) -> None:  # 新增代码+ComposerRealModelRoutingTest：测试段开始，验证 direct OAuth 真实模型优先使用 GUI 下拉选中的模型；如果没有这段，用户切换模型仍会调用 CODEX_MODEL 的固定值。
        from learning_agent.app.gui_agent_adapter import GuiDirectOAuthCodexTokenStoreAdapter, GuiAgentRunRequest, _default_real_model_factory  # 新增代码+ComposerRealModelRoutingTest：导入请求对象和默认工厂；如果没有这一行，测试无法模拟 GUI 底部菜单。
        from learning_agent.models.adapters import CodexOAuthChatModel  # 新增代码+ComposerRealModelRoutingTest：导入 OAuth 模型类型；如果没有这一行，无法检查真实工厂产物。

        env = {"OPENHARNESS_OPENAI_AUTH_MODE": "direct_oauth", "OPENHARNESS_OPENAI_EXPERIMENTAL": "1", "OPENHARNESS_PROVIDER_SECRET_STORE": "os_encrypted", "OPENHARNESS_OPENAI_CLIENT_ID": "openharness-client-test", "CODEX_MODEL": "gpt-env-should-not-win"}  # 新增代码+ComposerRealModelRoutingTest：构造环境变量默认模型；如果没有这一行，测试无法证明 GUI 选择优先级更高。
        request = GuiAgentRunRequest(session_id="session_real", turn_id="turn_real", run_id="run_real", prompt="你好", mode="real", provider_id="openai", model_id="gpt-5.5", reasoning_effort="ultra", permission_mode="full-access")  # 新增代码+ComposerRealModelRoutingTest：构造带模型选择的 GUI 请求；如果没有这一行，工厂只能退回环境变量。
        with mock.patch.dict(os.environ, env, clear=False):  # 新增代码+ComposerRealModelRoutingTest：临时启用 direct OAuth 环境；如果没有这一行，工厂会走错认证模式。
            model = _default_real_model_factory(request)  # 新增代码+ComposerRealModelRoutingTest：把 GUI 请求交给默认真实模型工厂；如果没有这一行，测试没有被测行为。
        self.assertIsInstance(model, CodexOAuthChatModel)  # 新增代码+ComposerRealModelRoutingTest：确认仍是 direct OAuth 模型；如果没有这一行，模型选择修复可能意外切回 CLI。
        self.assertEqual("gpt-5.5", model._model)  # 新增代码+ComposerRealModelRoutingTest：确认 GUI 下拉模型覆盖 CODEX_MODEL；如果没有这一行，用户选择 GPT-5.5 不会影响真实请求。
        self.assertEqual("openharness-client-test", model._client_id)  # 新增代码+ComposerRealModelRoutingTest：确认 client id 仍来自安全配置；如果没有这一行，修复模型选择时可能破坏 OAuth 门禁。
        self.assertIsInstance(model._token_store, GuiDirectOAuthCodexTokenStoreAdapter)  # 新增代码+ComposerRealModelRoutingTest：确认 token store 仍接 OpenHarness GUI store；如果没有这一行，刷新 token 可能不写回设置页。
    # 新增代码+ComposerRealModelRoutingTest：测试段结束，test_default_real_model_factory_uses_selected_gui_model_before_env_model 到此结束；如果没有边界说明，用户不容易看出覆盖的是模型选择优先级。

    def test_codex_cli_real_model_factory_uses_selected_gui_model_before_env_model(self) -> None:  # 新增代码+ComposerRealModelRoutingTest：测试段开始，验证 Codex CLI/OAuth 兼容路径也优先使用 GUI 下拉模型；如果没有这段，非 direct_oauth 真实路径仍会忽略用户选择。
        from learning_agent.app.gui_agent_adapter import GuiAgentRunRequest, _default_real_model_factory  # 新增代码+ComposerRealModelRoutingTest：导入请求对象和默认工厂；如果没有这一行，测试无法模拟 GUI 本轮模型上下文。
        from learning_agent.models.adapters import CodexCliChatModel  # 新增代码+ComposerRealModelRoutingTest：导入 Codex CLI 模型类型；如果没有这一行，测试无法确认工厂走的是 CLI/OAuth 兼容路径。

        env = {"OPENHARNESS_OPENAI_AUTH_MODE": "codex_cli", "CODEX_MODEL": "gpt-env-should-not-win", "CODEX_COMMAND": "codex-unit-test", "CODEX_TIMEOUT_SECONDS": "77"}  # 新增代码+ComposerRealModelRoutingTest：构造会诱发旧 bug 的环境默认模型；如果没有这一行，无法证明 GUI 选择覆盖环境变量。
        request = GuiAgentRunRequest(session_id="session_cli", turn_id="turn_cli", run_id="run_cli", prompt="你好", mode="real", provider_id="openai", model_id="gpt-5.5", reasoning_effort="ultra", permission_mode="full-access")  # 新增代码+ComposerRealModelRoutingTest：构造带 GPT-5.5 选择的 GUI 请求；如果没有这一行，工厂只能读取 CODEX_MODEL。
        with mock.patch.dict(os.environ, env, clear=False):  # 新增代码+ComposerRealModelRoutingTest：临时启用 CLI/OAuth 兼容模式；如果没有这一行，测试会受开发者本机环境污染。
            model = _default_real_model_factory(request)  # 新增代码+ComposerRealModelRoutingTest：把 GUI 请求交给真实模型工厂；如果没有这一行，测试没有实际被测结果。
        self.assertIsInstance(model, CodexCliChatModel)  # 新增代码+ComposerRealModelRoutingTest：确认非 direct_oauth 模式仍创建 Codex CLI 模型；如果没有这一行，工厂类型回归不会被发现。
        self.assertEqual("gpt-5.5", model._model)  # 新增代码+ComposerRealModelRoutingTest：确认 GUI 下拉模型覆盖 CODEX_MODEL；如果没有这一行，用户选择不同 OAuth 模型不会影响真实调用。
        self.assertEqual("codex-unit-test", model._codex_command)  # 新增代码+ComposerRealModelRoutingTest：确认命令仍来自 CODEX_COMMAND；如果没有这一行，修复模型选择时可能破坏现有启动配置。
        self.assertEqual(77, model._timeout_seconds)  # 新增代码+ComposerRealModelRoutingTest：确认超时仍来自 CODEX_TIMEOUT_SECONDS；如果没有这一行，真实长模型调用可能被错误默认值截断。
    # 新增代码+ComposerRealModelRoutingTest：测试段结束，test_codex_cli_real_model_factory_uses_selected_gui_model_before_env_model 到此结束；如果没有边界说明，用户不容易看出 CLI/OAuth 兼容路径也被覆盖。

    def test_gui_run_manager_treats_direct_oauth_source_as_real_model_connected(self) -> None:  # 新增代码+DirectOAuthModelFactoryTest：测试段开始，验证 bridge auto 模式承认 direct OAuth 连接；如果没有这段，设置页显示已连接但聊天仍 fake。
        from learning_agent.app import gui_bridge  # 新增代码+DirectOAuthModelFactoryTest：导入 bridge 模块以 patch provider payload；如果没有这行代码，测试会读取真实设置文件。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+DirectOAuthModelFactoryTest：导入真实 adapter 类型；如果没有这行代码，无法确认 auto 选择结果。

        payload = {"providers": [{"id": "openai", "connected": True, "source": "direct_oauth_experimental"}]}  # 新增代码+DirectOAuthModelFactoryTest：构造 direct OAuth 已连接 provider payload；如果没有这行代码，manager 无法看到 direct 来源。
        env = {"OPENHARNESS_OPENAI_AUTH_MODE": "direct_oauth"}  # 新增代码+DirectOAuthModelFactoryTest：启用 direct OAuth 认证模式；如果没有这行代码，默认真实模型工厂不会选择 direct OAuth。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectOAuthModelFactoryTest：创建隔离 workspace；如果没有这行代码，manager 会读取真实 memory 状态。
            with mock.patch.dict(os.environ, env, clear=False):  # 新增代码+DirectOAuthModelFactoryTest：临时设置环境变量；如果没有这行代码，测试会被外部模式污染。
                with mock.patch.object(gui_bridge, "build_provider_settings_payload", return_value=payload):  # 新增代码+DirectOAuthModelFactoryTest：替换 provider catalog 事实源；如果没有这行代码，测试需要真实登录。
                    manager = gui_bridge.GuiRunManager(Path(directory))  # 新增代码+DirectOAuthModelFactoryTest：创建 auto 模式 run manager；如果没有这行代码，无法验证 adapter 选择。
                    connected = manager._openai_real_provider_connected()  # 新增代码+DirectOAuthModelFactoryTest：读取真实模型连接门禁；如果没有这行代码，无法证明 direct 来源会放行。
        self.assertTrue(connected)  # 新增代码+DirectOAuthModelFactoryTest：确认 direct OAuth 已连接会放行真实模型；如果没有这行代码，聊天会继续 fake streaming。
        self.assertEqual("real", manager.agent_adapter_mode)  # 新增代码+DirectOAuthModelFactoryTest：确认 auto 模式切到 real；如果没有这行代码，登录成功后主聊天仍可能 fake。
        self.assertIsInstance(manager.agent_adapter, RealModelGuiAgentAdapter)  # 新增代码+DirectOAuthModelFactoryTest：确认 manager 创建真实 adapter；如果没有这行代码，运行时不会进入真实模型层。
    # 新增代码+DirectOAuthModelFactoryTest：测试段结束，test_gui_run_manager_treats_direct_oauth_source_as_real_model_connected 到此结束；如果没有边界说明，用户不容易看出覆盖的是 bridge auto 选择。

    def test_codex_oauth_model_refreshes_gui_token_store_and_uses_codex_endpoint(self) -> None:  # 新增代码+DirectOAuthModelFactoryTest：测试段开始，验证 direct OAuth 模型 refresh、账号头和远端 endpoint；如果没有这段，真实连接可能只显示已连但请求仍失败。
        from learning_agent.app.gui_agent_adapter import GuiDirectOAuthCodexTokenStoreAdapter  # 新增代码+DirectOAuthModelFactoryTest：导入 GUI token store 适配器；如果没有这行代码，模型无法使用 OpenHarness token store。
        from learning_agent.app.gui_provider_oauth_token_store import make_fake_token_store  # 新增代码+DirectOAuthModelFactoryTest：导入 fake token store；如果没有这行代码，测试会写入真实用户凭据目录。
        from learning_agent.models.adapters import CodexOAuthChatModel  # 新增代码+DirectOAuthModelFactoryTest：导入 Codex OAuth 模型；如果没有这行代码，无法验证 endpoint/header 行为。

        calls: list[dict[str, object]] = []  # 新增代码+DirectOAuthModelFactoryTest：记录 fake HTTP 请求；如果没有这行代码，测试无法确认 endpoint 和 header。
        model_payload = json.dumps({"decision_note": "fake", "text": "真实 direct OAuth 回答", "tool_calls": []}, ensure_ascii=False)  # 新增代码+DirectOAuthModelFactoryTest：准备 Codex responses 返回的模型 JSON 文本；如果没有这行代码，chat 解析器没有合法样本。

        def post_json(url: str, headers: dict[str, str], body: dict[str, object]) -> dict[str, object]:  # 新增代码+DirectOAuthModelFactoryTest：函数段开始，模拟 token refresh 和 Codex responses；如果没有这段，测试会访问真实网络。
            calls.append({"url": url, "headers": headers, "body": body})  # 新增代码+DirectOAuthModelFactoryTest：记录请求细节；如果没有这行代码，断言无法确认模型使用正确协议。
            if url.endswith("/oauth/token"):  # 新增代码+DirectOAuthModelFactoryTest：处理 access token 过期后的 refresh 请求；如果没有这行代码，测试无法覆盖刷新路径。
                self.assertEqual("refresh-old", body.get("refresh_token"))  # 新增代码+DirectOAuthModelFactoryTest：确认使用旧 refresh_token 续期；如果没有这行代码，模型可能没读到 GUI token store。
                self.assertEqual("openharness-client-test", body.get("client_id"))  # 新增代码+DirectOAuthModelFactoryTest：确认 refresh 使用 OpenHarness client id；如果没有这行代码，代码可能误用 OpenCode client id。
                return {"access_token": "access-new", "refresh_token": "refresh-new", "expires_in": 3600}  # 新增代码+DirectOAuthModelFactoryTest：返回刷新后的 token；如果没有这行代码，chat 无法继续请求模型。
            self.assertEqual(CodexOAuthChatModel.CODEX_API_ENDPOINT, url)  # 新增代码+DirectOAuthModelFactoryTest：确认模型请求发送到 Codex responses endpoint；如果没有这行代码，endpoint 漂移无法被发现。
            self.assertEqual("Bearer access-new", headers.get("authorization"))  # 新增代码+DirectOAuthModelFactoryTest：确认使用刷新后的 access token；如果没有这行代码，模型可能继续带旧过期 token。
            self.assertEqual("acct-old", headers.get("ChatGPT-Account-Id"))  # 新增代码+DirectOAuthModelFactoryTest：确认账号头被带上；如果没有这行代码，多账号 ChatGPT 连接可能路由错误。
            return {"output_text": model_payload}  # 新增代码+DirectOAuthModelFactoryTest：返回可解析模型文本；如果没有这行代码，chat 会进入格式错误路径。
        # 新增代码+DirectOAuthModelFactoryTest：函数段结束，post_json 到此结束；如果没有边界说明，用户不容易看出它是网络替身。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectOAuthModelFactoryTest：创建隔离 token store；如果没有这行代码，测试会污染真实凭据。
            fake_store = make_fake_token_store(Path(directory))  # 新增代码+DirectOAuthModelFactoryTest：创建明文 fake store；如果没有这行代码，测试无法检查刷新是否落盘。
            fake_store.set_tokens("openai", {"access_token": "access-old", "refresh_token": "refresh-old", "expires_at": 1, "account_id": "acct-old", "id_token": "id-old"})  # 新增代码+DirectOAuthModelFactoryTest：写入过期 token；如果没有这行代码，模型不会触发 refresh。
            store_adapter = GuiDirectOAuthCodexTokenStoreAdapter(token_store=fake_store)  # 新增代码+DirectOAuthModelFactoryTest：把 GUI store 适配给模型；如果没有这行代码，CodexOAuthChatModel 不能复用 direct OAuth token。
            model = CodexOAuthChatModel(model="gpt-direct-test", token_store=store_adapter, post_json=post_json, login_callback=lambda: self.fail("login should not be called"), client_id="openharness-client-test")  # 新增代码+DirectOAuthModelFactoryTest：创建带 fake HTTP 的 direct OAuth 模型；如果没有这行代码，测试没有被测模型。
            message = model.chat([{"role": "user", "content": "你好"}], [])  # 新增代码+DirectOAuthModelFactoryTest：执行一次真实模型适配器 chat；如果没有这行代码，refresh/header/endpoint 都不会发生。
            refreshed = fake_store.get_tokens("openai") or {}  # 新增代码+DirectOAuthModelFactoryTest：读取刷新后的 fake token；如果没有这行代码，无法确认 save 写回。
        self.assertEqual("真实 direct OAuth 回答", message.text)  # 新增代码+DirectOAuthModelFactoryTest：确认模型输出成功解析；如果没有这行代码，chat 可能只返回错误文本。
        self.assertEqual("access-new", refreshed.get("access_token"))  # 新增代码+DirectOAuthModelFactoryTest：确认刷新后的 access token 已写回；如果没有这行代码，下次请求仍会过期。
        self.assertEqual("refresh-new", refreshed.get("refresh_token"))  # 新增代码+DirectOAuthModelFactoryTest：确认刷新后的 refresh token 已写回；如果没有这行代码，长期登录会丢失续期能力。
        self.assertEqual(2, len(calls))  # 新增代码+DirectOAuthModelFactoryTest：确认先 refresh 再请求 Codex endpoint；如果没有这行代码，调用顺序可能漏掉模型请求。
    # 新增代码+DirectOAuthModelFactoryTest：测试段结束，test_codex_oauth_model_refreshes_gui_token_store_and_uses_codex_endpoint 到此结束；如果没有边界说明，用户不容易看出覆盖的是模型真实请求合同。
# 新增代码+DirectOAuthModelFactoryTest：测试类段结束，GuiDirectOAuthModelFactoryTests 到此结束；如果没有边界说明，用户不容易看出本文件只测 direct OAuth 模型工厂。


if __name__ == "__main__":  # 新增代码+DirectOAuthModelFactoryTest：允许直接运行本文件；如果没有这行代码，手动排查时不会启动测试。
    unittest.main()  # 新增代码+DirectOAuthModelFactoryTest：启动 unittest；如果没有这行代码，直接 python 文件不会执行测试。
