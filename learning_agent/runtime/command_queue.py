"""持久化运行时命令队列，对齐 ClaudeCode messageQueueManager。"""  # 新增代码+RuntimeCommandQueue: 说明本文件处理用户 prompt、任务通知和恢复命令；若没有这行代码，主循环队列边界不清楚。

from __future__ import annotations  # 新增代码+RuntimeCommandQueue: 延迟解析类型注解；若没有这行代码，类方法返回自身类型时更容易受顺序影响。

import secrets  # 新增代码+RuntimeCommandQueue: 生成 command_id 需要随机后缀；若没有这行代码，多命令可能 id 冲突。
from dataclasses import dataclass, field  # 新增代码+RuntimeCommandQueue: 用 dataclass 定义命令对象；若没有这行代码，命令字段会散成松散 dict。
from pathlib import Path  # 新增代码+RuntimeCommandQueue: 用 Path 管理队列目录；若没有这行代码，Windows 路径处理更脆弱。
from typing import Any  # 新增代码+RuntimeCommandQueue: 命令 payload 是通用 JSON；若没有这行代码，类型边界不清楚。

from learning_agent.harness.models import utc_timestamp  # 新增代码+RuntimeCommandQueue: 复用统一 UTC 时间戳；若没有这行代码，事件时间格式会不一致。
from learning_agent.runtime.files import FileLock, append_jsonl, atomic_write_json, read_json_or_default, read_jsonl  # 新增代码+RuntimeCommandQueue: 导入锁、原子写和 JSONL helper；若没有这行代码，队列会缺少崩溃安全。


PRIORITY_ORDER = {"now": 0, "next": 1, "later": 2}  # 新增代码+RuntimeCommandQueue: 定义命令优先级顺序；若没有这行代码，用户 prompt 和通知可能乱序。


@dataclass  # 新增代码+RuntimeCommandQueue: 自动生成 RuntimeCommand 初始化方法；若没有这行代码，命令对象要手写构造器。
class RuntimeCommand:  # 新增代码+RuntimeCommandQueue: 表示一条可持久化的运行时命令；若没有这个类，队列只能处理不透明 dict。
    command_id: str  # 新增代码+RuntimeCommandQueue: 保存命令唯一 id；若没有这行代码，ack/started/completed 无法定位命令。
    mode: str  # 新增代码+RuntimeCommandQueue: 保存 prompt/task_notification/resume_interrupted 等类型；若没有这行代码，主循环不知道如何处理命令。
    priority: str  # 新增代码+RuntimeCommandQueue: 保存 now/next/later 优先级；若没有这行代码，任务通知可能压过用户输入。
    payload: dict[str, Any] = field(default_factory=dict)  # 新增代码+RuntimeCommandQueue: 保存命令正文；若没有这行代码，prompt 文本和 task_id 会丢失。
    status: str = "queued"  # 新增代码+RuntimeCommandQueue: 保存 queued/started/completed 状态；若没有这行代码，重启后无法区分已处理命令。
    created_at: str = field(default_factory=utc_timestamp)  # 新增代码+RuntimeCommandQueue: 保存创建时间；若没有这行代码，队列审计缺少时间线。
    updated_at: str = field(default_factory=utc_timestamp)  # 新增代码+RuntimeCommandQueue: 保存更新时间；若没有这行代码，状态页无法判断命令新旧。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+RuntimeCommandQueue: 把命令转成 JSON dict；若没有这行代码，队列无法稳定落盘。
        return {"command_id": self.command_id, "mode": self.mode, "priority": self.priority, "payload": dict(self.payload), "status": self.status, "created_at": self.created_at, "updated_at": self.updated_at}  # 新增代码+RuntimeCommandQueue: 返回完整字段副本；若没有这行代码，恢复时会丢字段。

    @classmethod  # 新增代码+RuntimeCommandQueue: 提供从 JSON dict 恢复命令的入口；若没有这行代码，队列读取会拿到松散 dict。
    def from_dict(cls, payload: dict[str, Any]) -> "RuntimeCommand":  # 新增代码+RuntimeCommandQueue: 从持久化字段恢复命令对象；若没有这行代码，重启恢复无法类型化命令。
        raw_payload = payload.get("payload", {})  # 新增代码+RuntimeCommandQueue: 读取命令载荷字段；若没有这行代码，payload 缺失会抛错。
        safe_payload = raw_payload if isinstance(raw_payload, dict) else {}  # 新增代码+RuntimeCommandQueue: 非 dict payload 时回退空对象；若没有这行代码，坏文件会污染运行时。
        return cls(command_id=str(payload.get("command_id", "")), mode=str(payload.get("mode", "")), priority=str(payload.get("priority", "later")), payload=safe_payload, status=str(payload.get("status", "queued")), created_at=str(payload.get("created_at", "")), updated_at=str(payload.get("updated_at", "")))  # 新增代码+RuntimeCommandQueue: 返回稳定命令对象；若没有这行代码，队列无法跨进程恢复。


