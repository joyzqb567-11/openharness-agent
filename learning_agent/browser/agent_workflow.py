"""浏览器 workflow 与 agent 状态衔接的真实运行时实现。"""  # 新增代码+AgentPyPhaseFBrowserWorkflow: 把浏览器意图、harness、工具池解锁和客户模式 glue 从 agent.py 拆到 browser 层；若没有这个文件，主 agent 仍会承载浏览器 workflow 细节。

from __future__ import annotations  # 新增代码+AgentPyPhaseFBrowserWorkflow: 延迟解析类型注解；若没有这行代码，脚本模式下复杂注解更容易受导入顺序影响。

from typing import Any  # 新增代码+AgentPyPhaseFBrowserWorkflow: 用 Any 表示传入 agent、tool_call 和 AgentTool；若没有这行代码，本模块会为了类型注解反向导入 agent.py。

try:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 包运行模式下导入浏览器 workflow 依赖；若没有这行代码，python -m 运行时无法复用 browser 层规则。
    import learning_agent.browser.harness as harness_from_browser  # 新增代码+AgentPyPhaseFBrowserWorkflow: 导入真实 Chrome 和可见浏览器 harness 构造器；若没有这行代码，系统提示里的浏览器约束无法生成。
    import learning_agent.browser.intent as intent_from_browser  # 新增代码+AgentPyPhaseFBrowserWorkflow: 导入浏览器意图和工具阻断规则；若没有这行代码，agent 状态无法统一判断真实 Chrome/可见浏览器路线。
    import learning_agent.browser.permissions as permissions_from_browser  # 新增代码+AgentPyPhaseFBrowserWorkflow: 导入客户模式自动授权和进度文案规则；若没有这行代码，真实浏览器场景会回到多次 y/N。
    import learning_agent.core.run_helpers as run_helpers_from_core  # 新增代码+AgentPyPhaseFBrowserWorkflow: 导入 observation 记录 helper；若没有这行代码，workflow 解锁无法留下审计证据。
    import learning_agent.tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 导入工具目录和策略运行时；若没有这行代码，浏览器 workflow 仍会通过 agent.py 薄包装访问策略。
    import learning_agent.tools.search as search_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL3: 直接导入能力包查找实现；若没有这行代码，浏览器 workflow 还要绕回 agent.py 的能力包旧包装。
except ModuleNotFoundError as error:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 捕获 start_oauth_agent.bat 直接脚本模式下的包路径差异；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.harness", "learning_agent.browser.intent", "learning_agent.browser.permissions", "learning_agent.core", "learning_agent.core.run_helpers", "learning_agent.tools", "learning_agent.tools.catalog_runtime", "learning_agent.tools.search"}:  # 修改代码+AgentPyCompatWrapperRemovalL3: 允许 search 模块路径差异进入 fallback；若没有这行代码，bat 入口可能把路径模式误判成真实错误。
        raise  # 新增代码+AgentPyPhaseFBrowserWorkflow: 重新抛出真正的导入错误；若没有这行代码，排查 browser workflow 问题会看不到根因。
    import browser.harness as harness_from_browser  # 新增代码+AgentPyPhaseFBrowserWorkflow: 脚本模式下导入浏览器 harness 构造器；若没有这行代码，bat 入口无法注入浏览器任务约束。
    import browser.intent as intent_from_browser  # 新增代码+AgentPyPhaseFBrowserWorkflow: 脚本模式下导入浏览器意图和阻断规则；若没有这行代码，bat 入口无法识别真实 Chrome 或可见浏览器需求。
    import browser.permissions as permissions_from_browser  # 新增代码+AgentPyPhaseFBrowserWorkflow: 脚本模式下导入浏览器授权和进度文案规则；若没有这行代码，bat 入口客户模式会断开。
    import core.run_helpers as run_helpers_from_core  # 新增代码+AgentPyPhaseFBrowserWorkflow: 脚本模式下导入 observation helper；若没有这行代码，bat 入口 workflow 解锁无法审计。
    import tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入工具目录和策略运行时；若没有这行代码，bat 入口浏览器 workflow 策略查询会断开。
    import tools.search as search_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL3: 脚本模式下导入能力包查找实现；若没有这行代码，直接运行时浏览器工具解锁仍会依赖 agent.py 旧包装。


