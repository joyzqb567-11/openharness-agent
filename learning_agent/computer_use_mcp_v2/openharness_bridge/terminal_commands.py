"""Computer Use MCP v2 终端命令桥接层。"""  # 新增代码+ComputerUseMcpV2TerminalBridge：说明本文件对应 ClaudeCode 的启动接线层；如果没有这行代码，后续读者不知道 `/computer use` 同步逻辑已经归属 v2 bridge。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2TerminalBridge：延迟解析类型注解，避免运行时提前求值；如果没有这行代码，老版本 Python 或复杂类型可能在导入阶段出错。

from typing import Any, Callable  # 新增代码+ComputerUseMcpV2TerminalBridge：导入通用类型和回调类型；如果没有这行代码，下面的 agent duck typing 和观察回调边界不清楚。

MCP_COMPUTER_USE_TOOL_PREFIX = "mcp__computer-use__"  # 新增代码+ComputerUseMcpV2TerminalBridge：集中定义 v2 MCP 工具名前缀；如果没有这行代码，stop 清理已加载工具时会散落硬编码。


# 新增代码+ComputerUseMcpV2TerminalBridge：函数段开始，_detect_terminal_mode_from_output 从真实终端输出里识别已打开的 Computer Use 模式；如果没有这段函数，交互层只能重复写脆弱的字符串判断。
def _detect_terminal_mode_from_output(computer_output: str) -> str:
    output_text = str(computer_output or "")  # 新增代码+ComputerUseMcpV2TerminalBridge：把可能为空的输出稳定转成字符串；如果没有这行代码，None 输出会让 in 判断崩溃。
    if "mode=full" in output_text or "full_mode=true" in output_text:  # 新增代码+ComputerUseMcpV2TerminalBridge：优先识别 full 模式；如果没有这行代码，最高权限桌面模式会被误记成 normal。
        return "full"  # 新增代码+ComputerUseMcpV2TerminalBridge：返回 full 模式名；如果没有这行代码，调用方无法记录真实打开的模式。
    if "mode=observe" in output_text:  # 新增代码+ComputerUseMcpV2TerminalBridge：识别只观察模式；如果没有这行代码，observe 会被误归类为 normal。
        return "observe"  # 新增代码+ComputerUseMcpV2TerminalBridge：返回 observe 模式名；如果没有这行代码，审计事件不能区分只读观察和真实操作。
    return "normal"  # 新增代码+ComputerUseMcpV2TerminalBridge：默认返回 normal 模式；如果没有这行代码，成功但没有 full/observe 标记的命令没有稳定兜底。
# 新增代码+ComputerUseMcpV2TerminalBridge：函数段结束，_detect_terminal_mode_from_output 到此结束；如果没有这个边界说明，用户不容易看出它只负责模式识别。


# 新增代码+ComputerUseMcpV2TerminalBridge：函数段开始，_safe_desktop_context 读取并规范化 agent 的桌面上下文；如果没有这段函数，activate/deactivate 会重复写类型防御逻辑。
def _safe_desktop_context(agent: Any) -> dict[str, Any]:
    desktop_context = getattr(agent, "desktop_task_context", {})  # 新增代码+ComputerUseMcpV2TerminalBridge：读取 agent 现有桌面上下文；如果没有这行代码，切换模式会丢掉 target_app_hint 等已有线索。
    if isinstance(desktop_context, dict):  # 新增代码+ComputerUseMcpV2TerminalBridge：确认上下文确实是字典；如果没有这行代码，坏状态可能在 update 时崩溃。
        return dict(desktop_context)  # 新增代码+ComputerUseMcpV2TerminalBridge：复制一份再改，避免直接改调用方持有的奇怪子类；如果没有这行代码，状态更新可能产生隐式副作用。
    return {}  # 新增代码+ComputerUseMcpV2TerminalBridge：异常类型降级为空字典；如果没有这行代码，轻量测试对象或坏缓存会阻断终端模式切换。
# 新增代码+ComputerUseMcpV2TerminalBridge：函数段结束，_safe_desktop_context 到此结束；如果没有这个边界说明，用户不容易看出它只处理上下文容器。


# 新增代码+ComputerUseMcpV2TerminalBridge：函数段开始，_record_optional_observation 把 v2 终端桥接事件写回 agent 审计流；如果没有这段函数，真实终端验收失败时缺少可排查证据。
def _record_optional_observation(record_observation: Callable[[str, dict[str, Any]], None] | None, kind: str, payload: dict[str, Any]) -> None:
    if record_observation is None:  # 新增代码+ComputerUseMcpV2TerminalBridge：允许调用方不传观察回调；如果没有这行代码，轻量测试会被迫实现完整 agent 回调。
        return  # 新增代码+ComputerUseMcpV2TerminalBridge：没有回调时静默返回；如果没有这行代码，None 会被当函数调用并崩溃。
    record_observation(kind, payload)  # 新增代码+ComputerUseMcpV2TerminalBridge：把事件交给 agent 主循环记录；如果没有这行代码，模式切换不会留下 trace。
