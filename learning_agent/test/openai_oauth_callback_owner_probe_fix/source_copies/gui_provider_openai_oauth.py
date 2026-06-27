"""OpenHarness Desktop OpenAI ChatGPT OAuth 帮助函数。"""  # 新增代码+OpenAIRealOAuth：说明本模块只负责 OAuth URL、PKCE、token 引用落盘；如果没有这行，维护者容易把它误当 Direct SSE 客户端。

from __future__ import annotations  # 新增代码+OpenAIRealOAuth：启用延迟类型解析；如果没有这行，类型注解在旧解释顺序下更脆弱。

import base64  # 新增代码+OpenAIRealOAuth：生成 PKCE code_challenge；如果没有这行，真实授权 URL 无法满足 S256 要求。
import hashlib  # 新增代码+OpenAIRealOAuth：计算 code_verifier 的 SHA256；如果没有这行，PKCE challenge 无法生成。
import json  # 新增代码+OpenAIRealOAuthExchange：解析 OpenAI token endpoint JSON 响应；如果没有这行，callback 收到 code 后无法变成 token payload。
import os  # 新增代码+OpenAIRealOAuth：读取 callback port 等运行环境；如果没有这行，授权 URL 无法贴近真实本机回调。
import secrets  # 新增代码+OpenAIRealOAuth：生成不可预测 state 和 code_verifier；如果没有这行，OAuth state 容易被猜测。
import time  # 新增代码+OpenAIRealOAuth：记录 OAuth token 保存时间；如果没有这行，设置文件无法排序或审计更新时间。
import urllib.error  # 新增代码+OpenAIRealOAuthExchange：识别 OpenAI token endpoint HTTP/网络错误；如果没有这行，失败只能表现为模糊异常。
import urllib.request  # 新增代码+OpenAIRealOAuthExchange：向 OpenAI token endpoint 发起表单 POST；如果没有这行，授权 code 无法换 token。
from dataclasses import dataclass  # 新增代码+OpenAIRealOAuth：定义真实 OAuth 私有 attempt 数据；如果没有这行，字段会散成 dict。
from pathlib import Path  # 新增代码+OpenAIRealOAuth：标注 workspace 路径类型；如果没有这行，Windows 路径语义不清楚。
from typing import Any, Mapping  # 新增代码+OpenAIRealOAuth：标注 JSON-like token payload 和 env；如果没有这行，输入边界不清楚。
from urllib.parse import urlencode  # 新增代码+OpenAIRealOAuth：安全拼接授权 URL query；如果没有这行，redirect_uri 和 scope 编码容易出错。

from learning_agent.app.gui_provider_openai_auth_config import assert_real_oauth_allowed, build_openai_auth_config  # 新增代码+OpenAIRealOAuth：复用真实 OAuth 安全门禁；如果没有这行，token 保存可能绕过 os_encrypted/experimental/client_id 要求。
from learning_agent.app.gui_provider_secret_store import make_provider_secret_store, safe_secret_ref  # 新增代码+OpenAIRealOAuth：复用 secret store factory 和引用格式；如果没有这行，token 可能明文进入主配置。
from learning_agent.app.gui_provider_settings import GuiProviderSettingsError, load_provider_settings, save_provider_settings  # 新增代码+OpenAIRealOAuth：复用 provider settings 读写；如果没有这行，OAuth 完成后无法更新 OpenAI 连接状态。


OPENAI_AUTHORIZE_URL = "https://auth.openai.com/oauth/authorize"  # 新增代码+OpenAIRealOAuth：定义 OpenAI OAuth 授权入口；如果没有这行，URL 构造会散落到状态机。
OPENAI_TOKEN_URL = "https://auth.openai.com/oauth/token"  # 新增代码+OpenAIRealOAuthExchange：定义 OpenAI OAuth token 端点；如果没有这行，code exchange 会散落硬编码 URL。
OPENCODE_OBSERVED_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"  # 新增代码+OpenAIRealOAuth：标记来自 OpenCode 观察的 client id；如果没有这行，诊断无法区分用户配置和参考值。


