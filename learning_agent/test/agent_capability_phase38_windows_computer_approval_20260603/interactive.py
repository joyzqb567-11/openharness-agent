"""交互式终端应用层，承载真实用户可见的输入输出循环。"""  # 新增代码+AppSplit: 说明本模块负责交互终端；若没有这行代码，终端循环仍会堆在 learning_agent.py。
from __future__ import annotations  # 新增代码+AppSplit: 允许类型注解延迟解析；若没有这行代码，类型提示在部分运行顺序下可能提前求值。

import json  # 新增代码+TerminalStatusUI: 格式化 resume/compact 结构化状态；若没有这行代码，终端命令只能打印难读的 Python 对象。
import sys  # 新增代码+Phase9ChromeTerminalActions: 获取当前 Python 解释器路径；如果没有这行代码，/chrome install-preview 生成的 launcher 可能不知道该用哪个 Python。
import time  # 新增代码+Phase15ChromePairingTrigger: 生成配对请求时间戳；如果没有这行代码，pairing-preview 无法展示请求新鲜度。
from pathlib import Path  # 新增代码+AppSplit: 标注工作区路径类型；若没有这行代码，终端事件里的 workspace 来源不清楚。
from typing import Any  # 新增代码+AppSplit: 允许接收任意实现了 run 的 agent；若没有这行代码，模块会和 LearningAgent 类强耦合。
from uuid import uuid4  # 新增代码+Phase15ChromePairingTrigger: 生成配对请求 nonce；如果没有这行代码，配对触发无法区分不同请求。

CHROME_INSTALL_CONFIRM_TOKEN = "I_UNDERSTAND_WRITE_REGISTRY"  # 新增代码+Phase10ChromeInstallConfirm: 固定真实写 registry 的确认 token；如果没有这行代码，用户可能无意触发生产安装。
CHROME_UNINSTALL_CONFIRM_TOKEN = "I_UNDERSTAND_DELETE_REGISTRY"  # 新增代码+Phase11ChromeUninstallConfirm: 固定真实删 registry 的确认 token；如果没有这行代码，用户可能无意触发生产卸载。
CHROME_PAIRING_CONFIRM_TOKEN = "I_UNDERSTAND_PAIR_CHROME"  # 新增代码+Phase15ChromePairingTrigger: 固定配对触发确认 token；如果没有这行代码，用户可能误写 bridge 待配对请求。

try:  # 新增代码+AppSplit: 优先按包路径导入轮次格式化和验收事件 helper；若没有这行代码，包运行模式下交互层无法复用通用能力。
    from learning_agent.app.chrome_status_renderer import render_chrome_status  # 新增代码+ChromeTerminalUI: 导入 /chrome 专用状态渲染器；若没有这行代码，终端无法显示聚焦 Chrome 面板。
    from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+Phase15ChromePairingTrigger: 导入 bridge 状态对象；如果没有这行代码，终端无法写入待配对请求。
    from learning_agent.browser_extension_host.manifest_installer import ChromeNativeHostInstaller  # 新增代码+Phase9ChromeTerminalActions: 导入 native host 安装器；如果没有这行代码，/chrome install-preview 只能显示文案不能生成 manifest。
    from learning_agent.computer_use.approval import WindowsComputerUseApprovalModel  # 新增代码+Phase38WindowsComputerApproval: 导入 Windows approval 终端状态模型；如果没有这行代码，/computer status 无法显示 session allowlist 和 grant flags。
    from learning_agent.computer_use.lock import ComputerUseLockManager  # 新增代码+Phase31ComputerUseLockAbortEvidence: 导入桌面锁管理器；如果没有这行代码，/computer 终端命令无法读取或修改 abort 状态。
    from learning_agent.app.status_renderer import render_status_snapshot  # 新增代码+StatusEcosystem: 导入终端状态渲染器；若没有这行代码，/status 无法显示统一状态页。
    from learning_agent.core.config import format_max_turns_status  # 新增代码+AppSplit: 导入轮次状态格式化；若没有这行代码，终端启动提示无法显示当前策略。
    from learning_agent.observability.acceptance_events import emit_acceptance_event  # 新增代码+AppSplit: 导入验收事件写入器；若没有这行代码，真实终端控制器无法知道何时输入 prompt。
    from learning_agent.observability.run_records import build_final_answer_event_payload  # 新增代码+AppSplit: 导入最终回答事件 payload helper；若没有这行代码，final_answer_printed 会丢完整回答字段。
    from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+Phase16SessionSyncClosure: 导入 durable runtime queue；如果没有这行代码，session-sync-selftest 无法证明浏览器 prompt 入队。
    from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+StatusEcosystem: 导入统一状态快照聚合器；若没有这行代码，/status 会读不到 run/task/queue/session。
    from learning_agent.sdk.status import get_sessions, list_status_events, load_resume_report  # 新增代码+TerminalStatusUI: 复用 SDK 状态入口；若没有这行代码，终端 /events、/sessions、/resume 会另写旁路读取逻辑。
except ModuleNotFoundError as error:  # 新增代码+AppSplit: 捕获脚本模式下包路径不可用；若没有这行代码，双击 bat 时交互层可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.app", "learning_agent.app.chrome_status_renderer", "learning_agent.app.status_renderer", "learning_agent.browser_extension_host", "learning_agent.browser_extension_host.bridge_server", "learning_agent.browser_extension_host.manifest_installer", "learning_agent.computer_use", "learning_agent.computer_use.approval", "learning_agent.computer_use.lock", "learning_agent.core", "learning_agent.core.config", "learning_agent.observability", "learning_agent.observability.acceptance_events", "learning_agent.observability.run_records", "learning_agent.runtime", "learning_agent.runtime.command_queue", "learning_agent.runtime.status_snapshot", "learning_agent.sdk", "learning_agent.sdk.status"}:  # 修改代码+Phase38WindowsComputerApproval: 允许 computer_use.approval 在脚本模式 fallback；若没有这行代码，bat 入口下 /computer status 可能导入失败。
        raise  # 新增代码+AppSplit: 重新抛出真实导入错误；若没有这行代码，观测层或配置层问题会被隐藏。
    from app.chrome_status_renderer import render_chrome_status  # 新增代码+ChromeTerminalUI: 脚本模式导入 /chrome 专用渲染器；若没有这行代码，直接运行时 /chrome 无法显示。
    from browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+Phase15ChromePairingTrigger: 脚本模式导入 bridge 状态对象；如果没有这行代码，双击 bat 后 pairing-start-confirm 不可用。
    from browser_extension_host.manifest_installer import ChromeNativeHostInstaller  # 新增代码+Phase9ChromeTerminalActions: 脚本模式导入 native host 安装器；如果没有这行代码，双击 bat 后 /chrome install-preview 不可用。
    from computer_use.approval import WindowsComputerUseApprovalModel  # 新增代码+Phase38WindowsComputerApproval: 脚本模式导入 Windows approval 终端状态模型；如果没有这行代码，双击 bat 后 /computer status 看不到审批摘要。
    from computer_use.lock import ComputerUseLockManager  # 新增代码+Phase31ComputerUseLockAbortEvidence: 脚本模式导入桌面锁管理器；如果没有这行代码，双击 bat 后 /computer abort 不可用。
    from app.status_renderer import render_status_snapshot  # 新增代码+StatusEcosystem: 脚本模式导入状态渲染器；若没有这行代码，直接运行时 /status 无法显示。
    from core.config import format_max_turns_status  # 新增代码+AppSplit: 脚本模式从同目录 core 包导入；若没有这行代码，直接运行时轮次提示会断开。
    from observability.acceptance_events import emit_acceptance_event  # 新增代码+AppSplit: 脚本模式从同目录 observability 包导入；若没有这行代码，bat 入口无法写验收事件。
    from observability.run_records import build_final_answer_event_payload  # 新增代码+AppSplit: 脚本模式导入最终回答 payload helper；若没有这行代码，真实终端最终回答事件会断开。
    from runtime.command_queue import RuntimeCommandQueue  # 新增代码+Phase16SessionSyncClosure: 脚本模式导入 durable runtime queue；如果没有这行代码，双击 bat 后 session-sync-selftest 不可用。
    from runtime.status_snapshot import build_status_snapshot  # 新增代码+StatusEcosystem: 脚本模式导入状态聚合器；若没有这行代码，直接运行时 /status 没有数据源。
    from sdk.status import get_sessions, list_status_events, load_resume_report  # 新增代码+TerminalStatusUI: 脚本模式复用 SDK 状态入口；若没有这行代码，直接运行时新增状态命令无法工作。


def _print_events_command(workspace: Path) -> None:  # 新增代码+TerminalStatusUI: 打印最近状态事件；若没有这行代码，/events 会散落在主循环里难以维护。
    events = list_status_events(workspace, since_sequence=0, limit=10)  # 新增代码+TerminalStatusUI: 从 SDK 读取最新事件；若没有这行代码，终端事件视图会和 API/SDK 分裂。
    print("\nStatus Events")  # 新增代码+TerminalStatusUI: 输出事件区块标题；若没有这行代码，用户不知道下面是事件流。
    if not events:  # 新增代码+TerminalStatusUI: 检查是否没有事件；若没有这行代码，空事件时终端会像卡住。
        print("- (empty)")  # 新增代码+TerminalStatusUI: 明确事件为空；若没有这行代码，用户会误以为命令失败。
        return  # 新增代码+TerminalStatusUI: 空事件直接返回；若没有这行代码，后续循环没有意义。
    for event in events:  # 新增代码+TerminalStatusUI: 遍历事件列表；若没有这行代码，终端无法展示每条事件。
        print(f"- #{event.get('sequence', '')} {event.get('event_type', '')} session={event.get('session_id', '')} run={event.get('run_id', '')} turn={event.get('turn_id', '')}")  # 新增代码+TerminalStatusUI: 打印事件关键索引；若没有这行代码，用户无法判断任务卡在哪个 run/turn。


