"""OpenHarness Desktop OpenAI OAuth 安全配置门禁。"""  # 新增代码+OpenAIAuthConfig：说明本模块只负责真实 OAuth 开关判断；如果没有这行，维护者容易把它误当 OAuth 执行器。

from __future__ import annotations  # 新增代码+OpenAIAuthConfig：启用延迟类型解析；如果没有这行，类型注解在旧解释器兼容性上更脆弱。

import os  # 新增代码+OpenAIAuthConfig：读取运行环境变量；如果没有这行，默认配置无法来自真实桌面启动环境。
from dataclasses import dataclass  # 新增代码+OpenAIAuthConfig：定义不可变配置对象；如果没有这行，配置字段会散落成普通 dict。
from typing import Mapping  # 新增代码+OpenAIAuthConfig：标注环境变量映射类型；如果没有这行，测试注入 env 的意图不清楚。


REAL_OPENAI_AUTH_MODES = {"real_headless", "real_browser"}  # 新增代码+OpenAIAuthConfig：集中定义真实 OAuth 模式；如果没有这行，调用方可能用任意字符串开启真实 token 路径。
MOCK_OPENAI_AUTH_MODES = {"mock", "mock_headless", "mock_browser"}  # 新增代码+OpenAIAuthConfig：集中定义稳定 V1 mock 模式；如果没有这行，视觉验收默认路径没有明确白名单。
DEFAULT_OPENAI_AUTH_BASE_URL = "http://127.0.0.1:18991"  # 新增代码+OpenAIAuthConfig：定义本地 mock 授权服务默认地址；如果没有这行，auth-attempt 无法生成稳定测试链接。


class OpenAIAuthConfigError(Exception):  # 新增代码+OpenAIAuthConfig：类段开始，承载真实 OAuth 门禁错误；如果没有这个类，bridge 只能返回模糊异常。
    def __init__(self, code: str, message: str) -> None:  # 新增代码+OpenAIAuthConfig：函数段开始，初始化错误码和说明；如果没有这段，调用方无法稳定读取错误原因。
        super().__init__(message)  # 新增代码+OpenAIAuthConfig：把说明传给 Exception；如果没有这行，日志里的异常文本会为空。
        self.code = code  # 新增代码+OpenAIAuthConfig：保存机器可读错误码；如果没有这行，前端无法区分真实 OAuth 被门禁挡住。
        self.message = message  # 新增代码+OpenAIAuthConfig：保存用户/日志可读说明；如果没有这行，调用方只能使用 str(error)。
    # 新增代码+OpenAIAuthConfig：函数段结束，OpenAIAuthConfigError.__init__ 到此结束；如果没有边界说明，初学者不易看出字段范围。
# 新增代码+OpenAIAuthConfig：类段结束，OpenAIAuthConfigError 到此结束；如果没有边界说明，初学者不易看出它只负责错误传递。


@dataclass(frozen=True)  # 新增代码+OpenAIAuthConfig：生成不可变配置对象；如果没有这行，后续流程可能意外修改门禁结果。
class OpenAIAuthConfig:  # 新增代码+OpenAIAuthConfig：类段开始，描述 OpenAI OAuth 配置摘要；如果没有这个类，真实/模拟门禁字段会散成 dict。
    auth_mode: str  # 新增代码+OpenAIAuthConfig：保存当前认证模式；如果没有这行，调用方不知道是 mock 还是 real。
    secret_store_kind: str  # 新增代码+OpenAIAuthConfig：保存密钥存储类型；如果没有这行，真实 OAuth 无法判断 token 能否安全落盘。
    experimental_enabled: bool  # 新增代码+OpenAIAuthConfig：保存实验开关状态；如果没有这行，真实 OAuth 可能在普通启动中误开启。
    client_id: str  # 新增代码+OpenAIAuthConfig：保存 OpenAI OAuth client id；如果没有这行，真实 OAuth 请求无法构造。
    auth_base_url: str  # 新增代码+OpenAIAuthConfig：保存授权服务 base URL；如果没有这行，mock attempt 无法生成跳转链接。
    mock_enabled: bool  # 新增代码+OpenAIAuthConfig：保存 mock flow 是否启用；如果没有这行，稳定 V1 UI 无法判断是否能走 mock auth-attempt。
    real_oauth_enabled: bool  # 新增代码+OpenAIAuthConfig：保存真实 OAuth 是否通过门禁；如果没有这行，后续保存 token 路径没有硬门槛。
    blocked_reason: str  # 新增代码+OpenAIAuthConfig：保存第一条阻断原因；如果没有这行，日志和测试无法快速定位主要缺失条件。
    blocked_reasons: tuple[str, ...]  # 新增代码+OpenAIAuthConfig：保存全部阻断原因；如果没有这行，多条件缺失时只能看到一个原因。
    # 新增代码+OpenAIAuthConfig：类段结束，OpenAIAuthConfig 到此结束；如果没有边界说明，初学者不易看出配置字段范围。


