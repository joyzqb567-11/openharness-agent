"""可审计的多层 compact 模块。"""  # 新增代码+DeepCompact: 说明这个文件负责把长上下文压缩成可恢复、可审计的结构；如果没有这行，维护者不知道这里是 compact 的核心入口。

from __future__ import annotations  # 新增代码+DeepCompact: 让类型注解延迟解析，避免类还没创建时就解析自身类型；如果没有这行，部分 Python 版本会在类型引用上更脆弱。

import copy  # 新增代码+DeepCompact: 用来复制消息，避免压缩时改坏调用方手里的原始列表；如果没有这行，agent 历史消息可能被意外污染。
import secrets  # 新增代码+DeepCompact: 用来生成不可重复的 compact 边界编号；如果没有这行，多次压缩会难以审计区分。
from dataclasses import dataclass, field  # 新增代码+DeepCompact: 用 dataclass 清晰定义边界对象，并给列表字段默认值；如果没有这行，边界字段会散落在普通 dict 里。
from pathlib import Path  # 新增代码+DeepCompact: 用 Path 可靠处理 Windows 路径和 artifact 文件；如果没有这行，路径拼接容易出错。
from typing import Any  # 新增代码+DeepCompact: 标注 JSON 消息这种灵活结构；如果没有这行，接口类型边界会不清楚。

from learning_agent.core.compact_prompt import build_compact_user_summary_message  # 新增代码+ContextCompactRepair: 复用专用 compact 摘要消息格式；如果没有这行，TaskState 路径会继续用临时摘要文案。
from learning_agent.core.compact_quality import build_fallback_summary, validate_compact_summary  # 新增代码+ContextCompactRepair: 引入摘要质量检查和兜底摘要；如果没有这行，低质量 compact 会直接进入主循环。
from learning_agent.core.compact_summarizer import summarize_for_compact  # 新增代码+ContextCompactRepair: 引入 no-tools 专用压缩摘要器；如果没有这行，compact.py 只能自己拼导航摘要。
from learning_agent.core.post_compact_restore import build_post_compact_attachments  # 新增代码+ContextCompactRepair: 引入压缩后附件恢复；如果没有这行，模型 compact 后可能只剩摘要。
from learning_agent.core.task_state import TaskState  # 新增代码+ContextCompactRepair: 引入任务状态事实源；如果没有这行，compact 无法稳定保留用户原始目标。
from learning_agent.harness.models import utc_timestamp  # 新增代码+DeepCompact: 复用 harness 统一 UTC 时间戳；如果没有这行，compact 时间会和其他运行记录格式不一致。

COMPACT_SCHEMA_VERSION = 3  # 修改代码+ContextCompactRepair: 升级 compact boundary 协议以记录质量检查和恢复报告；如果没有这行，新旧边界字段无法区分。
TOOL_OUTPUT_INLINE_CHAR_LIMIT = 1500  # 新增代码+DeepCompact: 限制工具输出留在模型上下文里的长度；如果没有这行，超长工具结果仍会撑爆上下文。
TOOL_OUTPUT_SNIPPET_CHARS = 500  # 新增代码+DeepCompact: 保留一小段工具输出预览给模型理解；如果没有这行，模型只知道有文件但不知道大概内容。
MICRO_SUMMARY_CHAR_LIMIT = 1800  # 新增代码+DeepCompact: 限制微压缩摘要长度；如果没有这行，摘要本身也可能变得很长。
ORIGINAL_GOAL_ANCHOR_CHAR_LIMIT = 1200  # 新增代码+原始目标锚点: 限制原始用户目标锚点长度；如果没有这行，极长用户输入会再次撑大 compact 后上下文。


