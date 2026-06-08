"""Resume v2 一致性修复报告。"""  # 新增代码+ResumeRepair: 说明本模块专门把损坏 transcript、中断 turn 和工具链断裂整理成审计报告；如果没有这行，恢复风险会散在 ResumeLoader 里。

from __future__ import annotations  # 新增代码+ResumeRepair: 延迟解析类型注解；如果没有这行，跨模块类型引用在部分环境更容易出问题。

from dataclasses import dataclass, field  # 新增代码+ResumeRepair: 用 dataclass 表达修复报告和默认列表；如果没有这行，报告会变成难维护的散乱 dict。
from typing import Any  # 新增代码+ResumeRepair: 标注 transcript payload 这种 JSON 式数据；如果没有这行，函数边界不清楚。

from learning_agent.core.transcript_v2 import TranscriptEntry  # 新增代码+ResumeRepair: 引入 transcript 条目类型；如果没有这行，修复器不知道输入事件结构。
from learning_agent.core.turn_ledger import TurnRecord  # 新增代码+ResumeRepair: 引入 turn 记录类型；如果没有这行，修复器无法识别中断轮次。

INCOMPLETE_TURN_STATUSES = {"accepted", "model_running", "tools_running", "interrupted", "failed", "compacted"}  # 新增代码+ResumeRepair: 定义需要复核的非最终状态；如果没有这行，恢复器可能把中断任务当成安全完成。


@dataclass  # 新增代码+ResumeRepair: 自动生成报告对象构造器；如果没有这行，需要写很多样板代码。
class ResumeRepairReport:  # 新增代码+ResumeRepair: 表示一次恢复前的一致性检查结果；如果没有这个类，UI/SDK 只能读不透明 dict。
    bad_transcript_line_count: int = 0  # 新增代码+ResumeRepair: 记录 transcript_v2.jsonl 里坏 JSON 行数量；如果没有这行，损坏证据会被静默跳过。
    missing_tool_result_count: int = 0  # 新增代码+ResumeRepair: 记录有 tool_use 但没有 tool_result 的数量；如果没有这行，危险副作用可能被重复执行。
    orphan_tool_result_count: int = 0  # 新增代码+ResumeRepair: 记录没有对应 tool_use 的孤儿 tool_result 数量；如果没有这行，消息链断裂无法被发现。
    interrupted_turn_count: int = 0  # 新增代码+ResumeRepair: 记录未完成或中断 turn 数量；如果没有这行，恢复无法判断是否要接着做。
    tombstones: list[dict[str, Any]] = field(default_factory=list)  # 新增代码+ResumeRepair: 保存不可直接重放的占位修复记录；如果没有这行，UI/SDK 不知道哪些事件被标成风险。
    warnings: list[str] = field(default_factory=list)  # 新增代码+ResumeRepair: 保存面向用户和 agent 的风险提示；如果没有这行，恢复状态只有数字不容易理解。
    resume_state: str = "resume_safe"  # 新增代码+ResumeRepair: 保存最终恢复状态；如果没有这行，主循环不知道是安全继续还是需要复核。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+ResumeRepair: 把报告转成 JSON 友好 dict；如果没有这行，状态工具不能直接返回报告。
        return {  # 新增代码+ResumeRepair: 返回完整报告字段；如果没有这行，调用方拿不到结构化数据。
            "bad_transcript_line_count": self.bad_transcript_line_count,  # 新增代码+ResumeRepair: 输出坏行数量；如果没有这行，坏 JSON 证据不可见。
            "missing_tool_result_count": self.missing_tool_result_count,  # 新增代码+ResumeRepair: 输出缺失工具结果数量；如果没有这行，工具链风险不可见。
            "orphan_tool_result_count": self.orphan_tool_result_count,  # 新增代码+ResumeRepair: 输出孤儿工具结果数量；如果没有这行，消息链风险不可见。
            "interrupted_turn_count": self.interrupted_turn_count,  # 新增代码+ResumeRepair: 输出中断 turn 数量；如果没有这行，长任务恢复风险不可见。
            "tombstones": list(self.tombstones),  # 新增代码+ResumeRepair: 输出 tombstone 列表；如果没有这行，坏链路没有可审计占位。
            "warnings": list(self.warnings),  # 新增代码+ResumeRepair: 输出风险提示；如果没有这行，用户和外部 agent 难以理解恢复状态。
            "resume_state": self.resume_state,  # 新增代码+ResumeRepair: 输出最终状态；如果没有这行，调用方无法统一判断。
        }  # 新增代码+ResumeRepair: 结束报告 dict；如果没有这行，Python 字典语法不完整。