def detect_real_chrome_intent(user_input: str) -> bool:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，识别用户是否明确要求桌面真实 Chrome；若没有这段函数，agent.py 薄包装无法委托真实浏览器意图判断。
    return intent_from_browser.detect_real_chrome_intent(user_input)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 复用 browser.intent 的真实 Chrome 判断；若没有这行代码，真实浏览器关键词会重新散落到主类。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，detect_real_chrome_intent 到此结束；若没有这个边界说明，用户不容易看出意图识别入口已迁出 agent.py。


def detect_real_browser_information_task(user_input: str) -> bool:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，判断真实浏览器请求是否属于公开信息查询；若没有这段函数，客户模式无法区分查资料任务和普通打开浏览器。
    return intent_from_browser.detect_real_browser_information_task(user_input)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 复用 browser.intent 的信息任务判断；若没有这行代码，真实浏览器客户模式入口会分叉。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，detect_real_browser_information_task 到此结束；若没有这个边界说明，用户不容易看出真实浏览器信息任务判断已迁出 agent.py。


def detect_visible_browser_information_task(user_input: str) -> bool:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，判断普通实时查询是否需要可见独立浏览器；若没有这段函数，武汉天气攻略类 prompt 不会触发可见窗口路线。
    return intent_from_browser.detect_visible_browser_information_task(user_input)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 复用 browser.intent 的可见浏览器判断；若没有这行代码，普通实时查询识别会散落回 agent.py。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，detect_visible_browser_information_task 到此结束；若没有这个边界说明，用户不容易看出可见浏览器意图判断已迁出 agent.py。


def build_real_browser_task_harness_message(user_input: str) -> str:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，为真实 Chrome 信息任务构造系统提示约束；若没有这段函数，短 prompt 只能靠模型自觉走完整浏览器链路。
    return harness_from_browser.build_real_browser_task_harness_message(user_input)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 委托 browser.harness 生成真实浏览器 harness；若没有这行代码，harness 文案会回到主文件。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，build_real_browser_task_harness_message 到此结束；若没有这个边界说明，用户不容易看出真实浏览器 harness 入口已迁出 agent.py。


def build_visible_browser_task_harness_message(user_input: str) -> str:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，为普通实时查询构造可见浏览器系统提示约束；若没有这段函数，精准 prompt 仍可能只走后台搜索。
    return harness_from_browser.build_visible_browser_task_harness_message(user_input)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 委托 browser.harness 生成可见浏览器 harness；若没有这行代码，可见浏览器约束会回到主文件。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，build_visible_browser_task_harness_message 到此结束；若没有这个边界说明，用户不容易看出可见浏览器 harness 入口已迁出 agent.py。


def visible_browser_information_tool_names() -> set[str]:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，返回普通实时查询首轮可见的浏览器工具白名单；若没有这段函数，预加载逻辑会把白名单写散。
    return {  # 新增代码+AgentPyPhaseFBrowserWorkflow: 使用 set 保存可快速匹配的原始浏览器工具名；若没有这行代码，后续判断会更慢更脆弱。
        "browser_launch_visible",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 启动可见独立 Chromium；若没有这项，用户看不到真实浏览器窗口。
        "browser_open",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 打开公开搜索页或资料页；若没有这项，启动窗口后无法访问网页。
        "browser_wait",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 等待页面加载；若没有这项，动态页面可能读取过早。
        "browser_snapshot",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 读取可见页面文本；若没有这项，最终回答缺少网页证据。
        "browser_screenshot",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 保存视觉证据；若没有这项，肉眼可见验收证据不足。
        "browser_visual_locate",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 定位页面文字或搜索框；若没有这项，复杂页面流程容易失败。
        "browser_click",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 点击搜索框或同意按钮；若没有这项，模型无法完成拟人操作。
        "browser_type",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 输入搜索词；若没有这项，用户看不到真实输入过程。
        "browser_press_key",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 按 Enter 提交搜索；若没有这项，拟人搜索流程不完整。
        "browser_flow_run",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 执行短流程并保留步骤证据；若没有这项，复杂网站流程需要多次零散工具调用。
        "browser_recover_page",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 页面空白或失败时恢复；若没有这项，异常会退回后台搜索。
        "browser_replay",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 生成安全 dry-run 回放计划；若没有这项，任务回放证据不足。
        "browser_plugin_status",  # 新增代码+AgentPyPhaseFBrowserWorkflow: 查看插件兼容和可见浏览器状态；若没有这项，验收难以确认能力状态。
    }  # 新增代码+AgentPyPhaseFBrowserWorkflow: 白名单集合结束；若没有这行代码，Python set 语法不完整。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，visible_browser_information_tool_names 到此结束；若没有这个边界说明，用户不容易看出首轮白名单已迁出 agent.py。


