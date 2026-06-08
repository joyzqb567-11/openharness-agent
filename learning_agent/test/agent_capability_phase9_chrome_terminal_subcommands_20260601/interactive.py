"""交互式终端应用层，承载真实用户可见的输入输出循环。"""  # 新增代码+AppSplit: 说明本模块负责交互终端；若没有这行代码，终端循环仍会堆在 learning_agent.py。
from __future__ import annotations  # 新增代码+AppSplit: 允许类型注解延迟解析；若没有这行代码，类型提示在部分运行顺序下可能提前求值。

import json  # 新增代码+TerminalStatusUI: 格式化 resume/compact 结构化状态；若没有这行代码，终端命令只能打印难读的 Python 对象。
import sys  # 新增代码+Phase9ChromeTerminalActions: 获取当前 Python 解释器路径；如果没有这行代码，/chrome install-preview 生成的 launcher 可能不知道该用哪个 Python。
from pathlib import Path  # 新增代码+AppSplit: 标注工作区路径类型；若没有这行代码，终端事件里的 workspace 来源不清楚。
from typing import Any  # 新增代码+AppSplit: 允许接收任意实现了 run 的 agent；若没有这行代码，模块会和 LearningAgent 类强耦合。

try:  # 新增代码+AppSplit: 优先按包路径导入轮次格式化和验收事件 helper；若没有这行代码，包运行模式下交互层无法复用通用能力。
    from learning_agent.app.chrome_status_renderer import render_chrome_status  # 新增代码+ChromeTerminalUI: 导入 /chrome 专用状态渲染器；若没有这行代码，终端无法显示聚焦 Chrome 面板。
    from learning_agent.browser_extension_host.manifest_installer import ChromeNativeHostInstaller  # 新增代码+Phase9ChromeTerminalActions: 导入 native host 安装器；如果没有这行代码，/chrome install-preview 只能显示文案不能生成 manifest。
    from learning_agent.app.status_renderer import render_status_snapshot  # 新增代码+StatusEcosystem: 导入终端状态渲染器；若没有这行代码，/status 无法显示统一状态页。
    from learning_agent.core.config import format_max_turns_status  # 新增代码+AppSplit: 导入轮次状态格式化；若没有这行代码，终端启动提示无法显示当前策略。
    from learning_agent.observability.acceptance_events import emit_acceptance_event  # 新增代码+AppSplit: 导入验收事件写入器；若没有这行代码，真实终端控制器无法知道何时输入 prompt。
    from learning_agent.observability.run_records import build_final_answer_event_payload  # 新增代码+AppSplit: 导入最终回答事件 payload helper；若没有这行代码，final_answer_printed 会丢完整回答字段。
    from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+StatusEcosystem: 导入统一状态快照聚合器；若没有这行代码，/status 会读不到 run/task/queue/session。
    from learning_agent.sdk.status import get_sessions, list_status_events, load_resume_report  # 新增代码+TerminalStatusUI: 复用 SDK 状态入口；若没有这行代码，终端 /events、/sessions、/resume 会另写旁路读取逻辑。
