"Prompt, context, skill, docs, and token-budget tests."  # Stage14: this file owns the prompts_context test group.
from __future__ import annotations  # Stage14: keep annotations lazy after test split.
import unittest  # Stage14: keep direct unittest execution available.
from learning_agent.tests.support import *  # Stage14: import shared helpers and dependencies for copied tests.

class PromptsContextTests(LearningAgentTestBase):  # Stage14: unittest discovers this concrete modular test class.
    def test_prompt_registry_declares_default_blocks_with_metadata(self) -> None:  # 新增代码+PromptArchitectureV1: 验证默认提示词注册表声明核心 block 和元数据；若没有这行代码，默认提示词元数据缺失不会被测试发现
        registry = build_default_prompt_registry()  # 新增代码+PromptArchitectureV1: 构建默认 Prompt Registry 作为真实测试对象；若没有这行代码，后续无法检查默认 block 是否存在
        by_id = {block.block_id: block for block in registry.blocks}  # 新增代码+PromptArchitectureV1: 按 block_id 建索引方便精确断言；若没有这行代码，测试只能用列表位置导致含义不清
        self.assertIn("prompt.kernel.identity", by_id)  # 新增代码+PromptArchitectureV1: 确认身份内核提示词存在；若没有这行代码，关键身份提示缺失也可能漏测
        self.assertIn("prompt.policy.tool_boundary", by_id)  # 新增代码+PromptArchitectureV1: 确认工具边界策略提示词存在；若没有这行代码，工具边界提示缺失也可能漏测
        self.assertEqual(by_id["prompt.kernel.identity"].load_policy, "always")  # 新增代码+PromptArchitectureV1: 确认身份内核每次都加载；若没有这行代码，核心身份提示可能被错误延迟加载
        self.assertGreater(by_id["prompt.kernel.identity"].priority, by_id["prompt.policy.response"].priority)  # 新增代码+PromptArchitectureV1: 确认身份内核优先级高于回复策略；若没有这行代码，排序权重错误不容易被发现
        self.assertLessEqual(by_id["prompt.kernel.identity"].max_tokens, 1200)  # 新增代码+PromptArchitectureV1: 确认身份内核 token 上限不超过规格；若没有这行代码，默认块可能悄悄撑大上下文预算
        decision = PromptLoadDecision(block_id="prompt.kernel.identity", should_load=True, status="loaded", reason="always")  # 新增代码+PromptArchitectureV1: 构造加载决策对象确认注册表模块暴露计划要求的决策结构；若没有这行代码，PromptLoadDecision 缺失不会被测试发现
        self.assertTrue(decision.should_load)  # 新增代码+PromptArchitectureV1: 断言加载决策能表达 should_load；若没有这行代码，决策字段退化不会失败
    def test_prompt_registry_rejects_duplicate_block_ids(self) -> None:  # 新增代码+PromptArchitectureV1: 验证重复 block_id 会被拒绝；若没有这行代码，重复提示词块可能覆盖或重复进入上下文
        block = PromptBlock(block_id="same", title="A", source="test", priority=1, load_policy="always", max_tokens=100)  # 新增代码+PromptArchitectureV1: 构造两个引用同一 block_id 的测试块；若没有这行代码，重复检测没有输入样本
        with self.assertRaises(ValueError):  # 新增代码+PromptArchitectureV1: 期待注册表初始化主动报错；若没有这行代码，重复 block_id 被接受时测试不会失败
            PromptRegistry([block, block])  # 新增代码+PromptArchitectureV1: 用重复 block_id 创建注册表触发校验；若没有这行代码，重复拒绝逻辑不会被执行
    def test_context_assembler_orders_blocks_by_registry_priority(self) -> None:  # 新增代码+PromptArchitectureV1: 验证 ContextAssembler 按注册表优先级装配提示词块；若没有这行代码，Task 2 排序退化不会被测试发现
        registry = build_default_prompt_registry()  # 新增代码+PromptArchitectureV1: 构建真实默认注册表作为排序依据；若没有这行代码，装配器测试没有权威优先级来源
        assembler = ContextAssembler(registry)  # 新增代码+PromptArchitectureV1: 创建被测上下文装配器；若没有这行代码，测试无法调用 assemble_static_blocks
        result = assembler.assemble_static_blocks({  # 新增代码+PromptArchitectureV1: 传入故意乱序的 block 内容；若没有这行代码，无法证明装配器会重新按 registry 排序
            "prompt.policy.response": "Response Policy / 输出策略：",  # 新增代码+PromptArchitectureV1: 把低优先级输出策略先放入输入；若没有这行代码，测试无法覆盖“输入顺序不等于输出顺序”
            "prompt.kernel.identity": "Core Identity / 核心身份：",  # 新增代码+PromptArchitectureV1: 把高优先级身份内核后放入输入；若没有这行代码，测试无法断言身份内核提前
        })  # 新增代码+PromptArchitectureV1: 结束 block 内容字典；若没有这行代码，Python 语法不完整
        self.assertLess(result.system_prompt.index("Core Identity"), result.system_prompt.index("Response Policy"))  # 新增代码+PromptArchitectureV1: 断言系统提示词中身份内核早于输出策略；若没有这行代码，排序错误不会被发现
        self.assertEqual(result.loaded_blocks[0].block_id, "prompt.kernel.identity")  # 新增代码+PromptArchitectureV1: 断言加载记录第一项也是身份内核；若没有这行代码，报告顺序错误不会被发现
    def test_build_initial_messages_records_prompt_surface_report(self) -> None:  # 新增代码+PromptArchitectureV1: 验证 LearningAgent 构造初始消息时记录 prompt surface report；若没有这行代码，用户无法检查本轮加载了哪些提示词块
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PromptArchitectureV1: 创建临时工作区避免污染真实项目文件；若没有这行代码，测试可能读写用户真实 memory.md
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="ok")]), workspace=Path(raw_dir), ask_permission=lambda action: True)  # 新增代码+PromptArchitectureV1: 创建带假模型的 agent 以调用真实提示词构造逻辑；若没有这行代码，无法验证 last_prompt_surface_report
            messages = agent._build_initial_messages("你好")  # 新增代码+PromptArchitectureV1: 生成初始 messages 触发 ContextAssembler 装配；若没有这行代码，报告不会被刷新
            self.assertIn("Prompt Surface Architecture v2", messages[0]["content"])  # 新增代码+PromptArchitectureV1: 断言原有关键 system prompt 文案仍保留；若没有这行代码，装配改造可能误删用户可见关键提示词
            self.assertTrue(agent.last_prompt_surface_report.loaded_blocks)  # 新增代码+PromptArchitectureV1: 断言本轮 prompt surface report 记录了加载块；若没有这行代码，报告为空也不会被发现
    def test_static_prompt_file_is_loaded_into_system_prompt(self) -> None:  # 新增代码+PromptFiles: 验证系统提示词从 staticprompt.md 文件读取；若没有这行代码，提示词可能继续硬编码在 learning_agent.py 里
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PromptFiles: 创建临时工作区隔离用户真实提示词文件；若没有这行代码，测试可能污染当前项目
            workspace = Path(raw_dir)  # 新增代码+PromptFiles: 把临时目录转成 Path；若没有这行代码，后续创建 staticprompt 目录不方便
            static_prompt_dir = workspace / "staticprompt"  # 新增代码+PromptFiles: 定位工作区覆盖用静态提示词目录；若没有这行代码，无法验证用户可自定义 staticprompt.md
            static_prompt_dir.mkdir()  # 新增代码+PromptFiles: 创建 staticprompt 目录；若没有这行代码，写入 staticprompt.md 会失败
            (static_prompt_dir / "staticprompt.md").write_text("自定义静态提示词标记\n当前工作区：\n{{CURRENT_WORKSPACE}}\n", encoding="utf-8")  # 新增代码+PromptFiles: 写入带占位符的测试提示词；若没有这行代码，无法证明文件内容和工作区替换都生效
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="ok")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+PromptFiles: 创建 agent 触发静态提示词路径解析；若没有这行代码，无法检查真实加载路径
            messages = agent._build_initial_messages("你好")  # 新增代码+PromptFiles: 构造 system prompt；若没有这行代码，静态提示词不会被读取
            system_content = str(messages[0]["content"])  # 新增代码+PromptFiles: 取出系统提示词文本；若没有这行代码，后续断言没有对象
            self.assertEqual(agent.static_prompt_path, static_prompt_dir / "staticprompt.md")  # 新增代码+PromptFiles: 断言工作区 staticprompt 优先；若没有这行代码，用户自定义提示词可能被包内默认覆盖
            self.assertIn("自定义静态提示词标记", system_content)  # 新增代码+PromptFiles: 断言文件正文进入系统提示词；若没有这行代码，提示词文件可能只是存在但未加载
            self.assertIn(str(workspace), system_content)  # 新增代码+PromptFiles: 断言工作区占位符被替换；若没有这行代码，模型可能看见未展开模板
    def test_static_prompt_renders_current_date_each_turn(self) -> None:  # 新增代码+CurrentDatePrompt: 验证每轮 system prompt 都能看到当天真实日期；若没有这行代码，日期占位符回归时测试不会发现
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CurrentDatePrompt: 创建临时工作区隔离真实项目提示词；若没有这行代码，测试可能污染用户正在开发的 staticprompt.md
            workspace = Path(raw_dir)  # 新增代码+CurrentDatePrompt: 把临时目录转成 Path 对象；若没有这行代码，后续路径拼接会更容易写错
            static_prompt_dir = workspace / "staticprompt"  # 新增代码+CurrentDatePrompt: 定位工作区自定义静态提示词目录；若没有这行代码，测试无法覆盖用户可编辑提示词路径
            static_prompt_dir.mkdir()  # 新增代码+CurrentDatePrompt: 创建 staticprompt 目录；若没有这行代码，写入 staticprompt.md 会因为父目录不存在而失败
            (static_prompt_dir / "staticprompt.md").write_text("当前日期：\n{{CURRENT_DATE}}\n", encoding="utf-8")  # 新增代码+CurrentDatePrompt: 写入日期占位符；若没有这行代码，测试无法证明运行时会把日期渲染进系统提示词
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="ok")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+CurrentDatePrompt: 创建真实 agent 以走生产提示词构造路径；若没有这行代码，测试只是在检查文件文本而不是 agent 行为
            first_messages = agent._build_initial_messages("今天日期是什么？")  # 新增代码+CurrentDatePrompt: 构造第一轮消息；若没有这行代码，无法确认首轮 system prompt 包含当天日期
            second_messages = agent._build_initial_messages("再确认一次今天日期。")  # 新增代码+CurrentDatePrompt: 构造第二轮消息；若没有这行代码，无法确认每轮都会重新经过日期渲染路径
            expected_date = date.today().isoformat()  # 新增代码+CurrentDatePrompt: 计算测试当天的本地 YYYY-MM-DD 日期；若没有这行代码，断言会把日期写死导致第二天失败
            self.assertIn(f"当前日期：\n{expected_date}", str(first_messages[0]["content"]))  # 新增代码+CurrentDatePrompt: 断言第一轮看得到真实日期；若没有这行代码，首轮缺日期也不会被发现
            self.assertIn(f"当前日期：\n{expected_date}", str(second_messages[0]["content"]))  # 新增代码+CurrentDatePrompt: 断言第二轮也看得到真实日期；若没有这行代码，只能证明初始化时有日期，不能证明每轮都有
            self.assertNotIn("{{CURRENT_DATE}}", str(second_messages[0]["content"]))  # 新增代码+CurrentDatePrompt: 断言占位符不会泄漏给模型；若没有这行代码，模型可能看到模板而不知道今天是哪一天
    def test_package_static_and_dynamic_prompt_files_exist(self) -> None:  # 新增代码+PromptFiles: 验证默认静态/动态提示词文件都在新目录；若没有这行代码，后续打包可能漏掉提示词资产
        self.assertTrue(self._static_prompt_file().exists())  # 新增代码+PromptFiles: 断言包内 staticprompt.md 存在；若没有这行代码，默认 agent 可能只能靠 Python fallback 启动
        self.assertTrue(self._dynamic_prompt_file().exists())  # 新增代码+PromptFiles: 断言包内 dynamicprompt.md 存在；若没有这行代码，动态规则按需加载没有默认文件
        self.assertFalse((TEST_ROOT / "runtime_instructions.md").exists())  # 新增代码+PromptFiles: 断言旧 runtime_instructions.md 已迁移；若没有这行代码，用户会面对两个动态规则入口而混淆
    def test_agent_memory_files_are_not_loaded_into_system_prompt(self) -> None:  # 修改代码+AgentMemoryBoundary: 验证 Codex 开发用 agent_memory 不再进入目标 agent 每轮提示词；若没有这行代码，旧关联可能再次污染用户 agent
        with tempfile.TemporaryDirectory() as raw_dir:  # 修改代码+AgentMemoryBoundary: 创建临时项目目录隔离真实仓库记忆；若没有这行代码，测试会依赖当前 Codex 会话的 agent_memory
            root = Path(raw_dir)  # 修改代码+AgentMemoryBoundary: 把临时目录转成 Path 方便拼接文件路径；若没有这行代码，后续创建测试目录不稳定
            memory_dir = root / "agent_memory"  # 修改代码+AgentMemoryBoundary: 构造一个本不该被目标 agent 读取的 agent_memory 目录；若没有这行代码，测试无法证明即使存在也不加载
            memory_dir.mkdir()  # 修改代码+AgentMemoryBoundary: 创建 agent_memory 目录；若没有这行代码，下面写入三个测试文件会失败
            (memory_dir / "context.md").write_text("不应进入模型的 Codex 开发上下文", encoding="utf-8")  # 修改代码+AgentMemoryBoundary: 写入可断言的 context 标记；若没有这行代码，误加载 context.md 时测试抓不到
            (memory_dir / "progress.md").write_text("不应进入模型的 Codex 开发进度", encoding="utf-8")  # 修改代码+AgentMemoryBoundary: 写入可断言的 progress 标记；若没有这行代码，误加载 progress.md 时测试抓不到
            (memory_dir / "bugs.md").write_text("不应进入模型的 Codex 开发风险", encoding="utf-8")  # 修改代码+AgentMemoryBoundary: 写入可断言的 bugs 标记；若没有这行代码，误加载 bugs.md 时测试抓不到
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="ok")]), workspace=root, ask_permission=lambda action: True)  # 修改代码+AgentMemoryBoundary: 创建真实 LearningAgent；若没有这行代码，测试覆盖不到生产提示词构造入口
            messages = agent._build_initial_messages("继续")  # 修改代码+AgentMemoryBoundary: 构造初始 messages；若没有这行代码，system prompt 不会生成
            system_content = str(messages[0]["content"])  # 修改代码+AgentMemoryBoundary: 取出 system prompt 文本；若没有这行代码，后续断言没有对象
            loaded_ids = {block.block_id for block in agent.last_prompt_surface_report.loaded_blocks}  # 修改代码+AgentMemoryBoundary: 收集真实加载的 prompt block id；若没有这行代码，无法证明 project memory block 已移除
            self.assertNotIn("Project Memory Index", system_content)  # 修改代码+AgentMemoryBoundary: 断言项目记忆索引标题不再进入提示词；若没有这行代码，旧 agent_memory block 可能悄悄回归
            self.assertNotIn("不应进入模型的 Codex 开发上下文", system_content)  # 修改代码+AgentMemoryBoundary: 断言 context.md 内容不进入提示词；若没有这行代码，Codex 开发上下文可能污染用户 agent
            self.assertNotIn("不应进入模型的 Codex 开发进度", system_content)  # 修改代码+AgentMemoryBoundary: 断言 progress.md 内容不进入提示词；若没有这行代码，Codex 当前任务状态可能污染用户 agent
            self.assertNotIn("不应进入模型的 Codex 开发风险", system_content)  # 修改代码+AgentMemoryBoundary: 断言 bugs.md 内容不进入提示词；若没有这行代码，Codex 风险记录可能污染用户 agent
            self.assertNotIn("context.project_memory_index", loaded_ids)  # 修改代码+AgentMemoryBoundary: 断言报告里也没有项目记忆 block；若没有这行代码，报告可能仍显示旧关联
    def test_long_memory_does_not_enter_system_prompt_as_full_text(self) -> None:  # 新增代码+PromptArchitectureV1: 验证超长 memory.md 不再全文重复进入 system prompt；若没有这行代码，长记忆膨胀问题会回归
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PromptArchitectureV1: 创建临时工作区避免写真实 memory.md；若没有这行代码，测试可能破坏用户长期记忆
            workspace = Path(raw_dir)  # 新增代码+PromptArchitectureV1: 把临时目录转成 Path 供 LearningAgent 使用；若没有这行代码，路径拼接和文件写入不够稳定
            (workspace / "memory.md").write_text("开头\n" + ("超长记忆\n" * 3000) + "结尾\n", encoding="utf-8")  # 新增代码+PromptArchitectureV1: 写入超长长期记忆模拟真实膨胀场景；若没有这行代码，测试无法证明全文注入已被替换
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="ok")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+PromptArchitectureV1: 创建 agent 并保留已有 memory.md；若没有这行代码，无法验证长期记忆读取逻辑
            messages = agent._build_initial_messages("继续")  # 新增代码+PromptArchitectureV1: 构造初始消息触发长期记忆索引装配；若没有这行代码，system prompt 内容不会生成
            self.assertIn("Long-Term Memory Index", messages[0]["content"])  # 新增代码+PromptArchitectureV1: 断言长期记忆使用索引标题；若没有这行代码，旧的全文记忆标题可能继续存在
            self.assertNotIn("超长记忆\n超长记忆\n超长记忆\n超长记忆\n超长记忆", messages[0]["content"])  # 新增代码+PromptArchitectureV1: 断言连续重复正文没有整段进入提示词；若没有这行代码，长记忆全文注入不会被拦住
    def test_context_assembler_creates_compact_summary_when_budget_is_high(self) -> None:  # 修改代码+PromptArchitectureV1: 验证超过软 token 预算时动态上下文会生成 Compact Summary；若没有这行代码，压缩逻辑缺失也不会被发现
        registry = build_default_prompt_registry()  # 修改代码+PromptArchitectureV1: 构建默认提示词注册表作为装配器输入；若没有这行代码，测试没有真实 block 优先级来源
        assembler = ContextAssembler(registry, soft_token_limit=200)  # 修改代码+PromptArchitectureV1: 用很低软预算强制触发动态 block compact；若没有这行代码，测试可能因为默认预算太大而无法覆盖压缩路径
        result = assembler.assemble_static_blocks({  # 修改代码+PromptArchitectureV1: 传入超长动态 block 模拟上下文预算过高；若没有这行代码，装配器没有需要压缩的动态内容
            "context.dynamic_prompt_index": "运行规则\n" * 800,  # 修改代码+PromptFiles: 构造按需动态提示词索引的超长内容；若没有这行代码，测试会误用核心内置策略覆盖动态压缩边界
            "context.long_term_memory_index": "长期记忆索引\n" * 800,  # 修改代码+PromptArchitectureV1: 构造低优先级长期记忆索引；若没有这行代码，无法验证低优先级动态索引优先压缩
        })  # 修改代码+PromptArchitectureV1: 结束超长动态 block 输入字典；若没有这行代码，Python 语法不完整
        self.assertTrue(result.compacted)  # 修改代码+PromptArchitectureV1: 断言结果标记发生了压缩；若没有这行代码，压缩只改文本但报告状态可能缺失
        self.assertIn("Compact Summary", result.system_prompt)  # 修改代码+PromptArchitectureV1: 断言 system prompt 明确包含 Compact Summary；若没有这行代码，模型可能看不出该块不是完整加载
    def test_build_initial_messages_uses_only_static_prompt_and_memory_blocks(self) -> None:  # 修改代码+AgentMemoryBoundary: 验证生产初始提示词只加载静态提示词和 memory.md 索引；若没有这行代码，agent_memory block 可能再次混入
        with tempfile.TemporaryDirectory() as raw_dir:  # 修改代码+AgentMemoryBoundary: 创建临时工作区隔离真实项目文件；若没有这行代码，测试可能读取当前仓库状态
            workspace = Path(raw_dir)  # 修改代码+AgentMemoryBoundary: 把临时目录转成 Path；若没有这行代码，后续文件操作不够稳定
            (workspace / "memory.md").write_text("# Memory\n\n目标 agent 自己的长期记忆。\n", encoding="utf-8")  # 修改代码+AgentMemoryBoundary: 写入目标 agent 自己的 memory.md；若没有这行代码，测试无法证明 memory 仍保留
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="ok")]), workspace=workspace, ask_permission=lambda action: True, prompt_soft_token_limit=200)  # 修改代码+AgentMemoryBoundary: 创建真实 agent；若没有这行代码，无法覆盖生产提示词装配路径
            messages = agent._build_initial_messages("继续")  # 修改代码+AgentMemoryBoundary: 调用真实初始消息构造流程；若没有这行代码，测试无法检查模型实际看到的 system prompt
            loaded_ids = [block.block_id for block in agent.last_prompt_surface_report.loaded_blocks]  # 修改代码+AgentMemoryBoundary: 读取真实加载 block 顺序；若没有这行代码，无法证明只剩两个默认 prompt block
            loaded_by_id = {block.block_id: block for block in agent.last_prompt_surface_report.loaded_blocks}  # 修改代码+AgentMemoryBoundary: 建立 block 报告索引；若没有这行代码，后续无法检查身份内核状态
            self.assertEqual(loaded_ids, ["prompt.kernel.identity", "context.long_term_memory_index"])  # 修改代码+AgentMemoryBoundary: 断言默认每轮只加载静态提示词和 memory.md 索引；若没有这行代码，project memory 关联回归不会失败
            self.assertIn("Long-Term Memory Index", str(messages[0]["content"]))  # 修改代码+AgentMemoryBoundary: 断言 memory.md 索引仍进入提示词；若没有这行代码，删除 agent_memory 时可能误删目标 agent 自己的记忆
            self.assertNotIn("Project Memory Index", str(messages[0]["content"]))  # 修改代码+AgentMemoryBoundary: 断言项目 agent_memory 索引不再进入提示词；若没有这行代码，Codex 开发记忆可能继续污染目标 agent
            self.assertEqual(loaded_by_id["prompt.kernel.identity"].status, "loaded")  # 修改代码+LeanSystemPrompt: 断言精简后仍加载身份内核且不会被压缩；若没有这行代码，修预算时可能误压缩最高优先级系统身份
    def test_runtime_instructions_mentions_prompt_architecture_v1_reports(self) -> None:  # 新增代码+PromptArchitectureV1: 验证运行时规则文档说明 Prompt Architecture v1 和两个报告工具；如果没有这行代码，文档漏写关键运行规则也不会被测试发现
        runtime_text = self._dynamic_prompt_file().read_text(encoding="utf-8")  # 新增代码+PromptArchitectureV1: 读取与测试文件同目录的 runtime_instructions.md；如果没有这行代码，测试无法检查真实文档内容
        self.assertIn("Prompt Architecture v1", runtime_text)  # 新增代码+PromptArchitectureV1: 断言运行时文档明确写出架构名称；如果没有这行代码，文档可能只写零散工具名而缺少版本边界
        self.assertIn("prompt_surface_report", runtime_text)  # 新增代码+PromptArchitectureV1: 断言运行时文档说明提示词表面报告工具；如果没有这行代码，用户可能不知道如何查看加载了什么和为什么加载
        self.assertIn("token_budget_report", runtime_text)  # 新增代码+PromptArchitectureV1: 断言运行时文档说明 token 预算报告工具；如果没有这行代码，预算解释缺失也不会阻止测试通过
    def test_readme_documents_prompt_registry_and_context_assembler(self) -> None:  # 新增代码+PromptArchitectureV1: 验证 README 记录 Prompt Registry、Context Assembler 和 Prompt Surface Report；如果没有这行代码，学习文档缺少新架构入口也不会被发现
        readme_text = (TEST_ROOT / "README.md").read_text(encoding="utf-8")  # 新增代码+PromptArchitectureV1: 读取真实 README 文档；如果没有这行代码，测试无法验证用户会看到的说明
        self.assertIn("Prompt Registry", readme_text)  # 新增代码+PromptArchitectureV1: 断言 README 说明提示词注册表；如果没有这行代码，注册表概念缺失也不会被测试发现
        self.assertIn("Context Assembler", readme_text)  # 新增代码+PromptArchitectureV1: 断言 README 说明上下文装配器；如果没有这行代码，用户可能不知道提示词如何被组装
        self.assertIn("Prompt Surface Report", readme_text)  # 新增代码+PromptArchitectureV1: 断言 README 说明提示词表面报告；如果没有这行代码，报告工具学习入口缺失也不会被发现
    def test_prompts_package_exports_static_prompt_loader(self) -> None:  # 新增代码+PromptsSplit: 验证 prompts 层导出静态提示词读取入口；若没有这行代码，阶段 6 可能只保留旧散落模块而没有稳定 prompts 包边界
        from learning_agent.prompts.static_prompt import read_static_prompt  # 新增代码+PromptsSplit: 从新 static_prompt 模块导入读取函数；若没有这行代码，无法证明静态提示词加载已经脱离主入口
        self.assertTrue(callable(read_static_prompt))  # 新增代码+PromptsSplit: 断言导出的读取入口可调用；若没有这行代码，导入到非函数对象也可能误通过
    def test_packaged_skills_use_three_layer_dynamic_prompt_tree(self) -> None:  # 新增代码+动态提示词分层: 验证包内 skill 已拆成索引、skill、rules 三层；若没有这行代码，动态提示词可能重新堆成一大坨
        skills_root = (TEST_ROOT / "skills")  # 新增代码+动态提示词分层: 定位真实包内 skills 根目录；若没有这行代码，测试无法扫描交付给 agent 的动态规则
        skill_files = sorted(skills_root.glob("*/SKILL.md"))  # 新增代码+动态提示词分层: 收集每个能力包的顶层 SKILL.md；若没有这行代码，后续无法逐一检查分层约定
        self.assertGreater(len(skill_files), 0)  # 新增代码+动态提示词分层: 确认至少存在一个 skill 文件；若没有这行代码，空目录也可能让循环测试假通过
        forbidden_terms = ("tool_search", "select_pack")  # 新增代码+动态提示词分层: 定义旧路由关键词黑名单；若没有这行代码，旧工具搜索路线可能继续污染新分层
        for skill_file in skill_files:  # 新增代码+动态提示词分层: 遍历每个顶层 skill 文件；若没有这行代码，只能检查单个样本而漏掉其他旧路由
            with self.subTest(skill_file=skill_file.name, parent=skill_file.parent.name):  # 新增代码+动态提示词分层: 为每个 skill 提供独立失败上下文；若没有这行代码，失败时难以定位哪个文件没改干净
                skill_text = skill_file.read_text(encoding="utf-8")  # 新增代码+动态提示词分层: 读取顶层 skill 正文；若没有这行代码，无法检查内容是否遵守分层
                rules_dir = skill_file.parent / "rules"  # 新增代码+动态提示词分层: 定位该 skill 的第三层子规则目录；若没有这行代码，无法验证 rules 层是否存在
                rule_files = sorted(rules_dir.glob("*.md"))  # 新增代码+动态提示词分层: 收集该 skill 的子规则文件；若没有这行代码，无法确认子规则是否实际落盘
                self.assertIn("learning_agent/skills/tool_list.md", skill_text)  # 新增代码+动态提示词分层: 断言顶层 skill 仍提醒先从总索引进入；若没有这行代码，模型可能跳过第一层目录
                self.assertIn("rules/", skill_text.replace("\\", "/"))  # 新增代码+动态提示词分层: 断言顶层 skill 只指向子规则而不是展开全部细节；若没有这行代码，SKILL.md 可能继续膨胀
                self.assertGreater(len(rule_files), 0)  # 新增代码+动态提示词分层: 断言每个 skill 至少有一个子规则文件；若没有这行代码，所谓第三层可能只是文案
                for forbidden_term in forbidden_terms:  # 新增代码+动态提示词分层: 遍历旧路由黑名单；若没有这行代码，只能手写重复断言且容易漏词
                    self.assertNotIn(forbidden_term, skill_text)  # 新增代码+动态提示词分层: 断言顶层 skill 不再推荐旧工具搜索和能力包语法；若没有这行代码，模型会被拉回旧架构
    def test_dynamic_prompt_file_is_dynamic_and_not_added_to_system_prompt(self) -> None:  # 修改代码+PromptFiles: 验证 dynamicprompt 文件是按需规则来源而不是每轮 system prompt；若没有这行代码，动态提示词正文可能悄悄回到常驻上下文
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 创建临时工作区，避免测试读写真实项目文件
            workspace = Path(raw_dir)  # 新增代码: 把临时目录转成 Path，方便创建规则文件
            dynamic_prompt_dir = workspace / "dynamicprompt"  # 新增代码+PromptFiles: 定位工作区动态提示词目录；若没有这行代码，无法验证用户自定义 dynamicprompt.md 的路径
            dynamic_prompt_dir.mkdir()  # 新增代码+PromptFiles: 创建 dynamicprompt 目录；若没有这行代码，写入 dynamicprompt.md 会失败
            dynamic_prompt_file = dynamic_prompt_dir / "dynamicprompt.md"  # 新增代码+PromptFiles: 定义动态提示词文件路径；若没有这行代码，测试仍会依赖旧 runtime 文件名
            dynamic_prompt_file.write_text("- 动态规则标记：始终解释工具边界。\n", encoding="utf-8")  # 修改代码+PromptFiles: 写入只应按需读取的动态规则标记；若没有这行代码，测试无法发现 dynamicprompt 正文被错误常驻注入
            model = ToolCallingFakeModel([ModelMessage(text="不会真正调用模型。")])  # 新增代码: 准备假模型满足 LearningAgent 构造参数；本测试只检查 messages
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码: 创建 agent，让它读取临时工作区里的 runtime_instructions.md
            messages = agent._build_initial_messages("你好")  # 新增代码: 直接构造初始 messages，观察模型第一轮会看到什么
            system_content = str(messages[0]["content"])  # 新增代码: 取出 system prompt 文本，便于断言运行时规则是否注入
            self.assertEqual(agent.dynamic_prompt_path, dynamic_prompt_file)  # 新增代码+PromptFiles: 断言工作区 dynamicprompt 优先；若没有这行代码，用户自定义动态规则可能不生效
            self.assertNotIn("Runtime Tool Policy / 运行时工具策略", system_content)  # 修改代码+DynamicRuntimeRules: 断言旧 runtime 常驻区块不再进入首轮 system prompt；若没有这行代码，提示词仍会被大文件拖胖
            self.assertNotIn("动态规则标记", system_content)  # 修改代码+DynamicRuntimeRules: 断言 runtime 文件正文没有自动注入；若没有这行代码，按需加载边界无法被测试锁定
            self.assertIn("动态运行规则", system_content)  # 新增代码+DynamicRuntimeRules: 断言静态 kernel 仍告诉模型存在动态规则层；若没有这行代码，模型第一轮不知道何时按需加载规则
    def test_dynamic_prompt_can_be_loaded_through_skill_load(self) -> None:  # 新增代码+PromptFiles: 验证 dynamicprompt.md 可以通过 skill_load 按需加载；若没有这行代码，动态规则可能只是不常驻但无法被模型读取
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PromptFiles: 创建临时工作区隔离真实动态提示词；若没有这行代码，测试会依赖用户当前文件
            workspace = Path(raw_dir)  # 新增代码+PromptFiles: 把临时目录转成 Path；若没有这行代码，后续路径拼接不够稳定
            dynamic_prompt_dir = workspace / "dynamicprompt"  # 新增代码+PromptFiles: 定位工作区动态提示词目录；若没有这行代码，无法验证工作区覆盖文件可被加载
            dynamic_prompt_dir.mkdir()  # 新增代码+PromptFiles: 创建 dynamicprompt 目录；若没有这行代码，写入测试文件会失败
            (dynamic_prompt_dir / "dynamicprompt.md").write_text("动态提示词可加载标记\n", encoding="utf-8")  # 新增代码+PromptFiles: 写入可断言标记；若没有这行代码，测试无法证明正文来自 dynamicprompt.md
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="ok")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+PromptFiles: 创建 agent 触发动态提示词路径解析；若没有这行代码，无法调用真实 skill_load 流程
            output = agent._execute_tool(ToolCall(name="skill_load", arguments={"name": "dynamicprompt", "max_chars": 2000}))  # 新增代码+PromptFiles: 通过公开工具通道加载动态提示词；若没有这行代码，测试绕不开模型实际会用的入口
            self.assertIn("skill_load 成功：name=dynamicprompt", output)  # 新增代码+PromptFiles: 断言伪 skill 名称可被找到；若没有这行代码，dynamicprompt 入口缺失不会失败
            self.assertIn("动态提示词可加载标记", output)  # 新增代码+PromptFiles: 断言 dynamicprompt.md 正文按需返回；若没有这行代码，工具可能只返回元数据不返回规则
    def test_dynamic_prompt_falls_back_to_learning_agent_file(self) -> None:  # 修改代码+PromptFiles: 验证项目根目录没有 dynamicprompt 时会回退到包内 dynamicprompt.md；若没有这行代码，默认动态规则索引可能找不到
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RuntimePathFix: 创建没有 dynamicprompt.md 的临时项目根目录；若没有这行代码，无法复现包内兜底路径
            workspace = Path(raw_dir)  # 新增代码+RuntimePathFix: 把临时目录转换成 Path 传给 LearningAgent；若没有这行代码，后续路径判断不够清楚
            package_dynamic_prompt_file = self._dynamic_prompt_file()  # 修改代码+PromptFiles: 定位 learning_agent 包内真实 dynamicprompt 文件；若没有这行代码，测试无法确认新兜底目标
            model = ToolCallingFakeModel([ModelMessage(text="不会真正调用模型。")])  # 新增代码+RuntimePathFix: 使用假模型避免真实 API 调用；若没有这行代码，测试会依赖外部模型
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+RuntimePathFix: 创建被测 agent；若没有这行代码，无法触发 runtime 路径解析
            messages = agent._build_initial_messages("你好")  # 新增代码+RuntimePathFix: 构造首轮 messages 观察真实 system prompt；若没有这行代码，测试只会检查文件存在而不检查模型实际看到什么
            system_content = str(messages[0]["content"])  # 新增代码+RuntimePathFix: 取出 system prompt 文本用于断言；若没有这行代码，后续检查没有对象
            self.assertEqual(agent.dynamic_prompt_path, package_dynamic_prompt_file)  # 修改代码+PromptFiles: 断言 agent 实际选择包内 dynamicprompt 文件；若没有这行代码，路径回退可能没有真正生效
            self.assertNotIn("Learning Agent Runtime Kernel", system_content)  # 修改代码+DynamicRuntimeRules: 断言包内 runtime 索引不会自动注入首轮；若没有这行代码，路径兜底会再次把动态规则变成常驻规则
            self.assertIn("learning_agent/skills/tool_list.md", system_content)  # 修改代码+极简工具面: 断言静态 kernel 指向可读取的 skill 索引；若没有这行代码，首轮模型不知道从哪里按需发现能力
            self.assertIn("read / write / edit / bash", system_content)  # 修改代码+极简工具面: 断言静态 kernel 明确四原子工具边界；若没有这行代码，模型可能继续寻找旧能力包加载语法
            self.assertNotIn("没有找到 dynamicprompt.md", system_content)  # 修改代码+PromptFiles: 断言不再使用缺失占位文本；若没有这行代码，动态提示词路径兜底可能失效
    def test_system_prompt_uses_mature_coding_agent_identity(self) -> None:  # 新增代码+PromptContextV1: 验证系统提示词升级为成熟 coding agent 身份；若省略: 项目可能继续停留在最小教学 agent 定位
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PromptContextV1: 创建临时工作区隔离 memory 和规则文件；若省略: 测试会污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+PromptContextV1: 把临时目录转成 Path 方便拼接文件路径；若省略: 后续路径操作会更容易写错
            (workspace / "runtime_instructions.md").write_text("## Tool Policy\n\n- 测试规则。\n", encoding="utf-8")  # 新增代码+PromptContextV1: 写入最小运行规则；若省略: 测试无法证明规则区块仍被注入
            model = ToolCallingFakeModel([ModelMessage(text="不会真正调用模型。")])  # 新增代码+PromptContextV1: 使用假模型避免联网；若省略: 测试会依赖真实模型而不稳定
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+PromptContextV1: 创建 agent 以构造系统提示词；若省略: 无法检查真实提示词生成逻辑
            messages = agent._build_initial_messages("请帮我修改代码。")  # 新增代码+PromptContextV1: 构造一轮初始消息；若省略: system prompt 不会生成
            system_content = str(messages[0]["content"])  # 新增代码+PromptContextV1: 取出系统提示词文本；若省略: 后续断言没有检查对象
            self.assertIn("你是一个面向软件工程任务的成熟 coding agent", system_content)  # 修改代码+LeanSystemPrompt: 断言精简身份不再重复 Learning Agent 名称；若没有这行代码，系统提示词可能回退到旧冗长身份
            self.assertIn("对齐并逐步超越 Codex / Claude Code", system_content)  # 修改代码+LeanSystemPrompt: 断言长期演进目标采用用户确认的新表述；若没有这行代码，提示词可能仍停留在“逐步接近”
            self.assertIn("工具调用之外输出的所有文本都会展示给用户", system_content)  # 新增代码+LeanSystemPrompt: 断言 Claude Code 风格输出边界进入系统提示词；若没有这行代码，模型可能忽略可见文本边界
            self.assertIn("提示注入（Prompt Injection）", system_content)  # 新增代码+LeanSystemPrompt: 断言外部工具结果提示注入风险进入系统提示词；若没有这行代码，模型可能不标记可疑外部内容
            self.assertIn("不要假设所有历史细节都完整可见", system_content)  # 新增代码+LeanSystemPrompt: 断言压缩上下文边界进入系统提示词；若没有这行代码，模型可能误以为历史无限完整
            self.assertIn("不必要的兼容性垫片", system_content)  # 新增代码+LeanSystemPrompt: 断言范围控制和避免 shims 的规则进入系统提示词；若没有这行代码，模型可能继续做过度兼容
            self.assertIn("动态运行规则", system_content)  # 新增代码+DynamicRuntimeRules: 断言按需规则加载入口进入静态 kernel；若没有这行代码，runtime 动态化后模型第一轮不知道有规则包可加载
            self.assertIn("learning_agent/skills/tool_list.md", system_content)  # 修改代码+极简工具面: 断言静态 kernel 告诉模型通过 read 读取 skill 索引；若没有这行代码，模型可能不知道如何发现动态规则
            self.assertIn("read / write / edit / bash", system_content)  # 修改代码+极简工具面: 断言静态 kernel 告诉模型只依赖四原子工具；若没有这行代码，隐藏工具池可能重新牵引模型走旧架构
            self.assertNotIn("select_pack:<pack_name>", system_content)  # 修改代码+极简工具面: 断言旧能力包加载语法不再常驻；若没有这行代码，系统提示词会继续携带旧工具路由
            self.assertNotIn("Prompt / Context Architecture v1 compatibility", system_content)  # 修改代码+LeanSystemPrompt: 断言旧兼容标题已从每轮系统提示词移除；若没有这行代码，精简目标可能被旧兼容文案拖回
            self.assertNotIn("Tool Boundary / 工具边界", system_content)  # 修改代码+LeanSystemPrompt: 断言工具边界已并入精简原则而非单独常驻区块；若没有这行代码，系统提示词可能继续保留重复区块
            self.assertNotIn("Response Policy / 输出策略", system_content)  # 修改代码+LeanSystemPrompt: 断言输出策略已下沉到 runtime kernel；若没有这行代码，系统提示词可能继续重复运行规则
            self.assertNotIn("Runtime Tool Policy / 运行时工具策略", system_content)  # 新增代码+DynamicRuntimeRules: 断言 runtime 细节层不再常驻；若没有这行代码，静态提示词仍会继续过大
            self.assertNotIn("你是 Learning Agent，一个教学用的最小私人 agent。", system_content)  # 新增代码+PromptContextV1: 断言旧核心身份被替换；若省略: 新旧身份可能同时存在造成行为摇摆
    def test_system_prompt_declares_prompt_surface_v2_scope(self) -> None:  # 新增代码+PromptSurfaceV2: 验证系统提示词明确声明会影响判断的提示词表面；若省略: 后续改规则可能继续把无关架构文档混进模型判断入口
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PromptSurfaceV2: 创建临时工作区隔离真实项目文件；若省略: 测试可能污染用户目录
            workspace = Path(raw_dir)  # 新增代码+PromptSurfaceV2: 把临时目录转成 Path；若省略: 文件路径拼接会更难读
            (workspace / "runtime_instructions.md").write_text("## Tool Policy\n\n- 测试规则。\n", encoding="utf-8")  # 新增代码+PromptSurfaceV2: 写入最小运行规则文件；若省略: 系统提示词会出现缺失占位干扰断言
            model = ToolCallingFakeModel([ModelMessage(text="不会真正调用模型。")])  # 新增代码+PromptSurfaceV2: 使用假模型避免真实 API 调用；若省略: 单元测试会变慢且不稳定
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+PromptSurfaceV2: 创建被测 agent；若省略: 无法生成真实 system prompt
            messages = agent._build_initial_messages("只改提示词，不改其它功能。")  # 新增代码+PromptSurfaceV2: 构造一轮初始消息；若省略: system prompt 不会生成
            system_content = str(messages[0]["content"])  # 新增代码+PromptSurfaceV2: 取出 system prompt 文本；若省略: 后续断言没有检查对象
            self.assertIn("Prompt Surface Architecture v2", system_content)  # 新增代码+PromptSurfaceV2: 断言提示词架构版本进入模型上下文；若省略: 旧 PromptContextV1 可能继续主导判断
            self.assertIn("用户本轮明确纠偏", system_content)  # 新增代码+PromptSurfaceV2: 断言本轮纠偏高于历史计划；若省略: agent 可能继续执行旧路线而忽略用户最新要求
            self.assertIn("工具 schema/MCP 工具说明", system_content)  # 新增代码+PromptSurfaceV2: 断言工具说明也被纳入 prompt surface；若省略: 改系统提示词却漏掉工具描述会继续影响选择
    def test_parent_agent_memory_files_are_not_injected_into_system_prompt(self) -> None:  # 修改代码+AgentMemoryBoundary: 验证父目录 Codex agent_memory 不会被目标 agent 自动读取；若没有这行代码，workspace.parent 关联可能回归
        with tempfile.TemporaryDirectory() as raw_dir:  # 修改代码+AgentMemoryBoundary: 创建临时项目根目录；若没有这行代码，测试会碰到真实 agent_memory
            project_root = Path(raw_dir)  # 修改代码+AgentMemoryBoundary: 保存项目根目录 Path；若没有这行代码，后续路径表达不清楚
            workspace = project_root / "learning_agent"  # 修改代码+AgentMemoryBoundary: 模拟目标 agent 从子目录运行；若没有这行代码，无法覆盖旧 workspace.parent/agent_memory 查找路径
            workspace.mkdir()  # 修改代码+AgentMemoryBoundary: 创建 workspace 目录；若没有这行代码，LearningAgent 初始化没有工作区
            memory_dir = project_root / "agent_memory"  # 修改代码+AgentMemoryBoundary: 定位父目录里不应被目标 agent 读取的 Codex 记忆目录；若没有这行代码，测试无法覆盖父目录污染风险
            memory_dir.mkdir()  # 修改代码+AgentMemoryBoundary: 创建 agent_memory 目录；若没有这行代码，写入 context/progress/bugs 会失败
            (memory_dir / "context.md").write_text("父目录 Codex context 不应进入目标 agent", encoding="utf-8")  # 修改代码+AgentMemoryBoundary: 写入可断言 context 标记；若没有这行代码，误读父目录 context 时测试抓不到
            (memory_dir / "progress.md").write_text("父目录 Codex progress 不应进入目标 agent", encoding="utf-8")  # 修改代码+AgentMemoryBoundary: 写入可断言 progress 标记；若没有这行代码，误读父目录 progress 时测试抓不到
            (memory_dir / "bugs.md").write_text("父目录 Codex bugs 不应进入目标 agent", encoding="utf-8")  # 修改代码+AgentMemoryBoundary: 写入可断言 bugs 标记；若没有这行代码，误读父目录 bugs 时测试抓不到
            model = ToolCallingFakeModel([ModelMessage(text="不会真正调用模型。")])  # 修改代码+AgentMemoryBoundary: 使用假模型；若没有这行代码，测试会依赖真实模型
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 修改代码+AgentMemoryBoundary: 创建被测 agent；若没有这行代码，无法调用真实提示词构造逻辑
            messages = agent._build_initial_messages("继续。")  # 修改代码+AgentMemoryBoundary: 构造初始 messages；若没有这行代码，system prompt 不会生成
            system_content = str(messages[0]["content"])  # 修改代码+AgentMemoryBoundary: 提取 system prompt；若没有这行代码，后续断言没有目标
            self.assertNotIn("Project Agent Memory / 项目级上下文", system_content)  # 修改代码+AgentMemoryBoundary: 断言项目记忆标题不再进入模型；若没有这行代码，旧三件套入口可能回归
            self.assertNotIn("父目录 Codex context 不应进入目标 agent", system_content)  # 修改代码+AgentMemoryBoundary: 断言父目录 context.md 不注入；若没有这行代码，Codex 开发上下文会污染用户 agent
            self.assertNotIn("父目录 Codex progress 不应进入目标 agent", system_content)  # 修改代码+AgentMemoryBoundary: 断言父目录 progress.md 不注入；若没有这行代码，Codex 当前任务进度会污染用户 agent
            self.assertNotIn("父目录 Codex bugs 不应进入目标 agent", system_content)  # 修改代码+AgentMemoryBoundary: 断言父目录 bugs.md 不注入；若没有这行代码，Codex 风险记录会污染用户 agent
    def test_system_prompt_defines_context_priority(self) -> None:  # 新增代码+PromptContextV1: 验证系统提示词声明上下文优先级；若省略: agent 不知道项目规则、用户请求和记忆之间谁优先
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PromptContextV1: 创建临时工作区隔离上下文文件；若省略: 测试会读写真实工作区
            workspace = Path(raw_dir)  # 新增代码+PromptContextV1: 把临时目录转成 Path；若省略: 后续文件路径拼接不方便
            (workspace / "runtime_instructions.md").write_text("## Tool Policy\n\n- 测试规则。\n", encoding="utf-8")  # 新增代码+PromptContextV1: 写入运行规则文件；若省略: 系统提示词的运行规则区块缺少真实内容
            model = ToolCallingFakeModel([ModelMessage(text="不会真正调用模型。")])  # 新增代码+PromptContextV1: 使用假模型避免真实请求；若省略: 测试会变慢且不稳定
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+PromptContextV1: 创建 agent；若省略: 无法调用提示词构造函数
            messages = agent._build_initial_messages("继续当前任务。")  # 新增代码+PromptContextV1: 构造初始消息；若省略: 没有系统提示词可检查
            system_content = str(messages[0]["content"])  # 新增代码+PromptContextV1: 取出系统提示词；若省略: 后续断言无法执行
            self.assertIn("Context Policy", system_content)  # 新增代码+PromptContextV1: 断言上下文策略区块存在；若省略: 上下文加载策略可能散落无结构
            self.assertIn("系统身份和安全边界", system_content)  # 新增代码+PromptContextV1: 断言最高优先级上下文被说明；若省略: agent 可能忽略系统边界
            self.assertIn("用户本轮明确请求", system_content)  # 新增代码+PromptContextV1: 断言用户请求优先级被说明；若省略: agent 可能被旧记忆带偏
            self.assertIn("memory.md", system_content)  # 修改代码+AgentMemoryBoundary: 断言目标 agent 自己的长期记忆入口仍被说明；若没有这行代码，删除 agent_memory 时可能误删 memory.md 语义
            self.assertNotIn("agent_memory/context.md", system_content)  # 修改代码+AgentMemoryBoundary: 断言 Codex 开发用 context.md 不再出现在目标 agent 静态提示词；若没有这行代码，旧三件套规则可能回归
            self.assertNotIn("agent_memory/progress.md", system_content)  # 修改代码+AgentMemoryBoundary: 断言 Codex 开发用 progress.md 不再出现在目标 agent 静态提示词；若没有这行代码，旧三件套规则可能回归
            self.assertNotIn("agent_memory/bugs.md", system_content)  # 修改代码+AgentMemoryBoundary: 断言 Codex 开发用 bugs.md 不再出现在目标 agent 静态提示词；若没有这行代码，旧三件套规则可能回归
    def test_runtime_config_reads_prompt_soft_token_limit_file_and_environment(self) -> None:  # 新增代码+PromptArchitectureV1: 验证运行配置能控制 prompt soft token limit；若没有这行代码，生产 compact 预算可能一直停留在硬编码默认值
        old_env = os.environ.pop("LEARNING_AGENT_PROMPT_SOFT_TOKEN_LIMIT", None)  # 新增代码+PromptArchitectureV1: 暂时清理预算环境变量避免污染文件值断言；若没有这行代码，用户机器环境可能让测试不稳定
        try:  # 新增代码+PromptArchitectureV1: 用 try/finally 保证环境变量恢复；若没有这行代码，测试失败时会污染后续测试
            with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PromptArchitectureV1: 创建临时工作区写入 runtime_config.json；若没有这行代码，测试可能修改真实运行配置
                workspace = Path(raw_dir)  # 新增代码+PromptArchitectureV1: 把临时目录转成 Path；若没有这行代码，后续写配置和加载配置不够清楚
                (workspace / "runtime_config.json").write_text(json.dumps({"prompt_soft_token_limit": 1234}, ensure_ascii=False), encoding="utf-8")  # 新增代码+PromptArchitectureV1: 写入文件级 prompt 软预算；若没有这行代码，无法证明配置文件字段会生效
                self.assertEqual(load_agent_runtime_config(workspace).prompt_soft_token_limit, 1234)  # 新增代码+PromptArchitectureV1: 断言文件里的预算被读取；若没有这行代码，字段被忽略不会被发现
                os.environ["LEARNING_AGENT_PROMPT_SOFT_TOKEN_LIMIT"] = "2345"  # 新增代码+PromptArchitectureV1: 设置环境变量覆盖文件预算；若没有这行代码，无法验证临时启动覆盖能力
                self.assertEqual(load_agent_runtime_config(workspace).prompt_soft_token_limit, 2345)  # 新增代码+PromptArchitectureV1: 断言环境变量优先；若没有这行代码，CLI 外预算配置可能不生效
        finally:  # 新增代码+PromptArchitectureV1: 进入环境变量恢复分支；若没有这行代码，测试会影响用户当前进程环境
            if old_env is None:  # 新增代码+PromptArchitectureV1: 如果测试前没有该变量；若没有这行代码，无法区分删除和恢复两种情况
                os.environ.pop("LEARNING_AGENT_PROMPT_SOFT_TOKEN_LIMIT", None)  # 新增代码+PromptArchitectureV1: 删除测试设置的预算变量；若没有这行代码，后续测试会读到测试残留
            else:  # 新增代码+PromptArchitectureV1: 如果测试前已有预算变量；若没有这行代码，用户原配置无法恢复
                os.environ["LEARNING_AGENT_PROMPT_SOFT_TOKEN_LIMIT"] = old_env  # 新增代码+PromptArchitectureV1: 恢复原始预算环境变量；若没有这行代码，会改变用户运行环境
    def test_missing_dynamic_prompt_file_does_not_pollute_system_prompt(self) -> None:  # 修改代码+PromptFiles: 验证缺少动态提示词文件不会污染常驻系统提示词；若没有这行代码，动态文件缺失会浪费每轮上下文
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 创建没有 dynamicprompt.md 的临时工作区
            workspace = Path(raw_dir)  # 新增代码: 把临时目录转成 Path，方便传给 LearningAgent
            model = ToolCallingFakeModel([ModelMessage(text="不会真正调用模型。")])  # 新增代码: 准备假模型满足构造参数；本测试不需要真实模型响应
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码: 创建 agent，触发 memory.md 初始化但不创建规则文件
            agent.dynamic_prompt_path = workspace / "dynamicprompt" / "missing_dynamicprompt.md"  # 修改代码+PromptFiles: 显式指向不存在的 dynamicprompt 文件；若没有这行代码，新默认包内回退会让本测试不覆盖缺失场景
            messages = agent._build_initial_messages("你好")  # 新增代码: 构造初始 messages，验证缺失规则文件时不会报错
            system_content = str(messages[0]["content"])  # 新增代码: 取出 system prompt 文本，便于检查占位说明
            self.assertNotIn("Runtime Tool Policy / 运行时工具策略", system_content)  # 修改代码+DynamicRuntimeRules: 缺失 runtime 文件也不应产生常驻运行规则区块；若没有这行代码，动态规则缺失会重新污染 system prompt
            self.assertNotIn("没有找到 dynamicprompt.md", system_content)  # 修改代码+PromptFiles: 缺失动态文件不再写进每轮提示词；若没有这行代码，缺失占位会浪费常驻上下文
            self.assertIn("动态运行规则", system_content)  # 新增代码+DynamicRuntimeRules: 即使动态文件缺失，静态 kernel 仍保留按需规则加载原则；若没有这行代码，模型不知道后续可加载规则来源
    def test_agent_can_write_and_read_todos_without_permission_prompt(self) -> None:  # 新增代码+TodoWrite: 验证 agent 能写入并读取内部任务清单且不弹外部权限确认；若省略: Todo 工具可能无法实际保存状态
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TodoWrite: 创建临时工作区隔离 todo_state.json；若省略: 测试会污染真实 learning_agent 任务清单
            workspace = Path(raw_dir)  # 新增代码+TodoWrite: 把临时目录转成 Path 便于构造 agent；若省略: 路径处理不够清楚
            permission_requests: list[str] = []  # 新增代码+TodoWrite: 记录权限请求以确认 TodoWrite 不当成外部副作用；若省略: 无法发现工具错误地频繁打断用户
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: permission_requests.append(action) or True)  # 新增代码+TodoWrite: 创建测试 agent 并捕获权限请求；若省略: 无法直接执行内置 Todo 工具
            write_output = agent._execute_tool(ToolCall(name="todo_write", arguments={"todos": [{"content": "梳理工具列表", "status": "in_progress", "priority": "high"}, {"content": "补充后台命令工具", "status": "pending"}]}))  # 新增代码+TodoWrite: 写入两条任务模拟 Claude Code 式计划；若省略: 无法验证持久化和默认 priority
            read_output = agent._execute_tool(ToolCall(name="todo_read", arguments={}))  # 新增代码+TodoWrite: 读取刚保存的任务清单；若省略: 无法验证 todo_read 能恢复状态
            todo_payload = json.loads((workspace / "todo_state.json").read_text(encoding="utf-8"))  # 新增代码+TodoWrite: 读取落盘 JSON 以验证结构化保存；若省略: 只看输出无法证明文件内容正确
            self.assertEqual(permission_requests, [])  # 新增代码+TodoWrite: 断言内部任务清单更新不触发用户权限确认；若省略: agent 长任务会被任务状态更新频繁打断
            self.assertIn("todo_write 成功", write_output)  # 新增代码+TodoWrite: 断言写入工具返回成功说明；若省略: 工具可能静默失败而测试不发现
            self.assertIn("梳理工具列表", read_output)  # 新增代码+TodoWrite: 断言读取结果包含第一条任务；若省略: todo_read 可能没有读到真实状态
            self.assertEqual(todo_payload["todos"][0]["status"], "in_progress")  # 新增代码+TodoWrite: 断言状态字段被原样保存；若省略: 任务进度可能丢失
            self.assertEqual(todo_payload["todos"][1]["priority"], "medium")  # 新增代码+TodoWrite: 断言未传 priority 时默认 medium；若省略: 后续模型可能拿到缺字段任务
    def test_task_rejects_empty_prompt(self) -> None:  # 新增代码+TaskAgent: 验证 task 缺少 prompt 时返回可读失败；若省略: 模型传错参数可能得到模糊结果
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TaskAgent: 创建临时工作区隔离测试；若省略: 测试可能影响真实工作区
            workspace = Path(raw_dir)  # 新增代码+TaskAgent: 把临时目录转成 Path；若省略: agent 构造不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+TaskAgent: 创建测试 agent；若省略: 无法执行 task 工具
            output = agent._execute_tool(ToolCall(name="task", arguments={"prompt": ""}))  # 新增代码+TaskAgent: 提交空 prompt 触发校验；若省略: 空 prompt 分支没有测试输入
            self.assertIn("task 失败", output)  # 新增代码+TaskAgent: 断言空 prompt 返回失败前缀；若省略: 错误状态可能被误判为成功
            self.assertIn("prompt", output)  # 新增代码+TaskAgent: 断言错误说明缺少 prompt；若省略: 模型难以修正 task 参数
    def test_agent_lists_local_skills(self) -> None:  # 新增代码+SkillLoad: 验证 agent 能扫描工作区 skills 目录并列出 skill 元信息；若省略: 本地 skill 发现能力没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+SkillLoad: 创建临时工作区隔离 skills 测试文件；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+SkillLoad: 把临时目录转成 Path；若省略: 后续路径拼接不够清晰
            skill_dir = workspace / "skills" / "code-review"  # 新增代码+SkillLoad: 定义本地 skill 目录；若省略: skill_list 没有可发现目标
            skill_dir.mkdir(parents=True)  # 新增代码+SkillLoad: 创建 skill 目录；若省略: 写入 SKILL.md 会因目录不存在失败
            (skill_dir / "SKILL.md").write_text("---\nname: code-review\ndescription: Review code safely\n---\n# Code Review\nUse a review-first workflow.\n", encoding="utf-8")  # 新增代码+SkillLoad: 写入带 frontmatter 的 skill 文件；若省略: skill_list 无法验证元信息解析
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+SkillLoad: 创建测试 agent；若省略: 无法通过工具路由执行 skill_list
            output = agent._execute_tool(ToolCall(name="skill_list", arguments={"query": "review", "max_results": 5}))  # 新增代码+SkillLoad: 请求按 review 搜索本地 skills；若省略: 无法验证 skill_list 分发和搜索
            self.assertIn("skill_list 成功", output)  # 新增代码+SkillLoad: 断言列 skill 工具返回成功前缀；若省略: 未知工具输出可能被后续断言误判
            self.assertIn("code-review", output)  # 新增代码+SkillLoad: 断言 skill 名进入列表；若省略: 元信息解析或目录扫描退化不会被发现
            self.assertIn("Review code safely", output)  # 新增代码+SkillLoad: 断言 description 进入列表；若省略: 模型缺少选择 skill 的语义依据
            self.assertIn("skills/code-review/SKILL.md", output.replace("\\", "/"))  # 新增代码+SkillLoad: 断言相对路径进入列表；若省略: 用户和模型不知道 skill 文件位置
    def test_agent_lists_packaged_runtime_rule_skills_without_workspace_skills(self) -> None:  # 新增代码+DynamicRuntimeRules: 验证没有工作区 skills 时也能发现包内动态规则 skills；若没有这行代码，runtime 动态化后模型会找不到规则包
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DynamicRuntimeRules: 创建空工作区隔离用户真实 skills；若没有这行代码，测试可能被真实项目 skills 偶然通过
            workspace = Path(raw_dir)  # 新增代码+DynamicRuntimeRules: 把临时目录转成 Path；若没有这行代码，agent 构造和路径判断不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+DynamicRuntimeRules: 创建没有工作区 skills 的 agent；若没有这行代码，无法验证包内 skills fallback
            output = agent._execute_tool(ToolCall(name="skill_list", arguments={"query": "mcp", "max_results": 5}))  # 新增代码+DynamicRuntimeRules: 搜索包内 mcp 动态规则 skill；若没有这行代码，skill 发现 fallback 不会执行
            self.assertIn("skill_list 成功", output)  # 新增代码+DynamicRuntimeRules: 断言 skill_list 正常返回；若没有这行代码，失败输出可能被后续关键词误判
            self.assertIn("mcp", output)  # 新增代码+DynamicRuntimeRules: 断言包内 mcp skill 可发现；若没有这行代码，MCP 详细规则无法按需加载
            self.assertIn("learning_agent/skills/mcp/SKILL.md", output.replace("\\", "/"))  # 新增代码+DynamicRuntimeRules: 断言结果指向包内动态规则文件；若没有这行代码，模型和用户无法定位规则来源
    def test_agent_loads_packaged_runtime_rule_skill_by_name(self) -> None:  # 新增代码+DynamicRuntimeRules: 验证包内动态规则 skill 能被按名加载；若没有这行代码，静态 kernel 提示 skill_load 但真实加载会失败
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DynamicRuntimeRules: 创建空工作区避免依赖真实项目根 skills；若没有这行代码，测试可能被用户自定义 skill 干扰
            workspace = Path(raw_dir)  # 新增代码+DynamicRuntimeRules: 把临时目录转成 Path；若没有这行代码，agent 构造不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+DynamicRuntimeRules: 创建测试 agent；若没有这行代码，无法执行 skill_load
            output = agent._execute_tool(ToolCall(name="skill_load", arguments={"name": "mcp", "max_chars": 2000}))  # 新增代码+DynamicRuntimeRules: 加载包内 MCP 动态规则 skill；若没有这行代码，按需加载路径没有测试输入
            self.assertIn("skill_load 成功", output)  # 新增代码+DynamicRuntimeRules: 断言加载成功；若没有这行代码，失败路径可能被正文关键词掩盖
            self.assertIn("learning_agent/skills/mcp/rules/resources_prompts.md", output)  # 修改代码+动态提示词分层: 断言 skill 正文指向第三层 MCP 子规则；若没有这行代码，模型加载父 skill 后不知道继续读哪份细则
            self.assertNotIn("select_pack:mcp", output)  # 修改代码+动态提示词分层: 断言按需 skill 不再把模型带回旧能力包选择语法；若没有这行代码，旧路由可能重新污染动态提示词
            rule_text = self._skill_rule_file("mcp", "resources_prompts.md").read_text(encoding="utf-8")  # 修改代码+动态提示词分层: 单独读取第三层 MCP 规则验证细节仍存在；若没有这行代码，父 skill 变短后可能漏测资源规则
            self.assertIn("list_mcp_resources", rule_text)  # 修改代码+动态提示词分层: 断言 MCP 详细规则被下沉到子规则文件；若没有这行代码，runtime 动态化后 MCP resources 规则可能丢失
    def test_agent_loads_local_skill_by_name(self) -> None:  # 新增代码+SkillLoad: 验证 agent 能按 skill 名称加载 SKILL.md 正文；若省略: skill_load 核心读取能力没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+SkillLoad: 创建临时工作区隔离 skill 文件；若省略: 测试可能读取真实 skills
            workspace = Path(raw_dir)  # 新增代码+SkillLoad: 把临时目录转成 Path；若省略: 后续路径拼接不够清晰
            skill_dir = workspace / "skills" / "code-review"  # 新增代码+SkillLoad: 定义 skill 目录；若省略: skill_load 没有可加载目标
            skill_dir.mkdir(parents=True)  # 新增代码+SkillLoad: 创建 skill 目录；若省略: 写入 SKILL.md 会失败
            (skill_dir / "SKILL.md").write_text("---\nname: code-review\ndescription: Review code safely\n---\n# Code Review\nUse a review-first workflow.\n", encoding="utf-8")  # 新增代码+SkillLoad: 写入可加载 skill 内容；若省略: skill_load 无法验证正文返回
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+SkillLoad: 创建测试 agent；若省略: 无法通过工具路由执行 skill_load
            output = agent._execute_tool(ToolCall(name="skill_load", arguments={"name": "code-review", "max_chars": 2000}))  # 新增代码+SkillLoad: 请求加载指定 skill；若省略: 无法验证 skill_load 分发和读取
            self.assertIn("skill_load 成功", output)  # 新增代码+SkillLoad: 断言加载 skill 返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("name=code-review", output)  # 新增代码+SkillLoad: 断言输出包含加载的 skill 名；若省略: 模型难以确认加载目标
            self.assertIn("Use a review-first workflow.", output)  # 新增代码+SkillLoad: 断言 SKILL.md 正文进入结果；若省略: skill_load 可能只返回元信息不返回说明书
    def test_skill_load_reports_unknown_skill(self) -> None:  # 新增代码+SkillLoad: 验证加载不存在 skill 时返回可读失败；若省略: 模型传错名称可能得到模糊错误
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+SkillLoad: 创建临时工作区隔离空 skills 场景；若省略: 测试会受真实项目 skills 影响
            workspace = Path(raw_dir)  # 新增代码+SkillLoad: 把临时目录转成 Path；若省略: agent 构造不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+SkillLoad: 创建测试 agent；若省略: 无法执行 skill_load
            output = agent._execute_tool(ToolCall(name="skill_load", arguments={"name": "missing"}))  # 新增代码+SkillLoad: 请求加载不存在的 skill；若省略: 未知 skill 分支没有测试输入
            self.assertIn("skill_load 失败", output)  # 新增代码+SkillLoad: 断言未知 skill 返回失败前缀；若省略: 错误状态可能被误判为成功
            self.assertIn("没有找到", output)  # 新增代码+SkillLoad: 断言错误说明名称未找到；若省略: 模型难以修正 skill 名称
    def test_runtime_instructions_are_short_kernel_with_skill_router(self) -> None:  # 新增代码+CapabilityPacks: 验证运行时规则已经从长说明压成短内核；若没有这行代码，runtime_instructions 会再次膨胀进每轮 prompt
        runtime_file = self._dynamic_prompt_file()  # 新增代码+CapabilityPacks: 定位真实运行时规则文件；若没有这行代码，测试可能检查不到 agent 实际加载文件
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+CapabilityPacks: 用 UTF-8 读取中文规则；若没有这行代码，Windows 默认编码可能导致中文断言不稳定
        self.assertLess(len(runtime_text), 6000)  # 新增代码+CapabilityPacks: 断言常驻 runtime kernel 少于 6000 字符；若没有这行代码，方案 B 的 prompt 精简目标没有回归保护
        self.assertIn("tool_list.md", runtime_text)  # 修改代码+极简工具面: 断言短内核说明读取 skill 索引；若没有这行代码，模型可能不知道如何按需发现能力
        self.assertIn("read / write / edit / bash", runtime_text)  # 修改代码+极简工具面: 断言短内核保留四原子工具边界；若没有这行代码，模型可能继续猜旧工具名
        self.assertNotIn("select_pack:<pack_name>", runtime_text)  # 修改代码+极简工具面: 断言旧能力包语法不再进入动态规则；若没有这行代码，按需提示词仍会牵引旧架构
    def test_runtime_instructions_are_layered_for_prompt_context_v1(self) -> None:  # 新增代码+PromptContextV1: 验证运行规则从长清单升级为分层规则；若省略: runtime_instructions 可能继续无结构膨胀
        runtime_file = self._dynamic_prompt_file()  # 新增代码+PromptContextV1: 定位真实运行规则文件；若省略: 测试无法覆盖 agent 实际读取的文件
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+PromptContextV1: 用 UTF-8 读取中文规则；若省略: Windows 默认编码可能导致断言不稳定
        self.assertIn("## Operating Principles", runtime_text)  # 新增代码+PromptContextV1: 断言行为原则分层存在；若省略: 工具规则缺少稳定行为基础
        self.assertIn("## 极简工具面", runtime_text)  # 修改代码+极简工具面: 断言四原子工具分层存在；若省略: 动态规则可能重新变成旧工具大全
        self.assertIn("## Skill 发现", runtime_text)  # 修改代码+极简工具面: 断言按需 skill 发现分层存在；若省略: 模型不知道读哪个索引文件
        self.assertIn("## Internal Capability Keyword Index", runtime_text)  # 修改代码+极简工具面: 断言旧能力关键词被压缩进内部索引；若省略: 按需规则可能丢失历史能力映射
        self.assertIn("Tool Policy v2", runtime_text)  # 修改代码+极简工具面: 断言工具策略作为内部机制被保留；若省略: 维护者难以理解权限和门禁仍然生效
    def test_runtime_instructions_define_prompt_surface_v2_rules(self) -> None:  # 新增代码+PromptSurfaceV2: 验证运行规则只聚焦真实会影响模型判断的提示词入口；若省略: 文档可能继续扩散成无关架构清单
        runtime_file = self._dynamic_prompt_file()  # 新增代码+PromptSurfaceV2: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到实际加载文件
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+PromptSurfaceV2: 读取 UTF-8 中文运行规则；若省略: Windows 默认编码可能导致中文断言失败
        self.assertIn("Prompt Surface Architecture v2", runtime_text)  # 新增代码+PromptSurfaceV2: 断言运行规则升级到 prompt surface v2；若省略: 旧 PromptContextV1 规则可能继续主导行为
        self.assertIn("按需读取", runtime_text)  # 修改代码+极简工具面: 断言动态规则不再每轮常驻；若省略: prompt surface v2 可能回退为长提示词
        self.assertIn("staticprompt/staticprompt.md", runtime_text)  # 修改代码+极简工具面: 断言静态提示词入口仍被动态规则点名；若省略: 用户难以分清静态和动态提示词边界
        self.assertIn("tool_list.md", runtime_text)  # 修改代码+极简工具面: 断言工具能力通过 skill 索引进入提示词表面；若省略: 模型可能不知道动态能力来源
        self.assertIn("真实 Chrome", runtime_text)  # 修改代码+极简工具面: 断言真实浏览器类硬约束仍保留关键词；若省略: 用户明确要求真实 Chrome 时可能被普通网页能力替代
    def test_runtime_instructions_mentions_ask_user_question(self) -> None:  # 新增代码+AskUserQuestion: 验证运行规则会引导模型使用结构化提问工具；若省略: 工具存在但模型可能继续随口追问或乱猜
        runtime_file = self._dynamic_prompt_file()  # 新增代码+AskUserQuestion: 定位真实 runtime_instructions.md；若省略: 测试可能检查不到用户实际运行规则
        runtime_text = runtime_file.read_text(encoding="utf-8")  # 新增代码+AskUserQuestion: 读取 UTF-8 中文运行规则；若省略: 中文断言可能受 Windows 默认编码影响
        self.assertIn("ask_user_question", runtime_text)  # 新增代码+AskUserQuestion: 断言规则提到 ask_user_question；若省略: 模型不知道何时调用结构化提问
        self.assertIn("结构化", runtime_text)  # 新增代码+AskUserQuestion: 断言规则说明结构化澄清用途；若省略: 只有工具名不足以指导触发时机
    def test_agent_can_append_memory_when_permission_is_allowed(self) -> None:  # 作用: 测试代理在允许时能把信息追加到持久记忆（memory.md）；若省略: 无法验证记忆持久化逻辑
        with tempfile.TemporaryDirectory() as raw_dir:  # 作用: 使用临时目录作为工作区，测试完成后自动清理；若省略: 可能留下记忆文件或互相干扰
            workspace = Path(raw_dir)  # 作用: 将临时路径转为 Path，便于后续文件操作
            model = ToolCallingFakeModel(  # 作用: 构造假模型，模拟模型请求把首选项追加到记忆的场景
                [
                    ModelMessage(
                        text="",
                        tool_calls=[ToolCall(name="append_memory", arguments={"text": "用户喜欢中文解释"})],  # 作用: 指示代理调用 `append_memory` 工具，并提供要写入的文本
                    ),
                    ModelMessage(text="我已经记住：用户喜欢中文解释。"),  # 作用: 模拟成功追加后的自然语言确认，用于断言代理对用户的反馈
                ]
            )
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 作用: 允许权限以便实际执行记忆追加
            answer = agent.run("请记住我的偏好")  # 作用: 触发代理流程，驱动模型请求并执行追加记忆的操作
            memory_text = (workspace / "memory.md").read_text(encoding="utf-8")  # 作用: 读取持久化的记忆文件以验证写入是否生效；若省略: 无法确认持久化
            self.assertIn("用户喜欢中文解释", memory_text)  # 作用: 验证记忆文件包含预期内容
            self.assertIn("记住", answer)  # 作用: 验证代理向用户返回了确认语句，提升用户体验


if __name__ == "__main__":  # Stage14: allow running this test module directly.
    unittest.main()  # Stage14: start unittest when executed as a script.


