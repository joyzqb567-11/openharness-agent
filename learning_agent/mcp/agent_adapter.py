"""LearningAgent 与 MCP registry/client 之间的适配层。"""  # 新增代码+AgentPySplitPhase9: 说明本模块负责把 agent 的 MCP 工具入口委托给 MCP 层；若没有这行代码，用户不容易知道 MCP 适配逻辑已经从 agent.py 拆出。
from __future__ import annotations  # 新增代码+AgentPySplitPhase9: 延迟解析类型注解；若没有这行代码，类型引用在部分导入顺序下可能提前求值。

import copy  # 新增代码+AgentPySplitPhase9: 用于保存 MCP 参数快照；若没有这行代码，后续参数被修改时会污染历史进度记录。
import json  # 新增代码+AgentPySplitPhase9: 用于格式化权限提示里的参数 JSON；若没有这行代码，用户无法清楚核对 MCP 工具参数。
import time  # 新增代码+AgentPySplitPhase9: 用于记录 MCP call progress 时间；若没有这行代码，用户无法判断进度事件先后。
from typing import Any  # 新增代码+AgentPySplitPhase9: 用于标注 agent duck type 和通用 payload；若没有这行代码，函数签名无法表达这里依赖动态对象。

try:  # 新增代码+AgentPySplitPhase9: 优先按正式包路径导入 ToolCall；若没有这行代码，包运行模式下类型入口不稳定。
    from learning_agent.core import run_helpers as run_helpers_from_core  # 修改代码+AgentPySplitPhase15B2: 导入 core observation helper；若没有这行代码，删除 agent.py `旧观察薄包装` 后 MCP 进度无法写入通用观察流。
    from learning_agent.core.messages import ToolCall  # 新增代码+AgentPySplitPhase9: 导入工具调用对象；若没有这行代码，适配层无法构造清洗后的安全 ToolCall。
    import learning_agent.browser.agent_workflow as browser_agent_workflow_from_browser  # 修改代码+AgentPyCompatWrapperRemovalL7: MCP 适配层直接导入浏览器 workflow；若没有这行代码，删除 agent.py 浏览器权限薄包装后自动授权和状态推进会断开。
    import learning_agent.tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 导入工具目录和策略运行时；若没有这行代码，MCP 适配层仍会通过 agent.py 薄包装取拒绝 key 和 catalog 元数据。
    import learning_agent.tools.search as search_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL2: 直接导入工具搜索 helper；若没有这行代码，MCP resource/prompt 数量限制还要绕回 agent.py 旧包装。
except ModuleNotFoundError as error:  # 新增代码+AgentPySplitPhase9: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能因包路径不同失败。
    if error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.agent_workflow", "learning_agent.core", "learning_agent.core.messages", "learning_agent.core.run_helpers", "learning_agent.tools", "learning_agent.tools.catalog_runtime", "learning_agent.tools.search"}:  # 修改代码+AgentPyCompatWrapperRemovalL7: 允许 browser workflow 路径差异进入脚本 fallback；若没有这行代码，bat 入口可能误报导入失败。
        raise  # 新增代码+AgentPySplitPhase9: 重新抛出非路径问题；若没有这行代码，真实导入错误会被伪装成脚本模式问题。
    from core import run_helpers as run_helpers_from_core  # 修改代码+AgentPySplitPhase15B2: 脚本模式下导入 core observation helper；若没有这行代码，start_oauth_agent.bat 的 MCP 进度记录会找不到 helper。
    from core.messages import ToolCall  # 新增代码+AgentPySplitPhase9: 脚本模式下从同目录 core 包导入 ToolCall；若没有这行代码，bat 入口无法复用 MCP 适配层。
    import browser.agent_workflow as browser_agent_workflow_from_browser  # 修改代码+AgentPyCompatWrapperRemovalL7: 脚本模式下直接导入浏览器 workflow；若没有这行代码，start_oauth_agent.bat 删除旧薄包装后 MCP 浏览器流程会断开。
    import tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下导入工具目录和策略运行时；若没有这行代码，bat 入口 MCP 适配层 catalog 查询会断开。
    import tools.search as search_tools_from_tools  # 修改代码+AgentPyCompatWrapperRemovalL2: 脚本模式下导入工具搜索 helper；若没有这行代码，直接运行时 MCP 列表工具仍会依赖 agent.py 旧包装。

try:  # 修改代码+AgentPySplitPhase15B2: 包运行模式下导入不依赖 agent.py 的 max_chars 解析函数；若没有这行代码，MCP resource/prompt 读取仍会反向依赖 agent.旧输出长度薄包装。
    from learning_agent.runtime.background_commands import parse_max_chars_value  # 修改代码+AgentPySplitPhase15B2: 复用 runtime 层公共截断规则；若没有这行代码，MCP 长文本截断会继续分散在 agent.py。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase15B2: 兼容 start_oauth_agent.bat 直接运行时没有 learning_agent 包名前缀；若没有这行代码，脚本模式下 MCP 适配层可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.background_commands"}:  # 修改代码+AgentPySplitPhase15B2: 只允许路径模式差异进入 fallback；若没有这行代码，runtime 模块内部真实错误会被误吞。
        raise  # 修改代码+AgentPySplitPhase15B2: 非路径问题必须暴露出来；若没有这行代码，真实导入 bug 会被隐藏成脚本兼容问题。
    from runtime.background_commands import parse_max_chars_value  # 修改代码+AgentPySplitPhase15B2: 脚本模式下导入同一个公共截断函数；若没有这行代码，bat 入口读取 MCP 长文本会找不到解析函数。

try:  # 修改代码+ComputerUseMcpV2：优先按包路径导入 v2 agent-side wrapper；如果没有这一段，mcp__computer-use__ 工具会继续走旧 session adapter。
    from learning_agent.computer_use_mcp_v2.claudecode_bridge.wrapper import execute_agent_side_tool as computer_use_mcp_v2_execute_agent_side_tool  # 修改代码+ClaudeCodeWrapperParity：导入 v2 agent 侧 wrapper 执行入口；如果没有这一行，agent 主循环无法把 MCP 工具接到 ClaudeCode-style wrapper。
except ModuleNotFoundError as error:  # 修改代码+ComputerUseMcpV2：兼容 start_oauth_agent.bat 直接脚本模式；如果没有这一行，脚本入口路径不同时会启动失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2", "learning_agent.computer_use_mcp_v2.claudecode_bridge", "learning_agent.computer_use_mcp_v2.claudecode_bridge.wrapper"}:  # 修改代码+ComputerUseMcpV2：只允许包路径差异走 fallback；如果没有这一行，v2 内部真实导入错误会被误吞。
        raise  # 修改代码+ComputerUseMcpV2：重新抛出真实导入错误；如果没有这一行，排查 v2 wrapper bug 会变得很困难。
    from computer_use_mcp_v2.claudecode_bridge.wrapper import execute_agent_side_tool as computer_use_mcp_v2_execute_agent_side_tool  # type: ignore  # 修改代码+ClaudeCodeWrapperParity：脚本模式导入 v2 agent 侧 wrapper 执行入口；如果没有这一行，bat 启动时 Computer Use MCP v2 不能执行。


