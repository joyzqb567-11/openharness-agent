"""真实浏览器自然任务 harness 文本。"""  # 新增代码+BrowserSplit: 把短 prompt 的真实浏览器操作约束移出主文件；如果没有这行代码，harness 文本仍难以复用和测试。
try:  # 新增代码+BrowserSplit: 优先按包路径导入意图识别和工作流常量；如果没有这行代码，包模式运行无法复用 browser 层。
    from learning_agent.browser.intent import detect_real_browser_information_task  # 新增代码+BrowserSplit: 导入真实浏览器公开查询判断；如果没有这行代码，harness 无法按需注入。
    from learning_agent.browser.search_workflow import REAL_BROWSER_FINAL_ACTION_NAMES  # 新增代码+BrowserSplit: 导入最终回答需要列出的动作名；如果没有这行代码，harness 里会重复硬编码动作清单。
except ModuleNotFoundError as error:  # 新增代码+BrowserSplit: 兼容直接脚本模式下包名不可用；如果没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.intent", "learning_agent.browser.search_workflow"}:  # 新增代码+BrowserSplit: 只允许路径问题 fallback；如果没有这行代码，真实内部错误会被误吞。
        raise  # 新增代码+BrowserSplit: 重新抛出真实导入错误；如果没有这行代码，排查 harness 会缺少根因。
    from browser.intent import detect_real_browser_information_task  # 新增代码+BrowserSplit: 脚本模式下导入意图判断；如果没有这行代码，直接运行时 harness 不可用。
    from browser.search_workflow import REAL_BROWSER_FINAL_ACTION_NAMES  # 新增代码+BrowserSplit: 脚本模式下导入动作名常量；如果没有这行代码，直接运行时动作清单不可用。

def build_real_browser_task_harness_message(user_input: str) -> str:  # 新增代码+BrowserSplit: 为自然短 prompt 构造真实浏览器任务约束；如果没有这行代码，主 agent 无法委托 harness 生成。
    if not detect_real_browser_information_task(user_input):  # 新增代码+BrowserSplit: 只在真实浏览器公开查询任务里注入；如果没有这行代码，所有任务都会被浏览器规则污染。
        return ""  # 新增代码+BrowserSplit: 非目标任务返回空字符串；如果没有这行代码，调用方不能简单拼接。
    action_text = "、".join(REAL_BROWSER_FINAL_ACTION_NAMES)  # 新增代码+BrowserSplit: 把动作名清单格式化为中文顿号分隔；如果没有这行代码，最终回答要求会散落在长字符串里。
    return (  # 新增代码+BrowserSplit: 返回紧凑系统约束文本；如果没有这行代码，短 prompt 下模型缺少可执行路线。
        "Real Browser Task Harness / 真实浏览器查询任务约束：\n"  # 新增代码+BrowserSplit: 提供稳定标题供测试和调试定位；如果没有这行代码，无法确认 harness 是否注入。
        "- 用户本轮显式要求真实浏览器；不能用 web_search、fetch_url、普通回答、直接 API URL 或独立 Chromium 替代真实桌面 Chrome。\n"  # 新增代码+BrowserSplit: 明确替代路径不可用；如果没有这行代码，模型可能绕开真实 Chrome。
        "- 先 read `learning_agent/skills/tool_list.md`，再 read `learning_agent/skills/real_chrome/SKILL.md`；需要搜索细节时 read `learning_agent/skills/real_chrome/rules/search_task_workflow.md`。\n"  # 新增代码+BrowserSplit: 强制进入分层 skill 入口；如果没有这行代码，模型可能不知道如何解锁真实 Chrome 工具。
        "- 工具顺序：先 `browser_profile_status`，再 `browser_connect_real_chrome` 且 `confirm_real_profile=true`，连接成功后只在同一个真实 Chrome 会话里继续操作。\n"  # 新增代码+BrowserSplit: 固定真实 profile 安全前置顺序；如果没有这行代码，模型可能跳过状态检查。
        "- 对会议、酒店、航班、资料、天气、旅游攻略等公开信息查询，默认打开 `https://www.google.com/`，用页面快照找到搜索框。\n"  # 新增代码+BrowserSplit: 说明能力是通用查询；如果没有这行代码，流程会被误解为重庆天气专用。
        "- 必须用 `browser_click` 点击搜索框，用 `browser_type` 输入从用户请求提炼出的搜索词，用 `browser_press_key` 按 Enter，再用 `browser_wait` 等待结果加载。\n"  # 新增代码+BrowserSplit: 要求真实可见拟人搜索；如果没有这行代码，模型可能直接打开搜索结果 URL。
        "- 用 `browser_screenshot` 保存视觉证据，再用 `browser_snapshot` 读取标题、摘要或页面可见信息；遇到同意弹窗可点击同意，遇到 CAPTCHA 不绕过，只截图并说明。\n"  # 新增代码+BrowserSplit: 要求证据和异常边界；如果没有这行代码，结果难以复核。
        "- 不要读取 cookies、localStorage、sessionStorage、token、Authorization header、密码、已有标签页内容、插件内容、network、console，也不要调用 `browser_evaluate`。\n"  # 新增代码+BrowserSplit: 保留真实 profile 隐私边界；如果没有这行代码，登录态场景可能越界。
        f"- 最终回答必须包含 `real_chrome_connected=true`，并列出 {action_text} 这些实际动作名；同时说明搜索词、截图文件名或路径、来源摘要、结果结论和隐私边界。\n"  # 新增代码+BrowserSplit: 保留机器可读验收标记和动作名；如果没有这行代码，真实终端成功也可能被验收误判。
    )  # 新增代码+BrowserSplit: 结束 harness 文本表达式；如果没有这行代码，Python 语法不完整。
