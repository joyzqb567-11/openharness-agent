"""终端状态渲染器，把统一状态快照转成人类可读文本。"""  # 新增代码+StatusRenderer: 说明本模块负责 UI 文本而不是读取状态；若没有这行代码，渲染和聚合会再次耦合。

from __future__ import annotations  # 新增代码+StatusRenderer: 延迟解析类型注解；若没有这行代码，复杂 JSON 类型更容易受定义顺序影响。

from typing import Any  # 新增代码+StatusRenderer: 快照是通用 JSON dict；若没有这行代码，类型边界不清楚。


def _short_text(value: Any, max_chars: int = 160) -> str:  # 新增代码+StatusRenderer: 把长文本压成单行摘要；若没有这行代码，状态页可能被长 prompt 或输出刷屏。
    text = str(value or "").replace("\r", "\\r").replace("\n", "\\n")  # 新增代码+StatusRenderer: 转义换行保持单行；若没有这行代码，状态表会被输出内容打散。
    return text if len(text) <= max_chars else text[-max_chars:]  # 新增代码+StatusRenderer: 超长时取尾部；若没有这行代码，状态页会过长。


def _as_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase21TerminalStatusUI: 把未知快照片段安全转换为字典；如果没有这段函数，摘要逻辑会重复 isinstance 判断。
    return value if isinstance(value, dict) else {}  # 新增代码+Phase21TerminalStatusUI: 只有 dict 才原样返回；如果没有这行代码，坏快照会让摘要区访问 .get 时报错。


def _as_list(value: Any) -> list[Any]:  # 新增代码+Phase21TerminalStatusUI: 把未知快照片段安全转换为列表；如果没有这段函数，最近错误扫描会重复 isinstance 判断。
    return value if isinstance(value, list) else []  # 新增代码+Phase21TerminalStatusUI: 只有 list 才原样返回；如果没有这行代码，坏事件流会让遍历报错。


def _status_next_command(snapshot: dict[str, Any]) -> str:  # 新增代码+Phase21TerminalStatusUI: 根据状态快照计算最值得用户执行的下一条命令；如果没有这段函数，/status 只能展示事实不能指导行动。
    resume = _as_dict(snapshot.get("resume", {}))  # 新增代码+Phase21TerminalStatusUI: 读取恢复状态；如果没有这行代码，压缩恢复风险无法优先提示。
    browser = _as_dict(snapshot.get("browser", {}))  # 新增代码+Phase21TerminalStatusUI: 读取浏览器状态；如果没有这行代码，Chrome 连接问题无法生成下一步。
    provider_status = _as_dict(browser.get("provider_status", {}))  # 新增代码+Phase21TerminalStatusUI: 读取 provider 状态；如果没有这行代码，扩展和 native host 状态无法汇总。
    extension = _as_dict(provider_status.get("chrome_extension", {}))  # 新增代码+Phase21TerminalStatusUI: 读取 Chrome extension 状态；如果没有这行代码，配对问题无法识别。
    native_host = _as_dict(provider_status.get("native_host", {}))  # 新增代码+Phase21TerminalStatusUI: 读取 native host 状态；如果没有这行代码，注册后断连无法识别。
    if native_host.get("installer_state") == "registry_registered" and not bool(extension.get("paired", False)):  # 新增代码+Phase21TerminalStatusUI: 已注册但未配对时提示 Chrome 配对诊断；如果没有这行代码，用户会继续看长状态而不是定位插件问题。
        return "/chrome pairing-diagnose"  # 新增代码+Phase21TerminalStatusUI: 返回配对诊断命令；如果没有这行代码，下一步不够具体。
    if not bool(extension.get("connected", False)) and native_host.get("installer_state") == "registry_registered":  # 新增代码+Phase21TerminalStatusUI: 已注册但扩展未连接时也提示诊断；如果没有这行代码，断连状态不会给可执行命令。
        return "/chrome pairing-diagnose"  # 新增代码+Phase21TerminalStatusUI: 返回 Chrome 诊断命令；如果没有这行代码，用户需要自己推理断点。
    if bool(resume.get("needs_review", False)):  # 修改代码+Phase21TerminalStatusUI: Chrome 断点之后再提示恢复复核；如果没有这行代码，非浏览器恢复风险没有下一步。
        return "/compact"  # 修改代码+Phase21TerminalStatusUI: 返回 compact 状态命令；如果没有这行代码，用户不知道先复核压缩/恢复上下文。
    return "/events"  # 新增代码+Phase21TerminalStatusUI: 默认建议查看最近事件；如果没有这行代码，健康状态正常时没有轻量下一步。


