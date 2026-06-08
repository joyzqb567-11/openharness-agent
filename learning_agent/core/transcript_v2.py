"""可回放 transcript v2，保存带 uuid 和父子关系的 agent 运行事件。"""  # 新增代码+TranscriptV2: 说明本模块负责更接近 ClaudeCode 的可恢复 transcript；若没有这行代码，维护者会把它和旧 events.jsonl 混淆。

from __future__ import annotations  # 新增代码+TranscriptV2: 延迟解析类型注解；若没有这行代码，类方法返回自身类型时更容易受定义顺序影响。

import copy  # 新增代码+TranscriptV2: 复制 payload 防止调用方后续修改污染已保存事件；若没有这行代码，审计记录可能被可变对象改掉。
import secrets  # 新增代码+TranscriptV2: 生成 transcript 条目 uuid 随机后缀；若没有这行代码，多事件可能出现 id 冲突。
from dataclasses import dataclass, field  # 新增代码+TranscriptV2: 用 dataclass 定义事件条目；若没有这行代码，字段管理会变成松散 dict。
from pathlib import Path  # 新增代码+TranscriptV2: 使用 Path 管理 session 目录；若没有这行代码，Windows 路径拼接会更脆弱。
from typing import Any  # 新增代码+TranscriptV2: payload 是通用 JSON 数据；若没有这行代码，类型边界不清楚。

from learning_agent.harness.models import utc_timestamp  # 新增代码+TranscriptV2: 复用统一 UTC 时间戳；若没有这行代码，不同日志时间格式会分裂。
from learning_agent.runtime.files import FileLock, append_jsonl, read_jsonl  # 新增代码+TranscriptV2: 复用锁和 JSONL helper；若没有这行代码，落盘和读取规则会重复分叉。


@dataclass  # 新增代码+TranscriptV2: 自动生成初始化和比较方法；若没有这行代码，事件对象要手写样板代码。
class TranscriptEntry:  # 新增代码+TranscriptV2: 表示一条可回放 transcript 事件；若没有这个类，恢复器只能处理松散 dict。
    uuid: str  # 新增代码+TranscriptV2: 保存事件唯一编号；若没有这行代码，compact boundary 和 checkpoint 无法引用具体事件。
    session_id: str  # 新增代码+TranscriptV2: 保存所属 session；若没有这行代码，多个会话事件会混在一起。
    run_id: str  # 新增代码+TranscriptV2: 保存所属 run；若没有这行代码，状态和 transcript 难以关联。
    turn_id: str  # 新增代码+TranscriptV2: 保存所属 turn；若没有这行代码，恢复时无法知道事件属于哪一轮。
    event_type: str  # 新增代码+TranscriptV2: 保存事件类型；若没有这行代码，恢复器无法区分 user/model/tool/compact。
    payload: dict[str, Any] = field(default_factory=dict)  # 新增代码+TranscriptV2: 保存事件载荷；若没有这行代码，事件只有壳没有业务数据。
    parent_uuid: str = ""  # 新增代码+TranscriptV2: 保存父事件 uuid；若没有这行代码，事件链无法审计因果关系。
    timestamp: str = field(default_factory=utc_timestamp)  # 新增代码+TranscriptV2: 保存创建时间；若没有这行代码，审计时间线缺少顺序证据。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+TranscriptV2: 把条目转成可写 JSON 的字典；若没有这行代码，store 不能稳定落盘。
        return {"uuid": self.uuid, "session_id": self.session_id, "run_id": self.run_id, "turn_id": self.turn_id, "event_type": self.event_type, "payload": copy.deepcopy(self.payload), "parent_uuid": self.parent_uuid, "timestamp": self.timestamp}  # 新增代码+TranscriptV2: 返回完整字段副本；若没有这行代码，恢复会丢关键字段。

    @classmethod  # 新增代码+TranscriptV2: 提供从 JSON dict 恢复对象的入口；若没有这行代码，reader 只能返回松散 dict。
    def from_dict(cls, payload: dict[str, Any]) -> "TranscriptEntry":  # 新增代码+TranscriptV2: 从持久化字段恢复 transcript 条目；若没有这行代码，重启后无法类型化事件。
        raw_payload = payload.get("payload", {})  # 新增代码+TranscriptV2: 读取业务载荷字段；若没有这行代码，payload 缺失会造成 KeyError。
        safe_payload = copy.deepcopy(raw_payload) if isinstance(raw_payload, dict) else {}  # 新增代码+TranscriptV2: 非 dict 载荷兜底为空对象；若没有这行代码，坏事件会拖垮恢复器。
        return cls(uuid=str(payload.get("uuid", "")), session_id=str(payload.get("session_id", "")), run_id=str(payload.get("run_id", "")), turn_id=str(payload.get("turn_id", "")), event_type=str(payload.get("event_type", "")), payload=safe_payload, parent_uuid=str(payload.get("parent_uuid", "")), timestamp=str(payload.get("timestamp", "")))  # 新增代码+TranscriptV2: 返回稳定条目对象；若没有这行代码，调用方要重复清洗字段。


