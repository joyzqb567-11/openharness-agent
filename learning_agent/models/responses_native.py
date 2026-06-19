"""OpenAI Responses 原生工具协议适配层。"""  # 新增代码+OAuthNativeResponses: 说明本模块集中处理 Responses 原生 tools/output 协议；如果没有这个文件，协议细节会散落到 adapters.py 大文件里。
from __future__ import annotations  # 新增代码+OAuthNativeResponses: 延迟解析类型注解；如果没有这一行，后续 Callable/Any 注解在旧路径下更容易提前求值。

import copy  # 新增代码+OAuthNativeResponses: 深拷贝工具参数 schema，避免转换结果被调用方修改后污染原始工具定义；如果没有这一行，schema 可能在多轮请求间串改。
import json  # 新增代码+OAuthNativeOutputParser: 解析 Responses function_call.arguments JSON 字符串；如果没有这一行，原生工具参数无法变成内部 dict。
from typing import Any, Callable  # 新增代码+OAuthNativeResponses: Any 表示 JSON 风格工具结构，Callable 表示按工具名分配 namespace 的回调；如果没有这一行，接口边界不清楚。

try:  # 新增代码+OAuthNativeOutputParser: 包运行模式下导入内部消息对象；如果没有这一行，parser 无法返回 ModelMessage/ToolCall。
    from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+OAuthNativeOutputParser: 导入内部消息和工具调用类型；如果没有这一行，原生 output item 无法接入现有执行器。
except ModuleNotFoundError as error:  # 新增代码+OAuthNativeOutputParser: 兼容 start_oauth_agent.bat 脚本模式；如果没有这一行，脚本模式下包名前缀缺失会导致启动失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages"}:  # 新增代码+OAuthNativeOutputParser: 只允许目标包路径缺失进入 fallback；如果没有这一行，messages 内部 bug 会被误吞。
        raise  # 新增代码+OAuthNativeOutputParser: 重新抛出真实导入错误；如果没有这一行，排查 parser 导入失败会很困难。
    from core.messages import ModelMessage, ToolCall  # 新增代码+OAuthNativeOutputParser: 脚本模式下导入内部消息类型；如果没有这一行，bat 入口无法解析原生工具调用。


DEFAULT_RESPONSES_NAMESPACE_DESCRIPTION = "OpenHarness tools available to this agent turn."  # 新增代码+OAuthNativeResponses: 给单 namespace 模式提供稳定说明；如果没有这一行，模型看到的 namespace 说明会缺少兜底。
CORE_CODE_NAMESPACE = "core_code"  # 新增代码+OAuthNativeComputerUseNamespace: 保存核心代码工具 namespace 名；如果没有这一行，核心工具分组会用散落字符串。
COMPUTER_USE_NAMESPACE = "computer_use"  # 新增代码+OAuthNativeComputerUseNamespace: 保存 Windows Computer Use 工具 namespace 名；如果没有这一行，桌面工具无法稳定独立分组。
DEFAULT_NAMESPACE = "openharness"  # 新增代码+OAuthNativeComputerUseNamespace: 保存未知工具的兜底 namespace；如果没有这一行，无法处理临时或外部未知工具。

COMPUTER_USE_TOOL_NAMES = {  # 新增代码+OAuthNativeComputerUseNamespace: 函数段开始，列出必须归入 computer_use namespace 的安全桌面工具名；如果没有这个集合，Computer Use 工具会混入通用 namespace。
    "request_access",  # 新增代码+OAuthNativeComputerUseNamespace: 权限申请工具属于 Computer Use；如果没有这一项，权限工具会被错误分到核心代码工具里。
    "list_granted_applications",  # 新增代码+OAuthNativeComputerUseNamespace: 权限查询工具属于 Computer Use；如果没有这一项，模型难以通过 hosted tool_search 找到授权状态。
    "read_clipboard",  # 新增代码+OAuthNativeComputerUseNamespace: 剪贴板读取工具属于 Computer Use；如果没有这一项，系统剪贴板能力会混入普通工具。
    "write_clipboard",  # 新增代码+OAuthNativeComputerUseNamespace: 剪贴板写入工具属于 Computer Use；如果没有这一项，写剪贴板能力无法被单独审计。
    "computer_status",  # 新增代码+OAuthNativeComputerUseNamespace: Computer Use 状态工具属于桌面能力；如果没有这一项，状态查询可能脱离 computer_use namespace。
    "computer_observe",  # 新增代码+OAuthNativeComputerUseNamespace: 桌面观察工具属于 Computer Use；如果没有这一项，截图/窗口观察能力会被混入核心工具。
    "computer_execute",  # 新增代码+OAuthNativeComputerUseNamespace: 桌面执行工具属于 Computer Use；如果没有这一项，高风险动作无法独立延迟加载。
}  # 新增代码+OAuthNativeComputerUseNamespace: 函数段结束，Computer Use 工具名集合到此结束；如果没有这个边界，读者不容易看出分组覆盖范围。

