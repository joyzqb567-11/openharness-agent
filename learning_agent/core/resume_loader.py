"""Resume Loader v2：从 summary、transcript、turn ledger 和 repair report 重建上下文。"""  # 新增代码+ResumeLoaderV2: 说明恢复器已经从简单读取升级为可审计恢复；如果没有这行，维护者会误以为这里仍只是读 summary。

from __future__ import annotations  # 新增代码+ResumeLoaderV2: 延迟解析类型注解；如果没有这行，跨类引用在部分 Python 版本会更脆弱。

import copy  # 新增代码+ResumeLoaderV2: 复制消息和 payload，避免恢复过程污染原始存储对象；如果没有这行，调用方修改返回值可能改坏缓存。
import json  # 新增代码+ResumeLoaderV2: 手动统计 JSONL 坏行需要解析 JSON；如果没有这行，坏 transcript 行无法被审计计数。
from dataclasses import dataclass, field  # 新增代码+ResumeLoaderV2: 用 dataclass 定义恢复上下文；如果没有这行，返回结构会变成难读 dict。
from pathlib import Path  # 新增代码+ResumeLoaderV2: 用 Path 管理 session 路径；如果没有这行，Windows 路径拼接更容易出错。
from typing import Any  # 新增代码+ResumeLoaderV2: 标注通用 JSON 消息和一致性报告；如果没有这行，接口边界不清楚。

from learning_agent.core.compact import CompactBoundary  # 新增代码+ResumeLoaderV2: 读取 compact boundary 类型；如果没有这行，最后压缩边界无法结构化恢复。
from learning_agent.core.resume_repair import ResumeRepairReport, build_resume_repair_report  # 新增代码+ResumeLoaderV2: 引入恢复修复报告；如果没有这行，坏行、缺工具结果和中断 turn 不会进入审计。
from learning_agent.core.session import SessionRecord, SessionStore  # 新增代码+ResumeLoaderV2: 读取 session summary；如果没有这行，恢复器无法优先使用已保存的摘要上下文。
from learning_agent.core.transcript_v2 import TranscriptEntry, TranscriptV2Store  # 新增代码+ResumeLoaderV2: 读取可回放 transcript v2；如果没有这行，恢复器看不到原始事件链。
from learning_agent.core.turn_ledger import TurnLedger  # 新增代码+ResumeLoaderV2: 读取 turn 状态账本；如果没有这行，中断轮次和 checkpoint 无法恢复。


@dataclass  # 新增代码+ResumeLoaderV2: 自动生成恢复上下文构造器；如果没有这行，需要手写大量样板代码。
class ResumeContext:  # 新增代码+ResumeLoaderV2: 表示一个 session 的完整可恢复上下文；如果没有这个类，调用方只能处理松散 dict。
    session_id: str  # 新增代码+ResumeLoaderV2: 保存被恢复的 session id；如果没有这行，状态工具不知道恢复目标。
    summary: SessionRecord | None  # 新增代码+ResumeLoaderV2: 保存 summary 记录或 None；如果没有这行，调用方不知道上下文来源是否有 summary。
    model_messages: list[dict[str, Any]] = field(default_factory=list)  # 新增代码+ResumeLoaderV2: 保存给下一轮模型使用的消息；如果没有这行，主循环无法继续任务。
    transcript_entries: list[TranscriptEntry] = field(default_factory=list)  # 新增代码+ResumeLoaderV2: 保存原始 transcript 事件；如果没有这行，审计证据不可见。
    last_boundary: CompactBoundary | None = None  # 新增代码+ResumeLoaderV2: 保存最后一个 compact 边界；如果没有这行，恢复无法解释旧上下文压缩点。
    repair_report: ResumeRepairReport = field(default_factory=ResumeRepairReport)  # 新增代码+ResumeLoaderV2: 保存恢复修复报告；如果没有这行，坏 transcript 和中断风险不会暴露。
    consistency: dict[str, Any] = field(default_factory=dict)  # 新增代码+ResumeLoaderV2: 保存面向 UI/SDK 的一致性摘要；如果没有这行，状态页无法快速展示恢复质量。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+ResumeLoaderV2: 把恢复上下文转成 JSON 友好 dict；如果没有这行，工具和 HTTP API 无法直接返回。
        return {  # 新增代码+ResumeLoaderV2: 返回完整恢复字段；如果没有这行，调用方拿不到结构化结果。
            "session_id": self.session_id,  # 新增代码+ResumeLoaderV2: 输出 session id；如果没有这行，外部 agent 不知道恢复对象。
            "summary": self.summary.to_dict() if self.summary is not None else None,  # 新增代码+ResumeLoaderV2: 输出 summary 或 None；如果没有这行，来源信息会丢失。
            "model_messages": copy.deepcopy(self.model_messages),  # 新增代码+ResumeLoaderV2: 输出模型消息副本；如果没有这行，调用方可能污染内部列表。
            "transcript_entries": [entry.to_dict() for entry in self.transcript_entries],  # 新增代码+ResumeLoaderV2: 输出 transcript 事件；如果没有这行，审计链不可见。
            "last_boundary": self.last_boundary.to_dict() if self.last_boundary is not None else None,  # 新增代码+ResumeLoaderV2: 输出最后 compact 边界；如果没有这行，压缩恢复信息会丢失。
            "repair_report": self.repair_report.to_dict(),  # 新增代码+ResumeLoaderV2: 输出修复报告；如果没有这行，坏行和中断风险无法给 UI/SDK。
            "consistency": dict(self.consistency),  # 新增代码+ResumeLoaderV2: 输出一致性摘要；如果没有这行，状态工具无法快速判断是否安全。
        }  # 新增代码+ResumeLoaderV2: 结束 JSON dict；如果没有这行，Python 语法不完整。