# 新增代码+ComputerUseMcpV2TerminalBridge：函数段结束，_record_optional_observation 到此结束；如果没有这个边界说明，用户不容易看出它只做可选记录。


# 新增代码+ComputerUseMcpV2TerminalBridge：函数段开始，activate_computer_use_mode 把 `/computer use` 成功输出同步到 agent 工具池；如果没有这段函数，v2 MCP 工具虽然存在但终端模式不会让模型看到它们。
def activate_computer_use_mode(agent: Any, normalized_command: str, computer_output: str, record_observation: Callable[[str, dict[str, Any]], None] | None = None) -> dict[str, Any]:
    mode_name = _detect_terminal_mode_from_output(computer_output)  # 新增代码+ComputerUseMcpV2TerminalBridge：识别本次终端打开的模式；如果没有这行代码，后续上下文不知道写 full、observe 还是 normal。
    setattr(agent, "tool_scope_mode", "computer_use_operation")  # 新增代码+ComputerUseMcpV2TerminalBridge：把 agent 切到 Computer Use 操作工具池；如果没有这行代码，tool_search 会继续按代码模式隐藏 MCP 鼠标键盘工具。
    desktop_context = _safe_desktop_context(agent)  # 新增代码+ComputerUseMcpV2TerminalBridge：取得可安全更新的桌面上下文；如果没有这行代码，下面 update 可能撞到坏类型。
    desktop_context.update({"active": True, "requires_gui_actions": True, "terminal_mode": mode_name, "terminal_command": normalized_command, "reason": "terminal_computer_use_mode", "runtime": "computer_use_mcp_v2"})  # 新增代码+ComputerUseMcpV2TerminalBridge：写入 v2 桌面模式事实；如果没有这行代码，主循环和验收都不知道当前是 v2 Computer Use 接管。
    setattr(agent, "desktop_task_context", desktop_context)  # 新增代码+ComputerUseMcpV2TerminalBridge：把更新后的上下文写回 agent；如果没有这行代码，修改只停留在局部变量不会影响下一轮模型。
    payload = {"mode": mode_name, "tool_scope_mode": "computer_use_operation", "requires_gui_actions": True, "runtime": "computer_use_mcp_v2"}  # 新增代码+ComputerUseMcpV2TerminalBridge：整理审计 payload；如果没有这行代码，记录事件时字段会分散且容易漏。
    _record_optional_observation(record_observation, "computer_use_terminal_scope_synced", payload)  # 新增代码+ComputerUseMcpV2TerminalBridge：记录 v2 模式同步证据；如果没有这行代码，真实终端验收无法证明 agent 工具池已切换。
    return {"changed": True, "mode": mode_name, "tool_scope_mode": "computer_use_operation", "runtime": "computer_use_mcp_v2"}  # 新增代码+ComputerUseMcpV2TerminalBridge：返回结构化结果给交互层；如果没有这行代码，调用方只能靠副作用猜测是否成功。
# 新增代码+ComputerUseMcpV2TerminalBridge：函数段结束，activate_computer_use_mode 到此结束；如果没有这个边界说明，用户不容易看出它只负责打开模式的 agent 侧绑定。


