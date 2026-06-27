import json  # 新增代码+OpenAIRealOAuthAttemptTest：读取设置和密文文件验证无明文 token；如果没有这行，测试无法做泄漏断言。
import socket  # 新增代码+OpenAIRealOAuthCallbackTest：为回调监听测试分配临时本机端口；如果没有这行，测试只能硬编码 1455 并容易和真实进程冲突。
import sys  # 新增代码+OpenAIRealOAuthAttemptTest：判断当前平台是否支持 Windows DPAPI；如果没有这行，非 Windows 会误跑 OS 加密测试。
import time  # 新增代码+OpenAIRealOAuthCallbackTest：轮询等待 callback server 启动；如果没有这行，测试会因为线程启动竞态偶发失败。
from pathlib import Path  # 新增代码+OpenAIRealOAuthAttemptTest：标注 tmp_path 类型；如果没有这行，路径语义不清楚。
import urllib.request  # 新增代码+OpenAIRealOAuthCallbackTest：用真实 HTTP GET 访问本机 callback；如果没有这行，测试不能证明浏览器回调路径可用。
from urllib.parse import parse_qs, quote, urlparse  # 修改代码+OpenAIRealOAuthCallbackTest：增加 quote 编码 callback 参数；如果没有 quote，state/code 中的安全字符可能破坏测试 URL。

import pytest  # 新增代码+OpenAIRealOAuthAttemptTest：使用 pytest monkeypatch 和 skip；如果没有这行，测试无法隔离真实环境变量。


def _enable_real_openai_oauth_env(monkeypatch) -> None:  # 新增代码+OpenAIRealOAuthAttemptTest：helper 段开始，配置真实 OAuth 安全门禁；如果没有这段，每个测试会重复环境变量。
    monkeypatch.setenv("OPENHARNESS_OPENAI_AUTH_MODE", "real_browser")  # 新增代码+OpenAIRealOAuthAttemptTest：启用真实浏览器 OAuth 模式；如果没有这行，start 会继续走 mock。
    monkeypatch.setenv("OPENHARNESS_OPENAI_EXPERIMENTAL", "1")  # 新增代码+OpenAIRealOAuthAttemptTest：显式开启实验开关；如果没有这行，真实 OAuth 门禁会拒绝。
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "os_encrypted")  # 新增代码+OpenAIRealOAuthAttemptTest：强制真实 token 使用 OS 加密 store；如果没有这行，门禁会拒绝 dev_json。
    monkeypatch.setenv("OPENHARNESS_OPENAI_CLIENT_ID", "app_EMoamEEZ73f0CkXaXp7hrann")  # 新增代码+OpenAIRealOAuthAttemptTest：使用观察到的 OpenCode 参考 client id；如果没有这行，client source 诊断无法覆盖。
    monkeypatch.setenv("OPENHARNESS_OPENAI_CALLBACK_PORT", "1455")  # 新增代码+OpenAIRealOAuthAttemptTest：固定本机回调端口；如果没有这行，授权 URL 端口断言不稳定。
# 新增代码+OpenAIRealOAuthAttemptTest：helper 段结束，_enable_real_openai_oauth_env 到此结束；如果没有边界说明，初学者不易看出它只配 env。


def _clear_auth_attempt_registry() -> None:  # 新增代码+OpenAIRealOAuthAttemptTest：helper 段开始，清理进程内 attempt registry；如果没有这段，测试之间可能互相影响。
    from learning_agent.app.gui_provider_auth_attempts import _ATTEMPTS, _ATTEMPT_LOCK, _ATTEMPT_OAUTH_SECRETS  # 新增代码+OpenAIRealOAuthAttemptTest：导入受控测试 registry；如果没有这行，无法隔离全局状态。

    with _ATTEMPT_LOCK:  # 新增代码+OpenAIRealOAuthAttemptTest：锁住 registry 清理；如果没有这行，并发状态读取可能看到半清理。
        _ATTEMPTS.clear()  # 新增代码+OpenAIRealOAuthAttemptTest：清空公开 attempt；如果没有这行，旧 attempt 会影响 start/cancel。
        _ATTEMPT_OAUTH_SECRETS.clear()  # 新增代码+OpenAIRealOAuthAttemptTest：清空私有 OAuth state/verifier；如果没有这行，旧 verifier 可能影响 complete。
# 新增代码+OpenAIRealOAuthAttemptTest：helper 段结束，_clear_auth_attempt_registry 到此结束；如果没有边界说明，初学者不易看出它只做测试隔离。


def _free_tcp_port() -> int:  # 新增代码+OpenAIRealOAuthCallbackTest：helper 段开始，寻找一个当前空闲的本机端口；如果没有这段，callback listener 测试会和真实 1455/其它测试互相抢端口。
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:  # 新增代码+OpenAIRealOAuthCallbackTest：创建临时 TCP socket；如果没有这行，无法让系统安全挑选空闲端口。
        probe.bind(("localhost", 0))  # 新增代码+OpenAIRealOAuthCallbackTest：绑定 0 号端口让系统分配空闲端口；如果没有这行，测试端口需要硬编码。
        return int(probe.getsockname()[1])  # 新增代码+OpenAIRealOAuthCallbackTest：返回系统分配的端口号；如果没有这行，调用方拿不到 callback 端口。
# 新增代码+OpenAIRealOAuthCallbackTest：helper 段结束，_free_tcp_port 到此结束；如果没有边界说明，初学者不易看出它只做测试端口选择。


