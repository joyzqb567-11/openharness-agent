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
    from learning_agent.app.computer_status_renderer import render_computer_status  # 新增代码+Phase51ComputerStatusUI: 导入 /computer 专用状态渲染器；如果没有这行代码，/computer status 无法显示紧凑状态面板。
    from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+Phase15ChromePairingTrigger: 导入 bridge 状态对象；如果没有这行代码，终端无法写入待配对请求。
    from learning_agent.browser_extension_host.manifest_installer import ChromeNativeHostInstaller  # 新增代码+Phase9ChromeTerminalActions: 导入 native host 安装器；如果没有这行代码，/chrome install-preview 只能显示文案不能生成 manifest。
    from learning_agent.computer_use.approval import WindowsComputerUseApprovalModel  # 新增代码+Phase38WindowsComputerApproval: 导入 Windows approval 终端状态模型；如果没有这行代码，/computer status 无法显示 session allowlist 和 grant flags。
    from learning_agent.computer_use.abort_streaming_hooks import WindowsComputerUseAbortStreamingHooks  # 新增代码+Phase61AbortStreamingHooks: 导入 abort/cleanup/streaming hook 状态模型；如果没有这行代码，/computer abort-hooks 和 /computer status 无法显示中断钩子。
    from learning_agent.computer_use.high_level_tools import WindowsHighLevelComputerToolRuntime  # 新增代码+Phase62HighLevelTools: 导入高层 Computer Tool 状态模型；如果没有这行代码，/computer high-level-tools 和 /computer status 无法显示 Phase62。
    from learning_agent.computer_use.controller_takeover import WindowsComputerUseControllerTakeoverDebugSurface  # 新增代码+Phase63ControllerTakeover: 导入外部 agent controller 接管调试面；如果没有这行代码，/computer controller 和 /computer status 无法显示 Phase63。
    from learning_agent.computer_use.controller import ComputerUseController  # 新增代码+Phase51ComputerStatusUI: 导入 Computer Use 控制器用于 `/computer observe` 只读入口；如果没有这行代码，observe 命令只能停留在文案。
    from learning_agent.computer_use.lock import ComputerUseLockManager  # 新增代码+Phase31ComputerUseLockAbortEvidence: 导入桌面锁管理器；如果没有这行代码，/computer 终端命令无法读取或修改 abort 状态。
    from learning_agent.computer_use.mode_session import ComputerUseModeSessionStore  # 新增代码+Phase98UniversalComputerUseMode: 导入通用 Computer Use 模式 session store；如果没有这行代码，/computer use 无法真实打开 normal/observe/full 模式状态。
    from learning_agent.computer_use.native_diagnostics import format_phase43_capability_matrix_lines, run_phase43_native_capability_matrix_contract  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 导入 Phase43 终端能力矩阵渲染入口；如果没有这行代码，/computer status 看不到 WGC/UIA/SendInput 差距。
    from learning_agent.computer_use.persistent_grants import WindowsComputerUsePersistentGrantStore  # 新增代码+Phase60PersistentGrants: 导入生产级持久授权 store；如果没有这行代码，/computer approve/grants/revoke 无法真正落盘和评估。
    from learning_agent.computer_use.security_policy import WindowsComputerUseSecurityPolicy  # 新增代码+Phase48WindowsSecurityPolicy: 导入 Phase48 安全策略终端状态模型；如果没有这行代码，/computer status 无法显示 grant_classes 和高风险默认拒绝。
    from learning_agent.computer_use.session_context import DEFAULT_SESSION_CONTEXT_ID, ComputerUseSessionContextStore  # 新增代码+Phase59SessionContextAppState: 导入统一 session context store；如果没有这行代码，/computer status 无法读取 allowed_apps/grants/display/screenshot/cleanup 同一事实源。
    from learning_agent.computer_use.session_runtime import WindowsComputerUseSessionRuntime, format_phase40_runtime_action, format_phase50_recovery_action  # 修改代码+Phase50WindowsRecovery: 导入 Phase40 会话运行时和 Phase50 恢复格式化器；如果没有这行代码，/computer recover/journal 无法显示恢复层。
    from learning_agent.computer_use.terminal_grants import ComputerUseTerminalGrantStore  # 新增代码+Phase51ComputerStatusUI: 导入终端授权草案 store；如果没有这行代码，/computer grant/revoke 无法跨命令显示。
    from learning_agent.app.status_renderer import render_status_snapshot  # 新增代码+StatusEcosystem: 导入终端状态渲染器；若没有这行代码，/status 无法显示统一状态页。
    from learning_agent.core.config import format_max_turns_status  # 新增代码+AppSplit: 导入轮次状态格式化；若没有这行代码，终端启动提示无法显示当前策略。
    from learning_agent.observability.acceptance_events import emit_acceptance_event  # 新增代码+AppSplit: 导入验收事件写入器；若没有这行代码，真实终端控制器无法知道何时输入 prompt。
    from learning_agent.observability.run_records import build_final_answer_event_payload  # 新增代码+AppSplit: 导入最终回答事件 payload helper；若没有这行代码，final_answer_printed 会丢完整回答字段。
    from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+Phase16SessionSyncClosure: 导入 durable runtime queue；如果没有这行代码，session-sync-selftest 无法证明浏览器 prompt 入队。
    from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+StatusEcosystem: 导入统一状态快照聚合器；若没有这行代码，/status 会读不到 run/task/queue/session。
    from learning_agent.sdk.status import get_sessions, list_status_events, load_resume_report  # 新增代码+TerminalStatusUI: 复用 SDK 状态入口；若没有这行代码，终端 /events、/sessions、/resume 会另写旁路读取逻辑。
