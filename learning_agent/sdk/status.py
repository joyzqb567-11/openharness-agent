"""状态 SDK，供 Codex、ClaudeCode 或其他 agent 读取 learning_agent 当前状态。"""  # 新增代码+StatusSDK: 说明本模块是外部 agent 的稳定状态入口；若没有这行代码，调用方会去读内部 JSON 文件。

from __future__ import annotations  # 新增代码+StatusSDK: 延迟解析类型注解；若没有这行代码，生成器类型更容易受定义顺序影响。

import time  # 新增代码+StatusSDK: watch 轮询需要睡眠；若没有这行代码，事件订阅会忙等消耗 CPU。
from collections.abc import Iterator  # 新增代码+StatusSDK: 标注 watch 生成器返回类型；若没有这行代码，SDK 类型边界不清楚。
from pathlib import Path  # 新增代码+StatusSDK: 允许调用方传字符串或 Path；若没有这行代码，路径处理不稳定。
from typing import Any  # 新增代码+StatusSDK: 快照和事件是通用 JSON；若没有这行代码，类型边界不清楚。

from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserStatusStage11: SDK 读取浏览器 runtime 事件；若没有这行代码，外部 agent 只能解析内部文件。
from learning_agent.core.resume_loader import ResumeLoader  # 新增代码+StatusSDKV2: 复用真实恢复加载器读取 resume 报告；若没有这行代码，SDK 只能给出粗略 session 列表。
from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+StatusSDK: 读取状态事件 store；若没有这行代码，SDK 无法列事件。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+StatusSDK: 复用统一快照聚合器；若没有这行代码，SDK 会和 CLI 状态分叉。


def get_status_snapshot(workspace: str | Path) -> dict[str, Any]:  # 新增代码+StatusSDK: 获取一次完整状态快照；若没有这行代码，外部 agent 只能手动读多个文件。
    return build_status_snapshot(Path(workspace))  # 新增代码+StatusSDK: 委托统一聚合器；若没有这行代码，SDK 可能读出和终端不同的状态。


def get_runs(workspace: str | Path) -> list[dict[str, Any]]:  # 新增代码+StatusSDKV2: 返回 harness run 列表；若没有这行代码，外部 agent 只能解析完整快照。
    snapshot = get_status_snapshot(workspace)  # 新增代码+StatusSDKV2: 读取统一快照作为唯一事实源；若没有这行代码，run 列表可能和 /status 不一致。
    return list(snapshot.get("runs", [])) if isinstance(snapshot.get("runs", []), list) else []  # 新增代码+StatusSDKV2: 只返回列表格式的 runs；若没有这行代码，坏数据会传给调用方。


def get_sessions(workspace: str | Path) -> list[Any]:  # 新增代码+StatusSDKV2: 返回可恢复 session 列表；若没有这行代码，外部 agent 不知道有哪些会话可审计。
    snapshot = get_status_snapshot(workspace)  # 新增代码+StatusSDKV2: 复用统一快照读取 sessions；若没有这行代码，SDK 会形成第二套 session 读取逻辑。
    return list(snapshot.get("sessions", [])) if isinstance(snapshot.get("sessions", []), list) else []  # 新增代码+StatusSDKV2: 保护 sessions 类型；若没有这行代码，异常数据会破坏控制端。


def get_health(workspace: str | Path) -> dict[str, Any]:  # 新增代码+StatusSDKV2: 返回状态生态健康块；若没有这行代码，外部 agent 难以判断是否需要人工处理。
    snapshot = get_status_snapshot(workspace)  # 新增代码+StatusSDKV2: 读取统一快照；若没有这行代码，health 可能和终端显示不同。
    health = snapshot.get("health", {})  # 新增代码+StatusSDKV2: 提取健康区块；若没有这行代码，调用方需要知道内部字段位置。
    if not isinstance(health, dict):  # 新增代码+StatusSDKV2: 检查 health 是否为对象；若没有这行代码，坏数据会继续向外扩散。
        return {"state": "unknown", "warnings": ["health 字段格式异常"]}  # 新增代码+StatusSDKV2: 坏数据降级为明确警告；若没有这行代码，控制端会拿到不可预测类型。
    normalized_health = dict(health)  # 新增代码+StatusSDKV2: 复制健康块避免修改快照原对象；若没有这行代码，SDK 可能污染上层缓存。
    warnings = normalized_health.get("warnings", [])  # 新增代码+StatusSDKV2: 读取 warning 列表用于推断状态；若没有这行代码，state 无法稳定生成。
    normalized_health.setdefault("state", "warning" if warnings else "ok")  # 新增代码+StatusSDKV2: 补齐稳定 state 字段；若没有这行代码，外部 agent 要自己猜健康含义。
    return normalized_health  # 新增代码+StatusSDKV2: 返回规范化健康块；若没有这行代码，调用方拿不到结果。