def _tool_call_ids_from_entry(entry: TranscriptEntry) -> set[str]:  # 新增代码+ResumeRepair: 从模型事件中提取 tool_call id；如果没有这行，缺失工具结果无法检测。
    tool_calls = entry.payload.get("tool_calls", [])  # 新增代码+ResumeRepair: 读取 tool_calls 字段；如果没有这行，模型工具调用列表没有入口。
    if not isinstance(tool_calls, list):  # 新增代码+ResumeRepair: 防御坏 payload 把 tool_calls 写成非列表；如果没有这行，遍历会误处理字符串或 dict。
        return set()  # 新增代码+ResumeRepair: 坏格式时返回空集合；如果没有这行，恢复器可能崩溃。
    call_ids: set[str] = set()  # 新增代码+ResumeRepair: 准备收集调用 id；如果没有这行，函数没有返回容器。
    for call in tool_calls:  # 新增代码+ResumeRepair: 遍历每个工具调用；如果没有这行，只能检查第一条或完全不检查。
        if isinstance(call, dict):  # 新增代码+ResumeRepair: 只处理 dict 工具调用；如果没有这行，坏元素会触发属性错误。
            call_id = str(call.get("call_id") or call.get("id") or call.get("tool_call_id") or "")  # 新增代码+ResumeRepair: 兼容多种调用 id 字段；如果没有这行，不同模型格式会漏检。
            if call_id:  # 新增代码+ResumeRepair: 只保留非空 id；如果没有这行，空字符串会污染匹配集合。
                call_ids.add(call_id)  # 新增代码+ResumeRepair: 记录工具调用 id；如果没有这行，缺失结果无法计算。
    return call_ids  # 新增代码+ResumeRepair: 返回工具调用 id 集合；如果没有这行，调用方拿不到检测输入。


def _tool_result_id_from_entry(entry: TranscriptEntry) -> str:  # 新增代码+ResumeRepair: 从工具结果事件中提取 call_id；如果没有这行，孤儿结果无法检测。
    return str(entry.payload.get("call_id") or entry.payload.get("tool_call_id") or entry.payload.get("id") or "")  # 新增代码+ResumeRepair: 兼容多种结果 id 字段；如果没有这行，不同工具格式会漏检。


