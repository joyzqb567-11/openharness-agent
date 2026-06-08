import unittest  # 新增代码+Phase71GenericInputActions: 导入 unittest 承载 Phase71 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase71GenericInputActions: 导入 Path 检查真实终端验收场景文件；如果没有这行代码，场景缺失不会被单测发现。

from learning_agent.computer_use.generic_input_actions import PHASE71_ACTIONS_EXPANDED, PHASE71_GENERIC_INPUT_ACTIONS_MARKER, PHASE71_GENERIC_INPUT_ACTIONS_OK_TOKEN, Phase71RecordingInputSender, WindowsGenericInputActionRuntime, build_drag_path, build_hotkey_events, build_menu_sequence, build_scroll_events, phase71_cli_line, run_phase71_generic_input_actions_contract  # 新增代码+Phase71GenericInputActions: 导入 Phase71 预期公开 API；如果没有这行代码，红灯会证明生产模块尚未实现。


class WindowsComputerUseGenericInputActionsPhase71Tests(unittest.TestCase):  # 新增代码+Phase71GenericInputActions: 类段开始，集中验证热键、菜单、滚轮和拖拽事件构建；如果没有这个类，Phase71 没有自动化验收边界。
    def _window(self) -> dict[str, object]:  # 新增代码+Phase71GenericInputActions: 函数段开始，提供安全的记录型窗口引用；如果没有这段函数，每个测试都要重复构造窗口上下文。
        return {"app_id": "phase58_safe_app", "process_name": "phase58_safe_app", "window_id": "hwnd:7101", "hwnd": 7101, "title_preview": "LearningAgent-Phase71-GenericInputActions", "safe_to_target": True}  # 新增代码+Phase71GenericInputActions: 返回满足后续安全链的窗口；如果没有这行代码，动作报告缺少目标窗口证据。
    # 新增代码+Phase71GenericInputActions: 函数段结束，_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口样本范围。

    def test_phase71_contract_reports_required_generic_input_capabilities(self) -> None:  # 新增代码+Phase71GenericInputActions: 函数段开始，验证 Phase71 合同报告覆盖蓝图要求；如果没有这个测试，CLI 可能漏掉关键能力 token。
        report = run_phase71_generic_input_actions_contract()  # 新增代码+Phase71GenericInputActions: 运行合同自检；如果没有这行代码，断言没有结构化来源。
        self.assertTrue(report["hotkey_action"])  # 新增代码+Phase71GenericInputActions: 断言热键动作能力成立；如果没有这行代码，热键事件缺失可能漏过。
        self.assertTrue(report["menu_navigation"])  # 新增代码+Phase71GenericInputActions: 断言菜单导航能力成立；如果没有这行代码，菜单事件缺失可能漏过。
        self.assertTrue(report["scroll_action"])  # 新增代码+Phase71GenericInputActions: 断言滚轮动作能力成立；如果没有这行代码，滚动事件缺失可能漏过。
        self.assertTrue(report["drag_action"])  # 新增代码+Phase71GenericInputActions: 断言拖拽动作能力成立；如果没有这行代码，拖拽事件缺失可能漏过。
        self.assertTrue(report["continuous_mouse_path"])  # 新增代码+Phase71GenericInputActions: 断言拖拽包含连续鼠标路径；如果没有这行代码，拖拽可能退化成危险跳点。
        self.assertTrue(report["forbidden_system_hotkeys_blocked"])  # 新增代码+Phase71GenericInputActions: 断言系统级危险热键被阻断；如果没有这行代码，Win+R 等组合可能漏过。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase71GenericInputActions: 断言本阶段不新增真实动作面；如果没有这行代码，安全边界可能被误放宽。
        self.assertTrue(report["passed"])  # 新增代码+Phase71GenericInputActions: 断言合同整体通过；如果没有这行代码，单项通过但总体失败会被忽略。
    # 新增代码+Phase71GenericInputActions: 函数段结束，test_phase71_contract_reports_required_generic_input_capabilities 到此结束；如果没有这个边界说明，初学者不容易看出合同能力测试范围。

    def test_hotkey_events_are_ordered_and_forbidden_system_hotkeys_are_zero_event_refused(self) -> None:  # 新增代码+Phase71GenericInputActions: 函数段开始，验证热键事件顺序和危险热键零事件拒绝；如果没有这个测试，系统热键可能误触发真实桌面。
        events = build_hotkey_events(["Ctrl", "S"])  # 新增代码+Phase71GenericInputActions: 构造常见保存热键事件；如果没有这行代码，热键顺序没有样本。
        sender = Phase71RecordingInputSender()  # 新增代码+Phase71GenericInputActions: 创建记录型 sender；如果没有这行代码，无法证明事件只是记录不触碰系统。
        runtime = WindowsGenericInputActionRuntime(sender=sender)  # 新增代码+Phase71GenericInputActions: 创建被测运行时；如果没有这行代码，热键拒绝路径没有执行对象。
        blocked = runtime.send_hotkey(self._window(), ["ctrl", "alt", "delete"])  # 新增代码+Phase71GenericInputActions: 尝试危险系统热键；如果没有这行代码，禁止组合没有样本。
        self.assertEqual([event["type"] for event in events], ["key_down", "key_down", "key_up", "key_up"])  # 新增代码+Phase71GenericInputActions: 断言先按修饰键再按主键再反向抬起；如果没有这行代码，事件顺序可能错误。
        self.assertEqual([event["key"] for event in events], ["ctrl", "s", "s", "ctrl"])  # 新增代码+Phase71GenericInputActions: 断言键名被规范为小写；如果没有这行代码，大小写漂移会影响后端。
        self.assertFalse(blocked["ok"])  # 新增代码+Phase71GenericInputActions: 断言危险热键被拒绝；如果没有这行代码，系统级组合可能误报成功。
        self.assertTrue(blocked["forbidden_system_hotkeys_blocked"])  # 新增代码+Phase71GenericInputActions: 断言拒绝原因是系统热键门禁；如果没有这行代码，用户不知道为什么不执行。
        self.assertEqual(blocked["input_event_count"], 0)  # 新增代码+Phase71GenericInputActions: 断言拒绝路径 0 事件；如果没有这行代码，拒绝仍可能产生副作用。
        self.assertEqual(sender.events, [])  # 新增代码+Phase71GenericInputActions: 直接检查记录 sender 为空；如果没有这行代码，结果字段可能撒谎。
    # 新增代码+Phase71GenericInputActions: 函数段结束，test_hotkey_events_are_ordered_and_forbidden_system_hotkeys_are_zero_event_refused 到此结束；如果没有这个边界说明，初学者不容易看出热键测试范围。

    def test_menu_scroll_and_drag_event_shapes_are_recorded_without_real_dispatch(self) -> None:  # 新增代码+Phase71GenericInputActions: 函数段开始，验证菜单、滚轮和拖拽事件形状并只进入记录 sender；如果没有这个测试，事件构建层可能绕过 Phase72。
        sender = Phase71RecordingInputSender()  # 新增代码+Phase71GenericInputActions: 创建记录型 sender；如果没有这行代码，无法检查事件形状。
        runtime = WindowsGenericInputActionRuntime(sender=sender)  # 新增代码+Phase71GenericInputActions: 创建被测运行时；如果没有这行代码，测试没有执行对象。
        menu_result = runtime.navigate_menu(self._window(), ["File", "Save As"])  # 新增代码+Phase71GenericInputActions: 执行菜单路径记录；如果没有这行代码，菜单导航没有正例。
        scroll_result = runtime.scroll_at(self._window(), 320, 240, -480)  # 新增代码+Phase71GenericInputActions: 执行滚轮事件记录；如果没有这行代码，滚动没有正例。
        drag_result = runtime.drag_path(self._window(), [{"x": 10, "y": 20}, {"x": 30, "y": 40}, {"x": 60, "y": 70}])  # 新增代码+Phase71GenericInputActions: 执行连续拖拽路径记录；如果没有这行代码，拖拽没有正例。
        self.assertTrue(menu_result["ok"])  # 新增代码+Phase71GenericInputActions: 断言菜单导航记录成功；如果没有这行代码，失败结果可能被误忽略。
        self.assertTrue(scroll_result["ok"])  # 新增代码+Phase71GenericInputActions: 断言滚轮记录成功；如果没有这行代码，失败结果可能被误忽略。
        self.assertTrue(drag_result["ok"])  # 新增代码+Phase71GenericInputActions: 断言拖拽记录成功；如果没有这行代码，失败结果可能被误忽略。
        self.assertTrue(drag_result["continuous_mouse_path"])  # 新增代码+Phase71GenericInputActions: 断言拖拽保持连续路径；如果没有这行代码，画图类动作会变成跳跃鼠标。
        self.assertIn("menu_open", [event["type"] for event in sender.events])  # 新增代码+Phase71GenericInputActions: 断言菜单打开事件已记录；如果没有这行代码，菜单路径可能只是文案。
        self.assertIn("mouse_wheel", [event["type"] for event in sender.events])  # 新增代码+Phase71GenericInputActions: 断言滚轮事件已记录；如果没有这行代码，滚动动作可能缺失。
        self.assertIn("mouse_down", [event["type"] for event in sender.events])  # 新增代码+Phase71GenericInputActions: 断言拖拽按下事件已记录；如果没有这行代码，拖拽动作不完整。
        self.assertIn("mouse_up", [event["type"] for event in sender.events])  # 新增代码+Phase71GenericInputActions: 断言拖拽抬起事件已记录；如果没有这行代码，拖拽动作不完整。
        self.assertTrue(all(event.get("real_dispatch_allowed") is False for event in sender.events))  # 新增代码+Phase71GenericInputActions: 断言所有事件都标记不允许真实派发；如果没有这行代码，Phase71 可能提前扩大真实动作面。
    # 新增代码+Phase71GenericInputActions: 函数段结束，test_menu_scroll_and_drag_event_shapes_are_recorded_without_real_dispatch 到此结束；如果没有这个边界说明，初学者不容易看出菜单滚动拖拽测试范围。

    def test_direct_builders_return_stable_shapes(self) -> None:  # 新增代码+Phase71GenericInputActions: 函数段开始，验证四个事件构建函数的稳定形状；如果没有这个测试，下游 Phase72/74 很难依赖事件协议。
        menu_events = build_menu_sequence(["Tools", "Brush"])  # 新增代码+Phase71GenericInputActions: 构造菜单路径事件；如果没有这行代码，菜单 builder 没有样本。
        scroll_events = build_scroll_events(10, 20, 120)  # 新增代码+Phase71GenericInputActions: 构造滚轮事件；如果没有这行代码，滚轮 builder 没有样本。
        drag_events = build_drag_path([{"x": 1, "y": 2}, {"x": 3, "y": 4}, {"x": 5, "y": 6}])  # 新增代码+Phase71GenericInputActions: 构造拖拽路径事件；如果没有这行代码，拖拽 builder 没有样本。
        self.assertEqual(menu_events[0]["type"], "menu_open")  # 新增代码+Phase71GenericInputActions: 断言菜单序列以打开菜单开始；如果没有这行代码，菜单导航入口可能不清楚。
        self.assertEqual(menu_events[-1]["type"], "menu_commit")  # 新增代码+Phase71GenericInputActions: 断言菜单序列以确认结束；如果没有这行代码，菜单导航可能不闭合。
        self.assertEqual(scroll_events, [{"type": "mouse_move", "x": 10, "y": 20, "real_dispatch_allowed": False}, {"type": "mouse_wheel", "x": 10, "y": 20, "delta": 120, "real_dispatch_allowed": False}])  # 新增代码+Phase71GenericInputActions: 断言滚轮事件先移动再滚动；如果没有这行代码，滚轮可能在错误位置发生。
        self.assertEqual(drag_events[0]["type"], "mouse_move")  # 新增代码+Phase71GenericInputActions: 断言拖拽先移动到起点；如果没有这行代码，拖拽会从未知鼠标位置开始。
        self.assertEqual(drag_events[1]["type"], "mouse_down")  # 新增代码+Phase71GenericInputActions: 断言拖拽第二步按下鼠标；如果没有这行代码，拖拽不会开始。
        self.assertEqual(drag_events[-1]["type"], "mouse_up")  # 新增代码+Phase71GenericInputActions: 断言拖拽最后抬起鼠标；如果没有这行代码，拖拽不会结束。
        self.assertGreaterEqual(len([event for event in drag_events if event["type"] == "mouse_move"]), 3)  # 新增代码+Phase71GenericInputActions: 断言拖拽保留所有路径点；如果没有这行代码，连续路径可能丢点。
    # 新增代码+Phase71GenericInputActions: 函数段结束，test_direct_builders_return_stable_shapes 到此结束；如果没有这个边界说明，初学者不容易看出 builder 形状测试范围。

    def test_phase71_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase71GenericInputActions: 函数段开始，验证 CLI 和真实可见终端验收场景 token 稳定；如果没有这个测试，controller 可能漏检 Phase71。
        report = run_phase71_generic_input_actions_contract()  # 新增代码+Phase71GenericInputActions: 运行合同报告；如果没有这行代码，CLI token 没有结构化来源。
        cli_line = phase71_cli_line(report)  # 新增代码+Phase71GenericInputActions: 生成稳定 CLI 行；如果没有这行代码，场景断言无法复用同一格式。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase71_generic_input_actions.json")  # 新增代码+Phase71GenericInputActions: 定位 Phase71 真实终端场景；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase71GenericInputActions: 读取场景文本；如果没有这行代码，token 漏配无法检测。
        expected_tokens = {PHASE71_GENERIC_INPUT_ACTIONS_MARKER, PHASE71_GENERIC_INPUT_ACTIONS_OK_TOKEN, "hotkey_action=true", "menu_navigation=true", "scroll_action=true", "drag_action=true", "continuous_mouse_path=true", "forbidden_system_hotkeys_blocked=true", "actions_expanded=false"}  # 新增代码+Phase71GenericInputActions: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        self.assertFalse(PHASE71_ACTIONS_EXPANDED)  # 新增代码+Phase71GenericInputActions: 断言底层动作面没有扩大；如果没有这行代码，安全承诺可能被误改。
        for token in expected_tokens:  # 新增代码+Phase71GenericInputActions: 遍历所有关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase71GenericInputActions: 断言 CLI 输出包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase71GenericInputActions: 断言真实终端场景包含 token；如果没有这行代码，验收脚本可能放过错误输出。
    # 新增代码+Phase71GenericInputActions: 函数段结束，test_phase71_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景测试范围。
# 新增代码+Phase71GenericInputActions: 类段结束，WindowsComputerUseGenericInputActionsPhase71Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase71GenericInputActions: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase71GenericInputActions: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
