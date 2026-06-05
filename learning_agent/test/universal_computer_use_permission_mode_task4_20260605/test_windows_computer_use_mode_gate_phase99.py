import tempfile  # 新增代码+Phase99UniversalComputerUseModeGate：导入临时目录用来隔离 mode session 和运行报告；如果没有这行代码，测试会污染真实 memory 状态。
import unittest  # 新增代码+Phase99UniversalComputerUseModeGate：导入 unittest 沿用项目现有测试框架；如果没有这行代码，python -m unittest 无法发现本文件测试。
from pathlib import Path  # 新增代码+Phase99UniversalComputerUseModeGate：导入 Path 统一处理 Windows 路径；如果没有这行代码，临时目录拼接会更脆弱。

from learning_agent.computer_use.mode_session import ComputerUseModeSessionStore  # 新增代码+Phase99UniversalComputerUseModeGate：导入 Phase98 模式 session store；如果没有这行代码，测试无法打开 normal/observe 模式。
from learning_agent.computer_use.real_app_safety_boundary import WindowsRealAppSafetyBoundary  # 新增代码+Phase99UniversalComputerUseModeGate：导入待接入 mode 的安全边界；如果没有这行代码，红灯无法锁定新增边界方法。
from learning_agent.computer_use.universal_live_execution import UniversalWindowsLiveExecutionGate  # 新增代码+Phase99UniversalComputerUseModeGate：导入待接入 mode 的 live gate；如果没有这行代码，测试无法覆盖真实动作派发前的总闸。