except ModuleNotFoundError as error:  # 新增代码+AppSplit: 捕获脚本模式下包路径不可用；若没有这行代码，双击 bat 时交互层可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.app", "learning_agent.app.chrome_status_renderer", "learning_agent.app.status_renderer", "learning_agent.browser_extension_host", "learning_agent.browser_extension_host.manifest_installer", "learning_agent.core", "learning_agent.core.config", "learning_agent.observability", "learning_agent.observability.acceptance_events", "learning_agent.observability.run_records", "learning_agent.runtime", "learning_agent.runtime.status_snapshot", "learning_agent.sdk", "learning_agent.sdk.status"}:  # 修改代码+Phase9ChromeTerminalActions: 允许 native host 安装器在脚本模式 fallback；若没有这行代码，bat 入口下 /chrome 子命令可能导入失败。
        raise  # 新增代码+AppSplit: 重新抛出真实导入错误；若没有这行代码，观测层或配置层问题会被隐藏。
    from app.chrome_status_renderer import render_chrome_status  # 新增代码+ChromeTerminalUI: 脚本模式导入 /chrome 专用渲染器；若没有这行代码，直接运行时 /chrome 无法显示。
    from browser_extension_host.manifest_installer import ChromeNativeHostInstaller  # 新增代码+Phase9ChromeTerminalActions: 脚本模式导入 native host 安装器；如果没有这行代码，双击 bat 后 /chrome install-preview 不可用。
    from app.status_renderer import render_status_snapshot  # 新增代码+StatusEcosystem: 脚本模式导入状态渲染器；若没有这行代码，直接运行时 /status 无法显示。
    from core.config import format_max_turns_status  # 新增代码+AppSplit: 脚本模式从同目录 core 包导入；若没有这行代码，直接运行时轮次提示会断开。
    from observability.acceptance_events import emit_acceptance_event  # 新增代码+AppSplit: 脚本模式从同目录 observability 包导入；若没有这行代码，bat 入口无法写验收事件。
    from observability.run_records import build_final_answer_event_payload  # 新增代码+AppSplit: 脚本模式导入最终回答 payload helper；若没有这行代码，真实终端最终回答事件会断开。
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


def run_chrome_terminal_command(workspace: Path, user_input: str) -> str:  # 新增代码+Phase9ChromeTerminalActions: 执行 `/chrome` 及其子命令并返回可打印文本；如果没有这段函数，终端动作无法被单元测试和真实终端复用。
    command_parts = str(user_input or "").strip().split()  # 新增代码+Phase9ChromeTerminalActions: 拆分用户输入；如果没有这行代码，无法识别 install-preview/repair 等子命令。
    if len(command_parts) <= 1:  # 新增代码+Phase9ChromeTerminalActions: 没有子命令时保留原 `/chrome` 状态页行为；如果没有这行代码，老用户习惯会被破坏。
        status_snapshot = build_status_snapshot(workspace)  # 新增代码+ChromeTerminalUI: 从统一快照读取浏览器状态；若没有这行代码，/chrome 会和 SDK/API 事实源分裂。
        return render_chrome_status(status_snapshot)  # 新增代码+ChromeTerminalUI: 返回聚焦 Chrome 状态页；若没有这行代码，用户看不到 provider/native host/tab/权限摘要。
    subcommand = command_parts[1].lower()  # 新增代码+Phase9ChromeTerminalActions: 读取小写子命令；如果没有这行代码，大小写输入会导致重复判断。
    installer = ChromeNativeHostInstaller(_chrome_native_host_target_dir(workspace))  # 新增代码+Phase9ChromeTerminalActions: 创建 native host 安装器；如果没有这行代码，终端命令无法生成 manifest 或修复建议。
    if subcommand == "install-preview":  # 新增代码+Phase9ChromeTerminalActions: 识别安全安装预览；如果没有这行代码，用户无法从终端生成 manifest/launcher。
        extension_id = command_parts[2] if len(command_parts) >= 3 else "abcdefghijklmnopabcdefghijklmnop"  # 新增代码+Phase9ChromeTerminalActions: 支持用户传扩展 ID，同时提供本地预览默认值；如果没有这行代码，命令缺参会失败。
        payload = installer.install(extension_id=extension_id, python_executable=sys.executable, host_script=_chrome_native_host_script_path(workspace), dry_run=True)  # 新增代码+Phase9ChromeTerminalActions: 生成 manifest/launcher 且不写 registry；如果没有这行代码，install-preview 只是空壳命令。
        payload["launcher_path"] = str(Path(str(payload.get("manifest_path", ""))).with_suffix(".cmd"))  # 新增代码+Phase9ChromeTerminalActions: 在终端结果里展示 launcher 路径；如果没有这行代码，用户看不到 Chrome 实际启动入口。
        return _format_chrome_action_result("browser_extension_install", payload)  # 新增代码+Phase9ChromeTerminalActions: 返回安装预览结果；如果没有这行代码，用户看不到 manifest 和 registry_targets。
    if subcommand == "repair":  # 新增代码+Phase9ChromeTerminalActions: 识别修复建议命令；如果没有这行代码，用户无法在终端查询下一步。
        return _format_chrome_action_result("repair", installer.repair_hint())  # 新增代码+Phase9ChromeTerminalActions: 返回 native host 修复建议；如果没有这行代码，repair 命令没有实际输出。
    if subcommand == "uninstall-preview":  # 新增代码+Phase9ChromeTerminalActions: 识别安全卸载预览；如果没有这行代码，用户无法预演 registry 清理范围。
        payload = installer.uninstall(dry_run=True)  # 新增代码+Phase9ChromeTerminalActions: 生成卸载审计但不删除 registry；如果没有这行代码，卸载预览无法证明安全边界。
        return _format_chrome_action_result("browser_extension_uninstall", payload)  # 新增代码+Phase9ChromeTerminalActions: 返回卸载预览结果；如果没有这行代码，用户看不到将影响哪些 key。
    return "Chrome Action\n- 不支持的 /chrome 子命令。\n- 可用命令：/chrome、/chrome install-preview [extension_id]、/chrome repair、/chrome uninstall-preview\n"  # 新增代码+Phase9ChromeTerminalActions: 给未知命令返回清楚用法；如果没有这行代码，输错命令会被误发给模型或无响应。