def build_resume_repair_report(entries: list[TranscriptEntry], turns: list[TurnRecord], bad_transcript_line_count: int) -> ResumeRepairReport:  # 新增代码+ResumeRepair: 构建完整恢复修复报告；如果没有这行，ResumeLoader 只能做浅层 summary 恢复。
    tool_use_ids: set[str] = set()  # 新增代码+ResumeRepair: 准备记录所有模型发出的工具调用；如果没有这行，缺失结果无法比较。
    tool_result_ids: set[str] = set()  # 新增代码+ResumeRepair: 准备记录所有工具返回结果；如果没有这行，孤儿结果无法比较。
    for entry in entries:  # 新增代码+ResumeRepair: 遍历 transcript 事件；如果没有这行，报告没有事件输入。
        if entry.event_type == "model_message":  # 新增代码+ResumeRepair: 模型消息可能包含 tool_calls；如果没有这行，工具调用不会被识别。
            tool_use_ids.update(_tool_call_ids_from_entry(entry))  # 新增代码+ResumeRepair: 收集工具调用 id；如果没有这行，missing_tool_result 永远为 0。
        if entry.event_type in {"tool_result", "tool_call_completed"}:  # 新增代码+ResumeRepair: 工具结果事件可能使用不同类型名；如果没有这行，部分工具结果会漏掉。
            result_id = _tool_result_id_from_entry(entry)  # 新增代码+ResumeRepair: 提取结果对应 id；如果没有这行，无法与 tool_use 匹配。
            if result_id:  # 新增代码+ResumeRepair: 只记录非空 id；如果没有这行，空 id 会影响集合比较。
                tool_result_ids.add(result_id)  # 新增代码+ResumeRepair: 保存工具结果 id；如果没有这行，orphan/missing 无法计算。
    missing_tool_ids = sorted(tool_use_ids - tool_result_ids)  # 新增代码+ResumeRepair: 找出有调用但无结果的工具 id；如果没有这行，危险副作用重复执行风险不可见。
    orphan_tool_ids = sorted(tool_result_ids - tool_use_ids)  # 新增代码+ResumeRepair: 找出有结果但无调用的工具 id；如果没有这行，消息链断裂风险不可见。
    interrupted_turns = [turn for turn in turns if turn.status in INCOMPLETE_TURN_STATUSES]  # 新增代码+ResumeRepair: 找出未安全完成的轮次；如果没有这行，中断恢复无法定位。
    tombstones: list[dict[str, Any]] = []  # 新增代码+ResumeRepair: 准备风险占位记录；如果没有这行，UI/SDK 没有可审计的修复对象。
    tombstones.extend({"kind": "missing_tool_result", "call_id": call_id} for call_id in missing_tool_ids)  # 新增代码+ResumeRepair: 为缺失工具结果生成 tombstone；如果没有这行，缺失副作用没有占位。
    tombstones.extend({"kind": "orphan_tool_result", "call_id": call_id} for call_id in orphan_tool_ids)  # 新增代码+ResumeRepair: 为孤儿工具结果生成 tombstone；如果没有这行，孤儿结果没有占位。
    tombstones.extend({"kind": "interrupted_turn", "turn_id": turn.turn_id, "status": turn.status, "checkpoint_uuid": turn.checkpoint_uuid} for turn in interrupted_turns)  # 新增代码+ResumeRepair: 为中断 turn 生成 tombstone；如果没有这行，长任务中断点不清楚。
    warnings: list[str] = []  # 新增代码+ResumeRepair: 准备风险提示列表；如果没有这行，报告只有数字缺少解释。
    if bad_transcript_line_count:  # 新增代码+ResumeRepair: 如果发现坏 JSON 行；如果没有这行，坏行风险不会转成提示。
        warnings.append("transcript_v2 存在坏 JSON 行，恢复时已跳过，需要人工复核原始文件。")  # 新增代码+ResumeRepair: 写入坏行提示；如果没有这行，用户不知道有证据损坏。
    if missing_tool_ids:  # 新增代码+ResumeRepair: 如果存在缺失工具结果；如果没有这行，缺失副作用风险不会提示。
        warnings.append("存在 model tool_call 没有对应 tool_result，恢复时不要盲目重跑危险工具。")  # 新增代码+ResumeRepair: 写入缺失结果提示；如果没有这行，外部 agent 可能重复执行工具。
    if orphan_tool_ids:  # 新增代码+ResumeRepair: 如果存在孤儿工具结果；如果没有这行，消息链断裂风险不会提示。
        warnings.append("存在没有对应 tool_call 的 tool_result，消息链需要人工复核。")  # 新增代码+ResumeRepair: 写入孤儿结果提示；如果没有这行，用户不知道链路断裂。
    if interrupted_turns:  # 新增代码+ResumeRepair: 如果存在中断 turn；如果没有这行，任务未完成风险不会提示。
        warnings.append("存在未安全完成的 turn，下一轮应从 checkpoint 继续而不是重跑已完成阶段。")  # 新增代码+ResumeRepair: 写入中断提示；如果没有这行，长任务可能重复执行。
    resume_state = "resume_needs_review" if bad_transcript_line_count or missing_tool_ids or orphan_tool_ids or interrupted_turns else "resume_safe"  # 新增代码+ResumeRepair: 根据风险计算最终状态；如果没有这行，主循环无法判断恢复是否安全。
    return ResumeRepairReport(bad_transcript_line_count=bad_transcript_line_count, missing_tool_result_count=len(missing_tool_ids), orphan_tool_result_count=len(orphan_tool_ids), interrupted_turn_count=len(interrupted_turns), tombstones=tombstones, warnings=warnings, resume_state=resume_state)  # 新增代码+ResumeRepair: 返回完整修复报告；如果没有这行，ResumeLoader 拿不到结果。
