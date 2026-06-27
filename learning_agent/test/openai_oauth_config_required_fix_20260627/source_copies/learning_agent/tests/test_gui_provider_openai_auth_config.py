import unittest  # 新增代码+OpenAIAuthConfigTest：使用项目现有 unittest 风格；如果没有这行代码，测试类不会被标准 runner 发现。


class GuiProviderOpenAIAuthConfigTests(unittest.TestCase):  # 新增代码+OpenAIAuthConfigTest：测试类段开始，锁定 OpenAI OAuth 安全门禁；如果没有这个类，真实 OAuth 可能在不安全配置下误开启。
    def test_default_config_uses_api_key_only_and_blocks_oauth_attempts(self) -> None:  # 修改代码+OpenAIAuthConfigRequiredTest：测试段开始，验证默认配置只允许 API key 路径；如果没有这段，GUI 会继续把本地 mock 伪装成可点击 OAuth。
        from learning_agent.app.gui_provider_openai_auth_config import build_openai_auth_config  # 新增代码+OpenAIAuthConfigTest：导入待测配置 helper；如果没有这行代码，测试没有被测目标。

        config = build_openai_auth_config(env={})  # 新增代码+OpenAIAuthConfigTest：用空环境构造配置；如果没有这行代码，默认值不会被测试。

        self.assertEqual(config.auth_mode, "api_key_only")  # 修改代码+OpenAIAuthConfigRequiredTest：确认默认是 API key only；如果没有这行代码，默认启动仍可能误进 mock OAuth。
        self.assertFalse(config.mock_enabled)  # 修改代码+OpenAIAuthConfigRequiredTest：确认默认不允许 mock flow；如果没有这行代码，用户会继续打开 127.0.0.1 假认证。
        self.assertFalse(config.real_oauth_enabled)  # 新增代码+OpenAIAuthConfigTest：确认默认不允许真实 OAuth；如果没有这行代码，refresh token 保存风险会漏过。
    # 修改代码+OpenAIAuthConfigRequiredTest：测试段结束，默认配置门禁到此结束；如果没有边界说明，初学者不易看出默认只允许 API key。

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


if __name__ == "__main__":  # 新增代码+OpenAIAuthConfigTest：允许直接运行本测试文件；如果没有这行代码，手动调试需要记住 unittest 命令。
    unittest.main()  # 新增代码+OpenAIAuthConfigTest：启动 unittest runner；如果没有这行代码，直接 python 文件不会执行测试。
