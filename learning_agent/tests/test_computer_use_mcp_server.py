"""独立 computer-use MCP server 验收测试。"""  # 新增代码+ComputerUseMCP：说明本文件锁住独立 MCP server 合同；如果没有这行代码，测试意图不清楚。
from __future__ import annotations  # 新增代码+ComputerUseMCP：延迟类型解析保持测试导入稳定；如果没有这行代码，类型注解可能影响老环境。

import json  # 新增代码+ComputerUseMCP：导入 JSON 用于解析 selftest 输出；如果没有这行代码，测试无法读取报告。
import subprocess  # 新增代码+ComputerUseMCP：导入 subprocess 用于启动真实 stdio server 自检；如果没有这行代码，测试只能覆盖纯函数。
import sys  # 新增代码+ComputerUseMCP：导入 sys 取得当前 Python 可执行文件；如果没有这行代码，测试可能调用到错误解释器。
import unittest  # 新增代码+ComputerUseMCP：导入 unittest 测试框架；如果没有这行代码，测试类无法运行。
from pathlib import Path  # 新增代码+ComputerUseMCP：导入 Path 定位项目文件；如果没有这行代码，脚本路径拼接不稳定。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import COMPUTER_USE_MCP_READY_MARKER, COMPUTER_USE_MCP_TOOL_NAMES, assert_no_shell_surface, computer_use_mcp_tools  # 修改代码+ComputerUseMcpV2ImportCutover：改从 v2 inferred MCP 包导入 schema 和 ready marker；如果没有这一行，server 测试会继续读取已删除的旧工具清单。
from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_executor import ComputerUseMcpExecutionContext, call_computer_use_mcp_tool  # 修改代码+ComputerUseMcpV2ImportCutover：改从 v2 Windows runtime 导入内部 executor；如果没有这一行，删除旧 computer_use 包后执行边界测试会中断。
from learning_agent.mcp.runtime import McpServerConfig, McpToolRegistry  # 新增代码+ComputerUseMCP：导入 MCP registry 类型；如果没有这行代码，无法证明 server 能被模型工具目录发现。