def mcp_tool_risk_summary(tool_call: ToolCall) -> tuple[str, str]:  # 新增代码+AgentPySplitPhase9: 函数段开始，根据 MCP 工具名生成授权风险摘要；若没有这段函数，用户只能看到模糊外部调用而无法区分风险等级。
    tool_name = tool_call.name.lower()  # 新增代码+AgentPySplitPhase9: 统一转小写方便匹配工具类别；若没有这行代码，大小写变化可能导致风险分类漏判。
    if tool_name.endswith("__authenticate") or tool_name.endswith("authenticate"):  # 新增代码+AgentPySplitPhase9: 识别 MCP 鉴权说明伪工具；若没有这行代码，登录入口会被归类成普通外部调用。
        return ("鉴权说明/低风险", "只展示 WWW-Authenticate、resource_metadata 和 Authorization: Bearer 配置提示；不要在参数里填写 access token。")  # 新增代码+AgentPySplitPhase9: 返回保守且明确的鉴权风险说明；若没有这行代码，用户可能误以为工具会自动登录或收集令牌。
    if tool_name.endswith("__delete_file") or tool_name.endswith("delete_file"):  # 新增代码+AgentPySplitPhase9: 优先识别删除文件工具；若没有这行代码，删除操作可能被误归为普通写入或外部调用。
        return ("删除/破坏性操作", "会删除工作区文件；确认前请重点核对 path 和 confirm_delete。")  # 新增代码+AgentPySplitPhase9: 返回删除风险说明；若没有这行代码，用户看不到删除操作最需要核对的参数。
    if tool_name.endswith("__run_powershell") or "powershell" in tool_name or "shell" in tool_name or "command" in tool_name:  # 新增代码+AgentPySplitPhase9: 识别命令执行类工具；若没有这行代码，运行命令可能只显示普通外部工具提示。
        return ("命令执行", "会在本机或工作区执行命令；确认前请重点核对 command、cwd 和命令副作用。")  # 新增代码+AgentPySplitPhase9: 返回命令执行风险说明；若没有这行代码，用户缺少判断命令副作用的提醒。
    if tool_name.endswith("__write_file") or tool_name.endswith("__create_file") or tool_name.endswith("__edit_file") or tool_name.endswith("__copy_file") or tool_name.endswith("__move_file"):  # 新增代码+AgentPySplitPhase9: 识别写入、创建、编辑、复制和移动文件工具；若没有这行代码，文件变更可能被当成只读操作。
        return ("写入/文件变更", "会修改工作区文件；确认前请重点核对路径、覆盖参数和内容差异。")  # 新增代码+AgentPySplitPhase9: 返回文件变更风险说明；若没有这行代码，用户缺少检查文件副作用的提示。
    if "browser_automation" in tool_name and tool_name.endswith("__browser_connect_real_chrome"):  # 新增代码+AgentPySplitPhase9: 在通用浏览器自动化分类前识别真实 Chrome 连接工具；若没有这行代码，日常 profile 连接会被误标成低风险浏览器状态。
        return ("真实 Chrome 高风险", "会连接日常 Chrome profile 并接触真实登录态；确认前请重点核对 confirm_real_profile、chrome_path、user_data_dir、profile_directory、debug_port。")  # 新增代码+AgentPySplitPhase9: 明确真实 profile 和登录态风险以及关键确认参数；若没有这行代码，用户可能不知道该工具不同于独立 Chromium。
    if "browser_automation" in tool_name and tool_name.endswith("__browser_disconnect_real_chrome"):  # 新增代码+AgentPySplitPhase9: 在通用浏览器自动化分类前识别真实 Chrome 断开工具；若没有这行代码，断开 CDP 连接会被误归为只读状态。
        return ("真实 Chrome 中风险", "会断开真实 Chrome CDP 连接；默认不关闭用户 Chrome，确认前请重点核对 close_browser。")  # 新增代码+AgentPySplitPhase9: 说明默认不关闭日常 Chrome 并提示核对 close_browser；若没有这行代码，用户可能误以为断开一定会关闭浏览器或不会改变连接状态。
    if "browser_automation" in tool_name and tool_name.endswith("__browser_profile_status"):  # 新增代码+AgentPySplitPhase9: 在通用浏览器自动化分类前识别 profile 状态工具；若没有这行代码，只读隐私边界会被普通状态说明稀释。
        return ("只读/低风险浏览器状态", "只读当前浏览器会话模式、页面数量和最近安全拒绝；不读取 cookies、storage、token 或密码。")  # 新增代码+AgentPySplitPhase9: 明确 status 只读范围和敏感数据不读取边界；若没有这行代码，用户可能担心状态工具读取登录态明细。
    if "browser_automation" in tool_name and tool_name.endswith("__browser_evaluate"):  # 新增代码+AgentPySplitPhase9: 优先识别页面 JavaScript 执行工具；若没有这行代码，browser_evaluate 会被误归类为普通外部工具或联网工具。
        return ("浏览器自动化高风险", "会在网页里执行 JavaScript；确认前请重点核对 script，避免读取 cookie、localStorage、sessionStorage、token、密码框等敏感信息。")  # 新增代码+AgentPySplitPhase9: 明确脚本执行和敏感信息边界；若没有这行代码，用户可能不知道 evaluate 能读取页面内敏感状态。
    if "browser_automation" in tool_name and tool_name.endswith("__browser_downloads"):  # 新增代码+AgentPySplitPhase9: 单独识别下载记录读取工具；若没有这行代码，browser_downloads 会被误描述成主动下载文件。
        return ("浏览器自动化高风险", "会查看浏览器下载记录，本工具本身不主动触发下载；触发下载通常由 browser_click 等页面操作导致，确认前请重点核对 max_results、文件路径和 URL 记录范围。")  # 新增代码+AgentPySplitPhase9: 区分查看下载记录和触发下载动作；若没有这行代码，用户会误解 browser_downloads 的真实副作用。
    if "browser_automation" in tool_name and (tool_name.endswith("__browser_click") or tool_name.endswith("__browser_type") or tool_name.endswith("__browser_press_key") or tool_name.endswith("__browser_upload_file") or tool_name.endswith("__browser_close")):  # 新增代码+AgentPySplitPhase9: 识别会点击、输入、按键、上传或关闭浏览器的工具；若没有这行代码，这些高副作用操作会缺少醒目提醒。
        return ("浏览器自动化高风险", "会操作网页、输入文本、按键、上传文件、关闭页面或浏览器；确认前请重点核对 selector、文本、文件路径、URL。")  # 新增代码+AgentPySplitPhase9: 返回高风险浏览器操作说明且不把 downloads 说成主动下载；若没有这行代码，用户可能没核对目标元素、文本、路径或网址就授权。
    if "browser_automation" in tool_name and (tool_name.endswith("__browser_open") or tool_name.endswith("__browser_wait") or tool_name.endswith("__browser_screenshot") or tool_name.endswith("__browser_launch_visible")):  # 新增代码+AgentPySplitPhase9: 把弹出可见浏览器窗口识别为中等风险浏览器工具；若没有这行代码，权限提示不会说明本地窗口副作用。
        return ("浏览器自动化中风险", "会打开网页、等待页面变化或保存截图；确认前请重点核对 url、page_id、filename。")  # 新增代码+AgentPySplitPhase9: 返回中风险浏览器操作说明；若没有这行代码，用户可能忽略网址、页面 id 或截图文件名。
    if "browser_automation" in tool_name:  # 新增代码+AgentPySplitPhase9: 捕获 snapshot、tabs、console、network 等其他浏览器自动化工具；若没有这行代码，这些只读状态读取会落到普通外部工具分类。
        return ("只读/低风险浏览器状态", "主要读取浏览器页面状态、标签页、console 或 network 摘要；确认前请重点核对 page_id 和读取范围。")  # 新增代码+AgentPySplitPhase9: 返回低风险浏览器状态说明；若没有这行代码，用户看不到 page_id 和读取范围这两个核对点。
    if "browser_search" in tool_name or tool_name.endswith("__web_search") or tool_name.endswith("__fetch_url") or tool_name.endswith("__open_url"):  # 新增代码+AgentPySplitPhase9: 识别搜索、浏览器和 URL 抓取类工具；若没有这行代码，联网访问可能被误认为本地只读。
        return ("外部网络访问", "会访问网络、搜索引擎或网页；确认前请重点核对 query、url 和是否需要实时信息。")  # 新增代码+AgentPySplitPhase9: 返回联网风险说明；若没有这行代码，用户看不到外部网络访问边界。
    if tool_name.endswith("__read_file") or tool_name.endswith("__list_dir") or tool_name.endswith("__glob") or tool_name.endswith("__grep"):  # 新增代码+AgentPySplitPhase9: 识别本地只读工作区工具；若没有这行代码，低风险读取无法和高风险操作区分。
        return ("只读/低风险", "只读取工作区信息；确认前仍需核对路径、模式或搜索关键词。")  # 新增代码+AgentPySplitPhase9: 返回只读风险说明；若没有这行代码，用户不知道虽然低风险也要检查参数。
    return ("外部工具调用", "来自 MCP server 的外部能力；确认前请核对工具名和全部参数。")  # 新增代码+AgentPySplitPhase9: 为未知 MCP 工具提供保守默认分类；若没有这行代码，新增 MCP 工具可能没有任何风险提示。
# 新增代码+AgentPySplitPhase9: 函数段结束，mcp_tool_risk_summary 到此结束；若没有这行注释，用户不容易看出风险分类边界。


def format_mcp_permission_action(tool_call: ToolCall) -> str:  # 新增代码+AgentPySplitPhase9: 函数段开始，统一格式化 MCP 工具授权文本；若没有这段函数，风险等级、说明和参数可能在不同调用处格式不一致。
    arguments_json = json.dumps(tool_call.arguments, ensure_ascii=False, indent=2)  # 新增代码+AgentPySplitPhase9: 把参数格式化成用户可读 JSON；若没有这行代码，用户难以核对本次工具调用的真实参数。
    risk_level, risk_note = mcp_tool_risk_summary(tool_call)  # 新增代码+AgentPySplitPhase9: 计算风险等级和风险说明；若没有这行代码，授权文本无法显示分级信息。
    return f"调用 MCP 工具：{tool_call.name}\n风险等级：{risk_level}\n风险说明：{risk_note}\n参数：{arguments_json}"  # 新增代码+AgentPySplitPhase9: 返回包含工具名、风险和参数的完整授权说明；若没有这行代码，ask_permission 无法给用户足够决策信息。
# 新增代码+AgentPySplitPhase9: 函数段结束，format_mcp_permission_action 到此结束；若没有这行注释，用户不容易看出权限文案边界。


