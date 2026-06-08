"""真实浏览器运行时的文件持久化 store。"""  # 新增代码+BrowserRuntimeStore: 说明本文件负责 browser run/action/observation/event 落盘；若没有这行代码，状态持久化边界不清楚。

from __future__ import annotations  # 新增代码+BrowserRuntimeStore: 延迟解析类型注解；若没有这行代码，返回自身类型时更容易受定义顺序影响。

import secrets  # 新增代码+BrowserRuntimeStore: 创建默认 browser_run_id 需要短随机后缀；若没有这行代码，调用方必须手写唯一 run id。
from pathlib import Path  # 新增代码+BrowserRuntimeStore: 用 Path 管理跨平台目录；若没有这行代码，Windows 路径拼接更脆弱。
from typing import Any  # 新增代码+BrowserRuntimeStore: 事件 payload 和 metadata 使用通用 JSON 类型；若没有这行代码，类型边界不清楚。

from learning_agent.browser.runtime_events import BROWSER_ACTION_RECORDED, BROWSER_OBSERVATION_RECORDED, BROWSER_RUN_CREATED  # 新增代码+BrowserRuntimeStore: 导入稳定事件名；若没有这行代码，事件字符串会散落。
from learning_agent.browser.runtime_models import BrowserAction, BrowserObservation, BrowserRun, now_ms  # 新增代码+BrowserRuntimeStore: 导入浏览器协议模型和时间 helper；若没有这行代码，store 无法保存统一对象。
from learning_agent.runtime.files import FileLock, append_jsonl, atomic_write_json, read_json_or_default, read_jsonl  # 新增代码+BrowserRuntimeStore: 复用项目现有原子写和 JSONL helper；若没有这行代码，store 会重复实现且更容易半写。


