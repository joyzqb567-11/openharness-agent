"""Stage 15A 运行时事件类型。"""  # 新增代码+Stage15A: 这个文件集中定义 agent 运行事件；若没有这个文件，主循环、工具和权限日志会继续各写各的格式。

from __future__ import annotations  # 新增代码+Stage15A: 延迟解析类型注解；若没有这行代码，后续事件类型互相引用时更容易受定义顺序影响。

import copy  # 新增代码+Stage15A: 深拷贝事件载荷；若没有这行代码，调用方后续修改 payload 会污染已经创建的事件。
import json  # 新增代码+Stage15A: 把事件转换成 JSONL 文本；若没有这行代码，transcript 无法使用通用 JSON 格式落盘。
from dataclasses import dataclass, field  # 新增代码+Stage15A: 用 dataclass 定义轻量事件对象；若没有这行代码，需要手写重复初始化逻辑。
from datetime import datetime, timezone  # 新增代码+Stage15A: 生成 UTC 时间戳；若没有这行代码，未指定 timestamp 的事件无法稳定记录发生时间。
from typing import Any  # 新增代码+Stage15A: 事件 payload 是通用 JSON 风格数据；若没有这行代码，类型边界会不清楚。


def utc_timestamp() -> str:  # 新增代码+Stage15A: 生成统一 UTC 时间字符串；若没有这行代码，各调用点会用不同时间格式。
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")  # 新增代码+Stage15A: 返回无微秒的 ISO UTC 时间；若没有这行代码，事件时间戳会过细且测试更难稳定。


@dataclass(frozen=True)  # 新增代码+Stage15A: 让事件对象创建后不可变；若没有这行代码，事件写入前可能被后续逻辑意外修改。
class AgentEvent:  # 新增代码+Stage15A: 定义 agent 运行时事件；若没有这行代码，transcript 无法使用统一事件对象。
    event_type: str  # 新增代码+Stage15A: 保存事件类型；若没有这行代码，消费者无法区分模型请求、工具调用或最终回答。
    run_id: str  # 新增代码+Stage15A: 保存本次运行编号；若没有这行代码，多次 run 的事件会混在一起难以追踪。
    sequence: int  # 新增代码+Stage15A: 保存事件顺序号；若没有这行代码，恢复 transcript 时无法确认事件顺序。
    session_id: str = ""  # 新增代码+Stage15A: 保存会话编号；若没有这行代码，后续 resume 无法按 session 聚合事件。
    timestamp: str = field(default_factory=utc_timestamp)  # 新增代码+Stage15A: 保存事件发生时间；若没有这行代码，审计时不知道事件何时发生。
    payload: dict[str, Any] = field(default_factory=dict)  # 新增代码+Stage15A: 保存事件业务数据；若没有这行代码，事件只能说明类型而不能携带上下文。

    def to_json_dict(self) -> dict[str, Any]:  # 新增代码+Stage15A: 把事件对象转换成可序列化字典；若没有这行代码，writer 需要知道 dataclass 内部结构。
        return {  # 新增代码+Stage15A: 返回标准事件字段；若没有这行代码，调用方拿不到统一 JSON 结构。
            "event_type": self.event_type,  # 新增代码+Stage15A: 写出事件类型；若没有这行代码，JSON 里无法按事件类型过滤。
            "run_id": self.run_id,  # 新增代码+Stage15A: 写出运行编号；若没有这行代码，JSON 里无法串联一次运行。
            "sequence": self.sequence,  # 新增代码+Stage15A: 写出顺序号；若没有这行代码，JSON 里无法稳定回放事件。
            "session_id": self.session_id,  # 新增代码+Stage15A: 写出会话编号；若没有这行代码，JSON 里无法按 session 恢复。
            "timestamp": self.timestamp,  # 新增代码+Stage15A: 写出时间戳；若没有这行代码，JSON 里缺少审计时间。
            "payload": copy.deepcopy(self.payload),  # 新增代码+Stage15A: 写出载荷副本；若没有这行代码，外部修改返回字典可能影响原事件。
        }  # 新增代码+Stage15A: 结束事件字典；若没有这行代码，Python 字典语法不完整。


def create_agent_event(event_type: str, run_id: str, sequence: int, session_id: str = "", timestamp: str | None = None, payload: dict[str, Any] | None = None) -> AgentEvent:  # 新增代码+Stage15A: 提供创建事件的统一入口；若没有这行代码，各处会重复拼 AgentEvent。
    return AgentEvent(  # 新增代码+Stage15A: 返回不可变事件对象；若没有这行代码，工厂函数无法产生事件。
        event_type=event_type,  # 新增代码+Stage15A: 传入事件类型；若没有这行代码，创建出来的事件不知道自己是什么。
        run_id=run_id,  # 新增代码+Stage15A: 传入运行编号；若没有这行代码，事件无法关联到具体 run。
        sequence=sequence,  # 新增代码+Stage15A: 传入顺序号；若没有这行代码，事件顺序会丢失。
        session_id=session_id,  # 新增代码+Stage15A: 传入会话编号；若没有这行代码，事件无法归档到 session。
        timestamp=timestamp or utc_timestamp(),  # 新增代码+Stage15A: 使用指定时间或当前 UTC 时间；若没有这行代码，默认时间戳无法自动生成。
        payload=copy.deepcopy(payload or {}),  # 新增代码+Stage15A: 深拷贝载荷；若没有这行代码，调用方后续修改原始 payload 会污染事件。
    )  # 新增代码+Stage15A: 结束 AgentEvent 构造；若没有这行代码，Python 调用语法不完整。


def agent_event_to_json_line(event: AgentEvent) -> str:  # 新增代码+Stage15A: 把事件转换成 JSONL 单行；若没有这行代码，transcript writer 无法统一落盘格式。
    return json.dumps(event.to_json_dict(), ensure_ascii=False, sort_keys=True) + "\n"  # 新增代码+Stage15A: 输出 UTF-8 友好的稳定 JSON 行；若没有这行代码，多条事件可能无法逐行读取。
