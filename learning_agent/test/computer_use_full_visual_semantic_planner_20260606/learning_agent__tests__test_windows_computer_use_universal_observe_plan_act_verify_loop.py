import io  # 新增代码+URG4ObservePlanActVerify：导入内存文本缓冲区来捕获 CLI 输出；如果没有这行代码，测试无法确认真实终端会看到哪些固定 token。
import unittest  # 新增代码+URG4ObservePlanActVerify：导入 Python 标准测试框架；如果没有这行代码，本文件不会被 unittest 正常发现和执行。
from contextlib import redirect_stdout  # 新增代码+URG4ObservePlanActVerify：导入 stdout 重定向工具；如果没有这行代码，main 打印的验收行无法被自动断言。
from learning_agent.computer_use.universal_observe_plan_act_verify import PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MARKER, PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_OK_TOKEN, PHASE120_VISUAL_TASK_PLANNER_MODEL, Phase120VisualTaskPlanner, UniversalObservePlanActVerifyLoop, main, phase119_universal_loop_cli_line, run_phase119_universal_loop_contract  # 修改代码+VisualPlannerLoop：导入视觉任务规划器和模型名用于锁住 observe-plan-act 真接线；如果没有这一行，测试只能证明旧静态 actions 复制器存在。


class UniversalObservePlanActVerifyLoopTests(unittest.TestCase):  # 新增代码+URG4ObservePlanActVerify：测试类段开始，集中验证 URG-4 observe-plan-act-verify 通用闭环；如果没有这个类，闭环行为不会有自动化护栏。
    def test_contract_reports_universal_loop_for_representative_samples(self) -> None:  # 新增代码+URG4ObservePlanActVerify：函数段开始，验证合同报告覆盖 Notepad、Calculator、Paint 三个代表样本；如果没有这段测试，闭环可能只在单一任务上假通过。
        report = run_phase119_universal_loop_contract()  # 新增代码+URG4ObservePlanActVerify：运行安全记录型 URG-4 合同；如果没有这行代码，断言没有结构化事实来源。
        cli_line = phase119_universal_loop_cli_line(report)  # 新增代码+URG4ObservePlanActVerify：生成真实终端验收使用的固定 token 行；如果没有这行代码，场景 JSON 和测试会各自拼接导致漂移。
        self.assertTrue(report["passed"])  # 新增代码+URG4ObservePlanActVerify：断言总体合同通过；如果没有这行代码，局部字段成功可能掩盖整体失败。
        self.assertTrue(report["observe_plan_act_verify_loop"])  # 新增代码+URG4ObservePlanActVerify：断言闭环能力已存在；如果没有这行代码，模块可能只执行动作而没有闭环语义。
        self.assertTrue(report["before_after_observation_per_action"])  # 新增代码+URG4ObservePlanActVerify：断言每个动作都有前后观察；如果没有这行代码，动作后验证可能缺少证据。
        self.assertTrue(report["verification_decides_next_step"])  # 新增代码+URG4ObservePlanActVerify：断言 verifier 会决定继续或停止；如果没有这行代码，planner 可能盲目执行固定动作列表。
        self.assertTrue(report["bounded_retry"])  # 新增代码+URG4ObservePlanActVerify：断言重试有上限；如果没有这行代码，失败任务可能无限循环。
        self.assertTrue(report["failure_exits_with_evidence_and_cleanup"])  # 新增代码+URG4ObservePlanActVerify：断言失败路径会带证据和清理结果退出；如果没有这行代码，失败时容易留下不清楚的半状态。
        self.assertTrue(report["same_loop_handles_representative_samples"])  # 新增代码+URG4ObservePlanActVerify：断言三个代表样本走同一个 loop；如果没有这行代码，代码可能退回每个应用一套控制器。
        self.assertFalse(report["per_app_controller_required"])  # 新增代码+URG4ObservePlanActVerify：断言不需要逐应用 controller；如果没有这行代码，用户反对的架构路线可能复发。
        self.assertFalse(report["hardcoded_app_whitelist_required"])  # 新增代码+URG4ObservePlanActVerify：断言不需要硬编码应用白名单；如果没有这行代码，通用性会缩水。
        self.assertTrue(report["target_identity_rechecked_before_each_action"])  # 新增代码+URG4ObservePlanActVerify：断言每次动作前复核目标身份；如果没有这行代码，窗口漂移风险会重新出现。
        self.assertTrue(report["target_drift_zero_events"])  # 新增代码+URG4ObservePlanActVerify：断言漂移路径是零底层事件；如果没有这行代码，拒绝可能只是口头拒绝。
        self.assertTrue(report["abort_zero_events"])  # 新增代码+URG4ObservePlanActVerify：断言 abort 路径是零底层事件；如果没有这行代码，stop 后残余动作可能复发。
        self.assertTrue(report["low_level_event_count_gt_zero"])  # 新增代码+URG4ObservePlanActVerify：断言正常路径确实到达低层记录 sender；如果没有这行代码，闭环可能只是观察和文字报告。
        self.assertFalse(report["real_dispatch_performed"])  # 新增代码+URG4ObservePlanActVerify：断言合同默认不触碰真实桌面；如果没有这行代码，单元测试可能意外移动鼠标键盘。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+URG4ObservePlanActVerify：断言本阶段合同没有真实桌面副作用；如果没有这行代码，安全边界不可见。
        self.assertIn(PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MARKER, cli_line)  # 新增代码+URG4ObservePlanActVerify：断言 CLI 行包含 ready marker；如果没有这行代码，真实终端验收没有稳定锚点。
        self.assertIn(PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_OK_TOKEN, cli_line)  # 新增代码+URG4ObservePlanActVerify：断言 CLI 行包含 OK token；如果没有这行代码，验收器无法区分成功输出。
    # 新增代码+URG4ObservePlanActVerify：函数段结束，test_contract_reports_universal_loop_for_representative_samples 到此结束；如果没有这个边界说明，初学者不容易看出合同测试范围。

    def test_loop_stops_on_failed_verification_after_bounded_retry(self) -> None:  # 新增代码+URG4ObservePlanActVerify：函数段开始，验证失败验证不会无限重试；如果没有这段测试，真实任务失败时可能卡住。
        loop = UniversalObservePlanActVerifyLoop(max_retries=1)  # 新增代码+URG4ObservePlanActVerify：创建只允许一次重试的 loop；如果没有这行代码，测试无法稳定验证重试上限。
        result = loop.run_task({"target": "notepad", "goal": "forced failure", "actions": [{"type": "click_point", "x": 1, "y": 1}], "force_verification_failure": True})  # 新增代码+URG4ObservePlanActVerify：运行强制失败任务；如果没有这行代码，失败退出路径没有事实样本。
        self.assertFalse(result["ok"])  # 新增代码+URG4ObservePlanActVerify：断言任务最终失败；如果没有这行代码，失败任务可能被误报成功。
        self.assertEqual("verification_failed", result["decision"])  # 新增代码+URG4ObservePlanActVerify：断言失败原因来自验证；如果没有这行代码，失败原因可能被模糊处理。
        self.assertEqual(2, result["attempt_count"])  # 新增代码+URG4ObservePlanActVerify：断言首试加一次重试后停止；如果没有这行代码，bounded retry 不可验证。
        self.assertTrue(result["cleanup_completed"])  # 新增代码+URG4ObservePlanActVerify：断言失败后完成清理；如果没有这行代码，失败路径可能留下状态。
        self.assertGreaterEqual(result["evidence_count"], 2)  # 新增代码+URG4ObservePlanActVerify：断言失败仍有观察证据；如果没有这行代码，失败时无法复盘。
    # 新增代码+URG4ObservePlanActVerify：函数段结束，test_loop_stops_on_failed_verification_after_bounded_retry 到此结束；如果没有这个边界说明，初学者不容易看出失败路径测试范围。
    def test_visual_planner_generates_actions_from_observation_inside_loop(self) -> None:  # 新增代码+VisualPlannerLoop：函数段开始，验证自然语言视觉任务由 planner 在 observe 之后生成动作；如果没有这段测试，loop 可能继续只复制固定 actions。
        planner = Phase120VisualTaskPlanner()  # 新增代码+VisualPlannerLoop：创建视觉任务规划器；如果没有这一行，测试无法证明 planner 是可注入、可替换的独立部件。
        loop = UniversalObservePlanActVerifyLoop(planner=planner, max_retries=0)  # 新增代码+VisualPlannerLoop：把视觉规划器接入通用 observe-plan-act loop；如果没有这一行，测试不会覆盖真实接线位置。
        task = {"target": "mspaint", "goal": "natural_language_desktop_task", "visual_planning_requested": True, "prompt_signature": "cat-visual-plan", "prompt_length": 17}  # 新增代码+VisualPlannerLoop：构造不带静态 actions 的自然语言视觉任务；如果没有这一行，测试仍可能被旧 actions 列表假通过。
        result = loop.run_task(task)  # 新增代码+VisualPlannerLoop：运行通用闭环；如果没有这一行，planner 是否真正被 loop 调用没有事实来源。
        actions = [step["action"] for step in result["attempts"][0]["steps"]]  # 新增代码+VisualPlannerLoop：读取本轮实际执行动作；如果没有这一行，断言只能看顶层布尔字段而看不到动作来源。
        self.assertTrue(result["ok"])  # 新增代码+VisualPlannerLoop：断言视觉规划任务在记录型安全 loop 中能完成；如果没有这一行，空规划也可能被忽略。
        self.assertTrue(result["visual_planner_connected"])  # 新增代码+VisualPlannerLoop：断言 loop 报告视觉规划器已接线；如果没有这一行，后续成熟度可能无法区分静态 planner 和视觉 planner。
        self.assertTrue(result["visual_planner_used"])  # 新增代码+VisualPlannerLoop：断言本次任务实际使用视觉规划器；如果没有这一行，planner 只存在于构造参数也会误通过。
        self.assertEqual(result["planner_model"], PHASE120_VISUAL_TASK_PLANNER_MODEL)  # 新增代码+VisualPlannerLoop：断言报告暴露稳定 planner 模型名；如果没有这一行，验收无法追踪当前规划器版本。
        self.assertGreaterEqual(len(actions), 3)  # 新增代码+VisualPlannerLoop：断言至少包含聚焦、绘制和观察等动作；如果没有这一行，空动作或单动作会被误认为可用。
        self.assertTrue(any(action.get("visual_planner_action") for action in actions))  # 新增代码+VisualPlannerLoop：断言实际动作带视觉规划标记；如果没有这一行，固定旧 drag_path 仍可能混入并假通过。
        self.assertTrue(any(action.get("type") == "drag_path" for action in actions))  # 新增代码+VisualPlannerLoop：断言视觉规划最终能落到可执行拖拽动作；如果没有这一行，planner 可能只生成不可执行说明文字。
        self.assertFalse(any(action.get("points") == [{"x": 320, "y": 330}, {"x": 520, "y": 410}, {"x": 720, "y": 330}] for action in actions))  # 新增代码+VisualPlannerLoop：断言动作不是旧固定三点样本；如果没有这一行，根因可能原样复发。
    # 新增代码+VisualPlannerLoop：函数段结束，test_visual_planner_generates_actions_from_observation_inside_loop 到此结束；如果没有这个边界说明，初学者不容易看出视觉规划接线测试范围。
    def test_visual_planner_uses_real_rect_edges_and_avoids_paint_toolbar_area(self) -> None:  # 新增代码+VisualPlannerCanvas：函数段开始，验证真实 Paint 窗口只有 left/right/top/bottom 时 planner 仍把笔画放到画布区；如果没有这段测试，真实验收会继续只在左上角画短线。
        planner = Phase120VisualTaskPlanner()  # 新增代码+VisualPlannerCanvas：创建视觉任务 planner；如果没有这一行，断言没有规划主体。
        frame = {"target_window": {"app_id": "mspaintapp:pid:30228", "rect": {"left": -8, "top": -8, "right": 1928, "bottom": 1040}}}  # 新增代码+VisualPlannerCanvas：模拟真实 Paint observation 只带边界 rect；如果没有这一行，测试无法复现本轮真实截图暴露的问题。
        actions = planner.plan({"target": "mspaint", "goal": "natural_language_desktop_task", "visual_planning_requested": True, "prompt_signature": "paint-house"}, frame)  # 新增代码+VisualPlannerCanvas：生成真实 Paint 窗口下的视觉动作；如果没有这一行，坐标不会被实际计算。
        points = [point for action in actions if action.get("type") == "drag_path" for point in action.get("points", [])]  # 新增代码+VisualPlannerCanvas：收集所有拖拽点位；如果没有这一行，断言无法覆盖画布区域。
        self.assertGreater(min(point["x"] for point in points), 430)  # 新增代码+VisualPlannerCanvas：断言最左点避开 Paint 左侧工具和画布外边界；如果没有这一行，左上角短线问题会复发。
        self.assertGreater(min(point["y"] for point in points), 260)  # 新增代码+VisualPlannerCanvas：断言最上点避开 Paint 顶部功能区；如果没有这一行，大笔画仍会落到工具栏或画布外。
        self.assertGreater(max(point["x"] for point in points), 900)  # 新增代码+VisualPlannerCanvas：断言规划覆盖画布中央区域而不是只画小短线；如果没有这一行，默认 900 宽兜底会再次隐藏问题。
        self.assertGreater(max(point["y"] for point in points), 520)  # 新增代码+VisualPlannerCanvas：断言规划纵向覆盖画布中部；如果没有这一行，真实 Paint 仍可能只在左上角留下痕迹。
    # 新增代码+VisualPlannerCanvas：函数段结束，test_visual_planner_uses_real_rect_edges_and_avoids_paint_toolbar_area 到此结束；如果没有这个边界说明，初学者不容易看出真实画布坐标回归范围。
    def test_visual_planner_builds_house_primitives_from_semantic_intent(self) -> None:  # 新增代码+VisualSemanticPlanner：函数段开始，验证房子语义会变成屋顶、墙体、门窗等可解释 primitive；如果没有这段测试，planner 可能继续把任何 prompt 都画成通用脸。
        planner = Phase120VisualTaskPlanner()  # 新增代码+VisualSemanticPlanner：创建当前默认视觉 planner；如果没有这一行，测试无法覆盖生产 planner 的语义分支。
        frame = {"target_window": {"app_id": "mspaintapp:pid:30228", "rect": {"left": -8, "top": -8, "right": 1928, "bottom": 1040}}}  # 新增代码+VisualSemanticPlanner：提供真实 Paint 尺寸结构；如果没有这一行，语义 primitive 的画布坐标无法被检查。
        task = {"target": "mspaint", "goal": "natural_language_desktop_task", "visual_planning_requested": True, "visual_subject_hint": "house", "visual_intent": {"subject": "house"}, "prompt_signature": "paint-house"}  # 新增代码+VisualSemanticPlanner：构造不泄露原始 prompt 的房子语义任务；如果没有这一行，planner 无法知道用户想画房子。
        actions = planner.plan(task, frame)  # 新增代码+VisualSemanticPlanner：让 planner 把房子语义转成 DSL 动作；如果没有这一行，后续断言没有实际规划结果。
        semantic_roles = {str(action.get("semantic_role", "")) for action in actions}  # 新增代码+VisualSemanticPlanner：收集每个动作声明的语义角色；如果没有这一行，测试只能看坐标而看不出是否真按房子规划。
        self.assertIn("house_roof", semantic_roles)  # 新增代码+VisualSemanticPlanner：要求房子计划包含屋顶；如果没有这一行，通用脸轮廓也可能假装通过。
        self.assertIn("house_body", semantic_roles)  # 新增代码+VisualSemanticPlanner：要求房子计划包含墙体；如果没有这一行，只有屋顶三角形不能算房子。
        self.assertIn("house_door", semantic_roles)  # 新增代码+VisualSemanticPlanner：要求房子计划包含门；如果没有这一行，图像缺少可识别房屋细节也会通过。
        self.assertIn("house_window_left", semantic_roles)  # 新增代码+VisualSemanticPlanner：要求房子计划包含左窗；如果没有这一行，planner 可能仍停留在粗轮廓。
        self.assertIn("house_window_right", semantic_roles)  # 新增代码+VisualSemanticPlanner：要求房子计划包含右窗；如果没有这一行，左右结构不会被语义约束。
        self.assertNotIn("generic_face_outline", semantic_roles)  # 新增代码+VisualSemanticPlanner：禁止房子任务退回通用脸轮廓；如果没有这一行，当前真实失败会再次被测试漏掉。
    # 新增代码+VisualSemanticPlanner：函数段结束，test_visual_planner_builds_house_primitives_from_semantic_intent 到此结束；如果没有这个边界说明，初学者不容易看出房子语义测试范围。

    def test_main_prints_visible_terminal_tokens(self) -> None:  # 新增代码+URG4ObservePlanActVerify：函数段开始，验证命令行入口打印真实终端需要的 token；如果没有这段测试，可见终端场景可能找不到最终答案。
        buffer = io.StringIO()  # 新增代码+URG4ObservePlanActVerify：创建输出缓冲区；如果没有这行代码，main 的输出无法被测试读取。
        with redirect_stdout(buffer):  # 新增代码+URG4ObservePlanActVerify：捕获 main 的标准输出；如果没有这行代码，断言只能依赖人工查看。
            exit_code = main([])  # 新增代码+URG4ObservePlanActVerify：运行 URG-4 命令行入口；如果没有这行代码，真实终端入口没有自动化覆盖。
        output = buffer.getvalue()  # 新增代码+URG4ObservePlanActVerify：读取捕获到的输出文本；如果没有这行代码，后续断言没有检查对象。
        self.assertEqual(0, exit_code)  # 新增代码+URG4ObservePlanActVerify：断言命令行入口成功退出；如果没有这行代码，失败也可能被 token 文本掩盖。
        self.assertIn("observe_plan_act_verify_loop=true", output)  # 新增代码+URG4ObservePlanActVerify：断言输出闭环 token；如果没有这行代码，用户看不到 URG-4 核心事实。
        self.assertIn("before_after_observation_per_action=true", output)  # 新增代码+URG4ObservePlanActVerify：断言输出前后观察 token；如果没有这行代码，观察证据链不可见。
        self.assertIn("same_loop_handles_representative_samples=true", output)  # 新增代码+URG4ObservePlanActVerify：断言输出同一 loop 覆盖样本 token；如果没有这行代码，通用性不可见。
        self.assertIn("real_dispatch_performed=false", output)  # 新增代码+URG4ObservePlanActVerify：断言输出默认不真实派发；如果没有这行代码，安全边界不可见。
    # 新增代码+URG4ObservePlanActVerify：函数段结束，test_main_prints_visible_terminal_tokens 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 测试范围。
# 新增代码+URG4ObservePlanActVerify：测试类段结束，UniversalObservePlanActVerifyLoopTests 到此结束；如果没有这个边界说明，初学者不容易看出 URG-4 测试集合范围。


if __name__ == "__main__":  # 新增代码+URG4ObservePlanActVerify：文件入口段开始，允许直接运行本测试文件；如果没有这行代码，初学者需要记完整 unittest 命令。
    unittest.main()  # 新增代码+URG4ObservePlanActVerify：启动 unittest；如果没有这行代码，直接运行文件不会执行任何测试。
# 新增代码+URG4ObservePlanActVerify：文件入口段结束，本测试文件到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
