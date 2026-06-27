import json  # 新增代码+DirectOAuthTokenStoreTest：用于把 info payload 序列化后扫描敏感字段；如果没有这行代码，嵌套泄露不容易被测试发现。
import tempfile  # 新增代码+DirectOAuthTokenStoreTest：用于创建隔离的临时配置目录；如果没有这行代码，测试会污染用户真实 token 目录。
import unittest  # 新增代码+DirectOAuthTokenStoreTest：沿用项目现有 unittest 风格；如果没有这行代码，测试类不会被标准 runner 发现。
from pathlib import Path  # 新增代码+DirectOAuthTokenStoreTest：用于表达 Windows 友好的路径对象；如果没有这行代码，测试只能用脆弱字符串拼路径。


def _sample_tokens() -> dict[str, object]:  # 新增代码+DirectOAuthTokenStoreTest：函数段开始，生成一份只用于测试的 OAuth token 记录；如果没有这段，多个测试会重复手写敏感样本。
    return {  # 新增代码+DirectOAuthTokenStoreTest：返回测试 token 字典；如果没有这行代码，调用方拿不到统一样本。
        "access_token": "access-token-for-test",  # 新增代码+DirectOAuthTokenStoreTest：放入短期 token 样本；如果没有这行代码，泄露扫描无法覆盖 access token。
        "refresh_token": "refresh-token-for-test",  # 新增代码+DirectOAuthTokenStoreTest：放入长期 token 样本；如果没有这行代码，泄露扫描无法覆盖 refresh token。
        "id_token": "id-token-for-test",  # 新增代码+DirectOAuthTokenStoreTest：放入身份 token 样本；如果没有这行代码，泄露扫描无法覆盖 id token。
        "expires_at": 1782500000000,  # 新增代码+DirectOAuthTokenStoreTest：放入毫秒级过期时间；如果没有这行代码，info 无法展示非敏感过期摘要。
        "account_id": "acct_test_123",  # 新增代码+DirectOAuthTokenStoreTest：放入账号摘要；如果没有这行代码，ChatGPT-Account-Id 相关路径无法被后续复用。
    }  # 新增代码+DirectOAuthTokenStoreTest：测试 token 字典结束；如果没有这行代码，Python 语法不完整。
# 新增代码+DirectOAuthTokenStoreTest：函数段结束，_sample_tokens 到此结束；如果没有边界说明，用户不容易看出这里不是真实凭据。


