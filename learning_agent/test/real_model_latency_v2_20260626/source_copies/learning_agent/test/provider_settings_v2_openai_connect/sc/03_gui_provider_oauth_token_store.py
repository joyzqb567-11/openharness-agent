"""OpenHarness Desktop direct OAuth token store."""  # 新增代码+DirectOAuthTokenStore：说明本模块只负责 V1C direct OAuth token 的安全存储；如果没有这行代码，维护者容易把它误当成 provider catalog。

from __future__ import annotations  # 新增代码+DirectOAuthTokenStore：启用延迟类型注解解析；如果没有这行代码，Path 和类自身类型在旧解释器上更脆弱。

import base64  # 新增代码+DirectOAuthTokenStore：用于把 DPAPI 二进制密文转成可落盘文本；如果没有这行代码，加密结果不方便稳定保存。
import ctypes  # 新增代码+DirectOAuthTokenStore：用于调用 Windows DPAPI；如果没有这行代码，真实 refresh token 只能落到不安全明文文件。
import json  # 新增代码+DirectOAuthTokenStore：用于序列化 token 记录；如果没有这行代码，token store 无法保存结构化字段。
import os  # 新增代码+DirectOAuthTokenStore：用于识别 Windows 和读取本地应用数据目录；如果没有这行代码，默认路径和 DPAPI 判断无法工作。
import re  # 新增代码+DirectOAuthTokenStore：用于清洗 provider id 形成安全文件名；如果没有这行代码，恶意 provider id 可能影响文件路径。
from dataclasses import dataclass  # 新增代码+DirectOAuthTokenStore：用于声明脱敏摘要对象；如果没有这行代码，info payload 容易散成随意 dict。
from pathlib import Path  # 新增代码+DirectOAuthTokenStore：用于跨 Windows 路径管理；如果没有这行代码，路径拼接会更容易出错。
from typing import Any  # 新增代码+DirectOAuthTokenStore：用于标注 JSON-like token 字段；如果没有这行代码，测试注入的 token 类型边界不清楚。


SAFE_PROVIDER_ID_PATTERN = re.compile(r"[^a-zA-Z0-9_.-]+")  # 新增代码+DirectOAuthTokenStore：定义 provider 文件名清洗规则；如果没有这行代码，provider id 可能带入路径分隔符。
DEFAULT_TOKEN_DIR_NAME = "provider_oauth_tokens"  # 新增代码+DirectOAuthTokenStore：集中定义默认 token 子目录名；如果没有这行代码，默认路径会散落到多个函数里。


