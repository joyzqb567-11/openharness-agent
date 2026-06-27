import json  # 新增代码+OpenAIModelRegistryTest：读取模型注册表和 HTTP 响应；如果没有这行，测试无法检查安全 JSON。
import threading  # 新增代码+OpenAIModelRegistryTest：后台启动 GUI bridge；如果没有这行，HTTP endpoint 测试会阻塞。
import urllib.request  # 新增代码+OpenAIModelRegistryTest：请求本地 bridge 模型端点；如果没有这行，测试无法覆盖真实路由。
from pathlib import Path  # 新增代码+OpenAIModelRegistryTest：标注 tmp_path 类型；如果没有这行，路径语义不清楚。


def _openai_row(payload: dict[str, object], model_id: str) -> dict[str, object]:  # 新增代码+OpenAIModelRegistryTest：helper 段开始，从 payload 取指定模型行；如果没有这段，每个断言都要重复查找逻辑。
    rows = payload.get("models", []) if isinstance(payload.get("models", []), list) else []  # 新增代码+OpenAIModelRegistryTest：读取模型行列表；如果没有这行，坏 payload 会导致迭代异常。
    return next(row for row in rows if isinstance(row, dict) and row.get("id") == model_id)  # 新增代码+OpenAIModelRegistryTest：返回目标模型行；如果没有这行，测试无法断言状态。
# 新增代码+OpenAIModelRegistryTest：helper 段结束，_openai_row 到此结束；如果没有边界说明，初学者不易看出它只做查找。


def test_model_dropdown_uses_probed_models_when_available(tmp_path: Path) -> None:  # 新增代码+OpenAIModelRegistryTest：测试段开始，验证 probe 结果会覆盖静态模型状态；如果没有这段，模型下拉会只显示未知静态列表。
    from learning_agent.app.gui_provider_openai_models import build_openai_model_registry_payload, save_openai_model_probe_result  # 新增代码+OpenAIModelRegistryTest：导入模型注册表入口；如果没有这行，测试没有被测目标。
    from learning_agent.app.gui_provider_settings import build_provider_settings_payload  # 新增代码+OpenAIModelRegistryTest：导入 provider catalog；如果没有这行，无法验证设置页模型行。

    save_openai_model_probe_result(tmp_path, "gpt-5.4", "available", "probe ok")  # 新增代码+OpenAIModelRegistryTest：保存 gpt-5.4 可用探针结果；如果没有这行，模型状态不会从 unknown 变 available。
    registry_payload = build_openai_model_registry_payload(tmp_path)  # 新增代码+OpenAIModelRegistryTest：读取模型注册表 payload；如果没有这行，无法验证独立模型端点数据。
    provider_payload = build_provider_settings_payload(tmp_path)  # 新增代码+OpenAIModelRegistryTest：读取 provider settings payload；如果没有这行，无法验证设置页也使用注册表。
    provider_openai = next(provider for provider in provider_payload["providers"] if provider["id"] == "openai")  # 新增代码+OpenAIModelRegistryTest：取出 OpenAI provider；如果没有这行，无法检查 provider 模型行。
    registry_row = _openai_row(registry_payload, "gpt-5.4")  # 新增代码+OpenAIModelRegistryTest：取出注册表模型行；如果没有这行，状态断言没有对象。
    provider_row = next(row for row in provider_openai["models"] if row["id"] == "gpt-5.4")  # 新增代码+OpenAIModelRegistryTest：取出 provider catalog 模型行；如果没有这行，无法证明设置页消费注册表。

    assert registry_row["state"] == "available"  # 新增代码+OpenAIModelRegistryTest：确认注册表显示 available；如果没有这行，probe_available_models 不会生效。
    assert registry_row["source"] == "probe_available_models"  # 新增代码+OpenAIModelRegistryTest：确认来源是探针层；如果没有这行，诊断无法解释模型来源。
    assert provider_row["state"] == "available"  # 新增代码+OpenAIModelRegistryTest：确认 provider catalog 也显示 available；如果没有这行，设置页会和注册表不一致。
    assert provider_row["source"] == "probe_available_models"  # 新增代码+OpenAIModelRegistryTest：确认设置页模型来源是探针；如果没有这行，前端无法展示来源。
