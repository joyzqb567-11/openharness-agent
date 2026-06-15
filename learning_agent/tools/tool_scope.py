"""Computer Use 模式化工具池边界。"""  # 新增代码+ClaudeCodeToolSurface：说明本文件集中管理不同任务模式下哪些工具能被模型看到、搜索和执行；如果没有这行代码，读者很难知道工具隔离规则在哪里。
from __future__ import annotations  # 新增代码+ClaudeCodeToolSurface：延迟类型注解求值，避免脚本模式导入时因为类型顺序出错；如果没有这行代码，老版本运行方式可能在导入阶段失败。

from typing import Any  # 新增代码+ClaudeCodeToolSurface：引入 Any 以便本模块接收 duck-typing 的 agent 和工具对象；如果没有这行代码，模块会被迫反向导入主 Agent 类型。

try:  # 新增代码+ClaudeCodeToolSurface：优先按包路径导入工具策略类型；如果没有这行代码，python -m 运行时无法使用统一 ToolPolicyDecision。
    from learning_agent.tool_policy import ToolPolicyDecision  # 新增代码+ClaudeCodeToolSurface：导入策略决策对象用于返回可见、可选、可执行状态；如果没有这行代码，scope 层只能返回松散字典。
except ModuleNotFoundError as error:  # 新增代码+ClaudeCodeToolSurface：兼容 start_oauth_agent.bat 直接脚本运行路径；如果没有这行代码，脚本模式会因为包名前缀不同而启动失败。
    if error.name not in {"learning_agent", "learning_agent.tool_policy"}:  # 新增代码+ClaudeCodeToolSurface：只允许路径差异进入 fallback；如果没有这行代码，tool_policy 内部真实 bug 会被误吞。
        raise  # 新增代码+ClaudeCodeToolSurface：重新抛出非路径类导入错误；如果没有这行代码，真实错误会被伪装成兼容问题。
    from tool_policy import ToolPolicyDecision  # type: ignore  # 新增代码+ClaudeCodeToolSurface：脚本模式下导入同一个策略类型；如果没有这行代码，bat 入口无法执行工具池隔离。