class WindowsComputerUseModeGatePhase99Tests(unittest.TestCase):  # 新增代码+Phase99UniversalComputerUseModeGate：类段开始，集中验证 Phase99 mode-aware live execution gate；如果没有这个类，normal mode 替代 app 白名单没有自动门禁。
    def _normal_window(self) -> dict[str, object]:  # 新增代码+Phase99UniversalComputerUseModeGate：函数段开始，提供普通应用窗口样本；如果没有这段函数，各测试会重复且可能字段不一致。
        return {"app_id": "generic_windows_app.exe", "process_name": "generic_windows_app.exe", "window_id": "hwnd:9901", "title_preview": "Generic Windows App", "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase99UniversalComputerUseModeGate：返回普通应用窗口；如果没有这行代码，normal mode 正例没有稳定目标。
    # 新增代码+Phase99UniversalComputerUseModeGate：函数段结束，_normal_window 到此结束；如果没有这个边界说明，初学者不容易看出普通窗口样本范围。

    def _terminal_window(self) -> dict[str, object]:  # 新增代码+Phase99UniversalComputerUseModeGate：函数段开始，提供终端危险窗口样本；如果没有这段函数，危险目标拒绝没有固定输入。
        return {"app_id": "powershell.exe", "process_name": "powershell.exe", "window_id": "hwnd:9902", "title_preview": "Windows PowerShell", "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase99UniversalComputerUseModeGate：返回 PowerShell 窗口；如果没有这行代码，terminal/Powershell 拦截不会被测试覆盖。
    # 新增代码+Phase99UniversalComputerUseModeGate：函数段结束，_terminal_window 到此结束；如果没有这个边界说明，初学者不容易看出危险窗口样本范围。

    def test_boundary_normal_mode_allows_ordinary_app_without_per_app_grant(self) -> None:  # 新增代码+Phase99UniversalComputerUseModeGate：函数段开始，验证 normal mode 能放行普通 app 且不需要 per-app grant；如果没有这段测试，系统可能退回普通 app 白名单。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase99UniversalComputerUseModeGate：创建隔离目录；如果没有这行代码，mode 状态会写进真实用户目录。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir) / "mode_sessions")  # 新增代码+Phase99UniversalComputerUseModeGate：创建隔离 mode store；如果没有这行代码，测试无法控制 normal 状态。
            store.open_mode(mode="normal", reason="Phase99 normal mode allows ordinary apps")  # 新增代码+Phase99UniversalComputerUseModeGate：打开 normal 模式；如果没有这行代码，边界层应处于 off 而不能验证放行。
            decision = WindowsRealAppSafetyBoundary().evaluate_with_mode_session(self._normal_window(), "click_by_visual_point", store, "phase99-normal")  # 新增代码+Phase99UniversalComputerUseModeGate：调用新增 mode-aware 边界；如果没有这行代码，测试无法证明不走 per-app grant。
        self.assertTrue(decision["allowed"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言普通 app 被允许；如果没有这行代码，normal mode 放行失败不会暴露。
        self.assertEqual(decision["decision"], "allowed_by_computer_use_mode")  # 新增代码+Phase99UniversalComputerUseModeGate：断言放行来源是 mode session；如果没有这行代码，旧 persistent grant 路径可能混入。
        self.assertFalse(decision["per_app_allowlist_required"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言不需要每应用白名单；如果没有这行代码，Task4 核心目标没有保护。
        self.assertTrue(decision["ready_for_low_level_send"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言已通过发送前门禁；如果没有这行代码，允许结果可能只是状态文字。
        self.assertTrue(decision["mode_session_used"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言确实使用 mode session；如果没有这行代码，测试无法区分旧授权路径。
        self.assertTrue(decision["ordinary_apps_allowed_by_risk_policy"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言普通 app 按风险策略放行；如果没有这行代码，normal mode 语义不完整。
        self.assertEqual(decision["low_level_event_count"], 0)  # 新增代码+Phase99UniversalComputerUseModeGate：断言边界层本身不发送低层事件；如果没有这行代码，放行检查可能已产生真实输入。
    # 新增代码+Phase99UniversalComputerUseModeGate：函数段结束，test_boundary_normal_mode_allows_ordinary_app_without_per_app_grant 到此结束；如果没有这个边界说明，初学者不容易看出 normal 正例范围。

    def test_boundary_normal_mode_blocks_terminal_target_with_zero_events(self) -> None:  # 新增代码+Phase99UniversalComputerUseModeGate：函数段开始，验证 normal mode 仍阻断终端目标；如果没有这段测试，normal 可能被误解为任意窗口放行。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase99UniversalComputerUseModeGate：创建隔离目录；如果没有这行代码，危险目标测试会污染真实 mode 状态。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir) / "mode_sessions")  # 新增代码+Phase99UniversalComputerUseModeGate：创建隔离 mode store；如果没有这行代码，测试无法打开 normal 状态。
            store.open_mode(mode="normal", reason="Phase99 terminal target must stay blocked")  # 新增代码+Phase99UniversalComputerUseModeGate：打开 normal 模式；如果没有这行代码，危险目标拒绝可能只是 off 状态拒绝。
            decision = WindowsRealAppSafetyBoundary().evaluate_with_mode_session(self._terminal_window(), "click", store, "phase99-terminal")  # 新增代码+Phase99UniversalComputerUseModeGate：评估终端点击；如果没有这行代码，危险目标零事件没有证据。
        self.assertFalse(decision["allowed"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言终端目标不允许；如果没有这行代码，危险目标误放行不会暴露。
        self.assertEqual(decision["decision"], "dangerous_target_blocked")  # 新增代码+Phase99UniversalComputerUseModeGate：断言原因码来自 mode session 危险目标策略；如果没有这行代码，边界层原因码可能漂移。
        self.assertEqual(decision["low_level_event_count"], 0)  # 新增代码+Phase99UniversalComputerUseModeGate：断言终端拒绝零事件；如果没有这行代码，拒绝后仍可能有真实输入。
        self.assertFalse(decision["ready_for_low_level_send"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言不允许进入低层发送；如果没有这行代码，拒绝语义不够硬。
        self.assertTrue(decision["mode_session_used"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言拒绝也经过 mode session；如果没有这行代码，危险目标可能绕开 Phase98 策略。
    # 新增代码+Phase99UniversalComputerUseModeGate：函数段结束，test_boundary_normal_mode_blocks_terminal_target_with_zero_events 到此结束；如果没有这个边界说明，初学者不容易看出终端拒绝范围。

    def test_boundary_observe_mode_normalizes_write_refusal_but_preserves_mode_decision(self) -> None:  # 新增代码+Phase99UniversalComputerUseModeGate：函数段开始，验证 observe 写动作拒绝被边界层规范化且保留原始 mode 决策；如果没有这段测试，调试信息和上层原因码会漂移。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase99UniversalComputerUseModeGate：创建隔离目录；如果没有这行代码，observe 状态会污染其它测试。
            store = ComputerUseModeSessionStore(base_dir=Path(temp_dir) / "mode_sessions")  # 新增代码+Phase99UniversalComputerUseModeGate：创建隔离 mode store；如果没有这行代码，无法打开 observe 模式。
            store.open_mode(mode="observe", reason="Phase99 observe mode blocks click")  # 新增代码+Phase99UniversalComputerUseModeGate：打开 observe 模式；如果没有这行代码，写动作拒绝不是 observe 专属。
            decision = WindowsRealAppSafetyBoundary().evaluate_with_mode_session(self._normal_window(), "click", store, "phase99-observe")  # 新增代码+Phase99UniversalComputerUseModeGate：评估 observe 下的 click；如果没有这行代码，规范化原因码没有样本。
        self.assertFalse(decision["allowed"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言 observe 不允许 click；如果没有这行代码，观察模式可能误写桌面。
        self.assertEqual(decision["decision"], "action_risk_exceeds_mode")  # 新增代码+Phase99UniversalComputerUseModeGate：断言边界层使用统一风险超模原因码；如果没有这行代码，上层处理会被底层细节绑定。
        self.assertEqual(decision["mode_decision"]["decision"], "observe_mode_blocks_write_action")  # 新增代码+Phase99UniversalComputerUseModeGate：断言原始 mode 决策被保留；如果没有这行代码，排查时看不到 Phase98 原因。
        self.assertEqual(decision["low_level_event_count"], 0)  # 新增代码+Phase99UniversalComputerUseModeGate：断言 observe 拒绝零事件；如果没有这行代码，拒绝后仍可能触发输入。
        self.assertFalse(decision["per_app_allowlist_required"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言 observe 拒绝不要求 app 白名单；如果没有这行代码，UI 可能误提示用户配置旧授权。
    # 新增代码+Phase99UniversalComputerUseModeGate：函数段结束，test_boundary_observe_mode_normalizes_write_refusal_but_preserves_mode_decision 到此结束；如果没有这个边界说明，初学者不容易看出 observe 拒绝范围。

    def test_live_gate_uses_open_normal_mode_without_per_app_allowlist_or_real_dispatch(self) -> None:  # 新增代码+Phase99UniversalComputerUseModeGate：函数段开始，验证 live gate 注入 normal mode 后能走 mode-aware 动作报告；如果没有这段测试，Task4 可能只改边界层没接派发入口。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase99UniversalComputerUseModeGate：创建隔离目录；如果没有这行代码，live gate 报告和 mode 状态会污染真实项目。
            root = Path(temp_dir)  # 新增代码+Phase99UniversalComputerUseModeGate：保存临时根目录；如果没有这行代码，后续路径会重复构造。
            mode_store = ComputerUseModeSessionStore(base_dir=root / "mode_sessions")  # 新增代码+Phase99UniversalComputerUseModeGate：创建要注入的 mode store；如果没有这行代码，live gate 无法共享已打开 normal 状态。
            mode_store.open_mode(mode="normal", reason="Phase99 live gate normal mode")  # 新增代码+Phase99UniversalComputerUseModeGate：显式打开 normal 模式；如果没有这行代码，请求真实动作应保持拒绝。
            runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "live_gate", mode_store=mode_store)  # 新增代码+Phase99UniversalComputerUseModeGate：创建注入 mode store 的 live gate；如果没有这行代码，测试无法验证新依赖入口。
            report = runtime.run_prompt("请打开 computer use，在普通应用里做一次安全的记录型点击和滚动。", request_real_actions=True)  # 新增代码+Phase99UniversalComputerUseModeGate：运行真实用户风格 prompt；如果没有这行代码，动作报告不会生成。
        acted_reports = [event["action_result"] for event in report["loop"]["events"] if event.get("state") == "acted"]  # 新增代码+Phase99UniversalComputerUseModeGate：提取闭环动作报告；如果没有这行代码，只看总报告可能漏掉动作层字段。
        self.assertTrue(report["mode_session_used"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言运行报告显示使用 mode session；如果没有这行代码，live gate 可能仍走旧授权。
        self.assertFalse(report["per_app_allowlist_required"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言运行报告不需要 per-app 白名单；如果没有这行代码，Task4 目标可能只在边界层成立。
        self.assertTrue(report["ordinary_apps_allowed_by_risk_policy"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言普通应用由风险策略放行；如果没有这行代码，normal mode 语义没有进入总报告。
        self.assertTrue(report["authorized_recording_loop_ready"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言记录型闭环已就绪；如果没有这行代码，mode 放行后可能没有进入动作层。
        self.assertFalse(report["real_dispatch_performed"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言测试场景不做物理派发；如果没有这行代码，自动化测试可能误操作桌面。
        self.assertEqual(report["low_level_event_count"], 0)  # 新增代码+Phase99UniversalComputerUseModeGate：断言总低层事件数为 0；如果没有这行代码，记录型派发边界不够硬。
        self.assertTrue(any(action.get("mode_session_used") for action in acted_reports))  # 新增代码+Phase99UniversalComputerUseModeGate：断言动作报告也显示 mode session；如果没有这行代码，只有总报告会掩盖动作层未接入。
        self.assertTrue(any(action.get("ordinary_apps_allowed_by_risk_policy") for action in acted_reports))  # 新增代码+Phase99UniversalComputerUseModeGate：断言动作报告显示普通应用风险策略放行；如果没有这行代码，动作层字段可能缺失。
        self.assertFalse(any(action.get("per_app_allowlist_required") for action in acted_reports))  # 新增代码+Phase99UniversalComputerUseModeGate：断言动作报告不要求 per-app 白名单；如果没有这行代码，旧授权要求可能混入动作层。
    # 新增代码+Phase99UniversalComputerUseModeGate：函数段结束，test_live_gate_uses_open_normal_mode_without_per_app_allowlist_or_real_dispatch 到此结束；如果没有这个边界说明，初学者不容易看出 live gate 正例范围。

    def test_live_gate_without_open_mode_refuses_real_actions_without_fake_grant(self) -> None:  # 新增代码+Phase99UniversalComputerUseModeGate：函数段开始，验证未打开 mode 不会伪造授权放行动作；如果没有这段测试，默认请求真实动作可能又靠假 approve 通过。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase99UniversalComputerUseModeGate：创建隔离目录；如果没有这行代码，未打开模式测试会受其它状态影响。
            root = Path(temp_dir)  # 新增代码+Phase99UniversalComputerUseModeGate：保存临时根目录；如果没有这行代码，路径使用会重复且易错。
            mode_store = ComputerUseModeSessionStore(base_dir=root / "mode_sessions")  # 新增代码+Phase99UniversalComputerUseModeGate：创建但不打开 mode store；如果没有这行代码，无法模拟 off 状态。
            runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "live_gate", mode_store=mode_store)  # 新增代码+Phase99UniversalComputerUseModeGate：把 off mode store 注入 live gate；如果没有这行代码，默认 store 可能不是测试控制的状态。
            report = runtime.run_prompt("请打开 computer use 并尝试控制普通应用。", request_real_actions=True)  # 新增代码+Phase99UniversalComputerUseModeGate：请求真实动作但不先打开 normal；如果没有这行代码，off 拒绝路径没有证据。
        acted_reports = [event["action_result"] for event in report["loop"]["events"] if event.get("state") == "acted"]  # 新增代码+Phase99UniversalComputerUseModeGate：提取动作报告；如果没有这行代码，无法确认没有假授权放行。
        self.assertTrue(report["mode_session_used"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言即使 off 也经过 mode session；如果没有这行代码，默认路径可能绕开 mode。
        self.assertFalse(report["authorized_recording_loop_ready"])  # 新增代码+Phase99UniversalComputerUseModeGate：断言没有打开 mode 时记录型闭环不就绪；如果没有这行代码，假授权会被误判为成功。
        self.assertEqual(report["low_level_event_count"], 0)  # 新增代码+Phase99UniversalComputerUseModeGate：断言 off 拒绝零低层事件；如果没有这行代码，未授权请求可能产生输入。
        self.assertTrue(any(action.get("decision") == "action_class_not_allowed_by_mode" for action in acted_reports))  # 新增代码+Phase99UniversalComputerUseModeGate：断言 off 状态不会用 per-app grant 假放行；如果没有这行代码，拒绝原因可能被旧授权掩盖。
    # 新增代码+Phase99UniversalComputerUseModeGate：函数段结束，test_live_gate_without_open_mode_refuses_real_actions_without_fake_grant 到此结束；如果没有这个边界说明，初学者不容易看出 off 拒绝范围。
# 新增代码+Phase99UniversalComputerUseModeGate：类段结束，WindowsComputerUseModeGatePhase99Tests 到此结束；如果没有这个边界说明，初学者不容易看出 Phase99 测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase99UniversalComputerUseModeGate：文件入口段开始，允许直接运行本测试文件；如果没有这行代码，小白用户必须记完整 unittest 命令。
    unittest.main()  # 新增代码+Phase99UniversalComputerUseModeGate：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
# 新增代码+Phase99UniversalComputerUseModeGate：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出脚本入口范围。
