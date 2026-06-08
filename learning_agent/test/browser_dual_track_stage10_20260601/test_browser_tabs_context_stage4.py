"""双轨浏览器 Stage 4 标签页上下文合同测试。"""  # 新增代码+BrowserTabsContextStage4: 说明本文件锁定 browser_tabs_context 合同；若没有这行代码，维护者不知道测试保护的阶段边界。
from __future__ import annotations  # 新增代码+BrowserTabsContextStage4: 延迟解析类型注解；若没有这行代码，测试里的局部类型在旧解释顺序下更脆弱。

from learning_agent.tests.support import *  # 新增代码+BrowserTabsContextStage4: 复用项目测试基类、Path、tempfile 等公共支撑；若没有这行代码，测试会重复导入基础设施。


class FakeTabsContextPage:  # 新增代码+BrowserTabsContextStage4: 定义最小页面假对象；若没有这个类，单测会误启动真实浏览器。
    def __init__(self, url: str, title: str, closed: bool = False) -> None:  # 新增代码+BrowserTabsContextStage4: 初始化假页面 URL、标题和关闭状态；若没有这行代码，测试无法模拟 tab 摘要。
        self.url = url  # 新增代码+BrowserTabsContextStage4: 保存页面 URL；若没有这行代码，tabs_context 输出无法验证 URL。
        self._title = title  # 新增代码+BrowserTabsContextStage4: 保存页面标题；若没有这行代码，tabs_context 输出无法验证 title。
        self._closed = closed  # 新增代码+BrowserTabsContextStage4: 保存页面关闭状态；若没有这行代码，无法模拟失效标签页。
        self.bound_events: list[str] = []  # 新增代码+BrowserTabsContextStage4: 保存绑定过的事件名；若没有这行代码，假页面缺少 Playwright on() 兼容记录。

    def title(self) -> str:  # 新增代码+BrowserTabsContextStage4: 提供 Playwright Page.title() 兼容方法；若没有这行代码，server 同步标题会失败。
        return self._title  # 新增代码+BrowserTabsContextStage4: 返回假页面标题；若没有这行代码，测试无法断言标题输出。

    def is_closed(self) -> bool:  # 新增代码+BrowserTabsContextStage4: 提供 Playwright Page.is_closed() 兼容方法；若没有这行代码，server 清理失效页面会失败。
        return self._closed  # 新增代码+BrowserTabsContextStage4: 返回假页面关闭状态；若没有这行代码，测试无法控制页面是否可用。

    def on(self, event_name: str, callback: object) -> None:  # 新增代码+BrowserTabsContextStage4: 提供 Playwright Page.on() 兼容方法；若没有这行代码，页面登记测试会因缺方法失败。
        del callback  # 新增代码+BrowserTabsContextStage4: 明确测试不需要真实事件回调；若没有这行代码，未使用参数会干扰阅读。
        self.bound_events.append(event_name)  # 新增代码+BrowserTabsContextStage4: 记录事件名便于未来排查；若没有这行代码，假对象行为不可观察。


