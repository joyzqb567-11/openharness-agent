"""任务状态事实源模块。"""  # 新增代码+TaskState: 说明本文件负责保存用户任务目标和进展；如果没有这行代码，代码小白很难知道这个模块为什么存在。

from __future__ import annotations  # 新增代码+TaskState: 让类型注解延迟解析；如果没有这行代码，后续类方法返回自身类型时更容易遇到兼容问题。

import hashlib  # 新增代码+TaskState: 用来生成进展指纹；如果没有这行代码，收束控制器无法稳定判断“有没有新进展”。
import json  # 新增代码+TaskState: 用来把任务状态写成 JSON；如果没有这行代码，compact 后和中断后都不能可靠恢复任务状态。
from dataclasses import dataclass, field  # 新增代码+TaskState: 用数据类表达任务状态字段；如果没有这行代码，状态会退回容易写错的散乱字典。
from pathlib import Path  # 新增代码+TaskState: 用统一路径对象读写 task_state.json；如果没有这行代码，Windows 路径处理会更容易出错。
from typing import Any  # 新增代码+TaskState: 允许从 JSON 里接收不完全可信的任意字段；如果没有这行代码，恢复函数类型边界不清楚。

from learning_agent.harness.models import utc_timestamp  # 新增代码+TaskState: 复用项目统一 UTC 时间戳；如果没有这行代码，任务状态时间格式会和其他运行记录不一致。


TASK_STATE_SCHEMA_VERSION = 1  # 新增代码+TaskState: 标记 task_state.json 的协议版本；如果没有这行代码，后续字段升级时无法区分新旧格式。


def _safe_text(value: Any) -> str:  # 新增代码+TaskState: 函数段开始，把任意输入转成干净文本；如果没有这段函数，None、数字或异常 JSON 值会污染任务状态。
    return str(value or "").strip()  # 新增代码+TaskState: 返回去掉首尾空白的字符串；如果没有这行代码，摘要里可能出现 None 或多余空白。


def _safe_list(values: Any) -> list[str]:  # 新增代码+TaskState: 函数段开始，把 JSON 里的列表字段清洗成字符串列表；如果没有这段函数，坏数据会让 compact 和收束判断崩溃。
    if not isinstance(values, list):  # 新增代码+TaskState: 只接受真正的列表；如果没有这行代码，字符串会被逐字符拆成列表。
        return []  # 新增代码+TaskState: 非列表输入兜底为空列表；如果没有这行代码，坏字段会继续向下传播。
    return [_safe_text(item) for item in values if _safe_text(item)]  # 新增代码+TaskState: 清理每个非空条目；如果没有这行代码，空字符串和 None 会进入模型摘要。


