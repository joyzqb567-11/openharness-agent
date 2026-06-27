import json  # 新增代码+OpenAIProviderStateTest：序列化 runtime state 做泄漏扫描；如果没有这行，嵌套字段检查不方便。
from pathlib import Path  # 新增代码+OpenAIProviderStateTest：标注 tmp_path 类型；如果没有这行，路径语义不清楚。


def test_openai_runtime_state_serializes_without_token_values(tmp_path: Path) -> None:  # 新增代码+OpenAIProviderStateTest：测试段开始，验证 runtime state 不含 token 或 secret_ref；如果没有这段，诊断面板可能泄露敏感信息。
    from learning_agent.app.gui_provider_openai_state import build_openai_provider_runtime_state, serialize_openai_provider_runtime_state  # 新增代码+OpenAIProviderStateTest：导入 runtime state 入口；如果没有这行，测试没有被测目标。
    from learning_agent.app.gui_provider_settings import save_provider_settings  # 新增代码+OpenAIProviderStateTest：导入 settings 保存 helper；如果没有这行，测试无法准备连接状态。

    save_provider_settings(tmp_path, {"auth": {"openai": {"type": "oauth_real", "secret_refs": {"access_token": "provider:openai:access_token", "refresh_token": "provider:openai:refresh_token"}, "account_id": "acct_test_001", "account_label": "Test Account", "account_selection_status": "selected", "oauth_client_source": "operator_configured", "updated_at": 1.0}}, "custom_providers": {}, "model_visibility": {"openai:gpt-5.4-mini": False}, "default_provider_id": "openai", "default_model_id": "gpt-5.5", "selected_openai_account_id": "acct_test_001", "selected_openai_account_label": "Test Account", "selected_openai_model_id": "gpt-5.5"})  # 新增代码+OpenAIProviderStateTest：写入只含引用和安全摘要的 OpenAI 连接；如果没有这行，runtime state 没有数据来源。
    state = build_openai_provider_runtime_state(tmp_path)  # 新增代码+OpenAIProviderStateTest：构造 runtime state；如果没有这行，无法验证字段映射。
    payload = serialize_openai_provider_runtime_state(state)  # 新增代码+OpenAIProviderStateTest：序列化状态；如果没有这行，无法检查最终 JSON 形状。
    serialized = json.dumps(payload, ensure_ascii=False)  # 新增代码+OpenAIProviderStateTest：把 payload 转成文本；如果没有这行，字符串泄漏检查不方便。

    assert payload["provider_id"] == "openai"  # 新增代码+OpenAIProviderStateTest：确认 provider id 正确；如果没有这行，状态可能属于错误 provider。
    assert payload["auth_type"] == "oauth_real"  # 新增代码+OpenAIProviderStateTest：确认真实 OAuth 类型保留；如果没有这行，UI 无法区分连接方式。
    assert payload["runtime"] == "direct_sse"  # 新增代码+OpenAIProviderStateTest：确认目标 runtime 是 direct_sse；如果没有这行，诊断无法证明不走 WebSocket。
    assert payload["direct_route_status"] == "not_probed"  # 新增代码+OpenAIProviderStateTest：确认连接后未探针状态；如果没有这行，状态可能误报 healthy。
    assert payload["account_id"] == "acct_test_001"  # 新增代码+OpenAIProviderStateTest：确认安全账号 id 透传；如果没有这行，多账号状态无法显示。
    assert payload["selected_model_id"] == "gpt-5.5"  # 新增代码+OpenAIProviderStateTest：确认模型选择透传；如果没有这行，composer 路由目标不明确。
    assert "gpt-5.4-mini" not in payload["available_models"]  # 新增代码+OpenAIProviderStateTest：确认隐藏模型不会出现在可用列表；如果没有这行，模型可见性失效。
    assert payload["oauth_client_source"] == "operator_configured"  # 新增代码+OpenAIProviderStateTest：确认 client source 透传；如果没有这行，诊断无法说明来源。
    assert "access_token" not in serialized  # 新增代码+OpenAIProviderStateTest：确认序列化状态不含 token 字段名；如果没有这行，诊断可能暴露 token 语义。
    assert "refresh_token" not in serialized  # 新增代码+OpenAIProviderStateTest：确认序列化状态不含 refresh token 字段名；如果没有这行，长期凭据语义可能泄露。
    assert "secret_ref" not in serialized  # 新增代码+OpenAIProviderStateTest：确认序列化状态不含 secret_ref；如果没有这行，renderer 可能拿到后端密钥定位。
# 新增代码+OpenAIProviderStateTest：测试段结束，runtime state 安全序列化合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


def test_openai_runtime_state_surfaces_account_selection_required(tmp_path: Path) -> None:  # 新增代码+OpenAIProviderStateTest：测试段开始，验证账号选择需求状态；如果没有这段，多账号失败会被误报普通未探针。
    from learning_agent.app.gui_provider_openai_state import build_openai_provider_runtime_state, serialize_openai_provider_runtime_state  # 新增代码+OpenAIProviderStateTest：导入 runtime state 入口；如果没有这行，测试没有被测目标。
    from learning_agent.app.gui_provider_settings import save_provider_settings  # 新增代码+OpenAIProviderStateTest：导入 settings 保存 helper；如果没有这行，测试无法准备账号选择状态。

    save_provider_settings(tmp_path, {"auth": {"openai": {"type": "oauth_real", "secret_refs": {"access_token": "provider:openai:access_token"}, "account_selection_status": "account_selection_required", "oauth_client_source": "operator_configured", "updated_at": 1.0}}, "custom_providers": {}, "model_visibility": {}, "default_provider_id": "openai", "default_model_id": "", "selected_openai_account_id": "", "selected_openai_account_label": "", "selected_openai_model_id": ""})  # 新增代码+OpenAIProviderStateTest：写入账号选择阻断状态；如果没有这行，runtime state 没有 account_selection_required 来源。
    payload = serialize_openai_provider_runtime_state(build_openai_provider_runtime_state(tmp_path))  # 新增代码+OpenAIProviderStateTest：构造并序列化状态；如果没有这行，无法验证最终字段。

    assert payload["direct_route_status"] == "account_selection_required"  # 新增代码+OpenAIProviderStateTest：确认账号选择需求被显式暴露；如果没有这行，UI 无法提示用户选择账号。
    assert payload["needs_reconnect"] is False  # 新增代码+OpenAIProviderStateTest：确认这是账号选择问题不是未连接；如果没有这行，UI 可能误导用户重新登录。
# 新增代码+OpenAIProviderStateTest：测试段结束，账号选择状态合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。