@dataclass  # 新增代码+DeepCompact: 自动生成构造函数和字段管理；如果没有这行，边界对象需要大量手写样板代码。
class CompactBoundary:  # 新增代码+DeepCompact: 表示一次 compact 的完整审计边界；如果没有这个类，resume 无法知道压缩了什么、为什么压缩。
    boundary_uuid: str  # 新增代码+DeepCompact: 保存本次压缩的唯一编号；如果没有这行，artifact、事件、恢复报告无法关联到同一次 compact。
    session_id: str  # 新增代码+DeepCompact: 保存所属会话；如果没有这行，多会话同时运行时 compact 记录会混在一起。
    run_id: str  # 新增代码+DeepCompact: 保存所属运行；如果没有这行，状态页面无法把 compact 归到具体任务运行。
    turn_id: str  # 新增代码+DeepCompact: 保存触发压缩的轮次；如果没有这行，中断恢复时不知道是哪一轮发生了压缩。
    original_message_count: int  # 新增代码+DeepCompact: 保存压缩前消息数量；如果没有这行，审计时无法判断压缩规模。
    removed_message_count: int  # 新增代码+DeepCompact: 保存被摘要覆盖的消息数量；如果没有这行，用户看不出有多少历史被折叠。
    retained_message_count: int  # 新增代码+DeepCompact: 保存仍原样保留的尾部消息数量；如果没有这行，resume 无法复核尾部上下文。
    summary_text: str  # 新增代码+DeepCompact: 保存写回模型上下文的摘要文本；如果没有这行，模型看不到历史上下文的压缩说明。
    reason: str = "message_count_limit"  # 新增代码+DeepCompact: 保存触发 compact 的原因；如果没有这行，状态和验收无法解释为什么压缩。
    created_at: str = ""  # 新增代码+DeepCompact: 保存创建时间；如果没有这行，事件时间线缺少 compact 的实际时刻。
    schema_version: int = COMPACT_SCHEMA_VERSION  # 新增代码+DeepCompact: 保存边界协议版本；如果没有这行，新旧 compact 格式无法稳定迁移。
    strategy_events: list[dict[str, Any]] = field(default_factory=list)  # 新增代码+DeepCompact: 记录 snip、microcompact、context collapse、autocompact 每一步；如果没有这行，compact 仍像黑盒。
    artifact_paths: list[str] = field(default_factory=list)  # 新增代码+DeepCompact: 记录长工具输出落盘位置；如果没有这行，被裁掉的原始证据可能找不回来。
    estimated_chars_before: int = 0  # 新增代码+DeepCompact: 保存压缩前估算字符数；如果没有这行，无法证明 compact 真的减少了上下文。
    estimated_chars_after: int = 0  # 新增代码+DeepCompact: 保存压缩后估算字符数；如果没有这行，状态页无法显示压缩收益。
    first_archived_index: int = -1  # 新增代码+DeepCompact: 保存被折叠历史的起始索引；如果没有这行，恢复报告无法定位被折叠范围。
    last_archived_index: int = -1  # 新增代码+DeepCompact: 保存被折叠历史的结束索引；如果没有这行，恢复报告无法定位被折叠范围。
    context_collapse_commit_uuid: str = ""  # 新增代码+DeepCompact: 保存 context collapse 提交编号；如果没有这行，后续恢复无法像 ClaudeCode 一样引用 collapse 提交。
    quality_passed: bool = True  # 新增代码+ContextCompactRepair: 保存最终摘要质量是否通过；如果没有这行，验收无法判断 compact 是否可靠。
    quality_missing_fields: list[str] = field(default_factory=list)  # 新增代码+ContextCompactRepair: 保存摘要缺失字段；如果没有这行，低质量摘要失败原因不可见。
    quality_reason: str = ""  # 新增代码+ContextCompactRepair: 保存质量检查说明；如果没有这行，debug 时只能看到布尔值。
    task_state_path: str = ""  # 新增代码+ContextCompactRepair: 保存任务状态落盘位置；如果没有这行，中断恢复时难以追溯事实源。
    post_compact_chars: int = 0  # 新增代码+ContextCompactRepair: 保存压缩后恢复附件字符数；如果没有这行，恢复成本不可审计。
    compact_generation: int = 0  # 新增代码+ContextCompactRepair: 保存第几代 compact；如果没有这行，链式压缩无法被区分。
    is_recompaction_in_chain: bool = False  # 新增代码+ContextCompactRepair: 标记是否链式重压缩；如果没有这行，重复压缩风险不可见。
    turns_since_previous_compact: int = 0  # 新增代码+ContextCompactRepair: 保存距离上次 compact 的轮数；如果没有这行，autocompact 熔断无法审计。
    restore_report: dict[str, Any] = field(default_factory=dict)  # 新增代码+ContextCompactRepair: 保存 post-compact 恢复报告；如果没有这行，恢复了哪些上下文不可验收。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+DeepCompact: 把边界对象转成可写入 JSONL 的 dict；如果没有这行，transcript 不能持久化 compact 细节。
        return {  # 新增代码+DeepCompact: 返回完整边界字段集合；如果没有这行，调用方拿不到结构化审计数据。
            "schema_version": self.schema_version,  # 新增代码+DeepCompact: 写出协议版本；如果没有这行，旧数据和新数据无法区分。
            "boundary_uuid": self.boundary_uuid,  # 新增代码+DeepCompact: 写出 compact 唯一编号；如果没有这行，artifact 和事件不能互相指向。
            "session_id": self.session_id,  # 新增代码+DeepCompact: 写出会话编号；如果没有这行，多会话恢复会混淆。
            "run_id": self.run_id,  # 新增代码+DeepCompact: 写出运行编号；如果没有这行，状态生态无法按 run 聚合。
            "turn_id": self.turn_id,  # 新增代码+DeepCompact: 写出轮次编号；如果没有这行，审计无法定位 compact 发生在哪一轮。
            "original_message_count": self.original_message_count,  # 新增代码+DeepCompact: 写出原始消息数量；如果没有这行，压缩规模不可见。
            "removed_message_count": self.removed_message_count,  # 新增代码+DeepCompact: 写出折叠消息数量；如果没有这行，用户不知道历史被压缩了多少。
            "retained_message_count": self.retained_message_count,  # 新增代码+DeepCompact: 写出保留消息数量；如果没有这行，恢复时无法确认尾部上下文。
            "summary_text": self.summary_text,  # 新增代码+DeepCompact: 写出摘要文本；如果没有这行，resume loader 无法重建模型上下文。
            "reason": self.reason,  # 新增代码+DeepCompact: 写出触发原因；如果没有这行，compact 会缺少可解释性。
            "created_at": self.created_at,  # 新增代码+DeepCompact: 写出创建时间；如果没有这行，时间线无法排序分析。
            "strategy_events": copy.deepcopy(self.strategy_events),  # 新增代码+DeepCompact: 写出每个策略阶段；如果没有这行，外部 agent 只能看到最终摘要。
            "artifact_paths": list(self.artifact_paths),  # 新增代码+DeepCompact: 写出 artifact 路径；如果没有这行，完整工具输出无法追溯。
            "estimated_chars_before": self.estimated_chars_before,  # 新增代码+DeepCompact: 写出压缩前字符量；如果没有这行，压缩收益无法计算。
            "estimated_chars_after": self.estimated_chars_after,  # 新增代码+DeepCompact: 写出压缩后字符量；如果没有这行，压缩收益无法计算。
            "first_archived_index": self.first_archived_index,  # 新增代码+DeepCompact: 写出折叠起始索引；如果没有这行，恢复报告定位不完整。
            "last_archived_index": self.last_archived_index,  # 新增代码+DeepCompact: 写出折叠结束索引；如果没有这行，恢复报告定位不完整。
            "context_collapse_commit_uuid": self.context_collapse_commit_uuid,  # 新增代码+DeepCompact: 写出 collapse 提交编号；如果没有这行，collapse 结果无法被后续引用。
            "quality_passed": self.quality_passed,  # 新增代码+ContextCompactRepair: 写出摘要质量结果；如果没有这行，外部验收无法看到 compact 是否合格。
            "quality_missing_fields": list(self.quality_missing_fields),  # 新增代码+ContextCompactRepair: 写出缺失字段；如果没有这行，摘要失败无法定位。
            "quality_reason": self.quality_reason,  # 新增代码+ContextCompactRepair: 写出质量说明；如果没有这行，排查时只剩通过或失败。
            "task_state_path": self.task_state_path,  # 新增代码+ContextCompactRepair: 写出任务状态路径；如果没有这行，恢复链路缺少事实源位置。
            "post_compact_chars": self.post_compact_chars,  # 新增代码+ContextCompactRepair: 写出恢复附件字符数；如果没有这行，compact 后上下文大小不可审计。
            "compact_generation": self.compact_generation,  # 新增代码+ContextCompactRepair: 写出 compact 代次；如果没有这行，链式 compact 记录会混在一起。
            "is_recompaction_in_chain": self.is_recompaction_in_chain,  # 新增代码+ContextCompactRepair: 写出链式重压缩标记；如果没有这行，频繁压缩风险不清楚。
            "turns_since_previous_compact": self.turns_since_previous_compact,  # 新增代码+ContextCompactRepair: 写出距离上次压缩轮数；如果没有这行，熔断策略不可审计。
            "restore_report": copy.deepcopy(self.restore_report),  # 新增代码+ContextCompactRepair: 写出恢复报告；如果没有这行，验收无法知道恢复了哪些附件。
        }  # 新增代码+DeepCompact: 结束 JSON 字段返回；如果没有这行，Python 字典语法不完整。

    @classmethod  # 新增代码+DeepCompact: 提供类级恢复入口；如果没有这行，调用方要自己手动清洗 dict。
    def from_dict(cls, payload: dict[str, Any]) -> "CompactBoundary":  # 新增代码+DeepCompact: 从持久化 dict 恢复边界对象；如果没有这行，resume loader 只能处理散乱字段。
        safe_payload = payload if isinstance(payload, dict) else {}  # 新增代码+DeepCompact: 防御坏 payload；如果没有这行，损坏 transcript 会让恢复直接崩溃。
        return cls(  # 新增代码+DeepCompact: 构造兼容新旧字段的 CompactBoundary；如果没有这行，旧边界无法升级读取。
            boundary_uuid=str(safe_payload.get("boundary_uuid", "")),  # 新增代码+DeepCompact: 恢复唯一编号；如果没有这行，边界会失去身份。
            session_id=str(safe_payload.get("session_id", "")),  # 新增代码+DeepCompact: 恢复会话编号；如果没有这行，边界无法归属 session。
            run_id=str(safe_payload.get("run_id", "")),  # 新增代码+DeepCompact: 恢复运行编号；如果没有这行，边界无法归属 run。
            turn_id=str(safe_payload.get("turn_id", "")),  # 新增代码+DeepCompact: 恢复轮次编号；如果没有这行，边界无法归属 turn。
            original_message_count=int(safe_payload.get("original_message_count", 0)),  # 新增代码+DeepCompact: 恢复压缩前数量；如果没有这行，审计规模为空。
            removed_message_count=int(safe_payload.get("removed_message_count", 0)),  # 新增代码+DeepCompact: 恢复折叠数量；如果没有这行，恢复报告缺少范围信息。
            retained_message_count=int(safe_payload.get("retained_message_count", 0)),  # 新增代码+DeepCompact: 恢复保留数量；如果没有这行，尾部上下文不可校验。
            summary_text=str(safe_payload.get("summary_text", "")),  # 新增代码+DeepCompact: 恢复摘要文本；如果没有这行，模型上下文无法重建 compact 摘要。
            reason=str(safe_payload.get("reason", "message_count_limit")),  # 新增代码+DeepCompact: 恢复触发原因；如果没有这行，状态说明会丢失。
            created_at=str(safe_payload.get("created_at", "")),  # 新增代码+DeepCompact: 恢复创建时间；如果没有这行，时间线会断。
            schema_version=int(safe_payload.get("schema_version", 1)),  # 新增代码+DeepCompact: 恢复协议版本，旧数据默认 v1；如果没有这行，迁移逻辑无法判断旧格式。
            strategy_events=list(safe_payload.get("strategy_events", [])),  # 新增代码+DeepCompact: 恢复策略阶段；如果没有这行，多层 compact 证据会丢失。
            artifact_paths=[str(path) for path in safe_payload.get("artifact_paths", [])],  # 新增代码+DeepCompact: 恢复 artifact 路径；如果没有这行，长工具输出无法追溯。
            estimated_chars_before=int(safe_payload.get("estimated_chars_before", 0)),  # 新增代码+DeepCompact: 恢复压缩前字符量；如果没有这行，收益计算为空。
            estimated_chars_after=int(safe_payload.get("estimated_chars_after", 0)),  # 新增代码+DeepCompact: 恢复压缩后字符量；如果没有这行，收益计算为空。
            first_archived_index=int(safe_payload.get("first_archived_index", -1)),  # 新增代码+DeepCompact: 恢复折叠起点；如果没有这行，范围定位不完整。
            last_archived_index=int(safe_payload.get("last_archived_index", -1)),  # 新增代码+DeepCompact: 恢复折叠终点；如果没有这行，范围定位不完整。
            context_collapse_commit_uuid=str(safe_payload.get("context_collapse_commit_uuid", "")),  # 新增代码+DeepCompact: 恢复 collapse 提交编号；如果没有这行，collapse 链路会断。
            quality_passed=bool(safe_payload.get("quality_passed", True)),  # 新增代码+ContextCompactRepair: 恢复摘要质量结果；如果没有这行，旧边界之外的新验收字段会丢。
            quality_missing_fields=[str(field_name) for field_name in safe_payload.get("quality_missing_fields", [])],  # 新增代码+ContextCompactRepair: 恢复缺失字段列表；如果没有这行，失败原因会丢。
            quality_reason=str(safe_payload.get("quality_reason", "")),  # 新增代码+ContextCompactRepair: 恢复质量说明；如果没有这行，排查信息会丢。
            task_state_path=str(safe_payload.get("task_state_path", "")),  # 新增代码+ContextCompactRepair: 恢复任务状态路径；如果没有这行，事实源位置会丢。
            post_compact_chars=int(safe_payload.get("post_compact_chars", 0)),  # 新增代码+ContextCompactRepair: 恢复附件字符数；如果没有这行，预算信息会丢。
            compact_generation=int(safe_payload.get("compact_generation", 0)),  # 新增代码+ContextCompactRepair: 恢复 compact 代次；如果没有这行，链式压缩不可追踪。
            is_recompaction_in_chain=bool(safe_payload.get("is_recompaction_in_chain", False)),  # 新增代码+ContextCompactRepair: 恢复链式重压缩标记；如果没有这行，重复压缩风险会丢。
            turns_since_previous_compact=int(safe_payload.get("turns_since_previous_compact", 0)),  # 新增代码+ContextCompactRepair: 恢复距离上次压缩轮数；如果没有这行，熔断信息会丢。
            restore_report=copy.deepcopy(safe_payload.get("restore_report", {})) if isinstance(safe_payload.get("restore_report", {}), dict) else {},  # 新增代码+ContextCompactRepair: 恢复附件报告；如果没有这行，post-compact 恢复证据会丢。
        )  # 新增代码+DeepCompact: 结束边界构造；如果没有这行，Python 调用语法不完整。


