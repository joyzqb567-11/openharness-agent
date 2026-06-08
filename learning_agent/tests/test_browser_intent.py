"Real browser intent and customer-mode tests."  # Stage14: this file owns the browser_intent test group.
from __future__ import annotations  # Stage14: keep annotations lazy after test split.
import unittest  # Stage14: keep direct unittest execution available.
from learning_agent.tests.support import *  # Stage14: import shared helpers and dependencies for copied tests.

class BrowserIntentTests(LearningAgentTestBase):  # Stage14: unittest discovers this concrete modular test class.
    def test_natural_weather_travel_prompt_is_visible_browser_information_task(self) -> None:  # 新增代码+自然可见浏览器路由: 验证普通天气攻略查询也会进入可见浏览器路线；若没有这行代码，精准 prompt 可能继续只走后台搜索。
        from learning_agent.browser.intent import detect_visible_browser_information_task  # 新增代码+自然可见浏览器路由: 导入新增自然实时查询识别函数；若没有这行代码，测试无法锁定生产入口。
        prompt = "帮我查询3天后武汉的天气，并帮我做一下旅游攻略。"  # 新增代码+自然可见浏览器路由: 使用用户要求的精准 prompt；若没有这行代码，测试可能覆盖不到真实失败样本。
        self.assertTrue(detect_visible_browser_information_task(prompt))  # 新增代码+自然可见浏览器路由: 断言该 prompt 会触发可见浏览器 workflow；若没有这行代码，后台搜索回归不会失败。
    def test_natural_weather_travel_prompt_adds_visible_browser_harness_message(self) -> None:  # 新增代码+自然可见浏览器路由: 验证精准 prompt 会收到可见浏览器系统约束；若没有这行代码，模型可能不知道要启动可见窗口。
        workspace = self._project_root()  # 新增代码+自然可见浏览器路由: 使用真实项目根目录读取静态 prompt；若没有这行代码，测试不会覆盖交付路径。
        agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+自然可见浏览器路由: 创建最小 agent 构造初始 messages；若没有这行代码，harness 注入入口没有测试对象。
        prompt = "帮我查询3天后武汉的天气，并帮我做一下旅游攻略。"  # 新增代码+自然可见浏览器路由: 固定用户精准验收 prompt；若没有这行代码，测试无法证明当前痛点被覆盖。
        messages = agent._build_initial_messages(prompt)  # 新增代码+自然可见浏览器路由: 生成真实首轮消息；若没有这行代码，无法检查系统约束是否进入模型上下文。
        combined_content = "\n".join(str(message.get("content", "")) for message in messages)  # 新增代码+自然可见浏览器路由: 合并消息文本方便断言；若没有这行代码，system/user 消息位置变化会让测试脆弱。
        self.assertIn("Visible Browser Task Harness", combined_content)  # 新增代码+自然可见浏览器路由: 断言新增可见浏览器 harness 标题存在；若没有这行代码，缺注入不会失败。
        self.assertIn("browser_launch_visible", combined_content)  # 新增代码+自然可见浏览器路由: 断言 harness 明确要求启动可见浏览器；若没有这行代码，模型可能仍不打开窗口。
        self.assertIn("confirm_visible_browser=true", combined_content)  # 新增代码+自然可见浏览器路由: 断言启动可见窗口需要显式确认参数；若没有这行代码，模型可能少填关键安全参数。
        self.assertIn("不要用 web_search、fetch_url", combined_content)  # 新增代码+自然可见浏览器路由: 断言后台搜索不能替代真实可见浏览器；若没有这行代码，精准 prompt 失败会回归。
        self.assertIn("visible_browser=true", combined_content)  # 新增代码+自然可见浏览器路由: 断言最终验收需要可见窗口机器标记；若没有这行代码，controller 难以判断是否真的可见。
    def test_natural_weather_travel_prompt_preloads_visible_browser_launch_tool(self) -> None:  # 新增代码+自然可见浏览器路由: 验证模型第一轮实际能看到 browser_launch_visible；若没有这行代码，harness 有文案但工具池仍可能旁路失败。
        workspace = self._project_root()  # 新增代码+自然可见浏览器路由: 使用真实项目根目录初始化 agent；若没有这行代码，MCP 工具目录上下文不完整。
        fake_client = FakeMcpClient(tools=[{"name": "browser_profile_status", "description": "Status", "inputSchema": {"type": "object", "properties": {}}}, {"name": "browser_launch_visible", "description": "Launch visible browser", "inputSchema": {"type": "object", "properties": {"confirm_visible_browser": {"type": "boolean"}}, "required": ["confirm_visible_browser"]}}, {"name": "browser_open", "description": "Open page", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}, {"name": "browser_snapshot", "description": "Snapshot", "inputSchema": {"type": "object", "properties": {}}}], result_prefix="browser_result")  # 新增代码+自然可见浏览器路由: 构造最小浏览器 MCP 工具集合；若没有这行代码，测试无法观察首轮外部工具可见性。
        registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+自然可见浏览器路由: 用真实 browser_automation server 名触发生产能力包规则；若没有这行代码，MCP 工具不会归入浏览器包。
        model = RecordingToolNameFakeModel(ModelMessage(text="VISIBLE_BROWSER_TOOL_POOL_CHECK_DONE"))  # 新增代码+自然可见浏览器路由: 记录模型实际收到的工具名；若没有这行代码，只能猜工具池状态。
        agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry, debug_enabled=False)  # 新增代码+自然可见浏览器路由: 创建自动授权 agent；若没有这行代码，registry 不会启动并暴露 MCP 工具。
        list(agent.run_events("帮我查询3天后武汉的天气，并帮我做一下旅游攻略。", max_turns=1))  # 新增代码+自然可见浏览器路由: 运行一轮事件流触发真实初始工具池；若没有这行代码，假模型不会记录 tools 参数。
        self.assertTrue(model.received_tool_names)  # 新增代码+自然可见浏览器路由: 确认模型确实被调用；若没有这行代码，后续断言可能在空列表上误判。
        first_turn_tools = model.received_tool_names[0]  # 新增代码+自然可见浏览器路由: 取第一轮模型可见工具名；若没有这行代码，断言对象不清楚。
        self.assertIn("mcp__browser_automation__browser_launch_visible", first_turn_tools)  # 新增代码+自然可见浏览器路由: 断言可见浏览器启动工具首轮可见；若没有这行代码，精准 prompt 会继续无法主动打开窗口。
        self.assertIn("mcp__browser_automation__browser_open", first_turn_tools)  # 新增代码+自然可见浏览器路由: 断言打开网页工具也被预加载；若没有这行代码，启动窗口后下一步仍可能工具不可见。
    def test_explicit_real_chrome_prompt_does_not_become_visible_browser_query(self) -> None:  # 新增代码+自然可见浏览器路由: 防止登录态/真实 Chrome 请求被普通可见 Chromium 误替代；若没有这行代码，高风险 profile 路线可能被降级。
        from learning_agent.browser.intent import detect_visible_browser_information_task  # 新增代码+自然可见浏览器路由: 导入可见浏览器自然查询判断；若没有这行代码，无法锁定负向边界。
        prompt = "请使用真实浏览器和登录态，帮我查询我的订单状态。"  # 新增代码+自然可见浏览器路由: 构造明确真实 Chrome/profile 场景；若没有这行代码，测试无法保护登录态边界。
        self.assertFalse(detect_visible_browser_information_task(prompt))  # 新增代码+自然可见浏览器路由: 断言该场景不走普通可见 Chromium；若没有这行代码，隐私边界回归不会失败。
    def test_browser_intent_detects_real_browser_weather_task(self) -> None:  # 新增代码+BrowserSplit: 验证真实浏览器信息查询意图已从主文件迁移到 browser.intent；若没有这行代码，阶段 7 可能只移动文件不锁定可复用入口
        from learning_agent.browser.intent import detect_real_browser_information_task  # 新增代码+BrowserSplit: 从新 browser.intent 模块导入识别函数；若没有这行代码，测试无法证明浏览器意图有独立模块入口
        prompt = "请使用真实浏览器，帮我查询3天后重庆的天气，并帮我做一下旅游攻略。"  # 新增代码+BrowserSplit: 使用用户真实验收风格的自然短 prompt；若没有这行代码，测试可能只覆盖人工工具步骤 prompt 而漏掉客户场景
        self.assertTrue(detect_real_browser_information_task(prompt))  # 新增代码+BrowserSplit: 断言自然天气攻略查询会被识别为真实浏览器公开信息任务；若没有这行代码，后续客户模式自动授权可能失去触发条件
    def test_browser_permissions_auto_approve_public_google_workflow(self) -> None:  # 新增代码+BrowserSplit: 验证客户模式授权白名单已经迁入 browser.permissions；若没有这行代码，阶段 7 可能只拆意图不拆授权。
        from learning_agent.browser.permissions import DANGEROUS_SKIP_PERMISSIONS_ENV_VAR, real_browser_customer_auto_approve_reason  # 修改代码+DangerousDebugDefault: 同时导入危险模式环境变量名和自动授权判断；若没有这行代码，测试无法显式关闭默认危险模式来验证白名单逻辑。
        with mock.patch.dict(os.environ, {DANGEROUS_SKIP_PERMISSIONS_ENV_VAR: "0"}, clear=False):  # 新增代码+DangerousDebugDefault: 本测试专门验证安全白名单，所以显式关闭默认危险模式；若没有这行代码，默认危险模式会先接管授权原因。
            connect_reason = real_browser_customer_auto_approve_reason("mcp__browser_automation__browser_connect_real_chrome", {"confirm_real_profile": True}, customer_mode_active=True)  # 修改代码+DangerousDebugDefault: 验证真实 Chrome 连接在显式确认参数下可自动授权；若没有这行代码，用户仍可能在连接时被 y/N 打断。
            open_reason = real_browser_customer_auto_approve_reason("mcp__browser_automation__browser_open", {"url": "https://www.google.com/search?q=test"}, customer_mode_active=True)  # 修改代码+DangerousDebugDefault: 验证 Google 搜索 URL 在客户模式下可自动授权；若没有这行代码，公开查询第一步仍会弹权限。
            unsafe_reason = real_browser_customer_auto_approve_reason("mcp__browser_automation__browser_open", {"url": "https://example.com/private"}, customer_mode_active=True)  # 修改代码+DangerousDebugDefault: 验证非 Google URL 不被客户模式静默放行；若没有这行代码，白名单边界可能被放宽。
        self.assertIn("真实 Chrome", connect_reason)  # 修改代码+DangerousDebugDefault: 断言关闭危险模式后连接授权原因仍来自真实 Chrome 白名单；若没有这行代码，空原因或危险模式原因都可能误通过。
        self.assertIn("Google URL", open_reason)  # 修改代码+DangerousDebugDefault: 断言关闭危险模式后 Google URL 白名单原因可审计；若没有这行代码，测试无法区分固定白名单和 URL 白名单。
        self.assertEqual(unsafe_reason, "")  # 修改代码+DangerousDebugDefault: 断言关闭危险模式后未知 URL 仍需原权限流程；若没有这行代码，客户模式可能越界打开任意网站。
    def test_visible_browser_public_query_auto_approve_scope(self) -> None:  # 新增代码+自然可见浏览器路由: 验证普通可见浏览器查询的自动授权范围；若没有这行代码，真实验收可能再次被 y/N 焦点问题打断。
        from learning_agent.browser.permissions import DANGEROUS_SKIP_PERMISSIONS_ENV_VAR, visible_browser_customer_auto_approve_reason  # 修改代码+DangerousDebugDefault: 同时导入危险模式环境变量名和可见浏览器授权 helper；若没有这行代码，测试无法显式关闭默认危险模式。
        with mock.patch.dict(os.environ, {DANGEROUS_SKIP_PERMISSIONS_ENV_VAR: "0"}, clear=False):  # 新增代码+DangerousDebugDefault: 本测试专门验证可见浏览器安全白名单，所以关闭默认危险模式；若没有这行代码，危险模式会让所有原因都变成全局放行。
            launch_reason = visible_browser_customer_auto_approve_reason("mcp__browser_automation__browser_launch_visible", {"confirm_visible_browser": True}, customer_mode_active=True)  # 修改代码+DangerousDebugDefault: 验证显式确认后可自动启动可见窗口；若没有这行代码，精准 prompt 第一项工具仍会弹权限。
            open_reason = visible_browser_customer_auto_approve_reason("mcp__browser_automation__browser_open", {"url": "https://www.baidu.com/s?wd=武汉天气"}, customer_mode_active=True)  # 修改代码+DangerousDebugDefault: 验证 http(s) 公开网页可自动打开；若没有这行代码，实际天气搜索页会卡在权限。
            snapshot_reason = visible_browser_customer_auto_approve_reason("mcp__browser_automation__browser_snapshot", {"page_id": "page-1"}, customer_mode_active=True)  # 修改代码+DangerousDebugDefault: 验证公开页快照可自动读取；若没有这行代码，资料读取会反复弹权限。
            missing_confirm_reason = visible_browser_customer_auto_approve_reason("mcp__browser_automation__browser_launch_visible", {}, customer_mode_active=True)  # 修改代码+DangerousDebugDefault: 验证缺少可见确认时不自动放行；若没有这行代码，窗口启动安全边界会变弱。
            file_url_reason = visible_browser_customer_auto_approve_reason("mcp__browser_automation__browser_open", {"url": "file:///C:/secret.txt"}, customer_mode_active=True)  # 修改代码+DangerousDebugDefault: 验证本地文件 URL 不自动放行；若没有这行代码，公开查询可能越界到本地文件。
            evaluate_reason = visible_browser_customer_auto_approve_reason("mcp__browser_automation__browser_evaluate", {"script": "document.cookie"}, customer_mode_active=True)  # 修改代码+DangerousDebugDefault: 验证高风险脚本执行不自动放行；若没有这行代码，敏感读取可能被误允许。
            inactive_reason = visible_browser_customer_auto_approve_reason("mcp__browser_automation__browser_snapshot", {"page_id": "page-1"}, customer_mode_active=False)  # 修改代码+DangerousDebugDefault: 验证非自然查询模式不自动放行；若没有这行代码，普通浏览器工具权限会过宽。
        self.assertIn("独立 Chromium", launch_reason)  # 修改代码+DangerousDebugDefault: 断言关闭危险模式后启动授权原因来自可见浏览器白名单；若没有这行代码，空原因或危险模式原因都可能误通过。
        self.assertIn("公开网页", open_reason)  # 修改代码+DangerousDebugDefault: 断言关闭危险模式后网页打开授权原因明确；若没有这行代码，URL 边界不清楚。
        self.assertIn("白名单", snapshot_reason)  # 修改代码+DangerousDebugDefault: 断言关闭危险模式后快照工具命中白名单；若没有这行代码，自动授权原因不可读。
        self.assertEqual(missing_confirm_reason, "")  # 修改代码+DangerousDebugDefault: 断言关闭危险模式后缺确认不自动启动窗口；若没有这行代码，安全确认可能失效。
        self.assertEqual(file_url_reason, "")  # 修改代码+DangerousDebugDefault: 断言关闭危险模式后 file URL 不自动打开；若没有这行代码，本地文件边界可能被绕过。
        self.assertEqual(evaluate_reason, "")  # 修改代码+DangerousDebugDefault: 断言关闭危险模式后 evaluate 仍需人工授权；若没有这行代码，敏感脚本风险会扩大。
        self.assertEqual(inactive_reason, "")  # 修改代码+DangerousDebugDefault: 断言关闭危险模式后非客户模式不自动放行；若没有这行代码，权限模式会污染普通任务。
    def test_dangerously_skip_permissions_allows_any_mcp_tool_reason(self) -> None:  # 新增代码+危险调试权限: 验证危险模式会给任意 MCP 工具返回自动授权原因；若没有这行代码，全放开调试模式可能只放行真实浏览器白名单。
        from learning_agent.browser.permissions import dangerously_skip_permissions_enabled, real_browser_customer_auto_approve_reason  # 新增代码+危险调试权限: 导入危险开关和 MCP 自动授权入口；若没有这行代码，测试无法覆盖生产权限判断。
        with mock.patch.dict(os.environ, {"LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS": "1"}, clear=False):  # 新增代码+危险调试权限: 临时开启危险模式且不污染其他环境变量；若没有这行代码，测试会依赖开发者本机设置。
            self.assertTrue(dangerously_skip_permissions_enabled())  # 新增代码+危险调试权限: 断言环境变量被识别为开启；若没有这行代码，后续原因断言可能掩盖开关解析失败。
            reason = real_browser_customer_auto_approve_reason("mcp__browser_automation__browser_evaluate", {"script": "document.title"}, customer_mode_active=False)  # 新增代码+危险调试权限: 用非客户模式高风险工具验证全局放行；若没有这行代码，只能证明原白名单仍工作。
        self.assertIn("危险调试模式", reason)  # 新增代码+危险调试权限: 断言原因明确提示危险模式；若没有这行代码，日志可能让用户误以为普通安全白名单放行。
        self.assertIn("mcp__browser_automation__browser_evaluate", reason)  # 新增代码+危险调试权限: 断言原因包含具体工具名；若没有这行代码，审计时无法知道哪项权限被自动允许。
    def test_dangerously_skip_permissions_defaults_on_when_env_missing(self) -> None:  # 新增代码+DangerousDebugDefault: 函数段开始，验证调试开发阶段未设置环境变量也默认开启危险权限；若没有这段测试，controller 或非 ps1 入口可能继续保守卡权限而无人发现。
        from learning_agent.browser.permissions import DANGEROUS_SKIP_PERMISSIONS_ENV_VAR, dangerously_skip_permissions_enabled  # 新增代码+DangerousDebugDefault: 导入真实环境变量名和生产判断函数；若没有这行代码，测试会硬编码字符串且无法覆盖核心入口。
        with mock.patch.dict(os.environ, {}, clear=True):  # 新增代码+DangerousDebugDefault: 清空环境变量模拟非 start_oauth_agent.ps1 入口；若没有这行代码，测试会被开发机器已有设置污染。
            self.assertNotIn(DANGEROUS_SKIP_PERMISSIONS_ENV_VAR, os.environ)  # 新增代码+DangerousDebugDefault: 确认本次测试真的没有危险模式环境变量；若没有这行代码，红灯可能是假阳性。
            self.assertTrue(dangerously_skip_permissions_enabled())  # 新增代码+DangerousDebugDefault: 断言核心权限层默认开启危险调试；若没有这行代码，默认值回归保守不会被发现。
        # 新增代码+DangerousDebugDefault: 函数段结束，保证未设置环境变量时也走开发期默认放行；若没有这段结束注释，用户学习时不容易看出测试边界。
    def test_dangerously_skip_permissions_can_be_explicitly_disabled(self) -> None:  # 新增代码+DangerousDebugDefault: 函数段开始，验证未来正式产品或手动安全模式仍可关闭危险权限；若没有这段测试，默认开启后可能失去安全回退开关。
        from learning_agent.browser.permissions import DANGEROUS_SKIP_PERMISSIONS_ENV_VAR, dangerously_skip_permissions_enabled  # 新增代码+DangerousDebugDefault: 导入真实环境变量名和生产判断函数；若没有这行代码，测试无法锁定实际关闭入口。
        with mock.patch.dict(os.environ, {DANGEROUS_SKIP_PERMISSIONS_ENV_VAR: "0"}, clear=True):  # 新增代码+DangerousDebugDefault: 显式设置 0 模拟用户或正式产品关闭危险模式；若没有这行代码，测试无法证明关闭优先于默认开启。
            self.assertFalse(dangerously_skip_permissions_enabled())  # 新增代码+DangerousDebugDefault: 断言显式关闭仍然有效；若没有这行代码，默认开启会变成不可关闭的硬编码风险。
        # 新增代码+DangerousDebugDefault: 函数段结束，保证默认激进但仍保留清晰退出开关；若没有这段结束注释，用户不容易理解安全边界。
    def test_browser_artifacts_sanitizes_paths_inside_artifact_dir(self) -> None:  # 新增代码+BrowserSplit: 验证浏览器产物路径安全 helper 已迁入 browser.artifacts；若没有这行代码，截图路径清洗只能靠端到端测试发现问题。
        from learning_agent.browser.artifacts import safe_browser_artifact_path  # 新增代码+BrowserSplit: 从新 artifacts 模块导入路径 helper；若没有这行代码，测试无法证明产物路径逻辑有独立入口。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserSplit: 创建临时产物目录隔离测试文件；若没有这行代码，测试会污染真实 browser_artifacts。
            artifacts_dir = Path(raw_dir)  # 新增代码+BrowserSplit: 把临时目录转成 Path 供 helper 使用；若没有这行代码，后续 relative_to 检查不方便。
            target_path = safe_browser_artifact_path(artifacts_dir, r"..\\bad/name?.png", "fallback.png")  # 新增代码+BrowserSplit: 用带路径分隔符和特殊字符的文件名驱动清洗逻辑；若没有这行代码，越界文件名风险没有单测覆盖。
            target_path.relative_to(artifacts_dir.resolve())  # 新增代码+BrowserSplit: 断言生成路径仍在产物目录内；若没有这行代码，测试无法证明不会写到目录外。
            self.assertEqual(target_path.suffix, ".png")  # 新增代码+BrowserSplit: 断言清洗后仍保留截图扩展名；若没有这行代码，用户可能拿到没有图片扩展名的产物。
    def test_real_browser_automation_phrase_keeps_ordinary_browser_open_visible(self) -> None:  # 新增代码+真实浏览器误判: 验证“真实浏览器自动化测试”不等于真实 Chrome 登录态；若没有这行代码，普通 browser_open 会因为词义过宽被隐藏
        workspace = self._project_root()  # 新增代码+真实浏览器误判: 使用真实项目根目录读取 browser skill；若没有这行代码，测试不会覆盖交付路径
        fake_client = FakeMcpClient(tools=[{"name": "browser_open", "description": "Open a browser page", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}, {"name": "browser_snapshot", "description": "Snapshot", "inputSchema": {"type": "object", "properties": {}}}], result_prefix="browser_result")  # 新增代码+真实浏览器误判: 构造普通浏览器打开和快照工具；若没有这行代码，无法复现本次验收中 browser_open 被隐藏的问题
        registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+真实浏览器误判: 使用 browser_automation server 名触发 MCP 能力包映射；若没有这行代码，工具不会归入浏览器包
        agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry, debug_enabled=False)  # 新增代码+真实浏览器误判: 创建自动授权测试 agent；若没有这行代码，无法检查策略和工具池
        agent.real_chrome_requested = agent._detect_real_chrome_intent("Run a real browser automation acceptance test")  # 新增代码+真实浏览器误判: 用失败验收中的英文短语触发真实检测函数；若没有这行代码，测试无法覆盖真实入口语义
        self.assertFalse(agent.real_chrome_requested)  # 新增代码+真实浏览器误判: 断言普通真实浏览器自动化测试不应进入真实 Chrome profile workflow；若没有这行代码，检测词过宽不会失败
        agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/tool_list.md"}))  # 新增代码+真实浏览器误判: 先读动态提示词总索引；若没有这行代码，browser skill 会被层级门控拒绝
        agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/browser_automation/SKILL.md"}))  # 新增代码+真实浏览器误判: 读取普通浏览器 skill 触发工具包解锁；若没有这行代码，browser_open 不会进入候选工具池
        tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+真实浏览器误判: 读取解锁后的当前工具池；若没有这行代码，无法确认 browser_open 是否恢复可见
        self.assertIn("mcp__browser_automation__browser_open", tool_names)  # 新增代码+真实浏览器误判: 断言普通浏览器打开工具在该短语下仍可见；若没有这行代码，本次真实验收失败会回归
    def test_plain_real_browser_phrase_enters_real_chrome_workflow(self) -> None:  # 新增代码+通用真实浏览器Harness: 验证用户只说“真实浏览器”也会进入真实 Chrome/profile 路线；若没有这行代码，自然短 prompt 会继续被当成普通浏览器任务
        workspace = self._project_root()  # 新增代码+通用真实浏览器Harness: 使用真实项目根目录创建 agent；若没有这行代码，测试不会覆盖交付目录下的配置
        agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+通用真实浏览器Harness: 创建最小 agent 来调用真实意图检测函数；若没有这行代码，测试只能检查字符串而不是生产逻辑
        natural_prompt = "请使用真实浏览器，帮我查询3天后重庆的天气，并帮我做一下旅游攻略。"  # 新增代码+通用真实浏览器Harness: 固定用户最真实的短 prompt 样本；若没有这行代码，测试无法复现用户当前需求
        self.assertTrue(agent._detect_real_chrome_intent(natural_prompt))  # 新增代码+通用真实浏览器Harness: 断言“真实浏览器”触发真实 Chrome workflow；若没有这行代码，短 prompt 漏判不会失败
    def test_real_browser_youtube_video_question_is_customer_information_task(self) -> None:  # 新增代码+YouTube公开查询: 验证 YouTube 视频和评论排行这类公开查询也进入免多次 y 的客户模式；若没有这行代码，用户截图里的 YouTube 场景会继续回归
        workspace = self._project_root()  # 新增代码+YouTube公开查询: 使用真实项目根目录创建 agent；若没有这行代码，测试不会覆盖交付目录和真实提示词入口
        agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+YouTube公开查询: 创建最小 agent 来调用真实识别逻辑；若没有这行代码，测试只能停留在字符串猜测
        youtube_prompt = "请使用真实浏览器，youtube网站的视频关于ai agent介绍，评论最多的有哪些？"  # 新增代码+YouTube公开查询: 复现用户截图里的自然短 prompt；若没有这行代码，测试不能证明当前痛点已被覆盖
        self.assertTrue(agent._detect_real_chrome_intent(youtube_prompt))  # 新增代码+YouTube公开查询: 先确认“真实浏览器”仍触发真实 Chrome workflow；若没有这行代码，后续信息任务判断可能掩盖真实浏览器意图漏判
        self.assertTrue(agent._detect_real_browser_information_task(youtube_prompt))  # 新增代码+YouTube公开查询: 断言该公开资料查询会启用客户模式自动授权；若没有这行代码，browser_click/type/wait 等工具仍会逐步询问 y
    def test_real_browser_information_task_adds_compact_harness_message(self) -> None:  # 新增代码+通用真实浏览器Harness: 验证自然查询任务会收到通用真实浏览器搜索 harness；若没有这行代码，模型仍可能凭记忆或 API 直接回答
        workspace = self._project_root()  # 新增代码+通用真实浏览器Harness: 使用真实项目根目录读取生产静态提示词；若没有这行代码，测试无法覆盖实际首轮 messages
        agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+通用真实浏览器Harness: 创建最小 agent 以构造初始 messages；若没有这行代码，harness 注入入口没有测试对象
        natural_prompt = "请使用真实浏览器，帮我查询3天后重庆的天气，并帮我做一下旅游攻略。"  # 新增代码+通用真实浏览器Harness: 使用短 prompt 驱动 harness 判断；若没有这行代码，测试可能只覆盖人为长 prompt
        messages = agent._build_initial_messages(natural_prompt)  # 新增代码+通用真实浏览器Harness: 生成真实首轮模型 messages；若没有这行代码，无法确认 harness 是否真的进入模型上下文
        combined_content = "\n".join(str(message.get("content", "")) for message in messages)  # 新增代码+通用真实浏览器Harness: 合并所有 message 文本便于断言；若没有这行代码，新增 system 消息位置变化会让测试脆弱
        self.assertIn("Real Browser Task Harness", combined_content)  # 新增代码+通用真实浏览器Harness: 断言通用 harness 标题进入上下文；若没有这行代码，注入缺失不会失败
        self.assertIn("https://www.google.com/", combined_content)  # 新增代码+通用真实浏览器Harness: 断言默认从 Google 首页开始真实搜索；若没有这行代码，模型可能直接打开 API 或搜索结果 URL
        self.assertIn("browser_profile_status", combined_content)  # 新增代码+通用真实浏览器Harness: 断言 harness 要求先做 profile 状态检查；若没有这行代码，真实 profile 安全前置可能被跳过
        self.assertIn("browser_connect_real_chrome", combined_content)  # 新增代码+通用真实浏览器Harness: 断言 harness 要求连接真实 Chrome；若没有这行代码，普通 Chromium 可能继续冒充真实浏览器
        self.assertIn("browser_click", combined_content)  # 新增代码+通用真实浏览器Harness: 断言 harness 要求可见点击动作；若没有这行代码，用户看不到鼠标式交互
        self.assertIn("browser_type", combined_content)  # 新增代码+通用真实浏览器Harness: 断言 harness 要求可见输入动作；若没有这行代码，用户看不到拟人输入搜索词
        self.assertIn("browser_press_key", combined_content)  # 新增代码+通用真实浏览器Harness: 断言 harness 要求按 Enter 提交；若没有这行代码，搜索动作可能被直接 URL 替代
        self.assertIn("browser_screenshot", combined_content)  # 新增代码+通用真实浏览器Harness: 断言 harness 要求保存截图证据；若没有这行代码，真实浏览器动作缺少可复核证据
        self.assertIn("不要读取 cookies", combined_content)  # 新增代码+通用真实浏览器Harness: 断言 harness 保留真实 profile 隐私边界；若没有这行代码，登录态场景可能越界
        self.assertIn("会议、酒店、航班、资料", combined_content)  # 新增代码+通用真实浏览器Harness: 断言 harness 是通用查询能力而非重庆天气专用；若没有这行代码，后续会议酒店航班任务可能没有复用提示
        self.assertIn("real_chrome_connected=true", combined_content)  # 新增代码+通用真实浏览器Harness: 断言最终回答要包含机器可读连接标记；若没有这行代码，真实终端验收可能因中文摘要缺少标记而误判失败
        self.assertIn("browser_profile_status、browser_connect_real_chrome、browser_open、browser_click、browser_type、browser_press_key、browser_wait、browser_screenshot、browser_snapshot", combined_content)  # 新增代码+通用真实浏览器Harness: 断言最终回答要列出关键工具名；若没有这行代码，controller 无法从用户可见答案稳定核验真实动作


if __name__ == "__main__":  # Stage14: allow running this test module directly.
    unittest.main()  # Stage14: start unittest when executed as a script.