@dataclass(frozen=True)  # 新增代码+OpenAIRealOAuth：生成不可变私有 attempt 数据；如果没有这行，状态机可能意外改写 verifier。
class OpenAIRealOAuthAttemptSecret:  # 新增代码+OpenAIRealOAuth：类段开始，保存不返回给 renderer 的真实 OAuth 私有数据；如果没有这个类，code_verifier 可能被放进公开 attempt payload。
    attempt_id: str  # 新增代码+OpenAIRealOAuth：保存 attempt id；如果没有这行，完成回调无法关联 start。
    oauth_state: str  # 新增代码+OpenAIRealOAuth：保存 OAuth state；如果没有这行，回调无法防 CSRF/错配。
    code_verifier: str  # 新增代码+OpenAIRealOAuth：保存 PKCE verifier；如果没有这行，token exchange 无法证明发起方身份。
    redirect_uri: str  # 新增代码+OpenAIRealOAuth：保存本次回调地址；如果没有这行，token exchange 会缺少匹配 redirect_uri。
    client_id: str  # 新增代码+OpenAIRealOAuth：保存显式配置的 client id；如果没有这行，完成阶段无法记录来源诊断。
    oauth_client_source: str  # 新增代码+OpenAIRealOAuth：保存 client id 来源；如果没有这行，诊断无法说明是否使用 OpenCode 观察值。
    # 新增代码+OpenAIRealOAuth：类段结束，OpenAIRealOAuthAttemptSecret 到此结束；如果没有边界说明，初学者不易看出它不能返回给前端。


def detect_openai_oauth_client_source(client_id: str) -> str:  # 新增代码+OpenAIRealOAuth：函数段开始，判断 OAuth client id 来源；如果没有这段，诊断无法区分观察参考和用户配置。
    if str(client_id or "").strip() == OPENCODE_OBSERVED_CLIENT_ID:  # 新增代码+OpenAIRealOAuth：识别 OpenCode 观察参考 client id；如果没有这行，实验来源会被误标为普通配置。
        return "observed_opencode_reference"  # 新增代码+OpenAIRealOAuth：返回观察参考来源；如果没有这行，用户不知道这不是 OpenHarness 自有默认。
    return "operator_configured"  # 新增代码+OpenAIRealOAuth：其它显式 client id 都视为操作者配置；如果没有这行，诊断字段会为空。
# 新增代码+OpenAIRealOAuth：函数段结束，detect_openai_oauth_client_source 到此结束；如果没有边界说明，初学者不易看出它只做诊断分类。


def _base64_urlsafe_no_padding(data: bytes) -> str:  # 新增代码+OpenAIRealOAuth：函数段开始，生成无 padding 的 URL-safe base64；如果没有这段，PKCE challenge 可能带不兼容等号。
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")  # 新增代码+OpenAIRealOAuth：编码并去掉 padding；如果没有这行，授权端可能拒绝 code_challenge。
# 新增代码+OpenAIRealOAuth：函数段结束，_base64_urlsafe_no_padding 到此结束；如果没有边界说明，初学者不易看出它只做编码。


def new_pkce_code_verifier() -> str:  # 新增代码+OpenAIRealOAuth：函数段开始，生成 PKCE code_verifier；如果没有这段，OAuth URL 无法安全交换 code。
    return secrets.token_urlsafe(64)  # 新增代码+OpenAIRealOAuth：生成足够长的随机 verifier；如果没有这行，PKCE 可能太短或可预测。
# 新增代码+OpenAIRealOAuth：函数段结束，new_pkce_code_verifier 到此结束；如果没有边界说明，初学者不易看出它只生成随机字符串。


def pkce_code_challenge(code_verifier: str) -> str:  # 新增代码+OpenAIRealOAuth：函数段开始，从 verifier 生成 S256 challenge；如果没有这段，授权 URL 无法符合 PKCE。
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()  # 新增代码+OpenAIRealOAuth：计算 verifier 的 SHA256；如果没有这行，challenge 与 verifier 不匹配。
    return _base64_urlsafe_no_padding(digest)  # 新增代码+OpenAIRealOAuth：返回 OAuth 需要的 URL-safe challenge；如果没有这行，调用方拿不到参数值。
# 新增代码+OpenAIRealOAuth：函数段结束，pkce_code_challenge 到此结束；如果没有边界说明，初学者不易看出它只做 PKCE 派生。


