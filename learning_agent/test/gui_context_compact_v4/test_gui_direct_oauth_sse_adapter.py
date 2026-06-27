from __future__ import annotations  # 新增代码+DirectSseAdapterTest: 延迟解析测试类型注解；如果没有这行代码，跨版本运行更脆弱。

from pathlib import Path  # 新增代码+DirectSseAdapterTest: 使用 Path 读取 fixture；如果没有这行代码，路径拼接会更脆弱。
from typing import Any, Iterable  # 新增代码+DirectSseAdapterTest: 标注 fake post_sse 参数；如果没有这行代码，测试 helper 合同不清楚。

from learning_agent.app.gui_agent_adapter import FakeStreamingGuiAgentAdapter, GuiAgentRunRequest  # 新增代码+DirectSseAdapterTest: 导入被测 GUI adapter 和请求对象；如果没有这行代码，测试无法运行 Direct SSE。
from learning_agent.app.gui_provider_openai_models import save_openai_model_probe_result  # 新增代码+DirectSseAdapterTest: 导入模型 registry 写入 helper；如果没有这行代码，unsupported 模型门禁无法测试。
from learning_agent.app.gui_provider_secret_store import make_provider_secret_store, safe_secret_ref  # 新增代码+DirectSseAdapterTest: 导入 secret store helper；如果没有这行代码，测试无法模拟 OAuth token 引用。
from learning_agent.app.gui_provider_settings import save_provider_settings  # 新增代码+DirectSseAdapterTest: 导入 provider settings 保存 helper；如果没有这行代码，adapter 无法读取已连接状态。
import learning_agent.app.gui_agent_adapter as gui_agent_adapter_module  # 新增代码+DirectSseLatencyBudgetTest：导入模块对象以 monkeypatch time；如果没有这行，首包预算测试无法稳定控制时间。


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "chatgpt_codex_sse"  # 新增代码+DirectSseAdapterTest: 定位 ChatGPT Codex SSE fixture 目录；如果没有这行代码，测试会重复硬编码路径。


def _request(tmp_path: Path, model_id: str = "gpt-5.5") -> GuiAgentRunRequest:  # 新增代码+DirectSseAdapterTest: 函数段开始，构造标准 GUI adapter 请求；如果没有这个函数，测试会重复长参数，本段到 return 结束。
    return GuiAgentRunRequest(session_id="session_test", turn_id="turn_test", run_id="run_test", prompt="请输出 OPENHARNESS_OK", workspace=str(tmp_path), provider_id="openai", model_id=model_id, reasoning_effort="ultra", permission_mode="full_access")  # 新增代码+DirectSseAdapterTest: 返回带 OpenAI 模型选择的请求；如果没有这行代码，adapter 不知道 workspace/provider/model。


def _connect_openai_oauth(tmp_path: Path) -> None:  # 新增代码+DirectSseAdapterTest: 函数段开始，在临时 workspace 模拟已连接 OpenAI OAuth；如果没有这个函数，direct_sse 测试会停在 provider_not_connected，本段到 save 结束。
    secret_store = make_provider_secret_store(tmp_path, env={"OPENHARNESS_PROVIDER_SECRET_STORE": "dev_json", "OPENHARNESS_OPENAI_AUTH_MODE": "mock"})  # 新增代码+DirectSseAdapterTest: 使用开发 secret store 写入短测试 token；如果没有这行代码，测试会依赖用户真实 OS 加密状态。
    access_ref = secret_store.set_secret(safe_secret_ref("openai", "access_token"), "short_token")  # 新增代码+DirectSseAdapterTest: 写入短 access token 并取得引用；如果没有这行代码，adapter 无法构造 Authorization。
    save_provider_settings(tmp_path, {"auth": {"openai": {"type": "oauth_real", "secret_refs": {"access_token": access_ref}, "account_id": "acct_test_001", "account_label": "Test Account", "oauth_client_source": "operator_configured", "updated_at": 1.0}}, "custom_providers": {}, "model_visibility": {}, "default_provider_id": "openai", "default_model_id": "gpt-5.5", "selected_openai_account_id": "acct_test_001", "selected_openai_account_label": "Test Account", "selected_openai_model_id": "gpt-5.5"})  # 新增代码+DirectSseAdapterTest: 保存只含 secret_ref 的 OAuth 连接记录；如果没有这行代码，adapter 会认为 provider 未连接。


