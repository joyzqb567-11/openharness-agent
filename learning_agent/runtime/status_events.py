"""状态事件协议，为终端、SDK、HTTP 和工具提供统一事件流。"""  # 新增代码+StatusEcosystem: 说明本模块保存状态事件事实源；若没有这行代码，状态生态会继续分散在各日志里。

from __future__ import annotations  # 新增代码+StatusEcosystem: 延迟解析类型注解；若没有这行代码，类方法返回自身类型时更容易受顺序影响。

import copy  # 新增代码+StatusEcosystem: 深拷贝 payload 防止调用方污染事件；若没有这行代码，已记录状态可能被后续修改。
from dataclasses import dataclass, field  # 新增代码+StatusEcosystem: 用 dataclass 定义状态事件；若没有这行代码，字段会散成普通 dict。
from pathlib import Path  # 新增代码+StatusEcosystem: 使用 Path 管理 status 目录；若没有这行代码，路径拼接更脆弱。
from typing import Any  # 新增代码+StatusEcosystem: payload 是通用 JSON；若没有这行代码，类型边界不清楚。

from learning_agent.harness.models import utc_timestamp  # 新增代码+StatusEcosystem: 复用统一 UTC 时间戳；若没有这行代码，状态时间会和 harness 分裂。
from learning_agent.runtime.files import FileLock, append_jsonl, atomic_write_json, read_json_or_default, read_jsonl  # 新增代码+StatusEcosystem: 复用锁、原子写和 JSONL helper；若没有这行代码，状态事件读写规则会重复。
from learning_agent.runtime.status_schema import STATUS_EVENT_TYPES_V2, STATUS_SCHEMA_VERSION, normalize_event_type  # 新增代码+StatusSchemaV2: 导入统一状态协议常量；若没有这行代码，事件版本和类型会继续分散。


STATUS_EVENT_TYPES: set[str] = set(STATUS_EVENT_TYPES_V2) | {  # 修改代码+StatusSchemaV2: 兼容旧事件集合并扩展到 v2；若没有这行代码，旧引用会看不到新事件。
    "run_started",  # 新增代码+StatusEcosystem: 表示 run 开始；若没有这行代码，事件枚举缺少运行起点。
    "run_completed",  # 新增代码+StatusEcosystem: 表示 run 完成；若没有这行代码，事件枚举缺少运行终点。
    "run_failed",  # 新增代码+StatusEcosystem: 表示 run 失败；若没有这行代码，状态页无法分类失败事件。
    "stage_started",  # 新增代码+StatusEcosystem: 表示阶段开始；若没有这行代码，阶段状态事件缺起点。
    "stage_completed",  # 新增代码+StatusEcosystem: 表示阶段完成；若没有这行代码，阶段状态事件缺终点。
    "task_updated",  # 新增代码+StatusEcosystem: 表示任务状态更新；若没有这行代码，后台任务变化无法统一观察。
    "compact_completed",  # 新增代码+StatusEcosystem: 表示 compact 已完成；若没有这行代码，状态页无法提示上下文被压缩。
    "resume_loaded",  # 新增代码+StatusEcosystem: 表示恢复上下文已加载；若没有这行代码，状态页无法解释恢复动作。
    "status_probe",  # 新增代码+StatusEcosystem: 测试和外部探针事件；若没有这行代码，验收无法写入轻量事件。
}  # 新增代码+StatusEcosystem: 状态事件集合结束；若没有这行代码，Python set 语法不完整。


