"""OpenHarness Desktop experimental OpenAI direct OAuth helpers."""  # 新增代码+DirectOAuthFlow：说明本模块只承载 V1C 实验 direct OAuth helper；如果没有这行代码，维护者容易把它误当稳定认证入口。

from __future__ import annotations  # 新增代码+DirectOAuthFlow：启用延迟类型注解解析；如果没有这行代码，类内类型引用在旧解释器上更脆弱。

import base64  # 新增代码+DirectOAuthFlow：用于生成 PKCE challenge 的 base64url 文本；如果没有这行代码，授权 URL 无法满足 PKCE。
import hashlib  # 新增代码+DirectOAuthFlow：用于对 verifier 做 SHA-256；如果没有这行代码，PKCE S256 challenge 无法生成。
import html  # 新增代码+DirectOAuthFlow：用于转义 callback 页面文本；如果没有这行代码，错误消息可能污染浏览器页面。
import json  # 新增代码+DirectOAuthFlow：解析 token endpoint 返回的 JSON；如果没有这行代码，授权码无法换成结构化 token。
import secrets  # 新增代码+DirectOAuthFlow：用于生成高熵 verifier/state；如果没有这行代码，OAuth CSRF/PKCE 安全性会下降。
import socket  # 新增代码+DirectOAuthFlow：用于 localhost callback 端口预检；如果没有这行代码，端口冲突只能到启动 server 时才暴露。
import time  # 新增代码+DirectOAuthFlow：用于记录 attempt 时间和过期时间；如果没有这行代码，callback 状态无法审计。
import urllib.parse  # 新增代码+DirectOAuthFlow：用于构造授权 URL query；如果没有这行代码，参数编码容易出错。
import urllib.error  # 新增代码+DirectOAuthFlow：识别 token exchange HTTP 错误；如果没有这行代码，401/500 会变成模糊异常。
import urllib.request  # 新增代码+DirectOAuthFlow：向 OpenAI token endpoint 发送标准库 POST；如果没有这行代码，direct OAuth 无法换取 token。
from typing import Any, Callable  # 新增代码+DirectOAuthFlow：用于标注 token exchanger 和 JSON-like payload；如果没有这行代码，注入边界不清楚。

from learning_agent.app.gui_provider_oauth_token_store import GuiProviderOAuthTokenStore, default_oauth_token_store  # 新增代码+DirectOAuthFlow：复用安全 token store；如果没有这行代码，callback 成功后没有安全落盘位置。


OPENAI_AUTH_ISSUER = "https://auth.openai.com"  # 新增代码+DirectOAuthFlow：集中定义 OpenAI 授权服务器；如果没有这行代码，授权 URL host 会散落到调用方。
OPENAI_TOKEN_ENDPOINT = f"{OPENAI_AUTH_ISSUER}/oauth/token"  # 新增代码+DirectOAuthFlow：集中定义 token exchange endpoint；如果没有这行代码，网络层不知道向哪里换 token。
DEFAULT_CALLBACK_HOST = "127.0.0.1"  # 新增代码+DirectOAuthFlow：callback server 只绑定本机回环地址；如果没有这行代码，局域网设备可能访问 callback。
DEFAULT_CALLBACK_PORT = 1455  # 新增代码+DirectOAuthFlow：沿用 OpenCode/Codex 可观察 callback 端口；如果没有这行代码，浏览器 redirect_uri 没有稳定默认值。
DEFAULT_CALLBACK_PATH = "/auth/callback"  # 新增代码+DirectOAuthFlow：集中定义 callback 路径；如果没有这行代码，URL 和 server 路由可能不一致。
DEFAULT_OAUTH_TTL_SECONDS = 600.0  # 新增代码+DirectOAuthFlow：定义授权尝试过期时间；如果没有这行代码，pending attempt 可能永久有效。


