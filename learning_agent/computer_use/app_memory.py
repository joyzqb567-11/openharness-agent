"""Windows Computer Use app memory and self-learning store."""  # 新增代码+Phase73AppMemory: 标明本文件负责 Phase73 非敏感应用记忆；如果没有这行代码，读者不知道 app hint 学习逻辑集中在哪里。
from __future__ import annotations  # 新增代码+Phase73AppMemory: 启用延迟类型解析；如果没有这行代码，类型注解在旧导入顺序下更容易失败。

import hashlib  # 新增代码+Phase73AppMemory: 导入哈希工具生成 hint_id 和脱敏证据；如果没有这行代码，记忆和拒绝审计难以追踪但又不泄露原文。
import json  # 新增代码+Phase73AppMemory: 导入 JSON 用于 CLI 输出结构化报告；如果没有这行代码，真实终端失败时不易复盘。
import re  # 新增代码+Phase73AppMemory: 导入正则清理 app 名和检测敏感模式；如果没有这行代码，路径和隐私检测会更脆弱。
import time  # 新增代码+Phase73AppMemory: 导入时间用于 created_at/updated_at/revoked_at；如果没有这行代码，记忆新旧和撤销无法审计。
from pathlib import Path  # 新增代码+Phase73AppMemory: 导入 Path 统一处理 Windows 路径；如果没有这行代码，状态目录拼接更容易出错。
from typing import Any  # 新增代码+Phase73AppMemory: 导入 Any 描述 JSON 风格输入输出；如果没有这行代码，接口边界不清楚。

try:  # 新增代码+Phase73AppMemory: 优先按包路径导入安全文件工具；如果没有这段代码，包运行模式无法原子读写 app memory。
    from learning_agent.runtime.files import FileLock, append_jsonl, atomic_write_json, read_json_or_default  # 新增代码+Phase73AppMemory: 复用文件锁、审计追加、原子写和容错读；如果没有这行代码，并发 app memory 可能损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase73AppMemory: 兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，真实可见终端可能因包名前缀失败。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase73AppMemory: 只允许包路径缺失时 fallback；如果没有这行代码，runtime.files 内部真实错误会被误吞。
        raise  # 新增代码+Phase73AppMemory: 重新抛出非路径类导入错误；如果没有这行代码，底层 bug 会被隐藏。
    from runtime.files import FileLock, append_jsonl, atomic_write_json, read_json_or_default  # 新增代码+Phase73AppMemory: 脚本模式导入安全文件工具；如果没有这行代码，bat 入口无法保存 app memory。

PHASE73_APP_MEMORY_MARKER = "PHASE73_APP_MEMORY_READY"  # 新增代码+Phase73AppMemory: 定义 Phase73 ready marker；如果没有这行代码，真实终端验收没有稳定锚点。
PHASE73_APP_MEMORY_OK_TOKEN = "PHASE73_APP_MEMORY_OK"  # 新增代码+Phase73AppMemory: 定义 Phase73 OK token；如果没有这行代码，debug log 无法区分自检通过和普通输出。
PHASE73_APP_MEMORY_MODEL = "phase73_windows_app_memory"  # 新增代码+Phase73AppMemory: 定义 app memory 模型名；如果没有这行代码，状态和报告无法说明当前合同版本。
PHASE73_ACTIONS_EXPANDED = False  # 新增代码+Phase73AppMemory: 明确本阶段只增加非敏感记忆，不扩大真实动作能力；如果没有这行代码，用户可能误以为学习层会自动执行动作。
DEFAULT_APP_MEMORY_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "app_memory"  # 新增代码+Phase73AppMemory: 定义默认 app memory 目录；如果没有这行代码，生产入口不知道把记忆放在哪里。
PHASE73_ALLOWED_HINT_TYPES = {"window_class", "role_hint", "safe_control_name", "menu_label", "last_successful_strategy"}  # 新增代码+Phase73AppMemory: 定义允许保存的非敏感提示类型；如果没有这行代码，脚本或任意文本可能被写进 memory。
PHASE73_SECRET_TOKENS = {"password", "passcode", "credential", "token", "cookie", "secret", "captcha", "otp", "2fa", "verification code", "api key", "bearer", "private key", "credit card", "card number", "cvv", "bank", "payment", "ssn", "social security", "authentication", "auth code", "login code", "recovery key"}  # 新增代码+Phase73AppMemory: 定义敏感内容关键词；如果没有这行代码，密码、token、验证码和支付信息可能被记住。
PHASE73_TERMINAL_COMMAND_TOKENS = {"powershell", "powershell.exe", "pwsh", "cmd.exe", "cmd /c", "bash -c", "wsl.exe", "remove-item", "del /", "reg add", "reg delete", "schtasks", "net user", "curl ", "invoke-webrequest", "start-process"}  # 新增代码+Phase73AppMemory: 定义终端命令特征；如果没有这行代码，命令脚本可能伪装成策略记忆。


def _phase73_bool_token(value: Any) -> str:  # 新增代码+Phase73AppMemory: 函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会出现 True/False 漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase73AppMemory: 返回 true/false 文本；如果没有这行代码，验收场景匹配不稳定。
# 新增代码+Phase73AppMemory: 函数段结束，_phase73_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式范围。


def _phase73_timestamp(epoch_seconds: float | None = None) -> str:  # 新增代码+Phase73AppMemory: 函数段开始，生成 UTC 时间戳；如果没有这段函数，记忆和撤销无法按时间排序。
    source_seconds = time.time() if epoch_seconds is None else float(epoch_seconds)  # 新增代码+Phase73AppMemory: 使用当前时间或传入时间；如果没有这行代码，测试和生产不能复用统一格式。
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(source_seconds))  # 新增代码+Phase73AppMemory: 返回可排序 UTC 文本；如果没有这行代码，审计时间不稳定。
# 新增代码+Phase73AppMemory: 函数段结束，_phase73_timestamp 到此结束；如果没有这个边界说明，初学者不容易看出时间格式范围。


def _phase73_safe_text(value: Any, limit: int = 260) -> str:  # 新增代码+Phase73AppMemory: 函数段开始，把任意输入压成安全短文本；如果没有这段函数，换行或超长文本会污染状态和终端。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase73AppMemory: 去掉换行和首尾空白；如果没有这行代码，用户输入可能打散 JSONL 或状态面板。
    return text[:limit]  # 新增代码+Phase73AppMemory: 限制文本长度；如果没有这行代码，长窗口标题或策略会刷爆状态文件。
