"""compact 后必要上下文附件恢复模块。"""  # 新增代码+PostCompactRestore: 说明本文件负责压缩后恢复必要附件；如果没有这行代码，模型压缩后可能只剩摘要而失明。

from __future__ import annotations  # 新增代码+PostCompactRestore: 延迟解析类型注解；如果没有这行代码，类型引用在旧 Python 版本更容易出问题。

from dataclasses import dataclass, field  # 新增代码+PostCompactRestore: 用数据类保存恢复报告；如果没有这行代码，恢复字段会散落成普通 dict。
from typing import Any  # 新增代码+PostCompactRestore: runtime_state 是宽松 JSON 结构；如果没有这行代码，接口类型边界不清楚。

from learning_agent.core.task_state import TaskState  # 新增代码+PostCompactRestore: 使用任务状态事实源；如果没有这行代码，恢复附件无法带上目标摘要。


ATTACHMENT_CHAR_LIMIT = 1200  # 新增代码+PostCompactRestore: 限制单个附件字符数；如果没有这行代码，恢复附件可能再次撑爆上下文。


@dataclass  # 新增代码+PostCompactRestore: 自动生成恢复报告初始化方法；如果没有这行代码，调用方要手写报告对象。
class PostCompactRestoreReport:  # 新增代码+PostCompactRestore: 类段开始，记录 compact 后恢复了哪些附件；如果没有这个类，acceptance 无法验收恢复质量。
    restored_file_count: int = 0  # 新增代码+PostCompactRestore: 保存恢复的最近文件数量；如果没有这行代码，模型是否拿回文件线索不可见。
    restored_plan: bool = False  # 新增代码+PostCompactRestore: 保存是否恢复计划状态；如果没有这行代码，计划上下文恢复不可审计。
    restored_skills: list[str] = field(default_factory=list)  # 新增代码+PostCompactRestore: 保存恢复的技能名；如果没有这行代码，skill 状态是否保留不可见。
    restored_background_tasks: list[str] = field(default_factory=list)  # 新增代码+PostCompactRestore: 保存恢复的后台任务；如果没有这行代码，后台任务状态会丢证据。
    attachment_chars: int = 0  # 新增代码+PostCompactRestore: 保存附件总字符数；如果没有这行代码，恢复成本不可见。
    reason: str = ""  # 新增代码+PostCompactRestore: 保存恢复原因说明；如果没有这行代码，debug log 只有数字没有解释。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+PostCompactRestore: 函数段开始，把恢复报告转成 JSON；如果没有这段函数，boundary 无法保存报告。
        return {  # 新增代码+PostCompactRestore: 返回所有恢复字段；如果没有这行代码，调用方拿不到结构化报告。
            "restored_file_count": self.restored_file_count,  # 新增代码+PostCompactRestore: 写出文件数量；如果没有这行代码，验收看不到文件恢复。
            "restored_plan": self.restored_plan,  # 新增代码+PostCompactRestore: 写出计划恢复状态；如果没有这行代码，计划恢复不可见。
            "restored_skills": list(self.restored_skills),  # 新增代码+PostCompactRestore: 写出技能列表；如果没有这行代码，skill 恢复不可见。
            "restored_background_tasks": list(self.restored_background_tasks),  # 新增代码+PostCompactRestore: 写出后台任务列表；如果没有这行代码，后台状态不可见。
            "attachment_chars": self.attachment_chars,  # 新增代码+PostCompactRestore: 写出附件字符数；如果没有这行代码，恢复预算不可见。
            "reason": self.reason,  # 新增代码+PostCompactRestore: 写出说明；如果没有这行代码，报告不可读。
        }  # 新增代码+PostCompactRestore: 结束字典返回；如果没有这行代码，Python 字典语法不完整。


def _trim_text(value: Any, limit: int = ATTACHMENT_CHAR_LIMIT) -> str:  # 新增代码+PostCompactRestore: 函数段开始，限制附件文本长度；如果没有这段函数，大文件摘要可能再次塞爆上下文。
    return str(value or "").strip()[:limit]  # 新增代码+PostCompactRestore: 返回长度受控文本；如果没有这行代码，附件没有预算上限。


def _attachment(title: str, body: str) -> dict[str, str]:  # 新增代码+PostCompactRestore: 函数段开始，构造 system 附件消息；如果没有这段函数，附件格式会重复散落。
    return {"role": "system", "content": f"[post_compact_restore:{title}]\n{_trim_text(body)}"}  # 新增代码+PostCompactRestore: 返回模型可见恢复附件；如果没有这行代码，compact 后恢复信息无法进入上下文。