def real_chrome_initial_tool_names() -> set[str]:  # 新增代码+RealChromeToolChain：函数段开始，列出真实 Chrome 请求首轮必须可见的安全前置工具；若没有这段函数，用户要求本地 Chrome 时模型仍可能只看到零散工具。
    return {  # 新增代码+RealChromeToolChain：返回 set 便于快速匹配原始 MCP 工具名；若没有这行代码，后续加载逻辑需要重复硬编码。
        "browser_profile_status",  # 新增代码+RealChromeToolChain：只读检查日常 Chrome profile 状态；若没有这项，模型无法先确认真实登录态环境。
    }  # 新增代码+RealChromeToolChain：首轮工具集合结束；若没有这行代码，Python set 语法不完整。
# 新增代码+RealChromeToolChain：函数段结束，real_chrome_initial_tool_names 到此结束；若没有这个边界说明，代码小白不容易看出首轮只暴露只读检查。


def real_chrome_connect_tool_names() -> set[str]:  # 新增代码+RealChromeToolChain：函数段开始，列出 profile status 后可加载的真实 Chrome 连接工具；若没有这段函数，connect 入口会继续卡在隐藏工具池里。
    return {  # 新增代码+RealChromeToolChain：返回连接阶段工具集合；若没有这行代码，连接工具名会散落在 workflow 更新分支里。
        "browser_connect_real_chrome",  # 新增代码+RealChromeToolChain：连接用户确认过的日常 Chrome profile；若没有这项，后续 open/snapshot/type/click 无法绑定真实 Chrome。
    }  # 新增代码+RealChromeToolChain：连接工具集合结束；若没有这行代码，Python set 语法不完整。
# 新增代码+RealChromeToolChain：函数段结束，real_chrome_connect_tool_names 到此结束；若没有这个边界说明，代码小白不容易看出 status 后才开放 connect。


def real_chrome_action_tool_names() -> set[str]:  # 新增代码+RealChromeToolChain：函数段开始，列出真实 Chrome 连接后自动加载的安全动作工具；若没有这段函数，连接成功后模型仍看不到 open/type/click。
    return {  # 新增代码+RealChromeToolChain：返回安全动作白名单；若没有这行代码，批量加载可能误把 evaluate/download 等高风险工具暴露。
        "browser_open",  # 新增代码+RealChromeToolChain：允许在真实 Chrome 中打开网页；若没有这项，uisdc/qianwen 真实访问无法开始。
        "browser_tabs",  # 新增代码+RealChromeToolChain：允许读取和切换标签页基础信息；若没有这项，多网页流程容易打错目标页。
        "browser_tabs_context",  # 新增代码+RealChromeToolChain：允许读取更完整的标签页上下文；若没有这项，真实多站点任务缺少页面定位证据。
        "browser_wait",  # 新增代码+RealChromeToolChain：允许等待动态页面加载；若没有这项，千问/网易云这类网页状态可能读取过早。
        "browser_snapshot",  # 新增代码+RealChromeToolChain：允许观察页面结构并生成下一动作 marker；若没有这项，observe-plan-act-verify 链路没有观察来源。
        "browser_screenshot",  # 新增代码+RealChromeToolChain：允许保存视觉证据；若没有这项，真实可见验收缺少截图辅助判断。
        "browser_visual_locate",  # 新增代码+RealChromeToolChain：允许按文字或视觉线索定位控件；若没有这项，复杂网页找输入框和按钮更容易失败。
        "browser_click",  # 新增代码+RealChromeToolChain：允许真实点击网页元素；若没有这项，发送按钮只能被脚本或键盘绕行。
        "browser_type",  # 新增代码+RealChromeToolChain：允许真实向网页输入文本；若没有这项，千问输入框失败会再次复发。
        "browser_press_key",  # 新增代码+RealChromeToolChain：允许按 Enter/Escape 等键；若没有这项，搜索和提交流程不完整。
        "browser_recover_page",  # 新增代码+RealChromeToolChain：允许页面空白或失焦时恢复；若没有这项，真实网页轻微异常就会中断。
    }  # 新增代码+RealChromeToolChain：安全动作白名单结束；若没有这行代码，Python set 语法不完整。
# 新增代码+RealChromeToolChain：函数段结束，real_chrome_action_tool_names 到此结束；若没有这个边界说明，代码小白不容易看出哪些工具会自动暴露。


