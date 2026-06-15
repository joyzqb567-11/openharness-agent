"""Computer Use full 模式的模型主循环提示和工具范围规则。"""  # 新增代码+AgentPySplitPhase2: 说明本文件负责 full 模式如何给模型提示和收窄工具；如果没有这行代码，代码小白不知道这个模块和 models 文件夹不是一回事。

from __future__ import annotations  # 新增代码+AgentPySplitPhase2: 允许类型注解延迟解析；如果没有这行代码，复杂类型在旧运行方式下更容易受定义顺序影响。

from typing import Any, Callable  # 新增代码+AgentPySplitPhase2: 导入通用数据类型和回调类型；如果没有这行代码，函数签名无法清楚表达外层 agent 传入什么能力。


HasAgentOwnedLaunchTarget = Callable[[], bool]  # 新增代码+AgentPySplitPhase2: 定义“是否已有 agent 自己打开的窗口”的回调类型；如果没有这行代码，新模块会被迫直接依赖 LearningAgent 类。


# 新增代码+AgentPySplitPhase2: 函数段开始，build_computer_use_full_model_loop_harness_message 生成 full 模式模型主循环提示；如果没有这段函数，桌面任务提示词会继续堆在 agent.py。
def build_computer_use_full_model_loop_harness_message(user_input: str, desktop_task_context: Any, loaded_tool_names: Any) -> str:  # 新增代码+AgentPySplitPhase2: 定义提示词构造入口；如果没有这行代码，agent.py 无法把旧私有函数委托给新模块。
    if not isinstance(desktop_task_context, dict):  # 新增代码+AgentPySplitPhase2: 防御外层传入异常上下文形状；如果没有这行代码，坏状态可能让 system prompt 构造崩溃。
        return ""  # 新增代码+AgentPySplitPhase2: 上下文异常时不注入额外规则；如果没有这行代码，普通任务可能被错误污染。
    if not bool(desktop_task_context.get("active", False)):  # 新增代码+AgentPySplitPhase2: 只在桌面任务 active 时启用 Computer Use harness；如果没有这行代码，所有代码任务都会看到桌面控制规则。
        return ""  # 新增代码+AgentPySplitPhase2: 非桌面任务返回空字符串；如果没有这行代码，system prompt 会出现无关约束。
    if not bool(desktop_task_context.get("requires_gui_actions", False)):  # 新增代码+AgentPySplitPhase2: 只处理确实需要 GUI 动作的任务；如果没有这行代码，普通解释类桌面问题也会被误导去控制鼠标。
        return ""  # 新增代码+AgentPySplitPhase2: 无需 GUI 的桌面相关问题不注入；如果没有这行代码，模型可能过度使用 Computer Use。
    loaded_computer_tools = {"mcp__computer-use__request_access", "mcp__computer-use__observe", "mcp__computer-use__screenshot", "mcp__computer-use__open_application"} & set(loaded_tool_names or set())  # 新增代码+AgentPySplitPhase2: 确认 full 命令已经把核心桌面工具放入工具池；如果没有这行代码，模型会收到规则但看不到对应工具。
    if not {"mcp__computer-use__request_access", "mcp__computer-use__observe", "mcp__computer-use__screenshot", "mcp__computer-use__open_application"}.issubset(loaded_computer_tools):  # 新增代码+AgentPySplitPhase2: 四个核心工具不齐时不注入 full harness；如果没有这行代码，半加载状态会误导模型调用不存在的工具。
        return ""  # 新增代码+AgentPySplitPhase2: 工具不齐时返回空规则；如果没有这行代码，错误工具池会被提示词掩盖。
    target_app_hint = str(desktop_task_context.get("target_app_hint", "") or "").strip()  # 新增代码+AgentPySplitPhase2: 读取脱敏目标应用提示；如果没有这行代码，harness 无法把“画图/mspaint”这类安全线索传给模型。
    canonical_target_app = computer_use_full_canonical_target_app_hint(target_app_hint)  # 新增代码+AgentPySplitPhase2: 把用户友好应用名转成更稳定的启动名；如果没有这行代码，模型可能把中文应用名原样传给启动器导致失败。
    task_goal = str(desktop_task_context.get("task_goal", "") or "").strip()  # 新增代码+AgentPySplitPhase2: 读取脱敏任务目标提示；如果没有这行代码，harness 无法提醒模型当前是绘图、打开应用等 GUI 任务。
    discovery_only = computer_use_full_user_requested_discovery_only(user_input)  # 新增代码+AgentPySplitPhase2: 判断用户是否只想查找 app_name 且不要打开软件；如果没有这行代码，查询类任务会被首轮 launch_app 规则误导。
    desktop_task_context["discovery_only"] = bool(discovery_only)  # 新增代码+AgentPySplitPhase2: 把 discovery-only 意图写回桌面上下文供工具收窄逻辑使用；如果没有这行代码，第 0 轮仍可能只暴露 mcp__computer-use__open_application。
    app_catalog_context = "本轮是应用候选发现任务：不要直接从提示词里的内置候选清单回答，必须先调用 `mcp__computer-use__request_access`，query 使用用户目标应用或原始查询词；如果用户说不要打开或操作软件，禁止调用 `launch_app`。" if discovery_only else computer_use_full_app_catalog_context()  # 新增代码+AgentPySplitPhase2: 发现类任务改为工具驱动，非发现任务给模型应用候选清单；如果没有这行代码，真实主循环可能跳过 mcp__computer-use__request_access 或猜 app 名。
    return "\n".join([  # 新增代码+AgentPySplitPhase2: 拼出短提示词块；如果没有这行代码，模型不会获得结构化 Computer Use full 工作方式。
        "Computer Use full 模式已开启。",  # 新增代码+AgentPySplitPhase2: 明确告诉模型当前处于 full 模式；如果没有这行代码，模型可能不知道用户已经授权工具包。
        app_catalog_context,  # 新增代码+AgentPySplitPhase2: 把应用候选或发现任务规则交给模型主循环；如果没有这行代码，模型仍只能靠猜测 app 名。
        "用户自然语言仍在本轮 user message 中，请你在模型主循环里理解任务语义。",  # 新增代码+AgentPySplitPhase2: 强调语义理解由模型完成；如果没有这行代码，后续维护者可能再次把 prompt 交给 Python planner。
        "如果用户只是查询本机应用是否可用、要哪个 app_name、或明确不要打开/操作软件，第一步必须调用 `mcp__computer-use__request_access` 并基于工具结果回答。",  # 新增代码+AgentPySplitPhase2: 把应用发现作为主循环工具步骤；如果没有这行代码，模型可能再次直接从候选提示里回答。
        "如果 mcp__computer-use__request_access 返回唯一高置信候选，并且用户目标是打开或操作本机应用，下一轮必须使用该候选的 app_name 调用 `mcp__computer-use__open_application`，action=launch_app；不要把“发现到候选”当成最终完成。",  # 新增代码+AgentPySplitPhase2: 约束 discover 后必须进入真实启动；如果没有这行代码，微信这类应用可能被发现后模型直接结束。
        "从 mcp__computer-use__request_access 复制候选字段时必须逐字复制 app_name 或规范启动应用名，不要追加 .exe、.lnk、.pdf、问号、说明文字或其它后缀；需要保留启动标识时放在 target 字段。",  # 新增代码+AgentPySplitPhase2: 阻止模型污染启动名；如果没有这行代码，后端虽可兜底但日志和后续工具选择会被污染。
        "本机应用任务第 0 轮只做第一步：如果规范启动应用名不是“未知”且还没有 agent-owned target_window，必须先调用 `mcp__computer-use__open_application`，action=launch_app，app_name 使用规范启动应用名；不要在第 0 轮规划完整绘图、点击画布或等待截图。",  # 新增代码+AgentPySplitPhase2: 把真实终端失败的第 0 轮长规划收窄成启动绑定；如果没有这行代码，自然语言“用画图画树”可能再次卡在模型第 0 轮。
        "先用 `mcp__computer-use__observe` 观察屏幕和窗口，再用 `mcp__computer-use__left_click`、`mcp__computer-use__type`、`mcp__computer-use__key`、`mcp__computer-use__scroll` 或 `mcp__computer-use__computer_batch` 执行一个小步动作，随后继续观察和纠偏。",  # 新增代码+AgentPySplitPhase2: 描述 observe-plan-act 闭环；如果没有这行代码，模型可能跳过观察直接盲点鼠标。
        "每次观察后都要先判断当前画面是否服务于用户本轮目标；观察到当前画面与用户本轮目标不一致时，必须先纠偏到本轮目标状态，例如新建、清空、导航、重新聚焦或选择正确窗口，然后再继续操作。",  # 新增代码+AgentPySplitPhase2: 写入观察后的目标一致性检查；如果没有这行代码，模型可能把旧窗口或旧画布当成当前任务。
        "如果用户要求使用某个本机应用且该应用没有明确可用窗口，先调用 `mcp__computer-use__open_application` 的 `launch_app`，传入 `app_name`，再观察返回的 `target_window`。",  # 新增代码+AgentPySplitPhase2: 告诉模型先打开软件再操作窗口；如果没有这行代码，模型可能在未打开目标应用时盲目移动鼠标键盘。
        "除非用户明确要求复用已有窗口，否则本机应用任务优先用 `launch_app` 创建 agent-owned 新窗口，不要把用户旧窗口当成自己打开的软件。",  # 新增代码+AgentPySplitPhase2: 要求模型优先创建自有窗口；如果没有这行代码，真实验收会被用户预先打开的窗口误判成功。
        "本轮目标必须始终以用户原始自然语言为准；如果截图里有旧画布或旧图形，不要把任务漂移成续画、修补或美化旧内容。",  # 新增代码+AgentPySplitPhase2: 固定本轮用户目标；如果没有这行代码，画图任务可能因旧画布而跑偏。
        "不要主动添加用户未要求的对象、背景、装饰或新主题；当截图已经能表达用户要求的目标时，直接最终回答，不要为了“丰富画面”继续加笔。",  # 新增代码+AgentPySplitPhase2: 禁止模型扩展未请求内容；如果没有这行代码，简单绘图任务可能漂移成新主题。
        "如果目标应用里已有无关旧图，优先选择空白区域、新建空白画布或清空画布，再绘制本轮目标对象。",  # 新增代码+AgentPySplitPhase2: 给模型处理残留画布的通用策略；如果没有这行代码，旧画布会持续污染视觉规划。
        "桌面任务不要用 `bash`、`read`、`write`、`edit` 生成最终图像或替代 GUI 操作；这些工具只可用于必要诊断。",  # 新增代码+AgentPySplitPhase2: 阻止模型用脚本产物冒充 GUI 操作；如果没有这行代码，真实桌面任务可能被离线文件替代。
        "需要连续鼠标轨迹时使用 `mcp__computer-use__open_application` 的 `drag_path` 和 `points`，不要把绘图任务退化成输入文字说明。",  # 新增代码+AgentPySplitPhase2: 提醒模型用通用拖拽原语；如果没有这行代码，模型可能继续只打字描述图像。
        "完成前至少观察一次结果；最终回答必须包含 computer_use_mcp_v2、mspaint 或实际 app_id、screenshot、real_desktop_touched 和 low_level_event_count 摘要。",  # 新增代码+AgentPySplitPhase2: 要求最终输出带稳定验收 token；如果没有这行代码，终端只能看到“已完成”而无法机器确认真实触碰桌面。
        "不要调用 `computer_use_mcp_v2` 的 `run_prompt` 或 `mode` 来执行整段自然语言任务；那只是旧兼容入口，不是语义规划器。",  # 新增代码+AgentPySplitPhase2: 阻止黑盒 prompt 执行；如果没有这行代码，模型可能继续绕过主循环。
        f"脱敏目标应用提示：{target_app_hint or '未知'}；规范启动应用名：{canonical_target_app or '未知'}；脱敏任务类型提示：{task_goal or '未知'}。",  # 新增代码+AgentPySplitPhase2: 同时提供用户友好提示和规范启动名；如果没有这行代码，模型可能不知道应该把“画图”转换成 mspaint。
    ])  # 新增代码+AgentPySplitPhase2: 结束提示词行列表并返回；如果没有这行代码，Python 语法不完整。
