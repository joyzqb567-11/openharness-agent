"""Desktop GUI Harness controls backed by the existing file store."""  # 新增代码+DesktopGUIHarnessControls：说明本模块只负责把 GUI 控制接到现有 harness store；如果没有这行代码，维护者不清楚这里不是新 runner。

from __future__ import annotations  # 新增代码+DesktopGUIHarnessControls：启用延迟类型注解；如果没有这行代码，返回类型引用在旧 Python 版本上更脆弱。

from pathlib import Path  # 新增代码+DesktopGUIHarnessControls：使用 Path 处理 workspace 路径；如果没有这行代码，Windows 路径拼接容易出错。
from typing import Any  # 新增代码+DesktopGUIHarnessControls：控制 payload 是通用 JSON；如果没有这行代码，类型边界不清楚。

from learning_agent.app.gui_protocol import GUI_V2_SCHEMA_VERSION  # 新增代码+DesktopGUIHarnessControls：复用 GUI V2 协议版本；如果没有这行代码，控制响应版本会和 bridge 分裂。
from learning_agent.harness.models import HarnessRun, utc_timestamp  # 新增代码+DesktopGUIHarnessControls：复用真实 run 模型和时间戳；如果没有这行代码，控制层会退化成散装 dict。
from learning_agent.harness.store import HarnessStore  # 新增代码+DesktopGUIHarnessControls：复用真实 harness 持久化 store；如果没有这行代码，GUI 控制无法落盘。
from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DesktopGUIHarnessControls：复用统一状态事件流；如果没有这行代码，GUI 点击结果不会进入时间线。
from learning_agent.runtime.status_snapshot import _harness_store_for_workspace  # 新增代码+DesktopGUIHarnessControls：复用现有 workspace 到 harness store 的定位逻辑；如果没有这行代码，GUI 和状态快照可能读写两套目录。


GUI_HARNESS_CONTROL_SOURCE = "learning_agent.harness.store"  # 新增代码+DesktopGUIHarnessControls：声明控制能力来源；如果没有这行代码，前端和文档无法说明复用了哪个原模块。
GUI_HARNESS_ACTIVE_STATUSES = {"queued", "running", "paused", "needs_permission", "cancelling"}  # 新增代码+DesktopGUIHarnessControls：集中定义 GUI 需要关注的非终态；如果没有这行代码，暂停任务可能从面板消失。
GUI_HARNESS_STOPPABLE_STATUSES = {"queued", "running", "paused", "needs_permission", "cancelling"}  # 新增代码+DesktopGUIHarnessControls：集中定义可以停止的状态；如果没有这行代码，stop 语义会散在分支里。


def build_gui_harness_controls_capabilities() -> dict[str, Any]:  # 新增代码+DesktopGUIHarnessControls：函数段开始，返回 GUI 可渲染的控制能力；如果没有这段，状态端点只能继续隐藏按钮。
    return {"pause_supported": True, "resume_supported": True, "stop_supported": True, "checkpoint_supported": True, "restore_supported": False, "control_source": GUI_HARNESS_CONTROL_SOURCE}  # 新增代码+DesktopGUIHarnessControls：声明真实支持 pause/resume/stop/checkpoint；如果没有这行代码，Task 页签没有事实源能力开关。
# 新增代码+DesktopGUIHarnessControls：函数段结束，build_gui_harness_controls_capabilities 到此结束；如果没有边界说明，初学者不易看出它只负责能力声明。


def _workspace_path(workspace: str | Path) -> Path:  # 新增代码+DesktopGUIHarnessControls：函数段开始，规范化 workspace；如果没有这段，不同调用点可能读写相对路径。
    return Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIHarnessControls：返回绝对路径；如果没有这行代码，store 路径可能随当前目录变化。
# 新增代码+DesktopGUIHarnessControls：函数段结束，_workspace_path 到此结束；如果没有边界说明，初学者不易看出它只负责路径规范化。


def _status_store_for_workspace(root: Path) -> StatusEventStore:  # 新增代码+DesktopGUIHarnessControls：函数段开始，定位统一状态事件 store；如果没有这段，控制事件不会进入 GUI 时间线。
    return StatusEventStore(root / "memory" / "status")  # 新增代码+DesktopGUIHarnessControls：沿用 status_snapshot 的 memory/status 路径；如果没有这行代码，状态页读不到控制事件。
