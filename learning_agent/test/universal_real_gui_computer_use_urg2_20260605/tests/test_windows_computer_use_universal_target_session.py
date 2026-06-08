import io  # 新增代码+URG2UniversalTargetSession：导入内存缓冲区捕获 CLI 输出；如果没有这一行，测试无法检查真实终端 token。
import unittest  # 新增代码+URG2UniversalTargetSession：导入标准测试框架；如果没有这一行，本文件不会被 unittest 发现。
from contextlib import redirect_stdout  # 新增代码+URG2UniversalTargetSession：导入 stdout 重定向工具；如果没有这一行，main 输出无法断言。
from typing import Any  # 新增代码+URG2UniversalTargetSession：导入 Any 描述动态候选和窗口字典；如果没有这一行，测试 provider 接口边界不清楚。

from learning_agent.computer_use.universal_target_session import PHASE117_UNIVERSAL_TARGET_SESSION_MARKER, PHASE117_UNIVERSAL_TARGET_SESSION_OK_TOKEN, UniversalTargetSessionRuntime, main, phase117_universal_target_session_cli_line, run_phase117_universal_target_session_contract  # 新增代码+URG2UniversalTargetSession：导入 URG-2 公开 API；如果没有这一行，红测无法证明模块缺失或 API 漂移。


def _sample_candidates(target: str) -> list[dict[str, Any]]:  # 新增代码+URG2UniversalTargetSession：函数段开始，生成代表性普通应用候选；如果没有这段函数，测试会依赖本机是否安装具体应用。
    return [{"display_name": target, "executable": f"{target}.exe", "source": "urg2_injected_start_menu", "installed_app_verified": True}]  # 新增代码+URG2UniversalTargetSession：返回通用发现候选；如果没有这一行，resolver 无法形成普通目标报告。
# 新增代码+URG2UniversalTargetSession：函数段结束，_sample_candidates 到此结束；如果没有这个边界说明，初学者不容易看出候选构造范围。


