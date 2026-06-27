from __future__ import annotations  # 新增代码+DirectChatGptSseClient: 让测试里的类型注解延迟求值；如果没有这行代码，老解释器可能更容易遇到注解兼容问题。

from pathlib import Path  # 新增代码+DirectChatGptSseClient: 用 Path 读取 SSE fixture；如果没有这行代码，测试需要硬编码字符串路径。
from typing import Any, Iterable  # 新增代码+DirectChatGptSseClient: 导入假 post_sse 的类型；如果没有这行代码，测试 helper 的契约不清楚。

from learning_agent.models.chatgpt_codex_sse import CHATGPT_CODEX_RESPONSES_ENDPOINT  # 新增代码+DirectChatGptSseClient: 导入唯一端点常量；如果没有这行代码，测试无法确认请求 URL。
from learning_agent.models.chatgpt_codex_sse import ChatGptCodexSseClient  # 新增代码+DirectChatGptSseClient: 导入被测 SSE 客户端；如果没有这行代码，测试没有对象。


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "chatgpt_codex_sse"  # 新增代码+DirectChatGptSseClient: 定位 ChatGPT Codex SSE fixture 目录；如果没有这行代码，每个测试会重复拼路径。


def _read_fixture(name: str) -> str:  # 新增代码+DirectChatGptSseClient: 函数段开始，读取指定 SSE fixture 文本；如果没有这个函数，测试读取 fixture 会重复，本段到 return 结束。
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")  # 新增代码+DirectChatGptSseClient: 返回 UTF-8 fixture 内容；如果没有这行代码，测试拿不到样本流。


def test_basic_sse_fixture_yields_deltas_before_completion() -> None:  # 新增代码+DirectChatGptSseClient: 函数段开始，验证基础 SSE 流先增量后完成；如果没有这个测试，GUI 流式展示可能退化，本段到断言结束。
    raw_stream = _read_fixture("response_stream_basic.sse")  # 新增代码+DirectChatGptSseClient: 读取成功流 fixture；如果没有这行代码，测试没有输入样本。
    events = list(ChatGptCodexSseClient.events_from_sse_text(raw_stream))  # 新增代码+DirectChatGptSseClient: 把 fixture 转成模型流事件；如果没有这行代码，无法检查事件顺序。
    text_deltas = [event.text_delta for event in events if event.event_type == "text_delta"]  # 新增代码+DirectChatGptSseClient: 提取所有文本分片；如果没有这行代码，无法确认 OPENHARNESS_ 和 OK 分开到达。
    completed_events = [event for event in events if event.event_type == "model_message_completed"]  # 新增代码+DirectChatGptSseClient: 提取完成事件；如果没有这行代码，无法确认流已结束。
    assert text_deltas == ["OPENHARNESS_", "OK"]  # 新增代码+DirectChatGptSseClient: 断言分片顺序符合 fixture；如果没有这行代码，解析器可能吞掉增量。
    assert len(completed_events) == 1  # 新增代码+DirectChatGptSseClient: 断言只完成一次；如果没有这行代码，done 和 completed 双事件可能造成重复回复。
    assert completed_events[0].model_message is not None  # 新增代码+DirectChatGptSseClient: 确认完成事件带完整消息；如果没有这行代码，主循环无法消费结果。
    assert completed_events[0].model_message.text == "OPENHARNESS_OK"  # 新增代码+DirectChatGptSseClient: 断言最终文本正确；如果没有这行代码，done 文本可能丢失。


