from __future__ import annotations  # 新增代码+DirectSseCancelTest: 延迟解析测试类型注解；如果没有这行代码，跨版本测试更脆弱。

from pathlib import Path  # 新增代码+DirectSseCancelTest: 使用 Path 处理临时 workspace；如果没有这行代码，路径字符串更容易写错。
import time  # 新增代码+DirectSseCancelTest: 等待后台 worker 进入取消终态；如果没有这行代码，测试可能在线程运行前断言。
from typing import Iterator  # 新增代码+DirectSseCancelTest: 标注 closeable SSE 行源迭代器；如果没有这行代码，测试 helper 合同不清楚。

from learning_agent.app.gui_agent_adapter import FakeStreamingGuiAgentAdapter, GuiAgentRunRequest  # 新增代码+DirectSseCancelTest: 导入被测 adapter 和请求对象；如果没有这行代码，取消测试无法运行。
from learning_agent.app.gui_bridge import GuiRunManager  # 新增代码+DirectSseCancelTest: 导入 bridge run manager 验证 partial text 写回；如果没有这行代码，只能测试 adapter 不测 bridge。
from learning_agent.app.gui_provider_secret_store import make_provider_secret_store, safe_secret_ref  # 新增代码+DirectSseCancelTest: 导入 secret store helper；如果没有这行代码，测试无法模拟 OAuth token。
from learning_agent.app.gui_provider_settings import save_provider_settings  # 新增代码+DirectSseCancelTest: 导入 provider settings 保存 helper；如果没有这行代码，adapter 会认为未连接。


class CloseableSseLines:  # 新增代码+DirectSseCancelTest: 类段开始，模拟可关闭的 HTTP SSE response 行源；如果没有这个类，测试无法证明 cancel 会关闭底层流。
    def __init__(self) -> None:  # 新增代码+DirectSseCancelTest: 函数段开始，初始化关闭状态；如果没有这段，closed 字段不存在。
        self.closed = False  # 新增代码+DirectSseCancelTest: 记录 close 是否被调用；如果没有这行代码，断言没有依据。
    # 新增代码+DirectSseCancelTest: 函数段结束，CloseableSseLines.__init__ 到此结束；如果没有边界说明，用户不容易看出它只保存状态。

    def __iter__(self) -> Iterator[str]:  # 新增代码+DirectSseCancelTest: 函数段开始，产出一个可取消的 SSE 流；如果没有这段，ChatGptCodexSseClient 无法消费行源。
        yield 'data: {"type":"response.output_text.delta","delta":"PARTIAL_"}'  # 新增代码+DirectSseCancelTest: 先产出 partial delta；如果没有这行代码，取消时没有文本可保留。
        yield 'data: {"type":"response.output_text.delta","delta":"SHOULD_NOT_BE_USED"}'  # 新增代码+DirectSseCancelTest: 后续分片不应被消费；如果没有这行代码，无法证明取消中断。
        yield 'data: {"type":"response.output_text.done","text":"PARTIAL_SHOULD_NOT_BE_USED"}'  # 新增代码+DirectSseCancelTest: 完成事件不应抵达；如果没有这行代码，无法证明 completion-after-cancel 被阻断。
    # 新增代码+DirectSseCancelTest: 函数段结束，CloseableSseLines.__iter__ 到此结束；如果没有边界说明，用户不容易看出流式顺序。

    def close(self) -> None:  # 新增代码+DirectSseCancelTest: 函数段开始，模拟 HTTP response.close；如果没有这段，取消无法证明关闭连接。
        self.closed = True  # 新增代码+DirectSseCancelTest: 标记流已关闭；如果没有这行代码，测试无法确认释放资源。
    # 新增代码+DirectSseCancelTest: 函数段结束，CloseableSseLines.close 到此结束；如果没有边界说明，用户不容易看出它是关闭钩子。


def _connect_openai_oauth(tmp_path: Path) -> None:  # 新增代码+DirectSseCancelTest: 函数段开始，在临时 workspace 写入 OAuth 连接；如果没有这个函数，取消测试会停在未连接门禁。
    secret_store = make_provider_secret_store(tmp_path, env={"OPENHARNESS_PROVIDER_SECRET_STORE": "dev_json", "OPENHARNESS_OPENAI_AUTH_MODE": "mock"})  # 新增代码+DirectSseCancelTest: 使用测试 secret store；如果没有这行代码，测试会依赖真实 OS 加密。
    access_ref = secret_store.set_secret(safe_secret_ref("openai", "access_token"), "short_token")  # 新增代码+DirectSseCancelTest: 写入短 token 并取得引用；如果没有这行代码，adapter 没有 access token。
    save_provider_settings(tmp_path, {"auth": {"openai": {"type": "oauth_real", "secret_refs": {"access_token": access_ref}, "account_id": "acct_test_001", "account_label": "Test Account", "oauth_client_source": "operator_configured", "updated_at": 1.0}}, "custom_providers": {}, "model_visibility": {}, "default_provider_id": "openai", "default_model_id": "gpt-5.5", "selected_openai_account_id": "acct_test_001", "selected_openai_account_label": "Test Account", "selected_openai_model_id": "gpt-5.5"})  # 新增代码+DirectSseCancelTest: 保存只含 secret_ref 的连接状态；如果没有这行代码，adapter 会认为未连接。


