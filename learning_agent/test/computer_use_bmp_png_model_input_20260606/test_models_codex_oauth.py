"Model, Codex CLI, and OAuth tests."  # Stage14: this file owns the models_codex_oauth test group.
from __future__ import annotations  # Stage14: keep annotations lazy after test split.
import unittest  # Stage14: keep direct unittest execution available.
from learning_agent.tests.support import *  # Stage14: import shared helpers and dependencies for copied tests.

class ModelsCodexOAuthTests(LearningAgentTestBase):  # Stage14: unittest discovers this concrete modular test class.
    def test_core_messages_exports_tool_call_and_model_message(self) -> None:  # 新增代码+CoreSplit: 验证消息数据结构已从主文件迁移到 core.messages；若没有这行代码，后续可能只是假拆分但无人发现。
        from learning_agent.core.messages import ModelMessage as CoreModelMessage, ToolCall as CoreToolCall  # 新增代码+CoreSplit: 直接导入新模块的消息类型；若没有这行代码，测试无法证明新模块可独立使用。
        self.assertEqual(CoreToolCall(name="x", arguments={}).name, "x")  # 新增代码+CoreSplit: 断言新 ToolCall 保存工具名；若没有这行代码，迁移后字段语义错误不会被发现。
        self.assertEqual(CoreModelMessage(text="ok").text, "ok")  # 新增代码+CoreSplit: 断言新 ModelMessage 保存文本回答；若没有这行代码，模型最终回答字段可能在拆分中变形。
        self.assertIs(ToolCall, CoreToolCall)  # 新增代码+CoreSplit: 断言旧入口仍重导出同一个 ToolCall 类；若没有这行代码，老调用方可能在重构后悄悄拿到不同类型。
        self.assertIs(ModelMessage, CoreModelMessage)  # 新增代码+CoreSplit: 断言旧入口仍重导出同一个 ModelMessage 类；若没有这行代码，假模型和真实模型可能混用两套消息类型。
    def test_models_package_exports_chat_model_adapters(self) -> None:  # 新增代码+ModelsSplit: 验证模型适配器已迁移到 models 包；若没有这行代码，模型层可能继续堆在 learning_agent.py 里没人发现。
        from learning_agent.models.base import ChatModel as ModelPackageChatModel  # 新增代码+ModelsSplit: 直接导入模型接口模块；若没有这行代码，测试无法证明模型接口能被独立复用。
        from learning_agent.models.codex_cli import CodexCliChatModel as ModelPackageCodexCliChatModel  # 新增代码+ModelsSplit: 直接导入 Codex CLI 模型适配器；若没有这行代码，CLI 桥接层拆分无法被测试锁住。
        from learning_agent.models.codex_oauth import CodexOAuthChatModel as ModelPackageCodexOAuthChatModel  # 新增代码+ModelsSplit: 直接导入 OAuth/API 模型适配器；若没有这行代码，OAuth 模型拆分无法被测试锁住。
        from learning_agent.models.oauth_tokens import CodexOAuthTokenStore as ModelPackageCodexOAuthTokenStore, CodexOAuthTokens as ModelPackageCodexOAuthTokens  # 新增代码+ModelsSplit: 直接导入 token 数据和存储类；若没有这行代码，OAuth token 逻辑可能仍留在主文件。
        from learning_agent.models.openai_chat import OpenAIChatModel as ModelPackageOpenAIChatModel  # 新增代码+ModelsSplit: 直接导入 OpenAI-compatible 模型适配器；若没有这行代码，默认模型入口拆分无法被测试锁住。
        self.assertIsNotNone(ModelPackageChatModel)  # 新增代码+ModelsSplit: 断言模型接口模块存在；若没有这行代码，空导入也可能被误认为通过。
        self.assertIsNotNone(ModelPackageCodexCliChatModel)  # 新增代码+ModelsSplit: 断言 Codex CLI 类存在；若没有这行代码，模块导出缺失不会有清晰失败点。
        self.assertIsNotNone(ModelPackageCodexOAuthChatModel)  # 新增代码+ModelsSplit: 断言 OAuth 模型类存在；若没有这行代码，真实 OAuth 入口迁移失败不容易定位。
        self.assertIsNotNone(ModelPackageCodexOAuthTokenStore)  # 新增代码+ModelsSplit: 断言 token store 类存在；若没有这行代码，token 存储边界迁移失败不容易定位。
        self.assertIsNotNone(ModelPackageCodexOAuthTokens)  # 新增代码+ModelsSplit: 断言 token 数据类存在；若没有这行代码，token 数据结构迁移失败不容易定位。
        self.assertIsNotNone(ModelPackageOpenAIChatModel)  # 新增代码+ModelsSplit: 断言 OpenAI 模型类存在；若没有这行代码，默认模型入口迁移失败不容易定位。
        self.assertIs(CodexCliChatModel, ModelPackageCodexCliChatModel)  # 新增代码+ModelsSplit: 断言旧入口仍重导出同一个 Codex CLI 类；若没有这行代码，旧调用方可能拿到重复类型。
        self.assertIs(CodexOAuthChatModel, ModelPackageCodexOAuthChatModel)  # 新增代码+ModelsSplit: 断言旧入口仍重导出同一个 OAuth 模型类；若没有这行代码，旧测试和新模块可能分裂。
        self.assertIs(CodexOAuthTokens, ModelPackageCodexOAuthTokens)  # 新增代码+ModelsSplit: 断言旧入口仍重导出同一个 token 数据类；若没有这行代码，测试 fake store 可能和生产类不一致。
        self.assertIs(OpenAIChatModel, ModelPackageOpenAIChatModel)  # 新增代码+ModelsSplit: 断言旧入口仍重导出同一个 OpenAI 模型类；若没有这行代码，默认模型兼容性可能悄悄断开。
    def test_agent_tool_to_model_schema_preserves_existing_shape(self) -> None:  # 新增代码+ToolArchitectureV2: 验证 AgentTool 仍可转回现有模型工具 schema；若没有这行代码，兼容层可能破坏模型调用
        catalog = build_builtin_tool_catalog()  # 新增代码+ToolArchitectureV2: 构建内置工具目录；若没有这行代码，无法获得 AgentTool 对象
        tool_search = next(tool for tool in catalog if tool.name == "tool_search")  # 新增代码+ToolArchitectureV2: 找到 tool_search 元数据；若没有这行代码，无法检查转换结果
        schema = tool_search.to_model_schema()  # 新增代码+ToolArchitectureV2: 调用待实现的兼容转换；若没有这行代码，测试不到模型边界
        self.assertEqual(schema["type"], "function")  # 新增代码+ToolArchitectureV2: 断言仍使用 OpenAI-compatible function schema；若没有这行代码，模型适配器可能无法识别工具
        self.assertEqual(schema["function"]["name"], "tool_search")  # 新增代码+ToolArchitectureV2: 断言工具名不变；若没有这行代码，执行分发会找不到工具
        self.assertIn("query", schema["function"]["parameters"]["properties"])  # 新增代码+ToolArchitectureV2: 断言参数 schema 保留 query；若没有这行代码，模型无法构造搜索请求
        schema["function"]["parameters"]["properties"]["mutated_by_test"] = {"type": "string"}  # 新增代码+ToolArchitectureV2: 修改返回 schema 来验证深拷贝隔离；若没有这行代码，测试无法发现返回值污染 catalog 的问题
        self.assertNotIn("mutated_by_test", tool_search.input_schema["properties"])  # 新增代码+ToolArchitectureV2: 断言 AgentTool 内部 schema 没被外部返回值污染；若没有这行代码，可变对象共享风险不会被锁住
    def test_mcp_tool_registry_converts_tools_to_model_schemas(self) -> None:  # 新增代码+MCP 工具注册表: 验证注册表能启动 client、转换 schema、按前缀转发调用；若省略: Task 4 核心行为没有回归保护
        fake_client = FakeMcpClient()  # 新增代码+MCP 工具注册表: 创建可控 fake client；若省略: 测试无法隔离真实 MCP 子进程
        registry = McpToolRegistry({"demo": fake_client})  # 新增代码+MCP 工具注册表: 用 demo server 名构造注册表；若省略: 无法验证 mcp__demo__echo 命名格式
        registry.start()  # 新增代码+MCP 工具注册表: 启动注册表并读取 tools/list；若省略: tool_schemas 没有缓存工具可返回
        schemas = registry.tool_schemas()  # 新增代码+MCP 工具注册表: 读取 OpenAI-compatible function schemas；若省略: 无法断言 schema 转换结果
        self.assertEqual(schemas[0]["function"]["name"], "mcp__demo__echo")  # 新增代码+MCP 工具注册表: 断言工具名包含 mcp、服务器名和原工具名；若省略: 命名前缀回归不会被发现
        self.assertEqual(schemas[0]["function"]["parameters"]["required"], ["text"])  # 新增代码+MCP 工具注册表: 断言 MCP inputSchema 的 required 被保留；若省略: 参数必填约束丢失不会被发现
        result = registry.call_tool("mcp__demo__echo", {"text": "你好"})  # 新增代码+MCP 工具注册表: 用前缀名调用注册表工具；若省略: 无法验证前缀剥离和调用转发
        self.assertIn("called echo: 你好", result)  # 新增代码+MCP 工具注册表: 断言调用结果来自原始 echo 工具；若省略: 转发错误不会被测试捕获
    def test_agent_exposes_selected_mcp_tools_to_model(self) -> None:  # 修改代码+ToolArchitectureV2: 验证 MCP 工具先隐藏、select 后才暴露给模型；若没有这行代码，旧的全量暴露假设可能回归
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MCP接入LearningAgent: 创建临时工作区隔离 memory 和调试日志；若省略: 测试可能污染真实项目文件
            workspace = Path(raw_dir)  # 新增代码+MCP接入LearningAgent: 把临时目录转成 Path 方便传给 LearningAgent；若省略: 后续路径拼接和断言不够稳定
            fake_client = FakeMcpClient()  # 新增代码+MCP接入LearningAgent: 创建带 echo 工具的 fake MCP client；若省略: registry 没有可暴露给模型的 MCP 工具
            registry = McpToolRegistry({"demo": fake_client})  # 新增代码+MCP接入LearningAgent: 构造含 demo server 的 MCP 注册表；若省略: LearningAgent 无法测试注入 registry 的路径
            model = RecordingToolNameFakeModel(ModelMessage(text="MCP 工具已暴露。"))  # 新增代码+MCP接入LearningAgent: 使用记录工具名的假模型；若省略: 无法观察模型实际收到的 tools
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry)  # 新增代码+MCP接入LearningAgent: 注入 MCP registry 并允许启动权限；若省略: __init__ 不会走 registry.start 路径
            initial_tool_names = agent._tool_schema_names(agent._available_tool_schemas())  # 新增代码+ToolArchitectureV2: 读取 select 前当前工具池；若没有这行代码，测试无法证明 MCP 工具默认隐藏
            self.assertNotIn("mcp__demo__echo", initial_tool_names)  # 新增代码+ToolArchitectureV2: 断言 MCP 工具默认不进入首轮 Tool Pool；若没有这行代码，v2 deferred 策略可能静默失效
            select_output = self._select_tool_for_test(agent, "mcp__demo__echo")  # 新增代码+ToolArchitectureV2: 通过 tool_search select 加载 MCP echo；若没有这行代码，后续模型仍不应该看到 deferred 工具
            self.assertIn("已加载", select_output)  # 新增代码+ToolArchitectureV2: 断言 select 返回成功；若没有这行代码，后续可见性断言可能掩盖加载失败
            answer = agent.run("请确认 MCP 工具列表")  # 新增代码+MCP接入LearningAgent: 触发 agent.run 把工具 schema 传给模型；若省略: 只能测试私有方法而不能验证真实调用链路
            self.assertIn("MCP 工具已暴露", answer)  # 新增代码+MCP接入LearningAgent: 确认真正返回了假模型的最终文本；若省略: run 流程异常可能未被发现
            self.assertTrue(fake_client.started)  # 新增代码+MCP接入LearningAgent: 断言初始化时 registry.start 启动了 client；若省略: 只能证明 schema 存在而不能证明启动流程发生
            self.assertIn("read", model.received_tool_names[0])  # 修改代码+极简工具面: 确认 MCP 合并后读取原子工具仍暴露给模型；若省略: select 后可能丢失读取 skill 和文件的入口
            self.assertIn("write", model.received_tool_names[0])  # 修改代码+极简工具面: 确认 MCP 合并后写入原子工具仍暴露给模型；若省略: 加载 MCP 后可能误删基础写入能力
            self.assertIn("edit", model.received_tool_names[0])  # 修改代码+极简工具面: 确认 MCP 合并后编辑原子工具仍暴露给模型；若省略: 加载 MCP 后可能误删基础编辑能力
            self.assertIn("bash", model.received_tool_names[0])  # 修改代码+极简工具面: 确认 MCP 合并后命令原子工具仍暴露给模型；若省略: 加载 MCP 后可能误删测试和命令能力
            self.assertNotIn("tool_search", model.received_tool_names[0])  # 修改代码+极简工具面: 确认 MCP 合并后旧工具搜索仍不暴露给模型；若省略: select 后工具池可能回退到旧架构
            self.assertNotIn("skill_load", model.received_tool_names[0])  # 修改代码+极简工具面: 确认 MCP 合并后旧 skill_load 仍不暴露给模型；若省略: select 后首轮瘦身成果可能被破坏
            self.assertNotIn("read_file", model.received_tool_names[0])  # 修改代码+CapabilityPacks: 确认未选择文件能力包时 read_file 不暴露；若省略: MCP 测试会放过工具池膨胀回归
            self.assertIn("mcp__demo__echo", model.received_tool_names[0])  # 修改代码+ToolArchitectureV2: 确认 select 后 MCP echo 进入模型工具列表；若没有这行代码，加载后 Tool Pool 可能仍未更新
    def test_readme_explains_codex_oauth_relogin_and_timeout_boundaries(self) -> None:  # 新增代码+OAuth重登录文档: 验证 README 讲清 Codex OAuth 重新登录和超时边界；若省略: 用户会继续误以为所有失败都该弹网页登录
        readme_file = (TEST_ROOT / "README.md")  # 新增代码+OAuth重登录文档: 定位 learning_agent README；若省略: 文档测试可能读不到真实用户文档
        readme_text = readme_file.read_text(encoding="utf-8")  # 新增代码+OAuth重登录文档: 用 UTF-8 读取中文文档；若省略: Windows 默认编码可能导致中文断言失败
        self.assertIn("refresh token 失效", readme_text)  # 新增代码+OAuth重登录文档: 断言文档说明 refresh token 失效场景；若省略: 用户不知道为什么需要重新网页登录
        self.assertIn("重新打开浏览器", readme_text)  # 新增代码+OAuth重登录文档: 断言文档说明会打开浏览器重新认证；若省略: 用户不知道自动恢复动作是什么
        self.assertIn("401/403", readme_text)  # 新增代码+OAuth重登录文档: 断言文档列出 API 鉴权失败状态码；若省略: 用户无法区分认证失败和普通网络失败
        self.assertIn("响应读取超时", readme_text)  # 新增代码+OAuth重登录文档: 断言文档提到截图里的 timeout 类型；若省略: 用户仍会把 read timeout 当 OAuth 过期
        self.assertIn("远端连接关闭", readme_text)  # 新增代码+OAuth远端断连文档: 断言文档提到本次截图里的远端断连类型；若省略: 用户仍会把 Remote end closed 当成登录问题
        self.assertIn("不一定是 OAuth 登录过期", readme_text)  # 新增代码+OAuth重登录文档: 断言文档明确 timeout 边界；若省略: 后续排查方向会被误导
    def test_model_output_schema_includes_dynamic_mcp_argument_names(self) -> None:  # 新增代码+MCP参数适配回归: 验证模型输出 schema 会包含 MCP 工具自己的 query/url 参数；若省略: 模型会继续被旧 path/content/text 限制导致 web_search 传参失败
        tools = [  # 新增代码+MCP参数适配回归: 构造一个动态 MCP 工具 schema；若省略: 输出 schema 无法模拟真实 browser_search 工具
            {  # 新增代码+MCP参数适配回归: 定义 web_search 工具对象；若省略: 测试没有 query 参数来源
                "type": "function",  # 新增代码+MCP参数适配回归: 使用 OpenAI-compatible function 工具格式；若省略: 输出 schema 提取逻辑无法识别工具
                "function": {  # 新增代码+MCP参数适配回归: 放置函数定义；若省略: name/parameters 没有标准位置
                    "name": "mcp__browser_search__web_search",  # 新增代码+MCP参数适配回归: 使用真实 MCP 搜索工具名；若省略: 测试语义不清晰
                    "description": "联网搜索网页。",  # 新增代码+MCP参数适配回归: 提供工具说明；若省略: 不影响断言但不贴近真实 schema
                    "parameters": {  # 新增代码+MCP参数适配回归: 提供动态工具参数 schema；若省略: query/max_results 不会进入输出 schema
                        "type": "object",  # 新增代码+MCP参数适配回归: 声明参数是对象；若省略: schema 不完整
                        "properties": {  # 新增代码+MCP参数适配回归: 列出搜索工具参数；若省略: 无法验证动态参数名
                            "query": {"type": "string"},  # 新增代码+MCP参数适配回归: 搜索关键词参数；若省略: 用户截图里的失败不会被测试覆盖
                            "max_results": {"type": "integer"},  # 新增代码+MCP参数适配回归: 搜索结果数量参数；若省略: 数值类 MCP 参数不会被覆盖
                        },  # 新增代码+MCP参数适配回归: properties 定义结束；若省略: Python 语法不完整
                        "required": ["query"],  # 新增代码+MCP参数适配回归: 声明 query 必填；若省略: 不影响输出 schema 但不贴近真实工具
                    },  # 新增代码+MCP参数适配回归: parameters 定义结束；若省略: Python 语法不完整
                },  # 新增代码+MCP参数适配回归: function 定义结束；若省略: Python 语法不完整
            }  # 新增代码+MCP参数适配回归: 工具对象结束；若省略: Python 语法不完整
        ]  # 新增代码+MCP参数适配回归: 工具列表结束；若省略: Python 语法不完整
        schema = CodexCliChatModel._output_schema(tools=tools)  # 新增代码+MCP参数适配回归: 生成带动态工具参数的模型输出 schema；若省略: 无法检查修复目标
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 从 per-tool anyOf 分支汇总参数供旧回归断言使用；若没有这行代码，测试会继续依赖已移除的共享 arguments 路径
        self.assertIn("query", argument_schema["properties"])  # 新增代码+MCP参数适配回归: 断言 query 已允许输出；若省略: web_search 仍会被迫使用 text 参数
        self.assertIn("max_results", argument_schema["properties"])  # 新增代码+MCP参数适配回归: 断言 max_results 已允许输出；若省略: 搜索结果数量无法由模型传入
        self.assertIn("query", argument_schema["required"])  # 新增代码+MCP参数适配回归: 严格 JSON schema 要求所有可用参数字段出现；若省略: strict 输出可能不稳定
        self.assertNotIn("path", argument_schema["properties"])  # 修改代码+OutputProtocolV2: 断言自定义 MCP 工具池不会混入内置 read_file 的 path 参数；若没有这行代码，per-tool 输出协议退化成共享参数池也不容易被发现
    def test_oauth_request_uses_dynamic_output_schema_for_mcp_arguments(self) -> None:  # 新增代码+MCP参数适配回归: 验证 OAuth 请求体真正使用动态输出 schema；若省略: 只修静态方法但真实 GPT-5.5 路径仍可能继续传 text
        model = CodexOAuthChatModel(model="gpt-5.5", token_store=FakeOAuthTokenStore(None))  # 修改代码+MCP参数适配回归: 明确传入测试模型名并避免真实网络请求；若省略 model: 构造函数会因缺参失败而测不到动态 schema 问题
        tools = [  # 新增代码+MCP参数适配回归: 构造包含 query 参数的 MCP 工具；若省略: 请求体 schema 没有动态参数来源
            {  # 新增代码+MCP参数适配回归: 工具对象开始；若省略: Python 语法不完整
                "type": "function",  # 新增代码+MCP参数适配回归: 声明 function 工具；若省略: 动态参数提取逻辑会跳过
                "function": {  # 新增代码+MCP参数适配回归: 放置函数定义；若省略: 工具 schema 不完整
                    "name": "mcp__browser_search__web_search",  # 新增代码+MCP参数适配回归: 使用真实搜索 MCP 工具名；若省略: 测试语义不清楚
                    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},  # 新增代码+MCP参数适配回归: 声明 query 参数；若省略: 无法复现截图里的参数错配
                },  # 新增代码+MCP参数适配回归: function 定义结束；若省略: Python 语法不完整
            }  # 新增代码+MCP参数适配回归: 工具对象结束；若省略: Python 语法不完整
        ]  # 新增代码+MCP参数适配回归: 工具列表结束；若省略: Python 语法不完整
        body = model._build_responses_body(messages=[{"role": "user", "content": "查天气"}], tools=tools)  # 新增代码+MCP参数适配回归: 构造真实 OAuth 请求体；若省略: 无法确认 GPT-5.5 实际看到的输出 schema
        argument_schema = self._merged_tool_argument_schema(body["text"]["format"]["schema"])  # 修改代码+OutputProtocolV2: 从请求体 per-tool 分支汇总参数供旧回归断言使用；若没有这行代码，测试会继续读取不存在的共享 arguments 路径
        self.assertIn("query", argument_schema["properties"])  # 新增代码+MCP参数适配回归: 断言 OAuth 输出 schema 允许 query；若省略: 真实运行仍可能重现 text 错误
        self.assertNotIn("工具参数只能使用 path、content、text", body["instructions"])  # 新增代码+MCP参数适配回归: 断言旧错误指令不再出现；若省略: 模型可能仍被文字提示诱导传 text
        self.assertIn("不要输出不属于当前工具的参数", body["instructions"])  # 新增代码+OutputProtocolV2: 断言 OAuth prompt 明确禁止无关工具参数；若没有这行代码，真实 API 路径可能没有收到 Phase 2 指令
        self.assertNotIn("不属于本次工具的参数请写 null", body["instructions"])  # 新增代码+OutputProtocolV2: 断言旧共享 arguments 的 null 占位规则已移除；若没有这行代码，模型会同时收到新旧冲突指令
    def test_oauth_request_sends_computer_use_screenshot_as_native_image_input(self) -> None:  # 新增代码+ComputerUseVisionLoop：函数段开始，验证 Computer Use 截图不会只变成文本日志；如果没有这个测试，模型主循环可能看不到真实屏幕像素，作者意图是锁住 ClaudeCode 式“截图进入模型”的边界，本段到断言 prompt 不包含 base64 原文结束。
        model = CodexOAuthChatModel(model="gpt-5.5", token_store=FakeOAuthTokenStore(None))  # 新增代码+ComputerUseVisionLoop：创建不会联网的 OAuth 模型实例；如果没有这一行，测试无法调用真实请求体构造函数。
        screenshot_url = "data:image/png;base64,cGhhc2U0MV92aXNpb25fbG9vcA=="  # 新增代码+ComputerUseVisionLoop：准备一段模拟截图 data URL；如果没有这一行，测试没有可被转换成 input_image 的图片输入。
        messages = [  # 新增代码+ComputerUseVisionLoop：构造模型主循环会传入 OAuth 层的消息列表；如果没有这一行，测试无法复现 Computer Use 工具结果回灌场景。
            {  # 新增代码+ComputerUseVisionLoop：第一条消息对象开始；如果没有这一行，Python 字典结构不完整。
                "role": "user",  # 新增代码+ComputerUseVisionLoop：使用 user role 承载截图观察；如果没有这一行，Responses input 会缺少消息身份语义。
                "content": [  # 新增代码+ComputerUseVisionLoop：使用多模态 content 数组；如果没有这一行，图片块无法和说明文本一起进入模型输入。
                    {"type": "text", "text": "Computer Use screenshot pixels for the next observe-plan-act step."},  # 新增代码+ComputerUseVisionLoop：给图片补充简短文字说明；如果没有这一行，模型看到图片时缺少上下文来源。
                    {"type": "image_url", "image_url": {"url": screenshot_url, "detail": "high"}},  # 新增代码+ComputerUseVisionLoop：模拟 agent.py 注入的截图图片块；如果没有这一行，测试不会覆盖真实视觉输入转换。
                ],  # 新增代码+ComputerUseVisionLoop：content 数组结束；如果没有这一行，Python 列表语法不完整。
            }  # 新增代码+ComputerUseVisionLoop：消息对象结束；如果没有这一行，Python 字典语法不完整。
        ]  # 新增代码+ComputerUseVisionLoop：消息列表结束；如果没有这一行，测试输入无法传给请求体构造器。
        body = model._build_responses_body(messages=messages, tools=[])  # 新增代码+ComputerUseVisionLoop：构造真实 OAuth Responses 请求体；如果没有这一行，测试只能检查中间结构而不能证明真实 API 边界。
        content_blocks = body["input"][0]["content"]  # 新增代码+ComputerUseVisionLoop：读取真正发给 Responses API 的 content blocks；如果没有这一行，后续断言找不到检查对象。
        image_blocks = [block for block in content_blocks if block.get("type") == "input_image"]  # 新增代码+ComputerUseVisionLoop：筛出原生图片输入块；如果没有这一行，测试无法判断图片是否真的被模型视觉通道接收。
        self.assertEqual(image_blocks, [{"type": "input_image", "image_url": screenshot_url, "detail": "high"}])  # 新增代码+ComputerUseVisionLoop：断言截图以原生 input_image 形式发送；如果没有这一行，base64 图片可能继续只躺在文本里。
        text_blocks = [block for block in content_blocks if block.get("type") == "input_text"]  # 新增代码+ComputerUseVisionLoop：筛出文本 prompt 块；如果没有这一行，测试无法检查 prompt 是否重复塞入大图 base64。
        self.assertTrue(text_blocks)  # 新增代码+ComputerUseVisionLoop：断言结构化 prompt 仍然存在；如果没有这一行，修图像输入时可能误删工具 schema 和消息说明。
        self.assertNotIn(screenshot_url, text_blocks[0]["text"])  # 新增代码+ComputerUseVisionLoop：断言 base64 图片不会重复写进文本 prompt；如果没有这一行，长截图会浪费 token 并干扰模型注意力。
    def test_codex_adapter_instructions_keep_contract_for_prompt_context_v1(self) -> None:  # 新增代码+PromptContextV1: 验证 Codex-facing instructions 保留 JSON 输出契约；若省略: 提示词升级可能破坏工具调用格式
        model = CodexOAuthChatModel(model="gpt-test", token_store=FakeOAuthTokenStore(None), post_json=lambda url, headers, body: {}, login_callback=lambda: CodexOAuthTokens(access_token="a", refresh_token="r", expires_at=0))  # 新增代码+PromptContextV1: 构造不会联网的 OAuth 模型；若省略: 测试可能触发真实登录或 HTTP 请求
        instructions = model._build_instructions()  # 新增代码+PromptContextV1: 读取 Codex 后端会收到的顶层 instructions；若省略: 无法检查输出契约是否仍稳定
        self.assertIn("decision_note", instructions)  # 新增代码+PromptContextV1: 断言决策说明字段仍被要求；若省略: 初学者看不到模型选择工具的简短原因
        self.assertIn("tool_calls", instructions)  # 新增代码+PromptContextV1: 断言工具调用字段仍被要求；若省略: Codex 输出可能不再能驱动工具层
        self.assertIn("JSON 对象", instructions)  # 新增代码+PromptContextV1: 断言只输出 JSON 的要求仍存在；若省略: 解析器可能收到 Markdown 而失败
        self.assertIn("不要自己执行工具", instructions)  # 新增代码+PromptContextV1: 断言工具边界仍存在；若省略: 模型可能口头伪造执行结果
        self.assertIn("用户明确要求使用工具", instructions)  # 新增代码+PromptSurfaceV2: 断言适配器知道显式工具请求不能被普通回答替代；若省略: 用户要求真实浏览器时模型可能仍直接回答
        self.assertIn("真实 Chrome", instructions)  # 修改代码+真实浏览器误判: 断言适配器 prompt 保留真实 Chrome 高风险硬约束；若没有这行代码，真实 profile workflow 可能只靠运行规则提示而被忽略
        self.assertIn("当前浏览器", instructions)  # 新增代码+真实浏览器误判: 断言适配器 prompt 覆盖当前浏览器/登录态路线；若没有这行代码，当前已登录窗口需求可能被普通浏览器替代
    def test_cli_run_response_can_emit_json_for_codex(self) -> None:  # 新增代码+CLI接口: 验证一次性 CLI 输出能被 Codex 解析；若没有这行代码，CLI 只能给人读而不适合自动化接收
        payload_text = format_cli_run_response(answer="pong", output_json=True, workspace=Path("H:/demo"), visible_tools=["read", "bash"])  # 修改代码+H盘路径示例: 使用 H 盘示例路径避免旧盘符误导后续排查；若没有这行代码，JSON 输出测试没有可解析的工作区样本
        payload = json.loads(payload_text)  # 新增代码+CLI接口: 用标准 JSON 解析验证输出严格可机器读取；若没有这行代码，字符串看似 JSON 但可能不可解析
        self.assertTrue(payload["ok"])  # 新增代码+CLI接口: 断言成功标记为真；若没有这行代码，Codex 无法快速判断命令是否成功
        self.assertEqual(payload["answer"], "pong")  # 新增代码+CLI接口: 断言最终回答进入 JSON；若没有这行代码，Codex 收不到 agent 的输出
        self.assertEqual(payload["visible_tools"], ["read", "bash"])  # 新增代码+CLI接口: 断言可见工具随结果返回；若没有这行代码，调试时无法确认 Tool Pool
        self.assertIn("demo", payload["workspace"])  # 修改代码+CLI接口: 断言工作区进入结果且兼容 Windows 路径分隔符；若没有这行代码，外部控制器无法确认目标 agent 路径
    def test_agent_writes_debug_log_for_model_and_tool_loop(self) -> None:  # 新增代码: 测试 agent 会把每轮模型调用和工具循环写入调试日志；若省略: 调试日志功能没有自动化保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 使用临时目录隔离调试日志和测试文件，避免污染真实 learning_agent 工作区
            workspace = Path(raw_dir)  # 新增代码: 把临时目录转成 Path，方便拼接文件路径
            sample_file = workspace / "hello.txt"  # 新增代码: 准备 read_file 工具要读取的测试文件
            sample_file.write_text("调试日志测试内容", encoding="utf-8")  # 新增代码: 写入测试内容，便于后面确认工具结果被记录
            model = ToolCallingFakeModel(  # 新增代码: 构造假模型，稳定模拟一次 read_file 工具调用和一次最终回答
                [  # 新增代码: 假模型返回序列开始
                    ModelMessage(text="", tool_calls=[ToolCall(name="read_file", arguments={"path": "hello.txt"})]),  # 新增代码: 第一轮要求 agent 调用 read_file
                    ModelMessage(text="已经完成读取。"),  # 新增代码: 第二轮模拟模型收到工具结果后的最终回答
                ]  # 新增代码: 假模型返回序列结束
            )  # 新增代码: 假模型创建结束
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码: 创建 agent，并允许所有需要权限的操作
            answer = agent.run("请读取 hello.txt")  # 新增代码: 触发一次完整 tool loop，让日志有内容可记录
            log_path = workspace / "debug_logs" / "agent_debug.jsonl"  # 新增代码: 约定调试日志文件路径，便于用户和测试稳定查找
            log_events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]  # 新增代码: 按 JSONL 一行一事件解析日志
            event_names = [event["event"] for event in log_events]  # 新增代码: 提取事件名称，方便断言关键步骤是否都出现
            self.assertIn("user_input", event_names)  # 新增代码: 验证日志记录了用户输入
            self.assertIn("model_response", event_names)  # 新增代码: 验证日志记录了模型返回
            self.assertIn("tool_call", event_names)  # 新增代码: 验证日志记录了工具调用请求
            self.assertIn("tool_result", event_names)  # 新增代码: 验证日志记录了工具执行结果
            self.assertIn("final_answer", event_names)  # 新增代码: 验证日志记录了最终回答
            self.assertIn("已经完成读取", answer)  # 新增代码: 同时确认原本的 agent 返回值不受调试日志影响
            self.assertIn("read_file", json.dumps(log_events, ensure_ascii=False))  # 新增代码: 验证工具名进入日志，方便学习工具选择过程
            self.assertIn("调试日志测试内容", json.dumps(log_events, ensure_ascii=False))  # 新增代码: 验证工具结果进入日志，方便观察工具执行后模型看到什么
    def test_readable_debug_log_shows_model_decision_note(self) -> None:  # 新增代码: 测试 Markdown 日志会展示模型的决策说明，帮助初学者理解为什么调用工具
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 使用临时工作区隔离调试日志
            workspace = Path(raw_dir)  # 新增代码: 把临时目录转成 Path
            sample_file = workspace / "memory.md"  # 新增代码: 准备 read_file 工具要读取的文件
            sample_file.write_text("用户喜欢中文解释", encoding="utf-8")  # 新增代码: 写入测试内容，模拟长期记忆
            model = ToolCallingFakeModel(  # 新增代码: 构造假模型，显式带上 decision_note
                [  # 新增代码: 假模型返回序列开始
                    ModelMessage(  # 新增代码: 第一轮模型决定调用工具
                        decision_note="用户想读取 memory.md，所以我决定调用 read_file 工具。",  # 新增代码: 这是给日志展示的决策说明
                        text="",  # 新增代码: 工具调用轮通常没有最终文本
                        tool_calls=[ToolCall(name="read_file", arguments={"path": "memory.md"})],  # 新增代码: 请求读取 memory.md
                    ),  # 新增代码: 第一轮模型消息结束
                    ModelMessage(decision_note="工具已经返回内容，所以我现在可以总结。", text="memory.md 记录了用户喜欢中文解释。"),  # 新增代码: 第二轮模型根据工具结果回答
                ]  # 新增代码: 假模型返回序列结束
            )  # 新增代码: 假模型创建结束
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码: 创建 agent
            agent.run("请读取 memory.md")  # 新增代码: 运行一次完整工具调用流程
            log_path = workspace / "debug_logs" / "agent_debug.jsonl"  # 新增代码: 定位机器 JSONL 日志
            latest_path = workspace / "debug_logs" / "latest_run_readable.md"  # 新增代码: 定位最新一轮 Markdown 日志
            log_text = log_path.read_text(encoding="utf-8")  # 新增代码: 读取 JSONL 文本，确认 decision_note 被结构化记录
            latest_text = latest_path.read_text(encoding="utf-8")  # 新增代码: 读取 Markdown 文本，确认用户能看见决策说明
            self.assertIn("decision_note", log_text)  # 新增代码: 验证 JSONL 里保留 decision_note 字段
            self.assertIn("用户想读取 memory.md", log_text)  # 新增代码: 验证 JSONL 里保留具体决策说明
            self.assertIn("## 模型决策说明", latest_text)  # 新增代码: 验证 Markdown 有专门区块展示决策说明
            self.assertIn("用户想读取 memory.md，所以我决定调用 read_file 工具。", latest_text)  # 新增代码: 验证 Markdown 展示第一轮工具选择原因
            self.assertIn("工具已经返回内容，所以我现在可以总结。", latest_text)  # 新增代码: 验证 Markdown 展示第二轮最终回答原因
    def test_codex_cli_output_schema_requires_decision_note(self) -> None:  # 新增代码: 测试严格输出 schema 要求模型返回 decision_note，确保真模型也会写决策说明
        schema = CodexCliChatModel._output_schema()  # 新增代码: 获取真实传给 Codex/OAuth 的结构化输出 schema
        self.assertIn("decision_note", schema["properties"])  # 新增代码: 验证根字段里声明了 decision_note
        self.assertEqual(schema["properties"]["decision_note"]["type"], "string")  # 新增代码: 验证 decision_note 是字符串
        self.assertIn("decision_note", schema["required"])  # 新增代码: 验证严格 schema 要求模型必须返回 decision_note
    def test_codex_output_schema_uses_per_tool_anyof_branches(self) -> None:  # 新增代码+OutputProtocolV2: 验证输出协议从共享 arguments 升级为按工具名分支；若没有这行代码，参数串味的结构风险会再次回归
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+OutputProtocolV2: 用真实内置工具生成结构化输出 schema；若没有这行代码，测试无法覆盖真实请求体形状
        item_schema = self._tool_call_item_schema_for_test(schema)  # 新增代码+OutputProtocolV2: 定位单个 tool_call 的 schema；若没有这行代码，无法检查 anyOf 分支
        self.assertIn("anyOf", item_schema)  # 新增代码+OutputProtocolV2: 断言工具调用 item 使用 anyOf 分支；若没有这行代码，共享 arguments 对象仍可能被误认为完成 Phase 2
        branches = item_schema["anyOf"]  # 新增代码+OutputProtocolV2: 读取所有工具专属分支；若没有这行代码，后续无法检查分支数量和字段
        self.assertGreater(len(branches), 5)  # 新增代码+OutputProtocolV2: 断言真实工具池生成多个分支；若没有这行代码，单个兜底分支可能假装 per-tool
        read_branch = self._tool_call_branch_for_name(schema, "read_file")  # 新增代码+OutputProtocolV2: 读取 read_file 专属分支；若没有这行代码，测试无法证明分支按工具名定位
        read_properties = read_branch["properties"]  # 新增代码+OutputProtocolV2: 读取 read_file 分支字段；若没有这行代码，无法检查 name 和 arguments
        self.assertEqual(read_properties["name"]["enum"], ["read_file"])  # 新增代码+OutputProtocolV2: 断言分支工具名被单值 enum 约束；若没有这行代码，多个工具可能共用同一参数分支
        self.assertIn("arguments", read_properties)  # 新增代码+OutputProtocolV2: 断言分支仍保留 arguments 字段；若没有这行代码，解析层无法构造 ToolCall 参数
    def test_parse_model_message_accepts_arguments_by_tool_for_selected_name(self) -> None:  # 新增代码+OutputProtocolV2: 验证解析器能兼容按工具名存放参数的输出形态；若没有这行代码，未来 fallback 输出协议可能解析不到参数
        raw_output = json.dumps({"decision_note": "需要读文件", "text": "", "tool_calls": [{"name": "read_file", "arguments_by_tool": {"read_file": {"path": "memory.md"}, "write_file": {"path": "wrong.md", "content": "bad"}}}]}, ensure_ascii=False)  # 新增代码+OutputProtocolV2: 构造含 arguments_by_tool 的模型 JSON；若没有这行代码，兼容解析分支没有测试输入
        message = CodexCliChatModel._parse_model_message(raw_output)  # 新增代码+OutputProtocolV2: 调用真实模型输出解析器；若没有这行代码，测试不会覆盖生产解析逻辑
        self.assertEqual(len(message.tool_calls), 1)  # 新增代码+OutputProtocolV2: 断言只解析出一个工具调用；若没有这行代码，错误解析多个分支不会被发现
        self.assertEqual(message.tool_calls[0].name, "read_file")  # 新增代码+OutputProtocolV2: 断言工具名保留为 read_file；若没有这行代码，解析器可能丢失工具名
        self.assertEqual(message.tool_calls[0].arguments, {"path": "memory.md"})  # 新增代码+OutputProtocolV2: 断言只取 read_file 对应参数；若没有这行代码，write_file 参数可能串入 read_file
    def test_codex_output_schema_includes_todo_arguments_when_tools_are_available(self) -> None:  # 新增代码+TodoWrite: 验证模型结构化输出允许 todo_write 的 todos 参数；若省略: 真模型可能看见工具却无法输出 todos 字段
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+TodoWrite: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持旧 TodoWrite 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("todos", argument_schema["properties"])  # 新增代码+TodoWrite: 断言 todos 参数进入严格输出 schema；若省略: todo_write 参数可能被模型适配层过滤
        self.assertIn("todos", argument_schema["required"])  # 新增代码+TodoWrite: 断言严格 schema 要求 todos 字段出现，未用工具时可填 null；若省略: Responses 严格格式可能不稳定
        self.assertEqual(argument_schema["properties"]["todos"]["items"]["properties"]["status"]["enum"], ["pending", "in_progress", "completed"])  # 新增代码+TodoWrite: 断言状态枚举进入模型输出约束；若省略: 模型可能输出 doing/done 等无效状态
    def test_codex_output_schema_requires_all_nested_todo_item_properties_for_responses_api(self) -> None:  # 新增代码+StrictSchema: 复现 Codex Responses API 要求嵌套对象 required 覆盖所有 properties；若省略: 截图里的 missing id schema 错误会回归
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+StrictSchema: 用真实工具列表生成 OAuth/Codex 会发送的输出 schema；若省略: 测试不会覆盖真实请求体
        argument_schema = self._tool_argument_schema_for_name(schema, "todo_write")  # 修改代码+OutputProtocolV2: 精确读取 todo_write 分支 arguments；若没有这行代码，严格 schema 测试无法证明该工具自己的嵌套 required 正确
        todo_items_schema = argument_schema["properties"]["todos"]["items"]  # 新增代码+StrictSchema: 定位到截图报错的 todos.items 对象；若省略: 测试无法精确覆盖 missing id 位置
        self.assertEqual(set(todo_items_schema["required"]), set(todo_items_schema["properties"]))  # 新增代码+StrictSchema: 断言 required 包含 id/content/status/priority 全部字段；若省略: Codex 后端会拒绝 text.format.schema
        self.assertIn("id", todo_items_schema["required"])  # 新增代码+StrictSchema: 断言 id 不再缺失；若省略: 截图中的 Missing 'id' 会再次出现
        self.assertIn("priority", todo_items_schema["required"])  # 新增代码+StrictSchema: 断言另一个可选字段 priority 也进入 required；若省略: 修完 id 后可能继续暴露 priority 缺失错误
    def test_codex_output_schema_sets_additional_properties_false_for_all_object_nodes(self) -> None:  # 新增代码+StrictSchema: 验证所有 object schema 都关闭额外字段；若省略: prompt_arguments 这类开放对象会被 Codex API 拒绝
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+StrictSchema: 用真实工具列表生成实际发送给 Codex 的输出 schema；若省略: 测试无法覆盖 OAuth/API 真实请求体
        bad_paths: list[str] = []  # 新增代码+StrictSchema: 收集违反 strict 规则的路径；若省略: 失败时看不到是哪一个对象 schema 出错

        def includes_object_type(raw_schema: dict[str, object]) -> bool:  # 新增代码+StrictSchema: 判断一个 schema 是否包含 object 类型；若省略: list 联合类型里的 object 会漏检
            raw_type = raw_schema.get("type")  # 新增代码+StrictSchema: 读取 type 字段；若省略: 无法判断当前节点是否是对象
            return raw_type == "object" or (isinstance(raw_type, list) and "object" in raw_type)  # 新增代码+StrictSchema: 支持单类型和联合类型；若省略: ["object","null"] 这种截图路径会漏掉

        def walk(raw_schema: object, path: str) -> None:  # 新增代码+StrictSchema: 递归遍历 schema 树；若省略: 只能检查最外层，嵌套对象仍可能漏掉
            if not isinstance(raw_schema, dict):  # 新增代码+StrictSchema: 只处理字典 schema；若省略: 字符串或布尔 schema 会导致 .get 报错
                return  # 新增代码+StrictSchema: 非字典节点直接跳过；若省略: 遍历会在非对象节点崩溃
            if includes_object_type(raw_schema) and raw_schema.get("additionalProperties") is not False:  # 新增代码+StrictSchema: strict response_format 要求对象禁止额外字段；若省略: HTTP 400 invalid_json_schema 会继续出现
                bad_paths.append(path)  # 新增代码+StrictSchema: 保存违规路径方便定位；若省略: 失败只能看到数量不能看到位置
            raw_properties = raw_schema.get("properties")  # 新增代码+StrictSchema: 读取 properties 继续递归；若省略: 对象字段下的嵌套 schema 不会被检查
            if isinstance(raw_properties, dict):  # 新增代码+StrictSchema: 只有 properties 是对象时才遍历；若省略: 异常 schema 会让测试崩溃
                for property_name, property_schema in raw_properties.items():  # 新增代码+StrictSchema: 遍历每个字段 schema；若省略: 子字段不会被检查
                    walk(property_schema, f"{path}.properties.{property_name}")  # 新增代码+StrictSchema: 带路径递归检查子字段；若省略: 失败路径不完整
            raw_items = raw_schema.get("items")  # 新增代码+StrictSchema: 读取数组元素 schema；若省略: todos/items/calls 这类数组对象会漏检
            if isinstance(raw_items, dict):  # 新增代码+StrictSchema: 只有 items 是对象时才递归；若省略: 非对象 items 会导致错误
                walk(raw_items, f"{path}.items")  # 新增代码+StrictSchema: 检查数组元素 schema；若省略: 截图中的 type.0.items 路径不会被覆盖
            raw_any_of = raw_schema.get("anyOf")  # 新增代码+OutputProtocolV2: 读取 per-tool 输出协议的 anyOf 分支；若没有这行代码，分支内 arguments 对象不会被 strict 检查覆盖
            if isinstance(raw_any_of, list):  # 新增代码+OutputProtocolV2: 只有 anyOf 是列表时才遍历；若没有这行代码，异常 schema 会让测试报无关错误
                for index, branch_schema in enumerate(raw_any_of):  # 新增代码+OutputProtocolV2: 遍历每个工具专属输出分支；若没有这行代码，browser_open 等分支的 additionalProperties 回归不会被发现
                    walk(branch_schema, f"{path}.anyOf.{index}")  # 新增代码+OutputProtocolV2: 递归检查分支 schema；若没有这行代码，StrictSchema 测试仍只覆盖旧共享路径

        walk(schema, "$")  # 新增代码+StrictSchema: 从根 schema 开始检查；若省略: bad_paths 永远为空
        self.assertEqual(bad_paths, [])  # 新增代码+StrictSchema: 断言没有开放 object；若省略: prompt_arguments/additionalProperties=true 会再次发到 Codex 后端
    def test_codex_output_schema_includes_background_command_arguments(self) -> None:  # 新增代码+后台命令: 验证结构化输出允许后台命令参数；若省略: 真模型可能看见工具却无法输出 command_id 等字段
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+后台命令: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持后台命令参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("command", argument_schema["properties"])  # 新增代码+后台命令: 断言启动命令的 command 参数进入输出 schema；若省略: 模型无法发起后台命令
        self.assertIn("command_id", argument_schema["properties"])  # 新增代码+后台命令: 断言读取/停止需要的 command_id 参数进入输出 schema；若省略: 模型无法引用后台进程
        self.assertIn("max_chars", argument_schema["properties"])  # 新增代码+后台命令: 断言读取输出长度参数进入输出 schema；若省略: 长输出无法受控截断
        self.assertIn("cwd", argument_schema["properties"])  # 新增代码+后台命令: 断言工作目录参数进入输出 schema；若省略: 模型不能指定项目子目录运行命令
    def test_codex_output_schema_includes_task_management_arguments(self) -> None:  # 新增代码+TaskManagement: 验证结构化输出允许任务管理工具参数；若省略: 真模型可能看见工具却无法输出筛选或更新字段
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+TaskManagement: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持任务管理参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("status", argument_schema["properties"])  # 新增代码+TaskManagement: 断言 task_list 的 status 参数进入输出 schema；若省略: 模型无法按任务状态筛选
        self.assertIn("task_id", argument_schema["properties"])  # 新增代码+TaskManagement: 断言 task_get/task_update 的 task_id 参数进入输出 schema；若省略: 模型无法指定目标任务
        self.assertIn("label", argument_schema["properties"])  # 新增代码+TaskManagement: 断言 task_update 的 label 参数进入输出 schema；若省略: 模型无法给任务加短标签
        self.assertIn("notes", argument_schema["properties"])  # 新增代码+TaskManagement: 断言 task_update 的 notes 参数进入输出 schema；若省略: 模型无法保存任务备注
        self.assertIn("max_results", argument_schema["properties"])  # 新增代码+TaskManagement: 断言 task_list 的 max_results 参数进入输出 schema；若省略: 模型无法控制列表长度
    def test_codex_output_schema_includes_team_communication_arguments(self) -> None:  # 修改代码+TeamCommunicationLifecycle: 验证结构化输出允许 team 通信、读取确认和删除参数；若省略: 真模型可能看见工具却无法输出必要字段
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+TeamCommunication: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 team 通信参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("peer_id", argument_schema["properties"])  # 新增代码+TeamCommunication: 断言 send_message 的 peer_id 参数进入输出 schema；若省略: 模型无法指定收件 peer
        self.assertIn("message", argument_schema["properties"])  # 新增代码+TeamCommunication: 断言 send_message 的 message 参数进入输出 schema；若省略: 模型无法写入消息内容
        self.assertIn("sender", argument_schema["properties"])  # 新增代码+TeamCommunication: 断言 send_message 的 sender 参数进入输出 schema；若省略: 模型无法标记消息来源
        self.assertIn("name", argument_schema["properties"])  # 新增代码+TeamCommunication: 断言 team_create 的 name 参数进入输出 schema；若省略: 模型无法给 peer 起名
        self.assertIn("role", argument_schema["properties"])  # 新增代码+TeamCommunication: 断言 team_create 的 role 参数进入输出 schema；若省略: 模型无法标记 peer 角色
        self.assertIn("notes", argument_schema["properties"])  # 新增代码+TeamCommunication: 断言 team_create 的 notes 参数进入输出 schema；若省略: 模型无法写入 peer 说明
        self.assertIn("message_id", argument_schema["properties"])  # 新增代码+TeamCommunicationLifecycle: 断言 ack_peer_message 的 message_id 参数进入输出 schema；若省略: 模型无法确认具体消息
        self.assertIn("include_acknowledged", argument_schema["properties"])  # 新增代码+TeamCommunicationLifecycle: 断言 read_peer_messages 的 include_acknowledged 参数进入输出 schema；若省略: 模型无法读取已确认历史消息
        self.assertIn("confirm_delete", argument_schema["properties"])  # 新增代码+TeamCommunicationLifecycle: 断言 team_delete 的 confirm_delete 参数进入输出 schema；若省略: 模型无法显式确认删除 peer
        self.assertIn("prompt", argument_schema["properties"])  # 新增代码+TeamTaskBinding: 断言 team_start_task 的 prompt 参数进入输出 schema；若省略: 模型无法给绑定任务传目标
    def test_codex_output_schema_includes_tool_search_arguments(self) -> None:  # 新增代码+ToolSearch: 验证模型结构化输出允许 tool_search 的 query/max_results 参数；若省略: 真模型可能看见工具却无法输出搜索参数
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+ToolSearch: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 tool_search 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("query", argument_schema["properties"])  # 新增代码+ToolSearch: 断言工具搜索关键词参数进入输出 schema；若省略: 模型无法构造 tool_search 调用
        self.assertIn("max_results", argument_schema["properties"])  # 新增代码+ToolSearch: 断言搜索结果数量参数进入输出 schema；若省略: 模型无法控制返回工具数量
    def test_codex_output_schema_includes_mcp_resource_arguments(self) -> None:  # 新增代码+MCPResource: 验证结构化输出允许 MCP resource 工具参数；若省略: 真模型可能看见工具却无法输出 server/uri/max_chars
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+MCPResource: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 MCP resource 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("server", argument_schema["properties"])  # 新增代码+MCPResource: 断言 server 参数进入输出 schema；若省略: read_mcp_resource 无法指定 server
        self.assertIn("uri", argument_schema["properties"])  # 新增代码+MCPResource: 断言 uri 参数进入输出 schema；若省略: read_mcp_resource 无法指定资源地址
        self.assertIn("max_chars", argument_schema["properties"])  # 新增代码+MCPResource: 断言 max_chars 参数进入输出 schema；若省略: 读取资源无法控制返回长度
    def test_codex_output_schema_includes_mcp_prompt_arguments(self) -> None:  # 新增代码+MCPPrompt: 验证结构化输出允许 MCP prompt 工具参数；若省略: 真模型可能看见工具却无法输出 prompt 名和参数
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+MCPPrompt: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 MCP prompt 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("server", argument_schema["properties"])  # 新增代码+MCPPrompt: 断言 server 参数进入输出 schema；若省略: read_mcp_prompt 无法指定 prompt 来源
        self.assertIn("name", argument_schema["properties"])  # 新增代码+MCPPrompt: 断言 name 参数进入输出 schema；若省略: read_mcp_prompt 无法指定 prompt 名称
        self.assertIn("prompt_arguments", argument_schema["properties"])  # 新增代码+MCPPrompt: 断言 prompt_arguments 参数进入输出 schema；若省略: prompts/get 无法传入模板参数
        self.assertIn("max_chars", argument_schema["properties"])  # 新增代码+MCPPrompt: 断言 max_chars 参数进入输出 schema；若省略: 读取 prompt 无法控制返回长度
    def test_codex_output_schema_includes_skill_arguments(self) -> None:  # 新增代码+SkillLoad: 验证结构化输出允许 skill 工具参数；若省略: 真模型可能看见工具却无法输出 name/max_chars
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+SkillLoad: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 skill 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("name", argument_schema["properties"])  # 新增代码+SkillLoad: 断言 skill_load 的 name 参数进入输出 schema；若省略: 模型无法指定要加载的 skill
        self.assertIn("query", argument_schema["properties"])  # 新增代码+SkillLoad: 断言 skill_list 的 query 参数进入输出 schema；若省略: 模型无法按关键词筛选 skills
        self.assertIn("max_chars", argument_schema["properties"])  # 新增代码+SkillLoad: 断言 max_chars 参数进入输出 schema；若省略: 加载 skill 无法控制返回长度
    def test_codex_output_schema_includes_ask_user_question_arguments(self) -> None:  # 新增代码+AskUserQuestion: 验证结构化输出允许 ask_user_question 的 questions 参数；若省略: 真模型可能看见工具却无法输出问题数组
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+AskUserQuestion: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 ask_user_question 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("questions", argument_schema["properties"])  # 新增代码+AskUserQuestion: 断言 questions 参数进入输出 schema；若省略: 模型无法构造结构化提问调用
    def test_codex_output_schema_includes_task_arguments(self) -> None:  # 新增代码+TaskAgent: 验证结构化输出允许 task 的 prompt/allowed_tools/max_turns 参数；若省略: 真模型可能看见工具却无法构造子 agent 调用
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+TaskAgent: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 task 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("prompt", argument_schema["properties"])  # 新增代码+TaskAgent: 断言子任务 prompt 参数进入输出 schema；若省略: 模型无法说明子 agent 要做什么
        self.assertIn("allowed_tools", argument_schema["properties"])  # 新增代码+TaskAgent: 断言 allowed_tools 参数进入输出 schema；若省略: 模型无法限制子 agent 可用工具
        self.assertIn("max_turns", argument_schema["properties"])  # 新增代码+TaskAgent: 断言 max_turns 参数进入输出 schema；若省略: 模型无法限制子 agent 执行轮次
    def test_codex_output_schema_includes_task_lifecycle_arguments(self) -> None:  # 新增代码+TaskLifecycle: 验证结构化输出允许 task_output/task_stop 的 task_id 参数；若省略: 真模型可能看见工具却无法指定任务
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+TaskLifecycle: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 task lifecycle 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("task_id", argument_schema["properties"])  # 新增代码+TaskLifecycle: 断言 task_id 参数进入输出 schema；若省略: 模型无法查询或停止指定子任务
        self.assertIn("background", argument_schema["properties"])  # 新增代码+AsyncTask: 断言 background 参数进入输出 schema；若省略: 模型无法请求后台执行子任务
    def test_codex_output_schema_includes_plan_mode_arguments(self) -> None:  # 新增代码+PlanMode: 验证结构化输出允许 Plan mode 工具参数；若省略: 真模型可能看见工具却无法输出计划字段
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+PlanMode: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 Plan mode 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("reason", argument_schema["properties"])  # 新增代码+PlanMode: 断言进入计划模式的 reason 参数进入输出 schema；若省略: 模型无法说明为什么要计划
        self.assertIn("goal", argument_schema["properties"])  # 新增代码+PlanMode: 断言进入计划模式的 goal 参数进入输出 schema；若省略: 模型无法说明计划目标
        self.assertIn("steps", argument_schema["properties"])  # 新增代码+PlanMode: 断言计划步骤参数进入输出 schema；若省略: 模型无法输出结构化步骤
        self.assertIn("plan", argument_schema["properties"])  # 新增代码+PlanMode: 断言退出计划模式的 plan 参数进入输出 schema；若省略: 模型无法输出最终计划正文
        self.assertIn("executed_steps", argument_schema["properties"])  # 新增代码+PlanVerification: 断言计划验证的 executed_steps 参数进入输出 schema；若省略: 模型无法提交已执行步骤
        self.assertIn("evidence", argument_schema["properties"])  # 新增代码+PlanVerification: 断言计划验证的 evidence 参数进入输出 schema；若省略: 模型无法提交验证证据
        self.assertIn("open_items", argument_schema["properties"])  # 新增代码+PlanVerification: 断言计划验证的 open_items 参数进入输出 schema；若省略: 模型无法提交遗漏项
        self.assertIn("result", argument_schema["properties"])  # 新增代码+PlanVerification: 断言计划验证的 result 参数进入输出 schema；若省略: 模型无法声明验证结论
    def test_codex_output_schema_includes_worktree_arguments(self) -> None:  # 新增代码+WorktreeIsolation: 验证结构化输出允许 worktree 隔离工具参数；若省略: 真模型可能看见工具却无法输出隔离字段
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+WorktreeIsolation: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 worktree 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("worktree_path", argument_schema["properties"])  # 新增代码+WorktreeIsolation: 断言隔离目录参数进入输出 schema；若省略: 模型无法说明隔离状态指向哪里
        self.assertIn("summary", argument_schema["properties"])  # 新增代码+WorktreeIsolation: 断言退出总结参数进入输出 schema；若省略: 模型无法提交退出交接摘要
        self.assertIn("open_items", argument_schema["properties"])  # 新增代码+WorktreeIsolation: 断言遗漏项参数进入输出 schema；若省略: 模型无法说明隔离工作还有哪些风险
    def test_codex_output_schema_includes_lsp_arguments(self) -> None:  # 新增代码+LSP工具: 验证结构化输出允许 LSP 工具参数；若省略: 真模型可能看见工具却无法输出 symbol 参数
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+LSP工具: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 LSP 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("path", argument_schema["properties"])  # 新增代码+LSP工具: 断言文件路径参数进入输出 schema；若省略: 模型无法指定要分析的文件
        self.assertIn("symbol", argument_schema["properties"])  # 新增代码+LSP工具: 断言符号名参数进入输出 schema；若省略: 模型无法请求定义定位
        self.assertIn("max_results", argument_schema["properties"])  # 新增代码+LSP工具: 断言最大结果数参数进入输出 schema；若省略: 模型无法控制符号列表长度
    def test_codex_output_schema_includes_repl_arguments(self) -> None:  # 新增代码+REPL工具: 验证结构化输出允许 REPL 批量调用参数；若省略: 真模型可能看见工具却无法输出 calls 数组
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+REPL工具: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 REPL 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("calls", argument_schema["properties"])  # 新增代码+REPL工具: 断言 REPL 的 calls 数组进入输出 schema；若省略: 模型无法描述批量工具步骤
        self.assertIn("stop_on_error", argument_schema["properties"])  # 新增代码+REPL工具: 断言失败即停参数进入输出 schema；若省略: 模型无法控制子调用失败后的行为
        self.assertIn("max_output_chars", argument_schema["properties"])  # 新增代码+REPL工具: 断言输出截断参数进入输出 schema；若省略: 模型无法控制 REPL 输出长度
        call_item_schema = argument_schema["properties"]["calls"]["items"]  # 新增代码+REPL工具: 定位 calls 数组里的单个子调用 schema；若省略: 无法断言子调用字段约束
        self.assertIn("tool_name", call_item_schema["properties"])  # 新增代码+REPL工具: 断言每个子调用必须能指定工具名；若省略: REPL 不知道执行哪个工具
        self.assertIn("arguments", call_item_schema["properties"])  # 新增代码+REPL工具: 断言每个子调用必须能携带参数对象；若省略: REPL 子工具无法收到入参
    def test_codex_output_schema_includes_cron_monitor_arguments(self) -> None:  # 新增代码+CronMonitor: 验证结构化输出允许 Cron/Monitor 相关参数；若省略: 真模型可能看见工具却无法输出 schedule/action 等字段
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+CronMonitor: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 Cron/Monitor 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("cron_id", argument_schema["properties"])  # 新增代码+CronMonitor: 断言 cron 删除参数进入输出 schema；若省略: 模型无法指定要删除的定时记录
        self.assertIn("schedule", argument_schema["properties"])  # 新增代码+CronMonitor: 断言定时说明参数进入输出 schema；若省略: 模型无法登记触发时间
        self.assertIn("prompt", argument_schema["properties"])  # 新增代码+CronMonitor: 断言定时任务提示词进入输出 schema；若省略: 定时记录不知道到点应检查什么
        self.assertIn("action", argument_schema["properties"])  # 新增代码+CronMonitor: 断言 monitor 多动作参数进入输出 schema；若省略: 模型无法选择创建、列出、删除或记录结果
        self.assertIn("state", argument_schema["properties"])  # 新增代码+CronMonitor: 断言列表筛选状态参数进入输出 schema；若省略: 模型无法筛选 active/deleted/all 记录
        self.assertIn("monitor_id", argument_schema["properties"])  # 新增代码+CronMonitor: 断言 monitor id 参数进入输出 schema；若省略: 模型无法引用具体监控记录
        self.assertIn("target", argument_schema["properties"])  # 新增代码+CronMonitor: 断言 monitor 目标参数进入输出 schema；若省略: 监控记录不知道观察对象
        self.assertIn("condition", argument_schema["properties"])  # 新增代码+CronMonitor: 断言 monitor 触发条件参数进入输出 schema；若省略: 监控记录不知道何时算命中
        self.assertIn("result_status", argument_schema["properties"])  # 新增代码+CronMonitor: 断言最近观察状态参数进入输出 schema；若省略: 模型无法记录 monitor 检查结果状态
        self.assertIn("confirm_delete", argument_schema["properties"])  # 新增代码+CronMonitor: 断言删除确认参数进入输出 schema；若省略: 模型无法显式确认删除记录
    def test_codex_output_schema_includes_notebook_arguments(self) -> None:  # 新增代码+Notebook工具: 验证结构化输出允许 Notebook 工具参数；若省略: 真模型可能看见工具却无法输出 cell_index/source
        schema = CodexCliChatModel._output_schema(tools=TOOL_SCHEMAS)  # 新增代码+Notebook工具: 用真实内置工具列表生成输出 schema；若省略: 测试不会覆盖实际模型调用路径
        argument_schema = self._merged_tool_argument_schema(schema)  # 修改代码+OutputProtocolV2: 汇总所有工具分支参数以保持 Notebook 参数存在性测试；若没有这行代码，测试会继续依赖共享 arguments
        self.assertIn("cell_index", argument_schema["properties"])  # 新增代码+Notebook工具: 断言 cell_index 参数进入输出 schema；若省略: 模型无法指定要编辑哪个 cell
        self.assertIn("source", argument_schema["properties"])  # 新增代码+Notebook工具: 断言 source 参数进入输出 schema；若省略: 模型无法提交新的 cell 内容
    def test_codex_cli_model_parses_tool_call_from_structured_output(self) -> None:  # 新增代码: 测试 Codex CLI 桥接模型能解析结构化工具调用输出；若省略: 真模型桥接层没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 创建临时目录放输出文件，避免污染真实 learning_agent 目录
            workspace = Path(raw_dir)  # 新增代码: 把临时目录转成 Path，便于作为 Codex CLI 工作目录传给模型
            captured_prompt: list[str] = []  # 新增代码: 记录传给假子进程的 prompt，确保测试能检查上下文是否被发送

            def fake_run_codex(command: list[str], prompt: str, output_path: Path) -> subprocess.CompletedProcess[str]:  # 新增代码: 定义假的 codex exec 执行器，不联网也不消耗额度
                captured_prompt.append(prompt)  # 新增代码: 保存 prompt，验证桥接模型确实把消息历史写进提示词
                output_path.write_text(  # 新增代码: 模拟 codex exec 按 --output-last-message 写出的最终结构化 JSON
                    '{"text":"","tool_calls":[{"name":"read_file","arguments":{"path":"memory.md"}}]}',  # 新增代码: 这是模型请求 read_file 工具的最小 JSON
                    encoding="utf-8",  # 新增代码: 使用 UTF-8 写入，避免中文或 JSON 在 Windows 上出现编码问题
                )  # 新增代码: 写入模拟输出结束
                return subprocess.CompletedProcess(command, 0, "", "")  # 新增代码: 返回成功的子进程结果，模拟 codex exec 正常退出

            model = CodexCliChatModel(  # 新增代码: 创建 Codex CLI 桥接模型，并注入假执行器以避免真实调用
                codex_command="codex",  # 新增代码: 模拟使用名为 codex 的命令；测试不会真正执行它
                model="gpt-5.5",  # 新增代码: 指定目标模型名，验证命令参数会带上 GPT-5.5
                cwd=workspace,  # 新增代码: 指定工作目录，模拟真实启动时所在项目目录
                run_codex=fake_run_codex,  # 新增代码: 注入假的子进程函数，让测试可控且不联网
            )  # 新增代码: CodexCliChatModel 构造结束
            message = model.chat(  # 新增代码: 调用桥接模型，模拟 agent 把历史消息和工具 schema 交给 Codex
                messages=[{"role": "user", "content": "请读取 memory.md"}],  # 新增代码: 提供一条用户消息，验证 prompt 会包含它
                tools=[],  # 新增代码: 此测试只验证解析，不需要真实工具 schema
            )  # 新增代码: 模型调用结束

            self.assertEqual(message.text, "")  # 新增代码: 验证 JSON 里的文本被正确解析为空字符串
            self.assertEqual(len(message.tool_calls), 1)  # 新增代码: 验证解析出一个工具调用
            self.assertEqual(message.tool_calls[0].name, "read_file")  # 新增代码: 验证工具名是 read_file
            self.assertEqual(message.tool_calls[0].arguments["path"], "memory.md")  # 新增代码: 验证工具参数 path 被正确保留
            self.assertIn("gpt-5.5", model.last_command)  # 修改代码: 验证实际命令参数数组中包含 GPT-5.5 模型名
            self.assertNotIn("--ask-for-approval", model.last_command)  # 新增代码: 回归测试，确保不再传当前 Codex exec 不支持的审批参数
            self.assertIn("请读取 memory.md", captured_prompt[0])  # 新增代码: 验证用户消息进入了 Codex prompt
            self.assertIn("完整满足最后一条用户消息", captured_prompt[0])  # 新增代码+最终答案完整性: 验证模型适配器明确要求 text 完整满足用户输出要求；若没有这行代码，复杂任务可能只回答天气而漏掉攻略
            self.assertIn("text 字段内可以使用用户要求的 Markdown", captured_prompt[0])  # 新增代码+最终答案完整性: 验证适配器允许 Markdown 放在 JSON 的 text 字段里；若没有这行代码，模型可能误以为不能按用户标题输出
    def test_codex_cli_output_schema_is_strict_for_nested_arguments(self) -> None:  # 新增代码: 测试输出 schema 的内层 arguments 对象足够严格，避免 Codex API 拒绝
        schema = CodexCliChatModel._output_schema()  # 新增代码: 直接取 Codex CLI 桥接模型要传给 codex exec 的 JSON Schema
        read_arguments = self._tool_argument_schema_for_name(schema, "read_file")  # 修改代码+OutputProtocolV2: 读取 read_file 分支自己的 arguments schema；若没有这行代码，测试会继续依赖旧共享 arguments 路径
        write_arguments = self._tool_argument_schema_for_name(schema, "write_file")  # 修改代码+OutputProtocolV2: 读取 write_file 分支自己的 arguments schema；若没有这行代码，无法证明写文件参数和读文件参数已经分开
        append_arguments = self._tool_argument_schema_for_name(schema, "append_memory")  # 修改代码+OutputProtocolV2: 读取 append_memory 分支自己的 arguments schema；若没有这行代码，无法证明记忆追加参数没有混入文件参数
        self.assertEqual(set(read_arguments["properties"]), {"path"})  # 修改代码+OutputProtocolV2: 验证 read_file 只声明 path；若没有这行代码，content/text 混入 read_file 的回归不会被发现
        self.assertEqual(set(write_arguments["properties"]), {"path", "content"})  # 修改代码+OutputProtocolV2: 验证 write_file 只声明 path/content；若没有这行代码，text 混入 write_file 的回归不会被发现
        self.assertEqual(set(append_arguments["properties"]), {"text"})  # 修改代码+OutputProtocolV2: 验证 append_memory 只声明 text；若没有这行代码，文件 path/content 混入记忆工具的回归不会被发现
        self.assertEqual(read_arguments["required"], ["path"])  # 修改代码+OutputProtocolV2: 验证 read_file strict schema 的 required 只覆盖自己的参数；若没有这行代码，Codex strict 输出可能重新要求无关字段
        self.assertEqual(write_arguments["required"], ["path", "content"])  # 修改代码+OutputProtocolV2: 验证 write_file strict schema 的 required 只覆盖自己的参数；若没有这行代码，写文件工具可能缺少必要字段约束
        self.assertEqual(append_arguments["required"], ["text"])  # 修改代码+OutputProtocolV2: 验证 append_memory strict schema 的 required 只覆盖自己的参数；若没有这行代码，记忆工具可能重新继承文件字段
        self.assertIs(read_arguments["additionalProperties"], False)  # 修改代码+OutputProtocolV2: 验证 read_file 禁止额外字段；若没有这行代码，read_file 仍可能接受 confirm_real_profile 等无关参数
        self.assertIs(write_arguments["additionalProperties"], False)  # 修改代码+OutputProtocolV2: 验证 write_file 禁止额外字段；若没有这行代码，write_file 仍可能接受其他工具参数
        self.assertIs(append_arguments["additionalProperties"], False)  # 修改代码+OutputProtocolV2: 验证 append_memory 禁止额外字段；若没有这行代码，append_memory 仍可能接受文件或浏览器参数
    def test_codex_oauth_model_posts_authenticated_responses_request(self) -> None:  # 新增代码: 测试 OAuth/API 直连模型会带 Bearer token 请求 Codex responses 端点
        calls: list[dict[str, object]] = []  # 新增代码: 保存 fake HTTP 收到的请求，方便断言 URL、headers、body

        def fake_post_json(url: str, headers: dict[str, str], body: dict[str, object]) -> dict[str, object]:  # 新增代码: 定义假的 HTTP POST，不联网也能验证请求形状
            calls.append({"url": url, "headers": headers, "body": body})  # 新增代码: 记录本次请求的全部关键数据
            return {"output_text": '{"text":"","tool_calls":[{"name":"read_file","arguments":{"path":"memory.md"}}]}'}  # 新增代码: 模拟 Codex responses 返回结构化 JSON 文本

        token_store = FakeOAuthTokenStore(  # 新增代码: 准备一个已有且未过期的 OAuth token store
            CodexOAuthTokens(  # 新增代码: 创建 token 数据对象
                access_token="access-123",  # 新增代码: 模拟访问 token
                refresh_token="refresh-123",  # 新增代码: 模拟刷新 token
                expires_at=9999999999999,  # 新增代码: 设置很远的过期时间，确保本测试不触发 refresh
                account_id="account-abc",  # 新增代码: 模拟 ChatGPT account id，用于验证请求头
            )  # 新增代码: token 数据对象结束
        )  # 新增代码: token store 创建结束
        model = CodexOAuthChatModel(  # 新增代码: 创建 OAuth/API 直连模型，并注入 fake HTTP 和 fake token store
            model="gpt-5.5",  # 新增代码: 指定目标模型名
            token_store=token_store,  # 新增代码: 使用内存 token store，避免碰真实登录文件
            post_json=fake_post_json,  # 新增代码: 使用假 HTTP，避免测试联网
            login_callback=lambda: (_ for _ in ()).throw(RuntimeError("测试不应该触发网页登录")),  # 新增代码: 如果误触发登录就立刻失败
        )  # 新增代码: OAuth 模型创建结束
        message = model.chat(  # 新增代码: 调用模型适配器，模拟 agent 把 messages/tools 发给真模型
            messages=[{"role": "user", "content": "请读取 memory.md"}],  # 新增代码: 提供一条用户消息
            tools=[],  # 新增代码: 本测试只关心外层请求与解析，不需要真实工具 schema
        )  # 新增代码: 模型调用结束

        self.assertEqual(calls[0]["url"], CodexOAuthChatModel.CODEX_API_ENDPOINT)  # 新增代码: 验证请求发往 Codex responses 端点
        self.assertEqual(calls[0]["headers"]["authorization"], "Bearer access-123")  # 新增代码: 验证请求头带上 OAuth access token
        self.assertEqual(calls[0]["headers"]["ChatGPT-Account-Id"], "account-abc")  # 新增代码: 验证组织/账号订阅头被带上
        self.assertEqual(calls[0]["body"]["model"], "gpt-5.5")  # 新增代码: 验证请求体使用目标模型名
        self.assertIn("模型适配器", str(calls[0]["body"]["instructions"]))  # 新增代码: 回归测试，验证 Codex 后端要求的顶层 instructions 字段存在
        self.assertIsInstance(calls[0]["body"]["input"], list)  # 新增代码: 回归测试，验证 Codex 后端要求 input 是 Responses 消息列表，不是普通字符串
        self.assertIs(calls[0]["body"]["store"], False)  # 新增代码: 回归测试，验证 Codex 后端要求显式设置 store=false
        self.assertIs(calls[0]["body"]["stream"], True)  # 新增代码: 回归测试，验证 Codex 后端要求显式设置 stream=true
        self.assertIn("请读取 memory.md", str(calls[0]["body"]["input"]))  # 新增代码: 验证用户消息进入了 responses input
        self.assertEqual(message.tool_calls[0].name, "read_file")  # 新增代码: 验证 responses 输出被解析为内部工具调用
        self.assertEqual(message.tool_calls[0].arguments["path"], "memory.md")  # 新增代码: 验证工具参数被正确保留
    def test_codex_oauth_model_retries_once_when_json_output_is_invalid(self) -> None:  # 新增代码+模型JSON恢复: 验证 OAuth 模型遇到坏 JSON 会自动修复重试一次；若没有这行代码，真实终端会反复停在“格式错误”。
        calls: list[dict[str, object]] = []  # 新增代码+模型JSON恢复: 记录 fake HTTP 请求，方便断言确实发起了第二次模型调用；若没有这行代码，测试无法区分重试和单次成功。

        def fake_post_json(url: str, headers: dict[str, str], body: dict[str, object]) -> dict[str, object]:  # 新增代码+模型JSON恢复: 定义可控响应函数；若没有这行代码，测试会触发真实网络请求。
            calls.append({"url": url, "headers": headers, "body": body})  # 新增代码+模型JSON恢复: 保存请求体以检查修复提示；若没有这行代码，重试是否带上下文不可审计。
            if len(calls) == 1:  # 新增代码+模型JSON恢复: 第一次模拟模型输出非法 JSON；若没有这行代码，无法复现本次真实验收失败。
                return {"output_text": '{"decision_note":"坏输出","text":"","tool_calls":[{"name":"read_file","arguments":{"path":"memory.md"}'}  # 新增代码+模型JSON恢复: 返回缺少结尾括号的坏 JSON；若没有这行代码，解析器不会进入修复路径。
            return {"output_text": '{"decision_note":"修复后请求工具","text":"","tool_calls":[{"name":"read_file","arguments":{"path":"memory.md"}}]}'}  # 新增代码+模型JSON恢复: 第二次返回合法工具调用；若没有这行代码，无法证明修复成功会继续任务。

        token_store = FakeOAuthTokenStore(  # 新增代码+模型JSON恢复: 准备未过期 token，避免测试走刷新或网页登录分支；若没有这行代码，失败原因会被认证流程干扰。
            CodexOAuthTokens(  # 新增代码+模型JSON恢复: 创建 token 数据对象；若没有这行代码，OAuth 模型没有可用凭据。
                access_token="access-123",  # 新增代码+模型JSON恢复: 模拟 access token；若没有这行代码，请求头无法构造。
                refresh_token="refresh-123",  # 新增代码+模型JSON恢复: 模拟 refresh token；若没有这行代码，token store 会被当成无效。
                expires_at=9999999999999,  # 新增代码+模型JSON恢复: 设置远期过期时间；若没有这行代码，测试会先刷新 token。
                account_id=None,  # 新增代码+模型JSON恢复: 本测试不需要账号头；若没有这行代码，构造函数参数不完整。
            )  # 新增代码+模型JSON恢复: token 数据对象结束；若没有这行代码，Python 语法不完整。
        )  # 新增代码+模型JSON恢复: token store 创建结束；若没有这行代码，Python 语法不完整。
        model = CodexOAuthChatModel(  # 新增代码+模型JSON恢复: 创建 OAuth 模型并注入 fake HTTP；若没有这行代码，测试无法调用 chat。
            model="gpt-5.5",  # 新增代码+模型JSON恢复: 指定模型名；若没有这行代码，请求体缺少可断言模型。
            token_store=token_store,  # 新增代码+模型JSON恢复: 使用内存 token；若没有这行代码，测试会读写真实 token 文件。
            post_json=fake_post_json,  # 新增代码+模型JSON恢复: 使用 fake HTTP；若没有这行代码，测试会联网。
            login_callback=lambda: (_ for _ in ()).throw(RuntimeError("测试不应该触发网页登录")),  # 新增代码+模型JSON恢复: 误触发登录时立即失败；若没有这行代码，测试可能弹真实浏览器。
        )  # 新增代码+模型JSON恢复: OAuth 模型创建结束；若没有这行代码，Python 语法不完整。
        message = model.chat(messages=[{"role": "user", "content": "请读取 memory.md"}], tools=[])  # 新增代码+模型JSON恢复: 执行模型调用；若没有这行代码，修复逻辑不会运行。

        self.assertEqual(len(calls), 2)  # 新增代码+模型JSON恢复: 断言第一次失败后只重试一次；若没有这行代码，可能出现无限重试或完全没有重试。
        self.assertIn("上一轮模型输出不是合法 JSON", str(calls[1]["body"]["input"]))  # 新增代码+模型JSON恢复: 确认第二次请求携带修复提示；若没有这行代码，重试可能仍然重复坏输出。
        self.assertEqual(message.tool_calls[0].name, "read_file")  # 新增代码+模型JSON恢复: 断言修复后工具调用被保留；若没有这行代码，自动修复可能只返回空文本。
        self.assertEqual(message.tool_calls[0].arguments["path"], "memory.md")  # 新增代码+模型JSON恢复: 断言修复后的参数正确；若没有这行代码，工具可能拿不到目标文件。
    def test_codex_oauth_model_refreshes_expired_token_before_request(self) -> None:  # 新增代码: 测试 access token 过期时会先 refresh 再请求模型
        calls: list[dict[str, object]] = []  # 新增代码: 保存 fake HTTP 请求历史，方便确认调用顺序

        def fake_post_json(url: str, headers: dict[str, str], body: dict[str, object]) -> dict[str, object]:  # 新增代码: 定义假的 HTTP POST，根据 URL 返回刷新结果或模型结果
            calls.append({"url": url, "headers": headers, "body": body})  # 新增代码: 记录请求历史
            if url.endswith("/oauth/token"):  # 新增代码: 如果请求的是 OAuth token 端点
                return {"access_token": "new-access", "refresh_token": "new-refresh", "expires_in": 3600, "id_token": ""}  # 新增代码: 模拟刷新成功
            return {"output_text": '{"text":"刷新后回答","tool_calls":[]}'}  # 新增代码: 模拟模型正常返回最终回答

        token_store = FakeOAuthTokenStore(  # 新增代码: 准备一个已过期的 token store
            CodexOAuthTokens(  # 新增代码: 创建过期 token 数据对象
                access_token="old-access",  # 新增代码: 模拟旧访问 token
                refresh_token="old-refresh",  # 新增代码: 模拟旧刷新 token
                expires_at=0,  # 新增代码: 设置为 0，确保模型调用前必须刷新
                account_id=None,  # 新增代码: 本测试不需要账号头
            )  # 新增代码: token 数据对象结束
        )  # 新增代码: token store 创建结束
        model = CodexOAuthChatModel(  # 新增代码: 创建 OAuth/API 直连模型
            model="gpt-5.5",  # 新增代码: 指定目标模型名
            token_store=token_store,  # 新增代码: 使用内存 token store
            post_json=fake_post_json,  # 新增代码: 使用假 HTTP
            login_callback=lambda: (_ for _ in ()).throw(RuntimeError("测试不应该触发网页登录")),  # 新增代码: 如果误触发登录就立刻失败
        )  # 新增代码: OAuth 模型创建结束
        message = model.chat(messages=[{"role": "user", "content": "你好"}], tools=[])  # 新增代码: 触发一次模型调用

        self.assertTrue(str(calls[0]["url"]).endswith("/oauth/token"))  # 新增代码: 验证第一步是刷新 token
        self.assertEqual(calls[0]["body"]["refresh_token"], "old-refresh")  # 新增代码: 验证刷新请求使用旧 refresh token
        self.assertEqual(calls[1]["headers"]["authorization"], "Bearer new-access")  # 新增代码: 验证模型请求使用刷新后的 access token
        self.assertEqual(token_store.saved[0].access_token, "new-access")  # 新增代码: 验证新 token 被保存
        self.assertEqual(message.text, "刷新后回答")  # 新增代码: 验证刷新后仍能解析模型最终文本
    def test_codex_oauth_model_relogins_when_refresh_token_is_rejected(self) -> None:  # 新增代码+OAuth重登录: 验证 refresh token 失效时会重新打开登录流程；若省略: 过期登录态只会报错不会引导用户重新认证
        calls: list[dict[str, object]] = []  # 新增代码+OAuth重登录: 记录刷新请求和模型请求的顺序；若省略: 测试无法确认重登录后是否继续请求模型
        login_calls: list[str] = []  # 新增代码+OAuth重登录: 记录是否触发网页登录回调；若省略: 测试无法证明 refresh 失败后真的走了重新认证

        def fake_post_json(url: str, headers: dict[str, str], body: dict[str, object]) -> dict[str, object]:  # 新增代码+OAuth重登录: 用假 HTTP 模拟 refresh 失败与模型成功；若省略: 测试会依赖真实网络且无法稳定复现
            calls.append({"url": url, "headers": headers, "body": body})  # 新增代码+OAuth重登录: 保存本次请求细节；若省略: 后续断言无法检查 token 使用是否正确
            if url.endswith("/oauth/token"):  # 新增代码+OAuth重登录: 区分 OAuth token 端点；若省略: fake HTTP 无法模拟 refresh token 被拒绝
                raise RuntimeError("HTTP 400: invalid_grant")  # 新增代码+OAuth重登录: 模拟 refresh token 已失效；若省略: 测试不会覆盖用户需要重新登录的关键场景
            return {"output_text": '{"text":"重新登录后回答","tool_calls":[]}'}  # 新增代码+OAuth重登录: 模拟重新登录后模型正常返回；若省略: 测试无法验证兜底流程最终可用

        def fake_login() -> CodexOAuthTokens:  # 新增代码+OAuth重登录: 用假登录替代真实浏览器；若省略: 单元测试会弹出网页登录窗口
            login_calls.append("login")  # 新增代码+OAuth重登录: 标记登录流程被触发；若省略: 测试无法断言浏览器认证入口被调用
            return CodexOAuthTokens(access_token="login-access", refresh_token="login-refresh", expires_at=9999999999999)  # 新增代码+OAuth重登录: 返回新 token；若省略: 重登录后没有凭证可继续调用模型

        token_store = FakeOAuthTokenStore(  # 新增代码+OAuth重登录: 准备一个 access token 已过期的 token store；若省略: 不会进入 refresh 失败分支
            CodexOAuthTokens(  # 新增代码+OAuth重登录: 创建旧 token 数据对象；若省略: token store 没有可加载的过期凭证
                access_token="old-access",  # 新增代码+OAuth重登录: 模拟旧 access token；若省略: 测试缺少旧凭证状态
                refresh_token="old-refresh",  # 新增代码+OAuth重登录: 模拟会被服务端拒绝的 refresh token；若省略: 无法复现 refresh token 失效
                expires_at=0,  # 新增代码+OAuth重登录: 强制 access token 过期；若省略: `_get_valid_tokens` 不会尝试刷新
                account_id=None,  # 新增代码+OAuth重登录: 本测试不关心账号头；若省略: 构造 token 对象时字段语义不完整
            )  # 新增代码+OAuth重登录: 旧 token 数据对象结束；若省略: Python 调用无法闭合
        )  # 新增代码+OAuth重登录: token store 创建结束；若省略: 模型没有可注入的测试 token store
        model = CodexOAuthChatModel(  # 新增代码+OAuth重登录: 创建 OAuth 模型并注入假依赖；若省略: 测试会碰真实 token 和网络
            model="gpt-5.5",  # 新增代码+OAuth重登录: 指定模型名；若省略: 构造函数缺少必需参数
            token_store=token_store,  # 新增代码+OAuth重登录: 使用内存 token store；若省略: 测试可能读写真机 token 文件
            post_json=fake_post_json,  # 新增代码+OAuth重登录: 使用假 HTTP；若省略: 测试可能访问真实 OpenAI 服务
            login_callback=fake_login,  # 新增代码+OAuth重登录: 使用假登录；若省略: 测试会打开浏览器
        )  # 新增代码+OAuth重登录: OAuth 模型创建结束；若省略: Python 调用无法闭合
        message = model.chat(messages=[{"role": "user", "content": "你好"}], tools=[])  # 新增代码+OAuth重登录: 发起一次模型调用触发 refresh 失败兜底；若省略: 测试不会执行待验证行为

        self.assertEqual(login_calls, ["login"])  # 新增代码+OAuth重登录: 验证 refresh token 被拒绝后触发一次重新登录；若省略: 旧 bug 可能悄悄回归
        self.assertTrue(str(calls[0]["url"]).endswith("/oauth/token"))  # 新增代码+OAuth重登录: 验证第一步确实尝试 refresh；若省略: 测试无法确认失败来源是刷新链路
        self.assertEqual(calls[1]["headers"]["authorization"], "Bearer login-access")  # 新增代码+OAuth重登录: 验证模型请求使用重新登录得到的新 access token；若省略: 可能继续拿旧 token 请求
        self.assertEqual(token_store.saved[-1].refresh_token, "login-refresh")  # 新增代码+OAuth重登录: 验证新 refresh token 被保存；若省略: 下次启动仍可能继续使用失效凭证
        self.assertEqual(message.text, "重新登录后回答")  # 新增代码+OAuth重登录: 验证用户最终收到正常回答；若省略: 兜底流程可能只登录但不继续完成请求
    def test_codex_oauth_model_relogins_once_when_api_returns_unauthorized(self) -> None:  # 新增代码+OAuth重登录: 验证 Codex API 返回 401 时会重新认证并只重试一次；若省略: 运行中登录失效仍会直接暴露给用户
        calls: list[dict[str, object]] = []  # 新增代码+OAuth重登录: 记录模型 API 请求历史；若省略: 测试无法确认是否发生一次重试
        login_calls: list[str] = []  # 新增代码+OAuth重登录: 记录网页登录回调次数；若省略: 测试无法防止无限重新登录

        def fake_post_json(url: str, headers: dict[str, str], body: dict[str, object]) -> dict[str, object]:  # 新增代码+OAuth重登录: 用假 HTTP 模拟首次 API 401、第二次成功；若省略: 测试无法稳定覆盖鉴权失效
            calls.append({"url": url, "headers": headers, "body": body})  # 新增代码+OAuth重登录: 保存请求信息；若省略: 断言无法看到旧 token 和新 token 的切换
            api_call_count = sum(1 for call in calls if call["url"] == CodexOAuthChatModel.CODEX_API_ENDPOINT)  # 新增代码+OAuth重登录: 统计当前是第几次 Codex API 调用；若省略: fake HTTP 无法只让第一次失败
            if url == CodexOAuthChatModel.CODEX_API_ENDPOINT and api_call_count == 1:  # 新增代码+OAuth重登录: 只让第一次模型请求返回 401；若省略: 测试不能模拟“登录态运行中失效后恢复”
                raise RuntimeError("HTTP 401: unauthorized")  # 新增代码+OAuth重登录: 模拟服务端拒绝旧 access token；若省略: 不会触发重新登录兜底
            return {"output_text": '{"text":"重新认证后回答","tool_calls":[]}'}  # 新增代码+OAuth重登录: 模拟重登录后的成功响应；若省略: 测试无法验证最终恢复

        def fake_login() -> CodexOAuthTokens:  # 新增代码+OAuth重登录: 用假登录替代真实网页登录；若省略: 单元测试会弹浏览器
            login_calls.append("login")  # 新增代码+OAuth重登录: 记录重新登录次数；若省略: 测试无法确认只登录一次
            return CodexOAuthTokens(access_token="fresh-access", refresh_token="fresh-refresh", expires_at=9999999999999)  # 新增代码+OAuth重登录: 返回新的有效凭证；若省略: API 401 后没有新 token 可重试

        token_store = FakeOAuthTokenStore(  # 新增代码+OAuth重登录: 准备一个未过期但会被 API 拒绝的旧 token；若省略: 测试无法覆盖 API 401 分支
            CodexOAuthTokens(  # 新增代码+OAuth重登录: 创建旧 token 数据对象；若省略: token store 无法返回凭证
                access_token="stale-access",  # 新增代码+OAuth重登录: 模拟本地看似有效但服务端已拒绝的 access token；若省略: 无法验证 401 前后的 token 切换
                refresh_token="stale-refresh",  # 新增代码+OAuth重登录: 模拟旧 refresh token；若省略: token 数据对象缺少刷新凭证
                expires_at=9999999999999,  # 新增代码+OAuth重登录: 设置本地未过期，确保本测试走 API 401 而不是 refresh 分支；若省略: 可能测试到错误路径
                account_id=None,  # 新增代码+OAuth重登录: 本测试不需要账号头；若省略: 构造数据语义不完整
            )  # 新增代码+OAuth重登录: 旧 token 数据对象结束；若省略: Python 调用无法闭合
        )  # 新增代码+OAuth重登录: token store 创建结束；若省略: 模型无法使用测试凭证
        model = CodexOAuthChatModel(  # 新增代码+OAuth重登录: 创建 OAuth 模型；若省略: 测试无法执行 chat
            model="gpt-5.5",  # 新增代码+OAuth重登录: 指定模型名；若省略: 构造函数缺少必需参数
            token_store=token_store,  # 新增代码+OAuth重登录: 注入内存 token store；若省略: 测试会污染真实 token 文件
            post_json=fake_post_json,  # 新增代码+OAuth重登录: 注入假 HTTP；若省略: 测试会依赖真实网络
            login_callback=fake_login,  # 新增代码+OAuth重登录: 注入假登录；若省略: 测试会打开浏览器
        )  # 新增代码+OAuth重登录: OAuth 模型创建结束；若省略: Python 调用无法闭合
        message = model.chat(messages=[{"role": "user", "content": "你好"}], tools=[])  # 新增代码+OAuth重登录: 发起一次模型调用触发 API 401 兜底；若省略: 待验证逻辑不会执行

        self.assertEqual(login_calls, ["login"])  # 新增代码+OAuth重登录: 验证只重新登录一次；若省略: 无法防止未来出现循环登录
        self.assertEqual(calls[0]["headers"]["authorization"], "Bearer stale-access")  # 新增代码+OAuth重登录: 验证第一次请求使用旧 token；若省略: 测试无法证明 401 来自旧凭证
        self.assertEqual(calls[1]["headers"]["authorization"], "Bearer fresh-access")  # 新增代码+OAuth重登录: 验证第二次请求改用新 token；若省略: 可能仍用旧 token 重试导致继续失败
        self.assertEqual(token_store.saved[-1].access_token, "fresh-access")  # 新增代码+OAuth重登录: 验证重新登录的新 token 已保存；若省略: 下次调用仍可能读取旧 token
        self.assertEqual(message.text, "重新认证后回答")  # 新增代码+OAuth重登录: 验证用户最终得到恢复后的回答；若省略: 只能确认登录，不能确认请求恢复
    def test_codex_oauth_timeout_message_does_not_force_relogin(self) -> None:  # 新增代码+OAuth超时提示: 验证读响应超时不会被误判成登录过期；若省略: 截图里的 timeout 可能被错误地拿去弹网页登录
        login_calls: list[str] = []  # 新增代码+OAuth超时提示: 记录是否误触发网页登录；若省略: 测试无法保护“超时不自动登录”的边界

        def fake_post_json(url: str, headers: dict[str, str], body: dict[str, object]) -> dict[str, object]:  # 新增代码+OAuth超时提示: 用假 HTTP 模拟 Codex 后端读响应超时；若省略: 测试无法稳定复现截图错误
            del url, headers, body  # 新增代码+OAuth超时提示: 明确这些参数本测试不使用；若省略: 读者会误以为参数会影响超时判断
            raise TimeoutError("The read operation timed out")  # 新增代码+OAuth超时提示: 模拟标准库读取响应超时；若省略: 不能覆盖用户截图里的错误形态

        def fake_login() -> CodexOAuthTokens:  # 新增代码+OAuth超时提示: 如果超时误触发登录就记录下来；若省略: 测试无法发现错误的网页登录行为
            login_calls.append("login")  # 新增代码+OAuth超时提示: 标记登录被调用；若省略: 误登录不会被测试捕捉
            return CodexOAuthTokens(access_token="fresh-access", refresh_token="fresh-refresh", expires_at=9999999999999)  # 新增代码+OAuth超时提示: 返回 token 只是为了满足函数签名；若省略: 假登录无法返回合法对象

        token_store = FakeOAuthTokenStore(  # 新增代码+OAuth超时提示: 准备一个未过期 token，确保不会先触发 refresh；若省略: 测试路径会被 token 缺失或过期干扰
            CodexOAuthTokens(  # 新增代码+OAuth超时提示: 创建有效 token 数据对象；若省略: 模型会走首次登录而不是 API 超时
                access_token="valid-access",  # 新增代码+OAuth超时提示: 模拟有效 access token；若省略: 请求头缺少鉴权上下文
                refresh_token="valid-refresh",  # 新增代码+OAuth超时提示: 模拟有效 refresh token；若省略: `_get_valid_tokens` 会触发网页登录
                expires_at=9999999999999,  # 新增代码+OAuth超时提示: 设置本地未过期；若省略: 测试可能进入 refresh 分支
                account_id=None,  # 新增代码+OAuth超时提示: 本测试不需要账号头；若省略: token 构造语义不完整
            )  # 新增代码+OAuth超时提示: token 数据对象结束；若省略: Python 调用无法闭合
        )  # 新增代码+OAuth超时提示: token store 创建结束；若省略: 模型没有测试 token store
        model = CodexOAuthChatModel(  # 新增代码+OAuth超时提示: 创建 OAuth 模型；若省略: 无法执行超时场景
            model="gpt-5.5",  # 新增代码+OAuth超时提示: 指定模型名；若省略: 构造函数缺少必需参数
            token_store=token_store,  # 新增代码+OAuth超时提示: 注入内存 token store；若省略: 测试可能读写真机凭证
            post_json=fake_post_json,  # 新增代码+OAuth超时提示: 注入超时 fake HTTP；若省略: 测试会依赖真实网络超时
            login_callback=fake_login,  # 新增代码+OAuth超时提示: 注入假登录以检测误登录；若省略: 无法断言超时边界
        )  # 新增代码+OAuth超时提示: OAuth 模型创建结束；若省略: Python 调用无法闭合
        message = model.chat(messages=[{"role": "user", "content": "你好"}], tools=[])  # 新增代码+OAuth超时提示: 发起一次模型调用触发 timeout；若省略: 待验证错误提示不会生成

        self.assertEqual(login_calls, [])  # 新增代码+OAuth超时提示: 验证 timeout 不会自动打开网页登录；若省略: 程序可能把网络问题误当登录过期
        self.assertIn("响应读取超时", message.text)  # 新增代码+OAuth超时提示: 验证用户能看懂这是读响应超时；若省略: 仍会只显示英文底层错误
        self.assertIn("不一定是 OAuth 登录过期", message.text)  # 新增代码+OAuth超时提示: 验证提示明确区分 timeout 与登录过期；若省略: 用户会继续误解为必须登录
    def test_codex_oauth_model_retries_once_when_api_response_times_out(self) -> None:  # 新增代码+OAuth超时重试: 复现工具返回后下一轮模型 API 读响应超时的问题；若省略: 真实浏览器工具成功后仍可能因为一次后端抖动直接失败
        calls: list[str] = []  # 新增代码+OAuth超时重试: 记录 Codex API 被调用几次；若省略: 无法确认是否只重试一次
        login_calls: list[str] = []  # 新增代码+OAuth超时重试: 记录是否误触发网页登录；若省略: 无法保护 timeout 不等于登录过期的边界

        def fake_post_json(url: str, headers: dict[str, str], body: dict[str, object]) -> dict[str, object]:  # 新增代码+OAuth超时重试: 用假 HTTP 先超时再成功；若省略: 测试会依赖真实网络抖动
            del headers, body  # 新增代码+OAuth超时重试: 本测试只关心调用次数和 URL；若省略: 未用参数会干扰读者理解
            calls.append(url)  # 新增代码+OAuth超时重试: 记录本次请求目标；若省略: 后续无法断言重试次数
            if url == CodexOAuthChatModel.CODEX_API_ENDPOINT and calls.count(CodexOAuthChatModel.CODEX_API_ENDPOINT) == 1:  # 新增代码+OAuth超时重试: 只让第一次模型请求超时；若省略: 无法模拟一次性后端抖动
                raise TimeoutError("The read operation timed out")  # 新增代码+OAuth超时重试: 模拟截图里的 read timeout；若省略: 红灯不会覆盖用户实际错误
            return {"output_text": '{"text":"超时重试后回答","tool_calls":[]}'}  # 新增代码+OAuth超时重试: 第二次请求返回正常结构化输出；若省略: 无法验证重试后能恢复回答

        def fake_login() -> CodexOAuthTokens:  # 新增代码+OAuth超时重试: 如果 timeout 被错误当成登录过期就记录；若省略: 无法断言不会打开网页登录
            login_calls.append("login")  # 新增代码+OAuth超时重试: 标记登录被调用；若省略: 误登录不会被测试发现
            return CodexOAuthTokens(access_token="fresh-access", refresh_token="fresh-refresh", expires_at=9999999999999)  # 新增代码+OAuth超时重试: 返回合法 token 满足函数签名；若省略: 假登录不完整

        token_store = FakeOAuthTokenStore(  # 新增代码+OAuth超时重试: 准备未过期 token，确保只测试 API 调用重试；若省略: 可能先进入 refresh/login 分支
            CodexOAuthTokens(  # 新增代码+OAuth超时重试: 创建有效 token 数据对象；若省略: 模型没有可用凭证
                access_token="valid-access",  # 新增代码+OAuth超时重试: 模拟有效 access token；若省略: 请求头没有鉴权上下文
                refresh_token="valid-refresh",  # 新增代码+OAuth超时重试: 模拟有效 refresh token；若省略: `_get_valid_tokens` 会走登录分支
                expires_at=9999999999999,  # 新增代码+OAuth超时重试: 设置本地不过期；若省略: 测试会被 token 刷新逻辑干扰
                account_id=None,  # 新增代码+OAuth超时重试: 本测试不需要账号头；若省略: token 构造语义不完整
            )  # 新增代码+OAuth超时重试: token 数据对象结束；若省略: Python 调用无法闭合
        )  # 新增代码+OAuth超时重试: token store 创建结束；若省略: 模型无法加载测试凭证
        model = CodexOAuthChatModel(  # 新增代码+OAuth超时重试: 创建 OAuth 模型；若省略: 无法执行 chat 行为
            model="gpt-5.5",  # 新增代码+OAuth超时重试: 指定模型名；若省略: 构造函数缺少必填参数
            token_store=token_store,  # 新增代码+OAuth超时重试: 注入内存 token store；若省略: 测试可能读写真凭证
            post_json=fake_post_json,  # 新增代码+OAuth超时重试: 注入假 HTTP；若省略: 测试会联网
            login_callback=fake_login,  # 新增代码+OAuth超时重试: 注入假登录以观察是否误登录；若省略: 测试无法保护边界
        )  # 新增代码+OAuth超时重试: 模型创建结束；若省略: Python 调用语法不完整
        message = model.chat(messages=[{"role": "user", "content": "你好"}], tools=[])  # 新增代码+OAuth超时重试: 发起一次 chat 触发“第一次超时、第二次成功”；若省略: 被测逻辑不会运行

        self.assertEqual(message.text, "超时重试后回答")  # 新增代码+OAuth超时重试: 断言一次 timeout 后能恢复最终回答；若省略: 只能知道重试次数不知道用户结果
        self.assertEqual(calls, [CodexOAuthChatModel.CODEX_API_ENDPOINT, CodexOAuthChatModel.CODEX_API_ENDPOINT])  # 新增代码+OAuth超时重试: 断言只对模型 API 重试一次；若省略: 可能出现无限重试或没有重试
        self.assertEqual(login_calls, [])  # 新增代码+OAuth超时重试: 断言 timeout 不会打开网页登录；若省略: 网络抖动可能被误判成登录过期
    def test_codex_oauth_model_retries_once_when_api_remote_closes_connection(self) -> None:  # 新增代码+OAuth远端断连: 复现截图里的 Remote end closed connection without response 并要求自动重试一次；若省略: 远端临时断连会直接失败
        calls: list[str] = []  # 新增代码+OAuth远端断连: 记录 Codex API 调用次数；若省略: 无法确认是否只重试一次
        login_calls: list[str] = []  # 新增代码+OAuth远端断连: 记录是否误触发网页登录；若省略: 无法保护网络断连不等于登录过期的边界

        def fake_post_json(url: str, headers: dict[str, str], body: dict[str, object]) -> dict[str, object]:  # 新增代码+OAuth远端断连: 用假 HTTP 第一次断连第二次成功；若省略: 测试会依赖真实网络偶发断开
            del headers, body  # 新增代码+OAuth远端断连: 本测试不需要请求头和请求体细节；若省略: 未用参数会干扰阅读
            calls.append(url)  # 新增代码+OAuth远端断连: 保存本次请求目标；若省略: 后续无法断言重试次数
            if url == CodexOAuthChatModel.CODEX_API_ENDPOINT and calls.count(CodexOAuthChatModel.CODEX_API_ENDPOINT) == 1:  # 新增代码+OAuth远端断连: 只让第一次模型请求断连；若省略: 无法模拟一次性远端连接关闭
                raise http.client.RemoteDisconnected("Remote end closed connection without response")  # 新增代码+OAuth远端断连: 模拟 urllib 在服务端提前断开时抛出的真实异常；若省略: 红灯无法覆盖用户截图错误
            return {"output_text": '{"text":"远端断连重试后回答","tool_calls":[]}'}  # 新增代码+OAuth远端断连: 第二次请求返回正常模型输出；若省略: 无法证明重试可以恢复

        def fake_login() -> CodexOAuthTokens:  # 新增代码+OAuth远端断连: 如果断连被误判为登录过期就记录；若省略: 无法断言不会打开网页登录
            login_calls.append("login")  # 新增代码+OAuth远端断连: 标记登录被调用；若省略: 误登录不会被测试发现
            return CodexOAuthTokens(access_token="fresh-access", refresh_token="fresh-refresh", expires_at=9999999999999)  # 新增代码+OAuth远端断连: 返回合法 token 满足函数签名；若省略: 假登录不完整

        token_store = FakeOAuthTokenStore(  # 新增代码+OAuth远端断连: 准备本地有效 token，确保只测试 API 请求断连；若省略: 可能先进入登录或刷新分支
            CodexOAuthTokens(  # 新增代码+OAuth远端断连: 创建有效 token 数据对象；若省略: 模型没有测试凭证
                access_token="valid-access",  # 新增代码+OAuth远端断连: 模拟有效 access token；若省略: 请求头缺少鉴权上下文
                refresh_token="valid-refresh",  # 新增代码+OAuth远端断连: 模拟有效 refresh token；若省略: `_get_valid_tokens` 会走登录分支
                expires_at=9999999999999,  # 新增代码+OAuth远端断连: 设置本地 token 不过期；若省略: 测试路径会被 refresh 逻辑干扰
                account_id=None,  # 新增代码+OAuth远端断连: 本测试不需要账号头；若省略: token 构造语义不完整
            )  # 新增代码+OAuth远端断连: token 数据对象结束；若省略: Python 调用无法闭合
        )  # 新增代码+OAuth远端断连: token store 创建结束；若省略: 模型无法加载测试 token
        model = CodexOAuthChatModel(  # 新增代码+OAuth远端断连: 创建 OAuth 模型；若省略: 无法执行 chat 行为
            model="gpt-5.5",  # 新增代码+OAuth远端断连: 指定模型名；若省略: 构造函数缺少必填参数
            token_store=token_store,  # 新增代码+OAuth远端断连: 注入内存 token store；若省略: 测试可能读写真凭证
            post_json=fake_post_json,  # 新增代码+OAuth远端断连: 注入假 HTTP；若省略: 测试会联网
            login_callback=fake_login,  # 新增代码+OAuth远端断连: 注入假登录以观察误登录；若省略: 测试无法保护边界
        )  # 新增代码+OAuth远端断连: 模型创建结束；若省略: Python 调用语法不完整
        message = model.chat(messages=[{"role": "user", "content": "查天气"}], tools=[])  # 新增代码+OAuth远端断连: 发起 chat 触发第一次断连第二次成功；若省略: 被测逻辑不会运行

        self.assertEqual(message.text, "远端断连重试后回答")  # 新增代码+OAuth远端断连: 断言一次远端断连后能恢复最终回答；若省略: 只能验证重试次数不能验证用户结果
        self.assertEqual(calls, [CodexOAuthChatModel.CODEX_API_ENDPOINT, CodexOAuthChatModel.CODEX_API_ENDPOINT])  # 新增代码+OAuth远端断连: 断言只重试一次模型 API；若省略: 可能出现无限重试或没有重试
        self.assertEqual(login_calls, [])  # 新增代码+OAuth远端断连: 断言远端断连不会打开网页登录；若省略: 网络抖动可能被误判成登录过期
    def test_codex_oauth_remote_close_message_does_not_force_relogin(self) -> None:  # 新增代码+OAuth远端断连提示: 验证远端断连连续失败时给中文说明且不网页登录；若省略: 用户会继续只看到英文底层错误
        login_calls: list[str] = []  # 新增代码+OAuth远端断连提示: 记录是否误触发登录；若省略: 无法保护断连不等于登录过期

        def fake_post_json(url: str, headers: dict[str, str], body: dict[str, object]) -> dict[str, object]:  # 新增代码+OAuth远端断连提示: 用假 HTTP 始终模拟远端提前断开；若省略: 测试无法稳定复现截图错误
            del url, headers, body  # 新增代码+OAuth远端断连提示: 本测试不使用请求细节；若省略: 读者会误以为参数影响断连判断
            raise http.client.RemoteDisconnected("Remote end closed connection without response")  # 新增代码+OAuth远端断连提示: 模拟服务端没有响应就关闭连接；若省略: 无法覆盖截图原文

        def fake_login() -> CodexOAuthTokens:  # 新增代码+OAuth远端断连提示: 如果断连误触发登录就记录；若省略: 测试无法发现错误网页登录
            login_calls.append("login")  # 新增代码+OAuth远端断连提示: 标记登录被调用；若省略: 误登录不会被断言
            return CodexOAuthTokens(access_token="fresh-access", refresh_token="fresh-refresh", expires_at=9999999999999)  # 新增代码+OAuth远端断连提示: 返回合法 token 满足函数签名；若省略: 假登录不完整

        token_store = FakeOAuthTokenStore(  # 新增代码+OAuth远端断连提示: 准备未过期 token 避免进入 refresh/login 分支；若省略: 测试路径会不纯
            CodexOAuthTokens(  # 新增代码+OAuth远端断连提示: 创建有效 token 数据对象；若省略: 模型会先登录而不是请求 API
                access_token="valid-access",  # 新增代码+OAuth远端断连提示: 模拟有效 access token；若省略: 缺少鉴权上下文
                refresh_token="valid-refresh",  # 新增代码+OAuth远端断连提示: 模拟有效 refresh token；若省略: `_get_valid_tokens` 会触发登录
                expires_at=9999999999999,  # 新增代码+OAuth远端断连提示: 设置不过期；若省略: 会进入刷新分支
                account_id=None,  # 新增代码+OAuth远端断连提示: 本测试不需要账号头；若省略: token 数据语义不完整
            )  # 新增代码+OAuth远端断连提示: token 数据对象结束；若省略: Python 调用无法闭合
        )  # 新增代码+OAuth远端断连提示: token store 创建结束；若省略: 模型没有测试凭证
        model = CodexOAuthChatModel(  # 新增代码+OAuth远端断连提示: 创建 OAuth 模型；若省略: 无法执行错误格式化路径
            model="gpt-5.5",  # 新增代码+OAuth远端断连提示: 指定模型名；若省略: 构造函数缺参
            token_store=token_store,  # 新增代码+OAuth远端断连提示: 注入内存 token store；若省略: 测试会污染真实 token
            post_json=fake_post_json,  # 新增代码+OAuth远端断连提示: 注入始终断连的 fake HTTP；若省略: 测试依赖真实网络
            login_callback=fake_login,  # 新增代码+OAuth远端断连提示: 注入假登录以检测误登录；若省略: 无法保护边界
        )  # 新增代码+OAuth远端断连提示: 模型创建结束；若省略: Python 调用语法不完整
        message = model.chat(messages=[{"role": "user", "content": "查天气"}], tools=[])  # 新增代码+OAuth远端断连提示: 发起 chat 触发连续远端断连；若省略: 待验证错误文案不会生成

        self.assertEqual(login_calls, [])  # 新增代码+OAuth远端断连提示: 验证远端断连不会打开网页登录；若省略: 程序可能误把网络断开当登录过期
        self.assertIn("远端连接关闭", message.text)  # 新增代码+OAuth远端断连提示: 验证中文解释包含核心错误类型；若省略: 用户仍只能看到英文 Remote end closed
        self.assertIn("不一定是 OAuth 登录过期", message.text)  # 新增代码+OAuth远端断连提示: 验证提示明确区分网络断开和登录过期；若省略: 用户会继续期待弹出登录网页
    def test_codex_oauth_stream_parser_collects_output_text_delta(self) -> None:  # 新增代码: 测试 OAuth HTTP 层能从 Codex SSE 流里拼出最终文本
        raw_stream = (  # 新增代码: 构造一个最小 SSE 响应，模拟 Responses 流式 output_text delta
            'data: {"type":"response.output_text.delta","delta":"{\\"text\\":\\"你"}\n\n'  # 新增代码: 第一段 delta，包含 JSON 文本开头
            'data: {"type":"response.output_text.delta","delta":"好\\",\\"tool_calls\\":[]}"}\n\n'  # 新增代码: 第二段 delta，包含 JSON 文本结尾
            "data: [DONE]\n\n"  # 新增代码: SSE 结束标记
        )  # 新增代码: SSE 字符串结束
        parsed = CodexOAuthChatModel._parse_sse_response(raw_stream)  # 新增代码: 调用 SSE 解析器
        self.assertEqual(parsed["output_text"], '{"text":"你好","tool_calls":[]}')  # 新增代码: 验证 delta 被按顺序拼成完整 output_text
    def test_codex_oauth_stream_request_reads_until_done_without_full_response_read(self) -> None:  # 新增代码+OAuth流读取: 验证流式请求不能整包 read；若省略: 长连接 SSE 不关闭时 agent 会像截图一样卡住
        class FakeStreamingResponse:  # 新增代码+OAuth流读取: 构造假的 HTTP 流响应；若省略: 测试无法模拟 SSE 长连接读取方式
            def __init__(self) -> None:  # 新增代码+OAuth流读取: 初始化假响应状态；若省略: 无法记录 read 是否被误用
                self.read_called = False  # 新增代码+OAuth流读取: 记录是否调用了整包 read；若省略: 测试无法发现阻塞风险
                self.lines = [  # 新增代码+OAuth流读取: 准备按行返回的 SSE 数据；若省略: readline 没有可读内容
                    'data: {"type":"response.output_text.done","text":"{\\"text\\":\\"天气结果\\",\\"tool_calls\\":[]}"}\n'.encode("utf-8"),  # 修改代码+OAuth流读取: 用 UTF-8 编码中文 SSE 行；若省略: bytes 字面量包含中文会导致测试语法错误
                    b"\n",  # 新增代码+OAuth流读取: 第二行提供 SSE 空行分隔符；若省略: SSE 事件边界不完整
                    b"data: [DONE]\n",  # 新增代码+OAuth流读取: 第三行模拟后端结束标记；若省略: 只靠 done 事件也应返回但覆盖不完整
                    b"\n",  # 新增代码+OAuth流读取: 第四行结束 [DONE] 事件；若省略: SSE 文本格式不完整
                    b"",  # 新增代码+OAuth流读取: 最后一项模拟 EOF；若省略: readline 测试替身没有自然结束
                ]  # 新增代码+OAuth流读取: SSE 行列表结束；若省略: Python 列表语法不完整

            def __enter__(self) -> "FakeStreamingResponse":  # 新增代码+OAuth流读取: 支持 with urlopen(...) as response；若省略: `_post_json_request` 无法使用假响应
                return self  # 新增代码+OAuth流读取: 返回自身作为响应对象；若省略: with 块拿不到响应

            def __exit__(self, exc_type: object, exc: object, tb: object) -> None:  # 新增代码+OAuth流读取: 支持退出上下文；若省略: with 块结束时会报协议错误
                return None  # 新增代码+OAuth流读取: 不吞掉异常；若省略: Python 默认也返回 None，但这里让测试语义清楚

            def read(self) -> bytes:  # 新增代码+OAuth流读取: 模拟旧实现会调用的整包读取；若省略: 旧实现会因假响应缺方法而不是因行为错误失败
                self.read_called = True  # 新增代码+OAuth流读取: 标记整包 read 被调用；若省略: 断言无法识别旧阻塞路径
                return 'data: {"type":"response.output_text.done","text":"{\\"text\\":\\"天气结果\\",\\"tool_calls\\":[]}"}\n\n'.encode("utf-8")  # 修改代码+OAuth流读取: 用 UTF-8 编码中文完整响应；若省略: bytes 字面量包含中文会导致测试语法错误

            def readline(self) -> bytes:  # 新增代码+OAuth流读取: 模拟 HTTPResponse 的逐行读取；若省略: 新实现无法按 SSE 行读取
                if not self.lines:  # 新增代码+OAuth流读取: 如果行已经读完；若省略: pop 空列表会抛出无关错误
                    return b""  # 新增代码+OAuth流读取: 返回 EOF；若省略: 新实现无法自然结束读取
                return self.lines.pop(0)  # 新增代码+OAuth流读取: 返回下一行 SSE 字节；若省略: 测试无法推进读取循环

        fake_response = FakeStreamingResponse()  # 新增代码+OAuth流读取: 创建假响应实例；若省略: mock urlopen 没有返回对象
        model = CodexOAuthChatModel(model="gpt-5.5", token_store=FakeOAuthTokenStore(None))  # 新增代码+OAuth流读取: 创建待测模型但不触发真实登录；若省略: 无法调用实例方法
        with mock.patch("urllib.request.urlopen", return_value=fake_response):  # 新增代码+OAuth流读取: 拦截真实网络请求；若省略: 测试会访问真实 Codex API
            parsed = model._post_json_request(  # 新增代码+OAuth流读取: 直接调用 HTTP 层复现流式读取行为；若省略: 测试路径会被 chat 的 token 逻辑干扰
                "https://chatgpt.com/backend-api/codex/responses",  # 新增代码+OAuth流读取: 使用 responses 端点形状；若省略: request 构造缺少 URL
                {"Content-Type": "application/json"},  # 新增代码+OAuth流读取: 提供最小请求头；若省略: Request 构造仍可运行但测试语义不清楚
                {"stream": True},  # 新增代码+OAuth流读取: 显式进入 SSE 流式分支；若省略: `_post_json_request` 会按普通 JSON 读取
            )  # 新增代码+OAuth流读取: `_post_json_request` 调用结束；若省略: Python 调用语法不完整

        self.assertFalse(fake_response.read_called)  # 新增代码+OAuth流读取: 验证没有整包读取；若省略: 无法防止长连接再次卡住
        self.assertEqual(parsed["output_text"], '{"text":"天气结果","tool_calls":[]}')  # 新增代码+OAuth流读取: 验证逐行读取仍能得到模型结构化文本；若省略: 只测不卡住不测结果正确

    def test_codex_oauth_stream_reader_has_total_deadline_for_heartbeat_only_streams(self) -> None:  # 新增代码+OAuthSseDeadline: 函数段开始，验证 SSE 流只有心跳或未知事件时也会按总时长退出；如果没有这个测试，真实终端会继续卡在模型第 0 轮。
        class FakeHeartbeatResponse:  # 新增代码+OAuthSseDeadline: 构造只返回心跳行的假响应；如果没有这个类，测试无法稳定复现后端不断发非完成事件的长连接。
            def __init__(self) -> None:  # 新增代码+OAuthSseDeadline: 初始化假响应计数器；如果没有这段函数，测试无法证明读取循环确实持续了一段时间。
                self.readline_count = 0  # 新增代码+OAuthSseDeadline: 记录 readline 被调用次数；如果没有这行代码，断言无法确认循环不是立即退出。

            def readline(self) -> bytes:  # 新增代码+OAuthSseDeadline: 模拟 HTTPResponse.readline；如果没有这段函数，被测 SSE 读取器无法运行。
                self.readline_count += 1  # 新增代码+OAuthSseDeadline: 每读取一次就增加计数；如果没有这行代码，无法观察 deadline 前循环推进。
                return b": keep-alive\n"  # 新增代码+OAuthSseDeadline: 返回 SSE 心跳行但永远不给 done；如果没有这行代码，测试不会覆盖真实卡住条件。

        class FakeClock:  # 新增代码+OAuthSseDeadline: 构造可控假时钟；如果没有这个类，测试需要真实等待超时，速度慢且不稳定。
            def __init__(self) -> None:  # 新增代码+OAuthSseDeadline: 初始化当前时间；如果没有这段函数，假时钟没有起点。
                self.now = 1000.0  # 新增代码+OAuthSseDeadline: 设置起始秒数；如果没有这行代码，time 函数没有返回值。

            def time(self) -> float:  # 新增代码+OAuthSseDeadline: 提供和 time.monotonic 类似的接口；如果没有这段函数，被测函数无法注入时间来源。
                self.now += 0.6  # 新增代码+OAuthSseDeadline: 每次读取时间都推进 0.6 秒；如果没有这行代码，deadline 永远不会到达。
                return self.now  # 新增代码+OAuthSseDeadline: 返回推进后的时间；如果没有这行代码，调用方拿不到当前时间。

        fake_response = FakeHeartbeatResponse()  # 新增代码+OAuthSseDeadline: 创建心跳响应；如果没有这行代码，测试没有被测输入。
        fake_clock = FakeClock()  # 新增代码+OAuthSseDeadline: 创建可控时钟；如果没有这行代码，测试不能快速触发总截止。
        model = CodexOAuthChatModel(model="gpt-5.5", token_store=FakeOAuthTokenStore(None), sse_read_timeout_seconds=1, monotonic=fake_clock.time)  # 新增代码+OAuthSseDeadline: 用 1 秒 deadline 创建模型；如果没有这行代码，测试会使用生产默认值而无法快速验证。

        with self.assertRaisesRegex(TimeoutError, "SSE"):  # 新增代码+OAuthSseDeadline: 断言心跳流会抛出可识别的 SSE 超时；如果没有这行代码，读取器静默返回空文本也会误判通过。
            model._read_sse_response_until_done(fake_response)  # 新增代码+OAuthSseDeadline: 调用生产 SSE 读取器；如果没有这行代码，测试没有执行真实逻辑。
        self.assertGreater(fake_response.readline_count, 0)  # 新增代码+OAuthSseDeadline: 确认读取器确实尝试读取过流；如果没有这行代码，deadline 可能在读前误触发。
    # 新增代码+OAuthSseDeadline: 函数段结束，test_codex_oauth_stream_reader_has_total_deadline_for_heartbeat_only_streams 到此结束；如果没有这个边界说明，用户不容易看出 SSE 总截止验收范围。


if __name__ == "__main__":  # Stage14: allow running this test module directly.
    unittest.main()  # Stage14: start unittest when executed as a script.


