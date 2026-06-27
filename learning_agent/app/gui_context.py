"""GUI 会话上下文构建模块。"""  # 新增代码+GuiContextBuilder：说明本文件负责把桌面 GUI 历史消息整理成模型输入；如果没有这行，维护者很难知道这里不是普通聊天 UI 代码。

from __future__ import annotations  # 新增代码+GuiContextBuilder：启用延迟类型解析；如果没有这行，返回自身类型或较新类型语法时更容易遇到兼容问题。

import os  # 新增代码+GuiContextBuilder：读取 GUI context 预算环境变量；如果没有这行，真实 GUI 验收无法通过环境变量调小阈值。
from dataclasses import dataclass, field  # 新增代码+GuiContextBuilder：用 dataclass 表达构建结果和阈值；如果没有这行，调用方只能面对松散 dict。
from pathlib import Path  # 新增代码+GuiContextBuilder：规范化 workspace 和 artifact 路径；如果没有这行，Windows 路径拼接容易出错。
from typing import Any, Iterable, Mapping  # 新增代码+GuiContextBuilder：标注 GUI 消息和 JSON-like 输入类型；如果没有这行，接口边界不清楚。

from learning_agent.core.compact import estimate_messages_chars  # 新增代码+GuiContextBuilder：复用现有字符估算逻辑；如果没有这行，GUI 会另起一套不一致的预算算法。
from learning_agent.core.compact_pipeline import prepare_messages_before_model  # 新增代码+GuiContextBuilder：接入项目已有上下文压缩流水线；如果没有这行，GUI 会绕开成熟 compact 模块。
from learning_agent.core.task_state import TaskState  # 新增代码+GuiContextBuilder：用本轮 prompt 建立任务状态；如果没有这行，compact 摘要可能错误围绕第一句寒暄。


DEFAULT_GUI_CONTEXT_MAX_MESSAGES = 24  # 新增代码+GuiContextBuilder：定义 GUI 默认最大消息数；如果没有这行，短会话和长会话的预算没有统一默认值。
DEFAULT_GUI_CONTEXT_MAX_CHARS = 60_000  # 新增代码+GuiContextBuilder：定义 GUI 默认最大字符数；如果没有这行，极长历史可能不触发压缩。
MIN_GUI_CONTEXT_MAX_MESSAGES = 3  # 新增代码+GuiContextBuilder：确保至少能放摘要、目标和当前问题；如果没有这行，过小阈值会把当前 prompt 挤掉。
MIN_GUI_CONTEXT_MAX_CHARS = 100  # 新增代码+GuiContextBuilder：确保字符阈值不会小到所有正常输入都失真；如果没有这行，错误环境值可能造成持续压缩失败。


@dataclass  # 新增代码+GuiContextBuilder：自动生成阈值对象初始化逻辑；如果没有这行，阈值返回值会变成脆弱的 tuple。
class GuiContextLimits:  # 新增代码+GuiContextBuilder：类段开始，表达 GUI 上下文预算限制；如果没有这个类，调用方不知道 max_messages/max_chars 的字段语义。
    max_messages: int  # 新增代码+GuiContextBuilder：保存最大消息数；如果没有这行，builder 无法按消息数量触发 compact。
    max_chars: int  # 新增代码+GuiContextBuilder：保存最大字符数；如果没有这行，builder 无法按文本长度触发 compact。
    # 新增代码+GuiContextBuilder：类段结束，GuiContextLimits 到此结束；这段边界说明方便用户理解它只保存预算阈值。


@dataclass  # 新增代码+GuiContextBuilder：自动生成构建结果初始化逻辑；如果没有这行，调用方要手写容易漏字段的 dict。
class GuiContextBuildResult:  # 新增代码+GuiContextBuilder：类段开始，承载 GUI context 构建后的所有结果；如果没有这个类，bridge/adapter 之间的契约会散乱。
    messages: list[dict[str, Any]]  # 新增代码+GuiContextBuilder：保存 Responses input 格式消息；如果没有这行，adapter 无法拿到完整上下文。
    compacted: bool  # 新增代码+GuiContextBuilder：标记本轮是否发生 compact；如果没有这行，GUI 状态栏无法显示压缩行为。
    event_payload: dict[str, Any] = field(default_factory=dict)  # 新增代码+GuiContextBuilder：保存可写入事件流的脱敏预算信息；如果没有这行，右侧状态栏缺少可观测证据。
    task_state_summary: dict[str, str] = field(default_factory=dict)  # 新增代码+GuiContextBuilder：保存脱敏任务状态摘要；如果没有这行，测试和调试难以确认目标是否正确。
    # 新增代码+GuiContextBuilder：类段结束，GuiContextBuildResult 到此结束；这段边界说明方便用户知道它是 builder 的统一返回值。