except ModuleNotFoundError as error:  # 新增代码+AppSplit: 捕获脚本模式下包路径不可用；若没有这行代码，双击 bat 时交互层可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.app", "learning_agent.app.chrome_status_renderer", "learning_agent.app.computer_status_renderer", "learning_agent.app.status_renderer", "learning_agent.browser_extension_host", "learning_agent.browser_extension_host.bridge_server", "learning_agent.browser_extension_host.manifest_installer", "learning_agent.computer_use", "learning_agent.computer_use.approval", "learning_agent.computer_use.abort_streaming_hooks", "learning_agent.computer_use.high_level_tools", "learning_agent.computer_use.controller_takeover", "learning_agent.computer_use.controller", "learning_agent.computer_use.lock", "learning_agent.computer_use.mode_session", "learning_agent.computer_use.native_diagnostics", "learning_agent.computer_use.persistent_grants", "learning_agent.computer_use.security_policy", "learning_agent.computer_use.session_context", "learning_agent.computer_use.session_runtime", "learning_agent.computer_use.terminal_grants", "learning_agent.core", "learning_agent.core.config", "learning_agent.observability", "learning_agent.observability.acceptance_events", "learning_agent.observability.run_records", "learning_agent.runtime", "learning_agent.runtime.command_queue", "learning_agent.runtime.status_snapshot", "learning_agent.sdk", "learning_agent.sdk.status"}:  # 修改代码+Phase98UniversalComputerUseMode: 允许 mode_session 在脚本模式 fallback；若没有这行代码，bat 入口下 /computer use 会因为包路径缺失而启动失败。
        raise  # 新增代码+AppSplit: 重新抛出真实导入错误；若没有这行代码，观测层或配置层问题会被隐藏。
    from app.chrome_status_renderer import render_chrome_status  # 新增代码+ChromeTerminalUI: 脚本模式导入 /chrome 专用渲染器；若没有这行代码，直接运行时 /chrome 无法显示。
    from app.computer_status_renderer import render_computer_status  # 新增代码+Phase51ComputerStatusUI: 脚本模式导入 /computer 状态渲染器；如果没有这行代码，双击 bat 后 /computer status 无法显示紧凑面板。
    from browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+Phase15ChromePairingTrigger: 脚本模式导入 bridge 状态对象；如果没有这行代码，双击 bat 后 pairing-start-confirm 不可用。
    from browser_extension_host.manifest_installer import ChromeNativeHostInstaller  # 新增代码+Phase9ChromeTerminalActions: 脚本模式导入 native host 安装器；如果没有这行代码，双击 bat 后 /chrome install-preview 不可用。
    from computer_use.approval import WindowsComputerUseApprovalModel  # 新增代码+Phase38WindowsComputerApproval: 脚本模式导入 Windows approval 终端状态模型；如果没有这行代码，双击 bat 后 /computer status 看不到审批摘要。
    from computer_use.abort_streaming_hooks import WindowsComputerUseAbortStreamingHooks  # 新增代码+Phase61AbortStreamingHooks: 脚本模式导入 abort/cleanup/streaming hook 状态模型；如果没有这行代码，双击 bat 后 /computer abort-hooks 不可用。
    from computer_use.high_level_tools import WindowsHighLevelComputerToolRuntime  # 新增代码+Phase62HighLevelTools: 脚本模式导入高层 Computer Tool 状态模型；如果没有这行代码，双击 bat 后 /computer high-level-tools 不可用。
    from computer_use.controller_takeover import WindowsComputerUseControllerTakeoverDebugSurface  # 新增代码+Phase63ControllerTakeover: 脚本模式导入外部 agent controller 接管调试面；如果没有这行代码，双击 bat 后 /computer controller 不可用。
    from computer_use.controller import ComputerUseController  # 新增代码+Phase51ComputerStatusUI: 脚本模式导入 Computer Use 控制器；如果没有这行代码，双击 bat 后 /computer observe 不可用。
    from computer_use.lock import ComputerUseLockManager  # 新增代码+Phase31ComputerUseLockAbortEvidence: 脚本模式导入桌面锁管理器；如果没有这行代码，双击 bat 后 /computer abort 不可用。
    from computer_use.mode_session import ComputerUseModeSessionStore  # 新增代码+Phase98UniversalComputerUseMode: 脚本模式导入通用 Computer Use 模式 session store；如果没有这行代码，双击 bat 后 /computer use 不可用。
    from computer_use.native_diagnostics import format_phase43_capability_matrix_lines, run_phase43_native_capability_matrix_contract  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 脚本模式导入 Phase43 能力矩阵；如果没有这行代码，双击 bat 后 /computer status 看不到 native 能力矩阵。
    from computer_use.persistent_grants import WindowsComputerUsePersistentGrantStore  # 新增代码+Phase60PersistentGrants: 脚本模式导入持久授权 store；如果没有这行代码，双击 bat 后 /computer approve/grants/revoke 不可用。
    from computer_use.security_policy import WindowsComputerUseSecurityPolicy  # 新增代码+Phase48WindowsSecurityPolicy: 脚本模式导入 Phase48 安全策略模型；如果没有这行代码，双击 bat 后 /computer status 看不到 grant_classes。
    from computer_use.session_context import DEFAULT_SESSION_CONTEXT_ID, ComputerUseSessionContextStore  # 新增代码+Phase59SessionContextAppState: 脚本模式导入统一 session context store；如果没有这行代码，双击 bat 后 /computer status 读不到 AppState。
    from computer_use.session_runtime import WindowsComputerUseSessionRuntime, format_phase40_runtime_action, format_phase50_recovery_action  # 修改代码+Phase50WindowsRecovery: 脚本模式导入 Phase40/Phase50 运行时格式化器；如果没有这行代码，双击 bat 后 /computer recover/journal 不可用。
    from computer_use.terminal_grants import ComputerUseTerminalGrantStore  # 新增代码+Phase51ComputerStatusUI: 脚本模式导入终端授权草案 store；如果没有这行代码，双击 bat 后 /computer grant/revoke 不可用。
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


def _parse_phase60_persistent_grant_args(raw_text: str, default_scope: str = "observe") -> dict[str, Any]:  # 新增代码+Phase60PersistentGrants: 函数段开始，解析 /computer approve/deny 参数；如果没有这段函数，终端 UX 无法表达 ttl、scope、window、display 和 reason。
    tokens = str(raw_text or "").strip().split()  # 新增代码+Phase60PersistentGrants: 按空白拆分用户输入；如果没有这行代码，app 和 key=value 参数无法分离。
    app_key = tokens[0] if tokens else ""  # 新增代码+Phase60PersistentGrants: 第一个参数作为 app；如果没有这行代码，持久授权不知道目标应用。
    grant_flags: dict[str, bool] = {}  # 新增代码+Phase60PersistentGrants: 准备保存 desktopAction/systemKeyCombos 等 flags；如果没有这行代码，高风险显式授权无法表达。
    action_scope: list[str] = []  # 新增代码+Phase60PersistentGrants: 准备保存动作范围；如果没有这行代码，scope=click,type_text 无法传给 store。
    ttl_seconds = 900  # 新增代码+Phase60PersistentGrants: 默认 15 分钟授权；如果没有这行代码，approve 缺 ttl 时没有安全默认过期。
    reason_parts: list[str] = []  # 新增代码+Phase60PersistentGrants: 准备保存 reason 文本；如果没有这行代码，用户授权原因无法进入审计。
    window_id = ""  # 新增代码+Phase60PersistentGrants: 默认不绑定窗口；如果没有这行代码，缺 window= 参数会引用未定义变量。
    display_id = ""  # 新增代码+Phase60PersistentGrants: 默认不绑定显示器；如果没有这行代码，缺 display= 参数会引用未定义变量。
    for token in tokens[1:]:  # 新增代码+Phase60PersistentGrants: 遍历 app 之后的参数；如果没有这行代码，用户提供的 flags 和键值参数都会被忽略。
        if token.startswith("ttl="):  # 新增代码+Phase60PersistentGrants: 识别 ttl 秒数；如果没有这行代码，授权无法从终端设置有效期。
            try:  # 新增代码+Phase60PersistentGrants: 捕获用户输入非数字 ttl；如果没有这行代码，输错 ttl 会让命令崩溃。
                ttl_seconds = int(float(token.split("=", 1)[1]))  # 新增代码+Phase60PersistentGrants: 解析 ttl 值；如果没有这行代码，ttl 参数不会生效。
            except ValueError:  # 新增代码+Phase60PersistentGrants: 处理 ttl 解析失败；如果没有这行代码，用户拼错数字会得到异常堆栈。
                ttl_seconds = 900  # 新增代码+Phase60PersistentGrants: 解析失败时回到安全默认；如果没有这行代码，ttl 错误会留下不可预测状态。
        elif token.startswith("scope="):  # 新增代码+Phase60PersistentGrants: 识别动作范围；如果没有这行代码，用户无法限定 click/type_text。
            action_scope = [part.strip() for part in token.split("=", 1)[1].split(",") if part.strip()]  # 新增代码+Phase60PersistentGrants: 支持逗号分隔 scope；如果没有这行代码，多动作授权无法表达。
        elif token.startswith("window="):  # 新增代码+Phase60PersistentGrants: 识别窗口绑定；如果没有这行代码，用户无法把授权缩到某个 window_id。
            window_id = token.split("=", 1)[1].strip()  # 新增代码+Phase60PersistentGrants: 保存 window_id；如果没有这行代码，窗口级授权不会进入 store。
        elif token.startswith("display="):  # 新增代码+Phase60PersistentGrants: 识别显示器绑定；如果没有这行代码，多屏授权无法限定 display_id。
            display_id = token.split("=", 1)[1].strip()  # 新增代码+Phase60PersistentGrants: 保存 display_id；如果没有这行代码，显示器级授权不会进入 store。
        elif token.startswith("reason="):  # 新增代码+Phase60PersistentGrants: 识别授权原因；如果没有这行代码，审计记录缺少用户意图。
            reason_parts.append(token.split("=", 1)[1].strip())  # 新增代码+Phase60PersistentGrants: 保存 reason 文本；如果没有这行代码，reason=unit 会被当成 flag。
        elif token:  # 新增代码+Phase60PersistentGrants: 其他非空 token 视作 grant flag；如果没有这行代码，desktopAction/systemKeyCombos 无法用短写法输入。
            grant_flags[token] = True  # 新增代码+Phase60PersistentGrants: 启用对应 flag；如果没有这行代码，高风险显式授权不会生效。
    if not action_scope:  # 新增代码+Phase60PersistentGrants: 没有 scope 时使用保守默认；如果没有这行代码，空 scope 语义不清楚。
        action_scope = [default_scope]  # 新增代码+Phase60PersistentGrants: 默认只给 observe 或调用方指定范围；如果没有这行代码，approve 可能被误解为全权限。
    reason = " ".join(part for part in reason_parts if part) or "terminal persistent grant"  # 新增代码+Phase60PersistentGrants: 生成最终 reason；如果没有这行代码，审计记录可能为空。
    return {"app": app_key, "grant_flags": grant_flags, "action_scope": action_scope, "ttl_seconds": ttl_seconds, "reason": reason, "window_id": window_id, "display_id": display_id}  # 新增代码+Phase60PersistentGrants: 返回解析结果；如果没有这行代码，终端命令无法调用 store。
