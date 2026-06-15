"""交互终端多轮上下文和自动压缩模块。"""  # 新增代码+交互上下文: 说明本文件负责同一真实终端窗口里的历史记忆；如果没有这行，维护者容易把上下文逻辑又塞回 agent.py。

from __future__ import annotations  # 新增代码+交互上下文: 延迟解析类型注解，降低导入顺序风险；如果没有这行，某些类型引用可能在模块加载时提前求值。

import copy  # 新增代码+交互上下文: 复制消息列表避免调用方修改内部历史；如果没有这行，外部测试或 UI 可能意外污染真实会话上下文。
import json  # 新增代码+交互上下文: 把 compact boundary 写成 JSON artifact；如果没有这行，压缩证据只能留在内存里。
from dataclasses import dataclass  # 新增代码+交互上下文: 定义轻量配置和快照对象；如果没有这行，配置字段会散落成容易写错的 dict。
from pathlib import Path  # 新增代码+交互上下文: 处理 Windows artifact 路径；如果没有这行，字符串拼路径容易出错。
from typing import Any, Mapping, Sequence  # 新增代码+交互上下文: 标注消息输入这种灵活结构；如果没有这行，接口边界不清楚。

from learning_agent.core.compact import CompactBoundary, compact_messages_with_boundary, estimate_messages_chars  # 新增代码+交互上下文: 复用现有可审计 compact 能力；如果没有这行，本模块会重复造一套压缩机制。
from learning_agent.core.task_state import TaskState  # 新增代码+ContextCompactRepairInteractive: 引入任务状态给交互压缩使用；如果没有这行，多轮终端压缩后仍可能丢原始目标。


@dataclass(frozen=True)  # 新增代码+交互上下文: 自动生成不可变配置对象；如果没有这行，调用方可能运行中误改配置。
class ConversationContextConfig:  # 新增代码+交互上下文: 保存交互上下文预算和尾部保留策略；如果没有这个类，interactive.py 只能传散乱参数。
    prompt_soft_token_limit: int  # 新增代码+交互上下文: 保存项目已有 prompt 软预算；如果没有这行，自动压缩不知道模型上下文预算。
    compact_ratio: float = 0.75  # 新增代码+交互上下文: 默认在约 75% 预算时主动压缩；如果没有这行，长会话只能等模型报错后 reactive compact。
    raw_tail_messages: int = 8  # 新增代码+交互上下文: 压缩后保留最近原文消息条数；如果没有这行，用户刚刚纠正的信息可能只剩摘要。


@dataclass(frozen=True)  # 新增代码+交互上下文: 自动生成只读快照对象；如果没有这行，状态命令需要直接读内部字段。
class ConversationContextSnapshot:  # 新增代码+交互上下文: 描述当前交互历史状态；如果没有这个类，/status 和测试无法稳定读取压缩状态。
    message_count: int  # 新增代码+交互上下文: 保存当前历史消息数量；如果没有这行，用户看不到上下文规模。
    estimated_chars: int  # 新增代码+交互上下文: 保存当前历史估算字符数；如果没有这行，无法判断是否接近压缩阈值。
    compact_count: int  # 新增代码+交互上下文: 保存已发生主动压缩次数；如果没有这行，验收无法证明压缩真的触发过。
    last_compact_reason: str | None  # 新增代码+交互上下文: 保存最近一次压缩原因；如果没有这行，排查时不知道为什么压缩。
    last_compact_quality_passed: bool | None = None  # 新增代码+ContextCompactRepairInteractive: 保存最近一次压缩质量是否通过；如果没有这行，/status 看不到 compact 质量门禁结果。
    compact_generation: int = 0  # 新增代码+ContextCompactRepairInteractive: 保存交互上下文 compact 代次；如果没有这行，长终端会话无法区分多次压缩。


