"""持久任务登记表，对齐 ClaudeCode local/remote/background task 状态。"""  # 新增代码+DurableTaskRegistry: 说明本文件负责把 task 状态落盘；若没有这行代码，任务生命周期边界不清楚。

from __future__ import annotations  # 新增代码+DurableTaskRegistry: 延迟解析类型注解；若没有这行代码，类方法返回自身类型时更容易出错。

from dataclasses import dataclass, field  # 新增代码+DurableTaskRegistry: 用 dataclass 定义任务记录；若没有这行代码，字段管理会变成松散 dict。
from pathlib import Path  # 新增代码+DurableTaskRegistry: 用 Path 管理任务目录；若没有这行代码，Windows 路径处理更脆弱。
from typing import Any  # 新增代码+DurableTaskRegistry: 任务 metadata 是通用 JSON；若没有这行代码，类型边界不清楚。

from learning_agent.harness.models import utc_timestamp  # 新增代码+DurableTaskRegistry: 复用统一 UTC 时间；若没有这行代码，任务时间格式会和 harness 不一致。
from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+DurableTaskRegistry: 完成任务后要写通知队列；若没有这行代码，后台结果不能自动回灌。
from learning_agent.runtime.files import FileLock, atomic_write_json, read_json_or_default  # 新增代码+DurableTaskRegistry: 导入锁和原子 JSON helper；若没有这行代码，任务状态会有半写风险。
from learning_agent.runtime.task_output import TaskOutputStore  # 新增代码+DurableTaskRegistry: 导入输出文件管理器；若没有这行代码，长任务输出无法落盘。


@dataclass  # 新增代码+DurableTaskRegistry: 自动生成 TaskRecord 初始化方法；若没有这行代码，任务记录要手写构造器。
class TaskRecord:  # 新增代码+DurableTaskRegistry: 表示一个可恢复的任务记录；若没有这个类，任务状态只能散落在内存对象里。
    task_id: str  # 新增代码+DurableTaskRegistry: 保存任务唯一 id；若没有这行代码，task_get/task_output 无法定位任务。
    prompt: str  # 新增代码+DurableTaskRegistry: 保存任务原始目标；若没有这行代码，恢复后不知道任务要做什么。
    kind: str = "agent"  # 新增代码+DurableTaskRegistry: 保存任务类型 agent/background_shell/remote；若没有这行代码，poller 无法按类型处理。
    status: str = "running"  # 新增代码+DurableTaskRegistry: 保存 running/completed/failed/stopped/needs_input；若没有这行代码，状态页无法判断任务生命期。
    output: str = ""  # 新增代码+DurableTaskRegistry: 保存输出摘要；若没有这行代码，短任务结果无法直接展示。
    error: str = ""  # 新增代码+DurableTaskRegistry: 保存失败或停止原因；若没有这行代码，失败任务无法解释。
    output_path: str = ""  # 新增代码+DurableTaskRegistry: 保存完整输出文件路径；若没有这行代码，长输出无法追踪。
    last_offset: int = 0  # 新增代码+DurableTaskRegistry: 保存已读输出 offset；若没有这行代码，poller 无法增量读取。
    notified: bool = False  # 新增代码+DurableTaskRegistry: 保存是否已经回灌通知；若没有这行代码，同一任务会重复通知模型。
    owner_run_id: str = ""  # 新增代码+DurableTaskRegistry: 保存所属 harness run；若没有这行代码，状态页难以关联任务和主 run。
    allowed_tool_names: list[str] = field(default_factory=list)  # 新增代码+DurableTaskRegistry: 保存子 agent 工具边界；若没有这行代码，安全审计缺少权限范围。
    max_turns: int | None = None  # 新增代码+DurableTaskRegistry: 保存子 agent 最大轮次；若没有这行代码，恢复时不知道执行约束。
    background: bool = False  # 新增代码+DurableTaskRegistry: 保存是否后台运行；若没有这行代码，UI 无法区分同步和异步任务。
    metadata: dict[str, Any] = field(default_factory=dict)  # 新增代码+DurableTaskRegistry: 保存扩展信息如 label/notes/remote id；若没有这行代码，后续扩展会破坏 schema。
    created_at: str = field(default_factory=utc_timestamp)  # 新增代码+DurableTaskRegistry: 保存创建时间；若没有这行代码，审计时间线缺起点。
    updated_at: str = field(default_factory=utc_timestamp)  # 新增代码+DurableTaskRegistry: 保存更新时间；若没有这行代码，状态页不知道记录新旧。
    completed_at: str = ""  # 新增代码+DurableTaskRegistry: 保存完成/失败/停止时间；若没有这行代码，任务收束时间不可见。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+DurableTaskRegistry: 把任务记录转成 JSON dict；若没有这行代码，registry 无法稳定落盘。
        return {"task_id": self.task_id, "prompt": self.prompt, "kind": self.kind, "status": self.status, "output": self.output, "error": self.error, "output_path": self.output_path, "last_offset": self.last_offset, "notified": self.notified, "owner_run_id": self.owner_run_id, "allowed_tool_names": list(self.allowed_tool_names), "max_turns": self.max_turns, "background": self.background, "metadata": dict(self.metadata), "created_at": self.created_at, "updated_at": self.updated_at, "completed_at": self.completed_at}  # 新增代码+DurableTaskRegistry: 返回完整字段；若没有这行代码，恢复后会丢失状态。

    @classmethod  # 新增代码+DurableTaskRegistry: 提供从 JSON dict 恢复任务记录的入口；若没有这行代码，registry 读取会返回松散 dict。
    def from_dict(cls, payload: dict[str, Any]) -> "TaskRecord":  # 新增代码+DurableTaskRegistry: 从持久化字段恢复任务记录；若没有这行代码，重启后无法类型化任务。
        allowed_raw = payload.get("allowed_tool_names", [])  # 新增代码+DurableTaskRegistry: 读取工具白名单字段；若没有这行代码，权限边界会丢失。
        metadata_raw = payload.get("metadata", {})  # 新增代码+DurableTaskRegistry: 读取扩展元数据；若没有这行代码，label/notes 等会丢失。
        return cls(task_id=str(payload.get("task_id", "")), prompt=str(payload.get("prompt", "")), kind=str(payload.get("kind", "agent")), status=str(payload.get("status", "running")), output=str(payload.get("output", "")), error=str(payload.get("error", "")), output_path=str(payload.get("output_path", "")), last_offset=int(payload.get("last_offset", 0)), notified=bool(payload.get("notified", False)), owner_run_id=str(payload.get("owner_run_id", "")), allowed_tool_names=[str(item) for item in allowed_raw] if isinstance(allowed_raw, list) else [], max_turns=payload.get("max_turns") if payload.get("max_turns") is None else int(payload.get("max_turns", 0)), background=bool(payload.get("background", False)), metadata=metadata_raw if isinstance(metadata_raw, dict) else {}, created_at=str(payload.get("created_at", "")), updated_at=str(payload.get("updated_at", "")), completed_at=str(payload.get("completed_at", "")))  # 新增代码+DurableTaskRegistry: 返回稳定任务对象；若没有这行代码，调用方要处理坏字段。


