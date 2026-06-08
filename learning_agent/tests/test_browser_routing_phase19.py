"""Phase 19 browser provider 智能路由测试。"""  # 新增代码+Phase19BrowserRouting: 说明本文件专门保护 Phase 19 的浏览器 provider 路由规则；如果没有这行代码，维护者不知道这些测试对应哪个阶段。
from __future__ import annotations  # 新增代码+Phase19BrowserRouting: 延迟解析类型注解，避免运行时因为类型引用顺序导致测试导入失败；如果没有这行代码，未来补类型时更容易出现循环引用问题。

from learning_agent.tests.support import *  # 新增代码+Phase19BrowserRouting: 复用项目测试基类和临时目录工具；如果没有这行代码，测试需要重复编写公共准备逻辑。


class BrowserRoutingPhase19Tests(LearningAgentTestBase):  # 新增代码+Phase19BrowserRouting: 定义 Phase 19 路由测试集合；如果没有这个类，unittest 不会发现本阶段测试。
    def test_chrome_extension_health_requires_pairing_and_reports_supported_tools(self) -> None:  # 新增代码+Phase19BrowserRouting: 验证插件必须连接且配对后才算真正可用；如果没有这个测试，未配对插件可能被误当成生产级通道。
        from learning_agent.browser.providers.chrome_extension import ChromeExtensionProvider  # 新增代码+Phase19BrowserRouting: 导入被测 Chrome extension provider；如果没有这行代码，测试无法检查真实 health 逻辑。
        from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+Phase19BrowserRouting: 导入 bridge 状态对象来模拟扩展连接和配对；如果没有这行代码，测试无法构造插件运行状态。

        bridge_path = Path(tempfile.mkdtemp()) / "phase19_bridge.json"  # 新增代码+Phase19BrowserRouting: 为本测试创建隔离 bridge 文件；如果没有这行代码，测试可能污染真实插件状态。
        bridge = ChromeExtensionBridgeState(bridge_path)  # 新增代码+Phase19BrowserRouting: 创建 bridge 状态实例；如果没有这行代码，provider 没有状态来源。
        provider = ChromeExtensionProvider(bridge)  # 新增代码+Phase19BrowserRouting: 创建插件 provider；如果没有这行代码，无法调用 health。

        bridge.record_connection("extension-phase19")  # 新增代码+Phase19BrowserRouting: 模拟扩展已连接但尚未配对；如果没有这行代码，测试无法区分“已连接”和“已配对”。
        connected_but_unpaired = provider.health()  # 新增代码+Phase19BrowserRouting: 读取未配对状态下的健康结果；如果没有这行代码，无法断言未配对不应可用。

        self.assertFalse(connected_but_unpaired.available)  # 新增代码+Phase19BrowserRouting: 断言未配对插件不可用；如果没有这行代码，路由可能把未授权扩展当成可信通道。
        self.assertEqual(connected_but_unpaired.reason, "chrome_extension_not_paired")  # 新增代码+Phase19BrowserRouting: 断言不可用原因稳定；如果没有这行代码，终端和事件日志难以解释失败原因。
        self.assertEqual(connected_but_unpaired.metadata["paired"], False)  # 新增代码+Phase19BrowserRouting: 断言 metadata 明确暴露配对状态；如果没有这行代码，路由层无法审计为什么没有选插件。

        bridge.record_pairing({"extension_id": "extension-phase19", "device_id": "device-phase19", "session_id": "session-phase19"})  # 新增代码+Phase19BrowserRouting: 模拟完成 extension/device/session 配对；如果没有这行代码，测试无法验证配对后的可用状态。
        paired_health = provider.health()  # 新增代码+Phase19BrowserRouting: 读取已配对状态下的健康结果；如果没有这行代码，无法断言配对后可用。

        self.assertTrue(paired_health.available)  # 新增代码+Phase19BrowserRouting: 断言已配对插件可用；如果没有这行代码，真正配对完成后也可能被错误拦截。
        self.assertEqual(paired_health.metadata["paired"], True)  # 新增代码+Phase19BrowserRouting: 断言 metadata 标记配对完成；如果没有这行代码，provider 决策事件缺少关键证据。
        self.assertIn("browser_snapshot", paired_health.metadata["supported_tools"])  # 新增代码+Phase19BrowserRouting: 断言健康状态暴露插件支持的工具；如果没有这行代码，router 无法避免把不支持的工具发给插件。

    def test_router_prefers_extension_only_when_tool_supported_then_cdp_for_unsupported(self) -> None:  # 新增代码+Phase19BrowserRouting: 验证插件支持工具时优先插件，不支持时改走 CDP；如果没有这个测试，路由会继续粗糙地只看 provider 可用性。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+Phase19BrowserRouting: 导入 provider 健康模型和类型枚举；如果没有这行代码，测试无法构造路由输入。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+Phase19BrowserRouting: 导入被测路由器；如果没有这行代码，测试无法验证 provider 决策。

        router = BrowserProviderRouter()  # 新增代码+Phase19BrowserRouting: 创建默认路由器实例；如果没有这行代码，无法执行路由决策。
        health = {  # 新增代码+Phase19BrowserRouting: 构造插件和 CDP 同时可用的健康快照；如果没有这段代码，测试无法覆盖优先级选择。
            BrowserProviderKind.CHROME_EXTENSION: BrowserProviderHealth.available(BrowserProviderKind.CHROME_EXTENSION, metadata={"paired": True, "supported_tools": ["browser_snapshot"]}),  # 新增代码+Phase19BrowserRouting: 声明插件已配对但只支持 snapshot；如果没有这行代码，无法测试“不支持工具”的分支。
            BrowserProviderKind.REAL_CHROME_CDP: BrowserProviderHealth.available(BrowserProviderKind.REAL_CHROME_CDP),  # 新增代码+Phase19BrowserRouting: 声明真实 Chrome CDP 可作为替代路线；如果没有这行代码，不支持工具时没有可验证 fallback。
        }  # 新增代码+Phase19BrowserRouting: 结束健康快照字典；如果没有这行代码，Python 字典语法不完整。

        supported = router.decide_provider("使用我当前 Chrome 已登录账号截图", "browser_snapshot", {}, health)  # 新增代码+Phase19BrowserRouting: 模拟插件支持的当前 Chrome 任务；如果没有这行代码，无法验证插件优先规则。
        unsupported = router.decide_provider("使用我当前 Chrome 已登录账号上传文件", "browser_upload_file", {}, health)  # 新增代码+Phase19BrowserRouting: 模拟插件不支持但 CDP 可用的任务；如果没有这行代码，无法验证智能改走 CDP。

        self.assertEqual(supported.provider, BrowserProviderKind.CHROME_EXTENSION)  # 新增代码+Phase19BrowserRouting: 断言支持工具时选择插件；如果没有这行代码，插件优先级退化不会被发现。
        self.assertEqual(supported.metadata["supported_tool"], True)  # 新增代码+Phase19BrowserRouting: 断言事件 metadata 记录工具受支持；如果没有这行代码，外部审计看不到选择依据。
        self.assertEqual(unsupported.provider, BrowserProviderKind.REAL_CHROME_CDP)  # 新增代码+Phase19BrowserRouting: 断言插件不支持时选择真实 Chrome CDP；如果没有这行代码，不支持工具可能仍被发给插件导致失败。
        self.assertEqual(unsupported.reason_code, "chrome_extension_tool_unsupported_real_chrome_cdp")  # 新增代码+Phase19BrowserRouting: 断言不支持工具的 reason code 稳定；如果没有这行代码，外部 agent 难以识别该分支。
        self.assertEqual(unsupported.metadata["unsupported_tool"], "browser_upload_file")  # 新增代码+Phase19BrowserRouting: 断言 metadata 记录未支持工具名；如果没有这行代码，排查时不知道为什么切换 provider。

    def test_router_falls_back_to_visible_chromium_when_real_chrome_routes_blocked(self) -> None:  # 新增代码+Phase19BrowserRouting: 验证真实 Chrome 路线受阻时可退到可见 Chromium；如果没有这个测试，普通浏览任务可能因 Chrome 受阻直接失败。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+Phase19BrowserRouting: 导入 provider 健康模型和类型枚举；如果没有这行代码，测试无法构造 provider 状态。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+Phase19BrowserRouting: 导入被测路由器；如果没有这行代码，无法执行路由决策。

        router = BrowserProviderRouter()  # 新增代码+Phase19BrowserRouting: 创建默认路由器；如果没有这行代码，测试没有被测对象。
        health = {  # 新增代码+Phase19BrowserRouting: 构造插件不支持、CDP 不可用、可见 Chromium 可用的状态；如果没有这段代码，无法覆盖最终安全 fallback。
            BrowserProviderKind.CHROME_EXTENSION: BrowserProviderHealth.available(BrowserProviderKind.CHROME_EXTENSION, metadata={"paired": True, "supported_tools": ["browser_snapshot"]}),  # 新增代码+Phase19BrowserRouting: 声明插件已配对但不支持目标工具；如果没有这行代码，无法触发工具不支持分支。
            BrowserProviderKind.REAL_CHROME_CDP: BrowserProviderHealth.unavailable(BrowserProviderKind.REAL_CHROME_CDP, "cdp_blocked"),  # 新增代码+Phase19BrowserRouting: 声明 CDP 被阻断；如果没有这行代码，路由会优先走 CDP 而不是测试可见 Chromium fallback。
            BrowserProviderKind.VISIBLE_CHROMIUM: BrowserProviderHealth.available(BrowserProviderKind.VISIBLE_CHROMIUM),  # 新增代码+Phase19BrowserRouting: 声明隔离可见 Chromium 可用；如果没有这行代码，fallback 没有目标。
        }  # 新增代码+Phase19BrowserRouting: 结束健康快照字典；如果没有这行代码，Python 字典语法不完整。

        decision = router.decide_provider("使用我当前 Chrome 打开网页", "browser_upload_file", {}, health)  # 新增代码+Phase19BrowserRouting: 模拟真实 Chrome 路线受阻的任务；如果没有这行代码，无法验证 fallback 决策。

        self.assertEqual(decision.provider, BrowserProviderKind.VISIBLE_CHROMIUM)  # 新增代码+Phase19BrowserRouting: 断言最终使用可见 Chromium；如果没有这行代码，真实 Chrome 受阻时可能直接不可用。
        self.assertEqual(decision.reason_code, "chrome_extension_tool_unsupported_visible_chromium")  # 新增代码+Phase19BrowserRouting: 断言 fallback reason code 稳定；如果没有这行代码，事件日志无法区分 CDP 阻断和普通公开网页。
        self.assertEqual(decision.metadata["fallback_from"], "chrome_extension")  # 新增代码+Phase19BrowserRouting: 断言 metadata 记录原始目标 provider；如果没有这行代码，审计时看不出是从插件路线降级而来。
