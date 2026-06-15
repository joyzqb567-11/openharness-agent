"""OpenHarness 增强收束控制模块。"""  # 新增代码+ConvergenceController: 说明本文件负责重复工具、无进展和读日志恢复任务判断；如果没有这行代码，收束逻辑会散落在主循环。

from __future__ import annotations  # 新增代码+ConvergenceController: 延迟解析类型注解；如果没有这行代码，跨模块类型引用更容易受导入顺序影响。

import json  # 新增代码+ConvergenceController: 用稳定 JSON 生成工具调用签名；如果没有这行代码，重复工具判断容易受 dict 顺序影响。
import re  # 新增代码+SemanticReadLoop: 用正则从 bash 命令中提取被反复读取的文件路径；如果没有这行代码，换命令读同一文件的循环无法归一。
from dataclasses import dataclass  # 新增代码+ConvergenceController: 用数据类表达决策；如果没有这行代码，返回结构会散乱。
from typing import Any  # 新增代码+ConvergenceController: 标注工具调用和 runtime_state 宽松结构；如果没有这行代码，接口边界不清楚。

from learning_agent.core.task_state import TaskState  # 新增代码+ConvergenceController: 读取任务事实源；如果没有这行代码，收束提示无法引用原始目标和待办。
from learning_agent.core.actionability_state import get_pending_actionability, pending_actionability_argument_mismatch, pending_actionability_message, record_actionability_from_tool_result, should_block_tool_for_pending_actionability  # 修改代码+PendingArgumentGate：接入参数门禁；如果没有这一行，browser_type 用错 element_id 仍会真实执行。


REPEAT_TOOL_THRESHOLD = 3  # 新增代码+ConvergenceController: 同一工具同参数第 3 次开始视为重复风险；如果没有这行代码，重复工具阈值会散落。
SEMANTIC_FILE_READ_LOOP_THRESHOLD = 8  # 新增代码+SemanticReadLoop: 同一轮第 8 次读取同一文件时收束；如果没有这行代码，模型可通过换命令绕开重复签名判断。
RECOVERY_LOG_MARKERS = ("turns.json", "debug", "compact", "transcript", "events.jsonl", "runtime/events")  # 新增代码+ConvergenceController: 常见恢复日志/压缩产物标记；如果没有这行代码，读日志恢复任务无法识别。
LOG_DEBUG_INTENT_MARKERS = ("日志", "调试", "debug", "bug", "报错", "排查", "源码", "代码", "文件")  # 新增代码+ConvergenceController: 用户明确要查日志/代码时不拦截；如果没有这行代码，合法调试任务会被误挡。
READ_COMMAND_MARKERS = ("get-content", "select-string", "rg ", "grep ", "cat ", "type ", "read_text", "read-file", "read_file")  # 新增代码+SemanticReadLoop: 定义 bash 中常见读文件动作；如果没有这行代码，无法区分读取和普通命令。
WRITE_COMMAND_MARKERS = ("set-content", "out-file", "add-content", "write_text", "write-file", "write_file", ">>", " tee ")  # 新增代码+SemanticReadLoop: 定义 bash 中常见写文件动作；如果没有这行代码，写入后仍可能被误算成读循环。
SOURCE_FILE_PATTERN = re.compile(r"(?i)(?:[A-Za-z]:[\\/][^\s'\";|)]+|(?:\.?[\\/])?[\w./\\-]+\.(?:js|jsx|ts|tsx|py|html|css|json|md))")  # 修改代码+SemanticReadLoop: 修正路径正则的过度转义，让 `src/main.js` 这类相对路径可被提取；如果没有这行代码，换命令读同一文件仍无法归一。


