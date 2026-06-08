import importlib  # 新增代码+ComputerDiscoverTool：导入动态模块加载工具；如果没有这一行，测试无法清楚验证 inventory 查询 API 是否存在。
import json  # 新增代码+ComputerDiscoverTool：导入 JSON 解析工具；如果没有这一行，agent 工具返回的结构化文本无法被稳定断言。
import tempfile  # 新增代码+ComputerDiscoverTool：导入临时目录工具；如果没有这一行，真实 agent 测试可能污染用户工作区。
import unittest  # 新增代码+ComputerDiscoverTool：导入 unittest 测试框架；如果没有这一行，本文件不会被测试运行器识别。
from pathlib import Path  # 新增代码+ComputerDiscoverTool：导入 Path 处理 Windows 路径；如果没有这一行，临时工作区路径拼接容易出错。

from learning_agent.core.agent import LearningAgent, ModelMessage, ToolCallingFakeModel  # 新增代码+ComputerDiscoverTool：导入真实 agent 和假模型；如果没有这一行，测试只能检查孤立函数而不能覆盖主工具路由。
from learning_agent.core.messages import ToolCall  # 新增代码+ComputerDiscoverTool：导入统一工具调用对象；如果没有这一行，测试无法走真实 _execute_tool 路径。
from learning_agent.tools.catalog import build_builtin_tool_catalog  # 新增代码+ComputerDiscoverTool：导入工具目录构建函数；如果没有这一行，测试无法确认 discover 是只读低风险工具。
from learning_agent.tools.executor import _builtin_tool_handlers  # 新增代码+ComputerDiscoverTool：导入执行器分发表；如果没有这一行，schema 空壳不会被测试发现。
from learning_agent.tools.schemas import TOOL_SCHEMAS  # 新增代码+ComputerDiscoverTool：导入模型可见工具 schema；如果没有这一行，测试无法确认模型能看到 discover 工具。