# 新增代码+AgentPySplitPhase2: 函数段结束，build_computer_use_full_model_loop_harness_message 到此结束；如果没有这个边界说明，用户不容易看出模型循环 harness 的范围。


# 新增代码+AgentPySplitPhase2: 函数段开始，computer_use_full_user_requested_discovery_only 判断用户是否只想发现应用候选；如果没有这段函数，查 app_name 任务会被当成 GUI 操作任务。
def computer_use_full_user_requested_discovery_only(user_input: str) -> bool:  # 新增代码+AgentPySplitPhase2: 定义 discovery-only 意图识别入口；如果没有这行代码，工具收窄无法知道用户是否明确不要打开软件。
    text = str(user_input or "").casefold()  # 新增代码+AgentPySplitPhase2: 把用户输入转成大小写无关文本；如果没有这行代码，英文 app_name 查询大小写会影响判断。
    discovery_markers = ("查找", "查询", "是否可用", "可用", "哪个 app_name", "app_name", "候选", "discover", "find app", "which app")  # 新增代码+AgentPySplitPhase2: 定义发现类任务关键词；如果没有这行代码，函数无法识别用户只是想找应用名。
    no_launch_markers = ("不要打开", "不打开", "不要启动", "不启动", "不要操作", "不操作", "不要控制", "不控制", "without launching", "do not launch", "do not open")  # 新增代码+AgentPySplitPhase2: 定义禁止打开/操作关键词；如果没有这行代码，发现任务可能仍被当成启动任务。
    has_discovery_intent = any(marker in text for marker in discovery_markers)  # 新增代码+AgentPySplitPhase2: 检查用户是否表达应用发现意图；如果没有这行代码，函数只能看禁止打开而无法判断任务类型。
    has_no_launch_intent = any(marker in text for marker in no_launch_markers)  # 新增代码+AgentPySplitPhase2: 检查用户是否明确不要打开或操作；如果没有这行代码，函数可能误把普通“打开画图”当成发现任务。
    return bool(has_discovery_intent and has_no_launch_intent)  # 新增代码+AgentPySplitPhase2: 只有同时满足发现和不打开才进入 discovery-only；如果没有这行代码，函数没有最终判断结果。