TokenExchanger = Callable[..., dict[str, object]]  # 新增代码+DirectOAuthFlow：抽象 code-to-token 网络函数；如果没有这行代码，测试无法注入 fake token exchange。


class OpenAIProviderOAuthError(Exception):  # 新增代码+DirectOAuthFlow：类段开始，承载 direct OAuth 结构化错误；如果没有这个类，端口和 callback 失败只能抛模糊异常。
    def __init__(self, code: str, message: str) -> None:  # 新增代码+DirectOAuthFlow：函数段开始，保存错误码和说明；如果没有这段，前端无法机器读取失败原因。
        super().__init__(message)  # 新增代码+DirectOAuthFlow：把说明交给 Exception；如果没有这行代码，日志里的异常文本会为空。
        self.code = code  # 新增代码+DirectOAuthFlow：保存机器可读错误码；如果没有这行代码，调用方无法区分端口冲突和 token 交换失败。
        self.message = message  # 新增代码+DirectOAuthFlow：保存可读说明；如果没有这行代码，调用方只能依赖 str(error)。
    # 新增代码+DirectOAuthFlow：函数段结束，OpenAIProviderOAuthError.__init__ 到此结束；如果没有边界说明，用户不容易看出错误字段范围。
# 新增代码+DirectOAuthFlow：类段结束，OpenAIProviderOAuthError 到此结束；如果没有边界说明，用户不容易看出它只负责传递错误。


def generate_pkce_pair() -> dict[str, str]:  # 新增代码+DirectOAuthFlow：函数段开始，生成 PKCE verifier/challenge；如果没有这段，direct OAuth 无法安全使用授权码模式。
    verifier = secrets.token_urlsafe(96)[:96]  # 新增代码+DirectOAuthFlow：生成 URL-safe 高熵 verifier；如果没有这行代码，PKCE verifier 可能过短或不可用于 URL。
    digest = hashlib.sha256(verifier.encode("ascii")).digest()  # 新增代码+DirectOAuthFlow：对 verifier 做 SHA-256；如果没有这行代码，S256 challenge 无法计算。
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")  # 新增代码+DirectOAuthFlow：生成去 padding 的 base64url challenge；如果没有这行代码，授权服务器可能拒绝 PKCE 参数。
    return {"verifier": verifier, "challenge": challenge}  # 新增代码+DirectOAuthFlow：返回 verifier/challenge；如果没有这行代码，调用方拿不到 PKCE 对。
# 新增代码+DirectOAuthFlow：函数段结束，generate_pkce_pair 到此结束；如果没有边界说明，用户不容易看出 verifier 只能留在后端。


def generate_state() -> str:  # 新增代码+DirectOAuthFlow：函数段开始，生成 OAuth state；如果没有这段，callback 无法做 CSRF 校验。
    return secrets.token_urlsafe(32)  # 新增代码+DirectOAuthFlow：返回 URL-safe 随机 state；如果没有这行代码，state 可能固定或低熵。
# 新增代码+DirectOAuthFlow：函数段结束，generate_state 到此结束；如果没有边界说明，用户不容易看出它只负责随机防护。


def callback_redirect_uri(host: str = "localhost", port: int = DEFAULT_CALLBACK_PORT, path: str = DEFAULT_CALLBACK_PATH) -> str:  # 新增代码+DirectOAuthFlow：函数段开始，构造浏览器 redirect_uri；如果没有这段，URL 和 callback server 容易不一致。
    return f"http://{host}:{int(port)}{path}"  # 新增代码+DirectOAuthFlow：返回 localhost callback URL；如果没有这行代码，授权服务器不知道回调到哪里。
# 新增代码+DirectOAuthFlow：函数段结束，callback_redirect_uri 到此结束；如果没有边界说明，用户不容易看出 redirect_uri 是本地回环。


