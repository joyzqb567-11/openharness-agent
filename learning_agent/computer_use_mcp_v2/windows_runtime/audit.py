"""Computer Use 动作审计落盘仓库。"""  # 新增代码+Phase31ComputerUseAudit: 说明本文件负责保存桌面动作审计和证据链；如果没有这个文件，动作完成后只能看内存结果，无法长期复盘。
from __future__ import annotations  # 新增代码+Phase31ComputerUseAudit: 启用延迟类型解析；如果没有这行代码，旧运行路径下前向类型标注更容易出错。
import time  # 新增代码+Phase31ComputerUseAudit: 导入时间模块生成审计时间戳；如果没有这行代码，落盘事件缺少可排序的发生时间。
from pathlib import Path  # 新增代码+Phase31ComputerUseAudit: 导入 Path 统一管理 Windows 路径；如果没有这行代码，审计目录拼接会更容易写错。
from typing import Any  # 新增代码+Phase31ComputerUseAudit: 导入通用 JSON 类型标注；如果没有这行代码，审计 payload 边界不清楚。

try:  # 新增代码+Phase31ComputerUseAudit: 优先按包路径导入运行时文件工具；如果没有这行代码，审计仓库无法复用项目安全写入能力。
    from learning_agent.runtime.files import append_jsonl, atomic_write_json, read_jsonl  # 新增代码+Phase31ComputerUseAudit: 导入 JSONL 追加、原子 JSON 写入和容错读取；如果没有这行代码，审计落盘会重复实现且更容易半写。
except ModuleNotFoundError as error:  # 新增代码+Phase31ComputerUseAudit: 捕获 bat 脚本模式下包路径不可用的情况；如果没有这行代码，真实终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase31ComputerUseAudit: 只允许目标包路径缺失时 fallback；如果没有这行代码，runtime.files 内部真实 bug 会被误吞。
        raise  # 新增代码+Phase31ComputerUseAudit: 重新抛出非目标导入错误；如果没有这行代码，排查真实导入错误会很困难。
    from runtime.files import append_jsonl, atomic_write_json, read_jsonl  # 新增代码+Phase31ComputerUseAudit: 脚本模式下从本地 runtime 导入文件工具；如果没有这行代码，start_oauth_agent.bat 无法加载审计仓库。

DEFAULT_COMPUTER_USE_AUDIT_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "audit"  # 新增代码+Phase31ComputerUseAudit: 定义默认审计根目录；如果没有这行代码，生产运行不知道把审计文件保存到哪里。
SENSITIVE_AUDIT_KEYS = {"text", "password", "secret", "token", "authorization", "credential"}  # 新增代码+Phase31ComputerUseAudit: 定义需要从审计中移除的敏感字段名；如果没有这行代码，原始输入可能被写入磁盘。

# 新增代码+Phase31ComputerUseAudit: 函数段开始，phase31_audit_timestamp 用于生成 UTC 审计时间；如果没有这段函数，各处会重复手写时间格式，作者意图是让审计事件容易排序。
def phase31_audit_timestamp() -> str:  # 新增代码+Phase31ComputerUseAudit: 定义审计时间戳 helper；如果没有这行代码，调用方需要重复写 time.strftime。
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # 新增代码+Phase31ComputerUseAudit: 返回 ISO 风格 UTC 时间；如果没有这行代码，审计事件缺少统一时间格式。
# 新增代码+Phase31ComputerUseAudit: 函数段结束，phase31_audit_timestamp 到此结束；如果没有这个边界说明，初学者不容易看出时间 helper 范围。

