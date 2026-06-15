"""Computer Use ClaudeCode 风格工具池作用域测试。"""  # 新增代码+ComputerUseToolScopeTests: 说明本测试锁住 Computer Use 工具暴露边界；如果没有这一行，后续读测试时不清楚它验证的是顶层设计。
from __future__ import annotations  # 新增代码+ComputerUseToolScopeTests: 延迟解析类型注解；如果没有这一行，测试导入顺序可能更脆弱。

import json  # 新增代码+ComputerUseToolScopeTests: 用于解析 debug 工具返回的 JSON；如果没有这一行，测试只能做脆弱字符串断言。
import tempfile  # 新增代码+ComputerUseToolScopeTests: 用临时目录隔离 LearningAgent 工作区；如果没有这一行，测试会污染真实项目文件。
import unittest  # 新增代码+ComputerUseToolScopeTests: 使用标准 unittest 框架；如果没有这一行，测试类无法被发现和运行。
from collections import Counter  # 新增代码+ComputerUseNoDuplicateSurface: 用计数器找出同名工具重复暴露；如果没有这一行，测试只能用 set 而看不见重复 schema。
from pathlib import Path  # 新增代码+ComputerUseToolScopeTests: 用 Path 传入 agent workspace；如果没有这一行，路径处理不稳定。

from learning_agent.app.interactive import _activate_computer_use_tool_pack_for_agent  # 新增代码+ComputerUseTerminalScopeSyncTest：导入真实终端 use/stop 后的工具池同步入口；如果没有这一行，测试无法覆盖可见终端失败的根因路径。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import computer_use_mcp_tools  # 修改代码+ComputerUseMcpV2LegacyBlock：复用 v2 独立 Computer Use MCP schema；如果没有这一行，测试会继续依赖准备删除的旧 computer_use 包。
from learning_agent.computer_use_mcp_v2.windows_runtime.model_loop import scoped_tool_schemas_for_model_turn  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix：导入模型轮次工具面过滤函数；如果没有这一行，测试无法直接复现真实主循环把 observe/left_click 缩没的 bug。
from learning_agent.core.agent import LearningAgent, ModelMessage, ToolCallingFakeModel  # 新增代码+ComputerUseToolScopeTests: 创建真实 agent 和假模型；如果没有这一行，工具池测试只能测孤立函数。
from learning_agent.core.messages import ToolCall  # 新增代码+ComputerUseToolScopeTests: 构造真实工具调用对象；如果没有这一行，执行层守卫无法用生产入口测试。
from learning_agent.mcp.runtime import McpToolRegistry  # 新增代码+ComputerUseToolScopeTests: 用真实 MCP registry 包装 fake client；如果没有这一行，MCP 前缀命名路径不会被覆盖。
from learning_agent.tools import catalog_runtime as catalog_runtime_from_tools  # 新增代码+ComputerUseToolScopeTests: 读取当前模型可见工具 schema；如果没有这一行，无法验证最终工具池。
from learning_agent.tools import search as search_tools_from_tools  # 新增代码+ComputerUseToolScopeTests: 直接调用 tool_search 实现检查发现层过滤；如果没有这一行，搜索泄漏不会被测试覆盖。


OPERATION_RAW_TOOL_NAMES: set[str] = {  # 新增代码+ComputerUseToolScopeTests: 声明操作/debug 模式应自动暴露的原始 MCP 工具名；如果没有这一行，断言会散落难维护。
    "request_access",  # 新增代码+ComputerUseToolScopeTests: 授权申请工具必须在 Computer Use 模式可见；如果没有这一项，模型无法先申请桌面权限。
    "list_granted_applications",  # 新增代码+ComputerUseToolScopeTests: 授权查询工具必须可见；如果没有这一项，模型无法确认权限状态。
    "observe",  # 新增代码+ComputerUseToolScopeTests: ClaudeCode 风格观察别名必须可见；如果没有这一项，模型只能用旧 screenshot。
    "screenshot",  # 新增代码+ComputerUseToolScopeTests: 截图工具必须可见；如果没有这一项，模型无法看屏幕。
    "cursor_position",  # 新增代码+ComputerUseToolScopeTests: 光标位置工具必须可见；如果没有这一项，模型无法查询鼠标坐标。
    "mouse_move",  # 新增代码+ComputerUseToolScopeTests: 鼠标移动工具必须可见；如果没有这一项，模型无法移动鼠标。
    "left_click",  # 新增代码+ComputerUseToolScopeTests: 新左键工具必须可见；如果没有这一项，模型会退回旧 click。
    "double_click",  # 新增代码+ComputerUseToolScopeTests: 双击工具必须可见；如果没有这一项，桌面任务缺常见动作。
    "right_click",  # 新增代码+ComputerUseToolScopeTests: 右键工具必须可见；如果没有这一项，上下文菜单任务无法执行。
    "type",  # 新增代码+ComputerUseToolScopeTests: 文本输入工具必须可见；如果没有这一项，浏览器/Office 输入无法执行。
    "key",  # 新增代码+ComputerUseToolScopeTests: 按键工具必须可见；如果没有这一项，快捷键和回车无法执行。
    "scroll",  # 新增代码+ComputerUseToolScopeTests: 滚动工具必须可见；如果没有这一项，网页和文档滚动无法执行。
    "wait",  # 新增代码+ComputerUseToolScopeTests: 等待工具必须可见；如果没有这一项，界面加载无法等待。
    "read_clipboard",  # 新增代码+ComputerUseToolScopeTests: 读剪贴板工具必须可见；如果没有这一项，复制检查无法执行。
    "write_clipboard",  # 新增代码+ComputerUseToolScopeTests: 写剪贴板工具必须可见；如果没有这一项，粘贴文本路线不完整。
    "open_application",  # 新增代码+ComputerUseToolScopeTests: 打开应用工具必须可见；如果没有这一项，agent-owned 启动链路会断。
    "computer_batch",  # 新增代码+ComputerUseToolScopeTests: 批量工具必须可见；如果没有这一项，多步桌面动作无法合并。
}  # 新增代码+ComputerUseToolScopeTests: 操作工具名集合结束；如果没有这一行，Python 集合语法不完整。