def record_mcp_call_progress(agent: Any, tool_call: ToolCall, state: str, arguments: dict[str, Any], detail: str) -> None:  # 新增代码+AgentPySplitPhase9: 函数段开始，记录单次 MCP 调用进度；若没有这段函数，call progress 会分散在执行分支里。
    event = {  # 新增代码+AgentPySplitPhase9: 构造结构化进度事件；若没有这行代码，进度字段没有统一格式。
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),  # 新增代码+AgentPySplitPhase9: 保存事件时间；若没有这行代码，用户无法判断进度新旧。
        "tool_name": tool_call.name,  # 新增代码+AgentPySplitPhase9: 保存 MCP 前缀工具名；若没有这行代码，进度无法对应具体工具。
        "call_id": tool_call.call_id,  # 新增代码+AgentPySplitPhase9: 保存模型工具调用 id；若没有这行代码，多个连续调用难以区分。
        "state": state,  # 新增代码+AgentPySplitPhase9: 保存 permission_requested/started/completed/failed 等状态；若没有这行代码，进度没有机器可读阶段。
        "arguments": copy.deepcopy(arguments),  # 新增代码+AgentPySplitPhase9: 保存清洗后参数快照；若没有这行代码，审计无法核对用户确认和实际调用是否一致。
        "detail": detail,  # 新增代码+AgentPySplitPhase9: 保存补充说明或错误摘要；若没有这行代码，失败和输出长度细节会丢失。
    }  # 新增代码+AgentPySplitPhase9: 进度事件字典结束；若没有这行代码，Python 语法不完整。
    agent.mcp_call_progress_events.append(event)  # 新增代码+AgentPySplitPhase9: 把事件加入 MCP 调用进度列表；若没有这行代码，调用方无法回看进度。
    agent.mcp_call_progress_events = agent.mcp_call_progress_events[-200:]  # 新增代码+AgentPySplitPhase9: 限制最多保留最近 200 条；若没有这行代码，长期运行可能无限增长内存。
    run_helpers_from_core.safe_record_observation(agent, "mcp_call_progress", event)  # 修改代码+AgentPySplitPhase15B2: 通过 core helper 写入通用观察流，不再调用 agent.py 旧方法；若没有这行代码，删除 `旧观察薄包装` 后 MCP 进度审计会断开。
# 新增代码+AgentPySplitPhase9: 函数段结束，record_mcp_call_progress 到此结束；若没有这行注释，用户不容易看出 MCP 进度记录边界。


def is_computer_use_mcp_tool_call_name(tool_name: str) -> bool:  # 新增代码+McpSessionAdapter: 函数段开始，识别模型可见 Computer Use MCP 工具名；如果没有这段函数，execute_mcp_tool 无法区分内部桌面工具和普通外部 MCP 工具。
    return str(tool_name or "").strip().startswith("mcp__computer-use__")  # 新增代码+McpSessionAdapter: 只匹配 registry 暴露给模型的 computer-use 前缀；如果没有这一行，普通 MCP 工具可能被错误接管。
# 新增代码+McpSessionAdapter: 函数段结束，is_computer_use_mcp_tool_call_name 到此结束；如果没有这个边界说明，用户不容易看出工具名判断范围。


def computer_use_agent_block_count(result_text: str) -> int:  # 新增代码+ClaudeCodeWrapperParity：函数段开始，从 wrapper JSON 输出统计 agent_model_blocks 数量；如果没有这段函数，adapter 无法证明 MCP content blocks 已映射到 agent block。
    try:  # 新增代码+ClaudeCodeWrapperParity：解析 wrapper JSON 时捕获异常；如果没有这行代码，坏输出会让进度记录覆盖真实工具结果。
        payload = json.loads(str(result_text or ""))  # 新增代码+ClaudeCodeWrapperParity：把字符串输出解析成字典；如果没有这行代码，无法读取 agent_model_blocks。
    except (TypeError, ValueError, json.JSONDecodeError):  # 新增代码+ClaudeCodeWrapperParity：处理非 JSON 或坏 JSON 输出；如果没有这行代码，旧文本路径会抛异常。
        return 0  # 新增代码+ClaudeCodeWrapperParity：解析失败时返回 0；如果没有这行代码，调用方需要重复兜底判断。
    blocks = payload.get("agent_model_blocks", []) if isinstance(payload, dict) else []  # 新增代码+ClaudeCodeWrapperParity：读取 wrapper 生成的 agent block 列表；如果没有这行代码，非字典 payload 会属性错误。
    return len(blocks) if isinstance(blocks, list) else 0  # 新增代码+ClaudeCodeWrapperParity：只统计合法列表；如果没有这行代码，坏字段类型可能被误当作多个 block。
# 新增代码+ClaudeCodeWrapperParity：函数段结束，computer_use_agent_block_count 到此结束；如果没有这个边界说明，用户不容易看出 block 统计范围。


def execute_computer_use_mcp_tool(agent: Any, tool_call: ToolCall, safe_arguments: dict[str, Any]) -> str:  # 修改代码+ComputerUseMcpV2：函数段开始，执行 v2 agent-side Computer Use MCP 工具；如果没有这段函数，mcp__computer-use__ 会继续落回旧 executor。
    try:  # 修改代码+ComputerUseMcpV2：捕获 v2 runtime 绑定和工具执行异常；如果没有这一行，单个桌面 MCP 工具错误会中断整个 agent。
        record_mcp_call_progress(agent, tool_call, "started", safe_arguments, "agent-side computer-use mcp v2 runtime")  # 修改代码+ComputerUseMcpV2：记录 v2 工具开始执行；如果没有这一行，审计无法区分本次是否进入 v2。
        result_text = computer_use_mcp_v2_execute_agent_side_tool(agent, tool_call.name, safe_arguments, call_id=tool_call.call_id)  # 修改代码+ClaudeCodeWrapperParity：调用 v2 wrapper 并传入 call_id；如果没有这一行，current tool use context 无法和模型工具调用配对。
        block_count = computer_use_agent_block_count(result_text)  # 新增代码+ClaudeCodeWrapperParity：统计 wrapper 映射出的 agent block 数量；如果没有这行代码，进度记录无法证明 content block 映射是否发生。
        record_mcp_call_progress(agent, tool_call, "completed", safe_arguments, f"agent-side v2 chars={len(result_text)} agent_blocks={block_count}")  # 修改代码+ClaudeCodeWrapperParity：记录 v2 工具完成、输出长度和 block 数量；如果没有这一行，长任务审计无法确认 wrapper 映射结果。
        return result_text  # 修改代码+ComputerUseMcpV2：把 v2 JSON 文本结果返回给模型；如果没有这一行，模型拿不到 request_access/observe/action 的反馈。
    except Exception as error:  # 修改代码+ComputerUseMcpV2：把 v2 异常转成模型可读失败文本；如果没有这一行，异常会冒泡破坏当前轮。
        record_mcp_call_progress(agent, tool_call, "failed", safe_arguments, str(error))  # 修改代码+ComputerUseMcpV2：记录 v2 执行失败原因；如果没有这一行，后续排查无法知道失败发生在 v2。
        return f"Computer Use MCP v2 内部工具调用失败：{error}"  # 修改代码+ComputerUseMcpV2：返回清晰失败文本；如果没有这一行，模型无法根据错误恢复。
# 修改代码+ComputerUseMcpV2：函数段结束，execute_computer_use_mcp_tool 到此结束；如果没有这个边界说明，用户不容易看出执行范围已经切到 v2。


