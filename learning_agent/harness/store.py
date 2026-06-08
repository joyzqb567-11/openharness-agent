"""长任务 harness 的文件持久化 store。"""  # 新增代码+LongTaskHarness: 说明本文件负责状态和事件落盘；若没有这行代码，store 职责不清楚。

from __future__ import annotations  # 新增代码+LongTaskHarness: 延迟解析类型注解；若没有这行代码，类型引用更容易受顺序影响。

import json  # 新增代码+LongTaskHarness: 读写 JSON 状态和 JSONL 事件；若没有这行代码，harness 无法持久化。
from pathlib import Path  # 新增代码+LongTaskHarness: 用 Path 管理存储路径；若没有这行代码，路径拼接会更脆弱。
from typing import Any  # 新增代码+LongTaskHarness: 事件 payload 需要通用 JSON 类型；若没有这行代码，类型边界不清楚。

from learning_agent.harness.models import HarnessRun, utc_timestamp  # 新增代码+LongTaskHarness: 导入 run 模型和时间 helper；若没有这行代码，store 不能保存统一对象。
from learning_agent.runtime.files import FileLock, append_jsonl, atomic_write_json, read_json_or_default, read_jsonl  # 新增代码+RuntimeFileSafety: 复用锁、原子写和坏 JSON 隔离 helper；若没有这行代码，harness store 会继续有半写风险。