def _safe_text(value: Any) -> str:  # 新增代码+GuiContextBuilder：函数段开始，把任意输入清洗成安全文本；如果没有这段函数，None 或数字会污染模型消息。
    return str(value or "").strip()  # 新增代码+GuiContextBuilder：返回去掉首尾空白的字符串；如果没有这行，空白 prompt 和 None 会进入上下文。
# 新增代码+GuiContextBuilder：函数段结束，_safe_text 到此结束；这段边界说明方便用户知道它只负责文本清洗。


def _mapping_get(message: Any, key: str, default: Any = "") -> Any:  # 新增代码+GuiContextBuilder：函数段开始，兼容 dict 和 dataclass 消息字段读取；如果没有这段函数，builder 只能处理一种消息形态。
    if isinstance(message, Mapping):  # 新增代码+GuiContextBuilder：优先处理字典消息；如果没有这行，测试和 JSON 恢复消息无法读取字段。
        return message.get(key, default)  # 新增代码+GuiContextBuilder：从 dict 中读取字段；如果没有这行，dict 消息会全部变成空值。
    return getattr(message, key, default)  # 新增代码+GuiContextBuilder：从 dataclass 或对象属性读取字段；如果没有这行，真实 GuiMessage 无法被 builder 使用。
# 新增代码+GuiContextBuilder：函数段结束，_mapping_get 到此结束；这段边界说明方便用户知道它只是字段适配器。


def _content_to_text(content: Any) -> str:  # 新增代码+GuiContextBuilder：函数段开始，把多种 content 形态转成普通文本；如果没有这段函数，Responses input 和 GUI dict 会解析不一致。
    if isinstance(content, str):  # 新增代码+GuiContextBuilder：直接支持字符串正文；如果没有这行，最常见的 GUI text 无法提取。
        return _safe_text(content)  # 新增代码+GuiContextBuilder：清洗字符串正文；如果没有这行，首尾空白会污染上下文。
    if isinstance(content, list):  # 新增代码+GuiContextBuilder：支持 Responses input 分片列表；如果没有这行，已有 API 格式消息无法反向转换。
        pieces: list[str] = []  # 新增代码+GuiContextBuilder：准备收集分片文本；如果没有这行，多个 input_text 片段无法合并。
        for item in content:  # 新增代码+GuiContextBuilder：逐个扫描 content 分片；如果没有这行，只能处理第一个或完全不处理。
            if isinstance(item, Mapping):  # 新增代码+GuiContextBuilder：只从字典分片读取 text；如果没有这行，非字典分片会触发属性错误。
                pieces.append(_safe_text(item.get("text", "")))  # 新增代码+GuiContextBuilder：收集 text 字段；如果没有这行，input_text/output_text 内容会丢失。
        return "\n".join(piece for piece in pieces if piece)  # 新增代码+GuiContextBuilder：合并非空分片；如果没有这行，调用方拿不到可发送给 compact 的普通文本。
    return _safe_text(content)  # 新增代码+GuiContextBuilder：兜底把未知内容转成字符串；如果没有这行，异常结构会让 builder 崩溃。
# 新增代码+GuiContextBuilder：函数段结束，_content_to_text 到此结束；这段边界说明方便用户知道它负责正文抽取。


def _message_text(message: Any) -> str:  # 新增代码+GuiContextBuilder：函数段开始，从 GUI 消息中提取正文文本；如果没有这段函数，text/content 两种字段会重复处理。
    text = _safe_text(_mapping_get(message, "text", ""))  # 新增代码+GuiContextBuilder：优先读取 GUI 的 text 字段；如果没有这行，真实 GuiMessage 正文会被忽略。
    if text:  # 新增代码+GuiContextBuilder：已有 text 时直接使用；如果没有这行，后续 content 兜底可能覆盖真实正文。
        return text  # 新增代码+GuiContextBuilder：返回 GUI text；如果没有这行，函数会继续误读 content。
    return _content_to_text(_mapping_get(message, "content", ""))  # 新增代码+GuiContextBuilder：兜底读取 content；如果没有这行，dict 或 Responses 格式历史无法被转换。