def _load_browser_tools_by_original_names(agent: Any, original_names: set[str], observation_name: str) -> None:  # 新增代码+RealChromeToolChain：函数段开始，按 MCP 原始名把浏览器工具加入当前工具池；若没有这段函数，三个阶段会重复写加载和审计逻辑。
    if not original_names:  # 新增代码+RealChromeToolChain：防御空白名单；若没有这行代码，调用方传空集合时仍会遍历全部 catalog。
        return  # 新增代码+RealChromeToolChain：空集合直接退出；若没有这行代码，后续记录空事件会产生噪声。
    loaded_names: list[str] = []  # 新增代码+RealChromeToolChain：保存本次实际加载的模型工具名；若没有这行代码，审计无法解释工具池变化。
    blocked_lines: list[str] = []  # 新增代码+RealChromeToolChain：保存未能加载的策略原因；若没有这行代码，失败时看不到是 workflow 还是策略阻断。
    for pack_name in ("browser_automation", "real_chrome"):  # 新增代码+RealChromeToolChain：同时遍历普通浏览器包和真实 Chrome 包；若没有这行代码，connect 工具因属于 real_chrome 包会被漏掉。
        for tool in search_tools_from_tools.capability_pack_tools(agent, pack_name):  # 新增代码+RealChromeToolChain：遍历能力包内所有 MCP 浏览器工具；若没有这行代码，无法把原始名映射成 mcp__ 前缀名。
            if tool.server_name != "browser_automation":  # 新增代码+RealChromeToolChain：只处理 browser_automation server；若没有这行代码，其他 MCP server 的同名工具可能被误加载。
                continue  # 新增代码+RealChromeToolChain：跳过非浏览器 server 工具；若没有这行代码，工具边界会被放宽。
            if tool.original_name not in original_names:  # 新增代码+RealChromeToolChain：只加载本阶段白名单里的原始工具名；若没有这行代码，evaluate/download 等高风险工具可能被自动暴露。
                continue  # 新增代码+RealChromeToolChain：跳过不属于本阶段的工具；若没有这行代码，单个阶段会加载过多工具。
            decision = catalog_runtime_from_tools.tool_policy_decision(agent, tool)  # 新增代码+RealChromeToolChain：用统一 ToolPolicy 判断当前是否可选择；若没有这行代码，workflow/deny/skill gate 会被绕过。
            if not decision.selectable:  # 新增代码+RealChromeToolChain：不可选择的工具不能硬塞进工具池；若没有这行代码，安全策略会被自动加载绕开。
                blocked_lines.append(f"{tool.name}: state={decision.state}; reason={decision.reason}")  # 新增代码+RealChromeToolChain：记录被挡住的工具和原因；若没有这行代码，排查工具链仍会缺证据。
                continue  # 新增代码+RealChromeToolChain：继续检查其它工具；若没有这行代码，一个被挡工具会影响整批加载。
            agent.loaded_tool_names.add(tool.name)  # 新增代码+RealChromeToolChain：把安全且满足前置条件的工具加入当前工具池；若没有这行代码，下一轮模型仍看不到该工具。
            loaded_names.append(tool.name)  # 新增代码+RealChromeToolChain：记录实际加载成功的工具名；若没有这行代码，审计事件没有具体清单。
    if loaded_names or blocked_lines:  # 新增代码+RealChromeToolChain：只有有加载或阻断信息时才写 observation；若没有这行代码，空事件会污染调试日志。
        run_helpers_from_core.record_observation(agent, observation_name, {"tools": loaded_names, "blocked": blocked_lines})  # 新增代码+RealChromeToolChain：记录工具加载阶段证据；若没有这行代码，acceptance 失败后无法知道工具池为何变化。
# 新增代码+RealChromeToolChain：函数段结束，_load_browser_tools_by_original_names 到此结束；若没有这个边界说明，代码小白不容易看出通用加载 helper 范围。


def load_real_chrome_tools_for_requested_task(agent: Any) -> None:  # 新增代码+RealChromeToolChain：函数段开始，真实 Chrome prompt 首轮预加载只读前置工具；若没有这段函数，acceptance controller 初始工具面会缺真实 Chrome 准备入口。
    if not agent.real_chrome_requested:  # 新增代码+RealChromeToolChain：只在用户明确要求本地真实 Chrome 时启用；若没有这行代码，普通代码任务也会被浏览器工具污染。
        return  # 新增代码+RealChromeToolChain：非真实 Chrome 请求直接退出；若没有这行代码，工具池会不必要变大。
    agent.tool_policy_context.loaded_skills.add("real_chrome")  # 新增代码+RealChromeToolChain：标记真实 Chrome skill 已进入本轮任务范围；若没有这行代码，status 后 connect 仍可能被 skill gate 卡住。
    _load_browser_tools_by_original_names(agent, real_chrome_initial_tool_names(), "real_chrome_initial_tools_preloaded")  # 新增代码+RealChromeToolChain：加载只读 profile status；若没有这行代码，模型首轮无法执行安全前置检查。
