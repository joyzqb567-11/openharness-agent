"""内置工具目录构建与 schema 包装。"""  # 新增代码+ToolsSplit: 把工具目录逻辑从主入口拆出；若没有这个文件，工具 schema 和元数据仍会混在 learning_agent.py。

from __future__ import annotations  # 新增代码+ToolsSplit: 延迟解析类型注解；若没有这行代码，脚本模式导入时更容易受顺序影响。

import copy  # 新增代码+ToolsSplit: 包装工具 schema 时需要深拷贝；若没有这行代码，全局 TOOL_SCHEMAS 可能被目录调用方污染。
from typing import Any  # 新增代码+ToolsSplit: 工具 schema 是通用 JSON 字典；若没有这行代码，类型边界会不清楚。

try:  # 新增代码+ToolsSplit: 包运行模式下导入 AgentTool 类型；若没有这行代码，catalog 无法构造工具元数据对象。
    from learning_agent.tools.types import AgentTool  # 新增代码+ToolsSplit: 读取正式工具元数据类型；若没有这行代码，目录只能返回裸 dict。
except ModuleNotFoundError as error:  # 新增代码+ToolsSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，start_oauth_agent.bat 可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.types"}:  # 新增代码+ToolsSplit: 只允许目标包路径缺失时 fallback；若没有这行代码，types 内部真实 bug 会被误吞。
        raise  # 新增代码+ToolsSplit: 重新抛出真实导入错误；若没有这行代码，排查 catalog 问题会很困难。
    from tools.types import AgentTool  # 新增代码+ToolsSplit: 脚本运行模式下从同目录 tools 包导入类型；若没有这行代码，直接执行 learning_agent.py 时会失败。



try:  # 新增代码+ToolSchemaSplit: 包运行模式下从独立 schema 模块读取内置工具定义；若没有这行代码，catalog 仍会依赖旧 learning_agent.py 入口。
    from learning_agent.tools.schemas import BUILTIN_TOOL_CAPABILITY_PACKS, KERNEL_TOOL_NAMES, TOOL_SCHEMAS  # 新增代码+ToolSchemaSplit: 导入工具 schema、内核工具名和能力包映射；若没有这行代码，catalog 无法独立构建。
except ModuleNotFoundError as error:  # 新增代码+ToolSchemaSplit: 捕获直接脚本运行时包路径不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.tools", "learning_agent.tools.schemas"}:  # 新增代码+ToolSchemaSplit: 只允许目标路径缺失时 fallback；若没有这行代码，schema 内部 bug 会被误吞。
        raise  # 新增代码+ToolSchemaSplit: 重新抛出真实导入错误；若没有这行代码，工具目录问题会更难定位。
    from tools.schemas import BUILTIN_TOOL_CAPABILITY_PACKS, KERNEL_TOOL_NAMES, TOOL_SCHEMAS  # 新增代码+ToolSchemaSplit: 脚本模式下读取同目录 schema 模块；若没有这行代码，直接执行 learning_agent.py 时 catalog 没有工具定义。


def _builtin_tool_schemas() -> list[dict[str, Any]]:  # 修改代码+ToolSchemaSplit: 从独立 schema 模块读取内置工具列表；若没有这行代码，catalog 会重新依赖旧入口。
    return TOOL_SCHEMAS if isinstance(TOOL_SCHEMAS, list) else []  # 修改代码+ToolSchemaSplit: 异常类型降级为空列表；若没有这行代码，坏 schema 状态会让 catalog 构建崩溃。


def _builtin_tool_capability_packs() -> dict[str, str]:  # 修改代码+ToolSchemaSplit: 从独立 schema 模块读取能力包映射；若没有这行代码，工具延迟加载分组会丢失。
    return BUILTIN_TOOL_CAPABILITY_PACKS if isinstance(BUILTIN_TOOL_CAPABILITY_PACKS, dict) else {}  # 修改代码+ToolSchemaSplit: 异常类型降级为空映射；若没有这行代码，catalog 会在坏常量上崩溃。


