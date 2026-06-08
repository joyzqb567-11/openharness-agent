"""Chrome 扩展 native host 消息协议。"""  # 修改代码+ChromeExtensionStage6: 说明本文件同时处理只读消息和写动作结果；若没有这行代码，Stage 6 后的协议职责会被误读为只读。
from __future__ import annotations  # 新增代码+ChromeExtensionStage5: 延迟解析类型注解；若没有这行代码，复杂返回类型更脆弱。

from typing import Any  # 新增代码+ChromeExtensionStage5: JSON 消息字段需要通用类型；若没有这行代码，类型标注不清晰。

READONLY_ACTIONS = {"tabs_context", "read_page", "status"}  # 新增代码+ChromeExtensionStage5: 固定只读动作集合；若没有这行代码，协议无法区分读写边界。
WRITE_TOOL_ACTION_MAP = {"browser_click": "click", "browser_type": "type", "browser_press_key": "press_key", "browser_open": "navigate", "browser_wait": "wait", "browser_visual_locate": "visual_locate"}  # 新增代码+ChromeExtensionStage6: 统一 browser_* 工具名到插件动作名；若没有这行代码，provider 和扩展会各自猜动作名称。
WRITE_ACTIONS = set(WRITE_TOOL_ACTION_MAP.values()) | {"upload", "submit", "form_input", "scroll"}  # 修改代码+ChromeExtensionStage6: 明确所有写动作名称，其中 Stage 6 只通过命令队列开放安全子集；若没有这行代码，未知写动作可能混入协议。
SENSITIVE_KEYS = {"cookie", "cookies", "token", "password", "authorization", "localstorage", "sessionstorage", "storage"}  # 新增代码+ChromeExtensionStage5: 定义禁止进入响应的敏感字段名；若没有这行代码，扩展消息可能把隐私字段带给 host。


def _safe_text(value: Any, max_chars: int = 8000) -> str:  # 新增代码+ChromeExtensionStage5: 把任意值转成短文本；若没有这行代码，坏类型或超长文本可能破坏响应。
    text = str(value or "")  # 新增代码+ChromeExtensionStage5: 统一转字符串并处理空值；若没有这行代码，None 会进入响应。
    return text[:max(1, int(max_chars))]  # 新增代码+ChromeExtensionStage5: 截断到安全长度；若没有这行代码，页面正文可能撑爆 native message。


def _is_sensitive_key(key: Any) -> bool:  # 新增代码+ChromeExtensionStage5: 判断字段名是否敏感；若没有这行代码，多处过滤会重复写字符串判断。
    lowered = str(key or "").lower()  # 新增代码+ChromeExtensionStage5: 字段名转小写；若没有这行代码，大小写变化可能绕过过滤。
    return any(marker in lowered for marker in SENSITIVE_KEYS)  # 新增代码+ChromeExtensionStage5: 命中任一敏感片段就拒绝；若没有这行代码，cookie/token 字段可能保留。


def _sanitize_json(value: Any, max_chars: int = 8000) -> Any:  # 新增代码+ChromeExtensionStage6: 递归清理扩展结果；若没有这行代码，action_result 嵌套对象里的敏感字段可能漏掉。
    if isinstance(value, dict):  # 新增代码+ChromeExtensionStage6: 字典需要逐项检查键名；若没有这行代码，嵌套 result 无法过滤。
        return {str(key): _sanitize_json(item, max_chars) for key, item in value.items() if not _is_sensitive_key(key)}  # 新增代码+ChromeExtensionStage6: 删除敏感键并递归清理值；若没有这行代码，cookie/token 会进入 action 结果。
    if isinstance(value, list):  # 新增代码+ChromeExtensionStage6: 列表需要逐个元素清理；若没有这行代码，元素数组里的敏感字段会漏掉。
        return [_sanitize_json(item, max_chars) for item in value[:200]]  # 新增代码+ChromeExtensionStage6: 限制列表长度并递归清理；若没有这行代码，大页面结果可能撑爆消息。
    if isinstance(value, (str, int, float, bool)) or value is None:  # 新增代码+ChromeExtensionStage6: JSON 标量可以保留但字符串需要截断；若没有这行代码，普通值会被不必要字符串化。
        return _safe_text(value, max_chars) if isinstance(value, str) else value  # 新增代码+ChromeExtensionStage6: 字符串截断，其他标量原样返回；若没有这行代码，长文本可能过大。
    return _safe_text(value, max_chars)  # 新增代码+ChromeExtensionStage6: 未知对象转短文本；若没有这行代码，不可 JSON 序列化对象可能破坏响应。