# 新增代码+Phase60PersistentGrants: 函数段结束，_parse_phase60_persistent_grant_args 到此结束；如果没有这个边界说明，读者不容易看出参数解析范围。


def _format_phase60_approve_output(result: dict[str, Any]) -> str:  # 新增代码+Phase60PersistentGrants: 函数段开始，格式化 /computer approve 输出；如果没有这段函数，用户看不到授权是否记录。
    missing = ",".join(list(result.get("missing_grant_flags", [])))  # 新增代码+Phase60PersistentGrants: 格式化缺失 flags；如果没有这行代码，高风险拒绝原因不易读。
    return f"Computer Approve\n- approve_recorded={str(bool(result.get('approved', False))).lower()}\n- decision={result.get('decision', '')}\n- app={result.get('app', '')}\n- grant_id={result.get('grant_id', '')}\n- missing_grant_flags={missing}\n- marker={result.get('marker', '')}\n- actions_expanded={str(bool(result.get('actions_expanded', False))).lower()}\n"  # 新增代码+Phase60PersistentGrants: 返回稳定 approve 面板；如果没有这行代码，真实终端验收无法匹配 approve_recorded=true。
# 新增代码+Phase60PersistentGrants: 函数段结束，_format_phase60_approve_output 到此结束；如果没有这个边界说明，读者不容易看出 approve 输出范围。


def _format_phase60_deny_output(result: dict[str, Any]) -> str:  # 新增代码+Phase60PersistentGrants: 函数段开始，格式化 /computer deny 输出；如果没有这段函数，用户看不到拒绝是否进入审计。
    return f"Computer Deny\n- denied_recorded={str(bool(result.get('denied_recorded', False))).lower()}\n- decision={result.get('decision', '')}\n- app={result.get('app', '')}\n- marker={result.get('marker', '')}\n- actions_expanded={str(bool(result.get('actions_expanded', False))).lower()}\n"  # 新增代码+Phase60PersistentGrants: 返回稳定 deny 面板；如果没有这行代码，真实终端无法显示拒绝记录。
# 新增代码+Phase60PersistentGrants: 函数段结束，_format_phase60_deny_output 到此结束；如果没有这个边界说明，读者不容易看出 deny 输出范围。


def _format_phase60_revoke_output(persistent_result: dict[str, Any], terminal_result: dict[str, Any]) -> str:  # 新增代码+Phase60PersistentGrants: 函数段开始，同时格式化持久授权和旧草案撤销结果；如果没有这段函数，Phase51/Phase60 revoke 兼容性会分散在主函数里。
    revoked = bool(persistent_result.get("revoked", False) or terminal_result.get("revoked", False))  # 新增代码+Phase60PersistentGrants: 合并两个撤销来源；如果没有这行代码，旧草案或新持久授权任一成功都无法统一显示。
    return f"Computer Revoke\n- revoked={str(revoked).lower()}\n- persistent_revoked={str(bool(persistent_result.get('revoked', False))).lower()}\n- terminal_revoked={str(bool(terminal_result.get('revoked', False))).lower()}\n- app_key={persistent_result.get('app', '') or terminal_result.get('app_key', '')}\n- grant_scope=phase60_persistent_and_terminal\n- terminal_grant_scope={terminal_result.get('grant_scope', '')}\n- marker={persistent_result.get('marker', '')}\n- actions_expanded={str(bool(persistent_result.get('actions_expanded', False) or terminal_result.get('actions_expanded', False))).lower()}\n"  # 新增代码+Phase60PersistentGrants: 返回稳定 revoke 面板；如果没有这行代码，真实终端不知道撤销了哪一层授权。
# 新增代码+Phase60PersistentGrants: 函数段结束，_format_phase60_revoke_output 到此结束；如果没有这个边界说明，读者不容易看出 revoke 输出范围。


def _phase98_bool(value: Any) -> str:  # 新增代码+Phase98UniversalComputerUseMode: 函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，Task3 输出可能出现 True/False 导致断言漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase98UniversalComputerUseMode: 返回 true 或 false；如果没有这行代码，终端输出大小写会不稳定。
# 新增代码+Phase98UniversalComputerUseMode: 函数段结束，_phase98_bool 到此结束；如果没有这个边界说明，读者不容易看出布尔格式化范围。


def _phase98_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase98UniversalComputerUseMode: 函数段开始，把命令输出里的数字字段安全转成 int；如果没有这段函数，坏 store 结果可能让 `/computer use` formatter 崩溃。
    try:  # 新增代码+Phase98UniversalComputerUseMode: 尝试按数字语义转换；如果没有这行代码，合法数字字符串无法被稳定显示。
        return int(float(value))  # 新增代码+Phase98UniversalComputerUseMode: 兼容 int、float 和数字字符串；如果没有这行代码，ttl_seconds 或事件数可能因类型不同输出漂移。
    except (TypeError, ValueError, OverflowError):  # 新增代码+Phase98UniversalComputerUseMode: 捕获 None、非数字字符串和无穷大；如果没有这行代码，异常会打断终端命令。
        return int(default)  # 新增代码+Phase98UniversalComputerUseMode: 返回安全默认值；如果没有这行代码，坏数字字段没有降级路径。
