"""OpenHarness Desktop provider auth-attempt 状态机。"""  # 新增代码+OpenAIAuthAttempt：说明本模块负责连接尝试生命周期；如果没有这行，维护者容易把它误当真实 OAuth token 管理器。

from __future__ import annotations  # 新增代码+OpenAIAuthAttempt：启用延迟类型解析；如果没有这行，类型引用在旧解释器兼容性上更脆弱。

import http.server  # 新增代码+DirectOAuthCallback：启动本机 localhost OAuth callback server；如果没有这行代码，浏览器授权完成后没有后端接收 code。
import os  # 新增代码+DirectOAuthCallback：读取可选 OAuth callback 端口；如果没有这行代码，测试和高级用户无法避开端口冲突。
import threading  # 新增代码+OpenAIAuthAttempt：保护内存 attempt registry；如果没有这行，并发 start/status/cancel 可能读写错乱。
import time  # 新增代码+OpenAIAuthAttempt：记录 created/expires/updated 时间；如果没有这行，attempt 无法过期或排序。
import urllib.parse  # 新增代码+DirectOAuthCallback：解析浏览器 callback URL query；如果没有这行代码，无法读取 code/state。
import uuid  # 新增代码+OpenAIAuthAttempt：生成不可猜测 attempt id；如果没有这行，多个连接尝试 id 容易冲突。
from dataclasses import asdict, dataclass  # 新增代码+OpenAIAuthAttempt：定义 attempt 结构和安全序列化；如果没有这行，payload 字段会散成手写 dict。
from pathlib import Path  # 新增代码+OpenAIAuthAttempt：标注 workspace 路径类型；如果没有这行，Windows 路径语义不清楚。
from typing import Any  # 新增代码+OpenAIAuthAttempt：标注 JSON-like payload；如果没有这行，动态 bridge body 类型边界不清楚。

from learning_agent.app.gui_codex_auth_bridge import CodexAuthBridge  # 新增代码+CodexLoginAttempt：启动并轮询官方 Codex CLI 登录；如果没有这行，browser 方法只能停留在 mock auth-attempt。
from learning_agent.app.gui_provider_openai_auth_config import build_openai_auth_config  # 新增代码+OpenAIAuthAttempt：复用 OpenAI auth 配置门禁；如果没有这行，mock/real 边界会和配置 helper 分裂。
from learning_agent.app.gui_provider_openai_oauth import DEFAULT_CALLBACK_PATH, DEFAULT_CALLBACK_PORT, OpenAIProviderOAuthAttempt, callback_redirect_uri  # 修改代码+DirectOAuthCallback：复用 direct OAuth PKCE/state/authorize URL 和 callback URL helper；如果没有这行代码，OpenHarness 只能继续返回 mock 链接。
from learning_agent.app.gui_provider_settings import GuiProviderSettingsError, _clear_model_failures_in_settings, clear_provider_disabled_override, load_provider_settings, save_provider_settings  # 修改代码+ModelFailureState：复用 provider 设置读写、disabled 清理、模型失败清理和结构化错误；如果没有这行，OAuth 重连后旧模型失败标记不会被清掉。


AUTH_ATTEMPT_SCHEMA_VERSION = 3  # 新增代码+OpenAIAuthAttempt：声明 auth-attempt payload 版本；如果没有这行，前后端无法判断状态机合同。
OPENAI_AUTH_ATTEMPT_METHODS = {"chatgpt-browser", "chatgpt-headless"}  # 新增代码+OpenAIAuthAttempt：限制稳定 V1 只支持两个 OpenAI OAuth mock 方法；如果没有这行，任意方法可能进入 attempt 状态机。
AUTH_ATTEMPT_TTL_SECONDS = 600.0  # 新增代码+OpenAIAuthAttempt：定义 mock attempt 过期时间；如果没有这行，pending 尝试会永久留在内存。
_ATTEMPT_LOCK = threading.Lock()  # 新增代码+OpenAIAuthAttempt：保护全局 attempt registry；如果没有这行，多请求可能同时修改同一 attempt。
_ATTEMPTS: dict[str, "GuiProviderAuthAttempt"] = {}  # 新增代码+OpenAIAuthAttempt：保存当前进程内 auth attempts；如果没有这行，status/cancel 找不到 start 创建的尝试。
_DIRECT_OAUTH_ATTEMPTS: dict[str, OpenAIProviderOAuthAttempt] = {}  # 新增代码+DirectOAuthAttempt：保存 direct OAuth 后端状态机对象；如果没有这行代码，callback/status 无法关联 PKCE、state 和 token store。
_DIRECT_OAUTH_CALLBACK_SERVERS: dict[str, http.server.HTTPServer] = {}  # 新增代码+DirectOAuthCallback：保存 direct OAuth callback server；如果没有这行代码，cancel 无法关闭正在等待的 localhost server。


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
            if attempt.mode == "direct_oauth_browser":  # 新增代码+DirectOAuthCallback：direct OAuth 旧 attempt 被替代时关闭旧 callback server；如果没有这行代码，旧 server 会继续占用端口。
                _shutdown_direct_oauth_callback_server(attempt.attempt_id)  # 新增代码+DirectOAuthCallback：释放旧 direct OAuth server；如果没有这行代码，新授权可能因端口占用失败。
# 新增代码+OpenAIAuthAttempt：函数段结束，_cancel_existing_pending_for_provider 到此结束；如果没有边界说明，初学者不易看出它只清理旧 pending。