# 新增代码+Phase73AppMemory: 函数段结束，_phase73_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清理范围。


def _phase73_lower(value: Any, limit: int = 260) -> str:  # 新增代码+Phase73AppMemory: 函数段开始，生成小写安全文本；如果没有这段函数，敏感词和命令检测会受大小写影响。
    return _phase73_safe_text(value, limit=limit).lower()  # 新增代码+Phase73AppMemory: 返回小写短文本；如果没有这行代码，PowerShell/PASSWORD 等大小写变体可能漏检。
# 新增代码+Phase73AppMemory: 函数段结束，_phase73_lower 到此结束；如果没有这个边界说明，初学者不容易看出大小写规范范围。


def _phase73_app_key(app: Any) -> str:  # 新增代码+Phase73AppMemory: 函数段开始，规范化应用名；如果没有这段函数，同一 app 会因大小写或特殊字符重复记录。
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", _phase73_lower(app, 140))  # 新增代码+Phase73AppMemory: 只保留文件和状态友好的 app 字符；如果没有这行代码，外部输入可能污染索引。
    return cleaned[:140]  # 新增代码+Phase73AppMemory: 限制 app key 长度；如果没有这行代码，异常长 app 名会污染状态。
# 新增代码+Phase73AppMemory: 函数段结束，_phase73_app_key 到此结束；如果没有这个边界说明，初学者不容易看出 app 清理范围。


def _phase73_hint_type(value: Any) -> str:  # 新增代码+Phase73AppMemory: 函数段开始，规范化 hint_type；如果没有这段函数，类型大小写或空格会导致策略漂移。
    return re.sub(r"[^a-z0-9_]+", "_", _phase73_lower(value, 80)).strip("_")  # 新增代码+Phase73AppMemory: 返回小写下划线类型；如果没有这行代码，safe control name 等变体无法稳定匹配。
# 新增代码+Phase73AppMemory: 函数段结束，_phase73_hint_type 到此结束；如果没有这个边界说明，初学者不容易看出类型清理范围。