TOOL_SCOPE_AUTO = "auto"  # 新增代码+ClaudeCodeToolSurface：声明自动模式，让 agent 可根据 desktop_task_context 自动选择工具池；如果没有这行代码，默认模式只能写死为代码开发。
TOOL_SCOPE_CODE_DEVELOPMENT = "code_development"  # 新增代码+ClaudeCodeToolSurface：声明普通代码开发模式；如果没有这行代码，read/write/edit 的默认边界没有稳定名称。
TOOL_SCOPE_COMPUTER_USE_OPERATION = "computer_use_operation"  # 新增代码+ClaudeCodeToolSurface：声明真实桌面操作模式；如果没有这行代码，Computer Use 原子工具无法集中放行。
TOOL_SCOPE_COMPUTER_USE_DEBUG = "computer_use_debug"  # 新增代码+ClaudeCodeToolSurface：声明 Computer Use 调试模式；如果没有这行代码，开发调试工具会和真实操作工具混在一起。
TOOL_SCOPE_COMPUTER_USE_SOURCE_DEVELOPMENT = "computer_use_source_development"  # 新增代码+ClaudeCodeToolSurface：声明开发 Computer Use 源码的模式；如果没有这行代码，修源码时容易误暴露真实鼠标键盘工具。
TOOL_SCOPE_MODES = {TOOL_SCOPE_AUTO, TOOL_SCOPE_CODE_DEVELOPMENT, TOOL_SCOPE_COMPUTER_USE_OPERATION, TOOL_SCOPE_COMPUTER_USE_DEBUG, TOOL_SCOPE_COMPUTER_USE_SOURCE_DEVELOPMENT}  # 新增代码+ClaudeCodeToolSurface：集中保存合法模式名；如果没有这行代码，拼错模式名会静默进入未知状态。
COMPUTER_USE_MCP_SERVER_NAME = "computer-use"  # 新增代码+ClaudeCodeToolSurface：固定独立 Computer Use MCP server 名；如果没有这行代码，前缀判断会散落在多个模块。
COMPUTER_USE_MCP_PREFIX = f"mcp__{COMPUTER_USE_MCP_SERVER_NAME}__"  # 新增代码+ClaudeCodeToolSurface：固定模型侧看到的 MCP 工具名前缀；如果没有这行代码，工具名解析容易把连字符 server 写错。
TOP_LEVEL_CODE_TOOL_NAMES = {"read", "write", "edit"}  # 新增代码+ClaudeCodeToolSurface：列出普通代码开发模式允许首轮保留的文件原子工具；如果没有这行代码，文件工具边界会和其他模式混淆。
TOP_LEVEL_FILE_AND_SHELL_TOOL_NAMES = {"read", "write", "edit", "bash", "read_file", "write_file", "append_memory", "start_background_command", "read_background_command", "stop_background_command"}  # 新增代码+ClaudeCodeToolSurface：列出 Computer Use 模式必须隐藏和拦截的通用文件或命令工具；如果没有这行代码，bash 或文件写入仍可能抢走桌面任务。
COMPUTER_USE_OPERATION_RAW_TOOL_NAMES = {"request_access", "screenshot", "observe", "cursor_position", "mouse_move", "left_click", "double_click", "right_click", "middle_click", "triple_click", "left_mouse_down", "left_mouse_up", "type", "key", "hold_key", "scroll", "left_click_drag", "zoom", "wait", "read_clipboard", "write_clipboard", "open_application", "list_granted_applications", "computer_batch"}  # 修改代码+ClaudeCodeParity：列出 operation/debug 模式应暴露的 24 个 ClaudeCode parity Computer Use 工具；如果没有这一行，zoom/hold_key/left_click_drag 等公开 MCP 工具会继续被 scope 隐藏。
COMPUTER_USE_DEBUG_BUILTIN_TOOL_NAMES = {"read_trace", "read_state", "read_last_observation", "read_last_action_result", "assert_last_action"}  # 新增代码+ClaudeCodeToolSurface：列出只在调试模式暴露的内置诊断工具；如果没有这行代码，调试能力会污染普通操作模式。
COMPUTER_USE_LEGACY_RAW_TOOL_NAMES = {"click", "clipboard"}  # 新增代码+ClaudeCodeToolSurface：列出保留兼容但不在新模型工具面暴露的旧 MCP 名；如果没有这行代码，left_click 和 click 会同轮混用。
COMPUTER_USE_RESERVED_RAW_TOOL_NAMES = set()  # 修改代码+ClaudeCodeParity：ClaudeCode parity 已要求原预留鼠标工具公开，因此保留空集合兼容旧判断；如果没有这一行，middle_click/triple_click/left_mouse_down/left_mouse_up 会继续被 scope 拦截。
COMPUTER_USE_COMPAT_BUILTIN_TOOL_NAMES = {"computer_status", "computer_observe", "computer_discover", "computer_action", "computer_use", "computer-use", "request_access"}  # 新增代码+ClaudeCodeToolSurface：列出旧内置 Computer Use 兼容入口；如果没有这行代码，旧工具可能和独立 MCP 工具同轮竞争。


# 新增代码+ClaudeCodeToolSurface：函数段开始，computer_use_mcp_tool_name 把原始 MCP 工具名变成模型侧工具名；如果没有这段函数，多处代码会重复拼接前缀并容易写错。
def computer_use_mcp_tool_name(raw_name: str) -> str:  # 新增代码+ClaudeCodeToolSurface：定义前缀工具名生成入口；如果没有这行代码，测试和实现无法复用同一命名规则。
    return f"{COMPUTER_USE_MCP_PREFIX}{raw_name}"  # 新增代码+ClaudeCodeToolSurface：返回 mcp__computer-use__xxx 格式；如果没有这行代码，OpenHarness 的 MCP 路由名会和 registry 不一致。
# 新增代码+ClaudeCodeToolSurface：函数段结束，computer_use_mcp_tool_name 到此结束；如果没有这个边界说明，用户不容易看出命名 helper 范围。


