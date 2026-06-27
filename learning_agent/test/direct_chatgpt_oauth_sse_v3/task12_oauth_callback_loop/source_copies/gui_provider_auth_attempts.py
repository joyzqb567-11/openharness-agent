"""OpenHarness Desktop provider auth-attempt 状态机。"""  # 新增代码+OpenAIAuthAttempt：说明本模块负责连接尝试生命周期；如果没有这行，维护者容易把它误当真实 OAuth token 管理器。

from __future__ import annotations  # 新增代码+OpenAIAuthAttempt：启用延迟类型解析；如果没有这行，类型引用在旧解释器兼容性上更脆弱。

import threading  # 新增代码+OpenAIAuthAttempt：保护内存 attempt registry；如果没有这行，并发 start/status/cancel 可能读写错乱。
import time  # 新增代码+OpenAIAuthAttempt：记录 created/expires/updated 时间；如果没有这行，attempt 无法过期或排序。
import html  # 新增代码+OpenAIRealOAuthCallback：转义 callback 成功/失败页面文本；如果没有这行，官方错误文本可能破坏 HTML。
import http.server  # 新增代码+OpenAIRealOAuthCallback：启动本机 OAuth callback HTTP server；如果没有这行，浏览器授权完成后没有入口回到 OpenHarness。
import urllib.parse  # 新增代码+OpenAIRealOAuthCallback：解析 callback URL 的 code/state/error；如果没有这行，回调参数只能靠脆弱字符串处理。
import uuid  # 新增代码+OpenAIAuthAttempt：生成不可猜测 attempt id；如果没有这行，多个连接尝试 id 容易冲突。
from dataclasses import asdict, dataclass  # 新增代码+OpenAIAuthAttempt：定义 attempt 结构和安全序列化；如果没有这行，payload 字段会散成手写 dict。
from pathlib import Path  # 新增代码+OpenAIAuthAttempt：标注 workspace 路径类型；如果没有这行，Windows 路径语义不清楚。
from typing import Any  # 新增代码+OpenAIAuthAttempt：标注 JSON-like payload；如果没有这行，动态 bridge body 类型边界不清楚。

from learning_agent.app.gui_provider_openai_auth_config import build_openai_auth_config  # 新增代码+OpenAIAuthAttempt：复用 OpenAI auth 配置门禁；如果没有这行，mock/real 边界会和配置 helper 分裂。
from learning_agent.app.gui_provider_openai_oauth import OpenAIRealOAuthAttemptSecret, build_real_openai_oauth_attempt, exchange_openai_oauth_code_for_tokens, store_openai_oauth_token_response  # 修改代码+OpenAIRealOAuthCallback：导入 code exchange 和 token 保存；如果没有 exchange，callback 收到 code 后仍无法连接。
from learning_agent.app.gui_provider_settings import GuiProviderSettingsError, load_provider_settings, save_provider_settings  # 新增代码+OpenAIAuthAttempt：复用 provider 设置读写和结构化错误；如果没有这行，complete 后无法刷新 provider catalog。


AUTH_ATTEMPT_SCHEMA_VERSION = 3  # 新增代码+OpenAIAuthAttempt：声明 auth-attempt payload 版本；如果没有这行，前后端无法判断状态机合同。
OPENAI_AUTH_ATTEMPT_METHODS = {"chatgpt-browser", "chatgpt-headless"}  # 新增代码+OpenAIAuthAttempt：限制稳定 V1 只支持两个 OpenAI OAuth mock 方法；如果没有这行，任意方法可能进入 attempt 状态机。
AUTH_ATTEMPT_TTL_SECONDS = 600.0  # 新增代码+OpenAIAuthAttempt：定义 mock attempt 过期时间；如果没有这行，pending 尝试会永久留在内存。
_ATTEMPT_LOCK = threading.Lock()  # 新增代码+OpenAIAuthAttempt：保护全局 attempt registry；如果没有这行，多请求可能同时修改同一 attempt。
_ATTEMPTS: dict[str, "GuiProviderAuthAttempt"] = {}  # 新增代码+OpenAIAuthAttempt：保存当前进程内 auth attempts；如果没有这行，status/cancel 找不到 start 创建的尝试。
_ATTEMPT_OAUTH_SECRETS: dict[str, OpenAIRealOAuthAttemptSecret] = {}  # 新增代码+OpenAIRealOAuthAttempt：保存不返回 renderer 的 verifier/state；如果没有这行，完成回调无法校验 state 或交换 code。
_CALLBACK_SERVER_LOCK = threading.Lock()  # 新增代码+OpenAIRealOAuthCallback：保护 callback server 注册表；如果没有这行，并发 OAuth start 可能重复绑定同一端口。
_CALLBACK_SERVERS: dict[int, http.server.ThreadingHTTPServer] = {}  # 新增代码+OpenAIRealOAuthCallback：保存已启动的本机 callback servers；如果没有这行，每次 start 都会抢占 callback 端口。


@dataclass  # 新增代码+OpenAIAuthAttempt：自动生成 attempt 字段和 asdict 支持；如果没有这行，payload 序列化需要重复手写。
class GuiProviderAuthAttempt:  # 新增代码+OpenAIAuthAttempt：类段开始，描述一次 provider 授权尝试；如果没有这个类，状态字段会散落在多个 dict 中。
    attempt_id: str  # 新增代码+OpenAIAuthAttempt：保存 attempt 唯一 id；如果没有这行，status/cancel/complete 无法定位尝试。
    provider_id: str  # 新增代码+OpenAIAuthAttempt：保存 provider id；如果没有这行，complete 无法知道要更新哪个 provider。
    auth_method_id: str  # 新增代码+OpenAIAuthAttempt：保存认证方法 id；如果没有这行，browser/headless 展示和完成状态无法区分。
    mode: str  # 新增代码+OpenAIAuthAttempt：保存 mock/real 模式摘要；如果没有这行，前端和日志看不出当前是 mock。
    url: str  # 新增代码+OpenAIAuthAttempt：保存用户要打开的授权链接；如果没有这行，UI 没有“访问此链接”的目标。
    instructions: str  # 新增代码+OpenAIAuthAttempt：保存人类可读授权说明；如果没有这行，等待页只能显示机器状态。
    display_code: str  # 新增代码+OpenAIAuthAttempt：保存设备码或浏览器提示文本；如果没有这行，headless flow 没有可复制内容。
    display_code_kind: str  # 新增代码+OpenAIAuthAttempt：保存展示码类型；如果没有这行，前端无法区分 device code 和 browser instruction。
    display_code_copyable: bool  # 新增代码+OpenAIAuthAttempt：保存展示文本是否可复制；如果没有这行，UI 无法决定是否显示复制按钮。
    status: str  # 新增代码+OpenAIAuthAttempt：保存 pending/complete/failed/expired；如果没有这行，轮询没有状态机。
    message: str  # 新增代码+OpenAIAuthAttempt：保存安全短消息；如果没有这行，失败或取消没有可读说明。
    created_at: float  # 新增代码+OpenAIAuthAttempt：保存创建时间；如果没有这行，attempt 无法审计或排序。
    expires_at: float  # 新增代码+OpenAIAuthAttempt：保存过期时间；如果没有这行，pending 状态无法自动过期。
    oauth_state: str = ""  # 新增代码+OpenAIRealOAuthAttempt：保存公开的 OAuth state 摘要；如果没有这行，测试和回调难以验证 state 是否匹配。
    oauth_client_source: str = ""  # 新增代码+OpenAIRealOAuthAttempt：保存 client id 来源诊断；如果没有这行，UI 和日志不知道是否使用 OpenCode 观察参考。
    # 新增代码+OpenAIAuthAttempt：类段结束，GuiProviderAuthAttempt 到此结束；如果没有边界说明，初学者不易看出 attempt 字段范围。


