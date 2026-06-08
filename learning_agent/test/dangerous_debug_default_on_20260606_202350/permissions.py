"""真实浏览器客户模式授权 helper。"""  # 新增代码+BrowserSplit: 把客户模式白名单和进度提示集中到 browser 层；如果没有这行代码，授权逻辑会继续散在主 agent。
import os  # 新增代码+危险调试权限: 读取本地调试跳过权限环境变量；如果没有这行代码，start_oauth_agent.ps1 设置的危险模式无法被 Python 识别。
from typing import Any  # 新增代码+BrowserSplit: 为 JSON 参数字典标注通用类型；如果没有这行代码，函数签名边界不清楚。
try:  # 新增代码+BrowserSplit: 优先按包路径导入搜索工作流常量；如果没有这行代码，包模式无法复用白名单。
    from learning_agent.browser.search_workflow import REAL_BROWSER_ALWAYS_ALLOWED_TOOL_NAMES, google_url_allowed  # 新增代码+BrowserSplit: 导入固定白名单和 Google URL 判断；如果没有这行代码，权限模块会重复定义常量。
except ModuleNotFoundError as error:  # 新增代码+BrowserSplit: 兼容直接脚本模式下 learning_agent 包名不可用；如果没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.search_workflow"}:  # 新增代码+BrowserSplit: 只允许路径问题 fallback；如果没有这行代码，真实内部错误会被误吞。
        raise  # 新增代码+BrowserSplit: 重新抛出非路径错误；如果没有这行代码，排查权限模块会缺少根因。
    from browser.search_workflow import REAL_BROWSER_ALWAYS_ALLOWED_TOOL_NAMES, google_url_allowed  # 新增代码+BrowserSplit: 脚本模式下导入白名单和 URL 判断；如果没有这行代码，直接运行时客户模式不可用。

DANGEROUS_SKIP_PERMISSIONS_ENV_VAR = "LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS"  # 新增代码+危险调试权限: 统一声明危险跳过权限的环境变量名；如果没有这行代码，各入口会硬编码字符串导致容易写错。
DANGEROUS_SKIP_PERMISSION_TRUE_VALUES = {"1", "true", "yes", "y", "on"}  # 新增代码+危险调试权限: 定义哪些值表示开启危险模式；如果没有这行代码，用户无法用常见布尔写法启用调试放行。
DANGEROUS_SKIP_PERMISSION_FALSE_VALUES = {"0", "false", "no", "n", "off"}  # 新增代码+DangerousDebugDefault: 定义哪些值表示显式关闭危险模式；如果没有这行代码，默认开启后正式产品或手动安全模式就没有清晰退出开关。

def dangerously_skip_permissions_enabled() -> bool:  # 修改代码+DangerousDebugDefault: 函数段开始，判断当前进程是否启用开发期默认危险调试权限；如果没有这段函数，权限层无法统一决定是否跳过人工确认。
    raw_value = os.environ.get(DANGEROUS_SKIP_PERMISSIONS_ENV_VAR)  # 修改代码+DangerousDebugDefault: 读取原始环境变量并保留 None，用来区分“没设置”和“显式设置”；如果没有这行代码，核心层无法实现缺省默认开启。
    if raw_value is None:  # 新增代码+DangerousDebugDefault: 环境变量完全不存在时进入开发期默认开启分支；如果没有这行代码，非 ps1/controller 入口会继续保守卡在 y/N 权限确认。
        return True  # 新增代码+DangerousDebugDefault: 未设置即默认开启危险调试模式；如果没有这行代码，用户每次本地调试仍可能被权限弹窗打断。
    normalized_value = str(raw_value or "").strip().lower()  # 修改代码+DangerousDebugDefault: 清理空白并统一大小写，同时允许空字符串走默认开启；如果没有这行代码，" False " 或 " 0 " 这类写法会被误判。
    if normalized_value in DANGEROUS_SKIP_PERMISSION_FALSE_VALUES:  # 新增代码+DangerousDebugDefault: 识别用户或正式产品显式关闭危险模式；如果没有这行代码，默认开启会变成无法可靠关闭的风险。
        return False  # 新增代码+DangerousDebugDefault: 显式关闭时返回 False；如果没有这行代码，安全模式开关不会生效。
    if normalized_value in DANGEROUS_SKIP_PERMISSION_TRUE_VALUES:  # 新增代码+DangerousDebugDefault: 识别用户显式开启危险模式的常见写法；如果没有这行代码，已有 LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS=1 语义会变得不清楚。
        return True  # 新增代码+DangerousDebugDefault: 显式开启时返回 True；如果没有这行代码，启动脚本写入 1 后可能无法稳定生效。
    # 修改代码+DangerousDebugDefault: 函数段即将结束，做到“调试期默认开、显式关可关闭”；如果没有这段注释，用户不容易看懂默认和退出开关的边界。
    return True  # 新增代码+DangerousDebugDefault: 对空字符串或未知值采用开发期默认开启；如果没有这行代码，拼写小差异会让调试流程突然退回保守权限。

