"""Provider 设置页专用密钥存储。"""  # 新增代码+ProviderSecretStore：说明本模块只负责 Provider 密钥引用和开发存储；如果没有这行，维护者容易把它误当成模型运行时。

from __future__ import annotations  # 新增代码+ProviderSecretStore：启用延迟类型解析；如果没有这行，后续类型注解在旧解释顺序下更脆弱。

import base64  # 新增代码+OsEncryptedSecretStore：把 DPAPI 二进制密文转成 JSON 可保存文本；如果没有这行，OS 加密结果无法写入 secrets.os.json。
import ctypes  # 新增代码+OsEncryptedSecretStore：调用 Windows DPAPI；如果没有这行，真实 OAuth token 只能落到开发 JSON。
import json  # 新增代码+ProviderSecretStore：读写开发密钥 JSON；如果没有这行，DevJsonSecretStore 无法持久化密钥。
import os  # 新增代码+SecretStoreFactory：读取密钥存储模式环境变量；如果没有这行，真实 OAuth 无法强制选择 os_encrypted。
import sys  # 新增代码+OsEncryptedSecretStore：判断当前平台是否支持 Windows DPAPI；如果没有这行，非 Windows 环境会得到误导性错误。
import threading  # 新增代码+ProviderSecretStore：保护密钥文件并发写入；如果没有这行，快速点击连接/断开可能写坏 JSON。
import time  # 新增代码+ProviderSecretStore：生成损坏文件归档时间戳；如果没有这行，坏 JSON 备份文件名不稳定。
from ctypes import wintypes  # 新增代码+OsEncryptedSecretStore：复用 Windows API 类型定义；如果没有这行，DPAPI 结构字段容易写错。
from pathlib import Path  # 新增代码+ProviderSecretStore：用 Path 处理 Windows 和临时目录；如果没有这行，路径拼接容易出错。
from typing import Any, Mapping  # 修改代码+SecretStoreFactory：标注未知 JSON 对象和可注入环境变量；如果没有这行，helper 的输入边界不清楚。


_SECRET_STORE_LOCK = threading.Lock()  # 新增代码+ProviderSecretStore：集中锁住开发密钥文件写入；如果没有这行，并发保存会互相覆盖。
_CRYPTPROTECT_UI_FORBIDDEN = 0x01  # 新增代码+OsEncryptedSecretStore：禁止 DPAPI 弹系统 UI；如果没有这行，后台 bridge 可能被系统凭据弹窗卡住。


class GuiProviderSecretStoreError(RuntimeError):  # 新增代码+SecretStoreFactory：类段开始，承载密钥存储选择和 OS 加密失败；如果没有这个类，调用方只能看到模糊 RuntimeError。
    def __init__(self, code: str, message: str) -> None:  # 新增代码+SecretStoreFactory：函数段开始，保存机器码和说明；如果没有这段，测试和 UI 无法精确判断失败原因。
        super().__init__(message)  # 新增代码+SecretStoreFactory：把说明传给 RuntimeError；如果没有这行，日志里会缺少可读错误。
        self.code = code  # 新增代码+SecretStoreFactory：保存机器可读错误码；如果没有这行，真实 OAuth 门禁失败难以分类。
        self.message = message  # 新增代码+SecretStoreFactory：保存用户可读说明；如果没有这行，调用方只能依赖 str(error)。
    # 新增代码+SecretStoreFactory：函数段结束，GuiProviderSecretStoreError.__init__ 到此结束；如果没有边界说明，初学者不易看出错误字段范围。
# 新增代码+SecretStoreFactory：类段结束，GuiProviderSecretStoreError 到此结束；如果没有边界说明，初学者不易看出它只负责错误传递。


class _DATA_BLOB(ctypes.Structure):  # 新增代码+OsEncryptedSecretStore：类段开始，声明 Windows DPAPI 需要的 DATA_BLOB；如果没有这个结构，Python 无法把字节交给 CryptProtectData。
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]  # 新增代码+OsEncryptedSecretStore：定义长度和指针字段；如果没有这行，DPAPI 会读不到待加密数据。
    # 新增代码+OsEncryptedSecretStore：类段结束，_DATA_BLOB 到此结束；如果没有边界说明，初学者不易看出它只是 ctypes 结构。


def secret_settings_dir(workspace: str | Path) -> Path:  # 新增代码+ProviderSecretStore：函数段开始，定位 Provider 密钥目录；如果没有这段，多个模块会各自硬编码路径。
    return Path(workspace).expanduser().resolve() / "memory" / "gui_provider_settings"  # 新增代码+ProviderSecretStore：返回 workspace 内的密钥目录；如果没有这行，测试和真实项目会混用状态。
# 新增代码+ProviderSecretStore：函数段结束，secret_settings_dir 到此结束；如果没有边界说明，初学者不易看出它只负责路径。


