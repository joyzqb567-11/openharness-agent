"""状态快照聚合器，把 run、stage、task、queue、session、event 汇成一个视图。"""  # 新增代码+StatusSnapshot: 说明本模块是状态生态唯一聚合入口；若没有这行代码，CLI/SDK/工具会各读各的。

from __future__ import annotations  # 新增代码+StatusSnapshot: 延迟解析类型注解；若没有这行代码，复杂返回类型更容易受顺序影响。

import json  # 新增代码+ChromeExtensionStage8: 读取 Chrome 插件 bridge 状态 JSON；若没有这行代码，provider 状态只能停留在内存里。
from pathlib import Path  # 新增代码+StatusSnapshot: 使用 Path 管理 workspace；若没有这行代码，路径拼接更脆弱。
from typing import Any  # 新增代码+StatusSnapshot: 快照是通用 JSON dict；若没有这行代码，类型边界不清楚。

from learning_agent.browser.recording import BrowserRecordingStore  # 新增代码+BrowserRecordingStage9: 读取浏览器录制/GIF 证据；若没有这行代码，状态快照看不到 Stage 9 视觉产物。
from learning_agent.browser_extension_host.manifest_installer import ChromeNativeHostInstaller  # 新增代码+Phase12ChromeStatusGuide: 读取 native host 安装器状态；如果没有这行代码，/chrome 向导拿不到 installer_state。
from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+BrowserStatusStage11: 读取浏览器 runtime 事实源；若没有这行代码，状态快照看不到真实浏览器 run/action/observation。
from learning_agent.core.session import SessionStore  # 新增代码+StatusSnapshot: 读取 session summary 列表；若没有这行代码，快照缺少可恢复会话。
from learning_agent.harness.store import HarnessStore  # 新增代码+StatusSnapshot: 读取 harness run；若没有这行代码，快照无法显示长任务。
from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+StatusSnapshot: 读取 runtime 命令队列；若没有这行代码，快照看不到 prompt/task/resume 队列。
from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+StatusSnapshot: 读取全局状态事件；若没有这行代码，快照缺少事件尾巴。
from learning_agent.runtime.task_registry import TaskRegistry  # 新增代码+StatusSnapshot: 读取持久任务登记表；若没有这行代码，快照看不到后台任务。


def _latest_event(events: list[dict[str, Any]], event_types: set[str]) -> dict[str, Any]:  # 新增代码+StatusSnapshotV2: 找到某类事件的最后一条；若没有这行代码，current/compact/resume 区块会重复扫描。
    for event in reversed(events):  # 新增代码+StatusSnapshotV2: 从尾部向前找最新事件；若没有这行代码，状态会误用旧事件。
        if str(event.get("event_type", "")) in event_types:  # 新增代码+StatusSnapshotV2: 判断事件类型是否匹配；若没有这行代码，任意事件都可能被当成目标。
            return event  # 新增代码+StatusSnapshotV2: 返回最新匹配事件；若没有这行代码，调用方拿不到结果。
    return {}  # 新增代码+StatusSnapshotV2: 没有匹配时返回空字典；若没有这行代码，调用方需要处理 None。


def _current_run_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+StatusSnapshotV2: 从事件流推导当前 run；若没有这行代码，外部 agent 不知道当前运行对象。
    event = _latest_event(events, {"run_started", "run_completed", "run_failed"})  # 新增代码+StatusSnapshotV2: 找最新 run 生命周期事件；若没有这行代码，current_run 可能使用无关事件。
    return {"run_id": event.get("run_id", ""), "session_id": event.get("session_id", ""), "state": event.get("event_type", ""), "payload": event.get("payload", {})} if event else {}  # 新增代码+StatusSnapshotV2: 返回当前 run 摘要；若没有这行代码，快照缺少顶层运行状态。


def _current_turn_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+StatusSnapshotV2: 从事件流推导当前 turn；若没有这行代码，resume 和 UI 无法定位轮次。
    event = _latest_event(events, {"turn_accepted", "model_request_started", "model_message_delta", "model_response_completed", "tool_use_seen", "tool_result_seen", "compact_completed", "resume_needs_review"})  # 新增代码+StatusSnapshotV2: 找最新 turn 相关事件；若没有这行代码，current_turn 会缺少阶段信息。
    return {"turn_id": event.get("turn_id", ""), "run_id": event.get("run_id", ""), "session_id": event.get("session_id", ""), "state": event.get("event_type", ""), "payload": event.get("payload", {})} if event else {}  # 新增代码+StatusSnapshotV2: 返回当前 turn 摘要；若没有这行代码，快照无法说明当前卡点。