def _kernel_tool_names() -> set[str]:  # 修改代码+ToolSchemaSplit: 从独立 schema 模块读取首轮常驻原子工具名；若没有这行代码，极简工具面会退化。
    return KERNEL_TOOL_NAMES if isinstance(KERNEL_TOOL_NAMES, set) else set()  # 修改代码+ToolSchemaSplit: 异常类型降级为空集合；若没有这行代码，内核工具判断可能直接报错。


READ_ONLY_CONCURRENT_TOOL_NAMES: set[str] = {"read", "read_file", "todo_read", "read_background_command", "list_mcp_resources", "read_mcp_resource", "list_mcp_prompts", "read_mcp_prompt", "skill_list", "skill_load", "task_list", "task_get", "task_output", "list_peers", "read_peer_messages", "lsp_symbols", "lsp_definition", "lsp_diagnostics", "cron_list", "prompt_surface_report", "token_budget_report", "status_snapshot", "task_status", "session_list", "session_resume", "compact_status", "event_tail", "resume_report", "run_status", "health_status", "computer_status", "computer_observe"}  # 修改代码+Phase27ComputerUse: 把 computer_observe 标记为只读并发安全观察工具；如果没有这行代码，窗口观察会被当成高风险桌面动作。
DESTRUCTIVE_TOOL_NAMES: set[str] = {"write", "edit", "write_file", "append_memory", "todo_write", "notebook_edit", "task_stop", "task_update", "ack_peer_message", "team_delete", "exit_worktree", "cron_delete"}  # 新增代码+Stage15D: 集中列出会改变文件、状态或长期记录的工具；若没有这行代码，权限层无法突出危险操作。
SHELL_TOOL_NAMES: set[str] = {"bash", "start_background_command"}  # 新增代码+Stage15D: 集中列出会执行系统命令的工具；若没有这行代码，命令类工具无法获得更高风险和超时元数据。
INTERACTIVE_TOOL_PREFIXES: tuple[str, ...] = ("browser_",)  # 新增代码+Stage15D: 集中记录真实浏览器这类交互工具前缀；若没有这行代码，执行器无法知道这些工具可能依赖外部可见状态。
COMPUTER_ACTION_TOOL_NAMES: set[str] = {"computer_action"}  # 新增代码+OSComputerUse: 单独列出会控制桌面的 Computer Use 动作工具；若没有这行代码，catalog 无法给桌面动作高风险元数据。


def builtin_tool_protocol_metadata(tool_name: str) -> dict[str, Any]:  # 新增代码+Stage15D: 为内置工具补齐 v3 协议元数据；若没有这行代码，catalog 只能保留旧 schema 和零散默认值。
    metadata: dict[str, Any] = {"permission_mode": "ask", "interrupt_behavior": "block", "result_policy": "inline_or_artifact"}  # 新增代码+Stage15D: 先给未知工具保守默认值；若没有这行代码，未知工具可能绕过询问或缺少结果策略。
    if tool_name in READ_ONLY_CONCURRENT_TOOL_NAMES:  # 新增代码+Stage15D: 识别明确安全的只读工具；若没有这行代码，read/read_file 等工具无法进入并发读取批次。
        metadata.update({"risk_level": "low", "is_read_only": True, "is_concurrency_safe": True, "permission_mode": "auto_allow"})  # 新增代码+Stage15D: 给安全读取工具自动允许和并发标记；若没有这行代码，大项目分析会被串行读取拖慢。
    if tool_name in DESTRUCTIVE_TOOL_NAMES:  # 新增代码+Stage15D: 识别写入、编辑、删除或状态更新工具；若没有这行代码，危险工具和普通工具没有区别。
        metadata.update({"risk_level": "high", "is_destructive": True, "is_concurrency_safe": False, "permission_mode": "ask"})  # 新增代码+Stage15D: 强制副作用工具串行且需要询问；若没有这行代码，写文件或编辑可能被自动并发执行。
    if tool_name in SHELL_TOOL_NAMES:  # 新增代码+Stage15D: 识别 shell 命令类工具；若没有这行代码，bash 的风险和超时边界会被当成普通工具。
        metadata.update({"risk_level": "high", "is_concurrency_safe": False, "permission_mode": "ask", "timeout_seconds": 300.0})  # 新增代码+Stage15D: 给命令工具高风险和保守超时提示；若没有这行代码，命令执行缺少统一安全边界。
    if any(tool_name.startswith(prefix) for prefix in INTERACTIVE_TOOL_PREFIXES):  # 新增代码+Stage15D: 识别真实浏览器等交互工具；若没有这行代码，调度器不知道这些工具可能依赖可见外部状态。
        metadata.update({"risk_level": "medium", "requires_user_interaction": True, "is_concurrency_safe": False, "permission_mode": "ask"})  # 新增代码+Stage15D: 让交互工具保持串行并走权限通道；若没有这行代码，浏览器操作可能被乱序并发。
    if tool_name in COMPUTER_ACTION_TOOL_NAMES:  # 新增代码+OSComputerUse: 识别 OS 级桌面控制动作；若没有这行代码，computer_action 可能按普通工具处理。
        metadata.update({"risk_level": "high", "requires_user_interaction": True, "is_concurrency_safe": False, "permission_mode": "ask"})  # 新增代码+OSComputerUse: 强制桌面动作高风险、串行、需询问；若没有这行代码，鼠标键盘动作可能被自动或并发执行。
    return metadata  # 新增代码+Stage15D: 返回最终协议元数据；若没有这行代码，catalog 无法把这些安全判断传给 AgentTool。