def execute_mcp_tool(agent: Any, tool_call: ToolCall) -> str:  # 新增代码+AgentPySplitPhase9: 函数段开始，执行 MCP registry 工具并统一处理权限与异常；若没有这段函数，agent.py 仍要承载外部 MCP 调用细节。
    sanitizer = getattr(agent.mcp_tool_registry, "sanitize_tool_arguments", None)  # 新增代码+AgentPySplitPhase9: 读取 registry 的参数清洗能力；若没有这行代码，授权提示会展示模型混入的无关字段。
    safe_arguments = sanitizer(tool_call.name, tool_call.arguments) if callable(sanitizer) else dict(tool_call.arguments)  # 新增代码+AgentPySplitPhase9: 先按工具 schema 清洗参数；若没有这行代码，用户会继续看到 status/action/confirm_real_profile 这类串味字段。
    safe_tool_call = ToolCall(name=tool_call.name, arguments=safe_arguments, call_id=tool_call.call_id)  # 新增代码+AgentPySplitPhase9: 构造用于提示和调用的安全 ToolCall；若没有这行代码，权限文本和实际调用可能用的不是同一份参数。
    catalog_tool = catalog_runtime_from_tools.find_catalog_tool(agent, safe_tool_call.name)  # 新增代码+ClaudeCodeToolSurface: 在 MCP adapter 内再次查找工具策略元数据；如果没有这一行，绕过 executor 的直接 MCP 调用不会经过模式化工具池过滤。
    if catalog_tool is not None:  # 新增代码+ClaudeCodeToolSurface: 只有 catalog 知道的工具才做 scope 二次判断；如果没有这一行，未知外部工具会在访问策略字段时出错。
        decision = catalog_runtime_from_tools.tool_policy_decision(agent, catalog_tool)  # 新增代码+ClaudeCodeToolSurface: 复用同一套工具池策略；如果没有这一行，adapter 和模型可见工具池会产生不一致。
        if decision.state == "scope_blocked":  # 新增代码+ClaudeCodeToolSurface: scope 阻断必须早于权限请求和真实 MCP 调用；如果没有这一行，隐藏工具仍可能弹权限并触达 server。
            run_helpers_from_core.safe_record_observation(agent, "mcp_scope_blocked_tool", {"tool_name": safe_tool_call.name, "reason": decision.reason})  # 新增代码+ClaudeCodeToolSurface: 记录 MCP scope 拒绝事件；如果没有这一行，审计无法解释为什么没有进入权限提示。
            return f"{safe_tool_call.name} 失败：tool scope 阻断，原因：{decision.reason}"  # 新增代码+ClaudeCodeToolSurface: 返回清晰拒绝信息；如果没有这一行，模型不知道这是模式隔离而不是 server 故障。
    if is_computer_use_mcp_tool_call_name(safe_tool_call.name):  # 新增代码+McpSessionAdapter: Computer Use MCP 工具在 scope 通过后由 agent 内部 adapter 接管；如果没有这一行，click/request_access 等会继续调用外部 registry 而拿不到主循环回调。
        return execute_computer_use_mcp_tool(agent, safe_tool_call, safe_arguments)  # 新增代码+McpSessionAdapter: 执行内部 Computer Use MCP 工具并返回结果；如果没有这一行，agent-side binding 不会生效。
    denial_key = catalog_runtime_from_tools.tool_denial_key(safe_tool_call)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 基于清洗后的 ToolCall 直连 catalog_runtime 计算拒绝记忆指纹；若没有这行代码，MCP 权限去重仍依赖 agent.py 薄包装。
    if denial_key in agent.permission_denials:  # 新增代码+AgentPySplitPhase9: 检查同一工具和参数是否已经被用户拒绝；若没有这行代码，agent 会反复请求相同权限。
        record_mcp_call_progress(agent, safe_tool_call, "permission_denied_cached", safe_arguments, "same sanitized arguments were denied before")  # 新增代码+AgentPySplitPhase9: 记录命中拒绝记忆的进度；若没有这行代码，审计只能看到最终失败文本。
        return f"{tool_call.name} 失败：之前已被用户拒绝，同一工具和参数不会重复请求权限。"  # 新增代码+AgentPySplitPhase9: 直接返回拒绝记忆结果；若没有这行代码，用户会被同一被拒操作反复打断。
    auto_approve_reason = browser_agent_workflow_from_browser.real_browser_customer_auto_approve_reason(agent, safe_tool_call)  # 修改代码+AgentPyCompatWrapperRemovalL7: MCP 适配层直接调用浏览器 workflow 判断自动授权原因；若没有这行代码，删除 agent.py 旧包装后客户模式会每步弹 y/N。
    if auto_approve_reason:  # 新增代码+AgentPySplitPhase9: 命中自动授权时跳过人工 input；若没有这行代码，白名单判断结果不会生效。
        record_mcp_call_progress(agent, safe_tool_call, "permission_auto_approved", safe_arguments, auto_approve_reason)  # 新增代码+AgentPySplitPhase9: 记录自动授权进度；若没有这行代码，审计无法解释为什么没有 permission_required。
        browser_agent_workflow_from_browser.print_real_browser_customer_progress(browser_agent_workflow_from_browser.real_browser_customer_progress_message(safe_tool_call))  # 修改代码+AgentPyCompatWrapperRemovalL7: MCP 适配层直接用浏览器 workflow 生成并打印进度；若没有这行代码，删除旧包装后用户看不到 agent 正在思考和操作。
    else:  # 新增代码+AgentPySplitPhase9: 未命中白名单时保持原人工权限流程；若没有这行代码，敏感工具可能绕过用户确认。
        action = format_mcp_permission_action(safe_tool_call)  # 新增代码+AgentPySplitPhase9: 用清洗后的参数生成授权说明；若没有这行代码，截图里的多余字段会继续误导用户。
        record_mcp_call_progress(agent, safe_tool_call, "permission_requested", safe_arguments, "")  # 新增代码+AgentPySplitPhase9: 记录即将请求 MCP 工具权限；若没有这行代码，权限流缺少结构化进度。
        if not agent.ask_permission(action):  # 新增代码+AgentPySplitPhase9: 调用外部 MCP 工具前请求用户确认；若没有这行代码，agent 会绕过权限边界执行外部工具。
            agent.permission_denials.add(denial_key)  # 新增代码+AgentPySplitPhase9: 保存本次用户拒绝的稳定指纹；若没有这行代码，下次相同请求仍会再次弹权限确认。
            record_mcp_call_progress(agent, safe_tool_call, "permission_denied", safe_arguments, "user denied MCP tool call")  # 新增代码+AgentPySplitPhase9: 记录用户拒绝本次权限；若没有这行代码，审计看不到拒绝发生在哪一步。
            return f"用户拒绝了操作：{action}"  # 新增代码+AgentPySplitPhase9: 权限拒绝时返回可读结果给模型；若没有这行代码，模型不知道工具调用被用户拒绝。
    try:  # 新增代码+AgentPySplitPhase9: 捕获 MCP registry 或外部工具调用异常；若没有这行代码，单个 MCP 工具失败会中断整个 agent.run。
        record_mcp_call_progress(agent, safe_tool_call, "started", safe_arguments, "")  # 新增代码+AgentPySplitPhase9: 记录外部 MCP 工具正式开始执行；若没有这行代码，进度只停留在权限阶段。
        result_text = agent.mcp_tool_registry.call_tool(safe_tool_call.name, safe_tool_call.arguments)  # 新增代码+AgentPySplitPhase9: 调用 registry 并保存结果；若没有这行代码，无法在返回前更新 workflow 和 progress。
        record_mcp_call_progress(agent, safe_tool_call, "completed", safe_arguments, f"chars={len(result_text)}")  # 新增代码+AgentPySplitPhase9: 记录 MCP 工具完成和输出长度；若没有这行代码，大输出审计缺少完成状态。
        browser_agent_workflow_from_browser.update_workflows_after_mcp_tool(agent, safe_tool_call, result_text)  # 修改代码+AgentPyCompatWrapperRemovalL7: MCP 适配层直接调用浏览器 workflow 推进状态；若没有这行代码，真实 Chrome 前置检查不会解锁后续连接。
        record_browser_runtime_status_after_mcp_tool(agent, safe_tool_call, "completed")  # 新增代码+AgentPySplitPhase9: 浏览器 MCP 工具完成后把最新 browser run 镜像到统一状态事件；若没有这行代码，BrowserRuntimeStore 会成为旁路系统。
        return result_text  # 新增代码+AgentPySplitPhase9: 返回真实 MCP 工具结果；若没有这行代码，调用方拿不到外部工具输出。
    except Exception as error:  # 新增代码+AgentPySplitPhase9: 把外部异常转换成可读文本；若没有这行代码，用户和模型会看到 Python 堆栈或直接崩溃。
        record_mcp_call_progress(agent, safe_tool_call, "failed", safe_arguments, str(error))  # 新增代码+AgentPySplitPhase9: 记录 MCP 工具失败和错误摘要；若没有这行代码，结构化审计无法追踪外部失败。
        record_browser_runtime_status_after_mcp_tool(agent, safe_tool_call, "failed")  # 新增代码+AgentPySplitPhase9: 浏览器 MCP 工具失败后也尝试镜像 browser run；若没有这行代码，失败浏览器任务可能从状态生态消失。
        return f"MCP 工具调用失败：{error}"  # 新增代码+AgentPySplitPhase9: 返回清晰失败原因给模型；若没有这行代码，MCP 异常缺少可恢复反馈。
# 新增代码+AgentPySplitPhase9: 函数段结束，execute_mcp_tool 到此结束；若没有这行注释，用户不容易看出 MCP 工具执行边界。


