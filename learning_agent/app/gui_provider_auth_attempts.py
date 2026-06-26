"""OpenHarness Desktop provider auth-attempt 状态机。"""  # 新增代码+OpenAIAuthAttempt：说明本模块负责连接尝试生命周期；如果没有这行，维护者容易把它误当真实 OAuth token 管理器。

from __future__ import annotations  # 新增代码+OpenAIAuthAttempt：启用延迟类型解析；如果没有这行，类型引用在旧解释器兼容性上更脆弱。

import threading  # 新增代码+OpenAIAuthAttempt：保护内存 attempt registry；如果没有这行，并发 start/status/cancel 可能读写错乱。
import time  # 新增代码+OpenAIAuthAttempt：记录 created/expires/updated 时间；如果没有这行，attempt 无法过期或排序。
import uuid  # 新增代码+OpenAIAuthAttempt：生成不可猜测 attempt id；如果没有这行，多个连接尝试 id 容易冲突。
from dataclasses import asdict, dataclass  # 新增代码+OpenAIAuthAttempt：定义 attempt 结构和安全序列化；如果没有这行，payload 字段会散成手写 dict。
from pathlib import Path  # 新增代码+OpenAIAuthAttempt：标注 workspace 路径类型；如果没有这行，Windows 路径语义不清楚。
from typing import Any  # 新增代码+OpenAIAuthAttempt：标注 JSON-like payload；如果没有这行，动态 bridge body 类型边界不清楚。

from learning_agent.app.gui_provider_openai_auth_config import build_openai_auth_config  # 新增代码+OpenAIAuthAttempt：复用 OpenAI auth 配置门禁；如果没有这行，mock/real 边界会和配置 helper 分裂。
from learning_agent.app.gui_provider_settings import GuiProviderSettingsError, load_provider_settings, save_provider_settings  # 新增代码+OpenAIAuthAttempt：复用 provider 设置读写和结构化错误；如果没有这行，complete 后无法刷新 provider catalog。


AUTH_ATTEMPT_SCHEMA_VERSION = 3  # 新增代码+OpenAIAuthAttempt：声明 auth-attempt payload 版本；如果没有这行，前后端无法判断状态机合同。
OPENAI_AUTH_ATTEMPT_METHODS = {"chatgpt-browser", "chatgpt-headless"}  # 新增代码+OpenAIAuthAttempt：限制稳定 V1 只支持两个 OpenAI OAuth mock 方法；如果没有这行，任意方法可能进入 attempt 状态机。
AUTH_ATTEMPT_TTL_SECONDS = 600.0  # 新增代码+OpenAIAuthAttempt：定义 mock attempt 过期时间；如果没有这行，pending 尝试会永久留在内存。
_ATTEMPT_LOCK = threading.Lock()  # 新增代码+OpenAIAuthAttempt：保护全局 attempt registry；如果没有这行，多请求可能同时修改同一 attempt。
_ATTEMPTS: dict[str, "GuiProviderAuthAttempt"] = {}  # 新增代码+OpenAIAuthAttempt：保存当前进程内 auth attempts；如果没有这行，status/cancel 找不到 start 创建的尝试。


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
# 新增代码+OpenAIAuthAttempt：函数段结束，_cancel_existing_pending_for_provider 到此结束；如果没有边界说明，初学者不易看出它只清理旧 pending。


