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


class Phase49FakeTargetSessionRuntime:  # 新增代码+ModelLoopLaunchAppTool: 类段开始，模拟通用目标 session runtime；如果没有这个类，controller 启动动作测试只能真的打开本机软件。
    def __init__(self) -> None:  # 新增代码+ModelLoopLaunchAppTool: 函数段开始，初始化 fake runtime 调用记录；如果没有这段函数，测试无法证明 controller 是否调用了目标 session。
        self.calls: list[dict[str, object]] = []  # 新增代码+ModelLoopLaunchAppTool: 保存每次 open_target_session 的参数；如果没有这行代码，测试只能从返回值猜测启动链路。
    # 新增代码+ModelLoopLaunchAppTool: 函数段结束，Phase49FakeTargetSessionRuntime.__init__ 到此结束；如果没有这个边界说明，读者不容易看出 fake 初始化范围。

    def open_target_session(self, raw_target: object, candidates: object | None = None, user_authorized_window: bool = False) -> dict[str, object]:  # 新增代码+ModelLoopLaunchAppTool: 函数段开始，返回 agent 自有窗口形状；如果没有这段函数，controller 无法在单测里拿到目标窗口凭证。
        self.calls.append({"raw_target": raw_target, "candidates": candidates, "user_authorized_window": user_authorized_window})  # 新增代码+ModelLoopLaunchAppTool: 记录本次目标；如果没有这行代码，测试无法确认模型给出的 app_name 被保留下来。
        return {"session_ready": True, "session_id": "phase49-launch-session", "canonical_target": str(raw_target), "target_window": {"app_id": f"{raw_target}.exe", "window_id": "hwnd:4901", "pid": 4901, "title_preview": "Phase49 Launched Window", "rect": {"left": 10, "top": 20, "right": 510, "bottom": 420}}, "real_launch_performed": True, "backend_launch_performed": True, "process_started": True, "owned_process_registered": True, "visible_window_verified": True, "agent_owned_or_user_authorized_window": True, "target_identity_bound": True, "target_identity_rechecked_before_each_action": True, "low_level_event_count": 0, "real_desktop_touched": True}  # 新增代码+ModelLoopLaunchAppTool: 返回真实启动报告的安全 fake 形状；如果没有这行代码，controller 无法把启动结果交给模型后续观察。
    # 新增代码+ModelLoopLaunchAppTool: 函数段结束，Phase49FakeTargetSessionRuntime.open_target_session 到此结束；如果没有这个边界说明，读者不容易看出 fake 返回范围。
