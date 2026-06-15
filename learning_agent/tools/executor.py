"""工具执行分发器。"""  # 新增代码+ToolsExecutorSplit: 把 _execute_tool 的守卫和分发表从主入口拆出；若没有这个文件，执行层问题仍要翻 LearningAgent 大类。

from __future__ import annotations  # 新增代码+ToolsExecutorSplit: 延迟解析类型注解；若没有这行代码，脚本模式下导入顺序会更脆弱。

from typing import Any, Callable  # 新增代码+ToolsExecutorSplit: 执行器需要通用 agent 对象和 handler 回调类型；若没有这行代码，类型边界不清楚。

try:  # 新增代码+ToolsExecutorSplit: 包运行模式下导入工具调用数据结构；若没有这行代码，执行器无法读取 tool_call.name 和 arguments。
    from learning_agent.core import plan_runtime as plan_runtime_from_core  # 修改代码+AgentPyPhaseEPlanRuntime: 导入计划模式和 worktree 真实实现；若没有这行代码，executor 会继续反向依赖 agent.py 旧方法。
    from learning_agent.core import run_helpers as run_helpers_from_core  # 修改代码+AgentPySplitPhase15B2: 导入安全 observation helper；若没有这行代码，删除 agent.py `旧观察薄包装` 后 executor 审计事件无法写入。
    from learning_agent.core.messages import ToolCall  # 新增代码+ToolsExecutorSplit: 导入统一 ToolCall 类型；若没有这行代码，执行器会和主循环使用不同调用对象。
except ModuleNotFoundError as error:  # 新增代码+ToolsExecutorSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages", "learning_agent.core.plan_runtime", "learning_agent.core.run_helpers"}:  # 修改代码+AgentPyPhaseEPlanRuntime: 允许 plan_runtime 路径差异进入脚本 fallback；若没有这行代码，bat 入口可能误报导入失败。
        raise  # 新增代码+ToolsExecutorSplit: 重新抛出真实导入错误；若没有这行代码，排查 executor 问题会很困难。
    from core import plan_runtime as plan_runtime_from_core  # 修改代码+AgentPyPhaseEPlanRuntime: 脚本模式下导入计划模式和 worktree 真实实现；若没有这行代码，直接运行时计划工具分发会找不到模块。
    from core import run_helpers as run_helpers_from_core  # 修改代码+AgentPySplitPhase15B2: 脚本模式下导入安全 observation helper；若没有这行代码，直接运行时工具执行审计会找不到 helper。
    from core.messages import ToolCall  # 新增代码+ToolsExecutorSplit: 脚本模式下导入 ToolCall；若没有这行代码，直接执行时工具执行器无法工作。

try:  # 新增代码+Stage15E: 包运行模式下导入工具 hook 管理器和事件；若没有这行代码，executor v2 无法运行 pre/post/denied/error hook。
    from learning_agent.tools.hooks import ToolHookEvent, ToolHookManager  # 新增代码+Stage15E: 导入 hook 事件和管理器；若没有这行代码，执行器只能记录文本而不能运行扩展点。
except ModuleNotFoundError as error:  # 新增代码+Stage15E: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.hooks"}:  # 新增代码+Stage15E: 只允许目标包路径缺失时 fallback；若没有这行代码，hook 内部真实错误会被误吞。
        raise  # 新增代码+Stage15E: 重新抛出真实导入错误；若没有这行代码，排查 hook 问题会很困难。
    from tools.hooks import ToolHookEvent, ToolHookManager  # 新增代码+Stage15E: 脚本模式下从同目录 tools 包导入 hook 类型；若没有这行代码，直接执行 learning_agent.py 时 hook 不可用。

try:  # 新增代码+Stage15E: 包运行模式下导入统一权限决策函数；若没有这行代码，executor v2 无法产生结构化 permission_decided 事件。
    from learning_agent.tools.permissions import ToolPermissionDecision, decide_tool_permission  # 新增代码+Stage15E: 导入权限决策对象和 helper；若没有这行代码，执行器无法统一判断 allow/deny/ask。
except ModuleNotFoundError as error:  # 新增代码+Stage15E: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.permissions"}:  # 新增代码+Stage15E: 只允许目标包路径缺失时 fallback；若没有这行代码，permissions 内部真实错误会被误吞。
        raise  # 新增代码+Stage15E: 重新抛出真实导入错误；若没有这行代码，排查权限模块问题会很困难。
    from tools.permissions import ToolPermissionDecision, decide_tool_permission  # 新增代码+Stage15E: 脚本模式下导入权限 helper；若没有这行代码，直接执行时 executor v2 权限层不可用。


try:  # 修改代码+AgentPySplitPhase15B1: 让工具分发器直接导入 LSP/REPL 新模块；如果没有这行代码，删除 agent.py 里的 LSP/REPL 薄包装后工具路由会断开。
    import learning_agent.tools.lsp_repl_tools as lsp_repl_tools_from_tools  # 修改代码+AgentPySplitPhase15B1: 包运行模式下读取真正的 LSP/REPL 实现；如果没有这行代码，python -m 运行时 executor 找不到新模块入口。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase15B1: 兼容 start_oauth_agent.bat 这类直接脚本运行方式；如果没有这行代码，脚本模式下包名缺失会直接启动失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.lsp_repl_tools"}:  # 修改代码+AgentPySplitPhase15B1: 只允许包路径缺失时 fallback；如果没有这行代码，LSP/REPL 模块内部真实 bug 会被误吞。
        raise  # 修改代码+AgentPySplitPhase15B1: 重新抛出真实导入错误；如果没有这行代码，排查 executor 迁移问题会被伪装成脚本模式兼容问题。
    import tools.lsp_repl_tools as lsp_repl_tools_from_tools  # 修改代码+AgentPySplitPhase15B1: 脚本模式下从同级 tools 包导入 LSP/REPL 实现；如果没有这行代码，bat 入口调用 lsp/repl 会找不到实现。

try:  # 修改代码+AgentPySplitPhase15B9: 让工具执行器直接导入 MCP 适配层；若没有这行代码，删除 agent.py 的 MCP 薄包装后 MCP 工具分发会断开。
    import learning_agent.mcp.agent_adapter as mcp_agent_adapter_from_mcp  # 修改代码+AgentPySplitPhase15B9: 包运行模式下读取 MCP 的真实执行、resource、prompt 和 stream 入口；若没有这行代码，executor 仍会反向依赖 agent.py 旧方法。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase15B9: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致启动失败。
    if error.name not in {"learning_agent", "learning_agent.mcp", "learning_agent.mcp.agent_adapter"}:  # 修改代码+AgentPySplitPhase15B9: 只把包路径差异当作 fallback 条件；若没有这行代码，MCP 模块内部真实导入错误会被误判为兼容问题。
        raise  # 修改代码+AgentPySplitPhase15B9: 重新抛出真正的 MCP 导入错误；若没有这行代码，后续排查会看不到原始异常。
    import mcp.agent_adapter as mcp_agent_adapter_from_mcp  # 修改代码+AgentPySplitPhase15B9: 脚本模式下从同级 mcp 包读取同一个适配层；若没有这行代码，bat 入口无法使用拆出的 MCP 实现。

