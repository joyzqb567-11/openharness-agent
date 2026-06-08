"""双轨浏览器 Stage 3 工具表面测试。"""  # 新增代码+BrowserToolSurfaceStage3: 说明本文件锁定模型单轨工具表面；若没有这行代码，维护者不知道这些测试保护什么架构边界。
from __future__ import annotations  # 新增代码+BrowserToolSurfaceStage3: 延迟解析类型注解；若没有这行代码，局部类型在旧解释顺序下更脆弱。

from learning_agent.tests.support import *  # 新增代码+BrowserToolSurfaceStage3: 复用项目测试基类、Path、tempfile 和 FakeMcpClient；若没有这行代码，测试会重复公共支撑代码。


class BrowserToolSurfaceStage3Tests(LearningAgentTestBase):  # 新增代码+BrowserToolSurfaceStage3: 定义 Stage 3 测试集合；若没有这个类，unittest 不会发现本阶段门禁。
    def test_browser_server_tools_do_not_expose_provider_specific_action_duplicates(self) -> None:  # 新增代码+BrowserToolSurfaceStage3: 验证 MCP server 不暴露 provider 专属重复动作；若没有这行代码，未来插件接入可能重新让模型选错轨道。
        from learning_agent.browser.providers.tool_surface import is_provider_specific_tool_name  # 新增代码+BrowserToolSurfaceStage3: 导入工具表面分类 helper；若没有这行代码，测试无法复用生产规则。
        from learning_agent.browser_automation_mcp_server import TOOLS  # 新增代码+BrowserToolSurfaceStage3: 读取真实 browser_automation 工具清单；若没有这行代码，测试只会检查假数据。
        tool_names = [str(tool.get("name", "")) for tool in TOOLS]  # 新增代码+BrowserToolSurfaceStage3: 收集所有 server 原始工具名；若没有这行代码，后续无法逐个检查。
        provider_specific_names = [tool_name for tool_name in tool_names if is_provider_specific_tool_name(tool_name)]  # 新增代码+BrowserToolSurfaceStage3: 筛出 provider 专属命名工具；若没有这行代码，重复动作不会被发现。
        self.assertEqual(provider_specific_names, [])  # 新增代码+BrowserToolSurfaceStage3: 断言 server 只暴露统一 browser_* 工具；若没有这行代码，错误工具名不会让测试失败。

    def test_tool_surface_helper_classifies_provider_control_tools(self) -> None:  # 新增代码+BrowserToolSurfaceStage3: 验证 helper 能区分普通动作和高级控制入口；若没有这行代码，真实 Chrome 控制工具边界会继续靠口头约定。
        from learning_agent.browser.providers.tool_surface import is_provider_control_tool_name, is_provider_specific_tool_name  # 新增代码+BrowserToolSurfaceStage3: 导入分类函数；若没有这行代码，测试无法驱动新 helper。
        self.assertFalse(is_provider_specific_tool_name("browser_open"))  # 新增代码+BrowserToolSurfaceStage3: 统一 browser_open 不是 provider 专属工具；若没有这行代码，普通打开可能被误隐藏。
        self.assertTrue(is_provider_specific_tool_name("chrome_extension_open"))  # 新增代码+BrowserToolSurfaceStage3: 插件专属 open 是禁止暴露的重复工具；若没有这行代码，未来同名能力可能混进模型工具池。
        self.assertTrue(is_provider_specific_tool_name("real_chrome_cdp_click"))  # 新增代码+BrowserToolSurfaceStage3: CDP 专属 click 是禁止暴露的重复工具；若没有这行代码，模型可能被迫在 click 轨道中二选一。
        self.assertTrue(is_provider_control_tool_name("browser_connect_real_chrome"))  # 新增代码+BrowserToolSurfaceStage3: 真实 Chrome 连接是高级 provider 控制入口；若没有这行代码，它会被误当普通页面动作。
        self.assertFalse(is_provider_control_tool_name("browser_click"))  # 新增代码+BrowserToolSurfaceStage3: 普通点击不是 provider 控制入口；若没有这行代码，动作工具和控制工具边界会混乱。

    def test_mcp_catalog_marks_real_chrome_controls_as_advanced_provider_control(self) -> None:  # 新增代码+BrowserToolSurfaceStage3: 验证 MCP catalog 给真实 Chrome 控制工具打高级标记；若没有这行代码，模型搜索时会误把控制入口当普通动作。
        fake_client = FakeMcpClient(tools=[  # 新增代码+BrowserToolSurfaceStage3: 构造 browser_automation fake server；若没有这行代码，测试会依赖真实 MCP 子进程。
            {"name": "browser_open", "description": "Open page", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},  # 新增代码+BrowserToolSurfaceStage3: 普通统一打开工具；若没有这行代码，缺少普通动作对照组。
            {"name": "browser_connect_real_chrome", "description": "Connect real Chrome", "inputSchema": {"type": "object", "properties": {"confirm_real_profile": {"type": "boolean"}}, "required": ["confirm_real_profile"]}},  # 新增代码+BrowserToolSurfaceStage3: 高级真实 Chrome 连接入口；若没有这行代码，provider-control 标记没有被测目标。
        ])  # 新增代码+BrowserToolSurfaceStage3: 结束 fake server 工具列表；若没有这行代码，FakeMcpClient 构造语法不完整。
        registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+BrowserToolSurfaceStage3: 创建 MCP 注册表；若没有这行代码，MCP 工具不会转换成 AgentTool。
        registry.start()  # 新增代码+BrowserToolSurfaceStage3: 启动 fake registry 并读取工具；若没有这行代码，agent_tools 会是空列表。
        tools_by_name = {tool.name: tool for tool in registry.agent_tools()}  # 新增代码+BrowserToolSurfaceStage3: 按模型工具名索引 AgentTool；若没有这行代码，后续断言难以定位目标。
        open_tool = tools_by_name["mcp__browser_automation__browser_open"]  # 新增代码+BrowserToolSurfaceStage3: 取普通 browser_open 工具；若没有这行代码，无法确认普通动作不带高级标记。
        connect_tool = tools_by_name["mcp__browser_automation__browser_connect_real_chrome"]  # 新增代码+BrowserToolSurfaceStage3: 取真实 Chrome 连接工具；若没有这行代码，无法检查控制入口元数据。
        self.assertIn("advanced", connect_tool.search_hint)  # 新增代码+BrowserToolSurfaceStage3: 断言连接工具搜索提示包含高级标记；若没有这行代码，模型搜索结果缺少风险提示。
        self.assertIn("provider-control", connect_tool.search_hint)  # 新增代码+BrowserToolSurfaceStage3: 断言连接工具搜索提示包含 provider-control；若没有这行代码，模型不知道这是轨道控制入口。
        self.assertNotIn("provider-control", open_tool.search_hint)  # 新增代码+BrowserToolSurfaceStage3: 断言普通打开不被误标为控制入口；若没有这行代码，普通网页动作可能被错误劝退。

    def test_mcp_catalog_does_not_export_provider_specific_duplicate_actions(self) -> None:  # 新增代码+BrowserToolSurfaceStage3: 验证未来插件/CDP 专属动作不会进入模型 catalog；若没有这行代码，外部 MCP server 一旦新增专属 open 就会污染工具池。
        fake_client = FakeMcpClient(tools=[  # 新增代码+BrowserToolSurfaceStage3: 构造含错误 provider 专属动作的 fake server；若没有这行代码，测试没有输入样本。
            {"name": "chrome_extension_open", "description": "Provider specific open", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}}},  # 新增代码+BrowserToolSurfaceStage3: 模拟插件专属 open；若没有这行代码，禁止暴露规则没有目标。
            {"name": "browser_open", "description": "Unified open", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},  # 新增代码+BrowserToolSurfaceStage3: 模拟统一 browser_open；若没有这行代码，无法证明过滤只拦专属重复动作。
        ])  # 新增代码+BrowserToolSurfaceStage3: 结束 fake 工具列表；若没有这行代码，FakeMcpClient 调用语法不完整。
        registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+BrowserToolSurfaceStage3: 创建 registry；若没有这行代码，fake 工具不会经过真实 catalog 包装。
        registry.start()  # 新增代码+BrowserToolSurfaceStage3: 启动 registry 并读取工具；若没有这行代码，agent_tools 为空。
        tool_names = [tool.name for tool in registry.agent_tools()]  # 新增代码+BrowserToolSurfaceStage3: 收集模型 catalog 工具名；若没有这行代码，无法断言过滤结果。
        self.assertIn("mcp__browser_automation__browser_open", tool_names)  # 新增代码+BrowserToolSurfaceStage3: 断言统一动作保留；若没有这行代码，过滤可能过度删除可用工具。
        self.assertNotIn("mcp__browser_automation__chrome_extension_open", tool_names)  # 新增代码+BrowserToolSurfaceStage3: 断言 provider 专属重复动作不进模型 catalog；若没有这行代码，模型会重新面对双轨选择。

    def test_skills_and_harness_tell_model_not_to_choose_provider(self) -> None:  # 新增代码+BrowserToolSurfaceStage3: 验证提示词层明确单轨原则；若没有这行代码，模型仍可能按文字理解去选择 provider。
        browser_skill = self._skill_file("browser_automation").read_text(encoding="utf-8")  # 新增代码+BrowserToolSurfaceStage3: 读取普通浏览器 skill；若没有这行代码，无法检查真实交付提示词。
        real_chrome_skill = self._skill_file("real_chrome").read_text(encoding="utf-8")  # 新增代码+BrowserToolSurfaceStage3: 读取真实 Chrome skill；若没有这行代码，无法检查高风险路线提示词。
        harness_text = (TEST_ROOT / "browser" / "harness.py").read_text(encoding="utf-8")  # 新增代码+BrowserToolSurfaceStage3: 读取 harness 源码文本；若没有这行代码，短 prompt 自动注入规则不会被测试覆盖。
        combined_text = "\n".join([browser_skill, real_chrome_skill, harness_text])  # 新增代码+BrowserToolSurfaceStage3: 合并三处提示词表面；若没有这行代码，断言需要重复写三遍。
        self.assertIn("BrowserProviderRouter", combined_text)  # 新增代码+BrowserToolSurfaceStage3: 断言提示词明确底层路由器名称；若没有这行代码，模型和维护者难以知道谁负责选轨道。
        self.assertIn("不要直接选择 provider", combined_text)  # 新增代码+BrowserToolSurfaceStage3: 断言提示词用人话禁止模型选 provider；若没有这行代码，双轨架构可能被 prompt 误导破坏。

    def test_provider_decision_event_remains_visible_after_unified_tool_call(self) -> None:  # 新增代码+BrowserToolSurfaceStage3: 验证统一工具调用后仍能审计 provider 决策；若没有这行代码，单轨表面会丢失底层选择证据。
        from learning_agent.browser.runtime_events import BROWSER_PROVIDER_DECISION  # 新增代码+BrowserToolSurfaceStage3: 导入 provider 决策事件常量；若没有这行代码，测试会写死字符串。
        from learning_agent.browser_automation_mcp_server import BrowserAutomationServer  # 新增代码+BrowserToolSurfaceStage3: 导入真实 server；若没有这行代码，无法覆盖生产调用入口。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserToolSurfaceStage3: 使用临时目录隔离 browser runtime store；若没有这行代码，测试会污染真实运行记录。
            server = BrowserAutomationServer(Path(raw_dir))  # 新增代码+BrowserToolSurfaceStage3: 创建真实 browser server；若没有这行代码，无法触发真实 provider 决策写入。
            server.browser_wait = lambda arguments: "browser_wait 成功\nstage3_unified_tool=true"  # 新增代码+BrowserToolSurfaceStage3: 替换等待实现避免测试睡眠；若没有这行代码，测试会慢且不稳定。
            result = server.call("browser_wait", {"milliseconds": 1})  # 新增代码+BrowserToolSurfaceStage3: 调用统一 browser_wait 工具；若没有这行代码，event log 不会产生。
            run_id = server.browser_runtime_store.list_run_ids()[-1]  # 新增代码+BrowserToolSurfaceStage3: 获取最新 browser run；若没有这行代码，无法读取事件流。
            events = server.browser_runtime_store.tail_events(run_id, limit=0)  # 新增代码+BrowserToolSurfaceStage3: 读取完整事件列表；若没有这行代码，无法检查 provider 决策事件。
        provider_events = [event for event in events if event["event_type"] == BROWSER_PROVIDER_DECISION]  # 新增代码+BrowserToolSurfaceStage3: 筛选 provider 决策事件；若没有这行代码，断言会混入其他事件。
        self.assertIn("stage3_unified_tool=true", result)  # 新增代码+BrowserToolSurfaceStage3: 断言统一工具结果正常返回；若没有这行代码，事件存在但工具输出损坏也会漏掉。
        self.assertTrue(provider_events)  # 新增代码+BrowserToolSurfaceStage3: 断言至少有一条 provider 决策事件；若没有这行代码，底层选择不可审计。
        self.assertEqual(provider_events[-1]["payload"]["provider"], "visible_chromium")  # 新增代码+BrowserToolSurfaceStage3: 断言普通统一工具默认走可见 Chromium；若没有这行代码，默认 provider 错误不会被发现。