def _new_attempt_id() -> str:  # 新增代码+OpenAIAuthAttempt：函数段开始，生成 attempt id；如果没有这段，start 请求无法返回稳定标识。
    return f"auth_attempt_{uuid.uuid4().hex[:18]}"  # 新增代码+OpenAIAuthAttempt：返回带前缀的随机 id；如果没有这行，前端很难从 id 看出对象类型。
# 新增代码+OpenAIAuthAttempt：函数段结束，_new_attempt_id 到此结束；如果没有边界说明，初学者不易看出它只负责 id。


def _attempt_payload(attempt: GuiProviderAuthAttempt) -> dict[str, Any]:  # 新增代码+OpenAIAuthAttempt：函数段开始，包装 attempt 响应；如果没有这段，start/status/cancel/complete 会返回不同形状。
    return {"ok": True, "schema_version": AUTH_ATTEMPT_SCHEMA_VERSION, "attempt": asdict(attempt)}  # 新增代码+OpenAIAuthAttempt：返回统一 JSON payload；如果没有这行，前端轮询难以复用同一类型。
# 新增代码+OpenAIAuthAttempt：函数段结束，_attempt_payload 到此结束；如果没有边界说明，初学者不易看出它只负责响应形状。


def _expired_placeholder_attempt(attempt_id: Any, message: str) -> GuiProviderAuthAttempt:  # 新增代码+OpenAIAuthAttemptTail：函数段开始，为未知或已清理 attempt 构造 expired 占位；如果没有这段，旧轮询会收到 404 并把 GUI 带入异常态。
    clean_attempt_id = str(attempt_id or "").strip() or "auth_attempt_unknown"  # 新增代码+OpenAIAuthAttemptTail：清理并兜底 attempt id；如果没有这行，空 id 会让前端难以关联失败对象。
    now = time.time()  # 新增代码+OpenAIAuthAttemptTail：记录占位时间；如果没有这行，created_at/expires_at 字段会缺失。
    return GuiProviderAuthAttempt(attempt_id=clean_attempt_id, provider_id="", auth_method_id="", mode="mock", url="", instructions="", display_code="", display_code_kind="unknown", display_code_copyable=False, status="expired", message=message, created_at=now, expires_at=now)  # 新增代码+OpenAIAuthAttemptTail：返回非敏感 expired 占位 attempt；如果没有这行，status/cancel 对未知 id 无法保持同一 payload 形状。
# 新增代码+OpenAIAuthAttemptTail：函数段结束，_expired_placeholder_attempt 到此结束；如果没有边界说明，初学者不易看出它只生成安全占位对象。


def _validate_openai_attempt(provider_id: Any, auth_method_id: Any) -> tuple[str, str]:  # 新增代码+OpenAIAuthAttempt：函数段开始，校验 provider 和 method；如果没有这段，非 OpenAI 或 API key 也可能进入 OAuth attempt。
    clean_provider_id = str(provider_id or "").strip()  # 新增代码+OpenAIAuthAttempt：清理 provider id；如果没有这行，空白 provider 可能绕过判断。
    clean_auth_method_id = str(auth_method_id or "").strip()  # 新增代码+OpenAIAuthAttempt：清理 auth method id；如果没有这行，空白方法可能进入 registry。
    if clean_provider_id != "openai":  # 新增代码+OpenAIAuthAttempt：只允许 OpenAI provider；如果没有这行，Google/OpenRouter 等会进入错误状态机。
        raise GuiProviderSettingsError(400, "unsupported_auth_attempt_provider", "V1 auth-attempt 只支持 OpenAI。")  # 新增代码+OpenAIAuthAttempt：返回 provider 不支持错误；如果没有这行，前端无法显示稳定错误。
    if clean_auth_method_id not in OPENAI_AUTH_ATTEMPT_METHODS:  # 新增代码+OpenAIAuthAttempt：只允许 browser/headless 方法；如果没有这行，API key 会误走 OAuth attempt。
        raise GuiProviderSettingsError(400, "unsupported_auth_attempt_method", "该认证方式不支持 auth-attempt。")  # 新增代码+OpenAIAuthAttempt：返回方法不支持错误；如果没有这行，前端无法显示稳定错误。
    return clean_provider_id, clean_auth_method_id  # 新增代码+OpenAIAuthAttempt：返回清洗后的 provider/method；如果没有这行，调用方拿不到安全 id。
# 新增代码+OpenAIAuthAttempt：函数段结束，_validate_openai_attempt 到此结束；如果没有边界说明，初学者不易看出它只负责输入校验。


def _expire_stale_pending_attempt(attempt: GuiProviderAuthAttempt, now: float) -> GuiProviderAuthAttempt:  # 新增代码+OpenAIAuthAttempt：函数段开始，按时间过期 pending attempt；如果没有这段，过期状态不会自动收敛。
    if attempt.status == "pending" and now >= attempt.expires_at:  # 新增代码+OpenAIAuthAttempt：只过期超时的 pending；如果没有这行，complete/failed 状态可能被覆盖。
        attempt.status = "expired"  # 新增代码+OpenAIAuthAttempt：把超时尝试标记为 expired；如果没有这行，前端会永久等待。
        attempt.message = "expired"  # 新增代码+OpenAIAuthAttempt：保存过期原因；如果没有这行，UI 无法显示为什么结束。
    return attempt  # 新增代码+OpenAIAuthAttempt：返回可能更新后的 attempt；如果没有这行，调用方拿不到状态。
# 新增代码+OpenAIAuthAttempt：函数段结束，_expire_stale_pending_attempt 到此结束；如果没有边界说明，初学者不易看出它只处理过期。