def _status_recent_errors(snapshot: dict[str, Any]) -> list[str]:  # 新增代码+Phase21TerminalStatusUI: 汇总最近错误和警告为短列表；如果没有这段函数，错误会散落在 Health/Status Events 长区块里。
    errors: list[str] = []  # 新增代码+Phase21TerminalStatusUI: 准备累计错误摘要；如果没有这行代码，函数没有返回容器。
    health = _as_dict(snapshot.get("health", {}))  # 新增代码+Phase21TerminalStatusUI: 读取健康区块；如果没有这行代码，health warnings 不会进入最近问题。
    resume = _as_dict(snapshot.get("resume", {}))  # 新增代码+Phase21TerminalStatusUI: 读取恢复区块；如果没有这行代码，resume warnings 不会进入最近问题。
    for warning in _as_list(health.get("warnings", []))[:2]:  # 新增代码+Phase21TerminalStatusUI: 取前两条健康警告；如果没有这行代码，状态摘要可能被大量警告刷屏。
        errors.append(_short_text(warning, 120))  # 新增代码+Phase21TerminalStatusUI: 压缩健康警告；如果没有这行代码，长警告会破坏截图可读性。
    for warning in _as_list(resume.get("warnings", []))[:1]:  # 新增代码+Phase21TerminalStatusUI: 取一条恢复警告；如果没有这行代码，恢复风险不会出现在摘要。
        errors.append(_short_text(warning, 120))  # 新增代码+Phase21TerminalStatusUI: 压缩恢复警告；如果没有这行代码，长恢复提示会撑长状态页。
    for event in _as_list(snapshot.get("status_events", []))[-3:]:  # 新增代码+Phase21TerminalStatusUI: 扫描最近三条状态事件；如果没有这行代码，刚发生的错误事件不会进入摘要。
        event_block = _as_dict(event)  # 新增代码+Phase21TerminalStatusUI: 安全读取事件对象；如果没有这行代码，坏事件会导致摘要报错。
        event_type = str(event_block.get("event_type", ""))  # 新增代码+Phase21TerminalStatusUI: 读取事件类型；如果没有这行代码，无法筛选错误类事件。
        if "error" in event_type or "fail" in event_type or "warning" in event_type:  # 新增代码+Phase21TerminalStatusUI: 只把错误/失败/警告事件提升到摘要；如果没有这行代码，普通事件会淹没真正风险。
            errors.append(_short_text(event_block.get("payload", ""), 120))  # 新增代码+Phase21TerminalStatusUI: 压缩事件 payload；如果没有这行代码，最近错误没有具体内容。
    return errors[:3]  # 新增代码+Phase21TerminalStatusUI: 最多返回三条问题；如果没有这行代码，摘要区会再次变成长列表。