def _print_chrome_command(workspace: Path, user_input: str = "/chrome") -> None:  # 修改代码+Phase9ChromeTerminalActions: 打印 `/chrome` 状态或子命令结果；若没有这段代码，主循环会重复状态读取和渲染逻辑。
    print("\n" + run_chrome_terminal_command(workspace, user_input), end="")  # 修改代码+Phase9ChromeTerminalActions: 复用可测试的命令函数；若没有这行代码，真实终端和单元测试会走不同逻辑。


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
        if user_command in {"/chrome", "chrome"} or user_command.startswith("/chrome ") or user_command.startswith("chrome "):  # 修改代码+Phase9ChromeTerminalActions: 识别 Chrome 状态命令和子命令；若没有这行代码，/chrome install-preview 会被误发给模型。
            _print_chrome_command(workspace, user_input)  # 修改代码+Phase9ChromeTerminalActions: 打印浏览器状态或动作结果；若没有这行代码，/chrome 子命令不会输出内容。
            emit_acceptance_event("chrome_status_printed", {"workspace": str(workspace), "command": user_input[:200]})  # 修改代码+Phase9ChromeTerminalActions: 写入 /chrome 命令验收事件并记录具体命令；若没有这行代码，真实终端验收缺少子命令执行证据。
            continue  # 新增代码+ChromeTerminalUI: /chrome 命令处理后返回循环；若没有这行代码，/chrome 会继续进入模型调用。
        emit_acceptance_event("user_prompt_received", {"length": len(user_input), "prompt_preview": user_input[:200]})  # 新增代码+AppSplit: 记录输入长度和短预览；若没有这行代码，控制器无法确认真实终端收到的是哪条任务。
        answer = agent.run(user_input, max_turns=max_turns)  # 新增代码+AppSplit: 调用 agent 主循环生成最终回答；若没有这行代码，交互终端不会真正工作。
        print(f"\nAgent > {answer}")  # 新增代码+AppSplit: 打印最终回答给用户；若没有这行代码，用户看不到 agent 结果。
        final_answer_event_payload = build_final_answer_event_payload(answer)  # 新增代码+AppSplit: 组装最终回答验收 payload；若没有这行代码，完整 answer_text 字段会丢失。
        emit_acceptance_event("final_answer_printed", final_answer_event_payload)  # 新增代码+AppSplit: 写出最终回答事件；若没有这行代码，外部控制器无法稳定确认真实最终输出。
