import json  # 新增代码+OsSecretStoreTest：读取 secrets.os.json 验证密文内容；如果没有这行，测试无法确认明文没有落盘。
import sys  # 新增代码+OsSecretStoreTest：判断当前平台是否支持 Windows DPAPI；如果没有这行，非 Windows 测试会误跑失败。
from pathlib import Path  # 新增代码+OsSecretStoreTest：用 Path 处理临时工作区路径；如果没有这行，路径拼接在 Windows 上容易出错。

import pytest  # 新增代码+OsSecretStoreTest：使用 pytest 的 tmp_path、monkeypatch 和 skip；如果没有这行，测试无法隔离环境。


def test_os_encrypted_secret_store_round_trips_without_plaintext(tmp_path: Path) -> None:  # 新增代码+OsSecretStoreTest：测试段开始，验证 OS 加密存储不写明文且可取回；如果没有这段，真实 OAuth token 安全落盘没有证据。
    if sys.platform != "win32":  # 新增代码+OsSecretStoreTest：只在 Windows 跑 DPAPI 测试；如果没有这行，非 Windows CI 会因缺 DPAPI 失败。
        pytest.skip("Windows DPAPI CurrentUser is required for OsEncryptedSecretStore.")  # 新增代码+OsSecretStoreTest：非 Windows 明确跳过；如果没有这行，失败原因会误导为代码逻辑问题。
    from learning_agent.app.gui_provider_secret_store import OsEncryptedSecretStore  # 新增代码+OsSecretStoreTest：导入待测 OS 加密 store；如果没有这行，测试没有被测目标。

    store = OsEncryptedSecretStore(tmp_path)  # 新增代码+OsSecretStoreTest：创建隔离的 OS 加密 store；如果没有这行，测试会污染真实 workspace。
    secret_ref = store.set_secret("provider:openai:access_token", "unit-test-os-secret-value")  # 新增代码+OsSecretStoreTest：写入测试 token；如果没有这行，无法验证加密、取回和删除。
    secret_file = tmp_path / "memory" / "gui_provider_settings" / "secrets.os.json"  # 新增代码+OsSecretStoreTest：定位密文文件；如果没有这行，测试无法检查落盘内容。
    secret_text = secret_file.read_text(encoding="utf-8")  # 新增代码+OsSecretStoreTest：读取密文 JSON 文本；如果没有这行，无法断言明文缺席。
    parsed = json.loads(secret_text)  # 新增代码+OsSecretStoreTest：解析密文 JSON；如果没有这行，无法确认结构包含 ciphertext。

    assert secret_ref == "provider:openai:access_token"  # 新增代码+OsSecretStoreTest：确认引用保持稳定；如果没有这行，主配置无法长期指向同一 token。
    assert "unit-test-os-secret-value" not in secret_text  # 新增代码+OsSecretStoreTest：确认密文文件不含 token 明文；如果没有这行，安全目标可能退化。
    assert "ciphertext" in parsed[secret_ref]  # 新增代码+OsSecretStoreTest：确认文件只保存密文字段；如果没有这行，结构漂移会漏过。
    assert store.get_secret(secret_ref) == "unit-test-os-secret-value"  # 新增代码+OsSecretStoreTest：确认后端内部可以解密取回；如果没有这行，真实 SSE 请求无法拿 token。
    assert "unit-test-os-secret-value" not in store.mask_secret(secret_ref)  # 新增代码+OsSecretStoreTest：确认展示掩码不含完整明文；如果没有这行，UI 可能泄露 token。

    store.delete_secret(secret_ref)  # 新增代码+OsSecretStoreTest：删除测试 token；如果没有这行，无法验证断开连接清理密文。
    assert store.get_secret(secret_ref) == ""  # 新增代码+OsSecretStoreTest：确认删除后无法取回；如果没有这行，disconnect 可能留下旧 token。
# 新增代码+OsSecretStoreTest：测试段结束，OS 加密生命周期合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


def test_make_provider_secret_store_selects_kind_and_rejects_real_oauth_dev_json(tmp_path: Path) -> None:  # 新增代码+SecretStoreFactoryTest：测试段开始，验证 secret store factory 门禁；如果没有这段，真实 OAuth 可能误用 dev_json。
    from learning_agent.app.gui_provider_secret_store import DevJsonSecretStore, GuiProviderSecretStoreError, OsEncryptedSecretStore, make_provider_secret_store  # 新增代码+SecretStoreFactoryTest：导入 factory 和实现类；如果没有这行，测试无法断言具体类型和错误。

    dev_store = make_provider_secret_store(tmp_path, {"OPENHARNESS_PROVIDER_SECRET_STORE": "dev_json", "OPENHARNESS_OPENAI_AUTH_MODE": "mock"})  # 新增代码+SecretStoreFactoryTest：创建开发 JSON store；如果没有这行，无法证明默认开发路径仍可用。
    os_store = make_provider_secret_store(tmp_path, {"OPENHARNESS_PROVIDER_SECRET_STORE": "os_encrypted", "OPENHARNESS_OPENAI_AUTH_MODE": "mock"})  # 新增代码+SecretStoreFactoryTest：创建 OS 加密 store；如果没有这行，无法证明显式 os_encrypted 生效。

    assert isinstance(dev_store, DevJsonSecretStore)  # 新增代码+SecretStoreFactoryTest：确认 dev_json 返回开发 store；如果没有这行，V1 mock/API-key 路径可能被破坏。
    assert isinstance(os_store, OsEncryptedSecretStore)  # 新增代码+SecretStoreFactoryTest：确认 os_encrypted 返回 OS store；如果没有这行，真实 OAuth 没有安全存储入口。
    with pytest.raises(GuiProviderSecretStoreError) as error_info:  # 新增代码+SecretStoreFactoryTest：捕获真实 OAuth 使用 dev_json 的预期错误；如果没有这行，门禁失败会中断测试。
        make_provider_secret_store(tmp_path, {"OPENHARNESS_PROVIDER_SECRET_STORE": "dev_json", "OPENHARNESS_OPENAI_AUTH_MODE": "real_browser"})  # 新增代码+SecretStoreFactoryTest：模拟真实浏览器 OAuth 却使用 dev_json；如果没有这行，安全门禁没有触发输入。
    assert error_info.value.code == "os_encrypted_secret_store_required"  # 新增代码+SecretStoreFactoryTest：确认错误码稳定；如果没有这行，前端或日志无法精确解释缺失条件。
# 新增代码+SecretStoreFactoryTest：测试段结束，factory 门禁合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。