def render_status_snapshot(snapshot: dict[str, Any]) -> str:  # 新增代码+StatusRenderer: 渲染统一状态快照；若没有这行代码，终端/工具/CLI 会各写一套文本。
    lines: list[str] = []  # 新增代码+StatusRenderer: 准备累计输出行；若没有这行代码，函数没有拼接容器。
    counts = snapshot.get("counts", {}) if isinstance(snapshot.get("counts", {}), dict) else {}  # 新增代码+StatusRenderer: 安全读取计数字段；若没有这行代码，坏快照会报错。
    lines.append("LearningAgent Status")  # 新增代码+StatusRenderer: 输出状态标题；若没有这行代码，用户看不出这是状态视图。
    lines.append(f"workspace={snapshot.get('workspace', '')}")  # 新增代码+StatusRenderer: 输出工作区；若没有这行代码，用户无法判断读的是哪个项目。
    lines.append(f"runs={counts.get('runs', 0)} tasks={counts.get('tasks', 0)} commands={counts.get('commands', 0)} sessions={counts.get('sessions', 0)} events={counts.get('status_events', 0)}")  # 新增代码+StatusRenderer: 输出总数摘要；若没有这行代码，状态规模不直观。
    current_run = snapshot.get("current_run", {}) if isinstance(snapshot.get("current_run", {}), dict) else {}  # 新增代码+StatusRendererV2: 读取当前 run 区块；若没有这行代码，终端状态页看不到当前任务头寸。
    current_turn = snapshot.get("current_turn", {}) if isinstance(snapshot.get("current_turn", {}), dict) else {}  # 新增代码+StatusRendererV2: 读取当前 turn 区块；若没有这行代码，用户不知道当前卡在哪一轮。
    compact = snapshot.get("compact", {}) if isinstance(snapshot.get("compact", {}), dict) else {}  # 新增代码+StatusRendererV2: 读取 compact 区块；若没有这行代码，压缩状态不会进入真实终端 UI。
    resume = snapshot.get("resume", {}) if isinstance(snapshot.get("resume", {}), dict) else {}  # 新增代码+StatusRendererV2: 读取 resume 区块；若没有这行代码，恢复风险不会进入真实终端 UI。
    health = snapshot.get("health", {}) if isinstance(snapshot.get("health", {}), dict) else {}  # 新增代码+StatusRendererV2: 读取 health 区块；若没有这行代码，状态页无法提示风险。
    verifiers = snapshot.get("verifiers", {}) if isinstance(snapshot.get("verifiers", {}), dict) else {}  # 新增代码+StatusRendererV2: 读取 verifier 区块；若没有这行代码，阶段验收结果不会同屏显示。
    browser = snapshot.get("browser", {}) if isinstance(snapshot.get("browser", {}), dict) else {}  # 新增代码+BrowserStatusStage11: 读取浏览器 runtime 区块；若没有这行代码，终端 UI 看不到真实浏览器任务。
    lines.append("")  # 新增代码+StatusRenderer: 添加空行分隔区块；若没有这行代码，文本会挤在一起。
    provider_status_summary = _as_dict(browser.get("provider_status", {}))  # 新增代码+Phase21TerminalStatusUI: 读取 provider 状态用于顶层摘要；如果没有这行代码，状态页第一屏缺少连接概况。
    extension_summary = _as_dict(provider_status_summary.get("chrome_extension", {}))  # 新增代码+Phase21TerminalStatusUI: 读取扩展摘要；如果没有这行代码，第一屏看不到 extension 是否连接。
    native_host_summary = _as_dict(provider_status_summary.get("native_host", {}))  # 新增代码+Phase21TerminalStatusUI: 读取 native host 摘要；如果没有这行代码，第一屏看不到 native host 是否连接。
    recent_errors = _status_recent_errors(snapshot)  # 新增代码+Phase21TerminalStatusUI: 汇总最近问题；如果没有这行代码，摘要区无法展示风险。
    lines.append("Status Summary")  # 新增代码+Phase21TerminalStatusUI: 输出紧凑摘要区标题；如果没有这行代码，/status 第一屏仍要从多个区块里找重点。
    lines.append(f"- connection=native_host:{str(bool(native_host_summary.get('connected', False))).lower()} chrome_extension:{str(bool(extension_summary.get('connected', False))).lower()} paired:{str(bool(extension_summary.get('paired', False))).lower()} health_ok={health.get('ok', '')}")  # 新增代码+Phase21TerminalStatusUI: 一行展示连接和健康概况；如果没有这行代码，用户无法快速判断当前是否能继续。
    lines.append(f"- next={_status_next_command(snapshot)} : first command to inspect or fix current state")  # 新增代码+Phase21TerminalStatusUI: 显示下一条建议命令；如果没有这行代码，状态页无法指导小白用户下一步。
    lines.append(f"- recent_error={_short_text(recent_errors[0], 140) if recent_errors else '(none)'}")  # 新增代码+Phase21TerminalStatusUI: 显示最近一条问题；如果没有这行代码，错误仍会埋在长事件列表里。
    lines.append("")  # 新增代码+Phase21TerminalStatusUI: 分隔摘要和详细 current 区块；如果没有这行代码，摘要与旧内容会粘连。
    lines.append("Current")  # 新增代码+StatusRendererV2: 输出当前运行区块标题；若没有这行代码，run/turn 当前态不易扫描。
    lines.append(f"- run_id={current_run.get('run_id', '')} status={current_run.get('status', '')} stage={current_run.get('current_stage_index', '')}")  # 新增代码+StatusRendererV2: 输出当前 run 核心字段；若没有这行代码，用户只能在 run 列表里猜当前任务。
    lines.append(f"- turn_id={current_turn.get('turn_id', '')} state={current_turn.get('state', current_turn.get('status', ''))} session_id={current_turn.get('session_id', '')}")  # 新增代码+StatusRendererV2: 输出当前 turn 核心字段；若没有这行代码，中断/恢复时不知道当前轮次。
    lines.append("")  # 新增代码+StatusRendererV2: 分隔 current 和 compact 区块；若没有这行代码，文本区块会粘连。
    lines.append("Compact / Resume")  # 新增代码+StatusRendererV2: 输出 compact/resume 区块标题；若没有这行代码，用户找不到压缩恢复状态。
    lines.append(f"- compact_state={compact.get('state', '')} boundary_uuid={compact.get('boundary_uuid', compact.get('last_boundary_uuid', ''))} reason={compact.get('reason', '')}")  # 新增代码+StatusRendererV2: 输出 compact 核心证据；若没有这行代码，压缩发生与否不可见。
    lines.append(f"- resume_state={resume.get('resume_state', resume.get('state', ''))} needs_review={resume.get('needs_review', False)} warnings={_short_text(resume.get('warnings', ''))}")  # 新增代码+StatusRendererV2: 输出 resume 风险状态；若没有这行代码，用户不知道是否需要人工确认。
    lines.append("")  # 新增代码+StatusRendererV2: 分隔 compact 和 health 区块；若没有这行代码，状态文本不易读。
    lines.append("Health")  # 新增代码+StatusRendererV2: 输出健康区块标题；若没有这行代码，状态页不会突出风险。
    lines.append(f"- ok={health.get('ok', '')} warnings={_short_text(health.get('warnings', []))}")  # 新增代码+StatusRendererV2: 输出健康状态和警告；若没有这行代码，外部 agent 难以判断是否可继续。
    lines.append(f"- verifier={_short_text(verifiers.get('latest', ''))}")  # 新增代码+StatusRendererV2: 输出最近 verifier 事件；若没有这行代码，真实验收结果不会同屏可见。
    browser_counts = browser.get("counts", {}) if isinstance(browser.get("counts", {}), dict) else {}  # 新增代码+BrowserStatusStage11: 读取浏览器计数；若没有这行代码，浏览器状态摘要无法显示规模。
    latest_browser_run = browser.get("latest_run", {}) if isinstance(browser.get("latest_run", {}), dict) else {}  # 新增代码+BrowserStatusStage11: 读取最近浏览器 run；若没有这行代码，用户无法快速定位当前浏览器任务。
    lines.append("")  # 新增代码+BrowserStatusStage11: 分隔 health 和 browser 区块；若没有这行代码，状态文本会粘连。
    lines.append("Browser Runtime")  # 新增代码+BrowserStatusStage11: 输出浏览器 runtime 区块标题；若没有这行代码，真实浏览器状态不醒目。
    lines.append(f"- runs={browser_counts.get('runs', 0)} actions={browser_counts.get('actions', 0)} observations={browser_counts.get('observations', 0)} events={browser_counts.get('events', 0)}")  # 新增代码+BrowserStatusStage11: 输出浏览器状态计数；若没有这行代码，用户不知道是否有浏览器证据。
    lines.append(f"- latest_run_id={latest_browser_run.get('run_id', '')} status={latest_browser_run.get('status', '')} store={browser.get('store', '')}")  # 新增代码+BrowserStatusStage11: 输出最近浏览器 run 和 store；若没有这行代码，外部 agent 难以审计文件。
    for event in browser.get("events", [])[-3:] if isinstance(browser.get("events", []), list) else []:  # 新增代码+BrowserStatusStage11: 展示最近几条浏览器事件；若没有这行代码，工具动作流不可见。
        lines.append(f"  browser_event={event.get('event_type', '')} run_id={event.get('run_id', '')}")  # 新增代码+BrowserStatusStage11: 输出浏览器事件摘要；若没有这行代码，用户无法确认 snapshot/screenshot 是否落盘。
    provider_status = browser.get("provider_status", {}) if isinstance(browser.get("provider_status", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取 provider 状态区块；若没有这行代码，终端 UI 看不到插件轨道健康。
    providers = provider_status.get("providers", {}) if isinstance(provider_status.get("providers", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取 provider 健康集合；若没有这行代码，无法列出三条浏览器轨道。
    extension = provider_status.get("chrome_extension", {}) if isinstance(provider_status.get("chrome_extension", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取插件状态摘要；若没有这行代码，pending 和权限计数不可见。
    tabs = provider_status.get("tabs", {}) if isinstance(provider_status.get("tabs", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取 tab 状态摘要；若没有这行代码，active tab URL 不会显示。
    active_tab = tabs.get("active_tab", {}) if isinstance(tabs.get("active_tab", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取 active tab；若没有这行代码，状态页无法直接显示当前页面。
    permissions = provider_status.get("permissions", {}) if isinstance(provider_status.get("permissions", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取权限状态摘要；若没有这行代码，站点授权事件不可见。
    native_host = provider_status.get("native_host", {}) if isinstance(provider_status.get("native_host", {}), dict) else {}  # 新增代码+ChromeExtensionStage8: 读取 native host 状态；若没有这行代码，插件连接来源不可见。
    lines.append("")  # 新增代码+ChromeExtensionStage8: 分隔 browser runtime 和 provider 区块；若没有这行代码，状态文本会挤在一起。
    lines.append("Browser Providers")  # 新增代码+ChromeExtensionStage8: 输出 provider 状态标题；若没有这行代码，用户找不到双轨状态。
    for provider_name, provider_health in providers.items():  # 新增代码+ChromeExtensionStage8: 遍历 provider 健康状态；若没有这行代码，三条轨道不会显示。
        if isinstance(provider_health, dict):  # 新增代码+ChromeExtensionStage8: 只渲染结构化健康对象；若没有这行代码，坏状态会导致 get 异常。
            lines.append(f"- provider={provider_name} available={str(bool(provider_health.get('available', False))).lower()} reason={provider_health.get('reason', '')}")  # 新增代码+ChromeExtensionStage8: 输出单个 provider 健康摘要；若没有这行代码，外部 agent 无法肉眼判断可用性。
    lines.append(f"- native_host_connected={str(bool(native_host.get('connected', False))).lower()} bridge_state_file={native_host.get('bridge_state_file', '')}")  # 新增代码+ChromeExtensionStage8: 输出 native host 连接和状态文件；若没有这行代码，插件问题无法定位到文件。
    lines.append(f"- chrome_extension_connected={str(bool(extension.get('connected', False))).lower()} pending_command_count={extension.get('pending_command_count', 0)} permission_event_count={permissions.get('permission_event_count', extension.get('permission_event_count', 0))}")  # 新增代码+ChromeExtensionStage8: 输出插件连接、待命令和权限事件；若没有这行代码，卡住动作和授权变化不可见。
    lines.append(f"- active_tab_title={_short_text(active_tab.get('title', ''))} active_tab_url={_short_text(active_tab.get('url', ''), 240)}")  # 新增代码+ChromeExtensionStage8: 输出当前 tab 标题和 URL；若没有这行代码，真实 Chrome 当前页面不可见。
    recordings = browser.get("recordings", {}) if isinstance(browser.get("recordings", {}), dict) else {}  # 新增代码+BrowserRecordingStage9: 读取录制视觉证据区块；若没有这行代码，终端 UI 看不到帧序列和 GIF。
    latest_recording = recordings.get("latest", {}) if isinstance(recordings.get("latest", {}), dict) else {}  # 新增代码+BrowserRecordingStage9: 读取最近录制；若没有这行代码，状态页需要遍历列表。
    lines.append("")  # 新增代码+BrowserRecordingStage9: 分隔 provider 和 recordings 区块；若没有这行代码，文本会挤在一起。
    lines.append("Browser Recordings")  # 新增代码+BrowserRecordingStage9: 输出视觉证据区块标题；若没有这行代码，用户找不到录制状态。
    lines.append(f"- recording_count={recordings.get('recording_count', 0)} store={recordings.get('store', '')}")  # 新增代码+BrowserRecordingStage9: 输出录制总数和目录；若没有这行代码，用户不知道视觉证据存在哪里。
    if latest_recording:  # 新增代码+BrowserRecordingStage9: 有最近录制时输出摘要；若没有这行代码，空录制也会显示空字段。
        lines.append(f"- recording_id={latest_recording.get('recording_id', '')} status={latest_recording.get('status', '')} frame_count={latest_recording.get('frame_count', 0)} gif_path={_short_text(latest_recording.get('gif_path', ''), 240)}")  # 新增代码+BrowserRecordingStage9: 输出最近录制和 GIF 路径；若没有这行代码，用户无法快速打开过程证据。
    else:  # 新增代码+BrowserRecordingStage9: 没有录制时进入空态；若没有这行代码，用户可能以为渲染漏了。
        lines.append("- (empty)")  # 新增代码+BrowserRecordingStage9: 明确暂无录制；若没有这行代码，空区块语义不清楚。
    lines.append("")  # 新增代码+StatusRendererV2: 分隔 health 和 runs 区块；若没有这行代码，后续列表会粘连。
    lines.append("Runs")  # 新增代码+StatusRenderer: 输出 run 区块标题；若没有这行代码，run 列表不易扫描。
    for run in snapshot.get("runs", []) if isinstance(snapshot.get("runs", []), list) else []:  # 新增代码+StatusRenderer: 遍历 run 摘要；若没有这行代码，run 不会显示。
        lines.append(f"- run_id={run.get('run_id', '')} status={run.get('status', '')} current_stage_index={run.get('current_stage_index', '')} prompt={_short_text(run.get('prompt', ''))}")  # 新增代码+StatusRenderer: 输出 run 摘要；若没有这行代码，用户看不到 run 状态。
        for stage in run.get("stages", []) if isinstance(run.get("stages", []), list) else []:  # 新增代码+StatusRenderer: 遍历阶段摘要；若没有这行代码，stage 状态不可见。
            acceptance = stage.get("acceptance", {}) if isinstance(stage.get("acceptance", {}), dict) else {}  # 新增代码+StatusRenderer: 安全读取验收结果；若没有这行代码，坏 stage 会报错。
            lines.append(f"  stage[{stage.get('index', '')}] {stage.get('name', '')} status={stage.get('status', '')} verifier={acceptance.get('passed', False)} checkpoint={_short_text(stage.get('checkpoint', ''))}")  # 新增代码+StatusRenderer: 输出阶段和 verifier；若没有这行代码，用户无法同屏看验收。
    if not snapshot.get("runs"):  # 新增代码+StatusRenderer: 如果没有 run；若没有这行代码，空状态会显得像漏输出。
        lines.append("- (empty)")  # 新增代码+StatusRenderer: 明确 run 为空；若没有这行代码，用户不知是无任务还是渲染失败。
    lines.append("")  # 新增代码+StatusRenderer: 分隔区块；若没有这行代码，文本不易读。
    lines.append("Tasks")  # 新增代码+StatusRenderer: 输出任务区块标题；若没有这行代码，后台任务不易定位。
    for task in snapshot.get("tasks", []) if isinstance(snapshot.get("tasks", []), list) else []:  # 新增代码+StatusRenderer: 遍历任务摘要；若没有这行代码，task 不会显示。
        lines.append(f"- task_id={task.get('task_id', '')} status={task.get('status', '')} kind={task.get('kind', '')} output={_short_text(task.get('output', '') or task.get('error', ''))}")  # 新增代码+StatusRenderer: 输出任务状态和输出尾巴；若没有这行代码，用户只能另开 task_get。
    if not snapshot.get("tasks"):  # 新增代码+StatusRenderer: 如果没有任务；若没有这行代码，空任务区块不明确。
        lines.append("- (empty)")  # 新增代码+StatusRenderer: 明确任务为空；若没有这行代码，用户可能以为渲染漏了。
    lines.append("")  # 新增代码+StatusRenderer: 分隔区块；若没有这行代码，后续内容会挤在一起。
    lines.append("Commands")  # 新增代码+StatusRenderer: 输出命令队列标题；若没有这行代码，runtime queue 不易扫描。
    for command in snapshot.get("commands", []) if isinstance(snapshot.get("commands", []), list) else []:  # 新增代码+StatusRenderer: 遍历命令摘要；若没有这行代码，队列不可见。
        lines.append(f"- command_id={command.get('command_id', '')} mode={command.get('mode', '')} priority={command.get('priority', '')} status={command.get('status', '')}")  # 新增代码+StatusRenderer: 输出命令生命周期；若没有这行代码，外部 agent 不知道队列卡在哪。
    if not snapshot.get("commands"):  # 新增代码+StatusRenderer: 如果命令为空；若没有这行代码，空队列不明确。
        lines.append("- (empty)")  # 新增代码+StatusRenderer: 明确命令为空；若没有这行代码，用户可能误判状态页坏了。
    lines.append("")  # 新增代码+StatusRenderer: 分隔区块；若没有这行代码，事件区块不清楚。
    lines.append("Sessions")  # 新增代码+StatusRenderer: 输出 session 区块标题；若没有这行代码，resume 入口不易发现。
    for session_id in snapshot.get("sessions", []) if isinstance(snapshot.get("sessions", []), list) else []:  # 新增代码+StatusRenderer: 遍历最近 session；若没有这行代码，可恢复会话不可见。
        lines.append(f"- session_id={session_id}")  # 新增代码+StatusRenderer: 输出 session id；若没有这行代码，用户无法复制到 session_resume。
    if not snapshot.get("sessions"):  # 新增代码+StatusRenderer: 如果 session 为空；若没有这行代码，空区块不明确。
        lines.append("- (empty)")  # 新增代码+StatusRenderer: 明确 session 为空；若没有这行代码，用户不知是否无会话。
    lines.append("")  # 新增代码+StatusRenderer: 分隔区块；若没有这行代码，事件区块会贴在 session 后。
    lines.append("Status Events")  # 新增代码+StatusRenderer: 输出事件区块标题；若没有这行代码，状态事件尾巴不易理解。
    for event in snapshot.get("status_events", []) if isinstance(snapshot.get("status_events", []), list) else []:  # 新增代码+StatusRenderer: 遍历状态事件；若没有这行代码，事件尾巴不可见。
        lines.append(f"- #{event.get('sequence', '')} {event.get('event_type', '')} payload={_short_text(event.get('payload', ''))}")  # 新增代码+StatusRenderer: 输出事件序号和类型；若没有这行代码，SDK watcher 难以人工复核。
    if not snapshot.get("status_events"):  # 新增代码+StatusRenderer: 如果事件为空；若没有这行代码，空事件区块不明确。
        lines.append("- (empty)")  # 新增代码+StatusRenderer: 明确事件为空；若没有这行代码，用户可能以为读取失败。
    return "\n".join(lines) + "\n"  # 新增代码+StatusRenderer: 返回最终文本并换行；若没有这行代码，CLI 输出可能缺末尾换行。