def test_real_browser_oauth_start_builds_authorization_url_from_explicit_config(tmp_path: Path, monkeypatch) -> None:  # 新增代码+OpenAIRealOAuthAttemptTest：测试段开始，验证真实授权 URL 参数；如果没有这段，OpenAI 连接可能仍跳 mock 或缺 PKCE。
    _enable_real_openai_oauth_env(monkeypatch)  # 新增代码+OpenAIRealOAuthAttemptTest：打开真实 OAuth 安全门禁；如果没有这行，start 不会生成真实 URL。
    callback_port = _free_tcp_port()  # 修改代码+OpenAIRealOAuthCallbackOwnerProbeTest：为本测试选择隔离 callback 端口；如果没有这行，用户正在运行的 1455 会让单元测试误判失败。
    monkeypatch.setenv("OPENHARNESS_OPENAI_CALLBACK_PORT", str(callback_port))  # 修改代码+OpenAIRealOAuthCallbackOwnerProbeTest：让授权 URL 指向隔离端口；如果没有这行，测试会依赖真实桌面 GUI 的端口状态。
    _clear_auth_attempt_registry()  # 新增代码+OpenAIRealOAuthAttemptTest：清理全局状态；如果没有这行，旧 attempt 可能干扰断言。
    from learning_agent.app.gui_provider_auth_attempts import start_provider_auth_attempt  # 新增代码+OpenAIRealOAuthAttemptTest：导入真实 start 入口；如果没有这行，测试没有被测目标。

    started = start_provider_auth_attempt(tmp_path, "openai", "chatgpt-browser")  # 新增代码+OpenAIRealOAuthAttemptTest：启动真实 browser OAuth attempt；如果没有这行，无法得到授权 URL。
    attempt = started["attempt"]  # 新增代码+OpenAIRealOAuthAttemptTest：读取 attempt payload；如果没有这行，后续 query 解析没有来源。
    parsed = urlparse(attempt["url"])  # 新增代码+OpenAIRealOAuthAttemptTest：解析授权 URL；如果没有这行，无法稳定检查 query。
    query = parse_qs(parsed.query)  # 新增代码+OpenAIRealOAuthAttemptTest：解析 query 参数；如果没有这行，URL 编码会影响断言。

    assert parsed.scheme == "https"  # 新增代码+OpenAIRealOAuthAttemptTest：确认使用 HTTPS 授权入口；如果没有这行，OAuth 可能走不安全协议。
    assert parsed.netloc == "auth.openai.com"  # 新增代码+OpenAIRealOAuthAttemptTest：确认授权域名是 OpenAI；如果没有这行，链接可能仍是 mock server。
    assert query["response_type"] == ["code"]  # 新增代码+OpenAIRealOAuthAttemptTest：确认走授权码 flow；如果没有这行，token exchange 合同会错。
    assert query["client_id"] == ["app_EMoamEEZ73f0CkXaXp7hrann"]  # 新增代码+OpenAIRealOAuthAttemptTest：确认 client id 来自显式配置；如果没有这行，可能误用硬编码默认。
    assert query["redirect_uri"] == [f"http://localhost:{callback_port}/auth/callback"]  # 修改代码+OpenAIRealOAuthCallbackOwnerProbeTest：确认 redirect_uri 使用隔离端口；如果没有这行，测试会被真实 1455 上的其它 bridge 影响。
    assert query["scope"] == ["openid profile email offline_access"]  # 新增代码+OpenAIRealOAuthAttemptTest：确认 scope 包含 offline_access；如果没有这行，refresh token 可能拿不到。
    assert len(query["code_challenge"][0]) > 20  # 新增代码+OpenAIRealOAuthAttemptTest：确认生成了 PKCE challenge；如果没有这行，URL 可能缺安全参数。
    assert query["code_challenge_method"] == ["S256"]  # 新增代码+OpenAIRealOAuthAttemptTest：确认 PKCE 方法为 S256；如果没有这行，授权端可能拒绝。
    assert query["id_token_add_organizations"] == ["true"]  # 新增代码+OpenAIRealOAuthAttemptTest：确认携带组织信息请求；如果没有这行，账号发现可能缺上下文。
    assert query["codex_cli_simplified_flow"] == ["true"]  # 新增代码+OpenAIRealOAuthAttemptTest：确认使用 Codex 简化 flow 标记；如果没有这行，授权页面可能不是预期体验。
    assert query["originator"] == ["opencode"]  # 修改代码+OpenAIRealOAuthOpenCodeParityTest：确认来源标记与 OpenCode 成功链路一致；如果没有这行，OpenAI 官方授权可能拒绝非预期 originator。
    assert query["state"] == [attempt["oauth_state"]]  # 新增代码+OpenAIRealOAuthAttemptTest：确认 URL state 与 attempt state 一致；如果没有这行，回调无法校验。
    assert attempt["oauth_client_source"] == "observed_opencode_reference"  # 新增代码+OpenAIRealOAuthAttemptTest：确认 client 来源诊断；如果没有这行，用户不知道使用的是观察参考值。
# 新增代码+OpenAIRealOAuthAttemptTest：测试段结束，真实授权 URL 合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


