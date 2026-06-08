"""Chrome extension provider adapter。"""  # 修改代码+ChromeExtensionStage6: 说明本 provider 已从只读 MVP 升级为受控写动作轨道；若没有这行代码，维护者可能误判能力边界。
from __future__ import annotations  # 新增代码+ChromeExtensionStage5: 延迟解析类型注解；若没有这行代码，bridge 类型引用更脆弱。

try:  # 新增代码+ChromeExtensionStage5: 优先按包路径导入插件 bridge 状态；若没有这行代码，正常包运行无法读取扩展结果。
    from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+ChromeExtensionStage5: 导入插件 bridge 状态；若没有这行代码，provider 无法读取扩展结果。
    from learning_agent.browser.site_permissions import BrowserSitePermissions, normalize_origin  # 新增代码+ChromeExtensionStage7: 导入站点权限模型和 origin 规范化；若没有这行代码，provider 无法执行 origin 权限检查。
except ModuleNotFoundError as import_error:  # 新增代码+ChromeExtensionStage5: 兼容 MCP server 直接脚本模式；若没有这行代码，stdio 启动时可能找不到 learning_agent 包。
    if import_error.name not in {"learning_agent", "learning_agent.browser_extension_host", "learning_agent.browser_extension_host.bridge_server", "learning_agent.browser", "learning_agent.browser.site_permissions"}:  # 修改代码+ChromeExtensionStage7: 只允许包路径缺失时 fallback；若没有这行代码，bridge 或权限内部 bug 会被误吞。
        raise  # 新增代码+ChromeExtensionStage5: 重新抛出真实内部导入错误；若没有这行代码，排查方向会被误导。
    from browser_extension_host.bridge_server import ChromeExtensionBridgeState  # type: ignore  # 新增代码+ChromeExtensionStage5: 脚本模式导入 bridge 状态；若没有这行代码，直接运行 MCP server 时插件 provider 不可用。
    from browser.site_permissions import BrowserSitePermissions, normalize_origin  # type: ignore  # 新增代码+ChromeExtensionStage7: 脚本模式导入站点权限模型；若没有这行代码，直接运行 MCP server 时权限门禁不可用。

from .protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+ChromeExtensionStage5: 导入 provider 健康状态和类型；若没有这行代码，adapter 无法注册到 Router。


CHROME_EXTENSION_READONLY_TOOLS = {  # 新增代码+ChromeExtensionStage5: 定义插件 MVP 支持的只读统一工具；若没有这行代码，provider 支持范围不可审计。
    "browser_tabs_context",  # 新增代码+ChromeExtensionStage5: 插件可读取当前 Chrome 标签页上下文；若没有这项，登录态任务无法走插件只读 context。
    "browser_snapshot",  # 新增代码+ChromeExtensionStage5: 插件可返回活动页可见文本快照；若没有这项，插件 MVP 只能列 tab 不能读页面。
    "browser_extension_status",  # 新增代码+ChromeExtensionStage5: 插件可返回连接状态；若没有这项，用户无法通过统一工具查看插件健康。
}  # 新增代码+ChromeExtensionStage5: 结束只读工具集合；若没有这行代码，Python 集合语法不完整。
CHROME_EXTENSION_WRITE_TOOLS = {  # 新增代码+ChromeExtensionStage6: 定义插件 Stage 6 支持的统一写动作工具；若没有这行代码，server 会继续回退旧 Playwright handler。
    "browser_click",  # 新增代码+ChromeExtensionStage6: 插件可通过 content script 点击页面元素；若没有这项，当前 Chrome 表单无法点击。
    "browser_type",  # 新增代码+ChromeExtensionStage6: 插件可向页面输入普通文本；若没有这项，当前 Chrome 表单无法填写。
    "browser_press_key",  # 新增代码+ChromeExtensionStage6: 插件可向当前焦点发送按键事件；若没有这项，Enter 提交等流程无法表达。
    "browser_open",  # 新增代码+ChromeExtensionStage6: 插件可导航当前 Chrome 标签页；若没有这项，当前 Chrome 登录态流程无法打开目标页。
    "browser_wait",  # 新增代码+ChromeExtensionStage6: 插件可等待页面或短时间延迟；若没有这项，多步骤流程没有稳定节拍。
    "browser_visual_locate",  # 新增代码+ChromeExtensionStage6: 插件可返回元素坐标候选；若没有这项，复杂页面缺少视觉定位辅助。
}  # 新增代码+ChromeExtensionStage6: 结束写工具集合；若没有这行代码，Python 集合语法不完整。
CHROME_EXTENSION_SUPPORTED_TOOLS = CHROME_EXTENSION_READONLY_TOOLS | CHROME_EXTENSION_WRITE_TOOLS  # 新增代码+ChromeExtensionStage6: 合并 provider 支持范围；若没有这行代码，supports_tool 会重复拼集合。
CHROME_EXTENSION_TOOL_PERMISSIONS = {"browser_tabs_context": "read", "browser_snapshot": "read", "browser_visual_locate": "read", "browser_wait": "read", "browser_open": "read", "browser_click": "click", "browser_type": "type", "browser_press_key": "type"}  # 新增代码+ChromeExtensionStage7: 定义统一工具需要的站点权限；若没有这行代码，权限检查会散落在 execute_tool 分支里。