def _browser_store_for_workspace(workspace: str | Path) -> BrowserRuntimeStore:  # 新增代码+BrowserStatusStage11: SDK 按 workspace 形态定位浏览器 store；若没有这行代码，项目根和 agent 根会读不同位置。
    root = Path(workspace)  # 新增代码+BrowserStatusStage11: 规范化工作区路径；若没有这行代码，字符串路径后续处理不稳定。
    direct_store = BrowserRuntimeStore(root / "memory" / "browser_runtime")  # 新增代码+BrowserStatusStage11: 优先使用 agent.workspace 风格目录；若没有这行代码，真实 agent 运行状态读不到。
    package_store = BrowserRuntimeStore(root / "learning_agent" / "memory" / "browser_runtime")  # 新增代码+BrowserStatusStage11: 兼容从仓库根调用 SDK；若没有这行代码，Codex 外部查询可能漏数据。
    if direct_store.runs_dir.exists() or not package_store.runs_dir.exists():  # 新增代码+BrowserStatusStage11: 根据实际存在目录选择；若没有这行代码，状态路径会误判。
        return direct_store  # 新增代码+BrowserStatusStage11: 返回直接 store；若没有这行代码，调用方拿不到数据源。
    return package_store  # 新增代码+BrowserStatusStage11: 返回包内 store；若没有这行代码，项目根查询无法看到浏览器状态。


def get_browser_runs(workspace: str | Path) -> list[dict[str, Any]]:  # 新增代码+BrowserStatusStage11: 返回浏览器 runtime run 列表；若没有这行代码，外部 agent 只能读完整 snapshot。
    snapshot = get_status_snapshot(workspace)  # 新增代码+BrowserStatusStage11: 读取统一快照作为事实源；若没有这行代码，SDK 会和 /status 分裂。
    browser = snapshot.get("browser", {})  # 新增代码+BrowserStatusStage11: 提取浏览器区块；若没有这行代码，调用方需要知道内部字段。
    runs = browser.get("runs", []) if isinstance(browser, dict) else []  # 新增代码+BrowserStatusStage11: 安全读取 runs；若没有这行代码，坏快照会传出异常类型。
    return list(runs) if isinstance(runs, list) else []  # 新增代码+BrowserStatusStage11: 返回列表或空列表；若没有这行代码，调用方可能收到非列表。


def get_browser_provider_status(workspace: str | Path) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage8: 返回浏览器 provider 状态区块；若没有这行代码，外部 agent 只能解析完整 snapshot。
    snapshot = get_status_snapshot(workspace)  # 新增代码+ChromeExtensionStage8: 读取统一快照作为唯一事实源；若没有这行代码，SDK 可能和 CLI/API 状态分裂。
    browser = snapshot.get("browser", {})  # 新增代码+ChromeExtensionStage8: 提取 browser 区块；若没有这行代码，provider_status 的位置不清楚。
    provider_status = browser.get("provider_status", {}) if isinstance(browser, dict) else {}  # 新增代码+ChromeExtensionStage8: 安全读取 provider_status；若没有这行代码，坏快照会抛异常。
    return dict(provider_status) if isinstance(provider_status, dict) else {}  # 新增代码+ChromeExtensionStage8: 返回 dict 副本或空对象；若没有这行代码，调用方可能污染内部快照。


def get_browser_events(workspace: str | Path, run_id: str = "", limit: int = 20) -> list[dict[str, Any]]:  # 新增代码+BrowserStatusStage11: 返回浏览器事件尾巴；若没有这行代码，外部 agent 无法观察浏览器动作流。
    store = _browser_store_for_workspace(workspace)  # 新增代码+BrowserStatusStage11: 找到浏览器 runtime store；若没有这行代码，事件读取没有数据源。
    normalized_run_id = str(run_id).strip()  # 新增代码+BrowserStatusStage11: 清理可选 run id；若没有这行代码，复制空格会查不到。
    if normalized_run_id:  # 新增代码+BrowserStatusStage11: 指定 run 时只读该 run；若没有这行代码，单 run 查询无法生效。
        return store.tail_events(normalized_run_id, limit=limit)  # 新增代码+BrowserStatusStage11: 返回指定 run 事件；若没有这行代码，调用方拿不到事件。
    events: list[dict[str, Any]] = []  # 新增代码+BrowserStatusStage11: 准备合并所有 run 的事件；若没有这行代码，函数没有返回容器。
    for current_run_id in store.list_run_ids():  # 新增代码+BrowserStatusStage11: 遍历所有 browser run；若没有这行代码，未指定 run 时不会返回数据。
        events.extend(store.tail_events(current_run_id, limit=limit))  # 新增代码+BrowserStatusStage11: 合并每个 run 的事件尾巴；若没有这行代码，多任务事件不可见。
    return sorted(events, key=lambda event: int(event.get("timestamp_ms", 0)))[-limit:]  # 新增代码+BrowserStatusStage11: 返回全局最近事件；若没有这行代码，事件顺序不稳定。


