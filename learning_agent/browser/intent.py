"""真实浏览器任务意图识别。"""  # 新增代码+BrowserSplit: 把真实 Chrome 和公开信息查询识别集中到浏览器层；如果没有这行代码，意图判断会继续堆在 learning_agent.py。
REAL_CHROME_INTENT_KEYWORDS = (  # 新增代码+BrowserSplit: 定义真实桌面浏览器意图关键词；如果没有这行代码，真实 Chrome 判断会散落且难以复用。
    "真实的 chrome",  # 新增代码+BrowserSplit: 覆盖“真实的 Chrome”表达；如果没有这行代码，中英混合请求可能漏判。
    "真实 chrome",  # 新增代码+BrowserSplit: 覆盖省略“的”的写法；如果没有这行代码，常见短语会漏判。
    "真实浏览器",  # 新增代码+BrowserSplit: 覆盖用户自然说“真实浏览器”；如果没有这行代码，短 prompt 验收会失败。
    "真实的浏览器",  # 新增代码+BrowserSplit: 覆盖带“的”的自然表达；如果没有这行代码，同义请求会漏判。
    "真实可见浏览器",  # 新增代码+BrowserSplit: 覆盖真实且可见的桌面窗口需求；如果没有这行代码，可见窗口要求可能不触发。
    "桌面 chrome",  # 新增代码+BrowserSplit: 覆盖桌面 Chrome 说法；如果没有这行代码，agent 可能误走独立 Chromium。
    "桌面浏览器",  # 新增代码+BrowserSplit: 覆盖桌面浏览器中文表达；如果没有这行代码，真实桌面窗口需求会漏判。
    "可见浏览器",  # 新增代码+BrowserSplit: 覆盖可见浏览器窗口；如果没有这行代码，用户看得到的要求可能不生效。
    "当前浏览器",  # 新增代码+BrowserSplit: 覆盖当前浏览器指代；如果没有这行代码，登录态或已有窗口需求会漏判。
    "日常 chrome",  # 新增代码+BrowserSplit: 覆盖日常 profile 表达；如果没有这行代码，真实 profile 风险边界无法触发。
    "登录态",  # 新增代码+BrowserSplit: 覆盖已有登录状态需求；如果没有这行代码，agent 可能打开无登录独立浏览器。
    "real chrome",  # 新增代码+BrowserSplit: 覆盖英文真实 Chrome；如果没有这行代码，英文请求会漏判。
    "desktop chrome",  # 新增代码+BrowserSplit: 覆盖英文桌面 Chrome；如果没有这行代码，桌面浏览器英文表达会漏判。
    "visible browser",  # 新增代码+BrowserSplit: 覆盖英文可见浏览器；如果没有这行代码，英文可见窗口要求会漏判。
    "current browser",  # 新增代码+BrowserSplit: 覆盖英文当前浏览器；如果没有这行代码，当前窗口需求可能误走新实例。
    "login state",  # 新增代码+BrowserSplit: 覆盖英文登录态；如果没有这行代码，英文登录态需求会漏判。
)  # 新增代码+BrowserSplit: 结束真实 Chrome 关键词元组；如果没有这行代码，Python 语法不完整。
PUBLIC_INFORMATION_QUERY_KEYWORDS = (  # 新增代码+BrowserSplit: 定义公开信息查询关键词；如果没有这行代码，客户模式无法判断哪些任务可自动授权。
    "查询",  # 新增代码+BrowserSplit: 覆盖常见中文查询；如果没有这行代码，“帮我查询”会漏判。
    "查一下",  # 新增代码+BrowserSplit: 覆盖口语查询；如果没有这行代码，真实客户短句会漏判。
    "帮我查",  # 新增代码+BrowserSplit: 覆盖委托式查询；如果没有这行代码，用户自然表达会漏判。
    "搜索",  # 新增代码+BrowserSplit: 覆盖明确搜索；如果没有这行代码，Google 搜索请求不进入 harness。
    "查找",  # 新增代码+BrowserSplit: 覆盖资料查找；如果没有这行代码，文档资料任务可能漏判。
    "了解",  # 新增代码+BrowserSplit: 覆盖了解某资料；如果没有这行代码，研究型请求可能漏判。
    "资料",  # 新增代码+BrowserSplit: 覆盖资料检索；如果没有这行代码，资料类任务无法复用真实浏览器流程。
    "信息",  # 新增代码+BrowserSplit: 覆盖泛化信息获取；如果没有这行代码，宽泛查询容易漏掉。
    "网站",  # 新增代码+BrowserSplit: 覆盖网站公开内容查询；如果没有这行代码，YouTube 等站点查询会继续弹 y/N。
    "视频",  # 新增代码+BrowserSplit: 覆盖公开视频检索；如果没有这行代码，视频资料任务会漏判。
    "评论",  # 新增代码+BrowserSplit: 覆盖评论排行问题；如果没有这行代码，用户问评论最多仍会被打断。
    "最多",  # 新增代码+BrowserSplit: 覆盖最多/最热视频排行；如果没有这行代码，排序型公开查询会漏判。
    "有哪些",  # 新增代码+BrowserSplit: 覆盖有哪些问法；如果没有这行代码，不含“查”的问题会漏判。
    "哪些",  # 新增代码+BrowserSplit: 覆盖哪些视频/资料；如果没有这行代码，短问法可能漏判。
    "哪个",  # 新增代码+BrowserSplit: 覆盖单项比较查询；如果没有这行代码，比较型查询可能漏判。
    "排行",  # 新增代码+BrowserSplit: 覆盖排行榜查询；如果没有这行代码，榜单类任务无法复用客户模式。
    "排名",  # 新增代码+BrowserSplit: 覆盖排名表达；如果没有这行代码，公开排序任务会继续打断用户。
    "榜单",  # 新增代码+BrowserSplit: 覆盖榜单式资料检索；如果没有这行代码，榜单任务可能漏判。
    "介绍",  # 新增代码+BrowserSplit: 覆盖主题介绍查询；如果没有这行代码，介绍类内容检索会漏判。
    "youtube",  # 新增代码+BrowserSplit: 覆盖 YouTube 公开查询；如果没有这行代码，截图里的 YouTube 场景会回归多次授权。
    "天气",  # 新增代码+BrowserSplit: 覆盖天气查询；如果没有这行代码，重庆天气验收会漏判。
    "攻略",  # 新增代码+BrowserSplit: 覆盖旅游攻略；如果没有这行代码，天气加攻略任务可能只被部分识别。
    "会议",  # 新增代码+BrowserSplit: 覆盖会议查询；如果没有这行代码，未来会议任务无法复用。
    "酒店",  # 新增代码+BrowserSplit: 覆盖酒店查询；如果没有这行代码，未来酒店任务无法复用。
    "航班",  # 新增代码+BrowserSplit: 覆盖航班查询；如果没有这行代码，未来航班任务无法复用。
    "官网",  # 新增代码+BrowserSplit: 覆盖找官网任务；如果没有这行代码，网站资料任务可能漏判。
    "文档",  # 新增代码+BrowserSplit: 覆盖文档查询；如果没有这行代码，资料类任务覆盖不完整。
    "新闻",  # 新增代码+BrowserSplit: 覆盖新闻查询；如果没有这行代码，实时资讯任务可能漏判。
    "search",  # 新增代码+BrowserSplit: 覆盖英文搜索；如果没有这行代码，英文用户无法触发流程。
    "look up",  # 新增代码+BrowserSplit: 覆盖英文查询短语；如果没有这行代码，英文自然表达会漏判。
    "research",  # 新增代码+BrowserSplit: 覆盖英文研究任务；如果没有这行代码，英文资料任务无法复用。
    "weather",  # 新增代码+BrowserSplit: 覆盖英文天气；如果没有这行代码，英文天气任务会漏判。
    "hotel",  # 新增代码+BrowserSplit: 覆盖英文酒店；如果没有这行代码，英文酒店任务无法复用。
    "flight",  # 新增代码+BrowserSplit: 覆盖英文航班；如果没有这行代码，英文航班任务无法复用。
    "conference",  # 新增代码+BrowserSplit: 覆盖英文会议；如果没有这行代码，英文会议任务无法复用。
    "document",  # 新增代码+BrowserSplit: 覆盖英文文档；如果没有这行代码，英文资料任务无法复用。
)  # 新增代码+BrowserSplit: 结束公开信息关键词元组；如果没有这行代码，Python 语法不完整。
INDEPENDENT_BROWSER_TOOL_NAMES = {  # 新增代码+BrowserSplit: 定义真实 Chrome 连接前要拦截的独立浏览器工具；如果没有这行代码，真实浏览器请求可能误走独立实例。
    "browser_open",  # 新增代码+BrowserSplit: 打开网页默认可能启动独立 Chromium；如果没有这项，真实浏览器请求会被绕过。
    "browser_click",  # 新增代码+BrowserSplit: 点击页面必须落在正确会话；如果没有这项，未连接时可能点错浏览器。
    "browser_type",  # 新增代码+BrowserSplit: 输入文本必须落在正确会话；如果没有这项，可能输入到独立实例。
    "browser_press_key",  # 新增代码+BrowserSplit: 按键会改变页面状态；如果没有这项，真实浏览器需求下可能误操作。
    "browser_wait",  # 新增代码+BrowserSplit: 等待依赖正确页面；如果没有这项，可能等待错误会话。
    "browser_screenshot",  # 新增代码+BrowserSplit: 截图必须来自真实会话；如果没有这项，证据可能不是用户桌面 Chrome。
    "browser_tabs",  # 新增代码+BrowserSplit: 标签页读取必须来自真实会话；如果没有这项，状态会误导模型。
    "browser_console",  # 新增代码+BrowserSplit: console 摘要必须对应真实会话；如果没有这项，排查会看错浏览器。
    "browser_network",  # 新增代码+BrowserSplit: network 摘要必须对应真实会话；如果没有这项，网络观察会看错上下文。
    "browser_upload_file",  # 新增代码+BrowserSplit: 上传文件有副作用；如果没有这项，可能在错误浏览器上传。
    "browser_downloads",  # 新增代码+BrowserSplit: 下载记录语义和会话相关；如果没有这项，用户可能看到错误记录。
    "browser_evaluate",  # 新增代码+BrowserSplit: 页面脚本风险高；如果没有这项，可能绕开真实 profile 安全边界。
    "browser_close",  # 新增代码+BrowserSplit: 关闭会改变会话；如果没有这项，可能关闭错误上下文。
}  # 新增代码+BrowserSplit: 结束独立浏览器工具集合；如果没有这行代码，Python 语法不完整。

