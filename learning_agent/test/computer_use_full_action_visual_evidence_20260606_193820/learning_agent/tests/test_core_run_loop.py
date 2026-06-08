"Core run loop, config, tasks, and fallback tests."  # Stage14: this file owns the core_run_loop test group.
from __future__ import annotations  # Stage14: keep annotations lazy after test split.
import unittest  # Stage14: keep direct unittest execution available.
from learning_agent.tests.support import *  # Stage14: import shared helpers and dependencies for copied tests.

class CoreRunLoopTests(LearningAgentTestBase):  # Stage14: unittest discovers this concrete modular test class.
    def test_desktop_natural_language_reaches_model_loop_instead_of_preloop_runtime(self) -> None:  # 新增代码+ModelLoopComputerUse：函数段开始，验证自然语言桌面任务必须进入模型主循环；如果没有这个测试，Python 抢跑分类器可能再次替模型规划桌面任务。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ModelLoopComputerUse：创建临时 workspace 隔离 harness 和 debug 日志；如果没有这一行，测试会污染真实项目 memory。
            workspace = Path(raw_dir)  # 新增代码+ModelLoopComputerUse：把临时目录转成 Path；如果没有这一行，LearningAgent 构造参数会退回不清晰的字符串路径。
            model = RecordingToolNameFakeModel(ModelMessage(text="模型主循环收到桌面任务。"))  # 新增代码+ModelLoopComputerUse：构造会记录工具 schema 的假模型；如果没有这一行，测试无法证明 agent.run 真的调用了模型。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+ModelLoopComputerUse：创建真实 agent 并注入假模型；如果没有这一行，被测主循环入口不存在。
            answer = agent.run("请使用本地电脑的画图软件画一个房子。", max_turns=1)  # 新增代码+ModelLoopComputerUse：用真实用户习惯的桌面任务 prompt 运行 agent；如果没有这一行，模型前抢跑缺陷不会被触发。
            self.assertIn("模型主循环收到桌面任务", answer)  # 新增代码+ModelLoopComputerUse：断言最终回答来自模型主循环；如果没有这一行，旧 Computer Use runtime 抢跑也可能被误判通过。
            self.assertTrue(model.received_tool_names)  # 新增代码+ModelLoopComputerUse：断言假模型确实收到过工具列表；如果没有这一行，只看文本无法排除旁路返回。
            self.assertNotIn("Computer Use Desktop Task", answer)  # 新增代码+ModelLoopComputerUse：断言旧桌面任务 runtime 标题没有出现在答案中；如果没有这一行，旧抢跑路由可能继续混入。
    # 新增代码+ModelLoopComputerUse：函数段结束，test_desktop_natural_language_reaches_model_loop_instead_of_preloop_runtime 到此结束；如果没有这个边界说明，代码小白不容易看出模型主循环门禁范围。

    def test_computer_use_full_terminal_command_loads_tool_pack_for_next_model_turn(self) -> None:  # 新增代码+ModelLoopComputerUse：函数段开始，验证 `/computer use --full` 会把桌面工具 schema 挂到当前 agent；如果没有这个测试，用户下一句自然语言仍可能没有 computer_use 工具。
        from learning_agent.app.interactive import _activate_computer_use_tool_pack_for_agent  # 新增代码+ModelLoopComputerUse：导入交互层接线 helper；如果没有这一行，测试无法覆盖真实终端命令到工具池的桥。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ModelLoopComputerUse：创建临时 workspace；如果没有这一行，测试可能写入真实项目调试目录。
            workspace = Path(raw_dir)  # 新增代码+ModelLoopComputerUse：把临时目录转成 Path；如果没有这一行，agent 构造路径不够明确。
            agent = LearningAgent(model=RecordingToolNameFakeModel(ModelMessage(text="ok")), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+ModelLoopComputerUse：创建真实 agent 来使用正式 capability pack 逻辑；如果没有这一行，测试只能验证孤立字符串。
            output = _activate_computer_use_tool_pack_for_agent(agent, "/computer use --full", "Computer Use Mode\n- mode=full\n- full_mode=true\n")  # 新增代码+ModelLoopComputerUse：模拟终端 full 模式成功输出并触发工具包加载；如果没有这一行，用户真实命令路径没有自动化门禁。
            self.assertIn("model_loop_tools_loaded=true", output)  # 新增代码+ModelLoopComputerUse：断言 helper 报告工具包已进入模型主循环；如果没有这一行，失败输出可能被忽略。
            self.assertIn("computer_use", agent.loaded_tool_names)  # 新增代码+ModelLoopComputerUse：断言兼容 computer_use 入口进入当前工具池；如果没有这一行，模型无法用统一工具发 observe/action。
            self.assertIn("computer_observe", agent.loaded_tool_names)  # 新增代码+ModelLoopComputerUse：断言观察工具进入当前工具池；如果没有这一行，模型无法先看屏幕状态。
            self.assertIn("computer_action", agent.loaded_tool_names)  # 新增代码+ModelLoopComputerUse：断言动作工具进入当前工具池；如果没有这一行，模型无法通过工具层点击、输入或执行桌面动作。
    # 新增代码+ModelLoopComputerUse：函数段结束，test_computer_use_full_terminal_command_loads_tool_pack_for_next_model_turn 到此结束；如果没有这个边界说明，代码小白不容易看出 full 命令接线门禁范围。

    def test_computer_use_full_desktop_prompt_adds_model_loop_harness_and_uses_tools(self) -> None:  # 新增代码+ModelLoopSemanticPlanner：函数段开始，验证 full 模式后的自然语言桌面任务在模型主循环里规划；如果没有这个测试，语义任务可能再次被 Python runtime 抢跑。
        from learning_agent.app.interactive import _activate_computer_use_tool_pack_for_agent  # 新增代码+ModelLoopSemanticPlanner：导入真实交互 helper 来模拟用户输入 /computer use --full；如果没有这一行，测试无法覆盖真实终端命令接线。
        class RecordingDesktopLoopModel:  # 新增代码+ModelLoopSemanticPlanner：类段开始，用假模型记录消息和工具并主动选择 observe；如果没有这个类，测试无法证明模型拿到了语义规划上下文。
            def __init__(self) -> None:  # 新增代码+ModelLoopSemanticPlanner：初始化 fake 模型状态；如果没有这一行，后续无法记录 chat 调用。
                self.received_messages: list[list[dict[str, object]]] = []  # 新增代码+ModelLoopSemanticPlanner：保存每轮模型看到的 messages；如果没有这一行，测试无法检查系统提示是否包含模型循环 harness。
                self.received_tool_names: list[list[str]] = []  # 新增代码+ModelLoopSemanticPlanner：保存每轮模型看到的工具名；如果没有这一行，测试无法证明 computer_use 工具真的暴露给模型。
                self.index = 0  # 新增代码+ModelLoopSemanticPlanner：保存当前 fake 模型返回轮次；如果没有这一行，fake 模型无法先调用工具再最终回答。
            # 新增代码+ModelLoopSemanticPlanner：函数段结束，RecordingDesktopLoopModel.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。
            def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+ModelLoopSemanticPlanner：实现模型 chat 接口；如果没有这一行，LearningAgent.run 无法驱动 fake 模型。
                self.received_messages.append(messages)  # 新增代码+ModelLoopSemanticPlanner：记录本轮完整消息；如果没有这一行，系统 harness 是否进入模型不可验证。
                tool_names = [str(schema.get("function", {}).get("name", "")) for schema in tools if isinstance(schema.get("function", {}), dict)]  # 新增代码+ModelLoopSemanticPlanner：从真实 schema 提取工具名；如果没有这一行，测试只能猜测工具池状态。
                self.received_tool_names.append(tool_names)  # 新增代码+ModelLoopSemanticPlanner：记录模型可见工具名；如果没有这一行，工具 schema 暴露失败不会被发现。
                if self.index == 0:  # 修改代码+ModelLoopFirstStepLaunch：第一轮模拟模型按收窄工具面选择 launch_app；如果没有这一行，测试无法覆盖真实终端第 0 轮先打开目标应用的修复点。
                    self.index += 1  # 新增代码+ModelLoopSemanticPlanner：推进到下一轮最终回答；如果没有这一行，fake 模型会无限调用同一个工具。
                    return ModelMessage(text="", tool_calls=[ToolCall(name="computer_action", arguments={"action": "launch_app", "app_name": "mspaint", "target_app": "mspaint", "confirm_desktop_control": True})])  # 修改代码+ModelLoopFirstStepLaunch：让模型自己调用 computer_action launch_app；如果没有这一行，测试不能证明语义规划仍在模型主循环里完成启动绑定。
                return ModelMessage(text="模型主循环已根据自然语言任务选择 Computer Use 工具继续执行。")  # 新增代码+ModelLoopSemanticPlanner：第二轮返回最终说明；如果没有这一行，agent.run 无法正常结束。
            # 新增代码+ModelLoopSemanticPlanner：函数段结束，RecordingDesktopLoopModel.chat 到此结束；如果没有这个边界说明，初学者不容易看出 fake 模型行为范围。
        # 新增代码+ModelLoopSemanticPlanner：类段结束，RecordingDesktopLoopModel 到此结束；如果没有这个边界说明，初学者不容易看出测试模型范围。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ModelLoopSemanticPlanner：创建临时 workspace 隔离 memory/debug；如果没有这一行，测试会污染真实项目运行目录。
            workspace = Path(raw_dir)  # 新增代码+ModelLoopSemanticPlanner：把临时目录转成 Path；如果没有这一行，LearningAgent 构造路径会不清楚。
            model = RecordingDesktopLoopModel()  # 新增代码+ModelLoopSemanticPlanner：创建会记录首轮上下文的假模型；如果没有这一行，测试没有可观察模型。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+ModelLoopSemanticPlanner：创建真实 agent 并允许安全 fake 工具调用；如果没有这一行，主循环行为没有被测对象。
            def fake_computer_action(arguments: dict[str, object]) -> str:  # 新增代码+ModelLoopFirstStepLaunch：函数段开始，用假动作替代真实桌面启动；如果没有这段函数，单元测试会真的打开 Paint 而污染用户桌面。
                agent._record_observation("fake_computer_action", {"action": arguments.get("action"), "app_name": arguments.get("app_name")})  # 新增代码+ModelLoopFirstStepLaunch：记录模型确实请求了 launch_app；如果没有这一行，测试只能看到最终文本而无法证明工具执行路径。
                return "computer_action 成功：fake launch_app 已绑定 agent-owned target_window=mspaint。"  # 新增代码+ModelLoopFirstStepLaunch：返回可读工具结果给下一轮模型；如果没有这一行，工具循环没有可回灌的结果。
            # 新增代码+ModelLoopFirstStepLaunch：函数段结束，fake_computer_action 到此结束；如果没有这个边界说明，代码小白不容易看出这里没有真实打开软件。
            agent._computer_action = fake_computer_action  # 新增代码+ModelLoopFirstStepLaunch：把真实桌面动作替换为测试假动作；如果没有这一行，测试会触碰用户真实桌面。
            output = _activate_computer_use_tool_pack_for_agent(agent, "/computer use --full", "Computer Use Mode\n- mode=full\n- full_mode=true\n")  # 新增代码+ModelLoopSemanticPlanner：模拟用户先输入 /computer use --full；如果没有这一行，模型第一轮看不到 Computer Use 工具包。
            self.assertIn("model_loop_tools_loaded=true", output)  # 新增代码+ModelLoopSemanticPlanner：确认 full 命令确实加载工具包；如果没有这一行，后续失败原因不清楚。
            answer = agent.run("请使用本地电脑的画图软件画一棵树。", max_turns=2)  # 新增代码+ModelLoopSemanticPlanner：用真实用户自然语言任务进入主循环；如果没有这一行，无法验证树任务是否仍被外置 planner 抢跑。
            first_system_message = str(model.received_messages[0][0].get("content", ""))  # 新增代码+ModelLoopSemanticPlanner：读取首轮 system prompt；如果没有这一行，无法断言模型拿到 Computer Use full harness。
            self.assertIn("Computer Use full 模式", first_system_message)  # 新增代码+ModelLoopSemanticPlanner：断言 full 模式提示进入模型主循环；如果没有这一行，模型可能不知道要走 observe-plan-act。
            self.assertIn("launch_app", first_system_message)  # 新增代码+ModelLoopLaunchAppTool: 断言 full 模式提示模型先启动目标应用；如果没有这一行，模型可能在没打开软件时继续盲动鼠标键盘。
            self.assertIn("target_window", first_system_message)  # 新增代码+ModelLoopLaunchAppTool: 断言提示模型观察启动后返回的目标窗口；如果没有这一行，打开软件后模型可能不知道该观察哪个窗口。
            self.assertIn("第 0 轮只做第一步", first_system_message)  # 新增代码+ModelLoopFirstStepLaunch：断言自然语言本机应用任务会把首轮动作收窄为启动绑定；如果没有这一行，真实终端可能再次卡在模型第 0 轮长时间规划整张图。
            self.assertIn("action=launch_app", first_system_message)  # 新增代码+ModelLoopFirstStepLaunch：断言首轮策略点名 launch_app 动作；如果没有这一行，模型可能先盲目观察或盲目点击而不是打开目标软件。
            self.assertIn("agent-owned 新窗口", first_system_message)  # 新增代码+ModelLoopLaunchAppTool: 断言提示模型优先创建自有窗口；如果没有这一行，真实验收可能复用用户旧窗口造成误判。
            self.assertIn("本轮目标必须始终以用户原始自然语言为准", first_system_message)  # 新增代码+ComputerUseGoalAnchor: 断言 full 模式提示会固定本轮目标；如果没有这一行，模型可能观察旧画布后把画树漂移成补旧图。
            self.assertIn("旧画布或旧图形", first_system_message)  # 新增代码+ComputerUseGoalAnchor: 断言提示明确处理旧画布残留；如果没有这一行，真实 Paint 窗口里的历史图形会继续污染任务。
            self.assertEqual(model.received_tool_names[0], ["computer_action"])  # 新增代码+ModelLoopFirstStepLaunch：断言首轮工具面被收窄到唯一启动动作入口；如果没有这一行，模型会继续在完整工具池和完整绘图任务里卡住。
            self.assertIn("模型主循环已根据自然语言任务选择 Computer Use 工具", answer)  # 新增代码+ModelLoopSemanticPlanner：断言最终结果来自模型循环而不是 runtime 报告；如果没有这一行，旧黑盒 runtime 可能伪装成功。
            self.assertTrue(any(event.get("kind") == "fake_computer_action" for event in agent.observation_events))  # 修改代码+ModelLoopFirstStepLaunch：断言模型选择的 launch_app 工具真的经过工具执行层；如果没有这一行，只看回答无法证明模型主循环跑过首步工具。
            self.assertFalse(any(event.get("kind") == "computer_use_full_desktop_runtime" for event in agent.observation_events))  # 新增代码+ModelLoopSemanticPlanner：断言没有进入旧 run_prompt 黑盒 runtime；如果没有这一行，语义规划可能仍在 Python 层抢跑。
    # 新增代码+ModelLoopSemanticPlanner：函数段结束，test_computer_use_full_desktop_prompt_adds_model_loop_harness_and_uses_tools 到此结束；如果没有这个边界说明，代码小白不容易看出主循环语义规划测试范围。

    def test_computer_use_full_completion_gate_stops_repeated_real_drawing_actions(self) -> None:  # 新增代码+ComputerUseCompletionGate：函数段开始，验证 full 桌面任务已经多次真实绘图后会给模型收敛信号；如果没有这个测试，模型可能无限继续加笔不输出最终回答。
        class FailingController:  # 新增代码+ComputerUseCompletionGate：类段开始，定义不应被调用的假 controller；如果没有这个类，测试无法证明完成门在真实动作前拦住重复绘图。
            def __init__(self) -> None:  # 新增代码+ComputerUseCompletionGate：函数段开始，初始化假 controller 状态；如果没有这段函数，测试无法保存是否被调用。
                self.called = False  # 新增代码+ComputerUseCompletionGate：记录 execute 是否被调用；如果没有这行代码，测试不能证明没有继续触碰桌面后端。
                self.active_agent_owned_target_window = {"app_id": "mspaintapp:pid:1", "window_id": "hwnd:123"}  # 新增代码+ComputerUseCompletionGate：提供已启动并绑定的目标窗口；如果没有这行代码，测试会被 launch_app 门禁提前拦住。
            # 新增代码+ComputerUseCompletionGate：函数段结束，FailingController.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。
            def execute(self, arguments: dict[str, object]) -> object:  # 新增代码+ComputerUseCompletionGate：函数段开始，若完成门失效就暴露错误；如果没有这段函数，测试无法发现 controller 被误调用。
                self.called = True  # 新增代码+ComputerUseCompletionGate：记录后端被调用；如果没有这行代码，断言没有数据来源。
                raise AssertionError("completion gate should stop before controller.execute")  # 新增代码+ComputerUseCompletionGate：用异常阻止测试悄悄触碰后端；如果没有这行代码，完成门失效可能仍被假成功掩盖。
            # 新增代码+ComputerUseCompletionGate：函数段结束，FailingController.execute 到此结束；如果没有这个边界说明，读者不容易看出假执行范围。
        # 新增代码+ComputerUseCompletionGate：类段结束，FailingController 到此结束；如果没有这个边界说明，读者不容易看出测试假对象范围。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseCompletionGate：创建临时 workspace；如果没有这一行，测试会污染真实 debug 和 memory。
            workspace = Path(raw_dir)  # 新增代码+ComputerUseCompletionGate：把临时目录转成 Path；如果没有这一行，agent 构造路径不够明确。
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="unused")]), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+ComputerUseCompletionGate：创建真实 agent 并自动授权；如果没有这一行，无法调用真实 _computer_action 门禁链。
            controller = FailingController()  # 新增代码+ComputerUseCompletionGate：创建不应被调用的 controller；如果没有这一行，无法观察完成门是否提前返回。
            agent.computer_use_controller = controller  # 新增代码+ComputerUseCompletionGate：把假 controller 注入 agent；如果没有这一行，测试可能触碰真实 Computer Use 控制器。
            agent.desktop_task_context = {"active": True, "requires_gui_actions": True, "target_app_hint": "mspaint", "task_goal": "draw_with_local_paint"}  # 新增代码+ComputerUseCompletionGate：模拟 /computer use --full 绘图任务上下文；如果没有这一行，完成门不会启用。
            agent._record_observation("computer_use_observe", {"action": "get_window_state", "ok": True, "data": {"image_result_count": 1, "screenshot_captured": True}})  # 新增代码+ComputerUseCompletionGate：写入一次模型可见截图观察；如果没有这一行，动作门会认为模型还没看过屏幕。
            for index in range(12):  # 新增代码+ComputerUseCompletionGate：模拟已经成功执行十二次真实绘图动作；如果没有这一行，无法复现真实验收里无限加笔的问题。
                agent._record_observation("computer_use_action", {"action": "drag_path", "ok": True, "message": "ok", "data": {"dispatch": {"low_level_event_count": 8}, "real_input_enabled": True, "image_result_count": 1, "action_index": index}})  # 新增代码+ComputerUseCompletionGate：写入带低层输入数量的成功动作记录；如果没有这一行，完成门没有可审计动作数量。
            output = agent._computer_action({"action": "drag_path", "points": [{"x": 1, "y": 1}, {"x": 2, "y": 2}], "window": {"window_id": "hwnd:123"}})  # 新增代码+ComputerUseCompletionGate：再次请求拖拽绘图以触发完成门；如果没有这一行，测试不会覆盖 _computer_action 入口。
            self.assertFalse(controller.called)  # 新增代码+ComputerUseCompletionGate：断言没有继续调用桌面后端；如果没有这一行，完成门可能只返回文字但仍触碰真实动作。
            self.assertIn("computer_use_full_completion_ready", output)  # 新增代码+ComputerUseCompletionGate：断言工具结果给模型稳定完成原因码；如果没有这一行，模型不容易知道该最终回答。
            self.assertIn("请直接输出最终回答", output)  # 新增代码+ComputerUseCompletionGate：断言返回文本明确要求模型收敛；如果没有这一行，模型可能继续调用绘图动作。
    # 新增代码+ComputerUseCompletionGate：函数段结束，test_computer_use_full_completion_gate_stops_repeated_real_drawing_actions 到此结束；如果没有这个边界说明，读者不容易看出完成门测试范围。

    def test_computer_use_full_completion_gate_accepts_action_embedded_visual_evidence(self) -> None:  # 新增代码+ComputerUseActionVisualEvidence：函数段开始，验证真实动作结果自带截图证据时也能触发完成门；如果没有这个测试，真实终端里动作截图会被忽略导致模型无限加笔。
        class FailingController:  # 新增代码+ComputerUseActionVisualEvidence：类段开始，定义不应被继续调用的假 controller；如果没有这个类，测试无法证明完成门真的拦在后端之前。
            def __init__(self) -> None:  # 新增代码+ComputerUseActionVisualEvidence：函数段开始，初始化假 controller；如果没有这段函数，测试无法保存后端调用状态。
                self.called = False  # 新增代码+ComputerUseActionVisualEvidence：记录 execute 是否被调用；如果没有这行代码，完成门失效时测试看不出来。
                self.active_agent_owned_target_window = {"app_id": "mspaintapp:pid:1", "window_id": "hwnd:123"}  # 新增代码+ComputerUseActionVisualEvidence：模拟已经由 agent 打开并绑定 Paint 窗口；如果没有这行代码，启动门禁会先拦截而无法测试完成门。
            # 新增代码+ComputerUseActionVisualEvidence：函数段结束，FailingController.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。
            def execute(self, arguments: dict[str, object]) -> object:  # 新增代码+ComputerUseActionVisualEvidence：函数段开始，若完成门没有触发就暴露错误；如果没有这段函数，测试可能悄悄继续触碰后端。
                self.called = True  # 新增代码+ComputerUseActionVisualEvidence：记录后端已经被错误调用；如果没有这行代码，断言没有证据。
                raise AssertionError("completion gate should stop before controller.execute")  # 新增代码+ComputerUseActionVisualEvidence：用异常证明不能继续动作；如果没有这行代码，完成门失效可能被后续假返回掩盖。
            # 新增代码+ComputerUseActionVisualEvidence：函数段结束，FailingController.execute 到此结束；如果没有这个边界说明，读者不容易看出假执行范围。
        # 新增代码+ComputerUseActionVisualEvidence：类段结束，FailingController 到此结束；如果没有这个边界说明，读者不容易看出测试假对象范围。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseActionVisualEvidence：创建临时 workspace；如果没有这一行，测试会污染真实 debug 和 memory。
            workspace = Path(raw_dir)  # 新增代码+ComputerUseActionVisualEvidence：把临时目录转成 Path；如果没有这一行，agent 构造路径不够明确。
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="unused")]), workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+ComputerUseActionVisualEvidence：创建真实 agent 并自动授权；如果没有这一行，无法覆盖真实 _computer_action 门禁链。
            controller = FailingController()  # 新增代码+ComputerUseActionVisualEvidence：创建不应被调用的 controller；如果没有这一行，无法观察完成门是否提前返回。
            agent.computer_use_controller = controller  # 新增代码+ComputerUseActionVisualEvidence：把假 controller 注入 agent；如果没有这一行，测试可能触碰真实 Computer Use 控制器。
            agent.desktop_task_context = {"active": True, "requires_gui_actions": True, "target_app_hint": "mspaint", "task_goal": "draw_with_local_paint"}  # 新增代码+ComputerUseActionVisualEvidence：模拟 /computer use --full 绘图任务上下文；如果没有这一行，完成门不会启用。
            for index in range(12):  # 新增代码+ComputerUseActionVisualEvidence：模拟真实终端已经完成十二次带截图证据的动作；如果没有这一行，无法复现长绘图不收束问题。
                agent._record_observation("computer_use_action", {"action": "drag_path", "ok": True, "message": "ok", "data": {"dispatch": {"low_level_event_count": 8}, "real_input_enabled": True, "before_evidence": {"captured": True, "state": {"screenshot_captured": True, "image_result_count": 1}}, "image_result_count": 1, "action_index": index}})  # 新增代码+ComputerUseActionVisualEvidence：写入动作自带截图和低层输入计数；如果没有这一行，测试不能代表真实日志里的 before_evidence 形状。
            output = agent._computer_action({"action": "drag_path", "points": [{"x": 1, "y": 1}, {"x": 2, "y": 2}], "window": {"window_id": "hwnd:123"}})  # 新增代码+ComputerUseActionVisualEvidence：再次请求绘图动作以触发完成门；如果没有这一行，测试不会覆盖真实入口。
            self.assertFalse(controller.called)  # 新增代码+ComputerUseActionVisualEvidence：断言没有继续调用桌面后端；如果没有这一行，完成门可能没拦住真实鼠标键盘。
            self.assertIn("computer_use_full_completion_ready", output)  # 新增代码+ComputerUseActionVisualEvidence：断言工具结果给模型明确收束信号；如果没有这一行，模型可能继续重复动作。
    # 新增代码+ComputerUseActionVisualEvidence：函数段结束，test_computer_use_full_completion_gate_accepts_action_embedded_visual_evidence 到此结束；如果没有这个边界说明，读者不容易看出动作内嵌视觉证据测试范围。

    def test_core_config_exports_runtime_parsers(self) -> None:  # 新增代码+CoreSplit: 验证运行配置解析已从主文件迁移到 core.config；若没有这行代码，配置层拆分可能只停留在文件存在。
        from learning_agent.core.config import AgentRuntimeConfig as CoreAgentRuntimeConfig, parse_max_turns_value as core_parse_max_turns_value  # 新增代码+CoreSplit: 直接导入新模块配置类和解析器；若没有这行代码，测试无法证明 core.config 可独立工作。
        from learning_agent.core.config import parse_max_turns_value as entry_parse_max_turns_value  # 修改代码+LegacyEntryCut: 从正式配置层导入解析函数作为入口对照；若没有这行代码，测试会继续依赖旧脚本入口。
        self.assertEqual(core_parse_max_turns_value("3", "test"), 3)  # 新增代码+CoreSplit: 断言新解析器能解析正整数字符串；若没有这行代码，最常见配置输入可能回归。
        self.assertIs(AgentRuntimeConfig, CoreAgentRuntimeConfig)  # 修改代码+LegacyEntryCut: 断言测试全局导入与 core.config 是同一配置类；若没有这行代码，测试可能混用两套配置对象。
        self.assertIs(entry_parse_max_turns_value, core_parse_max_turns_value)  # 修改代码+LegacyEntryCut: 断言入口对照函数就是配置层函数；若没有这行代码，重复解析实现可能悄悄回流。
    def test_evidence_ledger_report_uses_observation_events_and_artifacts(self) -> None:  # 新增代码+PromptArchitectureV1: 验证提示词表面报告能桥接 observation_events 为 Evidence Ledger；若没有这行代码，证据账本预留入口可能一直空转
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PromptArchitectureV1: 创建临时工作区避免污染真实项目调试目录；若没有这行代码，测试可能依赖或修改真实文件
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="ok")]), workspace=Path(raw_dir), ask_permission=lambda action: True)  # 新增代码+PromptArchitectureV1: 创建带假模型的真实 agent；若没有这行代码，无法调用 _record_observation 和报告工具
            agent._record_observation("tool_result_offloaded", {"tool_name": "read_file", "artifact_path": "x.txt", "raw_output_chars": 9000})  # 新增代码+PromptArchitectureV1: 写入带 artifact 路径和原始长度的观察事件；若没有这行代码，Evidence Ledger 没有可验证输入
            output = agent._execute_tool(ToolCall(name="prompt_surface_report", arguments={"include_evidence": True}))  # 新增代码+PromptArchitectureV1: 请求包含证据账本的提示词表面报告；若没有这行代码，无法验证 include_evidence 参数真实生效
            self.assertIn("Evidence Ledger", output)  # 新增代码+PromptArchitectureV1: 断言报告包含证据账本标题；若没有这行代码，报告可能仍是 Task 4 的占位说明
            self.assertIn("tool_result_offloaded", output)  # 新增代码+PromptArchitectureV1: 断言原始事件类型进入证据账本；若没有这行代码，工具结果落盘事件可能丢失
    def test_text_index_truncation_preserves_latest_tail_summary(self) -> None:  # 新增代码+PromptArchitectureV1: 验证索引超预算时仍保留最新尾部摘要；若没有这行代码，长标题会把 tail 摘要挤掉而不被发现
        long_headings = "\n".join(f"# Heading {index} " + ("很长标题" * 20) for index in range(20))  # 新增代码+PromptArchitectureV1: 构造超长标题区块复现审查发现的截断场景；若没有这行代码，测试无法覆盖 headings 挤占预算的问题
        text = f"{long_headings}\n中间内容\n最终尾部事实"  # 新增代码+PromptArchitectureV1: 在长标题后放入必须保留的最新尾部事实；若没有这行代码，无法判断 tail 是否被保住
        index_text = build_text_index("Long-Term Memory Index", text, max_chars=220, source_path="memory.md")  # 新增代码+PromptArchitectureV1: 用很小预算构建索引逼出截断路径；若没有这行代码，回归测试不会触发关键分支
        included_line = next(line for line in index_text.splitlines() if line.startswith("included_chars="))  # 新增代码+PromptArchitectureV1: 读取 included_chars 元数据行；若没有这行代码，测试无法确认预算统计是否可信
        included_chars = int(included_line.split("=", 1)[1])  # 新增代码+PromptArchitectureV1: 把 included_chars 转成数字用于断言；若没有这行代码，只能做脆弱字符串比较
        self.assertLessEqual(included_chars, 220)  # 新增代码+PromptArchitectureV1: 断言记录的索引正文长度不超过 max_chars；若没有这行代码，报告可能显示不可靠预算
        self.assertIn("headings:", index_text)  # 新增代码+PromptArchitectureV1: 断言标题索引区仍存在；若没有这行代码，修复 tail 时可能反过来丢掉 headings
        self.assertIn("latest_tail_summary", index_text)  # 新增代码+PromptArchitectureV1: 断言尾部摘要区标题仍存在；若没有这行代码，索引可能只剩 headings 而模型看不到最新内容
        self.assertIn("最终尾部事实", index_text)  # 新增代码+PromptArchitectureV1: 断言最新尾部事实仍在索引中；若没有这行代码，Task 3 的“保留最新 tail”承诺会失守
    def test_text_index_zero_budget_keeps_included_chars_bounded(self) -> None:  # 新增代码+PromptArchitectureV1: 验证极小预算不会让 included_chars 反向超限；若没有这行代码，max_chars=0 的切片陷阱会回归
        index_text = build_text_index("Tiny Index", "# Heading\n尾部事实", max_chars=0, source_path="memory.md")  # 新增代码+PromptArchitectureV1: 用零预算触发极端截断路径；若没有这行代码，无法覆盖 body[-0:] 的边界问题
        included_line = next(line for line in index_text.splitlines() if line.startswith("included_chars="))  # 新增代码+PromptArchitectureV1: 读取 included_chars 元数据行；若没有这行代码，测试无法检查预算字段
        included_chars = int(included_line.split("=", 1)[1])  # 新增代码+PromptArchitectureV1: 转换 included_chars 为数字；若没有这行代码，无法做数值上限断言
        self.assertEqual(included_chars, 0)  # 新增代码+PromptArchitectureV1: 断言零预算时正文长度也为零；若没有这行代码，报告可能继续声称超预算内容被纳入
    def test_tasks_package_exports_background_and_task_records(self) -> None:  # 新增代码+TasksSplit: 验证任务层记录类型已经从主文件迁入 tasks 包；若没有这行代码，阶段 8 可能只创建空目录不提供可复用入口。
        from learning_agent.tasks.background import BackgroundCommand  # 新增代码+TasksSplit: 从新 background 模块导入后台命令记录；若没有这行代码，测试无法证明后台命令数据结构有独立入口。
        from learning_agent.tasks.cron_monitor import CronRecord, MonitorRecord  # 新增代码+TasksSplit: 从新 cron_monitor 模块导入定时和监控记录；若没有这行代码，Cron/Monitor 数据结构仍可能留在主文件。
        from learning_agent.tasks.task_runs import TaskRun  # 新增代码+TasksSplit: 从新 task_runs 模块导入子任务记录；若没有这行代码，测试无法证明 task 生命周期记录有独立入口。
        from learning_agent.tasks.team import TeamMessage, TeamPeer  # 新增代码+TasksSplit: 从新 team 模块导入团队通信记录；若没有这行代码，多 agent 教学记录仍可能留在主文件。
        self.assertIsNotNone(BackgroundCommand)  # 新增代码+TasksSplit: 断言后台命令记录类型可导入；若没有这行代码，导入空模块也可能误通过。
        self.assertIsNotNone(TaskRun)  # 新增代码+TasksSplit: 断言子任务记录类型可导入；若没有这行代码，task_runs 模块可能缺少核心数据结构。
        self.assertIsNotNone(TeamMessage)  # 新增代码+TasksSplit: 断言团队消息记录类型可导入；若没有这行代码，team 通信数据结构迁移没有覆盖。
        self.assertIsNotNone(TeamPeer)  # 新增代码+TasksSplit: 断言团队成员记录类型可导入；若没有这行代码，peer 管理数据结构迁移没有覆盖。
        self.assertIsNotNone(CronRecord)  # 新增代码+TasksSplit: 断言定时任务记录类型可导入；若没有这行代码，cron 记录迁移没有覆盖。
        self.assertIsNotNone(MonitorRecord)  # 新增代码+TasksSplit: 断言监控记录类型可导入；若没有这行代码，monitor 记录迁移没有覆盖。
    def test_app_package_exports_main_entrypoints(self) -> None:  # 新增代码+AppSplit: 验证 CLI 和 doctor 入口已经迁入 app 层；若没有这行代码，阶段 10 可能只改主文件而没有形成入口模块。
        from learning_agent.app.cli import main  # 新增代码+AppSplit: 从 app.cli 导入主入口函数；若没有这行代码，测试无法证明 CLI 有独立模块入口。
        from learning_agent.app.doctor import run_mcp_doctor  # 新增代码+AppSplit: 从 app.doctor 导入诊断入口；若没有这行代码，测试无法证明 doctor 已从主入口解耦。
        self.assertTrue(callable(main))  # 新增代码+AppSplit: 断言 CLI 入口可调用；若没有这行代码，导入到常量或错误对象也可能被遗漏。
        self.assertTrue(callable(run_mcp_doctor))  # 新增代码+AppSplit: 断言 doctor 入口可调用；若没有这行代码，诊断入口断开不会被及时发现。
    def test_plan_mode_blocks_side_effect_until_user_confirms_plan(self) -> None:  # 新增代码+PlanModeGate: 验证计划确认前写文件会被副作用闸门阻断；若没有这行代码，Phase 5 计划模式可能退化成只提示不拦截
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PlanModeGate: 创建临时工作区隔离写文件副作用；若没有这行代码，测试可能污染真实目录
            workspace = Path(raw_dir)  # 新增代码+PlanModeGate: 把临时目录转成 Path；若没有这行代码，后续路径拼接不清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+PlanModeGate: 创建自动授权 agent，确保阻断来自 plan gate 而不是权限拒绝；若没有这行代码，测试路径不完整
            agent._execute_tool(ToolCall(name="enter_plan_mode", arguments={"reason": "复杂改动", "goal": "先计划再写文件"}))  # 新增代码+PlanModeGate: 进入计划模式；若没有这行代码，副作用闸门不会启用
            agent._execute_tool(ToolCall(name="exit_plan_mode", arguments={"plan": "写入 marker 文件", "steps": ["写文件", "验证文件"]}))  # 新增代码+PlanModeGate: 输出计划并进入等待用户确认状态；若没有这行代码，确认前阻断状态不会出现
            blocked_output = agent._execute_tool(ToolCall(name="write_file", arguments={"path": "marker.txt", "content": "blocked"}))  # 新增代码+PlanModeGate: 用户确认前尝试写文件；若没有这行代码，无法证明副作用会被拦截
            agent._maybe_confirm_plan_from_user_input("我确认，按计划继续执行。")  # 新增代码+PlanModeGate: 用自然语言确认计划；若没有这行代码，后续写文件仍应被阻断
            allowed_output = agent._execute_tool(ToolCall(name="write_file", arguments={"path": "marker.txt", "content": "allowed"}))  # 新增代码+PlanModeGate: 确认后再次写文件；若没有这行代码，无法证明确认会真正解锁执行
            observation_kinds = [event["kind"] for event in agent.observation_events]  # 新增代码+PlanModeGate: 收集观察事件类型；若没有这行代码，无法验证阻断和确认被审计
            self.assertIn("plan mode 阻断", blocked_output)  # 新增代码+PlanModeGate: 断言确认前写文件被拦截；若没有这行代码，副作用可能提前发生
            self.assertFalse((workspace / "marker.txt").read_text(encoding="utf-8") == "blocked" if (workspace / "marker.txt").exists() else False)  # 新增代码+PlanModeGate: 断言阻断内容没有落盘；若没有这行代码，只看返回文本可能漏掉实际副作用
            self.assertIn("write_file 成功", allowed_output)  # 修改代码+PlanModeGate: 断言确认后写文件成功且匹配真实工具返回前缀；若没有这行代码，闸门可能永久锁死
            self.assertEqual((workspace / "marker.txt").read_text(encoding="utf-8"), "allowed")  # 新增代码+PlanModeGate: 断言最终文件内容来自确认后的调用；若没有这行代码，无法证明写入结果正确
            self.assertIn("plan_mode_blocked_tool", observation_kinds)  # 新增代码+PlanModeGate: 断言阻断事件进入 observation；若没有这行代码，Phase 6 审计看不到为何没执行
            self.assertIn("plan_confirmed", observation_kinds)  # 新增代码+PlanModeGate: 断言确认事件进入 observation；若没有这行代码，解锁依据缺少结构化证据
    def test_agent_default_run_does_not_have_fixed_eight_turn_limit(self) -> None:  # 新增代码+可配置轮次: 验证默认主循环不再写死 8 轮；若省略: learning_agent 可能继续比 Claude Code 更僵硬地提前停止
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+可配置轮次: 创建临时工作区隔离 memory 和调试日志；若省略: 测试会污染真实 learning_agent 目录
            workspace = Path(raw_dir)  # 新增代码+可配置轮次: 把临时目录转成 Path；若省略: 后续文件和 agent 构造不够稳定
            (workspace / "runtime_instructions.md").write_text("测试规则", encoding="utf-8")  # 新增代码+可配置轮次: 写入最小运行规则文件；若省略: 缺失占位不会影响逻辑但会让日志更嘈杂
            tool_loop_messages = [ModelMessage(text="", tool_calls=[ToolCall(name="read_file", arguments={"path": "memory.md"})]) for _ in range(9)]  # 新增代码+可配置轮次: 构造 9 轮连续工具调用，超过旧默认 8 轮；若省略: 测试无法证明旧硬编码会提前停止
            model = ToolCallingFakeModel(tool_loop_messages + [ModelMessage(text="第九轮工具调用后才完成。")])  # 新增代码+可配置轮次: 第 10 次模型调用才给最终答案；若省略: agent 没有最终完成信号
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+可配置轮次: 创建默认配置 agent；若省略: 无法验证默认 run 行为
            answer = agent.run("请连续读取 memory.md，直到模型给出最终答案")  # 新增代码+可配置轮次: 不传 max_turns 运行默认主循环；若省略: 被测默认行为不会发生
            self.assertIn("第九轮工具调用后才完成", answer)  # 新增代码+可配置轮次: 默认不应在 8 轮停止；若省略: 测试不会真正抓住硬编码轮次回归
    def test_runtime_config_defaults_to_unlimited_when_file_is_missing(self) -> None:  # 新增代码+可配置轮次: 验证没有配置文件时默认不按轮次主动停止；若省略: 旧硬编码默认值可能从配置层回流
        old_env = os.environ.pop("LEARNING_AGENT_MAX_TURNS", None)  # 新增代码+可配置轮次: 暂时移除环境变量避免污染默认值测试；若省略: 用户机器上的变量可能让测试不稳定
        try:  # 新增代码+可配置轮次: 用 try/finally 保证环境变量会恢复；若省略: 测试失败时可能污染后续测试
            with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+可配置轮次: 创建没有 runtime_config.json 的临时工作区；若省略: 无法验证缺省配置行为
                config = load_agent_runtime_config(Path(raw_dir))  # 新增代码+可配置轮次: 加载运行配置；若省略: 没有被测对象可断言
                self.assertIsNone(config.max_turns)  # 新增代码+可配置轮次: 断言缺省为无限制；若省略: 无法防止默认又变成固定数字
        finally:  # 新增代码+可配置轮次: 进入环境变量恢复分支；若省略: pop 后的变量不会被放回
            if old_env is not None:  # 新增代码+可配置轮次: 只有原来存在变量时才恢复；若省略: 会把不存在的变量错误设置成字符串 None
                os.environ["LEARNING_AGENT_MAX_TURNS"] = old_env  # 新增代码+可配置轮次: 恢复原始环境变量；若省略: 后续测试或用户环境可能被改变
    def test_runtime_config_reads_file_and_environment_max_turns(self) -> None:  # 新增代码+可配置轮次: 验证配置文件和环境变量都能控制 max_turns；若省略: CLI 外的启动方式仍难以配置轮次
        old_env = os.environ.pop("LEARNING_AGENT_MAX_TURNS", None)  # 新增代码+可配置轮次: 清理环境变量以先测试文件值；若省略: 文件配置断言可能被外部环境覆盖
        try:  # 新增代码+可配置轮次: 用 try/finally 包住环境变量改动；若省略: 测试异常会污染进程环境
            with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+可配置轮次: 创建临时工作区写入 runtime_config.json；若省略: 测试可能修改真实配置
                workspace = Path(raw_dir)  # 新增代码+可配置轮次: 把临时路径转成 Path；若省略: 后续写文件表达不清楚
                (workspace / "runtime_config.json").write_text(json.dumps({"max_turns": 3}, ensure_ascii=False), encoding="utf-8")  # 新增代码+可配置轮次: 写入配置文件 max_turns=3；若省略: 无法证明配置文件被读取
                self.assertEqual(load_agent_runtime_config(workspace).max_turns, 3)  # 新增代码+可配置轮次: 断言文件值生效；若省略: 配置文件读取失败不会被发现
                os.environ["LEARNING_AGENT_MAX_TURNS"] = "5"  # 新增代码+可配置轮次: 设置环境变量覆盖文件值；若省略: 无法验证临时覆盖能力
                self.assertEqual(load_agent_runtime_config(workspace).max_turns, 5)  # 新增代码+可配置轮次: 断言环境变量优先；若省略: 用户临时运行策略可能不生效
                os.environ["LEARNING_AGENT_MAX_TURNS"] = "none"  # 新增代码+可配置轮次: 设置 none 表示主动取消轮次上限；若省略: 用户无法从环境变量恢复无限制策略
                self.assertIsNone(load_agent_runtime_config(workspace).max_turns)  # 新增代码+可配置轮次: 断言 none 会覆盖文件数字；若省略: 显式无限制语义可能丢失
        finally:  # 新增代码+可配置轮次: 进入环境变量恢复分支；若省略: 环境变量会泄漏到后续测试
            if old_env is None:  # 新增代码+可配置轮次: 如果测试前没有变量；若省略: 无法区分删除和恢复两种状态
                os.environ.pop("LEARNING_AGENT_MAX_TURNS", None)  # 新增代码+可配置轮次: 删除测试设置的变量；若省略: 后续测试会读到测试残留
            else:  # 新增代码+可配置轮次: 如果测试前已有变量；若省略: 原有用户环境不能恢复
                os.environ["LEARNING_AGENT_MAX_TURNS"] = old_env  # 新增代码+可配置轮次: 恢复原始环境变量值；若省略: 会改变用户运行环境
    def test_parse_main_args_and_resolve_max_turns_cli_override(self) -> None:  # 新增代码+可配置轮次: 验证 --max-turns 命令行参数能覆盖配置；若省略: 用户无法像 Claude Code 那样临时指定轮次
        numeric_args = parse_main_args(["--max-turns", "4"])  # 新增代码+可配置轮次: 解析数字轮次参数；若省略: 无法验证普通 CLI 设置
        self.assertEqual(numeric_args.max_turns, 4)  # 新增代码+可配置轮次: 断言数字参数被转成 int；若省略: 字符串值可能传入 run 导致 range/比较错误
        self.assertTrue(numeric_args.max_turns_is_set)  # 新增代码+可配置轮次: 断言 CLI 显式传值被记录；若省略: 无法区分没传和传 none
        unlimited_args = parse_main_args(["--max-turns", "none"])  # 新增代码+可配置轮次: 解析显式无限制参数；若省略: 用户无法从 CLI 取消配置文件里的数字上限
        self.assertIsNone(unlimited_args.max_turns)  # 新增代码+可配置轮次: 断言 none 代表无限制；若省略: none 可能被误当普通字符串
        self.assertTrue(unlimited_args.max_turns_is_set)  # 新增代码+可配置轮次: 断言 none 也是一次显式 CLI 覆盖；若省略: 配置文件数字可能继续生效
        config = AgentRuntimeConfig(max_turns=3)  # 新增代码+可配置轮次: 构造配置文件给出的数字上限；若省略: 无法验证 CLI 覆盖配置的决策
        self.assertEqual(resolve_run_max_turns(config, numeric_args), 4)  # 新增代码+可配置轮次: 数字 CLI 应覆盖配置；若省略: 临时命令行策略可能被配置文件压住
        self.assertIsNone(resolve_run_max_turns(config, unlimited_args))  # 新增代码+可配置轮次: none CLI 应覆盖配置为无限制；若省略: 用户无法显式取消 max_turns
        self.assertEqual(resolve_run_max_turns(config, MainArgs(command="", max_turns=None, max_turns_is_set=False)), 3)  # 新增代码+可配置轮次: 没有 CLI 时应使用配置文件；若省略: 配置文件可能永远不生效
    def test_parse_main_args_supports_cli_run_and_bridge_commands(self) -> None:  # 新增代码+CommandBridge: 验证 CLI 能表达一次性运行和 HTTP bridge 启动；若没有这行代码，Codex 无法稳定启动和控制 agent
        run_args = parse_main_args(["run", "--prompt", "ping", "--json", "--max-turns", "2"])  # 新增代码+CLI接口: 解析一次性 run 命令；若没有这行代码，CLI run 参数没有测试输入
        self.assertEqual(run_args.command, "run")  # 新增代码+CLI接口: 断言命令名保留为 run；若没有这行代码，main 无法区分交互模式和一次性模式
        self.assertEqual(run_args.prompt, "ping")  # 新增代码+CLI接口: 断言 prompt 参数被保存；若没有这行代码，一次性运行不知道用户输入
        self.assertTrue(run_args.output_json)  # 新增代码+CLI接口: 断言 JSON 输出开关生效；若没有这行代码，Codex 无法稳定解析 CLI 返回
        self.assertEqual(run_args.max_turns, 2)  # 新增代码+CLI接口: 断言 run 命令仍能复用 max-turns；若没有这行代码，调试时无法限制工具循环
        bridge_args = parse_main_args(["bridge", "--bridge-host", "127.0.0.1", "--bridge-port", "8765", "--bridge-token", "secret"])  # 新增代码+CommandBridge: 解析 HTTP bridge 启动参数；若没有这行代码，桥接端口和 token 配置没有回归保护
        self.assertEqual(bridge_args.command, "bridge")  # 新增代码+CommandBridge: 断言命令名保留为 bridge；若没有这行代码，main 无法进入 HTTP 服务模式
        self.assertEqual(bridge_args.bridge_host, "127.0.0.1")  # 新增代码+CommandBridge: 断言默认本机绑定参数可解析；若没有这行代码，bridge 可能错误暴露到外部网络
        self.assertEqual(bridge_args.bridge_port, 8765)  # 新增代码+CommandBridge: 断言端口参数可解析为整数；若没有这行代码，server 无法绑定用户指定端口
        self.assertEqual(bridge_args.bridge_token, "secret")  # 新增代码+CommandBridge: 断言 token 参数被保存；若没有这行代码，Codex 和 agent 之间无法启用简单认证
    def test_http_command_bridge_health_and_run_with_token(self) -> None:  # 新增代码+CommandBridge: 验证本机 HTTP bridge 可探活、认证并运行 agent；若没有这行代码，Codex 控制接口没有真实回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CommandBridge: 创建临时工作区隔离桥接测试；若没有这行代码，测试可能污染真实项目文件
            workspace = Path(raw_dir)  # 新增代码+CommandBridge: 把临时目录转换成 Path；若没有这行代码，LearningAgent 初始化路径不清楚
            model = ToolCallingFakeModel([ModelMessage(text="bridge answer")])  # 新增代码+CommandBridge: 构造一次直接回答的假模型；若没有这行代码，HTTP run 会依赖真实模型
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+CommandBridge: 创建测试 agent 并允许工具权限；若没有这行代码，bridge 没有可控制对象
            server = create_command_bridge_server(agent=agent, host="127.0.0.1", port=0, token="secret", max_turns=3)  # 新增代码+CommandBridge: 在随机本机端口创建 bridge server；若没有这行代码，无法测试真实 HTTP 协议
            thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+CommandBridge: 用后台线程运行 HTTP server；若没有这行代码，测试会阻塞在 serve_forever
            thread.start()  # 新增代码+CommandBridge: 启动 bridge server；若没有这行代码，HTTP client 无法连接
            self.addCleanup(server.server_close)  # 新增代码+CommandBridge: 测试结束关闭 server socket；若没有这行代码，端口资源可能泄露
            self.addCleanup(server.shutdown)  # 新增代码+CommandBridge: 测试结束停止 serve_forever；若没有这行代码，后台线程可能残留
            host, port = server.server_address  # 新增代码+CommandBridge: 读取系统分配的实际监听地址；若没有这行代码，client 不知道连接哪个端口
            health_connection = http.client.HTTPConnection(host, port, timeout=5)  # 新增代码+CommandBridge: 创建探活 HTTP 连接；若没有这行代码，无法验证 GET /health
            health_connection.request("GET", "/health")  # 新增代码+CommandBridge: 请求健康检查；若没有这行代码，探活端点没有测试覆盖
            health_response = health_connection.getresponse()  # 新增代码+CommandBridge: 读取探活响应；若没有这行代码，无法断言状态码和正文
            health_payload = json.loads(health_response.read().decode("utf-8"))  # 新增代码+CommandBridge: 解析探活 JSON；若没有这行代码，健康检查可能返回不可解析文本
            self.assertEqual(health_response.status, 200)  # 新增代码+CommandBridge: 断言探活成功；若没有这行代码，Codex 无法可靠判断 bridge 是否在线
            self.assertEqual(health_payload["visible_tools"], ["read", "write", "edit", "bash"])  # 新增代码+CommandBridge: 断言探活返回四原子工具池；若没有这行代码，外部调试无法确认工具面
            run_body = json.dumps({"prompt": "hello"}, ensure_ascii=False).encode("utf-8")  # 新增代码+CommandBridge: 准备 run 请求 JSON 正文；若没有这行代码，POST /run 没有输入
            run_headers = {"Content-Type": "application/json", "Authorization": "Bearer secret"}  # 新增代码+CommandBridge: 设置 JSON 类型和 Bearer token；若没有这行代码，认证路径没有被覆盖
            run_connection = http.client.HTTPConnection(host, port, timeout=5)  # 新增代码+CommandBridge: 创建 run HTTP 连接；若没有这行代码，无法发送控制命令
            run_connection.request("POST", "/run", body=run_body, headers=run_headers)  # 新增代码+CommandBridge: 发送运行命令；若没有这行代码，agent.run 不会通过 bridge 触发
            run_response = run_connection.getresponse()  # 新增代码+CommandBridge: 读取 run 响应；若没有这行代码，无法验证 bridge 返回
            run_payload = json.loads(run_response.read().decode("utf-8"))  # 新增代码+CommandBridge: 解析 run JSON；若没有这行代码，Codex 接收路径不可验证
            self.assertEqual(run_response.status, 200)  # 新增代码+CommandBridge: 断言 run 请求成功；若没有这行代码，HTTP 状态错误可能被正文掩盖
            self.assertEqual(run_payload["answer"], "bridge answer")  # 新增代码+CommandBridge: 断言 agent 最终回答返回给 HTTP 调用方；若没有这行代码，Codex 收不到 agent 输出
            self.assertEqual(run_payload["max_turns"], 3)  # 新增代码+CommandBridge: 断言 bridge 默认轮次进入响应；若没有这行代码，外部调试无法确认运行策略
    def test_agent_can_read_file_then_return_final_answer(self) -> None:  # 作用: 测试代理是否能读取文件并在最终答案中包含文件内容；若省略: 该行为不被自动检查
        with tempfile.TemporaryDirectory() as raw_dir:  # 作用: 创建临时工作目录并在上下文退出时自动清理；若省略: 需手动清理，且可能污染磁盘
            workspace = Path(raw_dir)  # 作用: 将字符串路径包装为 Path 以便使用 `/` 拼接等便利操作；若省略: 后续 Path 操作会失败
            sample_file = workspace / "hello.txt"  # 作用: 定义测试用文件路径；若省略: 无法写入或引用测试文件
            sample_file.write_text("你好，agent 学习者！", encoding="utf-8")  # 作用: 在临时目录写入包含中文的测试内容；若省略: 读取操作找不到文件，测试会失败；若不显式指定 encoding，跨平台可能出现编码问题
            model = ToolCallingFakeModel(  # 作用: 构造一个可控的假模型，按序返回预设的 ModelMessage（包括触发工具调用和最终回答）；若省略: 无法驱动代理进入预期的工具调用流程
                [  # 作用: 假模型的返回序列，按列表顺序逐条提供 ModelMessage；若省略: 无法描述模型的交互流程
                    ModelMessage(  # 作用: 第一条消息用于指示代理执行工具调用（而非直接返回自然语言答案）；若省略: 代理不会接到读取文件的请求
                        text="",  # 作用: 留空文本，强调这条消息的主要内容是工具调用；若改为非空文本可能改变消息语义但不影响 tool_calls 本身
                        tool_calls=[ToolCall(name="read_file", arguments={"path": str(sample_file)})],  # 作用: 指示代理调用 `read_file` 工具并传入文件路径参数；若省略: 代理不会被要求去读取文件
                    ),
                    ModelMessage(text="我已经读到文件内容：你好，agent 学习者！"),  # 作用: 模拟模型在工具调用完成后的自然语言确认，用于断言代理最终返回的文本
                ]
            )
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 作用: 创建代理并注入假模型与始终允许的权限回调；若省略或权限不同，代理行为会变化
            answer = agent.run("请读取 hello.txt")  # 作用: 触发代理主流程（把用户请求传入），驱动模型-代理-工具的交互；若省略: 不会执行被测行为
            self.assertIn("你好，agent 学习者", answer)  # 作用: 验证最终回答包含文件内容，确保读取与回复链路正确；若省略: 测试没有实际验证点
    def test_agent_writes_human_readable_markdown_debug_logs(self) -> None:  # 新增代码: 测试 agent 会生成适合 Windows 记事本阅读的 Markdown 调试日志；若省略: 只能验证机器 JSONL，不能保护可读日志体验
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 使用临时工作区，避免测试日志写到真实项目目录
            workspace = Path(raw_dir)  # 新增代码: 把临时目录转成 Path，方便拼接文件路径
            sample_file = workspace / "hello.txt"  # 新增代码: 准备 read_file 工具要读取的文件
            sample_file.write_text("可读日志测试内容", encoding="utf-8")  # 新增代码: 写入测试内容，后面要确认工具结果会出现在 Markdown 日志里
            model = ToolCallingFakeModel(  # 新增代码: 构造假模型，稳定模拟工具调用和最终回答
                [  # 新增代码: 假模型返回序列开始
                    ModelMessage(text="", tool_calls=[ToolCall(name="read_file", arguments={"path": "hello.txt"})]),  # 新增代码: 第一轮请求 read_file 工具
                    ModelMessage(text="已经完成可读日志测试。"),  # 新增代码: 第二轮给出最终回答
                ]  # 新增代码: 假模型返回序列结束
            )  # 新增代码: 假模型创建结束
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码: 创建 agent，权限回调保持允许
            answer = agent.run("请读取 hello.txt")  # 新增代码: 运行一次完整流程，触发日志写入
            readable_path = workspace / "debug_logs" / "agent_debug_readable.md"  # 新增代码: 约定追加版可读 Markdown 日志路径
            latest_path = workspace / "debug_logs" / "latest_run_readable.md"  # 新增代码: 约定仅保留最新一轮的 Markdown 日志路径
            readable_text = readable_path.read_text(encoding="utf-8")  # 新增代码: 读取追加版 Markdown 日志
            latest_text = latest_path.read_text(encoding="utf-8")  # 新增代码: 读取最新一轮 Markdown 日志
            self.assertIn("## 用户输入", readable_text)  # 新增代码: 验证日志有用户输入区块
            self.assertIn("请读取 hello.txt", readable_text)  # 新增代码: 验证用户原始输入可读
            self.assertIn("## 加载的系统提示词和记忆上下文", readable_text)  # 新增代码: 验证系统提示词和 memory 上下文可见
            self.assertIn("## 可用工具", readable_text)  # 新增代码: 验证可用工具列表可见
            self.assertIn("read_file", readable_text)  # 新增代码: 验证工具名可见
            self.assertIn("## 工具执行结果", readable_text)  # 新增代码: 验证工具结果区块可见
            self.assertIn("可读日志测试内容", readable_text)  # 新增代码: 验证工具返回内容可见
            self.assertIn("## 最终回答", readable_text)  # 新增代码: 验证最终回答区块可见
            self.assertIn("已经完成可读日志测试", readable_text)  # 新增代码: 验证最终回答文本可见
            self.assertIn("已经完成可读日志测试", answer)  # 新增代码: 验证新增日志不影响 agent 正常返回
            self.assertEqual(readable_text, latest_text)  # 新增代码: 单轮测试中追加版和 latest 版内容应一致，方便确认 latest 是最新一轮视图
    def test_latest_readable_debug_log_keeps_only_the_most_recent_run(self) -> None:  # 新增代码: 测试 latest_run_readable.md 只保留最近一轮，避免用户每次打开都被历史内容干扰
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码: 使用临时工作区隔离日志文件
            workspace = Path(raw_dir)  # 新增代码: 把临时目录转成 Path
            model = ToolCallingFakeModel(  # 新增代码: 构造假模型，连续给两次直接回答
                [  # 新增代码: 假模型返回序列开始
                    ModelMessage(text="第一轮回答。"),  # 新增代码: 第一轮 agent.run 的最终回答
                    ModelMessage(text="第二轮回答。"),  # 新增代码: 第二轮 agent.run 的最终回答
                ]  # 新增代码: 假模型返回序列结束
            )  # 新增代码: 假模型创建结束
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码: 创建 agent
            agent.run("第一轮输入")  # 新增代码: 运行第一轮，写入历史日志和 latest 日志
            agent.run("第二轮输入")  # 新增代码: 运行第二轮，latest 应被重置为只包含第二轮
            readable_text = (workspace / "debug_logs" / "agent_debug_readable.md").read_text(encoding="utf-8")  # 新增代码: 读取追加版日志，应该包含两轮
            latest_text = (workspace / "debug_logs" / "latest_run_readable.md").read_text(encoding="utf-8")  # 新增代码: 读取 latest 日志，应该只包含第二轮
            self.assertIn("第一轮输入", readable_text)  # 新增代码: 验证追加版日志保留第一轮历史
            self.assertIn("第二轮输入", readable_text)  # 新增代码: 验证追加版日志也包含第二轮历史
            self.assertNotIn("第一轮输入", latest_text)  # 新增代码: 验证 latest 不再包含旧一轮输入
            self.assertIn("第二轮输入", latest_text)  # 新增代码: 验证 latest 包含最新一轮输入
            self.assertIn("第二轮回答", latest_text)  # 新增代码: 验证 latest 包含最新一轮最终回答
    def test_agent_rejects_invalid_todo_status(self) -> None:  # 新增代码+TodoWrite: 验证非法任务状态会被拒绝且不写入文件；若省略: 模型传错状态可能污染任务清单
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TodoWrite: 创建临时工作区隔离测试文件；若省略: 测试可能影响真实 todo_state.json
            workspace = Path(raw_dir)  # 新增代码+TodoWrite: 转成 Path 方便定位 todo_state.json；若省略: 路径表达不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+TodoWrite: 创建允许权限的 agent；若省略: 无法直接测试工具执行逻辑
            output = agent._execute_tool(ToolCall(name="todo_write", arguments={"todos": [{"content": "坏状态", "status": "doing"}]}))  # 新增代码+TodoWrite: 提交非法 status 触发校验；若省略: 状态白名单没有红灯测试
            self.assertIn("todo_write 失败", output)  # 新增代码+TodoWrite: 断言工具返回失败前缀；若省略: 非法输入可能被误报成功
            self.assertIn("pending/in_progress/completed", output)  # 新增代码+TodoWrite: 断言错误信息提示合法状态值；若省略: 模型难以自我修正参数
            self.assertFalse((workspace / "todo_state.json").exists())  # 新增代码+TodoWrite: 断言非法输入不会落盘；若省略: 坏数据可能污染后续任务状态
    def test_agent_starts_reads_and_stops_background_command(self) -> None:  # 新增代码+后台命令: 验证 agent 能启动长命令、读取输出并停止进程；若省略: 后台命令核心闭环没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+后台命令: 创建临时工作区隔离命令 cwd 和日志；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+后台命令: 把临时目录转成 Path；若省略: 后续构造 agent 和断言路径不够清楚
            permission_requests: list[str] = []  # 新增代码+后台命令: 记录权限请求；若省略: 无法确认启动和停止命令都经过权限层
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: permission_requests.append(action) or True)  # 新增代码+后台命令: 创建允许权限的 agent 并捕获权限文本；若省略: 无法直接验证后台命令工具
            command = f'"{sys.executable}" -c "import time; print(\'ready\', flush=True); time.sleep(30)"'  # 新增代码+后台命令: 用当前 Python 启动一个会输出 ready 后等待的长命令；若省略: 测试会依赖外部命令环境而不稳定
            start_output = agent._execute_tool(ToolCall(name="start_background_command", arguments={"command": command, "label": "long-running-test"}))  # 新增代码+后台命令: 启动后台命令并获取 command_id；若省略: 后续无法读取或停止目标进程
            self.assertIn("start_background_command 成功", start_output)  # 新增代码+后台命令: 断言启动工具返回成功；若省略: 启动失败可能继续进入读取断言
            command_id = start_output.split("command_id=")[1].splitlines()[0].strip()  # 新增代码+后台命令: 从工具输出中提取 command_id；若省略: 后续 read/stop 不知道操作哪个后台进程
            read_output = ""  # 新增代码+后台命令: 准备保存最近一次读取结果；若省略: 循环后无法断言输出内容
            for _ in range(30):  # 新增代码+后台命令: 等待后台进程把 ready 刷入管道；若省略: 读取可能发生在输出产生之前而偶发失败
                read_output = agent._execute_tool(ToolCall(name="read_background_command", arguments={"command_id": command_id, "max_chars": 4000}))  # 新增代码+后台命令: 读取后台命令增量输出；若省略: 无法观察后台命令进度
                if "ready" in read_output:  # 新增代码+后台命令: 如果已经读到期望输出就停止等待；若省略: 测试会无意义地等待满时长
                    break  # 新增代码+后台命令: 提前退出等待循环；若省略: 测试会变慢
                time.sleep(0.1)  # 新增代码+后台命令: 给后台进程一点输出时间；若省略: 紧密轮询会浪费 CPU 且更容易竞态
            stop_output = agent._execute_tool(ToolCall(name="stop_background_command", arguments={"command_id": command_id}))  # 新增代码+后台命令: 停止仍在运行的长命令；若省略: 测试会残留后台进程
            self.assertIn("ready", read_output)  # 新增代码+后台命令: 断言读取工具拿到了后台进程输出；若省略: 只证明进程启动但不能证明可观察
            self.assertIn("状态：running", read_output)  # 新增代码+后台命令: 断言读取时命令仍在运行；若省略: 无法覆盖长任务后台语义
            self.assertIn("stop_background_command 成功", stop_output)  # 新增代码+后台命令: 断言停止工具成功回收进程；若省略: 进程泄漏风险不被测试捕获
            self.assertIn("启动后台命令", permission_requests[0])  # 新增代码+后台命令: 断言启动命令需要权限确认；若省略: 高风险命令可能绕过用户确认
            self.assertIn("停止后台命令", permission_requests[1])  # 新增代码+后台命令: 断言停止命令也经过权限确认；若省略: agent 可能擅自停止用户关心的任务
    def test_background_command_completion_updates_registry_without_read_command(self) -> None:  # 新增代码+BackgroundAutoNotify: 验证后台命令结束后不依赖 read 工具也会自动写入持久状态；若没有这行代码，后台任务可能完成了但主 agent 永远不知道
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+BackgroundAutoNotify: 创建临时工作区隔离后台命令状态文件；若没有这行代码，测试会污染真实项目 memory
            workspace = Path(raw_dir)  # 新增代码+BackgroundAutoNotify: 把临时路径转成 Path 方便传给 agent；若没有这行代码，后续路径拼接和断言不够清楚
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+BackgroundAutoNotify: 创建自动授权 agent 来启动真实短后台命令；若没有这行代码，无法覆盖生产后台命令路径
            command = f'"{sys.executable}" -c "print(\'BG_DONE\', flush=True)"'  # 新增代码+BackgroundAutoNotify: 构造会快速输出并退出的后台命令；若没有这行代码，测试无法稳定等待自动完成
            start_output = agent._execute_tool(ToolCall(name="start_background_command", arguments={"command": command, "label": "auto-notify-test"}))  # 新增代码+BackgroundAutoNotify: 通过真实工具启动后台命令；若没有这行代码，持久任务表和通知队列不会被创建
            self.assertIn("start_background_command 成功", start_output)  # 新增代码+BackgroundAutoNotify: 先确认命令确实启动成功；若没有这行代码，后续等待可能掩盖启动失败
            command_id = start_output.split("command_id=")[1].splitlines()[0].strip()  # 新增代码+BackgroundAutoNotify: 从工具输出提取后台命令 id；若没有这行代码，无法查询对应持久任务
            completed_record = None  # 新增代码+BackgroundAutoNotify: 准备保存自动完成后的任务记录；若没有这行代码，循环结束后没有可断言对象
            for _ in range(50):  # 新增代码+BackgroundAutoNotify: 最多等待约 5 秒让后台监控线程收束命令；若没有这行代码，异步完成会产生偶发测试失败
                current_record = agent.task_registry.get_task(command_id)  # 新增代码+BackgroundAutoNotify: 读取持久任务状态而不是内存状态；若没有这行代码，无法证明状态真正落盘
                if current_record.status == "completed":  # 新增代码+BackgroundAutoNotify: 如果后台命令已自动标记完成；若没有这行代码，循环无法提前结束
                    completed_record = current_record  # 新增代码+BackgroundAutoNotify: 保存完成记录供后续断言；若没有这行代码，完成状态会丢在循环局部
                    break  # 新增代码+BackgroundAutoNotify: 已经观察到完成就停止等待；若没有这行代码，测试会无意义等待满时长
                time.sleep(0.1)  # 新增代码+BackgroundAutoNotify: 给后台进程和监控线程一点运行时间；若没有这行代码，紧密轮询会增加竞态和 CPU 浪费
            self.assertIsNotNone(completed_record)  # 新增代码+BackgroundAutoNotify: 断言不用 read_background_command 也能自动完成；若没有这行代码，缺口会被后续通知断言掩盖
            assert completed_record is not None  # 新增代码+BackgroundAutoNotify: 告诉类型检查和读者后续记录一定存在；若没有这行代码，后续访问 output 时语义不够明确
            self.assertIn("BG_DONE", completed_record.output)  # 新增代码+BackgroundAutoNotify: 断言后台输出被自动保存进任务摘要；若没有这行代码，模型收到通知也缺少结果上下文
            queued_command = agent.runtime_command_queue.dequeue_next()  # 新增代码+BackgroundAutoNotify: 读取自动回灌给主循环的下一条命令；若没有这行代码，无法证明通知真的进入 durable queue
            self.assertIsNotNone(queued_command)  # 新增代码+BackgroundAutoNotify: 断言完成事件必须产生队列通知；若没有这行代码，后台完成仍可能只写状态不回灌模型
            assert queued_command is not None  # 新增代码+BackgroundAutoNotify: 明确后续可以访问命令字段；若没有这行代码，后续断言可读性差
            self.assertEqual(queued_command.mode, "task_notification")  # 新增代码+BackgroundAutoNotify: 断言队列项类型是任务通知；若没有这行代码，prompt 或其他命令可能误混入
            self.assertEqual(queued_command.payload.get("task_id"), command_id)  # 新增代码+BackgroundAutoNotify: 断言通知指向刚完成的后台命令；若没有这行代码，主循环可能回灌错任务
            self.assertEqual(queued_command.payload.get("status"), "completed")  # 新增代码+BackgroundAutoNotify: 断言通知状态是 completed；若没有这行代码，模型无法判断后台命令成功结束
            self.assertIn("BG_DONE", str(queued_command.payload.get("summary", "")))  # 新增代码+BackgroundAutoNotify: 断言通知摘要包含真实输出；若没有这行代码，下一轮模型仍要手动查询 task_output
    def test_background_command_rejects_workspace_escape_cwd(self) -> None:  # 新增代码+后台命令: 验证后台命令 cwd 不能逃出工作区；若省略: 模型可能在用户工作区外运行命令
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+后台命令: 创建临时工作区隔离路径校验；若省略: 测试路径可能碰到真实文件
            workspace = Path(raw_dir)  # 新增代码+后台命令: 转成 Path 传给 agent；若省略: 路径处理不够清楚
            permission_requests: list[str] = []  # 新增代码+后台命令: 记录权限请求；若省略: 无法确认非法 cwd 会在权限前被拒绝
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: permission_requests.append(action) or True)  # 新增代码+后台命令: 创建 agent 并捕获权限文本；若省略: 无法测试后台命令工具
            output = agent._execute_tool(ToolCall(name="start_background_command", arguments={"command": "echo hi", "cwd": ".."}))  # 新增代码+后台命令: 尝试把 cwd 指向工作区外；若省略: 路径越界防护没有红灯测试
            self.assertIn("start_background_command 失败", output)  # 新增代码+后台命令: 断言越界 cwd 被拒绝；若省略: 工具可能误报成功
            self.assertIn("工作区内", output)  # 新增代码+后台命令: 断言错误信息提示边界原因；若省略: 模型难以修正 cwd 参数
            self.assertEqual(permission_requests, [])  # 新增代码+后台命令: 断言非法路径不会先弹权限；若省略: 用户会被无效操作打扰
    def test_agent_formats_structured_user_question(self) -> None:  # 新增代码+AskUserQuestion: 验证 agent 能把结构化问题格式化成用户可回答文本；若省略: 结构化提问核心输出没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+AskUserQuestion: 创建临时工作区隔离 agent 文件；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+AskUserQuestion: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+AskUserQuestion: 创建测试 agent；若省略: 无法通过工具路由执行 ask_user_question
            questions = [{"id": "scope", "header": "范围", "question": "你想先做哪个范围？", "options": [{"label": "最小版", "description": "先做核心链路。"}, {"label": "完整版", "description": "同时做更多功能。"}]}]  # 新增代码+AskUserQuestion: 构造一个含两个选项的问题；若省略: 无法验证选项格式化
            output = agent._execute_tool(ToolCall(name="ask_user_question", arguments={"questions": questions}))  # 新增代码+AskUserQuestion: 通过工具路由请求结构化提问；若省略: 无法验证分发和格式化
            self.assertIn("ask_user_question 成功", output)  # 新增代码+AskUserQuestion: 断言工具返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("scope", output)  # 新增代码+AskUserQuestion: 断言问题 id 进入输出；若省略: 用户回答后模型难以对应问题
            self.assertIn("范围", output)  # 新增代码+AskUserQuestion: 断言 header 进入输出；若省略: 问题分组信息可能丢失
            self.assertIn("最小版", output)  # 新增代码+AskUserQuestion: 断言选项 label 进入输出；若省略: 用户无法选择预设选项
            self.assertIn("先做核心链路", output)  # 新增代码+AskUserQuestion: 断言选项说明进入输出；若省略: 用户无法理解选项差异
    def test_ask_user_question_rejects_empty_questions(self) -> None:  # 新增代码+AskUserQuestion: 验证 questions 为空时返回可读失败；若省略: 模型传错参数可能得到模糊结果
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+AskUserQuestion: 创建临时工作区隔离测试；若省略: 测试可能影响真实工作区
            workspace = Path(raw_dir)  # 新增代码+AskUserQuestion: 把临时目录转成 Path；若省略: agent 构造不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+AskUserQuestion: 创建测试 agent；若省略: 无法执行 ask_user_question
            output = agent._execute_tool(ToolCall(name="ask_user_question", arguments={"questions": []}))  # 新增代码+AskUserQuestion: 提交空问题数组触发校验；若省略: 空 questions 分支没有测试输入
            self.assertIn("ask_user_question 失败", output)  # 新增代码+AskUserQuestion: 断言空问题返回失败前缀；若省略: 错误状态可能被误判为成功
            self.assertIn("1 到 3", output)  # 新增代码+AskUserQuestion: 断言错误说明问题数量范围；若省略: 模型难以修正 questions 数量
    def test_task_output_reads_completed_child_agent_result(self) -> None:  # 新增代码+TaskLifecycle: 验证 task 会记录 task_id 且 task_output 能读回结果；若省略: 子 agent 执行结果无法二次查询
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TaskLifecycle: 创建临时工作区隔离子任务记录；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+TaskLifecycle: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            model = RecordingToolNameFakeModel(ModelMessage(text="子任务完成：输出可被查询。"))  # 新增代码+TaskLifecycle: 创建会返回固定子任务结果的假模型；若省略: 无法验证 output 工具读到真实结果
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+TaskLifecycle: 创建测试 agent；若省略: 无法通过工具路由执行 task 和 task_output
            task_output = agent._execute_tool(ToolCall(name="task", arguments={"prompt": "生成可查询输出", "allowed_tools": ["read_file"], "max_turns": 1}))  # 新增代码+TaskLifecycle: 先启动子 agent 并期待返回 task_id；若省略: task_output 没有可查询目标
            task_id_line = next((line for line in task_output.splitlines() if line.startswith("task_id=")), "")  # 新增代码+TaskLifecycle: 从 task 输出中查找 task_id 行；若省略: 缺少 task_id 时测试会报生成器异常而不是清楚失败
            self.assertTrue(task_id_line, task_output)  # 新增代码+TaskLifecycle: 断言 task 输出必须包含 task_id；若省略: 生命周期缺口会表现成难懂的 StopIteration
            task_id = task_id_line.split("=", 1)[1].strip()  # 新增代码+TaskLifecycle: 从 task_id 行提取真实 id；若省略: 后续无法指定要查询哪个任务
            lookup_output = agent._execute_tool(ToolCall(name="task_output", arguments={"task_id": task_id, "max_chars": 2000}))  # 新增代码+TaskLifecycle: 查询刚完成的子任务输出；若省略: 无法验证 task_output 分发和读取记录
            self.assertIn("task_output 成功", lookup_output)  # 新增代码+TaskLifecycle: 断言查询工具返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("status=completed", lookup_output)  # 新增代码+TaskLifecycle: 断言完成状态被记录；若省略: 生命周期状态缺失不会被发现
            self.assertIn("子任务完成", lookup_output)  # 新增代码+TaskLifecycle: 断言子 agent 输出可被二次查询；若省略: task_output 可能只返回元信息不返回结果
    def test_task_stop_reports_completed_task_does_not_need_stop(self) -> None:  # 新增代码+TaskLifecycle: 验证 task_stop 对已完成任务给出可读结果；若省略: stop 工具边界行为没有保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TaskLifecycle: 创建临时工作区隔离子任务记录；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+TaskLifecycle: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            model = RecordingToolNameFakeModel(ModelMessage(text="子任务完成：无需停止。"))  # 新增代码+TaskLifecycle: 创建会立即完成的假模型；若省略: 无法构造已完成任务场景
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+TaskLifecycle: 创建测试 agent；若省略: 无法执行 task 和 task_stop
            task_output = agent._execute_tool(ToolCall(name="task", arguments={"prompt": "立即完成任务", "allowed_tools": ["read_file"], "max_turns": 1}))  # 新增代码+TaskLifecycle: 先启动并完成一个子任务；若省略: task_stop 没有目标任务
            task_id_line = next((line for line in task_output.splitlines() if line.startswith("task_id=")), "")  # 新增代码+TaskLifecycle: 从 task 输出中查找 task_id 行；若省略: 缺少 task_id 时测试会报生成器异常而不是清楚失败
            self.assertTrue(task_id_line, task_output)  # 新增代码+TaskLifecycle: 断言 task 输出必须包含 task_id；若省略: 生命周期缺口会表现成难懂的 StopIteration
            task_id = task_id_line.split("=", 1)[1].strip()  # 新增代码+TaskLifecycle: 从 task_id 行提取真实 id；若省略: 后续无法指定要停止哪个任务
            stop_output = agent._execute_tool(ToolCall(name="task_stop", arguments={"task_id": task_id, "reason": "测试停止"}))  # 新增代码+TaskLifecycle: 请求停止已完成任务以验证边界提示；若省略: task_stop 成功路径没有测试输入
            self.assertIn("task_stop 成功", stop_output)  # 新增代码+TaskLifecycle: 断言 stop 工具返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("已经完成", stop_output)  # 新增代码+TaskLifecycle: 断言已完成任务不会被错误标记为运行中；若省略: stop 边界语义可能混乱
    def test_task_background_runs_without_blocking_and_can_be_stopped(self) -> None:  # 新增代码+AsyncTask: 验证 background=true 会后台运行并允许 stop 标记运行中任务；若省略: task 仍可能阻塞主 agent
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+AsyncTask: 创建临时工作区隔离后台任务记录；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+AsyncTask: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            model = BlockingChatFakeModel()  # 新增代码+AsyncTask: 创建会短暂阻塞的假模型；若省略: 无法证明后台 task 不是同步阻塞
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+AsyncTask: 创建测试 agent；若省略: 无法执行 background task
            started_at = time.monotonic()  # 新增代码+AsyncTask: 记录调用 task 前的单调时间；若省略: 无法判断 task 是否快速返回
            task_output = agent._execute_tool(ToolCall(name="task", arguments={"prompt": "后台分析", "allowed_tools": ["read_file"], "max_turns": 1, "background": True}))  # 新增代码+AsyncTask: 请求后台执行子任务；若省略: 无法触发异步路径
            elapsed = time.monotonic() - started_at  # 新增代码+AsyncTask: 计算 task 工具调用耗时；若省略: 无法断言主 agent 未被阻塞
            self.assertLess(elapsed, 0.2)  # 新增代码+AsyncTask: 断言 background task 应快速返回；若省略: 同步阻塞回归不会被发现
            self.assertIn("后台启动", task_output)  # 新增代码+AsyncTask: 断言返回文本说明任务已在后台启动；若省略: 模型难以区分同步完成和后台运行
            task_id_line = next((line for line in task_output.splitlines() if line.startswith("task_id=")), "")  # 新增代码+AsyncTask: 从 task 输出中查找 task_id 行；若省略: 后续无法查询或停止后台任务
            self.assertTrue(task_id_line, task_output)  # 新增代码+AsyncTask: 断言后台 task 输出必须包含 task_id；若省略: 生命周期查询无从开始
            task_id = task_id_line.split("=", 1)[1].strip()  # 新增代码+AsyncTask: 提取 task_id；若省略: 后续工具调用无法指定目标任务
            self.assertTrue(model.started.wait(timeout=1.0))  # 新增代码+AsyncTask: 等待后台模型调用真正开始；若省略: running 状态断言可能存在竞态
            running_output = agent._execute_tool(ToolCall(name="task_output", arguments={"task_id": task_id, "max_chars": 2000}))  # 新增代码+AsyncTask: 查询后台任务当前状态；若省略: 无法验证 task_output 能看到 running
            self.assertIn("status=running", running_output)  # 新增代码+AsyncTask: 断言后台任务仍在运行；若省略: task 可能仍是同步完成路径
            stop_output = agent._execute_tool(ToolCall(name="task_stop", arguments={"task_id": task_id, "reason": "用户取消后台任务"}))  # 新增代码+AsyncTask: 请求停止运行中的后台任务；若省略: task_stop 真正取消语义没有测试输入
            self.assertIn("stopped", stop_output)  # 新增代码+AsyncTask: 断言 stop 会把运行中后台任务标记为 stopped；若省略: stop 可能只对已完成任务有用
            stopped_output = agent._execute_tool(ToolCall(name="task_output", arguments={"task_id": task_id, "max_chars": 2000}))  # 新增代码+AsyncTask: 再次查询后台任务状态；若省略: 无法确认 stop 状态写回记录
            self.assertIn("status=stopped", stopped_output)  # 新增代码+AsyncTask: 断言任务记录已变为 stopped；若省略: task_stop 状态更新回归不会被发现
            model.release.set()  # 新增代码+AsyncTask: 释放后台假模型让测试线程可收尾；若省略: 后台 daemon 线程会等到超时才结束
            task_thread = agent.task_runs[task_id].thread  # 新增代码+AsyncTask: 读取任务记录里的后台线程对象；若省略: 测试无法等待后台线程退出
            self.assertIsNotNone(task_thread)  # 新增代码+AsyncTask: 断言后台任务记录保存线程对象；若省略: 线程管理缺口不会被发现
            task_thread.join(timeout=1.0)  # 新增代码+AsyncTask: 等待后台线程收尾，避免测试结束时仍有活动线程；若省略: 后续测试可能受后台线程影响
    def test_task_list_get_update_manage_child_task_metadata(self) -> None:  # 新增代码+TaskManagement: 验证任务列表、详情读取和备注更新闭环；若省略: 多子任务管理视图没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TaskManagement: 创建临时工作区隔离任务记录；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+TaskManagement: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            model = RecordingToolNameFakeModel(ModelMessage(text="子任务完成：可被管理。"))  # 新增代码+TaskManagement: 创建会立即完成的假模型；若省略: 无法构造可管理的 completed 任务
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+TaskManagement: 创建测试 agent；若省略: 无法执行 task 和管理工具
            task_output = agent._execute_tool(ToolCall(name="task", arguments={"prompt": "整理任务管理信息", "allowed_tools": ["read_file"], "max_turns": 1}))  # 新增代码+TaskManagement: 先创建一个真实子任务记录；若省略: task_list/task_get/task_update 没有目标任务
            task_id_line = next((line for line in task_output.splitlines() if line.startswith("task_id=")), "")  # 新增代码+TaskManagement: 从 task 输出中查找 task_id 行；若省略: 缺少 task_id 时测试会报难懂异常
            self.assertTrue(task_id_line, task_output)  # 新增代码+TaskManagement: 断言 task 输出必须包含 task_id；若省略: 生命周期缺口会被后续断言掩盖
            task_id = task_id_line.split("=", 1)[1].strip()  # 新增代码+TaskManagement: 提取 task_id 供管理工具引用；若省略: 无法指定要查询或更新哪个任务
            list_output = agent._execute_tool(ToolCall(name="task_list", arguments={"status": "completed", "max_results": 10}))  # 新增代码+TaskManagement: 按 completed 状态列出任务；若省略: 状态筛选功能没有测试输入
            self.assertIn("task_list 成功", list_output)  # 新增代码+TaskManagement: 断言列表工具返回成功前缀；若省略: 未知工具也可能被后续文本断言误判
            self.assertIn(task_id, list_output)  # 新增代码+TaskManagement: 断言刚创建的任务出现在列表中；若省略: 列表可能漏掉任务却不报警
            self.assertIn("status=completed", list_output)  # 新增代码+TaskManagement: 断言列表摘要展示状态；若省略: 模型难以按列表判断任务进度
            get_output = agent._execute_tool(ToolCall(name="task_get", arguments={"task_id": task_id, "max_chars": 2000}))  # 新增代码+TaskManagement: 读取单任务详情；若省略: task_get 核心行为没有测试输入
            self.assertIn("task_get 成功", get_output)  # 新增代码+TaskManagement: 断言详情工具返回成功前缀；若省略: 未知工具或失败输出可能被误判
            self.assertIn("prompt=整理任务管理信息", get_output)  # 新增代码+TaskManagement: 断言详情包含原始 prompt；若省略: 主 agent 无法追溯任务目标
            self.assertIn("notes=(无备注)", get_output)  # 新增代码+TaskManagement: 断言未更新前有清楚备注占位；若省略: 空备注会降低可读性
            update_output = agent._execute_tool(ToolCall(name="task_update", arguments={"task_id": task_id, "label": "资料整理", "notes": "等待用户复核"}))  # 新增代码+TaskManagement: 更新任务标签和备注；若省略: 元信息更新功能没有测试输入
            self.assertIn("task_update 成功", update_output)  # 新增代码+TaskManagement: 断言更新工具返回成功前缀；若省略: 更新失败可能被后续详情断言误读
            updated_output = agent._execute_tool(ToolCall(name="task_get", arguments={"task_id": task_id, "max_chars": 2000}))  # 新增代码+TaskManagement: 再次读取详情确认更新落地；若省略: 无法证明 task_update 真的修改记录
            self.assertIn("label=资料整理", updated_output)  # 新增代码+TaskManagement: 断言标签已写入任务记录；若省略: 标签更新回归不会被发现
            self.assertIn("notes=等待用户复核", updated_output)  # 新增代码+TaskManagement: 断言备注已写入任务记录；若省略: 备注更新回归不会被发现
    def test_team_create_send_message_and_list_peers(self) -> None:  # 新增代码+TeamCommunication: 验证创建 peer、发送消息、查看 inbox 数量的闭环；若省略: 多 agent 通信层没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TeamCommunication: 创建临时工作区隔离 agent 状态；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+TeamCommunication: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+TeamCommunication: 创建测试 agent；若省略: 无法直接执行 team 工具
            create_output = agent._execute_tool(ToolCall(name="team_create", arguments={"name": "资料探索员", "role": "explorer", "notes": "负责只读探索"}))  # 新增代码+TeamCommunication: 创建一个教学版 peer；若省略: send_message/list_peers 没有目标 peer
            self.assertIn("team_create 成功", create_output)  # 新增代码+TeamCommunication: 断言创建工具返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            peer_id_line = next((line for line in create_output.splitlines() if line.startswith("peer_id=")), "")  # 新增代码+TeamCommunication: 从创建结果中查找 peer_id 行；若省略: 缺少 peer_id 时测试会报难懂异常
            self.assertTrue(peer_id_line, create_output)  # 新增代码+TeamCommunication: 断言创建结果必须包含 peer_id；若省略: 后续工具无法引用目标 peer
            peer_id = peer_id_line.split("=", 1)[1].strip()  # 新增代码+TeamCommunication: 提取 peer_id 供发送消息和列表断言使用；若省略: send_message 无法指定目标
            before_message_output = agent._execute_tool(ToolCall(name="list_peers", arguments={"max_results": 10}))  # 新增代码+TeamCommunication: 发送消息前查看 peer 总览；若省略: 无法验证初始 inbox 数量
            self.assertIn(peer_id, before_message_output)  # 新增代码+TeamCommunication: 断言新 peer 出现在列表中；若省略: 创建记录可能没有进入列表却不报警
            self.assertIn("role=explorer", before_message_output)  # 新增代码+TeamCommunication: 断言列表展示 peer 角色；若省略: 模型难以按角色选择通信对象
            self.assertIn("inbox_count=0", before_message_output)  # 新增代码+TeamCommunication: 断言新 peer 初始没有消息；若省略: inbox 计数初始状态没有保护
            message_output = agent._execute_tool(ToolCall(name="send_message", arguments={"peer_id": peer_id, "message": "请阅读 README 并总结工具差距。", "sender": "main"}))  # 新增代码+TeamCommunication: 向 peer 发送一条消息；若省略: 消息队列写入路径没有测试输入
            self.assertIn("send_message 成功", message_output)  # 新增代码+TeamCommunication: 断言发送工具返回成功前缀；若省略: 发送失败可能被后续列表断言掩盖
            self.assertIn("message_id=", message_output)  # 新增代码+TeamCommunication: 断言发送结果包含 message_id；若省略: 后续审计消息缺少稳定编号
            after_message_output = agent._execute_tool(ToolCall(name="list_peers", arguments={"max_results": 10}))  # 新增代码+TeamCommunication: 发送后再次查看 peer 总览；若省略: 无法证明 inbox 数量被更新
            self.assertIn("inbox_count=1", after_message_output)  # 新增代码+TeamCommunication: 断言消息进入 peer inbox；若省略: send_message 可能没有真正保存消息
            self.assertIn("请阅读 README", after_message_output)  # 新增代码+TeamCommunication: 断言列表展示最新消息摘要；若省略: 模型无法从列表快速知道 peer 收到什么
            self.assertIn("pending_count=1", after_message_output)  # 新增代码+TeamCommunicationLifecycle: 断言列表展示待确认消息数量；若省略: 主 agent 不知道 peer 还有多少消息未处理
    def test_read_and_ack_peer_messages(self) -> None:  # 新增代码+TeamCommunicationLifecycle: 验证读取 peer inbox 并确认指定消息的闭环；若省略: 消息确认能力没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TeamCommunicationLifecycle: 创建临时工作区隔离 agent 状态；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+TeamCommunicationLifecycle: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+TeamCommunicationLifecycle: 创建测试 agent；若省略: 无法直接执行 peer 消息工具
            create_output = agent._execute_tool(ToolCall(name="team_create", arguments={"name": "验证员", "role": "verifier"}))  # 新增代码+TeamCommunicationLifecycle: 创建一个 peer 作为消息收件箱；若省略: 后续读取和确认没有目标 peer
            peer_id = next(line for line in create_output.splitlines() if line.startswith("peer_id=")).split("=", 1)[1].strip()  # 新增代码+TeamCommunicationLifecycle: 提取 peer_id 用于后续工具调用；若省略: 无法指定目标 peer
            first_message_output = agent._execute_tool(ToolCall(name="send_message", arguments={"peer_id": peer_id, "message": "请先跑专项测试。"}))  # 新增代码+TeamCommunicationLifecycle: 发送第一条待确认消息；若省略: ack 工具没有目标消息
            second_message_output = agent._execute_tool(ToolCall(name="send_message", arguments={"peer_id": peer_id, "message": "再跑完整测试。"}))  # 新增代码+TeamCommunicationLifecycle: 发送第二条待确认消息；若省略: 无法验证确认一条后仍保留另一条
            first_message_id = next(line for line in first_message_output.splitlines() if line.startswith("message_id=")).split("=", 1)[1].strip()  # 新增代码+TeamCommunicationLifecycle: 提取第一条消息 id；若省略: ack_peer_message 无法指定具体消息
            second_message_id = next(line for line in second_message_output.splitlines() if line.startswith("message_id=")).split("=", 1)[1].strip()  # 新增代码+TeamCommunicationLifecycle: 提取第二条消息 id；若省略: 测试无法确认未处理消息仍存在
            read_output = agent._execute_tool(ToolCall(name="read_peer_messages", arguments={"peer_id": peer_id, "max_results": 10}))  # 新增代码+TeamCommunicationLifecycle: 读取 peer inbox 的待确认消息；若省略: 无法验证读取工具输出
            self.assertIn("read_peer_messages 成功", read_output)  # 新增代码+TeamCommunicationLifecycle: 断言读取工具成功；若省略: 未知工具输出可能被误判为正常列表
            self.assertIn(first_message_id, read_output)  # 新增代码+TeamCommunicationLifecycle: 断言第一条消息在读取结果中；若省略: 读取工具可能漏消息
            self.assertIn(second_message_id, read_output)  # 新增代码+TeamCommunicationLifecycle: 断言第二条消息在读取结果中；若省略: 读取工具可能只返回部分消息
            self.assertIn("acknowledged=false", read_output)  # 新增代码+TeamCommunicationLifecycle: 断言未确认消息会显示确认状态；若省略: 模型无法判断消息是否处理过
            ack_output = agent._execute_tool(ToolCall(name="ack_peer_message", arguments={"peer_id": peer_id, "message_id": first_message_id, "note": "专项测试已通过"}))  # 新增代码+TeamCommunicationLifecycle: 确认第一条消息并写入备注；若省略: ack 路径没有测试输入
            self.assertIn("ack_peer_message 成功", ack_output)  # 新增代码+TeamCommunicationLifecycle: 断言确认工具成功；若省略: ack 失败可能被后续读取掩盖
            self.assertIn("pending_count=1", ack_output)  # 新增代码+TeamCommunicationLifecycle: 断言确认后仍有一条待处理消息；若省略: ack 可能错误清空全部消息却不报警
            pending_output = agent._execute_tool(ToolCall(name="read_peer_messages", arguments={"peer_id": peer_id, "max_results": 10}))  # 新增代码+TeamCommunicationLifecycle: 再次读取默认待确认消息；若省略: 无法验证已确认消息默认不再出现
            self.assertNotIn(first_message_id, pending_output)  # 新增代码+TeamCommunicationLifecycle: 断言已确认消息默认被隐藏；若省略: 默认读取会混入已处理消息
            self.assertIn(second_message_id, pending_output)  # 新增代码+TeamCommunicationLifecycle: 断言未确认消息仍然可见；若省略: ack 可能误删其他消息
            all_output = agent._execute_tool(ToolCall(name="read_peer_messages", arguments={"peer_id": peer_id, "include_acknowledged": True, "max_results": 10}))  # 新增代码+TeamCommunicationLifecycle: 带 include_acknowledged 读取全部消息；若省略: 无法验证审计读取已确认消息
            self.assertIn(first_message_id, all_output)  # 新增代码+TeamCommunicationLifecycle: 断言全部读取包含已确认消息；若省略: 历史审计能力可能缺失
            self.assertIn("ack_note=专项测试已通过", all_output)  # 新增代码+TeamCommunicationLifecycle: 断言确认备注可审计；若省略: ack note 可能写入失败而不报警
    def test_team_delete_removes_peer_and_blocks_later_messages(self) -> None:  # 新增代码+TeamCommunicationLifecycle: 验证删除 peer 后列表和发送消息都会反映删除；若省略: team_delete 的核心行为没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TeamCommunicationLifecycle: 创建临时工作区隔离 agent 状态；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+TeamCommunicationLifecycle: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+TeamCommunicationLifecycle: 创建测试 agent；若省略: 无法直接执行删除工具
            create_output = agent._execute_tool(ToolCall(name="team_create", arguments={"name": "临时实现员", "role": "worker"}))  # 新增代码+TeamCommunicationLifecycle: 创建一个将被删除的 peer；若省略: 删除工具没有目标
            peer_id = next(line for line in create_output.splitlines() if line.startswith("peer_id=")).split("=", 1)[1].strip()  # 新增代码+TeamCommunicationLifecycle: 提取 peer_id 用于删除；若省略: team_delete 无法指定目标
            delete_without_confirm_output = agent._execute_tool(ToolCall(name="team_delete", arguments={"peer_id": peer_id}))  # 新增代码+TeamCommunicationLifecycle: 未确认删除先尝试一次；若省略: 无法验证删除需要显式确认
            self.assertIn("team_delete 失败", delete_without_confirm_output)  # 新增代码+TeamCommunicationLifecycle: 断言缺少确认时拒绝删除；若省略: 模型可能无确认删除 peer
            delete_output = agent._execute_tool(ToolCall(name="team_delete", arguments={"peer_id": peer_id, "confirm_delete": True}))  # 新增代码+TeamCommunicationLifecycle: 带显式确认删除 peer；若省略: 删除成功路径没有测试输入
            self.assertIn("team_delete 成功", delete_output)  # 新增代码+TeamCommunicationLifecycle: 断言删除工具成功；若省略: 删除失败不会被直接发现
            self.assertIn(peer_id, delete_output)  # 新增代码+TeamCommunicationLifecycle: 断言删除结果包含目标 peer id；若省略: 用户难以审计删除了谁
            list_output = agent._execute_tool(ToolCall(name="list_peers", arguments={"max_results": 10}))  # 新增代码+TeamCommunicationLifecycle: 删除后查看 peer 列表；若省略: 无法验证登记表已移除 peer
            self.assertNotIn(peer_id, list_output)  # 新增代码+TeamCommunicationLifecycle: 断言被删 peer 不再出现；若省略: team_delete 可能只返回成功但没有删除
            send_after_delete_output = agent._execute_tool(ToolCall(name="send_message", arguments={"peer_id": peer_id, "message": "删除后不应收到"}))  # 新增代码+TeamCommunicationLifecycle: 删除后尝试发送消息；若省略: 无法验证删除后的引用被阻止
            self.assertIn("未知 peer_id", send_after_delete_output)  # 新增代码+TeamCommunicationLifecycle: 断言删除后不能继续发消息；若省略: 已删除 peer 可能仍能收到消息
    def test_team_start_task_binds_peer_to_background_task(self) -> None:  # 新增代码+TeamTaskBinding: 验证 peer 可以启动并绑定后台 task；若省略: team 与 task 的真实协作连接没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TeamTaskBinding: 创建临时工作区隔离 agent 状态；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+TeamTaskBinding: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            model = BlockingChatFakeModel()  # 新增代码+TeamTaskBinding: 创建会阻塞的假模型以保持后台 task running；若省略: 无法稳定观察 peer 绑定运行中 task
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True)  # 新增代码+TeamTaskBinding: 创建测试 agent；若省略: 无法通过工具路由执行 team_start_task
            create_output = agent._execute_tool(ToolCall(name="team_create", arguments={"name": "实现员", "role": "worker"}))  # 新增代码+TeamTaskBinding: 创建一个将绑定后台 task 的 peer；若省略: team_start_task 没有目标 peer
            peer_id = next(line for line in create_output.splitlines() if line.startswith("peer_id=")).split("=", 1)[1].strip()  # 新增代码+TeamTaskBinding: 提取 peer_id 用于启动任务；若省略: team_start_task 无法指定目标 peer
            started_at = time.monotonic()  # 新增代码+TeamTaskBinding: 记录调用前时间用于验证后台启动不阻塞；若省略: 无法发现 team_start_task 退化成同步执行
            start_output = agent._execute_tool(ToolCall(name="team_start_task", arguments={"peer_id": peer_id, "prompt": "后台实现一个小功能", "allowed_tools": ["read_file"], "max_turns": 1}))  # 新增代码+TeamTaskBinding: 请求 peer 绑定后台子任务；若省略: team_start_task 核心路径没有测试输入
            elapsed = time.monotonic() - started_at  # 新增代码+TeamTaskBinding: 计算工具调用耗时；若省略: 无法断言主 agent 没被后台 task 阻塞
            self.assertLess(elapsed, 0.2)  # 新增代码+TeamTaskBinding: 断言 team_start_task 应快速返回；若省略: 后台绑定可能悄悄变成同步阻塞
            self.assertIn("team_start_task 成功", start_output)  # 新增代码+TeamTaskBinding: 断言启动工具返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn(f"peer_id={peer_id}", start_output)  # 新增代码+TeamTaskBinding: 断言输出包含被绑定 peer；若省略: 用户难以审计任务归属
            self.assertIn("background=true", start_output)  # 新增代码+TeamTaskBinding: 断言绑定任务明确是后台 task；若省略: 模型可能误以为同步任务已经完成
            task_id = next(line for line in start_output.splitlines() if line.startswith("task_id=")).split("=", 1)[1].strip()  # 新增代码+TeamTaskBinding: 提取 task_id 用于后续 task_output/task_stop；若省略: 无法验证任务管理工具仍可接管
            self.assertTrue(model.started.wait(timeout=1.0))  # 新增代码+TeamTaskBinding: 等待后台模型调用真正开始；若省略: running 状态断言可能存在竞态
            list_output = agent._execute_tool(ToolCall(name="list_peers", arguments={"max_results": 10}))  # 新增代码+TeamTaskBinding: 查看 peer 总览以验证绑定信息；若省略: 无法证明 peer 记录展示 task 绑定
            self.assertIn(f"bound_task_id={task_id}", list_output)  # 新增代码+TeamTaskBinding: 断言 peer 列表展示绑定的 task_id；若省略: 主 agent 无法从 team 视图跳转到 task_output
            self.assertIn("task_status=running", list_output)  # 新增代码+TeamTaskBinding: 断言 peer 列表展示任务运行状态；若省略: team 视图无法反映 peer 是否正在工作
            task_output = agent._execute_tool(ToolCall(name="task_output", arguments={"task_id": task_id, "max_chars": 2000}))  # 新增代码+TeamTaskBinding: 用原 task_output 查询绑定任务；若省略: 无法证明绑定复用现有任务生命周期
            self.assertIn("status=running", task_output)  # 新增代码+TeamTaskBinding: 断言 task_output 能看到运行中状态；若省略: 绑定可能没有真正创建 task 记录
            stop_output = agent._execute_tool(ToolCall(name="task_stop", arguments={"task_id": task_id, "reason": "测试停止 peer 绑定任务"}))  # 新增代码+TeamTaskBinding: 用原 task_stop 停止绑定任务；若省略: 无法验证绑定任务仍可停止
            self.assertIn("stopped", stop_output)  # 新增代码+TeamTaskBinding: 断言 task_stop 能停止绑定任务；若省略: peer 绑定可能绕过任务生命周期管理
            stopped_peer_output = agent._execute_tool(ToolCall(name="list_peers", arguments={"max_results": 10}))  # 新增代码+TeamTaskBinding: 停止后再次查看 peer 总览；若省略: 无法验证 task 状态会反映回 team 视图
            self.assertIn("task_status=stopped", stopped_peer_output)  # 新增代码+TeamTaskBinding: 断言 team 视图展示停止状态；若省略: peer 状态可能与 task 记录脱节
            model.release.set()  # 新增代码+TeamTaskBinding: 释放阻塞假模型让后台线程收尾；若省略: 后台 daemon 线程会等到超时才结束
            task_thread = agent.task_runs[task_id].thread  # 新增代码+TeamTaskBinding: 读取绑定 task 的线程对象；若省略: 测试无法等待后台线程退出
            self.assertIsNotNone(task_thread)  # 新增代码+TeamTaskBinding: 断言后台任务保存线程对象；若省略: 线程管理缺口不会被发现
            task_thread.join(timeout=1.0)  # 新增代码+TeamTaskBinding: 等待后台线程收尾，避免影响后续测试；若省略: 后续测试可能受后台线程影响
    def test_agent_enters_and_exits_plan_mode(self) -> None:  # 新增代码+PlanMode: 验证 agent 能进入计划模式并输出待确认计划；若省略: Plan mode 核心行为没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PlanMode: 创建临时工作区隔离 agent 文件和日志；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+PlanMode: 把临时目录转成 Path；若省略: 后续构造 agent 不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+PlanMode: 创建测试 agent；若省略: 无法通过工具路由执行 Plan mode
            enter_output = agent._execute_tool(ToolCall(name="enter_plan_mode", arguments={"reason": "复杂代码改动", "goal": "先写计划再执行", "steps": ["读代码", "写测试"]}))  # 新增代码+PlanMode: 请求进入计划模式并记录初始目标；若省略: 无法验证 enter_plan_mode 分发和状态保存
            self.assertIn("enter_plan_mode 成功", enter_output)  # 新增代码+PlanMode: 断言进入计划模式返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("复杂代码改动", enter_output)  # 新增代码+PlanMode: 断言进入原因进入输出；若省略: 计划模式缺少上下文
            exit_output = agent._execute_tool(ToolCall(name="exit_plan_mode", arguments={"plan": "先补测试，再实现 Plan mode。", "steps": ["补红灯测试", "实现工具", "运行测试"]}))  # 新增代码+PlanMode: 请求输出最终计划并等待用户确认；若省略: 无法验证 exit_plan_mode 成功路径
            self.assertIn("exit_plan_mode 成功", exit_output)  # 新增代码+PlanMode: 断言退出计划模式返回成功前缀；若省略: 失败输出可能被后续断言误判
            self.assertIn("等待用户确认", exit_output)  # 新增代码+PlanMode: 断言工具明确要求用户确认后再执行；若省略: agent 可能计划后直接动手
            self.assertIn("先补测试", exit_output)  # 新增代码+PlanMode: 断言最终计划正文进入输出；若省略: 主模型拿不到可展示计划
    def test_exit_plan_mode_requires_enter_first(self) -> None:  # 新增代码+PlanMode: 验证未进入计划模式时不能直接 exit；若省略: 模型可能跳过进入计划模式的边界
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PlanMode: 创建临时工作区隔离测试；若省略: 测试可能影响真实工作区
            workspace = Path(raw_dir)  # 新增代码+PlanMode: 把临时目录转成 Path；若省略: agent 构造不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+PlanMode: 创建测试 agent；若省略: 无法执行 exit_plan_mode
            output = agent._execute_tool(ToolCall(name="exit_plan_mode", arguments={"plan": "直接输出计划"}))  # 新增代码+PlanMode: 未进入计划模式直接退出以触发校验；若省略: 失败分支没有测试输入
            self.assertIn("exit_plan_mode 失败", output)  # 新增代码+PlanMode: 断言未进入时返回失败前缀；若省略: 错误状态可能被误判为成功
            self.assertIn("enter_plan_mode", output)  # 新增代码+PlanMode: 断言错误提示先调用 enter_plan_mode；若省略: 模型难以修正调用顺序
    def test_verify_plan_execution_reports_verified_with_evidence(self) -> None:  # 新增代码+PlanVerification: 验证计划执行验证工具能在有证据且无遗漏时返回 verified；若省略: Plan mode 后的验证闭环没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PlanVerification: 创建临时工作区隔离 agent 状态；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+PlanVerification: 把临时目录转成 Path；若省略: agent 构造不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+PlanVerification: 创建测试 agent；若省略: 无法通过工具路由执行 verify_plan_execution
            agent._execute_tool(ToolCall(name="enter_plan_mode", arguments={"reason": "复杂改动", "goal": "验证计划执行"}))  # 新增代码+PlanVerification: 先进入计划模式以模拟真实计划流；若省略: 无法验证工具可读取最近计划上下文
            agent._execute_tool(ToolCall(name="exit_plan_mode", arguments={"plan": "先补测试，再实现工具。", "steps": ["补测试", "实现工具"]}))  # 新增代码+PlanVerification: 保存最近计划供验证工具兜底使用；若省略: verify_plan_execution 无法证明可接在 exit_plan_mode 后面
            output = agent._execute_tool(ToolCall(name="verify_plan_execution", arguments={"executed_steps": ["补测试", "实现工具"], "evidence": ["专项测试通过", "完整 unittest 通过"], "open_items": [], "result": "verified"}))  # 新增代码+PlanVerification: 提交执行步骤、证据和无遗漏结果；若省略: verified 成功路径没有测试输入
            self.assertIn("verify_plan_execution 成功", output)  # 新增代码+PlanVerification: 断言验证工具返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("status=verified", output)  # 新增代码+PlanVerification: 断言无遗漏且有证据时状态为 verified；若省略: 工具可能无法区分完成和未完成
            self.assertIn("executed_step_count=2", output)  # 新增代码+PlanVerification: 断言执行步骤数量进入摘要；若省略: 用户无法快速审计完成了多少步骤
            self.assertIn("evidence_count=2", output)  # 新增代码+PlanVerification: 断言证据数量进入摘要；若省略: 用户无法快速判断验证依据是否充足
            self.assertIn("open_item_count=0", output)  # 新增代码+PlanVerification: 断言无遗漏项被明确展示；若省略: 用户无法判断是否还有未完成事项
    def test_verify_plan_execution_reports_incomplete_with_open_items(self) -> None:  # 新增代码+PlanVerification: 验证存在遗漏项时工具返回 incomplete；若省略: 计划验证可能把未完成任务误报为完成
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+PlanVerification: 创建临时工作区隔离 agent 状态；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+PlanVerification: 把临时目录转成 Path；若省略: agent 构造不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+PlanVerification: 创建测试 agent；若省略: 无法通过工具路由执行 verify_plan_execution
            output = agent._execute_tool(ToolCall(name="verify_plan_execution", arguments={"plan": "补工具并验证。", "executed_steps": ["补工具"], "evidence": ["专项测试通过"], "open_items": ["完整 unittest 尚未运行"], "result": "incomplete"}))  # 新增代码+PlanVerification: 提交带遗漏项的验证结果；若省略: incomplete 分支没有测试输入
            self.assertIn("verify_plan_execution 成功", output)  # 新增代码+PlanVerification: 断言验证工具成功处理输入；若省略: 失败输出可能被后续断言掩盖
            self.assertIn("status=incomplete", output)  # 新增代码+PlanVerification: 断言存在 open_items 时状态为 incomplete；若省略: 工具可能误报 verified
            self.assertIn("open_item_count=1", output)  # 新增代码+PlanVerification: 断言遗漏项数量进入摘要；若省略: 用户无法快速判断剩余事项数量
            self.assertIn("完整 unittest 尚未运行", output)  # 新增代码+PlanVerification: 断言遗漏项正文进入输出；若省略: 用户不知道还缺哪一步
    def test_agent_enters_and_exits_worktree_state(self) -> None:  # 新增代码+WorktreeIsolation: 验证 agent 能进入和退出轻量 worktree 隔离状态；若省略: Worktree 最小闭环没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+WorktreeIsolation: 创建临时工作区隔离 agent 状态；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+WorktreeIsolation: 把临时目录转成 Path；若省略: agent 构造不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+WorktreeIsolation: 创建测试 agent；若省略: 无法通过工具路由执行 worktree 工具
            enter_output = agent._execute_tool(ToolCall(name="enter_worktree", arguments={"reason": "大范围改动", "goal": "隔离实现 worktree 工具", "worktree_path": ".worktrees/worktree-tools"}))  # 新增代码+WorktreeIsolation: 请求进入隔离状态并记录目标路径；若省略: enter_worktree 成功路径没有测试输入
            self.assertIn("enter_worktree 成功", enter_output)  # 新增代码+WorktreeIsolation: 断言进入工具返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("worktree_path=.worktrees/worktree-tools", enter_output)  # 新增代码+WorktreeIsolation: 断言隔离目录进入输出；若省略: 用户无法确认后续修改应落在哪个上下文
            self.assertIn("不创建真实 git worktree", enter_output)  # 新增代码+WorktreeIsolation: 断言工具说明它只是状态约束；若省略: 模型可能误以为目录已被创建
            exit_output = agent._execute_tool(ToolCall(name="exit_worktree", arguments={"summary": "已完成隔离状态工具。", "result": "finished", "open_items": []}))  # 新增代码+WorktreeIsolation: 请求退出隔离状态并提交总结；若省略: exit_worktree 成功路径没有测试输入
            self.assertIn("exit_worktree 成功", exit_output)  # 新增代码+WorktreeIsolation: 断言退出工具返回成功前缀；若省略: 失败输出可能被后续断言误判
            self.assertIn("status=finished", exit_output)  # 新增代码+WorktreeIsolation: 断言无遗漏时状态为 finished；若省略: 用户无法快速判断隔离工作是否收尾
            self.assertIn("已完成隔离状态工具", exit_output)  # 新增代码+WorktreeIsolation: 断言总结进入输出；若省略: 退出时缺少交接信息
            self.assertIn("未完成/风险项：(无)", exit_output)  # 新增代码+WorktreeIsolation: 断言无风险项被明确展示；若省略: 用户不确定是否还有遗留
    def test_exit_worktree_requires_enter_first(self) -> None:  # 新增代码+WorktreeIsolation: 验证未进入隔离状态时不能直接退出；若省略: 模型可能跳过进入边界直接结束
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+WorktreeIsolation: 创建临时工作区隔离测试；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+WorktreeIsolation: 把临时目录转成 Path；若省略: agent 构造不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+WorktreeIsolation: 创建测试 agent；若省略: 无法执行 exit_worktree
            output = agent._execute_tool(ToolCall(name="exit_worktree", arguments={"summary": "直接退出"}))  # 新增代码+WorktreeIsolation: 未进入隔离状态直接退出以触发校验；若省略: 失败分支没有测试输入
            self.assertIn("exit_worktree 失败", output)  # 新增代码+WorktreeIsolation: 断言未进入时返回失败前缀；若省略: 错误状态可能被误判为成功
            self.assertIn("enter_worktree", output)  # 新增代码+WorktreeIsolation: 断言错误提示先调用 enter_worktree；若省略: 模型难以修正调用顺序
    def test_enter_worktree_rejects_workspace_escape_path(self) -> None:  # 新增代码+WorktreeIsolation: 验证隔离路径不能指向工作区外；若省略: 工具可能引导模型把大改动放到不受控位置
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+WorktreeIsolation: 创建临时工作区隔离测试；若省略: 测试可能受真实路径影响
            workspace = Path(raw_dir)  # 新增代码+WorktreeIsolation: 把临时目录转成 Path；若省略: agent 构造不够直接
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+WorktreeIsolation: 创建测试 agent；若省略: 无法执行 enter_worktree
            output = agent._execute_tool(ToolCall(name="enter_worktree", arguments={"reason": "隔离风险", "goal": "测试路径边界", "worktree_path": "../outside"}))  # 新增代码+WorktreeIsolation: 传入越界路径触发边界校验；若省略: 路径防护没有测试输入
            self.assertIn("enter_worktree 失败", output)  # 新增代码+WorktreeIsolation: 断言越界路径会被拒绝；若省略: 工具可能误报成功
            self.assertIn("工作区内", output)  # 新增代码+WorktreeIsolation: 断言错误说明路径边界；若省略: 模型难以修正 worktree_path
    def test_cron_create_list_delete_records_in_process_schedule(self) -> None:  # 新增代码+CronMonitor: 验证 Cron 最小版能登记、列出和删除进程内定时任务记录；若省略: 定时任务记录闭环没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CronMonitor: 创建临时工作区隔离 agent 状态；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+CronMonitor: 把临时目录转成 Path；若省略: agent 构造不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+CronMonitor: 创建测试 agent；若省略: 无法通过工具路由执行 cron 工具
            create_output = agent._execute_tool(ToolCall(name="cron_create", arguments={"name": "每日检查测试", "schedule": "daily 09:00", "prompt": "检查测试状态", "stop_condition": "用户要求停止"}))  # 新增代码+CronMonitor: 请求登记一个教学版定时任务；若省略: cron_create 成功路径没有测试输入
            self.assertIn("cron_create 成功", create_output)  # 新增代码+CronMonitor: 断言创建工具返回成功前缀；若省略: 未知工具或失败输出可能被后续断言误判
            self.assertIn("不执行真实定时任务", create_output)  # 新增代码+CronMonitor: 断言输出明确教学版边界；若省略: 模型可能误以为系统定时器已经启动
            cron_id = next(line.split("=", 1)[1] for line in create_output.splitlines() if line.startswith("cron_id="))  # 新增代码+CronMonitor: 从输出中提取 cron_id；若省略: 后续 list/delete 无法引用具体记录
            list_output = agent._execute_tool(ToolCall(name="cron_list", arguments={"state": "active", "max_results": 10}))  # 新增代码+CronMonitor: 请求列出 active 定时任务；若省略: cron_list 成功路径没有测试输入
            self.assertIn("cron_list 成功", list_output)  # 新增代码+CronMonitor: 断言列表工具返回成功前缀；若省略: 未知工具输出可能被后续断言误判
            self.assertIn(cron_id, list_output)  # 新增代码+CronMonitor: 断言刚创建的 cron_id 进入列表；若省略: 创建后不可见的回归不会被发现
            self.assertIn("schedule=daily 09:00", list_output)  # 新增代码+CronMonitor: 断言 schedule 进入列表；若省略: 用户无法审计触发说明
            refused_output = agent._execute_tool(ToolCall(name="cron_delete", arguments={"cron_id": cron_id}))  # 新增代码+CronMonitor: 不带确认尝试删除定时任务；若省略: 删除确认门槛没有测试输入
            self.assertIn("cron_delete 失败", refused_output)  # 新增代码+CronMonitor: 断言缺少确认时拒绝删除；若省略: 定时记录可能被静默删除
            self.assertIn("confirm_delete=true", refused_output)  # 新增代码+CronMonitor: 断言错误提示明确确认参数；若省略: 模型难以修正删除调用
            delete_output = agent._execute_tool(ToolCall(name="cron_delete", arguments={"cron_id": cron_id, "confirm_delete": True}))  # 新增代码+CronMonitor: 带确认删除定时任务记录；若省略: cron_delete 成功路径没有测试输入
            self.assertIn("cron_delete 成功", delete_output)  # 新增代码+CronMonitor: 断言删除工具返回成功前缀；若省略: 删除失败可能被忽略
            empty_output = agent._execute_tool(ToolCall(name="cron_list", arguments={"state": "active", "max_results": 10}))  # 新增代码+CronMonitor: 删除后再次列出 active 记录；若省略: 无法证明记录已被移除
            self.assertNotIn(cron_id, empty_output)  # 新增代码+CronMonitor: 断言删除后的列表不再包含该 id；若省略: 删除可能只返回成功但记录仍存在
    def test_monitor_create_record_result_list_delete_records(self) -> None:  # 新增代码+CronMonitor: 验证 Monitor 最小版能登记、记录结果、列出和删除监控记录；若省略: 监控记录闭环没有回归保护
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CronMonitor: 创建临时工作区隔离 monitor 状态；若省略: 测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+CronMonitor: 把临时目录转成 Path；若省略: agent 构造不够清晰
            agent = LearningAgent(model=ToolCallingFakeModel([ModelMessage(text="不会调用模型。")]), workspace=workspace, ask_permission=lambda action: True)  # 新增代码+CronMonitor: 创建测试 agent；若省略: 无法执行 monitor 工具
            create_output = agent._execute_tool(ToolCall(name="monitor", arguments={"action": "create", "name": "测试监控", "target": "unit tests", "condition": "失败时提醒复查", "check_interval": "manual", "stop_condition": "测试恢复通过"}))  # 新增代码+CronMonitor: 请求登记教学版监控记录；若省略: monitor create 成功路径没有测试输入
            self.assertIn("monitor 成功", create_output)  # 新增代码+CronMonitor: 断言 monitor 创建返回成功前缀；若省略: 未知工具或失败输出可能被误判
            self.assertIn("action=create", create_output)  # 新增代码+CronMonitor: 断言输出标明执行的是创建动作；若省略: 多动作工具结果不易审计
            self.assertIn("不启动真实监控", create_output)  # 新增代码+CronMonitor: 断言输出明确不会启动常驻观察器；若省略: 模型可能误以为监控已经自动运行
            monitor_id = next(line.split("=", 1)[1] for line in create_output.splitlines() if line.startswith("monitor_id="))  # 新增代码+CronMonitor: 从输出中提取 monitor_id；若省略: 后续记录结果和删除无法引用目标
            record_output = agent._execute_tool(ToolCall(name="monitor", arguments={"action": "record_result", "monitor_id": monitor_id, "result": "发现一次失败", "result_status": "triggered"}))  # 新增代码+CronMonitor: 给监控记录补最近一次观察结果；若省略: monitor 无法保存检查证据
            self.assertIn("action=record_result", record_output)  # 新增代码+CronMonitor: 断言结果记录动作成功执行；若省略: 记录结果可能没有进入工具输出
            self.assertIn("last_status=triggered", record_output)  # 新增代码+CronMonitor: 断言最近状态被保存为 triggered；若省略: 用户无法快速判断监控是否命中条件
            list_output = agent._execute_tool(ToolCall(name="monitor", arguments={"action": "list", "state": "active", "max_results": 10}))  # 新增代码+CronMonitor: 请求列出 active 监控记录；若省略: monitor list 成功路径没有测试输入
            self.assertIn(monitor_id, list_output)  # 新增代码+CronMonitor: 断言刚创建的 monitor_id 进入列表；若省略: 创建后不可见的回归不会被发现
            self.assertIn("last_status=triggered", list_output)  # 新增代码+CronMonitor: 断言最近观察状态进入列表；若省略: 列表无法用于快速审计命中情况
            refused_output = agent._execute_tool(ToolCall(name="monitor", arguments={"action": "delete", "monitor_id": monitor_id}))  # 新增代码+CronMonitor: 不带确认尝试删除监控记录；若省略: monitor 删除确认门槛没有测试输入
            self.assertIn("monitor 失败", refused_output)  # 新增代码+CronMonitor: 断言缺少确认时拒绝删除；若省略: 监控记录可能被静默删除
            self.assertIn("confirm_delete=true", refused_output)  # 新增代码+CronMonitor: 断言错误提示明确确认参数；若省略: 模型难以修正删除调用
            delete_output = agent._execute_tool(ToolCall(name="monitor", arguments={"action": "delete", "monitor_id": monitor_id, "confirm_delete": True}))  # 新增代码+CronMonitor: 带确认删除监控记录；若省略: monitor delete 成功路径没有测试输入
            self.assertIn("action=delete", delete_output)  # 新增代码+CronMonitor: 断言删除动作成功返回；若省略: 删除失败可能被忽略
            empty_output = agent._execute_tool(ToolCall(name="monitor", arguments={"action": "list", "state": "active", "max_results": 10}))  # 新增代码+CronMonitor: 删除后再次列出 active 监控记录；若省略: 无法证明记录已被移除
            self.assertNotIn(monitor_id, empty_output)  # 新增代码+CronMonitor: 断言删除后的列表不再包含该 id；若省略: 删除可能只返回成功但记录仍存在
    def test_claudecode_parity_checklist_records_phase_7_status(self) -> None:  # 新增代码+ParityPhase7: 验证 Phase 7 清单记录完整追平状态和边界；若没有这行代码，文档可能再次停留在旧阶段
        repo_root = PROJECT_ROOT  # 新增代码+ParityPhase7: 从测试文件定位项目根目录；若没有这行代码，测试无法稳定找到 docs 目录
        checklist_file = repo_root / "docs" / "superpowers" / "specs" / "claudecode_parity_checklist.md"  # 新增代码+ParityPhase7: 定位 Phase 7 parity 清单；若没有这行代码，测试可能读错文档
        checklist_text = checklist_file.read_text(encoding="utf-8")  # 新增代码+ParityPhase7: 用 UTF-8 读取中文清单；若没有这行代码，中文关键词断言可能受系统编码影响
        expected_terms = ("Phase 7", "PASS", "Tool Catalog", "Tool Pool", "Tool Policy", "Real Chrome workflow", "Observation", "私有产品能力")  # 新增代码+ParityPhase7: 集中列出清单必须说明的核心结构和边界；若没有这行代码，缺少任一关键项都可能漏过
        for expected_term in expected_terms:  # 新增代码+ParityPhase7: 逐个检查关键术语；若没有这行代码，只能写重复断言且定位失败更慢
            with self.subTest(expected_term=expected_term):  # 新增代码+ParityPhase7: 给每个关键词独立失败上下文；若没有这行代码，缺词时不容易知道具体缺哪一个
                self.assertIn(expected_term, checklist_text)  # 新增代码+ParityPhase7: 断言 parity 清单包含该关键词；若没有这行代码，Phase 7 文档缺口不会被测试发现
    def test_run_retries_final_answer_when_required_markdown_headings_are_missing(self) -> None:  # 新增代码+最终答案完整性: 验证最终回答漏掉用户要求标题时会自动重写一次；若没有这行代码，天气攻略测试会只答天气不答攻略
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+最终答案完整性: 创建临时工作区隔离 memory/debug 文件；若没有这行代码，测试可能污染真实项目目录
            workspace = Path(raw_dir)  # 新增代码+最终答案完整性: 把临时目录转成 Path 传给 agent；若没有这行代码，构造 LearningAgent 路径不清楚
            model = ToolCallingFakeModel([  # 新增代码+最终答案完整性: 构造两轮假模型，第一轮漏标题，第二轮按要求重写；若没有这行代码，无法稳定复现和验证重试机制
                ModelMessage(text="## 天气概况\n晴朗，适合出行。"),  # 新增代码+最终答案完整性: 第一轮故意缺少用户要求的攻略标题；若没有这行代码，红灯无法覆盖失败场景
                ModelMessage(text="## 天气来源\nOpen-Meteo\n## 北京一日旅游攻略\n上午故宫，下午颐和园。"),  # 新增代码+最终答案完整性: 第二轮返回完整标题；若没有这行代码，测试无法确认重试结果被返回
            ])  # 新增代码+最终答案完整性: 假模型响应列表结束；若没有这行代码，Python 调用语法不完整
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+最终答案完整性: 创建关闭调试落盘的测试 agent；若没有这行代码，无法执行 run 主循环
            answer = agent.run("最终回答必须使用下面 2 个 Markdown 小标题：\n## 天气来源\n## 北京一日旅游攻略", max_turns=3)  # 新增代码+最终答案完整性: 触发用户指定标题的直接回答场景；若没有这行代码，被测重试逻辑不会运行
            self.assertIn("## 天气来源", answer)  # 新增代码+最终答案完整性: 断言重试后的答案包含第一个必需标题；若没有这行代码，仍可能返回第一轮不完整答案
            self.assertIn("## 北京一日旅游攻略", answer)  # 新增代码+最终答案完整性: 断言重试后的答案包含攻略标题；若没有这行代码，旅游攻略缺失不会被发现


if __name__ == "__main__":  # Stage14: allow running this test module directly.
    unittest.main()  # Stage14: start unittest when executed as a script.


