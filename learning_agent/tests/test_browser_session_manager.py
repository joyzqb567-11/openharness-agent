"""浏览器 session manager 和 tab registry 测试。"""  # 新增代码+BrowserSessionManager: 说明本文件锁定 Stage 3 的 session/tab 生命周期边界；若没有这行代码，测试职责不清楚。

from __future__ import annotations  # 新增代码+BrowserSessionManager: 延迟解析类型注解；若没有这行代码，后续导入类型时更容易受顺序影响。

from learning_agent.tests.support import *  # 新增代码+BrowserSessionManager: 复用项目测试基类、临时目录和假对象；若没有这行代码，测试会重复公共准备。


class BrowserSessionManagerTests(LearningAgentTestBase):  # 新增代码+BrowserSessionManager: 定义 Stage 3 session manager 测试集合；若没有这个类，unittest 不会发现本组测试。
    def test_tab_registry_never_reuses_tab_ids_across_sessions(self) -> None:  # 新增代码+BrowserSessionManager: 验证 tab id 不能跨 session 重复；若没有这行代码，resume/replay 可能把旧 tab 当新 tab。
        from learning_agent.browser.session_manager import BrowserSessionManager  # 新增代码+BrowserSessionManager: 导入计划新增的 session manager；若没有这行代码，测试无法锁定公开 API。
        manager = BrowserSessionManager()  # 新增代码+BrowserSessionManager: 创建独立 session manager；若没有这行代码，后续无法模拟多会话。
        first_session = manager.start_session(mode="independent_chromium", visible=False, headless=True)  # 新增代码+BrowserSessionManager: 启动第一个独立 Chromium session；若没有这行代码，第一组 tab 没有归属。
        first_tab = manager.register_tab(url="https://example.com/first", title="First", active=True)  # 新增代码+BrowserSessionManager: 登记第一会话第一个 tab；若没有这行代码，无法得到第一 tab id。
        manager.end_session(reason="restart")  # 新增代码+BrowserSessionManager: 结束第一个 session 模拟浏览器重启；若没有这行代码，第二 session 可能复用同一个上下文。
        second_session = manager.start_session(mode="independent_chromium", visible=False, headless=True)  # 新增代码+BrowserSessionManager: 启动第二个独立 Chromium session；若没有这行代码，无法验证跨 session 不复用。
        second_tab = manager.register_tab(url="https://example.com/second", title="Second", active=True)  # 新增代码+BrowserSessionManager: 登记第二会话第一个 tab；若没有这行代码，无法比较 tab id。
        self.assertNotEqual(first_session.session_id, second_session.session_id)  # 新增代码+BrowserSessionManager: 断言 session id 不复用；若没有这行代码，两个浏览器生命周期会混淆。
        self.assertNotEqual(first_tab.tab_id, second_tab.tab_id)  # 新增代码+BrowserSessionManager: 断言 tab id 不跨 session 复用；若没有这行代码，旧 tab 事件可能污染新任务。
        self.assertTrue(first_tab.tab_id.startswith(first_session.session_id))  # 新增代码+BrowserSessionManager: 断言 tab id 带 session 前缀；若没有这行代码，审计时无法直接看出归属。
        self.assertTrue(second_tab.tab_id.startswith(second_session.session_id))  # 新增代码+BrowserSessionManager: 断言第二 tab 也带 session 前缀；若没有这行代码，新 session 归属不直观。

    def test_real_chrome_profile_summary_never_stores_full_user_data_path(self) -> None:  # 新增代码+BrowserSessionManager: 验证真实 Chrome profile 摘要不保存本机完整敏感路径；若没有这行代码，状态日志可能暴露用户目录。
        from learning_agent.browser.session_manager import BrowserSessionManager  # 新增代码+BrowserSessionManager: 导入 session manager；若没有这行代码，测试没有被测对象。
        manager = BrowserSessionManager()  # 新增代码+BrowserSessionManager: 创建 session manager；若没有这行代码，无法启动真实 Chrome 模式。
        manager.start_session(mode="real_chrome_cdp", visible=True, headless=False)  # 新增代码+BrowserSessionManager: 启动真实 Chrome CDP session；若没有这行代码，profile 摘要没有 session 可挂载。
        manager.record_real_chrome_profile(profile_directory="Default", profile_scope="debug_profile_fallback", user_data_dir="C:\\Users\\joyzq\\AppData\\Local\\Google\\Chrome\\User Data")  # 新增代码+BrowserSessionManager: 记录真实 Chrome profile 摘要并传入完整路径；若没有这行代码，无法验证路径脱敏。
        snapshot = manager.snapshot()  # 新增代码+BrowserSessionManager: 读取 session 状态快照；若没有这行代码，断言没有数据来源。
        self.assertEqual(snapshot["profile_summary"], "Default (debug_profile_fallback)")  # 新增代码+BrowserSessionManager: 断言只保存 profile 名和范围；若没有这行代码，用户目录可能进入状态生态。
        self.assertNotIn("joyzq", json.dumps(snapshot, ensure_ascii=False))  # 新增代码+BrowserSessionManager: 断言本机用户名不出现在快照；若没有这行代码，隐私路径泄露不会被发现。
        self.assertNotIn("User Data", json.dumps(snapshot, ensure_ascii=False))  # 新增代码+BrowserSessionManager: 断言 Chrome User Data 完整路径不出现在快照；若没有这行代码，敏感路径可能落盘。

    def test_session_health_report_includes_mode_visibility_and_tab_count(self) -> None:  # 新增代码+BrowserSessionManager: 验证健康报告包含状态生态需要的字段；若没有这行代码，CLI/API 无法稳定展示浏览器状态。
        from learning_agent.browser.session_manager import BrowserSessionManager  # 新增代码+BrowserSessionManager: 导入被测 session manager；若没有这行代码，测试无法运行。
        manager = BrowserSessionManager()  # 新增代码+BrowserSessionManager: 创建 manager；若没有这行代码，无法生成状态。
        manager.start_session(mode="visible_chromium", visible=True, headless=False)  # 新增代码+BrowserSessionManager: 启动可见 Chromium session；若没有这行代码，健康报告没有可见模式输入。
        active_tab = manager.register_tab(url="https://example.com/", title="Example", active=True)  # 新增代码+BrowserSessionManager: 登记当前活动 tab；若没有这行代码，tab_count 和 active_tab_id 无法验证。
        background_tab = manager.register_tab(url="https://openai.com/", title="OpenAI", active=False)  # 新增代码+BrowserSessionManager: 登记后台 tab；若没有这行代码，tab_count 只有 1 不足以验证多 tab。
        report = manager.health_report()  # 新增代码+BrowserSessionManager: 获取健康报告；若没有这行代码，状态断言没有对象。
        self.assertEqual(report["mode"], "visible_chromium")  # 新增代码+BrowserSessionManager: 断言报告包含 session mode；若没有这行代码，状态页无法区分浏览器后端。
        self.assertTrue(report["connected"])  # 新增代码+BrowserSessionManager: 断言启动 session 后 connected 为真；若没有这行代码，状态页无法判断可用性。
        self.assertTrue(report["visible"])  # 新增代码+BrowserSessionManager: 断言可见模式为真；若没有这行代码，肉眼验收状态不可见。
        self.assertFalse(report["headless"])  # 新增代码+BrowserSessionManager: 断言 headless 为假；若没有这行代码，状态无法证明不是无头浏览器。
        self.assertEqual(report["tab_count"], 2)  # 新增代码+BrowserSessionManager: 断言多 tab 数量准确；若没有这行代码，多页面状态不可审计。
        self.assertEqual(report["active_tab_id"], active_tab.tab_id)  # 新增代码+BrowserSessionManager: 断言活动 tab id 稳定；若没有这行代码，默认操作目标不清楚。
        self.assertIn(background_tab.tab_id, report["tab_ids"])  # 新增代码+BrowserSessionManager: 断言后台 tab 也进入报告；若没有这行代码，状态页会漏掉后台页面。

    def test_browser_plugin_status_reports_session_manager_fields(self) -> None:  # 新增代码+BrowserSessionManager: 验证现有 browser_plugin_status 能输出 session manager 字段；若没有这行代码，新 manager 可能没有接入真实工具状态。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserSessionManager: 导入真实浏览器 MCP server；若没有这行代码，测试无法覆盖生产状态工具。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserSessionManager: 使用临时 workspace 隔离 server 状态；若没有这行代码，测试会污染真实项目。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserSessionManager: 创建真实 server 实例；若没有这行代码，无法调用 browser_plugin_status。
            server.session_manager.start_session(mode="visible_chromium", visible=True, headless=False)  # 新增代码+BrowserSessionManager: 用新 manager 模拟可见浏览器 session；若没有这行代码，状态工具没有 session 数据。
            server.session_manager.register_tab(url="https://example.com/", title="Example", active=True)  # 新增代码+BrowserSessionManager: 给 session 加一个 tab；若没有这行代码，tab_count 仍是 0。
            status = server.call("browser_plugin_status", {})  # 新增代码+BrowserSessionManager: 通过公开工具入口读取状态；若没有这行代码，测试只覆盖内部方法不覆盖 MCP 调用。
        self.assertIn("session_mode=visible_chromium", status)  # 新增代码+BrowserSessionManager: 断言状态输出 session mode；若没有这行代码，UI/SDK 无法区分模式。
        self.assertIn("connected=true", status)  # 新增代码+BrowserSessionManager: 断言状态输出 connected；若没有这行代码，外部 agent 不知道浏览器是否可用。
        self.assertIn("visible=true", status)  # 新增代码+BrowserSessionManager: 断言状态输出 visible；若没有这行代码，肉眼可见验收状态不明确。
        self.assertIn("headless=false", status)  # 新增代码+BrowserSessionManager: 断言状态输出 headless；若没有这行代码，状态无法证明窗口模式。
        self.assertIn("tab_count=1", status)  # 新增代码+BrowserSessionManager: 断言状态输出 tab count；若没有这行代码，多页面状态不可见。