# 新增代码+ModelLoopLaunchAppTool: 类段结束，Phase49FakeTargetSessionRuntime 到此结束；如果没有这个边界说明，读者不容易看出 fake runtime 范围。


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
        self.assertEqual(compat_parameters["properties"]["operation"]["enum"], ["status", "discover", "observe", "action"])  # 修改代码+ComputerDiscoverTool：断言模型可见 operation 包含只读 discover 和主循环工具动作；如果没有这行代码，旧测试会把新增应用发现层误判成旧黑盒入口。
        self.assertNotIn("mode", compat_parameters["properties"]["operation"]["enum"])  # 修改代码+ModelLoopSemanticPlanner: 明确禁止把 mode 当成模型可选操作；如果没有这行代码，语义规划可能再次绕过模型主循环。
        self.assertNotIn("run_prompt", compat_parameters["properties"]["operation"]["enum"])  # 修改代码+ModelLoopSemanticPlanner: 明确禁止把 run_prompt 当成模型可选操作；如果没有这行代码，自然语言任务可能被重新交给黑盒 runtime。
        action_parameters = schemas_by_name["computer_action"]["function"]["parameters"]  # 新增代码+ModelLoopLaunchAppTool: 读取动作工具 schema；如果没有这行代码，测试无法确认模型是否能看到启动应用动作。
        self.assertIn("launch_app", action_parameters["properties"]["action"]["enum"])  # 新增代码+ModelLoopLaunchAppTool: 断言模型可见 launch_app；如果没有这行代码，agent 会继续只能在已有窗口里乱点鼠标。
        self.assertIn("app_name", action_parameters["properties"])  # 新增代码+ModelLoopLaunchAppTool: 断言动作参数暴露 app_name；如果没有这行代码，模型无法表达要打开哪个软件。
        self.assertIn("target_app", action_parameters["properties"])  # 新增代码+ModelLoopLaunchAppTool: 断言动作参数暴露 target_app 别名；如果没有这行代码，不同模型习惯的字段无法稳定兼容。
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

    def test_launch_app_routes_to_generic_target_session_instead_of_mouse_keyboard_backend(self) -> None:  # 新增代码+ModelLoopLaunchAppTool: 函数段开始，验证 launch_app 接到通用目标 session；如果没有这个测试，模型主循环仍可能无法自己打开软件。
        backend = MemoryComputerUseBackend()  # 新增代码+ModelLoopLaunchAppTool: 创建内存后端证明启动动作不该落到鼠标键盘执行器；如果没有这行代码，测试无法发现错误路由。
        target_runtime = Phase49FakeTargetSessionRuntime()  # 新增代码+ModelLoopLaunchAppTool: 创建 fake 目标 session runtime；如果没有这行代码，测试会依赖真实 Windows 启动。
        controller = ComputerUseController(backend=backend, target_session_runtime=target_runtime)  # 新增代码+ModelLoopLaunchAppTool: 把 fake runtime 注入 controller；如果没有这行代码，launch_app 不能在单测中可控验证。
        result = controller.execute({"action": "launch_app", "confirm_desktop_control": True, "app_name": "mspaint"})  # 新增代码+ModelLoopLaunchAppTool: 请求打开 Paint；如果没有这行代码，测试没有覆盖用户自然语言里的“打开软件”能力。
        self.assertTrue(result.ok)  # 新增代码+ModelLoopLaunchAppTool: 断言启动动作成功；如果没有这行代码，controller 可能仍把 launch_app 当未知动作拒绝。
        self.assertEqual([], backend.actions)  # 新增代码+ModelLoopLaunchAppTool: 断言启动没有落到鼠标键盘后端；如果没有这行代码，启动动作可能被错误当成普通输入动作。
        self.assertEqual("mspaint", target_runtime.calls[0]["raw_target"])  # 新增代码+ModelLoopLaunchAppTool: 断言 app_name 被传给通用目标 session；如果没有这行代码，模型意图可能在路由中丢失。
        self.assertEqual("launch_app", result.data["action_class"])  # 新增代码+ModelLoopLaunchAppTool: 断言返回数据标记启动动作类别；如果没有这行代码，真实终端验收不容易区分启动和普通点击。
        self.assertEqual("hwnd:4901", result.data["target_window"]["window_id"])  # 新增代码+ModelLoopLaunchAppTool: 断言返回可继续观察的窗口引用；如果没有这行代码，模型打开软件后不知道下一步观察哪个窗口。
    # 新增代码+ModelLoopLaunchAppTool: 函数段结束，test_launch_app_routes_to_generic_target_session_instead_of_mouse_keyboard_backend 到此结束；如果没有这个边界说明，读者不容易看出 launch_app 路由范围。

    def test_launch_app_skips_polluted_app_name_and_uses_clean_target_alias(self) -> None:  # 新增代码+ModelLoopLaunchAppTool: 函数段开始，复现真实终端里 app_name 被长文本污染的问题；如果没有这个测试，模型可能再次把历史回答当成 exe。
        backend = MemoryComputerUseBackend()  # 新增代码+ModelLoopLaunchAppTool: 创建内存后端避免真实桌面动作；如果没有这行代码，测试可能打开本机软件。
        target_runtime = Phase49FakeTargetSessionRuntime()  # 新增代码+ModelLoopLaunchAppTool: 创建 fake 目标 session；如果没有这行代码，无法检查最终选择的应用名。
        controller = ComputerUseController(backend=backend, target_session_runtime=target_runtime)  # 新增代码+ModelLoopLaunchAppTool: 注入 fake runtime；如果没有这行代码，测试无法隔离启动路由。
        polluted_text = "mspaint 找到了问题：`tools/computer_use.py` 里有一大段历史解释\npython tools/computer_use.py action"  # 新增代码+ModelLoopLaunchAppTool: 构造真实验收中出现的污染 app_name 形状；如果没有这行代码，回归无法覆盖本次失败。
        result = controller.execute({"action": "launch_app", "confirm_desktop_control": True, "app_name": polluted_text, "target_app": "paint", "app": "paint", "target": "paint"})  # 新增代码+ModelLoopLaunchAppTool: 同时传污染 app_name 和干净别名；如果没有这行代码，无法证明 controller 会跳过坏字段。
        self.assertTrue(result.ok)  # 新增代码+ModelLoopLaunchAppTool: 断言污染字段没有导致启动失败；如果没有这行代码，真实终端仍会卡在 unsafe_generic_launch_plan_rejected。
        self.assertEqual("paint", target_runtime.calls[0]["raw_target"])  # 新增代码+ModelLoopLaunchAppTool: 断言最终使用干净 target_app；如果没有这行代码，长文本仍可能盖过有效目标。
    # 新增代码+ModelLoopLaunchAppTool: 函数段结束，test_launch_app_skips_polluted_app_name_and_uses_clean_target_alias 到此结束；如果没有这个边界说明，读者不容易看出污染字段回归范围。

    def test_launch_app_prefers_clean_alias_when_app_name_contains_chinese_task_sentence(self) -> None:  # 新增代码+LaunchTargetPollutionGate: 函数段开始，复现真实可见终端中中文任务句污染 app_name 的失败；如果没有这个测试，controller 可能再次把“画树说明”当成 exe 名。
        backend = MemoryComputerUseBackend()  # 新增代码+LaunchTargetPollutionGate: 创建不会触碰真实桌面的内存后端；如果没有这行代码，单测可能误启动本机软件。
        target_runtime = Phase49FakeTargetSessionRuntime()  # 新增代码+LaunchTargetPollutionGate: 创建可检查 raw_target 的 fake runtime；如果没有这行代码，测试无法证明最终启动目标是否干净。
        controller = ComputerUseController(backend=backend, target_session_runtime=target_runtime)  # 新增代码+LaunchTargetPollutionGate: 把 fake runtime 注入 controller；如果没有这行代码，测试不能隔离 controller 的字段选择逻辑。
        polluted_text = "mspaint，非常熟练地画一棵树。使用画笔或形状工具，画出棕色树干、绿色树冠和地面。"  # 新增代码+LaunchTargetPollutionGate: 构造真实日志里的中文污染 app_name；如果没有这行代码，回归测试不会覆盖本次失败形状。
        result = controller.execute({"action": "launch_app", "confirm_desktop_control": True, "app_name": polluted_text, "target_app": "mspaint", "app": "mspaint", "target": "mspaint"})  # 新增代码+LaunchTargetPollutionGate: 同时传污染 app_name 和干净别名；如果没有这行代码，无法验证 controller 是否优先使用模型给出的干净目标。
        self.assertTrue(result.ok)  # 新增代码+LaunchTargetPollutionGate: 断言启动路由仍然成功；如果没有这行代码，污染字段可能让 full 模式卡死在启动阶段。
        self.assertEqual("mspaint", target_runtime.calls[0]["raw_target"])  # 新增代码+LaunchTargetPollutionGate: 断言最终发送给启动 runtime 的是 mspaint；如果没有这行代码，长句污染会继续进入真实 Start-Process。
    # 新增代码+LaunchTargetPollutionGate: 函数段结束，test_launch_app_prefers_clean_alias_when_app_name_contains_chinese_task_sentence 到此结束；如果没有这个边界说明，读者不容易看出中文污染回归范围。

    def test_launch_app_skips_polluted_target_app_and_uses_clean_app_field(self) -> None:  # 新增代码+LaunchTargetPollutionGate: 函数段开始，复现 target_app 被自然语言污染的新失败；如果没有这个测试，模型把任务句塞进 target_app 时仍会启动失败。
        backend = MemoryComputerUseBackend()  # 新增代码+LaunchTargetPollutionGate: 创建内存后端隔离真实桌面；如果没有这行代码，测试可能触发真实鼠标键盘或启动软件。
        target_runtime = Phase49FakeTargetSessionRuntime()  # 新增代码+LaunchTargetPollutionGate: 创建 fake runtime 用来记录最终 raw_target；如果没有这行代码，无法验证污染字段是否被跳过。
        controller = ComputerUseController(backend=backend, target_session_runtime=target_runtime)  # 新增代码+LaunchTargetPollutionGate: 注入 fake runtime；如果没有这行代码，测试会依赖生产启动后端。
        polluted_target_app = "mspaint画图软件画一棵树."  # 新增代码+LaunchTargetPollutionGate: 构造第二次真实验收中出现的污染 target_app；如果没有这行代码，回归不会覆盖混合英文和中文任务句。
        result = controller.execute({"action": "launch_app", "confirm_desktop_control": True, "app_name": "mspaintowy?", "target_app": polluted_target_app, "app": "mspaint", "target": "mspaint"})  # 新增代码+LaunchTargetPollutionGate: 提供污染 target_app 和干净 app 字段；如果没有这行代码，无法证明 controller 会继续向后找干净目标。
        self.assertTrue(result.ok)  # 新增代码+LaunchTargetPollutionGate: 断言污染 target_app 不会导致启动失败；如果没有这行代码，full 模式可能再次卡在 launch_app。
        self.assertEqual("mspaint", target_runtime.calls[0]["raw_target"])  # 新增代码+LaunchTargetPollutionGate: 断言最终使用干净 app 字段；如果没有这行代码，坏 target_app 可能继续传入 Start-Process。
    # 新增代码+LaunchTargetPollutionGate: 函数段结束，test_launch_app_skips_polluted_target_app_and_uses_clean_app_field 到此结束；如果没有这个边界说明，读者不容易看出 target_app 污染回归范围。

    def test_launch_app_recovers_safe_prefix_from_model_json_repair_pollution(self) -> None:  # 新增代码+LaunchTargetRepairPollution: 函数段开始，复现真实终端里模型把 JSON 修复自言自语混进 app_name 的失败；如果没有这个测试，mspaint 前缀污染会继续让 launch_app 缺参拒绝。
        backend = MemoryComputerUseBackend()  # 新增代码+LaunchTargetRepairPollution: 创建内存后端避免触碰真实桌面；如果没有这行代码，红灯测试可能真的打开本机软件。
        target_runtime = Phase49FakeTargetSessionRuntime()  # 新增代码+LaunchTargetRepairPollution: 创建 fake 启动 runtime 记录最终目标；如果没有这行代码，无法证明污染串被恢复成哪个应用名。
        controller = ComputerUseController(backend=backend, target_session_runtime=target_runtime)  # 新增代码+LaunchTargetRepairPollution: 注入 fake runtime；如果没有这行代码，测试会依赖真实 launch 后端。
        polluted_app_name = "mspaint}}]} } ikwembu? Need valid JSON. I accidentally malformed. Need final only."  # 新增代码+LaunchTargetRepairPollution: 使用本次真实可见终端日志里的污染形状；如果没有这行代码，测试不会覆盖第 0 轮模型工具参数污染。
        result = controller.execute({"action": "launch_app", "confirm_desktop_control": True, "app_name": polluted_app_name})  # 新增代码+LaunchTargetRepairPollution: 只提供污染 app_name 且不提供干净别名；如果没有这行代码，无法证明 controller 能从单一坏字段安全恢复。
        self.assertTrue(result.ok)  # 新增代码+LaunchTargetRepairPollution: 断言已知安全前缀可以恢复成功；如果没有这行代码，真实终端仍会因缺少干净别名而启动失败。
        self.assertEqual("mspaint", target_runtime.calls[0]["raw_target"])  # 新增代码+LaunchTargetRepairPollution: 断言最终传给启动 runtime 的是干净 mspaint；如果没有这行代码，污染文本可能继续进入真实启动器。
    # 新增代码+LaunchTargetRepairPollution: 函数段结束，test_launch_app_recovers_safe_prefix_from_model_json_repair_pollution 到此结束；如果没有这个边界说明，读者不容易看出恢复范围。

    def test_actions_after_launch_app_reject_drift_to_preexisting_window(self) -> None:  # 新增代码+ModelLoopLaunchAppTool: 函数段开始，验证 launch_app 后不能漂移回旧窗口；如果没有这个测试，真实验收会继续误操作用户旧 Paint。
        owned_window = {"app_id": "mspaint.exe", "window_id": "hwnd:4901", "title_preview": "Owned Paint", "rect": {"left": 0, "top": 0, "right": 500, "bottom": 400}}  # 新增代码+ModelLoopLaunchAppTool: 构造 agent-owned 目标窗口；如果没有这行代码，测试没有正确窗口基准。
        old_window = {"app_id": "mspaint.exe", "window_id": "hwnd:old-user-window", "title_preview": "Old Paint", "rect": {"left": 0, "top": 0, "right": 500, "bottom": 400}}  # 新增代码+ModelLoopLaunchAppTool: 构造用户旧窗口；如果没有这行代码，漂移负例没有目标。
        backend = MemoryComputerUseBackend(windows=[owned_window, old_window])  # 新增代码+ModelLoopLaunchAppTool: 创建包含新旧两个窗口的内存后端；如果没有这行代码，旧窗口存在性无法复现。
        target_runtime = Phase49FakeTargetSessionRuntime()  # 新增代码+ModelLoopLaunchAppTool: 创建 fake 启动 runtime；如果没有这行代码，launch_app 会依赖真实桌面。
        target_runtime.open_target_session = lambda raw_target, candidates=None, user_authorized_window=False: {"session_ready": True, "session_id": "owned-session", "canonical_target": raw_target, "target_window": owned_window, "real_desktop_touched": True, "low_level_event_count": 0}  # 新增代码+ModelLoopLaunchAppTool: 覆盖 fake 返回 owned_window；如果没有这行代码，测试窗口身份和 fake 默认值不一致。
        controller = ComputerUseController(backend=backend, target_session_runtime=target_runtime)  # 新增代码+ModelLoopLaunchAppTool: 注入 fake runtime 和内存后端；如果没有这行代码，无法隔离漂移门禁。
        launch_result = controller.execute({"action": "launch_app", "confirm_desktop_control": True, "app_name": "mspaint"})  # 新增代码+ModelLoopLaunchAppTool: 先建立 active agent-owned target；如果没有这行代码，后续漂移门禁没有基准。
        drift_result = controller.execute({"action": "click", "confirm_desktop_control": True, "window": old_window, "x": 10, "y": 10})  # 新增代码+ModelLoopLaunchAppTool: 尝试点击旧窗口；如果没有这行代码，测试无法证明漂移被拒绝。
        self.assertTrue(launch_result.ok)  # 新增代码+ModelLoopLaunchAppTool: 断言启动基准成功；如果没有这行代码，后续失败原因可能不是漂移门禁。
        self.assertFalse(drift_result.ok)  # 新增代码+ModelLoopLaunchAppTool: 断言旧窗口动作被拒绝；如果没有这行代码，漂移问题会回归。
        self.assertIn("agent-owned", drift_result.message)  # 新增代码+ModelLoopLaunchAppTool: 断言拒绝原因明确指向自有窗口；如果没有这行代码，模型不知道该改用哪个窗口。
        self.assertEqual(0, len(backend.actions))  # 新增代码+ModelLoopLaunchAppTool: 断言漂移拒绝没有触发后端鼠标事件；如果没有这行代码，拒绝路径可能仍发送输入。
    # 新增代码+ModelLoopLaunchAppTool: 函数段结束，test_actions_after_launch_app_reject_drift_to_preexisting_window 到此结束；如果没有这个边界说明，读者不容易看出漂移回归范围。

    def test_observe_after_launch_app_rejects_drift_to_preexisting_window(self) -> None:  # 新增代码+ComputerUseSessionTargetGuard：函数段开始，验证 launch_app 后只读观察也不能漂移回旧窗口；如果没有这个测试，旧窗口截图会继续进入模型上下文污染下一步规划。
        owned_window = {"app_id": "mspaint.exe", "window_id": "hwnd:owned-window", "title_preview": "Owned Paint", "rect": {"left": 0, "top": 0, "right": 500, "bottom": 400}}  # 新增代码+ComputerUseSessionTargetGuard：构造本次 agent 自己打开的目标窗口；如果没有这行代码，测试没有正确窗口基准。
        old_window = {"app_id": "mspaint.exe", "window_id": "hwnd:old-user-window", "title_preview": "Old Paint", "rect": {"left": 0, "top": 0, "right": 500, "bottom": 400}}  # 新增代码+ComputerUseSessionTargetGuard：构造用户遗留旧窗口；如果没有这行代码，测试无法复现旧截图污染。
        backend = MemoryComputerUseBackend(windows=[owned_window, old_window])  # 新增代码+ComputerUseSessionTargetGuard：创建同时包含新旧窗口的内存后端；如果没有这行代码，observe 漂移没有真实候选。
        target_runtime = Phase49FakeTargetSessionRuntime()  # 新增代码+ComputerUseSessionTargetGuard：创建 fake 启动 runtime；如果没有这行代码，单元测试会依赖真实桌面启动。
        target_runtime.open_target_session = lambda raw_target, candidates=None, user_authorized_window=False: {"session_ready": True, "session_id": "owned-session", "canonical_target": raw_target, "target_window": owned_window, "real_desktop_touched": True, "low_level_event_count": 0}  # 新增代码+ComputerUseSessionTargetGuard：让 launch_app 稳定绑定 owned_window；如果没有这行代码，测试无法控制 active target。
        controller = ComputerUseController(backend=backend, target_session_runtime=target_runtime)  # 新增代码+ComputerUseSessionTargetGuard：注入 fake runtime 和内存后端；如果没有这行代码，测试无法隔离 observe 门禁。
        launch_result = controller.execute({"action": "launch_app", "confirm_desktop_control": True, "app_name": "mspaint"})  # 新增代码+ComputerUseSessionTargetGuard：先建立本次 agent-owned 目标窗口；如果没有这行代码，observe 门禁没有会话目标。
        drift_observe = controller.observe({"action": "get_window_state", "window": old_window})  # 新增代码+ComputerUseSessionTargetGuard：尝试观察旧窗口；如果没有这行代码，测试不会覆盖旧截图进入模型上下文的问题。
        self.assertTrue(launch_result.ok)  # 新增代码+ComputerUseSessionTargetGuard：确认启动绑定成功；如果没有这行代码，后续拒绝可能不是目标漂移导致。
        self.assertFalse(drift_observe.ok)  # 新增代码+ComputerUseSessionTargetGuard：断言旧窗口观察被拒绝；如果没有这行代码，旧窗口截图污染会继续回归。
        self.assertTrue(drift_observe.data.get("target_drift_blocks_action"))  # 新增代码+ComputerUseSessionTargetGuard：断言结构化结果携带目标漂移原因；如果没有这行代码，模型难以判断下一步应回到 owned window。
        self.assertIn("agent-owned", drift_observe.message)  # 新增代码+ComputerUseSessionTargetGuard：断言人类可读信息点明 agent-owned 目标；如果没有这行代码，终端复盘不清楚为什么拒绝。
    # 新增代码+ComputerUseSessionTargetGuard：函数段结束，test_observe_after_launch_app_rejects_drift_to_preexisting_window 到此结束；如果没有这个边界说明，读者不容易看出 observe 漂移门禁范围。

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
