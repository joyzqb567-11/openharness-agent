import tempfile  # 新增代码+ProviderSecretStoreTest：创建隔离临时工作区；如果没有这行代码，密钥测试会污染真实项目目录。
import unittest  # 新增代码+ProviderSecretStoreTest：使用项目现有 unittest 风格；如果没有这行代码，测试类不会被标准 runner 发现。
from pathlib import Path  # 新增代码+ProviderSecretStoreTest：用 Path 管理 Windows/临时目录路径；如果没有这行代码，路径拼接容易出错。


class GuiProviderSecretStoreTests(unittest.TestCase):  # 新增代码+ProviderSecretStoreTest：测试类段开始，锁定 GUI Provider 密钥存储合同；如果没有这个类，secret store 退化不会被发现。
    def test_dev_json_secret_store_sets_masks_gets_and_deletes_secret(self) -> None:  # 新增代码+ProviderSecretStoreTest：测试段开始，验证开发密钥存储的完整生命周期；如果没有这段测试，raw key 可能被误放进主配置。
        from learning_agent.app.gui_provider_secret_store import DevJsonSecretStore  # 新增代码+ProviderSecretStoreTest：导入待实现的 dev store；如果没有这行代码，测试没有被测目标。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+ProviderSecretStoreTest：创建临时 workspace；如果没有这行代码，测试会依赖真实工作区。
            store = DevJsonSecretStore(Path(directory))  # 新增代码+ProviderSecretStoreTest：创建隔离 store；如果没有这行代码，后续无法写入密钥。
            secret_ref = store.set_secret("provider:openai:api_key", "unit-test-secret-value")  # 新增代码+ProviderSecretStoreTest：写入测试密钥并获取引用；如果没有这行代码，无法验证 secret_ref 合同。
            secret_path = Path(directory) / "memory" / "gui_provider_settings" / "secrets.dev.json"  # 新增代码+ProviderSecretStoreTest：定位开发密钥文件；如果没有这行代码，无法确认落盘位置。
            masked_secret = store.mask_secret(secret_ref)  # 新增代码+ProviderSecretStoreTest：读取脱敏显示值；如果没有这行代码，无法证明 UI 只显示掩码。

            self.assertEqual(secret_ref, "provider:openai:api_key")  # 新增代码+ProviderSecretStoreTest：确认引用稳定；如果没有这行代码，主配置无法长期引用同一个 secret。
            self.assertEqual(store.get_secret(secret_ref), "unit-test-secret-value")  # 新增代码+ProviderSecretStoreTest：确认后端内部能取回密钥；如果没有这行代码，连接探针无法使用密钥。
            self.assertTrue(secret_path.exists())  # 新增代码+ProviderSecretStoreTest：确认只写入开发密钥文件；如果没有这行代码，落盘路径变化不会被发现。
            self.assertNotEqual(masked_secret, "unit-test-secret-value")  # 新增代码+ProviderSecretStoreTest：确认掩码不是原文；如果没有这行代码，UI 可能泄露 raw key。
            self.assertNotIn("unit-test-secret-value", masked_secret)  # 新增代码+ProviderSecretStoreTest：确认掩码不包含完整密钥；如果没有这行代码，长 key 可能被部分原样暴露。

            store.delete_secret(secret_ref)  # 新增代码+ProviderSecretStoreTest：删除测试密钥；如果没有这行代码，无法验证断开连接会清理 secret。
            self.assertEqual(store.get_secret(secret_ref), "")  # 新增代码+ProviderSecretStoreTest：确认删除后无法取回；如果没有这行代码，disconnect 可能留下旧密钥。
    # 新增代码+ProviderSecretStoreTest：测试段结束，密钥生命周期合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


if __name__ == "__main__":  # 新增代码+ProviderSecretStoreTest：允许直接运行本测试文件；如果没有这行代码，手动调试需要记住 unittest 命令。
    unittest.main()  # 新增代码+ProviderSecretStoreTest：启动 unittest runner；如果没有这行代码，直接 python 文件不会执行测试。
