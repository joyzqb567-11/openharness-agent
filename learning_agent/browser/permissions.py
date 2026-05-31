"""真实浏览器客户模式授权 helper。"""  # 新增代码+BrowserSplit: 把客户模式白名单和进度提示集中到 browser 层；如果没有这行代码，授权逻辑会继续散在主 agent。
from typing import Any  # 新增代码+BrowserSplit: 为 JSON 参数字典标注通用类型；如果没有这行代码，函数签名边界不清楚。
try:  # 新增代码+BrowserSplit: 优先按包路径导入搜索工作流常量；如果没有这行代码，包模式无法复用白名单。
    from learning_agent.browser.search_workflow import REAL_BROWSER_ALWAYS_ALLOWED_TOOL_NAMES, google_url_allowed  # 新增代码+BrowserSplit: 导入固定白名单和 Google URL 判断；如果没有这行代码，权限模块会重复定义常量。
except ModuleNotFoundError as error:  # 新增代码+BrowserSplit: 兼容直接脚本模式下 learning_agent 包名不可用；如果没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.search_workflow"}:  # 新增代码+BrowserSplit: 只允许路径问题 fallback；如果没有这行代码，真实内部错误会被误吞。
        raise  # 新增代码+BrowserSplit: 重新抛出非路径错误；如果没有这行代码，排查权限模块会缺少根因。
    from browser.search_workflow import REAL_BROWSER_ALWAYS_ALLOWED_TOOL_NAMES, google_url_allowed  # 新增代码+BrowserSplit: 脚本模式下导入白名单和 URL 判断；如果没有这行代码，直接运行时客户模式不可用。

def real_browser_customer_mode_active(real_chrome_requested: bool, real_browser_information_task_requested: bool) -> bool:  # 新增代码+BrowserSplit: 判断当前轮次是否可启用客户模式；如果没有这行代码，主 agent 需要重复拼条件。
    return bool(real_chrome_requested and real_browser_information_task_requested)  # 新增代码+BrowserSplit: 只有真实浏览器意图和公开查询意图同时成立才启用；如果没有这行代码，普通浏览器动作可能被误放行。

def customer_mode_can_auto_approve_terminal_permission(permission_payload: dict[str, Any]) -> bool:  # 新增代码+BrowserSplit: 判断终端客户模式是否能自动允许 MCP 启动；如果没有这行代码，启动 MCP 仍会由主文件手写判断。
    if permission_payload.get("permission_kind") != "mcp_server_start":  # 新增代码+BrowserSplit: 终端入口目前只自动允许项目 MCP server 启动；如果没有这行代码，普通工具权限可能被过度放行。
        return False  # 新增代码+BrowserSplit: 非 MCP 启动权限回退人工确认；如果没有这行代码，敏感操作会绕过用户。
    allowed_servers = {"browser_search", "workspace_tools", "browser_automation"}  # 新增代码+BrowserSplit: 限定项目内置 MCP server；如果没有这行代码，未知 server 可能混入自动启动。
    server_names = {str(name).strip() for name in permission_payload.get("server_names", []) if str(name).strip()}  # 新增代码+BrowserSplit: 清理本次请求启动的 server 名；如果没有这行代码，白名单比较会不稳定。
    return bool(server_names) and server_names.issubset(allowed_servers)  # 新增代码+BrowserSplit: 只有全部 server 都在白名单时自动允许；如果没有这行代码，部分未知 server 可能被放行。

def real_browser_customer_auto_approve_reason(tool_name: str, arguments: dict[str, Any], *, customer_mode_active: bool) -> str:  # 新增代码+BrowserSplit: 返回客户模式工具自动授权原因；如果没有这行代码，主 agent 仍要手写白名单分支。
    if not customer_mode_active:  # 新增代码+BrowserSplit: 先确认当前任务属于客户模式适用范围；如果没有这行代码，任意浏览器工具都可能被放行。
        return ""  # 新增代码+BrowserSplit: 非客户模式返回空原因；如果没有这行代码，调用方无法保守回退。
    if tool_name in REAL_BROWSER_ALWAYS_ALLOWED_TOOL_NAMES:  # 新增代码+BrowserSplit: 固定白名单工具直接允许；如果没有这行代码，点击输入等待等动作仍会弹权限。
        return "真实浏览器公开查询客户模式白名单"  # 新增代码+BrowserSplit: 返回可审计原因；如果没有这行代码，进度日志不知道为什么自动授权。
    if tool_name == "mcp__browser_automation__browser_connect_real_chrome":  # 新增代码+BrowserSplit: 对高风险真实 Chrome 连接单独校验参数；如果没有这行代码，connect 无法默认放行。
        if arguments.get("confirm_real_profile") is True:  # 新增代码+BrowserSplit: 只有显式确认真实 profile 才允许连接；如果没有这行代码，模型漏填确认也可能越界连接。
            return "真实浏览器公开查询客户模式已默认允许真实 Chrome 连接"  # 新增代码+BrowserSplit: 返回连接授权原因；如果没有这行代码，审计看不出 connect 为什么没弹窗。
        return ""  # 新增代码+BrowserSplit: 缺少确认参数时回退人工权限；如果没有这行代码，错误参数也会被默认放行。
    if tool_name == "mcp__browser_automation__browser_open":  # 新增代码+BrowserSplit: 对打开网页工具做 URL 前缀限制；如果没有这行代码，browser_open 会变成任意网站放行。
        url = str(arguments.get("url", "") or "").strip()  # 新增代码+BrowserSplit: 读取并清理 URL；如果没有这行代码，URL 白名单无法判断真实目的地。
        if google_url_allowed(url):  # 新增代码+BrowserSplit: 只默认允许 Google 公共入口；如果没有这行代码，真实 Chrome 可能打开未授权网站。
            return "真实浏览器公开查询客户模式 Google URL 白名单"  # 新增代码+BrowserSplit: 返回 URL 放行原因；如果没有这行代码，审计缺少放行依据。
        return ""  # 新增代码+BrowserSplit: 非 Google URL 回退人工权限；如果没有这行代码，未知网站会被静默放行。
    return ""  # 新增代码+BrowserSplit: 其他工具默认不自动授权；如果没有这行代码，敏感 evaluate/network/downloads 可能被误允许。

