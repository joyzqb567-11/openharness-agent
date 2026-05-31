"Tool catalog, tool policy, atom tool, and output protocol tests."  # Stage14: this file owns the tools_policy test group.
from __future__ import annotations  # Stage14: keep annotations lazy after test split.
import unittest  # Stage14: keep direct unittest execution available.
from learning_agent.tests.support import *  # Stage14: import shared helpers and dependencies for copied tests.

class ToolsPolicyTests(LearningAgentTestBase):  # Stage14: unittest discovers this concrete modular test class.
    def test_real_browser_customer_task_auto_approves_public_query_tools(self) -> None:  # 新增代码+真实浏览器客户模式: 验证真实浏览器公开查询白名单工具不会再弹权限；若没有这行代码，用户仍会被每个点击输入动作打断
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+真实浏览器客户模式: 创建临时工作区隔离 memory/debug 文件；若没有这行代码，测试会污染项目目录
            browser_tools = [  # 新增代码+真实浏览器客户模式: 构造只含白名单工具的 fake browser MCP 工具集；若没有这行代码，测试无法模拟真实浏览器动作
                {"name": "browser_profile_status", "description": "Read Chrome profile status", "inputSchema": {"type": "object", "properties": {}}},  # 新增代码+真实浏览器客户模式: 提供只读状态工具；若没有这行代码，auto approve 无法覆盖第一步
                {"name": "browser_type", "description": "Type visible text", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}},  # 新增代码+真实浏览器客户模式: 提供输入工具；若没有这行代码，进度提示无法覆盖拟人输入动作
            ]  # 新增代码+真实浏览器客户模式: 结束 fake 工具列表；若没有这行代码，Python 列表语法不完整
            fake_client = FakeMcpClient(tools=browser_tools)  # 新增代码+真实浏览器客户模式: 创建 fake MCP client；若没有这行代码，registry 没有可调用目标
            registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+真实浏览器客户模式: 用 browser_automation server 名模拟真实工具前缀；若没有这行代码，工具名不会匹配生产白名单
            permission_requests: list[str] = []  # 新增代码+真实浏览器客户模式: 记录权限回调被调用的次数；若没有这行代码，无法证明工具动作没有弹窗
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=Path(raw_dir), ask_permission=lambda action: permission_requests.append(action) or True, mcp_tool_registry=registry)  # 新增代码+真实浏览器客户模式: 创建允许启动 MCP 的 agent；若没有这行代码，MCP 工具无法进入可调用状态
            agent.real_chrome_requested = True  # 新增代码+真实浏览器客户模式: 模拟本轮用户明确要求真实浏览器；若没有这行代码，自动授权不能确认这是目标场景
            agent.real_browser_information_task_requested = True  # 新增代码+真实浏览器客户模式: 模拟本轮属于公开信息查询任务；若没有这行代码，普通浏览器动作不会被客户模式放行
            before_tool_permissions = list(permission_requests)  # 新增代码+真实浏览器客户模式: 保存启动阶段权限快照；若没有这行代码，后续无法区分启动 MCP 和工具调用权限
            with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:  # 新增代码+真实浏览器客户模式: 捕获客户可见进度文本；若没有这行代码，无法验证 agent 展示下一步操作
                status_output = agent._execute_mcp_tool(ToolCall(name="mcp__browser_automation__browser_profile_status", arguments={}))  # 新增代码+真实浏览器客户模式: 执行白名单只读状态工具；若没有这行代码，无法证明第一个浏览器动作不弹 y
                type_output = agent._execute_mcp_tool(ToolCall(name="mcp__browser_automation__browser_type", arguments={"text": "重庆 2026-05-31 天气 旅游攻略"}))  # 新增代码+真实浏览器客户模式: 执行白名单输入工具；若没有这行代码，无法证明拟人输入不弹 y
            self.assertIn("called browser_profile_status", status_output)  # 新增代码+真实浏览器客户模式: 断言工具实际执行而不是只跳过权限；若没有这行代码，自动授权可能没有调用外部工具
            self.assertIn("called browser_type", type_output)  # 新增代码+真实浏览器客户模式: 断言输入工具实际执行；若没有这行代码，进度提示可能掩盖工具未运行
            self.assertEqual(permission_requests, before_tool_permissions)  # 新增代码+真实浏览器客户模式: 断言白名单工具没有新增权限请求；若没有这行代码，客户体验中的 y 提示可能回归
            self.assertIn("正在检查真实 Chrome 状态", fake_stdout.getvalue())  # 新增代码+真实浏览器客户模式: 断言状态工具显示人类可读进度；若没有这行代码，用户不知道 agent 正在检查什么
            self.assertIn("正在输入搜索词", fake_stdout.getvalue())  # 新增代码+真实浏览器客户模式: 断言输入工具显示人类可读进度；若没有这行代码，用户看不到 agent 思考和操作下一步
            self.assertIn("permission_auto_approved", json.dumps(agent.mcp_call_progress_events, ensure_ascii=False))  # 新增代码+真实浏览器客户模式: 断言内部进度记录自动授权；若没有这行代码，审计无法证明为什么没弹权限
    def test_real_browser_customer_task_does_not_auto_approve_sensitive_tools(self) -> None:  # 新增代码+真实浏览器客户模式: 验证敏感浏览器工具即使在客户模式也不会默认放行；若没有这行代码，取消 y 提示可能误伤隐私边界
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+真实浏览器客户模式: 创建临时工作区隔离测试副作用；若没有这行代码，测试会污染真实项目文件
            fake_client = FakeMcpClient(tools=[{"name": "browser_evaluate", "description": "Run JavaScript", "inputSchema": {"type": "object", "properties": {"script": {"type": "string"}}}}])  # 新增代码+真实浏览器客户模式: 构造敏感 JS 执行工具；若没有这行代码，测试无法覆盖拒绝边界
            registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+真实浏览器客户模式: 使用 browser_automation server 名触发浏览器工具分类；若没有这行代码，工具名不会贴近生产场景
            permission_requests: list[str] = []  # 新增代码+真实浏览器客户模式: 记录权限请求文本；若没有这行代码，无法证明敏感工具仍进入权限层
            def permission_callback(action: str) -> bool:  # 新增代码+真实浏览器客户模式: 定义只允许启动 MCP、拒绝具体敏感工具的回调；若没有这行代码，测试无法区分启动和执行阶段
                permission_requests.append(action)  # 新增代码+真实浏览器客户模式: 保存每次权限动作；若没有这行代码，后续断言没有输入
                return action.startswith("启动 MCP server")  # 新增代码+真实浏览器客户模式: 启动 MCP 放行但工具调用拒绝；若没有这行代码，敏感工具可能真的执行
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=Path(raw_dir), ask_permission=permission_callback, mcp_tool_registry=registry)  # 新增代码+真实浏览器客户模式: 创建带敏感工具的 agent；若没有这行代码，无法调用 _execute_mcp_tool
            agent.real_chrome_requested = True  # 新增代码+真实浏览器客户模式: 模拟真实浏览器任务；若没有这行代码，测试不能证明客户模式边界
            agent.real_browser_information_task_requested = True  # 新增代码+真实浏览器客户模式: 模拟公开信息查询任务；若没有这行代码，敏感拒绝不在目标模式下验证
            output = agent._execute_mcp_tool(ToolCall(name="mcp__browser_automation__browser_evaluate", arguments={"script": "window.localStorage"}))  # 新增代码+真实浏览器客户模式: 尝试执行敏感 JS 工具；若没有这行代码，敏感工具自动授权边界不会被测试
            self.assertIn("用户拒绝了操作", output)  # 新增代码+真实浏览器客户模式: 断言敏感工具仍会被拒绝；若没有这行代码，自动授权越界可能不被发现
            self.assertIn("调用 MCP 工具：mcp__browser_automation__browser_evaluate", permission_requests[-1])  # 新增代码+真实浏览器客户模式: 断言敏感工具仍进入权限提示；若没有这行代码，工具可能被静默放行或静默拦截
            self.assertEqual(fake_client.calls, [])  # 新增代码+真实浏览器客户模式: 断言拒绝后没有真正调用外部工具；若没有这行代码，隐私边界可能只是在文本上拒绝
    def test_prompt_surface_report_tool_lists_loaded_prompt_blocks(self) -> None:  # 新增代码+PromptArchitectureV1: 验证 prompt_surface_report 工具会列出本轮加载的提示词块；若没有这行代码，报告工具缺失或漏列块不会被发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PromptArchitectureV1: 创建临时工作区隔离真实项目文件；若没有这行代码，测试可能读取用户当前项目状态导致不稳定
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="ok")]), workspace=Path(raw_dir), ask_permission=lambda action: True)  # 新增代码+PromptArchitectureV1: 创建带假模型的真实 agent；若没有这行代码，无法调用真实提示词装配和工具分发逻辑
            agent._build_initial_messages("请报告当前提示词")  # 新增代码+PromptArchitectureV1: 先构造本轮消息以刷新 last_prompt_surface_report；若没有这行代码，报告工具只能看到空报告
            output = agent._execute_tool(ToolCall(name="prompt_surface_report", arguments={"include_block_text": False}))  # 新增代码+PromptArchitectureV1: 调用只读报告工具且不要求输出完整正文；若没有这行代码，测试无法验证工具真实输出
            self.assertIn("prompt.kernel.identity", output)  # 新增代码+PromptArchitectureV1: 断言核心身份块出现在报告中；若没有这行代码，基础 prompt block 漏报不会失败
            self.assertNotIn("context.dynamic_prompt_index", output)  # 修改代码+PromptFiles: 断言 dynamicprompt 索引不再作为每轮静态 block 自动加载；若没有这行代码，动态规则可能重新挤进 system prompt
            self.assertIn("历史设计文档", output)  # 新增代码+PromptArchitectureV1: 断言报告明确说明历史设计文档不会自动加载；若没有这行代码，用户可能误以为旧文档仍影响模型
            self.assertNotIn("完整设计文档全文", output)  # 新增代码+PromptArchitectureV1: 断言默认不泄露完整提示词正文；若没有这行代码，include_block_text=false 的边界可能回归失效
    def test_token_budget_report_tool_includes_prompt_and_tool_pool_budget(self) -> None:  # 新增代码+PromptArchitectureV1: 验证 token_budget_report 同时展示提示词预算和工具池预算；若没有这行代码，预算报告缺项不会被发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PromptArchitectureV1: 创建临时工作区隔离真实文件；若没有这行代码，测试会依赖当前用户项目状态
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="ok")]), workspace=Path(raw_dir), ask_permission=lambda action: True)  # 新增代码+PromptArchitectureV1: 创建带假模型的真实 agent；若没有这行代码，无法读取真实当前工具池
            agent._build_initial_messages("继续")  # 新增代码+PromptArchitectureV1: 先刷新提示词表面报告；若没有这行代码，预算报告的 prompt blocks 数据为空
            output = agent._execute_tool(ToolCall(name="token_budget_report", arguments={}))  # 新增代码+PromptArchitectureV1: 调用预算报告工具并使用 include_tools 默认值；若没有这行代码，测试无法验证默认会列出工具池
            self.assertIn("Prompt blocks", output)  # 新增代码+PromptArchitectureV1: 断言报告包含提示词块预算区域；若没有这行代码，prompt 预算丢失不会失败
            self.assertIn("Current Tool Pool", output)  # 新增代码+PromptArchitectureV1: 断言报告包含当前工具池区域；若没有这行代码，工具 schema 预算丢失不会失败
            self.assertIn("estimated_total_tokens", output)  # 新增代码+PromptArchitectureV1: 断言报告包含总 token 粗估字段；若没有这行代码，总量缺失不会失败
    def test_context_assembler_keeps_builtin_policy_blocks_full_under_tiny_budget(self) -> None:  # 新增代码+PromptArchitectureV1: 验证极低预算也不会压缩内置核心策略块；若没有这行代码，核心系统规则可能被误压缩而不被测试发现
        registry = build_default_prompt_registry()  # 新增代码+PromptArchitectureV1: 使用真实默认注册表拿到 built_in 策略块元数据；若没有这行代码，测试无法覆盖生产排序和来源标记
        assembler = ContextAssembler(registry, soft_token_limit=10)  # 新增代码+PromptArchitectureV1: 设置极低预算复现审查指出的误压缩风险；若没有这行代码，旧实现不会暴露核心策略被压缩的问题
        result = assembler.assemble_static_blocks({  # 新增代码+PromptArchitectureV1: 只传入内置策略块让动态候选为空；若没有这行代码，测试无法证明核心块本身不会被 compact
            "prompt.policy.response": "回复策略必须完整保留\n" * 500,  # 新增代码+PromptArchitectureV1: 构造超长回复策略块；若没有这行代码，低优先级 built_in 被压缩的风险没有样本
            "prompt.policy.tool_boundary": "工具边界必须完整保留\n" * 500,  # 新增代码+PromptArchitectureV1: 构造超长工具边界块；若没有这行代码，工具使用硬规则被摘要化的风险没有样本
        })  # 新增代码+PromptArchitectureV1: 结束内置策略输入字典；若没有这行代码，Python 语法不完整
        loaded_by_id = {block.block_id: block for block in result.loaded_blocks}  # 新增代码+PromptArchitectureV1: 按 block_id 建索引方便精确检查状态；若没有这行代码，测试只能依赖脆弱列表位置
        self.assertFalse(result.compacted)  # 新增代码+PromptArchitectureV1: 断言没有动态候选时不压缩 built_in 核心策略；若没有这行代码，误压缩核心规则不会导致测试失败
        self.assertNotIn("Compact Summary", result.system_prompt)  # 新增代码+PromptArchitectureV1: 断言系统提示词里没有核心策略摘要；若没有这行代码，模型仍可能只看到被压缩的硬规则
        self.assertEqual(loaded_by_id["prompt.policy.response"].status, "loaded")  # 新增代码+PromptArchitectureV1: 断言回复策略保持完整加载状态；若没有这行代码，报告状态退化不会被发现
        self.assertEqual(loaded_by_id["prompt.policy.tool_boundary"].status, "loaded")  # 新增代码+PromptArchitectureV1: 断言工具边界保持完整加载状态；若没有这行代码，工具硬边界被摘要化不会被发现
    def test_agent_tool_catalog_wraps_builtin_tools_with_metadata(self) -> None:  # 新增代码+ToolArchitectureV2: 验证内置工具会进入 AgentTool 目录；若没有这行代码，v2 可能仍停留在裸 schema 列表
        catalog = build_builtin_tool_catalog()  # 新增代码+ToolArchitectureV2: 调用待实现的内置工具目录构建函数；若没有这行代码，测试无法驱动新架构入口
        by_name = {tool.name: tool for tool in catalog}  # 新增代码+ToolArchitectureV2: 按工具名索引目录；若没有这行代码，后续断言需要重复遍历
        self.assertEqual(len(catalog), len(TOOL_SCHEMAS))  # 新增代码+ToolArchitectureV2: 断言内置 catalog 没有漏掉旧工具；若没有这行代码，后续迁移可能静默丢失某个内置工具
        self.assertIn("read", by_name)  # 修改代码+极简工具面: 断言四原子读取工具进入完整目录；若没有这行代码，首轮工具入口可能缺少读取 skill 和代码的能力
        self.assertTrue(by_name["read"].always_load)  # 修改代码+极简工具面: 断言 read 是首轮常驻工具；若没有这行代码，模型可能无法读取 tool_list.md 来发现后续能力
        self.assertFalse(by_name["read"].should_defer)  # 修改代码+极简工具面: 断言 read 不延迟加载；若没有这行代码，极简入口会被自己锁在门外
        self.assertIn("tool_search", by_name)  # 修改代码+极简工具面: 断言旧搜索工具仍保留在内部目录用于兼容；若没有这行代码，旧测试或迁移路径可能找不到内部能力
        self.assertTrue(by_name["tool_search"].should_defer)  # 修改代码+极简工具面: 断言旧搜索工具不再首轮暴露；若没有这行代码，首轮 schema 可能回退到旧的工具搜索入口
        self.assertTrue(by_name["skill_load"].should_defer)  # 修改代码+极简工具面: 断言旧 skill_load 不再首轮暴露；若没有这行代码，skill 读取会继续消耗独立工具 schema
        self.assertEqual(by_name["read_file"].capability_pack, "file_operations")  # 新增代码+CapabilityPacks: 断言读文件工具被归入文件能力包；若没有这行代码，tool_search 无法按能力包批量加载文件工具
        self.assertTrue(by_name["read_file"].should_defer)  # 修改代码+CapabilityPacks: 断言普通文件工具默认延迟加载；若没有这行代码，首轮工具 schema 会继续膨胀
        self.assertIn("read_file", by_name)  # 新增代码+ToolArchitectureV2: 断言普通内置工具仍进入目录；若没有这行代码，v2 可能误删已有能力
        self.assertEqual(by_name["read_file"].input_schema["type"], "object")  # 新增代码+ToolArchitectureV2: 断言保留原工具参数 schema；若没有这行代码，模型输出参数会失去约束
    def test_tools_package_exports_agent_tool_and_catalog_builder(self) -> None:  # 新增代码+ToolsSplit: 验证工具层新模块导出 AgentTool 和 catalog builder；若没有这行代码，阶段 5 拆分可能只改主入口而没有稳定模块边界
        from learning_agent.tools.catalog import build_builtin_tool_catalog as split_build_builtin_tool_catalog  # 新增代码+ToolsSplit: 从新 catalog 模块导入构建函数；若没有这行代码，无法证明 tools/catalog.py 可被外部 agent 复用
        from learning_agent.tools.pool import current_tool_pool as split_current_tool_pool  # 新增代码+ToolsPoolSplit: 从新 pool 模块导入工具池过滤函数；若没有这行代码，无法证明当前工具池逻辑已经有稳定模块边界
        from learning_agent.tools.policy import ToolPolicy as SplitToolPolicy  # 新增代码+ToolsPoolSplit: 从新 tools.policy 入口导入策略类；若没有这行代码，外部 agent 不知道策略层新入口是否可用
        from learning_agent.tools.types import AgentTool as SplitAgentTool  # 新增代码+ToolsSplit: 从新 types 模块导入 AgentTool；若没有这行代码，无法证明工具元数据类型已经脱离主入口
        catalog = split_build_builtin_tool_catalog()  # 新增代码+ToolsSplit: 调用新模块构建内置工具目录；若没有这行代码，测试只验证导入不验证实际目录可用
        self.assertGreater(len(catalog), 0)  # 新增代码+ToolsSplit: 断言新模块目录不是空壳；若没有这行代码，空实现也可能通过导入测试
        self.assertIs(catalog[0].__class__, SplitAgentTool)  # 新增代码+ToolsSplit: 断言目录元素使用新模块的 AgentTool 类型；若没有这行代码，旧入口和新模块类型可能不一致
        self.assertIs(SplitAgentTool, type(build_builtin_tool_catalog()[0]))  # 新增代码+ToolsSplit: 断言旧入口重导出和新模块类型保持一致；若没有这行代码，兼容导入可能悄悄分裂成两套类型
        self.assertGreater(len(split_current_tool_pool(catalog, lambda tool: SplitToolPolicy.decide(tool, ToolPolicyContext(), loaded=tool.always_load))), 0)  # 新增代码+ToolsPoolSplit: 验证新 pool helper 能按策略产出当前工具池；若没有这行代码，pool.py 可能只是可导入但不可用
    def test_initial_tool_pool_only_exposes_kernel_tools(self) -> None:  # 新增代码+CapabilityPacks: 验证首轮工具池只暴露内核入口；若没有这行代码，47 个内置工具可能再次全部进入模型上下文
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CapabilityPacks: 创建临时工作区隔离本测试的 memory 和 debug 文件；若没有这行代码，测试会污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+CapabilityPacks: 把临时目录转换为 Path；若没有这行代码，后续路径拼接和 agent 初始化不够稳定
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+CapabilityPacks: 创建无 MCP 的 agent 以检查纯内置首轮工具池；若没有这行代码，测试没有执行主体
            tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+CapabilityPacks: 读取当前真正会传给模型的工具名；若没有这行代码，无法证明首轮 schema 是否缩小
            self.assertEqual(sorted(tool_names), ["bash", "edit", "read", "write"])  # 修改代码+极简工具面: 断言首轮模型只看到四个原子工具；若没有这行代码，旧 tool_search/skill_load 体系可能重新占用首轮 schema
            self.assertNotIn("tool_search", tool_names)  # 修改代码+极简工具面: 断言工具搜索不再作为模型首轮工具暴露；若没有这行代码，首轮工具数会从 4 个回退到 5 个以上
            self.assertNotIn("skill_load", tool_names)  # 修改代码+极简工具面: 断言 skill 加载不再作为首轮工具暴露；若没有这行代码，技能读取会继续消耗独立工具 schema
            self.assertNotIn("read_file", tool_names)  # 新增代码+CapabilityPacks: 断言读文件工具不再首轮暴露；若没有这行代码，文件工具会继续占用首轮 schema
            self.assertNotIn("task", tool_names)  # 新增代码+CapabilityPacks: 断言子 agent 工具不再首轮暴露；若没有这行代码，低频复杂工具会继续撑大上下文
    def test_static_prompt_routes_skills_through_readable_tool_list(self) -> None:  # 新增代码+极简工具面: 验证静态提示词只告诉模型读取技能索引；若没有这行代码，旧 tool_search 路由可能重新写回每轮提示词
        prompt_text = self._static_prompt_file().read_text(encoding="utf-8")  # 新增代码+极简工具面: 读取真实静态提示词文件；若没有这行代码，测试无法约束用户每轮实际看到的提示词入口
        self.assertIn("learning_agent/skills/tool_list.md", prompt_text)  # 新增代码+极简工具面: 断言静态提示词指向可用 read 工具读取的技能索引；若没有这行代码，模型可能不知道技能清单在哪里
        self.assertIn("read / write / edit / bash", prompt_text)  # 新增代码+极简工具面: 断言静态提示词明确四个原子工具；若没有这行代码，模型可能继续寻找旧工具入口
        self.assertNotIn("tool_search", prompt_text)  # 新增代码+极简工具面: 断言静态提示词不再推荐旧工具搜索；若没有这行代码，每轮提示词仍会牵引模型走旧路线
        self.assertNotIn("skill_load", prompt_text)  # 新增代码+极简工具面: 断言静态提示词不再推荐旧 skill_load；若没有这行代码，模型会以为还有独立技能加载工具
        self.assertNotIn("select_pack", prompt_text)  # 新增代码+极简工具面: 断言静态提示词不再推荐能力包选择语法；若没有这行代码，旧能力包体系会继续污染首轮注意力
    def test_dynamic_prompt_is_lean_four_atom_rule_file(self) -> None:  # 新增代码+极简工具面: 验证动态提示词变成四原子工具的轻规则文件；若没有这行代码，dynamicprompt 可能继续膨胀成旧工具大全
        runtime_text = self._dynamic_prompt_file().read_text(encoding="utf-8")  # 新增代码+极简工具面: 读取真实 dynamicprompt 文件；若没有这行代码，测试无法约束按需加载的动态规则正文
        self.assertIn("read / write / edit / bash", runtime_text)  # 新增代码+极简工具面: 断言动态规则围绕四个原子工具展开；若没有这行代码，模型按需读取后仍可能不知道当前工具边界
        self.assertIn("tool_list.md", runtime_text)  # 新增代码+极简工具面: 断言动态规则也指向技能索引；若没有这行代码，按需规则和静态规则会出现两个入口
        self.assertNotIn("tool_search", runtime_text)  # 新增代码+极简工具面: 断言动态规则不再要求模型调用旧工具搜索；若没有这行代码，dynamicprompt 会继续放大旧架构
        self.assertNotIn("select_pack", runtime_text)  # 新增代码+极简工具面: 断言动态规则不再要求能力包选择语法；若没有这行代码，按需提示词仍会引导模型加载工具包 schema
    def test_packaged_skill_tool_list_exists_for_read_based_discovery(self) -> None:  # 新增代码+极简工具面: 验证包内技能索引文件存在；若没有这行代码，模型只能靠猜路径发现技能
        tool_list_path = (TEST_ROOT / "skills") / "tool_list.md"  # 新增代码+极简工具面: 定位 learning_agent/skills/tool_list.md；若没有这行代码，测试无法检查新技能索引入口
        self.assertTrue(tool_list_path.is_file())  # 新增代码+极简工具面: 断言技能索引是可读取文件；若没有这行代码，静态提示词指向的路径可能不存在
        tool_list_text = tool_list_path.read_text(encoding="utf-8")  # 新增代码+极简工具面: 读取技能索引正文；若没有这行代码，测试只能检查存在性不能检查内容是否有用
        self.assertIn("read", tool_list_text)  # 新增代码+极简工具面: 断言索引说明读取原子工具；若没有这行代码，模型看索引后仍可能不知道如何加载技能正文
        self.assertIn("file_operations/SKILL.md", tool_list_text)  # 新增代码+极简工具面: 断言索引列出已有文件能力 skill；若没有这行代码，最常见代码任务缺少技能路径
        self.assertNotIn("select_pack", tool_list_text)  # 新增代码+极简工具面: 断言索引不再依赖旧能力包选择语法；若没有这行代码，技能发现文件会把旧工具架构带回来
    def test_read_atom_enforces_dynamic_prompt_parent_layers(self) -> None:  # 新增代码+动态提示词分层: 验证 read 工具会阻止模型跳过父层直接读子规则；若没有这行代码，分层只靠提示词约定无法防止上下文膨胀
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+动态提示词分层: 创建临时工作区隔离门控测试文件；若没有这行代码，测试可能改到真实项目提示词
            workspace = Path(raw_dir)  # 新增代码+动态提示词分层: 把临时目录转换成 Path；若没有这行代码，后续路径拼接会不清楚
            rules_dir = workspace / "learning_agent" / "skills" / "mcp" / "rules"  # 新增代码+动态提示词分层: 构造第三层 rules 目录；若没有这行代码，无法复现子规则读取场景
            rules_dir.mkdir(parents=True)  # 新增代码+动态提示词分层: 创建嵌套规则目录；若没有这行代码，写入子规则文件会失败
            tool_list = workspace / "learning_agent" / "skills" / "tool_list.md"  # 新增代码+动态提示词分层: 定义第一层总索引路径；若没有这行代码，门控无法测试先读索引
            skill_file = workspace / "learning_agent" / "skills" / "mcp" / "SKILL.md"  # 新增代码+动态提示词分层: 定义第二层 skill 路径；若没有这行代码，门控无法测试先读父 skill
            rule_file = rules_dir / "auth.md"  # 新增代码+动态提示词分层: 定义第三层子规则路径；若没有这行代码，测试没有目标子规则
            tool_list.write_text("- mcp：learning_agent/skills/mcp/SKILL.md\n", encoding="utf-8")  # 新增代码+动态提示词分层: 写入最小总索引；若没有这行代码，第一层读取没有真实文件
            skill_file.write_text("# MCP\n子规则：learning_agent/skills/mcp/rules/auth.md\n", encoding="utf-8")  # 新增代码+动态提示词分层: 写入最小父 skill；若没有这行代码，第二层读取没有真实文件
            rule_file.write_text("# Auth Rule\n鉴权细节\n", encoding="utf-8")  # 新增代码+动态提示词分层: 写入最小子规则；若没有这行代码，第三层成功读取没有可断言内容
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+动态提示词分层: 创建使用四原子工具的测试 agent；若没有这行代码，无法通过真实 read 工具验证门控
            direct_rule_output = agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/mcp/rules/auth.md"}))  # 新增代码+动态提示词分层: 直接读取第三层子规则；若没有这行代码，无法证明跳层会被拦截
            self.assertIn("需要先读取 learning_agent/skills/tool_list.md", direct_rule_output)  # 新增代码+动态提示词分层: 断言未读总索引时会被要求回到第一层；若没有这行代码，模型可能直接把大量子规则塞进上下文
            tool_list_output = agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/tool_list.md"}))  # 新增代码+动态提示词分层: 正常读取第一层总索引；若没有这行代码，后续无法验证门控状态前进
            self.assertIn("mcp", tool_list_output)  # 新增代码+动态提示词分层: 断言第一层索引读取成功；若没有这行代码，后续失败可能其实来自文件没读到
            early_rule_output = agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/mcp/rules/auth.md"}))  # 新增代码+动态提示词分层: 读完总索引后再次尝试跳过父 skill；若没有这行代码，无法验证第二层门控
            self.assertIn("需要先读取 learning_agent/skills/mcp/SKILL.md", early_rule_output)  # 新增代码+动态提示词分层: 断言子规则必须等父 skill 读取后才开放；若没有这行代码，第二层说明会被绕过
            skill_output = agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/mcp/SKILL.md"}))  # 新增代码+动态提示词分层: 正常读取第二层父 skill；若没有这行代码，后续无法进入第三层
            self.assertIn("auth.md", skill_output)  # 新增代码+动态提示词分层: 断言父 skill 读取成功且指向子规则；若没有这行代码，最终成功读取可能没有父层依据
            final_rule_output = agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/mcp/rules/auth.md"}))  # 新增代码+动态提示词分层: 父层就绪后读取第三层子规则；若没有这行代码，无法证明门控不是永久拒绝
            self.assertIn("鉴权细节", final_rule_output)  # 新增代码+动态提示词分层: 断言第三层规则在正确顺序下可以读取；若没有这行代码，分层会变成不可用的死门控
    def test_read_atom_accepts_project_style_skill_path_inside_package_workspace(self) -> None:  # 新增代码+路径兼容: 验证 CLI 工作区为 learning_agent 目录时也能读取静态提示词推荐的 learning_agent/skills 路径；若没有这行代码，真实 CLI 提示词会引导模型读一个不存在的双层路径
        workspace = TEST_ROOT  # 新增代码+路径兼容: 使用 learning_agent 包目录模拟 main() 默认工作区；若没有这行代码，测试无法覆盖真实 CLI 入口路径
        agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+路径兼容: 创建不写调试日志的最小 agent；若没有这行代码，无法通过真实 read 工具验证路径兼容
        output = agent._execute_tool(ToolCall(name="read", arguments={"path": "learning_agent/skills/tool_list.md"}))  # 新增代码+路径兼容: 用项目根风格路径读取 skill 总索引；若没有这行代码，兼容分支没有输入
        self.assertIn("browser_automation/SKILL.md", output)  # 新增代码+路径兼容: 断言读取到了真实 tool_list 内容；若没有这行代码，路径兼容失败可能只返回错误文本而不被发现
    def test_default_prompt_budget_stays_under_capability_pack_target(self) -> None:  # 新增代码+CapabilityPacks: 验证默认 system prompt 预算落入方案 B 目标；若没有这行代码，工具隐藏后 system prompt 仍可能继续过大
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CapabilityPacks: 创建临时工作区隔离 prompt 预算测试；若没有这行代码，测试可能受真实 memory 内容波动影响
            workspace = Path(raw_dir)  # 新增代码+CapabilityPacks: 把临时目录转成 Path；若没有这行代码，后续写入上下文文件不方便
            memory_dir = workspace / "agent_memory"  # 新增代码+CapabilityPacks: 定义项目记忆目录；若没有这行代码，无法模拟真实三件套索引预算
            memory_dir.mkdir()  # 新增代码+CapabilityPacks: 创建 agent_memory 目录；若没有这行代码，写入三件套会失败
            (memory_dir / "context.md").write_text("# 项目上下文\n- 稳定事实\n" * 200, encoding="utf-8")  # 新增代码+CapabilityPacks: 写入较长 context 样本；若没有这行代码，预算测试无法覆盖索引截断
            (memory_dir / "progress.md").write_text("# 当前任务进度\n- 最近进度\n" * 200, encoding="utf-8")  # 新增代码+CapabilityPacks: 写入较长 progress 样本；若没有这行代码，项目记忆预算会被低估
            (memory_dir / "bugs.md").write_text("# 问题与风险记录\n- 剩余风险\n" * 200, encoding="utf-8")  # 新增代码+CapabilityPacks: 写入较长 bugs 样本；若没有这行代码，风险索引预算不会被覆盖
            runtime_source = self._dynamic_prompt_file().read_text(encoding="utf-8")  # 新增代码+CapabilityPacks: 读取真实短内核作为测试输入；若没有这行代码，测试无法约束实际 runtime 文件大小
            (workspace / "runtime_instructions.md").write_text(runtime_source, encoding="utf-8")  # 新增代码+CapabilityPacks: 把短内核写入临时工作区；若没有这行代码，agent 会使用缺失占位而不是实际规则
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+CapabilityPacks: 创建测试 agent；若没有这行代码，无法构造 prompt surface report
            agent._build_initial_messages("检查默认提示词预算")  # 新增代码+CapabilityPacks: 构造初始 messages 并刷新预算报告；若没有这行代码，last_prompt_surface_report 仍是空报告
            self.assertLessEqual(agent.last_prompt_surface_report.estimated_total_tokens, 1900)  # 新增代码+CapabilityPacks: 断言默认 prompt 粗估不超过 1900 tokens；若没有这行代码，方案 B 的 system prompt 目标没有硬保护
    def test_tool_search_select_pack_loads_builtin_capability_tools(self) -> None:  # 新增代码+CapabilityPacks: 验证 tool_search 可以按能力包加载内置工具；若没有这行代码，模型只能一个个 select 工具导致流程笨重
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CapabilityPacks: 创建临时工作区隔离测试文件；若没有这行代码，测试可能读取真实 skills 或 memory
            workspace = Path(raw_dir)  # 新增代码+CapabilityPacks: 把临时目录转成 Path；若没有这行代码，后续 agent 初始化不够清楚
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+CapabilityPacks: 创建测试 agent；若没有这行代码，无法通过真实工具入口执行 select_pack
            before_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+CapabilityPacks: 记录选择能力包前的可见工具；若没有这行代码，无法证明加载动作真的改变工具池
            select_output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "select_pack:file_operations"}))  # 新增代码+CapabilityPacks: 请求加载文件操作能力包；若没有这行代码，select_pack 分支没有测试输入
            after_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+CapabilityPacks: 记录选择能力包后的可见工具；若没有这行代码，无法验证工具 schema 已进入当前池
            self.assertIn("tool_search 成功", select_output)  # 新增代码+CapabilityPacks: 断言能力包选择返回成功前缀；若没有这行代码，失败输出可能被后续工具名断言掩盖
            self.assertIn("file_operations", select_output)  # 新增代码+CapabilityPacks: 断言输出明确说明加载的是文件能力包；若没有这行代码，模型难以确认自己选中了哪个包
            self.assertNotIn("read_file", before_names)  # 新增代码+CapabilityPacks: 断言选择前 read_file 隐藏；若没有这行代码，测试无法证明工具池真的被精简
            self.assertIn("read_file", after_names)  # 新增代码+CapabilityPacks: 断言选择后 read_file 可见；若没有这行代码，能力包加载可能只返回文本但没改变工具池
            self.assertIn("write_file", after_names)  # 新增代码+CapabilityPacks: 断言同包写文件工具也一起可见；若没有这行代码，能力包批量加载语义可能退化成单工具加载
    def test_tool_policy_blocks_denied_tool_before_pool_exposure(self) -> None:  # 新增代码+ToolPolicyV2: 验证 deny 规则会在工具进入当前池之前拦截；若没有这行代码，被拒绝工具可能仍暴露给模型
        tool = build_builtin_tool_catalog()[0]  # 新增代码+ToolPolicyV2: 使用真实内置 AgentTool 作为策略输入；若没有这行代码，测试只会覆盖假对象而可能漏掉真实字段
        context = ToolPolicyContext(deny_rules=[ToolPolicyRule(tool_name=tool.name)])  # 新增代码+ToolPolicyV2: 配置按工具名拒绝当前工具；若没有这行代码，blocked 分支没有可控输入
        decision = ToolPolicy.decide(tool, context)  # 新增代码+ToolPolicyV2: 调用核心策略决策入口；若没有这行代码，测试无法证明 ToolPolicy 会真的拦截
        self.assertEqual(decision.state, "blocked")  # 新增代码+ToolPolicyV2: 断言被拒绝工具状态为 blocked；若没有这行代码，错误状态可能混入后续流程
        self.assertFalse(decision.visible)  # 新增代码+ToolPolicyV2: 断言被拒绝工具不可见；若没有这行代码，deny 后仍可能进入模型上下文
        self.assertFalse(decision.selectable)  # 新增代码+ToolPolicyV2: 断言被拒绝工具不可被 select；若没有这行代码，模型可能绕过拒绝规则加载工具
        self.assertFalse(decision.executable)  # 新增代码+ToolPolicyV2: 断言被拒绝工具不可执行；若没有这行代码，执行层后续可能误以为只是不展示但可调用
    def test_tool_policy_requires_skill_and_workflow_gates(self) -> None:  # 新增代码+ToolPolicyV2: 验证 skill gate 和 workflow gate 的先后门禁；若没有这行代码，真实 Chrome 等 gated 工具可能过早暴露
        tool = next(item for item in build_builtin_tool_catalog() if item.name == "read")  # 修改代码+极简工具面: 使用四原子常驻工具测试 gate 成功态；若没有这行代码，测试会把旧 deferred 工具状态误当成 gate 失败
        tool.skill_gate = "real_chrome"  # 新增代码+ToolPolicyV2: 给工具设置需要加载的 skill；若没有这行代码，needs_skill 分支没有触发条件
        tool.workflow_gate = "real_chrome_profile_ready"  # 新增代码+ToolPolicyV2: 给工具设置需要完成的 workflow；若没有这行代码，needs_workflow 分支没有触发条件
        missing_skill = ToolPolicy.decide(tool, ToolPolicyContext())  # 新增代码+ToolPolicyV2: 在没有任何上下文门票时决策；若没有这行代码，无法验证缺 skill 会先被拦住
        self.assertEqual(missing_skill.state, "needs_skill")  # 新增代码+ToolPolicyV2: 断言缺少 skill 时返回 needs_skill；若没有这行代码，gate 优先级错误不会暴露
        self.assertFalse(missing_skill.visible)  # 新增代码+ToolPolicyV2: 断言缺 skill 的工具不可见；若没有这行代码，模型可能看到尚未准备好的工具
        skill_only_context = ToolPolicyContext(loaded_skills={"real_chrome"})  # 新增代码+ToolPolicyV2: 构造只有 skill 但没有 workflow 的上下文；若没有这行代码，无法验证第二道门禁
        missing_workflow = ToolPolicy.decide(tool, skill_only_context)  # 新增代码+ToolPolicyV2: 对只满足 skill 的情况做决策；若没有这行代码，needs_workflow 分支不会被测试
        self.assertEqual(missing_workflow.state, "needs_workflow")  # 新增代码+ToolPolicyV2: 断言缺 workflow 时返回 needs_workflow；若没有这行代码，workflow gate 可能被静默跳过
        ready_context = ToolPolicyContext(loaded_skills={"real_chrome"}, completed_workflows={"real_chrome_profile_ready"})  # 新增代码+ToolPolicyV2: 构造两个门禁都满足的上下文；若没有这行代码，无法验证最终可选状态
        ready_decision = ToolPolicy.decide(tool, ready_context)  # 新增代码+ToolPolicyV2: 对满足所有 gate 的工具做决策；若没有这行代码，测试无法证明工具会恢复可用
        self.assertEqual(ready_decision.state, "loaded")  # 新增代码+ToolPolicyV2: 断言满足所有 gate 后状态回到 loaded；若没有这行代码，成功路径可能只可选但状态仍错误
        self.assertTrue(ready_decision.visible)  # 新增代码+ToolPolicyV2: 断言满足所有 gate 后工具可见；若没有这行代码，模型可能仍看不到已经准备好的工具
        self.assertTrue(ready_decision.selectable)  # 新增代码+ToolPolicyV2: 断言满足 gate 后工具可被选择；若没有这行代码，策略可能一直把工具锁死
        self.assertTrue(ready_decision.executable)  # 新增代码+ToolPolicyV2: 断言满足所有 gate 后工具可执行；若没有这行代码，执行层可能仍把可用工具当成不可执行
    def test_tool_policy_handles_deferred_loaded_and_always_load_decisions(self) -> None:  # 新增代码+ToolPolicyV2: 覆盖 deferred、loaded 和 always_load 的基础决策；若没有这行代码，延迟加载核心分支缺少回归保护
        tool = build_builtin_tool_catalog()[0]  # 新增代码+ToolPolicyV2: 使用真实 AgentTool 作为策略输入；若没有这行代码，测试可能只验证假对象而漏掉真实字段行为
        tool.should_defer = True  # 新增代码+ToolPolicyV2: 把真实工具临时标记为需要延迟加载；若没有这行代码，deferred 分支不会被触发
        tool.always_load = False  # 新增代码+ToolPolicyV2: 明确该工具不是强制首轮加载；若没有这行代码，deferred 判断可能被默认值或前序状态干扰
        deferred_decision = ToolPolicy.decide(tool, ToolPolicyContext(), loaded=False)  # 新增代码+ToolPolicyV2: 在未加载状态下执行策略判断；若没有这行代码，无法验证未加载 deferred 工具的隐藏行为
        self.assertEqual(deferred_decision.state, "deferred")  # 新增代码+ToolPolicyV2: 断言未加载 deferred 工具状态为 deferred；若没有这行代码，状态回归不会被发现
        self.assertFalse(deferred_decision.visible)  # 新增代码+ToolPolicyV2: 断言未加载 deferred 工具不可见；若没有这行代码，外部工具可能重新默认进入模型上下文
        self.assertTrue(deferred_decision.selectable)  # 新增代码+ToolPolicyV2: 断言 deferred 工具仍可被 select 选择；若没有这行代码，模型可能无法加载延迟工具
        self.assertFalse(deferred_decision.executable)  # 新增代码+ToolPolicyV2: 断言未加载 deferred 工具不可执行；若没有这行代码，执行层可能绕过 select 直接调用
        loaded_decision = ToolPolicy.decide(tool, ToolPolicyContext(), loaded=True)  # 新增代码+ToolPolicyV2: 在已加载状态下执行策略判断；若没有这行代码，无法验证 select 后工具恢复可用
        self.assertEqual(loaded_decision.state, "loaded")  # 新增代码+ToolPolicyV2: 断言已加载 deferred 工具状态为 loaded；若没有这行代码，加载成功路径状态可能错误
        self.assertTrue(loaded_decision.visible)  # 新增代码+ToolPolicyV2: 断言已加载工具可见；若没有这行代码，模型可能 select 后仍看不到工具
        self.assertTrue(loaded_decision.selectable)  # 新增代码+ToolPolicyV2: 断言已加载工具仍可选择；若没有这行代码，工具池状态可能出现不一致
        self.assertTrue(loaded_decision.executable)  # 新增代码+ToolPolicyV2: 断言已加载工具可执行；若没有这行代码，select 后仍可能无法调用工具
        tool.always_load = True  # 新增代码+ToolPolicyV2: 把工具改为强制加载以覆盖 always_load 优先级；若没有这行代码，always_load 绕过 deferred 的规则缺少测试
        always_loaded_decision = ToolPolicy.decide(tool, ToolPolicyContext(), loaded=False)  # 新增代码+ToolPolicyV2: 在未显式 loaded 但 always_load 为真时执行判断；若没有这行代码，无法验证强制加载入口
        self.assertEqual(always_loaded_decision.state, "loaded")  # 新增代码+ToolPolicyV2: 断言 always_load 工具即使 loaded=False 也视为 loaded；若没有这行代码，发现入口可能被错误隐藏
        self.assertTrue(always_loaded_decision.visible)  # 新增代码+ToolPolicyV2: 断言 always_load 工具可见；若没有这行代码，tool_search 这类入口可能消失
        self.assertTrue(always_loaded_decision.selectable)  # 新增代码+ToolPolicyV2: 断言 always_load 工具可选择；若没有这行代码，强制加载工具可能无法进入选择流程
        self.assertTrue(always_loaded_decision.executable)  # 新增代码+ToolPolicyV2: 断言 always_load 工具可执行；若没有这行代码，强制加载工具可能仍被执行层拒绝
    def test_tool_policy_rule_matches_server_source_and_ignores_empty_rule(self) -> None:  # 新增代码+ToolPolicyV2: 覆盖 server/source 规则和空规则边界；若没有这行代码，deny 匹配可能误伤所有工具或漏掉来源规则
        tool = next(item for item in build_builtin_tool_catalog() if item.name == "read")  # 修改代码+极简工具面: 使用四原子常驻工具作为规则匹配目标；若没有这行代码，空规则断言会被 deferred 默认隐藏状态干扰
        tool.server_name = "browser_automation"  # 新增代码+ToolPolicyV2: 设置 server_name 来模拟外部 MCP server 来源；若没有这行代码，server_name 规则没有可匹配字段
        tool.source = "mcp"  # 新增代码+ToolPolicyV2: 设置 source 来模拟 MCP 工具来源；若没有这行代码，source 规则没有可匹配字段
        server_denied = ToolPolicy.decide(tool, ToolPolicyContext(deny_rules=[ToolPolicyRule(server_name="browser_automation")]))  # 新增代码+ToolPolicyV2: 用 server_name 拒绝规则执行决策；若没有这行代码，无法证明 server 级拦截生效
        self.assertEqual(server_denied.state, "blocked")  # 新增代码+ToolPolicyV2: 断言 server_name 命中后会 blocked；若没有这行代码，server 规则失效不会被发现
        self.assertFalse(server_denied.visible)  # 新增代码+ToolPolicyV2: 断言 server_name 命中后不可见；若没有这行代码，被拒绝 server 的工具可能仍暴露给模型
        source_denied = ToolPolicy.decide(tool, ToolPolicyContext(deny_rules=[ToolPolicyRule(source="mcp")]))  # 新增代码+ToolPolicyV2: 用 source 拒绝规则执行决策；若没有这行代码，无法证明来源级拦截生效
        self.assertEqual(source_denied.state, "blocked")  # 新增代码+ToolPolicyV2: 断言 source 命中后会 blocked；若没有这行代码，来源规则失效不会被发现
        self.assertFalse(source_denied.executable)  # 新增代码+ToolPolicyV2: 断言 source 命中后不可执行；若没有这行代码，被拒绝来源工具可能仍被调用
        empty_rule_decision = ToolPolicy.decide(tool, ToolPolicyContext(deny_rules=[ToolPolicyRule()]))  # 新增代码+ToolPolicyV2: 用空规则执行决策来验证不会全局匹配；若没有这行代码，空配置可能意外封禁所有工具
        self.assertEqual(empty_rule_decision.state, "loaded")  # 新增代码+ToolPolicyV2: 断言空规则不会把工具 block；若没有这行代码，空 deny rule 误伤所有工具不会被发现
        self.assertTrue(empty_rule_decision.visible)  # 新增代码+ToolPolicyV2: 断言空规则下工具仍可见；若没有这行代码，模型工具池可能被空规则清空
        self.assertTrue(empty_rule_decision.selectable)  # 新增代码+ToolPolicyV2: 断言空规则下工具仍可选择；若没有这行代码，select 流程可能被空规则误拦截
        self.assertTrue(empty_rule_decision.executable)  # 新增代码+ToolPolicyV2: 断言空规则下工具仍可执行；若没有这行代码，执行层可能被空规则误封锁
    def test_tool_policy_allow_rules_limit_tools_when_present(self) -> None:  # 新增代码+ToolPolicyV2: 验证 allow_rules 一旦配置就形成真实白名单；若没有这行代码，允许规则可能只是被保存但不生效
        allowed_tool = next(item for item in build_builtin_tool_catalog() if item.name == "read")  # 修改代码+极简工具面: 取四原子常驻工具作为白名单允许对象；若没有这行代码，允许对象可能因 deferred 默认隐藏而被误判失败
        blocked_tool = next(item for item in build_builtin_tool_catalog() if item.name == "write")  # 修改代码+极简工具面: 取另一个四原子工具作为未允许对象；若没有这行代码，白名单测试会混入旧工具延迟状态
        context = ToolPolicyContext(allow_rules=[ToolPolicyRule(tool_name=allowed_tool.name)])  # 新增代码+ToolPolicyV2: 构造只允许 allowed_tool 的策略上下文；若没有这行代码，allow_rules 白名单语义不会触发
        allowed_decision = ToolPolicy.decide(allowed_tool, context)  # 新增代码+ToolPolicyV2: 对命中 allow rule 的工具执行策略判断；若没有这行代码，无法证明允许对象仍可使用
        blocked_decision = ToolPolicy.decide(blocked_tool, context)  # 新增代码+ToolPolicyV2: 对未命中 allow rule 的工具执行策略判断；若没有这行代码，无法证明白名单会真正阻断
        self.assertEqual(allowed_decision.state, "loaded")  # 新增代码+ToolPolicyV2: 断言白名单命中工具仍是 loaded；若没有这行代码，allow_rules 可能错误地把允许对象也封锁
        self.assertTrue(allowed_decision.executable)  # 新增代码+ToolPolicyV2: 断言白名单命中工具可执行；若没有这行代码，允许规则可能只影响展示不影响执行
        self.assertEqual(blocked_decision.state, "blocked")  # 新增代码+ToolPolicyV2: 断言未命中白名单的工具被 blocked；若没有这行代码，allow_rules 不生效不会被发现
        self.assertFalse(blocked_decision.visible)  # 新增代码+ToolPolicyV2: 断言未允许工具不可见；若没有这行代码，模型仍可能看到白名单外工具
        self.assertFalse(blocked_decision.selectable)  # 新增代码+ToolPolicyV2: 断言未允许工具不可 select；若没有这行代码，模型可能通过 tool_search 加载白名单外工具
        self.assertFalse(blocked_decision.executable)  # 新增代码+ToolPolicyV2: 断言未允许工具不可执行；若没有这行代码，直接工具调用仍可能越过白名单
    def test_tool_search_uses_aliases_for_discovery(self) -> None:  # 新增代码+ToolPolicyV2: 验证 AgentTool aliases 会参与工具搜索召回；若没有这行代码，别名元数据只会存储不会真正帮助发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolPolicyV2: 创建临时工作区隔离 agent 文件；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolPolicyV2: 把临时目录转成 Path；若没有这行代码，LearningAgent 初始化路径语义不够清楚
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+ToolPolicyV2: 创建只含内置工具的 agent；若没有这行代码，无法操作真实 AgentTool catalog
            tool = agent._find_catalog_tool("read_file")  # 新增代码+ToolPolicyV2: 从 catalog 中找到 read_file 工具；若没有这行代码，无法给真实工具设置别名
            self.assertIsNotNone(tool)  # 新增代码+ToolPolicyV2: 断言 read_file 存在；若没有这行代码，后续失败可能来自测试数据异常
            assert tool is not None  # 新增代码+ToolPolicyV2: 告诉类型检查器 tool 已存在；若没有这行代码，后续修改 aliases 的类型不够明确
            tool.aliases.append("inspect-document")  # 新增代码+ToolPolicyV2: 给 read_file 增加一个名称和描述都不含的别名；若没有这行代码，aliases 召回路径不会触发
            output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "inspect-document", "max_results": 5}))  # 新增代码+ToolPolicyV2: 使用只存在于 alias 的关键词搜索；若没有这行代码，别名搜索是否生效无法被测试
            self.assertIn("read_file", output)  # 新增代码+ToolPolicyV2: 断言 alias 命中能召回 read_file；若没有这行代码，aliases 失效不会被发现
            self.assertIn("aliases：inspect-document", output)  # 新增代码+ToolPolicyV2: 断言搜索结果展示别名；若没有这行代码，命中依据不清楚
    def test_tool_search_select_unknown_tool_reports_clear_failure(self) -> None:  # 新增代码+ToolArchitectureV2: 验证 select 未知工具时返回清晰失败；若没有这行代码，模型可能误以为不存在工具也已加载
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolArchitectureV2: 创建临时工作区隔离 agent 文件；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolArchitectureV2: 把临时目录转成 Path；若没有这行代码，LearningAgent 初始化参数不够清楚
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+ToolArchitectureV2: 创建无 MCP 的 agent 以测试未知 select；若没有这行代码，无法执行 tool_search
            output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "select:mcp__missing__tool"}))  # 新增代码+ToolArchitectureV2: 请求加载不存在的工具名；若没有这行代码，未知 select 分支没有测试输入
            self.assertIn("tool_search 失败", output)  # 新增代码+ToolArchitectureV2: 断言未知工具返回失败状态；若没有这行代码，select 失败可能被误报成功
            self.assertIn("没有找到工具", output)  # 新增代码+ToolArchitectureV2: 断言失败原因说明工具不存在；若没有这行代码，模型不知道应重新搜索完整工具名
    def test_tool_search_reports_blocked_tools_from_policy(self) -> None:  # 新增代码+ToolPolicyV2: 验证 tool_search 会展示被策略阻断的工具；若没有这行代码，blocked 工具可能被静默隐藏导致模型不知道为什么不可用
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolPolicyV2: 创建临时工作区隔离 agent 文件和日志；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolPolicyV2: 把临时目录转成 Path 交给 LearningAgent；若没有这行代码，agent 初始化路径语义不够清晰
            fake_client = FakeMcpClient()  # 新增代码+ToolPolicyV2: 使用默认含 echo 工具的 fake MCP client；若没有这行代码，测试没有可被 deny rule 命中的 MCP 工具
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+ToolPolicyV2: 用 demo server 创建 registry 以生成 mcp__demo__echo；若没有这行代码，目标工具名不会出现在 catalog
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+ToolPolicyV2: 创建允许启动 MCP 的 agent；若没有这行代码，tool_search 无法搜索 fake MCP 工具
            agent.tool_policy_context.deny_rules.append(ToolPolicyRule(tool_name="mcp__demo__echo"))  # 新增代码+ToolPolicyV2: 配置拒绝 echo 工具的策略规则；若没有这行代码，blocked 分支没有真实触发条件
            output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "echo"}))  # 新增代码+ToolPolicyV2: 通过真实 tool_search 搜索 echo；若没有这行代码，测试不会覆盖工具搜索输出路径
            self.assertIn("mcp__demo__echo", output)  # 新增代码+ToolPolicyV2: 断言 blocked 工具仍被搜索结果报告；若没有这行代码，模型可能看不到被阻断工具的解释
            self.assertIn("state：blocked", output)  # 新增代码+ToolPolicyV2: 断言输出使用 ToolPolicyDecision.state；若没有这行代码，blocked 状态可能没有进入展示层
            self.assertIn("阻断原因", output)  # 新增代码+ToolPolicyV2: 断言输出包含清楚的策略原因；若没有这行代码，用户和模型不知道为什么不能加载该工具
    def test_tool_search_select_refuses_tools_missing_skill_gate(self) -> None:  # 新增代码+ToolPolicyV2: 验证缺 skill gate 的工具不能被 select 加载；若没有这行代码，模型可能绕过技能门禁直接加载真实 Chrome 工具
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolPolicyV2: 创建临时工作区隔离 agent 文件和日志；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolPolicyV2: 把临时目录转成 Path 交给 LearningAgent；若没有这行代码，agent 初始化路径语义不够清晰
            fake_client = FakeMcpClient(tools=[  # 新增代码+ToolPolicyV2: 构造只暴露真实 Chrome 连接工具的 fake MCP client；若没有这行代码，测试没有 skill gate 目标工具
                {  # 新增代码+ToolPolicyV2: 开始定义 browser_connect_real_chrome 工具条目；若没有这行代码，工具列表里没有目标 MCP 工具
                    "name": "browser_connect_real_chrome",  # 新增代码+ToolPolicyV2: 使用真实 Chrome 连接工具原始名；若没有这行代码，前缀工具名不会符合任务要求
                    "description": "Connect to a real Chrome profile",  # 新增代码+ToolPolicyV2: 提供可搜索的工具说明；若没有这行代码，tool_search select 前的 catalog 元数据不完整
                    "inputSchema": {  # 新增代码+ToolPolicyV2: 声明 MCP 工具输入 schema；若没有这行代码，AgentTool 参数边界不完整
                        "type": "object",  # 新增代码+ToolPolicyV2: 声明参数必须是对象；若没有这行代码，模型 schema 边界不清楚
                        "properties": {  # 新增代码+ToolPolicyV2: 开始列出允许的参数字段；若没有这行代码，confirm_real_profile 字段没有容器可放
                            "confirm_real_profile": {"type": "boolean"},  # 新增代码+ToolPolicyV2: 声明真实 profile 确认参数；若没有这行代码，测试工具不贴近真实 Chrome 工具
                        },  # 新增代码+ToolPolicyV2: 结束 properties 字典；若没有这行代码，测试工具 schema 语法不完整
                    },  # 新增代码+ToolPolicyV2: 结束 inputSchema 字典；若没有这行代码，MCP 工具条目结构不完整
                }  # 新增代码+ToolPolicyV2: 结束 browser_connect_real_chrome 工具条目；若没有这行代码，工具列表元素语法不完整
            ])  # 新增代码+ToolPolicyV2: 结束 fake client 构造；若没有这行代码，agent 没有可启动的 fake MCP client
            registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+ToolPolicyV2: 用 browser_automation server 名创建 registry；若没有这行代码，目标前缀工具名不会出现
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+ToolPolicyV2: 创建允许 MCP 启动的 agent；若没有这行代码，无法执行 tool_search select
            tool = agent._find_catalog_tool("mcp__browser_automation__browser_connect_real_chrome")  # 新增代码+ToolPolicyV2: 从完整 catalog 找到目标工具；若没有这行代码，无法给真实 catalog 工具设置 skill gate
            self.assertIsNotNone(tool)  # 新增代码+ToolPolicyV2: 断言目标工具确实存在；若没有这行代码，后续失败可能来自测试数据没建好而不是策略门禁
            assert tool is not None  # 新增代码+ToolPolicyV2: 帮类型检查器知道 tool 已存在；若没有这行代码，后续给 skill_gate 赋值在静态检查中不够明确
            tool.skill_gate = "real-chrome"  # 新增代码+ToolPolicyV2: 给目标工具设置需要先加载的 skill；若没有这行代码，needs_skill 分支不会触发
            output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "select:mcp__browser_automation__browser_connect_real_chrome"}))  # 新增代码+ToolPolicyV2: 尝试 select 缺 skill 的工具；若没有这行代码，测试不会覆盖 select 门禁
            self.assertIn("needs_skill", output)  # 新增代码+ToolPolicyV2: 断言失败输出包含策略状态；若没有这行代码，select 拒绝原因可能不清楚
            self.assertIn("需要先加载 skill", output)  # 新增代码+ToolPolicyV2: 断言失败输出给出人话提示；若没有这行代码，用户不知道下一步该补 skill
            self.assertNotIn("mcp__browser_automation__browser_connect_real_chrome", agent.loaded_tool_names)  # 新增代码+ToolPolicyV2: 断言缺 skill 时没有加入 loaded_tool_names；若没有这行代码，工具可能虽然报错但已经被偷偷加载
    def test_tool_search_select_does_not_allow_same_turn_deferred_tool_execution(self) -> None:  # 新增代码+ToolPolicyV2: 验证 run 同一批 tool_calls 里 select 不会立刻放行 deferred 工具；若没有这行代码，同轮执行绕过会再次回归
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolPolicyV2: 创建临时工作区隔离 agent 文件和调试日志；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolPolicyV2: 把临时目录转成 Path 交给 LearningAgent；若没有这行代码，agent 初始化路径语义不够清楚
            fake_client = FakeMcpClient()  # 新增代码+ToolPolicyV2: 使用默认含 echo 工具的 fake MCP client；若没有这行代码，测试没有 deferred MCP 调用目标
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+ToolPolicyV2: 用 demo server 创建 registry 以生成 mcp__demo__echo；若没有这行代码，目标工具名不会出现在 catalog
            model = SequentialRecordingToolNameFakeModel([  # 新增代码+ToolPolicyV2: 创建记录每轮工具池并返回多轮响应的假模型；若没有这行代码，测试无法观察下一轮 schema
                ModelMessage(text="", tool_calls=[  # 新增代码+ToolPolicyV2: 第一轮让模型在同一批里先 select 再直接调用；若没有这行代码，无法复现同轮绕过风险
                    ToolCall(name="tool_search", arguments={"query": "select:mcp__demo__echo"}),  # 新增代码+ToolPolicyV2: 第一条工具调用请求加载 deferred echo；若没有这行代码，pending select 场景不会触发
                    ToolCall(name="mcp__demo__echo", arguments={"text": "同轮不应执行"}),  # 新增代码+ToolPolicyV2: 第二条工具调用立刻尝试执行 echo；若没有这行代码，测试无法证明同批直接调用仍被拒绝
                ]),  # 新增代码+ToolPolicyV2: 结束第一轮模型消息；若没有这行代码，预设响应列表语法不完整
                ModelMessage(text="第二轮结束。"),  # 新增代码+ToolPolicyV2: 第二轮直接结束 run 以便检查工具池快照；若没有这行代码，agent.run 会继续等待更多模型输出
            ])  # 新增代码+ToolPolicyV2: 结束假模型构造；若没有这行代码，agent 没有可控模型输入
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+ToolPolicyV2: 创建允许启动 MCP 的 agent；若没有这行代码，run 无法搜索和加载 fake MCP 工具
            result = agent.run("测试同轮 select 后直接调用 deferred 工具。", max_turns=2)  # 新增代码+ToolPolicyV2: 执行两轮 agent run；若没有这行代码，pending select 和下一轮 schema 刷新都不会发生
            self.assertIn("第二轮结束", result)  # 新增代码+ToolPolicyV2: 断言 run 进入第二轮并正常结束；若没有这行代码，测试可能只停在第一轮而没覆盖下一轮工具池
            self.assertEqual([], fake_client.calls)  # 新增代码+ToolPolicyV2: 断言同批直接 MCP 调用没有真正转发给 fake client；若没有这行代码，同轮绕过执行不会被发现
            self.assertIn("mcp__demo__echo", agent.loaded_tool_names)  # 新增代码+ToolPolicyV2: 断言批次结束后 pending select 已合并；若没有这行代码，select 可能被永久丢失
            self.assertNotIn("mcp__demo__echo", model.received_tool_names[0])  # 新增代码+ToolPolicyV2: 断言第一轮模型工具池还没有 deferred echo；若没有这行代码，测试不能证明初始池仍隐藏 deferred 工具
            self.assertIn("mcp__demo__echo", model.received_tool_names[1])  # 新增代码+ToolPolicyV2: 断言第二轮模型工具池才出现 echo；若没有这行代码，run 每轮重新计算 tools 的要求没有被测试锁住
    def test_policy_blocked_tool_call_is_rejected_before_permission_prompt(self) -> None:  # 新增代码+ToolPolicyV2: 验证执行层会在 MCP 权限弹窗前拦截 policy blocked 工具；若没有这行代码，deny rule 可能只挡住搜索但挡不住直接执行
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolPolicyV2: 创建临时工作区隔离测试文件；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolPolicyV2: 把临时目录转成 Path 传给 agent；若没有这行代码，路径语义不够稳定
            fake_client = FakeMcpClient()  # 新增代码+ToolPolicyV2: 创建默认 echo MCP 工具供策略拦截；若没有这行代码，测试没有可被 deny rule 命中的 MCP 工具
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+ToolPolicyV2: 创建含 demo server 的 MCP registry；若没有这行代码，agent catalog 不会包含目标 MCP 工具
            permission_requests: list[str] = []  # 新增代码+ToolPolicyV2: 记录所有权限请求文本；若没有这行代码，无法证明工具权限弹窗没有出现
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: permission_requests.append(action) or True, mcp_tool_registry=registry)  # 新增代码+ToolPolicyV2: 创建允许启动 MCP 的 agent；若没有这行代码，执行层没有真实 catalog 和权限回调可测
            agent.tool_policy_context.deny_rules.append(ToolPolicyRule(tool_name="mcp__demo__echo"))  # 新增代码+ToolPolicyV2: 加入按工具名拒绝的策略规则；若没有这行代码，执行层不会触发 blocked 决策
            output = agent._execute_tool(ToolCall(name="mcp__demo__echo", arguments={"text": "x"}))  # 新增代码+ToolPolicyV2: 直接尝试执行被 deny 的 MCP 工具；若没有这行代码，无法覆盖绕过 ToolSearch 的执行入口
            self.assertIn("policy 阻断", output)  # 新增代码+ToolPolicyV2: 断言失败来自策略层阻断；若没有这行代码，测试可能误把其他失败当成成功
            self.assertEqual(permission_requests, ["启动 MCP server：demo"])  # 新增代码+ToolPolicyV2: 断言只请求了启动 MCP，未请求具体工具调用权限；若没有这行代码，blocked 工具仍弹权限窗不会被发现
            self.assertFalse(fake_client.calls)  # 新增代码+ToolPolicyV2: 断言被 blocked 的工具没有真实调用外部 client；若没有这行代码，文本返回正确但副作用已发生的回归会漏掉
    def test_repeated_permission_denial_is_remembered_for_same_tool_and_arguments(self) -> None:  # 新增代码+ToolPolicyV2: 验证同一 MCP 工具和清洗后参数被拒绝后会被记住；若没有这行代码，agent 可能反复打扰用户确认同一被拒操作
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolPolicyV2: 创建临时工作区隔离测试文件；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolPolicyV2: 把临时目录转成 Path 传给 agent；若没有这行代码，路径语义不够稳定
            fake_client = FakeMcpClient()  # 新增代码+ToolPolicyV2: 创建默认 echo MCP 工具供权限拒绝测试；若没有这行代码，无法进入 MCP 工具权限路径
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+ToolPolicyV2: 创建含 demo server 的 MCP registry；若没有这行代码，agent 无法发现并调用目标 MCP 工具
            permission_requests: list[str] = []  # 新增代码+ToolPolicyV2: 记录权限请求文本；若没有这行代码，无法统计工具权限是否重复弹出
            def ask_permission(action: str) -> bool:  # 新增代码+ToolPolicyV2: 定义可控权限回调；若没有这行代码，测试无法允许启动但拒绝具体 MCP 调用
                permission_requests.append(action)  # 新增代码+ToolPolicyV2: 保存本次权限请求；若没有这行代码，测试无法断言重复请求次数
                return action.startswith("启动 MCP server")  # 新增代码+ToolPolicyV2: 只允许启动 MCP server 且拒绝工具调用；若没有这行代码，拒绝记忆分支不会出现
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=ask_permission, mcp_tool_registry=registry)  # 新增代码+ToolPolicyV2: 创建带可控权限回调的 agent；若没有这行代码，测试没有执行主体
            self._select_tool_for_test(agent, "mcp__demo__echo")  # 新增代码+ToolPolicyV2: 先加载 deferred MCP 工具；若没有这行代码，执行会停在未 select 门禁而不是权限拒绝记忆
            first = agent._execute_tool(ToolCall(name="mcp__demo__echo", arguments={"text": "deny", "extra": "dropped"}))  # 新增代码+ToolPolicyV2: 第一次调用带一个会被 schema 清洗移除的多余参数；若没有这行代码，无法证明拒绝 key 基于清洗后参数
            second = agent._execute_tool(ToolCall(name="mcp__demo__echo", arguments={"extra": "different", "text": "deny"}))  # 新增代码+ToolPolicyV2: 第二次用同一清洗后参数但不同原始多余参数和顺序；若没有这行代码，无法验证稳定拒绝 key 会去重
            self.assertIn("拒绝", first)  # 新增代码+ToolPolicyV2: 断言第一次真实走到用户拒绝分支；若没有这行代码，测试可能没有覆盖权限拒绝
            self.assertIn("之前已被用户拒绝", second)  # 新增代码+ToolPolicyV2: 断言第二次直接命中拒绝记忆；若没有这行代码，重复弹窗回归不会被发现
            self.assertEqual(len([item for item in permission_requests if item.startswith("调用 MCP 工具")]), 1)  # 新增代码+ToolPolicyV2: 断言具体工具调用权限只弹一次；若没有这行代码，拒绝记忆无效也可能被文本断言漏掉
            self.assertFalse(fake_client.calls)  # 新增代码+ToolPolicyV2: 断言两次拒绝都没有调用外部 client；若没有这行代码，权限拒绝后的副作用回归不会被发现
    def test_real_chrome_safety_policy_blocks_sensitive_script(self) -> None:  # 新增代码+RealChrome测试: 验证敏感 JavaScript 默认被拒绝；若省略: 真实登录态隐私边界没有自动保护
        policy = BrowserSafetyPolicy()  # 新增代码+RealChrome测试: 创建安全策略对象；若省略: 无法调用脚本校验
        blocked_scripts = ["document.cookie", "localStorage.getItem('x')", "sessionStorage.clear()", "document.querySelector('input[type=password]').value", "window.token"]  # 新增代码+RealChrome测试: 准备应拒绝的敏感脚本；若省略: 关键敏感入口不会被覆盖
        for script in blocked_scripts:  # 新增代码+RealChrome测试: 遍历每个敏感脚本；若省略: 只能覆盖一个风险词
            with self.subTest(script=script):  # 新增代码+RealChrome测试: 给每个脚本单独显示失败上下文；若省略: 失败时难以定位是哪条规则
                with self.assertRaisesRegex(RealChromeProfileError, "敏感"):  # 新增代码+RealChrome测试: 断言返回真实 Chrome 专用敏感错误；若省略: 拒绝原因可能不清楚
                    policy.validate_script(script)  # 新增代码+RealChrome测试: 执行脚本安全校验；若省略: 测试不会真正触发策略
    def test_real_chrome_safety_policy_allows_visible_text_script(self) -> None:  # 新增代码+RealChrome测试: 验证可见文本读取脚本允许通过；若省略: 安全策略可能过度拦截正常页面摘要
        policy = BrowserSafetyPolicy()  # 新增代码+RealChrome测试: 创建安全策略对象；若省略: 无法调用脚本校验
        policy.validate_script("() => document.body.innerText")  # 新增代码+RealChrome测试: 验证读取可见文本不会报错；若省略: 正常快照替代路径可能被误封
    def test_agent_uses_dynamic_tool_schema_list(self) -> None:  # 新增代码: 验证 agent 调用模型时使用动态工具列表；若省略: 后续 MCP 工具可能无法被传给模型
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 创建临时工作区，避免测试污染真实 learning_agent 目录；若省略: 测试会读写真实文件
            workspace = Path(raw_dir)  # 新增代码: 把临时目录包装成 Path，方便传给 LearningAgent；若省略: 后续路径拼接不方便
            model = RecordingToolNameFakeModel(ModelMessage(text="动态工具测试完成。"))  # 修改代码: 使用会记录 tools 的假模型避免真实 API 调用；若省略: 无法验证 run 真正把动态工具传给模型
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码: 创建 agent 并允许权限；若省略: 无法观察工具列表行为
            original_global_tool_count = len(TOOL_SCHEMAS)  # 新增代码: 记录全局工具列表原始长度；若省略: 无法证明 append 动态副本不会污染全局常量
            tools = agent._available_tool_schemas()  # 新增代码: 调用计划新增的动态工具列表方法；若省略: 无法证明工具列表已从固定常量中解耦
            self.assertIsNot(tools, TOOL_SCHEMAS)  # 新增代码: 确认可用工具列表不是全局列表本体；若省略: 误返回全局列表时测试无法发现污染风险
            tools.append({"type": "function", "function": {"name": "fake_dynamic_tool"}})  # 新增代码: 向动态副本追加假工具；若省略: 无法验证追加副本不会改坏全局 TOOL_SCHEMAS
            tool_names = agent._tool_schema_names(tools)  # 新增代码: 把工具 schema 转成工具名，方便断言；若省略: 断言会更脆弱
            global_tool_names = agent._tool_schema_names(TOOL_SCHEMAS)  # 新增代码: 提取全局工具名用于污染检查；若省略: 无法证明假工具没有进入全局工具集合
            self.assertEqual(len(TOOL_SCHEMAS), original_global_tool_count)  # 新增代码: 确认追加副本后全局列表长度不变；若省略: 返回全局本体的回归可能漏检
            self.assertIn("fake_dynamic_tool", tool_names)  # 新增代码: 确认假工具只进入本地副本工具名；若省略: 无法证明 append 操作真的作用在测试副本上
            self.assertNotIn("fake_dynamic_tool", global_tool_names)  # 新增代码: 确认假工具没有污染全局工具名；若省略: 全局 TOOL_SCHEMAS 被误改时测试无法报警
            self.assertIn("read", tool_names)  # 修改代码+极简工具面: 确认动态列表首轮保留读取入口；若省略: 模型无法读取 tool_list.md 和相关代码
            self.assertIn("write", tool_names)  # 修改代码+极简工具面: 确认动态列表首轮保留写入入口；若省略: 明确新建或全量覆盖文件的请求无法直接完成
            self.assertIn("edit", tool_names)  # 修改代码+极简工具面: 确认动态列表首轮保留编辑入口；若省略: 小范围代码修改会退回旧的隐藏工具
            self.assertIn("bash", tool_names)  # 修改代码+极简工具面: 确认动态列表首轮保留命令入口；若省略: 测试、搜索和脚本执行无法通过原子工具完成
            self.assertNotIn("tool_search", tool_names)  # 修改代码+极简工具面: 确认旧工具搜索不再首轮暴露；若省略: 工具瘦身目标会回退到旧路由
            self.assertNotIn("skill_load", tool_names)  # 修改代码+极简工具面: 确认旧 skill_load 不再首轮暴露；若省略: skill 读取会继续消耗独立工具 schema
            self.assertNotIn("read_file", tool_names)  # 修改代码+CapabilityPacks: 确认文件工具首轮被能力包延迟；若省略: 工具瘦身目标回归为全量暴露不会被发现
            answer = agent.run("请确认动态工具列表")  # 新增代码: 通过 run 触发真实模型调用路径；若省略: 测试只覆盖私有方法而不覆盖实际运行链路
            self.assertIn("动态工具测试完成", answer)  # 新增代码: 确认假模型响应通过 agent.run 返回；若省略: 无法证明本次 run 正常走完
            self.assertEqual(len(model.received_tool_names), 1)  # 新增代码: 确认模型被调用一次；若省略: 后续读取第一条记录可能掩盖调用次数异常
            received_tool_names = model.received_tool_names[0]  # 新增代码: 取出模型实际收到的工具名；若省略: 无法和日志 tool_names 做一致性比较
            self.assertIn("read", received_tool_names)  # 修改代码+极简工具面: 确认模型实际收到读取入口；若省略: 运行链路可能与私有工具池检查不一致
            self.assertIn("write", received_tool_names)  # 修改代码+极简工具面: 确认模型实际收到写入入口；若省略: 四原子工具可能只在私有方法里存在
            self.assertIn("edit", received_tool_names)  # 修改代码+极简工具面: 确认模型实际收到编辑入口；若省略: 代码修改任务可能仍依赖旧工具
            self.assertIn("bash", received_tool_names)  # 修改代码+极简工具面: 确认模型实际收到命令入口；若省略: 真实 run 路径可能无法执行验证命令
            self.assertNotIn("tool_search", received_tool_names)  # 修改代码+极简工具面: 确认模型不再收到旧工具搜索入口；若省略: 每轮工具 schema 可能悄悄变大
            self.assertNotIn("skill_load", received_tool_names)  # 修改代码+极简工具面: 确认模型不再收到旧 skill_load 入口；若省略: skill 路由可能回退为独立工具
            self.assertNotIn("read_file", received_tool_names)  # 修改代码+CapabilityPacks: 确认模型首轮没有收到文件工具；若省略: 47 个工具瘦身目标可能悄悄失效
            self.assertNotIn("fake_dynamic_tool", received_tool_names)  # 新增代码: 确认污染测试用假工具没有进入 run 的全局工具来源；若省略: 无法保护旧行为不被副本 append 影响
            log_path = workspace / "debug_logs" / "agent_debug.jsonl"  # 新增代码: 定位 agent.run 生成的结构化调试日志；若省略: 无法验证日志工具名和模型实参一致
            log_events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]  # 新增代码: 读取并解析 JSONL 日志；若省略: 无法检查 initial_messages 和 model_request 事件
            initial_events = [event for event in log_events if event["event"] == "initial_messages"]  # 新增代码: 筛选初始上下文日志事件；若省略: 无法确认首轮可用工具列表记录正确
            model_request_events = [event for event in log_events if event["event"] == "model_request"]  # 新增代码: 筛选模型请求日志事件；若省略: 无法确认调用前日志工具名记录正确
            self.assertEqual(len(initial_events), 1)  # 新增代码: 确认只记录一次 initial_messages；若省略: 重复或缺失日志事件可能被忽略
            self.assertEqual(len(model_request_events), 1)  # 新增代码: 确认本测试只产生一次 model_request；若省略: 工具名一致性可能对错事件比较
            self.assertEqual(initial_events[0]["payload"]["tool_names"], received_tool_names)  # 新增代码: 确认 initial_messages 日志工具名与模型实际收到的一致；若省略: 日志可能与真实模型上下文脱节
            self.assertEqual(model_request_events[0]["payload"]["tool_names"], received_tool_names)  # 新增代码: 确认 model_request 日志工具名与模型实际收到的一致；若省略: 调试日志可能误导学习者
    def test_tool_result_offload_persists_long_output_and_returns_summary(self) -> None:  # 新增代码+ResultPersistence: 验证长工具结果会保存到磁盘并只回填摘要；若没有这行代码，Phase 6 长输出控制可能退化
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ResultPersistence: 创建临时工作区隔离工具结果产物；若没有这行代码，测试会污染真实 debug_logs
            workspace = Path(raw_dir)  # 新增代码+ResultPersistence: 把临时目录转为 Path；若没有这行代码，LearningAgent 构造不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+ResultPersistence: 创建待测 agent；若没有这行代码，无法调用结果持久化 helper
            long_output = "A" * 9000 + "TAIL"  # 新增代码+ResultPersistence: 构造超过 8000 字符的长结果；若没有这行代码，helper 不会触发落盘分支
            context_output = agent._offload_tool_output_if_needed(ToolCall(name="read_file", arguments={"path": "big.txt"}, call_id="call-long"), long_output)  # 新增代码+ResultPersistence: 直接执行长结果压缩；若没有这行代码，被测逻辑不会运行
            artifact_line = next(line for line in context_output.splitlines() if line.startswith("Full output saved to: "))  # 新增代码+ResultPersistence: 从返回摘要中提取完整输出路径；若没有这行代码，无法验证磁盘文件内容
            artifact_path = Path(artifact_line.replace("Full output saved to: ", "", 1))  # 新增代码+ResultPersistence: 把路径文本转成 Path；若没有这行代码，后续无法读取完整结果
            observation_kinds = [event["kind"] for event in agent.observation_events]  # 新增代码+ResultPersistence: 收集 observation 类型；若没有这行代码，无法验证落盘事件被审计
            self.assertIn("工具结果过长", context_output)  # 新增代码+ResultPersistence: 断言返回内容说明发生了压缩；若没有这行代码，模型可能误以为摘要是完整输出
            self.assertIn("TAIL", context_output)  # 新增代码+ResultPersistence: 断言摘要保留尾部关键信息；若没有这行代码，日志末尾错误可能丢失
            self.assertTrue(artifact_path.exists())  # 新增代码+ResultPersistence: 断言完整输出文件已创建；若没有这行代码，路径可能只是文本假象
            self.assertEqual(artifact_path.read_text(encoding="utf-8"), long_output)  # 新增代码+ResultPersistence: 断言落盘内容完整无截断；若没有这行代码，完整输出可能损坏
            self.assertIn(str(artifact_path), agent.active_artifacts)  # 新增代码+ResultPersistence: 断言 agent 记录了活跃产物路径；若没有这行代码，后续上下文控制找不到结果文件
            self.assertIn("tool_result_offloaded", observation_kinds)  # 新增代码+ResultPersistence: 断言落盘事件进入 observation；若没有这行代码，审计无法解释为什么上下文只有摘要
    def test_available_tool_schemas_deep_copies_builtin_schemas(self) -> None:  # 新增代码+MCP接入健壮性: 验证内置 TOOL_SCHEMAS 的嵌套结构会深拷贝；若省略: 调用方修改返回 schema 会污染全局常量
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP接入健壮性: 创建临时工作区隔离 agent 文件；若省略: 测试可能污染真实目录
            workspace = Path(raw_dir)  # 新增代码+MCP接入健壮性: 把临时目录转成 Path；若省略: LearningAgent 构造不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+MCP接入健壮性: 创建无 MCP 的 agent；若省略: 无法读取动态工具 schema
            agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "select_pack:file_operations"}))  # 修改代码+CapabilityPacks: 先加载文件能力包再检查 read_file schema；若没有这行代码，首轮 kernel 工具池里没有 path 参数可供深拷贝测试
            tools = agent._available_tool_schemas()  # 新增代码+MCP接入健壮性: 获取可变工具 schema 副本；若省略: 无法模拟调用方污染返回值
            read_file_schema = next(schema for schema in tools if schema["function"]["name"] == "read_file")  # 修改代码+CapabilityPacks: 从已加载能力包中定位 read_file；若没有这行代码，测试会错误依赖工具池首项顺序
            read_file_schema["function"]["parameters"]["properties"]["path"]["type"] = "number"  # 修改代码+CapabilityPacks: 修改返回副本的嵌套字段；若省略: 深拷贝防护无法被验证
            second_tools = agent._available_tool_schemas()  # 新增代码+MCP接入健壮性: 再次获取工具 schema；若省略: 无法检查全局是否被污染
            second_read_file_schema = next(schema for schema in second_tools if schema["function"]["name"] == "read_file")  # 修改代码+CapabilityPacks: 再次定位 read_file 副本；若没有这行代码，断言会误读 kernel 工具 schema
            self.assertEqual(second_read_file_schema["function"]["parameters"]["properties"]["path"]["type"], "string")  # 修改代码+CapabilityPacks: 断言内置 schema 嵌套字段未被污染；若省略: 浅拷贝回归不会被发现
    def test_runtime_instructions_mentions_todo_tools(self) -> None:  # 新增代码+TodoWrite: 验证运行规则会引导模型用任务清单工具管理长任务；若省略: 工具存在但模型可能不知道何时使用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+TodoWrite: 定位真实运行时规则文件；若省略: 测试无法覆盖模型实际读取的规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+TodoWrite: 用 UTF-8 读取中文规则；若省略: Windows 默认编码可能导致中文断言不稳定
        self.assertIn("todo_read", runtime_text)  # 新增代码+TodoWrite: 断言规则提到读取任务清单工具；若省略: 模型可能不会先查看已有计划
        self.assertIn("todo_write", runtime_text)  # 新增代码+TodoWrite: 断言规则提到写入任务清单工具；若省略: 模型可能无法主动维护任务状态
        self.assertIn("任务清单", runtime_text)  # 新增代码+TodoWrite: 断言规则用中文解释 Todo 工具用途；若省略: 初学者难以理解该工具和文件工具的区别
    def test_runtime_instructions_mentions_background_command_tools(self) -> None:  # 新增代码+后台命令: 验证运行规则会引导模型使用后台命令工具；若省略: 工具存在但模型可能不知道何时启动长任务
        runtime_file = self._dynamic_prompt_file()  # 新增代码+后台命令: 定位真实运行时规则文件；若省略: 测试无法覆盖模型实际读取的规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+后台命令: 用 UTF-8 读取中文规则；若省略: Windows 默认编码可能导致中文断言不稳定
        self.assertIn("start_background_command", runtime_text)  # 新增代码+后台命令: 断言规则提到启动后台命令工具；若省略: 模型可能仍用同步命令跑长任务
        self.assertIn("read_background_command", runtime_text)  # 新增代码+后台命令: 断言规则提到读取后台输出工具；若省略: 模型可能启动后无法观察进度
        self.assertIn("stop_background_command", runtime_text)  # 新增代码+后台命令: 断言规则提到停止后台命令工具；若省略: 模型可能不知道如何收束长任务
        self.assertIn("后台命令", runtime_text)  # 新增代码+后台命令: 断言规则用中文解释该能力；若省略: 初学者难以理解它和同步命令的区别
    def test_runtime_instructions_define_current_info_policy(self) -> None:  # 新增代码+实时信息策略: 验证真实运行规则写明哪些知识可直接回答、哪些信息必须查工具；若省略: agent 可能继续把实时问题当稳定知识回答
        runtime_file = self._dynamic_prompt_file()  # 新增代码+实时信息策略: 定位真实 runtime_instructions.md；若省略: 测试无法覆盖用户实际运行时加载的规则文件
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+实时信息策略: 用 UTF-8 读取中文规则；若省略: Windows 默认编码可能导致中文断言不可靠
        self.assertIn("稳定知识可以直接回答", runtime_text)  # 新增代码+实时信息策略: 断言规则不会要求所有知识都联网；若省略: agent 可能变成低效的“所有问题都搜索”
        self.assertIn("今天、现在、当前、最新、实时", runtime_text)  # 新增代码+实时信息策略: 断言高时效触发词进入规则；若省略: 天气、旅行、政策等场景可能不触发搜索
        self.assertIn("必须优先调用可用的搜索、浏览器或 MCP 工具", runtime_text)  # 新增代码+实时信息策略: 断言规则要求可用工具优先；若省略: 模型可能只给过期训练知识
    def test_output_schema_only_includes_loaded_tool_pool_arguments(self) -> None:  # 新增代码+ToolArchitectureV2: 验证输出 schema 跟随当前工具池收窄；若没有这行代码，未加载工具参数仍可能混进模型输出
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolArchitectureV2: 创建临时工作区隔离 agent 文件；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolArchitectureV2: 把临时目录转成 Path；若没有这行代码，LearningAgent 初始化参数不够清楚
            fake_client = FakeMcpClient(tools=[  # 新增代码+ToolArchitectureV2: 构造两个参数互不相同的 deferred MCP 工具；若没有这行代码，测试不到参数隔离
                {  # 新增代码+ToolArchitectureV2: 开始定义普通 browser_open 工具；若没有这行代码，加载后 schema 没有 browser_open 专属参数来源
                    "name": "browser_open",  # 新增代码+ToolArchitectureV2: 使用普通浏览器打开工具名；若没有这行代码，select 目标工具名不会存在
                    "description": "Open browser",  # 新增代码+ToolArchitectureV2: 提供工具说明；若没有这行代码，catalog 元数据不完整
                    "inputSchema": {"type": "object", "properties": {"browser_open_only_url": {"type": "string"}, "browser_open_only_timeout_ms": {"type": "integer"}}, "required": ["browser_open_only_url"]},  # 新增代码+ToolArchitectureV2: 使用独有参数名方便检测是否进入输出 schema；若没有这行代码，参数串味断言没有目标字段
                },  # 新增代码+ToolArchitectureV2: 结束 browser_open 工具定义；若没有这行代码，工具列表语法不完整
                {  # 新增代码+ToolArchitectureV2: 开始定义真实 Chrome 连接工具；若没有这行代码，未加载高风险参数没有对照来源
                    "name": "browser_connect_real_chrome",  # 新增代码+ToolArchitectureV2: 使用真实 Chrome 风格工具名；若没有这行代码，confirm_real_profile 参数来源不贴近真实风险
                    "description": "Connect real Chrome",  # 新增代码+ToolArchitectureV2: 提供工具说明；若没有这行代码，catalog 元数据不完整
                    "inputSchema": {"type": "object", "properties": {"confirm_real_profile": {"type": "boolean"}}, "required": ["confirm_real_profile"]},  # 新增代码+ToolArchitectureV2: 使用真实 Chrome 专属确认参数；若没有这行代码，无法证明未加载高风险参数不会混入普通工具
                },  # 新增代码+ToolArchitectureV2: 结束真实 Chrome 工具定义；若没有这行代码，工具列表语法不完整
            ])  # 新增代码+ToolArchitectureV2: 结束 fake client 构造；若没有这行代码，registry 没有可启动的工具来源
            registry = McpToolRegistry({"browser_automation": fake_client})  # 新增代码+ToolArchitectureV2: 用浏览器自动化 server 名创建 registry；若没有这行代码，MCP 工具不会进入 catalog
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+ToolArchitectureV2: 创建允许启动 MCP 的 agent；若没有这行代码，无法读取当前工具池 schema
            initial_schema = CodexCliChatModel._output_schema(tools=agent._available_tool_schemas())  # 新增代码+ToolArchitectureV2: 基于默认工具池生成输出 schema；若没有这行代码，无法证明未加载参数默认不可见
            initial_arguments = self._merged_tool_argument_schema(initial_schema)["properties"]  # 修改代码+OutputProtocolV2: 汇总当前默认工具池各分支参数用于检查未加载 MCP 参数；若没有这行代码，测试会继续读取已移除的共享 arguments 路径
            self.assertNotIn("browser_open_only_url", initial_arguments)  # 新增代码+ToolArchitectureV2: 断言未加载 browser_open 参数不进入 schema；若没有这行代码，默认 pool 隐藏可能只影响工具名不影响参数
            self.assertNotIn("confirm_real_profile", initial_arguments)  # 新增代码+ToolArchitectureV2: 断言未加载真实 Chrome 确认参数不进入 schema；若没有这行代码，高风险参数可能继续串味
            agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "select:mcp__browser_automation__browser_open"}))  # 新增代码+ToolArchitectureV2: 通过 select 加载普通 browser_open；若没有这行代码，后续 schema 不会发生 pool 变化
            loaded_schema = CodexCliChatModel._output_schema(tools=agent._available_tool_schemas())  # 新增代码+ToolArchitectureV2: 基于加载后的工具池重新生成输出 schema；若没有这行代码，无法检查 select 后参数进入情况
            loaded_arguments = self._tool_argument_schema_for_name(loaded_schema, "mcp__browser_automation__browser_open")["properties"]  # 修改代码+OutputProtocolV2: 读取已加载 browser_open 分支自己的参数；若没有这行代码，测试无法证明 select 后参数是按工具名进入对应分支
            self.assertIn("browser_open_only_url", loaded_arguments)  # 新增代码+ToolArchitectureV2: 断言已加载工具的专属参数进入 schema；若没有这行代码，select 后模型仍无法输出目标参数
            self.assertNotIn("confirm_real_profile", loaded_arguments)  # 新增代码+ToolArchitectureV2: 断言未加载真实 Chrome 参数仍不进入 schema；若没有这行代码，参数串味问题没有被根治
    def test_system_prompt_contains_current_info_policy(self) -> None:  # 新增代码+实时信息策略: 验证系统提示词内置实时信息判断原则；若省略: 只靠外部规则文件时核心身份规则可能缺失
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+实时信息策略: 创建临时工作区隔离真实项目文件；若省略: 测试可能污染用户工作区
            workspace = Path(raw_dir)  # 新增代码+实时信息策略: 把临时目录转成 Path；若省略: LearningAgent 构造不够直接
            model = ToolCallingFakeModel([ModelMessage(text="不会真正调用模型。")])  # 新增代码+实时信息策略: 准备假模型满足构造参数；若省略: 测试会依赖真实模型
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+实时信息策略: 创建 agent 以构造系统提示词；若省略: 无法检查真实提示词生成逻辑
            messages = agent._build_initial_messages("今天去胡志明旅游要注意什么？")  # 新增代码+实时信息策略: 构造含“今天”的用户输入；若省略: 测试意图不够贴近真实触发场景
            system_content = str(messages[0]["content"])  # 新增代码+实时信息策略: 取出系统提示词文本；若省略: 后续断言没有检查对象
            self.assertIn("知识与实时信息策略", system_content)  # 新增代码+实时信息策略: 断言提示词有专门策略区块；若省略: 行为规则可能散落难以维护
            self.assertIn("稳定知识可以直接回答", system_content)  # 新增代码+实时信息策略: 断言提示词允许稳定知识直接回答；若省略: agent 可能误判所有知识都要联网
            self.assertIn("今天、现在、当前、最新、实时", system_content)  # 新增代码+实时信息策略: 断言提示词覆盖明确时效触发词；若省略: 今天天气、旅行政策等问题可能不查工具
    def test_builtin_tools_include_todo_read_and_todo_write(self) -> None:  # 新增代码+TodoWrite: 验证内置工具列表暴露 todo_read 和 todo_write；若省略: 模型可能永远看不到任务清单工具
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+TodoWrite: 从内置工具 schema 中收集工具名；若省略: 无法判断模型可见工具是否包含 Todo 工具
        self.assertIn("todo_read", tool_names)  # 新增代码+TodoWrite: 断言模型可以请求读取任务清单；若省略: 只写不能读会让长任务恢复状态困难
        self.assertIn("todo_write", tool_names)  # 新增代码+TodoWrite: 断言模型可以请求写入任务清单；若省略: agent 无法像 Claude Code 一样维护任务状态
    def test_per_tool_output_schema_keeps_browser_open_arguments_isolated(self) -> None:  # 新增代码+OutputProtocolV2: 验证同一工具池内 browser_open 不会继承真实 Chrome 参数；若没有这行代码，用户最关心的浏览器参数串味会回归
        fake_tools = [  # 新增代码+OutputProtocolV2: 构造两个同池浏览器工具模拟普通打开和真实 Chrome 连接；若没有这行代码，测试无法覆盖参数隔离
            {  # 新增代码+OutputProtocolV2: 定义 browser_open 工具 schema；若没有这行代码，测试没有普通浏览器工具分支
                "type": "function",  # 新增代码+OutputProtocolV2: 使用 OpenAI-compatible function 工具格式；若没有这行代码，输出 schema 收集不到工具参数
                "function": {  # 新增代码+OutputProtocolV2: 开始 function 定义；若没有这行代码，工具名和参数没有容器
                    "name": "mcp__browser_automation__browser_open",  # 新增代码+OutputProtocolV2: 声明普通打开页面工具名；若没有这行代码，无法定位 browser_open 分支
                    "description": "Open a page",  # 新增代码+OutputProtocolV2: 提供工具说明；若没有这行代码，schema 仍可运行但工具不贴近真实结构
                    "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},  # 新增代码+OutputProtocolV2: 只给 browser_open 声明 url；若没有这行代码，无法证明它不该收到 confirm_real_profile
                },  # 新增代码+OutputProtocolV2: 结束 browser_open function 定义；若没有这行代码，工具 schema 语法不完整
            },  # 新增代码+OutputProtocolV2: 结束 browser_open 工具条目；若没有这行代码，fake_tools 列表语法不完整
            {  # 新增代码+OutputProtocolV2: 定义真实 Chrome 连接工具 schema；若没有这行代码，测试没有高风险真实 Chrome 分支
                "type": "function",  # 新增代码+OutputProtocolV2: 使用 OpenAI-compatible function 工具格式；若没有这行代码，输出 schema 收集不到工具参数
                "function": {  # 新增代码+OutputProtocolV2: 开始 function 定义；若没有这行代码，工具名和参数没有容器
                    "name": "mcp__browser_automation__browser_connect_real_chrome",  # 新增代码+OutputProtocolV2: 声明真实 Chrome 连接工具名；若没有这行代码，无法定位真实 Chrome 分支
                    "description": "Connect real Chrome",  # 新增代码+OutputProtocolV2: 提供工具说明；若没有这行代码，schema 仍可运行但工具不贴近真实结构
                    "parameters": {"type": "object", "properties": {"confirm_real_profile": {"type": "boolean"}}, "required": ["confirm_real_profile"]},  # 新增代码+OutputProtocolV2: 只给真实 Chrome 声明显式确认参数；若没有这行代码，无法证明 browser_open 不该继承此字段
                },  # 新增代码+OutputProtocolV2: 结束真实 Chrome function 定义；若没有这行代码，工具 schema 语法不完整
            },  # 新增代码+OutputProtocolV2: 结束真实 Chrome 工具条目；若没有这行代码，fake_tools 列表语法不完整
        ]  # 新增代码+OutputProtocolV2: 结束 fake 工具池；若没有这行代码，测试数据结构不完整
        schema = CodexCliChatModel._output_schema(tools=fake_tools)  # 新增代码+OutputProtocolV2: 为同一工具池生成输出 schema；若没有这行代码，被测分支逻辑不会运行
        open_arguments = self._tool_argument_schema_for_name(schema, "mcp__browser_automation__browser_open")  # 新增代码+OutputProtocolV2: 读取 browser_open 自己的 arguments schema；若没有这行代码，无法检查参数隔离
        real_chrome_arguments = self._tool_argument_schema_for_name(schema, "mcp__browser_automation__browser_connect_real_chrome")  # 新增代码+OutputProtocolV2: 读取真实 Chrome 自己的 arguments schema；若没有这行代码，无法对比两个分支
        self.assertIn("url", open_arguments["properties"])  # 新增代码+OutputProtocolV2: 断言 browser_open 保留自己的 url 参数；若没有这行代码，隔离实现可能误删正确参数
        self.assertNotIn("confirm_real_profile", open_arguments["properties"])  # 新增代码+OutputProtocolV2: 断言 browser_open 不包含真实 Chrome 确认参数；若没有这行代码，参数串味不会被发现
        self.assertIn("confirm_real_profile", real_chrome_arguments["properties"])  # 新增代码+OutputProtocolV2: 断言真实 Chrome 分支保留自己的确认参数；若没有这行代码，高风险工具可能无法输出必要确认字段
        self.assertNotIn("url", real_chrome_arguments["properties"])  # 新增代码+OutputProtocolV2: 断言真实 Chrome 分支不继承 browser_open 的 url；若没有这行代码，反向参数串味不会被发现
    def test_builtin_tools_include_background_command_tools(self) -> None:  # 新增代码+后台命令: 验证内置工具列表暴露后台命令三件套；若省略: 模型可能看不到启动、读取、停止后台进程的能力
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+后台命令: 从内置工具 schema 中收集工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("start_background_command", tool_names)  # 新增代码+后台命令: 断言模型可以启动后台命令；若省略: 长时间运行的测试或服务无法后台执行
        self.assertIn("read_background_command", tool_names)  # 新增代码+后台命令: 断言模型可以读取后台命令输出；若省略: agent 无法观察长任务进度
        self.assertIn("stop_background_command", tool_names)  # 新增代码+后台命令: 断言模型可以停止后台命令；若省略: 长任务失控时无法由工具层收束
    def test_builtin_tools_include_notebook_tools(self) -> None:  # 新增代码+Notebook工具: 验证内置工具列表暴露 notebook_read 和 notebook_edit；若省略: 模型可能永远看不到 Notebook 读写能力
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+Notebook工具: 从真实内置工具 schema 中收集工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("notebook_read", tool_names)  # 新增代码+Notebook工具: 断言模型可以请求读取 .ipynb 内容；若省略: NotebookRead 工具缺失不会被测试发现
        self.assertIn("notebook_edit", tool_names)  # 新增代码+Notebook工具: 断言模型可以请求编辑 .ipynb cell；若省略: NotebookEdit 工具缺失不会被测试发现
    def test_builtin_tools_include_tool_search(self) -> None:  # 新增代码+ToolSearch: 验证内置工具列表暴露 tool_search；若省略: 模型在工具变多后无法主动发现合适工具
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+ToolSearch: 收集真实内置工具名；若省略: 测试无法判断 tool_search 是否进入模型可见 schema
        self.assertIn("tool_search", tool_names)  # 新增代码+ToolSearch: 断言模型可以请求搜索工具；若省略: ToolSearch 缺失不会被回归测试发现
    def test_builtin_tools_include_skill_tools(self) -> None:  # 新增代码+SkillLoad: 验证内置工具列表暴露 skill_list 和 skill_load；若省略: 模型无法主动发现和加载本地 skill
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+SkillLoad: 收集真实内置工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("skill_list", tool_names)  # 新增代码+SkillLoad: 断言模型可以请求列出本地 skills；若省略: skill_list 缺失不会被测试发现
        self.assertIn("skill_load", tool_names)  # 新增代码+SkillLoad: 断言模型可以请求加载本地 skill；若省略: skill_load 缺失不会被测试发现
    def test_builtin_tools_include_ask_user_question(self) -> None:  # 新增代码+AskUserQuestion: 验证内置工具列表暴露 ask_user_question；若省略: 模型无法用结构化方式向用户澄清需求
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+AskUserQuestion: 收集真实内置工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("ask_user_question", tool_names)  # 新增代码+AskUserQuestion: 断言模型可以请求结构化提问；若省略: 工具缺失不会被测试发现
    def test_builtin_tools_include_task_tool(self) -> None:  # 新增代码+TaskAgent: 验证内置工具列表暴露 task；若省略: 模型无法请求子 agent 执行子任务
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+TaskAgent: 收集真实内置工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("task", tool_names)  # 新增代码+TaskAgent: 断言模型可以请求 task 子 agent；若省略: task 缺失不会被测试发现
    def test_task_runs_child_agent_with_allowed_tools(self) -> None:  # 新增代码+TaskAgent: 验证 task 会启动子 agent 且按 allowed_tools 限制工具；若省略: 子 agent 核心委派能力没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TaskAgent: 创建临时工作区隔离子 agent 文件和日志；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+TaskAgent: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            model = RecordingToolNameFakeModel(ModelMessage(text="子任务完成：已经完成只读分析。"))  # 新增代码+TaskAgent: 创建会记录子 agent 可见工具的假模型；若省略: 无法验证 allowed_tools 是否真的生效
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+TaskAgent: 创建主 agent；若省略: 无法通过工具路由执行 task
            output = agent._execute_tool(ToolCall(name="task", arguments={"prompt": "只读分析 memory.md", "allowed_tools": ["read_file"], "max_turns": 1}))  # 新增代码+TaskAgent: 通过 task 工具启动一个只允许 read_file 的子 agent；若省略: 无法验证委派执行路径
            self.assertIn("task 成功", output)  # 新增代码+TaskAgent: 断言 task 返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("子任务完成", output)  # 新增代码+TaskAgent: 断言子 agent 的最终回答进入 task 输出；若省略: 主 agent 无法拿到子任务摘要
            self.assertEqual(len(model.received_tool_names), 1)  # 新增代码+TaskAgent: 断言子 agent 调用模型一次；若省略: 无法确认 task 确实执行了子 agent
            self.assertIn("read_file", model.received_tool_names[0])  # 新增代码+TaskAgent: 断言允许的 read_file 暴露给子 agent；若省略: allowed_tools 可能误删目标工具
            self.assertNotIn("write_file", model.received_tool_names[0])  # 新增代码+TaskAgent: 断言未允许的 write_file 不暴露；若省略: 子 agent 可能越权写文件
            self.assertNotIn("task", model.received_tool_names[0])  # 新增代码+TaskAgent: 断言子 agent 默认不能递归创建 task；若省略: 子任务可能无限嵌套
    def test_allowed_tools_execution_guard_blocks_hidden_tool_call(self) -> None:  # 新增代码+ToolPolicyV2: 验证 allowed_tools 不只过滤展示层，也会阻止执行层越权；若没有这行代码，子 agent 伪造隐藏工具名仍可能执行
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolPolicyV2: 创建临时工作区隔离写文件测试；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+ToolPolicyV2: 把临时目录转成 Path 对象；若没有这行代码，后续路径拼接不够清楚
            permission_requests: list[str] = []  # 新增代码+ToolPolicyV2: 记录权限请求文本；若没有这行代码，无法证明越权调用没有进入权限弹窗
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: permission_requests.append(action) or True, allowed_tool_names={"read_file"})  # 新增代码+ToolPolicyV2: 创建只允许 read_file 的 agent；若没有这行代码，无法模拟子 agent allowed_tools 边界
            output = agent._execute_tool(ToolCall(name="write_file", arguments={"path": "blocked.txt", "content": "不应该写入"}))  # 新增代码+ToolPolicyV2: 直接尝试执行白名单外的 write_file；若没有这行代码，执行期白名单守卫没有测试输入
            self.assertIn("allowed_tools", output)  # 新增代码+ToolPolicyV2: 断言失败原因来自 allowed_tools 边界；若没有这行代码，其他失败可能被误当成守卫成功
            self.assertFalse((workspace / "blocked.txt").exists())  # 新增代码+ToolPolicyV2: 断言目标文件没有被写入；若没有这行代码，文本返回失败但副作用已发生不会被发现
            self.assertEqual(permission_requests, [])  # 新增代码+ToolPolicyV2: 断言越权工具没有进入权限确认；若没有这行代码，白名单外调用仍打扰用户或继续分发不会暴露
    def test_builtin_tools_include_task_lifecycle_tools(self) -> None:  # 新增代码+TaskLifecycle: 验证内置工具列表暴露 task_output 和 task_stop；若省略: 模型无法查询或停止子任务
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+TaskLifecycle: 收集真实内置工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("task_output", tool_names)  # 新增代码+TaskLifecycle: 断言模型可以请求读取子任务输出；若省略: task_output 缺失不会被测试发现
        self.assertIn("task_stop", tool_names)  # 新增代码+TaskLifecycle: 断言模型可以请求停止子任务；若省略: task_stop 缺失不会被测试发现
    def test_builtin_tools_include_task_management_tools(self) -> None:  # 新增代码+TaskManagement: 验证内置工具列表暴露 task_list/task_get/task_update；若省略: 模型可能看不到多任务管理入口
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+TaskManagement: 收集真实内置工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("task_list", tool_names)  # 新增代码+TaskManagement: 断言模型可以列出所有子任务；若省略: task_list 缺失不会被测试发现
        self.assertIn("task_get", tool_names)  # 新增代码+TaskManagement: 断言模型可以读取单个子任务详情；若省略: task_get 缺失不会被测试发现
        self.assertIn("task_update", tool_names)  # 新增代码+TaskManagement: 断言模型可以更新子任务元信息；若省略: task_update 缺失不会被测试发现
    def test_builtin_tools_include_team_communication_tools(self) -> None:  # 修改代码+TeamCommunicationLifecycle: 验证内置工具列表暴露 team 创建、通信、读取确认和删除工具；若省略: 模型可能看不到完整 team 生命周期入口
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+TeamCommunication: 收集真实内置工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("team_create", tool_names)  # 新增代码+TeamCommunication: 断言模型可以创建教学版 peer；若省略: team_create 缺失不会被测试发现
        self.assertIn("send_message", tool_names)  # 新增代码+TeamCommunication: 断言模型可以向 peer 发送消息；若省略: send_message 缺失不会被测试发现
        self.assertIn("list_peers", tool_names)  # 新增代码+TeamCommunication: 断言模型可以查看 peer 列表；若省略: list_peers 缺失不会被测试发现
        self.assertIn("read_peer_messages", tool_names)  # 新增代码+TeamCommunicationLifecycle: 断言模型可以读取 peer inbox；若省略: read_peer_messages 缺失不会被测试发现
        self.assertIn("ack_peer_message", tool_names)  # 新增代码+TeamCommunicationLifecycle: 断言模型可以确认某条 peer 消息；若省略: ack_peer_message 缺失不会被测试发现
        self.assertIn("team_delete", tool_names)  # 新增代码+TeamCommunicationLifecycle: 断言模型可以删除教学版 peer；若省略: team_delete 缺失不会被测试发现
        self.assertIn("team_start_task", tool_names)  # 新增代码+TeamTaskBinding: 断言模型可以把 peer 绑定到后台 task；若省略: team_start_task 缺失不会被测试发现
    def test_builtin_tools_include_plan_mode_tools(self) -> None:  # 新增代码+PlanMode: 验证内置工具列表暴露 enter_plan_mode 和 exit_plan_mode；若省略: 模型无法进入或退出计划模式
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+PlanMode: 收集真实内置工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("enter_plan_mode", tool_names)  # 新增代码+PlanMode: 断言模型可以请求进入计划模式；若省略: enter_plan_mode 缺失不会被测试发现
        self.assertIn("exit_plan_mode", tool_names)  # 新增代码+PlanMode: 断言模型可以请求输出计划并等待确认；若省略: exit_plan_mode 缺失不会被测试发现
        self.assertIn("verify_plan_execution", tool_names)  # 新增代码+PlanVerification: 断言模型可以请求验证计划执行结果；若省略: verify_plan_execution 缺失不会被测试发现
    def test_builtin_tools_include_worktree_tools(self) -> None:  # 新增代码+WorktreeIsolation: 验证内置工具列表暴露进入和退出工作区隔离状态工具；若省略: 模型看不到 worktree 隔离入口不会被测试发现
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+WorktreeIsolation: 收集真实内置工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("enter_worktree", tool_names)  # 新增代码+WorktreeIsolation: 断言模型可以请求进入 worktree 隔离状态；若省略: enter_worktree 缺失不会被测试发现
        self.assertIn("exit_worktree", tool_names)  # 新增代码+WorktreeIsolation: 断言模型可以请求退出 worktree 隔离状态；若省略: exit_worktree 缺失不会被测试发现
    def test_builtin_tools_include_lsp_tools(self) -> None:  # 新增代码+LSP工具: 验证内置工具列表暴露轻量 LSP 符号、定义和诊断工具；若省略: 模型看不到代码理解入口不会被测试发现
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+LSP工具: 收集真实内置工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("lsp_symbols", tool_names)  # 新增代码+LSP工具: 断言模型可以请求读取文件符号；若省略: lsp_symbols 缺失不会被测试发现
        self.assertIn("lsp_definition", tool_names)  # 新增代码+LSP工具: 断言模型可以请求定位符号定义；若省略: lsp_definition 缺失不会被测试发现
        self.assertIn("lsp_diagnostics", tool_names)  # 新增代码+LSP工具: 断言模型可以请求读取语法诊断；若省略: lsp_diagnostics 缺失不会被测试发现
    def test_builtin_tools_include_repl_tool(self) -> None:  # 新增代码+REPL工具: 验证内置工具列表暴露安全批量编排工具；若省略: 模型看不到 REPL 入口不会被测试发现
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+REPL工具: 收集真实内置工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("repl", tool_names)  # 新增代码+REPL工具: 断言模型可以请求批量执行安全只读工具；若省略: repl 缺失不会被测试发现
    def test_builtin_tools_include_cron_monitor_tools(self) -> None:  # 新增代码+CronMonitor: 验证内置工具列表暴露定时和监控最小版工具；若省略: 模型看不到 Cron/Monitor 入口不会被测试发现
        tool_names = [schema["function"]["name"] for schema in TOOL_SCHEMAS]  # 新增代码+CronMonitor: 收集真实内置工具名；若省略: 无法断言模型可见工具集合
        self.assertIn("cron_create", tool_names)  # 新增代码+CronMonitor: 断言模型可以登记教学版定时任务；若省略: cron_create 缺失不会被测试发现
        self.assertIn("cron_list", tool_names)  # 新增代码+CronMonitor: 断言模型可以列出教学版定时任务；若省略: cron_list 缺失不会被测试发现
        self.assertIn("cron_delete", tool_names)  # 新增代码+CronMonitor: 断言模型可以删除教学版定时任务记录；若省略: cron_delete 缺失不会被测试发现
        self.assertIn("monitor", tool_names)  # 新增代码+CronMonitor: 断言模型可以登记和管理教学版监控记录；若省略: monitor 缺失不会被测试发现
    def test_lsp_symbols_reads_python_classes_methods_and_functions(self) -> None:  # 新增代码+LSP工具: 验证轻量 LSP 能读取 Python 类、方法和函数符号；若省略: 符号列表核心行为没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+LSP工具: 创建临时工作区隔离测试文件；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+LSP工具: 把临时目录转成 Path；若省略: agent 构造不够清晰
            source_path = workspace / "sample.py"  # 新增代码+LSP工具: 定义 Python 测试文件路径；若省略: LSP 工具没有真实输入文件
            source_path.write_text("class Greeter:\n    def greet(self):\n        return 'hi'\n\ndef helper():\n    return Greeter()\n", encoding="utf-8")  # 新增代码+LSP工具: 写入包含类、方法和函数的源码；若省略: 无法验证 AST 符号提取
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+LSP工具: 创建测试 agent；若省略: 无法通过工具路由执行 lsp_symbols
            output = agent._execute_tool(ToolCall(name="lsp_symbols", arguments={"path": "sample.py", "max_results": 10}))  # 新增代码+LSP工具: 请求读取 Python 文件符号；若省略: lsp_symbols 成功路径没有测试输入
            self.assertIn("lsp_symbols 成功", output)  # 新增代码+LSP工具: 断言工具返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("symbol_count=3", output)  # 新增代码+LSP工具: 断言识别出三个符号；若省略: 漏掉方法或函数不易被发现
            self.assertIn("kind=class name=Greeter line=1", output)  # 新增代码+LSP工具: 断言类定义行号进入输出；若省略: 类符号定位可能退化
            self.assertIn("kind=method name=greet line=2 container=Greeter", output)  # 新增代码+LSP工具: 断言方法符号带容器类名；若省略: 模型难以区分类方法和顶层函数
            self.assertIn("kind=function name=helper line=5", output)  # 新增代码+LSP工具: 断言顶层函数定义进入输出；若省略: 函数符号定位可能退化
    def test_lsp_definition_finds_python_symbol(self) -> None:  # 新增代码+LSP工具: 验证轻量 LSP 能按名称定位 Python 符号定义；若省略: 定义跳转能力没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+LSP工具: 创建临时工作区隔离测试文件；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+LSP工具: 把临时目录转成 Path；若省略: agent 构造不够清晰
            source_path = workspace / "sample.py"  # 新增代码+LSP工具: 定义 Python 测试文件路径；若省略: LSP 定义工具没有真实输入文件
            source_path.write_text("class Greeter:\n    def greet(self):\n        return 'hi'\n\ndef helper():\n    return Greeter()\n", encoding="utf-8")  # 新增代码+LSP工具: 写入包含 helper 定义的源码；若省略: 无法验证定义定位
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+LSP工具: 创建测试 agent；若省略: 无法通过工具路由执行 lsp_definition
            output = agent._execute_tool(ToolCall(name="lsp_definition", arguments={"path": "sample.py", "symbol": "helper"}))  # 新增代码+LSP工具: 请求定位 helper 定义；若省略: lsp_definition 成功路径没有测试输入
            self.assertIn("lsp_definition 成功", output)  # 新增代码+LSP工具: 断言工具返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("match_count=1", output)  # 新增代码+LSP工具: 断言只找到一个匹配定义；若省略: 重复或漏匹配不易被发现
            self.assertIn("kind=function name=helper line=5", output)  # 新增代码+LSP工具: 断言定义类型、名称和行号进入输出；若省略: 模型无法跳到正确定义位置
    def test_lsp_diagnostics_reports_python_syntax_error(self) -> None:  # 新增代码+LSP工具: 验证轻量 LSP 能把 Python 语法错误转成诊断输出；若省略: 诊断核心行为没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+LSP工具: 创建临时工作区隔离测试文件；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+LSP工具: 把临时目录转成 Path；若省略: agent 构造不够清晰
            source_path = workspace / "broken.py"  # 新增代码+LSP工具: 定义含语法错误的 Python 文件路径；若省略: 诊断工具没有真实错误输入
            source_path.write_text("def broken(:\n    pass\n", encoding="utf-8")  # 新增代码+LSP工具: 写入稳定触发 SyntaxError 的源码；若省略: 无法验证错误诊断输出
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+LSP工具: 创建测试 agent；若省略: 无法通过工具路由执行 lsp_diagnostics
            output = agent._execute_tool(ToolCall(name="lsp_diagnostics", arguments={"path": "broken.py"}))  # 新增代码+LSP工具: 请求读取语法诊断；若省略: lsp_diagnostics 错误路径没有测试输入
            self.assertIn("lsp_diagnostics 成功", output)  # 新增代码+LSP工具: 断言诊断工具返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("diagnostic_count=1", output)  # 新增代码+LSP工具: 断言输出一个诊断；若省略: 语法错误可能被吞掉
            self.assertIn("severity=error", output)  # 新增代码+LSP工具: 断言诊断严重级别进入输出；若省略: 模型难以判断问题严重性
            self.assertIn("line=1", output)  # 新增代码+LSP工具: 断言诊断行号进入输出；若省略: 模型无法定位错误行
    def test_lsp_tools_reject_workspace_escape_path(self) -> None:  # 新增代码+LSP工具: 验证 LSP 工具不能读取工作区外路径；若省略: 模型可能借 LSP 工具越界读取文件
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+LSP工具: 创建临时工作区隔离路径边界测试；若省略: 越界路径会依赖真实目录结构
            workspace = Path(raw_dir)  # 新增代码+LSP工具: 把临时目录转成 Path；若省略: agent 构造不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+LSP工具: 创建测试 agent；若省略: 无法执行 lsp_symbols
            output = agent._execute_tool(ToolCall(name="lsp_symbols", arguments={"path": "../outside.py"}))  # 新增代码+LSP工具: 请求读取工作区外路径；若省略: 路径越界分支没有测试输入
            self.assertIn("lsp_symbols 失败", output)  # 新增代码+LSP工具: 断言越界读取失败；若省略: 工具可能误报成功
            self.assertIn("工作区内", output)  # 新增代码+LSP工具: 断言错误信息解释工作区边界；若省略: 模型难以修正 path 参数
    def test_repl_runs_safe_tool_batch_in_order(self) -> None:  # 新增代码+REPL工具: 验证 REPL 最小版能顺序执行安全只读工具批次；若省略: 批量编排核心行为没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+REPL工具: 创建临时工作区隔离源码文件；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+REPL工具: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            source_path = workspace / "sample.py"  # 新增代码+REPL工具: 定义 Python 测试文件路径；若省略: lsp_symbols 子调用没有真实输入
            source_path.write_text("def helper():\n    return 1\n", encoding="utf-8")  # 新增代码+REPL工具: 写入简单函数源码；若省略: 符号查询无法证明批量工具真的执行
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+REPL工具: 创建测试 agent；若省略: 无法通过工具路由执行 repl
            output = agent._execute_tool(ToolCall(name="repl", arguments={"calls": [{"tool_name": "tool_search", "arguments": {"query": "lsp", "max_results": 3}}, {"tool_name": "lsp_symbols", "arguments": {"path": "sample.py", "max_results": 10}}], "max_output_chars": 4000}))  # 新增代码+REPL工具: 请求批量执行工具搜索和符号读取；若省略: REPL 成功路径没有测试输入
            self.assertIn("repl 成功", output)  # 新增代码+REPL工具: 断言批量工具返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("call_count=2", output)  # 新增代码+REPL工具: 断言执行了两个子调用；若省略: 漏执行某个子调用不易被发现
            self.assertIn("[1] tool_name=tool_search", output)  # 新增代码+REPL工具: 断言第一个子调用按顺序执行；若省略: 批量顺序可能退化
            self.assertIn("[2] tool_name=lsp_symbols", output)  # 新增代码+REPL工具: 断言第二个子调用按顺序执行；若省略: 批量顺序可能退化
            self.assertIn("tool_search 成功", output)  # 新增代码+REPL工具: 断言 tool_search 子结果进入 REPL 输出；若省略: REPL 可能只显示调用名不显示证据
            self.assertIn("kind=function name=helper line=1", output)  # 新增代码+REPL工具: 断言 lsp_symbols 子结果进入 REPL 输出；若省略: REPL 可能没有真正执行第二个工具
    def test_repl_rejects_unsafe_write_tool_without_side_effect(self) -> None:  # 新增代码+REPL工具: 验证 REPL 不允许批量执行写文件等副作用工具；若省略: REPL 可能绕过权限边界写文件
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+REPL工具: 创建临时工作区隔离副作用测试；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+REPL工具: 把临时目录转成 Path；若省略: 后续路径断言不够清晰
            target_path = workspace / "unsafe.txt"  # 新增代码+REPL工具: 定义不应该被创建的目标文件；若省略: 无法证明拒绝后没有副作用
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+REPL工具: 创建测试 agent 且即使权限允许也应被白名单拦截；若省略: 无法验证 REPL 自身边界
            output = agent._execute_tool(ToolCall(name="repl", arguments={"calls": [{"tool_name": "write_file", "arguments": {"path": "unsafe.txt", "content": "不应该写入"}}]}))  # 新增代码+REPL工具: 尝试通过 REPL 调用写文件；若省略: 副作用拒绝分支没有测试输入
            self.assertIn("repl 失败", output)  # 新增代码+REPL工具: 断言不安全批量调用被拒绝；若省略: 工具可能误报成功
            self.assertIn("安全白名单", output)  # 新增代码+REPL工具: 断言错误说明来自白名单边界；若省略: 模型难以修正子调用工具名
            self.assertFalse(target_path.exists())  # 新增代码+REPL工具: 断言拒绝后文件没有被创建；若省略: 表面失败但实际写入的严重回归不会被发现
    def test_repl_limits_batch_size(self) -> None:  # 新增代码+REPL工具: 验证 REPL 限制单次批量调用数量；若省略: 模型可能一次塞入过多工具结果撑爆上下文
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+REPL工具: 创建临时工作区隔离批量大小测试；若省略: 测试可能受真实状态影响
            workspace = Path(raw_dir)  # 新增代码+REPL工具: 把临时目录转成 Path；若省略: agent 构造不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+REPL工具: 创建测试 agent；若省略: 无法执行 repl
            calls = [{"tool_name": "tool_search", "arguments": {"query": "read", "max_results": 1}} for _ in range(6)]  # 新增代码+REPL工具: 构造超过上限的六个安全调用；若省略: 数量上限分支没有测试输入
            output = agent._execute_tool(ToolCall(name="repl", arguments={"calls": calls}))  # 新增代码+REPL工具: 请求执行超大批次；若省略: 无法验证上限错误
            self.assertIn("repl 失败", output)  # 新增代码+REPL工具: 断言超出上限时失败；若省略: 工具可能继续执行过长批次
            self.assertIn("最多 5", output)  # 新增代码+REPL工具: 断言错误信息说明数量上限；若省略: 模型难以缩小 calls 数组
    def test_agent_searches_builtin_tool_descriptions(self) -> None:  # 新增代码+ToolSearch: 验证 tool_search 能按说明搜索内置工具；若省略: 只有工具名匹配会导致模型难以用自然语言发现工具
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ToolSearch: 创建临时工作区隔离 agent 文件；若省略: 测试可能影响真实 memory 或日志
            workspace = Path(raw_dir)  # 新增代码+ToolSearch: 转成 Path 供 agent 使用；若省略: 路径处理表达不直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+ToolSearch: 创建无 MCP 的 agent；若省略: 无法验证纯内置工具搜索
            output = agent._execute_tool(ToolCall(name="tool_search", arguments={"query": "Notebook cell", "max_results": 3}))  # 新增代码+ToolSearch: 用说明中的 Notebook cell 关键词搜索；若省略: 不能覆盖描述文本匹配
            self.assertIn("notebook_read", output)  # 新增代码+ToolSearch: 断言读取 Notebook 工具能被发现；若省略: 描述搜索退化不会被发现
            self.assertIn("notebook_edit", output)  # 新增代码+ToolSearch: 断言编辑 Notebook 工具能被发现；若省略: 多个相关工具排序或收集问题不会暴露
    def test_agent_reads_notebook_cells(self) -> None:  # 新增代码+Notebook工具: 验证 agent 能读取 notebook cell 摘要；若省略: NotebookRead 的核心可读输出没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Notebook工具: 创建临时工作区隔离 .ipynb 测试文件；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+Notebook工具: 把临时目录转成 Path；若省略: 后续路径拼接不够清晰
            notebook_path = workspace / "demo.ipynb"  # 新增代码+Notebook工具: 定义测试 notebook 文件路径；若省略: 工具没有真实 .ipynb 输入
            notebook_payload = {  # 新增代码+Notebook工具: 构造一个最小合法 notebook JSON；若省略: 无法验证真实 JSON 读取逻辑
                "cells": [  # 新增代码+Notebook工具: cells 保存 notebook 的单元格数组；若省略: notebook_read 没有可展示内容
                    {"cell_type": "markdown", "metadata": {}, "source": ["# 标题\n", "说明"]},  # 新增代码+Notebook工具: 第一个 markdown cell 用于验证中文和多行 source；若省略: markdown 读取场景缺失
                    {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": "print('hi')\n"},  # 新增代码+Notebook工具: 第二个 code cell 用于验证字符串 source；若省略: code 读取场景缺失
                ],  # 新增代码+Notebook工具: cells 数组结束；若省略: notebook JSON 结构不完整
                "metadata": {},  # 新增代码+Notebook工具: metadata 是 notebook 标准字段；若省略: 测试文件不像真实 .ipynb
                "nbformat": 4,  # 新增代码+Notebook工具: nbformat 指定 notebook 主版本；若省略: 读取摘要缺少版本信息
                "nbformat_minor": 5,  # 新增代码+Notebook工具: nbformat_minor 指定 notebook 次版本；若省略: 读取摘要缺少版本信息
            }  # 新增代码+Notebook工具: notebook JSON 构造结束；若省略: 变量无法传给写文件逻辑
            notebook_path.write_text(json.dumps(notebook_payload, ensure_ascii=False), encoding="utf-8")  # 新增代码+Notebook工具: 把 notebook 写入临时工作区；若省略: notebook_read 会因文件不存在失败
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+Notebook工具: 创建允许权限的 agent；若省略: 无法直接调用内置工具
            output = agent._execute_tool(ToolCall(name="notebook_read", arguments={"path": "demo.ipynb"}))  # 新增代码+Notebook工具: 通过工具路由读取 notebook；若省略: 无法验证 _execute_tool 分发路径
            self.assertIn("notebook_read 成功", output)  # 新增代码+Notebook工具: 断言读取成功前缀；若省略: 工具失败可能被后续内容断言掩盖
            self.assertIn("cell 0", output)  # 新增代码+Notebook工具: 断言输出包含第一个 cell 索引；若省略: 模型难以知道后续编辑哪个 cell
            self.assertIn("markdown", output)  # 新增代码+Notebook工具: 断言输出包含 markdown 类型；若省略: cell 类型可能丢失
            self.assertIn("标题", output)  # 新增代码+Notebook工具: 断言中文 source 被保留；若省略: 中文 notebook 内容可能乱码而不被发现
            self.assertIn("print('hi')", output)  # 新增代码+Notebook工具: 断言 code cell 预览进入输出；若省略: 代码单元格可能没有被读取
    def test_agent_edits_notebook_cell_with_permission(self) -> None:  # 新增代码+Notebook工具: 验证 agent 能在权限确认后替换指定 cell 的 source；若省略: NotebookEdit 核心写入路径没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Notebook工具: 创建临时工作区隔离 notebook 写入副作用；若省略: 测试可能修改真实文件
            workspace = Path(raw_dir)  # 新增代码+Notebook工具: 把临时目录转成 Path；若省略: 后续路径表达不够清楚
            notebook_path = workspace / "demo.ipynb"  # 新增代码+Notebook工具: 定义要编辑的 notebook 路径；若省略: 工具没有目标文件
            notebook_payload = {  # 新增代码+Notebook工具: 构造包含两个 cell 的 notebook；若省略: 无法验证按索引编辑第二个 cell
                "cells": [  # 新增代码+Notebook工具: cells 保存 notebook 单元格；若省略: 编辑工具没有 cell 可改
                    {"cell_type": "markdown", "metadata": {}, "source": ["# 标题\n"]},  # 新增代码+Notebook工具: 第一个 cell 保持不变用于验证索引定位；若省略: 无法证明只改目标 cell
                    {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": ["print('old')\n"]},  # 新增代码+Notebook工具: 第二个 cell 是编辑目标；若省略: 无法验证 source 替换
                ],  # 新增代码+Notebook工具: cells 数组结束；若省略: JSON 结构不完整
                "metadata": {},  # 新增代码+Notebook工具: metadata 是 notebook 标准字段；若省略: 测试文件不像真实 .ipynb
                "nbformat": 4,  # 新增代码+Notebook工具: nbformat 指定 notebook 主版本；若省略: 文件结构不完整
                "nbformat_minor": 5,  # 新增代码+Notebook工具: nbformat_minor 指定 notebook 次版本；若省略: 文件结构不完整
            }  # 新增代码+Notebook工具: notebook JSON 构造结束；若省略: 变量无法落盘
            notebook_path.write_text(json.dumps(notebook_payload, ensure_ascii=False), encoding="utf-8")  # 新增代码+Notebook工具: 写入待编辑 notebook；若省略: notebook_edit 会因文件不存在失败
            permission_requests: list[str] = []  # 新增代码+Notebook工具: 记录权限请求；若省略: 无法确认编辑 notebook 前经过用户确认
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: permission_requests.append(action) or True)  # 新增代码+Notebook工具: 创建 agent 并捕获权限文本；若省略: 无法验证权限和编辑结果
            output = agent._execute_tool(ToolCall(name="notebook_edit", arguments={"path": "demo.ipynb", "cell_index": 1, "source": "print('updated')\n"}))  # 新增代码+Notebook工具: 请求替换第二个 cell source；若省略: 编辑工具不会被执行
            updated_payload = json.loads(notebook_path.read_text(encoding="utf-8"))  # 新增代码+Notebook工具: 读取编辑后的 notebook JSON；若省略: 只看返回文本无法证明文件真的改变
            self.assertIn("notebook_edit 成功", output)  # 新增代码+Notebook工具: 断言工具返回成功；若省略: 失败输出可能被后续文件断言误解
            self.assertIn("编辑 Notebook cell", permission_requests[0])  # 新增代码+Notebook工具: 断言写入前弹出明确权限说明；若省略: notebook_edit 可能绕过权限层
            self.assertEqual(updated_payload["cells"][0]["source"], ["# 标题\n"])  # 新增代码+Notebook工具: 断言非目标 cell 保持不变；若省略: 编辑工具可能误改其他 cell
            self.assertEqual(updated_payload["cells"][1]["source"], ["print('updated')\n"])  # 新增代码+Notebook工具: 断言目标 cell source 被替换为行数组；若省略: 写入格式或内容错误不被发现
    def test_notebook_read_rejects_workspace_escape_path(self) -> None:  # 新增代码+Notebook工具: 验证 notebook_read 不能读取工作区外路径；若省略: 模型可能借 NotebookRead 越界读取文件
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Notebook工具: 创建临时工作区隔离路径边界测试；若省略: 越界路径会依赖真实目录结构
            workspace = Path(raw_dir)  # 新增代码+Notebook工具: 把临时目录转成 Path；若省略: agent 构造不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+Notebook工具: 创建测试 agent；若省略: 无法直接调用 notebook_read
            output = agent._execute_tool(ToolCall(name="notebook_read", arguments={"path": "../outside.ipynb"}))  # 新增代码+Notebook工具: 请求读取工作区外路径；若省略: 路径越界分支没有测试输入
            self.assertIn("notebook_read 失败", output)  # 新增代码+Notebook工具: 断言越界读取失败；若省略: 工具可能误报成功
            self.assertIn("工作区内", output)  # 新增代码+Notebook工具: 断言错误信息解释工作区边界；若省略: 模型难以修正 path 参数
    def test_runtime_instructions_mentions_notebook_tools(self) -> None:  # 新增代码+Notebook工具: 验证运行规则会引导模型使用 Notebook 工具；若省略: 工具存在但模型可能不知道何时调用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+Notebook工具: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+Notebook工具: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("notebook_read", runtime_text)  # 新增代码+Notebook工具: 断言规则提到读取 notebook 工具；若省略: 模型可能继续用普通 read_file 直接看 JSON
        self.assertIn("notebook_edit", runtime_text)  # 新增代码+Notebook工具: 断言规则提到编辑 notebook 工具；若省略: 模型可能直接文本替换破坏 .ipynb 结构
    def test_runtime_instructions_routes_discovery_through_tool_list(self) -> None:  # 修改代码+极简工具面: 验证动态规则通过可读 skill 索引发现能力；若省略: 旧 tool_search 入口可能重新进入动态提示词
        runtime_file = self._dynamic_prompt_file()  # 修改代码+极简工具面: 定位真实 dynamicprompt.md；若省略: 测试可能检查不到用户实际按需规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 修改代码+极简工具面: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("tool_list.md", runtime_text)  # 修改代码+极简工具面: 断言规则引导模型读取 skill 索引；若省略: 模型可能不知道如何用 read 发现能力
        self.assertIn("read / write / edit / bash", runtime_text)  # 修改代码+极简工具面: 断言规则围绕四原子工具展开；若省略: 模型可能继续寻找旧工具搜索入口
        self.assertNotIn("tool_search", runtime_text)  # 修改代码+极简工具面: 断言旧工具搜索不进入动态提示词；若省略: dynamicprompt 会继续放大旧架构
    def test_runtime_instructions_mentions_tool_architecture_v2_deferred_loading(self) -> None:  # 新增代码+ToolArchitectureV2: 验证运行规则说明 catalog、pool 和 deferred 加载；若没有这行代码，文档可能退回旧的全量暴露工具思路
        runtime_file = self._dynamic_prompt_file()  # 新增代码+ToolArchitectureV2: 定位真实 runtime_instructions.md；若没有这行代码，测试可能检查不到 agent 实际加载的规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+ToolArchitectureV2: 用 UTF-8 读取中文运行规则；若没有这行代码，Windows 默认编码可能导致中文关键词断言不稳定
        self.assertIn("Tool Architecture v2", runtime_text)  # 新增代码+ToolArchitectureV2: 断言运行规则明确写入 v2 架构名；若没有这行代码，模型可能不知道这是顶层工具架构约束
        self.assertIn("read / write / edit / bash", runtime_text)  # 修改代码+极简工具面: 断言规则解释当前可见工具面；若没有这行代码，模型可能误以为 catalog 工具都能直接调用
        self.assertIn("tool_list.md", runtime_text)  # 修改代码+极简工具面: 断言规则解释按需能力发现入口；若没有这行代码，模型不知道用哪个文件替代旧 select 流程
        self.assertIn("deferred", runtime_text)  # 修改代码+极简工具面: 断言规则保留内部延迟状态概念；若没有这行代码，维护者难以理解旧目录仍存在但不首轮暴露
        self.assertNotIn("select:<tool_name>", runtime_text)  # 修改代码+极简工具面: 断言旧单工具 select 语法不再指导模型；若没有这行代码，动态规则会把模型带回旧加载方式
    def test_runtime_instructions_mentions_tool_policy_v2(self) -> None:  # 新增代码+ToolPolicyV2: 验证运行规则明确说明 Tool Policy v2；若没有这行代码，文档可能漏掉 select 会被策略门禁限制的事实
        runtime_file = self._dynamic_prompt_file()  # 新增代码+ToolPolicyV2: 定位真实 runtime_instructions.md；若没有这行代码，测试可能检查不到 agent 实际加载给模型的规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+ToolPolicyV2: 用 UTF-8 读取中文运行规则；若没有这行代码，Windows 默认编码可能让中英文混排断言不稳定
        self.assertIn("Tool Policy v2", runtime_text)  # 新增代码+ToolPolicyV2: 断言文档写明第二层工具策略名称；若没有这行代码，模型可能只知道工具架构但不知道权限策略层
        self.assertIn("deny rule", runtime_text)  # 新增代码+ToolPolicyV2: 断言文档写明拒绝规则；若没有这行代码，模型可能不知道工具会在暴露前和执行前被硬拦截
        self.assertIn("skill gate", runtime_text)  # 新增代码+ToolPolicyV2: 断言文档写明技能门禁；若没有这行代码，模型可能尝试在技能未加载时强行 select 工具
        self.assertIn("workflow gate", runtime_text)  # 新增代码+ToolPolicyV2: 断言文档写明工作流门禁；若没有这行代码，模型可能跳过真实 Chrome 等高风险工具的前置流程
    def test_capability_pack_skill_files_exist(self) -> None:  # 新增代码+CapabilityPacks: 验证每个能力包都有可按需加载的 SKILL.md；若没有这行代码，工具被隐藏后可能没有对应说明书可读
        skills_root = (TEST_ROOT / "skills")  # 新增代码+CapabilityPacks: 定位 learning_agent 的本地 skills 目录；若没有这行代码，测试无法检查实际 skill 文件
        expected_skills = ["file_operations", "memory", "execution", "notebook", "mcp", "browser_automation", "real_chrome", "delegation", "planning", "diagnostics", "long_running_work", "prompt_architecture"]  # 新增代码+CapabilityPacks: 列出方案 B 必须存在的能力包 skill；若没有这行代码，新增能力包可能缺少说明书
        for skill_name in expected_skills:  # 新增代码+CapabilityPacks: 逐个检查 skill 目录；若没有这行代码，只能手写重复断言且难维护
            with self.subTest(skill_name=skill_name):  # 新增代码+CapabilityPacks: 为每个 skill 提供独立失败上下文；若没有这行代码，失败时不容易定位缺哪个 skill
                skill_file = skills_root / skill_name / "SKILL.md"  # 新增代码+CapabilityPacks: 生成该能力包的 SKILL.md 路径；若没有这行代码，无法检查具体文件
                self.assertTrue(skill_file.exists(), f"缺少 skill 文件：{skill_file}")  # 新增代码+CapabilityPacks: 断言说明书文件存在；若没有这行代码，隐藏工具后模型没有按需学习入口
    def test_readme_explains_tool_architecture_v2_catalog_and_pool(self) -> None:  # 新增代码+ToolArchitectureV2: 验证 README 面向学习者解释 v2 工具架构；若没有这行代码，用户文档可能继续误导为“所有工具都直接暴露”
        readme_file = (TEST_ROOT / "README.md")  # 新增代码+ToolArchitectureV2: 定位真实 README；若没有这行代码，测试无法覆盖用户实际阅读的说明
        readme_text = readme_file.read_text(encoding="utf-8")  # 新增代码+ToolArchitectureV2: 用 UTF-8 读取中文 README；若没有这行代码，中文断言在 Windows 上可能乱码
        self.assertIn("Tool Architecture v2", readme_text)  # 新增代码+ToolArchitectureV2: 断言 README 写明 v2 名称；若没有这行代码，学习者难以把改动和顶层架构联系起来
        self.assertIn("Tool Catalog", readme_text)  # 新增代码+ToolArchitectureV2: 断言 README 说明完整工具目录；若没有这行代码，学习者可能不知道 deferred 工具仍可被搜索
        self.assertIn("Tool Pool", readme_text)  # 新增代码+ToolArchitectureV2: 断言 README 说明当前工具池；若没有这行代码，学习者可能不知道模型默认只看 pool
        self.assertIn("read / write / edit / bash", readme_text)  # 修改代码+极简工具面: 断言 README 说明首轮只暴露四原子工具；若没有这行代码，学习者可能以为旧工具搜索仍是默认入口
        self.assertIn("learning_agent/skills/tool_list.md", readme_text)  # 修改代码+极简工具面: 断言 README 指向可读取的 skill 索引；若没有这行代码，学习者不知道新能力如何按需发现
    def test_runtime_instructions_mentions_skill_tools(self) -> None:  # 新增代码+SkillLoad: 验证运行规则会引导模型发现和加载本地 skills；若省略: 工具存在但模型可能不知道何时使用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+SkillLoad: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+SkillLoad: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("skill_list", runtime_text)  # 新增代码+SkillLoad: 断言规则提到 skill_list；若省略: 模型不知道先列出本地 skills
        self.assertIn("skill_load", runtime_text)  # 新增代码+SkillLoad: 断言规则提到 skill_load；若省略: 模型不知道如何加载 skill 说明
        self.assertIn("skills", runtime_text)  # 新增代码+SkillLoad: 断言规则保留 skills 语义词；若省略: 只有工具名不足以说明用途
    def test_runtime_instructions_mentions_task_tool(self) -> None:  # 新增代码+TaskAgent: 验证运行规则会引导模型使用 task 子 agent；若省略: 工具存在但模型可能不知道复杂任务可委派
        runtime_file = self._dynamic_prompt_file()  # 新增代码+TaskAgent: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+TaskAgent: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("task", runtime_text)  # 新增代码+TaskAgent: 断言规则提到 task；若省略: 模型不知道可以调用子 agent
        self.assertIn("子 agent", runtime_text)  # 新增代码+TaskAgent: 断言规则说明 task 的子 agent 用途；若省略: 只有工具名不足以指导触发时机
    def test_runtime_instructions_mentions_task_lifecycle_tools(self) -> None:  # 新增代码+TaskLifecycle: 验证运行规则会引导模型查询或停止子任务；若省略: 工具存在但模型可能不知道何时使用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+TaskLifecycle: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+TaskLifecycle: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("task_output", runtime_text)  # 新增代码+TaskLifecycle: 断言规则提到 task_output；若省略: 模型不知道如何查询子任务输出
        self.assertIn("task_stop", runtime_text)  # 新增代码+TaskLifecycle: 断言规则提到 task_stop；若省略: 模型不知道如何停止子任务
        self.assertIn("background=true", runtime_text)  # 修改代码+AsyncTask: 断言规则提到 task 的 background=true 参数；若省略: 测试可能误命中 start_background_command 的英文 background
    def test_runtime_instructions_mentions_task_management_tools(self) -> None:  # 新增代码+TaskManagement: 验证运行规则会引导模型管理多个子任务；若省略: 工具存在但模型可能不知道何时使用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+TaskManagement: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+TaskManagement: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("task_list", runtime_text)  # 新增代码+TaskManagement: 断言规则提到 task_list；若省略: 模型不知道如何列出多个子任务
        self.assertIn("task_get", runtime_text)  # 新增代码+TaskManagement: 断言规则提到 task_get；若省略: 模型不知道如何读取单任务详情
        self.assertIn("task_update", runtime_text)  # 新增代码+TaskManagement: 断言规则提到 task_update；若省略: 模型不知道如何更新标签或备注
    def test_runtime_instructions_mentions_team_communication_tools(self) -> None:  # 修改代码+TeamCommunicationLifecycle: 验证运行规则会引导模型使用教学版多 agent 通信生命周期工具；若省略: 工具存在但模型可能不知道何时使用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+TeamCommunication: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+TeamCommunication: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("team_create", runtime_text)  # 新增代码+TeamCommunication: 断言规则提到 team_create；若省略: 模型不知道如何登记 peer
        self.assertIn("send_message", runtime_text)  # 新增代码+TeamCommunication: 断言规则提到 send_message；若省略: 模型不知道如何发送协作消息
        self.assertIn("list_peers", runtime_text)  # 新增代码+TeamCommunication: 断言规则提到 list_peers；若省略: 模型不知道如何查看 peer 列表
        self.assertIn("read_peer_messages", runtime_text)  # 新增代码+TeamCommunicationLifecycle: 断言规则提到 read_peer_messages；若省略: 模型不知道如何读取 peer inbox
        self.assertIn("ack_peer_message", runtime_text)  # 新增代码+TeamCommunicationLifecycle: 断言规则提到 ack_peer_message；若省略: 模型不知道如何确认消息已处理
        self.assertIn("team_delete", runtime_text)  # 新增代码+TeamCommunicationLifecycle: 断言规则提到 team_delete；若省略: 模型不知道如何回收教学版 peer
        self.assertIn("team_start_task", runtime_text)  # 新增代码+TeamTaskBinding: 断言规则提到 team_start_task；若省略: 模型不知道如何让 peer 绑定后台 task
    def test_runtime_instructions_mentions_plan_mode_tools(self) -> None:  # 新增代码+PlanMode: 验证运行规则会引导模型使用 Plan mode；若省略: 工具存在但模型可能继续直接执行复杂改动
        runtime_file = self._dynamic_prompt_file()  # 新增代码+PlanMode: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+PlanMode: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("enter_plan_mode", runtime_text)  # 新增代码+PlanMode: 断言规则提到 enter_plan_mode；若省略: 模型不知道如何进入计划模式
        self.assertIn("exit_plan_mode", runtime_text)  # 新增代码+PlanMode: 断言规则提到 exit_plan_mode；若省略: 模型不知道如何输出计划并等待确认
        self.assertIn("verify_plan_execution", runtime_text)  # 新增代码+PlanVerification: 断言规则提到 verify_plan_execution；若省略: 模型不知道如何验证计划执行结果
        self.assertIn("计划模式", runtime_text)  # 新增代码+PlanMode: 断言规则说明计划模式用途；若省略: 只有工具名不足以指导触发时机
    def test_runtime_instructions_mentions_worktree_tools(self) -> None:  # 新增代码+WorktreeIsolation: 验证运行规则会引导模型使用 worktree 隔离状态工具；若省略: 工具存在但模型可能不知道何时使用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+WorktreeIsolation: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+WorktreeIsolation: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("enter_worktree", runtime_text)  # 新增代码+WorktreeIsolation: 断言规则提到 enter_worktree；若省略: 模型不知道如何进入隔离状态
        self.assertIn("exit_worktree", runtime_text)  # 新增代码+WorktreeIsolation: 断言规则提到 exit_worktree；若省略: 模型不知道如何退出隔离状态
        self.assertIn("工作区隔离", runtime_text)  # 新增代码+WorktreeIsolation: 断言规则说明隔离用途；若省略: 只有工具名不足以指导触发时机
    def test_runtime_instructions_mentions_lsp_tools(self) -> None:  # 新增代码+LSP工具: 验证运行规则会引导模型使用轻量 LSP 工具；若省略: 工具存在但模型可能不知道何时使用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+LSP工具: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+LSP工具: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("lsp_symbols", runtime_text)  # 新增代码+LSP工具: 断言规则提到 lsp_symbols；若省略: 模型不知道如何读取符号列表
        self.assertIn("lsp_definition", runtime_text)  # 新增代码+LSP工具: 断言规则提到 lsp_definition；若省略: 模型不知道如何定位定义
        self.assertIn("lsp_diagnostics", runtime_text)  # 新增代码+LSP工具: 断言规则提到 lsp_diagnostics；若省略: 模型不知道如何读取诊断
        self.assertIn("符号", runtime_text)  # 新增代码+LSP工具: 断言规则说明符号级理解用途；若省略: 只有工具名不足以指导触发时机
    def test_runtime_instructions_mentions_repl_tool(self) -> None:  # 新增代码+REPL工具: 验证运行规则会引导模型使用安全 REPL 批量编排；若省略: 工具存在但模型可能不知道何时使用
        runtime_file = self._dynamic_prompt_file()  # 新增代码+REPL工具: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+REPL工具: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("repl", runtime_text)  # 新增代码+REPL工具: 断言规则提到 repl；若省略: 模型不知道可以批量执行安全工具
        self.assertIn("批量", runtime_text)  # 新增代码+REPL工具: 断言规则说明批量编排用途；若省略: 只有工具名不足以指导触发时机
        self.assertIn("安全白名单", runtime_text)  # 新增代码+REPL工具: 断言规则说明 REPL 的安全边界；若省略: 模型可能尝试用 REPL 执行副作用工具
    def test_runtime_instructions_mentions_cron_monitor_tools(self) -> None:  # 新增代码+CronMonitor: 验证运行规则会引导模型使用 Cron/Monitor 教学版工具；若省略: 工具存在但模型可能不知道边界和触发时机
        runtime_file = self._dynamic_prompt_file()  # 新增代码+CronMonitor: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+CronMonitor: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("cron_create", runtime_text)  # 新增代码+CronMonitor: 断言规则提到 cron_create；若省略: 模型不知道如何登记定时检查
        self.assertIn("cron_list", runtime_text)  # 新增代码+CronMonitor: 断言规则提到 cron_list；若省略: 模型不知道如何查看定时任务记录
        self.assertIn("cron_delete", runtime_text)  # 新增代码+CronMonitor: 断言规则提到 cron_delete；若省略: 模型不知道如何回收定时任务记录
        self.assertIn("monitor", runtime_text)  # 新增代码+CronMonitor: 断言规则提到 monitor；若省略: 模型不知道如何登记或更新监控记录
        self.assertIn("进程内", runtime_text)  # 新增代码+CronMonitor: 断言规则说明记录只在当前进程内存在；若省略: 模型可能误以为跨重启持久化
        self.assertIn("不会自动执行", runtime_text)  # 新增代码+CronMonitor: 断言规则说明不会真实调度执行；若省略: 模型可能误以为系统定时器已启动


if __name__ == "__main__":  # Stage14: allow running this test module directly.
    unittest.main()  # Stage14: start unittest when executed as a script.


