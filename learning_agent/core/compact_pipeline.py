"""compact 流水线控制模块。"""  # 新增代码+CompactPipeline: 说明本文件统一管理 compact 触发、代次和熔断；如果没有这行代码，维护者不知道这里是压缩编排入口。

from __future__ import annotations  # 新增代码+CompactPipeline: 延迟解析类型注解；如果没有这行代码，跨模块类型引用更容易受导入顺序影响。

from dataclasses import dataclass, field  # 新增代码+CompactPipeline: 用数据类表达流水线决策；如果没有这行代码，返回值会变成散乱 dict。
from pathlib import Path  # 新增代码+CompactPipeline: 支持 artifact_dir 使用 Windows 路径；如果没有这行代码，压缩产物路径处理不稳定。
from typing import Any  # 新增代码+CompactPipeline: 标注 runtime_state 这类宽松 JSON；如果没有这行代码，接口边界不清楚。

from learning_agent.core.compact import CompactBoundary, compact_messages_with_boundary, should_compact_messages  # 新增代码+CompactPipeline: 复用底层 compact 能力和触发判断；如果没有这行代码，流水线会重复实现压缩。
from learning_agent.core.reactive_compact import is_prompt_too_long_error, try_reactive_compact  # 新增代码+CompactPipeline: 复用上下文超限恢复；如果没有这行代码，模型报错后无法 reactive compact。
from learning_agent.core.task_state import TaskState  # 新增代码+CompactPipeline: 使用任务状态作为压缩事实源；如果没有这行代码，压缩后目标仍可能丢失。


AUTOCOMPACT_FAILURE_BREAKER_LIMIT = 3  # 新增代码+CompactPipeline: 连续失败 3 次后打开熔断；如果没有这行代码，压缩失败可能每轮重复尝试。


@dataclass  # 新增代码+CompactPipeline: 自动生成流水线决策对象构造器；如果没有这行代码，调用方要手写样板。
class CompactPipelineDecision:  # 新增代码+CompactPipeline: 类段开始，表示模型请求前后的 compact 决策；如果没有这个类，agent.py 很难读懂压缩结果。
    messages: list[dict[str, Any]]  # 新增代码+CompactPipeline: 保存要送入模型的消息；如果没有这行代码，调用方拿不到压缩后上下文。
    compacted: bool  # 新增代码+CompactPipeline: 标记本次是否真实压缩；如果没有这行代码，状态事件无法区分 no-op 和 compact。
    reason: str  # 新增代码+CompactPipeline: 保存决策原因；如果没有这行代码，debug log 无法解释为什么压缩或不压缩。
    compact_generation: int  # 新增代码+CompactPipeline: 保存 compact 代次；如果没有这行代码，链式压缩无法审计。
    failure_count: int  # 新增代码+CompactPipeline: 保存连续失败次数；如果没有这行代码，熔断状态不可见。
    circuit_breaker_open: bool  # 新增代码+CompactPipeline: 标记熔断是否打开；如果没有这行代码，主循环不知道是否要跳过 autocompact。
    boundary: CompactBoundary | None = None  # 新增代码+CompactPipeline: 保存 compact boundary；如果没有这行代码，外部无法写 transcript 或验收字段。
    event_payload: dict[str, Any] = field(default_factory=dict)  # 新增代码+CompactPipeline: 保存可直接写事件的结构化信息；如果没有这行代码，agent.py 还要手动拼日志。

    def to_event_payload(self) -> dict[str, Any]:  # 新增代码+CompactPipeline: 函数段开始，把决策转成事件 payload；如果没有这段函数，状态事件格式会散落。
        payload = {  # 新增代码+CompactPipeline: 准备基础事件字段；如果没有这行代码，调用方拿不到结构化输出。
            "compacted": self.compacted,  # 新增代码+CompactPipeline: 写出是否压缩；如果没有这行代码，事件无法展示动作。
            "reason": self.reason,  # 新增代码+CompactPipeline: 写出原因；如果没有这行代码，事件不可解释。
            "compact_generation": self.compact_generation,  # 新增代码+CompactPipeline: 写出代次；如果没有这行代码，事件无法串联链式压缩。
            "failure_count": self.failure_count,  # 新增代码+CompactPipeline: 写出失败次数；如果没有这行代码，熔断过程不可见。
            "circuit_breaker_open": self.circuit_breaker_open,  # 新增代码+CompactPipeline: 写出熔断状态；如果没有这行代码，外部看不到是否跳过压缩。
        }  # 新增代码+CompactPipeline: 结束基础事件字段；如果没有这行代码，Python 字典语法不完整。
        payload.update(self.event_payload)  # 新增代码+CompactPipeline: 合并额外事件字段；如果没有这行代码，boundary 等细节无法附加。
        if self.boundary is not None:  # 新增代码+CompactPipeline: 有边界时写出 boundary；如果没有这行代码，未压缩 no-op 会错误访问 None。
            payload["boundary"] = self.boundary.to_dict()  # 新增代码+CompactPipeline: 写出完整边界；如果没有这行代码，acceptance 看不到 compact 细节。
        return payload  # 新增代码+CompactPipeline: 返回事件 payload；如果没有这行代码，调用方拿不到结果。