def _print_sessions_command(workspace: Path) -> None:  # 新增代码+TerminalStatusUI: 打印可恢复 session；若没有这行代码，/sessions 会和状态页重复实现。
    sessions = get_sessions(workspace)  # 新增代码+TerminalStatusUI: 从 SDK 读取 session 列表；若没有这行代码，终端 session 视图会和 API 不一致。
    print("\nSessions")  # 新增代码+TerminalStatusUI: 输出 session 区块标题；若没有这行代码，用户不知道下面是恢复入口。
    if not sessions:  # 新增代码+TerminalStatusUI: 检查 session 是否为空；若没有这行代码，空列表时没有明确反馈。
        print("- (empty)")  # 新增代码+TerminalStatusUI: 明确没有 session；若没有这行代码，用户可能以为命令没执行。
        return  # 新增代码+TerminalStatusUI: 空 session 直接返回；若没有这行代码，后续循环无意义。
    for session_id in sessions:  # 新增代码+TerminalStatusUI: 遍历 session id；若没有这行代码，终端无法展示可恢复会话。
        print(f"- session_id={session_id}")  # 新增代码+TerminalStatusUI: 打印可复制 session id；若没有这行代码，用户无法执行 /resume。


def _print_resume_command(workspace: Path, user_input: str) -> None:  # 新增代码+TerminalStatusUI: 打印指定 session 的恢复报告；若没有这行代码，/resume 命令没有实现位置。
    parts = user_input.split(maxsplit=1)  # 新增代码+TerminalStatusUI: 从命令中拆出 session_id；若没有这行代码，/resume 不知道目标会话。
    if len(parts) < 2 or not parts[1].strip():  # 新增代码+TerminalStatusUI: 检查用户是否传 session_id；若没有这行代码，缺参会变成难懂错误。
        print("\nResume Report\n- 缺少 session_id，用法：/resume <session_id>")  # 新增代码+TerminalStatusUI: 给出清楚用法；若没有这行代码，小白用户不知道怎么修正。
        return  # 新增代码+TerminalStatusUI: 缺参时停止处理；若没有这行代码，后面会用空 id 查询。
    report = load_resume_report(workspace, parts[1].strip())  # 新增代码+TerminalStatusUI: 通过 SDK 读取恢复报告；若没有这行代码，终端 resume 会绕过真实 ResumeLoader。
    print("\nResume Report")  # 新增代码+TerminalStatusUI: 输出恢复报告标题；若没有这行代码，用户不知道下面是恢复结果。
    print(json.dumps(report, ensure_ascii=False, indent=2)[:4000])  # 新增代码+TerminalStatusUI: 打印结构化报告并限长；若没有这行代码，大报告会刷屏或不可读。


def _print_compact_command(workspace: Path) -> None:  # 新增代码+TerminalStatusUI: 打印 compact/resume 状态块；若没有这行代码，/compact 会重复解析完整状态页。
    snapshot = build_status_snapshot(workspace)  # 新增代码+TerminalStatusUI: 从统一快照读取 compact 信息；若没有这行代码，终端 compact 状态会和 /status 不一致。
    compact_block = snapshot.get("compact", {})  # 新增代码+TerminalStatusUI: 取 compact 区块；若没有这行代码，用户需要在完整 JSON 里翻找。
    resume_block = snapshot.get("resume", {})  # 新增代码+TerminalStatusUI: 取 resume 区块；若没有这行代码，compact 后续恢复风险不可见。
    print("\nCompact / Resume")  # 新增代码+TerminalStatusUI: 输出 compact 区块标题；若没有这行代码，终端输出不易扫描。
    print(json.dumps({"compact": compact_block, "resume": resume_block}, ensure_ascii=False, indent=2)[:4000])  # 新增代码+TerminalStatusUI: 打印压缩和恢复状态并限长；若没有这行代码，用户看不到 boundary/retry 等证据。


def _chrome_native_host_target_dir(workspace: Path) -> Path:  # 新增代码+Phase9ChromeTerminalActions: 统一计算 native host 预览输出目录；如果没有这段函数，/chrome 子命令会到处手写路径。
    if Path(workspace).name == "learning_agent":  # 新增代码+Phase9ChromeTerminalActions: 识别 start_oauth_agent.bat 已经传入 learning_agent 目录的真实场景；如果没有这行代码，路径会变成 learning_agent/learning_agent。
        return Path(workspace) / "memory" / "chrome_native_host"  # 新增代码+Phase9ChromeTerminalActions: 在已有 learning_agent 工作区下写 memory；如果没有这行代码，真实终端预览文件会落到双层目录。
    return Path(workspace) / "learning_agent" / "memory" / "chrome_native_host"  # 新增代码+Phase9ChromeTerminalActions: 把 manifest/launcher 放到项目内存目录；如果没有这行代码，预览文件位置不稳定也不方便排查。


def _chrome_native_host_script_path(workspace: Path) -> Path:  # 新增代码+Phase9ChromeTerminalActions: 统一计算 native host Python 脚本路径；如果没有这段函数，launcher 可能指向错误入口。
    workspace_script = Path(workspace) / "browser_extension_host" / "native_host.py" if Path(workspace).name == "learning_agent" else Path(workspace) / "learning_agent" / "browser_extension_host" / "native_host.py"  # 修改代码+Phase9ChromeTerminalActions: 同时兼容 repo 根目录和 learning_agent 目录；如果没有这行代码，真实 bat 启动会指向双层路径。
    if workspace_script.exists():  # 新增代码+Phase9ChromeTerminalActions: 检查工作区脚本是否真实存在；如果没有这行代码，测试临时目录会得到不存在路径。
        return workspace_script  # 新增代码+Phase9ChromeTerminalActions: 返回工作区脚本；如果没有这行代码，真实项目预览不会指向当前源码。
    return Path(__file__).resolve().parents[1] / "browser_extension_host" / "native_host.py"  # 新增代码+Phase9ChromeTerminalActions: 临时工作区回退到当前包源码；如果没有这行代码，单元测试无法生成可理解 launcher。

def _chrome_bridge_state_path(workspace: Path) -> Path:  # 新增代码+Phase15ChromePairingTrigger: 统一计算 Chrome extension bridge 状态文件路径；如果没有这段函数，配对触发可能写到 learning_agent/learning_agent 双层目录。
    if Path(workspace).name == "learning_agent":  # 新增代码+Phase15ChromePairingTrigger: 识别真实 bat 传入包目录的场景；如果没有这行代码，真实终端会写错 bridge 位置。
        return Path(workspace) / "memory" / "chrome_extension_bridge.json"  # 新增代码+Phase15ChromePairingTrigger: 包目录 workspace 直接写 memory；如果没有这行代码，扩展和状态页读不到同一文件。
    return Path(workspace) / "learning_agent" / "memory" / "chrome_extension_bridge.json"  # 新增代码+Phase15ChromePairingTrigger: repo 根目录 workspace 写入包内 memory；如果没有这行代码，Codex/测试从仓库根调用时路径不稳定。

def _chrome_runtime_queue_dir(workspace: Path) -> Path:  # 新增代码+Phase16SessionSyncClosure: 统一计算 runtime queue 目录；如果没有这段函数，自检命令可能把 prompt 写到错误 memory 路径。
    if Path(workspace).name == "learning_agent":  # 新增代码+Phase16SessionSyncClosure: 识别真实 bat 传入包目录的场景；如果没有这行代码，真实终端自检会写到双层目录。
        return Path(workspace) / "memory" / "runtime"  # 新增代码+Phase16SessionSyncClosure: 包目录 workspace 直接使用 memory/runtime；如果没有这行代码，主循环读不到自检命令。
    return Path(workspace) / "learning_agent" / "memory" / "runtime"  # 新增代码+Phase16SessionSyncClosure: repo 根目录 workspace 写入包内 runtime；如果没有这行代码，测试和真实状态路径会分裂。


def _chrome_action_json(data: dict[str, object]) -> str:  # 新增代码+Phase9ChromeTerminalActions: 把动作结果格式化成稳定 JSON；如果没有这段函数，终端输出和测试断言会各写一套格式。
    return json.dumps(data, ensure_ascii=False, indent=2)  # 新增代码+Phase9ChromeTerminalActions: 保留中文并缩进显示；如果没有这行代码，小白用户很难读懂安装审计结果。


def _format_chrome_action_result(action_name: str, payload: dict[str, object] | str) -> str:  # 新增代码+Phase9ChromeTerminalActions: 包装 /chrome 动作输出；如果没有这段函数，install/repair/uninstall 的终端样式不统一。
    if isinstance(payload, str):  # 新增代码+Phase9ChromeTerminalActions: repair_hint 返回文本而不是字典；如果没有这行代码，字符串会被当成 JSON 字典处理。
        body = payload  # 新增代码+Phase9ChromeTerminalActions: 直接使用修复建议文本；如果没有这行代码，用户看不到自然语言建议。
    else:  # 新增代码+Phase9ChromeTerminalActions: 字典 payload 走结构化格式；如果没有这行代码，安装审计记录无法清楚显示。
        dry_run_summary = f"- dry_run={str(payload.get('dry_run', '')).lower()}\n" if "dry_run" in payload else ""  # 新增代码+Phase9ChromeTerminalActions: 为 dry-run 单独加一行人类可读摘要；如果没有这行代码，用户要在 JSON 里找安全边界。
        manifest_summary = f"- manifest_path={payload.get('manifest_path')}\n" if payload.get("manifest_path") else ""  # 新增代码+Phase9ChromeTerminalActions: 单独展示未转义的 manifest 路径；如果没有这行代码，Windows 反斜杠在 JSON 里会显得难读。
        launcher_summary = f"- launcher_path={payload.get('launcher_path')}\n" if payload.get("launcher_path") else ""  # 新增代码+Phase9ChromeTerminalActions: 单独展示未转义的 launcher 路径；如果没有这行代码，用户不容易确认 .cmd 入口。
        body = dry_run_summary + manifest_summary + launcher_summary + _chrome_action_json(payload)  # 修改代码+Phase9ChromeTerminalActions: 输出摘要加完整审计 JSON；如果没有这行代码，结果既不够直观也不够可审计。
    return f"Chrome Action\n- action={action_name}\n{body}\n"  # 新增代码+Phase9ChromeTerminalActions: 返回动作标题、名称和正文；如果没有这行代码，用户不知道命令执行结果属于哪个动作。