def _mock_attempt_fields(auth_method_id: str, attempt_id: str, base_url: str) -> tuple[str, str, str, str, bool]:  # 新增代码+OpenAIAuthAttempt：函数段开始，生成 mock 授权展示字段；如果没有这段，browser/headless 文案会散落。
    safe_base_url = base_url.rstrip("/")  # 新增代码+OpenAIAuthAttempt：去掉 base URL 尾部斜杠；如果没有这行，拼接 URL 可能出现双斜杠。
    if auth_method_id == "chatgpt-headless":  # 新增代码+OpenAIAuthAttempt：处理 headless 设备码 flow；如果没有这行，设备码和浏览器说明无法区分。
        display_code = f"MOCK-OPENAI-{attempt_id[-6:].upper()}"  # 新增代码+OpenAIAuthAttempt：生成可复制 mock 设备码；如果没有这行，headless 等待页没有用户输入内容。
        return f"{safe_base_url}/mock/openai/device", "访问此链接并输入设备码，以完成 mock ChatGPT 授权。", display_code, "device_code", True  # 新增代码+OpenAIAuthAttempt：返回 headless mock 展示字段；如果没有这行，前端无法显示设备码流程。
    return f"{safe_base_url}/mock/openai/browser", "在浏览器中完成 mock ChatGPT 授权。", "Complete authorization in your browser. This window will close automatically.", "browser_instruction", False  # 新增代码+OpenAIAuthAttempt：返回 browser mock 展示字段；如果没有这行，前端无法显示浏览器登录流程。
# 新增代码+OpenAIAuthAttempt：函数段结束，_mock_attempt_fields 到此结束；如果没有边界说明，初学者不易看出它只生成展示字段。


def _codex_cli_attempt_fields() -> tuple[str, str, str, str, bool]:  # 新增代码+CodexLoginAttempt：函数段开始，生成官方 Codex 登录等待页字段；如果没有这段，codex_cli_login 文案会散落在 start/status 里。
    return "", "在浏览器中完成官方 Codex/ChatGPT 登录；OpenHarness 不读取 Codex token。", "Complete authorization in your browser. This window will close automatically.", "browser_instruction", False  # 新增代码+CodexLoginAttempt：返回无 URL 的浏览器说明字段；如果没有这行，前端会要求一个不存在的授权链接。
# 新增代码+CodexLoginAttempt：函数段结束，_codex_cli_attempt_fields 到此结束；如果没有边界说明，初学者不易看出它只生成展示字段。


def _direct_oauth_attempt_fields(oauth_attempt: OpenAIProviderOAuthAttempt) -> tuple[str, str, str, str, bool]:  # 新增代码+DirectOAuthAttempt：函数段开始，生成 direct OAuth 等待页字段；如果没有这段代码，真实授权 URL 会散落在 start 函数里。
    return oauth_attempt.authorize_url, "在浏览器中完成 OpenHarness experimental direct OAuth；token 只保存到 OS 加密存储。", "Complete authorization in your browser. This window will close automatically.", "browser_instruction", False  # 新增代码+DirectOAuthAttempt：返回授权 URL 和安全说明；如果没有这行代码，前端无法打开 OpenAI 登录页或知道不会展示 token。
# 新增代码+DirectOAuthAttempt：函数段结束，_direct_oauth_attempt_fields 到此结束；如果没有边界说明，初学者不易看出它只生成展示字段。


def _direct_oauth_callback_port() -> int:  # 新增代码+DirectOAuthCallback：函数段开始，读取 direct OAuth callback 端口；如果没有这段代码，测试和用户无法避开 1455 端口冲突。
    raw_port = os.environ.get("OPENHARNESS_OPENAI_OAUTH_CALLBACK_PORT", str(DEFAULT_CALLBACK_PORT)).strip()  # 新增代码+DirectOAuthCallback：读取端口环境变量并默认 1455；如果没有这行代码，回调端口只能硬编码。
    try:  # 新增代码+DirectOAuthCallback：捕获非法端口文本；如果没有这行代码，坏环境变量会让 GUI 启动失败。
        return int(raw_port)  # 新增代码+DirectOAuthCallback：返回整数端口；如果没有这行代码，HTTPServer 无法绑定端口。
    except ValueError:  # 新增代码+DirectOAuthCallback：处理非数字端口；如果没有这行代码，错误配置不会有清晰兜底。
        return DEFAULT_CALLBACK_PORT  # 新增代码+DirectOAuthCallback：非法值回退默认端口；如果没有这行代码，用户填错端口会直接崩溃。
# 新增代码+DirectOAuthCallback：函数段结束，_direct_oauth_callback_port 到此结束；如果没有边界说明，用户不容易看出它只读配置。


def _flat_query(query: dict[str, list[str]]) -> dict[str, str]:  # 新增代码+DirectOAuthCallback：函数段开始，把 parse_qs 结果转成单值 dict；如果没有这段代码，OAuth attempt 无法直接读取 code/state。
    return {str(key): str(values[0]) if values else "" for key, values in query.items()}  # 新增代码+DirectOAuthCallback：只取每个 query 参数的第一个值；如果没有这行代码，state/code 会变成列表而无法校验。
# 新增代码+DirectOAuthCallback：函数段结束，_flat_query 到此结束；如果没有边界说明，用户不容易看出它只处理 query 形状。


