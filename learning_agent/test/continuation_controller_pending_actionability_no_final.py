"""模型轮次继续/结束控制模块。"""  # 新增代码+ContinuationController: 说明本文件负责判断模型响应后是否继续主循环；如果没有这行代码，收束判断会散落在 agent.py。

from __future__ import annotations  # 新增代码+ContinuationController: 延迟解析类型注解；如果没有这行代码，跨模块类型引用更容易受导入顺序影响。

from dataclasses import dataclass  # 新增代码+ContinuationController: 用数据类表达继续/结束决策；如果没有这行代码，返回值会变成散乱 dict。
from typing import Any  # 新增代码+ContinuationController: 标注模型响应和 runtime_state 宽松结构；如果没有这行代码，接口边界不清楚。

from learning_agent.core.actionability_state import get_pending_actionability, pending_actionability_message  # 新增代码+PendingActionabilityNoFinal：导入真实动作 pending 读取和提示构造；如果没有这一行，模型拒绝继续调用工具时仍可能直接最终回答。
from learning_agent.core.task_state import TaskState  # 新增代码+ContinuationController: 使用任务状态构造模型可见提示；如果没有这行代码，stop hook 无法引用可靠目标。


@dataclass  # 新增代码+ContinuationController: 自动生成决策对象初始化方法；如果没有这行代码，调用方要写大量样板代码。
class ContinuationDecision:  # 新增代码+ContinuationController: 类段开始，表示一次模型响应后主循环如何继续；如果没有这个类，agent.py 无法清楚区分继续和最终回答。
    continue_loop: bool  # 新增代码+ContinuationController: 标记是否继续下一轮模型调用；如果没有这行代码，主循环不知道该停还是继续。
    injected_message: dict[str, str] | None  # 新增代码+ContinuationController: 保存需要注入模型的提示消息；如果没有这行代码，stop hook/token budget 无法推动下一轮。
    reason: str  # 新增代码+ContinuationController: 保存决策原因；如果没有这行代码，debug 事件无法解释收束判断。
    event_name: str  # 新增代码+ContinuationController: 保存事件名；如果没有这行代码，观测层无法区分自然停止、hook 阻塞和预算提醒。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+ContinuationController: 函数段开始，把决策转成 JSON；如果没有这段函数，事件 payload 要重复拼。
        return {  # 新增代码+ContinuationController: 返回结构化字段；如果没有这行代码，调用方拿不到统一 payload。
            "continue_loop": self.continue_loop,  # 新增代码+ContinuationController: 写出是否继续；如果没有这行代码，事件不完整。
            "injected_message": dict(self.injected_message) if self.injected_message is not None else None,  # 新增代码+ContinuationController: 写出可选注入消息；如果没有这行代码，hook 追加内容不可见。
            "reason": self.reason,  # 新增代码+ContinuationController: 写出原因；如果没有这行代码，debug 不可解释。
            "event_name": self.event_name,  # 新增代码+ContinuationController: 写出事件名；如果没有这行代码，观测层难以分类。
        }  # 新增代码+ContinuationController: 结束字典返回；如果没有这行代码，Python 字典语法不完整。


def _tool_calls_from_response(model_response: Any) -> list[Any]:  # 新增代码+ContinuationController: 函数段开始，安全读取模型工具调用；如果没有这段函数，None 或不同模型对象会让主循环崩溃。
    return list(getattr(model_response, "tool_calls", []) or [])  # 新增代码+ContinuationController: 返回工具调用列表；如果没有这行代码，判断继续/结束没有依据。


def _runtime_dict(runtime_state: dict[str, Any] | None) -> dict[str, Any]:  # 新增代码+ContinuationController: 函数段开始，统一 runtime_state 输入；如果没有这段函数，None 输入会崩溃。
    return runtime_state if isinstance(runtime_state, dict) else {}  # 新增代码+ContinuationController: 非 dict 返回空字典；如果没有这行代码，后续 get 会失败。


def _system_message(content: str) -> dict[str, str]:  # 新增代码+ContinuationController: 函数段开始，构造模型可见系统提示；如果没有这段函数，注入消息格式会重复散落。
    return {"role": "system", "content": content}  # 新增代码+ContinuationController: 返回 system 消息；如果没有这行代码，主循环无法追加提示。