def estimate_messages_chars(messages: list[dict[str, Any]]) -> int:  # 新增代码+DeepCompact: 粗略估算消息 content 字符量；如果没有这行，compact 不能判断上下文是否过大。
    return sum(len(str(message.get("content", ""))) for message in messages if isinstance(message, dict))  # 新增代码+DeepCompact: 累加每条消息 content 长度；如果没有这行，压缩前后收益无法量化。


def should_compact_messages(messages: list[dict[str, Any]], max_messages: int = 20, max_chars: int = 60_000) -> bool:  # 新增代码+DeepCompact: 判断是否需要主动 compact；如果没有这行，主循环会缺少统一压缩策略。
    safe_max_messages = max(2, int(max_messages))  # 新增代码+DeepCompact: 确保消息数量阈值至少能放摘要和一条尾部消息；如果没有这行，错误配置会让 compact 结果不可用。
    safe_max_chars = max(100, int(max_chars))  # 新增代码+DeepCompact: 确保字符阈值有合理下限；如果没有这行，0 或负数会导致短上下文反复压缩。
    return len(messages) > safe_max_messages or estimate_messages_chars(messages) > safe_max_chars  # 新增代码+DeepCompact: 数量或字符任一超限就需要 compact；如果没有这行，长任务会继续堆到模型报错。


