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


def agent_tool_from_schema(schema: dict[str, Any], *, source: str = "builtin", should_defer: bool = False, always_load: bool = False, risk_level: str = "low", is_read_only: bool = False, is_destructive: bool = False, permission_category: str = "", skill_gate: str = "", workflow_gate: str = "", original_name: str = "", server_name: str = "", aliases: list[str] | None = None, search_hint: str = "", input_json_schema: dict[str, Any] | None = None, output_schema: dict[str, Any] | None = None, is_open_world: bool = False, strict: bool = False, max_result_size_chars: int = 20000, capability_pack: str = "") -> AgentTool:  # 新增代码+ToolsSplit: 把旧 schema 包装成 AgentTool；若没有这行代码，内置和 MCP 工具无法共享统一元数据类型。
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
        catalog.append(agent_tool_from_schema(schema, source="builtin", should_defer=should_defer, always_load=always_load, capability_pack=capability_pack))  # 新增代码+ToolsSplit: 保存延迟加载和能力包元数据；若没有这行代码，工具目录无法支持按需加载。
    return catalog  # 新增代码+ToolsSplit: 返回完整内置工具目录；若没有这行代码，调用方无法取得构建结果。