class ComputerUseMcpServerTests(unittest.TestCase):  # 新增代码+ComputerUseMCP：定义独立 MCP server 测试类；如果没有这段类，unittest 不会发现这些测试。
    # 新增代码+ComputerUseMCP：函数段开始，_project_root 定位项目根；如果没有这段函数，测试会重复写 parents 路径。
    def _project_root(self) -> Path:  # 新增代码+ComputerUseMCP：声明项目根 helper；如果没有这行代码，脚本路径定位不集中。
        return Path(__file__).resolve().parents[2]  # 新增代码+ComputerUseMCP：返回 OpenHarness-main 根目录；如果没有这行代码，server 脚本路径会算错。
    # 新增代码+ComputerUseMCP：函数段结束，_project_root 到此结束；如果没有这个边界说明，初学者不容易看出路径 helper 范围。

    # 新增代码+ComputerUseMCP：函数段开始，_server_path 定位独立 server；如果没有这段函数，每个测试都要重复拼路径。
    def _server_path(self) -> Path:  # 新增代码+ComputerUseMCP：声明 server 路径 helper；如果没有这行代码，测试启动 server 容易拼错。
        return self._project_root() / "learning_agent" / "mcp" / "servers" / "computer_use_server.py"  # 新增代码+ComputerUseMCP：返回 server 文件绝对路径；如果没有这行代码，subprocess 找不到脚本。
    # 新增代码+ComputerUseMCP：函数段结束，_server_path 到此结束；如果没有这个边界说明，初学者不容易看出 server 路径范围。

    # 新增代码+ComputerUseMCP：函数段开始，test_schema_exposes_claudecode_style_desktop_tools_without_shell_surface 检查工具清单；如果没有这段测试，bash 回归可能没人发现。
    def test_schema_exposes_claudecode_style_desktop_tools_without_shell_surface(self) -> None:  # 新增代码+ComputerUseMCP：声明 schema 边界测试；如果没有这行代码，工具名合同没有自动保护。
        tools = computer_use_mcp_tools()  # 新增代码+ComputerUseMCP：读取工具清单副本；如果没有这行代码，后续断言没有输入。
        tool_names = {str(tool.get("name", "")) for tool in tools}  # 新增代码+ComputerUseMCP：抽取工具名集合；如果没有这行代码，断言会反复遍历原始对象。
        self.assertTrue(set(COMPUTER_USE_MCP_TOOL_NAMES).issubset(tool_names))  # 新增代码+ComputerUseMCP：断言预期桌面原子工具都存在；如果没有这行代码，工具缺失不会失败。
        self.assertNotIn("bash", tool_names)  # 新增代码+ComputerUseMCP：断言 bash 没进 computer-use MCP；如果没有这行代码，首轮 shell 混入可能回归。
        self.assertNotIn("powershell", tool_names)  # 新增代码+ComputerUseMCP：断言 powershell 没进 computer-use MCP；如果没有这行代码，Windows 命令面可能误暴露。
        self.assertTrue(assert_no_shell_surface(tools))  # 新增代码+ComputerUseMCP：断言 schema 没有命令执行参数；如果没有这行代码，command/script 字段回归不会失败。
    # 新增代码+ComputerUseMCP：函数段结束，test_schema_exposes_claudecode_style_desktop_tools_without_shell_surface 到此结束；如果没有这个边界说明，初学者不容易看出 schema 测试范围。

    # 新增代码+ComputerUseMCP：函数段开始，test_registry_preserves_computer_use_hyphen_prefix 检查 ClaudeCode 风格前缀；如果没有这段测试，server 名可能被错误改成下划线。
    def test_registry_preserves_computer_use_hyphen_prefix(self) -> None:  # 新增代码+ComputerUseMCP：声明 registry 命名测试；如果没有这行代码，工具名前缀合同没有保护。
        registry = McpToolRegistry({"computer-use": _FakeMcpClient(computer_use_mcp_tools())})  # 新增代码+ComputerUseMCP：用 fake client 避免启动子进程；如果没有这行代码，测试会变慢且不必要。
        registry.start()  # 新增代码+ComputerUseMCP：让 registry 读取 tools/list；如果没有这行代码，tool_schemas 会是空列表。
        tool_names = [schema["function"]["name"] for schema in registry.tool_schemas()]  # 新增代码+ComputerUseMCP：读取模型最终看到的工具名；如果没有这行代码，无法断言前缀。
        self.assertIn("mcp__computer-use__request_access", tool_names)  # 新增代码+ComputerUseMCP：断言保留 computer-use 连字符；如果没有这行代码，对齐 ClaudeCode 的名称会回归。
        self.assertIn("mcp__computer-use__open_application", tool_names)  # 新增代码+ComputerUseMCP：断言桌面动作也带同样前缀；如果没有这行代码，只测 request_access 不够完整。
    # 新增代码+ComputerUseMCP：函数段结束，test_registry_preserves_computer_use_hyphen_prefix 到此结束；如果没有这个边界说明，初学者不容易看出前缀测试范围。

    # 新增代码+ComputerUseMCP：函数段开始，test_registry_assigns_computer_use_capability_pack 检查能力包；如果没有这段测试，/computer use --full 可能加载不到 MCP 工具。
    def test_registry_assigns_computer_use_capability_pack(self) -> None:  # 新增代码+ComputerUseMCP：声明能力包测试；如果没有这行代码，tool_search select_pack 合同没有保护。
        registry = McpToolRegistry({"computer-use": _FakeMcpClient(computer_use_mcp_tools())})  # 新增代码+ComputerUseMCP：创建 fake computer-use registry；如果没有这行代码，测试没有 MCP 工具来源。
        registry.start()  # 新增代码+ComputerUseMCP：启动 registry 读取工具；如果没有这行代码，agent_tools 为空。
        packs = {tool.name: tool.capability_pack for tool in registry.agent_tools()}  # 新增代码+ComputerUseMCP：提取每个 MCP 工具的能力包；如果没有这行代码，无法断言 select_pack 归属。
        self.assertEqual(packs["mcp__computer-use__request_access"], "computer_use")  # 新增代码+ComputerUseMCP：断言 request_access 归入 computer_use 包；如果没有这行代码，full 模式批量加载入口可能失败。
        self.assertEqual(packs["mcp__computer-use__open_application"], "computer_use")  # 新增代码+ComputerUseMCP：断言 open_application 也归入同一包；如果没有这行代码，动作工具可能被留在通用 mcp 包。
    # 新增代码+ComputerUseMCP：函数段结束，test_registry_assigns_computer_use_capability_pack 到此结束；如果没有这个边界说明，初学者不容易看出能力包测试范围。

    # 新增代码+ComputerUseMCP：函数段开始，test_executor_rejects_shell_like_arguments_before_controller 检查执行器硬拒绝；如果没有这段测试，串味 command 参数可能触达 controller。
    def test_executor_rejects_shell_like_arguments_before_controller(self) -> None:  # 新增代码+ComputerUseMCP：声明执行器安全测试；如果没有这行代码，shell 参数拒绝没有自动保护。
        context = ComputerUseMcpExecutionContext(controller_factory=_ExplodingController)  # 新增代码+ComputerUseMCP：注入会爆炸的 controller；如果没有这行代码，无法证明拒绝发生在 controller 之前。
        result = call_computer_use_mcp_tool("click", {"x": 1, "y": 2, "command": "whoami"}, context)  # 新增代码+ComputerUseMCP：传入串味 command 参数；如果没有这行代码，测试不会覆盖危险绕路。
        self.assertFalse(result["ok"])  # 新增代码+ComputerUseMCP：断言本次调用失败；如果没有这行代码，危险参数放行不会暴露。
        self.assertEqual(result["error_class"], "shell_argument_forbidden")  # 新增代码+ComputerUseMCP：断言失败类别明确；如果没有这行代码，模型无法根据错误恢复。
    # 新增代码+ComputerUseMCP：函数段结束，test_executor_rejects_shell_like_arguments_before_controller 到此结束；如果没有这个边界说明，初学者不容易看出安全拒绝测试范围。

    # 新增代码+McpSessionAdapter: 函数段开始，test_executor_delegates_to_session_adapter_before_controller 验证 agent-side adapter 优先级；如果没有这段测试，MCP 原子工具可能继续绕开主循环回调。
    def test_executor_delegates_to_session_adapter_before_controller(self) -> None:  # 新增代码+McpSessionAdapter: 声明 session adapter 优先级测试；如果没有这一行，mcp_executor 的 adapter 字段没有行为保护。
        adapter = _RecordingSessionAdapter()  # 新增代码+McpSessionAdapter: 创建记录型 session adapter；如果没有这一行，测试无法知道是否委托成功。
        context = ComputerUseMcpExecutionContext(controller_factory=_ExplodingController, session_adapter=adapter)  # 新增代码+McpSessionAdapter: 同时注入会爆炸 controller 和 adapter；如果没有这一行，无法证明 controller 未被触碰。
        result = call_computer_use_mcp_tool("left_click", {"x": 3, "y": 4}, context)  # 新增代码+McpSessionAdapter: 调用应由 adapter 接管的原子工具；如果没有这一行，测试没有执行路径。
        self.assertTrue(result["ok"])  # 新增代码+McpSessionAdapter: 断言 adapter 返回成功；如果没有这一行，委托失败也可能被忽略。
        self.assertEqual(adapter.calls, [("left_click", {"x": 3, "y": 4})])  # 新增代码+McpSessionAdapter: 断言工具名和参数原样进入 adapter；如果没有这一行，参数清洗或路由漂移不会暴露。
        self.assertTrue(result["payload"]["adapter_called"])  # 新增代码+McpSessionAdapter: 断言结果来自 adapter；如果没有这一行，测试无法区分 controller 路径和 adapter 路径。
    # 新增代码+McpSessionAdapter: 函数段结束，test_executor_delegates_to_session_adapter_before_controller 到此结束；如果没有这个边界说明，用户不容易看出 adapter 优先级测试范围。

    # 新增代码+ClaudeCodeToolSurface：函数段开始，test_executor_maps_claudecode_style_aliases_to_controller 检查新工具名真实映射；如果没有这段测试，schema 可能有工具但执行层仍然未知。
    def test_executor_maps_claudecode_style_aliases_to_controller(self) -> None:  # 新增代码+ClaudeCodeToolSurface：声明 ClaudeCode 风格工具名映射测试；如果没有这一行，left_click/observe/drag 的执行合同没有保护。
        controller = _RecordingController()  # 新增代码+ClaudeCodeToolSurface：创建记录型 controller；如果没有这一行，无法检查 executor 传给底层的 action。
        context = ComputerUseMcpExecutionContext(controller_factory=lambda: controller)  # 新增代码+ClaudeCodeToolSurface：把记录 controller 注入执行上下文；如果没有这一行，测试可能碰真实桌面后端。
        left_result = call_computer_use_mcp_tool("left_click", {"x": 11, "y": 22}, context)  # 新增代码+ClaudeCodeToolSurface：调用新 left_click 工具名；如果没有这一行，无法证明 left_click 可执行。
        observe_result = call_computer_use_mcp_tool("observe", {"reason": "test"}, context)  # 新增代码+ClaudeCodeToolSurface：调用 observe 别名；如果没有这一行，无法证明 observe 复用 screenshot。
        drag_result = call_computer_use_mcp_tool("left_click_drag", {"start_x": 1, "start_y": 2, "end_x": 3, "end_y": 4}, context)  # 新增代码+ClaudeCodeToolSurface：调用左键拖拽工具；如果没有这一行，无法证明 drag_path 映射。
        zoom_result = call_computer_use_mcp_tool("zoom", {"x": 5, "y": 6, "width": 7, "height": 8}, context)  # 新增代码+ClaudeCodeToolSurface：调用 zoom 观察工具；如果没有这一行，无法证明局部观察映射。
        hold_result = call_computer_use_mcp_tool("hold_key", {"keys": ["Shift"], "duration_seconds": 1.25}, context)  # 新增代码+ClaudeCodeToolSurface：按正式 schema 调用按住按键工具；如果没有这一行，hold_key 可能只有 schema 没有执行映射。
        self.assertTrue(left_result["ok"])  # 新增代码+ClaudeCodeToolSurface：断言 left_click 执行成功；如果没有这一行，controller 返回失败不会暴露。
        self.assertTrue(observe_result["ok"])  # 新增代码+ClaudeCodeToolSurface：断言 observe 执行成功；如果没有这一行，observe 断开不会暴露。
        self.assertTrue(drag_result["ok"])  # 新增代码+ClaudeCodeToolSurface：断言 left_click_drag 执行成功；如果没有这一行，拖拽映射失败不会暴露。
        self.assertTrue(zoom_result["ok"])  # 新增代码+ClaudeCodeToolSurface：断言 zoom 执行成功；如果没有这一行，局部观察映射失败不会暴露。
        self.assertTrue(hold_result["ok"])  # 新增代码+ClaudeCodeToolSurface：断言 hold_key 执行成功；如果没有这一行，按住按键工具断开不会暴露。
        self.assertEqual(controller.calls[0]["action"], "click")  # 新增代码+ClaudeCodeToolSurface：断言 left_click 复用 click action；如果没有这一行，新旧点击映射可能漂移。
        self.assertEqual(controller.calls[0]["button"], "left")  # 新增代码+ClaudeCodeToolSurface：断言 left_click 默认左键；如果没有这一行，点击按钮语义可能错误。
        self.assertEqual(controller.calls[1]["action"], "screenshot")  # 新增代码+ClaudeCodeToolSurface：断言 observe 复用 screenshot action；如果没有这一行，observe 可能误执行其他动作。
        self.assertEqual(controller.calls[2]["action"], "drag_path")  # 新增代码+ClaudeCodeToolSurface：断言 left_click_drag 转成 drag_path；如果没有这一行，拖拽路径不会对齐现有 controller。
        self.assertEqual(controller.calls[2]["points"][0]["x"], 1)  # 新增代码+ClaudeCodeToolSurface：断言拖拽起点 x 被传入；如果没有这一行，坐标转换错误不会暴露。
        self.assertEqual(controller.calls[3]["action"], "screenshot")  # 新增代码+ClaudeCodeToolSurface：断言 zoom 走 screenshot；如果没有这一行，zoom 可能落入未知动作。
        self.assertTrue(controller.calls[3]["zoom"])  # 新增代码+ClaudeCodeToolSurface：断言 zoom 标志传给 controller；如果没有这一行，局部放大语义会丢失。
        self.assertEqual(controller.calls[4]["action"], "press_key")  # 新增代码+ClaudeCodeToolSurface：断言 hold_key 复用受控按键执行；如果没有这一行，按键保持工具可能映射到未知动作。
        self.assertEqual(controller.calls[4]["hold_duration_seconds"], 1.25)  # 新增代码+ClaudeCodeToolSurface：断言 hold_key 传递保持秒数；如果没有这一行，长按会退化成普通短按。
    # 新增代码+ClaudeCodeToolSurface：函数段结束，test_executor_maps_claudecode_style_aliases_to_controller 到此结束；如果没有这个边界说明，用户不容易看出映射测试范围。

    # 新增代码+ClaudeCodeToolSurface：函数段开始，test_executor_supports_split_clipboard_tools_and_reserved_failures 检查剪贴板新名和预留工具；如果没有这段测试，读写剪贴板和 unsupported 语义可能回归。
    def test_executor_supports_split_clipboard_tools_and_reserved_failures(self) -> None:  # 新增代码+ClaudeCodeToolSurface：声明剪贴板和预留工具测试；如果没有这一行，read_clipboard/write_clipboard 合同没有保护。
        controller = _RecordingController()  # 新增代码+ClaudeCodeToolSurface：创建记录型 controller；如果没有这一行，无法确认预留工具没有误触底层动作。
        context = ComputerUseMcpExecutionContext(controller_factory=lambda: controller)  # 新增代码+ClaudeCodeToolSurface：注入记录 controller；如果没有这一行，测试可能触达真实桌面后端。
        write_result = call_computer_use_mcp_tool("write_clipboard", {"text": "hello"}, context)  # 新增代码+ClaudeCodeToolSurface：调用拆分后的写剪贴板工具；如果没有这一行，写剪贴板路径没有测试输入。
        read_result = call_computer_use_mcp_tool("read_clipboard", {}, context)  # 新增代码+ClaudeCodeToolSurface：调用拆分后的读剪贴板工具；如果没有这一行，读剪贴板路径没有测试输入。
        reserved_result = call_computer_use_mcp_tool("triple_click", {"x": 1, "y": 2}, context)  # 新增代码+ClaudeCodeToolSurface：调用暂未成熟的预留工具；如果没有这一行，unsupported 语义没有保护。
        down_result = call_computer_use_mcp_tool("left_mouse_down", {"x": 1, "y": 2}, context)  # 新增代码+ClaudeCodeToolSurface：调用预留左键按下工具；如果没有这一行，left_mouse_down 可能假成功或误触 controller。
        up_result = call_computer_use_mcp_tool("left_mouse_up", {"x": 1, "y": 2}, context)  # 新增代码+ClaudeCodeToolSurface：调用预留左键释放工具；如果没有这一行，left_mouse_up 可能假成功或误触 controller。
        self.assertTrue(write_result["ok"])  # 新增代码+ClaudeCodeToolSurface：断言写剪贴板成功；如果没有这一行，写入失败不会暴露。
        self.assertTrue(read_result["ok"])  # 新增代码+ClaudeCodeToolSurface：断言读剪贴板成功；如果没有这一行，读取失败不会暴露。
        self.assertEqual(read_result["payload"]["text"], "hello")  # 新增代码+ClaudeCodeToolSurface：断言读回刚写入的文本；如果没有这一行，剪贴板闭环断开不会暴露。
        self.assertFalse(reserved_result["ok"])  # 新增代码+ClaudeCodeToolSurface：断言预留工具当前明确失败；如果没有这一行，未实现工具可能假成功。
        self.assertEqual(reserved_result["error_class"], "unsupported_computer_use_tool")  # 新增代码+ClaudeCodeToolSurface：断言失败类别是 unsupported；如果没有这一行，模型无法区分未实现和参数错误。
        self.assertFalse(down_result["ok"])  # 新增代码+ClaudeCodeToolSurface：断言 left_mouse_down 当前明确失败；如果没有这一行，未实现拆分动作可能假成功。
        self.assertFalse(up_result["ok"])  # 新增代码+ClaudeCodeToolSurface：断言 left_mouse_up 当前明确失败；如果没有这一行，未实现拆分动作可能假成功。
        self.assertEqual(down_result["error_class"], "unsupported_computer_use_tool")  # 新增代码+ClaudeCodeToolSurface：断言 left_mouse_down 的失败类别明确；如果没有这一行，模型无法知道这是暂未实现。
        self.assertEqual(up_result["error_class"], "unsupported_computer_use_tool")  # 新增代码+ClaudeCodeToolSurface：断言 left_mouse_up 的失败类别明确；如果没有这一行，模型无法知道这是暂未实现。
        self.assertEqual(controller.calls, [])  # 新增代码+ClaudeCodeToolSurface：断言剪贴板和预留工具没有误触 controller；如果没有这一行，预留工具可能真实动鼠标。
    # 新增代码+ClaudeCodeToolSurface：函数段结束，test_executor_supports_split_clipboard_tools_and_reserved_failures 到此结束；如果没有这个边界说明，用户不容易看出剪贴板测试范围。

    # 新增代码+ComputerUseMCP：函数段开始，test_selftest_cli_reports_ready_marker 检查命令行自检；如果没有这段测试，server 文件可能无法独立启动。
    def test_selftest_cli_reports_ready_marker(self) -> None:  # 新增代码+ComputerUseMCP：声明 selftest CLI 测试；如果没有这行代码，命令行入口没有保护。
        completed = subprocess.run([sys.executable, str(self._server_path()), "--selftest"], cwd=str(self._project_root()), text=True, capture_output=True, timeout=10, check=False)  # 新增代码+ComputerUseMCP：启动真实 server 自检；如果没有这行代码，无法验证脚本模式导入和退出码。
        self.assertEqual(completed.returncode, 0, completed.stderr)  # 新增代码+ComputerUseMCP：断言自检退出成功；如果没有这行代码，失败也可能继续解析输出。
        self.assertIn(COMPUTER_USE_MCP_READY_MARKER, completed.stdout)  # 新增代码+ComputerUseMCP：断言输出固定 marker；如果没有这行代码，验收脚本缺少稳定锚点。
        report = json.loads(completed.stdout.splitlines()[0])  # 新增代码+ComputerUseMCP：解析第一行 JSON 报告；如果没有这行代码，无法检查详细字段。
        self.assertTrue(report["passed"])  # 新增代码+ComputerUseMCP：断言 selftest 总结通过；如果没有这行代码，marker 单独出现也可能是假阳性。
        self.assertTrue(report["no_shell_surface"])  # 新增代码+ComputerUseMCP：断言自检确认无 shell 面；如果没有这行代码，自检可能只证明有工具。
    # 新增代码+ComputerUseMCP：函数段结束，test_selftest_cli_reports_ready_marker 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 自检测试范围。

    # 新增代码+ComputerUseMCP：函数段开始，test_real_stdio_server_is_discovered_by_registry 检查真实 stdio 注册；如果没有这段测试，mcp_servers.json 接入可能表面成功但 registry 读不到工具。
    def test_real_stdio_server_is_discovered_by_registry(self) -> None:  # 新增代码+ComputerUseMCP：声明真实 stdio registry 测试；如果没有这行代码，server 和 registry 的协议兼容性没有保护。
        config = McpServerConfig(name="computer-use", command=sys.executable, args=[str(self._server_path())])  # 新增代码+ComputerUseMCP：构造真实 stdio server 配置；如果没有这行代码，registry 没有启动目标。
        registry = McpToolRegistry.from_configs([config])  # 新增代码+ComputerUseMCP：通过正式工厂创建 registry；如果没有这行代码，测试绕不开真实配置路径。
        try:  # 新增代码+ComputerUseMCP：确保测试结束关闭子进程；如果没有这行代码，server 可能残留。
            registry.start()  # 新增代码+ComputerUseMCP：启动 server 并读取工具；如果没有这行代码，工具列表为空。
            tool_names = [schema["function"]["name"] for schema in registry.tool_schemas()]  # 新增代码+ComputerUseMCP：读取模型可见工具名；如果没有这行代码，无法确认发现结果。
            self.assertIn("mcp__computer-use__request_access", tool_names)  # 新增代码+ComputerUseMCP：断言授权工具被发现；如果没有这行代码，真实 stdio 接入失败不会暴露。
            output = registry.call_tool("mcp__computer-use__request_access", {"applications": ["Google Chrome"], "reason": "测试授权申请"})  # 修改代码+ComputerUseMcpV2：调用一个无桌面副作用的 v2 授权工具；如果没有这行代码，只能证明能列不能证明能调用。
            payload = json.loads(output)  # 修改代码+ComputerUseMcpV2：解析 v2 JSON 文本结果；如果没有这一行，测试只能靠旧 marker 判断成功。
            self.assertTrue(payload["ok"], payload)  # 修改代码+ComputerUseMcpV2：断言 request_access 成功；如果没有这一行，失败 JSON 也可能被误当作成功调用。
            self.assertEqual("computer_use_mcp_v2", payload["runtime"])  # 修改代码+ComputerUseMcpV2：断言真实 stdio 调用进入 v2 runtime；如果没有这一行，旧 executor 回归不会被发现。
            self.assertFalse(payload["legacy_adapter_used"])  # 修改代码+ComputerUseMcpV2：断言没有走旧 adapter；如果没有这一行，旧接口可能继续偷偷接管。
        finally:  # 新增代码+ComputerUseMCP：无论断言是否失败都清理 registry；如果没有这行代码，子进程泄漏会污染后续测试。
            registry.close()  # 新增代码+ComputerUseMCP：关闭 stdio server 子进程；如果没有这行代码，测试结束后 server 仍可能运行。
    # 新增代码+ComputerUseMCP：函数段结束，test_real_stdio_server_is_discovered_by_registry 到此结束；如果没有这个边界说明，初学者不容易看出真实 stdio 测试范围。

    # 新增代码+ComputerUseMCP：函数段开始，test_project_mcp_servers_registers_computer_use_server 检查真实配置；如果没有这段测试，mcp_servers.json 漏配 computer-use 不会被发现。
    def test_project_mcp_servers_registers_computer_use_server(self) -> None:  # 新增代码+ComputerUseMCP：声明 mcp_servers.json 注册测试；如果没有这行代码，独立 server 可能只在测试里存在。
        config_path = self._project_root() / "learning_agent" / "mcp_servers.json"  # 新增代码+ComputerUseMCP：定位项目真实 MCP 配置文件；如果没有这行代码，测试不知道检查哪个文件。
        payload = json.loads(config_path.read_text(encoding="utf-8"))  # 新增代码+ComputerUseMCP：读取并解析 mcp_servers.json；如果没有这行代码，配置格式错误不会暴露。
        servers = payload.get("servers", [])  # 新增代码+ComputerUseMCP：取得 server 配置数组；如果没有这行代码，后续无法遍历。
        computer_servers = [server for server in servers if server.get("name") == "computer-use"]  # 新增代码+ComputerUseMCP：筛选独立 Computer Use MCP 配置；如果没有这行代码，无法判断是否注册。
        self.assertEqual(len(computer_servers), 1)  # 新增代码+ComputerUseMCP：断言只注册一个 computer-use server；如果没有这行代码，缺失或重复配置都不会失败。
        self.assertIn("computer_use_server.py", " ".join(computer_servers[0].get("args", [])))  # 新增代码+ComputerUseMCP：断言配置指向独立 server 入口；如果没有这行代码，可能误配到旧脚本。
    # 新增代码+ComputerUseMCP：函数段结束，test_project_mcp_servers_registers_computer_use_server 到此结束；如果没有这个边界说明，初学者不容易看出配置测试范围。

    # 新增代码+ComputerUseMCP：函数段开始，test_acceptance_probe_and_visible_terminal_scenario_exist 检查验收资产；如果没有这段测试，真实终端验收入口可能被漏提交。
    def test_acceptance_probe_and_visible_terminal_scenario_exist(self) -> None:  # 新增代码+ComputerUseMCP：声明 acceptance 资产测试；如果没有这行代码，probe 和场景文件缺失不会被发现。
        probe_path = self._project_root() / "learning_agent" / "acceptance_controller" / "probes" / "computer_use_independent_mcp_server_probe.py"  # 新增代码+ComputerUseMCP：定位新增 probe；如果没有这行代码，测试无法运行探针。
        scenario_path = self._project_root() / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_computer_use_mcp_smoke_visible_terminal.json"  # 新增代码+ComputerUseMCP：定位真实终端场景；如果没有这行代码，测试无法检查场景配置。
        self.assertTrue(probe_path.exists())  # 新增代码+ComputerUseMCP：断言 probe 文件存在；如果没有这行代码，场景可能指向不存在脚本。
        self.assertTrue(scenario_path.exists())  # 新增代码+ComputerUseMCP：断言场景文件存在；如果没有这行代码，acceptance controller 没有复跑入口。
        completed = subprocess.run([sys.executable, str(probe_path)], cwd=str(self._project_root()), text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=20, check=False)  # 修改代码+ComputerUseMCP：直接运行 probe 并容忍 Windows 错误输出编码；如果没有这行代码，probe 失败时中文 stderr 可能先触发解码异常而掩盖根因。
        self.assertEqual(completed.returncode, 0, completed.stderr)  # 新增代码+ComputerUseMCP：断言 probe 成功退出；如果没有这行代码，失败 probe 也可能只靠场景文本存在而通过。
        self.assertIn(COMPUTER_USE_MCP_READY_MARKER, completed.stdout)  # 新增代码+ComputerUseMCP：断言 probe 输出固定标记；如果没有这行代码，真实终端场景无法稳定匹配成功。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+ComputerUseMCP：解析真实终端场景 JSON；如果没有这行代码，坏 JSON 不会被发现。
        self.assertTrue(scenario["visible_terminal_gate"])  # 新增代码+ComputerUseMCP：断言场景强制真实可见终端；如果没有这行代码，验收可能退化成纯自动化脚本。
        self.assertIn("/computer use --full", scenario["prompt_lines"])  # 新增代码+ComputerUseMCP：断言场景先打开 Computer Use full 模式；如果没有这行代码，模型主循环可能没有加载 computer_use 能力包。
        self.assertEqual("COMPUTER_USE_MCP_V2_VISIBLE_TERMINAL_OK", scenario["success_marker"])  # 修改代码+ComputerUseMCPVisibleGate：断言最终回答使用独立成功标记；如果没有这一行，缺证据失败句子可能因为包含 ready marker 而假阳性。
        self.assertNotIn(COMPUTER_USE_MCP_READY_MARKER, scenario["success_marker"])  # 新增代码+ComputerUseMCPVisibleGate：确认 probe marker 不会同时充当最终回答 marker；如果没有这一行，场景可能再次把“未看到 READY”误判成通过。
    # 新增代码+ComputerUseMCP：函数段结束，test_acceptance_probe_and_visible_terminal_scenario_exist 到此结束；如果没有这个边界说明，初学者不容易看出验收资产测试范围。