def safe_secret_ref(provider_id: str, secret_name: str) -> str:  # 新增代码+ProviderSecretStore：函数段开始，生成稳定 secret 引用；如果没有这段，主配置无法用非明文方式指向密钥。
    clean_provider_id = str(provider_id).strip()  # 新增代码+ProviderSecretStore：清理 provider id 两端空白；如果没有这行，同一个 provider 可能生成不同引用。
    clean_secret_name = str(secret_name).strip()  # 新增代码+ProviderSecretStore：清理 secret 名称两端空白；如果没有这行，引用键可能包含隐藏空格。
    return f"provider:{clean_provider_id}:{clean_secret_name}"  # 新增代码+ProviderSecretStore：返回 provider 作用域引用；如果没有这行，主配置只能保存 raw key。
# 新增代码+ProviderSecretStore：函数段结束，safe_secret_ref 到此结束；如果没有边界说明，初学者不易看出它只负责引用格式。


def mask_secret_value(value: str) -> str:  # 新增代码+ProviderSecretStore：函数段开始，把密钥变成安全掩码；如果没有这段，UI 可能直接显示 raw key。
    text = str(value or "")  # 新增代码+ProviderSecretStore：把未知输入收敛为字符串；如果没有这行，None 会让长度判断报错。
    if not text:  # 新增代码+ProviderSecretStore：处理空密钥；如果没有这行，未连接状态可能显示奇怪掩码。
        return ""  # 新增代码+ProviderSecretStore：空密钥返回空掩码；如果没有这行，UI 无法区分未连接。
    if len(text) <= 8:  # 新增代码+ProviderSecretStore：短密钥不保留任何原文；如果没有这行，短 token 可能被完全暴露。
        return "••••"  # 新增代码+ProviderSecretStore：返回固定短掩码；如果没有这行，短密钥脱敏不充分。
    return f"{text[:2]}••••{text[-2:]}"  # 新增代码+ProviderSecretStore：只保留极少前后缀方便识别；如果没有这行，用户无法辨认当前连接是哪把 key。
# 新增代码+ProviderSecretStore：函数段结束，mask_secret_value 到此结束；如果没有边界说明，初学者不易看出它只负责显示掩码。


class GuiProviderSecretStore:  # 新增代码+ProviderSecretStore：类段开始，定义 Provider 密钥存储抽象；如果没有这个类，未来 OS 凭据存储没有替换边界。
    kind = "abstract"  # 新增代码+ProviderSecretStore：声明抽象存储类型；如果没有这行，UI 无法显示当前密钥存储类别。

    def set_secret(self, secret_ref: str, value: str) -> str:  # 新增代码+ProviderSecretStore：函数段开始，声明写入密钥接口；如果没有这段，调用方会依赖具体 DevJsonSecretStore。
        raise NotImplementedError  # 新增代码+ProviderSecretStore：要求子类实现；如果没有这行，抽象类误用会静默失败。
    # 新增代码+ProviderSecretStore：函数段结束，set_secret 到此结束；如果没有边界说明，初学者不易看出它是抽象接口。

    def get_secret(self, secret_ref: str) -> str:  # 新增代码+ProviderSecretStore：函数段开始，声明后端内部取密钥接口；如果没有这段，连接探针无法读取 secret。
        raise NotImplementedError  # 新增代码+ProviderSecretStore：要求子类实现；如果没有这行，抽象类误用会静默失败。
    # 新增代码+ProviderSecretStore：函数段结束，get_secret 到此结束；如果没有边界说明，初学者不易看出它只供后端内部使用。

    def delete_secret(self, secret_ref: str) -> None:  # 新增代码+ProviderSecretStore：函数段开始，声明删除密钥接口；如果没有这段，断开连接会留下旧 key。
        raise NotImplementedError  # 新增代码+ProviderSecretStore：要求子类实现；如果没有这行，抽象类误用会静默失败。
    # 新增代码+ProviderSecretStore：函数段结束，delete_secret 到此结束；如果没有边界说明，初学者不易看出它只负责清理 secret。

    def mask_secret(self, secret_ref: str) -> str:  # 新增代码+ProviderSecretStore：函数段开始，声明脱敏显示接口；如果没有这段，UI 无法显示已连接但不泄密的状态。
        raise NotImplementedError  # 新增代码+ProviderSecretStore：要求子类实现；如果没有这行，抽象类误用会静默失败。
    # 新增代码+ProviderSecretStore：函数段结束，mask_secret 到此结束；如果没有边界说明，初学者不易看出它只返回安全文本。