# 新增代码+Phase98UniversalComputerUseMode: 函数段结束，_phase98_safe_int 到此结束；如果没有这个边界说明，读者不容易看出命令数字容错范围。


def _phase98_csv(value: Any) -> str:  # 新增代码+Phase98UniversalComputerUseMode: 函数段开始，把动作列表转成人类可读逗号文本；如果没有这段函数，allowed_action_classes 会显示成难读的 Python 对象。
    items = value if isinstance(value, list) else []  # 新增代码+Phase98UniversalComputerUseMode: 只接受 list 输入；如果没有这行代码，坏状态可能让 join 崩溃。
    return ",".join(str(item) for item in items)  # 新增代码+Phase98UniversalComputerUseMode: 拼接动作类别；如果没有这行代码，permissions 和 mode 输出无法稳定展示动作面。
# 新增代码+Phase98UniversalComputerUseMode: 函数段结束，_phase98_csv 到此结束；如果没有这个边界说明，读者不容易看出列表格式化范围。


def _format_computer_mode_result(result: dict[str, Any]) -> str:  # 修改代码+Phase98UniversalComputerUseMode: 函数段开始，格式化 `/computer use` 模式结果并保留失败 decision；如果没有这段函数，full-confirm 错误只会显示空 mode 难排查。
    decision_line = f"- decision={result.get('decision', '')}\n" if "decision" in result else ""  # 新增代码+Phase98UniversalComputerUseMode: 仅在 store 返回 decision 时追加原因码；如果没有这行代码，缺 token 或错 token 时终端看不到 mismatch 原因。
    return f"Computer Use Mode\n- mode={result.get('mode', '')}\n- full_mode={_phase98_bool(result.get('full_mode', False))}\n- opened={_phase98_bool(result.get('opened', False))}\n- stopped={_phase98_bool(result.get('stopped', False))}\n{decision_line}- ttl_seconds={_phase98_safe_int(result.get('ttl_seconds', result.get('ttl_original_seconds', 0)))}\n- per_app_allowlist_required={_phase98_bool(result.get('per_app_allowlist_required', False))}\n- ordinary_apps_allowed_by_risk_policy={_phase98_bool(result.get('ordinary_apps_allowed_by_risk_policy', False))}\n- allowed_action_classes={_phase98_csv(result.get('allowed_action_classes', []))}\n- real_desktop_touched=false\n- low_level_event_count={_phase98_safe_int(result.get('low_level_event_count', 0))}\n- marker={result.get('marker', '')}\n- ok_token={result.get('ok_token', '')}\n"  # 修改代码+Phase98UniversalComputerUseMode: 返回包含 decision 和安全数字转换的稳定模式面板；如果没有这行代码，真实终端验收无法匹配 full-confirm 失败原因和零事件字段。
# 修改代码+Phase98UniversalComputerUseMode: 函数段结束，_format_computer_mode_result 到此结束；如果没有这个边界说明，读者不容易看出模式结果输出和失败诊断范围。


def _format_computer_full_request(result: dict[str, Any]) -> str:  # 修改代码+Phase100FullComputerUseMode: 函数段开始，格式化 `/computer use --full` 强确认请求并明确显示高风险；如果没有这段函数，高风险 full 请求可能被用户误解成已经打开或低风险。
    token = str(result.get("confirmation_token", "") or "")  # 新增代码+Phase98UniversalComputerUseMode: 读取确认 token；如果没有这行代码，输出无法告诉用户下一步命令。
    return f"Computer Use Full Request\n- strong_confirmation_required={_phase98_bool(result.get('strong_confirmation_required', False))}\n- risk=high\n- confirmation_token={token}\n- confirm_command=/computer use --full-confirm {token}\n- full_mode={_phase98_bool(result.get('full_mode', False))}\n- opened={_phase98_bool(result.get('opened', False))}\n- real_desktop_touched=false\n- low_level_event_count={_phase98_safe_int(result.get('low_level_event_count', 0))}\n- marker={result.get('marker', '')}\n- ok_token={result.get('ok_token', '')}\n"  # 修改代码+Phase100FullComputerUseMode: 返回待确认面板并安全显示 high 风险、opened=false 和低层事件数；如果没有这行代码，full 请求会缺少高风险提示和低层事件为零的安全证据。
# 修改代码+Phase100FullComputerUseMode: 函数段结束，_format_computer_full_request 到此结束；如果没有这个边界说明，读者不容易看出 full 请求输出范围。


def _format_computer_permissions_result(result: dict[str, Any]) -> str:  # 修改代码+Phase98UniversalComputerUseMode: 函数段开始，格式化 `/computer permissions` 权限摘要并安全显示事件数；如果没有这段函数，用户无法从终端快速查看本轮可做什么。
    return f"Computer Use Permissions\n- mode={result.get('mode', '')}\n- full_mode={_phase98_bool(result.get('full_mode', False))}\n- per_app_allowlist_required={_phase98_bool(result.get('per_app_allowlist_required', False))}\n- ordinary_apps_allowed_by_risk_policy={_phase98_bool(result.get('ordinary_apps_allowed_by_risk_policy', False))}\n- high_risk_requires_confirmation={_phase98_bool(result.get('high_risk_requires_confirmation', False))}\n- dangerous_target_terms_hidden={_phase98_bool(result.get('dangerous_target_terms_hidden', False))}\n- allowed_action_classes={_phase98_csv(result.get('allowed_action_classes', []))}\n- real_desktop_touched=false\n- low_level_event_count={_phase98_safe_int(result.get('low_level_event_count', 0))}\n- marker={result.get('marker', '')}\n- ok_token={result.get('ok_token', '')}\n"  # 修改代码+Phase98UniversalComputerUseMode: 返回稳定权限面板并安全显示低层事件数；如果没有这行代码，Task3 要求的安全字段会分散且容易漏。
# 修改代码+Phase98UniversalComputerUseMode: 函数段结束，_format_computer_permissions_result 到此结束；如果没有这个边界说明，读者不容易看出权限输出范围。


def _format_computer_stop_result(stop_result: dict[str, Any]) -> str:  # 修改代码+Phase98UniversalComputerUseMode: 函数段开始，格式化 `/computer stop` 模式停止结果并安全显示事件数；如果没有这段函数，用户看不到 mode session 是否真的 stopped。
    return f"Computer Use Stop\n- stopped={_phase98_bool(stop_result.get('stopped', False))}\n- real_desktop_touched=false\n- low_level_event_count={_phase98_safe_int(stop_result.get('low_level_event_count', 0))}\n- marker={stop_result.get('marker', '')}\n- ok_token={stop_result.get('ok_token', '')}\n"  # 修改代码+Phase98UniversalComputerUseMode: 返回稳定停止面板并安全显示低层事件数；如果没有这行代码，stop 只靠旧 abort 输出无法证明模式已停止。
# 修改代码+Phase98UniversalComputerUseMode: 函数段结束，_format_computer_stop_result 到此结束；如果没有这个边界说明，读者不容易看出 stop 输出范围。