def _write_html_response(handler: http.server.BaseHTTPRequestHandler, html: str) -> None:  # 新增代码+DirectOAuthCallback：函数段开始，向浏览器写 callback HTML；如果没有这段代码，成功或失败页无法显示。
    raw = html.encode("utf-8")  # 新增代码+DirectOAuthCallback：把 HTML 编码为 UTF-8 字节；如果没有这行代码，中文或英文页面无法写入 socket。
    handler.send_response(200)  # 新增代码+DirectOAuthCallback：返回 HTTP 200；如果没有这行代码，浏览器可能显示连接错误。
    handler.send_header("Content-Type", "text/html; charset=utf-8")  # 新增代码+DirectOAuthCallback：声明 HTML 和 UTF-8；如果没有这行代码，浏览器可能乱码。
    handler.send_header("Content-Length", str(len(raw)))  # 新增代码+DirectOAuthCallback：声明响应长度；如果没有这行代码，部分浏览器可能等待更多字节。
    handler.end_headers()  # 新增代码+DirectOAuthCallback：结束响应头；如果没有这行代码，响应体不会开始。
    handler.wfile.write(raw)  # 新增代码+DirectOAuthCallback：写出 HTML 页面；如果没有这行代码，浏览器看不到授权结果。
# 新增代码+DirectOAuthCallback：函数段结束，_write_html_response 到此结束；如果没有边界说明，用户不容易看出它只写页面不含 token。


def _shutdown_direct_oauth_callback_server(attempt_id: str) -> None:  # 新增代码+DirectOAuthCallback：函数段开始，关闭 direct OAuth callback server；如果没有这段代码，完成或取消后 1455 端口可能残留占用。
    server = _DIRECT_OAUTH_CALLBACK_SERVERS.pop(attempt_id, None)  # 新增代码+DirectOAuthCallback：从 registry 取出并移除 server；如果没有这行代码，重复关闭会访问旧对象。
    if server is None:  # 新增代码+DirectOAuthCallback：处理没有 server 的场景；如果没有这行代码，mock/codex cancel 会抛错。
        return  # 新增代码+DirectOAuthCallback：无 server 时直接返回；如果没有这行代码，函数会继续访问空对象。
    server.shutdown()  # 新增代码+DirectOAuthCallback：停止 serve_forever 循环；如果没有这行代码，后台线程会继续占用端口。
    server.server_close()  # 新增代码+DirectOAuthCallback：关闭监听 socket；如果没有这行代码，端口可能短时间无法复用。
# 新增代码+DirectOAuthCallback：函数段结束，_shutdown_direct_oauth_callback_server 到此结束；如果没有边界说明，用户不容易看出它只清理本地 server。


def _token_ref_from_oauth_attempt(oauth_attempt: OpenAIProviderOAuthAttempt) -> str:  # 新增代码+DirectOAuthCallback：函数段开始，读取 direct OAuth token_ref；如果没有这段代码，callback 完成后 provider catalog 无法关联 token store。
    token_ref_for = getattr(oauth_attempt.token_store, "token_ref_for", None)  # 新增代码+DirectOAuthCallback：读取 token store 的 token_ref helper；如果没有这行代码，不同 store 无法提供稳定引用。
    if callable(token_ref_for):  # 新增代码+DirectOAuthCallback：确认 helper 可调用；如果没有这行代码，测试替身可能导致 TypeError。
        return str(token_ref_for("openai"))  # 新增代码+DirectOAuthCallback：使用 store 自己的安全 token_ref；如果没有这行代码，provider 设置和 token store 可能不一致。
    return "provider_oauth:openai"  # 新增代码+DirectOAuthCallback：没有 helper 时使用安全兜底引用；如果没有这行代码，callback 完成后无法保存连接记录。
# 新增代码+DirectOAuthCallback：函数段结束，_token_ref_from_oauth_attempt 到此结束；如果没有边界说明，用户不容易看出它不读取 raw token。


