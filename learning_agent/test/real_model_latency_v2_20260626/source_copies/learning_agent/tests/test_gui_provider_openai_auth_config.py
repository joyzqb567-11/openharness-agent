import unittest  # 新增代码+OpenAIAuthConfigTest：使用项目现有 unittest 风格；如果没有这行代码，测试类不会被标准 runner 发现。


class GuiProviderOpenAIAuthConfigTests(unittest.TestCase):  # 新增代码+OpenAIAuthConfigTest：测试类段开始，锁定 OpenAI OAuth 安全门禁；如果没有这个类，真实 OAuth 可能在不安全配置下误开启。
    def test_default_config_uses_mock_mode_and_blocks_real_oauth(self) -> None:  # 新增代码+OpenAIAuthConfigTest：测试段开始，验证默认配置只允许 mock；如果没有这段，开发环境可能误保存真实 OAuth token。
        from learning_agent.app.gui_provider_openai_auth_config import build_openai_auth_config  # 新增代码+OpenAIAuthConfigTest：导入待测配置 helper；如果没有这行代码，测试没有被测目标。

        config = build_openai_auth_config(env={})  # 新增代码+OpenAIAuthConfigTest：用空环境构造配置；如果没有这行代码，默认值不会被测试。

        self.assertEqual(config.auth_mode, "mock")  # 新增代码+OpenAIAuthConfigTest：确认默认是 mock；如果没有这行代码，稳定 V1 可能默认走真实 OAuth。
        self.assertTrue(config.mock_enabled)  # 新增代码+OpenAIAuthConfigTest：确认 mock flow 可用于稳定 V1 视觉验收；如果没有这行代码，browser/headless UI 没有安全后端。
        self.assertFalse(config.real_oauth_enabled)  # 新增代码+OpenAIAuthConfigTest：确认默认不允许真实 OAuth；如果没有这行代码，refresh token 保存风险会漏过。
    # 新增代码+OpenAIAuthConfigTest：测试段结束，默认配置门禁到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_real_mode_requires_encrypted_store_experimental_flag_and_client_id(self) -> None:  # 新增代码+OpenAIAuthConfigTest：测试段开始，验证真实 OAuth 三重门禁；如果没有这段，缺任一条件也可能开启真实登录。
        from learning_agent.app.gui_provider_openai_auth_config import build_openai_auth_config  # 新增代码+OpenAIAuthConfigTest：导入待测配置 helper；如果没有这行代码，测试没有被测目标。

        blocked_config = build_openai_auth_config(env={"OPENHARNESS_OPENAI_AUTH_MODE": "real_headless", "OPENHARNESS_OPENAI_EXPERIMENTAL": "1", "OPENHARNESS_OPENAI_CLIENT_ID": "client-id", "OPENHARNESS_PROVIDER_SECRET_STORE": "dev_json"})  # 新增代码+OpenAIAuthConfigTest：构造缺加密存储的真实模式；如果没有这行代码，最危险的 dev_json 场景不会被覆盖。
        allowed_config = build_openai_auth_config(env={"OPENHARNESS_OPENAI_AUTH_MODE": "real_headless", "OPENHARNESS_OPENAI_EXPERIMENTAL": "1", "OPENHARNESS_OPENAI_CLIENT_ID": "client-id", "OPENHARNESS_PROVIDER_SECRET_STORE": "os_encrypted"})  # 新增代码+OpenAIAuthConfigTest：构造满足三重门禁的真实模式；如果没有这行代码，允许路径也无法验证。

        self.assertFalse(blocked_config.real_oauth_enabled)  # 新增代码+OpenAIAuthConfigTest：确认 dev_json 阻止真实 OAuth；如果没有这行代码，真实 token 可能落到开发 JSON。
        self.assertEqual(blocked_config.blocked_reason, "os_encrypted_secret_store_required")  # 新增代码+OpenAIAuthConfigTest：确认阻断原因稳定；如果没有这行代码，前端/日志无法解释为什么不能真实登录。
        self.assertTrue(allowed_config.real_oauth_enabled)  # 新增代码+OpenAIAuthConfigTest：确认三条件满足时允许真实 OAuth；如果没有这行代码，后续实验路径无法开启。
        self.assertEqual(allowed_config.client_id, "client-id")  # 新增代码+OpenAIAuthConfigTest：确认 client id 被配置保存；如果没有这行代码，真实 OAuth 请求无法构造。
    # 新增代码+OpenAIAuthConfigTest：测试段结束，真实模式三重门禁到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_assert_real_oauth_allowed_raises_structured_error_when_blocked(self) -> None:  # 新增代码+OpenAIAuthConfigTest：测试段开始，验证阻断时有结构化错误；如果没有这段，调用方只能处理模糊异常。
        from learning_agent.app.gui_provider_openai_auth_config import OpenAIAuthConfigError, assert_real_oauth_allowed, build_openai_auth_config  # 新增代码+OpenAIAuthConfigTest：导入错误和断言 helper；如果没有这行代码，结构化错误无法测试。

        config = build_openai_auth_config(env={"OPENHARNESS_OPENAI_AUTH_MODE": "real_browser"})  # 新增代码+OpenAIAuthConfigTest：构造缺全部安全条件的真实 browser 模式；如果没有这行代码，错误路径没有输入。

        with self.assertRaises(OpenAIAuthConfigError) as error_context:  # 新增代码+OpenAIAuthConfigTest：捕获预期结构化错误；如果没有这行代码，异常会直接中断测试。
            assert_real_oauth_allowed(config)  # 新增代码+OpenAIAuthConfigTest：执行真实 OAuth 许可断言；如果没有这行代码，错误 helper 没有被调用。
        self.assertEqual(error_context.exception.code, "openai_real_oauth_blocked")  # 新增代码+OpenAIAuthConfigTest：确认错误码稳定；如果没有这行代码，bridge 无法返回机器可读失败。
        self.assertIn("experimental", error_context.exception.message)  # 新增代码+OpenAIAuthConfigTest：确认错误说明包含缺失条件；如果没有这行代码，用户无法知道如何启用实验路径。
    # 新增代码+OpenAIAuthConfigTest：测试段结束，结构化错误门禁到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_direct_oauth_requires_experimental_flag_and_client_id(self) -> None:  # 新增代码+DirectOAuthConfigTest：测试段开始，确认 direct_oauth 必须显式实验开关；如果没有这段，真实 OAuth 可能被普通启动误开。
        from learning_agent.app.gui_provider_openai_auth_config import OpenAIAuthConfigError, build_openai_auth_config  # 新增代码+DirectOAuthConfigTest：导入待测配置和结构化错误；如果没有这行代码，测试没有被测目标。

        with self.assertRaises(OpenAIAuthConfigError) as error_context:  # 新增代码+DirectOAuthConfigTest：捕获预期门禁异常；如果没有这行代码，异常会直接中断测试。
            build_openai_auth_config(env={"OPENHARNESS_OPENAI_AUTH_MODE": "direct_oauth"})  # 新增代码+DirectOAuthConfigTest：只启用 direct_oauth 但不给实验开关；如果没有这行代码，缺实验开关路径不会被覆盖。
        self.assertIn("experimental", error_context.exception.message)  # 新增代码+DirectOAuthConfigTest：确认错误说明指向实验开关；如果没有这行代码，用户不知道该设置什么。
        self.assertEqual(error_context.exception.code, "openai_direct_oauth_blocked")  # 新增代码+DirectOAuthConfigTest：确认 direct OAuth 有独立错误码；如果没有这行代码，前端无法区分稳定 real 和实验 direct。
    # 新增代码+DirectOAuthConfigTest：测试段结束，实验开关门禁到此结束；如果没有边界说明，初学者不易看出 direct OAuth 默认关闭。

    def test_direct_oauth_does_not_default_to_opencode_client_id(self) -> None:  # 新增代码+DirectOAuthConfigTest：测试段开始，确认 OpenHarness 不默认借用 OpenCode client id；如果没有这段，项目可能依赖不属于自己的 OAuth client。
        from learning_agent.app.gui_provider_openai_auth_config import OpenAIAuthConfigError, build_openai_auth_config  # 新增代码+DirectOAuthConfigTest：导入待测配置和结构化错误；如果没有这行代码，测试没有被测目标。

        env = {"OPENHARNESS_OPENAI_AUTH_MODE": "direct_oauth", "OPENHARNESS_OPENAI_EXPERIMENTAL": "1", "OPENHARNESS_PROVIDER_SECRET_STORE": "os_encrypted"}  # 新增代码+DirectOAuthConfigTest：构造只缺 client id 的 direct OAuth 环境；如果没有这行代码，client id 缺失路径无法测试。
        with self.assertRaises(OpenAIAuthConfigError) as error_context:  # 新增代码+DirectOAuthConfigTest：捕获预期门禁异常；如果没有这行代码，异常会直接中断测试。
            build_openai_auth_config(env=env)  # 新增代码+DirectOAuthConfigTest：执行配置构建；如果没有这行代码，缺 client id 不会被验证。
        self.assertIn("client_id", error_context.exception.message)  # 新增代码+DirectOAuthConfigTest：确认错误说明指向 client id；如果没有这行代码，用户不知道不能默认借用 OpenCode。
        self.assertNotIn("app_EMoamEEZ73f0CkXaXp7hrann", error_context.exception.message)  # 新增代码+DirectOAuthConfigTest：确认错误里不暗示 OpenCode client id；如果没有这行代码，后续可能把研究值当默认值。
    # 新增代码+DirectOAuthConfigTest：测试段结束，client id 门禁到此结束；如果没有边界说明，初学者不易看出 client id 必须显式提供。

    def test_direct_oauth_requires_os_encrypted_store(self) -> None:  # 新增代码+DirectOAuthConfigTest：测试段开始，确认 direct OAuth 只允许 OS 加密存储；如果没有这段，refresh token 可能落到 dev_json。
        from learning_agent.app.gui_provider_openai_auth_config import OpenAIAuthConfigError, build_openai_auth_config  # 新增代码+DirectOAuthConfigTest：导入待测配置和结构化错误；如果没有这行代码，测试没有被测目标。

        env = {"OPENHARNESS_OPENAI_AUTH_MODE": "direct_oauth", "OPENHARNESS_OPENAI_EXPERIMENTAL": "1", "OPENHARNESS_OPENAI_CLIENT_ID": "openharness-local-test", "OPENHARNESS_PROVIDER_SECRET_STORE": "plain_file"}  # 新增代码+DirectOAuthConfigTest：构造只缺 OS 加密的环境；如果没有这行代码，不安全存储路径无法测试。
        with self.assertRaises(OpenAIAuthConfigError) as error_context:  # 新增代码+DirectOAuthConfigTest：捕获预期门禁异常；如果没有这行代码，异常会直接中断测试。
            build_openai_auth_config(env=env)  # 新增代码+DirectOAuthConfigTest：执行配置构建；如果没有这行代码，存储门禁不会运行。
        self.assertIn("os_encrypted", error_context.exception.message)  # 新增代码+DirectOAuthConfigTest：确认错误说明指向 OS 加密；如果没有这行代码，用户不知道要使用安全 token store。
    # 新增代码+DirectOAuthConfigTest：测试段结束，OS 加密门禁到此结束；如果没有边界说明，初学者不易看出 direct OAuth 的安全底线。


if __name__ == "__main__":  # 新增代码+OpenAIAuthConfigTest：允许直接运行本测试文件；如果没有这行代码，手动调试需要记住 unittest 命令。
    unittest.main()  # 新增代码+OpenAIAuthConfigTest：启动 unittest runner；如果没有这行代码，直接 python 文件不会执行测试。