def test_real_oauth_wrong_state_fails_and_correct_state_stores_encrypted_refs_only(tmp_path: Path, monkeypatch) -> None:  # 新增代码+OpenAIRealOAuthAttemptTest：测试段开始，验证 state 校验和加密落盘；如果没有这段，真实 OAuth 回调安全性没有证据。
    if sys.platform != "win32":  # 新增代码+OpenAIRealOAuthAttemptTest：只在 Windows 验证 DPAPI 加密落盘；如果没有这行，非 Windows 环境会因缺 DPAPI 失败。
        pytest.skip("Windows DPAPI CurrentUser is required for real OAuth encrypted token storage.")  # 新增代码+OpenAIRealOAuthAttemptTest：非 Windows 明确跳过；如果没有这行，失败原因会误导。
    _enable_real_openai_oauth_env(monkeypatch)  # 新增代码+OpenAIRealOAuthAttemptTest：打开真实 OAuth 安全门禁；如果没有这行，token 保存会被拒绝。
    callback_port = _free_tcp_port()  # 修改代码+OpenAIRealOAuthCallbackOwnerProbeTest：为本测试选择隔离 callback 端口；如果没有这行，用户正在运行的 1455 会让单元测试误判失败。
    monkeypatch.setenv("OPENHARNESS_OPENAI_CALLBACK_PORT", str(callback_port))  # 修改代码+OpenAIRealOAuthCallbackOwnerProbeTest：让授权 URL 指向隔离端口；如果没有这行，测试会依赖真实桌面 GUI 的端口状态。
    _clear_auth_attempt_registry()  # 新增代码+OpenAIRealOAuthAttemptTest：清理全局状态；如果没有这行，旧 OAuth secret 可能影响 state。
    from learning_agent.app.gui_provider_auth_attempts import complete_real_provider_auth_attempt_with_tokens, start_provider_auth_attempt  # 新增代码+OpenAIRealOAuthAttemptTest：导入真实 start/complete；如果没有这行，测试没有被测入口。
    from learning_agent.app.gui_provider_secret_store import make_provider_secret_store  # 新增代码+OpenAIRealOAuthAttemptTest：导入 store factory；如果没有这行，测试无法验证 token 可解密。
    from learning_agent.app.gui_provider_settings import build_provider_settings_payload, provider_settings_file  # 新增代码+OpenAIRealOAuthAttemptTest：导入 catalog 和设置文件路径；如果没有这行，无法验证连接状态和无明文。

    wrong = start_provider_auth_attempt(tmp_path, "openai", "chatgpt-browser")  # 新增代码+OpenAIRealOAuthAttemptTest：启动用于错 state 的 attempt；如果没有这行，无法证明错配失败。
    wrong_attempt_id = str(wrong["attempt"]["attempt_id"])  # 新增代码+OpenAIRealOAuthAttemptTest：读取错 state attempt id；如果没有这行，complete 无法定位。
    with pytest.raises(Exception) as wrong_state_error:  # 新增代码+OpenAIRealOAuthAttemptTest：捕获预期 state 错误；如果没有这行，测试会在抛错处中断。
        complete_real_provider_auth_attempt_with_tokens(tmp_path, wrong_attempt_id, "wrong-state", {"access_token": "test_access_token_value"})  # 新增代码+OpenAIRealOAuthAttemptTest：用错误 state 完成；如果没有这行，state 校验没有输入。
    assert getattr(wrong_state_error.value, "code", "") == "openai_oauth_state_mismatch"  # 新增代码+OpenAIRealOAuthAttemptTest：确认错 state 错误码稳定；如果没有这行，前端无法精确处理。

    started = start_provider_auth_attempt(tmp_path, "openai", "chatgpt-browser")  # 新增代码+OpenAIRealOAuthAttemptTest：启动用于正确 state 的 attempt；如果没有这行，无法验证成功落盘。
    attempt = started["attempt"]  # 新增代码+OpenAIRealOAuthAttemptTest：读取 attempt payload；如果没有这行，无法拿到 state。
    token_payload = {"access_token": "test_access_token_value", "refresh_token": "test_refresh_token_value", "id_token": "test_id_token_value", "expires_in": 3600, "account_id": "acct_test_001", "account_label": "Test Account"}  # 新增代码+OpenAIRealOAuthAttemptTest：准备 fake-safe token payload；如果没有这行，正确完成没有 token 输入。
    completed = complete_real_provider_auth_attempt_with_tokens(tmp_path, str(attempt["attempt_id"]), str(attempt["oauth_state"]), token_payload)  # 新增代码+OpenAIRealOAuthAttemptTest：用正确 state 完成真实 OAuth；如果没有这行，token refs 不会保存。
    settings_text = provider_settings_file(tmp_path).read_text(encoding="utf-8")  # 新增代码+OpenAIRealOAuthAttemptTest：读取主配置文本；如果没有这行，无法检查 settings 不含明文 token。
    secret_text = (tmp_path / "memory" / "gui_provider_settings" / "secrets.os.json").read_text(encoding="utf-8")  # 新增代码+OpenAIRealOAuthAttemptTest：读取 OS 密文文件；如果没有这行，无法检查密文文件不含明文 token。
    catalog = build_provider_settings_payload(tmp_path)  # 新增代码+OpenAIRealOAuthAttemptTest：读取 provider catalog；如果没有这行，无法验证 UI 会显示已连接。
    store = make_provider_secret_store(tmp_path)  # 新增代码+OpenAIRealOAuthAttemptTest：创建 OS 加密 store；如果没有这行，无法验证后端内部可取回 token。
    settings = json.loads(settings_text)  # 新增代码+OpenAIRealOAuthAttemptTest：解析主配置；如果没有这行，无法读取 secret_refs。
    refs = settings["auth"]["openai"]["secret_refs"]  # 新增代码+OpenAIRealOAuthAttemptTest：读取主配置里的 token 引用组；如果没有这行，无法验证只保存引用。
    openai = next(provider for provider in catalog["providers"] if provider["id"] == "openai")  # 新增代码+OpenAIRealOAuthAttemptTest：读取 catalog 中 OpenAI 行；如果没有这行，无法断言 connected。

    assert completed["attempt"]["status"] == "complete"  # 新增代码+OpenAIRealOAuthAttemptTest：确认正确 state 后 attempt 完成；如果没有这行，前端仍会等待。
    assert "test_access_token_value" not in settings_text  # 新增代码+OpenAIRealOAuthAttemptTest：确认 access token 不在主配置；如果没有这行，token 可能泄露到 providers.json。
    assert "test_refresh_token_value" not in settings_text  # 新增代码+OpenAIRealOAuthAttemptTest：确认 refresh token 不在主配置；如果没有这行，长期 token 可能明文落盘。
    assert "test_id_token_value" not in settings_text  # 新增代码+OpenAIRealOAuthAttemptTest：确认 id token 不在主配置；如果没有这行，身份 token 可能明文落盘。
    assert "test_access_token_value" not in secret_text  # 新增代码+OpenAIRealOAuthAttemptTest：确认 access token 不在密文文件明文出现；如果没有这行，OS 加密目标可能退化。
    assert "test_refresh_token_value" not in secret_text  # 新增代码+OpenAIRealOAuthAttemptTest：确认 refresh token 不在密文文件明文出现；如果没有这行，断开前 token 可能被读出。
    assert store.get_secret(refs["access_token"]) == "test_access_token_value"  # 新增代码+OpenAIRealOAuthAttemptTest：确认后端可通过引用取回 access token；如果没有这行，Direct SSE 无法认证。
    assert store.get_secret(refs["refresh_token"]) == "test_refresh_token_value"  # 新增代码+OpenAIRealOAuthAttemptTest：确认后端可通过引用取回 refresh token；如果没有这行，过期后无法刷新。
    assert settings["auth"]["openai"]["oauth_client_source"] == "observed_opencode_reference"  # 新增代码+OpenAIRealOAuthAttemptTest：确认 client source 落盘；如果没有这行，诊断无法说明来源。
    assert openai["connected"] is True  # 新增代码+OpenAIRealOAuthAttemptTest：确认 catalog 显示真实 OAuth 已连接；如果没有这行，设置页会误显示未连接。
    assert openai["source"] == "oauth"  # 新增代码+OpenAIRealOAuthAttemptTest：确认来源是 oauth；如果没有这行，UI 无法区分 API key 和 OAuth。