def _cancel_existing_pending_for_provider(provider_id: str) -> None:  # 新增代码+OpenAIAuthAttempt：函数段开始，取消同 provider 的旧 pending attempt；如果没有这段，多个等待页会互相打架。
    for attempt in _ATTEMPTS.values():  # 新增代码+OpenAIAuthAttempt：遍历当前进程内 attempts；如果没有这行，无法找到旧 pending。
        if attempt.provider_id == provider_id and attempt.status == "pending":  # 新增代码+OpenAIAuthAttempt：只处理同 provider pending；如果没有这行，其他 provider 或终态 attempt 会被误改。
            attempt.status = "expired"  # 新增代码+OpenAIAuthAttempt：把旧 pending 收敛为 expired；如果没有这行，旧轮询会一直等待。
            attempt.message = "superseded_by_new_attempt"  # 新增代码+OpenAIAuthAttempt：记录被新 attempt 替代；如果没有这行，排查时看不出为什么取消。
# 新增代码+OpenAIAuthAttempt：函数段结束，_cancel_existing_pending_for_provider 到此结束；如果没有边界说明，初学者不易看出它只清理旧 pending。


def _mock_attempt_fields(auth_method_id: str, attempt_id: str, base_url: str) -> tuple[str, str, str, str, bool]:  # 新增代码+OpenAIAuthAttempt：函数段开始，生成 mock 授权展示字段；如果没有这段，browser/headless 文案会散落。
    safe_base_url = base_url.rstrip("/")  # 新增代码+OpenAIAuthAttempt：去掉 base URL 尾部斜杠；如果没有这行，拼接 URL 可能出现双斜杠。
    if auth_method_id == "chatgpt-headless":  # 新增代码+OpenAIAuthAttempt：处理 headless 设备码 flow；如果没有这行，设备码和浏览器说明无法区分。
        display_code = f"MOCK-OPENAI-{attempt_id[-6:].upper()}"  # 新增代码+OpenAIAuthAttempt：生成可复制 mock 设备码；如果没有这行，headless 等待页没有用户输入内容。
        return f"{safe_base_url}/mock/openai/device", "访问此链接并输入设备码，以完成 mock ChatGPT 授权。", display_code, "device_code", True  # 新增代码+OpenAIAuthAttempt：返回 headless mock 展示字段；如果没有这行，前端无法显示设备码流程。
    return f"{safe_base_url}/mock/openai/browser", "在浏览器中完成 mock ChatGPT 授权。", "Complete authorization in your browser. This window will close automatically.", "browser_instruction", False  # 新增代码+OpenAIAuthAttempt：返回 browser mock 展示字段；如果没有这行，前端无法显示浏览器登录流程。
# 新增代码+OpenAIAuthAttempt：函数段结束，_mock_attempt_fields 到此结束；如果没有边界说明，初学者不易看出它只生成展示字段。


def _callback_port_from_redirect_uri(redirect_uri: str) -> int:  # 新增代码+OpenAIRealOAuthCallback：函数段开始，从 redirect_uri 提取本机 callback 端口；如果没有这段，listener 可能绑定错端口。
    parsed = urllib.parse.urlparse(str(redirect_uri or ""))  # 新增代码+OpenAIRealOAuthCallback：解析 redirect_uri；如果没有这行，端口和路径只能靠字符串切片。
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1"} or parsed.path != "/auth/callback" or not parsed.port:  # 新增代码+OpenAIRealOAuthCallback：只允许预期本机 callback URI；如果没有这行，错误配置可能启动危险监听。
        raise GuiProviderSettingsError(400, "invalid_openai_redirect_uri", "OpenAI OAuth redirect_uri 必须是本机 /auth/callback。")  # 新增代码+OpenAIRealOAuthCallback：返回结构化 redirect 错误；如果没有这行，排查端口错误会很困难。
    return int(parsed.port)  # 新增代码+OpenAIRealOAuthCallback：返回 callback 端口；如果没有这行，listener 没有端口输入。
# 新增代码+OpenAIRealOAuthCallback：函数段结束，_callback_port_from_redirect_uri 到此结束；如果没有边界说明，初学者不易看出它只验证本机 URI。


def _find_oauth_secret_by_state_locked(callback_state: Any) -> tuple[str, OpenAIRealOAuthAttemptSecret]:  # 新增代码+OpenAIRealOAuthCallback：函数段开始，按 OAuth state 查找 attempt 和私有 verifier；如果没有这段，callback 只有 state 时无法定位 attempt。
    clean_state = str(callback_state or "").strip()  # 新增代码+OpenAIRealOAuthCallback：清理 callback state；如果没有这行，空白 state 可能误匹配。
    for attempt_id, oauth_secret in _ATTEMPT_OAUTH_SECRETS.items():  # 新增代码+OpenAIRealOAuthCallback：遍历当前真实 OAuth 私有状态；如果没有这行，无法从 state 找 attempt。
        if oauth_secret.oauth_state == clean_state:  # 新增代码+OpenAIRealOAuthCallback：匹配本次 callback state；如果没有这行，任何回调都可能被接受。
            return attempt_id, oauth_secret  # 新增代码+OpenAIRealOAuthCallback：返回 attempt id 和私有 verifier；如果没有这行，token exchange 缺少材料。
    raise GuiProviderSettingsError(400, "openai_oauth_state_not_found", "OpenAI OAuth state 未找到或已过期。")  # 新增代码+OpenAIRealOAuthCallback：返回未知 state 错误；如果没有这行，错误回调会变成不明 500。
# 新增代码+OpenAIRealOAuthCallback：函数段结束，_find_oauth_secret_by_state_locked 到此结束；如果没有边界说明，初学者不易看出调用方必须持锁。


def _mark_real_provider_auth_attempt_failed(attempt_id: str, message: str) -> None:  # 新增代码+OpenAIRealOAuthCallback：函数段开始，把真实 OAuth attempt 标记失败并清理 verifier；如果没有这段，token exchange 失败后前端会永久 pending。
    clean_attempt_id = str(attempt_id or "").strip()  # 新增代码+OpenAIRealOAuthCallback：清理 attempt id；如果没有这行，空 id 可能污染 registry。
    with _ATTEMPT_LOCK:  # 新增代码+OpenAIRealOAuthCallback：锁住 attempt 状态更新；如果没有这行，callback/status/cancel 会竞态。
        attempt = _ATTEMPTS.get(clean_attempt_id)  # 新增代码+OpenAIRealOAuthCallback：读取目标 attempt；如果没有这行，无法更新状态。
        if attempt is not None and attempt.status == "pending":  # 新增代码+OpenAIRealOAuthCallback：只把 pending 变 failed；如果没有这行，complete/expired 可能被覆盖。
            attempt.status = "failed"  # 新增代码+OpenAIRealOAuthCallback：标记失败终态；如果没有这行，前端轮询不会停止。
            attempt.message = str(message or "openai_oauth_failed")[:160]  # 新增代码+OpenAIRealOAuthCallback：保存短失败原因；如果没有这行，用户不知道失败阶段。
        _ATTEMPT_OAUTH_SECRETS.pop(clean_attempt_id, None)  # 新增代码+OpenAIRealOAuthCallback：失败后清理 PKCE verifier/state；如果没有这行，敏感交换材料会残留。