# 新增代码+ClaudeCodeToolSurface：函数段开始，normalize_tool_scope_mode 规整外部传入的工具模式名；如果没有这段函数，大小写或空值会导致模式判断漂移。
def normalize_tool_scope_mode(raw_mode: Any) -> str:  # 新增代码+ClaudeCodeToolSurface：声明模式规整入口；如果没有这行代码，调用方必须自己处理 None 和空字符串。
    mode = str(raw_mode or TOOL_SCOPE_AUTO).strip().lower()  # 新增代码+ClaudeCodeToolSurface：把传入模式转成小写非空字符串；如果没有这行代码，" Computer_Use_Operation " 这类输入会失效。
    return mode if mode in TOOL_SCOPE_MODES else TOOL_SCOPE_AUTO  # 新增代码+ClaudeCodeToolSurface：未知模式回退 auto；如果没有这行代码，拼错模式名可能意外放开工具。
# 新增代码+ClaudeCodeToolSurface：函数段结束，normalize_tool_scope_mode 到此结束；如果没有这个边界说明，用户不容易看出容错范围。


# 新增代码+ClaudeCodeToolSurface：函数段开始，tool_scope_mode_from_agent 根据显式配置或桌面上下文选择当前模式；如果没有这段函数，每个模块会各自猜当前是不是 Computer Use。
def tool_scope_mode_from_agent(agent: Any) -> str:  # 新增代码+ClaudeCodeToolSurface：定义 agent 当前工具模式读取入口；如果没有这行代码，catalog、search、executor 无法使用同一模式判断。
    explicit_mode = normalize_tool_scope_mode(getattr(agent, "tool_scope_mode", TOOL_SCOPE_AUTO))  # 新增代码+ClaudeCodeToolSurface：优先读取 agent 显式模式；如果没有这行代码，测试和调试无法强制切换工具面。
    if explicit_mode != TOOL_SCOPE_AUTO:  # 新增代码+ClaudeCodeToolSurface：显式模式优先于自动推断；如果没有这行代码，debug/source 模式会被 desktop_task_context 覆盖。
        return explicit_mode  # 新增代码+ClaudeCodeToolSurface：返回显式模式；如果没有这行代码，调用方拿不到用户或测试指定的模式。
    desktop_context = getattr(agent, "desktop_task_context", {})  # 新增代码+ClaudeCodeToolSurface：读取桌面任务上下文；如果没有这行代码，自然语言桌面任务无法自动切换到 Computer Use 操作模式。
    if isinstance(desktop_context, dict) and bool(desktop_context.get("active", False)) and bool(desktop_context.get("requires_gui_actions", False)):  # 新增代码+ClaudeCodeToolSurface：只有真实 GUI 动作任务才自动进入操作模式；如果没有这行代码，普通代码任务可能误隐藏 read/write/edit。
        return TOOL_SCOPE_COMPUTER_USE_DEBUG if bool(desktop_context.get("debug_tools", False)) else TOOL_SCOPE_COMPUTER_USE_OPERATION  # 新增代码+ClaudeCodeToolSurface：debug 标志进入调试模式，否则进入操作模式；如果没有这行代码，调试工具无法由上下文启用。
    return TOOL_SCOPE_CODE_DEVELOPMENT  # 新增代码+ClaudeCodeToolSurface：默认回到普通代码开发模式；如果没有这行代码，空上下文会导致工具池模式不确定。
# 新增代码+ClaudeCodeToolSurface：函数段结束，tool_scope_mode_from_agent 到此结束；如果没有这个边界说明，用户不容易看出模式选择顺序。