def openai_callback_port(env: Mapping[str, str] | None = None) -> int:  # 新增代码+OpenAIRealOAuth：函数段开始，读取本机 OAuth callback 端口；如果没有这段，授权 URL 只能硬编码端口。
    source_env = os.environ if env is None else env  # 新增代码+OpenAIRealOAuth：真实运行读 os.environ、测试可注入 env；如果没有这行，测试会污染用户环境。
    raw_port = str(source_env.get("OPENHARNESS_OPENAI_CALLBACK_PORT", "1455") or "1455").strip()  # 新增代码+OpenAIRealOAuth：读取回调端口并默认 1455；如果没有这行，URL 无法兼容 OpenCode 观察到的本机回调形态。
    try:  # 新增代码+OpenAIRealOAuth：保护端口转换；如果没有这行，坏 env 会抛 ValueError。
        port = int(raw_port)  # 新增代码+OpenAIRealOAuth：把端口文本转成整数；如果没有这行，范围校验无法进行。
    except ValueError:  # 新增代码+OpenAIRealOAuth：处理非数字端口；如果没有这行，错误码不稳定。
        raise GuiProviderSettingsError(400, "invalid_openai_callback_port", "OPENHARNESS_OPENAI_CALLBACK_PORT 必须是数字端口。")  # 新增代码+OpenAIRealOAuth：抛出结构化端口错误；如果没有这行，用户不知道 env 写错。
    if port <= 0 or port > 65535:  # 新增代码+OpenAIRealOAuth：校验 TCP 端口范围；如果没有这行，无效端口会进入 redirect_uri。
        raise GuiProviderSettingsError(400, "invalid_openai_callback_port", "OPENHARNESS_OPENAI_CALLBACK_PORT 必须位于 1-65535。")  # 新增代码+OpenAIRealOAuth：抛出范围错误；如果没有这行，授权 URL 会不可用。
    return port  # 新增代码+OpenAIRealOAuth：返回合法端口；如果没有这行，调用方拿不到 callback port。
# 新增代码+OpenAIRealOAuth：函数段结束，openai_callback_port 到此结束；如果没有边界说明，初学者不易看出它只读端口。


def openai_redirect_uri(callback_port: int) -> str:  # 新增代码+OpenAIRealOAuth：函数段开始，生成本机回调 URI；如果没有这段，redirect_uri 会散落硬编码。
    return f"http://localhost:{callback_port}/auth/callback"  # 新增代码+OpenAIRealOAuth：返回 localhost OAuth callback；如果没有这行，授权完成无法回到本机服务。
# 新增代码+OpenAIRealOAuth：函数段结束，openai_redirect_uri 到此结束；如果没有边界说明，初学者不易看出它只拼 URI。