def build_authorize_url(client_id: str, redirect_uri: str, code_challenge: str, state: str, originator: str = "openharness") -> str:  # 新增代码+DirectOAuthFlow：函数段开始，构造 OpenAI 授权 URL；如果没有这段，GUI 无法打开浏览器登录。
    clean_client_id = str(client_id or "").strip()  # 新增代码+DirectOAuthFlow：清理 client id；如果没有这行代码，空白值可能生成坏 URL。
    if not clean_client_id:  # 新增代码+DirectOAuthFlow：拒绝缺失 client id；如果没有这行代码，OpenHarness 可能偷偷回退到不属于自己的默认 id。
        raise OpenAIProviderOAuthError("oauth_client_id_required", "OpenAI direct OAuth requires an explicit OpenHarness client_id.")  # 新增代码+DirectOAuthFlow：抛出缺 client id 错误；如果没有这行代码，授权 URL 会不可用。
    params = urllib.parse.urlencode(  # 新增代码+DirectOAuthFlow：开始编码 OAuth query 参数；如果没有这行代码，空格和特殊字符会破坏 URL。
        {  # 新增代码+DirectOAuthFlow：授权参数字典开始；如果没有这行代码，query 参数没有容器。
            "response_type": "code",  # 新增代码+DirectOAuthFlow：使用授权码模式；如果没有这行代码，token exchange 没有 code。
            "client_id": clean_client_id,  # 新增代码+DirectOAuthFlow：使用显式配置的 OpenHarness client id；如果没有这行代码，授权服务器无法识别应用。
            "redirect_uri": redirect_uri,  # 新增代码+DirectOAuthFlow：告诉授权服务器回调地址；如果没有这行代码，本地 server 收不到 code。
            "scope": "openid profile email offline_access",  # 新增代码+DirectOAuthFlow：请求用户资料和 refresh token；如果没有这行代码，后端无法长期刷新。
            "code_challenge": code_challenge,  # 新增代码+DirectOAuthFlow：传入 PKCE challenge；如果没有这行代码，授权码无法安全交换。
            "code_challenge_method": "S256",  # 新增代码+DirectOAuthFlow：声明 PKCE S256；如果没有这行代码，授权服务器可能按 plain 处理或拒绝。
            "id_token_add_organizations": "true",  # 新增代码+DirectOAuthFlow：请求 id_token 附带组织信息；如果没有这行代码，account id 推导可能不完整。
            "codex_cli_simplified_flow": "true",  # 新增代码+DirectOAuthFlow：沿用 Codex 简化登录体验；如果没有这行代码，浏览器可能出现非 Codex 授权路径。
            "state": state,  # 新增代码+DirectOAuthFlow：传入 CSRF state；如果没有这行代码，callback 无法校验来源。
            "originator": originator,  # 新增代码+DirectOAuthFlow：标记 OpenHarness 发起；如果没有这行代码，审计无法区分来源。
        }  # 新增代码+DirectOAuthFlow：授权参数字典结束；如果没有这行代码，Python 语法不完整。
    )  # 新增代码+DirectOAuthFlow：query 编码结束；如果没有这行代码，params 不会生成。
    return f"{OPENAI_AUTH_ISSUER}/oauth/authorize?{params}"  # 新增代码+DirectOAuthFlow：返回完整授权 URL；如果没有这行代码，浏览器没有目标地址。
# 新增代码+DirectOAuthFlow：函数段结束，build_authorize_url 到此结束；如果没有边界说明，用户不容易看出这里不保存 token。