def _env_value(env: Mapping[str, str], key: str, default: str = "") -> str:  # 新增代码+OpenAIAuthConfig：函数段开始，安全读取环境变量字符串；如果没有这段，None/空白处理会散落。
    return str(env.get(key, default) or default).strip()  # 新增代码+OpenAIAuthConfig：返回去空白后的环境变量；如果没有这行，空字符串可能被误当有效配置。
# 新增代码+OpenAIAuthConfig：函数段结束，_env_value 到此结束；如果没有边界说明，初学者不易看出它只负责读取 env。


def _flag_enabled(value: str) -> bool:  # 新增代码+OpenAIAuthConfig：函数段开始，判断实验开关是否启用；如果没有这段，true/yes/on 等常见写法无法兼容。
    return value.strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+OpenAIAuthConfig：识别安全的显式开启值；如果没有这行，任意非空字符串都可能误开启真实 OAuth。
# 新增代码+OpenAIAuthConfig：函数段结束，_flag_enabled 到此结束；如果没有边界说明，初学者不易看出它只负责布尔开关。


def _blocked_reasons(auth_mode: str, secret_store_kind: str, experimental_enabled: bool, client_id: str) -> tuple[str, ...]:  # 新增代码+OpenAIAuthConfig：函数段开始，计算真实 OAuth 缺失条件；如果没有这段，门禁判断会散落到多个调用点。
    if auth_mode not in REAL_OPENAI_AUTH_MODES:  # 新增代码+OpenAIAuthConfig：非真实模式不需要真实 OAuth 门禁；如果没有这行，mock 模式会被误报阻断。
        return ()  # 新增代码+OpenAIAuthConfig：mock 模式无真实 OAuth 阻断原因；如果没有这行，默认配置会显示错误原因。
    reasons: list[str] = []  # 新增代码+OpenAIAuthConfig：准备收集缺失条件；如果没有这行，无法同时记录多个阻断原因。
    if secret_store_kind != "os_encrypted":  # 新增代码+OpenAIAuthConfig：要求真实 token 只能进入 OS 加密存储；如果没有这行，refresh token 可能写入 dev JSON。
        reasons.append("os_encrypted_secret_store_required")  # 新增代码+OpenAIAuthConfig：记录缺少加密存储；如果没有这行，用户不知道首要安全条件。
    if not experimental_enabled:  # 新增代码+OpenAIAuthConfig：要求显式实验开关；如果没有这行，真实 OAuth 会在普通启动里误开启。
        reasons.append("experimental_flag_required")  # 新增代码+OpenAIAuthConfig：记录缺少 experimental flag；如果没有这行，用户不知道要设置显式开关。
    if not client_id:  # 新增代码+OpenAIAuthConfig：要求真实 OAuth client id；如果没有这行，后续授权 URL 无法正确构造。
        reasons.append("openai_client_id_required")  # 新增代码+OpenAIAuthConfig：记录缺少 client id；如果没有这行，用户不知道需要配置 OAuth client。
    return tuple(reasons)  # 新增代码+OpenAIAuthConfig：返回不可变阻断原因；如果没有这行，调用方拿不到门禁结果。
# 新增代码+OpenAIAuthConfig：函数段结束，_blocked_reasons 到此结束；如果没有边界说明，初学者不易看出它只计算缺失条件。


