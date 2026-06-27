import json  # 新增代码+OpenAIRealOAuthAttemptTest：读取设置和密文文件验证无明文 token；如果没有这行，测试无法做泄漏断言。
import sys  # 新增代码+OpenAIRealOAuthAttemptTest：判断当前平台是否支持 Windows DPAPI；如果没有这行，非 Windows 会误跑 OS 加密测试。
from pathlib import Path  # 新增代码+OpenAIRealOAuthAttemptTest：标注 tmp_path 类型；如果没有这行，路径语义不清楚。
from urllib.parse import parse_qs, urlparse  # 新增代码+OpenAIRealOAuthAttemptTest：解析授权 URL query；如果没有这行，只能做脆弱字符串匹配。

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


def test_real_browser_oauth_start_builds_authorization_url_from_explicit_config(tmp_path: Path, monkeypatch) -> None:  # 新增代码+OpenAIRealOAuthAttemptTest：测试段开始，验证真实授权 URL 参数；如果没有这段，OpenAI 连接可能仍跳 mock 或缺 PKCE。
    _enable_real_openai_oauth_env(monkeypatch)  # 新增代码+OpenAIRealOAuthAttemptTest：打开真实 OAuth 安全门禁；如果没有这行，start 不会生成真实 URL。
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
    assert query["redirect_uri"] == ["http://localhost:1455/auth/callback"]  # 新增代码+OpenAIRealOAuthAttemptTest：确认 redirect_uri 使用本机 callback 端口；如果没有这行，浏览器成功后回不到本机。
    assert query["scope"] == ["openid profile email offline_access"]  # 新增代码+OpenAIRealOAuthAttemptTest：确认 scope 包含 offline_access；如果没有这行，refresh token 可能拿不到。
    assert len(query["code_challenge"][0]) > 20  # 新增代码+OpenAIRealOAuthAttemptTest：确认生成了 PKCE challenge；如果没有这行，URL 可能缺安全参数。
    assert query["code_challenge_method"] == ["S256"]  # 新增代码+OpenAIRealOAuthAttemptTest：确认 PKCE 方法为 S256；如果没有这行，授权端可能拒绝。
    assert query["id_token_add_organizations"] == ["true"]  # 新增代码+OpenAIRealOAuthAttemptTest：确认携带组织信息请求；如果没有这行，账号发现可能缺上下文。
    assert query["codex_cli_simplified_flow"] == ["true"]  # 新增代码+OpenAIRealOAuthAttemptTest：确认使用 Codex 简化 flow 标记；如果没有这行，授权页面可能不是预期体验。
    assert query["originator"] == ["openharness"]  # 新增代码+OpenAIRealOAuthAttemptTest：确认来源标记为 OpenHarness；如果没有这行，诊断会混淆 OpenCode/OpenHarness。
    assert query["state"] == [attempt["oauth_state"]]  # 新增代码+OpenAIRealOAuthAttemptTest：确认 URL state 与 attempt state 一致；如果没有这行，回调无法校验。
    assert attempt["oauth_client_source"] == "observed_opencode_reference"  # 新增代码+OpenAIRealOAuthAttemptTest：确认 client 来源诊断；如果没有这行，用户不知道使用的是观察参考值。
# 新增代码+OpenAIRealOAuthAttemptTest：测试段结束，真实授权 URL 合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


def test_real_oauth_wrong_state_fails_and_correct_state_stores_encrypted_refs_only(tmp_path: Path, monkeypatch) -> None:  # 新增代码+OpenAIRealOAuthAttemptTest：测试段开始，验证 state 校验和加密落盘；如果没有这段，真实 OAuth 回调安全性没有证据。
    if sys.platform != "win32":  # 新增代码+OpenAIRealOAuthAttemptTest：只在 Windows 验证 DPAPI 加密落盘；如果没有这行，非 Windows 环境会因缺 DPAPI 失败。
        pytest.skip("Windows DPAPI CurrentUser is required for real OAuth encrypted token storage.")  # 新增代码+OpenAIRealOAuthAttemptTest：非 Windows 明确跳过；如果没有这行，失败原因会误导。
    _enable_real_openai_oauth_env(monkeypatch)  # 新增代码+OpenAIRealOAuthAttemptTest：打开真实 OAuth 安全门禁；如果没有这行，token 保存会被拒绝。
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