def preflight_oauth_port(host: str = DEFAULT_CALLBACK_HOST, port: int = DEFAULT_CALLBACK_PORT) -> None:  # 新增代码+DirectOAuthFlow：函数段开始，预检 callback 端口是否可绑定；如果没有这段，用户登录后才会发现 callback 失败。
    probe_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 新增代码+DirectOAuthFlow：创建 TCP socket；如果没有这行代码，无法检查端口占用。
    try:  # 新增代码+DirectOAuthFlow：确保 socket 最终关闭；如果没有这行代码，预检自身可能泄漏端口。
        probe_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 新增代码+DirectOAuthFlow：允许快速复用测试端口；如果没有这行代码，Windows 上短暂 TIME_WAIT 更容易误报。
        probe_socket.bind((host, int(port)))  # 新增代码+DirectOAuthFlow：尝试绑定目标端口；如果没有这行代码，端口冲突无法提前发现。
    except OSError as error:  # 新增代码+DirectOAuthFlow：捕获端口占用或权限问题；如果没有这行代码，底层异常会直接冒泡给 GUI。
        raise OpenAIProviderOAuthError("oauth_port_in_use", f"OAuth callback port {port} is not available on {host}.") from error  # 新增代码+DirectOAuthFlow：抛出结构化端口错误；如果没有这行代码，前端无法提示换端口或关闭占用进程。
    finally:  # 新增代码+DirectOAuthFlow：无论成功失败都关闭 socket；如果没有这行代码，预检会把端口占住。
        probe_socket.close()  # 新增代码+DirectOAuthFlow：释放 socket；如果没有这行代码，后续真正 callback server 可能绑定失败。
# 新增代码+DirectOAuthFlow：函数段结束，preflight_oauth_port 到此结束；如果没有边界说明，用户不容易看出它不启动 server。


def _html_page(title: str, body: str) -> str:  # 新增代码+DirectOAuthFlow：函数段开始，生成 callback 浏览器页面；如果没有这段，成功/失败页面会重复拼 HTML。
    safe_title = html.escape(title)  # 新增代码+DirectOAuthFlow：转义标题；如果没有这行代码，错误文本可能注入页面。
    safe_body = html.escape(body)  # 新增代码+DirectOAuthFlow：转义正文；如果没有这行代码，远端错误文本可能注入页面。
    return f"<!doctype html><html><head><meta charset=\"utf-8\"><title>{safe_title}</title></head><body style=\"font-family: system-ui; background:#111; color:#f5f5f5; display:grid; min-height:100vh; place-items:center;\"><main><h1>{safe_title}</h1><p>{safe_body}</p></main></body></html>"  # 新增代码+DirectOAuthFlow：返回简洁可见页面；如果没有这行代码，浏览器 callback 没有用户反馈。
# 新增代码+DirectOAuthFlow：函数段结束，_html_page 到此结束；如果没有边界说明，用户不容易看出页面不含 token。


