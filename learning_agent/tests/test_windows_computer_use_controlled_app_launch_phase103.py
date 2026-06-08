import tempfile  # 新增代码+Phase103ControlledAppLaunch：导入临时目录工具隔离 Phase103 报告和 mode 状态；如果没有这行代码，测试会污染真实项目 memory。
import unittest  # 新增代码+Phase103ControlledAppLaunch：导入项目现有 unittest 测试框架；如果没有这行代码，标准测试发现器找不到这些用例。
from pathlib import Path  # 新增代码+Phase103ControlledAppLaunch：导入 Path 统一处理 Windows 路径；如果没有这行代码，临时目录路径拼接会更脆弱。

from learning_agent.computer_use.generic_launch_backend import PHASE103_CONTROLLED_APP_LAUNCH_MARKER, PHASE103_CONTROLLED_APP_LAUNCH_OK_TOKEN, Phase103RecordingLaunchBackend, WindowsControlledAppLaunchCandidate, phase103_cli_line, run_phase103_controlled_app_launch_contract  # 新增代码+Phase103ControlledAppLaunch：导入 Phase103 受控应用启动候选接口；如果没有这行代码，测试无法证明 full 模式 launch_app 进入受控后端前的安全门。
from learning_agent.computer_use.mode_session import ComputerUseModeSessionStore  # 新增代码+Phase103ControlledAppLaunch：导入 mode store 用真实 token 流程确认 full 模式；如果没有这行代码，测试可能绕过用户二次确认设计。
from learning_agent.computer_use.universal_live_execution import UniversalWindowsLiveExecutionGate  # 新增代码+Phase103ControlledAppLaunch：导入通用 live execution gate；如果没有这行代码，Phase103 只能测试底层模块而不能证明 full gate 已接入。


class Phase103FakeLaunchBackend:  # 新增代码+Phase103ControlledAppLaunch：类段开始，提供测试专用后端；如果没有这个类，单元测试可能需要真的打开 Windows 应用。
    def __init__(self) -> None:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，初始化后端调用记录；如果没有这段函数，测试无法确认默认关闭时没有调用后端。
        self.calls: list[dict[str, object]] = []  # 新增代码+Phase103ControlledAppLaunch：保存每次收到的启动计划副本；如果没有这行代码，后端是否被调用不可验证。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，Phase103FakeLaunchBackend.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch(self, plan: dict[str, object]) -> dict[str, object]:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，模拟受控后端收到启动计划；如果没有这段函数，正向桥接路径没有安全替身。
        safe_plan = dict(plan)  # 新增代码+Phase103ControlledAppLaunch：复制计划避免调用方后续修改污染测试证据；如果没有这行代码，断言可能被外部对象变化影响。
        self.calls.append(safe_plan)  # 新增代码+Phase103ControlledAppLaunch：记录一次后端调用；如果没有这行代码，测试无法证明显式开启时确实到达后端。
        return {"ok": True, "backend": "phase103_fake_launch_backend", "backend_launch_performed": True, "process_started": True, "process_id": 10301, "real_desktop_touched": False, "cleanup_registered": True, "low_level_event_count": 0}  # 新增代码+Phase103ControlledAppLaunch：返回模拟成功但不触碰真实桌面的结果；如果没有这行代码，测试会误以为必须真实启动应用才算通过。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，Phase103FakeLaunchBackend.launch 到此结束；如果没有这个边界说明，初学者不容易看出后端替身范围。
# 新增代码+Phase103ControlledAppLaunch：类段结束，Phase103FakeLaunchBackend 到此结束；如果没有这个边界说明，初学者不容易看出测试后端范围。


