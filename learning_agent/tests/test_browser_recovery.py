"""浏览器恢复管理器测试，锁定 Stage 7 的错误分类和重试预算。"""  # 新增代码+BrowserRecoveryStage7: 说明本测试覆盖恢复策略；若没有这行代码，测试目的不清楚。

from learning_agent.tests.support import *  # 新增代码+BrowserRecoveryStage7: 复用项目测试基础设施；若没有这行代码，unittest 需要重复导入。

from learning_agent.browser.recovery import BrowserRecoveryManager, classify_browser_error  # 新增代码+BrowserRecoveryStage7: 导入待实现恢复模块；若没有这行代码，测试无法驱动 Stage 7。


class BrowserRecoveryStage7Tests(unittest.TestCase):  # 新增代码+BrowserRecoveryStage7: 定义 Stage 7 测试类；若没有这行代码，unittest 无法收集断言。
    def test_error_classifier_covers_browser_failure_modes(self) -> None:  # 新增代码+BrowserRecoveryStage7: 验证常见错误分类；若没有这行代码，恢复策略只能靠模糊字符串。
        self.assertEqual(classify_browser_error("Target page has been closed"), "page_closed")  # 新增代码+BrowserRecoveryStage7: 验证页面关闭分类；若没有这行代码，关闭页面后无法建议重开。
        self.assertEqual(classify_browser_error("Timeout 30000ms exceeded waiting for navigation"), "navigation_timeout")  # 新增代码+BrowserRecoveryStage7: 验证导航超时分类；若没有这行代码，超时恢复无法选择 reload。
        self.assertEqual(classify_browser_error("locator not found for selector"), "locator_not_found")  # 新增代码+BrowserRecoveryStage7: 验证定位失败分类；若没有这行代码，定位失败无法自动 snapshot。
        self.assertEqual(classify_browser_error("Chrome disconnected from CDP"), "chrome_disconnected")  # 新增代码+BrowserRecoveryStage7: 验证 Chrome 断连分类；若没有这行代码，真实 Chrome 掉线无法重连提示。

    def test_recovery_manager_chooses_strategy_and_respects_budget(self) -> None:  # 新增代码+BrowserRecoveryStage7: 验证恢复策略和预算；若没有这行代码，恢复可能无限重试。
        manager = BrowserRecoveryManager(max_attempts_per_error=1)  # 新增代码+BrowserRecoveryStage7: 创建一次预算管理器；若没有这行代码，预算分支不会被覆盖。
        first = manager.plan_recovery("action-1", "Target page has been closed")  # 新增代码+BrowserRecoveryStage7: 计划第一次恢复；若没有这行代码，策略没有输入。
        second = manager.plan_recovery("action-1", "Target page has been closed")  # 新增代码+BrowserRecoveryStage7: 计划第二次恢复；若没有这行代码，预算耗尽分支无法验证。
        self.assertTrue(first["allowed"])  # 新增代码+BrowserRecoveryStage7: 第一次应允许恢复；若没有这行代码，恢复策略可能过度保守。
        self.assertEqual(first["strategy"], "reopen_or_new_page")  # 新增代码+BrowserRecoveryStage7: 页面关闭应建议重开；若没有这行代码，策略可能错误。
        self.assertFalse(second["allowed"])  # 新增代码+BrowserRecoveryStage7: 第二次应因预算拒绝；若没有这行代码，无限恢复风险无法锁定。
        self.assertIn("budget", second["reason"])  # 新增代码+BrowserRecoveryStage7: 失败原因应说明预算；若没有这行代码，用户不知道为什么停下。
