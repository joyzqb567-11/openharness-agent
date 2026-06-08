import io  # 新增代码+URG3ActionDSL：导入内存文本缓冲区用来捕获 CLI 输出；如果没有这一行，测试无法检查真实终端会看到的固定 token。
import json  # 新增代码+URG3ActionDSL：导入 JSON 用来检查结果里是否泄露原始输入文本；如果没有这一行，文本脱敏只能靠人工肉眼判断。
import unittest  # 新增代码+URG3ActionDSL：导入标准测试框架；如果没有这一行，本文件不会被 unittest 正常发现和执行。
from contextlib import redirect_stdout  # 新增代码+URG3ActionDSL：导入 stdout 重定向工具；如果没有这一行，main 函数打印的验收行无法被断言。
from typing import Any  # 新增代码+URG3ActionDSL：导入 Any 描述动态动作和候选应用字典；如果没有这一行，测试 helper 的接口边界不清楚。

from learning_agent.computer_use.universal_action_dsl import PHASE118_UNIVERSAL_ACTION_DSL_MARKER, PHASE118_UNIVERSAL_ACTION_DSL_OK_TOKEN, UniversalActionDslRuntime, main, phase118_universal_action_dsl_cli_line, run_phase118_universal_action_dsl_contract  # 新增代码+URG3ActionDSL：导入 URG-3 公开 API；如果没有这一行，红测无法证明模块缺失或 API 漂移。


def _sample_candidates(target: str) -> list[dict[str, Any]]:  # 新增代码+URG3ActionDSL：函数段开始，生成代表性普通应用候选；如果没有这段函数，测试会依赖本机是否安装具体应用。
    return [{"display_name": target, "executable": f"{target}.exe", "source": "urg3_injected_start_menu", "installed_app_verified": True}]  # 新增代码+URG3ActionDSL：返回通用发现候选；如果没有这一行，target session 无法在单测里稳定建立。
# 新增代码+URG3ActionDSL：函数段结束，_sample_candidates 到此结束；如果没有这个边界说明，初学者不容易看出候选生成范围。


