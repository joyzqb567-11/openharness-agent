import json  # 新增代码+Phase47WindowsSendInputDispatcher: 导入 JSON 用于检查调度结果是否泄露原始文本；如果没有这行代码，raw text hidden 无法被机器验证。
import unittest  # 新增代码+Phase47WindowsSendInputDispatcher: 导入 unittest 框架承载 Phase47 测试；如果没有这行代码，自动化回归不会运行本阶段验收。
from pathlib import Path  # 新增代码+Phase47WindowsSendInputDispatcher: 导入 Path 稳定定位场景文件；如果没有这行代码，Windows 路径拼接会更脆。

from learning_agent.computer_use.native_host import InProcessWindowsNativeHostClient, WindowsComputerUseNativeHost  # 新增代码+Phase47WindowsSendInputDispatcher: 导入 native host 验证 action 路由；如果没有这行代码，dispatcher 只停留在孤立模块。
from learning_agent.computer_use.sendinput_dispatcher import PHASE47_WINDOWS_SENDINPUT_DISPATCHER_MARKER, PHASE47_WINDOWS_SENDINPUT_DISPATCHER_OK_TOKEN, Phase47RecordingLowLevelSender, WindowsSendInputDispatcher, phase47_cli_line, run_phase47_sendinput_dispatcher_contract  # 新增代码+Phase47WindowsSendInputDispatcher: 导入 Phase47 期望的新 dispatcher；如果没有这行代码，红灯会证明真实调度层尚未实现。
from learning_agent.computer_use.sendinput_executor import WindowsSendInputExecutor  # 新增代码+Phase47WindowsSendInputDispatcher: 复用 Phase37 executor 生成规范事件；如果没有这行代码，Phase47 无法证明与现有动作层兼容。


class Phase47TargetVerifier:  # 新增代码+Phase47WindowsSendInputDispatcher: 定义可控目标校验器；如果没有这个类，测试无法证明动作前目标未变化检查。
    def __init__(self, ok: bool = True) -> None:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，保存校验结果；如果没有这段函数，测试不能切换通过/失败路径。
        self.ok = ok  # 新增代码+Phase47WindowsSendInputDispatcher: 保存是否允许发送；如果没有这行代码，校验器无法模拟窗口变化。
        self.calls = 0  # 新增代码+Phase47WindowsSendInputDispatcher: 记录校验调用次数；如果没有这行代码，测试无法证明发送前真的校验。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，Phase47TargetVerifier.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def __call__(self) -> dict[str, object]:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，执行一次目标校验；如果没有这段函数，dispatcher 无法调用校验器。
        self.calls += 1  # 新增代码+Phase47WindowsSendInputDispatcher: 递增调用次数；如果没有这行代码，测试看不出校验是否发生。
        return {"ok": self.ok, "reason": "target stable" if self.ok else "target window changed"}  # 新增代码+Phase47WindowsSendInputDispatcher: 返回结构化校验结果；如果没有这行代码，dispatcher 无法判断是否继续发送。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，Phase47TargetVerifier.__call__ 到此结束；如果没有这个边界说明，读者不容易看出校验范围。


