import json  # 新增代码+Phase37WindowsSendInputExecutor: 导入 JSON 工具用于检查场景文件和脱敏输出；如果没有这行代码，测试无法稳定确认真实终端验收需要匹配哪些 token。
import tempfile  # 新增代码+Phase37WindowsSendInputExecutor: 导入临时目录工具用于隔离 desktop lock 文件；如果没有这行代码，测试可能污染真实运行目录。
import unittest  # 新增代码+Phase37WindowsSendInputExecutor: 导入 unittest 框架承载 Phase37 测试；如果没有这行代码，自动化回归不会发现 SendInput 执行器问题。
from pathlib import Path  # 新增代码+Phase37WindowsSendInputExecutor: 导入 Path 方便定位场景文件和临时目录；如果没有这行代码，路径拼接会变得脆弱。
from learning_agent.computer_use.controller import ComputerUseController, WindowsComputerUseBackend  # 新增代码+Phase37WindowsSendInputExecutor: 导入控制器和 Windows 后端用于验证真实动作路由；如果没有这行代码，测试只能覆盖孤立执行器而不能证明接入链路。
from learning_agent.computer_use.lock import ComputerUseLockManager  # 新增代码+Phase37WindowsSendInputExecutor: 导入 desktop lock 管理器用于通过 Phase30 安全门；如果没有这行代码，控制器测试会因为缺少持锁条件提前失败。
from learning_agent.computer_use.sendinput_executor import PHASE37_WINDOWS_SENDINPUT_EXECUTOR_MARKER, PHASE37_WINDOWS_SENDINPUT_EXECUTOR_OK_TOKEN, WindowsSendInputExecutor, phase37_cli_line, run_phase37_sendinput_executor_contract  # 新增代码+Phase37WindowsSendInputExecutor: 导入 Phase37 预期新模块入口；如果没有这行代码，红灯测试会证明 SendInput 执行器尚未实现。
from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase37WindowsSendInputExecutor: 导入静态窗口 inventory 让测试不依赖真实桌面；如果没有这行代码，单元测试可能误读用户本机窗口。


class Phase37RecordingInputImplementation:  # 新增代码+Phase37WindowsSendInputExecutor: 定义记录型输入实现用于替代真实 SendInput；如果没有这个类，测试只能触碰真实鼠标键盘或无法验证事件。
    def __init__(self) -> None:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，初始化事件记录容器；如果没有这段函数，fake 实现无法保存收到的输入事件。
        self.calls: list[dict[str, object]] = []  # 新增代码+Phase37WindowsSendInputExecutor: 保存每次 send 调用的规范事件；如果没有这行代码，测试无法证明执行器发送了什么。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，Phase37RecordingInputImplementation.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def send(self, events: list[dict[str, object]]) -> dict[str, object]:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，接收执行器生成的规范事件；如果没有这段函数，注入实现没有统一调用入口。
        self.calls.extend(dict(event) for event in events)  # 新增代码+Phase37WindowsSendInputExecutor: 复制并保存事件避免后续修改污染断言；如果没有这行代码，测试无法检查事件顺序和内容。
        return {"ok": True, "event_count": len(events), "backend": "phase37_recording_impl"}  # 新增代码+Phase37WindowsSendInputExecutor: 返回成功摘要模拟底层 SendInput；如果没有这行代码，执行器无法得到可审计结果。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，Phase37RecordingInputImplementation.send 到此结束；如果没有这个边界说明，读者不容易分清 fake 调用范围。