# 新增代码+DesktopGUIHarnessControls：函数段结束，_status_store_for_workspace 到此结束；如果没有边界说明，初学者不易看出它只负责状态事件目录。


def _load_control_runs(store: HarnessStore) -> list[HarnessRun]:  # 新增代码+DesktopGUIHarnessControls：函数段开始，读取可供 GUI 控制选择的 run 列表；如果没有这段，每个动作都要重复容错读取。
    runs: list[HarnessRun] = []  # 新增代码+DesktopGUIHarnessControls：准备累计 run；如果没有这行代码，函数没有返回容器。
    for run_id in store.list_run_ids():  # 新增代码+DesktopGUIHarnessControls：遍历现有 run id；如果没有这行代码，控制层找不到任何持久任务。
        run = store.try_load_run(run_id)  # 新增代码+DesktopGUIHarnessControls：容错读取 run；如果没有这行代码，单个坏 JSON 会拖垮整个 GUI 控制。
        if run is not None:  # 新增代码+DesktopGUIHarnessControls：只保留读取成功的 run；如果没有这行代码，后续会访问 None。
            runs.append(run)  # 新增代码+DesktopGUIHarnessControls：加入候选列表；如果没有这行代码，成功读取的任务也不会被控制。
    return sorted(runs, key=lambda run: run.updated_at)  # 新增代码+DesktopGUIHarnessControls：按更新时间排序；如果没有这行代码，选择“最新任务”的行为不稳定。
# 新增代码+DesktopGUIHarnessControls：函数段结束，_load_control_runs 到此结束；如果没有边界说明，初学者不易看出它只负责读取候选。


def _select_latest_run(store: HarnessStore, statuses: set[str]) -> HarnessRun | None:  # 新增代码+DesktopGUIHarnessControls：函数段开始，选择最新的指定状态 run；如果没有这段，控制按钮不知道该作用于哪个目标。
    candidates = [run for run in _load_control_runs(store) if run.status in statuses]  # 新增代码+DesktopGUIHarnessControls：筛选可操作状态；如果没有这行代码，已完成任务可能被错误修改。
    return candidates[-1] if candidates else None  # 新增代码+DesktopGUIHarnessControls：返回最新候选或空；如果没有这行代码，调用方拿不到明确选择结果。
# 新增代码+DesktopGUIHarnessControls：函数段结束，_select_latest_run 到此结束；如果没有边界说明，初学者不易看出它只负责选择 run。


def _current_stage(run: HarnessRun):  # 新增代码+DesktopGUIHarnessControls：函数段开始，安全读取当前阶段；如果没有这段，空 stages 或越界索引会让控制端点 500。
    if 0 <= run.current_stage_index < len(run.stages):  # 新增代码+DesktopGUIHarnessControls：确认索引落在阶段范围内；如果没有这行代码，坏状态文件会触发 IndexError。
        return run.stages[run.current_stage_index]  # 新增代码+DesktopGUIHarnessControls：返回当前阶段对象；如果没有这行代码，pause/checkpoint 无法更新阶段状态。
    return None  # 新增代码+DesktopGUIHarnessControls：没有当前阶段时返回空；如果没有这行代码，调用方无法安全兜底。
# 新增代码+DesktopGUIHarnessControls：函数段结束，_current_stage 到此结束；如果没有边界说明，初学者不易看出它只负责阶段访问。