def _compact_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+StatusSnapshotV2: 汇总最近 compact 状态；若没有这行代码，用户只能手动翻事件。
    event = _latest_event(events, {"compact_completed", "reactive_compact_retry"})  # 新增代码+StatusSnapshotV2: 读取最近压缩或恢复压缩事件；若没有这行代码，reactive compact 不会显示。
    payload = event.get("payload", {}) if event else {}  # 新增代码+StatusSnapshotV2: 安全读取事件载荷；若没有这行代码，空事件会报错。
    boundary = payload.get("boundary", payload.get("compact_boundary", {})) if isinstance(payload, dict) else {}  # 新增代码+StatusSnapshotV2: 兼容不同调用点的 boundary 字段；若没有这行代码，最新边界可能读不到。
    if isinstance(boundary, dict):  # 新增代码+StatusSnapshotV2: 只有字典 boundary 才读取 uuid；若没有这行代码，异常 payload 会导致属性错误。
        boundary_uuid = str(boundary.get("boundary_uuid", ""))  # 新增代码+StatusSnapshotV2: 读取边界 uuid；若没有这行代码，状态页无法快速引用 compact。
    else:  # 新增代码+StatusSnapshotV2: 处理非字典 boundary；若没有这行代码，坏 payload 会中断快照。
        boundary_uuid = ""  # 新增代码+StatusSnapshotV2: 非字典时使用空 uuid；若没有这行代码，变量未定义。
    return {"state": event.get("event_type", "") if event else "", "latest_boundary_uuid": boundary_uuid, "event": event}  # 新增代码+StatusSnapshotV2: 返回 compact 区块；若没有这行代码，快照缺少压缩状态。