class UniversalTargetSessionTests(unittest.TestCase):  # 新增代码+URG2UniversalTargetSession：类段开始，集中验收 URG-2 目标 session 和身份防漂移；如果没有这个类，蓝图 URG-2 没有自动化护栏。
    def test_contract_reports_generic_target_session(self) -> None:  # 新增代码+URG2UniversalTargetSession：函数段开始，验收合同自检输出通用 session token；如果没有这段测试，模块可能只输出文案。
        report = run_phase117_universal_target_session_contract()  # 新增代码+URG2UniversalTargetSession：运行无真实桌面副作用合同；如果没有这一行，断言没有结构化事实来源。
        cli_line = phase117_universal_target_session_cli_line(report)  # 新增代码+URG2UniversalTargetSession：生成固定 CLI token 行；如果没有这一行，场景验收无法复用格式。
        self.assertTrue(report["passed"])  # 新增代码+URG2UniversalTargetSession：断言总合同通过；如果没有这一行，局部字段成功但整体失败会漏掉。
        self.assertTrue(report["universal_target_session_ready"])  # 新增代码+URG2UniversalTargetSession：断言通用 session 已建立；如果没有这一行，URG-2 可能仍停在孤立发现报告。
        self.assertTrue(report["generic_target_resolver_used"])  # 新增代码+URG2UniversalTargetSession：断言使用通用 resolver；如果没有这一行，系统可能退回逐应用白名单。
        self.assertTrue(report["representative_samples_session_ready"])  # 新增代码+URG2UniversalTargetSession：断言代表应用样本都走同一 session；如果没有这一行，单样本通过会掩盖通用性不足。
        self.assertFalse(report["per_app_controller_required"])  # 新增代码+URG2UniversalTargetSession：断言不需要每 app controller；如果没有这一行，用户指出的架构问题可能复发。
        self.assertFalse(report["hardcoded_app_whitelist_required"])  # 新增代码+URG2UniversalTargetSession：断言不需要硬编码白名单；如果没有这一行，本机成千上万应用无法通用。
        self.assertTrue(report["target_identity_bound"])  # 新增代码+URG2UniversalTargetSession：断言目标身份已绑定；如果没有这一行，后续动作前没有凭证。
        self.assertTrue(report["target_identity_rechecked_before_each_action"])  # 新增代码+URG2UniversalTargetSession：断言动作前会复核身份；如果没有这一行，窗口漂移后仍可能动作。
        self.assertTrue(report["target_drift_zero_events"])  # 新增代码+URG2UniversalTargetSession：断言漂移时零事件；如果没有这一行，漂移拒绝只是口号。
        self.assertTrue(report["agent_owned_or_user_authorized_window"])  # 新增代码+URG2UniversalTargetSession：断言目标必须自有或授权；如果没有这一行，用户已有窗口可能被误操作。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+URG2UniversalTargetSession：断言合同不触碰真实桌面；如果没有这一行，单测可能打开本机应用。
        self.assertEqual(0, report["low_level_event_count"])  # 新增代码+URG2UniversalTargetSession：断言底层事件为 0；如果没有这一行，session 阶段可能混入输入动作。
        self.assertIn(PHASE117_UNIVERSAL_TARGET_SESSION_MARKER, cli_line)  # 新增代码+URG2UniversalTargetSession：断言 CLI 行包含 ready marker；如果没有这一行，真实终端无法稳定匹配阶段。
        self.assertIn(PHASE117_UNIVERSAL_TARGET_SESSION_OK_TOKEN, cli_line)  # 新增代码+URG2UniversalTargetSession：断言 CLI 行包含 OK token；如果没有这一行，验收器无法区分成功输出。
    # 新增代码+URG2UniversalTargetSession：函数段结束，test_contract_reports_generic_target_session 到此结束；如果没有这个边界说明，初学者不容易看出合同测试范围。

    def test_same_runtime_builds_notepad_paint_and_calculator_sessions(self) -> None:  # 新增代码+URG2UniversalTargetSession：函数段开始，验收代表性普通应用共用同一 runtime；如果没有这段测试，代码可能暗中写 app 专用分支。
        runtime = UniversalTargetSessionRuntime()  # 新增代码+URG2UniversalTargetSession：创建通用目标 session runtime；如果没有这一行，测试无法证明 runtime 可复用。
        reports = [runtime.open_target_session(target, candidates=_sample_candidates(target)) for target in ["notepad", "mspaint", "calc"]]  # 新增代码+URG2UniversalTargetSession：用同一入口建立三个代表样本 session；如果没有这一行，通用性没有实际样本覆盖。
        self.assertEqual(3, len(reports))  # 新增代码+URG2UniversalTargetSession：断言三个样本都产生报告；如果没有这一行，漏掉某个样本不会被发现。
        for report in reports:  # 新增代码+URG2UniversalTargetSession：逐个检查 session 报告；如果没有这一行，只会检查列表存在。
            self.assertTrue(report["session_ready"])  # 新增代码+URG2UniversalTargetSession：断言当前样本 session 就绪；如果没有这一行，失败样本可能混在列表里。
            self.assertTrue(report["target_identity_bound"])  # 新增代码+URG2UniversalTargetSession：断言当前样本绑定目标身份；如果没有这一行，样本可能只有发现没有凭证。
            self.assertTrue(report["stable_verification"]["allowed"])  # 新增代码+URG2UniversalTargetSession：断言稳定窗口通过复核；如果没有这一行，正常路径可能不能动作。
            self.assertTrue(report["drift_verification"]["target_drift_blocks_action"])  # 新增代码+URG2UniversalTargetSession：断言漂移窗口被阻断；如果没有这一行，防漂移能力没有样本证明。
            self.assertFalse(report["per_app_controller_required"])  # 新增代码+URG2UniversalTargetSession：断言当前样本不需要专用 controller；如果没有这一行，样本可能变成逐应用补丁。
            self.assertEqual(0, report["low_level_event_count"])  # 新增代码+URG2UniversalTargetSession：断言 session 建立不发送输入事件；如果没有这一行，目标绑定阶段可能误动作。
    # 新增代码+URG2UniversalTargetSession：函数段结束，test_same_runtime_builds_notepad_paint_and_calculator_sessions 到此结束；如果没有这个边界说明，初学者不容易看出代表样本范围。

    def test_verify_before_action_blocks_drift_with_zero_events(self) -> None:  # 新增代码+URG2UniversalTargetSession：函数段开始，验收动作前复核遇到漂移时零事件拒绝；如果没有这段测试，后续 SendInput 可能误打漂移窗口。
        runtime = UniversalTargetSessionRuntime()  # 新增代码+URG2UniversalTargetSession：创建通用目标 session runtime；如果没有这一行，测试没有验证主体。
        session = runtime.open_target_session("notepad", candidates=_sample_candidates("notepad"))  # 新增代码+URG2UniversalTargetSession：建立稳定目标 session；如果没有这一行，漂移验证没有基准。
        drifted_window = dict(session["target_window"], pid=99117, hwnd=99118, window_id="hwnd:99118")  # 新增代码+URG2UniversalTargetSession：构造 pid/hwnd 漂移窗口；如果没有这一行，测试不会触发漂移分支。
        verification = runtime.verify_before_action(session, drifted_window)  # 新增代码+URG2UniversalTargetSession：执行动作前复核；如果没有这一行，漂移门禁没有被调用。
        self.assertFalse(verification["allowed"])  # 新增代码+URG2UniversalTargetSession：断言漂移不允许动作；如果没有这一行，动作可能继续落到错误窗口。
        self.assertTrue(verification["target_drift_blocks_action"])  # 新增代码+URG2UniversalTargetSession：断言拒绝原因是漂移；如果没有这一行，失败原因不可审计。
        self.assertEqual(0, verification["low_level_event_count"])  # 新增代码+URG2UniversalTargetSession：断言漂移时底层事件为 0；如果没有这一行，拒绝路径可能仍发送输入。
    # 新增代码+URG2UniversalTargetSession：函数段结束，test_verify_before_action_blocks_drift_with_zero_events 到此结束；如果没有这个边界说明，初学者不容易看出漂移测试范围。

    def test_main_prints_fixed_visible_terminal_tokens(self) -> None:  # 新增代码+URG2UniversalTargetSession：函数段开始，验收 main 输出真实终端固定 token；如果没有这段测试，controller 场景可能匹配不到结果。
        buffer = io.StringIO()  # 新增代码+URG2UniversalTargetSession：创建输出缓冲区；如果没有这一行，main 打印内容无法断言。
        with redirect_stdout(buffer):  # 新增代码+URG2UniversalTargetSession：捕获 main 输出；如果没有这一行，测试只能依赖退出码。
            exit_code = main([])  # 新增代码+URG2UniversalTargetSession：运行 URG-2 命令行入口；如果没有这一行，真实终端入口没有覆盖。
        output = buffer.getvalue()  # 新增代码+URG2UniversalTargetSession：读取捕获输出；如果没有这一行，token 断言没有文本来源。
        self.assertEqual(0, exit_code)  # 新增代码+URG2UniversalTargetSession：断言 main 成功；如果没有这一行，失败退出也可能被忽略。
        self.assertIn("universal_target_session_ready=true", output)  # 新增代码+URG2UniversalTargetSession：断言输出包含 session 就绪 token；如果没有这一行，用户看不到 URG-2 核心能力。
        self.assertIn("generic_target_resolver_used=true", output)  # 新增代码+URG2UniversalTargetSession：断言输出包含通用 resolver token；如果没有这一行，通用性不可见。
        self.assertIn("per_app_controller_required=false", output)  # 新增代码+URG2UniversalTargetSession：断言输出明确无需 per-app controller；如果没有这一行，架构边界不可见。
        self.assertIn("target_drift_zero_events=true", output)  # 新增代码+URG2UniversalTargetSession：断言输出包含漂移零事件 token；如果没有这一行，防漂移边界不可见。
        self.assertIn("low_level_event_count=0", output)  # 新增代码+URG2UniversalTargetSession：断言输出底层事件为 0；如果没有这一行，session 阶段的只读边界不可见。
    # 新增代码+URG2UniversalTargetSession：函数段结束，test_main_prints_fixed_visible_terminal_tokens 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 测试范围。
# 新增代码+URG2UniversalTargetSession：类段结束，UniversalTargetSessionTests 到此结束；如果没有这个边界说明，初学者不容易看出 URG-2 测试集合范围。


if __name__ == "__main__":  # 新增代码+URG2UniversalTargetSession：文件入口段开始，允许直接运行本测试文件；如果没有这一行，初学者需要记住完整 unittest 命令。
    unittest.main()  # 新增代码+URG2UniversalTargetSession：启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+URG2UniversalTargetSession：文件入口段结束，本测试文件到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