@dataclass(frozen=True)  # 新增代码+DirectOAuthTokenStore：生成不可变脱敏摘要对象；如果没有这行代码，info 返回结构容易被后续逻辑意外修改。
class GuiProviderOAuthTokenInfo:  # 新增代码+DirectOAuthTokenStore：类段开始，描述 renderer 可以看到的 token 摘要；如果没有这个类，raw token 字段可能被误放进响应。
    provider_id: str  # 新增代码+DirectOAuthTokenStore：保存 provider id；如果没有这行代码，catalog 无法知道摘要属于哪个 provider。
    connected: bool  # 新增代码+DirectOAuthTokenStore：保存是否存在可用 token 记录；如果没有这行代码，provider 行无法显示连接状态。
    status: str  # 新增代码+DirectOAuthTokenStore：保存 missing/connected 等安全状态；如果没有这行代码，GUI 无法解释当前连接摘要。
    token_ref: str  # 新增代码+DirectOAuthTokenStore：保存不含 secret 的 token 引用；如果没有这行代码，后端和 catalog 没有安全关联标识。
    account_id: str  # 新增代码+DirectOAuthTokenStore：保存账号摘要；如果没有这行代码，用户难以确认连接的是哪个 ChatGPT 账号。
    expires_at: int  # 新增代码+DirectOAuthTokenStore：保存 access token 过期摘要；如果没有这行代码，后续刷新策略没有可见依据。
    store_kind: str  # 新增代码+DirectOAuthTokenStore：保存存储类型摘要；如果没有这行代码，诊断时无法确认是否走 OS 加密。
    # 新增代码+DirectOAuthTokenStore：类段结束，GuiProviderOAuthTokenInfo 到此结束；如果没有边界说明，初学者不易看出这里没有任何 raw token。

    def to_dict(self) -> dict[str, object]:  # 新增代码+DirectOAuthTokenStore：函数段开始，把摘要对象转成 JSON dict；如果没有这段，bridge 无法直接序列化 dataclass。
        return {  # 新增代码+DirectOAuthTokenStore：返回 renderer 安全字段字典；如果没有这行代码，调用方只能用 asdict 而更难审计字段。
            "provider_id": self.provider_id,  # 新增代码+DirectOAuthTokenStore：输出 provider id；如果没有这行代码，前端无法归属状态。
            "connected": self.connected,  # 新增代码+DirectOAuthTokenStore：输出连接状态；如果没有这行代码，provider catalog 无法判断连接。
            "status": self.status,  # 新增代码+DirectOAuthTokenStore：输出状态字符串；如果没有这行代码，UI 无法解释 missing/corrupt。
            "token_ref": self.token_ref,  # 新增代码+DirectOAuthTokenStore：输出安全引用；如果没有这行代码，后端无法用非敏感方式关联 token。
            "account_id": self.account_id,  # 新增代码+DirectOAuthTokenStore：输出账号摘要；如果没有这行代码，用户无法核对登录身份。
            "expires_at": self.expires_at,  # 新增代码+DirectOAuthTokenStore：输出过期时间；如果没有这行代码，诊断刷新问题会更困难。
            "store_kind": self.store_kind,  # 新增代码+DirectOAuthTokenStore：输出存储类型；如果没有这行代码，验收无法确认 OS 加密路径。
        }  # 新增代码+DirectOAuthTokenStore：安全字段字典结束；如果没有这行代码，Python 语法不完整。
    # 新增代码+DirectOAuthTokenStore：函数段结束，to_dict 到此结束；如果没有边界说明，用户不容易看出序列化白名单范围。


def _safe_provider_id(provider: str) -> str:  # 新增代码+DirectOAuthTokenStore：函数段开始，把 provider id 转成安全文件名片段；如果没有这段，路径可能被输入污染。
    clean_provider = SAFE_PROVIDER_ID_PATTERN.sub("_", str(provider or "").strip())  # 新增代码+DirectOAuthTokenStore：替换危险字符；如果没有这行代码，provider 可能包含斜杠或控制字符。
    return clean_provider or "unknown_provider"  # 新增代码+DirectOAuthTokenStore：空 provider 使用兜底名；如果没有这行代码，空文件名会导致路径异常。
# 新增代码+DirectOAuthTokenStore：函数段结束，_safe_provider_id 到此结束；如果没有边界说明，用户不容易看出 provider 清洗规则。


def _default_config_dir() -> Path:  # 新增代码+DirectOAuthTokenStore：函数段开始，计算默认 token 存储目录；如果没有这段，真实 token 路径会散落在调用方。
    local_root = Path(os.environ.get("LOCALAPPDATA", Path.home()))  # 新增代码+DirectOAuthTokenStore：优先使用 Windows 本地应用数据目录；如果没有这行代码，token 可能误写入项目目录。
    return local_root / "OpenHarness" / DEFAULT_TOKEN_DIR_NAME  # 新增代码+DirectOAuthTokenStore：返回 OpenHarness 专属 token 目录；如果没有这行代码，多个应用可能混用凭据。
# 新增代码+DirectOAuthTokenStore：函数段结束，_default_config_dir 到此结束；如果没有边界说明，用户不容易看出默认路径来源。


class _DATA_BLOB(ctypes.Structure):  # 新增代码+DirectOAuthTokenStore：类段开始，声明 Windows DPAPI DATA_BLOB 结构；如果没有这个类，ctypes 无法把字节交给 CryptProtectData。
    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]  # 新增代码+DirectOAuthTokenStore：声明长度和指针字段；如果没有这行代码，DPAPI 调用会读取错误内存。
    # 新增代码+DirectOAuthTokenStore：类段结束，_DATA_BLOB 到此结束；如果没有边界说明，用户不容易看出它只服务 Windows API。