class BrowserTabsContextStage4Tests(LearningAgentTestBase):  # 新增代码+BrowserTabsContextStage4: 定义 Stage 4 测试集合；若没有这个类，unittest 不会发现这些合同测试。
    def _real_chrome_server_with_page(self, raw_dir: str, page_id: str = "page-1", title: str = "Example") -> object:  # 新增代码+BrowserTabsContextStage4: 创建带真实 Chrome session 状态的 server；若没有这行代码，多处测试会重复搭环境。
        from learning_agent.browser.session_manager import SESSION_MODE_REAL_CHROME  # 新增代码+BrowserTabsContextStage4: 导入真实 Chrome session 常量；若没有这行代码，测试会写散落字符串。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserTabsContextStage4: 导入真实 MCP server；若没有这行代码，测试不能覆盖生产入口。
        server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserTabsContextStage4: 用临时 workspace 创建 server；若没有这行代码，测试会污染真实项目 memory。
        server.session_mode = "real_chrome"  # 新增代码+BrowserTabsContextStage4: 模拟 server 已接入真实 Chrome；若没有这行代码，写动作门禁不会进入真实 Chrome 分支。
        server.session_manager.start_session(mode=SESSION_MODE_REAL_CHROME, visible=True, headless=False, session_id="stage4-session")  # 新增代码+BrowserTabsContextStage4: 启动稳定 session id；若没有这行代码，tabs_context 无法输出 session 和 tab 状态。
        page = FakeTabsContextPage("https://example.com/login", title)  # 新增代码+BrowserTabsContextStage4: 创建假登录页；若没有这行代码，server 没有页面可列。
        server.pages[page_id] = page  # 新增代码+BrowserTabsContextStage4: 把假页面放入 server 页面表；若没有这行代码，current_page 找不到 page_id。
        server.current_page_id = page_id  # 新增代码+BrowserTabsContextStage4: 设置当前页面；若没有这行代码，默认写动作目标不明确。
        server.session_manager.register_tab(url=page.url, title=title, active=True, page_key=page_id)  # 新增代码+BrowserTabsContextStage4: 把 page_id 映射到稳定 tab_id；若没有这行代码，tabs_context 输出缺少 tab_id/page_id 关系。
        return server  # 新增代码+BrowserTabsContextStage4: 返回准备好的 server；若没有这行代码，调用方拿不到被测对象。

    def test_browser_tabs_context_tool_is_public_and_provider_supported(self) -> None:  # 新增代码+BrowserTabsContextStage4: 验证工具清单和 provider 支持范围；若没有这行代码，模型可能看不到统一 tabs context。
        from learning_agent.browser.providers.real_chrome_cdp import REAL_CHROME_CDP_TOOLS  # 新增代码+BrowserTabsContextStage4: 导入 CDP provider 工具集合；若没有这行代码，无法检查真实 Chrome 轨道支持。
        from learning_agent.browser.providers.visible_chromium import VISIBLE_CHROMIUM_TOOLS  # 新增代码+BrowserTabsContextStage4: 导入可见 Chromium 工具集合；若没有这行代码，无法检查默认轨道支持。
        from learning_agent.browser_automation_mcp_server import TOOLS  # 新增代码+BrowserTabsContextStage4: 读取真实 MCP 工具清单；若没有这行代码，测试只会检查假数据。
        tool_names = [str(tool.get("name", "")) for tool in TOOLS]  # 新增代码+BrowserTabsContextStage4: 收集公开工具名；若没有这行代码，后续无法断言工具是否暴露。
        self.assertIn("browser_tabs_context", tool_names)  # 新增代码+BrowserTabsContextStage4: 断言模型能看到统一 tabs context；若没有这行代码，缺工具不会被发现。
        self.assertIn("browser_tabs_context", VISIBLE_CHROMIUM_TOOLS)  # 新增代码+BrowserTabsContextStage4: 断言可见 Chromium provider 支持只读 context；若没有这行代码，默认路由可能回退旁路。
        self.assertIn("browser_tabs_context", REAL_CHROME_CDP_TOOLS)  # 新增代码+BrowserTabsContextStage4: 断言真实 Chrome CDP provider 支持 context；若没有这行代码，登录态任务无法先读 tab。

    def test_browser_tabs_context_returns_session_tabs_with_page_ids(self) -> None:  # 新增代码+BrowserTabsContextStage4: 验证 context 输出包含可审计标签页字段；若没有这行代码，工具可能只是旧 browser_tabs list。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserTabsContextStage4: 使用临时 workspace 隔离 runtime store；若没有这行代码，测试会写入真实 memory。
            server = self._real_chrome_server_with_page(raw_dir)  # 新增代码+BrowserTabsContextStage4: 创建真实 Chrome 模式假页面 server；若没有这行代码，没有可列的 tab。
            result = server.call("browser_tabs_context", {})  # 新增代码+BrowserTabsContextStage4: 通过公开入口读取 tabs context；若没有这行代码，工具合同没有被触发。
        self.assertIn("browser_tabs_context 成功", result)  # 新增代码+BrowserTabsContextStage4: 断言返回明确成功标题；若没有这行代码，调用方难以识别工具结果。
        self.assertIn("session_id=stage4-session", result)  # 新增代码+BrowserTabsContextStage4: 断言输出 session id；若没有这行代码，无法判断 tab 属于哪次浏览器会话。
        self.assertIn("mode=real_chrome_cdp", result)  # 新增代码+BrowserTabsContextStage4: 断言输出 session mode；若没有这行代码，用户不知道是否处于真实 Chrome 轨道。
        self.assertIn("provider=real_chrome_cdp", result)  # 新增代码+BrowserTabsContextStage4: 断言输出 provider；若没有这行代码，其他 agent 无法判断底层轨道。
        self.assertIn("active_tab_id=stage4-session-tab-1", result)  # 新增代码+BrowserTabsContextStage4: 断言输出当前活动 tab id；若没有这行代码，默认操作目标不可审计。
        self.assertIn("tab_count=1", result)  # 新增代码+BrowserTabsContextStage4: 断言输出标签页数量；若没有这行代码，状态视图不完整。
        self.assertIn("page_id=page-1", result)  # 新增代码+BrowserTabsContextStage4: 断言输出 server page_id；若没有这行代码，后续工具无法把 tab 映射回 page。
        self.assertIn("tab_id=stage4-session-tab-1", result)  # 新增代码+BrowserTabsContextStage4: 断言输出稳定 tab id；若没有这行代码，跨 session 审计会混乱。
        self.assertIn("URL=https://example.com/login", result)  # 新增代码+BrowserTabsContextStage4: 断言输出 URL；若没有这行代码，用户不知道当前页在哪里。
        self.assertIn("title=Example", result)  # 新增代码+BrowserTabsContextStage4: 断言输出标题；若没有这行代码，tab 列表缺少人类可读线索。

    def test_real_chrome_write_requires_tabs_context_first(self) -> None:  # 新增代码+BrowserTabsContextStage4: 验证真实 Chrome 写动作会被 context 门禁拦住；若没有这行代码，agent 可能在未知标签页上误点。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserTabsContextStage4: 使用临时 workspace 隔离状态；若没有这行代码，测试会污染真实项目。
            server = self._real_chrome_server_with_page(raw_dir)  # 新增代码+BrowserTabsContextStage4: 创建真实 Chrome 模式 server；若没有这行代码，写动作门禁没有上下文。
            with self.assertRaisesRegex(RuntimeError, "browser_tabs_context"):  # 新增代码+BrowserTabsContextStage4: 期待错误直接提示先读 context；若没有这行代码，错误类型不受保护。
                server.call("browser_click", {"page_id": "page-1", "selector": "#login"})  # 新增代码+BrowserTabsContextStage4: 在未读 context 时尝试点击；若没有这行代码，门禁不会被验证。

    def test_real_chrome_write_is_allowed_after_tabs_context(self) -> None:  # 新增代码+BrowserTabsContextStage4: 验证读取 context 后真实 Chrome 写动作可继续执行；若没有这行代码，门禁可能只会永久阻断。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserTabsContextStage4: 使用临时 workspace 隔离状态；若没有这行代码，测试会污染真实项目。
            server = self._real_chrome_server_with_page(raw_dir)  # 新增代码+BrowserTabsContextStage4: 创建真实 Chrome 模式 server；若没有这行代码，没有 context 状态。
            server.browser_click = lambda arguments: "browser_click 成功\nstage4_allowed=true"  # 新增代码+BrowserTabsContextStage4: 用假点击避免真实浏览器动作；若没有这行代码，测试会依赖 Playwright 页面。
            server.call("browser_tabs_context", {})  # 新增代码+BrowserTabsContextStage4: 先读取 tab context 建立有效合同；若没有这行代码，后续写动作应被拦截。
        result = server.call("browser_click", {"page_id": "page-1", "selector": "#login", "allow_cdp_fallback": True})  # 修改代码+BrowserFallbackStage10: 读过 tabs context 后仍需显式允许 CDP 兜底再执行写动作；若没有这行代码，测试会保留旧的静默降级假设。
        self.assertIn("stage4_allowed=true", result)  # 新增代码+BrowserTabsContextStage4: 断言读取 context 后写动作可以通过；若没有这行代码，允许路径无测试保护。

    def test_tabs_context_invalidates_when_active_tab_changes(self) -> None:  # 新增代码+BrowserTabsContextStage4: 验证 active tab 改变后旧 context 失效；若没有这行代码，模型可能拿旧 tab 信息操作新页面。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserTabsContextStage4: 使用临时 workspace 隔离状态；若没有这行代码，测试会污染真实项目。
            server = self._real_chrome_server_with_page(raw_dir)  # 新增代码+BrowserTabsContextStage4: 创建带 page-1 的真实 Chrome 模式 server；若没有这行代码，初始 context 无 tab。
            server.browser_type = lambda arguments: "browser_type 成功\nstage4_type_allowed=true"  # 新增代码+BrowserTabsContextStage4: 用假输入避免真实浏览器动作；若没有这行代码，测试会依赖 fake page 输入能力。
            server.call("browser_tabs_context", {})  # 新增代码+BrowserTabsContextStage4: 读取 page-1 的 context；若没有这行代码，后续无法验证失效。
            second_page = FakeTabsContextPage("https://example.com/second", "Second")  # 新增代码+BrowserTabsContextStage4: 创建第二个假页面；若没有这行代码，active tab 无法变化。
            server.pages["page-2"] = second_page  # 新增代码+BrowserTabsContextStage4: 把第二页加入页面表；若没有这行代码，page-2 不存在。
            server.current_page_id = "page-2"  # 新增代码+BrowserTabsContextStage4: 切换当前页到第二页；若没有这行代码，默认写动作仍指向旧页。
            server.session_manager.register_tab(url=second_page.url, title="Second", active=True, page_key="page-2")  # 新增代码+BrowserTabsContextStage4: 同步第二页为 active tab；若没有这行代码，manager 仍认为 page-1 是活动页。
            with self.assertRaisesRegex(RuntimeError, "browser_tabs_context"):  # 新增代码+BrowserTabsContextStage4: 期待旧 context 因 active tab 变化而失效；若没有这行代码，危险复用不会失败。
                server.call("browser_type", {"page_id": "page-2", "selector": "#name", "text": "hello"})  # 新增代码+BrowserTabsContextStage4: 尝试在新 active tab 输入；若没有这行代码，失效门禁不会被触发。
