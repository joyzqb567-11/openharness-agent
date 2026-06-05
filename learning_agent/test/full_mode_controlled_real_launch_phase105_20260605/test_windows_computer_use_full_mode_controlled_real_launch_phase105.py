import tempfile  # 新增代码+Phase105FullModeControlledRealLaunch：导入临时目录工具隔离测试产物；如果没有这行代码，测试会把 mode 状态和报告写进真实项目 memory。
import unittest  # 新增代码+Phase105FullModeControlledRealLaunch：导入项目现有 unittest 框架；如果没有这行代码，测试发现器无法执行本文件用例。
from pathlib import Path  # 新增代码+Phase105FullModeControlledRealLaunch：导入 Path 统一处理 Windows 路径；如果没有这行代码，受控文件路径拼接会更脆弱。

from learning_agent.computer_use.mode_session import ComputerUseModeSessionStore  # 新增代码+Phase105FullModeControlledRealLaunch：导入真实 mode store 复用 full token 确认流程；如果没有这行代码，测试可能绕过用户强确认设计。
from learning_agent.computer_use.universal_live_execution import PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_MARKER, PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_OK_TOKEN, UniversalWindowsLiveExecutionGate, phase105_cli_line, run_phase105_full_mode_controlled_real_launch_contract  # 新增代码+Phase105FullModeControlledRealLaunch：导入即将实现的 Phase105 full-mode 真实启动合同；如果没有这行代码，测试无法约束新能力入口。


class Phase105SpyLaunchCandidate:  # 新增代码+Phase105FullModeControlledRealLaunch：类段开始，定义测试专用受控启动候选；如果没有这个类，单元测试可能需要真的打开 Windows 应用。
    def __init__(self, touches_desktop: bool = False) -> None:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，初始化 spy 候选；如果没有这段函数，测试无法切换“假后端是否声称触碰桌面”。
        self.touches_desktop = bool(touches_desktop)  # 新增代码+Phase105FullModeControlledRealLaunch：保存假后端触桌面标记；如果没有这行代码，测试无法覆盖真实派发汇总字段。
        self.calls: list[dict[str, object]] = []  # 新增代码+Phase105FullModeControlledRealLaunch：记录 full gate 传给候选的参数；如果没有这行代码，无法证明 enable_real_launch 是否真的传到最后一跳。
    # 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，Phase105SpyLaunchCandidate.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch(self, app_name: str, enable_real_launch: bool | None = None, test_file: str | None = None) -> dict[str, object]:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，模拟受控 launcher 接收启动请求；如果没有这段函数，live gate 没有可调用的候选对象。
        call = {"app_name": app_name, "enable_real_launch": bool(enable_real_launch), "test_file": test_file}  # 新增代码+Phase105FullModeControlledRealLaunch：保存本次调用参数；如果没有这行代码，断言只能猜测 gate 是否放开真实启动。
        self.calls.append(call)  # 新增代码+Phase105FullModeControlledRealLaunch：记录调用事实；如果没有这行代码，默认关闭和启用路径无法区分。
        if not bool(enable_real_launch):  # 新增代码+Phase105FullModeControlledRealLaunch：模拟默认关闭路径；如果没有这行代码，测试无法证明 full 模式默认仍不真实启动。
            return {"ok": True, "decision": "real_app_launch_disabled_by_default", "controlled_launch_candidate_ready": True, "safe_start_process_plan": True, "real_app_launch_default_disabled": True, "backend_launch_reaches_launcher": False, "real_dispatch_performed": False, "real_desktop_touched": False, "low_level_event_count": 0, "unsafe_launch_zero_events": False, "uncontrolled_actions_expanded": False, "target_app": app_name}  # 新增代码+Phase105FullModeControlledRealLaunch：返回默认关闭零副作用报告；如果没有这行代码，测试无法锁定安全默认值。
        return {"ok": True, "decision": "controlled_app_launch_sent_to_backend", "controlled_launch_candidate_ready": True, "safe_start_process_plan": True, "real_app_launch_default_disabled": True, "backend_launch_reaches_launcher": True, "real_dispatch_performed": bool(self.touches_desktop), "real_desktop_touched": bool(self.touches_desktop), "low_level_event_count": 0, "unsafe_launch_zero_events": False, "uncontrolled_actions_expanded": False, "target_app": app_name, "test_file": test_file}  # 新增代码+Phase105FullModeControlledRealLaunch：返回显式启用后端桥接报告；如果没有这行代码，测试无法证明 Phase105 会把真实启动请求送到受控候选。
    # 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，Phase105SpyLaunchCandidate.launch 到此结束；如果没有这个边界说明，初学者不容易看出 spy 调用范围。