def detect_real_chrome_intent(user_input: str) -> bool:  # 新增代码+BrowserSplit: 判断用户是否要求真实桌面 Chrome/浏览器；如果没有这行代码，主 agent 无法委托意图识别。
    lowered_input = str(user_input or "").lower()  # 新增代码+BrowserSplit: 统一输入为空和英文大小写；如果没有这行代码，None 或大写英文会导致误判。
    return any(keyword in lowered_input for keyword in REAL_CHROME_INTENT_KEYWORDS)  # 新增代码+BrowserSplit: 任一真实浏览器关键词命中即返回 True；如果没有这行代码，调用方拿不到判断结果。

def detect_real_browser_information_task(user_input: str) -> bool:  # 新增代码+BrowserSplit: 判断真实浏览器请求是否属于公开信息查询任务；如果没有这行代码，客户模式自动授权没有独立入口。
    if not detect_real_chrome_intent(user_input):  # 新增代码+BrowserSplit: 先确认是真实浏览器需求；如果没有这行代码，普通搜索任务也会被强行导向真实 profile。
        return False  # 新增代码+BrowserSplit: 非真实浏览器任务不启用公开查询 harness；如果没有这行代码，普通任务会受到浏览器规则污染。
    lowered_input = str(user_input or "").lower()  # 新增代码+BrowserSplit: 统一输入为空和英文大小写；如果没有这行代码，英文查询短语可能漏判。
    return any(keyword in lowered_input for keyword in PUBLIC_INFORMATION_QUERY_KEYWORDS)  # 新增代码+BrowserSplit: 任一公开查询关键词命中即返回 True；如果没有这行代码，客户模式无法触发。

