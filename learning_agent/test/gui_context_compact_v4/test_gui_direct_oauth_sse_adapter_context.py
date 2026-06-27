from __future__ import annotations  # 新增代码+GuiContextDirectSseAdapter：启用延迟类型注解；如果没有这行，跨版本运行更容易受注解影响。

from pathlib import Path  # 新增代码+GuiContextDirectSseAdapter：导入 Path 管理临时 workspace；如果没有这行，测试路径拼接会更脆弱。
from typing import Any, Iterable  # 新增代码+GuiContextDirectSseAdapter：导入 fake 网络函数类型；如果没有这行，测试 helper 契约不清楚。

from learning_agent.app.gui_agent_adapter import FakeStreamingGuiAgentAdapter, GuiAgentRunRequest  # 新增代码+GuiContextDirectSseAdapter：导入被测 adapter 和请求对象；如果没有这行，测试无法运行。
from learning_agent.app.gui_provider_secret_store import make_provider_secret_store, safe_secret_ref  # 新增代码+GuiContextDirectSseAdapter：导入测试 secret store；如果没有这行，测试无法模拟 OAuth token。
from learning_agent.app.gui_provider_settings import save_provider_settings  # 新增代码+GuiContextDirectSseAdapter：导入 provider settings 保存 helper；如果没有这行，adapter 会认为 OpenAI 未连接。


def _connect_openai_oauth(tmp_path: Path) -> None:  # 新增代码+GuiContextDirectSseAdapter：函数段开始，在临时 workspace 模拟已连接 OpenAI OAuth；如果没有这段函数，测试会停在 provider_not_connected。
    secret_store = make_provider_secret_store(tmp_path, env={"OPENHARNESS_PROVIDER_SECRET_STORE": "dev_json", "OPENHARNESS_OPENAI_AUTH_MODE": "mock"})  # 新增代码+GuiContextDirectSseAdapter：创建测试用 dev secret store；如果没有这一行，测试会依赖用户真实系统密钥。
    access_ref = secret_store.set_secret(safe_secret_ref("openai", "access_token"), "short_token")  # 新增代码+GuiContextDirectSseAdapter：写入短 access token 并取得引用；如果没有这一行，adapter 无法构造 Authorization。
    save_provider_settings(tmp_path, {"auth": {"openai": {"type": "oauth_real", "secret_refs": {"access_token": access_ref}, "account_id": "acct_test_001", "account_label": "Test Account", "oauth_client_source": "operator_configured", "updated_at": 1.0}}, "custom_providers": {}, "model_visibility": {}, "default_provider_id": "openai", "default_model_id": "gpt-5.5", "selected_openai_account_id": "acct_test_001", "selected_openai_account_label": "Test Account", "selected_openai_model_id": "gpt-5.5"})  # 新增代码+GuiContextDirectSseAdapter：保存只含 secret_ref 的 OAuth 连接记录；如果没有这一行，adapter 会拒绝 Direct SSE。
    # 新增代码+GuiContextDirectSseAdapter：函数段结束，_connect_openai_oauth 到此结束；这段边界说明方便用户知道它只准备测试连接状态。


def test_direct_sse_adapter_uses_request_messages_when_present(tmp_path: Path, monkeypatch) -> None:  # 新增代码+GuiContextDirectSseAdapter：函数段开始，验证 adapter 优先使用 request.messages；如果没有这个测试，Direct SSE 可能继续只发最后一句 prompt。
    monkeypatch.setenv("OPENHARNESS_OPENAI_RUNTIME", "direct_sse")  # 新增代码+GuiContextDirectSseAdapter：开启 Direct SSE runtime；如果没有这一行，adapter 会走 fake streaming。
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json")  # 新增代码+GuiContextDirectSseAdapter：指定测试 secret store；如果没有这一行，系统真实 secret store 会影响测试。
    _connect_openai_oauth(tmp_path)  # 新增代码+GuiContextDirectSseAdapter：写入已连接 OAuth 状态；如果没有这一行，测试会失败在未连接门禁。
    captured: dict[str, Any] = {}  # 新增代码+GuiContextDirectSseAdapter：保存 fake post_sse 收到的请求体；如果没有这一行，测试无法检查 input。
    request_messages = [{"role": "user", "content": [{"type": "input_text", "text": "历史事实 ALPHA_CONTEXT_927"}]}, {"role": "assistant", "content": [{"type": "output_text", "text": "已记住。"}]}, {"role": "user", "content": [{"type": "input_text", "text": "当前追问是什么？"}]}]  # 修改代码+GuiContextDirectSse400Fix：准备用户 input_text、助手 output_text、当前用户 input_text 的真实多轮上下文；如果没有这一行，adapter 测试无法覆盖官方 400 根因。
    def fake_post_sse(url: str, headers: dict[str, str], body: dict[str, object], timeout_seconds: float) -> Iterable[str]:  # 新增代码+GuiContextDirectSseAdapter：函数段开始，替代真实网络并捕获 body；如果没有这个函数，测试会联网。
        captured["body"] = body  # 新增代码+GuiContextDirectSseAdapter：记录请求体；如果没有这一行，断言没有检查对象。
        return ["data: [DONE]"]  # 新增代码+GuiContextDirectSseAdapter：返回最小完成流；如果没有这一行，adapter 无法结束。
    request = GuiAgentRunRequest(session_id="session_test", turn_id="turn_test", run_id="run_test", prompt="只应作为 fallback 的 prompt", workspace=str(tmp_path), provider_id="openai", model_id="gpt-5.5", reasoning_effort="ultra", permission_mode="full_access", messages=request_messages)  # 新增代码+GuiContextDirectSseAdapter：构造带完整 messages 的请求；如果没有这一行，测试无法锁定新请求字段契约。
    result = FakeStreamingGuiAgentAdapter(direct_sse_post_sse=fake_post_sse).run(request, lambda event: None, lambda: False)  # 新增代码+GuiContextDirectSseAdapter：执行 Direct SSE adapter；如果没有这一行，fake_post_sse 不会收到请求。
    assert result.status == "completed"  # 新增代码+GuiContextDirectSseAdapter：确认最小完成流不会报错；如果没有这一行，后续 body 断言可能掩盖运行失败。
    assert captured["body"]["input"] == request_messages  # 新增代码+GuiContextDirectSseAdapter：断言 adapter 原样使用 request.messages；如果没有这一行，latest-prompt-only 回归不会被发现。
    assert "只应作为 fallback 的 prompt" not in str(captured["body"]["input"])  # 新增代码+GuiContextDirectSseAdapter：确认 fallback prompt 没有污染完整上下文；如果没有这一行，adapter 可能把两套输入混在一起。
    # 新增代码+GuiContextDirectSseAdapter：函数段结束，request.messages 优先级契约到此结束。