class ComputerUseToolScopeTests(unittest.TestCase):  # 新增代码+ComputerUseToolScopeTests: 定义工具作用域测试类；如果没有这一段，unittest 不会发现这些测试。
    # 新增代码+ComputerUseToolScopeTests: 函数段开始，_build_agent 创建带 fake computer-use MCP 的真实 agent；如果没有这段函数，每个测试会重复初始化逻辑。
    def _build_agent(self, workspace: Path, mode: str) -> LearningAgent:  # 新增代码+ComputerUseToolScopeTests: 声明 agent 构造 helper；如果没有这一行，测试无法统一设置工具作用域。
        registry = McpToolRegistry({"computer-use": _FakeMcpClient(computer_use_mcp_tools())})  # 新增代码+ComputerUseToolScopeTests: 用 fake client 注入真实 Computer Use MCP schema；如果没有这一行，测试不会覆盖 mcp__computer-use__ 前缀。
        agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="ok")]), workspace=workspace, ask_permission=lambda action: True, mcp_tool_registry=registry, debug_enabled=False)  # 新增代码+ComputerUseToolScopeTests: 创建真实 agent 并允许启动 fake MCP；如果没有这一行，catalog_runtime 没有执行主体。
        agent.tool_scope_mode = mode  # 新增代码+ComputerUseToolScopeTests: 强制当前测试使用指定工具模式；如果没有这一行，auto 模式会依赖自然语言桌面分类。
        agent._tool_catalog_cache = None  # 新增代码+ComputerUseToolScopeTests: 清空目录缓存让 mode/MCP schema 变化即时生效；如果没有这一行，前一次 catalog 可能污染当前断言。
        return agent  # 新增代码+ComputerUseToolScopeTests: 返回准备好的 agent；如果没有这一行，调用方拿不到测试对象。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，_build_agent 到此结束；如果没有这个边界说明，用户不容易看出测试夹具范围。

    # 新增代码+ComputerUseToolScopeTests: 函数段开始，_tool_names 读取模型本轮可见工具名；如果没有这段函数，测试会重复 schema 解析。
    def _tool_names(self, agent: LearningAgent) -> set[str]:  # 新增代码+ComputerUseToolScopeTests: 声明可见工具名 helper；如果没有这一行，断言需要重复调用 catalog_runtime。
        schemas = catalog_runtime_from_tools.available_tool_schemas(agent)  # 新增代码+ComputerUseToolScopeTests: 读取当前真实工具池 schema；如果没有这一行，测试只是在看静态常量。
        return set(catalog_runtime_from_tools.tool_schema_names(agent, schemas))  # 新增代码+ComputerUseToolScopeTests: 提取工具名集合；如果没有这一行，后续集合断言无法运行。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，_tool_names 到此结束；如果没有这个边界说明，用户不容易看出工具名读取范围。

    # 新增代码+ComputerUseNoDuplicateSurface: 函数段开始，_tool_name_list 保留重复工具名；如果没有这段函数，重复暴露会被 set 静默吞掉。
    def _tool_name_list(self, agent: LearningAgent) -> list[str]:  # 新增代码+ComputerUseNoDuplicateSurface: 声明可见工具名列表 helper；如果没有这一行，测试无法判断同名工具出现几次。
        schemas = catalog_runtime_from_tools.available_tool_schemas(agent)  # 新增代码+ComputerUseNoDuplicateSurface: 读取当前真实工具 schema 列表；如果没有这一行，重复检查没有生产数据来源。
        return catalog_runtime_from_tools.tool_schema_names(agent, schemas)  # 新增代码+ComputerUseNoDuplicateSurface: 返回未去重名称列表；如果没有这一行，重复 request_access 不会被发现。
    # 新增代码+ComputerUseNoDuplicateSurface: 函数段结束，_tool_name_list 到此结束；如果没有这个边界说明，用户不容易看出它和 _tool_names 的区别。

    # 新增代码+ComputerUseNoDuplicateSurface: 函数段开始，_duplicate_tool_names 找出重复模型工具名；如果没有这段函数，每个模式测试都要重复计数逻辑。
    def _duplicate_tool_names(self, agent: LearningAgent) -> list[str]:  # 新增代码+ComputerUseNoDuplicateSurface: 声明重复名称检测 helper；如果没有这一行，测试无法输出清楚的重复工具名。
        counts = Counter(self._tool_name_list(agent))  # 新增代码+ComputerUseNoDuplicateSurface: 统计每个模型工具名出现次数；如果没有这一行，无法区分一次暴露和重复暴露。
        return sorted(name for name, count in counts.items() if count > 1)  # 新增代码+ComputerUseNoDuplicateSurface: 返回重复出现的工具名；如果没有这一行，断言失败时不知道哪个工具重复。
    # 新增代码+ComputerUseNoDuplicateSurface: 函数段结束，_duplicate_tool_names 到此结束；如果没有这个边界说明，用户不容易看出重复检测范围。

    # 新增代码+ComputerUseToolScopeTests: 函数段开始，test_code_mode_hides_computer_use_and_debug_tools 验证普通代码模式；如果没有这段测试，桌面工具可能泄露到代码轮次。
    def test_code_mode_hides_computer_use_and_debug_tools(self) -> None:  # 新增代码+ComputerUseToolScopeTests: 声明代码模式工具池测试；如果没有这一行，首轮默认边界没有保护。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseToolScopeTests: 创建临时工作区；如果没有这一行，agent 运行会污染真实项目。
            agent = self._build_agent(Path(raw_dir), "code_development")  # 新增代码+ComputerUseToolScopeTests: 构造代码开发模式 agent；如果没有这一行，测试没有主体。
            names = self._tool_names(agent)  # 新增代码+ComputerUseToolScopeTests: 读取可见工具名；如果没有这一行，后续断言没有输入。
            self.assertEqual(names, {"read", "write", "edit"})  # 新增代码+ComputerUseToolScopeTests: 断言普通代码模式只保留三文件原子工具；如果没有这一行，debug 或 MCP 泄露不会失败。
            self.assertNotIn("read_trace", names)  # 新增代码+ComputerUseToolScopeTests: 断言 debug 工具不在普通代码模式可见；如果没有这一行，read_trace 泄露不会被发现。
            self.assertNotIn("mcp__computer-use__left_click", names)  # 新增代码+ComputerUseToolScopeTests: 断言真实鼠标工具不在代码模式可见；如果没有这一行，模型可能误点真实桌面。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，test_code_mode_hides_computer_use_and_debug_tools 到此结束；如果没有这个边界说明，用户不容易看出代码模式测试范围。

    # 新增代码+ComputerUseToolScopeTests: 函数段开始，test_source_development_mode_hides_computer_use_tools 验证开发 Computer Use 源码时恢复文件工具；如果没有这段测试，源码开发模式可能误暴露真实鼠标键盘工具。
    def test_source_development_mode_hides_computer_use_tools(self) -> None:  # 新增代码+ComputerUseToolScopeTests: 声明 Computer Use 源码开发模式工具池测试；如果没有这一行，蓝图要求的第四种模式没有快照保护。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseToolScopeTests: 创建临时工作区；如果没有这一行，测试可能污染真实项目路径。
            agent = self._build_agent(Path(raw_dir), "computer_use_source_development")  # 新增代码+ComputerUseToolScopeTests: 构造 Computer Use 源码开发模式 agent；如果没有这一行，无法验证该模式工具面。
            names = self._tool_names(agent)  # 新增代码+ComputerUseToolScopeTests: 读取当前模型可见工具名；如果没有这一行，后续断言没有真实输入。
            self.assertEqual(names, {"read", "write", "edit"})  # 新增代码+ComputerUseToolScopeTests: 断言源码开发模式只保留文件开发三工具；如果没有这一行，桌面工具泄露不会让测试失败。
            self.assertNotIn("read_trace", names)  # 新增代码+ComputerUseToolScopeTests: 断言调试诊断工具不在源码开发模式可见；如果没有这一行，debug 工具可能污染源码开发轮次。
            self.assertNotIn("mcp__computer-use__left_click", names)  # 新增代码+ComputerUseToolScopeTests: 断言真实左键工具不在源码开发模式可见；如果没有这一行，改源码时可能误触桌面。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，test_source_development_mode_hides_computer_use_tools 到此结束；如果没有这个边界说明，用户不容易看出源码开发模式测试范围。

    # 新增代码+ComputerUseToolScopeTests: 函数段开始，test_operation_mode_exposes_only_claudecode_mcp_surface 验证操作模式；如果没有这段测试，同义工具可能同轮混用。
    def test_operation_mode_exposes_only_claudecode_mcp_surface(self) -> None:  # 新增代码+ComputerUseToolScopeTests: 声明 Computer Use 操作模式工具池测试；如果没有这一行，ClaudeCode 风格工具面没有自动保护。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseToolScopeTests: 创建临时工作区；如果没有这一行，agent 运行会污染真实项目。
            agent = self._build_agent(Path(raw_dir), "computer_use_operation")  # 新增代码+ComputerUseToolScopeTests: 构造操作模式 agent；如果没有这一行，测试没有主体。
            names = self._tool_names(agent)  # 新增代码+ComputerUseToolScopeTests: 读取当前可见工具名；如果没有这一行，后续断言没有输入。
            expected_names = {f"mcp__computer-use__{name}" for name in OPERATION_RAW_TOOL_NAMES}  # 新增代码+ComputerUseToolScopeTests: 生成 MCP 前缀期望工具名；如果没有这一行，断言会手写重复列表。
            legacy_names = {"computer_status", "computer_observe", "computer_discover", "computer_action", "computer_use", "computer-use", "request_access"}  # 新增代码+ComputerUseLegacyHidden: 声明操作模式必须隐藏的旧兼容入口；如果没有这一行，旧工具可能重新和 MCP 原子工具同轮竞争。
            self.assertEqual([], self._duplicate_tool_names(agent))  # 新增代码+ComputerUseNoDuplicateSurface: 断言操作模式没有任何重复工具名；如果没有这一行，重复 request_access 会再次混入模型工具池。
            self.assertTrue(expected_names.issubset(names), sorted(expected_names - names))  # 新增代码+ComputerUseToolScopeTests: 断言操作模式暴露全部 ClaudeCode 风格 MCP 工具；如果没有这一行，缺工具不会失败。
            self.assertFalse({"read", "write", "edit", "bash", "request_access"}.intersection(names))  # 新增代码+ComputerUseToolScopeTests: 断言顶层文件/shell/旧申请入口不暴露；如果没有这一行，工具抢任务问题会回归。
            self.assertFalse(legacy_names.intersection(names), sorted(legacy_names.intersection(names)))  # 新增代码+ComputerUseLegacyHidden: 断言旧 Computer Use 顶层入口不暴露给模型；如果没有这一行，第二阶段的 legacy hidden 约束没有测试门禁。
            self.assertNotIn("mcp__computer-use__click", names)  # 新增代码+ComputerUseToolScopeTests: 断言旧 click 不和 left_click 同轮暴露；如果没有这一行，同义点击工具会混用。
            self.assertNotIn("mcp__computer-use__clipboard", names)  # 新增代码+ComputerUseToolScopeTests: 断言旧 clipboard 不和 read/write_clipboard 同轮暴露；如果没有这一行，剪贴板工具会混用。
            self.assertNotIn("mcp__computer-use__middle_click", names)  # 新增代码+ComputerUseToolScopeTests: 断言预留中键不默认暴露；如果没有这一行，低优先级工具会抢常规点击。
            self.assertNotIn("mcp__computer-use__triple_click", names)  # 新增代码+ComputerUseToolScopeTests: 断言预留三击不默认暴露；如果没有这一行，未成熟工具会进入首选面。
            self.assertNotIn("mcp__computer-use__left_mouse_down", names)  # 新增代码+ComputerUseToolScopeTests: 断言预留左键按下不默认暴露；如果没有这一行，未成熟拆分鼠标动作可能绕过 left_click_drag。
            self.assertNotIn("mcp__computer-use__left_mouse_up", names)  # 新增代码+ComputerUseToolScopeTests: 断言预留左键释放不默认暴露；如果没有这一行，未成熟拆分鼠标动作可能和拖拽工具混用。
            self.assertNotIn("read_trace", names)  # 新增代码+ComputerUseToolScopeTests: 断言操作模式不暴露 debug 诊断工具；如果没有这一行，普通操作轮次会变吵。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，test_operation_mode_exposes_only_claudecode_mcp_surface 到此结束；如果没有这个边界说明，用户不容易看出操作模式测试范围。

    # 新增代码+ComputerUseTerminalScopeSyncTest: 函数段开始，test_terminal_full_activation_switches_agent_scope_before_select_pack 验证真实终端 full 命令会先同步 agent scope；如果没有这段测试，可见终端会再次出现“模型看不到 mcp__computer-use__request_access”。
    def test_terminal_full_activation_switches_agent_scope_before_select_pack(self) -> None:  # 新增代码+ComputerUseTerminalScopeSyncTest: 声明 full 命令同步工具池测试；如果没有这一行，单元测试不会覆盖终端入口。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseTerminalScopeSyncTest: 创建临时工作区；如果没有这一行，测试会污染真实项目状态。
            agent = self._build_agent(Path(raw_dir), "auto")  # 新增代码+ComputerUseTerminalScopeSyncTest: 构造 auto 模式 agent 模拟真实启动默认状态；如果没有这一行，测试会绕过本次 bug 的 code_development 推断。
            output = _activate_computer_use_tool_pack_for_agent(agent, "/computer use --full", "Computer Use Mode\n- mode=full\n- full_mode=true\n- opened=true\n")  # 新增代码+ComputerUseTerminalScopeSyncTest: 模拟用户真实输入 full 后的终端输出；如果没有这一行，无法复现工具包加载入口。
            names = self._tool_names(agent)  # 新增代码+ComputerUseTerminalScopeSyncTest: 读取同步后的模型可见工具池；如果没有这一行，测试只能看输出文字不能证明 schema 真可见。
            self.assertIn("model_loop_tools_loaded=true", output)  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言工具包加载成功；如果没有这一行，scope 同步失败可能只在后续断言里模糊失败。
            self.assertEqual("computer_use_operation", agent.tool_scope_mode)  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言 agent 已进入 Computer Use 操作模式；如果没有这一行，tool_search 仍可能按代码模式过滤工具。
            self.assertTrue(agent.desktop_task_context["active"])  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言桌面任务上下文已激活；如果没有这一行，auto scope 和主循环提示可能仍不知道 full 已打开。
            self.assertTrue(agent.desktop_task_context["requires_gui_actions"])  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言上下文标记需要 GUI 动作；如果没有这一行，Computer Use harness 可能不会进入桌面任务边界。
            self.assertIn("mcp__computer-use__request_access", names)  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言 MCP 授权申请工具对模型可见；如果没有这一行，真实终端 adapter 验收会继续失败。
            self.assertNotIn("read", names)  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言顶层 read 没有混入 Computer Use 操作模式；如果没有这一行，文件工具可能重新抢桌面任务。
            self.assertNotIn("write", names)  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言顶层 write 没有混入 Computer Use 操作模式；如果没有这一行，文本输入任务可能被文件写入抢走。
            self.assertNotIn("edit", names)  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言顶层 edit 没有混入 Computer Use 操作模式；如果没有这一行，Office/浏览器编辑可能被源码 edit 抢走。
    # 新增代码+ComputerUseTerminalScopeSyncTest: 函数段结束，test_terminal_full_activation_switches_agent_scope_before_select_pack 到此结束；如果没有这个边界说明，用户不容易看出 full 同步测试范围。

    # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 函数段开始，test_terminal_full_model_turn_keeps_claudecode_atomic_tools 验证 full 模式下一轮模型 schema 不会被旧首轮收窄逻辑缩成两个工具；如果没有这段测试，真实可见终端会再次出现 observe/left_click 不在 schema 里的回归。
    def test_terminal_full_model_turn_keeps_claudecode_atomic_tools(self) -> None:  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 声明 v2 full 主循环工具面测试；如果没有这一行，unittest 不会覆盖本次真实验收失败路径。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 创建临时工作区隔离 agent 状态；如果没有这一行，测试会污染真实项目 memory。
            agent = self._build_agent(Path(raw_dir), "auto")  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 用真实 agent 和 fake MCP schema 模拟可见终端默认启动状态；如果没有这一行，测试无法覆盖 catalog/tool_scope/run loop 的组合路径。
            _activate_computer_use_tool_pack_for_agent(agent, "/computer use --full", "Computer Use Mode\n- mode=full\n- full_mode=true\n- opened=true\n")  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 模拟用户先打开 full 模式并加载 17 个 MCP 工具；如果没有这一行，后续上下文没有 v2 terminal session 事实。
            prompt = "请执行 Computer Use MCP v2 ClaudeCode 接入链路验收，第一步调用 mcp__computer-use__observe，第二步调用 mcp__computer-use__left_click。"  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 使用真实验收同类自然语言 prompt；如果没有这一行，无法复现 prompt 分类器把任务识别成 local_app 的场景。
            context = agent._desktop_task_policy_context_from_prompt(prompt)  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 调用真实主循环会用的桌面上下文构造入口；如果没有这一行，测试只会验证孤立过滤函数而不是实际接线。
            schemas = catalog_runtime_from_tools.available_tool_schemas(agent)  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 读取 full 模式下真实模型基础工具 schema；如果没有这一行，后续 scoped 结果没有输入。
            scoped_schemas = scoped_tool_schemas_for_model_turn(schemas, 0, context, lambda: False)  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 用第 0 轮执行旧 bug 所在的 schema 收窄函数；如果没有这一行，测试不会抓到 observe/left_click 被过滤的问题。
            scoped_names = set(catalog_runtime_from_tools.tool_schema_names(agent, scoped_schemas))  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 提取本轮真正会发给模型的工具名；如果没有这一行，断言无法看见最终 schema 名称。
            self.assertEqual("computer_use_mcp_v2", context["runtime"])  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 断言 `/computer use --full` 的运行时标记被保留；如果没有这一行，后续过滤层仍可能把它当普通自动桌面任务。
            self.assertEqual("full", context["terminal_mode"])  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 断言 full 终端模式没有被 prompt 分类覆盖；如果没有这一行，首轮收窄逻辑可能重新生效。
            self.assertTrue(context["computer_use_mcp_v2_session_active"])  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 断言本轮上下文明确知道 v2 会话仍有效；如果没有这一行，代码只靠 tool_scope_mode 推断会不够清楚。
            self.assertIn("mcp__computer-use__observe", scoped_names)  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 断言观察工具真实进入模型 schema；如果没有这一行，本次验收失败会再次漏掉。
            self.assertIn("mcp__computer-use__left_click", scoped_names)  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 断言左键工具真实进入模型 schema；如果没有这一行，模型仍可能看不到执行点击的入口。
            self.assertIn("mcp__computer-use__open_application", scoped_names)  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 断言启动工具仍保留而不是反向删掉；如果没有这一行，修复可能破坏本机应用启动路线。
            self.assertGreaterEqual(len(scoped_names), len(OPERATION_RAW_TOOL_NAMES))  # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 断言 v2 full 模式保留 ClaudeCode 风格全量原子工具面；如果没有这一行，只保留三四个工具的回归可能逃过单点断言。
    # 新增代码+ComputerUseMcpV2SchemaNarrowingFix: 函数段结束，test_terminal_full_model_turn_keeps_claudecode_atomic_tools 到此结束；如果没有这个边界说明，用户不容易看出这段测试锁的是模型请求前最终 schema。

    # 新增代码+ComputerUseTerminalScopeSyncTest: 函数段开始，test_terminal_stop_resets_agent_scope_and_loaded_mcp_tools 验证 stop 后工具池回到普通边界；如果没有这段测试，用户停止 Computer Use 后模型仍可能看到 MCP 桌面工具。
    def test_terminal_stop_resets_agent_scope_and_loaded_mcp_tools(self) -> None:  # 新增代码+ComputerUseTerminalScopeSyncTest: 声明 stop 同步恢复测试；如果没有这一行，stop 命令不会有工具池回归门禁。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseTerminalScopeSyncTest: 创建临时工作区；如果没有这一行，测试状态会污染真实项目。
            agent = self._build_agent(Path(raw_dir), "auto")  # 新增代码+ComputerUseTerminalScopeSyncTest: 构造 auto 模式 agent；如果没有这一行，无法模拟真实终端默认 agent。
            _activate_computer_use_tool_pack_for_agent(agent, "/computer use --full", "Computer Use Mode\n- mode=full\n- full_mode=true\n- opened=true\n")  # 新增代码+ComputerUseTerminalScopeSyncTest: 先打开 full 并加载 MCP 工具；如果没有这一行，stop 测试没有可清理状态。
            stop_output = _activate_computer_use_tool_pack_for_agent(agent, "/computer stop", "Computer Use Stop\n- stopped=true\n")  # 新增代码+ComputerUseTerminalScopeSyncTest: 模拟用户真实 stop 输出；如果没有这一行，无法覆盖 stop 清理入口。
            names = self._tool_names(agent)  # 新增代码+ComputerUseTerminalScopeSyncTest: 读取 stop 后模型可见工具池；如果没有这一行，测试无法证明工具真的隐藏了。
            self.assertIn("model_loop_tools_loaded=false", stop_output)  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言 stop 输出说明工具包关闭；如果没有这一行，真实终端用户看不到工具面恢复。
            self.assertEqual("auto", agent.tool_scope_mode)  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言显式模式恢复 auto；如果没有这一行，普通代码任务仍可能继承 Computer Use scope。
            self.assertFalse(agent.desktop_task_context["active"])  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言桌面任务上下文关闭；如果没有这一行，auto scope 可能继续推断为桌面任务。
            self.assertNotIn("mcp__computer-use__request_access", names)  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言 MCP 授权工具 stop 后不可见；如果没有这一行，停止命令不会真正收回工具面。
            self.assertIn("read", names)  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言普通代码模式 read 恢复可见；如果没有这一行，stop 后用户可能无法继续开发代码。
            self.assertIn("write", names)  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言普通代码模式 write 恢复可见；如果没有这一行，stop 后文件写入工具可能丢失。
            self.assertIn("edit", names)  # 新增代码+ComputerUseTerminalScopeSyncTest: 断言普通代码模式 edit 恢复可见；如果没有这一行，stop 后源码编辑会被误隐藏。
    # 新增代码+ComputerUseTerminalScopeSyncTest: 函数段结束，test_terminal_stop_resets_agent_scope_and_loaded_mcp_tools 到此结束；如果没有这个边界说明，用户不容易看出 stop 同步测试范围。

    # 新增代码+ComputerUseToolScopeTests: 函数段开始，test_debug_mode_exposes_operation_surface_and_debug_tools 验证调试模式；如果没有这段测试，debug 工具可能不可见。
    def test_debug_mode_exposes_operation_surface_and_debug_tools(self) -> None:  # 新增代码+ComputerUseToolScopeTests: 声明 Computer Use debug 模式工具池测试；如果没有这一行，调试工具面没有保护。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseToolScopeTests: 创建临时工作区；如果没有这一行，agent 运行会污染真实项目。
            agent = self._build_agent(Path(raw_dir), "computer_use_debug")  # 新增代码+ComputerUseToolScopeTests: 构造 debug 模式 agent；如果没有这一行，测试没有主体。
            names = self._tool_names(agent)  # 新增代码+ComputerUseToolScopeTests: 读取当前可见工具名；如果没有这一行，后续断言没有输入。
            legacy_names = {"computer_status", "computer_observe", "computer_discover", "computer_action", "computer_use", "computer-use", "request_access"}  # 新增代码+ComputerUseLegacyHidden: 声明 debug 模式仍要隐藏的旧兼容入口；如果没有这一行，调试模式可能重新暴露旧工具面。
            self.assertEqual([], self._duplicate_tool_names(agent))  # 新增代码+ComputerUseNoDuplicateSurface: 断言 debug 模式也没有重复工具名；如果没有这一行，调试工具池可能再次出现同名 MCP/内置混用。
            self.assertIn("mcp__computer-use__left_click", names)  # 新增代码+ComputerUseToolScopeTests: 断言 debug 模式仍能测试真实点击工具；如果没有这一行，调试模式无法覆盖真实动作。
            self.assertIn("read_trace", names)  # 新增代码+ComputerUseToolScopeTests: 断言 read_trace 在 debug 模式可见；如果没有这一行，运行轨迹调试不可用。
            self.assertIn("read_state", names)  # 新增代码+ComputerUseToolScopeTests: 断言 read_state 在 debug 模式可见；如果没有这一行，状态调试不可用。
            self.assertIn("assert_last_action", names)  # 新增代码+ComputerUseToolScopeTests: 断言 assert_last_action 在 debug 模式可见；如果没有这一行，结果断言不可用。
            self.assertFalse({"read", "write", "edit", "bash", "request_access"}.intersection(names))  # 新增代码+ComputerUseToolScopeTests: 断言 debug 模式仍隐藏顶层文件/shell/旧申请入口；如果没有这一行，调试会重新混入文件工具。
            self.assertFalse(legacy_names.intersection(names), sorted(legacy_names.intersection(names)))  # 新增代码+ComputerUseLegacyHidden: 断言 debug 模式不把旧 Computer Use 入口暴露给模型；如果没有这一行，第二阶段调试模式会和操作模式不一致。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，test_debug_mode_exposes_operation_surface_and_debug_tools 到此结束；如果没有这个边界说明，用户不容易看出 debug 模式测试范围。

    # 修改代码+McpSessionAdapter: 函数段开始，test_mcp_request_access_executes_through_agent_side_adapter 验证 MCP 工具进入内部 adapter；如果没有这段测试，request_access 可能重新走外部 registry 而失去 agent 回调。
    def test_mcp_request_access_executes_through_agent_side_adapter(self) -> None:  # 修改代码+McpSessionAdapter: 声明 MCP request_access agent-side 路由测试；如果没有这一行，执行层新绑定没有自动化门禁。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseMcpRequestAccessRouting: 创建临时工作区；如果没有这一行，agent 运行会污染真实项目。
            agent = self._build_agent(Path(raw_dir), "computer_use_operation")  # 新增代码+ComputerUseMcpRequestAccessRouting: 构造操作模式 agent；如果没有这一行，MCP 工具会被 scope 拦截。
            output = agent._execute_tool(ToolCall(name="mcp__computer-use__request_access", arguments={"applications": ["Notepad"], "reason": "测试 MCP 路由"}))  # 修改代码+McpSessionAdapter: 调用 MCP 风格授权申请工具；如果没有这一行，无法证明执行进入 agent-side adapter。
            payload = json.loads(output)  # 修改代码+ComputerUseMcpV2: 解析 v2 JSON 结果；如果没有这一行，测试只能靠旧 marker 字符串判断是否执行成功。
            self.assertTrue(payload["ok"], payload)  # 修改代码+ComputerUseMcpV2: 断言 v2 request_access 成功；如果没有这一行，失败结果可能被误当作路由成功。
            self.assertEqual("computer_use_mcp_v2", payload["runtime"])  # 修改代码+ComputerUseMcpV2: 断言执行运行时来自 v2；如果没有这一行，旧 adapter 回归不会被发现。
            self.assertFalse(payload["legacy_adapter_used"])  # 修改代码+ComputerUseMcpV2: 断言没有使用旧 adapter；如果没有这一行，旧接口可能继续偷偷接管。
            self.assertTrue(any(event.get("phase") == "tool_completed" and event.get("payload", {}).get("tool_name") == "request_access" for event in agent.computer_use_runtime_trace_events))  # 修改代码+ComputerUseMcpV2: 按 v2 trace 真实结构断言 runtime trace 被写入；如果没有这一行，request_access 可能只是返回文本但缺少证据链。
    # 修改代码+McpSessionAdapter: 函数段结束，test_mcp_request_access_executes_through_agent_side_adapter 到此结束；如果没有这个边界说明，用户不容易看出 agent-side 路由测试范围。

    # 新增代码+ComputerUseToolScopeTests: 函数段开始，test_tool_search_does_not_leak_scope_blocked_tools 验证发现层过滤；如果没有这段测试，隐藏工具名可能通过搜索泄露。
    def test_tool_search_does_not_leak_scope_blocked_tools(self) -> None:  # 新增代码+ComputerUseToolScopeTests: 声明 tool_search 泄露测试；如果没有这一行，发现层没有保护。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseToolScopeTests: 创建临时工作区；如果没有这一行，agent 运行会污染真实项目。
            agent = self._build_agent(Path(raw_dir), "code_development")  # 新增代码+ComputerUseToolScopeTests: 构造代码模式 agent；如果没有这一行，测试无法验证非桌面模式搜索。
            output = search_tools_from_tools.tool_search(agent, {"query": "left click computer use", "max_results": 20})  # 新增代码+ComputerUseToolScopeTests: 直接搜索桌面点击工具；如果没有这一行，搜索泄露没有输入。
            self.assertNotIn("mcp__computer-use__left_click", output)  # 新增代码+ComputerUseToolScopeTests: 断言代码模式搜索不到隐藏点击工具；如果没有这一行，模型仍能发现并尝试 select 隐藏工具。
            self.assertNotIn("mcp__computer-use__click", output)  # 新增代码+ComputerUseToolScopeTests: 断言旧 click 也不会从搜索泄露；如果没有这一行，同义旧名仍可能被发现。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，test_tool_search_does_not_leak_scope_blocked_tools 到此结束；如果没有这个边界说明，用户不容易看出发现层测试范围。

    # 新增代码+ComputerUseToolScopeTests: 函数段开始，test_executor_blocks_hidden_tools_even_when_called_directly 验证执行层硬拦截；如果没有这段测试，模型历史里记住隐藏工具名可能绕过展示层。
    def test_executor_blocks_hidden_tools_even_when_called_directly(self) -> None:  # 新增代码+ComputerUseToolScopeTests: 声明执行层 scope 拦截测试；如果没有这一行，硬拦截没有保护。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseToolScopeTests: 创建临时工作区；如果没有这一行，agent 运行会污染真实项目。
            operation_agent = self._build_agent(Path(raw_dir), "computer_use_operation")  # 新增代码+ComputerUseToolScopeTests: 构造操作模式 agent；如果没有这一行，无法验证 read 被隐藏。
            read_output = operation_agent._execute_tool(ToolCall(name="read", arguments={"path": "missing.txt"}))  # 新增代码+ComputerUseToolScopeTests: 直接伪造顶层 read 调用；如果没有这一行，执行层文件工具拦截没有输入。
            self.assertIn("scope_blocked", read_output)  # 新增代码+ComputerUseToolScopeTests: 断言 read 被 scope 拦截而不是读文件；如果没有这一行，文件工具可能绕过隐藏层。
            code_agent = self._build_agent(Path(raw_dir), "code_development")  # 新增代码+ComputerUseToolScopeTests: 构造代码模式 agent；如果没有这一行，无法验证桌面工具被隐藏。
            click_output = code_agent._execute_tool(ToolCall(name="mcp__computer-use__left_click", arguments={"x": 1, "y": 2}))  # 新增代码+ComputerUseToolScopeTests: 直接伪造桌面点击调用；如果没有这一行，执行层桌面工具拦截没有输入。
            self.assertIn("scope_blocked", click_output)  # 新增代码+ComputerUseToolScopeTests: 断言桌面点击在代码模式被拒绝；如果没有这一行，真实鼠标工具可能绕过展示层。
            legacy_action_output = operation_agent._execute_tool(ToolCall(name="computer_action", arguments={"action": "click"}))  # 新增代码+ComputerUseMcpV2LegacyBlockTest: 直接伪造旧 computer_action 调用；如果没有这一行，旧执行入口是否被硬阻断就没有测试证据。
            self.assertIn("旧 Computer Use 内置入口已停用", legacy_action_output)  # 新增代码+ComputerUseMcpV2LegacyBlockTest: 断言旧动作入口只能返回迁移提示；如果没有这一行，旧工具可能悄悄重新暴露给模型。
            legacy_request_output = operation_agent._execute_tool(ToolCall(name="request_access", arguments={"requested_apps": ["Notepad"]}))  # 新增代码+ComputerUseMcpV2LegacyBlockTest: 直接伪造旧裸 request_access 调用；如果没有这一行，裸权限工具名可能绕过 mcp 前缀。
            self.assertIn("旧 Computer Use 内置入口已停用", legacy_request_output)  # 新增代码+ComputerUseMcpV2LegacyBlockTest: 断言旧裸权限入口被拒绝；如果没有这一行，模型可能绕开 mcp__computer-use__request_access。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，test_executor_blocks_hidden_tools_even_when_called_directly 到此结束；如果没有这个边界说明，用户不容易看出执行层测试范围。

    # 新增代码+ComputerUseToolScopeTests: 函数段开始，test_debug_tools_execute_in_debug_scope 验证 debug 工具真实执行；如果没有这段测试，schema 可见但分发表可能断开。
    def test_debug_tools_execute_in_debug_scope(self) -> None:  # 新增代码+ComputerUseToolScopeTests: 声明 debug 工具执行测试；如果没有这一行，read_trace/read_state 执行路径没有保护。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseToolScopeTests: 创建临时工作区；如果没有这一行，agent 运行会污染真实项目。
            agent = self._build_agent(Path(raw_dir), "computer_use_debug")  # 新增代码+ComputerUseToolScopeTests: 构造 debug 模式 agent；如果没有这一行，debug 工具会被 scope 拦截。
            agent.computer_use_runtime_trace_events.append({"phase": "tool_result", "payload": {"tool_name": "mcp__computer-use__left_click", "ok": True}})  # 新增代码+ComputerUseToolScopeTests: 注入一条动作结果 trace；如果没有这一行，read_trace/assert_last_action 没有可验证数据。
            trace_output = agent._execute_tool(ToolCall(name="read_trace", arguments={"limit": 5}))  # 新增代码+ComputerUseToolScopeTests: 执行 read_trace；如果没有这一行，debug 分发表不会被覆盖。
            trace_payload = json.loads(trace_output)  # 新增代码+ComputerUseToolScopeTests: 解析 read_trace JSON 输出；如果没有这一行，断言会依赖脆弱文本。
            self.assertTrue(trace_payload["ok"])  # 新增代码+ComputerUseToolScopeTests: 断言 read_trace 成功；如果没有这一行，工具执行失败不会暴露。
            assert_output = agent._execute_tool(ToolCall(name="assert_last_action", arguments={"expected_tool": "mcp__computer-use__left_click", "expected_ok": True}))  # 新增代码+ComputerUseToolScopeTests: 执行最近动作断言；如果没有这一行，assert_last_action 分发表不会被覆盖。
            assert_payload = json.loads(assert_output)  # 新增代码+ComputerUseToolScopeTests: 解析断言输出；如果没有这一行，无法结构化验证 ok。
            self.assertTrue(assert_payload["ok"], assert_payload)  # 新增代码+ComputerUseToolScopeTests: 断言最近动作符合预期；如果没有这一行，debug 验收工具可能假成功或假失败。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，test_debug_tools_execute_in_debug_scope 到此结束；如果没有这个边界说明，用户不容易看出 debug 执行测试范围。


