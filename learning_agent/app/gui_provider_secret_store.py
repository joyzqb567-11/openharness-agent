"""Provider 设置页专用密钥存储。"""  # 新增代码+ProviderSecretStore：说明本模块只负责 Provider 密钥引用和开发存储；如果没有这行，维护者容易把它误当成模型运行时。

from __future__ import annotations  # 新增代码+ProviderSecretStore：启用延迟类型解析；如果没有这行，后续类型注解在旧解释顺序下更脆弱。

import json  # 新增代码+ProviderSecretStore：读写开发密钥 JSON；如果没有这行，DevJsonSecretStore 无法持久化密钥。
import threading  # 新增代码+ProviderSecretStore：保护密钥文件并发写入；如果没有这行，快速点击连接/断开可能写坏 JSON。
import time  # 新增代码+ProviderSecretStore：生成损坏文件归档时间戳；如果没有这行，坏 JSON 备份文件名不稳定。
from pathlib import Path  # 新增代码+ProviderSecretStore：用 Path 处理 Windows 和临时目录；如果没有这行，路径拼接容易出错。
from typing import Any  # 新增代码+ProviderSecretStore：标注未知 JSON 对象；如果没有这行，helper 的输入边界不清楚。


_SECRET_STORE_LOCK = threading.Lock()  # 新增代码+ProviderSecretStore：集中锁住开发密钥文件写入；如果没有这行，并发保存会互相覆盖。


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
