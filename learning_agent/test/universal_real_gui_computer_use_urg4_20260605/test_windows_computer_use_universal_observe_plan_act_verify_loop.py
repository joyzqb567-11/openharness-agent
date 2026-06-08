import io  # 新增代码+URG4ObservePlanActVerify：导入内存文本缓冲区来捕获 CLI 输出；如果没有这行代码，测试无法确认真实终端会看到哪些固定 token。
import unittest  # 新增代码+URG4ObservePlanActVerify：导入 Python 标准测试框架；如果没有这行代码，本文件不会被 unittest 正常发现和执行。
from contextlib import redirect_stdout  # 新增代码+URG4ObservePlanActVerify：导入 stdout 重定向工具；如果没有这行代码，main 打印的验收行无法被自动断言。
from learning_agent.computer_use.universal_observe_plan_act_verify import PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MARKER, PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_OK_TOKEN, UniversalObservePlanActVerifyLoop, main, phase119_universal_loop_cli_line, run_phase119_universal_loop_contract  # 新增代码+URG4ObservePlanActVerify：导入预期的 URG-4 公开 API；如果没有这行代码，红灯无法证明当前项目缺少通用闭环模块。


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