# 新增代码+AgentPySplitPhase2: 函数段结束，computer_use_full_user_requested_discovery_only 到此结束；如果没有这个边界说明，用户不容易看出发现类意图识别范围。


# 新增代码+AgentPySplitPhase2: 函数段开始，computer_use_full_app_catalog_context 构造 full 模式模型可见应用候选清单；如果没有这段函数，应用发现无法接入模型主循环。
def computer_use_full_app_catalog_context() -> str:  # 新增代码+AgentPySplitPhase2: 定义应用候选清单提示入口；如果没有这行代码，agent.py 无法把 inventory 提示委托给新模块。
    from .windows_app_inventory import build_windows_app_inventory, format_windows_app_inventory_for_model  # 新增代码+AgentPySplitPhase2: 从同包导入统一应用枚举和格式化函数；如果没有这行代码，模型提示拿不到清洗后的候选清单。
    catalog = build_windows_app_inventory(include_common=True)  # 新增代码+AgentPySplitPhase2: 枚举并清洗本机应用候选；如果没有这行代码，模型提示没有实际候选来源。
    return format_windows_app_inventory_for_model(catalog)  # 新增代码+AgentPySplitPhase2: 返回不含原始路径的模型提示文本；如果没有这行代码，harness 无法拼接候选清单。