def test_model_not_supported_fixture_becomes_model_not_available() -> None:  # 新增代码+DirectChatGptSseClient: 函数段开始，验证模型不支持错误可被 registry 识别；如果没有这个测试，GUI 会把模型不可用当普通失败，本段到断言结束。
    raw_stream = _read_fixture("response_stream_error_model_not_supported.sse")  # 新增代码+DirectChatGptSseClient: 读取错误流 fixture；如果没有这行代码，测试没有错误样本。
    events = list(ChatGptCodexSseClient.events_from_sse_text(raw_stream))  # 新增代码+DirectChatGptSseClient: 解析错误 SSE 流；如果没有这行代码，无法检查错误映射。
    assert len(events) == 1  # 新增代码+DirectChatGptSseClient: 断言错误流只产生一个错误事件；如果没有这行代码，后续处理可能重复。
    assert events[0].event_type == "model_error"  # 新增代码+DirectChatGptSseClient: 断言事件类型是模型错误；如果没有这行代码，上层不会进入错误处理。
    assert events[0].raw_event["status"] == "model_not_available"  # 新增代码+DirectChatGptSseClient: 断言状态可驱动模型 registry；如果没有这行代码，模型可用性不会更新。
    assert events[0].raw_event["code"] == "model_not_supported"  # 新增代码+DirectChatGptSseClient: 保留原始错误码；如果没有这行代码，排查真实账号权限会少证据。


def test_content_part_events_are_accepted_before_text_delta() -> None:  # 新增代码+DirectSseRealApi400Fix: 函数段开始，验证真实 ChatGPT Codex 流里的 content_part 事件不会被误判为漂移；如果没有这个测试，GUI 会在 200 SSE 后仍失败，本段到断言结束。
    raw_stream = "\n".join([  # 新增代码+DirectSseRealApi400Fix: 构造最小真实事件序列；如果没有这行代码，测试无法复现 response.content_part.added 导致的失败。
        'data: {"type":"response.created","response":{"status":"in_progress"}}',  # 新增代码+DirectSseRealApi400Fix: 模拟响应创建事件；如果没有这行代码，样本不像真实 SSE 开头。
        'data: {"type":"response.content_part.added","content_index":0,"part":{"type":"output_text","text":""}}',  # 新增代码+DirectSseRealApi400Fix: 模拟真实后端新增 content part 事件；如果没有这行代码，无法覆盖本次 GUI 失败根因。
        'data: {"type":"response.output_text.delta","delta":"OH"}',  # 新增代码+DirectSseRealApi400Fix: 模拟第一段文本增量；如果没有这行代码，无法确认 parser 会继续走到可见输出。
        'data: {"type":"response.content_part.done","content_index":0,"part":{"type":"output_text","text":"OH_FIXED_OK"}}',  # 新增代码+DirectSseRealApi400Fix: 模拟真实后端完成 content part 事件；如果没有这行代码，后续真实流可能在 done 事件处再次失败。
        'data: {"type":"response.output_text.done","text":"OH_FIXED_OK"}',  # 新增代码+DirectSseRealApi400Fix: 模拟最终文本事件；如果没有这行代码，parser 没有完成信号。
    ])  # 新增代码+DirectSseRealApi400Fix: 结束最小 SSE 样本构造；如果没有这行代码，Python 列表和 join 语法不完整。
    events = list(ChatGptCodexSseClient.events_from_sse_text(raw_stream))  # 新增代码+DirectSseRealApi400Fix: 用真实 parser 解析样本；如果没有这行代码，测试没有被测行为。
    assert [event.event_type for event in events] == ["text_delta", "model_message_completed"]  # 新增代码+DirectSseRealApi400Fix: 断言 content_part 事件被安静跳过且文本正常输出；如果没有这行代码，endpoint_drift 回归不会被发现。
    assert events[-1].model_message is not None and events[-1].model_message.text == "OH_FIXED_OK"  # 新增代码+DirectSseRealApi400Fix: 断言完成事件保留最终回答；如果没有这行代码，GUI 可能显示 completed 但答案为空。