class WindowsComputerUseDiscoverToolPhase123Tests(unittest.TestCase):  # 新增代码+ComputerDiscoverTool：测试类开始，集中验证 Computer Use 应用发现工具；如果没有这个类，unittest 不会组织本阶段门禁。
    def _inventory_module(self):  # 新增代码+ComputerDiscoverTool：函数段开始，动态读取 Windows 应用清单模块；如果没有这段函数，模块缺失时失败信息不够友好。
        try:  # 新增代码+ComputerDiscoverTool：尝试导入正式 inventory 模块；如果没有这一行，红测不能证明 discover 复用统一应用清单。
            return importlib.import_module("learning_agent.computer_use.windows_app_inventory")  # 新增代码+ComputerDiscoverTool：返回被测 inventory 模块；如果没有这一行，后续测试拿不到查询函数。
        except ModuleNotFoundError as error:  # 新增代码+ComputerDiscoverTool：捕获模块不存在错误；如果没有这一行，用户会看到较难理解的导入堆栈。
            self.fail(f"windows_app_inventory module is missing: {error}")  # 新增代码+ComputerDiscoverTool：把缺失模块转成明确测试失败；如果没有这一行，排查目标不清楚。
    # 新增代码+ComputerDiscoverTool：函数段结束，_inventory_module 到此结束；如果没有这个边界说明，用户不容易看出动态导入范围。

    def test_computer_discover_is_visible_read_only_and_routed(self) -> None:  # 新增代码+ComputerDiscoverTool：函数段开始，验证工具 schema、catalog 和 executor 三层接线；如果没有这段测试，discover 可能只加了一半。
        schemas_by_name = {schema.get("function", {}).get("name", ""): schema for schema in TOOL_SCHEMAS if isinstance(schema.get("function", {}), dict)}  # 新增代码+ComputerDiscoverTool：把 schema 按工具名索引；如果没有这一行，后续断言需要重复遍历。
        self.assertIn("computer_discover", schemas_by_name)  # 新增代码+ComputerDiscoverTool：断言模型可见 discover 工具；如果没有这一行，模型主循环仍无法主动发现应用清单。
        discover_schema = schemas_by_name["computer_discover"]["function"]["parameters"]["properties"]  # 新增代码+ComputerDiscoverTool：取出 discover 参数定义；如果没有这一行，测试无法确认 query/max_results 暴露给模型。
        self.assertIn("query", discover_schema)  # 新增代码+ComputerDiscoverTool：断言工具允许自然语言应用查询；如果没有这一行，模型只能拿全量清单难以选择。
        self.assertIn("max_results", discover_schema)  # 新增代码+ComputerDiscoverTool：断言工具允许限制候选数量；如果没有这一行，大清单容易污染上下文。
        catalog = {tool.name: tool for tool in build_builtin_tool_catalog()}  # 新增代码+ComputerDiscoverTool：构建正式工具目录；如果没有这一行，无法验证风险元数据。
        self.assertIn("computer_discover", catalog)  # 新增代码+ComputerDiscoverTool：断言目录包含 discover；如果没有这一行，tool_search/select 可能找不到它。
        self.assertEqual(catalog["computer_discover"].capability_pack, "computer_use")  # 新增代码+ComputerDiscoverTool：断言 discover 随 Computer Use 能力包加载；如果没有这一行，/computer use --full 后模型仍看不到它。
        self.assertEqual(catalog["computer_discover"].risk_level, "low")  # 新增代码+ComputerDiscoverTool：断言 discover 是低风险只读工具；如果没有这一行，它可能被误走高风险桌面权限。
        self.assertTrue(catalog["computer_discover"].is_read_only)  # 新增代码+ComputerDiscoverTool：断言 discover 不改变桌面；如果没有这一行，权限层可能不敢自动允许应用查询。
        self.assertTrue(catalog["computer_discover"].is_concurrency_safe)  # 新增代码+ComputerDiscoverTool：断言 discover 可并发读取；如果没有这一行，大任务中只读发现会被无谓串行。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+ComputerDiscoverTool：创建临时 agent 工作区；如果没有这一行，测试可能把事件文件写到真实项目目录。
            agent = LearningAgent(ToolCallingFakeModel([ModelMessage(text="unused")]), Path(temp_dir), ask_permission=lambda _reason: True, debug_enabled=False)  # 新增代码+ComputerDiscoverTool：创建真实 agent 且自动授权；如果没有这一行，无法验证 executor handler 是否能绑定真实方法。
            handlers = _builtin_tool_handlers(agent)  # 新增代码+ComputerDiscoverTool：读取真实内置工具分发表；如果没有这一行，schema 空壳不会被发现。
        self.assertIn("computer_discover", handlers)  # 新增代码+ComputerDiscoverTool：断言执行器能路由 discover；如果没有这一行，模型调用工具会变成未知工具。
    # 新增代码+ComputerDiscoverTool：函数段结束，test_computer_discover_is_visible_read_only_and_routed 到此结束；如果没有这个边界说明，用户不容易看出接线测试范围。

    def test_inventory_query_returns_ranked_app_candidates_without_paths(self) -> None:  # 新增代码+ComputerDiscoverTool：函数段开始，验证统一 inventory 能按查询返回排序候选；如果没有这段测试，discover 可能退回硬编码 app 名。
        module = self._inventory_module()  # 新增代码+ComputerDiscoverTool：读取被测 inventory 模块；如果没有这一行，测试无法调用查询 API。
        report = module.query_windows_app_inventory("画图", candidates=[  # 新增代码+ComputerDiscoverTool：用中文真实习惯查询画图候选；如果没有这一行，测试无法覆盖中文自然语言入口。
            {"display_name": "Obsidian", "app_name": "Obsidian", "launch_id": "C:/Users/demo/Obsidian.lnk", "source": "start_menu", "launch_kind": "exe"},  # 新增代码+ComputerDiscoverTool：模拟无关普通应用；如果没有这一行，排序测试无法证明 Paint 被排到前面。
            {"display_name": "Paint", "app_name": "mspaint", "launch_id": "C:/Users/demo/Paint.lnk", "source": "start_menu", "launch_kind": "exe", "aliases": ("画图", "画图软件", "paint", "mspaint")},  # 新增代码+ComputerDiscoverTool：模拟 Paint 候选和中文别名；如果没有这一行，中文查询没有稳定命中对象。
        ], include_common=False, max_count=5)  # 新增代码+ComputerDiscoverTool：关闭公共兜底并限制返回数量；如果没有这一行，测试会受本机真实应用环境影响。
        self.assertTrue(report["ok"])  # 新增代码+ComputerDiscoverTool：断言查询成功；如果没有这一行，后续候选断言可能在错误报告上误通过。
        self.assertEqual(report["tool"], "computer_discover")  # 新增代码+ComputerDiscoverTool：断言报告归属 discover 工具；如果没有这一行，模型难以区分普通状态和应用发现结果。
        self.assertEqual(report["query"], "画图")  # 新增代码+ComputerDiscoverTool：断言保留用户查询文本；如果没有这一行，调试时难以知道模型查了什么。
        self.assertEqual(report["candidates"][0]["app_name"], "mspaint")  # 新增代码+ComputerDiscoverTool：断言中文查询首选 Paint 的稳定 app_name；如果没有这一行，launch_app 仍可能收到中文句子。
        self.assertEqual(report["candidates"][0]["launch_kind"], "exe")  # 新增代码+ComputerDiscoverTool：断言启动类型进入结果；如果没有这一行，后续 resolver 不知道该用哪个后端。
        self.assertNotIn("C:/Users/demo/Paint.lnk", json.dumps(report, ensure_ascii=False))  # 新增代码+ComputerDiscoverTool：断言原始路径不会泄露给模型；如果没有这一行，用户本机路径可能进入上下文。
    # 新增代码+ComputerDiscoverTool：函数段结束，test_inventory_query_returns_ranked_app_candidates_without_paths 到此结束；如果没有这个边界说明，用户不容易看出查询测试范围。

    def test_agent_executes_computer_discover_through_real_tool_path(self) -> None:  # 新增代码+ComputerDiscoverTool：函数段开始，验证 agent 可以真实执行 discover 工具；如果没有这段测试，工具可能只在模块层能用。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+ComputerDiscoverTool：创建临时 agent 工作区；如果没有这一行，测试会污染真实 workspace。
            agent = LearningAgent(ToolCallingFakeModel([ModelMessage(text="unused")]), Path(temp_dir), ask_permission=lambda _reason: True, debug_enabled=False)  # 新增代码+ComputerDiscoverTool：创建真实 agent；如果没有这一行，无法覆盖 _execute_tool 到 handler 的完整路径。
            agent.loaded_tool_names.add("computer_discover")  # 新增代码+ComputerDiscoverTool：模拟 Computer Use 能力包已加载；如果没有这一行，延迟工具策略可能阻断执行。
            output = agent._execute_tool(ToolCall(name="computer_discover", arguments={"query": "画图", "max_results": 8}))  # 新增代码+ComputerDiscoverTool：通过正式工具入口查询画图；如果没有这一行，测试无法证明模型调用时能得到结果。
        report = json.loads(output)  # 新增代码+ComputerDiscoverTool：解析工具返回 JSON；如果没有这一行，断言只能做脆弱字符串匹配。
        self.assertTrue(report["ok"])  # 新增代码+ComputerDiscoverTool：断言工具执行成功；如果没有这一行，错误文本可能被误当成普通输出。
        self.assertEqual(report["tool"], "computer_discover")  # 新增代码+ComputerDiscoverTool：断言返回来自 discover 工具；如果没有这一行，兼容入口可能混淆工具结果。
        self.assertGreaterEqual(report["result_count"], 1)  # 新增代码+ComputerDiscoverTool：断言至少返回一个候选；如果没有这一行，模型还是没有可选应用清单。
        self.assertTrue(any(candidate.get("app_name") == "mspaint" for candidate in report["candidates"]))  # 新增代码+ComputerDiscoverTool：断言真实工具路径能给出 Paint app_name；如果没有这一行，画图任务仍可能靠猜测启动。
        self.assertTrue(report["not_hard_whitelist"])  # 新增代码+ComputerDiscoverTool：断言 discover 是建议清单不是限制清单；如果没有这一行，设计可能重新变成硬白名单。
    # 新增代码+ComputerDiscoverTool：函数段结束，test_agent_executes_computer_discover_through_real_tool_path 到此结束；如果没有这个边界说明，用户不容易看出 agent 工具路径测试范围。

    def test_full_mode_discovery_only_prompt_keeps_discover_in_first_model_turn(self) -> None:  # 新增代码+ComputerDiscoverTool：函数段开始，验证只查 app_name 时首轮工具面包含 discover；如果没有这段测试，真实终端会再次只给模型 computer_action。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+ComputerDiscoverTool：创建临时 agent 工作区；如果没有这一行，测试可能污染真实 workspace。
            agent = LearningAgent(ToolCallingFakeModel([ModelMessage(text="unused")]), Path(temp_dir), ask_permission=lambda _reason: True, debug_enabled=False)  # 新增代码+ComputerDiscoverTool：创建真实 agent；如果没有这一行，无法覆盖 harness 和工具收窄的真实方法。
            agent.loaded_tool_names.update({"computer_use", "computer_observe", "computer_discover", "computer_action"})  # 新增代码+ComputerDiscoverTool：模拟 /computer use --full 已加载四个核心工具；如果没有这一行，harness 会按半加载状态跳过。
            agent.desktop_task_context = {"active": True, "requires_gui_actions": True, "target_app_hint": "画图", "task_goal": "discover_local_app"}  # 新增代码+ComputerDiscoverTool：模拟本机应用发现任务上下文；如果没有这一行，full harness 不会启用。
            harness = agent._build_computer_use_full_model_loop_harness_message("请先帮我查找本机画图软件是否可用，并告诉我应该使用哪个 app_name，不要打开或操作软件。")  # 新增代码+ComputerDiscoverTool：构造真实发现类自然语言提示；如果没有这一行，无法复现真实终端失败路径。
            scoped_tools = agent._scoped_tool_schemas_for_model_turn(TOOL_SCHEMAS, 0)  # 新增代码+ComputerDiscoverTool：读取第 0 轮模型可见工具；如果没有这一行，测试无法证明 discover 留在主循环工具面。
        scoped_names = {schema.get("function", {}).get("name", "") for schema in scoped_tools if isinstance(schema.get("function", {}), dict)}  # 新增代码+ComputerDiscoverTool：按工具名索引收窄结果；如果没有这一行，断言需要重复遍历。
        self.assertIn("必须先调用 `computer_discover`", harness)  # 新增代码+ComputerDiscoverTool：断言 harness 明确要求发现类任务调用工具；如果没有这一行，模型可能再次直接回答。
        self.assertNotIn("Available desktop application candidates", harness)  # 新增代码+ComputerDiscoverTool：断言发现类任务不直接注入完整候选清单；如果没有这一行，模型会继续跳过 computer_discover。
        self.assertTrue(agent.desktop_task_context.get("discovery_only"))  # 新增代码+ComputerDiscoverTool：断言 discovery-only 状态写入上下文；如果没有这一行，工具收窄层不知道不要启动软件。
        self.assertIn("computer_discover", scoped_names)  # 新增代码+ComputerDiscoverTool：断言第 0 轮模型能看到 discover；如果没有这一行，真实终端无法调用发现工具。
        self.assertIn("computer_action", scoped_names)  # 新增代码+ComputerDiscoverTool：断言第 0 轮仍保留启动工具给非发现类路径；如果没有这一行，普通本机应用任务会失去启动能力。
    # 新增代码+ComputerDiscoverTool：函数段结束，test_full_mode_discovery_only_prompt_keeps_discover_in_first_model_turn 到此结束；如果没有这个边界说明，用户不容易看出真实终端回归范围。


if __name__ == "__main__":  # 新增代码+ComputerDiscoverTool：文件入口开始，允许直接运行本测试文件；如果没有这一行，初学者必须记完整 unittest 模块名。
    unittest.main()  # 新增代码+ComputerDiscoverTool：启动 unittest；如果没有这一行，直接执行测试文件不会运行断言。
# 新增代码+ComputerDiscoverTool：文件入口结束，直接运行测试到此结束；如果没有这个边界说明，用户不容易看出入口范围。
