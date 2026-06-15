"""Computer Use MCP 原子工具到 agent 会话能力的适配层。"""  # 新增代码+McpSessionAdapter: 说明本文件负责把独立 MCP 工具接回 agent 主循环；如果没有这一行，读者很难区分它和独立 stdio executor 的职责。
from __future__ import annotations  # 新增代码+McpSessionAdapter: 延迟解析类型注解；如果没有这一行，回调类型互相引用时可能受导入顺序影响。

import json  # 新增代码+McpSessionAdapter: 用于解析旧工具文本和生成统一 JSON 结果；如果没有这一行，adapter 无法稳定输出机器可读结果。
import re  # 修改代码+ComputerUseMcpV2ResidualCleanup：用于只替换完整旧工具名 token；如果没有这一行，简单 replace 可能误伤 computer_use_mcp_v2 这类新模块名。
import time  # 新增代码+McpSessionAdapter: 用于实现 wait 原子工具；如果没有这一行，等待工具无法给界面加载留时间。
from dataclasses import dataclass, field  # 新增代码+McpSessionAdapter: 用 dataclass 保存回调和状态；如果没有这一行，就要手写大量初始化样板。
from typing import Any, Callable  # 新增代码+McpSessionAdapter: 标注 controller 和回调的动态边界；如果没有这一行，adapter 的 duck typing 意图不清楚。

try:  # 新增代码+McpSessionAdapter: 优先按包路径导入 Computer Use 旧能力；如果没有这一行，正常包运行无法找到 agent_tools。
    from learning_agent.computer_use_mcp_v2.windows_runtime import internal_adapter_tools as computer_use_internal_adapter_tools  # 修改代码+ComputerUseMcpV2InternalAdapterFence：通过内部 facade 导入成熟状态/观察/发现/执行能力；如果没有这一行，session adapter 会继续直接引用旧公开工具名并造成误判。
    from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_tool_schemas import SHELL_FORBIDDEN_ARGUMENT_NAMES, SHELL_FORBIDDEN_TOOL_NAMES  # 新增代码+McpSessionAdapter: 导入 shell 面禁止清单；如果没有这一行，adapter 可能被误用成命令执行入口。
except ModuleNotFoundError as error:  # 新增代码+McpSessionAdapter: 兼容 start_oauth_agent.bat 直接脚本运行；如果没有这一行，脚本路径下可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.internal_adapter_tools", "learning_agent.computer_use_mcp_v2.windows_runtime.mcp_tool_schemas"}:  # 修改代码+ComputerUseMcpV2InternalAdapterFence：只允许内部 facade 和路径差异进入 fallback；如果没有这一行，真实 bug 会被误当兼容问题隐藏。
        raise  # 新增代码+McpSessionAdapter: 重新抛出非路径错误；如果没有这一行，排查导入问题会很困难。
    from computer_use_mcp_v2.windows_runtime import internal_adapter_tools as computer_use_internal_adapter_tools  # type: ignore  # 修改代码+ComputerUseMcpV2InternalAdapterFence：脚本模式通过内部 facade 导入成熟能力；如果没有这一行，bat 入口会继续直接依赖旧公开工具名。
    from computer_use_mcp_v2.windows_runtime.mcp_tool_schemas import SHELL_FORBIDDEN_ARGUMENT_NAMES, SHELL_FORBIDDEN_TOOL_NAMES  # type: ignore  # 新增代码+McpSessionAdapter: 脚本模式导入禁止清单；如果没有这一行，bat 入口缺少同一套安全边界。


RecordObservation = Callable[[str, dict[str, Any]], None]  # 新增代码+McpSessionAdapter: 定义 observation 回调签名；如果没有这一行，回调字段含义不清楚。
RecordRuntimeTrace = Callable[[str, dict[str, Any]], None]  # 新增代码+McpSessionAdapter: 定义 runtime trace 回调签名；如果没有这一行，agent-side 证据链注入点不清楚。
RecordImageArtifacts = Callable[[dict[str, Any], str], None]  # 新增代码+McpSessionAdapter: 定义截图 artifact 回调签名；如果没有这一行，观察图片如何进入 agent 产物列表不清楚。
AskPermission = Callable[[str], bool]  # 新增代码+McpSessionAdapter: 定义权限询问回调签名；如果没有这一行，高风险动作权限边界不清楚。
ActionGate = Callable[[str, dict[str, Any]], str | None]  # 新增代码+McpSessionAdapter: 定义动作门禁回调签名；如果没有这一行，先观察、先启动、完成收束这些 agent 能力无法表达。
AcceptanceEmitter = Callable[[str, dict[str, Any]], None]  # 新增代码+McpSessionAdapter: 定义验收事件回调签名；如果没有这一行，真实终端验收证据无法注入。


def _noop_record_observation(_kind: str, _payload: dict[str, Any]) -> None:  # 新增代码+McpSessionAdapter: 函数段开始，提供 observation 空回调；如果没有这段函数，轻量测试对象缺回调时会崩溃。
    return None  # 新增代码+McpSessionAdapter: 明确不做任何记录；如果没有这一行，函数没有稳定返回。
# 新增代码+McpSessionAdapter: 函数段结束，_noop_record_observation 到此结束；如果没有这个边界说明，用户不容易看出兜底范围。


def _noop_record_image_artifacts(_payload: dict[str, Any], _source: str) -> None:  # 新增代码+McpSessionAdapter: 函数段开始，提供截图 artifact 空回调；如果没有这段函数，observe/action 在轻量环境会报错。
    return None  # 新增代码+McpSessionAdapter: 明确不登记图片；如果没有这一行，函数没有稳定返回。
# 新增代码+McpSessionAdapter: 函数段结束，_noop_record_image_artifacts 到此结束；如果没有这个边界说明，用户不容易看出兜底范围。


def _noop_emit_acceptance_event(_event_name: str, _payload: dict[str, Any]) -> None:  # 新增代码+McpSessionAdapter: 函数段开始，提供验收事件空回调；如果没有这段函数，非终端测试场景会因缺事件输出失败。
    return None  # 新增代码+McpSessionAdapter: 明确不输出事件；如果没有这一行，函数没有稳定返回。
# 新增代码+McpSessionAdapter: 函数段结束，_noop_emit_acceptance_event 到此结束；如果没有这个边界说明，用户不容易看出兜底范围。


def _allow_permission(_action: str) -> bool:  # 新增代码+McpSessionAdapter: 函数段开始，提供测试级默认授权回调；如果没有这段函数，adapter 独立单测无法进入 fake controller。
    return True  # 新增代码+McpSessionAdapter: 默认允许仅用于显式构造的 adapter；如果没有这一行，旧 computer_action 会保守拒绝所有动作。
# 新增代码+McpSessionAdapter: 函数段结束，_allow_permission 到此结束；如果没有这个边界说明，用户不容易看出默认授权范围。


def _no_action_gate(_action: str, _arguments: dict[str, Any]) -> str | None:  # 新增代码+McpSessionAdapter: 函数段开始，提供动作门禁空实现；如果没有这段函数，adapter 单独使用时缺少 gate 会崩溃。
    return None  # 新增代码+McpSessionAdapter: 默认不阻断；如果没有这一行，旧 computer_action 无法继续执行。
# 新增代码+McpSessionAdapter: 函数段结束，_no_action_gate 到此结束；如果没有这个边界说明，用户不容易看出默认门禁范围。