try:  # 修改代码+AgentPySplitPhase15B10: 让工具执行器直接导入 task/team/cron/monitor 实现模块；若没有这行代码，删除 agent.py 任务薄包装后分发表会找不到真实实现。
    import learning_agent.tasks.agent_tools as tasks_agent_tools_from_tasks  # 修改代码+AgentPySplitPhase15B10: 包运行模式下读取任务、团队、定时和监控工具入口；若没有这行代码，python -m 运行时 task 工具会继续依赖旧 agent 方法。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase15B10: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致启动失败。
    if error.name not in {"learning_agent", "learning_agent.tasks", "learning_agent.tasks.agent_tools"}:  # 修改代码+AgentPySplitPhase15B10: 只允许路径模式差异进入 fallback；若没有这行代码，tasks 模块内部真实导入错误会被误吞。
        raise  # 修改代码+AgentPySplitPhase15B10: 重新抛出真正的 tasks 导入错误；若没有这行代码，后续排查会看不到原始异常。
    import tasks.agent_tools as tasks_agent_tools_from_tasks  # 修改代码+AgentPySplitPhase15B10: 脚本模式下从同级 tasks 包读取同一组实现；若没有这行代码，bat 入口调用 task/team/cron/monitor 会找不到实现。

try:  # 修改代码+AgentPyPhaseCSkillRuntime: 让工具执行器直接导入 skill runtime；若没有这行代码，删除 agent.py skill 真实实现后分发表会找不到真实实现。
    import learning_agent.skills.runtime as skills_runtime_from_skills  # 修改代码+AgentPyPhaseCSkillRuntime: 包运行模式下读取 skill_list/skill_load 真实实现；若没有这行代码，python -m 运行时 skill 工具会继续依赖旧 agent 方法。
except ModuleNotFoundError as error:  # 修改代码+AgentPyPhaseCSkillRuntime: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致启动失败。
    if error.name not in {"learning_agent", "learning_agent.skills", "learning_agent.skills.runtime"}:  # 修改代码+AgentPyPhaseCSkillRuntime: 只允许路径模式差异进入 fallback；若没有这行代码，skill runtime 内部真实错误会被误吞。
        raise  # 修改代码+AgentPyPhaseCSkillRuntime: 重新抛出真正的 skill runtime 导入错误；若没有这行代码，后续排查会看不到根因。
    import skills.runtime as skills_runtime_from_skills  # 修改代码+AgentPyPhaseCSkillRuntime: 脚本模式下从同级 skills 目录读取同一个 skill runtime；若没有这行代码，bat 入口调用 skill 工具会找不到实现。

try:  # 修改代码+AgentPyPhaseDReportTools: 让工具执行器直接导入 prompt/token 报告工具；若没有这行代码，删除 agent.py 报告真实实现后分发表会找不到真实实现。
    import learning_agent.prompts.report_tools as report_tools_from_prompts  # 修改代码+AgentPyPhaseDReportTools: 包运行模式下读取 prompt_surface_report/token_budget_report 真实实现；若没有这行代码，python -m 运行时报告工具会继续依赖旧 agent 方法。
except ModuleNotFoundError as error:  # 修改代码+AgentPyPhaseDReportTools: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致启动失败。
    if error.name not in {"learning_agent", "learning_agent.prompts", "learning_agent.prompts.report_tools"}:  # 修改代码+AgentPyPhaseDReportTools: 只允许路径模式差异进入 fallback；若没有这行代码，report_tools 内部真实错误会被误吞。
        raise  # 修改代码+AgentPyPhaseDReportTools: 重新抛出真正的 report_tools 导入错误；若没有这行代码，后续排查会看不到根因。
    import prompts.report_tools as report_tools_from_prompts  # 修改代码+AgentPyPhaseDReportTools: 脚本模式下从同级 prompts 包读取同一个报告实现；若没有这行代码，bat 入口调用报告工具会找不到实现。

try:  # 修改代码+AgentPyPhaseDStatusTools: 让工具执行器直接导入状态查询工具；若没有这行代码，删除 agent.py 状态真实实现后分发表会找不到真实实现。
    import learning_agent.observability.status_tools as status_tools_from_observability  # 修改代码+AgentPyPhaseDStatusTools: 包运行模式下读取 status/run/session/health 工具真实实现；若没有这行代码，python -m 运行时状态工具会继续依赖旧 agent 方法。
except ModuleNotFoundError as error:  # 修改代码+AgentPyPhaseDStatusTools: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致启动失败。
    if error.name not in {"learning_agent", "learning_agent.observability", "learning_agent.observability.status_tools"}:  # 修改代码+AgentPyPhaseDStatusTools: 只允许路径模式差异进入 fallback；若没有这行代码，status_tools 内部真实错误会被误吞。
        raise  # 修改代码+AgentPyPhaseDStatusTools: 重新抛出真正的 status_tools 导入错误；若没有这行代码，后续排查会看不到根因。
    import observability.status_tools as status_tools_from_observability  # 修改代码+AgentPyPhaseDStatusTools: 脚本模式下从同级 observability 包读取同一个状态实现；若没有这行代码，bat 入口调用状态工具会找不到实现。
try:  # 修改代码+AgentPySplitPhase15B11: 让工具执行器直接导入本地文件、Notebook 和后台命令实现；若没有这行代码，删除 agent.py 本组薄包装后 read/write/notebook/background 工具会断开。
    import learning_agent.runtime.background_commands as background_commands_from_runtime  # 修改代码+AgentPySplitPhase15B11: 包运行模式下读取后台命令运行时入口；若没有这行代码，start/read/stop 后台命令仍会反向依赖 agent.py 旧方法。
    import learning_agent.tools.atom_tools as atom_tools_from_tools  # 修改代码+AgentPyPhaseGAtomTools: 包运行模式下读取 read/write/edit/bash 真实实现；若没有这行代码，executor 仍会反向依赖 agent.py 旧方法。
    import learning_agent.tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 包运行模式下读取工具目录和策略真实实现；若没有这行代码，executor 守卫仍会反向依赖 agent.py 薄包装。
    import learning_agent.tools.tool_scope as tool_scope_from_tools  # 新增代码+ComputerUseMcpV2LegacyBlock：导入统一工具池隔离规则；如果没有这行代码，executor 无法硬阻断旧 Computer Use 内置入口。
    import learning_agent.tools.local_file_tools as local_file_tools_from_tools  # 修改代码+AgentPySplitPhase15B11: 包运行模式下读取本地文件、memory 和 todo 工具入口；若没有这行代码，read_file/write_file 等工具删除旧入口后会变成未知路径。
    import learning_agent.tools.notebook_tools as notebook_tools_from_tools  # 修改代码+AgentPySplitPhase15B11: 包运行模式下读取 Notebook 工具入口；若没有这行代码，notebook_read/notebook_edit 删除旧入口后无法执行。
