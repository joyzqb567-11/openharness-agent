from __future__ import annotations  # 新增代码+GuiContextDirectSseBody：启用延迟类型注解；如果没有这行，部分 Python 版本处理类型时更脆弱。

from typing import Any, Iterable  # 新增代码+GuiContextDirectSseBody：导入 fake post_sse 需要的类型；如果没有这行，测试 helper 契约不清楚。

from learning_agent.models.chatgpt_codex_sse import ChatGptCodexSseClient  # 新增代码+GuiContextDirectSseBody：导入被测 Direct SSE client；如果没有这行，测试没有对象。


def test_stream_responses_preserves_text_only_message_input_body() -> None:  # 新增代码+GuiContextDirectSseBody：函数段开始，验证 client 不改写 GUI builder 产出的 text-only messages；如果没有这个测试，多轮上下文可能在 client 层退化成最后一句。
    captured: dict[str, Any] = {}  # 新增代码+GuiContextDirectSseBody：保存 fake post_sse 收到的 body；如果没有这一行，测试无法检查 input 是否原样保留。
    messages = [{"role": "user", "content": [{"type": "input_text", "text": "历史事实"}]}, {"role": "assistant", "content": [{"type": "output_text", "text": "历史回答"}]}, {"role": "user", "content": [{"type": "input_text", "text": "当前问题"}]}]  # 修改代码+GuiContextDirectSse400Fix：准备含助手 output_text 的 text-only Responses input；如果没有这一行，client body 测试无法覆盖多轮官方格式。
    def fake_post_sse(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> Iterable[str]:  # 新增代码+GuiContextDirectSseBody：函数段开始，替代真实网络并捕获请求；如果没有这个函数，测试会联网。
        captured["body"] = body  # 新增代码+GuiContextDirectSseBody：记录请求体；如果没有这一行，断言没有检查对象。
        return ["data: [DONE]"]  # 新增代码+GuiContextDirectSseBody：返回最小完成流；如果没有这一行，stream_responses 无法结束。
    client = ChatGptCodexSseClient(access_token="token_test_value", model="gpt-5.5", post_sse=fake_post_sse, timeout_seconds=9)  # 新增代码+GuiContextDirectSseBody：创建带假网络的客户端；如果没有这一行，无法调用 stream_responses。
    list(client.stream_responses(messages=messages, tools=None))  # 新增代码+GuiContextDirectSseBody：触发请求构造；如果没有这一行，fake_post_sse 不会收到 body。
    assert captured["body"]["input"] == messages  # 新增代码+GuiContextDirectSseBody：断言 input 原样等于调用方 messages；如果没有这一行，client 层改写上下文不会被发现。
    # 新增代码+GuiContextDirectSseBody：函数段结束，client body 原样保留契约到此结束。