# 新增代码+OpenAIRealOAuthAttemptTest：测试段结束，真实 OAuth 完成合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


def test_openai_oauth_code_exchange_posts_form_request(monkeypatch) -> None:  # 新增代码+OpenAIRealOAuthExchangeTest：测试段开始，验证授权 code 会按表单请求换 token；如果没有这段，callback 即使收到 code 也可能无法换 token。
    from learning_agent.app.gui_provider_openai_oauth import OpenAIRealOAuthAttemptSecret, exchange_openai_oauth_code_for_tokens  # 新增代码+OpenAIRealOAuthExchangeTest：导入真实 exchange 函数和 secret 类型；如果没有这行，测试没有被测目标。

    captured: dict[str, object] = {}  # 新增代码+OpenAIRealOAuthExchangeTest：保存 fake urlopen 收到的请求；如果没有这行，测试无法断言请求体。

    class FakeResponse:  # 新增代码+OpenAIRealOAuthExchangeTest：类段开始，模拟 urllib HTTP 响应；如果没有这个类，测试需要真实访问 OpenAI。
        def __enter__(self):  # 新增代码+OpenAIRealOAuthExchangeTest：进入上下文管理器；如果没有这段，with urlopen(...) 会失败。
            return self  # 新增代码+OpenAIRealOAuthExchangeTest：返回自身供读取响应体；如果没有这行，调用方拿不到 read 方法。

        def __exit__(self, exc_type, exc, traceback) -> None:  # 新增代码+OpenAIRealOAuthExchangeTest：退出上下文管理器；如果没有这段，with 语法不完整。
            return None  # 新增代码+OpenAIRealOAuthExchangeTest：不吞异常；如果没有这行，异常传播语义不清楚。

        def read(self) -> bytes:  # 新增代码+OpenAIRealOAuthExchangeTest：返回 fake JSON 响应体；如果没有这段，exchange 无法解析 token payload。
            return b'{"access_token":"exchanged_access","refresh_token":"exchanged_refresh","expires_in":3600}'  # 新增代码+OpenAIRealOAuthExchangeTest：提供不含真实 secret 的 token 响应；如果没有这行，测试没有成功 payload。
    # 新增代码+OpenAIRealOAuthExchangeTest：类段结束，FakeResponse 到此结束；如果没有边界说明，初学者不易看出它只模拟 HTTP。

    def fake_urlopen(request, timeout: int):  # 新增代码+OpenAIRealOAuthExchangeTest：fake 段开始，拦截 token endpoint 请求；如果没有这段，测试会真实联网。
        captured["url"] = request.full_url  # 新增代码+OpenAIRealOAuthExchangeTest：记录请求 URL；如果没有这行，无法确认请求打到 token 端点。
        captured["headers"] = dict(request.header_items())  # 新增代码+OpenAIRealOAuthExchangeTest：记录请求头；如果没有这行，无法确认 form content-type。
        captured["body"] = request.data.decode("utf-8")  # 新增代码+OpenAIRealOAuthExchangeTest：记录表单请求体；如果没有这行，无法确认 code/verifier/client_id。
        captured["timeout"] = timeout  # 新增代码+OpenAIRealOAuthExchangeTest：记录 timeout；如果没有这行，无法确认请求不会无限等待。
        return FakeResponse()  # 新增代码+OpenAIRealOAuthExchangeTest：返回 fake 响应；如果没有这行，exchange 没有可解析结果。
    # 新增代码+OpenAIRealOAuthExchangeTest：fake 段结束，fake_urlopen 到此结束；如果没有边界说明，初学者不易看出它只替代网络。

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)  # 新增代码+OpenAIRealOAuthExchangeTest：替换标准库联网函数；如果没有这行，测试会访问外网。
    secret = OpenAIRealOAuthAttemptSecret(attempt_id="auth_attempt_exchange", oauth_state="state_value", code_verifier="verifier_value", redirect_uri="http://localhost:1455/auth/callback", client_id="client_value", oauth_client_source="operator_configured")  # 新增代码+OpenAIRealOAuthExchangeTest：构造 token exchange 所需私有 OAuth 材料；如果没有这行，exchange 缺少 redirect/client/verifier。
    payload = exchange_openai_oauth_code_for_tokens(secret, "authorization_code_value")  # 新增代码+OpenAIRealOAuthExchangeTest：执行被测 exchange；如果没有这行，测试不会覆盖实现。
    form = parse_qs(str(captured["body"]))  # 新增代码+OpenAIRealOAuthExchangeTest：解析 form body；如果没有这行，断言只能脆弱匹配字符串。

    assert payload["access_token"] == "exchanged_access"  # 新增代码+OpenAIRealOAuthExchangeTest：确认返回解析后的 access token；如果没有这行，调用方可能拿不到 token。
    assert captured["url"] == "https://auth.openai.com/oauth/token"  # 新增代码+OpenAIRealOAuthExchangeTest：确认请求 OpenAI token endpoint；如果没有这行，exchange 可能打错地址。
    assert form["grant_type"] == ["authorization_code"]  # 新增代码+OpenAIRealOAuthExchangeTest：确认授权码 flow；如果没有这行，服务端会拒绝请求。
    assert form["code"] == ["authorization_code_value"]  # 新增代码+OpenAIRealOAuthExchangeTest：确认 callback code 被传入；如果没有这行，无法换 token。
    assert form["redirect_uri"] == ["http://localhost:1455/auth/callback"]  # 新增代码+OpenAIRealOAuthExchangeTest：确认 redirect_uri 与授权 URL 一致；如果没有这行，OAuth token 端会拒绝。
    assert form["client_id"] == ["client_value"]  # 新增代码+OpenAIRealOAuthExchangeTest：确认 client id 被传入；如果没有这行，OpenAI 无法识别 OAuth app。
    assert form["code_verifier"] == ["verifier_value"]  # 新增代码+OpenAIRealOAuthExchangeTest：确认 PKCE verifier 被传入；如果没有这行，S256 challenge 无法验证。
    assert captured["timeout"] == 30  # 新增代码+OpenAIRealOAuthExchangeTest：确认 token exchange 有明确超时；如果没有这行，官方无响应会卡住 GUI。