CORE_CODE_TOOL_NAMES = {  # 新增代码+OAuthNativeComputerUseNamespace: 函数段开始，列出应优先归入 core_code namespace 的核心编码工具；如果没有这个集合，核心工具可能落到默认 namespace。
    "read",  # 新增代码+OAuthNativeComputerUseNamespace: 读取文件工具属于核心代码能力；如果没有这一项，read namespace 可能不稳定。
    "write",  # 新增代码+OAuthNativeComputerUseNamespace: 写文件工具属于核心代码能力；如果没有这一项，write namespace 可能不稳定。
    "edit",  # 新增代码+OAuthNativeComputerUseNamespace: 编辑文件工具属于核心代码能力；如果没有这一项，edit namespace 可能不稳定。
    "bash",  # 新增代码+OAuthNativeComputerUseNamespace: shell 工具属于核心代码能力；如果没有这一项，bash 可能落入兜底 namespace。
    "tool_search",  # 新增代码+OAuthNativeComputerUseNamespace: 本地兼容 tool_search 属于核心调度入口；如果没有这一项，旧协议 fallback 搜索入口可能被错分。
}  # 新增代码+OAuthNativeComputerUseNamespace: 函数段结束，核心工具名集合到此结束；如果没有这个边界，读者不容易看出核心分组覆盖范围。


def chat_completion_tool_to_responses_function(tool_schema: dict[str, Any]) -> dict[str, Any]:  # 新增代码+OAuthNativeResponses: 函数段开始，把旧 Chat Completions function tool 转成 Responses function；如果没有这个函数，顶层 tools 会继续使用旧嵌套结构。
    function_schema = tool_schema.get("function", {}) if isinstance(tool_schema, dict) else {}  # 新增代码+OAuthNativeResponses: 读取旧格式 function 字段并防御坏输入；如果没有这一行，异常 schema 会导致转换崩溃。
    if not isinstance(function_schema, dict):  # 新增代码+OAuthNativeResponses: 确认 function 字段是对象；如果没有这一行，字符串或列表会进入 .get 调用报错。
        function_schema = {}  # 新增代码+OAuthNativeResponses: 坏 function 字段回退为空对象；如果没有这一行，异常输入无法安全处理。
    parameters = function_schema.get("parameters", {"type": "object", "properties": {}, "additionalProperties": False})  # 新增代码+OAuthNativeResponses: 读取参数 schema 并提供空对象兜底；如果没有这一行，无参工具可能缺少 parameters 字段。
    response_function: dict[str, Any] = {  # 新增代码+OAuthNativeResponses: 准备 Responses function 工具对象；如果没有这一行，转换结果没有容器。
        "type": "function",  # 新增代码+OAuthNativeResponses: Responses namespace 内部工具类型固定为 function；如果没有这一行，OpenAI 后端无法识别工具。
        "name": str(function_schema.get("name", "")),  # 新增代码+OAuthNativeResponses: 把旧格式 function.name 提升到顶层；如果没有这一行，模型无法调用正确工具名。
        "description": str(function_schema.get("description", "")),  # 新增代码+OAuthNativeResponses: 把旧格式说明提升到顶层；如果没有这一行，模型选择工具时缺少语义。
        "parameters": copy.deepcopy(parameters) if isinstance(parameters, dict) else {"type": "object", "properties": {}, "additionalProperties": False},  # 新增代码+OAuthNativeResponses: 深拷贝参数 schema 或回退空对象；如果没有这一行，调用方可能污染原始 schema。
    }  # 新增代码+OAuthNativeResponses: 结束 Responses function 工具对象；如果没有这一行，Python 字典语法不完整。
    strict_value = function_schema.get("strict", tool_schema.get("strict") if isinstance(tool_schema, dict) else None)  # 新增代码+OAuthNativeResponses: 兼容旧 schema 可能携带 strict 的位置；如果没有这一行，严格模式标记无法流入 Responses 工具。
    if strict_value is True:  # 新增代码+OAuthNativeResponses: 只有明确 True 才透传 strict；如果没有这一行，None/False 可能产生多余字段。
        response_function["strict"] = True  # 新增代码+OAuthNativeResponses: 保留严格参数约束；如果没有这一行，支持 strict 的工具会被降级。
    return response_function  # 新增代码+OAuthNativeResponses: 返回转换后的 Responses function；如果没有这一行，调用方拿不到原生工具对象。