@dataclass  # 新增代码+McpSessionAdapter: 自动生成回调容器初始化逻辑；如果没有这一行，agent-side binding 需要手写初始化。
class ComputerUseMcpSessionCallbacks:  # 新增代码+McpSessionAdapter: 函数段开始，保存 agent 主循环注入的能力；如果没有这个类，stdio MCP server 很难拿到 ask_permission/trace 等回调。
    ask_permission: AskPermission = _allow_permission  # 新增代码+McpSessionAdapter: 保存权限确认回调；如果没有这一行，高风险动作会绕开或丢失用户确认入口。
    observe_before_action_rejection: ActionGate = _no_action_gate  # 新增代码+McpSessionAdapter: 保存“先观察再动作”门禁；如果没有这一行，MCP 原子动作无法继承旧盲动拦截。
    agent_owned_launch_rejection: ActionGate = _no_action_gate  # 新增代码+McpSessionAdapter: 保存“先由 agent 启动目标软件”门禁；如果没有这一行，MCP 原子动作可能操作用户已有旧窗口。
    completion_signal_for_action: ActionGate = _no_action_gate  # 新增代码+McpSessionAdapter: 保存完成收束门禁；如果没有这一行，任务完成后模型可能继续真实操作。
    record_observation: RecordObservation = _noop_record_observation  # 新增代码+McpSessionAdapter: 保存观察记录回调；如果没有这一行，状态/观察/动作证据不会进入 agent 审计流。
    record_runtime_trace: RecordRuntimeTrace = _noop_record_observation  # 新增代码+McpSessionAdapter: 保存 runtime trace 回调；如果没有这一行，运行证据无法被 long-task harness 回看。
    record_image_artifacts: RecordImageArtifacts = _noop_record_image_artifacts  # 新增代码+McpSessionAdapter: 保存截图 artifact 回调；如果没有这一行，observe/action 返回的截图不会进入 active_artifacts。
    emit_acceptance_event: AcceptanceEmitter = _noop_emit_acceptance_event  # 新增代码+McpSessionAdapter: 保存验收事件回调；如果没有这一行，真实终端验收无法消费动作结果事件。
# 新增代码+McpSessionAdapter: 函数段结束，ComputerUseMcpSessionCallbacks 到此结束；如果没有这个边界说明，用户不容易看出 agent-side 回调集合范围。


@dataclass  # 新增代码+McpSessionAdapter: 自动生成会话状态初始化逻辑；如果没有这一行，state 要手写构造函数。
class ComputerUseMcpSessionState:  # 修改代码+ClaudeCodeParity: 函数段开始，保存一次 agent 会话内共享状态并记录 parity 鼠标按下状态；如果没有这个类，request_access、clipboard、鼠标状态无法跨工具调用闭环。
    grants: dict[str, Any] = field(default_factory=dict)  # 新增代码+McpSessionAdapter: 保存授权申请摘要；如果没有这一行，list_granted_applications 没有事实源。
    clipboard_text: str = ""  # 新增代码+McpSessionAdapter: 保存受控内存剪贴板文本；如果没有这一行，write_clipboard 后 read_clipboard 读不回内容。
    last_observed_window: dict[str, Any] = field(default_factory=dict)  # 新增代码+McpObservedWindowFix: 保存最近一次 observe 得到的可信窗口；如果没有这一行，后续 click/type/key 会因缺 window 被旧 Phase 30 门禁拒绝。
    pressed_mouse_buttons: set[str] = field(default_factory=set)  # 新增代码+ClaudeCodeParity: 只记录 adapter 会话认为已按下的鼠标按钮；如果没有这一行，后续 Task 4 接真实低层事件时缺少保守状态入口。
# 新增代码+McpSessionAdapter: 函数段结束，ComputerUseMcpSessionState 到此结束；如果没有这个边界说明，用户不容易看出状态范围。


def _json_result(tool_name: str, ok: bool, payload: dict[str, Any], *, error_class: str = "") -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，生成统一工具结果；如果没有这段函数，每个分支输出字段会漂移。
    result = {"ok": bool(ok), "tool_name": tool_name, "error_class": error_class, "payload": payload}  # 新增代码+McpSessionAdapter: 构造机器可读结果主体；如果没有这一行，模型无法稳定判断成功失败。
    result["text"] = json.dumps(result, ensure_ascii=False, sort_keys=True)  # 新增代码+McpSessionAdapter: 生成 MCP 可返回的文本副本；如果没有这一行，调用方还要重复序列化。
    return result  # 新增代码+McpSessionAdapter: 返回统一结果对象；如果没有这一行，调用方拿不到执行结果。
# 新增代码+McpSessionAdapter: 函数段结束，_json_result 到此结束；如果没有这个边界说明，用户不容易看出统一输出范围。


def _contains_forbidden_argument_key(value: Any) -> bool:  # 新增代码+McpSessionAdapter: 函数段开始，递归检查危险参数名；如果没有这段函数，batch.steps.arguments.command 可绕过顶层检查。
    if isinstance(value, dict):  # 新增代码+McpSessionAdapter: 处理 JSON 对象；如果没有这一行，字典键不会被检查。
        for key, item in value.items():  # 新增代码+McpSessionAdapter: 遍历每个键值；如果没有这一行，只能检查对象整体字符串。
            if str(key).strip().lower() in SHELL_FORBIDDEN_ARGUMENT_NAMES:  # 新增代码+McpSessionAdapter: 命中 command/script 等禁止字段时拒绝；如果没有这一行，Computer Use 可能被误用成命令执行工具。
                return True  # 新增代码+McpSessionAdapter: 返回发现危险字段；如果没有这一行，检查结果无法上报。
            if _contains_forbidden_argument_key(item):  # 新增代码+McpSessionAdapter: 继续检查嵌套值；如果没有这一行，危险字段可藏在数组或子对象里。
                return True  # 新增代码+McpSessionAdapter: 子层命中时向上传递；如果没有这一行，递归结果会丢失。
    if isinstance(value, list):  # 新增代码+McpSessionAdapter: 处理 JSON 数组；如果没有这一行，批量步骤列表不会被检查。
        return any(_contains_forbidden_argument_key(item) for item in value)  # 新增代码+McpSessionAdapter: 检查每个数组元素；如果没有这一行，危险字段可藏在列表项里。
    return False  # 新增代码+McpSessionAdapter: 非容器类型默认安全；如果没有这一行，函数没有稳定布尔返回。
# 新增代码+McpSessionAdapter: 函数段结束，_contains_forbidden_argument_key 到此结束；如果没有这个边界说明，用户不容易看出递归检查范围。


