"""compact 专用 no-tools 摘要器。"""  # 新增代码+CompactSummarizer: 说明本文件负责把旧上下文压缩成摘要；如果没有这行代码，维护者可能把它误当主任务执行器。

from __future__ import annotations  # 新增代码+CompactSummarizer: 延迟解析类型注解；如果没有这行代码，跨模块类型引用更容易受导入顺序影响。

from dataclasses import dataclass  # 新增代码+CompactSummarizer: 用数据类保存摘要结果；如果没有这行代码，结果字段会散落成普通 dict。
from typing import Any  # 新增代码+CompactSummarizer: 接收模型和消息的宽松类型；如果没有这行代码，接口类型边界不清楚。

from learning_agent.core.compact_prompt import COMPACT_SECTION_HEADINGS, build_compact_prompt  # 新增代码+CompactSummarizer: 复用固定 prompt 合同；如果没有这行代码，摘要器和质量检查会用不同标题。
from learning_agent.core.task_state import TaskState  # 新增代码+CompactSummarizer: 使用任务状态事实源；如果没有这行代码，摘要器无法保留原始目标。

ASSISTANT_FINDING_CHAR_LIMIT = 1200  # 新增代码+CompactAssistantFindings: 限制单条 assistant 阶段结论长度；如果没有这行代码，上一轮长回答可能再次撑爆 compact 后上下文。
ASSISTANT_FINDING_MAX_COUNT = 3  # 新增代码+CompactAssistantFindings: 最多保留最近 3 条 assistant 阶段结论；如果没有这行代码，多轮长任务会把摘要挤成历史聊天全文。


@dataclass  # 新增代码+CompactSummarizer: 自动生成摘要结果初始化方法；如果没有这行代码，调用方要手写结果对象。
class CompactSummaryResult:  # 新增代码+CompactSummarizer: 类段开始，表示一次 compact 摘要尝试；如果没有这个类，used_tools 等关键审计字段会丢失。
    summary_text: str  # 新增代码+CompactSummarizer: 保存摘要文本；如果没有这行代码，compact.py 拿不到要放回模型的摘要。
    used_tools: bool  # 新增代码+CompactSummarizer: 标记摘要阶段是否试图调用工具；如果没有这行代码，质量检查无法拒绝违规压缩。
    model_name: str  # 新增代码+CompactSummarizer: 保存使用的模型名称；如果没有这行代码，调试时不知道摘要来自哪里。
    prompt_chars: int  # 新增代码+CompactSummarizer: 保存 prompt 字符数；如果没有这行代码，无法审计压缩输入规模。
    summary_chars: int  # 新增代码+CompactSummarizer: 保存摘要字符数；如果没有这行代码，无法审计压缩输出规模。
    reason: str  # 新增代码+CompactSummarizer: 保存触发原因；如果没有这行代码，compact boundary 无法解释摘要来源。


def _message_content(message: dict[str, Any]) -> str:  # 新增代码+CompactSummarizer: 函数段开始，安全读取消息正文；如果没有这段函数，不同消息结构会重复处理。
    if not isinstance(message, dict):  # 修改代码+CompactNone污染: 先确认消息是字典；如果没有这行代码，坏消息结构可能让摘要器崩溃。
        return ""  # 修改代码+CompactNone污染: 坏消息直接当空正文；如果没有这行代码，摘要器会把无效结构继续传下去。
    content = message.get("content", "")  # 修改代码+CompactNone污染: 取出原始正文对象；如果没有这行代码，就无法区分真正文本和 None。
    if content is None:  # 新增代码+CompactNone污染: 明确识别无正文的 assistant/tool 占位消息；如果没有这行代码，None 会被 str(None) 变成有害的 "None" 阶段结论。
        return ""  # 新增代码+CompactNone污染: 无正文消息返回空文本；如果没有这行代码，compact summary 会继续出现“前文 assistant 阶段结论：None”。
    return str(content)  # 修改代码+CompactNone污染: 只有真实正文才转成字符串；如果没有这行代码，普通文本、数字或对象正文无法被摘要器读取。


def _collect_user_messages(messages: list[dict[str, Any]]) -> list[str]:  # 新增代码+CompactSummarizer: 函数段开始，收集历史用户消息；如果没有这段函数，九段摘要的 All user messages 会缺内容。
    return [_message_content(message).strip() for message in messages if isinstance(message, dict) and message.get("role") == "user" and _message_content(message).strip()]  # 新增代码+CompactSummarizer: 返回非空用户消息列表；如果没有这行代码，多轮用户意图无法进入摘要。

