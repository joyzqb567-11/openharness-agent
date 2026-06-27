"""Desktop GUI browser automation workbench adapter."""  # 新增代码+DesktopGUIBrowserWorkbench：说明本文件只做 GUI 浏览器工作台薄适配；如果没有这行，维护者可能误以为这里重写浏览器自动化 runtime。

from __future__ import annotations  # 新增代码+DesktopGUIBrowserWorkbench：启用延迟类型解析；如果没有这行，复杂类型在导入期更容易互相牵连。

from pathlib import Path  # 新增代码+DesktopGUIBrowserWorkbench：使用 Path 处理 workspace 和 memory 路径；如果没有这行，Windows 路径拼接会脆弱。
from typing import Any  # 新增代码+DesktopGUIBrowserWorkbench：声明 JSON payload 里允许通用值；如果没有这行，函数边界不清楚。
from urllib.parse import urlparse  # 新增代码+DesktopGUIBrowserWorkbench：复用标准 URL parser 做安全校验；如果没有这行，open 请求可能靠字符串猜测。

from learning_agent.app.gui_protocol import GUI_V2_SCHEMA_VERSION  # 新增代码+DesktopGUIBrowserWorkbench：复用 GUI V2 协议版本；如果没有这行，Browser endpoint 会和其它 V2 contract 分裂。
from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DesktopGUIBrowserWorkbench：复用统一状态事件流；如果没有这行，Browser 工作台按钮不会进入右侧时间线。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+DesktopGUIBrowserWorkbench：复用统一状态快照；如果没有这行，Browser 面板会旁路现有状态系统。


GUI_BROWSER_CONTROL_SOURCE = "learning_agent.browser_automation_mcp_server"  # 新增代码+DesktopGUIBrowserWorkbench：声明能力来源是现有 Browser MCP server；如果没有这行，前端无法说明复用了哪个模块。
GUI_BROWSER_SAFE_ERROR = "浏览器自动化状态暂时不可读。"  # 新增代码+DesktopGUIBrowserWorkbench：统一脱敏错误文案；如果没有这行，异常路径可能泄漏本机目录。
GUI_BROWSER_ACTIONS = {"open", "refresh-status"}  # 新增代码+DesktopGUIBrowserWorkbench：集中列出 GUI 允许的最小动作；如果没有这行，路由容易接受未知动作。
GUI_BROWSER_COLLECTIONS = {"tabs", "console", "network"}  # 新增代码+DesktopGUIBrowserWorkbench：集中列出只读集合 endpoint；如果没有这行，GET 路由和 payload 形状容易漂移。
GUI_BROWSER_CONSOLE_TOOLS = {"browser_console", "mcp__browser_automation__browser_console"}  # 新增代码+DesktopGUIBrowserWorkbench：定义 console 事件工具名；如果没有这行，console 摘要无法从事件流识别。
GUI_BROWSER_NETWORK_TOOLS = {"browser_network", "mcp__browser_automation__browser_network"}  # 新增代码+DesktopGUIBrowserWorkbench：定义 network 事件工具名；如果没有这行，network 摘要无法从事件流识别。
GUI_BROWSER_DOWNLOAD_TOOLS = {"browser_downloads", "mcp__browser_automation__browser_downloads"}  # 新增代码+DesktopGUIBrowserWorkbench：定义 downloads 事件工具名；如果没有这行，下载摘要无法从事件流识别。


def _workspace_path(workspace: str | Path) -> Path:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，规范化 workspace；如果没有这段，不同调用点会读写不同相对目录。
    return Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIBrowserWorkbench：返回绝对路径；如果没有这行，memory/status 可能落到当前 shell 目录。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_workspace_path 到此结束；如果没有边界说明，用户不容易看出它只负责路径规范化。


def _status_store(root: Path) -> StatusEventStore:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，定位统一状态事件目录；如果没有这段，按钮动作没有审计事实源。
    return StatusEventStore(root / "memory" / "status")  # 新增代码+DesktopGUIBrowserWorkbench：沿用现有 memory/status；如果没有这行，右侧事件页读不到 Browser 工作台动作。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_status_store 到此结束；如果没有边界说明，用户不容易看出它只负责状态 store。