# 新增代码+Phase105FullModeControlledRealLaunch：类段结束，Phase105SpyLaunchCandidate 到此结束；如果没有这个边界说明，初学者不容易看出测试替身范围。


class WindowsComputerUseFullModeControlledRealLaunchPhase105Tests(unittest.TestCase):  # 新增代码+Phase105FullModeControlledRealLaunch：类段开始，集中验证 `/computer use --full` 受控真实启动接入；如果没有这个类，Phase105 的安全门和真实门没有回归保护。
    def _confirmed_full_store(self, root: Path) -> ComputerUseModeSessionStore:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，创建已确认 full mode store；如果没有这段函数，每个测试会重复 token 流程且容易漏掉强确认。
        store = ComputerUseModeSessionStore(base_dir=root / "mode_sessions")  # 新增代码+Phase105FullModeControlledRealLaunch：创建隔离 mode store；如果没有这行代码，测试会污染真实用户权限状态。
        request = store.request_full_mode(reason="Phase105 test requests full mode")  # 新增代码+Phase105FullModeControlledRealLaunch：按真实流程申请 full token；如果没有这行代码，测试会绕过 `/computer use --full` 高风险确认。
        confirmed = store.confirm_full_mode(request["confirmation_token"], reason="Phase105 test confirms full mode")  # 新增代码+Phase105FullModeControlledRealLaunch：用 token 确认 full；如果没有这行代码，launch_app 仍应被 mode gate 拦截。
        self.assertTrue(confirmed["full_mode"])  # 新增代码+Phase105FullModeControlledRealLaunch：断言 full 状态已生效；如果没有这行代码，后续断言可能建立在错误前置条件上。
        return store  # 新增代码+Phase105FullModeControlledRealLaunch：返回已确认 store；如果没有这行代码，live gate 无法读取 full 状态。
    # 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，_confirmed_full_store 到此结束；如果没有这个边界说明，初学者不容易看出 helper 范围。

    def _launch_report(self, report: dict[str, object]) -> dict[str, object]:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，从闭环报告中提取 launch_app 动作；如果没有这段函数，断言会被 observe/verify 事件干扰。
        events = dict(report.get("loop", {}) or {}).get("events", [])  # 新增代码+Phase105FullModeControlledRealLaunch：读取闭环事件列表；如果没有这行代码，测试无法定位动作阶段。
        launch_reports = [event.get("action_result", {}) for event in events if isinstance(event, dict) and event.get("state") == "acted" and dict(event.get("action_result", {}) or {}).get("action_class") == "launch_app"]  # 新增代码+Phase105FullModeControlledRealLaunch：筛出 launch_app 动作报告；如果没有这行代码，后续断言可能读到观察步骤。
        self.assertTrue(launch_reports)  # 新增代码+Phase105FullModeControlledRealLaunch：先确认存在启动动作报告；如果没有这行代码，下标错误会掩盖真正缺失。
        return dict(launch_reports[0])  # 新增代码+Phase105FullModeControlledRealLaunch：返回第一条启动报告副本；如果没有这行代码，调用方拿不到稳定断言对象。
    # 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，_launch_report 到此结束；如果没有这个边界说明，初学者不容易看出事件筛选范围。

    def test_full_mode_launch_stays_default_off_without_phase105_gate(self) -> None:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，验证 full 模式没有 Phase105 门时仍默认不真实启动；如果没有这段测试，`--full` 可能直接打开应用。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase105FullModeControlledRealLaunch：创建临时目录隔离报告；如果没有这行代码，测试会污染项目 memory。
            root = Path(temp_dir)  # 新增代码+Phase105FullModeControlledRealLaunch：保存临时根路径；如果没有这行代码，后续路径会重复拼接且容易写错。
            candidate = Phase105SpyLaunchCandidate(touches_desktop=True)  # 新增代码+Phase105FullModeControlledRealLaunch：创建会暴露越权的 spy 候选；如果没有这行代码，默认关闭路径即使越权也不容易被发现。
            runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "live_gate", mode_store=self._confirmed_full_store(root), controlled_launch_candidate=candidate)  # 新增代码+Phase105FullModeControlledRealLaunch：创建未开启 Phase105 真实门的 live gate；如果没有这行代码，测试没有被测执行入口。
            report = runtime.run_prompt("请使用 /computer use --full 启动 notepad，并保持受控。", request_real_actions=True)  # 新增代码+Phase105FullModeControlledRealLaunch：运行真实用户风格启动 prompt；如果没有这行代码，launch_app 路径不会被覆盖。
        launch_report = self._launch_report(report)  # 新增代码+Phase105FullModeControlledRealLaunch：提取启动动作报告；如果没有这行代码，后续断言无法定位受控启动结果。
        self.assertEqual(candidate.calls[0]["enable_real_launch"], False)  # 新增代码+Phase105FullModeControlledRealLaunch：断言默认没有把 enable_real_launch 传成真；如果没有这行代码，full 模式可能绕过 Phase105 门。
        self.assertFalse(launch_report["controlled_real_launch_gate_passed"])  # 新增代码+Phase105FullModeControlledRealLaunch：断言动作报告明确真实门未通过；如果没有这行代码，用户看不出默认关闭原因。
        self.assertTrue(report["controlled_real_launch_default_disabled"])  # 新增代码+Phase105FullModeControlledRealLaunch：断言总报告显示真实启动默认关闭；如果没有这行代码，终端验收无法确认安全默认值。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+Phase105FullModeControlledRealLaunch：断言真实桌面未触碰；如果没有这行代码，测试可能误开本地应用而不报警。
    # 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，test_full_mode_launch_stays_default_off_without_phase105_gate 到此结束；如果没有这个边界说明，初学者不容易看出默认关闭测试范围。

    def test_phase105_gate_passes_enable_real_launch_to_controlled_launcher(self) -> None:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，验证 Phase105 门会把真实启动请求送到受控候选；如果没有这段测试，功能可能只停留在报告层。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase105FullModeControlledRealLaunch：创建临时目录隔离报告；如果没有这行代码，测试会污染项目 memory。
            root = Path(temp_dir)  # 新增代码+Phase105FullModeControlledRealLaunch：保存临时根路径；如果没有这行代码，后续路径会重复拼接。
            controlled_file = root / "phase105-controlled-notepad.txt"  # 新增代码+Phase105FullModeControlledRealLaunch：准备受控文件路径；如果没有这行代码，真实路径无法证明只打开测试文件。
            candidate = Phase105SpyLaunchCandidate(touches_desktop=False)  # 新增代码+Phase105FullModeControlledRealLaunch：创建不触碰桌面的 spy 候选；如果没有这行代码，单元测试会变成真实桌面测试。
            runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "live_gate", mode_store=self._confirmed_full_store(root), controlled_launch_candidate=candidate, controlled_real_launch_enabled=True, controlled_launch_test_file=controlled_file)  # 新增代码+Phase105FullModeControlledRealLaunch：创建显式开启 Phase105 真实门的 live gate；如果没有这行代码，enable_real_launch 不会传到候选。
            report = runtime.run_prompt("请使用 /computer use --full 启动 notepad，并保持受控。", request_real_actions=True)  # 新增代码+Phase105FullModeControlledRealLaunch：运行真实用户风格启动 prompt；如果没有这行代码，受控真实启动路径不会执行。
        launch_report = self._launch_report(report)  # 新增代码+Phase105FullModeControlledRealLaunch：提取启动动作报告；如果没有这行代码，后续断言无法定位 Phase105 字段。
        self.assertEqual(candidate.calls[0]["enable_real_launch"], True)  # 新增代码+Phase105FullModeControlledRealLaunch：断言 Phase105 门把 enable_real_launch 传成真；如果没有这行代码，真实启动桥接可能没有发生。
        self.assertEqual(candidate.calls[0]["test_file"], str(controlled_file))  # 新增代码+Phase105FullModeControlledRealLaunch：断言只传入受控测试文件；如果没有这行代码，后续真实启动可能打开用户文件。
        self.assertTrue(launch_report["controlled_real_launch_gate_passed"])  # 新增代码+Phase105FullModeControlledRealLaunch：断言动作报告显示真实门已通过；如果没有这行代码，终端报告无法解释为什么进入后端。
        self.assertTrue(launch_report["backend_launch_reaches_launcher"])  # 新增代码+Phase105FullModeControlledRealLaunch：断言受控候选最后一跳被调用；如果没有这行代码，Phase105 可能只改了状态字段。
        self.assertTrue(report["full_mode_controlled_real_launch_ready"])  # 新增代码+Phase105FullModeControlledRealLaunch：断言总报告显示 full-mode 受控真实启动就绪；如果没有这行代码，CLI 合同无法确认接入完成。
        self.assertEqual(report["real_action_decision"], "authorized_controlled_real_launch")  # 新增代码+Phase105FullModeControlledRealLaunch：断言执行结论不再伪装成 recording-only；如果没有这行代码，真实启动能力会和旧合同混淆。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+Phase105FullModeControlledRealLaunch：断言单元测试仍未触碰真实桌面；如果没有这行代码，开发机可能被测试误操作。
    # 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，test_phase105_gate_passes_enable_real_launch_to_controlled_launcher 到此结束；如果没有这个边界说明，初学者不容易看出正向桥接测试范围。

    def test_phase105_contract_cli_tokens_are_stable_in_default_safe_mode(self) -> None:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，验证 Phase105 默认安全合同 token 稳定；如果没有这段测试，真实终端验收容易因输出漂移失败。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase105FullModeControlledRealLaunch：创建临时目录隔离合同报告；如果没有这行代码，测试会污染真实 memory。
            report = run_phase105_full_mode_controlled_real_launch_contract(base_dir=Path(temp_dir), real_launch=False, allow_real_gate=False)  # 新增代码+Phase105FullModeControlledRealLaunch：运行默认安全合同；如果没有这行代码，CLI token 没有事实来源。
        line = phase105_cli_line(report)  # 新增代码+Phase105FullModeControlledRealLaunch：把报告转成终端 token 行；如果没有这行代码，场景无法复用同一格式。
        self.assertTrue(report["passed"])  # 新增代码+Phase105FullModeControlledRealLaunch：断言默认安全合同通过；如果没有这行代码，失败合同也可能输出固定字段。
        self.assertIn(PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_MARKER, line)  # 新增代码+Phase105FullModeControlledRealLaunch：断言 ready marker 存在；如果没有这行代码，可见终端没有稳定锚点。
        self.assertIn(PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_OK_TOKEN, line)  # 新增代码+Phase105FullModeControlledRealLaunch：断言 OK token 存在；如果没有这行代码，验收器无法区分成功与普通日志。
        self.assertIn("default_off_zero_events=true", line)  # 新增代码+Phase105FullModeControlledRealLaunch：断言默认关闭零副作用 token 存在；如果没有这行代码，安全默认值不可验收。
        self.assertIn("full_gate_passes_enable_real_launch=true", line)  # 新增代码+Phase105FullModeControlledRealLaunch：断言 full gate 能传递 enable_real_launch；如果没有这行代码，Phase105 可能没有接上最后一跳。
        self.assertIn("real_enable_gate_required=true", line)  # 新增代码+Phase105FullModeControlledRealLaunch：断言真实启动仍需要额外门；如果没有这行代码，用户可能误以为 full 模式等于无限放开。
        self.assertIn("real_full_launch_attempted=false", line)  # 新增代码+Phase105FullModeControlledRealLaunch：断言默认合同不真实打开应用；如果没有这行代码，单元验收可能误触桌面。
        self.assertIn("real_desktop_touched=false", line)  # 新增代码+Phase105FullModeControlledRealLaunch：断言默认合同未触碰桌面；如果没有这行代码，安全边界不可见。
        self.assertIn("uncontrolled_actions_expanded=false", line)  # 新增代码+Phase105FullModeControlledRealLaunch：断言没有扩张无边界动作面；如果没有这行代码，full 模式可能被误读为任意执行。
    # 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，test_phase105_contract_cli_tokens_are_stable_in_default_safe_mode 到此结束；如果没有这个边界说明，初学者不容易看出 CLI token 测试范围。
# 新增代码+Phase105FullModeControlledRealLaunch：类段结束，WindowsComputerUseFullModeControlledRealLaunchPhase105Tests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase105FullModeControlledRealLaunch：文件入口段开始，允许直接运行本测试文件；如果没有这行代码，初学者必须记完整 unittest 命令。
    unittest.main()  # 新增代码+Phase105FullModeControlledRealLaunch：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
# 新增代码+Phase105FullModeControlledRealLaunch：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出脚本入口范围。