def test_stream_responses_posts_to_chatgpt_codex_endpoint_with_oauth_headers() -> None:  # 新增代码+DirectChatGptSseClient: 函数段开始，验证真实请求契约；如果没有这个测试，端点/header/body 漂移不会被发现，本段到断言结束。
    captured: dict[str, Any] = {}  # 新增代码+DirectChatGptSseClient: 保存 fake post_sse 收到的参数；如果没有这行代码，测试无法检查请求。

    def fake_post_sse(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> Iterable[str]:  # 新增代码+DirectChatGptSseClient: 函数段开始，替代真实网络请求；如果没有这个函数，测试会联网，本段到 return 结束。
        captured["url"] = url  # 新增代码+DirectChatGptSseClient: 记录请求 URL；如果没有这行代码，无法断言端点。
        captured["headers"] = headers  # 新增代码+DirectChatGptSseClient: 记录请求头；如果没有这行代码，无法断言鉴权头。
        captured["body"] = body  # 新增代码+DirectChatGptSseClient: 记录请求体；如果没有这行代码，无法断言模型和 stream。
        captured["timeout_seconds"] = timeout_seconds  # 新增代码+DirectChatGptSseClient: 记录超时；如果没有这行代码，无法确认 timeout 传入。
        return ["data: [DONE]"]  # 新增代码+DirectChatGptSseClient: 返回最小完成流；如果没有这行代码，stream_responses 没有事件可结束。

    client = ChatGptCodexSseClient(access_token="token_test_value", model="gpt-5.5", account_id="account_test", post_sse=fake_post_sse, timeout_seconds=9)  # 新增代码+DirectChatGptSseClient: 创建带假网络的客户端；如果没有这行代码，测试无法调用 stream_responses。
    events = list(client.stream_responses(messages=[{"role": "user", "content": "ping"}], tools=None))  # 新增代码+DirectChatGptSseClient: 发起一次流式请求；如果没有这行代码，fake_post_sse 不会被调用。
    assert captured["url"] == CHATGPT_CODEX_RESPONSES_ENDPOINT  # 新增代码+DirectChatGptSseClient: 断言 URL 是唯一 Codex endpoint；如果没有这行代码，GUI 可能打到错误地址。
    assert captured["headers"]["Accept"] == "text/event-stream"  # 新增代码+DirectChatGptSseClient: 断言 SSE Accept header；如果没有这行代码，服务端可能不返回流。
    assert captured["headers"]["Authorization"] == "Bearer token_test_value"  # 新增代码+DirectChatGptSseClient: 断言 OAuth Bearer header；如果没有这行代码，真实连接会 401。
    assert captured["headers"]["ChatGPT-Account-Id"] == "account_test"  # 新增代码+DirectChatGptSseClient: 断言账号头；如果没有这行代码，多账号路由无法验证。
    assert captured["body"]["model"] == "gpt-5.5"  # 新增代码+DirectChatGptSseClient: 断言模型来自用户选择；如果没有这行代码，模型选择菜单不会生效。
    assert captured["body"]["stream"] is True  # 新增代码+DirectChatGptSseClient: 断言开启 SSE；如果没有这行代码，GUI 无法真流式。
    assert captured["timeout_seconds"] == 9  # 新增代码+DirectChatGptSseClient: 断言 timeout 透传；如果没有这行代码，延迟调优无法验证。
    assert events[-1].event_type == "model_message_completed"  # 新增代码+DirectChatGptSseClient: 断言 DONE 产生完成事件；如果没有这行代码，GUI 可能停在 running。


def test_parse_sse_text_to_response_preserves_output_text() -> None:  # 新增代码+DirectChatGptSseClient: 函数段开始，验证完整 parser 仍能产出旧 wrapper 需要的 dict；如果没有这个测试，旧 chat() 路径可能断掉，本段到断言结束。
    raw_stream = _read_fixture("response_stream_basic.sse")  # 新增代码+DirectChatGptSseClient: 读取成功流 fixture；如果没有这行代码，测试没有输入。
    parsed = ChatGptCodexSseClient.parse_sse_text_to_response(raw_stream)  # 新增代码+DirectChatGptSseClient: 用完整 parser 解析 SSE；如果没有这行代码，无法检查旧 wrapper 响应形态。
    assert parsed == {"output_text": "OPENHARNESS_OK"}  # 新增代码+DirectChatGptSseClient: 断言返回旧 wrapper 可消费的 output_text；如果没有这行代码，chat() 可能无法解析回答。