# 新增代码+OpenAIRealOAuthCallback：函数段结束，_mark_real_provider_auth_attempt_failed 到此结束；如果没有边界说明，初学者不易看出它只处理终态失败。


def complete_real_provider_auth_attempt_with_code(workspace: str | Path, callback_state: Any, code: Any) -> dict[str, Any]:  # 新增代码+OpenAIRealOAuthCallback：函数段开始，用浏览器 callback code 完成真实 OAuth attempt；如果没有这段，callback server 收到 code 后仍不能保存连接。
    clean_state = str(callback_state or "").strip()  # 新增代码+OpenAIRealOAuthCallback：清理 state；如果没有这行，state 查找不稳定。
    clean_code = str(code or "").strip()  # 新增代码+OpenAIRealOAuthCallback：清理 authorization code；如果没有这行，空白 code 可能传入 exchange。
    with _ATTEMPT_LOCK:  # 新增代码+OpenAIRealOAuthCallback：锁住 state 查找；如果没有这行，cancel 可能同时删除私有状态。
        attempt_id, oauth_secret = _find_oauth_secret_by_state_locked(clean_state)  # 新增代码+OpenAIRealOAuthCallback：按 state 找到 attempt 和 PKCE verifier；如果没有这行，无法安全交换 token。
    try:  # 新增代码+OpenAIRealOAuthCallback：保护 token exchange；如果没有这行，失败时 attempt 会一直 pending。
        token_payload = exchange_openai_oauth_code_for_tokens(oauth_secret, clean_code)  # 新增代码+OpenAIRealOAuthCallback：用 code 换 token payload；如果没有这行，真实授权不会变成可用凭据。
    except GuiProviderSettingsError as error:  # 新增代码+OpenAIRealOAuthCallback：处理结构化 exchange 失败；如果没有这行，等待页看不到失败状态。
        _mark_real_provider_auth_attempt_failed(attempt_id, error.code)  # 新增代码+OpenAIRealOAuthCallback：把 attempt 标成 failed；如果没有这行，前端会持续等待。
        raise  # 新增代码+OpenAIRealOAuthCallback：继续把错误交给 callback 页面；如果没有这行，浏览器不会显示失败原因。
    except Exception as error:  # 新增代码+OpenAIRealOAuthCallback：兜底处理非结构化异常；如果没有这行，未知错误会留下 pending。
        _mark_real_provider_auth_attempt_failed(attempt_id, "openai_oauth_token_exchange_failed")  # 新增代码+OpenAIRealOAuthCallback：把未知 exchange 失败收敛成终态；如果没有这行，用户只能取消重试。
        raise GuiProviderSettingsError(502, "openai_oauth_token_exchange_failed", f"OpenAI OAuth token exchange failed: {error}") from error  # 新增代码+OpenAIRealOAuthCallback：抛出结构化未知错误；如果没有这行，callback 页面没有可读失败。
    return complete_real_provider_auth_attempt_with_tokens(workspace, attempt_id, clean_state, token_payload)  # 新增代码+OpenAIRealOAuthCallback：复用已有 state 校验和加密保存；如果没有这行，provider catalog 不会变成已连接。
# 新增代码+OpenAIRealOAuthCallback：函数段结束，complete_real_provider_auth_attempt_with_code 到此结束；如果没有边界说明，初学者不易看出它连接 callback 与保存逻辑。


class _OpenAIRealOAuthCallbackServer(http.server.ThreadingHTTPServer):  # 新增代码+OpenAIRealOAuthCallback：类段开始，保存 workspace 的本机 OAuth callback server；如果没有这个类，handler 不知道 token 应写入哪个 workspace。
    daemon_threads = True  # 新增代码+OpenAIRealOAuthCallback：让 callback 工作线程随进程退出；如果没有这行，测试或桌面关闭时可能残留阻塞线程。

    def __init__(self, server_address: tuple[str, int], workspace: str | Path) -> None:  # 新增代码+OpenAIRealOAuthCallback：函数段开始，初始化带 workspace 的 HTTP server；如果没有这段，server 不能携带工作区。
        super().__init__(server_address, _OpenAIRealOAuthCallbackHandler)  # 新增代码+OpenAIRealOAuthCallback：绑定 callback handler；如果没有这行，HTTP server 收到请求不知道如何处理。
        self.workspace = Path(workspace).expanduser().resolve()  # 新增代码+OpenAIRealOAuthCallback：保存规范化 workspace；如果没有这行，token 会写到不确定位置。
    # 新增代码+OpenAIRealOAuthCallback：函数段结束，_OpenAIRealOAuthCallbackServer.__init__ 到此结束；如果没有边界说明，初学者不易看出它只保存 workspace。
# 新增代码+OpenAIRealOAuthCallback：类段结束，_OpenAIRealOAuthCallbackServer 到此结束；如果没有边界说明，初学者不易看出它是 HTTPServer 包装。


