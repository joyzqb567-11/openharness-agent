import json  # 新增代码+Phase15ChromePairingTrigger: 读取 bridge 状态 JSON；如果没有这行代码，测试无法确认配对请求是否真的落盘。
import tempfile  # 新增代码+Phase15ChromePairingTrigger: 创建隔离临时目录；如果没有这行代码，测试会污染真实 learning_agent memory。
import unittest  # 新增代码+Phase15ChromePairingTrigger: 使用项目现有 unittest 框架；如果没有这行代码，本文件无法定义自动化测试。
from pathlib import Path  # 新增代码+Phase15ChromePairingTrigger: 处理 Windows 和临时路径；如果没有这行代码，路径拼接会更脆弱。

from learning_agent.app.interactive import run_chrome_terminal_command  # 新增代码+Phase15ChromePairingTrigger: 复用真实 /chrome 终端入口；如果没有这行代码，测试会绕过用户实际使用路径。
from learning_agent.browser_extension_host.bridge_server import ChromeExtensionBridgeState  # 新增代码+Phase15ChromePairingTrigger: 直接验证 bridge 配对请求生命周期；如果没有这行代码，无法证明 host 侧状态更新。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+Phase15ChromePairingTrigger: 验证 /chrome 状态事实源；如果没有这行代码，状态 UI 可能和 bridge 文件脱节。


