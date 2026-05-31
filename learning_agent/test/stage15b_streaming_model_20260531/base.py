"""模型接口定义。"""  # 新增代码+ModelsSplit: 这个文件只放模型共同接口；若没有这个文件，模型边界仍会散落在主入口。

from __future__ import annotations  # 新增代码+ModelsSplit: 延迟解析类型注解；若没有这行代码，前向引用和脚本模式导入更容易受顺序影响。

from dataclasses import dataclass, field  # 新增代码+Stage15B: 定义模型流式事件数据对象；若没有这行代码，流式事件需要手写初始化样板。
from typing import Any, Iterable, Protocol  # 修改代码+Stage15B: 导入通用 JSON 类型、可迭代流和协议基类；若没有 Iterable，stream_chat 协议无法表达事件流。

try:  # 新增代码+ModelsSplit: 包运行模式下从 core.messages 读取统一消息结构；若没有这行代码，模型接口会重新定义消息类型。
    from learning_agent.core.messages import ModelMessage  # 新增代码+ModelsSplit: 导入模型返回消息对象；若没有这行代码，ChatModel.chat 无法表达返回值类型。
except ModuleNotFoundError as error:  # 新增代码+ModelsSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages"}:  # 新增代码+ModelsSplit: 只允许路径缺失时 fallback；若没有这行代码，core 内部真实错误会被误吞。
        raise  # 新增代码+ModelsSplit: 重新抛出真实导入错误；若没有这行代码，排查模型接口问题会很困难。
    from core.messages import ModelMessage  # 新增代码+ModelsSplit: 脚本运行模式下从同目录 core 包导入消息对象；若没有这行代码，直接执行 learning_agent.py 会找不到 ModelMessage。


class ChatModel(Protocol):  # 新增代码+ModelsSplit: 定义所有模型适配器必须实现的最小接口；若没有这行代码，LearningAgent 无法用统一方式调用不同模型。
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelMessage:  # 新增代码+ModelsSplit: 声明模型接收消息和工具列表并返回统一消息；若没有这行代码，模型替换会缺少稳定契约。
        ...  # 新增代码+ModelsSplit: Protocol 只声明接口不实现逻辑；若没有这行代码，Python 类体为空会语法错误。


@dataclass(frozen=True)  # 新增代码+Stage15B: 让模型流式事件创建后不可变；若没有这行代码，事件在传递过程中可能被误改。
class ModelStreamEvent:  # 新增代码+Stage15B: 定义模型层流式事件；若没有这行代码，主循环无法统一处理文本增量、工具调用和完成消息。
    event_type: str  # 新增代码+Stage15B: 保存流式事件类型；若没有这行代码，消费者无法区分 text_delta 和 model_message_completed。
    text_delta: str = ""  # 新增代码+Stage15B: 保存模型流式文本增量；若没有这行代码，终端 UI 未来无法边输出边显示。
    tool_call_delta: dict[str, Any] = field(default_factory=dict)  # 新增代码+Stage15B: 保存未来工具调用增量；若没有这行代码，后续真流式 tool_call 无法携带分片数据。
    tool_call: Any | None = None  # 新增代码+Stage15B: 保存已完成的单个工具调用对象；若没有这行代码，未来工具调用完成事件没有统一字段。
    model_message: ModelMessage | None = None  # 新增代码+Stage15B: 保存完整模型消息；若没有这行代码，兼容旧 chat 的完成事件无法把结果交给主循环。
    raw_event: dict[str, Any] = field(default_factory=dict)  # 新增代码+Stage15B: 保存上游原始事件摘要；若没有这行代码，调试真实流式模型时会丢失底层线索。


class StreamingChatModel(Protocol):  # 新增代码+Stage15B: 定义可选流式模型协议；若没有这行代码，模型层无法声明 stream_chat 扩展点。
    def stream_chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Iterable[ModelStreamEvent]:  # 新增代码+Stage15B: 声明模型接收消息和工具并返回事件流；若没有这行代码，主循环无法以统一方式消费流式模型。
        ...  # 新增代码+Stage15B: Protocol 只声明接口不实现逻辑；若没有这行代码，Python 类体为空会语法错误。


def stream_chat_events(model: ChatModel, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Iterable[ModelStreamEvent]:  # 新增代码+Stage15B: 提供统一模型流入口；若没有这行代码，主循环需要自己判断每个模型是否支持 stream_chat。
    stream_chat = getattr(model, "stream_chat", None)  # 新增代码+Stage15B: 动态读取模型是否有原生 stream_chat；若没有这行代码，兼容层无法优先使用真流式能力。
    if callable(stream_chat):  # 新增代码+Stage15B: 如果模型提供原生流式接口就优先使用；若没有这行代码，真流式模型会被错误降级成一次性 chat。
        yield from stream_chat(messages, tools)  # 新增代码+Stage15B: 透传模型原生事件流；若没有这行代码，调用方收不到真实流式事件。
        return  # 新增代码+Stage15B: 原生流式完成后结束兼容函数；若没有这行代码，后面还会再调用 chat 产生重复结果。
    model_message = model.chat(messages, tools)  # 新增代码+Stage15B: 旧模型没有 stream_chat 时回落到 chat；若没有这行代码，旧模型会因为缺少流式接口而无法使用。
    yield ModelStreamEvent(event_type="model_message_completed", model_message=model_message)  # 新增代码+Stage15B: 把旧模型结果包装成完成事件；若没有这行代码，事件流主循环拿不到兼容结果。