# 新增代码+OAuthNativeResponses: 函数段结束，chat_completion_tool_to_responses_function 到此结束；如果没有这个边界说明，用户不容易看出转换职责。


def build_hosted_tool_search_tools(tool_schemas: list[dict[str, Any]], *, namespace_name: str, deferred_tool_names: set[str]) -> list[dict[str, Any]]:  # 新增代码+OAuthNativeResponses: 函数段开始，构造单 namespace hosted tool_search 工具列表；如果没有这个函数，Task 2 无法先跑通基础协议。
    namespace_tools: list[dict[str, Any]] = []  # 新增代码+OAuthNativeResponses: 准备 namespace 内部 function 列表；如果没有这一行，转换后的工具没有保存位置。
    has_deferred_tool = False  # 新增代码+OAuthNativeToolSearchContract: 记录本次 payload 是否真的包含 defer_loading 工具；如果没有这一行，后端会在空 deferred 场景拒绝 hosted tool_search。
    for tool_schema in tool_schemas:  # 新增代码+OAuthNativeResponses: 遍历当前轮可见工具 schema；如果没有这一行，无法逐个转换工具。
        function_tool = chat_completion_tool_to_responses_function(tool_schema)  # 新增代码+OAuthNativeResponses: 把旧格式工具转成 Responses function；如果没有这一行，namespace 内会混入旧 schema。
        if function_tool["name"] in deferred_tool_names:  # 新增代码+OAuthNativeResponses: 判断当前工具是否应该延迟加载；如果没有这一行，defer_loading 不会生效。
            function_tool["defer_loading"] = True  # 新增代码+OAuthNativeResponses: 标记工具由 hosted tool_search 发现后再完整加载；如果没有这一行，模型会 eager 看到所有动态工具。
            has_deferred_tool = True  # 新增代码+OAuthNativeToolSearchContract: 确认至少一个工具真实带上 defer_loading；如果没有这一行，无法决定是否安全追加 hosted tool_search。
        namespace_tools.append(function_tool)  # 新增代码+OAuthNativeResponses: 保存转换后的 function 工具；如果没有这一行，namespace tools 会为空。
    native_tools = [  # 修改代码+OAuthNativeToolSearchContract: 先构造 namespace，再按需追加 hosted tool_search；如果没有这一行，无法避免空 deferred 场景的 400。
        {  # 新增代码+OAuthNativeResponses: namespace 对象开始；如果没有这一行，function 工具没有分组容器。
            "type": "namespace",  # 新增代码+OAuthNativeResponses: 声明 Responses namespace 类型；如果没有这一行，OpenAI 后端不会按 namespace 处理。
            "name": namespace_name,  # 新增代码+OAuthNativeResponses: 写入调用方指定 namespace 名；如果没有这一行，工具路径不稳定。
            "description": DEFAULT_RESPONSES_NAMESPACE_DESCRIPTION,  # 新增代码+OAuthNativeResponses: 写入 namespace 说明；如果没有这一行，模型缺少分组语义。
            "tools": namespace_tools,  # 新增代码+OAuthNativeResponses: 放入 function 工具列表；如果没有这一行，namespace 里没有可调用工具。
        },  # 新增代码+OAuthNativeResponses: namespace 对象结束；如果没有这一行，Python 字典语法不完整。
    ]  # 修改代码+OAuthNativeToolSearchContract: 顶层 tools 初始列表只含 namespace；如果没有这一行，Python 列表语法不完整。
    if has_deferred_tool:  # 新增代码+OAuthNativeToolSearchContract: 只有真实存在 deferred 工具才启用 hosted tool_search；如果没有这一行，OpenAI 后端会提示 requires at least one deferred tool。
        native_tools.append({"type": "tool_search"})  # 修改代码+OAuthNativeToolSearchContract: 按协议安全追加 hosted tool_search；如果没有这一行，存在 deferred 工具时模型无法使用原生搜索入口。
    return native_tools  # 修改代码+OAuthNativeToolSearchContract: 返回按协议裁剪后的顶层 tools；如果没有这一行，调用方拿不到 payload。
