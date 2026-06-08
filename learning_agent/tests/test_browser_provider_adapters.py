"""浏览器 provider adapter 测试。"""  # 新增代码+BrowserProviderAdapters: 说明本文件锁定 Stage 2 provider adapter 迁入行为；若没有这行代码，维护者不知道这些测试保护双轨执行层。
from __future__ import annotations  # 新增代码+BrowserProviderAdapters: 延迟解析类型注解；若没有这行代码，局部测试类的类型引用在旧解释顺序下更脆弱。

from learning_agent.tests.support import *  # 新增代码+BrowserProviderAdapters: 复用 unittest、tempfile、Path 等测试基础设施；若没有这行代码，测试会重复导入公共 helper。


class BrowserProviderAdapterTests(LearningAgentTestBase):  # 新增代码+BrowserProviderAdapters: 定义 Stage 2 provider adapter 测试集；若没有这个类，unittest 不会收集本阶段测试。
    def test_visible_chromium_provider_delegates_browser_open(self) -> None:  # 新增代码+BrowserProviderAdapters: 验证可见 Chromium provider 会委托旧 browser_open；若没有这行代码，adapter 可能只是空壳。
        from learning_agent.browser.providers.visible_chromium import VisibleChromiumProvider  # 新增代码+BrowserProviderAdapters: 导入待实现可见 Chromium provider；若没有这行代码，测试无法驱动 adapter。
        class FakeServer:  # 新增代码+BrowserProviderAdapters: 定义最小 fake server；若没有这个类，测试会误启动真实浏览器。
            def __init__(self) -> None:  # 新增代码+BrowserProviderAdapters: 初始化调用记录；若没有这行代码，无法断言委托发生。
                self.calls: list[tuple[str, dict[str, object]]] = []  # 新增代码+BrowserProviderAdapters: 保存调用过的工具和参数；若没有这行代码，测试没有证据。
            def browser_open(self, arguments: dict[str, object]) -> str:  # 新增代码+BrowserProviderAdapters: 模拟旧 server 的 browser_open 方法；若没有这行代码，provider 没有可委托目标。
                self.calls.append(("browser_open", arguments))  # 新增代码+BrowserProviderAdapters: 记录委托调用；若没有这行代码，无法证明 adapter 调了旧方法。
                return f"open:{arguments['url']}"  # 新增代码+BrowserProviderAdapters: 返回可断言文本；若没有这行代码，测试无法确认返回值兼容。
        server = FakeServer()  # 新增代码+BrowserProviderAdapters: 创建 fake server；若没有这行代码，provider 无 backend。
        provider = VisibleChromiumProvider(server)  # 新增代码+BrowserProviderAdapters: 用 fake server 创建 provider；若没有这行代码，测试没有被测对象。
        result = provider.execute_tool("browser_open", {"url": "https://example.com"})  # 新增代码+BrowserProviderAdapters: 通过 provider 执行统一工具；若没有这行代码，委托路径未被触发。
        self.assertEqual(result, "open:https://example.com")  # 新增代码+BrowserProviderAdapters: 断言 provider 保留旧返回文本；若没有这行代码，adapter 可能破坏 MCP 输出。
        self.assertEqual(server.calls, [("browser_open", {"url": "https://example.com"})])  # 新增代码+BrowserProviderAdapters: 断言旧 handler 被调用且参数不变；若没有这行代码，adapter 参数可能串味。

    def test_real_chrome_cdp_provider_delegates_connect_tool(self) -> None:  # 新增代码+BrowserProviderAdapters: 验证 CDP provider 会委托真实 Chrome 连接工具；若没有这行代码，CDP 迁入 provider 没有测试保护。
        from learning_agent.browser.providers.real_chrome_cdp import RealChromeCdpProvider  # 新增代码+BrowserProviderAdapters: 导入待实现 CDP provider；若没有这行代码，测试无法驱动 CDP adapter。
        class FakeServer:  # 新增代码+BrowserProviderAdapters: 定义最小 fake server；若没有这个类，测试可能误触真实 Chrome。
            def __init__(self) -> None:  # 新增代码+BrowserProviderAdapters: 初始化调用记录；若没有这行代码，无法断言委托。
                self.calls: list[tuple[str, dict[str, object]]] = []  # 新增代码+BrowserProviderAdapters: 保存调用记录；若没有这行代码，测试缺少证据。
            def browser_connect_real_chrome(self, arguments: dict[str, object]) -> str:  # 新增代码+BrowserProviderAdapters: 模拟真实 Chrome 连接 handler；若没有这行代码，provider 没有目标方法。
                self.calls.append(("browser_connect_real_chrome", arguments))  # 新增代码+BrowserProviderAdapters: 记录连接调用；若没有这行代码，无法证明 provider 委托。
                return "real_chrome_connected=true"  # 新增代码+BrowserProviderAdapters: 返回机器可读成功标记；若没有这行代码，测试无法确认结果。
        server = FakeServer()  # 新增代码+BrowserProviderAdapters: 创建 fake server；若没有这行代码，provider 无 backend。
        provider = RealChromeCdpProvider(server)  # 新增代码+BrowserProviderAdapters: 用 fake server 创建 CDP provider；若没有这行代码，测试没有被测对象。
        result = provider.execute_tool("browser_connect_real_chrome", {"confirm_real_profile": True})  # 新增代码+BrowserProviderAdapters: 通过 provider 执行 CDP 连接工具；若没有这行代码，委托路径不触发。
        self.assertIn("real_chrome_connected=true", result)  # 新增代码+BrowserProviderAdapters: 断言返回文本保持兼容；若没有这行代码，adapter 可能吞掉连接结果。
        self.assertEqual(server.calls, [("browser_connect_real_chrome", {"confirm_real_profile": True})])  # 新增代码+BrowserProviderAdapters: 断言参数原样传给旧 handler；若没有这行代码，高风险确认参数可能丢失。

    def test_registry_can_register_provider_and_report_health(self) -> None:  # 新增代码+BrowserProviderAdapters: 验证 registry 能管理 provider 对象；若没有这行代码，router 仍只能接收散落 health dict。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderAdapters: 导入 provider 健康和类型；若没有这行代码，fake provider 无法返回标准状态。
        from learning_agent.browser.providers.registry import BrowserProviderRegistry  # 新增代码+BrowserProviderAdapters: 导入 provider registry；若没有这行代码，测试没有被测注册表。
        class FakeProvider:  # 新增代码+BrowserProviderAdapters: 定义最小 provider；若没有这个类，registry 注册路径没有输入。
            kind = BrowserProviderKind.VISIBLE_CHROMIUM  # 新增代码+BrowserProviderAdapters: 声明 provider 类型；若没有这行代码，registry 不知道按哪个 kind 保存。
            def health(self) -> BrowserProviderHealth:  # 新增代码+BrowserProviderAdapters: 返回 provider 当前健康状态；若没有这行代码，registry 无法刷新健康。
                return BrowserProviderHealth.available(self.kind, "fake_ready")  # 新增代码+BrowserProviderAdapters: 声明 fake provider 可用；若没有这行代码，测试无法断言 available。
            def supports_tool(self, tool_name: str) -> bool:  # 新增代码+BrowserProviderAdapters: 提供协议所需方法；若没有这行代码，FakeProvider 不像真实 provider。
                return tool_name == "browser_open"  # 新增代码+BrowserProviderAdapters: 只支持 browser_open；若没有这行代码，测试无法表达工具能力。
            def execute_tool(self, tool_name: str, arguments: dict[str, object]) -> str:  # 新增代码+BrowserProviderAdapters: 提供协议所需执行方法；若没有这行代码，FakeProvider 不完整。
                return f"{tool_name}:{arguments}"  # 新增代码+BrowserProviderAdapters: 返回调试文本；若没有这行代码，执行方法没有语义。
        provider = FakeProvider()  # 新增代码+BrowserProviderAdapters: 创建 fake provider；若没有这行代码，registry 无对象可注册。
        registry = BrowserProviderRegistry()  # 新增代码+BrowserProviderAdapters: 创建 registry；若没有这行代码，测试没有被测对象。
        registry.register_provider(provider)  # 新增代码+BrowserProviderAdapters: 注册 provider 并刷新健康状态；若没有这行代码，registry 仍是空表。
        self.assertIs(registry.provider(BrowserProviderKind.VISIBLE_CHROMIUM), provider)  # 新增代码+BrowserProviderAdapters: 断言能取回同一 provider；若没有这行代码，执行层无法从 registry 找 adapter。
        self.assertTrue(registry.health(BrowserProviderKind.VISIBLE_CHROMIUM).available)  # 新增代码+BrowserProviderAdapters: 断言注册后健康状态可用；若没有这行代码，router 可能看不到 provider 可用。
        self.assertEqual(registry.all_providers()[BrowserProviderKind.VISIBLE_CHROMIUM], provider)  # 新增代码+BrowserProviderAdapters: 断言 provider 快照包含注册对象；若没有这行代码，状态 API 难以列 provider。

    def test_server_routes_visible_tool_through_provider_and_records_decision(self) -> None:  # 新增代码+BrowserProviderAdapters: 验证生产 server 顶层调用经过 provider 并写决策事件；若没有这行代码，Stage 2 接入可能只停在独立类。
        from learning_agent.browser.runtime_events import BROWSER_PROVIDER_DECISION  # 新增代码+BrowserProviderAdapters: 导入 provider 决策事件名；若没有这行代码，测试会写死字符串。
        from learning_agent.browser.providers.visible_chromium import VisibleChromiumProvider  # 新增代码+BrowserProviderAdapters: 导入 provider adapter 供 spy 继承；若没有这行代码，测试无法观察 provider 执行。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserProviderAdapters: 导入真实 server；若没有这行代码，测试不能覆盖生产入口。
        class RecordingVisibleProvider(VisibleChromiumProvider):  # 新增代码+BrowserProviderAdapters: 定义记录执行工具的 provider；若没有这个类，无法证明 server.call 走了 provider。
            def __init__(self, backend: object) -> None:  # 新增代码+BrowserProviderAdapters: 初始化 spy provider；若没有这行代码，无法保存调用记录。
                super().__init__(backend)  # 新增代码+BrowserProviderAdapters: 复用真实 provider 委托逻辑；若没有这行代码，spy 会偏离生产行为。
                self.executed_tools: list[str] = []  # 新增代码+BrowserProviderAdapters: 保存执行过的工具名；若没有这行代码，断言没有数据。
            def execute_tool(self, tool_name: str, arguments: dict[str, object]) -> str:  # 新增代码+BrowserProviderAdapters: 拦截执行入口；若没有这行代码，无法记录工具名。
                self.executed_tools.append(tool_name)  # 新增代码+BrowserProviderAdapters: 记录 provider 执行工具；若没有这行代码，测试不知道是否经过 provider。
                return super().execute_tool(tool_name, arguments)  # 新增代码+BrowserProviderAdapters: 继续调用真实 adapter；若没有这行代码，工具不会返回旧 handler 结果。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserProviderAdapters: 使用临时 workspace 隔离 runtime store；若没有这行代码，测试会污染真实 memory。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserProviderAdapters: 创建真实 server；若没有这行代码，生产 call 入口无法测试。
            server.browser_wait = lambda arguments: "browser_wait 成功\nprovider_adapter=true"  # 新增代码+BrowserProviderAdapters: 用假等待避免真实 sleep；若没有这行代码，测试变慢且不稳定。
            recorder = RecordingVisibleProvider(server)  # 新增代码+BrowserProviderAdapters: 创建可观察 provider；若没有这行代码，server 没有 spy provider。
            server.visible_chromium_provider = recorder  # 新增代码+BrowserProviderAdapters: 替换 server 的可见 provider；若没有这行代码，无法观察 provider 调用。
            server.browser_provider_registry.register_provider(recorder)  # 新增代码+BrowserProviderAdapters: 把 spy provider 注册回 registry；若没有这行代码，router 健康状态仍可能指向旧对象。
            result = server.call("browser_wait", {"milliseconds": 1})  # 新增代码+BrowserProviderAdapters: 通过公开入口执行只读等待工具；若没有这行代码，provider 和事件都不会触发。
            run_id = server.browser_runtime_store.list_run_ids()[-1]  # 新增代码+BrowserProviderAdapters: 获取本次 browser run id；若没有这行代码，无法读取事件。
            events = server.browser_runtime_store.tail_events(run_id, limit=0)  # 新增代码+BrowserProviderAdapters: 读取完整事件流；若没有这行代码，无法检查 provider 决策。
        provider_events = [event for event in events if event["event_type"] == BROWSER_PROVIDER_DECISION]  # 新增代码+BrowserProviderAdapters: 筛选 provider 决策事件；若没有这行代码，断言会混入其他事件。
        self.assertIn("browser_wait 成功", result)  # 新增代码+BrowserProviderAdapters: 断言原工具输出保留；若没有这行代码，provider 接入可能破坏返回。
        self.assertEqual(recorder.executed_tools, ["browser_wait"])  # 新增代码+BrowserProviderAdapters: 断言 server.call 经过可见 provider；若没有这行代码，server 可能仍直接调 dispatch。
        self.assertEqual(provider_events[-1]["payload"]["provider"], "visible_chromium")  # 新增代码+BrowserProviderAdapters: 断言事件记录选择可见 Chromium；若没有这行代码，其他 agent 无法复盘 provider 决策。

    def test_server_routes_real_chrome_connect_through_cdp_provider(self) -> None:  # 新增代码+BrowserProviderAdapters: 验证真实 Chrome 连接入口通过 CDP provider；若没有这行代码，高风险连接可能绕过 provider 决策。
        from learning_agent.browser.providers.real_chrome_cdp import RealChromeCdpProvider  # 新增代码+BrowserProviderAdapters: 导入 CDP provider 供 spy 继承；若没有这行代码，测试无法观察 CDP provider。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserProviderAdapters: 导入真实 server；若没有这行代码，生产 call 入口无法测试。
        class RecordingCdpProvider(RealChromeCdpProvider):  # 新增代码+BrowserProviderAdapters: 定义记录 CDP 执行的 provider；若没有这个类，无法证明 call 走 CDP provider。
            def __init__(self, backend: object) -> None:  # 新增代码+BrowserProviderAdapters: 初始化记录列表；若没有这行代码，无法保存执行证据。
                super().__init__(backend)  # 新增代码+BrowserProviderAdapters: 复用真实 CDP adapter 委托逻辑；若没有这行代码，spy 行为不贴近生产。
                self.executed_tools: list[str] = []  # 新增代码+BrowserProviderAdapters: 保存执行工具名；若没有这行代码，断言无数据。
            def execute_tool(self, tool_name: str, arguments: dict[str, object]) -> str:  # 新增代码+BrowserProviderAdapters: 拦截 CDP 执行入口；若没有这行代码，无法记录工具名。
                self.executed_tools.append(tool_name)  # 新增代码+BrowserProviderAdapters: 记录 CDP 工具名；若没有这行代码，测试不知道是否经过 provider。
                return super().execute_tool(tool_name, arguments)  # 新增代码+BrowserProviderAdapters: 继续委托旧 handler；若没有这行代码，工具输出丢失。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserProviderAdapters: 使用临时 workspace 隔离 run；若没有这行代码，测试会污染真实状态。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserProviderAdapters: 创建真实 server；若没有这行代码，无法覆盖 call。
            server.browser_connect_real_chrome = lambda arguments: "browser_connect_real_chrome 成功\nreal_chrome_connected=true"  # 新增代码+BrowserProviderAdapters: 用假连接避免启动真实 Chrome；若没有这行代码，单测会触碰用户浏览器。
            recorder = RecordingCdpProvider(server)  # 新增代码+BrowserProviderAdapters: 创建 CDP spy provider；若没有这行代码，server 没有可观察 provider。
            server.real_chrome_cdp_provider = recorder  # 新增代码+BrowserProviderAdapters: 替换 server 的 CDP provider；若没有这行代码，无法观察 provider 调用。
            server.browser_provider_registry.register_provider(recorder)  # 新增代码+BrowserProviderAdapters: 注册 CDP spy；若没有这行代码，router 健康状态可能仍用旧 provider。
            result = server.call("browser_connect_real_chrome", {"confirm_real_profile": True})  # 新增代码+BrowserProviderAdapters: 通过公开入口执行真实 Chrome 连接；若没有这行代码，CDP provider 不会触发。
        self.assertIn("real_chrome_connected=true", result)  # 新增代码+BrowserProviderAdapters: 断言旧 handler 输出保留；若没有这行代码，provider 可能破坏连接结果。
        self.assertEqual(recorder.executed_tools, ["browser_connect_real_chrome"])  # 新增代码+BrowserProviderAdapters: 断言连接工具通过 CDP provider；若没有这行代码，真实 Chrome 可能绕过双轨架构。
