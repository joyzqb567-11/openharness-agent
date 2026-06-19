"""Computer Use MCP 原子工具到 agent 会话能力的适配层。"""  # 新增代码+McpSessionAdapter: 说明本文件负责把独立 MCP 工具接回 agent 主循环；如果没有这一行，读者很难区分它和独立 stdio executor 的职责。
from __future__ import annotations  # 新增代码+McpSessionAdapter: 延迟解析类型注解；如果没有这一行，回调类型互相引用时可能受导入顺序影响。

import json  # 新增代码+McpSessionAdapter: 用于解析旧工具文本和生成统一 JSON 结果；如果没有这一行，adapter 无法稳定输出机器可读结果。
import re  # 修改代码+ComputerUseMcpV2ResidualCleanup：用于只替换完整旧工具名 token；如果没有这一行，简单 replace 可能误伤 computer_use_mcp_v2 这类新模块名。
import time  # 新增代码+McpSessionAdapter: 用于实现 wait 原子工具；如果没有这一行，等待工具无法给界面加载留时间。
from dataclasses import dataclass, field  # 新增代码+McpSessionAdapter: 用 dataclass 保存回调和状态；如果没有这一行，就要手写大量初始化样板。
from pathlib import Path  # 新增代码+ClaudeCodeZoom: 用 Path 处理 zoom 源图和裁剪图路径；如果没有这一行，裁剪 artifact 路径会退回脆弱字符串拼接。
from typing import Any, Callable  # 新增代码+McpSessionAdapter: 标注 controller 和回调的动态边界；如果没有这一行，adapter 的 duck typing 意图不清楚。

try:  # 新增代码+McpSessionAdapter: 优先按包路径导入 Computer Use 旧能力；如果没有这一行，正常包运行无法找到 agent_tools。
    from learning_agent.computer_use_mcp_v2.windows_runtime import internal_adapter_tools as computer_use_internal_adapter_tools  # 修改代码+ComputerUseMcpV2InternalAdapterFence：通过内部 facade 导入成熟状态/观察/发现/执行能力；如果没有这一行，session adapter 会继续直接引用旧公开工具名并造成误判。
    from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_tool_schemas import SHELL_FORBIDDEN_ARGUMENT_NAMES, SHELL_FORBIDDEN_TOOL_NAMES  # 新增代码+McpSessionAdapter: 导入 shell 面禁止清单；如果没有这一行，adapter 可能被误用成命令执行入口。
    from learning_agent.computer_use_mcp_v2.windows_runtime.resource_identity import RESOURCE_USER_ACTION_REQUIRED_MARKER, build_resource_freshness  # 新增代码+ResourceFreshnessAdapter：导入资源新鲜度判断；如果没有这一行，adapter 只能绑定应用窗口，不能防止写入旧文档资源。
except ModuleNotFoundError as error:  # 新增代码+McpSessionAdapter: 兼容 start_oauth_agent.bat 直接脚本运行；如果没有这一行，脚本路径下可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.internal_adapter_tools", "learning_agent.computer_use_mcp_v2.windows_runtime.mcp_tool_schemas", "learning_agent.computer_use_mcp_v2.windows_runtime.resource_identity"}:  # 修改代码+ResourceFreshnessAdapter：允许资源身份模块在脚本路径下 fallback；如果没有这一行，bat 入口可能因包路径差异启动失败。
        raise  # 新增代码+McpSessionAdapter: 重新抛出非路径错误；如果没有这一行，排查导入问题会很困难。
    from computer_use_mcp_v2.windows_runtime import internal_adapter_tools as computer_use_internal_adapter_tools  # type: ignore  # 修改代码+ComputerUseMcpV2InternalAdapterFence：脚本模式通过内部 facade 导入成熟能力；如果没有这一行，bat 入口会继续直接依赖旧公开工具名。
    from computer_use_mcp_v2.windows_runtime.mcp_tool_schemas import SHELL_FORBIDDEN_ARGUMENT_NAMES, SHELL_FORBIDDEN_TOOL_NAMES  # type: ignore  # 新增代码+McpSessionAdapter: 脚本模式导入禁止清单；如果没有这一行，bat 入口缺少同一套安全边界。
    from computer_use_mcp_v2.windows_runtime.resource_identity import RESOURCE_USER_ACTION_REQUIRED_MARKER, build_resource_freshness  # type: ignore  # 新增代码+ResourceFreshnessAdapter：脚本模式导入资源新鲜度判断；如果没有这一行，start_oauth_agent.bat 看不到旧资源门禁。