@dataclass  # 新增代码+StatusEcosystem: 自动生成初始化方法；若没有这行代码，状态事件对象要手写构造器。
class StatusEvent:  # 新增代码+StatusEcosystem: 表示一条全局状态事件；若没有这个类，SDK 只能返回松散 dict。
    sequence: int  # 新增代码+StatusEcosystem: 保存全局递增序号；若没有这行代码，外部 SDK 无法增量订阅。
    event_type: str  # 新增代码+StatusEcosystem: 保存事件类型；若没有这行代码，状态消费者无法过滤。
    schema_version: int = STATUS_SCHEMA_VERSION  # 新增代码+StatusSchemaV2: 保存事件协议版本；若没有这行代码，外部 agent 无法区分 v1/v2 字段。
    session_id: str = ""  # 新增代码+StatusSchemaV2: 顶层保存 session id；若没有这行代码，SDK 必须解析 payload 才能关联会话。
    run_id: str = ""  # 新增代码+StatusSchemaV2: 顶层保存 run id；若没有这行代码，状态事件无法和 durable run 直接对齐。
    turn_id: str = ""  # 新增代码+StatusSchemaV2: 顶层保存 turn id；若没有这行代码，resume 和 UI 无法定位事件属于哪轮。
    payload: dict[str, Any] = field(default_factory=dict)  # 新增代码+StatusEcosystem: 保存事件正文；若没有这行代码，事件没有业务信息。
    timestamp: str = field(default_factory=utc_timestamp)  # 新增代码+StatusEcosystem: 保存事件时间；若没有这行代码，审计时间线缺失。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+StatusEcosystem: 把事件转成 JSON dict；若没有这行代码，store 无法稳定落盘。
        return {"schema_version": self.schema_version, "sequence": self.sequence, "timestamp": self.timestamp, "session_id": self.session_id, "run_id": self.run_id, "turn_id": self.turn_id, "event_type": self.event_type, "payload": copy.deepcopy(self.payload)}  # 修改代码+StatusSchemaV2: 返回 v2 顶层身份字段；若没有这行代码，外部 SDK 仍要猜事件归属。

    @classmethod  # 新增代码+StatusEcosystem: 提供从 dict 恢复事件的入口；若没有这行代码，list_events 要返回松散 dict。
    def from_dict(cls, payload: dict[str, Any]) -> "StatusEvent":  # 新增代码+StatusEcosystem: 从持久化字段恢复状态事件；若没有这行代码，重启后无法类型化事件。
        raw_payload = payload.get("payload", {})  # 新增代码+StatusEcosystem: 读取事件载荷；若没有这行代码，payload 缺失会报错。
        safe_payload = copy.deepcopy(raw_payload) if isinstance(raw_payload, dict) else {}  # 新增代码+StatusEcosystem: 非 dict 载荷兜底为空；若没有这行代码，坏事件会拖垮 SDK。
        return cls(sequence=int(payload.get("sequence", 0)), event_type=normalize_event_type(str(payload.get("event_type", ""))), schema_version=int(payload.get("schema_version", 1)), session_id=str(payload.get("session_id", safe_payload.get("session_id", ""))), run_id=str(payload.get("run_id", safe_payload.get("run_id", ""))), turn_id=str(payload.get("turn_id", safe_payload.get("turn_id", ""))), payload=safe_payload, timestamp=str(payload.get("timestamp", "")))  # 修改代码+StatusSchemaV2: 兼容旧 payload 内身份字段并恢复 v2 事件；若没有这行代码，旧事件会丢关联信息。