class HarnessStore:  # 新增代码+LongTaskHarness: 管理 harness 持久化目录；若没有这个类，状态文件路径会散落在各处。
    def __init__(self, base_dir: str | Path) -> None:  # 新增代码+LongTaskHarness: 初始化 store 根目录；若没有这行代码，调用方无法指定测试或生产存储位置。
        self.base_dir = Path(base_dir)  # 新增代码+LongTaskHarness: 规范化根目录为 Path；若没有这行代码，后续路径操作不稳定。
        self.runs_dir = self.base_dir / "runs"  # 新增代码+LongTaskHarness: 定义 run 状态目录；若没有这行代码，多个 run 文件会散落。
        self.events_dir = self.base_dir / "events"  # 新增代码+LongTaskHarness: 定义事件日志目录；若没有这行代码，状态和事件无法分层保存。
        self.lock_path = self.base_dir / "store.lock"  # 新增代码+RuntimeFileSafety: 定义 store 写入锁；若没有这行代码，多 worker 保存 run 可能互相覆盖。
        self.quarantine_dir = self.base_dir / "quarantine"  # 新增代码+RuntimeFileSafety: 定义坏 JSON 隔离目录；若没有这行代码，半写状态会反复拖垮恢复。

    def run_path(self, run_id: str) -> Path:  # 新增代码+LongTaskHarness: 计算 run JSON 路径；若没有这行代码，读写路径容易不一致。
        return self.runs_dir / f"{run_id}.json"  # 新增代码+LongTaskHarness: 返回固定 run 文件；若没有这行代码，resume 找不到状态文件。

    def event_path(self, run_id: str) -> Path:  # 新增代码+LongTaskHarness: 计算事件 JSONL 路径；若没有这行代码，事件回放入口不稳定。
        return self.events_dir / f"{run_id}.jsonl"  # 新增代码+LongTaskHarness: 返回固定事件文件；若没有这行代码，审计证据无法定位。

    def save_run(self, run: HarnessRun) -> Path:  # 新增代码+LongTaskHarness: 保存 run 状态到 JSON；若没有这行代码，任务状态只能留在内存。
        run.updated_at = utc_timestamp()  # 新增代码+LongTaskHarness: 每次保存刷新更新时间；若没有这行代码，状态页无法判断新旧。
        path = self.run_path(run.run_id)  # 新增代码+LongTaskHarness: 计算目标路径；若没有这行代码，无法写到固定文件。
        with FileLock(self.lock_path):  # 新增代码+RuntimeFileSafety: 加锁保护 run 状态写入；若没有这行代码，多 worker 可能同时保存同一任务。
            atomic_write_json(path, run.to_dict())  # 修改代码+RuntimeFileSafety: 用临时文件加 replace 原子写 JSON；若没有这行代码，崩溃可能留下半截状态。
        return path  # 新增代码+LongTaskHarness: 返回保存路径；若没有这行代码，调用方无法记录证据位置。

    def load_run(self, run_id: str) -> HarnessRun:  # 新增代码+LongTaskHarness: 从 JSON 读取 run 状态；若没有这行代码，重启后无法恢复任务。
        run = self.try_load_run(run_id)  # 新增代码+RuntimeFileSafety: 通过容错入口读取 run；若没有这行代码，坏 JSON 会直接抛出并拖垮调用方。
        if run is None:  # 新增代码+RuntimeFileSafety: 如果 run 不存在或已被隔离；若没有这行代码，调用方会拿到空对象。
            raise FileNotFoundError(f"无法读取 harness run：{run_id}")  # 新增代码+RuntimeFileSafety: 明确报告读取失败；若没有这行代码，状态页会显示空 run。
        return run  # 新增代码+RuntimeFileSafety: 返回成功读取的 run；若没有这行代码，load_run 无返回。

    def try_load_run(self, run_id: str) -> HarnessRun | None:  # 新增代码+RuntimeFileSafety: 尝试读取 run，坏 JSON 返回 None 并隔离；若没有这行代码，队列无法跳过坏任务。
        payload = read_json_or_default(self.run_path(run_id), None, quarantine_dir=self.quarantine_dir)  # 新增代码+RuntimeFileSafety: 容错读取 JSON 并隔离坏文件；若没有这行代码，半写状态会抛 JSONDecodeError。
        if not isinstance(payload, dict):  # 新增代码+RuntimeFileSafety: 非 dict 或缺文件视为不可恢复；若没有这行代码，坏根对象会污染 run。
            return None  # 新增代码+RuntimeFileSafety: 返回 None 让队列跳过；若没有这行代码，坏状态仍会进入 runner。
        payload.setdefault("run_id", run_id)  # 新增代码+RuntimeFileSafety: 确保 run_id 不因旧文件缺字段而为空；若没有这行代码，恢复后事件和状态无法定位。
        return HarnessRun.from_dict(payload)  # 新增代码+RuntimeFileSafety: 返回稳定 run 对象；若没有这行代码，调用方要处理松散 dict。

    def list_run_ids(self) -> list[str]:  # 新增代码+LongTaskHarness: 列出所有 run id；若没有这行代码，队列无法扫描待执行任务。
        if not self.runs_dir.exists():  # 新增代码+LongTaskHarness: 目录不存在时返回空列表；若没有这行代码，首次运行会报 FileNotFoundError。
            return []  # 新增代码+LongTaskHarness: 没有任务时返回空列表；若没有这行代码，队列扫描需要自己兜底。
        return sorted(path.stem for path in self.runs_dir.glob("*.json"))  # 新增代码+LongTaskHarness: 按文件名稳定列出 run；若没有这行代码，队列顺序不可预测。

    def append_event(self, run_id: str, event_type: str, payload: dict[str, Any] | None = None) -> Path:  # 新增代码+LongTaskHarness: 追加一条审计事件；若没有这行代码，状态变化无法复盘。
        path = self.event_path(run_id)  # 新增代码+LongTaskHarness: 计算事件日志路径；若没有这行代码，事件写入位置不稳定。
        path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+LongTaskHarness: 确保事件目录存在；若没有这行代码，首次事件写入会失败。
        row = {"timestamp": utc_timestamp(), "run_id": run_id, "event_type": event_type, "payload": payload or {}}  # 新增代码+LongTaskHarness: 构造标准事件行；若没有这行代码，JSONL 字段会不统一。
        append_jsonl(path, row)  # 修改代码+RuntimeFileSafety: 统一追加完整 JSONL 行；若没有这行代码，事件写入格式和容错规则会分叉。
        return path  # 新增代码+LongTaskHarness: 返回事件文件路径；若没有这行代码，调用方无法记录证据位置。

    def read_events(self, run_id: str) -> list[dict[str, Any]]:  # 新增代码+LongTaskHarness: 读取某个 run 的事件列表；若没有这行代码，状态页无法显示最近事件。
        path = self.event_path(run_id)  # 新增代码+LongTaskHarness: 定位事件日志；若没有这行代码，读取路径可能和写入路径不一致。
        if not path.exists():  # 新增代码+LongTaskHarness: 没有事件文件时返回空列表；若没有这行代码，新任务状态渲染会报错。
            return []  # 新增代码+LongTaskHarness: 返回空事件列表；若没有这行代码，调用方要重复处理缺文件。
        return read_jsonl(path)  # 修改代码+RuntimeFileSafety: 复用容错 JSONL 读取；若没有这行代码，坏事件行会拖垮状态读取。