# 新增代码+GuiContextBuilder：函数段结束，_message_text 到此结束；这段边界说明方便用户知道它负责消息正文读取。


def _normalize_role(role: Any) -> str:  # 新增代码+GuiContextBuilder：函数段开始，把角色归一成 user 或 assistant；如果没有这段函数，系统/工具/未知角色会污染 ChatGPT OAuth 输入。
    safe_role = _safe_text(role).lower()  # 新增代码+GuiContextBuilder：清洗并小写角色；如果没有这行，大小写差异会导致角色判断失败。
    return "assistant" if safe_role == "assistant" else "user"  # 新增代码+GuiContextBuilder：只保留 assistant，其它都降级为 user；如果没有这行，Responses input 可能收到不支持的 GUI 角色。
# 新增代码+GuiContextBuilder：函数段结束，_normalize_role 到此结束；这段边界说明方便用户知道它只负责角色白名单。


def _should_keep_message(message: Any, role: str, text: str) -> bool:  # 新增代码+GuiContextBuilder：函数段开始，决定 GUI 历史消息是否进入模型上下文；如果没有这段函数，空占位消息会污染请求。
    if not text:  # 新增代码+GuiContextBuilder：跳过空正文；如果没有这行，running 占位助手会作为空消息进入模型。
        return False  # 新增代码+GuiContextBuilder：空正文不保留；如果没有这行，空消息会增加预算压力。
    if role == "assistant":  # 新增代码+GuiContextBuilder：助手消息需要额外判断状态；如果没有这行，未完成助手回复可能进入模型。
        status = _safe_text(_mapping_get(message, "status", ""))  # 新增代码+GuiContextBuilder：读取助手消息状态；如果没有这行，无法区分 completed/running。
        return status == "completed"  # 新增代码+GuiContextBuilder：只保留已完成助手回复；如果没有这行，当前空回复或失败回复会误入上下文。
    return True  # 新增代码+GuiContextBuilder：用户消息只要有文本就保留；如果没有这行，正常用户历史会被全部丢弃。
# 新增代码+GuiContextBuilder：函数段结束，_should_keep_message 到此结束；这段边界说明方便用户知道它负责过滤消息。


def _normalize_session_messages(session_messages: Iterable[Any]) -> list[dict[str, Any]]:  # 新增代码+GuiContextBuilder：函数段开始，把 GUI 历史转换为 compact 可处理格式；如果没有这段函数，bridge 无法把会话历史传给模型。
    normalized: list[dict[str, Any]] = []  # 新增代码+GuiContextBuilder：准备输出列表；如果没有这行，函数没有地方保存结果。
    for message in session_messages:  # 新增代码+GuiContextBuilder：逐条处理 GUI 消息；如果没有这行，只能处理空上下文。
        role = _normalize_role(_mapping_get(message, "role", "user"))  # 新增代码+GuiContextBuilder：读取并归一角色；如果没有这行，模型输入角色不稳定。
        text = _message_text(message)  # 新增代码+GuiContextBuilder：提取消息文本；如果没有这行，正文无法进入上下文。
        if not _should_keep_message(message, role, text):  # 新增代码+GuiContextBuilder：过滤空消息和未完成助手消息；如果没有这行，GUI 占位符会污染模型输入。
            continue  # 新增代码+GuiContextBuilder：跳过不可用消息；如果没有这行，过滤条件不会生效。
        normalized.append({"role": role, "content": text, "turn_id": _safe_text(_mapping_get(message, "turn_id", ""))})  # 新增代码+GuiContextBuilder：保存 compact 消息和 turn_id；如果没有这行，历史上下文不会形成模型输入。
    return normalized  # 新增代码+GuiContextBuilder：返回归一化消息；如果没有这行，调用方拿不到结果。
# 新增代码+GuiContextBuilder：函数段结束，_normalize_session_messages 到此结束；这段边界说明方便用户知道它负责历史消息标准化。