# 新增代码+AgentPySplitPhase2: 函数段结束，computer_use_full_app_catalog_context 到此结束；如果没有这个边界说明，用户不容易看出候选清单提示范围。


# 新增代码+AgentPySplitPhase2: 函数段开始，computer_use_full_canonical_target_app_hint 把脱敏应用提示转换成稳定启动别名；如果没有这段函数，模型会在“画图”和 mspaint 之间摇摆。
def computer_use_full_canonical_target_app_hint(target_app_hint: str) -> str:  # 新增代码+AgentPySplitPhase2: 定义目标应用规范化入口；如果没有这行代码，首轮 launch_app 收窄不知道应该使用哪个 app_name。
    normalized_hint = str(target_app_hint or "").strip().lower()  # 新增代码+AgentPySplitPhase2: 清理目标应用提示并统一小写；如果没有这行代码，空白和大小写会让别名匹配不稳定。
    if not normalized_hint or normalized_hint == "未知":  # 新增代码+AgentPySplitPhase2: 没有有效应用提示时返回空；如果没有这行代码，未知目标可能被误当成可启动应用。
        return ""  # 新增代码+AgentPySplitPhase2: 空提示不生成规范启动名；如果没有这行代码，首轮工具收窄会错误要求 launch_app。
    from .windows_app_inventory import resolve_windows_app_name_hint  # 新增代码+AgentPySplitPhase2: 使用统一应用名解析器；如果没有这行代码，中文/英文别名无法共享清单逻辑。
    catalog_hint = resolve_windows_app_name_hint(normalized_hint)  # 新增代码+AgentPySplitPhase2: 用统一候选清单解析规范 app_name；如果没有这行代码，模型仍无法从清单别名得到 mspaint。
    if catalog_hint:  # 新增代码+AgentPySplitPhase2: 命中清单别名时优先使用；如果没有这行代码，清单解析结果不会生效。
        return catalog_hint  # 新增代码+AgentPySplitPhase2: 返回清单给出的稳定 app_name；如果没有这行代码，后续仍走旧硬编码路径。
    alias_map = {"画图": "mspaint", "画图软件": "mspaint", "paint": "mspaint", "mspaint": "mspaint", "mspaint.exe": "mspaint", "记事本": "notepad", "notepad": "notepad", "notepad.exe": "notepad", "计算器": "calc", "calculator": "calc", "calc": "calc", "calc.exe": "calc"}  # 新增代码+AgentPySplitPhase2: 保存常见安全本机应用别名；如果没有这行代码，模型需要自己猜中文应用名和可执行名的对应关系。
    return alias_map.get(normalized_hint, str(target_app_hint or "").strip())  # 新增代码+AgentPySplitPhase2: 优先返回规范别名，未知普通应用保留原提示给通用发现层；如果没有这行代码，函数没有返回值。