# 新增代码+ClaudeCodeToolSurface：函数段开始，computer_use_raw_name_from_agent_tool 从 AgentTool 中提取 Computer Use 原始工具名；如果没有这段函数，scope 层无法同时兼容前缀名和原始名。
def computer_use_raw_name_from_agent_tool(tool: Any) -> str:  # 新增代码+ClaudeCodeToolSurface：定义工具原始名读取入口；如果没有这行代码，MCP 和内置兼容工具要写两套判断。
    tool_name = str(getattr(tool, "name", "") or "")  # 新增代码+ClaudeCodeToolSurface：读取模型侧工具名；如果没有这行代码，后续前缀判断没有输入。
    server_name = str(getattr(tool, "server_name", "") or "")  # 新增代码+ClaudeCodeToolSurface：读取 MCP server 名；如果没有这行代码，无法识别从 registry 包装来的 Computer Use 工具。
    original_name = str(getattr(tool, "original_name", "") or "")  # 新增代码+ClaudeCodeToolSurface：读取 MCP 原始工具名；如果没有这行代码，前缀工具无法还原为 left_click 等原子名。
    if tool_name.startswith(COMPUTER_USE_MCP_PREFIX):  # 新增代码+ClaudeCodeToolSurface：优先按模型侧前缀解析；如果没有这行代码，mcp__computer-use__left_click 会被当成普通工具。
        return tool_name.removeprefix(COMPUTER_USE_MCP_PREFIX)  # 新增代码+ClaudeCodeToolSurface：返回去掉前缀的原始名；如果没有这行代码，允许列表无法命中。
    if server_name == COMPUTER_USE_MCP_SERVER_NAME and original_name:  # 新增代码+ClaudeCodeToolSurface：兼容 AgentTool 元数据保存了 server/original 的情况；如果没有这行代码，后续 registry 格式变化会影响 scope 判断。
        return original_name  # 新增代码+ClaudeCodeToolSurface：返回 registry 记录的原始工具名；如果没有这行代码，MCP 工具会被误判为非 Computer Use。
    if tool_name in COMPUTER_USE_COMPAT_BUILTIN_TOOL_NAMES:  # 新增代码+ClaudeCodeToolSurface：识别旧内置兼容工具；如果没有这行代码，computer_action 可能绕过新工具面隔离。
        return tool_name  # 新增代码+ClaudeCodeToolSurface：兼容工具用自身名称作为原始名；如果没有这行代码，旧工具无法被集中隐藏。
    return ""  # 新增代码+ClaudeCodeToolSurface：非 Computer Use 工具返回空字符串；如果没有这行代码，调用方无法区分未命中。
# 新增代码+ClaudeCodeToolSurface：函数段结束，computer_use_raw_name_from_agent_tool 到此结束；如果没有这个边界说明，用户不容易看出原始名解析范围。


# 新增代码+ClaudeCodeToolSurface：函数段开始，is_computer_use_agent_tool 判断 AgentTool 是否属于 Computer Use；如果没有这段函数，多个模块会重复写前缀判断。
def is_computer_use_agent_tool(tool: Any) -> bool:  # 新增代码+ClaudeCodeToolSurface：定义 Computer Use 工具判断入口；如果没有这行代码，scope 策略会变得分散。
    return bool(computer_use_raw_name_from_agent_tool(tool))  # 新增代码+ClaudeCodeToolSurface：只要能提取原始名就认为属于 Computer Use；如果没有这行代码，MCP 与兼容入口无法统一。
# 新增代码+ClaudeCodeToolSurface：函数段结束，is_computer_use_agent_tool 到此结束；如果没有这个边界说明，用户不容易看出归属判断范围。


# 新增代码+ClaudeCodeToolSurface：函数段开始，is_computer_use_tool_call_name 判断裸工具调用名是否属于 Computer Use；如果没有这段函数，执行层无法拦截模型伪造的隐藏工具名。
def is_computer_use_tool_call_name(tool_name: str) -> bool:  # 新增代码+ClaudeCodeToolSurface：定义工具调用名判断入口；如果没有这行代码，executor 只能依赖 catalog 是否查得到工具。
    name = str(tool_name or "").strip()  # 新增代码+ClaudeCodeToolSurface：清理工具名；如果没有这行代码，前后空格会影响安全判断。
    return name.startswith(COMPUTER_USE_MCP_PREFIX) or name in COMPUTER_USE_COMPAT_BUILTIN_TOOL_NAMES  # 新增代码+ClaudeCodeToolSurface：识别 MCP 前缀和旧兼容名；如果没有这行代码，隐藏 Computer Use 工具仍可能被直接调用。
# 新增代码+ClaudeCodeToolSurface：函数段结束，is_computer_use_tool_call_name 到此结束；如果没有这个边界说明，用户不容易看出裸名判断范围。