def _current_prompt_exists(messages: list[dict[str, Any]], current_prompt: str, turn_id: str) -> bool:  # 新增代码+GuiContextBuilder：函数段开始，判断当前 prompt 是否已经在历史中；如果没有这段函数，builder 可能重复追加当前问题。
    safe_prompt = _safe_text(current_prompt)  # 新增代码+GuiContextBuilder：清洗当前 prompt；如果没有这行，空白差异会影响去重。
    safe_turn_id = _safe_text(turn_id)  # 新增代码+GuiContextBuilder：清洗当前 turn id；如果没有这行，turn id 比较不稳定。
    for message in messages:  # 新增代码+GuiContextBuilder：扫描归一化消息；如果没有这行，无法判断已有消息。
        if message.get("role") != "user":  # 新增代码+GuiContextBuilder：只检查用户消息；如果没有这行，助手重复文本可能误判为当前 prompt 已存在。
            continue  # 新增代码+GuiContextBuilder：非用户消息跳过；如果没有这行，角色过滤不会生效。
        if _safe_text(message.get("content")) != safe_prompt:  # 新增代码+GuiContextBuilder：正文不一致时继续找；如果没有这行，任何用户消息都会误判。
            continue  # 新增代码+GuiContextBuilder：正文不匹配就跳过；如果没有这行，后续 turn_id 判断会误用。
        if not safe_turn_id or _safe_text(message.get("turn_id")) in {"", safe_turn_id}:  # 新增代码+GuiContextBuilder：turn_id 匹配或缺省时认为当前 prompt 已存在；如果没有这行，当前用户消息可能被重复追加。
            return True  # 新增代码+GuiContextBuilder：确认当前 prompt 已存在；如果没有这行，函数永远返回 False。
    return False  # 新增代码+GuiContextBuilder：没有匹配消息时返回 False；如果没有这行，缺失当前 prompt 的场景无法补齐。
# 新增代码+GuiContextBuilder：函数段结束，_current_prompt_exists 到此结束；这段边界说明方便用户知道它负责 exact-once 判断。


def _ensure_current_prompt_once(messages: list[dict[str, Any]], current_prompt: str, turn_id: str) -> list[dict[str, Any]]:  # 新增代码+GuiContextBuilder：函数段开始，保证当前 prompt 至少且至多出现一次；如果没有这段函数，异步 GUI 可能丢当前问题或发两遍。
    safe_prompt = _safe_text(current_prompt)  # 新增代码+GuiContextBuilder：清洗当前 prompt；如果没有这行，空输入无法被统一处理。
    if not safe_prompt:  # 新增代码+GuiContextBuilder：空 prompt 不追加；如果没有这行，空用户消息会进入模型。
        return list(messages)  # 新增代码+GuiContextBuilder：返回原消息副本；如果没有这行，空 prompt 场景可能返回 None。
    if _current_prompt_exists(messages, safe_prompt, turn_id):  # 新增代码+GuiContextBuilder：检测当前 prompt 是否已经存在；如果没有这行，已写入 session 的当前消息会重复。
        return list(messages)  # 新增代码+GuiContextBuilder：已有当前 prompt 时直接返回；如果没有这行，exact-once 去重不会生效。
    return list(messages) + [{"role": "user", "content": safe_prompt, "turn_id": _safe_text(turn_id)}]  # 新增代码+GuiContextBuilder：缺失时追加当前 prompt；如果没有这行，当前问题可能不发给模型。
# 新增代码+GuiContextBuilder：函数段结束，_ensure_current_prompt_once 到此结束；这段边界说明方便用户知道它负责当前问题补齐。


def _safe_int(value: Any, default: int, minimum: int) -> int:  # 新增代码+GuiContextBuilder：函数段开始，安全读取正整数配置；如果没有这段函数，坏环境变量会让 GUI 启动失败。
    try:  # 新增代码+GuiContextBuilder：尝试转换整数；如果没有这行，字符串数字无法被使用。
        parsed = int(value)  # 新增代码+GuiContextBuilder：执行整数转换；如果没有这行，无法从环境变量得到数值。
    except (TypeError, ValueError):  # 新增代码+GuiContextBuilder：捕获空值和坏字符串；如果没有这行，错误环境变量会抛异常。
        parsed = default  # 新增代码+GuiContextBuilder：坏配置回退默认值；如果没有这行，GUI 没有安全退路。
    return max(minimum, parsed)  # 新增代码+GuiContextBuilder：应用最小阈值保护；如果没有这行，小到离谱的配置会破坏 compact 结果。