def build_post_compact_attachments(task_state: TaskState, recent_runtime_state: dict[str, Any] | None = None) -> tuple[list[dict[str, str]], PostCompactRestoreReport]:  # 新增代码+PostCompactRestore: 函数段开始，构造 compact 后恢复附件和报告；如果没有这段函数，压缩后只剩摘要。
    runtime_state = recent_runtime_state if isinstance(recent_runtime_state, dict) else {}  # 新增代码+PostCompactRestore: 防御空或坏 runtime_state；如果没有这行代码，调用方传 None 会崩溃。
    attachments: list[dict[str, str]] = []  # 新增代码+PostCompactRestore: 准备附件消息列表；如果没有这行代码，后续无法追加恢复内容。
    report = PostCompactRestoreReport(reason="post compact restore completed")  # 新增代码+PostCompactRestore: 初始化恢复报告；如果没有这行代码，调用方拿不到恢复审计。
    attachments.append(_attachment("task_state", task_state.to_model_summary()))  # 新增代码+PostCompactRestore: 始终恢复任务状态摘要；如果没有这行代码，压缩后模型可能忘记原始目标。
    recent_files = runtime_state.get("recent_files", [])  # 新增代码+PostCompactRestore: 读取最近文件状态；如果没有这行代码，文件线索无法恢复。
    if isinstance(recent_files, list):  # 新增代码+PostCompactRestore: 只处理列表形态；如果没有这行代码，坏字段可能被错误遍历。
        for file_item in recent_files[:5]:  # 新增代码+PostCompactRestore: 最多恢复 5 个文件摘要；如果没有这行代码，文件列表可能过长。
            file_text = _trim_text(file_item)  # 新增代码+PostCompactRestore: 限制单个文件摘要长度；如果没有这行代码，文件内容可能过长。
            if file_text:  # 新增代码+PostCompactRestore: 只恢复非空文件摘要；如果没有这行代码，空附件会污染上下文。
                attachments.append(_attachment("recent_file", file_text))  # 新增代码+PostCompactRestore: 添加最近文件附件；如果没有这行代码，模型压缩后不知道最近读过什么。
                report.restored_file_count += 1  # 新增代码+PostCompactRestore: 记录恢复文件数量；如果没有这行代码，报告数量不准确。
    plan_state = _trim_text(runtime_state.get("plan_state", ""))  # 新增代码+PostCompactRestore: 读取计划状态摘要；如果没有这行代码，plan mode 上下文无法恢复。
    if plan_state:  # 新增代码+PostCompactRestore: 有计划状态才恢复；如果没有这行代码，空计划附件会污染上下文。
        attachments.append(_attachment("plan_state", plan_state))  # 新增代码+PostCompactRestore: 添加计划附件；如果没有这行代码，compact 后计划上下文会丢。
        report.restored_plan = True  # 新增代码+PostCompactRestore: 记录计划已恢复；如果没有这行代码，报告不可审计。
    skills = runtime_state.get("skills", [])  # 新增代码+PostCompactRestore: 读取已调用 skill 列表；如果没有这行代码，skill 状态无法恢复。
    if isinstance(skills, list):  # 新增代码+PostCompactRestore: 只处理列表；如果没有这行代码，坏字段可能被错误遍历。
        clean_skills = [_trim_text(skill, 120) for skill in skills if _trim_text(skill, 120)]  # 新增代码+PostCompactRestore: 清理技能名；如果没有这行代码，空 skill 会进入报告。
        if clean_skills:  # 新增代码+PostCompactRestore: 有技能才恢复；如果没有这行代码，空附件会污染上下文。
            attachments.append(_attachment("skills", "；".join(clean_skills[:10])))  # 新增代码+PostCompactRestore: 添加技能附件；如果没有这行代码，压缩后模型不知道使用过哪些技能。
            report.restored_skills = clean_skills[:10]  # 新增代码+PostCompactRestore: 记录恢复技能；如果没有这行代码，报告看不到 skill 列表。
    background_tasks = runtime_state.get("background_tasks", [])  # 新增代码+PostCompactRestore: 读取后台任务状态；如果没有这行代码，后台任务压缩后会丢。
    if isinstance(background_tasks, list):  # 新增代码+PostCompactRestore: 只处理列表；如果没有这行代码，坏字段可能被错误遍历。
        clean_tasks = [_trim_text(task, 180) for task in background_tasks if _trim_text(task, 180)]  # 新增代码+PostCompactRestore: 清理后台任务摘要；如果没有这行代码，空任务会进入附件。
        if clean_tasks:  # 新增代码+PostCompactRestore: 有后台任务才恢复；如果没有这行代码，空附件会污染上下文。
            attachments.append(_attachment("background_tasks", "；".join(clean_tasks[:10])))  # 新增代码+PostCompactRestore: 添加后台任务附件；如果没有这行代码，模型压缩后不知道后台状态。
            report.restored_background_tasks = clean_tasks[:10]  # 新增代码+PostCompactRestore: 记录后台任务；如果没有这行代码，报告不可审计。
    report.attachment_chars = sum(len(message.get("content", "")) for message in attachments)  # 新增代码+PostCompactRestore: 统计附件字符数；如果没有这行代码，恢复预算不可见。
    return attachments, report  # 新增代码+PostCompactRestore: 返回附件和报告；如果没有这行代码，compact.py 无法使用恢复结果。


__all__ = ["PostCompactRestoreReport", "build_post_compact_attachments"]  # 新增代码+PostCompactRestore: 明确公开接口；如果没有这行代码，其他模块导入边界不清。
