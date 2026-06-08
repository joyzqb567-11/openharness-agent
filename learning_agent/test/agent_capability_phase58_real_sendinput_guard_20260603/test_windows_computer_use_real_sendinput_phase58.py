import json  # 新增代码+Phase58RealSendInputGuard: 导入 JSON 用来检查结果和事件里不会泄露 type_text 原文；如果没有这行代码，测试无法做全局泄露扫描。
import unittest  # 新增代码+Phase58RealSendInputGuard: 导入 unittest 承载 Phase58 自动化测试；如果没有这行代码，本阶段测试不会被标准测试命令发现。
from pathlib import Path  # 新增代码+Phase58RealSendInputGuard: 导入 Path 稳定读取真实终端验收场景；如果没有这行代码，Windows 路径拼接会更脆弱。
from typing import Any  # 新增代码+Phase58RealSendInputGuard: 导入 Any 标注 fake observer 和 sender 的 JSON 数据；如果没有这行代码，测试辅助对象接口不清楚。

from learning_agent.computer_use.real_sendinput_guard import PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_MARKER, PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_OK_TOKEN, Phase58RecordingLowLevelSender, Phase58StaticSafeWindowObserver, WindowsRealSendInputGuardRuntime, phase58_cli_line, run_phase58_real_sendinput_guard_contract  # 新增代码+Phase58RealSendInputGuard: 导入预期的 Phase58 真实 SendInput 守卫入口；如果没有这行代码，红灯会证明本阶段生产模块尚未实现。
from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase58RealSendInputGuard: 复用静态窗口 inventory 构造可信窗口快照；如果没有这行代码，单测会依赖用户真实桌面状态。