def _start_direct_oauth_callback_server(workspace: str | Path, attempt: GuiProviderAuthAttempt, oauth_attempt: OpenAIProviderOAuthAttempt, host: str = "127.0.0.1", port: int | None = None) -> None:  # 新增代码+DirectOAuthCallback：函数段开始，启动 localhost OAuth callback server；如果没有这段代码，浏览器授权回来没有接收方。
    bind_port = DEFAULT_CALLBACK_PORT if port is None else int(port)  # 新增代码+DirectOAuthCallback：确定实际监听端口；如果没有这行代码，HTTPServer 不能绑定可配置端口。
    class DirectOAuthCallbackHandler(http.server.BaseHTTPRequestHandler):  # 新增代码+DirectOAuthCallback：类段开始，处理浏览器 OAuth callback；如果没有这个类，HTTPServer 不知道如何响应 GET。
        def log_message(self, _format: str, *_args: Any) -> None:  # 新增代码+DirectOAuthCallback：函数段开始，关闭默认 HTTP 访问日志；如果没有这段代码，终端会出现噪音。
            return  # 新增代码+DirectOAuthCallback：忽略日志输出；如果没有这行代码，log_message 仍可能写到 stderr。
        # 新增代码+DirectOAuthCallback：函数段结束，DirectOAuthCallbackHandler.log_message 到此结束；如果没有边界说明，用户不容易看出它只静音日志。

        def do_GET(self) -> None:  # 新增代码+DirectOAuthCallback：函数段开始，处理 OpenAI 授权回调 GET；如果没有这段代码，浏览器会收到 501。
            parsed = urllib.parse.urlparse(self.path)  # 新增代码+DirectOAuthCallback：解析 callback 路径和 query；如果没有这行代码，无法区分 /auth/callback 和其它路径。
            if parsed.path != DEFAULT_CALLBACK_PATH:  # 新增代码+DirectOAuthCallback：只接受预期 callback 路径；如果没有这行代码，任意路径都可能触发状态变化。
                _write_html_response(self, "<!doctype html><html><body><h1>Authorization Failed</h1><p>Unexpected callback path.</p></body></html>")  # 新增代码+DirectOAuthCallback：返回安全失败页；如果没有这行代码，错误路径没有用户反馈。
                return  # 新增代码+DirectOAuthCallback：路径错误后停止处理；如果没有这行代码，错误请求仍会进入 token exchange。
            html = oauth_attempt.handle_callback(_flat_query(urllib.parse.parse_qs(parsed.query)))  # 新增代码+DirectOAuthCallback：交给 OAuth 状态机校验 state 并换 token；如果没有这行代码，callback 不会完成登录。
            if oauth_attempt.status == "complete":  # 新增代码+DirectOAuthCallback：成功保存 token 后写 provider 连接记录；如果没有这行代码，设置页仍会显示未连接。
                save_direct_oauth_provider_connection(workspace, token_ref=_token_ref_from_oauth_attempt(oauth_attempt), auth_method_id=attempt.auth_method_id)  # 新增代码+DirectOAuthCallback：只保存 token_ref 到 provider settings；如果没有这行代码，catalog 无法显示 direct OAuth connected。
            with _ATTEMPT_LOCK:  # 新增代码+DirectOAuthCallback：锁住 GUI attempt 状态同步；如果没有这行代码，status 轮询可能读到半更新。
                attempt.status = oauth_attempt.status  # 新增代码+DirectOAuthCallback：同步 complete/failed/expired 状态；如果没有这行代码，等待页不会自动结束。
                attempt.message = oauth_attempt.message  # 新增代码+DirectOAuthCallback：同步安全消息；如果没有这行代码，失败原因不会进入轮询结果。
            _write_html_response(self, html)  # 新增代码+DirectOAuthCallback：把成功/失败页面返回浏览器；如果没有这行代码，用户不知道授权结果。
            threading.Thread(target=_shutdown_direct_oauth_callback_server, args=(attempt.attempt_id,), daemon=True).start()  # 新增代码+DirectOAuthCallback：异步关闭 callback server；如果没有这行代码，端口会继续被占用。
        # 新增代码+DirectOAuthCallback：函数段结束，DirectOAuthCallbackHandler.do_GET 到此结束；如果没有边界说明，用户不容易看出 token 不会写到响应里。
    # 新增代码+DirectOAuthCallback：类段结束，DirectOAuthCallbackHandler 到此结束；如果没有边界说明，用户不容易看出它只服务一次 OAuth 回调。

    server = http.server.ThreadingHTTPServer((host, bind_port), DirectOAuthCallbackHandler)  # 新增代码+DirectOAuthCallback：绑定本机 callback server；如果没有这行代码，浏览器 redirect_uri 无法连接。
    _DIRECT_OAUTH_CALLBACK_SERVERS[attempt.attempt_id] = server  # 新增代码+DirectOAuthCallback：把 server 放进 registry；如果没有这行代码，cancel 无法停止监听。
    threading.Thread(target=server.serve_forever, daemon=True).start()  # 新增代码+DirectOAuthCallback：后台等待浏览器回调；如果没有这行代码，start 请求会阻塞 GUI。
# 新增代码+DirectOAuthCallback：函数段结束，_start_direct_oauth_callback_server 到此结束；如果没有边界说明，用户不容易看出它只启动本地 server。


def _refresh_codex_cli_attempt(attempt: GuiProviderAuthAttempt) -> GuiProviderAuthAttempt:  # 新增代码+CodexLoginAttempt：函数段开始，轮询官方 Codex 登录状态并更新 attempt；如果没有这段，浏览器登录完成后等待页不会自动关闭。
    if attempt.mode != "codex_cli_login" or attempt.status != "pending":  # 新增代码+CodexLoginAttempt：只刷新官方登录的 pending attempt；如果没有这行，mock 或终态 attempt 会被错误改写。
        return attempt  # 新增代码+CodexLoginAttempt：非目标状态原样返回；如果没有这行，函数会继续无意义调用 CLI。
    codex_status = CodexAuthBridge().login_status()  # 新增代码+CodexLoginAttempt：调用官方 status 命令检查登录是否完成；如果没有这行，等待页无法知道用户是否已授权。
    if codex_status.available and codex_status.connected:  # 新增代码+CodexLoginAttempt：判断 Codex CLI 已登录；如果没有这行，complete 状态无法触发。
        attempt.status = "complete"  # 新增代码+CodexLoginAttempt：把等待页标记完成；如果没有这行，前端会继续轮询。
        attempt.message = "codex_cli_login_complete"  # 新增代码+CodexLoginAttempt：保存完成消息；如果没有这行，日志无法区分官方登录完成。
    elif not codex_status.available:  # 新增代码+CodexLoginAttempt：判断 Codex CLI 不可用；如果没有这行，CLI 缺失会一直 pending。
        attempt.status = "failed"  # 新增代码+CodexLoginAttempt：把缺 CLI 标记失败；如果没有这行，用户不知道需要安装 Codex。
        attempt.message = codex_status.message  # 新增代码+CodexLoginAttempt：保存缺失原因；如果没有这行，前端只有泛化失败。
    return attempt  # 新增代码+CodexLoginAttempt：返回更新后的 attempt；如果没有这行，调用方拿不到状态变化。