class OsEncryptedSecretStore(GuiProviderSecretStore):  # 新增代码+OsEncryptedSecretStore：类段开始，使用 Windows DPAPI CurrentUser 保存真实 OAuth token；如果没有这个类，真实 refresh token 只能落到开发 JSON。
    kind = "os_encrypted"  # 新增代码+OsEncryptedSecretStore：声明 OS 加密存储类型；如果没有这行，真实 OAuth 门禁无法确认安全存储已启用。

    def __init__(self, workspace: str | Path) -> None:  # 新增代码+OsEncryptedSecretStore：函数段开始，初始化 OS 加密 secret store；如果没有这段，store 不知道密文文件位置。
        self.workspace = Path(workspace).expanduser().resolve()  # 新增代码+OsEncryptedSecretStore：保存规范化 workspace；如果没有这行，相对路径会把密文写到不可预期目录。
        self.root = secret_settings_dir(self.workspace)  # 新增代码+OsEncryptedSecretStore：保存 provider 设置目录；如果没有这行，每次读写都要重复计算路径。
        self.path = self.root / "secrets.os.json"  # 新增代码+OsEncryptedSecretStore：保存 OS 加密密文文件路径；如果没有这行，密文无法稳定落盘。
    # 新增代码+OsEncryptedSecretStore：函数段结束，__init__ 到此结束；如果没有边界说明，初学者不易看出实例字段范围。

    def _ensure_windows_dpapi(self) -> None:  # 新增代码+OsEncryptedSecretStore：函数段开始，确认当前机器支持 Windows DPAPI；如果没有这段，非 Windows 会得到难懂的 ctypes 错误。
        if sys.platform != "win32":  # 新增代码+OsEncryptedSecretStore：只允许 Windows 当前用户 DPAPI；如果没有这行，Linux/macOS 会误以为已有 OS 加密。
            raise GuiProviderSecretStoreError("os_encrypted_store_unavailable", "OS encrypted provider secret store requires Windows DPAPI CurrentUser.")  # 新增代码+OsEncryptedSecretStore：抛出明确不可用错误；如果没有这行，真实 OAuth token 可能进入不安全 fallback。
    # 新增代码+OsEncryptedSecretStore：函数段结束，_ensure_windows_dpapi 到此结束；如果没有边界说明，初学者不易看出它只做平台门禁。

    def _protect_bytes(self, plaintext: bytes) -> bytes:  # 新增代码+OsEncryptedSecretStore：函数段开始，把明文字节交给 DPAPI 加密；如果没有这段，secrets.os.json 会含 raw token。
        self._ensure_windows_dpapi()  # 新增代码+OsEncryptedSecretStore：先确认 DPAPI 可用；如果没有这行，非 Windows 错误会发生在更深处。
        crypt32 = ctypes.windll.crypt32  # 新增代码+OsEncryptedSecretStore：加载 CryptProtectData 所在系统库；如果没有这行，无法调用 Windows 加密 API。
        kernel32 = ctypes.windll.kernel32  # 新增代码+OsEncryptedSecretStore：加载 LocalFree 所在系统库；如果没有这行，DPAPI 返回内存无法释放。
        input_buffer = ctypes.create_string_buffer(plaintext)  # 新增代码+OsEncryptedSecretStore：创建稳定输入缓冲区；如果没有这行，DPAPI 可能读到被移动的 Python bytes。
        input_blob = _DATA_BLOB(len(plaintext), ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_ubyte)))  # 新增代码+OsEncryptedSecretStore：把输入字节包装成 DATA_BLOB；如果没有这行，CryptProtectData 不知道输入长度。
        output_blob = _DATA_BLOB()  # 新增代码+OsEncryptedSecretStore：准备接收 DPAPI 输出；如果没有这行，密文没有写入位置。
        ok = crypt32.CryptProtectData(ctypes.byref(input_blob), None, None, None, None, _CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(output_blob))  # 新增代码+OsEncryptedSecretStore：调用 CurrentUser DPAPI 加密；如果没有这行，真实 token 不会被系统级加密。
        if not ok:  # 新增代码+OsEncryptedSecretStore：检查 Windows API 返回值；如果没有这行，加密失败会被误当成功。
            raise ctypes.WinError()  # 新增代码+OsEncryptedSecretStore：抛出系统错误码；如果没有这行，用户无法知道 DPAPI 为什么失败。
        try:  # 新增代码+OsEncryptedSecretStore：保护 DPAPI 输出读取；如果没有这行，读取异常会跳过 LocalFree。
            return ctypes.string_at(output_blob.pbData, output_blob.cbData)  # 新增代码+OsEncryptedSecretStore：复制密文字节回 Python；如果没有这行，后续无法 base64 保存。
        finally:  # 新增代码+OsEncryptedSecretStore：确保释放 DPAPI 分配的内存；如果没有这行，频繁连接/刷新会泄漏本机进程内存。
            kernel32.LocalFree(output_blob.pbData)  # 新增代码+OsEncryptedSecretStore：释放系统分配的密文缓冲区；如果没有这行，bridge 长期运行会累积内存。
    # 新增代码+OsEncryptedSecretStore：函数段结束，_protect_bytes 到此结束；如果没有边界说明，初学者不易看出它只做加密。

    def _unprotect_bytes(self, ciphertext: bytes) -> bytes:  # 新增代码+OsEncryptedSecretStore：函数段开始，把 DPAPI 密文字节解回明文；如果没有这段，后端无法用 token 发请求。
        self._ensure_windows_dpapi()  # 新增代码+OsEncryptedSecretStore：先确认 DPAPI 可用；如果没有这行，非 Windows 错误会更难定位。
        crypt32 = ctypes.windll.crypt32  # 新增代码+OsEncryptedSecretStore：加载 CryptUnprotectData 所在系统库；如果没有这行，无法调用 Windows 解密 API。
        kernel32 = ctypes.windll.kernel32  # 新增代码+OsEncryptedSecretStore：加载 LocalFree 所在系统库；如果没有这行，DPAPI 返回内存无法释放。
        input_buffer = ctypes.create_string_buffer(ciphertext)  # 新增代码+OsEncryptedSecretStore：创建稳定密文输入缓冲区；如果没有这行，DPAPI 可能读到无效内存。
        input_blob = _DATA_BLOB(len(ciphertext), ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_ubyte)))  # 新增代码+OsEncryptedSecretStore：把密文包装成 DATA_BLOB；如果没有这行，CryptUnprotectData 不知道输入长度。
        output_blob = _DATA_BLOB()  # 新增代码+OsEncryptedSecretStore：准备接收解密输出；如果没有这行，明文没有写入位置。
        ok = crypt32.CryptUnprotectData(ctypes.byref(input_blob), None, None, None, None, _CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(output_blob))  # 新增代码+OsEncryptedSecretStore：调用 CurrentUser DPAPI 解密；如果没有这行，后端无法恢复 token。
        if not ok:  # 新增代码+OsEncryptedSecretStore：检查 Windows API 返回值；如果没有这行，坏密文会被当成空 token。
            raise ctypes.WinError()  # 新增代码+OsEncryptedSecretStore：抛出系统错误码；如果没有这行，用户无法定位解密失败原因。
        try:  # 新增代码+OsEncryptedSecretStore：保护 DPAPI 输出读取；如果没有这行，读取异常会跳过 LocalFree。
            return ctypes.string_at(output_blob.pbData, output_blob.cbData)  # 新增代码+OsEncryptedSecretStore：复制明文字节回 Python；如果没有这行，调用方拿不到 secret。
        finally:  # 新增代码+OsEncryptedSecretStore：确保释放 DPAPI 输出内存；如果没有这行，长期运行会泄漏本机进程内存。
            kernel32.LocalFree(output_blob.pbData)  # 新增代码+OsEncryptedSecretStore：释放系统分配的明文缓冲区；如果没有这行，内存不会及时归还系统。
    # 新增代码+OsEncryptedSecretStore：函数段结束，_unprotect_bytes 到此结束；如果没有边界说明，初学者不易看出它只做解密。

    def _load_unlocked(self) -> dict[str, dict[str, str]]:  # 新增代码+OsEncryptedSecretStore：函数段开始，在外部锁内读取密文 JSON；如果没有这段，读写逻辑会重复且容易漏掉坏文件处理。
        if not self.path.exists():  # 新增代码+OsEncryptedSecretStore：处理首次使用没有密文文件；如果没有这行，第一次打开设置页会报 FileNotFoundError。
            return {}  # 新增代码+OsEncryptedSecretStore：无文件时返回空存储；如果没有这行，未连接 provider 无法安全显示。
        try:  # 新增代码+OsEncryptedSecretStore：保护 JSON 解析；如果没有这行，损坏密文索引会让 GUI bridge 500。
            raw = json.loads(self.path.read_text(encoding="utf-8"))  # 新增代码+OsEncryptedSecretStore：读取并解析密文索引；如果没有这行，已保存 token 无法恢复。
        except json.JSONDecodeError:  # 新增代码+OsEncryptedSecretStore：捕获损坏 JSON；如果没有这行，坏文件无法自动隔离。
            corrupt_path = self.path.with_name(f"secrets.os.json.corrupt-{int(time.time())}")  # 新增代码+OsEncryptedSecretStore：生成损坏文件备份名；如果没有这行，原始坏文件会被直接覆盖。
            self.path.replace(corrupt_path)  # 新增代码+OsEncryptedSecretStore：移动损坏文件；如果没有这行，下一次读取仍会失败。
            return {}  # 新增代码+OsEncryptedSecretStore：损坏后使用空存储继续；如果没有这行，GUI 无法恢复到可用状态。
        if not isinstance(raw, dict):  # 新增代码+OsEncryptedSecretStore：防御非对象 JSON；如果没有这行，数组或字符串会让字段读取不稳定。
            return {}  # 新增代码+OsEncryptedSecretStore：非对象视为空存储；如果没有这行，坏类型会污染密文读取。
        return {str(key): value for key, value in raw.items() if isinstance(key, str) and isinstance(value, dict) and isinstance(value.get("ciphertext"), str)}  # 新增代码+OsEncryptedSecretStore：只保留带 ciphertext 的对象；如果没有这行，坏记录可能进入解密流程。
    # 新增代码+OsEncryptedSecretStore：函数段结束，_load_unlocked 到此结束；如果没有边界说明，初学者不易看出它必须在锁内调用。

    def _save_unlocked(self, data: dict[str, dict[str, str]]) -> None:  # 新增代码+OsEncryptedSecretStore：函数段开始，在外部锁内原子保存密文 JSON；如果没有这段，并发写入可能产生半截文件。
        self.root.mkdir(parents=True, exist_ok=True)  # 新增代码+OsEncryptedSecretStore：确保密文目录存在；如果没有这行，第一次保存会因目录缺失失败。
        temp_path = self.path.with_suffix(".tmp")  # 新增代码+OsEncryptedSecretStore：准备临时文件路径；如果没有这行，无法先完整写入再替换。
        temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")  # 新增代码+OsEncryptedSecretStore：写入格式化密文 JSON；如果没有这行，token 密文不会持久化。
        temp_path.replace(self.path)  # 新增代码+OsEncryptedSecretStore：用完整临时文件替换目标；如果没有这行，崩溃时可能留下半写 JSON。
    # 新增代码+OsEncryptedSecretStore：函数段结束，_save_unlocked 到此结束；如果没有边界说明，初学者不易看出它只负责原子写。

    def set_secret(self, secret_ref: str, value: str) -> str:  # 新增代码+OsEncryptedSecretStore：函数段开始，加密并写入 secret；如果没有这段，真实 OAuth token 无法安全保存。
        clean_ref = str(secret_ref).strip()  # 新增代码+OsEncryptedSecretStore：清理引用空白；如果没有这行，引用键可能因为隐藏空格无法匹配。
        clean_value = str(value or "")  # 新增代码+OsEncryptedSecretStore：收敛 secret 值为字符串；如果没有这行，None 会写成异常类型。
        encrypted = base64.b64encode(self._protect_bytes(clean_value.encode("utf-8"))).decode("ascii")  # 新增代码+OsEncryptedSecretStore：用 DPAPI 加密后转 base64；如果没有这行，JSON 会包含明文或不可写二进制。
        with _SECRET_STORE_LOCK:  # 新增代码+OsEncryptedSecretStore：锁住读改写全过程；如果没有这行，并发连接可能丢数据。
            data = self._load_unlocked()  # 新增代码+OsEncryptedSecretStore：读取当前密文字典；如果没有这行，保存新 token 会覆盖旧 token。
            data[clean_ref] = {"version": "dpapi-current-user-v1", "ciphertext": encrypted}  # 新增代码+OsEncryptedSecretStore：写入密文记录；如果没有这行，set_secret 没有效果。
            self._save_unlocked(data)  # 新增代码+OsEncryptedSecretStore：原子保存更新后字典；如果没有这行，密文只在内存存在。
        return clean_ref  # 新增代码+OsEncryptedSecretStore：返回稳定引用；如果没有这行，调用方无法写入主配置 secret_ref。
    # 新增代码+OsEncryptedSecretStore：函数段结束，set_secret 到此结束；如果没有边界说明，初学者不易看出它会写密文磁盘。

    def get_secret(self, secret_ref: str) -> str:  # 新增代码+OsEncryptedSecretStore：函数段开始，后端内部读取并解密 secret；如果没有这段，Direct SSE 运行时无法拿 token。
        clean_ref = str(secret_ref).strip()  # 新增代码+OsEncryptedSecretStore：清理引用空白；如果没有这行，同一引用可能查不到。
        with _SECRET_STORE_LOCK:  # 新增代码+OsEncryptedSecretStore：锁住读取；如果没有这行，读写同时发生时可能看到半状态。
            record = self._load_unlocked().get(clean_ref, {})  # 新增代码+OsEncryptedSecretStore：读取目标密文记录；如果没有这行，后续无法判断是否存在。
        ciphertext = str(record.get("ciphertext", "")) if isinstance(record, dict) else ""  # 新增代码+OsEncryptedSecretStore：取出 base64 密文；如果没有这行，坏记录会进入解密。
        if not ciphertext:  # 新增代码+OsEncryptedSecretStore：处理未保存 secret；如果没有这行，空字符串会触发 base64/DPAPI 错误。
            return ""  # 新增代码+OsEncryptedSecretStore：缺失时返回空；如果没有这行，调用方要到处捕获异常。
        plaintext = self._unprotect_bytes(base64.b64decode(ciphertext.encode("ascii")))  # 新增代码+OsEncryptedSecretStore：base64 解码并交给 DPAPI 解密；如果没有这行，后端拿不到 raw secret。
        return plaintext.decode("utf-8")  # 新增代码+OsEncryptedSecretStore：把明文字节转回字符串；如果没有这行，调用方会收到 bytes。
    # 新增代码+OsEncryptedSecretStore：函数段结束，get_secret 到此结束；如果没有边界说明，初学者不易看出它只供后端内部使用。

    def delete_secret(self, secret_ref: str) -> None:  # 新增代码+OsEncryptedSecretStore：函数段开始，删除指定密文记录；如果没有这段，断开 OAuth 后 token 引用仍留在磁盘。
        clean_ref = str(secret_ref).strip()  # 新增代码+OsEncryptedSecretStore：清理引用空白；如果没有这行，删除可能找不到目标。
        with _SECRET_STORE_LOCK:  # 新增代码+OsEncryptedSecretStore：锁住读改写全过程；如果没有这行，并发删除和保存可能互相覆盖。
            data = self._load_unlocked()  # 新增代码+OsEncryptedSecretStore：读取当前密文字典；如果没有这行，删除不知道现有键。
            data.pop(clean_ref, None)  # 新增代码+OsEncryptedSecretStore：删除目标密文并容忍不存在；如果没有这行，重复断开会失败。
            self._save_unlocked(data)  # 新增代码+OsEncryptedSecretStore：保存删除后的字典；如果没有这行，磁盘仍保留旧 token 密文。
    # 新增代码+OsEncryptedSecretStore：函数段结束，delete_secret 到此结束；如果没有边界说明，初学者不易看出它会清理密文磁盘。

    def mask_secret(self, secret_ref: str) -> str:  # 新增代码+OsEncryptedSecretStore：函数段开始，按引用返回脱敏 secret；如果没有这段，catalog 无法显示已连接但不泄密的状态。
        return mask_secret_value(self.get_secret(secret_ref))  # 新增代码+OsEncryptedSecretStore：读取后立即脱敏；如果没有这行，调用方可能误返回 raw token。
    # 新增代码+OsEncryptedSecretStore：函数段结束，mask_secret 到此结束；如果没有边界说明，初学者不易看出它只返回安全文本。

    def info(self) -> dict[str, Any]:  # 新增代码+OsEncryptedSecretStore：函数段开始，返回给 UI 的密钥存储摘要；如果没有这段，设置页无法提示真实 token 使用 OS 加密。
        return {"kind": self.kind, "label": "系统加密密钥存储", "warning": ""}  # 新增代码+OsEncryptedSecretStore：返回不含路径和 token 的存储信息；如果没有这行，UI 可能暴露本机目录。
    # 新增代码+OsEncryptedSecretStore：函数段结束，info 到此结束；如果没有边界说明，初学者不易看出它只给 UI 安全摘要。