# 新增代码+OpenAIRealOAuthExchangeTest：测试段结束，token exchange 合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


def test_real_oauth_callback_listener_exchanges_code_and_updates_catalog(tmp_path: Path, monkeypatch) -> None:  # 新增代码+OpenAIRealOAuthCallbackTest：测试段开始，验证浏览器 callback 能把 code 换 token 并刷新 catalog；如果没有这段，真实网页登录完成后仍可能无人接收。
    if sys.platform != "win32":  # 新增代码+OpenAIRealOAuthCallbackTest：真实 token 保存仍依赖 Windows DPAPI；如果没有这行，非 Windows CI 会误报实现失败。
        pytest.skip("Windows DPAPI CurrentUser is required for real OAuth encrypted token storage.")  # 新增代码+OpenAIRealOAuthCallbackTest：非 Windows 明确跳过；如果没有这行，失败原因会误导。
    callback_port = _free_tcp_port()  # 新增代码+OpenAIRealOAuthCallbackTest：为本测试选择独立 callback 端口；如果没有这行，测试会占用或依赖用户真实 1455。
    _enable_real_openai_oauth_env(monkeypatch)  # 新增代码+OpenAIRealOAuthCallbackTest：打开真实 OAuth 三重门禁；如果没有这行，start 会退回 mock。
    monkeypatch.setenv("OPENHARNESS_OPENAI_CALLBACK_PORT", str(callback_port))  # 新增代码+OpenAIRealOAuthCallbackTest：让授权 URL 指向测试端口；如果没有这行，callback 会打到默认 1455。
    _clear_auth_attempt_registry()  # 新增代码+OpenAIRealOAuthCallbackTest：清理旧 attempt 和私有 state；如果没有这行，state 查找可能命中旧数据。
    from learning_agent.app import gui_provider_auth_attempts as attempts  # 新增代码+OpenAIRealOAuthCallbackTest：导入 auth-attempt 模块以便 monkeypatch token exchange；如果没有这行，测试会真实联网。
    from learning_agent.app.gui_provider_settings import build_provider_settings_payload  # 新增代码+OpenAIRealOAuthCallbackTest：导入 provider catalog 构造器；如果没有这行，测试无法确认 GUI 会显示已连接。

    exchange_calls: list[dict[str, str]] = []  # 新增代码+OpenAIRealOAuthCallbackTest：记录 fake token exchange 输入；如果没有这行，测试不能证明 callback code 被传到交换层。

    def fake_exchange(oauth_secret, code: str) -> dict[str, object]:  # 新增代码+OpenAIRealOAuthCallbackTest：fake 段开始，替代真实 OpenAI `/oauth/token` 请求；如果没有这段，测试会访问外网并依赖真实账号。
        exchange_calls.append({"code": code, "redirect_uri": oauth_secret.redirect_uri, "client_id": oauth_secret.client_id})  # 新增代码+OpenAIRealOAuthCallbackTest：记录低敏交换参数；如果没有这行，无法断言 code/redirect/client 正确传递。
        return {"access_token": "callback_access_token_value", "refresh_token": "callback_refresh_token_value", "id_token": "callback_id_token_value", "account_id": "acct_callback_001", "account_label": "Callback Account"}  # 新增代码+OpenAIRealOAuthCallbackTest：返回 fake-safe token payload；如果没有这行，callback 完成无法形成真实 OAuth 连接。
    # 新增代码+OpenAIRealOAuthCallbackTest：fake 段结束，fake_exchange 到此结束；如果没有边界说明，初学者不易看出它只替代联网。

    monkeypatch.setattr(attempts, "exchange_openai_oauth_code_for_tokens", fake_exchange, raising=False)  # 新增代码+OpenAIRealOAuthCallbackTest：把真实 token exchange 替换为 fake；如果没有这行，测试会向 OpenAI 官方发请求。
    started = attempts.start_provider_auth_attempt(tmp_path, "openai", "chatgpt-browser")  # 新增代码+OpenAIRealOAuthCallbackTest：启动真实 browser auth-attempt；如果没有这行，callback server 没有 state 可匹配。
    attempt = started["attempt"]  # 新增代码+OpenAIRealOAuthCallbackTest：读取 attempt payload；如果没有这行，测试拿不到 attempt_id/state。
    state = quote(str(attempt["oauth_state"]), safe="")  # 新增代码+OpenAIRealOAuthCallbackTest：编码 state query 参数；如果没有这行，URL 安全字符可能被错误解释。
    code = quote("test_authorization_code", safe="")  # 新增代码+OpenAIRealOAuthCallbackTest：编码 fake authorization code；如果没有这行，callback URL 构造不完整。
    callback_url = f"http://127.0.0.1:{callback_port}/auth/callback?code={code}&state={state}"  # 修改代码+OpenAIRealOAuthCallbackTest：用 IPv4 loopback 快速访问同一个本机 callback；如果没有这行，未监听端口在 Windows 上可能慢速超时。

    response_text = ""  # 新增代码+OpenAIRealOAuthCallbackTest：准备保存 callback HTML；如果没有这行，循环外无法断言页面内容。
    for _ in range(20):  # 修改代码+OpenAIRealOAuthCallbackTest：最多等待约 1 秒让后台监听线程启动；如果没有这行，红测和回归都会在 Windows 上拖太久。
        try:  # 新增代码+OpenAIRealOAuthCallbackTest：尝试访问 callback；如果没有这行，第一次连接失败会直接终止测试。
            with urllib.request.urlopen(callback_url, timeout=0.2) as response:  # 修改代码+OpenAIRealOAuthCallbackTest：真实 GET 本机 callback 且快速失败；如果没有这行，listener 缺失时红测会等待数分钟。
                response_text = response.read().decode("utf-8")  # 新增代码+OpenAIRealOAuthCallbackTest：读取 callback 返回页面；如果没有这行，无法确认用户看到成功页。
            break  # 新增代码+OpenAIRealOAuthCallbackTest：访问成功后退出等待循环；如果没有这行，测试会重复提交同一个 code。
        except OSError:  # 新增代码+OpenAIRealOAuthCallbackTest：容忍监听线程尚未启动；如果没有这行，测试会因毫秒级竞态失败。
            time.sleep(0.05)  # 新增代码+OpenAIRealOAuthCallbackTest：短暂等待后台线程；如果没有这行，循环会忙等浪费 CPU。

    status = attempts.get_provider_auth_attempt_status(attempt["attempt_id"])  # 新增代码+OpenAIRealOAuthCallbackTest：读取 callback 后 attempt 状态；如果没有这行，无法确认前端轮询会看到 complete。
    catalog = build_provider_settings_payload(tmp_path)  # 新增代码+OpenAIRealOAuthCallbackTest：读取 callback 后 provider catalog；如果没有这行，无法确认设置页会显示已连接。
    openai = next(provider for provider in catalog["providers"] if provider["id"] == "openai")  # 新增代码+OpenAIRealOAuthCallbackTest：定位 OpenAI provider 行；如果没有这行，后续断言没有目标。

    assert "Authorization Successful" in response_text  # 新增代码+OpenAIRealOAuthCallbackTest：确认浏览器看到成功页；如果没有这行，用户可能以为授权失败。
    assert exchange_calls == [{"code": "test_authorization_code", "redirect_uri": f"http://localhost:{callback_port}/auth/callback", "client_id": "app_EMoamEEZ73f0CkXaXp7hrann"}]  # 新增代码+OpenAIRealOAuthCallbackTest：确认 callback code 被正确送到 token exchange；如果没有这行，可能保存的是错误授权材料。
    assert status["attempt"]["status"] == "complete"  # 新增代码+OpenAIRealOAuthCallbackTest：确认 attempt 进入完成态；如果没有这行，前端会一直显示等待授权。
    assert status["attempt"]["message"] == "real_oauth_completed"  # 新增代码+OpenAIRealOAuthCallbackTest：确认完成消息是真实 OAuth；如果没有这行，mock/real 状态容易混淆。
    assert openai["connected"] is True  # 新增代码+OpenAIRealOAuthCallbackTest：确认 provider catalog 显示已连接；如果没有这行，设置页仍会显示未连接。
    assert openai["source"] == "oauth"  # 新增代码+OpenAIRealOAuthCallbackTest：确认来源是 OAuth；如果没有这行，UI 无法区分 API key 与 ChatGPT OAuth。
    assert openai["direct_route_status"] == "direct_sse_ready"  # 新增代码+OpenAIRealOAuthCallbackTest：确认真实 OAuth 后 Direct SSE 可选；如果没有这行，底部模型路由仍可能不可用。