def _protect_with_windows_dpapi(data: bytes) -> bytes:  # 新增代码+DirectOAuthTokenStore：函数段开始，用 Windows DPAPI 加密字节；如果没有这段，真实 refresh token 无法 OS 级保护。
    if os.name != "nt":  # 新增代码+DirectOAuthTokenStore：确认当前系统是 Windows；如果没有这行代码，非 Windows 会尝试不存在的 crypt32。
        raise RuntimeError("windows_dpapi_unavailable")  # 新增代码+DirectOAuthTokenStore：非 Windows 明确失败；如果没有这行代码，真实 direct OAuth 可能误以为已加密。
    crypt32 = ctypes.windll.crypt32  # 新增代码+DirectOAuthTokenStore：读取 Windows crypt32 DLL；如果没有这行代码，无法调用 CryptProtectData。
    kernel32 = ctypes.windll.kernel32  # 新增代码+DirectOAuthTokenStore：读取 kernel32 用于释放内存；如果没有这行代码，DPAPI 输出缓冲区会泄漏。
    input_buffer = ctypes.create_string_buffer(data)  # 新增代码+DirectOAuthTokenStore：创建稳定输入缓冲区；如果没有这行代码，指针可能指向被移动的 Python 对象。
    input_blob = _DATA_BLOB(len(data), ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_ubyte)))  # 新增代码+DirectOAuthTokenStore：把输入字节包装成 DATA_BLOB；如果没有这行代码，DPAPI 不知道输入长度。
    output_blob = _DATA_BLOB()  # 新增代码+DirectOAuthTokenStore：准备接收 DPAPI 输出；如果没有这行代码，CryptProtectData 没有目标缓冲区。
    ok = crypt32.CryptProtectData(ctypes.byref(input_blob), None, None, None, None, 0, ctypes.byref(output_blob))  # 新增代码+DirectOAuthTokenStore：执行用户上下文加密；如果没有这行代码，数据仍是明文。
    if not ok:  # 新增代码+DirectOAuthTokenStore：检查 Windows API 返回值；如果没有这行代码，加密失败也会继续写坏数据。
        raise RuntimeError("windows_dpapi_encrypt_failed")  # 新增代码+DirectOAuthTokenStore：抛出结构化加密失败；如果没有这行代码，调用方无法知道 token 未安全保存。
    try:  # 新增代码+DirectOAuthTokenStore：确保 finally 释放 DPAPI 输出内存；如果没有这行代码，异常路径可能泄漏内存。
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)  # 新增代码+DirectOAuthTokenStore：复制密文字节回 Python；如果没有这行代码，调用方拿不到加密结果。
    finally:  # 新增代码+DirectOAuthTokenStore：无论复制是否成功都释放 Windows 分配的缓冲区；如果没有这行代码，重复保存会泄漏内存。
        kernel32.LocalFree(output_blob.pbData)  # 新增代码+DirectOAuthTokenStore：释放 DPAPI 输出缓冲；如果没有这行代码，Windows 进程内存会逐步增长。
# 新增代码+DirectOAuthTokenStore：函数段结束，_protect_with_windows_dpapi 到此结束；如果没有边界说明，用户不容易看出这里不返回明文。