class ChromePairingTriggerPhase15Tests(unittest.TestCase):  # 新增代码+Phase15ChromePairingTrigger: 定义 Phase 15 配对触发测试集合；如果没有这段测试，配对触发链路没有行为红线。
    def test_pairing_preview_is_read_only_and_shows_request_shape(self) -> None:  # 新增代码+Phase15ChromePairingTrigger: 验证预览命令只展示不写文件；如果没有这段测试，preview 可能误写真实状态。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase15ChromePairingTrigger: 创建临时目录；如果没有这行代码，测试会复用真实 workspace。
            workspace = Path(temp_dir) / "learning_agent"  # 新增代码+Phase15ChromePairingTrigger: 模拟 start_oauth_agent.bat 的 workspace 形态；如果没有这行代码，路径兼容问题无法覆盖。
            workspace.mkdir()  # 新增代码+Phase15ChromePairingTrigger: 创建 workspace 目录；如果没有这行代码，后续状态路径没有根目录。
            bridge_path = workspace / "memory" / "chrome_extension_bridge.json"  # 新增代码+Phase15ChromePairingTrigger: 定位预期 bridge 文件；如果没有这行代码，无法验证 preview 不写入。
            text = run_chrome_terminal_command(workspace, "/chrome pairing-preview")  # 新增代码+Phase15ChromePairingTrigger: 执行只读预览命令；如果没有这行代码，无法验证终端入口。
            self.assertIn("chrome_pairing_preview", text)  # 新增代码+Phase15ChromePairingTrigger: 输出必须标明预览动作；如果没有这行断言，未知命令也可能误通过。
            self.assertIn("dry_run=true", text)  # 新增代码+Phase15ChromePairingTrigger: 输出必须说明没有写入；如果没有这行断言，用户无法确认安全边界。
            self.assertIn("pairing_request_id=", text)  # 新增代码+Phase15ChromePairingTrigger: 预览必须显示请求形状；如果没有这行断言，后续确认命令没有可理解目标。
            self.assertFalse(bridge_path.exists())  # 新增代码+Phase15ChromePairingTrigger: preview 不应创建 bridge 文件；如果没有这行断言，安全预览可能偷偷改状态。

    def test_pairing_start_confirm_writes_pending_request_and_status(self) -> None:  # 新增代码+Phase15ChromePairingTrigger: 验证强确认会写入待配对请求并进入状态页；如果没有这段测试，/chrome 看不到触发结果。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase15ChromePairingTrigger: 创建临时目录；如果没有这行代码，测试会污染真实 bridge。
            workspace = Path(temp_dir) / "learning_agent"  # 新增代码+Phase15ChromePairingTrigger: 模拟真实 learning_agent workspace；如果没有这行代码，bridge 路径可能测错。
            workspace.mkdir()  # 新增代码+Phase15ChromePairingTrigger: 创建 workspace；如果没有这行代码，状态文件无法落盘。
            text = run_chrome_terminal_command(workspace, "/chrome pairing-start-confirm I_UNDERSTAND_PAIR_CHROME")  # 新增代码+Phase15ChromePairingTrigger: 执行强确认配对触发；如果没有这行代码，无法证明终端命令会写 pending request。
            self.assertIn("chrome_pairing_start_confirm", text)  # 新增代码+Phase15ChromePairingTrigger: 输出必须标明确认动作；如果没有这行断言，preview 或未知命令可能误通过。
            self.assertIn("pending_pairing_request_status=pending", text)  # 新增代码+Phase15ChromePairingTrigger: 输出必须显示请求等待扩展处理；如果没有这行断言，用户不知道下一步是否已发起。
            bridge_path = workspace / "memory" / "chrome_extension_bridge.json"  # 新增代码+Phase15ChromePairingTrigger: 定位真实 bridge 状态文件；如果没有这行代码，无法读取落盘内容。
            state = json.loads(bridge_path.read_text(encoding="utf-8"))  # 新增代码+Phase15ChromePairingTrigger: 读取 bridge JSON；如果没有这行代码，无法验证 durable 状态。
            request = state.get("pending_pairing_request", {})  # 新增代码+Phase15ChromePairingTrigger: 取待配对请求对象；如果没有这行代码，断言会重复路径。
            self.assertEqual(request.get("status"), "pending")  # 新增代码+Phase15ChromePairingTrigger: 写入后必须是 pending；如果没有这行断言，状态机可能无效。
            self.assertTrue(str(request.get("request_id", "")).startswith("chrome-pair-"))  # 新增代码+Phase15ChromePairingTrigger: request id 必须稳定可识别；如果没有这行断言，状态审计无法区分请求。
            snapshot = build_status_snapshot(workspace)  # 新增代码+Phase15ChromePairingTrigger: 构建统一状态快照；如果没有这行代码，无法证明 /chrome 事实源已接入。
            extension = snapshot["browser"]["provider_status"]["chrome_extension"]  # 新增代码+Phase15ChromePairingTrigger: 取 extension 状态区块；如果没有这行代码，断言路径会分散。
            self.assertEqual(extension["pending_pairing_request_status"], "pending")  # 新增代码+Phase15ChromePairingTrigger: 快照必须显示 pending；如果没有这行断言，状态 UI 会看不到触发结果。
            chrome_text = run_chrome_terminal_command(workspace, "/chrome")  # 新增代码+Phase15ChromePairingTrigger: 渲染真实 /chrome 状态页；如果没有这行代码，无法证明用户可见。
            self.assertIn("pending_pairing_request_status=pending", chrome_text)  # 新增代码+Phase15ChromePairingTrigger: /chrome 必须显示待配对请求；如果没有这行断言，用户仍然不知道触发链路状态。

    def test_bridge_marks_pending_pairing_request_completed_when_pairing_matches(self) -> None:  # 新增代码+Phase15ChromePairingTrigger: 验证扩展回传匹配 request 后关闭 pending；如果没有这段测试，session sync 会一直显示待处理。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+Phase15ChromePairingTrigger: 创建临时目录；如果没有这行代码，测试会污染真实状态。
            bridge = ChromeExtensionBridgeState(Path(temp_dir) / "chrome_extension_bridge.json")  # 新增代码+Phase15ChromePairingTrigger: 创建 bridge 状态对象；如果没有这行代码，无法直接测状态机。
            request = bridge.start_pairing_request(source="unit-test")  # 新增代码+Phase15ChromePairingTrigger: 发起待配对请求；如果没有这行代码，record_pairing 没有 pending 对象可匹配。
            bridge.record_pairing({"request_id": request["request_id"], "device_id": "device-1", "session_id": "session-1", "extension_id": "ext-1", "allowed_origins": ["chrome-extension://ext-1/"]})  # 新增代码+Phase15ChromePairingTrigger: 模拟扩展带 request id 回传配对；如果没有这行代码，无法验证 completed 状态。
            summary = bridge.pairing_request_summary()  # 新增代码+Phase15ChromePairingTrigger: 读取配对请求摘要；如果没有这行代码，无法断言状态机结果。
            self.assertEqual(summary["status"], "completed")  # 新增代码+Phase15ChromePairingTrigger: 匹配配对后必须完成；如果没有这行断言，pending 会永久挂起。

    def test_extension_script_reacts_to_pairing_request_from_poll(self) -> None:  # 新增代码+Phase15ChromePairingTrigger: 验证扩展脚本能处理 host 轮询返回的 pairing_request；如果没有这段测试，Python 绿但真实插件不会配对。
        background_text = (Path(__file__).resolve().parents[1] / "chrome_extension" / "background.js").read_text(encoding="utf-8")  # 新增代码+Phase15ChromePairingTrigger: 读取扩展后台脚本；如果没有这行代码，无法检查真实插件实现。
        self.assertIn("pairing_request", background_text)  # 新增代码+Phase15ChromePairingTrigger: 脚本必须识别 pairing_request；如果没有这行断言，host 下发请求不会触发扩展动作。
        self.assertIn("request_nonce", background_text)  # 新增代码+Phase15ChromePairingTrigger: 脚本必须携带 nonce；如果没有这行断言，配对请求无法审计和防混淆。


if __name__ == "__main__":  # 新增代码+Phase15ChromePairingTrigger: 允许直接运行本测试文件；如果没有这行代码，初学者不能单独执行本阶段测试。
    unittest.main()  # 新增代码+Phase15ChromePairingTrigger: 启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