def build_openai_authorization_url(client_id: str, redirect_uri: str, code_verifier: str, oauth_state: str) -> str:  # 新增代码+OpenAIRealOAuth：函数段开始，构造真实 OpenAI 授权 URL；如果没有这段，auth-attempt 仍只能走 mock 链接。
    query = {"response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri, "scope": "openid profile email offline_access", "code_challenge": pkce_code_challenge(code_verifier), "code_challenge_method": "S256", "id_token_add_organizations": "true", "codex_cli_simplified_flow": "true", "originator": "opencode", "state": oauth_state}  # 修改代码+OpenAIRealOAuthOpenCodeParity： 新增代码+OpenAIRealOAuth：准备 OAuth 必需 query 参数；如果没有这行，真实浏览器登录会缺 scope、PKCE 或来源标记。
    return f"{OPENAI_AUTHORIZE_URL}?{urlencode(query)}"  # 新增代码+OpenAIRealOAuth：返回完整授权链接；如果没有这行，前端没有可打开的 URL。
# 新增代码+OpenAIRealOAuth：函数段结束，build_openai_authorization_url 到此结束；如果没有边界说明，初学者不易看出它不发网络请求。


def build_real_openai_oauth_attempt(attempt_id: str, env: Mapping[str, str] | None = None) -> tuple[str, OpenAIRealOAuthAttemptSecret]:  # 新增代码+OpenAIRealOAuth：函数段开始，生成真实 OAuth URL 和私有 attempt 数据；如果没有这段，auth-attempt 无法从 mock 进入真实浏览器 flow。
    config = build_openai_auth_config(env)  # 新增代码+OpenAIRealOAuth：读取并校验真实 OAuth 配置摘要；如果没有这行，client id/门禁状态不统一。
    assert_real_oauth_allowed(config)  # 新增代码+OpenAIRealOAuth：强制真实 OAuth 已满足 os_encrypted、experimental、client_id；如果没有这行，token 保存会不安全。
    callback_port = openai_callback_port(env)  # 新增代码+OpenAIRealOAuth：读取实际本机回调端口；如果没有这行，redirect_uri 不能跟本机 callback 对齐。
    redirect_uri = openai_redirect_uri(callback_port)  # 新增代码+OpenAIRealOAuth：生成本次 redirect_uri；如果没有这行，授权 URL 缺少回调地址。
    code_verifier = new_pkce_code_verifier()  # 新增代码+OpenAIRealOAuth：生成本次 PKCE verifier；如果没有这行，token exchange 缺少安全凭据。
    oauth_state = secrets.token_urlsafe(32)  # 新增代码+OpenAIRealOAuth：生成本次 OAuth state；如果没有这行，回调无法防错配。
    client_source = detect_openai_oauth_client_source(config.client_id)  # 新增代码+OpenAIRealOAuth：记录 client id 来源；如果没有这行，诊断无法说明参考值来源。
    url = build_openai_authorization_url(config.client_id, redirect_uri, code_verifier, oauth_state)  # 新增代码+OpenAIRealOAuth：构造真实浏览器授权 URL；如果没有这行，前端仍然只能打开 mock URL。
    secret = OpenAIRealOAuthAttemptSecret(attempt_id=attempt_id, oauth_state=oauth_state, code_verifier=code_verifier, redirect_uri=redirect_uri, client_id=config.client_id, oauth_client_source=client_source)  # 新增代码+OpenAIRealOAuth：保存不公开的 OAuth 私有字段；如果没有这行，complete 阶段无法校验 state 或交换 code。
    return url, secret  # 新增代码+OpenAIRealOAuth：返回公开 URL 和私有状态；如果没有这行，状态机无法保存 attempt。
# 新增代码+OpenAIRealOAuth：函数段结束，build_real_openai_oauth_attempt 到此结束；如果没有边界说明，初学者不易看出它只准备授权。


def _safe_openai_oauth_error_detail(raw_value: Any) -> str:  # 新增代码+OpenAIRealOAuthExchange：函数段开始，生成不含 token/code 的短错误说明；如果没有这段，token exchange 失败可能把原始响应直接暴露给 GUI。
    raw_text = str(raw_value or "").strip()  # 新增代码+OpenAIRealOAuthExchange：把未知错误内容收敛成字符串；如果没有这行，None 或对象会让错误处理不稳定。
    try:  # 新增代码+OpenAIRealOAuthExchange：尝试解析 OpenAI JSON 错误；如果没有这行，用户只能看到整段原始 JSON。
        parsed = json.loads(raw_text) if raw_text else {}  # 新增代码+OpenAIRealOAuthExchange：解析错误响应；如果没有这行，error_description 无法提取。
    except json.JSONDecodeError:  # 新增代码+OpenAIRealOAuthExchange：处理非 JSON 错误体；如果没有这行，HTML/纯文本错误会导致二次异常。
        parsed = {}  # 新增代码+OpenAIRealOAuthExchange：非 JSON 时使用空对象兜底；如果没有这行，后续 isinstance 判断没有输入。
    if isinstance(parsed, dict):  # 新增代码+OpenAIRealOAuthExchange：只从对象错误体提取字段；如果没有这行，数组或字符串会被误当 dict。
        raw_text = str(parsed.get("error_description", parsed.get("error", raw_text)) or "").strip()  # 新增代码+OpenAIRealOAuthExchange：优先使用 OpenAI 的短错误字段；如果没有这行，错误说明会过长。
    safe_text = raw_text.replace("\r", " ").replace("\n", " ").strip()  # 新增代码+OpenAIRealOAuthExchange：移除换行避免污染 GUI/日志；如果没有这行，错误显示可能破坏布局。
    return (safe_text[:300] if safe_text else "unknown_error")  # 新增代码+OpenAIRealOAuthExchange：限制长度并兜底；如果没有这行，错误响应可能过长或为空。
# 新增代码+OpenAIRealOAuthExchange：函数段结束，_safe_openai_oauth_error_detail 到此结束；如果没有边界说明，初学者不易看出它只做安全错误摘要。


def exchange_openai_oauth_code_for_tokens(oauth_secret: OpenAIRealOAuthAttemptSecret, code: str, timeout_seconds: int = 30) -> dict[str, Any]:  # 新增代码+OpenAIRealOAuthExchange：函数段开始，用 callback code 换 OpenAI OAuth token；如果没有这段，真实网页登录成功后仍不能连接模型。
    clean_code = str(code or "").strip()  # 新增代码+OpenAIRealOAuthExchange：清理 authorization code；如果没有这行，空白 code 可能被发给 OpenAI。
    if not clean_code:  # 新增代码+OpenAIRealOAuthExchange：拒绝缺 code 的 callback；如果没有这行，错误会推迟到官方 token endpoint。
        raise GuiProviderSettingsError(400, "openai_oauth_code_missing", "OpenAI OAuth callback 缺少 authorization code。")  # 新增代码+OpenAIRealOAuthExchange：返回结构化缺 code 错误；如果没有这行，前端无法显示明确原因。
    form_body = urlencode({"grant_type": "authorization_code", "code": clean_code, "redirect_uri": oauth_secret.redirect_uri, "client_id": oauth_secret.client_id, "code_verifier": oauth_secret.code_verifier}).encode("utf-8")  # 新增代码+OpenAIRealOAuthExchange：构造 token endpoint 要求的表单体；如果没有这行，PKCE 授权码无法换 token。
    request = urllib.request.Request(OPENAI_TOKEN_URL, data=form_body, headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}, method="POST")  # 新增代码+OpenAIRealOAuthExchange：构造标准库 POST 请求；如果没有这行，无法控制 headers 和 method。
    try:  # 新增代码+OpenAIRealOAuthExchange：保护官方 token 请求；如果没有这行，网络/HTTP 错误会变成不稳定异常。
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # 新增代码+OpenAIRealOAuthExchange：发送 token exchange 请求并设置超时；如果没有这行，官方无响应会卡住 GUI。
            response_text = response.read().decode("utf-8")  # 新增代码+OpenAIRealOAuthExchange：读取 JSON 响应文本；如果没有这行，无法解析 token payload。
    except urllib.error.HTTPError as error:  # 新增代码+OpenAIRealOAuthExchange：处理 OpenAI 返回的 4xx/5xx；如果没有这行，用户只能看到 Python HTTPError。
        error_text = error.read().decode("utf-8", errors="replace")  # 新增代码+OpenAIRealOAuthExchange：读取官方错误体并容忍编码问题；如果没有这行，错误原因会丢失。
        detail = _safe_openai_oauth_error_detail(error_text)  # 新增代码+OpenAIRealOAuthExchange：提取安全短错误；如果没有这行，GUI 可能暴露过长原始响应。
        raise GuiProviderSettingsError(400, "openai_oauth_token_exchange_failed", f"OpenAI OAuth token exchange failed: {detail}") from error  # 新增代码+OpenAIRealOAuthExchange：抛出结构化 exchange 错误；如果没有这行，callback 无法把失败传给等待页。
    except (OSError, TimeoutError, urllib.error.URLError) as error:  # 新增代码+OpenAIRealOAuthExchange：处理网络、代理或超时错误；如果没有这行，断网会表现为 500。
        detail = _safe_openai_oauth_error_detail(error)  # 新增代码+OpenAIRealOAuthExchange：生成网络错误摘要；如果没有这行，错误文案可能带底层噪声。
        raise GuiProviderSettingsError(502, "openai_oauth_token_exchange_network_failed", f"OpenAI OAuth token exchange network failed: {detail}") from error  # 新增代码+OpenAIRealOAuthExchange：抛出结构化网络错误；如果没有这行，用户不知道是联网失败。
    try:  # 新增代码+OpenAIRealOAuthExchange：保护 JSON 解析；如果没有这行，坏响应会抛底层 JSONDecodeError。
        payload = json.loads(response_text)  # 新增代码+OpenAIRealOAuthExchange：解析 token payload；如果没有这行，后续保存拿不到字段。
    except json.JSONDecodeError as error:  # 新增代码+OpenAIRealOAuthExchange：处理非 JSON 成功响应；如果没有这行，用户不知道官方响应格式异常。
        raise GuiProviderSettingsError(502, "openai_oauth_token_exchange_bad_json", "OpenAI OAuth token endpoint 返回了非 JSON 响应。") from error  # 新增代码+OpenAIRealOAuthExchange：抛出结构化坏 JSON 错误；如果没有这行，callback 失败不可读。
    if not isinstance(payload, dict):  # 新增代码+OpenAIRealOAuthExchange：要求 token payload 是对象；如果没有这行，数组/字符串会污染存储层。
        raise GuiProviderSettingsError(502, "openai_oauth_token_exchange_bad_payload", "OpenAI OAuth token endpoint 返回了无效 payload。")  # 新增代码+OpenAIRealOAuthExchange：抛出结构化 payload 错误；如果没有这行，后续 `.get` 可能崩溃。
    return payload  # 新增代码+OpenAIRealOAuthExchange：返回解析后的 token payload；如果没有这行，callback 完成没有 token 输入。