# 新增代码+GuiContextBuilder：函数段结束，_safe_int 到此结束；这段边界说明方便用户知道它只负责配置数字清洗。


def gui_context_limits_from_env(env: Mapping[str, str] | None = None) -> GuiContextLimits:  # 新增代码+GuiContextBuilder：函数段开始，从环境变量读取 GUI 上下文预算；如果没有这段函数，真实 GUI 验收无法控制压缩触发点。
    source = env if env is not None else os.environ  # 新增代码+GuiContextBuilder：支持测试传入 env，也支持真实运行读 os.environ；如果没有这行，测试会污染全局环境。
    max_messages = _safe_int(source.get("OPENHARNESS_GUI_CONTEXT_MAX_MESSAGES"), DEFAULT_GUI_CONTEXT_MAX_MESSAGES, MIN_GUI_CONTEXT_MAX_MESSAGES)  # 新增代码+GuiContextBuilder：读取消息数量阈值；如果没有这行，小阈值视觉验收无法生效。
    max_chars = _safe_int(source.get("OPENHARNESS_GUI_CONTEXT_MAX_CHARS"), DEFAULT_GUI_CONTEXT_MAX_CHARS, MIN_GUI_CONTEXT_MAX_CHARS)  # 新增代码+GuiContextBuilder：读取字符数量阈值；如果没有这行，长文本 compact 无法由环境控制。
    return GuiContextLimits(max_messages=max_messages, max_chars=max_chars)  # 新增代码+GuiContextBuilder：返回结构化阈值；如果没有这行，调用方拿不到预算配置。
# 新增代码+GuiContextBuilder：函数段结束，gui_context_limits_from_env 到此结束；这段边界说明方便用户知道它是环境变量入口。


def compact_messages_to_responses_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:  # 新增代码+GuiContextBuilder：函数段开始，把 compact 消息转成 Responses input；如果没有这段函数，Direct SSE 不能直接使用 builder 输出。
    responses_messages: list[dict[str, Any]] = []  # 新增代码+GuiContextBuilder：准备输出列表；如果没有这行，转换结果无处保存。
    for message in messages:  # 新增代码+GuiContextBuilder：逐条转换 compact 消息；如果没有这行，历史消息无法进入 Responses input。
        role = _normalize_role(message.get("role", "user"))  # 新增代码+GuiContextBuilder：归一化角色；如果没有这行，system 等角色可能进入 ChatGPT OAuth 请求。
        text = _content_to_text(message.get("content", ""))  # 新增代码+GuiContextBuilder：提取普通文本；如果没有这行，嵌套内容无法发送。
        if not text:  # 新增代码+GuiContextBuilder：跳过空文本；如果没有这行，模型请求会包含空消息。
            continue  # 新增代码+GuiContextBuilder：空文本不输出；如果没有这行，过滤不会生效。
        content_type = "output_text" if role == "assistant" else "input_text"  # 修改代码+GuiContextDirectSse400Fix：助手历史必须使用 output_text，用户输入才使用 input_text；如果没有这行，ChatGPT Codex endpoint 会用 invalid_value 拒绝多轮上下文。
        responses_messages.append({"role": role, "content": [{"type": content_type, "text": text}]})  # 修改代码+GuiContextDirectSse400Fix：按角色写入 Responses 分片；如果没有这行，adapter 拿不到 API 兼容格式且助手历史会继续触发 400。
    return responses_messages  # 新增代码+GuiContextBuilder：返回 Responses input 消息；如果没有这行，调用方拿不到转换结果。
# 新增代码+GuiContextBuilder：函数段结束，compact_messages_to_responses_input 到此结束；这段边界说明方便用户知道它负责模型输入格式转换。