# 新增代码+Phase31ComputerUseAudit: 函数段开始，sanitize_audit_payload 用于递归脱敏审计内容；如果没有这段函数，文本输入或 token 可能进入磁盘，作者意图是保留结构但移除明文。
def sanitize_audit_payload(payload: Any) -> Any:  # 新增代码+Phase31ComputerUseAudit: 定义递归审计脱敏函数；如果没有这行代码，审计仓库只能直接相信调用方。
    if isinstance(payload, dict):  # 新增代码+Phase31ComputerUseAudit: 处理字典对象；如果没有这行代码，JSON 对象内部敏感字段不会被检查。
        sanitized: dict[str, Any] = {}  # 新增代码+Phase31ComputerUseAudit: 准备保存脱敏后的字典；如果没有这行代码，递归结果没有容器。
        for key, value in payload.items():  # 新增代码+Phase31ComputerUseAudit: 遍历每个字段；如果没有这行代码，字段级脱敏无法执行。
            key_text = str(key)  # 新增代码+Phase31ComputerUseAudit: 把字段名转成字符串便于比较；如果没有这行代码，非字符串 key 可能导致 lower 失败。
            if key_text.lower() in SENSITIVE_AUDIT_KEYS:  # 新增代码+Phase31ComputerUseAudit: 检查字段名是否敏感；如果没有这行代码，text/password/token 会被保留下来。
                sanitized[key_text] = {"redacted": True, "reason": "sensitive_audit_key"}  # 新增代码+Phase31ComputerUseAudit: 用脱敏占位替代敏感值；如果没有这行代码，审计读者不知道该字段为什么缺失。
                continue  # 新增代码+Phase31ComputerUseAudit: 跳过敏感字段的原值递归；如果没有这行代码，下面仍可能保存明文。
            sanitized[key_text] = sanitize_audit_payload(value)  # 新增代码+Phase31ComputerUseAudit: 递归处理普通字段；如果没有这行代码，嵌套结构里的敏感字段会漏掉。
        return sanitized  # 新增代码+Phase31ComputerUseAudit: 返回脱敏后的字典；如果没有这行代码，字典处理不会产生结果。
    if isinstance(payload, list):  # 新增代码+Phase31ComputerUseAudit: 处理列表对象；如果没有这行代码，列表里的字典无法递归脱敏。
        return [sanitize_audit_payload(item) for item in payload]  # 新增代码+Phase31ComputerUseAudit: 递归处理列表元素；如果没有这行代码，列表内敏感字段会漏掉。
    if isinstance(payload, tuple):  # 新增代码+Phase31ComputerUseAudit: 处理元组对象；如果没有这行代码，元组里的敏感字段无法递归脱敏。
        return [sanitize_audit_payload(item) for item in payload]  # 新增代码+Phase31ComputerUseAudit: 把元组安全转换为 JSON 列表；如果没有这行代码，JSON 写入可能遇到不可序列化对象。
    if isinstance(payload, (str, int, float, bool)) or payload is None:  # 新增代码+Phase31ComputerUseAudit: 允许 JSON 原子值直接通过；如果没有这行代码，简单字段会被错误替换。
        return payload  # 新增代码+Phase31ComputerUseAudit: 返回安全原子值；如果没有这行代码，普通审计信息会丢失。
    return str(payload)[:500]  # 新增代码+Phase31ComputerUseAudit: 其他对象转成短字符串兜底；如果没有这行代码，写 JSON 时可能因不可序列化对象失败。
# 新增代码+Phase31ComputerUseAudit: 函数段结束，sanitize_audit_payload 到此结束；如果没有这个边界说明，读者不容易看出脱敏逻辑范围。