def sanitize_tab(tab: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage5: 把 Chrome tab 对象转成安全摘要；若没有这行代码，完整 tab 对象可能带入多余字段。
    raw_id = tab.get("id", "")  # 新增代码+ChromeExtensionStage5: 读取 Chrome tab id；若没有这行代码，无法生成稳定 tab_id。
    tab_id = f"chrome-tab-{raw_id}" if str(raw_id or "") else ""  # 新增代码+ChromeExtensionStage5: 给 tab id 加 provider 前缀；若没有这行代码，插件 tab 和 CDP tab 可能混淆。
    return {"tab_id": tab_id, "chrome_tab_id": raw_id, "url": _safe_text(tab.get("url", ""), 2000), "title": _safe_text(tab.get("title", ""), 500), "active": bool(tab.get("active", False)), "window_id": tab.get("windowId", tab.get("window_id", ""))}  # 新增代码+ChromeExtensionStage5: 只返回安全 tab 摘要；若没有这行代码，敏感或无关字段会进入响应。


def sanitize_element(element: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage5: 清理页面元素摘要；若没有这行代码，content script 结果可能包含多余字段。
    return {"id": element.get("id", ""), "tag": _safe_text(element.get("tag", ""), 50), "label": _safe_text(element.get("label", ""), 200), "visible": bool(element.get("visible", False)), "x": element.get("x", 0), "y": element.get("y", 0), "width": element.get("width", 0), "height": element.get("height", 0)}  # 新增代码+ChromeExtensionStage5: 只保留只读视觉摘要；若没有这行代码，元素内部属性可能泄漏。


def _command_target(arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage6: 从统一工具参数中提取插件可执行目标；若没有这行代码，每个写工具会重复散落字段过滤。
    return {key: _sanitize_json(arguments.get(key, "")) for key in ("page_id", "element_id", "selector", "text", "label", "x", "y", "exact", "clear", "timeout_ms", "url", "key", "milliseconds")}  # 新增代码+ChromeExtensionStage6: 只保留浏览器动作需要的安全字段；若没有这行代码，任意参数可能进入扩展命令。


def build_write_command(tool_name: str, arguments: dict[str, Any] | None = None, command_id: str = "") -> dict[str, Any]:  # 新增代码+ChromeExtensionStage6: 构造 provider 发给扩展的写动作命令；若没有这行代码，插件写动作没有稳定协议。
    normalized_tool = str(tool_name or "")  # 新增代码+ChromeExtensionStage6: 规范化工具名；若没有这行代码，None 工具名会破坏映射。
    action = WRITE_TOOL_ACTION_MAP.get(normalized_tool, "")  # 新增代码+ChromeExtensionStage6: 把统一工具名映射为插件动作；若没有这行代码，扩展不知道要做 click 还是 type。
    if not action:  # 新增代码+ChromeExtensionStage6: 检查该工具是否属于 Stage 6 写动作集合；若没有这行代码，未知工具可能被当作命令发送。
        return _reject(f"chrome extension write command does not support tool: {normalized_tool}")  # 新增代码+ChromeExtensionStage6: 返回标准拒绝响应；若没有这行代码，调用方只会看到 KeyError。
    safe_arguments = dict(arguments or {})  # 新增代码+ChromeExtensionStage6: 复制参数避免污染调用方对象；若没有这行代码，清理过程可能改动原始参数。
    safe_command_id = _safe_text(command_id or safe_arguments.get("command_id", ""), 200)  # 新增代码+ChromeExtensionStage6: 读取稳定命令 id；若没有这行代码，结果无法可靠关联命令。
    target = _command_target(safe_arguments)  # 新增代码+ChromeExtensionStage6: 先构造通用目标字段；若没有这行代码，后续 type 特例会重复过滤。
    if normalized_tool == "browser_type":  # 新增代码+ChromeExtensionStage6: browser_type 的 text 是输入内容，不一定是定位文本；若没有这行代码，无目标输入会误把内容当元素标签。
        target["input_text"] = _sanitize_json(safe_arguments.get("text", ""))  # 新增代码+ChromeExtensionStage6: 单独保存输入内容；若没有这行代码，content script 无法区分输入值和定位文本。
        if not any(str(safe_arguments.get(key, "") or "").strip() for key in ("selector", "label", "element_id")):  # 新增代码+ChromeExtensionStage6: 没有显式定位目标时使用当前焦点；若没有这行代码，纯文本输入会误查同名元素。
            target["text"] = ""  # 新增代码+ChromeExtensionStage6: 清空定位文本让 content script 选择当前焦点；若没有这行代码，无目标输入会找不到元素。
    return {"ok": True, "kind": "browser_command", "command_id": safe_command_id, "tool_name": normalized_tool, "action": action, "target": target}  # 新增代码+ChromeExtensionStage6: 返回可发送给扩展的安全命令；若没有这行代码，provider 无法入队命令。


def _reject(message: str) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage5: 构造统一拒绝响应；若没有这行代码，错误格式会不稳定。
    return {"ok": False, "error": message}  # 新增代码+ChromeExtensionStage5: 返回机器可读失败对象；若没有这行代码，调用方无法判断失败。


def _tabs_context_response(message: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage5: 构造标签页上下文响应；若没有这行代码，tabs_context 动作没有实现。
    raw_tabs = message.get("tabs", [])  # 新增代码+ChromeExtensionStage5: 读取扩展传来的 tabs 数组；若没有这行代码，响应没有数据来源。
    tabs = [sanitize_tab(tab) for tab in raw_tabs if isinstance(tab, dict)]  # 新增代码+ChromeExtensionStage5: 逐个清理 tab；若没有这行代码，敏感字段可能进入响应。
    active_tab = next((tab for tab in tabs if tab.get("active")), tabs[0] if tabs else {})  # 新增代码+ChromeExtensionStage5: 找到 active tab 或首个兜底；若没有这行代码，状态缺少当前页。
    return {"ok": True, "action": "tabs_context", "provider": "chrome_extension", "tab_count": len(tabs), "active_tab_id": active_tab.get("tab_id", ""), "tabs": tabs}  # 新增代码+ChromeExtensionStage5: 返回标准 tabs context；若没有这行代码，provider 无法格式化结果。


def _read_page_response(message: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage5: 构造页面只读响应；若没有这行代码，browser_snapshot 无法走插件。
    tab = sanitize_tab(message.get("tab", {}) if isinstance(message.get("tab"), dict) else {})  # 新增代码+ChromeExtensionStage5: 清理活动 tab 摘要；若没有这行代码，页面内容缺少来源。
    page = message.get("page", {}) if isinstance(message.get("page"), dict) else {}  # 新增代码+ChromeExtensionStage5: 读取页面摘要对象；若没有这行代码，坏消息可能抛错。
    elements = [sanitize_element(item) for item in page.get("elements", []) if isinstance(item, dict)]  # 新增代码+ChromeExtensionStage5: 清理元素列表；若没有这行代码，页面元素可能带多余字段。
    visible_text = _safe_text(page.get("visibleText", page.get("visible_text", "")))  # 新增代码+ChromeExtensionStage5: 读取并截断可见文本；若没有这行代码，页面正文无法返回。
    return {"ok": True, "action": "read_page", "provider": "chrome_extension", "tab": tab, "visible_text": visible_text, "elements": elements}  # 新增代码+ChromeExtensionStage5: 返回标准页面快照；若没有这行代码，provider 无法生成 browser_snapshot。


def _action_result_response(message: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage6: 构造插件写动作执行结果响应；若没有这行代码，host 无法保存 click/type 的完成证据。
    command_id = _safe_text(message.get("command_id", ""), 200)  # 新增代码+ChromeExtensionStage6: 读取命令 id；若没有这行代码，结果无法关联 pending command。
    tool_name = _safe_text(message.get("tool_name", ""), 200)  # 新增代码+ChromeExtensionStage6: 读取统一工具名；若没有这行代码，状态页不知道哪个工具完成。
    ok = bool(message.get("ok", False))  # 新增代码+ChromeExtensionStage6: 读取成功状态；若没有这行代码，失败结果可能被误当成功。
    result = _sanitize_json(message.get("result", {}))  # 新增代码+ChromeExtensionStage6: 清理扩展回传结果；若没有这行代码，嵌套敏感内容可能泄露。
    error = _safe_text(message.get("error", ""), 2000)  # 新增代码+ChromeExtensionStage6: 读取短错误信息；若没有这行代码，失败时没有原因。
    return {"ok": ok, "action": "action_result", "provider": "chrome_extension", "command_id": command_id, "tool_name": tool_name, "result": result, "error": error}  # 新增代码+ChromeExtensionStage6: 返回标准动作结果；若没有这行代码，bridge 和 provider 无法统一解析。


def build_host_response(message: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ChromeExtensionStage5: native host 协议统一入口；若没有这行代码，host 和测试会重复分发逻辑。
    if not isinstance(message, dict):  # 新增代码+ChromeExtensionStage5: 消息必须是对象；若没有这行代码，坏输入可能抛底层异常。
        return _reject("read-only host requires an object message")  # 新增代码+ChromeExtensionStage5: 返回对象类型错误；若没有这行代码，调用方不知道格式问题。
    action = _safe_text(message.get("action", "")).strip()  # 新增代码+ChromeExtensionStage5: 读取并清理 action；若没有这行代码，空白动作会绕过判断。
    if action == "action_result":  # 新增代码+ChromeExtensionStage6: 写动作结果是扩展回传给 host 的合法消息；若没有这行代码，click/type 完成后无法落盘。
        return _action_result_response(message)  # 新增代码+ChromeExtensionStage6: 返回标准动作结果响应；若没有这行代码，bridge 无法消费结果。
    if action in WRITE_ACTIONS:  # 修改代码+ChromeExtensionStage6: 直接从扩展发来的写动作仍拒绝，写动作只能由 provider 命令队列下发；若没有这行代码，扩展可能绕过 provider 审计自行执行。
        return _reject(f"read-only direct host channel rejected write action; write action must be issued through queued command: {action}")  # 修改代码+ChromeExtensionStage6: 保留 Stage 5 只读直连边界并说明 Stage 6 命令队列入口；若没有这行代码，旧测试和新调用方都难以理解拒绝原因。
    if action not in READONLY_ACTIONS:  # 新增代码+ChromeExtensionStage5: 只允许白名单动作；若没有这行代码，未知动作可能被误处理。
        return _reject(f"read-only host does not support action: {action}")  # 新增代码+ChromeExtensionStage5: 返回不支持动作说明；若没有这行代码，调用方无法修正。
    if any(_is_sensitive_key(key) for key in message.keys()):  # 新增代码+ChromeExtensionStage5: 顶层敏感字段直接丢弃处理而不是信任；若没有这行代码，隐私字段可能保留。
        message = {key: value for key, value in message.items() if not _is_sensitive_key(key)}  # 新增代码+ChromeExtensionStage5: 删除敏感顶层字段；若没有这行代码，cookie/token 会进入后续响应。
    if action == "tabs_context":  # 新增代码+ChromeExtensionStage5: 分发 tabs_context；若没有这行代码，只读标签页动作无结果。
        return _tabs_context_response(message)  # 新增代码+ChromeExtensionStage5: 返回 tabs context；若没有这行代码，函数会继续到兜底。
    if action == "read_page":  # 新增代码+ChromeExtensionStage5: 分发 read_page；若没有这行代码，页面只读动作无结果。
        return _read_page_response(message)  # 新增代码+ChromeExtensionStage5: 返回页面快照；若没有这行代码，函数会继续到兜底。
    return {"ok": True, "action": "status", "provider": "chrome_extension", "read_only": True}  # 新增代码+ChromeExtensionStage5: 返回状态动作响应；若没有这行代码，status 无实现。
