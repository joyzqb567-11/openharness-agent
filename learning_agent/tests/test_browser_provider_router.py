"""浏览器 provider router 测试。"""  # 新增代码+BrowserProviderRouter: 说明本文件锁定双轨浏览器路由规则；若没有这行代码，维护者不知道测试保护哪条架构原则。
from __future__ import annotations  # 新增代码+BrowserProviderRouter: 延迟解析类型注解；若没有这行代码，后续类型引用在旧解释顺序下更脆弱。

from learning_agent.tests.support import *  # 新增代码+BrowserProviderRouter: 复用项目测试基类和临时目录 helper；若没有这行代码，测试会重复公共准备逻辑。


class BrowserProviderRouterTests(LearningAgentTestBase):  # 新增代码+BrowserProviderRouter: 定义 provider router 测试集合；若没有这个类，unittest 不会发现本组路由规则测试。
    def test_public_web_query_defaults_to_visible_chromium(self) -> None:  # 新增代码+BrowserProviderRouter: 验证公开网页查询默认走隔离可见浏览器；若没有这行代码，模型可能误碰用户真实 Chrome。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，测试无法构造 provider 输入。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导入被测路由器；若没有这行代码，测试无法锁定公开 API。
        router = BrowserProviderRouter()  # 新增代码+BrowserProviderRouter: 创建默认路由器；若没有这行代码，无法执行 provider 决策。
        health = {BrowserProviderKind.VISIBLE_CHROMIUM: BrowserProviderHealth.available(BrowserProviderKind.VISIBLE_CHROMIUM)}  # 新增代码+BrowserProviderRouter: 声明可见 Chromium 可用；若没有这行代码，路由器没有健康输入。
        decision = router.decide_provider(user_input="帮我查询明天武汉天气", tool_name="browser_open", arguments={"url": "https://www.baidu.com"}, provider_health=health)  # 新增代码+BrowserProviderRouter: 模拟公开网页查询；若没有这行代码，无法验证默认路线。
        self.assertEqual(decision.provider, BrowserProviderKind.VISIBLE_CHROMIUM)  # 新增代码+BrowserProviderRouter: 断言公开查询走可见 Chromium；若没有这行代码，默认路线错误不会报红。
        self.assertFalse(decision.requires_user_confirmation)  # 新增代码+BrowserProviderRouter: 断言低风险公开查询不需要额外确认；若没有这行代码，普通查询可能被不必要打断。

    def test_current_chrome_login_state_prefers_extension(self) -> None:  # 新增代码+BrowserProviderRouter: 验证当前 Chrome 登录态任务优先插件 provider；若没有这行代码，登录态任务可能误走 CDP 或独立浏览器。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，测试无法表示插件可用。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导入被测路由器；若没有这行代码，测试无法执行路由。
        router = BrowserProviderRouter()  # 新增代码+BrowserProviderRouter: 创建默认路由器；若没有这行代码，无法得到 provider 决策。
        health = {BrowserProviderKind.CHROME_EXTENSION: BrowserProviderHealth.available(BrowserProviderKind.CHROME_EXTENSION), BrowserProviderKind.REAL_CHROME_CDP: BrowserProviderHealth.available(BrowserProviderKind.REAL_CHROME_CDP)}  # 新增代码+BrowserProviderRouter: 同时声明插件和 CDP 可用；若没有这行代码，无法证明插件优先级高于 CDP。
        decision = router.decide_provider(user_input="使用我当前 Chrome 已登录账号查看订单", tool_name="browser_snapshot", arguments={}, provider_health=health)  # 新增代码+BrowserProviderRouter: 模拟当前 Chrome 登录态任务；若没有这行代码，插件优先规则没有输入。
        self.assertEqual(decision.provider, BrowserProviderKind.CHROME_EXTENSION)  # 新增代码+BrowserProviderRouter: 断言插件优先；若没有这行代码，核心双轨策略可能失效。
        self.assertIn("登录态", decision.reason)  # 新增代码+BrowserProviderRouter: 断言原因文本可审计；若没有这行代码，event log 难以解释决策。

    def test_existing_real_browser_keywords_prefer_extension(self) -> None:  # 新增代码+BrowserProviderRouter: 验证 router 覆盖已有 intent.py 中的真实浏览器表达；若没有这行代码，关键词漂移会让真实浏览器请求误走可见 Chromium。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，测试无法声明插件可用。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导入被测路由器；若没有这行代码，无法检查关键词路由。
        router = BrowserProviderRouter()  # 新增代码+BrowserProviderRouter: 创建默认路由器；若没有这行代码，无法执行 provider 决策。
        health = {BrowserProviderKind.CHROME_EXTENSION: BrowserProviderHealth.available(BrowserProviderKind.CHROME_EXTENSION)}  # 新增代码+BrowserProviderRouter: 声明插件 provider 可用；若没有这行代码，真实浏览器关键词没有可选目标。
        prompts = ("当前浏览器打开页面", "真实浏览器查询", "真实 Chrome 登录态", "current browser tab", "login state page")  # 新增代码+BrowserProviderRouter: 覆盖审查指出的中英文漏判表达；若没有这行代码，关键词缺口不会被测试锁住。
        for prompt in prompts:  # 新增代码+BrowserProviderRouter: 遍历每个真实浏览器表达；若没有这行代码，只会覆盖一个样本。
            decision = router.decide_provider(user_input=prompt, tool_name="browser_snapshot", arguments={}, provider_health=health)  # 新增代码+BrowserProviderRouter: 对每个 prompt 执行路由；若没有这行代码，循环没有被测行为。
            self.assertEqual(decision.provider, BrowserProviderKind.CHROME_EXTENSION, prompt)  # 新增代码+BrowserProviderRouter: 断言真实浏览器表达走插件；若没有这行代码，漏判不会报红。

    def test_extension_unavailable_does_not_silently_fallback_without_permission(self) -> None:  # 新增代码+BrowserProviderRouter: 验证插件不可用时不能静默降级；若没有这行代码，真实 Chrome 登录态任务可能误走 CDP。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，测试无法表达插件不可用。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导入被测路由器；若没有这行代码，无法测试 fallback。
        router = BrowserProviderRouter()  # 新增代码+BrowserProviderRouter: 创建默认路由器；若没有这行代码，无法执行路由。
        health = {BrowserProviderKind.CHROME_EXTENSION: BrowserProviderHealth.unavailable(BrowserProviderKind.CHROME_EXTENSION, "extension_not_connected"), BrowserProviderKind.REAL_CHROME_CDP: BrowserProviderHealth.available(BrowserProviderKind.REAL_CHROME_CDP)}  # 新增代码+BrowserProviderRouter: 插件不可用但 CDP 可用；若没有这行代码，无法验证不静默降级。
        decision = router.decide_provider(user_input="使用我当前 Chrome 登录态打开网页", tool_name="browser_open", arguments={"url": "https://example.com"}, provider_health=health)  # 新增代码+BrowserProviderRouter: 模拟登录态任务；若没有这行代码，fallback 规则没有触发条件。
        self.assertEqual(decision.provider, BrowserProviderKind.UNAVAILABLE)  # 新增代码+BrowserProviderRouter: 断言没有用户许可时返回不可用；若没有这行代码，静默降级风险不会被捕获。
        self.assertEqual(decision.fallback_provider, BrowserProviderKind.REAL_CHROME_CDP)  # 新增代码+BrowserProviderRouter: 断言 CDP 只是候选 fallback；若没有这行代码，用户无法知道可选路线。
        self.assertTrue(decision.requires_user_confirmation)  # 新增代码+BrowserProviderRouter: 断言需要用户确认；若没有这行代码，高风险降级可能直接执行。

    def test_allowed_cdp_fallback_records_source_without_self_fallback(self) -> None:  # 新增代码+BrowserProviderRouter: 验证明确允许降级时最终 provider 和 fallback 来源语义清晰；若没有这行代码，event log 会把 provider 和 fallback 混在一起。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，测试无法构造插件不可用和 CDP 可用状态。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导入被测路由器；若没有这行代码，无法覆盖降级分支。
        router = BrowserProviderRouter()  # 新增代码+BrowserProviderRouter: 创建默认路由器；若没有这行代码，无法执行路由。
        health = {BrowserProviderKind.CHROME_EXTENSION: BrowserProviderHealth.unavailable(BrowserProviderKind.CHROME_EXTENSION, "extension_not_connected"), BrowserProviderKind.REAL_CHROME_CDP: BrowserProviderHealth.available(BrowserProviderKind.REAL_CHROME_CDP)}  # 新增代码+BrowserProviderRouter: 插件不可用但 CDP 可用；若没有这行代码，降级分支不会触发。
        decision = router.decide_provider(user_input="使用我当前浏览器登录态打开网页", tool_name="browser_open", arguments={"url": "https://example.com"}, provider_health=health, allow_cdp_fallback=True)  # 新增代码+BrowserProviderRouter: 明确允许 CDP 降级；若没有这行代码，无法验证授权降级语义。
        self.assertEqual(decision.provider, BrowserProviderKind.REAL_CHROME_CDP)  # 新增代码+BrowserProviderRouter: 断言最终执行 provider 是 CDP；若没有这行代码，降级结果不明确。
        self.assertEqual(decision.fallback_provider, BrowserProviderKind.UNAVAILABLE)  # 新增代码+BrowserProviderRouter: 断言已执行降级后不再把 CDP 自己标为 fallback；若没有这行代码，事件语义会自相矛盾。
        self.assertEqual(decision.reason_code, "extension_unavailable_cdp_fallback_allowed")  # 新增代码+BrowserProviderRouter: 断言稳定 reason code 表示授权降级；若没有这行代码，外部 agent 只能解析自然语言。
        self.assertEqual(decision.metadata["fallback_from"], "chrome_extension")  # 新增代码+BrowserProviderRouter: 断言 metadata 记录降级来源；若没有这行代码，审计不知道原始目标 provider。

    def test_explicit_cdp_debug_request_uses_real_chrome_cdp(self) -> None:  # 新增代码+BrowserProviderRouter: 验证明确 CDP 调试请求走 CDP provider；若没有这行代码，调试任务可能被插件拦截。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，测试无法声明 CDP 可用。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导入路由器；若没有这行代码，无法执行 CDP 规则。
        router = BrowserProviderRouter()  # 新增代码+BrowserProviderRouter: 创建默认路由器；若没有这行代码，无法得到决策。
        health = {BrowserProviderKind.REAL_CHROME_CDP: BrowserProviderHealth.available(BrowserProviderKind.REAL_CHROME_CDP)}  # 新增代码+BrowserProviderRouter: 声明 CDP 可用；若没有这行代码，路由器会缺健康输入。
        decision = router.decide_provider(user_input="使用 CDP 调试端口连接真实 Chrome", tool_name="browser_connect_real_chrome", arguments={"confirm_real_profile": True}, provider_health=health)  # 新增代码+BrowserProviderRouter: 模拟显式 CDP 请求；若没有这行代码，CDP 规则无法验证。
        self.assertEqual(decision.provider, BrowserProviderKind.REAL_CHROME_CDP)  # 新增代码+BrowserProviderRouter: 断言显式 CDP 走 CDP provider；若没有这行代码，调试入口可能走错。

    def test_decision_payload_is_event_log_ready(self) -> None:  # 新增代码+BrowserProviderRouter: 验证决策能直接写 event log；若没有这行代码，状态生态无法复盘 provider 选择。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型和健康状态；若没有这行代码，测试无法构造路由输入。
        from learning_agent.browser.providers.router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导入被测路由器；若没有这行代码，无法生成事件 payload。
        router = BrowserProviderRouter()  # 新增代码+BrowserProviderRouter: 创建默认路由器；若没有这行代码，无法得到决策。
        health = {BrowserProviderKind.VISIBLE_CHROMIUM: BrowserProviderHealth.available(BrowserProviderKind.VISIBLE_CHROMIUM)}  # 新增代码+BrowserProviderRouter: 声明可见 Chromium 可用；若没有这行代码，路由器没有健康输入。
        decision = router.decide_provider(user_input="打开本地 localhost 页面", tool_name="browser_open", arguments={"url": "http://localhost:3000"}, provider_health=health)  # 新增代码+BrowserProviderRouter: 模拟本地开发任务；若没有这行代码，事件 payload 没有具体样本。
        payload = decision.to_event_payload()  # 新增代码+BrowserProviderRouter: 转换为事件 payload；若没有这行代码，无法验证 event log 格式。
        self.assertEqual(payload["provider"], "visible_chromium")  # 新增代码+BrowserProviderRouter: 断言 provider 使用稳定字符串；若没有这行代码，外部 agent 难以解析。
        self.assertEqual(payload["schema_version"], 1)  # 新增代码+BrowserProviderRouter: 断言事件 payload 有 schema 版本；若没有这行代码，未来协议变化无法兼容解析。
        self.assertEqual(payload["reason_code"], "visible_chromium_local_development")  # 新增代码+BrowserProviderRouter: 断言本地开发有稳定 reason code；若没有这行代码，外部 agent 只能读自然语言。
        self.assertEqual(payload["tool_name"], "browser_open")  # 新增代码+BrowserProviderRouter: 断言工具名进入事件；若没有这行代码，审计不知道哪个工具触发决策。
        self.assertIn("reason", payload)  # 新增代码+BrowserProviderRouter: 断言原因字段存在；若没有这行代码，用户无法理解 provider 选择。

    def test_decision_payload_sanitizes_non_json_metadata(self) -> None:  # 新增代码+BrowserProviderRouter: 验证事件 metadata 会被转成 JSON 安全值；若没有这行代码，JSONL 写入可能遇到不可序列化对象。
        from learning_agent.browser.providers.protocol import BrowserProviderDecision, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入决策对象和 provider 类型；若没有这行代码，测试无法构造特殊 metadata。
        decision = BrowserProviderDecision(provider=BrowserProviderKind.VISIBLE_CHROMIUM, reason="测试 metadata", tool_name="browser_open", metadata={"unsafe": object(), "nested": {"ok": True}})  # 新增代码+BrowserProviderRouter: 构造含不可 JSON 序列化对象的 metadata；若没有这行代码，脱敏转换没有压力样本。
        payload = decision.to_event_payload()  # 新增代码+BrowserProviderRouter: 生成事件 payload；若没有这行代码，无法检查 metadata。
        self.assertIsInstance(payload["metadata"]["unsafe"], str)  # 新增代码+BrowserProviderRouter: 断言不可序列化对象被转成字符串；若没有这行代码，JSONL 写入风险不会暴露。
        self.assertEqual(payload["metadata"]["nested"]["ok"], True)  # 新增代码+BrowserProviderRouter: 断言普通 JSON 值不被破坏；若没有这行代码，metadata 可能被过度字符串化。

    def test_provider_event_helper_matches_decision_payload(self) -> None:  # 新增代码+BrowserProviderRouter: 验证事件 helper 与决策对象序列化一致；若没有这行代码，后续接入可能出现两套 payload 格式。
        from learning_agent.browser.providers import build_provider_decision_event  # 新增代码+BrowserProviderRouter: 从 provider 包入口导入事件 helper；若没有这行代码，包入口导出不会被测试覆盖。
        from learning_agent.browser.providers.protocol import BrowserProviderDecision, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入决策对象和 provider 类型；若没有这行代码，测试无法构造 helper 输入。
        decision = BrowserProviderDecision(provider=BrowserProviderKind.VISIBLE_CHROMIUM, reason="公开网页", tool_name="browser_open", reason_code="visible_chromium_public_web")  # 新增代码+BrowserProviderRouter: 构造稳定 provider 决策；若没有这行代码，helper 没有输入。
        self.assertEqual(build_provider_decision_event(decision), decision.to_event_payload())  # 新增代码+BrowserProviderRouter: 断言 helper 复用决策 payload；若没有这行代码，helper 行为漂移不会报红。

    def test_provider_decision_event_type_is_registered(self) -> None:  # 新增代码+BrowserProviderRouter: 验证 provider 决策事件进入 runtime 事件集合；若没有这行代码，状态生态可能订阅不到该事件。
        from learning_agent.browser.runtime_events import BROWSER_PROVIDER_DECISION, BROWSER_RUNTIME_EVENT_TYPES  # 新增代码+BrowserProviderRouter: 导入事件常量和事件集合；若没有这行代码，测试无法覆盖协议注册。
        self.assertEqual(BROWSER_PROVIDER_DECISION, "browser_provider_decision")  # 新增代码+BrowserProviderRouter: 断言事件名稳定；若没有这行代码，外部 agent 解析会被改名破坏。
        self.assertIn(BROWSER_PROVIDER_DECISION, BROWSER_RUNTIME_EVENT_TYPES)  # 新增代码+BrowserProviderRouter: 断言事件集合包含 provider 决策；若没有这行代码，状态校验可能漏掉新事件。

    def test_registry_returns_unavailable_for_missing_provider(self) -> None:  # 新增代码+BrowserProviderRouter: 验证 registry 对未注册 provider 返回不可用；若没有这行代码，缺插件时可能被误判可用。
        from learning_agent.browser.providers.protocol import BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入 provider 类型；若没有这行代码，测试无法指定插件 provider。
        from learning_agent.browser.providers.registry import BrowserProviderRegistry  # 新增代码+BrowserProviderRouter: 导入 registry；若没有这行代码，测试无法覆盖健康查询。
        registry = BrowserProviderRegistry()  # 新增代码+BrowserProviderRouter: 创建空 registry；若没有这行代码，无法模拟 provider 尚未接入状态。
        health = registry.health(BrowserProviderKind.CHROME_EXTENSION)  # 新增代码+BrowserProviderRouter: 查询未注册插件 provider；若没有这行代码，无法验证缺省不可用。
        self.assertFalse(health.available)  # 新增代码+BrowserProviderRouter: 断言未注册 provider 不可用；若没有这行代码，路由器可能误选插件。
        self.assertIn("not_registered", health.reason)  # 新增代码+BrowserProviderRouter: 断言原因可审计；若没有这行代码，状态输出不可解释。

    def test_registry_set_health_and_all_health_returns_copy(self) -> None:  # 新增代码+BrowserProviderRouter: 验证 registry 写入和快照副本行为；若没有这行代码，未来 provider 健康接入关键路径未覆盖。
        from learning_agent.browser.providers.protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderRouter: 导入健康状态和 provider 类型；若没有这行代码，测试无法写入 registry。
        from learning_agent.browser.providers.registry import BrowserProviderRegistry  # 新增代码+BrowserProviderRouter: 导入 registry；若没有这行代码，测试无法覆盖注册行为。
        registry = BrowserProviderRegistry()  # 新增代码+BrowserProviderRouter: 创建空 registry；若没有这行代码，无法执行 set_health。
        registry.set_health(BrowserProviderHealth.available(BrowserProviderKind.VISIBLE_CHROMIUM, "ready"))  # 新增代码+BrowserProviderRouter: 写入可见 Chromium 健康状态；若没有这行代码，all_health 没有数据。
        snapshot = registry.all_health()  # 新增代码+BrowserProviderRouter: 读取健康状态快照；若没有这行代码，无法验证副本语义。
        snapshot.clear()  # 新增代码+BrowserProviderRouter: 修改返回快照模拟调用方误操作；若没有这行代码，无法证明内部状态不被污染。
        self.assertTrue(registry.health(BrowserProviderKind.VISIBLE_CHROMIUM).available)  # 新增代码+BrowserProviderRouter: 断言 registry 内部状态仍可用；若没有这行代码，副本保护失效不会报红。
