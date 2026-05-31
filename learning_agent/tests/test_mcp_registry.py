"MCP config, registry, transport, and resource tests."  # Stage14: this file owns the mcp_registry test group.
from __future__ import annotations  # Stage14: keep annotations lazy after test split.
import unittest  # Stage14: keep direct unittest execution available.
from learning_agent.tests.support import *  # Stage14: import shared helpers and dependencies for copied tests.

class McpRegistryTests(LearningAgentTestBase):  # Stage14: unittest discovers this concrete modular test class.
    def test_mcp_package_exports_config_and_registry(self) -> None:  # 新增代码+McpSplit: 验证 MCP 配置和 registry 已迁移到 mcp 包；若没有这行代码，MCP 层可能继续堆在主文件里没人发现。
        from learning_agent.mcp.config import McpServerConfig as McpPackageServerConfig  # 新增代码+McpSplit: 直接导入 MCP 配置模块；若没有这行代码，mcp_servers.json 解析边界无法被测试锁住。
        from learning_agent.mcp.registry import McpToolRegistry as McpPackageToolRegistry  # 新增代码+McpSplit: 直接导入 MCP registry 模块；若没有这行代码，工具发现和路由边界无法被测试锁住。
        self.assertIsNotNone(McpPackageServerConfig)  # 新增代码+McpSplit: 断言配置类型存在；若没有这行代码，空模块也可能被误认为通过。
        self.assertIsNotNone(McpPackageToolRegistry)  # 新增代码+McpSplit: 断言 registry 类型存在；若没有这行代码，registry 导出缺失不会有清晰失败点。
        self.assertIs(McpServerConfig, McpPackageServerConfig)  # 新增代码+McpSplit: 断言旧入口仍重导出同一个配置类；若没有这行代码，旧测试和新模块可能分裂。
        self.assertIs(McpToolRegistry, McpPackageToolRegistry)  # 新增代码+McpSplit: 断言旧入口仍重导出同一个 registry 类；若没有这行代码，MCP 调用方可能拿到重复类型。
    def test_customer_permission_auto_approves_mcp_start_without_input(self) -> None:  # 新增代码+真实浏览器客户模式: 验证客户模式启动本项目 MCP 时不会再打断用户输入 y；若没有这行代码，截图里的第一个授权提示可能回归
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+真实浏览器客户模式: 创建临时目录保存验收事件；若没有这行代码，测试会污染真实验收输出
            event_log_path = Path(raw_dir) / "events.jsonl"  # 新增代码+真实浏览器客户模式: 指定本测试事件日志路径；若没有这行代码，后续无法确认自动授权事件
            with mock.patch.dict(os.environ, {ACCEPTANCE_EVENT_ENV_VAR: str(event_log_path)}, clear=False):  # 新增代码+真实浏览器客户模式: 临时启用验收事件日志；若没有这行代码，自动授权缺少可审计事件
                with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:  # 新增代码+真实浏览器客户模式: 捕获终端进度文本；若没有这行代码，测试无法验证用户看到的是进度而不是 y/N
                    with mock.patch("builtins.input", side_effect=AssertionError("客户模式不应调用 input")) as fake_input:  # 新增代码+真实浏览器客户模式: 如果代码仍调用 input 就让测试失败；若没有这行代码，回归会被静默放过
                        allowed = ask_permission_from_terminal_customer_mode("启动 MCP server：browser_search, workspace_tools, browser_automation")  # 新增代码+真实浏览器客户模式: 调用客户模式权限入口；若没有这行代码，无法覆盖真实 main() 要使用的新入口
            self.assertTrue(allowed)  # 新增代码+真实浏览器客户模式: 断言本项目 MCP 启动默认允许；若没有这行代码，客户模式仍可能卡在启动授权
            fake_input.assert_not_called()  # 新增代码+真实浏览器客户模式: 断言不再要求用户输入 y；若没有这行代码，多余输入框可能重新出现
            self.assertIn("正在启动 MCP 工具", fake_stdout.getvalue())  # 新增代码+真实浏览器客户模式: 断言终端显示进度提示；若没有这行代码，用户可能看不到 agent 正在做什么
            events = self._read_acceptance_events(event_log_path)  # 新增代码+真实浏览器客户模式: 读取自动授权事件；若没有这行代码，后续无法确认协议状态
            self.assertEqual([event["state"] for event in events], ["permission_auto_approved"])  # 新增代码+真实浏览器客户模式: 断言自动授权不会产生 permission_required；若没有这行代码，控制器仍可能输入 y
            self.assertEqual(events[0]["payload"]["permission_kind"], "mcp_server_start")  # 新增代码+真实浏览器客户模式: 断言自动授权对象是 MCP 启动；若没有这行代码，审计无法区分启动和工具调用
            self.assertTrue(events[0]["payload"]["allowed"])  # 新增代码+真实浏览器客户模式: 断言事件记录允许结果；若没有这行代码，result 复盘时不知道是否真的放行
    def test_terminal_permission_emits_structured_mcp_tool_payload(self) -> None:  # 新增代码+StructuredPermissionLedger: 验证 MCP 工具权限事件带结构化工具名和参数；若没有这行代码，controller 只能继续靠文本 contains 猜权限
        action = "\n".join([  # 新增代码+StructuredPermissionLedger: 构造真实 MCP 权限提示文本；若没有这行代码，测试无法覆盖生产格式解析
            "调用 MCP 工具：mcp__browser_automation__browser_open",  # 新增代码+StructuredPermissionLedger: 第一行提供 MCP 工具名；若没有这行代码，解析器没有 tool_name 输入
            "风险等级：浏览器自动化中风险",  # 新增代码+StructuredPermissionLedger: 第二行提供风险等级；若没有这行代码，事件无法给 controller 和用户展示风险级别
            "风险说明：会打开网页、等待页面变化或保存截图；确认前请重点核对 url、page_id、filename。",  # 新增代码+StructuredPermissionLedger: 第三行提供风险说明；若没有这行代码，事件缺少可审计风险摘要
            '参数：{"url":"https://api.open-meteo.com/v1/forecast?start_date=2026-05-31","new_tab":true}',  # 新增代码+StructuredPermissionLedger: 参数行提供 JSON 参数；若没有这行代码，URL 前缀白名单无法被结构化验证
        ])  # 新增代码+StructuredPermissionLedger: 结束权限提示文本数组；若没有这行代码，Python 语法不完整
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+StructuredPermissionLedger: 创建临时目录保存事件日志；若没有这行代码，测试会污染真实验收证据
            event_log_path = Path(raw_dir) / "events.jsonl"  # 新增代码+StructuredPermissionLedger: 指定本测试事件日志路径；若没有这行代码，后续无法读取事件
            with mock.patch.dict(os.environ, {ACCEPTANCE_EVENT_ENV_VAR: str(event_log_path)}, clear=False):  # 新增代码+StructuredPermissionLedger: 临时启用验收事件；若没有这行代码，权限函数不会写 JSONL
                with mock.patch("sys.stdout", new=io.StringIO()):  # 新增代码+StructuredPermissionLedger: 收起终端标记避免污染单测输出；若没有这行代码，测试输出会混入机器事件行
                    with mock.patch("builtins.input", return_value="y"):  # 新增代码+StructuredPermissionLedger: 模拟用户同意权限；若没有这行代码，单元测试会卡住等待输入
                        allowed = ask_permission_from_terminal(action)  # 新增代码+StructuredPermissionLedger: 调用真实终端权限入口；若没有这行代码，结构化事件不会从生产路径生成
            self.assertTrue(allowed)  # 新增代码+StructuredPermissionLedger: 断言 y 仍然保持允许语义；若没有这行代码，改造可能破坏原有权限行为
            events = self._read_acceptance_events(event_log_path)  # 新增代码+StructuredPermissionLedger: 读取刚生成的事件；若没有这行代码，后续无法断言 payload 结构
            required_payload = events[0]["payload"]  # 新增代码+StructuredPermissionLedger: 取出待授权事件 payload；若没有这行代码，断言会重复索引难以阅读
            answered_payload = events[1]["payload"]  # 新增代码+StructuredPermissionLedger: 取出已回答事件 payload；若没有这行代码，无法确认回答事件也保留审计字段
            self.assertEqual(required_payload["permission_kind"], "mcp_tool")  # 新增代码+StructuredPermissionLedger: 断言事件明确标记为 MCP 工具权限；若没有这行代码，controller 无法区分启动 server 和工具调用
            self.assertEqual(required_payload["tool_name"], "mcp__browser_automation__browser_open")  # 新增代码+StructuredPermissionLedger: 断言工具名被结构化提取；若没有这行代码，精确工具白名单无法实现
            self.assertEqual(required_payload["risk_level"], "浏览器自动化中风险")  # 新增代码+StructuredPermissionLedger: 断言风险等级被保留；若没有这行代码，审计报告缺少风险分类
            self.assertIn("打开网页", required_payload["risk_summary"])  # 新增代码+StructuredPermissionLedger: 断言风险说明被保留；若没有这行代码，用户无法复盘为什么这是中风险操作
            self.assertEqual(required_payload["arguments"]["url"], "https://api.open-meteo.com/v1/forecast?start_date=2026-05-31")  # 新增代码+StructuredPermissionLedger: 断言 URL 参数被 JSON 解析；若没有这行代码，URL 前缀白名单只能继续看 action 字符串
            self.assertTrue(required_payload["arguments"]["new_tab"])  # 新增代码+StructuredPermissionLedger: 断言布尔参数类型被保留；若没有这行代码，参数审计会退化成不可靠文本
            self.assertEqual(answered_payload["tool_name"], required_payload["tool_name"])  # 新增代码+StructuredPermissionLedger: 断言已回答事件也带工具名；若没有这行代码，result 审计无法把 y/n 对应到具体工具
            self.assertTrue(answered_payload["allowed"])  # 新增代码+StructuredPermissionLedger: 断言已回答事件仍记录允许结果；若没有这行代码，controller 无法确认 y 是否生效
    def test_reading_browser_skill_loads_browser_automation_mcp_tools(self) -> None:  # 新增代码+浏览器自动化: 验证读取浏览器 skill 后真实 MCP 浏览器工具进入当前工具池；若没有这行代码，四原子架构可能只会读提示词却无法真正自动化浏览器
        workspace = self._project_root()  # 新增代码+浏览器自动化: 使用真实项目根目录读取包内 browser_automation skill；若没有这行代码，测试不能覆盖用户实际会用到的 skill 文件
        fake_client = FakeMcpClient(tools=[{"name": "browser_open", "description": "Open a browser page", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}], result_prefix="browser_result")  # 新增代码+浏览器自动化: 构造只暴露 browser_open 的假 MCP server；若没有这行代码，测试会依赖真实浏览器进程而不稳定
        registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+浏览器自动化: 使用真实 browser_automation server 名触发能力包映射；若没有这行代码，工具不会归入浏览器自动化能力包
        agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry, debug_enabled=False)  # 新增代码+浏览器自动化: 创建自动授权且关闭调试落盘的测试 agent；若没有这行代码，无法检查 read-based 解锁链路
        initial_tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+浏览器自动化: 读取首轮模型可见工具名；若没有这行代码，无法证明浏览器工具不是默认塞进上下文
        self.assertNotIn("mcp__browser_automation__browser_open", initial_tool_names)  # 新增代码+浏览器自动化: 断言 browser_open 首轮隐藏；若没有这行代码，极简工具面被破坏也不会失败
        self.assertNotIn("tool_search", initial_tool_names)  # 新增代码+浏览器自动化: 断言首轮仍不暴露旧 tool_search 路由；若没有这行代码，修复可能退回旧架构
        tool_list_output = agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/tool_list.md"}))  # 新增代码+浏览器自动化: 先按动态提示词第一层读取工具索引；若没有这行代码，第二层 skill 会被层级门控拦住
        self.assertIn("browser_automation/SKILL.md", tool_list_output)  # 新增代码+浏览器自动化: 断言总索引确实指向浏览器 skill；若没有这行代码，后续读取可能不是按真实索引发现
        skill_output = agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/browser_automation/SKILL.md"}))  # 新增代码+浏览器自动化: 读取第二层普通浏览器 skill；若没有这行代码，read-based 工具解锁不会触发
        self.assertIn("ordinary_browser.md", skill_output)  # 新增代码+浏览器自动化: 断言浏览器 skill 读取成功并指向第三层规则；若没有这行代码，测试可能误把错误文本当成功
        loaded_tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+浏览器自动化: 读取 skill 后的当前工具池；若没有这行代码，无法确认 schema 是否真的变更
        self.assertIn("mcp__browser_automation__browser_open", loaded_tool_names)  # 新增代码+浏览器自动化: 断言 browser_open 已进入当前工具池；若没有这行代码，read skill 后仍不能操作浏览器的问题不会暴露
        self.assertNotIn("tool_search", loaded_tool_names)  # 新增代码+浏览器自动化: 再次确认解锁浏览器不需要恢复旧 tool_search；若没有这行代码，工具面可能被顺手放大
        open_output = agent._execute_tool(ToolCall(name="mcp__browser_automation__browser_open", arguments={"url": "data:text/html,<title>ok</title>"}))  # 新增代码+浏览器自动化: 直接调用刚解锁的 MCP 浏览器工具；若没有这行代码，只检查可见性会漏掉执行层仍阻断的问题
        self.assertIn("browser_result browser_open", open_output)  # 新增代码+浏览器自动化: 断言调用结果来自 fake browser_open；若没有这行代码，执行可能路由到错误工具或失败文本
        self.assertEqual(fake_client.calls[-1][0], "browser_open")  # 新增代码+浏览器自动化: 断言 MCP 前缀被正确剥离成原始工具名；若没有这行代码，真实 server 可能收到错误名称
    def test_mcp_registry_exposes_agent_tools_as_deferred_catalog_entries(self) -> None:  # 新增代码+ToolArchitectureV2: 验证 MCP registry 能把已发现工具包装成延迟加载的 AgentTool；若没有这行代码，MCP 工具目录化回归不会被测试发现
        fake_client = FakeMcpClient(tools=[  # 新增代码+ToolArchitectureV2: 创建只暴露天气查询工具的 fake MCP client；若没有这行代码，测试没有可控 MCP 工具来源
            {  # 新增代码+ToolArchitectureV2: 定义一个 MCP tools/list 返回的工具条目；若没有这行代码，registry 无法发现 weather_lookup
                "name": "weather_lookup",  # 新增代码+ToolArchitectureV2: 声明 MCP 原始工具名；若没有这行代码，无法验证 original_name 是否被保留
                "description": "Search weather",  # 新增代码+ToolArchitectureV2: 提供工具说明；若没有这行代码，AgentTool 的 description 可能丢失而测试不报警
                "inputSchema": {  # 新增代码+ToolArchitectureV2: 提供 MCP 原始参数 schema；若没有这行代码，无法验证 query 和 required 是否透传
                    "type": "object",  # 新增代码+ToolArchitectureV2: 声明参数是对象；若没有这行代码，模型参数结构约束会不完整
                    "properties": {  # 新增代码+ToolArchitectureV2: 声明可用参数字段集合；若没有这行代码，query 参数无法出现在 AgentTool input_schema 中
                        "query": {"type": "string"},  # 新增代码+ToolArchitectureV2: 声明天气查询文本参数；若没有这行代码，模型不知道要传 query
                    },  # 新增代码+ToolArchitectureV2: 结束 properties 字典；若没有这行代码，测试工具 schema 语法不完整
                    "required": ["query"],  # 新增代码+ToolArchitectureV2: 声明 query 必填；若没有这行代码，必填约束丢失不会被测试发现
                },  # 新增代码+ToolArchitectureV2: 结束 inputSchema 字典；若没有这行代码，MCP 参数 schema 无法闭合
            }  # 新增代码+ToolArchitectureV2: 结束 weather_lookup 工具条目；若没有这行代码，工具列表元素语法不完整
        ])  # 新增代码+ToolArchitectureV2: 结束 fake client 构造；若没有这行代码，后续 registry 没有可启动的 client
        registry = McpToolRegistry({"weather": fake_client})  # 新增代码+ToolArchitectureV2: 用 weather server 名创建 registry；若没有这行代码，无法验证 server_name 元数据
        registry.start()  # 新增代码+ToolArchitectureV2: 启动 registry 并缓存 MCP 工具 schema；若没有这行代码，agent_tools 没有已发现工具可包装
        agent_tools = registry.agent_tools()  # 新增代码+ToolArchitectureV2: 读取 MCP 工具的 AgentTool 目录条目；若没有这行代码，测试无法验证新入口
        self.assertEqual(len(agent_tools), 1)  # 新增代码+ToolArchitectureV2: 断言只暴露一个目录条目；若没有这行代码，重复或遗漏 MCP 工具不会被发现
        tool = agent_tools[0]  # 新增代码+ToolArchitectureV2: 取出唯一 AgentTool 方便逐项断言；若没有这行代码，后续断言会重复索引难读且易错
        self.assertEqual(tool.name, "mcp__weather__weather_lookup")  # 新增代码+ToolArchitectureV2: 断言工具名包含 MCP 前缀和 server 名；若没有这行代码，命名路由回归不会暴露
        self.assertEqual(tool.source, "mcp")  # 新增代码+ToolArchitectureV2: 断言来源标记为 MCP；若没有这行代码，权限和展示层可能把外部工具误当内置工具
        self.assertEqual(tool.server_name, "weather")  # 新增代码+ToolArchitectureV2: 断言保留 server_name；若没有这行代码，目录层无法追踪工具来自哪个 MCP server
        self.assertEqual(tool.original_name, "weather_lookup")  # 新增代码+ToolArchitectureV2: 断言保留 MCP 原始工具名；若没有这行代码，调试和审计会丢失外部原名
        self.assertTrue(tool.should_defer)  # 新增代码+ToolArchitectureV2: 断言 MCP 工具默认延迟加载；若没有这行代码，大量外部工具可能默认挤进首轮上下文
        self.assertFalse(tool.always_load)  # 新增代码+ToolArchitectureV2: 断言 MCP 工具默认不会强制首轮加载；若没有这行代码，always_load 回归会让外部工具重新默认暴露
        self.assertIn("query", tool.input_schema["properties"])  # 新增代码+ToolArchitectureV2: 断言 input_schema 保留 query 参数；若没有这行代码，参数透传丢失不会被发现
        self.assertEqual(tool.input_schema["required"], ["query"])  # 新增代码+ToolArchitectureV2: 断言 input_schema 保留 required 约束；若没有这行代码，必填参数约束回归不会被发现
        tool.input_schema["properties"]["mutated_by_test"] = {"type": "string"}  # 新增代码+ToolArchitectureV2: 修改返回的 AgentTool schema 来验证 registry 隔离；若没有这行代码，测试无法发现 agent_tools 返回值污染缓存
        fresh_tool = registry.agent_tools()[0]  # 新增代码+ToolArchitectureV2: 再次读取新的 AgentTool 条目；若没有这行代码，无法确认污染没有进入下一次返回
        self.assertNotIn("mutated_by_test", fresh_tool.input_schema["properties"])  # 新增代码+ToolArchitectureV2: 断言第二次返回没有携带外部修改；若没有这行代码，可变对象共享风险不会被锁住
    def test_agent_tool_pool_hides_deferred_mcp_tools_until_loaded(self) -> None:  # 新增代码+ToolArchitectureV2: 验证 agent 当前工具池默认隐藏 deferred MCP 工具但完整 catalog 仍保留它们；若没有这行代码，MCP 工具可能重新默认挤进模型上下文
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolArchitectureV2: 创建临时工作区隔离 memory 和调试日志；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolArchitectureV2: 把临时目录转成 Path 传给 LearningAgent；若没有这行代码，后续路径参数不够清晰稳定
            fake_client = FakeMcpClient(tools=[  # 新增代码+ToolArchitectureV2: 构造只暴露 browser_open 的 fake MCP client；若没有这行代码，测试没有 deferred MCP 工具来源
                {  # 新增代码+ToolArchitectureV2: 定义一个 MCP tools/list 返回的浏览器打开工具；若没有这行代码，registry 无法生成目标前缀工具名
                    "name": "browser_open",  # 新增代码+ToolArchitectureV2: 使用真实 browser_open 原始工具名；若没有这行代码，无法验证 mcp__browser_automation__browser_open 的隐藏行为
                    "description": "Open a browser page",  # 新增代码+ToolArchitectureV2: 提供英文工具说明贴近真实 MCP 工具；若没有这行代码，catalog 描述字段缺少测试输入
                    "inputSchema": {  # 新增代码+ToolArchitectureV2: 声明 browser_open 的 MCP 参数 schema；若没有这行代码，AgentTool 无法保留 url 参数约束
                        "type": "object",  # 新增代码+ToolArchitectureV2: 声明参数必须是对象；若没有这行代码，模型 schema 边界不完整
                        "properties": {  # 新增代码+ToolArchitectureV2: 列出 browser_open 允许的参数字段；若没有这行代码，url 字段没有容器可放
                            "url": {"type": "string"},  # 新增代码+ToolArchitectureV2: 声明 url 参数是字符串；若没有这行代码，测试无法覆盖 required url 的字段定义
                        },  # 新增代码+ToolArchitectureV2: 结束 properties 字典；若没有这行代码，测试工具 schema 语法不完整
                        "required": ["url"],  # 新增代码+ToolArchitectureV2: 声明 url 必填；若没有这行代码，required url 的目标场景没有被锁住
                    },  # 新增代码+ToolArchitectureV2: 结束 inputSchema 字典；若没有这行代码，MCP 工具条目结构不完整
                }  # 新增代码+ToolArchitectureV2: 结束 browser_open 工具条目；若没有这行代码，工具列表元素语法不完整
            ])  # 新增代码+ToolArchitectureV2: 结束 fake client 构造；若没有这行代码，后续 registry 没有可启动的测试 client
            registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+ToolArchitectureV2: 用 browser_automation server 名构造 registry；若没有这行代码，目标 MCP 前缀名不会出现
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+ToolArchitectureV2: 创建允许启动 MCP 的 agent；若没有这行代码，无法读取当前工具池和完整工具目录
            tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+ToolArchitectureV2: 收集当前模型可见工具池的名称；若没有这行代码，无法断言 deferred MCP 工具是否被隐藏
            self.assertEqual(sorted(tool_names), ["bash", "edit", "read", "write"])  # 修改代码+极简工具面: 断言当前工具池只保留四原子入口；若没有这行代码，MCP 隐藏测试会漏掉首轮工具膨胀回归
            self.assertNotIn("mcp__browser_automation__browser_open", tool_names)  # 新增代码+ToolArchitectureV2: 断言 deferred MCP 工具默认不进入当前工具池；若没有这行代码，大量 MCP 工具可能撑爆模型上下文
            catalog_names = [tool.name for tool in agent._tool_catalog()]  # 新增代码+ToolArchitectureV2: 收集完整工具目录里的工具名；若没有这行代码，无法证明隐藏只是当前池隐藏而不是 catalog 丢失
            self.assertIn("mcp__browser_automation__browser_open", catalog_names)  # 新增代码+ToolArchitectureV2: 断言完整 catalog 仍包含 deferred MCP 工具；若没有这行代码，后续 tool_search/select 将找不到待加载工具
    def test_tool_catalog_excludes_mcp_tools_when_start_is_denied(self) -> None:  # 新增代码+ToolArchitectureV2: 验证用户拒绝启动 MCP 时 catalog 不泄露外部工具；若没有这行代码，未授权工具可能仍被 tool_search 发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolArchitectureV2: 创建临时工作区隔离 agent 文件；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolArchitectureV2: 把临时目录转成 Path；若没有这行代码，LearningAgent 初始化参数不够清楚
            fake_client = FakeMcpClient(tools=[{"name": "browser_open", "description": "Open a browser page", "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}])  # 新增代码+ToolArchitectureV2: 构造一个会被拒绝启动的 MCP 工具来源；若没有这行代码，无法验证 catalog 泄露边界
            registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+ToolArchitectureV2: 用真实风格 server 名创建 registry；若没有这行代码，拒绝启动分支没有 MCP server 输入
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: False, mcp_tool_registry=registry)  # 新增代码+ToolArchitectureV2: 创建拒绝启动 MCP 的 agent；若没有这行代码，无法验证未授权 catalog 边界
            catalog_names = [tool.name for tool in agent._tool_catalog()]  # 新增代码+ToolArchitectureV2: 读取完整工具目录名称；若没有这行代码，无法判断拒绝后 catalog 是否还包含 MCP 工具
            self.assertIn("tool_search", catalog_names)  # 新增代码+ToolArchitectureV2: 断言拒绝 MCP 不影响内置发现入口；若没有这行代码，修复泄露时可能误删核心工具
            self.assertNotIn("mcp__browser_automation__browser_open", catalog_names)  # 新增代码+ToolArchitectureV2: 断言未授权 MCP 工具不会进入 catalog；若没有这行代码，用户拒绝启动后仍可能被模型发现外部工具
    def test_tool_search_select_loads_deferred_mcp_tool_into_next_pool(self) -> None:  # 新增代码+ToolArchitectureV2: 验证 tool_search 能先发现 deferred MCP 工具再用 select 加载进后续工具池；若没有这行代码，catalog 搜索和加载流程回归不会被测试发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolArchitectureV2: 创建临时工作区隔离 agent 文件和调试日志；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolArchitectureV2: 把临时目录转成 Path 传给 LearningAgent；若没有这行代码，后续构造 agent 的路径语义不够清晰
            fake_client = FakeMcpClient(tools=[  # 新增代码+ToolArchitectureV2: 构造只暴露 browser_open 的 fake MCP client；若没有这行代码，测试没有 deferred MCP 工具来源
                {  # 新增代码+ToolArchitectureV2: 定义一个 MCP tools/list 返回的浏览器打开工具；若没有这行代码，registry 无法生成目标前缀工具名
                    "name": "browser_open",  # 新增代码+ToolArchitectureV2: 使用真实 browser_open 原始工具名；若没有这行代码，无法验证 mcp__browser_automation__browser_open 的加载行为
                    "description": "Open a browser page",  # 新增代码+ToolArchitectureV2: 提供英文工具说明贴近真实 MCP 工具；若没有这行代码，tool_search 无法按 browser open 语义命中
                    "inputSchema": {  # 新增代码+ToolArchitectureV2: 声明 browser_open 的 MCP 参数 schema；若没有这行代码，AgentTool 无法保留 url 参数约束
                        "type": "object",  # 新增代码+ToolArchitectureV2: 声明参数必须是对象；若没有这行代码，模型 schema 边界不完整
                        "properties": {  # 新增代码+ToolArchitectureV2: 列出 browser_open 允许的参数字段；若没有这行代码，url 字段没有容器可放
                            "url": {"type": "string"},  # 新增代码+ToolArchitectureV2: 声明 url 参数是字符串；若没有这行代码，测试无法覆盖 required url 的字段定义
                        },  # 新增代码+ToolArchitectureV2: 结束 properties 字典；若没有这行代码，测试工具 schema 语法不完整
                        "required": ["url"],  # 新增代码+ToolArchitectureV2: 声明 url 必填；若没有这行代码，required url 的目标场景没有被锁住
                    },  # 新增代码+ToolArchitectureV2: 结束 inputSchema 字典；若没有这行代码，MCP 工具条目结构不完整
                }  # 新增代码+ToolArchitectureV2: 结束 browser_open 工具条目；若没有这行代码，工具列表元素语法不完整
            ])  # 新增代码+ToolArchitectureV2: 结束 fake client 构造；若没有这行代码，后续 registry 没有可启动的测试 client
            registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+ToolArchitectureV2: 用 browser_automation server 名构造 registry；若没有这行代码，目标 MCP 前缀名不会出现
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+ToolArchitectureV2: 创建允许启动 MCP 的 agent；若没有这行代码，无法执行 tool_search 和检查当前工具池
            search_output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "browser open", "max_results": 5}))  # 新增代码+ToolArchitectureV2: 先搜索 browser open 以发现 deferred 工具；若没有这行代码，无法证明未加载工具也能被 catalog 搜索到
            self.assertIn("mcp__browser_automation__browser_open", search_output)  # 新增代码+ToolArchitectureV2: 断言搜索结果包含 deferred MCP 工具名；若没有这行代码，tool_search 只搜当前池的回归不会失败
            self.assertIn("state：deferred", search_output)  # 新增代码+ToolArchitectureV2: 断言搜索输出明确标出 deferred 状态；若没有这行代码，模型可能不知道还不能直接调用该工具
            self.assertIn("source/来源：mcp", search_output)  # 新增代码+ToolArchitectureV2: 断言搜索输出包含 MCP 来源；若没有这行代码，模型难以区分外部工具和内置工具
            self.assertIn("加载提示：select:mcp__browser_automation__browser_open", search_output)  # 新增代码+ToolArchitectureV2: 断言搜索输出给出精确加载语法；若没有这行代码，模型可能猜错 select 用法
            select_output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "select:mcp__browser_automation__browser_open"}))  # 新增代码+ToolArchitectureV2: 用 select 指令请求把 deferred 工具加入后续工具池；若没有这行代码，加载入口没有测试输入
            self.assertIn("已加载", select_output)  # 新增代码+ToolArchitectureV2: 断言 select 成功文本包含已加载；若没有这行代码，模型无法确认加载是否成功
            tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+ToolArchitectureV2: 读取 select 后当前模型可见工具池名称；若没有这行代码，无法验证加载结果真正影响后续 pool
            self.assertIn("mcp__browser_automation__browser_open", tool_names)  # 新增代码+ToolArchitectureV2: 断言 deferred MCP 工具已进入当前工具池；若没有这行代码，只返回成功文本但没加载的假阳性不会暴露
    def test_tool_search_uses_mcp_search_hint_for_discovery(self) -> None:  # 新增代码+ToolPolicyV2: 验证 MCP searchHint 会参与工具搜索召回；若没有这行代码，服务端提示只会存档但不会帮助模型发现工具
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolPolicyV2: 创建临时工作区隔离 agent 文件；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolPolicyV2: 把临时目录转成 Path；若没有这行代码，LearningAgent 初始化路径语义不够清楚
            fake_client = FakeMcpClient(tools=[  # 新增代码+ToolPolicyV2: 构造一个名称和描述都不含 forecast 的 MCP 工具；若没有这行代码，无法证明召回来自 searchHint
                {  # 新增代码+ToolPolicyV2: 开始定义测试 MCP 工具条目；若没有这行代码，工具列表没有可搜索对象
                    "name": "opaque",  # 新增代码+ToolPolicyV2: 使用不含查询词的原始工具名；若没有这行代码，测试可能误由工具名命中
                    "description": "General remote lookup",  # 新增代码+ToolPolicyV2: 使用不含查询词的说明；若没有这行代码，测试可能误由描述命中
                    "inputSchema": {"type": "object", "properties": {"value": {"type": "string"}}},  # 新增代码+ToolPolicyV2: 提供不含查询词的参数 schema；若没有这行代码，参数名可能无法排除误命中
                    "_meta": {"anthropic/searchHint": "forecast climate lookup"},  # 新增代码+ToolPolicyV2: 把唯一查询线索放进 searchHint；若没有这行代码，无法验证 searchHint 召回路径
                }  # 新增代码+ToolPolicyV2: 结束测试 MCP 工具条目；若没有这行代码，工具字典语法不完整
            ])  # 新增代码+ToolPolicyV2: 结束 fake client 构造；若没有这行代码，registry 没有测试工具来源
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+ToolPolicyV2: 用 demo server 创建 registry；若没有这行代码，agent catalog 不会包含测试 MCP 工具
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+ToolPolicyV2: 创建允许启动 MCP 的 agent；若没有这行代码，tool_search 无法读取外部 catalog
            output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "forecast", "max_results": 5}))  # 新增代码+ToolPolicyV2: 使用只存在于 searchHint 的关键词搜索；若没有这行代码，searchHint 是否生效无法被测试
            self.assertIn("mcp__demo__opaque", output)  # 新增代码+ToolPolicyV2: 断言 searchHint 命中能召回目标工具；若没有这行代码，搜索提示失效不会被发现
            self.assertIn("search_hint：forecast climate lookup", output)  # 新增代码+ToolPolicyV2: 断言搜索结果解释命中提示；若没有这行代码，模型不知道为什么该工具被召回
    def test_deferred_mcp_tool_call_is_rejected_until_selected(self) -> None:  # 新增代码+ToolArchitectureV2: 验证未 select 的 deferred MCP 工具即使被模型直接点名也会被执行层拒绝；若没有这行代码，隐藏工具名可被绕过直接执行
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolArchitectureV2: 创建临时工作区隔离 agent 产生的文件；若没有这行代码，测试可能污染真实项目工作区
            workspace = Path(raw_dir)  # 新增代码+ToolArchitectureV2: 把临时目录字符串转成 Path 对象；若没有这行代码，LearningAgent 初始化路径不够清晰
            fake_client = FakeMcpClient(tools=[  # 新增代码+ToolArchitectureV2: 构造只暴露 browser_open 的 fake MCP client；若没有这行代码，测试无法模拟 deferred MCP 工具
                {  # 新增代码+ToolArchitectureV2: 开始定义 browser_open 工具条目；若没有这行代码，工具列表里没有可注册的 MCP 工具
                    "name": "browser_open",  # 新增代码+ToolArchitectureV2: 使用真实浏览器 MCP 原始工具名；若没有这行代码，前缀工具名不会变成目标 browser_open
                    "description": "Open a browser page",  # 新增代码+ToolArchitectureV2: 提供工具说明用于 catalog 搜索；若没有这行代码，工具元数据不符合任务要求
                    "inputSchema": {  # 新增代码+ToolArchitectureV2: 声明 MCP 工具输入 schema；若没有这行代码，registry 无法知道 url 是合法参数
                        "type": "object",  # 新增代码+ToolArchitectureV2: 声明参数必须是对象；若没有这行代码，工具参数边界不完整
                        "properties": {  # 新增代码+ToolArchitectureV2: 开始列出允许的参数字段；若没有这行代码，url 字段没有 schema 容器
                            "url": {"type": "string"},  # 新增代码+ToolArchitectureV2: 声明 url 是字符串参数；若没有这行代码，browser_open 的必填网址无法表达
                        },  # 新增代码+ToolArchitectureV2: 结束 properties 字典；若没有这行代码，测试工具 schema 语法不完整
                        "required": ["url"],  # 新增代码+ToolArchitectureV2: 声明 url 为必填参数；若没有这行代码，测试不符合 required url 场景
                    },  # 新增代码+ToolArchitectureV2: 结束 inputSchema 字典；若没有这行代码，MCP 工具条目结构不完整
                }  # 新增代码+ToolArchitectureV2: 结束 browser_open 工具条目；若没有这行代码，工具列表元素语法不完整
            ])  # 新增代码+ToolArchitectureV2: 结束 fake client 构造；若没有这行代码，agent 没有可启动的 fake MCP client
            registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+ToolArchitectureV2: 用 browser_automation server 名创建 registry；若没有这行代码，目标前缀工具名不会出现
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+ToolArchitectureV2: 创建允许 MCP 启动和调用的 agent；若没有这行代码，无法走 LearningAgent 执行层
            tool_call = ToolCall(name="mcp__browser_automation__browser_open", arguments={"url": "https://example.com"})  # 新增代码+ToolArchitectureV2: 构造模型直接猜出的隐藏 MCP 工具调用；若没有这行代码，无法验证绕过当前工具池的风险
            refused_output = agent._execute_tool(tool_call)  # 新增代码+ToolArchitectureV2: 未 select 前直接执行隐藏工具名；若没有这行代码，红灯不会覆盖执行层绕过路径
            self.assertIn("尚未通过 tool_search select 加载", refused_output)  # 新增代码+ToolArchitectureV2: 断言未加载工具被明确拒绝；若没有这行代码，直接 MCP 调用绕过不会失败
            select_output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "select:mcp__browser_automation__browser_open"}))  # 新增代码+ToolArchitectureV2: 通过 tool_search select 加载 deferred 工具；若没有这行代码，无法验证加载后允许执行
            self.assertIn("已加载", select_output)  # 新增代码+ToolArchitectureV2: 断言 select 成功；若没有这行代码，后续执行成功可能不是因为加载流程生效
            allowed_output = agent._execute_tool(tool_call)  # 新增代码+ToolArchitectureV2: select 后再次直接执行同一个 MCP 工具；若没有这行代码，无法验证加载后不再被拦截
            self.assertNotIn("尚未通过 tool_search select 加载", allowed_output)  # 新增代码+ToolArchitectureV2: 断言加载后的执行不包含拒绝文本；若没有这行代码，拦截可能错误地一直生效
            self.assertEqual(fake_client.calls[0][0], "browser_open")  # 新增代码+ToolArchitectureV2: 断言真实转发到 MCP 原始 browser_open 工具；若没有这行代码，执行可能只返回文本但没调用 fake client
    def test_mcp_registry_refreshes_tools_after_tools_list_changed_notification(self) -> None:  # 新增代码+MCPLifecycleV2: 验证 tools/list_changed 会驱动 registry 重新拉取 tools/list；若没有这行代码，Phase 3 可能只记录通知却不刷新工具目录
        old_tool = {"name": "old_tool", "description": "Old tool", "inputSchema": {"type": "object"}}  # 新增代码+MCPLifecycleV2: 准备刷新前的旧 MCP 工具；若没有这行代码，无法证明旧工具应被替换
        new_tool = {"name": "new_tool", "description": "New tool", "inputSchema": {"type": "object"}}  # 新增代码+MCPLifecycleV2: 准备刷新后的新 MCP 工具；若没有这行代码，无法证明 registry 重新读取了 client 当前工具列表
        fake_client = FakeMcpClient(tools=[old_tool])  # 新增代码+MCPLifecycleV2: 创建初始只暴露旧工具的 fake client；若没有这行代码，测试没有动态变化来源
        registry = McpToolRegistry({"demo": fake_client})  # 新增代码+MCPLifecycleV2: 构造 MCP registry；若没有这行代码，刷新逻辑没有被测对象
        registry.start()  # 新增代码+MCPLifecycleV2: 首次读取旧工具并建立缓存；若没有这行代码，后续无法断言刷新前后差异
        self.assertTrue(registry.has_tool("mcp__demo__old_tool"))  # 新增代码+MCPLifecycleV2: 断言旧工具刷新前存在；若没有这行代码，测试无法确认基线正确
        fake_client.tools = [new_tool]  # 新增代码+MCPLifecycleV2: 模拟 MCP server 动态替换工具列表；若没有这行代码，刷新前后内容不会变化
        fake_client.notifications.append({"jsonrpc": "2.0", "method": "notifications/tools/list_changed", "params": {}})  # 新增代码+MCPLifecycleV2: 模拟 server 推送 tools/list_changed；若没有这行代码，registry 不知道需要刷新
        summary = registry.refresh_from_notifications()  # 新增代码+MCPLifecycleV2: 触发 registry 消费通知并刷新；若没有这行代码，生产代码可能永远不处理 pending notifications
        refreshed_names = [schema["function"]["name"] for schema in registry.tool_schemas()]  # 新增代码+MCPLifecycleV2: 收集刷新后的工具名；若没有这行代码，无法断言 catalog 是否更新
        self.assertTrue(summary["refreshed_tools"])  # 新增代码+MCPLifecycleV2: 断言摘要标记执行过工具刷新；若没有这行代码，刷新动作可能悄悄缺失
        self.assertIn("tools", summary["changed_kinds"])  # 新增代码+MCPLifecycleV2: 断言通知被归类为 tools 变化；若没有这行代码，错误方法名映射不会暴露
        self.assertEqual(refreshed_names, ["mcp__demo__new_tool"])  # 新增代码+MCPLifecycleV2: 断言旧工具被替换为新工具；若没有这行代码，缓存不清理或重复累积不会被发现
        self.assertFalse(registry.has_tool("mcp__demo__old_tool"))  # 新增代码+MCPLifecycleV2: 断言旧路由已被移除；若没有这行代码，模型可能继续调用 server 已删除的工具
    def test_mcp_registry_records_prompts_resources_list_changed_for_skill_refresh(self) -> None:  # 新增代码+MCPLifecycleV2: 验证 prompts/resources list_changed 会形成 MCP skills/search 刷新挂点；若没有这行代码，Phase 3 只覆盖工具刷新而漏掉 ClaudeCode 的 prompt/resource 生命周期
        fake_client = FakeMcpClient(notifications=[{"jsonrpc": "2.0", "method": "notifications/prompts/list_changed", "params": {}}, {"jsonrpc": "2.0", "method": "notifications/resources/list_changed", "params": {}}])  # 新增代码+MCPLifecycleV2: 模拟同一 MCP server 连续通知 prompts 和 resources 变化；若没有这行代码，registry 没有可消费的非 tools 生命周期事件
        registry = McpToolRegistry({"docs": fake_client})  # 新增代码+MCPLifecycleV2: 构造 docs server 的 registry；若没有这行代码，刷新测试没有被测对象
        registry.start()  # 新增代码+MCPLifecycleV2: 先完成初始 MCP catalog 读取；若没有这行代码，生命周期刷新状态无法和正常启动流程对齐
        summary = registry.refresh_from_notifications()  # 新增代码+MCPLifecycleV2: 消费 fake client 的 prompts/resources 通知；若没有这行代码，通知只留在队列里不会变成刷新摘要
        self.assertEqual(summary["changed_kinds"], ["prompts", "resources"])  # 新增代码+MCPLifecycleV2: 断言两个 list_changed 类型都被正确归类；若没有这行代码，method 映射错误不会被发现
        self.assertFalse(summary["refreshed_tools"])  # 新增代码+MCPLifecycleV2: 断言非 tools 变化不会错误重建工具目录；若没有这行代码，prompt/resource 变化可能造成不必要的 tools/list 副作用
        self.assertTrue(summary["refreshed_prompts"])  # 新增代码+MCPLifecycleV2: 断言 prompts 变化进入刷新摘要；若没有这行代码，后续 prompt cache 清理层没有可验证信号
        self.assertTrue(summary["refreshed_resources"])  # 新增代码+MCPLifecycleV2: 断言 resources 变化进入刷新摘要；若没有这行代码，后续 resource cache 清理层没有可验证信号
        self.assertEqual(summary["mcp_skill_refresh_version"], 1)  # 新增代码+MCPLifecycleV2: 断言 prompts/resources 会递增 MCP skills/search 索引失效版本；若没有这行代码，技能刷新挂点可能只是口头设计
        self.assertEqual([event["kind"] for event in registry.lifecycle_events()], ["prompts", "resources"])  # 新增代码+MCPLifecycleV2: 断言审计事件保留处理顺序；若没有这行代码，用户无法追踪到底是哪类 MCP 生命周期通知触发刷新
    def test_tool_search_uses_refreshed_mcp_catalog_after_list_changed(self) -> None:  # 新增代码+MCPLifecycleV2: 验证 LearningAgent 的 tool_search 会看到刷新后的 MCP catalog；若没有这行代码，registry 刷新可能无法传到模型发现层
        old_tool = {"name": "old_weather", "description": "Old weather lookup", "inputSchema": {"type": "object"}}  # 新增代码+MCPLifecycleV2: 准备旧天气工具；若没有这行代码，搜索刷新前基线不明确
        new_tool = {"name": "live_forecast", "description": "Fresh forecast lookup", "inputSchema": {"type": "object"}}  # 新增代码+MCPLifecycleV2: 准备刷新后应被搜索到的新工具；若没有这行代码，ToolSearch 没有新目标可断言
        fake_client = FakeMcpClient(tools=[old_tool])  # 新增代码+MCPLifecycleV2: 创建初始旧工具 fake client；若没有这行代码，agent 初始化时没有 MCP 工具目录
        registry = McpToolRegistry({"weather": fake_client})  # 新增代码+MCPLifecycleV2: 用 weather server 名构造 registry；若没有这行代码，MCP 工具前缀无法确定
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCPLifecycleV2: 创建临时工作区隔离 agent memory/debug 文件；若没有这行代码，测试会污染真实工作区
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=raw_dir, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+MCPLifecycleV2: 创建允许启动 MCP 的 agent；若没有这行代码，ToolSearch 路径不会运行
            first_output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "weather", "max_results": 5}))  # 新增代码+MCPLifecycleV2: 先搜索旧工具并填充 catalog cache；若没有这行代码，后续无法证明缓存会被刷新失效
            self.assertIn("mcp__weather__old_weather", first_output)  # 新增代码+MCPLifecycleV2: 断言旧工具初始可被搜索；若没有这行代码，测试基线可能为空
            fake_client.tools = [new_tool]  # 新增代码+MCPLifecycleV2: 模拟 server 把工具列表替换成新工具；若没有这行代码，刷新不会产生可见变化
            fake_client.notifications.append({"jsonrpc": "2.0", "method": "notifications/tools/list_changed", "params": {}})  # 新增代码+MCPLifecycleV2: 模拟 list_changed 通知到达 client；若没有这行代码，agent 没有刷新信号
            second_output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "forecast", "max_results": 5}))  # 新增代码+MCPLifecycleV2: 再次通过模型可用入口搜索新能力；若没有这行代码，无法证明 ToolSearch 使用刷新后目录
        self.assertIn("mcp__weather__live_forecast", second_output)  # 新增代码+MCPLifecycleV2: 断言新工具进入 ToolSearch 输出；若没有这行代码，catalog cache 未失效不会暴露
        self.assertNotIn("mcp__weather__old_weather", second_output)  # 新增代码+MCPLifecycleV2: 断言旧工具不再混入搜索结果；若没有这行代码，旧 catalog 残留不会被发现
    def test_mcp_http_client_records_sse_notifications_for_lifecycle_refresh(self) -> None:  # 新增代码+MCPLifecycleV2: 验证 HTTP SSE 中的 JSON-RPC notification 会进入 pending 队列；若没有这行代码，Streamable HTTP server 的 list_changed 会被解析后丢弃
        registry = McpToolRegistry.from_configs([McpServerConfig(name="remote", command="", transport="http", url="http://127.0.0.1/mcp")])  # 新增代码+MCPLifecycleV2: 通过真实工厂创建 HTTP client 但不联网；若没有这行代码，测试不到 HTTP transport 的 SSE 解析对象
        client = registry._clients["remote"]  # 新增代码+MCPLifecycleV2: 取出 HTTP client 用于直接测试 SSE 解析；若没有这行代码，无法触发私有解析函数
        client._parse_sse_events('id: 7\nevent: message\ndata: {"jsonrpc":"2.0","method":"notifications/tools/list_changed","params":{}}\n\n')  # 新增代码+MCPLifecycleV2: 注入一条 list_changed SSE 事件；若没有这行代码，pending notification 队列没有输入
        notifications = client.pop_notifications()  # 新增代码+MCPLifecycleV2: 拉取 client 记录的 pending notifications；若没有这行代码，无法证明通知没有被丢弃
        self.assertEqual([notification["method"] for notification in notifications], ["notifications/tools/list_changed"])  # 新增代码+MCPLifecycleV2: 断言 HTTP SSE 通知被完整保留；若没有这行代码，后续 registry 无法基于通知刷新
    def test_mcp_stdio_client_records_json_rpc_notifications_for_lifecycle_refresh(self) -> None:  # 新增代码+MCPLifecycleV2: 验证 stdio client 会缓存无 id 的 JSON-RPC notification；若没有这行代码，stdio MCP server 的 list_changed 可能仍在响应读取时被丢弃
        client = McpStdioClient(McpServerConfig(name="demo", command=sys.executable, args=[]))  # 新增代码+MCPLifecycleV2: 构造不启动进程的 stdio client 用于测试通知缓存；若没有这行代码，无法覆盖 stdio transport 的 notification 队列
        client._remember_notification({"jsonrpc": "2.0", "method": "notifications/tools/list_changed", "params": {"source": "stdio"}})  # 新增代码+MCPLifecycleV2: 模拟 server 推送没有 id 的 tools/list_changed；若没有这行代码，pending 队列没有有效通知输入
        client._remember_notification({"jsonrpc": "2.0", "id": 1, "result": {}})  # 新增代码+MCPLifecycleV2: 模拟普通 response 消息；若没有这行代码，测试无法确认 response 不会被误当成 notification
        notifications = client.pop_notifications()  # 新增代码+MCPLifecycleV2: 拉取 stdio client 缓存的通知；若没有这行代码，无法验证 pop 会返回并清空 pending 队列
        self.assertEqual([notification["method"] for notification in notifications], ["notifications/tools/list_changed"])  # 新增代码+MCPLifecycleV2: 断言只保存真正 notification；若没有这行代码，response 混入队列的回归不会被发现
        self.assertEqual(client.pop_notifications(), [])  # 新增代码+MCPLifecycleV2: 断言通知被一次性消费；若没有这行代码，同一 list_changed 可能反复触发刷新
    def test_mcp_agent_tools_preserve_annotations_search_hint_and_always_load(self) -> None:  # 新增代码+ToolPolicyV2: 验证 MCP annotations 和 _meta 会进入 AgentTool；若没有这行代码，Task 2 元数据映射回归不会被测试发现
        input_schema = {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}  # 新增代码+ToolPolicyV2: 准备原始 MCP inputSchema；若没有这行代码，测试无法确认 input_json_schema 保存的是原始输入结构
        output_schema = {"type": "object", "properties": {"answer": {"type": "string"}}}  # 新增代码+ToolPolicyV2: 准备原始 MCP outputSchema；若没有这行代码，测试无法确认 output_schema 被保留下来
        fake_client = FakeMcpClient(tools=[  # 新增代码+ToolPolicyV2: 创建带 annotations 和 _meta 的 fake MCP client；若没有这行代码，registry 没有可控元数据输入
            {  # 新增代码+ToolPolicyV2: 定义一个 MCP 工具对象；若没有这行代码，工具字段无法按 MCP 返回形态组织
                "name": "docs_lookup",  # 新增代码+ToolPolicyV2: 设置原始 MCP 工具名；若没有这行代码，server 路由和 original_name 无法建立
                "description": "Lookup network documentation",  # 新增代码+ToolPolicyV2: 设置工具说明；若没有这行代码，AgentTool 描述会缺少来源文本
                "inputSchema": input_schema,  # 新增代码+ToolPolicyV2: 传入原始 inputSchema；若没有这行代码，input_json_schema 断言没有比较对象
                "outputSchema": output_schema,  # 新增代码+ToolPolicyV2: 传入原始 outputSchema；若没有这行代码，output_schema 断言没有比较对象
                "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True},  # 新增代码+ToolPolicyV2: 模拟 MCP annotations；若没有这行代码，只读、破坏性和开放世界标记不会被覆盖
                "_meta": {"anthropic/searchHint": "network docs lookup", "anthropic/alwaysLoad": True},  # 新增代码+ToolPolicyV2: 模拟 Anthropic 扩展元数据；若没有这行代码，search_hint 和 always_load 映射不会被测试
            }  # 新增代码+ToolPolicyV2: 结束 MCP 工具对象；若没有这行代码，工具列表语法无法闭合
        ])  # 新增代码+ToolPolicyV2: 结束 fake client 构造；若没有这行代码，测试无法继续创建 registry
        registry = McpToolRegistry({"docs": fake_client})  # 新增代码+ToolPolicyV2: 用 docs server 名构造注册表；若没有这行代码，server_name 映射无法验证
        registry.start()  # 新增代码+ToolPolicyV2: 启动注册表并读取 tools/list；若没有这行代码，agent_tools 没有缓存工具可包装
        tool = registry.agent_tools()[0]  # 新增代码+ToolPolicyV2: 取出转换后的 AgentTool；若没有这行代码，后续断言没有目标对象
        self.assertTrue(tool.is_read_only)  # 新增代码+ToolPolicyV2: 断言 readOnlyHint 映射为只读；若没有这行代码，只读标记丢失不会被发现
        self.assertFalse(tool.is_destructive)  # 新增代码+ToolPolicyV2: 断言 destructiveHint=False 被保留；若没有这行代码，破坏性标记误判不会被发现
        self.assertTrue(tool.is_open_world)  # 新增代码+ToolPolicyV2: 断言 openWorldHint 映射为开放世界；若没有这行代码，网络/外部世界能力标记丢失不会被发现
        self.assertEqual(tool.search_hint, "network docs lookup")  # 新增代码+ToolPolicyV2: 断言 searchHint 被保留；若没有这行代码，搜索提示丢失不会被发现
        self.assertTrue(tool.always_load)  # 新增代码+ToolPolicyV2: 断言 alwaysLoad 会覆盖 MCP 默认延迟策略；若没有这行代码，关键外部工具可能不会首轮加载
        self.assertEqual(tool.input_json_schema, input_schema)  # 新增代码+ToolPolicyV2: 断言原始 inputSchema 被深拷贝保存；若没有这行代码，后续策略拿不到 MCP 原始输入结构
        self.assertEqual(tool.output_schema, output_schema)  # 新增代码+ToolPolicyV2: 断言 outputSchema 被深拷贝保存；若没有这行代码，结果结构约束会丢失
        self.assertEqual(tool.server_name, "docs")  # 新增代码+ToolPolicyV2: 断言 server_name 保留 docs；若没有这行代码，多 server 场景无法追踪工具来源
    def test_mcp_agent_tools_accept_plain_meta_search_hint_and_always_load(self) -> None:  # 新增代码+ToolPolicyV2: 验证非 anthropic 前缀的兼容 _meta 字段也会被识别；若没有这行代码，兼容 MCP server 的元数据声明会失效
        fake_client = FakeMcpClient(tools=[  # 新增代码+ToolPolicyV2: 创建带普通 searchHint/alwaysLoad 的 fake MCP client；若没有这行代码，测试没有兼容元数据输入
            {  # 新增代码+ToolPolicyV2: 定义一个 MCP 工具对象；若没有这行代码，registry 无法生成 AgentTool
                "name": "plain_meta",  # 新增代码+ToolPolicyV2: 设置原始 MCP 工具名；若没有这行代码，前缀路由无法建立
                "description": "Plain metadata",  # 新增代码+ToolPolicyV2: 设置工具说明；若没有这行代码，AgentTool 描述会为空
                "inputSchema": {"type": "object"},  # 新增代码+ToolPolicyV2: 提供最小输入 schema；若没有这行代码，工具参数结构会走兜底路径
                "_meta": {"searchHint": "plain hint", "alwaysLoad": True},  # 新增代码+ToolPolicyV2: 使用兼容普通字段而不是 anthropic 前缀字段；若没有这行代码，无法验证 fallback 逻辑
            }  # 新增代码+ToolPolicyV2: 结束 MCP 工具对象；若没有这行代码，工具字典语法不完整
        ])  # 新增代码+ToolPolicyV2: 结束 fake client 构造；若没有这行代码，registry 没有测试 client
        registry = McpToolRegistry({"docs": fake_client})  # 新增代码+ToolPolicyV2: 用 docs server 名构造注册表；若没有这行代码，被测转换逻辑不会运行
        registry.start()  # 新增代码+ToolPolicyV2: 启动 registry 并读取 _meta；若没有这行代码，agent_tools 没有缓存元数据可用
        tool = registry.agent_tools()[0]  # 新增代码+ToolPolicyV2: 取出转换后的 AgentTool；若没有这行代码，后续断言没有目标对象
        self.assertEqual(tool.search_hint, "plain hint")  # 新增代码+ToolPolicyV2: 断言普通 searchHint 被保存；若没有这行代码，兼容搜索提示丢失不会被发现
        self.assertTrue(tool.always_load)  # 新增代码+ToolPolicyV2: 断言普通 alwaysLoad 会启用强制加载；若没有这行代码，兼容强制加载声明丢失不会被发现
    def test_mcp_agent_tools_treat_string_false_metadata_as_false(self) -> None:  # 新增代码+ToolPolicyV2: 验证字符串 false/0/no 不会被当成 True；若没有这行代码，bool("false") 回归会误开元数据标记
        fake_client = FakeMcpClient(tools=[  # 新增代码+ToolPolicyV2: 构造带字符串 false 元数据的 fake MCP client；若没有这行代码，测试没有可控输入
            {  # 新增代码+ToolPolicyV2: 定义一个测试用 MCP 工具对象；若没有这行代码，annotations 和 _meta 无处挂载
                "name": "metadata_false",  # 新增代码+ToolPolicyV2: 设置原始工具名；若没有这行代码，registry 无法生成前缀工具
                "description": "Metadata false strings",  # 新增代码+ToolPolicyV2: 设置工具说明；若没有这行代码，AgentTool 描述会为空
                "inputSchema": {"type": "object"},  # 新增代码+ToolPolicyV2: 提供最小合法输入 schema；若没有这行代码，参数结构会走兜底而不贴近正常 MCP 工具
                "annotations": {"readOnlyHint": "false", "destructiveHint": "0", "openWorldHint": "no"},  # 新增代码+ToolPolicyV2: 用常见字符串假值覆盖 annotations；若没有这行代码，误判 True 的风险不会被测试
                "_meta": {"anthropic/alwaysLoad": "false", "strict": "false", "anthropic/strict": True},  # 新增代码+ToolPolicyV2: 用字符串 false 覆盖 alwaysLoad/strict 并放入后备 True；若没有这行代码，优先级和严格布尔解析不会被测试
            }  # 新增代码+ToolPolicyV2: 结束工具定义；若没有这行代码，Python 字典语法不完整
        ])  # 新增代码+ToolPolicyV2: 结束 fake client 构造；若没有这行代码，测试无法创建 registry
        registry = McpToolRegistry({"docs": fake_client})  # 新增代码+ToolPolicyV2: 创建 registry 执行 MCP 元数据转换；若没有这行代码，被测逻辑不会运行
        registry.start()  # 新增代码+ToolPolicyV2: 启动 registry 并缓存工具元数据；若没有这行代码，agent_tools 会返回空列表
        tool = registry.agent_tools()[0]  # 新增代码+ToolPolicyV2: 取出转换后的 AgentTool；若没有这行代码，后续断言没有目标
        self.assertFalse(tool.is_read_only)  # 新增代码+ToolPolicyV2: 断言字符串 false 不会开启只读标记；若没有这行代码，readOnlyHint 误判不会暴露
        self.assertFalse(tool.is_destructive)  # 新增代码+ToolPolicyV2: 断言字符串 0 不会开启破坏性标记；若没有这行代码，destructiveHint 误判不会暴露
        self.assertFalse(tool.is_open_world)  # 新增代码+ToolPolicyV2: 断言字符串 no 不会开启开放世界标记；若没有这行代码，openWorldHint 误判不会暴露
        self.assertFalse(tool.always_load)  # 新增代码+ToolPolicyV2: 断言字符串 false 不会开启 always_load；若没有这行代码，外部工具可能被错误强制加载
        self.assertFalse(tool.strict)  # 新增代码+ToolPolicyV2: 断言 strict 字符串 false 优先时不会被后备 True 误覆盖；若没有这行代码，strict 解析优先级和布尔解析错误不会暴露
    def test_mcp_agent_tools_ignore_non_dict_annotations_and_meta(self) -> None:  # 新增代码+ToolPolicyV2: 验证 annotations/_meta 非字典时不崩溃且布尔默认 False；若没有这行代码，坏 MCP 元数据可能让 catalog 构建失败
        fake_client = FakeMcpClient(tools=[  # 新增代码+ToolPolicyV2: 构造异常元数据 fake MCP client；若没有这行代码，测试没有坏输入
            {  # 新增代码+ToolPolicyV2: 定义一个异常元数据工具；若没有这行代码，registry 没有工具可转换
                "name": "metadata_bad",  # 新增代码+ToolPolicyV2: 设置原始工具名；若没有这行代码，前缀名无法生成
                "description": "Bad metadata",  # 新增代码+ToolPolicyV2: 设置说明；若没有这行代码，AgentTool 描述为空
                "inputSchema": {"type": "object"},  # 新增代码+ToolPolicyV2: 提供最小输入 schema；若没有这行代码，测试会混入坏 inputSchema 兜底逻辑
                "annotations": "not a dict",  # 新增代码+ToolPolicyV2: 模拟异常 annotations；若没有这行代码，非 dict 容错分支不会被覆盖
                "_meta": "not a dict",  # 新增代码+ToolPolicyV2: 模拟异常 _meta；若没有这行代码，非 dict meta 容错分支不会被覆盖
            }  # 新增代码+ToolPolicyV2: 结束工具定义；若没有这行代码，Python 字典语法不完整
        ])  # 新增代码+ToolPolicyV2: 结束 fake client 构造；若没有这行代码，registry 没有测试 client
        registry = McpToolRegistry({"docs": fake_client})  # 新增代码+ToolPolicyV2: 创建 registry；若没有这行代码，被测转换逻辑不会运行
        registry.start()  # 新增代码+ToolPolicyV2: 启动 registry 并处理异常元数据；若没有这行代码，无法验证不崩溃
        tool = registry.agent_tools()[0]  # 新增代码+ToolPolicyV2: 读取转换后的 AgentTool；若没有这行代码，默认值无法断言
        self.assertFalse(tool.is_read_only)  # 新增代码+ToolPolicyV2: 断言异常 annotations 不会开启只读；若没有这行代码，默认值错误不会暴露
        self.assertFalse(tool.is_destructive)  # 新增代码+ToolPolicyV2: 断言异常 annotations 不会开启破坏性；若没有这行代码，默认值错误不会暴露
        self.assertFalse(tool.is_open_world)  # 新增代码+ToolPolicyV2: 断言异常 annotations 不会开启开放世界；若没有这行代码，默认值错误不会暴露
        self.assertFalse(tool.always_load)  # 新增代码+ToolPolicyV2: 断言异常 _meta 不会开启 always_load；若没有这行代码，默认值错误不会暴露
        self.assertFalse(tool.strict)  # 新增代码+ToolPolicyV2: 断言异常 _meta 不会开启 strict；若没有这行代码，默认值错误不会暴露
    def test_mcp_agent_tools_deep_copy_input_and_output_schema_metadata(self) -> None:  # 新增代码+ToolPolicyV2: 验证 AgentTool 保存的 input/output schema 不被原始 MCP 对象后续修改污染；若没有这行代码，深拷贝隔离回归不会被发现
        input_schema = {"type": "object", "properties": {"query": {"type": "string"}}}  # 新增代码+ToolPolicyV2: 准备可变 inputSchema；若没有这行代码，后续无法模拟原始输入污染
        output_schema = {"type": "object", "properties": {"answer": {"type": "string"}}}  # 新增代码+ToolPolicyV2: 准备可变 outputSchema；若没有这行代码，后续无法模拟原始输出污染
        fake_client = FakeMcpClient(tools=[  # 新增代码+ToolPolicyV2: 创建引用可变 schema 的 fake client；若没有这行代码，registry 无法读取这些 schema
            {  # 新增代码+ToolPolicyV2: 定义一个带 input/output schema 的 MCP 工具；若没有这行代码，测试没有可转换工具
                "name": "schema_copy",  # 新增代码+ToolPolicyV2: 设置原始工具名；若没有这行代码，前缀路由无法生成
                "description": "Schema copy",  # 新增代码+ToolPolicyV2: 设置工具说明；若没有这行代码，AgentTool 描述为空
                "inputSchema": input_schema,  # 新增代码+ToolPolicyV2: 传入可变 inputSchema；若没有这行代码，input_json_schema 深拷贝无法被验证
                "outputSchema": output_schema,  # 新增代码+ToolPolicyV2: 传入可变 outputSchema；若没有这行代码，output_schema 深拷贝无法被验证
            }  # 新增代码+ToolPolicyV2: 结束工具定义；若没有这行代码，Python 字典语法不完整
        ])  # 新增代码+ToolPolicyV2: 结束 fake client 构造；若没有这行代码，registry 没有测试 client
        registry = McpToolRegistry({"docs": fake_client})  # 新增代码+ToolPolicyV2: 创建 registry；若没有这行代码，被测缓存逻辑不会运行
        registry.start()  # 新增代码+ToolPolicyV2: 启动 registry 并缓存 schema 深拷贝；若没有这行代码，后续污染无比较基准
        input_schema["properties"]["query"]["type"] = "number"  # 新增代码+ToolPolicyV2: 修改原始 inputSchema 嵌套字段模拟污染；若没有这行代码，深拷贝隔离无法被检验
        output_schema["properties"]["answer"]["type"] = "number"  # 新增代码+ToolPolicyV2: 修改原始 outputSchema 嵌套字段模拟污染；若没有这行代码，深拷贝隔离无法被检验
        tool = registry.agent_tools()[0]  # 新增代码+ToolPolicyV2: 读取转换后的 AgentTool；若没有这行代码，无法观察缓存是否被污染
        self.assertEqual(tool.input_json_schema["properties"]["query"]["type"], "string")  # 新增代码+ToolPolicyV2: 断言 input_json_schema 没被原始对象污染；若没有这行代码，输入 schema 共享引用问题不会暴露
        self.assertEqual(tool.output_schema["properties"]["answer"]["type"], "string")  # 新增代码+ToolPolicyV2: 断言 output_schema 没被原始对象污染；若没有这行代码，输出 schema 共享引用问题不会暴露
    def test_mcp_tool_registry_prunes_arguments_not_declared_by_tool_schema(self) -> None:  # 新增代码+MCP参数清洗: 复现 browser_open 混入 status/action 等无关字段的问题；若省略: 授权后仍可能把模型串味参数发给真实浏览器工具
        browser_tools = [  # 新增代码+MCP参数清洗: 构造真实 browser_open 风格 schema；若省略: 测试无法贴近截图里的真实工具
            {  # 新增代码+MCP参数清洗: 定义一个最小 browser_open 工具；若省略: registry 没有可注册的浏览器工具
                "name": "browser_open",  # 新增代码+MCP参数清洗: 使用真实 MCP 原始工具名；若省略: 前缀工具名无法匹配 browser_open
                "description": "Open browser page",  # 新增代码+MCP参数清洗: 提供工具说明；若省略: schema 转换语义不完整
                "inputSchema": {  # 新增代码+MCP参数清洗: 写出该工具允许的参数范围；若省略: registry 无法知道哪些字段该保留
                    "type": "object",  # 新增代码+MCP参数清洗: 声明参数是对象；若省略: 参数过滤没有对象边界
                    "properties": {  # 新增代码+MCP参数清洗: 只声明 url/new_tab/timeout_ms 三个合法字段；若省略: 无法证明 status/action 应被丢弃
                        "url": {"type": "string"},  # 新增代码+MCP参数清洗: 声明打开网页地址；若省略: url 会被错误清掉
                        "new_tab": {"type": "boolean"},  # 新增代码+MCP参数清洗: 声明是否新标签页打开；若省略: 合法 new_tab 可能被误删
                        "timeout_ms": {"type": "integer"},  # 新增代码+MCP参数清洗: 声明页面加载超时；若省略: 合法 timeout_ms 可能被误删
                    },  # 新增代码+MCP参数清洗: properties 结束；若省略: 测试工具 schema 语法不完整
                    "required": ["url"],  # 新增代码+MCP参数清洗: 声明 url 必填；若省略: 工具约束不贴近真实 browser_open
                },  # 新增代码+MCP参数清洗: inputSchema 结束；若省略: 工具定义不完整
            }  # 新增代码+MCP参数清洗: browser_open 工具定义结束；若省略: 列表项语法不完整
        ]  # 新增代码+MCP参数清洗: 工具列表结束；若省略: fake client 没有工具输入
        fake_client = FakeMcpClient(tools=browser_tools)  # 新增代码+MCP参数清洗: 用 fake client 记录 registry 实际转发参数；若省略: 测试无法观察参数是否被清洗
        registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+MCP参数清洗: 使用真实 server 名前缀构造 registry；若省略: 工具名不贴近用户截图
        registry.start()  # 新增代码+MCP参数清洗: 启动 registry 并缓存 browser_open schema；若省略: call_tool 会找不到工具路由
        registry.call_tool(  # 新增代码+MCP参数清洗: 调用带有混入字段的工具；若省略: 红灯不会覆盖真实错误输入
            "mcp__browser_automation__browser_open",  # 新增代码+MCP参数清洗: 调用模型可见的前缀工具名；若省略: registry 无法路由到原始 browser_open
            {  # 新增代码+MCP参数清洗: 模拟截图里模型输出的参数；若省略: 测试无法复现 status/action 混入
                "status": "all",  # 新增代码+MCP参数清洗: 混入来自 browser_tabs 的无关字段；若省略: 无法证明 status 会被清掉
                "state": "active",  # 新增代码+MCP参数清洗: 混入来自标签页状态的无关字段；若省略: 无法证明 state 会被清掉
                "action": "list",  # 新增代码+MCP参数清洗: 混入来自 tabs/downloads 的动作字段；若省略: 无法证明 action 会被清掉
                "result_status": "ok",  # 新增代码+MCP参数清洗: 混入工具结果字段；若省略: 无法证明结果字段不会反送给工具
                "url": "https://www.bing.com/search?q=Ho+Chi+Minh+City+weather+today",  # 新增代码+MCP参数清洗: 保留 browser_open 真正需要的地址；若省略: 工具无法打开页面
                "new_tab": False,  # 新增代码+MCP参数清洗: 保留合法布尔参数；若省略: 测试无法确认合法字段不会被删
                "timeout_ms": 10000,  # 新增代码+MCP参数清洗: 保留合法超时参数；若省略: 测试无法确认加载超时仍可控制
                "confirm_real_profile": True,  # 新增代码+MCP参数清洗: 混入真实 Chrome 连接工具字段；若省略: 无法覆盖截图里最容易让用户紧张的字段
            },  # 新增代码+MCP参数清洗: 混合参数结束；若省略: Python 调用无法闭合
        )  # 新增代码+MCP参数清洗: registry 调用结束；若省略: fake_client.calls 不会产生记录
        self.assertEqual(fake_client.calls, [("browser_open", {"url": "https://www.bing.com/search?q=Ho+Chi+Minh+City+weather+today", "new_tab": False, "timeout_ms": 10000})])  # 新增代码+MCP参数清洗: 断言只把 schema 声明过的字段发给真实工具；若省略: 参数串味问题会继续回归
    def test_mcp_registry_gives_browser_automation_longer_stdio_timeout(self) -> None:  # 新增代码+浏览器超时: 验证 browser_automation 的外层 MCP 等待时间长于页面加载时间；若省略: browser_open 可能页面还没超时，stdio 客户端先报超时
        config = McpServerConfig(name="browser_automation", command=sys.executable, args=["-c", "pass"])  # 新增代码+浏览器超时: 构造 browser_automation stdio 配置但不真正启动；若省略: 无法测试工厂创建 client 的超时参数
        registry = McpToolRegistry.from_configs([config])  # 新增代码+浏览器超时: 通过真实工厂创建 registry；若省略: 测试不到用户启动路径
        client = registry._clients["browser_automation"]  # 新增代码+浏览器超时: 取出工厂创建的 browser client；若省略: 无法检查 request_timeout_seconds
        self.assertGreaterEqual(client.request_timeout_seconds, 35.0)  # 新增代码+浏览器超时: 断言外层至少能覆盖 30000ms 页面超时并留余量；若省略: 5 秒默认值会继续制造“浏览器卡住”的假象
    def test_mcp_stdio_client_defaults_to_longer_timeout_for_browser_automation(self) -> None:  # 新增代码+浏览器超时: 验证直接构造 browser_automation stdio client 也使用长超时；若省略: 单元测试和其他代码绕过 registry 时仍会 5 秒误超时
        config = McpServerConfig(name="browser_automation", command=sys.executable, args=["-c", "pass"])  # 新增代码+浏览器超时: 构造 browser_automation 配置但不启动进程；若省略: 无法检查默认超时策略
        client = McpStdioClient(config)  # 新增代码+浏览器超时: 直接构造 stdio client 复现全量测试里的路径；若省略: 只测 registry 工厂会漏掉直接构造场景
        self.assertGreaterEqual(client.request_timeout_seconds, 35.0)  # 新增代码+浏览器超时: 断言默认值覆盖浏览器 30000ms 页面等待；若省略: 直接构造仍可能导致 browser_open 偶发超时
    def test_mcp_tool_registry_start_is_idempotent(self) -> None:  # 新增代码+MCP 工具注册表健壮性: 验证重复 start 不重复累计 schema 或污染路由；若省略: 重新启动注册表可能悄悄制造重复工具
        fake_client = FakeMcpClient()  # 新增代码+MCP 工具注册表健壮性: 创建默认 echo fake client；若省略: 无法驱动注册表发现工具
        registry = McpToolRegistry({"demo": fake_client})  # 新增代码+MCP 工具注册表健壮性: 构造单 server 注册表；若省略: 无法验证重复启动行为
        registry.start()  # 新增代码+MCP 工具注册表健壮性: 第一次启动并缓存工具；若省略: 后续无法比较重复启动前后的状态
        registry.start()  # 新增代码+MCP 工具注册表健壮性: 第二次启动同一注册表；若省略: 无法覆盖重复 start 场景
        schemas = registry.tool_schemas()  # 新增代码+MCP 工具注册表健壮性: 读取重复启动后的 schema；若省略: 无法判断是否重复累积工具
        self.assertEqual(len(schemas), 1)  # 新增代码+MCP 工具注册表健壮性: 断言 schema 没有重复；若省略: 重复工具污染不会被发现
        self.assertTrue(registry.has_tool("mcp__demo__echo"))  # 新增代码+MCP 工具注册表健壮性: 断言路由仍包含正确工具；若省略: 路由清空或污染不会被发现
        self.assertEqual(registry.call_tool("mcp__demo__echo", {"text": "again"}), "called echo: again")  # 新增代码+MCP 工具注册表健壮性: 断言重复启动后仍能正确调用；若省略: schema 正确但路由错误不会被发现
    def test_mcp_tool_registry_uses_safe_unique_tool_names(self) -> None:  # 新增代码+MCP 工具注册表健壮性: 验证 ASCII 安全命名、sanitize 冲突递增和多 server 路由；若省略: 非 ASCII 名称或冲突会污染模型工具名
        demo_client = FakeMcpClient(  # 新增代码+MCP 工具注册表健壮性: 创建含冲突工具名的 demo client；若省略: 无法覆盖同 server sanitize 后冲突
            tools=[  # 新增代码+MCP 工具注册表健壮性: 定义两个 sanitize 后同名的工具；若省略: 唯一名称递增逻辑没有测试输入
                {"name": "a/b", "description": "Slash name", "inputSchema": {"type": "object"}},  # 新增代码+MCP 工具注册表健壮性: 第一个工具 sanitize 后应为 a_b；若省略: 无法建立冲突基准
                {"name": "a b", "description": "Space name", "inputSchema": {"type": "object"}},  # 新增代码+MCP 工具注册表健壮性: 第二个工具 sanitize 后也为 a_b 并应追加 _2；若省略: 冲突递增不会被触发
                {"name": "你好.tool", "description": "Unicode name", "inputSchema": {"type": "object"}},  # 新增代码+MCP 工具注册表健壮性: 非 ASCII 和点号工具名应被替换为 ASCII 下划线；若省略: 中文保留问题不会被发现
            ],  # 新增代码+MCP 工具注册表健壮性: 结束 demo 工具列表；若省略: fake client 构造语法不完整
            result_prefix="demo",  # 新增代码+MCP 工具注册表健壮性: 返回结果中标记 demo server；若省略: 无法确认路由到 demo client
        )  # 新增代码+MCP 工具注册表健壮性: demo fake client 构造完成；若省略: 注册表没有 demo client 可用
        other_client = FakeMcpClient(result_prefix="other")  # 新增代码+MCP 工具注册表健壮性: 创建第二个 server 的默认 echo client；若省略: 无法覆盖多 server
        registry = McpToolRegistry({"demo": demo_client, "中文 server": other_client})  # 新增代码+MCP 工具注册表健壮性: 构造包含特殊 server 名和多 server 的注册表；若省略: server 名 sanitize 和多 server 不会被验证
        registry.start()  # 新增代码+MCP 工具注册表健壮性: 启动并转换所有工具；若省略: schema 和 route 都为空
        names = [schema["function"]["name"] for schema in registry.tool_schemas()]  # 新增代码+MCP 工具注册表健壮性: 收集转换后的函数名；若省略: 无法断言命名结果
        self.assertEqual(names, ["mcp__demo__a_b", "mcp__demo__a_b_2", "mcp__demo__tool", "mcp__server__echo"])  # 修改代码+MCP 工具注册表健壮性: 断言冲突递增、非 ASCII 清理和多 server 命名；若省略: 命名规则回归不会被发现
        self.assertEqual(registry.call_tool("mcp__demo__a_b", {"text": "first"}), "demo a/b: first")  # 新增代码+MCP 工具注册表健壮性: 断言第一个冲突名路由到原始 a/b；若省略: route 与 schema 不一致不会被发现
        self.assertEqual(registry.call_tool("mcp__demo__a_b_2", {"text": "second"}), "demo a b: second")  # 新增代码+MCP 工具注册表健壮性: 断言第二个唯一名路由到原始 a b；若省略: 冲突工具可能错误覆盖前一个路由
        self.assertEqual(registry.call_tool("mcp__server__echo", {"text": "third"}), "other echo: third")  # 新增代码+MCP 工具注册表健壮性: 断言特殊 server 名清理后仍路由到第二个 client；若省略: 多 server 路由错误不会被发现
    def test_mcp_tool_registry_handles_invalid_input_schema_and_unknown_tool(self) -> None:  # 新增代码+MCP 工具注册表健壮性: 验证坏 inputSchema 兜底和未知工具错误可读；若省略: 异常 MCP server 输出会破坏模型 schema
        fake_client = FakeMcpClient(  # 新增代码+MCP 工具注册表健壮性: 创建返回坏 inputSchema 的 fake client；若省略: 无法覆盖非 dict schema 场景
            tools=[{"name": "bad", "description": "Bad schema", "inputSchema": "not a dict"}]  # 新增代码+MCP 工具注册表健壮性: inputSchema 故意使用字符串；若省略: 兜底 object schema 不会被测试
        )  # 新增代码+MCP 工具注册表健壮性: fake client 构造结束；若省略: 注册表没有测试 client
        registry = McpToolRegistry({"demo": fake_client})  # 新增代码+MCP 工具注册表健壮性: 构造注册表；若省略: 无法执行 schema 转换
        registry.start()  # 新增代码+MCP 工具注册表健壮性: 启动并转换坏 schema 工具；若省略: tool_schemas 为空
        schemas = registry.tool_schemas()  # 新增代码+MCP 工具注册表健壮性: 读取转换结果；若省略: 无法检查兜底 schema
        self.assertEqual(schemas[0]["function"]["parameters"], {"type": "object"})  # 新增代码+MCP 工具注册表健壮性: 断言非 dict inputSchema 兜底为空对象 schema；若省略: 坏 schema 可能进入模型接口
        with self.assertRaisesRegex(RuntimeError, "未知 MCP 工具：mcp__demo__missing"):  # 新增代码+MCP 工具注册表健壮性: 断言未知工具报错包含工具名；若省略: 可读错误回归不会被发现
            registry.call_tool("mcp__demo__missing", {})  # 新增代码+MCP 工具注册表健壮性: 调用不存在工具触发错误；若省略: 未知工具分支无法覆盖
    def test_mcp_tool_registry_returns_deep_copied_schemas(self) -> None:  # 新增代码+MCP 工具注册表健壮性: 验证 tool_schemas 和缓存 inputSchema 都是深拷贝；若省略: 调用方修改 schema 会污染注册表
        tools = FakeMcpClient()._default_tools()  # 新增代码+MCP 工具注册表健壮性: 获取可变的默认工具定义；若省略: 无法模拟 MCP 原始 schema 后续被外部修改
        fake_client = FakeMcpClient(tools=tools)  # 新增代码+MCP 工具注册表健壮性: 把可变工具传入 fake client；若省略: 注册表无法读取这份可变 inputSchema
        registry = McpToolRegistry({"demo": fake_client})  # 新增代码+MCP 工具注册表健壮性: 构造注册表；若省略: 无法测试深拷贝行为
        registry.start()  # 新增代码+MCP 工具注册表健壮性: 启动并缓存 schema；若省略: 没有缓存可供污染测试
        first_schemas = registry.tool_schemas()  # 新增代码+MCP 工具注册表健壮性: 第一次读取 schema 副本；若省略: 无法模拟调用方污染返回值
        first_schemas[0]["function"]["parameters"]["properties"]["text"]["type"] = "number"  # 新增代码+MCP 工具注册表健壮性: 修改返回副本的嵌套字段；若省略: 深拷贝防护无法被验证
        tools[0]["inputSchema"]["properties"]["text"]["type"] = "boolean"  # 新增代码+MCP 工具注册表健壮性: 修改原始 MCP inputSchema 的嵌套字段；若省略: start 时保存 inputSchema 深拷贝无法被验证
        second_schemas = registry.tool_schemas()  # 新增代码+MCP 工具注册表健壮性: 再次读取 schema；若省略: 无法判断内部缓存是否被污染
        self.assertEqual(second_schemas[0]["function"]["parameters"]["properties"]["text"]["type"], "string")  # 新增代码+MCP 工具注册表健壮性: 断言内部缓存仍保持原始 string；若省略: 嵌套污染不会被发现
    def test_mcp_stdio_client_lists_and_calls_tools(self) -> None:  # 新增代码+MCP stdio client: 验证最小 MCP stdio 客户端能列工具并调用工具；若省略: 客户端协议行为没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP stdio client: 创建临时目录隔离 fake server 文件；若省略: 测试会污染真实项目目录
            server_script = Path(raw_dir) / "fake_mcp_server.py"  # 新增代码+MCP stdio client: 定位临时 fake MCP server 脚本；若省略: 子进程没有可执行测试服务器
            server_script.write_text(  # 新增代码+MCP stdio client: 写入最小 fake MCP server 代码；若省略: 客户端无法连接到可控 MCP 服务
                """import json  # 新增代码+MCP stdio client: 导入 JSON 模块解析单行 JSON-RPC；若省略: fake server 无法读写 MCP 消息
import sys  # 新增代码+MCP stdio client: 导入 sys 以访问标准输入输出；若省略: fake server 无法通过 stdio 通信

for raw_line in sys.stdin:  # 新增代码+MCP stdio client: 逐行读取客户端请求；若省略: fake server 不会响应任何 MCP 消息
    message = json.loads(raw_line)  # 新增代码+MCP stdio client: 将 JSON-RPC 文本解析为字典；若省略: fake server 无法判断请求方法
    method = message.get("method")  # 新增代码+MCP stdio client: 取出请求方法名；若省略: fake server 无法分派 initialize/tools 调用
    if method == "notifications/initialized":  # 新增代码+MCP stdio client: 忽略初始化完成通知；若省略: 通知可能被当成未知请求错误处理
        continue  # 新增代码+MCP stdio client: 通知不需要响应；若省略: fake server 会错误地给 notification 回包
    request_id = message.get("id")  # 新增代码+MCP stdio client: 保存请求 id 以便响应匹配；若省略: 客户端无法确认响应属于哪个请求
    if method == "initialize":  # 新增代码+MCP stdio client: 处理 MCP initialize 请求；若省略: 客户端启动握手会失败
        response = {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "fake", "version": "0.1"}}}  # 新增代码+MCP stdio client: 返回最小初始化结果；若省略: 客户端无法进入可用状态
    elif method == "tools/list":  # 新增代码+MCP stdio client: 处理工具列表请求；若省略: list_tools 无法得到 echo 工具
        response = {"jsonrpc": "2.0", "id": request_id, "result": {"tools": [{"name": "echo", "description": "Echo text", "inputSchema": {"type": "object"}}]}}  # 新增代码+MCP stdio client: 返回一个 echo 工具；若省略: 测试无法断言工具名
    elif method == "tools/call":  # 新增代码+MCP stdio client: 处理工具调用请求；若省略: call_tool 无法验证结果转换
        text = message.get("params", {}).get("arguments", {}).get("text", "")  # 新增代码+MCP stdio client: 读取 echo 文本参数；若省略: fake server 无法返回用户传入内容
        response = {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": f"echo: {text}"}]}}  # 新增代码+MCP stdio client: 返回 MCP 文本 content；若省略: 客户端无法测试文本提取
    else:  # 新增代码+MCP stdio client: 兜底处理未知方法；若省略: 新请求出错时 fake server 行为不清晰
        response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown method"}}  # 新增代码+MCP stdio client: 返回 JSON-RPC 未知方法错误；若省略: 客户端可能一直等待
    sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\\n")  # 新增代码+MCP stdio client: 输出一行 JSON-RPC 响应；若省略: 客户端读不到服务端返回
    sys.stdout.flush()  # 新增代码+MCP stdio client: 立即刷新 stdout；若省略: 响应可能停留在缓冲区导致测试卡住
""",  # 新增代码+MCP stdio client: 结束 fake server 脚本文本；若省略: 测试文件语法不完整
                encoding="utf-8",  # 新增代码+MCP stdio client: 使用 UTF-8 写入中文参数脚本；若省略: Windows 默认编码可能破坏中文
            )  # 新增代码+MCP stdio client: 完成 fake server 写入；若省略: 后续启动脚本时文件内容可能未准备好
            client = McpStdioClient(McpServerConfig(name="demo", command=sys.executable, args=[str(server_script)]))  # 新增代码+MCP stdio client: 用当前 Python 启动 fake MCP server；若省略: 无法实例化被测客户端
            try:  # 新增代码+MCP stdio client: 确保测试失败时也关闭子进程；若省略: 失败可能遗留后台进程
                client.start()  # 新增代码+MCP stdio client: 启动子进程并完成 initialize 握手；若省略: list_tools 没有可通信进程
                tools = client.list_tools()  # 新增代码+MCP stdio client: 请求 MCP 工具列表；若省略: 无法验证 tools/list 行为
                self.assertEqual(tools[0]["name"], "echo")  # 新增代码+MCP stdio client: 断言第一个工具名是 echo；若省略: 工具列表解析错误不会被发现
                result = client.call_tool("echo", {"text": "你好"})  # 新增代码+MCP stdio client: 调用 echo 工具并传入中文参数；若省略: 无法验证 tools/call 和中文传输
                self.assertIn("echo: 你好", result)  # 新增代码+MCP stdio client: 断言 MCP 文本结果被提取出来；若省略: 结果转换错误不会被发现
            finally:  # 新增代码+MCP stdio client: 无论断言是否失败都执行清理；若省略: 子进程可能残留
                client.close()  # 新增代码+MCP stdio client: 关闭 fake MCP server 子进程；若省略: 测试会泄漏进程资源
    def test_mcp_stdio_client_lists_and_reads_resources(self) -> None:  # 新增代码+MCPResource: 验证 stdio client 支持 resources/list 和 resources/read；若省略: MCP resources 底层协议缺口不会被测试发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCPResource: 创建临时目录隔离 fake resources server；若省略: 测试会污染真实项目目录
            server_script = Path(raw_dir) / "resource_mcp_server.py"  # 新增代码+MCPResource: 定义 fake MCP resource server 脚本路径；若省略: 客户端没有可启动的测试目标
            server_script.write_text(  # 新增代码+MCPResource: 写入能响应 resources/list/read 的最小 MCP server；若省略: stdio client 无法进行端到端资源读取测试
                """import json  # 新增代码+MCPResource: 导入 JSON 模块解析和输出 JSON-RPC；若省略: fake server 无法读写 MCP 消息
import sys  # 新增代码+MCPResource: 导入 sys 使用标准输入输出；若省略: fake server 无法通过 stdio 通信

for raw_line in sys.stdin:  # 新增代码+MCPResource: 逐行读取客户端请求；若省略: fake server 不会收到任何 MCP 消息
    message = json.loads(raw_line)  # 新增代码+MCPResource: 把请求文本解析成字典；若省略: fake server 无法判断 method 和 id
    method = message.get("method")  # 新增代码+MCPResource: 读取 JSON-RPC method；若省略: fake server 无法区分初始化、列资源和读资源
    if method == "notifications/initialized":  # 新增代码+MCPResource: 忽略 initialized 通知；若省略: fake server 可能错误地给 notification 返回响应
        continue  # 新增代码+MCPResource: notification 不需要响应；若省略: 客户端可能读到多余消息
    request_id = message.get("id")  # 新增代码+MCPResource: 保存请求 id 用于匹配响应；若省略: 客户端无法确认响应对应哪个请求
    if method == "initialize":  # 新增代码+MCPResource: 处理 MCP 初始化请求；若省略: 客户端 start 无法完成握手
        response = {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"resources": {}}, "serverInfo": {"name": "fake-resource", "version": "0.1"}}}  # 新增代码+MCPResource: 返回支持 resources 的初始化结果；若省略: fake server 不像真实资源 server
    elif method == "resources/list":  # 新增代码+MCPResource: 处理资源列表请求；若省略: client.list_resources 没有可验证响应
        response = {"jsonrpc": "2.0", "id": request_id, "result": {"resources": [{"uri": "file://guide.md", "name": "Guide", "mimeType": "text/markdown", "description": "Project guide"}]}}  # 新增代码+MCPResource: 返回一个可断言的资源条目；若省略: 列表解析没有目标数据
    elif method == "resources/read":  # 新增代码+MCPResource: 处理资源读取请求；若省略: client.read_resource 没有可验证响应
        uri = message.get("params", {}).get("uri", "")  # 新增代码+MCPResource: 读取客户端传来的 uri；若省略: 测试无法证明 uri 被正确发送
        response = {"jsonrpc": "2.0", "id": request_id, "result": {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": "resource text for " + uri}]}}  # 新增代码+MCPResource: 返回 MCP resources/read 标准 contents 文本；若省略: 文本提取逻辑没有输入
    else:  # 新增代码+MCPResource: 兜底处理未知方法；若省略: 新请求出错时 fake server 行为不清楚
        response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown method"}}  # 新增代码+MCPResource: 返回标准 JSON-RPC 未知方法错误；若省略: 客户端可能一直等待
    sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\\n")  # 新增代码+MCPResource: 输出单行 JSON-RPC 响应；若省略: 客户端读不到返回值
    sys.stdout.flush()  # 新增代码+MCPResource: 立即刷新 stdout；若省略: 响应可能留在缓冲区导致测试超时
""",  # 新增代码+MCPResource: fake server 源码字符串结束；若省略: 测试文件语法不完整
                encoding="utf-8",  # 新增代码+MCPResource: 使用 UTF-8 写入脚本；若省略: Windows 默认编码可能破坏中文注释或内容
            )  # 新增代码+MCPResource: 完成 fake server 写入；若省略: 子进程启动时脚本可能不存在
            client = McpStdioClient(McpServerConfig(name="docs", command=sys.executable, args=[str(server_script)]))  # 新增代码+MCPResource: 创建被测 stdio client；若省略: 无法调用 resources/list/read
            try:  # 新增代码+MCPResource: 确保测试结束后关闭 client；若省略: 失败时可能残留子进程
                client.start()  # 新增代码+MCPResource: 完成 MCP initialize 握手；若省略: resources/list/read 没有可用连接
                resources = client.list_resources()  # 新增代码+MCPResource: 调用新增资源列表接口；若省略: 无法验证 resources/list 路径
                self.assertEqual(resources[0]["uri"], "file://guide.md")  # 新增代码+MCPResource: 断言资源 uri 被正确解析；若省略: 列表结果格式错误不会被发现
                self.assertEqual(resources[0]["name"], "Guide")  # 新增代码+MCPResource: 断言资源名称保留；若省略: 模型后续选择资源缺少可读名称的问题不会暴露
                text = client.read_resource("file://guide.md")  # 新增代码+MCPResource: 调用新增资源读取接口；若省略: 无法验证 resources/read 路径
                self.assertIn("resource text for file://guide.md", text)  # 新增代码+MCPResource: 断言 contents[].text 被提取；若省略: read_resource 可能只返回 JSON 或空文本
            finally:  # 新增代码+MCPResource: 无论断言是否失败都清理 client；若省略: fake MCP server 可能残留
                client.close()  # 新增代码+MCPResource: 关闭 MCP 子进程；若省略: 测试会泄漏进程资源
    def test_mcp_tool_registry_lists_and_reads_resources(self) -> None:  # 新增代码+MCPResource: 验证 registry 能按 server 暴露和读取 MCP resources；若省略: 上层无法知道资源来自哪个 MCP server
        fake_client = FakeMcpClient(resources=[{"uri": "file://guide.md", "name": "Guide", "mimeType": "text/markdown", "description": "Project guide"}], resource_text="guide body")  # 新增代码+MCPResource: 创建含一个 resource 的 fake client；若省略: registry 没有可测试资源
        registry = McpToolRegistry({"docs": fake_client})  # 新增代码+MCPResource: 创建带 docs server 的注册表；若省略: list_resources/read_resource 没有 server 路由
        registry.start()  # 新增代码+MCPResource: 启动 registry，让它进入可用状态；若省略: 资源读取语义无法和工具发现生命周期对齐
        resources = registry.list_resources()  # 新增代码+MCPResource: 读取全部 server 的资源列表；若省略: 无法验证资源发现聚合
        self.assertEqual(resources[0]["server"], "docs")  # 新增代码+MCPResource: 断言资源条目带 server 名；若省略: 后续 read_resource 无法定位来源
        self.assertEqual(resources[0]["uri"], "file://guide.md")  # 新增代码+MCPResource: 断言资源 uri 被保留；若省略: 资源读取目标可能丢失
        self.assertIn("guide body: file://guide.md", registry.read_resource("docs", "file://guide.md"))  # 新增代码+MCPResource: 断言读取请求被转发到正确 client；若省略: registry 路由错误不会被发现
        self.assertEqual(fake_client.resource_reads, ["file://guide.md"])  # 新增代码+MCPResource: 断言 fake client 收到正确 uri；若省略: read_resource 可能调用了错误参数
    def test_mcp_stdio_client_lists_and_reads_prompts(self) -> None:  # 新增代码+MCPPrompt: 验证 stdio client 支持 prompts/list 和 prompts/get；若省略: MCP prompts 底层协议缺口不会被测试发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCPPrompt: 创建临时目录隔离 fake prompts server；若省略: 测试会污染真实项目目录
            server_script = Path(raw_dir) / "prompt_mcp_server.py"  # 新增代码+MCPPrompt: 定义 fake MCP prompt server 脚本路径；若省略: 客户端没有可启动的测试目标
            server_script.write_text(  # 新增代码+MCPPrompt: 写入能响应 prompts/list/get 的最小 MCP server；若省略: stdio client 无法进行端到端 prompt 读取测试
                """import json  # 新增代码+MCPPrompt: 导入 JSON 模块解析和输出 JSON-RPC；若省略: fake server 无法读写 MCP 消息
import sys  # 新增代码+MCPPrompt: 导入 sys 使用标准输入输出；若省略: fake server 无法通过 stdio 通信

for raw_line in sys.stdin:  # 新增代码+MCPPrompt: 逐行读取客户端请求；若省略: fake server 不会收到任何 MCP 消息
    message = json.loads(raw_line)  # 新增代码+MCPPrompt: 把请求文本解析成字典；若省略: fake server 无法判断 method 和 id
    method = message.get("method")  # 新增代码+MCPPrompt: 读取 JSON-RPC method；若省略: fake server 无法区分初始化、列 prompt 和读 prompt
    if method == "notifications/initialized":  # 新增代码+MCPPrompt: 忽略 initialized 通知；若省略: fake server 可能错误地给 notification 返回响应
        continue  # 新增代码+MCPPrompt: notification 不需要响应；若省略: 客户端可能读到多余消息
    request_id = message.get("id")  # 新增代码+MCPPrompt: 保存请求 id 用于匹配响应；若省略: 客户端无法确认响应对应哪个请求
    if method == "initialize":  # 新增代码+MCPPrompt: 处理 MCP 初始化请求；若省略: 客户端 start 无法完成握手
        response = {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"prompts": {}}, "serverInfo": {"name": "fake-prompt", "version": "0.1"}}}  # 新增代码+MCPPrompt: 返回支持 prompts 的初始化结果；若省略: fake server 不像真实 prompts server
    elif method == "prompts/list":  # 新增代码+MCPPrompt: 处理 prompt 列表请求；若省略: client.list_prompts 没有可验证响应
        response = {"jsonrpc": "2.0", "id": request_id, "result": {"prompts": [{"name": "plan_brief", "description": "Create a bounded plan brief", "arguments": [{"name": "topic", "description": "Brief topic", "required": True}]}]}}  # 新增代码+MCPPrompt: 返回一个可断言的 prompt 条目；若省略: 列表解析没有目标数据
    elif method == "prompts/get":  # 新增代码+MCPPrompt: 处理 prompt 读取请求；若省略: client.get_prompt 没有可验证响应
        params = message.get("params", {})  # 新增代码+MCPPrompt: 读取客户端传来的 params；若省略: 测试无法证明 name 和 arguments 被正确发送
        name = params.get("name", "")  # 新增代码+MCPPrompt: 读取 prompt 名称；若省略: fake server 无法把目标 prompt 写入结果
        topic = params.get("arguments", {}).get("topic", "")  # 新增代码+MCPPrompt: 读取 prompt 参数 topic；若省略: fake server 无法验证 arguments 传输
        response = {"jsonrpc": "2.0", "id": request_id, "result": {"description": "Create a bounded plan brief", "messages": [{"role": "user", "content": {"type": "text", "text": "Prompt " + name + " for " + topic}}]}}  # 新增代码+MCPPrompt: 返回 MCP prompts/get 标准 messages 文本；若省略: 文本提取逻辑没有输入
    else:  # 新增代码+MCPPrompt: 兜底处理未知方法；若省略: 新请求出错时 fake server 行为不清楚
        response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown method"}}  # 新增代码+MCPPrompt: 返回标准 JSON-RPC 未知方法错误；若省略: 客户端可能一直等待
    sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\\n")  # 新增代码+MCPPrompt: 输出单行 JSON-RPC 响应；若省略: 客户端读不到返回值
    sys.stdout.flush()  # 新增代码+MCPPrompt: 立即刷新 stdout；若省略: 响应可能留在缓冲区导致测试超时
""",  # 新增代码+MCPPrompt: fake server 源码字符串结束；若省略: 测试文件语法不完整
                encoding="utf-8",  # 新增代码+MCPPrompt: 使用 UTF-8 写入脚本；若省略: Windows 默认编码可能破坏中文注释或内容
            )  # 新增代码+MCPPrompt: 完成 fake server 写入；若省略: 子进程启动时脚本可能不存在
            client = McpStdioClient(McpServerConfig(name="docs", command=sys.executable, args=[str(server_script)]))  # 新增代码+MCPPrompt: 创建被测 stdio client；若省略: 无法调用 prompts/list/get
            try:  # 新增代码+MCPPrompt: 确保测试结束后关闭 client；若省略: 失败时可能残留子进程
                client.start()  # 新增代码+MCPPrompt: 完成 MCP initialize 握手；若省略: prompts/list/get 没有可用连接
                prompts = client.list_prompts()  # 新增代码+MCPPrompt: 调用新增 prompt 列表接口；若省略: 无法验证 prompts/list 路径
                self.assertEqual(prompts[0]["name"], "plan_brief")  # 新增代码+MCPPrompt: 断言 prompt 名称被正确解析；若省略: 列表结果格式错误不会被发现
                self.assertEqual(prompts[0]["arguments"][0]["name"], "topic")  # 新增代码+MCPPrompt: 断言 prompt 参数元信息保留；若省略: 模型后续不知道如何传 prompt_arguments
                text = client.get_prompt("plan_brief", {"topic": "MCP prompts"})  # 新增代码+MCPPrompt: 调用新增 prompt 读取接口；若省略: 无法验证 prompts/get 路径
                self.assertIn("Prompt plan_brief for MCP prompts", text)  # 新增代码+MCPPrompt: 断言 messages[].content.text 被提取；若省略: get_prompt 可能只返回 JSON 或空文本
            finally:  # 新增代码+MCPPrompt: 无论断言是否失败都清理 client；若省略: fake MCP server 可能残留
                client.close()  # 新增代码+MCPPrompt: 关闭 MCP 子进程；若省略: 测试会泄漏进程资源
    def test_mcp_tool_registry_lists_and_reads_prompts(self) -> None:  # 新增代码+MCPPrompt: 验证 registry 能按 server 暴露和读取 MCP prompts；若省略: 上层无法知道 prompt 来自哪个 MCP server
        fake_client = FakeMcpClient(prompts=[{"name": "plan_brief", "description": "Create a bounded plan brief", "arguments": [{"name": "topic", "required": True}]}], prompt_text="prompt body")  # 新增代码+MCPPrompt: 创建含一个 prompt 的 fake client；若省略: registry 没有可测试 prompt
        registry = McpToolRegistry({"docs": fake_client})  # 新增代码+MCPPrompt: 创建带 docs server 的注册表；若省略: list_prompts/read_prompt 没有 server 路由
        registry.start()  # 新增代码+MCPPrompt: 启动 registry，让 prompts 语义和工具发现生命周期对齐；若省略: 测试不能证明启动后可读 prompt
        prompts = registry.list_prompts()  # 新增代码+MCPPrompt: 读取全部 server 的 prompt 列表；若省略: 无法验证 prompt 发现聚合
        self.assertEqual(prompts[0]["server"], "docs")  # 新增代码+MCPPrompt: 断言 prompt 条目带 server 名；若省略: 后续 read_prompt 无法定位来源
        self.assertEqual(prompts[0]["name"], "plan_brief")  # 新增代码+MCPPrompt: 断言 prompt 名称被保留；若省略: prompt 读取目标可能丢失
        self.assertIn("prompt body: plan_brief MCP", registry.read_prompt("docs", "plan_brief", {"topic": "MCP"}))  # 新增代码+MCPPrompt: 断言读取请求被转发到正确 client；若省略: registry 路由错误不会被发现
        self.assertEqual(fake_client.prompt_reads, [("plan_brief", {"topic": "MCP"})])  # 新增代码+MCPPrompt: 断言 fake client 收到正确 name 和 arguments；若省略: read_prompt 可能调用了错误参数
    def test_mcp_stdio_client_raises_when_server_returns_error(self) -> None:  # 新增代码+MCP stdio client 健壮性: 验证 JSON-RPC error 会变成清晰异常；若省略: server 报错时客户端可能误判成功
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP stdio client 健壮性: 创建临时目录保存 fake server；若省略: 测试会污染真实工作区
            server_script = Path(raw_dir) / "error_mcp_server.py"  # 新增代码+MCP stdio client 健壮性: 定义返回错误的 fake server 路径；若省略: 子进程没有脚本可运行
            server_script.write_text(  # 新增代码+MCP stdio client 健壮性: 写入返回 JSON-RPC error 的 server；若省略: 无法覆盖错误响应路径
                """import json  # 新增代码+MCP stdio client 健壮性: 导入 JSON 解析和输出消息；若省略: fake server 无法处理 JSON-RPC
import sys  # 新增代码+MCP stdio client 健壮性: 导入 sys 使用标准输入输出；若省略: fake server 无法 stdio 通信

for raw_line in sys.stdin:  # 新增代码+MCP stdio client 健壮性: 逐行读取客户端消息；若省略: fake server 不会收到请求
    message = json.loads(raw_line)  # 新增代码+MCP stdio client 健壮性: 解析请求 JSON；若省略: fake server 无法判断方法
    method = message.get("method")  # 新增代码+MCP stdio client 健壮性: 获取 JSON-RPC 方法；若省略: 无法区分 initialize 和 tools/list
    if method == "notifications/initialized":  # 新增代码+MCP stdio client 健壮性: 忽略初始化完成通知；若省略: fake server 可能错误响应 notification
        continue  # 新增代码+MCP stdio client 健壮性: notification 不回包；若省略: 客户端可能读到无关响应
    request_id = message.get("id")  # 新增代码+MCP stdio client 健壮性: 取请求 id 用于响应匹配；若省略: 客户端无法匹配响应
    if method == "initialize":  # 新增代码+MCP stdio client 健壮性: initialize 仍然成功；若省略: 测试到不了 tools/list 错误路径
        response = {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {}}}  # 新增代码+MCP stdio client 健壮性: 返回最小初始化成功结果；若省略: client.start 会失败
    else:  # 新增代码+MCP stdio client 健壮性: 其他请求统一返回错误；若省略: tools/list 不会触发错误路径
        response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": "boom"}}  # 新增代码+MCP stdio client 健壮性: 构造 JSON-RPC error；若省略: 客户端错误处理无法被验证
    sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\\n")  # 新增代码+MCP stdio client 健壮性: 输出单行响应；若省略: 客户端会等待响应
    sys.stdout.flush()  # 新增代码+MCP stdio client 健壮性: 刷新响应；若省略: 响应可能留在缓冲区
""",  # 新增代码+MCP stdio client 健壮性: 结束 fake server 源码字符串；若省略: 测试语法不完整
                encoding="utf-8",  # 新增代码+MCP stdio client 健壮性: 用 UTF-8 写脚本；若省略: 跨平台编码不稳定
            )  # 新增代码+MCP stdio client 健壮性: 完成脚本写入；若省略: 子进程可能读取空文件
            client = McpStdioClient(McpServerConfig(name="demo", command=sys.executable, args=[str(server_script)]))  # 新增代码+MCP stdio client 健壮性: 创建被测客户端；若省略: 无法执行错误路径
            try:  # 新增代码+MCP stdio client 健壮性: 确保异常后关闭客户端；若省略: 失败时可能泄漏子进程
                client.start()  # 新增代码+MCP stdio client 健壮性: 完成初始化握手；若省略: list_tools 前没有连接
                with self.assertRaisesRegex(RuntimeError, "boom"):  # 新增代码+MCP stdio client 健壮性: 断言错误消息包含 server 原因；若省略: 异常不清晰也不会被发现
                    client.list_tools()  # 新增代码+MCP stdio client 健壮性: 触发 tools/list 错误响应；若省略: 测试没有实际行为
            finally:  # 新增代码+MCP stdio client 健壮性: 无论是否失败都清理；若省略: 可能残留进程
                client.close()  # 新增代码+MCP stdio client 健壮性: 关闭 fake server；若省略: 测试会泄漏资源
    def test_mcp_stdio_client_raises_when_server_exits_without_response(self) -> None:  # 新增代码+MCP stdio client 健壮性: 验证 stdout 关闭时抛清晰异常；若省略: server 退出可能被误当成空结果
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP stdio client 健壮性: 创建临时目录保存退出脚本；若省略: 测试会影响真实文件
            server_script = Path(raw_dir) / "exit_mcp_server.py"  # 新增代码+MCP stdio client 健壮性: 定义会提前退出的 fake server；若省略: 无法模拟 stdout 关闭
            server_script.write_text(  # 新增代码+MCP stdio client 健壮性: 写入 initialize 后退出的 server；若省略: 无法覆盖进程退出路径
                """import json  # 新增代码+MCP stdio client 健壮性: 导入 JSON 处理请求响应；若省略: fake server 无法输出 JSON-RPC
import sys  # 新增代码+MCP stdio client 健壮性: 导入 sys 使用 stdio；若省略: fake server 无法通信

for raw_line in sys.stdin:  # 新增代码+MCP stdio client 健壮性: 读取客户端消息；若省略: fake server 无法握手
    message = json.loads(raw_line)  # 新增代码+MCP stdio client 健壮性: 解析 JSON-RPC 请求；若省略: 无法读取方法和 id
    if message.get("method") == "initialize":  # 新增代码+MCP stdio client 健壮性: 只响应初始化；若省略: client.start 无法成功
        response = {"jsonrpc": "2.0", "id": message.get("id"), "result": {"protocolVersion": "2024-11-05", "capabilities": {}}}  # 新增代码+MCP stdio client 健壮性: 返回初始化成功；若省略: 测试不到后续退出路径
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\\n")  # 新增代码+MCP stdio client 健壮性: 写出初始化响应；若省略: 客户端会等不到握手
        sys.stdout.flush()  # 新增代码+MCP stdio client 健壮性: 刷新初始化响应；若省略: 响应可能卡在缓冲区
        break  # 新增代码+MCP stdio client 健壮性: 初始化后退出循环；若省略: server 不会退出
""",  # 新增代码+MCP stdio client 健壮性: 结束 fake server 源码字符串；若省略: 测试语法不完整
                encoding="utf-8",  # 新增代码+MCP stdio client 健壮性: 用 UTF-8 写脚本；若省略: 编码可能不一致
            )  # 新增代码+MCP stdio client 健壮性: 完成脚本写入；若省略: 子进程无可执行内容
            client = McpStdioClient(McpServerConfig(name="demo", command=sys.executable, args=[str(server_script)]))  # 新增代码+MCP stdio client 健壮性: 创建被测客户端；若省略: 无法触发退出场景
            try:  # 新增代码+MCP stdio client 健壮性: 确保测试后关闭客户端；若省略: 子进程资源可能残留
                client.start()  # 新增代码+MCP stdio client 健壮性: 完成初始化，随后 server 退出；若省略: 无法进入 stdout 关闭场景
                with self.assertRaisesRegex(RuntimeError, "stdout closed|已关闭"):  # 新增代码+MCP stdio client 健壮性: 断言 stdout 关闭错误清晰；若省略: 异常内容退化不会被发现
                    client.list_tools()  # 新增代码+MCP stdio client 健壮性: server 已退出后请求工具列表；若省略: 不会触发读取关闭管道
            finally:  # 新增代码+MCP stdio client 健壮性: 无论测试结果如何都清理；若省略: 资源可能泄漏
                client.close()  # 新增代码+MCP stdio client 健壮性: 关闭客户端；若省略: 管道句柄可能残留
    def test_mcp_result_to_text_handles_non_text_and_empty_content(self) -> None:  # 新增代码+MCP stdio client 健壮性: 验证非文本和空 content 的结果转换；若省略: 工具返回边界格式可能丢失
        client = McpStdioClient(McpServerConfig(name="demo", command=sys.executable))  # 新增代码+MCP stdio client 健壮性: 创建无需启动的客户端用于测试纯转换函数；若省略: 无法调用结果转换逻辑
        non_text = client._mcp_result_to_text({"content": [{"type": "image", "data": "abc"}]})  # 新增代码+MCP stdio client 健壮性: 转换非文本 content；若省略: JSON 兜底路径没有测试覆盖
        self.assertIn('"type": "image"', non_text)  # 新增代码+MCP stdio client 健壮性: 断言非文本 content 用 JSON 表示；若省略: 非文本结果丢失不会被发现
        empty = client._mcp_result_to_text({"content": []})  # 新增代码+MCP stdio client 健壮性: 转换空 content；若省略: 空 content 边界没有测试覆盖
        self.assertIn('"content": []', empty)  # 新增代码+MCP stdio client 健壮性: 断言空 content 返回完整 JSON；若省略: 空结果被错误变空字符串不会被发现
    def test_mcp_stdio_client_times_out_when_server_does_not_respond(self) -> None:  # 新增代码+MCP stdio client 健壮性: 验证 server 不响应时请求会超时退出；若省略: 客户端可能无限阻塞
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP stdio client 健壮性: 创建临时目录保存沉默 server；若省略: 测试会污染项目目录
            server_script = Path(raw_dir) / "silent_mcp_server.py"  # 新增代码+MCP stdio client 健壮性: 定义不响应工具请求的 fake server；若省略: 无法模拟卡住场景
            server_script.write_text(  # 新增代码+MCP stdio client 健壮性: 写入初始化后沉默的 server；若省略: 无法验证超时逻辑
                """import json  # 新增代码+MCP stdio client 健壮性: 导入 JSON 处理初始化响应；若省略: fake server 无法握手
import sys  # 新增代码+MCP stdio client 健壮性: 导入 sys 使用标准输入输出；若省略: fake server 无法 stdio 通信
import time  # 新增代码+MCP stdio client 健壮性: 导入 time 让 server 保持运行但不响应；若省略: 无法模拟无限等待

for raw_line in sys.stdin:  # 新增代码+MCP stdio client 健壮性: 逐行读取客户端消息；若省略: fake server 不会收到请求
    message = json.loads(raw_line)  # 新增代码+MCP stdio client 健壮性: 解析 JSON-RPC 消息；若省略: fake server 无法判断方法
    if message.get("method") == "notifications/initialized":  # 新增代码+MCP stdio client 健壮性: 忽略初始化完成通知；若省略: 通知可能干扰后续逻辑
        continue  # 新增代码+MCP stdio client 健壮性: notification 不响应；若省略: 客户端可能读到多余响应
    if message.get("method") == "initialize":  # 新增代码+MCP stdio client 健壮性: initialize 正常响应；若省略: 超时会发生在 start 而不是 list_tools
        response = {"jsonrpc": "2.0", "id": message.get("id"), "result": {"protocolVersion": "2024-11-05", "capabilities": {}}}  # 新增代码+MCP stdio client 健壮性: 返回初始化成功；若省略: 客户端不能进入工具请求阶段
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\\n")  # 新增代码+MCP stdio client 健壮性: 写出初始化响应；若省略: start 会等待
        sys.stdout.flush()  # 新增代码+MCP stdio client 健壮性: 刷新初始化响应；若省略: 响应可能留在缓冲区
    else:  # 新增代码+MCP stdio client 健壮性: 工具请求进入沉默分支；若省略: 无法模拟不响应
        time.sleep(10)  # 新增代码+MCP stdio client 健壮性: 长时间睡眠模拟 server 卡住；若省略: 测试无法证明客户端有超时保护
""",  # 新增代码+MCP stdio client 健壮性: 结束 fake server 源码字符串；若省略: 测试语法不完整
                encoding="utf-8",  # 新增代码+MCP stdio client 健壮性: 用 UTF-8 写脚本；若省略: 编码不稳定
            )  # 新增代码+MCP stdio client 健壮性: 完成沉默 server 写入；若省略: 子进程无法启动
            client = McpStdioClient(McpServerConfig(name="demo", command=sys.executable, args=[str(server_script)]), request_timeout_seconds=0.5)  # 修改代码+MCP超时测试稳定性: 用仍然很短但足够完成 Windows Python 初始化的超时；若继续使用 0.2 秒: 测试可能在 initialize 阶段误超时而不是验证 tools/list 超时
            try:  # 新增代码+MCP stdio client 健壮性: 确保超时后也执行清理；若省略: 沉默 server 可能残留
                client.start()  # 新增代码+MCP stdio client 健壮性: 先完成正常初始化；若省略: 无法验证 list_tools 的超时
                started_at = time.monotonic()  # 新增代码+MCP stdio client 健壮性: 记录请求开始时间；若省略: 无法断言不会长时间卡住
                with self.assertRaisesRegex(RuntimeError, "超时"):  # 新增代码+MCP stdio client 健壮性: 断言不响应会抛超时异常；若省略: 无限阻塞风险不会被测试保护
                    client.list_tools()  # 新增代码+MCP stdio client 健壮性: 触发不会响应的 tools/list；若省略: 测试没有卡住路径
                self.assertLess(time.monotonic() - started_at, 2.0)  # 新增代码+MCP stdio client 健壮性: 确认测试快速返回；若省略: 超时实现过慢不会被发现
                self.assertIsNone(client._process)  # 新增代码+MCP stdio client 健壮性: 确认超时后客户端已清理；若省略: 超时后进程残留不会被发现
            finally:  # 新增代码+MCP stdio client 健壮性: 无论断言结果如何都清理；若省略: 子进程可能泄漏
                client.close()  # 新增代码+MCP stdio client 健壮性: 再次关闭保证幂等清理；若省略: 失败路径可能残留资源
    def test_browser_search_mcp_server_lists_tools_and_fetches_local_page(self) -> None:  # 新增代码+browser/search MCP: 验证真实本地 MCP server 能列出搜索/读取工具并读取网页；若省略: 新增 server 可能只存在文件但端到端不可用
        server_script = (TEST_ROOT / "browser_search_mcp_server.py")  # 新增代码+browser/search MCP: 定位真实 browser_search MCP server；若省略: 测试无法启动被交付的 server 文件
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+browser/search MCP: 创建临时网页目录；若省略: 测试会污染项目目录
            workspace = Path(raw_dir)  # 新增代码+browser/search MCP: 把临时目录转成 Path；若省略: 后续写 HTML 文件不方便
            page_file = workspace / "index.html"  # 新增代码+browser/search MCP: 定义本地测试页面路径；若省略: fetch_url 没有稳定目标
            page_file.write_text("<html><body><h1>本地 MCP 页面</h1><p>browser search MCP fetch works.</p></body></html>", encoding="utf-8")  # 新增代码+browser/search MCP: 写入可断言的 HTML 内容；若省略: 本地 HTTP server 没有页面可返回

            class QuietHandler(http.server.SimpleHTTPRequestHandler):  # 新增代码+browser/search MCP: 定义静默 HTTP handler；若省略: 测试会把访问日志打印到单元测试输出
                def log_message(self, format: str, *args: object) -> None:  # 新增代码+browser/search MCP: 覆盖默认日志方法；若省略: 每次请求都会输出噪声
                    return None  # 新增代码+browser/search MCP: 不打印任何 HTTP 访问日志；若省略: 测试输出会变乱

            handler_factory = lambda *args, **kwargs: QuietHandler(*args, directory=str(workspace), **kwargs)  # 新增代码+browser/search MCP: 让 HTTP server 从临时目录提供文件；若省略: server 会从当前目录找页面
            httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler_factory)  # 新增代码+browser/search MCP: 在本机随机端口启动 HTTP server；若省略: fetch_url 测试只能依赖外网
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)  # 新增代码+browser/search MCP: 创建后台服务线程；若省略: serve_forever 会阻塞当前测试
            thread.start()  # 新增代码+browser/search MCP: 启动本地网页服务；若省略: fetch_url 会连接失败
            client = McpStdioClient(McpServerConfig(name="browser_search", command=sys.executable, args=[str(server_script)]))  # 新增代码+browser/search MCP: 用当前 Python 启动真实 MCP server；若省略: 不能验证 learning_agent 的 stdio client 能连接它
            try:  # 新增代码+browser/search MCP: 确保无论断言是否失败都清理 HTTP server 和 MCP client；若省略: 失败时可能残留线程或进程
                client.start()  # 新增代码+browser/search MCP: 完成 MCP initialize 握手；若省略: 后续 list_tools/call_tool 无法执行
                tools = client.list_tools()  # 新增代码+browser/search MCP: 请求 server 暴露的工具列表；若省略: 无法确认模型会看到哪些 MCP 工具
                tool_names = [tool.get("name") for tool in tools if isinstance(tool, dict)]  # 新增代码+browser/search MCP: 提取原始 MCP 工具名；若省略: 断言需要重复遍历结构
                tools_by_name = {str(tool.get("name")): tool for tool in tools if isinstance(tool, dict)}  # 新增代码+PromptSurfaceV2: 按工具名索引工具说明；若省略: 无法检查搜索工具描述是否误导真实浏览器请求
                self.assertIn("web_search", tool_names)  # 新增代码+browser/search MCP: 断言搜索工具已暴露；若省略: 搜索能力缺失不会被发现
                self.assertIn("fetch_url", tool_names)  # 新增代码+browser/search MCP: 断言网页读取工具已暴露；若省略: 搜索后打开网页能力缺失不会被发现
                self.assertIn("不是可见浏览器", str(tools_by_name["web_search"].get("description", "")))  # 新增代码+PromptSurfaceV2: 断言搜索工具说明不会冒充真实浏览器；若省略: 模型可能用搜索替代用户要求的真实浏览器
                self.assertIn("真实浏览器", str(tools_by_name["web_search"].get("description", "")))  # 新增代码+PromptSurfaceV2: 断言搜索工具描述显式提到真实浏览器边界；若省略: 工具选择仍可能混淆搜索和可见浏览器
                self.assertIn("不是可见浏览器", str(tools_by_name["fetch_url"].get("description", "")))  # 新增代码+PromptSurfaceV2: 断言网页读取工具说明不会冒充真实浏览器；若省略: 模型可能用 fetch_url 替代真实打开页面
                url = f"http://127.0.0.1:{httpd.server_port}/index.html"  # 新增代码+browser/search MCP: 构造本地测试页面 URL；若省略: fetch_url 没有目标地址
                result = client.call_tool("fetch_url", {"url": url, "max_chars": 2000})  # 新增代码+browser/search MCP: 调用真实 fetch_url 工具读取页面；若省略: 只验证 list_tools 不能证明 tools/call 可用
                self.assertIn("本地 MCP 页面", result)  # 新增代码+browser/search MCP: 断言 HTML 标题被提取为正文；若省略: fetch_url 提取失败不会被发现
                self.assertIn("browser search MCP fetch works.", result)  # 新增代码+browser/search MCP: 断言段落正文被提取；若省略: 只能证明页面打开但不能证明正文解析正确
            finally:  # 新增代码+browser/search MCP: 统一清理资源；若省略: 测试失败时可能残留子进程或端口
                client.close()  # 新增代码+browser/search MCP: 关闭 MCP server 子进程；若省略: browser_search_mcp_server.py 可能残留运行
                httpd.shutdown()  # 新增代码+browser/search MCP: 请求 HTTP server 停止；若省略: 后台线程可能继续运行
                httpd.server_close()  # 新增代码+browser/search MCP: 释放监听端口；若省略: Windows 上端口句柄可能残留
                thread.join(timeout=2)  # 新增代码+browser/search MCP: 等待后台线程退出；若省略: 测试结束时线程状态不确定
    def test_browser_automation_mcp_server_lists_real_chrome_tools(self) -> None:  # 新增代码+RealChrome测试: 验证 MCP server 暴露真实 Chrome 工具；若省略: 工具 schema 缺失不会被发现
        server_script = self._browser_automation_server_script()  # 新增代码+RealChrome测试: 定位 browser automation server；若省略: 测试无法启动真实 MCP server
        client = McpStdioClient(McpServerConfig(name="browser_automation", command=sys.executable, args=[str(server_script), str(TEST_ROOT)]))  # 新增代码+RealChrome测试: 通过 stdio 启动 MCP server；若省略: 只检查文件无法验证协议层
        try:  # 新增代码+RealChrome测试: 确保 finally 能关闭 MCP client；若省略: 失败时可能残留子进程
            client.start()  # 新增代码+RealChrome测试: 启动 MCP server 并初始化；若省略: tools/list 无法调用
            tools_by_name = {str(tool.get("name")): tool for tool in client.list_tools() if isinstance(tool, dict)}  # 修改代码+RealChrome测试: 把工具列表转成按名称索引的字典方便检查 schema；若省略: 只能确认工具存在，无法验证安全参数边界
            self.assertIn("browser_open", tools_by_name)  # 新增代码+PromptSurfaceV2: 断言普通打开网页工具可检查描述；若省略: 无法防止它继续误导真实浏览器请求
            self.assertIn("browser_connect_real_chrome", tools_by_name)  # 修改代码+RealChrome测试: 断言连接真实 Chrome 工具可见；若省略: 入口工具缺失不会失败
            self.assertIn("browser_disconnect_real_chrome", tools_by_name)  # 修改代码+RealChrome测试: 断言断开工具可见；若省略: 用户可能无法释放 CDP 连接
            self.assertIn("browser_profile_status", tools_by_name)  # 修改代码+RealChrome测试: 断言状态工具可见；若省略: 用户无法查看当前模式
            open_description = str(tools_by_name["browser_open"].get("description", ""))  # 新增代码+PromptSurfaceV2: 读取普通打开工具描述；若省略: 无法检查独立 Chromium 边界是否写清
            self.assertIn("独立 Chromium", open_description)  # 新增代码+PromptSurfaceV2: 断言 browser_open 默认语义仍清楚是独立 Chromium；若省略: 模型可能误以为它就是桌面 Chrome
            self.assertIn("不用于真实 Chrome", open_description)  # 新增代码+PromptSurfaceV2: 断言显式真实 Chrome 请求不应走 browser_open 初始路径；若省略: 用户要求真实浏览器时模型可能先打开独立实例
            connect_tool = tools_by_name["browser_connect_real_chrome"]  # 新增代码+RealChrome测试: 取出连接工具 schema 用于检查确认门槛；若省略: 无法验证 confirm_real_profile 必须为 true
            disconnect_tool = tools_by_name["browser_disconnect_real_chrome"]  # 新增代码+RealChrome测试: 取出断开工具 schema 用于检查默认不关闭浏览器；若省略: close_browser 默认值回归不会被发现
            status_tool = tools_by_name["browser_profile_status"]  # 新增代码+RealChrome测试: 取出状态工具说明用于检查只读边界；若省略: 状态工具可能误导用户以为会读取 profile
            connect_schema = connect_tool["inputSchema"]  # 新增代码+RealChrome测试: 读取连接工具输入 schema；若省略: 无法检查 schema 层安全约束
            confirm_schema = connect_schema["properties"]["confirm_real_profile"]  # 新增代码+RealChrome测试: 读取确认参数 schema；若省略: 无法断言模型必须传 true
            connect_description = str(connect_tool.get("description", ""))  # 新增代码+RealChrome规格修复测试: 读取连接工具描述用于防止旧 Task 3 文案残留；若省略: schema 描述可能继续误导用户以为不会启动 Chrome
            self.assertIn("confirm_real_profile", connect_schema["required"])  # 新增代码+RealChrome测试: 断言确认参数仍是必填；若省略: 调用方可能完全省略确认字段
            self.assertTrue(confirm_schema.get("const") is True or confirm_schema.get("enum") == [True])  # 新增代码+RealChrome测试: 断言 schema 机器可验证地只允许 true；若省略: false 也可能通过 schema 只在运行时才失败
            self.assertIn("127.0.0.1", connect_description)  # 新增代码+RealChrome规格修复测试: 断言文案说明 CDP 只走本机回环；若省略: 高风险连接的暴露边界不清楚
            self.assertIn("启动/连接", connect_description)  # 新增代码+RealChrome规格修复测试: 断言文案说明确认后会启动或连接真实 Chrome；若省略: 用户可能误以为仍只是临时桩
            self.assertNotIn("临时桩", connect_description)  # 新增代码+RealChrome规格修复测试: 断言旧 Task 3 临时桩文案已移除；若省略: 过期说明会继续误导用户
            disconnect_schema = disconnect_tool["inputSchema"]  # 新增代码+RealChrome测试: 读取断开工具输入 schema；若省略: 无法检查 close_browser 默认值
            close_browser_schema = disconnect_schema["properties"]["close_browser"]  # 新增代码+RealChrome测试: 读取 close_browser 参数 schema；若省略: 默认不关闭用户 Chrome 的契约没有测试保护
            self.assertIs(close_browser_schema.get("default"), False)  # 新增代码+RealChrome测试: 断言默认不关闭用户 Chrome；若省略: 默认值被改成 true 的高风险回归不会暴露
            disconnect_description = str(disconnect_tool.get("description", "")) + str(close_browser_schema.get("description", ""))  # 新增代码+RealChrome断开测试: 合并断开工具和参数描述检查当前行为；若没有这行代码，旧临时桩文案可能继续误导用户
            self.assertIn("默认", disconnect_description)  # 新增代码+RealChrome断开测试: 断言文案说明默认行为；若没有这行代码，用户可能不知道不传 close_browser 会发生什么
            self.assertIn("不关闭", disconnect_description)  # 新增代码+RealChrome断开测试: 断言默认不关闭真实 Chrome；若没有这行代码，高风险默认关闭回归不易被发现
            self.assertIn("chrome_process", disconnect_description)  # 新增代码+RealChrome断开测试: 断言文案说明只管理 agent 启动进程；若没有这行代码，用户可能误以为能关闭任意 Chrome
            self.assertNotIn("Task 3", disconnect_description)  # 新增代码+RealChrome断开测试: 断言不再出现过期 Task 3 临时桩文案；若没有这行代码，schema 可能继续显示错误阶段信息
            self.assertNotIn("临时桩", disconnect_description)  # 新增代码+RealChrome断开测试: 断言断开工具文案已是正式行为；若没有这行代码，旧临时说明回归不会暴露
            status_description = str(status_tool.get("description", ""))  # 新增代码+RealChrome测试: 读取状态工具描述文本；若省略: 无法验证文案是否说明只读和隐私边界
            self.assertIn("只读", status_description)  # 新增代码+RealChrome测试: 断言状态工具明确只读；若省略: 用户可能误会状态查询会动真实 profile
            self.assertIn("不读取", status_description)  # 新增代码+RealChrome测试: 断言状态工具明确不读取数据；若省略: 敏感数据边界可能被文案遗漏
            self.assertIn("敏感", status_description)  # 新增代码+RealChrome测试: 断言状态工具明确涉及敏感数据边界；若省略: profile 隐私风险提示不够醒目
            status_result = client.call_tool("browser_profile_status", {})  # 新增代码+RealChrome测试: 调用只读状态桩确认不会启动真实 Chrome；若省略: 只能验证 schema 不能验证安全返回
            self.assertIn("mode=independent_chromium", status_result)  # 新增代码+RealChrome测试: 断言默认仍是独立 Chromium；若省略: 默认模式被误改为真实 Chrome 不会暴露
            self.assertIn("real_chrome_connected=false", status_result)  # 新增代码+RealChrome测试: 断言当前没有真实 Chrome 连接；若省略: 用户可能误解连接状态
            disconnect_result = client.call_tool("browser_disconnect_real_chrome", {})  # 新增代码+RealChrome测试: 调用断开桩确认无连接时安全返回；若省略: 断开入口可能在无连接时失败
            self.assertIn("real_chrome_connected=false", disconnect_result)  # 修改代码+RealChrome断开测试: 断言无连接断开也返回机器可读 false 状态；若没有这行代码，断开工具可能退回临时文案导致上层无法稳定判断是否已断开
            with self.assertRaisesRegex(RuntimeError, "confirm_real_profile"):  # 修改代码+RealChrome测试: 改为验证未确认时必须被运行时拒绝；若省略: Task 4 实现后测试会继续期待旧桩错误
                client.call_tool("browser_connect_real_chrome", {"confirm_real_profile": False})  # 修改代码+RealChrome测试: 故意传 false 避免触发真实 Chrome 启动流程；若省略: 测试可能越过确认边界并尝试连接真实 profile
        finally:  # 新增代码+RealChrome测试: 统一关闭 MCP client；若省略: 测试进程可能残留
            client.close()  # 新增代码+RealChrome测试: 关闭 stdio server；若省略: 浏览器 MCP 子进程可能不退出
    def test_browser_automation_mcp_server_lists_mature_tools(self) -> None:  # 新增代码+BrowserAutomation: 验证成熟版浏览器自动化 MCP server 暴露完整工具清单；若省略: 后续实现可能只做打开网页而缺少点击、输入、截图等关键能力
        server_script = self._browser_automation_server_script()  # 新增代码+BrowserAutomation: 通过 helper 定位待实现 server 脚本；若省略: 测试无法检查真实交付文件
        self.assertTrue(server_script.exists(), f"缺少浏览器自动化 MCP server: {server_script}")  # 新增代码+BrowserAutomation: 红灯阶段先断言脚本必须存在；若省略: 测试可能以难懂的子进程启动错误失败
        client = McpStdioClient(McpServerConfig(name="browser_automation", command=sys.executable, args=[str(server_script), str(TEST_ROOT)]))  # 新增代码+BrowserAutomation: 用真实 stdio MCP client 启动浏览器自动化 server；若省略: 只能检查文件存在而不能验证 MCP 协议可用
        try:  # 新增代码+BrowserAutomation: 确保测试失败时也会关闭 MCP 子进程；若省略: server 可能残留在后台占用资源
            client.start()  # 新增代码+BrowserAutomation: 完成 MCP initialize 握手；若省略: tools/list 没有可用连接
            tools = client.list_tools()  # 新增代码+BrowserAutomation: 读取 server 暴露的原始工具列表；若省略: 无法知道成熟版能力是否注册
            tool_names = {tool.get("name") for tool in tools if isinstance(tool, dict)}  # 新增代码+BrowserAutomation: 提取工具名集合方便批量断言；若省略: 每个工具都要重复遍历且容易漏判
            expected_tools = {  # 新增代码+BrowserAutomation: 定义成熟浏览器自动化必须暴露的工具集合；若省略: 测试没有明确成功标准
                "browser_open",  # 新增代码+BrowserAutomation: 要求能打开网页；若省略: agent 无法进入目标页面
                "browser_snapshot",  # 新增代码+BrowserAutomation: 要求能读取页面结构快照；若省略: agent 点击前无法理解页面
                "browser_click",  # 新增代码+BrowserAutomation: 要求能点击元素；若省略: agent 无法操作按钮和链接
                "browser_type",  # 新增代码+BrowserAutomation: 要求能输入文本；若省略: agent 无法填写表单
                "browser_press_key",  # 新增代码+BrowserAutomation: 要求能发送键盘按键；若省略: agent 无法提交快捷键或回车
                "browser_wait",  # 新增代码+BrowserAutomation: 要求能等待页面状态变化；若省略: 异步页面容易读到旧状态
                "browser_screenshot",  # 新增代码+BrowserAutomation: 要求能截图并产出 artifact；若省略: 用户无法检查浏览器视觉结果
                "browser_tabs",  # 新增代码+BrowserAutomation: 要求能管理标签页；若省略: 多页面流程无法稳定控制
                "browser_console",  # 新增代码+BrowserAutomation: 要求能读取控制台日志；若省略: 页面脚本错误和调试信息不可见
                "browser_network",  # 新增代码+BrowserAutomation: 要求能读取网络记录；若省略: 无法确认页面访问了哪些地址
                "browser_upload_file",  # 新增代码+BrowserAutomation: 要求能上传文件；若省略: 文件表单流程不完整
                "browser_downloads",  # 新增代码+BrowserAutomation: 要求能查看下载结果；若省略: 下载类任务没有可验证出口
                "browser_evaluate",  # 新增代码+BrowserAutomation: 要求能执行受控页面 JavaScript；若省略: 难以读取复杂页面状态
                "browser_close",  # 新增代码+BrowserAutomation: 要求能关闭浏览器资源；若省略: 测试和运行后可能残留浏览器进程
            }  # 新增代码+BrowserAutomation: 结束成熟工具集合定义；若省略: Python 集合语法不完整
            self.assertTrue(expected_tools.issubset(tool_names), f"缺少工具: {sorted(expected_tools - tool_names)}")  # 新增代码+BrowserAutomation: 断言工具清单至少包含成熟版必需能力；若省略: server 少注册工具也会误判为通过
        finally:  # 新增代码+BrowserAutomation: 统一进入 MCP client 清理分支；若省略: 断言失败时可能不关闭子进程
            client.close()  # 新增代码+BrowserAutomation: 关闭 stdio MCP server 子进程；若省略: 测试会泄漏后台进程
    def test_browser_automation_mcp_server_operates_local_page(self) -> None:  # 新增代码+BrowserAutomation: 验证浏览器自动化 MCP 能真实操作本地页面；若省略: 只列工具无法证明打开、输入、点击、截图和日志采集能工作
        server_script = self._browser_automation_server_script()  # 新增代码+BrowserAutomation: 定位待实现 browser automation server；若省略: 测试无法启动真实 MCP server
        self.assertTrue(server_script.exists(), f"缺少浏览器自动化 MCP server: {server_script}")  # 新增代码+BrowserAutomation: 红灯阶段明确失败在脚本缺失；若省略: 本地 HTTP server 会先启动但真正缺口不直观
        page_html = """<!doctype html><html><head><title>Browser Automation Demo</title><script>console.log('page-ready'); window.testValue = 41;</script></head><body><h1>Browser Automation Demo</h1><input id="name" value=""><button id="apply" onclick="document.getElementById('status').textContent = 'Hello ' + document.getElementById('name').value; window.testValue = window.testValue + 1;">Apply</button><div id="status">等待输入</div></body></html>"""  # 新增代码+BrowserAutomation: 准备包含输入框、按钮、状态区、控制台日志和测试变量的页面；若省略: 自动化测试没有可操作目标
        class Handler(http.server.BaseHTTPRequestHandler):  # 新增代码+BrowserAutomation: 定义只服务当前测试 HTML 的 HTTP handler；若省略: 本地页面无法通过浏览器 URL 打开
            def do_GET(self) -> None:  # 新增代码+BrowserAutomation: 响应浏览器 GET 请求；若省略: browser_open 会拿不到测试页面
                body = page_html.encode("utf-8")  # 新增代码+BrowserAutomation: 把 HTML 转成 UTF-8 字节；若省略: HTTP 响应无法写入网络流
                self.send_response(200)  # 新增代码+BrowserAutomation: 返回 HTTP 200 表示页面存在；若省略: 浏览器可能认为加载失败
                self.send_header("Content-Type", "text/html; charset=utf-8")  # 新增代码+BrowserAutomation: 声明 HTML 和编码；若省略: 浏览器可能按错误编码解释页面
                self.send_header("Content-Length", str(len(body)))  # 新增代码+BrowserAutomation: 声明响应长度；若省略: 客户端可能等待或截断响应
                self.end_headers()  # 新增代码+BrowserAutomation: 结束响应头并准备写正文；若省略: 浏览器收不到合法 HTTP 响应
                self.wfile.write(body)  # 新增代码+BrowserAutomation: 写出测试页面正文；若省略: 页面为空导致后续元素不存在
            def log_message(self, format: str, *args: object) -> None:  # 新增代码+BrowserAutomation: 覆盖默认访问日志；若省略: 单元测试输出会被 HTTP 日志干扰
                return None  # 新增代码+BrowserAutomation: 静默 HTTP 访问日志；若省略: 测试结果不够干净
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)  # 新增代码+BrowserAutomation: 在本机随机端口启动测试页面 server；若省略: 浏览器没有稳定本地 URL 可访问
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)  # 新增代码+BrowserAutomation: 创建后台线程运行 HTTP server；若省略: serve_forever 会阻塞测试主线程
        thread.start()  # 新增代码+BrowserAutomation: 启动本地 HTTP 服务；若省略: browser_open 会连接失败
        client: McpStdioClient | None = None  # 新增代码+BrowserAutomation: 先声明可为空的 MCP client 让 finally 能安全判断；若省略: client 构造失败时 HTTP server 清理可能被未绑定变量异常打断
        try:  # 修改代码+BrowserAutomation: 把 client 构造也放入清理边界；若省略: McpStdioClient 构造失败时本地 HTTP server 可能无法 shutdown
            client = McpStdioClient(McpServerConfig(name="browser_automation", command=sys.executable, args=[str(server_script), str(TEST_ROOT)]))  # 修改代码+BrowserAutomation: 在 try 内启动真实浏览器自动化 MCP server 并传入工作目录；若省略: 构造失败路径无法被 finally 统一清理
            client.start()  # 新增代码+BrowserAutomation: 完成 MCP initialize 握手；若省略: 后续工具调用无法发送
            url = f"http://127.0.0.1:{httpd.server_port}/index.html"  # 新增代码+BrowserAutomation: 构造本地页面 URL；若省略: browser_open 没有目标地址
            open_result = client.call_tool("browser_open", {"url": url})  # 新增代码+BrowserAutomation: 让 MCP 浏览器打开本地页面；若省略: 后续快照、输入和点击没有页面上下文
            snapshot = client.call_tool("browser_snapshot", {})  # 新增代码+BrowserAutomation: 获取页面可访问性或结构快照；若省略: 无法断言标题和按钮可见
            type_result = client.call_tool("browser_type", {"selector": "#name", "text": "Codex"})  # 新增代码+BrowserAutomation: 在输入框写入 Codex；若省略: 点击按钮后不会产生 Hello Codex
            click_result = client.call_tool("browser_click", {"selector": "#apply"})  # 新增代码+BrowserAutomation: 点击 Apply 按钮触发页面逻辑；若省略: 状态区不会更新
            wait_result = client.call_tool("browser_wait", {"text": "Hello Codex", "timeout_ms": 3000})  # 新增代码+BrowserAutomation: 等待状态文字出现；若省略: 异步更新可能尚未完成就断言
            evaluate_result = client.call_tool("browser_evaluate", {"script": "() => ({value: window.testValue, status: document.querySelector('#status').textContent})"})  # 修改代码+BrowserAutomation: 使用设计要求的 script 参数读取 value 和 status；若省略: 后续 server 按 script 接口实现时此红灯测试会错误传 expression
            screenshot_result = client.call_tool("browser_screenshot", {"filename": "test-page.png", "full_page": True})  # 修改代码+BrowserAutomation: 使用设计要求的 filename 和 full_page 参数截图；若省略: 后续 server 按 filename 接口实现时此红灯测试会错误传 name
            console_result = client.call_tool("browser_console", {})  # 新增代码+BrowserAutomation: 读取页面控制台日志；若省略: page-ready 日志是否被收集无法验证
            network_result = client.call_tool("browser_network", {})  # 新增代码+BrowserAutomation: 读取页面网络记录；若省略: 访问 127.0.0.1 的事实无法验证
            combined = "\n".join([open_result, snapshot, type_result, click_result, wait_result, evaluate_result, screenshot_result, console_result, network_result])  # 新增代码+BrowserAutomation: 合并所有工具输出便于统一断言；若省略: 每个断言都要手动挑输出且容易漏掉流程结果
            self.assertIn("Browser Automation Demo", combined)  # 新增代码+BrowserAutomation: 断言页面标题或正文被浏览器读取；若省略: 打开了错误页面也可能通过
            self.assertIn("Apply", combined)  # 新增代码+BrowserAutomation: 断言按钮可见于快照；若省略: 点击目标缺失不容易被发现
            self.assertIn("Codex", combined)  # 新增代码+BrowserAutomation: 断言输入动作被结果或页面状态反映；若省略: browser_type 失败可能不被发现
            self.assertIn("Hello Codex", combined)  # 新增代码+BrowserAutomation: 断言点击后页面状态完成更新；若省略: browser_click 可能没有真正触发页面逻辑
            self.assertRegex(combined, r"[\"']?value[\"']?\s*[:=]\s*42(?!\d)")  # 修改代码+BrowserAutomation: 用带数字边界的宽松正则断言 value 必须是 42，避免 value:420 或 value=421 这种错误值被误判通过；若省略: browser_evaluate 返回错误数值也可能骗过测试
            self.assertIn("browser_artifacts", combined)  # 新增代码+BrowserAutomation: 断言截图输出落到约定 artifacts 目录；若省略: 截图可能没有生成可查看文件
            self.assertIn("page-ready", combined)  # 新增代码+BrowserAutomation: 断言控制台日志被采集；若省略: console 工具失效不会被发现
            self.assertIn("127.0.0.1", combined)  # 新增代码+BrowserAutomation: 断言网络记录包含本地页面请求；若省略: network 工具失效不会被发现
        finally:  # 修改代码+BrowserAutomation: 无论 client 构造、启动或工具调用在哪一步失败都清理外部资源；若省略: 可能残留浏览器、MCP 子进程或 HTTP 端口
            if client is not None:  # 新增代码+BrowserAutomation: 只有 client 构造成功后才尝试关闭浏览器和 MCP；若省略: client 构造失败时清理阶段会再次抛错
                try:  # 修改代码+BrowserAutomation: 在 client 存在时尝试请求浏览器 server 关闭页面和浏览器；若省略: Playwright 浏览器可能在失败路径残留
                    client.call_tool("browser_close", {"all": True})  # 修改代码+BrowserAutomation: 关闭所有浏览器上下文；若省略: 自动化浏览器资源可能泄漏
                except Exception:  # 修改代码+BrowserAutomation: 红灯阶段 server 不存在或未启动时容忍关闭失败；若省略: 清理异常会掩盖真正的红灯失败原因
                    pass  # 修改代码+BrowserAutomation: 忽略关闭浏览器失败并继续清理基础资源；若省略: 后续 client.close 和 HTTP shutdown 可能不执行
                client.close()  # 修改代码+BrowserAutomation: 关闭 MCP stdio client 和子进程；若省略: 测试可能泄漏 server 进程
            httpd.shutdown()  # 新增代码+BrowserAutomation: 停止本地 HTTP server；若省略: 后台服务会继续运行
            httpd.server_close()  # 新增代码+BrowserAutomation: 释放 HTTP 监听端口；若省略: Windows 上端口句柄可能残留
            thread.join(timeout=2)  # 新增代码+BrowserAutomation: 等待 HTTP server 线程退出；若省略: 测试结束时线程状态不确定
    def test_browser_automation_mcp_server_uploads_and_downloads(self) -> None:  # 新增代码+BrowserAutomation上传下载: 验证真实 MCP 浏览器能上传工作区文件并记录下载；若省略: Task 5 的上传/下载闭环没有端到端保护
        server_script = self._browser_automation_server_script()  # 新增代码+BrowserAutomation上传下载: 定位被测浏览器自动化 MCP server；若省略: 测试无法启动真实 server
        self.assertTrue(server_script.exists(), f"缺少浏览器自动化 MCP server: {server_script}")  # 新增代码+BrowserAutomation上传下载: 先确认 server 文件存在；若省略: 缺文件时会表现成难懂的子进程错误
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserAutomation上传下载: 创建临时 workspace 隔离上传文件和浏览器产物；若省略: 测试会污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+BrowserAutomation上传下载: 把临时目录包装成 Path；若省略: 后续拼接 upload.txt 不方便
            upload_file = workspace / "upload.txt"  # 新增代码+BrowserAutomation上传下载: 定义允许上传的工作区内文件；若省略: browser_upload_file 没有合法输入文件
            upload_file.write_text("hello upload", encoding="utf-8")  # 新增代码+BrowserAutomation上传下载: 写入上传测试文件内容；若省略: 上传路径会缺失导致测试无法证明成功路径
            page_html = """<!doctype html><html><head><title>Upload Download Demo</title></head><body><input type="file" id="upload"><a id="download" download="download.txt" href="data:text/plain,hello-download">Download</a></body></html>"""  # 新增代码+BrowserAutomation上传下载: 准备同时包含上传 input 和 data 下载链接的页面；若省略: 浏览器没有可操作的上传下载目标
            class Handler(http.server.BaseHTTPRequestHandler):  # 新增代码+BrowserAutomation上传下载: 定义本测试专用 HTTP handler；若省略: 本地页面无法通过 URL 提供给浏览器
                def do_GET(self) -> None:  # 新增代码+BrowserAutomation上传下载: 响应浏览器访问测试页面的 GET 请求；若省略: browser_open 会打开失败
                    body = page_html.encode("utf-8")  # 新增代码+BrowserAutomation上传下载: 把 HTML 编码成 HTTP 响应字节；若省略: wfile 无法写出字符串正文
                    self.send_response(200)  # 新增代码+BrowserAutomation上传下载: 返回 200 表示测试页面存在；若省略: 浏览器可能按失败页面处理
                    self.send_header("Content-Type", "text/html; charset=utf-8")  # 新增代码+BrowserAutomation上传下载: 声明 HTML 内容和 UTF-8 编码；若省略: 浏览器可能用错误编码解析页面
                    self.send_header("Content-Length", str(len(body)))  # 新增代码+BrowserAutomation上传下载: 告诉浏览器响应长度；若省略: 客户端可能等待更多数据
                    self.end_headers()  # 新增代码+BrowserAutomation上传下载: 结束 HTTP 响应头；若省略: 正文不会被当作合法响应读取
                    self.wfile.write(body)  # 新增代码+BrowserAutomation上传下载: 写出测试 HTML 正文；若省略: 页面为空且找不到 input/link
                def log_message(self, format: str, *args: object) -> None:  # 新增代码+BrowserAutomation上传下载: 覆盖默认访问日志；若省略: 单元测试输出会混入 HTTP 日志
                    return None  # 新增代码+BrowserAutomation上传下载: 静默本地 HTTP 访问日志；若省略: 测试结果不够干净
            httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)  # 新增代码+BrowserAutomation上传下载: 在随机端口启动本地页面 server；若省略: browser_open 没有可访问 URL
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)  # 新增代码+BrowserAutomation上传下载: 后台线程运行 HTTP server；若省略: serve_forever 会阻塞测试
            thread.start()  # 新增代码+BrowserAutomation上传下载: 启动本地 HTTP 服务；若省略: 浏览器连接会失败
            client: McpStdioClient | None = None  # 新增代码+BrowserAutomation上传下载: 先声明 client 让 finally 可安全清理；若省略: 构造失败时清理会遇到未绑定变量
            try:  # 新增代码+BrowserAutomation上传下载: 把 MCP client 和 HTTP server 生命周期纳入统一清理；若省略: 失败路径可能残留进程或端口
                client = McpStdioClient(McpServerConfig(name="browser_automation", command=sys.executable, args=[str(server_script), str(workspace)]))  # 新增代码+BrowserAutomation上传下载: 用临时 workspace 启动真实浏览器 MCP server；若省略: upload.txt 相对路径不会被允许上传
                client.start()  # 新增代码+BrowserAutomation上传下载: 完成 MCP initialize 握手；若省略: 后续工具调用没有连接
                url = f"http://127.0.0.1:{httpd.server_port}/index.html"  # 新增代码+BrowserAutomation上传下载: 构造本地上传下载页面 URL；若省略: browser_open 没有目标地址
                client.call_tool("browser_open", {"url": url})  # 新增代码+BrowserAutomation上传下载: 打开测试页面；若省略: 上传和下载工具没有页面上下文
                upload_result = client.call_tool("browser_upload_file", {"selector": "#upload", "path": "upload.txt"})  # 新增代码+BrowserAutomation上传下载: 上传 workspace 内的 upload.txt；若省略: 文件选择控件能力不会被验证
                self.assertIn("browser_upload_file 成功", upload_result)  # 新增代码+BrowserAutomation上传下载: 断言上传工具返回成功；若省略: 上传失败可能不被测试发现
                client.call_tool("browser_click", {"selector": "#download"})  # 修改代码+BrowserAutomation上传下载: 第一次点击 data 下载链接触发 download.txt；若省略: 下载记录不会产生
                client.call_tool("browser_click", {"selector": "#download"})  # 新增代码+BrowserAutomation上传下载: 第二次点击同名下载链接验证唯一化保存；若省略: 同名覆盖回归不会被测试发现
                artifacts_dir = workspace / "browser_artifacts"  # 新增代码+BrowserAutomation上传下载: 定位临时 workspace 下的浏览器产物目录；若省略: 无法检查真实下载文件是否落盘
                downloaded_files: list[Path] = []  # 新增代码+BrowserAutomation上传下载: 保存轮询期间发现的下载文件列表；若省略: 循环后无法断言文件数量和内容
                downloaded_texts: list[str] = []  # 修改代码+BrowserAutomation上传下载: 保存轮询期间读取到的下载文件内容；若省略: 文件刚创建但尚未写完时会被误判为成功
                downloads_result = ""  # 新增代码+BrowserAutomation上传下载: 保存最近一次 browser_downloads 输出；若省略: 轮询失败时断言没有可诊断文本
                deadline = time.time() + 5  # 新增代码+BrowserAutomation上传下载: 设置最多 5 秒轮询窗口；若省略: 等待下载可能无限循环或过早失败
                while time.time() < deadline:  # 新增代码+BrowserAutomation上传下载: 持续查询下载记录直到文件真正出现；若省略: 固定 sleep 会让测试在慢机器上不稳定
                    client.call_tool("browser_wait", {"milliseconds": 100})  # 新增代码+BrowserAutomation上传下载: 每轮短暂推进浏览器事件以便 download 回调落盘；若省略: 只读内存的 browser_downloads 可能看不到异步下载事件
                    downloads_result = client.call_tool("browser_downloads", {"max_results": 5})  # 修改代码+BrowserAutomation上传下载: 轮询最近下载记录；若省略: 无法知道 MCP server 是否已记录下载事件
                    downloaded_files = sorted(artifacts_dir.glob("download*.txt"))  # 新增代码+BrowserAutomation上传下载: 用通配符兼容 download.txt、download-2.txt 等唯一文件名；若省略: 唯一化命名会让测试找不到第二个文件
                    downloaded_texts = []  # 修改代码+BrowserAutomation上传下载: 每轮重新读取文件内容避免沿用旧结果；若省略: 上一轮空内容可能污染后续判断
                    for downloaded_file in downloaded_files:  # 修改代码+BrowserAutomation上传下载: 逐个读取已出现的下载文件；若省略: 无法确认两个文件都真正写入完成
                        try:  # 修改代码+BrowserAutomation上传下载: 读取文件时允许下载回调还在写入；若省略: Windows 文件锁会让测试直接异常退出
                            downloaded_texts.append(downloaded_file.read_text(encoding="utf-8"))  # 修改代码+BrowserAutomation上传下载: 记录当前文件文本；若省略: 轮询条件无法检查 hello-download 内容
                        except OSError:  # 修改代码+BrowserAutomation上传下载: 捕获文件暂不可读的短暂状态；若省略: 真实浏览器写文件期间可能让测试假失败
                            downloaded_texts.append("")  # 修改代码+BrowserAutomation上传下载: 暂不可读时记为空文本等待下一轮；若省略: 后续条件长度和文件列表不同步
                    if "download.txt" in downloads_result and len(downloaded_files) >= 2 and all("hello-download" in text for text in downloaded_texts[:2]):  # 修改代码+BrowserAutomation上传下载: 只有记录可见、两个文件存在且内容写完整才停止轮询；若省略: 空文件时序会继续偶发失败
                        break  # 新增代码+BrowserAutomation上传下载: 下载条件满足时退出轮询；若省略: 测试会额外等待到超时
                    time.sleep(0.1)  # 新增代码+BrowserAutomation上传下载: 短暂等待后再查，避免忙等占用 CPU；若省略: 轮询会持续占满处理器
                self.assertIn("download.txt", downloads_result)  # 修改代码+BrowserAutomation上传下载: 断言下载列表包含目标文件名；若省略: 下载工具可能返回空也不失败
                self.assertGreaterEqual(len(downloaded_files), 2, downloads_result)  # 新增代码+BrowserAutomation上传下载: 断言两次同名下载都以唯一文件真实存在；若省略: 同名覆盖只留下一个文件也会通过
                self.assertIn("hello-download", downloaded_texts[0] if downloaded_texts else "", downloads_result)  # 修改代码+BrowserAutomation上传下载: 断言第一个下载文件内容正确并在失败时展示下载记录；若省略: 只看文件名不能证明下载内容真实保存
                self.assertIn("hello-download", downloaded_texts[1] if len(downloaded_texts) > 1 else "", downloads_result)  # 修改代码+BrowserAutomation上传下载: 断言第二个唯一下载文件内容正确并在失败时展示下载记录；若省略: 第二次下载可能是空文件或覆盖结果仍不被发现
            finally:  # 新增代码+BrowserAutomation上传下载: 清理浏览器、MCP 子进程和本地 HTTP server；若省略: 测试失败会留下后台资源
                if client is not None:  # 新增代码+BrowserAutomation上传下载: 只有 client 构造成功才调用关闭；若省略: 构造失败会让清理再次报错
                    try:  # 新增代码+BrowserAutomation上传下载: 尝试优雅关闭浏览器会话；若省略: Playwright/Chromium 可能残留
                        client.call_tool("browser_close", {"all": True})  # 新增代码+BrowserAutomation上传下载: 请求 MCP server 关闭所有浏览器资源；若省略: 测试后可能残留无头浏览器
                    except Exception:  # 新增代码+BrowserAutomation上传下载: 容忍红灯阶段工具未实现或 server 已退出；若省略: 清理异常会掩盖真正失败原因
                        pass  # 新增代码+BrowserAutomation上传下载: 忽略关闭失败继续做基础清理；若省略: except 分支语法不完整
                    client.close()  # 新增代码+BrowserAutomation上传下载: 关闭 stdio MCP client 子进程；若省略: server 进程可能残留
                httpd.shutdown()  # 新增代码+BrowserAutomation上传下载: 停止本地 HTTP server；若省略: 后台线程会继续运行
                httpd.server_close()  # 新增代码+BrowserAutomation上传下载: 释放监听端口；若省略: Windows 可能保留端口句柄
                thread.join(timeout=2)  # 新增代码+BrowserAutomation上传下载: 等待 HTTP server 线程退出；若省略: 测试结束时线程状态不确定
    def test_missing_mcp_config_returns_empty_server_list(self) -> None:  # 新增代码: 验证缺少 mcp_servers.json 时保持无 MCP 行为；若省略: 缺省启动可能误报或崩溃
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 创建没有配置文件的临时目录；若省略: 测试会受真实项目配置影响
            workspace = Path(raw_dir)  # 新增代码: 把临时目录转成 Path；若省略: 无法传给配置加载函数
            configs = load_mcp_server_configs(workspace)  # 新增代码: 读取计划新增的 MCP 配置；若省略: 无法验证缺省行为
            self.assertEqual(configs, [])  # 新增代码: 缺少配置时应返回空列表；若省略: 不能保护旧行为
    def test_mcp_config_file_is_parsed_into_server_configs(self) -> None:  # 新增代码: 验证 mcp_servers.json 能被解析成配置对象；若省略: MCP server 无法可靠启动
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 创建临时工作区；若省略: 会污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码: 包装路径；若省略: 后续文件写入不方便
            config_file = workspace / "mcp_servers.json"  # 新增代码: 定义配置文件路径；若省略: 无法模拟真实配置文件
            config_file.write_text(  # 新增代码: 写入最小 MCP 配置；若省略: 配置加载函数没有输入
                json.dumps({"servers": [{"name": "demo", "command": sys.executable, "args": ["fake_server.py"]}]}, ensure_ascii=False),  # 新增代码: 使用当前 Python 作为命令，避免硬编码平台路径；若省略: 测试跨机器不稳定
                encoding="utf-8",  # 新增代码: 明确 UTF-8，避免中文环境编码差异；若省略: Windows 可能出现编码问题
            )
            configs = load_mcp_server_configs(workspace)  # 新增代码: 调用配置加载函数；若省略: 测试没有行为
            self.assertEqual(configs, [McpServerConfig(name="demo", command=sys.executable, args=["fake_server.py"])])  # 新增代码: 断言解析结果准确；若省略: 配置字段可能被读错也不会发现
    def test_mcp_config_parses_http_and_sse_transport_fields(self) -> None:  # 新增代码+MCPTransport: 验证配置能读取 http/sse transport、url 和 headers；若省略: 远程 MCP server 配置缺口不会被测试发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCPTransport: 创建临时工作区隔离 transport 配置；若省略: 测试可能污染真实 mcp_servers.json
            workspace = Path(raw_dir)  # 新增代码+MCPTransport: 把临时目录包装成 Path；若省略: 后续路径拼接不清晰
            config_file = workspace / "mcp_servers.json"  # 新增代码+MCPTransport: 定位待写入的 MCP 配置文件；若省略: 配置加载函数没有真实输入
            config_file.write_text(  # 新增代码+MCPTransport: 写入同时包含 Streamable HTTP 和旧 SSE 的配置；若省略: 无法覆盖非 stdio transport
                json.dumps(  # 新增代码+MCPTransport: 使用 JSON 序列化模拟真实用户配置；若省略: 测试数据不会按真实文件格式进入加载函数
                    {  # 新增代码+MCPTransport: 顶层对象保存 servers 数组；若省略: 加载函数无法找到 server 列表
                        "servers": [  # 新增代码+MCPTransport: 准备两个远程 transport server；若省略: http/sse 解析都没有样本
                            {  # 新增代码+MCPTransport: 定义 Streamable HTTP server 配置；若省略: http transport 无法被测试
                                "name": "remote_http",  # 新增代码+MCPTransport: 保存 server 名用于 mcp__ 前缀；若省略: 配置项应被跳过
                                "transport": "http",  # 新增代码+MCPTransport: 声明使用 HTTP transport；若省略: 加载器会默认按 stdio 处理
                                "url": "http://127.0.0.1:9/mcp",  # 新增代码+MCPTransport: 提供远程 MCP endpoint；若省略: HTTP client 无法知道 POST 到哪里
                                "headers": {"Authorization": "Bearer test", "X-Number": 123},  # 新增代码+MCPTransport: 提供自定义请求头并覆盖非字符串值转换；若省略: 鉴权类 MCP server 无法配置
                            },  # 新增代码+MCPTransport: Streamable HTTP 配置对象结束；若省略: JSON 结构不完整
                            {  # 新增代码+MCPTransport: 定义旧 HTTP+SSE server 配置；若省略: sse 边界无法被测试
                                "name": "legacy_sse",  # 新增代码+MCPTransport: 保存 legacy server 名称；若省略: SSE 配置无法进入结果
                                "transport": "sse",  # 新增代码+MCPTransport: 声明旧 SSE transport；若省略: 无法区分兼容边界
                                "url": "http://127.0.0.1:9/sse",  # 新增代码+MCPTransport: 保存旧 SSE 入口 URL；若省略: SSE client 无法报告目标
                            },  # 新增代码+MCPTransport: SSE 配置对象结束；若省略: JSON 结构不完整
                        ],  # 新增代码+MCPTransport: servers 数组结束；若省略: JSON 结构不完整
                    },  # 新增代码+MCPTransport: 顶层对象结束；若省略: JSON 结构不完整
                    ensure_ascii=False,  # 新增代码+MCPTransport: 保持中文和符号可读；若省略: 文档式测试数据会变成转义形式
                ),  # 新增代码+MCPTransport: JSON 文本构造结束；若省略: write_text 缺少内容
                encoding="utf-8",  # 新增代码+MCPTransport: 用 UTF-8 写入配置；若省略: Windows 默认编码可能影响读取
            )  # 新增代码+MCPTransport: 配置文件写入完成；若省略: 后续加载不到测试配置
            configs = load_mcp_server_configs(workspace)  # 新增代码+MCPTransport: 调用配置加载函数读取新 transport 字段；若省略: 测试没有实际行为
            self.assertEqual([config.name for config in configs], ["remote_http", "legacy_sse"])  # 新增代码+MCPTransport: 断言两个远程配置都被保留；若省略: 跳过远程 server 的回归不会被发现
            self.assertEqual(configs[0].transport, "http")  # 新增代码+MCPTransport: 断言 HTTP transport 被规范化保存；若省略: registry 无法按 transport 选择 client
            self.assertEqual(configs[0].url, "http://127.0.0.1:9/mcp")  # 新增代码+MCPTransport: 断言 HTTP endpoint 被保存；若省略: client 可能无法连接远程 MCP
            self.assertEqual(configs[0].headers["Authorization"], "Bearer test")  # 新增代码+MCPTransport: 断言自定义鉴权头被保留；若省略: 需要鉴权的 MCP server 无法使用
            self.assertEqual(configs[0].headers["X-Number"], "123")  # 新增代码+MCPTransport: 断言 header 值被转成字符串；若省略: urllib header 可能收到非法类型
            self.assertEqual(configs[1].transport, "sse")  # 新增代码+MCPTransport: 断言 SSE transport 被保留；若省略: 旧协议边界无法进入 registry
            self.assertEqual(configs[1].url, "http://127.0.0.1:9/sse")  # 新增代码+MCPTransport: 断言 SSE URL 被保存；若省略: doctor 无法指出旧协议目标
    def test_mcp_registry_creates_clients_by_transport(self) -> None:  # 新增代码+MCPTransport: 验证 registry 会按 transport 创建 stdio/http/sse client；若省略: 配置解析正确但运行时仍可能固定走 stdio
        configs = [  # 新增代码+MCPTransport: 准备三种 transport 配置；若省略: registry 工厂没有测试输入
            McpServerConfig(name="local", command=sys.executable, args=[]),  # 新增代码+MCPTransport: stdio 配置保持旧写法；若省略: 旧配置兼容性没有对照
            McpServerConfig(name="remote", command="", transport="http", url="http://127.0.0.1:9/mcp"),  # 新增代码+MCPTransport: HTTP 配置用于触发 HTTP client；若省略: 新 transport 不会进入 registry
            McpServerConfig(name="legacy", command="", transport="sse", url="http://127.0.0.1:9/sse"),  # 新增代码+MCPTransport: SSE 配置用于触发明确边界 client；若省略: 旧协议边界没有覆盖
        ]  # 新增代码+MCPTransport: transport 配置列表结束；若省略: Python 语法不完整
        registry = McpToolRegistry.from_configs(configs)  # 新增代码+MCPTransport: 从配置创建 registry；若省略: 无法观察工厂选择结果
        self.assertEqual(registry.server_names(), ["local", "remote", "legacy"])  # 新增代码+MCPTransport: 断言 server 顺序和名称被保留；若省略: 多 transport 配置可能丢项
        self.assertEqual(type(registry._clients["local"]).__name__, "McpStdioClient")  # 新增代码+MCPTransport: 断言 stdio 继续使用原 client；若省略: 旧行为可能被新改动破坏
        self.assertEqual(type(registry._clients["remote"]).__name__, "McpHttpClient")  # 新增代码+MCPTransport: 断言 HTTP 配置使用 HTTP client；若省略: 远程 MCP 仍可能被当成本地命令启动
        self.assertEqual(type(registry._clients["legacy"]).__name__, "McpSseClient")  # 新增代码+MCPTransport: 断言 SSE 配置使用边界 client；若省略: 旧协议可能给出误导性 stdio 错误
    def test_mcp_http_client_lists_calls_resources_and_prompts(self) -> None:  # 新增代码+MCPTransport: 验证 Streamable HTTP client 能完成 tools/resources/prompts 最小链路；若省略: 只测配置无法证明远程 MCP 可调用
        requests: list[dict[str, str]] = []  # 新增代码+MCPTransport: 保存本地 HTTP server 收到的请求摘要；若省略: 无法断言请求头和生命周期

        class Handler(http.server.BaseHTTPRequestHandler):  # 新增代码+MCPTransport: 定义测试专用 HTTP MCP handler；若省略: 没有可控远程 MCP server
            def log_message(self, format: str, *args: object) -> None:  # 新增代码+MCPTransport: 覆盖默认日志避免测试输出噪声；若省略: unittest 输出会混入 HTTP 访问日志
                return None  # 新增代码+MCPTransport: 静默处理日志；若省略: log_message 仍可能写 stderr

            def do_POST(self) -> None:  # 新增代码+MCPTransport: 处理 Streamable HTTP 的 JSON-RPC POST；若省略: HTTP client 无法获得响应
                length = int(self.headers.get("Content-Length", "0"))  # 新增代码+MCPTransport: 读取请求体长度；若省略: 无法完整读取 JSON-RPC body
                body = self.rfile.read(length).decode("utf-8")  # 新增代码+MCPTransport: 读取并解码请求体；若省略: fake server 无法解析客户端消息
                message = json.loads(body) if body else {}  # 新增代码+MCPTransport: 把 JSON-RPC body 转成字典；若省略: 无法判断 method 和 id
                method = str(message.get("method", ""))  # 新增代码+MCPTransport: 读取方法名用于分支响应；若省略: fake server 不知道该返回什么
                requests.append(  # 新增代码+MCPTransport: 记录请求方法和关键 header；若省略: 测试无法确认 HTTP transport 是否符合规范
                    {  # 新增代码+MCPTransport: 请求审计对象开始；若省略: 记录结构不完整
                        "method": method,  # 新增代码+MCPTransport: 保存 JSON-RPC 方法；若省略: 后续无法定位 tools/list 请求
                        "accept": self.headers.get("Accept", ""),  # 新增代码+MCPTransport: 保存 Accept 头；若省略: 无法验证客户端接受 JSON 和 SSE
                        "authorization": self.headers.get("Authorization", ""),  # 新增代码+MCPTransport: 保存自定义鉴权头；若省略: headers 配置可能未生效
                        "session": self.headers.get("Mcp-Session-Id", ""),  # 新增代码+MCPTransport: 保存会话头；若省略: 无法验证初始化后 session 继承
                        "version": self.headers.get("MCP-Protocol-Version", ""),  # 新增代码+MCPTransport: 保存协议版本头；若省略: 无法验证后续 HTTP 请求版本信息
                    }  # 新增代码+MCPTransport: 请求审计对象结束；若省略: Python 语法不完整
                )  # 新增代码+MCPTransport: 请求审计追加完成；若省略: requests 不会累积记录
                if "id" not in message:  # 新增代码+MCPTransport: 识别 initialized notification；若省略: fake server 会把通知错误当作请求响应
                    self.send_response(202)  # 新增代码+MCPTransport: notification 接受后返回 202；若省略: HTTP client 会误判通知失败
                    self.end_headers()  # 新增代码+MCPTransport: 结束 notification 响应头；若省略: 客户端可能等不到完整响应
                    return  # 新增代码+MCPTransport: notification 不返回 JSON-RPC body；若省略: 后续分支会访问缺失 request_id
                request_id = message.get("id")  # 新增代码+MCPTransport: 保存请求 id 用于 JSON-RPC 响应匹配；若省略: 客户端无法确认响应归属
                params = message.get("params", {}) if isinstance(message.get("params", {}), dict) else {}  # 新增代码+MCPTransport: 读取参数对象并兜底；若省略: tools/call 等分支取参可能崩溃
                if method == "initialize":  # 新增代码+MCPTransport: 处理 MCP 初始化请求；若省略: client.start 无法进入就绪状态
                    result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}, "resources": {}, "prompts": {}}}  # 新增代码+MCPTransport: 返回协议版本和能力；若省略: 客户端无法保存协商版本
                elif method == "tools/list":  # 新增代码+MCPTransport: 处理工具发现请求；若省略: registry 无法暴露 HTTP 工具
                    result = {"tools": [{"name": "echo", "description": "Echo over HTTP", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}}]}  # 新增代码+MCPTransport: 返回一个 echo 工具；若省略: tool_schemas 没有可见工具
                elif method == "tools/call":  # 新增代码+MCPTransport: 处理工具调用请求；若省略: registry.call_tool 无法验证 HTTP 执行链路
                    arguments = params.get("arguments", {}) if isinstance(params.get("arguments", {}), dict) else {}  # 新增代码+MCPTransport: 读取工具参数；若省略: echo 无法返回输入文本
                    result = {"content": [{"type": "text", "text": "echo:" + str(arguments.get("text", ""))}]}  # 新增代码+MCPTransport: 返回标准 MCP 文本结果；若省略: call_tool 文本转换无法验证
                elif method == "resources/list":  # 新增代码+MCPTransport: 处理 resource 列表请求；若省略: HTTP resources 能力没有覆盖
                    result = {"resources": [{"uri": "file://remote.md", "name": "remote-doc", "mimeType": "text/markdown"}]}  # 新增代码+MCPTransport: 返回一个远程资源；若省略: registry.list_resources 结果为空
                elif method == "resources/read":  # 新增代码+MCPTransport: 处理 resource 读取请求；若省略: HTTP read_resource 能力没有覆盖
                    result = {"contents": [{"uri": params.get("uri", ""), "mimeType": "text/markdown", "text": "remote resource body"}]}  # 新增代码+MCPTransport: 返回标准资源文本；若省略: 资源正文无法验证
                elif method == "prompts/list":  # 新增代码+MCPTransport: 处理 prompt 列表请求；若省略: HTTP prompts 能力没有覆盖
                    result = {"prompts": [{"name": "brief", "description": "HTTP prompt", "arguments": [{"name": "topic"}]}]}  # 新增代码+MCPTransport: 返回一个远程 prompt；若省略: registry.list_prompts 结果为空
                elif method == "prompts/get":  # 新增代码+MCPTransport: 处理 prompt 读取请求；若省略: HTTP read_prompt 能力没有覆盖
                    prompt_arguments = params.get("arguments", {}) if isinstance(params.get("arguments", {}), dict) else {}  # 新增代码+MCPTransport: 读取 prompt 参数；若省略: 带参 prompt 无法验证
                    result = {"description": "HTTP prompt", "messages": [{"role": "user", "content": {"type": "text", "text": "plan " + str(prompt_arguments.get("topic", ""))}}]}  # 新增代码+MCPTransport: 返回标准 prompt message；若省略: prompt 正文转换无法验证
                else:  # 新增代码+MCPTransport: 处理未知方法；若省略: fake server 遇到意外请求会无响应
                    self._send_json({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown method"}})  # 新增代码+MCPTransport: 返回 JSON-RPC 未知方法错误；若省略: 客户端可能一直等待
                    return  # 新增代码+MCPTransport: 错误响应后退出；若省略: 后续还会尝试发送成功响应
                self._send_json({"jsonrpc": "2.0", "id": request_id, "result": result}, session_id="session-1" if method == "initialize" else "")  # 新增代码+MCPTransport: 发送成功响应并在初始化时下发 session；若省略: 客户端无法验证 session 继承

            def _send_json(self, payload: dict[str, object], session_id: str = "") -> None:  # 新增代码+MCPTransport: 统一发送 JSON 响应；若省略: 每个分支会重复写响应头和编码
                response_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # 新增代码+MCPTransport: 把响应对象编码成 UTF-8 JSON；若省略: HTTP client 读不到标准 body
                self.send_response(200)  # 新增代码+MCPTransport: 返回 HTTP 200 表示请求成功；若省略: urllib 会把响应当异常
                self.send_header("Content-Type", "application/json")  # 新增代码+MCPTransport: 声明 JSON 响应类型；若省略: 客户端无法区分 JSON 和 SSE
                if session_id:  # 新增代码+MCPTransport: 只有初始化响应需要下发 session；若省略: 所有响应都会多带空 session
                    self.send_header("Mcp-Session-Id", session_id)  # 新增代码+MCPTransport: 按规范返回 session id；若省略: 客户端无法在后续请求携带会话
                self.send_header("Content-Length", str(len(response_body)))  # 新增代码+MCPTransport: 写明响应长度；若省略: 客户端读取 body 可能不稳定
                self.end_headers()  # 新增代码+MCPTransport: 结束响应头；若省略: body 不会被客户端正常解析
                self.wfile.write(response_body)  # 新增代码+MCPTransport: 写出响应 body；若省略: 客户端会收到空响应

        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)  # 新增代码+MCPTransport: 在随机本地端口启动 fake HTTP MCP server；若省略: 测试会依赖外部网络
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)  # 新增代码+MCPTransport: 创建后台线程运行 HTTP server；若省略: 当前测试会阻塞
        thread.start()  # 新增代码+MCPTransport: 启动 fake HTTP MCP server；若省略: 客户端连接会失败
        registry = McpToolRegistry.from_configs([McpServerConfig(name="remote", command="", transport="http", url=f"http://127.0.0.1:{httpd.server_port}/mcp", headers={"Authorization": "Bearer test"})])  # 新增代码+MCPTransport: 创建指向本地 HTTP endpoint 的 registry；若省略: HTTP client 没有运行入口
        try:  # 新增代码+MCPTransport: 确保测试结束后清理 registry 和 HTTP server；若省略: 端口和线程可能残留
            registry.start()  # 新增代码+MCPTransport: 启动 HTTP MCP client 并读取 tools/list；若省略: tool_schemas 不会生成
            tool_names = [schema["function"]["name"] for schema in registry.tool_schemas()]  # 新增代码+MCPTransport: 收集模型可见工具名；若省略: 无法断言 HTTP 工具暴露
            self.assertIn("mcp__remote__echo", tool_names)  # 新增代码+MCPTransport: 断言 HTTP 工具被包装成 mcp__ 前缀；若省略: 工具命名回归不会被发现
            self.assertEqual(registry.call_tool("mcp__remote__echo", {"text": "ping"}), "echo:ping")  # 新增代码+MCPTransport: 断言 HTTP tools/call 结果可读；若省略: 只能证明工具可见不能证明可执行
            resources = registry.list_resources("remote")  # 新增代码+MCPTransport: 读取 HTTP MCP resources 列表；若省略: resources/list 没有测试对象
            self.assertEqual(resources[0]["uri"], "file://remote.md")  # 新增代码+MCPTransport: 断言资源 URI 正确；若省略: 资源发现结果可能错乱
            self.assertIn("remote resource body", registry.read_resource("remote", "file://remote.md"))  # 新增代码+MCPTransport: 断言 HTTP resources/read 返回正文；若省略: 资源读取链路可能坏掉
            prompts = registry.list_prompts("remote")  # 新增代码+MCPTransport: 读取 HTTP MCP prompts 列表；若省略: prompts/list 没有测试对象
            self.assertEqual(prompts[0]["name"], "brief")  # 新增代码+MCPTransport: 断言 prompt 名称正确；若省略: prompt 发现结果可能错乱
            self.assertIn("plan MCP", registry.read_prompt("remote", "brief", {"topic": "MCP"}))  # 新增代码+MCPTransport: 断言 HTTP prompts/get 支持参数并返回正文；若省略: prompt 读取链路可能坏掉
            tools_list_request = next(item for item in requests if item["method"] == "tools/list")  # 新增代码+MCPTransport: 找到初始化后的 tools/list 请求；若省略: 无法验证关键 HTTP header
            self.assertIn("application/json", tools_list_request["accept"])  # 新增代码+MCPTransport: 断言客户端接受 JSON 响应；若省略: Streamable HTTP 基本要求可能缺失
            self.assertIn("text/event-stream", tools_list_request["accept"])  # 新增代码+MCPTransport: 断言客户端接受 SSE 响应；若省略: 支持流式响应的要求可能缺失
            self.assertEqual(tools_list_request["authorization"], "Bearer test")  # 新增代码+MCPTransport: 断言自定义 headers 被发送；若省略: 远程鉴权配置可能无效
            self.assertEqual(tools_list_request["session"], "session-1")  # 新增代码+MCPTransport: 断言初始化返回的 session 被用于后续请求；若省略: 有状态 MCP server 可能不可用
            self.assertEqual(tools_list_request["version"], "2025-06-18")  # 新增代码+MCPTransport: 断言后续请求带协议版本头；若省略: HTTP server 无法按协商版本处理请求
        finally:  # 新增代码+MCPTransport: 进入资源清理分支；若省略: 测试失败时也可能残留 server
            registry.close()  # 新增代码+MCPTransport: 关闭 registry 内 client；若省略: 后续扩展真实连接时可能泄漏资源
            httpd.shutdown()  # 新增代码+MCPTransport: 请求 HTTP server 停止；若省略: 后台线程会继续监听
            httpd.server_close()  # 新增代码+MCPTransport: 释放监听端口；若省略: Windows 上端口句柄可能残留
            thread.join(timeout=2)  # 新增代码+MCPTransport: 等待 HTTP server 线程退出；若省略: 测试进程关闭时状态不确定
    def test_mcp_http_client_parses_post_sse_events_and_records_stream_state(self) -> None:  # 新增代码+HTTP流生命周期: 验证 POST 返回 SSE 时能解析事件并记录流状态；若省略: 未来实现可能只会解析 JSON 而丢失 event id 和 retry
        requests: list[dict[str, str]] = []  # 新增代码+HTTP流生命周期: 保存 fake server 收到的请求头和方法；若省略: 测试无法确认 session 与协议版本是否被后续请求携带
        host = socket.gethostbyname("localhost")  # 新增代码+HTTP流生命周期: 把 localhost 解析成 IPv4 回环地址用于本地 server；若省略: Windows 上地址族选择可能不稳定

        class Handler(http.server.BaseHTTPRequestHandler):  # 新增代码+HTTP流生命周期: 定义只服务本测试的 Streamable HTTP MCP server；若省略: 测试会依赖真实远程服务且不可控
            def log_message(self, format: str, *args: object) -> None:  # 新增代码+HTTP流生命周期: 覆盖默认访问日志，保持 unittest 输出干净；若省略: 每个 HTTP 请求都会把噪声写到测试输出
                return None  # 新增代码+HTTP流生命周期: 明确不输出访问日志；若省略: 父类会继续写 stderr 影响红灯结果阅读

            def do_POST(self) -> None:  # 新增代码+HTTP流生命周期: 处理 initialize、initialized notification 和 tools/list；若省略: HTTP client 没有可交互的服务器
                length = int(self.headers.get("Content-Length", "0"))  # 新增代码+HTTP流生命周期: 读取请求体长度以便完整读取 JSON-RPC；若省略: fake server 可能读不到客户端发送的方法
                body = self.rfile.read(length).decode("utf-8")  # 新增代码+HTTP流生命周期: 按 UTF-8 读取请求体；若省略: 中文或 JSON 内容可能无法正确解析
                message = json.loads(body) if body else {}  # 新增代码+HTTP流生命周期: 把 JSON-RPC body 转成字典；若省略: 后续无法根据 method 分支响应
                method = str(message.get("method", ""))  # 新增代码+HTTP流生命周期: 取出 JSON-RPC 方法名；若省略: fake server 不知道该返回初始化还是工具列表
                requests.append(  # 新增代码+HTTP流生命周期: 记录本次请求的关键字段；若省略: 测试无法验证客户端是否按生命周期发送 header
                    {  # 新增代码+HTTP流生命周期: 创建请求审计对象；若省略: 请求记录缺少结构化字段
                        "method": method,  # 新增代码+HTTP流生命周期: 保存方法名用于定位 tools/list 请求；若省略: 多个 POST 请求无法区分
                        "session": self.headers.get("Mcp-Session-Id", ""),  # 新增代码+HTTP流生命周期: 保存会话 header；若省略: 无法断言初始化 session 被复用
                        "version": self.headers.get("MCP-Protocol-Version", ""),  # 新增代码+HTTP流生命周期: 保存协议版本 header；若省略: 无法断言协商版本进入后续请求
                    }  # 新增代码+HTTP流生命周期: 结束请求审计对象；若省略: Python 字典语法不完整
                )  # 新增代码+HTTP流生命周期: 把请求审计对象追加到列表；若省略: 测试结束时没有可断言数据
                if "id" not in message:  # 新增代码+HTTP流生命周期: 识别 initialized notification 这类无响应 id 的消息；若省略: fake server 会错误地要求通知也有 JSON-RPC 响应
                    self.send_response(202)  # 新增代码+HTTP流生命周期: 按 Streamable HTTP 习惯接受 notification；若省略: 客户端会把 initialized 当失败
                    self.end_headers()  # 新增代码+HTTP流生命周期: 结束 202 响应头；若省略: 客户端可能一直等响应完成
                    return  # 新增代码+HTTP流生命周期: notification 不需要继续返回 JSON-RPC body；若省略: 后续代码会访问不该访问的 request id
                request_id = message.get("id")  # 新增代码+HTTP流生命周期: 保存请求 id 用于响应匹配；若省略: 客户端无法确认响应对应哪个请求
                if method == "initialize":  # 新增代码+HTTP流生命周期: 初始化分支下发协议版本和 session；若省略: 后续 tools/list 无法携带正确生命周期头
                    self._send_json(  # 新增代码+HTTP流生命周期: 发送标准 JSON 初始化响应；若省略: HTTP client 无法完成 start
                        {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}}}},  # 新增代码+HTTP流生命周期: 返回未来协议版本和工具能力；若省略: 测试无法断言版本继承
                        session_id="stream-session",  # 新增代码+HTTP流生命周期: 下发固定 session id；若省略: 后续请求不会有可验证的会话值
                    )  # 新增代码+HTTP流生命周期: 初始化响应发送结束；若省略: Python 调用语法不完整
                    return  # 新增代码+HTTP流生命周期: 初始化已经响应完毕；若省略: 代码会继续进入未知方法错误
                if method == "tools/list":  # 新增代码+HTTP流生命周期: 工具列表分支返回 SSE 事件流；若省略: 无法覆盖 POST SSE 响应解析
                    self._send_tools_sse(request_id)  # 新增代码+HTTP流生命周期: 发送包含 retry、notification 和响应的 SSE；若省略: 测试不会驱动流状态记录
                    return  # 新增代码+HTTP流生命周期: tools/list 已经响应完毕；若省略: 代码会继续发送未知方法错误
                self._send_json({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown"}})  # 新增代码+HTTP流生命周期: 对意外方法返回明确错误；若省略: 客户端遇到多余请求会挂起

            def _send_json(self, payload: dict[str, object], session_id: str = "") -> None:  # 新增代码+HTTP流生命周期: 统一发送 JSON 响应；若省略: 初始化和错误响应会重复编码逻辑
                response_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # 新增代码+HTTP流生命周期: 把响应对象编码成 UTF-8 JSON；若省略: 客户端无法解析响应体
                self.send_response(200)  # 新增代码+HTTP流生命周期: 声明请求成功；若省略: urllib 会把响应当异常
                self.send_header("Content-Type", "application/json")  # 新增代码+HTTP流生命周期: 标明响应是 JSON；若省略: 客户端无法区分 JSON 与 SSE
                if session_id:  # 新增代码+HTTP流生命周期: 只在初始化响应中写 session；若省略: 空 session 可能覆盖客户端状态
                    self.send_header("Mcp-Session-Id", session_id)  # 新增代码+HTTP流生命周期: 写入服务器分配的会话 id；若省略: 后续请求无法按有状态协议继续
                self.send_header("Content-Length", str(len(response_body)))  # 新增代码+HTTP流生命周期: 写明响应长度；若省略: 客户端读取响应可能不稳定
                self.end_headers()  # 新增代码+HTTP流生命周期: 结束响应头；若省略: body 不会被客户端正常读取
                self.wfile.write(response_body)  # 新增代码+HTTP流生命周期: 写出 JSON body；若省略: 客户端会收到空响应

            def _send_tools_sse(self, request_id: object) -> None:  # 新增代码+HTTP流生命周期: 构造 tools/list 的 SSE 响应；若省略: 无法测试 POST SSE 多事件解析
                response_message = {"jsonrpc": "2.0", "id": request_id, "result": {"tools": [{"name": "echo", "description": "Echo over SSE", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}}]}}  # 新增代码+HTTP流生命周期: 准备最终 JSON-RPC 工具列表响应；若省略: registry 看不到 mcp__remote__echo
                stream_text = (  # 新增代码+HTTP流生命周期: 准备包含三段事件的 SSE 文本；若省略: 流状态无法覆盖 id、retry 和通知混排
                    "id: event-1\n"  # 新增代码+HTTP流生命周期: 第一段事件 id 用于验证未来解析器能推进事件游标；若省略: last_event_id 不会经历空 data 事件
                    "retry: 25\n"  # 新增代码+HTTP流生命周期: 第一段事件 retry 用于验证未来解析器保存重试间隔；若省略: retry_ms 行为没有测试保护
                    "data:\n\n"  # 新增代码+HTTP流生命周期: 第一段事件故意为空 data；若省略: 解析器可能只在有 JSON 时才更新状态而不被发现
                    "id: event-2\n"  # 新增代码+HTTP流生命周期: 第二段事件 id 用于验证通知事件也会推进游标；若省略: notification 场景没有覆盖
                    'data: {"jsonrpc":"2.0","method":"notifications/message","params":{"level":"info","data":"hello"}}\n\n'  # 新增代码+HTTP流生命周期: 第二段事件放 JSON-RPC notification；若省略: 解析器可能把 notification 当错误或最终结果
                    "id: event-3\n"  # 新增代码+HTTP流生命周期: 第三段事件 id 是最终应记录的 last_event_id；若省略: 断言无法定位最终游标
                    f"data: {json.dumps(response_message, ensure_ascii=False)}\n\n"  # 新增代码+HTTP流生命周期: 第三段事件放匹配 request_id 的 JSON-RPC 响应；若省略: tools/list 不会成功返回 echo 工具
                )  # 新增代码+HTTP流生命周期: SSE 文本构造结束；若省略: Python 字符串拼接语法不完整
                response_body = stream_text.encode("utf-8")  # 新增代码+HTTP流生命周期: 把 SSE 文本编码成 UTF-8；若省略: HTTP 响应无法发送字节
                self.send_response(200)  # 新增代码+HTTP流生命周期: 返回成功状态；若省略: 客户端不会尝试解析事件流
                self.send_header("Content-Type", "text/event-stream")  # 新增代码+HTTP流生命周期: 声明响应是 SSE；若省略: 客户端可能按 JSON 解析
                self.send_header("Content-Length", str(len(response_body)))  # 新增代码+HTTP流生命周期: 写明响应长度；若省略: urllib 读取完成时机可能不稳定
                self.end_headers()  # 新增代码+HTTP流生命周期: 结束 SSE 响应头；若省略: 客户端收不到 body
                self.wfile.write(response_body)  # 新增代码+HTTP流生命周期: 写出 SSE body；若省略: 测试没有事件可解析

        httpd = http.server.ThreadingHTTPServer((host, 0), Handler)  # 新增代码+HTTP流生命周期: 在本机随机端口启动 fake MCP HTTP server；若省略: 测试会依赖外部服务
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)  # 新增代码+HTTP流生命周期: 用后台线程运行 HTTP server；若省略: 当前测试会阻塞在 serve_forever
        thread.start()  # 新增代码+HTTP流生命周期: 启动 fake server 监听；若省略: registry.start 会连接失败
        registry = McpToolRegistry.from_configs([McpServerConfig(name="remote", command="", transport="http", url=f"http://{host}:{httpd.server_port}/mcp")])  # 新增代码+HTTP流生命周期: 创建指向 fake server 的 HTTP registry；若省略: 测试无法调用真实 client 路径
        try:  # 新增代码+HTTP流生命周期: 确保无论红灯如何失败都清理 server；若省略: 失败时端口和线程可能残留
            registry.start()  # 新增代码+HTTP流生命周期: 触发 initialize、initialized 和 tools/list；若省略: SSE POST 解析不会发生
            tool_names = [schema["function"]["name"] for schema in registry.tool_schemas()]  # 新增代码+HTTP流生命周期: 收集模型可见工具名；若省略: 无法断言 echo 工具已从 SSE 响应注册
            self.assertIn("mcp__remote__echo", tool_names)  # 新增代码+HTTP流生命周期: 断言 SSE 里的 echo 工具可见；若省略: 只检查状态会漏掉解析结果是否可用
            tools_list_request = next(item for item in requests if item["method"] == "tools/list")  # 新增代码+HTTP流生命周期: 找到 tools/list 请求记录；若省略: 无法验证 session 和版本头
            self.assertEqual(tools_list_request["session"], "stream-session")  # 新增代码+HTTP流生命周期: 断言 tools/list 带初始化返回的 session；若省略: 有状态 server 回归不会被发现
            self.assertEqual(tools_list_request["version"], "2025-11-25")  # 新增代码+HTTP流生命周期: 断言 tools/list 带协商协议版本；若省略: 协议升级回归不会被发现
            self.assertEqual(registry.stream_state("remote")["last_event_id"], "event-3")  # 新增代码+HTTP流生命周期: 断言 registry 暴露最终 SSE 事件 id；若省略: 断线续传无法知道从哪里恢复
            self.assertEqual(registry.stream_state("remote")["retry_ms"], 25)  # 新增代码+HTTP流生命周期: 断言 registry 暴露 SSE retry 间隔；若省略: 客户端无法按服务端建议节流重连
        finally:  # 新增代码+HTTP流生命周期: 进入清理分支；若省略: 红灯失败时仍可能泄漏本地 server
            registry.close()  # 新增代码+HTTP流生命周期: 关闭 registry 管理的 HTTP client；若省略: 后续实现可能残留会话状态
            httpd.shutdown()  # 新增代码+HTTP流生命周期: 停止 fake HTTP server；若省略: 后台线程会继续运行
            httpd.server_close()  # 新增代码+HTTP流生命周期: 释放监听端口；若省略: Windows 上端口句柄可能残留
            thread.join(timeout=2)  # 新增代码+HTTP流生命周期: 等待 server 线程退出；若省略: 测试进程状态可能不确定
    def test_mcp_http_listen_stream_sends_last_event_id_and_handles_405(self) -> None:  # 新增代码+HTTP流生命周期: 验证 GET 监听会携带 Last-Event-ID 并优雅处理 405；若省略: 后续实现可能无法恢复监听或错误提示难懂
        get_requests: list[dict[str, str]] = []  # 新增代码+HTTP流生命周期: 保存 GET 请求头；若省略: 无法断言 Last-Event-ID、session 和 Accept
        get_count = 0  # 新增代码+HTTP流生命周期: 记录 fake server 已处理的 GET 次数；若省略: 无法让两次监听返回不同事件
        host = socket.gethostbyname("localhost")  # 新增代码+HTTP流生命周期: 使用 IPv4 回环地址启动本地 server；若省略: 本地连接地址可能不稳定

        class ListenHandler(http.server.BaseHTTPRequestHandler):  # 新增代码+HTTP流生命周期: 定义支持 initialize、tools/list 和 GET SSE 的 fake server；若省略: listen_stream 没有可验证对象
            def log_message(self, format: str, *args: object) -> None:  # 新增代码+HTTP流生命周期: 屏蔽 HTTP 访问日志；若省略: 测试输出会混入无关日志
                return None  # 新增代码+HTTP流生命周期: 明确不输出日志；若省略: 父类会写 stderr

            def do_POST(self) -> None:  # 新增代码+HTTP流生命周期: 支持 registry.start 需要的初始化和工具发现；若省略: GET 监听前 client 无法启动
                length = int(self.headers.get("Content-Length", "0"))  # 新增代码+HTTP流生命周期: 读取 JSON-RPC body 长度；若省略: fake server 无法读完整请求
                body = self.rfile.read(length).decode("utf-8")  # 新增代码+HTTP流生命周期: 解码请求体；若省略: 后续 json.loads 没有输入
                message = json.loads(body) if body else {}  # 新增代码+HTTP流生命周期: 解析 JSON-RPC 消息；若省略: fake server 无法判断 method
                method = str(message.get("method", ""))  # 新增代码+HTTP流生命周期: 提取方法名；若省略: 初始化和工具列表无法区分
                if "id" not in message:  # 新增代码+HTTP流生命周期: 识别 initialized notification；若省略: fake server 会错误地要求 notification 返回 body
                    self.send_response(202)  # 新增代码+HTTP流生命周期: 接受 notification；若省略: client.start 会误判就绪通知失败
                    self.end_headers()  # 新增代码+HTTP流生命周期: 结束 notification 响应；若省略: 客户端可能等待更多数据
                    return  # 新增代码+HTTP流生命周期: notification 不再继续处理；若省略: 后续会构造错误响应
                request_id = message.get("id")  # 新增代码+HTTP流生命周期: 保存请求 id；若省略: JSON-RPC 响应无法匹配
                if method == "initialize":  # 新增代码+HTTP流生命周期: 初始化分支；若省略: client 无法得到 session
                    self._send_json({"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}}}}, session_id="listen-session")  # 新增代码+HTTP流生命周期: 返回协议版本和 listen-session；若省略: GET 无法验证会话 header
                    return  # 新增代码+HTTP流生命周期: 初始化响应完成后退出；若省略: 会继续发送错误响应
                if method == "tools/list":  # 新增代码+HTTP流生命周期: 工具列表分支；若省略: registry.start 无法完成
                    self._send_json({"jsonrpc": "2.0", "id": request_id, "result": {"tools": []}})  # 新增代码+HTTP流生命周期: 返回空工具列表，聚焦 GET 监听行为；若省略: 启动流程会失败
                    return  # 新增代码+HTTP流生命周期: tools/list 响应完成后退出；若省略: 会继续发送错误响应
                self._send_json({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown"}})  # 新增代码+HTTP流生命周期: 未知方法返回明确错误；若省略: 意外请求会挂起

            def do_GET(self) -> None:  # 新增代码+HTTP流生命周期: 提供 listen_stream 需要的 GET SSE 通道；若省略: 无法验证 Last-Event-ID 续传
                nonlocal get_count  # 新增代码+HTTP流生命周期: 允许方法更新外层 GET 次数；若省略: 两次监听无法返回不同事件
                get_count += 1  # 新增代码+HTTP流生命周期: 记录当前是第几次 GET；若省略: 无法区分 listen-1 和 listen-2
                event_id = "listen-1" if get_count == 1 else "listen-2"  # 新增代码+HTTP流生命周期: 第一轮返回 listen-1，第二轮返回 listen-2；若省略: resume 行为没有可观察差异
                get_requests.append(  # 新增代码+HTTP流生命周期: 记录 GET 请求头；若省略: 测试无法检查客户端发了什么
                    {  # 新增代码+HTTP流生命周期: GET 审计对象开始；若省略: 请求记录结构不完整
                        "last_event_id": self.headers.get("Last-Event-ID", ""),  # 新增代码+HTTP流生命周期: 保存续传游标；若省略: 无法断言第二次 GET 从 listen-1 恢复
                        "session": self.headers.get("Mcp-Session-Id", ""),  # 新增代码+HTTP流生命周期: 保存 session header；若省略: 无法断言 GET 继承 initialize session
                        "accept": self.headers.get("Accept", ""),  # 新增代码+HTTP流生命周期: 保存 Accept header；若省略: 无法断言客户端声明接受 SSE
                    }  # 新增代码+HTTP流生命周期: GET 审计对象结束；若省略: Python 字典语法不完整
                )  # 新增代码+HTTP流生命周期: 追加 GET 请求记录；若省略: 断言没有数据来源
                stream_text = f"id: {event_id}\ndata: {{\"type\":\"notice\",\"id\":\"{event_id}\"}}\n\n"  # 新增代码+HTTP流生命周期: 返回一条带 id 的 SSE 事件；若省略: listen_stream 没有事件可读
                response_body = stream_text.encode("utf-8")  # 新增代码+HTTP流生命周期: 把 SSE 文本编码成字节；若省略: HTTP body 无法写出
                self.send_response(200)  # 新增代码+HTTP流生命周期: 返回 GET 成功；若省略: 客户端不会解析 SSE
                self.send_header("Content-Type", "text/event-stream")  # 新增代码+HTTP流生命周期: 标明响应是 SSE；若省略: listen_stream 可能无法识别流
                self.send_header("Content-Length", str(len(response_body)))  # 新增代码+HTTP流生命周期: 写明响应长度；若省略: 测试读取完成时机不稳定
                self.end_headers()  # 新增代码+HTTP流生命周期: 结束响应头；若省略: 客户端收不到事件体
                self.wfile.write(response_body)  # 新增代码+HTTP流生命周期: 写出事件流；若省略: listen_stream 读不到事件

            def _send_json(self, payload: dict[str, object], session_id: str = "") -> None:  # 新增代码+HTTP流生命周期: 统一发送 JSON 响应；若省略: POST 分支会重复编码和 header
                response_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # 新增代码+HTTP流生命周期: 编码 JSON 响应；若省略: 客户端无法解析 body
                self.send_response(200)  # 新增代码+HTTP流生命周期: 返回成功状态；若省略: urllib 会抛 HTTPError
                self.send_header("Content-Type", "application/json")  # 新增代码+HTTP流生命周期: 标明 JSON 类型；若省略: 客户端可能误判响应格式
                if session_id:  # 新增代码+HTTP流生命周期: 只有 initialize 需要设置 session；若省略: 空 session 可能污染状态
                    self.send_header("Mcp-Session-Id", session_id)  # 新增代码+HTTP流生命周期: 下发 listen-session；若省略: GET 无法携带会话
                self.send_header("Content-Length", str(len(response_body)))  # 新增代码+HTTP流生命周期: 写明响应长度；若省略: 客户端读取可能不稳定
                self.end_headers()  # 新增代码+HTTP流生命周期: 结束响应头；若省略: body 不会正常发送
                self.wfile.write(response_body)  # 新增代码+HTTP流生命周期: 写出 JSON body；若省略: POST 请求没有响应体

        httpd = http.server.ThreadingHTTPServer((host, 0), ListenHandler)  # 新增代码+HTTP流生命周期: 启动支持 GET SSE 的 fake server；若省略: listen_stream 无法连接
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)  # 新增代码+HTTP流生命周期: 后台运行 fake server；若省略: 测试线程会阻塞
        thread.start()  # 新增代码+HTTP流生命周期: 开始监听本地端口；若省略: registry.start 会连接失败
        registry = McpToolRegistry.from_configs([McpServerConfig(name="remote", command="", transport="http", url=f"http://{host}:{httpd.server_port}/mcp")])  # 新增代码+HTTP流生命周期: 创建待验证的 HTTP registry；若省略: 无法调用 listen_stream
        try:  # 新增代码+HTTP流生命周期: 确保第一台 fake server 被清理；若省略: 红灯失败会残留端口
            registry.start()  # 新增代码+HTTP流生命周期: 完成 initialize 和 tools/list；若省略: listen_stream 缺少 session 状态
            first_events = registry.listen_stream("remote", max_events=2, timeout_seconds=1.0, resume=True)  # 新增代码+HTTP流生命周期: 第一次有界 GET 监听；若省略: 无法验证首次不带 Last-Event-ID
            second_events = registry.listen_stream("remote", max_events=2, timeout_seconds=1.0, resume=True)  # 新增代码+HTTP流生命周期: 第二次有界 GET 监听；若省略: 无法验证续传带 Last-Event-ID
            self.assertIn("listen-1", str(first_events))  # 新增代码+HTTP流生命周期: 断言第一次读到 listen-1；若省略: GET 返回内容是否被解析不可见
            self.assertIn("listen-2", str(second_events))  # 新增代码+HTTP流生命周期: 断言第二次读到 listen-2；若省略: 续传后新事件是否读到不可见
            self.assertEqual(get_requests[0]["last_event_id"], "")  # 新增代码+HTTP流生命周期: 断言第一次 GET 不带 Last-Event-ID；若省略: 初始监听可能错误跳过事件
            self.assertEqual(get_requests[1]["last_event_id"], "listen-1")  # 新增代码+HTTP流生命周期: 断言第二次 GET 从 listen-1 续传；若省略: 断线恢复游标回归不会被发现
            self.assertEqual(get_requests[0]["session"], "listen-session")  # 新增代码+HTTP流生命周期: 断言 GET 带 initialize 下发的 session；若省略: 有状态监听 server 可能不可用
            self.assertIn("text/event-stream", get_requests[0]["accept"])  # 新增代码+HTTP流生命周期: 断言 GET Accept 声明 SSE；若省略: server 可能不知道客户端要事件流
        finally:  # 新增代码+HTTP流生命周期: 清理第一台 fake server；若省略: 测试失败时会泄漏本地线程
            registry.close()  # 新增代码+HTTP流生命周期: 关闭 registry；若省略: 后续实现可能保留 HTTP 状态
            httpd.shutdown()  # 新增代码+HTTP流生命周期: 停止 GET SSE fake server；若省略: 后台线程继续监听
            httpd.server_close()  # 新增代码+HTTP流生命周期: 释放本地端口；若省略: Windows 端口句柄可能残留
            thread.join(timeout=2)  # 新增代码+HTTP流生命周期: 等待后台线程退出；若省略: 测试进程清理不确定

        class MethodNotAllowedHandler(http.server.BaseHTTPRequestHandler):  # 新增代码+HTTP流生命周期: 定义 GET 返回 405 的 fake server；若省略: 不支持 GET 的边界提示没有测试
            def log_message(self, format: str, *args: object) -> None:  # 新增代码+HTTP流生命周期: 屏蔽 405 server 日志；若省略: 测试输出会混入访问日志
                return None  # 新增代码+HTTP流生命周期: 明确静默日志；若省略: 父类会写 stderr

            def do_POST(self) -> None:  # 新增代码+HTTP流生命周期: 支持 initialize 和 tools/list 让 registry 能启动；若省略: 405 测试无法到达 GET 边界
                length = int(self.headers.get("Content-Length", "0"))  # 新增代码+HTTP流生命周期: 读取请求长度；若省略: fake server 无法解析 POST
                body = self.rfile.read(length).decode("utf-8")  # 新增代码+HTTP流生命周期: 解码请求体；若省略: json.loads 没有输入
                message = json.loads(body) if body else {}  # 新增代码+HTTP流生命周期: 解析 JSON-RPC；若省略: 方法分支无法判断
                method = str(message.get("method", ""))  # 新增代码+HTTP流生命周期: 读取方法名；若省略: 初始化和工具列表无法区分
                if "id" not in message:  # 新增代码+HTTP流生命周期: 识别 notification；若省略: initialized 会收到错误响应
                    self.send_response(202)  # 新增代码+HTTP流生命周期: 接受 notification；若省略: client.start 可能失败
                    self.end_headers()  # 新增代码+HTTP流生命周期: 结束 202 响应；若省略: 客户端可能等待
                    return  # 新增代码+HTTP流生命周期: notification 不再继续；若省略: 会构造多余 JSON 响应
                request_id = message.get("id")  # 新增代码+HTTP流生命周期: 保存请求 id；若省略: 响应无法匹配
                result = {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}}} if method == "initialize" else {"tools": []}  # 新增代码+HTTP流生命周期: 初始化返回协议，tools/list 返回空工具；若省略: registry_405 无法启动
                session_id = "listen-session" if method == "initialize" else ""  # 新增代码+HTTP流生命周期: 只在初始化下发 session；若省略: GET 无法验证已存在 session 状态
                self._send_json({"jsonrpc": "2.0", "id": request_id, "result": result}, session_id=session_id)  # 新增代码+HTTP流生命周期: 发送成功 JSON-RPC 响应；若省略: registry_405.start 会失败

            def do_GET(self) -> None:  # 新增代码+HTTP流生命周期: 模拟不提供 GET 监听的 server；若省略: 405 边界无法触发
                message = "GET 不提供 GET stream"  # 新增代码+HTTP流生命周期: 准备可读错误正文；若省略: 失败信息可能没有中文边界提示
                response_body = message.encode("utf-8")  # 新增代码+HTTP流生命周期: 编码错误正文；若省略: HTTP 响应无法写 body
                self.send_response(405)  # 新增代码+HTTP流生命周期: 返回 Method Not Allowed；若省略: 客户端无法识别 GET 不支持
                self.send_header("Content-Type", "text/plain; charset=utf-8")  # 新增代码+HTTP流生命周期: 标明错误正文是 UTF-8 文本；若省略: 中文提示可能乱码
                self.send_header("Content-Length", str(len(response_body)))  # 新增代码+HTTP流生命周期: 写明响应长度；若省略: 客户端读取错误正文不稳定
                self.end_headers()  # 新增代码+HTTP流生命周期: 结束错误响应头；若省略: body 不会被客户端读取
                self.wfile.write(response_body)  # 新增代码+HTTP流生命周期: 写出错误正文；若省略: listen_stream 无法返回可读边界

            def _send_json(self, payload: dict[str, object], session_id: str = "") -> None:  # 新增代码+HTTP流生命周期: 统一发送 JSON；若省略: 405 server 的 POST 响应会重复代码
                response_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # 新增代码+HTTP流生命周期: 编码 JSON 响应；若省略: 客户端无法解析
                self.send_response(200)  # 新增代码+HTTP流生命周期: 返回 POST 成功；若省略: registry_405.start 会失败
                self.send_header("Content-Type", "application/json")  # 新增代码+HTTP流生命周期: 标明 JSON 类型；若省略: 客户端可能误判格式
                if session_id:  # 新增代码+HTTP流生命周期: 初始化时写 session；若省略: client 不会保存 listen-session
                    self.send_header("Mcp-Session-Id", session_id)  # 新增代码+HTTP流生命周期: 下发 session；若省略: GET 请求缺少会话上下文
                self.send_header("Content-Length", str(len(response_body)))  # 新增代码+HTTP流生命周期: 写明响应长度；若省略: 读取完成不稳定
                self.end_headers()  # 新增代码+HTTP流生命周期: 结束响应头；若省略: body 不会发送
                self.wfile.write(response_body)  # 新增代码+HTTP流生命周期: 写出 JSON body；若省略: client 收不到响应

        httpd_405 = http.server.ThreadingHTTPServer((host, 0), MethodNotAllowedHandler)  # 新增代码+HTTP流生命周期: 启动 GET 405 fake server；若省略: 无法验证不支持 GET 的边界
        thread_405 = threading.Thread(target=httpd_405.serve_forever, daemon=True)  # 新增代码+HTTP流生命周期: 后台运行 405 server；若省略: 测试会阻塞
        thread_405.start()  # 新增代码+HTTP流生命周期: 开始监听 405 server；若省略: registry_405 连接失败
        registry_405 = McpToolRegistry.from_configs([McpServerConfig(name="remote", command="", transport="http", url=f"http://{host}:{httpd_405.server_port}/mcp")])  # 新增代码+HTTP流生命周期: 创建指向 405 server 的 registry；若省略: 无法调用 405 边界
        try:  # 新增代码+HTTP流生命周期: 确保 405 server 被清理；若省略: 红灯失败会残留端口
            registry_405.start()  # 新增代码+HTTP流生命周期: 先完成初始化；若省略: listen_stream 的 405 不是在合法 session 中发生
            boundary = registry_405.listen_stream("remote", max_events=2, timeout_seconds=1.0, resume=True)  # 新增代码+HTTP流生命周期: 触发 GET 405 并期待可读边界；若省略: 不支持 GET 的提示没有验证
            self.assertRegex(str(boundary), "405|不提供 GET")  # 新增代码+HTTP流生命周期: 断言返回说明包含状态码或中文边界；若省略: 用户可能只看到底层异常
        finally:  # 新增代码+HTTP流生命周期: 清理 405 server；若省略: 测试失败时会泄漏本地线程
            registry_405.close()  # 新增代码+HTTP流生命周期: 关闭 405 registry；若省略: 后续实现可能残留状态
            httpd_405.shutdown()  # 新增代码+HTTP流生命周期: 停止 405 fake server；若省略: 后台线程继续监听
            httpd_405.server_close()  # 新增代码+HTTP流生命周期: 释放 405 server 端口；若省略: Windows 上端口句柄可能残留
            thread_405.join(timeout=2)  # 新增代码+HTTP流生命周期: 等待 405 server 线程退出；若省略: 测试进程状态不确定
    def test_mcp_http_listen_stream_ignores_sse_comment_heartbeats(self) -> None:  # 新增代码+HTTP流生命周期: 验证 SSE 注释心跳不会消耗 max_events；若省略: 真实长连接可能只读到 keepalive 而漏掉业务事件
        get_requests: list[dict[str, str]] = []  # 新增代码+HTTP流生命周期: 保存 GET 请求头用于断言 Content-Type 边界；若省略: GET 误带请求体类型不会被发现
        host = socket.gethostbyname("localhost")  # 新增代码+HTTP流生命周期: 使用 IPv4 回环地址启动本地 server；若省略: Windows 上 localhost 地址族可能不稳定

        class HeartbeatHandler(http.server.BaseHTTPRequestHandler):  # 新增代码+HTTP流生命周期: 定义先发注释心跳再发真实事件的 fake server；若省略: 无法复现真实 SSE 心跳场景
            def log_message(self, format: str, *args: object) -> None:  # 新增代码+HTTP流生命周期: 屏蔽 HTTP 测试日志；若省略: unittest 输出会混入访问日志
                return None  # 新增代码+HTTP流生命周期: 明确不输出日志；若省略: 父类会写 stderr

            def do_POST(self) -> None:  # 新增代码+HTTP流生命周期: 支持 registry.start 的 initialize 和 tools/list；若省略: GET 心跳测试无法启动 client
                length = int(self.headers.get("Content-Length", "0"))  # 新增代码+HTTP流生命周期: 读取请求体长度；若省略: fake server 无法读完整 JSON-RPC
                body = self.rfile.read(length).decode("utf-8")  # 新增代码+HTTP流生命周期: 解码请求体；若省略: 无法解析请求方法
                message = json.loads(body) if body else {}  # 新增代码+HTTP流生命周期: 解析 JSON-RPC 消息；若省略: fake server 无法按 method 分支
                method = str(message.get("method", ""))  # 新增代码+HTTP流生命周期: 读取方法名；若省略: initialize 和 tools/list 无法区分
                if "id" not in message:  # 新增代码+HTTP流生命周期: 识别 initialized notification；若省略: notification 会被误当请求
                    self.send_response(202)  # 新增代码+HTTP流生命周期: 接受 notification；若省略: client.start 可能失败
                    self.end_headers()  # 新增代码+HTTP流生命周期: 结束 202 响应；若省略: 客户端可能等待
                    return  # 新增代码+HTTP流生命周期: notification 不继续处理；若省略: 会构造多余 JSON 响应
                request_id = message.get("id")  # 新增代码+HTTP流生命周期: 保存请求 id；若省略: 响应无法匹配
                if method == "initialize":  # 新增代码+HTTP流生命周期: 初始化分支下发 session；若省略: GET 无法验证 session 继承
                    self._send_json({"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}}}}, session_id="heartbeat-session")  # 新增代码+HTTP流生命周期: 返回协议和会话；若省略: client 缺少启动状态
                    return  # 新增代码+HTTP流生命周期: 初始化响应完成后退出；若省略: 会继续发送其他响应
                self._send_json({"jsonrpc": "2.0", "id": request_id, "result": {"tools": []}})  # 新增代码+HTTP流生命周期: tools/list 返回空工具；若省略: registry.start 会失败

            def do_GET(self) -> None:  # 新增代码+HTTP流生命周期: 返回无 Content-Length 的长连接 SSE；若省略: 无法验证有界读取不等 EOF
                get_requests.append({"content_type": self.headers.get("Content-Type", "")})  # 新增代码+HTTP流生命周期: 记录 GET Content-Type；若省略: GET 误带 application/json 不会被发现
                self.send_response(200)  # 新增代码+HTTP流生命周期: 返回 GET 成功；若省略: client 会抛 HTTPError
                self.send_header("Content-Type", "text/event-stream")  # 新增代码+HTTP流生命周期: 声明 SSE 响应；若省略: listen_stream 会认为不是事件流
                self.end_headers()  # 新增代码+HTTP流生命周期: 不发送 Content-Length 并结束响应头；若省略: 无法模拟真实长连接 SSE
                self.wfile.write(b": keepalive\n\n")  # 新增代码+HTTP流生命周期: 先发送 SSE 注释心跳；若省略: 无法验证心跳不消耗 max_events
                self.wfile.flush()  # 新增代码+HTTP流生命周期: 立刻推送心跳给客户端；若省略: 客户端可能等不到第一段数据
                self.wfile.write(b"id: real-1\ndata: {\"type\":\"notice\",\"id\":\"real-1\"}\n\n")  # 新增代码+HTTP流生命周期: 发送真实业务事件；若省略: 测试没有应该被读取的目标事件
                self.wfile.flush()  # 新增代码+HTTP流生命周期: 立刻推送真实事件；若省略: 客户端可能等到连接关闭才看到事件
                time.sleep(0.2)  # 新增代码+HTTP流生命周期: 短暂保持连接模拟长流；若省略: 不能覆盖无 EOF 时的有界返回

            def _send_json(self, payload: dict[str, object], session_id: str = "") -> None:  # 新增代码+HTTP流生命周期: 统一发送 JSON 响应；若省略: POST 分支会重复编码逻辑
                response_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # 新增代码+HTTP流生命周期: 编码 JSON body；若省略: 客户端无法解析响应
                self.send_response(200)  # 新增代码+HTTP流生命周期: 返回成功状态；若省略: urllib 会抛异常
                self.send_header("Content-Type", "application/json")  # 新增代码+HTTP流生命周期: 标明 JSON 响应；若省略: 客户端可能误判格式
                if session_id:  # 新增代码+HTTP流生命周期: 只有初始化时写 session；若省略: GET 无法验证会话继承
                    self.send_header("Mcp-Session-Id", session_id)  # 新增代码+HTTP流生命周期: 下发固定 session；若省略: client 没有 session 状态
                self.send_header("Content-Length", str(len(response_body)))  # 新增代码+HTTP流生命周期: 写明 JSON 长度；若省略: 客户端读取可能不稳定
                self.end_headers()  # 新增代码+HTTP流生命周期: 结束响应头；若省略: body 不会正常发送
                self.wfile.write(response_body)  # 新增代码+HTTP流生命周期: 写出响应 body；若省略: POST 没有响应内容

        httpd = http.server.ThreadingHTTPServer((host, 0), HeartbeatHandler)  # 新增代码+HTTP流生命周期: 启动心跳 fake server；若省略: 测试会依赖外部服务
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)  # 新增代码+HTTP流生命周期: 后台运行 fake server；若省略: 测试线程会阻塞
        thread.start()  # 新增代码+HTTP流生命周期: 开始监听本地端口；若省略: registry.start 会连接失败
        registry = McpToolRegistry.from_configs([McpServerConfig(name="remote", command="", transport="http", url=f"http://{host}:{httpd.server_port}/mcp")])  # 新增代码+HTTP流生命周期: 创建指向心跳 server 的 registry；若省略: 无法走真实 HTTP client 路径
        try:  # 新增代码+HTTP流生命周期: 确保测试结束清理资源；若省略: 失败时可能残留端口和线程
            registry.start()  # 新增代码+HTTP流生命周期: 完成 initialize 和 tools/list；若省略: listen_stream 缺少 session
            output = registry.listen_stream("remote", max_events=1, timeout_seconds=1.0, resume=True)  # 新增代码+HTTP流生命周期: 只请求 1 个真实事件；若省略: 无法验证心跳不占用事件额度
            self.assertIn("real-1", output)  # 新增代码+HTTP流生命周期: 断言真实事件被读取；若省略: 心跳误占额度不会被发现
            self.assertNotIn("keepalive", output)  # 新增代码+HTTP流生命周期: 断言注释心跳不进入用户输出；若省略: 输出可能被心跳噪声污染
            self.assertEqual(get_requests[0]["content_type"], "")  # 新增代码+HTTP流生命周期: 断言 GET 不带 Content-Type；若省略: GET header 回归不会被发现
        finally:  # 新增代码+HTTP流生命周期: 清理心跳 fake server 和 registry；若省略: 测试失败时会泄漏资源
            registry.close()  # 新增代码+HTTP流生命周期: 关闭 registry 管理的 client；若省略: 后续实现可能残留状态
            httpd.shutdown()  # 新增代码+HTTP流生命周期: 请求 fake server 停止；若省略: 后台线程继续运行
            httpd.server_close()  # 新增代码+HTTP流生命周期: 释放本地端口；若省略: Windows 上端口句柄可能残留
            thread.join(timeout=2)  # 新增代码+HTTP流生命周期: 等待 server 线程退出；若省略: 测试进程状态不确定
    def test_mcp_http_close_sends_delete_when_session_exists_and_ignores_405(self) -> None:  # 新增代码+HTTP流生命周期: 验证有 session 时 close 会发 DELETE 且忽略 405；若省略: 会话清理和不支持 DELETE 的兼容性没有保护
        host = socket.gethostbyname("localhost")  # 新增代码+HTTP流生命周期: 使用 IPv4 回环地址运行 fake server；若省略: 本地连接地址可能不稳定

        def run_delete_case(delete_status: int) -> list[dict[str, str]]:  # 新增代码+HTTP流生命周期: 封装 200 和 405 两种 DELETE 场景；若省略: 两个状态码会重复大量测试代码
            delete_requests: list[dict[str, str]] = []  # 新增代码+HTTP流生命周期: 保存 DELETE 请求头；若省略: 无法断言 close 是否真的发出了 DELETE

            class DeleteHandler(http.server.BaseHTTPRequestHandler):  # 新增代码+HTTP流生命周期: 定义支持初始化、tools/list 和 DELETE 的 fake server；若省略: close 生命周期无法端到端验证
                def log_message(self, format: str, *args: object) -> None:  # 新增代码+HTTP流生命周期: 屏蔽 HTTP 访问日志；若省略: 测试输出会混入噪声
                    return None  # 新增代码+HTTP流生命周期: 明确静默日志；若省略: 父类会写 stderr

                def do_POST(self) -> None:  # 新增代码+HTTP流生命周期: 支持 registry.start 需要的 POST 请求；若省略: close 前无法建立 session
                    length = int(self.headers.get("Content-Length", "0"))  # 新增代码+HTTP流生命周期: 读取请求长度；若省略: 无法读取 JSON-RPC body
                    body = self.rfile.read(length).decode("utf-8")  # 新增代码+HTTP流生命周期: 解码请求体；若省略: fake server 无法解析方法
                    message = json.loads(body) if body else {}  # 新增代码+HTTP流生命周期: 解析 JSON-RPC 消息；若省略: 无法按 method 返回响应
                    method = str(message.get("method", ""))  # 新增代码+HTTP流生命周期: 提取方法名；若省略: 初始化和工具列表无法区分
                    if "id" not in message:  # 新增代码+HTTP流生命周期: 识别 initialized notification；若省略: fake server 会错误处理 notification
                        self.send_response(202)  # 新增代码+HTTP流生命周期: 接受 notification；若省略: client.start 会误判通知失败
                        self.end_headers()  # 新增代码+HTTP流生命周期: 结束 202 响应；若省略: 客户端可能等待
                        return  # 新增代码+HTTP流生命周期: notification 不需要 JSON-RPC body；若省略: 会继续发送多余响应
                    request_id = message.get("id")  # 新增代码+HTTP流生命周期: 保存请求 id；若省略: 响应无法匹配请求
                    if method == "initialize":  # 新增代码+HTTP流生命周期: 初始化分支返回 session-delete；若省略: close 不知道是否应发送 DELETE
                        self._send_json({"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}}}}, session_id="session-delete")  # 新增代码+HTTP流生命周期: 下发协议版本和删除测试 session；若省略: DELETE header 没有可验证来源
                        return  # 新增代码+HTTP流生命周期: 初始化响应完成；若省略: 会继续发送错误响应
                    if method == "tools/list":  # 新增代码+HTTP流生命周期: 工具列表分支让 registry.start 成功；若省略: 测试无法走到 close
                        self._send_json({"jsonrpc": "2.0", "id": request_id, "result": {"tools": []}})  # 新增代码+HTTP流生命周期: 返回空工具列表聚焦 close 行为；若省略: 启动会失败
                        return  # 新增代码+HTTP流生命周期: tools/list 响应完成；若省略: 会继续发送未知方法错误
                    self._send_json({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown"}})  # 新增代码+HTTP流生命周期: 未知方法返回错误；若省略: 意外请求会挂起

                def do_DELETE(self) -> None:  # 新增代码+HTTP流生命周期: 捕获 close 应发送的 DELETE 请求；若省略: 测试无法证明会话被关闭
                    delete_requests.append(  # 新增代码+HTTP流生命周期: 记录 DELETE 请求头；若省略: 后续无法检查 session 和版本
                        {  # 新增代码+HTTP流生命周期: DELETE 审计对象开始；若省略: 请求记录结构不完整
                            "session": self.headers.get("Mcp-Session-Id", ""),  # 新增代码+HTTP流生命周期: 保存 DELETE session header；若省略: 无法确认关闭的是正确会话
                            "version": self.headers.get("MCP-Protocol-Version", ""),  # 新增代码+HTTP流生命周期: 保存 DELETE 协议版本；若省略: 无法确认 close 也遵守协商版本
                        }  # 新增代码+HTTP流生命周期: DELETE 审计对象结束；若省略: Python 字典语法不完整
                    )  # 新增代码+HTTP流生命周期: 追加 DELETE 请求记录；若省略: 测试看不到 close 副作用
                    self.send_response(delete_status)  # 新增代码+HTTP流生命周期: 按用例返回 200 或 405；若省略: 无法验证 405 被忽略
                    self.end_headers()  # 新增代码+HTTP流生命周期: 结束 DELETE 响应；若省略: 客户端可能等待响应完成

                def _send_json(self, payload: dict[str, object], session_id: str = "") -> None:  # 新增代码+HTTP流生命周期: 统一发送 POST JSON 响应；若省略: 初始化和 tools/list 会重复代码
                    response_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # 新增代码+HTTP流生命周期: 编码响应体；若省略: 客户端无法解析 JSON
                    self.send_response(200)  # 新增代码+HTTP流生命周期: 返回成功状态；若省略: urllib 会抛异常
                    self.send_header("Content-Type", "application/json")  # 新增代码+HTTP流生命周期: 标明 JSON 响应；若省略: 客户端可能误判格式
                    if session_id:  # 新增代码+HTTP流生命周期: 初始化时写 session；若省略: client 不会保存 session-delete
                        self.send_header("Mcp-Session-Id", session_id)  # 新增代码+HTTP流生命周期: 下发 session-delete；若省略: close 无法知道目标会话
                    self.send_header("Content-Length", str(len(response_body)))  # 新增代码+HTTP流生命周期: 写明响应长度；若省略: 客户端读取不稳定
                    self.end_headers()  # 新增代码+HTTP流生命周期: 结束响应头；若省略: body 不会正常发送
                    self.wfile.write(response_body)  # 新增代码+HTTP流生命周期: 写出 JSON body；若省略: POST 请求没有响应

            httpd = http.server.ThreadingHTTPServer((host, 0), DeleteHandler)  # 新增代码+HTTP流生命周期: 启动 DELETE fake server；若省略: close 无法发真实 HTTP 请求
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)  # 新增代码+HTTP流生命周期: 后台运行 fake server；若省略: 测试线程会阻塞
            thread.start()  # 新增代码+HTTP流生命周期: 开始监听本地端口；若省略: registry.start 连接失败
            registry = McpToolRegistry.from_configs([McpServerConfig(name="remote", command="", transport="http", url=f"http://{host}:{httpd.server_port}/mcp")])  # 新增代码+HTTP流生命周期: 创建指向 DELETE fake server 的 registry；若省略: 无法驱动 HTTP close
            try:  # 新增代码+HTTP流生命周期: 确保 server 无论红灯如何都清理；若省略: 失败会残留端口
                registry.start()  # 新增代码+HTTP流生命周期: 建立 session-delete 会话；若省略: close 不应发送 DELETE，测试没有意义
                registry.close()  # 新增代码+HTTP流生命周期: 触发待实现的 HTTP DELETE close；若省略: 无法验证会话关闭请求
            finally:  # 新增代码+HTTP流生命周期: 清理本地 fake server；若省略: 异常时线程和端口会残留
                httpd.shutdown()  # 新增代码+HTTP流生命周期: 停止 fake server；若省略: 后台线程继续运行
                httpd.server_close()  # 新增代码+HTTP流生命周期: 释放监听端口；若省略: Windows 上端口句柄可能残留
                thread.join(timeout=2)  # 新增代码+HTTP流生命周期: 等待后台线程退出；若省略: 测试进程状态不确定
            return delete_requests  # 新增代码+HTTP流生命周期: 返回记录供外层断言；若省略: 外层无法检查 DELETE header

        for delete_status in (200, 405):  # 新增代码+HTTP流生命周期: 同时覆盖正常关闭和 server 不支持 DELETE；若省略: 405 兼容性没有红灯保护
            delete_requests = run_delete_case(delete_status)  # 新增代码+HTTP流生命周期: 执行一个 DELETE 场景；若省略: 测试不会触发 close 行为
            self.assertEqual(len(delete_requests), 1)  # 新增代码+HTTP流生命周期: 断言 close 发送且只发送一次 DELETE；若省略: 不发或重复发 DELETE 都可能漏掉
            self.assertEqual(delete_requests[0]["session"], "session-delete")  # 新增代码+HTTP流生命周期: 断言 DELETE 带正确 session；若省略: server 可能关闭不到目标会话
            self.assertEqual(delete_requests[0]["version"], "2025-11-25")  # 新增代码+HTTP流生命周期: 断言 DELETE 带协商版本；若省略: close 请求可能不符合协议
    def test_mcp_http_request_reinitializes_once_when_session_returns_404(self) -> None:  # 新增代码+HTTP流生命周期: 验证 session 失效返回 404 时只重新初始化一次并重试请求；若省略: 有状态 server 重建会话能力没有红灯保护
        initialize_count = 0  # 新增代码+HTTP流生命周期: 记录 initialize 次数；若省略: 无法断言只重建一次
        tools_list_count = 0  # 新增代码+HTTP流生命周期: 记录 tools/list 次数；若省略: 无法断言第一次 404 后只重试一次
        host = socket.gethostbyname("localhost")  # 新增代码+HTTP流生命周期: 使用 IPv4 回环地址运行 fake server；若省略: 本地连接地址可能不稳定

        class RebuildHandler(http.server.BaseHTTPRequestHandler):  # 新增代码+HTTP流生命周期: 定义第一次 session 404、第二次成功的 fake server；若省略: 404 recovery 没有可验证对象
            def log_message(self, format: str, *args: object) -> None:  # 新增代码+HTTP流生命周期: 屏蔽访问日志；若省略: unittest 输出会混入 HTTP 日志
                return None  # 新增代码+HTTP流生命周期: 明确静默日志；若省略: 父类会写 stderr

            def do_POST(self) -> None:  # 新增代码+HTTP流生命周期: 处理 initialize、notification 和 tools/list；若省略: 404 recovery 无法端到端触发
                nonlocal initialize_count, tools_list_count  # 新增代码+HTTP流生命周期: 允许 handler 更新外层计数器；若省略: 测试无法观察请求次数
                length = int(self.headers.get("Content-Length", "0"))  # 新增代码+HTTP流生命周期: 读取请求长度；若省略: fake server 无法完整读取 body
                body = self.rfile.read(length).decode("utf-8")  # 新增代码+HTTP流生命周期: 解码 JSON-RPC body；若省略: 后续无法解析消息
                message = json.loads(body) if body else {}  # 新增代码+HTTP流生命周期: 解析 JSON-RPC 消息；若省略: 无法根据 method 分支
                method = str(message.get("method", ""))  # 新增代码+HTTP流生命周期: 提取方法名；若省略: initialize 和 tools/list 无法区分
                if "id" not in message:  # 新增代码+HTTP流生命周期: 识别 initialized notification；若省略: notification 会干扰计数和响应
                    self.send_response(202)  # 新增代码+HTTP流生命周期: 接受 notification；若省略: client.start 可能失败
                    self.end_headers()  # 新增代码+HTTP流生命周期: 结束 notification 响应；若省略: 客户端可能等待
                    return  # 新增代码+HTTP流生命周期: notification 不继续处理；若省略: 后续会误判方法
                request_id = message.get("id")  # 新增代码+HTTP流生命周期: 保存请求 id；若省略: 响应无法匹配
                if method == "initialize":  # 新增代码+HTTP流生命周期: 初始化分支；若省略: 无法下发 old-session 和 new-session
                    initialize_count += 1  # 新增代码+HTTP流生命周期: 统计初始化次数；若省略: 无法断言只重建一次
                    session_id = "old-session" if initialize_count == 1 else "new-session"  # 新增代码+HTTP流生命周期: 第一次给旧会话，第二次给新会话；若省略: 无法模拟 session rebuild
                    self._send_json({"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": "2025-11-25", "capabilities": {"tools": {}}}}, session_id=session_id)  # 新增代码+HTTP流生命周期: 返回初始化成功和对应 session；若省略: client 没有会话可重试
                    return  # 新增代码+HTTP流生命周期: 初始化响应完成；若省略: 会继续进入后续分支
                if method == "tools/list":  # 新增代码+HTTP流生命周期: 工具列表分支；若省略: 404 recovery 不会被触发
                    tools_list_count += 1  # 新增代码+HTTP流生命周期: 统计 tools/list 次数；若省略: 无法断言重试次数
                    current_session = self.headers.get("Mcp-Session-Id", "")  # 新增代码+HTTP流生命周期: 读取客户端当前 session；若省略: fake server 无法区分旧会话和新会话
                    if current_session == "old-session":  # 新增代码+HTTP流生命周期: 旧 session 第一次业务请求失效；若省略: 不会触发 404 recovery
                        self._send_status(404, "old session missing")  # 新增代码+HTTP流生命周期: 返回 404 表示会话不存在；若省略: 客户端不会重建 session
                        return  # 新增代码+HTTP流生命周期: 404 已响应；若省略: 还会继续发送成功响应
                    self._send_json({"jsonrpc": "2.0", "id": request_id, "result": {"tools": [{"name": "echo", "description": "Echo after rebuild", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}}]}})  # 新增代码+HTTP流生命周期: 新 session 下返回 echo 工具；若省略: recovery 成功后没有可见工具可断言
                    return  # 新增代码+HTTP流生命周期: tools/list 成功响应完成；若省略: 会继续发送未知方法错误
                self._send_json({"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown"}})  # 新增代码+HTTP流生命周期: 未知方法返回错误；若省略: 意外请求可能挂起

            def _send_json(self, payload: dict[str, object], session_id: str = "") -> None:  # 新增代码+HTTP流生命周期: 统一发送 JSON 响应；若省略: 初始化和成功 tools/list 会重复逻辑
                response_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # 新增代码+HTTP流生命周期: 编码 JSON body；若省略: 客户端无法解析响应
                self.send_response(200)  # 新增代码+HTTP流生命周期: 返回成功状态；若省略: urllib 会抛异常
                self.send_header("Content-Type", "application/json")  # 新增代码+HTTP流生命周期: 标明 JSON 类型；若省略: 客户端可能误判格式
                if session_id:  # 新增代码+HTTP流生命周期: 初始化响应下发 session；若省略: client 不会切换 old/new session
                    self.send_header("Mcp-Session-Id", session_id)  # 新增代码+HTTP流生命周期: 写入 session header；若省略: 后续请求没有会话状态
                self.send_header("Content-Length", str(len(response_body)))  # 新增代码+HTTP流生命周期: 写明响应长度；若省略: 客户端读取可能不稳定
                self.end_headers()  # 新增代码+HTTP流生命周期: 结束响应头；若省略: body 不会发送
                self.wfile.write(response_body)  # 新增代码+HTTP流生命周期: 写出响应 body；若省略: 客户端收到空响应

            def _send_status(self, status: int, message: str) -> None:  # 新增代码+HTTP流生命周期: 统一发送非 200 状态；若省略: 404 场景会重复底层 HTTP 代码
                response_body = message.encode("utf-8")  # 新增代码+HTTP流生命周期: 编码错误正文；若省略: HTTP 错误没有可读内容
                self.send_response(status)  # 新增代码+HTTP流生命周期: 返回指定 HTTP 状态码；若省略: 无法模拟 404
                self.send_header("Content-Type", "text/plain; charset=utf-8")  # 新增代码+HTTP流生命周期: 标明错误正文编码；若省略: 错误文本可能乱码
                self.send_header("Content-Length", str(len(response_body)))  # 新增代码+HTTP流生命周期: 写明错误正文长度；若省略: 客户端读取错误体不稳定
                self.end_headers()  # 新增代码+HTTP流生命周期: 结束错误响应头；若省略: body 不会发送
                self.wfile.write(response_body)  # 新增代码+HTTP流生命周期: 写出错误正文；若省略: 客户端无法展示 404 原因

        httpd = http.server.ThreadingHTTPServer((host, 0), RebuildHandler)  # 新增代码+HTTP流生命周期: 启动 session rebuild fake server；若省略: 404 recovery 没有本地目标
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)  # 新增代码+HTTP流生命周期: 后台运行 fake server；若省略: 测试会阻塞
        thread.start()  # 新增代码+HTTP流生命周期: 开始监听端口；若省略: registry.start 连接失败
        registry = McpToolRegistry.from_configs([McpServerConfig(name="remote", command="", transport="http", url=f"http://{host}:{httpd.server_port}/mcp")])  # 新增代码+HTTP流生命周期: 创建指向 rebuild server 的 registry；若省略: 无法测试真实 HTTP client 行为
        try:  # 新增代码+HTTP流生命周期: 确保红灯失败也清理 server；若省略: 失败后端口和线程可能残留
            registry.start()  # 新增代码+HTTP流生命周期: 触发 old-session、404、new-session 和重试 tools/list；若省略: recovery 行为不会发生
            tool_names = [schema["function"]["name"] for schema in registry.tool_schemas()]  # 新增代码+HTTP流生命周期: 收集最终可见工具名；若省略: 无法确认 recovery 后 echo 被注册
            self.assertIn("mcp__remote__echo", tool_names)  # 新增代码+HTTP流生命周期: 断言新 session 的 echo 工具可见；若省略: 只看计数无法证明功能恢复
            self.assertEqual(initialize_count, 2)  # 新增代码+HTTP流生命周期: 断言只初始化两次；若省略: 实现可能无限或重复重建 session
            self.assertEqual(tools_list_count, 2)  # 新增代码+HTTP流生命周期: 断言 tools/list 只请求两次；若省略: 实现可能重复重试污染 server
        finally:  # 新增代码+HTTP流生命周期: 清理 rebuild fake server；若省略: 失败时会泄漏本地资源
            registry.close()  # 新增代码+HTTP流生命周期: 关闭 registry；若省略: 后续实现可能残留 HTTP 状态
            httpd.shutdown()  # 新增代码+HTTP流生命周期: 停止 fake server；若省略: 后台线程继续监听
            httpd.server_close()  # 新增代码+HTTP流生命周期: 释放端口；若省略: Windows 上端口句柄可能残留
            thread.join(timeout=2)  # 新增代码+HTTP流生命周期: 等待 server 线程退出；若省略: 测试进程状态不确定
    def test_mcp_sse_transport_fails_with_clear_boundary(self) -> None:  # 修改代码+MCP启动隔离: 验证旧 HTTP+SSE transport 失败会被记录且不抛出拖垮其他 server；若省略: 单 server 容错可能回归
        config = McpServerConfig(name="legacy", command="", transport="sse", url="http://127.0.0.1:9/sse")  # 新增代码+MCPTransport: 构造旧 SSE 配置；若省略: 无法触发 SSE client 路径
        registry = McpToolRegistry.from_configs([config])  # 新增代码+MCPTransport: 从 SSE 配置创建 registry；若省略: client 工厂路径没有覆盖
        registry.start()  # 修改代码+MCP启动隔离: 启动 registry 并让 SSE 单 server 失败被记录；若省略: 边界错误不会实际产生
        self.assertFalse(registry.has_available_servers())  # 新增代码+MCP启动隔离: 断言只有失败 SSE server 时没有可用 MCP server；若省略: 全部失败可能被误判为可用
        self.assertRegex(registry.start_errors()["legacy"], "SSE|HTTP\\+SSE|transport=http")  # 新增代码+MCP启动隔离: 断言失败记录仍包含清楚 SSE 边界；若省略: 用户可能看到模糊启动失败
    def test_mcp_http_401_exposes_authenticate_tool_with_metadata_hint(self) -> None:  # 新增代码+MCPAuthMetadata: 验证 HTTP MCP 401 会变成可见 authenticate 入口；若省略: 需要登录的远程 MCP 会直接启动失败且模型无恢复路径
        requests: list[str] = []  # 新增代码+MCPAuthMetadata: 保存 fake server 收到的方法名；若省略: 测试无法确认客户端确实尝试 initialize

        class Handler(http.server.BaseHTTPRequestHandler):  # 新增代码+MCPAuthMetadata: 定义测试专用受保护 MCP HTTP server；若省略: 鉴权 401 场景只能依赖外部服务且不稳定
            def log_message(self, format: str, *args: object) -> None:  # 新增代码+MCPAuthMetadata: 屏蔽测试 HTTP 日志；若省略: unittest 输出会被访问日志污染
                return None  # 新增代码+MCPAuthMetadata: 明确不输出日志；若省略: BaseHTTPRequestHandler 会写 stderr

            def do_POST(self) -> None:  # 新增代码+MCPAuthMetadata: 处理 MCP Streamable HTTP POST；若省略: client 无法收到 401 鉴权挑战
                length = int(self.headers.get("Content-Length", "0"))  # 新增代码+MCPAuthMetadata: 读取请求体长度；若省略: fake server 无法解析 JSON-RPC 方法
                body = self.rfile.read(length).decode("utf-8")  # 新增代码+MCPAuthMetadata: 读取并解码请求体；若省略: 方法名无法记录
                message = json.loads(body) if body else {}  # 新增代码+MCPAuthMetadata: 把请求体转成对象；若省略: 后续 get 方法会失败
                requests.append(str(message.get("method", "")))  # 新增代码+MCPAuthMetadata: 保存 JSON-RPC 方法名；若省略: 测试无法断言 initialize 已发出
                metadata_url = f"http://127.0.0.1:{self.server.server_port}/.well-known/oauth-protected-resource"  # 新增代码+MCPAuthMetadata: 构造受保护资源 metadata URL；若省略: WWW-Authenticate 缺少客户端可展示的发现入口
                response_body = b"auth required"  # 新增代码+MCPAuthMetadata: 准备 401 错误正文；若省略: 错误提示缺少 body 覆盖
                self.send_response(401)  # 新增代码+MCPAuthMetadata: 返回 Unauthorized 触发 auth metadata 路径；若省略: client 不会进入鉴权处理
                self.send_header("WWW-Authenticate", f'Bearer resource_metadata="{metadata_url}", error="invalid_token"')  # 新增代码+MCPAuthMetadata: 按 MCP 授权规范返回 resource_metadata；若省略: 客户端无法发现授权服务器入口
                self.send_header("Content-Type", "text/plain")  # 新增代码+MCPAuthMetadata: 声明错误正文类型；若省略: 响应仍可用但测试不够贴近真实服务
                self.send_header("Content-Length", str(len(response_body)))  # 新增代码+MCPAuthMetadata: 写明正文长度；若省略: Windows 上读取 body 可能不稳定
                self.end_headers()  # 新增代码+MCPAuthMetadata: 结束响应头；若省略: 客户端收不到完整 401 响应
                self.wfile.write(response_body)  # 新增代码+MCPAuthMetadata: 写出错误正文；若省略: auth challenge 的 body 提示无法被覆盖

        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)  # 新增代码+MCPAuthMetadata: 在随机本地端口启动受保护 fake server；若省略: 测试会占用固定端口或依赖外网
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)  # 新增代码+MCPAuthMetadata: 创建后台线程运行 HTTP server；若省略: 当前测试会阻塞
        thread.start()  # 新增代码+MCPAuthMetadata: 启动 fake server；若省略: registry.start 会连接失败而不是收到 401
        registry = McpToolRegistry.from_configs([McpServerConfig(name="locked", command="", transport="http", url=f"http://127.0.0.1:{httpd.server_port}/mcp")])  # 新增代码+MCPAuthMetadata: 创建指向受保护 endpoint 的 registry；若省略: 鉴权挑战没有运行入口
        try:  # 新增代码+MCPAuthMetadata: 确保测试结束能清理 registry 和 HTTP server；若省略: 测试失败时可能残留端口
            registry.start()  # 新增代码+MCPAuthMetadata: 启动 registry 并期望 401 被转成 authenticate 工具；若省略: 红灯测试无法覆盖 registry 恢复路径
            tool_names = [schema["function"]["name"] for schema in registry.tool_schemas()]  # 新增代码+MCPAuthMetadata: 收集模型可见工具名；若省略: 无法断言 authenticate 工具是否暴露
            self.assertEqual(tool_names, ["mcp__locked__authenticate"])  # 新增代码+MCPAuthMetadata: 断言只暴露鉴权说明工具；若省略: 需要登录的 server 可能仍误暴露业务工具
            self.assertEqual(requests, ["initialize"])  # 新增代码+MCPAuthMetadata: 断言客户端在初始化阶段收到鉴权挑战；若省略: 测试可能没真正覆盖 401 初始化路径
            auth_text = registry.call_tool("mcp__locked__authenticate", {})  # 新增代码+MCPAuthMetadata: 调用伪 authenticate 工具读取指导文本；若省略: 只能证明工具可见不能证明可解释
            self.assertIn("resource_metadata", auth_text)  # 新增代码+MCPAuthMetadata: 断言输出解释 metadata 来源；若省略: 模型可能不知道下一步该看哪个授权入口
            self.assertIn(".well-known/oauth-protected-resource", auth_text)  # 新增代码+MCPAuthMetadata: 断言输出包含服务端 metadata URL；若省略: 用户无法定位登录发现信息
            self.assertIn("Authorization", auth_text)  # 新增代码+MCPAuthMetadata: 断言输出提示使用 Authorization header；若省略: 用户可能把 token 放进 URL 或其他危险位置
            self.assertIn("Bearer", auth_text)  # 新增代码+MCPAuthMetadata: 断言输出提示 Bearer token 写法；若省略: 用户不知道 header 值格式
            self.assertIn("mcp_servers.json", auth_text)  # 新增代码+MCPAuthMetadata: 断言输出提示配置文件位置；若省略: 初学者不知道该改哪里
            self.assertIn("不会自动", auth_text)  # 新增代码+MCPAuthMetadata: 断言输出说明不会自动追随 metadata URL；若省略: SSRF 边界容易被误解为已自动完成登录
        finally:  # 新增代码+MCPAuthMetadata: 进入资源清理分支；若省略: 测试成功或失败后都可能残留后台线程
            registry.close()  # 新增代码+MCPAuthMetadata: 关闭 registry 内 client；若省略: 后续扩展真实连接时可能泄漏状态
            httpd.shutdown()  # 新增代码+MCPAuthMetadata: 停止 fake HTTP server；若省略: 端口会继续监听
            httpd.server_close()  # 新增代码+MCPAuthMetadata: 释放监听端口；若省略: Windows 上端口句柄可能残留
            thread.join(timeout=2)  # 新增代码+MCPAuthMetadata: 等待后台线程退出；若省略: 测试进程关闭时状态不确定
    def test_mcp_config_invalid_json_returns_empty_server_list(self) -> None:  # 新增代码: 验证坏 JSON 不会让 MCP 配置加载崩溃；若省略: 用户写错配置时 agent 可能直接退出
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 创建临时工作区隔离坏配置文件；若省略: 测试可能污染真实配置
            workspace = Path(raw_dir)  # 新增代码: 把临时目录包装成 Path；若省略: 后续路径拼接和函数调用不方便
            config_file = workspace / "mcp_servers.json"  # 新增代码: 定位 MCP 配置文件路径；若省略: 无法写入坏 JSON 场景
            config_file.write_text("{这不是合法 JSON", encoding="utf-8")  # 新增代码: 写入故意损坏的 JSON；若省略: 无法验证解析失败时的容错行为
            configs = load_mcp_server_configs(workspace)  # 新增代码: 调用配置加载函数观察坏 JSON 行为；若省略: 测试没有实际验证对象
            self.assertEqual(configs, [])  # 新增代码: 坏 JSON 应返回空列表；若省略: 无法保护配置错误时 agent 继续可用
    def test_mcp_doctor_reports_missing_config_and_builtin_tools(self) -> None:  # 新增代码+MCP诊断: 验证没有 mcp_servers.json 时 doctor 会说明外部工具未启用；若省略: 用户仍会困惑为什么模型看不到搜索工具
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP诊断: 创建没有 MCP 配置的临时工作区；若省略: 测试会受真实项目配置影响
            workspace = Path(raw_dir)  # 新增代码+MCP诊断: 把临时目录转成 Path；若省略: 后续传参不够清晰
            report = run_mcp_doctor(workspace)  # 新增代码+MCP诊断: 执行 MCP Doctor；若省略: 无法观察诊断输出
            self.assertIn("MCP Doctor", report)  # 新增代码+MCP诊断: 断言输出有清楚标题；若省略: 用户可能不知道这段文本的用途
            self.assertIn("配置状态：未找到 mcp_servers.json", report)  # 新增代码+MCP诊断: 断言缺配置时给出直接原因；若省略: 工具不可见原因仍然模糊
            self.assertIn("模型可见 MCP 工具：0 个", report)  # 新增代码+MCP诊断: 断言无配置时外部工具数量为零；若省略: 用户无法确认模型是否真的看不到 MCP 工具
            self.assertIn("内置工具", report)  # 新增代码+MCP诊断: 断言 doctor 同时提示内置工具仍可用；若省略: 用户可能误以为 agent 完全没有工具
    def test_mcp_doctor_reports_real_chrome_profile_diagnostic(self) -> None:  # 新增代码+RealChromeDoctor测试: 验证 MCP Doctor 先输出真实 Chrome profile 诊断；若省略: 缺配置场景可能完全看不到真实 Chrome 环境问题
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RealChromeDoctor测试: 创建不含 mcp_servers.json 的临时工作区；若省略: 测试可能读取真实项目配置导致不稳定
            workspace = Path(raw_dir)  # 新增代码+RealChromeDoctor测试: 把临时目录转成 Path 传给 doctor；若省略: 后续路径语义不够清楚
            fake_diagnostic = mock.Mock(status="needs_user_action", chrome_path="C:/Chrome/chrome.exe", user_data_dir="C:/Chrome/User Data", chrome_running=True, port_available=False, messages=["请先关闭 Chrome。"])  # 新增代码+RealChromeDoctor测试: 构造稳定假诊断对象避免依赖真实机器；若省略: 测试会受本机 Chrome 安装和端口状态影响
            with mock.patch("learning_agent.mcp.runtime.diagnose_real_chrome_environment", return_value=fake_diagnostic, create=True):  # 修改代码+ToolSchemaSplit测试: 改为 patch 新 MCP runtime 诊断入口；若没有这行代码，去旧入口后 doctor 测试会继续绑在 compatibility 层
                report = run_mcp_doctor(workspace)  # 新增代码+RealChromeDoctor测试: 执行 doctor 获取报告文本；若省略: 无法验证新增诊断输出
            self.assertIn("真实 Chrome profile 诊断：needs_user_action", report)  # 新增代码+RealChromeDoctor测试: 断言报告包含三态诊断状态；若省略: doctor 可能不展示 available/needs_user_action/blocked
            self.assertIn("真实 Chrome 路径：C:/Chrome/chrome.exe", report)  # 新增代码+RealChromeDoctor测试: 断言报告包含 Chrome 路径字段；若省略: 用户不知道 doctor 检测到哪个浏览器
            self.assertIn("真实 Chrome User Data：C:/Chrome/User Data", report)  # 新增代码+RealChromeDoctor测试: 断言报告包含 User Data 字段；若省略: 用户不知道真实 profile 根目录是否被识别
            self.assertIn("真实 Chrome 正在运行：true", report)  # 新增代码+RealChromeDoctor测试: 断言报告包含 Chrome 运行状态；若省略: 用户不知道是否需要先关闭 Chrome
            self.assertIn("真实 Chrome 默认端口可用：false", report)  # 新增代码+RealChromeDoctor测试: 断言报告包含默认端口状态；若省略: 端口冲突不会被提前看见
            self.assertIn("真实 Chrome 提示：请先关闭 Chrome。", report)  # 新增代码+RealChromeDoctor测试: 断言报告包含可读提示；若省略: 状态原因会变成猜测
            self.assertLess(report.index("真实 Chrome profile 诊断"), report.index("配置状态：未找到 mcp_servers.json"))  # 新增代码+RealChromeDoctor测试: 断言真实 Chrome 诊断早于缺配置状态；若省略: 缺配置分支可能提前 return 导致诊断丢失
    def test_mcp_doctor_script_entrypoint_reports_real_chrome_diagnostic(self) -> None:  # 新增代码+RealChromeDoctor脚本测试: 验证 learning_agent.py mcp-doctor 脚本入口不会因包导入崩溃；若省略: CLI 入口坏掉时单纯包导入测试发现不了
        script_path = (TEST_ROOT / "learning_agent.py")  # 新增代码+RealChromeDoctor脚本测试: 定位同目录下的 learning_agent.py 脚本；若省略: subprocess 无法准确执行被测入口
        completed = subprocess.run([sys.executable, str(script_path), "mcp-doctor"], cwd=str(script_path.parent.parent), text=True, capture_output=True, timeout=15)  # 新增代码+RealChromeDoctor脚本测试: 用当前 Python 启动真实脚本入口并捕获输出；若省略: 无法复现脚本模式导入 fallback 问题
        combined_output = completed.stdout + completed.stderr  # 新增代码+RealChromeDoctor脚本测试: 合并 stdout/stderr 方便失败时检查真实错误；若省略: 导入崩溃可能只在 stderr 中而断言看不到
        self.assertEqual(completed.returncode, 0, combined_output)  # 新增代码+RealChromeDoctor脚本测试: 断言脚本入口正常退出并在失败时展示输出；若省略: ModuleNotFoundError 仍可能悄悄回归
        self.assertIn("MCP Doctor", completed.stdout)  # 新增代码+RealChromeDoctor脚本测试: 断言脚本入口输出 doctor 标题；若省略: 命令可能运行了但没有进入诊断模式
        self.assertIn("真实 Chrome profile 诊断", completed.stdout)  # 新增代码+RealChromeDoctor脚本测试: 断言脚本入口输出真实 Chrome 诊断字段；若省略: 只验证不崩溃但不能保护 Task 7 新能力
        self.assertTrue(any(status in completed.stdout for status in ("available", "needs_user_action", "blocked")))  # 新增代码+RealChromeDoctor脚本测试: 断言输出包含三态之一但不依赖真实机器状态；若省略: 测试会把本机 Chrome 环境固定死
    def test_mcp_doctor_lists_visible_tools_from_configured_server(self) -> None:  # 新增代码+MCP诊断: 验证 doctor 能启动配置的 MCP server 并列出模型可见工具名；若省略: 诊断无法证明 tools/list 链路真的可用
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP诊断: 创建临时工作区隔离配置和 fake server；若省略: 测试会污染真实项目
            workspace = Path(raw_dir)  # 新增代码+MCP诊断: 把临时目录转成 Path；若省略: 后续路径操作不方便
            server_script = workspace / "doctor_mcp_server.py"  # 新增代码+MCP诊断: 定义 fake MCP server 脚本路径；若省略: doctor 没有可启动的测试 server
            server_script.write_text(  # 新增代码+MCP诊断: 写入最小 MCP server 源码；若省略: 配置指向的 server 文件不存在
                """import json  # 新增代码+MCP诊断: 导入 JSON 处理 JSON-RPC；若省略: fake server 无法解析请求
import sys  # 新增代码+MCP诊断: 导入 sys 读写标准输入输出；若省略: fake server 无法和 McpStdioClient 通信

TOOLS = [  # 新增代码+MCP诊断: 定义 fake server 暴露的工具列表；若省略: doctor 无法列出任何工具
    {  # 新增代码+MCP诊断: 定义 hello 工具对象；若省略: 模型可见工具名没有测试目标
        "name": "hello",  # 新增代码+MCP诊断: 原始 MCP 工具名；若省略: 注册表无法生成 mcp__doctor__hello
        "description": "Doctor hello tool",  # 新增代码+MCP诊断: 工具说明；若省略: schema 缺少可读描述
        "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}},  # 新增代码+MCP诊断: 工具参数 schema；若省略: 模型不知道参数结构
    }  # 新增代码+MCP诊断: hello 工具对象结束；若省略: Python 语法不完整
]  # 新增代码+MCP诊断: 工具列表结束；若省略: fake server 没有 TOOLS

for raw_line in sys.stdin:  # 新增代码+MCP诊断: 循环读取客户端发来的 JSON-RPC 消息；若省略: fake server 不会响应请求
    message = json.loads(raw_line)  # 新增代码+MCP诊断: 解析一行请求 JSON；若省略: fake server 无法判断方法
    method = message.get("method")  # 新增代码+MCP诊断: 读取 JSON-RPC 方法名；若省略: 无法区分 initialize/tools/list
    if method == "notifications/initialized":  # 新增代码+MCP诊断: 忽略 initialized 通知；若省略: notification 可能产生多余响应
        continue  # 新增代码+MCP诊断: notification 不需要响应；若省略: 客户端可能收到无关消息
    request_id = message.get("id")  # 新增代码+MCP诊断: 读取请求 id 用于响应匹配；若省略: 客户端无法确认响应属于哪个请求
    if method == "initialize":  # 新增代码+MCP诊断: 处理 MCP 初始化请求；若省略: client.start 会失败
        response = {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {}}}  # 新增代码+MCP诊断: 返回最小初始化成功结果；若省略: doctor 到不了 tools/list
    elif method == "tools/list":  # 新增代码+MCP诊断: 处理工具列表请求；若省略: doctor 无法发现 hello 工具
        response = {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}  # 新增代码+MCP诊断: 返回 fake 工具列表；若省略: 模型可见工具列表为空
    else:  # 新增代码+MCP诊断: 处理其他未知方法；若省略: fake server 行为不完整
        response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown method"}}  # 新增代码+MCP诊断: 返回标准未知方法错误；若省略: 客户端可能一直等待
    sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\\n")  # 新增代码+MCP诊断: 输出一行 JSON-RPC 响应；若省略: client 读不到结果
    sys.stdout.flush()  # 新增代码+MCP诊断: 立即刷新 stdout；若省略: 响应可能停留在缓冲区
""",  # 新增代码+MCP诊断: fake server 源码字符串结束；若省略: 测试语法不完整
                encoding="utf-8",  # 新增代码+MCP诊断: 用 UTF-8 写入脚本；若省略: Windows 中文环境可能编码不一致
            )  # 新增代码+MCP诊断: fake server 文件写入完成；若省略: 后续配置无法启动 server
            (workspace / "mcp_servers.json").write_text(  # 新增代码+MCP诊断: 写入 doctor 使用的 MCP 配置文件；若省略: run_mcp_doctor 会走缺配置分支
                json.dumps({"servers": [{"name": "doctor", "command": sys.executable, "args": [str(server_script)]}]}, ensure_ascii=False),  # 新增代码+MCP诊断: 配置 fake server 命令和参数；若省略: doctor 不知道如何启动 server
                encoding="utf-8",  # 新增代码+MCP诊断: 用 UTF-8 写配置；若省略: 配置读取可能受系统编码影响
            )  # 新增代码+MCP诊断: MCP 配置写入完成；若省略: Python 语法不完整
            report = run_mcp_doctor(workspace)  # 新增代码+MCP诊断: 执行 doctor 并启动 fake MCP server；若省略: 无法观察诊断结果
            self.assertIn("配置状态：已找到 mcp_servers.json", report)  # 新增代码+MCP诊断: 断言配置文件被发现；若省略: doctor 可能误报缺配置
            self.assertIn("启动成功：doctor", report)  # 新增代码+MCP诊断: 断言 server 启动成功；若省略: 启动失败也可能被误认为正常
            self.assertIn("模型可见 MCP 工具：1 个", report)  # 新增代码+MCP诊断: 断言工具数量正确；若省略: 工具列表为空也不会被发现
            self.assertIn("mcp__doctor__hello", report)  # 新增代码+MCP诊断: 断言最终模型可见工具名正确；若省略: 前缀命名或 tools/list 回归不会被发现
    def test_mcp_doctor_reports_partial_start_failure_without_marking_bad_server_success(self) -> None:  # 新增代码+MCP诊断部分失败: 验证 doctor 不会把已记录失败的 server 误报为成功；若省略: Task 6 的部分启动失败语义会在诊断命令里回归
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP诊断部分失败: 创建临时工作区隔离 mcp_servers.json；若省略: 测试会污染真实项目配置
            workspace = Path(raw_dir)  # 新增代码+MCP诊断部分失败: 把临时目录转成 Path 方便写配置；若省略: 后续路径拼接不清晰
            good_server_script = (TEST_ROOT / "browser_search_mcp_server.py")  # 新增代码+MCP诊断部分失败: 使用已有可列工具的 stdio MCP server 作为成功样本；若省略: 测试需要重复写 fake server
            (workspace / "mcp_servers.json").write_text(  # 新增代码+MCP诊断部分失败: 写入一个成功 server 和一个失败 server 的配置；若省略: doctor 没有部分失败场景可检查
                json.dumps({"servers": [{"name": "good_server", "command": sys.executable, "args": [str(good_server_script)]}, {"name": "bad_server", "command": sys.executable, "args": ["-c", "import sys; sys.exit(3)"]}]}, ensure_ascii=False),  # 新增代码+MCP诊断部分失败: 配置 good_server 可启动、bad_server 立即退出；若省略: 无法稳定复现单 server 失败不拖垮其他 server
                encoding="utf-8",  # 新增代码+MCP诊断部分失败: 使用 UTF-8 写配置；若省略: Windows 默认编码可能影响 JSON 读取
            )  # 新增代码+MCP诊断部分失败: 完成配置写入；若省略: Python 语法不完整
            report = run_mcp_doctor(workspace)  # 新增代码+MCP诊断部分失败: 执行 doctor 观察部分失败报告；若省略: 无法验证诊断输出
            self.assertIn("启动成功：good_server", report)  # 新增代码+MCP诊断部分失败: 断言成功 server 仍被报告为成功；若省略: 可能修坏正常 server 展示
            self.assertIn("启动失败：bad_server", report)  # 新增代码+MCP诊断部分失败: 断言失败 server 被明确报告失败；若省略: 用户会误以为 bad server 正常
            self.assertNotIn("启动成功：bad_server", report)  # 新增代码+MCP诊断部分失败: 断言 bad server 不会被误报成功；若省略: 本次质量审查问题会再次出现
            self.assertIn("模型可见 MCP 工具：", report)  # 新增代码+MCP诊断部分失败: 断言工具数量仍来自 registry.tool_schemas；若省略: doctor 可能只报告启动状态不报告可见工具
            self.assertIn("mcp__good_server__web_search", report)  # 新增代码+MCP诊断部分失败: 断言成功 server 的工具仍可见；若省略: 部分失败可能隐藏可用工具
    def test_mcp_registry_can_be_created_from_workspace_config(self) -> None:  # 新增代码: 验证工作区配置能创建 MCP 注册表；若省略: CLI 加载路径没有测试保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 创建临时工作区；若省略: 会污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码: 包装路径；若省略: 无法写配置文件
            (workspace / "mcp_servers.json").write_text(  # 新增代码: 写入一个空参数的 demo 配置；若省略: 注册表没有配置来源
                json.dumps({"servers": [{"name": "demo", "command": sys.executable, "args": []}]}, ensure_ascii=False),  # 新增代码: 使用当前 Python 作为命令；若省略: 测试跨机器不稳定
                encoding="utf-8",  # 新增代码: 明确 UTF-8；若省略: Windows 编码可能不同
            )
            configs = load_mcp_server_configs(workspace)  # 新增代码: 加载配置；若省略: 无法创建注册表
            registry = McpToolRegistry.from_configs(configs)  # 新增代码: 从配置创建注册表；若省略: CLI 无法把配置接入运行时
            self.assertTrue(registry.has_servers())  # 新增代码: 验证注册表知道有 server；若省略: 配置可能被忽略
            self.assertEqual(registry.server_names(), ["demo"])  # 新增代码: 验证 server 名被保留；若省略: 权限提示可能错误
    def test_mcp_config_skips_invalid_server_entries(self) -> None:  # 新增代码: 验证无效 server 项会被跳过且有效项保留；若省略: 单个坏配置可能破坏全部 MCP 配置
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 创建临时工作区避免影响真实项目；若省略: 测试会读写真正配置文件
            workspace = Path(raw_dir)  # 新增代码: 把临时目录转成 Path；若省略: 无法方便定位配置文件
            config_file = workspace / "mcp_servers.json"  # 新增代码: 定义 MCP 配置文件路径；若省略: 无法模拟配置文件内容
            config_file.write_text(json.dumps({"servers": 123}, ensure_ascii=False), encoding="utf-8")  # 新增代码: 写入 servers 非 list 的配置；若省略: 无法覆盖顶层 servers 类型错误
            self.assertEqual(load_mcp_server_configs(workspace), [])  # 新增代码: servers 非 list 时应返回空列表；若省略: 该边界仍可能崩溃
            config_file.write_text(  # 新增代码: 覆盖写入包含多种无效项和有效项的配置；若省略: 无法验证逐项跳过策略
                json.dumps(  # 新增代码: 把 Python 测试数据序列化为 JSON；若省略: 配置文件无法按真实格式写入
                    {  # 新增代码: 顶层对象模拟真实 mcp_servers.json；若省略: 加载函数拿不到 servers 字段
                        "servers": [  # 新增代码: servers 数组包含有效和无效配置；若省略: 无法验证列表逐项处理
                            "bad-entry",  # 新增代码: 非 dict 项应被跳过；若省略: 无法覆盖 server 项类型错误
                            {"name": "", "command": sys.executable},  # 新增代码: 缺 name 的项应被跳过；若省略: 空名称可能进入结果
                            {"name": "missing-command"},  # 新增代码: 缺 command 的项应被跳过；若省略: 空命令可能进入结果
                            {"name": "bad-args", "command": sys.executable, "args": "not-list"},  # 新增代码: args 非 list 时应转为空列表；若省略: 参数类型不稳定可能外泄
                            {"name": "good", "command": sys.executable, "args": ["server.py", 5]},  # 新增代码: 有效项应保留且参数转成字符串；若省略: 无法证明好配置不会被坏配置拖累
                        ],  # 新增代码: 结束 servers 数组；若省略: JSON 测试数据结构不完整
                    },  # 新增代码: 结束顶层配置对象；若省略: JSON 测试数据结构不完整
                    ensure_ascii=False,  # 新增代码: 保持中文不转义便于调试；若省略: 不影响逻辑但降低可读性
                ),  # 新增代码: 结束 JSON 序列化调用；若省略: write_text 没有可写字符串
                encoding="utf-8",  # 新增代码: 明确 UTF-8 写入；若省略: Windows 中文环境可能出现编码差异
            )
            configs = load_mcp_server_configs(workspace)  # 新增代码: 读取混合配置结果；若省略: 无法验证跳过和保留行为
            self.assertEqual(  # 新增代码: 断言只有有效配置进入结果；若省略: 无法发现无效项泄漏或有效项丢失
                configs,  # 新增代码: 实际解析结果；若省略: 断言没有被测对象
                [McpServerConfig(name="bad-args", command=sys.executable, args=[]), McpServerConfig(name="good", command=sys.executable, args=["server.py", "5"])],  # 新增代码: 期望保留有效项并规范化 args；若省略: 无法保护字段解析规则
            )
    def test_agent_calls_mcp_tool_and_returns_final_answer(self) -> None:  # 新增代码+MCP接入LearningAgent: 验证模型选择 MCP 工具时 agent 会调用 registry 并继续返回最终答案；若省略: MCP 工具执行链路没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP接入LearningAgent: 创建临时工作区隔离运行副作用；若省略: 测试可能写入真实 learning_agent 目录
            workspace = Path(raw_dir)  # 新增代码+MCP接入LearningAgent: 把临时目录包装成 Path；若省略: LearningAgent 构造参数不够清晰
            fake_client = FakeMcpClient()  # 新增代码+MCP接入LearningAgent: 创建可记录调用历史的 fake MCP client；若省略: 无法断言 registry 是否真正调用外部工具
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+MCP接入LearningAgent: 构造包含 echo 工具的 MCP 注册表；若省略: agent 没有 MCP 工具可执行
            model = ToolCallingFakeModel([ModelMessage(text="", tool_calls=[ToolCall(name="tool_search", arguments={"query": "select:mcp__demo__echo"})]), ModelMessage(text="", tool_calls=[ToolCall(name="mcp__demo__echo", arguments={"text": "来自 MCP"})]), ModelMessage(text="最终答案包含 MCP 结果。")])  # 修改代码+ToolArchitectureV2: 第一轮先 select 加载 MCP 工具，第二轮再调用 MCP 工具，第三轮返回最终答案；若没有这行代码，测试会继续使用已被 v2 禁止的直接调用路径
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+MCP接入LearningAgent: 创建允许 MCP 启动和调用权限的 agent；若省略: 工具调用会被权限层阻断或 registry 不会启动
            answer = agent.run("请调用 MCP echo")  # 新增代码+MCP接入LearningAgent: 触发模型工具调用和后续最终回答；若省略: 被测执行链路不会发生
            self.assertEqual(fake_client.calls, [("echo", {"text": "来自 MCP"})])  # 新增代码+MCP接入LearningAgent: 确认 registry 剥离前缀后调用原始 echo 工具；若省略: 可能把 mcp__demo__echo 错传给 server 而不被发现
            self.assertIn("最终答案包含 MCP 结果", answer)  # 新增代码+MCP接入LearningAgent: 确认 MCP 工具结果回到模型后 agent 返回最终答案；若省略: 只能验证调用而不能验证闭环
    def test_agent_does_not_call_mcp_tool_when_permission_is_denied(self) -> None:  # 新增代码+MCP接入LearningAgent: 验证用户拒绝 MCP 工具调用时 agent 不会调用 registry；若省略: 权限边界回归不会被发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP接入LearningAgent: 创建临时工作区隔离 memory 和日志；若省略: 测试可能影响真实文件
            workspace = Path(raw_dir)  # 新增代码+MCP接入LearningAgent: 把临时目录转成 Path；若省略: 后续构造 agent 不够直接
            fake_client = FakeMcpClient()  # 新增代码+MCP接入LearningAgent: 创建 fake MCP client 用来观察是否被调用；若省略: 无法证明拒绝后没有外部调用
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+MCP接入LearningAgent: 构造 MCP 注册表供 agent 初始化；若省略: 测试不会覆盖 MCP 工具名分发
            permission_requests: list[str] = []  # 新增代码+MCP接入LearningAgent: 记录每次权限请求文本；若省略: 无法区分启动权限和工具调用权限
            def ask_permission(action: str) -> bool:  # 新增代码+MCP接入LearningAgent: 定义可控权限回调；若省略: 无法精确允许启动但拒绝工具调用
                permission_requests.append(action)  # 新增代码+MCP接入LearningAgent: 保存权限说明供断言包含工具名和参数；若省略: 权限提示内容无法被验证
                return action.startswith("启动 MCP server")  # 新增代码+MCP接入LearningAgent: 只允许初始化启动 MCP server；若省略: 工具调用会被允许导致拒绝场景失效
            model = ToolCallingFakeModel([ModelMessage(text="", tool_calls=[ToolCall(name="tool_search", arguments={"query": "select:mcp__demo__echo"})]), ModelMessage(text="", tool_calls=[ToolCall(name="mcp__demo__echo", arguments={"text": "禁止调用"})]), ModelMessage(text="我看到用户拒绝了操作。")])  # 修改代码+ToolArchitectureV2: 先加载 MCP 工具再测试用户拒绝真实工具调用；若没有这行代码，拒绝测试会停在未加载 deferred 门禁而不是权限层
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=ask_permission, mcp_tool_registry=registry)  # 新增代码+MCP接入LearningAgent: 注入 registry 和权限回调创建 agent；若省略: 无法覆盖 Task 5 的拒绝分支
            answer = agent.run("请调用 MCP echo 但用户会拒绝")  # 新增代码+MCP接入LearningAgent: 触发 MCP 工具调用请求；若省略: 权限拒绝逻辑不会运行
            self.assertEqual(fake_client.calls, [])  # 新增代码+MCP接入LearningAgent: 断言用户拒绝后没有调用 fake MCP client；若省略: 外部副作用可能偷偷发生
            self.assertIn("调用 MCP 工具：mcp__demo__echo", permission_requests[-1])  # 新增代码+MCP接入LearningAgent: 断言工具调用权限说明包含 MCP 工具名；若省略: 用户可能不知道正在授权哪个工具
            self.assertIn('"text": "禁止调用"', permission_requests[-1])  # 新增代码+MCP接入LearningAgent: 断言权限说明包含 JSON 参数；若省略: 用户无法基于参数判断是否允许
            self.assertIn("拒绝", answer)  # 新增代码+MCP接入LearningAgent: 确认最终答案体现拒绝状态；若省略: agent 可能吞掉拒绝结果
    def test_mcp_permission_prompt_marks_network_tool_risk(self) -> None:  # 新增代码+权限分级: 验证联网 MCP 工具授权提示会标明外部网络访问风险；若省略: agent 可能仍用模糊提示让用户看不出这是联网操作
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+权限分级: 创建临时工作区隔离 memory 和日志；若省略: 测试可能污染真实 learning_agent 目录
            workspace = Path(raw_dir)  # 新增代码+权限分级: 把临时目录包装成 Path 传给 agent；若省略: 后续构造 LearningAgent 不够清晰
            search_tools = [{"name": "web_search", "description": "联网搜索", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}]  # 新增代码+权限分级: 构造 browser_search 的搜索工具 schema；若省略: fake MCP server 没有联网类工具可供风险分类
            fake_client = FakeMcpClient(tools=search_tools)  # 新增代码+权限分级: 创建只暴露 web_search 的 fake MCP client；若省略: 测试无法覆盖搜索工具风险提示
            registry = McpToolRegistry({"browser_search": fake_client})  # 新增代码+权限分级: 用 browser_search server 名生成真实前缀工具名；若省略: 分类逻辑可能无法识别真实搜索工具名
            permission_requests: list[str] = []  # 新增代码+权限分级: 记录启动和工具调用两次权限文本；若省略: 无法断言用户实际看到的风险提示
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: permission_requests.append(action) or True, mcp_tool_registry=registry)  # 新增代码+权限分级: 创建始终允许的 agent 以捕获权限提示；若省略: MCP 工具不会进入可执行状态
            self._select_tool_for_test(agent, "mcp__browser_search__web_search")  # 新增代码+ToolArchitectureV2: 先把 deferred 搜索工具加载进当前 Tool Pool；若没有这行代码，直接调用会被 v2 门禁拒绝而不会进入风险提示
            output = agent._execute_tool(ToolCall(name="mcp__browser_search__web_search", arguments={"query": "胡志明 天气"}))  # 新增代码+权限分级: 直接执行搜索 MCP 工具触发授权提示；若省略: 风险分级提示不会产生
            self.assertIn("风险等级：外部网络访问", permission_requests[-1])  # 新增代码+权限分级: 断言授权提示明确标出联网风险；若省略: 回归后用户仍可能不知道工具会访问网络
            self.assertIn("风险说明：", permission_requests[-1])  # 新增代码+权限分级: 断言授权提示提供解释而不只是标签；若省略: 初学者很难理解风险等级含义
            self.assertIn('"query": "胡志明 天气"', permission_requests[-1])  # 新增代码+权限分级: 断言提示仍保留具体查询参数；若省略: 用户无法判断本次联网搜索内容
            self.assertIn("called web_search", output)  # 新增代码+权限分级: 断言授权后工具仍正常转发执行；若省略: 风险提示改造可能悄悄破坏 MCP 调用链路
    def test_mcp_permission_prompt_prunes_browser_open_arguments_before_user_confirmation(self) -> None:  # 新增代码+MCP参数清洗: 验证用户授权前看到的 browser_open 参数已经去掉无关字段；若省略: 截图里的 status/action/confirm_real_profile 会继续误导用户
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP参数清洗: 创建临时工作区隔离 agent 运行副作用；若省略: 测试可能污染真实记忆或日志
            workspace = Path(raw_dir)  # 新增代码+MCP参数清洗: 把临时目录转成 Path；若省略: LearningAgent 构造参数不够清楚
            browser_tools = [  # 新增代码+MCP参数清洗: 构造真实 browser_open 风格工具列表；若省略: agent 没有浏览器 MCP 工具可执行
                {  # 新增代码+MCP参数清洗: 定义单个 browser_open 工具；若省略: registry 无法生成 mcp__browser_automation__browser_open
                    "name": "browser_open",  # 新增代码+MCP参数清洗: 使用真实工具名；若省略: 风险分类和前缀名不贴近截图
                    "description": "Open browser page",  # 新增代码+MCP参数清洗: 提供工具说明；若省略: schema 结构不完整
                    "inputSchema": {  # 新增代码+MCP参数清洗: 声明 browser_open 合法参数；若省略: agent 无法据此清洗模型输出
                        "type": "object",  # 新增代码+MCP参数清洗: 声明参数是对象；若省略: 参数清洗没有对象边界
                        "properties": {  # 新增代码+MCP参数清洗: 列出用户应该看到并授权的字段；若省略: 清洗逻辑无法区分合法和串味参数
                            "url": {"type": "string"},  # 新增代码+MCP参数清洗: 声明打开地址；若省略: 授权提示可能丢掉最重要的 URL
                            "new_tab": {"type": "boolean"},  # 新增代码+MCP参数清洗: 声明是否开新标签；若省略: 合法参数可能被误删
                            "timeout_ms": {"type": "integer"},  # 新增代码+MCP参数清洗: 声明页面等待超时；若省略: 合法超时边界可能被误删
                        },  # 新增代码+MCP参数清洗: properties 结束；若省略: schema 字典无法闭合
                        "required": ["url"],  # 新增代码+MCP参数清洗: 标出 url 必填；若省略: 工具 schema 不贴近真实 browser_open
                    },  # 新增代码+MCP参数清洗: inputSchema 结束；若省略: 工具定义不完整
                }  # 新增代码+MCP参数清洗: browser_open 工具结束；若省略: 列表项语法不完整
            ]  # 新增代码+MCP参数清洗: 工具列表结束；若省略: fake client 构造没有工具输入
            fake_client = FakeMcpClient(tools=browser_tools)  # 新增代码+MCP参数清洗: 创建可记录调用的 fake 浏览器 client；若省略: 无法检查最终转发参数
            registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+MCP参数清洗: 用真实 browser_automation server 名构造 registry；若省略: 工具名与截图不一致
            permission_requests: list[str] = []  # 新增代码+MCP参数清洗: 收集启动和工具调用授权文本；若省略: 无法断言用户看到的参数
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: permission_requests.append(action) or True, mcp_tool_registry=registry)  # 新增代码+MCP参数清洗: 创建允许权限的 agent 以进入执行路径；若省略: MCP 工具不会启动或调用
            self._select_tool_for_test(agent, "mcp__browser_automation__browser_open")  # 新增代码+ToolArchitectureV2: 先用 select 加载 browser_open；若没有这行代码，v2 门禁会在参数清洗和授权提示前拒绝直接调用
            output = agent._execute_tool(  # 新增代码+MCP参数清洗: 直接执行 browser_open 以触发授权提示；若省略: 无法复现用户看到的授权界面
                ToolCall(  # 新增代码+MCP参数清洗: 构造模型请求的工具调用；若省略: _execute_tool 没有输入
                    name="mcp__browser_automation__browser_open",  # 新增代码+MCP参数清洗: 使用真实前缀工具名；若省略: agent 无法路由到 fake browser_open
                    arguments={  # 新增代码+MCP参数清洗: 模拟模型把多个工具字段混进 browser_open；若省略: 红灯不会覆盖截图问题
                        "status": "all",  # 新增代码+MCP参数清洗: 混入 tabs/status 字段；若省略: 无法确认授权提示会移除 status
                        "action": "list",  # 新增代码+MCP参数清洗: 混入 action 字段；若省略: 无法确认授权提示会移除 action
                        "url": "https://www.bing.com/search?q=Ho+Chi+Minh+City+weather+today",  # 新增代码+MCP参数清洗: 提供真正要打开的页面；若省略: browser_open 缺少核心参数
                        "new_tab": False,  # 新增代码+MCP参数清洗: 提供合法标签页参数；若省略: 无法确认合法字段保留
                        "timeout_ms": 10000,  # 新增代码+MCP参数清洗: 提供合法超时参数；若省略: 无法确认合法字段保留
                        "confirm_real_profile": True,  # 新增代码+MCP参数清洗: 混入真实 Chrome 连接确认字段；若省略: 无法覆盖用户截图里的高混淆字段
                    },  # 新增代码+MCP参数清洗: 参数对象结束；若省略: ToolCall 语法不完整
                )  # 新增代码+MCP参数清洗: ToolCall 构造结束；若省略: _execute_tool 调用不完整
            )  # 新增代码+MCP参数清洗: _execute_tool 调用结束；若省略: 测试没有执行行为
            tool_prompt = permission_requests[-1]  # 新增代码+MCP参数清洗: 取最后一次工具调用授权提示；若省略: 断言可能误看启动 MCP 的授权文本
            self.assertIn('"url": "https://www.bing.com/search?q=Ho+Chi+Minh+City+weather+today"', tool_prompt)  # 新增代码+MCP参数清洗: 断言提示保留用户最该核对的 URL；若省略: 清洗可能过度删除核心参数
            self.assertNotIn('"status"', tool_prompt)  # 新增代码+MCP参数清洗: 断言授权提示不再展示无关 status；若省略: 截图混淆会继续存在
            self.assertNotIn('"action"', tool_prompt)  # 新增代码+MCP参数清洗: 断言授权提示不再展示无关 action；若省略: 用户仍会看到非 browser_open 参数
            self.assertNotIn("confirm_real_profile", tool_prompt)  # 新增代码+MCP参数清洗: 断言授权提示不再展示真实 profile 确认字段；若省略: 用户可能误以为正在连接真实 Chrome profile
            self.assertEqual(fake_client.calls, [("browser_open", {"url": "https://www.bing.com/search?q=Ho+Chi+Minh+City+weather+today", "new_tab": False, "timeout_ms": 10000})])  # 新增代码+MCP参数清洗: 断言真实工具也只收到清洗后的参数；若省略: 只清洗提示不清洗调用仍会有隐藏风险
            self.assertIn("called browser_open", output)  # 新增代码+MCP参数清洗: 断言清洗后工具仍正常执行；若省略: 可能修掉混入字段却破坏调用链路
    def test_mcp_permission_risk_classifies_browser_automation_tools(self) -> None:  # 新增代码+BrowserAutomation: 验证浏览器自动化 MCP 工具获得专门风险分级；若省略: 用户授权时看不出打开网页和执行脚本的不同风险
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BrowserAutomation: 创建临时工作区隔离 agent 初始化副作用；若省略: 测试可能污染真实项目记忆或日志
            workspace = Path(raw_dir)  # 新增代码+BrowserAutomation: 把临时目录转成 Path 供 LearningAgent 使用；若省略: agent 构造参数不清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+BrowserAutomation: 创建允许权限的 agent 用来直接调用风险分类 helper；若省略: 无法验证真实 LearningAgent 的分类逻辑
            open_level, open_note = agent._mcp_tool_risk_summary(ToolCall(name="mcp__browser_automation__browser_open", arguments={"url": "http://127.0.0.1"}))  # 新增代码+BrowserAutomation: 检查打开网页工具的风险摘要；若省略: browser_open 可能被误归类为普通外部工具
            self.assertIn("浏览器", open_level)  # 新增代码+BrowserAutomation: 断言打开网页风险等级明确提到浏览器；若省略: 用户看不出这是会驱动浏览器的操作
            self.assertTrue("url" in open_note.lower() or "网址" in open_note)  # 修改代码+BrowserAutomation: 兼容英文 url/URL 和中文“网址”的风险说明；若省略: 正确中文化实现可能因为没写英文 URL 被误伤
            evaluate_level, evaluate_note = agent._mcp_tool_risk_summary(ToolCall(name="mcp__browser_automation__browser_evaluate", arguments={"script": "window.secret"}))  # 修改代码+BrowserAutomation: 使用设计要求的 script 参数检查 JavaScript 执行工具风险；若省略: 测试会继续用过时 expression 参数误导后续 server 实现
            self.assertIn("高风险", evaluate_level)  # 新增代码+BrowserAutomation: 断言执行 JavaScript 被标为高风险；若省略: 用户可能低估脚本执行副作用
            self.assertIn("JavaScript", evaluate_note)  # 新增代码+BrowserAutomation: 断言风险说明直说 JavaScript；若省略: 初学者不容易理解 evaluate 的含义
            downloads_level, downloads_note = agent._mcp_tool_risk_summary(ToolCall(name="mcp__browser_automation__browser_downloads", arguments={"max_results": 5}))  # 新增代码+BrowserAutomation风险: 检查下载记录工具的风险摘要；若省略: browser_downloads 可能继续被描述成主动下载文件
            self.assertIn("高风险", downloads_level)  # 新增代码+BrowserAutomation风险: 保留下载记录工具的高风险分类；若省略: 下载相关记录可能被低估
            self.assertIn("下载记录", downloads_note)  # 新增代码+BrowserAutomation风险: 断言说明强调这是查看下载记录；若省略: 用户可能误以为工具本身会触发下载
            self.assertIn("触发下载", downloads_note)  # 新增代码+BrowserAutomation风险: 断言说明区分触发下载通常来自点击等工具；若省略: 风险提示会把记录查询和下载动作混在一起
    def test_mcp_permission_risk_classifies_real_chrome_tools(self) -> None:  # 新增代码+RealChrome风险测试: 验证真实 Chrome MCP 工具有专门授权措辞；若省略: 日常 profile 高风险可能被普通浏览器分类掩盖
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RealChrome风险测试: 创建临时工作区隔离 agent 日志和记忆；若省略: 测试可能污染真实 learning_agent 工作区
            workspace = Path(raw_dir)  # 新增代码+RealChrome风险测试: 把临时目录包装成 Path；若省略: LearningAgent 构造输入不够明确
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+RealChrome风险测试: 创建允许权限的 agent 直接测试风险摘要 helper；若省略: 无法覆盖真实分类函数
            connect_level, connect_note = agent._mcp_tool_risk_summary(ToolCall(name="mcp__browser_automation__browser_connect_real_chrome", arguments={"confirm_real_profile": True}))  # 新增代码+RealChrome风险测试: 检查连接真实 Chrome profile 的风险摘要；若省略: 高风险连接工具可能被普通 browser_automation 分支吞掉
            self.assertIn("真实 Chrome 高风险", connect_level)  # 新增代码+RealChrome风险测试: 断言连接工具被标为真实 Chrome 高风险；若省略: 用户可能低估真实登录态暴露风险
            self.assertIn("日常 Chrome profile", connect_note)  # 新增代码+RealChrome风险测试: 断言说明提到日常 profile；若省略: 用户看不出这不是临时浏览器
            self.assertIn("登录态", connect_note)  # 新增代码+RealChrome风险测试: 断言说明提到真实登录态；若省略: 授权前无法理解敏感边界
            self.assertIn("confirm_real_profile", connect_note)  # 新增代码+RealChrome风险测试: 断言说明提示核对确认参数；若省略: 用户可能不知道哪个参数表示已确认真实 profile
            disconnect_level, disconnect_note = agent._mcp_tool_risk_summary(ToolCall(name="mcp__browser_automation__browser_disconnect_real_chrome", arguments={}))  # 新增代码+RealChrome风险测试: 检查断开真实 Chrome CDP 连接的风险摘要；若省略: 断开工具可能被误标成只读状态
            self.assertIn("真实 Chrome 中风险", disconnect_level)  # 新增代码+RealChrome风险测试: 断言断开工具被标为中风险；若省略: 用户可能看不出它会改变浏览器连接状态
            self.assertIn("close_browser", disconnect_note)  # 新增代码+RealChrome风险测试: 断言说明提示核对 close_browser；若省略: 用户不知道是否会关闭浏览器
            self.assertIn("默认不关闭", disconnect_note)  # 新增代码+RealChrome风险测试: 断言说明明确默认不关闭用户 Chrome；若省略: 用户可能误以为断开一定会关掉日常浏览器
            status_level, status_note = agent._mcp_tool_risk_summary(ToolCall(name="mcp__browser_automation__browser_profile_status", arguments={}))  # 新增代码+RealChrome风险测试: 检查真实 Chrome 状态工具的只读风险摘要；若省略: 状态工具可能缺少隐私边界说明
            self.assertTrue("只读" in status_level or "低风险" in status_level)  # 新增代码+RealChrome风险测试: 断言状态工具风险等级表明只读或低风险；若省略: 低副作用工具可能被过度或错误标记
            self.assertIn("当前浏览器会话模式", status_note)  # 新增代码+RealChrome风险测试: 断言说明只读取当前会话模式；若省略: 用户不知道 status 到底看什么
            self.assertIn("页面数量", status_note)  # 新增代码+RealChrome风险测试: 断言说明只读取页面数量；若省略: 状态输出范围不清楚
            self.assertIn("最近安全拒绝", status_note)  # 新增代码+RealChrome风险测试: 断言说明读取最近安全拒绝摘要；若省略: 安全审计范围不清楚
            self.assertIn("cookies", status_note)  # 新增代码+RealChrome风险测试: 断言说明不读取 cookies；若省略: 用户可能担心状态工具偷看登录 cookie
            self.assertIn("storage", status_note)  # 新增代码+RealChrome风险测试: 断言说明不读取 storage；若省略: localStorage/sessionStorage 边界不清楚
            self.assertIn("token", status_note)  # 新增代码+RealChrome风险测试: 断言说明不读取 token；若省略: 用户可能担心令牌泄露
            self.assertIn("密码", status_note)  # 新增代码+RealChrome风险测试: 断言说明不读取密码；若省略: 用户可能担心密码字段泄露
    def test_mcp_permission_prompt_marks_delete_tool_risk(self) -> None:  # 新增代码+权限分级: 验证删除类 MCP 工具授权提示会标明破坏性风险；若省略: 删除文件这种高风险操作可能只显示普通外部工具提示
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+权限分级: 创建临时工作区隔离测试副作用；若省略: 测试可能影响真实项目文件
            workspace = Path(raw_dir)  # 新增代码+权限分级: 把临时路径转成 Path；若省略: agent 构造参数不够明确
            delete_tools = [{"name": "delete_file", "description": "删除文件", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "confirm_delete": {"type": "boolean"}}, "required": ["path", "confirm_delete"]}}]  # 新增代码+权限分级: 构造 workspace_tools 的删除工具 schema；若省略: fake MCP server 没有删除工具可供风险分类
            fake_client = FakeMcpClient(tools=delete_tools)  # 新增代码+权限分级: 创建只暴露 delete_file 的 fake MCP client；若省略: 测试无法覆盖删除工具风险提示
            registry = McpToolRegistry({"workspace_tools": fake_client})  # 新增代码+权限分级: 用 workspace_tools server 名生成真实删除工具名；若省略: 风险分类不会贴近真实运行路径
            permission_requests: list[str] = []  # 新增代码+权限分级: 记录权限提示文本；若省略: 无法检查删除操作提示是否足够醒目
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: permission_requests.append(action) or True, mcp_tool_registry=registry)  # 新增代码+权限分级: 创建始终允许的 agent 以便观察提示并执行工具；若省略: MCP 删除工具不会进入测试路径
            self._select_tool_for_test(agent, "mcp__workspace_tools__delete_file")  # 新增代码+ToolArchitectureV2: 先把删除工具加载进当前 Tool Pool；若没有这行代码，直接调用会被 deferred 门禁拒绝而不会出现删除风险提示
            output = agent._execute_tool(ToolCall(name="mcp__workspace_tools__delete_file", arguments={"path": "old.txt", "confirm_delete": True}))  # 新增代码+权限分级: 触发删除 MCP 工具授权提示；若省略: 删除风险分级不会被验证
            self.assertIn("风险等级：删除/破坏性操作", permission_requests[-1])  # 新增代码+权限分级: 断言提示明确标记删除风险；若省略: 用户可能把删除误认为普通读取或搜索
            self.assertIn("confirm_delete", permission_requests[-1])  # 新增代码+权限分级: 断言提示展示删除确认参数；若省略: 用户无法确认模型是否真的带了删除确认
            self.assertIn("called delete_file", output)  # 新增代码+权限分级: 断言风险提示不影响已授权工具转发；若省略: 只验证提示无法保证功能仍可用
    def test_agent_does_not_expose_mcp_tools_when_start_permission_is_denied(self) -> None:  # 新增代码+MCP接入健壮性: 验证拒绝启动时不会暴露复用 registry 里的旧 MCP 工具；若省略: 旧 schema 和旧 route 可能绕过本次权限拒绝
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP接入健壮性: 创建临时工作区隔离 agent 初始化文件；若省略: 测试可能污染真实 learning_agent 目录
            workspace = Path(raw_dir)  # 新增代码+MCP接入健壮性: 把临时目录转成 Path；若省略: 构造 LearningAgent 时路径处理不够清楚
            fake_client = FakeMcpClient()  # 新增代码+MCP接入健壮性: 创建可观察调用历史的 fake MCP client；若省略: 无法证明拒绝后没有调用外部工具
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+MCP接入健壮性: 创建可复用的 MCP 注册表；若省略: 无法模拟旧 registry 已经缓存 schema 的场景
            registry.start()  # 新增代码+MCP接入健壮性: 预先启动 registry 让内部已有旧 schema 和 route；若省略: 无法覆盖复用 registry 的权限绕过风险
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: False, mcp_tool_registry=registry)  # 新增代码+MCP接入健壮性: 构造拒绝启动权限的 agent；若省略: 无法验证拒绝启动后的禁用状态
            tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+MCP接入健壮性: 读取 agent 当前暴露给模型的工具名；若省略: 无法断言旧 MCP schema 是否被隐藏
            output = agent._execute_tool(ToolCall(name="mcp__demo__echo", arguments={"text": "x"}))  # 新增代码+MCP接入健壮性: 直接尝试执行旧 MCP route；若省略: 只能验证 schema 隐藏不能验证调用禁用
            self.assertNotIn("mcp__demo__echo", tool_names)  # 新增代码+MCP接入健壮性: 断言拒绝启动后不暴露旧 MCP 工具；若省略: 模型仍可能看到未授权工具
            self.assertEqual(fake_client.calls, [])  # 新增代码+MCP接入健壮性: 断言拒绝启动后没有调用外部 MCP client；若省略: route 绕过权限不会被发现
            self.assertIn("MCP 工具不可用", output)  # 新增代码+MCP接入健壮性: 断言禁用状态返回可读错误；若省略: 模型无法理解 MCP 工具为什么不能执行
    def test_agent_survives_mcp_registry_start_failure(self) -> None:  # 修改代码+MCP启动隔离: 验证唯一 MCP server 启动失败时 agent 不崩溃且禁用 MCP；若省略: 全部失败场景可能暴露坏工具或缺少错误说明
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP接入健壮性: 创建临时工作区隔离构造副作用；若省略: 测试可能写入真实目录
            workspace = Path(raw_dir)  # 新增代码+MCP接入健壮性: 包装临时路径方便传入 LearningAgent；若省略: 后续路径拼接不稳定
            fake_client = FakeMcpClient(start_error=RuntimeError("boom"))  # 新增代码+MCP接入健壮性: 创建启动时抛错的 fake MCP client；若省略: 无法稳定复现 start 失败
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+MCP接入健壮性: 用失败 client 构造 MCP 注册表；若省略: agent 无法触发 registry.start 异常
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="构造后仍可用。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+MCP接入健壮性: 构造允许启动但 start 会失败的 agent；若省略: 防崩溃行为没有被测对象
            tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+MCP接入健壮性: 读取失败后的可见工具列表；若省略: 无法确认失败时 MCP 工具被隐藏
            self.assertNotIn("mcp__demo__echo", tool_names)  # 新增代码+MCP接入健壮性: 断言启动失败后不暴露 MCP 工具；若省略: 失败 registry 可能仍把半成品工具暴露给模型
            self.assertIn("所有 MCP server 启动失败", agent.mcp_start_error)  # 修改代码+MCP启动隔离: 断言全部失败时保存清楚状态；若省略: 用户无法区分全部不可用和部分失败
            self.assertIn("demo=boom", agent.mcp_start_error)  # 新增代码+MCP启动隔离: 断言错误说明包含失败 server 名和原因；若省略: 用户不知道哪个 MCP server 坏了
            self.assertFalse(agent.mcp_tools_enabled)  # 修改代码+MCP启动隔离: 断言没有任何可用 server 时 MCP 被禁用；若省略: 后续调用可能继续进入坏 registry
    def test_agent_closes_partially_started_mcp_clients_when_start_fails(self) -> None:  # 修改代码+MCP启动隔离: 沿用旧测试名验证部分失败不会拖垮已成功 server；若省略: 一个坏 server 会让全部 MCP 能力消失
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP接入清理: 创建临时工作区隔离 agent 初始化文件；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+MCP接入清理: 把临时目录转成 Path；若省略: 后续传入 LearningAgent 的路径不够稳定
            fake_client_ok = FakeMcpClient(result_prefix="ok")  # 新增代码+MCP接入清理: 创建第一个可成功启动的 fake MCP client；若省略: 无法模拟已经部分启动的 server
            class ListToolsFailingMcpClient(FakeMcpClient):  # 新增代码+MCP启动隔离: 定义 list_tools 阶段失败的 fake client；若省略: 普通 tools/list 失败不会被回归测试覆盖
                def list_tools(self) -> list[dict[str, object]]:  # 新增代码+MCP启动隔离: 覆盖工具列表接口来模拟 server 已启动但列工具失败；若省略: 测试只能覆盖 start 失败
                    raise RuntimeError("boom")  # 新增代码+MCP启动隔离: 抛出稳定异常模拟 browser_automation 依赖坏掉；若省略: 无法触发部分失败隔离路径
            fake_client_bad = ListToolsFailingMcpClient(result_prefix="bad")  # 修改代码+MCP启动隔离: 创建 list_tools 失败的 bad client；若省略: 无法验证 list_tools 失败不会拖垮 ok server
            registry = McpToolRegistry({"ok": fake_client_ok, "bad": fake_client_bad})  # 新增代码+MCP接入清理: 构造按顺序启动 ok 后再失败 bad 的 registry；若省略: 无法验证部分启动清理路径
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="构造后仍可用。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+MCP接入清理: 构造允许启动但第二个 server 失败的 agent；若省略: 被测清理逻辑不会执行
            initial_tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 修改代码+ToolArchitectureV2: 读取 select 前的可见工具名；若没有这行代码，无法证明成功 server 的 MCP 工具仍默认 deferred
            self.assertNotIn("mcp__ok__echo", initial_tool_names)  # 新增代码+ToolArchitectureV2: 断言 ok server 工具默认不直接暴露；若没有这行代码，部分失败测试可能退回全量暴露旧契约
            self._select_tool_for_test(agent, "mcp__ok__echo")  # 新增代码+ToolArchitectureV2: 加载成功 server 的 MCP 工具；若没有这行代码，后续执行会被 deferred 门禁拒绝
            tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 修改代码+ToolArchitectureV2: 读取 select 后的可见工具名；若没有这行代码，无法确认加载后 Tool Pool 更新
            output = agent._execute_tool(ToolCall(name="mcp__ok__echo", arguments={"text": "ping"}))  # 新增代码+MCP启动隔离: 调用 ok server 工具验证成功 server 仍可用；若省略: 只看 schema 不能证明路由可调用
            self.assertTrue(agent.mcp_tools_enabled)  # 新增代码+MCP启动隔离: 断言存在可用 server 时 MCP 整体保持启用；若省略: 部分失败仍可能把全部 MCP 禁用
            self.assertIn("部分 MCP server 启动失败", agent.mcp_start_error)  # 新增代码+MCP启动隔离: 断言部分失败被记录但不等于全局失败；若省略: 用户无法知道有 server 需要修复
            self.assertIn("bad=boom", agent.mcp_start_error)  # 新增代码+MCP启动隔离: 断言错误说明包含失败 server 名和原因；若省略: 排查坏 server 会更困难
            self.assertFalse(fake_client_ok.closed)  # 修改代码+MCP启动隔离: 断言成功启动的 ok client 没有被关闭；若省略: 可用 server 可能被错误清理
            self.assertTrue(fake_client_bad.closed)  # 修改代码+MCP启动隔离: 断言失败的 bad client 被关闭；若省略: 失败 server 资源可能残留
            self.assertIn("mcp__ok__echo", tool_names)  # 修改代码+MCP启动隔离: 断言 ok server 的工具仍暴露给模型；若省略: 部分失败可能隐藏可用工具
            self.assertNotIn("mcp__bad__echo", tool_names)  # 修改代码+MCP启动隔离: 断言失败 server 的工具不会暴露；若省略: 半失败状态可能进入模型工具列表
            self.assertIn("ok echo: ping", output)  # 新增代码+MCP启动隔离: 断言调用结果来自 ok client；若省略: 不能证明路由没有被部分失败破坏
    def test_agent_reports_mcp_call_failure_as_tool_result(self) -> None:  # 新增代码+MCP接入健壮性: 验证 MCP 工具调用异常会转成可读工具结果；若省略: 外部工具失败可能中断 agent 循环
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP接入健壮性: 创建临时工作区隔离日志和 memory；若省略: 测试可能污染真实目录
            workspace = Path(raw_dir)  # 新增代码+MCP接入健壮性: 把临时目录转成 Path；若省略: LearningAgent 构造不够明确
            fake_client = FakeMcpClient(call_error=RuntimeError("call boom"))  # 新增代码+MCP接入健壮性: 创建调用时抛错的 fake MCP client；若省略: 无法覆盖 MCP call 异常
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+MCP接入健壮性: 构造包含失败工具的 registry；若省略: agent 没有 MCP 工具可调用
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+MCP接入健壮性: 创建允许启动和调用的 agent；若省略: MCP call 失败路径无法执行
            self._select_tool_for_test(agent, "mcp__demo__echo")  # 新增代码+ToolArchitectureV2: 先加载失败工具以进入真实 MCP 调用路径；若没有这行代码，测试只会命中未加载门禁而不是 call_error
            output = agent._execute_tool(ToolCall(name="mcp__demo__echo", arguments={"text": "x"}))  # 新增代码+MCP接入健壮性: 直接执行 MCP 工具触发 call_error；若省略: 无法断言工具结果文本
            self.assertIn("MCP 工具调用失败", output)  # 新增代码+MCP接入健壮性: 断言异常被转成规定的可读前缀；若省略: 错误格式回归不会被发现
            self.assertIn("call boom", output)  # 新增代码+MCP接入健壮性: 断言原始异常信息被保留；若省略: 排查外部工具失败会更困难
    def test_mcp_call_progress_records_permission_start_and_completion(self) -> None:  # 新增代码+MCPProgress: 验证 MCP 调用会记录权限、开始和完成进度；若没有这行代码，Phase 3 call progress 回归不会被发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCPProgress: 创建临时工作区隔离日志和产物；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+MCPProgress: 把临时目录转换成 Path；若没有这行代码，LearningAgent 构造不够明确
            fake_client = FakeMcpClient()  # 新增代码+MCPProgress: 创建默认 echo MCP client；若没有这行代码，agent 没有可调用的 MCP 工具
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+MCPProgress: 用 fake client 构造 registry；若没有这行代码，MCP 工具无法进入 catalog
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+MCPProgress: 创建自动授权 agent 以覆盖完整调用路径；若没有这行代码，测试无法执行 MCP 工具
            self._select_tool_for_test(agent, "mcp__demo__echo")  # 新增代码+MCPProgress: 先通过 tool_search 加载 deferred MCP 工具；若没有这行代码，执行会被未加载门禁拒绝
            output = agent._execute_tool(ToolCall(name="mcp__demo__echo", arguments={"text": "progress"}))  # 新增代码+MCPProgress: 执行 echo 工具产生真实进度事件；若没有这行代码，被测逻辑不会运行
            states = [event["state"] for event in agent.mcp_call_progress_events]  # 新增代码+MCPProgress: 收集结构化进度状态；若没有这行代码，后续断言只能读最终文本
            observation_kinds = [event["kind"] for event in agent.observation_events]  # 新增代码+MCPProgress: 收集通用 observation 类型；若没有这行代码，无法证明进度同步进入 Phase 6 观察流
            self.assertIn("called echo: progress", output)  # 新增代码+MCPProgress: 断言工具本身仍正常返回；若没有这行代码，只测进度可能漏掉调用失败
            self.assertIn("permission_requested", states)  # 新增代码+MCPProgress: 断言权限请求阶段被记录；若没有这行代码，用户确认前后无法审计
            self.assertIn("started", states)  # 新增代码+MCPProgress: 断言外部工具开始阶段被记录；若没有这行代码，长工具调用没有开始信号
            self.assertIn("completed", states)  # 新增代码+MCPProgress: 断言外部工具完成阶段被记录；若没有这行代码，成功调用缺少收尾证据
            self.assertIn("mcp_call_progress", observation_kinds)  # 新增代码+MCPProgress: 断言 MCP 进度进入统一 observation；若没有这行代码，Phase 6 审计需要查多个私有列表
    def test_builtin_tool_takes_priority_over_mcp_tool_name(self) -> None:  # 新增代码+MCP接入健壮性: 验证内置工具名优先于 MCP 同名工具；若省略: MCP registry 可能覆盖 read_file 等核心工具
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP接入健壮性: 创建临时工作区放置待读文件；若省略: 读文件测试会污染真实目录
            workspace = Path(raw_dir)  # 新增代码+MCP接入健壮性: 包装临时目录为 Path；若省略: 后续文件路径拼接不方便
            (workspace / "hello.txt").write_text("内置读取结果", encoding="utf-8")  # 新增代码+MCP接入健壮性: 写入内置 read_file 应读取的内容；若省略: 无法证明执行的是内置读文件
            class ConflictingRegistry:  # 新增代码+MCP接入健壮性: 定义测试专用冲突 registry；若省略: McpToolRegistry 的前缀命名无法模拟 read_file 同名冲突
                def __init__(self) -> None:  # 新增代码+MCP接入健壮性: 初始化冲突 registry 调用记录；若省略: 无法断言 MCP call 未发生
                    self.calls: list[tuple[str, dict[str, object]]] = []  # 新增代码+MCP接入健壮性: 保存被调用历史；若省略: 内置优先级无法被直接观察
                def has_servers(self) -> bool:  # 新增代码+MCP接入健壮性: 声明存在 server 以触发 agent 的 MCP 启动路径；若省略: agent 不会设置 MCP 启用状态
                    return True  # 新增代码+MCP接入健壮性: 返回 True 模拟有 MCP server；若省略: 冲突 registry 不会进入启动分支
                def server_names(self) -> list[str]:  # 新增代码+MCP接入健壮性: 提供权限提示所需 server 名；若省略: agent 初始化会缺少方法
                    return ["conflict"]  # 新增代码+MCP接入健壮性: 返回测试 server 名；若省略: 权限提示无法构造
                def start(self) -> None:  # 新增代码+MCP接入健壮性: 提供启动方法让 agent 初始化成功；若省略: agent 初始化会抛 AttributeError
                    return None  # 新增代码+MCP接入健壮性: 启动不做事；若省略: 测试需要无关外部状态
                def tool_schemas(self) -> list[dict[str, object]]:  # 新增代码+MCP接入健壮性: 暴露一个同名 read_file schema；若省略: 无法模拟 MCP 与内置工具重名
                    return [{"type": "function", "function": {"name": "read_file", "description": "冲突工具", "parameters": {"type": "object"}}}]  # 新增代码+MCP接入健壮性: 返回同名 schema；若省略: 模型工具列表不会出现冲突输入
                def has_tool(self, name: str) -> bool:  # 新增代码+MCP接入健壮性: 声明 registry 也拥有 read_file；若省略: _execute_tool 不会面临冲突选择
                    return name == "read_file"  # 新增代码+MCP接入健壮性: 只让 read_file 冲突；若省略: 测试意图不明确
                def call_tool(self, name: str, arguments: dict[str, object]) -> str:  # 新增代码+MCP接入健壮性: 如果误走 MCP 就记录并报错；若省略: 无法发现内置优先级被破坏
                    self.calls.append((name, arguments))  # 新增代码+MCP接入健壮性: 记录误调用；若省略: 断言无法观察 MCP 是否被调用
                    raise RuntimeError("不应该调用 MCP read_file")  # 新增代码+MCP接入健壮性: 误走 MCP 时立即暴露问题；若省略: 测试可能假阳性
            registry = ConflictingRegistry()  # 新增代码+MCP接入健壮性: 创建冲突 registry 实例；若省略: agent 没有测试用 MCP 注入对象
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+MCP接入健壮性: 创建带冲突 registry 的 agent；若省略: 无法测试内置优先级
            output = agent._execute_tool(ToolCall(name="read_file", arguments={"path": "hello.txt"}))  # 新增代码+MCP接入健壮性: 直接请求 read_file；若省略: 冲突分发不会发生
            self.assertIn("内置读取结果", output)  # 新增代码+MCP接入健壮性: 断言结果来自内置 read_file；若省略: 不能证明内置工具优先
            self.assertEqual(registry.calls, [])  # 新增代码+MCP接入健壮性: 断言 MCP registry 没有被调用；若省略: 内置优先级可能被悄悄破坏
    def test_workspace_tools_mcp_server_lists_and_searches_workspace(self) -> None:  # 新增代码+workspace_tools: 验证本地工作区 MCP server 能列目录、按 glob 找文件并 grep 内容；若省略: Claude Code 高频本地工具能力没有端到端保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+workspace_tools: 创建临时工作区隔离测试文件；若省略: 测试会污染真实 learning_agent 目录
            workspace = Path(raw_dir)  # 新增代码+workspace_tools: 把临时目录转为 Path 便于拼接文件；若省略: 后续路径处理会更脆弱
            docs_dir = workspace / "docs"  # 新增代码+workspace_tools: 准备嵌套目录用于验证 list_dir 和 glob；若省略: 测试只能覆盖根目录单文件
            docs_dir.mkdir()  # 新增代码+workspace_tools: 创建 docs 子目录；若省略: 写入 docs/guide.txt 会失败
            (docs_dir / "guide.txt").write_text("alpha needle beta", encoding="utf-8")  # 新增代码+workspace_tools: 写入含搜索词的文本文件；若省略: grep 没有可命中的内容
            (workspace / "notes.md").write_text("普通笔记", encoding="utf-8")  # 新增代码+workspace_tools: 写入另一个文件用于验证目录列表；若省略: list_dir 输出覆盖面不足
            server_script = (TEST_ROOT / "workspace_tools_mcp_server.py")  # 新增代码+workspace_tools: 定位待新增的 workspace_tools MCP server 脚本；若省略: 测试无法启动真实 server
            self.assertTrue(server_script.exists(), "workspace_tools_mcp_server.py 应该存在")  # 新增代码+workspace_tools: 红灯阶段先确认文件缺失会失败；若省略: 缺文件会变成较慢的子进程超时
            config = McpServerConfig(name="workspace_tools", command=sys.executable, args=[str(server_script), str(workspace)])  # 新增代码+workspace_tools: 构造指向临时工作区的 MCP server 配置；若省略: client 不知道启动哪个 server
            client = McpStdioClient(config)  # 新增代码+workspace_tools: 创建最小 MCP stdio client；若省略: 无法走 initialize/tools/list/tools/call 真实协议
            try:  # 新增代码+workspace_tools: 用 try/finally 确保测试结束关闭子进程；若省略: 失败时可能残留 MCP 进程
                client.start()  # 新增代码+workspace_tools: 启动 server 并完成 MCP 初始化握手；若省略: 后续 list_tools 和 call_tool 没有连接
                tool_names = [tool["name"] for tool in client.list_tools()]  # 新增代码+workspace_tools: 收集 server 暴露的原始工具名；若省略: 无法断言模型能看到哪些能力
                self.assertIn("list_dir", tool_names)  # 新增代码+workspace_tools: 断言目录列表工具存在；若省略: agent 仍可能无法发现目录内容
                self.assertIn("glob", tool_names)  # 新增代码+workspace_tools: 断言文件模式匹配工具存在；若省略: Claude Code 的 Glob 类能力没有保护
                self.assertIn("grep", tool_names)  # 新增代码+workspace_tools: 断言内容搜索工具存在；若省略: Claude Code 的 Grep 类能力没有保护
                self.assertIn("read_file", tool_names)  # 新增代码+MCP文件工具: 断言 MCP 版读取文件工具存在；若省略: agent 仍会依赖内置 read_file 而不是统一 MCP 文件通道
                self.assertIn("write_file", tool_names)  # 新增代码+MCP文件工具: 断言 MCP 版覆盖写入工具存在；若省略: agent 不能通过 workspace_tools 写已有文件
                self.assertIn("create_file", tool_names)  # 新增代码+MCP文件工具: 断言 MCP 版新建文件工具存在；若省略: agent 不能通过 workspace_tools 安全创建新文件
                self.assertIn("copy_file", tool_names)  # 新增代码+MCP文件操作: 断言 MCP 版复制文件工具存在；若省略: agent 不能通过 workspace_tools 复制工作区文件
                self.assertIn("move_file", tool_names)  # 新增代码+MCP文件操作: 断言 MCP 版移动文件工具存在；若省略: agent 不能通过 workspace_tools 重命名或移动文件
                self.assertIn("delete_file", tool_names)  # 新增代码+MCP文件操作: 断言 MCP 版删除文件工具存在；若省略: agent 不能通过 workspace_tools 请求受控删除文件
                self.assertIn("run_powershell", tool_names)  # 新增代码+workspace_tools: 断言命令执行工具 schema 存在；若省略: 后续模型不会知道可请求 PowerShell 验证
                self.assertIn("edit_file", tool_names)  # 新增代码+edit_file: 断言精确编辑工具 schema 存在；若省略: agent 可能仍无法对标 Claude Code 的 Edit 能力
                list_output = client.call_tool("list_dir", {"path": "."})  # 新增代码+workspace_tools: 调用目录列表工具；若省略: 只验证 schema 不验证真实工具执行
                self.assertIn("docs/", list_output)  # 新增代码+workspace_tools: 断言输出包含目录标记；若省略: list_dir 格式回归不会被发现
                self.assertIn("notes.md", list_output)  # 新增代码+workspace_tools: 断言输出包含根目录文件；若省略: 普通文件可能被遗漏
                glob_output = client.call_tool("glob", {"pattern": "**/*.txt"})  # 新增代码+workspace_tools: 调用 glob 查找 txt 文件；若省略: 模式搜索行为没有端到端验证
                self.assertIn("docs/guide.txt", glob_output)  # 新增代码+workspace_tools: 断言 glob 返回相对路径；若省略: 输出可能变成绝对路径或漏文件
                grep_output = client.call_tool("grep", {"query": "needle", "pattern": "**/*.txt", "max_results": 5})  # 新增代码+workspace_tools: 调用 grep 搜索文件内容；若省略: 内容搜索能力没有真实验证
                self.assertIn("docs/guide.txt", grep_output)  # 新增代码+workspace_tools: 断言 grep 标明命中文件；若省略: 用户无法定位搜索结果来源
                self.assertIn("needle", grep_output)  # 新增代码+workspace_tools: 断言 grep 返回命中行内容；若省略: 搜索结果可能只显示文件名而不足以回答问题
            finally:  # 新增代码+workspace_tools: 无论测试成功失败都进入清理；若省略: 子进程清理不可靠
                client.close()  # 新增代码+workspace_tools: 关闭 MCP 子进程；若省略: 测试结束后可能留下后台进程
    def test_workspace_tools_edit_file_replaces_exact_text(self) -> None:  # 新增代码+edit_file: 验证 workspace_tools 能对工作区文件做精确文本替换；若省略: 新增 Edit 类能力没有端到端保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+edit_file: 创建临时工作区隔离真实文件；若省略: 测试可能修改用户项目文件
            workspace = Path(raw_dir)  # 新增代码+edit_file: 把临时目录转成 Path；若省略: 后续文件读写表达不清楚
            target_file = workspace / "sample.txt"  # 新增代码+edit_file: 准备要编辑的测试文件路径；若省略: edit_file 没有目标文件
            target_file.write_text("hello old world\n", encoding="utf-8")  # 新增代码+edit_file: 写入包含 old_text 的初始内容；若省略: 替换测试没有匹配文本
            server_script = (TEST_ROOT / "workspace_tools_mcp_server.py")  # 新增代码+edit_file: 定位真实 workspace_tools MCP server；若省略: 测试无法走真实协议
            config = McpServerConfig(name="workspace_tools", command=sys.executable, args=[str(server_script), str(workspace)])  # 新增代码+edit_file: 构造指向临时工作区的 MCP 配置；若省略: server 不知道要限制在哪个目录
            client = McpStdioClient(config)  # 新增代码+edit_file: 创建 MCP stdio client；若省略: 无法调用真实 edit_file 工具
            try:  # 新增代码+edit_file: 用 try/finally 保证子进程被关闭；若省略: 测试失败可能残留进程
                client.start()  # 新增代码+edit_file: 启动 server 并完成初始化；若省略: tools/call 没有连接
                output = client.call_tool("edit_file", {"path": "sample.txt", "old_text": "old", "new_text": "new"})  # 新增代码+edit_file: 请求把 old 精确替换成 new；若省略: 无法验证编辑行为
                self.assertIn("已修改", output)  # 新增代码+edit_file: 断言工具报告修改成功；若省略: 工具可能静默失败
                self.assertIn("替换次数：1", output)  # 新增代码+edit_file: 断言只替换一次；若省略: 多替换或零替换不会被发现
                self.assertEqual(target_file.read_text(encoding="utf-8"), "hello new world\n")  # 新增代码+edit_file: 断言文件真实内容已改变；若省略: 只看工具文本可能假阳性
            finally:  # 新增代码+edit_file: 进入清理分支；若省略: 子进程关闭不可靠
                client.close()  # 新增代码+edit_file: 关闭 MCP 子进程；若省略: 测试结束后可能留下后台进程
    def test_workspace_tools_edit_file_refuses_ambiguous_replacement(self) -> None:  # 新增代码+edit_file: 验证 edit_file 默认拒绝多处相同文本的模糊替换；若省略: agent 可能误改文件多个位置
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+edit_file: 创建临时工作区；若省略: 测试会污染真实文件
            workspace = Path(raw_dir)  # 新增代码+edit_file: 把临时目录转成 Path；若省略: 后续路径处理不清楚
            target_file = workspace / "sample.txt"  # 新增代码+edit_file: 准备重复文本文件路径；若省略: edit_file 没有测试目标
            target_file.write_text("same\nsame\n", encoding="utf-8")  # 新增代码+edit_file: 写入两处相同 old_text；若省略: 无法覆盖模糊替换场景
            server_script = (TEST_ROOT / "workspace_tools_mcp_server.py")  # 新增代码+edit_file: 定位真实 workspace_tools MCP server；若省略: 测试不能端到端执行
            config = McpServerConfig(name="workspace_tools", command=sys.executable, args=[str(server_script), str(workspace)])  # 新增代码+edit_file: 构造临时工作区 server 配置；若省略: server 会操作错误目录
            client = McpStdioClient(config)  # 新增代码+edit_file: 创建 MCP client；若省略: 无法调用 edit_file
            try:  # 新增代码+edit_file: 确保后续关闭子进程；若省略: 测试失败会残留进程
                client.start()  # 新增代码+edit_file: 启动并初始化 server；若省略: tools/call 会失败
                output = client.call_tool("edit_file", {"path": "sample.txt", "old_text": "same", "new_text": "changed"})  # 新增代码+edit_file: 请求替换模糊 old_text；若省略: 无法验证安全拒绝
                self.assertIn("出现 2 次", output)  # 新增代码+edit_file: 断言工具指出文本出现多次；若省略: 模糊错误信息可能退化
                self.assertIn("replace_all", output)  # 新增代码+edit_file: 断言工具提示显式全量替换开关；若省略: 模型不知道下一步怎么修正
                self.assertEqual(target_file.read_text(encoding="utf-8"), "same\nsame\n")  # 新增代码+edit_file: 断言文件没有被误改；若省略: 安全拒绝可能只是返回文本但实际已修改
            finally:  # 新增代码+edit_file: 进入清理分支；若省略: 子进程关闭不可靠
                client.close()  # 新增代码+edit_file: 关闭 MCP 子进程；若省略: 测试会泄漏进程
    def test_workspace_tools_edit_file_supports_multiple_edits(self) -> None:  # 新增代码+edit_file批量编辑: 验证 edit_file 能一次完成多个精确替换；若省略: agent 仍需要多轮工具调用才能完成同一文件的多个小修改
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+edit_file批量编辑: 创建临时工作区隔离真实文件；若省略: 测试可能修改用户项目文件
            workspace = Path(raw_dir)  # 新增代码+edit_file批量编辑: 把临时目录转成 Path；若省略: 后续文件操作不够清楚
            target_file = workspace / "multi.txt"  # 新增代码+edit_file批量编辑: 准备要批量编辑的文件；若省略: edit_file 没有目标
            target_file.write_text("alpha old_a\nbeta old_b\n", encoding="utf-8")  # 新增代码+edit_file批量编辑: 写入两个不同待替换片段；若省略: 无法验证多段替换
            server_script = (TEST_ROOT / "workspace_tools_mcp_server.py")  # 新增代码+edit_file批量编辑: 定位真实 workspace_tools MCP server；若省略: 测试无法走真实 MCP 协议
            config = McpServerConfig(name="workspace_tools", command=sys.executable, args=[str(server_script), str(workspace)])  # 新增代码+edit_file批量编辑: 构造临时工作区 server 配置；若省略: server 可能操作错误目录
            client = McpStdioClient(config)  # 新增代码+edit_file批量编辑: 创建 MCP client；若省略: 无法调用 edit_file
            try:  # 新增代码+edit_file批量编辑: 确保测试结束关闭子进程；若省略: 失败时可能残留进程
                client.start()  # 新增代码+edit_file批量编辑: 启动并初始化 server；若省略: tools/call 无法执行
                output = client.call_tool("edit_file", {"path": "multi.txt", "edits": [{"old_text": "old_a", "new_text": "new_a"}, {"old_text": "old_b", "new_text": "new_b"}]})  # 新增代码+edit_file批量编辑: 请求一次提交两个替换；若省略: 无法验证多段编辑输入
                self.assertIn("替换次数：2", output)  # 新增代码+edit_file批量编辑: 断言两个替换都执行；若省略: 部分替换成功不会被发现
                self.assertEqual(target_file.read_text(encoding="utf-8"), "alpha new_a\nbeta new_b\n")  # 新增代码+edit_file批量编辑: 断言文件真实完成两处修改；若省略: 只看工具文本可能假阳性
            finally:  # 新增代码+edit_file批量编辑: 进入清理分支；若省略: 子进程关闭不可靠
                client.close()  # 新增代码+edit_file批量编辑: 关闭 MCP 子进程；若省略: 测试会泄漏进程
    def test_workspace_tools_edit_file_dry_run_returns_diff_without_writing(self) -> None:  # 新增代码+edit_file预览: 验证 dry_run 只返回 diff 预览而不写文件；若省略: agent 无法先审阅修改再执行
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+edit_file预览: 创建临时工作区隔离真实文件；若省略: 测试可能修改用户项目文件
            workspace = Path(raw_dir)  # 新增代码+edit_file预览: 把临时目录转成 Path；若省略: 后续路径表达不清楚
            target_file = workspace / "preview.txt"  # 新增代码+edit_file预览: 准备 dry_run 目标文件；若省略: edit_file 没有预览对象
            target_file.write_text("before\n", encoding="utf-8")  # 新增代码+edit_file预览: 写入预览前内容；若省略: diff 无法显示变化
            server_script = (TEST_ROOT / "workspace_tools_mcp_server.py")  # 新增代码+edit_file预览: 定位真实 workspace_tools MCP server；若省略: 测试无法走真实协议
            config = McpServerConfig(name="workspace_tools", command=sys.executable, args=[str(server_script), str(workspace)])  # 新增代码+edit_file预览: 构造临时工作区 server 配置；若省略: server 会操作错误目录
            client = McpStdioClient(config)  # 新增代码+edit_file预览: 创建 MCP client；若省略: 无法调用 edit_file
            try:  # 新增代码+edit_file预览: 确保子进程关闭；若省略: 失败时可能残留进程
                client.start()  # 新增代码+edit_file预览: 启动并初始化 server；若省略: tools/call 无法执行
                output = client.call_tool("edit_file", {"path": "preview.txt", "old_text": "before", "new_text": "after", "dry_run": True})  # 新增代码+edit_file预览: 请求 dry_run 预览替换；若省略: 无法验证预览模式
                self.assertIn("预览模式", output)  # 新增代码+edit_file预览: 断言工具明确说明没有写入；若省略: 用户可能误以为已修改
                self.assertIn("-before", output)  # 新增代码+edit_file预览: 断言 diff 显示删除行；若省略: 预览信息不足
                self.assertIn("+after", output)  # 新增代码+edit_file预览: 断言 diff 显示新增行；若省略: 预览信息不足
                self.assertEqual(target_file.read_text(encoding="utf-8"), "before\n")  # 新增代码+edit_file预览: 断言 dry_run 不写文件；若省略: 预览模式可能偷偷改文件
            finally:  # 新增代码+edit_file预览: 进入清理分支；若省略: 子进程关闭不可靠
                client.close()  # 新增代码+edit_file预览: 关闭 MCP 子进程；若省略: 测试会泄漏进程
    def test_workspace_tools_file_tools_read_write_and_create_files(self) -> None:  # 新增代码+MCP文件工具: 验证 workspace_tools 能通过 MCP 读取、覆盖写入和创建文件；若省略: 文件工具迁移到 MCP 后没有端到端保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP文件工具: 创建临时工作区隔离真实文件；若省略: 测试可能污染用户项目文件
            workspace = Path(raw_dir)  # 新增代码+MCP文件工具: 把临时目录转成 Path；若省略: 后续路径拼接不够清楚
            existing_file = workspace / "existing.txt"  # 新增代码+MCP文件工具: 准备已存在文件路径；若省略: write_file 没有覆盖写入目标
            existing_file.write_text("旧内容", encoding="utf-8")  # 新增代码+MCP文件工具: 写入初始文本；若省略: read_file 和 write_file 缺少可验证内容
            server_script = (TEST_ROOT / "workspace_tools_mcp_server.py")  # 新增代码+MCP文件工具: 定位真实 workspace_tools MCP server；若省略: 测试无法走真实协议
            config = McpServerConfig(name="workspace_tools", command=sys.executable, args=[str(server_script), str(workspace)])  # 新增代码+MCP文件工具: 构造临时工作区 server 配置；若省略: server 可能操作错误目录
            client = McpStdioClient(config)  # 新增代码+MCP文件工具: 创建 MCP client；若省略: 无法调用文件工具
            try:  # 新增代码+MCP文件工具: 确保测试结束关闭子进程；若省略: 失败时可能残留 MCP 进程
                client.start()  # 新增代码+MCP文件工具: 启动并初始化 server；若省略: tools/call 无法执行
                read_output = client.call_tool("read_file", {"path": "existing.txt"})  # 新增代码+MCP文件工具: 读取已有文件内容；若省略: 无法验证 MCP 读文件能力
                self.assertIn("旧内容", read_output)  # 新增代码+MCP文件工具: 断言读取结果包含真实内容；若省略: read_file 可能返回错误文本也不被发现
                write_output = client.call_tool("write_file", {"path": "existing.txt", "content": "新内容"})  # 新增代码+MCP文件工具: 覆盖写入已有文件；若省略: 无法验证 MCP 写文件能力
                self.assertIn("已写入", write_output)  # 新增代码+MCP文件工具: 断言写入工具报告成功；若省略: 写入失败可能被误判
                self.assertEqual(existing_file.read_text(encoding="utf-8"), "新内容")  # 新增代码+MCP文件工具: 断言文件真实被覆盖；若省略: 只看工具文本可能假阳性
                create_output = client.call_tool("create_file", {"path": "nested/new.txt", "content": "新文件"})  # 新增代码+MCP文件工具: 创建嵌套目录里的新文件；若省略: 无法验证新建文件和自动建父目录
                self.assertIn("已创建", create_output)  # 新增代码+MCP文件工具: 断言创建工具报告成功；若省略: 创建失败不会被发现
                self.assertEqual((workspace / "nested" / "new.txt").read_text(encoding="utf-8"), "新文件")  # 新增代码+MCP文件工具: 断言新文件真实存在且内容正确；若省略: create_file 可能只返回文本不落盘
            finally:  # 新增代码+MCP文件工具: 进入清理分支；若省略: 子进程关闭不可靠
                client.close()  # 新增代码+MCP文件工具: 关闭 MCP 子进程；若省略: 测试会泄漏进程
    def test_workspace_tools_file_tools_refuse_overwrite_and_missing_write(self) -> None:  # 新增代码+MCP文件工具: 验证 create_file 不覆盖已有文件且 write_file 不创建缺失文件；若省略: 文件工具可能误覆盖或误创建文件
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP文件工具: 创建临时工作区；若省略: 测试可能影响真实项目文件
            workspace = Path(raw_dir)  # 新增代码+MCP文件工具: 把临时目录转成 Path；若省略: 后续路径表达不清楚
            existing_file = workspace / "safe.txt"  # 新增代码+MCP文件工具: 准备已有文件用于覆盖保护测试；若省略: create_file 没有冲突目标
            existing_file.write_text("保留", encoding="utf-8")  # 新增代码+MCP文件工具: 写入应被保留的内容；若省略: 无法断言拒绝覆盖是否真的保护内容
            server_script = (TEST_ROOT / "workspace_tools_mcp_server.py")  # 新增代码+MCP文件工具: 定位真实 workspace_tools MCP server；若省略: 测试无法启动工具 server
            config = McpServerConfig(name="workspace_tools", command=sys.executable, args=[str(server_script), str(workspace)])  # 新增代码+MCP文件工具: 构造临时工作区 server 配置；若省略: server 会操作错误目录
            client = McpStdioClient(config)  # 新增代码+MCP文件工具: 创建 MCP client；若省略: 无法调用文件工具
            try:  # 新增代码+MCP文件工具: 确保后续关闭子进程；若省略: 测试失败会残留进程
                client.start()  # 新增代码+MCP文件工具: 启动并初始化 server；若省略: tools/call 会失败
                create_output = client.call_tool("create_file", {"path": "safe.txt", "content": "覆盖"})  # 新增代码+MCP文件工具: 尝试用创建工具覆盖已有文件；若省略: 无法验证 create_file 的安全边界
                self.assertIn("已存在", create_output)  # 新增代码+MCP文件工具: 断言工具拒绝覆盖已有文件；若省略: 覆盖保护回归不会被发现
                self.assertEqual(existing_file.read_text(encoding="utf-8"), "保留")  # 新增代码+MCP文件工具: 断言原内容没有被覆盖；若省略: 工具可能返回拒绝但实际已写
                write_output = client.call_tool("write_file", {"path": "missing.txt", "content": "内容"})  # 新增代码+MCP文件工具: 尝试覆盖写入不存在文件；若省略: 无法验证 write_file 不负责创建文件
                self.assertIn("文件不存在", write_output)  # 新增代码+MCP文件工具: 断言缺失文件写入被拒绝；若省略: write_file 可能意外创建新文件
                self.assertFalse((workspace / "missing.txt").exists())  # 新增代码+MCP文件工具: 断言缺失文件没有被创建；若省略: 副作用回归不会被发现
            finally:  # 新增代码+MCP文件工具: 进入清理分支；若省略: 子进程关闭不可靠
                client.close()  # 新增代码+MCP文件工具: 关闭 MCP 子进程；若省略: 测试会泄漏进程
    def test_workspace_tools_file_operations_copy_move_and_delete_files(self) -> None:  # 新增代码+MCP文件操作: 验证 copy_file、move_file、delete_file 的正常路径；若省略: 新增文件操作工具没有端到端保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP文件操作: 创建临时工作区隔离真实文件；若省略: 测试可能误动用户项目文件
            workspace = Path(raw_dir)  # 新增代码+MCP文件操作: 把临时目录转成 Path；若省略: 后续路径拼接不够清楚
            source_file = workspace / "source.txt"  # 新增代码+MCP文件操作: 准备复制源文件路径；若省略: copy_file 没有输入目标
            source_file.write_text("源内容", encoding="utf-8")  # 新增代码+MCP文件操作: 写入源文件内容；若省略: 无法验证复制和移动后内容是否保留
            server_script = (TEST_ROOT / "workspace_tools_mcp_server.py")  # 新增代码+MCP文件操作: 定位真实 workspace_tools MCP server；若省略: 测试无法走真实 MCP 协议
            config = McpServerConfig(name="workspace_tools", command=sys.executable, args=[str(server_script), str(workspace)])  # 新增代码+MCP文件操作: 构造临时工作区 server 配置；若省略: server 可能操作错误目录
            client = McpStdioClient(config)  # 新增代码+MCP文件操作: 创建 MCP client；若省略: 无法调用文件操作工具
            try:  # 新增代码+MCP文件操作: 确保测试结束关闭子进程；若省略: 失败时可能残留 MCP 进程
                client.start()  # 新增代码+MCP文件操作: 启动并初始化 server；若省略: tools/call 无法执行
                copy_output = client.call_tool("copy_file", {"source_path": "source.txt", "target_path": "nested/copy.txt"})  # 新增代码+MCP文件操作: 复制文件到嵌套路径；若省略: 无法验证复制和自动建父目录
                self.assertIn("已复制", copy_output)  # 新增代码+MCP文件操作: 断言复制工具报告成功；若省略: 复制失败可能不被发现
                self.assertEqual((workspace / "nested" / "copy.txt").read_text(encoding="utf-8"), "源内容")  # 新增代码+MCP文件操作: 断言复制目标内容正确；若省略: 只看工具文本可能假阳性
                self.assertTrue(source_file.exists())  # 新增代码+MCP文件操作: 断言复制不会删除源文件；若省略: copy_file 可能退化成 move 而不被发现
                move_output = client.call_tool("move_file", {"source_path": "nested/copy.txt", "target_path": "moved.txt"})  # 新增代码+MCP文件操作: 把复制结果移动到新位置；若省略: 无法验证移动文件能力
                self.assertIn("已移动", move_output)  # 新增代码+MCP文件操作: 断言移动工具报告成功；若省略: 移动失败可能不被发现
                self.assertFalse((workspace / "nested" / "copy.txt").exists())  # 新增代码+MCP文件操作: 断言移动后旧路径消失；若省略: move_file 可能只是复制而不被发现
                self.assertEqual((workspace / "moved.txt").read_text(encoding="utf-8"), "源内容")  # 新增代码+MCP文件操作: 断言移动目标内容正确；若省略: 移动可能损坏内容
                delete_output = client.call_tool("delete_file", {"path": "moved.txt", "confirm_delete": True})  # 新增代码+MCP文件操作: 显式确认删除移动后的文件；若省略: 无法验证删除工具的确认参数
                self.assertIn("已删除", delete_output)  # 新增代码+MCP文件操作: 断言删除工具报告成功；若省略: 删除失败可能不被发现
                self.assertFalse((workspace / "moved.txt").exists())  # 新增代码+MCP文件操作: 断言文件真实被删除；若省略: 只看返回文本可能假阳性
            finally:  # 新增代码+MCP文件操作: 进入清理分支；若省略: 子进程关闭不可靠
                client.close()  # 新增代码+MCP文件操作: 关闭 MCP 子进程；若省略: 测试会泄漏进程
    def test_workspace_tools_file_operations_refuse_unsafe_changes(self) -> None:  # 新增代码+MCP文件操作: 验证删除确认和默认不覆盖安全边界；若省略: 文件操作工具可能误删或误覆盖文件
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP文件操作: 创建临时工作区；若省略: 测试可能影响真实项目文件
            workspace = Path(raw_dir)  # 新增代码+MCP文件操作: 把临时目录转成 Path；若省略: 后续路径表达不清楚
            source_file = workspace / "source.txt"  # 新增代码+MCP文件操作: 准备源文件路径；若省略: copy/move 没有源文件
            target_file = workspace / "target.txt"  # 新增代码+MCP文件操作: 准备已有目标路径；若省略: 无法验证默认拒绝覆盖
            source_file.write_text("源", encoding="utf-8")  # 新增代码+MCP文件操作: 写入源文件内容；若省略: 源文件不存在会干扰覆盖测试
            target_file.write_text("保留", encoding="utf-8")  # 新增代码+MCP文件操作: 写入应被保留的目标内容；若省略: 无法确认是否发生误覆盖
            (workspace / "folder").mkdir()  # 新增代码+MCP文件操作: 创建目录用于验证 delete_file 拒绝目录；若省略: 删除目录安全边界没有测试目标
            server_script = (TEST_ROOT / "workspace_tools_mcp_server.py")  # 新增代码+MCP文件操作: 定位真实 workspace_tools MCP server；若省略: 测试无法启动真实工具 server
            config = McpServerConfig(name="workspace_tools", command=sys.executable, args=[str(server_script), str(workspace)])  # 新增代码+MCP文件操作: 构造临时工作区 server 配置；若省略: server 会操作错误目录
            client = McpStdioClient(config)  # 新增代码+MCP文件操作: 创建 MCP client；若省略: 无法调用文件操作工具
            try:  # 新增代码+MCP文件操作: 确保后续关闭子进程；若省略: 测试失败会残留进程
                client.start()  # 新增代码+MCP文件操作: 启动并初始化 server；若省略: tools/call 会失败
                delete_without_confirm = client.call_tool("delete_file", {"path": "source.txt"})  # 新增代码+MCP文件操作: 尝试不带确认参数删除；若省略: 无法验证删除确认门槛
                self.assertIn("confirm_delete=true", delete_without_confirm)  # 新增代码+MCP文件操作: 断言删除工具要求显式确认；若省略: 误删风险回归不会被发现
                self.assertTrue(source_file.exists())  # 新增代码+MCP文件操作: 断言未确认删除不会动文件；若省略: 工具可能返回拒绝但实际已删
                delete_directory = client.call_tool("delete_file", {"path": "folder", "confirm_delete": True})  # 新增代码+MCP文件操作: 尝试删除目录；若省略: 删除目录安全边界没有执行验证
                self.assertIn("不是文件", delete_directory)  # 新增代码+MCP文件操作: 断言 delete_file 拒绝目录；若省略: 工具可能递归删除目录而不被发现
                copy_conflict = client.call_tool("copy_file", {"source_path": "source.txt", "target_path": "target.txt"})  # 新增代码+MCP文件操作: 尝试复制到已有目标；若省略: 无法验证复制默认不覆盖
                self.assertIn("目标已存在", copy_conflict)  # 新增代码+MCP文件操作: 断言复制拒绝覆盖已有目标；若省略: 覆盖保护回归不会被发现
                self.assertEqual(target_file.read_text(encoding="utf-8"), "保留")  # 新增代码+MCP文件操作: 断言复制冲突没有改目标内容；若省略: 工具可能返回拒绝但实际覆盖
                move_conflict = client.call_tool("move_file", {"source_path": "source.txt", "target_path": "target.txt"})  # 新增代码+MCP文件操作: 尝试移动到已有目标；若省略: 无法验证移动默认不覆盖
                self.assertIn("目标已存在", move_conflict)  # 新增代码+MCP文件操作: 断言移动拒绝覆盖已有目标；若省略: 覆盖保护回归不会被发现
                self.assertTrue(source_file.exists())  # 新增代码+MCP文件操作: 断言移动冲突后源文件仍在；若省略: move_file 可能误删源文件
                self.assertEqual(target_file.read_text(encoding="utf-8"), "保留")  # 新增代码+MCP文件操作: 断言移动冲突没有改目标内容；若省略: 目标可能被误覆盖
            finally:  # 新增代码+MCP文件操作: 进入清理分支；若省略: 子进程关闭不可靠
                client.close()  # 新增代码+MCP文件操作: 关闭 MCP 子进程；若省略: 测试会泄漏进程
    def test_default_mcp_config_enables_workspace_tools_server(self) -> None:  # 新增代码+workspace_tools: 验证真实 mcp_servers.json 默认启用 workspace_tools；若省略: 新 server 可能存在但用户启动 agent 时看不到
        configs = load_mcp_server_configs(TEST_ROOT)  # 新增代码+workspace_tools: 读取项目真实 MCP 配置；若省略: 测试无法覆盖 CLI 启动会加载的文件
        names = [config.name for config in configs]  # 新增代码+workspace_tools: 提取 server 名称列表便于断言；若省略: 后续断言需要重复访问对象字段
        self.assertIn("browser_search", names)  # 新增代码+workspace_tools: 保留原有浏览器搜索 server 作为回归断言；若省略: 修改配置时可能误删已有联网能力
        self.assertIn("workspace_tools", names)  # 新增代码+workspace_tools: 断言新增工作区工具 server 会被加载；若省略: agent 仍只能搜索网页不能像 Claude Code 一样探索本地项目
    def test_default_mcp_config_enables_browser_automation_server(self) -> None:  # 新增代码+BrowserAutomation: 验证默认 MCP 配置启用浏览器自动化 server；若省略: server 实现后用户启动 agent 仍可能看不到该能力
        configs = load_mcp_server_configs(TEST_ROOT)  # 新增代码+BrowserAutomation: 读取 learning_agent 目录下真实默认 MCP 配置；若省略: 测试无法覆盖实际启动入口会加载的配置
        names = [config.name for config in configs]  # 新增代码+BrowserAutomation: 提取 server 名称列表用于断言；若省略: 后续检查需要重复访问配置对象
        self.assertIn("browser_automation", names)  # 新增代码+BrowserAutomation: 断言默认配置注册 browser_automation；若省略: 配置缺失不会在红灯阶段暴露
    def test_readme_explains_browser_automation_mcp_boundaries(self) -> None:  # 新增代码+BrowserAutomation文档: 验证 README 说明安装、工具清单和安全边界；若省略: 用户可能不知道如何启用真实浏览器 MCP
        readme_text = (TEST_ROOT / "README.md").read_text(encoding="utf-8")  # 新增代码+BrowserAutomation文档: 读取真实 README.md；若省略: 测试无法覆盖交付给用户阅读的文档
        self.assertIn("browser_automation", readme_text)  # 新增代码+BrowserAutomation文档: 断言 README 提到新 MCP server 名称；若省略: 用户可能找不到配置入口
        self.assertIn("python -m pip install playwright", readme_text)  # 新增代码+BrowserAutomation文档: 断言 README 给出 Playwright Python 包安装命令；若省略: 用户不知道先装哪个依赖
        self.assertIn("playwright install chromium", readme_text)  # 新增代码+BrowserAutomation文档: 断言 README 给出 Chromium 安装命令关键字符串；若省略: 用户可能只装包而没有浏览器内核
        self.assertIn("browser_open", readme_text)  # 新增代码+BrowserAutomation文档: 断言 README 列出打开页面工具；若省略: 工具清单不完整
        self.assertIn("browser_snapshot", readme_text)  # 新增代码+BrowserAutomation文档: 断言 README 列出页面快照工具；若省略: 用户不知道如何观察页面
        self.assertIn("browser_type", readme_text)  # 新增代码+BrowserAutomation文档: 断言 README 示例或清单包含输入工具；若省略: 表单流程说明不完整
        self.assertIn("browser_click", readme_text)  # 新增代码+BrowserAutomation文档: 断言 README 示例或清单包含点击工具；若省略: 交互流程说明不完整
        self.assertIn("browser_wait", readme_text)  # 新增代码+BrowserAutomation文档: 断言 README 示例或清单包含等待工具；若省略: 页面变化等待边界不清楚
        self.assertIn("browser_screenshot", readme_text)  # 新增代码+BrowserAutomation文档: 断言 README 示例或清单包含截图工具；若省略: 视觉证据产物说明不完整
        self.assertIn("browser_evaluate", readme_text)  # 新增代码+BrowserAutomation文档: 断言 README 点名 JS 执行工具；若省略: 高风险能力可能被隐藏
        self.assertIn("browser_artifacts", readme_text)  # 新增代码+BrowserAutomation文档: 断言 README 说明 artifact 目录；若省略: 截图和下载文件位置不透明
        self.assertIn("真实 Chrome", readme_text)  # 修改代码+BrowserAutomation文档: 断言 README 说明默认仍优先独立 Chromium，真实 Chrome 登录态已是可选高风险模式且必须用户确认 confirm_real_profile=true；若省略: 用户可能误解成默认继承登录态或无需确认
    def test_runtime_instructions_mentions_workspace_tools_usage(self) -> None:  # 新增代码+workspace_tools: 验证运行规则会引导模型使用本地工作区工具；若省略: 工具存在但模型可能不知道何时调用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+workspace_tools: 定位真实运行时规则文件；若省略: 测试无法覆盖模型实际会读到的规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+workspace_tools: 用 UTF-8 读取中文规则；若省略: Windows 默认编码可能导致中文断言不稳定
        self.assertIn("list_dir", runtime_text)  # 新增代码+workspace_tools: 断言规则提到目录列表工具；若省略: 模型可能继续不知道如何枚举目录
        self.assertIn("glob", runtime_text)  # 新增代码+workspace_tools: 断言规则提到文件模式搜索工具；若省略: 模型可能不用更高效的文件发现工具
        self.assertIn("grep", runtime_text)  # 新增代码+workspace_tools: 断言规则提到内容搜索工具；若省略: 模型可能不知道可搜索代码内容
        self.assertIn("mcp__workspace_tools__read_file", runtime_text)  # 新增代码+MCP文件工具: 断言规则提醒模型用 MCP 版读文件；若省略: 模型可能继续优先使用内置读文件通道
        self.assertIn("mcp__workspace_tools__write_file", runtime_text)  # 新增代码+MCP文件工具: 断言规则提醒模型用 MCP 版写文件；若省略: 模型可能不知道已有文件可走 workspace_tools 覆盖写入
        self.assertIn("mcp__workspace_tools__create_file", runtime_text)  # 新增代码+MCP文件工具: 断言规则提醒模型用 MCP 版创建文件；若省略: 模型可能用错误工具覆盖新文件
        self.assertIn("mcp__workspace_tools__copy_file", runtime_text)  # 新增代码+MCP文件操作: 断言规则提醒模型用 MCP 版复制文件；若省略: 模型可能不知道复制文件能力
        self.assertIn("mcp__workspace_tools__move_file", runtime_text)  # 新增代码+MCP文件操作: 断言规则提醒模型用 MCP 版移动文件；若省略: 模型可能不知道移动或重命名文件能力
        self.assertIn("mcp__workspace_tools__delete_file", runtime_text)  # 新增代码+MCP文件操作: 断言规则提醒模型用 MCP 版删除文件；若省略: 模型可能不知道删除必须走受控工具
        self.assertIn("confirm_delete", runtime_text)  # 新增代码+MCP文件操作: 断言规则强调删除确认参数；若省略: 模型可能遗漏删除安全门槛
        self.assertIn("风险等级", runtime_text)  # 新增代码+权限分级: 断言运行规则提醒模型和用户工具授权会显示风险等级；若省略: 权限分级文档可能被误删而不被测试发现
        self.assertIn("run_powershell", runtime_text)  # 新增代码+workspace_tools: 断言规则提到命令执行工具；若省略: 模型可能无法主动请求验证命令
        self.assertIn("edit_file", runtime_text)  # 新增代码+edit_file: 断言规则提到精确编辑工具；若省略: 模型可能仍只会搜索和读取，不会请求受控修改
        self.assertIn("edits", runtime_text)  # 新增代码+edit_file批量编辑: 断言规则提醒模型多处修改用 edits；若省略: 工具支持批量但模型可能不会主动使用
        self.assertIn("dry_run", runtime_text)  # 新增代码+edit_file预览: 断言规则提醒模型不确定时先预览；若省略: agent 可能直接写文件而缺少审阅步骤
    def test_runtime_instructions_mentions_mcp_tools_when_present(self) -> None:  # 新增代码+MCP文档说明: 验证真实 runtime_instructions.md 会提醒模型优先请求 MCP 外部工具；若省略: 运行时规则可能遗漏 MCP 接入边界而不被发现
        runtime_file = self._dynamic_prompt_file()  # 新增代码+MCP文档说明: 定位与测试文件同目录的真实运行时规则文件；若省略: 测试无法读取项目实际交给模型的规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+MCP文档说明: 用 UTF-8 读取中文规则文本；若省略: 断言没有可检查的运行时规则内容且 Windows 编码可能误判
        self.assertIn("MCP", runtime_text)  # 新增代码+MCP文档说明: 断言规则明确提到 MCP；若省略: 模型可能不知道外部能力应通过 MCP 工具接入
        self.assertIn("外部工具", runtime_text)  # 新增代码+MCP文档说明: 断言规则明确提到外部工具边界；若省略: 浏览器、搜索、数据库等外部能力可能被模型假装已连接
    def test_readme_explains_mcp_browser_boundaries(self) -> None:  # 新增代码+MCP浏览器边界说明: 验证 README 讲清示例配置、Playwright 依赖和模型不能直接操作网页；若省略: 文档回归会让初学者误以为示例文件自动启用 MCP 或模型能直接点网页
        readme_file = (TEST_ROOT / "README.md")  # 新增代码+MCP浏览器边界说明: 定位真实 README 文档；若省略: 测试无法覆盖用户实际阅读的说明文件
        readme_text = readme_file.read_text(encoding="utf-8")  # 新增代码+MCP浏览器边界说明: 用 UTF-8 读取中文 README；若省略: Windows 默认编码可能导致中文关键词读取失败
        self.assertIn("mcp_servers.example.json", readme_text)  # 新增代码+MCP浏览器边界说明: 断言 README 提到示例配置文件；若省略: 示例配置入口可能被误删而不被发现
        self.assertIn("不会被自动读取", readme_text)  # 新增代码+MCP浏览器边界说明: 断言 README 说明 example 文件不会自动生效；若省略: 初学者可能误以为放着示例文件就启用了 MCP
        self.assertIn("mcp_servers.json", readme_text)  # 新增代码+MCP浏览器边界说明: 断言 README 提到真正会生效的配置文件名；若省略: 用户可能不知道该复制成哪个文件
        self.assertIn("browser_automation", readme_text)  # 修改代码+MCP浏览器边界说明: 断言 README 提到当前 Python Playwright 浏览器自动化 server；若省略: 旧 Node/npx 路线可能重新误导用户
        self.assertIn("playwright install chromium", readme_text)  # 修改代码+MCP浏览器边界说明: 断言 README 提到当前 Chromium 安装命令；若省略: 用户可能不知道第一阶段依赖 Python Playwright 浏览器内核
        self.assertIn("真实 Chrome 登录态", readme_text)  # 修改代码+MCP浏览器边界说明: 断言 README 说明真实 Chrome 登录态已经是第一版可选高风险模式，且必须用户明确确认 confirm_real_profile=true；若省略: 用户可能误以为默认会继承本机 Chrome 登录或绕过确认门槛
        self.assertIn("模型本身仍然不能直接操作网页", readme_text)  # 新增代码+MCP浏览器边界说明: 断言 README 明确模型与网页操作的边界；若省略: 用户可能误解模型已经拥有直接浏览器控制权
        self.assertIn("MCP server", readme_text)  # 新增代码+MCP浏览器边界说明: 断言 README 说明真实执行者是 MCP server；若省略: 工具层职责可能不清楚
        self.assertIn("权限确认", readme_text)  # 新增代码+MCP浏览器边界说明: 断言 README 保留外部工具权限约束；若省略: 外部操作安全边界可能被误读
    def test_readme_explains_mcp_http_transport_boundaries(self) -> None:  # 新增代码+MCPTransport: 验证 README 讲清 HTTP/SSE transport 配置和边界；若省略: 初学者不知道远程 MCP 应该怎么写配置
        readme_file = (TEST_ROOT / "README.md")  # 新增代码+MCPTransport: 定位真实 README 文档；若省略: 文档测试无法读取用户会看的文件
        readme_text = readme_file.read_text(encoding="utf-8")  # 新增代码+MCPTransport: 用 UTF-8 读取 README；若省略: 中文关键词可能受系统编码影响
        self.assertIn("transport", readme_text)  # 新增代码+MCPTransport: 断言文档提到 transport 字段；若省略: 用户可能仍以为只有 command/args
        self.assertIn("http", readme_text)  # 新增代码+MCPTransport: 断言文档提到 HTTP transport；若省略: 远程 Streamable HTTP 配置入口不明显
        self.assertIn("url", readme_text)  # 新增代码+MCPTransport: 断言文档提到 URL 字段；若省略: 用户不知道远程 endpoint 写在哪里
        self.assertIn("headers", readme_text)  # 新增代码+MCPTransport: 断言文档提到自定义 headers；若省略: 需要鉴权的 MCP server 无配置线索
        self.assertIn("SSE", readme_text)  # 新增代码+MCPTransport: 断言文档提到旧 SSE 边界；若省略: 用户可能误以为 legacy SSE 已完整支持
    def test_readme_explains_mcp_http_session_stream_lifecycle(self) -> None:  # 新增代码+HTTP流生命周期文档: 验证 README 讲清 HTTP 会话流生命周期；若省略: 文档可能只讲配置而不讲 GET/DELETE/续传边界
        readme_file = (TEST_ROOT / "README.md")  # 新增代码+HTTP流生命周期文档: 定位用户实际阅读的 learning_agent README；若省略: 测试可能检查不到真实文档
        readme_text = readme_file.read_text(encoding="utf-8")  # 新增代码+HTTP流生命周期文档: 用 UTF-8 读取中文文档；若省略: Windows 默认编码可能导致中文断言乱码
        self.assertIn("GET", readme_text)  # 新增代码+HTTP流生命周期文档: 断言 README 提到 GET 监听流；若省略: 用户不知道 POST 之外还有监听入口
        self.assertIn("Last-Event-ID", readme_text)  # 新增代码+HTTP流生命周期文档: 断言 README 提到 SSE 续传游标；若省略: 用户不知道断线恢复依赖哪个 header
        self.assertIn("DELETE", readme_text)  # 新增代码+HTTP流生命周期文档: 断言 README 提到会话关闭请求；若省略: 用户不知道如何释放远程 session
        self.assertIn("有界", readme_text)  # 新增代码+HTTP流生命周期文档: 断言 README 说明监听是有限边界；若省略: 用户可能以为 agent 会无限常驻监听
    def test_readme_explains_mcp_auth_metadata_boundaries(self) -> None:  # 新增代码+MCPAuthMetadata: 验证 README 讲清 MCP 鉴权 metadata 和 authenticate 边界；若省略: 初学者可能把登录能力误解为完整 OAuth UI
        readme_file = (TEST_ROOT / "README.md")  # 新增代码+MCPAuthMetadata: 定位真实 README 文档；若省略: 文档测试无法读取用户会看的文件
        readme_text = readme_file.read_text(encoding="utf-8")  # 新增代码+MCPAuthMetadata: 用 UTF-8 读取 README；若省略: 中文关键词可能受系统编码影响
        self.assertIn("mcp__server__authenticate", readme_text)  # 新增代码+MCPAuthMetadata: 断言文档说明伪 authenticate 工具命名；若省略: 用户不知道模型会看到什么工具入口
        self.assertIn("WWW-Authenticate", readme_text)  # 新增代码+MCPAuthMetadata: 断言文档提到 401 鉴权 header；若省略: 用户不知道 auth metadata 从哪里来
        self.assertIn("resource_metadata", readme_text)  # 新增代码+MCPAuthMetadata: 断言文档提到受保护资源 metadata 字段；若省略: 用户无法理解 OAuth 发现入口
        self.assertIn("Authorization", readme_text)  # 新增代码+MCPAuthMetadata: 断言文档提示使用 Authorization header；若省略: token 配置位置不清楚
        self.assertIn("不会自动", readme_text)  # 新增代码+MCPAuthMetadata: 断言文档说明不会自动完成 OAuth；若省略: 用户可能以为 agent 会自动打开任意授权 URL
    def test_builtin_tools_include_mcp_prompt_tools(self) -> None:  # 新增代码+MCPPrompt: 验证内置工具列表暴露 MCP prompt 发现和读取工具；若省略: 模型可能永远看不到 MCP prompts 能力
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+MCPPrompt: 从内置工具 schema 中收集工具名；若省略: 无法判断模型可见工具是否包含 prompt 工具
        self.assertIn("list_mcp_prompts", tool_names)  # 新增代码+MCPPrompt: 断言模型可以请求列出 MCP prompts；若省略: agent 无法发现 MCP server 暴露的提示词
        self.assertIn("read_mcp_prompt", tool_names)  # 新增代码+MCPPrompt: 断言模型可以请求读取 MCP prompt；若省略: agent 即使发现 prompt 也无法加载正文
    def test_builtin_tools_include_mcp_resource_tools(self) -> None:  # 新增代码+MCPResource: 验证内置工具列表暴露 MCP resources 列表和读取工具；若省略: 模型无法主动请求读取 MCP 资源
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+MCPResource: 收集真实内置工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("list_mcp_resources", tool_names)  # 新增代码+MCPResource: 断言模型可以请求列出 MCP resources；若省略: resources/list 缺失不会被测试发现
        self.assertIn("read_mcp_resource", tool_names)  # 新增代码+MCPResource: 断言模型可以请求读取 MCP resource；若省略: resources/read 缺失不会被测试发现
    def test_task_child_agent_can_inherit_allowed_mcp_tool(self) -> None:  # 新增代码+TaskAgent: 验证子 agent 能继承父 agent 已启动且被 allowed_tools 允许的 MCP 工具；若省略: 子 agent 只能用内置工具而无法接近 Claude Code 的外部工具委派
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TaskAgent: 创建临时工作区隔离 MCP 和日志测试；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+TaskAgent: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            fake_client = FakeMcpClient(tools=[{"name": "weather_lookup", "description": "Search current weather information", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}}])  # 新增代码+TaskAgent: 构造一个可被子 agent 继承的 MCP 工具；若省略: 无法验证 MCP 工具继承
            registry = McpToolRegistry({"weather": fake_client})  # 新增代码+TaskAgent: 创建带 weather server 的 MCP registry；若省略: 主 agent 没有外部工具来源
            model = RecordingToolNameFakeModel(ModelMessage(text="子任务完成：已经确认可用天气工具。"))  # 新增代码+TaskAgent: 创建记录子 agent 可见工具的假模型；若省略: 无法观察子 agent 是否看见 MCP 工具
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+TaskAgent: 创建会启动 MCP registry 的主 agent；若省略: 子 agent 没有已启动 MCP 状态可继承
            self._select_tool_for_test(agent, "mcp__weather__weather_lookup")  # 新增代码+ToolArchitectureV2: 先在父 agent 中加载天气 MCP 工具；若没有这行代码，子 agent 不能继承尚未进入 Tool Pool 的 deferred 工具
            output = agent._execute_tool(ToolCall(name="task", arguments={"prompt": "检查天气查询工具是否可用", "allowed_tools": ["mcp__weather__weather_lookup"], "max_turns": 1}))  # 新增代码+TaskAgent: 启动只允许天气 MCP 工具的子 agent；若省略: 无法验证 allowed_tools 对 MCP 工具生效
            self.assertIn("task 成功", output)  # 新增代码+TaskAgent: 断言 task 返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertEqual(len(model.received_tool_names), 1)  # 新增代码+TaskAgent: 断言子 agent 调用模型一次；若省略: 无法确认 task 确实执行子 agent
            self.assertIn("mcp__weather__weather_lookup", model.received_tool_names[0])  # 新增代码+TaskAgent: 断言允许的 MCP 工具暴露给子 agent；若省略: MCP 工具继承退化不会被发现
            self.assertNotIn("read_file", model.received_tool_names[0])  # 新增代码+TaskAgent: 断言未列入 allowed_tools 的内置工具不暴露；若省略: 子 agent 工具范围可能过宽
    def test_child_agent_inherits_policy_denials_for_allowed_mcp_tools(self) -> None:  # 新增代码+ToolPolicyV2: 验证子 agent 会继承父 agent 的 deny 策略；若没有这行代码，父 agent 禁掉的 MCP 工具可能在子 agent 中重新暴露
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolPolicyV2: 创建临时工作区来隔离本测试文件和日志；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolPolicyV2: 把临时目录转换为 Path 对象给 agent 使用；若没有这行代码，后续构造 agent 的路径语义不够清楚
            fake_client = FakeMcpClient()  # 新增代码+ToolPolicyV2: 创建默认 echo MCP 假客户端作为可被继承的外部工具；若没有这行代码，测试没有目标 MCP 工具可加载
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+ToolPolicyV2: 注册 demo MCP server 让 mcp__demo__echo 出现在工具目录；若没有这行代码，父 agent 无法 select 目标工具
            model = RecordingToolNameFakeModel(ModelMessage(text="子任务完成：已检查工具池。"))  # 新增代码+ToolPolicyV2: 使用会记录子 agent 模型工具池的假模型；若没有这行代码，测试无法观察子 agent 实际看到了哪些工具
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+ToolPolicyV2: 创建父 agent 并允许启动 MCP；若没有这行代码，无法执行父子 agent 继承流程
            self._select_tool_for_test(agent, "mcp__demo__echo")  # 新增代码+ToolPolicyV2: 父 agent 先加载 echo MCP 工具；若没有这行代码，测试无法覆盖 loaded_tool_names 继承再被 policy 过滤的场景
            agent.tool_policy_context.deny_rules.append(ToolPolicyRule(tool_name="mcp__demo__echo"))  # 新增代码+ToolPolicyV2: 父 agent 后续添加针对 echo 工具的 deny rule；若没有这行代码，子 agent 没有需要继承的拒绝策略
            captured_child_agents: list[LearningAgent] = []  # 新增代码+ToolPolicyV2: 保存 task 内部创建出的子 agent 供测试检查策略上下文；若没有这行代码，测试只能看输出而无法证明 deny_rules 被复制
            def capture_child_run(child_self: LearningAgent, child_prompt: str, max_turns: int | None = None) -> str:  # 新增代码+ToolPolicyV2: 替代子 agent run 来观察真实 child_agent 状态；若没有这行代码，红灯可能被父侧 allowed_tools 过滤掩盖
                del child_prompt, max_turns  # 新增代码+ToolPolicyV2: 明确本测试不依赖 prompt 和轮次参数；若没有这行代码，未使用参数会让测试意图不够清楚
                captured_child_agents.append(child_self)  # 新增代码+ToolPolicyV2: 记录 _task 构造出的子 agent 实例；若没有这行代码，后续无法断言 policy context 是否继承
                child_tool_names = [schema["function"]["name"] for schema in child_self._available_tool_schemas()]  # 新增代码+ToolPolicyV2: 读取子 agent 自己过滤后的模型工具池；若没有这行代码，测试无法确认 loaded_tool_names 继承仍受子 policy 过滤
                model.received_tool_names.append(child_tool_names)  # 新增代码+ToolPolicyV2: 复用记录模型的字段保存子工具池快照；若没有这行代码，后续 NotIn 断言没有稳定观察点
                return "子任务完成：已检查工具池。"  # 新增代码+ToolPolicyV2: 返回固定子任务结果让 task 走成功路径；若没有这行代码，主 agent 会把子任务视为失败
            with mock.patch.object(LearningAgent, "run", autospec=True, side_effect=capture_child_run):  # 新增代码+ToolPolicyV2: 只在本测试中拦截子 agent run 并捕获 child_agent；若没有这行代码，测试无法直接验证继承字段
                output = agent._execute_tool(ToolCall(name="task", arguments={"prompt": "检查工具池", "allowed_tools": ["mcp__demo__echo"], "max_turns": 1}))  # 新增代码+ToolPolicyV2: 启动只允许 echo MCP 工具的子 agent；若没有这行代码，继承过滤逻辑不会真正运行
            self.assertIn("task 成功", output)  # 新增代码+ToolPolicyV2: 断言子任务正常完成而不是因为工具限制崩溃；若没有这行代码，后续工具池断言可能来自失败路径
            self.assertEqual(len(captured_child_agents), 1)  # 新增代码+ToolPolicyV2: 断言确实捕获到一个子 agent；若没有这行代码，继承断言可能没有真实对象可检查
            inherited_deny_tool_names = [rule.tool_name for rule in captured_child_agents[0].tool_policy_context.deny_rules]  # 新增代码+ToolPolicyV2: 提取子 agent 继承到的 deny 工具名；若没有这行代码，无法清楚判断父策略是否传给子任务
            self.assertIn("mcp__demo__echo", inherited_deny_tool_names)  # 新增代码+ToolPolicyV2: 断言子 agent 的 policy context 含有父 agent 的 echo deny rule；若没有这行代码，真正的继承缺失不会被发现
            self.assertIn("mcp__demo__echo", captured_child_agents[0].loaded_tool_names)  # 新增代码+ToolPolicyV2: 断言已加载 MCP 工具名仍继承进子 agent；若没有这行代码，NotIn 可能只是 allowed_tools 被父侧提前清空造成的假通过
            self.assertEqual(len(model.received_tool_names), 1)  # 新增代码+ToolPolicyV2: 断言子 agent 确实调用了一次模型并记录工具池；若没有这行代码，空记录会让 NotIn 断言失去意义
            self.assertNotIn("mcp__demo__echo", model.received_tool_names[0])  # 新增代码+ToolPolicyV2: 断言父 agent deny 的 MCP 工具没有暴露给子 agent 模型；若没有这行代码，子 agent 绕过父策略不会被发现
    def test_agent_searches_builtin_and_mcp_tools(self) -> None:  # 新增代码+ToolSearch: 验证 tool_search 同时搜索内置工具和已启动 MCP 工具；若省略: 后续只搜内置或只搜 MCP 的退化不会被发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolSearch: 创建临时工作区隔离 memory/debug 文件；若省略: 测试可能污染真实 learning_agent 工作区
            workspace = Path(raw_dir)  # 新增代码+ToolSearch: 把临时路径转成 Path；若省略: 后续构造 agent 和写文件不够清晰
            fake_client = FakeMcpClient(tools=[{"name": "weather_lookup", "description": "Search current weather information", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}}])  # 新增代码+ToolSearch: 构造一个含天气搜索语义的 MCP 工具；若省略: 测试无法确认 tool_search 会搜索外部工具
            registry = McpToolRegistry({"weather": fake_client})  # 新增代码+ToolSearch: 创建带 weather server 的 MCP registry；若省略: agent 没有 MCP 工具来源
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+ToolSearch: 创建允许启动 MCP 的 agent；若省略: tool_search 无法看到已启动 MCP 工具
            output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "weather", "max_results": 5}))  # 新增代码+ToolSearch: 请求按 weather 关键词搜索工具；若省略: 无法验证 tool_search 执行分发和搜索结果
            self.assertIn("tool_search 成功", output)  # 新增代码+ToolSearch: 断言工具搜索返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("mcp__weather__weather_lookup", output)  # 新增代码+ToolSearch: 断言 MCP 工具被搜索到；若省略: 外部工具发现能力可能退化
            self.assertIn("Search current weather information", output)  # 新增代码+ToolSearch: 断言 MCP 工具说明进入结果；若省略: 模型即使看到名字也缺少选择依据
            self.assertIn("query", output)  # 新增代码+ToolSearch: 断言参数名会展示给模型；若省略: 模型找到工具后仍可能不知道如何传参
    def test_agent_lists_and_reads_mcp_resources_with_permission(self) -> None:  # 新增代码+MCPResource: 验证 agent 通过内置工具列出和读取 MCP resources 且请求权限；若省略: 最上层工具分发缺口不会被发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCPResource: 创建临时工作区隔离 agent 文件；若省略: 测试可能污染真实 memory 或日志
            workspace = Path(raw_dir)  # 新增代码+MCPResource: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            permissions: list[str] = []  # 新增代码+MCPResource: 准备记录权限提示文本；若省略: 无法断言 resources 操作经过权限层
            fake_client = FakeMcpClient(resources=[{"uri": "file://guide.md", "name": "Guide", "mimeType": "text/markdown", "description": "Project guide"}], resource_text="guide body")  # 新增代码+MCPResource: 创建含 resource 的 fake MCP client；若省略: agent 没有可列出的资源
            registry = McpToolRegistry({"docs": fake_client})  # 新增代码+MCPResource: 创建带 docs server 的 registry；若省略: agent 无法通过 MCP registry 获取 resources
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: permissions.append(action) or True, mcp_tool_registry=registry)  # 新增代码+MCPResource: 创建允许 MCP 启动和操作的 agent；若省略: _execute_tool 没有真实运行环境
            listed = agent._execute_tool(ToolCall(name="list_mcp_resources", arguments={"max_results": 5}))  # 新增代码+MCPResource: 通过 agent 工具路由列出 resources；若省略: 无法验证 list_mcp_resources 分发
            self.assertIn("list_mcp_resources 成功", listed)  # 新增代码+MCPResource: 断言列资源工具返回成功前缀；若省略: 未知工具输出可能被后续断言误判
            self.assertIn("docs", listed)  # 新增代码+MCPResource: 断言结果显示 server 名；若省略: 模型后续读取时缺少 server
            self.assertIn("file://guide.md", listed)  # 新增代码+MCPResource: 断言结果显示 uri；若省略: 模型不知道要读哪个资源
            read = agent._execute_tool(ToolCall(name="read_mcp_resource", arguments={"server": "docs", "uri": "file://guide.md", "max_chars": 2000}))  # 新增代码+MCPResource: 通过 agent 工具路由读取 resource；若省略: 无法验证 read_mcp_resource 分发
            self.assertIn("read_mcp_resource 成功", read)  # 新增代码+MCPResource: 断言读取工具返回成功前缀；若省略: MCP 读取失败可能被内容断言掩盖
            self.assertIn("guide body: file://guide.md", read)  # 新增代码+MCPResource: 断言资源正文进入工具结果；若省略: 模型拿不到 resource 内容不会暴露
            self.assertTrue(any("列出 MCP resources" in action for action in permissions))  # 新增代码+MCPResource: 断言列资源经过权限确认；若省略: 外部资源枚举可能绕过用户同意
            self.assertTrue(any("读取 MCP resource" in action for action in permissions))  # 新增代码+MCPResource: 断言读资源经过权限确认；若省略: 外部资源读取可能绕过用户同意
    def test_listen_mcp_stream_tool_schema_is_available(self) -> None:  # 新增代码+MCPStream: 验证内置工具列表暴露 listen_mcp_stream；若省略: 模型可能永远看不到监听 MCP stream 的入口
        schema_by_name = {schema["function"]["name"]: schema for schema in TOOL_SCHEMAS}  # 新增代码+MCPStream: 把工具 schema 按名称索引；若省略: 测试需要手写循环且更容易漏判工具名
        self.assertIn("listen_mcp_stream", schema_by_name)  # 新增代码+MCPStream: 断言 listen_mcp_stream 已注册；若省略: 只实现 wrapper 但忘记暴露给模型不会失败
        properties = schema_by_name["listen_mcp_stream"]["function"]["parameters"]["properties"]  # 新增代码+MCPStream: 取出工具参数定义；若省略: 无法继续确认模型能传入哪些参数
        self.assertIn("server", properties)  # 新增代码+MCPStream: 断言 server 参数存在；若省略: 模型无法指定要监听哪个 MCP server
        self.assertIn("max_events", properties)  # 新增代码+MCPStream: 断言 max_events 参数存在；若省略: 模型无法控制最多读取多少条事件
        self.assertIn("timeout_seconds", properties)  # 新增代码+MCPStream: 断言 timeout_seconds 参数存在；若省略: 模型无法控制监听等待时间
        self.assertIn("resume", properties)  # 新增代码+MCPStream: 断言 resume 参数存在；若省略: 模型无法选择是否带 session 续传信息
    def test_listen_mcp_stream_wrapper_validates_server(self) -> None:  # 新增代码+MCPStream: 验证 wrapper 会先检查 server 参数；若省略: 空 server 可能进入 registry 并返回难懂错误
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCPStream: 创建临时工作区隔离 agent 文件；若省略: 测试可能污染真实 memory 或日志
            workspace = Path(raw_dir)  # 新增代码+MCPStream: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+MCPStream: 创建测试 agent；若省略: 无法直接调用 listen_mcp_stream wrapper
            output = agent._listen_mcp_stream({})  # 新增代码+MCPStream: 直接传空参数触发缺 server 分支；若省略: wrapper 参数校验没有测试输入
            self.assertIn("缺少 server", output)  # 新增代码+MCPStream: 断言返回清楚的缺参提示；若省略: wrapper 可能抛异常或给出模糊错误
    def test_listen_mcp_stream_execute_tool_dispatch_validates_server(self) -> None:  # 新增代码+MCPStream: 验证 _execute_tool 会分发 listen_mcp_stream；若省略: 只实现 wrapper 但忘记分发不会失败
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCPStream: 创建临时工作区隔离 agent 文件；若省略: 测试可能污染真实 memory 或日志
            workspace = Path(raw_dir)  # 新增代码+MCPStream: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+MCPStream: 创建测试 agent；若省略: 无法通过工具路由执行 listen_mcp_stream
            output = agent._execute_tool(ToolCall(name="listen_mcp_stream", arguments={}))  # 新增代码+MCPStream: 通过统一工具分发触发缺 server 分支；若省略: 分发路径没有测试输入
            self.assertIn("缺少 server", output)  # 新增代码+MCPStream: 断言分发路径也返回缺参提示；若省略: 未知工具或错误分支可能被漏掉
    def test_listen_mcp_stream_falls_back_for_non_finite_limits(self) -> None:  # 新增代码+MCPStream: 验证 inf/nan 等非有限限制值会回退默认值；若省略: 裸异常回归不会被测试发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCPStream: 创建临时工作区隔离 agent 文件；若省略: 测试可能污染真实 memory 或日志
            workspace = Path(raw_dir)  # 新增代码+MCPStream: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            permission_actions: list[str] = []  # 新增代码+MCPStream: 保存权限确认文本用于断言参数已回退；若省略: 只能知道没崩溃而不能证明兜底值正确
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: permission_actions.append(action) or True)  # 新增代码+MCPStream: 创建记录权限且允许执行的 agent；若省略: 无法观察 listen_mcp_stream 的权限 action
            output = agent._listen_mcp_stream({"server": "demo", "max_events": float("inf"), "timeout_seconds": float("nan"), "resume": "off"})  # 新增代码+MCPStream: 传入非有限 max_events/timeout_seconds 和字符串 off；若省略: 无法复现本次裸异常和 resume 转换场景
            self.assertTrue("listen_mcp_stream 失败" in output or "未知 MCP server" in output)  # 新增代码+MCPStream: 断言工具返回可读失败而不是抛裸异常；若省略: 测试无法表达允许 registry 层未知 server 的结果
            self.assertTrue(permission_actions)  # 新增代码+MCPStream: 断言已经走到权限确认阶段；若省略: 参数解析提前崩溃可能被后续字符串断言误读
            action = permission_actions[-1]  # 新增代码+MCPStream: 取最后一次权限文本用于检查实际监听参数；若省略: 后续断言没有目标字符串
            self.assertIn('"max_events": 5', action)  # 新增代码+MCPStream: 断言 inf 回退默认 5；若省略: 非有限事件数可能继续流入 registry
            self.assertIn('"timeout_seconds": 2.0', action)  # 新增代码+MCPStream: 断言 nan 回退默认 2.0；若省略: 非有限超时可能继续流入 registry
            self.assertIn('"resume": false', action)  # 新增代码+MCPStream: 断言字符串 off 被转换成 false；若省略: resume 字符串兼容规则可能退化
    def test_agent_lists_and_reads_mcp_prompts_with_permission(self) -> None:  # 新增代码+MCPPrompt: 验证 agent 通过内置工具列出和读取 MCP prompts 且请求权限；若省略: 最上层 prompt 工具分发缺口不会被发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCPPrompt: 创建临时工作区隔离 agent 文件；若省略: 测试可能污染真实 memory 或日志
            workspace = Path(raw_dir)  # 新增代码+MCPPrompt: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            permissions: list[str] = []  # 新增代码+MCPPrompt: 准备记录权限提示文本；若省略: 无法断言 prompts 操作经过权限层
            fake_client = FakeMcpClient(prompts=[{"name": "plan_brief", "description": "Create a bounded plan brief", "arguments": [{"name": "topic", "required": True}]}], prompt_text="prompt body")  # 新增代码+MCPPrompt: 创建含 prompt 的 fake MCP client；若省略: agent 没有可列出的 prompt
            registry = McpToolRegistry({"docs": fake_client})  # 新增代码+MCPPrompt: 创建带 docs server 的 registry；若省略: agent 无法通过 MCP registry 获取 prompts
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: permissions.append(action) or True, mcp_tool_registry=registry)  # 新增代码+MCPPrompt: 创建允许 MCP 启动和操作的 agent；若省略: _execute_tool 没有真实运行环境
            listed = agent._execute_tool(ToolCall(name="list_mcp_prompts", arguments={"max_results": 5}))  # 新增代码+MCPPrompt: 通过 agent 工具路由列出 prompts；若省略: 无法验证 list_mcp_prompts 分发
            self.assertIn("list_mcp_prompts 成功", listed)  # 新增代码+MCPPrompt: 断言列 prompt 工具返回成功前缀；若省略: 未知工具输出可能被后续断言误判
            self.assertIn("docs", listed)  # 新增代码+MCPPrompt: 断言结果显示 server 名；若省略: 模型后续读取时缺少 server
            self.assertIn("plan_brief", listed)  # 新增代码+MCPPrompt: 断言结果显示 prompt 名；若省略: 模型不知道要读哪个 prompt
            self.assertIn("topic(必填)", listed)  # 新增代码+MCPPrompt: 断言结果显示 prompt 参数需求；若省略: 模型不知道要传哪些 prompt_arguments
            read = agent._execute_tool(ToolCall(name="read_mcp_prompt", arguments={"server": "docs", "name": "plan_brief", "prompt_arguments": {"topic": "MCP"}, "max_chars": 2000}))  # 新增代码+MCPPrompt: 通过 agent 工具路由读取 prompt；若省略: 无法验证 read_mcp_prompt 分发
            self.assertIn("read_mcp_prompt 成功", read)  # 新增代码+MCPPrompt: 断言读取工具返回成功前缀；若省略: MCP 读取失败可能被内容断言掩盖
            self.assertIn("prompt body: plan_brief MCP", read)  # 新增代码+MCPPrompt: 断言 prompt 正文进入工具结果；若省略: 模型拿不到 prompt 内容不会暴露
            self.assertTrue(any("列出 MCP prompts" in action for action in permissions))  # 新增代码+MCPPrompt: 断言列 prompts 经过权限确认；若省略: 外部 prompt 枚举可能绕过用户同意
            self.assertTrue(any("读取 MCP prompt" in action for action in permissions))  # 新增代码+MCPPrompt: 断言读 prompt 经过权限确认；若省略: 外部 prompt 读取可能绕过用户同意
    def test_runtime_instructions_mentions_mcp_resource_tools(self) -> None:  # 新增代码+MCPResource: 验证运行规则会引导模型列出和读取 MCP resources；若省略: 工具存在但模型可能不知道何时使用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+MCPResource: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+MCPResource: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("list_mcp_resources", runtime_text)  # 新增代码+MCPResource: 断言规则提到资源列表工具；若省略: 模型不知道先列出 MCP resources
        self.assertIn("read_mcp_resource", runtime_text)  # 新增代码+MCPResource: 断言规则提到资源读取工具；若省略: 模型不知道如何读取具体资源
        self.assertIn("resources", runtime_text)  # 新增代码+MCPResource: 断言规则保留 MCP resources 语义词；若省略: 只有工具名不足以说明用途
    def test_runtime_instructions_mentions_mcp_prompt_tools(self) -> None:  # 新增代码+MCPPrompt: 验证运行规则会引导模型列出和读取 MCP prompts；若省略: 工具存在但模型可能不知道何时使用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+MCPPrompt: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+MCPPrompt: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("list_mcp_prompts", runtime_text)  # 新增代码+MCPPrompt: 断言规则提到 prompt 列表工具；若省略: 模型不知道先列出 MCP prompts
        self.assertIn("read_mcp_prompt", runtime_text)  # 新增代码+MCPPrompt: 断言规则提到 prompt 读取工具；若省略: 模型不知道如何读取具体 prompt
        self.assertIn("prompts", runtime_text)  # 新增代码+MCPPrompt: 断言规则保留 MCP prompts 语义词；若省略: 只有工具名不足以说明用途
    def test_runtime_instructions_mentions_mcp_http_transport(self) -> None:  # 新增代码+MCPTransport: 验证运行规则讲清 MCP HTTP/SSE transport 边界；若省略: 模型可能误用旧 SSE 或不知道远程 MCP 可用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+MCPTransport: 定位真实 runtime_instructions.md；若省略: 测试无法覆盖 agent 实际加载的说明
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+MCPTransport: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("Streamable HTTP", runtime_text)  # 新增代码+MCPTransport: 断言规则提到当前推荐 HTTP transport；若省略: 模型不知道远程 MCP 的主路径
        self.assertIn("transport=http", runtime_text)  # 新增代码+MCPTransport: 断言规则给出明确配置写法；若省略: 模型可能自造配置字段
        self.assertIn("SSE", runtime_text)  # 新增代码+MCPTransport: 断言规则提到旧 SSE 边界；若省略: 模型可能误以为 legacy SSE 已完整可用
    def test_runtime_instructions_mentions_mcp_http_session_stream_lifecycle(self) -> None:  # 新增代码+HTTP流生命周期文档: 验证运行规则提醒模型 HTTP 会话流生命周期；若省略: 模型可能不知道 GET 续传和 DELETE 清理边界
        runtime_file = self._dynamic_prompt_file()  # 新增代码+HTTP流生命周期文档: 定位 agent 实际加载的 runtime_instructions；若省略: 文档断言可能检查错文件
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+HTTP流生命周期文档: 用 UTF-8 读取中文运行规则；若省略: 中文关键词可能受系统编码影响
        self.assertIn("GET", runtime_text)  # 新增代码+HTTP流生命周期文档: 断言运行规则提到 GET 监听流；若省略: 模型可能只知道 POST 请求
        self.assertIn("Last-Event-ID", runtime_text)  # 新增代码+HTTP流生命周期文档: 断言运行规则提到续传 header；若省略: 模型不知道恢复监听要带哪个游标
        self.assertIn("DELETE", runtime_text)  # 新增代码+HTTP流生命周期文档: 断言运行规则提到关闭 session；若省略: 模型可能忘记释放远程会话
        self.assertIn("不会后台常驻监听", runtime_text)  # 新增代码+HTTP流生命周期文档: 断言运行规则说明监听不是后台常驻；若省略: 模型可能误报一直在监听
    def test_runtime_instructions_mentions_mcp_auth_metadata(self) -> None:  # 新增代码+MCPAuthMetadata: 验证运行规则讲清 MCP auth metadata 和 authenticate 工具边界；若省略: 模型可能遇到 401 后乱猜登录流程
        runtime_file = self._dynamic_prompt_file()  # 新增代码+MCPAuthMetadata: 定位真实 runtime_instructions.md；若省略: 测试无法覆盖 agent 实际加载的说明
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+MCPAuthMetadata: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("mcp__server__authenticate", runtime_text)  # 新增代码+MCPAuthMetadata: 断言规则提到伪 authenticate 工具；若省略: 模型不知道 401 后的恢复入口
        self.assertIn("WWW-Authenticate", runtime_text)  # 新增代码+MCPAuthMetadata: 断言规则提到鉴权挑战 header；若省略: 模型无法解释 auth metadata 来源
        self.assertIn("resource_metadata", runtime_text)  # 新增代码+MCPAuthMetadata: 断言规则提到 metadata 字段；若省略: 模型不知道 OAuth 发现信息名称
        self.assertIn("Authorization", runtime_text)  # 新增代码+MCPAuthMetadata: 断言规则提醒使用 Authorization header；若省略: 模型可能建议把 token 放到 URL


if __name__ == "__main__":  # Stage14: allow running this test module directly.
    unittest.main()  # Stage14: start unittest when executed as a script.