# 新增代码+ClaudeCodeToolSurface：函数段开始，_operation_mode_allows_raw_tool 判断某个原始 Computer Use 工具是否属于本模式；如果没有这段函数，操作模式和调试模式会重复维护名单。
def _operation_mode_allows_raw_tool(mode: str, raw_name: str) -> bool:  # 新增代码+ClaudeCodeToolSurface：定义原始工具模式白名单入口；如果没有这行代码，left_click/click 去重规则会散落。
    if raw_name in COMPUTER_USE_LEGACY_RAW_TOOL_NAMES:  # 新增代码+ClaudeCodeToolSurface：旧 click/clipboard 在新表面不直接暴露；如果没有这行代码，模型会同轮看到 left_click 和 click 两种写法。
        return False  # 新增代码+ClaudeCodeToolSurface：明确拒绝旧兼容名进入模型工具池；如果没有这行代码，同名混用风险会回归。
    if raw_name in COMPUTER_USE_RESERVED_RAW_TOOL_NAMES:  # 新增代码+ClaudeCodeToolSurface：预留工具默认不进入首选操作面；如果没有这行代码，未成熟工具会抢占常规鼠标动作。
        return False  # 新增代码+ClaudeCodeToolSurface：保留可执行预留实现但不自动暴露；如果没有这行代码，模型可能把 reserved 工具当作首选。
    return raw_name in COMPUTER_USE_OPERATION_RAW_TOOL_NAMES and mode in {TOOL_SCOPE_COMPUTER_USE_OPERATION, TOOL_SCOPE_COMPUTER_USE_DEBUG}  # 新增代码+ClaudeCodeToolSurface：操作和调试模式共享 ClaudeCode 风格原子工具；如果没有这行代码，debug 模式无法测试真实操作工具。
# 新增代码+ClaudeCodeToolSurface：函数段结束，_operation_mode_allows_raw_tool 到此结束；如果没有这个边界说明，用户不容易看出模式白名单范围。


# 新增代码+ClaudeCodeToolSurface：函数段开始，tool_scope_forces_visible_agent_tool 判断 scope 是否应绕过 deferred 把工具放入当前池；如果没有这段函数，Computer Use 操作模式仍需要模型先 select 每个动作工具。
def tool_scope_forces_visible_agent_tool(agent: Any, tool: Any) -> bool:  # 新增代码+ClaudeCodeToolSurface：定义 scope 强制可见判断入口；如果没有这行代码，catalog_runtime 无法让操作模式直接暴露动作工具。
    mode = tool_scope_mode_from_agent(agent)  # 新增代码+ClaudeCodeToolSurface：读取当前模式；如果没有这行代码，强制可见不会随任务类型变化。
    tool_name = str(getattr(tool, "name", "") or "")  # 修改代码+ClaudeCodeToolSurface：读取模型侧工具名以识别旧顶层兼容入口；如果没有这一行，request_access 这类旧内置入口会和 MCP 前缀入口同轮暴露。
    if tool_name in COMPUTER_USE_COMPAT_BUILTIN_TOOL_NAMES:  # 修改代码+ClaudeCodeToolSurface：旧内置兼容入口不参与操作模式自动加载；如果没有这一行，模型会同时看到 request_access 和 mcp__computer-use__request_access。
        return False  # 修改代码+ClaudeCodeToolSurface：让旧兼容入口留给 policy 层隐藏；如果没有这一行，同义工具去重规则会失效。
    raw_name = computer_use_raw_name_from_agent_tool(tool)  # 新增代码+ClaudeCodeToolSurface：提取 Computer Use 原始名；如果没有这行代码，无法匹配操作工具白名单。
    return bool(raw_name) and _operation_mode_allows_raw_tool(mode, raw_name)  # 新增代码+ClaudeCodeToolSurface：只在操作或调试模式强制加载允许的原子工具；如果没有这行代码，deferred 规则仍会隐藏真实动作工具。
# 新增代码+ClaudeCodeToolSurface：函数段结束，tool_scope_forces_visible_agent_tool 到此结束；如果没有这个边界说明，用户不容易看出自动加载边界。