class _OpenAIRealOAuthCallbackHandler(http.server.BaseHTTPRequestHandler):  # 新增代码+OpenAIRealOAuthCallback：类段开始，处理浏览器访问 /auth/callback；如果没有这个类，OpenAI 授权返回后没人接收 code。
    server: _OpenAIRealOAuthCallbackServer  # 新增代码+OpenAIRealOAuthCallback：标注 server 带 workspace 字段；如果没有这行，类型检查和维护者都不知道 self.server 形状。

    def log_message(self, format: str, *args: Any) -> None:  # 新增代码+OpenAIRealOAuthCallback：函数段开始，关闭默认 HTTP 访问日志；如果没有这段，授权 code 可能被默认日志格式间接暴露。
        del format, args  # 新增代码+OpenAIRealOAuthCallback：明确丢弃日志参数；如果没有这行，静态检查会提示未使用。
    # 新增代码+OpenAIRealOAuthCallback：函数段结束，log_message 到此结束；如果没有边界说明，初学者不易看出它是安全降噪。

    def _send_callback_page(self, title: str, message: str, status: int = 200) -> None:  # 新增代码+OpenAIRealOAuthCallback：函数段开始，返回浏览器可见授权结果页；如果没有这段，用户认证后只会看到空白或底层错误。
        safe_title = html.escape(str(title or "Authorization"))  # 新增代码+OpenAIRealOAuthCallback：转义标题；如果没有这行，错误文本可能注入 HTML。
        safe_message = html.escape(str(message or ""))  # 新增代码+OpenAIRealOAuthCallback：转义说明；如果没有这行，官方错误文本可能破坏页面。
        body = f"<html><body style='background:#111;color:#f7f7f7;font-family:Segoe UI,Arial,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0'><main><h1>{safe_title}</h1><p>{safe_message}</p></main></body></html>"  # 新增代码+OpenAIRealOAuthCallback：构造简单结果页；如果没有这行，浏览器没有肉眼可见反馈。
        encoded = body.encode("utf-8")  # 新增代码+OpenAIRealOAuthCallback：编码 HTML；如果没有这行，wfile 不能写字符串。
        self.send_response(status)  # 新增代码+OpenAIRealOAuthCallback：发送 HTTP 状态码；如果没有这行，浏览器收不到合法响应。
        self.send_header("Content-Type", "text/html; charset=utf-8")  # 新增代码+OpenAIRealOAuthCallback：声明 UTF-8 HTML；如果没有这行，中文错误可能乱码。
        self.send_header("Content-Length", str(len(encoded)))  # 新增代码+OpenAIRealOAuthCallback：声明响应长度；如果没有这行，浏览器可能等待连接关闭判断结束。
        self.end_headers()  # 新增代码+OpenAIRealOAuthCallback：结束响应头；如果没有这行，响应体无法写出。
        self.wfile.write(encoded)  # 新增代码+OpenAIRealOAuthCallback：写出页面内容；如果没有这行，用户看不到结果。
    # 新增代码+OpenAIRealOAuthCallback：函数段结束，_send_callback_page 到此结束；如果没有边界说明，初学者不易看出它只负责 HTML 输出。

    def do_GET(self) -> None:  # 新增代码+OpenAIRealOAuthCallback：函数段开始，接收 OpenAI OAuth callback GET；如果没有这段，浏览器回调无法进入后端。
        parsed = urllib.parse.urlparse(self.path)  # 新增代码+OpenAIRealOAuthCallback：解析请求路径；如果没有这行，无法区分 /auth/callback 和其它路径。
        if parsed.path != "/auth/callback":  # 新增代码+OpenAIRealOAuthCallback：只处理 OAuth callback 路径；如果没有这行，server 会误响应任意本机请求。
            self._send_callback_page("Authorization Failed", "Unknown OpenAI OAuth callback path.", status=404)  # 新增代码+OpenAIRealOAuthCallback：未知路径返回可见失败页；如果没有这行，错误访问没有反馈。
            return  # 新增代码+OpenAIRealOAuthCallback：未知路径处理完退出；如果没有这行，会继续解析不存在的 OAuth 参数。
        query = urllib.parse.parse_qs(parsed.query)  # 新增代码+OpenAIRealOAuthCallback：解析 callback query；如果没有这行，拿不到 code/state/error。
        callback_state = query.get("state", [""])[0]  # 新增代码+OpenAIRealOAuthCallback：读取 OAuth state；如果没有这行，无法匹配 attempt。
        callback_code = query.get("code", [""])[0]  # 新增代码+OpenAIRealOAuthCallback：读取 authorization code；如果没有这行，无法交换 token。
        callback_error = query.get("error_description", query.get("error", [""]))[0]  # 新增代码+OpenAIRealOAuthCallback：读取 OpenAI 授权错误；如果没有这行，用户取消/拒绝会被误当缺 code。
        try:  # 新增代码+OpenAIRealOAuthCallback：保护 callback 完成流程；如果没有这行，浏览器只会看到断开的连接。
            if callback_error:  # 新增代码+OpenAIRealOAuthCallback：处理 OpenAI 授权端返回错误；如果没有这行，用户取消授权会继续尝试 exchange。
                with _ATTEMPT_LOCK:  # 新增代码+OpenAIRealOAuthCallback：锁住 state 查找；如果没有这行，取消和 callback 可能竞态。
                    failed_attempt_id, _ = _find_oauth_secret_by_state_locked(callback_state)  # 新增代码+OpenAIRealOAuthCallback：定位失败 attempt；如果没有这行，前端状态无法从 pending 收敛。
                _mark_real_provider_auth_attempt_failed(failed_attempt_id, "openai_oauth_callback_error")  # 新增代码+OpenAIRealOAuthCallback：标记授权端错误；如果没有这行，等待页会一直 pending。
                raise GuiProviderSettingsError(400, "openai_oauth_callback_error", str(callback_error)[:160])  # 新增代码+OpenAIRealOAuthCallback：把授权端错误显示到结果页；如果没有这行，用户不知道失败原因。
            complete_real_provider_auth_attempt_with_code(self.server.workspace, callback_state, callback_code)  # 新增代码+OpenAIRealOAuthCallback：用 code 完成 token exchange 和保存；如果没有这行，provider 不会变成已连接。
            self._send_callback_page("Authorization Successful", "You can close this window and return to OpenHarness Desktop.")  # 新增代码+OpenAIRealOAuthCallback：返回成功页；如果没有这行，用户不知道授权已完成。
        except GuiProviderSettingsError as error:  # 新增代码+OpenAIRealOAuthCallback：处理结构化 OAuth 错误；如果没有这行，浏览器会看到连接重置。
            self._send_callback_page("Authorization Failed", error.message)  # 新增代码+OpenAIRealOAuthCallback：返回失败页；如果没有这行，用户无法把错误截图反馈。
    # 新增代码+OpenAIRealOAuthCallback：函数段结束，do_GET 到此结束；如果没有边界说明，初学者不易看出它处理一次浏览器回调。
# 新增代码+OpenAIRealOAuthCallback：类段结束，_OpenAIRealOAuthCallbackHandler 到此结束；如果没有边界说明，初学者不易看出它只服务本机 callback。