def record_browser_runtime_status_after_mcp_tool(agent: Any, tool_call: ToolCall, state: str) -> None:  # 新增代码+AgentPySplitPhase9: 函数段开始，将 browser runtime store 最新 run 镜像进 observation 和 status event；若没有这段函数，主循环看不见浏览器 durable run。
    catalog_tool = catalog_runtime_from_tools.find_catalog_tool(agent, tool_call.name)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 直连 catalog_runtime 读取工具目录元数据；若没有这行代码，browser runtime 镜像仍依赖 agent.py 薄包装。
    if catalog_tool is None or catalog_tool.server_name != "browser_automation":  # 新增代码+AgentPySplitPhase9: 只处理浏览器自动化 MCP server；若没有这行代码，搜索、文件、命令工具会产生无意义扫描。
        return  # 新增代码+AgentPySplitPhase9: 非浏览器工具直接退出；若没有这行代码，函数会继续访问不存在的 browser run。
    try:  # 新增代码+AgentPySplitPhase9: status 镜像不能破坏真实工具结果返回；若没有这行代码，状态写入异常会拖垮浏览器任务。
        from learning_agent.browser.runtime_store import BrowserRuntimeStore  # 新增代码+AgentPySplitPhase9: 延迟导入 browser runtime store；若没有这行代码，agent 无法读取 browser run 文件。
        from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+AgentPySplitPhase9: 延迟导入统一状态事件 store；若没有这行代码，UI/SDK 仍看不到 browser runtime。
        browser_runtime_root = agent.workspace / "learning_agent" / "memory" / "browser_runtime"  # 新增代码+AgentPySplitPhase9: 使用 browser MCP server 约定的生产路径；若没有这行代码，agent 会扫描错误目录。
        browser_store = BrowserRuntimeStore(browser_runtime_root)  # 新增代码+AgentPySplitPhase9: 创建读取端 store；若没有这行代码，无法结构化读取 run 和 event。
        run_ids = browser_store.list_run_ids()  # 新增代码+AgentPySplitPhase9: 列出当前 workspace 下的 browser run；若没有这行代码，无法找到最新任务。
        if not run_ids:  # 新增代码+AgentPySplitPhase9: 没有 browser run 时直接退出；若没有这行代码，空列表 max 会抛错。
            return  # 新增代码+AgentPySplitPhase9: 无 run 可镜像时保持工具结果不受影响；若没有这行代码，非落盘工具会失败。
        latest_run_id = max(run_ids, key=lambda run_id: browser_store.run_path(run_id).stat().st_mtime)  # 新增代码+AgentPySplitPhase9: 按文件修改时间选择刚刚写入的 run；若没有这行代码，多次浏览器调用会镜像旧 run。
        browser_run = browser_store.load_run(latest_run_id)  # 新增代码+AgentPySplitPhase9: 读取最新 browser run 对象；若没有这行代码，状态事件只能写文件名不能写状态。
        browser_events = browser_store.tail_events(browser_run.run_id, limit=10)  # 新增代码+AgentPySplitPhase9: 读取最近 browser runtime 事件；若没有这行代码，状态事件缺少 started/completed 证据。
        event_types = [str(event.get("event_type", "")) for event in browser_events]  # 新增代码+AgentPySplitPhase9: 提取事件名列表；若没有这行代码，UI/SDK 无法快速显示浏览器时间线。
        payload = {"browser_run_id": browser_run.run_id, "browser_run_status": browser_run.status, "browser_current_stage_id": browser_run.current_stage_id, "browser_action_ids": list(browser_run.action_ids), "browser_observation_ids": list(browser_run.observation_ids), "browser_event_types": event_types, "mcp_tool_name": tool_call.name, "mirror_state": state}  # 新增代码+AgentPySplitPhase9: 构造状态事件正文；若没有这行代码，状态生态拿不到 browser run 关键字段。
        run_helpers_from_core.safe_record_observation(agent, "browser_runtime_run_detected", payload)  # 修改代码+AgentPySplitPhase15B2: 通过 core helper 同步 browser run observation；若没有这行代码，删除 `旧观察薄包装` 后旧调试入口看不到镜像结果。
        StatusEventStore(agent.workspace / "memory" / "status").append("browser_runtime_event", payload, run_id=browser_run.run_id)  # 新增代码+AgentPySplitPhase9: 写入统一状态事件流；若没有这行代码，CLI/API/SDK 无法订阅 browser runtime。
    except Exception as error:  # 新增代码+AgentPySplitPhase9: 镜像失败只记录 observation，不影响工具输出；若没有这行代码，状态写入问题会破坏真实浏览器操作。
        run_helpers_from_core.safe_record_observation(agent, "browser_runtime_status_mirror_failed", {"tool_name": tool_call.name, "state": state, "error": str(error)})  # 修改代码+AgentPySplitPhase15B2: 通过 core helper 留下镜像失败原因；若没有这行代码，删除 `旧观察薄包装` 后状态缺失会无迹可查。
# 新增代码+AgentPySplitPhase9: 函数段结束，record_browser_runtime_status_after_mcp_tool 到此结束；若没有这行注释，用户不容易看出 browser runtime 镜像边界。


