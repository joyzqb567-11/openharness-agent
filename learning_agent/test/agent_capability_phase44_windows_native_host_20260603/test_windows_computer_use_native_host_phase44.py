import json  # 新增代码+Phase44WindowsNativeHost: 导入 JSON 工具检查验收场景；如果没有这行代码，测试无法验证场景文件是否包含固定 token。
import unittest  # 新增代码+Phase44WindowsNativeHost: 导入 unittest 框架承载 Phase44 测试；如果没有这行代码，本阶段测试不会被自动发现。
from pathlib import Path  # 新增代码+Phase44WindowsNativeHost: 导入 Path 定位场景文件；如果没有这行代码，路径拼接会变成脆弱字符串。

from learning_agent.computer_use.helper_client import StaticWindowObservationHelper, WindowObservationPayload  # 新增代码+Phase44WindowsNativeHost: 导入静态 helper 和 payload；如果没有这行代码，测试会依赖真实桌面观察。
from learning_agent.computer_use.native_host import PHASE44_WINDOWS_NATIVE_HOST_MARKER, PHASE44_WINDOWS_NATIVE_HOST_OK_TOKEN, InProcessWindowsNativeHostClient, WindowsComputerUseNativeHost, phase44_cli_line, run_phase44_native_host_contract  # 新增代码+Phase44WindowsNativeHost: 导入 Phase44 期望的新 host 协议；如果没有这行代码，红灯会证明 native host 还没实现。