def _ensure_openai_oauth_callback_server(workspace: str | Path, oauth_secret: OpenAIRealOAuthAttemptSecret) -> None:  # 新增代码+OpenAIRealOAuthCallback：函数段开始，确保本机 callback server 已监听；如果没有这段，OpenAI 返回 redirect_uri 时会连接失败。
    callback_port = _callback_port_from_redirect_uri(oauth_secret.redirect_uri)  # 新增代码+OpenAIRealOAuthCallback：从本次 redirect_uri 读取端口；如果没有这行，server 可能和 URL 不一致。
    with _CALLBACK_SERVER_LOCK:  # 新增代码+OpenAIRealOAuthCallback：锁住 server 创建；如果没有这行，并发 start 会重复 bind。
        if callback_port in _CALLBACK_SERVERS:  # 新增代码+OpenAIRealOAuthCallback：复用同端口已启动 server；如果没有这行，第二次连接会因端口占用失败。
            return  # 新增代码+OpenAIRealOAuthCallback：已监听时直接返回；如果没有这行，会继续重复创建 server。
        try:  # 新增代码+OpenAIRealOAuthCallback：保护端口绑定；如果没有这行，端口占用会变成底层 OSError。
            server = _OpenAIRealOAuthCallbackServer(("localhost", callback_port), workspace)  # 新增代码+OpenAIRealOAuthCallback：创建本机 callback server；如果没有这行，浏览器回调没有接收者。
        except OSError as error:  # 新增代码+OpenAIRealOAuthCallback：处理端口占用/权限错误；如果没有这行，用户看不到可读原因。
            raise GuiProviderSettingsError(503, "openai_oauth_callback_listener_unavailable", f"无法启动 OpenAI OAuth callback listener：{error}") from error  # 新增代码+OpenAIRealOAuthCallback：返回结构化 listener 错误；如果没有这行，连接按钮会显示泛化失败。
        thread = threading.Thread(target=server.serve_forever, daemon=True, name=f"OpenHarnessOpenAIOAuthCallback:{callback_port}")  # 新增代码+OpenAIRealOAuthCallback：创建后台监听线程；如果没有这行，server 创建后不会处理请求。
        thread.start()  # 新增代码+OpenAIRealOAuthCallback：启动后台 listener；如果没有这行，callback URL 仍然连接不上。
        _CALLBACK_SERVERS[callback_port] = server  # 新增代码+OpenAIRealOAuthCallback：记录已启动 server；如果没有这行，后续 start 会重复绑定端口。
# 新增代码+OpenAIRealOAuthCallback：函数段结束，_ensure_openai_oauth_callback_server 到此结束；如果没有边界说明，初学者不易看出它只负责监听生命周期。


def start_provider_auth_attempt(workspace: str | Path, provider_id: Any, auth_method_id: Any) -> dict[str, Any]:  # 新增代码+OpenAIAuthAttempt：函数段开始，启动 provider auth attempt；如果没有这段，browser/headless 连接按钮没有后端状态机。
    clean_provider_id, clean_auth_method_id = _validate_openai_attempt(provider_id, auth_method_id)  # 新增代码+OpenAIAuthAttempt：校验并清洗 provider/method；如果没有这行，非法请求会进入 registry。
    config = build_openai_auth_config()  # 新增代码+OpenAIAuthAttempt：读取 OpenAI auth 配置；如果没有这行，mock/real 门禁不会生效。
    now = time.time()  # 新增代码+OpenAIAuthAttempt：记录当前时间；如果没有这行，created/expires 无法稳定生成。
    attempt_id = _new_attempt_id()  # 新增代码+OpenAIAuthAttempt：生成新 attempt id；如果没有这行，前端无法轮询。
    oauth_secret: OpenAIRealOAuthAttemptSecret | None = None  # 新增代码+OpenAIRealOAuthAttempt：准备真实 OAuth 私有状态占位；如果没有这行，mock/real 分支无法统一保存。
    if config.real_oauth_enabled:  # 新增代码+OpenAIRealOAuthAttempt：真实 OAuth 门禁通过时走真实浏览器 URL；如果没有这行，用户只有 mock 链接。
        url, oauth_secret = build_real_openai_oauth_attempt(attempt_id)  # 新增代码+OpenAIRealOAuthAttempt：生成真实授权 URL 和私有 verifier/state；如果没有这行，browser flow 无法跳转 OpenAI。
        instructions = "访问此链接并在浏览器中完成 OpenAI 授权。授权成功后，本地 callback 会保存加密 token。"  # 新增代码+OpenAIRealOAuthAttempt：提供真实授权说明；如果没有这行，等待页仍会显示 mock 文案。
        display_code = "Complete authorization in your browser. This window will close automatically."  # 新增代码+OpenAIRealOAuthAttempt：沿用浏览器完成提示；如果没有这行，前端展示码区域会空白。
        display_code_kind = "browser_instruction"  # 新增代码+OpenAIRealOAuthAttempt：声明展示内容是浏览器说明；如果没有这行，前端可能把它当设备码。
        copyable = False  # 新增代码+OpenAIRealOAuthAttempt：真实浏览器提示不可复制为设备码；如果没有这行，UI 可能显示错误复制按钮。
        attempt = GuiProviderAuthAttempt(attempt_id=attempt_id, provider_id=clean_provider_id, auth_method_id=clean_auth_method_id, mode=config.auth_mode, url=url, instructions=instructions, display_code=display_code, display_code_kind=display_code_kind, display_code_copyable=copyable, status="pending", message="", created_at=now, expires_at=now + AUTH_ATTEMPT_TTL_SECONDS, oauth_state=oauth_secret.oauth_state, oauth_client_source=oauth_secret.oauth_client_source)  # 新增代码+OpenAIRealOAuthAttempt：创建真实 OAuth pending attempt；如果没有这行，前端无法看到真实 URL 和来源诊断。
    else:  # 新增代码+OpenAIRealOAuthAttempt：未开启真实 OAuth 时保持稳定 mock 路径；如果没有这行，默认设置页会被真实门禁阻断。
        url, instructions, display_code, display_code_kind, copyable = _mock_attempt_fields(clean_auth_method_id, attempt_id, config.auth_base_url)  # 新增代码+OpenAIAuthAttempt：生成 mock 展示字段；如果没有这行，等待页没有链接和说明。
        attempt = GuiProviderAuthAttempt(attempt_id=attempt_id, provider_id=clean_provider_id, auth_method_id=clean_auth_method_id, mode="mock", url=url, instructions=instructions, display_code=display_code, display_code_kind=display_code_kind, display_code_copyable=copyable, status="pending", message="", created_at=now, expires_at=now + AUTH_ATTEMPT_TTL_SECONDS)  # 新增代码+OpenAIAuthAttempt：创建 pending attempt；如果没有这行，状态机没有核心对象。
    with _ATTEMPT_LOCK:  # 新增代码+OpenAIAuthAttempt：锁住 registry 写入；如果没有这行，并发 start 可能互相覆盖。
        _cancel_existing_pending_for_provider(clean_provider_id)  # 新增代码+OpenAIAuthAttempt：取消同 provider 旧 pending；如果没有这行，多窗口等待状态会冲突。
        _ATTEMPTS[attempt_id] = attempt  # 新增代码+OpenAIAuthAttempt：保存新 attempt；如果没有这行，status/cancel/complete 找不到它。
        if oauth_secret is not None:  # 新增代码+OpenAIRealOAuthAttempt：真实 flow 才保存私有 verifier/state；如果没有这行，mock attempt 会污染真实 OAuth registry。
            _ATTEMPT_OAUTH_SECRETS[attempt_id] = oauth_secret  # 新增代码+OpenAIRealOAuthAttempt：保存不返回前端的私有 OAuth 数据；如果没有这行，complete 无法校验 state。
    if oauth_secret is not None:  # 新增代码+OpenAIRealOAuthCallback：真实 OAuth attempt 创建后启动本机 callback listener；如果没有这行，OpenAI 官方 redirect 会无人接收。
        try:  # 新增代码+OpenAIRealOAuthCallback：保护 listener 启动；如果没有这行，端口错误会留下永久 pending attempt。
            _ensure_openai_oauth_callback_server(workspace, oauth_secret)  # 新增代码+OpenAIRealOAuthCallback：确保 redirect_uri 对应端口正在监听；如果没有这行，浏览器认证成功也无法回写 token。
        except GuiProviderSettingsError:  # 新增代码+OpenAIRealOAuthCallback：处理 listener 启动失败；如果没有这行，失败 attempt 会残留 verifier。
            _mark_real_provider_auth_attempt_failed(attempt_id, "openai_oauth_callback_listener_unavailable")  # 新增代码+OpenAIRealOAuthCallback：把 attempt 收敛成 failed；如果没有这行，前端会一直等待。
            raise  # 新增代码+OpenAIRealOAuthCallback：把启动失败返回给调用方；如果没有这行，用户会拿到不可用链接。
    return _attempt_payload(attempt)  # 新增代码+OpenAIAuthAttempt：返回 pending payload；如果没有这行，bridge 无法响应前端。