class RuntimeCommandQueue:  # 新增代码+RuntimeCommandQueue: 管理持久化运行时命令；若没有这个类，主循环无法统一处理 prompt 和 task notification。
    def __init__(self, base_dir: str | Path) -> None:  # 新增代码+RuntimeCommandQueue: 初始化队列目录；若没有这行代码，调用方无法指定测试或生产存储。
        self.base_dir = Path(base_dir)  # 新增代码+RuntimeCommandQueue: 规范化队列根目录；若没有这行代码，路径操作不稳定。
        self.commands_path = self.base_dir / "commands.json"  # 新增代码+RuntimeCommandQueue: 定义命令状态文件；若没有这行代码，重启后找不到队列。
        self.events_path = self.base_dir / "events.jsonl"  # 新增代码+RuntimeCommandQueue: 定义命令事件日志；若没有这行代码，命令生命周期不可审计。
        self.lock_path = self.base_dir / "commands.lock"  # 新增代码+RuntimeCommandQueue: 定义队列锁文件；若没有这行代码，多 worker 会并发改队列。
        self.quarantine_dir = self.base_dir / "quarantine"  # 新增代码+RuntimeCommandQueue: 定义坏状态隔离目录；若没有这行代码，半写文件会反复拖垮启动。

    def enqueue_prompt(self, text: str, priority: str = "next") -> RuntimeCommand:  # 新增代码+RuntimeCommandQueue: 把用户 prompt 写入队列；若没有这行代码，真实输入不能 durable 排队。
        return self._enqueue_or_merge_prompt(str(text), priority=priority)  # 新增代码+RuntimeCommandQueue: 委托合并逻辑处理 prompt；若没有这行代码，多 prompt 无法批处理。

    def enqueue_task_notification(self, payload: dict[str, Any], priority: str = "later") -> RuntimeCommand:  # 新增代码+RuntimeCommandQueue: 把任务通知写入队列；若没有这行代码，后台任务无法自动回灌主 agent。
        return self.enqueue(mode="task_notification", payload=payload, priority=priority)  # 新增代码+RuntimeCommandQueue: 复用通用入队逻辑；若没有这行代码，通知入队会重复实现。

    def enqueue_resume_interrupted(self, payload: dict[str, Any]) -> RuntimeCommand:  # 新增代码+RuntimeCommandQueue: 把中断恢复命令写入队列；若没有这行代码，崩溃恢复无法进入主循环。
        return self.enqueue(mode="resume_interrupted", payload=payload, priority="now")  # 新增代码+RuntimeCommandQueue: 恢复命令使用最高优先级；若没有这行代码，恢复可能被普通通知饿死。

    def enqueue(self, mode: str, payload: dict[str, Any] | None = None, priority: str = "later") -> RuntimeCommand:  # 新增代码+RuntimeCommandQueue: 通用命令入队入口；若没有这行代码，各命令类型会重复写文件。
        safe_priority = priority if priority in PRIORITY_ORDER else "later"  # 新增代码+RuntimeCommandQueue: 非法优先级回退 later；若没有这行代码，坏输入会破坏排序。
        command = RuntimeCommand(command_id=f"cmd_{secrets.token_hex(8)}", mode=str(mode), priority=safe_priority, payload=dict(payload or {}))  # 新增代码+RuntimeCommandQueue: 创建新命令对象；若没有这行代码，命令没有稳定 id。
        with FileLock(self.lock_path):  # 新增代码+RuntimeCommandQueue: 加锁保护读改写；若没有这行代码，并发入队可能互相覆盖。
            commands = self._load_commands_unlocked()  # 新增代码+RuntimeCommandQueue: 读取当前队列；若没有这行代码，新命令会覆盖旧命令。
            commands.append(command)  # 新增代码+RuntimeCommandQueue: 追加新命令；若没有这行代码，入队不会保存。
            self._save_commands_unlocked(commands)  # 新增代码+RuntimeCommandQueue: 原子保存队列；若没有这行代码，命令只存在内存。
        self._append_event("command_queued", command, {"priority": safe_priority})  # 新增代码+RuntimeCommandQueue: 记录入队事件；若没有这行代码，审计不知道命令何时进入。
        return command  # 新增代码+RuntimeCommandQueue: 返回命令给调用方；若没有这行代码，调用方拿不到 command_id。

    def _enqueue_or_merge_prompt(self, text: str, priority: str) -> RuntimeCommand:  # 新增代码+RuntimeCommandQueue: 合并未处理 prompt；若没有这行代码，多条用户输入会变成多轮零散请求。
        safe_priority = priority if priority in PRIORITY_ORDER else "next"  # 新增代码+RuntimeCommandQueue: 校验 prompt 优先级；若没有这行代码，坏输入会破坏队列排序。
        with FileLock(self.lock_path):  # 新增代码+RuntimeCommandQueue: 合并过程必须加锁；若没有这行代码，并发 prompt 可能丢失。
            commands = self._load_commands_unlocked()  # 新增代码+RuntimeCommandQueue: 读取已有命令；若没有这行代码，无法找到可合并 prompt。
            existing = next((command for command in commands if command.mode == "prompt" and command.status == "queued"), None)  # 新增代码+RuntimeCommandQueue: 找到尚未消费的 prompt；若没有这行代码，prompt 无法批量合并。
            if existing is not None:  # 新增代码+RuntimeCommandQueue: 如果已有 queued prompt；若没有这行代码，下面会误创建重复命令。
                previous_text = str(existing.payload.get("text", ""))  # 新增代码+RuntimeCommandQueue: 读取旧 prompt 文本；若没有这行代码，合并时会丢旧输入。
                existing.payload["text"] = (previous_text + "\n" + text).strip()  # 新增代码+RuntimeCommandQueue: 把新 prompt 接到旧 prompt 后面；若没有这行代码，用户后续输入会丢失。
                existing.priority = safe_priority  # 新增代码+RuntimeCommandQueue: 保持 prompt 当前优先级；若没有这行代码，优先级可能停留旧值。
                existing.updated_at = utc_timestamp()  # 新增代码+RuntimeCommandQueue: 刷新更新时间；若没有这行代码，状态页不知道 prompt 已追加。
                self._save_commands_unlocked(commands)  # 新增代码+RuntimeCommandQueue: 保存合并后的队列；若没有这行代码，合并只在内存中。
                command = existing  # 新增代码+RuntimeCommandQueue: 让后续事件使用已有命令 id；若没有这行代码，函数返回对象不明确。
            else:  # 新增代码+RuntimeCommandQueue: 没有 queued prompt 时创建新命令；若没有这行代码，首次 prompt 无法入队。
                command = RuntimeCommand(command_id=f"cmd_{secrets.token_hex(8)}", mode="prompt", priority=safe_priority, payload={"text": text})  # 新增代码+RuntimeCommandQueue: 创建 prompt 命令；若没有这行代码，用户输入没有 durable 对象。
                commands.append(command)  # 新增代码+RuntimeCommandQueue: 把 prompt 加入队列；若没有这行代码，状态文件不会包含它。
                self._save_commands_unlocked(commands)  # 新增代码+RuntimeCommandQueue: 保存新队列；若没有这行代码，prompt 重启后会丢失。
        self._append_event("command_queued", command, {"priority": safe_priority, "merged": existing is not None})  # 新增代码+RuntimeCommandQueue: 记录 prompt 入队或合并事件；若没有这行代码，审计看不到合并行为。
        return command  # 新增代码+RuntimeCommandQueue: 返回 prompt 命令；若没有这行代码，调用方拿不到 command_id。

    def dequeue_next(self) -> RuntimeCommand | None:  # 新增代码+RuntimeCommandQueue: 取出下一条应处理命令并标记 started；若没有这行代码，主循环无法消费队列。
        with FileLock(self.lock_path):  # 新增代码+RuntimeCommandQueue: 消费队列必须加锁；若没有这行代码，两个 worker 可能拿到同一命令。
            commands = self._load_commands_unlocked()  # 新增代码+RuntimeCommandQueue: 读取当前命令列表；若没有这行代码，无法选择下一条。
            queued = [command for command in commands if command.status == "queued"]  # 新增代码+RuntimeCommandQueue: 只考虑未开始命令；若没有这行代码，已完成命令会重复执行。
            if not queued:  # 新增代码+RuntimeCommandQueue: 队列为空时返回 None；若没有这行代码，后续会访问空列表。
                return None  # 新增代码+RuntimeCommandQueue: 没有命令可处理；若没有这行代码，调用方无法区分空队列。
            queued.sort(key=lambda command: (PRIORITY_ORDER.get(command.priority, 99), command.created_at))  # 新增代码+RuntimeCommandQueue: 按优先级和时间排序；若没有这行代码，用户 prompt 和通知顺序不稳定。
            selected = queued[0]  # 新增代码+RuntimeCommandQueue: 取最高优先级最早命令；若没有这行代码，无法确定处理对象。
            selected.status = "started"  # 新增代码+RuntimeCommandQueue: 标记命令已开始；若没有这行代码，重启后可能重复消费。
            selected.updated_at = utc_timestamp()  # 新增代码+RuntimeCommandQueue: 刷新更新时间；若没有这行代码，状态页不知道命令何时开始。
            self._save_commands_unlocked(commands)  # 新增代码+RuntimeCommandQueue: 保存 started 状态；若没有这行代码，多 worker 仍会看到 queued。
        self._append_event("command_started", selected, {})  # 新增代码+RuntimeCommandQueue: 记录开始事件；若没有这行代码，命令生命周期缺少 started。
        return selected  # 新增代码+RuntimeCommandQueue: 返回选中的命令；若没有这行代码，主循环无法处理命令。

    def ack(self, command_id: str) -> RuntimeCommand | None:  # 新增代码+RuntimeCommandQueue: 记录命令已被上层确认收到；若没有这行代码，UI 无法区分 started 和 ack。
        return self._mark(command_id, "acked", "command_acked")  # 新增代码+RuntimeCommandQueue: 复用状态标记 helper；若没有这行代码，ack 会重复实现读写。

    def mark_started(self, command_id: str) -> RuntimeCommand | None:  # 新增代码+RuntimeCommandQueue: 显式标记命令开始；若没有这行代码，外部 runner 无法补写 started。
        return self._mark(command_id, "started", "command_started")  # 新增代码+RuntimeCommandQueue: 复用通用状态标记；若没有这行代码，状态更新规则会分叉。

    def mark_completed(self, command_id: str) -> RuntimeCommand | None:  # 新增代码+RuntimeCommandQueue: 标记命令完成；若没有这行代码，队列无法收束处理过的命令。
        return self._mark(command_id, "completed", "command_completed")  # 新增代码+RuntimeCommandQueue: 复用状态标记 helper；若没有这行代码，completed 事件不会统一写入。

    def list_commands(self) -> list[RuntimeCommand]:  # 新增代码+RuntimeCommandQueue: 列出全部命令对象；若没有这行代码，CLI 无法展示队列状态。
        with FileLock(self.lock_path):  # 新增代码+RuntimeCommandQueue: 读取也加锁避免半读；若没有这行代码，可能读到写入中状态。
            return self._load_commands_unlocked()  # 新增代码+RuntimeCommandQueue: 返回恢复后的命令对象；若没有这行代码，调用方拿不到队列。

    def read_events(self) -> list[dict[str, Any]]:  # 新增代码+RuntimeCommandQueue: 读取命令事件日志；若没有这行代码，测试和 CLI 无法审计命令生命周期。
        return read_jsonl(self.events_path)  # 新增代码+RuntimeCommandQueue: 委托 JSONL helper 容错读取；若没有这行代码，坏事件行会拖垮状态页。

    def _mark(self, command_id: str, status: str, event_type: str) -> RuntimeCommand | None:  # 新增代码+RuntimeCommandQueue: 更新命令状态并记录事件；若没有这行代码，ack/start/complete 会重复代码。
        changed: RuntimeCommand | None = None  # 新增代码+RuntimeCommandQueue: 保存被修改命令；若没有这行代码，with 外无法记录事件。
        with FileLock(self.lock_path):  # 新增代码+RuntimeCommandQueue: 状态修改必须加锁；若没有这行代码，并发 complete 可能覆盖状态。
            commands = self._load_commands_unlocked()  # 新增代码+RuntimeCommandQueue: 读取队列；若没有这行代码，无法定位目标命令。
            for command in commands:  # 新增代码+RuntimeCommandQueue: 遍历所有命令寻找 id；若没有这行代码，状态无法更新。
                if command.command_id != command_id:  # 新增代码+RuntimeCommandQueue: 跳过非目标命令；若没有这行代码，可能改错命令。
                    continue  # 新增代码+RuntimeCommandQueue: 继续找目标；若没有这行代码，非目标分支会继续执行。
                command.status = status  # 新增代码+RuntimeCommandQueue: 写入新状态；若没有这行代码，命令生命周期不会推进。
                command.updated_at = utc_timestamp()  # 新增代码+RuntimeCommandQueue: 更新时间；若没有这行代码，审计无法看到状态何时变化。
                changed = command  # 新增代码+RuntimeCommandQueue: 保存修改对象供事件使用；若没有这行代码，with 外不知道改了谁。
                break  # 新增代码+RuntimeCommandQueue: 找到后退出循环；若没有这行代码，会继续无意义扫描。
            if changed is not None:  # 新增代码+RuntimeCommandQueue: 只有找到命令才保存；若没有这行代码，未知 id 也会重写文件。
                self._save_commands_unlocked(commands)  # 新增代码+RuntimeCommandQueue: 保存更新后的队列；若没有这行代码，状态变更不落盘。
        if changed is not None:  # 新增代码+RuntimeCommandQueue: 找到命令后记录事件；若没有这行代码，未知 id 会产生假事件。
            self._append_event(event_type, changed, {})  # 新增代码+RuntimeCommandQueue: 追加生命周期事件；若没有这行代码，状态变化不可审计。
        return changed  # 新增代码+RuntimeCommandQueue: 返回被修改命令或 None；若没有这行代码，调用方不知道是否成功。

    def _load_commands_unlocked(self) -> list[RuntimeCommand]:  # 新增代码+RuntimeCommandQueue: 在外层持锁时读取命令列表；若没有这行代码，读写逻辑会重复。
        payload = read_json_or_default(self.commands_path, {"commands": []}, quarantine_dir=self.quarantine_dir)  # 新增代码+RuntimeCommandQueue: 容错读取命令 JSON；若没有这行代码，坏文件会中断启动。
        raw_commands = payload.get("commands", []) if isinstance(payload, dict) else []  # 新增代码+RuntimeCommandQueue: 提取 commands 数组；若没有这行代码，坏根对象会触发属性错误。
        return [RuntimeCommand.from_dict(item) for item in raw_commands if isinstance(item, dict)]  # 新增代码+RuntimeCommandQueue: 恢复所有合法命令；若没有这行代码，队列只能返回原始 dict。

    def _save_commands_unlocked(self, commands: list[RuntimeCommand]) -> Path:  # 新增代码+RuntimeCommandQueue: 在外层持锁时保存命令列表；若没有这行代码，各方法会重复 dumps。
        payload = {"commands": [command.to_dict() for command in commands]}  # 新增代码+RuntimeCommandQueue: 构造稳定 JSON 根对象；若没有这行代码，文件结构不固定。
        return atomic_write_json(self.commands_path, payload)  # 新增代码+RuntimeCommandQueue: 原子写入命令状态；若没有这行代码，崩溃可能留下半写 JSON。

    def _append_event(self, event_type: str, command: RuntimeCommand, payload: dict[str, Any]) -> Path:  # 新增代码+RuntimeCommandQueue: 追加命令事件；若没有这行代码，事件字段会散落。
        row = {"timestamp": utc_timestamp(), "event_type": event_type, "command_id": command.command_id, "mode": command.mode, "priority": command.priority, "status": command.status, "payload": dict(payload)}  # 新增代码+RuntimeCommandQueue: 构造标准事件行；若没有这行代码，事件审计字段不统一。
        return append_jsonl(self.events_path, row)  # 新增代码+RuntimeCommandQueue: 写入 JSONL 事件；若没有这行代码，事件不会落盘。