def independent_browser_tool_names() -> set[str]:  # 新增代码+BrowserSplit: 返回真实 Chrome 连接前需要拦截的工具集合副本；如果没有这行代码，外部可能直接修改模块常量。
    return set(INDEPENDENT_BROWSER_TOOL_NAMES)  # 新增代码+BrowserSplit: 返回副本保护全局集合；如果没有这行代码，调用方修改结果会污染后续判断。

def real_chrome_request_blocks_independent_browser(*, real_chrome_requested: bool, real_chrome_connected: bool, server_name: str, original_name: str) -> bool:  # 新增代码+BrowserSplit: 判断真实浏览器请求是否应拦截独立浏览器工具；如果没有这行代码，工具池策略仍要手写多条件判断。
    if not real_chrome_requested:  # 新增代码+BrowserSplit: 只有用户明确要求真实浏览器时才拦截；如果没有这行代码，普通浏览器任务会被误伤。
        return False  # 新增代码+BrowserSplit: 非真实浏览器请求不拦截；如果没有这行代码，普通 browser_open 会失效。
    if real_chrome_connected:  # 新增代码+BrowserSplit: 连接完成后允许页面工具操作真实会话；如果没有这行代码，连接成功后仍不能继续打开和输入。
        return False  # 新增代码+BrowserSplit: 已连接时不再拦截；如果没有这行代码，真实浏览器流程会卡在 connect 后。
    if server_name != "browser_automation":  # 新增代码+BrowserSplit: 只拦截浏览器自动化 server；如果没有这行代码，文件、MCP、搜索等无关工具会被误拦。
        return False  # 新增代码+BrowserSplit: 非浏览器工具不拦截；如果没有这行代码，真实浏览器请求会锁住无关能力。
    return original_name in INDEPENDENT_BROWSER_TOOL_NAMES  # 新增代码+BrowserSplit: 命中独立浏览器工具集合则拦截；如果没有这行代码，真实 Chrome 前置流程可以被绕过。