class ChromeExtensionProvider:  # 修改代码+ChromeExtensionStage6: 定义 Chrome 插件 provider adapter；若没有这个类，Router 无法真正选择插件轨道。
    kind = BrowserProviderKind.CHROME_EXTENSION  # 新增代码+ChromeExtensionStage5: 声明 provider 类型；若没有这行代码，registry 无法按 chrome_extension 注册。

    def __init__(self, bridge_state: ChromeExtensionBridgeState, command_timeout_seconds: float = 5.0, site_permissions: BrowserSitePermissions | None = None) -> None:  # 修改代码+ChromeExtensionStage7: 接收 bridge 状态、写动作等待超时和站点权限对象；若没有这行代码，provider 无法执行 origin 权限检查。
        self.bridge_state = bridge_state  # 新增代码+ChromeExtensionStage5: 保存 bridge 引用；若没有这行代码，health 和 execute_tool 无法读取状态。
        self.command_timeout_seconds = max(0.05, float(command_timeout_seconds or 5.0))  # 新增代码+ChromeExtensionStage6: 保存最小等待超时；若没有这行代码，写动作可能无限等待或立即超时。
        self.site_permissions = site_permissions or BrowserSitePermissions(strict=False)  # 新增代码+ChromeExtensionStage7: 保存站点权限对象，默认非严格兼容旧行为；若没有这行代码，Stage 6 现有流程会突然被全部拦截。

    def health(self) -> BrowserProviderHealth:  # 修改代码+Phase19BrowserRouting: 返回插件 provider 的生产级健康状态；如果没有这段函数，Router 不知道插件是否已连接、已配对、支持哪些工具。
        pairing = self.bridge_state.pairing_summary()  # 新增代码+Phase19BrowserRouting: 读取已保存的 extension/device/session 配对摘要；如果没有这行代码，连接状态会被误当成可信配对状态。
        paired = bool(pairing.get("extension_id") and pairing.get("device_id") and pairing.get("session_id"))  # 新增代码+Phase19BrowserRouting: 同时要求 extension_id、device_id、session_id 存在才算配对完成；如果没有这行代码，半截配对也可能被当成可用。
        metadata = {"connected": self.bridge_state.connected(), "paired": paired, "extension_id": pairing.get("extension_id", ""), "device_id": pairing.get("device_id", ""), "session_id": pairing.get("session_id", ""), "supported_tools": sorted(CHROME_EXTENSION_SUPPORTED_TOOLS)}  # 新增代码+Phase19BrowserRouting: 汇总健康证据和支持工具清单；如果没有这行代码，router 和事件日志无法解释 provider 决策。
        if not self.bridge_state.connected():  # 新增代码+Phase19BrowserRouting: 插件没连接时立即判不可用；如果没有这行代码，未连接插件可能被错误选中。
            return BrowserProviderHealth.unavailable(self.kind, "chrome_extension_bridge_not_connected", metadata=metadata)  # 修改代码+Phase19BrowserRouting: 返回未连接原因并保留诊断 metadata；如果没有这行代码，状态页只能看到失败却看不到证据。
        if not paired:  # 新增代码+Phase19BrowserRouting: 插件连接但未配对时也必须判不可用；如果没有这行代码，未授权扩展连接会绕过配对门禁。
            return BrowserProviderHealth.unavailable(self.kind, "chrome_extension_not_paired", metadata=metadata)  # 新增代码+Phase19BrowserRouting: 返回未配对原因并保留工具清单；如果没有这行代码，用户不知道下一步应该先完成配对。
        return BrowserProviderHealth.available(self.kind, "chrome_extension_bridge_connected_and_paired", metadata=metadata)  # 修改代码+Phase19BrowserRouting: 只有连接且配对后才返回可用；如果没有这行代码，生产级 extension 通道不会有明确成功条件。

    def supports_tool(self, tool_name: str) -> bool:  # 修改代码+ChromeExtensionStage6: 判断插件 provider 是否支持统一浏览器工具；若没有这行代码，server 可能把工具发给错误轨道。
        return tool_name in CHROME_EXTENSION_SUPPORTED_TOOLS  # 修改代码+ChromeExtensionStage6: 允许 Stage 5 只读工具和 Stage 6 受控写动作；若没有这行代码，插件写动作无法接管。

    def execute_tool(self, tool_name: str, arguments: dict[str, object]) -> str:  # 修改代码+ChromeExtensionStage6: 通过插件 provider 执行统一只读或写工具；若没有这行代码，adapter 只有健康状态没有能力。
        if not self.supports_tool(tool_name):  # 新增代码+ChromeExtensionStage5: 拒绝不属于只读 MVP 的工具；若没有这行代码，写动作可能误入插件 provider。
            raise RuntimeError(f"chrome_extension provider 不支持工具：{tool_name}")  # 修改代码+ChromeExtensionStage6: 返回清楚错误；若没有这行代码，调用方只会看到 AttributeError。
        self._ensure_site_permission(tool_name, dict(arguments or {}))  # 新增代码+ChromeExtensionStage7: 执行读写工具前检查 origin 权限；若没有这行代码，插件连接后可直接读写任意站点。
        if tool_name == "browser_tabs_context":  # 新增代码+ChromeExtensionStage5: tabs context 工具分支；若没有这行代码，标签页上下文无法返回。
            return self.bridge_state.tabs_context_text()  # 新增代码+ChromeExtensionStage5: 返回 bridge 中的标签页上下文；若没有这行代码，工具无输出。
        if tool_name == "browser_snapshot":  # 新增代码+ChromeExtensionStage5: 页面快照工具分支；若没有这行代码，活动页只读内容无法返回。
            return self.bridge_state.snapshot_text()  # 新增代码+ChromeExtensionStage5: 返回 bridge 中的页面快照；若没有这行代码，snapshot 无输出。
        if tool_name == "browser_extension_status":  # 新增代码+ChromeExtensionStage6: 状态工具单独返回 bridge 状态；若没有这行代码，状态查询会被当作写动作入队。
            return self.bridge_state.status_text()  # 新增代码+ChromeExtensionStage6: 返回扩展连接和命令队列状态；若没有这行代码，browser_extension_status 无输出。
        return self._execute_write_tool(tool_name, dict(arguments or {}))  # 新增代码+ChromeExtensionStage6: 其他支持工具走写命令队列；若没有这行代码，点击输入不会发给插件。

    def _permission_for_tool(self, tool_name: str, arguments: dict[str, object]) -> str:  # 新增代码+ChromeExtensionStage7: 计算统一工具需要的权限类型；若没有这行代码，工具到权限的映射会分散。
        if tool_name == "browser_press_key" and str(arguments.get("key", "") or "").strip().lower() == "enter":  # 新增代码+ChromeExtensionStage7: Enter 通常可能触发表单提交；若没有这行代码，高风险提交会只按普通输入授权处理。
            return "submit"  # 新增代码+ChromeExtensionStage7: Enter 使用 submit 权限；若没有这行代码，提交类动作不能单独授权。
        return CHROME_EXTENSION_TOOL_PERMISSIONS.get(tool_name, "read")  # 新增代码+ChromeExtensionStage7: 默认未知辅助工具按 read 处理；若没有这行代码，权限映射缺省会抛错。

    def _url_for_permission(self, tool_name: str, arguments: dict[str, object]) -> str:  # 新增代码+ChromeExtensionStage7: 找到本次工具对应的 URL；若没有这行代码，origin 权限无法判断目标站点。
        if tool_name == "browser_open" and str(arguments.get("url", "") or "").strip():  # 新增代码+ChromeExtensionStage7: 导航工具按目标 URL 授权；若没有这行代码，打开新站点会只检查旧 active tab。
            return str(arguments.get("url", "") or "").strip()  # 新增代码+ChromeExtensionStage7: 返回目标 URL；若没有这行代码，browser_open 权限检查会错位。
        page_id = str(arguments.get("page_id", "") or "").strip()  # 新增代码+ChromeExtensionStage7: 读取目标 page_id；若没有这行代码，指定标签页动作无法定位 URL。
        if page_id:  # 新增代码+ChromeExtensionStage7: 指定 page_id 时按该 tab 查询 URL；若没有这行代码，可能误用 active tab 权限。
            return self.bridge_state.url_for_page_id(page_id)  # 新增代码+ChromeExtensionStage7: 返回 page_id 对应 URL；若没有这行代码，provider 无法处理非 active tab。
        return self.bridge_state.active_tab_url()  # 新增代码+ChromeExtensionStage7: 未指定 page_id 时按 active tab 授权；若没有这行代码，普通工具调用无法检查 origin。

    def _ensure_site_permission(self, tool_name: str, arguments: dict[str, object]) -> None:  # 新增代码+ChromeExtensionStage7: 统一执行插件站点权限检查；若没有这行代码，读写分支容易漏拦。
        if tool_name == "browser_extension_status":  # 新增代码+ChromeExtensionStage7: 状态工具不读取页面内容也不操作页面；若没有这行代码，未授权 origin 连状态都看不到。
            return  # 新增代码+ChromeExtensionStage7: 状态工具直接放行；若没有这行代码，用户无法诊断为什么不可用。
        url = self._url_for_permission(tool_name, arguments)  # 新增代码+ChromeExtensionStage7: 读取目标 URL；若没有这行代码，权限检查没有 origin。
        if not url:  # 新增代码+ChromeExtensionStage7: 严格模式下没有 URL 也不能随便放行；若没有这行代码，空 context 会绕过权限。
            if self.site_permissions.strict:  # 新增代码+ChromeExtensionStage7: 只有严格模式才拦截空 URL；若没有这行代码，兼容模式会被破坏。
                raise PermissionError("Chrome 插件站点权限拒绝：当前没有可判断的 tab URL，请先读取 browser_tabs_context 或授权目标页面。")  # 新增代码+ChromeExtensionStage7: 给出修复提示；若没有这行代码，模型不知道下一步。
            return  # 新增代码+ChromeExtensionStage7: 非严格模式保持兼容；若没有这行代码，旧任务会失败。
        permission = self._permission_for_tool(tool_name, arguments)  # 新增代码+ChromeExtensionStage7: 计算动作需要的权限；若没有这行代码，无法区分 read/click/type/submit。
        self.site_permissions.require(url, permission)  # 新增代码+ChromeExtensionStage7: 执行权限检查并在失败时抛 PermissionError；若没有这行代码，权限对象不会生效。
        normalize_origin(url)  # 新增代码+ChromeExtensionStage7: 对 URL 做一次规范化校验；若没有这行代码，异常 URL 可能进入扩展命令。

    def _execute_write_tool(self, tool_name: str, arguments: dict[str, object]) -> str:  # 新增代码+ChromeExtensionStage6: 执行插件写动作并等待结果；若没有这行代码，execute_tool 会变得过长且难测试。
        if not self.bridge_state.connected():  # 新增代码+ChromeExtensionStage6: 写动作必须在扩展连接后执行；若没有这行代码，命令会发到没人处理的队列。
            raise RuntimeError("Chrome extension provider 未连接，不能执行写动作。")  # 新增代码+ChromeExtensionStage6: 返回清楚不可用错误；若没有这行代码，用户不知道要先安装/连接扩展。
        command = self.bridge_state.enqueue_command(tool_name, arguments)  # 新增代码+ChromeExtensionStage6: 把工具调用转成 pending command；若没有这行代码，扩展无法收到动作。
        command_id = str(command.get("command_id", "") or "")  # 新增代码+ChromeExtensionStage6: 读取命令 id；若没有这行代码，等待结果没有目标。
        timeout_seconds = self._timeout_for_arguments(arguments)  # 新增代码+ChromeExtensionStage6: 根据工具参数计算等待时间；若没有这行代码，所有动作都只能用固定等待。
        result = self.bridge_state.wait_for_command_result(command_id, timeout_seconds)  # 新增代码+ChromeExtensionStage6: 等待扩展回传结果；若没有这行代码，provider 只能返回“已发送”。
        if not bool(result.get("ok", False)):  # 新增代码+ChromeExtensionStage6: 扩展执行失败时转成工具失败；若没有这行代码，失败点击可能被误报成功。
            raise RuntimeError(str(result.get("error", "Chrome 插件写动作失败。")))  # 新增代码+ChromeExtensionStage6: 抛出脱敏错误；若没有这行代码，调用方看不到失败原因。
        return self._format_write_result(tool_name, command_id, result)  # 新增代码+ChromeExtensionStage6: 返回可读动作结果；若没有这行代码，模型拿不到执行证据。

    def _timeout_for_arguments(self, arguments: dict[str, object]) -> float:  # 新增代码+ChromeExtensionStage6: 从参数里读取动作等待超时；若没有这行代码，长页面导航无法调整等待。
        raw_timeout_ms = arguments.get("timeout_ms", 0)  # 新增代码+ChromeExtensionStage6: 读取毫秒超时参数；若没有这行代码，用户设置不会生效。
        try:  # 新增代码+ChromeExtensionStage6: 转换用户参数可能失败；若没有这行代码，坏参数会产生不友好 ValueError。
            timeout_ms = int(str(raw_timeout_ms or "0"))  # 新增代码+ChromeExtensionStage6: 把参数转成整数毫秒；若没有这行代码，字符串数字无法使用。
        except (TypeError, ValueError, OverflowError):  # 新增代码+ChromeExtensionStage6: 捕获无法转换的参数；若没有这行代码，异常类型不稳定。
            timeout_ms = 0  # 新增代码+ChromeExtensionStage6: 坏参数回退默认值；若没有这行代码，provider 会直接失败。
        if timeout_ms > 0:  # 新增代码+ChromeExtensionStage6: 用户显式设置超时时使用它；若没有这行代码，timeout_ms 永远被忽略。
            return max(0.05, min(30.0, timeout_ms / 1000.0))  # 新增代码+ChromeExtensionStage6: 限制等待在 0.05 到 30 秒；若没有这行代码，超大等待可能卡住任务。
        return self.command_timeout_seconds  # 新增代码+ChromeExtensionStage6: 未设置时使用 provider 默认值；若没有这行代码，默认超时没有来源。

    def _format_write_result(self, tool_name: str, command_id: str, result: dict[str, object]) -> str:  # 新增代码+ChromeExtensionStage6: 把插件动作结果转成人类可读文本；若没有这行代码，模型只能看到原始 dict。
        payload = result.get("result", {}) if isinstance(result.get("result", {}), dict) else {}  # 新增代码+ChromeExtensionStage6: 读取扩展结果 payload；若没有这行代码，坏结果可能抛错。
        tab = payload.get("tab", {}) if isinstance(payload.get("tab", {}), dict) else {}  # 新增代码+ChromeExtensionStage6: 读取 tab 摘要；若没有这行代码，输出缺少页面来源。
        visible_text = str(payload.get("visibleText", payload.get("visible_text", "")) or "")  # 新增代码+ChromeExtensionStage6: 读取动作后的页面可见文本摘要；若没有这行代码，用户看不到页面反馈。
        summary = str(payload.get("summary", "") or visible_text)[:800]  # 新增代码+ChromeExtensionStage6: 优先使用动作摘要并截断；若没有这行代码，长正文可能污染工具输出。
        return "\n".join([f"{tool_name} 成功", "provider=chrome_extension", f"command_id={command_id}", f"tab_id={tab.get('tab_id', tab.get('id', ''))}", f"URL={tab.get('url', '')}", f"结果摘要：{summary}"])  # 新增代码+ChromeExtensionStage6: 返回稳定多行结果；若没有这行代码，验收器难以匹配 provider 和 command_id。