# 新增代码+OpenAIModelRegistryTest：测试段结束，probe available 合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


def test_unsupported_model_shows_visible_account_model_error(tmp_path: Path) -> None:  # 新增代码+OpenAIModelRegistryTest：测试段开始，验证不支持模型的可见错误；如果没有这段，用户只会看到慢或失败。
    from learning_agent.app.gui_provider_openai_models import build_openai_model_registry_payload, save_openai_model_probe_result  # 新增代码+OpenAIModelRegistryTest：导入模型注册表入口；如果没有这行，测试没有被测目标。

    save_openai_model_probe_result(tmp_path, "gpt-5.5", "not_supported_for_account", "The requested test model is not supported for this account.")  # 新增代码+OpenAIModelRegistryTest：保存账号不支持错误；如果没有这行，错误态没有来源。
    payload = build_openai_model_registry_payload(tmp_path)  # 新增代码+OpenAIModelRegistryTest：读取模型注册表 payload；如果没有这行，无法验证错误显示。
    row = _openai_row(payload, "gpt-5.5")  # 新增代码+OpenAIModelRegistryTest：取出 gpt-5.5 模型行；如果没有这行，状态断言没有对象。

    assert row["state"] == "not_supported_for_account"  # 新增代码+OpenAIModelRegistryTest：确认状态明确为账号不支持；如果没有这行，UI 可能误报普通网络失败。
    assert "not supported" in str(row["message"])  # 新增代码+OpenAIModelRegistryTest：确认错误消息可见且低敏；如果没有这行，用户不知道是账号/模型不匹配。
# 新增代码+OpenAIModelRegistryTest：测试段结束，unsupported 模型错误合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


def test_last_known_good_models_persist_without_token_or_email_values(tmp_path: Path) -> None:  # 新增代码+OpenAIModelRegistryTest：测试段开始，验证 last-known-good 安全持久化；如果没有这段，成功模型缓存可能混入敏感值。
    from learning_agent.app.gui_provider_openai_models import build_openai_model_registry_payload, openai_model_registry_file, record_openai_last_known_good_model  # 新增代码+OpenAIModelRegistryTest：导入 LKG 入口和文件路径；如果没有这行，测试没有被测目标。

    record_openai_last_known_good_model(tmp_path, "gpt-5.3-codex-spark")  # 新增代码+OpenAIModelRegistryTest：记录一个真实成功过的模型 id；如果没有这行，LKG 文件不会生成。
    registry_text = openai_model_registry_file(tmp_path).read_text(encoding="utf-8")  # 新增代码+OpenAIModelRegistryTest：读取缓存文件文本；如果没有这行，无法检查敏感值。
    payload = build_openai_model_registry_payload(tmp_path)  # 新增代码+OpenAIModelRegistryTest：读取模型注册表 payload；如果没有这行，无法验证 LKG 进入模型行。
    row = _openai_row(payload, "gpt-5.3-codex-spark")  # 新增代码+OpenAIModelRegistryTest：取出 LKG 模型行；如果没有这行，状态断言没有对象。

    assert "access_token" not in registry_text  # 新增代码+OpenAIModelRegistryTest：确认缓存不含 token 字段；如果没有这行，模型缓存可能泄露凭据语义。
    assert "refresh_token" not in registry_text  # 新增代码+OpenAIModelRegistryTest：确认缓存不含 refresh token 字段；如果没有这行，长期凭据语义可能泄露。
    assert "@" not in registry_text  # 新增代码+OpenAIModelRegistryTest：确认缓存不含邮箱样式账号；如果没有这行，账号隐私可能进入模型缓存。
    assert row["state"] == "available"  # 新增代码+OpenAIModelRegistryTest：确认 LKG 模型显示 available；如果没有这行，成功缓存无法帮助模型菜单。
    assert row["source"] == "last_known_good_models"  # 新增代码+OpenAIModelRegistryTest：确认来源是 last-known-good；如果没有这行，诊断无法解释模型为何保留。