class _FakeMcpClient:  # 新增代码+ComputerUseMCP：定义 registry 测试用 fake client；如果没有这段类，命名测试需要启动真实子进程。
    # 新增代码+ComputerUseMCP：函数段开始，__init__ 保存工具列表；如果没有这段函数，fake client 没有可返回的 tools。
    def __init__(self, tools: list[dict[str, object]]) -> None:  # 新增代码+ComputerUseMCP：声明 fake 初始化入口；如果没有这行代码，测试无法注入工具清单。
        self.tools = tools  # 新增代码+ComputerUseMCP：保存工具清单；如果没有这行代码，list_tools 会返回空。
    # 新增代码+ComputerUseMCP：函数段结束，__init__ 到此结束；如果没有这个边界说明，初学者不容易看出 fake 初始化范围。

    # 新增代码+ComputerUseMCP：函数段开始，start 模拟 client 启动；如果没有这段函数，registry.start 会因缺方法失败。
    def start(self) -> None:  # 新增代码+ComputerUseMCP：声明 fake start；如果没有这行代码，registry 无法统一调用。
        return None  # 新增代码+ComputerUseMCP：fake 启动无需动作；如果没有这行代码，函数没有明确返回。
    # 新增代码+ComputerUseMCP：函数段结束，start 到此结束；如果没有这个边界说明，初学者不容易看出 fake 启动范围。

    # 新增代码+ComputerUseMCP：函数段开始，list_tools 返回工具清单；如果没有这段函数，registry 无法发现 fake 工具。
    def list_tools(self) -> list[dict[str, object]]:  # 新增代码+ComputerUseMCP：声明 fake tools/list；如果没有这行代码，测试无法模拟 MCP server。
        return self.tools  # 新增代码+ComputerUseMCP：返回注入工具；如果没有这行代码，registry 看不到 computer-use 工具。
    # 新增代码+ComputerUseMCP：函数段结束，list_tools 到此结束；如果没有这个边界说明，初学者不容易看出 fake list 范围。

    # 新增代码+ComputerUseMCP：函数段开始，close 兼容 registry 清理；如果没有这段函数，registry.close 会失败。
    def close(self) -> None:  # 新增代码+ComputerUseMCP：声明 fake close；如果没有这行代码，测试清理路径不完整。
        return None  # 新增代码+ComputerUseMCP：fake 关闭无需动作；如果没有这行代码，函数没有明确返回。
    # 新增代码+ComputerUseMCP：函数段结束，close 到此结束；如果没有这个边界说明，初学者不容易看出 fake close 范围。