RecordObservation = Callable[[str, dict[str, Any]], None]  # 新增代码+McpSessionAdapter: 定义 observation 回调签名；如果没有这一行，回调字段含义不清楚。
RecordRuntimeTrace = Callable[[str, dict[str, Any]], None]  # 新增代码+McpSessionAdapter: 定义 runtime trace 回调签名；如果没有这一行，agent-side 证据链注入点不清楚。
RecordImageArtifacts = Callable[[dict[str, Any], str], None]  # 新增代码+McpSessionAdapter: 定义截图 artifact 回调签名；如果没有这一行，观察图片如何进入 agent 产物列表不清楚。
AskPermission = Callable[[str], bool]  # 新增代码+McpSessionAdapter: 定义权限询问回调签名；如果没有这一行，高风险动作权限边界不清楚。
ActionGate = Callable[[str, dict[str, Any]], str | None]  # 新增代码+McpSessionAdapter: 定义动作门禁回调签名；如果没有这一行，先观察、先启动、完成收束这些 agent 能力无法表达。
AcceptanceEmitter = Callable[[str, dict[str, Any]], None]  # 新增代码+McpSessionAdapter: 定义验收事件回调签名；如果没有这一行，真实终端验收证据无法注入。
ZOOM_IMAGE_RESULT_MODEL = "claudecode_parity_zoom_image_result_v1"  # 新增代码+ClaudeCodeZoom: 定义 zoom 裁剪图的稳定协议名；如果没有这一行，后续审计无法区分全窗口截图和局部放大截图。


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
class ComputerUseMcpSessionState:  # 修改代码+ClaudeCodeParity: 函数段开始，保存一次 agent 会话内共享状态；如果没有这个类，request_access、clipboard 和最近观察窗口无法跨工具调用闭环。
    grants: dict[str, Any] = field(default_factory=dict)  # 新增代码+McpSessionAdapter: 保存授权申请摘要；如果没有这一行，list_granted_applications 没有事实源。
    clipboard_text: str = ""  # 新增代码+McpSessionAdapter: 保存受控内存剪贴板文本；如果没有这一行，write_clipboard 后 read_clipboard 读不回内容。
    last_observed_window: dict[str, Any] = field(default_factory=dict)  # 新增代码+McpObservedWindowFix: 保存最近一次 observe 得到的可信窗口；如果没有这一行，后续 click/type/key 会因缺 window 被旧 Phase 30 门禁拒绝。
    last_resource_freshness: dict[str, Any] = field(default_factory=dict)  # 新增代码+ResourceFreshnessAdapter：保存最近一次 observe 的资源新鲜度；如果没有这一行，发现旧文档后后续键鼠动作仍可能穿透。
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
    if tool_name == "left_mouse_up":  # 修改代码+ClaudeCodeParity: 支持 ClaudeCode parity 左键释放工具并按 schema 保留坐标；如果没有这一行，模型无法表达带坐标证据的释放动作。
        return {"action": "mouse_up", "x": arguments.get("x"), "y": arguments.get("y"), "button": "left", "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 修改代码+ClaudeCodeParity: 把左键释放转成 controller 的 mouse_up 并保留 x/y；如果没有这一行，坐标证据和未来 move-before-up 实现会缺入口。
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


def _active_target_window_from_controller(controller: Any) -> dict[str, Any]:  # 新增代码+ObserveTargetRef：函数段开始，从 controller registry 读取当前已绑定 target 窗口；如果没有这段函数，observe 会优先看前台终端而不是刚打开的目标应用。
    try:  # 新增代码+ObserveTargetRef：保护 registry 读取过程；如果没有这一行，fake controller 或旧 controller 缺字段会让 observe 崩溃。
        target_registry = getattr(controller, "target_registry", None)  # 新增代码+ObserveTargetRef：读取 controller 的目标注册表；如果没有这一行，adapter 无法知道 launch_app 已经登记了哪个窗口。
        get_active_target = getattr(target_registry, "get_active_target", None)  # 新增代码+ObserveTargetRef：读取 active target 方法；如果没有这一行，后续无法兼容没有 registry 的 controller。
        active_target = get_active_target() if callable(get_active_target) else None  # 新增代码+ObserveTargetRef：调用 active target 查询；如果没有这一行，registry 里的 target_ref 不会进入 observe。
    except Exception:  # 新增代码+ObserveTargetRef：捕获 registry 查询异常；如果没有这一行，观察工具会因状态对象问题直接失败。
        return {}  # 新增代码+ObserveTargetRef：查询异常时返回空窗口并走旧观察降级；如果没有这一行，函数没有安全兜底。
    if not isinstance(active_target, dict) or not active_target:  # 新增代码+ObserveTargetRef：检查 active target 是否是有效字典；如果没有这一行，None 或坏对象可能进入窗口解析。
        return {}  # 新增代码+ObserveTargetRef：没有 active target 时返回空窗口；如果没有这一行，旧路径无法继续。
    raw_window = active_target.get("window") if isinstance(active_target.get("window"), dict) else active_target.get("raw_window")  # 新增代码+ObserveTargetRef：优先读取 registry 公开窗口并兼容 raw_window；如果没有这一行，target 记录无法变成 observe 参数。
    if not isinstance(raw_window, dict) or not raw_window:  # 新增代码+ObserveTargetRef：检查窗口事实是否存在；如果没有这一行，空 target 可能被当成有效窗口。
        return {}  # 新增代码+ObserveTargetRef：缺窗口时返回空并降级旧观察；如果没有这一行，get_window_state 会收到坏 window。
    window = dict(raw_window)  # 新增代码+ObserveTargetRef：复制窗口事实；如果没有这一行，给 observe 补 target_ref 会污染 registry 原始记录。
    target_ref = str(active_target.get("target_ref", "") or "").strip()  # 新增代码+ObserveTargetRef：读取稳定窗口 ID；如果没有这一行，观察结果仍缺后续动作必需的 target_ref。
    if target_ref:  # 新增代码+ObserveTargetRef：只在 target_ref 非空时写入；如果没有这一行，空字符串会制造假目标。
        window["target_ref"] = target_ref  # 新增代码+ObserveTargetRef：把 target_ref 放进 observe 窗口；如果没有这一行，模型下一步无法知道该操作哪个窗口。
    lease = active_target.get("lease") if isinstance(active_target.get("lease"), dict) else {}  # 新增代码+ObserveTargetRef：读取租约摘要；如果没有这一行，观察窗口缺少权限来源证据。
    if lease:  # 新增代码+ObserveTargetRef：只在租约存在时补充；如果没有这一行，空 lease 会产生噪音字段。
        window["target_lease"] = dict(lease)  # 新增代码+ObserveTargetRef：把租约副本附加到窗口；如果没有这一行，调试 observe 结果看不到权限边界。
    return window  # 新增代码+ObserveTargetRef：返回带 target_ref 的 active target 窗口；如果没有这一行，调用方拿不到 registry 优先结果。
# 新增代码+ObserveTargetRef：函数段结束，_active_target_window_from_controller 到此结束；如果没有这个边界说明，用户不容易看出 active target 观察范围。


# 新增代码+McpObserveMapping: 函数段开始，_resolve_default_observation_window 自动为 observe 找到安全窗口；如果没有这段函数，模型无法在封闭 schema 下传 action/window 时会被 full 模式卡住。
def _resolve_default_observation_window(controller: Any, reason: str) -> dict[str, Any]:  # 新增代码+McpObserveMapping: 声明默认窗口解析入口；如果没有这一行，_call_observe 会堆入多步解析细节。
    try:  # 新增代码+McpObserveMapping: 防御 controller 后端不可用或观察异常；如果没有这一行，默认窗口解析失败会中断 MCP 工具。
        active_target_window = _active_target_window_from_controller(controller)  # 新增代码+ObserveTargetRef：优先读取 registry 中已绑定的 active target；如果没有这一行，刚启动的目标窗口会被前台终端覆盖。
        if active_target_window:  # 新增代码+ObserveTargetRef：registry 已有目标时直接使用；如果没有这一行，仍会继续调用 get_active_window。
            return active_target_window  # 新增代码+ObserveTargetRef：返回带 target_ref 的目标窗口；如果没有这一行，observe 结果仍可能缺窗口 ID。
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


def _copy_action_target_fields_from_arguments(legacy_arguments: dict[str, Any], arguments: dict[str, Any]) -> None:  # 新增代码+ExplicitTargetRefResourceFallback：函数段开始，把 MCP 原始目标字段补回旧动作参数；如果没有这段函数，target_ref 会在原子工具映射时丢失。
    target_ref = str(arguments.get("target_ref", "") or "").strip()  # 新增代码+ExplicitTargetRefResourceFallback：读取模型显式传入的一对一窗口 ID；如果没有这一行，多窗口任务无法保留用户选中的目标。
    if target_ref and not legacy_arguments.get("target_ref"):  # 新增代码+ExplicitTargetRefResourceFallback：只在旧参数缺 target_ref 时补入；如果没有这一行，后续解析会把显式目标当作缺失目标。
        legacy_arguments["target_ref"] = target_ref  # 新增代码+ExplicitTargetRefResourceFallback：把 target_ref 写回旧 controller 参数；如果没有这一行，adapter 会误走多目标隐式拒绝或单目标自动注入。
    raw_window = arguments.get("window") if isinstance(arguments.get("window"), dict) else {}  # 新增代码+ExplicitTargetRefResourceFallback：读取 MCP 参数里可能携带的窗口对象；如果没有这一行，已有可信窗口会被映射层丢弃。
    if raw_window and not isinstance(legacy_arguments.get("window"), dict):  # 新增代码+ExplicitTargetRefResourceFallback：只在旧参数没有窗口时复制；如果没有这一行，映射层已有窗口可能被覆盖。
        legacy_arguments["window"] = dict(raw_window)  # 新增代码+ExplicitTargetRefResourceFallback：把窗口副本写回旧参数；如果没有这一行，资源门禁看不到动作实际目标。
    raw_target_window = arguments.get("target_window") if isinstance(arguments.get("target_window"), dict) else {}  # 新增代码+ExplicitTargetRefResourceFallback：兼容未来 schema 的 target_window 字段；如果没有这一行，新字段传入时仍会缺窗口。
    if raw_target_window and not isinstance(legacy_arguments.get("window"), dict):  # 新增代码+ExplicitTargetRefResourceFallback：只在 window 仍缺失时使用 target_window；如果没有这一行，两个窗口字段会互相覆盖。
        legacy_arguments["window"] = dict(raw_target_window)  # 新增代码+ExplicitTargetRefResourceFallback：把 target_window 写成旧 controller 可读的 window；如果没有这一行，底层无法复用目标窗口。
    # 新增代码+ExplicitTargetRefResourceFallback：函数段结束，_copy_action_target_fields_from_arguments 到此结束；如果没有这个边界说明，用户不容易看出目标字段保留范围。


def _window_identity_values(window: dict[str, Any]) -> set[str]:  # 新增代码+TargetRefAutoInject：函数段开始，提取窗口里能证明同一对象的身份值；如果没有这段函数，自动补 target_ref 时无法确认 window 和 registry 是否指向同一窗口。
    values: set[str] = set()  # 新增代码+TargetRefAutoInject：准备保存窗口身份值集合；如果没有这一行，后续字段没有容器。
    for field_name in ("window_id", "hwnd", "pid", "process_id"):  # 新增代码+TargetRefAutoInject：遍历通用窗口身份字段；如果没有这一行，只靠标题会让窗口匹配不可靠。
        field_value = str(window.get(field_name, "") or "").strip()  # 新增代码+TargetRefAutoInject：把当前字段转成干净字符串；如果没有这一行，None 或数字会影响比较。
        if field_value:  # 新增代码+TargetRefAutoInject：只保留非空身份值；如果没有这一行，空字符串会让两个缺字段窗口误匹配。
            values.add(field_value)  # 新增代码+TargetRefAutoInject：写入身份值集合；如果没有这一行，函数不会返回任何可比较事实。
    return values  # 新增代码+TargetRefAutoInject：返回身份值集合；如果没有这一行，调用方拿不到比较依据。
# 新增代码+TargetRefAutoInject：函数段结束，_window_identity_values 到此结束；如果没有这个边界说明，用户不容易看出身份提取范围。


def _windows_share_identity(left_window: dict[str, Any], right_window: dict[str, Any]) -> bool:  # 新增代码+TargetRefAutoInject：函数段开始，判断两个窗口事实是否有共同身份值；如果没有这段函数，adapter 可能把 target_ref 注入到错误窗口。
    left_values = _window_identity_values(left_window)  # 新增代码+TargetRefAutoInject：提取左侧窗口身份值；如果没有这一行，比较没有左侧输入。
    right_values = _window_identity_values(right_window)  # 新增代码+TargetRefAutoInject：提取右侧窗口身份值；如果没有这一行，比较没有右侧输入。
    if not left_values or not right_values:  # 新增代码+TargetRefAutoInject：任一侧缺少身份值时不能证明匹配；如果没有这一行，缺字段窗口可能被误认为同一个。
        return False  # 新增代码+TargetRefAutoInject：缺少证据时返回不匹配；如果没有这一行，安全边界会变成猜测。
    return bool(left_values & right_values)  # 新增代码+TargetRefAutoInject：只要有共同身份值就认为同一窗口；如果没有这一行，pid/hwnd/window_id 任一可信字段都无法发挥作用。
# 新增代码+TargetRefAutoInject：函数段结束，_windows_share_identity 到此结束；如果没有这个边界说明，用户不容易看出同窗判断范围。


def _resolve_implicit_target_for_action(controller: Any, legacy_arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+MultiTargetRefGate：函数段开始，为漏 target_ref 的窗口动作读取 registry 隐式解析结果；如果没有这段函数，单目标注入和多目标拒绝会重复写解析逻辑。
    if legacy_arguments.get("target_ref"):  # 新增代码+MultiTargetRefGate：显式 target_ref 已存在时不做隐式解析；如果没有这一行，多目标显式动作也可能被误挡。
        return {}  # 新增代码+MultiTargetRefGate：返回空表示无需隐式处理；如果没有这一行，调用方无法区分显式目标场景。
    if not _action_can_reuse_observed_window(legacy_arguments):  # 新增代码+MultiTargetRefGate：只对键鼠写动作做目标歧义判断；如果没有这一行，launch_app 等非目标动作会被误挡。
        return {}  # 新增代码+MultiTargetRefGate：非窗口写动作不处理；如果没有这一行，普通工具会进入错误门禁。
    target_registry = getattr(controller, "target_registry", None)  # 新增代码+MultiTargetRefGate：读取 controller 目标注册表；如果没有这一行，函数不知道当前有几个 active target。
    resolve_implicit_target = getattr(target_registry, "resolve_implicit_target", None)  # 新增代码+MultiTargetRefGate：读取 registry 的隐式解析方法；如果没有这一行，多目标合同无法复用。
    if not callable(resolve_implicit_target):  # 新增代码+MultiTargetRefGate：旧 controller 没有该能力时不处理；如果没有这一行，调用 None 会崩溃。
        return {}  # 新增代码+MultiTargetRefGate：返回空并交给旧底层门禁；如果没有这一行，兼容路径会中断。
    try:  # 新增代码+MultiTargetRefGate：保护 registry 解析过程；如果没有这一行，异常会中断工具调用。
        resolution = resolve_implicit_target()  # 新增代码+MultiTargetRefGate：执行现有隐式目标解析；如果没有这一行，函数没有事实来源。
    except Exception:  # 新增代码+MultiTargetRefGate：捕获 registry 异常；如果没有这一行，坏状态会抛出到模型层。
        return {}  # 新增代码+MultiTargetRefGate：异常时保持旧路径；如果没有这一行，函数没有安全失败出口。
    return dict(resolution) if isinstance(resolution, dict) else {}  # 新增代码+MultiTargetRefGate：返回解析结果副本；如果没有这一行，调用方可能污染 registry 输出。
# 新增代码+MultiTargetRefGate：函数段结束，_resolve_implicit_target_for_action 到此结束；如果没有这个边界说明，用户不容易看出隐式解析范围。


def _target_window_from_resolution(resolution: dict[str, Any]) -> dict[str, Any]:  # 新增代码+TargetRefAutoInject：函数段开始，从 registry 解析结果里取后端可用窗口；如果没有这段函数，多处代码会重复拆 target/window/raw_window。
    target = resolution.get("target") if isinstance(resolution.get("target"), dict) else {}  # 新增代码+TargetRefAutoInject：读取解析结果里的 target 字典；如果没有这一行，后续无法兼容 registry 返回结构。
    window = target.get("window") if isinstance(target.get("window"), dict) else target.get("raw_window")  # 新增代码+TargetRefAutoInject：优先读取公开清洗窗口并兼容 raw_window；如果没有这一行，动作层可能拿不到真实 window。
    return dict(window) if isinstance(window, dict) else {}  # 新增代码+TargetRefAutoInject：返回窗口副本或空字典；如果没有这一行，调用方可能污染 registry 原始状态。
# 新增代码+TargetRefAutoInject：函数段结束，_target_window_from_resolution 到此结束；如果没有这个边界说明，用户不容易看出解析范围。


def _resolve_explicit_target_for_action(controller: Any, legacy_arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ExplicitTargetRefResourceFallback：函数段开始，按显式 target_ref 从 registry 解析目标窗口；如果没有这段函数，多目标场景会把明确目标误判成歧义。
    target_ref = str(legacy_arguments.get("target_ref", "") or "").strip()  # 新增代码+ExplicitTargetRefResourceFallback：读取旧动作参数里的显式 target_ref；如果没有这一行，函数不知道要解析哪个窗口。
    if not target_ref:  # 新增代码+ExplicitTargetRefResourceFallback：检查是否真的有显式 ref；如果没有这一行，空 ref 会进入 registry 查询。
        return {}  # 新增代码+ExplicitTargetRefResourceFallback：没有显式 ref 时返回空结果；如果没有这一行，调用方无法区分无需处理和解析失败。
    if not _action_can_reuse_observed_window(legacy_arguments):  # 新增代码+ExplicitTargetRefResourceFallback：只处理键鼠写动作；如果没有这一行，launch_app 等非窗口动作会被错误解析成窗口动作。
        return {}  # 新增代码+ExplicitTargetRefResourceFallback：非窗口写动作不解析；如果没有这一行，普通启动应用可能被不相关 target_ref 干扰。
    target_registry = getattr(controller, "target_registry", None)  # 新增代码+ExplicitTargetRefResourceFallback：读取 controller 目标注册表；如果没有这一行，adapter 无法按 ref 找回窗口。
    resolve_target_ref = getattr(target_registry, "resolve_target_ref", None)  # 新增代码+ExplicitTargetRefResourceFallback：读取 registry 显式 ref 解析方法；如果没有这一行，旧 controller 兼容路径会崩溃。
    if not callable(resolve_target_ref):  # 新增代码+ExplicitTargetRefResourceFallback：确认后端支持 ref 解析；如果没有这一行，None 会被当函数调用。
        return {}  # 新增代码+ExplicitTargetRefResourceFallback：后端不支持时返回空交给旧路径；如果没有这一行，兼容环境无法运行。
    try:  # 新增代码+ExplicitTargetRefResourceFallback：保护 registry 解析过程；如果没有这一行，坏 ref 状态会抛出到模型层。
        resolution = resolve_target_ref(target_ref)  # 新增代码+ExplicitTargetRefResourceFallback：执行显式 target_ref 解析；如果没有这一行，target_ref 仍只是字符串。
    except Exception:  # 新增代码+ExplicitTargetRefResourceFallback：捕获 registry 异常；如果没有这一行，单次坏状态会中断整个 agent。
        return {}  # 新增代码+ExplicitTargetRefResourceFallback：异常时保持旧路径；如果没有这一行，函数没有安全失败出口。
    return dict(resolution) if isinstance(resolution, dict) else {}  # 新增代码+ExplicitTargetRefResourceFallback：返回解析结果副本；如果没有这一行，调用方可能污染 registry 输出。
# 新增代码+ExplicitTargetRefResourceFallback：函数段结束，_resolve_explicit_target_for_action 到此结束；如果没有这个边界说明，用户不容易看出显式解析范围。


def _inject_explicit_target_ref_window(controller: Any, legacy_arguments: dict[str, Any]) -> bool:  # 新增代码+ExplicitTargetRefResourceFallback：函数段开始，把显式 target_ref 对应窗口注入 action 参数；如果没有这段函数，资源门禁会在缺 window 时失效。
    resolution = _resolve_explicit_target_for_action(controller, legacy_arguments)  # 新增代码+ExplicitTargetRefResourceFallback：读取显式 ref 的 registry 解析结果；如果没有这一行，注入逻辑没有事实来源。
    if not isinstance(resolution, dict) or not bool(resolution.get("ok")):  # 新增代码+ExplicitTargetRefResourceFallback：只有解析成功才注入窗口；如果没有这一行，坏 ref 可能被误当成有效目标。
        return False  # 新增代码+ExplicitTargetRefResourceFallback：解析失败时保持旧路径；如果没有这一行，调用方会误记录成功注入。
    target_ref = str(resolution.get("target_ref", "") or legacy_arguments.get("target_ref", "") or "").strip()  # 新增代码+ExplicitTargetRefResourceFallback：读取 registry 确认后的 target_ref；如果没有这一行，窗口和 ref 可能对不上。
    target_window = _target_window_from_resolution(resolution)  # 新增代码+ExplicitTargetRefResourceFallback：取出 target_ref 绑定的一对一窗口；如果没有这一行，资源门禁仍没有 window。
    if not target_ref or not target_window:  # 新增代码+ExplicitTargetRefResourceFallback：确认 ref 和窗口事实完整；如果没有这一行，半截状态会进入动作链。
        return False  # 新增代码+ExplicitTargetRefResourceFallback：证据不完整时不注入；如果没有这一行，安全判断会变成猜测。
    current_window = legacy_arguments.get("window") if isinstance(legacy_arguments.get("window"), dict) else {}  # 新增代码+ExplicitTargetRefResourceFallback：读取动作参数已有窗口；如果没有这一行，无法判断是否需要替换或补齐。
    current_identity_values = _window_identity_values(current_window) if current_window else set()  # 新增代码+ExplicitTargetRefResourceFallback：提取已有窗口身份值；如果没有这一行，缺身份窗口可能被错误当成冲突。
    if current_window and current_identity_values and not _windows_share_identity(current_window, target_window):  # 新增代码+ExplicitTargetRefResourceFallback：已有窗口若带身份则必须和 registry 目标一致；如果没有这一行，target_ref 可能被注入到错误窗口。
        return False  # 新增代码+ExplicitTargetRefResourceFallback：窗口身份冲突时交给底层拒绝；如果没有这一行，复杂多窗口任务可能误操作别的窗口。
    injected_window = dict(current_window if current_identity_values else target_window)  # 新增代码+ExplicitTargetRefResourceFallback：优先保留同身份窗口，否则使用 registry 可信窗口；如果没有这一行，动作窗口无法稳定确定。
    target = resolution.get("target") if isinstance(resolution.get("target"), dict) else {}  # 新增代码+ExplicitTargetRefResourceFallback：读取完整 target 记录；如果没有这一行，拿不到租约来源。
    lease = target.get("lease") if isinstance(target.get("lease"), dict) else {}  # 新增代码+ExplicitTargetRefResourceFallback：读取 target 租约；如果没有这一行，资源门禁不知道这是 agent-owned 窗口。
    if lease and not isinstance(injected_window.get("target_lease"), dict):  # 新增代码+ExplicitTargetRefResourceFallback：只在窗口缺租约时补充；如果没有这一行，已有更精确租约会被覆盖。
        injected_window["target_lease"] = dict(lease)  # 新增代码+ExplicitTargetRefResourceFallback：把租约写入动作窗口；如果没有这一行，恢复旧资源的新窗口不会触发 action 级兜底。
    injected_window["target_ref"] = target_ref  # 新增代码+ExplicitTargetRefResourceFallback：把稳定 ref 写入窗口；如果没有这一行，底层日志看不到窗口绑定关系。
    legacy_arguments["window"] = injected_window  # 新增代码+ExplicitTargetRefResourceFallback：把解析后的窗口写回旧动作参数；如果没有这一行，资源门禁和底层执行仍缺目标窗口。
    legacy_arguments["target_ref"] = target_ref  # 新增代码+ExplicitTargetRefResourceFallback：把规范化 target_ref 写回顶层参数；如果没有这一行，controller 后续 target_ref 校验仍可能失败。
    return True  # 新增代码+ExplicitTargetRefResourceFallback：返回已注入；如果没有这一行，调用方无法记录 trace。
# 新增代码+ExplicitTargetRefResourceFallback：函数段结束，_inject_explicit_target_ref_window 到此结束；如果没有这个边界说明，用户不容易看出显式目标注入范围。


def _inject_single_active_target_ref(controller: Any, legacy_arguments: dict[str, Any]) -> bool:  # 新增代码+TargetRefAutoInject：函数段开始，在安全单目标场景为动作补 target_ref；如果没有这段函数，模型漏传 target_ref 时真实键鼠动作会被底层反复拒绝。
    if legacy_arguments.get("target_ref"):  # 新增代码+TargetRefAutoInject：已有显式 target_ref 时不再改写；如果没有这一行，模型明确选择的目标可能被覆盖。
        return False  # 新增代码+TargetRefAutoInject：返回未注入表示保持原参数；如果没有这一行，调用方无法记录是否自动补齐。
    if not _action_can_reuse_observed_window(legacy_arguments):  # 新增代码+TargetRefAutoInject：只处理需要窗口绑定的键鼠写动作；如果没有这一行，launch_app 等非窗口动作可能被错误塞 target_ref。
        return False  # 新增代码+TargetRefAutoInject：非复用动作直接放行；如果没有这一行，函数会继续读取无关 registry。
    resolution = _resolve_implicit_target_for_action(controller, legacy_arguments)  # 修改代码+MultiTargetRefGate：复用统一隐式解析 helper；如果没有这一行，单目标注入和多目标拒绝会出现分叉。
    if not isinstance(resolution, dict) or not bool(resolution.get("ok")):  # 新增代码+TargetRefAutoInject：只有单目标解析成功才允许注入；如果没有这一行，多目标或无目标也会被隐式使用。
        return False  # 新增代码+TargetRefAutoInject：解析失败时不注入；如果没有这一行，多窗口任务会误打 active 窗口。
    target_ref = str(resolution.get("target_ref", "") or "").strip()  # 新增代码+TargetRefAutoInject：读取 registry 返回的稳定 target_ref；如果没有这一行，动作仍缺少目标 ID。
    target_window = _target_window_from_resolution(resolution)  # 新增代码+TargetRefAutoInject：读取 target_ref 对应窗口；如果没有这一行，无法校验和补全 window。
    if not target_ref or not target_window:  # 新增代码+TargetRefAutoInject：target_ref 和窗口都必须存在；如果没有这一行，半截状态可能进入真实动作。
        return False  # 新增代码+TargetRefAutoInject：证据不完整时不注入；如果没有这一行，安全边界会降低。
    current_window = legacy_arguments.get("window") if isinstance(legacy_arguments.get("window"), dict) else {}  # 新增代码+TargetRefAutoInject：读取当前动作已有窗口；如果没有这一行，无法判断是否需要补 window。
    if current_window and not _windows_share_identity(current_window, target_window):  # 新增代码+TargetRefAutoInject：已有窗口必须和 registry 目标同一对象；如果没有这一行，可能把 target_ref 注入到错误窗口。
        return False  # 新增代码+TargetRefAutoInject：窗口不一致时保持旧路径交给底层拒绝；如果没有这一行，错误窗口会被放行。
    injected_window = dict(current_window or target_window)  # 新增代码+TargetRefAutoInject：选择已有窗口或 registry 窗口作为动作窗口；如果没有这一行，后续补字段没有对象。
    target = resolution.get("target") if isinstance(resolution.get("target"), dict) else {}  # 新增代码+ResourceFreshnessActionFallback：读取 registry 里的完整 target 记录；如果没有这一行，动作窗口拿不到 launch 租约来源。
    lease = target.get("lease") if isinstance(target.get("lease"), dict) else {}  # 新增代码+ResourceFreshnessActionFallback：读取 target 的租约摘要；如果没有这一行，action 兜底门禁不知道窗口是否由 agent 新启动。
    if lease and not isinstance(injected_window.get("target_lease"), dict):  # 新增代码+ResourceFreshnessActionFallback：只在窗口缺租约时补充；如果没有这一行，已有更精确租约可能被覆盖。
        injected_window["target_lease"] = dict(lease)  # 新增代码+ResourceFreshnessActionFallback：把租约附加到动作窗口；如果没有这一行，资源恢复判断缺少 agent-owned 事实。
    injected_window["target_ref"] = target_ref  # 新增代码+TargetRefAutoInject：把 target_ref 放进窗口副本便于底层和日志使用；如果没有这一行，窗口字段仍缺目标 ID。
    legacy_arguments["window"] = injected_window  # 新增代码+TargetRefAutoInject：写回动作窗口；如果没有这一行，底层仍可能只看到无 ref 的 raw window。
    legacy_arguments["target_ref"] = target_ref  # 新增代码+TargetRefAutoInject：写回顶层 target_ref；如果没有这一行，controller 的 target_ref 门禁仍会拒绝。
    return True  # 新增代码+TargetRefAutoInject：返回已注入；如果没有这一行，调用方无法记录自动修复证据。
# 新增代码+TargetRefAutoInject：函数段结束，_inject_single_active_target_ref 到此结束；如果没有这个边界说明，用户不容易看出自动注入边界。


RESOURCE_HINT_PATTERN = re.compile(r"(?i)([a-z0-9_\-.()\u4e00-\u9fff]+[.](?:txt|md|docx?|xlsx?|pptx?|csv|json|html?|pdf))")  # 新增代码+ResourceFreshnessAdapter：定义从用户 reason 中提取文件名的通用正则；如果没有这一行，adapter 无法从“保存到桌面 1.txt”识别目标资源。
NEW_RESOURCE_INTENT_TOKENS = ("保存到", "保存为", "另存", "新文件", "新建", "桌面", "save as", "save to", "new file", "new document")  # 新增代码+ResourceFreshnessAdapter：声明需要新资源/保存目标的常见提示词；如果没有这一行，普通观察会被过度资源门禁。


def _extract_requested_resource_hint(arguments: dict[str, Any]) -> str:  # 新增代码+ResourceFreshnessAdapter：函数段开始，从工具参数中提取用户目标资源名；如果没有这段函数，资源新鲜度只能依赖模型显式传新字段。
    explicit_hint = str(arguments.get("requested_resource_hint", "") or arguments.get("resource_hint", "") or "").strip()  # 新增代码+ResourceFreshnessAdapter：优先读取结构化资源 hint；如果没有这一行，未来 schema 增加字段后不能直接使用。
    if explicit_hint:  # 新增代码+ResourceFreshnessAdapter：如果模型已经明确给出资源名就直接使用；如果没有这一行，明确字段会被 reason 正则覆盖。
        return explicit_hint  # 新增代码+ResourceFreshnessAdapter：返回显式资源 hint；如果没有这一行，函数无法利用结构化输入。
    reason = str(arguments.get("reason", "") or "")  # 新增代码+ResourceFreshnessAdapter：读取工具 reason 里的自然语言任务片段；如果没有这一行，用户真实 prompt 里的 1.txt 无法被识别。
    matches = RESOURCE_HINT_PATTERN.findall(reason)  # 新增代码+ResourceFreshnessAdapter：从 reason 中提取文件名候选；如果没有这一行，保存目标无法自动进入资源门禁。
    return str(matches[-1]).strip() if matches else ""  # 新增代码+ResourceFreshnessAdapter：返回最后一个文件名候选；如果没有这一行，函数缺少稳定输出。
# 新增代码+ResourceFreshnessAdapter：函数段结束，_extract_requested_resource_hint 到此结束；如果没有这个边界说明，用户不容易看出资源 hint 来源。


def _arguments_request_new_resource(arguments: dict[str, Any], resource_hint: str) -> bool:  # 新增代码+ResourceFreshnessAdapter：函数段开始，判断当前观察是否要求新资源；如果没有这段函数，旧文档门禁会在普通查看场景误触发。
    if bool(arguments.get("requires_new_resource")):  # 新增代码+ResourceFreshnessAdapter：结构化参数明确要求新资源时直接启用；如果没有这一行，未来工具 schema 不能精确控制。
        return True  # 新增代码+ResourceFreshnessAdapter：返回需要新资源；如果没有这一行，显式请求会被忽略。
    reason = str(arguments.get("reason", "") or "").lower()  # 新增代码+ResourceFreshnessAdapter：读取并小写自然语言 reason；如果没有这一行，中文/英文 token 无法统一匹配。
    if not resource_hint:  # 新增代码+ResourceFreshnessAdapter：没有资源名时不把普通文档标题当旧资源风险；如果没有这一行，多数应用观察会被误挡。
        return False  # 新增代码+ResourceFreshnessAdapter：返回不要求新资源；如果没有这一行，函数缺少保守出口。
    return any(token in reason for token in NEW_RESOURCE_INTENT_TOKENS)  # 新增代码+ResourceFreshnessAdapter：命中新建/保存语义才启用新鲜度门禁；如果没有这一行，资源判断会对复杂任务过度保守。
# 新增代码+ResourceFreshnessAdapter：函数段结束，_arguments_request_new_resource 到此结束；如果没有这个边界说明，用户不容易看出新资源意图范围。


def _arguments_allow_existing_resource(arguments: dict[str, Any]) -> bool:  # 新增代码+ResourceFreshnessAdapter：函数段开始，判断用户是否明确授权使用已有资源；如果没有这段函数，微信/单实例或用户授权旧窗口路径无法恢复。
    return any(bool(arguments.get(field_name)) for field_name in ("allow_existing_resource", "user_authorized_existing_resource", "user_authorized_window", "use_existing_window", "reuse_existing_window"))  # 新增代码+ResourceFreshnessAdapter：识别常见授权字段；如果没有这一行，明确授权仍会被资源门禁挡住。
# 新增代码+ResourceFreshnessAdapter：函数段结束，_arguments_allow_existing_resource 到此结束；如果没有这个边界说明，用户不容易看出授权字段范围。


def _window_has_agent_owned_launch_context(window: dict[str, Any]) -> bool:  # 新增代码+ResourceFreshnessActionFallback：函数段开始，判断窗口是否来自 agent 新启动/绑定链路；如果没有这段函数，action 兜底会误把普通用户窗口当成新资源要求。
    lease = window.get("target_lease") if isinstance(window.get("target_lease"), dict) else {}  # 新增代码+ResourceFreshnessActionFallback：读取动作窗口携带的租约；如果没有这一行，无法使用 registry 的 agent-owned 证据。
    lease_origin = str(lease.get("origin", "") or "").strip().lower()  # 新增代码+ResourceFreshnessActionFallback：规范化租约来源；如果没有这一行，大小写或空值会影响判断。
    if lease_origin in {"agent_owned_launch", "agent_owned_proxy_window", "fresh_agent_owned_window"}:  # 新增代码+ResourceFreshnessActionFallback：命中 agent 自己启动/绑定的来源；如果没有这一行，恢复旧资源的新进程不会进入兜底门禁。
        return True  # 新增代码+ResourceFreshnessActionFallback：返回具备 agent-owned 上下文；如果没有这一行，调用方无法启用资源兜底。
    freshness = window.get("fresh_target_freshness") if isinstance(window.get("fresh_target_freshness"), dict) else {}  # 新增代码+ResourceFreshnessActionFallback：读取 FreshTarget 附带的新鲜窗口报告；如果没有这一行，只有 freshness 没有 lease 的窗口会漏判。
    freshness_class = str(freshness.get("fresh_target_class", "") or "").strip().lower()  # 新增代码+ResourceFreshnessActionFallback：规范化 FreshTarget 分类；如果没有这一行，分类值不能稳定比较。
    if freshness_class in {"fresh_agent_owned_window", "agent_owned_proxy_window"}:  # 新增代码+ResourceFreshnessActionFallback：确认 FreshTarget 认为这是 agent 拥有的新目标；如果没有这一行，proxy PID 场景缺少兜底。
        return True  # 新增代码+ResourceFreshnessActionFallback：返回具备 agent-owned 上下文；如果没有这一行，调用方无法阻断恢复旧资源。
    return bool(window.get("agent_owned_proxy_window"))  # 新增代码+ResourceFreshnessActionFallback：兼容窗口事实里的布尔代理绑定字段；如果没有这一行，旧字段命名的证据会被忽略。
# 新增代码+ResourceFreshnessActionFallback：函数段结束，_window_has_agent_owned_launch_context 到此结束；如果没有这个边界说明，用户不容易看出 agent-owned 判断范围。


def _window_title_contains_resource_filename(window: dict[str, Any]) -> bool:  # 新增代码+ResourceFreshnessActionFallback：函数段开始，判断窗口标题是否像已打开的具体文件资源；如果没有这段函数，action 兜底只能依赖模型 reason，真实验收会漏掉恢复旧文档。
    title = str(window.get("title_preview") or window.get("title") or window.get("window_title") or "")  # 新增代码+ResourceFreshnessActionFallback：读取常见标题字段；如果没有这一行，Notepad/Word/浏览器标题字段差异会漏判。
    return bool(RESOURCE_HINT_PATTERN.search(title))  # 新增代码+ResourceFreshnessActionFallback：用通用文件名正则识别 .txt/.md/.docx 等资源；如果没有这一行，旧文档标题不会触发新资源门禁。
# 新增代码+ResourceFreshnessActionFallback：函数段结束，_window_title_contains_resource_filename 到此结束；如果没有这个边界说明，用户不容易看出标题文件名判断范围。


def _action_requires_new_resource_from_window(window: dict[str, Any], arguments: dict[str, Any], resource_hint: str) -> bool:  # 新增代码+ResourceFreshnessActionFallback：函数段开始，在 action 入口根据窗口事实补齐新资源需求；如果没有这段函数，observe 没写状态时旧文档会继续被按键写入。
    if _arguments_request_new_resource(arguments, resource_hint):  # 新增代码+ResourceFreshnessActionFallback：保留已有结构化/自然语言新资源判断；如果没有这一行，显式 1.txt/save as 语义会被忽略。
        return True  # 新增代码+ResourceFreshnessActionFallback：返回需要新资源；如果没有这一行，调用方无法启用硬门禁。
    if _arguments_allow_existing_resource(arguments):  # 新增代码+ResourceFreshnessActionFallback：用户明确授权已有窗口时不兜底阻断；如果没有这一行，微信/单实例或授权编辑旧文件会无法继续。
        return False  # 新增代码+ResourceFreshnessActionFallback：返回不强制新资源；如果没有这一行，授权字段不会生效。
    if not _window_has_agent_owned_launch_context(window):  # 新增代码+ResourceFreshnessActionFallback：只有 agent 新启动/绑定的目标才启用标题兜底；如果没有这一行，普通用户窗口会被过度保守拦截。
        return False  # 新增代码+ResourceFreshnessActionFallback：返回不强制新资源；如果没有这一行，未知窗口会误入文档恢复门禁。
    return _window_title_contains_resource_filename(window)  # 新增代码+ResourceFreshnessActionFallback：标题里出现具体文件名时视为恢复旧资源风险；如果没有这一行，新进程恢复旧 .md/.txt 文档会再次穿透。
# 新增代码+ResourceFreshnessActionFallback：函数段结束，_action_requires_new_resource_from_window 到此结束；如果没有这个边界说明，用户不容易看出 action 兜底策略范围。


def _build_resource_freshness_for_action_arguments(window: dict[str, Any], arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ResourceFreshnessActionFallback：函数段开始，为 action 前置门禁生成资源新鲜度报告；如果没有这段函数，action 只能依赖 observe 的上一次状态。
    resource_hint = _extract_requested_resource_hint(arguments)  # 新增代码+ResourceFreshnessActionFallback：提取动作参数里的目标资源名；如果没有这一行，显式 resource_hint 或 reason 文件名无法进入判断。
    requires_new_resource = _action_requires_new_resource_from_window(window, arguments, resource_hint)  # 新增代码+ResourceFreshnessActionFallback：结合窗口事实判断是否需要新空白/目标资源；如果没有这一行，旧资源标题无法触发兜底。
    allow_existing_resource = _arguments_allow_existing_resource(arguments)  # 新增代码+ResourceFreshnessActionFallback：读取用户是否授权已有资源；如果没有这一行，合法授权无法越过兜底。
    return build_resource_freshness(window, requested_resource_hint=resource_hint, requires_new_resource=requires_new_resource, allow_existing_resource=allow_existing_resource)  # 新增代码+ResourceFreshnessActionFallback：复用统一资源新鲜度 helper；如果没有这一行，action 和 observe 的阻断语义会分叉。
# 新增代码+ResourceFreshnessActionFallback：函数段结束，_build_resource_freshness_for_action_arguments 到此结束；如果没有这个边界说明，用户不容易看出 action 报告构造范围。


def _build_resource_freshness_for_arguments(window: dict[str, Any], arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ResourceFreshnessAdapter：函数段开始，用窗口和工具参数生成资源新鲜度报告；如果没有这段函数，observe/action 会各写一套判断。
    resource_hint = _extract_requested_resource_hint(arguments)  # 新增代码+ResourceFreshnessAdapter：提取目标资源名；如果没有这一行，build_resource_freshness 不知道用户要哪个文件。
    requires_new_resource = _arguments_request_new_resource(arguments, resource_hint)  # 新增代码+ResourceFreshnessAdapter：判断是否启用新资源门禁；如果没有这一行，所有文档标题都会被误用成硬门禁。
    allow_existing_resource = _arguments_allow_existing_resource(arguments)  # 新增代码+ResourceFreshnessAdapter：读取用户是否授权已有资源；如果没有这一行，合法显式授权无法通过。
    return build_resource_freshness(window, requested_resource_hint=resource_hint, requires_new_resource=requires_new_resource, allow_existing_resource=allow_existing_resource)  # 新增代码+ResourceFreshnessAdapter：调用通用资源新鲜度 helper；如果没有这一行，adapter 无法得到结构化允许/阻断报告。
# 新增代码+ResourceFreshnessAdapter：函数段结束，_build_resource_freshness_for_arguments 到此结束；如果没有这个边界说明，用户不容易看出报告构造范围。


def _resource_user_action_legacy_text(report: dict[str, Any]) -> str:  # 新增代码+ResourceFreshnessAdapter：函数段开始，把资源阻断报告转成 actionability 可解析文本；如果没有这段函数，收敛层无法从 JSON 工具结果里读到 marker。
    lines = [  # 新增代码+ResourceFreshnessAdapter：准备 key=value 协议行；如果没有这一行，marker 文本没有容器。
        RESOURCE_USER_ACTION_REQUIRED_MARKER,  # 新增代码+ResourceFreshnessAdapter：写入资源阻断 marker；如果没有这一行，收敛器不会识别旧资源用户动作要求。
        "block_class=user_action_required",  # 新增代码+ResourceFreshnessAdapter：复用用户动作阻断分类；如果没有这一行，最终回答收束不会触发。
        f"block_reason={report.get('decision', 'resource_user_action_required')}",  # 新增代码+ResourceFreshnessAdapter：写入稳定阻断原因；如果没有这一行，用户看不到为什么停止。
        f"resource_freshness_decision={report.get('decision', '')}",  # 新增代码+ResourceFreshnessAdapter：写入资源新鲜度决策；如果没有这一行，日志无法区分 FreshTarget 和 ResourceFreshness。
        f"target_app={report.get('app_id') or report.get('process_name') or '目标软件'}",  # 新增代码+ResourceFreshnessAdapter：写入目标应用；如果没有这一行，提示里缺少具体软件名。
        "retry_launch_allowed=false",  # 新增代码+ResourceFreshnessAdapter：禁止模型通过反复启动绕过旧资源风险；如果没有这一行，open_application 循环会复发。
        "next_required_response=ask_user_to_create_blank_or_authorize_existing_resource",  # 新增代码+ResourceFreshnessAdapter：告诉模型应向用户解释并等待授权/新空白；如果没有这一行，模型不知道下一步是最终回答。
        "low_level_event_count=0",  # 新增代码+ResourceFreshnessAdapter：声明阻断没有触发底层事件；如果没有这一行，真实验收无法证明没有污染桌面。
    ]  # 新增代码+ResourceFreshnessAdapter：协议行列表结束；如果没有这一行，Python 语法不完整。
    return "\n".join(lines)  # 新增代码+ResourceFreshnessAdapter：返回多行 marker 文本；如果没有这一行，调用方拿不到可解析文本。
# 新增代码+ResourceFreshnessAdapter：函数段结束，_resource_user_action_legacy_text 到此结束；如果没有这个边界说明，用户不容易看出 marker 文本范围。


def _resource_user_action_result(tool_name: str, report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ResourceFreshnessAdapter：函数段开始，构造资源旧内容阻断工具结果；如果没有这段函数，每个动作分支会重复拼接错误结构。
    legacy_text = _resource_user_action_legacy_text(report)  # 新增代码+ResourceFreshnessAdapter：生成收敛层可解析文本；如果没有这一行，结果缺少 marker。
    payload = {"reason": "当前窗口恢复了已有资源，Computer Use 不会默认写入旧文档。", "resource_freshness": dict(report), "legacy_text": legacy_text}  # 新增代码+ResourceFreshnessAdapter：构造模型可读 payload；如果没有这一行，工具结果没有结构化阻断证据。
    return _json_result(tool_name, False, payload, error_class="desktop_resource_user_action_required")  # 新增代码+ResourceFreshnessAdapter：返回统一失败结果；如果没有这一行，调用方无法识别动作已被安全拒绝。
# 新增代码+ResourceFreshnessAdapter：函数段结束，_resource_user_action_result 到此结束；如果没有这个边界说明，用户不容易看出结果构造范围。


def _multiple_target_ref_required_result(tool_name: str, resolution: dict[str, Any]) -> dict[str, Any]:  # 新增代码+MultiTargetRefGate：函数段开始，构造多目标缺 target_ref 的零事件拒绝结果；如果没有这段函数，多窗口歧义会继续穿到底层执行。
    payload = {  # 新增代码+MultiTargetRefGate：准备结构化拒绝 payload；如果没有这一行，模型拿不到可执行纠偏信息。
        "decision": "multiple_active_targets_require_target_ref",  # 新增代码+MultiTargetRefGate：写入稳定决策码；如果没有这一行，测试和模型不知道拒绝原因。
        "target_count": int(resolution.get("target_count", 0) or 0),  # 新增代码+MultiTargetRefGate：写入 active target 数量；如果没有这一行，用户不知道为什么必须显式选择。
        "available_target_refs": list(resolution.get("available_target_refs", []) or []),  # 新增代码+MultiTargetRefGate：写入可选 target_ref 列表；如果没有这一行，模型不知道可选窗口 ID。
        "low_level_event_count": 0,  # 新增代码+MultiTargetRefGate：声明拒绝发生在底层事件之前；如果没有这一行，真实验收无法证明没有误操作。
        "reason": "当前会话存在多个 Computer Use 目标窗口，必须显式传入 target_ref 才能继续。",  # 新增代码+MultiTargetRefGate：写入用户可读原因；如果没有这一行，终端输出不够清楚。
    }  # 新增代码+MultiTargetRefGate：payload 字典结束；如果没有这一行，Python 语法不完整。
    return _json_result(tool_name, False, payload, error_class="multiple_active_targets_require_target_ref")  # 新增代码+MultiTargetRefGate：返回统一拒绝结果；如果没有这一行，调用方无法短路真实 action。
# 新增代码+MultiTargetRefGate：函数段结束，_multiple_target_ref_required_result 到此结束；如果没有这个边界说明，用户不容易看出多目标拒绝结果范围。


def _annotate_wrapped_result_with_resource_freshness(wrapped: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ResourceFreshnessAdapter：函数段开始，把资源新鲜度写回 observe 结果；如果没有这段函数，模型看不到旧资源 marker，会继续尝试键鼠动作。
    payload = wrapped.get("payload", {}) if isinstance(wrapped.get("payload", {}), dict) else {}  # 新增代码+ResourceFreshnessAdapter：读取包装 payload；如果没有这一行，后续写入可能对非 dict 报错。
    payload["resource_freshness"] = dict(report)  # 新增代码+ResourceFreshnessAdapter：保存结构化资源报告；如果没有这一行，调试时无法看到资源判断依据。
    if not bool(report.get("allowed", True)):  # 新增代码+ResourceFreshnessAdapter：只有阻断时才追加 marker 和改失败状态；如果没有这一行，正常 observe 会输出多余阻断文本。
        legacy_text = str(payload.get("legacy_text", ""))  # 新增代码+ResourceFreshnessAdapter：读取已有旧 observe 文本；如果没有这一行，追加 marker 会丢失原观察摘要。
        resource_text = _resource_user_action_legacy_text(report)  # 新增代码+ResourceFreshnessAdapter：生成资源阻断 marker 文本；如果没有这一行，payload 只有结构化报告没有收敛协议。
        payload["legacy_text"] = legacy_text + ("\n" if legacy_text else "") + resource_text  # 新增代码+ResourceFreshnessAdapter：把 marker 追加到模型可见文本；如果没有这一行，actionability_state 解析不到资源阻断。
        wrapped["ok"] = False  # 新增代码+ResourceFreshnessAdapter：把 observe 结果标记为安全阻断；如果没有这一行，模型可能误以为可以继续动作。
        wrapped["error_class"] = "desktop_resource_user_action_required"  # 新增代码+ResourceFreshnessAdapter：写入稳定错误分类；如果没有这一行，调试日志无法快速定位资源旧内容门禁。
    wrapped["payload"] = payload  # 新增代码+ResourceFreshnessAdapter：写回 payload；如果没有这一行，局部修改不会返回调用方。
    wrapped["text"] = json.dumps(wrapped, ensure_ascii=False, sort_keys=True)  # 新增代码+ResourceFreshnessAdapter：重新生成最终 JSON 文本；如果没有这一行，返回 text 仍是旧内容。
    return wrapped  # 新增代码+ResourceFreshnessAdapter：返回更新后的结果；如果没有这一行，调用方拿不到注释后的 observe。
# 新增代码+ResourceFreshnessAdapter：函数段结束，_annotate_wrapped_result_with_resource_freshness 到此结束；如果没有这个边界说明，用户不容易看出 observe 注入范围。


def _zoom_safe_int(arguments: dict[str, Any], name: str, default: int = 0) -> int:  # 新增代码+ClaudeCodeZoom: 函数段开始，安全读取 zoom 坐标和尺寸整数；如果没有这段函数，坏参数会让裁剪逻辑抛异常中断工具调用。
    try:  # 新增代码+ClaudeCodeZoom: 捕获无法转整数的输入；如果没有这一行，字符串空值或 None 会直接抛出 ValueError/TypeError。
        return int(arguments.get(name, default) or default)  # 新增代码+ClaudeCodeZoom: 返回指定字段的整数值；如果没有这一行，裁剪坐标没有稳定数值来源。
    except (TypeError, ValueError):  # 新增代码+ClaudeCodeZoom: 处理非数字输入；如果没有这一行，异常会冒泡到 agent 主循环。
        return int(default)  # 新增代码+ClaudeCodeZoom: 返回兜底整数；如果没有这一行，函数没有稳定失败输出。
# 新增代码+ClaudeCodeZoom: 函数段结束，_zoom_safe_int 到此结束；如果没有这个边界说明，用户不容易看出参数兜底范围。


def _zoom_annotate_wrapped_result(wrapped: dict[str, Any], image_results: list[dict[str, Any]], failure_reason: str = "") -> dict[str, Any]:  # 新增代码+ClaudeCodeZoom: 函数段开始，把 zoom 裁剪结果写回 adapter 包装结果；如果没有这段函数，payload 和模型可解析文本会各写各的容易漂移。
    payload = wrapped.get("payload", {}) if isinstance(wrapped.get("payload", {}), dict) else {}  # 新增代码+ClaudeCodeZoom: 安全读取包装 payload；如果没有这一行，异常包装结构会触发属性错误。
    payload["zoom_image_results"] = [dict(item) for item in image_results]  # 新增代码+ClaudeCodeZoom: 保存 zoom 专属图片块；如果没有这一行，调用方无法区分局部放大图和原始全图。
    payload["zoom_image_result_count"] = len(image_results)  # 新增代码+ClaudeCodeZoom: 保存 zoom 图片数量；如果没有这一行，测试和终端日志无法快速判断是否产出裁剪图。
    payload["zoom_failure_reason"] = str(failure_reason or "")  # 新增代码+ClaudeCodeZoom: 记录无法裁剪的原因；如果没有这一行，真实环境缺图或缺坐标时只能猜。
    if image_results:  # 新增代码+ClaudeCodeZoom: 只有成功生成裁剪图时才覆盖模型可见图片区；如果没有这一行，失败也会输出空图片区噪音。
        payload["image_results"] = [dict(item) for item in image_results]  # 新增代码+ClaudeCodeZoom: 把局部图放到浅层 image_results；如果没有这一行，active artifact 收集器可能优先看到旧全图。
        payload["image_result_count"] = len(image_results)  # 新增代码+ClaudeCodeZoom: 同步浅层图片数量；如果没有这一行，观察结果数量仍可能显示原始全图数量。
        try:  # 新增代码+ClaudeCodeZoom: 复用现有图片区文本格式化函数；如果没有这一行，导入或格式化失败会中断 zoom 工具。
            from .evidence import format_image_result_lines  # 新增代码+ClaudeCodeZoom: 导入模型可解析图片区格式器；如果没有这一行，zoom 图无法进入后续多模态回灌解析器。
            image_result_lines = format_image_result_lines(image_results)  # 新增代码+ClaudeCodeZoom: 生成 Computer Use Image Results 文本行；如果没有这一行，payload 有图但模型消息解析不到。
        except Exception as error:  # 新增代码+ClaudeCodeZoom: 兜底处理格式化函数不可用；如果没有这一行，偶发导入问题会让整个 observe 失败。
            image_result_lines = [f"Computer Use Image Results", f"- image_result_count=0", f"- image_0_marker=zoom_format_failed:{type(error).__name__}"]  # 新增代码+ClaudeCodeZoom: 返回可审计失败文本；如果没有这一行，格式化失败没有任何线索。
        if image_result_lines:  # 新增代码+ClaudeCodeZoom: 确认确实有图片区文本；如果没有这一行，空列表会产生多余换行。
            legacy_text = str(payload.get("legacy_text", ""))  # 新增代码+ClaudeCodeZoom: 读取原 observe 文本；如果没有这一行，追加 zoom 图片区会丢失原始观察摘要。
            joiner = "\n" if legacy_text else ""  # 新增代码+ClaudeCodeZoom: 只在已有文本后补换行；如果没有这一行，空文本会多一个开头换行。
            payload["legacy_text"] = legacy_text + joiner + "\n".join(image_result_lines)  # 新增代码+ClaudeCodeZoom: 追加 zoom 图片区且让后出现的 image_0 覆盖原全图解析；如果没有这一行，模型仍会回灌原始截图。
    wrapped["payload"] = payload  # 新增代码+ClaudeCodeZoom: 把更新后的 payload 放回结果；如果没有这一行，局部修改不会返回给调用方。
    wrapped["text"] = json.dumps(wrapped, ensure_ascii=False, sort_keys=True)  # 新增代码+ClaudeCodeZoom: 重新生成最终 JSON 文本；如果没有这一行，result["text"] 仍是旧全图版本。
    return wrapped  # 新增代码+ClaudeCodeZoom: 返回更新后的包装结果；如果没有这一行，调用方拿不到增强结果。
# 新增代码+ClaudeCodeZoom: 函数段结束，_zoom_annotate_wrapped_result 到此结束；如果没有这个边界说明，用户不容易看出结果回写范围。


def _build_zoom_image_result(arguments: dict[str, Any], wrapped: dict[str, Any], observed_window: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:  # 新增代码+ClaudeCodeZoom: 函数段开始，从 observe 结果生成局部裁剪 image_result；如果没有这段函数，zoom 只能返回整张截图。
    if not bool(wrapped.get("ok")):  # 新增代码+ClaudeCodeZoom: 观察失败时不尝试裁剪；如果没有这一行，失败文本可能被当成有效源图继续处理。
        return None, "observe_failed"  # 新增代码+ClaudeCodeZoom: 返回观察失败原因；如果没有这一行，调用方无法解释为什么没有局部图。
    payload = wrapped.get("payload", {}) if isinstance(wrapped.get("payload", {}), dict) else {}  # 新增代码+ClaudeCodeZoom: 读取 adapter 包装 payload；如果没有这一行，legacy_text 无处获取。
    legacy_text = str(payload.get("legacy_text", ""))  # 新增代码+ClaudeCodeZoom: 读取旧 observe 文本中的图片区；如果没有这一行，源截图路径无法被发现。
    try:  # 新增代码+ClaudeCodeZoom: 导入现有图片结果文本解析器；如果没有这一行，导入失败会中断整个工具。
        from .image_messages import extract_computer_use_image_specs_from_tool_output  # 新增代码+ClaudeCodeZoom: 复用模型回灌路径解析逻辑；如果没有这一行，zoom 会自造一套路径解析规则。
        source_specs = extract_computer_use_image_specs_from_tool_output(legacy_text)  # 新增代码+ClaudeCodeZoom: 从 observe 文本中提取源图路径；如果没有这一行，裁剪没有输入图片。
    except Exception as error:  # 新增代码+ClaudeCodeZoom: 捕获解析器不可用或坏文本异常；如果没有这一行，zoom 会把解析问题冒泡成工具崩溃。
        return None, f"image_spec_parse_failed:{type(error).__name__}"  # 新增代码+ClaudeCodeZoom: 返回解析失败原因；如果没有这一行，用户不知道为什么没有局部图。
    if not source_specs:  # 新增代码+ClaudeCodeZoom: 检查 observe 是否真的提供了图片引用；如果没有这一行，空列表会在索引时崩溃。
        return None, "no_source_image_result"  # 新增代码+ClaudeCodeZoom: 返回缺少源图原因；如果没有这一行，模型无法恢复为普通 observe。
    source_spec = dict(source_specs[0])  # 新增代码+ClaudeCodeZoom: 使用第一张 observe 截图作为 zoom 源；如果没有这一行，后续修改可能污染解析器返回值。
    source_path = Path(str(source_spec.get("artifact_path", "") or ""))  # 新增代码+ClaudeCodeZoom: 把源图路径转为 Path；如果没有这一行，文件存在性和派生路径处理不稳定。
    if not source_path.is_file():  # 新增代码+ClaudeCodeZoom: 确认源图真实存在；如果没有这一行，Pillow 会抛出更难懂的文件错误。
        return None, "source_artifact_missing"  # 新增代码+ClaudeCodeZoom: 返回源图缺失原因；如果没有这一行，缺文件问题不可审计。
    try:  # 新增代码+ClaudeCodeZoom: 延迟导入 Pillow 和坐标映射函数；如果没有这一行，缺依赖会在 agent 启动阶段就失败。
        from PIL import Image  # 新增代码+ClaudeCodeZoom: 使用 Pillow 打开和裁剪 PNG/JPEG/WebP；如果没有这一行，无法真正生成局部图片。
        from .coordinates import build_screenshot_coordinate_mapping  # 新增代码+ClaudeCodeZoom: 复用正式截图 scale 合同；如果没有这一行，zoom 会手写一份易漂移坐标换算。
    except Exception as error:  # 新增代码+ClaudeCodeZoom: 处理 Pillow 或坐标模块不可用；如果没有这一行，环境缺依赖会让工具调用崩溃。
        return None, f"zoom_dependencies_unavailable:{type(error).__name__}"  # 新增代码+ClaudeCodeZoom: 返回依赖缺失原因；如果没有这一行，用户只能看到异常类型。
    x = _zoom_safe_int(arguments, "x")  # 新增代码+ClaudeCodeZoom: 读取 zoom 区域左上角 x；如果没有这一行，横向裁剪位置没有来源。
    y = _zoom_safe_int(arguments, "y")  # 新增代码+ClaudeCodeZoom: 读取 zoom 区域左上角 y；如果没有这一行，纵向裁剪位置没有来源。
    width = max(1, _zoom_safe_int(arguments, "width", 1))  # 新增代码+ClaudeCodeZoom: 读取并限制 zoom 宽度至少 1；如果没有这一行，零宽裁剪会生成无效图片。
    height = max(1, _zoom_safe_int(arguments, "height", 1))  # 新增代码+ClaudeCodeZoom: 读取并限制 zoom 高度至少 1；如果没有这一行，零高裁剪会生成无效图片。
    try:  # 新增代码+ClaudeCodeZoom: 捕获打开、换算、裁剪、保存中的所有可恢复错误；如果没有这一行，坏图会中断 agent 主循环。
        with Image.open(source_path) as source_image_handle:  # 新增代码+ClaudeCodeZoom: 打开 observe 源截图；如果没有这一行，无法读取像素尺寸和裁剪内容。
            source_image = source_image_handle.convert("RGBA")  # 新增代码+ClaudeCodeZoom: 转成稳定 RGBA 模式；如果没有这一行，不同源图模式保存 PNG 时可能表现不同。
            image_width, image_height = source_image.size  # 新增代码+ClaudeCodeZoom: 读取源图像素尺寸；如果没有这一行，坐标映射和边界裁剪无从计算。
            mapping = build_screenshot_coordinate_mapping(observed_window, int(image_width), int(image_height))  # 新增代码+ClaudeCodeZoom: 用窗口逻辑 rect 和截图尺寸计算 scale；如果没有这一行，zoom 坐标无法从屏幕逻辑坐标转成截图像素。
            if not bool(mapping.get("valid", False)):  # 新增代码+ClaudeCodeZoom: 坐标映射无效时停止裁剪；如果没有这一行，缺 rect 会产生误导性局部图。
                return None, str(mapping.get("fallback_reason", "invalid_screenshot_coordinate_mapping"))  # 新增代码+ClaudeCodeZoom: 返回映射失败原因；如果没有这一行，用户不知道是坐标数据不足。
            window_rect = mapping.get("window_logical_rect", {}) if isinstance(mapping.get("window_logical_rect", {}), dict) else {}  # 新增代码+ClaudeCodeZoom: 读取窗口逻辑矩形；如果没有这一行，屏幕坐标无法转成窗口相对坐标。
            scale = mapping.get("window_relative_logical_to_screenshot_pixel", {}) if isinstance(mapping.get("window_relative_logical_to_screenshot_pixel", {}), dict) else {}  # 新增代码+ClaudeCodeZoom: 读取逻辑到像素的比例；如果没有这一行，DPI/截图缩放会被忽略。
            scale_x = float(scale.get("scale_x", 1.0) or 1.0)  # 新增代码+ClaudeCodeZoom: 读取横向 scale；如果没有这一行，宽度换算只能假设 1:1。
            scale_y = float(scale.get("scale_y", 1.0) or 1.0)  # 新增代码+ClaudeCodeZoom: 读取纵向 scale；如果没有这一行，高度换算只能假设 1:1。
            left = int(round((x - int(window_rect.get("left", 0) or 0)) * scale_x))  # 新增代码+ClaudeCodeZoom: 把屏幕逻辑 x 转成截图像素 left；如果没有这一行，裁剪会错位。
            top = int(round((y - int(window_rect.get("top", 0) or 0)) * scale_y))  # 新增代码+ClaudeCodeZoom: 把屏幕逻辑 y 转成截图像素 top；如果没有这一行，裁剪会错位。
            right = int(round((x + width - int(window_rect.get("left", 0) or 0)) * scale_x))  # 新增代码+ClaudeCodeZoom: 计算截图像素 right；如果没有这一行，裁剪宽度无法对齐逻辑区域。
            bottom = int(round((y + height - int(window_rect.get("top", 0) or 0)) * scale_y))  # 新增代码+ClaudeCodeZoom: 计算截图像素 bottom；如果没有这一行，裁剪高度无法对齐逻辑区域。
            crop_left = max(0, min(int(image_width), left))  # 新增代码+ClaudeCodeZoom: 将左边界夹到图片范围内；如果没有这一行，越界区域会让裁剪语义不清。
            crop_top = max(0, min(int(image_height), top))  # 新增代码+ClaudeCodeZoom: 将上边界夹到图片范围内；如果没有这一行，越界区域会让裁剪语义不清。
            crop_right = max(crop_left, min(int(image_width), right))  # 新增代码+ClaudeCodeZoom: 将右边界夹到图片范围内且不小于左边界；如果没有这一行，反向区域会生成坏图。
            crop_bottom = max(crop_top, min(int(image_height), bottom))  # 新增代码+ClaudeCodeZoom: 将下边界夹到图片范围内且不小于上边界；如果没有这一行，反向区域会生成坏图。
            if crop_right <= crop_left or crop_bottom <= crop_top:  # 新增代码+ClaudeCodeZoom: 检查裁剪区域是否为空；如果没有这一行，Pillow 可能保存 0 尺寸异常图。
                return None, "zoom_region_outside_screenshot"  # 新增代码+ClaudeCodeZoom: 返回区域越界原因；如果没有这一行，用户无法调整坐标。
            zoom_path = source_path.with_name(f"{source_path.stem}_zoom_{x}_{y}_{width}_{height}_{int(time.time() * 1000)}.png")  # 新增代码+ClaudeCodeZoom: 生成同目录局部图路径；如果没有这一行，裁剪图没有稳定 artifact 文件。
            cropped_image = source_image.crop((crop_left, crop_top, crop_right, crop_bottom))  # 新增代码+ClaudeCodeZoom: 真正裁剪局部像素；如果没有这一行，zoom 仍然只是元数据。
            cropped_image.save(zoom_path, format="PNG")  # 新增代码+ClaudeCodeZoom: 保存局部 PNG artifact；如果没有这一行，模型无法读取裁剪后的图片。
            zoom_width, zoom_height = cropped_image.size  # 新增代码+ClaudeCodeZoom: 读取裁剪图尺寸；如果没有这一行，image_result 无法报告局部图大小。
    except Exception as error:  # 新增代码+ClaudeCodeZoom: 处理图片打开或裁剪失败；如果没有这一行，坏 artifact 会让整个工具调用失败。
        return None, f"zoom_crop_failed:{type(error).__name__}"  # 新增代码+ClaudeCodeZoom: 返回裁剪失败原因；如果没有这一行，调用方无法审计失败。
    zoom_block = {"type": "image_result", "model": ZOOM_IMAGE_RESULT_MODEL, "source": "zoom", "artifact_path": str(zoom_path), "image_path": str(zoom_path), "mime_type": "image/png", "width": int(zoom_width), "height": int(zoom_height), "sensitive_text_included": False, "text_redacted": True, "screenshot_coordinate_model": str(mapping.get("model", "")), "screenshot_coordinate_mapping": mapping, "zoom_source_artifact_path": str(source_path), "zoom_region_logical": {"x": x, "y": y, "width": width, "height": height}, "zoom_crop_pixel_rect": {"left": crop_left, "top": crop_top, "right": crop_right, "bottom": crop_bottom, "width": int(zoom_width), "height": int(zoom_height)}, "marker": "claudecode_parity_zoom_image_result"}  # 新增代码+ClaudeCodeZoom: 构造局部放大图片块；如果没有这一行，裁剪图无法进入统一 image_result 协议。
    return zoom_block, ""  # 新增代码+ClaudeCodeZoom: 返回成功图片块和空失败原因；如果没有这一行，调用方拿不到 zoom 结果。
# 新增代码+ClaudeCodeZoom: 函数段结束，_build_zoom_image_result 到此结束；如果没有这个边界说明，用户不容易看出 zoom 裁剪流程范围。


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
                if resolved_window.get("target_ref"):  # 新增代码+ObserveTargetRef：检查解析窗口是否来自 registry target；如果没有这一行，旧 observe 参数不会携带 target_ref。
                    legacy_arguments["target_ref"] = resolved_window.get("target_ref")  # 新增代码+ObserveTargetRef：同步 target_ref 给 actionability 摘要；如果没有这一行，终端日志里的 target_ref 仍会显示为空。
        legacy_text = computer_use_internal_adapter_tools.internal_observe_desktop(legacy_arguments, self.controller, self.callbacks.record_observation, self.callbacks.record_runtime_trace, self.callbacks.record_image_artifacts)  # 修改代码+ComputerUseMcpV2InternalAdapterFence：通过内部 facade 调用观察截图能力；如果没有这一行，接线层会继续直接引用旧 computer_observe 工具名。
        wrapped = _wrap_legacy_text(tool_name, "computer_observe", legacy_text)  # 修改代码+McpObservedWindowFix: 先包装 observe 结果再决定是否写 session 状态；如果没有这一行，失败 observe 也可能污染窗口上下文。
        observed_window = legacy_arguments.get("window") if isinstance(legacy_arguments.get("window"), dict) else {}  # 新增代码+McpObservedWindowFix: 读取本次 observe 使用的可信窗口；如果没有这一行，后续 click 无法复用同一目标。
        if tool_name == "zoom":  # 新增代码+ClaudeCodeZoom: 只对 zoom 执行局部裁剪增强；如果没有这一行，普通 observe/screenshot 会被错误改成局部图。
            zoom_block, zoom_failure_reason = _build_zoom_image_result(arguments, wrapped, observed_window)  # 新增代码+ClaudeCodeZoom: 根据源截图和坐标映射生成局部图片块；如果没有这一行，zoom 仍只会返回全窗口截图。
            zoom_results = [zoom_block] if zoom_block is not None else []  # 新增代码+ClaudeCodeZoom: 把可选图片块转成列表；如果没有这一行，结果回写函数要处理 None 分支。
            wrapped = _zoom_annotate_wrapped_result(wrapped, zoom_results, zoom_failure_reason)  # 新增代码+ClaudeCodeZoom: 把 zoom 图片和失败原因写回 payload/text；如果没有这一行，模型下一轮仍解析不到局部图。
            if zoom_results:  # 新增代码+ClaudeCodeZoom: 只有真实生成裁剪图时才登记 artifact；如果没有这一行，失败 zoom 会产生空 artifact 事件。
                self.callbacks.record_image_artifacts(wrapped, "computer_observe")  # 新增代码+ClaudeCodeZoom: 复用观察图片登记链记录局部图；如果没有这一行，active_artifacts 可能只保留原全图。
        if bool(wrapped.get("ok")) and observed_window:  # 新增代码+McpObservedWindowFix: 只有成功观察且窗口非空才保存；如果没有这一行，失败或空窗口会污染动作目标。
            resource_freshness = _build_resource_freshness_for_arguments(observed_window, arguments)  # 新增代码+ResourceFreshnessAdapter：根据观察窗口和用户目标生成资源新鲜度报告；如果没有这一行，旧资源恢复不会被记录。
            self.state.last_resource_freshness = dict(resource_freshness)  # 新增代码+ResourceFreshnessAdapter：保存资源新鲜度给后续动作使用；如果没有这一行，type/key 仍可能穿透旧文档。
            wrapped = _annotate_wrapped_result_with_resource_freshness(wrapped, resource_freshness)  # 新增代码+ResourceFreshnessAdapter：把资源报告写回 observe 结果；如果没有这一行，模型和收敛层看不到旧资源阻断。
            self.callbacks.record_runtime_trace("computer_use_mcp_resource_freshness_observed", {"tool_name": tool_name, "decision": resource_freshness.get("decision", ""), "allowed": bool(resource_freshness.get("allowed", True))})  # 新增代码+ResourceFreshnessAdapter：记录资源新鲜度证据；如果没有这一行，验收失败时难以定位资源门禁是否运行。
            self.state.last_observed_window = dict(observed_window)  # 新增代码+McpObservedWindowFix: 把窗口写入会话状态；如果没有这一行，left_click 后续仍会缺少可信 window。
        return wrapped  # 修改代码+McpObservedWindowFix: 返回包装后的 observe 结果；如果没有这一行，调用方拿不到观察结果。
    # 新增代码+McpSessionAdapter: 函数段结束，_call_observe 到此结束；如果没有这个边界说明，用户不容易看出观察工具范围。

    def _call_action(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpSessionAdapter: 函数段开始，执行高风险桌面动作；如果没有这段函数，click/type/key 无法复用旧权限和门禁。
        legacy_arguments = _controller_arguments_for_tool(tool_name, arguments)  # 新增代码+McpSessionAdapter: 把 MCP 原子名映射为旧动作参数；如果没有这一行，旧 computer_action 收不到 action。
        _copy_action_target_fields_from_arguments(legacy_arguments, arguments)  # 新增代码+ExplicitTargetRefResourceFallback：把 target_ref/window 从 MCP 原始参数补回旧动作参数；如果没有这一行，显式窗口选择会在映射层丢失。
        if not legacy_arguments.get("window") and self.state.last_observed_window and _action_can_reuse_observed_window(legacy_arguments):  # 新增代码+McpObservedWindowFix: 动作缺窗口且适合复用时注入最近观察窗口；如果没有这一行，模型 observe 后 click 仍会被 Phase 30 拒绝。
            legacy_arguments["window"] = dict(self.state.last_observed_window)  # 新增代码+McpObservedWindowFix: 传入窗口副本避免污染 session 状态；如果没有这一行，旧 computer_action 收不到可信目标。
            self.callbacks.record_runtime_trace("computer_use_mcp_observed_window_reused", {"tool_name": tool_name, "action": legacy_arguments.get("action", ""), "window_id": legacy_arguments["window"].get("window_id", "")})  # 新增代码+McpObservedWindowFix: 记录窗口复用证据；如果没有这一行，验收失败时难以证明 adapter 是否自动注入目标。
        if _inject_explicit_target_ref_window(self.controller, legacy_arguments):  # 新增代码+ExplicitTargetRefResourceFallback：显式 target_ref 存在时先解析并注入对应窗口；如果没有这一行，多目标任务会把明确目标误判为歧义或缺窗口。
            self.callbacks.record_runtime_trace("computer_use_mcp_explicit_target_ref_window_injected", {"tool_name": tool_name, "action": legacy_arguments.get("action", ""), "target_ref": legacy_arguments.get("target_ref", ""), "window_id": legacy_arguments.get("window", {}).get("window_id", "") if isinstance(legacy_arguments.get("window"), dict) else ""})  # 新增代码+ExplicitTargetRefResourceFallback：记录显式目标注入证据；如果没有这一行，真实验收日志难以证明 adapter 已在底层动作前绑定窗口。
        implicit_resolution = _resolve_implicit_target_for_action(self.controller, legacy_arguments)  # 新增代码+MultiTargetRefGate：读取漏 target_ref 动作的隐式目标解析结果；如果没有这一行，多目标歧义无法在 adapter 层零事件拦截。
        if implicit_resolution.get("decision") == "multiple_active_targets_require_target_ref":  # 新增代码+MultiTargetRefGate：多目标时必须显式 target_ref；如果没有这一行，复杂多应用任务会误用最近窗口。
            self.callbacks.record_runtime_trace("computer_use_mcp_multiple_targets_require_target_ref", {"tool_name": tool_name, "action": legacy_arguments.get("action", ""), "target_count": implicit_resolution.get("target_count", 0), "low_level_event_count": 0})  # 新增代码+MultiTargetRefGate：记录多目标零事件拒绝证据；如果没有这一行，验收日志难以证明动作没穿透。
            return _multiple_target_ref_required_result(tool_name, implicit_resolution)  # 新增代码+MultiTargetRefGate：返回多目标拒绝结果；如果没有这一行，函数会继续调用真实桌面执行。
        if _inject_single_active_target_ref(self.controller, legacy_arguments):  # 新增代码+TargetRefAutoInject：单 active target 且模型漏写 target_ref 时自动补齐；如果没有这一行，真实验收会继续卡在 target_ref_required_for_bound_window_action。
            self.callbacks.record_runtime_trace("computer_use_mcp_single_active_target_ref_injected", {"tool_name": tool_name, "action": legacy_arguments.get("action", ""), "target_ref": legacy_arguments.get("target_ref", "")})  # 新增代码+TargetRefAutoInject：记录自动补 target_ref 证据；如果没有这一行，验收失败时难以证明 adapter 是否接上 registry。
        resource_freshness = dict(self.state.last_resource_freshness or {})  # 新增代码+ResourceFreshnessAdapter：读取最近 observe 得到的资源新鲜度；如果没有这一行，动作前无法知道旧资源风险。
        action_window = legacy_arguments.get("window") if isinstance(legacy_arguments.get("window"), dict) else {}  # 新增代码+ResourceFreshnessActionFallback：读取即将执行动作的真实窗口；如果没有这一行，缺 observe 状态时无法做 action 级资源兜底。
        if not resource_freshness and action_window:  # 新增代码+ResourceFreshnessActionFallback：只有 observe 没留下资源状态且动作有窗口时才兜底；如果没有这一行，真实验收里的旧资源恢复会继续穿透。
            resource_freshness = _build_resource_freshness_for_action_arguments(action_window, arguments)  # 新增代码+ResourceFreshnessActionFallback：根据 action 窗口生成资源新鲜度报告；如果没有这一行，标题里的旧文件名不会被阻断。
            if resource_freshness.get("decision") != "resource_freshness_not_required":  # 新增代码+ResourceFreshnessActionFallback：只记录有意义的资源判断，避免普通动作日志噪音；如果没有这一行，运行日志会被默认允许状态刷屏。
                self.state.last_resource_freshness = dict(resource_freshness)  # 新增代码+ResourceFreshnessActionFallback：把兜底判断写回状态；如果没有这一行，后续动作会重复计算且难以收敛。
                self.callbacks.record_runtime_trace("computer_use_mcp_resource_freshness_action_checked", {"tool_name": tool_name, "action": legacy_arguments.get("action", ""), "decision": resource_freshness.get("decision", ""), "allowed": bool(resource_freshness.get("allowed", True)), "low_level_event_count": 0})  # 新增代码+ResourceFreshnessActionFallback：记录 action 级资源判断证据；如果没有这一行，验收日志无法证明阻断发生在底层动作前。
        if resource_freshness and not bool(resource_freshness.get("allowed", True)) and not _arguments_allow_existing_resource(arguments):  # 新增代码+ResourceFreshnessAdapter：旧资源未授权时阻断写动作；如果没有这一行，type/key/click 会继续写入恢复旧文档。
            self.callbacks.record_runtime_trace("computer_use_mcp_resource_freshness_action_blocked", {"tool_name": tool_name, "action": legacy_arguments.get("action", ""), "decision": resource_freshness.get("decision", ""), "low_level_event_count": 0})  # 新增代码+ResourceFreshnessAdapter：记录零事件阻断证据；如果没有这一行，安全验收无法证明动作被执行前拦下。
            return _resource_user_action_result(tool_name, resource_freshness)  # 新增代码+ResourceFreshnessAdapter：返回资源用户动作阻断结果；如果没有这一行，函数会继续调用真实桌面执行。
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