# 新增代码+OpenAIRealOAuthExchange：函数段结束，exchange_openai_oauth_code_for_tokens 到此结束；如果没有边界说明，初学者不易看出它只负责 code exchange。


def redact_openai_account_label(value: Any) -> str:  # 新增代码+OpenAIRealOAuth：函数段开始，生成安全账号标签；如果没有这段，真实邮箱可能进入状态文件或 UI。
    text = str(value or "").strip()  # 新增代码+OpenAIRealOAuth：把未知输入收敛成字符串；如果没有这行，None 或数字会导致后续判断不稳定。
    if "@" in text:  # 新增代码+OpenAIRealOAuth：识别邮箱样式账号；如果没有这行，邮箱会被完整保存。
        local, _, domain = text.partition("@")  # 新增代码+OpenAIRealOAuth：拆分邮箱本地名和域名；如果没有这行，无法做可读但安全的脱敏。
        safe_local = f"{local[:2]}***" if len(local) >= 2 else "***"  # 新增代码+OpenAIRealOAuth：只保留少量本地名前缀；如果没有这行，账号标签可能泄露完整邮箱。
        safe_domain = domain.split(".")[0][:2] + "***" if domain else "***"  # 新增代码+OpenAIRealOAuth：只保留少量域名前缀；如果没有这行，域名可能泄露个人信息。
        return f"{safe_local}@{safe_domain}"  # 新增代码+OpenAIRealOAuth：返回脱敏邮箱标签；如果没有这行，UI 无法提示已连接账号。
    return text[:4] + "…" if len(text) > 8 else text  # 新增代码+OpenAIRealOAuth：非邮箱长标签也截断；如果没有这行，任意账号字符串可能过长或敏感。