class _ExplodingController:  # 新增代码+ComputerUseMCP：定义拒绝前不应被调用的 controller；如果没有这段类，无法证明 shell 参数被提前拦截。
    # 新增代码+ComputerUseMCP：函数段开始，execute 遇调用就失败；如果没有这段函数，危险参数可能触达 controller 而测试不知道。
    def execute(self, arguments: dict[str, object]) -> object:  # 新增代码+ComputerUseMCP：声明爆炸 execute；如果没有这行代码，executor 调用 controller 时没有失败信号。
        raise AssertionError(f"controller should not be called: {arguments}")  # 新增代码+ComputerUseMCP：抛出明确测试失败；如果没有这行代码，安全拦截顺序无法验证。
    # 新增代码+ComputerUseMCP：函数段结束，execute 到此结束；如果没有这个边界说明，初学者不容易看出爆炸 controller 范围。


class _RecordingSessionAdapter:  # 新增代码+McpSessionAdapter: 定义记录型 session adapter；如果没有这段类，mcp_executor 的 adapter 优先级测试没有可观测对象。
    # 新增代码+McpSessionAdapter: 函数段开始，__init__ 初始化调用记录；如果没有这段函数，fake adapter 没有地方保存调用历史。
    def __init__(self) -> None:  # 新增代码+McpSessionAdapter: 声明 fake adapter 初始化入口；如果没有这一行，测试无法创建对象。
        self.calls: list[tuple[str, dict[str, object]]] = []  # 新增代码+McpSessionAdapter: 保存 adapter 收到的工具名和参数；如果没有这一行，测试无法断言是否真正委托。
    # 新增代码+McpSessionAdapter: 函数段结束，__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake 初始化范围。

    # 新增代码+McpSessionAdapter: 函数段开始，call_atomic_tool 模拟 adapter 执行；如果没有这段函数，mcp_executor 无法调用 fake adapter。
    def call_atomic_tool(self, tool_name: str, arguments: dict[str, object]) -> dict[str, object]:  # 新增代码+McpSessionAdapter: 声明 fake adapter 执行入口；如果没有这一行，委托路径会属性错误。
        self.calls.append((tool_name, dict(arguments)))  # 新增代码+McpSessionAdapter: 记录本次委托；如果没有这一行，测试无法证明 controller 被绕开。
        return {"ok": True, "tool_name": tool_name, "error_class": "", "payload": {"adapter_called": True}, "text": "adapter called"}  # 新增代码+McpSessionAdapter: 返回统一形态的成功结果；如果没有这一行，mcp_executor 调用方拿不到结果。
    # 新增代码+McpSessionAdapter: 函数段结束，call_atomic_tool 到此结束；如果没有这个边界说明，用户不容易看出 fake adapter 执行范围。