def _unprotect_with_windows_dpapi(data: bytes) -> bytes:  # 新增代码+DirectOAuthTokenStore：函数段开始，用 Windows DPAPI 解密字节；如果没有这段，后端无法读取已保存 token。
    if os.name != "nt":  # 新增代码+DirectOAuthTokenStore：确认当前系统是 Windows；如果没有这行代码，非 Windows 会尝试不存在的 crypt32。
        raise RuntimeError("windows_dpapi_unavailable")  # 新增代码+DirectOAuthTokenStore：非 Windows 明确失败；如果没有这行代码，解密错误会变成模糊 AttributeError。
    crypt32 = ctypes.windll.crypt32  # 新增代码+DirectOAuthTokenStore：读取 Windows crypt32 DLL；如果没有这行代码，无法调用 CryptUnprotectData。
    kernel32 = ctypes.windll.kernel32  # 新增代码+DirectOAuthTokenStore：读取 kernel32 用于释放内存；如果没有这行代码，DPAPI 输出缓冲区会泄漏。
    input_buffer = ctypes.create_string_buffer(data)  # 新增代码+DirectOAuthTokenStore：创建稳定密文缓冲区；如果没有这行代码，指针可能失效。
    input_blob = _DATA_BLOB(len(data), ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_ubyte)))  # 新增代码+DirectOAuthTokenStore：把密文字节包装成 DATA_BLOB；如果没有这行代码，DPAPI 不知道密文长度。
    output_blob = _DATA_BLOB()  # 新增代码+DirectOAuthTokenStore：准备接收明文字节；如果没有这行代码，CryptUnprotectData 没有输出目标。
    ok = crypt32.CryptUnprotectData(ctypes.byref(input_blob), None, None, None, None, 0, ctypes.byref(output_blob))  # 新增代码+DirectOAuthTokenStore：执行用户上下文解密；如果没有这行代码，后端拿不到 token。
    if not ok:  # 新增代码+DirectOAuthTokenStore：检查 Windows API 返回值；如果没有这行代码，解密失败可能返回无效字节。
        raise RuntimeError("windows_dpapi_decrypt_failed")  # 新增代码+DirectOAuthTokenStore：抛出结构化解密失败；如果没有这行代码，坏凭据会导致不可读错误。
    try:  # 新增代码+DirectOAuthTokenStore：确保 finally 释放 DPAPI 输出内存；如果没有这行代码，异常路径可能泄漏内存。
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)  # 新增代码+DirectOAuthTokenStore：复制明文字节回 Python 后端内存；如果没有这行代码，模型适配器无法构造请求。
    finally:  # 新增代码+DirectOAuthTokenStore：无论复制是否成功都释放 Windows 分配的缓冲区；如果没有这行代码，重复读取会泄漏内存。
        kernel32.LocalFree(output_blob.pbData)  # 新增代码+DirectOAuthTokenStore：释放 DPAPI 输出缓冲；如果没有这行代码，Windows 进程内存会逐步增长。
# 新增代码+DirectOAuthTokenStore：函数段结束，_unprotect_with_windows_dpapi 到此结束；如果没有边界说明，用户不容易看出解密只在后端内存中发生。