def _safe_int(value: Any, default: int = 0) -> int:  # 新增代码+CompactPipeline: 函数段开始，安全读取整数配置；如果没有这段函数，坏 runtime_state 容易让流水线崩溃。
    try:  # 新增代码+CompactPipeline: 尝试把值转成整数；如果没有这行代码，字符串数字无法兼容。
        return int(value)  # 新增代码+CompactPipeline: 返回整数值；如果没有这行代码，调用方拿不到转换结果。
    except (TypeError, ValueError):  # 新增代码+CompactPipeline: 捕获空值和坏字符串；如果没有这行代码，坏配置会中断主循环。
        return default  # 新增代码+CompactPipeline: 返回默认值；如果没有这行代码，异常场景没有安全退路。


def _runtime_dict(runtime_state: dict[str, Any] | None) -> dict[str, Any]:  # 新增代码+CompactPipeline: 函数段开始，确保 runtime_state 是可写字典；如果没有这段函数，None 输入会崩溃。
    return runtime_state if isinstance(runtime_state, dict) else {}  # 新增代码+CompactPipeline: 非 dict 时返回新空字典；如果没有这行代码，后续 get/set 会失败。


def _circuit_breaker_open(runtime_state: dict[str, Any]) -> bool:  # 新增代码+CompactPipeline: 函数段开始，判断 autocompact 熔断是否打开；如果没有这段函数，熔断条件会重复写。
    return _safe_int(runtime_state.get("autocompact_failure_count"), 0) >= AUTOCOMPACT_FAILURE_BREAKER_LIMIT  # 新增代码+CompactPipeline: 连续失败达到阈值就熔断；如果没有这行代码，压缩失败会每轮重试。


def _build_decision(messages: list[dict[str, Any]], compacted: bool, reason: str, runtime_state: dict[str, Any], boundary: CompactBoundary | None = None, event_payload: dict[str, Any] | None = None) -> CompactPipelineDecision:  # 新增代码+CompactPipeline: 函数段开始，统一构造流水线决策；如果没有这段函数，返回字段会重复拼。
    return CompactPipelineDecision(  # 新增代码+CompactPipeline: 构造决策对象；如果没有这行代码，调用方拿不到标准返回值。
        messages=messages,  # 新增代码+CompactPipeline: 写入模型消息；如果没有这行代码，决策没有上下文载荷。
        compacted=compacted,  # 新增代码+CompactPipeline: 写入是否压缩；如果没有这行代码，状态不可区分。
        reason=reason,  # 新增代码+CompactPipeline: 写入原因；如果没有这行代码，事件不可解释。
        compact_generation=_safe_int(runtime_state.get("compact_generation"), 0),  # 新增代码+CompactPipeline: 从 runtime_state 读取 compact 代次；如果没有这行代码，代次无法延续。
        failure_count=_safe_int(runtime_state.get("autocompact_failure_count"), 0),  # 新增代码+CompactPipeline: 从 runtime_state 读取失败次数；如果没有这行代码，熔断次数不可见。
        circuit_breaker_open=_circuit_breaker_open(runtime_state),  # 新增代码+CompactPipeline: 写入熔断状态；如果没有这行代码，主循环不知道是否处于熔断。
        boundary=boundary,  # 新增代码+CompactPipeline: 写入可选边界；如果没有这行代码，compact 成功细节会丢。
        event_payload=dict(event_payload or {}),  # 新增代码+CompactPipeline: 写入额外事件信息；如果没有这行代码，异常原因等细节会丢。
    )  # 新增代码+CompactPipeline: 结束决策构造；如果没有这行代码，Python 调用语法不完整。