# 新增代码+ComputerUseMcpV2TerminalBridge：函数段开始，deactivate_computer_use_mode 把 `/computer stop` 成功输出同步回普通工具池；如果没有这段函数，停止 full 后模型可能继续看到 Computer Use MCP 工具。
def deactivate_computer_use_mode(agent: Any, normalized_command: str, computer_output: str, record_observation: Callable[[str, dict[str, Any]], None] | None = None) -> dict[str, Any]:
    command_text = str(normalized_command or "").strip().lower()  # 新增代码+ComputerUseMcpV2TerminalBridge：规范化终端命令文本；如果没有这行代码，大小写或空白变化会让 stop 判断不稳定。
    if not (command_text == "/computer stop" or command_text == "computer stop" or command_text.startswith("/computer stop ") or command_text.startswith("computer stop ")):  # 新增代码+ComputerUseMcpV2TerminalBridge：只处理真正的 stop 命令；如果没有这行代码，status/observe 也可能错误清理工具池。
        return {"changed": False, "reason": "not_stop_command", "runtime": "computer_use_mcp_v2"}  # 新增代码+ComputerUseMcpV2TerminalBridge：非 stop 命令返回未改变；如果没有这行代码，调用方不知道该继续处理 use 加载逻辑。
    output_text = str(computer_output or "")  # 新增代码+ComputerUseMcpV2TerminalBridge：把 stop 输出转成字符串；如果没有这行代码，None 输出会让包含判断崩溃。
    if "stopped=true" not in output_text and "Computer Use Stop" not in output_text:  # 新增代码+ComputerUseMcpV2TerminalBridge：只在终端确认停止时清理 agent 状态；如果没有这行代码，失败 stop 也会错误隐藏工具。
        return {"changed": False, "reason": "stop_not_confirmed", "runtime": "computer_use_mcp_v2"}  # 新增代码+ComputerUseMcpV2TerminalBridge：stop 未确认时返回未改变；如果没有这行代码，调用方无法安全区分失败和成功。
    setattr(agent, "tool_scope_mode", "auto")  # 新增代码+ComputerUseMcpV2TerminalBridge：恢复自动工具池模式；如果没有这行代码，普通代码任务会继续被 Computer Use 工具池接管。
    desktop_context = _safe_desktop_context(agent)  # 新增代码+ComputerUseMcpV2TerminalBridge：读取可安全更新的桌面上下文；如果没有这行代码，停止清理可能撞到坏类型。
    desktop_context.update({"active": False, "requires_gui_actions": False, "terminal_mode": "stopped", "terminal_command": normalized_command, "reason": "terminal_computer_use_stopped", "runtime": "computer_use_mcp_v2"})  # 新增代码+ComputerUseMcpV2TerminalBridge：关闭 agent 内存里的桌面任务标记；如果没有这行代码，auto scope 可能继续推断为 Computer Use。
    setattr(agent, "desktop_task_context", desktop_context)  # 新增代码+ComputerUseMcpV2TerminalBridge：把关闭后的上下文写回 agent；如果没有这行代码，清理不会影响下一轮模型请求。
    loaded_tool_names = getattr(agent, "loaded_tool_names", None)  # 新增代码+ComputerUseMcpV2TerminalBridge：读取已加载工具集合；如果没有这行代码，stop 后显式 loaded 状态可能残留。
    if isinstance(loaded_tool_names, set):  # 新增代码+ComputerUseMcpV2TerminalBridge：只在字段确实是集合时清理；如果没有这行代码，轻量 fake agent 可能因为字段类型不同而崩溃。
        loaded_tool_names.difference_update(name for name in list(loaded_tool_names) if str(name).startswith(MCP_COMPUTER_USE_TOOL_PREFIX))  # 新增代码+ComputerUseMcpV2TerminalBridge：移除已加载的 v2 MCP Computer Use 工具；如果没有这行代码，stop 后工具历史仍可能影响模型工具池。
    pending_tool_names = getattr(agent, "pending_loaded_tool_names", None)  # 新增代码+ComputerUseMcpV2TerminalBridge：读取下一轮待加载工具集合；如果没有这行代码，刚 select 但未提交的 Computer Use 工具会残留。
    if isinstance(pending_tool_names, set):  # 新增代码+ComputerUseMcpV2TerminalBridge：只在字段确实是集合时清理；如果没有这行代码，测试替身缺字段时会崩溃。
        pending_tool_names.difference_update(name for name in list(pending_tool_names) if str(name).startswith(MCP_COMPUTER_USE_TOOL_PREFIX))  # 新增代码+ComputerUseMcpV2TerminalBridge：移除待加载的 v2 MCP Computer Use 工具；如果没有这行代码，stop 后下一轮仍可能加载桌面工具。
    payload = {"tool_scope_mode": "auto", "active": False, "runtime": "computer_use_mcp_v2"}  # 新增代码+ComputerUseMcpV2TerminalBridge：整理 stop 审计 payload；如果没有这行代码，记录事件字段会分散且容易漏。
    _record_optional_observation(record_observation, "computer_use_terminal_scope_reset", payload)  # 新增代码+ComputerUseMcpV2TerminalBridge：记录工具池恢复证据；如果没有这行代码，真实终端验收无法证明 stop 已回到普通边界。
    return {"changed": True, "tool_scope_mode": "auto", "active": False, "runtime": "computer_use_mcp_v2"}  # 新增代码+ComputerUseMcpV2TerminalBridge：返回结构化恢复结果；如果没有这行代码，交互层不能稳定打印 stop 同步状态。
# 新增代码+ComputerUseMcpV2TerminalBridge：函数段结束，deactivate_computer_use_mode 到此结束；如果没有这个边界说明，用户不容易看出它只负责关闭模式的 agent 侧绑定。