def _normalise_finding_text(value: Any) -> str:  # 新增代码+CompactAssistantFindings: 函数段开始，把 assistant 历史结论压成单行可读文本；如果没有这段函数，换行很多的回答会让 compact 摘要难读。
    return " ".join(str(value or "").split())  # 新增代码+CompactAssistantFindings: 合并空白并去掉首尾空格；如果没有这行代码，摘要里会保留大量无意义换行和缩进。


def _is_recursive_summary_text(text: str) -> bool:  # 新增代码+CompactAssistantFindings: 函数段开始，识别已经是压缩摘要的 assistant 消息；如果没有这段函数，压缩摘要会一层套一层越来越空。
    stripped = str(text or "").strip()  # 新增代码+CompactAssistantFindings: 清理待判断文本；如果没有这行代码，前导空白会影响识别。
    return stripped.startswith("前文压缩摘要：") or stripped.startswith("<summary>")  # 新增代码+CompactAssistantFindings: 返回是否为旧摘要文本；如果没有这行代码，旧摘要容易被当成新阶段结论重复吸收。


def _is_placeholder_finding_text(text: str) -> bool:  # 新增代码+CompactNone污染: 函数段开始，识别没有真实语义的 assistant 占位文本；如果没有这段函数，历史遗留的 "None"/"null" 仍可能污染摘要。
    stripped = str(text or "").strip().lower()  # 新增代码+CompactNone污染: 统一清理大小写和空白；如果没有这行代码，" None " 或 "NULL" 会绕过过滤。
    return stripped in {"none", "null"}  # 新增代码+CompactNone污染: 返回是否为占位词；如果没有这行代码，摘要会把无意义占位当成阶段结论。


def _clip_finding_text(text: str, limit: int = ASSISTANT_FINDING_CHAR_LIMIT) -> str:  # 新增代码+CompactAssistantFindings: 函数段开始，裁剪单条 assistant 结论；如果没有这段函数，极长回复会让九段摘要过大。
    clean_text = _normalise_finding_text(text)  # 新增代码+CompactAssistantFindings: 先归一化文本；如果没有这行代码，裁剪位置会被无意义空白浪费。
    if len(clean_text) <= limit:  # 新增代码+CompactAssistantFindings: 短文本直接返回；如果没有这行代码，所有结论都会被强行加省略号。
        return clean_text  # 新增代码+CompactAssistantFindings: 返回完整短结论；如果没有这行代码，调用方拿不到未裁剪内容。
    return clean_text[:limit].rstrip() + "..."  # 新增代码+CompactAssistantFindings: 裁剪长结论并标记省略；如果没有这行代码，模型无法知道后面还有被压缩掉的细节。


def _collect_assistant_findings(messages: list[dict[str, Any]]) -> list[str]:  # 新增代码+CompactAssistantFindings: 函数段开始，收集最近 assistant 已确认的阶段结论；如果没有这段函数，compact 后只知道用户问过什么，不知道 agent 已经答出什么。
    findings: list[str] = []  # 新增代码+CompactAssistantFindings: 准备保存 assistant 结论列表；如果没有这行代码，后续循环没有收集容器。
    for message in messages:  # 新增代码+CompactAssistantFindings: 遍历待压缩消息；如果没有这行代码，无法从历史里找 assistant 回答。
        if not isinstance(message, dict):  # 新增代码+CompactAssistantFindings: 跳过坏消息结构；如果没有这行代码，异常消息可能让 compact 崩溃。
            continue  # 新增代码+CompactAssistantFindings: 坏消息不参与摘要；如果没有这行代码，后续字段读取会报错。
        if message.get("role") != "assistant":  # 新增代码+CompactAssistantFindings: 只抽取 assistant 结论；如果没有这行代码，用户原话和工具结果会混入阶段结论。
            continue  # 新增代码+CompactAssistantFindings: 非 assistant 消息跳过；如果没有这行代码，摘要语义会混乱。
        content = _message_content(message).strip()  # 新增代码+CompactAssistantFindings: 读取 assistant 正文；如果没有这行代码，无法判断和裁剪回答内容。
        if not content or _is_placeholder_finding_text(content) or _is_recursive_summary_text(content):  # 修改代码+CompactNone污染: 跳过空回答、None/null 占位和旧压缩摘要；如果没有这行代码，摘要会被无正文工具消息污染。
            continue  # 新增代码+CompactAssistantFindings: 无效 assistant 内容不保存；如果没有这行代码，findings 会出现无用条目。
        findings.append(_clip_finding_text(content))  # 新增代码+CompactAssistantFindings: 保存裁剪后的阶段结论；如果没有这行代码，上一轮关键结论不会进入 compact summary。
    return findings[-ASSISTANT_FINDING_MAX_COUNT:]  # 新增代码+CompactAssistantFindings: 只返回最近几条结论；如果没有这行代码，长期任务摘要会越来越臃肿。


