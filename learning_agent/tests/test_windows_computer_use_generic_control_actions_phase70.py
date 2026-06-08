import unittest  # 新增代码+Phase70GenericControlActions: 导入 unittest 承载 Phase70 自动化门禁；如果没有这行代码，标准测试命令无法发现本阶段测试。
from pathlib import Path  # 新增代码+Phase70GenericControlActions: 导入 Path 检查真实终端验收场景文件；如果没有这行代码，场景缺失不会被单测发现。

from learning_agent.computer_use.generic_control_actions import PHASE70_ACTIONS_EXPANDED, PHASE70_GENERIC_CONTROL_ACTIONS_MARKER, PHASE70_GENERIC_CONTROL_ACTIONS_OK_TOKEN, Phase70RecordingHighLevelTool, WindowsGenericControlActionRuntime, phase70_cli_line, run_phase70_generic_control_actions_contract  # 新增代码+Phase70GenericControlActions: 导入 Phase70 预期公开 API；如果没有这行代码，红灯会证明生产模块尚未实现。


class WindowsComputerUseGenericControlActionsPhase70Tests(unittest.TestCase):  # 新增代码+Phase70GenericControlActions: 类段开始，集中验证通用点击、输入和视觉点兜底动作；如果没有这个类，Phase70 没有自动化验收边界。
    def _window(self) -> dict[str, object]:  # 新增代码+Phase70GenericControlActions: 函数段开始，提供安全的记录型窗口引用；如果没有这段函数，每个测试都要重复构造窗口上下文。
        return {"app_id": "phase58_safe_app", "process_name": "phase58_safe_app", "window_id": "hwnd:7001", "hwnd": 7001, "title_preview": "LearningAgent-Phase70-GenericControlActions", "safe_to_target": True}  # 新增代码+Phase70GenericControlActions: 返回满足高层工具安全链的窗口；如果没有这行代码，点击和输入没有目标窗口证据。
    # 新增代码+Phase70GenericControlActions: 函数段结束，_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口样本范围。

    def _observation(self) -> dict[str, object]:  # 新增代码+Phase70GenericControlActions: 函数段开始，提供融合观察里的 UIA 控件候选；如果没有这段函数，query 动作会依赖真实桌面。
        return {"fingerprint": "phase70-before", "flat_nodes": [{"node_id": "0", "name": "Phase70 root", "role": "Window", "automation_id": "Phase70Root", "class_name": "Window", "bounds": {"left": 80, "top": 90, "right": 680, "bottom": 430, "width": 600, "height": 340}, "enabled": True, "clickable": False, "editable": False}, {"node_id": "0.1", "name": "Message box", "role": "Edit", "automation_id": "Phase70MessageBox", "class_name": "TextBox", "bounds": {"left": 110, "top": 130, "right": 430, "bottom": 170, "width": 320, "height": 40}, "enabled": True, "clickable": True, "editable": True}, {"node_id": "0.2", "name": "Send message", "role": "Button", "automation_id": "Phase70SendButton", "class_name": "Button", "bounds": {"left": 450, "top": 130, "right": 580, "bottom": 170, "width": 130, "height": 40}, "enabled": True, "clickable": True, "editable": False}]}  # 新增代码+Phase70GenericControlActions: 返回既有按钮又有输入框的控件列表；如果没有这行代码，locator/click/type 无法被稳定验证。
    # 新增代码+Phase70GenericControlActions: 函数段结束，_observation 到此结束；如果没有这个边界说明，初学者不容易看出观察样本范围。

    def test_phase70_contract_reports_required_generic_action_capabilities(self) -> None:  # 新增代码+Phase70GenericControlActions: 函数段开始，验证 Phase70 合同报告覆盖蓝图要求；如果没有这个测试，CLI 可能漏掉关键能力 token。
        report = run_phase70_generic_control_actions_contract()  # 新增代码+Phase70GenericControlActions: 运行合同自检；如果没有这行代码，断言没有结构化来源。
        self.assertTrue(report["generic_click"])  # 新增代码+Phase70GenericControlActions: 断言通用点击能力成立；如果没有这行代码，点击链路缺失可能漏过。
        self.assertTrue(report["generic_type"])  # 新增代码+Phase70GenericControlActions: 断言通用输入能力成立；如果没有这行代码，输入链路缺失可能漏过。
        self.assertTrue(report["control_locator"])  # 新增代码+Phase70GenericControlActions: 断言复用控件定位能力；如果没有这行代码，query 可能只是硬编码坐标。
        self.assertTrue(report["visual_fallback"])  # 新增代码+Phase70GenericControlActions: 断言视觉点兜底能力成立；如果没有这行代码，画布类软件无法靠视觉点操作。
        self.assertTrue(report["before_after_evidence"])  # 新增代码+Phase70GenericControlActions: 断言动作带前后证据；如果没有这行代码，闭环执行器无法确认动作影响。
        self.assertTrue(report["zero_event_refusal"])  # 新增代码+Phase70GenericControlActions: 断言找不到目标时零事件拒绝；如果没有这行代码，错误目标可能被误点击。
        self.assertFalse(report["actions_expanded"])  # 新增代码+Phase70GenericControlActions: 断言本阶段不新增底层动作面；如果没有这行代码，安全边界可能被误放宽。
        self.assertTrue(report["passed"])  # 新增代码+Phase70GenericControlActions: 断言合同整体通过；如果没有这行代码，单项通过但总体失败会被忽略。
    # 新增代码+Phase70GenericControlActions: 函数段结束，test_phase70_contract_reports_required_generic_action_capabilities 到此结束；如果没有这个边界说明，初学者不容易看出合同能力测试范围。

    def test_query_click_and_type_route_through_locator_and_high_level_tool(self) -> None:  # 新增代码+Phase70GenericControlActions: 函数段开始，验证 query 点击和输入都走 Phase57/Phase62 风格桥接；如果没有这个测试，Phase70 可能绕过高层安全链。
        tool = Phase70RecordingHighLevelTool()  # 新增代码+Phase70GenericControlActions: 创建记录型高层工具；如果没有这行代码，测试无法观察动作是否被委托。
        runtime = WindowsGenericControlActionRuntime(high_level_tool=tool)  # 新增代码+Phase70GenericControlActions: 创建被测运行时并注入记录工具；如果没有这行代码，测试可能调用默认真实链路。
        click_result = runtime.click_by_query(self._window(), self._observation(), "Send")  # 新增代码+Phase70GenericControlActions: 按自然语言 query 点击按钮；如果没有这行代码，通用点击路径没有样本。
        type_result = runtime.type_by_query(self._window(), self._observation(), "Message", "hello phase70")  # 新增代码+Phase70GenericControlActions: 按自然语言 query 输入文本；如果没有这行代码，通用输入路径没有样本。
        self.assertTrue(click_result["ok"])  # 新增代码+Phase70GenericControlActions: 断言点击成功；如果没有这行代码，失败结果可能继续被当成功使用。
        self.assertTrue(type_result["ok"])  # 新增代码+Phase70GenericControlActions: 断言输入成功；如果没有这行代码，失败输入可能漏过。
        self.assertTrue(click_result["used_control_locator"])  # 新增代码+Phase70GenericControlActions: 断言点击先通过控件定位；如果没有这行代码，点击可能只靠坐标猜测。
        self.assertTrue(type_result["used_control_locator"])  # 新增代码+Phase70GenericControlActions: 断言输入先通过控件定位；如果没有这行代码，输入可能落到错误控件。
        self.assertTrue(click_result["used_high_level_tool"])  # 新增代码+Phase70GenericControlActions: 断言点击委托高层工具；如果没有这行代码，Phase62 安全链可能被绕过。
        self.assertTrue(type_result["used_high_level_tool"])  # 新增代码+Phase70GenericControlActions: 断言输入委托高层工具；如果没有这行代码，授权/锁/急停可能不可用。
        self.assertNotEqual(click_result["before_fingerprint"], click_result["after_fingerprint"])  # 新增代码+Phase70GenericControlActions: 断言点击有前后证据变化；如果没有这行代码，闭环验证缺少状态差异。
        self.assertFalse(type_result["text_summary"]["raw_text_included"])  # 新增代码+Phase70GenericControlActions: 断言输入报告不暴露原始文本；如果没有这行代码，敏感输入可能进入日志。
        self.assertEqual([event["operation"] for event in tool.events], ["click_control", "type_into_control"])  # 新增代码+Phase70GenericControlActions: 断言动作按高层工具名记录；如果没有这行代码，委托链路可能是假字段。
    # 新增代码+Phase70GenericControlActions: 函数段结束，test_query_click_and_type_route_through_locator_and_high_level_tool 到此结束；如果没有这个边界说明，初学者不容易看出 query 动作测试范围。

    def test_visual_click_uses_point_fallback_without_locator(self) -> None:  # 新增代码+Phase70GenericControlActions: 函数段开始，验证无控件目标时可用视觉点兜底；如果没有这个测试，画图画布等场景无法被 Phase70 表达。
        tool = Phase70RecordingHighLevelTool()  # 新增代码+Phase70GenericControlActions: 创建记录型高层工具；如果没有这行代码，视觉兜底无法证明被委托。
        runtime = WindowsGenericControlActionRuntime(high_level_tool=tool)  # 新增代码+Phase70GenericControlActions: 创建被测运行时；如果没有这行代码，测试没有执行对象。
        result = runtime.click_by_visual_point(self._window(), {"x": 260, "y": 220}, "canvas center")  # 新增代码+Phase70GenericControlActions: 用视觉点执行点击；如果没有这行代码，视觉兜底没有动作样本。
        self.assertTrue(result["ok"])  # 新增代码+Phase70GenericControlActions: 断言视觉点击成功；如果没有这行代码，失败结果可能漏过。
        self.assertTrue(result["visual_fallback"])  # 新增代码+Phase70GenericControlActions: 断言结果明确来自视觉兜底；如果没有这行代码，调用方无法区分 UIA 和视觉路径。
        self.assertFalse(result["used_control_locator"])  # 新增代码+Phase70GenericControlActions: 断言视觉点不冒充控件定位；如果没有这行代码，审计会误以为找到了 UIA 控件。
        self.assertEqual(tool.events[0]["target"]["point"], {"x": 260, "y": 220})  # 新增代码+Phase70GenericControlActions: 断言高层工具收到视觉点；如果没有这行代码，坐标可能被丢失或改错。
        self.assertEqual(tool.events[0]["target"]["reason"], "canvas center")  # 新增代码+Phase70GenericControlActions: 断言视觉点理由被保留；如果没有这行代码，后续复盘不知道为什么点击这里。
    # 新增代码+Phase70GenericControlActions: 函数段结束，test_visual_click_uses_point_fallback_without_locator 到此结束；如果没有这个边界说明，初学者不容易看出视觉兜底测试范围。

    def test_missing_query_refuses_with_zero_events(self) -> None:  # 新增代码+Phase70GenericControlActions: 函数段开始，验证找不到目标时不发送任何动作；如果没有这个测试，误识别目标可能导致真实桌面副作用。
        tool = Phase70RecordingHighLevelTool()  # 新增代码+Phase70GenericControlActions: 创建记录型高层工具；如果没有这行代码，无法统计拒绝路径是否零事件。
        runtime = WindowsGenericControlActionRuntime(high_level_tool=tool)  # 新增代码+Phase70GenericControlActions: 创建被测运行时；如果没有这行代码，拒绝路径没有执行对象。
        result = runtime.click_by_query(self._window(), self._observation(), "DoesNotExist")  # 新增代码+Phase70GenericControlActions: 查询不存在控件；如果没有这行代码，零事件拒绝没有样本。
        self.assertFalse(result["ok"])  # 新增代码+Phase70GenericControlActions: 断言动作失败；如果没有这行代码，找不到目标也可能被误报成功。
        self.assertTrue(result["refused"])  # 新增代码+Phase70GenericControlActions: 断言结果明确拒绝；如果没有这行代码，调用方无法区分失败和未执行。
        self.assertTrue(result["zero_event_refusal"])  # 新增代码+Phase70GenericControlActions: 断言拒绝路径是零事件；如果没有这行代码，拒绝仍可能产生副作用。
        self.assertEqual(result["high_level_event_count"], 0)  # 新增代码+Phase70GenericControlActions: 断言没有委托高层动作；如果没有这行代码，找不到目标后仍可能执行默认点击。
        self.assertEqual(tool.events, [])  # 新增代码+Phase70GenericControlActions: 直接检查记录工具为空；如果没有这行代码，结果字段可能撒谎。
    # 新增代码+Phase70GenericControlActions: 函数段结束，test_missing_query_refuses_with_zero_events 到此结束；如果没有这个边界说明，初学者不容易看出零事件拒绝测试范围。

    def test_phase70_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase70GenericControlActions: 函数段开始，验证 CLI 和真实可见终端验收场景 token 稳定；如果没有这个测试，controller 可能漏检 Phase70。
        report = run_phase70_generic_control_actions_contract()  # 新增代码+Phase70GenericControlActions: 运行合同报告；如果没有这行代码，CLI token 没有结构化来源。
        cli_line = phase70_cli_line(report)  # 新增代码+Phase70GenericControlActions: 生成稳定 CLI 行；如果没有这行代码，场景断言无法复用同一格式。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase70_generic_control_actions.json")  # 新增代码+Phase70GenericControlActions: 定位 Phase70 真实终端场景；如果没有这行代码，场景缺失不会暴露。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase70GenericControlActions: 读取场景文本；如果没有这行代码，token 漏配无法检测。
        expected_tokens = {PHASE70_GENERIC_CONTROL_ACTIONS_MARKER, PHASE70_GENERIC_CONTROL_ACTIONS_OK_TOKEN, "generic_click=true", "generic_type=true", "control_locator=true", "visual_fallback=true", "before_after_evidence=true", "zero_event_refusal=true", "actions_expanded=false"}  # 新增代码+Phase70GenericControlActions: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准容易漂移。
        self.assertFalse(PHASE70_ACTIONS_EXPANDED)  # 新增代码+Phase70GenericControlActions: 断言底层动作面没有扩大；如果没有这行代码，安全承诺可能被误改。
        for token in expected_tokens:  # 新增代码+Phase70GenericControlActions: 遍历所有关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase70GenericControlActions: 断言 CLI 输出包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase70GenericControlActions: 断言真实终端场景包含 token；如果没有这行代码，验收脚本可能放过错误输出。
    # 新增代码+Phase70GenericControlActions: 函数段结束，test_phase70_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景测试范围。
# 新增代码+Phase70GenericControlActions: 类段结束，WindowsComputerUseGenericControlActionsPhase70Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase70GenericControlActions: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase70GenericControlActions: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行测试。