@dataclass  # 新增代码+ConvergenceController: 自动生成工具决策初始化方法；如果没有这行代码，需要手写样板。
class ToolCallDecision:  # 新增代码+ConvergenceController: 类段开始，表示一个工具调用是否执行真实工具；如果没有这个类，agent.py 难以区分真实执行和合成收束信号。
    execute_real_tool: bool  # 新增代码+ConvergenceController: 标记是否执行真实工具；如果没有这行代码，主循环无法阻断重复工具。
    synthetic_output: str | None  # 新增代码+ConvergenceController: 保存合成工具结果；如果没有这行代码，被阻断的 tool_call 无法闭合协议。
    injected_message: dict[str, str] | None  # 新增代码+ConvergenceController: 保存可选注入消息；如果没有这行代码，模型收不到收束建议。
    reason: str  # 新增代码+ConvergenceController: 保存决策原因；如果没有这行代码，审计无法解释为什么阻断或放行。
    signature: str = ""  # 新增代码+ConvergenceController: 保存工具调用签名；如果没有这行代码，重复判断证据不可见。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+ConvergenceController: 函数段开始，把工具决策转成 JSON；如果没有这段函数，事件 payload 会重复拼。
        return {  # 新增代码+ConvergenceController: 返回结构化字段；如果没有这行代码，调用方拿不到完整 payload。
            "execute_real_tool": self.execute_real_tool,  # 新增代码+ConvergenceController: 写出是否真实执行；如果没有这行代码，事件不完整。
            "synthetic_output": self.synthetic_output,  # 新增代码+ConvergenceController: 写出合成结果；如果没有这行代码，阻断内容不可见。
            "injected_message": dict(self.injected_message) if self.injected_message is not None else None,  # 新增代码+ConvergenceController: 写出注入消息；如果没有这行代码，模型提示不可审计。
            "reason": self.reason,  # 新增代码+ConvergenceController: 写出原因；如果没有这行代码，debug 不可解释。
            "signature": self.signature,  # 新增代码+ConvergenceController: 写出签名；如果没有这行代码，重复工具判断无法复核。
        }  # 新增代码+ConvergenceController: 结束字典返回；如果没有这行代码，Python 字典语法不完整。


@dataclass  # 新增代码+ConvergenceController: 自动生成模型前评估对象；如果没有这行代码，调用方要手写样板。
class ConvergenceAssessment:  # 新增代码+ConvergenceController: 类段开始，表示模型调用前是否要注入收束提醒；如果没有这个类，agent.py 会继续散落提示逻辑。
    should_inject_message: bool  # 新增代码+ConvergenceController: 标记是否注入消息；如果没有这行代码，主循环不知道是否追加上下文。
    injected_message: dict[str, str] | None  # 新增代码+ConvergenceController: 保存注入消息；如果没有这行代码，模型收不到收束提醒。
    reason: str  # 新增代码+ConvergenceController: 保存原因；如果没有这行代码，状态事件无法解释注入。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+ConvergenceController: 函数段开始，把评估转成 JSON；如果没有这段函数，事件 payload 会重复拼。
        return {  # 新增代码+ConvergenceController: 返回评估字段；如果没有这行代码，调用方拿不到结构化信息。
            "should_inject_message": self.should_inject_message,  # 新增代码+ConvergenceController: 写出是否注入；如果没有这行代码，事件不完整。
            "injected_message": dict(self.injected_message) if self.injected_message is not None else None,  # 新增代码+ConvergenceController: 写出注入消息；如果没有这行代码，提示内容不可见。
            "reason": self.reason,  # 新增代码+ConvergenceController: 写出原因；如果没有这行代码，debug 无解释。
        }  # 新增代码+ConvergenceController: 结束字典返回；如果没有这行代码，Python 字典语法不完整。


def _runtime_dict(runtime_state: dict[str, Any] | None) -> dict[str, Any]:  # 新增代码+ConvergenceController: 函数段开始，确保 runtime_state 可读写；如果没有这段函数，None 输入会崩溃。
    return runtime_state if isinstance(runtime_state, dict) else {}  # 新增代码+ConvergenceController: 非 dict 返回空字典；如果没有这行代码，后续 get/set 会失败。


def _tool_name(tool_call: Any) -> str:  # 新增代码+ConvergenceController: 函数段开始，安全提取工具名；如果没有这段函数，不同 ToolCall 形态会重复处理。
    if isinstance(tool_call, dict):  # 新增代码+ConvergenceController: 支持 dict 形态工具调用；如果没有这行代码，测试和部分适配器会失败。
        return str(tool_call.get("name", "") or "")  # 新增代码+ConvergenceController: 从 dict 读取 name；如果没有这行代码，dict 工具签名缺工具名。
    return str(getattr(tool_call, "name", "") or "")  # 新增代码+ConvergenceController: 从对象读取 name；如果没有这行代码，ModelMessage ToolCall 无法签名。