# 新增代码+RealChromeToolChain：函数段结束，load_real_chrome_tools_for_requested_task 到此结束；若没有这个边界说明，代码小白不容易看出真实 Chrome 首轮加载范围。


def load_real_chrome_connect_tool_after_profile_status(agent: Any) -> None:  # 新增代码+RealChromeToolChain：函数段开始，在 profile status 后加载 connect；若没有这段函数，真实 Chrome 流程会停在状态检查后。
    if not agent.real_chrome_requested:  # 新增代码+RealChromeToolChain：只服务真实 Chrome 请求；若没有这行代码，普通 profile_status 调试也可能暴露 connect。
        return  # 新增代码+RealChromeToolChain：非目标任务直接退出；若没有这行代码，工具池会过度开放。
    _load_browser_tools_by_original_names(agent, real_chrome_connect_tool_names(), "real_chrome_connect_tool_loaded")  # 新增代码+RealChromeToolChain：把 connect 工具加入下一轮可见工具池；若没有这行代码，模型只能继续用 bash/CDP 绕行。
# 新增代码+RealChromeToolChain：函数段结束，load_real_chrome_connect_tool_after_profile_status 到此结束；若没有这个边界说明，代码小白不容易看出 connect 加载时机。


def load_real_chrome_action_tools_after_connect(agent: Any) -> None:  # 新增代码+RealChromeToolChain：函数段开始，在真实 Chrome 连接成功后加载安全页面动作工具；若没有这段函数，连接成功后仍无法 open/type/click。
    if not agent.real_chrome_requested:  # 新增代码+RealChromeToolChain：只在真实 Chrome 请求下启用；若没有这行代码，普通浏览器任务加载逻辑会被混用。
        return  # 新增代码+RealChromeToolChain：非目标任务直接退出；若没有这行代码，工具池会不必要膨胀。
    _load_browser_tools_by_original_names(agent, real_chrome_action_tool_names(), "real_chrome_action_tools_loaded")  # 新增代码+RealChromeToolChain：加载连接后的安全动作白名单；若没有这行代码，观察、输入、点击闭环无法执行。
# 新增代码+RealChromeToolChain：函数段结束，load_real_chrome_action_tools_after_connect 到此结束；若没有这个边界说明，代码小白不容易看出动作工具加载时机。


def load_visible_browser_tools_after_launch(agent: Any) -> None:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，可见浏览器启动成功后补加载普通浏览器能力包；若没有这段函数，agent 只能启动窗口但看不到 browser_open。
    loaded_names: list[str] = []  # 新增代码+AgentPyPhaseFBrowserWorkflow: 保存本次恢复可见的工具名；若没有这行代码，审计日志无法解释工具池变化。
    for tool in search_tools_from_tools.capability_pack_tools(agent, "browser_automation"):  # 修改代码+AgentPyCompatWrapperRemovalL3: 直连 tools.search 遍历普通浏览器自动化能力包；若没有这行代码，删除 agent.py 能力包旧包装后 browser_open、snapshot 等后续工具不会恢复。
        decision = catalog_runtime_from_tools.tool_policy_decision(agent, tool)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 直连 catalog_runtime 复用统一工具策略；若没有这行代码，浏览器工具解锁仍会反向依赖 agent.py。
        if decision.state == "blocked":  # 新增代码+AgentPyPhaseFBrowserWorkflow: 明确被安全策略禁止的工具仍不能加载；若没有这行代码，deny 规则会被 visible workflow 绕开。
            continue  # 新增代码+AgentPyPhaseFBrowserWorkflow: 跳过被禁止的工具并继续处理同包其他工具；若没有这行代码，一个禁用工具会影响整个包。
        agent.loaded_tool_names.add(tool.name)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 把允许的浏览器工具加入当前工具池；若没有这行代码，下一轮模型仍看不到 browser_open。
        loaded_names.append(tool.name)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 记录成功加入的工具名；若没有这行代码，观察事件没有详细清单。
    if loaded_names:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 只有确实加载到工具时才写观察事件；若没有这行代码，日志会出现空事件噪声。
        run_helpers_from_core.record_observation(agent, "visible_browser_loaded_tools", {"tools": loaded_names})  # 新增代码+AgentPyPhaseFBrowserWorkflow: 记录可见浏览器 workflow 解锁了哪些工具；若没有这行代码，验收失败时难以追溯工具池状态。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，load_visible_browser_tools_after_launch 到此结束；若没有这个边界说明，用户不容易看出可见浏览器后置加载已迁出 agent.py。


