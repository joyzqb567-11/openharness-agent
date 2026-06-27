from pathlib import Path  # 新增代码+OpenAIDisconnectTest：用 Path 标注临时 workspace 类型；如果没有这行，测试路径意图不清楚。


def test_disconnect_provider_deletes_oauth_secret_refs_and_openai_selection(tmp_path: Path, monkeypatch) -> None:  # 新增代码+OpenAIDisconnectTest：测试段开始，验证断开 OpenAI 会删 token 组和模型选择；如果没有这段，连接后无法断开的 bug 会回归。
    monkeypatch.setenv("OPENHARNESS_PROVIDER_SECRET_STORE", "dev_json")  # 新增代码+OpenAIDisconnectTest：强制使用开发 store 便于检查删除效果；如果没有这行，外部真实 env 会影响测试。
    monkeypatch.setenv("OPENHARNESS_OPENAI_AUTH_MODE", "mock")  # 新增代码+OpenAIDisconnectTest：强制非真实 OAuth 模式；如果没有这行，factory 可能因本机 env 进入真实门禁。
    from learning_agent.app.gui_provider_secret_store import make_provider_secret_store, safe_secret_ref  # 新增代码+OpenAIDisconnectTest：导入 store factory 和引用 helper；如果没有这行，测试无法写入待删 token。
    from learning_agent.app.gui_provider_settings import disconnect_provider, load_provider_settings, save_provider_settings  # 新增代码+OpenAIDisconnectTest：导入 provider 设置 mutation；如果没有这行，测试没有断开入口。

    store = make_provider_secret_store(tmp_path)  # 新增代码+OpenAIDisconnectTest：创建隔离 secret store；如果没有这行，token fixtures 无处保存。
    access_ref = store.set_secret(safe_secret_ref("openai", "access_token"), "test_access_token_for_disconnect")  # 新增代码+OpenAIDisconnectTest：写入 fake access token；如果没有这行，无法证明 access_token 会被删除。
    refresh_ref = store.set_secret(safe_secret_ref("openai", "refresh_token"), "test_refresh_token_for_disconnect")  # 新增代码+OpenAIDisconnectTest：写入 fake refresh token；如果没有这行，无法证明 refresh_token 会被删除。
    id_ref = store.set_secret(safe_secret_ref("openai", "id_token"), "test_id_token_for_disconnect")  # 新增代码+OpenAIDisconnectTest：写入 fake id token；如果没有这行，无法证明 id_token 会被删除。
    save_provider_settings(tmp_path, {"auth": {"openai": {"type": "oauth", "secret_refs": {"access_token": access_ref, "refresh_token": refresh_ref, "id_token": id_ref}, "updated_at": 1.0}}, "custom_providers": {}, "model_visibility": {}, "default_provider_id": "openai", "default_model_id": "gpt-5.5", "selected_openai_account_id": "acct_test_001", "selected_openai_account_label": "jo***@example.test", "selected_openai_model_id": "gpt-5.5"})  # 新增代码+OpenAIDisconnectTest：保存带 OAuth token 组和 OpenAI 选择的配置；如果没有这行，disconnect 没有真实对象可清。

    payload = disconnect_provider(tmp_path, "openai")  # 新增代码+OpenAIDisconnectTest：执行 OpenAI 断开；如果没有这行，无法验证真实 mutation 结果。
    saved = load_provider_settings(tmp_path)  # 新增代码+OpenAIDisconnectTest：重新读取落盘设置；如果没有这行，只能看到内存返回值。
    openai = next(provider for provider in payload["providers"] if provider["id"] == "openai")  # 新增代码+OpenAIDisconnectTest：读取返回 catalog 中的 OpenAI 行；如果没有这行，无法验证 UI 会刷新为未连接。

    assert store.get_secret(access_ref) == ""  # 新增代码+OpenAIDisconnectTest：确认 access token 已删除；如果没有这行，真实请求仍可能拿旧 token。
    assert store.get_secret(refresh_ref) == ""  # 新增代码+OpenAIDisconnectTest：确认 refresh token 已删除；如果没有这行，断开后仍可能自动续期。
    assert store.get_secret(id_ref) == ""  # 新增代码+OpenAIDisconnectTest：确认 id token 已删除；如果没有这行，账号身份残留风险会漏掉。
    assert "openai" not in saved["auth"]  # 新增代码+OpenAIDisconnectTest：确认 auth 记录已移除；如果没有这行，catalog 可能继续显示已连接。
    assert saved["selected_openai_account_id"] == ""  # 新增代码+OpenAIDisconnectTest：确认账号 id 已清空；如果没有这行，重连前可能误用旧账号。
    assert saved["selected_openai_account_label"] == ""  # 新增代码+OpenAIDisconnectTest：确认账号标签已清空；如果没有这行，UI 会误显示旧账号。
    assert saved["selected_openai_model_id"] == ""  # 新增代码+OpenAIDisconnectTest：确认 OpenAI 模型选择已清空；如果没有这行，底部模型菜单会误用断开前模型。
    assert saved["default_provider_id"] == ""  # 新增代码+OpenAIDisconnectTest：确认默认 provider 已清空；如果没有这行，断开后 composer 仍可能默认 OpenAI。
    assert saved["default_model_id"] == ""  # 新增代码+OpenAIDisconnectTest：确认默认模型已清空；如果没有这行，真实调用路由可能继续带旧 gpt 模型。
    assert openai["connected"] is False  # 新增代码+OpenAIDisconnectTest：确认返回给前端的 OpenAI 状态为未连接；如果没有这行，断开按钮视觉状态会错误。
# 新增代码+OpenAIDisconnectTest：测试段结束，OpenAI OAuth 断开合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。