def _safe_positive_int(value: int, fallback: int) -> int:  # 新增代码+交互上下文: 函数段开始，把配置数字保护成正整数；如果没有这段函数，坏配置可能让阈值和尾部保留变成 0 或负数。
    try:  # 新增代码+交互上下文: 捕获无法转成整数的值；如果没有这一行，坏配置会抛出底层异常。
        parsed_value = int(value)  # 新增代码+交互上下文: 把输入转成整数；如果没有这一行，字符串数字无法作为预算使用。
    except (TypeError, ValueError):  # 新增代码+交互上下文: 处理 None、对象或非数字文本；如果没有这一行，配置错误提示不够稳定。
        return fallback  # 新增代码+交互上下文: 使用兜底值保持 agent 可运行；如果没有这一行，交互终端可能因为小配置错误无法启动。
    return parsed_value if parsed_value > 0 else fallback  # 新增代码+交互上下文: 只接受正整数；如果没有这一行，0 或负数会导致反复压缩或保留空历史。
# 新增代码+交互上下文: 函数段结束，_safe_positive_int 到此结束；如果没有这个边界说明，代码小白不容易看出配置保护范围。


def _safe_compact_ratio(value: float) -> float:  # 新增代码+交互上下文: 函数段开始，把压缩比例限制在可用范围；如果没有这段函数，坏比例可能让压缩永远不触发或每轮都触发。
    try:  # 新增代码+交互上下文: 捕获无法转成浮点数的值；如果没有这一行，坏配置会抛出底层异常。
        parsed_value = float(value)  # 新增代码+交互上下文: 把输入转成浮点比例；如果没有这一行，JSON 或环境变量里的数字字符串无法使用。
    except (TypeError, ValueError):  # 新增代码+交互上下文: 处理 None、对象或非数字文本；如果没有这一行，配置错误会打断终端启动。
        return 0.75  # 新增代码+交互上下文: 坏值使用蓝图默认 75%；如果没有这一行，agent 没有稳定默认策略。
    if parsed_value <= 0:  # 新增代码+交互上下文: 拒绝小于等于 0 的比例；如果没有这一行，任何上下文都会被判定超预算。
        return 0.75  # 新增代码+交互上下文: 非法低值回到默认；如果没有这一行，用户配置错误会造成体验异常。
    if parsed_value > 1:  # 新增代码+交互上下文: 拒绝大于 100% 的比例；如果没有这一行，自动压缩可能太晚触发。
        return 0.75  # 新增代码+交互上下文: 非法高值回到默认；如果没有这一行，模型上下文仍可能爆掉。
    return parsed_value  # 新增代码+交互上下文: 返回合法比例；如果没有这一行，调用方拿不到最终阈值比例。
# 新增代码+交互上下文: 函数段结束，_safe_compact_ratio 到此结束；如果没有这个边界说明，代码小白不容易看出比例保护范围。


def _normalise_history_message(raw_message: Mapping[str, Any]) -> dict[str, str] | None:  # 新增代码+交互上下文: 函数段开始，把任意历史消息清洗成模型安全的 user/assistant；如果没有这段函数，system 伪造或空消息可能污染上下文。
    role = str(raw_message.get("role", "")).strip()  # 新增代码+交互上下文: 读取并清理消息角色；如果没有这一行，后续无法判断消息来源。
    content = str(raw_message.get("content", "")).strip()  # 新增代码+交互上下文: 读取并清理消息正文；如果没有这一行，空白或非字符串内容会直接进入模型。
    if not content:  # 新增代码+交互上下文: 跳过空正文；如果没有这一行，模型会收到没有意义的历史消息。
        return None  # 新增代码+交互上下文: 空消息不进入历史；如果没有这一行，调用方无法过滤掉无效项。
    if role in {"user", "assistant"}:  # 新增代码+交互上下文: 只原样接受 user 和 assistant；如果没有这一行，普通历史也会被错误改写。
        return {"role": role, "content": content}  # 新增代码+交互上下文: 返回安全消息副本；如果没有这一行，模型拿不到有效历史。
    return {"role": "assistant", "content": f"前文压缩摘要：{content}"}  # 新增代码+交互上下文: 把 compact 产生的 system 摘要降级为 assistant 历史；如果没有这一行，agent.py 的 system 过滤会丢掉压缩摘要。
