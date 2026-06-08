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
    lines.append("- /chrome install-preview : 生成 native host manifest 和 launcher 的安全预览，不写 registry")  # 新增代码+Phase8ProductionEdges: 提示安全安装预览入口；如果没有这行代码，小白用户可能不知道先 dry-run。
    lines.append("- /chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY : 强确认后写 registry")  # 新增代码+Phase12ChromeStatusGuide: 展示真实安装确认命令；如果没有这行代码，用户看不到完整安装链路。
    lines.append("- /chrome pairing-preview : 预览 Chrome extension 配对请求，不写 bridge 状态")  # 新增代码+Phase15ChromePairingTrigger: 展示只读配对预览入口；如果没有这行代码，用户不知道如何安全查看触发请求。
    lines.append("- /chrome pairing-start-confirm I_UNDERSTAND_PAIR_CHROME : 强确认后写入待配对请求，等待扩展轮询处理")  # 新增代码+Phase15ChromePairingTrigger: 展示强确认配对触发入口；如果没有这行代码，用户不知道如何真正刷新配对。
    lines.append("- /chrome session-sync-selftest : 模拟浏览器侧 prompt 入队，用于终端验收 session sync durable queue")  # 新增代码+Phase16SessionSyncClosure: 展示 session sync 自检入口；如果没有这行代码，用户不知道如何证明浏览器 prompt 已入队。
    lines.append("- /chrome repair : 查看 native host/extension 下一步修复建议")  # 新增代码+Phase8ProductionEdges: 提示修复入口；如果没有这行代码，连接失败时仍需要用户猜下一步。
    lines.append("- /chrome uninstall-preview : 预览卸载 native host registry，不直接删除")  # 新增代码+Phase8ProductionEdges: 提示安全卸载预览入口；如果没有这行代码，用户不知道如何回滚安装。
    lines.append("- /chrome uninstall-confirm I_UNDERSTAND_DELETE_REGISTRY : 强确认后删除 registry")  # 新增代码+Phase12ChromeStatusGuide: 展示真实卸载确认命令；如果没有这行代码，用户看不到完整回滚链路。
    return "\n".join(lines) + "\n"  # 新增代码+ChromeTerminalUI: 返回最终文本并带末尾换行；若没有这行代码，终端输出会和下一个 prompt 粘在一起。