# 新增代码+OAuthNativeResponses: 函数段结束，build_hosted_tool_search_tools 到此结束；如果没有这个边界说明，用户不容易看出单 namespace 构造范围。


def build_hosted_tool_search_tools_by_namespace(tool_schemas: list[dict[str, Any]], *, deferred_tool_names: set[str], namespace_for_tool: Callable[[str], str], namespace_descriptions: dict[str, str] | None = None) -> list[dict[str, Any]]:  # 新增代码+OAuthNativeComputerUseNamespace: 函数段开始，按 namespace 分组构造 hosted tool_search 工具列表；如果没有这段函数，Computer Use 不能独立分组。
    buckets: dict[str, list[dict[str, Any]]] = {}  # 新增代码+OAuthNativeComputerUseNamespace: 准备按 namespace 收集 function 工具；如果没有这一行，分组结果没有容器。
    has_deferred_tool = False  # 新增代码+OAuthNativeToolSearchContract: 记录所有 namespace 中是否至少有一个 deferred 工具；如果没有这一行，无法避免空 deferred 场景发送非法 hosted tool_search。
    for tool_schema in tool_schemas:  # 新增代码+OAuthNativeComputerUseNamespace: 遍历当前轮工具 schema；如果没有这一行，无法逐个分配 namespace。
        function_tool = chat_completion_tool_to_responses_function(tool_schema)  # 新增代码+OAuthNativeComputerUseNamespace: 先转换成 Responses function；如果没有这一行，namespace 内会保留旧格式。
        tool_name = str(function_tool.get("name", ""))  # 新增代码+OAuthNativeComputerUseNamespace: 读取转换后的工具名；如果没有这一行，namespace 分配函数没有输入。
        namespace_name = namespace_for_tool(tool_name) or DEFAULT_NAMESPACE  # 新增代码+OAuthNativeComputerUseNamespace: 使用回调分配 namespace 并提供兜底；如果没有这一行，未知工具可能没有 namespace。
        if tool_name in deferred_tool_names:  # 新增代码+OAuthNativeComputerUseNamespace: 判断当前工具是否延迟加载；如果没有这一行，defer_loading 无法按工具名生效。
            function_tool["defer_loading"] = True  # 新增代码+OAuthNativeComputerUseNamespace: 标记延迟加载；如果没有这一行，动态工具会被 eager 暴露。
            has_deferred_tool = True  # 新增代码+OAuthNativeToolSearchContract: 确认本次 payload 至少有一个真实 deferred 工具；如果没有这一行，顶层 hosted tool_search 条件无法判断。
        buckets.setdefault(namespace_name, []).append(function_tool)  # 新增代码+OAuthNativeComputerUseNamespace: 把工具放入对应 namespace；如果没有这一行，最终 namespace 会没有工具。
    descriptions = namespace_descriptions or {}  # 新增代码+OAuthNativeComputerUseNamespace: 读取调用方提供的 namespace 说明或空字典；如果没有这一行，描述查找可能访问 None。
    native_tools: list[dict[str, Any]] = []  # 新增代码+OAuthNativeComputerUseNamespace: 准备最终 Responses 顶层 tools；如果没有这一行，无法累积多个 namespace。
    for namespace_name in sorted(buckets):  # 新增代码+OAuthNativeComputerUseNamespace: 按名称排序保证请求体稳定；如果没有这一行，测试和缓存会因字典顺序漂移。
        native_tools.append(  # 新增代码+OAuthNativeComputerUseNamespace: 追加一个 namespace 对象；如果没有这一行，分组不会进入最终 payload。
            {  # 新增代码+OAuthNativeComputerUseNamespace: namespace 对象开始；如果没有这一行，工具分组没有结构。
                "type": "namespace",  # 新增代码+OAuthNativeComputerUseNamespace: 声明 Responses namespace 类型；如果没有这一行，OpenAI 后端无法识别分组。
                "name": namespace_name,  # 新增代码+OAuthNativeComputerUseNamespace: 写入 namespace 名；如果没有这一行，工具路径不稳定。
                "description": descriptions.get(namespace_name, f"OpenHarness {namespace_name} tools available to this agent turn."),  # 新增代码+OAuthNativeComputerUseNamespace: 写入 namespace 说明；如果没有这一行，模型缺少分组语义。
                "tools": buckets[namespace_name],  # 新增代码+OAuthNativeComputerUseNamespace: 放入该 namespace 下的工具；如果没有这一行，namespace 会是空壳。
            }  # 新增代码+OAuthNativeComputerUseNamespace: namespace 对象结束；如果没有这一行，Python 字典语法不完整。
        )  # 新增代码+OAuthNativeComputerUseNamespace: 结束 namespace append；如果没有这一行，Python 调用语法不完整。
    if has_deferred_tool:  # 新增代码+OAuthNativeToolSearchContract: 只有 namespace 内真实含有 deferred 工具时才启用 hosted tool_search；如果没有这一行，真实 OAuth 后端会返回 invalid_request_error。
        native_tools.append({"type": "tool_search"})  # 修改代码+OAuthNativeToolSearchContract: 按协议安全追加 hosted tool_search；如果没有这一行，有 deferred 工具时模型无法通过原生搜索发现它们。
    return native_tools  # 新增代码+OAuthNativeComputerUseNamespace: 返回完整 Responses native tools 列表；如果没有这一行，OAuth adapter 拿不到顶层 tools。
