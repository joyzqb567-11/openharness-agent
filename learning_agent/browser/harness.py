"""真实浏览器自然任务 harness 文本。"""  # 新增代码+BrowserSplit: 把短 prompt 的真实浏览器操作约束移出主文件；如果没有这行代码，harness 文本仍难以复用和测试。
try:  # 新增代码+BrowserSplit: 优先按包路径导入意图识别和工作流常量；如果没有这行代码，包模式运行无法复用 browser 层。
    from learning_agent.browser.intent import detect_real_browser_information_task  # 新增代码+BrowserSplit: 导入真实浏览器公开查询判断；如果没有这行代码，harness 无法按需注入。
    from learning_agent.browser.intent import detect_visible_browser_information_task  # 新增代码+自然可见浏览器路由: 导入普通自然实时查询判断；如果没有这行代码，harness 无法为武汉天气 prompt 注入可见浏览器路线。
    from learning_agent.browser.search_workflow import REAL_BROWSER_FINAL_ACTION_NAMES  # 新增代码+BrowserSplit: 导入最终回答需要列出的动作名；如果没有这行代码，harness 里会重复硬编码动作清单。
except ModuleNotFoundError as error:  # 新增代码+BrowserSplit: 兼容直接脚本模式下包名不可用；如果没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.intent", "learning_agent.browser.search_workflow"}:  # 新增代码+BrowserSplit: 只允许路径问题 fallback；如果没有这行代码，真实内部错误会被误吞。
        raise  # 新增代码+BrowserSplit: 重新抛出真实导入错误；如果没有这行代码，排查 harness 会缺少根因。
    from browser.intent import detect_real_browser_information_task  # 新增代码+BrowserSplit: 脚本模式下导入意图判断；如果没有这行代码，直接运行时 harness 不可用。
    from browser.intent import detect_visible_browser_information_task  # 新增代码+自然可见浏览器路由: 脚本模式下导入自然实时查询判断；如果没有这行代码，bat 入口无法注入可见浏览器路线。
    from browser.search_workflow import REAL_BROWSER_FINAL_ACTION_NAMES  # 新增代码+BrowserSplit: 脚本模式下导入动作名常量；如果没有这行代码，直接运行时动作清单不可用。