def _mock_attempt_fields(auth_method_id: str, attempt_id: str, base_url: str) -> tuple[str, str, str, str, bool]:  # 新增代码+OpenAIAuthAttempt：函数段开始，生成 mock 授权展示字段；如果没有这段，browser/headless 文案会散落。
    safe_base_url = base_url.rstrip("/")  # 新增代码+OpenAIAuthAttempt：去掉 base URL 尾部斜杠；如果没有这行，拼接 URL 可能出现双斜杠。
    if auth_method_id == "chatgpt-headless":  # 新增代码+OpenAIAuthAttempt：处理 headless 设备码 flow；如果没有这行，设备码和浏览器说明无法区分。
        display_code = f"MOCK-OPENAI-{attempt_id[-6:].upper()}"  # 新增代码+OpenAIAuthAttempt：生成可复制 mock 设备码；如果没有这行，headless 等待页没有用户输入内容。
        return f"{safe_base_url}/mock/openai/device", "访问此链接并输入设备码，以完成 mock ChatGPT 授权。", display_code, "device_code", True  # 新增代码+OpenAIAuthAttempt：返回 headless mock 展示字段；如果没有这行，前端无法显示设备码流程。
    return f"{safe_base_url}/mock/openai/browser", "在浏览器中完成 mock ChatGPT 授权。", "Complete authorization in your browser. This window will close automatically.", "browser_instruction", False  # 新增代码+OpenAIAuthAttempt：返回 browser mock 展示字段；如果没有这行，前端无法显示浏览器登录流程。
# 新增代码+OpenAIAuthAttempt：函数段结束，_mock_attempt_fields 到此结束；如果没有边界说明，初学者不易看出它只生成展示字段。


def start_provider_auth_attempt(workspace: str | Path, provider_id: Any, auth_method_id: Any) -> dict[str, Any]:  # 新增代码+OpenAIAuthAttempt：函数段开始，启动 provider auth attempt；如果没有这段，browser/headless 连接按钮没有后端状态机。
    clean_provider_id, clean_auth_method_id = _validate_openai_attempt(provider_id, auth_method_id)  # 新增代码+OpenAIAuthAttempt：校验并清洗 provider/method；如果没有这行，非法请求会进入 registry。
    config = build_openai_auth_config()  # 新增代码+OpenAIAuthAttempt：读取 OpenAI auth 配置；如果没有这行，mock/real 门禁不会生效。
    now = time.time()  # 新增代码+OpenAIAuthAttempt：记录当前时间；如果没有这行，created/expires 无法稳定生成。
    attempt_id = _new_attempt_id()  # 新增代码+OpenAIAuthAttempt：生成新 attempt id；如果没有这行，前端无法轮询。
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


def cancel_provider_auth_attempt(attempt_id: Any) -> dict[str, Any]:  # 新增代码+OpenAIAuthAttempt：函数段开始，取消 auth attempt；如果没有这段，关闭 wizard 后后端仍会 pending。
    clean_attempt_id = str(attempt_id or "").strip()  # 新增代码+OpenAIAuthAttempt：清理 attempt id；如果没有这行，空白 id 可能访问 registry。
    with _ATTEMPT_LOCK:  # 新增代码+OpenAIAuthAttempt：锁住 registry 更新；如果没有这行，cancel 和 status 可能竞态。
        attempt = _ATTEMPTS.get(clean_attempt_id)  # 新增代码+OpenAIAuthAttempt：读取目标 attempt；如果没有这行，无法判断是否存在。
        if attempt is None:  # 新增代码+OpenAIAuthAttempt：处理未知 attempt；如果没有这行，后续访问会 AttributeError。
            return _attempt_payload(_expired_placeholder_attempt(clean_attempt_id, "auth_attempt_not_found"))  # 修改代码+OpenAIAuthAttemptTail：未知 cancel 返回 expired 占位；如果没有这行，关闭旧弹窗可能因为 404 变成可见错误。
        if attempt.status == "pending":  # 新增代码+OpenAIAuthAttempt：只把 pending 取消成 expired；如果没有这行，complete 状态可能被取消覆盖。
            attempt.status = "expired"  # 新增代码+OpenAIAuthAttempt：取消统一表现为 expired；如果没有这行，状态 enum 会多出 cancel 分支。
            attempt.message = "cancelled_by_user"  # 新增代码+OpenAIAuthAttempt：保存用户取消原因；如果没有这行，UI 无法显示明确取消状态。
        return _attempt_payload(attempt)  # 新增代码+OpenAIAuthAttempt：返回取消后的 payload；如果没有这行，前端拿不到终态。
# 新增代码+OpenAIAuthAttempt：函数段结束，cancel_provider_auth_attempt 到此结束；如果没有边界说明，初学者不易看出它只取消状态机。