def responses_input_to_compact_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:  # 新增代码+GuiContextBuilder：函数段开始，把 Responses input 反转成 compact 消息；如果没有这段函数，后续 reactive compact 无法复用现有流水线。
    compact_messages: list[dict[str, Any]] = []  # 新增代码+GuiContextBuilder：准备输出列表；如果没有这行，转换结果无处保存。
    for message in messages:  # 新增代码+GuiContextBuilder：逐条扫描 Responses input；如果没有这行，无法处理多轮上下文。
        if not isinstance(message, Mapping):  # 新增代码+GuiContextBuilder：跳过非 dict 消息；如果没有这行，坏输入会触发属性错误。
            continue  # 新增代码+GuiContextBuilder：坏消息不参与转换；如果没有这行，过滤不会生效。
        role = _normalize_role(message.get("role", "user"))  # 新增代码+GuiContextBuilder：归一化角色；如果没有这行，compact 可能收到未知角色。
        text = _content_to_text(message.get("content", ""))  # 新增代码+GuiContextBuilder：提取文本；如果没有这行，Responses 分片无法被 compact 使用。
        if text:  # 新增代码+GuiContextBuilder：只保留非空文本；如果没有这行，空消息会浪费预算。
            compact_messages.append({"role": role, "content": text})  # 新增代码+GuiContextBuilder：写入 compact 格式；如果没有这行，reactive compact 没有输入。
    return compact_messages  # 新增代码+GuiContextBuilder：返回 compact 消息；如果没有这行，调用方拿不到转换结果。
# 新增代码+GuiContextBuilder：函数段结束，responses_input_to_compact_messages 到此结束；这段边界说明方便用户知道它负责格式反转。


def _fit_compact_messages_to_limit(messages: list[dict[str, Any]], max_messages: int) -> list[dict[str, Any]]:  # 新增代码+GuiContextBuilder：函数段开始，把 compact 后仍超数量预算的消息贴合到上限；如果没有这段函数，post-compact restore 可能让 GUI 请求继续超预算。
    safe_limit = max(MIN_GUI_CONTEXT_MAX_MESSAGES, int(max_messages))  # 新增代码+GuiContextBuilder：保护最小消息预算；如果没有这行，极小阈值会把当前 prompt 挤掉。
    if len(messages) <= safe_limit:  # 新增代码+GuiContextBuilder：未超预算时直接返回；如果没有这行，短上下文也会被不必要合并。
        return list(messages)  # 新增代码+GuiContextBuilder：返回消息副本避免调用方误改原列表；如果没有这行，后续修改可能污染 compact decision。
    tail_count = max(1, safe_limit - 1)  # 新增代码+GuiContextBuilder：保留尽可能多的尾部近期消息；如果没有这行，当前用户 prompt 可能被合并进摘要而不够显眼。
    head_messages = messages[:-tail_count]  # 新增代码+GuiContextBuilder：取出需要合并的前置摘要消息；如果没有这行，无法减少消息数量。
    tail_messages = messages[-tail_count:]  # 新增代码+GuiContextBuilder：保留尾部近期消息；如果没有这行，当前问题和最近上下文会丢失。
    folded_text = "\n\n".join(_content_to_text(message.get("content", "")) for message in head_messages if _content_to_text(message.get("content", "")))  # 新增代码+GuiContextBuilder：把前置摘要合并成一条文本；如果没有这行，超出的摘要消息无法保留。
    folded_message = {"role": "user", "content": folded_text or "[compact_budget_fit] compact summary folded to fit GUI message budget."}  # 新增代码+GuiContextBuilder：创建合并后的预算消息；如果没有这行，前置 compact 摘要会被直接丢弃。
    return [folded_message] + list(tail_messages)  # 新增代码+GuiContextBuilder：返回一条合并摘要加近期尾部消息；如果没有这行，builder 无法满足消息数量预算。
# 新增代码+GuiContextBuilder：函数段结束，_fit_compact_messages_to_limit 到此结束；这段边界说明方便用户知道它只负责最终消息数量贴合。


def _task_state_summary(task_state: TaskState) -> dict[str, str]:  # 新增代码+GuiContextBuilder：函数段开始，提取不含原始历史的任务状态摘要；如果没有这段函数，测试和事件可能直接读取整个 TaskState。
    return {"current_goal": task_state.current_goal, "latest_user_input": task_state.latest_user_input, "original_user_request": task_state.original_user_request}  # 新增代码+GuiContextBuilder：返回当前目标等少量字段；如果没有这行，无法验证 compact 目标是否正确。
# 新增代码+GuiContextBuilder：函数段结束，_task_state_summary 到此结束；这段边界说明方便用户知道它不暴露历史全文。