class OpenAIProviderOAuthAttempt:  # 新增代码+DirectOAuthFlow：类段开始，管理一次 direct OAuth 授权尝试；如果没有这个类，callback/state/token 保存会散落在 bridge 路由里。
    def __init__(self, client_id: str, token_exchanger: TokenExchanger | None = None, token_store: GuiProviderOAuthTokenStore | None = None, redirect_uri: str | None = None, ttl_seconds: float = DEFAULT_OAUTH_TTL_SECONDS) -> None:  # 新增代码+DirectOAuthFlow：函数段开始，初始化一次授权尝试；如果没有这段，attempt 无法持有 PKCE/state。
        self.client_id = str(client_id or "").strip()  # 新增代码+DirectOAuthFlow：保存显式 client id；如果没有这行代码，授权 URL 无法构造。
        self.pkce = generate_pkce_pair()  # 新增代码+DirectOAuthFlow：生成本次 PKCE；如果没有这行代码，code exchange 无法校验 verifier。
        self.state = generate_state()  # 新增代码+DirectOAuthFlow：生成本次 state；如果没有这行代码，callback 无法防 CSRF。
        self.redirect_uri = redirect_uri or callback_redirect_uri()  # 新增代码+DirectOAuthFlow：保存 redirect_uri；如果没有这行代码，授权 URL 和 token exchange 无法共享回调地址。
        self.token_exchanger = token_exchanger or exchange_code_for_tokens  # 新增代码+DirectOAuthFlow：保存 token exchange 函数；如果没有这行代码，callback 成功后无法换 token。
        self.token_store = token_store or default_oauth_token_store()  # 新增代码+DirectOAuthFlow：保存安全 token store；如果没有这行代码，成功 token 没有落盘位置。
        self.created_at = time.time()  # 新增代码+DirectOAuthFlow：记录创建时间；如果没有这行代码，attempt 无法审计。
        self.expires_at = self.created_at + float(ttl_seconds)  # 新增代码+DirectOAuthFlow：记录过期时间；如果没有这行代码，用户关闭或超时后 callback 仍可能有效。
        self.status = "pending"  # 新增代码+DirectOAuthFlow：初始状态为 pending；如果没有这行代码，前端无法轮询等待。
        self.error_code = ""  # 新增代码+DirectOAuthFlow：初始化错误码为空；如果没有这行代码，成功路径可能残留旧错误。
        self.message = ""  # 新增代码+DirectOAuthFlow：初始化用户消息为空；如果没有这行代码，状态摘要没有可读说明字段。
    # 新增代码+DirectOAuthFlow：函数段结束，__init__ 到此结束；如果没有边界说明，用户不容易看出初始化不打开浏览器。

    @property  # 新增代码+DirectOAuthFlow：属性段开始，提供本次授权 URL；如果没有这行代码，调用方需要手动拼 PKCE/state。
    def authorize_url(self) -> str:  # 新增代码+DirectOAuthFlow：函数段开始，返回本次 attempt 的授权 URL；如果没有这段，GUI 无法打开正确登录页。
        return build_authorize_url(client_id=self.client_id, redirect_uri=self.redirect_uri, code_challenge=self.pkce["challenge"], state=self.state)  # 新增代码+DirectOAuthFlow：用本次 state/PKCE 构造 URL；如果没有这行代码，callback 无法匹配 attempt。
    # 新增代码+DirectOAuthFlow：函数段结束，authorize_url 到此结束；如果没有边界说明，用户不容易看出 URL 不含 verifier。

    def cancel(self) -> None:  # 新增代码+DirectOAuthFlow：函数段开始，取消本次授权尝试；如果没有这段，关闭 dialog 后 callback 仍可写 token。
        if self.status == "pending":  # 新增代码+DirectOAuthFlow：只取消等待中的 attempt；如果没有这行代码，complete/failed 状态可能被覆盖。
            self.status = "expired"  # 新增代码+DirectOAuthFlow：把取消收敛为 expired；如果没有这行代码，状态 enum 会多出不必要分支。
            self.message = "cancelled_by_user"  # 新增代码+DirectOAuthFlow：记录取消原因；如果没有这行代码，用户不知道为什么 callback 过期。
    # 新增代码+DirectOAuthFlow：函数段结束，cancel 到此结束；如果没有边界说明，用户不容易看出取消不会删除已完成 token。

    def _expire_if_needed(self) -> None:  # 新增代码+DirectOAuthFlow：函数段开始，按时间自动过期 pending attempt；如果没有这段，授权尝试会永久有效。
        if self.status == "pending" and time.time() >= self.expires_at:  # 新增代码+DirectOAuthFlow：只过期等待中的超时 attempt；如果没有这行代码，complete/failed 可能被误改。
            self.status = "expired"  # 新增代码+DirectOAuthFlow：设置过期状态；如果没有这行代码，GUI 会继续等待。
            self.message = "expired"  # 新增代码+DirectOAuthFlow：记录过期原因；如果没有这行代码，用户不知道需要重新开始。
    # 新增代码+DirectOAuthFlow：函数段结束，_expire_if_needed 到此结束；如果没有边界说明，用户不容易看出它只处理 pending。

    def _normalized_tokens(self, raw_tokens: dict[str, object]) -> dict[str, object]:  # 新增代码+DirectOAuthFlow：函数段开始，规范化 token exchange 响应；如果没有这段，store 可能缺 expires_at。
        tokens = dict(raw_tokens)  # 新增代码+DirectOAuthFlow：复制 token 响应；如果没有这行代码，后续修改会污染测试 fake 返回值。
        if "expires_at" not in tokens and "expires_in" in tokens:  # 新增代码+DirectOAuthFlow：兼容 OAuth expires_in 响应；如果没有这行代码，真实 token 记录可能缺过期时间。
            tokens["expires_at"] = int(time.time() * 1000) + int(tokens.get("expires_in") or 0) * 1000  # 新增代码+DirectOAuthFlow：把秒级 expires_in 转成毫秒时间戳；如果没有这行代码，刷新策略无法判断过期。
        return tokens  # 新增代码+DirectOAuthFlow：返回规范化 token 字典；如果没有这行代码，调用方拿不到结果。
    # 新增代码+DirectOAuthFlow：函数段结束，_normalized_tokens 到此结束；如果没有边界说明，用户不容易看出它仍然是后端 raw token。

    def handle_callback(self, query: dict[str, str]) -> str:  # 新增代码+DirectOAuthFlow：函数段开始，处理 localhost callback 参数；如果没有这段，浏览器授权完成后无法保存登录。
        self._expire_if_needed()  # 新增代码+DirectOAuthFlow：先收敛超时状态；如果没有这行代码，过期 callback 可能仍被接受。
        if self.status == "complete":  # 新增代码+DirectOAuthFlow：重复 callback 已完成时幂等返回成功页；如果没有这行代码，刷新成功页会重复 exchange。
            return _html_page("Authorization Successful", "You can close this window and return to OpenHarness.")  # 新增代码+DirectOAuthFlow：返回安全成功页；如果没有这行代码，用户刷新页面可能看到误导失败。
        if self.status == "expired":  # 新增代码+DirectOAuthFlow：已取消或超时的 callback 不再保存 token；如果没有这行代码，取消后浏览器回调仍会登录。
            return _html_page("Authorization Expired", "This authorization attempt is no longer active. Return to OpenHarness and start again.")  # 新增代码+DirectOAuthFlow：返回过期页；如果没有这行代码，用户不知道 callback 为何无效。
        if str(query.get("state", "")) != self.state:  # 新增代码+DirectOAuthFlow：校验 OAuth state；如果没有这行代码，CSRF callback 可能被接受。
            self.status = "failed"  # 新增代码+DirectOAuthFlow：标记失败；如果没有这行代码，GUI 可能继续 pending。
            self.error_code = "oauth_state_mismatch"  # 新增代码+DirectOAuthFlow：保存稳定错误码；如果没有这行代码，前端无法解释失败原因。
            self.message = "OAuth state did not match."  # 新增代码+DirectOAuthFlow：保存可读失败说明；如果没有这行代码，日志没有上下文。
            return _html_page("Authorization Failed", self.message)  # 新增代码+DirectOAuthFlow：返回失败页；如果没有这行代码，浏览器没有反馈。
        code = str(query.get("code", "")).strip()  # 新增代码+DirectOAuthFlow：读取授权码；如果没有这行代码，token exchange 没有输入。
        if not code:  # 新增代码+DirectOAuthFlow：拒绝缺 code callback；如果没有这行代码，空 code 会发送到 token endpoint。
            self.status = "failed"  # 新增代码+DirectOAuthFlow：标记失败；如果没有这行代码，GUI 可能继续 pending。
            self.error_code = "oauth_code_missing"  # 新增代码+DirectOAuthFlow：保存缺 code 错误码；如果没有这行代码，前端无法解释失败原因。
            self.message = "OAuth callback did not include a code."  # 新增代码+DirectOAuthFlow：保存可读失败说明；如果没有这行代码，日志没有上下文。
            return _html_page("Authorization Failed", self.message)  # 新增代码+DirectOAuthFlow：返回失败页；如果没有这行代码，浏览器没有反馈。
        try:  # 新增代码+DirectOAuthFlow：捕获 token exchange 失败；如果没有这行代码，远端 500 会让 callback handler 崩溃。
            raw_tokens = self.token_exchanger(code=code, redirect_uri=self.redirect_uri, code_verifier=self.pkce["verifier"], client_id=self.client_id)  # 新增代码+DirectOAuthFlow：执行 code-to-token 交换；如果没有这行代码，登录成功不会得到 token。
            self.token_store.set_tokens("openai", self._normalized_tokens(raw_tokens))  # 新增代码+DirectOAuthFlow：把 token 保存到安全 store；如果没有这行代码，provider catalog 无法显示 connected。
        except Exception as error:  # 新增代码+DirectOAuthFlow：处理远端或存储失败；如果没有这行代码，错误会变成 bridge 500。
            self.status = "failed"  # 新增代码+DirectOAuthFlow：标记失败；如果没有这行代码，GUI 可能继续 pending。
            self.error_code = "oauth_token_exchange_failed"  # 新增代码+DirectOAuthFlow：保存 token exchange 失败码；如果没有这行代码，前端无法显示可读失败。
            self.message = str(error)  # 新增代码+DirectOAuthFlow：保存错误摘要；如果没有这行代码，日志缺少失败细节。
            return _html_page("Authorization Failed", "OpenAI token exchange failed. Return to OpenHarness and try again.")  # 新增代码+DirectOAuthFlow：返回失败页且不泄露 token；如果没有这行代码，浏览器没有反馈。
        self.status = "complete"  # 新增代码+DirectOAuthFlow：标记授权完成；如果没有这行代码，前端轮询不会关闭等待页。
        self.message = "oauth_complete"  # 新增代码+DirectOAuthFlow：保存完成消息；如果没有这行代码，日志无法区分成功来源。
        return _html_page("Authorization Successful", "You can close this window and return to OpenHarness.")  # 新增代码+DirectOAuthFlow：返回成功页；如果没有这行代码，用户不知道可以回到 GUI。
    # 新增代码+DirectOAuthFlow：函数段结束，handle_callback 到此结束；如果没有边界说明，用户不容易看出 callback 不返回 raw token。

    def to_payload(self) -> dict[str, object]:  # 新增代码+DirectOAuthFlow：函数段开始，返回 renderer 安全 attempt 摘要；如果没有这段，auth-attempt 可能暴露 verifier/token。
        return {  # 新增代码+DirectOAuthFlow：返回安全字段字典；如果没有这行代码，调用方无法序列化 attempt。
            "provider_id": "openai",  # 新增代码+DirectOAuthFlow：固定 provider id；如果没有这行代码，前端无法归属 attempt。
            "mode": "direct_oauth_browser",  # 新增代码+DirectOAuthFlow：声明实验 direct OAuth 模式；如果没有这行代码，前端无法渲染正确等待页。
            "url": self.authorize_url,  # 新增代码+DirectOAuthFlow：返回授权 URL；如果没有这行代码，用户无法打开浏览器认证。
            "status": self.status,  # 新增代码+DirectOAuthFlow：返回当前状态；如果没有这行代码，前端无法轮询状态。
            "message": self.message,  # 新增代码+DirectOAuthFlow：返回安全消息；如果没有这行代码，前端无法显示失败/过期原因。
            "error_code": self.error_code,  # 新增代码+DirectOAuthFlow：返回错误码；如果没有这行代码，前端无法区分失败类型。
        }  # 新增代码+DirectOAuthFlow：安全字段字典结束；如果没有这行代码，Python 语法不完整。
    # 新增代码+DirectOAuthFlow：函数段结束，to_payload 到此结束；如果没有边界说明，用户不容易看出 payload 不含 verifier/token。