def _tool_arguments(tool_call: Any) -> Any:  # 新增代码+ConvergenceController: 函数段开始，安全提取工具参数；如果没有这段函数，重复判断缺少参数。
    if isinstance(tool_call, dict):  # 新增代码+ConvergenceController: 支持 dict 工具调用；如果没有这行代码，测试工具对象会失败。
        return tool_call.get("arguments", {})  # 新增代码+ConvergenceController: 从 dict 读取参数；如果没有这行代码，签名会丢参数。
    return getattr(tool_call, "arguments", {})  # 新增代码+ConvergenceController: 从对象读取参数；如果没有这行代码，ToolCall 对象无法签名。


def _tool_signature(tool_call: Any) -> str:  # 新增代码+ConvergenceController: 函数段开始，生成稳定工具调用签名；如果没有这段函数，重复工具无法识别。
    name = _tool_name(tool_call)  # 新增代码+ConvergenceController: 提取工具名；如果没有这行代码，签名缺少核心字段。
    arguments = _tool_arguments(tool_call)  # 新增代码+ConvergenceController: 提取参数；如果没有这行代码，同工具不同参数会被误判。
    try:  # 新增代码+ConvergenceController: 尝试 JSON 排序序列化；如果没有这行代码，dict 顺序会影响签名。
        argument_text = json.dumps(arguments, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+ConvergenceController: 生成稳定参数文本；如果没有这行代码，重复判断不稳定。
    except TypeError:  # 新增代码+ConvergenceController: 处理无法 JSON 化的参数；如果没有这行代码，复杂参数会让收束器崩溃。
        argument_text = str(arguments)  # 新增代码+ConvergenceController: 回退为字符串；如果没有这行代码，坏参数没有签名。
    return f"{name}:{argument_text}"  # 新增代码+ConvergenceController: 返回工具名加参数签名；如果没有这行代码，调用方拿不到重复键。


def _argument_text(tool_call: Any) -> str:  # 新增代码+SemanticReadLoop: 函数段开始，把工具参数转成可搜索文本；如果没有这段函数，多处要重复处理 JSON 失败情况。
    try:  # 新增代码+SemanticReadLoop: 优先使用 JSON 序列化参数；如果没有这行代码，dict 参数顺序和嵌套结构难以统一。
        return json.dumps(_tool_arguments(tool_call), ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+SemanticReadLoop: 返回稳定参数文本；如果没有这行代码，路径提取容易漏掉 dict 中的值。
    except TypeError:  # 新增代码+SemanticReadLoop: 处理无法 JSON 化的参数；如果没有这行代码，复杂参数会让收束判断崩溃。
        return str(_tool_arguments(tool_call))  # 新增代码+SemanticReadLoop: 回退到普通字符串；如果没有这行代码，坏参数没有可分析文本。


def _normalized_path_marker(raw_path: str) -> str:  # 新增代码+SemanticReadLoop: 函数段开始，归一化不同写法的文件路径；如果没有这段函数，`src/main.js` 和 `.\\src\\main.js` 会被当成不同文件。
    path = raw_path.strip().strip("'\"`")  # 新增代码+SemanticReadLoop: 去掉命令中常见引号；如果没有这行代码，同一路径会因为引号不同而分裂。
    path = path.replace("\\", "/")  # 新增代码+SemanticReadLoop: 统一 Windows 和 POSIX 分隔符；如果没有这行代码，反斜杠路径无法和斜杠路径合并。
    while "//" in path:  # 修改代码+SemanticReadLoop: 合并重复斜杠；如果没有这行代码，`.\\src\\main.js` 可能变成 `src//main.js` 而绕过同文件计数。
        path = path.replace("//", "/")  # 修改代码+SemanticReadLoop: 每次压缩一组重复斜杠；如果没有这行代码，循环不会推进到稳定路径。
    while path.startswith("./"):  # 新增代码+SemanticReadLoop: 移除相对路径前缀；如果没有这行代码，`./src/main.js` 会绕过同文件计数。
        path = path[2:]  # 新增代码+SemanticReadLoop: 删除一个 `./` 前缀；如果没有这行代码，循环不会推进。
    while path.startswith("/"):  # 修改代码+SemanticReadLoop: 移除误捕获出的开头斜杠；如果没有这行代码，`/src/main.js` 会和 `src/main.js` 分裂。
        path = path[1:]  # 修改代码+SemanticReadLoop: 删除一个开头斜杠；如果没有这行代码，循环不会推进。
    lowered = path.lower()  # 新增代码+SemanticReadLoop: 转小写用于跨大小写比较；如果没有这行代码，Windows 上大小写差异会绕过计数。
    marker = lowered.split("/learning_agent/")[-1]  # 新增代码+SemanticReadLoop: 去掉工作区绝对路径前缀；如果没有这行代码，绝对路径和相对路径无法合并。
    return marker  # 新增代码+SemanticReadLoop: 返回归一化路径；如果没有这行代码，调用方拿不到语义桶键。


def _candidate_paths_from_text(text: str) -> list[str]:  # 新增代码+SemanticReadLoop: 函数段开始，从命令文本中提取候选文件路径；如果没有这段函数，bash 换壳读取无法识别同一文件。
    return [_normalized_path_marker(match.group(0)) for match in SOURCE_FILE_PATTERN.finditer(text or "")]  # 新增代码+SemanticReadLoop: 返回所有归一化路径；如果没有这行代码，路径提取结果不会传给计数器。


def _tool_is_write_like(tool_call: Any) -> bool:  # 新增代码+SemanticReadLoop: 函数段开始，判断工具是否明显在写文件；如果没有这段函数，写入后的合法复查可能被旧读计数误伤。
    name = _tool_name(tool_call).lower()  # 新增代码+SemanticReadLoop: 读取小写工具名；如果没有这行代码，大小写差异会影响判断。
    if name in {"write", "edit", "write_file"}:  # 新增代码+SemanticReadLoop: 原子写/编辑工具直接视为写入；如果没有这行代码，真实修改后读计数不会重置。
        return True  # 新增代码+SemanticReadLoop: 返回写入工具；如果没有这行代码，调用方无法重置语义读循环。
    if name != "bash":  # 新增代码+SemanticReadLoop: 非 bash 且非写工具不按命令文本判断；如果没有这行代码，读工具会被误扫写标记。
        return False  # 新增代码+SemanticReadLoop: 返回非写入；如果没有这行代码，普通工具可能被误重置。
    text = _argument_text(tool_call).lower()  # 新增代码+SemanticReadLoop: 读取 bash 参数文本；如果没有这行代码，无法识别 Set-Content/write_text 等写入动作。
    return any(marker in text for marker in WRITE_COMMAND_MARKERS)  # 新增代码+SemanticReadLoop: 命中写入标记即视为写入；如果没有这行代码，bash 写文件后仍可能沿用旧读计数。


def _semantic_file_read_key(tool_call: Any) -> str | None:  # 新增代码+SemanticReadLoop: 函数段开始，把“读同一文件”的不同命令归到同一个桶；如果没有这段函数，真实失败中的换命令循环会漏过。
    name = _tool_name(tool_call).lower()  # 新增代码+SemanticReadLoop: 读取小写工具名；如果没有这行代码，工具名大小写会影响判断。
    text = _argument_text(tool_call)  # 新增代码+SemanticReadLoop: 读取参数文本；如果没有这行代码，无法从 path/command 中提取文件。
    lowered = text.lower()  # 新增代码+SemanticReadLoop: 转小写做动作标记匹配；如果没有这行代码，PowerShell 命令大小写会影响判断。
    if _tool_is_write_like(tool_call):  # 新增代码+SemanticReadLoop: 写入动作不参与读循环计数；如果没有这行代码，修复代码本身可能被误挡。
        return None  # 新增代码+SemanticReadLoop: 写入工具没有读循环键；如果没有这行代码，调用方会错误累加。
    if name in {"read", "read_file"}:  # 新增代码+SemanticReadLoop: 原子读取工具按路径参数归桶；如果没有这行代码，read 换参数形态也可能绕过。
        paths = _candidate_paths_from_text(text)  # 新增代码+SemanticReadLoop: 从 read 参数中提取路径；如果没有这行代码，read 工具无法形成语义键。
    elif name == "bash" and any(marker in lowered for marker in READ_COMMAND_MARKERS):  # 新增代码+SemanticReadLoop: bash 中含读文件标记才归桶；如果没有这行代码，普通命令会被误算成读循环。
        paths = _candidate_paths_from_text(text)  # 新增代码+SemanticReadLoop: 从 bash 命令中提取路径；如果没有这行代码，Select-String/Get-Content 无法归一。
    else:  # 新增代码+SemanticReadLoop: 其他工具不参与语义读循环；如果没有这行代码，浏览器和计算类工具可能被误挡。
        return None  # 新增代码+SemanticReadLoop: 返回无语义键；如果没有这行代码，调用方无法区分不适用场景。
    if not paths:  # 新增代码+SemanticReadLoop: 没有提取到路径时不阻断；如果没有这行代码，无路径命令可能被错误归到空桶。
        return None  # 新增代码+SemanticReadLoop: 返回无语义键；如果没有这行代码，空路径会造成误判。
    return f"file_read:{paths[0]}"  # 新增代码+SemanticReadLoop: 使用第一个源码路径作为同文件读取桶；如果没有这行代码，调用方拿不到可累加的语义签名。


def _system_message(content: str) -> dict[str, str]:  # 新增代码+ConvergenceController: 函数段开始，构造模型可见提示；如果没有这段函数，注入消息格式会重复。
    return {"role": "system", "content": content}  # 新增代码+ConvergenceController: 返回 system 消息；如果没有这行代码，主循环无法追加提示。


def _mentions_recovery_log(tool_call: Any) -> bool:  # 新增代码+ConvergenceController: 函数段开始，识别工具是否在读恢复日志/compact artifact；如果没有这段函数，读日志恢复任务循环无法发现。
    text = f"{_tool_name(tool_call)} {json.dumps(_tool_arguments(tool_call), ensure_ascii=False, default=str)}".lower()  # 新增代码+ConvergenceController: 拼接工具名和参数文本；如果没有这行代码，路径标记无法统一匹配。
    return any(marker in text for marker in RECOVERY_LOG_MARKERS)  # 新增代码+ConvergenceController: 命中任一恢复日志标记就返回 true；如果没有这行代码，日志恢复循环不会被识别。


def _user_asked_for_debug_artifacts(task_state: TaskState) -> bool:  # 新增代码+ConvergenceController: 函数段开始，判断用户是否明确要求查日志/代码；如果没有这段函数，合法调试任务会被误拦截。
    text = f"{task_state.original_user_request} {task_state.latest_user_input}".lower()  # 新增代码+ConvergenceController: 合并用户原始和最新输入；如果没有这行代码，只看单轮容易漏掉补充要求。
    return any(marker.lower() in text for marker in LOG_DEBUG_INTENT_MARKERS)  # 新增代码+ConvergenceController: 命中调试意图就放行；如果没有这行代码，源码分析任务会被误挡。


def assess_before_model(task_state: TaskState, recent_messages: list[dict[str, Any]], runtime_state: dict[str, Any] | None = None) -> ConvergenceAssessment:  # 新增代码+ConvergenceController: 函数段开始，模型调用前评估是否需要收束提醒；如果没有这段函数，主循环无法提前注入任务状态。
    state = _runtime_dict(runtime_state)  # 新增代码+ConvergenceController: 取得运行时状态；如果没有这行代码，评估无法读取重复计数。
    pending_actionability = get_pending_actionability(state)  # 新增代码+ObservePlanActVerify：读取当前必须先完成的真实动作；如果没有这一行，模型可能在有可操作目标时直接最终回答。
    if pending_actionability and not _user_asked_for_debug_artifacts(task_state):  # 新增代码+ObservePlanActVerify：非调试任务中存在 pending 时优先要求执行动作；如果没有这一行，S7 R3 会从真实动作漂移到读日志。
        message = _system_message(f"收束提醒：当前已经识别到可真实操作的目标，请先完成 pending 指定的下一步工具调用，不要改为读取日志或写本地替代结果。\n{pending_actionability_message(pending_actionability)}\n{task_state.to_model_summary()}")  # 新增代码+ObservePlanActVerify：把下一步工具和任务状态注入模型；如果没有这一行，模型不知道具体该调用 computer_observe 还是 browser_type。
        return ConvergenceAssessment(True, message, "pending_actionability_requires_tool")  # 新增代码+ObservePlanActVerify：返回需要注入的评估结果；如果没有这一行，主循环不会收到纠偏提示。
    if bool(state.get("convergence_goal_evidence_sufficient", False)):  # 新增代码+ConvergenceController: 如果外部已标记证据足够；如果没有这行代码，agent 可能继续查证而不回答。
        message = _system_message(f"收束提醒：当前证据已经足够，请围绕原始目标输出最终回答。\n{task_state.to_model_summary()}")  # 新增代码+ConvergenceController: 注入最终回答提醒；如果没有这行代码，模型不知道该整理答案。
        return ConvergenceAssessment(True, message, "goal_evidence_sufficient")  # 新增代码+ConvergenceController: 返回注入评估；如果没有这行代码，调用方不知道要追加消息。
    if recent_messages and "Compact Summary" in str(recent_messages[-1].get("content", "")) and task_state.original_user_request:  # 新增代码+ConvergenceController: 如果尾部仍是旧 compact 摘要且 TaskState 有目标；如果没有这行代码，模型可能继续读旧摘要恢复任务。
        message = _system_message(f"收束提醒：不要依赖旧 Compact Summary 恢复任务，请使用 TaskState。\n{task_state.to_model_summary()}")  # 新增代码+ConvergenceController: 注入 TaskState 提醒；如果没有这行代码，压缩后恢复可能继续跑偏。
        return ConvergenceAssessment(True, message, "use_task_state_after_compact")  # 新增代码+ConvergenceController: 返回注入评估；如果没有这行代码，主循环不知道提醒原因。
    return ConvergenceAssessment(False, None, "no_convergence_injection_needed")  # 新增代码+ConvergenceController: 默认不注入；如果没有这行代码，模型每轮都会被无意义提示干扰。


def decide_tool_call(tool_call: Any, task_state: TaskState, runtime_state: dict[str, Any] | None = None) -> ToolCallDecision:  # 新增代码+ConvergenceController: 函数段开始，判断一个工具调用是否真实执行；如果没有这段函数，重复工具无法被收束。
    state = _runtime_dict(runtime_state)  # 新增代码+ConvergenceController: 取得可写运行时状态；如果没有这行代码，重复计数无法保存。
    signature = _tool_signature(tool_call)  # 新增代码+ConvergenceController: 生成工具调用签名；如果没有这行代码，无法识别同工具同参数。
    counts = state.setdefault("convergence_tool_signature_counts", {})  # 新增代码+ConvergenceController: 取得或创建签名计数字典；如果没有这行代码，重复计数无处存放。
    current_count = int(counts.get(signature, 0)) + 1  # 新增代码+ConvergenceController: 计算本次是第几次调用；如果没有这行代码，无法判断重复阈值。
    counts[signature] = current_count  # 新增代码+ConvergenceController: 写回调用次数；如果没有这行代码，下一轮无法看到历史。
    pending_actionability = get_pending_actionability(state)  # 新增代码+ObservePlanActVerify：读取工具调用前的下一步动作要求；如果没有这一行，控制器无法判断本次工具是否绕过真实动作。
    tool_call_text = _argument_text(tool_call)  # 新增代码+ObservePlanActVerify：把工具参数转成文本供绕行识别；如果没有这一行，bash 读 snapshot 日志无法被识别。
    argument_mismatch = pending_actionability_argument_mismatch(_tool_name(tool_call), _tool_arguments(tool_call), pending_actionability)  # 新增代码+PendingArgumentGate：检查正确工具是否带错 page_id/element_id/target_ref；如果没有这一行，模型会把错误元素当作完成路径。
    if argument_mismatch:  # 新增代码+PendingArgumentGate：发现参数不吻合时不执行真实工具；如果没有这行代码，错误输入会打到用户真实浏览器页面。
        output = f"{pending_actionability_message(pending_actionability)}\n当前工具调用已被阻断，因为它使用的关键参数与 pending 不一致：{argument_mismatch}\n{task_state.to_model_summary()}"  # 新增代码+PendingArgumentGate：构造合成工具结果闭合 tool_call；如果没有这一行，模型不知道必须换成 pending 参数。
        message = _system_message("收束提醒：你调用了正确工具，但 page_id、element_id、target_ref 或 action 与 pending 不一致。请使用 pending 里给出的参数重新调用，不要继续提交、等待、读日志或写 fallback。")  # 新增代码+PendingArgumentGate：注入模型可见纠偏消息；如果没有这一行，模型可能继续用旧 element_id。
        return ToolCallDecision(False, output, message, "pending_actionability_argument_mismatch", signature)  # 新增代码+PendingArgumentGate：返回参数不匹配阻断决策；如果没有这一行，主循环会继续执行错误工具。
    if should_block_tool_for_pending_actionability(_tool_name(tool_call), tool_call_text, pending_actionability, _user_asked_for_debug_artifacts(task_state)):  # 新增代码+ObservePlanActVerify：在 pending 存在时阻断读日志/写 fallback 等绕行动作；如果没有这一行，真实浏览器候选出现后仍会回到日志分析。
        output = f"{pending_actionability_message(pending_actionability)}\n当前工具调用已被阻断，因为它没有完成 pending 指定的真实动作。\n{task_state.to_model_summary()}"  # 新增代码+ObservePlanActVerify：构造合成工具结果闭合 tool_call；如果没有这一行，被阻断调用没有可读反馈。
        message = _system_message("收束提醒：请立刻调用 pending.next_required_tool 指定的真实工具，并使用 pending 里的 page_id、element_id、target_ref 或 next_required_action 参数。")  # 新增代码+ObservePlanActVerify：构造模型可见纠偏消息；如果没有这一行，模型可能继续换一种方式绕行。
        return ToolCallDecision(False, output, message, "pending_actionability_tool_required", signature)  # 新增代码+ObservePlanActVerify：返回阻断决策；如果没有这一行，绕行工具仍会真实执行。
    if current_count >= REPEAT_TOOL_THRESHOLD:  # 新增代码+ConvergenceController: 同签名重复达到阈值时阻断；如果没有这行代码，模型可能无限查同一页/同一日志。
        output = f"convergence_controller: 已阻断重复工具调用。工具签名已连续出现 {current_count} 次，建议基于已有证据整理最终回答，而不是继续重复同一工具。\n{task_state.to_model_summary()}"  # 新增代码+ConvergenceController: 构造合成工具结果闭合 tool_call；如果没有这行代码，协议里会缺工具输出。
        message = _system_message("收束提醒：刚才的工具调用被判定为重复且无新增收益，请基于已有任务状态输出最终回答或明确说明缺哪项关键证据。")  # 新增代码+ConvergenceController: 构造模型可见收束提示；如果没有这行代码，模型可能继续换方式重复。
        return ToolCallDecision(False, output, message, "repeated_tool_call_blocked", signature)  # 新增代码+ConvergenceController: 返回阻断决策；如果没有这行代码，主循环会继续执行重复工具。
    if _tool_is_write_like(tool_call):  # 新增代码+SemanticReadLoop: 遇到真实写入/编辑时清空同文件读取计数；如果没有这行代码，修复后复查文件可能被误挡。
        state["convergence_semantic_file_read_counts"] = {}  # 新增代码+SemanticReadLoop: 重置语义读计数；如果没有这行代码，新一轮读取会继承写入前的旧疲劳度。
        return ToolCallDecision(True, None, None, "execute_real_tool", signature)  # 新增代码+SemanticReadLoop: 写入动作直接放行；如果没有这行代码，模型无法真正修复文件。
    semantic_key = _semantic_file_read_key(tool_call)  # 新增代码+SemanticReadLoop: 计算同文件语义读取键；如果没有这行代码，换命令读同一文件不会被计数。
    if semantic_key is not None:  # 新增代码+SemanticReadLoop: 只有读文件工具才进入语义循环判断；如果没有这行代码，普通工具会被误挡。
        semantic_counts = state.setdefault("convergence_semantic_file_read_counts", {})  # 新增代码+SemanticReadLoop: 取得语义读取计数字典；如果没有这行代码，跨工具调用无法累加。
        semantic_count = int(semantic_counts.get(semantic_key, 0)) + 1  # 新增代码+SemanticReadLoop: 计算同一文件第几次读取；如果没有这行代码，无法触发阈值。
        semantic_counts[semantic_key] = semantic_count  # 新增代码+SemanticReadLoop: 写回同文件读取次数；如果没有这行代码，下一次仍看不到历史。
        if semantic_count >= SEMANTIC_FILE_READ_LOOP_THRESHOLD:  # 新增代码+SemanticReadLoop: 达到同文件读取阈值时阻断；如果没有这行代码，模型可无限换读法继续消耗上下文。
            output = f"convergence_controller: 已阻断同一文件的语义重复读取。文件读取键 {semantic_key} 已出现 {semantic_count} 次；请基于已有证据直接修改代码或输出结论，不要继续换命令读取同一文件。\n{task_state.to_model_summary()}"  # 新增代码+SemanticReadLoop: 构造合成工具结果；如果没有这行代码，模型不知道已有证据足够。
            message = _system_message("收束提醒：同一文件已经被多次读取且仍未产生修改，请停止继续读取同一文件，直接执行必要的 edit/write，或基于已有证据回答。")  # 新增代码+SemanticReadLoop: 注入模型可见提示；如果没有这行代码，模型可能继续请求相似读取。
            return ToolCallDecision(False, output, message, "semantic_file_read_loop_blocked", semantic_key)  # 新增代码+SemanticReadLoop: 返回语义读循环阻断；如果没有这行代码，真实验收第 8 轮会复发卡死。
    if current_count >= 2 and _mentions_recovery_log(tool_call) and not _user_asked_for_debug_artifacts(task_state):  # 新增代码+ConvergenceController: 第二次起反复读日志且用户没要求调试时阻断；如果没有这行代码，压缩后读日志恢复任务会循环。
        output = f"convergence_controller: 已阻断重复读取日志/compact artifact 来恢复任务。TaskState 已保存原始目标和下一步，请直接使用它继续。\n{task_state.to_model_summary()}"  # 新增代码+ConvergenceController: 构造合成工具结果；如果没有这行代码，被阻断 tool_call 无法闭合。
        message = _system_message("收束提醒：不要继续读取旧日志恢复任务，请直接依据 TaskState 完成用户目标。")  # 新增代码+ConvergenceController: 构造 TaskState 收束提示；如果没有这行代码，模型不知道为何停止读日志。
        return ToolCallDecision(False, output, message, "task_state_recovery_log_loop_blocked", signature)  # 新增代码+ConvergenceController: 返回阻断决策；如果没有这行代码，日志恢复循环会继续。
    return ToolCallDecision(True, None, None, "execute_real_tool", signature)  # 新增代码+ConvergenceController: 默认放行真实工具；如果没有这行代码，正常工具调用会被误挡。


def record_tool_result(tool_call: Any, output_text: str, task_state: TaskState, runtime_state: dict[str, Any] | None = None) -> None:  # 新增代码+ConvergenceController: 函数段开始，记录工具结果用于后续无进展判断；如果没有这段函数，收束器只能看调用不能看结果。
    state = _runtime_dict(runtime_state)  # 新增代码+ConvergenceController: 取得运行时状态；如果没有这行代码，结果指纹无法保存。
    signature = _tool_signature(tool_call)  # 新增代码+ConvergenceController: 生成工具签名；如果没有这行代码，结果无法和调用关联。
    record_actionability_from_tool_result(_tool_name(tool_call), output_text, state)  # 新增代码+ObservePlanActVerify：从工具输出里沉淀下一步动作状态；如果没有这一行，browser_snapshot/computer_action 的 marker 不会影响下一轮决策。
    output_preview = str(output_text or "")[:500]  # 新增代码+ConvergenceController: 截取结果预览；如果没有这行代码，巨大工具结果会撑大 runtime_state。
    state.setdefault("convergence_tool_result_previews", {})[signature] = output_preview  # 新增代码+ConvergenceController: 保存最近结果预览；如果没有这行代码，后续无法比较工具收益。
    if output_preview and output_preview not in "；".join(task_state.evidence_summaries):  # 新增代码+ConvergenceController: 新预览未进入证据摘要时补充；如果没有这行代码，TaskState 不会吸收关键工具证据。
        task_state.add_evidence_summary(output_preview[:160])  # 新增代码+ConvergenceController: 追加短证据摘要；如果没有这行代码，compact 后模型可能又去查同一证据。


__all__ = ["ConvergenceAssessment", "ToolCallDecision", "assess_before_model", "decide_tool_call", "record_tool_result"]  # 新增代码+ConvergenceController: 明确公开接口；如果没有这行代码，其他模块导入边界不清。