def load_visible_browser_tools_for_information_task(agent: Any) -> None:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，为普通实时查询首轮预加载可见浏览器工具；若没有这段函数，模型第一轮只能看到后台搜索或 profile_status。
    if not agent.visible_browser_information_task_requested:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 只处理被识别为自然实时查询的任务；若没有这行代码，所有任务都会提前暴露浏览器工具。
        return  # 新增代码+AgentPyPhaseFBrowserWorkflow: 非目标任务直接退出；若没有这行代码，代码分析任务可能被浏览器工具污染。
    agent.tool_policy_context.loaded_skills.add("browser_automation")  # 新增代码+AgentPyPhaseFBrowserWorkflow: 标记普通浏览器 skill 已准备；若没有这行代码，后续策略或审计无法解释工具为何可见。
    visible_query_tool_names = visible_browser_information_tool_names()  # 新增代码+AgentPyPhaseFBrowserWorkflow: 读取普通查询白名单；若没有这行代码，高风险 evaluate/downloads 可能首轮可见。
    loaded_names: list[str] = []  # 新增代码+AgentPyPhaseFBrowserWorkflow: 保存本次预加载的工具名；若没有这行代码，观察日志无法说明工具池变化。
    for tool in search_tools_from_tools.capability_pack_tools(agent, "browser_automation"):  # 修改代码+AgentPyCompatWrapperRemovalL3: 直连 tools.search 遍历普通浏览器自动化能力包；若没有这行代码，删除 agent.py 能力包旧包装后无法把白名单原始名转成 MCP 前缀工具名。
        if tool.original_name not in visible_query_tool_names:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 跳过不在自然查询白名单内的浏览器工具；若没有这行代码，高风险工具可能首轮可见。
            continue  # 新增代码+AgentPyPhaseFBrowserWorkflow: 继续检查同包其它工具；若没有这行代码，一个不需要的工具会中断循环。
        decision = catalog_runtime_from_tools.tool_policy_decision(agent, tool)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 直连 catalog_runtime 复用统一策略；若没有这行代码，预加载策略来源仍不在 tools 层。
        if decision.state == "blocked":  # 新增代码+AgentPyPhaseFBrowserWorkflow: 被策略明确禁止的工具不能暴露；若没有这行代码，deny rule 会被预加载绕开。
            continue  # 新增代码+AgentPyPhaseFBrowserWorkflow: 跳过被阻断工具；若没有这行代码，一个禁用工具会影响其它安全工具。
        agent.loaded_tool_names.add(tool.name)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 将允许的 MCP 工具加入当前工具池；若没有这行代码，模型第一轮看不到 browser_launch_visible。
        loaded_names.append(tool.name)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 记录预加载成功的工具名；若没有这行代码，调试日志缺少具体列表。
    if loaded_names:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 只有确实预加载到工具时记录观察事件；若没有这行代码，日志会出现空事件噪声。
        run_helpers_from_core.record_observation(agent, "visible_browser_information_tools_preloaded", {"tools": loaded_names})  # 新增代码+AgentPyPhaseFBrowserWorkflow: 写入工具池预加载证据；若没有这行代码，验收失败时难以确认首轮工具状态。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，load_visible_browser_tools_for_information_task 到此结束；若没有这个边界说明，用户不容易看出首轮可见工具预加载已迁出 agent.py。


