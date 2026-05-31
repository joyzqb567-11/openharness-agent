"""会话保存、恢复和最小 compact 辅助。"""  # 新增代码+Stage15G: 把 session resume/compact 边界独立成模块；若没有这个文件，长任务恢复逻辑会继续散落在主循环和 transcript 里。

from __future__ import annotations  # 新增代码+Stage15G: 延迟解析类型注解；若没有这行代码，跨模块引用更容易受定义顺序影响。

import copy  # 新增代码+Stage15G: 保存和 compact 消息时需要深拷贝；若没有这行代码，调用方原始 messages 可能被污染。
import json  # 新增代码+Stage15G: summary.json 需要标准 JSON 读写；若没有这行代码，session 摘要无法稳定落盘。
from dataclasses import dataclass, field  # 新增代码+Stage15G: 快速定义 session 摘要对象并支持列表默认值；若没有这行代码，需要手写重复初始化逻辑。
from pathlib import Path  # 新增代码+Stage15G: 使用 Path 管理 session 目录；若没有这行代码，路径拼接会更脆弱。
from typing import Any  # 新增代码+Stage15G: messages 和工具结果是 JSON 风格数据；若没有这行代码，类型边界不清楚。


@dataclass  # 新增代码+Stage15G: 自动生成 SessionRecord 初始化方法；若没有这行代码，保存 summary 时要手写大量样板代码。
class SessionRecord:  # 新增代码+Stage15G: 表示一次可恢复 agent 会话摘要；若没有这个类，resume 只能依赖松散 dict。
    session_id: str  # 新增代码+Stage15G: 保存会话编号；若没有这行代码，summary 无法和 events.jsonl 目录对应。
    run_id: str = ""  # 新增代码+Stage15G: 保存运行编号；若没有这行代码，summary 无法和单次 run 事件串联。
    user_input: str = ""  # 新增代码+Stage15G: 保存用户原始输入；若没有这行代码，恢复时不知道任务从哪里开始。
    messages: list[dict[str, Any]] = field(default_factory=list)  # 新增代码+Stage15G: 保存可恢复消息摘要；若没有这行代码，resume 无法重建上下文。
    tool_calls: list[dict[str, Any]] = field(default_factory=list)  # 新增代码+Stage15G: 保存工具调用摘要；若没有这行代码，审计无法看到模型做过哪些动作。
    tool_results: list[dict[str, Any]] = field(default_factory=list)  # 新增代码+Stage15G: 保存工具结果摘要；若没有这行代码，恢复时缺少外部观察结果。
    permission_decisions: list[dict[str, Any]] = field(default_factory=list)  # 新增代码+Stage15G: 保存权限决策摘要；若没有这行代码，安全审计无法复盘授权过程。
    final_answer: str = ""  # 新增代码+Stage15G: 保存最终回答；若没有这行代码，恢复列表无法展示会话结果。
    artifacts: list[str] = field(default_factory=list)  # 新增代码+Stage15G: 保存会话关联产物路径；若没有这行代码，长工具结果落盘后难以追踪。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+Stage15G: 把 session 记录转成可写 JSON 的字典；若没有这行代码，保存 summary 会重复拼字段。
        return {  # 新增代码+Stage15G: 返回新的 dict 避免外部修改对象内部列表；若没有这行代码，summary 写入可能污染原对象。
            "session_id": self.session_id,  # 新增代码+Stage15G: 写入会话编号；若没有这行代码，读取 summary 后无法定位目录。
            "run_id": self.run_id,  # 新增代码+Stage15G: 写入运行编号；若没有这行代码，summary 和 transcript 难以关联。
            "user_input": self.user_input,  # 新增代码+Stage15G: 写入用户输入；若没有这行代码，恢复时缺少任务起点。
            "messages": copy.deepcopy(self.messages),  # 新增代码+Stage15G: 深拷贝消息列表；若没有这行代码，写入过程可能共享可变对象。
            "tool_calls": copy.deepcopy(self.tool_calls),  # 新增代码+Stage15G: 深拷贝工具调用；若没有这行代码，后续修改会污染已保存摘要。
            "tool_results": copy.deepcopy(self.tool_results),  # 新增代码+Stage15G: 深拷贝工具结果；若没有这行代码，审计摘要可能被调用方改掉。
            "permission_decisions": copy.deepcopy(self.permission_decisions),  # 新增代码+Stage15G: 深拷贝权限决策；若没有这行代码，权限审计数据可能被污染。
            "final_answer": self.final_answer,  # 新增代码+Stage15G: 写入最终回答；若没有这行代码，列表页无法展示结果。
            "artifacts": list(self.artifacts),  # 新增代码+Stage15G: 写入产物列表副本；若没有这行代码，外部修改 artifacts 会影响 summary。
        }  # 新增代码+Stage15G: 字典结束；若没有这行代码，Python 语法不完整。

    @classmethod  # 新增代码+Stage15G: 提供从 dict 恢复 SessionRecord 的类方法；若没有这行代码，load_summary 需要手写字段兜底。
    def from_dict(cls, payload: dict[str, Any]) -> "SessionRecord":  # 新增代码+Stage15G: 从 JSON dict 构造 session 记录；若没有这行代码，恢复接口无法返回稳定对象。
        return cls(  # 新增代码+Stage15G: 构造 SessionRecord；若没有这行代码，调用方只能拿普通 dict。
            session_id=str(payload.get("session_id", "")),  # 新增代码+Stage15G: 读取会话编号并兜底空字符串；若没有这行代码，坏 summary 会直接报错。
            run_id=str(payload.get("run_id", "")),  # 新增代码+Stage15G: 读取运行编号；若没有这行代码，恢复后 run_id 会丢失。
            user_input=str(payload.get("user_input", "")),  # 新增代码+Stage15G: 读取用户输入；若没有这行代码，恢复上下文缺任务起点。
            messages=copy.deepcopy(payload.get("messages", [])) if isinstance(payload.get("messages", []), list) else [],  # 新增代码+Stage15G: 安全读取消息列表；若没有这行代码，坏 summary 会污染 resume。
            tool_calls=copy.deepcopy(payload.get("tool_calls", [])) if isinstance(payload.get("tool_calls", []), list) else [],  # 新增代码+Stage15G: 安全读取工具调用；若没有这行代码，非列表字段会导致后续遍历失败。
            tool_results=copy.deepcopy(payload.get("tool_results", [])) if isinstance(payload.get("tool_results", []), list) else [],  # 新增代码+Stage15G: 安全读取工具结果；若没有这行代码，恢复时可能拿到错误类型。
            permission_decisions=copy.deepcopy(payload.get("permission_decisions", [])) if isinstance(payload.get("permission_decisions", []), list) else [],  # 新增代码+Stage15G: 安全读取权限决策；若没有这行代码，权限审计可能崩溃。
            final_answer=str(payload.get("final_answer", "")),  # 新增代码+Stage15G: 读取最终回答；若没有这行代码，会话列表无法展示完成结果。
            artifacts=[str(item) for item in payload.get("artifacts", [])] if isinstance(payload.get("artifacts", []), list) else [],  # 新增代码+Stage15G: 安全读取产物路径；若没有这行代码，artifact 引用可能是非字符串。
        )  # 新增代码+Stage15G: SessionRecord 构造结束；若没有这行代码，Python 语法不完整。