def _request(tmp_path: Path) -> GuiAgentRunRequest:  # 新增代码+DirectSseCancelTest: 函数段开始，构造可取消 Direct SSE 请求；如果没有这个函数，测试会重复长参数。
    return GuiAgentRunRequest(session_id="session_test", turn_id="turn_test", run_id="run_test", prompt="请输出 OPENHARNESS_OK", workspace=str(tmp_path), provider_id="openai", model_id="gpt-5.5", reasoning_effort="high", permission_mode="full_access")  # 新增代码+DirectSseCancelTest: 返回标准请求；如果没有这行代码，adapter 不知道 workspace/provider/model。


def test_direct_sse_cancel_closes_active_stream_and_preserves_partial_text(tmp_path: Path, monkeypatch) -> None:  # 新增代码+DirectSseCancelTest: 函数段开始，验证 adapter cancel 合同；如果没有这个测试，取消可能只改状态不关连接，本段到断言结束。
    monkeypatch.setenv("OPENHARNESS_OPENAI_RUNTIME", "direct_sse")  # 新增代码+DirectSseCancelTest: 开启 Direct SSE runtime；如果没有这行代码，测试会走 fake streaming。
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json")  # 新增代码+DirectSseCancelTest: 使用测试 secret store；如果没有这行代码，环境会影响读取。
    _connect_openai_oauth(tmp_path)  # 新增代码+DirectSseCancelTest: 写入连接状态；如果没有这行代码，测试会失败在未连接。
    closeable_lines = CloseableSseLines()  # 新增代码+DirectSseCancelTest: 创建可关闭行源；如果没有这行代码，无法检查 close。
    cancel_after_first_delta = {"value": False}  # 新增代码+DirectSseCancelTest: 保存取消触发标记；如果没有这行代码，is_cancelled 无法在 emit 后改变。

    def fake_post_sse(*_args, **_kwargs) -> CloseableSseLines:  # 新增代码+DirectSseCancelTest: 函数段开始，返回可关闭 SSE 行源；如果没有这个函数，测试会联网。
        return closeable_lines  # 新增代码+DirectSseCancelTest: 返回同一个行源对象；如果没有这行代码，断言 close 的对象不确定。

    def emit_event(event: dict[str, object]) -> None:  # 新增代码+DirectSseCancelTest: 函数段开始，收到首个 delta 后请求取消；如果没有这段，adapter 会完整跑完。
        if event.get("kind") == "message_delta":  # 新增代码+DirectSseCancelTest: 识别首个可见增量；如果没有这行代码，无法在 partial 后取消。
            cancel_after_first_delta["value"] = True  # 新增代码+DirectSseCancelTest: 设置取消标记；如果没有这行代码，is_cancelled 会一直 False。
    # 新增代码+DirectSseCancelTest: 函数段结束，emit_event 到此结束；如果没有边界说明，用户不容易看出取消触发点。

    adapter = FakeStreamingGuiAgentAdapter(direct_sse_post_sse=fake_post_sse)  # 新增代码+DirectSseCancelTest: 创建注入假网络的 adapter；如果没有这行代码，测试不能控制流。
    result = adapter.run(_request(tmp_path), emit_event, lambda: cancel_after_first_delta["value"])  # 新增代码+DirectSseCancelTest: 执行并在首个 delta 后取消；如果没有这行代码，测试没有实际行为。
    assert result.status == "cancelled"  # 新增代码+DirectSseCancelTest: 断言 adapter 返回取消；如果没有这行代码，取消可能被误当完成。
    assert result.final_text == "PARTIAL_"  # 新增代码+DirectSseCancelTest: 断言 partial text 被保留；如果没有这行代码，用户会丢掉已看见输出。
    assert closeable_lines.closed is True  # 新增代码+DirectSseCancelTest: 断言底层行源被关闭；如果没有这行代码，HTTP response 可能泄漏。