def decide_after_model_response(model_response: Any, task_state: TaskState, runtime_state: dict[str, Any] | None = None) -> ContinuationDecision:  # 新增代码+ContinuationController: 函数段开始，决定模型响应后是否继续；如果没有这段函数，agent.py 会继续直接写 if tool_calls。
    state = _runtime_dict(runtime_state)  # 新增代码+ContinuationController: 取得可读运行时状态；如果没有这行代码，stop hook 和预算状态无法读取。
    if _tool_calls_from_response(model_response):  # 新增代码+ContinuationController: 只要模型真的产生工具调用就继续工具循环；如果没有这行代码，ClaudeCode 式 tool_use 语义会丢。
        state["pending_actionability_no_tool_exit_count"] = 0  # 新增代码+PendingActionabilityNoFinal：模型已经重新调用工具时清零“无工具结束”计数；如果没有这一行，后续审计会误以为模型仍在反复提前结束。
        return ContinuationDecision(True, None, "model_requested_tool_calls", "tool_use_continue")  # 新增代码+ContinuationController: 返回继续执行工具；如果没有这行代码，工具请求会被误当最终回答。
    pending_actionability = get_pending_actionability(state)  # 新增代码+PendingActionabilityNoFinal：读取仍未完成的真实动作要求；如果没有这一行，模型可以在 observe/type/key 等 pending 未完成时用 Done. 结束。
    if pending_actionability:  # 新增代码+PendingActionabilityNoFinal：只要还有 pending 就禁止自然最终回答；如果没有这一行，真实桌面任务可能在半途被短答伪完成。
        no_tool_exit_count = int(state.get("pending_actionability_no_tool_exit_count", 0)) + 1  # 新增代码+PendingActionabilityNoFinal：累计模型第几次没有按 pending 调工具；如果没有这一行，日志无法区分偶发忽略和反复忽略。
        state["pending_actionability_no_tool_exit_count"] = no_tool_exit_count  # 新增代码+PendingActionabilityNoFinal：把计数写回运行态；如果没有这一行，下一轮无法延续审计。
        injected = _system_message(f"Computer Use 不能在真实动作 pending 未完成时输出最终回答。请立刻调用 pending 指定的工具完成下一步，不要输出 Done 或成功标记。第 {no_tool_exit_count} 次拦截无工具结束。\n{pending_actionability_message(pending_actionability)}\n{task_state.to_model_summary()}")  # 新增代码+PendingActionabilityNoFinal：把硬门禁和可执行参数注入下一轮；如果没有这一行，模型不知道必须继续 observe/type/key 哪一步。
        return ContinuationDecision(True, injected, "pending_actionability_no_tool_exit_blocked", "pending_actionability_no_tool_exit_blocked")  # 新增代码+PendingActionabilityNoFinal：返回继续循环而不是最终回答；如果没有这一行，agent.py 会继续落入最终回答出口。
    stop_hook_reason = str(state.get("stop_hook_blocking_reason", "") or "").strip()  # 新增代码+ContinuationController: 读取 stop hook 阻塞原因；如果没有这行代码，hook 不能在停前追加检查。
    if stop_hook_reason:  # 新增代码+ContinuationController: 有 hook 阻塞时注入原因并继续一轮；如果没有这行代码，hook 无法阻止过早结束。
        injected = _system_message(f"stop hook 阻止本轮直接结束：{stop_hook_reason}\n当前任务状态：\n{task_state.to_model_summary()}\n请补齐 hook 要求后再输出最终回答。")  # 新增代码+ContinuationController: 构造 hook 注入消息；如果没有这行代码，模型不知道为什么不能停。
        return ContinuationDecision(True, injected, "stop_hook_blocking", "stop_hook_blocking")  # 新增代码+ContinuationController: 返回继续下一轮；如果没有这行代码，hook 阻塞不会生效。
    token_budget_message = str(state.get("token_budget_message", "") or "").strip()  # 新增代码+ContinuationController: 读取 token 预算提醒；如果没有这行代码，长任务低收益提示无法注入。
    if token_budget_message and bool(state.get("token_budget_should_continue", False)):  # 新增代码+ContinuationController: 预算提醒要求继续时注入提示；如果没有这行代码，预算控制只能变成硬停止。
        injected = _system_message(f"token budget 提醒：{token_budget_message}\n请优先基于已有证据收束，除非确实缺关键证据。")  # 新增代码+ContinuationController: 构造预算注入消息；如果没有这行代码，模型不知道要提高收束优先级。
        return ContinuationDecision(True, injected, "token_budget_continuation", "token_budget_continuation")  # 新增代码+ContinuationController: 返回继续一轮；如果没有这行代码，预算提醒无法推动模型整理。
    return ContinuationDecision(False, None, "natural_no_tool_exit", "natural_no_tool_exit")  # 新增代码+ContinuationController: 没有工具调用且无 hook 阻塞时自然进入最终回答；如果没有这行代码，主循环无法稳定收束。


__all__ = ["ContinuationDecision", "decide_after_model_response"]  # 新增代码+ContinuationController: 明确公开接口；如果没有这行代码，其他模块导入边界不清。