class GuiProviderOAuthTokenStoreTests(unittest.TestCase):  # 新增代码+DirectOAuthTokenStoreTest：测试类段开始，锁定 direct OAuth token store 的安全边界；如果没有这个类，V1C 可能绕过安全存储先写 token。
    def test_token_store_writes_outside_workspace(self) -> None:  # 新增代码+DirectOAuthTokenStoreTest：测试段开始，确认 token 写到显式 profile 目录；如果没有这段，token 可能误写进项目 workspace。
        from learning_agent.app.gui_provider_oauth_token_store import make_fake_token_store  # 新增代码+DirectOAuthTokenStoreTest：导入测试用 fake store；如果没有这行代码，测试没有被测目标。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectOAuthTokenStoreTest：创建隔离目录；如果没有这行代码，测试会污染真实文件系统。
            config_dir = Path(directory) / "profile"  # 新增代码+DirectOAuthTokenStoreTest：定义模拟用户 profile 目录；如果没有这行代码，路径归属无法断言。
            store = make_fake_token_store(config_dir=config_dir)  # 新增代码+DirectOAuthTokenStoreTest：创建 fake token store；如果没有这行代码，后续无法写入 token。
            store.set_tokens(provider="openai", tokens=_sample_tokens())  # 新增代码+DirectOAuthTokenStoreTest：写入 OpenAI token 样本；如果没有这行代码，path_for 不会产生文件。

            token_path = store.path_for("openai")  # 新增代码+DirectOAuthTokenStoreTest：读取 provider token 文件路径；如果没有这行代码，断言只能猜测内部路径。

        self.assertTrue(str(token_path).startswith(str(config_dir)))  # 新增代码+DirectOAuthTokenStoreTest：确认 token 文件属于 profile 目录；如果没有这行代码，workspace 泄露风险会漏过。
    # 新增代码+DirectOAuthTokenStoreTest：测试段结束，写入位置合同到此结束；如果没有边界说明，用户不容易看出此测试只检查路径边界。

    def test_token_store_never_returns_raw_tokens_in_info(self) -> None:  # 新增代码+DirectOAuthTokenStoreTest：测试段开始，确认 info 永远不返回原始 token；如果没有这段，renderer 可能拿到敏感凭据。
        from learning_agent.app.gui_provider_oauth_token_store import make_fake_token_store  # 新增代码+DirectOAuthTokenStoreTest：导入测试用 fake store；如果没有这行代码，测试没有被测目标。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectOAuthTokenStoreTest：创建隔离目录；如果没有这行代码，测试会污染真实文件系统。
            store = make_fake_token_store(config_dir=Path(directory))  # 新增代码+DirectOAuthTokenStoreTest：创建 fake token store；如果没有这行代码，后续无法写入 token。
            store.set_tokens(provider="openai", tokens=_sample_tokens())  # 新增代码+DirectOAuthTokenStoreTest：写入 token 样本；如果没有这行代码，info 没有 connected 场景。
            info = store.info(provider="openai")  # 新增代码+DirectOAuthTokenStoreTest：读取脱敏摘要；如果没有这行代码，无法验证 renderer 可见 payload。

        serialized = json.dumps(info, ensure_ascii=False)  # 新增代码+DirectOAuthTokenStoreTest：序列化摘要做敏感词扫描；如果没有这行代码，嵌套字段可能漏过。
        self.assertTrue(info["connected"])  # 新增代码+DirectOAuthTokenStoreTest：确认写入后摘要显示 connected；如果没有这行代码，catalog 无法判断真实连接。
        self.assertEqual(info["provider_id"], "openai")  # 新增代码+DirectOAuthTokenStoreTest：确认摘要保留 provider id；如果没有这行代码，调用方无法归属 token 引用。
        self.assertIn("token_ref", info)  # 新增代码+DirectOAuthTokenStoreTest：确认摘要只暴露引用而非原文；如果没有这行代码，后续 provider catalog 没有安全 source。
        self.assertNotIn("access_token", serialized)  # 新增代码+DirectOAuthTokenStoreTest：确认摘要不含 access_token 字段名；如果没有这行代码，短期凭据字段可能进入前端。
        self.assertNotIn("refresh_token", serialized)  # 新增代码+DirectOAuthTokenStoreTest：确认摘要不含 refresh_token 字段名；如果没有这行代码，长期凭据字段可能进入前端。
        self.assertNotIn("id_token", serialized)  # 新增代码+DirectOAuthTokenStoreTest：确认摘要不含 id_token 字段名；如果没有这行代码，身份凭据字段可能进入前端。
        self.assertNotIn("access-token-for-test", serialized)  # 新增代码+DirectOAuthTokenStoreTest：确认摘要不含 access token 值；如果没有这行代码，字段改名泄露会漏过。
        self.assertNotIn("refresh-token-for-test", serialized)  # 新增代码+DirectOAuthTokenStoreTest：确认摘要不含 refresh token 值；如果没有这行代码，长期凭据值泄露会漏过。
    # 新增代码+DirectOAuthTokenStoreTest：测试段结束，脱敏摘要合同到此结束；如果没有边界说明，用户不容易看出 info 是 renderer 安全入口。

    def test_token_store_delete_removes_login(self) -> None:  # 新增代码+DirectOAuthTokenStoreTest：测试段开始，确认删除 token 会断开连接；如果没有这段，用户退出登录后 catalog 可能仍显示连接。
        from learning_agent.app.gui_provider_oauth_token_store import make_fake_token_store  # 新增代码+DirectOAuthTokenStoreTest：导入测试用 fake store；如果没有这行代码，测试没有被测目标。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectOAuthTokenStoreTest：创建隔离目录；如果没有这行代码，测试会污染真实文件系统。
            store = make_fake_token_store(config_dir=Path(directory))  # 新增代码+DirectOAuthTokenStoreTest：创建 fake token store；如果没有这行代码，后续无法写入和删除 token。
            store.set_tokens(provider="openai", tokens=_sample_tokens())  # 新增代码+DirectOAuthTokenStoreTest：先写入 token；如果没有这行代码，delete 没有已登录状态可清理。
            store.delete_tokens(provider="openai")  # 新增代码+DirectOAuthTokenStoreTest：删除 OpenAI token；如果没有这行代码，断开连接行为不会发生。
            info = store.info(provider="openai")  # 新增代码+DirectOAuthTokenStoreTest：读取删除后的摘要；如果没有这行代码，无法确认 catalog 状态。

        self.assertFalse(info["connected"])  # 新增代码+DirectOAuthTokenStoreTest：确认删除后 disconnected；如果没有这行代码，用户可能误以为仍能真实请求模型。
    # 新增代码+DirectOAuthTokenStoreTest：测试段结束，删除登录合同到此结束；如果没有边界说明，用户不容易看出 delete 影响 catalog。

    def test_corrupt_token_record_is_reported_as_missing(self) -> None:  # 新增代码+DirectOAuthTokenStoreTest：测试段开始，确认坏 token 文件不会让 GUI 崩溃；如果没有这段，磁盘损坏会导致设置页失败。
        from learning_agent.app.gui_provider_oauth_token_store import make_fake_token_store  # 新增代码+DirectOAuthTokenStoreTest：导入测试用 fake store；如果没有这行代码，测试没有被测目标。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DirectOAuthTokenStoreTest：创建隔离目录；如果没有这行代码，测试会污染真实文件系统。
            store = make_fake_token_store(config_dir=Path(directory))  # 新增代码+DirectOAuthTokenStoreTest：创建 fake token store；如果没有这行代码，后续无法写坏文件。
            store.write_raw(provider="openai", raw=b"not-json")  # 新增代码+DirectOAuthTokenStoreTest：写入损坏记录；如果没有这行代码，坏文件恢复路径无法覆盖。
            info = store.info(provider="openai")  # 新增代码+DirectOAuthTokenStoreTest：读取坏文件摘要；如果没有这行代码，无法确认安全降级。

        self.assertFalse(info["connected"])  # 新增代码+DirectOAuthTokenStoreTest：确认坏文件按未登录处理；如果没有这行代码，GUI 可能误报 connected。
        self.assertEqual(info["status"], "missing")  # 新增代码+DirectOAuthTokenStoreTest：确认状态为 missing；如果没有这行代码，调用方无法区分未登录和真实错误。
    # 新增代码+DirectOAuthTokenStoreTest：测试段结束，损坏记录合同到此结束；如果没有边界说明，用户不容易看出坏文件不会抛给 UI。


if __name__ == "__main__":  # 新增代码+DirectOAuthTokenStoreTest：允许直接运行本测试文件；如果没有这行代码，手动调试需要记住 unittest 命令。
    unittest.main()  # 新增代码+DirectOAuthTokenStoreTest：启动 unittest runner；如果没有这行代码，直接 python 文件不会执行测试。