class _FakeMcpClient:  # 新增代码+ComputerUseToolScopeTests: 定义 fake MCP client；如果没有这一段，测试需要启动真实 stdio server。
    # 新增代码+ComputerUseToolScopeTests: 函数段开始，__init__ 保存工具列表；如果没有这段函数，fake client 没有可返回 schema。
    def __init__(self, tools: list[dict[str, object]]) -> None:  # 新增代码+ComputerUseToolScopeTests: 声明 fake 初始化入口；如果没有这一行，测试无法注入 Computer Use 工具清单。
        self.tools = tools  # 新增代码+ComputerUseToolScopeTests: 保存工具清单；如果没有这一行，list_tools 会返回空。
        self.calls: list[tuple[str, dict[str, object]]] = []  # 新增代码+ComputerUseToolScopeTests: 保存调用记录；如果没有这一行，后续排查无法确认是否触达 fake server。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake 初始化范围。

    # 新增代码+ComputerUseToolScopeTests: 函数段开始，start 模拟 MCP client 启动；如果没有这段函数，registry.start 会失败。
    def start(self) -> None:  # 新增代码+ComputerUseToolScopeTests: 声明 fake start；如果没有这一行，registry 无法统一启动。
        return None  # 新增代码+ComputerUseToolScopeTests: fake 启动无需动作；如果没有这一行，函数没有明确返回。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，start 到此结束；如果没有这个边界说明，用户不容易看出 fake 启动范围。

    # 新增代码+ComputerUseToolScopeTests: 函数段开始，list_tools 返回 fake 工具清单；如果没有这段函数，registry 无法发现 MCP 工具。
    def list_tools(self) -> list[dict[str, object]]:  # 新增代码+ComputerUseToolScopeTests: 声明 fake tools/list；如果没有这一行，Computer Use MCP schema 不会进入 catalog。
        return self.tools  # 新增代码+ComputerUseToolScopeTests: 返回注入工具列表；如果没有这一行，模型看不到任何 MCP 工具。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，list_tools 到此结束；如果没有这个边界说明，用户不容易看出 fake list 范围。

    # 新增代码+ComputerUseToolScopeTests: 函数段开始，call_tool 记录并返回 fake 调用结果；如果没有这段函数，直接 MCP 执行测试会缺入口。
    def call_tool(self, tool_name: str, arguments: dict[str, object]) -> str:  # 新增代码+ComputerUseToolScopeTests: 声明 fake tools/call；如果没有这一行，adapter 触达 fake server 时会失败。
        self.calls.append((tool_name, dict(arguments)))  # 新增代码+ComputerUseToolScopeTests: 保存调用记录；如果没有这一行，无法排查是否绕过 scope 触达 server。
        return f"called {tool_name}"  # 新增代码+ComputerUseToolScopeTests: 返回简单结果文本；如果没有这一行，MCP adapter 拿不到工具输出。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，call_tool 到此结束；如果没有这个边界说明，用户不容易看出 fake call 范围。

    # 新增代码+ComputerUseToolScopeTests: 函数段开始，close 模拟清理；如果没有这段函数，registry.close 会失败。
    def close(self) -> None:  # 新增代码+ComputerUseToolScopeTests: 声明 fake close；如果没有这一行，测试清理路径不完整。
        return None  # 新增代码+ComputerUseToolScopeTests: fake 关闭无需动作；如果没有这一行，函数没有明确返回。
    # 新增代码+ComputerUseToolScopeTests: 函数段结束，close 到此结束；如果没有这个边界说明，用户不容易看出 fake close 范围。


if __name__ == "__main__":  # 新增代码+ComputerUseToolScopeTests: 允许直接运行本测试文件；如果没有这一行，手动调试不方便。
    unittest.main()  # 新增代码+ComputerUseToolScopeTests: 启动 unittest 主程序；如果没有这一行，直接运行不会执行测试。