class WindowsComputerUseSendInputPhase37Tests(unittest.TestCase):  # 新增代码+Phase37WindowsSendInputExecutor: 定义 Phase37 SendInput 执行器测试集合；如果没有这个类，unittest 不会组织这些安全契约检查。
    def _window(self) -> dict[str, object]:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，提供可信窗口样本；如果没有这段函数，每个测试都要重复拼写窗口身份且容易不一致。
        return {"app_id": "notepad.exe", "window_id": "hwnd:3701", "process_name": "notepad.exe", "hwnd": 3701, "title": "Phase37 Notepad", "title_preview": "Phase37 Notepad", "rect": {"left": 100, "top": 200, "right": 500, "bottom": 420}, "safe_to_target": True}  # 修改代码+Phase37WindowsSendInputExecutor: 返回同时兼容 controller 和 Phase28 inventory 归一化的安全窗口；如果没有这行代码，动作前可信窗口校验会误拒绝测试目标。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，_window 到此结束；如果没有这个边界说明，初学者不容易看出样本 helper 范围。

    def test_sendinput_executor_is_safe_and_contract_ready_by_default(self) -> None:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，验证默认状态只建立合同不执行真实输入；如果没有这个测试，默认关闭边界可能被误改。
        executor = WindowsSendInputExecutor(platform="win32", enabled=False)  # 新增代码+Phase37WindowsSendInputExecutor: 创建默认关闭的 Windows 执行器；如果没有这行代码，无法观察安全默认状态。
        status = executor.status()  # 新增代码+Phase37WindowsSendInputExecutor: 读取执行器状态；如果没有这行代码，后续断言没有输入数据。
        self.assertEqual(status["backend"], "windows_sendinput")  # 新增代码+Phase37WindowsSendInputExecutor: 断言后端名称稳定；如果没有这行代码，状态消费者可能无法识别 SendInput 执行器。
        self.assertTrue(status["contract_ready"])  # 新增代码+Phase37WindowsSendInputExecutor: 断言合同入口已建立；如果没有这行代码，Phase37 可能只剩文档没有代码入口。
        self.assertFalse(status["real_input_enabled"])  # 新增代码+Phase37WindowsSendInputExecutor: 断言默认不会执行真实输入；如果没有这行代码，测试无法防止默认触碰桌面。
        self.assertTrue(status["safe_gate_required"])  # 新增代码+Phase37WindowsSendInputExecutor: 断言仍需上游安全门；如果没有这行代码，执行器可能绕过 Phase30 门禁。
        self.assertIn("type_text", status["actions_supported"])  # 新增代码+Phase37WindowsSendInputExecutor: 断言文本动作进入支持集合；如果没有这行代码，Phase37 可能遗漏键盘输入能力。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，test_sendinput_executor_is_safe_and_contract_ready_by_default 到此结束；如果没有这个边界说明，读者不容易看出默认安全测试范围。

    def test_sendinput_executor_refuses_when_disabled_or_not_windows(self) -> None:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，验证禁用和非 Windows 都不会放行；如果没有这个测试，执行器可能跨平台误触发。
        disabled = WindowsSendInputExecutor(platform="win32", enabled=False)  # 新增代码+Phase37WindowsSendInputExecutor: 创建禁用执行器；如果没有这行代码，无法覆盖未启用拒绝路径。
        disabled_result = disabled.execute("click", {"x": 1, "y": 2})  # 新增代码+Phase37WindowsSendInputExecutor: 尝试点击用于触发拒绝；如果没有这行代码，禁用分支没有行为证据。
        non_windows = WindowsSendInputExecutor(platform="linux", enabled=True, sendinput_impl=Phase37RecordingInputImplementation())  # 新增代码+Phase37WindowsSendInputExecutor: 创建非 Windows 执行器；如果没有这行代码，跨平台拒绝路径没有覆盖。
        non_windows_result = non_windows.execute("click", {"x": 1, "y": 2})  # 新增代码+Phase37WindowsSendInputExecutor: 尝试在非 Windows 执行点击；如果没有这行代码，平台拒绝没有被验证。
        self.assertFalse(disabled_result.ok)  # 新增代码+Phase37WindowsSendInputExecutor: 断言禁用时失败；如果没有这行代码，禁用路径可能错误成功。
        self.assertFalse(non_windows_result.ok)  # 新增代码+Phase37WindowsSendInputExecutor: 断言非 Windows 时失败；如果没有这行代码，跨平台误用不会被发现。
        self.assertFalse(disabled_result.data["real_input_enabled"])  # 新增代码+Phase37WindowsSendInputExecutor: 断言禁用结果明确没有真实输入；如果没有这行代码，用户难以确认没有触碰桌面。
        self.assertEqual(non_windows_result.data["platform"], "linux")  # 新增代码+Phase37WindowsSendInputExecutor: 断言平台信息写入结果；如果没有这行代码，排查跨平台拒绝会缺少证据。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，test_sendinput_executor_refuses_when_disabled_or_not_windows 到此结束；如果没有这个边界说明，读者不容易看出拒绝路径测试范围。

    def test_sendinput_executor_uses_injected_impl_and_redacts_text(self) -> None:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，验证注入实现可执行且不会泄露原始文本；如果没有这个测试，成功路径和脱敏边界不可靠。
        recorder = Phase37RecordingInputImplementation()  # 新增代码+Phase37WindowsSendInputExecutor: 创建记录型输入实现；如果没有这行代码，测试无法检查事件列表。
        executor = WindowsSendInputExecutor(platform="win32", enabled=True, sendinput_impl=recorder)  # 新增代码+Phase37WindowsSendInputExecutor: 创建启用且注入 fake 的执行器；如果没有这行代码，成功路径无法安全触发。
        result = executor.execute("type_text", {"text": "secret-phase37"})  # 新增代码+Phase37WindowsSendInputExecutor: 执行文本输入动作；如果没有这行代码，脱敏逻辑没有被触发。
        serialized = json.dumps({"result": result.data, "events": recorder.calls}, ensure_ascii=False)  # 新增代码+Phase37WindowsSendInputExecutor: 序列化可见结果和事件用于泄露检查；如果没有这行代码，可能遗漏某处保存了原文。
        self.assertTrue(result.ok)  # 新增代码+Phase37WindowsSendInputExecutor: 断言注入实现成功；如果没有这行代码，后续事件断言可能误读失败路径。
        self.assertNotIn("secret-phase37", serialized)  # 新增代码+Phase37WindowsSendInputExecutor: 断言原始文本不进入结果或事件；如果没有这行代码，密码/token 可能被写进日志。
        self.assertEqual(result.data["text_length"], len("secret-phase37"))  # 新增代码+Phase37WindowsSendInputExecutor: 断言只保留文本长度；如果没有这行代码，审计无法知道输入规模。
        self.assertTrue(result.data["text_redacted"])  # 新增代码+Phase37WindowsSendInputExecutor: 断言结果明确标记文本已脱敏；如果没有这行代码，用户可能误以为字段丢失。
        self.assertEqual(recorder.calls[0]["type"], "text")  # 新增代码+Phase37WindowsSendInputExecutor: 断言事件类型是脱敏文本事件；如果没有这行代码，执行器可能生成错误事件。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，test_sendinput_executor_uses_injected_impl_and_redacts_text 到此结束；如果没有这个边界说明，读者不容易看出脱敏成功路径范围。

    def test_windows_backend_routes_actions_through_injected_sendinput_executor(self) -> None:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，验证 Windows 后端通过注入执行器路由动作；如果没有这个测试，新执行器可能没有接入真实链路。
        recorder = Phase37RecordingInputImplementation()  # 新增代码+Phase37WindowsSendInputExecutor: 创建 fake SendInput 实现；如果没有这行代码，后端测试可能触碰真实桌面。
        executor = WindowsSendInputExecutor(platform="win32", enabled=True, sendinput_impl=recorder)  # 新增代码+Phase37WindowsSendInputExecutor: 创建可执行但安全注入的执行器；如果没有这行代码，后端无法证明路由成功。
        window = self._window()  # 新增代码+Phase37WindowsSendInputExecutor: 获取可信窗口；如果没有这行代码，控制器无法通过窗口验证和坐标转换。
        inventory = StaticWindowsWindowInventory([window], captured_at="2026-06-03T00:00:00Z", source="phase37-static")  # 新增代码+Phase37WindowsSendInputExecutor: 创建静态 inventory 避免读取真实桌面；如果没有这行代码，测试会依赖用户本机状态。
        backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=True, action_executor=executor)  # 新增代码+Phase37WindowsSendInputExecutor: 把 SendInput 执行器注入 Windows 后端；如果没有这行代码，后端仍会走旧 mouse_event 路径。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase37WindowsSendInputExecutor: 创建临时锁目录；如果没有这行代码，测试会污染真实 lock 状态。
            lock_manager = ComputerUseLockManager(base_dir=Path(temp_dir))  # 新增代码+Phase37WindowsSendInputExecutor: 创建隔离锁管理器；如果没有这行代码，控制器不会满足持锁安全门。
            lock_manager.acquire("phase37-session", owner_label="unit-test")  # 新增代码+Phase37WindowsSendInputExecutor: 为当前 session 获取锁；如果没有这行代码，动作会在后端路由前被拒绝。
            controller = ComputerUseController(backend=backend, lock_manager=lock_manager, owner_session_id="phase37-session")  # 新增代码+Phase37WindowsSendInputExecutor: 创建带 Windows 后端的控制器；如果没有这行代码，无法验证完整 execute 链路。
            result = controller.execute({"action": "click", "confirm_desktop_control": True, "window": window, "x": 9, "y": 11})  # 新增代码+Phase37WindowsSendInputExecutor: 执行窗口相对点击；如果没有这行代码，坐标转换和后端路由不会发生。
        self.assertTrue(result.ok)  # 新增代码+Phase37WindowsSendInputExecutor: 断言完整链路成功；如果没有这行代码，后端失败也可能被忽略。
        self.assertEqual(result.data["backend"], "windows_sendinput")  # 新增代码+Phase37WindowsSendInputExecutor: 断言结果来自 SendInput 执行器；如果没有这行代码，旧 Win32 mouse_event 路径可能混进来。
        self.assertEqual(recorder.calls[0]["x"], 109)  # 新增代码+Phase37WindowsSendInputExecutor: 断言 x 坐标已从窗口相对 9 转为屏幕 100+9；如果没有这行代码，坐标空间错误不会暴露。
        self.assertEqual(recorder.calls[0]["y"], 211)  # 新增代码+Phase37WindowsSendInputExecutor: 断言 y 坐标已从窗口相对 11 转为屏幕 200+11；如果没有这行代码，点击位置可能错误。
        self.assertEqual(result.data["action_evidence"]["coordinate_used"]["space"], "screen")  # 新增代码+Phase37WindowsSendInputExecutor: 断言控制器仍附加坐标证据；如果没有这行代码，Phase30 evidence 可能被新执行器破坏。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，test_windows_backend_routes_actions_through_injected_sendinput_executor 到此结束；如果没有这个边界说明，读者不容易看出接入链路测试范围。

    def test_phase37_contract_cli_and_visible_terminal_scenario_tokens(self) -> None:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，验证 CLI token 和场景文件稳定；如果没有这个测试，真实终端验收可能漏掉关键标记。
        report = run_phase37_sendinput_executor_contract()  # 新增代码+Phase37WindowsSendInputExecutor: 运行 Phase37 合同诊断；如果没有这行代码，CLI 输出没有可断言数据。
        line = phase37_cli_line(report)  # 新增代码+Phase37WindowsSendInputExecutor: 生成稳定的一行验收 token；如果没有这行代码，debug log 匹配会变得脆弱。
        project_root = Path(__file__).resolve().parents[2]  # 新增代码+Phase37WindowsSendInputExecutor: 定位项目根目录；如果没有这行代码，测试无法稳定找到 scenario。
        scenario_path = project_root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_phase37_windows_sendinput_executor.json"  # 新增代码+Phase37WindowsSendInputExecutor: 定位 Phase37 真实终端场景；如果没有这行代码，测试可能检查错文件。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase37WindowsSendInputExecutor: 读取场景 JSON；如果没有这行代码，场景缺失或格式错误不会被发现。
        expected_tokens = {PHASE37_WINDOWS_SENDINPUT_EXECUTOR_MARKER, PHASE37_WINDOWS_SENDINPUT_EXECUTOR_OK_TOKEN, "contract_ready=true", "real_input_default=false", "fake_impl_exercised=true", "raw_text_hidden=true", "actions_expanded=false"}  # 新增代码+Phase37WindowsSendInputExecutor: 定义必须同时出现在 CLI 和场景中的 token；如果没有这行代码，验收标准容易漂移。
        self.assertIn("learning_agent.computer_use.sendinput_executor", " ".join(scenario["prompt_lines"]))  # 新增代码+Phase37WindowsSendInputExecutor: 断言场景调用 Phase37 模块；如果没有这行代码，场景可能绕过新能力。
        for token in expected_tokens:  # 新增代码+Phase37WindowsSendInputExecutor: 遍历所有稳定 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, line)  # 新增代码+Phase37WindowsSendInputExecutor: 断言 CLI 行包含 token；如果没有这行代码，命令行验收可能不稳定。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase37WindowsSendInputExecutor: 断言 debug log 检查包含 token；如果没有这行代码，controller 可能没有验证命令输出。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase37WindowsSendInputExecutor: 断言最终回答检查包含 token；如果没有这行代码，用户可见输出可能漏标记。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，test_phase37_contract_cli_and_visible_terminal_scenario_tokens 到此结束；如果没有这个边界说明，读者不容易看出场景 token 测试范围。


if __name__ == "__main__":  # 新增代码+Phase37WindowsSendInputExecutor: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase37WindowsSendInputExecutor: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行任何测试。