class GuiProviderOAuthTokenStore:  # 新增代码+DirectOAuthTokenStore：类段开始，管理 direct OAuth token 文件生命周期；如果没有这个类，V1C 无安全 token 存储边界。
    def __init__(self, config_dir: str | Path | None = None, encrypted: bool = True) -> None:  # 新增代码+DirectOAuthTokenStore：函数段开始，初始化 token store；如果没有这段，调用方无法指定安全目录和加密模式。
        self.config_dir = Path(config_dir).expanduser().resolve() if config_dir else _default_config_dir()  # 新增代码+DirectOAuthTokenStore：保存最终配置目录；如果没有这行代码，token 可能跟随当前工作目录漂移。
        self.encrypted = bool(encrypted)  # 新增代码+DirectOAuthTokenStore：保存是否使用 DPAPI；如果没有这行代码，fake 测试和真实加密路径无法分开。
    # 新增代码+DirectOAuthTokenStore：函数段结束，__init__ 到此结束；如果没有边界说明，用户不容易看出初始化只保存配置不读 token。

    @property  # 新增代码+DirectOAuthTokenStore：属性段开始，提供存储类型摘要；如果没有这行代码，info 需要重复判断 encrypted。
    def store_kind(self) -> str:  # 新增代码+DirectOAuthTokenStore：函数段开始，返回 os_encrypted 或 fake_plain；如果没有这段，catalog 无法解释 token 保护级别。
        return "os_encrypted" if self.encrypted else "fake_plain"  # 新增代码+DirectOAuthTokenStore：根据模式返回安全摘要；如果没有这行代码，验收无法区分真实和测试存储。
    # 新增代码+DirectOAuthTokenStore：函数段结束，store_kind 到此结束；如果没有边界说明，用户不容易看出它不暴露路径内容。

    def path_for(self, provider: str) -> Path:  # 新增代码+DirectOAuthTokenStore：函数段开始，返回 provider token 文件路径；如果没有这段，读写会重复拼接路径。
        safe_provider = _safe_provider_id(provider)  # 新增代码+DirectOAuthTokenStore：清洗 provider id；如果没有这行代码，文件名可能包含危险字符。
        extension = ".oauth.bin" if self.encrypted else ".oauth.json"  # 新增代码+DirectOAuthTokenStore：按存储模式选择扩展名；如果没有这行代码，调试时难以区分密文和测试文件。
        return self.config_dir / f"{safe_provider}{extension}"  # 新增代码+DirectOAuthTokenStore：拼出最终 token 文件路径；如果没有这行代码，store 无法定位记录。
    # 新增代码+DirectOAuthTokenStore：函数段结束，path_for 到此结束；如果没有边界说明，用户不容易看出路径只由安全 provider id 组成。

    def token_ref_for(self, provider: str) -> str:  # 新增代码+DirectOAuthTokenStore：函数段开始，返回非敏感 token 引用；如果没有这段，catalog 可能暴露真实路径或 token。
        return f"provider_oauth:{_safe_provider_id(provider)}"  # 新增代码+DirectOAuthTokenStore：生成稳定引用；如果没有这行代码，后端各层难以关联同一 provider token。
    # 新增代码+DirectOAuthTokenStore：函数段结束，token_ref_for 到此结束；如果没有边界说明，用户不容易看出它不是 secret。

    def _encode_record(self, tokens: dict[str, Any]) -> bytes:  # 新增代码+DirectOAuthTokenStore：函数段开始，把 token dict 编码成落盘字节；如果没有这段，set_tokens 无法统一处理加密和 fake。
        raw_json = json.dumps(tokens, ensure_ascii=False, sort_keys=True).encode("utf-8")  # 新增代码+DirectOAuthTokenStore：序列化 token 记录；如果没有这行代码，字典无法直接写成稳定字节。
        if not self.encrypted:  # 新增代码+DirectOAuthTokenStore：测试 fake 模式跳过 DPAPI；如果没有这行代码，单元测试会依赖真实 Windows 密钥环。
            return raw_json  # 新增代码+DirectOAuthTokenStore：返回明文测试字节；如果没有这行代码，fake store 无法简单验证生命周期。
        protected = _protect_with_windows_dpapi(raw_json)  # 新增代码+DirectOAuthTokenStore：调用 DPAPI 加密 JSON；如果没有这行代码，真实 refresh token 会明文落盘。
        return base64.b64encode(protected)  # 新增代码+DirectOAuthTokenStore：把密文字节转成 base64；如果没有这行代码，文本工具难以稳定处理密文文件。
    # 新增代码+DirectOAuthTokenStore：函数段结束，_encode_record 到此结束；如果没有边界说明，用户不容易看出真实路径会加密。

    def _decode_record(self, raw: bytes) -> dict[str, Any] | None:  # 新增代码+DirectOAuthTokenStore：函数段开始，把落盘字节解码成 token dict；如果没有这段，get_tokens/info 无法读取记录。
        try:  # 新增代码+DirectOAuthTokenStore：捕获坏文件、坏密文和坏 JSON；如果没有这行代码，设置页可能因为单个坏 token 崩溃。
            raw_json = raw if not self.encrypted else _unprotect_with_windows_dpapi(base64.b64decode(raw))  # 新增代码+DirectOAuthTokenStore：按模式解码明文或 DPAPI 密文；如果没有这行代码，真实记录无法恢复。
            payload = json.loads(raw_json.decode("utf-8"))  # 新增代码+DirectOAuthTokenStore：解析 JSON 字节；如果没有这行代码，后端无法读取 token 字段。
        except Exception:  # 新增代码+DirectOAuthTokenStore：坏记录统一按缺失处理；如果没有这行代码，损坏文件会变成 GUI 500。
            return None  # 新增代码+DirectOAuthTokenStore：返回 None 表示不可用；如果没有这行代码，调用方无法安全降级。
        return payload if isinstance(payload, dict) else None  # 新增代码+DirectOAuthTokenStore：只接受对象记录；如果没有这行代码，数组或字符串会污染 token 流程。
    # 新增代码+DirectOAuthTokenStore：函数段结束，_decode_record 到此结束；如果没有边界说明，用户不容易看出坏文件不会抛给 UI。

    def set_tokens(self, provider: str, tokens: dict[str, Any]) -> None:  # 新增代码+DirectOAuthTokenStore：函数段开始，保存 provider token；如果没有这段，direct OAuth callback 无法持久化登录。
        token_path = self.path_for(provider)  # 新增代码+DirectOAuthTokenStore：定位 token 文件；如果没有这行代码，保存不知道目标路径。
        token_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+DirectOAuthTokenStore：确保目录存在；如果没有这行代码，首次登录会因目录缺失失败。
        token_path.write_bytes(self._encode_record(dict(tokens)))  # 新增代码+DirectOAuthTokenStore：写入编码后的 token 记录；如果没有这行代码，登录成功不会落盘。
    # 新增代码+DirectOAuthTokenStore：函数段结束，set_tokens 到此结束；如果没有边界说明，用户不容易看出它不返回 token 给前端。

    def write_raw(self, provider: str, raw: bytes) -> None:  # 新增代码+DirectOAuthTokenStore：函数段开始，测试专用写入坏记录；如果没有这段，corrupt 文件恢复路径难以覆盖。
        token_path = self.path_for(provider)  # 新增代码+DirectOAuthTokenStore：定位 token 文件；如果没有这行代码，测试不知道该写哪里。
        token_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+DirectOAuthTokenStore：确保目录存在；如果没有这行代码，测试首次写入会失败。
        token_path.write_bytes(raw)  # 新增代码+DirectOAuthTokenStore：写入原始字节；如果没有这行代码，坏记录无法制造。
    # 新增代码+DirectOAuthTokenStore：函数段结束，write_raw 到此结束；如果没有边界说明，用户不容易看出它只给测试和排查使用。

    def get_tokens(self, provider: str) -> dict[str, Any] | None:  # 新增代码+DirectOAuthTokenStore：函数段开始，后端读取 raw token；如果没有这段，模型适配器无法调用真实 Codex backend。
        token_path = self.path_for(provider)  # 新增代码+DirectOAuthTokenStore：定位 token 文件；如果没有这行代码，读取不知道目标路径。
        if not token_path.exists():  # 新增代码+DirectOAuthTokenStore：处理未登录状态；如果没有这行代码，首次打开设置页会尝试读取不存在文件。
            return None  # 新增代码+DirectOAuthTokenStore：未登录返回 None；如果没有这行代码，调用方无法区分未连接。
        return self._decode_record(token_path.read_bytes())  # 新增代码+DirectOAuthTokenStore：读取并解码 token 记录；如果没有这行代码，后端拿不到 raw token。
    # 新增代码+DirectOAuthTokenStore：函数段结束，get_tokens 到此结束；如果没有边界说明，用户不容易看出 raw token 只留在后端。

    def delete_tokens(self, provider: str) -> None:  # 新增代码+DirectOAuthTokenStore：函数段开始，删除 provider token；如果没有这段，用户无法断开 direct OAuth 登录。
        token_path = self.path_for(provider)  # 新增代码+DirectOAuthTokenStore：定位 token 文件；如果没有这行代码，删除不知道目标路径。
        try:  # 新增代码+DirectOAuthTokenStore：兼容文件不存在；如果没有这行代码，重复断开连接会抛异常。
            token_path.unlink()  # 新增代码+DirectOAuthTokenStore：删除 token 文件；如果没有这行代码，provider 会继续显示已登录。
        except FileNotFoundError:  # 新增代码+DirectOAuthTokenStore：处理已经删除的场景；如果没有这行代码，幂等删除会失败。
            return  # 新增代码+DirectOAuthTokenStore：文件不存在时视为已删除；如果没有这行代码，调用方需要额外判断。
    # 新增代码+DirectOAuthTokenStore：函数段结束，delete_tokens 到此结束；如果没有边界说明，用户不容易看出删除是幂等的。

    def info(self, provider: str) -> dict[str, object]:  # 新增代码+DirectOAuthTokenStore：函数段开始，返回 renderer 安全摘要；如果没有这段，catalog 可能直接调用 get_tokens 泄露 raw token。
        clean_provider = _safe_provider_id(provider)  # 新增代码+DirectOAuthTokenStore：清洗 provider id；如果没有这行代码，摘要和路径引用可能不一致。
        tokens = self.get_tokens(clean_provider)  # 新增代码+DirectOAuthTokenStore：读取后端 token 记录；如果没有这行代码，无法判断是否 connected。
        if not tokens:  # 新增代码+DirectOAuthTokenStore：处理缺失或损坏记录；如果没有这行代码，坏文件可能被误判 connected。
            return GuiProviderOAuthTokenInfo(provider_id=clean_provider, connected=False, status="missing", token_ref=self.token_ref_for(clean_provider), account_id="", expires_at=0, store_kind=self.store_kind).to_dict()  # 新增代码+DirectOAuthTokenStore：返回无敏感字段的 missing 摘要；如果没有这行代码，UI 无法安全显示未登录。
        account_id = str(tokens.get("account_id") or "")  # 新增代码+DirectOAuthTokenStore：提取账号摘要；如果没有这行代码，info 会缺少用户可核对身份。
        expires_at = int(tokens.get("expires_at") or 0)  # 新增代码+DirectOAuthTokenStore：提取过期时间摘要；如果没有这行代码，info 无法展示刷新相关状态。
        return GuiProviderOAuthTokenInfo(provider_id=clean_provider, connected=True, status="connected", token_ref=self.token_ref_for(clean_provider), account_id=account_id, expires_at=expires_at, store_kind=self.store_kind).to_dict()  # 新增代码+DirectOAuthTokenStore：返回脱敏 connected 摘要；如果没有这行代码，catalog 无法显示 direct OAuth 已连接。
    # 新增代码+DirectOAuthTokenStore：函数段结束，info 到此结束；如果没有边界说明，用户不容易看出 info 永远不含 token。