class WindowsComputerUseControlledAppLaunchPhase103Tests(unittest.TestCase):  # 新增代码+Phase103ControlledAppLaunch：类段开始，集中验证 Phase103 受控应用启动候选；如果没有这个类，full 模式 launch_app 真实启动候选能力没有回归保护。
    def _confirmed_full_store(self, root: Path) -> ComputerUseModeSessionStore:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，创建并确认 full mode store；如果没有这段函数，每个测试都要重复 token 流程且容易漏确认。
        store = ComputerUseModeSessionStore(base_dir=root / "mode_sessions")  # 新增代码+Phase103ControlledAppLaunch：创建隔离 mode store；如果没有这行代码，full 状态会写进真实项目 memory。
        request = store.request_full_mode(reason="Phase103 test requests full mode")  # 新增代码+Phase103ControlledAppLaunch：按真实流程申请 full token；如果没有这行代码，测试会绕开用户显式授权设计。
        confirmed = store.confirm_full_mode(request["confirmation_token"], reason="Phase103 test confirms full mode")  # 新增代码+Phase103ControlledAppLaunch：用 token 确认 full 模式；如果没有这行代码，后续 launch_app 应该仍被 mode gate 拦截。
        self.assertTrue(confirmed["full_mode"])  # 新增代码+Phase103ControlledAppLaunch：断言 full 状态确实生效；如果没有这行代码，后续正向测试可能在错误前置条件下运行。
        return store  # 新增代码+Phase103ControlledAppLaunch：返回已确认的 store 给调用方；如果没有这行代码，测试无法把 full 状态注入 live gate。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，_confirmed_full_store 到此结束；如果没有这个边界说明，初学者不容易看出 helper 范围。

    def test_default_off_records_safe_launch_candidate_without_backend_call(self) -> None:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，验证默认关闭不会触碰真实桌面或后端；如果没有这段测试，安全默认值可能被后续改坏。
        backend = Phase103FakeLaunchBackend()  # 新增代码+Phase103ControlledAppLaunch：创建测试后端；如果没有这行代码，无法证明默认关闭时后端调用数为零。
        runtime = WindowsControlledAppLaunchCandidate(launch_backend=backend)  # 新增代码+Phase103ControlledAppLaunch：创建受控启动候选运行时；如果没有这行代码，测试没有被测对象。
        result = runtime.launch("notepad", enable_real_launch=False)  # 新增代码+Phase103ControlledAppLaunch：执行默认关闭路径；如果没有这行代码，零副作用设计没有事实证据。
        self.assertTrue(result["ok"])  # 新增代码+Phase103ControlledAppLaunch：断言默认关闭仍然是安全可记录成功；如果没有这行代码，调用方无法区分安全预览和失败。
        self.assertEqual(result["decision"], "real_app_launch_disabled_by_default")  # 新增代码+Phase103ControlledAppLaunch：断言决策明确说明默认不真实启动；如果没有这行代码，用户会误读为已经打开应用。
        self.assertTrue(result["controlled_launch_candidate_ready"])  # 新增代码+Phase103ControlledAppLaunch：断言受控候选能力已就绪；如果没有这行代码，Phase103 可能只是沿用 Phase102 记录型假动作。
        self.assertTrue(result["safe_start_process_plan"])  # 新增代码+Phase103ControlledAppLaunch：断言 notepad 被转成安全启动计划；如果没有这行代码，后端可能收到未经审计的命令。
        self.assertTrue(result["real_app_launch_default_disabled"])  # 新增代码+Phase103ControlledAppLaunch：断言真实启动默认关闭字段存在；如果没有这行代码，验收报告无法看出安全默认值。
        self.assertFalse(result["backend_launch_reaches_launcher"])  # 新增代码+Phase103ControlledAppLaunch：断言默认关闭不会调用后端；如果没有这行代码，测试可能漏掉真实启动风险。
        self.assertFalse(result["real_desktop_touched"])  # 新增代码+Phase103ControlledAppLaunch：断言没有触碰真实桌面；如果没有这行代码，自动化测试可能误开本地应用。
        self.assertEqual(result["low_level_event_count"], 0)  # 新增代码+Phase103ControlledAppLaunch：断言没有低层鼠标键盘事件；如果没有这行代码，启动候选可能误混输入派发。
        self.assertEqual(backend.calls, [])  # 新增代码+Phase103ControlledAppLaunch：断言后端调用列表为空；如果没有这行代码，默认关闭可能实际已经越过最后一跳。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，test_default_off_records_safe_launch_candidate_without_backend_call 到此结束；如果没有这个边界说明，初学者不容易看出默认关闭测试范围。

    def test_explicit_enabled_safe_plan_reaches_injected_backend(self) -> None:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，验证显式开启会把安全计划送到注入后端；如果没有这段测试，Phase103 可能只停留在 recording-only。
        backend = Phase103FakeLaunchBackend()  # 新增代码+Phase103ControlledAppLaunch：创建测试后端；如果没有这行代码，无法安全观察最后一跳调用。
        runtime = WindowsControlledAppLaunchCandidate(launch_backend=backend)  # 新增代码+Phase103ControlledAppLaunch：创建受控启动候选运行时；如果没有这行代码，正向桥接路径没有主体。
        result = runtime.launch("notepad", enable_real_launch=True)  # 新增代码+Phase103ControlledAppLaunch：显式启用受控启动；如果没有这行代码，后端正向路径没有证据。
        self.assertTrue(result["ok"])  # 新增代码+Phase103ControlledAppLaunch：断言显式启用的安全计划成功；如果没有这行代码，后端桥接失败可能被忽略。
        self.assertEqual(result["decision"], "controlled_app_launch_sent_to_backend")  # 新增代码+Phase103ControlledAppLaunch：断言决策说明已送到受控后端；如果没有这行代码，Phase103 与默认关闭路径不可区分。
        self.assertTrue(result["backend_launch_reaches_launcher"])  # 新增代码+Phase103ControlledAppLaunch：断言最后一跳后端被调用；如果没有这行代码，能力可能仍停在报告层。
        self.assertEqual(len(backend.calls), 1)  # 新增代码+Phase103ControlledAppLaunch：断言后端只收到一次调用；如果没有这行代码，重复启动风险不可见。
        self.assertEqual(backend.calls[0]["executable"], "notepad.exe")  # 新增代码+Phase103ControlledAppLaunch：断言后端收到的是安全别名解析后的 exe；如果没有这行代码，用户输入可能直接变成命令。
        self.assertEqual(result["backend_result"]["backend"], "phase103_fake_launch_backend")  # 新增代码+Phase103ControlledAppLaunch：断言结果来自注入假后端；如果没有这行代码，测试可能误用真实后端。
        self.assertFalse(result["real_desktop_touched"])  # 新增代码+Phase103ControlledAppLaunch：断言测试后端不触碰真实桌面；如果没有这行代码，单元测试可能变成危险验收。
        self.assertFalse(result["uncontrolled_actions_expanded"])  # 新增代码+Phase103ControlledAppLaunch：断言没有扩张无边界动作面；如果没有这行代码，full 模式可能被误读成任意命令执行。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，test_explicit_enabled_safe_plan_reaches_injected_backend 到此结束；如果没有这个边界说明，初学者不容易看出正向桥接测试范围。

    def test_unsafe_launch_plan_is_refused_before_backend(self) -> None:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，验证危险应用在后端前被拒绝；如果没有这段测试，powershell 等高风险目标可能进入启动后端。
        backend = Phase103FakeLaunchBackend()  # 新增代码+Phase103ControlledAppLaunch：创建测试后端；如果没有这行代码，无法证明拒绝路径没有后端调用。
        runtime = WindowsControlledAppLaunchCandidate(launch_backend=backend)  # 新增代码+Phase103ControlledAppLaunch：创建受控启动候选运行时；如果没有这行代码，危险拒绝没有被测对象。
        result = runtime.launch("powershell", enable_real_launch=True)  # 新增代码+Phase103ControlledAppLaunch：尝试启动高风险 powershell；如果没有这行代码，危险目标零事件没有样本。
        self.assertFalse(result["ok"])  # 新增代码+Phase103ControlledAppLaunch：断言危险计划失败；如果没有这行代码，高风险误放行不容易被发现。
        self.assertEqual(result["decision"], "unsafe_launch_plan_rejected")  # 新增代码+Phase103ControlledAppLaunch：断言拒绝原因是 unsafe launch plan；如果没有这行代码，失败可能来自偶然后端错误。
        self.assertTrue(result["unsafe_launch_zero_events"])  # 新增代码+Phase103ControlledAppLaunch：断言危险计划零事件；如果没有这行代码，拒绝也可能已经触碰桌面。
        self.assertFalse(result["backend_launch_reaches_launcher"])  # 新增代码+Phase103ControlledAppLaunch：断言危险计划没有到达后端；如果没有这行代码，后端可能收到不该启动的目标。
        self.assertFalse(result["real_desktop_touched"])  # 新增代码+Phase103ControlledAppLaunch：断言没有触碰真实桌面；如果没有这行代码，危险测试可能有副作用。
        self.assertEqual(backend.calls, [])  # 新增代码+Phase103ControlledAppLaunch：断言后端调用为空；如果没有这行代码，拒绝路径最后一跳不可审计。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，test_unsafe_launch_plan_is_refused_before_backend 到此结束；如果没有这个边界说明，初学者不容易看出危险拒绝测试范围。

    def test_universal_full_launch_uses_controlled_candidate_default_off(self) -> None:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，验证 full gate 的 launch_app 接入受控启动候选；如果没有这段测试，Phase103 底层能力可能没有接到真实入口。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase103ControlledAppLaunch：创建临时目录隔离报告；如果没有这行代码，测试会污染真实 memory。
            root = Path(temp_dir)  # 新增代码+Phase103ControlledAppLaunch：保存临时根目录；如果没有这行代码，后续路径会重复构造且容易写错。
            backend = Phase103FakeLaunchBackend()  # 新增代码+Phase103ControlledAppLaunch：创建测试后端；如果没有这行代码，无法证明 full gate 默认不调用真实启动后端。
            candidate = WindowsControlledAppLaunchCandidate(launch_backend=backend)  # 新增代码+Phase103ControlledAppLaunch：创建注入给 full gate 的受控启动候选；如果没有这行代码，gate 只能沿用 Phase102 recording-only。
            mode_store = self._confirmed_full_store(root)  # 新增代码+Phase103ControlledAppLaunch：获取已确认 full store；如果没有这行代码，launch_app 会被 normal/off mode 拦截。
            runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "live_gate", mode_store=mode_store, controlled_launch_candidate=candidate)  # 新增代码+Phase103ControlledAppLaunch：创建接入受控候选的 live gate；如果没有这行代码，测试无法覆盖 Phase103 与 Phase102 的连接点。
            report = runtime.run_prompt("请使用 full 模式启动 notepad，只做受控启动候选合同，不要真实打开。", request_real_actions=True)  # 新增代码+Phase103ControlledAppLaunch：运行真实用户风格 full 启动 prompt；如果没有这行代码，full gate 入口没有验收事实。
        launch_reports = [event["action_result"] for event in report["loop"]["events"] if event.get("state") == "acted" and event.get("action_result", {}).get("action_class") == "launch_app"]  # 新增代码+Phase103ControlledAppLaunch：提取 launch_app 动作报告；如果没有这行代码，断言会被 observe/verify 干扰。
        self.assertTrue(report["full_mode_session_used"])  # 新增代码+Phase103ControlledAppLaunch：断言 full 状态被 live gate 看见；如果没有这行代码，受控候选可能在错误模式下运行。
        self.assertTrue(report["full_mode_action_ready"])  # 新增代码+Phase103ControlledAppLaunch：断言 full 专属动作已就绪；如果没有这行代码，Phase103 可能没有经过 mode gate。
        self.assertTrue(launch_reports)  # 新增代码+Phase103ControlledAppLaunch：断言存在 launch_app 报告；如果没有这行代码，后续下标读取会变成难懂异常。
        self.assertTrue(launch_reports[0]["controlled_launch_candidate_ready"])  # 新增代码+Phase103ControlledAppLaunch：断言动作层接入 Phase103 候选；如果没有这行代码，full gate 可能仍是 Phase102 假记录。
        self.assertEqual(launch_reports[0]["controlled_launch_result"]["decision"], "real_app_launch_disabled_by_default")  # 新增代码+Phase103ControlledAppLaunch：断言 full gate 默认仍不真实启动；如果没有这行代码，单元测试可能打开本机应用。
        self.assertFalse(launch_reports[0]["controlled_launch_result"]["backend_launch_reaches_launcher"])  # 新增代码+Phase103ControlledAppLaunch：断言默认关闭未到达后端；如果没有这行代码，full 模式可能越过最后一跳。
        self.assertFalse(report["real_dispatch_performed"])  # 新增代码+Phase103ControlledAppLaunch：断言总报告没有真实派发；如果没有这行代码，用户可能误以为已经安全验证零副作用。
        self.assertFalse(report["real_desktop_touched"])  # 新增代码+Phase103ControlledAppLaunch：断言真实桌面未被触碰；如果没有这行代码，验收可能误放真实窗口启动。
        self.assertEqual(backend.calls, [])  # 新增代码+Phase103ControlledAppLaunch：断言默认关闭没有调用后端；如果没有这行代码，full gate 默认安全性不可量化。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，test_universal_full_launch_uses_controlled_candidate_default_off 到此结束；如果没有这个边界说明，初学者不容易看出 full gate 接入测试范围。

    def test_phase103_contract_cli_tokens_are_stable(self) -> None:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，验证合同报告和 CLI token 稳定；如果没有这段测试，真实终端验收容易因输出漂移失败。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase103ControlledAppLaunch：创建临时目录隔离合同产物；如果没有这行代码，报告会污染真实 memory。
            report = run_phase103_controlled_app_launch_contract(base_dir=Path(temp_dir))  # 新增代码+Phase103ControlledAppLaunch：运行 Phase103 合同；如果没有这行代码，CLI token 没有事实来源。
        line = phase103_cli_line(report)  # 新增代码+Phase103ControlledAppLaunch：把报告转成单行 token；如果没有这行代码，场景匹配无法复用同一格式。
        self.assertTrue(report["passed"])  # 新增代码+Phase103ControlledAppLaunch：断言合同通过；如果没有这行代码，失败合同可能仍输出 token。
        self.assertIn(PHASE103_CONTROLLED_APP_LAUNCH_MARKER, line)  # 新增代码+Phase103ControlledAppLaunch：断言 ready marker 存在；如果没有这行代码，可见终端验收没有等待锚点。
        self.assertIn(PHASE103_CONTROLLED_APP_LAUNCH_OK_TOKEN, line)  # 新增代码+Phase103ControlledAppLaunch：断言 OK token 存在；如果没有这行代码，验收器无法区分成功和普通日志。
        self.assertIn("controlled_launch_candidate_ready=true", line)  # 新增代码+Phase103ControlledAppLaunch：断言受控候选就绪 token 存在；如果没有这行代码，Phase103 核心能力无法被终端匹配。
        self.assertIn("real_app_launch_default_disabled=true", line)  # 新增代码+Phase103ControlledAppLaunch：断言默认关闭 token 存在；如果没有这行代码，用户无法确认安全默认值。
        self.assertIn("enabled_backend_reaches_launcher=true", line)  # 新增代码+Phase103ControlledAppLaunch：断言显式启用后端桥接 token 存在；如果没有这行代码，Phase103 可能没有推进到最后一跳候选。
        self.assertIn("unsafe_launch_zero_events=true", line)  # 新增代码+Phase103ControlledAppLaunch：断言危险启动零事件 token 存在；如果没有这行代码，高风险拒绝不可验收。
        self.assertIn("universal_full_gate_uses_controlled_launcher=true", line)  # 新增代码+Phase103ControlledAppLaunch：断言 full gate 接入 token 存在；如果没有这行代码，底层能力可能没有接入真实入口。
        self.assertIn("real_desktop_touched=false", line)  # 新增代码+Phase103ControlledAppLaunch：断言真实桌面未触碰 token 存在；如果没有这行代码，安全边界无法被场景验证。
        self.assertIn("uncontrolled_actions_expanded=false", line)  # 新增代码+Phase103ControlledAppLaunch：断言未扩大无边界动作面 token 存在；如果没有这行代码，full 模式可能被误读成无限制。
        self.assertIsInstance(Phase103RecordingLaunchBackend().launch({"safe_to_launch": True, "executable": "notepad.exe", "arguments": []}), dict)  # 新增代码+Phase103ControlledAppLaunch：断言内置记录后端可调用；如果没有这行代码，默认安全替身可能缺失。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，test_phase103_contract_cli_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出合同 token 测试范围。
# 新增代码+Phase103ControlledAppLaunch：类段结束，WindowsComputerUseControlledAppLaunchPhase103Tests 到此结束；如果没有这个边界说明，初学者不容易看出 Phase103 测试集合范围。


if __name__ == "__main__":  # 新增代码+Phase103ControlledAppLaunch：文件入口段开始，允许直接运行本测试文件；如果没有这行代码，小白用户必须记完整 unittest 命令。
    unittest.main()  # 新增代码+Phase103ControlledAppLaunch：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
# 新增代码+Phase103ControlledAppLaunch：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出脚本入口范围。