class SessionStore:  # 新增代码+Stage15G: 管理 memory/sessions 下的 summary 文件；若没有这个类，session 保存和恢复路径会散在各处。
    def __init__(self, base_dir: Path) -> None:  # 新增代码+Stage15G: 初始化 session 根目录；若没有这行代码，store 不知道读写哪里。
        self.base_dir = Path(base_dir)  # 新增代码+Stage15G: 规范化根目录路径；若没有这行代码，调用方传字符串时路径操作不稳定。

    def session_dir(self, session_id: str) -> Path:  # 新增代码+Stage15G: 计算指定 session 目录；若没有这行代码，各方法会重复拼路径。
        return self.base_dir / session_id  # 新增代码+Stage15G: 返回 session 目录路径；若没有这行代码，summary 和 events 无法放在同一目录。

    def summary_path(self, session_id: str) -> Path:  # 新增代码+Stage15G: 计算指定 session 的 summary.json 路径；若没有这行代码，保存和读取可能路径不一致。
        return self.session_dir(session_id) / "summary.json"  # 新增代码+Stage15G: 返回固定 summary 文件路径；若没有这行代码，resume 找不到摘要文件。

    def events_path(self, session_id: str) -> Path:  # 新增代码+Stage15G: 计算指定 session 的 events.jsonl 路径；若没有这行代码，store 无法关联原始 transcript。
        return self.session_dir(session_id) / "events.jsonl"  # 新增代码+Stage15G: 返回固定事件文件路径；若没有这行代码，恢复时无法找到原始证据。

    def save_summary(self, record: SessionRecord) -> Path:  # 新增代码+Stage15G: 保存 session 摘要到 summary.json；若没有这行代码，会话恢复信息无法落盘。
        path = self.summary_path(record.session_id)  # 新增代码+Stage15G: 计算摘要路径；若没有这行代码，保存位置不稳定。
        path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+Stage15G: 确保 session 目录存在；若没有这行代码，首次保存 summary 会失败。
        path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # 新增代码+Stage15G: 写入 UTF-8 JSON 摘要；若没有这行代码，summary 不会真正保存。
        return path  # 新增代码+Stage15G: 返回摘要路径；若没有这行代码，调用方无法记录保存位置。

    def load_summary(self, session_id: str) -> SessionRecord:  # 新增代码+Stage15G: 从 summary.json 读取 session 摘要；若没有这行代码，resume 无法加载会话状态。
        payload = json.loads(self.summary_path(session_id).read_text(encoding="utf-8"))  # 新增代码+Stage15G: 读取并解析 JSON 摘要；若没有这行代码，无法恢复 SessionRecord。
        return SessionRecord.from_dict(payload if isinstance(payload, dict) else {})  # 新增代码+Stage15G: 返回稳定 SessionRecord；若没有这行代码，调用方会拿到松散 JSON。

    def list_recent_sessions(self, limit: int = 20) -> list[str]:  # 新增代码+Stage15G: 列出最近有 summary 的 session；若没有这行代码，用户无法发现可恢复会话。
        if not self.base_dir.exists():  # 新增代码+Stage15G: 根目录不存在时返回空列表；若没有这行代码，首次运行前列出 session 会报错。
            return []  # 新增代码+Stage15G: 返回空 session 列表；若没有这行代码，调用方需要自己捕获文件错误。
        session_dirs = [path for path in self.base_dir.iterdir() if path.is_dir() and (path / "summary.json").exists()]  # 新增代码+Stage15G: 只收集有 summary 的目录；若没有这行代码，半成品目录也会出现在恢复列表。
        session_dirs.sort(key=lambda path: (path / "summary.json").stat().st_mtime, reverse=True)  # 新增代码+Stage15G: 按 summary 修改时间倒序排列；若没有这行代码，最近会话可能排在后面。
        return [path.name for path in session_dirs[: max(1, limit)]]  # 新增代码+Stage15G: 返回最多 limit 个 session id；若没有这行代码，长任务会话太多会刷屏。