def prepare_messages_before_model(messages: list[dict[str, Any]], task_state: TaskState, runtime_state: dict[str, Any] | None = None) -> CompactPipelineDecision:  # 新增代码+CompactPipeline: 函数段开始，模型调用前按流水线整理上下文；如果没有这段函数，agent.py 会继续散落 compact 判断。
    state = _runtime_dict(runtime_state)  # 新增代码+CompactPipeline: 取得可写运行时状态；如果没有这行代码，后续更新代次和失败次数会失败。
    if _circuit_breaker_open(state):  # 新增代码+CompactPipeline: 熔断打开时跳过主动 compact；如果没有这行代码，压缩失败会每轮重复发生。
        return _build_decision(messages, False, "autocompact_circuit_breaker_open", state)  # 新增代码+CompactPipeline: 返回跳过决策；如果没有这行代码，主循环不知道本轮为什么不压缩。
    max_messages = _safe_int(state.get("compact_max_messages"), 24)  # 新增代码+CompactPipeline: 读取消息数量阈值；如果没有这行代码，配置无法调整 compact 触发点。
    max_chars = _safe_int(state.get("compact_max_chars"), 60_000)  # 新增代码+CompactPipeline: 读取字符阈值；如果没有这行代码，长工具输出可能只按数量判断。
    if not should_compact_messages(messages, max_messages=max_messages, max_chars=max_chars):  # 新增代码+CompactPipeline: 未超阈值时不主动压缩；如果没有这行代码，短上下文也会被频繁 compact。
        return _build_decision(messages, False, "compact_not_needed", state)  # 新增代码+CompactPipeline: 返回 no-op 决策；如果没有这行代码，主循环无法知道无需压缩。
    next_generation = _safe_int(state.get("compact_generation"), 0) + 1  # 新增代码+CompactPipeline: 计算下一代 compact 编号；如果没有这行代码，边界代次不会增长。
    current_turn = _safe_int(state.get("turn"), 0)  # 新增代码+CompactPipeline: 读取当前轮数用于审计；如果没有这行代码，距离上次 compact 无法计算。
    last_turn = _safe_int(state.get("last_compact_turn"), current_turn)  # 新增代码+CompactPipeline: 读取上次 compact 轮数；如果没有这行代码，首次 compact 的轮距不稳定。
    turns_since_previous = max(0, current_turn - last_turn)  # 新增代码+CompactPipeline: 计算距离上次 compact 的轮数；如果没有这行代码，熔断和审计缺少时间距离。
    try:  # 新增代码+CompactPipeline: 包住底层 compact 防止主循环因压缩失败崩溃；如果没有这行代码，compact bug 会中断任务。
        compacted_messages, boundary = compact_messages_with_boundary(messages, session_id=str(state.get("session_id", "")), run_id=str(state.get("run_id", "")), turn_id=str(state.get("turn_id", "")), max_messages=max_messages, reason="run_events_pre_model_budget", artifact_dir=state.get("artifact_dir"), task_state=task_state, compact_model=state.get("compact_model"), recent_runtime_state=state, task_state_path=str(state.get("task_state_path", "")), compact_generation=next_generation, is_recompaction_in_chain=turns_since_previous == 0 and next_generation > 1, turns_since_previous_compact=turns_since_previous)  # 新增代码+CompactPipeline: 调用结构化 compact；如果没有这行代码，流水线不会真正压缩。
    except Exception as error:  # 新增代码+CompactPipeline: 捕获 compact 异常；如果没有这行代码，压缩失败会直接打断用户任务。
        state["autocompact_failure_count"] = _safe_int(state.get("autocompact_failure_count"), 0) + 1  # 新增代码+CompactPipeline: 记录连续失败次数；如果没有这行代码，熔断无法生效。
        return _build_decision(messages, False, "autocompact_failed", state, event_payload={"error": str(error)})  # 新增代码+CompactPipeline: 返回失败但不中断的决策；如果没有这行代码，主循环无法继续尝试模型。
    state["compact_generation"] = next_generation  # 新增代码+CompactPipeline: 写回 compact 代次；如果没有这行代码，下次压缩仍从旧代次开始。
    state["last_compact_turn"] = current_turn  # 新增代码+CompactPipeline: 写回上次 compact 轮数；如果没有这行代码，轮距审计会不准。
    state["autocompact_failure_count"] = 0 if boundary.quality_passed else _safe_int(state.get("autocompact_failure_count"), 0) + 1  # 新增代码+CompactPipeline: 成功则清零失败，质量不合格则累计；如果没有这行代码，熔断状态无法反映质量。
    return _build_decision(compacted_messages, True, "compacted_before_model", state, boundary=boundary)  # 新增代码+CompactPipeline: 返回成功 compact 决策；如果没有这行代码，主循环拿不到压缩后消息。