def load_resume_report(workspace: str | Path, session_id: str) -> dict[str, Any]:  # 新增代码+StatusSDKV2: 读取指定 session 的完整恢复报告；若没有这行代码，外部 agent 不能审计 resume 是否安全。
    normalized_session_id = str(session_id).strip()  # 新增代码+StatusSDKV2: 清理 session_id 空白；若没有这行代码，用户复制命令时可能查不到会话。
    if not normalized_session_id:  # 新增代码+StatusSDKV2: 检查 session_id 是否为空；若没有这行代码，调用错误会变成难懂的文件不存在。
        return {"ok": False, "error": "missing_session_id"}  # 新增代码+StatusSDKV2: 返回结构化缺参错误；若没有这行代码，外部 agent 难以自动修正。
    context = ResumeLoader(Path(workspace) / "memory" / "sessions").load(normalized_session_id)  # 新增代码+StatusSDKV2: 调用真实 ResumeLoader；若没有这行代码，SDK 报告不会包含 repair/tombstone 信息。
    return {"ok": True, "resume": context.to_dict()}  # 新增代码+StatusSDKV2: 返回结构化恢复上下文；若没有这行代码，调用方拿不到可复现证据。


def list_status_events(workspace: str | Path, since_sequence: int | None = None, limit: int | None = None, event_type: str | None = None, event_types: set[str] | None = None) -> list[dict[str, Any]]:  # 修改代码+StatusSDKV2: 支持按事件类型过滤；若没有这行代码，外部 agent 只能自己筛全量事件。
    store = StatusEventStore(Path(workspace) / "memory" / "status")  # 新增代码+StatusSDK: 打开默认状态事件目录；若没有这行代码，SDK 找不到事件流。
    raw_events = [event.to_dict() for event in store.list_events(since_sequence=since_sequence, limit=limit)]  # 修改代码+StatusSDKV2: 先读取 JSON 友好事件；若没有这行代码，后续过滤没有输入。
    requested_types = set(event_types or set())  # 新增代码+StatusSDKV2: 复制事件类型集合；若没有这行代码，调用方集合可能被污染。
    if event_type:  # 新增代码+StatusSDKV2: 如果调用方传入单个类型；若没有这行代码，event_type 参数不会生效。
        requested_types.add(str(event_type))  # 新增代码+StatusSDKV2: 合并单类型过滤；若没有这行代码，单类型调用会返回全量。
    if requested_types:  # 新增代码+StatusSDKV2: 只有存在过滤条件时才过滤；若没有这行代码，默认调用会错误返回空。
        raw_events = [event for event in raw_events if str(event.get("event_type", "")) in requested_types]  # 新增代码+StatusSDKV2: 保留目标事件类型；若没有这行代码，外部 watcher 收到噪声。
    return raw_events  # 修改代码+StatusSDKV2: 返回过滤后的事件；若没有这行代码，调用方拿不到结果。


def watch_status_events(workspace: str | Path, since_sequence: int = 0, poll_interval_seconds: float = 1.0, max_polls: int | None = None, event_types: set[str] | None = None) -> Iterator[dict[str, Any]]:  # 修改代码+StatusSDKV2: watch 支持事件类型过滤；若没有这行代码，长任务观察会收到无关事件。
    current_sequence = int(since_sequence)  # 新增代码+StatusSDK: 保存当前已消费序号；若没有这行代码，watch 会重复返回旧事件。
    poll_count = 0  # 新增代码+StatusSDK: 保存已轮询次数；若没有这行代码，max_polls 无法生效。
    while max_polls is None or poll_count < max_polls:  # 新增代码+StatusSDK: 按次数或无限轮询；若没有这行代码，watch 只能跑一次。
        poll_count += 1  # 新增代码+StatusSDK: 推进轮询次数；若没有这行代码，max_polls 会无限循环。
        events = list_status_events(workspace, since_sequence=current_sequence, event_types=event_types)  # 修改代码+StatusSDKV2: 读取新事件并应用类型过滤；若没有这行代码，watch 参数不会生效。
        for event in events:  # 新增代码+StatusSDK: 逐条返回新事件；若没有这行代码，调用方拿不到增量事件。
            current_sequence = max(current_sequence, int(event.get("sequence", 0)))  # 新增代码+StatusSDK: 更新已消费序号；若没有这行代码，下一轮会重复事件。
            yield event  # 新增代码+StatusSDK: 把事件交给调用方；若没有这行代码，生成器不会产出任何内容。
        if max_polls is not None and poll_count >= max_polls:  # 新增代码+StatusSDK: 达到最大轮询次数时退出；若没有这行代码，测试或短任务无法自然结束。
            break  # 新增代码+StatusSDK: 停止 watch；若没有这行代码，函数会继续 sleep。
        time.sleep(max(0.05, float(poll_interval_seconds)))  # 新增代码+StatusSDK: 等待下一轮；若没有这行代码，watch 会忙等占用 CPU。