def _format_chrome_pairing_diagnose(workspace: Path) -> str:  # 新增代码+Phase14ChromePairingDiagnose: 生成 Chrome extension 配对诊断文本；如果没有这段函数，用户只能看到 paired=false 却不知道原因。
    snapshot = build_status_snapshot(workspace)  # 新增代码+Phase14ChromePairingDiagnose: 读取统一状态快照；如果没有这行代码，诊断会和 /chrome 事实源分裂。
    browser = snapshot.get("browser", {}) if isinstance(snapshot.get("browser", {}), dict) else {}  # 新增代码+Phase14ChromePairingDiagnose: 安全读取 browser 区块；如果没有这行代码，坏快照会导致诊断崩溃。
    provider_status = browser.get("provider_status", {}) if isinstance(browser.get("provider_status", {}), dict) else {}  # 新增代码+Phase14ChromePairingDiagnose: 安全读取 provider_status；如果没有这行代码，缺状态时会抛异常。
    extension = provider_status.get("chrome_extension", {}) if isinstance(provider_status.get("chrome_extension", {}), dict) else {}  # 新增代码+Phase14ChromePairingDiagnose: 安全读取 extension 状态；如果没有这行代码，诊断拿不到 paired/session。
    native_host = provider_status.get("native_host", {}) if isinstance(provider_status.get("native_host", {}), dict) else {}  # 新增代码+Phase14ChromePairingDiagnose: 安全读取 native host 状态；如果没有这行代码，诊断拿不到 installer_state。
    bridge_path = Path(str(extension.get("bridge_state_file") or native_host.get("bridge_state_file") or ""))  # 新增代码+Phase14ChromePairingDiagnose: 定位 bridge 状态文件；如果没有这行代码，无法区分缺文件和缺字段。
    bridge_exists = bridge_path.exists() if str(bridge_path) else False  # 新增代码+Phase14ChromePairingDiagnose: 判断 bridge 文件是否存在；如果没有这行代码，用户不知道 extension 是否写过状态。
    connected = bool(extension.get("connected", False))  # 新增代码+Phase14ChromePairingDiagnose: 读取 extension 连接状态；如果没有这行代码，诊断无法说明插件是否在线。
    paired = bool(extension.get("paired", False))  # 新增代码+Phase14ChromePairingDiagnose: 读取配对状态；如果没有这行代码，诊断无法判断是否已完成 session sync。
    device_id = str(extension.get("device_id", "") or "")  # 新增代码+Phase14ChromePairingDiagnose: 读取 device id；如果没有这行代码，诊断无法指出设备字段是否缺失。
    session_id = str(extension.get("session_id", "") or "")  # 新增代码+Phase14ChromePairingDiagnose: 读取 session id；如果没有这行代码，诊断无法指出 session sync 是否缺失。
    allowed_origin_count = int(extension.get("allowed_origin_count", 0) or 0)  # 新增代码+Phase14ChromePairingDiagnose: 读取 allowed origin 数量；如果没有这行代码，诊断无法说明扩展来源边界。
    last_seen_at = str(extension.get("last_seen_at", "") or "")  # 新增代码+Phase14ChromePairingDiagnose: 读取最近同步时间；如果没有这行代码，诊断无法说明状态是否新鲜。
    installer_state = str(native_host.get("installer_state", "") or "")  # 新增代码+Phase14ChromePairingDiagnose: 读取 native host 安装状态；如果没有这行代码，诊断无法判断是否应先安装。
    reasons: list[str] = []  # 新增代码+Phase14ChromePairingDiagnose: 准备原因分类列表；如果没有这行代码，诊断无法累计多个缺失项。
    if installer_state not in {"manifest_created", "registry_registered"}:  # 新增代码+Phase14ChromePairingDiagnose: native host 未准备好时记录原因；如果没有这行代码，用户会直接尝试配对但 host 不可用。
        reasons.append("native_host_not_ready")  # 新增代码+Phase14ChromePairingDiagnose: 标记 native host 未准备；如果没有这行代码，诊断结果不够具体。
    if not bridge_exists:  # 新增代码+Phase14ChromePairingDiagnose: bridge 文件不存在表示 extension/native host 尚未写状态；如果没有这行代码，缺文件原因不可见。
        reasons.append("bridge_file_missing")  # 新增代码+Phase14ChromePairingDiagnose: 标记 bridge 文件缺失；如果没有这行代码，用户不知道先检查 extension。
    if bridge_exists and not connected:  # 新增代码+Phase14ChromePairingDiagnose: 文件存在但未连接表示 extension 可能离线；如果没有这行代码，连接问题会被误判配对问题。
        reasons.append("extension_not_connected")  # 新增代码+Phase14ChromePairingDiagnose: 标记扩展未连接；如果没有这行代码，用户不知道要刷新/重载扩展。
    if not device_id:  # 新增代码+Phase14ChromePairingDiagnose: 缺 device id 表示配对摘要不完整；如果没有这行代码，配对缺字段不可见。
        reasons.append("device_id_missing")  # 新增代码+Phase14ChromePairingDiagnose: 标记 device_id 缺失；如果没有这行代码，用户不知道配对设备未写入。
    if not session_id:  # 新增代码+Phase14ChromePairingDiagnose: 缺 session id 表示 session sync 未闭环；如果没有这行代码，同步失败点不可见。
        reasons.append("session_id_missing")  # 新增代码+Phase14ChromePairingDiagnose: 标记 session_id 缺失；如果没有这行代码，用户不知道 session sync 未完成。
    if allowed_origin_count <= 0:  # 新增代码+Phase14ChromePairingDiagnose: allowed origins 为空会导致扩展来源不可审计；如果没有这行代码，来源边界缺失不可见。
        reasons.append("allowed_origins_empty")  # 新增代码+Phase14ChromePairingDiagnose: 标记 allowed origins 为空；如果没有这行代码，用户不知道扩展 origin 未保存。
    if not last_seen_at:  # 新增代码+Phase14ChromePairingDiagnose: 缺最近同步时间表示状态可能从未更新；如果没有这行代码，状态新鲜度不可见。
        reasons.append("last_seen_missing")  # 新增代码+Phase14ChromePairingDiagnose: 标记 last_seen 缺失；如果没有这行代码，用户不知道 bridge 是否活跃过。
    if paired and not reasons:  # 新增代码+Phase14ChromePairingDiagnose: 已配对且无缺失时给完成态；如果没有这行代码，成功状态也会显得异常。
        next_step = "session sync 已连接，可继续使用浏览器侧任务同步。"  # 新增代码+Phase14ChromePairingDiagnose: 成功态下一步；如果没有这行代码，用户不知道可以继续使用。
    elif installer_state == "not_installed":  # 新增代码+Phase14ChromePairingDiagnose: 未安装时先做安全预览；如果没有这行代码，用户可能直接尝试配对。
        next_step = "/chrome install-preview"  # 新增代码+Phase14ChromePairingDiagnose: 未安装下一步；如果没有这行代码，首次修复没有入口。
    elif installer_state == "manifest_created":  # 新增代码+Phase14ChromePairingDiagnose: manifest 已生成但未注册时提示确认安装；如果没有这行代码，用户会停在 preview 状态。
        next_step = "/chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY"  # 新增代码+Phase14ChromePairingDiagnose: 注册下一步；如果没有这行代码，配对前 host 不会注册。
    elif not bridge_exists or not connected:  # 新增代码+Phase14ChromePairingDiagnose: host 已注册但 extension 未连上时提示打开/重载扩展；如果没有这行代码，用户不知道检查浏览器侧。
        next_step = "打开或重载 Chrome extension，并确认 native host 允许连接。"  # 新增代码+Phase14ChromePairingDiagnose: 连接问题下一步；如果没有这行代码，诊断没有行动建议。
    else:  # 新增代码+Phase14ChromePairingDiagnose: 其他缺字段情况进入配对触发阶段；如果没有这行代码，半配对状态没有下一步。
        next_step = "进入 Phase 15 pairing trigger：生成或刷新配对请求。"  # 新增代码+Phase14ChromePairingDiagnose: 半配对下一步；如果没有这行代码，用户不知道该刷新配对。
    lines = ["pairing_diagnose"]  # 新增代码+Phase14ChromePairingDiagnose: 输出诊断标题；如果没有这行代码，验收器无法稳定识别诊断结果。
    lines.append(f"installer_state={installer_state}")  # 新增代码+Phase14ChromePairingDiagnose: 输出安装状态；如果没有这行代码，用户不知道 native host 是否准备好。
    lines.append(f"bridge_file_exists={str(bridge_exists).lower()} bridge_state_file={bridge_path}")  # 新增代码+Phase14ChromePairingDiagnose: 输出 bridge 文件状态；如果没有这行代码，用户无法定位状态文件。
    lines.append(f"connected={str(connected).lower()} paired={str(paired).lower()}")  # 新增代码+Phase14ChromePairingDiagnose: 输出连接和配对布尔值；如果没有这行代码，核心状态不可见。
    lines.append(f"device_id={device_id}")  # 新增代码+Phase14ChromePairingDiagnose: 输出 device id；如果没有这行代码，用户无法识别配对设备。
    lines.append(f"session_id={session_id}")  # 新增代码+Phase14ChromePairingDiagnose: 输出 session id；如果没有这行代码，session sync 不可审计。
    lines.append(f"allowed_origin_count={allowed_origin_count}")  # 新增代码+Phase14ChromePairingDiagnose: 输出 allowed origin 数量；如果没有这行代码，来源边界不可见。
    lines.append(f"last_seen_at={last_seen_at}")  # 新增代码+Phase14ChromePairingDiagnose: 输出最近同步时间；如果没有这行代码，用户无法判断状态是否新鲜。
    for reason in reasons:  # 新增代码+Phase14ChromePairingDiagnose: 遍历所有原因分类；如果没有这行代码，多重缺失只能显示一个。
        lines.append(f"reason={reason}")  # 新增代码+Phase14ChromePairingDiagnose: 输出单个原因；如果没有这行代码，诊断不可操作。
    lines.append(f"next={next_step}")  # 新增代码+Phase14ChromePairingDiagnose: 输出下一步建议；如果没有这行代码，诊断后仍然不知道怎么修。
    return "\n".join(lines) + "\n"  # 新增代码+Phase14ChromePairingDiagnose: 返回多行诊断文本；如果没有这行代码，终端不会显示结果。