# 新增代码+OpenAIRealOAuth：函数段结束，redact_openai_account_label 到此结束；如果没有边界说明，初学者不易看出它只做显示脱敏。


def discover_openai_account(token_payload: Mapping[str, Any]) -> dict[str, str]:  # 新增代码+OpenAIRealOAuth：函数段开始，从 token 响应中提取安全账号摘要；如果没有这段，runtime state 没有账号选择状态。
    accounts = token_payload.get("accounts", []) if isinstance(token_payload.get("accounts", []), list) else []  # 新增代码+OpenAIRealOAuth：读取可能的多账号列表；如果没有这行，多账号无法自动选择。
    first_account = accounts[0] if accounts and isinstance(accounts[0], dict) else {}  # 新增代码+OpenAIRealOAuth：选择第一个可用账号；如果没有这行，多账号场景没有确定结果。
    account_id = str(first_account.get("id", token_payload.get("account_id", ""))).strip() if isinstance(first_account, dict) else str(token_payload.get("account_id", "")).strip()  # 新增代码+OpenAIRealOAuth：读取安全账号 id；如果没有这行，状态无法关联账号。
    raw_label = first_account.get("label", first_account.get("email", token_payload.get("account_label", token_payload.get("email", account_id)))) if isinstance(first_account, dict) else token_payload.get("account_label", account_id)  # 新增代码+OpenAIRealOAuth：选择最可读但需脱敏的账号标签；如果没有这行，UI 只能显示空白。
    status = "auto_selected_first" if len(accounts) > 1 else ("selected" if account_id else "unknown")  # 新增代码+OpenAIRealOAuth：记录账号选择状态；如果没有这行，多账号自动选择没有审计字段。
    return {"account_id": account_id, "account_label": redact_openai_account_label(raw_label), "account_selection_status": status}  # 新增代码+OpenAIRealOAuth：返回不含完整邮箱/token 的账号摘要；如果没有这行，调用方会重复实现。
# 新增代码+OpenAIRealOAuth：函数段结束，discover_openai_account 到此结束；如果没有边界说明，初学者不易看出它不发网络请求。