def _message_content(message: dict[str, Any]) -> str:  # 新增代码+DeepCompact: 安全提取消息正文；如果没有这行，不同消息结构会在多个地方重复处理。
    return str(message.get("content", "")) if isinstance(message, dict) else ""  # 新增代码+DeepCompact: 非 dict 消息返回空字符串；如果没有这行，坏消息会让 compact 崩溃。


def _is_tool_like_message(message: dict[str, Any]) -> bool:  # 新增代码+DeepCompact: 判断消息是否像工具输出；如果没有这行，长工具结果无法被优先落盘。
    return bool(message.get("role") == "tool" or message.get("tool_call_id") or message.get("name"))  # 新增代码+DeepCompact: role/tool_call_id/name 任一命中就视为工具相关；如果没有这行，部分工具格式会漏掉。


def _write_artifact(artifact_dir: Path, boundary_uuid: str, message_index: int, content: str) -> Path:  # 新增代码+DeepCompact: 把完整长输出写入 artifact 文件；如果没有这行，snip 后原始证据会丢失。
    artifact_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+DeepCompact: 确保 artifact 目录存在；如果没有这行，第一次写文件会因为目录不存在失败。
    artifact_path = artifact_dir / f"{boundary_uuid}_message_{message_index}.txt"  # 新增代码+DeepCompact: 生成稳定可读的 artifact 文件名；如果没有这行，外部 agent 不知道哪个文件对应哪条消息。
    artifact_path.write_text(content, encoding="utf-8")  # 新增代码+DeepCompact: 用 UTF-8 写出完整内容；如果没有这行，被 snip 的长输出无法审计复原。
    return artifact_path  # 新增代码+DeepCompact: 返回文件路径给边界记录；如果没有这行，调用方无法把 artifact 挂到 boundary。


def _record_strategy(strategy_events: list[dict[str, Any]], stage: str, detail: dict[str, Any]) -> None:  # 新增代码+DeepCompact: 统一记录 compact 策略阶段；如果没有这行，阶段 payload 会散在各处不一致。
    event = {"stage": stage, "detail": copy.deepcopy(detail), "created_at": utc_timestamp()}  # 新增代码+DeepCompact: 构造带阶段名、详情、时间的事件；如果没有这行，审计记录缺少必要字段。
    strategy_events.append(event)  # 新增代码+DeepCompact: 把阶段追加到 boundary；如果没有这行，状态页看不到发生过什么压缩动作。


def _snip_long_tool_outputs(messages: list[dict[str, Any]], artifact_dir: Path | None, boundary_uuid: str, strategy_events: list[dict[str, Any]], artifact_paths: list[str]) -> list[dict[str, Any]]:  # 新增代码+DeepCompact: 裁短长工具输出并落盘；如果没有这行，工具结果会继续占满模型上下文。
    snipped_messages = copy.deepcopy(messages)  # 新增代码+DeepCompact: 复制消息后再改写；如果没有这行，原始 messages 会被 snip 污染。
    for index, message in enumerate(snipped_messages):  # 新增代码+DeepCompact: 逐条检查消息；如果没有这行，无法发现具体哪条工具输出过长。
        content = _message_content(message)  # 新增代码+DeepCompact: 读取消息正文；如果没有这行，后续长度判断没有输入。
        if not _is_tool_like_message(message) or len(content) <= TOOL_OUTPUT_INLINE_CHAR_LIMIT:  # 新增代码+DeepCompact: 只处理超长工具类消息；如果没有这行，普通短消息也会被错误裁剪。
            continue  # 新增代码+DeepCompact: 跳过不需要 snip 的消息；如果没有这行，循环会继续执行错误的落盘逻辑。
        artifact_path = _write_artifact(artifact_dir, boundary_uuid, index, content) if artifact_dir is not None else None  # 新增代码+DeepCompact: 有目录就写完整 artifact；如果没有这行，长输出没有外部证据文件。
        artifact_path_text = str(artifact_path) if artifact_path is not None else ""  # 新增代码+DeepCompact: 把路径转成 JSON 友好的字符串；如果没有这行，boundary 不能稳定序列化。
        if artifact_path_text:  # 新增代码+DeepCompact: 只有实际写文件才记录路径；如果没有这行，空路径会污染 artifact 列表。
            artifact_paths.append(artifact_path_text)  # 新增代码+DeepCompact: 把 artifact 路径加入边界；如果没有这行，状态和 resume 找不到完整输出。
        snippet = content[:TOOL_OUTPUT_SNIPPET_CHARS]  # 新增代码+DeepCompact: 取一小段预览留给模型；如果没有这行，模型完全不知道工具输出内容概貌。
        message["content"] = f"[tool_output_snip] 完整工具输出已落盘，artifact_path={artifact_path_text}，原始字符数={len(content)}，预览={snippet}"  # 新增代码+DeepCompact: 用短说明替换超长输出；如果没有这行，压缩后仍可能把完整输出塞回模型。
        _record_strategy(strategy_events, "tool_output_snip", {"message_index": index, "original_chars": len(content), "inline_chars": len(str(message.get("content", ""))), "artifact_path": artifact_path_text})  # 新增代码+DeepCompact: 记录 snip 证据；如果没有这行，审计无法证明工具输出被安全处理。
    return snipped_messages  # 新增代码+DeepCompact: 返回处理后的消息列表；如果没有这行，后续 microcompact 拿不到裁短结果。