def _pairing_request_preview_payload() -> dict[str, object]:  # 新增代码+Phase15ChromePairingTrigger: 生成只读配对请求预览；如果没有这段函数，preview 和 confirm 会重复构造请求字段。
    now = int(time.time())  # 新增代码+Phase15ChromePairingTrigger: 记录预览时间；如果没有这行代码，用户无法判断请求是否新鲜。
    return {"dry_run": True, "pairing_request_id": f"chrome-pair-preview-{now}-{uuid4().hex[:8]}", "request_nonce_preview": uuid4().hex[:16], "created_at": now, "will_write_bridge": False, "confirm_command": f"/chrome pairing-start-confirm {CHROME_PAIRING_CONFIRM_TOKEN}"}  # 新增代码+Phase15ChromePairingTrigger: 返回预览摘要；如果没有这行代码，用户看不到确认命令和安全边界。

def _format_chrome_pairing_preview() -> str:  # 新增代码+Phase15ChromePairingTrigger: 渲染配对触发预览；如果没有这段函数，用户无法安全查看即将创建的请求形状。
    payload = _pairing_request_preview_payload()  # 新增代码+Phase15ChromePairingTrigger: 生成预览 payload；如果没有这行代码，输出没有 request id 和确认命令。
    return "\n".join(["Chrome Action", "- action=chrome_pairing_preview", "- dry_run=true", f"- pairing_request_id={payload['pairing_request_id']}", f"- request_nonce_preview={payload['request_nonce_preview']}", f"- confirm_command={payload['confirm_command']}", _chrome_action_json(payload)]) + "\n"  # 新增代码+Phase15ChromePairingTrigger: 返回稳定多行预览；如果没有这行代码，验收器和用户都难以确认只读边界。

def _format_chrome_pairing_start_confirm(workspace: Path, confirm_token: str) -> str:  # 新增代码+Phase15ChromePairingTrigger: 强确认后写入待配对请求；如果没有这段函数，终端无法触发扩展刷新配对。
    if confirm_token != CHROME_PAIRING_CONFIRM_TOKEN:  # 新增代码+Phase15ChromePairingTrigger: 检查固定确认 token；如果没有这行代码，误输入可能写入 bridge 状态。
        return f"Chrome Action\n- action=chrome_pairing_start_confirm\n- 已拒绝执行：需要显式确认 token。\n- 用法：/chrome pairing-start-confirm {CHROME_PAIRING_CONFIRM_TOKEN}\n- 说明：该命令只写入本地 bridge 的 pending pairing request，不写 Windows registry。\n"  # 新增代码+Phase15ChromePairingTrigger: 返回拒绝说明；如果没有这行代码，小白用户不知道如何修正命令。
    bridge = ChromeExtensionBridgeState(_chrome_bridge_state_path(workspace))  # 新增代码+Phase15ChromePairingTrigger: 打开真实 bridge 状态对象；如果没有这行代码，请求无法持久化给 native host/extension。
    request = bridge.start_pairing_request(source="chrome_terminal")  # 新增代码+Phase15ChromePairingTrigger: 写入 pending pairing request；如果没有这行代码，扩展轮询拿不到触发信号。
    payload = {"dry_run": False, "bridge_state_file": str(_chrome_bridge_state_path(workspace)), "pending_pairing_request_id": request.get("request_id", ""), "pending_pairing_request_status": request.get("status", ""), "pending_pairing_request_created_at": request.get("created_at", ""), "next": "打开或重载 Chrome extension，等待 native host poll_commands 下发 pairing_request。"}  # 新增代码+Phase15ChromePairingTrigger: 构造审计 payload；如果没有这行代码，用户看不到写入位置和下一步。
    return "\n".join(["Chrome Action", "- action=chrome_pairing_start_confirm", "- dry_run=false", f"- bridge_state_file={payload['bridge_state_file']}", f"- pending_pairing_request_id={payload['pending_pairing_request_id']}", f"- pending_pairing_request_status={payload['pending_pairing_request_status']}", f"- pending_pairing_request_created_at={payload['pending_pairing_request_created_at']}", f"- next={payload['next']}", _chrome_action_json(payload)]) + "\n"  # 新增代码+Phase15ChromePairingTrigger: 返回确认写入结果；如果没有这行代码，用户无法确认触发是否成功。

def _format_chrome_session_sync_selftest(workspace: Path) -> str:  # 新增代码+Phase16SessionSyncClosure: 模拟浏览器侧 prompt 并证明 durable queue 入队；如果没有这段函数，真实终端无法验收 session sync 闭环。
    bridge = ChromeExtensionBridgeState(_chrome_bridge_state_path(workspace))  # 新增代码+Phase16SessionSyncClosure: 打开 bridge 状态对象；如果没有这行代码，自检无法写 last_browser_prompt 证据。
    queue = RuntimeCommandQueue(_chrome_runtime_queue_dir(workspace))  # 新增代码+Phase16SessionSyncClosure: 打开 runtime queue；如果没有这行代码，自检不能证明 durable command 存在。
    result = bridge.enqueue_browser_prompt(queue, {"prompt": "Phase16 session sync selftest", "url": "https://session-sync.local/selftest", "title": "Session Sync Selftest", "selected_text": "selftest-selected-text", "tab_id": "chrome-tab-selftest"})  # 新增代码+Phase16SessionSyncClosure: 写入模拟浏览器 prompt；如果没有这行代码，终端自检没有真实入队动作。
    command_id = str(result.get("command_id", "") or "")  # 新增代码+Phase16SessionSyncClosure: 读取入队 command id；如果没有这行代码，输出无法定位 durable 命令。
    queue_command_exists = any(command.command_id == command_id for command in queue.list_commands())  # 新增代码+Phase16SessionSyncClosure: 确认 command 真实存在于队列；如果没有这行代码，自检可能只返回假 id。
    payload = {"mode": result.get("mode", ""), "last_browser_prompt_id": command_id, "last_browser_prompt_url": result.get("url", ""), "queue_command_exists": queue_command_exists, "queue_dir": str(_chrome_runtime_queue_dir(workspace)), "bridge_state_file": str(_chrome_bridge_state_path(workspace))}  # 新增代码+Phase16SessionSyncClosure: 构造自检审计 payload；如果没有这行代码，用户看不到队列和 bridge 的证据路径。
    return "\n".join(["Chrome Action", "- action=chrome_session_sync_selftest", f"- mode={payload['mode']}", f"- last_browser_prompt_id={payload['last_browser_prompt_id']}", f"- last_browser_prompt_url={payload['last_browser_prompt_url']}", f"- queue_command_exists={str(bool(payload['queue_command_exists'])).lower()}", f"- queue_dir={payload['queue_dir']}", f"- bridge_state_file={payload['bridge_state_file']}", _chrome_action_json(payload)]) + "\n"  # 新增代码+Phase16SessionSyncClosure: 返回稳定自检结果；如果没有这行代码，真实终端看不到 session sync 证明。


