"""`/chrome` 专用终端状态渲染器。"""  # 新增代码+ChromeTerminalUI: 把浏览器/插件状态从大 /status 页拆成专门视图；若没有这个文件，用户只能在长状态页里翻找 Chrome 信息。

from __future__ import annotations  # 新增代码+ChromeTerminalUI: 延迟解析类型注解；若没有这行代码，复杂 JSON 注解更容易受导入顺序影响。

from typing import Any  # 新增代码+ChromeTerminalUI: 快照来自 JSON 字典，字段类型不固定；若没有这行代码，渲染器类型边界不清楚。


def _block(value: Any) -> dict[str, Any]:  # 新增代码+ChromeTerminalUI: 把未知值安全转换成字典；若没有这段代码，坏状态会在 .get 调用时报错。
    return value if isinstance(value, dict) else {}  # 新增代码+ChromeTerminalUI: 只有 dict 原样返回，否则给空字典；若没有这行代码，渲染空态不稳定。


def _items(value: Any) -> list[Any]:  # 新增代码+ChromeTerminalUI: 把未知值安全转换成列表；若没有这段代码，坏 events/actions 会在遍历时报错。
    return value if isinstance(value, list) else []  # 新增代码+ChromeTerminalUI: 只有 list 原样返回，否则给空列表；若没有这行代码，空态渲染不稳定。


def _short_text(value: Any, max_chars: int = 180) -> str:  # 新增代码+ChromeTerminalUI: 把长标题、URL、路径压成单行；若没有这段代码，终端状态会被长 URL 刷屏。
    text = str(value or "").replace("\r", "\\r").replace("\n", "\\n")  # 新增代码+ChromeTerminalUI: 转义换行保证单行显示；若没有这行代码，状态表会被页面标题打散。
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."  # 新增代码+ChromeTerminalUI: 超长时保留开头并加省略号；若没有这行代码，终端 UI 不易扫描。


def _chrome_guide_line(installer_state: str, paired: bool = False) -> str:  # 修改代码+Phase13ChromePairingGuide: 根据安装和配对状态生成下一步建议；如果没有这段函数，/chrome 只能展示状态不能指导操作。
    state = str(installer_state or "").strip()  # 新增代码+Phase12ChromeStatusGuide: 清理状态码；如果没有这行代码，空格或 None 会导致分支不稳定。
    if state in {"", "not_installed"}:  # 新增代码+Phase12ChromeStatusGuide: 未安装或未知时先走安全预览；如果没有这行代码，新用户不知道第一步。
        return "- next=/chrome install-preview : 先生成 manifest 和 launcher 的安全预览，不写 registry"  # 新增代码+Phase12ChromeStatusGuide: 给出未安装下一步；如果没有这行代码，用户要猜安装流程。
    if state == "manifest_created":  # 新增代码+Phase12ChromeStatusGuide: 已 preview 但未注册时进入强确认；如果没有这行代码，preview 后流程会断开。
        return "- next=/chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY : 确认后写 HKCU registry"  # 新增代码+Phase12ChromeStatusGuide: 给出确认安装命令；如果没有这行代码，用户不知道如何完成注册。
    if state == "registry_registered" and paired:  # 新增代码+Phase13ChromePairingGuide: 已注册且已配对时说明 session sync 已连接；如果没有这行代码，用户会误以为仍需配对。
        return "- next=session sync 已连接 : native host、Chrome extension 和 session id 已形成配对，可继续使用浏览器侧任务同步"  # 新增代码+Phase13ChromePairingGuide: 给出已同步状态；如果没有这行代码，完成态没有清楚反馈。
    if state == "registry_registered":  # 新增代码+Phase12ChromeStatusGuide: 已注册后进入配对和同步；如果没有这行代码，用户会重复安装而不是配对插件。
        return "- next=extension pairing / session sync : native host 已注册，下一步检查 Chrome extension 配对和 session sync"  # 新增代码+Phase12ChromeStatusGuide: 给出注册后的下一步；如果没有这行代码，安装链路无法衔接插件配对。
    if state == "registry_mismatch":  # 新增代码+Phase12ChromeStatusGuide: registry 指向错误时提示修复；如果没有这行代码，用户不知道该重装还是卸载。
        return "- next=/chrome repair : registry 路径不一致，先查看修复建议再决定 install-confirm 或 uninstall-confirm"  # 新增代码+Phase12ChromeStatusGuide: 给出不匹配修复建议；如果没有这行代码，错误状态没有行动方向。
    return "- next=/chrome repair : installer 状态异常，先查看修复建议"  # 新增代码+Phase12ChromeStatusGuide: 兜底异常状态；如果没有这行代码，未知状态没有下一步。