def compact_messages_for_session(messages: list[dict[str, Any]], session_id: str = "", max_messages: int = 20) -> list[dict[str, Any]]:  # 新增代码+Stage15G: 生成最小 compact 消息列表；若没有这行代码，长会话只能无限增长上下文。
    safe_limit = max(2, int(max_messages))  # 新增代码+Stage15G: 至少保留摘要加一条尾部消息；若没有这行代码，max_messages=0 会产生不可用上下文。
    if len(messages) <= safe_limit:  # 新增代码+Stage15G: 未超过阈值时不压缩；若没有这行代码，短对话也会被无意义摘要化。
        return copy.deepcopy(messages)  # 新增代码+Stage15G: 返回深拷贝保护调用方原始消息；若没有这行代码，外部修改结果会污染原列表。
    tail_count = safe_limit - 1  # 新增代码+Stage15G: 摘要占一条，其余预算留给最近消息；若没有这行代码，压缩后长度无法控制。
    removed_count = len(messages) - tail_count  # 新增代码+Stage15G: 计算被摘要覆盖的旧消息数；若没有这行代码，摘要无法告诉模型压缩范围。
    summary_text = f"Compact Summary: session_id={session_id or 'unknown'}; 压缩了 {removed_count} 条较早消息；原始证据仍保留在 session transcript，不要把摘要当作唯一证据。"  # 新增代码+Stage15G: 构造可读压缩摘要；若没有这行代码，模型不知道旧上下文去哪了。
    summary_message = {"role": "system", "content": summary_text}  # 新增代码+Stage15G: 用 system 消息承载 compact 摘要；若没有这行代码，模型可能把摘要当用户新请求。
    tail_messages = copy.deepcopy(messages[-tail_count:])  # 新增代码+Stage15G: 深拷贝最近消息作为可继续上下文；若没有这行代码，恢复后会丢掉最新对话。
    return [summary_message] + tail_messages  # 新增代码+Stage15G: 返回摘要加尾部消息；若没有这行代码，调用方拿不到压缩结果。