# 新增代码+OpenAIAuthAttempt：函数段结束，start_provider_auth_attempt 到此结束；如果没有边界说明，初学者不易看出它只启动状态机不保存 token。


def get_provider_auth_attempt_status(attempt_id: Any) -> dict[str, Any]:  # 新增代码+OpenAIAuthAttempt：函数段开始，读取 auth attempt 状态；如果没有这段，前端无法轮询等待页。
    clean_attempt_id = str(attempt_id or "").strip()  # 新增代码+OpenAIAuthAttempt：清理 attempt id；如果没有这行，空白 id 可能访问 registry。
    with _ATTEMPT_LOCK:  # 新增代码+OpenAIAuthAttempt：锁住 registry 读取和过期更新；如果没有这行，status 可能读到半更新状态。
        attempt = _ATTEMPTS.get(clean_attempt_id)  # 新增代码+OpenAIAuthAttempt：读取目标 attempt；如果没有这行，无法判断是否存在。
        if attempt is None:  # 新增代码+OpenAIAuthAttempt：处理未知 attempt；如果没有这行，后续访问会 AttributeError。
            return _attempt_payload(_expired_placeholder_attempt(clean_attempt_id, "auth_attempt_not_found"))  # 修改代码+OpenAIAuthAttemptTail：未知 status 返回 expired 占位而不是 404；如果没有这行，旧轮询会把 GUI 带入错误态。
        _expire_stale_pending_attempt(attempt, time.time())  # 新增代码+OpenAIAuthAttempt：按时间自动过期；如果没有这行，超时状态不会更新。
        return _attempt_payload(attempt)  # 新增代码+OpenAIAuthAttempt：返回状态 payload；如果没有这行，前端拿不到状态。
# 新增代码+OpenAIAuthAttempt：函数段结束，get_provider_auth_attempt_status 到此结束；如果没有边界说明，初学者不易看出它只读状态。


def complete_provider_auth_attempt(workspace: str | Path, attempt_id: Any) -> dict[str, Any]:  # 新增代码+OpenAIAuthAttempt：函数段开始，完成 mock auth attempt；如果没有这段，视觉 QA 无法模拟授权完成。
    clean_attempt_id = str(attempt_id or "").strip()  # 新增代码+OpenAIAuthAttempt：清理 attempt id；如果没有这行，空白 id 可能访问 registry。
    with _ATTEMPT_LOCK:  # 新增代码+OpenAIAuthAttempt：锁住 registry 更新；如果没有这行，complete 和 cancel 可能竞态。
        attempt = _ATTEMPTS.get(clean_attempt_id)  # 新增代码+OpenAIAuthAttempt：读取目标 attempt；如果没有这行，无法判断是否存在。
        if attempt is None:  # 新增代码+OpenAIAuthAttempt：处理未知 attempt；如果没有这行，后续访问会 AttributeError。
            raise GuiProviderSettingsError(404, "auth_attempt_not_found", "授权尝试不存在。")  # 新增代码+OpenAIAuthAttempt：返回稳定 404；如果没有这行，前端无法处理错误 id。
        _expire_stale_pending_attempt(attempt, time.time())  # 新增代码+OpenAIAuthAttempt：完成前先处理过期；如果没有这行，过期 attempt 仍可能被完成。
        if attempt.status != "pending":  # 新增代码+OpenAIAuthAttempt：只允许 pending 完成；如果没有这行，cancel/expired 后还能变 complete。
            return _attempt_payload(attempt)  # 新增代码+OpenAIAuthAttempt：终态直接返回；如果没有这行，重复 complete 会改写状态。
        attempt.status = "complete"  # 新增代码+OpenAIAuthAttempt：把 mock attempt 标记完成；如果没有这行，前端无法进入完成态。
        attempt.message = "mock_completed"  # 新增代码+OpenAIAuthAttempt：记录 mock 完成消息；如果没有这行，日志无法区分真实/模拟完成。
    settings = load_provider_settings(workspace)  # 新增代码+OpenAIAuthAttempt：读取 provider settings；如果没有这行，mock 完成无法刷新 catalog。
    auth = settings.setdefault("auth", {})  # 新增代码+OpenAIAuthAttempt：获取 auth 区块；如果没有这行，无法保存 mock 连接状态。
    auth["openai"] = {"type": "oauth_mock", "auth_method_id": attempt.auth_method_id, "updated_at": time.time()}  # 新增代码+OpenAIAuthAttempt：只保存非敏感 mock auth 标记；如果没有这行，catalog 不知道 mock 已完成。
    save_provider_settings(workspace, settings)  # 新增代码+OpenAIAuthAttempt：保存主配置；如果没有这行，刷新或重启后 mock 状态会丢失。
    return _attempt_payload(attempt)  # 新增代码+OpenAIAuthAttempt：返回完成 payload；如果没有这行，bridge 无法响应前端。
# 新增代码+OpenAIAuthAttempt：函数段结束，complete_provider_auth_attempt 到此结束；如果没有边界说明，初学者不易看出它不保存真实 token。