# 新增代码+CodexLoginAttempt：函数段结束，_refresh_codex_cli_attempt 到此结束；如果没有边界说明，初学者不易看出它只轮询官方登录。


def _refresh_direct_oauth_attempt(attempt: GuiProviderAuthAttempt) -> GuiProviderAuthAttempt:  # 新增代码+DirectOAuthAttempt：函数段开始，把 direct OAuth 内部状态同步到 GUI attempt；如果没有这段代码，callback 成功或失败后前端轮询看不到变化。
    if attempt.mode != "direct_oauth_browser":  # 新增代码+DirectOAuthAttempt：只处理 direct OAuth browser attempt；如果没有这行代码，mock/codex attempt 可能被错误同步。
        return attempt  # 新增代码+DirectOAuthAttempt：非目标模式原样返回；如果没有这行代码，函数会继续访问不存在的 direct OAuth 对象。
    oauth_attempt = _DIRECT_OAUTH_ATTEMPTS.get(attempt.attempt_id)  # 新增代码+DirectOAuthAttempt：读取后端 OAuth 状态对象；如果没有这行代码，无法知道 callback 是否完成。
    if oauth_attempt is None:  # 新增代码+DirectOAuthAttempt：处理进程重启或状态丢失；如果没有这行代码，后续访问会 AttributeError。
        if attempt.status == "pending":  # 新增代码+DirectOAuthAttempt：只收敛仍在等待的 orphan attempt；如果没有这行代码，已完成状态可能被覆盖。
            attempt.status = "expired"  # 新增代码+DirectOAuthAttempt：把孤儿 attempt 变成 expired；如果没有这行代码，前端可能永久等待。
            attempt.message = "direct_oauth_attempt_not_found"  # 新增代码+DirectOAuthAttempt：记录状态丢失原因；如果没有这行代码，排查时看不出是进程状态丢失。
        return attempt  # 新增代码+DirectOAuthAttempt：返回收敛后的 attempt；如果没有这行代码，调用方拿不到结果。
    if attempt.status == "pending":  # 新增代码+DirectOAuthAttempt：只在等待态同步内部状态；如果没有这行代码，终态 attempt 可能被重复改写。
        oauth_attempt._expire_if_needed()  # 新增代码+DirectOAuthAttempt：让内部状态先按时间过期；如果没有这行代码，GUI attempt 可能比 OAuth attempt 更晚过期。
        attempt.status = oauth_attempt.status  # 新增代码+DirectOAuthAttempt：同步 pending/complete/failed/expired；如果没有这行代码，前端轮询看不到 callback 结果。
        attempt.message = oauth_attempt.message  # 新增代码+DirectOAuthAttempt：同步安全消息；如果没有这行代码，前端没有失败或完成说明。
    return attempt  # 新增代码+DirectOAuthAttempt：返回同步后的 attempt；如果没有这行代码，status/cancel 无法输出最新状态。
# 新增代码+DirectOAuthAttempt：函数段结束，_refresh_direct_oauth_attempt 到此结束；如果没有边界说明，用户不容易看出它只做状态同步。