# 新增代码+OpenAIRealOAuthCallbackTest：测试段结束，callback listener 合同到此结束；如果没有边界说明，初学者不易看出覆盖的是浏览器回调闭环。
def test_real_oauth_start_rejects_callback_port_owned_by_another_process(tmp_path: Path, monkeypatch) -> None:  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：测试段开始，验证端口被其它进程占用时拒绝启动真实 OAuth；如果没有这段，GUI 会生成一个回调会进错进程的假 pending。
    callback_port = _free_tcp_port()  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：先选择一个测试专用端口；如果没有这行，测试可能误伤用户真实 1455。
    _enable_real_openai_oauth_env(monkeypatch)  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：打开真实 OAuth 安全门禁；如果没有这行，start 会走 mock 而不是 callback listener。
    monkeypatch.setenv("OPENHARNESS_OPENAI_CALLBACK_PORT", str(callback_port))  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：让授权 URL 使用被测试端口；如果没有这行，测试无法控制冲突端口。
    _clear_auth_attempt_registry()  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：清理旧 attempt 状态；如果没有这行，旧 state 可能干扰失败断言。
    from learning_agent.app.gui_provider_auth_attempts import _CALLBACK_SERVER_LOCK, _CALLBACK_SERVERS, start_provider_auth_attempt  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：导入被测 start 和当前进程 callback registry；如果没有这行，测试无法模拟“外部占用”。
    from learning_agent.app.gui_provider_settings import GuiProviderSettingsError  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：导入结构化错误类型；如果没有这行，测试只能捕获泛化异常。
    with _CALLBACK_SERVER_LOCK:  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：锁住 registry 后清除同端口旧记录；如果没有这行，并发测试可能读到半更新状态。
        _CALLBACK_SERVERS.pop(callback_port, None)  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：确保当前进程不认为自己拥有该端口；如果没有这行，测试不能模拟其它进程占用。
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blocker:  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：创建一个 IPv4 listener 模拟另一个 bridge；如果没有这行，端口冲突没有真实复现。
        blocker.bind(("127.0.0.1", callback_port))  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：占用和浏览器常用解析一致的 loopback 端口；如果没有这行，OpenHarness 仍可能错误启动。
        blocker.listen(1)  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：进入监听态让 preflight 能发现端口已有接收者；如果没有这行，只 bind 不一定像真实 bridge。
        with pytest.raises(GuiProviderSettingsError) as error:  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：捕获期望的结构化启动失败；如果没有这行，失败路径无法断言错误码。
            start_provider_auth_attempt(tmp_path, "openai", "chatgpt-browser")  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：尝试启动真实 OAuth；如果没有这行，测试不会触发 callback listener。
    assert error.value.code == "openai_oauth_callback_listener_unavailable"  # 新增代码+OpenAIRealOAuthCallbackPortGuardTest：确认错误码能让 GUI 显示可读失败而不是继续等待；如果没有这行，前端无法精准处理端口冲突。
