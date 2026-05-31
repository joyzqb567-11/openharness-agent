"""真实浏览器公开搜索工作流常量。"""  # 新增代码+BrowserSplit: 集中保存 Google 入口、验收动作名和客户模式工具白名单；如果没有这行代码，真实浏览器流程常量会继续散在主文件里。
GOOGLE_URL_PREFIXES = ("https://www.google.com", "https://google.com")  # 新增代码+BrowserSplit: 只允许客户模式默认打开 Google 公共入口；如果没有这行代码，URL 白名单会在多个分支重复。
REAL_BROWSER_FINAL_ACTION_NAMES = (  # 新增代码+BrowserSplit: 定义最终回答里要求列出的真实浏览器动作名；如果没有这行代码，harness 和验收要求可能逐渐不一致。
    "browser_profile_status",  # 新增代码+BrowserSplit: 记录真实 Chrome 状态检查动作；如果没有这行代码，最终回答可能无法证明做过安全前置检查。
    "browser_connect_real_chrome",  # 新增代码+BrowserSplit: 记录真实 Chrome 连接动作；如果没有这行代码，最终回答无法区分真实 Chrome 和独立 Chromium。
    "browser_open",  # 新增代码+BrowserSplit: 记录打开 Google 页面动作；如果没有这行代码，最终回答可能缺少实际访问入口。
    "browser_click",  # 新增代码+BrowserSplit: 记录点击搜索框动作；如果没有这行代码，拟人操作验收缺少关键证据。
    "browser_type",  # 新增代码+BrowserSplit: 记录输入搜索词动作；如果没有这行代码，用户无法确认 agent 没有直接拼 URL 绕过输入。
    "browser_press_key",  # 新增代码+BrowserSplit: 记录 Enter 提交动作；如果没有这行代码，搜索提交流程不完整。
    "browser_wait",  # 新增代码+BrowserSplit: 记录等待结果加载动作；如果没有这行代码，页面读取可能发生在加载前。
    "browser_screenshot",  # 新增代码+BrowserSplit: 记录截图取证动作；如果没有这行代码，真实浏览器结果缺少视觉证据。
    "browser_snapshot",  # 新增代码+BrowserSplit: 记录读取可见页面内容动作；如果没有这行代码，最终摘要缺少页面来源依据。
)  # 新增代码+BrowserSplit: 结束验收动作名元组；如果没有这行代码，Python 语法不完整。
REAL_BROWSER_ALWAYS_ALLOWED_TOOL_NAMES = {  # 新增代码+BrowserSplit: 定义客户模式下固定允许的浏览器工具；如果没有这行代码，点击、输入、等待仍会每步打断用户。
    "mcp__browser_automation__browser_profile_status",  # 新增代码+BrowserSplit: 允许只读状态检查；如果没有这行代码，真实浏览器任务第一步仍会弹 y/N。
    "mcp__browser_automation__browser_snapshot",  # 新增代码+BrowserSplit: 允许读取公开搜索页可见快照；如果没有这行代码，结果摘要读取会被打断。
    "mcp__browser_automation__browser_click",  # 新增代码+BrowserSplit: 允许点击搜索框或同意按钮；如果没有这行代码，拟人点击无法顺畅完成。
    "mcp__browser_automation__browser_type",  # 新增代码+BrowserSplit: 允许输入搜索词；如果没有这行代码，搜索输入仍会要求用户逐次确认。
    "mcp__browser_automation__browser_press_key",  # 新增代码+BrowserSplit: 允许按 Enter；如果没有这行代码，搜索提交仍会弹权限。
    "mcp__browser_automation__browser_wait",  # 新增代码+BrowserSplit: 允许等待页面加载；如果没有这行代码，等待动作也会打断用户。
    "mcp__browser_automation__browser_screenshot",  # 新增代码+BrowserSplit: 允许保存可见截图证据；如果没有这行代码，取证动作会继续弹权限。
    "mcp__browser_automation__browser_disconnect_real_chrome",  # 新增代码+BrowserSplit: 允许结束时断开自动化连接；如果没有这行代码，清理动作也可能打断用户。
}  # 新增代码+BrowserSplit: 结束固定白名单集合；如果没有这行代码，Python 集合语法不完整。

def google_url_allowed(url: str) -> bool:  # 新增代码+BrowserSplit: 判断 URL 是否属于客户模式默认允许的 Google 公共入口；如果没有这行代码，权限模块需要重复写前缀判断。
    normalized_url = str(url or "").strip().lower()  # 新增代码+BrowserSplit: 统一清理 URL 并转小写；如果没有这行代码，大小写或空白会让白名单判断不稳定。
    return any(normalized_url.startswith(prefix) for prefix in GOOGLE_URL_PREFIXES)  # 新增代码+BrowserSplit: 只要命中 Google 前缀就允许；如果没有这行代码，调用方拿不到判断结果。