def complete_real_provider_auth_attempt_with_tokens(workspace: str | Path, attempt_id: Any, callback_state: Any, token_payload: dict[str, Any]) -> dict[str, Any]:  # 新增代码+OpenAIRealOAuthAttempt：函数段开始，用真实 OAuth token 完成 attempt；如果没有这段，本机 callback 无法把授权变成连接状态。
    clean_attempt_id = str(attempt_id or "").strip()  # 新增代码+OpenAIRealOAuthAttempt：清理 attempt id；如果没有这行，空白 id 可能访问 registry。
    clean_callback_state = str(callback_state or "").strip()  # 新增代码+OpenAIRealOAuthAttempt：清理回调 state；如果没有这行，空白或 None 会导致比较不稳定。
    with _ATTEMPT_LOCK:  # 新增代码+OpenAIRealOAuthAttempt：锁住 registry 读取和状态更新；如果没有这行，callback/cancel 可能竞态。
        attempt = _ATTEMPTS.get(clean_attempt_id)  # 新增代码+OpenAIRealOAuthAttempt：读取目标 attempt；如果没有这行，无法判断是否存在。
        oauth_secret = _ATTEMPT_OAUTH_SECRETS.get(clean_attempt_id)  # 新增代码+OpenAIRealOAuthAttempt：读取后端私有 OAuth state/verifier；如果没有这行，无法校验回调来源。
        if attempt is None:  # 新增代码+OpenAIRealOAuthAttempt：处理未知 attempt；如果没有这行，后续访问会 AttributeError。
            raise GuiProviderSettingsError(404, "auth_attempt_not_found", "授权尝试不存在。")  # 新增代码+OpenAIRealOAuthAttempt：返回稳定 404；如果没有这行，callback 无法解释旧 id。
        _expire_stale_pending_attempt(attempt, time.time())  # 新增代码+OpenAIRealOAuthAttempt：完成前先处理过期；如果没有这行，过期 attempt 仍可能被完成。
        if attempt.status != "pending":  # 新增代码+OpenAIRealOAuthAttempt：只允许 pending 完成；如果没有这行，cancel/expired 后还能变 complete。
            return _attempt_payload(attempt)  # 新增代码+OpenAIRealOAuthAttempt：终态直接返回；如果没有这行，重复 callback 会改写状态。
        if oauth_secret is None:  # 新增代码+OpenAIRealOAuthAttempt：真实完成必须存在私有 OAuth 数据；如果没有这行，mock attempt 可能被当成真实完成。
            raise GuiProviderSettingsError(400, "openai_oauth_attempt_secret_missing", "授权尝试缺少真实 OAuth 私有状态。")  # 新增代码+OpenAIRealOAuthAttempt：返回结构化私有状态缺失错误；如果没有这行，排查不知道是 registry 丢失。
        if clean_callback_state != oauth_secret.oauth_state:  # 新增代码+OpenAIRealOAuthAttempt：校验回调 state 必须匹配 start；如果没有这行，错误浏览器回调可能写入 token。
            raise GuiProviderSettingsError(400, "openai_oauth_state_mismatch", "OpenAI OAuth state 不匹配。")  # 新增代码+OpenAIRealOAuthAttempt：返回稳定 state 错误；如果没有这行，测试无法证明错配会失败。
        attempt.status = "complete"  # 新增代码+OpenAIRealOAuthAttempt：把真实 attempt 标记完成；如果没有这行，前端仍会显示等待中。
        attempt.message = "real_oauth_completed"  # 新增代码+OpenAIRealOAuthAttempt：记录真实完成消息；如果没有这行，日志无法区分真实和 mock。
        _ATTEMPT_OAUTH_SECRETS.pop(clean_attempt_id, None)  # 新增代码+OpenAIRealOAuthAttempt：完成后移除私有 verifier/state；如果没有这行，进程内会残留敏感交换材料。
    store_openai_oauth_token_response(workspace, token_payload, attempt.auth_method_id, oauth_secret.oauth_client_source)  # 新增代码+OpenAIRealOAuthAttempt：把 token 安全保存成 secret_refs；如果没有这行，OpenAI provider 不会变成真实连接状态。
    return _attempt_payload(attempt)  # 新增代码+OpenAIRealOAuthAttempt：返回完成 payload；如果没有这行，callback 无法通知前端。
# 新增代码+OpenAIRealOAuthAttempt：函数段结束，complete_real_provider_auth_attempt_with_tokens 到此结束；如果没有边界说明，初学者不易看出它负责真实完成。


def cancel_provider_auth_attempt(attempt_id: Any) -> dict[str, Any]:  # 新增代码+OpenAIAuthAttempt：函数段开始，取消 auth attempt；如果没有这段，关闭 wizard 后后端仍会 pending。
    clean_attempt_id = str(attempt_id or "").strip()  # 新增代码+OpenAIAuthAttempt：清理 attempt id；如果没有这行，空白 id 可能访问 registry。
    with _ATTEMPT_LOCK:  # 新增代码+OpenAIAuthAttempt：锁住 registry 更新；如果没有这行，cancel 和 status 可能竞态。
        attempt = _ATTEMPTS.get(clean_attempt_id)  # 新增代码+OpenAIAuthAttempt：读取目标 attempt；如果没有这行，无法判断是否存在。
        if attempt is None:  # 新增代码+OpenAIAuthAttempt：处理未知 attempt；如果没有这行，后续访问会 AttributeError。
            return _attempt_payload(_expired_placeholder_attempt(clean_attempt_id, "auth_attempt_not_found"))  # 修改代码+OpenAIAuthAttemptTail：未知 cancel 返回 expired 占位；如果没有这行，关闭旧弹窗可能因为 404 变成可见错误。
        if attempt.status == "pending":  # 新增代码+OpenAIAuthAttempt：只把 pending 取消成 expired；如果没有这行，complete 状态可能被取消覆盖。
            attempt.status = "expired"  # 新增代码+OpenAIAuthAttempt：取消统一表现为 expired；如果没有这行，状态 enum 会多出 cancel 分支。
            attempt.message = "cancelled_by_user"  # 新增代码+OpenAIAuthAttempt：保存用户取消原因；如果没有这行，UI 无法显示明确取消状态。
            _ATTEMPT_OAUTH_SECRETS.pop(clean_attempt_id, None)  # 新增代码+OpenAIRealOAuthAttempt：取消时清理真实 OAuth 私有状态；如果没有这行，verifier/state 会在进程里残留。
        return _attempt_payload(attempt)  # 新增代码+OpenAIAuthAttempt：返回取消后的 payload；如果没有这行，前端拿不到终态。
# 新增代码+OpenAIAuthAttempt：函数段结束，cancel_provider_auth_attempt 到此结束；如果没有边界说明，初学者不易看出它只取消状态机。
