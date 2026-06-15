"""compact 摘要质量门禁模块。"""  # 新增代码+CompactQuality: 说明本文件负责判断压缩摘要能不能进入主循环；如果没有这行代码，低质量摘要会继续污染模型上下文。

from __future__ import annotations  # 新增代码+CompactQuality: 延迟解析类型注解；如果没有这行代码，跨模块类型引用更容易受导入顺序影响。

from dataclasses import dataclass, field  # 新增代码+CompactQuality: 用数据类保存质量报告；如果没有这行代码，质量字段会散落成普通 dict。
from typing import Any  # 新增代码+CompactQuality: 接收摘要结果等宽松对象；如果没有这行代码，接口类型边界不清楚。

from learning_agent.core.compact_prompt import COMPACT_SECTION_HEADINGS  # 新增代码+CompactQuality: 复用固定九段标题；如果没有这行代码，质量检查和 prompt 合同可能分裂。
from learning_agent.core.task_state import TaskState  # 新增代码+CompactQuality: 读取任务状态事实源；如果没有这行代码，无法检查原始目标是否保留。


@dataclass  # 新增代码+CompactQuality: 自动生成质量报告初始化方法；如果没有这行代码，调用方要手写报告对象。
class CompactQualityReport:  # 新增代码+CompactQuality: 类段开始，表示 compact summary 是否合格；如果没有这个类，compact.py 无法审计质量失败原因。
    passed: bool  # 新增代码+CompactQuality: 保存质量检查是否通过；如果没有这行代码，compact.py 无法决定是否 fallback。
    missing_fields: list[str] = field(default_factory=list)  # 新增代码+CompactQuality: 保存缺失字段；如果没有这行代码，开发者不知道摘要为什么失败。
    reason: str = ""  # 新增代码+CompactQuality: 保存可读原因；如果没有这行代码，验收日志无法解释判断。
    summary_chars: int = 0  # 新增代码+CompactQuality: 保存摘要长度；如果没有这行代码，调试时不知道摘要是不是过短。
    used_tools: bool = False  # 新增代码+CompactQuality: 保存摘要阶段是否违规请求工具；如果没有这行代码，no-tools 门禁不可审计。
    nine_section_contract_passed: bool = False  # 新增代码+CompactQuality: 保存九段合同是否满足；如果没有这行代码，验收无法区分标题问题和内容问题。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+CompactQuality: 函数段开始，把报告转成 JSON 字典；如果没有这段函数，boundary 无法稳定保存质量报告。
        return {  # 新增代码+CompactQuality: 返回所有质量字段；如果没有这行代码，调用方拿不到结构化报告。
            "passed": self.passed,  # 新增代码+CompactQuality: 写出是否通过；如果没有这行代码，验收无法直接判断。
            "missing_fields": list(self.missing_fields),  # 新增代码+CompactQuality: 写出缺失字段列表；如果没有这行代码，失败原因会丢。
            "reason": self.reason,  # 新增代码+CompactQuality: 写出可读原因；如果没有这行代码，debug log 不好理解。
            "summary_chars": self.summary_chars,  # 新增代码+CompactQuality: 写出摘要长度；如果没有这行代码，过短摘要难以排查。
            "used_tools": self.used_tools,  # 新增代码+CompactQuality: 写出是否违规工具调用；如果没有这行代码，no-tools 验收无证据。
            "nine_section_contract_passed": self.nine_section_contract_passed,  # 新增代码+CompactQuality: 写出九段合同状态；如果没有这行代码，摘要结构问题不可见。
        }  # 新增代码+CompactQuality: 结束报告字典；如果没有这行代码，Python 字典语法不完整。


def _contains_meaningful_text(summary_text: str, expected_text: str) -> bool:  # 新增代码+CompactQuality: 函数段开始，检查摘要是否含关键文本；如果没有这段函数，原始目标检查会重复写。
    clean_expected = str(expected_text or "").strip()  # 新增代码+CompactQuality: 清理期望文本；如果没有这行代码，空白目标会造成误判。
    if not clean_expected:  # 新增代码+CompactQuality: 没有期望文本时不要求命中；如果没有这行代码，空字段会永远失败。
        return True  # 新增代码+CompactQuality: 空期望视为通过；如果没有这行代码，无原始目标测试会不可用。
    return clean_expected[:120] in summary_text or clean_expected in summary_text  # 新增代码+CompactQuality: 用前 120 字或全文命中即可；如果没有这行代码，长 prompt 截断会导致误失败。


