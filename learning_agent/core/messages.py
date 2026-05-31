from __future__ import annotations  # 新增代码+CoreMessages: 延迟解析类型注解；如果没有这行代码，类之间互相引用时更容易受定义顺序影响。

import secrets  # 新增代码+CoreMessages: 生成工具调用唯一 id；如果没有这行代码，ToolCall 无法自动生成可追踪 call_id。
from dataclasses import dataclass, field  # 新增代码+CoreMessages: 快速定义只保存数据的小对象；如果没有这行代码，消息对象需要手写初始化逻辑。
from typing import Any  # 新增代码+CoreMessages: 表示任意 JSON 风格参数；如果没有这行代码，工具参数类型会缺少清楚边界。


@dataclass  # 新增代码+CoreMessages: 自动生成工具调用对象的初始化方法；如果没有这行代码，测试和模型适配器都要手写对象构造。
class ToolCall:  # 新增代码+CoreMessages: 表示模型请求 agent 执行的一次工具调用；如果没有这个类，工具调用只能用松散字典传递。
    name: str  # 新增代码+CoreMessages: 保存工具名称，例如 read/write/bash；如果没有这行代码，agent 不知道模型想调用哪个工具。
    arguments: dict[str, Any]  # 新增代码+CoreMessages: 保存工具参数；如果没有这行代码，工具执行器拿不到模型提供的输入。
    call_id: str = field(default_factory=lambda: f"call_{secrets.token_hex(8)}")  # 新增代码+CoreMessages: 自动生成唯一调用 id；如果没有这行代码，工具结果难以和模型调用对应。


@dataclass  # 新增代码+CoreMessages: 自动生成模型消息对象的初始化方法；如果没有这行代码，假模型和真实模型适配器都要重复样板代码。
class ModelMessage:  # 新增代码+CoreMessages: 表示模型返回给 agent 的一条消息；如果没有这个类，文本回答和工具调用会缺少统一容器。
    decision_note: str = ""  # 新增代码+CoreMessages: 保存模型给人的简短决策说明；如果没有这行代码，学习者更难理解模型为什么调用工具。
    text: str = ""  # 新增代码+CoreMessages: 保存模型直接回复用户的文本；如果没有这行代码，最终回答没有稳定字段。
    tool_calls: list[ToolCall] = field(default_factory=list)  # 新增代码+CoreMessages: 保存模型请求的工具调用数组；如果没有这行代码，agent 无法执行多工具调用。