def _build_micro_summary(messages: list[dict[str, Any]]) -> str:  # 新增代码+DeepCompact: 为较早历史构造轻量摘要；如果没有这行，compact 只能粗暴丢弃旧消息。
    summary_parts: list[str] = []  # 新增代码+DeepCompact: 准备摘要片段列表；如果没有这行，摘要文本无法逐段累积。
    for index, message in enumerate(messages):  # 新增代码+DeepCompact: 遍历被折叠的旧消息；如果没有这行，摘要不知道历史里有什么。
        role = str(message.get("role", "unknown"))  # 新增代码+DeepCompact: 记录消息角色；如果没有这行，摘要会丢失 user/assistant/tool 的区别。
        content = _message_content(message).replace("\n", " ")  # 新增代码+DeepCompact: 把多行内容压成一行预览；如果没有这行，摘要可能变得不易读。
        summary_parts.append(f"{index}:{role}:{content[:220]}")  # 新增代码+DeepCompact: 添加一条短历史片段；如果没有这行，旧消息不会进入摘要。
        if len("\n".join(summary_parts)) >= MICRO_SUMMARY_CHAR_LIMIT:  # 新增代码+DeepCompact: 控制微摘要总长度；如果没有这行，摘要可能再次过长。
            break  # 新增代码+DeepCompact: 达到长度上限就停止；如果没有这行，摘要会继续增长。
    return "\n".join(summary_parts)[:MICRO_SUMMARY_CHAR_LIMIT]  # 新增代码+DeepCompact: 返回被限制长度的微摘要；如果没有这行，autocompact 没有摘要输入。


def _compact_summary_text(session_id: str, run_id: str, turn_id: str, removed_count: int, original_count: int, reason: str, micro_summary: str, artifact_paths: list[str], collapse_commit_uuid: str) -> str:  # 新增代码+DeepCompact: 生成模型可读 compact 摘要；如果没有这行，摘要文案会分散且难维护。
    artifact_note = ", ".join(artifact_paths) if artifact_paths else "无单独 artifact"  # 新增代码+DeepCompact: 生成 artifact 提示；如果没有这行，模型和用户不知道长输出是否落盘。
    return f"Compact Summary: session_id={session_id}; run_id={run_id}; turn_id={turn_id}; reason={reason}; 已折叠 {removed_count}/{original_count} 条较早消息；context_collapse_commit={collapse_commit_uuid}; artifacts={artifact_note}; 微摘要如下：\n{micro_summary}\n请把这段摘要当作导航线索，真实证据以 transcript_v2、artifact 和状态事件为准。"  # 新增代码+DeepCompact: 返回带审计提示的摘要文本；如果没有这行，模型会丢失旧上下文的可追溯说明。


def _find_original_user_goal(messages: list[dict[str, Any]]) -> str:  # 新增代码+原始目标锚点: 从完整消息里寻找本轮第一条用户目标；如果没有这行，compact 无法稳定知道要保护哪句话。
    for message in messages:  # 新增代码+原始目标锚点: 按时间顺序扫描消息；如果没有这行，可能误把后续噪声当成原始目标。
        if not isinstance(message, dict):  # 新增代码+原始目标锚点: 跳过坏消息结构；如果没有这行，异常消息会让 compact 崩溃。
            continue  # 新增代码+原始目标锚点: 坏消息不参与目标识别；如果没有这行，后续 role 判断会拿到无效对象。
        if str(message.get("role", "")) != "user":  # 新增代码+原始目标锚点: 只把用户消息当成任务来源；如果没有这行，系统提示或工具输出可能被误认为用户目标。
            continue  # 新增代码+原始目标锚点: 非用户消息直接跳过；如果没有这行，第一条系统消息可能覆盖真实目标。
        content = _message_content(message).strip()  # 新增代码+原始目标锚点: 提取并清理用户原话；如果没有这行，空白内容也可能进入锚点。
        if content:  # 新增代码+原始目标锚点: 只接受非空用户目标；如果没有这行，空用户消息会挡住后面的真实目标。
            return content[:ORIGINAL_GOAL_ANCHOR_CHAR_LIMIT]  # 新增代码+原始目标锚点: 返回长度受控的原始目标；如果没有这行，长 prompt 会破坏压缩预算。
    return ""  # 新增代码+原始目标锚点: 没有用户目标时返回空字符串；如果没有这行，无用户消息场景会没有明确结果。


def _build_original_goal_anchor_message(original_goal: str) -> dict[str, Any] | None:  # 新增代码+原始目标锚点: 构造压缩后固定保留的目标提示；如果没有这行，目标锚点逻辑会散落在主 compact 分支里。
    safe_goal = str(original_goal).strip()[:ORIGINAL_GOAL_ANCHOR_CHAR_LIMIT]  # 新增代码+原始目标锚点: 再次清理并限制目标长度；如果没有这行，调用方传入超长文本会绕过保护。
    if not safe_goal:  # 新增代码+原始目标锚点: 没有目标时不生成锚点；如果没有这行，模型会看到空目标提示而更困惑。
        return None  # 新增代码+原始目标锚点: 返回 None 让调用方保持原压缩结构；如果没有这行，空目标也会占用消息预算。
    anchor_text = f"本轮原始用户目标：\n{safe_goal}\n请始终围绕这个目标判断是否继续调用工具；已有证据足够时，直接整理最终回答，不要因为尾部上下文缺少原始问题而改写任务。"  # 新增代码+原始目标锚点: 写入人话版目标守卫；如果没有这行，agent 可能像验收日志里那样忘记用户要天气和3天攻略。
    return {"role": "system", "content": anchor_text}  # 新增代码+原始目标锚点: 用 system 消息承载锚点；如果没有这行，模型可能把锚点误认为新的用户补充。