# 新增代码+OpenAIModelRegistryTest：测试段结束，LKG 安全持久化合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


def test_openai_model_registry_bridge_endpoint_respects_visibility(tmp_path: Path) -> None:  # 新增代码+OpenAIModelRegistryTest：测试段开始，验证 bridge 模型端点和可见性；如果没有这段，前端无法独立刷新模型状态。
    from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+OpenAIModelRegistryTest：导入 GUI bridge 工厂；如果没有这行，测试无法覆盖真实 HTTP 路由。
    from learning_agent.app.gui_provider_openai_models import save_openai_model_probe_result  # 新增代码+OpenAIModelRegistryTest：导入探针保存入口；如果没有这行，端点没有 probe 数据。
    from learning_agent.app.gui_provider_settings import save_provider_settings  # 新增代码+OpenAIModelRegistryTest：导入 settings 保存 helper；如果没有这行，无法设置模型可见性。

    save_openai_model_probe_result(tmp_path, "gpt-5.4", "available", "probe ok")  # 新增代码+OpenAIModelRegistryTest：保存可用模型探针；如果没有这行，端点返回的状态仍是 unknown。
    save_provider_settings(tmp_path, {"auth": {}, "custom_providers": {}, "model_visibility": {"openai:gpt-5.4": False}, "default_provider_id": "", "default_model_id": ""})  # 新增代码+OpenAIModelRegistryTest：隐藏 gpt-5.4；如果没有这行，端点无法证明尊重可见性。
    server = create_gui_bridge_server(workspace=tmp_path, host="127.0.0.1", port=0, token="test-token")  # 新增代码+OpenAIModelRegistryTest：启动随机端口 bridge；如果没有这行，HTTP 路由没有服务。
    thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+OpenAIModelRegistryTest：创建后台线程；如果没有这行，请求会阻塞在 serve_forever。
    thread.start()  # 新增代码+OpenAIModelRegistryTest：启动 bridge；如果没有这行，urllib 会连接失败。
    try:  # 新增代码+OpenAIModelRegistryTest：确保 server 最终关闭；如果没有这行，失败时端口会泄漏。
        host, port = server.server_address  # 新增代码+OpenAIModelRegistryTest：读取真实监听地址；如果没有这行，端口 0 场景无法请求。
        request = urllib.request.Request(f"http://{host}:{port}/v2/gui/provider-settings/openai-models", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+OpenAIModelRegistryTest：构造带 token 的模型请求；如果没有这行，安全门禁会返回 401。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+OpenAIModelRegistryTest：发送模型端点请求；如果没有这行，无法验证 bridge 路由。
            payload = json.loads(response.read().decode("utf-8"))  # 新增代码+OpenAIModelRegistryTest：解析响应 JSON；如果没有这行，断言无法读取模型行。
    finally:  # 新增代码+OpenAIModelRegistryTest：清理 server；如果没有这行，后台线程和 socket 可能残留。
        server.shutdown()  # 新增代码+OpenAIModelRegistryTest：停止 serve_forever；如果没有这行，测试进程可能挂住。
        server.server_close()  # 新增代码+OpenAIModelRegistryTest：释放 socket；如果没有这行，Windows 端口可能短时间占用。
        thread.join(timeout=5)  # 新增代码+OpenAIModelRegistryTest：等待线程退出；如果没有这行，测试结束时可能仍有线程。
    row = _openai_row(payload, "gpt-5.4")  # 新增代码+OpenAIModelRegistryTest：读取端点返回的 gpt-5.4 行；如果没有这行，无法检查可见性。

    assert payload["ok"] is True  # 新增代码+OpenAIModelRegistryTest：确认端点成功；如果没有这行，前端可能收到错误 payload。
    assert row["state"] == "available"  # 新增代码+OpenAIModelRegistryTest：确认端点携带 probe 状态；如果没有这行，前端模型菜单无法显示可用状态。
    assert row["visible"] is False  # 新增代码+OpenAIModelRegistryTest：确认端点尊重模型隐藏；如果没有这行，隐藏模型会重新出现在下拉。
# 新增代码+OpenAIModelRegistryTest：测试段结束，bridge 模型端点合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。