except ModuleNotFoundError as error:  # 修改代码+AgentPySplitPhase15B11: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致启动失败。
    if error.name not in {"learning_agent", "learning_agent.runtime", "learning_agent.runtime.background_commands", "learning_agent.tools", "learning_agent.tools.atom_tools", "learning_agent.tools.catalog_runtime", "learning_agent.tools.tool_scope", "learning_agent.tools.local_file_tools", "learning_agent.tools.notebook_tools"}:  # 修改代码+ComputerUseMcpV2LegacyBlock：允许 tool_scope 路径差异进入 fallback；若没有这行代码，bat 入口可能把路径模式误判成真实错误。
        raise  # 修改代码+AgentPySplitPhase15B11: 重新抛出非路径类导入错误；若没有这行代码，后续排查会被错误 fallback 遮住根因。
    import runtime.background_commands as background_commands_from_runtime  # 修改代码+AgentPySplitPhase15B11: 脚本模式下从同级 runtime 包读取后台命令实现；若没有这行代码，bat 入口调用后台命令会找不到拆出的模块。
    import tools.atom_tools as atom_tools_from_tools  # 修改代码+AgentPyPhaseGAtomTools: 脚本模式下读取 read/write/edit/bash 真实实现；若没有这行代码，bat 入口调用四原子工具会断开。
    import tools.catalog_runtime as catalog_runtime_from_tools  # 修改代码+AgentPyPhaseHMcpToolRuntime: 脚本模式下读取工具目录和策略真实实现；若没有这行代码，bat 入口的执行守卫会断开。
    import tools.tool_scope as tool_scope_from_tools  # 新增代码+ComputerUseMcpV2LegacyBlock：脚本模式导入统一工具池隔离规则；如果没有这行代码，start_oauth_agent.bat 无法硬阻断旧 Computer Use 内置入口。
    import tools.local_file_tools as local_file_tools_from_tools  # 修改代码+AgentPySplitPhase15B11: 脚本模式下从同级 tools 包读取本地文件工具实现；若没有这行代码，bat 入口调用 read/write/todo/memory 会失败。
    import tools.notebook_tools as notebook_tools_from_tools  # 修改代码+AgentPySplitPhase15B11: 脚本模式下从同级 tools 包读取 Notebook 工具实现；若没有这行代码，bat 入口调用 notebook 工具会失败。

try:  # 修改代码+ComputerUseMcpV2LegacyBlock：让工具执行器只导入 Computer Use 调试工具；若没有这行代码，debug 模式可见 read_trace/read_state 但无法执行。
    import learning_agent.computer_use_mcp_v2.windows_runtime.debug_tools as computer_use_debug_tools_from_v2  # 修改代码+ComputerUseMcpV2ResidualCleanup：包运行模式下读取 v2 Computer Use 调试工具实现；如果没有这一行，read_trace/read_state 等 debug schema 会变成未知工具。
except ModuleNotFoundError as error:  # 修改代码+ComputerUseMcpV2LegacyBlock：兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致启动失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.debug_tools"}:  # 修改代码+ComputerUseMcpV2LegacyBlock：只允许 debug_tools 路径差异进入脚本 fallback；如果没有这一行，内部真实导入错误会被误吞。
        raise  # 修改代码+AgentPySplitPhase15B12: 重新抛出真正的 Computer Use 导入错误；若没有这行代码，后续排查会看不到根因。
    import computer_use_mcp_v2.windows_runtime.debug_tools as computer_use_debug_tools_from_v2  # 修改代码+ComputerUseMcpV2ResidualCleanup：脚本模式下读取 v2 Computer Use 调试工具实现；如果没有这一行，start_oauth_agent.bat 无法执行 read_trace/read_state。

try:  # 修改代码+AgentPyPhaseBToolSearch: 让工具执行器直接导入 tool_search 真实实现；若没有这行代码，executor 仍会反向依赖 agent.py 搜索方法。
    import learning_agent.tools.search as search_tools_from_tools  # 修改代码+AgentPyPhaseBToolSearch: 包运行模式下读取 tools/search.py；若没有这行代码，python -m 运行时 tool_search 路由无法直连新模块。
except ModuleNotFoundError as error:  # 修改代码+AgentPyPhaseBToolSearch: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，脚本模式下包名前缀缺失会导致启动失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.search"}:  # 修改代码+AgentPyPhaseBToolSearch: 只允许路径模式差异进入 fallback；若没有这行代码，search 模块内部真实错误会被误吞。
        raise  # 修改代码+AgentPyPhaseBToolSearch: 重新抛出真正的 search 导入错误；若没有这行代码，后续排查会看不到根因。
    import tools.search as search_tools_from_tools  # 修改代码+AgentPyPhaseBToolSearch: 脚本模式下从同级 tools 包读取同一个搜索实现；若没有这行代码，bat 入口调用 tool_search 会找不到实现。

ToolHandler = Callable[[dict[str, Any]], str]  # 新增代码+ToolsExecutorSplit: 定义具体工具 handler 的统一签名；若没有这行代码，分发表类型会难以阅读。


def _record_executor_observation(agent: Any, kind: str, payload: dict[str, Any]) -> None:  # 新增代码+Stage15E: 安全写入执行器观察事件；若没有这行代码，fake agent 或老调用方缺少 旧观察薄包装 时会崩溃。
    run_helpers_from_core.safe_record_observation(agent, kind, payload)  # 修改代码+AgentPySplitPhase15B2: 使用 core 安全记录入口替代动态读取旧方法；若没有这行代码，删除 `旧观察薄包装` 后权限和 hook 生命周期不可审计。


def _get_tool_hook_manager(agent: Any) -> ToolHookManager | None:  # 新增代码+Stage15E: 读取 agent 上挂载的 hook 管理器；若没有这行代码，执行器无法支持可选 hook。
    manager = getattr(agent, "tool_hooks", None)  # 新增代码+Stage15E: 从 agent 取 hook 管理器；若没有这行代码，调用方无法注入自定义 hook。
    return manager if isinstance(manager, ToolHookManager) else None  # 新增代码+Stage15E: 只接受正确类型的管理器；若没有这行代码，错误对象可能在 run_hooks 处崩溃。