def compact_messages_with_boundary(messages: list[dict[str, Any]], session_id: str, run_id: str, turn_id: str, max_messages: int = 20, reason: str = "message_count_limit", artifact_dir: str | Path | None = None, task_state: TaskState | None = None, compact_model: Any | None = None, recent_runtime_state: dict[str, Any] | None = None, task_state_path: str = "", compact_generation: int | None = None, is_recompaction_in_chain: bool = False, turns_since_previous_compact: int = 0) -> tuple[list[dict[str, Any]], CompactBoundary]:  # 修改代码+ContextCompactRepair: 扩展 compact 入口接收任务状态、摘要模型和恢复状态；如果没有这行，主循环无法使用成熟 compact 闭环。
    safe_limit = max(3, int(max_messages))  # 修改代码+原始目标锚点: 确保至少能放摘要、原始目标锚点和一条尾部消息；如果没有这行，目标保护会挤掉最新上下文或突破预算。
    boundary_uuid = f"compact_{secrets.token_hex(12)}"  # 新增代码+DeepCompact: 先生成边界编号用于 artifact 命名；如果没有这行，artifact 和 boundary 不能提前绑定。
    original_messages = copy.deepcopy(messages)  # 新增代码+DeepCompact: 保留原始消息副本用于计数和估算；如果没有这行，后续改写后无法知道压缩前状态。
    strategy_events: list[dict[str, Any]] = []  # 新增代码+DeepCompact: 准备策略事件列表；如果没有这行，边界无法记录多层压缩过程。
    artifact_paths: list[str] = []  # 新增代码+DeepCompact: 准备 artifact 路径列表；如果没有这行，长输出文件无法挂到边界。
    resolved_artifact_dir = Path(artifact_dir) if artifact_dir is not None else None  # 新增代码+DeepCompact: 标准化 artifact 目录；如果没有这行，字符串路径和 Path 路径会分散处理。
    estimated_before = estimate_messages_chars(original_messages)  # 新增代码+DeepCompact: 计算压缩前字符量；如果没有这行，无法证明 compact 有效果。
    snipped_messages = _snip_long_tool_outputs(original_messages, resolved_artifact_dir, boundary_uuid, strategy_events, artifact_paths)  # 新增代码+DeepCompact: 先处理长工具输出；如果没有这行，后面的摘要仍可能包含巨大工具结果。
    collapse_commit_uuid = f"collapse_{secrets.token_hex(8)}"  # 新增代码+DeepCompact: 生成 context collapse 提交编号；如果没有这行，resume 无法引用这次 collapse。
    quality_passed = True  # 新增代码+ContextCompactRepair: 默认兼容旧 compact 路径为质量通过；如果没有这行，未启用 TaskState 的旧调用会缺少默认值。
    quality_missing_fields: list[str] = []  # 新增代码+ContextCompactRepair: 准备摘要缺失字段列表；如果没有这行，boundary 构造时字段来源不清楚。
    quality_reason = ""  # 新增代码+ContextCompactRepair: 准备质量检查说明；如果没有这行，boundary 质量字段没有可读解释。
    post_compact_chars = 0  # 新增代码+ContextCompactRepair: 准备附件字符统计；如果没有这行，非 TaskState 路径会缺少默认值。
    restore_report_payload: dict[str, Any] = {}  # 新增代码+ContextCompactRepair: 准备恢复报告；如果没有这行，boundary 无法统一写 restore_report。
    compact_generation_value = int(compact_generation if compact_generation is not None else (task_state.compact_generation if task_state is not None else 0))  # 新增代码+ContextCompactRepair: 计算 compact 代次；如果没有这行，链式 compact 无法审计。
    if len(snipped_messages) <= safe_limit and estimate_messages_chars(snipped_messages) <= max(100, estimated_before):  # 新增代码+DeepCompact: 如果 snip 后已经满足数量限制就不强行折叠历史；如果没有这行，短上下文会被无意义摘要化。
        micro_summary = _build_micro_summary(snipped_messages[:1]) if strategy_events else ""  # 新增代码+DeepCompact: 有 snip 时保留一个很短说明；如果没有这行，只有 snip 的 compact 摘要会太空。
        summary_text = _compact_summary_text(session_id, run_id, turn_id, 0, len(original_messages), "not_needed" if not strategy_events else reason, micro_summary, artifact_paths, collapse_commit_uuid)  # 新增代码+DeepCompact: 构造未折叠或仅 snip 的摘要说明；如果没有这行，边界缺少可读解释。
        compacted_messages = snipped_messages  # 新增代码+DeepCompact: 直接使用 snip 后消息；如果没有这行，调用方拿不到安全处理后的内容。
        removed_count = 0  # 新增代码+DeepCompact: 标记没有消息被历史折叠；如果没有这行，边界计数会不准确。
        retained_count = len(compacted_messages)  # 新增代码+DeepCompact: 标记保留消息数量；如果没有这行，resume 无法校验。
        first_archived_index = -1  # 新增代码+DeepCompact: 标记没有折叠起点；如果没有这行，状态页可能误以为有历史归档。
        last_archived_index = -1  # 新增代码+DeepCompact: 标记没有折叠终点；如果没有这行，状态页可能误以为有历史归档。
        summary_source_messages = snipped_messages  # 新增代码+ContextCompactRepair: 设置 TaskState 摘要输入为 snip 后消息；如果没有这行，结构化摘要不知道该总结什么。
        tail_messages_for_structured = copy.deepcopy(compacted_messages)  # 新增代码+ContextCompactRepair: 设置结构化路径要保留的尾部消息；如果没有这行，TaskState 路径会丢掉最新上下文。
    else:  # 新增代码+DeepCompact: 上下文仍过长时进入真正多层 compact；如果没有这行，长任务无法继续压缩。
        original_goal_anchor = _build_original_goal_anchor_message(_find_original_user_goal(snipped_messages))  # 新增代码+原始目标锚点: 在折叠历史前提取用户原始目标；如果没有这行，长任务压缩后仍可能忘记用户到底要什么。
        goal_anchor_messages = [original_goal_anchor] if original_goal_anchor is not None else []  # 新增代码+原始目标锚点: 把可选锚点转成可拼接列表；如果没有这行，后面拼消息时需要重复判断。
        tail_count = max(1, safe_limit - 1 - len(goal_anchor_messages))  # 修改代码+原始目标锚点: 摘要和目标锚点占预算后仍至少保留一条最新消息；如果没有这行，新增锚点可能让消息数量超限。
        archived_messages = snipped_messages[:-tail_count]  # 新增代码+DeepCompact: 取出将被折叠的较早历史；如果没有这行，microcompact 不知道要总结哪段。
        tail_messages = copy.deepcopy(snipped_messages[-tail_count:])  # 新增代码+DeepCompact: 深拷贝尾部消息；如果没有这行，后续修改可能污染 snipped 列表。
        micro_summary = _build_micro_summary(archived_messages)  # 新增代码+DeepCompact: 生成较早历史微摘要；如果没有这行，被折叠历史会完全消失。
        _record_strategy(strategy_events, "microcompact", {"archived_message_count": len(archived_messages), "summary_chars": len(micro_summary)})  # 新增代码+DeepCompact: 记录微压缩阶段；如果没有这行，无法证明旧消息被摘要过。
        _record_strategy(strategy_events, "context_collapse", {"commit_uuid": collapse_commit_uuid, "first_archived_index": 0, "last_archived_index": len(archived_messages) - 1})  # 新增代码+DeepCompact: 记录 collapse 提交；如果没有这行，resume 无法像 ClaudeCode 一样引用 collapse 边界。
        removed_count = len(archived_messages)  # 新增代码+DeepCompact: 计算折叠消息数；如果没有这行，boundary 的 removed_count 会错误。
        retained_count = len(tail_messages)  # 新增代码+DeepCompact: 计算保留尾部消息数；如果没有这行，boundary 的 retained_count 会错误。
        first_archived_index = 0 if archived_messages else -1  # 新增代码+DeepCompact: 记录折叠起始位置；如果没有这行，恢复报告不能定位历史范围。
        last_archived_index = len(archived_messages) - 1 if archived_messages else -1  # 新增代码+DeepCompact: 记录折叠结束位置；如果没有这行，恢复报告不能定位历史范围。
        summary_text = _compact_summary_text(session_id, run_id, turn_id, removed_count, len(original_messages), reason, micro_summary, artifact_paths, collapse_commit_uuid)  # 新增代码+DeepCompact: 构造最终上下文摘要；如果没有这行，模型看不到被折叠历史说明。
        summary_message = {"role": "system", "content": summary_text}  # 新增代码+DeepCompact: 用 system 消息承载 compact 摘要；如果没有这行，模型可能把摘要误认为用户新要求。
        compacted_messages = [summary_message] + goal_anchor_messages + tail_messages  # 修改代码+原始目标锚点: 返回摘要、原始目标锚点和最新尾部消息；如果没有这行，agent 会再次在长链路中偏离用户真实任务。
        summary_source_messages = archived_messages  # 新增代码+ContextCompactRepair: 设置 TaskState 摘要输入为被折叠历史；如果没有这行，专用摘要器无法总结真正被压缩的内容。
        tail_messages_for_structured = copy.deepcopy(tail_messages)  # 新增代码+ContextCompactRepair: 设置结构化路径要保留的最新消息；如果没有这行，九段摘要后会缺少近期模型/工具上下文。
        if goal_anchor_messages:  # 新增代码+原始目标锚点: 只有实际插入锚点时才记录策略事件；如果没有这行，审计日志会误报空锚点。
            _record_strategy(strategy_events, "original_goal_anchor", {"goal_chars": len(str(goal_anchor_messages[0].get("content", "")))})  # 新增代码+原始目标锚点: 记录目标锚点证据；如果没有这行，后续排查无法确认 compact 是否保护了原始目标。
        _record_strategy(strategy_events, "autocompact", {"max_messages": safe_limit, "returned_message_count": len(compacted_messages)})  # 新增代码+DeepCompact: 记录最终自动压缩阶段；如果没有这行，状态生态看不到最终裁定。
    if task_state is not None:  # 新增代码+ContextCompactRepair: TaskState 存在时启用成熟结构化 compact 路径；如果没有这行，新增模块不会真正参与主循环。
        summary_result = summarize_for_compact(summary_source_messages, task_state, reason, model=compact_model)  # 新增代码+ContextCompactRepair: 调用 no-tools 摘要器生成九段摘要；如果没有这行，compact 仍然只是导航摘要。
        original_quality_report = validate_compact_summary(summary_result.summary_text, task_state, summary_result)  # 新增代码+ContextCompactRepair: 检查模型摘要是否合格；如果没有这行，低质量摘要会直接进入上下文。
        final_summary_text = summary_result.summary_text  # 新增代码+ContextCompactRepair: 默认使用模型摘要；如果没有这行，后续 fallback 分支没有可替换目标。
        fallback_used = False  # 新增代码+ContextCompactRepair: 记录是否启用兜底摘要；如果没有这行，debug 无法区分模型摘要和 fallback。
        final_quality_report = original_quality_report  # 新增代码+ContextCompactRepair: 默认最终质量报告等于原报告；如果没有这行，后续 boundary 不知道该写哪个报告。
        if not original_quality_report.passed:  # 新增代码+ContextCompactRepair: 摘要不合格时不能继续使用；如果没有这行，目标丢失问题会重复出现。
            final_summary_text = build_fallback_summary(task_state, reason)  # 新增代码+ContextCompactRepair: 用任务状态生成兜底九段摘要；如果没有这行，compact failure 后没有可靠内容可放回模型。
            fallback_used = True  # 新增代码+ContextCompactRepair: 标记本次使用 fallback；如果没有这行，审计看不到摘要替换。
            final_quality_report = validate_compact_summary(final_summary_text, task_state)  # 新增代码+ContextCompactRepair: 再检查 fallback 摘要；如果没有这行，兜底摘要自身是否合格不可见。
            _record_strategy(strategy_events, "compact_quality_fallback", {"missing_fields": list(original_quality_report.missing_fields), "reason": original_quality_report.reason})  # 新增代码+ContextCompactRepair: 记录原摘要失败原因；如果没有这行，acceptance 无法确认低质量摘要被拦截。
        summary_text = final_summary_text  # 新增代码+ContextCompactRepair: 用最终合格摘要覆盖边界摘要文本；如果没有这行，boundary 仍会保存旧导航摘要。
        summary_message = build_compact_user_summary_message(summary_text)  # 新增代码+ContextCompactRepair: 构造模型可见九段摘要消息；如果没有这行，摘要格式会与专用 prompt 脱节。
        post_attachments, restore_report = build_post_compact_attachments(task_state, recent_runtime_state)  # 新增代码+ContextCompactRepair: 构造压缩后恢复附件；如果没有这行，计划/文件/技能状态会丢。
        boundary_marker = {"role": "system", "content": f"[compact_boundary] boundary_uuid={boundary_uuid}; reason={reason}; compact_generation={compact_generation_value}; quality_passed={final_quality_report.passed}"}  # 新增代码+ContextCompactRepair: 显式写入 compact 边界标记；如果没有这行，模型上下文缺少稳定压缩边界。
        tail_budget = max(1, safe_limit - 2)  # 新增代码+ContextCompactRepair: 给边界和摘要留位置后至少保留一条尾部消息；如果没有这行，近期工具结果可能被摘要完全替代。
        kept_tail_messages = copy.deepcopy(tail_messages_for_structured[-tail_budget:])  # 新增代码+ContextCompactRepair: 复制并保留最新尾部消息；如果没有这行，主循环最新上下文会丢失或被原列表污染。
        compacted_messages = [boundary_marker, summary_message] + kept_tail_messages + post_attachments  # 新增代码+ContextCompactRepair: 按 boundary、summary、messages_to_keep、attachments 顺序重建上下文；如果没有这行，压缩后上下文顺序不符合蓝图。
        retained_count = len(kept_tail_messages)  # 新增代码+ContextCompactRepair: 更新保留消息数量为结构化路径实际数量；如果没有这行，boundary 会误报 retained_count。
        post_compact_chars = restore_report.attachment_chars  # 新增代码+ContextCompactRepair: 保存附件字符数；如果没有这行，boundary 无法审计恢复成本。
        restore_report_payload = restore_report.to_dict()  # 新增代码+ContextCompactRepair: 保存结构化恢复报告；如果没有这行，acceptance 无法看到恢复明细。
        quality_passed = bool(final_quality_report.passed)  # 新增代码+ContextCompactRepair: 保存最终质量结果；如果没有这行，低质量摘要是否被替换不可见。
        quality_missing_fields = list(final_quality_report.missing_fields)  # 新增代码+ContextCompactRepair: 保存最终缺失字段；如果没有这行，失败字段无法审计。
        quality_reason = f"fallback_used={fallback_used}; original_reason={original_quality_report.reason}; final_reason={final_quality_report.reason}"  # 新增代码+ContextCompactRepair: 保存完整质量说明；如果没有这行，排查时不知道是否用过兜底。
        _record_strategy(strategy_events, "compact_quality_check", {"passed": quality_passed, "fallback_used": fallback_used, "missing_fields": quality_missing_fields})  # 新增代码+ContextCompactRepair: 记录质量检查事件；如果没有这行，compact quality 对外不可审计。
        _record_strategy(strategy_events, "post_compact_restore", restore_report_payload)  # 新增代码+ContextCompactRepair: 记录附件恢复事件；如果没有这行，压缩后恢复动作不可见。
    estimated_after = estimate_messages_chars(compacted_messages)  # 新增代码+DeepCompact: 计算压缩后字符量；如果没有这行，无法验证压缩收益。
    boundary = CompactBoundary(  # 新增代码+DeepCompact: 构造完整 compact boundary；如果没有这行，调用方无法保存审计结果。
        boundary_uuid=boundary_uuid,  # 新增代码+DeepCompact: 绑定边界编号；如果没有这行，artifact 和事件会失去主键。
        session_id=str(session_id),  # 新增代码+DeepCompact: 绑定 session；如果没有这行，多会话会混淆。
        run_id=str(run_id),  # 新增代码+DeepCompact: 绑定 run；如果没有这行，状态快照无法聚合。
        turn_id=str(turn_id),  # 新增代码+DeepCompact: 绑定 turn；如果没有这行，中断恢复无法定位。
        original_message_count=len(original_messages),  # 新增代码+DeepCompact: 记录原始数量；如果没有这行，审计规模为空。
        removed_message_count=removed_count,  # 新增代码+DeepCompact: 记录折叠数量；如果没有这行，用户不知道 compact 影响范围。
        retained_message_count=retained_count,  # 新增代码+DeepCompact: 记录保留数量；如果没有这行，resume 无法校验上下文尾部。
        summary_text=summary_text,  # 新增代码+DeepCompact: 保存摘要文本；如果没有这行，resume loader 无法重建 compact 摘要。
        reason=reason if removed_count or strategy_events else "not_needed",  # 新增代码+DeepCompact: 保存真实原因；如果没有这行，不需要 compact 的情况也会误报。
        created_at=utc_timestamp(),  # 新增代码+DeepCompact: 保存创建时间；如果没有这行，时间线不完整。
        strategy_events=strategy_events,  # 新增代码+DeepCompact: 保存策略阶段；如果没有这行，多层 compact 不可审计。
        artifact_paths=artifact_paths,  # 新增代码+DeepCompact: 保存 artifact 路径；如果没有这行，长工具输出无法找回。
        estimated_chars_before=estimated_before,  # 新增代码+DeepCompact: 保存压缩前字符量；如果没有这行，压缩收益无证据。
        estimated_chars_after=estimated_after,  # 新增代码+DeepCompact: 保存压缩后字符量；如果没有这行，压缩收益无证据。
        first_archived_index=first_archived_index,  # 新增代码+DeepCompact: 保存折叠范围起点；如果没有这行，恢复报告缺少定位。
        last_archived_index=last_archived_index,  # 新增代码+DeepCompact: 保存折叠范围终点；如果没有这行，恢复报告缺少定位。
        context_collapse_commit_uuid=collapse_commit_uuid,  # 新增代码+DeepCompact: 保存 collapse 提交编号；如果没有这行，resume 不能引用 collapse。
        quality_passed=quality_passed,  # 新增代码+ContextCompactRepair: 保存摘要质量是否通过；如果没有这行，acceptance 无法验收 compact 质量。
        quality_missing_fields=quality_missing_fields,  # 新增代码+ContextCompactRepair: 保存摘要缺失字段；如果没有这行，失败原因无法追溯。
        quality_reason=quality_reason,  # 新增代码+ContextCompactRepair: 保存质量检查说明；如果没有这行，debug 信息会太粗。
        task_state_path=str(task_state_path),  # 新增代码+ContextCompactRepair: 保存 task state 文件路径；如果没有这行，中断恢复缺少索引。
        post_compact_chars=post_compact_chars,  # 新增代码+ContextCompactRepair: 保存恢复附件大小；如果没有这行，压缩后上下文预算不可见。
        compact_generation=compact_generation_value,  # 新增代码+ContextCompactRepair: 保存 compact 代次；如果没有这行，链式压缩无法区分。
        is_recompaction_in_chain=bool(is_recompaction_in_chain),  # 新增代码+ContextCompactRepair: 保存是否链式重压缩；如果没有这行，重复压缩风险不可见。
        turns_since_previous_compact=int(turns_since_previous_compact),  # 新增代码+ContextCompactRepair: 保存距离上次压缩轮数；如果没有这行，熔断判断不可审计。
        restore_report=restore_report_payload,  # 新增代码+ContextCompactRepair: 保存附件恢复报告；如果没有这行，compact 后恢复内容不可验收。
    )  # 新增代码+DeepCompact: 结束边界构造；如果没有这行，Python 语法不完整。
    return compacted_messages, boundary  # 新增代码+DeepCompact: 返回压缩后的消息和边界；如果没有这行，主循环拿不到 compact 结果。
