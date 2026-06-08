import json  # 新增代码+Phase49ComputerUseToolSurface: 导入 JSON 工具用于读取验收场景；如果没有这行代码，测试无法确认场景 token 是否稳定。
import tempfile  # 新增代码+Phase49ComputerUseToolSurface: 导入临时目录工具隔离真实 agent 工作区；如果没有这行代码，执行器测试可能污染项目文件。
import unittest  # 新增代码+Phase49ComputerUseToolSurface: 导入 unittest 框架承载 Phase49 测试；如果没有这行代码，自动化命令无法发现这些断言。
from pathlib import Path  # 新增代码+Phase49ComputerUseToolSurface: 导入 Path 便于稳定定位项目和临时目录；如果没有这行代码，路径拼接会变脆弱。

from learning_agent.computer_use.controller import ComputerUseController, MemoryComputerUseBackend  # 新增代码+Phase49ComputerUseToolSurface: 导入同一 Computer Use 控制器和内存后端；如果没有这行代码，无法证明兼容工具没有绕过 controller。
from learning_agent.computer_use.tool_surface import PHASE49_COMPUTER_USE_TOOL_SURFACE_MARKER, PHASE49_COMPUTER_USE_TOOL_SURFACE_OK_TOKEN, phase49_cli_line, run_phase49_tool_surface_contract  # 新增代码+Phase49ComputerUseToolSurface: 导入 Phase49 预期新增的兼容工具面模块；如果没有这行代码，红测会证明适配层尚未实现。
from learning_agent.core.agent import LearningAgent, ToolCallingFakeModel  # 新增代码+Phase49ComputerUseToolSurface: 导入真实 agent 和假模型；如果没有这行代码，测试无法覆盖 executor 到 agent 的真实路由。
from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+Phase49ComputerUseToolSurface: 导入统一消息和工具调用对象；如果没有这行代码，测试无法构造真实工具调用。
from learning_agent.tools.catalog import build_builtin_tool_catalog  # 新增代码+Phase49ComputerUseToolSurface: 导入工具目录构建入口；如果没有这行代码，测试无法检查工具风险元数据。
from learning_agent.tools.schemas import TOOL_SCHEMAS  # 新增代码+Phase49ComputerUseToolSurface: 导入内置工具 schema；如果没有这行代码，测试无法确认兼容工具暴露给模型。