class ComputerUseAuditStore:  # 新增代码+Phase31ComputerUseAudit: 定义 Computer Use 审计仓库；如果没有这个类，控制器无法把动作事件和证据链统一落盘。
    def __init__(self, base_dir: str | Path | None = None) -> None:  # 新增代码+Phase31ComputerUseAudit: 函数段开始，初始化审计路径；如果没有这段函数，测试和生产无法指定独立审计目录。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_COMPUTER_USE_AUDIT_ROOT  # 新增代码+Phase31ComputerUseAudit: 保存审计根目录并允许测试注入临时目录；如果没有这行代码，测试会污染真实运行目录。
        self.events_path = self.base_dir / "events.jsonl"  # 新增代码+Phase31ComputerUseAudit: 定义审计事件 JSONL 路径；如果没有这行代码，事件没有统一文件位置。
        self.chains_dir = self.base_dir / "chains"  # 新增代码+Phase31ComputerUseAudit: 定义动作证据链目录；如果没有这行代码，before/after chain 会和事件混在一起难以查看。
    # 新增代码+Phase31ComputerUseAudit: 函数段结束，__init__ 到此结束；如果没有这个边界说明，读者不容易看出路径初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase31ComputerUseAudit: 函数段开始，返回审计仓库状态；如果没有这段函数，computer_status 无法展示审计落盘位置。
        return {"enabled": True, "base_dir": str(self.base_dir), "events_path": str(self.events_path), "chains_dir": str(self.chains_dir)}  # 新增代码+Phase31ComputerUseAudit: 返回审计路径摘要；如果没有这行代码，用户不知道证据链保存在哪里。
    # 新增代码+Phase31ComputerUseAudit: 函数段结束，status 到此结束；如果没有这个边界说明，读者不容易看出状态输出范围。

    def record_event(self, event: dict[str, Any], action_evidence: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase31ComputerUseAudit: 函数段开始，写入审计事件并可保存证据链；如果没有这段函数，动作事件不会持久化。
        audit_id = str(event.get("audit_id", ""))  # 新增代码+Phase31ComputerUseAudit: 读取审计 id；如果没有这行代码，事件和链路无法互相关联。
        sanitized_event = sanitize_audit_payload(dict(event))  # 新增代码+Phase31ComputerUseAudit: 对事件做递归脱敏；如果没有这行代码，磁盘可能保存原始敏感字段。
        sanitized_event["recorded_at"] = phase31_audit_timestamp()  # 新增代码+Phase31ComputerUseAudit: 追加落盘时间；如果没有这行代码，事件只知道控制器时间不知道写盘时间。
        chain_path = ""  # 新增代码+Phase31ComputerUseAudit: 初始化证据链路径为空；如果没有这行代码，无证据链事件会缺少稳定字段。
        if action_evidence is not None and audit_id:  # 新增代码+Phase31ComputerUseAudit: 只有成功传入动作证据且有 audit_id 时保存链路；如果没有这行代码，空链路也会生成无意义文件。
            chain_path = str(self.save_chain(audit_id, action_evidence))  # 新增代码+Phase31ComputerUseAudit: 保存证据链并取得路径；如果没有这行代码，before/after evidence 不会落盘。
            sanitized_event["chain_path"] = chain_path  # 新增代码+Phase31ComputerUseAudit: 把链路路径写回事件；如果没有这行代码，读事件时找不到链路文件。
        append_jsonl(self.events_path, sanitized_event)  # 新增代码+Phase31ComputerUseAudit: 追加写入 JSONL 审计事件；如果没有这行代码，事件只存在内存里。
        return {"events_path": str(self.events_path), "chain_path": chain_path, "event": sanitized_event}  # 新增代码+Phase31ComputerUseAudit: 返回写入结果；如果没有这行代码，调用方无法确认落盘位置。
    # 新增代码+Phase31ComputerUseAudit: 函数段结束，record_event 到此结束；如果没有这个边界说明，读者不容易看出事件保存流程范围。

    def save_chain(self, audit_id: str, action_evidence: dict[str, Any]) -> Path:  # 新增代码+Phase31ComputerUseAudit: 函数段开始，保存单个动作证据链；如果没有这段函数，before/after 证据无法独立打开查看。
        safe_audit_id = "".join(character if character.isalnum() or character in {"-", "_"} else "_" for character in str(audit_id))  # 新增代码+Phase31ComputerUseAudit: 清理 audit_id 用作文件名；如果没有这行代码，奇怪字符可能破坏 Windows 路径。
        chain_path = self.chains_dir / f"{safe_audit_id}.json"  # 新增代码+Phase31ComputerUseAudit: 生成证据链文件路径；如果没有这行代码，链路没有固定保存目标。
        payload = sanitize_audit_payload(dict(action_evidence))  # 新增代码+Phase31ComputerUseAudit: 对证据链递归脱敏；如果没有这行代码，链路文件也可能泄露原始文本。
        payload["audit_id"] = str(audit_id)  # 新增代码+Phase31ComputerUseAudit: 确保证据链顶层带 audit_id；如果没有这行代码，单独打开链路文件时无法知道来源事件。
        payload["recorded_at"] = phase31_audit_timestamp()  # 新增代码+Phase31ComputerUseAudit: 记录链路落盘时间；如果没有这行代码，证据文件缺少写入时间。
        atomic_write_json(chain_path, payload)  # 新增代码+Phase31ComputerUseAudit: 原子写入证据链 JSON；如果没有这行代码，崩溃可能留下半个 JSON。
        return chain_path  # 新增代码+Phase31ComputerUseAudit: 返回证据链路径；如果没有这行代码，调用方无法把路径写回事件。
    # 新增代码+Phase31ComputerUseAudit: 函数段结束，save_chain 到此结束；如果没有这个边界说明，读者不容易看出链路保存流程范围。

    def read_events(self) -> list[dict[str, Any]]:  # 新增代码+Phase31ComputerUseAudit: 函数段开始，读取审计事件；如果没有这段函数，测试和状态页无法复查落盘事件。
        return read_jsonl(self.events_path)  # 新增代码+Phase31ComputerUseAudit: 容错读取 JSONL 事件；如果没有这行代码，坏行可能拖垮审计查看。
    # 新增代码+Phase31ComputerUseAudit: 函数段结束，read_events 到此结束；如果没有这个边界说明，读者不容易看出事件读取范围。

    def read_chains(self) -> list[dict[str, Any]]:  # 新增代码+Phase31ComputerUseAudit: 函数段开始，读取所有证据链文件；如果没有这段函数，测试无法统一检查链路脱敏。
        if not self.chains_dir.exists():  # 新增代码+Phase31ComputerUseAudit: 检查链路目录是否存在；如果没有这行代码，首次读取会因目录缺失报错。
            return []  # 新增代码+Phase31ComputerUseAudit: 无链路目录时返回空列表；如果没有这行代码，调用方需要自己兜底。
        chains: list[dict[str, Any]] = []  # 新增代码+Phase31ComputerUseAudit: 准备累计链路对象；如果没有这行代码，读取结果没有容器。
        for chain_file in sorted(self.chains_dir.glob("*.json")):  # 新增代码+Phase31ComputerUseAudit: 按文件名读取链路 JSON；如果没有这行代码，无法遍历所有链路。
            try:  # 新增代码+Phase31ComputerUseAudit: 包住单个文件读取错误；如果没有这行代码，一个坏链路会拖垮全部读取。
                import json  # 新增代码+Phase31ComputerUseAudit: 延迟导入 JSON 用于解析链路文件；如果没有这行代码，read_chains 无法解析 JSON。
                parsed = json.loads(chain_file.read_text(encoding="utf-8"))  # 新增代码+Phase31ComputerUseAudit: 解析当前链路文件；如果没有这行代码，链路只能作为文本存在。
            except (OSError, ValueError):  # 新增代码+Phase31ComputerUseAudit: 捕获读取或解析失败；如果没有这行代码，坏文件会中断读取。
                continue  # 新增代码+Phase31ComputerUseAudit: 跳过坏链路继续读取其他文件；如果没有这行代码，审计查看缺少容错。
            if isinstance(parsed, dict):  # 新增代码+Phase31ComputerUseAudit: 只接受字典链路对象；如果没有这行代码，异常 JSON 类型会污染结果。
                chains.append(parsed)  # 新增代码+Phase31ComputerUseAudit: 保存当前链路对象；如果没有这行代码，读取结果始终为空。
        return chains  # 新增代码+Phase31ComputerUseAudit: 返回所有链路对象；如果没有这行代码，调用方拿不到结果。
    # 新增代码+Phase31ComputerUseAudit: 函数段结束，read_chains 到此结束；如果没有这个边界说明，读者不容易看出链路读取流程范围。