# 新增代码+AgentPySplitPhase2: 函数段结束，computer_use_full_canonical_target_app_hint 到此结束；如果没有这个边界说明，用户不容易看出这里不解析“画树/画猫”等任务主体。


# 新增代码+AgentPySplitPhase2: 函数段开始，computer_use_full_initial_launch_required 判断第 0 轮是否必须先让模型选择 launch_app；如果没有这段函数，首轮工具收窄逻辑会散落在 run_events 主循环里。
def computer_use_full_initial_launch_required(turn: int, desktop_task_context: Any, has_agent_owned_launch_target: HasAgentOwnedLaunchTarget) -> bool:  # 新增代码+AgentPySplitPhase2: 定义首轮启动判断入口；如果没有这行代码，agent.py 无法把旧私有判断委托给新模块。
    if turn != 0:  # 新增代码+AgentPySplitPhase2: 只收窄第 0 轮；如果没有这行代码，后续观察、绘图和纠偏轮次会一直看不到观察/动作工具。
        return False  # 新增代码+AgentPySplitPhase2: 非首轮不要求启动；如果没有这行代码，任务无法进入完整 observe-plan-act 循环。
    if not isinstance(desktop_task_context, dict):  # 新增代码+AgentPySplitPhase2: 防御异常上下文形状；如果没有这行代码，坏状态可能让主循环崩溃。
        return False  # 新增代码+AgentPySplitPhase2: 上下文异常时不收窄工具面；如果没有这行代码，普通任务可能被误拦。
    if str(desktop_task_context.get("runtime", "") or "") == "computer_use_mcp_v2" and str(desktop_task_context.get("terminal_mode", "") or "") in {"full", "normal", "observe"}:  # 修改代码+ComputerUseMcpV2SchemaNarrowingFix：已通过 `/computer use` 打开的 v2 会话要保持 ClaudeCode 风格 MCP 全量工具面；如果没有这一行，首轮会把 observe/left_click 等工具误删，只剩 request_access/open_application。
        return False  # 修改代码+ComputerUseMcpV2SchemaNarrowingFix：v2 终端会话不触发旧首轮启动收窄；如果没有这一行，真实验收里模型会看不到用户明确要求的原子工具。
    if not bool(desktop_task_context.get("active", False)):  # 新增代码+AgentPySplitPhase2: 只对桌面任务启用；如果没有这行代码，代码开发任务第 0 轮也可能只剩 mcp__computer-use__open_application。
        return False  # 新增代码+AgentPySplitPhase2: 非桌面任务保持原工具池；如果没有这行代码，agent 的 coding 能力会被破坏。
    if not bool(desktop_task_context.get("requires_gui_actions", False)):  # 新增代码+AgentPySplitPhase2: 只对需要真实 GUI 动作的任务启用；如果没有这行代码，桌面解释类问题也会被迫启动应用。
        return False  # 新增代码+AgentPySplitPhase2: 无需 GUI 动作时不收窄；如果没有这行代码，普通状态询问可能被误导。
    if bool(desktop_task_context.get("discovery_only", False)):  # 新增代码+AgentPySplitPhase2: 发现类任务不强制启动应用；如果没有这行代码，用户明确不要打开软件时第 0 轮仍会只剩 launch_app。
        return False  # 新增代码+AgentPySplitPhase2: 返回不要求 launch_app；如果没有这行代码，模型无法先调用 mcp__computer-use__request_access。
    target_app_hint = str(desktop_task_context.get("target_app_hint", "") or "").strip()  # 新增代码+AgentPySplitPhase2: 读取脱敏目标应用提示；如果没有这行代码，无法判断是否有可启动应用。
    if not computer_use_full_canonical_target_app_hint(target_app_hint):  # 新增代码+AgentPySplitPhase2: 没有规范启动名时不强制 launch_app；如果没有这行代码，开放式坐标任务会被错误要求启动未知软件。
        return False  # 新增代码+AgentPySplitPhase2: 无目标应用时保留完整工具面；如果没有这行代码，模型无法处理纯屏幕任务。
    if has_agent_owned_launch_target():  # 新增代码+AgentPySplitPhase2: 如果已经有 agent-owned 目标窗口就不再要求首轮启动；如果没有这行代码，恢复或重入时可能重复打开应用。
        return False  # 新增代码+AgentPySplitPhase2: 已有目标窗口时放开完整工具面；如果没有这行代码，后续无法观察和绘制。
    return True  # 新增代码+AgentPySplitPhase2: 满足条件时首轮必须先启动绑定；如果没有这行代码，函数永远不会触发收窄。