class TaskRegistry:  # 新增代码+DurableTaskRegistry: 管理持久任务 JSON 文件；若没有这个类，task 状态只能保存在 LearningAgent 内存字典。
    def __init__(self, base_dir: str | Path, output_store: TaskOutputStore | None = None, command_queue: RuntimeCommandQueue | None = None) -> None:  # 新增代码+DurableTaskRegistry: 初始化任务目录和可选依赖；若没有这行代码，调用方无法注入测试组件。
        self.base_dir = Path(base_dir)  # 新增代码+DurableTaskRegistry: 规范化任务根目录；若没有这行代码，路径操作不稳定。
        self.records_dir = self.base_dir / "records"  # 新增代码+DurableTaskRegistry: 定义任务记录目录；若没有这行代码，任务 JSON 会散落。
        self.lock_path = self.base_dir / "tasks.lock"  # 新增代码+DurableTaskRegistry: 定义任务登记表锁；若没有这行代码，多线程/多进程可能覆盖任务状态。
        self.quarantine_dir = self.base_dir / "quarantine"  # 新增代码+DurableTaskRegistry: 定义坏任务状态隔离目录；若没有这行代码，坏 JSON 会反复拖垮读取。
        self.output_store = output_store or TaskOutputStore(self.base_dir / "outputs")  # 新增代码+DurableTaskRegistry: 保存输出 store；若没有这行代码，任务输出无法统一落盘。
        self.command_queue = command_queue  # 新增代码+DurableTaskRegistry: 保存通知队列；若没有这行代码，任务完成后不能自动回灌。

    def task_path(self, task_id: str) -> Path:  # 新增代码+DurableTaskRegistry: 计算任务记录路径；若没有这行代码，读写路径可能不一致。
        safe_task_id = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in str(task_id))  # 新增代码+DurableTaskRegistry: 清洗 task_id 防止路径注入；若没有这行代码，奇怪 id 可能逃出目录。
        return self.records_dir / f"{safe_task_id}.json"  # 新增代码+DurableTaskRegistry: 返回固定 JSON 文件路径；若没有这行代码，重启恢复找不到任务。

    def create_task(self, task_id: str, prompt: str, kind: str = "agent", status: str = "running", allowed_tool_names: list[str] | None = None, max_turns: int | None = None, background: bool = False, owner_run_id: str = "", metadata: dict[str, Any] | None = None) -> TaskRecord:  # 新增代码+DurableTaskRegistry: 创建并保存任务记录；若没有这行代码，task 工具不能 durable 登记。
        record = TaskRecord(task_id=task_id, prompt=prompt, kind=kind, status=status, allowed_tool_names=list(allowed_tool_names or []), max_turns=max_turns, background=background, owner_run_id=owner_run_id, metadata=dict(metadata or {}))  # 新增代码+DurableTaskRegistry: 构造任务记录；若没有这行代码，创建入口没有对象可保存。
        record.output_path = str(self.output_store.flush(task_id))  # 新增代码+DurableTaskRegistry: 初始化并记录输出文件路径；若没有这行代码，长输出引用为空。
        self.save_task(record)  # 新增代码+DurableTaskRegistry: 保存任务记录；若没有这行代码，任务只存在内存。
        return record  # 新增代码+DurableTaskRegistry: 返回新记录；若没有这行代码，调用方拿不到任务对象。

    def save_task(self, record: TaskRecord) -> Path:  # 新增代码+DurableTaskRegistry: 保存任务记录到 JSON；若没有这行代码，任务状态不能跨进程恢复。
        record.updated_at = utc_timestamp()  # 新增代码+DurableTaskRegistry: 刷新更新时间；若没有这行代码，状态页无法判断信息新旧。
        with FileLock(self.lock_path):  # 新增代码+DurableTaskRegistry: 加锁保护任务文件写入；若没有这行代码，并发状态更新可能互相覆盖。
            return atomic_write_json(self.task_path(record.task_id), record.to_dict())  # 新增代码+DurableTaskRegistry: 原子保存任务 JSON；若没有这行代码，半写状态会破坏恢复。

    def get_task(self, task_id: str) -> TaskRecord:  # 新增代码+DurableTaskRegistry: 读取单个任务记录；若没有这行代码，task_get 无法跨 agent 实例工作。
        payload = read_json_or_default(self.task_path(task_id), {}, quarantine_dir=self.quarantine_dir)  # 新增代码+DurableTaskRegistry: 容错读取任务 JSON；若没有这行代码，坏任务文件会拖垮列表。
        if not isinstance(payload, dict) or not payload:  # 新增代码+DurableTaskRegistry: 检查任务是否存在或有效；若没有这行代码，空对象会伪装成任务。
            raise KeyError(task_id)  # 新增代码+DurableTaskRegistry: 未找到任务时抛 KeyError；若没有这行代码，调用方无法区分空记录和真实任务。
        return TaskRecord.from_dict(payload)  # 新增代码+DurableTaskRegistry: 返回类型化任务；若没有这行代码，调用方拿到松散 dict。

    def list_tasks(self) -> list[TaskRecord]:  # 新增代码+DurableTaskRegistry: 列出所有任务记录；若没有这行代码，状态 CLI 无法展示任务表。
        if not self.records_dir.exists():  # 新增代码+DurableTaskRegistry: 没有任务目录时返回空列表；若没有这行代码，首次运行 task_list 会报错。
            return []  # 新增代码+DurableTaskRegistry: 返回空任务列表；若没有这行代码，调用方需要重复兜底。
        records: list[TaskRecord] = []  # 新增代码+DurableTaskRegistry: 准备累计任务对象；若没有这行代码，函数没有返回容器。
        for path in sorted(self.records_dir.glob("*.json")):  # 新增代码+DurableTaskRegistry: 稳定遍历所有任务 JSON；若没有这行代码，任务列表顺序不可预测。
            payload = read_json_or_default(path, {}, quarantine_dir=self.quarantine_dir)  # 新增代码+DurableTaskRegistry: 容错读取单个任务；若没有这行代码，坏文件会中断整个列表。
            if isinstance(payload, dict) and payload:  # 新增代码+DurableTaskRegistry: 只恢复非空对象；若没有这行代码，空文件会污染列表。
                records.append(TaskRecord.from_dict(payload))  # 新增代码+DurableTaskRegistry: 保存恢复后的任务；若没有这行代码，列表不会包含该任务。
        return records  # 新增代码+DurableTaskRegistry: 返回任务列表；若没有这行代码，CLI 和工具拿不到结果。

    def append_output(self, task_id: str, text: str) -> TaskRecord:  # 新增代码+DurableTaskRegistry: 追加任务输出并更新摘要；若没有这行代码，输出文件和记录会脱节。
        record = self.get_task(task_id)  # 新增代码+DurableTaskRegistry: 读取当前任务；若没有这行代码，无法更新 output_path 和 last_offset。
        path = self.output_store.append(task_id, text)  # 新增代码+DurableTaskRegistry: 追加完整输出；若没有这行代码，长输出不会落盘。
        record.output_path = str(path)  # 新增代码+DurableTaskRegistry: 保存输出文件路径；若没有这行代码，状态页无法定位完整输出。
        record.output = self.output_store.tail(task_id, max_chars=4000)  # 新增代码+DurableTaskRegistry: 保存尾部摘要；若没有这行代码，task_get 无法快速展示最新输出。
        record.last_offset = len(self.output_store.read_all(task_id))  # 新增代码+DurableTaskRegistry: 保存当前输出长度；若没有这行代码，poller 无法增量读取。
        self.save_task(record)  # 新增代码+DurableTaskRegistry: 保存更新后的任务；若没有这行代码，输出摘要只在内存中。
        return record  # 新增代码+DurableTaskRegistry: 返回更新记录；若没有这行代码，调用方无法继续处理。

    def complete_task(self, task_id: str, output: str = "", usage: dict[str, Any] | None = None) -> TaskRecord:  # 新增代码+DurableTaskRegistry: 标记任务完成并可通知主 agent；若没有这行代码，子任务完成后不会 durable 收束。
        record = self.get_task(task_id)  # 新增代码+DurableTaskRegistry: 读取任务记录；若没有这行代码，无法更新指定任务。
        if output:  # 新增代码+DurableTaskRegistry: 如果有输出需要保存；若没有这行代码，空输出也会追加无意义内容。
            self.output_store.append(task_id, output)  # 新增代码+DurableTaskRegistry: 保存完整输出；若没有这行代码，长结果可能只保存在摘要字段。
        record.status = "completed"  # 新增代码+DurableTaskRegistry: 标记任务完成；若没有这行代码，状态页会一直显示 running。
        record.output_path = str(self.output_store.output_path(task_id))  # 新增代码+DurableTaskRegistry: 更新输出路径；若没有这行代码，通知里可能缺完整结果引用。
        record.output = output or self.output_store.tail(task_id, max_chars=4000)  # 新增代码+DurableTaskRegistry: 保存输出摘要；若没有这行代码，task_get 看不到结果。
        record.last_offset = len(self.output_store.read_all(task_id))  # 新增代码+DurableTaskRegistry: 更新输出 offset；若没有这行代码，后续 delta 会重复旧内容。
        record.completed_at = utc_timestamp()  # 新增代码+DurableTaskRegistry: 保存完成时间；若没有这行代码，审计不知道任务何时结束。
        self._notify_once(record, usage=usage or {})  # 新增代码+DurableTaskRegistry: 生成完成通知；若没有这行代码，主 agent 需要手动 task_output 才能看到结果。
        self.save_task(record)  # 新增代码+DurableTaskRegistry: 保存完成状态；若没有这行代码，重启后任务仍可能 running。
        return record  # 新增代码+DurableTaskRegistry: 返回完成记录；若没有这行代码，调用方拿不到状态。

    def fail_task(self, task_id: str, error: str) -> TaskRecord:  # 新增代码+DurableTaskRegistry: 标记任务失败并通知；若没有这行代码，失败后台任务会卡在 running。
        record = self.get_task(task_id)  # 新增代码+DurableTaskRegistry: 读取任务记录；若没有这行代码，无法更新指定任务。
        record.status = "failed"  # 新增代码+DurableTaskRegistry: 标记失败；若没有这行代码，任务失败不可见。
        record.error = str(error)  # 新增代码+DurableTaskRegistry: 保存失败原因；若没有这行代码，用户不知道为什么失败。
        record.completed_at = utc_timestamp()  # 新增代码+DurableTaskRegistry: 保存失败时间；若没有这行代码，审计时间线缺终点。
        self._notify_once(record, usage={})  # 新增代码+DurableTaskRegistry: 生成失败通知；若没有这行代码，主 agent 不会自动知道失败。
        self.save_task(record)  # 新增代码+DurableTaskRegistry: 保存失败状态；若没有这行代码，失败只在内存中。
        return record  # 新增代码+DurableTaskRegistry: 返回失败记录；若没有这行代码，调用方拿不到状态。

    def stop_task(self, task_id: str, reason: str = "") -> TaskRecord:  # 新增代码+DurableTaskRegistry: 持久标记任务停止；若没有这行代码，task_stop 无法跨实例审计。
        record = self.get_task(task_id)  # 新增代码+DurableTaskRegistry: 读取任务记录；若没有这行代码，无法定位任务。
        record.status = "stopped"  # 新增代码+DurableTaskRegistry: 标记停止；若没有这行代码，状态页仍显示 running。
        record.error = reason or "任务已停止。"  # 新增代码+DurableTaskRegistry: 保存停止原因；若没有这行代码，用户不知道谁为什么停止。
        record.completed_at = utc_timestamp()  # 新增代码+DurableTaskRegistry: 保存停止时间；若没有这行代码，任务收束不可审计。
        self._notify_once(record, usage={})  # 新增代码+DurableTaskRegistry: 生成停止通知；若没有这行代码，主 agent 不会自动知道停止。
        self.save_task(record)  # 新增代码+DurableTaskRegistry: 保存停止状态；若没有这行代码，状态不会跨进程生效。
        return record  # 新增代码+DurableTaskRegistry: 返回停止记录；若没有这行代码，调用方拿不到结果。

    def mark_needs_input(self, task_id: str, summary: str) -> TaskRecord:  # 新增代码+DurableTaskRegistry: 标记任务需要用户输入并通知；若没有这行代码，watchdog 只能观察不能回灌。
        record = self.get_task(task_id)  # 新增代码+DurableTaskRegistry: 读取任务记录；若没有这行代码，无法更新任务状态。
        record.status = "needs_input"  # 新增代码+DurableTaskRegistry: 标记需要输入；若没有这行代码，状态页无法突出卡点。
        record.output = summary  # 新增代码+DurableTaskRegistry: 保存卡点摘要；若没有这行代码，通知缺少上下文。
        self._notify_once(record, usage={})  # 新增代码+DurableTaskRegistry: 生成 needs_input 通知；若没有这行代码，主 agent 不会提示用户接管。
        self.save_task(record)  # 新增代码+DurableTaskRegistry: 保存状态；若没有这行代码，重启后卡点丢失。
        return record  # 新增代码+DurableTaskRegistry: 返回更新记录；若没有这行代码，poller 无法统计变化。

    def _notify_once(self, record: TaskRecord, usage: dict[str, Any]) -> None:  # 新增代码+DurableTaskRegistry: 对终态或卡点任务只通知一次；若没有这行代码，同一任务会反复回灌模型。
        if self.command_queue is None:  # 新增代码+DurableTaskRegistry: 没有队列时跳过通知；若没有这行代码，测试或只读场景会因 None 崩溃。
            return  # 新增代码+DurableTaskRegistry: 无通知队列时正常结束；若没有这行代码，后续会访问 None。
        if record.notified:  # 新增代码+DurableTaskRegistry: 已通知过则跳过；若没有这行代码，同一任务每次保存都会通知。
            return  # 新增代码+DurableTaskRegistry: 保持幂等；若没有这行代码，重复通知会污染下一轮模型。
        payload = {"task_id": record.task_id, "status": record.status, "summary": record.output or record.error, "output_file": record.output_path, "usage": dict(usage)}  # 新增代码+DurableTaskRegistry: 构造通知 payload；若没有这行代码，主 agent 不知道任务 id、状态和输出文件。
        self.command_queue.enqueue_task_notification(payload)  # 新增代码+DurableTaskRegistry: 写入 runtime queue；若没有这行代码，后台任务结果无法自动回灌。
        record.notified = True  # 新增代码+DurableTaskRegistry: 标记已经通知；若没有这行代码，后续保存会重复通知。