def build_real_browser_task_harness_message(user_input: str) -> str:  # 新增代码+BrowserSplit: 为自然短 prompt 构造真实浏览器任务约束；如果没有这行代码，主 agent 无法委托 harness 生成。
    if not detect_real_browser_information_task(user_input):  # 新增代码+BrowserSplit: 只在真实浏览器公开查询任务里注入；如果没有这行代码，所有任务都会被浏览器规则污染。
        return ""  # 新增代码+BrowserSplit: 非目标任务返回空字符串；如果没有这行代码，调用方不能简单拼接。
    action_text = "、".join(REAL_BROWSER_FINAL_ACTION_NAMES)  # 新增代码+BrowserSplit: 把动作名清单格式化为中文顿号分隔；如果没有这行代码，最终回答要求会散落在长字符串里。
    return (  # 新增代码+BrowserSplit: 返回紧凑系统约束文本；如果没有这行代码，短 prompt 下模型缺少可执行路线。
        "Real Browser Task Harness / 真实浏览器查询任务约束：\n"  # 新增代码+BrowserSplit: 提供稳定标题供测试和调试定位；如果没有这行代码，无法确认 harness 是否注入。
        "- 用户本轮显式要求真实浏览器；不能用 web_search、fetch_url、普通回答、直接 API URL 或独立 Chromium 替代真实桌面 Chrome。\n"  # 新增代码+BrowserSplit: 明确替代路径不可用；如果没有这行代码，模型可能绕开真实 Chrome。
        "- 不要直接选择 provider，也不要发明 chrome_extension_open、real_chrome_cdp_click 等 provider 专属工具；只调用统一 browser_* 工具，底层由 BrowserProviderRouter 选择并写入 event log。\n"  # 新增代码+BrowserToolSurfaceStage3: 把单轨工具表面写进真实浏览器 harness；如果没有这行代码，模型可能仍把 provider 当成自己要选择的工具。
        "- 先 read `learning_agent/skills/tool_list.md`，再 read `learning_agent/skills/real_chrome/SKILL.md`；需要搜索细节时 read `learning_agent/skills/real_chrome/rules/search_task_workflow.md`。\n"  # 新增代码+BrowserSplit: 强制进入分层 skill 入口；如果没有这行代码，模型可能不知道如何解锁真实 Chrome 工具。
        "- 工具顺序：先 `browser_profile_status`，再 `browser_connect_real_chrome` 且 `confirm_real_profile=true`，连接成功后只在同一个真实 Chrome 会话里继续操作。\n"  # 新增代码+BrowserSplit: 固定真实 profile 安全前置顺序；如果没有这行代码，模型可能跳过状态检查。
        "- 连接真实 Chrome 后、任何 `browser_click`/`browser_type`/`browser_type_secret`/`browser_press_key`/`browser_upload_file` 前，必须先调用 `browser_tabs_context`；切换、新建、关闭或导航标签页后也要重新调用。\n"  # 新增代码+BrowserTabsContextStage4: 把 tabs context 门禁写入真实 Chrome harness；如果没有这行代码，模型可能不知道写动作为什么被工具层拦截。
        "- 对会议、酒店、航班、资料、天气、旅游攻略等公开信息查询，默认打开 `https://www.google.com/`，用页面快照找到搜索框。\n"  # 新增代码+BrowserSplit: 说明能力是通用查询；如果没有这行代码，流程会被误解为重庆天气专用。
        "- 必须用 `browser_click` 点击搜索框，用 `browser_type` 输入从用户请求提炼出的搜索词，用 `browser_press_key` 按 Enter，再用 `browser_wait` 等待结果加载。\n"  # 新增代码+BrowserSplit: 要求真实可见拟人搜索；如果没有这行代码，模型可能直接打开搜索结果 URL。
        "- 用 `browser_screenshot` 保存视觉证据，再用 `browser_snapshot` 读取标题、摘要或页面可见信息；遇到同意弹窗可点击同意，遇到 CAPTCHA 不绕过，只截图并说明。\n"  # 新增代码+BrowserSplit: 要求证据和异常边界；如果没有这行代码，结果难以复核。
        "- 如果 `browser_snapshot` 已经同时包含天气结论和 3天/Day 1/Day 2/Day 3/路线/攻略信息，立即停止继续浏览并整理最终回答，不要因为尾部上下文变短而改写用户目标。\n"  # 新增代码+真实浏览器结果收束: 告诉模型证据足够时要收束；如果没有这行代码，agent 可能继续过度搜索并偏到错误日期。
        "- 不要读取 cookies、localStorage、sessionStorage、token、Authorization header、密码、已有标签页内容、插件内容、network、console，也不要调用 `browser_evaluate`。\n"  # 新增代码+BrowserSplit: 保留真实 profile 隐私边界；如果没有这行代码，登录态场景可能越界。
        f"- 内部验收只看 event log 里的 `real_chrome_connected=true` 和 {action_text} 动作记录；最终回答面向普通用户，不要输出这些内部标记或工具名，只需要给出搜索词、来源摘要、天气结论、3天路线和必要提醒。\n"  # 修改代码+真实浏览器用户结果: 把机器验收从用户答案挪回日志；如果没有这行代码，用户会看到一堆调试标记而不是想要的最终结果。
    )  # 新增代码+BrowserSplit: 结束 harness 文本表达式；如果没有这行代码，Python 语法不完整。