def _deterministic_summary(messages: list[dict[str, Any]], task_state: TaskState, compact_reason: str) -> str:  # 新增代码+CompactSummarizer: 函数段开始，生成无需模型的兜底九段摘要；如果没有这段函数，compact 测试和紧急恢复会依赖真实 API。
    user_messages = _collect_user_messages(messages)  # 新增代码+CompactSummarizer: 收集所有用户消息；如果没有这行代码，All user messages 会缺失。
    assistant_findings = _collect_assistant_findings(messages)  # 新增代码+CompactAssistantFindings: 收集 assistant 已经确认过的阶段结论；如果没有这行代码，压缩后模型会忘记前面已经分析出的事实。
    assistant_findings_text = "；".join(assistant_findings) if assistant_findings else ""  # 新增代码+CompactAssistantFindings: 把阶段结论整理成一段文本；如果没有这行代码，后面每个摘要字段都要重复拼接。
    user_messages_text = " | ".join(user_messages) if user_messages else task_state.original_user_request or "未记录用户消息"  # 新增代码+CompactSummarizer: 生成用户消息文本；如果没有这行代码，空历史会导致摘要字段空白。
    completed_parts = list(task_state.completed_items)  # 新增代码+CompactAssistantFindings: 复制 TaskState 已完成事项；如果没有这行代码，不能把 assistant 阶段结论并入已完成内容。
    if assistant_findings_text:  # 新增代码+CompactAssistantFindings: 只有存在 assistant 结论时才追加；如果没有这行代码，空字符串会污染摘要。
        completed_parts.append(f"前文 assistant 已确认：{assistant_findings_text}")  # 新增代码+CompactAssistantFindings: 把上一轮结论写入已完成字段；如果没有这行代码，模型可能重复读文件确认已知事实。
    completed_text = "；".join(completed_parts) if completed_parts else "暂无明确完成项"  # 修改代码+CompactAssistantFindings: 用合并后的完成事项生成文本；如果没有这行代码，assistant 历史结论不会显示在 Current Work。
    pending_text = "；".join(task_state.pending_items) if task_state.pending_items else "继续完成当前用户目标"  # 新增代码+CompactSummarizer: 整理待办事项；如果没有这行代码，模型不知道还要做什么。
    fact_parts = list(task_state.key_facts)  # 新增代码+CompactAssistantFindings: 复制 TaskState 关键事实；如果没有这行代码，不能把 assistant 结论并入事实字段。
    if assistant_findings_text:  # 新增代码+CompactAssistantFindings: 只有存在 assistant 结论时才追加事实；如果没有这行代码，事实字段会多出空内容。
        fact_parts.append(f"前文 assistant 阶段结论：{assistant_findings_text}")  # 新增代码+CompactAssistantFindings: 保存上一轮 agent 已确认的事实；如果没有这行代码，compact 后会忘记原型已有功能和缺口。
    facts_text = "；".join(fact_parts) if fact_parts else "暂无额外关键事实"  # 修改代码+CompactAssistantFindings: 用合并后的事实生成文本；如果没有这行代码，Key Technical Concepts 仍然缺上一轮结论。
    evidence_parts = list(task_state.evidence_summaries)  # 新增代码+CompactAssistantFindings: 复制已有证据摘要；如果没有这行代码，assistant 结论无法并入解决过程证据。
    if assistant_findings_text:  # 新增代码+CompactAssistantFindings: 存在阶段结论才追加证据说明；如果没有这行代码，证据字段会出现空证据。
        evidence_parts.append(f"交互历史中的 assistant 输出已确认：{assistant_findings_text}")  # 新增代码+CompactAssistantFindings: 把历史回答作为软证据保留；如果没有这行代码，模型会反复读文件找同一批信息。
    evidence_text = "；".join(evidence_parts) if evidence_parts else "暂无工具证据摘要"  # 修改代码+CompactAssistantFindings: 用合并后的证据生成文本；如果没有这行代码，Problem Solving 仍然会显示没有证据。
    sections = {  # 新增代码+CompactSummarizer: 构造九段摘要内容；如果没有这行代码，标题和正文无法稳定对应。
        "Primary Request and Intent": task_state.original_user_request or task_state.current_goal or user_messages_text,  # 新增代码+CompactSummarizer: 第一段写用户主目标；如果没有这行代码，目标仍会丢失。
        "Key Technical Concepts": facts_text,  # 新增代码+CompactSummarizer: 第二段写关键事实/概念；如果没有这行代码，事实会丢。
        "Files and Code Sections": "本次摘要器未额外读取文件，只保留已进入上下文的文件线索。",  # 新增代码+CompactSummarizer: 第三段声明没有额外读文件；如果没有这行代码，模型可能以为 compact 已查过文件。
        "Errors and fixes": "若前文出现错误，请以后续工具证据和 TaskState 为准。",  # 新增代码+CompactSummarizer: 第四段给出错误处理原则；如果没有这行代码，模型可能重复旧错误。
        "Problem Solving": f"compact_reason={compact_reason}；关键证据：{evidence_text}",  # 新增代码+CompactSummarizer: 第五段写解决过程和证据；如果没有这行代码，模型会缺执行脉络。
        "All user messages": user_messages_text,  # 新增代码+CompactSummarizer: 第六段写用户消息；如果没有这行代码，多轮短句会丢。
        "Pending Tasks": pending_text,  # 新增代码+CompactSummarizer: 第七段写待办；如果没有这行代码，模型可能提前最终回答。
        "Current Work": f"已完成：{completed_text}；当前目标：{task_state.current_goal or task_state.original_user_request}",  # 新增代码+CompactSummarizer: 第八段写当前工作；如果没有这行代码，模型不知道做到哪一步。
        "Optional Next Step": task_state.next_step_hint or "基于已有任务状态继续推进，证据足够时输出最终回答。",  # 新增代码+CompactSummarizer: 第九段写下一步；如果没有这行代码，模型可能再次读日志恢复任务。
    }  # 新增代码+CompactSummarizer: 结束九段内容字典；如果没有这行代码，Python 字典语法不完整。
    return "\n\n".join(f"## {heading}\n{sections[heading]}" for heading in COMPACT_SECTION_HEADINGS)  # 新增代码+CompactSummarizer: 按固定标题顺序输出摘要；如果没有这行代码，质量检查器无法稳定识别九段合同。