def listen_mcp_stream(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase9: 函数段开始，监听 MCP stream；若没有这段函数，listen_mcp_stream 会继续堆在 agent.py。
    server_name = str(arguments.get("server", "") or "").strip()  # 新增代码+AgentPySplitPhase9: 读取并清理必填 server 参数；若没有这行代码，无法确定要监听哪个 MCP server。
    if not server_name:  # 新增代码+AgentPySplitPhase9: 检查 server 是否为空；若没有这行代码，空 server 会进入 registry 并产生较难懂错误。
        return "listen_mcp_stream 失败：缺少 server 参数。"  # 新增代码+AgentPySplitPhase9: 返回清楚缺参错误；若没有这行代码，模型难以修正工具调用参数。
    if not agent.mcp_tools_enabled:  # 新增代码+AgentPySplitPhase9: 检查 MCP 是否已启动或可用；若没有这行代码，拒绝启动后仍可能尝试访问外部 stream。
        detail = agent.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+AgentPySplitPhase9: 选择最清楚的不可用原因；若没有这行代码，返回信息会缺少排查线索。
        return f"MCP stream 不可用：{detail}"  # 新增代码+AgentPySplitPhase9: 返回可读不可用结果；若没有这行代码，模型会把 stream 不可用误解为未知工具。
    max_events = 5  # 新增代码+AgentPySplitPhase9: 设置默认最多读取 5 条事件；若没有这行代码，非法或缺省参数没有安全兜底。
    try:  # 新增代码+AgentPySplitPhase9: 捕获 max_events 转换错误和无穷大溢出；若没有这行代码，模型传入字符串、对象或 inf 会抛裸异常。
        parsed_max_events = int(arguments.get("max_events", max_events))  # 新增代码+AgentPySplitPhase9: 把 max_events 转成整数；若没有这行代码，registry 可能收到非数字导致底层错误。
        if 1 <= parsed_max_events <= 20:  # 新增代码+AgentPySplitPhase9: 检查事件数在 1 到 20 内；若没有这行代码，过大事件数可能撑爆上下文或等待过久。
            max_events = parsed_max_events  # 新增代码+AgentPySplitPhase9: 使用合法事件数；若没有这行代码，用户传入的合法限制不会生效。
    except (TypeError, ValueError, OverflowError):  # 新增代码+AgentPySplitPhase9: 处理无法转成整数或无穷大溢出的非法值；若没有这行代码，inf 会触发 OverflowError 中断整个工具调用。
        max_events = 5  # 新增代码+AgentPySplitPhase9: 非法值回退默认 5；若没有这行代码，后续变量可能不存在或保留危险值。
    timeout_seconds = 2.0  # 新增代码+AgentPySplitPhase9: 设置默认监听等待 2 秒；若没有这行代码，非法或缺省参数没有安全兜底。
    try:  # 新增代码+AgentPySplitPhase9: 捕获 timeout_seconds 转换错误；若没有这行代码，模型传入字符串或对象会抛裸异常。
        parsed_timeout_seconds = float(arguments.get("timeout_seconds", timeout_seconds))  # 新增代码+AgentPySplitPhase9: 把 timeout_seconds 转成浮点数；若没有这行代码，registry 可能收到非数字导致底层错误。
        if parsed_timeout_seconds != parsed_timeout_seconds or parsed_timeout_seconds in {float("inf"), float("-inf")}:  # 新增代码+AgentPySplitPhase9: 拒绝 nan 和正负无穷大；若没有这行代码，nan 可能绕过范围判断后留下不清楚的非法超时。
            raise ValueError("timeout_seconds 必须是有限数字")  # 新增代码+AgentPySplitPhase9: 把非有限数字转入统一兜底分支；若没有这行代码，后续无法稳定回退默认 2.0。
        if 0.1 <= parsed_timeout_seconds <= 10.0:  # 新增代码+AgentPySplitPhase9: 检查等待时间在 0.1 到 10 秒内；若没有这行代码，过长等待会卡住工具调用。
            timeout_seconds = parsed_timeout_seconds  # 新增代码+AgentPySplitPhase9: 使用合法等待时间；若没有这行代码，用户传入的合法限制不会生效。
    except (TypeError, ValueError):  # 新增代码+AgentPySplitPhase9: 处理无法转成浮点数的非法值；若没有这行代码，非法 timeout_seconds 会中断整个工具调用。
        timeout_seconds = 2.0  # 新增代码+AgentPySplitPhase9: 非法值回退默认 2.0；若没有这行代码，后续变量可能不存在或保留危险值。
    raw_resume = arguments.get("resume", True)  # 新增代码+AgentPySplitPhase9: 读取 resume 参数并默认开启；若没有这行代码，缺省调用无法按要求自动续传。
    if isinstance(raw_resume, bool):  # 新增代码+AgentPySplitPhase9: 直接支持布尔 resume；若没有这行代码，true/false 会被字符串逻辑误处理。
        resume = raw_resume  # 新增代码+AgentPySplitPhase9: 保留调用方给出的布尔值；若没有这行代码，用户无法明确关闭或开启续传。
    elif isinstance(raw_resume, str):  # 新增代码+AgentPySplitPhase9: 支持常见字符串开关；若没有这行代码，模型传 "false" 时仍会被当成 True。
        resume = raw_resume.strip().lower() not in {"false", "0", "no", "off"}  # 新增代码+AgentPySplitPhase9: false/0/no/off 视为 False，其余视为 True；若没有这行代码，字符串兼容规则不会生效。
    else:  # 新增代码+AgentPySplitPhase9: 处理数字、None 或其他类型；若没有这行代码，非字符串非布尔值的语义不清楚。
        resume = True  # 新增代码+AgentPySplitPhase9: 其他类型按默认 True 处理；若没有这行代码，非法 resume 可能导致底层收到奇怪类型。
    permission_payload = {"server": server_name, "max_events": max_events, "timeout_seconds": timeout_seconds, "resume": resume}  # 新增代码+AgentPySplitPhase9: 构造权限提示里的参数快照；若没有这行代码，用户看不到本次监听的关键边界。
    action = f"监听 MCP stream\n参数：{json.dumps(permission_payload, ensure_ascii=False, indent=2)}"  # 新增代码+AgentPySplitPhase9: 生成 stream 监听权限说明；若没有这行代码，ask_permission 缺少 server、事件数、超时和续传信息。
    if not agent.ask_permission(action):  # 新增代码+AgentPySplitPhase9: 监听外部 MCP stream 前请求用户确认；若没有这行代码，外部 stream 读取会绕过权限边界。
        return f"用户拒绝了操作：{action}"  # 新增代码+AgentPySplitPhase9: 权限拒绝时返回可读结果；若没有这行代码，模型不知道 stream 监听被拒绝。
    try:  # 新增代码+AgentPySplitPhase9: 捕获 registry 或外部 server 的 stream 监听异常；若没有这行代码，单个 MCP stream 失败会中断整个 agent。
        text = agent.mcp_tool_registry.listen_stream(server_name, max_events=max_events, timeout_seconds=timeout_seconds, resume=resume)  # 新增代码+AgentPySplitPhase9: 调用 registry 监听目标 server；若没有这行代码，权限确认后不会真正读取 stream。
    except Exception as error:  # 新增代码+AgentPySplitPhase9: 把外部异常转换成可读文本；若没有这行代码，用户和模型会看到 Python 堆栈或直接崩溃。
        return f"listen_mcp_stream 失败：{error}"  # 新增代码+AgentPySplitPhase9: 返回清晰失败原因；若没有这行代码，模型无法判断下一步怎么修复。
    return f"listen_mcp_stream 成功：server={server_name}\n{text}"  # 新增代码+AgentPySplitPhase9: 返回带 server 和正文的成功结果；若没有这行代码，工具结果缺少来源或 stream 内容。
# 新增代码+AgentPySplitPhase9: 函数段结束，listen_mcp_stream 到此结束；若没有这行注释，用户不容易看出 stream 监听边界。


def list_mcp_resources(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase9: 函数段开始，执行内置 list_mcp_resources 工具；若没有这段函数，模型无法从内置工具列 MCP 资源。
    if not agent.mcp_tools_enabled:  # 新增代码+AgentPySplitPhase9: 检查 MCP 是否已启动或可用；若没有这行代码，拒绝启动后仍可能尝试访问外部资源。
        detail = agent.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+AgentPySplitPhase9: 选择最清楚的不可用原因；若没有这行代码，返回信息会缺少排查线索。
        return f"MCP resources 不可用：{detail}"  # 新增代码+AgentPySplitPhase9: 返回可读不可用结果；若没有这行代码，模型会把资源不可用误解为未知工具。
    raw_server = arguments.get("server")  # 新增代码+AgentPySplitPhase9: 读取可选 server 参数；若没有这行代码，无法支持只列某个 MCP server。
    server_name = str(raw_server).strip() if raw_server is not None else ""  # 新增代码+AgentPySplitPhase9: 清理 server 参数并允许省略；若没有这行代码，None 或空白 server 可能被误当真实名称。
    selected_server = server_name or None  # 新增代码+AgentPySplitPhase9: 空字符串转成 None 表示列所有 server；若没有这行代码，registry 会查找名为空的 server。
    max_results = search_tools_from_tools.tool_search_max_results(arguments.get("max_results"))  # 修改代码+AgentPyCompatWrapperRemovalL2: 直接复用 tools.search 的 1 到 20 结果数限制；若没有这行代码，删除 agent.py 旧包装后 resources 列表会断开。
    permission_payload = {"server": selected_server, "max_results": max_results}  # 新增代码+AgentPySplitPhase9: 构造权限提示里的参数快照；若没有这行代码，用户看不到本次要列哪些资源。
    action = f"列出 MCP resources\n参数：{json.dumps(permission_payload, ensure_ascii=False, indent=2)}"  # 新增代码+AgentPySplitPhase9: 生成资源列表权限说明；若没有这行代码，ask_permission 缺少可读操作描述。
    if not agent.ask_permission(action):  # 新增代码+AgentPySplitPhase9: 列出外部 MCP 资源前请求用户确认；若没有这行代码，外部资源枚举会绕过权限边界。
        return f"用户拒绝了操作：{action}"  # 新增代码+AgentPySplitPhase9: 权限拒绝时返回可读结果；若没有这行代码，模型不知道资源列表被拒绝。
    try:  # 新增代码+AgentPySplitPhase9: 捕获 registry 或外部 server 的资源列表异常；若没有这行代码，单个 MCP server 失败会中断整个 agent。
        resources = agent.mcp_tool_registry.list_resources(selected_server)  # 新增代码+AgentPySplitPhase9: 调用 registry 聚合 resources/list；若没有这行代码，权限确认后不会真正读取资源列表。
    except Exception as error:  # 新增代码+AgentPySplitPhase9: 把外部异常转换成可读文本；若没有这行代码，用户和模型会看到 Python 堆栈或直接崩溃。
        return f"list_mcp_resources 失败：{error}"  # 新增代码+AgentPySplitPhase9: 返回清晰失败原因；若没有这行代码，模型无法判断下一步怎么修复。
    visible_resources = resources[:max_results]  # 新增代码+AgentPySplitPhase9: 截取最多 max_results 条资源；若没有这行代码，大量 resources 可能撑爆上下文。
    if not visible_resources:  # 新增代码+AgentPySplitPhase9: 处理没有资源的情况；若没有这行代码，空结果会返回只有标题的模糊文本。
        return "list_mcp_resources 成功：没有找到 MCP resources。"  # 新增代码+AgentPySplitPhase9: 明确说明列表为空；若没有这行代码，模型可能误以为工具失败。
    lines = [f"list_mcp_resources 成功：找到 {len(resources)} 个 resource，显示前 {len(visible_resources)} 个。"]  # 新增代码+AgentPySplitPhase9: 构造资源列表标题；若没有这行代码，模型不知道数量和截断情况。
    for index, resource in enumerate(visible_resources, start=1):  # 新增代码+AgentPySplitPhase9: 逐条格式化资源信息；若没有这行代码，资源对象无法变成人类和模型可读文本。
        name = str(resource.get("name", "") or "(无名称)")  # 新增代码+AgentPySplitPhase9: 读取资源名称并兜底；若没有这行代码，缺名称资源展示不友好。
        uri = str(resource.get("uri", "") or "(无 uri)")  # 新增代码+AgentPySplitPhase9: 读取资源 uri 并兜底；若没有这行代码，模型不知道 read_mcp_resource 要传什么 uri。
        server = str(resource.get("server", "") or "(未知 server)")  # 新增代码+AgentPySplitPhase9: 读取来源 server 并兜底；若没有这行代码，模型不知道 read_mcp_resource 要传什么 server。
        mime_type = str(resource.get("mimeType", "") or resource.get("mime_type", "") or "(未知类型)")  # 新增代码+AgentPySplitPhase9: 读取资源 MIME 类型并兼容字段名；若没有这行代码，模型缺少判断资源内容格式的信息。
        description = str(resource.get("description", "") or "(无说明)")  # 新增代码+AgentPySplitPhase9: 读取资源说明并兜底；若没有这行代码，模型缺少判断资源用途的信息。
        lines.append(f"{index}. {name}")  # 新增代码+AgentPySplitPhase9: 输出资源序号和名称；若没有这行代码，结果清单不易阅读。
        lines.append(f"   server：{server}")  # 新增代码+AgentPySplitPhase9: 输出读取时必需的 server；若没有这行代码，模型后续无法精确读取资源。
        lines.append(f"   uri：{uri}")  # 新增代码+AgentPySplitPhase9: 输出读取时必需的 uri；若没有这行代码，模型后续无法精确读取资源。
        lines.append(f"   mimeType：{mime_type}")  # 新增代码+AgentPySplitPhase9: 输出资源类型；若没有这行代码，模型不知道内容可能是 markdown、json 或其他格式。
        lines.append(f"   说明：{description}")  # 新增代码+AgentPySplitPhase9: 输出资源说明；若没有这行代码，模型缺少选择资源的语义依据。
    return "\n".join(lines)  # 新增代码+AgentPySplitPhase9: 返回完整资源列表文本；若没有这行代码，工具无法把结果交回模型。
# 新增代码+AgentPySplitPhase9: 函数段结束，list_mcp_resources 到此结束；若没有这行注释，用户不容易看出 resource 列表边界。


def read_mcp_resource(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase9: 函数段开始，执行内置 read_mcp_resource 工具；若没有这段函数，模型无法从内置工具读取 MCP 资源正文。
    if not agent.mcp_tools_enabled:  # 新增代码+AgentPySplitPhase9: 检查 MCP 是否已启动或可用；若没有这行代码，拒绝启动后仍可能尝试读取外部资源。
        detail = agent.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+AgentPySplitPhase9: 选择最清楚的不可用原因；若没有这行代码，返回信息会缺少排查线索。
        return f"MCP resources 不可用：{detail}"  # 新增代码+AgentPySplitPhase9: 返回可读不可用结果；若没有这行代码，模型会把资源不可用误解为未知工具。
    server_name = str(arguments.get("server", "") or "").strip()  # 新增代码+AgentPySplitPhase9: 读取并清理必填 server 参数；若没有这行代码，无法确定资源来自哪个 MCP server。
    uri = str(arguments.get("uri", "") or "").strip()  # 新增代码+AgentPySplitPhase9: 读取并清理必填 uri 参数；若没有这行代码，无法确定要读取哪个资源。
    if not server_name:  # 新增代码+AgentPySplitPhase9: 检查 server 是否为空；若没有这行代码，空 server 会进入 registry 并产生较难懂错误。
        return "read_mcp_resource 失败：缺少 server 参数。"  # 新增代码+AgentPySplitPhase9: 返回清楚缺参错误；若没有这行代码，模型难以修正工具调用参数。
    if not uri:  # 新增代码+AgentPySplitPhase9: 检查 uri 是否为空；若没有这行代码，空 uri 会进入外部 server 并产生较难懂错误。
        return "read_mcp_resource 失败：缺少 uri 参数。"  # 新增代码+AgentPySplitPhase9: 返回清楚缺参错误；若没有这行代码，模型难以修正工具调用参数。
    max_chars = parse_max_chars_value(arguments.get("max_chars"))  # 修改代码+AgentPySplitPhase15B2: 直接使用公共解析函数，不再反向调用 agent.py 薄包装；若没有这行代码，删除 `旧输出长度薄包装` 后 MCP resource 读取会断开。
    permission_payload = {"server": server_name, "uri": uri, "max_chars": max_chars}  # 新增代码+AgentPySplitPhase9: 构造权限提示里的参数快照；若没有这行代码，用户看不到本次读取哪个资源。
    action = f"读取 MCP resource\n参数：{json.dumps(permission_payload, ensure_ascii=False, indent=2)}"  # 新增代码+AgentPySplitPhase9: 生成资源读取权限说明；若没有这行代码，ask_permission 缺少可读操作描述。
    if not agent.ask_permission(action):  # 新增代码+AgentPySplitPhase9: 读取外部 MCP 资源前请求用户确认；若没有这行代码，外部资源正文会绕过权限边界。
        return f"用户拒绝了操作：{action}"  # 新增代码+AgentPySplitPhase9: 权限拒绝时返回可读结果；若没有这行代码，模型不知道资源读取被拒绝。
    try:  # 新增代码+AgentPySplitPhase9: 捕获 registry 或外部 server 的资源读取异常；若没有这行代码，单个 MCP resource 失败会中断整个 agent。
        text = agent.mcp_tool_registry.read_resource(server_name, uri)  # 新增代码+AgentPySplitPhase9: 调用 registry 读取目标 resource；若没有这行代码，权限确认后不会真正读取正文。
    except Exception as error:  # 新增代码+AgentPySplitPhase9: 把外部异常转换成可读文本；若没有这行代码，用户和模型会看到 Python 堆栈或直接崩溃。
        return f"read_mcp_resource 失败：{error}"  # 新增代码+AgentPySplitPhase9: 返回清晰失败原因；若没有这行代码，模型无法判断下一步怎么修复。
    truncated_text = text[:max_chars]  # 新增代码+AgentPySplitPhase9: 按 max_chars 截断资源正文；若没有这行代码，长资源可能撑爆上下文。
    if len(text) > max_chars:  # 新增代码+AgentPySplitPhase9: 检查正文是否被截断；若没有这行代码，用户和模型不知道返回内容是否完整。
        truncated_text += "\n...[MCP resource 内容过长，已截断]..."  # 新增代码+AgentPySplitPhase9: 添加截断提示；若没有这行代码，模型可能误以为读取了完整资源。
    return f"read_mcp_resource 成功：server={server_name} uri={uri}\n{truncated_text}"  # 新增代码+AgentPySplitPhase9: 返回带来源和正文的结果；若没有这行代码，工具结果缺少上下文或正文。
# 新增代码+AgentPySplitPhase9: 函数段结束，read_mcp_resource 到此结束；若没有这行注释，用户不容易看出 resource 读取边界。


def list_mcp_prompts(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase9: 函数段开始，执行内置 list_mcp_prompts 工具；若没有这段函数，模型无法从内置工具列 MCP prompts。
    if not agent.mcp_tools_enabled:  # 新增代码+AgentPySplitPhase9: 检查 MCP 是否已启动或可用；若没有这行代码，拒绝启动后仍可能尝试访问外部 prompts。
        detail = agent.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+AgentPySplitPhase9: 选择最清楚的不可用原因；若没有这行代码，返回信息会缺少排查线索。
        return f"MCP prompts 不可用：{detail}"  # 新增代码+AgentPySplitPhase9: 返回可读不可用结果；若没有这行代码，模型会把 prompt 不可用误解为未知工具。
    raw_server = arguments.get("server")  # 新增代码+AgentPySplitPhase9: 读取可选 server 参数；若没有这行代码，无法支持只列某个 MCP server。
    server_name = str(raw_server).strip() if raw_server is not None else ""  # 新增代码+AgentPySplitPhase9: 清理 server 参数并允许省略；若没有这行代码，None 或空白 server 可能被误当真实名称。
    selected_server = server_name or None  # 新增代码+AgentPySplitPhase9: 空字符串转成 None 表示列所有 server；若没有这行代码，registry 会查找名为空的 server。
    max_results = search_tools_from_tools.tool_search_max_results(arguments.get("max_results"))  # 修改代码+AgentPyCompatWrapperRemovalL2: 直接复用 tools.search 的 1 到 20 结果数限制；若没有这行代码，删除 agent.py 旧包装后 prompts 列表会断开。
    permission_payload = {"server": selected_server, "max_results": max_results}  # 新增代码+AgentPySplitPhase9: 构造权限提示里的参数快照；若没有这行代码，用户看不到本次要列哪些 prompts。
    action = f"列出 MCP prompts\n参数：{json.dumps(permission_payload, ensure_ascii=False, indent=2)}"  # 新增代码+AgentPySplitPhase9: 生成 prompt 列表权限说明；若没有这行代码，ask_permission 缺少可读操作描述。
    if not agent.ask_permission(action):  # 新增代码+AgentPySplitPhase9: 列出外部 MCP prompts 前请求用户确认；若没有这行代码，外部 prompt 枚举会绕过权限边界。
        return f"用户拒绝了操作：{action}"  # 新增代码+AgentPySplitPhase9: 权限拒绝时返回可读结果；若没有这行代码，模型不知道 prompt 列表被拒绝。
    try:  # 新增代码+AgentPySplitPhase9: 捕获 registry 或外部 server 的 prompt 列表异常；若没有这行代码，单个 MCP server 失败会中断整个 agent。
        prompts = agent.mcp_tool_registry.list_prompts(selected_server)  # 新增代码+AgentPySplitPhase9: 调用 registry 聚合 prompts/list；若没有这行代码，权限确认后不会真正读取 prompt 列表。
    except Exception as error:  # 新增代码+AgentPySplitPhase9: 把外部异常转换成可读文本；若没有这行代码，用户和模型会看到 Python 堆栈或直接崩溃。
        return f"list_mcp_prompts 失败：{error}"  # 新增代码+AgentPySplitPhase9: 返回清晰失败原因；若没有这行代码，模型无法判断下一步怎么修复。
    visible_prompts = prompts[:max_results]  # 新增代码+AgentPySplitPhase9: 截取最多 max_results 条 prompt；若没有这行代码，大量 prompts 可能撑爆上下文。
    if not visible_prompts:  # 新增代码+AgentPySplitPhase9: 处理没有 prompts 的情况；若没有这行代码，空结果会返回只有标题的模糊文本。
        return "list_mcp_prompts 成功：没有找到 MCP prompts。"  # 新增代码+AgentPySplitPhase9: 明确说明列表为空；若没有这行代码，模型可能误以为工具失败。
    lines = [f"list_mcp_prompts 成功：找到 {len(prompts)} 个 prompt，显示前 {len(visible_prompts)} 个。"]  # 新增代码+AgentPySplitPhase9: 构造 prompt 列表标题；若没有这行代码，模型不知道数量和截断情况。
    for index, prompt in enumerate(visible_prompts, start=1):  # 新增代码+AgentPySplitPhase9: 逐条格式化 prompt 信息；若没有这行代码，prompt 对象无法变成人类和模型可读文本。
        name = str(prompt.get("name", "") or "(无名称)")  # 新增代码+AgentPySplitPhase9: 读取 prompt 名称并兜底；若没有这行代码，模型不知道 read_mcp_prompt 要传什么 name。
        server = str(prompt.get("server", "") or "(未知 server)")  # 新增代码+AgentPySplitPhase9: 读取来源 server 并兜底；若没有这行代码，模型不知道 read_mcp_prompt 要传什么 server。
        description = str(prompt.get("description", "") or "(无说明)")  # 新增代码+AgentPySplitPhase9: 读取 prompt 说明并兜底；若没有这行代码，模型缺少判断 prompt 用途的信息。
        argument_names = mcp_prompt_argument_names(prompt)  # 新增代码+AgentPySplitPhase9: 格式化 prompt 参数名和必填性；若没有这行代码，模型不知道如何构造 prompt_arguments。
        lines.append(f"{index}. {name}")  # 新增代码+AgentPySplitPhase9: 输出 prompt 序号和名称；若没有这行代码，结果清单不易阅读。
        lines.append(f"   server：{server}")  # 新增代码+AgentPySplitPhase9: 输出读取时必需的 server；若没有这行代码，模型后续无法精确读取 prompt。
        lines.append(f"   arguments：{', '.join(argument_names) if argument_names else '(无参数)'}")  # 新增代码+AgentPySplitPhase9: 输出 prompt 参数列表；若没有这行代码，带参数 prompt 无法被正确填充。
        lines.append(f"   说明：{description}")  # 新增代码+AgentPySplitPhase9: 输出 prompt 说明；若没有这行代码，模型缺少选择 prompt 的语义依据。
    return "\n".join(lines)  # 新增代码+AgentPySplitPhase9: 返回完整 prompt 列表文本；若没有这行代码，工具无法把结果交回模型。
# 新增代码+AgentPySplitPhase9: 函数段结束，list_mcp_prompts 到此结束；若没有这行注释，用户不容易看出 prompt 列表边界。


def read_mcp_prompt(agent: Any, arguments: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase9: 函数段开始，执行内置 read_mcp_prompt 工具；若没有这段函数，模型无法从内置工具读取 MCP prompt 正文。
    if not agent.mcp_tools_enabled:  # 新增代码+AgentPySplitPhase9: 检查 MCP 是否已启动或可用；若没有这行代码，拒绝启动后仍可能尝试读取外部 prompt。
        detail = agent.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+AgentPySplitPhase9: 选择最清楚的不可用原因；若没有这行代码，返回信息会缺少排查线索。
        return f"MCP prompts 不可用：{detail}"  # 新增代码+AgentPySplitPhase9: 返回可读不可用结果；若没有这行代码，模型会把 prompt 不可用误解为未知工具。
    server_name = str(arguments.get("server", "") or "").strip()  # 新增代码+AgentPySplitPhase9: 读取并清理必填 server 参数；若没有这行代码，无法确定 prompt 来自哪个 MCP server。
    prompt_name = str(arguments.get("name", "") or "").strip()  # 新增代码+AgentPySplitPhase9: 读取并清理必填 name 参数；若没有这行代码，无法确定要读取哪个 prompt。
    if not server_name:  # 新增代码+AgentPySplitPhase9: 检查 server 是否为空；若没有这行代码，空 server 会进入 registry 并产生较难懂错误。
        return "read_mcp_prompt 失败：缺少 server 参数。"  # 新增代码+AgentPySplitPhase9: 返回清楚缺参错误；若没有这行代码，模型难以修正工具调用参数。
    if not prompt_name:  # 新增代码+AgentPySplitPhase9: 检查 prompt 名称是否为空；若没有这行代码，空名称会进入外部 server 并产生较难懂错误。
        return "read_mcp_prompt 失败：缺少 name 参数。"  # 新增代码+AgentPySplitPhase9: 返回清楚缺参错误；若没有这行代码，模型难以修正工具调用参数。
    raw_prompt_arguments = arguments.get("prompt_arguments")  # 新增代码+AgentPySplitPhase9: 读取可选 prompt_arguments 参数；若没有这行代码，带参数 prompt 无法接收模板参数。
    if raw_prompt_arguments is None:  # 新增代码+AgentPySplitPhase9: 允许模型省略 prompt_arguments；若没有这行代码，无参 prompt 可能被误判失败。
        prompt_arguments: dict[str, Any] = {}  # 新增代码+AgentPySplitPhase9: 省略时使用空字典；若没有这行代码，prompts/get 参数结构不稳定。
    elif isinstance(raw_prompt_arguments, dict):  # 新增代码+AgentPySplitPhase9: 只有对象类型才可作为 MCP prompt arguments；若没有这行代码，字符串或数组会传入外部 server 造成歧义。
        prompt_arguments = raw_prompt_arguments  # 新增代码+AgentPySplitPhase9: 使用模型传入的 prompt 参数对象；若没有这行代码，用户提供的 prompt 参数会丢失。
    else:  # 新增代码+AgentPySplitPhase9: 处理 prompt_arguments 类型不正确的情况；若没有这行代码，错误类型会进入外部 server。
        return "read_mcp_prompt 失败：prompt_arguments 必须是对象。"  # 新增代码+AgentPySplitPhase9: 返回清楚类型错误；若没有这行代码，模型难以修正参数。
    max_chars = parse_max_chars_value(arguments.get("max_chars"))  # 修改代码+AgentPySplitPhase15B2: 直接使用公共解析函数，不再反向调用 agent.py 薄包装；若没有这行代码，删除 `旧输出长度薄包装` 后 MCP prompt 读取会断开。
    permission_payload = {"server": server_name, "name": prompt_name, "prompt_arguments": prompt_arguments, "max_chars": max_chars}  # 新增代码+AgentPySplitPhase9: 构造权限提示里的参数快照；若没有这行代码，用户看不到本次读取哪个 prompt。
    action = f"读取 MCP prompt\n参数：{json.dumps(permission_payload, ensure_ascii=False, indent=2)}"  # 新增代码+AgentPySplitPhase9: 生成 prompt 读取权限说明；若没有这行代码，ask_permission 缺少可读操作描述。
    if not agent.ask_permission(action):  # 新增代码+AgentPySplitPhase9: 读取外部 MCP prompt 前请求用户确认；若没有这行代码，外部 prompt 正文会绕过权限边界。
        return f"用户拒绝了操作：{action}"  # 新增代码+AgentPySplitPhase9: 权限拒绝时返回可读结果；若没有这行代码，模型不知道 prompt 读取被拒绝。
    try:  # 新增代码+AgentPySplitPhase9: 捕获 registry 或外部 server 的 prompt 读取异常；若没有这行代码，单个 MCP prompt 失败会中断整个 agent。
        text = agent.mcp_tool_registry.read_prompt(server_name, prompt_name, prompt_arguments)  # 新增代码+AgentPySplitPhase9: 调用 registry 读取目标 prompt；若没有这行代码，权限确认后不会真正读取正文。
    except Exception as error:  # 新增代码+AgentPySplitPhase9: 把外部异常转换成可读文本；若没有这行代码，用户和模型会看到 Python 堆栈或直接崩溃。
        return f"read_mcp_prompt 失败：{error}"  # 新增代码+AgentPySplitPhase9: 返回清晰失败原因；若没有这行代码，模型无法判断下一步怎么修复。
    truncated_text = text[:max_chars]  # 新增代码+AgentPySplitPhase9: 按 max_chars 截断 prompt 正文；若没有这行代码，长 prompt 可能撑爆上下文。
    if len(text) > max_chars:  # 新增代码+AgentPySplitPhase9: 检查正文是否被截断；若没有这行代码，用户和模型不知道返回内容是否完整。
        truncated_text += "\n...[MCP prompt 内容过长，已截断]..."  # 新增代码+AgentPySplitPhase9: 添加截断提示；若没有这行代码，模型可能误以为读取了完整 prompt。
    return f"read_mcp_prompt 成功：server={server_name} name={prompt_name}\n{truncated_text}"  # 新增代码+AgentPySplitPhase9: 返回带来源和正文的结果；若没有这行代码，工具结果缺少上下文或正文。
# 新增代码+AgentPySplitPhase9: 函数段结束，read_mcp_prompt 到此结束；若没有这行注释，用户不容易看出 prompt 读取边界。


def mcp_prompt_argument_names(prompt: dict[str, Any]) -> list[str]:  # 新增代码+AgentPySplitPhase9: 函数段开始，把 prompt arguments 元数据格式化成可读参数名；若没有这段函数，list_mcp_prompts 会重复复杂解析逻辑。
    raw_arguments = prompt.get("arguments")  # 新增代码+AgentPySplitPhase9: 读取 MCP prompt 的 arguments 字段；若没有这行代码，无法展示 prompt 参数要求。
    if not isinstance(raw_arguments, list):  # 新增代码+AgentPySplitPhase9: 只处理标准数组形式参数；若没有这行代码，非数组 arguments 可能导致遍历异常。
        return []  # 新增代码+AgentPySplitPhase9: 非数组参数按无参数展示；若没有这行代码，调用方需要额外判断 None 或坏类型。
    argument_names: list[str] = []  # 新增代码+AgentPySplitPhase9: 准备保存参数名和必填性；若没有这行代码，无处累积格式化结果。
    for raw_argument in raw_arguments:  # 新增代码+AgentPySplitPhase9: 遍历每个 prompt 参数元数据；若没有这行代码，参数列表永远为空。
        if not isinstance(raw_argument, dict):  # 新增代码+AgentPySplitPhase9: 跳过非对象参数项；若没有这行代码，异常 server 返回会导致 .get 崩溃。
            continue  # 新增代码+AgentPySplitPhase9: 保持单个坏参数不影响其他参数；若没有这行代码，容错路径无法继续。
        argument_name = str(raw_argument.get("name", "") or "").strip()  # 新增代码+AgentPySplitPhase9: 读取并清理参数名；若没有这行代码，输出可能包含空白或空名称。
        if not argument_name:  # 新增代码+AgentPySplitPhase9: 跳过空参数名；若没有这行代码，输出会出现无法传入的参数提示。
            continue  # 新增代码+AgentPySplitPhase9: 继续处理其他参数；若没有这行代码，单个空参数会污染结果。
        required_label = "必填" if bool(raw_argument.get("required")) else "可选"  # 新增代码+AgentPySplitPhase9: 标出参数是否必填；若没有这行代码，模型不知道哪些 prompt_arguments 必须提供。
        argument_names.append(f"{argument_name}({required_label})")  # 新增代码+AgentPySplitPhase9: 保存格式化参数名；若没有这行代码，有效参数不会出现在列表输出。
    return argument_names  # 新增代码+AgentPySplitPhase9: 返回格式化参数列表；若没有这行代码，list_mcp_prompts 无法展示参数。
# 新增代码+AgentPySplitPhase9: 函数段结束，mcp_prompt_argument_names 到此结束；若没有这行注释，用户不容易看出 prompt 参数格式化边界。