def real_browser_customer_progress_message(tool_name: str, arguments: dict[str, Any]) -> str:  # 新增代码+BrowserSplit: 把工具动作转换成人类可见进度提示；如果没有这行代码，真实终端看不到 agent 下一步。
    if tool_name == "mcp__browser_automation__browser_profile_status":  # 新增代码+BrowserSplit: 识别状态检查动作；如果没有这行代码，第一步进度会很模糊。
        return "正在检查真实 Chrome 状态..."  # 新增代码+BrowserSplit: 输出安全前置检查提示；如果没有这行代码，用户只看到安静等待。
    if tool_name == "mcp__browser_automation__browser_connect_real_chrome":  # 新增代码+BrowserSplit: 识别真实 Chrome 连接动作；如果没有这行代码，用户不知道 agent 正在接入桌面 Chrome。
        return "正在连接真实 Chrome（仅使用公开查询白名单）..."  # 新增代码+BrowserSplit: 输出连接边界；如果没有这行代码，高风险动作缺少可见解释。
    if tool_name == "mcp__browser_automation__browser_open":  # 新增代码+BrowserSplit: 识别打开网页动作；如果没有这行代码，用户不知道即将打开哪个站点。
        return "正在打开 Google..."  # 新增代码+BrowserSplit: 输出目标站点；如果没有这行代码，终端进度不够贴近真实操作。
    if tool_name == "mcp__browser_automation__browser_snapshot":  # 新增代码+BrowserSplit: 识别页面快照读取；如果没有这行代码，用户不知道 agent 正在读取可见内容。
        return "正在读取页面可见内容..."  # 新增代码+BrowserSplit: 输出只读可见内容提示；如果没有这行代码，隐私边界不够直观。
    if tool_name == "mcp__browser_automation__browser_click":  # 新增代码+BrowserSplit: 识别点击动作；如果没有这行代码，用户不知道 agent 正在模拟点击。
        return "正在点击页面元素..."  # 新增代码+BrowserSplit: 输出点击进度；如果没有这行代码，真实浏览器动作缺少说明。
    if tool_name == "mcp__browser_automation__browser_type":  # 新增代码+BrowserSplit: 识别输入动作；如果没有这行代码，用户不知道 agent 正在输入什么。
        text_preview = str(arguments.get("text", "") or "").strip()[:120]  # 新增代码+BrowserSplit: 截断搜索词预览避免刷屏；如果没有这行代码，长 prompt 可能撑满终端。
        return f"正在输入搜索词：{text_preview}" if text_preview else "正在输入搜索词..."  # 新增代码+BrowserSplit: 显示搜索词或兜底提示；如果没有这行代码，输入动作不透明。
    if tool_name == "mcp__browser_automation__browser_press_key":  # 新增代码+BrowserSplit: 识别按键动作；如果没有这行代码，用户不知道搜索何时提交。
        key_name = str(arguments.get("key", "") or "按键").strip()  # 新增代码+BrowserSplit: 读取按键名；如果没有这行代码，Enter 等动作无法展示。
        return f"正在按 {key_name} 提交操作..."  # 新增代码+BrowserSplit: 输出按键进度；如果没有这行代码，提交搜索动作缺少说明。
    if tool_name == "mcp__browser_automation__browser_wait":  # 新增代码+BrowserSplit: 识别等待动作；如果没有这行代码，用户不知道 agent 是否卡住。
        return "正在等待页面加载..."  # 新增代码+BrowserSplit: 输出等待进度；如果没有这行代码，加载期间像无响应。
    if tool_name == "mcp__browser_automation__browser_screenshot":  # 新增代码+BrowserSplit: 识别截图动作；如果没有这行代码，用户不知道证据何时保存。
        return "正在保存搜索结果截图..."  # 新增代码+BrowserSplit: 输出截图进度；如果没有这行代码，证据落盘动作不透明。
    if tool_name == "mcp__browser_automation__browser_disconnect_real_chrome":  # 新增代码+BrowserSplit: 识别断开动作；如果没有这行代码，清理阶段可能显得突然。
        return "正在断开真实 Chrome 自动化连接..."  # 新增代码+BrowserSplit: 输出清理进度；如果没有这行代码，用户不知道连接已收束。
    return "正在执行真实浏览器操作..."  # 新增代码+BrowserSplit: 未细分工具的兜底提示；如果没有这行代码，新增白名单工具可能没有可见进度。