class WindowsComputerUseNativeHostPhase44Tests(unittest.TestCase):  # 新增代码+Phase44WindowsNativeHost: 定义 Phase44 测试集合；如果没有这个类，unittest 不会组织 native host 测试。
    def _payload(self) -> WindowObservationPayload:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，构造安全观察 payload；如果没有这段函数，每个测试都要重复创建截图和文本样本。
        return WindowObservationPayload(screenshot_bytes=b"phase44-bmp", screenshot_format="bmp", screenshot_width=44, screenshot_height=22, accessibility_text="button: OK", focused_element="edit", selected_text="", document_text="document", helper_name="static_phase44_helper", helper_available=True, helper_reason="phase44 static")  # 新增代码+Phase44WindowsNativeHost: 返回静态 payload；如果没有这行代码，host observe/capture 没有可验证数据。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，_payload 到此结束；如果没有这个边界说明，读者不容易看出 payload 构造范围。

    def _host(self) -> WindowsComputerUseNativeHost:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，构造带静态 helper 的 host；如果没有这段函数，测试搭建会重复且容易漏安全默认值。
        helper = StaticWindowObservationHelper(default_payload=self._payload())  # 新增代码+Phase44WindowsNativeHost: 创建静态 helper 避免读取真实桌面；如果没有这行代码，host 测试会依赖本机窗口。
        return WindowsComputerUseNativeHost(helper=helper, platform="win32")  # 新增代码+Phase44WindowsNativeHost: 返回 Windows 平台 host；如果没有这行代码，测试无法验证协议状态。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，_host 到此结束；如果没有这个边界说明，读者不容易看出 host 构造范围。

    def test_native_host_status_exposes_protocol_and_safe_defaults(self) -> None:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，验证 host 状态和安全默认值；如果没有这个测试，host 可能默认开启真实动作。
        host = self._host()  # 新增代码+Phase44WindowsNativeHost: 创建被测 host；如果没有这行代码，测试没有对象。
        start_result = host.start()  # 新增代码+Phase44WindowsNativeHost: 启动 host 会话；如果没有这行代码，health_check 无法证明启动流程。
        status = host.status()  # 新增代码+Phase44WindowsNativeHost: 读取 host 状态；如果没有这行代码，后续断言没有输入。

        self.assertTrue(start_result["started"])  # 新增代码+Phase44WindowsNativeHost: 断言 start 成功；如果没有这行代码，启动失败不会暴露。
        self.assertEqual(status["marker"], PHASE44_WINDOWS_NATIVE_HOST_MARKER)  # 新增代码+Phase44WindowsNativeHost: 断言 marker 稳定；如果没有这行代码，真实终端场景可能等待错误标记。
        self.assertTrue(status["healthy"])  # 新增代码+Phase44WindowsNativeHost: 断言 host 健康；如果没有这行代码，status 可能只返回静态文本。
        self.assertIn("status", status["supported_messages"])  # 新增代码+Phase44WindowsNativeHost: 断言 status 消息受支持；如果没有这行代码，client 无法健康检查。
        self.assertIn("observe", status["supported_messages"])  # 新增代码+Phase44WindowsNativeHost: 断言 observe 消息受支持；如果没有这行代码，host 不能做窗口观察。
        self.assertIn("capture", status["supported_messages"])  # 新增代码+Phase44WindowsNativeHost: 断言 capture 消息受支持；如果没有这行代码，host 不能承接截图协议。
        self.assertIn("action", status["supported_messages"])  # 新增代码+Phase44WindowsNativeHost: 断言 action 消息存在但默认拒绝；如果没有这行代码，未来动作协议没有稳定入口。
        self.assertFalse(status["real_actions_enabled"])  # 新增代码+Phase44WindowsNativeHost: 断言真实动作默认关闭；如果没有这行代码，host 可能误触碰鼠标键盘。
        self.assertFalse(status["actions_expanded"])  # 新增代码+Phase44WindowsNativeHost: 断言 Phase44 不扩大动作面；如果没有这行代码，架构阶段可能被误解成动作阶段。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，test_native_host_status_exposes_protocol_and_safe_defaults 到此结束；如果没有这个边界说明，读者不容易看出状态测试范围。

    def test_client_routes_status_observe_capture_and_cleanup_messages(self) -> None:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，验证 client 能路由核心消息；如果没有这个测试，host 和 client 可能只是两个孤立类。
        client = InProcessWindowsNativeHostClient(self._host())  # 新增代码+Phase44WindowsNativeHost: 创建进程内 client；如果没有这行代码，测试无法模拟主 agent 与 host 通信。
        health = client.health_check()  # 新增代码+Phase44WindowsNativeHost: 执行健康检查；如果没有这行代码，start/health 流程没有覆盖。
        observe = client.request({"op": "observe", "window": {"window_id": "hwnd:4401"}})  # 新增代码+Phase44WindowsNativeHost: 发送 observe 消息；如果没有这行代码，观察协议没有验证。
        capture = client.request({"op": "capture", "window": {"window_id": "hwnd:4401"}})  # 新增代码+Phase44WindowsNativeHost: 发送 capture 消息；如果没有这行代码，截图协议没有验证。
        cleanup = client.request({"op": "cleanup"})  # 新增代码+Phase44WindowsNativeHost: 发送 cleanup 消息；如果没有这行代码，turn cleanup 协议没有验证。

        self.assertTrue(health["healthy"])  # 新增代码+Phase44WindowsNativeHost: 断言 health 成功；如果没有这行代码，client 可能没有启动 host。
        self.assertTrue(observe["ok"])  # 新增代码+Phase44WindowsNativeHost: 断言 observe 成功；如果没有这行代码，host observe 失败不会暴露。
        self.assertEqual(observe["result"]["helper_name"], "static_phase44_helper")  # 新增代码+Phase44WindowsNativeHost: 断言 helper 来源透传；如果没有这行代码，结果来源不可审计。
        self.assertTrue(capture["ok"])  # 新增代码+Phase44WindowsNativeHost: 断言 capture 成功；如果没有这行代码，截图协议失败不会暴露。
        self.assertTrue(capture["result"]["screenshot_captured"])  # 新增代码+Phase44WindowsNativeHost: 断言截图字节被识别为已捕获；如果没有这行代码，capture 可能只返回空壳。
        self.assertFalse(capture["result"]["screenshot_bytes_included"])  # 新增代码+Phase44WindowsNativeHost: 断言 host JSON 响应不直接带原始图片字节；如果没有这行代码，后续 IPC 可能传大二进制或泄露内容。
        self.assertTrue(cleanup["result"]["cleanup_completed"])  # 新增代码+Phase44WindowsNativeHost: 断言 cleanup 完成；如果没有这行代码，host 停止/清理协议没有证据。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，test_client_routes_status_observe_capture_and_cleanup_messages 到此结束；如果没有这个边界说明，读者不容易看出消息路由测试范围。

    def test_native_host_refuses_actions_and_unknown_messages_by_default(self) -> None:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，验证默认拒绝真实动作和未知消息；如果没有这个测试，host 可能绕过安全门。
        client = InProcessWindowsNativeHostClient(self._host())  # 新增代码+Phase44WindowsNativeHost: 创建进程内 client；如果没有这行代码，测试无法发送消息。
        action = client.request({"op": "action", "action": "click", "x": 1, "y": 2})  # 新增代码+Phase44WindowsNativeHost: 尝试发送动作消息；如果没有这行代码，默认拒绝路径没有覆盖。
        unknown = client.request({"op": "delete_everything"})  # 新增代码+Phase44WindowsNativeHost: 尝试未知消息；如果没有这行代码，协议白名单没有覆盖。

        self.assertFalse(action["ok"])  # 新增代码+Phase44WindowsNativeHost: 断言动作被拒绝；如果没有这行代码，真实动作默认关闭可能失效。
        self.assertEqual(action["error"]["decision"], "real_action_refused_by_native_host")  # 新增代码+Phase44WindowsNativeHost: 断言拒绝原因稳定；如果没有这行代码，用户不知道为什么动作没执行。
        self.assertFalse(unknown["ok"])  # 新增代码+Phase44WindowsNativeHost: 断言未知消息被拒绝；如果没有这行代码，host 可能接收任意命令。
        self.assertEqual(unknown["error"]["decision"], "unsupported_native_host_message")  # 新增代码+Phase44WindowsNativeHost: 断言未知消息拒绝原因稳定；如果没有这行代码，调试协议错误会困难。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，test_native_host_refuses_actions_and_unknown_messages_by_default 到此结束；如果没有这个边界说明，读者不容易看出拒绝测试范围。

    def test_phase44_cli_line_and_visible_terminal_scenario_tokens(self) -> None:  # 新增代码+Phase44WindowsNativeHost: 函数段开始，验证 CLI 行和真实终端场景 token；如果没有这个测试，Phase44 可能缺少可见验收入口。
        report = run_phase44_native_host_contract()  # 新增代码+Phase44WindowsNativeHost: 运行 Phase44 合同自检；如果没有这行代码，CLI 行没有真实输入。
        cli_line = phase44_cli_line(report)  # 新增代码+Phase44WindowsNativeHost: 生成稳定验收行；如果没有这行代码，场景 token 无法复用。
        scenario_path = Path("learning_agent/acceptance_controller/scenarios/agent_capability_phase44_windows_native_host.json")  # 新增代码+Phase44WindowsNativeHost: 定位 Phase44 场景；如果没有这行代码，测试无法确认真实终端配置。
        scenario_text = scenario_path.read_text(encoding="utf-8")  # 新增代码+Phase44WindowsNativeHost: 读取场景文本；如果没有这行代码，场景缺失不会被发现。
        expected_tokens = {PHASE44_WINDOWS_NATIVE_HOST_MARKER, PHASE44_WINDOWS_NATIVE_HOST_OK_TOKEN, "health=true", "messages=true", "safe_action_refused=true", "actions_expanded=false"}  # 新增代码+Phase44WindowsNativeHost: 定义 CLI 和场景都必须包含的 token；如果没有这行代码，验收标准容易漂移。

        for token in expected_tokens:  # 新增代码+Phase44WindowsNativeHost: 遍历关键 token；如果没有这行代码，断言会重复且容易漏项。
            self.assertIn(token, cli_line)  # 新增代码+Phase44WindowsNativeHost: 断言 CLI 行包含 token；如果没有这行代码，命令行验收可能不稳定。
            self.assertIn(token, scenario_text)  # 新增代码+Phase44WindowsNativeHost: 断言场景包含 token；如果没有这行代码，真实可见终端验收可能漏检。
    # 新增代码+Phase44WindowsNativeHost: 函数段结束，test_phase44_cli_line_and_visible_terminal_scenario_tokens 到此结束；如果没有这个边界说明，读者不容易看出场景 token 测试范围。


if __name__ == "__main__":  # 新增代码+Phase44WindowsNativeHost: 允许直接运行本测试文件；如果没有这行代码，初学者不能用 python 文件方式启动测试。
    unittest.main()  # 新增代码+Phase44WindowsNativeHost: 启动 unittest 主入口；如果没有这行代码，直接运行文件不会执行任何测试。