def test_bridge_cancelled_turn_keeps_partial_assistant_text(tmp_path: Path, monkeypatch) -> None:  # 新增代码+DirectSseCancelTest: 函数段开始，验证 bridge 写回 partial text；如果没有这个测试，adapter 正确但 GUI 消息仍可能丢文本，本段到断言结束。
    monkeypatch.setenv("OPENHARNESS_OPENAI_RUNTIME", "direct_sse")  # 新增代码+DirectSseCancelTest: 开启 Direct SSE runtime；如果没有这行代码，run manager 会走 fake streaming。
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json")  # 新增代码+DirectSseCancelTest: 使用测试 secret store；如果没有这行代码，环境会影响读取。
    _connect_openai_oauth(tmp_path)  # 新增代码+DirectSseCancelTest: 写入连接状态；如果没有这行代码，run manager 会未连接失败。
    closeable_lines = CloseableSseLines()  # 新增代码+DirectSseCancelTest: 创建可关闭行源；如果没有这行代码，adapter 无流可读。

    def fake_post_sse(*_args, **_kwargs) -> CloseableSseLines:  # 新增代码+DirectSseCancelTest: 函数段开始，返回可关闭 SSE 行源；如果没有这个函数，run manager 会联网。
        return closeable_lines  # 新增代码+DirectSseCancelTest: 返回同一个行源；如果没有这行代码，关闭断言不稳定。

    class CancelAfterDeltaAdapter(FakeStreamingGuiAgentAdapter):  # 新增代码+DirectSseCancelTest: 类段开始，在 bridge 事件写入后触发取消；如果没有这个类，run manager 很难精确取消在 partial 后。
        def _emit(self, events, emit_event, event):  # 新增代码+DirectSseCancelTest: 函数段开始，扩展发射逻辑；如果没有这段，无法在 message_delta 后设置取消信号。
            super()._emit(events, emit_event, event)  # 新增代码+DirectSseCancelTest: 先执行正常发射；如果没有这行代码，bridge 收不到事件。
            if event.get("kind") == "message_delta":  # 新增代码+DirectSseCancelTest: 识别 partial delta；如果没有这行代码，取消触发时机不对。
                manager.cancel_events[event["turn_id"]].set()  # 新增代码+DirectSseCancelTest: 直接设置当前 turn 的取消信号；如果没有这行代码，adapter 不会在 partial 后取消。
        # 新增代码+DirectSseCancelTest: 函数段结束，CancelAfterDeltaAdapter._emit 到此结束；如果没有边界说明，用户不容易看出它只用于测试。
    # 新增代码+DirectSseCancelTest: 类段结束，CancelAfterDeltaAdapter 到此结束；如果没有边界说明，用户不容易看出它是测试替身。

    manager = GuiRunManager(tmp_path, agent_adapter=CancelAfterDeltaAdapter(direct_sse_post_sse=fake_post_sse))  # 新增代码+DirectSseCancelTest: 创建注入取消 adapter 的 run manager；如果没有这行代码，bridge 写回逻辑无法测试。
    response = manager.start_message("session_test", "请输出 OPENHARNESS_OK", provider_id="openai", model_id="gpt-5.5")  # 新增代码+DirectSseCancelTest: 提交一轮 GUI 消息；如果没有这行代码，worker 不会运行。
    turn_id = str(response["turn_id"])  # 新增代码+DirectSseCancelTest: 保存 turn id；如果没有这行代码，后续无法查状态。
    for _ in range(200):  # 新增代码+DirectSseCancelTest: 等待后台 worker 进入终态；如果没有这行代码，测试会抢在线程前断言。
        if manager.turns[turn_id].status == "cancelled":  # 新增代码+DirectSseCancelTest: 检查是否已取消；如果没有这行代码，循环不知道何时结束。
            break  # 新增代码+DirectSseCancelTest: 已取消时退出等待；如果没有这行代码，测试会无谓等待。
        time.sleep(0.01)  # 新增代码+DirectSseCancelTest: 给后台线程一点执行时间；如果没有这行代码，循环可能空转导致 flaky。
    assistant_messages = [message for message in manager.sessions["session_test"].messages if message.role == "assistant" and message.turn_id == turn_id]  # 新增代码+DirectSseCancelTest: 找到本轮助手消息；如果没有这行代码，无法检查 GUI 可见文本。
    assert manager.turns[turn_id].status == "cancelled"  # 新增代码+DirectSseCancelTest: 断言 turn 已取消；如果没有这行代码，worker 可能仍 running。
    assert assistant_messages[0].text == "PARTIAL_"  # 新增代码+DirectSseCancelTest: 断言 bridge 保留 partial text；如果没有这行代码，GUI 会显示空取消消息。
    assert closeable_lines.closed is True  # 新增代码+DirectSseCancelTest: 断言行源被关闭；如果没有这行代码，bridge 取消可能泄漏连接。