# 新增代码+AgentPySplitPhase2: 函数段结束，computer_use_full_initial_launch_required 到此结束；如果没有这个边界说明，用户不容易看出首轮收窄边界。


# 新增代码+AgentPySplitPhase2: 函数段开始，scoped_tool_schemas_for_model_turn 按当前轮次收窄模型可见工具；如果没有这段函数，模型首轮会继续在大工具面里超时。
def scoped_tool_schemas_for_model_turn(tools: list[dict[str, Any]], turn: int, desktop_task_context: Any, has_agent_owned_launch_target: HasAgentOwnedLaunchTarget) -> list[dict[str, Any]]:  # 新增代码+AgentPySplitPhase2: 定义工具 schema 收窄入口；如果没有这行代码，agent.py 无法把首轮工具范围规则迁到新模块。
    if not computer_use_full_initial_launch_required(turn, desktop_task_context, has_agent_owned_launch_target):  # 新增代码+AgentPySplitPhase2: 只有 full 本机应用任务首轮才收窄；如果没有这行代码，所有任务都会被错误过滤工具。
        return tools  # 新增代码+AgentPySplitPhase2: 不需要收窄时返回原工具池；如果没有这行代码，普通主循环无法继续。
    scoped_tools: list[dict[str, Any]] = []  # 新增代码+AgentPySplitPhase2: 准备保存首轮允许模型看到的工具；如果没有这行代码，后续无法构造过滤结果。
    for tool_schema in tools:  # 新增代码+AgentPySplitPhase2: 遍历当前工具池以保留发现和启动工具；如果没有这行代码，函数无法找到 mcp__computer-use__request_access/mcp__computer-use__open_application schema。
        function_schema = tool_schema.get("function", {}) if isinstance(tool_schema, dict) else {}  # 新增代码+AgentPySplitPhase2: 安全读取 function 层；如果没有这行代码，畸形 schema 会让过滤崩溃。
        tool_name = str(function_schema.get("name", "") or "").strip() if isinstance(function_schema, dict) else ""  # 新增代码+AgentPySplitPhase2: 读取工具名；如果没有这行代码，无法判断哪个 schema 是动作工具。
        if tool_name in {"mcp__computer-use__request_access", "mcp__computer-use__open_application"}:  # 新增代码+AgentPySplitPhase2: 首轮保留应用发现和启动动作入口；如果没有这行代码，模型无法先发现候选或启动目标应用。
            scoped_tools.append(tool_schema)  # 新增代码+AgentPySplitPhase2: 加入 discover/action schema；如果没有这行代码，模型首轮看不到必要的发现或启动工具。
    return scoped_tools or tools  # 新增代码+AgentPySplitPhase2: 有动作工具则返回收窄工具面，缺失时回退原工具池避免死路；如果没有这行代码，函数没有稳定返回。
# 新增代码+AgentPySplitPhase2: 函数段结束，scoped_tool_schemas_for_model_turn 到此结束；如果没有这个边界说明，用户不容易看出工具面收窄范围。