# 新增代码+OAuthNativeComputerUseNamespace: 函数段结束，build_hosted_tool_search_tools_by_namespace 到此结束；如果没有这个边界说明，用户不容易看出多 namespace 构造范围。


def default_responses_namespace_for_tool_name(tool_name: str) -> str:  # 新增代码+OAuthNativeComputerUseNamespace: 函数段开始，按工具名给 Responses native tools 分配默认 namespace；如果没有这个函数，catalog runtime 会重复硬编码分组。
    if tool_name in COMPUTER_USE_TOOL_NAMES or tool_name.startswith("mcp__computer-use__"):  # 新增代码+OAuthNativeComputerUseNamespace: 识别内置和 MCP 风格 Computer Use 工具；如果没有这一行，桌面工具可能不进 computer_use namespace。
        return COMPUTER_USE_NAMESPACE  # 新增代码+OAuthNativeComputerUseNamespace: 返回 Computer Use namespace；如果没有这一行，权限/观察工具会混入通用分组。
    if tool_name in CORE_CODE_TOOL_NAMES:  # 新增代码+OAuthNativeComputerUseNamespace: 识别核心代码工具；如果没有这一行，read/edit/bash 可能落入兜底 namespace。
        return CORE_CODE_NAMESPACE  # 新增代码+OAuthNativeComputerUseNamespace: 返回 core_code namespace；如果没有这一行，核心工具分组不稳定。
    return DEFAULT_NAMESPACE  # 新增代码+OAuthNativeComputerUseNamespace: 未知工具使用兜底 namespace；如果没有这一行，临时工具没有分组。
# 新增代码+OAuthNativeComputerUseNamespace: 函数段结束，default_responses_namespace_for_tool_name 到此结束；如果没有这个边界说明，用户不容易看出分组规则范围。