def _resume_from_events(events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+StatusSnapshotV2: 汇总最近 resume 状态；若没有这行代码，用户不知道恢复是否安全。
    event = _latest_event(events, {"resume_completed", "resume_needs_review", "resume_blocked", "resume_started"})  # 新增代码+StatusSnapshotV2: 找最近恢复生命周期事件；若没有这行代码，resume 区块无法推导。
    return {"state": event.get("event_type", "") if event else "", "event": event}  # 新增代码+StatusSnapshotV2: 返回 resume 区块；若没有这行代码，快照缺少恢复风险。


def _health_from_inputs(runs: list[dict[str, Any]], tasks: list[dict[str, Any]], commands: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+StatusSnapshotV2: 构建快照健康信息；若没有这行代码，坏数据和风险没有统一落点。
    warnings: list[str] = []  # 新增代码+StatusSnapshotV2: 准备健康警告列表；若没有这行代码，函数没有返回容器。
    if any(event.get("event_type") in {"resume_needs_review", "resume_blocked"} for event in events):  # 新增代码+StatusSnapshotV2: 检查恢复风险事件；若没有这行代码，状态页可能假装安全。
        warnings.append("resume requires attention")  # 新增代码+StatusSnapshotV2: 记录恢复需要关注；若没有这行代码，用户看不到风险摘要。
    if any(command.get("status") in {"queued", "leased", "running"} for command in commands):  # 新增代码+StatusSnapshotV2: 检查仍有未完成命令；若没有这行代码，队列堵塞不明显。
        warnings.append("runtime commands pending")  # 新增代码+StatusSnapshotV2: 记录命令队列未清空；若没有这行代码，长任务卡点不明显。
    return {"ok": not warnings, "warnings": warnings, "run_count": len(runs), "task_count": len(tasks), "event_count": len(events)}  # 新增代码+StatusSnapshotV2: 返回健康摘要；若没有这行代码，外部 agent 没有快速判断字段。


def _stage_to_snapshot(stage: Any, index: int) -> dict[str, Any]:  # 新增代码+StatusSnapshot: 把 HarnessStage 转成轻量状态 dict；若没有这行代码，run 快照会包含过大的完整对象。
    return {"index": index, "name": stage.name, "status": stage.status, "attempt_count": len(stage.attempts), "acceptance": stage.acceptance.to_dict(), "checkpoint": stage.checkpoint, "started_at": stage.started_at, "completed_at": stage.completed_at}  # 新增代码+StatusSnapshot: 返回阶段关键字段；若没有这行代码，状态页无法显示 stage/verifier/checkpoint。


def _run_to_snapshot(run: Any) -> dict[str, Any]:  # 新增代码+StatusSnapshot: 把 HarnessRun 转成轻量状态 dict；若没有这行代码，CLI/SDK 会重复挑字段。
    return {"run_id": run.run_id, "prompt": run.prompt, "status": run.status, "current_stage_index": run.current_stage_index, "failure_reason": run.failure_reason, "updated_at": run.updated_at, "stages": [_stage_to_snapshot(stage, index) for index, stage in enumerate(run.stages)]}  # 新增代码+StatusSnapshot: 返回 run 和阶段摘要；若没有这行代码，状态生态无法同屏看到阶段。


def _task_to_snapshot(task: Any) -> dict[str, Any]:  # 新增代码+StatusSnapshot: 把 TaskRecord 转成轻量状态 dict；若没有这行代码，任务状态输出会重复字段选择。
    return {"task_id": task.task_id, "kind": task.kind, "status": task.status, "prompt": task.prompt, "output": task.output, "error": task.error, "output_path": task.output_path, "owner_run_id": task.owner_run_id, "updated_at": task.updated_at, "completed_at": task.completed_at}  # 新增代码+StatusSnapshot: 返回任务关键字段；若没有这行代码，状态页无法显示任务输出和错误。


def _command_to_snapshot(command: Any) -> dict[str, Any]:  # 新增代码+StatusSnapshot: 把 RuntimeCommand 转成轻量状态 dict；若没有这行代码，队列状态会泄露过大 payload。
    return {"command_id": command.command_id, "mode": command.mode, "priority": command.priority, "status": command.status, "payload": dict(command.payload), "created_at": command.created_at, "updated_at": command.updated_at}  # 新增代码+StatusSnapshot: 返回命令关键字段；若没有这行代码，状态页无法显示队列生命周期。


def _harness_store_for_workspace(root: Path) -> HarnessStore:  # 新增代码+BrowserHarnessStage11: 按 workspace 形态定位 harness store；若没有这行代码，项目根和 learning_agent 包目录会读写两套 run。
    direct_store = HarnessStore(root / "memory" / "harness")  # 新增代码+BrowserHarnessStage11: 支持 workspace 已经是 learning_agent 包目录；若没有这行代码，真实终端 agent 的 harness 状态读不到。
    package_store = HarnessStore(root / "learning_agent" / "memory" / "harness")  # 新增代码+BrowserHarnessStage11: 支持从项目根读取包内 harness；若没有这行代码，browser MCP server 写入的 harness run 会不可见。
    if root.name.lower() == "learning_agent":  # 新增代码+BrowserHarnessStage11: 明确识别包目录 workspace；若没有这行代码，可能错误选择 learning_agent/learning_agent 路径。
        return direct_store  # 新增代码+BrowserHarnessStage11: 包目录直接返回 memory/harness；若没有这行代码，主 agent 状态快照会读错目录。
    if direct_store.runs_dir.exists() or not package_store.runs_dir.exists():  # 新增代码+BrowserHarnessStage11: 直接目录存在时优先直接目录，否则项目根模式选包内目录；若没有这行代码，空目录会遮住真实包内 run。
        return direct_store  # 新增代码+BrowserHarnessStage11: 返回直接 harness store；若没有这行代码，测试和包目录模式会失效。
    return package_store  # 新增代码+BrowserHarnessStage11: 返回项目根兼容 harness store；若没有这行代码，browser run 的 harness 投影不会进入状态快照。


def _load_runs(workspace: Path) -> list[dict[str, Any]]:  # 新增代码+StatusSnapshot: 读取所有 harness run 摘要；若没有这行代码，主函数会塞满容错逻辑。
    store = _harness_store_for_workspace(workspace)  # 修改代码+BrowserHarnessStage11: 兼容项目根和包目录两种 harness store；若没有这行代码，browser MCP server 生成的 harness run 会被快照漏掉。
    runs: list[dict[str, Any]] = []  # 新增代码+StatusSnapshot: 准备累计 run；若没有这行代码，函数没有返回容器。
    for run_id in store.list_run_ids():  # 新增代码+StatusSnapshot: 遍历所有 run id；若没有这行代码，快照不会包含任务。
        try:  # 新增代码+StatusSnapshot: 单个坏 run 不应拖垮全局状态；若没有这行代码，坏 JSON 会让状态页不可用。
            runs.append(_run_to_snapshot(store.load_run(run_id)))  # 新增代码+StatusSnapshot: 读取并转换 run；若没有这行代码，run 不会进入快照。
        except (FileNotFoundError, OSError, ValueError):  # 新增代码+StatusSnapshot: 跳过损坏或消失的 run；若没有这行代码，状态页会因为一个坏文件失败。
            continue  # 新增代码+StatusSnapshot: 继续读取其他 run；若没有这行代码，后续 run 会被跳过。
    return runs  # 新增代码+StatusSnapshot: 返回 run 摘要列表；若没有这行代码，调用方拿不到数据。


def _browser_store_for_workspace(root: Path) -> BrowserRuntimeStore:  # 新增代码+BrowserStatusStage11: 按 workspace 形态找到浏览器 runtime store；若没有这行代码，项目根和 learning_agent 根会读不同位置。
    direct_store = BrowserRuntimeStore(root / "memory" / "browser_runtime")  # 新增代码+BrowserStatusStage11: 优先使用 agent.workspace 风格目录；若没有这行代码，真实 agent 运行状态读不到。
    package_store = BrowserRuntimeStore(root / "learning_agent" / "memory" / "browser_runtime")  # 新增代码+BrowserStatusStage11: 兼容外部传项目根目录；若没有这行代码，Codex 从仓库根查状态会漏数据。
    if direct_store.runs_dir.exists() or not package_store.runs_dir.exists():  # 新增代码+BrowserStatusStage11: 直接目录存在时优先直接目录；若没有这行代码，测试和真实 agent 工作区会被误判。
        return direct_store  # 新增代码+BrowserStatusStage11: 返回直接 store；若没有这行代码，调用方拿不到数据源。
    return package_store  # 新增代码+BrowserStatusStage11: 返回项目根兼容 store；若没有这行代码，从仓库根调用状态会看不到浏览器任务。


def _browser_harness_snapshot(store: HarnessStore, run_id: str) -> dict[str, Any]:  # 新增代码+BrowserHarnessStage11: 读取 browser run 对应的 harness 摘要；若没有这行代码，browser.runs 不能直接展示 verifier。
    try:  # 新增代码+BrowserHarnessStage11: 单个缺失 harness run 不应拖垮整个 browser 状态；若没有这行代码，坏投影会导致 /status 失败。
        run = store.load_run(run_id)  # 新增代码+BrowserHarnessStage11: 按同 id 读取 harness run；若没有这行代码，无法关联 browser runtime 和 harness。
    except (FileNotFoundError, OSError, ValueError):  # 新增代码+BrowserHarnessStage11: 缺失或损坏时返回空摘要；若没有这行代码，历史坏文件会破坏状态页。
        return {}  # 新增代码+BrowserHarnessStage11: 空字典表示该 browser run 暂无 harness 投影；若没有这行代码，调用方要处理异常。
    events = store.read_events(run_id)  # 新增代码+BrowserHarnessStage11: 读取 harness event log；若没有这行代码，latest_verifier 无法从事件流提取。
    verifier_events = [event for event in events if str(event.get("event_type", "")) == "verifier_result"]  # 新增代码+BrowserHarnessStage11: 过滤 verifier 事件；若没有这行代码，状态页无法快速看到验收结果。
    latest_verifier = verifier_events[-1].get("payload", {}) if verifier_events else {}  # 新增代码+BrowserHarnessStage11: 取最新 verifier payload；若没有这行代码，UI/SDK 只能遍历完整事件。
    payload = _run_to_snapshot(run)  # 新增代码+BrowserHarnessStage11: 复用标准 harness run 摘要；若没有这行代码，browser 区块和 runs 区块字段会分裂。
    payload["latest_verifier"] = latest_verifier if isinstance(latest_verifier, dict) else {}  # 新增代码+BrowserHarnessStage11: 附加浏览器相关最新 verifier；若没有这行代码，browser.runs[*].harness 缺少验收快捷入口。
    payload["event_count"] = len(events)  # 新增代码+BrowserHarnessStage11: 附加 harness 事件数量；若没有这行代码，外部 agent 无法判断投影是否有审计轨迹。
    return payload  # 新增代码+BrowserHarnessStage11: 返回可 JSON 序列化摘要；若没有这行代码，调用方拿不到关联结果。


def _chrome_extension_bridge_path(root: Path) -> Path:  # 新增代码+ChromeExtensionStage8: 按 workspace 形态定位插件 bridge 状态文件；若没有这行代码，CLI/API/SDK 会读错插件状态。
    direct_path = root / "memory" / "chrome_extension_bridge.json"  # 新增代码+ChromeExtensionStage8: 支持 agent 根目录直接存放 bridge 状态；若没有这行代码，包内运行方式无法被读取。
    package_path = root / "learning_agent" / "memory" / "chrome_extension_bridge.json"  # 新增代码+ChromeExtensionStage8: 支持仓库根目录下的生产 bridge 状态；若没有这行代码，当前项目默认路径会漏读。
    if direct_path.exists() and not package_path.exists():  # 新增代码+ChromeExtensionStage8: 只有直接路径存在且包内路径不存在时才选直接路径；若没有这行代码，仓库根和包根可能冲突。
        return direct_path  # 新增代码+ChromeExtensionStage8: 返回直接 bridge 状态路径；若没有这行代码，调用方拿不到目标文件。
    return package_path  # 新增代码+ChromeExtensionStage8: 默认返回仓库根生产路径；若没有这行代码，首次状态也需要自行拼路径。

def _chrome_native_host_target_dir(root: Path) -> Path:  # 新增代码+Phase12ChromeStatusGuide: 按 workspace 形态定位 native host manifest 目录；如果没有这段函数，状态快照会重复出现 learning_agent/learning_agent 路径。
    return root / "memory" / "chrome_native_host" if root.name.lower() == "learning_agent" else root / "learning_agent" / "memory" / "chrome_native_host"  # 新增代码+Phase12ChromeStatusGuide: 兼容包目录和仓库根目录；如果没有这行代码，真实 bat 和 Codex 根目录会读不同位置。

def _native_host_installer_status(root: Path) -> dict[str, Any]:  # 新增代码+Phase12ChromeStatusGuide: 读取 native host 安装器状态；如果没有这段函数，/chrome 无法显示 install-preview/install-confirm 的下一步依据。
    try:  # 新增代码+Phase12ChromeStatusGuide: registry 读取可能因平台或权限失败；如果没有这行代码，状态页会被 registry 异常拖垮。
        status = ChromeNativeHostInstaller(_chrome_native_host_target_dir(root)).status()  # 新增代码+Phase12ChromeStatusGuide: 使用真实安装器生成状态；如果没有这行代码，快照会和安装命令事实源分裂。
    except Exception as error:  # 新增代码+Phase12ChromeStatusGuide: 捕获安装器异常；如果没有这行代码，非 Windows 或权限问题会让 /status 崩溃。
        return {"state": "registry_unavailable", "error": str(error)}  # 新增代码+Phase12ChromeStatusGuide: 返回可展示错误状态；如果没有这行代码，用户只能看到堆栈。
    return status if isinstance(status, dict) else {"state": "registry_unavailable"}  # 新增代码+Phase12ChromeStatusGuide: 保证返回字典；如果没有这行代码，坏实现会破坏后续字段合并。

def _load_json_object(path: Path) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage8: 安全读取 JSON 对象状态；若没有这行代码，坏 bridge 文件会拖垮整个 /status。
    if not path.exists():  # 新增代码+ChromeExtensionStage8: 文件不存在时返回空状态；若没有这行代码，未安装插件会抛 FileNotFoundError。
        return {}  # 新增代码+ChromeExtensionStage8: 返回空字典表示暂无状态；若没有这行代码，调用方需要处理 None。
    try:  # 新增代码+ChromeExtensionStage8: 捕获 JSON 损坏和读取错误；若没有这行代码，半写入状态会让状态页不可用。
        data = json.loads(path.read_text(encoding="utf-8"))  # 新增代码+ChromeExtensionStage8: 用 UTF-8 读取并解析状态文件；若没有这行代码，中文 title 或 URL 状态无法稳定读取。
    except (OSError, json.JSONDecodeError):  # 新增代码+ChromeExtensionStage8: 处理文件系统和 JSON 格式错误；若没有这行代码，坏文件异常会外溢。
        return {"status_error": f"无法读取状态文件：{path}"}  # 新增代码+ChromeExtensionStage8: 返回结构化错误；若没有这行代码，用户不知道状态为什么缺失。
    return data if isinstance(data, dict) else {"status_error": "状态文件顶层不是对象"}  # 新增代码+ChromeExtensionStage8: 只接受对象状态；若没有这行代码，数组或字符串会破坏后续字段读取。

def _active_tab_from_context(context: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage8: 从 tabs context 中提取 active tab；若没有这行代码，状态渲染要重复搜索逻辑。
    tabs = context.get("tabs", []) if isinstance(context.get("tabs", []), list) else []  # 新增代码+ChromeExtensionStage8: 安全读取 tab 列表；若没有这行代码，坏状态会导致遍历异常。
    active_tab_id = str(context.get("active_tab_id", "") or "")  # 新增代码+ChromeExtensionStage8: 读取 active tab id；若没有这行代码，无法优先匹配当前页。
    for tab in tabs:  # 新增代码+ChromeExtensionStage8: 遍历 tab 摘要查找 active id；若没有这行代码，active_tab 可能为空。
        if isinstance(tab, dict) and str(tab.get("tab_id", "") or "") == active_tab_id:  # 新增代码+ChromeExtensionStage8: 匹配插件生成的 tab_id；若没有这行代码，可能显示错误标签页。
            return dict(tab)  # 新增代码+ChromeExtensionStage8: 返回 active tab 副本；若没有这行代码，调用方可能污染原始状态。
    for tab in tabs:  # 新增代码+ChromeExtensionStage8: active id 不可靠时按 active 标记兜底；若没有这行代码，旧状态无法显示当前页。
        if isinstance(tab, dict) and bool(tab.get("active", False)):  # 新增代码+ChromeExtensionStage8: 检查 active 布尔标记；若没有这行代码，兜底无法生效。
            return dict(tab)  # 新增代码+ChromeExtensionStage8: 返回 active 标记的 tab；若没有这行代码，调用方拿不到当前页。
    return dict(tabs[0]) if tabs and isinstance(tabs[0], dict) else {}  # 新增代码+ChromeExtensionStage8: 最后用首个 tab 兜底；若没有这行代码，无 active 状态会完全空白。

def _load_browser_provider_status(root: Path, browser_runtime: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage8: 聚合 provider、插件、native host、tab、权限和最近证据；若没有这行代码，Stage 8 状态生态仍是旁路。
    bridge_path = _chrome_extension_bridge_path(root)  # 新增代码+ChromeExtensionStage8: 找到插件 bridge 状态文件；若没有这行代码，后续无法读取插件连接。
    bridge_state = _load_json_object(bridge_path)  # 新增代码+ChromeExtensionStage8: 读取 bridge 状态；若没有这行代码，provider 状态没有输入。
    connected = bool(bridge_state.get("connected", False))  # 新增代码+ChromeExtensionStage8: 读取插件连接布尔值；若没有这行代码，provider 健康无法判断。
    tabs_context = bridge_state.get("last_tabs_context", {}) if isinstance(bridge_state.get("last_tabs_context", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取最近 tab context；若没有这行代码，状态页看不到标签页。
    tabs = tabs_context.get("tabs", []) if isinstance(tabs_context.get("tabs", []), list) else []  # 新增代码+ChromeExtensionStage8: 安全读取 tabs 列表；若没有这行代码，tab_count 和 active_tab 会不可靠。
    permission_events = bridge_state.get("permission_events", []) if isinstance(bridge_state.get("permission_events", []), list) else []  # 新增代码+ChromeExtensionStage8: 读取权限事件列表；若没有这行代码，授权变更不可审计。
    pending_commands = bridge_state.get("pending_commands", []) if isinstance(bridge_state.get("pending_commands", []), list) else []  # 新增代码+ChromeExtensionStage8: 读取待执行命令；若没有这行代码，插件卡住时状态不可见。
    command_results = bridge_state.get("command_results", {}) if isinstance(bridge_state.get("command_results", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取尚未消费的命令结果；若没有这行代码，执行完成但 provider 未消费的状态不可见。
    installer_status = _native_host_installer_status(root)  # 新增代码+Phase12ChromeStatusGuide: 读取 native host 安装器状态；如果没有这行代码，/chrome 无法展示安装向导。
    actions = browser_runtime.get("actions", []) if isinstance(browser_runtime.get("actions", []), list) else []  # 新增代码+ChromeExtensionStage8: 读取 browser runtime 最近动作；若没有这行代码，provider 状态缺少工作证据。
    observations = browser_runtime.get("observations", []) if isinstance(browser_runtime.get("observations", []), list) else []  # 新增代码+ChromeExtensionStage8: 读取 browser runtime 最近观察；若没有这行代码，状态缺少页面证据。
    chrome_reason = "chrome_extension_bridge_connected" if connected else "chrome_extension_bridge_not_connected"  # 新增代码+ChromeExtensionStage8: 生成插件健康原因；若没有这行代码，外部 agent 不知道可用/不可用依据。
    return {"providers": {"visible_chromium": {"available": True, "reason": "visible_chromium_adapter_ready"}, "real_chrome_cdp": {"available": True, "reason": "real_chrome_cdp_adapter_ready"}, "chrome_extension": {"available": connected, "reason": chrome_reason}}, "chrome_extension": {"connected": connected, "extension_id": bridge_state.get("extension_id", ""), "last_seen_at": bridge_state.get("last_seen_at", ""), "read_only": bool(bridge_state.get("read_only", False)), "pending_command_count": len(pending_commands), "command_result_count": len(command_results), "permission_event_count": len(permission_events), "bridge_state_file": str(bridge_path), "status_error": bridge_state.get("status_error", "")}, "native_host": {"connected": connected, "installed": bridge_path.exists(), "bridge_state_file": str(bridge_path), "last_seen_at": bridge_state.get("last_seen_at", ""), "disconnect_reason": bridge_state.get("disconnect_reason", ""), "installer_state": installer_status.get("state", ""), "manifest_path": installer_status.get("manifest_path", ""), "manifest_exists": installer_status.get("manifest_exists", False), "registry_key_path": installer_status.get("registry_key_path", ""), "registry_value": installer_status.get("registry_value", ""), "registry_targets": installer_status.get("registry_targets", [])}, "tabs": {"tab_count": len(tabs), "active_tab": _active_tab_from_context(tabs_context), "tabs": [dict(tab) for tab in tabs if isinstance(tab, dict)][-20:]}, "permissions": {"permission_event_count": len(permission_events), "events": [dict(event) for event in permission_events if isinstance(event, dict)][-20:]}, "recent_actions": [dict(action) for action in actions if isinstance(action, dict)][-5:], "recent_observations": [dict(observation) for observation in observations if isinstance(observation, dict)][-5:]}  # 修改代码+Phase12ChromeStatusGuide: 返回完整 provider 状态并加入 installer 状态；若没有这行代码，CLI/SDK/API 没有统一安装向导依据。

def _load_browser_recordings(root: Path) -> dict[str, Any]:  # 新增代码+BrowserRecordingStage9: 聚合浏览器录制/GIF 证据；若没有这行代码，状态页看不到可回放视觉产物。
    store = BrowserRecordingStore(root / "browser_artifacts" / "browser_recordings")  # 新增代码+BrowserRecordingStage9: 使用生产录制目录；若没有这行代码，快照会读错录制位置。
    recordings = store.list_recordings(limit=20)  # 新增代码+BrowserRecordingStage9: 读取最近录制 manifest；若没有这行代码，状态页无法列出录制。
    latest = recordings[0] if recordings else {}  # 新增代码+BrowserRecordingStage9: 取最新录制；若没有这行代码，终端 UI 需要重复判断。
    return {"store": str(store.base_dir), "recording_count": len(recordings), "latest": latest, "items": recordings}  # 新增代码+BrowserRecordingStage9: 返回录制状态区块；若没有这行代码，SDK/API 无法机器读取帧数和 GIF 路径。

def _load_browser_runtime(root: Path, event_limit: int = 20) -> dict[str, Any]:  # 新增代码+BrowserStatusStage11: 聚合浏览器 run/action/observation/event 状态；若没有这行代码，UI/SDK/API 看不到真实浏览器生态。
    store = _browser_store_for_workspace(root)  # 新增代码+BrowserStatusStage11: 找到浏览器 runtime store；若没有这行代码，状态聚合没有数据源。
    harness_store = _harness_store_for_workspace(root)  # 新增代码+BrowserHarnessStage11: 找到 browser run 对应 harness store；若没有这行代码，browser 状态无法展示 verifier。
    runs: list[dict[str, Any]] = []  # 新增代码+BrowserStatusStage11: 准备保存 run 摘要；若没有这行代码，返回字段没有容器。
    actions: list[dict[str, Any]] = []  # 新增代码+BrowserStatusStage11: 准备保存最近动作；若没有这行代码，状态页看不到工具步骤。
    observations: list[dict[str, Any]] = []  # 新增代码+BrowserStatusStage11: 准备保存最近观察；若没有这行代码，状态页看不到页面证据。
    events: list[dict[str, Any]] = []  # 新增代码+BrowserStatusStage11: 准备保存事件尾巴；若没有这行代码，外部 watcher 无法观察浏览器时间线。
    latest_browser_verifier: dict[str, Any] = {}  # 新增代码+BrowserHarnessStage11: 保存最近 browser harness verifier；若没有这行代码，browser 总览缺少验收结论。
    for run_id in store.list_run_ids():  # 新增代码+BrowserStatusStage11: 遍历所有浏览器 run；若没有这行代码，历史浏览器任务不会进入快照。
        try:  # 新增代码+BrowserStatusStage11: 单个坏 run 不应拖垮全局状态；若没有这行代码，坏 JSON 会让 /status 失败。
            browser_run = store.load_run(run_id)  # 新增代码+BrowserStatusStage11: 读取浏览器 run；若没有这行代码，run 摘要没有来源。
        except FileNotFoundError:  # 新增代码+BrowserStatusStage11: 跳过消失或损坏的 run；若没有这行代码，状态页会中断。
            continue  # 新增代码+BrowserStatusStage11: 继续其他 run；若没有这行代码，一个坏 run 会阻止后续数据。
        run_payload = browser_run.to_dict()  # 新增代码+BrowserStatusStage11: 转成 JSON 友好 dict；若没有这行代码，快照无法序列化。
        runs.append(run_payload)  # 新增代码+BrowserStatusStage11: 保存 run 摘要；若没有这行代码，browser.runs 会为空。
        for action_id in browser_run.action_ids[-10:]:  # 新增代码+BrowserStatusStage11: 只读取最近动作避免快照过大；若没有这行代码，大任务会输出过多数据。
            try:  # 新增代码+BrowserStatusStage11: 单个动作可能已损坏；若没有这行代码，状态页会被坏动作拖垮。
                actions.append(store.load_action(action_id).to_dict())  # 新增代码+BrowserStatusStage11: 读取并保存动作摘要；若没有这行代码，工具步骤不可见。
            except FileNotFoundError:  # 新增代码+BrowserStatusStage11: 缺动作时跳过；若没有这行代码，旧状态兼容性差。
                continue  # 新增代码+BrowserStatusStage11: 继续后续动作；若没有这行代码，剩余动作会丢失。
        for observation_id in browser_run.observation_ids[-10:]:  # 新增代码+BrowserStatusStage11: 只读取最近观察避免快照过大；若没有这行代码，大页面证据会撑爆状态。
            try:  # 新增代码+BrowserStatusStage11: 单个观察可能已损坏；若没有这行代码，状态页会被坏证据拖垮。
                observations.append(store.load_observation(observation_id).to_dict())  # 新增代码+BrowserStatusStage11: 读取并保存页面证据；若没有这行代码，浏览器观察不可见。
            except FileNotFoundError:  # 新增代码+BrowserStatusStage11: 缺观察时跳过；若没有这行代码，旧状态兼容性差。
                continue  # 新增代码+BrowserStatusStage11: 继续后续观察；若没有这行代码，剩余证据会丢失。
        harness_payload = _browser_harness_snapshot(harness_store, run_id)  # 新增代码+BrowserHarnessStage11: 读取该 browser run 的 harness 投影；若没有这行代码，状态快照无法直接关联 verifier。
        if harness_payload:  # 新增代码+BrowserHarnessStage11: 只有存在 harness 投影时才附加；若没有这行代码，空字段会误导 UI 认为已有验收。
            run_payload["harness"] = harness_payload  # 新增代码+BrowserHarnessStage11: 把 harness 摘要挂到 browser run；若没有这行代码，CLI/API 仍需要手工跨 store 查询。
            latest_candidate = harness_payload.get("latest_verifier", {})  # 新增代码+BrowserHarnessStage11: 读取该 run 最新 verifier；若没有这行代码，总览字段无法更新。
            if isinstance(latest_candidate, dict) and latest_candidate:  # 新增代码+BrowserHarnessStage11: 只接受非空 dict verifier；若没有这行代码，坏数据可能覆盖有效结果。
                latest_browser_verifier = latest_candidate  # 新增代码+BrowserHarnessStage11: 保存最近 verifier 供 browser 总览使用；若没有这行代码，UI/SDK 缺少快速判断入口。
        events.extend(store.tail_events(run_id, limit=event_limit))  # 新增代码+BrowserStatusStage11: 合并每个 run 的事件尾巴；若没有这行代码，外部 agent 看不到浏览器事件。
    events = sorted(events, key=lambda event: int(event.get("timestamp_ms", 0)))[-event_limit:]  # 新增代码+BrowserStatusStage11: 全局按时间取最近事件；若没有这行代码，多 run 事件顺序会混乱。
    latest_run = runs[-1] if runs else {}  # 新增代码+BrowserStatusStage11: 保存最近 run 摘要；若没有这行代码，状态页缺少快捷入口。
    browser_runtime = {"store": str(store.base_dir), "harness": {"store": str(harness_store.base_dir), "latest_verifier": latest_browser_verifier}, "latest_run": latest_run, "runs": runs, "actions": actions, "observations": observations, "events": events, "counts": {"runs": len(runs), "actions": len(actions), "observations": len(observations), "events": len(events)}}  # 修改代码+BrowserHarnessStage11: 构造 browser runtime 状态块并加入 harness verifier；若没有这行代码，provider 状态和 UI/SDK 看不到浏览器验收结果。
    browser_runtime["provider_status"] = _load_browser_provider_status(root, browser_runtime)  # 新增代码+ChromeExtensionStage8: 把 provider、插件、native host、tab、权限接入同一 browser 区块；若没有这行代码，Stage 8 状态生态仍不可见。
    browser_runtime["recordings"] = _load_browser_recordings(root)  # 新增代码+BrowserRecordingStage9: 把录制/GIF 视觉证据接入同一 browser 区块；若没有这行代码，Stage 9 产物会成为旁路文件。
    return browser_runtime  # 修改代码+ChromeExtensionStage8: 返回包含 provider_status 的 browser 状态块；若没有这行代码，CLI/SDK/API 拿不到新增区块。


def build_status_snapshot(workspace: str | Path, event_limit: int = 50) -> dict[str, Any]:  # 新增代码+StatusSnapshot: 构建统一状态快照；若没有这行代码，终端、SDK、HTTP 和工具无法共享事实源。
    root = Path(workspace)  # 新增代码+StatusSnapshot: 规范化 workspace；若没有这行代码，字符串路径后续操作不稳定。
    task_registry = TaskRegistry(root / "memory" / "tasks")  # 新增代码+StatusSnapshot: 打开任务登记表；若没有这行代码，快照缺少 task。
    runtime_queue = RuntimeCommandQueue(root / "memory" / "runtime")  # 新增代码+StatusSnapshot: 打开 runtime queue；若没有这行代码，快照缺少 command。
    status_store = StatusEventStore(root / "memory" / "status")  # 新增代码+StatusSnapshot: 打开状态事件 store；若没有这行代码，快照缺少全局事件。
    session_store = SessionStore(root / "memory" / "sessions")  # 新增代码+StatusSnapshot: 打开 session store；若没有这行代码，快照缺少可恢复会话。
    runs = _load_runs(root)  # 新增代码+StatusSnapshot: 读取 run 摘要；若没有这行代码，快照 run 字段为空。
    tasks = [_task_to_snapshot(task) for task in task_registry.list_tasks()]  # 新增代码+StatusSnapshot: 读取任务摘要；若没有这行代码，状态页看不到 task。
    commands = [_command_to_snapshot(command) for command in runtime_queue.list_commands()]  # 新增代码+StatusSnapshot: 读取命令摘要；若没有这行代码，队列不可见。
    events = [event.to_dict() for event in status_store.list_events(limit=event_limit)]  # 新增代码+StatusSnapshot: 读取状态事件尾巴；若没有这行代码，状态页没有事件流。
    sessions = session_store.list_recent_sessions(limit=20)  # 新增代码+StatusSnapshot: 读取最近 session id；若没有这行代码，resume 工具和状态页缺入口。
    current_run = _current_run_from_events(events)  # 新增代码+StatusSnapshotV2: 从事件流计算当前 run；若没有这行代码，快照缺少 ClaudeCode 式当前状态。
    current_turn = _current_turn_from_events(events)  # 新增代码+StatusSnapshotV2: 从事件流计算当前 turn；若没有这行代码，状态页无法解释当前卡点。
    compact = _compact_from_events(events)  # 新增代码+StatusSnapshotV2: 计算 compact 区块；若没有这行代码，压缩边界无法同屏显示。
    resume = _resume_from_events(events)  # 新增代码+StatusSnapshotV2: 计算 resume 区块；若没有这行代码，恢复风险无法同屏显示。
    browser = _load_browser_runtime(root, event_limit=event_limit)  # 新增代码+BrowserStatusStage11: 聚合浏览器 runtime 状态；若没有这行代码，真实浏览器 run/action/observation 仍是旁路系统。
    health = _health_from_inputs(runs, tasks, commands, events)  # 新增代码+StatusSnapshotV2: 计算健康摘要；若没有这行代码，外部 agent 缺少快速判断入口。
    return {"schema_version": 2, "workspace": str(root), "current_run": current_run, "current_turn": current_turn, "compact": compact, "resume": resume, "browser": browser, "model": {"state": current_turn.get("state", "") if current_turn else ""}, "tools": {"latest_tool_event": _latest_event(events, {"tool_use_seen", "tool_result_seen", "tool_call_started", "tool_call_completed"})}, "runs": runs, "tasks": tasks, "commands": commands, "status_events": events, "sessions": sessions, "verifiers": {"latest": _latest_event(events, {"verifier_result"})}, "outputs": {"artifacts": []}, "latest_events": events, "health": health, "counts": {"runs": len(runs), "tasks": len(tasks), "commands": len(commands), "status_events": len(events), "sessions": len(sessions), "browser_runs": browser.get("counts", {}).get("runs", 0)}}  # 修改代码+BrowserStatusStage11: 返回 v2 状态生态字段并加入 browser 区块；若没有这行代码，SDK/终端仍看不到浏览器 runtime。