def build_visible_browser_task_harness_message(user_input: str) -> str:  # 新增代码+自然可见浏览器路由: 为普通实时查询构造可见独立浏览器任务约束；如果没有这行代码，精准 prompt 仍会走后台搜索。
    if not detect_visible_browser_information_task(user_input):  # 新增代码+自然可见浏览器路由: 只在普通实时公开查询中注入；如果没有这行代码，所有任务都会被浏览器规则污染。
        return ""  # 新增代码+自然可见浏览器路由: 非目标任务返回空文本；如果没有这行代码，调用方不能安全拼接。
    visible_action_text = "browser_launch_visible、browser_open、browser_snapshot"  # 新增代码+自然可见浏览器路由: 定义最小验收动作名清单；如果没有这行代码，最终回答缺少机器可核验证据。
    return (  # 新增代码+自然可见浏览器路由: 返回紧凑系统约束文本；如果没有这行代码，模型缺少可执行浏览器路线。
        "Visible Browser Task Harness / 可见浏览器查询任务约束：\n"  # 新增代码+自然可见浏览器路由: 提供稳定标题供测试和调试定位；如果没有这行代码，无法确认 harness 是否注入。
        "- 用户本轮是在查询天气、旅游攻略、新闻、价格、官网、会议、酒店或航班等公开实时信息；必须用用户肉眼可见的独立 Chromium 查询和核验。\n"  # 新增代码+自然可见浏览器路由: 说明普通实时查询也要可见；如果没有这行代码，模型可能误以为后台搜索就够。
        "- 不要直接选择 provider，也不要发明 chrome_extension_open、real_chrome_cdp_click 等 provider 专属工具；只调用统一 browser_* 工具，底层由 BrowserProviderRouter 选择并写入 event log。\n"  # 新增代码+BrowserToolSurfaceStage3: 把单轨工具表面写进可见浏览器 harness；如果没有这行代码，模型可能把普通查询误导到 provider 专属工具。
        "- 不要用 web_search、fetch_url、普通回答、直接 API URL 或纯记忆替代可见浏览器；这些后台路径不能证明用户桌面看到了真实浏览器。\n"  # 新增代码+自然可见浏览器路由: 明确禁止本次失败路径；如果没有这行代码，精准 prompt 会继续只调用 browser_search。
        "- 先 read `learning_agent/skills/tool_list.md`，再 read `learning_agent/skills/browser_automation/SKILL.md`；需要复杂流程时再读浏览器子规则。\n"  # 新增代码+自然可见浏览器路由: 引导模型加载普通浏览器 skill；如果没有这行代码，模型可能不知道如何使用可见浏览器工具。
        "- 第一项浏览器工具必须调用 `browser_launch_visible`，并传入 `confirm_visible_browser=true`，确认结果里有 `visible_browser=true` 和 `headless=false`。\n"  # 新增代码+自然可见浏览器路由: 固定可见窗口启动门槛；如果没有这行代码，模型可能继续启动 headless 浏览器。
        "- 然后用 `browser_open` 打开公开搜索页、天气页或旅游资料页，再用 `browser_snapshot` 读取页面可见信息；需要视觉定位时用 `browser_visual_locate`。\n"  # 新增代码+自然可见浏览器路由: 给出最小查询链路；如果没有这行代码，启动窗口后模型可能不知道下一步。
        "- 需要查看标签页状态时调用 `browser_tabs_context`，它会显示 session、active tab、URL、标题和 page_id；普通独立 Chromium 不强制写动作前调用。\n"  # 新增代码+BrowserTabsContextStage4: 让普通浏览器也知道 context 工具用途；如果没有这行代码，模型可能继续只用旧 browser_tabs list。
        "- 页面失败、超时或空白时，优先用 `browser_recover_page` 或重新 `browser_open`，不要直接放弃到后台搜索。\n"  # 新增代码+自然可见浏览器路由: 要求失败恢复留在可见浏览器路线；如果没有这行代码，异常时仍可能退回隐藏工具。
        "- 不要读取 cookies、localStorage、sessionStorage、token、Authorization header、密码、已有标签页内容、插件内容，也不要调用 `browser_evaluate`。\n"  # 新增代码+自然可见浏览器路由: 保留独立浏览器和隐私边界；如果没有这行代码，浏览器任务可能越权读取敏感信息。
        f"- 最终回答必须包含 `visible_browser=true`、`headless=false`，并列出 {visible_action_text} 这些实际动作名；同时说明查询词、来源摘要和结论。\n"  # 新增代码+自然可见浏览器路由: 给 controller 和用户可核验标记；如果没有这行代码，真实可见验收难以判断是否成功。
    )  # 新增代码+自然可见浏览器路由: 结束 harness 文本表达式；如果没有这行代码，Python 语法不完整。