def update_workflows_after_mcp_tool(agent: Any, tool_call: Any, result_text: str) -> None:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，根据 MCP 结果推进真实 Chrome 和可见浏览器 workflow 状态；若没有这段函数，status/connect/launch 只是文本不会影响 ToolPolicy。
    catalog_tool = catalog_runtime_from_tools.find_catalog_tool(agent, tool_call.name)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 直连 catalog_runtime 读取 AgentTool 元数据；若没有这行代码，浏览器 workflow 仍依赖 agent.py 兼容查找入口。
    if catalog_tool is None:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 找不到目录工具时不更新 workflow；若没有这行代码，后续访问 original_name 会报错。
        return  # 新增代码+AgentPyPhaseFBrowserWorkflow: 无元数据直接退出；若没有这行代码，异常 catalog 会中断 MCP 调用结果返回。
    if catalog_tool.server_name == "browser_automation" and catalog_tool.original_name == "browser_profile_status":  # 新增代码+AgentPyPhaseFBrowserWorkflow: profile status 是真实 Chrome workflow 的前置检查；若没有这行代码，状态工具不会解锁连接准备。
        agent.tool_policy_context.loaded_skills.add("real_chrome")  # 新增代码+AgentPyPhaseFBrowserWorkflow: 标记真实 Chrome skill 已准备；若没有这行代码，connect 工具会一直卡在 needs_skill。
        agent.tool_policy_context.completed_workflows.add("real_chrome_profile_ready")  # 新增代码+AgentPyPhaseFBrowserWorkflow: 标记 profile 状态检查已完成；若没有这行代码，connect 工具会一直卡在 needs_workflow。
        load_real_chrome_connect_tool_after_profile_status(agent)  # 新增代码+RealChromeToolChain：profile status 后立即加载 connect 工具；若没有这行代码，真实 Chrome 流程会卡住并诱发 bash/CDP 绕行。
        run_helpers_from_core.record_observation(agent, "real_chrome_profile_ready", {"tool_name": tool_call.name})  # 新增代码+AgentPyPhaseFBrowserWorkflow: 记录真实 Chrome 前置 workflow 完成；若没有这行代码，审计看不到为何 connect 被解锁。
    if catalog_tool.server_name == "browser_automation" and catalog_tool.original_name == "browser_connect_real_chrome" and "real_chrome_connected=true" in result_text:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 连接结果明确成功时推进 connected workflow；若没有这行代码，后续 browser_open 仍会被真实 Chrome 需求拦截。
        agent.tool_policy_context.completed_workflows.add("real_chrome_connected")  # 新增代码+AgentPyPhaseFBrowserWorkflow: 标记真实 Chrome 会话已连接；若没有这行代码，后续页面操作无法被策略放行。
        load_real_chrome_action_tools_after_connect(agent)  # 新增代码+RealChromeToolChain：连接成功后加载 open/snapshot/type/click 等安全动作工具；若没有这行代码，模型仍看不到真实浏览器操作工具。
        run_helpers_from_core.record_observation(agent, "real_chrome_connected", {"tool_name": tool_call.name})  # 新增代码+AgentPyPhaseFBrowserWorkflow: 记录真实 Chrome 连接完成；若没有这行代码，审计缺少高风险 workflow 证据。
    if catalog_tool.server_name == "browser_automation" and catalog_tool.original_name == "browser_launch_visible" and "visible_browser=true" in result_text and "headless=false" in result_text:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 可见独立浏览器启动成功时推进 visible workflow；若没有这行代码，后续 browser_open 仍会被真实 Chrome 关键词拦截。
        agent.tool_policy_context.completed_workflows.add("visible_browser_launched")  # 新增代码+AgentPyPhaseFBrowserWorkflow: 标记可见浏览器会话已启动；若没有这行代码，策略层不知道可以放行普通页面工具。
        load_visible_browser_tools_after_launch(agent)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 启动成功后补加载 browser_automation 能力包；若没有这行代码，下一轮模型工具池仍缺 browser_open。
        run_helpers_from_core.record_observation(agent, "visible_browser_launched", {"tool_name": tool_call.name})  # 新增代码+AgentPyPhaseFBrowserWorkflow: 记录可见浏览器 workflow 完成；若没有这行代码，真实验收日志缺少为什么放行的证据。
    if catalog_tool.server_name == "browser_automation" and catalog_tool.original_name == "browser_disconnect_real_chrome":  # 新增代码+AgentPyPhaseFBrowserWorkflow: 断开工具执行后需要清连接状态；若没有这行代码，策略会误以为仍连接真实 Chrome。
        agent.tool_policy_context.completed_workflows.discard("real_chrome_connected")  # 新增代码+AgentPyPhaseFBrowserWorkflow: 移除真实 Chrome 已连接状态；若没有这行代码，断开后仍可能放行页面操作。
        run_helpers_from_core.record_observation(agent, "real_chrome_disconnected", {"tool_name": tool_call.name})  # 新增代码+AgentPyPhaseFBrowserWorkflow: 记录真实 Chrome 断开事件；若没有这行代码，审计无法还原连接生命周期。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，update_workflows_after_mcp_tool 到此结束；若没有这个边界说明，用户不容易看出 MCP 后置 workflow 推进已迁出 agent.py。