def _base_control_payload(action: str, supported: bool, status: str, message: str, run_id: str = "", extra: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+DesktopGUIHarnessControls：函数段开始，组装统一控制响应；如果没有这段，各动作响应字段容易漂移。
    payload = {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": action, "supported": supported, "status": status, "run_id": run_id, "message": message, "safe_error": ""}  # 新增代码+DesktopGUIHarnessControls：写入 GUI 需要的稳定字段；如果没有这行代码，前端无法统一显示控制结果。
    payload.update(extra or {})  # 新增代码+DesktopGUIHarnessControls：合并动作专属字段；如果没有这行代码，checkpoint 文本等细节无法返回给 GUI。
    return payload  # 新增代码+DesktopGUIHarnessControls：返回响应；如果没有这行代码，调用方拿不到 payload。
# 新增代码+DesktopGUIHarnessControls：函数段结束，_base_control_payload 到此结束；如果没有边界说明，初学者不易看出它只负责响应形状。


def _record_control_event(store: HarnessStore, status_store: StatusEventStore, run: HarnessRun, action: str, status: str, message: str, checkpoint: str = "") -> None:  # 新增代码+DesktopGUIHarnessControls：函数段开始，记录 harness 和全局状态事件；如果没有这段，控制动作缺少审计证据。
    payload = {"action": action, "status": status, "message": message, "checkpoint": checkpoint, "control_source": GUI_HARNESS_CONTROL_SOURCE}  # 新增代码+DesktopGUIHarnessControls：构造事件正文；如果没有这行代码，事件消费者看不懂控制发生了什么。
    store.append_event(run.run_id, "gui_harness_control", payload)  # 新增代码+DesktopGUIHarnessControls：写入 run 私有事件日志；如果没有这行代码，harness CLI 无法复盘 GUI 控制。
    status_store.append("gui_harness_control", payload, run_id=run.run_id)  # 新增代码+DesktopGUIHarnessControls：写入全局状态事件；如果没有这行代码，右侧状态页看不到控制动作。
# 新增代码+DesktopGUIHarnessControls：函数段结束，_record_control_event 到此结束；如果没有边界说明，初学者不易看出它只负责事件记录。


def _pause_harness_run(store: HarnessStore, status_store: StatusEventStore) -> dict[str, Any]:  # 新增代码+DesktopGUIHarnessControls：函数段开始，执行暂停动作；如果没有这段，GUI 暂停按钮只能返回占位。
    run = _select_latest_run(store, {"queued", "running", "needs_permission", "cancelling"})  # 新增代码+DesktopGUIHarnessControls：选择可暂停 run；如果没有这行代码，暂停不知道作用于哪个任务。
    if run is None:  # 新增代码+DesktopGUIHarnessControls：处理没有活动任务的情况；如果没有这行代码，空 workspace 会抛异常。
        return _base_control_payload("pause", True, "no_active_run", "当前没有可暂停的长任务。")  # 新增代码+DesktopGUIHarnessControls：返回安全空态；如果没有这行代码，GUI 点击空任务会显示网络失败。
    stage = _current_stage(run)  # 新增代码+DesktopGUIHarnessControls：读取当前阶段；如果没有这行代码，阶段状态无法同步暂停。
    run.status = "paused"  # 新增代码+DesktopGUIHarnessControls：把 run 标记为 paused；如果没有这行代码，HarnessQueue 仍可能继续领取任务。
    run.lease_worker = ""  # 新增代码+DesktopGUIHarnessControls：清空 worker；如果没有这行代码，暂停任务仍像被 worker 占用。
    run.lease_until = 0.0  # 新增代码+DesktopGUIHarnessControls：清空租约时间；如果没有这行代码，恢复时可能还受旧租约影响。
    if stage is not None and stage.status in {"pending", "running"}:  # 新增代码+DesktopGUIHarnessControls：只改当前未完成阶段；如果没有这行代码，已完成阶段可能被误标 paused。
        stage.status = "paused"  # 新增代码+DesktopGUIHarnessControls：把当前阶段标记暂停；如果没有这行代码，面板会显示 run 暂停但阶段仍 running。
    store.save_run(run)  # 新增代码+DesktopGUIHarnessControls：保存暂停后的 run；如果没有这行代码，状态变化只在内存里。
    message = "长任务已暂停，恢复前不会被队列 worker 继续领取。"  # 新增代码+DesktopGUIHarnessControls：准备用户可读说明；如果没有这行代码，GUI 只能显示机器状态。
    _record_control_event(store, status_store, run, "pause", "paused", message)  # 新增代码+DesktopGUIHarnessControls：记录暂停审计事件；如果没有这行代码，后续无法复盘谁暂停了任务。
    return _base_control_payload("pause", True, "paused", message, run_id=run.run_id)  # 新增代码+DesktopGUIHarnessControls：返回暂停响应；如果没有这行代码，按钮点击后没有结构化结果。
# 新增代码+DesktopGUIHarnessControls：函数段结束，_pause_harness_run 到此结束；如果没有边界说明，初学者不易看出暂停动作范围。


def _resume_harness_run(store: HarnessStore, status_store: StatusEventStore) -> dict[str, Any]:  # 新增代码+DesktopGUIHarnessControls：函数段开始，执行恢复动作；如果没有这段，GUI 恢复按钮只能返回占位。
    run = _select_latest_run(store, {"paused"})  # 新增代码+DesktopGUIHarnessControls：选择已暂停 run；如果没有这行代码，恢复可能误改正在运行的任务。
    if run is None:  # 新增代码+DesktopGUIHarnessControls：处理没有暂停任务的情况；如果没有这行代码，空恢复会抛异常。
        return _base_control_payload("resume", True, "no_paused_run", "当前没有已暂停的长任务。")  # 新增代码+DesktopGUIHarnessControls：返回安全空态；如果没有这行代码，GUI 无法给用户明确反馈。
    stage = _current_stage(run)  # 新增代码+DesktopGUIHarnessControls：读取当前阶段；如果没有这行代码，阶段状态无法同步恢复。
    run.status = "queued"  # 新增代码+DesktopGUIHarnessControls：把 run 放回 queued；如果没有这行代码，HarnessQueue 不会重新领取它。
    run.lease_worker = ""  # 新增代码+DesktopGUIHarnessControls：清空 worker；如果没有这行代码，恢复任务可能仍显示旧占用者。
    run.lease_until = 0.0  # 新增代码+DesktopGUIHarnessControls：清空租约时间；如果没有这行代码，恢复后可能被旧租约挡住。
    if stage is not None and stage.status == "paused":  # 新增代码+DesktopGUIHarnessControls：只恢复被暂停的当前阶段；如果没有这行代码，其他阶段状态可能被误改。
        stage.status = "pending"  # 新增代码+DesktopGUIHarnessControls：把阶段放回待执行；如果没有这行代码，runner 可能不知道从哪里继续。
    store.save_run(run)  # 新增代码+DesktopGUIHarnessControls：保存恢复后的 run；如果没有这行代码，状态变化不会落盘。
    message = "长任务已恢复为 queued，下一轮 worker 可以继续领取。"  # 新增代码+DesktopGUIHarnessControls：准备用户可读说明；如果没有这行代码，GUI 只能显示机器状态。
    _record_control_event(store, status_store, run, "resume", "queued", message)  # 新增代码+DesktopGUIHarnessControls：记录恢复审计事件；如果没有这行代码，时间线看不到恢复动作。
    return _base_control_payload("resume", True, "queued", message, run_id=run.run_id)  # 新增代码+DesktopGUIHarnessControls：返回恢复响应；如果没有这行代码，按钮点击后没有结构化结果。
# 新增代码+DesktopGUIHarnessControls：函数段结束，_resume_harness_run 到此结束；如果没有边界说明，初学者不易看出恢复动作范围。


def _stop_harness_run(store: HarnessStore, status_store: StatusEventStore) -> dict[str, Any]:  # 新增代码+DesktopGUIHarnessControls：函数段开始，执行停止动作；如果没有这段，GUI 没有长任务急停入口。
    run = _select_latest_run(store, GUI_HARNESS_STOPPABLE_STATUSES)  # 新增代码+DesktopGUIHarnessControls：选择可停止 run；如果没有这行代码，stop 不知道作用于哪个任务。
    if run is None:  # 新增代码+DesktopGUIHarnessControls：处理没有可停止任务的情况；如果没有这行代码，空停止会抛异常。
        return _base_control_payload("stop", True, "no_active_run", "当前没有可停止的长任务。")  # 新增代码+DesktopGUIHarnessControls：返回安全空态；如果没有这行代码，GUI 无法给用户明确反馈。
    stage = _current_stage(run)  # 新增代码+DesktopGUIHarnessControls：读取当前阶段；如果没有这行代码，阶段终止状态无法同步。
    run.status = "cancelled"  # 新增代码+DesktopGUIHarnessControls：把 run 标记为 cancelled；如果没有这行代码，队列可能继续执行被用户停止的任务。
    run.failure_reason = "用户从 Desktop GUI 停止长任务。"  # 新增代码+DesktopGUIHarnessControls：写入停止原因；如果没有这行代码，用户以后不知道任务为什么结束。
    run.lease_worker = ""  # 新增代码+DesktopGUIHarnessControls：清空 worker；如果没有这行代码，停止任务仍像被 worker 占用。
    run.lease_until = 0.0  # 新增代码+DesktopGUIHarnessControls：清空租约时间；如果没有这行代码，状态页会显示无意义租约。
    if stage is not None and stage.status not in {"completed", "failed", "cancelled"}:  # 新增代码+DesktopGUIHarnessControls：只终止未完成阶段；如果没有这行代码，已完成阶段会被覆盖。
        stage.status = "cancelled"  # 新增代码+DesktopGUIHarnessControls：把当前阶段标记取消；如果没有这行代码，面板会显示 run 已停但阶段仍 running。
    store.save_run(run)  # 新增代码+DesktopGUIHarnessControls：保存停止后的 run；如果没有这行代码，停止只在内存里。
    message = "长任务已停止并进入 cancelled 终态。"  # 新增代码+DesktopGUIHarnessControls：准备用户可读说明；如果没有这行代码，GUI 只能显示机器状态。
    _record_control_event(store, status_store, run, "stop", "cancelled", message)  # 新增代码+DesktopGUIHarnessControls：记录停止审计事件；如果没有这行代码，时间线看不到停止动作。
    return _base_control_payload("stop", True, "cancelled", message, run_id=run.run_id)  # 新增代码+DesktopGUIHarnessControls：返回停止响应；如果没有这行代码，按钮点击后没有结构化结果。
# 新增代码+DesktopGUIHarnessControls：函数段结束，_stop_harness_run 到此结束；如果没有边界说明，初学者不易看出停止动作范围。


def _checkpoint_harness_run(store: HarnessStore, status_store: StatusEventStore) -> dict[str, Any]:  # 新增代码+DesktopGUIHarnessControls：函数段开始，执行手动 checkpoint；如果没有这段，GUI 无法主动留下恢复点。
    run = _select_latest_run(store, GUI_HARNESS_ACTIVE_STATUSES)  # 新增代码+DesktopGUIHarnessControls：选择可 checkpoint 的活动 run；如果没有这行代码，恢复点不知道写到哪个任务。
    if run is None:  # 新增代码+DesktopGUIHarnessControls：处理没有活动任务的情况；如果没有这行代码，空 checkpoint 会抛异常。
        return _base_control_payload("checkpoint", True, "no_active_run", "当前没有可写入 checkpoint 的长任务。")  # 新增代码+DesktopGUIHarnessControls：返回安全空态；如果没有这行代码，GUI 无法给用户明确反馈。
    stage = _current_stage(run)  # 新增代码+DesktopGUIHarnessControls：读取当前阶段；如果没有这行代码，恢复点无法关联阶段名。
    timestamp = utc_timestamp()  # 新增代码+DesktopGUIHarnessControls：生成稳定 UTC 时间戳；如果没有这行代码，checkpoint 无法定位创建时间。
    stage_name = stage.name if stage is not None else "未命名阶段"  # 新增代码+DesktopGUIHarnessControls：读取阶段名或兜底；如果没有这行代码，事件 checkpoint 缺少归属。
    checkpoint = f"Desktop GUI checkpoint {timestamp}"  # 新增代码+DesktopGUIHarnessControls：生成手动 checkpoint 文本；如果没有这行代码，用户看不到 checkpoint 来源。
    if stage is not None:  # 新增代码+DesktopGUIHarnessControls：确认存在当前阶段；如果没有这行代码，空 stages 会触发属性错误。
        stage.checkpoint = checkpoint  # 新增代码+DesktopGUIHarnessControls：把 checkpoint 写入当前阶段；如果没有这行代码，run 快照不会携带手动恢复点。
    store.save_run(run)  # 新增代码+DesktopGUIHarnessControls：保存 checkpoint 后的 run；如果没有这行代码，恢复点不会落盘。
    message = "手动 checkpoint 已写入。"  # 新增代码+DesktopGUIHarnessControls：准备用户可读说明；如果没有这行代码，GUI 点击后没有清楚反馈。
    store.append_event(run.run_id, "harness_checkpoint", {"stage_name": stage_name, "checkpoint": checkpoint, "status": "checkpointed", "control_source": GUI_HARNESS_CONTROL_SOURCE})  # 新增代码+DesktopGUIHarnessControls：写入 run 私有 checkpoint 事件；如果没有这行代码，harness 事件日志缺少恢复点。
    status_store.append("harness_checkpoint", {"stage_name": stage_name, "checkpoint": checkpoint, "status": "checkpointed", "control_source": GUI_HARNESS_CONTROL_SOURCE}, run_id=run.run_id)  # 新增代码+DesktopGUIHarnessControls：写入全局 checkpoint 事件；如果没有这行代码，Task 面板 checkpoint 时间线不会立即出现。
    _record_control_event(store, status_store, run, "checkpoint", "checkpointed", message, checkpoint=checkpoint)  # 新增代码+DesktopGUIHarnessControls：记录通用控制事件；如果没有这行代码，状态页无法把点击和 checkpoint 联系起来。
    return _base_control_payload("checkpoint", True, "checkpointed", message, run_id=run.run_id, extra={"checkpoint": checkpoint, "stage_name": stage_name})  # 新增代码+DesktopGUIHarnessControls：返回 checkpoint 响应；如果没有这行代码，GUI 无法显示恢复点摘要。
# 新增代码+DesktopGUIHarnessControls：函数段结束，_checkpoint_harness_run 到此结束；如果没有边界说明，初学者不易看出 checkpoint 动作范围。


def build_gui_harness_control_payload(action: str, workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIHarnessControls：函数段开始，按 action 分发真实控制；如果没有这段，bridge 路由会继续返回 unsupported。
    root = _workspace_path(workspace)  # 新增代码+DesktopGUIHarnessControls：规范化 workspace；如果没有这行代码，store 可能读写相对路径。
    store = _harness_store_for_workspace(root)  # 新增代码+DesktopGUIHarnessControls：复用状态快照的 harness store 定位；如果没有这行代码，GUI 控制可能改错目录。
    status_store = _status_store_for_workspace(root)  # 新增代码+DesktopGUIHarnessControls：打开全局状态事件 store；如果没有这行代码，控制结果不会进入右侧时间线。
    if action == "pause":  # 新增代码+DesktopGUIHarnessControls：匹配暂停动作；如果没有这行代码，pause 路由无法分发。
        return _pause_harness_run(store, status_store)  # 新增代码+DesktopGUIHarnessControls：执行暂停并返回结果；如果没有这行代码，暂停请求没有真实效果。
    if action == "resume":  # 新增代码+DesktopGUIHarnessControls：匹配恢复动作；如果没有这行代码，resume 路由无法分发。
        return _resume_harness_run(store, status_store)  # 新增代码+DesktopGUIHarnessControls：执行恢复并返回结果；如果没有这行代码，恢复请求没有真实效果。
    if action == "stop":  # 新增代码+DesktopGUIHarnessControls：匹配停止动作；如果没有这行代码，stop 路由无法分发。
        return _stop_harness_run(store, status_store)  # 新增代码+DesktopGUIHarnessControls：执行停止并返回结果；如果没有这行代码，停止请求没有真实效果。
    if action == "checkpoint":  # 新增代码+DesktopGUIHarnessControls：匹配 checkpoint 动作；如果没有这行代码，checkpoint 路由无法分发。
        return _checkpoint_harness_run(store, status_store)  # 新增代码+DesktopGUIHarnessControls：执行 checkpoint 并返回结果；如果没有这行代码，恢复点请求没有真实效果。
    return _base_control_payload(action, False, "unsupported", "未知长任务控制动作。")  # 新增代码+DesktopGUIHarnessControls：未知动作返回结构化不支持；如果没有这行代码，坏路由可能变成 500。
# 新增代码+DesktopGUIHarnessControls：函数段结束，build_gui_harness_control_payload 到此结束；如果没有边界说明，初学者不易看出公共入口范围。
