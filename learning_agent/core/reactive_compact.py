"""模型报错后的 reactive compact 恢复模块。"""  # 新增代码+ReactiveCompact: 说明这个文件专门处理 prompt too long 后的自动压缩重试；如果没有这行，维护者不知道异常恢复入口在哪里。

from __future__ import annotations  # 新增代码+ReactiveCompact: 延迟解析类型注解；如果没有这行，自引用或较新类型写法在部分环境更容易出问题。

from dataclasses import dataclass  # 新增代码+ReactiveCompact: 用 dataclass 表达恢复结果；如果没有这行，调用方只能读散乱 dict。
from pathlib import Path  # 新增代码+ReactiveCompact: 支持 artifact_dir 使用 Windows 路径；如果没有这行，落盘目录处理会不稳定。
from typing import Any  # 新增代码+ReactiveCompact: 标注消息这种 JSON 式结构；如果没有这行，接口输入输出不清楚。

from learning_agent.core.compact import CompactBoundary, compact_messages_with_boundary  # 新增代码+ReactiveCompact: 复用主 compact 能力生成可审计边界；如果没有这行，reactive 恢复会变成旁路裁剪。
from learning_agent.core.task_state import TaskState  # 新增代码+ContextCompactRepair: 引入任务状态用于 reactive compact；如果没有这行，上下文超限恢复仍可能丢目标。


@dataclass  # 新增代码+ReactiveCompact: 自动生成结果对象构造器；如果没有这行，需要写很多样板代码。
class ReactiveCompactResult:  # 新增代码+ReactiveCompact: 表示一次 reactive compact 的决策结果；如果没有这个类，主循环无法清楚知道是否该重试。
    should_retry: bool  # 新增代码+ReactiveCompact: 告诉主循环是否可以再请求一次模型；如果没有这行，agent 可能无限失败或直接放弃。
    messages: list[dict[str, Any]]  # 新增代码+ReactiveCompact: 保存压缩后的模型消息；如果没有这行，重试时仍会使用过长上下文。
    boundary: CompactBoundary | None  # 新增代码+ReactiveCompact: 保存本次压缩边界；如果没有这行，异常恢复无法被 transcript 审计。
    transition_reason: str  # 新增代码+ReactiveCompact: 保存状态转换原因；如果没有这行，状态生态无法解释为什么重试。
    blocked_reason: str = ""  # 新增代码+ReactiveCompact: 保存不能重试的原因；如果没有这行，失败时用户只看到模糊错误。


def _error_text(error: BaseException | str) -> str:  # 新增代码+ReactiveCompact: 统一把异常或字符串转成小写文本；如果没有这行，错误识别逻辑会重复。
    return str(error).lower()  # 新增代码+ReactiveCompact: 返回小写错误文本；如果没有这行，大小写差异会导致关键词漏判。


def is_prompt_too_long_error(error: BaseException | str) -> bool:  # 新增代码+ReactiveCompact: 判断是否是上下文过长错误；如果没有这行，agent 不能针对 prompt too long 自动恢复。
    text = _error_text(error)  # 新增代码+ReactiveCompact: 提取标准化错误文本；如果没有这行，后续关键词判断没有输入。
    markers = ("prompt too long", "context length", "context_length_exceeded", "maximum context", "too many tokens", "token limit")  # 新增代码+ReactiveCompact: 覆盖常见模型上下文超限表达；如果没有这行，很多真实报错不会触发恢复。
    return any(marker in text for marker in markers)  # 新增代码+ReactiveCompact: 任一关键词命中就认为可 reactive compact；如果没有这行，函数永远不能给出判断。


def is_media_too_large_error(error: BaseException | str) -> bool:  # 新增代码+ReactiveCompact: 判断是否是媒体输入过大错误；如果没有这行，未来图片/文件超限无法进入明确分支。
    text = _error_text(error)  # 新增代码+ReactiveCompact: 提取标准化错误文本；如果没有这行，关键词判断没有输入。
    markers = ("image too large", "media too large", "file too large", "payload too large", "request entity too large")  # 新增代码+ReactiveCompact: 覆盖常见媒体或请求体过大表达；如果没有这行，错误分类会太窄。
    return any(marker in text for marker in markers)  # 新增代码+ReactiveCompact: 任一关键词命中就返回 true；如果没有这行，媒体超限无法识别。


def try_reactive_compact(messages: list[dict[str, Any]], session_id: str, run_id: str, turn_id: str, has_attempted: bool, artifact_dir: str | Path | None = None, task_state: TaskState | None = None, recent_runtime_state: dict[str, Any] | None = None, compact_generation: int | None = None, turns_since_previous_compact: int = 0) -> ReactiveCompactResult:  # 修改代码+ContextCompactRepair: 扩展 reactive compact 接收任务状态和恢复状态；如果没有这行，超限恢复会绕开新 compact 质量闭环。
    if has_attempted:  # 新增代码+ReactiveCompact: 防止同一轮无限 reactive compact；如果没有这行，模型持续报错时 agent 可能卡死循环。
        return ReactiveCompactResult(False, messages, None, "reactive_compact_blocked", "reactive_compact_already_attempted")  # 新增代码+ReactiveCompact: 返回不可重试并说明原因；如果没有这行，调用方不知道为什么停止。
    compacted_messages, boundary = compact_messages_with_boundary(messages, session_id=session_id, run_id=run_id, turn_id=turn_id, max_messages=8, reason="reactive_prompt_too_long", artifact_dir=artifact_dir, task_state=task_state, recent_runtime_state=recent_runtime_state, compact_generation=compact_generation, is_recompaction_in_chain=True, turns_since_previous_compact=turns_since_previous_compact)  # 修改代码+ContextCompactRepair: 调用结构化 compact 生成更短上下文；如果没有这行，重试仍会丢任务目标或恢复附件。
    return ReactiveCompactResult(True, compacted_messages, boundary, "reactive_compact_retry")  # 新增代码+ReactiveCompact: 告诉主循环可以用压缩后的消息重试一次；如果没有这行，恢复路径不会继续执行。