class WindowsComputerUseToolSurfacePhase49Tests(unittest.TestCase):  # 新增代码+Phase49ComputerUseToolSurface: 类段开始，集中验证 ClaudeCode 风格 Computer Use 兼容工具面；如果没有这个类，unittest 不会组织 Phase49 验收。
    def _safe_window(self) -> dict[str, object]:  # 新增代码+Phase49ComputerUseToolSurface: 函数段开始，提供安全窗口样本；如果没有这段函数，多处测试会重复构造窗口引用。
        return {"app_id": "notepad", "window_id": "win-49", "title_preview": "Phase49 Notepad", "rect": {"left": 10, "top": 20, "right": 300, "bottom": 240}}  # 新增代码+Phase49ComputerUseToolSurface: 返回带 app/window 身份的测试窗口；如果没有这行代码，observe/action 路由没有可信目标。
    # 新增代码+Phase49ComputerUseToolSurface: 函数段结束，_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口样本范围。

    def test_schema_exposes_compatibility_tools_without_removing_existing_tools(self) -> None:  # 新增代码+Phase49ComputerUseToolSurface: 函数段开始，验证 schema 同时保留旧工具和新增兼容工具；如果没有这个测试，兼容层可能破坏原工具名。
        schemas_by_name = {schema["function"]["name"]: schema for schema in TOOL_SCHEMAS}  # 新增代码+Phase49ComputerUseToolSurface: 按工具名索引 schema；如果没有这行代码，后续断言无法快速定位工具。
        self.assertIn("computer_status", schemas_by_name)  # 新增代码+Phase49ComputerUseToolSurface: 断言旧状态工具仍存在；如果没有这行代码，Phase49 可能误删现有入口。
        self.assertIn("computer_observe", schemas_by_name)  # 新增代码+Phase49ComputerUseToolSurface: 断言旧观察工具仍存在；如果没有这行代码，只读观察可能被兼容工具取代。
        self.assertIn("computer_action", schemas_by_name)  # 新增代码+Phase49ComputerUseToolSurface: 断言旧动作工具仍存在；如果没有这行代码，高风险动作入口可能被重命名破坏。
        self.assertIn("computer_use", schemas_by_name)  # 新增代码+Phase49ComputerUseToolSurface: 断言 OpenAI 友好的兼容工具名存在；如果没有这行代码，模型无法使用统一 computer_use 入口。
        self.assertIn("computer-use", schemas_by_name)  # 新增代码+Phase49ComputerUseToolSurface: 断言 ClaudeCode 风格连字符兼容名存在；如果没有这行代码，来自 ClaudeCode 习惯的 tool 名无法被兼容。
        compat_parameters = schemas_by_name["computer_use"]["function"]["parameters"]  # 新增代码+Phase49ComputerUseToolSurface: 读取兼容工具参数 schema；如果没有这行代码，无法检查 operation 规范。
        self.assertEqual(compat_parameters["properties"]["operation"]["enum"], ["status", "observe", "action", "mode", "run_prompt"])  # 修改代码+Phase92UniversalComputerUse：断言统一入口保留旧三类操作并新增通用 mode；如果没有这行代码，schema 可能漏掉 prompt 驱动的 Computer Use 入口。
        self.assertIn("prompt", compat_parameters["properties"])  # 新增代码+Phase92UniversalComputerUse：断言 schema 暴露 mode prompt 字段；如果没有这行代码，模型无法传入自然语言任务。
        self.assertIn("real_actions", compat_parameters["properties"])  # 新增代码+Phase92UniversalComputerUse：断言 schema 暴露真实动作开关；如果没有这行代码，模型不清楚 mode 默认不会真实控制桌面。
    # 新增代码+Phase49ComputerUseToolSurface: 函数段结束，test_schema_exposes_compatibility_tools_without_removing_existing_tools 到此结束；如果没有这个边界说明，读者不容易看出 schema 测试范围。

    def test_catalog_marks_compatibility_aliases_as_same_computer_use_pack_and_high_risk(self) -> None:  # 新增代码+Phase49ComputerUseToolSurface: 函数段开始，验证兼容工具风险元数据；如果没有这个测试，统一工具可能被误标为只读低风险。
        catalog = {tool.name: tool for tool in build_builtin_tool_catalog()}  # 新增代码+Phase49ComputerUseToolSurface: 构建并索引内置工具目录；如果没有这行代码，无法读取 AgentTool 元数据。
        for tool_name in ("computer_use", "computer-use"):  # 新增代码+Phase49ComputerUseToolSurface: 同时检查下划线和连字符兼容名；如果没有这行代码，某个别名可能漏配置。
            tool = catalog[tool_name]  # 新增代码+Phase49ComputerUseToolSurface: 取出目标兼容工具；如果没有这行代码，后续断言没有对象。
            self.assertEqual(tool.capability_pack, "computer_use")  # 新增代码+Phase49ComputerUseToolSurface: 断言兼容工具属于 Computer Use 能力包；如果没有这行代码，读取 skill 后不会一起加载。
            self.assertEqual(tool.risk_level, "high")  # 新增代码+Phase49ComputerUseToolSurface: 断言统一入口因可能执行 action 而高风险；如果没有这行代码，动作路径可能自动放行。
            self.assertFalse(tool.is_read_only)  # 新增代码+Phase49ComputerUseToolSurface: 断言统一入口不能整体标只读；如果没有这行代码，action operation 会被只读权限误覆盖。
            self.assertFalse(tool.is_concurrency_safe)  # 新增代码+Phase49ComputerUseToolSurface: 断言统一入口不能并发执行；如果没有这行代码，桌面动作可能乱序。
            self.assertTrue(tool.requires_user_interaction)  # 新增代码+Phase49ComputerUseToolSurface: 断言统一入口需要交互风险提示；如果没有这行代码，用户可能不知道它能控制桌面。
    # 新增代码+Phase49ComputerUseToolSurface: 函数段结束，test_catalog_marks_compatibility_aliases_as_same_computer_use_pack_and_high_risk 到此结束；如果没有这个边界说明，读者不容易看出 catalog 测试范围。

    def test_compatibility_tools_route_observe_and_action_through_same_controller(self) -> None:  # 新增代码+Phase49ComputerUseToolSurface: 函数段开始，验证兼容工具实际复用同一 controller；如果没有这个测试，schema 可能只是空壳。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase49ComputerUseToolSurface: 创建临时 workspace；如果没有这行代码，真实 agent 初始化会污染项目目录。
            workspace = Path(raw_dir)  # 新增代码+Phase49ComputerUseToolSurface: 转成 Path 供 agent 使用；如果没有这行代码，路径处理不够稳定。
            backend = MemoryComputerUseBackend(windows=[self._safe_window()])  # 新增代码+Phase49ComputerUseToolSurface: 创建安全内存后端；如果没有这行代码，测试可能触碰真实桌面。
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="unused")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+Phase49ComputerUseToolSurface: 创建真实 agent 且权限自动允许；如果没有这行代码，无法覆盖 executor 路由。
            agent.computer_use_controller = ComputerUseController(backend=backend)  # 新增代码+Phase49ComputerUseToolSurface: 注入同一 controller；如果没有这行代码，兼容工具无法证明走的是生产控制器边界。
            agent.loaded_tool_names.update({"computer_use", "computer-use"})  # 新增代码+Phase49ComputerUseToolSurface: 标记兼容工具已被加载以绕过 deferred 可见性门；如果没有这行代码，测试会失败在工具池加载而不是路由能力。
            observe_output = agent._execute_tool(ToolCall(name="computer_use", arguments={"operation": "observe", "action": "list_windows"}))  # 新增代码+Phase49ComputerUseToolSurface: 通过下划线兼容工具执行只读观察；如果没有这行代码，无法证明 observe 转发。
            action_output = agent._execute_tool(ToolCall(name="computer-use", arguments={"operation": "action", "action": "click", "confirm_desktop_control": True, "window": self._safe_window(), "x": 5, "y": 6}))  # 新增代码+Phase49ComputerUseToolSurface: 通过连字符兼容工具执行安全内存动作；如果没有这行代码，无法证明 action 转发。
        self.assertIn("computer_observe", observe_output)  # 新增代码+Phase49ComputerUseToolSurface: 断言兼容 observe 返回旧工具名文本；如果没有这行代码，转发可能没有复用旧入口。
        self.assertIn("win-49", observe_output)  # 新增代码+Phase49ComputerUseToolSurface: 断言观察返回内存窗口；如果没有这行代码，controller 后端可能没有被调用。
        self.assertIn("computer_action", action_output)  # 新增代码+Phase49ComputerUseToolSurface: 断言兼容 action 返回旧动作工具文本；如果没有这行代码，转发可能走了新旁路。
        self.assertEqual(len(backend.actions), 1)  # 新增代码+Phase49ComputerUseToolSurface: 断言同一内存后端记录一次动作；如果没有这行代码，无法证明请求到达 controller 后端。
        self.assertEqual(backend.actions[0]["action"], "click")  # 新增代码+Phase49ComputerUseToolSurface: 断言后端收到的是规范化 click 动作；如果没有这行代码，适配层可能改坏 action 参数。
    # 新增代码+Phase49ComputerUseToolSurface: 函数段结束，test_compatibility_tools_route_observe_and_action_through_same_controller 到此结束；如果没有这个边界说明，读者不容易看出执行路由测试范围。

    def test_phase49_cli_contract_and_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase49ComputerUseToolSurface: 函数段开始，验证 CLI 合同和验收场景 token；如果没有这个测试，真实验收可能缺少稳定证据。
        report = run_phase49_tool_surface_contract()  # 新增代码+Phase49ComputerUseToolSurface: 运行 Phase49 无副作用合同自检；如果没有这行代码，CLI token 没有报告来源。
        line = phase49_cli_line(report)  # 新增代码+Phase49ComputerUseToolSurface: 生成稳定单行 CLI 输出；如果没有这行代码，验收器需要解析完整 JSON。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase49ComputerUseToolSurface: 定位项目根目录；如果没有这行代码，场景文件路径会依赖当前工作目录。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase49_windows_tool_surface.json"  # 新增代码+Phase49ComputerUseToolSurface: 定位 Phase49 验收场景；如果没有这行代码，测试无法确认场景包含新 token。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase49ComputerUseToolSurface: 读取并解析验收场景；如果没有这行代码，场景 token 漏写不会被发现。
        expected_tokens = {PHASE49_COMPUTER_USE_TOOL_SURFACE_MARKER, PHASE49_COMPUTER_USE_TOOL_SURFACE_OK_TOKEN, "legacy_tools=true", "compat_tools=true", "same_controller=true", "catalog=true", "actions_expanded=false"}  # 新增代码+Phase49ComputerUseToolSurface: 列出 Phase49 必须稳定输出的 token；如果没有这行代码，成功标准会散落在多个断言里。
        self.assertIn(PHASE49_COMPUTER_USE_TOOL_SURFACE_MARKER, line)  # 新增代码+Phase49ComputerUseToolSurface: 断言 CLI 行包含 ready marker；如果没有这行代码，阶段完成信号可能缺失。
        self.assertTrue(report["legacy_tools"])  # 新增代码+Phase49ComputerUseToolSurface: 断言旧工具仍保留；如果没有这行代码，兼容层可能破坏现有接口。
        self.assertTrue(report["compat_tools"])  # 新增代码+Phase49ComputerUseToolSurface: 断言兼容工具暴露；如果没有这行代码，Phase49 工具面没有新增能力。
        for token in expected_tokens:  # 新增代码+Phase49ComputerUseToolSurface: 遍历所有场景 token；如果没有这行代码，场景断言可能漏项。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase49ComputerUseToolSurface: 断言 debug log 检查包含 token；如果没有这行代码，调试日志证据可能缺失。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase49ComputerUseToolSurface: 断言最终回答检查包含 token；如果没有这行代码，用户可见回答可能缺少证据。
    # 新增代码+Phase49ComputerUseToolSurface: 函数段结束，test_phase49_cli_contract_and_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，读者不容易看出 CLI/场景测试范围。


if __name__ == "__main__":  # 新增代码+Phase49ComputerUseToolSurface: 允许直接运行本测试文件；如果没有这行代码，初学者无法用 python 文件方式单独验证 Phase49。
    unittest.main()  # 新增代码+Phase49ComputerUseToolSurface: 启动 unittest 主入口；如果没有这行代码，直接运行测试文件不会执行任何断言。
