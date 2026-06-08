"""持久 turn ledger，记录每一轮从接收到完成或中断的状态。"""  # 新增代码+TurnLedger: 说明本模块让恢复器知道每一轮进度；若没有这行代码，维护者会误以为只靠 transcript 就够。

from __future__ import annotations  # 新增代码+TurnLedger: 延迟解析类型注解；若没有这行代码，类方法返回自身类型时更容易受顺序影响。

from dataclasses import dataclass, field  # 新增代码+TurnLedger: 用 dataclass 定义 turn 记录；若没有这行代码，字段会散成普通 dict。
from pathlib import Path  # 新增代码+TurnLedger: 使用 Path 管理 session 目录；若没有这行代码，路径拼接更脆弱。
from typing import Any  # 新增代码+TurnLedger: metadata 是通用 JSON；若没有这行代码，类型边界不清楚。

from learning_agent.harness.models import utc_timestamp  # 新增代码+TurnLedger: 复用统一 UTC 时间；若没有这行代码，状态时间格式会分裂。
from learning_agent.runtime.files import FileLock, atomic_write_json, read_json_or_default  # 新增代码+TurnLedger: 复用锁和原子 JSON helper；若没有这行代码，turn 状态会有半写风险。


@dataclass  # 新增代码+TurnLedger: 自动生成初始化方法；若没有这行代码，turn 记录要手写构造器。
class TurnRecord:  # 新增代码+TurnLedger: 表示一个可恢复的模型轮次；若没有这个类，状态只能是松散 dict。
    session_id: str  # 新增代码+TurnLedger: 保存所属 session；若没有这行代码，多个会话的 turn 会混在一起。
    run_id: str  # 新增代码+TurnLedger: 保存所属 run；若没有这行代码，turn 无法和 harness 状态关联。
    turn_id: str  # 新增代码+TurnLedger: 保存轮次唯一编号；若没有这行代码，更新状态无法定位目标轮次。
    user_input: str = ""  # 新增代码+TurnLedger: 保存该轮用户输入摘要；若没有这行代码，恢复时不知道轮次起点。
    status: str = "accepted"  # 新增代码+TurnLedger: 保存 accepted/model_running/tools_running/completed/failed/interrupted 等状态；若没有这行代码，恢复器无法判断进度。
    checkpoint_uuid: str = ""  # 新增代码+TurnLedger: 保存最近安全恢复点；若没有这行代码，中断恢复无法定位 transcript 事件。
    metadata: dict[str, Any] = field(default_factory=dict)  # 新增代码+TurnLedger: 保存扩展信息；若没有这行代码，后续 compact 和 verifier 字段无处存放。
    created_at: str = field(default_factory=utc_timestamp)  # 新增代码+TurnLedger: 保存创建时间；若没有这行代码，审计时间线缺起点。
    updated_at: str = field(default_factory=utc_timestamp)  # 新增代码+TurnLedger: 保存更新时间；若没有这行代码，状态页无法判断新旧。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+TurnLedger: 把 turn 转成 JSON dict；若没有这行代码，ledger 无法保存。
        return {"session_id": self.session_id, "run_id": self.run_id, "turn_id": self.turn_id, "user_input": self.user_input, "status": self.status, "checkpoint_uuid": self.checkpoint_uuid, "metadata": dict(self.metadata), "created_at": self.created_at, "updated_at": self.updated_at}  # 新增代码+TurnLedger: 返回完整字段；若没有这行代码，恢复会丢失 checkpoint。

    @classmethod  # 新增代码+TurnLedger: 提供从 JSON dict 恢复记录的入口；若没有这行代码，ledger 读取只能返回松散 dict。
    def from_dict(cls, payload: dict[str, Any]) -> "TurnRecord":  # 新增代码+TurnLedger: 从持久化字段恢复 turn；若没有这行代码，重启后无法类型化状态。
        metadata_raw = payload.get("metadata", {})  # 新增代码+TurnLedger: 读取扩展字段；若没有这行代码，metadata 缺失会抛错。
        return cls(session_id=str(payload.get("session_id", "")), run_id=str(payload.get("run_id", "")), turn_id=str(payload.get("turn_id", "")), user_input=str(payload.get("user_input", "")), status=str(payload.get("status", "accepted")), checkpoint_uuid=str(payload.get("checkpoint_uuid", "")), metadata=metadata_raw if isinstance(metadata_raw, dict) else {}, created_at=str(payload.get("created_at", "")), updated_at=str(payload.get("updated_at", "")))  # 新增代码+TurnLedger: 返回稳定记录；若没有这行代码，调用方要重复清洗。