# 新增代码+OpenAIRealOAuthCallbackPortGuardTest：测试段结束，callback 端口外部占用保护合同到此结束；如果没有边界说明，初学者不易看出覆盖的是多 GUI/多 bridge 冲突。
def test_real_oauth_start_rejects_when_localhost_routes_to_another_callback_owner(tmp_path: Path, monkeypatch) -> None:  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：测试段开始，验证 localhost 实际打到其它 listener 时拒绝启动；如果没有这段，两个 bridge 同时存在时 GUI 会拿到必失败的授权链接。
    import http.server  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：导入本机 HTTP server 模拟错误 owner；如果没有这行，测试无法复现 redirect 打到别的进程。
    import threading  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：导入线程启动模拟 server；如果没有这行，错误 owner 无法并行监听。
    callback_port = _free_tcp_port()  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：选择测试专用端口；如果没有这行，测试会和真实 1455 或其它测试冲突。
    class WrongOwnerHandler(http.server.BaseHTTPRequestHandler):  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：类段开始，模拟另一个 bridge 的 callback listener；如果没有这个类，owner 错位没有 HTTP 证据。
        def log_message(self, format: str, *args) -> None:  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：函数段开始，关闭测试 HTTP 默认日志；如果没有这段，测试输出会被无关访问日志污染。
            del format, args  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：显式丢弃未使用参数；如果没有这行，静态检查会看到无意义变量。
        # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：函数段结束，WrongOwnerHandler.log_message 到此结束；如果没有边界说明，初学者不易看出它只管日志。
        def do_GET(self) -> None:  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：函数段开始，返回错误 owner 响应；如果没有这段，probe 无法检测自己打到了谁。
            body = b"wrong-callback-owner"  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：准备不匹配 OpenHarness owner token 的响应；如果没有这行，未来 probe 可能误判通过。
            self.send_response(200)  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：返回 200 模拟“端口可访问但不是本进程”；如果没有这行，测试只覆盖连接失败而非 owner 错位。
            self.send_header("Content-Length", str(len(body)))  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：声明响应长度；如果没有这行，客户端可能等待连接关闭。
            self.end_headers()  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：结束 HTTP 头；如果没有这行，响应体无法发送。
            self.wfile.write(body)  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：写入错误 owner 响应；如果没有这行，probe 没有可比对内容。
        # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：函数段结束，WrongOwnerHandler.do_GET 到此结束；如果没有边界说明，初学者不易看出它模拟的是别的 bridge。
    # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：类段结束，WrongOwnerHandler 到此结束；如果没有边界说明，初学者不易看出它只服务测试。
    wrong_owner_server = http.server.ThreadingHTTPServer(("127.0.0.1", callback_port), WrongOwnerHandler)  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：启动错误 owner 的 IPv4 listener；如果没有这行，localhost 不会被其它进程抢走。
    wrong_owner_thread = threading.Thread(target=wrong_owner_server.serve_forever, daemon=True)  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：准备后台线程服务错误 owner；如果没有这行，server 不会响应 probe。
    wrong_owner_thread.start()  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：启动错误 owner listener；如果没有这行，后续 start 仍可能打到空端口。
    try:  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：保护错误 owner server 清理；如果没有这行，测试失败时端口可能残留。
        _enable_real_openai_oauth_env(monkeypatch)  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：打开真实 OAuth 安全门禁；如果没有这行，start 会退回 mock。
        monkeypatch.setenv("OPENHARNESS_OPENAI_CALLBACK_PORT", str(callback_port))  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：让 redirect_uri 指向错误 owner 端口；如果没有这行，测试不会命中模拟 listener。
        _clear_auth_attempt_registry()  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：清理旧 attempt；如果没有这行，旧 state 可能污染断言。
        from learning_agent.app import gui_provider_auth_attempts as attempts  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：导入 auth-attempt 模块以 monkeypatch server 类；如果没有这行，测试无法模拟“创建成功但路由错位”。
        from learning_agent.app.gui_provider_settings import GuiProviderSettingsError  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：导入结构化错误；如果没有这行，测试无法断言稳定错误码。
        class FakeCallbackServer:  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：类段开始，模拟当前 bridge 以为自己已创建 listener；如果没有这个类，当前实现会在 bind 阶段提前失败。
            owner_token = "fake-current-bridge-owner"  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：提供未来 owner probe 需要的当前 bridge token；如果没有这行，修复后无法比对 owner。
            def __init__(self, server_address, workspace) -> None:  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：函数段开始，保存 workspace 但不真实 bind；如果没有这段，无法模拟 IPv6/IPv4 错位。
                self.server_address = server_address  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：记录被请求的监听地址；如果没有这行，fake server 形状不像真实 server。
                self.workspace = Path(workspace).expanduser().resolve()  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：保存规范化 workspace；如果没有这行，未来逻辑检查 workspace 会失败。
            # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：函数段结束，FakeCallbackServer.__init__ 到此结束；如果没有边界说明，初学者不易看出它不绑定端口。
            def serve_forever(self) -> None:  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：函数段开始，模拟后台 server 主循环；如果没有这段，thread target 不存在。
                return None  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：立即返回避免测试挂起；如果没有这行，fake server 行为不明确。
            # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：函数段结束，FakeCallbackServer.serve_forever 到此结束；如果没有边界说明，初学者不易看出它只是占位。
        # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：类段结束，FakeCallbackServer 到此结束；如果没有边界说明，初学者不易看出它模拟的是当前 bridge。
        monkeypatch.setattr(attempts, "_OpenAIRealOAuthCallbackServer", FakeCallbackServer)  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：让 start 以为当前 bridge listener 创建成功；如果没有这行，测试会停在普通端口占用而不是 owner probe。
        with pytest.raises(GuiProviderSettingsError) as error:  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：期望 start 拒绝错误 owner；如果没有这行，错误路径不会被锁定。
            attempts.start_provider_auth_attempt(tmp_path, "openai", "chatgpt-browser")  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：执行被测启动流程；如果没有这行，owner probe 不会运行。
        assert error.value.code == "openai_oauth_callback_listener_unavailable"  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：确认 GUI 能得到稳定的 listener 错误码；如果没有这行，前端无法给出明确提示。
    finally:  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：无论断言结果都清理错误 owner server；如果没有这行，测试可能遗留端口监听。
        wrong_owner_server.shutdown()  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：停止错误 owner server；如果没有这行，后续测试可能端口冲突。
        wrong_owner_server.server_close()  # 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：关闭错误 owner socket；如果没有这行，端口可能短时间不可复用。
# 新增代码+OpenAIRealOAuthCallbackOwnerProbeTest：测试段结束，localhost owner probe 合同到此结束；如果没有边界说明，初学者不易看出覆盖的是“可访问但不是本进程”。
