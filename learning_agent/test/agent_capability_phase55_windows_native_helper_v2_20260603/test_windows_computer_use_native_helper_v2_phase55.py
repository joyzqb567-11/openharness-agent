import json  # 新增代码+Phase55WindowsNativeHelperV2: 导入 JSON 工具检查响应和场景；如果没有这行代码，测试无法验证敏感字段没有泄露。
import unittest  # 新增代码+Phase55WindowsNativeHelperV2: 导入 unittest 框架；如果没有这行代码，自动化命令无法发现 Phase55 测试。
from pathlib import Path  # 新增代码+Phase55WindowsNativeHelperV2: 导入 Path 定位真实终端场景；如果没有这行代码，场景路径拼接会更脆弱。

from learning_agent.computer_use.native_helper_v2 import PHASE55_WINDOWS_NATIVE_HELPER_V2_MARKER, PHASE55_WINDOWS_NATIVE_HELPER_V2_OK_TOKEN, WindowsNativeHelperV2Client, phase55_cli_line, run_phase55_native_helper_v2_contract  # 新增代码+Phase55WindowsNativeHelperV2: 导入预期新增的 out-of-process helper v2；如果没有这行代码，红灯会证明 Phase55 尚未实现。


class WindowsComputerUseNativeHelperV2Phase55Tests(unittest.TestCase):  # 新增代码+Phase55WindowsNativeHelperV2: 类段开始，组织 Phase55 helper v2 测试；如果没有这个类，unittest 不会执行本阶段门禁。
    def test_process_helper_lifecycle_protocol_and_safe_defaults(self) -> None:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，验证 helper 子进程生命周期、协议和安全默认值；如果没有这个测试，helper v2 可能仍只是进程内假对象。
        client = WindowsNativeHelperV2Client()  # 新增代码+Phase55WindowsNativeHelperV2: 创建真实子进程 helper client；如果没有这行代码，测试没有进程边界对象。
        try:  # 新增代码+Phase55WindowsNativeHelperV2: 确保测试结束时清理子进程；如果没有这行代码，失败时可能残留 worker。
            health = client.start()  # 新增代码+Phase55WindowsNativeHelperV2: 启动 helper 子进程并读取 health；如果没有这行代码，无法证明 out-of-process 边界。
            status = client.request({"op": "status"})  # 新增代码+Phase55WindowsNativeHelperV2: 请求 status；如果没有这行代码，协议状态分支没有覆盖。
            windows = client.request({"op": "list_windows"})  # 新增代码+Phase55WindowsNativeHelperV2: 请求 list_windows；如果没有这行代码，窗口枚举协议没有覆盖。
            capture = client.request({"op": "capture_window", "window": {"window_id": "hwnd:5501"}})  # 新增代码+Phase55WindowsNativeHelperV2: 请求 capture_window；如果没有这行代码，截图协议没有覆盖。
            uia = client.request({"op": "read_uia_tree", "window": {"window_id": "hwnd:5501"}})  # 新增代码+Phase55WindowsNativeHelperV2: 请求 read_uia_tree；如果没有这行代码，UIA 树协议没有覆盖。
            action = client.request({"op": "send_input", "action": "type_text", "text": "phase55-hidden-secret"})  # 新增代码+Phase55WindowsNativeHelperV2: 请求 send_input 并期待默认拒绝；如果没有这行代码，真实输入安全门没有覆盖。
            hotkey = client.request({"op": "hotkey", "action": "status"})  # 新增代码+Phase55WindowsNativeHelperV2: 请求 hotkey 状态；如果没有这行代码，全局热键协议没有覆盖。
            cleanup = client.request({"op": "cleanup"})  # 新增代码+Phase55WindowsNativeHelperV2: 请求 cleanup；如果没有这行代码，worker 清理协议没有覆盖。
        finally:  # 新增代码+Phase55WindowsNativeHelperV2: 无论断言是否失败都清理 helper；如果没有这行代码，子进程可能留在后台。
            client.close(kill=True)  # 新增代码+Phase55WindowsNativeHelperV2: 强制关闭子进程兜底；如果没有这行代码，测试失败时可能残留 python worker。
        serialized = json.dumps({"action": action, "capture": capture, "uia": uia}, ensure_ascii=False)  # 新增代码+Phase55WindowsNativeHelperV2: 序列化响应做泄露检查；如果没有这行代码，原始文本或 bytes 泄露不易发现。
        self.assertTrue(health["healthy"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言 health 为真；如果没有这行代码，helper 启动失败不会被发现。
        self.assertGreater(int(health["pid"]), 0)  # 新增代码+Phase55WindowsNativeHelperV2: 断言 pid 存在；如果没有这行代码，进程内假对象也可能误过。
        self.assertTrue(status["ok"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言 status 响应成功；如果没有这行代码，协议健康不可靠。
        self.assertIn("capture_window", status["result"]["capabilities"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言截图能力在 helper 能力表里；如果没有这行代码，协议覆盖可能缺项。
        self.assertTrue(windows["ok"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言 list_windows 响应成功；如果没有这行代码，窗口协议失败不会暴露。
        self.assertTrue(capture["ok"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言 capture_window 协议成功返回摘要；如果没有这行代码，截图协议失败不会暴露。
        self.assertFalse(capture["result"]["screenshot_bytes_included"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言截图 bytes 不进 JSON；如果没有这行代码，大图或敏感屏幕内容可能外泄。
        self.assertTrue(uia["ok"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言 read_uia_tree 协议成功返回摘要；如果没有这行代码，UIA 协议失败不会暴露。
        self.assertFalse(uia["result"]["raw_text_included"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言 UIA 原文不进 JSON；如果没有这行代码，敏感文本可能越过脱敏层。
        self.assertFalse(action["ok"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言 send_input 默认拒绝；如果没有这行代码，helper v2 可能默认触碰真实键鼠。
        self.assertEqual(action["error"]["decision"], "real_action_refused_by_helper_v2")  # 新增代码+Phase55WindowsNativeHelperV2: 断言拒绝原因稳定；如果没有这行代码，调用方不知道动作为何没执行。
        self.assertTrue(hotkey["ok"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言 hotkey 状态协议成功；如果没有这行代码，热键协议缺口不会暴露。
        self.assertTrue(cleanup["ok"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言 cleanup 响应成功；如果没有这行代码，生命周期清理不可验证。
        self.assertNotIn("phase55-hidden-secret", serialized)  # 新增代码+Phase55WindowsNativeHelperV2: 断言原始输入文本没有出现在响应里；如果没有这行代码，send_input 脱敏可能失效。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，test_process_helper_lifecycle_protocol_and_safe_defaults 到此结束；如果没有这个边界说明，初学者不容易看出生命周期测试范围。

    def test_timeout_and_crash_return_structured_errors_without_crashing_agent(self) -> None:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，验证超时和崩溃变成结构化错误；如果没有这个测试，helper 崩溃可能拖垮主 agent。
        timeout_client = WindowsNativeHelperV2Client(default_timeout_seconds=0.05)  # 新增代码+Phase55WindowsNativeHelperV2: 创建短超时 client；如果没有这行代码，超时路径难以稳定触发。
        try:  # 新增代码+Phase55WindowsNativeHelperV2: 确保超时后清理进程；如果没有这行代码，阻塞 worker 可能残留。
            timeout_client.start()  # 新增代码+Phase55WindowsNativeHelperV2: 启动短超时 worker；如果没有这行代码，请求没有目标进程。
            timeout_result = timeout_client.request({"op": "debug_sleep", "seconds": 1})  # 新增代码+Phase55WindowsNativeHelperV2: 发送测试用睡眠请求；如果没有这行代码，超时错误没有覆盖。
        finally:  # 新增代码+Phase55WindowsNativeHelperV2: 无论超时断言如何都清理 worker；如果没有这行代码，睡眠进程可能残留。
            timeout_client.close(kill=True)  # 新增代码+Phase55WindowsNativeHelperV2: 强制杀掉超时 worker；如果没有这行代码，测试会等待 worker 自然醒来。
        crash_client = WindowsNativeHelperV2Client()  # 新增代码+Phase55WindowsNativeHelperV2: 创建崩溃路径 client；如果没有这行代码，崩溃测试没有独立进程。
        try:  # 新增代码+Phase55WindowsNativeHelperV2: 确保崩溃后清理句柄；如果没有这行代码，子进程资源可能残留。
            crash_client.start()  # 新增代码+Phase55WindowsNativeHelperV2: 启动 worker；如果没有这行代码，debug_crash 请求没有目标。
            crash_result = crash_client.request({"op": "debug_crash"})  # 新增代码+Phase55WindowsNativeHelperV2: 发送测试用崩溃请求；如果没有这行代码，崩溃恢复没有覆盖。
            after_crash = crash_client.request({"op": "status"})  # 新增代码+Phase55WindowsNativeHelperV2: 崩溃后再次请求 status；如果没有这行代码，主 agent 是否稳定不可验证。
        finally:  # 新增代码+Phase55WindowsNativeHelperV2: 无论断言如何都关闭 client；如果没有这行代码，残留句柄可能影响后续测试。
            crash_client.close(kill=True)  # 新增代码+Phase55WindowsNativeHelperV2: 强制关闭崩溃 worker 兜底；如果没有这行代码，资源可能残留。
        self.assertFalse(timeout_result["ok"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言超时返回失败；如果没有这行代码，超时可能被误当成功。
        self.assertEqual(timeout_result["error"]["decision"], "native_helper_v2_timeout")  # 新增代码+Phase55WindowsNativeHelperV2: 断言超时错误码稳定；如果没有这行代码，调用方无法恢复。
        self.assertFalse(crash_result["ok"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言崩溃请求返回失败；如果没有这行代码，worker 崩溃可能误过。
        self.assertIn(crash_result["error"]["decision"], {"native_helper_v2_process_exited", "native_helper_v2_transport_error"})  # 新增代码+Phase55WindowsNativeHelperV2: 允许崩溃被读取为进程退出或传输错误；如果没有这行代码，Windows 管道时序差异会让测试脆弱。
        self.assertFalse(after_crash["ok"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言崩溃后请求不拖垮主 agent；如果没有这行代码，恢复路径无法验证。
        self.assertEqual(after_crash["error"]["decision"], "native_helper_v2_process_unavailable")  # 新增代码+Phase55WindowsNativeHelperV2: 断言崩溃后错误码稳定；如果没有这行代码，主 agent 无法判断需要重启 helper。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，test_timeout_and_crash_return_structured_errors_without_crashing_agent 到此结束；如果没有这个边界说明，初学者不容易看出错误恢复测试范围。

    def test_phase55_cli_line_and_visible_terminal_scenario_tokens_are_stable(self) -> None:  # 新增代码+Phase55WindowsNativeHelperV2: 函数段开始，验证 CLI 行和真实终端场景 token；如果没有这个测试，Phase55 可能缺少可见验收入口。
        report = run_phase55_native_helper_v2_contract()  # 新增代码+Phase55WindowsNativeHelperV2: 运行 Phase55 合同自检；如果没有这行代码，CLI 行没有真实输入。
        cli_line = phase55_cli_line(report)  # 新增代码+Phase55WindowsNativeHelperV2: 生成稳定验收行；如果没有这行代码，场景 token 无法复用。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase55_windows_native_helper_v2.json")  # 新增代码+Phase55WindowsNativeHelperV2: 定位 Phase55 场景；如果没有这行代码，测试无法确认真实终端配置。
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))  # 新增代码+Phase55WindowsNativeHelperV2: 读取场景 JSON；如果没有这行代码，场景缺失不会被发现。
        expected_tokens = {PHASE55_WINDOWS_NATIVE_HELPER_V2_MARKER, PHASE55_WINDOWS_NATIVE_HELPER_V2_OK_TOKEN, "process_started=true", "health=true", "messages=true", "timeout_handled=true", "crash_handled=true", "send_input_refused=true", "raw_text_hidden=true", "actions_expanded=false"}  # 新增代码+Phase55WindowsNativeHelperV2: 定义 CLI 和场景都必须包含的 token；如果没有这行代码，验收标准容易漂移。
        for token in expected_tokens:  # 新增代码+Phase55WindowsNativeHelperV2: 遍历关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase55WindowsNativeHelperV2: 断言 CLI 行包含 token；如果没有这行代码，命令行验收可能不稳定。
            self.assertIn(token, scenario["debug_log_contains"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言场景 debug log 检查包含 token；如果没有这行代码，真实终端验收可能漏检。
            self.assertIn(token, scenario["event_answer_contains"])  # 新增代码+Phase55WindowsNativeHelperV2: 断言场景最终回答检查包含 token；如果没有这行代码，用户可见答案可能缺少证据。
    # 新增代码+Phase55WindowsNativeHelperV2: 函数段结束，test_phase55_cli_line_and_visible_terminal_scenario_tokens_are_stable 到此结束；如果没有这个边界说明，初学者不容易看出场景 token 测试范围。


if __name__ == "__main__":  # 新增代码+Phase55WindowsNativeHelperV2: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase55WindowsNativeHelperV2: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行任何测试。