def _chrome_current_state(installer_state: str, extension_connected: bool, paired: bool, pending_pairing_status: str) -> str:  # 新增代码+Phase17ChromeOperableGuide: 计算 /chrome 当前阶段状态码；如果没有这段函数，用户需要自己从多行状态里推断当前阶段。
    state = str(installer_state or "").strip()  # 新增代码+Phase17ChromeOperableGuide: 清理安装状态；如果没有这行代码，空格或 None 会导致状态码不稳定。
    pending = str(pending_pairing_status or "").strip()  # 新增代码+Phase17ChromeOperableGuide: 清理待配对状态；如果没有这行代码，pending 状态判断可能失效。
    if state in {"", "not_installed"}:  # 新增代码+Phase17ChromeOperableGuide: native host 未安装时归类为安装前状态；如果没有这行代码，首次用户不知道从哪里开始。
        return "not_installed"  # 新增代码+Phase17ChromeOperableGuide: 返回未安装状态码；如果没有这行代码，当前状态区无法展示起点。
    if state == "manifest_created":  # 新增代码+Phase17ChromeOperableGuide: manifest 已生成但 registry 未写入；如果没有这行代码，preview 后状态不清楚。
        return "manifest_ready_needs_confirm"  # 新增代码+Phase17ChromeOperableGuide: 返回需要确认安装状态码；如果没有这行代码，用户不知道下一步是 install-confirm。
    if state == "registry_mismatch":  # 新增代码+Phase17ChromeOperableGuide: registry 指向异常；如果没有这行代码，修复场景没有清楚状态。
        return "registry_mismatch"  # 新增代码+Phase17ChromeOperableGuide: 返回 registry 不匹配状态码；如果没有这行代码，repair 建议缺少状态背景。
    if state == "registry_registered" and paired:  # 新增代码+Phase17ChromeOperableGuide: 已注册且已配对；如果没有这行代码，完成态会被误归入未配对。
        return "session_synced"  # 新增代码+Phase17ChromeOperableGuide: 返回已同步状态码；如果没有这行代码，用户不知道闭环已完成。
    if state == "registry_registered" and pending == "pending":  # 新增代码+Phase17ChromeOperableGuide: 已注册且存在待配对请求；如果没有这行代码，用户不知道正在等待扩展处理。
        return "pairing_pending"  # 新增代码+Phase17ChromeOperableGuide: 返回配对等待状态码；如果没有这行代码，pending 请求不够醒目。
    if state == "registry_registered" and extension_connected:  # 新增代码+Phase17ChromeOperableGuide: 已注册且扩展连接但未配对；如果没有这行代码，半连接状态难区分。
        return "extension_connected_unpaired"  # 新增代码+Phase17ChromeOperableGuide: 返回扩展已连未配对状态码；如果没有这行代码，用户不知道要触发配对。
    if state == "registry_registered":  # 新增代码+Phase17ChromeOperableGuide: 已注册但扩展未连接；如果没有这行代码，注册后断点不明确。
        return "registered_unpaired"  # 新增代码+Phase17ChromeOperableGuide: 返回已注册未配对状态码；如果没有这行代码，状态区没有可扫描标签。
    return "needs_repair"  # 新增代码+Phase17ChromeOperableGuide: 兜底异常状态；如果没有这行代码，未知状态没有统一分类。