# 新增代码+DirectOAuthTokenStore：类段结束，GuiProviderOAuthTokenStore 到此结束；如果没有边界说明，用户不容易看出它是 direct OAuth 的唯一 token 边界。


def make_fake_token_store(config_dir: str | Path) -> GuiProviderOAuthTokenStore:  # 新增代码+DirectOAuthTokenStore：函数段开始，创建测试用明文 fake store；如果没有这段，单元测试会依赖真实 DPAPI。
    return GuiProviderOAuthTokenStore(config_dir=config_dir, encrypted=False)  # 新增代码+DirectOAuthTokenStore：返回关闭加密的隔离 store；如果没有这行代码，测试无法简单制造坏 JSON。
# 新增代码+DirectOAuthTokenStore：函数段结束，make_fake_token_store 到此结束；如果没有边界说明，用户不容易看出 fake store 不能用于真实 OAuth。


def default_oauth_token_store() -> GuiProviderOAuthTokenStore:  # 新增代码+DirectOAuthTokenStore：函数段开始，创建真实 direct OAuth 默认 store；如果没有这段，调用方会重复读取环境变量。
    raw_dir = os.environ.get("OPENHARNESS_PROVIDER_OAUTH_TOKEN_DIR", "").strip()  # 新增代码+DirectOAuthTokenStore：读取可选 token 目录；如果没有这行代码，高级用户无法改存储位置。
    config_dir = Path(raw_dir).expanduser().resolve() if raw_dir else _default_config_dir()  # 新增代码+DirectOAuthTokenStore：解析目录或使用默认目录；如果没有这行代码，环境变量不会生效。
    return GuiProviderOAuthTokenStore(config_dir=config_dir, encrypted=True)  # 新增代码+DirectOAuthTokenStore：真实 store 固定走 OS 加密；如果没有这行代码，direct OAuth 可能退化到明文。
# 新增代码+DirectOAuthTokenStore：函数段结束，default_oauth_token_store 到此结束；如果没有边界说明，用户不容易看出真实路径默认强制加密。