class StatusEventStore:  # 新增代码+StatusEcosystem: 管理全局状态事件落盘；若没有这个类，状态事件会分散在各组件。
    def __init__(self, base_dir: str | Path) -> None:  # 新增代码+StatusEcosystem: 初始化 status 根目录；若没有这行代码，调用方无法指定测试或生产位置。
        self.base_dir = Path(base_dir)  # 新增代码+StatusEcosystem: 规范化根目录；若没有这行代码，路径操作不稳定。
        self.events_path = self.base_dir / "events.jsonl"  # 新增代码+StatusEcosystem: 定义事件 JSONL 路径；若没有这行代码，SDK 找不到事件流。
        self.state_path = self.base_dir / "state.json"  # 新增代码+StatusEcosystem: 定义状态序号文件；若没有这行代码，sequence 重启后会重复。
        self.lock_path = self.base_dir / "status.lock"  # 新增代码+StatusEcosystem: 定义写锁；若没有这行代码，多进程 append 可能重复序号。
        self.quarantine_dir = self.base_dir / "quarantine"  # 新增代码+StatusEcosystem: 定义坏 JSON 隔离目录；若没有这行代码，半写 state 会反复拖垮读取。

    def append(self, event_type: str, payload: dict[str, Any] | None = None, session_id: str = "", run_id: str = "", turn_id: str = "") -> StatusEvent:  # 修改代码+StatusSchemaV2: 追加事件时允许顶层身份字段；若没有这行代码，SDK 无法直接按 run/session/turn 过滤。
        with FileLock(self.lock_path):  # 新增代码+StatusEcosystem: sequence 分配和写入必须加锁；若没有这行代码，并发事件可能同号。
            state = read_json_or_default(self.state_path, {"last_sequence": 0}, quarantine_dir=self.quarantine_dir)  # 新增代码+StatusEcosystem: 读取上次序号；若没有这行代码，重启后无法继续递增。
            last_sequence = int(state.get("last_sequence", 0)) if isinstance(state, dict) else 0  # 新增代码+StatusEcosystem: 安全提取序号；若没有这行代码，坏 state 会报错。
            safe_payload = copy.deepcopy(payload or {})  # 新增代码+StatusSchemaV2: 复制 payload 防止调用方后续修改；若没有这行代码，落盘事件可能被污染。
            inferred_session_id = str(session_id or safe_payload.get("session_id", ""))  # 新增代码+StatusSchemaV2: 从参数或 payload 推断 session；若没有这行代码，旧调用点会丢 session_id。
            inferred_run_id = str(run_id or safe_payload.get("run_id", ""))  # 新增代码+StatusSchemaV2: 从参数或 payload 推断 run；若没有这行代码，旧 emit 事件无法和 run 对齐。
            inferred_turn_id = str(turn_id or safe_payload.get("turn_id", ""))  # 新增代码+StatusSchemaV2: 从参数或 payload 推断 turn；若没有这行代码，模型轮次不可见。
            event = StatusEvent(sequence=last_sequence + 1, event_type=normalize_event_type(event_type), schema_version=STATUS_SCHEMA_VERSION, session_id=inferred_session_id, run_id=inferred_run_id, turn_id=inferred_turn_id, payload=safe_payload, timestamp=utc_timestamp())  # 修改代码+StatusSchemaV2: 构造带身份字段的 v2 事件；若没有这行代码，事件流仍停留在基础日志。
            append_jsonl(self.events_path, event.to_dict())  # 新增代码+StatusEcosystem: 写入 JSONL 事件；若没有这行代码，事件不会落盘。
            atomic_write_json(self.state_path, {"last_sequence": event.sequence})  # 新增代码+StatusEcosystem: 保存最新序号；若没有这行代码，下次事件会重复 sequence。
        return event  # 新增代码+StatusEcosystem: 返回事件供调用方记录；若没有这行代码，调用方拿不到 sequence。

    def list_events(self, since_sequence: int | None = None, limit: int | None = None) -> list[StatusEvent]:  # 新增代码+StatusEcosystem: 列出状态事件；若没有这行代码，SDK 和状态工具无法观察历史。
        rows = read_jsonl(self.events_path)  # 新增代码+StatusEcosystem: 容错读取 JSONL；若没有这行代码，坏行会拖垮状态页。
        events = [StatusEvent.from_dict(row) for row in rows]  # 新增代码+StatusEcosystem: 恢复类型化事件；若没有这行代码，调用方要重复转换。
        if since_sequence is not None:  # 新增代码+StatusEcosystem: 如果调用方请求增量；若没有这行代码，SDK 只能每次全量读取。
            events = [event for event in events if event.sequence > int(since_sequence)]  # 新增代码+StatusEcosystem: 只保留新事件；若没有这行代码，watcher 会反复看到旧事件。
        if limit is not None:  # 新增代码+StatusEcosystem: 如果调用方限制数量；若没有这行代码，长事件流可能刷屏。
            events = events[-max(1, int(limit)):]  # 新增代码+StatusEcosystem: 返回最后 N 条；若没有这行代码，limit=0 会产生空结果难以排查。
        return events  # 新增代码+StatusEcosystem: 返回事件列表；若没有这行代码，调用方拿不到历史。