def _phase73_value_hash(value: Any) -> str:  # 新增代码+Phase73AppMemory: 函数段开始，生成脱敏值哈希；如果没有这段函数，拒绝审计要么泄露原文要么无法追踪。
    return hashlib.sha256(str(value or "").encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase73AppMemory: 返回短 SHA256；如果没有这行代码，审计无法证明同一拒绝输入但不泄露内容。
# 新增代码+Phase73AppMemory: 函数段结束，_phase73_value_hash 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。


def _phase73_contains_secret_or_private_text(value: Any) -> bool:  # 新增代码+Phase73AppMemory: 函数段开始，判断文本是否包含秘密或隐私内容；如果没有这段函数，app memory 可能泄露用户敏感信息。
    text = _phase73_lower(value, 900)  # 新增代码+Phase73AppMemory: 清理并小写输入文本；如果没有这行代码，敏感词大小写变体会漏检。
    if any(token in text for token in PHASE73_SECRET_TOKENS):  # 新增代码+Phase73AppMemory: 检查敏感关键词；如果没有这行代码，密码/token/支付等会被保存。
        return True  # 新增代码+Phase73AppMemory: 命中敏感词时拒绝；如果没有这行代码，调用方无法失败关闭。
    if re.search(r"\b\d{13,19}\b", text):  # 新增代码+Phase73AppMemory: 检查疑似长银行卡号或敏感编号；如果没有这行代码，纯数字支付信息可能漏检。
        return True  # 新增代码+Phase73AppMemory: 命中长数字时拒绝；如果没有这行代码，支付编号可能落盘。
    if re.search(r"sk-[a-z0-9_-]{6,}", text):  # 新增代码+Phase73AppMemory: 检查常见 API key 形态；如果没有这行代码，token 即使没有 token 字样也可能漏检。
        return True  # 新增代码+Phase73AppMemory: 命中 API key 形态时拒绝；如果没有这行代码，密钥可能落盘。
    return False  # 新增代码+Phase73AppMemory: 未发现敏感模式时返回安全；如果没有这行代码，所有提示都会被拒绝。
# 新增代码+Phase73AppMemory: 函数段结束，_phase73_contains_secret_or_private_text 到此结束；如果没有这个边界说明，初学者不容易看出隐私检测范围。


def _phase73_looks_like_terminal_command(value: Any) -> bool:  # 新增代码+Phase73AppMemory: 函数段开始，判断文本是否像终端命令或脚本；如果没有这段函数，app memory 可能变成命令仓库。
    text = _phase73_lower(value, 900)  # 新增代码+Phase73AppMemory: 清理并小写输入文本；如果没有这行代码，PowerShell/CMD 大小写变体可能漏检。
    return bool(any(token in text for token in PHASE73_TERMINAL_COMMAND_TOKENS))  # 新增代码+Phase73AppMemory: 命中终端命令特征则拒绝；如果没有这行代码，危险命令可能被当成策略保存。
# 新增代码+Phase73AppMemory: 函数段结束，_phase73_looks_like_terminal_command 到此结束；如果没有这个边界说明，初学者不容易看出命令检测范围。


def _phase73_confidence(value: Any) -> float:  # 新增代码+Phase73AppMemory: 函数段开始，规范化 confidence 到 0 到 1；如果没有这段函数，坏置信度会污染排序和状态。
    try:  # 新增代码+Phase73AppMemory: 捕获无法转成数字的输入；如果没有这行代码，字符串置信度会让记忆写入崩溃。
        numeric = float(value)  # 新增代码+Phase73AppMemory: 转成浮点数；如果没有这行代码，后续无法 clamp。
    except (TypeError, ValueError):  # 新增代码+Phase73AppMemory: 处理空值或坏字符串；如果没有这行代码，坏 confidence 无法容错。
        numeric = 0.5  # 新增代码+Phase73AppMemory: 坏输入使用中性置信度；如果没有这行代码，提示可能无故失败。
    return max(0.0, min(1.0, numeric))  # 新增代码+Phase73AppMemory: 限制在 0 到 1；如果没有这行代码，排序和 UI 可能显示异常值。
# 新增代码+Phase73AppMemory: 函数段结束，_phase73_confidence 到此结束；如果没有这个边界说明，初学者不容易看出置信度范围。


def _phase73_redacted_rejection_payload(app: str, hint_type: str, hint_value: Any, decision: str) -> dict[str, Any]:  # 新增代码+Phase73AppMemory: 函数段开始，构造不含原文的拒绝审计；如果没有这段函数，拒绝秘密时可能把秘密写进日志。
    return {"app": app, "hint_type": hint_type, "decision": decision, "value_hash": _phase73_value_hash(hint_value), "redacted": True, "marker": PHASE73_APP_MEMORY_MARKER, "model": PHASE73_APP_MEMORY_MODEL, "actions_expanded": PHASE73_ACTIONS_EXPANDED}  # 新增代码+Phase73AppMemory: 返回脱敏拒绝 payload；如果没有这行代码，审计无法安全记录拒绝原因。
# 新增代码+Phase73AppMemory: 函数段结束，_phase73_redacted_rejection_payload 到此结束；如果没有这个边界说明，初学者不容易看出拒绝审计范围。


class WindowsComputerUseAppMemoryStore:  # 新增代码+Phase73AppMemory: 类段开始，管理非敏感 app hints 的持久化、查询和撤销；如果没有这个类，自学习提示会散落且不可审计。
    def __init__(self, base_dir: str | Path | None = None, lock_timeout_seconds: float = 5.0) -> None:  # 新增代码+Phase73AppMemory: 函数段开始，初始化 app memory 目录和文件路径；如果没有这段函数，测试和生产无法隔离状态。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_APP_MEMORY_ROOT  # 新增代码+Phase73AppMemory: 保存状态根目录；如果没有这行代码，store 不知道读写哪里。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase73AppMemory: 确保目录存在；如果没有这行代码，首次写入 app memory 会失败。
        self.lock_timeout_seconds = float(lock_timeout_seconds)  # 新增代码+Phase73AppMemory: 保存文件锁等待时间；如果没有这行代码，并发等待没有明确边界。
        self.state_path = self.base_dir / "app_memory.json"  # 新增代码+Phase73AppMemory: 定义主状态文件；如果没有这行代码，记忆没有固定读取入口。
        self.audit_path = self.base_dir / "app_memory_audit.jsonl"  # 新增代码+Phase73AppMemory: 定义审计文件；如果没有这行代码，拒绝、写入和撤销无法回放。
        self.mutex_path = self.base_dir / ".app_memory.mutex"  # 新增代码+Phase73AppMemory: 定义互斥锁文件；如果没有这行代码，并发写入可能互相覆盖。
        self.quarantine_dir = self.base_dir / "quarantine"  # 新增代码+Phase73AppMemory: 定义坏 JSON 隔离目录；如果没有这行代码，损坏状态无法留证。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _default_state(self) -> dict[str, Any]:  # 新增代码+Phase73AppMemory: 函数段开始，构造默认 app memory 状态；如果没有这段函数，首次运行缺少完整字段。
        return {"schema_version": 1, "model": PHASE73_APP_MEMORY_MODEL, "marker": PHASE73_APP_MEMORY_MARKER, "hints": [], "created_at": _phase73_timestamp(), "updated_at": _phase73_timestamp(), "state_path": str(self.state_path), "audit_path": str(self.audit_path), "actions_expanded": PHASE73_ACTIONS_EXPANDED}  # 新增代码+Phase73AppMemory: 返回完整默认状态；如果没有这行代码，状态 UI 和合同会遇到缺字段。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore._default_state 到此结束；如果没有这个边界说明，初学者不容易看出默认状态范围。

    def _normalize_hint(self, hint: Any) -> dict[str, Any] | None:  # 新增代码+Phase73AppMemory: 函数段开始，规范化单条提示；如果没有这段函数，旧状态或坏状态会污染查询。
        if not isinstance(hint, dict):  # 新增代码+Phase73AppMemory: 只接受 dict 提示；如果没有这行代码，字符串或坏对象会让状态崩溃。
            return None  # 新增代码+Phase73AppMemory: 坏项直接丢弃；如果没有这行代码，后续字段读取会异常。
        app = _phase73_app_key(hint.get("app"))  # 新增代码+Phase73AppMemory: 规范化提示所属 app；如果没有这行代码，查询时 app 匹配会漂移。
        hint_type = _phase73_hint_type(hint.get("hint_type"))  # 新增代码+Phase73AppMemory: 规范化提示类型；如果没有这行代码，旧状态类型会不稳定。
        hint_value = _phase73_safe_text(hint.get("hint_value"), 360)  # 新增代码+Phase73AppMemory: 清理提示值；如果没有这行代码，换行或超长值会污染状态。
        if not app or hint_type not in PHASE73_ALLOWED_HINT_TYPES or not hint_value:  # 新增代码+Phase73AppMemory: 丢弃无效 app、类型和值；如果没有这行代码，空记忆会进入状态。
            return None  # 新增代码+Phase73AppMemory: 返回 None 表示不可用；如果没有这行代码，坏提示可能继续参与查询。
        return {"hint_id": _phase73_safe_text(hint.get("hint_id") or self._new_hint_id(app, hint_type, hint_value), 120), "app": app, "hint_type": hint_type, "hint_value": hint_value, "source": _phase73_safe_text(hint.get("source"), 180), "confidence": _phase73_confidence(hint.get("confidence", 0.5)), "created_at": _phase73_safe_text(hint.get("created_at") or _phase73_timestamp(), 80), "updated_at": _phase73_safe_text(hint.get("updated_at") or _phase73_timestamp(), 80), "revoked": bool(hint.get("revoked", False)), "revoked_at": _phase73_safe_text(hint.get("revoked_at"), 80), "revoked_reason": _phase73_safe_text(hint.get("revoked_reason"), 180)}  # 新增代码+Phase73AppMemory: 返回规范化提示；如果没有这行代码，查询和写入无法统一字段。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore._normalize_hint 到此结束；如果没有这个边界说明，初学者不容易看出提示清洗范围。

    def _normalize_state(self, payload: Any) -> dict[str, Any]:  # 新增代码+Phase73AppMemory: 函数段开始，把磁盘状态修复为标准结构；如果没有这段函数，坏状态会拖垮 app memory。
        state = self._default_state()  # 新增代码+Phase73AppMemory: 先创建完整默认状态；如果没有这行代码，缺字段无法补齐。
        if isinstance(payload, dict):  # 新增代码+Phase73AppMemory: 只有 dict 状态才合并；如果没有这行代码，坏类型会污染 state。
            state.update(dict(payload))  # 新增代码+Phase73AppMemory: 合并已有状态；如果没有这行代码，旧记忆无法恢复。
        normalized_hints = []  # 新增代码+Phase73AppMemory: 准备保存清洗后的提示；如果没有这行代码，函数没有提示容器。
        for hint in list(state.get("hints", [])) if isinstance(state.get("hints", []), list) else []:  # 新增代码+Phase73AppMemory: 遍历旧提示列表；如果没有这行代码，旧状态不会被清理。
            normalized = self._normalize_hint(hint)  # 新增代码+Phase73AppMemory: 清洗单条提示；如果没有这行代码，坏提示会残留。
            if normalized is not None:  # 新增代码+Phase73AppMemory: 只保留有效提示；如果没有这行代码，None 会污染列表。
                normalized_hints.append(normalized)  # 新增代码+Phase73AppMemory: 添加有效提示；如果没有这行代码，状态会丢失所有提示。
        state["hints"] = normalized_hints  # 新增代码+Phase73AppMemory: 写回规范提示列表；如果没有这行代码，调用方拿到的仍是坏列表。
        state["model"] = PHASE73_APP_MEMORY_MODEL  # 新增代码+Phase73AppMemory: 固定模型名；如果没有这行代码，旧状态可能显示错误模型。
        state["marker"] = PHASE73_APP_MEMORY_MARKER  # 新增代码+Phase73AppMemory: 固定 marker；如果没有这行代码，状态 UI 缺少阶段锚点。
        state["state_path"] = str(self.state_path)  # 新增代码+Phase73AppMemory: 刷新状态路径；如果没有这行代码，移动目录后 state_path 会过期。
        state["audit_path"] = str(self.audit_path)  # 新增代码+Phase73AppMemory: 刷新审计路径；如果没有这行代码，状态面板会指向旧审计文件。
        state["actions_expanded"] = PHASE73_ACTIONS_EXPANDED  # 新增代码+Phase73AppMemory: 固定动作边界；如果没有这行代码，学习层可能被误报为动作扩展。
        return state  # 新增代码+Phase73AppMemory: 返回规范化状态；如果没有这行代码，调用方拿不到清洗结果。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore._normalize_state 到此结束；如果没有这个边界说明，初学者不容易看出状态清洗范围。

    def _read_state(self) -> dict[str, Any]:  # 新增代码+Phase73AppMemory: 函数段开始，读取并规范化 app memory 状态；如果没有这段函数，每个公开方法都要重复容错读取。
        payload = read_json_or_default(self.state_path, {}, quarantine_dir=self.quarantine_dir)  # 新增代码+Phase73AppMemory: 容错读取 JSON 状态；如果没有这行代码，首次运行或半写文件会崩溃。
        return self._normalize_state(payload)  # 新增代码+Phase73AppMemory: 返回规范化状态；如果没有这行代码，坏状态不会被修复。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore._read_state 到此结束；如果没有这个边界说明，初学者不容易看出读取范围。

    def _write_state(self, state: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase73AppMemory: 函数段开始，原子写入 app memory 状态；如果没有这段函数，状态落盘会重复且不安全。
        state["updated_at"] = _phase73_timestamp()  # 新增代码+Phase73AppMemory: 刷新更新时间；如果没有这行代码，多轮记忆无法判断新旧。
        normalized = self._normalize_state(state)  # 新增代码+Phase73AppMemory: 写入前再规范化；如果没有这行代码，调用方坏字段可能落盘。
        atomic_write_json(self.state_path, normalized)  # 新增代码+Phase73AppMemory: 原子写入 JSON；如果没有这行代码，崩溃时可能留下半个状态文件。
        return normalized  # 新增代码+Phase73AppMemory: 返回实际写入内容；如果没有这行代码，调用方拿不到更新时间和规范字段。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore._write_state 到此结束；如果没有这个边界说明，初学者不容易看出写入范围。

    def _audit(self, event_type: str, payload: dict[str, Any]) -> None:  # 新增代码+Phase73AppMemory: 函数段开始，写入脱敏审计事件；如果没有这段函数，记忆写入、拒绝和撤销无法回放。
        event = {"event_type": _phase73_safe_text(event_type, 120), "created_at": _phase73_timestamp(), "payload": dict(payload or {}), "marker": PHASE73_APP_MEMORY_MARKER, "model": PHASE73_APP_MEMORY_MODEL}  # 新增代码+Phase73AppMemory: 构造审计事件；如果没有这行代码，事件缺少时间、阶段和内容。
        append_jsonl(self.audit_path, event)  # 新增代码+Phase73AppMemory: 追加写入 JSONL；如果没有这行代码，审计事件不会落盘。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore._audit 到此结束；如果没有这个边界说明，初学者不容易看出审计范围。

    def _new_hint_id(self, app: str, hint_type: str, hint_value: str) -> str:  # 新增代码+Phase73AppMemory: 函数段开始，生成稳定短 hint_id；如果没有这段函数，撤销和审计难以定位具体提示。
        seed = f"{app}|{hint_type}|{hint_value}"  # 新增代码+Phase73AppMemory: 构造稳定种子；如果没有这行代码，同一提示无法得到同一哈希来源。
        return "phase73-hint-" + hashlib.sha256(seed.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase73AppMemory: 返回短哈希 id；如果没有这行代码，id 会过长或不稳定。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore._new_hint_id 到此结束；如果没有这个边界说明，初学者不容易看出 id 生成范围。

    def remember_app_hint(self, app: Any, hint_type: Any, hint_value: Any, source: Any = "", confidence: Any = 0.5) -> dict[str, Any]:  # 新增代码+Phase73AppMemory: 函数段开始，记录一条非敏感 app 辅助提示；如果没有这段函数，agent 无法积累可撤销的应用使用经验。
        safe_app = _phase73_app_key(app)  # 新增代码+Phase73AppMemory: 清理 app 名；如果没有这行代码，同一应用无法稳定归档。
        safe_type = _phase73_hint_type(hint_type)  # 新增代码+Phase73AppMemory: 清理提示类型；如果没有这行代码，允许类型检查会漂移。
        safe_value = _phase73_safe_text(hint_value, 360)  # 新增代码+Phase73AppMemory: 清理提示值；如果没有这行代码，换行或超长值会污染状态。
        safe_source = _phase73_safe_text(source, 180)  # 新增代码+Phase73AppMemory: 清理来源文本；如果没有这行代码，审计来源可能刷屏。
        if not safe_app:  # 新增代码+Phase73AppMemory: app 为空时拒绝；如果没有这行代码，记忆会变成未知应用全局提示。
            result = {"remembered": False, "decision": "missing_app", "marker": PHASE73_APP_MEMORY_MARKER, "actions_expanded": PHASE73_ACTIONS_EXPANDED}  # 新增代码+Phase73AppMemory: 返回缺 app 拒绝；如果没有这行代码，用户不知道为什么没记住。
            self._audit("remember_rejected", _phase73_redacted_rejection_payload("", safe_type, hint_value, "missing_app"))  # 新增代码+Phase73AppMemory: 记录脱敏拒绝审计；如果没有这行代码，拒绝路径无法回放。
            return result  # 新增代码+Phase73AppMemory: 返回拒绝结果；如果没有这行代码，函数会继续写入坏记忆。
        if safe_type not in PHASE73_ALLOWED_HINT_TYPES:  # 新增代码+Phase73AppMemory: 只允许非敏感辅助提示类型；如果没有这行代码，脚本和任意文本可能落盘。
            payload = _phase73_redacted_rejection_payload(safe_app, safe_type, hint_value, "unsupported_hint_type")  # 新增代码+Phase73AppMemory: 构造脱敏拒绝 payload；如果没有这行代码，审计可能泄露原文。
            self._audit("remember_rejected", payload)  # 新增代码+Phase73AppMemory: 写入拒绝审计；如果没有这行代码，unsupported 类型不可追踪。
            return {"remembered": False, "decision": "unsupported_hint_type", "app": safe_app, "hint_type": safe_type, "redacted": True, "marker": PHASE73_APP_MEMORY_MARKER, "actions_expanded": PHASE73_ACTIONS_EXPANDED}  # 新增代码+Phase73AppMemory: 返回不支持类型拒绝；如果没有这行代码，调用方无法区分脚本拒绝。
        if _phase73_contains_secret_or_private_text(safe_value) or _phase73_contains_secret_or_private_text(safe_source):  # 新增代码+Phase73AppMemory: 检查提示值和来源是否包含秘密；如果没有这行代码，密码/token/支付信息可能落盘。
            payload = _phase73_redacted_rejection_payload(safe_app, safe_type, hint_value, "secret_or_private_content_rejected")  # 新增代码+Phase73AppMemory: 构造脱敏秘密拒绝；如果没有这行代码，秘密可能进入审计。
            self._audit("remember_rejected", payload)  # 新增代码+Phase73AppMemory: 写入脱敏拒绝审计；如果没有这行代码，秘密拒绝不可回放。
            return {"remembered": False, "decision": "secret_or_private_content_rejected", "app": safe_app, "hint_type": safe_type, "redacted": True, "marker": PHASE73_APP_MEMORY_MARKER, "actions_expanded": PHASE73_ACTIONS_EXPANDED}  # 新增代码+Phase73AppMemory: 返回秘密拒绝；如果没有这行代码，调用方无法知道内容被保护。
        if _phase73_looks_like_terminal_command(safe_value):  # 新增代码+Phase73AppMemory: 检查提示值是否像终端命令；如果没有这行代码，命令脚本可能伪装成成功策略。
            payload = _phase73_redacted_rejection_payload(safe_app, safe_type, hint_value, "terminal_command_rejected")  # 新增代码+Phase73AppMemory: 构造脱敏命令拒绝；如果没有这行代码，命令原文可能进入审计。
            self._audit("remember_rejected", payload)  # 新增代码+Phase73AppMemory: 写入命令拒绝审计；如果没有这行代码，命令拒绝不可追踪。
            return {"remembered": False, "decision": "terminal_command_rejected", "app": safe_app, "hint_type": safe_type, "redacted": True, "marker": PHASE73_APP_MEMORY_MARKER, "actions_expanded": PHASE73_ACTIONS_EXPANDED}  # 新增代码+Phase73AppMemory: 返回命令拒绝；如果没有这行代码，调用方无法区分命令和秘密。
        now = _phase73_timestamp()  # 新增代码+Phase73AppMemory: 捕获写入时间；如果没有这行代码，提示无法审计创建和更新时间。
        hint = {"hint_id": self._new_hint_id(safe_app, safe_type, safe_value), "app": safe_app, "hint_type": safe_type, "hint_value": safe_value, "source": safe_source, "confidence": _phase73_confidence(confidence), "created_at": now, "updated_at": now, "revoked": False, "revoked_at": "", "revoked_reason": ""}  # 新增代码+Phase73AppMemory: 构造安全提示记录；如果没有这行代码，状态缺少 app/type/value/source/confidence。
        with FileLock(self.mutex_path, timeout_seconds=self.lock_timeout_seconds):  # 新增代码+Phase73AppMemory: 用互斥锁保护读改写；如果没有这行代码，并发 remember 可能互相覆盖。
            state = self._read_state()  # 新增代码+Phase73AppMemory: 读取当前状态；如果没有这行代码，新提示会覆盖旧提示。
            existing = next((item for item in state["hints"] if item.get("hint_id") == hint["hint_id"] and not item.get("revoked", False)), None)  # 新增代码+Phase73AppMemory: 查找同一 active 提示；如果没有这行代码，重复学习会不断堆重复项。
            if existing is not None:  # 新增代码+Phase73AppMemory: 如果已有同一提示则更新元数据；如果没有这行代码，重复提示无法提权置信度或刷新时间。
                existing["confidence"] = max(float(existing.get("confidence", 0.0)), hint["confidence"])  # 新增代码+Phase73AppMemory: 保留更高置信度；如果没有这行代码，重复成功经验不能提升可信度。
                existing["source"] = safe_source or existing.get("source", "")  # 新增代码+Phase73AppMemory: 刷新来源但不强制清空；如果没有这行代码，来源信息可能过期。
                existing["updated_at"] = now  # 新增代码+Phase73AppMemory: 刷新更新时间；如果没有这行代码，用户无法看到提示被再次确认。
                saved = self._write_state(state)  # 新增代码+Phase73AppMemory: 写回更新后的状态；如果没有这行代码，重复提示更新不会落盘。
                self._audit("remember_updated", {"app": safe_app, "hint_type": safe_type, "hint_id": hint["hint_id"], "redacted": False, "marker": PHASE73_APP_MEMORY_MARKER, "actions_expanded": PHASE73_ACTIONS_EXPANDED})  # 新增代码+Phase73AppMemory: 记录更新审计；如果没有这行代码，重复学习不可追踪。
                return {"remembered": True, "decision": "updated_existing_hint", "hint": existing, "hint_count": len(saved["hints"]), "marker": PHASE73_APP_MEMORY_MARKER, "actions_expanded": PHASE73_ACTIONS_EXPANDED}  # 新增代码+Phase73AppMemory: 返回更新结果；如果没有这行代码，调用方不知道是否写入成功。
            state["hints"].append(hint)  # 新增代码+Phase73AppMemory: 添加新提示；如果没有这行代码，remember 不会产生记忆。
            saved = self._write_state(state)  # 新增代码+Phase73AppMemory: 原子写回状态；如果没有这行代码，下一次 list 读不到新提示。
            self._audit("remember_added", {"app": safe_app, "hint_type": safe_type, "hint_id": hint["hint_id"], "redacted": False, "marker": PHASE73_APP_MEMORY_MARKER, "actions_expanded": PHASE73_ACTIONS_EXPANDED})  # 新增代码+Phase73AppMemory: 记录写入审计；如果没有这行代码，成功学习不可回放。
            return {"remembered": True, "decision": "remembered", "hint": hint, "hint_count": len(saved["hints"]), "marker": PHASE73_APP_MEMORY_MARKER, "actions_expanded": PHASE73_ACTIONS_EXPANDED}  # 新增代码+Phase73AppMemory: 返回写入成功摘要；如果没有这行代码，终端和测试拿不到结果。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore.remember_app_hint 到此结束；如果没有这个边界说明，初学者不容易看出记忆写入范围。

    def list_app_hints(self, app: Any) -> dict[str, Any]:  # 新增代码+Phase73AppMemory: 函数段开始，列出某个 app 的有效非敏感提示；如果没有这段函数，规划器无法复用学习经验。
        safe_app = _phase73_app_key(app)  # 新增代码+Phase73AppMemory: 清理 app 名；如果没有这行代码，查询大小写和特殊字符会漂移。
        state = self._read_state()  # 新增代码+Phase73AppMemory: 读取当前状态；如果没有这行代码，查询没有事实来源。
        hints = [hint for hint in state["hints"] if hint.get("app") == safe_app and not hint.get("revoked", False)]  # 新增代码+Phase73AppMemory: 只返回目标 app 的 active 提示；如果没有这行代码，撤销或其他 app 提示会混入。
        hints.sort(key=lambda item: (-float(item.get("confidence", 0.0)), str(item.get("hint_type", "")), str(item.get("hint_value", ""))))  # 新增代码+Phase73AppMemory: 按置信度和类型稳定排序；如果没有这行代码，规划器每次看到顺序可能不同。
        return {"app": safe_app, "hints": hints, "hint_count": len(hints), "marker": PHASE73_APP_MEMORY_MARKER, "model": PHASE73_APP_MEMORY_MODEL, "actions_expanded": PHASE73_ACTIONS_EXPANDED}  # 新增代码+Phase73AppMemory: 返回机器可读提示列表；如果没有这行代码，调用方无法知道数量和阶段边界。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore.list_app_hints 到此结束；如果没有这个边界说明，初学者不容易看出查询范围。

    def revoke_app_memory(self, app: Any, reason: str = "user revoke") -> dict[str, Any]:  # 新增代码+Phase73AppMemory: 函数段开始，撤销某个 app 的有效记忆；如果没有这段函数，用户无法清理学习痕迹。
        safe_app = _phase73_app_key(app)  # 新增代码+Phase73AppMemory: 清理 app 名；如果没有这行代码，撤销目标可能匹配不到。
        safe_reason = _phase73_safe_text(reason, 180)  # 新增代码+Phase73AppMemory: 清理撤销原因；如果没有这行代码，审计文本可能污染 JSONL。
        revoked_count = 0  # 新增代码+Phase73AppMemory: 初始化撤销计数；如果没有这行代码，返回数量没有来源。
        now = _phase73_timestamp()  # 新增代码+Phase73AppMemory: 捕获撤销时间；如果没有这行代码，撤销记录无法排序。
        with FileLock(self.mutex_path, timeout_seconds=self.lock_timeout_seconds):  # 新增代码+Phase73AppMemory: 用互斥锁保护撤销；如果没有这行代码，撤销和写入可能交错。
            state = self._read_state()  # 新增代码+Phase73AppMemory: 读取当前状态；如果没有这行代码，撤销不知道哪些提示存在。
            for hint in state["hints"]:  # 新增代码+Phase73AppMemory: 遍历所有提示；如果没有这行代码，无法按 app 标记撤销。
                if hint.get("app") == safe_app and not hint.get("revoked", False):  # 新增代码+Phase73AppMemory: 只撤销目标 app 的 active 提示；如果没有这行代码，可能误伤其他 app 或重复计数。
                    hint["revoked"] = True  # 新增代码+Phase73AppMemory: 标记提示已撤销；如果没有这行代码，list 仍会返回旧提示。
                    hint["revoked_at"] = now  # 新增代码+Phase73AppMemory: 记录撤销时间；如果没有这行代码，用户无法知道何时撤销。
                    hint["revoked_reason"] = safe_reason  # 新增代码+Phase73AppMemory: 记录撤销原因；如果没有这行代码，审计无法说明为什么撤销。
                    revoked_count += 1  # 新增代码+Phase73AppMemory: 增加撤销计数；如果没有这行代码，返回数量不准确。
            saved = self._write_state(state)  # 新增代码+Phase73AppMemory: 写回撤销状态；如果没有这行代码，撤销不会落盘。
            self._audit("app_memory_revoked", {"app": safe_app, "revoked_count": revoked_count, "reason": safe_reason, "marker": PHASE73_APP_MEMORY_MARKER, "actions_expanded": PHASE73_ACTIONS_EXPANDED})  # 新增代码+Phase73AppMemory: 记录撤销审计；如果没有这行代码，用户清理操作不可回放。
            return {"revoked": bool(revoked_count), "revoked_count": revoked_count, "app": safe_app, "remaining_active_count": len([hint for hint in saved["hints"] if hint.get("app") == safe_app and not hint.get("revoked", False)]), "marker": PHASE73_APP_MEMORY_MARKER, "actions_expanded": PHASE73_ACTIONS_EXPANDED}  # 新增代码+Phase73AppMemory: 返回撤销摘要；如果没有这行代码，调用方不知道撤销是否生效。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore.revoke_app_memory 到此结束；如果没有这个边界说明，初学者不容易看出撤销范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase73AppMemory: 函数段开始，返回 app memory 状态摘要；如果没有这段函数，测试和状态 UI 无法查看记忆数量。
        state = self._read_state()  # 新增代码+Phase73AppMemory: 读取规范状态；如果没有这行代码，状态没有事实来源。
        active_hints = [hint for hint in state["hints"] if not hint.get("revoked", False)]  # 新增代码+Phase73AppMemory: 计算有效提示；如果没有这行代码，状态无法区分 active 和 revoked。
        revoked_hints = [hint for hint in state["hints"] if hint.get("revoked", False)]  # 新增代码+Phase73AppMemory: 计算撤销提示；如果没有这行代码，用户看不到撤销数量。
        apps = sorted({str(hint.get("app", "")) for hint in active_hints if hint.get("app")})  # 新增代码+Phase73AppMemory: 统计有 active 提示的 app；如果没有这行代码，状态无法显示学习覆盖范围。
        return {"enabled": True, "marker": PHASE73_APP_MEMORY_MARKER, "model": PHASE73_APP_MEMORY_MODEL, "state_path": str(self.state_path), "audit_path": str(self.audit_path), "active_hint_count": len(active_hints), "revoked_hint_count": len(revoked_hints), "app_count": len(apps), "apps": apps, "hints": active_hints, "actions_expanded": PHASE73_ACTIONS_EXPANDED}  # 新增代码+Phase73AppMemory: 返回机器可读状态；如果没有这行代码，状态 UI 和测试无法读取 app memory。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def terminal_status_lines(self) -> list[str]:  # 新增代码+Phase73AppMemory: 函数段开始，生成终端可读 app memory 面板；如果没有这段函数，小白用户只能读 JSON。
        status = self.status()  # 新增代码+Phase73AppMemory: 读取机器状态；如果没有这行代码，终端文本没有事实来源。
        return ["Computer App Memory", f"- marker={PHASE73_APP_MEMORY_MARKER}", f"- memory_model={PHASE73_APP_MEMORY_MODEL}", f"- active_hint_count={status.get('active_hint_count', 0)}", f"- revoked_hint_count={status.get('revoked_hint_count', 0)}", f"- app_count={status.get('app_count', 0)}", f"- apps={','.join(list(status.get('apps', []))[:8])}", f"- state_path={status.get('state_path', '')}", f"- audit_path={status.get('audit_path', '')}", f"- actions_expanded={_phase73_bool_token(PHASE73_ACTIONS_EXPANDED)}"]  # 新增代码+Phase73AppMemory: 返回完整终端面板行；如果没有这行代码，用户看不到 memory 数量和边界。
    # 新增代码+Phase73AppMemory: 函数段结束，WindowsComputerUseAppMemoryStore.terminal_status_lines 到此结束；如果没有这个边界说明，初学者不容易看出终端状态范围。
# 新增代码+Phase73AppMemory: 类段结束，WindowsComputerUseAppMemoryStore 到此结束；如果没有这个边界说明，初学者不容易看出 store 类范围。


def run_phase73_app_memory_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase73AppMemory: 函数段开始，运行 Phase73 app memory 合同自检；如果没有这段函数，CLI 和真实终端没有统一验收入口。
    store = WindowsComputerUseAppMemoryStore(base_dir=Path(base_dir) if base_dir is not None else None)  # 新增代码+Phase73AppMemory: 创建指定或默认 store；如果没有这行代码，自检没有 app memory 事实源。
    safe_results = [store.remember_app_hint("notepad.exe", "window_class", "Notepad", source="phase73-contract", confidence=0.9), store.remember_app_hint("notepad.exe", "role_hint", "main editor role is Edit", source="phase73-contract", confidence=0.8), store.remember_app_hint("notepad.exe", "safe_control_name", "File name", source="phase73-contract", confidence=0.85), store.remember_app_hint("notepad.exe", "menu_label", "File", source="phase73-contract", confidence=0.95), store.remember_app_hint("notepad.exe", "last_successful_strategy", "Open File menu, choose Save As, then use standard dialog controls.", source="phase73-contract", confidence=0.7)]  # 新增代码+Phase73AppMemory: 写入五类安全提示；如果没有这行代码，app_memory 和非敏感正例没有证据。
    before_revoke = store.list_app_hints("notepad.exe")  # 新增代码+Phase73AppMemory: 读取撤销前提示；如果没有这行代码，合同无法证明已记住。
    secret = store.remember_app_hint("chrome.exe", "safe_control_name", "password hunter2 api token sk-test-secret credit card 4111111111111111", source="phase73-contract", confidence=1.0)  # 新增代码+Phase73AppMemory: 尝试写入秘密内容；如果没有这行代码，non_secret_memory 没有反例。
    script_type = store.remember_app_hint("notepad.exe", "script", "click 10 10; type private text", source="phase73-contract", confidence=0.5)  # 新增代码+Phase73AppMemory: 尝试写入脚本类型；如果没有这行代码，memory_assists_not_scripts 没有类型反例。
    command_value = store.remember_app_hint("notepad.exe", "last_successful_strategy", "powershell.exe -NoProfile -Command Remove-Item C:\\important -Recurse", source="phase73-contract", confidence=0.5)  # 新增代码+Phase73AppMemory: 尝试写入终端命令策略；如果没有这行代码，命令拒绝没有反例。
    safe_assist = store.remember_app_hint("notepad.exe", "last_successful_strategy", "Use visible menu labels and dialog roles, not replayed scripts.", source="phase73-contract", confidence=0.65)  # 新增代码+Phase73AppMemory: 写入安全辅助策略；如果没有这行代码，非脚本辅助正例不足。
    state_text = store.state_path.read_text(encoding="utf-8") if store.state_path.exists() else ""  # 新增代码+Phase73AppMemory: 读取状态文本用于泄露检查；如果没有这行代码，秘密是否落盘无法验证。
    audit_text = store.audit_path.read_text(encoding="utf-8") if store.audit_path.exists() else ""  # 新增代码+Phase73AppMemory: 读取审计文本用于泄露检查；如果没有这行代码，审计泄露无法验证。
    persisted_text = state_text + audit_text  # 新增代码+Phase73AppMemory: 合并持久化文本；如果没有这行代码，泄露检查要重复扫描。
    revoke = store.revoke_app_memory("notepad.exe", reason="phase73-contract-revoke")  # 新增代码+Phase73AppMemory: 撤销 notepad 记忆；如果没有这行代码，memory_can_be_revoked 没有证据。
    after_revoke = store.list_app_hints("notepad.exe")  # 新增代码+Phase73AppMemory: 读取撤销后的提示；如果没有这行代码，撤销效果无法验证。
    app_memory = bool(all(result.get("remembered") for result in safe_results) and len(before_revoke.get("hints", [])) >= 5)  # 新增代码+Phase73AppMemory: 汇总 app memory 正例；如果没有这行代码，报告无法表达安全提示已记住。
    non_secret_memory = bool(not secret.get("remembered") and secret.get("decision") == "secret_or_private_content_rejected" and "hunter2" not in persisted_text and "sk-test-secret" not in persisted_text and "4111111111111111" not in persisted_text)  # 新增代码+Phase73AppMemory: 汇总秘密拒绝和不落盘；如果没有这行代码，隐私门禁无法进入 token。
    memory_assists_not_scripts = bool(not script_type.get("remembered") and script_type.get("decision") == "unsupported_hint_type" and not command_value.get("remembered") and command_value.get("decision") == "terminal_command_rejected" and safe_assist.get("remembered") and "Remove-Item" not in persisted_text and "click 10 10" not in persisted_text)  # 新增代码+Phase73AppMemory: 汇总非脚本边界；如果没有这行代码，脚本/命令拒绝无法进入 token。
    memory_can_be_revoked = bool(revoke.get("revoked") and revoke.get("revoked_count", 0) >= 1 and after_revoke.get("hints") == [])  # 新增代码+Phase73AppMemory: 汇总撤销结果；如果没有这行代码，用户清理能力无法进入 token。
    passed = bool(app_memory and non_secret_memory and memory_assists_not_scripts and memory_can_be_revoked and not PHASE73_ACTIONS_EXPANDED)  # 新增代码+Phase73AppMemory: 汇总合同通过条件；如果没有这行代码，main 无法用退出码表达失败。
    return {"marker": PHASE73_APP_MEMORY_MARKER, "ok_token": PHASE73_APP_MEMORY_OK_TOKEN, "app_memory": app_memory, "non_secret_memory": non_secret_memory, "memory_assists_not_scripts": memory_assists_not_scripts, "memory_can_be_revoked": memory_can_be_revoked, "actions_expanded": PHASE73_ACTIONS_EXPANDED, "passed": passed, "state_dir": str(store.base_dir)}  # 新增代码+Phase73AppMemory: 返回完整合同报告；如果没有这行代码，测试和真实终端拿不到统一结果。
# 新增代码+Phase73AppMemory: 函数段结束，run_phase73_app_memory_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase73_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase73AppMemory: 函数段开始，把合同报告转成稳定 CLI token 行；如果没有这段函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE73_APP_MEMORY_MARKER} {PHASE73_APP_MEMORY_OK_TOKEN} app_memory={_phase73_bool_token(report.get('app_memory'))} non_secret_memory={_phase73_bool_token(report.get('non_secret_memory'))} memory_assists_not_scripts={_phase73_bool_token(report.get('memory_assists_not_scripts'))} memory_can_be_revoked={_phase73_bool_token(report.get('memory_can_be_revoked'))} actions_expanded={_phase73_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase73AppMemory: 返回固定顺序 token；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase73AppMemory: 函数段结束，phase73_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase73AppMemory: 函数段开始，提供命令行入口；如果没有这段函数，真实终端无法直接运行 Phase73 自检。
    _ = argv  # 新增代码+Phase73AppMemory: 保留 argv 供未来扩展；如果没有这行代码，参数存在但用途不清楚。
    report = run_phase73_app_memory_contract()  # 新增代码+Phase73AppMemory: 运行合同自检；如果没有这行代码，CLI 不会生成 app memory 证据。
    print(phase73_cli_line(report))  # 新增代码+Phase73AppMemory: 打印稳定 token 行；如果没有这行代码，debug log 无法匹配 Phase73 成功。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase73AppMemory: 打印结构化报告；如果没有这行代码，失败时不易复盘。
    print(PHASE73_APP_MEMORY_MARKER)  # 新增代码+Phase73AppMemory: 单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase73AppMemory: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase73AppMemory: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_APP_MEMORY_ROOT", "PHASE73_ACTIONS_EXPANDED", "PHASE73_APP_MEMORY_MARKER", "PHASE73_APP_MEMORY_MODEL", "PHASE73_APP_MEMORY_OK_TOKEN", "WindowsComputerUseAppMemoryStore", "main", "phase73_cli_line", "run_phase73_app_memory_contract"]  # 新增代码+Phase73AppMemory: 限定公开导出名称；如果没有这行代码，包导入容易暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase73AppMemory: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase73AppMemory: 用 main 返回码退出；如果没有这行代码，命令行状态不明确。