class BrowserRuntimeStore:  # 新增代码+BrowserRuntimeStore: 管理浏览器 runtime 的可恢复磁盘状态；若没有这个类，run/action/event 路径会散落在工具层。
    def __init__(self, base_dir: str | Path) -> None:  # 新增代码+BrowserRuntimeStore: 初始化 store 根目录；若没有这行代码，测试和生产无法指定不同存储位置。
        self.base_dir = Path(base_dir)  # 新增代码+BrowserRuntimeStore: 规范化根目录为 Path；若没有这行代码，后续路径拼接不稳定。
        self.runs_dir = self.base_dir / "runs"  # 新增代码+BrowserRuntimeStore: 定义 run 状态目录；若没有这行代码，run 文件会散落。
        self.actions_dir = self.base_dir / "actions"  # 新增代码+BrowserRuntimeStore: 定义动作状态目录；若没有这行代码，工具动作无法独立回放。
        self.observations_dir = self.base_dir / "observations"  # 新增代码+BrowserRuntimeStore: 定义页面观察目录；若没有这行代码，页面证据无法独立复验。
        self.events_dir = self.base_dir / "events"  # 新增代码+BrowserRuntimeStore: 定义事件 JSONL 目录；若没有这行代码，审计事件无法按 run 存放。
        self.lock_path = self.base_dir / "browser_runtime.lock"  # 新增代码+BrowserRuntimeStore: 定义跨进程写入锁；若没有这行代码，多 worker 可能互相覆盖状态。
        self.quarantine_dir = self.base_dir / "quarantine"  # 新增代码+BrowserRuntimeStore: 定义坏 JSON 隔离目录；若没有这行代码，半写文件会反复拖垮恢复。

    def run_path(self, run_id: str) -> Path:  # 新增代码+BrowserRuntimeStore: 计算 browser run JSON 路径；若没有这行代码，读写路径容易不一致。
        return self.runs_dir / f"{run_id}.json"  # 新增代码+BrowserRuntimeStore: 返回固定 run 文件路径；若没有这行代码，load_run 找不到保存结果。

    def action_path(self, action_id: str) -> Path:  # 新增代码+BrowserRuntimeStore: 计算 action JSON 路径；若没有这行代码，动作读写路径会散落。
        return self.actions_dir / f"{action_id}.json"  # 新增代码+BrowserRuntimeStore: 返回固定 action 文件路径；若没有这行代码，回放无法定位动作。

    def observation_path(self, observation_id: str) -> Path:  # 新增代码+BrowserRuntimeStore: 计算 observation JSON 路径；若没有这行代码，页面证据读写路径会散落。
        return self.observations_dir / f"{observation_id}.json"  # 新增代码+BrowserRuntimeStore: 返回固定 observation 文件路径；若没有这行代码，verifier 找不到证据。

    def event_path(self, run_id: str) -> Path:  # 新增代码+BrowserRuntimeStore: 计算 run 事件 JSONL 路径；若没有这行代码，事件写入和读取无法对齐。
        return self.events_dir / f"{run_id}.jsonl"  # 新增代码+BrowserRuntimeStore: 返回固定事件文件路径；若没有这行代码，审计日志难以定位。

    def create_run(self, run_id: str | None = None, session_id: str = "", prompt: str = "", metadata: dict[str, Any] | None = None) -> BrowserRun:  # 新增代码+BrowserRuntimeStore: 创建并落盘新的浏览器 run；若没有这行代码，真实浏览器任务不能自动创建 durable run。
        safe_run_id = run_id or f"browser_run_{secrets.token_hex(8)}"  # 新增代码+BrowserRuntimeStore: 没传 run_id 时生成唯一 id；若没有这行代码，调用方需要重复写 id 规则。
        browser_run = BrowserRun(run_id=safe_run_id, session_id=session_id, prompt=prompt, metadata=dict(metadata or {}))  # 新增代码+BrowserRuntimeStore: 构造 run 根对象；若没有这行代码，后续 action/observation 没有归属。
        self.save_run(browser_run, event_type=BROWSER_RUN_CREATED)  # 新增代码+BrowserRuntimeStore: 立刻保存 run 并写创建事件；若没有这行代码，中断后看不到任务入口。
        return browser_run  # 新增代码+BrowserRuntimeStore: 返回已落盘 run；若没有这行代码，调用方无法继续追加动作。

    def save_run(self, browser_run: BrowserRun, event_type: str | None = None) -> Path:  # 新增代码+BrowserRuntimeStore: 保存 run 状态到 JSON；若没有这行代码，浏览器任务状态只能留在内存。
        browser_run.updated_at_ms = now_ms()  # 新增代码+BrowserRuntimeStore: 每次保存刷新更新时间；若没有这行代码，状态页无法判断新旧。
        path = self.run_path(browser_run.run_id)  # 新增代码+BrowserRuntimeStore: 计算 run 文件路径；若没有这行代码，写入位置不稳定。
        with FileLock(self.lock_path):  # 新增代码+BrowserRuntimeStore: 加锁保护状态写入；若没有这行代码，多进程保存同一 run 可能互相覆盖。
            atomic_write_json(path, browser_run.to_dict())  # 新增代码+BrowserRuntimeStore: 使用原子写保存 run；若没有这行代码，崩溃可能留下半截 JSON。
        if event_type:  # 新增代码+BrowserRuntimeStore: 只有调用方要求时才写事件；若没有这行代码，内部更新会制造多余事件。
            self.append_event(browser_run.run_id, event_type, {"run": browser_run.to_dict()})  # 新增代码+BrowserRuntimeStore: 追加 run 级事件；若没有这行代码，harness event log 看不到状态变化。
        return path  # 新增代码+BrowserRuntimeStore: 返回保存路径作为证据；若没有这行代码，调用方无法记录落盘位置。

    def load_run(self, run_id: str) -> BrowserRun:  # 新增代码+BrowserRuntimeStore: 从磁盘读取 browser run；若没有这行代码，进程重启无法恢复任务。
        payload = read_json_or_default(self.run_path(run_id), None, quarantine_dir=self.quarantine_dir)  # 新增代码+BrowserRuntimeStore: 容错读取 run JSON 并隔离坏文件；若没有这行代码，半写文件会拖垮恢复。
        if not isinstance(payload, dict):  # 新增代码+BrowserRuntimeStore: 缺文件或坏根对象视为找不到；若没有这行代码，后续 from_dict 会拿到错误类型。
            raise FileNotFoundError(f"无法读取 browser run：{run_id}")  # 新增代码+BrowserRuntimeStore: 抛出明确错误；若没有这行代码，调用方难以知道哪个 run 缺失。
        payload.setdefault("run_id", run_id)  # 新增代码+BrowserRuntimeStore: 兼容旧文件缺 run_id 的情况；若没有这行代码，恢复后 id 可能为空。
        return BrowserRun.from_dict(payload)  # 新增代码+BrowserRuntimeStore: 返回稳定 run 对象；若没有这行代码，调用方只能处理松散 dict。

    def save_action(self, action: BrowserAction, event_type: str = BROWSER_ACTION_RECORDED) -> Path:  # 新增代码+BrowserRuntimeStore: 保存浏览器动作并追加事件；若没有这行代码，工具执行无法可审计。
        path = self.action_path(action.action_id)  # 新增代码+BrowserRuntimeStore: 计算 action 文件路径；若没有这行代码，动作落盘位置不稳定。
        with FileLock(self.lock_path):  # 新增代码+BrowserRuntimeStore: 加锁保护动作写入；若没有这行代码，多工具并发会互相覆盖。
            atomic_write_json(path, action.to_dict())  # 新增代码+BrowserRuntimeStore: 原子写动作 JSON；若没有这行代码，崩溃可能留下半截动作。
        self._attach_action_to_run(action)  # 新增代码+BrowserRuntimeStore: 把 action id 记录到 run；若没有这行代码，run/action 文件会断链。
        self.append_event(action.run_id, event_type, {"action": action.to_dict()})  # 新增代码+BrowserRuntimeStore: 追加动作事件；若没有这行代码，事件流看不到工具开始/完成。
        return path  # 新增代码+BrowserRuntimeStore: 返回保存路径；若没有这行代码，调用方无法记录动作证据位置。

    def load_action(self, action_id: str) -> BrowserAction:  # 新增代码+BrowserRuntimeStore: 从磁盘读取浏览器动作；若没有这行代码，回放无法重建动作序列。
        payload = read_json_or_default(self.action_path(action_id), None, quarantine_dir=self.quarantine_dir)  # 新增代码+BrowserRuntimeStore: 容错读取 action JSON；若没有这行代码，坏动作文件会拖垮回放。
        if not isinstance(payload, dict):  # 新增代码+BrowserRuntimeStore: 缺文件或坏根对象视为找不到；若没有这行代码，from_dict 会拿到错误类型。
            raise FileNotFoundError(f"无法读取 browser action：{action_id}")  # 新增代码+BrowserRuntimeStore: 抛出明确错误；若没有这行代码，用户不知道哪个动作缺失。
        payload.setdefault("action_id", action_id)  # 新增代码+BrowserRuntimeStore: 兼容旧文件缺 action_id 的情况；若没有这行代码，恢复后 id 可能为空。
        return BrowserAction.from_dict(payload)  # 新增代码+BrowserRuntimeStore: 返回稳定动作对象；若没有这行代码，调用方只能处理 dict。

    def save_observation(self, observation: BrowserObservation, event_type: str = BROWSER_OBSERVATION_RECORDED) -> Path:  # 新增代码+BrowserRuntimeStore: 保存页面观察并追加事件；若没有这行代码，页面证据无法复验。
        path = self.observation_path(observation.observation_id)  # 新增代码+BrowserRuntimeStore: 计算 observation 文件路径；若没有这行代码，页面证据落盘位置不稳定。
        with FileLock(self.lock_path):  # 新增代码+BrowserRuntimeStore: 加锁保护 observation 写入；若没有这行代码，多观察并发可能互相覆盖。
            atomic_write_json(path, observation.to_dict())  # 新增代码+BrowserRuntimeStore: 原子写页面观察 JSON；若没有这行代码，崩溃可能留下半截证据。
        self._attach_observation_to_run(observation)  # 新增代码+BrowserRuntimeStore: 把 observation id 记录到 run；若没有这行代码，run/页面证据会断链。
        self.append_event(observation.run_id, event_type, {"observation": observation.to_dict()})  # 新增代码+BrowserRuntimeStore: 追加 observation 事件；若没有这行代码，verifier 无法从事件流找到页面证据。
        return path  # 新增代码+BrowserRuntimeStore: 返回保存路径；若没有这行代码，调用方无法记录证据位置。

    def load_observation(self, observation_id: str) -> BrowserObservation:  # 新增代码+BrowserRuntimeStore: 从磁盘读取页面观察；若没有这行代码，验收器无法复验页面状态。
        payload = read_json_or_default(self.observation_path(observation_id), None, quarantine_dir=self.quarantine_dir)  # 新增代码+BrowserRuntimeStore: 容错读取 observation JSON；若没有这行代码，坏证据文件会拖垮验收。
        if not isinstance(payload, dict):  # 新增代码+BrowserRuntimeStore: 缺文件或坏根对象视为找不到；若没有这行代码，from_dict 会拿到错误类型。
            raise FileNotFoundError(f"无法读取 browser observation：{observation_id}")  # 新增代码+BrowserRuntimeStore: 抛出明确错误；若没有这行代码，用户不知道哪个观察缺失。
        payload.setdefault("observation_id", observation_id)  # 新增代码+BrowserRuntimeStore: 兼容旧文件缺 observation_id 的情况；若没有这行代码，恢复后 id 可能为空。
        return BrowserObservation.from_dict(payload)  # 新增代码+BrowserRuntimeStore: 返回稳定 observation 对象；若没有这行代码，调用方只能处理 dict。

    def append_event(self, run_id: str, event_type: str, payload: dict[str, Any] | None = None) -> Path:  # 新增代码+BrowserRuntimeStore: 追加一条浏览器 runtime JSONL 事件；若没有这行代码，状态变化无法复盘。
        row = {"timestamp_ms": now_ms(), "run_id": run_id, "event_type": event_type, "payload": dict(payload or {})}  # 新增代码+BrowserRuntimeStore: 构造标准事件行；若没有这行代码，事件字段会不统一。
        return append_jsonl(self.event_path(run_id), row)  # 新增代码+BrowserRuntimeStore: 追加 JSONL 并返回路径；若没有这行代码，事件不会落盘。

    def tail_events(self, run_id: str, limit: int = 20) -> list[dict[str, Any]]:  # 新增代码+BrowserRuntimeStore: 读取某个 run 的最近事件；若没有这行代码，CLI/API 无法展示浏览器时间线。
        events = read_jsonl(self.event_path(run_id))  # 新增代码+BrowserRuntimeStore: 读取完整事件列表并跳过坏行；若没有这行代码，事件查看会因单行损坏失败。
        if limit <= 0:  # 新增代码+BrowserRuntimeStore: limit 非正数时返回全部事件；若没有这行代码，调用方无法明确请求完整事件。
            return events  # 新增代码+BrowserRuntimeStore: 返回完整事件列表；若没有这行代码，limit<=0 没有语义。
        return events[-limit:]  # 新增代码+BrowserRuntimeStore: 返回最近 N 条事件；若没有这行代码，状态页可能输出过长日志。

    def list_run_ids(self) -> list[str]:  # 新增代码+BrowserRuntimeStore: 列出已有 browser run id；若没有这行代码，状态 CLI 无法发现历史任务。
        if not self.runs_dir.exists():  # 新增代码+BrowserRuntimeStore: 首次运行目录不存在时返回空列表；若没有这行代码，状态页会报 FileNotFoundError。
            return []  # 新增代码+BrowserRuntimeStore: 没有 run 时返回空列表；若没有这行代码，调用方要重复兜底。
        return sorted(path.stem for path in self.runs_dir.glob("*.json"))  # 新增代码+BrowserRuntimeStore: 按文件名稳定列出 run id；若没有这行代码，输出顺序不可预测。

    def _attach_action_to_run(self, action: BrowserAction) -> None:  # 新增代码+BrowserRuntimeStore: 内部 helper，把 action id 关联到 run；若没有这行代码，save_action 会重复写恢复逻辑。
        try:  # 新增代码+BrowserRuntimeStore: run 可能已被清理或尚未创建，需要容错；若没有这行代码，单个孤立 action 会让保存失败。
            browser_run = self.load_run(action.run_id)  # 新增代码+BrowserRuntimeStore: 读取所属 run；若没有这行代码，无法更新 action_ids。
        except FileNotFoundError:  # 新增代码+BrowserRuntimeStore: 找不到 run 时跳过关联；若没有这行代码，测试或迁移场景会直接失败。
            return  # 新增代码+BrowserRuntimeStore: 保留 action 文件本身；若没有这行代码，except 分支没有退出语义。
        browser_run.add_action(action.action_id)  # 新增代码+BrowserRuntimeStore: 把 action id 挂到 run；若没有这行代码，run 和 action 文件断链。
        self.save_run(browser_run)  # 新增代码+BrowserRuntimeStore: 保存更新后的 run 但不追加多余事件；若没有这行代码，关联关系不会落盘。

    def _attach_observation_to_run(self, observation: BrowserObservation) -> None:  # 新增代码+BrowserRuntimeStore: 内部 helper，把 observation id 关联到 run；若没有这行代码，save_observation 会重复写恢复逻辑。
        try:  # 新增代码+BrowserRuntimeStore: run 可能已被清理或尚未创建，需要容错；若没有这行代码，孤立 observation 会让保存失败。
            browser_run = self.load_run(observation.run_id)  # 新增代码+BrowserRuntimeStore: 读取所属 run；若没有这行代码，无法更新 observation_ids。
        except FileNotFoundError:  # 新增代码+BrowserRuntimeStore: 找不到 run 时跳过关联；若没有这行代码，迁移数据会直接失败。
            return  # 新增代码+BrowserRuntimeStore: 保留 observation 文件本身；若没有这行代码，except 分支没有退出语义。
        browser_run.add_observation(observation.observation_id)  # 新增代码+BrowserRuntimeStore: 把 observation id 挂到 run；若没有这行代码，run 和页面证据断链。
        self.save_run(browser_run)  # 新增代码+BrowserRuntimeStore: 保存更新后的 run 但不追加多余事件；若没有这行代码，关联关系不会落盘。