class WindowsComputerUseRealSendInputPhase58Tests(unittest.TestCase):  # 新增代码+Phase58RealSendInputGuard: 类段开始，组织 Phase58 真实 SendInput 目标守卫测试；如果没有这个类，unittest 不会运行本阶段门禁。
    def _safe_window(self) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，提供 Phase58 自有安全窗口引用；如果没有这段函数，每个测试都要重复构造安全窗口。
        return {"app_id": "phase58_safe_app", "window_id": "hwnd:5801", "hwnd": 5801, "pid": 580, "title": "LearningAgent-Phase58-RealSendInputGuardSmoke", "title_preview": "LearningAgent-Phase58-RealSendInputGuardSmoke", "class_name": "WindowsForms10.Window", "rect": {"left": 100, "top": 120, "right": 740, "bottom": 520}, "safe_to_target": True}  # 新增代码+Phase58RealSendInputGuard: 返回只允许测试动作命中的窗口；如果没有这行代码，目标守卫没有可信输入。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，_safe_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口样本范围。

    def _forbidden_window(self) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，提供禁止窗口引用；如果没有这段函数，零低层事件拒绝路径缺少测试输入。
        return {"app_id": "powershell.exe", "window_id": "hwnd:9999", "hwnd": 9999, "pid": 999, "title_preview": "Windows PowerShell", "rect": {"left": 0, "top": 0, "right": 800, "bottom": 400}}  # 新增代码+Phase58RealSendInputGuard: 返回终端类窗口；如果没有这行代码，测试不能证明禁止目标不会发送事件。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，_forbidden_window 到此结束；如果没有这个边界说明，初学者不容易看出禁止样本范围。

    def test_guarded_runtime_sends_only_after_safe_target_and_before_after_observe(self) -> None:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，验证安全窗口通过目标守卫后才发送，并且有前后观察；如果没有这个测试，真实动作可能缺少 evidence 链。
        window = self._safe_window()  # 新增代码+Phase58RealSendInputGuard: 读取安全窗口样本；如果没有这行代码，runtime 没有目标。
        sender = Phase58RecordingLowLevelSender()  # 新增代码+Phase58RealSendInputGuard: 创建只记录低层事件的 sender；如果没有这行代码，单测可能触碰真实鼠标键盘。
        observer = Phase58StaticSafeWindowObserver(before_text="before", after_text="after")  # 新增代码+Phase58RealSendInputGuard: 创建前后不同的观察器；如果没有这行代码，测试无法证明动作后状态变化。
        inventory = StaticWindowsWindowInventory([window], captured_at="2026-06-03T00:00:00Z", source="phase58-static")  # 新增代码+Phase58RealSendInputGuard: 构造只包含安全窗口的可信快照；如果没有这行代码，目标守卫无法复查窗口身份。
        runtime = WindowsRealSendInputGuardRuntime(platform="win32", inventory=inventory, low_level_sender=sender, observer=observer)  # 新增代码+Phase58RealSendInputGuard: 创建注入 fake sender/observer 的 runtime；如果没有这行代码，测试无法安全驱动发送路径。
        result = runtime.execute_safe_action(window, "click", {"x": 35, "y": 45})  # 新增代码+Phase58RealSendInputGuard: 对安全窗口执行一次点击；如果没有这行代码，前后观察和发送路径没有输入。
        self.assertTrue(result["ok"])  # 新增代码+Phase58RealSendInputGuard: 断言安全动作成功；如果没有这行代码，失败路径也可能被误当成功路径。
        self.assertTrue(result["target_guard_passed"])  # 新增代码+Phase58RealSendInputGuard: 断言目标守卫通过；如果没有这行代码，发送可能绕过守卫。
        self.assertTrue(result["before_after_observed"])  # 新增代码+Phase58RealSendInputGuard: 断言动作前后观察都发生；如果没有这行代码，evidence 链可能缺少现场。
        self.assertTrue(result["after_state_changed"])  # 新增代码+Phase58RealSendInputGuard: 断言后置观察确实变化；如果没有这行代码，验收无法确认动作有可见效果。
        self.assertGreater(result["low_level_event_count"], 0)  # 新增代码+Phase58RealSendInputGuard: 断言通过安全门后才有低层事件；如果没有这行代码，runtime 可能只做空成功。
        self.assertEqual(sender.low_level_events[0]["type"], "mouse_move")  # 新增代码+Phase58RealSendInputGuard: 断言点击前先移动到目标坐标；如果没有这行代码，点击落点不可审计。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，test_guarded_runtime_sends_only_after_safe_target_and_before_after_observe 到此结束；如果没有这个边界说明，初学者不容易看出安全发送测试范围。

    def test_forbidden_or_changed_target_sends_zero_low_level_events(self) -> None:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，验证任一门禁失败时低层事件为 0；如果没有这个测试，表面拒绝可能仍有系统副作用。
        safe_window = self._safe_window()  # 新增代码+Phase58RealSendInputGuard: 读取安全窗口样本；如果没有这行代码，改变目标测试没有基准。
        changed_window = dict(safe_window, title_preview="LearningAgent-Phase58-ChangedTitle")  # 新增代码+Phase58RealSendInputGuard: 构造标题变化的同 hwnd 窗口；如果没有这行代码，目标漂移拒绝路径缺少输入。
        forbidden_sender = Phase58RecordingLowLevelSender()  # 新增代码+Phase58RealSendInputGuard: 创建禁止目标 sender；如果没有这行代码，无法确认拒绝时未发送事件。
        forbidden_runtime = WindowsRealSendInputGuardRuntime(platform="win32", inventory=StaticWindowsWindowInventory([self._forbidden_window()]), low_level_sender=forbidden_sender, observer=Phase58StaticSafeWindowObserver())  # 新增代码+Phase58RealSendInputGuard: 创建只含禁止窗口的 runtime；如果没有这行代码，禁止目标可能被误放行。
        forbidden_result = forbidden_runtime.execute_safe_action(self._forbidden_window(), "click", {"x": 1, "y": 1})  # 新增代码+Phase58RealSendInputGuard: 对禁止窗口尝试点击；如果没有这行代码，零事件拒绝没有触发。
        changed_sender = Phase58RecordingLowLevelSender()  # 新增代码+Phase58RealSendInputGuard: 创建标题变化 sender；如果没有这行代码，无法检查变化目标未发送事件。
        changed_runtime = WindowsRealSendInputGuardRuntime(platform="win32", inventory=StaticWindowsWindowInventory([changed_window]), low_level_sender=changed_sender, observer=Phase58StaticSafeWindowObserver())  # 新增代码+Phase58RealSendInputGuard: 创建快照中目标已变化的 runtime；如果没有这行代码，身份漂移拒绝无法覆盖。
        changed_result = changed_runtime.execute_safe_action(safe_window, "click", {"x": 1, "y": 1})  # 新增代码+Phase58RealSendInputGuard: 用旧身份请求点击；如果没有这行代码，目标复验逻辑没有输入。
        self.assertFalse(forbidden_result["ok"])  # 新增代码+Phase58RealSendInputGuard: 断言禁止目标被拒绝；如果没有这行代码，终端窗口可能被误操作。
        self.assertFalse(changed_result["ok"])  # 新增代码+Phase58RealSendInputGuard: 断言目标变化被拒绝；如果没有这行代码，旧窗口引用可能被继续使用。
        self.assertEqual(forbidden_result["low_level_event_count"], 0)  # 新增代码+Phase58RealSendInputGuard: 断言禁止目标发送 0 事件；如果没有这行代码，拒绝仍可能有副作用。
        self.assertEqual(changed_result["low_level_event_count"], 0)  # 新增代码+Phase58RealSendInputGuard: 断言目标变化发送 0 事件；如果没有这行代码，窗口漂移可能仍会点击。
        self.assertEqual(forbidden_sender.low_level_events, [])  # 新增代码+Phase58RealSendInputGuard: 直接检查 fake sender 没有记录；如果没有这行代码，结果字段可能撒谎。
        self.assertEqual(changed_sender.low_level_events, [])  # 新增代码+Phase58RealSendInputGuard: 直接检查变化目标未发送；如果没有这行代码，低层副作用漏检。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，test_forbidden_or_changed_target_sends_zero_low_level_events 到此结束；如果没有这个边界说明，初学者不容易看出拒绝路径范围。

    def test_type_text_result_redacts_raw_text_and_records_length_hash_only(self) -> None:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，验证 type_text 原文不进入结果、事件或观察摘要；如果没有这个测试，用户输入可能泄露到日志。
        window = self._safe_window()  # 新增代码+Phase58RealSendInputGuard: 读取安全窗口样本；如果没有这行代码，文本动作没有目标。
        secret_text = "phase58-secret-raw-text"  # 新增代码+Phase58RealSendInputGuard: 准备泄露检测文本；如果没有这行代码，脱敏测试没有明确对象。
        sender = Phase58RecordingLowLevelSender()  # 新增代码+Phase58RealSendInputGuard: 创建 fake sender；如果没有这行代码，文本测试可能触碰真实键盘。
        runtime = WindowsRealSendInputGuardRuntime(platform="win32", inventory=StaticWindowsWindowInventory([window]), low_level_sender=sender, observer=Phase58StaticSafeWindowObserver(before_text="before", after_text="after"))  # 新增代码+Phase58RealSendInputGuard: 创建安全 runtime；如果没有这行代码，文本动作无法通过守卫。
        result = runtime.execute_safe_action(window, "type_text", {"text": secret_text, "x": 20, "y": 30})  # 新增代码+Phase58RealSendInputGuard: 执行文本输入；如果没有这行代码，脱敏路径没有运行。
        encoded = json.dumps({"result": result, "events": sender.low_level_events}, ensure_ascii=False).lower()  # 新增代码+Phase58RealSendInputGuard: 序列化可见输出做泄露检查；如果没有这行代码，单字段断言容易漏掉原文。
        self.assertTrue(result["ok"])  # 新增代码+Phase58RealSendInputGuard: 断言安全文本动作成功；如果没有这行代码，失败结果也可能通过脱敏断言。
        self.assertEqual(result["text_length"], len(secret_text))  # 新增代码+Phase58RealSendInputGuard: 断言只保留文本长度；如果没有这行代码，审计无法知道输入规模。
        self.assertTrue(result["text_redacted"])  # 新增代码+Phase58RealSendInputGuard: 断言文本被明确标记脱敏；如果没有这行代码，用户可能误解字段缺失。
        self.assertNotIn(secret_text.lower(), encoded)  # 新增代码+Phase58RealSendInputGuard: 断言原文不在任何可见结果中；如果没有这行代码，日志泄露不会被发现。
        self.assertIn("text_sha256_16", result)  # 新增代码+Phase58RealSendInputGuard: 断言保留短哈希；如果没有这行代码，审计无法安全关联输入。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，test_type_text_result_redacts_raw_text_and_records_length_hash_only 到此结束；如果没有这个边界说明，初学者不容易看出文本脱敏范围。

    def test_phase58_cli_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，验证 CLI 和真实终端场景 token 稳定；如果没有这个测试，controller 可能漏验关键安全字段。
        report = run_phase58_real_sendinput_guard_contract(real_smoke=False)  # 新增代码+Phase58RealSendInputGuard: 运行无真实桌面的合同自检；如果没有这行代码，单测会打开安全窗口并发送真实输入。
        cli_line = phase58_cli_line(report)  # 新增代码+Phase58RealSendInputGuard: 生成稳定 CLI token 行；如果没有这行代码，场景断言无法复用。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase58_real_sendinput_guard.json")  # 新增代码+Phase58RealSendInputGuard: 定位 Phase58 可见终端场景；如果没有这行代码，测试无法确认场景配置。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase58RealSendInputGuard: 读取场景文本；如果没有这行代码，场景缺失或漏 token 不会暴露。
        expected_tokens = {PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_MARKER, PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_OK_TOKEN, "target_guard=true", "low_level_events=true", "forbidden_zero_events=true", "before_after=true", "after_changed=true", "raw_text_hidden=true", "safe_window_only=true", "actions_expanded=true"}  # 新增代码+Phase58RealSendInputGuard: 定义 CLI 和场景都必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase58RealSendInputGuard: 遍历稳定 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase58RealSendInputGuard: 断言 CLI 包含 token；如果没有这行代码，自检输出漂移不会被发现。
            self.assertIn(token, scenario_text)  # 新增代码+Phase58RealSendInputGuard: 断言场景包含 token；如果没有这行代码，真实终端验收可能漏检。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，test_phase58_cli_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 场景范围。
# 新增代码+Phase58RealSendInputGuard: 类段结束，WindowsComputerUseRealSendInputPhase58Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase58RealSendInputGuard: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase58RealSendInputGuard: 调用 unittest 主入口；如果没有这行代码，直接运行文件不会执行任何测试。