def _looks_artifact_only(summary_text: str) -> bool:  # 新增代码+CompactQuality: 函数段开始，识别只有 artifact 或日志路径的低质量摘要；如果没有这段函数，旧导航摘要会继续混入。
    stripped = summary_text.strip()  # 新增代码+CompactQuality: 清理摘要空白；如果没有这行代码，空白会影响判断。
    if not stripped:  # 新增代码+CompactQuality: 空摘要肯定不合格；如果没有这行代码，空字符串可能被后续逻辑漏掉。
        return True  # 新增代码+CompactQuality: 返回低质量；如果没有这行代码，空摘要会进模型。
    lower_text = stripped.lower()  # 新增代码+CompactQuality: 转小写便于匹配路径关键词；如果没有这行代码，大小写会影响判断。
    path_markers = ["artifact", "transcript", "debug.log", "turns.json", ".jsonl", ".txt"]  # 新增代码+CompactQuality: 列出常见导航路径标记；如果没有这行代码，路径型摘要难以识别。
    has_path_marker = any(marker in lower_text for marker in path_markers)  # 新增代码+CompactQuality: 判断是否包含路径标记；如果没有这行代码，后续无法识别 artifact-only。
    has_section_heading = any(heading in stripped for heading in COMPACT_SECTION_HEADINGS)  # 新增代码+CompactQuality: 判断是否包含九段标题；如果没有这行代码，路径加合格标题会被误判。
    return has_path_marker and not has_section_heading and len(stripped) < 800  # 新增代码+CompactQuality: 路径标记多且短且无九段标题视为低质量；如果没有这行代码，旧 artifact 导航摘要会通过。


def _looks_recursive_compact_summary(summary_text: str) -> bool:  # 新增代码+CompactQuality: 函数段开始，识别 Compact Summary 套 Compact Summary；如果没有这段函数，递归摘要会越来越空。
    lower_text = summary_text.lower()  # 新增代码+CompactQuality: 转小写便于计数；如果没有这行代码，大小写会影响判断。
    return lower_text.count("compact summary") >= 2 and not any(heading in summary_text for heading in COMPACT_SECTION_HEADINGS)  # 新增代码+CompactQuality: 多次旧标题且无九段合同视为递归低质；如果没有这行代码，旧摘要会不断套娃。


def _extract_used_tools(summary_result: Any | None) -> bool:  # 新增代码+CompactQuality: 函数段开始，从可选摘要结果读取 used_tools；如果没有这段函数，质量检查不能识别压缩阶段违规调工具。
    return bool(getattr(summary_result, "used_tools", False)) if summary_result is not None else False  # 新增代码+CompactQuality: 返回 used_tools 布尔值；如果没有这行代码，None 输入会崩溃。


def validate_compact_summary(summary_text: str, task_state: TaskState, summary_result: Any | None = None) -> CompactQualityReport:  # 新增代码+CompactQuality: 函数段开始，检查 compact summary 是否能进入模型；如果没有这段函数，低质量摘要没有统一门禁。
    text = str(summary_text or "")  # 新增代码+CompactQuality: 统一摘要为字符串；如果没有这行代码，None 摘要会让检查崩溃。
    missing_fields: list[str] = []  # 新增代码+CompactQuality: 准备缺失字段列表；如果没有这行代码，无法汇总失败原因。
    used_tools = _extract_used_tools(summary_result)  # 新增代码+CompactQuality: 读取摘要阶段是否违规调工具；如果没有这行代码，no-tools 失败不会进入报告。
    nine_section_contract_passed = all(heading in text for heading in COMPACT_SECTION_HEADINGS)  # 新增代码+CompactQuality: 检查九段标题是否全部存在；如果没有这行代码，结构化摘要合同不受保护。
    if used_tools:  # 新增代码+CompactQuality: 如果摘要阶段请求了工具；如果没有这行代码，违规行为不会导致失败。
        missing_fields.append("no_tools_contract")  # 新增代码+CompactQuality: 记录 no-tools 失败；如果没有这行代码，报告看不出违规原因。
    if not nine_section_contract_passed:  # 新增代码+CompactQuality: 如果缺少九段标题；如果没有这行代码，摘要结构缺失不会失败。
        missing_fields.append("nine_section_contract")  # 新增代码+CompactQuality: 记录九段合同失败；如果没有这行代码，报告无法指导修复。
    if not _contains_meaningful_text(text, task_state.original_user_request):  # 新增代码+CompactQuality: 检查原始用户目标；如果没有这行代码，压缩后最重要的目标可能丢失。
        missing_fields.append("original_user_request")  # 新增代码+CompactQuality: 记录缺原始目标；如果没有这行代码，失败原因不具体。
    if not _contains_meaningful_text(text, task_state.current_goal):  # 新增代码+CompactQuality: 检查当前任务目标；如果没有这行代码，模型可能不知道现在要做什么。
        missing_fields.append("current_goal")  # 新增代码+CompactQuality: 记录缺当前目标；如果没有这行代码，报告不完整。
    if "Pending Tasks" not in text and "待完成" not in text:  # 新增代码+CompactQuality: 检查待办字段；如果没有这行代码，攻略这类剩余任务可能继续丢。
        missing_fields.append("pending_items")  # 新增代码+CompactQuality: 记录缺待办；如果没有这行代码，报告不说明漏什么。
    if "Current Work" not in text and "已完成" not in text:  # 新增代码+CompactQuality: 检查当前工作/已完成字段；如果没有这行代码，模型可能重复做已完成事项。
        missing_fields.append("completed_items")  # 新增代码+CompactQuality: 记录缺已完成；如果没有这行代码，报告不说明漏什么。
    if "Problem Solving" not in text and "关键证据" not in text and "暂无工具证据摘要" not in text:  # 新增代码+CompactQuality: 检查证据/解决过程字段；如果没有这行代码，模型会反复读日志找证据。
        missing_fields.append("evidence_summaries")  # 新增代码+CompactQuality: 记录缺证据；如果没有这行代码，报告不说明证据问题。
    if _looks_artifact_only(text):  # 新增代码+CompactQuality: 拒绝 artifact-only 摘要；如果没有这行代码，旧导航摘要会继续通过。
        missing_fields.append("artifact_only_summary")  # 新增代码+CompactQuality: 记录 artifact-only 问题；如果没有这行代码，失败原因不清。
    if _looks_recursive_compact_summary(text):  # 新增代码+CompactQuality: 拒绝递归旧摘要；如果没有这行代码，Compact Summary 套娃会继续恶化。
        missing_fields.append("recursive_compact_summary")  # 新增代码+CompactQuality: 记录递归摘要问题；如果没有这行代码，失败原因不清。
    passed = not missing_fields  # 新增代码+CompactQuality: 没有缺失字段才通过；如果没有这行代码，调用方无法得到总结果。
    reason = "compact summary 质量合格" if passed else "compact summary 质量不合格：" + "、".join(missing_fields)  # 新增代码+CompactQuality: 生成可读原因；如果没有这行代码，debug log 只有布尔值。
    return CompactQualityReport(passed=passed, missing_fields=missing_fields, reason=reason, summary_chars=len(text), used_tools=used_tools, nine_section_contract_passed=nine_section_contract_passed)  # 新增代码+CompactQuality: 返回完整质量报告；如果没有这行代码，compact.py 无法做 fallback。