class ResumeLoader:  # 新增代码+ResumeLoaderV2: 管理 session 恢复流程；如果没有这个类，主循环、工具和 API 会各写一套恢复逻辑。
    def __init__(self, base_dir: str | Path) -> None:  # 新增代码+ResumeLoaderV2: 初始化持久化根目录；如果没有这行，调用方无法指定测试或生产 session 目录。
        self.base_dir = Path(base_dir)  # 新增代码+ResumeLoaderV2: 标准化根路径；如果没有这行，路径类型会混乱。
        self.session_store = SessionStore(self.base_dir)  # 新增代码+ResumeLoaderV2: 创建 summary store；如果没有这行，load 无法读取 session summary。
        self.transcript_store = TranscriptV2Store(self.base_dir)  # 新增代码+ResumeLoaderV2: 创建 transcript store；如果没有这行，load 无法回放 transcript_v2。
        self.turn_ledger = TurnLedger(self.base_dir)  # 新增代码+ResumeLoaderV2: 创建 turn ledger；如果没有这行，load 无法发现中断 turn。

    def load(self, session_id: str) -> ResumeContext:  # 新增代码+ResumeLoaderV2: 加载某个 session 的恢复上下文；如果没有这行，外部没有恢复入口。
        summary = self._load_summary_or_none(session_id)  # 新增代码+ResumeLoaderV2: 尝试读取 summary；如果没有这行，保存过的压缩上下文不会被复用。
        transcript_entries = self.transcript_store.list_entries(session_id)  # 新增代码+ResumeLoaderV2: 读取 transcript v2 事件；如果没有这行，恢复只剩 summary 旁路。
        turns = self.turn_ledger.list_turns(session_id)  # 新增代码+ResumeLoaderV2: 读取 turn 账本；如果没有这行，进程中断状态无法被发现。
        bad_line_count = self._count_bad_transcript_lines(session_id)  # 新增代码+ResumeLoaderV2: 统计 transcript 坏 JSON 行；如果没有这行，坏行会被 read_jsonl 静默跳过。
        last_boundary = self._last_compact_boundary(transcript_entries)  # 新增代码+ResumeLoaderV2: 找出最后 compact 边界；如果没有这行，恢复无法解释压缩点。
        model_messages = copy.deepcopy(summary.messages) if summary is not None else self._messages_from_transcript(transcript_entries)  # 新增代码+ResumeLoaderV2: 优先使用 summary，缺失时从 transcript 重建；如果没有这行，模型上下文可能为空。
        repair_report = build_resume_repair_report(transcript_entries, turns, bad_line_count)  # 新增代码+ResumeLoaderV2: 生成缺失工具结果、中断 turn 等报告；如果没有这行，恢复安全性不可审计。
        if repair_report.resume_state == "resume_needs_review":  # 新增代码+ResumeLoaderV2: 风险恢复时给模型明确继续提示；如果没有这行，下一轮模型不知道要从中断处继续而不是重跑。
            model_messages.append(self._continuation_message(repair_report))  # 新增代码+ResumeLoaderV2: 把继续任务提示写进上下文；如果没有这行，测试和真实恢复都缺少延续语义。
        consistency = self._build_consistency(summary, transcript_entries, last_boundary, model_messages, repair_report, turns)  # 新增代码+ResumeLoaderV2: 构建统一一致性摘要；如果没有这行，状态生态没有汇总字段。
        return ResumeContext(session_id=str(session_id), summary=summary, model_messages=model_messages, transcript_entries=transcript_entries, last_boundary=last_boundary, repair_report=repair_report, consistency=consistency)  # 新增代码+ResumeLoaderV2: 返回完整恢复上下文；如果没有这行，调用方拿不到结果。

    def _load_summary_or_none(self, session_id: str) -> SessionRecord | None:  # 新增代码+ResumeLoaderV2: 读取 summary 并把缺失或损坏转成 None；如果没有这行，坏 summary 会让恢复直接失败。
        try:  # 新增代码+ResumeLoaderV2: 捕获文件缺失和 JSON 问题；如果没有这行，恢复无法容错。
            return self.session_store.load_summary(session_id)  # 新增代码+ResumeLoaderV2: 读取正式 session summary；如果没有这行，已保存上下文无法恢复。
        except (FileNotFoundError, OSError, ValueError):  # 新增代码+ResumeLoaderV2: 兼容文件不存在、读取失败和解析失败；如果没有这行，恢复器会被单个坏文件拖垮。
            return None  # 新增代码+ResumeLoaderV2: 没有可用 summary 时返回 None；如果没有这行，调用方无法走 transcript fallback。

    def _count_bad_transcript_lines(self, session_id: str) -> int:  # 新增代码+ResumeLoaderV2: 统计 transcript_v2.jsonl 的坏行数量；如果没有这行，坏行不会进入修复报告。
        transcript_path = self.transcript_store.transcript_path(session_id)  # 新增代码+ResumeLoaderV2: 定位 transcript 文件；如果没有这行，无法扫描真实 JSONL。
        if not transcript_path.exists():  # 新增代码+ResumeLoaderV2: 文件不存在时没有坏行；如果没有这行，新 session 会因为缺文件报错。
            return 0  # 新增代码+ResumeLoaderV2: 返回 0 表示无坏行；如果没有这行，空 session 无法恢复。
        bad_count = 0  # 新增代码+ResumeLoaderV2: 准备坏行计数；如果没有这行，函数没有累积变量。
        for raw_line in transcript_path.read_text(encoding="utf-8").splitlines():  # 新增代码+ResumeLoaderV2: 按行读取 JSONL；如果没有这行，无法定位单行损坏。
            if not raw_line.strip():  # 新增代码+ResumeLoaderV2: 跳过空行；如果没有这行，手工空行会误判为坏 JSON。
                continue  # 新增代码+ResumeLoaderV2: 继续下一行；如果没有这行，空行会进入解析。
            try:  # 新增代码+ResumeLoaderV2: 捕获单行 JSON 错误；如果没有这行，一行坏数据会中断统计。
                parsed = json.loads(raw_line)  # 新增代码+ResumeLoaderV2: 尝试解析当前行；如果没有这行，无法判断是否坏 JSON。
            except json.JSONDecodeError:  # 新增代码+ResumeLoaderV2: 当前行不是合法 JSON；如果没有这行，坏行异常不会被计数。
                bad_count += 1  # 新增代码+ResumeLoaderV2: 累加坏行数量；如果没有这行，报告会漏掉损坏证据。
                continue  # 新增代码+ResumeLoaderV2: 跳过坏行继续扫描；如果没有这行，后续好行无法检查。
            if not isinstance(parsed, dict):  # 新增代码+ResumeLoaderV2: JSONL 事件必须是对象；如果没有这行，数组或字符串会被误认为正常事件。
                bad_count += 1  # 新增代码+ResumeLoaderV2: 非对象行也记为坏行；如果没有这行，结构损坏无法发现。
        return bad_count  # 新增代码+ResumeLoaderV2: 返回坏行总数；如果没有这行，修复报告拿不到输入。

    def _last_compact_boundary(self, entries: list[TranscriptEntry]) -> CompactBoundary | None:  # 新增代码+ResumeLoaderV2: 从 transcript 中找最后一个 compact 边界；如果没有这行，恢复无法说明压缩点。
        boundaries = [entry for entry in entries if entry.event_type == "compact_boundary"]  # 新增代码+ResumeLoaderV2: 筛选 compact_boundary 事件；如果没有这行，普通事件会被误解析。
        if not boundaries:  # 新增代码+ResumeLoaderV2: 没有 compact 时返回 None；如果没有这行，空列表访问会报错。
            return None  # 新增代码+ResumeLoaderV2: 明确表示没有边界；如果没有这行，调用方无法区分无 compact 和解析失败。
        return CompactBoundary.from_dict(boundaries[-1].payload)  # 新增代码+ResumeLoaderV2: 恢复最后一个边界对象；如果没有这行，状态工具拿不到边界字段。

    def _messages_from_transcript(self, entries: list[TranscriptEntry]) -> list[dict[str, Any]]:  # 新增代码+ResumeLoaderV2: summary 缺失时从 transcript 粗略重建模型消息；如果没有这行，坏 summary 后无法继续。
        messages: list[dict[str, Any]] = []  # 新增代码+ResumeLoaderV2: 准备消息列表；如果没有这行，函数没有返回容器。
        for entry in entries:  # 新增代码+ResumeLoaderV2: 遍历 transcript 事件；如果没有这行，无法生成任何消息。
            if entry.event_type == "user_message":  # 新增代码+ResumeLoaderV2: 识别用户消息；如果没有这行，用户输入不会恢复。
                messages.append({"role": "user", "content": str(entry.payload.get("content", ""))})  # 新增代码+ResumeLoaderV2: 转成模型 user 消息；如果没有这行，模型看不到用户历史。
            if entry.event_type == "model_message":  # 新增代码+ResumeLoaderV2: 识别模型消息；如果没有这行，assistant 历史不会恢复。
                messages.append({"role": "assistant", "content": str(entry.payload.get("content", entry.payload.get("text", "")))})  # 新增代码+ResumeLoaderV2: 转成 assistant 消息；如果没有这行，模型看不到已完成回答。
            if entry.event_type == "compact_boundary":  # 新增代码+ResumeLoaderV2: 识别 compact 边界；如果没有这行，压缩摘要不会回填。
                messages.append({"role": "system", "content": str(entry.payload.get("summary_text", ""))})  # 新增代码+ResumeLoaderV2: 把 compact 摘要放回 system 消息；如果没有这行，旧上下文说明丢失。
        return messages  # 新增代码+ResumeLoaderV2: 返回重建消息；如果没有这行，调用方拿不到上下文。

    def _continuation_message(self, repair_report: ResumeRepairReport) -> dict[str, str]:  # 新增代码+ResumeLoaderV2: 构造给模型的继续任务提示；如果没有这行，风险恢复时没有统一提示语。
        warning_text = "；".join(repair_report.warnings) if repair_report.warnings else "无额外警告"  # 新增代码+ResumeLoaderV2: 合并风险提示；如果没有这行，模型看不到为什么需要谨慎继续。
        content = f"Continue from where you left off. 恢复状态为 {repair_report.resume_state}。请从已有 checkpoint 继续，不要重跑已完成阶段；风险提示：{warning_text}"  # 新增代码+ResumeLoaderV2: 写出中英双语继续提示；如果没有这行，模型可能把恢复当成新任务。
        return {"role": "system", "content": content}  # 新增代码+ResumeLoaderV2: 返回 system 消息；如果没有这行，主循环无法插入恢复提示。

    def _build_consistency(self, summary: SessionRecord | None, entries: list[TranscriptEntry], boundary: CompactBoundary | None, messages: list[dict[str, Any]], repair_report: ResumeRepairReport, turns: list[Any]) -> dict[str, Any]:  # 新增代码+ResumeLoaderV2: 生成恢复一致性摘要；如果没有这行，状态页无法快速判断恢复质量。
        consistency = {  # 新增代码+ResumeLoaderV2: 创建统一一致性 dict；如果没有这行，后续字段没有容器。
            "summary_exists": summary is not None,  # 新增代码+ResumeLoaderV2: 标记是否有 summary；如果没有这行，来源可信度不可见。
            "transcript_entry_count": len(entries),  # 新增代码+ResumeLoaderV2: 记录 transcript 事件数量；如果没有这行，审计规模不可见。
            "turn_count": len(turns),  # 新增代码+ResumeLoaderV2: 记录 turn 数量；如果没有这行，状态页无法看出轮次规模。
            "has_compact_boundary": boundary is not None,  # 新增代码+ResumeLoaderV2: 标记是否有 compact 边界；如果没有这行，压缩恢复状态不可见。
            "last_boundary_uuid": boundary.boundary_uuid if boundary is not None else "",  # 新增代码+ResumeLoaderV2: 记录最后边界编号；如果没有这行，边界无法点击追溯。
            "message_count": len(messages),  # 新增代码+ResumeLoaderV2: 记录恢复后模型消息数量；如果没有这行，上下文大小不可见。
            "resume_safe": repair_report.resume_state == "resume_safe",  # 新增代码+ResumeLoaderV2: 保留旧字段兼容调用方；如果没有这行，旧工具会失去安全布尔值。
        }  # 新增代码+ResumeLoaderV2: 结束基础一致性字段；如果没有这行，Python dict 语法不完整。
        consistency.update(repair_report.to_dict())  # 新增代码+ResumeLoaderV2: 合并修复报告字段到顶层；如果没有这行，旧调用方拿不到 bad_line/missing_tool 等字段。
        return consistency  # 新增代码+ResumeLoaderV2: 返回一致性报告；如果没有这行，ResumeContext 没有 consistency。