def recover_from_context_overflow(messages: list[dict[str, Any]], task_state: TaskState, error: BaseException | str, runtime_state: dict[str, Any] | None = None) -> CompactPipelineDecision:  # 新增代码+CompactPipeline: 函数段开始，模型报上下文过长时进行 reactive compact；如果没有这段函数，prompt too long 只能失败。
    state = _runtime_dict(runtime_state)  # 新增代码+CompactPipeline: 取得可写运行时状态；如果没有这行代码，恢复状态无法更新。
    if not is_prompt_too_long_error(error):  # 新增代码+CompactPipeline: 只处理上下文超限错误；如果没有这行代码，普通模型错误会被误当 compact 恢复。
        return _build_decision(messages, False, "context_overflow_not_detected", state, event_payload={"error": str(error)})  # 新增代码+CompactPipeline: 返回不恢复决策；如果没有这行代码，调用方不知道错误不匹配。
    if _circuit_breaker_open(state):  # 新增代码+CompactPipeline: 熔断打开时不再 reactive compact；如果没有这行代码，失败恢复会无限重复。
        return _build_decision(messages, False, "reactive_compact_circuit_breaker_open", state, event_payload={"error": str(error)})  # 新增代码+CompactPipeline: 返回熔断决策；如果没有这行代码，主循环不知道为何不能重试。
    next_generation = _safe_int(state.get("compact_generation"), 0) + 1  # 新增代码+CompactPipeline: 计算 reactive compact 代次；如果没有这行代码，恢复压缩无法纳入代次链。
    reactive_result = try_reactive_compact(messages, session_id=str(state.get("session_id", "")), run_id=str(state.get("run_id", "")), turn_id=str(state.get("turn_id", "")), has_attempted=bool(state.get("reactive_compact_attempted", False)), artifact_dir=state.get("artifact_dir"), task_state=task_state, recent_runtime_state=state, compact_generation=next_generation, turns_since_previous_compact=max(0, _safe_int(state.get("turn"), 0) - _safe_int(state.get("last_compact_turn"), _safe_int(state.get("turn"), 0))))  # 新增代码+CompactPipeline: 调用 reactive compact；如果没有这行代码，超限恢复无法保留 TaskState。
    state["reactive_compact_attempted"] = True  # 新增代码+CompactPipeline: 标记本轮已经尝试 reactive compact；如果没有这行代码，同一错误可能无限重试。
    if not reactive_result.should_retry or reactive_result.boundary is None:  # 新增代码+CompactPipeline: 处理不可重试结果；如果没有这行代码，失败恢复会被误判成功。
        state["autocompact_failure_count"] = _safe_int(state.get("autocompact_failure_count"), 0) + 1  # 新增代码+CompactPipeline: reactive 失败也累计失败；如果没有这行代码，熔断无法覆盖异常恢复。
        return _build_decision(messages, False, reactive_result.blocked_reason or reactive_result.transition_reason, state, event_payload={"error": str(error)})  # 新增代码+CompactPipeline: 返回失败决策；如果没有这行代码，主循环拿不到 blocked_reason。
    state["compact_generation"] = next_generation  # 新增代码+CompactPipeline: 写回 reactive compact 代次；如果没有这行代码，下次压缩代次不连续。
    state["last_compact_turn"] = _safe_int(state.get("turn"), 0)  # 新增代码+CompactPipeline: 写回 compact 轮次；如果没有这行代码，轮距审计会不准。
    state["autocompact_failure_count"] = 0 if reactive_result.boundary.quality_passed else _safe_int(state.get("autocompact_failure_count"), 0) + 1  # 新增代码+CompactPipeline: 根据质量结果更新失败次数；如果没有这行代码，reactive 质量失败不会熔断。
    return _build_decision(reactive_result.messages, True, reactive_result.transition_reason, state, boundary=reactive_result.boundary, event_payload={"error": str(error)})  # 新增代码+CompactPipeline: 返回可重试 compact 决策；如果没有这行代码，主循环无法用短上下文重试。


__all__ = ["AUTOCOMPACT_FAILURE_BREAKER_LIMIT", "CompactPipelineDecision", "prepare_messages_before_model", "recover_from_context_overflow"]  # 新增代码+CompactPipeline: 明确公开接口；如果没有这行代码，其他模块导入边界不清。