def build_openai_auth_config(env: Mapping[str, str] | None = None) -> OpenAIAuthConfig:  # 新增代码+OpenAIAuthConfig：函数段开始，构造 OpenAI Auth 配置摘要；如果没有这段，auth-attempt 无法统一读取安全门禁。
    source_env = os.environ if env is None else env  # 新增代码+OpenAIAuthConfig：允许测试注入 env，真实运行读取 os.environ；如果没有这行，测试会污染本机环境。
    auth_mode = _env_value(source_env, "OPENHARNESS_OPENAI_AUTH_MODE", "mock").lower()  # 新增代码+OpenAIAuthConfig：读取认证模式并默认 mock；如果没有这行，稳定 V1 可能没有安全默认值。
    secret_store_kind = _env_value(source_env, "OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json")  # 新增代码+OpenAIAuthConfig：读取 provider secret store 类型；如果没有这行，真实 OAuth 无法判断落盘安全性。
    experimental_enabled = _flag_enabled(_env_value(source_env, "OPENHARNESS_OPENAI_EXPERIMENTAL", ""))  # 新增代码+OpenAIAuthConfig：读取实验开关；如果没有这行，真实 OAuth 不会有显式 opt-in。
    client_id = _env_value(source_env, "OPENHARNESS_OPENAI_CLIENT_ID", "")  # 新增代码+OpenAIAuthConfig：读取 OpenAI OAuth client id；如果没有这行，真实 OAuth URL 无法构造。
    auth_base_url = _env_value(source_env, "OPENHARNESS_OPENAI_AUTH_BASE_URL", DEFAULT_OPENAI_AUTH_BASE_URL)  # 新增代码+OpenAIAuthConfig：读取授权服务 base URL；如果没有这行，mock server 和真实授权服务不能配置。
    reasons = _blocked_reasons(auth_mode, secret_store_kind, experimental_enabled, client_id)  # 新增代码+OpenAIAuthConfig：计算真实 OAuth 阻断原因；如果没有这行，real_oauth_enabled 没有安全依据。
    real_oauth_enabled = auth_mode in REAL_OPENAI_AUTH_MODES and len(reasons) == 0  # 新增代码+OpenAIAuthConfig：只有真实模式且无阻断原因才允许真实 OAuth；如果没有这行，token 保存路径可能误开启。
    mock_enabled = auth_mode in MOCK_OPENAI_AUTH_MODES or not real_oauth_enabled  # 新增代码+OpenAIAuthConfig：默认和阻断情况下都允许 mock flow；如果没有这行，稳定 V1 视觉验收会因真实门禁阻断而不可用。
    return OpenAIAuthConfig(auth_mode=auth_mode, secret_store_kind=secret_store_kind, experimental_enabled=experimental_enabled, client_id=client_id, auth_base_url=auth_base_url, mock_enabled=mock_enabled, real_oauth_enabled=real_oauth_enabled, blocked_reason=reasons[0] if reasons else "", blocked_reasons=reasons)  # 新增代码+OpenAIAuthConfig：返回完整配置摘要；如果没有这行，调用方拿不到门禁结果。
# 新增代码+OpenAIAuthConfig：函数段结束，build_openai_auth_config 到此结束；如果没有边界说明，初学者不易看出它不执行 OAuth。


def assert_real_oauth_allowed(config: OpenAIAuthConfig) -> None:  # 新增代码+OpenAIAuthConfig：函数段开始，断言真实 OAuth 已通过门禁；如果没有这段，真实 token 保存点容易忘记检查安全条件。
    if config.real_oauth_enabled:  # 新增代码+OpenAIAuthConfig：已通过门禁时直接返回；如果没有这行，合法实验配置也会被阻断。
        return  # 新增代码+OpenAIAuthConfig：真实 OAuth 允许时无异常；如果没有这行，调用方无法继续实验路径。
    missing = ", ".join(config.blocked_reasons or ("real_oauth_mode_required",))  # 新增代码+OpenAIAuthConfig：生成缺失条件列表；如果没有这行，错误说明没有具体原因。
    message = f"OpenAI real OAuth blocked: {missing}. Required: OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted, OPENHARNESS_OPENAI_EXPERIMENTAL=1, OPENHARNESS_OPENAI_CLIENT_ID."  # 新增代码+OpenAIAuthConfig：生成结构化安全说明；如果没有这行，用户不知道启用真实 OAuth 的完整条件。
    raise OpenAIAuthConfigError("openai_real_oauth_blocked", message)  # 新增代码+OpenAIAuthConfig：抛出机器可读错误；如果没有这行，调用方可能误继续保存真实 token。
# 新增代码+OpenAIAuthConfig：函数段结束，assert_real_oauth_allowed 到此结束；如果没有边界说明，初学者不易看出它是保存真实 token 前的硬门禁。