class TranscriptV2Store:  # 新增代码+TranscriptV2: 管理 transcript v2 的读写路径；若没有这个类，事件持久化会散落在主循环。
    def __init__(self, base_dir: str | Path) -> None:  # 新增代码+TranscriptV2: 初始化 session 根目录；若没有这行代码，调用方无法指定测试或生产位置。
        self.base_dir = Path(base_dir)  # 新增代码+TranscriptV2: 规范化根目录；若没有这行代码，路径操作不稳定。
        self.lock_path = self.base_dir / "transcript_v2.lock"  # 新增代码+TranscriptV2: 定义全局写入锁；若没有这行代码，多进程追加可能交错。

    def session_dir(self, session_id: str) -> Path:  # 新增代码+TranscriptV2: 计算 session 目录；若没有这行代码，读写路径可能不一致。
        return self.base_dir / str(session_id)  # 新增代码+TranscriptV2: 返回固定 session 目录；若没有这行代码，恢复器找不到同一位置。

    def transcript_path(self, session_id: str) -> Path:  # 新增代码+TranscriptV2: 计算 transcript_v2.jsonl 路径；若没有这行代码，事件文件名会散乱。
        return self.session_dir(session_id) / "transcript_v2.jsonl"  # 新增代码+TranscriptV2: 返回固定 JSONL 文件；若没有这行代码，重启回放没有稳定入口。

    def append_entry(self, session_id: str, run_id: str, turn_id: str, event_type: str, payload: dict[str, Any] | None = None, parent_uuid: str = "", timestamp: str = "") -> TranscriptEntry:  # 新增代码+TranscriptV2: 追加一条 transcript 事件；若没有这行代码，主循环无法在模型前持久化 prompt。
        entry = TranscriptEntry(uuid=f"entry_{secrets.token_hex(12)}", session_id=str(session_id), run_id=str(run_id), turn_id=str(turn_id), event_type=str(event_type), payload=copy.deepcopy(payload or {}), parent_uuid=str(parent_uuid), timestamp=timestamp or utc_timestamp())  # 新增代码+TranscriptV2: 构造完整事件条目；若没有这行代码，事件缺少唯一 id 和时间。
        with FileLock(self.lock_path):  # 新增代码+TranscriptV2: 追加写入前加锁；若没有这行代码，并发写入可能破坏 JSONL 行。
            append_jsonl(self.transcript_path(entry.session_id), entry.to_dict())  # 新增代码+TranscriptV2: 把事件写入 session JSONL；若没有这行代码，事件不会落盘。
        return entry  # 新增代码+TranscriptV2: 返回条目供 checkpoint 引用；若没有这行代码，调用方拿不到 uuid。

    def list_entries(self, session_id: str) -> list[TranscriptEntry]:  # 新增代码+TranscriptV2: 读取某个 session 的所有事件；若没有这行代码，resume loader 无法回放 transcript。
        rows = read_jsonl(self.transcript_path(session_id))  # 新增代码+TranscriptV2: 容错读取 JSONL 行；若没有这行代码，坏行会拖垮恢复。
        return [TranscriptEntry.from_dict(row) for row in rows]  # 新增代码+TranscriptV2: 转成类型化事件列表；若没有这行代码，调用方要重复 from_dict。

    def latest_uuid(self, session_id: str) -> str:  # 新增代码+TranscriptV2: 读取某个 session 最后一条事件 uuid；若没有这行代码，新事件父节点要由调用方遍历。
        entries = self.list_entries(session_id)  # 新增代码+TranscriptV2: 读取事件列表；若没有这行代码，无法找到最后一条。
        return entries[-1].uuid if entries else ""  # 新增代码+TranscriptV2: 返回最后 uuid 或空字符串；若没有这行代码，空 transcript 会抛越界错误。