def _run_tool_hooks(agent: Any, hook_name: str, event: ToolHookEvent) -> str | None:  # 新增代码+Stage15E: 统一记录并运行某个阶段的 hook；若没有这行代码，pre/post/denied/error 会各写各的异常处理。
    _record_executor_observation(agent, hook_name, event.to_payload())  # 新增代码+Stage15E: 先记录 hook 阶段事件；若没有这行代码，即使没有注册 hook 也看不到生命周期节点。
    manager = _get_tool_hook_manager(agent)  # 新增代码+Stage15E: 获取可选 hook 管理器；若没有这行代码，注册的 hook 不会执行。
    if manager is None:  # 新增代码+Stage15E: 没有 hook 管理器时正常跳过；若没有这行代码，默认 agent 会因为未注册 hook 而失败。
        return None  # 新增代码+Stage15E: 无 hook 错误时返回 None；若没有这行代码，调用方无法区分正常和失败。
    errors = manager.run_hooks(hook_name, event)  # 新增代码+Stage15E: 运行该阶段全部 hook；若没有这行代码，扩展点只记录不执行。
    if not errors:  # 新增代码+Stage15E: 没有 hook 错误时继续执行；若没有这行代码，正常 hook 会被误判失败。
        return None  # 新增代码+Stage15E: 返回 None 表示无错误；若没有这行代码，调用方会收到空错误文本。
    error_text = "; ".join(errors)  # 新增代码+Stage15E: 合并多个 hook 错误；若没有这行代码，多个失败原因无法展示。
    _record_executor_observation(agent, "tool_error", {"tool_name": event.tool_name, "call_id": event.call_id, "hook_name": hook_name, "error": error_text})  # 新增代码+Stage15E: 把 hook 异常转成工具错误事件；若没有这行代码，hook 报错缺少审计证据。
    return f"{event.tool_name} tool hook 失败：{hook_name}: {error_text}"  # 新增代码+Stage15E: 返回可读错误给模型；若没有这行代码，hook 异常可能变成裸 Python 错误。


def _record_permission_decision(agent: Any, tool_call: ToolCall, decision: ToolPermissionDecision) -> None:  # 新增代码+Stage15E: 统一记录权限决策事件；若没有这行代码，权限判断缺少结构化审计。
    _record_executor_observation(agent, "permission_decided", {"tool_name": tool_call.name, "call_id": tool_call.call_id, "status": decision.status, "allowed": decision.allowed, "reason": decision.reason})  # 新增代码+Stage15E: 写入 allow/deny/ask/auto_allow 决策；若没有这行代码，后续无法复盘工具为何执行或拒绝。


def _permission_denied_message(agent: Any, tool_call: ToolCall, decision: ToolPermissionDecision) -> str:  # 新增代码+Stage15E: 统一处理权限拒绝事件和返回文本；若没有这行代码，每个拒绝分支会格式不一致。
    event = ToolHookEvent(tool_name=tool_call.name, call_id=tool_call.call_id, arguments=tool_call.arguments, permission_status=decision.status, error_text=decision.reason)  # 新增代码+Stage15E: 构造权限拒绝 hook 事件；若没有这行代码，permission_denied hook 看不到上下文。
    _run_tool_hooks(agent, "permission_denied", event)  # 新增代码+Stage15E: 记录并运行拒绝 hook；若没有这行代码，权限拒绝无法触发审计或 UI 扩展。
    return f"{tool_call.name} 权限拒绝：{decision.reason}"  # 新增代码+Stage15E: 返回清楚拒绝说明；若没有这行代码，模型不知道工具没有执行的原因。


def _dispatch_tool_call(agent: Any, tool_call: ToolCall) -> str:  # 新增代码+Stage15E: 把具体工具分发从 executor v2 生命周期中拆出；若没有这行代码，hook 包裹逻辑和分发表会混在一起。
    handler = _builtin_tool_handlers(agent).get(tool_call.name)  # 新增代码+Stage15E: 从内置分发表查找工具实现；若没有这行代码，内置工具无法分发。
    if handler is not None:  # 新增代码+Stage15E: 命中内置工具时执行；若没有这行代码，找到 handler 后仍会落到未知工具。
        return handler(tool_call.arguments)  # 新增代码+Stage15E: 把模型参数传给具体工具实现；若没有这行代码，内置工具不会真正运行。
    if tool_call.name.startswith("mcp__") and not agent.mcp_tools_enabled:  # 修改代码+McpImageReinjection: MCP 被拒绝或启动失败时先区分内部 Computer Use MCP 和外部 MCP；若没有这行代码，外部 registry route 可能绕过启动权限继续调用。
        if mcp_agent_adapter_from_mcp.is_computer_use_mcp_tool_call_name(tool_call.name):  # 修改代码+McpImageReinjection: Computer Use MCP 是 agent-side 内部绑定，可在 registry 未启动时继续走本地 adapter；如果没有这行代码，单元测试和内部模式会把 mcp__computer-use__observe 当成不可用。
            return mcp_agent_adapter_from_mcp.execute_mcp_tool(agent, tool_call)  # 修改代码+McpImageReinjection: 直接进入 Computer Use session adapter；如果没有这行代码，模型可见 MCP observe 无法复用旧截图和 artifact 链。
        detail = agent.mcp_start_error or "MCP 工具尚未启用。"  # 新增代码+Stage15E: 选择最清楚的不可用原因；若没有这行代码，返回信息会缺少排查线索。
        return f"MCP 工具不可用：{detail}"  # 新增代码+Stage15E: 返回可读不可用结果给模型；若没有这行代码，模型会把禁用 MCP 误解为未知工具。
    if agent.mcp_tool_registry.has_tool(tool_call.name) or mcp_agent_adapter_from_mcp.is_computer_use_mcp_tool_call_name(tool_call.name):  # 修改代码+McpImageReinjection: registry 工具和内部 Computer Use MCP 工具都进入 MCP adapter；如果没有这行代码，未登记到 registry 的 agent-side Computer Use 工具会被当成未知工具。
        return mcp_agent_adapter_from_mcp.execute_mcp_tool(agent, tool_call)  # 修改代码+AgentPySplitPhase15B9: 直接调用 MCP 适配层执行外部工具；若没有这行代码，删除 agent.py 旧 MCP 薄包装后外部工具会变成 AttributeError。
    _record_executor_observation(agent, "tool_error", {"tool_name": tool_call.name, "call_id": tool_call.call_id, "error": "unknown tool"})  # 新增代码+Stage15E: 记录未知工具错误事件；若没有这行代码，未知工具失败不可审计。
    return f"未知工具：{tool_call.name}"  # 新增代码+Stage15E: 未知工具返回错误给模型；若没有这行代码，模型无法知道工具名写错。