# 新增代码+OsEncryptedSecretStore：类段结束，OsEncryptedSecretStore 到此结束；如果没有边界说明，初学者不易看出它是 OS 加密存储实现。


class DevJsonSecretStore(GuiProviderSecretStore):  # 新增代码+ProviderSecretStore：类段开始，提供本地开发 JSON 密钥存储；如果没有这个类，V1 无法在无 OS 凭据实现时跑通。
    kind = "dev_json"  # 新增代码+ProviderSecretStore：声明这是开发存储；如果没有这行，UI 无法提示它不是生产级 OS 凭据。

    def __init__(self, workspace: str | Path) -> None:  # 新增代码+ProviderSecretStore：函数段开始，初始化开发密钥存储；如果没有这段，store 不知道文件位置。
        self.workspace = Path(workspace).expanduser().resolve()  # 新增代码+ProviderSecretStore：保存规范化 workspace；如果没有这行，相对路径会导致密钥写错位置。
        self.root = secret_settings_dir(self.workspace)  # 新增代码+ProviderSecretStore：保存密钥根目录；如果没有这行，每次读写都要重复计算路径。
        self.path = self.root / "secrets.dev.json"  # 新增代码+ProviderSecretStore：保存开发密钥文件路径；如果没有这行，密钥无法稳定落盘。
    # 新增代码+ProviderSecretStore：函数段结束，__init__ 到此结束；如果没有边界说明，初学者不易看出实例字段范围。

    def _load_unlocked(self) -> dict[str, str]:  # 新增代码+ProviderSecretStore：函数段开始，在外部锁内读取密钥 JSON；如果没有这段，读写逻辑会重复且容易漏掉损坏处理。
        if not self.path.exists():  # 新增代码+ProviderSecretStore：处理首次使用无文件场景；如果没有这行，第一次读取会抛 FileNotFoundError。
            return {}  # 新增代码+ProviderSecretStore：无文件时返回空存储；如果没有这行，未连接 provider 无法安全显示。
        try:  # 新增代码+ProviderSecretStore：保护 JSON 解析；如果没有这行，损坏文件会让整个 GUI bridge 500。
            raw = json.loads(self.path.read_text(encoding="utf-8"))  # 新增代码+ProviderSecretStore：读取并解析开发密钥文件；如果没有这行，store 无法恢复已保存密钥。
        except json.JSONDecodeError:  # 新增代码+ProviderSecretStore：捕获损坏 JSON；如果没有这行，坏文件无法自动隔离。
            corrupt_path = self.path.with_name(f"secrets.dev.json.corrupt-{int(time.time())}")  # 新增代码+ProviderSecretStore：生成损坏文件备份名；如果没有这行，原始坏文件会被直接覆盖。
            self.path.replace(corrupt_path)  # 新增代码+ProviderSecretStore：移动损坏文件；如果没有这行，下一次读取仍会失败。
            return {}  # 新增代码+ProviderSecretStore：损坏后使用空存储继续；如果没有这行，GUI 无法恢复到可用状态。
        if not isinstance(raw, dict):  # 新增代码+ProviderSecretStore：防御非对象 JSON；如果没有这行，数组或字符串会让字段读取不稳定。
            return {}  # 新增代码+ProviderSecretStore：非对象视为空存储；如果没有这行，坏类型会污染密钥读取。
        return {str(key): str(value) for key, value in raw.items() if isinstance(key, str) and isinstance(value, str)}  # 新增代码+ProviderSecretStore：只保留字符串键值；如果没有这行，未知类型可能进入 secret store。
    # 新增代码+ProviderSecretStore：函数段结束，_load_unlocked 到此结束；如果没有边界说明，初学者不易看出它必须在锁内调用。

    def _save_unlocked(self, data: dict[str, str]) -> None:  # 新增代码+ProviderSecretStore：函数段开始，在外部锁内原子写入密钥 JSON；如果没有这段，并发写入可能产生半截文件。
        self.root.mkdir(parents=True, exist_ok=True)  # 新增代码+ProviderSecretStore：确保密钥目录存在；如果没有这行，第一次保存会因目录缺失失败。
        temp_path = self.path.with_suffix(".tmp")  # 新增代码+ProviderSecretStore：准备临时文件路径；如果没有这行，无法先写完整再替换。
        temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")  # 新增代码+ProviderSecretStore：写入格式化 JSON；如果没有这行，密钥不会持久化。
        temp_path.replace(self.path)  # 新增代码+ProviderSecretStore：用完整临时文件替换目标；如果没有这行，崩溃时可能留下半写 JSON。
    # 新增代码+ProviderSecretStore：函数段结束，_save_unlocked 到此结束；如果没有边界说明，初学者不易看出它只负责原子写。

    def set_secret(self, secret_ref: str, value: str) -> str:  # 新增代码+ProviderSecretStore：函数段开始，写入或更新密钥；如果没有这段，连接 provider 后无法保存 secret_ref 对应值。
        clean_ref = str(secret_ref).strip()  # 新增代码+ProviderSecretStore：清理引用空白；如果没有这行，引用键可能因为隐藏空格无法匹配。
        clean_value = str(value or "")  # 新增代码+ProviderSecretStore：收敛密钥值为字符串；如果没有这行，None 会写成异常类型。
        with _SECRET_STORE_LOCK:  # 新增代码+ProviderSecretStore：锁住读改写全过程；如果没有这行，并发连接可能丢数据。
            data = self._load_unlocked()  # 新增代码+ProviderSecretStore：读取当前密钥字典；如果没有这行，保存新 key 会覆盖旧 key。
            data[clean_ref] = clean_value  # 新增代码+ProviderSecretStore：写入目标密钥；如果没有这行，set_secret 没有效果。
            self._save_unlocked(data)  # 新增代码+ProviderSecretStore：原子保存更新后字典；如果没有这行，密钥只在内存存在。
        return clean_ref  # 新增代码+ProviderSecretStore：返回稳定引用；如果没有这行，调用方无法写入主配置 secret_ref。
    # 新增代码+ProviderSecretStore：函数段结束，set_secret 到此结束；如果没有边界说明，初学者不易看出它会写磁盘。

    def get_secret(self, secret_ref: str) -> str:  # 新增代码+ProviderSecretStore：函数段开始，后端内部读取密钥；如果没有这段，连接探针无法认证请求。
        clean_ref = str(secret_ref).strip()  # 新增代码+ProviderSecretStore：清理引用空白；如果没有这行，同一引用可能查不到。
        with _SECRET_STORE_LOCK:  # 新增代码+ProviderSecretStore：锁住读取；如果没有这行，读写同时发生时可能看到半状态。
            return self._load_unlocked().get(clean_ref, "")  # 新增代码+ProviderSecretStore：返回密钥或空字符串；如果没有这行，调用方要自己处理 KeyError。
    # 新增代码+ProviderSecretStore：函数段结束，get_secret 到此结束；如果没有边界说明，初学者不易看出它不能给 renderer 调用。

    def delete_secret(self, secret_ref: str) -> None:  # 新增代码+ProviderSecretStore：函数段开始，删除指定密钥；如果没有这段，断开 provider 后 secret 仍会留在磁盘。
        clean_ref = str(secret_ref).strip()  # 新增代码+ProviderSecretStore：清理引用空白；如果没有这行，删除可能找不到目标。
        with _SECRET_STORE_LOCK:  # 新增代码+ProviderSecretStore：锁住读改写全过程；如果没有这行，并发删除和保存可能互相覆盖。
            data = self._load_unlocked()  # 新增代码+ProviderSecretStore：读取当前密钥字典；如果没有这行，删除不知道现有键。
            data.pop(clean_ref, None)  # 新增代码+ProviderSecretStore：删除目标密钥并容忍不存在；如果没有这行，disconnect 可能因重复删除失败。
            self._save_unlocked(data)  # 新增代码+ProviderSecretStore：保存删除后的字典；如果没有这行，磁盘仍保留旧密钥。
    # 新增代码+ProviderSecretStore：函数段结束，delete_secret 到此结束；如果没有边界说明，初学者不易看出它会清理磁盘。

    def mask_secret(self, secret_ref: str) -> str:  # 新增代码+ProviderSecretStore：函数段开始，按引用返回脱敏密钥；如果没有这段，catalog 无法显示已连接状态的安全摘要。
        return mask_secret_value(self.get_secret(secret_ref))  # 新增代码+ProviderSecretStore：读取后立即脱敏；如果没有这行，调用方可能误返回 raw key。
    # 新增代码+ProviderSecretStore：函数段结束，mask_secret 到此结束；如果没有边界说明，初学者不易看出它只返回掩码。

    def info(self) -> dict[str, Any]:  # 新增代码+ProviderSecretStore：函数段开始，返回给 UI 的密钥存储摘要；如果没有这段，设置页无法提示 dev_json 风险。
        return {"kind": self.kind, "label": "本地开发密钥存储", "warning": "当前密钥仅适合本机开发实验，真实生产密钥需要接入系统凭据存储。"}  # 新增代码+ProviderSecretStore：返回不含路径的存储信息；如果没有这行，UI 可能暴露本机目录。
    # 新增代码+ProviderSecretStore：函数段结束，info 到此结束；如果没有边界说明，初学者不易看出它只给 UI 安全摘要。