def _reject_shell_surface(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:  # 新增代码+McpSessionAdapter: 函数段开始，拒绝命令执行面；如果没有这段函数，MCP Computer Use 可能被 bash/powershell 抢跑。
    normalized_name = str(tool_name or "").strip().lower()  # 新增代码+McpSessionAdapter: 规范化工具名用于比较；如果没有这一行，大小写变化可能绕过禁止清单。
    if normalized_name in SHELL_FORBIDDEN_TOOL_NAMES:  # 新增代码+McpSessionAdapter: 拒绝命令类工具名；如果没有这一行，bash/powershell 可能进入 Computer Use adapter。
        return _json_result(tool_name, False, {"reason": "Computer Use MCP 不暴露命令执行工具。"}, error_class="shell_tool_forbidden")  # 新增代码+McpSessionAdapter: 返回机器可读拒绝；如果没有这一行，模型不知道为什么不能这样调用。
    if _contains_forbidden_argument_key(arguments):  # 新增代码+McpSessionAdapter: 拒绝命令类参数名；如果没有这一行，command/script 字段可能传入桌面动作。
        return _json_result(tool_name, False, {"reason": "Computer Use MCP 参数中禁止出现命令执行字段。"}, error_class="shell_argument_forbidden")  # 新增代码+McpSessionAdapter: 返回参数拒绝；如果没有这一行，审计无法说明危险面被挡住。
    return None  # 新增代码+McpSessionAdapter: 没有危险面时允许继续；如果没有这一行，调用方无法区分安全和拒绝。
# 新增代码+McpSessionAdapter: 函数段结束，_reject_shell_surface 到此结束；如果没有这个边界说明，用户不容易看出 shell 安全边界。


def _normalize_tool_name(tool_name: str) -> str:  # 新增代码+McpSessionAdapter: 函数段开始，把完整 MCP 名字转成原子名；如果没有这段函数，agent_adapter 传入 mcp__computer-use__left_click 时无法匹配。
    normalized = str(tool_name or "").strip()  # 新增代码+McpSessionAdapter: 清理工具名空白；如果没有这一行，带空格名字会匹配失败。
    prefix = "mcp__computer-use__"  # 新增代码+McpSessionAdapter: 定义 Computer Use MCP 工具名前缀；如果没有这一行，前缀处理会散落多处。
    if normalized.startswith(prefix):  # 新增代码+McpSessionAdapter: 检查是否为完整 MCP 可见工具名；如果没有这一行，完整名会直接进入 controller 当未知动作。
        return normalized[len(prefix):]  # 新增代码+McpSessionAdapter: 去掉 MCP 前缀得到原子名；如果没有这一行，left_click 等原子映射不会生效。
    return normalized  # 新增代码+McpSessionAdapter: 已经是原子名时原样返回；如果没有这一行，函数没有稳定输出。
# 新增代码+McpSessionAdapter: 函数段结束，_normalize_tool_name 到此结束；如果没有这个边界说明，用户不容易看出工具名归一化范围。


def _parse_first_json_object(text: str) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，从旧工具文本中提取首个 JSON 对象；如果没有这段函数，observe/action 追加 marker 后无法恢复结构化 payload。
    stripped = str(text or "").strip()  # 新增代码+McpSessionAdapter: 清理文本空白；如果没有这一行，空白会影响 JSON 判断。
    if not stripped.startswith("{"):  # 新增代码+McpSessionAdapter: 非 JSON 文本直接返回空对象；如果没有这一行，普通拒绝文本会进入 JSON 解析异常。
        return {}  # 新增代码+McpSessionAdapter: 返回空对象表示无法解析；如果没有这一行，调用方无法安全兜底。
    decoder = json.JSONDecoder()  # 新增代码+McpSessionAdapter: 创建标准 JSON 解码器；如果没有这一行，无法只解析文本开头的 JSON。
    try:  # 新增代码+McpSessionAdapter: 捕获旧工具文本不是纯 JSON 的情况；如果没有这一行，actionability marker 会让工具调用失败。
        parsed, _index = decoder.raw_decode(stripped)  # 新增代码+McpSessionAdapter: 只解析第一个 JSON 对象；如果没有这一行，后续 marker 会破坏解析。
    except json.JSONDecodeError:  # 新增代码+McpSessionAdapter: 处理无法解析的文本；如果没有这一行，坏文本会抛到 agent 主循环。
        return {}  # 新增代码+McpSessionAdapter: 返回空对象兜底；如果没有这一行，调用方需要重复异常处理。
    return parsed if isinstance(parsed, dict) else {}  # 新增代码+McpSessionAdapter: 只接受 JSON 对象；如果没有这一行，数组或字符串会让 payload 形态不稳定。
# 新增代码+McpSessionAdapter: 函数段结束，_parse_first_json_object 到此结束；如果没有这个边界说明，用户不容易看出旧文本解析范围。

LEGACY_TOOL_NAME_MODEL_VISIBLE_REPLACEMENTS: tuple[tuple[str, str], ...] = (  # 修改代码+ComputerUseMcpV2ResidualCleanup：定义内部旧工具名到模型可见 v2 工具名的翻译表；如果没有这段常量，旧 adapter 文本会继续把模型引回隐藏接口。
    (r"\bcomputer_status\b", "mcp__computer-use__observe"),  # 修改代码+ComputerUseMcpV2ResidualCleanup：把旧状态入口翻译成只读观察入口；如果没有这行代码，状态文案会看起来像仍有顶层 computer_status。
    (r"\bcomputer_observe\b", "mcp__computer-use__observe"),  # 修改代码+ComputerUseMcpV2ResidualCleanup：把旧观察入口翻译成 v2 observe；如果没有这行代码，observe 结果会泄露旧工具名。
    (r"\bcomputer_discover\b", "mcp__computer-use__request_access"),  # 修改代码+ComputerUseMcpV2ResidualCleanup：把旧发现入口翻译成 v2 授权/发现起点；如果没有这行代码，应用发现结果会建议隐藏 discover。
    (r"\bcomputer_action\b", "mcp__computer-use__computer_batch"),  # 修改代码+ComputerUseMcpV2ResidualCleanup：把旧泛化动作入口翻译成 v2 batch/原子动作入口；如果没有这行代码，模型会继续尝试隐藏 action。
    (r"\bcomputer_use\b", "mcp__computer-use__computer_batch"),  # 修改代码+ComputerUseMcpV2ResidualCleanup：把旧统一入口翻译成 v2 batch；如果没有这行代码，兼容报告会泄露 computer_use。
    (r"\bcomputer-use\b", "mcp__computer-use__computer_batch"),  # 修改代码+ComputerUseMcpV2ResidualCleanup：把旧连字符入口翻译成 v2 batch；如果没有这行代码，历史别名仍可能出现在模型上下文。
)  # 修改代码+ComputerUseMcpV2ResidualCleanup：翻译表结束；如果没有这行代码，Python 元组语法不完整。


def _sanitize_legacy_tool_names_for_model(text: Any) -> str:  # 修改代码+ComputerUseMcpV2ResidualCleanup：函数段开始，净化将返回给模型的旧 adapter 文本；如果没有这段函数，内部旧函数名会通过 tool result 重新暴露。
    sanitized = str(text or "")  # 修改代码+ComputerUseMcpV2ResidualCleanup：把任意值转成可替换字符串；如果没有这行代码，None 或非字符串结果会让正则处理失败。
    for pattern, replacement in LEGACY_TOOL_NAME_MODEL_VISIBLE_REPLACEMENTS:  # 修改代码+ComputerUseMcpV2ResidualCleanup：逐项应用完整 token 替换；如果没有这行代码，翻译表不会生效。
        sanitized = re.sub(pattern, replacement, sanitized)  # 修改代码+ComputerUseMcpV2ResidualCleanup：只替换完整旧工具名；如果没有这行代码，模型仍会看到旧入口。
    return sanitized  # 修改代码+ComputerUseMcpV2ResidualCleanup：返回净化后的模型可见文本；如果没有这行代码，调用方拿不到净化结果。
    # 修改代码+ComputerUseMcpV2ResidualCleanup：函数段结束，_sanitize_legacy_tool_names_for_model 到此结束；如果没有这个边界说明，用户不容易看出它只处理模型可见文本。


def _sanitize_legacy_payload_for_model(value: Any) -> Any:  # 修改代码+ComputerUseMcpV2ResidualCleanup：函数段开始，递归净化将进入 MCP payload 的旧 adapter 值；如果没有这段函数，JSON 嵌套字段仍可能泄露旧工具名。
    if isinstance(value, dict):  # 修改代码+ComputerUseMcpV2ResidualCleanup：处理 JSON 对象；如果没有这行代码，结构化旧结果里的 tool/next_step 字段不会被净化。
        return {key: _sanitize_legacy_payload_for_model(item) for key, item in value.items()}  # 修改代码+ComputerUseMcpV2ResidualCleanup：递归净化字典值但保留键名；如果没有这行代码，嵌套 payload 仍可能残留旧入口。
    if isinstance(value, list):  # 修改代码+ComputerUseMcpV2ResidualCleanup：处理 JSON 数组；如果没有这行代码，next_tools 这类列表会继续暴露旧名。
        return [_sanitize_legacy_payload_for_model(item) for item in value]  # 修改代码+ComputerUseMcpV2ResidualCleanup：逐项净化列表内容；如果没有这行代码，列表里的旧工具名不会被翻译。
    if isinstance(value, str):  # 修改代码+ComputerUseMcpV2ResidualCleanup：只对字符串做正则替换；如果没有这行代码，布尔值和数字会被不必要地转成字符串。
        return _sanitize_legacy_tool_names_for_model(value)  # 修改代码+ComputerUseMcpV2ResidualCleanup：复用文本净化函数；如果没有这行代码，payload 字符串和普通文本净化规则会漂移。
    return value  # 修改代码+ComputerUseMcpV2ResidualCleanup：非字符串标量原样返回；如果没有这行代码，结构化数据类型会被破坏。
    # 修改代码+ComputerUseMcpV2ResidualCleanup：函数段结束，_sanitize_legacy_payload_for_model 到此结束；如果没有这个边界说明，读者不容易看出递归净化范围。


def _wrap_legacy_text(tool_name: str, legacy_internal_tool: str, legacy_text: str) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，把旧工具文本包成 MCP 统一结果；如果没有这段函数，新旧结果格式会混杂。
    legacy_payload = _parse_first_json_object(legacy_text)  # 新增代码+McpSessionAdapter: 尝试解析旧工具结构化输出；如果没有这一行，request_access/status/discover 的 JSON 会变成普通文本。
    ok = not _legacy_text_indicates_failure(legacy_text, legacy_payload)  # 修改代码+McpObserveMapping: 用统一失败识别判断旧文本是否失败；如果没有这一行，computer_observe 失败和 full 模式拒绝会被 MCP 包装成 ok=true。
    model_visible_internal_tool = _sanitize_legacy_tool_names_for_model(legacy_internal_tool)  # 修改代码+ComputerUseMcpV2ResidualCleanup：把内部路由名翻译成 v2 模型可见名；如果没有这行代码，payload 会直接显示旧 computer_observe/computer_action。
    model_visible_payload = _sanitize_legacy_payload_for_model(legacy_payload)  # 修改代码+ComputerUseMcpV2ResidualCleanup：净化结构化旧结果；如果没有这行代码，JSON 字段会继续建议旧接口。
    model_visible_text = _sanitize_legacy_tool_names_for_model(legacy_text)  # 修改代码+ComputerUseMcpV2ResidualCleanup：净化普通旧文本；如果没有这行代码，actionability marker 会继续泄露旧工具名。
    payload = {"execution_route": "agent-side adapter", "legacy_internal_tool": model_visible_internal_tool, "legacy_payload": model_visible_payload, "legacy_text": model_visible_text}  # 修改代码+ComputerUseMcpV2ResidualCleanup：只把净化后的 adapter 证据返回给模型；如果没有这行代码，v2 工具结果会把旧入口重新暴露。
    return _json_result(tool_name, ok, payload, error_class="" if ok else "legacy_computer_use_rejected")  # 新增代码+McpSessionAdapter: 返回统一结果；如果没有这一行，调用方拿不到一致字段。
# 新增代码+McpSessionAdapter: 函数段结束，_wrap_legacy_text 到此结束；如果没有这个边界说明，用户不容易看出旧文本包装范围。


# 新增代码+McpObserveMapping: 函数段开始，_legacy_text_indicates_failure 识别旧工具普通文本里的失败语义；如果没有这段函数，旧工具非 JSON 失败文本会继续被 adapter 当成功。
def _legacy_text_indicates_failure(legacy_text: str, legacy_payload: dict[str, Any]) -> bool:  # 新增代码+McpObserveMapping: 声明旧文本失败判断入口；如果没有这一行，_wrap_legacy_text 只能靠脆弱的 startswith 判断。
    if legacy_payload:  # 新增代码+McpObserveMapping: 旧工具返回 JSON 时优先相信结构化 ok 字段；如果没有这一行，结构化失败可能被后面的文本规则误判。
        return not bool(legacy_payload.get("ok", True))  # 新增代码+McpObserveMapping: ok=false 就表示失败；如果没有这一行，request_access 等结构化结果的失败状态会丢失。
    normalized_text = str(legacy_text or "").strip()  # 新增代码+McpObserveMapping: 清理旧工具文本用于匹配；如果没有这一行，空白和 None 会干扰失败识别。
    failure_markers = ("用户拒绝", "已拒绝", "失败：", "observe_before_action_required", "agent_owned_launch_required", "legacy_computer_use_rejected")  # 新增代码+McpObserveMapping: 集中列出旧工具会用到的失败/拒绝标记；如果没有这一行，观察失败和门禁拒绝仍可能被包成成功。
    return any(marker in normalized_text[:240] for marker in failure_markers)  # 新增代码+McpObserveMapping: 只检查开头短文本避免误读深层数据；如果没有这一行，函数没有稳定布尔输出。
# 新增代码+McpObserveMapping: 函数段结束，_legacy_text_indicates_failure 到此结束；如果没有这个边界说明，用户不容易看出失败识别范围。


def _normalize_request_access_arguments(arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，把 ClaudeCode 风格授权参数转为旧 request_access 参数；如果没有这段函数，applications 会丢失。
    applications = arguments.get("applications", arguments.get("requested_apps", []))  # 新增代码+McpSessionAdapter: 兼容 MCP 的 applications 和旧 requested_apps；如果没有这一行，模型传 applications 时旧工具看不到目标。
    return {"requested_apps": applications if isinstance(applications, list) else [], "reason": str(arguments.get("reason", "")), "duration_seconds": arguments.get("duration_seconds", 600), "allow_mouse": bool(arguments.get("allow_mouse", True)), "allow_keyboard": bool(arguments.get("allow_keyboard", True)), "allow_clipboard": bool(arguments.get("allow_clipboard", False))}  # 新增代码+McpSessionAdapter: 返回旧工具可读参数；如果没有这一行，授权申请报告不会包含目标、原因和权限位。
# 新增代码+McpSessionAdapter: 函数段结束，_normalize_request_access_arguments 到此结束；如果没有这个边界说明，用户不容易看出授权参数转换范围。


def _controller_arguments_for_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 修改代码+ClaudeCodeParity: 函数段开始，把 MCP 原子名映射为旧 controller action 并补齐 ClaudeCode parity 新工具；如果没有这段函数，click/type/key/triple_click/mouse_down/mouse_up/hold_key 无法复用旧 computer_action。
    if tool_name in {"screenshot", "observe"}:  # 修改代码+McpObserveMapping: observe/screenshot 在 agent-side adapter 里映射为旧 observe 支持的窗口状态观察；如果没有这一行，旧 screenshot 动作会被 controller.observe 拒绝。
        raw_window = arguments.get("window") if isinstance(arguments.get("window"), dict) else {}  # 新增代码+McpObserveMapping: 兼容内部调用传入可信窗口；如果没有这一行，已有 window 也会被默认解析覆盖。
        return {"action": "get_window_state", "window": dict(raw_window), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 修改代码+McpObserveMapping: 返回旧 computer_observe 合法动作；如果没有这一行，full 模式无法得到模型可见截图证据。
    if tool_name == "zoom":  # 修改代码+McpObserveMapping: 支持局部观察语义但仍先走合法窗口状态观察；如果没有这一行，zoom 会落入未知动作。
        raw_window = arguments.get("window") if isinstance(arguments.get("window"), dict) else {}  # 新增代码+McpObserveMapping: 允许内部测试或后续工具传入可信窗口；如果没有这一行，局部观察无法绑定目标窗口。
        return {"action": "get_window_state", "window": dict(raw_window), "confirm_desktop_control": True, "region": {"x": arguments.get("x"), "y": arguments.get("y"), "width": arguments.get("width", 400), "height": arguments.get("height", 300)}, "zoom": True, "reason": arguments.get("reason", "")}  # 修改代码+McpObserveMapping: 保留 zoom 区域元数据并使用合法 observe 动作；如果没有这一行，局部观察语义会丢失或被旧 observe 拒绝。
    if tool_name == "open_application":  # 新增代码+McpSessionAdapter: 支持打开应用工具；如果没有这一行，open_application 不会复用 launch_app。
        return {"action": "launch_app", "target_app": arguments.get("app_name", ""), "app_name": arguments.get("app_name", ""), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+McpSessionAdapter: 返回旧启动动作参数；如果没有这一行，controller 找不到目标应用。
    if tool_name == "mouse_move":  # 新增代码+McpSessionAdapter: 支持鼠标移动工具；如果没有这一行，mouse_move 会进入未知动作。
        return {"action": "move_mouse", "x": arguments.get("x"), "y": arguments.get("y"), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+McpSessionAdapter: 返回移动坐标；如果没有这一行，鼠标移动没有目标位置。
    if tool_name in {"click", "left_click", "middle_click"}:  # 新增代码+McpSessionAdapter: 兼容旧 click、新 left_click 和预留 middle_click；如果没有这一行，模型可见点击名会映射失败。
        button = "middle" if tool_name == "middle_click" else arguments.get("button", "left")  # 新增代码+McpSessionAdapter: 中键固定 middle，其余默认左键；如果没有这一行，middle_click 会误当左键。
        return {"action": "click", "x": arguments.get("x"), "y": arguments.get("y"), "button": button, "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+McpSessionAdapter: 返回点击参数；如果没有这一行，旧 computer_action 无法执行坐标点击。
    if tool_name == "double_click":  # 新增代码+McpSessionAdapter: 支持双击；如果没有这一行，double_click 会落入未知动作。
        return {"action": "double_click", "x": arguments.get("x"), "y": arguments.get("y"), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+McpSessionAdapter: 返回双击参数；如果没有这一行，双击坐标会丢失。
    if tool_name == "triple_click":  # 新增代码+ClaudeCodeParity: 支持 ClaudeCode parity 三击工具；如果没有这一行，triple_click 会落入旧 controller 的未知动作或被错误拒绝。
        return {"action": "triple_click", "x": arguments.get("x"), "y": arguments.get("y"), "button": "left", "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ClaudeCodeParity: 把三击转成 controller 可理解的 triple_click+left；如果没有这一行，三击坐标和左键语义会丢失。
    if tool_name == "left_mouse_down":  # 新增代码+ClaudeCodeParity: 支持 ClaudeCode parity 左键按下工具；如果没有这一行，模型无法表达拖拽前的按下原子动作。
        return {"action": "mouse_down", "x": arguments.get("x"), "y": arguments.get("y"), "button": "left", "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ClaudeCodeParity: 把左键按下转成 controller 的 mouse_down；如果没有这一行，旧执行链不知道要按下哪个按钮。
    if tool_name == "left_mouse_up":  # 新增代码+ClaudeCodeParity: 支持 ClaudeCode parity 左键释放工具；如果没有这一行，模型无法表达不带坐标的释放动作。
        return {"action": "mouse_up", "button": "left", "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ClaudeCodeParity: 把左键释放转成 controller 的 mouse_up；如果没有这一行，旧执行链不知道要释放哪个按钮。
    if tool_name == "right_click":  # 新增代码+McpSessionAdapter: 支持右键点击；如果没有这一行，right_click 无法复用旧 click。
        return {"action": "click", "x": arguments.get("x"), "y": arguments.get("y"), "button": "right", "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+McpSessionAdapter: 用 click+right 表达右键；如果没有这一行，旧 controller 不知道这是右键。
    if tool_name in {"type", "type_text", "write_text", "edit_text"}:  # 新增代码+McpSessionAdapter: 支持 ClaudeCode type 和 OpenHarness 调试输入别名；如果没有这一行，输入文字会重新被 write/edit 文件工具抢语义。
        return {"action": "type_text", "text": arguments.get("text", ""), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+McpSessionAdapter: 返回桌面文本输入参数；如果没有这一行，文本不会进入键盘输入链。
    if tool_name in {"key", "press_key"}:  # 新增代码+McpSessionAdapter: 支持按键和 OpenHarness press_key 别名；如果没有这一行，组合键无法复用旧 press_key。
        keys = arguments.get("keys", arguments.get("key", []))  # 新增代码+McpSessionAdapter: 读取 keys 数组或 key 字符串；如果没有这一行，模型两种写法无法兼容。
        return {"action": "press_key", "key": "+".join(str(key) for key in keys) if isinstance(keys, list) else str(keys), "keys": keys, "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+McpSessionAdapter: 返回按键参数；如果没有这一行，controller 收不到组合键。
    if tool_name == "hold_key":  # 新增代码+ClaudeCodeParity: 支持 ClaudeCode parity 按住组合键工具；如果没有这一行，hold_key 只会带 action 名而丢失 keys 和 duration。
        raw_keys = arguments.get("keys", arguments.get("key", []))  # 新增代码+ClaudeCodeParity: 兼容新 schema 的 keys 数组和旧兼容 key 字段；如果没有这一行，模型传入的按键会丢失。
        normalized_keys = [str(key) for key in raw_keys] if isinstance(raw_keys, list) else ([str(raw_keys)] if raw_keys else [])  # 新增代码+ClaudeCodeParity: 把字符串或数组统一成字符串列表；如果没有这一行，controller 可能收到不可预测的 keys 类型。
        return {"action": "hold_key", "keys": normalized_keys, "key": "+".join(normalized_keys), "duration_seconds": arguments.get("duration_seconds", 0.1), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ClaudeCodeParity: 返回新旧兼容的 hold_key 参数；如果没有这一行，旧 controller 只读 key 或新逻辑只读 keys 都可能失败。
    if tool_name == "scroll":  # 新增代码+McpSessionAdapter: 支持滚动；如果没有这一行，scroll 不会进入旧动作链。
        return {"action": "scroll", "x": arguments.get("x"), "y": arguments.get("y"), "delta_y": arguments.get("delta_y", -500), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+McpSessionAdapter: 返回滚动参数；如果没有这一行，滚动方向和位置会丢失。
    if tool_name == "left_click_drag":  # 新增代码+McpSessionAdapter: 支持左键拖拽；如果没有这一行，绘图和拖放无法通过原子工具表达。
        points = [{"x": arguments.get("start_x"), "y": arguments.get("start_y")}, {"x": arguments.get("end_x"), "y": arguments.get("end_y")}]  # 新增代码+McpSessionAdapter: 把起终点转成旧 drag_path 点列；如果没有这一行，controller 不认识 start/end 字段。
        return {"action": "drag_path", "points": points, "duration_seconds": arguments.get("duration_seconds", 0.5), "button": "left", "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+McpSessionAdapter: 返回拖拽路径动作；如果没有这一行，真实低层动作没有路径。
    return {"action": tool_name, "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+McpSessionAdapter: 未知工具交给旧 controller 保守拒绝；如果没有这一行，函数可能返回 None 造成异常。
# 新增代码+McpSessionAdapter: 函数段结束，_controller_arguments_for_tool 到此结束；如果没有这个边界说明，用户不容易看出原子名映射范围。


# 新增代码+McpObserveMapping: 函数段开始，_window_from_observe_result 从 controller 观察结果中取一个可信窗口；如果没有这段函数，observe 默认窗口解析会重复写脆弱字典读取。
def _window_from_observe_result(result: Any) -> dict[str, Any]:  # 新增代码+McpObserveMapping: 声明观察结果窗口提取入口；如果没有这一行，默认观察无法把 active/list_windows 结果转成 get_window_state 参数。
    data = getattr(result, "data", {}) if isinstance(getattr(result, "data", {}), dict) else {}  # 新增代码+McpObserveMapping: 安全读取 controller 返回 data；如果没有这一行，异常结果会触发属性错误。
    window = data.get("window") if isinstance(data.get("window"), dict) else {}  # 新增代码+McpObserveMapping: 优先读取 get_active_window 的单窗口；如果没有这一行，活动窗口不会被使用。
    if window:  # 新增代码+McpObserveMapping: 判断是否已经拿到窗口；如果没有这一行，后续会无谓扫描列表。
        return dict(window)  # 新增代码+McpObserveMapping: 返回副本避免污染 controller 数据；如果没有这一行，后续补字段可能改到原结果。
    windows = data.get("windows") if isinstance(data.get("windows"), list) else []  # 新增代码+McpObserveMapping: 读取 list_windows 返回的窗口列表；如果没有这一行，活动窗口为空时无法降级。
    for raw_window in windows:  # 新增代码+McpObserveMapping: 顺序寻找第一个安全窗口；如果没有这一行，列表结果不会被使用。
        if isinstance(raw_window, dict) and raw_window:  # 新增代码+McpObserveMapping: 只接受非空字典窗口；如果没有这一行，坏数据可能进入 get_window_state。
            return dict(raw_window)  # 新增代码+McpObserveMapping: 返回可信窗口副本；如果没有这一行，默认观察无法继续。
    return {}  # 新增代码+McpObserveMapping: 没有窗口时返回空字典；如果没有这一行，函数没有稳定失败输出。
# 新增代码+McpObserveMapping: 函数段结束，_window_from_observe_result 到此结束；如果没有这个边界说明，用户不容易看出窗口提取范围。


# 新增代码+McpObserveMapping: 函数段开始，_resolve_default_observation_window 自动为 observe 找到安全窗口；如果没有这段函数，模型无法在封闭 schema 下传 action/window 时会被 full 模式卡住。
def _resolve_default_observation_window(controller: Any, reason: str) -> dict[str, Any]:  # 新增代码+McpObserveMapping: 声明默认窗口解析入口；如果没有这一行，_call_observe 会堆入多步解析细节。
    try:  # 新增代码+McpObserveMapping: 防御 controller 后端不可用或观察异常；如果没有这一行，默认窗口解析失败会中断 MCP 工具。
        active_result = controller.observe({"action": "get_active_window", "confirm_desktop_control": True, "reason": reason})  # 新增代码+McpObserveMapping: 先读活动安全窗口；如果没有这一行，observe 无法自动绑定当前桌面上下文。
        active_window = _window_from_observe_result(active_result)  # 新增代码+McpObserveMapping: 从活动窗口结果提取 window；如果没有这一行，后续不知道是否解析成功。
        if active_window:  # 新增代码+McpObserveMapping: 活动窗口可用时直接返回；如果没有这一行，会多做一次窗口列表扫描。
            return active_window  # 新增代码+McpObserveMapping: 返回活动窗口作为 get_window_state 目标；如果没有这一行，模型可见截图观察仍缺目标。
        list_result = controller.observe({"action": "list_windows", "confirm_desktop_control": True, "reason": reason})  # 新增代码+McpObserveMapping: 活动窗口不可用时降级读取安全窗口列表；如果没有这一行，前台是终端/Codex 被过滤时无法恢复。
        return _window_from_observe_result(list_result)  # 新增代码+McpObserveMapping: 返回列表中的第一个安全窗口或空字典；如果没有这一行，降级结果不会传回调用方。
    except Exception:  # 新增代码+McpObserveMapping: 捕获默认解析异常，后续让正式 computer_observe 返回可审计失败；如果没有这一行，工具会抛异常而不是给模型纠错文本。
        return {}  # 新增代码+McpObserveMapping: 解析异常时返回空窗口；如果没有这一行，函数没有安全兜底。
# 新增代码+McpObserveMapping: 函数段结束，_resolve_default_observation_window 到此结束；如果没有这个边界说明，用户不容易看出默认窗口解析范围。


def _action_can_reuse_observed_window(legacy_arguments: dict[str, Any]) -> bool:  # 修改代码+ClaudeCodeParity: 函数段开始，判断旧动作是否适合复用 observe 窗口并包含新增 parity 动作；如果没有这段函数，launch_app 可能被错误塞窗，而三击/按下/释放/hold_key 又会缺 window。
    action_name = str(legacy_arguments.get("action", "")).strip().lower()  # 新增代码+McpObservedWindowFix: 读取旧 controller action 名；如果没有这一行，无法区分点击、输入、启动等动作。
    reusable_actions = {"click", "double_click", "move_mouse", "type_text", "press_key", "scroll", "drag_path", "triple_click", "mouse_down", "mouse_up", "hold_key"}  # 修改代码+ClaudeCodeParity: 限定需要桌面目标的动作集合并加入新增 parity 动作；如果没有这一行，新工具 observe 后仍可能因缺 window 被门禁拒绝。
    return action_name in reusable_actions  # 新增代码+McpObservedWindowFix: 返回是否可复用窗口；如果没有这一行，调用方无法做布尔判断。
# 新增代码+McpObservedWindowFix: 函数段结束，_action_can_reuse_observed_window 到此结束；如果没有这个边界说明，用户不容易看出窗口复用规则。


@dataclass  # 新增代码+McpSessionAdapter: 自动生成 adapter 初始化逻辑；如果没有这一行，构造函数会重复样板代码。
class ComputerUseMcpSessionAdapter:  # 新增代码+McpSessionAdapter: 函数段开始，执行 MCP 原子工具并复用 agent 旧能力；如果没有这个类，stdio MCP server 无法拿到 agent 回调。
    controller: Any  # 新增代码+McpSessionAdapter: 保存 Computer Use controller；如果没有这一行，旧 status/observe/action 没有后端。
    callbacks: ComputerUseMcpSessionCallbacks = field(default_factory=ComputerUseMcpSessionCallbacks)  # 新增代码+McpSessionAdapter: 保存 agent 注入的回调；如果没有这一行，权限、trace、截图、验收链会断开。
    state: ComputerUseMcpSessionState = field(default_factory=ComputerUseMcpSessionState)  # 新增代码+McpSessionAdapter: 保存会话状态；如果没有这一行，授权申请和剪贴板跨调用不能共享。

    def call_atomic_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:  # 修改代码+ClaudeCodeParity: 函数段开始，公开执行单个 MCP 原子工具并让新增 parity 工具进入 action 映射；如果没有这段函数，agent_adapter 无法调用这层绑定。
        normalized_tool_name = _normalize_tool_name(tool_name)  # 新增代码+McpSessionAdapter: 把完整 MCP 名转成原子名；如果没有这一行，mcp__computer-use__left_click 无法匹配。
        safe_arguments = dict(arguments or {})  # 新增代码+McpSessionAdapter: 复制参数避免污染调用方；如果没有这一行，后续补字段可能改掉模型原始参数。
        if normalized_tool_name == "computer_batch":  # 新增代码+McpSessionAdapter: batch 先进入逐步执行以保留每步错误；如果没有这一行，嵌套 command 会变成顶层模糊拒绝。
            return self._call_batch(safe_arguments)  # 新增代码+McpSessionAdapter: 委托 batch helper；如果没有这一行，批量逻辑会挤在主函数里。
        rejection = _reject_shell_surface(normalized_tool_name, safe_arguments)  # 新增代码+McpSessionAdapter: 单步工具先执行 shell 面硬拒绝；如果没有这一行，危险参数可能进入旧动作链。
        if rejection is not None:  # 新增代码+McpSessionAdapter: 判断是否命中危险面；如果没有这一行，拒绝结果会被忽略。
            return rejection  # 新增代码+McpSessionAdapter: 返回拒绝且不触碰 controller；如果没有这一行，安全边界会失效。
        if normalized_tool_name == "request_access":  # 新增代码+McpSessionAdapter: 处理授权申请原子工具；如果没有这一行，request_access 会落入未知动作。
            return self._call_request_access(normalized_tool_name, safe_arguments)  # 新增代码+McpSessionAdapter: 委托旧 request_access；如果没有这一行，申请不会进入 observation/trace。
        if normalized_tool_name == "list_granted_applications":  # 新增代码+McpSessionAdapter: 处理授权状态查询；如果没有这一行，模型无法查看最近申请摘要。
            return _json_result(normalized_tool_name, True, {"grants": self.state.grants, "grant_created": False})  # 新增代码+McpSessionAdapter: 返回会话授权摘要；如果没有这一行，授权状态没有模型可读出口。
        if normalized_tool_name == "computer_status":  # 新增代码+McpSessionAdapter: 兼容旧状态工具名作为内部 adapter 能力；如果没有这一行，调试模式无法复用状态链。
            return self._call_status(normalized_tool_name, safe_arguments)  # 新增代码+McpSessionAdapter: 委托旧 status；如果没有这一行，状态查询会绕开 observation。
        if normalized_tool_name == "computer_discover":  # 新增代码+McpSessionAdapter: 兼容旧发现工具名作为内部 adapter 能力；如果没有这一行，调试模式无法复用应用发现链。
            return self._call_discover(normalized_tool_name, safe_arguments)  # 新增代码+McpSessionAdapter: 委托旧 discover；如果没有这一行，应用发现不会进入 trace。
        if normalized_tool_name == "cursor_position":  # 新增代码+McpSessionAdapter: 处理只读鼠标位置工具；如果没有这一行，cursor_position 会被当作 controller 动作。
            return self._call_cursor_position(normalized_tool_name, safe_arguments)  # 新增代码+McpSessionAdapter: 委托位置 helper；如果没有这一行，模型拿不到当前光标位置。
        if normalized_tool_name == "wait":  # 新增代码+McpSessionAdapter: 处理等待工具；如果没有这一行，wait 会误入 controller。
            return self._call_wait(normalized_tool_name, safe_arguments)  # 新增代码+McpSessionAdapter: 委托等待 helper；如果没有这一行，界面加载等待无法表达。
        if normalized_tool_name in {"read_clipboard", "write_clipboard", "clipboard"}:  # 新增代码+McpSessionAdapter: 处理受控剪贴板工具；如果没有这一行，复制粘贴状态不能闭环。
            return self._call_clipboard(normalized_tool_name, safe_arguments)  # 新增代码+McpSessionAdapter: 委托剪贴板 helper；如果没有这一行，read/write_clipboard 会落入未知动作。
        if normalized_tool_name in {"screenshot", "observe", "zoom"}:  # 新增代码+McpSessionAdapter: 处理只读观察原子工具；如果没有这一行，observe 会误用高风险 action 权限链。
            return self._call_observe(normalized_tool_name, safe_arguments)  # 新增代码+McpSessionAdapter: 委托旧 computer_observe；如果没有这一行，截图 artifact 可能丢失。
        return self._call_action(normalized_tool_name, safe_arguments)  # 新增代码+McpSessionAdapter: 其余原子工具按桌面动作处理；如果没有这一行，click/type/key/open_application 等无法执行。
    # 新增代码+McpSessionAdapter: 函数段结束，call_atomic_tool 到此结束；如果没有这个边界说明，用户不容易看出单工具执行范围。

    def _call_request_access(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，执行授权申请；如果没有这段函数，request_access 无法进入旧 observation/trace。
        legacy_arguments = _normalize_request_access_arguments(arguments)  # 新增代码+McpSessionAdapter: 转换 MCP 参数为旧参数；如果没有这一行，applications 字段会丢失。
        legacy_text = computer_use_internal_adapter_tools.internal_request_access(legacy_arguments, self.callbacks.record_observation, self.callbacks.record_runtime_trace)  # 修改代码+ComputerUseMcpV2InternalAdapterFence：通过内部 facade 调用授权申请能力；如果没有这一行，接线层会继续直接引用旧 request_access 工具名。
        wrapped = _wrap_legacy_text(tool_name, "request_access", legacy_text)  # 新增代码+McpSessionAdapter: 包装旧工具结果；如果没有这一行，MCP 返回格式不统一。
        self.state.grants["last_request"] = wrapped["payload"].get("legacy_payload", {})  # 新增代码+McpSessionAdapter: 保存最近申请摘要；如果没有这一行，list_granted_applications 无法回看。
        return wrapped  # 新增代码+McpSessionAdapter: 返回包装后的申请结果；如果没有这一行，调用方拿不到报告。
    # 新增代码+McpSessionAdapter: 函数段结束，_call_request_access 到此结束；如果没有这个边界说明，用户不容易看出授权申请范围。

    def _call_status(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，执行旧状态工具；如果没有这段函数，状态查询会绕开旧 trace。
        legacy_text = computer_use_internal_adapter_tools.internal_status_snapshot(arguments, self.controller, self.callbacks.record_observation, self.callbacks.record_runtime_trace)  # 修改代码+ComputerUseMcpV2InternalAdapterFence：通过内部 facade 调用状态快照能力；如果没有这一行，接线层会继续直接引用旧 computer_status 工具名。
        return _wrap_legacy_text(tool_name, "computer_status", legacy_text)  # 新增代码+McpSessionAdapter: 返回统一包装结果；如果没有这一行，调用方无法读取统一 ok 字段。
    # 新增代码+McpSessionAdapter: 函数段结束，_call_status 到此结束；如果没有这个边界说明，用户不容易看出状态工具范围。

    def _call_discover(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，执行旧应用发现工具；如果没有这段函数，应用发现会和旧 inventory 逻辑分裂。
        legacy_text = computer_use_internal_adapter_tools.internal_discover_applications(arguments, self.callbacks.record_observation, self.callbacks.record_runtime_trace)  # 修改代码+ComputerUseMcpV2InternalAdapterFence：通过内部 facade 调用应用发现能力；如果没有这一行，接线层会继续直接引用旧 computer_discover 工具名。
        return _wrap_legacy_text(tool_name, "computer_discover", legacy_text)  # 新增代码+McpSessionAdapter: 返回统一包装结果；如果没有这一行，模型无法稳定读取发现结果。
    # 新增代码+McpSessionAdapter: 函数段结束，_call_discover 到此结束；如果没有这个边界说明，用户不容易看出发现工具范围。

    def _call_observe(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，执行只读观察工具；如果没有这段函数，截图观察无法进入旧 artifact 链。
        legacy_arguments = _controller_arguments_for_tool(tool_name, arguments)  # 新增代码+McpSessionAdapter: 把 observe/zoom 映射为旧观察参数；如果没有这一行，旧 computer_observe 收不到 action。
        if legacy_arguments.get("action") == "get_window_state" and not legacy_arguments.get("window"):  # 新增代码+McpObserveMapping: schema 没给 window 时自动解析安全窗口；如果没有这一行，observe 会因缺 window 被旧 controller 拒绝。
            resolved_window = _resolve_default_observation_window(self.controller, str(arguments.get("reason", "")))  # 新增代码+McpObserveMapping: 从当前活动窗口或安全窗口列表里取目标；如果没有这一行，full 模式先观察步骤仍无法产生截图证据。
            if resolved_window:  # 新增代码+McpObserveMapping: 只有真的找到可信窗口才补参；如果没有这一行，空窗口会伪装成有效目标。
                legacy_arguments["window"] = resolved_window  # 新增代码+McpObserveMapping: 把解析到的窗口传给 get_window_state；如果没有这一行，旧 observe 仍会报告未知窗口。
        legacy_text = computer_use_internal_adapter_tools.internal_observe_desktop(legacy_arguments, self.controller, self.callbacks.record_observation, self.callbacks.record_runtime_trace, self.callbacks.record_image_artifacts)  # 修改代码+ComputerUseMcpV2InternalAdapterFence：通过内部 facade 调用观察截图能力；如果没有这一行，接线层会继续直接引用旧 computer_observe 工具名。
        wrapped = _wrap_legacy_text(tool_name, "computer_observe", legacy_text)  # 修改代码+McpObservedWindowFix: 先包装 observe 结果再决定是否写 session 状态；如果没有这一行，失败 observe 也可能污染窗口上下文。
        observed_window = legacy_arguments.get("window") if isinstance(legacy_arguments.get("window"), dict) else {}  # 新增代码+McpObservedWindowFix: 读取本次 observe 使用的可信窗口；如果没有这一行，后续 click 无法复用同一目标。
        if bool(wrapped.get("ok")) and observed_window:  # 新增代码+McpObservedWindowFix: 只有成功观察且窗口非空才保存；如果没有这一行，失败或空窗口会污染动作目标。
            self.state.last_observed_window = dict(observed_window)  # 新增代码+McpObservedWindowFix: 把窗口写入会话状态；如果没有这一行，left_click 后续仍会缺少可信 window。
        return wrapped  # 修改代码+McpObservedWindowFix: 返回包装后的 observe 结果；如果没有这一行，调用方拿不到观察结果。
    # 新增代码+McpSessionAdapter: 函数段结束，_call_observe 到此结束；如果没有这个边界说明，用户不容易看出观察工具范围。

    def _call_action(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，执行高风险桌面动作；如果没有这段函数，click/type/key 无法复用旧权限和门禁。
        legacy_arguments = _controller_arguments_for_tool(tool_name, arguments)  # 新增代码+McpSessionAdapter: 把 MCP 原子名映射为旧动作参数；如果没有这一行，旧 computer_action 收不到 action。
        if not legacy_arguments.get("window") and self.state.last_observed_window and _action_can_reuse_observed_window(legacy_arguments):  # 新增代码+McpObservedWindowFix: 动作缺窗口且适合复用时注入最近观察窗口；如果没有这一行，模型 observe 后 click 仍会被 Phase 30 拒绝。
            legacy_arguments["window"] = dict(self.state.last_observed_window)  # 新增代码+McpObservedWindowFix: 传入窗口副本避免污染 session 状态；如果没有这一行，旧 computer_action 收不到可信目标。
            self.callbacks.record_runtime_trace("computer_use_mcp_observed_window_reused", {"tool_name": tool_name, "action": legacy_arguments.get("action", ""), "window_id": legacy_arguments["window"].get("window_id", "")})  # 新增代码+McpObservedWindowFix: 记录窗口复用证据；如果没有这一行，验收失败时难以证明 adapter 是否自动注入目标。
        legacy_text = computer_use_internal_adapter_tools.internal_execute_desktop_action(legacy_arguments, self.controller, self.callbacks.ask_permission, self.callbacks.observe_before_action_rejection, self.callbacks.agent_owned_launch_rejection, self.callbacks.completion_signal_for_action, self.callbacks.record_observation, self.callbacks.record_runtime_trace, self.callbacks.record_image_artifacts, self.callbacks.emit_acceptance_event)  # 修改代码+ComputerUseMcpV2InternalAdapterFence：通过内部 facade 调用桌面执行能力；如果没有这一行，接线层会继续直接引用旧 computer_action 工具名。
        return _wrap_legacy_text(tool_name, "computer_action", legacy_text)  # 新增代码+McpSessionAdapter: 返回统一包装结果；如果没有这一行，MCP 原子工具输出与旧工具文本难以区分。
    # 新增代码+McpSessionAdapter: 函数段结束，_call_action 到此结束；如果没有这个边界说明，用户不容易看出动作工具范围。

    def _call_cursor_position(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，读取当前鼠标位置；如果没有这段函数，cursor_position 只能落入未知动作。
        try:  # 新增代码+McpSessionAdapter: 捕获非 Windows 或 ctypes 不可用场景；如果没有这一行，位置读取失败会中断 agent。
            import ctypes  # 新增代码+McpSessionAdapter: 延迟导入 Windows API 访问库；如果没有这一行，无法读取真实鼠标坐标。
            class _Point(ctypes.Structure):  # 新增代码+McpSessionAdapter: 声明 Windows POINT 结构；如果没有这个类，GetCursorPos 没有写入容器。
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]  # 新增代码+McpSessionAdapter: 定义 x/y 字段；如果没有这一行，Windows API 不知道结构布局。
            point = _Point()  # 新增代码+McpSessionAdapter: 创建坐标容器；如果没有这一行，GetCursorPos 没有输出目标。
            ok = bool(ctypes.windll.user32.GetCursorPos(ctypes.byref(point)))  # type: ignore[attr-defined]  # 新增代码+McpSessionAdapter: 调用 User32 读取坐标；如果没有这一行，工具无法返回真实位置。
            if ok:  # 新增代码+McpSessionAdapter: 只有系统调用成功才返回坐标；如果没有这一行，失败时可能返回默认 0,0。
                return _json_result(tool_name, True, {"x": int(point.x), "y": int(point.y), "backend": "windows_user32", "reason": arguments.get("reason", "")})  # 新增代码+McpSessionAdapter: 返回坐标和后端来源；如果没有这一行，模型无法利用当前位置。
        except Exception as error:  # 新增代码+McpSessionAdapter: 捕获平台/API 异常；如果没有这一行，非 Windows 测试会失败。
            return _json_result(tool_name, False, {"reason": str(error), "backend": "windows_user32"}, error_class="cursor_position_unavailable")  # 新增代码+McpSessionAdapter: 返回不可用原因；如果没有这一行，模型无法恢复。
        return _json_result(tool_name, False, {"reason": "GetCursorPos returned false", "backend": "windows_user32"}, error_class="cursor_position_unavailable")  # 新增代码+McpSessionAdapter: 处理 API 返回 false；如果没有这一行，函数可能隐式返回 None。
    # 新增代码+McpSessionAdapter: 函数段结束，_call_cursor_position 到此结束；如果没有这个边界说明，用户不容易看出位置工具范围。

    def _call_wait(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，执行短等待；如果没有这段函数，wait 无法在界面变化后再观察。
        seconds = max(0.0, min(float(arguments.get("seconds", 1) or 0), 30.0))  # 新增代码+McpSessionAdapter: 限制等待秒数；如果没有这一行，模型可能让 agent 长时间卡住。
        time.sleep(seconds)  # 新增代码+McpSessionAdapter: 真实等待；如果没有这一行，wait 只是空结果不会给 UI 加载时间。
        return _json_result(tool_name, True, {"waited_seconds": seconds, "reason": arguments.get("reason", "")})  # 新增代码+McpSessionAdapter: 返回等待结果；如果没有这一行，模型不知道等待已完成。
    # 新增代码+McpSessionAdapter: 函数段结束，_call_wait 到此结束；如果没有这个边界说明，用户不容易看出等待工具范围。

    def _call_clipboard(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，处理受控剪贴板；如果没有这段函数，剪贴板工具无法闭环。
        operation = str(arguments.get("operation", "")).strip().lower()  # 新增代码+McpSessionAdapter: 读取兼容 clipboard 工具的 operation；如果没有这一行，无法区分读写。
        if tool_name == "read_clipboard" or operation == "read":  # 新增代码+McpSessionAdapter: 处理读取剪贴板；如果没有这一行，read_clipboard 会落入非法操作。
            return _json_result(tool_name, True, {"operation": "read", "text": self.state.clipboard_text, "backend": "agent_session_memory_clipboard", "reason": arguments.get("reason", "")})  # 新增代码+McpSessionAdapter: 返回受控内存剪贴板文本；如果没有这一行，复制粘贴测试无法回读。
        if tool_name == "write_clipboard" or operation == "write":  # 新增代码+McpSessionAdapter: 处理写入剪贴板；如果没有这一行，write_clipboard 不会保存状态。
            self.state.clipboard_text = str(arguments.get("text", ""))  # 新增代码+McpSessionAdapter: 保存受控剪贴板文本；如果没有这一行，后续 read_clipboard 没有内容。
            return _json_result(tool_name, True, {"operation": "write", "text_length": len(self.state.clipboard_text), "backend": "agent_session_memory_clipboard", "reason": arguments.get("reason", "")})  # 新增代码+McpSessionAdapter: 返回写入摘要而不回显全部文本；如果没有这一行，模型不知道写入是否成功。
        return _json_result(tool_name, False, {"reason": "clipboard.operation 必须是 read 或 write。"}, error_class="invalid_clipboard_operation")  # 新增代码+McpSessionAdapter: 拒绝非法剪贴板操作；如果没有这一行，坏参数会悄悄失败。
    # 新增代码+McpSessionAdapter: 函数段结束，_call_clipboard 到此结束；如果没有这个边界说明，用户不容易看出剪贴板范围。

    def _call_batch(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，顺序执行批量工具；如果没有这段函数，computer_batch 无法复用同一 adapter 状态。
        steps = arguments.get("steps", [])  # 新增代码+McpSessionAdapter: 读取步骤列表；如果没有这一行，批量工具不知道要执行什么。
        stop_on_error = bool(arguments.get("stop_on_error", True))  # 新增代码+McpSessionAdapter: 读取失败是否停止；如果没有这一行，批量失败策略不可控。
        if not isinstance(steps, list):  # 新增代码+McpSessionAdapter: 校验 steps 类型；如果没有这一行，坏参数会在遍历时报错。
            return _json_result("computer_batch", False, {"reason": "steps 必须是数组。"}, error_class="invalid_batch_steps")  # 新增代码+McpSessionAdapter: 返回参数错误；如果没有这一行，模型难以修正。
        results: list[dict[str, Any]] = []  # 新增代码+McpSessionAdapter: 保存每一步结果；如果没有这一行，最终报告没有明细。
        for index, raw_step in enumerate(steps):  # 新增代码+McpSessionAdapter: 按顺序遍历 batch 步骤；如果没有这一行，批量不会执行。
            step = raw_step if isinstance(raw_step, dict) else {}  # 新增代码+McpSessionAdapter: 防御非字典步骤；如果没有这一行，坏步骤会触发属性错误。
            step_name = str(step.get("tool_name") or step.get("name") or "")  # 新增代码+McpSessionAdapter: 读取步骤工具名；如果没有这一行，无法分发。
            step_arguments = step.get("arguments", {}) if isinstance(step.get("arguments", {}), dict) else {}  # 新增代码+McpSessionAdapter: 读取步骤参数；如果没有这一行，参数会丢失或崩溃。
            step_result = self.call_atomic_tool(step_name, step_arguments)  # 新增代码+McpSessionAdapter: 复用同一 adapter 执行步骤；如果没有这一行，batch 会绕开 state、shell 拒绝和旧工具链。
            step_result["batch_index"] = index  # 新增代码+McpSessionAdapter: 标记步骤序号；如果没有这一行，失败时难以定位第几步。
            results.append(step_result)  # 新增代码+McpSessionAdapter: 保存步骤结果；如果没有这一行，批量汇总没有明细。
            if stop_on_error and not bool(step_result.get("ok")):  # 新增代码+McpSessionAdapter: 失败且要求停止时中断；如果没有这一行，危险或失败后续动作仍会继续。
                break  # 新增代码+McpSessionAdapter: 停止后续步骤；如果没有这一行，stop_on_error 不生效。
        return _json_result("computer_batch", all(bool(item.get("ok")) for item in results), {"results": results, "step_count": len(results)})  # 新增代码+McpSessionAdapter: 返回批量汇总；如果没有这一行，调用方拿不到整体状态。
    # 新增代码+McpSessionAdapter: 函数段结束，_call_batch 到此结束；如果没有这个边界说明，用户不容易看出批量执行范围。
# 新增代码+McpSessionAdapter: 函数段结束，ComputerUseMcpSessionAdapter 到此结束；如果没有这个边界说明，用户不容易看出 adapter 类范围。
