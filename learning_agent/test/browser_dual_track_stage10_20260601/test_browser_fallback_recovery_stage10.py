"""Stage 10 fallback and recovery tests for browser dual-track runtime."""  # 新增代码+BrowserFallbackStage10: 说明本文件锁定浏览器降级和失败停止策略；若没有这行代码，测试文件职责不清楚。
from __future__ import annotations  # 新增代码+BrowserFallbackStage10: 延迟解析类型注解；若没有这行代码，旧 Python 解析前向类型时更容易出错。

import tempfile  # 新增代码+BrowserFallbackStage10: 创建隔离工作区；若没有这行代码，测试会污染真实项目目录。
import unittest  # 新增代码+BrowserFallbackStage10: 使用项目现有 unittest 风格；若没有这行代码，测试类无法运行。
from pathlib import Path  # 新增代码+BrowserFallbackStage10: 处理临时工作区路径；若没有这行代码，路径拼接会变成脆弱字符串。

from learning_agent.browser.providers import BrowserProviderDecision, BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserFallbackStage10: 导入 provider 决策模型；若没有这行代码，测试无法构造路由和阻断场景。
from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserFallbackStage10: 导入真实 server；若没有这行代码，只能测 router，不能证明工具入口已接管。


class BrowserFallbackRecoveryStage10Tests(unittest.TestCase):  # 新增代码+BrowserFallbackStage10: 定义 Stage 10 测试集合；若没有这个类，unittest 无法发现测试。
    def make_server(self) -> BrowserAutomationServer:  # 新增代码+BrowserFallbackStage10: 创建隔离 server；若没有这行代码，每个测试都要重复搭建工作区。
        temp_dir = tempfile.TemporaryDirectory()  # 新增代码+BrowserFallbackStage10: 创建临时目录对象；若没有这行代码，测试会写入真实工作区。
        self.addCleanup(temp_dir.cleanup)  # 新增代码+BrowserFallbackStage10: 测试结束自动清理目录；若没有这行代码，临时文件会残留。
        return BrowserAutomationServer(Path(temp_dir.name))  # 新增代码+BrowserFallbackStage10: 返回使用临时工作区的 server；若没有这行代码，测试拿不到被测对象。

    def install_health(self, server: BrowserAutomationServer) -> None:  # 新增代码+BrowserFallbackStage10: 注入稳定 provider 健康状态；若没有这行代码，测试会依赖本机浏览器真实状态。
        server.browser_provider_registry.all_health = lambda: {  # 新增代码+BrowserFallbackStage10: 用 lambda 覆盖健康读取；若没有这行代码，测试无法稳定模拟插件断开。
            BrowserProviderKind.CHROME_EXTENSION: BrowserProviderHealth.unavailable(BrowserProviderKind.CHROME_EXTENSION, "extension_disconnected"),  # 新增代码+BrowserFallbackStage10: 模拟插件不可用；若没有这行代码，降级规则不会触发。
            BrowserProviderKind.REAL_CHROME_CDP: BrowserProviderHealth.available(BrowserProviderKind.REAL_CHROME_CDP, "cdp_ready"),  # 新增代码+BrowserFallbackStage10: 模拟 CDP 可作为候选；若没有这行代码，无法区分候选和不可用。
            BrowserProviderKind.VISIBLE_CHROMIUM: BrowserProviderHealth.available(BrowserProviderKind.VISIBLE_CHROMIUM, "visible_ready"),  # 新增代码+BrowserFallbackStage10: 模拟公开网页轨道可用；若没有这行代码，默认公开网页路由不稳定。
        }  # 新增代码+BrowserFallbackStage10: 结束健康状态字典；若没有这行代码，Python 语法不完整。

    def test_current_chrome_task_does_not_silently_allow_cdp_fallback(self) -> None:  # 新增代码+BrowserFallbackStage10: 验证真实 Chrome 场景不会静默降级；若没有这行代码，server 可能继续把 allow_cdp_fallback 写死为 True。
        server = self.make_server()  # 新增代码+BrowserFallbackStage10: 创建被测 server；若没有这行代码，后续没有对象可调用。
        self.install_health(server)  # 新增代码+BrowserFallbackStage10: 注入插件断开但 CDP 可用状态；若没有这行代码，测试不稳定。
        server._tabs_context_contract_applies = lambda: True  # 新增代码+BrowserFallbackStage10: 强制模拟当前 Chrome/登录态任务；若没有这行代码，router 会按公开网页处理。
        decision = server._decide_browser_provider_for_tool("browser_click", {"selector": "#login"})  # 新增代码+BrowserFallbackStage10: 调用真实 server 路由入口；若没有这行代码，无法发现工具入口硬编码降级。
        self.assertEqual(decision.provider, BrowserProviderKind.UNAVAILABLE)  # 新增代码+BrowserFallbackStage10: 断言未确认时不可执行；若没有这行代码，静默 CDP 降级会漏网。
        self.assertEqual(decision.fallback_provider, BrowserProviderKind.REAL_CHROME_CDP)  # 新增代码+BrowserFallbackStage10: 断言 CDP 只是候选；若没有这行代码，用户不知道可选修复路径。
        self.assertTrue(decision.requires_user_confirmation)  # 新增代码+BrowserFallbackStage10: 断言必须用户确认；若没有这行代码，高风险降级门禁不成立。

    def test_current_chrome_task_allows_cdp_only_when_explicitly_confirmed(self) -> None:  # 新增代码+BrowserFallbackStage10: 验证显式允许时才走 CDP；若没有这行代码，确认开关可能失效。
        server = self.make_server()  # 新增代码+BrowserFallbackStage10: 创建被测 server；若没有这行代码，后续没有对象可调用。
        self.install_health(server)  # 新增代码+BrowserFallbackStage10: 注入稳定 provider 健康状态；若没有这行代码，测试依赖真实环境。
        server._tabs_context_contract_applies = lambda: True  # 新增代码+BrowserFallbackStage10: 强制模拟登录态任务；若没有这行代码，降级规则不会进入插件分支。
        decision = server._decide_browser_provider_for_tool("browser_click", {"selector": "#login", "allow_cdp_fallback": True})  # 新增代码+BrowserFallbackStage10: 带显式降级确认调用路由；若没有这行代码，授权分支没有覆盖。
        self.assertEqual(decision.provider, BrowserProviderKind.REAL_CHROME_CDP)  # 新增代码+BrowserFallbackStage10: 断言确认后才选择 CDP；若没有这行代码，授权降级结果不明确。
        self.assertEqual(decision.reason_code, "extension_unavailable_cdp_fallback_allowed")  # 新增代码+BrowserFallbackStage10: 断言原因码稳定；若没有这行代码，外部 agent 难以审计。

    def test_unavailable_provider_blocks_fallback_handler(self) -> None:  # 新增代码+BrowserFallbackStage10: 验证 unavailable 决策不会继续执行旧 handler；若没有这行代码，路由阻断只是纸面结果。
        server = self.make_server()  # 新增代码+BrowserFallbackStage10: 创建被测 server；若没有这行代码，后续没有对象可调用。
        decision = BrowserProviderDecision(provider=BrowserProviderKind.UNAVAILABLE, reason="插件不可用，需要用户确认", tool_name="browser_click", fallback_provider=BrowserProviderKind.REAL_CHROME_CDP, requires_user_confirmation=True)  # 新增代码+BrowserFallbackStage10: 构造不可用决策；若没有这行代码，阻断分支没有输入。
        handler = server._provider_handler_for_tool(decision, "browser_click", lambda _arguments: "should not run")  # 新增代码+BrowserFallbackStage10: 请求 server 包装 handler；若没有这行代码，无法验证实际执行入口。
        with self.assertRaises(RuntimeError) as caught:  # 新增代码+BrowserFallbackStage10: 捕获预期阻断异常；若没有这行代码，测试无法检查错误内容。
            handler({})  # 新增代码+BrowserFallbackStage10: 执行包装后 handler；若没有这行代码，阻断逻辑不会运行。
        self.assertIn("插件不可用", str(caught.exception))  # 新增代码+BrowserFallbackStage10: 断言错误说明原始原因；若没有这行代码，用户可能只看到泛化失败。
        self.assertIn("allow_cdp_fallback=true", str(caught.exception))  # 新增代码+BrowserFallbackStage10: 断言提示显式确认参数；若没有这行代码，用户不知道如何安全降级。

    def test_tabs_context_contract_requests_refresh_when_stale(self) -> None:  # 新增代码+BrowserFallbackStage10: 验证旧 tab context 会要求刷新；若没有这行代码，模型可能继续复用失效 context。
        server = self.make_server()  # 新增代码+BrowserFallbackStage10: 创建被测 server；若没有这行代码，后续没有对象可调用。
        server._tabs_context_contract_applies = lambda: True  # 新增代码+BrowserFallbackStage10: 强制进入真实 Chrome context 门禁；若没有这行代码，写动作不会被检查。
        server._tabs_context_is_valid = lambda: False  # 新增代码+BrowserFallbackStage10: 模拟 context 已失效；若没有这行代码，测试无法稳定触发错误。
        server.tabs_context_last_reason = "active tab 已变化"  # 新增代码+BrowserFallbackStage10: 设置失效原因；若没有这行代码，错误文案没有可断言内容。
        with self.assertRaises(RuntimeError) as caught:  # 新增代码+BrowserFallbackStage10: 捕获预期门禁异常；若没有这行代码，测试无法检查提示。
            server._enforce_tabs_context_contract("browser_click")  # 新增代码+BrowserFallbackStage10: 执行写动作门禁；若没有这行代码，刷新提示不会生成。
        self.assertIn("重新调用 browser_tabs_context", str(caught.exception))  # 新增代码+BrowserFallbackStage10: 断言明确要求重读 context；若没有这行代码，模型下一步可能猜错。

    def test_consecutive_failure_budget_stops_after_three_failures(self) -> None:  # 新增代码+BrowserFallbackStage10: 验证连续失败刹车；若没有这行代码，浏览器任务可能在坏页面上反复乱试。
        server = self.make_server()  # 新增代码+BrowserFallbackStage10: 创建被测 server；若没有这行代码，后续没有对象可调用。
        first = server._record_browser_tool_failure("browser_click", RuntimeError("fail-1"))  # 新增代码+BrowserFallbackStage10: 记录第一次失败；若没有这行代码，预算不会推进。
        second = server._record_browser_tool_failure("browser_click", RuntimeError("fail-2"))  # 新增代码+BrowserFallbackStage10: 记录第二次失败；若没有这行代码，无法验证临界前状态。
        third = server._record_browser_tool_failure("browser_click", RuntimeError("fail-3"))  # 新增代码+BrowserFallbackStage10: 记录第三次失败；若没有这行代码，停止条件不会触发。
        self.assertFalse(first["stop_required"])  # 新增代码+BrowserFallbackStage10: 第一次失败不立刻停止；若没有这行代码，恢复策略会过早中断。
        self.assertFalse(second["stop_required"])  # 新增代码+BrowserFallbackStage10: 第二次失败仍允许上层恢复；若没有这行代码，2-3 次预算语义不清。
        self.assertTrue(third["stop_required"])  # 新增代码+BrowserFallbackStage10: 第三次失败必须停止；若没有这行代码，连续失败刹车没有被锁定。
        server._reset_browser_tool_failure_budget()  # 新增代码+BrowserFallbackStage10: 模拟成功动作后复位预算；若没有这行代码，恢复后仍会误报连续失败。
        self.assertEqual(server.browser_consecutive_failure_count, 0)  # 新增代码+BrowserFallbackStage10: 断言复位成功；若没有这行代码，成功动作后仍可能被旧失败状态拖累。


if __name__ == "__main__":  # 新增代码+BrowserFallbackStage10: 支持直接运行测试文件；若没有这行代码，人工调试需要额外命令格式。
    unittest.main()  # 新增代码+BrowserFallbackStage10: 启动 unittest；若没有这行代码，直接运行文件不会执行测试。