def start_provider_auth_attempt(workspace: str | Path, provider_id: Any, auth_method_id: Any) -> dict[str, Any]:  # 新增代码+OpenAIAuthAttempt：函数段开始，启动 provider auth attempt；如果没有这段，browser/headless 连接按钮没有后端状态机。
    clean_provider_id, clean_auth_method_id = _validate_openai_attempt(provider_id, auth_method_id)  # 新增代码+OpenAIAuthAttempt：校验并清洗 provider/method；如果没有这行，非法请求会进入 registry。
    config = build_openai_auth_config()  # 新增代码+OpenAIAuthAttempt：读取 OpenAI auth 配置；如果没有这行，mock/real 门禁不会生效。
    now = time.time()  # 新增代码+OpenAIAuthAttempt：记录当前时间；如果没有这行，created/expires 无法稳定生成。
    attempt_id = _new_attempt_id()  # 新增代码+OpenAIAuthAttempt：生成新 attempt id；如果没有这行，前端无法轮询。
    if config.auth_mode == "codex_cli" and clean_auth_method_id == "chatgpt-browser":  # 新增代码+CodexLoginAttempt：官方模式下 browser 方法启动 codex login；如果没有这行，用户仍只能看到 mock 授权。
        clear_provider_disabled_override(workspace, clean_provider_id)  # 新增代码+ProviderReconnect：用户主动重新连接时解除本地 disabled 覆盖；如果没有这行，pending 登录完成后 catalog 仍会被断开状态挡住。
        bridge = CodexAuthBridge()  # 新增代码+CodexLoginAttempt：创建官方 Codex CLI 桥；如果没有这行，无法启动或查询 Codex 登录。
        start_result = bridge.start_login()  # 新增代码+CodexLoginAttempt：启动官方 codex login；如果没有这行，浏览器 OAuth 不会打开。
        codex_status = bridge.login_status()  # 新增代码+CodexLoginAttempt：启动后立即读取当前登录状态；如果没有这行，已登录用户也会多等一轮。
        url, instructions, display_code, display_code_kind, copyable = _codex_cli_attempt_fields()  # 新增代码+CodexLoginAttempt：生成官方等待页展示字段；如果没有这行，前端没有可读说明。
        attempt_status = "complete" if codex_status.available and codex_status.connected else "pending"  # 新增代码+CodexLoginAttempt：已登录则直接完成，否则等待浏览器授权；如果没有这行，已登录用户也会停在 pending。
        attempt_status = "failed" if not bool(start_result.get("ok", False)) else attempt_status  # 新增代码+CodexLoginAttempt：启动失败时标记 failed；如果没有这行，Codex CLI 缺失会伪装成 pending。
        attempt_message = "codex_cli_login_complete" if attempt_status == "complete" else str(start_result.get("message", codex_status.message))  # 新增代码+CodexLoginAttempt：保存安全短消息；如果没有这行，等待页没有状态说明。
        if attempt_status == "complete":  # 新增代码+ProviderReconnect：官方登录已经完成时清理本地断开覆盖；如果没有这行，用户断开后再连接仍会被 disabled 状态挡住。
            clear_provider_disabled_override(workspace, clean_provider_id)  # 新增代码+ProviderReconnect：删除 OpenHarness 本地 disabled 记录；如果没有这行，刷新 catalog 仍显示 OpenAI 未连接。
        attempt = GuiProviderAuthAttempt(attempt_id=attempt_id, provider_id=clean_provider_id, auth_method_id=clean_auth_method_id, mode="codex_cli_login", url=url, instructions=instructions, display_code=display_code, display_code_kind=display_code_kind, display_code_copyable=copyable, status=attempt_status, message=attempt_message, created_at=now, expires_at=now + AUTH_ATTEMPT_TTL_SECONDS)  # 新增代码+CodexLoginAttempt：创建官方 Codex 登录 attempt；如果没有这行，前端无法轮询官方登录状态。
        with _ATTEMPT_LOCK:  # 新增代码+CodexLoginAttempt：锁住 registry 写入；如果没有这行，并发 start/status 可能读到半状态。
            _cancel_existing_pending_for_provider(clean_provider_id)  # 新增代码+CodexLoginAttempt：取消同 provider 旧 pending；如果没有这行，多个 OpenAI 登录弹窗会冲突。
            _ATTEMPTS[attempt_id] = attempt  # 新增代码+CodexLoginAttempt：保存官方登录 attempt；如果没有这行，status/cancel 找不到它。
        return _attempt_payload(attempt)  # 新增代码+CodexLoginAttempt：返回官方登录 payload；如果没有这行，bridge 无法响应前端。
    if config.auth_mode == "direct_oauth" and clean_auth_method_id == "chatgpt-browser":  # 新增代码+DirectOAuthAttempt：实验 direct OAuth 模式下 browser 方法返回真实授权 URL；如果没有这行代码，用户仍会看到 mock 链接。
        callback_port = _direct_oauth_callback_port()  # 新增代码+DirectOAuthCallback：读取本次 localhost callback 端口；如果没有这行代码，授权 URL 和 server 端口无法保持一致。
        redirect_uri = callback_redirect_uri(host="localhost", port=callback_port)  # 新增代码+DirectOAuthCallback：生成浏览器看到的 redirect_uri；如果没有这行代码，OpenAI 授权完成后不知道回调地址。
        oauth_attempt = OpenAIProviderOAuthAttempt(client_id=config.client_id, redirect_uri=redirect_uri)  # 修改代码+DirectOAuthCallback：创建含 PKCE/state/redirect_uri 的 OAuth attempt；如果没有这行代码，授权 URL 无法和 callback server 安全匹配。
        url, instructions, display_code, display_code_kind, copyable = _direct_oauth_attempt_fields(oauth_attempt)  # 新增代码+DirectOAuthAttempt：生成等待页展示字段；如果没有这行代码，前端没有可打开的 OpenAI 授权 URL。
        attempt = GuiProviderAuthAttempt(attempt_id=attempt_id, provider_id=clean_provider_id, auth_method_id=clean_auth_method_id, mode="direct_oauth_browser", url=url, instructions=instructions, display_code=display_code, display_code_kind=display_code_kind, display_code_copyable=copyable, status="pending", message="", created_at=now, expires_at=oauth_attempt.expires_at)  # 新增代码+DirectOAuthAttempt：创建 direct OAuth GUI attempt；如果没有这行代码，前端无法轮询真实授权状态。
        with _ATTEMPT_LOCK:  # 新增代码+DirectOAuthCallback：先取消同 provider 旧 pending；如果没有这行代码，新 server 可能先撞上旧 server 占用端口。
            _cancel_existing_pending_for_provider(clean_provider_id)  # 新增代码+DirectOAuthCallback：释放旧 direct OAuth server 和状态；如果没有这行代码，重复点击连接会失败。
        try:  # 新增代码+DirectOAuthCallback：尝试启动 localhost callback server；如果没有这行代码，端口占用会变成底层 OSError。
            _start_direct_oauth_callback_server(workspace, attempt, oauth_attempt, port=callback_port)  # 新增代码+DirectOAuthCallback：启动本机回调接收器；如果没有这行代码，浏览器授权完成后无法保存 token。
        except OSError as error:  # 新增代码+DirectOAuthCallback：处理端口占用或绑定失败；如果没有这行代码，GUI 会收到泛化 500。
            raise GuiProviderSettingsError(409, "oauth_port_in_use", f"OAuth callback port {callback_port} is not available.") from error  # 新增代码+DirectOAuthCallback：返回结构化端口冲突错误；如果没有这行代码，用户不知道要关闭占用 1455 的程序。
        with _ATTEMPT_LOCK:  # 新增代码+DirectOAuthAttempt：锁住 registry 写入；如果没有这行代码，并发 direct OAuth start 可能覆盖状态。
            _ATTEMPTS[attempt_id] = attempt  # 新增代码+DirectOAuthAttempt：保存 GUI attempt；如果没有这行代码，status/cancel 找不到它。
            _DIRECT_OAUTH_ATTEMPTS[attempt_id] = oauth_attempt  # 新增代码+DirectOAuthAttempt：保存 direct OAuth 内部状态；如果没有这行代码，callback 无法验证 state 或保存 token。
        return _attempt_payload(attempt)  # 新增代码+DirectOAuthAttempt：返回 direct OAuth pending payload；如果没有这行代码，bridge 无法响应前端。
    url, instructions, display_code, display_code_kind, copyable = _mock_attempt_fields(clean_auth_method_id, attempt_id, config.auth_base_url)  # 新增代码+OpenAIAuthAttempt：生成 mock 展示字段；如果没有这行，等待页没有链接和说明。
    attempt = GuiProviderAuthAttempt(attempt_id=attempt_id, provider_id=clean_provider_id, auth_method_id=clean_auth_method_id, mode="mock", url=url, instructions=instructions, display_code=display_code, display_code_kind=display_code_kind, display_code_copyable=copyable, status="pending", message="", created_at=now, expires_at=now + AUTH_ATTEMPT_TTL_SECONDS)  # 新增代码+OpenAIAuthAttempt：创建 pending attempt；如果没有这行，状态机没有核心对象。
    with _ATTEMPT_LOCK:  # 新增代码+OpenAIAuthAttempt：锁住 registry 写入；如果没有这行，并发 start 可能互相覆盖。
        _cancel_existing_pending_for_provider(clean_provider_id)  # 新增代码+OpenAIAuthAttempt：取消同 provider 旧 pending；如果没有这行，多窗口等待状态会冲突。
        _ATTEMPTS[attempt_id] = attempt  # 新增代码+OpenAIAuthAttempt：保存新 attempt；如果没有这行，status/cancel/complete 找不到它。
    return _attempt_payload(attempt)  # 新增代码+OpenAIAuthAttempt：返回 pending payload；如果没有这行，bridge 无法响应前端。