class _RecordingController:  # 新增代码+ClaudeCodeToolSurface：定义记录型 controller；如果没有这段类，测试无法确认 executor 映射到哪个底层 action。
    # 新增代码+ClaudeCodeToolSurface：函数段开始，__init__ 初始化调用记录；如果没有这段函数，controller 没有保存 calls 的地方。
    def __init__(self) -> None:  # 新增代码+ClaudeCodeToolSurface：声明记录 controller 初始化入口；如果没有这一行，测试无法创建对象。
        self.calls: list[dict[str, object]] = []  # 新增代码+ClaudeCodeToolSurface：保存每次 execute 参数；如果没有这一行，测试无法检查 action/button/points。
    # 新增代码+ClaudeCodeToolSurface：函数段结束，__init__ 到此结束；如果没有这个边界说明，用户不容易看出记录初始化范围。

    # 新增代码+ClaudeCodeToolSurface：函数段开始，execute 记录参数并返回成功；如果没有这段函数，mcp executor 调用 controller 时会失败。
    def execute(self, arguments: dict[str, object]) -> object:  # 新增代码+ClaudeCodeToolSurface：声明 fake execute；如果没有这一行，执行器没有可调用后端。
        self.calls.append(dict(arguments))  # 新增代码+ClaudeCodeToolSurface：保存本次 controller 参数；如果没有这一行，测试无法验证映射结果。
        return _ControllerResult(ok=True, message="recorded", data={"action": arguments.get("action", "")})  # 新增代码+ClaudeCodeToolSurface：返回成功结果对象；如果没有这一行，executor 无法包装成功输出。
    # 新增代码+ClaudeCodeToolSurface：函数段结束，execute 到此结束；如果没有这个边界说明，用户不容易看出 fake 执行范围。