def default_responses_namespace_descriptions() -> dict[str, str]:  # 新增代码+OAuthNativeComputerUseNamespace: 函数段开始，返回默认 namespace 说明；如果没有这个函数，工具分组说明会散落在调用方。
    return {  # 新增代码+OAuthNativeComputerUseNamespace: 返回说明字典；如果没有这一行，调用方拿不到稳定说明。
        CORE_CODE_NAMESPACE: "Core OpenHarness coding tools for reading, editing, writing files, and running shell commands.",  # 新增代码+OAuthNativeComputerUseNamespace: 核心代码工具说明；如果没有这一行，模型不知道 core_code 的职责。
        COMPUTER_USE_NAMESPACE: "Windows Computer Use tools for safe desktop permission checks, observation, clipboard, and agent-owned app interaction.",  # 新增代码+OAuthNativeComputerUseNamespace: Computer Use 工具说明；如果没有这一行，模型难以理解桌面工具边界。
        DEFAULT_NAMESPACE: DEFAULT_RESPONSES_NAMESPACE_DESCRIPTION,  # 新增代码+OAuthNativeComputerUseNamespace: 兜底 namespace 说明；如果没有这一行，未知工具分组没有说明。
    }  # 新增代码+OAuthNativeComputerUseNamespace: 说明字典结束；如果没有这一行，Python 字典语法不完整。
# 新增代码+OAuthNativeComputerUseNamespace: 函数段结束，default_responses_namespace_descriptions 到此结束；如果没有这个边界说明，用户不容易看出说明来源。


def parse_responses_function_arguments(raw_arguments: Any) -> dict[str, Any]:  # 新增代码+OAuthNativeOutputParser: 函数段开始，把 Responses function_call.arguments 解析成 dict；如果没有这段函数，工具执行器会收到字符串或坏参数。
    if isinstance(raw_arguments, dict):  # 新增代码+OAuthNativeOutputParser: 兼容后端直接给 dict 的情况；如果没有这一行，dict 参数会被错误转成字符串再解析。
        return dict(raw_arguments)  # 新增代码+OAuthNativeOutputParser: 返回参数副本避免污染原始 item；如果没有这一行，调用方修改参数会改到审计证据。
    raw_text = str(raw_arguments or "{}")  # 新增代码+OAuthNativeOutputParser: 把缺失或字符串参数规范成 JSON 文本；如果没有这一行，None 会导致 json.loads 报错。
    try:  # 新增代码+OAuthNativeOutputParser: 捕获模型输出的坏 JSON；如果没有这一行，单个坏参数会让整个模型响应崩溃。
        parsed = json.loads(raw_text)  # 新增代码+OAuthNativeOutputParser: 解析 JSON 参数；如果没有这一行，工具参数无法变成 dict。
    except json.JSONDecodeError:  # 新增代码+OAuthNativeOutputParser: 处理坏 JSON 参数；如果没有这一行，解析异常会中断任务。
        return {}  # 新增代码+OAuthNativeOutputParser: 坏参数回退为空 dict；如果没有这一行，工具执行器拿不到安全兜底。
    return parsed if isinstance(parsed, dict) else {}  # 新增代码+OAuthNativeOutputParser: 只接受对象形态参数；如果没有这一行，列表或字符串参数会污染工具执行器。
# 新增代码+OAuthNativeOutputParser: 函数段结束，parse_responses_function_arguments 到此结束；如果没有这个边界说明，用户不容易看出参数解析范围。