def _env_secret_store_kind(env: Mapping[str, str]) -> str:  # 新增代码+SecretStoreFactory：函数段开始，读取 provider secret store 类型；如果没有这段，真实 OAuth 和开发模式会各自解析环境变量。
    return str(env.get("OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json") or "dev_json").strip().lower()  # 新增代码+SecretStoreFactory：默认 dev_json 并规范大小写；如果没有这行，空环境变量会变成未知类型。
# 新增代码+SecretStoreFactory：函数段结束，_env_secret_store_kind 到此结束；如果没有边界说明，初学者不易看出它只读一个 env。


def _env_openai_auth_mode(env: Mapping[str, str]) -> str:  # 新增代码+SecretStoreFactory：函数段开始，读取 OpenAI OAuth 模式；如果没有这段，factory 无法知道是否处在真实 OAuth 模式。
    return str(env.get("OPENHARNESS_OPENAI_AUTH_MODE", "mock") or "mock").strip().lower()  # 新增代码+SecretStoreFactory：默认 mock 并规范大小写；如果没有这行，空环境变量会被误当真实模式。
# 新增代码+SecretStoreFactory：函数段结束，_env_openai_auth_mode 到此结束；如果没有边界说明，初学者不易看出它只读认证模式。


def make_provider_secret_store(workspace: str | Path, env: Mapping[str, str] | None = None) -> GuiProviderSecretStore:  # 新增代码+SecretStoreFactory：函数段开始，根据环境创建 provider secret store；如果没有这段，各调用点会继续硬编码 DevJsonSecretStore。
    source_env = os.environ if env is None else env  # 新增代码+SecretStoreFactory：真实运行读 os.environ、测试可注入 env；如果没有这行，测试会污染用户本机环境。
    store_kind = _env_secret_store_kind(source_env)  # 新增代码+SecretStoreFactory：读取目标存储类型；如果没有这行，factory 不知道返回哪个实现。
    auth_mode = _env_openai_auth_mode(source_env)  # 新增代码+SecretStoreFactory：读取当前 OpenAI auth 模式；如果没有这行，真实 OAuth 无法强制 OS 加密。
    real_oauth_mode = auth_mode in {"real_browser", "real_headless"}  # 新增代码+SecretStoreFactory：识别真实 OAuth 模式；如果没有这行，refresh token 可能写入开发 JSON。
    if real_oauth_mode and store_kind != "os_encrypted":  # 新增代码+SecretStoreFactory：真实 OAuth 必须使用 OS 加密存储；如果没有这行，用户的 ChatGPT token 会落到不安全文件。
        raise GuiProviderSecretStoreError("os_encrypted_secret_store_required", "Real OpenAI OAuth requires OPENHARNESS_PROVIDER_SECRET_STORE=os_encrypted.")  # 新增代码+SecretStoreFactory：抛出明确门禁错误；如果没有这行，调用方可能误继续保存真实 token。
    if store_kind == "os_encrypted":  # 新增代码+SecretStoreFactory：识别 OS 加密存储；如果没有这行，显式配置 os_encrypted 不会生效。
        return OsEncryptedSecretStore(workspace)  # 新增代码+SecretStoreFactory：返回 DPAPI CurrentUser 存储；如果没有这行，真实 OAuth 没有安全落盘路径。
    if store_kind in {"", "dev_json"}:  # 新增代码+SecretStoreFactory：允许空值和开发 JSON；如果没有这行，稳定 V1 mock/API-key 测试会被破坏。
        return DevJsonSecretStore(workspace)  # 新增代码+SecretStoreFactory：返回开发 JSON 存储；如果没有这行，本地测试和 mock provider 无法保存 secret。
    raise GuiProviderSecretStoreError("unsupported_secret_store", f"Unsupported provider secret store: {store_kind}")  # 新增代码+SecretStoreFactory：拒绝未知存储类型；如果没有这行，拼写错误会悄悄退回不安全默认。
# 新增代码+SecretStoreFactory：函数段结束，make_provider_secret_store 到此结束；如果没有边界说明，初学者不易看出它是唯一选择入口。