def _format_chrome_extension_e2e_check(workspace: Path, installer: Any) -> str:  # 新增代码+Phase18ChromeExtensionE2E: 生成 Chrome extension/native host/session sync 端到端证据；如果没有这段函数，Phase 18 只能靠分散命令手工拼证据。
    status_before = build_status_snapshot(workspace)  # 新增代码+Phase18ChromeExtensionE2E: 先读取真实状态快照；如果没有这行代码，自检写入后可能把模拟连接误判为真实扩展连接。
    extension_before = status_before.get("browser", {}).get("provider_status", {}).get("chrome_extension", {}) if isinstance(status_before.get("browser", {}), dict) else {}  # 新增代码+Phase18ChromeExtensionE2E: 安全提取真实扩展状态；如果没有这行代码，缺字段会导致端到端检查崩溃。
    real_extension_connected = bool(extension_before.get("connected", False)) if isinstance(extension_before, dict) else False  # 新增代码+Phase18ChromeExtensionE2E: 记录真实扩展是否已连接；如果没有这行代码，local selftest 会被误说成真实浏览器已连。
    extension_id = str(extension_before.get("extension_id", "") or "abcdefghijklmnopabcdefghijklmnop") if isinstance(extension_before, dict) else "abcdefghijklmnopabcdefghijklmnop"  # 新增代码+Phase18ChromeExtensionE2E: 优先使用真实扩展 id，缺失时用预览 id；如果没有这行代码，manifest allowed_origins 无法稳定生成。
    install_payload = installer.install(extension_id=extension_id, python_executable=sys.executable, host_script=_chrome_native_host_script_path(workspace), dry_run=True)  # 新增代码+Phase18ChromeExtensionE2E: 生成 manifest 和 launcher 但不写 registry；如果没有这行代码，native host 启动链路没有文件证据。
    manifest_path = Path(str(install_payload.get("manifest_path", "")))  # 新增代码+Phase18ChromeExtensionE2E: 读取 manifest 路径；如果没有这行代码，后续无法检查 Chrome native host 配置文件。
    launcher_path = manifest_path.with_suffix(".cmd")  # 新增代码+Phase18ChromeExtensionE2E: 推导 launcher 路径；如果没有这行代码，无法确认 manifest 指向的本地入口存在。
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}  # 新增代码+Phase18ChromeExtensionE2E: 读取 manifest JSON；如果没有这行代码，只能证明文件存在不能证明内容可解析。
    manifest_ok = bool(manifest_data.get("name")) and str(manifest_data.get("path", "")) == str(launcher_path)  # 新增代码+Phase18ChromeExtensionE2E: 校验 manifest 名称和 launcher 指向；如果没有这行代码，坏 manifest 也可能通过。
    launcher_text = launcher_path.read_text(encoding="utf-8") if launcher_path.exists() else ""  # 新增代码+Phase18ChromeExtensionE2E: 读取 launcher 内容；如果没有这行代码，空壳 launcher 也可能被当成成功。
    launcher_ok = launcher_path.exists() and "native_host.py" in launcher_text  # 新增代码+Phase18ChromeExtensionE2E: 确认 launcher 会启动 native_host.py；如果没有这行代码，Chrome 可能找得到 cmd 却启动错入口。
    selftest_bridge_path = Path(workspace) / "memory" / "chrome_extension_e2e_selftest" / "chrome_extension_bridge.json"  # 新增代码+Phase18ChromeExtensionE2E: 使用隔离 bridge 文件；如果没有这行代码，自检会污染真实扩展连接状态。
    bridge = ChromeExtensionBridgeState(selftest_bridge_path)  # 新增代码+Phase18ChromeExtensionE2E: 创建自检 bridge；如果没有这行代码，pairing 和 prompt 链路无法形成统一证据。
    request = bridge.start_pairing_request(source="phase18_e2e_check")  # 新增代码+Phase18ChromeExtensionE2E: 创建 pending pairing request；如果没有这行代码，无法证明终端触发和扩展配对请求可衔接。
    pairing = bridge.record_pairing({"extension_id": extension_id, "device_id": f"phase18-device-{extension_id[:8]}", "session_id": f"phase18-session-{request.get('request_id', '')}", "allowed_origins": [f"chrome-extension://{extension_id}/"], "request_id": request.get("request_id", ""), "request_nonce": request.get("request_nonce", "")})  # 新增代码+Phase18ChromeExtensionE2E: 模拟扩展回传脱敏 pairing 摘要；如果没有这行代码，pending 请求不会闭合成 completed。
    pairing_status = bridge.pairing_request_summary().get("status", "")  # 新增代码+Phase18ChromeExtensionE2E: 读取闭合后的 pairing request 状态；如果没有这行代码，无法确认 pending 是否完成。
    pairing_completed = bool(pairing.get("device_id")) and str(pairing_status) == "completed"  # 新增代码+Phase18ChromeExtensionE2E: 计算配对闭环是否完成；如果没有这行代码，输出无法作为 verifier 证据。
    queue = RuntimeCommandQueue(_chrome_runtime_queue_dir(workspace))  # 新增代码+Phase18ChromeExtensionE2E: 打开真实 durable runtime queue；如果没有这行代码，browser prompt 不能进入主循环可恢复队列。
    prompt_result = bridge.enqueue_browser_prompt(queue, {"prompt": "Phase18 Chrome extension E2E selftest", "url": "https://extension-e2e.local/selftest", "title": "Extension E2E Selftest", "selected_text": "phase18-selected-text", "tab_id": "chrome-tab-phase18"})  # 新增代码+Phase18ChromeExtensionE2E: 通过 bridge 写入浏览器侧 prompt；如果没有这行代码，session sync 缺少 durable 入队证据。
    prompt_command_id = str(prompt_result.get("command_id", "") or "")  # 新增代码+Phase18ChromeExtensionE2E: 读取入队命令 id；如果没有这行代码，无法在队列里复查对应命令。
    browser_prompt_queued = any(command.command_id == prompt_command_id for command in queue.list_commands())  # 新增代码+Phase18ChromeExtensionE2E: 二次确认 command 真在队列中；如果没有这行代码，输出可能只是返回了未落盘 id。
    real_extension_e2e = real_extension_connected and manifest_ok and launcher_ok and pairing_completed and browser_prompt_queued  # 新增代码+Phase18ChromeExtensionE2E: 只有真实扩展已连接且本地链路全通才标真实 E2E；如果没有这行代码，local selftest 会被误当完成态。
    payload = {"manifest_ok": manifest_ok, "launcher_ok": launcher_ok, "pairing_completed": pairing_completed, "browser_prompt_queued": browser_prompt_queued, "real_extension_connected": real_extension_connected, "real_extension_e2e": real_extension_e2e, "e2e_level": "real_extension_observed" if real_extension_connected else "local_protocol_selftest", "manifest_path": str(manifest_path), "launcher_path": str(launcher_path), "selftest_bridge_state_file": str(selftest_bridge_path), "runtime_queue_dir": str(_chrome_runtime_queue_dir(workspace)), "last_browser_prompt_id": prompt_command_id}  # 新增代码+Phase18ChromeExtensionE2E: 汇总机器可读证据；如果没有这行代码，报告和截图缺少统一字段。
    return "\n".join(["Chrome Action", "- action=chrome_extension_e2e_check", f"- manifest_ok={str(bool(payload['manifest_ok'])).lower()}", f"- launcher_ok={str(bool(payload['launcher_ok'])).lower()}", f"- pairing_completed={str(bool(payload['pairing_completed'])).lower()}", f"- browser_prompt_queued={str(bool(payload['browser_prompt_queued'])).lower()}", f"- real_extension_connected={str(bool(payload['real_extension_connected'])).lower()}", f"- real_extension_e2e={str(bool(payload['real_extension_e2e'])).lower()}", f"- e2e_level={payload['e2e_level']}", f"- manifest_path={payload['manifest_path']}", f"- launcher_path={payload['launcher_path']}", f"- selftest_bridge_state_file={payload['selftest_bridge_state_file']}", f"- runtime_queue_dir={payload['runtime_queue_dir']}", f"- last_browser_prompt_id={payload['last_browser_prompt_id']}", _chrome_action_json(payload)]) + "\n"  # 新增代码+Phase18ChromeExtensionE2E: 返回稳定多行证据；如果没有这行代码，真实终端和 verifier 无法审计 Phase 18。


def _format_chrome_real_extension_e2e_check(workspace: Path, installer: Any) -> str:  # 新增代码+Phase24RealExtensionE2E: 只读取真实扩展 bridge 的端到端状态；如果没有这段函数，Phase 24 会继续停留在模拟自检。
    status_snapshot = build_status_snapshot(workspace)  # 新增代码+Phase24RealExtensionE2E: 读取统一状态事实源；如果没有这行代码，命令会绕过 /chrome 当前真实状态。
    browser = status_snapshot.get("browser", {}) if isinstance(status_snapshot.get("browser", {}), dict) else {}  # 新增代码+Phase24RealExtensionE2E: 安全读取 browser 区块；如果没有这行代码，缺失状态会导致命令崩溃。
    provider_status = browser.get("provider_status", {}) if isinstance(browser.get("provider_status", {}), dict) else {}  # 新增代码+Phase24RealExtensionE2E: 安全读取 provider 状态；如果没有这行代码，扩展和 native host 字段不可见。
    extension = provider_status.get("chrome_extension", {}) if isinstance(provider_status.get("chrome_extension", {}), dict) else {}  # 新增代码+Phase24RealExtensionE2E: 读取真实扩展状态；如果没有这行代码，无法判断 real_extension_connected。
    native_host = provider_status.get("native_host", {}) if isinstance(provider_status.get("native_host", {}), dict) else {}  # 新增代码+Phase24RealExtensionE2E: 读取 native host 状态；如果没有这行代码，无法定位 bridge 文件和 installer 状态。
    bridge_state_file = Path(str(native_host.get("bridge_state_file", _chrome_bridge_state_path(workspace)) or _chrome_bridge_state_path(workspace)))  # 新增代码+Phase24RealExtensionE2E: 定位真实 bridge 文件；如果没有这行代码，workspace lock 无法验证。
    runtime_queue_dir = _chrome_runtime_queue_dir(workspace)  # 新增代码+Phase24RealExtensionE2E: 定位真实 runtime queue；如果没有这行代码，browser prompt 入队证据无法复查。
    queue = RuntimeCommandQueue(runtime_queue_dir)  # 新增代码+Phase24RealExtensionE2E: 打开 durable queue；如果没有这行代码，只能看 bridge 摘要不能确认命令是否存在。
    last_browser_prompt_id = str(extension.get("last_browser_prompt_id", "") or "")  # 新增代码+Phase24RealExtensionE2E: 读取最后一个 Chrome 侧 prompt id；如果没有这行代码，无法关联 bridge 和 queue。
    browser_prompt_queued = bool(last_browser_prompt_id) and any(command.command_id == last_browser_prompt_id for command in queue.list_commands())  # 新增代码+Phase24RealExtensionE2E: 确认 Chrome prompt 真实进入队列；如果没有这行代码，bridge 里的旧字段可能被误当入队成功。
    real_extension_connected = bool(extension.get("connected", False))  # 新增代码+Phase24RealExtensionE2E: 读取真实扩展连接状态；如果没有这行代码，不能区分真实连接和本地自检。
    paired = bool(extension.get("paired", False))  # 新增代码+Phase24RealExtensionE2E: 读取真实配对状态；如果没有这行代码，连接后是否完成 session sync 不可见。
    workspace_lock_ok = bridge_state_file == _chrome_bridge_state_path(workspace) and runtime_queue_dir == _chrome_runtime_queue_dir(workspace)  # 新增代码+Phase24RealExtensionE2E: 验证 bridge 和 queue 属于同一工作区；如果没有这行代码，Chrome host 写错目录会被漏掉。
    installer_status = installer.status()  # 新增代码+Phase24RealExtensionE2E: 读取 native host 注册状态；如果没有这行代码，真实扩展失败时无法判断是否因为未注册。
    real_extension_e2e = real_extension_connected and paired and browser_prompt_queued and workspace_lock_ok  # 新增代码+Phase24RealExtensionE2E: 只有真实连接、配对、prompt 入队和路径一致都满足才算真实 E2E；如果没有这行代码，部分成功会被误报完成。
    payload = {"real_extension_connected": real_extension_connected, "paired": paired, "browser_prompt_queued": browser_prompt_queued, "workspace_lock_ok": workspace_lock_ok, "real_extension_e2e": real_extension_e2e, "installer_state": installer_status.get("state", ""), "bridge_state_file": str(bridge_state_file), "expected_bridge_state_file": str(_chrome_bridge_state_path(workspace)), "runtime_queue_dir": str(runtime_queue_dir), "last_browser_prompt_id": last_browser_prompt_id, "extension_id": extension.get("extension_id", ""), "session_id": extension.get("session_id", ""), "last_seen_at": extension.get("last_seen_at", "")}  # 新增代码+Phase24RealExtensionE2E: 汇总机器可读证据；如果没有这行代码，验收器和用户都只能读散落字段。
    return "\n".join(["Chrome Action", "- action=phase24_real_extension_e2e_check", f"- real_extension_connected={str(bool(payload['real_extension_connected'])).lower()}", f"- paired={str(bool(payload['paired'])).lower()}", f"- browser_prompt_queued={str(bool(payload['browser_prompt_queued'])).lower()}", f"- workspace_lock_ok={str(bool(payload['workspace_lock_ok'])).lower()}", f"- real_extension_e2e={str(bool(payload['real_extension_e2e'])).lower()}", f"- installer_state={payload['installer_state']}", f"- bridge_state_file={payload['bridge_state_file']}", f"- expected_bridge_state_file={payload['expected_bridge_state_file']}", f"- runtime_queue_dir={payload['runtime_queue_dir']}", f"- last_browser_prompt_id={payload['last_browser_prompt_id']}", f"- extension_id={payload['extension_id']}", f"- session_id={payload['session_id']}", f"- last_seen_at={payload['last_seen_at']}", _chrome_action_json(payload)]) + "\n"  # 新增代码+Phase24RealExtensionE2E: 返回稳定多行真实扩展 E2E 证据；如果没有这行代码，真实终端无法验收 Phase 24。