@dataclass  # 新增代码+TaskState: 自动生成初始化方法；如果没有这行代码，维护者要手写大量重复赋值。
class TaskState:  # 新增代码+TaskState: 类段开始，保存单次用户任务的可靠事实源；如果没有这个类，compact 后只能靠旧日志猜用户目标。
    schema_version: int = TASK_STATE_SCHEMA_VERSION  # 新增代码+TaskState: 保存协议版本；如果没有这行代码，后续升级无法兼容旧 task_state.json。
    session_id: str = ""  # 新增代码+TaskState: 保存交互会话编号；如果没有这行代码，多会话任务状态会混在一起。
    run_id: str = ""  # 新增代码+TaskState: 保存本次运行编号；如果没有这行代码，验收 artifact 无法定位到具体运行。
    original_user_request: str = ""  # 新增代码+TaskState: 保存用户最初到底要求什么；如果没有这行代码，compact 后最容易丢的就是原始目标。
    latest_user_input: str = ""  # 新增代码+TaskState: 保存用户最近一次补充；如果没有这行代码，多轮短句会失去上下文。
    current_goal: str = ""  # 新增代码+TaskState: 保存当前应该完成的目标；如果没有这行代码，模型可能把子任务误当最终目标。
    completed_items: list[str] = field(default_factory=list)  # 新增代码+TaskState: 保存已经完成的事项；如果没有这行代码，模型会重复做已经完成的工具查询。
    pending_items: list[str] = field(default_factory=list)  # 新增代码+TaskState: 保存还没完成的事项；如果没有这行代码，天气查完后可能忘掉旅游攻略。
    key_facts: list[str] = field(default_factory=list)  # 新增代码+TaskState: 保存任务里确认过的重要事实；如果没有这行代码，压缩后会反复确认地点、天数等事实。
    evidence_summaries: list[str] = field(default_factory=list)  # 新增代码+TaskState: 保存工具证据摘要；如果没有这行代码，模型会反复读日志找证据。
    next_step_hint: str = ""  # 新增代码+TaskState: 保存下一步建议；如果没有这行代码，compact 后模型不知道该继续做什么。
    last_progress_fingerprint: str = ""  # 新增代码+TaskState: 保存最近进展指纹；如果没有这行代码，收束控制器难以识别无进展循环。
    compact_generation: int = 0  # 新增代码+TaskState: 保存经历过几次 compact；如果没有这行代码，验收无法判断压缩代际。
    created_at: str = ""  # 新增代码+TaskState: 保存创建时间；如果没有这行代码，审计记录缺少时间线起点。
    updated_at: str = ""  # 新增代码+TaskState: 保存更新时间；如果没有这行代码，无法知道状态是否真的被刷新。

    @classmethod  # 新增代码+TaskState: 声明下面是类级构造入口；如果没有这行代码，调用方需要先手动 new 再填字段。
    def from_user_input(cls, user_input: str, session_id: str = "", run_id: str = "") -> "TaskState":  # 新增代码+TaskState: 函数段开始，从真实用户输入创建状态；如果没有这段函数，原始目标来源会分散到主循环。
        now = utc_timestamp()  # 新增代码+TaskState: 记录创建时刻；如果没有这行代码，created_at 和 updated_at 没有稳定值。
        clean_input = _safe_text(user_input)  # 新增代码+TaskState: 清理用户输入；如果没有这行代码，空白和 None 可能进入原始目标。
        state = cls(session_id=_safe_text(session_id), run_id=_safe_text(run_id), original_user_request=clean_input, latest_user_input=clean_input, current_goal=clean_input, next_step_hint="基于当前目标继续推进，已有证据足够时输出最终回答。", created_at=now, updated_at=now)  # 新增代码+TaskState: 构造完整初始状态；如果没有这行代码，compact 和收束没有共同事实源。
        state.refresh_progress_fingerprint()  # 新增代码+TaskState: 初始化进展指纹；如果没有这行代码，第一次无进展判断没有基线。
        return state  # 新增代码+TaskState: 返回可继续更新的任务状态；如果没有这行代码，调用方拿不到结果。

    @classmethod  # 新增代码+TaskState: 声明下面是 JSON 恢复入口；如果没有这行代码，调用方要自己解析 dict。
    def from_dict(cls, payload: dict[str, Any]) -> "TaskState":  # 新增代码+TaskState: 函数段开始，从持久化字典恢复状态；如果没有这段函数，compact 后恢复只能靠手写字段。
        safe_payload = payload if isinstance(payload, dict) else {}  # 新增代码+TaskState: 防御坏 JSON 顶层；如果没有这行代码，损坏文件会直接让恢复崩溃。
        state = cls(  # 新增代码+TaskState: 开始构造恢复后的状态对象；如果没有这行代码，下面清洗字段没有承载对象。
            schema_version=int(safe_payload.get("schema_version", TASK_STATE_SCHEMA_VERSION)),  # 新增代码+TaskState: 恢复协议版本；如果没有这行代码，后续迁移无法判断来源。
            session_id=_safe_text(safe_payload.get("session_id", "")),  # 新增代码+TaskState: 恢复会话编号；如果没有这行代码，状态归属会丢失。
            run_id=_safe_text(safe_payload.get("run_id", "")),  # 新增代码+TaskState: 恢复运行编号；如果没有这行代码，验收无法关联 run。
            original_user_request=_safe_text(safe_payload.get("original_user_request", "")),  # 新增代码+TaskState: 恢复原始用户目标；如果没有这行代码，compact 后任务目标仍会丢。
            latest_user_input=_safe_text(safe_payload.get("latest_user_input", "")),  # 新增代码+TaskState: 恢复最近用户输入；如果没有这行代码，多轮补充会消失。
            current_goal=_safe_text(safe_payload.get("current_goal", "")),  # 新增代码+TaskState: 恢复当前目标；如果没有这行代码，收束判断不知道在完成什么。
            completed_items=_safe_list(safe_payload.get("completed_items", [])),  # 新增代码+TaskState: 恢复已完成列表；如果没有这行代码，模型可能重复完成事项。
            pending_items=_safe_list(safe_payload.get("pending_items", [])),  # 新增代码+TaskState: 恢复待办列表；如果没有这行代码，模型可能漏掉剩余任务。
            key_facts=_safe_list(safe_payload.get("key_facts", [])),  # 新增代码+TaskState: 恢复关键事实；如果没有这行代码，地点和日期等事实会丢。
            evidence_summaries=_safe_list(safe_payload.get("evidence_summaries", [])),  # 新增代码+TaskState: 恢复证据摘要；如果没有这行代码，模型会重新读日志找证据。
            next_step_hint=_safe_text(safe_payload.get("next_step_hint", "")),  # 新增代码+TaskState: 恢复下一步提示；如果没有这行代码，compact 后行动方向会变空。
            last_progress_fingerprint=_safe_text(safe_payload.get("last_progress_fingerprint", "")),  # 新增代码+TaskState: 恢复进展指纹；如果没有这行代码，无进展判断没有历史基线。
            compact_generation=int(safe_payload.get("compact_generation", 0)),  # 新增代码+TaskState: 恢复压缩代际；如果没有这行代码，验收无法知道压缩次数。
            created_at=_safe_text(safe_payload.get("created_at", "")),  # 新增代码+TaskState: 恢复创建时间；如果没有这行代码，时间线起点会丢失。
            updated_at=_safe_text(safe_payload.get("updated_at", "")),  # 新增代码+TaskState: 恢复更新时间；如果没有这行代码，状态新旧不可判断。
        )  # 新增代码+TaskState: 结束状态对象构造；如果没有这行代码，Python 语法不完整。
        if not state.last_progress_fingerprint:  # 新增代码+TaskState: 兼容旧文件没有指纹的情况；如果没有这行代码，旧状态恢复后无法判断进展。
            state.refresh_progress_fingerprint()  # 新增代码+TaskState: 补算进展指纹；如果没有这行代码，收束控制器会拿到空指纹。
        return state  # 新增代码+TaskState: 返回恢复后的状态；如果没有这行代码，调用方拿不到对象。

    @classmethod  # 新增代码+TaskState: 声明下面是文件恢复入口；如果没有这行代码，调用方需要手动读 JSON。
    def load_json(cls, path: str | Path) -> "TaskState":  # 新增代码+TaskState: 函数段开始，从 task_state.json 读取状态；如果没有这段函数，中断恢复会重复实现文件读取。
        payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))  # 新增代码+TaskState: 用 UTF-8 兼容 BOM 读取 JSON；如果没有这行代码，中文状态文件可能读失败。
        return cls.from_dict(payload)  # 新增代码+TaskState: 复用字典恢复逻辑；如果没有这行代码，文件和内存恢复规则会不一致。

    def touch(self) -> None:  # 新增代码+TaskState: 函数段开始，刷新更新时间；如果没有这段函数，每个更新方法都要重复写时间逻辑。
        self.updated_at = utc_timestamp()  # 新增代码+TaskState: 写入新的更新时间；如果没有这行代码，状态更新无法被审计。

    def update_latest_user_input(self, user_input: str) -> None:  # 新增代码+TaskState: 函数段开始，记录用户最近补充；如果没有这段函数，多轮短句不会进入任务状态。
        self.latest_user_input = _safe_text(user_input)  # 新增代码+TaskState: 保存清理后的最近输入；如果没有这行代码，后续摘要无法解释用户新补充。
        if self.latest_user_input:  # 新增代码+TaskState: 只有非空补充才更新当前目标提示；如果没有这行代码，空输入会覆盖目标。
            self.current_goal = self.current_goal or self.latest_user_input  # 新增代码+TaskState: 当前目标为空时用最新输入补上；如果没有这行代码，恢复旧状态可能没有目标。
        self.touch()  # 新增代码+TaskState: 更新时间；如果没有这行代码，状态变化没有时间证据。
        self.refresh_progress_fingerprint()  # 新增代码+TaskState: 输入变化后刷新指纹；如果没有这行代码，收束判断可能看不到用户补充。

    def add_completed_item(self, item: str) -> None:  # 新增代码+TaskState: 函数段开始，记录已完成事项；如果没有这段函数，工具结果无法沉淀为完成清单。
        clean_item = _safe_text(item)  # 新增代码+TaskState: 清理完成事项文本；如果没有这行代码，空白项会污染摘要。
        if clean_item and clean_item not in self.completed_items:  # 新增代码+TaskState: 只追加非空且未重复事项；如果没有这行代码，列表会被重复证据刷屏。
            self.completed_items.append(clean_item)  # 新增代码+TaskState: 写入已完成事项；如果没有这行代码，模型不知道哪些事已经做完。
        self.touch()  # 新增代码+TaskState: 更新时间；如果没有这行代码，完成事项变化不可审计。
        self.refresh_progress_fingerprint()  # 新增代码+TaskState: 刷新进展指纹；如果没有这行代码，无进展判断会误判。

    def add_pending_item(self, item: str) -> None:  # 新增代码+TaskState: 函数段开始，记录待完成事项；如果没有这段函数，模型容易漏掉剩余目标。
        clean_item = _safe_text(item)  # 新增代码+TaskState: 清理待办文本；如果没有这行代码，空待办会进入模型上下文。
        if clean_item and clean_item not in self.pending_items:  # 新增代码+TaskState: 只追加非空且未重复待办；如果没有这行代码，待办列表会膨胀。
            self.pending_items.append(clean_item)  # 新增代码+TaskState: 写入待完成事项；如果没有这行代码，压缩后不知道还欠用户什么。
        self.touch()  # 新增代码+TaskState: 更新时间；如果没有这行代码，待办变化不可审计。
        self.refresh_progress_fingerprint()  # 新增代码+TaskState: 刷新进展指纹；如果没有这行代码，待办变化不会影响收束判断。

    def add_key_fact(self, fact: str) -> None:  # 新增代码+TaskState: 函数段开始，记录关键事实；如果没有这段函数，地点、日期、用户偏好会反复丢失。
        clean_fact = _safe_text(fact)  # 新增代码+TaskState: 清理事实文本；如果没有这行代码，坏文本会污染摘要。
        if clean_fact and clean_fact not in self.key_facts:  # 新增代码+TaskState: 避免重复事实；如果没有这行代码，摘要会越来越啰嗦。
            self.key_facts.append(clean_fact)  # 新增代码+TaskState: 写入关键事实；如果没有这行代码，compact 后会忘掉事实。
        self.touch()  # 新增代码+TaskState: 更新时间；如果没有这行代码，事实更新无审计。
        self.refresh_progress_fingerprint()  # 新增代码+TaskState: 刷新指纹；如果没有这行代码，事实变化不会被判断为进展。

    def add_evidence_summary(self, summary: str) -> None:  # 新增代码+TaskState: 函数段开始，记录工具证据摘要；如果没有这段函数，模型会反复读日志找同一证据。
        clean_summary = _safe_text(summary)  # 新增代码+TaskState: 清理证据摘要；如果没有这行代码，空证据会污染状态。
        if clean_summary and clean_summary not in self.evidence_summaries:  # 新增代码+TaskState: 避免重复证据摘要；如果没有这行代码，同一工具结果会反复堆叠。
            self.evidence_summaries.append(clean_summary)  # 新增代码+TaskState: 写入证据摘要；如果没有这行代码，compact 后证据会丢。
        self.touch()  # 新增代码+TaskState: 更新时间；如果没有这行代码，证据更新时间不可见。
        self.refresh_progress_fingerprint()  # 新增代码+TaskState: 刷新进展指纹；如果没有这行代码，新增证据不会解除无进展判断。

    def set_next_step_hint(self, hint: str) -> None:  # 新增代码+TaskState: 函数段开始，设置下一步建议；如果没有这段函数，compact 后模型不知道该继续还是收束。
        self.next_step_hint = _safe_text(hint)  # 新增代码+TaskState: 保存清理后的提示；如果没有这行代码，空白提示会进入摘要。
        self.touch()  # 新增代码+TaskState: 更新时间；如果没有这行代码，下一步变化不可审计。
        self.refresh_progress_fingerprint()  # 新增代码+TaskState: 刷新进展指纹；如果没有这行代码，下一步变化不影响收束判断。

    def refresh_progress_fingerprint(self) -> str:  # 新增代码+TaskState: 函数段开始，重新计算进展指纹；如果没有这段函数，无法判断重复工具是否有新进展。
        payload = {  # 新增代码+TaskState: 构造参与指纹的稳定 payload；如果没有这行代码，hash 输入会分散不稳定。
            "current_goal": self.current_goal,  # 新增代码+TaskState: 目标参与指纹；如果没有这行代码，目标变化不会被识别。
            "completed_items": self.completed_items,  # 新增代码+TaskState: 完成项参与指纹；如果没有这行代码，完成进展不会被识别。
            "pending_items": self.pending_items,  # 新增代码+TaskState: 待办项参与指纹；如果没有这行代码，待办变化不会被识别。
            "key_facts": self.key_facts,  # 新增代码+TaskState: 关键事实参与指纹；如果没有这行代码，新事实不会被识别。
            "evidence_summaries": self.evidence_summaries,  # 新增代码+TaskState: 证据摘要参与指纹；如果没有这行代码，新证据不会被识别。
            "next_step_hint": self.next_step_hint,  # 新增代码+TaskState: 下一步提示参与指纹；如果没有这行代码，行动方向变化不会被识别。
        }  # 新增代码+TaskState: 结束指纹 payload；如果没有这行代码，Python 字典语法不完整。
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")  # 新增代码+TaskState: 稳定序列化为 UTF-8；如果没有这行代码，相同内容可能生成不同 hash。
        self.last_progress_fingerprint = hashlib.sha256(encoded).hexdigest()  # 新增代码+TaskState: 生成 SHA256 指纹；如果没有这行代码，收束控制器没有稳定比较值。
        return self.last_progress_fingerprint  # 新增代码+TaskState: 返回新指纹；如果没有这行代码，调用方无法立即使用结果。

    def to_model_summary(self) -> str:  # 新增代码+TaskState: 函数段开始，生成给模型看的任务状态摘要；如果没有这段函数，compact 和收束会各写各的摘要格式。
        completed_text = "；".join(self.completed_items) if self.completed_items else "暂无明确完成项"  # 新增代码+TaskState: 整理已完成事项；如果没有这行代码，空列表会直接暴露成程序格式。
        pending_text = "；".join(self.pending_items) if self.pending_items else "暂无明确待办项"  # 新增代码+TaskState: 整理待办事项；如果没有这行代码，模型看不懂空列表含义。
        facts_text = "；".join(self.key_facts) if self.key_facts else "暂无关键事实"  # 新增代码+TaskState: 整理关键事实；如果没有这行代码，事实为空时摘要不完整。
        evidence_text = "；".join(self.evidence_summaries) if self.evidence_summaries else "暂无关键证据"  # 新增代码+TaskState: 整理证据摘要；如果没有这行代码，证据为空时摘要不完整。
        return "\n".join([  # 新增代码+TaskState: 按固定七段格式返回摘要；如果没有这行代码，质量检查器无法稳定识别字段。
            "任务状态摘要：",  # 新增代码+TaskState: 标题说明下面是任务状态；如果没有这行代码，模型可能把它当普通聊天文本。
            f"1. 原始用户目标：{self.original_user_request or '未记录'}",  # 新增代码+TaskState: 输出原始目标；如果没有这行代码，压缩后最关键目标会丢。
            f"2. 当前目标：{self.current_goal or '未记录'}",  # 新增代码+TaskState: 输出当前目标；如果没有这行代码，模型不知道现在要完成什么。
            f"3. 已完成：{completed_text}",  # 新增代码+TaskState: 输出已完成事项；如果没有这行代码，模型可能重复查证。
            f"4. 待完成：{pending_text}",  # 新增代码+TaskState: 输出待办事项；如果没有这行代码，模型可能漏任务。
            f"5. 关键事实：{facts_text}",  # 新增代码+TaskState: 输出关键事实；如果没有这行代码，模型会反复确认事实。
            f"6. 关键证据：{evidence_text}",  # 新增代码+TaskState: 输出证据摘要；如果没有这行代码，模型会反复读日志。
            f"7. 下一步：{self.next_step_hint or '基于已有状态继续推进。'}",  # 新增代码+TaskState: 输出下一步提示；如果没有这行代码，模型不知道继续还是收束。
        ])  # 新增代码+TaskState: 结束摘要拼接；如果没有这行代码，Python 调用语法不完整。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+TaskState: 函数段开始，把状态转成 JSON 字典；如果没有这段函数，落盘和验收 artifact 无法统一。
        return {  # 新增代码+TaskState: 返回所有持久化字段；如果没有这行代码，调用方拿不到结构化状态。
            "schema_version": self.schema_version,  # 新增代码+TaskState: 写出协议版本；如果没有这行代码，旧数据升级困难。
            "session_id": self.session_id,  # 新增代码+TaskState: 写出会话编号；如果没有这行代码，状态归属不清。
            "run_id": self.run_id,  # 新增代码+TaskState: 写出运行编号；如果没有这行代码，验收无法关联运行。
            "original_user_request": self.original_user_request,  # 新增代码+TaskState: 写出原始目标；如果没有这行代码，最重要的任务目标不能落盘。
            "latest_user_input": self.latest_user_input,  # 新增代码+TaskState: 写出最近输入；如果没有这行代码，多轮补充不能恢复。
            "current_goal": self.current_goal,  # 新增代码+TaskState: 写出当前目标；如果没有这行代码，恢复后不知道要做什么。
            "completed_items": list(self.completed_items),  # 新增代码+TaskState: 写出已完成列表；如果没有这行代码，进展会丢失。
            "pending_items": list(self.pending_items),  # 新增代码+TaskState: 写出待办列表；如果没有这行代码，剩余任务会丢失。
            "key_facts": list(self.key_facts),  # 新增代码+TaskState: 写出关键事实；如果没有这行代码，事实会丢失。
            "evidence_summaries": list(self.evidence_summaries),  # 新增代码+TaskState: 写出证据摘要；如果没有这行代码，工具证据会丢失。
            "next_step_hint": self.next_step_hint,  # 新增代码+TaskState: 写出下一步提示；如果没有这行代码，恢复后行动方向会丢。
            "last_progress_fingerprint": self.last_progress_fingerprint,  # 新增代码+TaskState: 写出进展指纹；如果没有这行代码，恢复后无法延续无进展判断。
            "compact_generation": self.compact_generation,  # 新增代码+TaskState: 写出压缩代际；如果没有这行代码，验收无法看到 compact 次数。
            "created_at": self.created_at,  # 新增代码+TaskState: 写出创建时间；如果没有这行代码，审计时间线不完整。
            "updated_at": self.updated_at,  # 新增代码+TaskState: 写出更新时间；如果没有这行代码，审计时间线不完整。
        }  # 新增代码+TaskState: 结束字典返回；如果没有这行代码，Python 字典语法不完整。

    def save_json(self, path: str | Path) -> Path:  # 新增代码+TaskState: 函数段开始，把状态保存到 JSON 文件；如果没有这段函数，compact 后没有可靠状态 artifact。
        target_path = Path(path)  # 新增代码+TaskState: 统一把输入转成 Path；如果没有这行代码，字符串路径和 Path 路径处理会分裂。
        target_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+TaskState: 确保父目录存在；如果没有这行代码，第一次保存会因为目录不存在失败。
        target_path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")  # 新增代码+TaskState: 用 UTF-8 写出可读 JSON；如果没有这行代码，中文目标可能乱码或无法落盘。
        return target_path  # 新增代码+TaskState: 返回保存路径；如果没有这行代码，调用方无法把路径写进 boundary 和验收结果。


__all__ = ["TASK_STATE_SCHEMA_VERSION", "TaskState"]  # 新增代码+TaskState: 明确本模块公开接口；如果没有这行代码，后续导入边界不清晰。