def _build_event_payload(session_id: str, run_id: str, turn_id: str, limits: GuiContextLimits, input_count: int, output_count: int, chars_before: int, chars_after: int, compacted: bool, reason: str, compact_generation: int) -> dict[str, Any]:  # 新增代码+GuiContextBuilder：函数段开始，生成脱敏上下文预算事件；如果没有这段函数，GUI 状态栏缺少可验证预算指标。
    return {  # 新增代码+GuiContextBuilder：返回结构化 payload；如果没有这行，调用方无法写入事件流。
        "source": "gui_session_messages",  # 新增代码+GuiContextBuilder：标记上下文来自 GUI 会话历史；如果没有这行，事件来源不清楚。
        "session_id": _safe_text(session_id),  # 新增代码+GuiContextBuilder：写入 session id；如果没有这行，事件无法归属会话。
        "run_id": _safe_text(run_id),  # 新增代码+GuiContextBuilder：写入 run id；如果没有这行，事件无法归属运行。
        "turn_id": _safe_text(turn_id),  # 新增代码+GuiContextBuilder：写入 turn id；如果没有这行，事件无法归属轮次。
        "input_message_count": input_count,  # 新增代码+GuiContextBuilder：记录压缩前消息数；如果没有这行，GUI 看不到输入规模。
        "output_message_count": output_count,  # 新增代码+GuiContextBuilder：记录压缩后消息数；如果没有这行，GUI 看不到压缩收益。
        "estimated_chars_before": chars_before,  # 新增代码+GuiContextBuilder：记录压缩前估算字符数；如果没有这行，长上下文问题难以量化。
        "estimated_chars_after": chars_after,  # 新增代码+GuiContextBuilder：记录压缩后估算字符数；如果没有这行，压缩效果无法验证。
        "max_messages": limits.max_messages,  # 新增代码+GuiContextBuilder：记录消息数预算；如果没有这行，事件无法解释为什么 compact。
        "max_chars": limits.max_chars,  # 新增代码+GuiContextBuilder：记录字符预算；如果没有这行，事件无法解释为什么 compact。
        "compacted": compacted,  # 新增代码+GuiContextBuilder：记录是否压缩；如果没有这行，GUI 无法显示 compact 发生状态。
        "reason": reason,  # 新增代码+GuiContextBuilder：记录 compact pipeline 原因；如果没有这行，排查时只能猜。
        "compact_generation": compact_generation,  # 新增代码+GuiContextBuilder：记录 compact 代次；如果没有这行，链式压缩不可审计。
    }  # 新增代码+GuiContextBuilder：payload 字典结束；如果没有这行，Python 语法不完整。
# 新增代码+GuiContextBuilder：函数段结束，_build_event_payload 到此结束；这段边界说明方便用户知道它负责脱敏事件。