def store_openai_oauth_token_response(workspace: str | Path, token_payload: Mapping[str, Any], auth_method_id: str, oauth_client_source: str) -> dict[str, Any]:  # 新增代码+OpenAIRealOAuth：函数段开始，把真实 OAuth token 保存成 secret_refs；如果没有这段，正确回调无法形成可用连接状态。
    config = build_openai_auth_config()  # 新增代码+OpenAIRealOAuth：读取当前真实 OAuth 门禁；如果没有这行，保存 token 可能绕过安全环境。
    assert_real_oauth_allowed(config)  # 新增代码+OpenAIRealOAuth：确保真实 token 只能写入 OS 加密 store；如果没有这行，refresh token 可能进入 dev JSON。
    secret_store = make_provider_secret_store(workspace)  # 新增代码+OpenAIRealOAuth：创建当前安全 secret store；如果没有这行，token 没有安全存储位置。
    secret_refs: dict[str, str] = {}  # 新增代码+OpenAIRealOAuth：准备主配置可保存的 token 引用组；如果没有这行，settings 只能保存明文 token。
    for token_name in ("access_token", "refresh_token", "id_token"):  # 新增代码+OpenAIRealOAuth：遍历需要保存的 OAuth token；如果没有这行，refresh/id token 可能漏存或漏删。
        token_value = str(token_payload.get(token_name, "") or "")  # 新增代码+OpenAIRealOAuth：读取 token 值并收敛为字符串；如果没有这行，None 会写入异常类型。
        if token_value:  # 新增代码+OpenAIRealOAuth：只保存存在的 token；如果没有这行，空值会产生无意义密文。
            secret_refs[token_name] = secret_store.set_secret(safe_secret_ref("openai", token_name), token_value)  # 新增代码+OpenAIRealOAuth：加密保存 token 并记录引用；如果没有这行，Direct SSE 无法认证。
    if "access_token" not in secret_refs:  # 新增代码+OpenAIRealOAuth：要求至少有 access token；如果没有这行，连接会显示成功但无法发请求。
        raise GuiProviderSettingsError(400, "missing_openai_access_token", "OpenAI OAuth token response 缺少 access_token。")  # 新增代码+OpenAIRealOAuth：抛出结构化缺 token 错误；如果没有这行，后续错误会更晚更模糊。
    account = discover_openai_account(token_payload)  # 新增代码+OpenAIRealOAuth：提取安全账号摘要；如果没有这行，runtime state 无法展示账号。
    settings = load_provider_settings(workspace)  # 新增代码+OpenAIRealOAuth：读取 provider settings；如果没有这行，保存 token 会覆盖已有配置。
    auth = settings.setdefault("auth", {})  # 新增代码+OpenAIRealOAuth：获取 auth 区块；如果没有这行，无法记录 OpenAI 已连接。
    auth["openai"] = {"type": "oauth_real", "auth_method_id": auth_method_id, "secret_refs": secret_refs, "account_id": account["account_id"], "account_label": account["account_label"], "account_selection_status": account["account_selection_status"], "oauth_client_source": oauth_client_source, "updated_at": time.time()}  # 新增代码+OpenAIRealOAuth：主配置只保存引用和安全摘要；如果没有这行，重启后无法识别真实 OAuth 连接。
    settings["selected_openai_account_id"] = account["account_id"]  # 新增代码+OpenAIRealOAuth：保存当前 OpenAI 账号 id；如果没有这行，runtime state 无法关联账号。
    settings["selected_openai_account_label"] = account["account_label"]  # 新增代码+OpenAIRealOAuth：保存脱敏账号标签；如果没有这行，UI 无法提示已连接账号。
    settings["selected_openai_model_id"] = str(settings.get("selected_openai_model_id", "") or settings.get("default_model_id", ""))  # 新增代码+OpenAIRealOAuth：保留已有模型选择；如果没有这行，连接完成后底部模型可能丢失。
    settings["default_provider_id"] = "openai"  # 新增代码+OpenAIRealOAuth：把默认 provider 指向 OpenAI；如果没有这行，连接完成后 composer 仍可能没有 provider。
    save_provider_settings(workspace, settings)  # 新增代码+OpenAIRealOAuth：保存不含明文 token 的 provider settings；如果没有这行，连接状态只在内存存在。
    return settings  # 新增代码+OpenAIRealOAuth：返回保存后的 settings；如果没有这行，调用方无法继续构造状态。
# 新增代码+OpenAIRealOAuth：函数段结束，store_openai_oauth_token_response 到此结束；如果没有边界说明，初学者不易看出它负责安全落盘。