def dangerously_skip_permission_reason(target: str = "") -> str:  # 新增代码+危险调试权限: 生成危险自动授权的可审计原因；如果没有这行代码，日志只显示自动允许但不知道为什么允许。
    target_text = str(target or "").strip()  # 新增代码+危险调试权限: 清理工具名或操作名；如果没有这行代码，原因文本可能混入 None 或多余空白。
    if target_text:  # 新增代码+危险调试权限: 判断是否有具体授权对象；如果没有这行代码，带对象和不带对象的提示无法区分。
        return f"危险调试模式已开启：{DANGEROUS_SKIP_PERMISSIONS_ENV_VAR}=1，自动允许 {target_text}"  # 新增代码+危险调试权限: 返回带对象的审计原因；如果没有这行代码，真实验收无法确认哪项工具被危险模式放行。
    return f"危险调试模式已开启：{DANGEROUS_SKIP_PERMISSIONS_ENV_VAR}=1，自动允许本次权限请求"  # 新增代码+危险调试权限: 返回通用审计原因；如果没有这行代码，终端权限自动放行缺少人话说明。

def real_browser_customer_mode_active(real_chrome_requested: bool, real_browser_information_task_requested: bool) -> bool:  # 新增代码+BrowserSplit: 判断当前轮次是否可启用客户模式；如果没有这行代码，主 agent 需要重复拼条件。
    return bool(real_chrome_requested and real_browser_information_task_requested)  # 新增代码+BrowserSplit: 只有真实浏览器意图和公开查询意图同时成立才启用；如果没有这行代码，普通浏览器动作可能被误放行。

def customer_mode_can_auto_approve_terminal_permission(permission_payload: dict[str, Any]) -> bool:  # 新增代码+BrowserSplit: 判断终端客户模式是否能自动允许 MCP 启动；如果没有这行代码，启动 MCP 仍会由主文件手写判断。
    if dangerously_skip_permissions_enabled():  # 新增代码+危险调试权限: 危险模式下终端权限全部自动允许；如果没有这行代码，真实调试仍会被 y/N 打断。
        return True  # 新增代码+危险调试权限: 直接放行本次终端权限；如果没有这行代码，危险模式开关对终端权限不会产生效果。
    if permission_payload.get("permission_kind") != "mcp_server_start":  # 新增代码+BrowserSplit: 终端入口目前只自动允许项目 MCP server 启动；如果没有这行代码，普通工具权限可能被过度放行。
        return False  # 新增代码+BrowserSplit: 非 MCP 启动权限回退人工确认；如果没有这行代码，敏感操作会绕过用户。
    allowed_servers = {"browser_search", "workspace_tools", "browser_automation"}  # 新增代码+BrowserSplit: 限定项目内置 MCP server；如果没有这行代码，未知 server 可能混入自动启动。
    server_names = {str(name).strip() for name in permission_payload.get("server_names", []) if str(name).strip()}  # 新增代码+BrowserSplit: 清理本次请求启动的 server 名；如果没有这行代码，白名单比较会不稳定。
    return bool(server_names) and server_names.issubset(allowed_servers)  # 新增代码+BrowserSplit: 只有全部 server 都在白名单时自动允许；如果没有这行代码，部分未知 server 可能被放行。

def real_browser_customer_auto_approve_reason(tool_name: str, arguments: dict[str, Any], *, customer_mode_active: bool) -> str:  # 新增代码+BrowserSplit: 返回客户模式工具自动授权原因；如果没有这行代码，主 agent 仍要手写白名单分支。
    if dangerously_skip_permissions_enabled():  # 新增代码+危险调试权限: 危险模式下所有 MCP 工具权限都自动允许；如果没有这行代码，browser_connect_real_chrome 以外的调试工具仍可能弹窗。
        return dangerously_skip_permission_reason(tool_name)  # 新增代码+危险调试权限: 返回包含工具名的审计原因；如果没有这行代码，MCP progress 无法解释为什么工具被直接放行。
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