def summarize_for_compact(messages: list[dict[str, Any]], task_state: TaskState, compact_reason: str, model: Any | None = None) -> CompactSummaryResult:  # 新增代码+CompactSummarizer: 函数段开始，执行 no-tools compact 摘要；如果没有这段函数，compact.py 仍会自己拼不合格摘要。
    prompt = build_compact_prompt(task_state, compact_reason)  # 新增代码+CompactSummarizer: 构造固定 no-tools prompt；如果没有这行代码，摘要器不会看到任务状态和九段合同。
    if model is None or not hasattr(model, "chat"):  # 新增代码+CompactSummarizer: 没有可用模型时走 deterministic fallback；如果没有这行代码，单元测试和紧急压缩会依赖真实模型。
        summary_text = _deterministic_summary(messages, task_state, compact_reason)  # 新增代码+CompactSummarizer: 生成本地九段摘要；如果没有这行代码，fallback 没有输出。
        return CompactSummaryResult(summary_text=summary_text, used_tools=False, model_name="deterministic_fallback", prompt_chars=len(prompt), summary_chars=len(summary_text), reason=compact_reason)  # 新增代码+CompactSummarizer: 返回无工具 fallback 结果；如果没有这行代码，调用方拿不到摘要结果。
    compact_messages = [{"role": "system", "content": prompt}, {"role": "user", "content": "请压缩以下上下文，不要调用工具：\n" + str(messages)}]  # 新增代码+CompactSummarizer: 构造给摘要模型的消息；如果没有这行代码，模型不知道要总结哪些上下文。
    model_message = model.chat(compact_messages, tools=[])  # 新增代码+CompactSummarizer: 用空工具列表调用模型；如果没有这行代码，no-tools 规则无法从协议层落实。
    tool_calls = list(getattr(model_message, "tool_calls", []) or [])  # 新增代码+CompactSummarizer: 读取模型是否违规请求工具；如果没有这行代码，质量检查无法发现违规。
    summary_text = str(getattr(model_message, "text", "") or "")  # 新增代码+CompactSummarizer: 读取模型摘要文本；如果没有这行代码，调用方拿不到模型输出。
    if not summary_text.strip():  # 新增代码+CompactSummarizer: 模型没有文本时使用 fallback；如果没有这行代码，空摘要会进入质量检查。
        summary_text = _deterministic_summary(messages, task_state, compact_reason)  # 新增代码+CompactSummarizer: 生成兜底摘要；如果没有这行代码，空响应会让 compact 失去上下文。
    model_name = type(model).__name__  # 新增代码+CompactSummarizer: 记录模型类名；如果没有这行代码，debug 无法知道摘要来源。
    return CompactSummaryResult(summary_text=summary_text, used_tools=bool(tool_calls), model_name=model_name, prompt_chars=len(prompt), summary_chars=len(summary_text), reason=compact_reason)  # 新增代码+CompactSummarizer: 返回摘要文本和是否违规调工具；如果没有这行代码，compact.py 无法做质量门禁。


__all__ = ["CompactSummaryResult", "summarize_for_compact"]  # 新增代码+CompactSummarizer: 明确公开接口；如果没有这行代码，其他模块导入边界不清。