def build_fallback_summary(task_state: TaskState, compact_reason: str) -> str:  # 新增代码+CompactQuality: 函数段开始，从 TaskState 生成兜底九段摘要；如果没有这段函数，低质量摘要失败后没有安全替代。
    state_summary = task_state.to_model_summary()  # 新增代码+CompactQuality: 先生成任务状态七段摘要；如果没有这行代码，fallback 会丢任务事实。
    sections = {  # 新增代码+CompactQuality: 构造九段 fallback 内容；如果没有这行代码，fallback 不能满足九段合同。
        "Primary Request and Intent": task_state.original_user_request or task_state.current_goal or "未记录原始用户目标",  # 新增代码+CompactQuality: 第一段保留原始目标；如果没有这行代码，fallback 仍会丢目标。
        "Key Technical Concepts": "以 TaskState 为事实源，优先保留用户目标、待办、关键事实和证据。",  # 新增代码+CompactQuality: 第二段说明核心概念；如果没有这行代码，摘要缺少技术背景。
        "Files and Code Sections": "fallback summary 未读取新文件，只使用已保存 TaskState。",  # 新增代码+CompactQuality: 第三段声明没有新文件读取；如果没有这行代码，模型可能误以为 compact 又查了文件。
        "Errors and fixes": "上一版 compact summary 质量不足，已使用 TaskState 兜底替代。",  # 新增代码+CompactQuality: 第四段记录修复动作；如果没有这行代码，摘要失败历史不可见。
        "Problem Solving": state_summary,  # 新增代码+CompactQuality: 第五段放完整任务状态；如果没有这行代码，fallback 信息太少。
        "All user messages": task_state.latest_user_input or task_state.original_user_request or "未记录用户消息",  # 新增代码+CompactQuality: 第六段保存用户消息；如果没有这行代码，多轮补充会丢。
        "Pending Tasks": "；".join(task_state.pending_items) if task_state.pending_items else "根据当前目标继续推进，证据足够时最终回答。",  # 新增代码+CompactQuality: 第七段保存待办；如果没有这行代码，未完成事项会丢。
        "Current Work": "；".join(task_state.completed_items) if task_state.completed_items else "当前依赖 TaskState 恢复任务状态。",  # 新增代码+CompactQuality: 第八段保存当前工作；如果没有这行代码，模型不知道已完成什么。
        "Optional Next Step": task_state.next_step_hint or f"compact_reason={compact_reason}；请基于 TaskState 继续，避免反复读日志恢复任务。",  # 新增代码+CompactQuality: 第九段给下一步；如果没有这行代码，模型可能继续读日志。
    }  # 新增代码+CompactQuality: 结束 fallback 内容字典；如果没有这行代码，Python 字典语法不完整。
    return "\n\n".join(f"## {heading}\n{sections[heading]}" for heading in COMPACT_SECTION_HEADINGS)  # 新增代码+CompactQuality: 按九段标题输出 fallback；如果没有这行代码，fallback 仍不满足质量合同。


__all__ = ["CompactQualityReport", "validate_compact_summary", "build_fallback_summary"]  # 新增代码+CompactQuality: 明确公开接口；如果没有这行代码，其他模块导入边界不清。