# 新增代码+DirectOAuthFlow：类段结束，OpenAIProviderOAuthAttempt 到此结束；如果没有边界说明，用户不容易看出它是 direct OAuth 状态机。


def exchange_code_for_tokens(code: str, redirect_uri: str, code_verifier: str, client_id: str) -> dict[str, object]:  # 修改代码+DirectOAuthFlow：函数段开始，执行真实授权码 token exchange；如果没有这段，浏览器 callback 成功后仍无法保存登录。
    form = urllib.parse.urlencode({"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri, "client_id": client_id, "code_verifier": code_verifier}).encode("utf-8")  # 修改代码+DirectOAuthFlow：构造授权码换 token 的表单体；如果没有这行代码，callback 成功后无法得到 access/refresh token。
    request = urllib.request.Request(OPENAI_TOKEN_ENDPOINT, data=form, method="POST", headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})  # 修改代码+DirectOAuthFlow：构造 token endpoint POST 请求；如果没有这行代码，urllib 无法发送正确内容类型。
    try:  # 修改代码+DirectOAuthFlow：捕获网络、HTTP 和 JSON 解析错误；如果没有这行代码，callback handler 可能崩溃而不是返回失败页。
        with urllib.request.urlopen(request, timeout=30) as response:  # 修改代码+DirectOAuthFlow：发送 token exchange 请求；如果没有这行代码，授权码不会被交换。
            raw_body = response.read().decode("utf-8")  # 修改代码+DirectOAuthFlow：读取 token endpoint 响应文本；如果没有这行代码，无法解析 token JSON。
    except urllib.error.HTTPError as error:  # 新增代码+DirectOAuthFlow：处理 OpenAI 返回的 HTTP 错误；如果没有这行代码，错误响应体可能泄露或变成不清楚异常。
        raise OpenAIProviderOAuthError("oauth_token_exchange_http_failed", f"OpenAI token exchange failed with HTTP {error.code}.") from error  # 新增代码+DirectOAuthFlow：返回结构化 HTTP 失败；如果没有这行代码，GUI 无法显示稳定失败原因。
    except urllib.error.URLError as error:  # 新增代码+DirectOAuthFlow：处理 DNS/代理/连接失败；如果没有这行代码，网络失败会冒泡成底层异常。
        raise OpenAIProviderOAuthError("oauth_token_exchange_network_failed", "OpenAI token exchange network request failed.") from error  # 新增代码+DirectOAuthFlow：返回结构化网络失败；如果没有这行代码，用户不知道是网络问题。
    try:  # 新增代码+DirectOAuthFlow：保护 JSON 解析；如果没有这行代码，非 JSON 响应会让 callback handler 崩溃。
        payload = json.loads(raw_body)  # 新增代码+DirectOAuthFlow：解析 token JSON；如果没有这行代码，后续无法保存 token 字段。
    except json.JSONDecodeError as error:  # 新增代码+DirectOAuthFlow：处理非 JSON token 响应；如果没有这行代码，错误页面没有稳定原因。
        raise OpenAIProviderOAuthError("oauth_token_exchange_bad_json", "OpenAI token exchange returned invalid JSON.") from error  # 新增代码+DirectOAuthFlow：返回结构化 JSON 失败；如果没有这行代码，排查会更困难。
    if not isinstance(payload, dict):  # 新增代码+DirectOAuthFlow：要求 token 响应是对象；如果没有这行代码，数组或字符串会污染 token store。
        raise OpenAIProviderOAuthError("oauth_token_exchange_bad_payload", "OpenAI token exchange returned a non-object payload.")  # 新增代码+DirectOAuthFlow：返回结构化 payload 失败；如果没有这行代码，后续字段读取会异常。
    return payload  # 新增代码+DirectOAuthFlow：返回 token payload 给 attempt 状态机保存；如果没有这行代码，direct OAuth 登录无法完成。
# 新增代码+DirectOAuthFlow：函数段结束，exchange_code_for_tokens 到此结束；如果没有边界说明，用户不容易看出真实网络会在集成层接入。