def _fixture_lines() -> list[str]:  # 新增代码+DirectSseAdapterTest: 函数段开始，读取成功 SSE fixture 行；如果没有这个函数，fake post_sse 没有返回流，本段到 return 结束。
    return (FIXTURE_DIR / "response_stream_basic.sse").read_text(encoding="utf-8").splitlines()  # 新增代码+DirectSseAdapterTest: 返回 fixture 行列表；如果没有这行代码，测试无法模拟流式响应。


def test_direct_sse_adapter_emits_runtime_path_and_streaming_events(tmp_path: Path, monkeypatch) -> None:  # 新增代码+DirectSseAdapterTest: 函数段开始，验证 direct_sse 成功路径；如果没有这个测试，GUI 可能仍走 Codex CLI 或 fake，本段到断言结束。
    monkeypatch.setenv("OPENHARNESS_OPENAI_RUNTIME", "direct_sse")  # 新增代码+DirectSseAdapterTest: 开启 Direct SSE runtime；如果没有这行代码，adapter 会走普通 fake streaming。
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json")  # 新增代码+DirectSseAdapterTest: 指定测试用 dev secret store；如果没有这行代码，Windows DPAPI 环境会影响测试。
    _connect_openai_oauth(tmp_path)  # 新增代码+DirectSseAdapterTest: 写入已连接 OAuth 状态；如果没有这行代码，测试会失败在未连接门禁。
    captured: dict[str, Any] = {}  # 新增代码+DirectSseAdapterTest: 保存 fake post_sse 收到的请求；如果没有这行代码，无法确认 model/account 传入。

    def fake_post_sse(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> Iterable[str]:  # 新增代码+DirectSseAdapterTest: 函数段开始，替代真实 ChatGPT 网络；如果没有这个函数，测试会联网，本段到 return 结束。
        captured["headers"] = headers  # 新增代码+DirectSseAdapterTest: 记录请求头；如果没有这行代码，无法确认账号头和 Bearer。
        captured["body"] = body  # 新增代码+DirectSseAdapterTest: 记录请求体；如果没有这行代码，无法确认模型选择。
        return _fixture_lines()  # 新增代码+DirectSseAdapterTest: 返回成功 SSE fixture；如果没有这行代码，adapter 没有流式事件。

    events: list[dict[str, object]] = []  # 新增代码+DirectSseAdapterTest: 保存 adapter 发出的事件；如果没有这行代码，测试无法检查事件类型。
    result = FakeStreamingGuiAgentAdapter(direct_sse_post_sse=fake_post_sse).run(_request(tmp_path), events.append, lambda: False)  # 新增代码+DirectSseAdapterTest: 执行 Direct SSE adapter；如果没有这行代码，测试没有实际行为。
    event_types = [str(event["kind"]) for event in events]  # 新增代码+DirectSseAdapterTest: 提取事件类型顺序；如果没有这行代码，断言会重复索引。
    assert result.status == "completed"  # 新增代码+DirectSseAdapterTest: 断言 adapter 完成；如果没有这行代码，成功路径可能回归。
    assert result.final_text == "OPENHARNESS_OK"  # 新增代码+DirectSseAdapterTest: 断言最终文本来自 SSE done；如果没有这行代码，消息完成可能为空。
    assert event_types[0] == "runtime_path"  # 新增代码+DirectSseAdapterTest: 断言首事件是 runtime_path；如果没有这行代码，诊断无法第一时间确认路线。
    assert "message_delta" in event_types  # 新增代码+DirectSseAdapterTest: 断言存在流式 delta；如果没有这行代码，GUI 可能只显示最终答案。
    assert "direct_sse_completed" in event_types  # 新增代码+DirectSseAdapterTest: 断言存在 Direct SSE 完成诊断；如果没有这行代码，状态面板缺少完成证据。
    assert events[0]["payload"]["codex_cli_used"] is False  # 新增代码+DirectSseAdapterTest: 断言没有走 Codex CLI；如果没有这行代码，慢路径可能被隐藏。
    assert events[0]["payload"]["websocket_enabled"] is False  # 新增代码+DirectSseAdapterTest: 断言 WebSocket 被禁用；如果没有这行代码，WS fallback 回归不明显。
    assert events[0]["payload"]["oauth_client_source"] == "operator_configured"  # 新增代码+DirectSseLatencyBudgetTest：断言第一条 runtime_path 带 OAuth client 来源；如果没有这行，诊断无法确认真实配置来源。
    assert captured["headers"]["ChatGPT-Account-Id"] == "acct_test_001"  # 新增代码+DirectSseAdapterTest: 断言账号头透传；如果没有这行代码，多账号 OAuth 可能请求错账号。
    assert captured["body"]["model"] == "gpt-5.5"  # 新增代码+DirectSseAdapterTest: 断言模型来自 GUI 选择；如果没有这行代码，底部模型菜单不会生效。
    assert captured["body"]["reasoning"] == {"effort": "xhigh"}  # 新增代码+DirectSseRealApi400Fix: 断言 GUI 的“超高/ultra”被翻译成 ChatGPT Codex 接受的 xhigh；如果没有这行代码，真实后端会返回 reasoning.effort invalid_value。
    assert "metadata" not in captured["body"]  # 新增代码+DirectSseRealApi400Fix: 断言 OpenHarness 内部诊断字段不会进入 ChatGPT 请求体；如果没有这行代码，真实后端会返回 Unsupported parameter: metadata。


def test_direct_sse_adapter_marks_first_delta_budget_exceeded(tmp_path: Path, monkeypatch) -> None:  # 新增代码+DirectSseLatencyBudgetTest：函数段开始，验证首个 delta 超过 5 秒会进入诊断；如果没有这个测试，慢回复预算可能失效。
    monkeypatch.setenv("OPENHARNESS_OPENAI_RUNTIME", "direct_sse")  # 新增代码+DirectSseLatencyBudgetTest：开启 Direct SSE runtime；如果没有这行代码，adapter 会走普通 fake streaming。
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json")  # 新增代码+DirectSseLatencyBudgetTest：指定测试用 dev secret store；如果没有这行代码，环境 secret store 会影响测试。
    _connect_openai_oauth(tmp_path)  # 新增代码+DirectSseLatencyBudgetTest：写入已连接 OAuth 状态；如果没有这行代码，测试会失败在未连接门禁。
    monotonic_values = iter([100.0, 106.2, 107.0, 107.0])  # 新增代码+DirectSseLatencyBudgetTest：准备模拟时间序列；如果没有这行，首包延迟无法稳定超过预算。
    monkeypatch.setattr(gui_agent_adapter_module.time, "monotonic", lambda: next(monotonic_values))  # 新增代码+DirectSseLatencyBudgetTest：替换模块内 monotonic；如果没有这行，测试会依赖真实机器速度。

    def fake_post_sse(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> Iterable[str]:  # 新增代码+DirectSseLatencyBudgetTest：函数段开始，替代真实 ChatGPT 网络；如果没有这个函数，测试会联网。
        return _fixture_lines()  # 新增代码+DirectSseLatencyBudgetTest：返回成功 SSE fixture；如果没有这行，adapter 没有 delta 可测。

    events: list[dict[str, object]] = []  # 新增代码+DirectSseLatencyBudgetTest：保存 adapter 发出的事件；如果没有这行，无法检查 payload。
    result = FakeStreamingGuiAgentAdapter(direct_sse_post_sse=fake_post_sse).run(_request(tmp_path), events.append, lambda: False)  # 新增代码+DirectSseLatencyBudgetTest：执行 Direct SSE adapter；如果没有这行，测试没有实际行为。
    first_delta = next(event for event in events if event["kind"] == "message_delta")  # 新增代码+DirectSseLatencyBudgetTest：找到第一条 message_delta；如果没有这行，后续断言没有目标。
    assert result.status == "completed"  # 新增代码+DirectSseLatencyBudgetTest：确认慢首包仍可完成；如果没有这行，预算诊断可能误中断请求。
    assert first_delta["payload"]["first_delta_latency_ms"] == 6200  # 新增代码+DirectSseLatencyBudgetTest：确认首包延迟按模拟时间写入；如果没有这行，诊断数字可能错误。
    assert first_delta["payload"]["first_delta_budget_ms"] == 5000  # 新增代码+DirectSseLatencyBudgetTest：确认健康预算随事件公开；如果没有这行，用户只看到慢但不知道阈值。
    assert first_delta["payload"]["first_delta_budget_exceeded"] is True  # 新增代码+DirectSseLatencyBudgetTest：确认超过 5 秒被显式标记；如果没有这行，慢回复问题无法自动诊断。


def test_direct_sse_adapter_emits_provider_not_connected(tmp_path: Path, monkeypatch) -> None:  # 新增代码+DirectSseAdapterTest: 函数段开始，验证未连接 provider 门禁；如果没有这个测试，空 token 可能被发到远端，本段到断言结束。
    monkeypatch.setenv("OPENHARNESS_OPENAI_RUNTIME", "direct_sse")  # 新增代码+DirectSseAdapterTest: 开启 Direct SSE runtime；如果没有这行代码，未连接路径不会进入 direct adapter。
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json")  # 新增代码+DirectSseAdapterTest: 使用测试 secret store；如果没有这行代码，环境状态可能影响测试。
    events: list[dict[str, object]] = []  # 新增代码+DirectSseAdapterTest: 保存事件；如果没有这行代码，无法检查 provider_not_connected。
    result = FakeStreamingGuiAgentAdapter().run(_request(tmp_path), events.append, lambda: False)  # 新增代码+DirectSseAdapterTest: 执行未连接请求；如果没有这行代码，测试没有行为。
    assert result.status == "failed"  # 新增代码+DirectSseAdapterTest: 断言未连接失败；如果没有这行代码，adapter 可能假装成功。
    assert result.error_code == "provider_not_connected"  # 新增代码+DirectSseAdapterTest: 断言错误码稳定；如果没有这行代码，前端无法分支提示连接。
    assert any(event["kind"] == "provider_not_connected" for event in events)  # 新增代码+DirectSseAdapterTest: 断言发出可见事件；如果没有这行代码，诊断面板看不到原因。


def test_direct_sse_adapter_blocks_known_unsupported_model(tmp_path: Path, monkeypatch) -> None:  # 新增代码+DirectSseAdapterTest: 函数段开始，验证本地 unsupported 模型门禁；如果没有这个测试，已知坏模型会继续慢请求，本段到断言结束。
    monkeypatch.setenv("OPENHARNESS_OPENAI_RUNTIME", "direct_sse")  # 新增代码+DirectSseAdapterTest: 开启 Direct SSE runtime；如果没有这行代码，unsupported 门禁不会运行。
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json")  # 新增代码+DirectSseAdapterTest: 使用测试 secret store；如果没有这行代码，环境状态可能影响测试。
    _connect_openai_oauth(tmp_path)  # 新增代码+DirectSseAdapterTest: 写入连接状态；如果没有这行代码，测试会先失败在未连接。
    save_openai_model_probe_result(tmp_path, "gpt-5.4-mini", "not_supported_for_account", "not supported")  # 新增代码+DirectSseAdapterTest: 写入模型不支持状态；如果没有这行代码，adapter 不会本地拦截。
    called = {"post_sse": False}  # 新增代码+DirectSseAdapterTest: 记录 fake 网络是否被调用；如果没有这行代码，无法证明已本地拦截。

    def fake_post_sse(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> Iterable[str]:  # 新增代码+DirectSseAdapterTest: 函数段开始，若被调用说明门禁失败；如果没有这个函数，测试无法检查是否联网，本段到 return 结束。
        called["post_sse"] = True  # 新增代码+DirectSseAdapterTest: 标记网络被调用；如果没有这行代码，断言没有依据。
        return _fixture_lines()  # 新增代码+DirectSseAdapterTest: 返回普通 fixture；如果没有这行代码，函数签名不完整。

    events: list[dict[str, object]] = []  # 新增代码+DirectSseAdapterTest: 保存事件；如果没有这行代码，无法检查 model_not_available。
    result = FakeStreamingGuiAgentAdapter(direct_sse_post_sse=fake_post_sse).run(_request(tmp_path, model_id="gpt-5.4-mini"), events.append, lambda: False)  # 新增代码+DirectSseAdapterTest: 执行 unsupported 模型请求；如果没有这行代码，测试没有行为。
    assert result.status == "failed"  # 新增代码+DirectSseAdapterTest: 断言失败；如果没有这行代码，unsupported 可能误完成。
    assert result.error_code == "model_not_available"  # 新增代码+DirectSseAdapterTest: 断言错误码可供前端识别；如果没有这行代码，模型菜单不会得到正确提示。
    assert called["post_sse"] is False  # 新增代码+DirectSseAdapterTest: 断言没有发起网络；如果没有这行代码，慢请求问题会回归。
    assert any(event["kind"] == "model_not_available" for event in events)  # 新增代码+DirectSseAdapterTest: 断言发出可见模型错误事件；如果没有这行代码，用户只会看到泛化失败。


def test_direct_sse_adapter_emits_total_turn_timeout(tmp_path: Path, monkeypatch) -> None:  # 新增代码+DirectSseAdapterTest: 函数段开始，验证 timeout class 事件；如果没有这个测试，慢请求只会显示 request_failed，本段到断言结束。
    monkeypatch.setenv("OPENHARNESS_OPENAI_RUNTIME", "direct_sse")  # 新增代码+DirectSseAdapterTest: 开启 Direct SSE runtime；如果没有这行代码，timeout 不会进入 direct adapter。
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json")  # 新增代码+DirectSseAdapterTest: 使用测试 secret store；如果没有这行代码，环境状态可能影响测试。
    _connect_openai_oauth(tmp_path)  # 新增代码+DirectSseAdapterTest: 写入连接状态；如果没有这行代码，测试会先失败在未连接。

    def fake_post_sse(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> Iterable[str]:  # 新增代码+DirectSseAdapterTest: 函数段开始，模拟总超时；如果没有这个函数，测试不能稳定触发 timeout，本段到 raise 结束。
        raise TimeoutError("total timeout for test")  # 新增代码+DirectSseAdapterTest: 抛出显式 timeout；如果没有这行代码，adapter 不会产生 timeout class。

    events: list[dict[str, object]] = []  # 新增代码+DirectSseAdapterTest: 保存事件；如果没有这行代码，无法检查 total_turn_timeout。
    result = FakeStreamingGuiAgentAdapter(direct_sse_post_sse=fake_post_sse).run(_request(tmp_path), events.append, lambda: False)  # 新增代码+DirectSseAdapterTest: 执行 timeout 请求；如果没有这行代码，测试没有行为。
    assert result.status == "failed"  # 新增代码+DirectSseAdapterTest: 断言失败；如果没有这行代码，timeout 可能误完成。
    assert result.error_code == "total_turn_timeout"  # 新增代码+DirectSseAdapterTest: 断言 timeout 错误码；如果没有这行代码，前端无法分类慢请求。
    assert any(event["kind"] == "total_turn_timeout" for event in events)  # 新增代码+DirectSseAdapterTest: 断言可见 timeout 事件；如果没有这行代码，诊断面板没有 timeout class。


def test_direct_sse_adapter_retries_once_after_context_overflow_before_visible_delta(tmp_path: Path, monkeypatch) -> None:  # 新增代码+ReactiveDirectSseCompactTest：函数段开始，验证未显示文本前遇到上下文超限会压缩并重试一次；如果没有这个测试，prompt too long 会直接让 GUI 失败。
    monkeypatch.setenv("OPENHARNESS_OPENAI_RUNTIME", "direct_sse")  # 新增代码+ReactiveDirectSseCompactTest：开启 Direct SSE runtime；如果没有这行代码，adapter 会走普通 fake streaming。
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json")  # 新增代码+ReactiveDirectSseCompactTest：使用测试 secret store；如果没有这行代码，环境中的真实 secret store 会影响测试。
    _connect_openai_oauth(tmp_path)  # 新增代码+ReactiveDirectSseCompactTest：写入已连接 OAuth 状态；如果没有这行代码，测试会先失败在 provider_not_connected。
    calls: list[dict[str, object]] = []  # 新增代码+ReactiveDirectSseCompactTest：记录每次 Direct SSE 请求体；如果没有这行代码，无法证明只重试一次。

    def fake_post_sse(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> Iterable[str]:  # 新增代码+ReactiveDirectSseCompactTest：函数段开始，第一次返回超限错误第二次返回成功 fixture；如果没有这个函数，测试会联网。
        calls.append(body)  # 新增代码+ReactiveDirectSseCompactTest：保存请求体；如果没有这行代码，断言无法知道请求次数和 body。
        if len(calls) == 1:  # 新增代码+ReactiveDirectSseCompactTest：识别第一次请求；如果没有这行代码，无法模拟先失败后成功。
            return ['data: {"error": {"code": "context_length_exceeded", "message": "prompt too long for reactive compact test"}}']  # 新增代码+ReactiveDirectSseCompactTest：返回上下文超限 SSE 错误；如果没有这行代码，reactive compact 分支不会被触发。
        return _fixture_lines()  # 新增代码+ReactiveDirectSseCompactTest：第二次返回成功流；如果没有这行代码，重试后无法完成。
    # 新增代码+ReactiveDirectSseCompactTest：函数段结束，fake_post_sse 到此结束；如果没有边界说明，用户不容易看出它只模拟远端 SSE。

    request = _request(tmp_path)  # 新增代码+ReactiveDirectSseCompactTest：创建标准请求；如果没有这行代码，adapter 缺少 workspace/provider/model。
    request.messages = [{"role": "user", "content": [{"type": "input_text", "text": f"历史上下文 {index} ALPHA_CONTEXT_927"}]} for index in range(12)]  # 新增代码+ReactiveDirectSseCompactTest：放入多轮上下文消息；如果没有这行代码，重试无法验证 request.messages 会被压缩替换。
    events: list[dict[str, object]] = []  # 新增代码+ReactiveDirectSseCompactTest：收集 adapter 事件；如果没有这行代码，无法检查 reactive_compact_completed。
    result = FakeStreamingGuiAgentAdapter(direct_sse_post_sse=fake_post_sse).run(request, events.append, lambda: False)  # 新增代码+ReactiveDirectSseCompactTest：执行被测 adapter；如果没有这行代码，测试没有实际行为。

    assert result.status == "completed"  # 新增代码+ReactiveDirectSseCompactTest：确认重试后成功完成；如果没有这行代码，重试可能仍然返回失败。
    assert len(calls) == 2  # 新增代码+ReactiveDirectSseCompactTest：确认最多且实际只重试一次；如果没有这行代码，无限重试或不重试都可能漏掉。
    assert len(calls[1]["input"]) <= len(calls[0]["input"])  # 新增代码+ReactiveDirectSseCompactTest：确认第二次请求没有比第一次更长；如果没有这行代码，compact 可能没有作用。
    assert any(event["kind"] == "reactive_compact_completed" for event in events)  # 新增代码+ReactiveDirectSseCompactTest：确认可见事件记录 reactive compact；如果没有这行代码，GUI 状态面板无法解释为什么有第二次请求。
# 新增代码+ReactiveDirectSseCompactTest：测试段结束，未显示文本前压缩重试测试到此结束；如果没有边界说明，用户不容易看出本测试锁定的是成功恢复路径。


def test_direct_sse_adapter_does_not_retry_context_error_after_visible_delta(tmp_path: Path, monkeypatch) -> None:  # 新增代码+ReactiveDirectSseCompactTest：函数段开始，验证已经显示文本后遇到超限错误不能重试；如果没有这个测试，GUI 可能把两次模型输出混到同一条消息。
    monkeypatch.setenv("OPENHARNESS_OPENAI_RUNTIME", "direct_sse")  # 新增代码+ReactiveDirectSseCompactTest：开启 Direct SSE runtime；如果没有这行代码，adapter 会走普通 fake streaming。
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json")  # 新增代码+ReactiveDirectSseCompactTest：使用测试 secret store；如果没有这行代码，环境中的真实 secret store 会影响测试。
    _connect_openai_oauth(tmp_path)  # 新增代码+ReactiveDirectSseCompactTest：写入已连接 OAuth 状态；如果没有这行代码，测试会先失败在 provider_not_connected。
    calls: list[dict[str, object]] = []  # 新增代码+ReactiveDirectSseCompactTest：记录请求体；如果没有这行代码，无法证明没有第二次请求。

    def fake_post_sse(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> Iterable[str]:  # 新增代码+ReactiveDirectSseCompactTest：函数段开始，先返回可见 delta 再返回超限错误；如果没有这个函数，测试会联网。
        calls.append(body)  # 新增代码+ReactiveDirectSseCompactTest：保存请求体；如果没有这行代码，无法断言请求次数。
        return ['data: {"type": "response.output_text.delta", "delta": "partial visible text"}', 'data: {"error": {"code": "context_length_exceeded", "message": "prompt too long after visible delta"}}']  # 新增代码+ReactiveDirectSseCompactTest：返回已流出文本后的上下文错误；如果没有这行代码，禁止重试分支不会被覆盖。
    # 新增代码+ReactiveDirectSseCompactTest：函数段结束，fake_post_sse 到此结束；如果没有边界说明，用户不容易看出它只模拟远端 SSE。

    events: list[dict[str, object]] = []  # 新增代码+ReactiveDirectSseCompactTest：收集 adapter 事件；如果没有这行代码，无法检查 message_delta 和 reactive 事件。
    result = FakeStreamingGuiAgentAdapter(direct_sse_post_sse=fake_post_sse).run(_request(tmp_path), events.append, lambda: False)  # 新增代码+ReactiveDirectSseCompactTest：执行被测 adapter；如果没有这行代码，测试没有实际行为。

    assert result.status == "failed"  # 新增代码+ReactiveDirectSseCompactTest：确认已流出文本后的错误仍按失败结束；如果没有这行代码，adapter 可能误报成功。
    assert len(calls) == 1  # 新增代码+ReactiveDirectSseCompactTest：确认没有二次请求；如果没有这行代码，可见 delta 后重试的混流风险不会被发现。
    assert any(event["kind"] == "message_delta" for event in events)  # 新增代码+ReactiveDirectSseCompactTest：确认测试确实先产生了可见文本；如果没有这行代码，禁止重试断言可能是空路径。
    assert not any(event["kind"] == "reactive_compact_completed" for event in events)  # 新增代码+ReactiveDirectSseCompactTest：确认没有 reactive compact 事件；如果没有这行代码，已流出文本后的错误仍可能触发重试。
# 新增代码+ReactiveDirectSseCompactTest：测试段结束，已显示文本后禁止重试测试到此结束；如果没有边界说明，用户不容易看出本测试锁定的是混流保护。