def run_computer_terminal_command(workspace: Path, user_input: str) -> str:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，执行 `/computer` 子命令；如果没有这段函数，真实用户无法在终端查看或触发桌面急停。
    command_parts = str(user_input or "").strip().split(maxsplit=2)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 拆分命令、子命令和原因文本；如果没有这行代码，abort reason 会被截断或无法读取。
    subcommand = command_parts[1].lower() if len(command_parts) >= 2 else "status"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 默认无子命令时显示 status；如果没有这行代码，输入 /computer 会得到空行为。
    lock_manager = ComputerUseLockManager(base_dir=_computer_lock_root(Path(workspace)))  # 新增代码+Phase31ComputerUseLockAbortEvidence: 打开当前工作区的桌面锁管理器；如果没有这行代码，命令无法读取真实 lock/abort 文件。
    runtime = WindowsComputerUseSessionRuntime(lock_manager=lock_manager)  # 新增代码+Phase40WindowsAbortCleanup: 创建 Phase40 会话运行时；如果没有这行代码，/computer 命令无法统一记录 abort、cleanup 和通知。
    terminal_grants = ComputerUseTerminalGrantStore(base_dir=_computer_lock_root(Path(workspace)))  # 新增代码+Phase51ComputerStatusUI: 打开同一 workspace 的终端授权草案 store；如果没有这行代码，/computer grant/revoke 无法跨命令显示。
    session_context_store = ComputerUseSessionContextStore(base_dir=_computer_lock_root(Path(workspace)).parent / "session_state")  # 新增代码+Phase59SessionContextAppState: 打开同一 workspace 的统一 session context store；如果没有这行代码，/computer status 无法展示持久化 AppState。
    persistent_grants = WindowsComputerUsePersistentGrantStore(base_dir=_computer_lock_root(Path(workspace)).parent / "persistent_grants")  # 新增代码+Phase60PersistentGrants: 打开同一 workspace 的持久授权 store；如果没有这行代码，/computer approve/grants/revoke 无法共享真实状态。
    abort_streaming_hooks = WindowsComputerUseAbortStreamingHooks(lock_manager=lock_manager, session_id=DEFAULT_SESSION_CONTEXT_ID, base_dir=_computer_lock_root(Path(workspace)).parent / "abort_streaming_hooks")  # 新增代码+Phase61AbortStreamingHooks: 打开同一 workspace 的 abort/cleanup/streaming hook 状态；如果没有这行代码，终端入口无法看到中断钩子和事件流。
    high_level_tools = WindowsHighLevelComputerToolRuntime(base_dir=_computer_lock_root(Path(workspace)).parent / "high_level_tools", lock_manager=lock_manager, grant_store=persistent_grants, abort_hooks=abort_streaming_hooks, session_id=DEFAULT_SESSION_CONTEXT_ID)  # 新增代码+Phase62HighLevelTools: 打开同一 workspace 的高层工具状态；如果没有这行代码，/computer status 和 /computer high-level-tools 会和真实锁/授权/abort 分裂。
    controller_takeover = WindowsComputerUseControllerTakeoverDebugSurface(repo_root=Path(workspace) if Path(workspace).name != "learning_agent" else Path(workspace).parent, base_dir=_computer_lock_root(Path(workspace)).parent / "controller_takeover")  # 新增代码+Phase63ControllerTakeover: 打开外部 agent controller 接管调试面；如果没有这行代码，/computer status 和 /computer controller 看不到 controller.ps1、可见终端和证据包状态。
    mode_sessions = ComputerUseModeSessionStore(base_dir=_computer_lock_root(Path(workspace)).parent / "mode_sessions")  # 新增代码+Phase98UniversalComputerUseMode: 打开同一 workspace 的通用 Computer Use 模式 session；如果没有这行代码，/computer use/stop/status/permissions 无法共享真实模式状态。
    if subcommand == "parity":  # 新增代码+Phase53ParityGapMatrix: 识别 Phase53 差距矩阵命令；如果没有这行代码，用户无法在真实终端直接查看 ClaudeCode 对齐差距。
        try:  # 新增代码+Phase53ParityGapMatrix: 优先按包路径导入 Phase53 渲染入口；如果没有这行代码，项目根目录运行时无法加载标准包模块。
            from learning_agent.computer_use.parity_gap_matrix import format_phase53_parity_gap_lines, run_phase53_parity_gap_matrix_contract  # 新增代码+Phase53ParityGapMatrix: 导入只读差距矩阵渲染和合同函数；如果没有这行代码，/computer parity 没有报告来源。
        except ModuleNotFoundError as error:  # 新增代码+Phase53ParityGapMatrix: 兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行的脚本模式；如果没有这行代码，真实终端入口可能因包前缀缺失失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.parity_gap_matrix"}:  # 新增代码+Phase53ParityGapMatrix: 只吞掉预期的包路径缺失；如果没有这行代码，真实内部 bug 会被错误隐藏。
                raise  # 新增代码+Phase53ParityGapMatrix: 重新抛出非路径类导入错误；如果没有这行代码，排查 Phase53 模块问题会很困难。
            from computer_use.parity_gap_matrix import format_phase53_parity_gap_lines, run_phase53_parity_gap_matrix_contract  # 新增代码+Phase53ParityGapMatrix: 脚本模式导入 Phase53 渲染和合同函数；如果没有这行代码，双击 bat 后 /computer parity 不可用。
        parity_report = run_phase53_parity_gap_matrix_contract()  # 新增代码+Phase53ParityGapMatrix: 运行只读差距矩阵合同；如果没有这行代码，终端输出没有真实结构化依据。
        return "\n".join(format_phase53_parity_gap_lines(parity_report)) + "\n"  # 新增代码+Phase53ParityGapMatrix: 返回人类可读矩阵面板；如果没有这行代码，用户看不到 Phase53-64 每项归属。
    if subcommand in {"native-gate", "native-reality", "dependencies"}:  # 新增代码+Phase54WindowsNativeRealityGate: 识别 Windows 原生依赖现实门禁命令；如果没有这行代码，用户无法在真实终端看到依赖缺口和下一步。
        try:  # 新增代码+Phase54WindowsNativeRealityGate: 优先按包路径导入 Phase54 渲染入口；如果没有这行代码，项目根目录运行时无法加载标准包模块。
            from learning_agent.computer_use.native_reality_gate import format_phase54_native_reality_gate_lines, run_phase54_native_reality_gate_contract  # 新增代码+Phase54WindowsNativeRealityGate: 导入只读现实门禁渲染和合同函数；如果没有这行代码，/computer native-gate 没有报告来源。
        except ModuleNotFoundError as error:  # 新增代码+Phase54WindowsNativeRealityGate: 兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行的脚本模式；如果没有这行代码，真实终端入口可能因包前缀缺失失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.native_reality_gate"}:  # 新增代码+Phase54WindowsNativeRealityGate: 只吞掉预期的包路径缺失；如果没有这行代码，真实内部 bug 会被错误隐藏。
                raise  # 新增代码+Phase54WindowsNativeRealityGate: 重新抛出非路径类导入错误；如果没有这行代码，排查 Phase54 模块问题会很困难。
            from computer_use.native_reality_gate import format_phase54_native_reality_gate_lines, run_phase54_native_reality_gate_contract  # 新增代码+Phase54WindowsNativeRealityGate: 脚本模式导入 Phase54 渲染和合同函数；如果没有这行代码，双击 bat 后 /computer native-gate 不可用。
        report_root = _computer_lock_root(Path(workspace)).parent  # 新增代码+Phase54WindowsNativeRealityGate: 把报告写到 memory/computer_use 而不是 locks 目录；如果没有这行代码，native_dependency_report.json 会混进锁文件目录。
        native_report = run_phase54_native_reality_gate_contract(output_root=report_root)  # 新增代码+Phase54WindowsNativeRealityGate: 运行只读现实门禁并落盘报告；如果没有这行代码，终端输出没有真实结构化依据。
        return "\n".join(format_phase54_native_reality_gate_lines(native_report)) + "\n"  # 新增代码+Phase54WindowsNativeRealityGate: 返回人类可读现实门禁面板；如果没有这行代码，用户看不到每项依赖和下一步。
    if subcommand == "use":  # 新增代码+Phase98UniversalComputerUseMode: 识别 `/computer use` 模式命令；如果没有这行代码，用户无法从真实终端打开通用 Computer Use 模式。
        use_args = command_parts[2].strip() if len(command_parts) >= 3 else ""  # 新增代码+Phase98UniversalComputerUseMode: 读取 use 后面的参数；如果没有这行代码，--observe/--full/--full-confirm 都无法区分。
        use_tokens = use_args.split()  # 新增代码+Phase98UniversalComputerUseMode: 按空白拆分 use 参数；如果没有这行代码，确认 token 和选项会黏在一起难解析。
        use_tokens_lower = [token.lower() for token in use_tokens]  # 新增代码+Phase98UniversalComputerUseMode: 准备小写选项列表；如果没有这行代码，用户输入大写参数会漏识别。
        if "--full-confirm" in use_tokens_lower:  # 新增代码+Phase98UniversalComputerUseMode: 识别 full 二次确认命令；如果没有这行代码，full 请求生成的 token 无法激活模式。
            token_index = use_tokens_lower.index("--full-confirm")  # 新增代码+Phase98UniversalComputerUseMode: 找到确认选项位置；如果没有这行代码，后续无法读取紧跟的 token。
            confirmation_token = use_tokens[token_index + 1] if len(use_tokens) > token_index + 1 else ""  # 新增代码+Phase98UniversalComputerUseMode: 读取确认 token；如果没有这行代码，confirm_full_mode 只能收到空值。
            confirm_result = mode_sessions.confirm_full_mode(confirmation_token, reason="terminal /computer use --full-confirm")  # 新增代码+Phase98UniversalComputerUseMode: 调用 store 激活 full mode；如果没有这行代码，二次确认不会真正写入 full 状态。
            mode_result = mode_sessions.status() if bool(confirm_result.get("opened", False)) else confirm_result  # 新增代码+Phase98UniversalComputerUseMode: 成功时读取带 ttl_seconds 的状态；如果没有这行代码，输出可能缺少动态 TTL 字段。
            return _format_computer_mode_result(mode_result)  # 新增代码+Phase98UniversalComputerUseMode: 用统一 mode formatter 输出 full 确认结果；如果没有这行代码，full 输出会和 normal/observe 不一致。
        if "--full" in use_tokens_lower:  # 新增代码+Phase98UniversalComputerUseMode: 识别 full 请求命令；如果没有这行代码，高风险模式无法生成强确认请求。
            return _format_computer_full_request(mode_sessions.request_full_mode(reason="terminal /computer use --full"))  # 新增代码+Phase98UniversalComputerUseMode: 只生成 pending token 不打开 full；如果没有这行代码，full 可能被误实现成一步提权。
        requested_mode = "observe" if "--observe" in use_tokens_lower else "normal"  # 新增代码+Phase98UniversalComputerUseMode: 根据参数决定 observe 或 normal；如果没有这行代码，--observe 会误开普通写模式。
        mode_sessions.open_mode(mode=requested_mode, reason=f"terminal /computer use {requested_mode}")  # 新增代码+Phase98UniversalComputerUseMode: 写入 normal/observe 模式状态；如果没有这行代码，/computer use 输出只是文字不会持久化。
        return _format_computer_mode_result(mode_sessions.status())  # 新增代码+Phase98UniversalComputerUseMode: 返回带 ttl_seconds 的统一模式面板；如果没有这行代码，用户看不到当前模式和权限边界。
    if subcommand in {"status", ""}:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 识别状态查询；如果没有这行代码，用户无法只读查看 Computer Use 状态。
        approval_model = WindowsComputerUseApprovalModel(security_policy=WindowsComputerUseSecurityPolicy())  # 修改代码+Phase51ComputerStatusUI: 创建带 Phase48 策略的审批状态模型；如果没有这行代码，renderer 拿不到 approval/grant flags。
        capability_report = run_phase43_native_capability_matrix_contract()  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 生成无副作用 native 能力矩阵报告；如果没有这行代码，/computer status 看不到 WGC/UIA/SendInput 统一差距。
        status_snapshot = {"lock": lock_manager.status(), "approval": approval_model.status(), "runtime": runtime.status(), "recovery": runtime.action_journal(limit=3), "terminal_grants": terminal_grants.status(), "persistent_grants": persistent_grants.status(DEFAULT_SESSION_CONTEXT_ID), "abort_streaming_hooks": abort_streaming_hooks.status(), "high_level_tools": high_level_tools.status(), "controller_takeover": controller_takeover.status(), "session_context": session_context_store.status(DEFAULT_SESSION_CONTEXT_ID), "mode_session": mode_sessions.status(), "capability_matrix": capability_report["matrix"]}  # 修改代码+Phase98UniversalComputerUseMode: 组装 renderer 快照并加入 Phase98 模式 session；如果没有这行代码，/computer status 看不到 mode/full/ttl 和普通应用风险策略。
        return render_computer_status(status_snapshot)  # 修改代码+Phase98UniversalComputerUseMode: 返回包含 Phase98 mode_session 的紧凑 `/computer` 状态面板；如果没有这行代码，/computer status 无法把 mode/full/ttl 渲染给用户。
    if subcommand in {"abort-hooks", "hooks"}:  # 新增代码+Phase61AbortStreamingHooks: 识别中断钩子状态命令；如果没有这行代码，用户无法在真实终端直接查看 abort/streaming hook。
        return "\n".join(abort_streaming_hooks.terminal_status_lines()) + "\n"  # 新增代码+Phase61AbortStreamingHooks: 返回中断钩子面板；如果没有这行代码，Phase61 的热键降级和 stream 文件路径不可见。
    if subcommand in {"high-level-tools", "tools"}:  # 新增代码+Phase62HighLevelTools: 识别高层工具状态命令；如果没有这行代码，用户无法在真实终端直接查看 Phase62 高层 API。
        return "\n".join(high_level_tools.terminal_status_lines()) + "\n"  # 新增代码+Phase62HighLevelTools: 返回高层工具面板；如果没有这行代码，Phase62 operations/progress/artifact 入口不可见。
    if subcommand in {"controller", "takeover", "controller-status"}:  # 新增代码+Phase63ControllerTakeover: 识别外部 agent controller 接管状态命令；如果没有这行代码，用户无法在真实终端直接查看 Phase63。
        return "\n".join(controller_takeover.terminal_status_lines()) + "\n"  # 新增代码+Phase63ControllerTakeover: 返回 controller 接管调试面板；如果没有这行代码，Phase63 可见终端、证据包和急停预览入口不可见。
    if subcommand == "permissions":  # 新增代码+Phase98UniversalComputerUseMode: 识别 `/computer permissions` 权限摘要命令；如果没有这行代码，用户无法查看当前模式允许哪些动作。
        return _format_computer_permissions_result(mode_sessions.permissions())  # 新增代码+Phase98UniversalComputerUseMode: 返回 Phase98 权限面板；如果没有这行代码，权限字段只能埋在 status 里。
    if subcommand == "stop":  # 新增代码+Phase98UniversalComputerUseMode: 识别 `/computer stop` 模式停止命令；如果没有这行代码，用户无法用新模式入口终止后续动作。
        reason = command_parts[2].strip() if len(command_parts) >= 3 else "terminal /computer stop"  # 新增代码+Phase98UniversalComputerUseMode: 读取 stop 原因；如果没有这行代码，审计记录无法关联用户为什么停止。
        stop_result = mode_sessions.stop(reason=reason)  # 新增代码+Phase98UniversalComputerUseMode: 停止 Phase98 mode session；如果没有这行代码，status 后续仍可能显示 normal/full。
        abort_result = runtime.request_global_abort(reason, source="terminal-stop")  # 新增代码+Phase98UniversalComputerUseMode: 保留现有 runtime global abort 行为；如果没有这行代码，旧动作层急停保护会被新 stop 绕过。
        return _format_computer_stop_result(stop_result) + _format_computer_lock_action("stop", {"status": abort_result.get("status", {})}) + format_phase40_runtime_action("stop", abort_result)  # 新增代码+Phase98UniversalComputerUseMode: 同时输出 mode stop 和旧 abort 证据；如果没有这行代码，用户和回归测试看不到两层保护。
    if subcommand == "abort":  # 新增代码+Phase31ComputerUseLockAbortEvidence: 识别急停请求；如果没有这行代码，用户无法从终端阻断下一次桌面动作。
        reason = command_parts[2].strip() if len(command_parts) >= 3 else "terminal abort"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 读取可选急停原因；如果没有这行代码，abort 记录缺少上下文。
        abort_result = runtime.request_global_abort(reason, source="terminal")  # 修改代码+Phase40WindowsAbortCleanup: 通过 runtime 写入 abort 并记录通知；如果没有这行代码，急停不会产生用户可见通知。
        return _format_computer_lock_action("abort", {"status": abort_result.get("status", {})}) + format_phase40_runtime_action("abort", abort_result)  # 修改代码+Phase40WindowsAbortCleanup: 同时返回旧 lock 面板和新 runtime 面板；如果没有这行代码，旧测试兼容性或新通知可见性会丢失。
    if subcommand in {"clear-abort", "clear"}:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 识别清除急停命令；如果没有这行代码，用户无法恢复后续安全动作。
        return _format_computer_lock_action("clear-abort", lock_manager.clear_abort(cleared_by="terminal"))  # 新增代码+Phase31ComputerUseLockAbortEvidence: 清除 abort 并返回状态；如果没有这行代码，急停会一直阻断动作。
    if subcommand == "observe":  # 新增代码+Phase51ComputerStatusUI: 识别只读观察命令；如果没有这行代码，用户无法从 `/computer` 面板安全获取窗口观察入口。
        observe_action = command_parts[2].strip() if len(command_parts) >= 3 else "list_windows"  # 新增代码+Phase51ComputerStatusUI: 读取可选观察动作，默认 list_windows；如果没有这行代码，observe 命令不知道要观察什么。
        observe_result = ComputerUseController().observe({"action": observe_action})  # 新增代码+Phase51ComputerStatusUI: 通过生产控制器执行只读 observe；如果没有这行代码，observe 命令只是空文案不会走安全枚举。
        return observe_result.to_text("computer_observe") + "\n"  # 新增代码+Phase51ComputerStatusUI: 返回统一 observe 文本；如果没有这行代码，用户看不到只读观察结果。
    if subcommand == "grant":  # 新增代码+Phase51ComputerStatusUI: 识别终端授权草案命令；如果没有这行代码，用户无法在状态面板记录 app/flag 选择。
        raw_grant = command_parts[2].strip() if len(command_parts) >= 3 else ""  # 新增代码+Phase51ComputerStatusUI: 读取 grant 参数文本；如果没有这行代码，app 和 flags 无法解析。
        grant_parts = raw_grant.split()  # 新增代码+Phase51ComputerStatusUI: 拆分 app_key 和 flags；如果没有这行代码，`notepad.exe desktopAction` 无法表达。
        app_key = grant_parts[0] if grant_parts else ""  # 新增代码+Phase51ComputerStatusUI: 提取 app_key；如果没有这行代码，grant_store 不知道授权对象。
        flags = grant_parts[1:] if len(grant_parts) > 1 else ["observe"]  # 新增代码+Phase51ComputerStatusUI: 提取 flags，默认只记录 observe 草案；如果没有这行代码，缺 flag 命令没有保守默认值。
        grant_result = terminal_grants.grant_app(app_key, flags)  # 新增代码+Phase51ComputerStatusUI: 写入终端授权草案；如果没有这行代码，grant 命令不会持久化。
        return f"Computer Grant\n- grant_recorded={str(bool(grant_result.get('grant_recorded', False))).lower()}\n- app_key={grant_result.get('app_key', '')}\n- flags={','.join(grant_result.get('flags', [])) if isinstance(grant_result.get('flags', []), list) else ''}\n- grant_scope={grant_result.get('grant_scope', '')}\n- actions_expanded={str(bool(grant_result.get('actions_expanded', False))).lower()}\n"  # 新增代码+Phase51ComputerStatusUI: 返回稳定 grant 结果；如果没有这行代码，用户看不到授权草案是否记录。
    if subcommand == "approve":  # 新增代码+Phase60PersistentGrants: 识别生产级持久授权命令；如果没有这行代码，用户无法从真实终端写入可评估 grant。
        raw_approve = command_parts[2].strip() if len(command_parts) >= 3 else ""  # 新增代码+Phase60PersistentGrants: 读取 approve 参数文本；如果没有这行代码，app/scope/ttl/reason 无法解析。
        parsed = _parse_phase60_persistent_grant_args(raw_approve, default_scope="observe")  # 新增代码+Phase60PersistentGrants: 解析终端参数；如果没有这行代码，approve 命令不能支持 ttl= 和 scope=。
        approve_result = persistent_grants.approve(session_id=DEFAULT_SESSION_CONTEXT_ID, app=parsed["app"], window_id=parsed["window_id"], display_id=parsed["display_id"], action_scope=parsed["action_scope"], ttl_seconds=parsed["ttl_seconds"], reason=parsed["reason"], grant_flags=parsed["grant_flags"])  # 新增代码+Phase60PersistentGrants: 写入持久授权；如果没有这行代码，approve_recorded 永远不会为 true。
        if bool(approve_result.get("approved", False)):  # 新增代码+Phase60PersistentGrants: 只有授权成功才同步 session context；如果没有这行代码，失败授权也可能污染 AppState。
            session_context_store.bind_context(DEFAULT_SESSION_CONTEXT_ID, allowed_apps=[approve_result.get("app", "")], grant_flags=dict(parsed["grant_flags"]))  # 新增代码+Phase60PersistentGrants: 把 app 和 flags 同步到统一 context；如果没有这行代码，/computer status 的 session_context 看不到 approve 选择。
        return _format_phase60_approve_output(approve_result)  # 新增代码+Phase60PersistentGrants: 返回稳定 approve 面板；如果没有这行代码，用户看不到持久授权写入结果。
    if subcommand == "deny":  # 新增代码+Phase60PersistentGrants: 识别显式拒绝命令；如果没有这行代码，用户无法把拒绝选择写入审计。
        raw_deny = command_parts[2].strip() if len(command_parts) >= 3 else ""  # 新增代码+Phase60PersistentGrants: 读取 deny 参数文本；如果没有这行代码，deny 不知道拒绝哪个 app。
        parsed = _parse_phase60_persistent_grant_args(raw_deny, default_scope="observe")  # 新增代码+Phase60PersistentGrants: 解析 deny 参数；如果没有这行代码，reason/scope 无法进入审计。
        deny_result = persistent_grants.deny(session_id=DEFAULT_SESSION_CONTEXT_ID, app=parsed["app"], action_scope=parsed["action_scope"], reason=parsed["reason"])  # 新增代码+Phase60PersistentGrants: 写入拒绝审计；如果没有这行代码，deny 命令不会留下记录。
        return _format_phase60_deny_output(deny_result)  # 新增代码+Phase60PersistentGrants: 返回稳定 deny 面板；如果没有这行代码，用户看不到拒绝是否记录。
    if subcommand == "grants":  # 新增代码+Phase60PersistentGrants: 识别持久授权状态命令；如果没有这行代码，用户无法直接查看 active/revoked/expired grants。
        return "\n".join(persistent_grants.terminal_status_lines(DEFAULT_SESSION_CONTEXT_ID)) + "\n"  # 新增代码+Phase60PersistentGrants: 返回持久授权面板；如果没有这行代码，/computer grants 没有可读状态。
    if subcommand == "revoke":  # 新增代码+Phase51ComputerStatusUI: 识别终端授权草案撤销命令；如果没有这行代码，用户无法从状态面板收回 grant 草案。
        app_key = command_parts[2].strip() if len(command_parts) >= 3 else ""  # 新增代码+Phase51ComputerStatusUI: 读取要撤销的 app_key；如果没有这行代码，revoke_store 不知道撤销对象。
        persistent_result = persistent_grants.revoke(session_id=DEFAULT_SESSION_CONTEXT_ID, app=app_key, reason="terminal revoke")  # 新增代码+Phase60PersistentGrants: 先撤销生产级持久授权；如果没有这行代码，/computer revoke 只会删草案不会阻断已批准动作。
        revoke_result = terminal_grants.revoke_app(app_key)  # 新增代码+Phase51ComputerStatusUI: 同时从草案 store 删除 app；如果没有这行代码，旧 Phase51 状态可能残留。
        return _format_phase60_revoke_output(persistent_result, revoke_result)  # 修改代码+Phase60PersistentGrants: 返回兼容 Phase51 和 Phase60 的 revoke 面板；如果没有这行代码，用户看不到持久撤销是否成功。
    if subcommand == "cleanup":  # 新增代码+Phase40WindowsAbortCleanup: 识别 turn cleanup 命令；如果没有这行代码，用户无法从终端清理残留桌面锁。
        session_id = command_parts[2].strip() if len(command_parts) >= 3 else "learning-agent-default-session"  # 新增代码+Phase40WindowsAbortCleanup: 读取可选 cleanup 会话，默认使用生产会话；如果没有这行代码，cleanup 不知道清理哪个 owner。
        cleanup_result = runtime.cleanup_turn(session_id=session_id, reason="terminal cleanup")  # 新增代码+Phase40WindowsAbortCleanup: 执行 runtime cleanup；如果没有这行代码，cleanup 命令只会显示文字不会释放锁。
        return format_phase40_runtime_action("cleanup", cleanup_result) + format_phase50_recovery_action("cleanup", cleanup_result)  # 修改代码+Phase50WindowsRecovery: 同时返回 cleanup runtime 和恢复层摘要；如果没有这行代码，真实终端看不到 abort_cleared 等恢复证据。
    if subcommand == "recover":  # 新增代码+Phase50WindowsRecovery: 识别陈旧锁恢复命令；如果没有这行代码，用户无法从终端显式接管崩溃遗留锁。
        recover_result = runtime.recover_stale_lock(owner_label="terminal-recovery")  # 新增代码+Phase50WindowsRecovery: 执行 stale lock recovery；如果没有这行代码，recover 命令只会显示文字不会改变锁 owner。
        return format_phase50_recovery_action("recover", recover_result)  # 新增代码+Phase50WindowsRecovery: 返回恢复层面板；如果没有这行代码，真实终端看不到 stale_recovered 和 Phase50 marker。
    if subcommand in {"journal", "action-journal"}:  # 新增代码+Phase50WindowsRecovery: 识别动作 journal 查看命令；如果没有这行代码，用户无法从终端回放最近动作链路。
        return "\n".join(runtime.terminal_journal_lines()) + "\n"  # 新增代码+Phase50WindowsRecovery: 返回最近动作 journal；如果没有这行代码，action journal 虽存在但不可见。
    if subcommand in {"notifications", "notification"}:  # 新增代码+Phase40WindowsAbortCleanup: 识别通知查看命令；如果没有这行代码，用户无法复盘最近 abort/cleanup 事件。
        return "\n".join(runtime.terminal_notification_lines()) + "\n"  # 新增代码+Phase40WindowsAbortCleanup: 返回最近通知列表；如果没有这行代码，通知队列虽然写入但不可见。
    if subcommand == "release":  # 新增代码+Phase31ComputerUseLockAbortEvidence: 识别释放桌面锁命令；如果没有这行代码，用户无法从终端释放默认会话锁。
        session_id = command_parts[2].strip() if len(command_parts) >= 3 else "learning-agent-default-session"  # 新增代码+Phase31ComputerUseLockAbortEvidence: 读取释放会话，默认使用生产会话；如果没有这行代码，release 不知道释放哪个 owner。
        return _format_computer_lock_action("release", lock_manager.release(session_id))  # 新增代码+Phase31ComputerUseLockAbortEvidence: 执行释放并返回状态；如果没有这行代码，锁残留时用户只能手删文件。
    return "Computer Action\n- 不支持的 /computer 子命令。\n- 可用命令：/computer、/computer status、/computer use、/computer use --observe、/computer use --full、/computer use --full-confirm <token>、/computer stop、/computer permissions、/computer parity、/computer native-gate、/computer abort-hooks、/computer high-level-tools、/computer controller、/computer observe [action]、/computer grant <app> [flags]、/computer approve <app> [flags] ttl=60 scope=click、/computer grants、/computer deny <app>、/computer revoke <app>、/computer abort <reason>、/computer clear-abort、/computer cleanup [session_id]、/computer recover、/computer journal、/computer notifications、/computer release [session_id]\n"  # 修改代码+Phase98UniversalComputerUseMode: 返回包含 Phase98 mode 命令的用法；如果没有这行代码，输错命令时用户不知道 `/computer use`、stop 和 permissions 入口。
# 修改代码+Phase98UniversalComputerUseMode: 函数段结束，run_computer_terminal_command 到此结束；如果没有这个边界说明，读者不容易看出 Phase98 use/stop/permissions 与旧命令共同处理的范围。


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