def _builtin_tool_handlers(agent: Any) -> dict[str, ToolHandler]:  # 新增代码+ToolsExecutorSplit: 构建内置工具名到 agent 方法的分发表；若没有这行代码，execute_tool 只能继续写长 if 链。
    return {  # 新增代码+ToolsExecutorSplit: 返回新的分发表字典；若没有这行代码，执行器没有路由依据。
        "read": lambda arguments: atom_tools_from_tools.read_atom(agent, arguments),  # 修改代码+AgentPyPhaseGAtomTools: executor 直接路由到 atom_tools 的 read 实现；若没有这行代码，read 仍会反向依赖 agent.py。
        "write": lambda arguments: atom_tools_from_tools.write_atom(agent, arguments),  # 修改代码+AgentPyPhaseGAtomTools: executor 直接路由到 atom_tools 的 write 实现；若没有这行代码，write 仍会反向依赖 agent.py。
        "edit": lambda arguments: atom_tools_from_tools.edit_atom(agent, arguments),  # 修改代码+AgentPyPhaseGAtomTools: executor 直接路由到 atom_tools 的 edit 实现；若没有这行代码，edit 仍会反向依赖 agent.py。
        "bash": lambda arguments: atom_tools_from_tools.bash_atom(agent, arguments),  # 修改代码+AgentPyPhaseGAtomTools: executor 直接路由到 atom_tools 的 bash 实现；若没有这行代码，bash 仍会反向依赖 agent.py。
        "read_file": lambda arguments: local_file_tools_from_tools.read_file(agent, arguments),  # 修改代码+AgentPySplitPhase15B11: 直接路由到本地文件模块读取文件；若没有这行代码，删除 agent.py 的 _read_file 后 read_file 工具会断开。
        "write_file": lambda arguments: local_file_tools_from_tools.write_file(agent, arguments),  # 修改代码+AgentPySplitPhase15B11: 直接路由到本地文件模块写文件；若没有这行代码，删除 agent.py 的 _write_file 后 write_file 工具会断开。
        "append_memory": lambda arguments: local_file_tools_from_tools.append_memory(agent, arguments),  # 修改代码+AgentPySplitPhase15B11: 直接路由到本地文件模块追加记忆；若没有这行代码，删除 agent.py 的 _append_memory 后长期记忆工具会断开。
        "todo_read": lambda arguments: local_file_tools_from_tools.todo_read(agent, arguments),  # 修改代码+AgentPySplitPhase15B11: 直接路由到本地文件模块读取 todo；若没有这行代码，删除 agent.py 的 _todo_read 后长任务清单无法恢复。
        "todo_write": lambda arguments: local_file_tools_from_tools.todo_write(agent, arguments),  # 修改代码+AgentPySplitPhase15B11: 直接路由到本地文件模块写入 todo；若没有这行代码，删除 agent.py 的 _todo_write 后长任务清单无法保存。
        "start_background_command": lambda arguments: background_commands_from_runtime.start_background_command(agent, arguments),  # 修改代码+AgentPySplitPhase15B11: 直接路由到 runtime 后台命令启动入口；若没有这行代码，删除 agent.py 的 _start_background_command 后后台任务无法启动。
        "read_background_command": lambda arguments: background_commands_from_runtime.read_background_command(agent, arguments),  # 修改代码+AgentPySplitPhase15B11: 直接路由到 runtime 后台输出读取入口；若没有这行代码，删除 agent.py 的 _read_background_command 后模型无法观察后台输出。
        "stop_background_command": lambda arguments: background_commands_from_runtime.stop_background_command(agent, arguments),  # 修改代码+AgentPySplitPhase15B11: 直接路由到 runtime 后台停止入口；若没有这行代码，删除 agent.py 的 _stop_background_command 后后台进程可能无法收束。
        "notebook_read": lambda arguments: notebook_tools_from_tools.notebook_read(agent, arguments),  # 修改代码+AgentPySplitPhase15B11: 直接路由到 Notebook 模块读取 cell；若没有这行代码，删除 agent.py 的 _notebook_read 后 notebook_read 会断开。
        "notebook_edit": lambda arguments: notebook_tools_from_tools.notebook_edit(agent, arguments),  # 修改代码+AgentPySplitPhase15B11: 直接路由到 Notebook 模块编辑 cell；若没有这行代码，删除 agent.py 的 _notebook_edit 后 notebook_edit 会断开。
        "tool_search": lambda arguments: search_tools_from_tools.tool_search(agent, arguments),  # 修改代码+AgentPyPhaseBToolSearch: executor 直接路由到 tools/search.py 真实实现；若没有这行代码，agent.py 仍会承担 tool_search 能力实现。
        "prompt_surface_report": lambda arguments: report_tools_from_prompts.prompt_surface_report(agent, arguments),  # 修改代码+AgentPyPhaseDReportTools: executor 直接路由到 prompts/report_tools.py 提示词表面报告；若没有这行代码，agent.py 仍会承担 prompt_surface_report 能力实现。
        "token_budget_report": lambda arguments: report_tools_from_prompts.token_budget_report(agent, arguments),  # 修改代码+AgentPyPhaseDReportTools: executor 直接路由到 prompts/report_tools.py token 预算报告；若没有这行代码，agent.py 仍会承担 token_budget_report 能力实现。
        "status_snapshot": lambda arguments: status_tools_from_observability.status_snapshot(agent, arguments),  # 修改代码+AgentPyPhaseDStatusTools: executor 直接路由到 observability/status_tools.py 状态快照；若没有这行代码，agent.py 仍会承担 status_snapshot 能力实现。
        "task_status": lambda arguments: status_tools_from_observability.task_status(agent, arguments),  # 修改代码+AgentPyPhaseDStatusTools: executor 直接路由到任务状态查询模块；若没有这行代码，agent.py 仍会承担 task_status 能力实现。
        "session_list": lambda arguments: status_tools_from_observability.session_list(agent, arguments),  # 修改代码+AgentPyPhaseDStatusTools: executor 直接路由到 session 列表模块；若没有这行代码，agent.py 仍会承担 session_list 能力实现。
        "session_resume": lambda arguments: status_tools_from_observability.session_resume(agent, arguments),  # 修改代码+AgentPyPhaseDStatusTools: executor 直接路由到 session 恢复模块；若没有这行代码，agent.py 仍会承担 session_resume 能力实现。
        "compact_status": lambda arguments: status_tools_from_observability.compact_status(agent, arguments),  # 修改代码+AgentPyPhaseDStatusTools: executor 直接路由到 compact 状态模块；若没有这行代码，agent.py 仍会承担 compact_status 能力实现。
        "event_tail": lambda arguments: status_tools_from_observability.event_tail(agent, arguments),  # 修改代码+AgentPyPhaseDStatusTools: executor 直接路由到状态事件尾部模块；若没有这行代码，agent.py 仍会承担 event_tail 能力实现。
        "resume_report": lambda arguments: status_tools_from_observability.resume_report(agent, arguments),  # 修改代码+AgentPyPhaseDStatusTools: executor 直接路由到恢复审计报告模块；若没有这行代码，agent.py 仍会承担 resume_report 能力实现。
        "run_status": lambda arguments: status_tools_from_observability.run_status(agent, arguments),  # 修改代码+AgentPyPhaseDStatusTools: executor 直接路由到 run 状态模块；若没有这行代码，agent.py 仍会承担 run_status 能力实现。
        "health_status": lambda arguments: status_tools_from_observability.health_status(agent, arguments),  # 修改代码+AgentPyPhaseDStatusTools: executor 直接路由到健康状态模块；若没有这行代码，agent.py 仍会承担 health_status 能力实现。
        "read_trace": lambda arguments: computer_use_debug_tools_from_v2.read_trace(agent, arguments),  # 修改代码+ComputerUseMcpV2ResidualCleanup：路由 v2 Computer Use trace 读取工具；如果没有这一行，debug 模式可见 read_trace 但执行时会变成未知工具。
        "read_state": lambda arguments: computer_use_debug_tools_from_v2.read_state(agent, arguments),  # 修改代码+ComputerUseMcpV2ResidualCleanup：路由 v2 Computer Use 状态读取工具；如果没有这一行，debug 模式无法读取当前工具作用域和事件数量。
        "read_last_observation": lambda arguments: computer_use_debug_tools_from_v2.read_last_observation(agent, arguments),  # 修改代码+ComputerUseMcpV2ResidualCleanup：路由 v2 最近 observation 读取工具；如果没有这一行，debug 模式无法按 kind 查看最近审计事件。
        "read_last_action_result": lambda arguments: computer_use_debug_tools_from_v2.read_last_action_result(agent, arguments),  # 修改代码+ComputerUseMcpV2ResidualCleanup：路由 v2 最近动作结果读取工具；如果没有这一行，debug 模式无法快速检查上一步桌面动作结果。
        "assert_last_action": lambda arguments: computer_use_debug_tools_from_v2.assert_last_action(agent, arguments),  # 修改代码+ComputerUseMcpV2ResidualCleanup：路由 v2 最近动作断言工具；如果没有这一行，debug 模式无法用工具层验证动作是否符合预期。
        "list_mcp_resources": lambda arguments: mcp_agent_adapter_from_mcp.list_mcp_resources(agent, arguments),  # 修改代码+AgentPySplitPhase15B9: 直接路由到 MCP resource 列表模块；若没有这行代码，删除 agent.py 旧列表入口后模型无法发现外部资源。
        "read_mcp_resource": lambda arguments: mcp_agent_adapter_from_mcp.read_mcp_resource(agent, arguments),  # 修改代码+AgentPySplitPhase15B9: 直接路由到 MCP resource 读取模块；若没有这行代码，删除 agent.py 旧读取入口后模型无法读取外部资源正文。
        "list_mcp_prompts": lambda arguments: mcp_agent_adapter_from_mcp.list_mcp_prompts(agent, arguments),  # 修改代码+AgentPySplitPhase15B9: 直接路由到 MCP prompt 列表模块；若没有这行代码，删除 agent.py 旧 prompt 列表入口后模型无法发现外部 prompt。
        "read_mcp_prompt": lambda arguments: mcp_agent_adapter_from_mcp.read_mcp_prompt(agent, arguments),  # 修改代码+AgentPySplitPhase15B9: 直接路由到 MCP prompt 读取模块；若没有这行代码，删除 agent.py 旧 prompt 读取入口后模型无法加载 prompt 正文。
        "listen_mcp_stream": lambda arguments: mcp_agent_adapter_from_mcp.listen_mcp_stream(agent, arguments),  # 修改代码+AgentPySplitPhase15B9: 直接路由到 MCP stream 监听模块；若没有这行代码，删除 agent.py 旧 stream 入口后模型无法读取流式外部状态。
        "skill_list": lambda arguments: skills_runtime_from_skills.skill_list(agent, arguments),  # 修改代码+AgentPyPhaseCSkillRuntime: executor 直接路由到 skills/runtime.py 列表实现；若没有这行代码，agent.py 仍会承担 skill_list 能力实现。
        "skill_load": lambda arguments: skills_runtime_from_skills.skill_load(agent, arguments),  # 修改代码+AgentPyPhaseCSkillRuntime: executor 直接路由到 skills/runtime.py 加载实现；若没有这行代码，agent.py 仍会承担 skill_load 能力实现。
        "ask_user_question": agent._ask_user_question,  # 新增代码+ToolsExecutorSplit: 路由结构化提问工具；若没有这行代码，模型无法输出稳定澄清问题。
        "task": lambda arguments: tasks_agent_tools_from_tasks.task(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的子 agent 委派入口；若没有这行代码，删除 agent.py 旧 task 方法后主 agent 无法拆分复杂任务。
        "task_output": lambda arguments: tasks_agent_tools_from_tasks.task_output(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的输出读取入口；若没有这行代码，删除旧薄包装后主 agent 无法二次查询子任务结果。
        "task_stop": lambda arguments: tasks_agent_tools_from_tasks.task_stop(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的停止入口；若没有这行代码，删除旧薄包装后主 agent 无法取消后台子任务。
        "task_list": lambda arguments: tasks_agent_tools_from_tasks.task_list(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的列表入口；若没有这行代码，删除旧薄包装后主 agent 无法管理多个子任务。
        "task_get": lambda arguments: tasks_agent_tools_from_tasks.task_get(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的详情入口；若没有这行代码，删除旧薄包装后主 agent 无法追溯任务边界。
        "task_update": lambda arguments: tasks_agent_tools_from_tasks.task_update(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的元信息更新入口；若没有这行代码，删除旧薄包装后主 agent 无法为任务补标签或备注。
        "team_create": lambda arguments: tasks_agent_tools_from_tasks.team_create(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的 peer 创建入口；若没有这行代码，删除旧薄包装后教学版团队协作无法登记成员。
        "send_message": lambda arguments: tasks_agent_tools_from_tasks.send_message(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的 peer 消息发送入口；若没有这行代码，删除旧薄包装后团队消息队列无法建立。
        "list_peers": lambda arguments: tasks_agent_tools_from_tasks.list_peers(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的 peer 列表入口；若没有这行代码，删除旧薄包装后主 agent 无法查看团队成员。
        "read_peer_messages": lambda arguments: tasks_agent_tools_from_tasks.read_peer_messages(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的 inbox 读取入口；若没有这行代码，删除旧薄包装后主 agent 无法读取团队消息。
        "ack_peer_message": lambda arguments: tasks_agent_tools_from_tasks.ack_peer_message(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的消息确认入口；若没有这行代码，删除旧薄包装后消息状态无法标记已处理。
        "team_delete": lambda arguments: tasks_agent_tools_from_tasks.team_delete(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的 peer 删除入口；若没有这行代码，删除旧薄包装后主 agent 无法回收成员记录。
        "team_start_task": lambda arguments: tasks_agent_tools_from_tasks.team_start_task(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的团队任务启动入口；若没有这行代码，删除旧薄包装后 peer 无法绑定后台子任务。
        "enter_plan_mode": lambda arguments: plan_runtime_from_core.enter_plan_mode(agent, arguments),  # 修改代码+AgentPyPhaseEPlanRuntime: executor 直接路由到 core/plan_runtime.py 进入计划模式；若没有这行代码，agent.py 仍会承担 enter_plan_mode 能力实现。
        "exit_plan_mode": lambda arguments: plan_runtime_from_core.exit_plan_mode(agent, arguments),  # 修改代码+AgentPyPhaseEPlanRuntime: executor 直接路由到 core/plan_runtime.py 退出计划模式；若没有这行代码，agent.py 仍会承担 exit_plan_mode 能力实现。
        "verify_plan_execution": lambda arguments: plan_runtime_from_core.verify_plan_execution(agent, arguments),  # 修改代码+AgentPyPhaseEPlanRuntime: executor 直接路由到 core/plan_runtime.py 计划验收；若没有这行代码，agent.py 仍会承担 verify_plan_execution 能力实现。
        "enter_worktree": lambda arguments: plan_runtime_from_core.enter_worktree(agent, arguments),  # 修改代码+AgentPyPhaseEPlanRuntime: executor 直接路由到 core/plan_runtime.py 进入轻量 worktree 状态；若没有这行代码，agent.py 仍会承担 enter_worktree 能力实现。
        "exit_worktree": lambda arguments: plan_runtime_from_core.exit_worktree(agent, arguments),  # 修改代码+AgentPyPhaseEPlanRuntime: executor 直接路由到 core/plan_runtime.py 退出轻量 worktree 状态；若没有这行代码，agent.py 仍会承担 exit_worktree 能力实现。
        "lsp_symbols": lambda arguments: lsp_repl_tools_from_tools.lsp_symbols(agent, arguments),  # 修改代码+AgentPySplitPhase15B1: executor 直接调用 LSP 符号模块；如果没有这行代码，删除 `agent._lsp_symbols` 后模型无法读取文件结构。
        "lsp_definition": lambda arguments: lsp_repl_tools_from_tools.lsp_definition(agent, arguments),  # 修改代码+AgentPySplitPhase15B1: executor 直接调用 LSP 定义定位模块；如果没有这行代码，删除 `agent._lsp_definition` 后模型无法跳到符号行。
        "lsp_diagnostics": lambda arguments: lsp_repl_tools_from_tools.lsp_diagnostics(agent, arguments),  # 修改代码+AgentPySplitPhase15B1: executor 直接调用 LSP 语法诊断模块；如果没有这行代码，删除 `agent._lsp_diagnostics` 后模型无法检查 SyntaxError。
        "repl": lambda arguments: lsp_repl_tools_from_tools.repl(agent, arguments),  # 修改代码+AgentPySplitPhase15B1: executor 直接调用安全 REPL 模块；如果没有这行代码，删除 `agent._repl` 后批量只读查询会变成未知工具。
        "cron_create": lambda arguments: tasks_agent_tools_from_tasks.cron_create(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的定时任务创建入口；若没有这行代码，删除旧薄包装后长期检查任务无法登记。
        "cron_list": lambda arguments: tasks_agent_tools_from_tasks.cron_list(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的定时任务列表入口；若没有这行代码，删除旧薄包装后长期任务记录无法查询。
        "cron_delete": lambda arguments: tasks_agent_tools_from_tasks.cron_delete(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的定时任务删除入口；若没有这行代码，删除旧薄包装后不需要的长期记录无法清理。
        "monitor": lambda arguments: tasks_agent_tools_from_tasks.monitor(agent, arguments),  # 修改代码+AgentPySplitPhase15B10: 直接路由到任务模块的监控总入口；若没有这行代码，删除旧薄包装后监控登记、列出、删除和记录结果无法执行。
    }  # 新增代码+ToolsExecutorSplit: 分发表结束；若没有这行代码，Python 字典语法不完整。


def _guard_tool_execution(agent: Any, tool_call: ToolCall) -> str | None:  # 新增代码+ToolsExecutorSplit: 执行具体工具前统一做权限和策略守卫；若没有这行代码，守卫逻辑会留在主类大方法中。
    if tool_call.name in tool_scope_from_tools.COMPUTER_USE_COMPAT_BUILTIN_TOOL_NAMES:  # 新增代码+ComputerUseMcpV2LegacyBlock：执行层硬阻断旧 Computer Use 内置工具名；如果没有这行代码，模型历史里伪造 computer_action 仍可能绕过 v2 MCP 工具面。
        run_helpers_from_core.safe_record_observation(agent, "computer_use_legacy_tool_blocked", {"tool_name": tool_call.name, "replacement": "mcp__computer-use__*", "runtime": "computer_use_mcp_v2"})  # 新增代码+ComputerUseMcpV2LegacyBlock：记录旧入口被拦截的审计事件；如果没有这行代码，验收失败时无法证明 executor 已经拦住旧接口。
        return f"{tool_call.name} 失败：旧 Computer Use 内置入口已停用，请使用 mcp__computer-use__* 工具。"  # 新增代码+ComputerUseMcpV2LegacyBlock：把明确迁移说明返回给模型；如果没有这行代码，模型只会看到未知工具或不清楚应改用 v2 MCP。
    if agent.allowed_tool_names is not None and tool_call.name not in agent.allowed_tool_names:  # 新增代码+ToolsExecutorSplit: 执行期再次检查当前 agent 的 allowed_tools 边界；若没有这行代码，模型伪造隐藏工具名仍能绕过展示层过滤。
        return f"{tool_call.name} 失败：不在当前 agent 的 allowed_tools 范围内。"  # 新增代码+ToolsExecutorSplit: 直接拒绝越权工具调用；若没有这行代码，未授权工具可能继续写文件、跑命令或调用 MCP。
    catalog_tool = catalog_runtime_from_tools.find_catalog_tool(agent, tool_call.name)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 执行前直连 catalog_runtime 查找工具元数据；若没有这行代码，executor 仍会反向依赖 agent.py 薄包装。
    if catalog_tool is not None:  # 新增代码+ToolsExecutorSplit: 只对 catalog 中存在的工具做策略二次校验；若没有这行代码，未知工具会在访问决策属性前报错。
        decision = catalog_runtime_from_tools.tool_policy_decision(agent, catalog_tool)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 执行层直连 catalog_runtime 复用统一 ToolPolicy 决策；若没有这行代码，policy 真实实现仍留在 agent.py 边界上。
        if not decision.executable and decision.state != "deferred":  # 新增代码+ToolsExecutorSplit: 非 deferred 的策略阻断必须在具体工具分发前停止；若没有这行代码，blocked/needs_skill/needs_workflow 工具仍可能进入权限弹窗。
            run_helpers_from_core.safe_record_observation(agent, "policy_blocked_tool", {"tool_name": tool_call.name, "state": decision.state, "reason": decision.reason})  # 修改代码+AgentPySplitPhase15B2: 通过 core helper 记录策略阻断事件；若没有这行代码，删除 `旧观察薄包装` 后审计无法解释工具为什么没执行。
            return f"{tool_call.name} 失败：policy 阻断，state={decision.state}，原因：{decision.reason}"  # 新增代码+ToolsExecutorSplit: 返回清晰策略阻断原因；若没有这行代码，模型不知道应处理 deny rule、skill gate 还是 workflow gate。
    if plan_runtime_from_core.plan_mode_blocks_tool_call(agent, tool_call, catalog_tool):  # 修改代码+AgentPyPhaseEPlanRuntime: 在具体分发前直连新计划闸门模块；若没有这行代码，模型可能 exit_plan_mode 后马上写文件或跑命令。
        run_helpers_from_core.safe_record_observation(agent, "plan_mode_blocked_tool", {"tool_name": tool_call.name, "plan_state": dict(agent.plan_mode_state)})  # 修改代码+AgentPySplitPhase15B2: 通过 core helper 记录计划闸门阻断事件；若没有这行代码，删除 `旧观察薄包装` 后审计看不到副作用为何没执行。
        return f"{tool_call.name} 失败：plan mode 阻断，当前计划尚未确认，不能执行写入、删除、命令、外部操作或其他副作用工具。"  # 新增代码+ToolsExecutorSplit: 返回清晰阻断说明；若没有这行代码，模型不知道需要等待用户确认计划。
    if catalog_runtime_from_tools.is_unloaded_deferred_tool(agent, tool_call.name):  # 修改代码+AgentPyPhaseHMcpToolRuntime: 执行层直连 catalog_runtime 拦截未加载 deferred 工具；若没有这行代码，隐藏 MCP 工具仍会经由 agent.py 薄包装判断。
        return f'{tool_call.name} 失败：该工具尚未通过 tool_search select 加载。请先调用 tool_search，query="select:{tool_call.name}"。'  # 新增代码+ToolsExecutorSplit: 返回清楚加载指引并拒绝执行；若没有这行代码，用户看不到为什么工具被拒绝。
    return None  # 新增代码+ToolsExecutorSplit: 没有守卫阻断时返回 None；若没有这行代码，调用方无法区分阻断和放行。


def execute_tool(agent: Any, tool_call: ToolCall) -> str:  # 新增代码+ToolsExecutorSplit: 根据工具名称分发到具体工具函数；若没有这行代码，主入口仍要维护长 if 链。
    guard_message = _guard_tool_execution(agent, tool_call)  # 新增代码+ToolsExecutorSplit: 先运行 allowed_tools、policy、plan mode 和 deferred 守卫；若没有这行代码，安全边界会被分发表绕过。
    if guard_message is not None:  # 新增代码+ToolsExecutorSplit: 检查守卫是否返回阻断文本；若没有这行代码，阻断结果不会提前返回。
        return guard_message  # 新增代码+ToolsExecutorSplit: 返回守卫阻断说明；若没有这行代码，被拒绝工具仍可能继续执行。
    catalog_tool = catalog_runtime_from_tools.find_catalog_tool(agent, tool_call.name)  # 修改代码+AgentPyPhaseHMcpToolRuntime: 权限层直连 catalog_runtime 读取工具目录元数据；若没有这行代码，permission_mode 仍通过 agent.py 薄包装取元数据。
    permission_decision = decide_tool_permission(agent, tool_call, catalog_tool)  # 新增代码+Stage15E: 生成统一权限决策；若没有这行代码，allow/deny/ask/auto_allow 不会进入执行流程。
    _record_permission_decision(agent, tool_call, permission_decision)  # 新增代码+Stage15E: 记录权限决策 observation；若没有这行代码，审计看不到工具为什么被允许或拒绝。
    if not permission_decision.allowed:  # 新增代码+Stage15E: 权限拒绝时禁止继续执行；若没有这行代码，deny 决策可能只被记录但仍执行工具。
        return _permission_denied_message(agent, tool_call, permission_decision)  # 新增代码+Stage15E: 返回拒绝文本并运行拒绝 hook；若没有这行代码，权限拒绝没有统一出口。
    pre_event = ToolHookEvent(tool_name=tool_call.name, call_id=tool_call.call_id, arguments=tool_call.arguments, permission_status=permission_decision.status)  # 新增代码+Stage15E: 构造执行前 hook 事件；若没有这行代码，pre_tool_use hook 没有上下文。
    pre_hook_error = _run_tool_hooks(agent, "pre_tool_use", pre_event)  # 新增代码+Stage15E: 运行执行前 hook；若没有这行代码，工具执行前无法插入审计和拦截点。
    if pre_hook_error is not None:  # 新增代码+Stage15E: pre hook 报错时停止执行工具；若没有这行代码，坏 hook 后工具仍可能继续产生副作用。
        return pre_hook_error  # 新增代码+Stage15E: 返回 hook 错误给模型；若没有这行代码，调用方拿不到可恢复反馈。
    try:  # 新增代码+Stage15E: 捕获具体工具执行异常；若没有这行代码，单个工具异常会中断整个 agent。
        result_text = _dispatch_tool_call(agent, tool_call)  # 新增代码+Stage15E: 调用真正的工具分发；若没有这行代码，hook 生命周期没有实际工具执行。
    except Exception as error:  # 新增代码+Stage15E: 把工具异常转换成可读文本和事件；若没有这行代码，用户会看到裸堆栈或 agent 直接崩溃。
        error_text = str(error)  # 新增代码+Stage15E: 保存错误摘要；若没有这行代码，后续事件和返回文本没有具体原因。
        error_event = ToolHookEvent(tool_name=tool_call.name, call_id=tool_call.call_id, arguments=tool_call.arguments, error_text=error_text, permission_status=permission_decision.status)  # 新增代码+Stage15E: 构造工具错误 hook 事件；若没有这行代码，tool_error hook 看不到失败上下文。
        _run_tool_hooks(agent, "tool_error", error_event)  # 新增代码+Stage15E: 记录并运行工具错误 hook；若没有这行代码，异常缺少统一审计点。
        return f"{tool_call.name} 工具执行失败：{error_text}"  # 新增代码+Stage15E: 返回可读执行失败文本；若没有这行代码，模型无法根据错误继续恢复。
    post_event = ToolHookEvent(tool_name=tool_call.name, call_id=tool_call.call_id, arguments=tool_call.arguments, result_text=result_text, permission_status=permission_decision.status)  # 新增代码+Stage15E: 构造执行后 hook 事件；若没有这行代码，post_tool_use hook 拿不到结果。
    post_hook_error = _run_tool_hooks(agent, "post_tool_use", post_event)  # 新增代码+Stage15E: 运行执行后 hook；若没有这行代码，工具成功后无法插入审计和结果处理点。
    if post_hook_error is not None:  # 新增代码+Stage15E: post hook 报错时返回可恢复错误；若没有这行代码，hook 异常可能被吞掉。
        return post_hook_error  # 新增代码+Stage15E: 返回 hook 错误文本；若没有这行代码，模型不知道后处理失败。
    return result_text  # 新增代码+Stage15E: 返回真实工具结果；若没有这行代码，工具成功输出无法回填给模型。