def visible_browser_customer_auto_approve_reason(tool_name: str, arguments: dict[str, Any], *, customer_mode_active: bool) -> str:  # 新增代码+自然可见浏览器路由: 返回普通可见浏览器查询的自动授权原因；如果没有这行代码，真实验收会被大量 y/N 焦点问题打断。
    if dangerously_skip_permissions_enabled():  # 新增代码+危险调试权限: 危险模式下普通可见浏览器工具也直接放行；如果没有这行代码，调试任务可能仍被自然查询白名单边界卡住。
        return dangerously_skip_permission_reason(tool_name)  # 新增代码+危险调试权限: 返回工具级危险授权原因；如果没有这行代码，日志无法说明可见浏览器工具为何无需确认。
    if not customer_mode_active:  # 新增代码+自然可见浏览器路由: 只有自然实时查询模式才允许自动授权；如果没有这行代码，普通浏览器工具会被过度放行。
        return ""  # 新增代码+自然可见浏览器路由: 非目标模式返回空原因；如果没有这行代码，调用方无法回退人工权限。
    always_allowed_tools = {  # 新增代码+自然可见浏览器路由: 定义独立 Chromium 下可自动放行的安全工具；如果没有这行代码，权限边界会散落难审计。
        "mcp__browser_automation__browser_wait",  # 新增代码+自然可见浏览器路由: 等待页面加载无高风险副作用；如果没有这项，页面加载会反复弹权限。
        "mcp__browser_automation__browser_snapshot",  # 新增代码+自然可见浏览器路由: 读取独立浏览器当前公开页文本；如果没有这项，网页证据读取会卡住。
        "mcp__browser_automation__browser_screenshot",  # 新增代码+自然可见浏览器路由: 保存当前公开页截图证据；如果没有这项，肉眼可见验收证据会卡住。
        "mcp__browser_automation__browser_visual_locate",  # 新增代码+自然可见浏览器路由: 定位公开页面文字或元素；如果没有这项，视觉定位流程会卡住。
        "mcp__browser_automation__browser_click",  # 新增代码+自然可见浏览器路由: 点击公开页面搜索框或同意按钮；如果没有这项，拟人浏览器流程会卡住。
        "mcp__browser_automation__browser_type",  # 新增代码+自然可见浏览器路由: 输入用户查询词；如果没有这项，真实输入流程会卡住。
        "mcp__browser_automation__browser_press_key",  # 新增代码+自然可见浏览器路由: 按 Enter 提交搜索；如果没有这项，真实搜索流程会卡住。
        "mcp__browser_automation__browser_flow_run",  # 新增代码+自然可见浏览器路由: 执行受限浏览器流程；如果没有这项，复杂流程验收会卡住。
        "mcp__browser_automation__browser_recover_page",  # 新增代码+自然可见浏览器路由: 恢复空白或失败页面；如果没有这项，异常恢复会卡住。
        "mcp__browser_automation__browser_replay",  # 新增代码+自然可见浏览器路由: dry-run 回放计划是安全审计动作；如果没有这项，回放证据会卡住。
        "mcp__browser_automation__browser_plugin_status",  # 新增代码+自然可见浏览器路由: 读取插件兼容状态；如果没有这项，能力状态确认会卡住。
    }  # 新增代码+自然可见浏览器路由: 结束安全工具集合；如果没有这行代码，Python 语法不完整。
    if tool_name == "mcp__browser_automation__browser_launch_visible":  # 新增代码+自然可见浏览器路由: 可见窗口启动需要单独校验确认参数；如果没有这行代码，启动可见浏览器仍会弹权限。
        if arguments.get("confirm_visible_browser") is True:  # 新增代码+自然可见浏览器路由: 只有模型显式确认可见窗口才放行；如果没有这行代码，漏参也可能打开窗口。
            return "可见浏览器公开查询客户模式已默认允许启动独立 Chromium"  # 新增代码+自然可见浏览器路由: 返回可审计授权原因；如果没有这行代码，日志无法解释为什么没有 y/N。
        return ""  # 新增代码+自然可见浏览器路由: 缺少确认参数时回退人工权限；如果没有这行代码，错误参数会被静默放行。
    if tool_name == "mcp__browser_automation__browser_open":  # 新增代码+自然可见浏览器路由: 打开网页需要 URL 安全校验；如果没有这行代码，公开查询无法顺畅打开资料页。
        url = str(arguments.get("url", "") or "").strip().lower()  # 新增代码+自然可见浏览器路由: 读取并小写化 URL；如果没有这行代码，前缀判断可能大小写不稳定。
        if url.startswith("https://") or url.startswith("http://"):  # 新增代码+自然可见浏览器路由: 只允许标准网页地址；如果没有这行代码，file/javascript 等危险 scheme 可能被放行。
            return "可见浏览器公开查询客户模式已默认允许打开公开网页"  # 新增代码+自然可见浏览器路由: 返回网页打开授权原因；如果没有这行代码，审计不知道为什么 browser_open 自动通过。
        return ""  # 新增代码+自然可见浏览器路由: 非 http(s) URL 回退人工权限；如果没有这行代码，本地文件或脚本 URL 可能被静默打开。
    if tool_name in always_allowed_tools:  # 新增代码+自然可见浏览器路由: 安全白名单工具自动放行；如果没有这行代码，snapshot/wait/click 等仍会打断真实验收。
        return "可见浏览器公开查询客户模式白名单"  # 新增代码+自然可见浏览器路由: 返回统一白名单原因；如果没有这行代码，权限审计缺少可读依据。
    return ""  # 新增代码+自然可见浏览器路由: 其它工具不自动授权；如果没有这行代码，browser_evaluate/downloads 等敏感工具可能被误放行。

