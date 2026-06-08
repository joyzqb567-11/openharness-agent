import json  # 新增代码+Phase2Pairing: 用来扫描持久化状态是否泄露敏感字段；如果没有这行代码，测试无法验证脱敏结果。
import tempfile  # 新增代码+Phase2Pairing: 用临时目录隔离 bridge 和 runtime queue；如果没有这行代码，测试会污染真实 memory。
import unittest  # 新增代码+Phase2Pairing: 使用项目现有 unittest 框架；如果没有这行代码，测试类无法执行。
from pathlib import Path  # 新增代码+Phase2Pairing: 用 Path 处理临时文件路径；如果没有这行代码，路径拼接容易出错。


class ChromeExtensionPairingStage14Tests(unittest.TestCase):  # 新增代码+Phase2Pairing: 验证扩展配对和 session sync；如果没有这个测试类，Phase 2 没有自动化红线。
    def test_pairing_record_redacts_sensitive_fields_and_reports_status(self) -> None:  # 新增代码+Phase2Pairing: 锁定配对状态脱敏和状态输出；如果没有这个测试，token/cookie 可能进入状态文件。
        from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+Phase2Pairing: 导入 bridge 状态；如果没有这行代码，无法模拟 native host 连接。

        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase2Pairing: 创建隔离目录；如果没有这行代码，测试会写真实 bridge 文件。
            bridge = ChromeExtensionBridgeState(Path(raw_dir) / "bridge.json")  # 新增代码+Phase2Pairing: 创建 bridge 状态对象；如果没有这行代码，无法保存配对信息。
            bridge.record_pairing({"device_id": "device-1", "session_id": "session-1", "extension_id": "ext-1", "allowed_origins": ["https://example.com"], "token": "SECRET", "cookie": "COOKIE"})  # 新增代码+Phase2Pairing: 模拟扩展配对请求并夹带敏感字段；如果没有这行代码，无法证明脱敏。
            status = bridge.session_sync_status_text()  # 新增代码+Phase2Pairing: 读取 session sync 状态文本；如果没有这行代码，无法验证 UI/状态输出。
            raw_state = json.dumps(bridge.store.load(), ensure_ascii=False)  # 新增代码+Phase2Pairing: 读取落盘 JSON 文本；如果没有这行代码，无法扫描敏感值。

        self.assertIn("paired=true", status)  # 新增代码+Phase2Pairing: 状态应显示已配对；如果没有这行断言，UI 可能看不到配对成功。
        self.assertIn("device_id=device-1", status)  # 新增代码+Phase2Pairing: 状态应显示设备 id；如果没有这行断言，排障无法定位设备。
        self.assertIn("session_id=session-1", status)  # 新增代码+Phase2Pairing: 状态应显示 session id；如果没有这行断言，session sync 无法审计。
        self.assertNotIn("SECRET", raw_state)  # 新增代码+Phase2Pairing: token 值不能落盘；如果没有这行断言，敏感信息可能泄露。
        self.assertNotIn("COOKIE", raw_state)  # 新增代码+Phase2Pairing: cookie 值不能落盘；如果没有这行断言，浏览器登录态可能泄露。

    def test_browser_prompt_is_enqueued_into_runtime_command_queue(self) -> None:  # 新增代码+Phase2Pairing: 验证浏览器侧 prompt 进入 durable queue；如果没有这个测试，扩展可能绕过主循环。
        from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+Phase2Pairing: 导入 bridge 状态；如果没有这行代码，无法模拟 browser prompt。
        from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+Phase2Pairing: 导入 durable queue；如果没有这行代码，无法验证 prompt 是否入队。

        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase2Pairing: 创建临时 workspace；如果没有这行代码，队列会污染真实项目。
            root = Path(raw_dir)  # 新增代码+Phase2Pairing: 转成 Path；如果没有这行代码，后续路径不统一。
            bridge = ChromeExtensionBridgeState(root / "bridge.json")  # 新增代码+Phase2Pairing: 创建 bridge；如果没有这行代码，无法调用 prompt push。
            queue = RuntimeCommandQueue(root / "runtime")  # 新增代码+Phase2Pairing: 创建 durable queue；如果没有这行代码，prompt 没有落盘目标。
            result = bridge.enqueue_browser_prompt(queue, {"prompt": "帮我总结当前网页", "url": "https://example.com/page", "title": "Example", "selected_text": "hello", "tab_id": "chrome-tab-7", "password": "SECRET"})  # 新增代码+Phase2Pairing: 模拟浏览器侧推任务；如果没有这行代码，无法验证 payload。
            command = RuntimeCommandQueue(root / "runtime").dequeue_next()  # 新增代码+Phase2Pairing: 重启式读取队列命令；如果没有这行代码，无法证明持久化。

        self.assertEqual(result["mode"], "browser_prompt")  # 新增代码+Phase2Pairing: bridge 返回应说明 browser_prompt；如果没有这行断言，调用方无法区分来源。
        self.assertIsNotNone(command)  # 新增代码+Phase2Pairing: 队列里必须有命令；如果没有这行断言，prompt 可能没有入队。
        self.assertEqual(command.mode, "prompt")  # 新增代码+Phase2Pairing: 浏览器 prompt 应进入主 prompt 模式；如果没有这行断言，主循环可能不消费。
        self.assertIn("帮我总结当前网页", command.payload["text"])  # 新增代码+Phase2Pairing: prompt 正文必须进入模型上下文；如果没有这行断言，用户意图会丢失。
        self.assertIn("https://example.com/page", command.payload["text"])  # 新增代码+Phase2Pairing: URL 必须随 prompt 进入上下文；如果没有这行断言，agent 不知道页面来源。
        self.assertNotIn("SECRET", json.dumps(command.to_dict(), ensure_ascii=False))  # 新增代码+Phase2Pairing: 敏感值不能进入队列；如果没有这行断言，浏览器密码可能进入模型上下文。


if __name__ == "__main__":  # 新增代码+Phase2Pairing: 支持直接运行测试文件；如果没有这行代码，手动排查不方便。
    unittest.main()  # 新增代码+Phase2Pairing: 启动 unittest；如果没有这行代码，直接运行不会执行测试。