# 新增代码+交互上下文: 函数段结束，_normalise_history_message 到此结束；如果没有这个边界说明，代码小白不容易看出消息清洗范围。


class InteractiveConversationContext:  # 新增代码+交互上下文: 类段开始，维护同一真实终端窗口的多轮历史；如果没有这个类，interactive.py 只能继续每轮丢掉上文。
    def __init__(self, config: ConversationContextConfig, artifact_dir: Path | None = None) -> None:  # 新增代码+交互上下文: 函数段开始，初始化上下文状态；如果没有这段函数，调用方无法创建可复用历史容器。
        self.config = config  # 新增代码+交互上下文: 保存预算和尾部配置；如果没有这一行，后续无法判断何时压缩。
        self.artifact_dir = artifact_dir  # 新增代码+交互上下文: 保存压缩证据目录；如果没有这一行，boundary JSON 无法落盘。
        self._messages: list[dict[str, str]] = []  # 新增代码+交互上下文: 保存当前结构化历史；如果没有这一行，第二轮无法拿到第一轮问答。
        self._compact_boundaries: list[CompactBoundary] = []  # 新增代码+交互上下文: 保存压缩边界列表；如果没有这一行，状态和验收无法知道压缩详情。
        self._last_compact_reason: str | None = None  # 新增代码+交互上下文: 保存最近一次压缩原因；如果没有这一行，snapshot 缺少解释字段。
        self._last_compact_quality_passed: bool | None = None  # 新增代码+ContextCompactRepairInteractive: 保存最近压缩质量结果；如果没有这一行，真实终端状态无法证明摘要质量。
        self._compact_generation = 0  # 新增代码+ContextCompactRepairInteractive: 保存交互压缩代次；如果没有这一行，多次压缩无法审计。
    # 新增代码+交互上下文: 函数段结束，InteractiveConversationContext.__init__ 到此结束；如果没有这个边界说明，代码小白不容易看出初始化范围。

    def append_exchange(self, user_text: str, assistant_text: str) -> None:  # 新增代码+交互上下文: 函数段开始，追加一轮成功完成的用户和 assistant 问答；如果没有这段函数，下一轮不会继承上一轮结果。
        safe_user_text = str(user_text or "").strip()  # 新增代码+交互上下文: 清理用户输入文本；如果没有这一行，空白输入也可能进入历史。
        safe_assistant_text = str(assistant_text or "").strip()  # 新增代码+交互上下文: 清理 assistant 最终回答；如果没有这一行，空回答会污染历史。
        if safe_user_text:  # 新增代码+交互上下文: 只有用户文本非空才追加；如果没有这一行，空回车可能被当成历史任务。
            self._messages.append({"role": "user", "content": safe_user_text})  # 新增代码+交互上下文: 保存用户原话；如果没有这一行，后续短句无法继承用户目标。
        if safe_assistant_text:  # 新增代码+交互上下文: 只有 assistant 文本非空才追加；如果没有这一行，失败或空答也可能进入上下文。
            self._messages.append({"role": "assistant", "content": safe_assistant_text})  # 新增代码+交互上下文: 保存 assistant 最终回答；如果没有这一行，下一轮不知道 agent 已经答过什么。
    # 新增代码+交互上下文: 函数段结束，append_exchange 到此结束；如果没有这个边界说明，代码小白不容易看出历史追加时机。

    def messages_for_run(self, current_user_input: str, *, session_id: str, run_id: str, turn_id: int | str) -> list[dict[str, str]]:  # 新增代码+交互上下文: 函数段开始，为下一次 agent.run 返回应注入的历史；如果没有这段函数，interactive.py 无法拿到预算受控的 conversation_history。
        history_messages = copy.deepcopy(self._messages)  # 新增代码+交互上下文: 复制内部历史给本轮预算判断；如果没有这一行，压缩过程可能意外改坏原列表。
        budget_probe_messages = history_messages + [{"role": "user", "content": str(current_user_input or "")}]  # 新增代码+交互上下文: 把当前输入只用于估算预算；如果没有这一行，长当前输入可能绕过压缩阈值。
        threshold_chars = self._compact_threshold_chars()  # 新增代码+交互上下文: 计算 70%-80% 主动压缩阈值；如果没有这一行，预算逻辑会散落在调用处。
        if history_messages and estimate_messages_chars(budget_probe_messages) > threshold_chars:  # 新增代码+交互上下文: 历史加当前输入超阈值时才主动压缩；如果没有这一行，长会话会一直堆到模型报错。
            self._compact_history(session_id=session_id, run_id=run_id, turn_id=turn_id)  # 新增代码+交互上下文: 执行旧历史压缩并更新内部状态；如果没有这一行，摘要不会替代旧消息。
        return copy.deepcopy(self._messages)  # 新增代码+交互上下文: 返回安全副本给 agent.run；如果没有这一行，调用方可能直接改动内部历史。
    # 新增代码+交互上下文: 函数段结束，messages_for_run 到此结束；如果没有这个边界说明，代码小白不容易看出当前输入不会被重复返回。

    def snapshot(self) -> ConversationContextSnapshot:  # 新增代码+交互上下文: 函数段开始，返回当前上下文状态快照；如果没有这段函数，状态命令和测试无法读取压缩状态。
        return ConversationContextSnapshot(  # 新增代码+交互上下文: 构造只读快照对象；如果没有这一行，调用方只能读取内部私有字段。
            message_count=len(self._messages),  # 新增代码+交互上下文: 写入当前消息数量；如果没有这一行，用户看不到历史规模。
            estimated_chars=estimate_messages_chars(self._messages),  # 新增代码+交互上下文: 写入当前估算字符数；如果没有这一行，用户看不到上下文预算压力。
            compact_count=len(self._compact_boundaries),  # 新增代码+交互上下文: 写入压缩次数；如果没有这一行，验收无法证明压缩发生过。
            last_compact_reason=self._last_compact_reason,  # 新增代码+交互上下文: 写入最近压缩原因；如果没有这一行，状态信息缺少解释。
            last_compact_quality_passed=self._last_compact_quality_passed,  # 新增代码+ContextCompactRepairInteractive: 写入最近压缩质量；如果没有这一行，状态页无法发现低质量摘要。
            compact_generation=self._compact_generation,  # 新增代码+ContextCompactRepairInteractive: 写入压缩代次；如果没有这一行，验收无法追踪多次压缩。
        )  # 新增代码+交互上下文: 快照构造结束；如果没有这一行，Python 调用语法不完整。
    # 新增代码+交互上下文: 函数段结束，snapshot 到此结束；如果没有这个边界说明，代码小白不容易看出状态读取范围。

    def _compact_threshold_chars(self) -> int:  # 新增代码+交互上下文: 函数段开始，计算主动压缩字符阈值；如果没有这段函数，阈值公式会在多个地方重复。
        safe_token_limit = _safe_positive_int(self.config.prompt_soft_token_limit, 60_000)  # 新增代码+交互上下文: 保护 prompt 预算为正整数；如果没有这一行，坏预算会造成压缩异常。
        safe_ratio = _safe_compact_ratio(self.config.compact_ratio)  # 新增代码+交互上下文: 保护压缩比例在 0 到 1 之间；如果没有这一行，坏比例会让压缩时机失控。
        return max(100, int(safe_token_limit * 4 * safe_ratio))  # 新增代码+交互上下文: 按蓝图用 token 预算乘 4 估算字符阈值；如果没有这一行，自动压缩没有明确触发点。
    # 新增代码+交互上下文: 函数段结束，_compact_threshold_chars 到此结束；如果没有这个边界说明，代码小白不容易看出预算公式。

    def _compact_history(self, *, session_id: str, run_id: str, turn_id: int | str) -> None:  # 新增代码+交互上下文: 函数段开始，压缩内部历史并记录边界；如果没有这段函数，超预算时只能丢历史或继续膨胀。
        tail_limit = _safe_positive_int(self.config.raw_tail_messages, 8)  # 新增代码+交互上下文: 保护原文尾巴数量；如果没有这一行，错误配置可能让最近消息全丢。
        task_state = self._task_state_for_compact(session_id=str(session_id), run_id=str(run_id))  # 新增代码+ContextCompactRepairInteractive: 从交互历史构造 TaskState；如果没有这一行，压缩摘要没有可靠用户目标。
        self._compact_generation += 1  # 新增代码+ContextCompactRepairInteractive: 推进交互 compact 代次；如果没有这一行，boundary 代次不会增长。
        _compacted_messages, boundary = compact_messages_with_boundary(self._messages, session_id=str(session_id), run_id=str(run_id), turn_id=str(turn_id), max_messages=max(3, tail_limit + 1), reason="interactive_context_soft_limit", artifact_dir=self.artifact_dir, task_state=task_state, recent_runtime_state={"plan_state": "interactive conversation context autocompact"}, compact_generation=self._compact_generation, turns_since_previous_compact=0 if len(self._compact_boundaries) else int(turn_id) if str(turn_id).isdigit() else 0)  # 修改代码+ContextCompactRepairInteractive: 使用 TaskState-aware compact 生成高质量摘要；如果没有这一行，交互压缩仍可能只保留旧导航摘要。
        summary_message = {"role": "assistant", "content": f"前文压缩摘要：{boundary.summary_text}"}  # 修改代码+交互上下文: 用 assistant 历史承载 compact 摘要；如果没有这一行，agent.py 会过滤 system 摘要导致旧上下文丢失。
        tail_messages = copy.deepcopy(self._messages[-tail_limit:])  # 修改代码+交互上下文: 明确保留最近 raw_tail_messages 条原文；如果没有这一行，用户刚刚纠正的信息可能被 compact 内部锚点挤掉。
        candidate_messages = [summary_message] + tail_messages  # 修改代码+交互上下文: 组合“旧历史摘要 + 最近原文尾巴”；如果没有这一行，压缩后历史结构不符合蓝图。
        safe_messages = [_normalise_history_message(message) for message in candidate_messages if isinstance(message, Mapping)]  # 修改代码+交互上下文: 清洗摘要和尾部消息；如果没有这一行，agent.py 可能收到空消息或不安全角色。
        self._messages = [message for message in safe_messages if message is not None]  # 新增代码+交互上下文: 用安全消息替换内部历史；如果没有这一行，旧超长历史仍会留在下一轮。
        self._compact_boundaries.append(boundary)  # 新增代码+交互上下文: 保存压缩边界；如果没有这一行，snapshot 和验收无法看到压缩次数。
        self._last_compact_reason = boundary.reason  # 新增代码+交互上下文: 保存最近压缩原因；如果没有这一行，用户无法知道为什么压缩。
        self._last_compact_quality_passed = boundary.quality_passed  # 新增代码+ContextCompactRepairInteractive: 保存最近压缩质量结果；如果没有这一行，/status 无法展示质量门禁。
        self._write_boundary_artifact(boundary)  # 新增代码+交互上下文: 把压缩边界写入 artifact；如果没有这一行，长期任务中压缩证据容易被覆盖或丢失。
    # 新增代码+交互上下文: 函数段结束，_compact_history 到此结束；如果没有这个边界说明，代码小白不容易看出主动压缩范围。

    def _task_state_for_compact(self, *, session_id: str, run_id: str) -> TaskState:  # 新增代码+ContextCompactRepairInteractive: 函数段开始，从交互历史构造 compact 用 TaskState；如果没有这段函数，交互压缩没有事实源。
        user_messages = [message["content"] for message in self._messages if message.get("role") == "user"]  # 新增代码+ContextCompactRepairInteractive: 收集历史用户消息；如果没有这一行，TaskState 找不到原始目标和最新补充。
        original_request = user_messages[0] if user_messages else "交互终端历史压缩"  # 新增代码+ContextCompactRepairInteractive: 选择第一条用户消息作为原始目标；如果没有这一行，压缩后会忘记最初任务。
        latest_input = user_messages[-1] if user_messages else original_request  # 新增代码+ContextCompactRepairInteractive: 选择最后一条用户消息作为最新输入；如果没有这一行，多轮补充会丢失。
        task_state = TaskState.from_user_input(original_request, session_id=session_id, run_id=run_id)  # 新增代码+ContextCompactRepairInteractive: 创建任务状态；如果没有这一行，compact_quality 无法检查目标保留。
        task_state.update_latest_user_input(latest_input)  # 新增代码+ContextCompactRepairInteractive: 写入最新用户输入；如果没有这一行，摘要不会包含最近补充。
        task_state.add_pending_item("继续当前交互终端里的多轮用户目标")  # 新增代码+ContextCompactRepairInteractive: 写入默认待办；如果没有这一行，Pending Tasks 可能为空。
        task_state.add_key_fact(f"历史用户消息数量：{len(user_messages)}")  # 新增代码+ContextCompactRepairInteractive: 写入历史规模事实；如果没有这一行，模型不知道摘要覆盖多少轮。
        task_state.set_next_step_hint("结合压缩摘要和最近原文继续回答当前用户输入，证据足够时收束。")  # 新增代码+ContextCompactRepairInteractive: 写入下一步；如果没有这一行，压缩后模型可能继续读旧日志恢复任务。
        return task_state  # 新增代码+ContextCompactRepairInteractive: 返回 TaskState；如果没有这一行，调用方拿不到事实源。
    # 新增代码+ContextCompactRepairInteractive: 函数段结束，_task_state_for_compact 到此结束；如果没有这个边界说明，代码小白不容易看出 TaskState 构造范围。

    def _write_boundary_artifact(self, boundary: CompactBoundary) -> None:  # 新增代码+交互上下文: 函数段开始，把一次压缩边界落盘；如果没有这段函数，acceptance controller 只能从内存事件猜测压缩发生过。
        if self.artifact_dir is None:  # 新增代码+交互上下文: 没有 artifact 目录时跳过落盘；如果没有这一行，纯单元测试会因为空路径失败。
            return  # 新增代码+交互上下文: 无目录直接返回；如果没有这一行，后续 Path 操作会崩溃。
        self.artifact_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+交互上下文: 确保 artifact 目录存在；如果没有这一行，首次写 boundary JSON 会失败。
        artifact_path = self.artifact_dir / f"{boundary.boundary_uuid}_interactive_context_boundary.json"  # 新增代码+交互上下文: 生成可追踪的 boundary 文件名；如果没有这一行，多次压缩证据可能互相覆盖。
        artifact_path.write_text(json.dumps(boundary.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")  # 新增代码+交互上下文: 写入 UTF-8 JSON 证据；如果没有这一行，用户无法离线查看压缩前后规模。
    # 新增代码+交互上下文: 函数段结束，_write_boundary_artifact 到此结束；如果没有这个边界说明，代码小白不容易看出证据落盘范围。
# 新增代码+交互上下文: 类段结束，InteractiveConversationContext 到此结束；如果没有这个边界说明，代码小白不容易看出上下文管理器范围。