class UniversalActionDslTests(unittest.TestCase):  # 新增代码+URG3ActionDSL：类段开始，集中验收通用 Action DSL 到 SendInput dispatcher 的桥；如果没有这个类，URG-3 没有自动化护栏。
    def test_contract_reports_generic_action_dsl_sendinput_bridge(self) -> None:  # 新增代码+URG3ActionDSL：函数段开始，验收 URG-3 合同输出核心 token；如果没有这段测试，模块可能只输出文案而不输出机器事实。
        report = run_phase118_universal_action_dsl_contract()  # 新增代码+URG3ActionDSL：运行安全记录型合同；如果没有这一行，断言没有结构化事实来源。
        cli_line = phase118_universal_action_dsl_cli_line(report)  # 新增代码+URG3ActionDSL：生成真实终端固定验收行；如果没有这一行，场景文件无法复用同一格式。
        self.assertTrue(report["passed"])  # 新增代码+URG3ActionDSL：断言总体合同通过；如果没有这一行，局部字段成功可能掩盖整体失败。
        self.assertTrue(report["generic_action_dsl_ready"])  # 新增代码+URG3ActionDSL：断言通用动作 DSL 已就绪；如果没有这一行，后续 loop 可能没有动作语言基础。
        self.assertTrue(report["generic_action_to_sendinput_bridge"])  # 新增代码+URG3ActionDSL：断言 DSL 已桥接到 SendInput dispatcher；如果没有这一行，动作仍可能停在计划层。
        self.assertTrue(report["normal_actions_reach_low_level_sender"])  # 新增代码+URG3ActionDSL：断言正常动作到达低层 sender；如果没有这一行，低层事件数可能永远为 0。
        self.assertTrue(report["target_identity_rechecked_before_each_action"])  # 新增代码+URG3ActionDSL：断言每次动作前都会复核目标身份；如果没有这一行，窗口漂移风险会重新出现。
        self.assertTrue(report["target_drift_zero_events"])  # 新增代码+URG3ActionDSL：断言目标漂移时事件数为 0；如果没有这一行，拒绝路径可能只是嘴上拒绝。
        self.assertTrue(report["abort_zero_events"])  # 新增代码+URG3ActionDSL：断言 abort 时事件数为 0；如果没有这一行，stop 后仍继续动作的问题可能复发。
        self.assertTrue(report["type_text_raw_hidden"])  # 新增代码+URG3ActionDSL：断言原始文本没有泄露；如果没有这一行，输入内容可能进入日志和审计。
        self.assertFalse(report["per_app_controller_required"])  # 新增代码+URG3ActionDSL：断言不需要逐应用 controller；如果没有这一行，用户指出的架构问题可能复发。
        self.assertFalse(report["hardcoded_app_whitelist_required"])  # 新增代码+URG3ActionDSL：断言不需要硬编码应用白名单；如果没有这一行，成千上万应用无法通用。
        self.assertFalse(report["real_dispatch_performed"])  # 新增代码+URG3ActionDSL：断言合同默认不触碰真实桌面；如果没有这一行，单测可能意外移动用户鼠标键盘。
        self.assertGreater(report["low_level_event_count"], 0)  # 新增代码+URG3ActionDSL：断言正常动作确实展开出低层事件；如果没有这一行，桥接可能是空实现。
        self.assertIn(PHASE118_UNIVERSAL_ACTION_DSL_MARKER, cli_line)  # 新增代码+URG3ActionDSL：断言 CLI 行包含 ready marker；如果没有这一行，可见终端验收没有稳定锚点。
        self.assertIn(PHASE118_UNIVERSAL_ACTION_DSL_OK_TOKEN, cli_line)  # 新增代码+URG3ActionDSL：断言 CLI 行包含 OK token；如果没有这一行，验收器无法区分成功输出。
    # 新增代码+URG3ActionDSL：函数段结束，test_contract_reports_generic_action_dsl_sendinput_bridge 到此结束；如果没有这个边界说明，初学者不容易看出合同测试范围。

    def test_runtime_dispatches_representative_actions_through_one_bridge(self) -> None:  # 新增代码+URG3ActionDSL：函数段开始，验收代表性动作都走同一个 runtime；如果没有这段测试，代码可能暗中按应用分支执行。
        runtime = UniversalActionDslRuntime()  # 新增代码+URG3ActionDSL：创建通用动作 DSL runtime；如果没有这一行，测试没有统一执行主体。
        session = runtime.open_target_session("notepad", candidates=_sample_candidates("notepad"))  # 新增代码+URG3ActionDSL：创建代表性普通应用 session；如果没有这一行，动作前身份复核没有基准。
        secret_text = "urg3-secret-text-should-not-leak"  # 新增代码+URG3ActionDSL：准备泄露检查文本；如果没有这一行，文本脱敏没有明确样本。
        actions = [{"type": "focus_window"}, {"type": "click_point", "x": 10, "y": 20}, {"type": "double_click_point", "x": 11, "y": 21}, {"type": "drag_path", "points": [{"x": 1, "y": 1}, {"x": 5, "y": 5}, {"x": 9, "y": 1}]}, {"type": "type_text", "text": secret_text}, {"type": "press_key", "key": "ENTER"}, {"type": "hotkey", "keys": ["CTRL", "S"]}, {"type": "scroll", "x": 12, "y": 22, "delta": -120}, {"type": "wait", "milliseconds": 1}, {"type": "observe"}]  # 新增代码+URG3ActionDSL：定义所有 URG-3 代表性 DSL 动作；如果没有这一行，动作覆盖面不足。
        results = [runtime.dispatch(session, action) for action in actions]  # 新增代码+URG3ActionDSL：逐个通过同一个 runtime 分发动作；如果没有这一行，无法证明动作桥真实被调用。
        payload = json.dumps({"results": results, "events": runtime.low_level_events}, ensure_ascii=False)  # 新增代码+URG3ActionDSL：汇总结果和低层事件用于泄露检查；如果没有这一行，敏感文本可能藏在任一字段里。
        event_types = {str(event.get("type", "")) for event in runtime.low_level_events}  # 新增代码+URG3ActionDSL：收集低层事件类型；如果没有这一行，无法证明动作族覆盖完整。
        self.assertTrue(all(result["ok"] for result in results))  # 新增代码+URG3ActionDSL：断言所有代表性动作都被通用桥接受；如果没有这一行，某个动作失败可能被忽略。
        self.assertTrue({"mouse_move", "mouse_down", "mouse_up", "mouse_wheel", "key_down", "key_up", "unicode_text"}.issubset(event_types))  # 新增代码+URG3ActionDSL：断言鼠标、滚轮、键盘、文本族都已展开；如果没有这一行，桥接覆盖面会缩水。
        self.assertNotIn(secret_text, payload)  # 新增代码+URG3ActionDSL：断言原始文本没有出现在可见结果；如果没有这一行，日志泄露不会被发现。
        self.assertGreater(len(runtime.low_level_events), 0)  # 新增代码+URG3ActionDSL：断言至少有低层事件产生；如果没有这一行，动作可能只是空跑。
    # 新增代码+URG3ActionDSL：函数段结束，test_runtime_dispatches_representative_actions_through_one_bridge 到此结束；如果没有这个边界说明，初学者不容易看出动作覆盖范围。

    def test_drift_abort_and_unknown_session_send_zero_events(self) -> None:  # 新增代码+URG3ActionDSL：函数段开始，验收拒绝路径都是零事件；如果没有这段测试，安全门禁可能只返回失败但已经发了事件。
        runtime = UniversalActionDslRuntime()  # 新增代码+URG3ActionDSL：创建通用动作 DSL runtime；如果没有这一行，拒绝路径没有执行主体。
        session = runtime.open_target_session("calc", candidates=_sample_candidates("calc"))  # 新增代码+URG3ActionDSL：创建代表性普通应用 session；如果没有这一行，漂移测试没有原始目标。
        drifted_window = dict(session["target_window"], pid=999118, hwnd=999119, window_id="hwnd:999119")  # 新增代码+URG3ActionDSL：构造 pid/hwnd 漂移窗口；如果没有这一行，target guard 不会进入拒绝分支。
        drift_result = runtime.dispatch(session, {"type": "click_point", "x": 1, "y": 1}, current_window=drifted_window)  # 新增代码+URG3ActionDSL：对漂移窗口尝试点击；如果没有这一行，漂移零事件没有事实来源。
        abort_result = runtime.dispatch(session, {"type": "click_point", "x": 1, "y": 1}, abort_requested=True)  # 新增代码+URG3ActionDSL：在 abort 状态尝试点击；如果没有这一行，stop/abort 门禁没有事实来源。
        unknown_result = runtime.dispatch({"session_id": "missing-session", "target_window": session["target_window"]}, {"type": "click_point", "x": 1, "y": 1})  # 新增代码+URG3ActionDSL：用未知 session 尝试点击；如果没有这一行，坏凭证路径没有测试。
        self.assertFalse(drift_result["ok"])  # 新增代码+URG3ActionDSL：断言漂移动作失败；如果没有这一行，漂移窗口可能被误操作。
        self.assertFalse(abort_result["ok"])  # 新增代码+URG3ActionDSL：断言 abort 动作失败；如果没有这一行，停止请求可能被忽略。
        self.assertFalse(unknown_result["ok"])  # 新增代码+URG3ActionDSL：断言未知 session 动作失败；如果没有这一行，伪造 session 可能进入动作层。
        self.assertEqual(0, drift_result["low_level_event_count"])  # 新增代码+URG3ActionDSL：断言漂移失败零事件；如果没有这一行，失败前可能已经发出点击。
        self.assertEqual(0, abort_result["low_level_event_count"])  # 新增代码+URG3ActionDSL：断言 abort 失败零事件；如果没有这一行，stop 后可能仍有残余动作。
        self.assertEqual(0, unknown_result["low_level_event_count"])  # 新增代码+URG3ActionDSL：断言未知 session 失败零事件；如果没有这一行，非法凭证可能造成桌面副作用。
    # 新增代码+URG3ActionDSL：函数段结束，test_drift_abort_and_unknown_session_send_zero_events 到此结束；如果没有这个边界说明，初学者不容易看出拒绝路径范围。

    def test_main_prints_fixed_visible_terminal_tokens(self) -> None:  # 新增代码+URG3ActionDSL：函数段开始，验收 main 输出可被真实终端场景匹配；如果没有这段测试，controller 场景可能找不到最终答案。
        buffer = io.StringIO()  # 新增代码+URG3ActionDSL：创建输出缓冲区；如果没有这一行，main 打印内容无法断言。
        with redirect_stdout(buffer):  # 新增代码+URG3ActionDSL：捕获 main 输出；如果没有这一行，测试只能看退出码而看不到 token。
            exit_code = main([])  # 新增代码+URG3ActionDSL：运行 URG-3 命令行入口；如果没有这一行，真实终端入口没有自动化覆盖。
        output = buffer.getvalue()  # 新增代码+URG3ActionDSL：读取捕获的输出；如果没有这一行，后续断言没有文本来源。
        self.assertEqual(0, exit_code)  # 新增代码+URG3ActionDSL：断言 main 成功退出；如果没有这一行，失败也可能被输出 token 掩盖。
        self.assertIn("generic_action_dsl_ready=true", output)  # 新增代码+URG3ActionDSL：断言输出 DSL ready token；如果没有这一行，用户看不到动作层是否就绪。
        self.assertIn("generic_action_to_sendinput_bridge=true", output)  # 新增代码+URG3ActionDSL：断言输出桥接 ready token；如果没有这一行，SendInput 桥接事实不可见。
        self.assertIn("target_identity_rechecked_before_each_action=true", output)  # 新增代码+URG3ActionDSL：断言输出动作前复核 token；如果没有这一行，漂移保护不可见。
        self.assertIn("target_drift_zero_events=true", output)  # 新增代码+URG3ActionDSL：断言输出漂移零事件 token；如果没有这一行，拒绝边界不可见。
        self.assertIn("abort_zero_events=true", output)  # 新增代码+URG3ActionDSL：断言输出 abort 零事件 token；如果没有这一行，stop 边界不可见。
        self.assertIn("real_dispatch_performed=false", output)  # 新增代码+URG3ActionDSL：断言合同默认不触碰真实桌面；如果没有这一行，安全边界不可见。
    # 新增代码+URG3ActionDSL：函数段结束，test_main_prints_fixed_visible_terminal_tokens 到此结束；如果没有这个边界说明，初学者不容易看出 CLI token 测试范围。
# 新增代码+URG3ActionDSL：类段结束，UniversalActionDslTests 到此结束；如果没有这个边界说明，初学者不容易看出 URG-3 测试集合范围。


if __name__ == "__main__":  # 新增代码+URG3ActionDSL：文件入口段开始，允许直接运行本测试文件；如果没有这一行，初学者需要记完整 unittest 命令。
    unittest.main()  # 新增代码+URG3ActionDSL：启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+URG3ActionDSL：文件入口段结束，本测试文件到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