def agent_tool_from_schema(schema: dict[str, Any], *, source: str = "builtin", should_defer: bool = False, always_load: bool = False, risk_level: str = "low", is_read_only: bool = False, is_destructive: bool = False, is_concurrency_safe: bool = False, requires_user_interaction: bool = False, interrupt_behavior: str = "block", permission_mode: str = "ask", result_policy: str = "inline_or_artifact", timeout_seconds: float = 0.0, permission_category: str = "", skill_gate: str = "", workflow_gate: str = "", original_name: str = "", server_name: str = "", aliases: list[str] | None = None, search_hint: str = "", input_json_schema: dict[str, Any] | None = None, output_schema: dict[str, Any] | None = None, is_open_world: bool = False, strict: bool = False, max_result_size_chars: int = 20000, capability_pack: str = "") -> AgentTool:  # 修改代码+Stage15D: 把旧 schema 包装成携带 v3 协议元数据的 AgentTool；若没有这行代码，执行器无法读取并发、权限、超时和结果策略。
    function_schema = schema.get("function", {})  # 新增代码+ToolsSplit: 取出旧 schema 的 function 部分；若没有这行代码，无法读取工具名、说明和参数。
    if not isinstance(function_schema, dict):  # 新增代码+ToolsSplit: 防御异常 schema 没有合法 function 字典；若没有这行代码，坏数据会在后续 get 调用处崩溃。
        function_schema = {}  # 新增代码+ToolsSplit: 用空字典兜底异常 function；若没有这行代码，后续字段提取没有安全默认值。
    tool_name = str(function_schema.get("name", ""))  # 新增代码+ToolsSplit: 读取并规范化工具名；若没有这行代码，AgentTool 缺少目录索引键。
    tool_description = str(function_schema.get("description", ""))  # 新增代码+ToolsSplit: 读取并规范化工具说明；若没有这行代码，AgentTool 无法保留旧 schema 的描述。
    parameters = function_schema.get("parameters", {"type": "object"})  # 新增代码+ToolsSplit: 读取旧 schema 参数定义并提供空对象兜底；若没有这行代码，参数约束可能丢失或缺省时报错。
    if not isinstance(parameters, dict):  # 新增代码+ToolsSplit: 防御异常 parameters 不是字典；若没有这行代码，坏参数 schema 会进入模型边界。
        parameters = {"type": "object"}  # 新增代码+ToolsSplit: 用最小 object schema 兜底；若没有这行代码，兼容层无法处理不规范旧 schema。
    return AgentTool(  # 新增代码+ToolsSplit: 返回包装后的 AgentTool；若没有这行代码，调用方拿不到带元数据的工具对象。
        name=tool_name,  # 新增代码+ToolsSplit: 传入工具名；若没有这行代码，目录中工具无法按名称查找。
        description=tool_description,  # 新增代码+ToolsSplit: 传入工具说明；若没有这行代码，目录会丢失模型选择工具的文本依据。
        input_schema=copy.deepcopy(parameters),  # 新增代码+ToolsSplit: 深拷贝参数 schema；若没有这行代码，catalog 可能和全局 TOOL_SCHEMAS 共享可变嵌套对象。
        source=source,  # 新增代码+ToolsSplit: 传入工具来源；若没有这行代码，内置和外部工具无法区分。
        risk_level=risk_level,  # 新增代码+ToolsSplit: 传入风险级别；若没有这行代码，安全层无法读取风险元数据。
        is_read_only=is_read_only,  # 新增代码+ToolsSplit: 传入只读标记；若没有这行代码，权限层无法识别读取工具。
        is_destructive=is_destructive,  # 新增代码+ToolsSplit: 传入破坏性标记；若没有这行代码，高风险工具无法被特别处理。
        is_concurrency_safe=is_concurrency_safe,  # 新增代码+Stage15D: 传入并发安全标记；若没有这行代码，AgentTool 会丢失 catalog 判断出的并发能力。
        requires_user_interaction=requires_user_interaction,  # 新增代码+Stage15D: 传入交互需求标记；若没有这行代码，浏览器等工具的外部交互属性会丢失。
        interrupt_behavior=interrupt_behavior,  # 新增代码+Stage15D: 传入中断策略；若没有这行代码，执行器无法按工具决定取消时是阻塞还是可打断。
        permission_mode=permission_mode,  # 新增代码+Stage15D: 传入权限模式；若没有这行代码，权限 hook 无法区分自动允许和需要询问的工具。
        result_policy=result_policy,  # 新增代码+Stage15D: 传入结果策略；若没有这行代码，执行器无法统一处理内联结果和 artifact 结果。
        timeout_seconds=timeout_seconds,  # 新增代码+Stage15D: 传入建议超时；若没有这行代码，命令类或慢工具没有工具级超时提示。
        should_defer=should_defer,  # 新增代码+ToolsSplit: 传入延迟加载标记；若没有这行代码，工具池不能按工具控制可见时机。
        always_load=always_load,  # 新增代码+ToolsSplit: 传入强制加载标记；若没有这行代码，发现入口可能无法首轮出现。
        permission_category=permission_category,  # 新增代码+ToolsSplit: 传入权限类别；若没有这行代码，授权展示无法按类别组织。
        skill_gate=skill_gate,  # 新增代码+ToolsSplit: 传入 skill 门控；若没有这行代码，skill 相关加载规则没有落点。
        workflow_gate=workflow_gate,  # 新增代码+ToolsSplit: 传入 workflow 门控；若没有这行代码，流程相关加载规则没有落点。
        original_name=original_name or tool_name,  # 新增代码+ToolsSplit: 默认把原始名设为当前工具名；若没有这行代码，内置工具也缺少可追溯原名。
        server_name=server_name,  # 新增代码+ToolsSplit: 传入 server 名；若没有这行代码，外部 server 来源无法记录。
        aliases=list(aliases or []),  # 新增代码+ToolsSplit: 复制别名列表避免调用方共享可变对象；若没有这行代码，外部修改 aliases 会污染 AgentTool。
        search_hint=search_hint,  # 新增代码+ToolsSplit: 传入搜索提示；若没有这行代码，MCP 的 anthropic/searchHint 会被包装层丢掉。
        input_json_schema=copy.deepcopy(input_json_schema if input_json_schema is not None else parameters),  # 新增代码+ToolsSplit: 保存原始输入 JSON Schema 并缺省复用参数 schema；若没有这行代码，策略层拿不到独立的原始 inputSchema 副本。
        output_schema=copy.deepcopy(output_schema or {}),  # 新增代码+ToolsSplit: 保存输出 schema 深拷贝；若没有这行代码，MCP outputSchema 会丢失或被外部可变对象污染。
        is_open_world=is_open_world,  # 新增代码+ToolsSplit: 传入开放世界标记；若没有这行代码，openWorldHint 无法进入 AgentTool。
        strict=strict,  # 新增代码+ToolsSplit: 传入 strict 标记；若没有这行代码，合理的 strict 元数据无法随工具保存。
        max_result_size_chars=max_result_size_chars,  # 新增代码+ToolsSplit: 传入结果大小上限；若没有这行代码，AgentTool 只能依赖默认字段而无法从包装入口覆盖。
        capability_pack=capability_pack,  # 新增代码+ToolsSplit: 传入能力包名称；若没有这行代码，工具进入 catalog 后无法被 select_pack 批量加载。
    )  # 新增代码+ToolsSplit: 结束 AgentTool 构造调用；若没有这行代码，Python 调用语法不完整且新增元数据无法完整传入。