# 新增代码+OpenAIAuthAttempt：函数段结束，start_provider_auth_attempt 到此结束；如果没有边界说明，初学者不易看出它只启动状态机不保存 token。


def get_provider_auth_attempt_status(attempt_id: Any) -> dict[str, Any]:  # 新增代码+OpenAIAuthAttempt：函数段开始，读取 auth attempt 状态；如果没有这段，前端无法轮询等待页。
    clean_attempt_id = str(attempt_id or "").strip()  # 新增代码+OpenAIAuthAttempt：清理 attempt id；如果没有这行，空白 id 可能访问 registry。
    with _ATTEMPT_LOCK:  # 新增代码+OpenAIAuthAttempt：锁住 registry 读取和过期更新；如果没有这行，status 可能读到半更新状态。
        attempt = _ATTEMPTS.get(clean_attempt_id)  # 新增代码+OpenAIAuthAttempt：读取目标 attempt；如果没有这行，无法判断是否存在。
        if attempt is None:  # 新增代码+OpenAIAuthAttempt：处理未知 attempt；如果没有这行，后续访问会 AttributeError。
            return _attempt_payload(_expired_placeholder_attempt(clean_attempt_id, "auth_attempt_not_found"))  # 修改代码+OpenAIAuthAttemptTail：未知 status 返回 expired 占位而不是 404；如果没有这行，旧轮询会把 GUI 带入错误态。
        _expire_stale_pending_attempt(attempt, time.time())  # 新增代码+OpenAIAuthAttempt：按时间自动过期；如果没有这行，超时状态不会更新。
        _refresh_codex_cli_attempt(attempt)  # 新增代码+CodexLoginAttempt：刷新官方 Codex 登录状态；如果没有这行，用户完成浏览器授权后等待页不会自动完成。
        _refresh_direct_oauth_attempt(attempt)  # 新增代码+DirectOAuthAttempt：刷新 direct OAuth callback 状态；如果没有这行代码，真实授权完成后等待页不会自动收敛。
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
    _clear_model_failures_in_settings(settings, "openai")  # 新增代码+ModelFailureState：mock OAuth 重连后清理 OpenAI 旧模型失败；如果没有这行，用户会看到过期失败标记。
    save_provider_settings(workspace, settings)  # 新增代码+OpenAIAuthAttempt：保存主配置；如果没有这行，刷新或重启后 mock 状态会丢失。
    return _attempt_payload(attempt)  # 新增代码+OpenAIAuthAttempt：返回完成 payload；如果没有这行，bridge 无法响应前端。
# 新增代码+OpenAIAuthAttempt：函数段结束，complete_provider_auth_attempt 到此结束；如果没有边界说明，初学者不易看出它不保存真实 token。