def build_gui_context_for_turn(session_messages: Iterable[Any], current_prompt: str, session_id: str, run_id: str, turn_id: str, workspace: str | Path, max_messages: int | None = None, max_chars: int | None = None) -> GuiContextBuildResult:  # 新增代码+GuiContextBuilder：函数段开始，构建本轮 GUI 模型输入上下文；如果没有这段函数，GUI 会继续只把最后一句发给模型。
    limits = gui_context_limits_from_env()  # 新增代码+GuiContextBuilder：读取默认环境阈值；如果没有这行，builder 不支持真实 GUI 配置。
    if max_messages is not None:  # 新增代码+GuiContextBuilder：允许测试或调用方覆盖消息阈值；如果没有这行，自动化验收无法稳定触发 compact。
        limits.max_messages = max(MIN_GUI_CONTEXT_MAX_MESSAGES, int(max_messages))  # 新增代码+GuiContextBuilder：应用并保护最小消息阈值；如果没有这行，过小阈值会压掉当前 prompt。
    if max_chars is not None:  # 新增代码+GuiContextBuilder：允许测试或调用方覆盖字符阈值；如果没有这行，长文本验收不稳定。
        limits.max_chars = max(MIN_GUI_CONTEXT_MAX_CHARS, int(max_chars))  # 新增代码+GuiContextBuilder：应用并保护最小字符阈值；如果没有这行，错误阈值会导致持续压缩失败。
    normalized_messages = _normalize_session_messages(session_messages)  # 新增代码+GuiContextBuilder：把 GUI 历史转为 compact 消息；如果没有这行，历史上下文无法进入模型。
    input_messages = _ensure_current_prompt_once(normalized_messages, current_prompt, turn_id)  # 新增代码+GuiContextBuilder：保证当前 prompt exact-once；如果没有这行，本轮问题可能丢失或重复。
    task_state = TaskState.from_user_input(_safe_text(current_prompt), session_id=_safe_text(session_id), run_id=_safe_text(run_id))  # 新增代码+GuiContextBuilder：用当前 prompt 建立任务状态；如果没有这行，compact 可能围绕旧寒暄生成摘要。
    workspace_path = Path(workspace).expanduser().resolve()  # 新增代码+GuiContextBuilder：规范化 workspace；如果没有这行，artifact 路径可能相对错位。
    runtime_state = {  # 新增代码+GuiContextBuilder：准备传给 compact pipeline 的运行时状态；如果没有这段，现有 compact 模块拿不到阈值和身份信息。
        "compact_max_messages": limits.max_messages,  # 新增代码+GuiContextBuilder：传入消息数阈值；如果没有这行，pipeline 会使用默认阈值而忽略 GUI 配置。
        "compact_max_chars": limits.max_chars,  # 新增代码+GuiContextBuilder：传入字符数阈值；如果没有这行，pipeline 会使用默认阈值而忽略 GUI 配置。
        "session_id": _safe_text(session_id),  # 新增代码+GuiContextBuilder：传入 session id；如果没有这行，compact boundary 无法归属会话。
        "run_id": _safe_text(run_id),  # 新增代码+GuiContextBuilder：传入 run id；如果没有这行，compact boundary 无法归属运行。
        "turn_id": _safe_text(turn_id),  # 新增代码+GuiContextBuilder：传入 turn id；如果没有这行，compact boundary 无法归属轮次。
        "turn": len(input_messages),  # 新增代码+GuiContextBuilder：传入当前消息数量作为审计轮次；如果没有这行，compact 代次间隔不清楚。
        "artifact_dir": str(workspace_path / "memory" / "gui_context_compact"),  # 新增代码+GuiContextBuilder：传入 GUI compact artifact 目录；如果没有这行，压缩证据无法落盘。
    }  # 新增代码+GuiContextBuilder：runtime_state 字典结束；如果没有这行，Python 语法不完整。
    chars_before = estimate_messages_chars(input_messages)  # 新增代码+GuiContextBuilder：估算压缩前字符数；如果没有这行，事件无法显示输入规模。
    decision = prepare_messages_before_model(input_messages, task_state, runtime_state)  # 新增代码+GuiContextBuilder：调用现有 compact pipeline；如果没有这行，GUI 不会复用成熟上下文压缩模块。
    compact_messages = _fit_compact_messages_to_limit(decision.messages, limits.max_messages)  # 新增代码+GuiContextBuilder：把 pipeline 输出再贴合 GUI 消息预算；如果没有这行，post-compact restore 可能让请求仍超消息数。
    response_messages = compact_messages_to_responses_input(compact_messages)  # 新增代码+GuiContextBuilder：转换为 Responses input；如果没有这行，Direct SSE adapter 无法直接发送。
    chars_after = estimate_messages_chars(compact_messages)  # 新增代码+GuiContextBuilder：估算压缩后字符数；如果没有这行，事件无法显示压缩收益。
    event_payload = _build_event_payload(_safe_text(session_id), _safe_text(run_id), _safe_text(turn_id), limits, len(input_messages), len(response_messages), chars_before, chars_after, decision.compacted, decision.reason, decision.compact_generation)  # 新增代码+GuiContextBuilder：生成脱敏预算事件；如果没有这行，右侧状态栏无法显示 context_budget。
    return GuiContextBuildResult(messages=response_messages, compacted=decision.compacted, event_payload=event_payload, task_state_summary=_task_state_summary(task_state))  # 新增代码+GuiContextBuilder：返回完整构建结果；如果没有这行，bridge 拿不到模型输入和事件 payload。
# 新增代码+GuiContextBuilder：函数段结束，build_gui_context_for_turn 到此结束；这段边界说明方便用户知道它是 GUI 上下文构建总入口。


__all__ = ["GuiContextBuildResult", "GuiContextLimits", "build_gui_context_for_turn", "compact_messages_to_responses_input", "gui_context_limits_from_env", "responses_input_to_compact_messages"]  # 新增代码+GuiContextBuilder：声明公开 API；如果没有这行，后续维护者不清楚哪些函数可被 bridge/adapter 使用。