def text_parts_from_responses_message_item(item: dict[str, Any]) -> list[str]:  # 新增代码+OAuthNativeOutputParser: 函数段开始，从 Responses message item 提取文本片段；如果没有这段函数，native 模式无工具回答可能没有 text。
    content = item.get("content", [])  # 新增代码+OAuthNativeOutputParser: 读取 message.content；如果没有这一行，无法遍历文本块。
    if not isinstance(content, list):  # 新增代码+OAuthNativeOutputParser: 只处理列表形态内容；如果没有这一行，字符串 content 会被误当成块遍历。
        return []  # 新增代码+OAuthNativeOutputParser: 非列表 content 不产生文本；如果没有这一行，异常形态可能导致后续报错。
    text_parts: list[str] = []  # 新增代码+OAuthNativeOutputParser: 准备保存文本片段；如果没有这一行，无法累积多个 content 文本。
    for content_item in content:  # 新增代码+OAuthNativeOutputParser: 遍历 Responses content 块；如果没有这一行，无法逐块提取文本。
        if isinstance(content_item, dict) and isinstance(content_item.get("text"), str):  # 新增代码+OAuthNativeOutputParser: 只接受含 text 字符串的块；如果没有这一行，图片或其它块可能污染文本。
            text_parts.append(str(content_item["text"]))  # 新增代码+OAuthNativeOutputParser: 保存文本块内容；如果没有这一行，最终回答文本会丢失。
    return text_parts  # 新增代码+OAuthNativeOutputParser: 返回提取到的文本片段；如果没有这一行，调用方拿不到文本。
# 新增代码+OAuthNativeOutputParser: 函数段结束，text_parts_from_responses_message_item 到此结束；如果没有这个边界说明，用户不容易看出文本提取范围。


def parse_responses_output_items_to_model_message(output_items: list[dict[str, Any]]) -> ModelMessage:  # 新增代码+OAuthNativeOutputParser: 函数段开始，把 Responses 原生 output items 转成内部 ModelMessage；如果没有这段函数，OAuth native 模式无法进入现有工具执行器。
    tool_calls: list[ToolCall] = []  # 新增代码+OAuthNativeOutputParser: 准备保存转换出的内部工具调用；如果没有这一行，function_call 没有容器。
    text_parts: list[str] = []  # 新增代码+OAuthNativeOutputParser: 准备保存原生 message 文本；如果没有这一行，无工具回答无法汇总。
    for index, item in enumerate(output_items):  # 新增代码+OAuthNativeOutputParser: 遍历每个原生 output item 并保留序号；如果没有这一行，无法逐个处理 function_call/message。
        if not isinstance(item, dict):  # 新增代码+OAuthNativeOutputParser: 防御异常非 dict item；如果没有这一行，坏数据会导致 .get 报错。
            continue  # 新增代码+OAuthNativeOutputParser: 跳过坏 item 继续解析其它输出；如果没有这一行，单个坏 item 会阻断整轮。
        item_type = str(item.get("type", "") or "")  # 新增代码+OAuthNativeOutputParser: 读取原生 item 类型；如果没有这一行，分支判断没有依据。
        if item_type == "function_call":  # 新增代码+OAuthNativeOutputParser: 处理原生工具调用；如果没有这一行，模型请求的工具不会执行。
            arguments = parse_responses_function_arguments(item.get("arguments", "{}"))  # 新增代码+OAuthNativeOutputParser: 解析 function_call 参数；如果没有这一行，工具执行器拿不到 dict 参数。
            call_id = str(item.get("call_id", "") or f"call_native_{index}")  # 新增代码+OAuthNativeOutputParser: 保留 call_id 或生成字符串兜底；如果没有这一行，工具结果回填可能无法配对。
            tool_calls.append(ToolCall(name=str(item.get("name", "")), arguments=arguments, call_id=call_id))  # 新增代码+OAuthNativeOutputParser: 转成内部 ToolCall；如果没有这一行，现有 execute_tool_calls 无法复用。
        if item_type == "message":  # 新增代码+OAuthNativeOutputParser: 处理原生文本消息；如果没有这一行，native 模式直接回答会没有 text。
            text_parts.extend(text_parts_from_responses_message_item(item))  # 新增代码+OAuthNativeOutputParser: 提取并追加文本片段；如果没有这一行，message.content 的文本会丢失。
    return ModelMessage(decision_note="Responses native output parsed.", text="".join(text_parts), tool_calls=tool_calls, native_output_items=list(output_items))  # 新增代码+OAuthNativeOutputParser: 返回内部模型消息并保留原生证据；如果没有这一行，主循环拿不到工具调用和审计 item。
# 新增代码+OAuthNativeOutputParser: 函数段结束，parse_responses_output_items_to_model_message 到此结束；如果没有这个边界说明，用户不容易看出 parser 输出范围。