class TurnLedger:  # 新增代码+TurnLedger: 管理 session 下 turns.json；若没有这个类，主循环和恢复器会重复读写逻辑。
    def __init__(self, base_dir: str | Path) -> None:  # 新增代码+TurnLedger: 初始化 session 根目录；若没有这行代码，调用方无法指定存储位置。
        self.base_dir = Path(base_dir)  # 新增代码+TurnLedger: 规范化根目录；若没有这行代码，路径操作不稳定。
        self.lock_path = self.base_dir / "turn_ledger.lock"  # 新增代码+TurnLedger: 定义 ledger 写锁；若没有这行代码，多进程更新可能互相覆盖。

    def turns_path(self, session_id: str) -> Path:  # 新增代码+TurnLedger: 计算某个 session 的 turns.json；若没有这行代码，读写路径可能不一致。
        return self.base_dir / str(session_id) / "turns.json"  # 新增代码+TurnLedger: 返回固定 turn 文件；若没有这行代码，恢复器找不到状态。

    def accept_turn(self, session_id: str, run_id: str, turn_id: str, user_input: str, metadata: dict[str, Any] | None = None) -> TurnRecord:  # 新增代码+TurnLedger: 记录新 turn 已接收；若没有这行代码，用户输入进入模型前没有 durable 标记。
        record = TurnRecord(session_id=str(session_id), run_id=str(run_id), turn_id=str(turn_id), user_input=str(user_input), metadata=dict(metadata or {}))  # 新增代码+TurnLedger: 构造 accepted 状态记录；若没有这行代码，ledger 没有对象可保存。
        self._upsert(record)  # 新增代码+TurnLedger: 保存或更新 turn；若没有这行代码，新 turn 只存在内存。
        return record  # 新增代码+TurnLedger: 返回记录供调用方继续更新；若没有这行代码，调用方拿不到 turn_id 状态。

    def update_status(self, session_id: str, turn_id: str, status: str, checkpoint_uuid: str = "", metadata: dict[str, Any] | None = None) -> TurnRecord:  # 新增代码+TurnLedger: 更新指定 turn 状态；若没有这行代码，模型运行、工具运行和完成状态无法落盘。
        record = self.get_turn(session_id, turn_id)  # 新增代码+TurnLedger: 读取现有 turn；若没有这行代码，更新可能覆盖其他字段。
        record.status = str(status)  # 新增代码+TurnLedger: 写入新状态；若没有这行代码，状态不会推进。
        if checkpoint_uuid:  # 新增代码+TurnLedger: 只有提供 checkpoint 时才覆盖；若没有这行代码，空字符串会误清掉恢复点。
            record.checkpoint_uuid = str(checkpoint_uuid)  # 新增代码+TurnLedger: 保存最近恢复点；若没有这行代码，中断后无法定位。
        if metadata:  # 新增代码+TurnLedger: 如果调用方提供扩展字段；若没有这行代码，metadata 更新会被忽略。
            record.metadata.update(dict(metadata))  # 新增代码+TurnLedger: 合并扩展字段；若没有这行代码，compact/verifier 信息无法追加。
        record.updated_at = utc_timestamp()  # 新增代码+TurnLedger: 刷新更新时间；若没有这行代码，审计不知道状态何时变化。
        self._upsert(record)  # 新增代码+TurnLedger: 保存更新后的记录；若没有这行代码，状态只在内存中。
        return record  # 新增代码+TurnLedger: 返回更新记录；若没有这行代码，调用方无法检查结果。

    def get_turn(self, session_id: str, turn_id: str) -> TurnRecord:  # 新增代码+TurnLedger: 读取指定 turn；若没有这行代码，恢复器无法定位轮次。
        turns = self.list_turns(session_id)  # 新增代码+TurnLedger: 读取该 session 所有 turn；若没有这行代码，无法查找目标。
        for record in turns:  # 新增代码+TurnLedger: 遍历 turn 列表；若没有这行代码，目标无法匹配。
            if record.turn_id == turn_id:  # 新增代码+TurnLedger: 找到目标 turn；若没有这行代码，所有记录都会被跳过。
                return record  # 新增代码+TurnLedger: 返回目标记录；若没有这行代码，调用方拿不到结果。
        raise KeyError(turn_id)  # 新增代码+TurnLedger: 找不到时明确报错；若没有这行代码，调用方会拿到空值并误判。

    def list_turns(self, session_id: str) -> list[TurnRecord]:  # 新增代码+TurnLedger: 列出 session 下所有 turn；若没有这行代码，状态页无法展示轮次。
        payload = read_json_or_default(self.turns_path(session_id), {"turns": []}, quarantine_dir=self.base_dir / "quarantine")  # 新增代码+TurnLedger: 容错读取 turns.json；若没有这行代码，坏 JSON 会拖垮恢复。
        raw_turns = payload.get("turns", []) if isinstance(payload, dict) else []  # 新增代码+TurnLedger: 提取 turns 数组；若没有这行代码，坏根对象会触发属性错误。
        return [TurnRecord.from_dict(item) for item in raw_turns if isinstance(item, dict)]  # 新增代码+TurnLedger: 返回类型化 turn 列表；若没有这行代码，调用方要重复转换。

    def _upsert(self, record: TurnRecord) -> None:  # 新增代码+TurnLedger: 保存或替换某个 turn；若没有这行代码，accept 和 update 会重复读改写。
        with FileLock(self.lock_path):  # 新增代码+TurnLedger: 加锁保护 turns.json；若没有这行代码，并发更新可能丢记录。
            payload = read_json_or_default(self.turns_path(record.session_id), {"turns": []}, quarantine_dir=self.base_dir / "quarantine")  # 新增代码+TurnLedger: 读取现有 turn 文件；若没有这行代码，新记录会覆盖旧记录。
            raw_turns = payload.get("turns", []) if isinstance(payload, dict) else []  # 新增代码+TurnLedger: 提取数组并兜底；若没有这行代码，坏文件会崩溃。
            records = [TurnRecord.from_dict(item) for item in raw_turns if isinstance(item, dict)]  # 新增代码+TurnLedger: 恢复已有记录；若没有这行代码，无法替换目标。
            replaced = False  # 新增代码+TurnLedger: 标记是否已替换旧记录；若没有这行代码，可能重复追加同一 turn。
            for index, old_record in enumerate(records):  # 新增代码+TurnLedger: 遍历已有记录和索引；若没有这行代码，无法原位替换。
                if old_record.turn_id == record.turn_id:  # 新增代码+TurnLedger: 匹配同一 turn；若没有这行代码，会把所有 turn 都保留为旧值。
                    records[index] = record  # 新增代码+TurnLedger: 替换目标记录；若没有这行代码，更新不会生效。
                    replaced = True  # 新增代码+TurnLedger: 标记已替换；若没有这行代码，后面会重复追加。
                    break  # 新增代码+TurnLedger: 找到后停止扫描；若没有这行代码，会继续无意义遍历。
            if not replaced:  # 新增代码+TurnLedger: 如果没有旧记录；若没有这行代码，新 turn 不会追加。
                records.append(record)  # 新增代码+TurnLedger: 追加新 turn；若没有这行代码，accept_turn 不会保存。
            atomic_write_json(self.turns_path(record.session_id), {"turns": [item.to_dict() for item in records]})  # 新增代码+TurnLedger: 原子写回 turns.json；若没有这行代码，崩溃可能留下半写文件。