class WindowsComputerUseSendInputDispatcherPhase47Tests(unittest.TestCase):  # 新增代码+Phase47WindowsSendInputDispatcher: 定义 Phase47 测试集合；如果没有这个类，unittest 不会组织 SendInput dispatcher 测试。
    def _executor(self, verifier: Phase47TargetVerifier, sender: Phase47RecordingLowLevelSender) -> WindowsSendInputExecutor:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，创建接入 dispatcher 的 executor；如果没有这段函数，每个测试都要重复搭建链路。
        dispatcher = WindowsSendInputDispatcher(platform="win32", enabled=True, low_level_sender=sender, target_verifier=verifier)  # 新增代码+Phase47WindowsSendInputDispatcher: 创建启用且注入 fake sender 的 dispatcher；如果没有这行代码，测试会触碰真实桌面或无法执行。
        return WindowsSendInputExecutor(platform="win32", enabled=True, sendinput_impl=dispatcher)  # 新增代码+Phase47WindowsSendInputDispatcher: 把 dispatcher 作为 Phase37 executor 的实现；如果没有这行代码，Phase47 无法证明兼容旧执行入口。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，_executor 到此结束；如果没有这个边界说明，读者不容易看出链路搭建范围。

    def test_dispatcher_expands_supported_actions_and_redacts_text(self) -> None:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，验证 dispatcher 展开所有关键动作且不泄露文本；如果没有这个测试，Phase47 可能只支持部分动作。
        verifier = Phase47TargetVerifier(ok=True)  # 新增代码+Phase47WindowsSendInputDispatcher: 创建通过的目标校验器；如果没有这行代码，dispatcher 会缺少目标稳定证据。
        sender = Phase47RecordingLowLevelSender()  # 新增代码+Phase47WindowsSendInputDispatcher: 创建记录型低层 sender；如果没有这行代码，测试无法检查低层事件。
        executor = self._executor(verifier, sender)  # 新增代码+Phase47WindowsSendInputDispatcher: 创建 executor-dispatcher 链路；如果没有这行代码，动作无法进入 dispatcher。
        self.assertTrue(executor.execute("move_mouse", {"x": 10, "y": 20}).ok)  # 新增代码+Phase47WindowsSendInputDispatcher: 验证鼠标移动可调度；如果没有这行代码，move 动作可能缺失。
        self.assertTrue(executor.execute("click", {"x": 10, "y": 20}).ok)  # 新增代码+Phase47WindowsSendInputDispatcher: 验证单击可调度；如果没有这行代码，click 动作可能缺失。
        self.assertTrue(executor.execute("double_click", {"x": 10, "y": 20}).ok)  # 新增代码+Phase47WindowsSendInputDispatcher: 验证双击可调度；如果没有这行代码，double_click 动作可能缺失。
        self.assertTrue(executor.execute("scroll", {"x": 10, "y": 20, "delta": -120}).ok)  # 新增代码+Phase47WindowsSendInputDispatcher: 验证滚轮可调度；如果没有这行代码，scroll 动作可能缺失。
        self.assertTrue(executor.execute("press_key", {"key": "ENTER"}).ok)  # 新增代码+Phase47WindowsSendInputDispatcher: 验证按键可调度；如果没有这行代码，press_key 动作可能缺失。
        text_result = executor.execute("type_text", {"text": "phase47-secret"})  # 新增代码+Phase47WindowsSendInputDispatcher: 执行文本输入动作；如果没有这行代码，文本脱敏路径不会被覆盖。
        serialized = json.dumps({"result": text_result.data, "events": sender.low_level_events}, ensure_ascii=False).lower()  # 新增代码+Phase47WindowsSendInputDispatcher: 序列化可见结果做泄露检查；如果没有这行代码，低层事件泄露原文不易发现。
        low_level_types = {event["type"] for event in sender.low_level_events}  # 新增代码+Phase47WindowsSendInputDispatcher: 收集低层事件类型；如果没有这行代码，测试无法确认动作展开结果。
        self.assertIn("mouse_move", low_level_types)  # 新增代码+Phase47WindowsSendInputDispatcher: 断言鼠标移动事件存在；如果没有这行代码，坐标移动可能没有展开。
        self.assertIn("mouse_down", low_level_types)  # 新增代码+Phase47WindowsSendInputDispatcher: 断言鼠标按下事件存在；如果没有这行代码，点击可能只有移动没有按键。
        self.assertIn("mouse_up", low_level_types)  # 新增代码+Phase47WindowsSendInputDispatcher: 断言鼠标抬起事件存在；如果没有这行代码，点击可能无法完成。
        self.assertIn("mouse_wheel", low_level_types)  # 新增代码+Phase47WindowsSendInputDispatcher: 断言滚轮事件存在；如果没有这行代码，scroll 没有真实低层含义。
        self.assertIn("key_down", low_level_types)  # 新增代码+Phase47WindowsSendInputDispatcher: 断言按键按下事件存在；如果没有这行代码，press_key 没有真实低层含义。
        self.assertIn("unicode_text", low_level_types)  # 新增代码+Phase47WindowsSendInputDispatcher: 断言文本事件以脱敏 unicode_text 摘要存在；如果没有这行代码，type_text 可能未被展开。
        self.assertGreaterEqual(verifier.calls, 6)  # 新增代码+Phase47WindowsSendInputDispatcher: 断言每次发送前都会校验目标；如果没有这行代码，目标变化检查可能没执行。
        self.assertNotIn("phase47-secret", serialized)  # 新增代码+Phase47WindowsSendInputDispatcher: 断言原始文本没有进入可见结果；如果没有这行代码，密码/token 可能泄露。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，test_dispatcher_expands_supported_actions_and_redacts_text 到此结束；如果没有这个边界说明，读者不容易看出动作展开测试范围。

    def test_dispatcher_refuses_when_target_changed_before_send(self) -> None:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，验证目标变化时拒绝发送；如果没有这个测试，动作可能发到错误窗口。
        verifier = Phase47TargetVerifier(ok=False)  # 新增代码+Phase47WindowsSendInputDispatcher: 创建失败的目标校验器；如果没有这行代码，拒绝路径无法触发。
        sender = Phase47RecordingLowLevelSender()  # 新增代码+Phase47WindowsSendInputDispatcher: 创建记录型低层 sender；如果没有这行代码，无法确认没有发送事件。
        executor = self._executor(verifier, sender)  # 新增代码+Phase47WindowsSendInputDispatcher: 创建 executor-dispatcher 链路；如果没有这行代码，无法执行动作。
        result = executor.execute("click", {"x": 10, "y": 20})  # 新增代码+Phase47WindowsSendInputDispatcher: 尝试点击触发目标校验失败；如果没有这行代码，拒绝路径没有输入。
        self.assertFalse(result.ok)  # 新增代码+Phase47WindowsSendInputDispatcher: 断言动作被拒绝；如果没有这行代码，目标变化可能仍然成功。
        self.assertEqual(sender.low_level_events, [])  # 新增代码+Phase47WindowsSendInputDispatcher: 断言没有低层事件被发送；如果没有这行代码，表面拒绝可能仍有副作用。
        self.assertEqual(result.data["dispatch"]["decision"], "target_changed_before_send")  # 修改代码+Phase47WindowsSendInputDispatcher: 断言拒绝原因稳定保留在 dispatch 摘要里；如果没有这行代码，测试会误读 Phase37 executor 的既有结果结构。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，test_dispatcher_refuses_when_target_changed_before_send 到此结束；如果没有这个边界说明，读者不容易看出目标校验测试范围。

    def test_native_host_action_can_use_enabled_dispatcher_without_raw_text(self) -> None:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，验证 native host action 可接入 dispatcher；如果没有这个测试，Phase47 与 native host 可能割裂。
        sender = Phase47RecordingLowLevelSender()  # 新增代码+Phase47WindowsSendInputDispatcher: 创建记录型低层 sender；如果没有这行代码，host 测试可能触碰真实桌面。
        executor = self._executor(Phase47TargetVerifier(ok=True), sender)  # 新增代码+Phase47WindowsSendInputDispatcher: 创建安全 executor-dispatcher 链路；如果没有这行代码，host 没有动作执行入口。
        host = WindowsComputerUseNativeHost(platform="win32", real_actions_enabled=True, action_executor=executor)  # 新增代码+Phase47WindowsSendInputDispatcher: 注入动作 executor 到 native host；如果没有这行代码，action 消息仍只能拒绝。
        response = InProcessWindowsNativeHostClient(host).request({"op": "action", "action": "type_text", "text": "phase47-host-secret"})  # 新增代码+Phase47WindowsSendInputDispatcher: 通过 host action 发送文本动作；如果没有这行代码，host 集成路径不会执行。
        encoded = json.dumps(response, ensure_ascii=False).lower()  # 新增代码+Phase47WindowsSendInputDispatcher: 序列化 host 响应用于泄露检查；如果没有这行代码，原始文本泄露不易发现。
        self.assertTrue(response["ok"])  # 新增代码+Phase47WindowsSendInputDispatcher: 断言 host action 成功；如果没有这行代码，集成失败可能被忽略。
        self.assertEqual(response["result"]["backend"], "windows_sendinput")  # 新增代码+Phase47WindowsSendInputDispatcher: 断言结果来自 SendInput 链路；如果没有这行代码，host 可能绕过 dispatcher。
        self.assertNotIn("phase47-host-secret", encoded)  # 新增代码+Phase47WindowsSendInputDispatcher: 断言 host 响应不泄露文本；如果没有这行代码，IPC 可能暴露用户输入。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，test_native_host_action_can_use_enabled_dispatcher_without_raw_text 到此结束；如果没有这个边界说明，读者不容易看出 host action 测试范围。

    def test_phase47_cli_contract_and_visible_terminal_scenario_tokens(self) -> None:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，验证 CLI 和场景 token；如果没有这个测试，真实终端验收可能漏关键断言。
        report = run_phase47_sendinput_dispatcher_contract()  # 新增代码+Phase47WindowsSendInputDispatcher: 运行安全自检合同；如果没有这行代码，CLI 行没有真实输入。
        cli_line = phase47_cli_line(report)  # 新增代码+Phase47WindowsSendInputDispatcher: 生成稳定 token 行；如果没有这行代码，场景无法复用同一格式。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase47_windows_sendinput_dispatcher.json")  # 新增代码+Phase47WindowsSendInputDispatcher: 定位 Phase47 场景文件；如果没有这行代码，测试无法确认真实终端配置。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase47WindowsSendInputDispatcher: 读取场景文本；如果没有这行代码，场景缺失不会暴露。
        expected_tokens = {PHASE47_WINDOWS_SENDINPUT_DISPATCHER_MARKER, PHASE47_WINDOWS_SENDINPUT_DISPATCHER_OK_TOKEN, "dispatch=true", "all_actions=true", "target_check=true", "host_action=true", "raw_text_hidden=true", "actions_expanded=true"}  # 新增代码+Phase47WindowsSendInputDispatcher: 定义 CLI 和场景必须包含的 token；如果没有这行代码，验收标准会漂移。
        for token in expected_tokens:  # 新增代码+Phase47WindowsSendInputDispatcher: 遍历关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase47WindowsSendInputDispatcher: 断言 CLI 行包含 token；如果没有这行代码，自检输出可能不稳定。
            self.assertIn(token, scenario_text)  # 新增代码+Phase47WindowsSendInputDispatcher: 断言场景包含 token；如果没有这行代码，真实终端验收可能漏检。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，test_phase47_cli_contract_and_visible_terminal_scenario_tokens 到此结束；如果没有这个边界说明，读者不容易看出场景 token 测试范围。


if __name__ == "__main__":  # 新增代码+Phase47WindowsSendInputDispatcher: 允许直接运行本测试文件；如果没有这行代码，初学者无法单独启动 Phase47 测试。
    unittest.main()  # 新增代码+Phase47WindowsSendInputDispatcher: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