def _computer_lock_root(workspace: Path) -> Path:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，计算 Computer Use 锁目录；如果没有这段函数，/computer 命令会在 repo 根和 learning_agent 目录之间写错位置。
    if Path(workspace).name == "learning_agent":  # 新增代码+Phase31ComputerUseLockAbortEvidence: 判断 start_oauth_agent.bat 是否传入 learning_agent 目录；如果没有这行代码，真实终端路径会变成双层 learning_agent。
        return Path(workspace) / "memory" / "computer_use" / "locks"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回 learning_agent 内部 memory 锁目录；如果没有这行代码，真实终端 abort flag 不会和控制器使用同一位置。
    return Path(workspace) / "learning_agent" / "memory" / "computer_use" / "locks"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回 repo 根下的锁目录；如果没有这行代码，单元测试和项目根运行会找不到锁状态。
# 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，_computer_lock_root 到此结束；如果没有这个边界说明，初学者不容易看出路径选择范围。


def _computer_action_json(payload: dict[str, Any]) -> str:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，把 /computer 结果转成 JSON 行；如果没有这段函数，验收器很难读取结构化证据。
    return "JSON=" + json.dumps(payload, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 输出稳定 JSON 证据；如果没有这行代码，只能解析人类文本。
# 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，_computer_action_json 到此结束；如果没有这个边界说明，读者不容易看出结构化输出范围。


def _format_computer_lock_action(action: str, payload: dict[str, Any]) -> str:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，格式化 Computer Use 锁和 abort 状态；如果没有这段函数，每个子命令会重复拼接终端输出。
    status = payload.get("status", payload) if isinstance(payload, dict) else {}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 兼容 acquire/release 包裹状态和直接 status；如果没有这行代码，不同子命令输出会不一致。
    status = dict(status) if isinstance(status, dict) else {}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 确保 status 是可索引字典；如果没有这行代码，异常 payload 会导致格式化崩溃。
    lines = ["Computer Action"]  # 新增代码+Phase31ComputerUseLockAbortEvidence: 输出固定标题供验收器匹配；如果没有这行代码，真实终端测试无法确认进入 /computer 面板。
    lines.append(f"- action={action}")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 显示本次子命令；如果没有这行代码，用户看不出执行了 status 还是 abort。
    lines.append(f"- locked={str(bool(status.get('locked', False))).lower()}")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 显示桌面锁是否被持有；如果没有这行代码，用户不知道是否能安全执行动作。
    lines.append(f"- stale={str(bool(status.get('stale', False))).lower()}")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 显示锁是否陈旧；如果没有这行代码，崩溃遗留锁风险不可见。
    lines.append(f"- owner_session_id={status.get('owner_session_id', '')}")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 显示当前 owner；如果没有这行代码，锁冲突时不知道是谁占用。
    lines.append(f"- abort_requested={str(bool(status.get('abort_requested', False))).lower()}")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 显示急停是否触发；如果没有这行代码，用户无法确认下一次动作会被阻断。
    lines.append(f"- abort_reason={status.get('abort_reason', '')}")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 显示急停原因；如果没有这行代码，后续恢复时不知道为什么中断。
    lines.append(f"- state_path={status.get('state_path', '')}")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 显示锁状态文件路径；如果没有这行代码，排查持锁问题时找不到文件。
    lines.append(f"- abort_path={status.get('abort_path', '')}")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 显示 abort 文件路径；如果没有这行代码，排查急停问题时找不到文件。
    lines.append(_computer_action_json({"action": action, "payload": payload, "status": status}))  # 新增代码+Phase31ComputerUseLockAbortEvidence: 附加结构化 JSON；如果没有这行代码，验收器只能依赖脆弱文本。
    return "\n".join(lines) + "\n"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回完整终端文本；如果没有这行代码，调用方无法打印或写入事件。
# 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，_format_computer_lock_action 到此结束；如果没有这个边界说明，读者不容易看出输出格式化范围。


def is_computer_terminal_command(user_command: str) -> bool:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，判断用户输入是否属于 /computer 命令；如果没有这段函数，真实终端命令会被误发给模型。
    command = str(user_command or "").strip().lower()  # 新增代码+Phase31ComputerUseLockAbortEvidence: 规范化命令文本；如果没有这行代码，大小写或空白会影响识别。
    return command in {"/computer", "computer"} or command.startswith("/computer ") or command.startswith("computer ") or command.startswith("/computer/")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 同时识别状态和子命令；如果没有这行代码，/computer abort 不会进入本地安全入口。
# 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，is_computer_terminal_command 到此结束；如果没有这个边界说明，读者不容易看出命令识别范围。


def run_computer_terminal_command(workspace: Path, user_input: str) -> str:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，执行 `/computer` 子命令；如果没有这段函数，真实用户无法在终端查看或触发桌面急停。
    command_parts = str(user_input or "").strip().split(maxsplit=2)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 拆分命令、子命令和原因文本；如果没有这行代码，abort reason 会被截断或无法读取。
    subcommand = command_parts[1].lower() if len(command_parts) >= 2 else "status"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 默认无子命令时显示 status；如果没有这行代码，输入 /computer 会得到空行为。
    lock_manager = ComputerUseLockManager(base_dir=_computer_lock_root(Path(workspace)))  # 新增代码+Phase31ComputerUseLockAbortEvidence: 打开当前工作区的桌面锁管理器；如果没有这行代码，命令无法读取真实 lock/abort 文件。
    if subcommand in {"status", ""}:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 识别状态查询；如果没有这行代码，用户无法只读查看 Computer Use 状态。
        approval_lines = WindowsComputerUseApprovalModel().terminal_status_lines()  # 新增代码+Phase38WindowsComputerApproval: 生成默认审批模型的终端摘要；如果没有这行代码，用户看不到 Phase38 approval 状态。
        return _format_computer_lock_action("status", lock_manager.status()) + "\n".join(approval_lines) + "\n"  # 修改代码+Phase38WindowsComputerApproval: 返回锁状态并追加 approval 摘要；如果没有这行代码，/computer status 只能看到 lock/abort 看不到 session allowlist。
    if subcommand == "abort":  # 新增代码+Phase31ComputerUseLockAbortEvidence: 识别急停请求；如果没有这行代码，用户无法从终端阻断下一次桌面动作。
        reason = command_parts[2].strip() if len(command_parts) >= 3 else "terminal abort"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 读取可选急停原因；如果没有这行代码，abort 记录缺少上下文。
        return _format_computer_lock_action("abort", lock_manager.request_abort(reason, requested_by="terminal"))  # 新增代码+Phase31ComputerUseLockAbortEvidence: 写入急停并返回状态；如果没有这行代码，abort 命令只是空打印不会生效。
    if subcommand in {"clear-abort", "clear"}:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 识别清除急停命令；如果没有这行代码，用户无法恢复后续安全动作。
        return _format_computer_lock_action("clear-abort", lock_manager.clear_abort(cleared_by="terminal"))  # 新增代码+Phase31ComputerUseLockAbortEvidence: 清除 abort 并返回状态；如果没有这行代码，急停会一直阻断动作。
    if subcommand == "release":  # 新增代码+Phase31ComputerUseLockAbortEvidence: 识别释放桌面锁命令；如果没有这行代码，用户无法从终端释放默认会话锁。
        session_id = command_parts[2].strip() if len(command_parts) >= 3 else "learning-agent-default-session"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 读取释放会话，默认使用生产会话；如果没有这行代码，release 不知道释放哪个 owner。
        return _format_computer_lock_action("release", lock_manager.release(session_id))  # 新增代码+Phase31ComputerUseLockAbortEvidence: 执行释放并返回状态；如果没有这行代码，锁残留时用户只能手删文件。
    return "Computer Action\n- 不支持的 /computer 子命令。\n- 可用命令：/computer、/computer status、/computer abort <reason>、/computer clear-abort、/computer release [session_id]\n"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回清楚用法；如果没有这行代码，输错命令会让小白用户不知道怎么修正。
# 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，run_computer_terminal_command 到此结束；如果没有这个边界说明，读者不容易看出终端命令处理范围。


def _print_computer_command(workspace: Path, user_input: str = "/computer") -> str:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，打印并返回 `/computer` 结果；如果没有这段函数，验收事件无法拿到真实终端输出。
    computer_output = run_computer_terminal_command(workspace, user_input)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 先保存命令输出；如果没有这行代码，打印后无法把同一份文本写入事件。
    print("\n" + computer_output, end="")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 把结果显示在真实终端；如果没有这行代码，用户看不到 Computer Use 锁和 abort 状态。
    return computer_output  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回输出供验收事件保存；如果没有这行代码，controller 无法断言 abort_requested=true。
# 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，_print_computer_command 到此结束；如果没有这个边界说明，读者不容易看出打印 helper 范围。


def is_chrome_terminal_command(user_command: str) -> bool:  # 新增代码+Phase13ChromePairingGuide: 判断用户输入是否属于 /chrome 命令；如果没有这段函数，真实终端重复粘连输入会误进模型调用。
    command = str(user_command or "").strip().lower()  # 新增代码+Phase13ChromePairingGuide: 规范化输入；如果没有这行代码，大小写或空白会影响识别。
    return command in {"/chrome", "chrome"} or command.startswith("/chrome ") or command.startswith("chrome ") or command.startswith("/chrome/")  # 新增代码+Phase13ChromePairingGuide: 同时识别正常子命令和 /chrome/chrome 重复粘连；如果没有这行代码，验收控制器重复输入会失败。


def run_chrome_terminal_command(workspace: Path, user_input: str, registry_adapter: Any | None = None) -> str:  # 修改代码+Phase10ChromeInstallConfirm: 执行 `/chrome` 子命令并允许测试注入 fake registry；如果没有这段函数，终端动作无法被单元测试和真实终端复用。
    command_parts = str(user_input or "").strip().split()  # 新增代码+Phase9ChromeTerminalActions: 拆分用户输入；如果没有这行代码，无法识别 install-preview/repair 等子命令。
    if len(command_parts) <= 1:  # 新增代码+Phase9ChromeTerminalActions: 没有子命令时保留原 `/chrome` 状态页行为；如果没有这行代码，老用户习惯会被破坏。
        status_snapshot = build_status_snapshot(workspace)  # 新增代码+ChromeTerminalUI: 从统一快照读取浏览器状态；若没有这行代码，/chrome 会和 SDK/API 事实源分裂。
        return render_chrome_status(status_snapshot)  # 新增代码+ChromeTerminalUI: 返回聚焦 Chrome 状态页；若没有这行代码，用户看不到 provider/native host/tab/权限摘要。
    subcommand = command_parts[1].lower()  # 新增代码+Phase9ChromeTerminalActions: 读取小写子命令；如果没有这行代码，大小写输入会导致重复判断。
    installer = ChromeNativeHostInstaller(_chrome_native_host_target_dir(workspace), registry_adapter=registry_adapter)  # 修改代码+Phase10ChromeInstallConfirm: 创建 native host 安装器并支持测试 fake registry；如果没有这行代码，install-confirm 测试会误碰真实系统。
    if subcommand == "install-preview":  # 新增代码+Phase9ChromeTerminalActions: 识别安全安装预览；如果没有这行代码，用户无法从终端生成 manifest/launcher。
        extension_id = command_parts[2] if len(command_parts) >= 3 else "abcdefghijklmnopabcdefghijklmnop"  # 新增代码+Phase9ChromeTerminalActions: 支持用户传扩展 ID，同时提供本地预览默认值；如果没有这行代码，命令缺参会失败。
        payload = installer.install(extension_id=extension_id, python_executable=sys.executable, host_script=_chrome_native_host_script_path(workspace), dry_run=True)  # 新增代码+Phase9ChromeTerminalActions: 生成 manifest/launcher 且不写 registry；如果没有这行代码，install-preview 只是空壳命令。
        payload["launcher_path"] = str(Path(str(payload.get("manifest_path", ""))).with_suffix(".cmd"))  # 新增代码+Phase9ChromeTerminalActions: 在终端结果里展示 launcher 路径；如果没有这行代码，用户看不到 Chrome 实际启动入口。
        return _format_chrome_action_result("browser_extension_install", payload)  # 新增代码+Phase9ChromeTerminalActions: 返回安装预览结果；如果没有这行代码，用户看不到 manifest 和 registry_targets。
    if subcommand == "install-confirm":  # 新增代码+Phase10ChromeInstallConfirm: 识别真实安装确认命令；如果没有这行代码，用户无法从终端完成生产 registry 注册。
        extension_id = command_parts[2] if len(command_parts) >= 3 else ""  # 新增代码+Phase10ChromeInstallConfirm: 读取扩展 ID；如果没有这行代码，allowed_origins 会缺少目标 Chrome extension。
        confirm_token = command_parts[3] if len(command_parts) >= 4 else ""  # 新增代码+Phase10ChromeInstallConfirm: 读取确认 token；如果没有这行代码，无法区分误输入和明确授权。
        if not extension_id or confirm_token != CHROME_INSTALL_CONFIRM_TOKEN:  # 新增代码+Phase10ChromeInstallConfirm: 强制同时提供扩展 ID 和固定 token；如果没有这行代码，真实 registry 写入风险过高。
            return f"Chrome Action\n- action=browser_extension_install_confirm\n- 已拒绝执行：需要显式确认 token，且必须提供 extension_id。\n- 用法：/chrome install-confirm <extension_id> {CHROME_INSTALL_CONFIRM_TOKEN}\n- 说明：该命令会写入当前用户 HKCU 下的 Chrome/Edge/Brave/Chromium NativeMessagingHosts registry。\n"  # 新增代码+Phase10ChromeInstallConfirm: 返回拒绝和用法说明；如果没有这行代码，小白用户不知道为什么没有安装。
        payload = installer.install(extension_id=extension_id, python_executable=sys.executable, host_script=_chrome_native_host_script_path(workspace), dry_run=False)  # 新增代码+Phase10ChromeInstallConfirm: 带强确认后执行真实安装路径；如果没有这行代码，install-confirm 永远无法注册 native host。
        payload["launcher_path"] = str(Path(str(payload.get("manifest_path", ""))).with_suffix(".cmd"))  # 新增代码+Phase10ChromeInstallConfirm: 展示真实 launcher 路径；如果没有这行代码，用户无法确认 Chrome 将启动哪个入口。
        return _format_chrome_action_result("browser_extension_install_confirm", payload)  # 新增代码+Phase10ChromeInstallConfirm: 返回确认安装审计结果；如果没有这行代码，用户看不到本次写入范围。
    if subcommand == "repair":  # 新增代码+Phase9ChromeTerminalActions: 识别修复建议命令；如果没有这行代码，用户无法在终端查询下一步。
        return _format_chrome_action_result("repair", installer.repair_hint())  # 新增代码+Phase9ChromeTerminalActions: 返回 native host 修复建议；如果没有这行代码，repair 命令没有实际输出。
    if subcommand == "pairing-diagnose":  # 新增代码+Phase14ChromePairingDiagnose: 识别 Chrome extension 配对诊断命令；如果没有这行代码，用户无法解释 paired=false。
        return _format_chrome_pairing_diagnose(workspace)  # 新增代码+Phase14ChromePairingDiagnose: 返回只读诊断结果；如果没有这行代码，诊断命令没有输出。
    if subcommand == "pairing-preview":  # 新增代码+Phase15ChromePairingTrigger: 识别只读配对触发预览；如果没有这行代码，用户无法安全查看 pairing request 形状。
        return _format_chrome_pairing_preview()  # 新增代码+Phase15ChromePairingTrigger: 返回不写 bridge 的预览结果；如果没有这行代码，preview 命令没有实际输出。
    if subcommand == "pairing-start-confirm":  # 新增代码+Phase15ChromePairingTrigger: 识别强确认配对触发命令；如果没有这行代码，终端无法写入 pending pairing request。
        confirm_token = command_parts[2] if len(command_parts) >= 3 else ""  # 新增代码+Phase15ChromePairingTrigger: 读取确认 token；如果没有这行代码，无法区分误输入和明确触发。
        return _format_chrome_pairing_start_confirm(workspace, confirm_token)  # 新增代码+Phase15ChromePairingTrigger: 执行配对触发确认逻辑；如果没有这行代码，pending 请求不会创建。
    if subcommand == "session-sync-selftest":  # 新增代码+Phase16SessionSyncClosure: 识别 session sync 终端自检命令；如果没有这行代码，真实终端无法证明浏览器 prompt 入队。
        return _format_chrome_session_sync_selftest(workspace)  # 新增代码+Phase16SessionSyncClosure: 执行自检并返回 durable queue 证据；如果没有这行代码，自检命令没有输出。
    if subcommand == "extension-e2e-check":  # 新增代码+Phase18ChromeExtensionE2E: 识别 Chrome extension 端到端证据检查命令；如果没有这行代码，真实终端无法一键验收 Phase 18 链路。
        return _format_chrome_extension_e2e_check(workspace, installer)  # 新增代码+Phase18ChromeExtensionE2E: 执行 manifest/pairing/prompt/真实连接边界检查；如果没有这行代码，Phase 18 输出没有统一证据。
    if subcommand == "real-extension-e2e-check":  # 新增代码+Phase24RealExtensionE2E: 识别真实 Chrome extension 闭环检查命令；如果没有这行代码，用户无法从终端验证真实扩展是否连上。
        return _format_chrome_real_extension_e2e_check(workspace, installer)  # 新增代码+Phase24RealExtensionE2E: 执行只读真实扩展证据检查；如果没有这行代码，Phase 24 命令不会产生输出。
    if subcommand == "uninstall-preview":  # 新增代码+Phase9ChromeTerminalActions: 识别安全卸载预览；如果没有这行代码，用户无法预演 registry 清理范围。
        payload = installer.uninstall(dry_run=True)  # 新增代码+Phase9ChromeTerminalActions: 生成卸载审计但不删除 registry；如果没有这行代码，卸载预览无法证明安全边界。
        return _format_chrome_action_result("browser_extension_uninstall", payload)  # 新增代码+Phase9ChromeTerminalActions: 返回卸载预览结果；如果没有这行代码，用户看不到将影响哪些 key。
    if subcommand == "uninstall-confirm":  # 新增代码+Phase11ChromeUninstallConfirm: 识别真实卸载确认命令；如果没有这行代码，用户无法从终端回滚 registry 注册。
        confirm_token = command_parts[2] if len(command_parts) >= 3 else ""  # 新增代码+Phase11ChromeUninstallConfirm: 读取删除确认 token；如果没有这行代码，无法区分误输入和明确授权。
        if confirm_token != CHROME_UNINSTALL_CONFIRM_TOKEN:  # 新增代码+Phase11ChromeUninstallConfirm: 强制固定 token 才允许删除 registry；如果没有这行代码，真实卸载风险过高。
            return f"Chrome Action\n- action=browser_extension_uninstall_confirm\n- 已拒绝执行：需要显式确认 token。\n- 用法：/chrome uninstall-confirm {CHROME_UNINSTALL_CONFIRM_TOKEN}\n- 说明：该命令会删除当前用户 HKCU 下的 Chrome/Edge/Brave/Chromium NativeMessagingHosts registry。\n"  # 新增代码+Phase11ChromeUninstallConfirm: 返回拒绝和用法说明；如果没有这行代码，小白用户不知道为什么没有卸载。
        payload = installer.uninstall(dry_run=False)  # 新增代码+Phase11ChromeUninstallConfirm: 带强确认后执行真实卸载路径；如果没有这行代码，uninstall-confirm 永远无法回滚 native host。
        return _format_chrome_action_result("browser_extension_uninstall_confirm", payload)  # 新增代码+Phase11ChromeUninstallConfirm: 返回确认卸载审计结果；如果没有这行代码，用户看不到本次删除范围。
    return f"Chrome Action\n- 不支持的 /chrome 子命令。\n- 可用命令：/chrome、/chrome install-preview [extension_id]、/chrome install-confirm <extension_id> {CHROME_INSTALL_CONFIRM_TOKEN}、/chrome repair、/chrome pairing-diagnose、/chrome pairing-preview、/chrome pairing-start-confirm {CHROME_PAIRING_CONFIRM_TOKEN}、/chrome session-sync-selftest、/chrome extension-e2e-check、/chrome real-extension-e2e-check、/chrome uninstall-preview、/chrome uninstall-confirm {CHROME_UNINSTALL_CONFIRM_TOKEN}\n"  # 修改代码+Phase24RealExtensionE2E: 给未知命令返回包含真实扩展 E2E 检查的清楚用法；如果没有这行代码，输错命令会漏掉 Phase 24 入口。


def _print_chrome_command(workspace: Path, user_input: str = "/chrome") -> str:  # 修改代码+Phase24AcceptancePayload: 打印并返回 `/chrome` 状态或子命令结果；若没有这段代码，验收事件无法拿到终端真实输出，false 也可能被事件误判为通过。
    chrome_output = run_chrome_terminal_command(workspace, user_input)  # 修改代码+Phase24AcceptancePayload: 先保存 `/chrome` 输出文本；若没有这行代码，打印之后就无法把同一份结果写入 acceptance event。
    print("\n" + chrome_output, end="")  # 修改代码+Phase24AcceptancePayload: 把结果显示给真实终端用户；若没有这行代码，用户只能从事件文件看结果而看不到屏幕输出。
    return chrome_output  # 修改代码+Phase24AcceptancePayload: 返回同一份输出给调用方写入事件；若没有这行代码，controller 不能断言 real_extension_e2e=true。


def run_interactive_session(agent: Any, workspace: Path, visible_tools: list[str], max_turns: int | None, prompt_soft_token_limit: int) -> None:  # 新增代码+AppSplit: 运行用户可见交互式终端循环；若没有这行代码，main 仍要承载所有交互逻辑。
    print("模型-工具循环轮次策略：" + format_max_turns_status(max_turns))  # 新增代码+AppSplit: 启动时显示当前轮次策略；若没有这行代码，用户不知道配置文件、环境变量或 CLI 是否生效。
    print(f"提示词软预算：约 {prompt_soft_token_limit} tokens")  # 新增代码+AppSplit: 启动时显示 prompt compact 预算；若没有这行代码，用户不知道当前是否会触发提示词压缩。
    print("模型当前可见工具：" + ", ".join(visible_tools))  # 新增代码+AppSplit: 显示模型本轮能看到的全部工具名；若没有这行代码，用户无法确认 web_search/fetch_url 是否进入工具列表。
    print("Learning Agent 已启动。输入 exit 或 quit 退出。")  # 新增代码+AppSplit: 显示启动提示；若没有这行代码，用户不知道终端已准备好。
    while True:  # 新增代码+AppSplit: 开始命令行交互循环；若没有这行代码，agent 只能回答一次或直接退出。
        emit_acceptance_event("agent_ready_for_user_prompt", {"workspace": str(workspace), "visible_tools": visible_tools})  # 新增代码+AppSplit: 在显示输入提示前写 ready 事件；若没有这行代码，外部 agent 无法稳定知道何时输入任务 prompt。
        user_input = input("\n你 > ").strip()  # 新增代码+AppSplit: 读取用户输入并清理空白；若没有这行代码，终端无法接收真实用户任务。
        if user_input.lower() in {"exit", "quit"}:  # 新增代码+AppSplit: 判断用户是否要退出；若没有这行代码，用户无法自然结束交互。
            print("再见。")  # 新增代码+AppSplit: 打印退出提示；若没有这行代码，用户不知道程序是否正常结束。
            return  # 新增代码+AppSplit: 结束交互函数；若没有这行代码，退出命令后仍会继续循环。
        if not user_input:  # 新增代码+AppSplit: 跳过空输入；若没有这行代码，空白回车会触发无意义模型调用。
            continue  # 新增代码+AppSplit: 等待下一次输入；若没有这行代码，空输入会继续向下执行。
        user_command = user_input.lower()  # 新增代码+TerminalStatusUI: 统一小写命令文本；若没有这行代码，每个命令都要重复 lower 判断。
        if user_command in {"/status", "status"}:  # 新增代码+StatusEcosystem: 识别终端状态命令；若没有这行代码，用户只能通过外部 CLI 才能看状态。
            status_snapshot = build_status_snapshot(workspace)  # 新增代码+StatusEcosystem: 从当前工作区读取统一状态；若没有这行代码，/status 没有数据来源。
            print("\n" + render_status_snapshot(status_snapshot), end="")  # 新增代码+StatusEcosystem: 打印人类可读状态页；若没有这行代码，终端用户看不到 run/task/queue/session。
            emit_acceptance_event("status_snapshot_printed", {"workspace": str(workspace), "counts": status_snapshot.get("counts", {})})  # 新增代码+StatusEcosystem: 记录状态页已打印；若没有这行代码，真实验收无法证明 /status 生效。
            continue  # 新增代码+StatusEcosystem: 状态命令处理后回到输入循环；若没有这行代码，/status 会继续被当成模型 prompt。
        if user_command in {"/events", "events"}:  # 新增代码+TerminalStatusUI: 识别终端事件命令；若没有这行代码，用户无法在真实终端查看事件流。
            _print_events_command(workspace)  # 新增代码+TerminalStatusUI: 打印最近状态事件；若没有这行代码，/events 命令不会输出内容。
            emit_acceptance_event("status_events_printed", {"workspace": str(workspace)})  # 新增代码+TerminalStatusUI: 写入事件视图验收记录；若没有这行代码，控制器无法证明 /events 被执行。
            continue  # 新增代码+TerminalStatusUI: 事件命令处理完返回循环；若没有这行代码，/events 会被当成 prompt 发送给模型。
        if user_command in {"/sessions", "sessions"}:  # 新增代码+TerminalStatusUI: 识别 session 列表命令；若没有这行代码，用户不能快速发现可恢复会话。
            _print_sessions_command(workspace)  # 新增代码+TerminalStatusUI: 打印 session 列表；若没有这行代码，/sessions 不会输出恢复入口。
            emit_acceptance_event("status_sessions_printed", {"workspace": str(workspace)})  # 新增代码+TerminalStatusUI: 写入 session 视图验收记录；若没有这行代码，真实终端验收缺证据。
            continue  # 新增代码+TerminalStatusUI: session 命令处理完返回循环；若没有这行代码，/sessions 会进入模型。
        if user_command.startswith("/resume ") or user_command.startswith("resume "):  # 新增代码+TerminalStatusUI: 识别 resume 报告命令；若没有这行代码，用户无法在终端审计恢复报告。
            _print_resume_command(workspace, user_input)  # 新增代码+TerminalStatusUI: 打印指定 session 的恢复报告；若没有这行代码，/resume 没有实际行为。
            emit_acceptance_event("status_resume_printed", {"workspace": str(workspace), "command": user_input[:200]})  # 新增代码+TerminalStatusUI: 写入 resume 视图验收记录；若没有这行代码，控制器不知道查了哪个 session。
            continue  # 新增代码+TerminalStatusUI: resume 命令处理后返回循环；若没有这行代码，/resume 会被发给模型。
        if user_command in {"/compact", "compact"}:  # 新增代码+TerminalStatusUI: 识别 compact 状态命令；若没有这行代码，用户无法快速查看压缩/恢复状态。
            _print_compact_command(workspace)  # 新增代码+TerminalStatusUI: 打印 compact/resume 状态块；若没有这行代码，/compact 不会输出证据。
            emit_acceptance_event("status_compact_printed", {"workspace": str(workspace)})  # 新增代码+TerminalStatusUI: 写入 compact 视图验收记录；若没有这行代码，真实终端验收缺少状态命令证据。
            continue  # 新增代码+TerminalStatusUI: compact 命令处理后返回循环；若没有这行代码，/compact 会被发给模型。
        if is_computer_terminal_command(user_command):  # 新增代码+Phase31ComputerUseLockAbortEvidence: 识别 Computer Use 锁和 abort 命令；如果没有这行代码，/computer abort 会被误发给模型。
            computer_output = _print_computer_command(workspace, user_input)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 打印并保留 `/computer` 输出；如果没有这行代码，事件只能证明命令执行过却不能证明 abort 状态。
            emit_acceptance_event("computer_status_printed", {"workspace": str(workspace), "command": user_input[:200], "output_text": computer_output[:8000]})  # 新增代码+Phase31ComputerUseLockAbortEvidence: 写入 Computer Use 输出供 controller 断言；如果没有这行代码，真实终端验收无法证明 abort_requested=true。
            continue  # 新增代码+Phase31ComputerUseLockAbortEvidence: /computer 命令处理后回到输入循环；如果没有这行代码，命令还会进入模型调用。
        if is_chrome_terminal_command(user_command):  # 修改代码+Phase13ChromePairingGuide: 识别 Chrome 状态命令、子命令和重复粘连命令；若没有这行代码，/chrome install-preview 或 /chrome/chrome 会被误发给模型。
            chrome_output = _print_chrome_command(workspace, user_input)  # 修改代码+Phase24AcceptancePayload: 打印并保留本次 `/chrome` 输出；若没有这行代码，事件只能证明命令执行过，不能证明输出内容为 true。
            emit_acceptance_event("chrome_status_printed", {"workspace": str(workspace), "command": user_input[:200], "output_text": chrome_output[:8000]})  # 修改代码+Phase24AcceptancePayload: 写入 `/chrome` 输出文本供 controller 断言；若没有这行代码，real_extension_e2e=false 也可能靠状态事件误通过。
            continue  # 新增代码+ChromeTerminalUI: /chrome 命令处理后返回循环；若没有这行代码，/chrome 会继续进入模型调用。
        emit_acceptance_event("user_prompt_received", {"length": len(user_input), "prompt_preview": user_input[:200]})  # 新增代码+AppSplit: 记录输入长度和短预览；若没有这行代码，控制器无法确认真实终端收到的是哪条任务。
        answer = agent.run(user_input, max_turns=max_turns)  # 新增代码+AppSplit: 调用 agent 主循环生成最终回答；若没有这行代码，交互终端不会真正工作。
        print(f"\nAgent > {answer}")  # 新增代码+AppSplit: 打印最终回答给用户；若没有这行代码，用户看不到 agent 结果。
        final_answer_event_payload = build_final_answer_event_payload(answer)  # 新增代码+AppSplit: 组装最终回答验收 payload；若没有这行代码，完整 answer_text 字段会丢失。
        emit_acceptance_event("final_answer_printed", final_answer_event_payload)  # 新增代码+AppSplit: 写出最终回答事件；若没有这行代码，外部控制器无法稳定确认真实最终输出。