# 新增代码+ClaudeCodeToolSurface：函数段开始，tool_scope_policy_decision 在原有 ToolPolicy 结果上叠加模式隔离；如果没有这段函数，工具池过滤只能靠提示词提醒模型。
def tool_scope_policy_decision(agent: Any, tool: Any, base_decision: ToolPolicyDecision) -> ToolPolicyDecision:  # 新增代码+ClaudeCodeToolSurface：定义 scope 策略入口；如果没有这行代码，catalog、search、executor 无法复用同一隔离规则。
    mode = tool_scope_mode_from_agent(agent)  # 新增代码+ClaudeCodeToolSurface：读取当前工具模式；如果没有这行代码，后续判断不知道该按代码开发还是桌面操作过滤。
    tool_name = str(getattr(tool, "name", "") or "")  # 新增代码+ClaudeCodeToolSurface：读取模型侧工具名；如果没有这行代码，无法识别 read/bash/debug 等内置工具。
    raw_name = computer_use_raw_name_from_agent_tool(tool)  # 新增代码+ClaudeCodeToolSurface：读取 Computer Use 原始工具名；如果没有这行代码，MCP 工具无法按 ClaudeCode 表面过滤。
    if mode in {TOOL_SCOPE_CODE_DEVELOPMENT, TOOL_SCOPE_COMPUTER_USE_SOURCE_DEVELOPMENT}:  # 新增代码+ClaudeCodeToolSurface：普通开发和 Computer Use 源码开发都不应暴露真实桌面动作；如果没有这行代码，开发源码时可能误点真实鼠标。
        if raw_name:  # 新增代码+ClaudeCodeToolSurface：发现 Computer Use 工具时进入阻断；如果没有这行代码，mcp__computer-use__left_click 可能在代码模式可选可执行。
            return ToolPolicyDecision(state="scope_blocked", visible=False, selectable=False, executable=False, reason=f"tool scope {mode} hides Computer Use desktop tools")  # 新增代码+ClaudeCodeToolSurface：返回不可见不可选不可执行；如果没有这行代码，隐藏只会发生在展示层。
        if tool_name in COMPUTER_USE_DEBUG_BUILTIN_TOOL_NAMES:  # 修改代码+ClaudeCodeToolSurface：代码开发和源码开发模式也隐藏 Computer Use 调试工具；如果没有这一行，read_trace/read_state 会因为被加入内核工具而泄露到普通代码轮次。
            return ToolPolicyDecision(state="scope_blocked", visible=False, selectable=False, executable=False, reason=f"tool scope {mode} hides Computer Use debug tools")  # 修改代码+ClaudeCodeToolSurface：执行层同步拒绝调试工具；如果没有这一行，模型可以绕过工具池直接调用 debug 工具读取桌面运行状态。
        if tool_name == "bash":  # 新增代码+ClaudeCodeToolSurface：bash 在代码模式也不作为默认可执行工具面；如果没有这行代码，模型可能继续用 bash 抢走 Computer Use 或文件任务。
            return ToolPolicyDecision(state="scope_blocked", visible=False, selectable=False, executable=False, reason=f"tool scope {mode} hides bash by default")  # 新增代码+ClaudeCodeToolSurface：执行期也拒绝 bash；如果没有这行代码，隐藏的 bash 仍可能被直接调用。
        return base_decision  # 新增代码+ClaudeCodeToolSurface：其他代码工具沿用原有策略；如果没有这行代码，LSP、task 等非目标工具可能被误拦。
    if mode in {TOOL_SCOPE_COMPUTER_USE_OPERATION, TOOL_SCOPE_COMPUTER_USE_DEBUG}:  # 新增代码+ClaudeCodeToolSurface：进入 Computer Use 操作或调试工具池；如果没有这行代码，桌面模式不会隐藏文件工具。
        if tool_name in TOP_LEVEL_FILE_AND_SHELL_TOOL_NAMES:  # 新增代码+ClaudeCodeToolSurface：文件和命令工具在桌面模式必须隐藏；如果没有这行代码，read/write/edit/bash 仍可能抢任务。
            return ToolPolicyDecision(state="scope_blocked", visible=False, selectable=False, executable=False, reason=f"tool scope {mode} hides top-level file/shell tool {tool_name}")  # 新增代码+ClaudeCodeToolSurface：执行期硬拒绝通用文件/命令工具；如果没有这行代码，模型可伪造隐藏工具名。
        if tool_name in COMPUTER_USE_DEBUG_BUILTIN_TOOL_NAMES:  # 新增代码+ClaudeCodeToolSurface：识别 Computer Use 调试内置工具；如果没有这行代码，read_trace/read_state 无法按模式单独控制。
            if mode != TOOL_SCOPE_COMPUTER_USE_DEBUG:  # 新增代码+ClaudeCodeToolSurface：非 debug 模式不暴露诊断工具；如果没有这行代码，普通操作模式会看到调试噪声。
                return ToolPolicyDecision(state="scope_blocked", visible=False, selectable=False, executable=False, reason="debug tool is only available in computer_use_debug mode")  # 新增代码+ClaudeCodeToolSurface：拒绝非 debug 调试工具；如果没有这行代码，隐藏层和执行层会不一致。
            return ToolPolicyDecision(state="loaded", visible=True, selectable=True, executable=True, reason="debug tool is enabled by computer_use_debug scope")  # 新增代码+ClaudeCodeToolSurface：debug 模式强制暴露诊断入口；如果没有这行代码，调试工具可能因为 deferred 仍不可见。
        if raw_name:  # 新增代码+ClaudeCodeToolSurface：Computer Use MCP 或兼容工具进入新表面判断；如果没有这行代码，旧兼容工具不会被隔离。
            if tool_name in COMPUTER_USE_COMPAT_BUILTIN_TOOL_NAMES:  # 修改代码+ClaudeCodeToolSurface：操作/debug 模式隐藏旧顶层兼容入口，只保留独立 MCP 工具名；如果没有这一行，同轮会暴露 request_access 与 mcp__computer-use__request_access 等同义入口。
                return ToolPolicyDecision(state="scope_blocked", visible=False, selectable=False, executable=False, reason=f"tool scope {mode} hides legacy Computer Use builtin {tool_name}")  # 修改代码+ClaudeCodeToolSurface：返回结构化 scope 拒绝；如果没有这一行，执行层仍可能调用旧兼容入口绕过 MCP 表面。
            if _operation_mode_allows_raw_tool(mode, raw_name):  # 新增代码+ClaudeCodeToolSurface：只允许蓝图声明的 ClaudeCode 风格工具；如果没有这行代码，click/clipboard 或 reserved 工具会混进来。
                if base_decision.state == "deferred":  # 新增代码+ClaudeCodeToolSurface：操作模式下允许自动加载原子工具；如果没有这行代码，模型还得先 tool_search select 才能点鼠标。
                    return ToolPolicyDecision(state="loaded", visible=True, selectable=True, executable=True, reason=f"tool scope {mode} auto-loads Computer Use tool")  # 新增代码+ClaudeCodeToolSurface：把 deferred 转为当前可见可执行；如果没有这行代码，操作工具仍会被 executor 拦为未加载。
                return base_decision  # 新增代码+ClaudeCodeToolSurface：原本已 loaded/always_load 的工具保持原策略；如果没有这行代码，只读入口的元数据可能丢失。
            return ToolPolicyDecision(state="scope_blocked", visible=False, selectable=False, executable=False, reason=f"tool scope {mode} hides Computer Use tool {raw_name}")  # 新增代码+ClaudeCodeToolSurface：拒绝旧名、预留名和兼容入口；如果没有这行代码，同轮混名会回归。
        return ToolPolicyDecision(state="scope_blocked", visible=False, selectable=False, executable=False, reason=f"tool scope {mode} only exposes Computer Use tools")  # 新增代码+ClaudeCodeToolSurface：桌面模式默认隐藏其他非 Computer Use 工具；如果没有这行代码，之前加载过的通用工具会残留进桌面轮次。
    return base_decision  # 新增代码+ClaudeCodeToolSurface：未知模式兜底沿用原策略；如果没有这行代码，函数可能隐式返回 None。
# 新增代码+ClaudeCodeToolSurface：函数段结束，tool_scope_policy_decision 到此结束；如果没有这个边界说明，用户不容易看出工具隔离主逻辑范围。