def builtin_tool_capability_pack(tool_name: str) -> str:  # 新增代码+ToolsSplit: 查询内置工具所属能力包；若没有这行代码，目录构建处会重复硬编码映射读取逻辑。
    return _builtin_tool_capability_packs().get(tool_name, "")  # 新增代码+ToolsSplit: 未映射工具返回空包名；若没有这行代码，内核工具可能被错误归入某个能力包。


def build_builtin_tool_catalog(tool_schemas: list[dict[str, Any]] | None = None) -> list[AgentTool]:  # 新增代码+ToolsSplit: 构建内置工具的 AgentTool 目录；若没有这行代码，工具层无法从现有 schema 生成带元数据的 catalog。
    catalog: list[AgentTool] = []  # 新增代码+ToolsSplit: 准备保存包装后的内置工具列表；若没有这行代码，函数没有地方累计转换结果。
    schemas = tool_schemas if tool_schemas is not None else _builtin_tool_schemas()  # 新增代码+ToolsSplit: 允许测试传入 schema，也兼容旧主入口全局 schema；若没有这行代码，新模块只能依赖单一入口。
    kernel_tool_names = _kernel_tool_names()  # 新增代码+ToolsSplit: 读取首轮必须可见的四原子工具名；若没有这行代码，首轮工具池可能回归全量或变空。
    for schema in schemas:  # 新增代码+ToolsSplit: 遍历现有内置工具 schema；若没有这行代码，目录不会包含任何已有工具。
        function_schema = schema.get("function", {})  # 新增代码+ToolsSplit: 取出 function 层以判断工具名；若没有这行代码，无法识别内核工具。
        tool_name = str(function_schema.get("name", "")) if isinstance(function_schema, dict) else ""  # 新增代码+ToolsSplit: 安全读取并规范化工具名；若没有这行代码，能力包映射可能收到非字符串键。
        capability_pack = builtin_tool_capability_pack(tool_name)  # 新增代码+ToolsSplit: 查询当前内置工具所属能力包；若没有这行代码，普通工具无法被按包延迟加载。
        always_load = tool_name in kernel_tool_names  # 新增代码+ToolsSplit: 只有内核工具首轮强制可见；若没有这行代码，低频工具会继续污染首轮工具池。
        should_defer = not always_load  # 新增代码+ToolsSplit: 除 read/write/edit/bash 外全部内置工具默认不进首轮模型 schema；若没有这行代码，未映射的旧工具仍会常驻可见。
        protocol_metadata = builtin_tool_protocol_metadata(tool_name)  # 新增代码+Stage15D: 读取工具协议 v3 元数据；若没有这行代码，内置工具不会携带并发和权限语义。
        catalog.append(agent_tool_from_schema(schema, source="builtin", should_defer=should_defer, always_load=always_load, capability_pack=capability_pack, **protocol_metadata))  # 修改代码+Stage15D: 保存延迟加载、能力包和协议元数据；若没有这行代码，Stage 15E/F 无法基于 catalog 做权限和并发决策。
    return catalog  # 新增代码+ToolsSplit: 返回完整内置工具目录；若没有这行代码，调用方无法取得构建结果。