def real_browser_customer_progress_message(tool_name: str, arguments: dict[str, Any]) -> str:  # 新增代码+BrowserSplit: 把工具动作转换成人类可见进度提示；如果没有这行代码，真实终端看不到 agent 下一步。
    if tool_name == "mcp__browser_automation__browser_profile_status":  # 新增代码+BrowserSplit: 识别状态检查动作；如果没有这行代码，第一步进度会很模糊。
        return "正在检查真实 Chrome 状态..."  # 新增代码+BrowserSplit: 输出安全前置检查提示；如果没有这行代码，用户只看到安静等待。
    if tool_name == "mcp__browser_automation__browser_connect_real_chrome":  # 新增代码+BrowserSplit: 识别真实 Chrome 连接动作；如果没有这行代码，用户不知道 agent 正在接入桌面 Chrome。
        return "正在连接真实 Chrome（仅使用公开查询白名单）..."  # 新增代码+BrowserSplit: 输出连接边界；如果没有这行代码，高风险动作缺少可见解释。
    if tool_name == "mcp__browser_automation__browser_open":  # 新增代码+BrowserSplit: 识别打开网页动作；如果没有这行代码，用户不知道即将打开哪个站点。
        return "正在打开 Google..."  # 新增代码+BrowserSplit: 输出目标站点；如果没有这行代码，终端进度不够贴近真实操作。
    if tool_name == "mcp__browser_automation__browser_launch_visible":  # 新增代码+自然可见浏览器路由: 识别启动可见独立浏览器动作；如果没有这行代码，普通可见浏览器自动授权时没有清楚进度。
        return "正在启动可见独立 Chromium..."  # 新增代码+自然可见浏览器路由: 输出可见窗口启动提示；如果没有这行代码，用户不知道桌面窗口为什么弹出。
    if tool_name == "mcp__browser_automation__browser_visual_locate":  # 新增代码+自然可见浏览器路由: 识别视觉定位动作；如果没有这行代码，定位阶段没有可见说明。
        return "正在定位页面可见文字或元素..."  # 新增代码+自然可见浏览器路由: 输出视觉定位进度；如果没有这行代码，用户不知道 agent 在看页面哪里。
    if tool_name == "mcp__browser_automation__browser_flow_run":  # 新增代码+自然可见浏览器路由: 识别复杂流程执行动作；如果没有这行代码，流程执行没有终端说明。
        return "正在执行可见浏览器流程..."  # 新增代码+自然可见浏览器路由: 输出流程进度；如果没有这行代码，用户会误以为卡住。
    if tool_name == "mcp__browser_automation__browser_recover_page":  # 新增代码+自然可见浏览器路由: 识别页面恢复动作；如果没有这行代码，异常恢复阶段不透明。
        return "正在恢复或刷新页面..."  # 新增代码+自然可见浏览器路由: 输出页面恢复进度；如果没有这行代码，用户不知道为何页面刷新。
    if tool_name == "mcp__browser_automation__browser_replay":  # 新增代码+自然可见浏览器路由: 识别回放计划动作；如果没有这行代码，任务回放审计没有说明。
        return "正在生成浏览器动作回放计划..."  # 新增代码+自然可见浏览器路由: 输出回放进度；如果没有这行代码，用户不知道 agent 在做审计。
    if tool_name == "mcp__browser_automation__browser_plugin_status":  # 新增代码+自然可见浏览器路由: 识别插件兼容状态动作；如果没有这行代码，能力检查没有说明。
        return "正在检查浏览器能力和插件兼容状态..."  # 新增代码+自然可见浏览器路由: 输出插件状态进度；如果没有这行代码，用户不知道该工具只读。
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