class _ControllerResult:  # 新增代码+ClaudeCodeToolSurface：定义最小 controller 结果对象；如果没有这段类，_result_from_controller 无法读取 ok/message/data。
    # 新增代码+ClaudeCodeToolSurface：函数段开始，__init__ 保存 controller 结果字段；如果没有这段函数，结果对象没有 executor 需要的属性。
    def __init__(self, ok: bool, message: str, data: dict[str, object]) -> None:  # 新增代码+ClaudeCodeToolSurface：声明结果初始化入口；如果没有这一行，测试无法构造 controller 返回值。
        self.ok = ok  # 新增代码+ClaudeCodeToolSurface：保存是否成功；如果没有这一行，executor 会把结果当失败。
        self.message = message  # 新增代码+ClaudeCodeToolSurface：保存结果说明；如果没有这一行，payload.message 会缺失。
        self.data = data  # 新增代码+ClaudeCodeToolSurface：保存结果数据；如果没有这一行，payload.data 会缺失。
    # 新增代码+ClaudeCodeToolSurface：函数段结束，__init__ 到此结束；如果没有这个边界说明，用户不容易看出结果对象范围。


if __name__ == "__main__":  # 新增代码+ComputerUseMCP：允许直接运行本测试文件；如果没有这行代码，手动调试不方便。
    unittest.main()  # 新增代码+ComputerUseMCP：启动 unittest 主程序；如果没有这行代码，直接运行不会执行测试。