def _as_dict(value: Any) -> dict[str, Any]:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，把未知值收敛为 dict；如果没有这段，坏快照会让 endpoint 崩溃。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+DesktopGUIBrowserWorkbench：只复制普通字典，其它类型返回空对象；如果没有这行，列表/字符串可能被当对象访问。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_as_dict 到此结束；如果没有边界说明，类型防护范围不清楚。


def _as_list(value: Any) -> list[Any]:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，把未知值收敛为 list；如果没有这段，tabs/events 遍历会信任坏类型。
    return list(value) if isinstance(value, list) else []  # 新增代码+DesktopGUIBrowserWorkbench：只接受列表并复制；如果没有这行，None 或对象会污染摘要逻辑。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_as_list 到此结束；如果没有边界说明，列表防护范围不清楚。


def _safe_text(value: Any, fallback: str = "", max_chars: int = 220) -> str:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，把任意值变成短文本；如果没有这段，长 URL 或异常会撑破 GUI。
    text = str(value or fallback or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+DesktopGUIBrowserWorkbench：把多行文本压成单行；如果没有这行，右侧面板布局会被换行打散。
    return text[:max_chars]  # 新增代码+DesktopGUIBrowserWorkbench：限制最大长度；如果没有这行，URL/query 或错误文本可能挤爆右栏。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_safe_text 到此结束；如果没有边界说明，文本裁剪职责不清楚。


def _safe_int(value: Any, default: int = 0) -> int:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，安全读取数字字段；如果没有这段，坏 count 会让 payload 生成失败。
    try:  # 新增代码+DesktopGUIBrowserWorkbench：捕获 int 转换异常；如果没有这行，字符串或对象会抛到 HTTP handler。
        return int(value)  # 新增代码+DesktopGUIBrowserWorkbench：返回整数值；如果没有这行，调用方拿不到稳定数字。
    except (TypeError, ValueError, OverflowError):  # 新增代码+DesktopGUIBrowserWorkbench：处理不可转换输入；如果没有这行，坏状态文件会导致 500。
        return default  # 新增代码+DesktopGUIBrowserWorkbench：坏输入回退默认值；如果没有这行，函数会隐式返回 None。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_safe_int 到此结束；如果没有边界说明，数字兜底范围不清楚。


def _safe_url_parts(url: Any) -> dict[str, Any]:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，校验并脱敏 URL；如果没有这段，open 请求可能显示带 token 的完整 query。
    raw_url = _safe_text(url, "", 500)  # 新增代码+DesktopGUIBrowserWorkbench：读取 URL 并限制长度；如果没有这行，恶意长 URL 会进入日志。
    parsed = urlparse(raw_url)  # 新增代码+DesktopGUIBrowserWorkbench：使用标准库解析 URL；如果没有这行，scheme/host 判断会靠脆弱字符串。
    valid = parsed.scheme in {"http", "https"} and bool(parsed.netloc)  # 新增代码+DesktopGUIBrowserWorkbench：只允许 http/https 且必须有 host；如果没有这行，file/javascript URL 可能进入打开请求。
    origin = f"{parsed.scheme}://{parsed.netloc}" if valid else ""  # 新增代码+DesktopGUIBrowserWorkbench：只保留 origin；如果没有这行，query 中的隐私可能显示到 GUI。
    return {"valid": valid, "origin": origin, "host": parsed.netloc if valid else "", "scheme": parsed.scheme, "raw_url_present": bool(raw_url)}  # 新增代码+DesktopGUIBrowserWorkbench：返回脱敏校验结果；如果没有这行，调用方要重复解析 URL。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_safe_url_parts 到此结束；如果没有边界说明，URL 安全边界不清楚。


def _browser_snapshot(root: Path, snapshot: dict[str, Any] | None = None) -> tuple[dict[str, Any], bool, str]:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，读取或复用统一状态快照；如果没有这段，多个 endpoint 会重复 try/except。
    if isinstance(snapshot, dict):  # 新增代码+DesktopGUIBrowserWorkbench：优先复用调用方已经读取的快照；如果没有这行，runtime panels 会重复读磁盘。
        return snapshot, False, ""  # 新增代码+DesktopGUIBrowserWorkbench：返回传入快照并标记未降级；如果没有这行，函数会继续重读。
    try:  # 新增代码+DesktopGUIBrowserWorkbench：保护快照读取；如果没有这行，文件锁或坏 JSON 会拖垮 bridge。
        loaded = build_status_snapshot(root)  # 新增代码+DesktopGUIBrowserWorkbench：复用现有状态系统；如果没有这行，Browser 面板会和 CLI/SDK 分裂。
        return loaded if isinstance(loaded, dict) else {}, False, ""  # 新增代码+DesktopGUIBrowserWorkbench：只接受 dict 快照；如果没有这行，坏返回类型会污染 payload。
    except Exception:  # 新增代码+DesktopGUIBrowserWorkbench：捕获状态读取异常；如果没有这行，临时状态问题会变成 HTTP 500。
        return {"browser": {"provider_status": {"providers": {}, "error": GUI_BROWSER_SAFE_ERROR}}, "status_events": []}, True, GUI_BROWSER_SAFE_ERROR  # 新增代码+DesktopGUIBrowserWorkbench：返回安全降级快照；如果没有这行，前端可能空白或泄露路径。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_browser_snapshot 到此结束；如果没有边界说明，快照读取范围不清楚。


def _events_from_snapshot(root: Path, snapshot: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，从快照或 store 取事件；如果没有这段，console/network 摘要没有事实源。
    events = [event for event in _as_list(snapshot.get("status_events", [])) if isinstance(event, dict)]  # 新增代码+DesktopGUIBrowserWorkbench：优先使用快照里的事件尾巴；如果没有这行，runtime panels 会重复读事件文件。
    if events:  # 新增代码+DesktopGUIBrowserWorkbench：如果快照已有事件直接返回；如果没有这行，仍会做额外磁盘读取。
        return events  # 新增代码+DesktopGUIBrowserWorkbench：返回事件列表；如果没有这行，后续会重复加载。
    return [event.to_dict() for event in _status_store(root).list_events(limit=80)]  # 新增代码+DesktopGUIBrowserWorkbench：兜底读取最近 80 条状态事件；如果没有这行，独立 endpoint 没有事件数据。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_events_from_snapshot 到此结束；如果没有边界说明，事件来源优先级不清楚。


def _event_payload(event: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，安全读取事件 payload；如果没有这段，不同事件形状会重复防御逻辑。
    return _as_dict(event.get("payload", {}))  # 新增代码+DesktopGUIBrowserWorkbench：只接受 dict payload；如果没有这行，坏事件会拖垮摘要扫描。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_event_payload 到此结束；如果没有边界说明，payload 读取范围不清楚。


def _event_tool_name(event: dict[str, Any]) -> str:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，从事件中提取 browser 工具名；如果没有这段，事件扫描无法识别 console/network/downloads。
    payload = _event_payload(event)  # 新增代码+DesktopGUIBrowserWorkbench：读取事件正文；如果没有这行，嵌套工具名会丢失。
    return _safe_text(event.get("tool_name") or payload.get("tool_name") or payload.get("mcp_tool_name") or payload.get("tool") or payload.get("action"), "", 160)  # 新增代码+DesktopGUIBrowserWorkbench：兼容多种工具名字段；如果没有这行，MCP 前缀事件会漏掉。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_event_tool_name 到此结束；如果没有边界说明，工具名提取范围不清楚。


def _latest_browser_event(events: list[dict[str, Any]], tool_names: set[str]) -> dict[str, Any] | None:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，从事件尾巴找指定浏览器工具；如果没有这段，console/network/downloads 摘要会重复扫描。
    for event in reversed(events):  # 新增代码+DesktopGUIBrowserWorkbench：从最新事件向前找；如果没有这行，GUI 可能显示旧日志。
        if _event_tool_name(event) in tool_names:  # 新增代码+DesktopGUIBrowserWorkbench：检查工具名是否命中目标集合；如果没有这行，无法过滤具体工具。
            return event  # 新增代码+DesktopGUIBrowserWorkbench：返回最近匹配事件；如果没有这行，命中后仍会继续扫描。
    return None  # 新增代码+DesktopGUIBrowserWorkbench：找不到时返回空；如果没有这行，函数会隐式返回不清楚。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_latest_browser_event 到此结束；如果没有边界说明，事件查找范围不清楚。


def _safe_tool_summary(event: dict[str, Any] | None, empty_message: str) -> dict[str, Any]:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，把工具事件裁剪成 GUI 摘要；如果没有这段，原始 payload 可能泄露路径或撑爆面板。
    if not isinstance(event, dict):  # 新增代码+DesktopGUIBrowserWorkbench：处理没有事件的空态；如果没有这行，None 会继续访问字段。
        return {"available": False, "entry_count": 0, "error_count": 0, "latest_message": empty_message, "latest_tool": "", "sequence": 0}  # 新增代码+DesktopGUIBrowserWorkbench：返回稳定空摘要；如果没有这行，前端要猜空态字段。
    payload = _event_payload(event)  # 新增代码+DesktopGUIBrowserWorkbench：读取事件正文；如果没有这行，摘要无法提取消息和数量。
    message = _safe_text(payload.get("message") or payload.get("summary") or payload.get("result") or payload.get("text") or payload.get("status"), empty_message, 240)  # 新增代码+DesktopGUIBrowserWorkbench：读取安全短消息；如果没有这行，面板可能空白。
    explicit_error_count = payload.get("error_count")  # 新增代码+DesktopGUIBrowserWorkbench：读取显式错误数；如果没有这行，错误摘要只能靠文本猜。
    inferred_error_count = 1 if "error" in message.casefold() or "错误" in message else 0  # 新增代码+DesktopGUIBrowserWorkbench：无字段时按文本推断错误；如果没有这行，明显错误也会显示 0。
    return {"available": True, "entry_count": _safe_int(payload.get("entry_count", payload.get("count", 0))), "error_count": _safe_int(explicit_error_count, inferred_error_count), "latest_message": message, "latest_tool": _event_tool_name(event), "sequence": _safe_int(event.get("sequence", 0))}  # 新增代码+DesktopGUIBrowserWorkbench：返回稳定工具摘要；如果没有这行，前端无法渲染 console/network/downloads。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_safe_tool_summary 到此结束；如果没有边界说明，工具摘要裁剪范围不清楚。


def _safe_tabs_summary(provider_status: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，裁剪 tabs 状态；如果没有这段，原始 tab 列表可能过长或字段不稳。
    tabs = _as_dict(provider_status.get("tabs", {}))  # 新增代码+DesktopGUIBrowserWorkbench：读取 tabs 区块；如果没有这行，tab_count/active_tab 没有来源。
    raw_tabs = [tab for tab in _as_list(tabs.get("tabs", [])) if isinstance(tab, dict)]  # 新增代码+DesktopGUIBrowserWorkbench：读取并过滤 tab 列表；如果没有这行，坏 tab 会进入 GUI。
    active_tab = _as_dict(tabs.get("active_tab", provider_status.get("active_target", {})))  # 新增代码+DesktopGUIBrowserWorkbench：读取当前 tab；如果没有这行，活跃目标可能为空。
    safe_tabs = [{"title": _safe_text(tab.get("title"), "Untitled", 120), "url": _safe_text(tab.get("url"), "", 180), "active": bool(tab.get("active", False)), "page_id": _safe_text(tab.get("page_id") or tab.get("id"), "", 80)} for tab in raw_tabs[-10:]]  # 新增代码+DesktopGUIBrowserWorkbench：只返回最近 10 个安全 tab 摘要；如果没有这行，完整 URL 列表可能过大。
    return {"tab_count": _safe_int(tabs.get("tab_count", len(raw_tabs))), "active_tab": {"title": _safe_text(active_tab.get("title"), "暂无活跃目标", 120), "url": _safe_text(active_tab.get("url"), "", 180), "host": _safe_text(active_tab.get("host") or active_tab.get("url_host"), "", 120), "page_id": _safe_text(active_tab.get("page_id") or active_tab.get("id"), "", 80)}, "tabs": safe_tabs}  # 新增代码+DesktopGUIBrowserWorkbench：返回稳定 tab 摘要；如果没有这行，前端无法显示 tab count 和 active tab。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_safe_tabs_summary 到此结束；如果没有边界说明，tab 字段裁剪范围不清楚。


def _safe_active_target(provider_status: dict[str, Any], tabs_summary: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，生成活跃目标摘要；如果没有这段，BrowserPanel 只能显示 provider 轨道。
    active_target = _as_dict(provider_status.get("active_target", {}))  # 新增代码+DesktopGUIBrowserWorkbench：读取 provider active_target；如果没有这行，无法优先使用后端目标摘要。
    active_tab = _as_dict(tabs_summary.get("active_tab", {}))  # 新增代码+DesktopGUIBrowserWorkbench：读取 tab 兜底；如果没有这行，无 active_target 时缺少数据。
    return {"kind": _safe_text(active_target.get("kind"), "tab", 80), "title": _safe_text(active_target.get("title") or active_tab.get("title"), "暂无活跃目标", 120), "url": _safe_text(active_target.get("url") or active_tab.get("url"), "", 180), "host": _safe_text(active_target.get("host") or active_target.get("url_host") or active_tab.get("host"), "未提供地址", 120)}  # 新增代码+DesktopGUIBrowserWorkbench：返回 BrowserPanel 可直接显示的目标；如果没有这行，前端要自己猜 host/title。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_safe_active_target 到此结束；如果没有边界说明，活跃目标逻辑不清楚。


def build_gui_browser_workbench_payload(workspace: str | Path, snapshot: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，构建 Browser 工作台 payload；如果没有这段，前端只能显示旧 provider 摘要。
    root = _workspace_path(workspace)  # 新增代码+DesktopGUIBrowserWorkbench：规范化工作区；如果没有这行，状态快照和事件 store 路径不稳定。
    safe_snapshot, degraded, safe_error = _browser_snapshot(root, snapshot)  # 新增代码+DesktopGUIBrowserWorkbench：读取或复用快照；如果没有这行，后续没有 browser/status_events 数据。
    browser = _as_dict(safe_snapshot.get("browser", {}))  # 新增代码+DesktopGUIBrowserWorkbench：读取 browser 区块；如果没有这行，provider_status 没有父级来源。
    provider_status = _as_dict(browser.get("provider_status", {}))  # 新增代码+DesktopGUIBrowserWorkbench：读取 provider_status；如果没有这行，providers/tabs/extension 都不可见。
    providers = _as_dict(provider_status.get("providers", {}))  # 新增代码+DesktopGUIBrowserWorkbench：读取 provider 集合；如果没有这行，visible/CDP/extension 轨道无法显示。
    extension = _as_dict(provider_status.get("chrome_extension", {}))  # 新增代码+DesktopGUIBrowserWorkbench：读取扩展状态；如果没有这行，pending commands 和配对状态不可见。
    native_host = _as_dict(provider_status.get("native_host", {}))  # 新增代码+DesktopGUIBrowserWorkbench：读取 native host 状态；如果没有这行，用户无法区分扩展和 native host 问题。
    tabs_summary = _safe_tabs_summary(provider_status)  # 新增代码+DesktopGUIBrowserWorkbench：裁剪 tab 状态；如果没有这行，tab count 和 active tab 不稳定。
    active_target = _safe_active_target(provider_status, tabs_summary)  # 新增代码+DesktopGUIBrowserWorkbench：生成活跃目标摘要；如果没有这行，前端还要拼接多个字段。
    events = _events_from_snapshot(root, safe_snapshot)  # 新增代码+DesktopGUIBrowserWorkbench：读取状态事件尾巴；如果没有这行，console/network/downloads 摘要为空。
    console_summary = _safe_tool_summary(_latest_browser_event(events, GUI_BROWSER_CONSOLE_TOOLS), "最近没有捕获到 console 输出。")  # 新增代码+DesktopGUIBrowserWorkbench：生成 console 摘要；如果没有这行，用户看不到 console 错误线索。
    network_summary = _safe_tool_summary(_latest_browser_event(events, GUI_BROWSER_NETWORK_TOOLS), "最近没有捕获到网络请求或响应。")  # 新增代码+DesktopGUIBrowserWorkbench：生成 network 摘要；如果没有这行，用户看不到网络错误线索。
    downloads_summary = _safe_tool_summary(_latest_browser_event(events, GUI_BROWSER_DOWNLOAD_TOOLS), "最近没有捕获到下载。")  # 新增代码+DesktopGUIBrowserWorkbench：生成 downloads 摘要；如果没有这行，用户看不到下载记录线索。
    recordings = _as_dict(browser.get("recordings", {}))  # 新增代码+DesktopGUIBrowserWorkbench：读取录制证据摘要；如果没有这行，可回放视觉证据不可见。
    replay = {"available": True, "mode": "dry_run_only", "reason": "复用 browser_replay，默认只生成安全回放计划。"}  # 新增代码+DesktopGUIBrowserWorkbench：声明回放能力边界；如果没有这行，用户不知道 replay 是否会自动操作网页。
    return {"providers": providers, "extension": extension, "native_host": native_host, "tabs": tabs_summary, "active_target": active_target, "console": console_summary, "network": network_summary, "downloads": downloads_summary, "recordings": {"recording_count": _safe_int(recordings.get("recording_count", 0)), "latest": _as_dict(recordings.get("latest", {}))}, "replay": replay, "status_degraded": bool(degraded or browser.get("degraded") or provider_status.get("error")), "safe_error": safe_error or (GUI_BROWSER_SAFE_ERROR if provider_status.get("error") else ""), "control_source": GUI_BROWSER_CONTROL_SOURCE}  # 新增代码+DesktopGUIBrowserWorkbench：返回完整 Browser 工作台字段；如果没有这行，前端无法诊断 provider/tabs/console/network/downloads/replay。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，build_gui_browser_workbench_payload 到此结束；如果没有边界说明，payload 范围不清楚。


def _append_browser_action_event(root: Path, action: str, status: str, message: str, extra: dict[str, Any] | None = None) -> int:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，记录 GUI Browser 动作事件；如果没有这段，按钮点击没有审计证据。
    payload = {"action": action, "status": status, "message": message, "control_source": GUI_BROWSER_CONTROL_SOURCE, "browser_action_count": 0}  # 新增代码+DesktopGUIBrowserWorkbench：构造通用事件正文；如果没有这行，事件消费者看不懂动作来源。
    payload.update(extra or {})  # 新增代码+DesktopGUIBrowserWorkbench：合并动作专属摘要；如果没有这行，open URL origin 或刷新事件数无法记录。
    event = _status_store(root).append("gui_browser_action", payload)  # 新增代码+DesktopGUIBrowserWorkbench：写入统一状态事件；如果没有这行，右侧状态页不会出现 Browser 动作。
    return max(0, event.sequence - 1)  # 新增代码+DesktopGUIBrowserWorkbench：返回前端补拉事件的游标；如果没有这行，GUI 可能错过刚写入的事件。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，_append_browser_action_event 到此结束；如果没有边界说明，事件写入范围不清楚。


def build_gui_browser_action_payload(action: str, workspace: str | Path, body: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，处理 Browser 工作台最小安全动作；如果没有这段，POST 路由只能返回 404。
    root = _workspace_path(workspace)  # 新增代码+DesktopGUIBrowserWorkbench：规范化工作区；如果没有这行，动作事件会写错目录。
    request_body = _as_dict(body)  # 新增代码+DesktopGUIBrowserWorkbench：收敛请求体；如果没有这行，坏 JSON 会污染逻辑。
    if action not in GUI_BROWSER_ACTIONS:  # 新增代码+DesktopGUIBrowserWorkbench：拒绝未知动作；如果没有这行，非法 action 可能误返回成功。
        sequence = _append_browser_action_event(root, action, "unsupported", "未知 Browser GUI 动作。")  # 新增代码+DesktopGUIBrowserWorkbench：记录未知动作；如果没有这行，排查错误按钮没有证据。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": action, "status": "unsupported", "message": "未知 Browser GUI 动作。", "safe_error": "unsupported", "events_after_sequence": sequence, "browser": build_gui_browser_workbench_payload(root)}  # 新增代码+DesktopGUIBrowserWorkbench：返回结构化不支持；如果没有这行，前端无法稳定显示错误。
    if action == "refresh-status":  # 新增代码+DesktopGUIBrowserWorkbench：处理刷新状态动作；如果没有这行，刷新按钮没有后端路径。
        snapshot, degraded, safe_error = _browser_snapshot(root)  # 新增代码+DesktopGUIBrowserWorkbench：读取最新状态快照；如果没有这行，刷新动作不会更新事实。
        event_count = len(_as_list(snapshot.get("status_events", [])))  # 新增代码+DesktopGUIBrowserWorkbench：统计快照事件数；如果没有这行，审计缺少读取范围。
        message = "已刷新浏览器状态，未绕过 agent 权限策略执行网页动作。"  # 新增代码+DesktopGUIBrowserWorkbench：准备用户可读说明；如果没有这行，用户可能误以为刷新会控制网页。
        sequence = _append_browser_action_event(root, action, "refreshed", message, {"snapshot_event_count": event_count})  # 新增代码+DesktopGUIBrowserWorkbench：记录刷新事件；如果没有这行，状态页没有按钮证据。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": action, "status": "refreshed", "message": message, "safe_error": safe_error if degraded else "", "events_after_sequence": sequence, "browser": build_gui_browser_workbench_payload(root, snapshot)}  # 新增代码+DesktopGUIBrowserWorkbench：返回刷新后的 Browser 工作台；如果没有这行，前端仍要等下一轮轮询。
    url_parts = _safe_url_parts(request_body.get("url", ""))  # 新增代码+DesktopGUIBrowserWorkbench：校验并脱敏 open URL；如果没有这行，open 可能接受危险 scheme。
    if not url_parts["valid"]:  # 新增代码+DesktopGUIBrowserWorkbench：拒绝非 http/https URL；如果没有这行，file/javascript URL 可能进入浏览器链路。
        message = "浏览器打开请求被拒绝：只支持 http:// 或 https:// URL。"  # 新增代码+DesktopGUIBrowserWorkbench：准备拒绝说明；如果没有这行，用户不知道哪里错了。
        sequence = _append_browser_action_event(root, action, "invalid_url", message, {"url_present": bool(url_parts["raw_url_present"])})  # 新增代码+DesktopGUIBrowserWorkbench：记录拒绝事件但不写完整 URL；如果没有这行，失败没有审计或可能泄露 query。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": action, "status": "invalid_url", "message": message, "safe_error": "invalid_url", "events_after_sequence": sequence, "browser": build_gui_browser_workbench_payload(root)}  # 新增代码+DesktopGUIBrowserWorkbench：返回拒绝 payload；如果没有这行，前端按钮失败无反馈。
    message = f"已记录打开 {url_parts['origin']} 的请求；GUI 不绕过现有 Browser/agent 权限策略直接控制网页。"  # 新增代码+DesktopGUIBrowserWorkbench：准备接受说明但明确边界；如果没有这行，用户可能以为已经打开网页。
    sequence = _append_browser_action_event(root, action, "recorded", message, {"url_origin": url_parts["origin"], "url_host": url_parts["host"]})  # 新增代码+DesktopGUIBrowserWorkbench：只记录 origin/host；如果没有这行，完整 query 可能泄露到事件流。
    return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "action": action, "status": "recorded", "message": message, "safe_error": "", "events_after_sequence": sequence, "browser": build_gui_browser_workbench_payload(root)}  # 新增代码+DesktopGUIBrowserWorkbench：返回 open 请求响应；如果没有这行，前端无法更新工作台和主线程反馈。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，build_gui_browser_action_payload 到此结束；如果没有边界说明，动作范围不清楚。


def build_gui_browser_collection_payload(kind: str, workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIBrowserWorkbench：函数段开始，返回 tabs/console/network 只读集合；如果没有这段，GET 路由只能复制 workbench 逻辑。
    root = _workspace_path(workspace)  # 新增代码+DesktopGUIBrowserWorkbench：规范化工作区；如果没有这行，collection endpoint 路径不稳定。
    browser = build_gui_browser_workbench_payload(root)  # 新增代码+DesktopGUIBrowserWorkbench：复用同一个 Browser 工作台 payload；如果没有这行，集合 endpoint 会和主面板字段漂移。
    if kind not in GUI_BROWSER_COLLECTIONS:  # 新增代码+DesktopGUIBrowserWorkbench：拒绝未知集合；如果没有这行，非法 GET 可能返回误导数据。
        return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "kind": kind, "status": "unsupported", "safe_error": "unsupported", "data": {}, "browser": browser}  # 新增代码+DesktopGUIBrowserWorkbench：返回结构化不支持；如果没有这行，前端无法稳定处理错误。
    data = browser.get(kind, {}) if kind in {"console", "network"} else browser.get("tabs", {})  # 新增代码+DesktopGUIBrowserWorkbench：按集合名选取数据；如果没有这行，三个 GET 路由要各自拼 payload。
    return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "kind": kind, "status": "ready", "safe_error": "", "data": data, "browser": browser}  # 新增代码+DesktopGUIBrowserWorkbench：返回集合 payload；如果没有这行，client 无法读取 tabs/console/network。
# 新增代码+DesktopGUIBrowserWorkbench：函数段结束，build_gui_browser_collection_payload 到此结束；如果没有边界说明，集合 payload 范围不清楚。


__all__ = ["build_gui_browser_action_payload", "build_gui_browser_collection_payload", "build_gui_browser_workbench_payload"]  # 新增代码+DesktopGUIBrowserWorkbench：声明 bridge 可用公开 API；如果没有这行，未来维护者可能误用内部 helper。