def real_browser_customer_mode_active(agent: Any) -> bool:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，判断本轮是否可以启用真实浏览器公开查询自动授权；若没有这段函数，权限分支会重复拼条件且容易放宽边界。
    return permissions_from_browser.real_browser_customer_mode_active(agent.real_chrome_requested, agent.real_browser_information_task_requested)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 委托 browser.permissions 判断客户模式是否激活；若没有这行代码，终端和 MCP 的客户模式条件会继续重复。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，real_browser_customer_mode_active 到此结束；若没有这个边界说明，用户不容易看出客户模式判断已迁出 agent.py。


def real_browser_customer_auto_approve_reason(agent: Any, tool_call: Any) -> str:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，给 MCP 适配层返回浏览器客户模式自动授权原因；若没有这段函数，MCP 适配层无法区分客户模式和普通高风险权限。
    real_reason = permissions_from_browser.real_browser_customer_auto_approve_reason(tool_call.name, tool_call.arguments, customer_mode_active=real_browser_customer_mode_active(agent))  # 新增代码+AgentPyPhaseFBrowserWorkflow: 先保留真实 Chrome 客户模式白名单；若没有这行代码，显式真实浏览器查询会回归多次授权。
    if real_reason:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 如果真实 Chrome 白名单已命中就直接使用；若没有这行代码，后续普通浏览器规则可能覆盖真实 profile 审计原因。
        return real_reason  # 新增代码+AgentPyPhaseFBrowserWorkflow: 返回真实 Chrome 授权原因；若没有这行代码，调用方拿不到既有客户模式结果。
    return permissions_from_browser.visible_browser_customer_auto_approve_reason(tool_call.name, tool_call.arguments, customer_mode_active=agent.visible_browser_information_task_requested)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 普通实时查询走独立 Chromium 白名单；若没有这行代码，精准 prompt 会被大量 y/N 打断。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，real_browser_customer_auto_approve_reason 到此结束；若没有这个边界说明，用户不容易看出浏览器自动授权原因已迁出 agent.py。


def real_browser_customer_progress_message(tool_call: Any) -> str:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，返回真实浏览器客户模式进度提示；若没有这段函数，MCP 工具执行时无法在终端展示下一步操作。
    return permissions_from_browser.real_browser_customer_progress_message(tool_call.name, tool_call.arguments)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 委托 browser.permissions 生成进度文案；若没有这行代码，进度提示逻辑会重新散落在巨型 agent 文件里。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，real_browser_customer_progress_message 到此结束；若没有这个边界说明，用户不容易看出浏览器进度文案入口已迁出 agent.py。


def print_real_browser_customer_progress(message: str) -> None:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，统一打印客户可见进度行；若没有这段函数，多个工具分支会重复 print 格式。
    if message:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 只有非空消息才打印；若没有这行代码，空消息可能产生无意义空行。
        print(f"Agent > {message}", flush=True)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 立即把进度显示到真实终端；若没有这行代码，用户看不到 agent 正在做什么。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，print_real_browser_customer_progress 到此结束；若没有这个边界说明，用户不容易看出终端进度输出已迁出 agent.py。


def real_chrome_request_blocks_independent_browser(agent: Any, tool: Any) -> bool:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，判断真实 Chrome 请求是否应拦截独立浏览器工具；若没有这段函数，工具策略会在主类里拼状态。
    return intent_from_browser.real_chrome_request_blocks_independent_browser(real_chrome_requested=agent.real_chrome_requested, real_chrome_connected="real_chrome_connected" in agent.tool_policy_context.completed_workflows, visible_browser_launched="visible_browser_launched" in agent.tool_policy_context.completed_workflows, server_name=tool.server_name, original_name=tool.original_name)  # 新增代码+AgentPyPhaseFBrowserWorkflow: 委托 browser.intent 做最终阻断判断；若没有这行代码，browser_launch_visible 成功后 browser_open 仍可能被隐藏。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，real_chrome_request_blocks_independent_browser 到此结束；若没有这个边界说明，用户不容易看出工具策略阻断入口已迁出 agent.py。


def independent_browser_tool_names() -> set[str]:  # 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段开始，列出真实 Chrome 连接前不应直接使用的独立浏览器工具；若没有这段函数，拦截范围没有统一来源。
    return intent_from_browser.independent_browser_tool_names()  # 新增代码+AgentPyPhaseFBrowserWorkflow: 委托 browser.intent 返回独立浏览器工具集合；若没有这行代码，工具名单仍无法被浏览器层测试复用。
# 新增代码+AgentPyPhaseFBrowserWorkflow: 函数段结束，independent_browser_tool_names 到此结束；若没有这个边界说明，用户不容易看出独立浏览器名单入口已迁出 agent.py。
