"""浏览器秘密与站点权限测试，锁定 Stage 9 的登录态安全边界。"""  # 新增代码+BrowserSecretStage9: 说明本测试覆盖 secret vault 和 origin 权限；若没有这行代码，测试目的不清楚。

from learning_agent.tests.support import *  # 新增代码+BrowserSecretStage9: 复用项目测试基础设施；若没有这行代码，临时环境和断言工具需要重复导入。

from learning_agent.browser.secret_vault import BrowserSecretVault  # 新增代码+BrowserSecretStage9: 导入待实现秘密库；若没有这行代码，secret ref 无法测试。
from learning_agent.browser.site_permissions import BrowserSitePermissions  # 新增代码+BrowserSecretStage9: 导入待实现站点权限；若没有这行代码，origin 边界无法测试。


class BrowserSecretStage9Tests(unittest.TestCase):  # 新增代码+BrowserSecretStage9: 定义 Stage 9 测试类；若没有这行代码，unittest 无法收集断言。
    def test_secret_vault_allows_only_safe_env_prefixes_and_redacts(self) -> None:  # 新增代码+BrowserSecretStage9: 验证 secret 引用和脱敏；若没有这行代码，密码可能被日志泄露。
        with mock.patch.dict(os.environ, {"LEARNING_AGENT_SECRET_PASSWORD": "zhang111", "PATH": "do-not-read"}, clear=False):  # 新增代码+BrowserSecretStage9: 临时设置环境变量；若没有这行代码，测试会依赖用户真实环境。
            vault = BrowserSecretVault()  # 新增代码+BrowserSecretStage9: 创建秘密库；若没有这行代码，测试没有执行对象。
            resolved = vault.resolve("env:LEARNING_AGENT_SECRET_PASSWORD")  # 新增代码+BrowserSecretStage9: 读取允许前缀的 secret；若没有这行代码，正常登录输入无法验证。
            self.assertEqual(resolved.value, "zhang111")  # 新增代码+BrowserSecretStage9: 验证能取到真实值；若没有这行代码，secret 输入可能为空。
            self.assertEqual(resolved.audit_name, "env:LEARNING_AGENT_SECRET_PASSWORD")  # 新增代码+BrowserSecretStage9: 验证审计只记录引用名；若没有这行代码，日志可能记录明文。
            self.assertIn("[已脱敏]", vault.redact_text("密码是 zhang111"))  # 新增代码+BrowserSecretStage9: 验证明文会从输出脱敏；若没有这行代码，最终回答可能泄露密码。
            with self.assertRaises(PermissionError):  # 新增代码+BrowserSecretStage9: 期待读取普通 PATH 被拒绝；若没有这行代码，模型可能读取无关系统环境。
                vault.resolve("env:PATH")  # 新增代码+BrowserSecretStage9: 尝试读取非白名单环境变量；若没有这行代码，拒绝分支不会被覆盖。

    def test_site_permissions_normalize_grant_and_check_origin(self) -> None:  # 新增代码+BrowserSecretStage9: 验证站点授权边界；若没有这行代码，真实 Chrome 登录态可能被任意站点使用。
        permissions = BrowserSitePermissions(strict=True)  # 新增代码+BrowserSecretStage9: 创建严格权限管理器；若没有这行代码，授权检查没有执行对象。
        permissions.grant("https://example.test/path?a=1")  # 新增代码+BrowserSecretStage9: 授权一个具体 URL；若没有这行代码，允许列表为空。
        self.assertTrue(permissions.is_allowed("https://example.test/next"))  # 新增代码+BrowserSecretStage9: 同 origin 应允许；若没有这行代码，正常同站操作会被误拒。
        self.assertFalse(permissions.is_allowed("https://evil.test/"))  # 新增代码+BrowserSecretStage9: 不同 origin 应拒绝；若没有这行代码，登录态边界失效无法发现。
        self.assertIn("https://example.test", permissions.to_dict()["grants"])  # 新增代码+BrowserSecretStage9: 验证持久化只存 origin；若没有这行代码，授权列表会重复散乱。