def cancel_provider_auth_attempt(attempt_id: Any) -> dict[str, Any]:  # 新增代码+OpenAIAuthAttempt：函数段开始，取消 auth attempt；如果没有这段，关闭 wizard 后后端仍会 pending。
    clean_attempt_id = str(attempt_id or "").strip()  # 新增代码+OpenAIAuthAttempt：清理 attempt id；如果没有这行，空白 id 可能访问 registry。
    with _ATTEMPT_LOCK:  # 新增代码+OpenAIAuthAttempt：锁住 registry 更新；如果没有这行，cancel 和 status 可能竞态。
        attempt = _ATTEMPTS.get(clean_attempt_id)  # 新增代码+OpenAIAuthAttempt：读取目标 attempt；如果没有这行，无法判断是否存在。
        if attempt is None:  # 新增代码+OpenAIAuthAttempt：处理未知 attempt；如果没有这行，后续访问会 AttributeError。
            return _attempt_payload(_expired_placeholder_attempt(clean_attempt_id, "auth_attempt_not_found"))  # 修改代码+OpenAIAuthAttemptTail：未知 cancel 返回 expired 占位；如果没有这行，关闭旧弹窗可能因为 404 变成可见错误。
        if attempt.status == "pending":  # 新增代码+OpenAIAuthAttempt：只把 pending 取消成 expired；如果没有这行，complete 状态可能被取消覆盖。
            attempt.status = "expired"  # 新增代码+OpenAIAuthAttempt：取消统一表现为 expired；如果没有这行，状态 enum 会多出 cancel 分支。
            attempt.message = "cancelled_by_user"  # 新增代码+OpenAIAuthAttempt：保存用户取消原因；如果没有这行，UI 无法显示明确取消状态。
            oauth_attempt = _DIRECT_OAUTH_ATTEMPTS.get(clean_attempt_id)  # 新增代码+DirectOAuthAttempt：读取 direct OAuth 内部状态；如果没有这行代码，关闭弹窗后 callback 仍可能写 token。
            if oauth_attempt is not None:  # 新增代码+DirectOAuthAttempt：只在 direct OAuth attempt 存在时取消；如果没有这行代码，mock/codex 取消会访问空对象。
                oauth_attempt.cancel()  # 新增代码+DirectOAuthAttempt：同步取消内部 OAuth 状态；如果没有这行代码，浏览器稍后回调仍可能被接受。
                _shutdown_direct_oauth_callback_server(clean_attempt_id)  # 新增代码+DirectOAuthCallback：关闭 direct OAuth callback server；如果没有这行代码，取消后端口会继续监听。
        return _attempt_payload(attempt)  # 新增代码+OpenAIAuthAttempt：返回取消后的 payload；如果没有这行，前端拿不到终态。
# 新增代码+OpenAIAuthAttempt：函数段结束，cancel_provider_auth_attempt 到此结束；如果没有边界说明，初学者不易看出它只取消状态机。


def save_direct_oauth_provider_connection(workspace: str | Path, token_ref: Any, auth_method_id: Any = "chatgpt-browser") -> dict[str, Any]:  # 新增代码+DirectOAuthAttempt：函数段开始，保存 direct OAuth 非敏感连接记录；如果没有这段代码，token 加密落盘后 catalog 仍不知道 OpenAI 已连接。
    clean_token_ref = str(token_ref or "").strip()  # 新增代码+DirectOAuthAttempt：清理 token 引用；如果没有这行代码，空白引用可能被当成有效连接。
    if not clean_token_ref:  # 新增代码+DirectOAuthAttempt：拒绝空 token 引用；如果没有这行代码，provider 可能显示 connected 但无法读取 token。
        raise GuiProviderSettingsError(400, "direct_oauth_token_ref_required", "direct OAuth token_ref 不能为空。")  # 新增代码+DirectOAuthAttempt：返回结构化输入错误；如果没有这行代码，前端只能看到泛化失败。
    clean_auth_method_id = str(auth_method_id or "chatgpt-browser").strip() or "chatgpt-browser"  # 新增代码+DirectOAuthAttempt：清理认证方法并默认 browser；如果没有这行代码，落盘记录可能缺少来源方法。
    settings = load_provider_settings(workspace)  # 新增代码+DirectOAuthAttempt：读取 provider 设置；如果没有这行代码，保存连接会覆盖其它 provider 状态。
    auth = settings.setdefault("auth", {})  # 新增代码+DirectOAuthAttempt：获取 auth 配置区块；如果没有这行代码，无法记录 OpenAI 连接状态。
    auth["openai"] = {"type": "oauth_direct", "auth_method_id": clean_auth_method_id, "token_ref": clean_token_ref, "updated_at": time.time()}  # 新增代码+DirectOAuthAttempt：主配置只保存 token_ref，不保存 raw token；如果没有这行代码，GUI 不能识别 direct OAuth 已连接。
    _clear_model_failures_in_settings(settings, "openai")  # 新增代码+ModelFailureState：direct OAuth 重连后清理 OpenAI 旧模型失败；如果没有这行代码，用户换授权后仍会看到旧模型不可用标记。
    save_provider_settings(workspace, settings)  # 新增代码+DirectOAuthAttempt：把非敏感连接记录写入磁盘；如果没有这行代码，重启后连接状态会丢失。
    return {"ok": True, "provider_id": "openai", "source": "direct_oauth_experimental"}  # 新增代码+DirectOAuthAttempt：返回安全摘要；如果没有这行代码，调用方无法确认保存完成。
# 新增代码+DirectOAuthAttempt：函数段结束，save_direct_oauth_provider_connection 到此结束；如果没有边界说明，用户不容易看出它不保存 raw token。
