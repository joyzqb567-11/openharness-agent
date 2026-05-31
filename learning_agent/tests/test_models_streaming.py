"""Stage 15B 流式模型接口测试。"""  # 新增代码+Stage15B: 说明本文件验证模型流式协议；若没有这行代码，后续维护者不清楚测试边界。

from __future__ import annotations  # 新增代码+Stage15B: 延迟解析类型注解；若没有这行代码，前向引用类型更容易受定义顺序影响。

import unittest  # 新增代码+Stage15B: 使用项目现有 unittest 测试框架；若没有这行代码，测试类无法被 discover 执行。

from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+Stage15B: 导入模型消息和工具调用对象；若没有这行代码，测试无法构造真实模型返回。
from learning_agent.models.base import ModelStreamEvent, stream_chat_events  # 新增代码+Stage15B: 导入新增流式事件和兼容包装入口；若没有这行代码，红灯无法证明接口缺失。


class LegacyChatOnlyModel:  # 新增代码+Stage15B: 定义只有 chat() 的旧模型；若没有这行代码，无法验证兼容包装不会破坏旧适配器。
    def __init__(self) -> None:  # 新增代码+Stage15B: 初始化旧模型调用记录；若没有这行代码，测试无法确认 fallback 真调用了 chat。
        self.chat_called = False  # 新增代码+Stage15B: 记录 chat 是否被调用；若没有这行代码，测试无法证明 fallback 路径生效。

    def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+Stage15B: 实现旧模型 chat 接口；若没有这行代码，兼容包装没有可调用目标。
        self.chat_called = True  # 新增代码+Stage15B: 标记 chat 被调用；若没有这行代码，测试无法确认旧接口被复用。
        return ModelMessage(text="旧模型一次性完成", tool_calls=[ToolCall(name="read", arguments={"path": "README.md"})])  # 新增代码+Stage15B: 返回带文本和工具调用的消息；若没有这行代码，测试无法确认 completed 事件携带完整消息。


class NativeStreamingModel:  # 新增代码+Stage15B: 定义带 stream_chat() 的模型；若没有这行代码，无法验证新接口优先级。
    def __init__(self) -> None:  # 新增代码+Stage15B: 初始化原生流式模型调用记录；若没有这行代码，测试无法确认 chat 未被 fallback 调用。
        self.chat_called = False  # 新增代码+Stage15B: 记录 chat 是否被误调用；若没有这行代码，测试无法证明 stream_chat 优先。
        self.stream_called = False  # 新增代码+Stage15B: 记录 stream_chat 是否被调用；若没有这行代码，测试无法证明原生流式入口生效。

    def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+Stage15B: 保留 chat 以模拟真实模型同时有两个接口；若没有这行代码，无法断言没有误走 fallback。
        self.chat_called = True  # 新增代码+Stage15B: 如果 fallback 误调用 chat 就留下证据；若没有这行代码，测试无法发现优先级错误。
        return ModelMessage(text="不应该走这里")  # 新增代码+Stage15B: 返回明显文本；若没有这行代码，误走 chat 时不容易定位。

    def stream_chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]):  # 新增代码+Stage15B: 实现原生流式接口；若没有这行代码，测试无法验证 stream_chat_events 优先调用它。
        self.stream_called = True  # 新增代码+Stage15B: 标记 stream_chat 被调用；若没有这行代码，测试无法确认原生流式路径。
        yield ModelStreamEvent(event_type="text_delta", text_delta="你")  # 新增代码+Stage15B: 产出文本增量事件；若没有这行代码，无法验证增量事件能透传。
        yield ModelStreamEvent(event_type="text_delta", text_delta="好")  # 新增代码+Stage15B: 产出第二个文本增量事件；若没有这行代码，无法验证多事件顺序。
        yield ModelStreamEvent(event_type="model_message_completed", model_message=ModelMessage(text="你好"))  # 新增代码+Stage15B: 产出完成事件；若没有这行代码，主循环后续无法拿到完整模型消息。


class ModelStreamingTests(unittest.TestCase):  # 新增代码+Stage15B: 定义流式模型测试类；若没有这行代码，测试方法没有统一容器。
    def test_stream_chat_events_wraps_legacy_chat_model_as_completed_event(self) -> None:  # 新增代码+Stage15B: 验证旧模型可以被包装成一次性完成事件；若没有这行代码，兼容性回归不会被发现。
        model = LegacyChatOnlyModel()  # 新增代码+Stage15B: 创建只有 chat 的旧模型；若没有这行代码，测试没有被包装对象。
        events = list(stream_chat_events(model, messages=[{"role": "user", "content": "ping"}], tools=[]))  # 新增代码+Stage15B: 通过统一流式入口消费旧模型；若没有这行代码，无法观察 fallback 输出。
        self.assertTrue(model.chat_called)  # 新增代码+Stage15B: 断言 fallback 调用了 chat；若没有这行代码，stream_chat_events 可能没有真正调用模型。
        self.assertEqual(len(events), 1)  # 新增代码+Stage15B: 断言旧模型只产生一个完成事件；若没有这行代码，兼容层可能制造多余事件。
        self.assertEqual(events[0].event_type, "model_message_completed")  # 新增代码+Stage15B: 断言事件类型是模型消息完成；若没有这行代码，主循环无法统一处理旧模型结果。
        self.assertEqual(events[0].model_message.text, "旧模型一次性完成")  # 新增代码+Stage15B: 断言完整文本被保留；若没有这行代码，fallback 可能丢失最终回答。
        self.assertEqual(events[0].model_message.tool_calls[0].name, "read")  # 新增代码+Stage15B: 断言工具调用被保留；若没有这行代码，fallback 会破坏工具循环。

    def test_stream_chat_events_prefers_native_stream_chat(self) -> None:  # 新增代码+Stage15B: 验证原生 stream_chat 优先于 fallback；若没有这行代码，真实流式模型可能被降级成一次性 chat。
        model = NativeStreamingModel()  # 新增代码+Stage15B: 创建同时有 chat 和 stream_chat 的模型；若没有这行代码，测试没有优先级对象。
        events = list(stream_chat_events(model, messages=[{"role": "user", "content": "你好"}], tools=[]))  # 新增代码+Stage15B: 通过统一入口消费原生流式模型；若没有这行代码，无法观察事件序列。
        self.assertTrue(model.stream_called)  # 新增代码+Stage15B: 断言 stream_chat 被调用；若没有这行代码，优先级错误不会被发现。
        self.assertFalse(model.chat_called)  # 新增代码+Stage15B: 断言没有误调用 chat；若没有这行代码，模型可能被错误降级。
        self.assertEqual([event.event_type for event in events], ["text_delta", "text_delta", "model_message_completed"])  # 新增代码+Stage15B: 断言事件顺序稳定；若没有这行代码，主循环无法可靠重放流式输出。
        self.assertEqual("".join(event.text_delta for event in events if event.event_type == "text_delta"), "你好")  # 新增代码+Stage15B: 断言文本增量可以拼回完整文本；若没有这行代码，终端 UI 未来无法实时显示文本。
        self.assertEqual(events[-1].model_message.text, "你好")  # 新增代码+Stage15B: 断言最终完成事件携带完整消息；若没有这行代码，工具循环无法继续处理完整结果。


if __name__ == "__main__":  # 新增代码+Stage15B: 支持直接运行本测试文件；若没有这行代码，单文件排查不方便。
    unittest.main()  # 新增代码+Stage15B: 直接运行时启动 unittest；若没有这行代码，python 文件本身不会执行测试。