def render_chrome_status(snapshot: dict[str, Any]) -> str:  # 新增代码+ChromeTerminalUI: 渲染 `/chrome` 聚焦状态页；若没有这段代码，终端命令没有可复用输出逻辑。
    browser = _block(snapshot.get("browser", {}))  # 新增代码+ChromeTerminalUI: 读取统一快照中的 browser 区块；若没有这行代码，渲染器拿不到浏览器事实源。
    provider_status = _block(browser.get("provider_status", {}))  # 新增代码+ChromeTerminalUI: 读取 provider/native host/extension 区块；若没有这行代码，插件状态无法显示。
    providers = _block(provider_status.get("providers", {}))  # 新增代码+ChromeTerminalUI: 读取 provider 健康集合；若没有这行代码，三条浏览器轨道无法列出。
    extension = _block(provider_status.get("chrome_extension", {}))  # 新增代码+ChromeTerminalUI: 读取 Chrome extension 状态；若没有这行代码，插件连接和 pending 计数不可见。
    native_host = _block(provider_status.get("native_host", {}))  # 新增代码+ChromeTerminalUI: 读取 native host 状态；若没有这行代码，安装/桥接状态不可见。
    tabs = _block(provider_status.get("tabs", {}))  # 新增代码+ChromeTerminalUI: 读取标签页状态；若没有这行代码，active tab 不可见。
    active_tab = _block(tabs.get("active_tab", {}))  # 新增代码+ChromeTerminalUI: 读取当前活动 tab；若没有这行代码，当前页面摘要为空。
    permissions = _block(provider_status.get("permissions", {}))  # 新增代码+ChromeTerminalUI: 读取权限状态；若没有这行代码，站点授权事件不可见。
    recordings = _block(browser.get("recordings", {}))  # 新增代码+ChromeTerminalUI: 读取录制证据状态；若没有这行代码，GIF/帧证据不可见。
    latest_recording = _block(recordings.get("latest", {}))  # 新增代码+ChromeTerminalUI: 读取最近录制；若没有这行代码，用户无法快速打开最新证据。
    latest_run = _block(browser.get("latest_run", {}))  # 新增代码+ChromeTerminalUI: 读取最近浏览器 run；若没有这行代码，状态页无法定位最近任务。
    lines: list[str] = []  # 新增代码+ChromeTerminalUI: 准备累计输出行；若没有这行代码，渲染器没有拼接容器。
    lines.append("Chrome Status")  # 新增代码+ChromeTerminalUI: 输出专用状态标题；若没有这行代码，用户看不出这是 /chrome 视图。
    lines.append("Chrome Current")  # 新增代码+Phase17ChromeOperableGuide: 输出当前状态区标题；如果没有这行代码，用户需要自己推断当前阶段。
    lines.append(f"- state={_chrome_current_state(str(native_host.get('installer_state', '')), bool(extension.get('connected', False)), bool(extension.get('paired', False)), str(extension.get('pending_pairing_request_status', '') or ''))} next_hint=see Chrome Guide")  # 新增代码+Phase17ChromeOperableGuide: 输出紧凑状态码；如果没有这行代码，/chrome 不是可扫描操作面板。
    if providers:  # 新增代码+ChromeTerminalUI: 有 provider 数据时逐项展示；若没有这行代码，非空状态也会走空态。
        for provider_name, provider_health in providers.items():  # 新增代码+ChromeTerminalUI: 遍历 provider 健康对象；若没有这行代码，多个轨道不会显示。
            health = _block(provider_health)  # 新增代码+ChromeTerminalUI: 防御坏 provider 值；若没有这行代码，字符串健康值会导致异常。
            lines.append(f"- provider={provider_name} available={str(bool(health.get('available', False))).lower()} reason={_short_text(health.get('reason', ''))}")  # 新增代码+ChromeTerminalUI: 输出 provider 可用性和原因；若没有这行代码，用户无法判断走 extension 还是 CDP。
    else:  # 新增代码+ChromeTerminalUI: 没有 provider 数据时输出空态；若没有这行代码，首次运行会显示得像漏内容。
        lines.append("- provider=(empty)")  # 新增代码+ChromeTerminalUI: 明确 provider 为空；若没有这行代码，用户不知道是否读取失败。
    lines.append(f"- native_host_connected={str(bool(native_host.get('connected', False))).lower()} bridge_state_file={_short_text(native_host.get('bridge_state_file', ''), 240)}")  # 新增代码+ChromeTerminalUI: 输出 native host 连接和状态文件；若没有这行代码，注册/桥接问题难定位。
    lines.append(f"- chrome_extension_connected={str(bool(extension.get('connected', False))).lower()} pending_command_count={extension.get('pending_command_count', 0)} permission_event_count={permissions.get('permission_event_count', extension.get('permission_event_count', 0))}")  # 新增代码+ChromeTerminalUI: 输出插件连接、待命令和权限事件；若没有这行代码，卡住命令和授权变化不可见。
    lines.append(f"- paired={str(bool(extension.get('paired', False))).lower()} device_id={_short_text(extension.get('device_id', ''), 120)} session_id={_short_text(extension.get('session_id', ''), 120)} allowed_origin_count={extension.get('allowed_origin_count', 0)} last_seen_at={extension.get('last_seen_at', '')}")  # 新增代码+Phase13ChromePairingGuide: 输出 extension pairing/session sync 摘要；如果没有这行代码，已注册后的同步状态不可见。
    lines.append(f"- pending_pairing_request_status={_short_text(extension.get('pending_pairing_request_status', ''), 80)} pending_pairing_request_id={_short_text(extension.get('pending_pairing_request_id', ''), 160)} pending_pairing_request_created_at={extension.get('pending_pairing_request_created_at', '')}")  # 新增代码+Phase15ChromePairingTrigger: 输出终端触发的待配对请求；如果没有这行代码，用户执行 pairing-start-confirm 后仍看不到等待状态。
    lines.append(f"- last_browser_prompt_id={_short_text(extension.get('last_browser_prompt_id', ''), 160)} last_browser_prompt_url={_short_text(extension.get('last_browser_prompt_url', ''), 240)}")  # 新增代码+Phase16SessionSyncClosure: 输出最近浏览器侧 prompt 入队证据；如果没有这行代码，用户无法确认 session sync 是否进入 durable queue。
    lines.append(f"- active_tab_title={_short_text(active_tab.get('title', ''))} active_tab_url={_short_text(active_tab.get('url', ''), 240)}")  # 新增代码+ChromeTerminalUI: 输出当前标签页标题和 URL；若没有这行代码，用户不知道 Chrome 当前页。
    lines.append(f"- latest_run_id={latest_run.get('run_id', '')} status={latest_run.get('status', '')} store={_short_text(browser.get('store', ''), 240)}")  # 新增代码+ChromeTerminalUI: 输出最近浏览器 run；若没有这行代码，用户无法追踪最近浏览器任务。
    lines.append(f"- recording_count={recordings.get('recording_count', 0)} recording_id={latest_recording.get('recording_id', '')} gif_path={_short_text(latest_recording.get('gif_path', ''), 240)}")  # 新增代码+ChromeTerminalUI: 输出录制证据摘要；若没有这行代码，真实验收视觉证据入口不可见。
    lines.append(f"- installer_state={native_host.get('installer_state', '')} manifest_path={_short_text(native_host.get('manifest_path', ''), 240)}")  # 新增代码+Phase12ChromeStatusGuide: 输出 native host 安装器状态和 manifest 路径；如果没有这行代码，向导依据对用户不可见。
    recent_events = _items(browser.get("events", []))[-3:]  # 新增代码+ChromeTerminalUI: 取最近三条浏览器事件；若没有这行代码，状态页缺少动作时间线。
    for event in recent_events:  # 新增代码+ChromeTerminalUI: 遍历最近事件；若没有这行代码，事件不会显示。
        event_block = _block(event)  # 新增代码+ChromeTerminalUI: 防御坏事件对象；若没有这行代码，非 dict 事件会报错。
        lines.append(f"- browser_event={event_block.get('event_type', '')} run_id={event_block.get('run_id', '')}")  # 新增代码+ChromeTerminalUI: 输出事件类型和 run id；若没有这行代码，用户无法确认浏览器动作流。
    lines.append("Chrome Guide")  # 新增代码+Phase12ChromeStatusGuide: 增加向导区标题；如果没有这行代码，用户分不清状态和下一步建议。
    lines.append(_chrome_guide_line(str(native_host.get("installer_state", "")), bool(extension.get("paired", False))))  # 修改代码+Phase13ChromePairingGuide: 输出按安装和配对状态计算的下一条命令；如果没有这行代码，/chrome 不能指导后续操作。
    lines.append("Chrome Actions")  # 新增代码+Phase8ProductionEdges: 增加 /chrome 管理动作区标题；如果没有这行代码，/chrome 仍只是只读状态页。
    lines.append("- risk=low confirm=no command=/chrome install-preview : dry-run manifest/launcher")  # 修改代码+Phase17ChromeOperableGuide: 标注低风险预览命令；如果没有这行代码，用户不知道该命令不会写 registry。
    lines.append("- risk=high confirm=yes command=/chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY : writes HKCU registry")  # 修改代码+Phase17ChromeOperableGuide: 标注高风险安装确认；如果没有这行代码，生产写入边界不清楚。
    lines.append("- risk=low confirm=no command=/chrome pairing-preview : preview pairing request only")  # 修改代码+Phase17ChromeOperableGuide: 标注低风险配对预览；如果没有这行代码，用户不知道该命令不写 bridge。
    lines.append("- risk=medium confirm=yes command=/chrome pairing-start-confirm I_UNDERSTAND_PAIR_CHROME : writes pending bridge request")  # 修改代码+Phase17ChromeOperableGuide: 标注中风险配对触发；如果没有这行代码，bridge 写入边界不清楚。
    lines.append("- risk=low confirm=no command=/chrome session-sync-selftest : writes local test prompt to runtime queue")  # 修改代码+Phase17ChromeOperableGuide: 标注自检命令风险；如果没有这行代码，用户不知道该命令会写本地队列。
    lines.append("- risk=low confirm=no command=/chrome extension-e2e-check : checks manifest/pairing/prompt evidence")  # 新增代码+Phase18ChromeExtensionE2E: 暴露端到端证据检查入口；如果没有这行代码，用户需要猜测 Phase 18 命令。
    lines.append("- risk=low confirm=no command=/chrome repair : read repair hints")  # 修改代码+Phase17ChromeOperableGuide: 标注修复建议为只读；如果没有这行代码，用户可能不敢查看修复建议。
    lines.append("- risk=low confirm=no command=/chrome uninstall-preview : dry-run registry removal")  # 修改代码+Phase17ChromeOperableGuide: 标注卸载预览为只读；如果没有这行代码，用户不知道可先安全预演。
    lines.append("- risk=high confirm=yes command=/chrome uninstall-confirm I_UNDERSTAND_DELETE_REGISTRY : deletes HKCU registry")  # 修改代码+Phase17ChromeOperableGuide: 标注高风险卸载确认；如果没有这行代码，删除 registry 边界不清楚。
    return "\n".join(lines) + "\n"  # 新增代码+ChromeTerminalUI: 返回最终文本并带末尾换行；若没有这行代码，终端输出会和下一个 prompt 粘在一起。
