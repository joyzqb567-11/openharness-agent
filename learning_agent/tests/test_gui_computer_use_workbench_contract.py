import json  # 新增代码+DesktopGUIComputerUseWorkbenchTest：解析和序列化 JSON payload；如果没有这行代码，测试无法检查字段泄漏。
import tempfile  # 新增代码+DesktopGUIComputerUseWorkbenchTest：创建隔离工作区；如果没有这行代码，测试会污染真实 memory 目录。
import threading  # 新增代码+DesktopGUIComputerUseWorkbenchTest：后台启动 GUI bridge server；如果没有这行代码，HTTP 路由测试会阻塞。
import unittest  # 新增代码+DesktopGUIComputerUseWorkbenchTest：使用 unittest 承载后端合同测试；如果没有这行代码，标准测试命令不会收集本文件。
import urllib.error  # 新增代码+DesktopGUIComputerUseWorkbenchTest：读取未授权 HTTP 错误；如果没有这行代码，token 门禁无法断言响应。
import urllib.request  # 新增代码+DesktopGUIComputerUseWorkbenchTest：使用标准库请求本地 bridge；如果没有这行代码，HTTP 合同无法自动验证。
from pathlib import Path  # 新增代码+DesktopGUIComputerUseWorkbenchTest：使用 Path 管理临时路径；如果没有这行代码，Windows 路径拼接容易出错。
from unittest.mock import patch  # 新增代码+DesktopGUIComputerUseWorkbenchTest：隔离 request_access 的桌面环境依赖；如果没有这行代码，测试会受当前打开窗口影响。

from learning_agent.app.gui_computer_use import build_gui_computer_use_action_payload, build_gui_computer_use_workbench_payload  # 新增代码+DesktopGUIComputerUseWorkbenchTest：导入被测 Computer Use GUI 适配器；如果没有这行代码，测试没有后端目标。
from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DesktopGUIComputerUseWorkbenchTest：复用真实状态事件 store；如果没有这行代码，最近观察/动作只能靠假字典。


class GuiComputerUseWorkbenchContractTests(unittest.TestCase):  # 新增代码+DesktopGUIComputerUseWorkbenchTest：测试类段开始，锁定 Computer Use 工作台后端合同；如果没有这个类，GUI 适配器漂移不会被发现。
    def _fake_access_report(self) -> dict[str, object]:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：helper 段开始，返回稳定 request_access 报告；如果没有这段，每个测试都要重复同一份安全响应。
        return {"access_request_created": True, "grant_created": False, "denied_requested_apps": [], "safe_app_hints": [{"app": "Notepad"}]}  # 新增代码+DesktopGUIComputerUseWorkbenchTest：模拟只读授权申请结果；如果没有这行代码，测试无法脱离真实桌面窗口。
    # 新增代码+DesktopGUIComputerUseWorkbenchTest：helper 段结束，_fake_access_report 到此结束；如果没有边界说明，用户不容易看出它只负责测试夹具。

    def _start_server(self, workspace: Path):  # 新增代码+DesktopGUIComputerUseWorkbenchTest：helper 段开始，启动带 token 的 bridge；如果没有这段，HTTP 测试会重复端口和线程逻辑。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIComputerUseWorkbenchTest：导入真实 GUI bridge server；如果没有这行代码，路由测试无法启动目标。

        server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUIComputerUseWorkbenchTest：绑定随机端口并固定 token；如果没有这行代码，测试可能端口冲突。
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：创建后台服务线程；如果没有这行代码，urlopen 会连接不到 server。
        thread.start()  # 新增代码+DesktopGUIComputerUseWorkbenchTest：启动 HTTP 服务；如果没有这行代码，后续请求会失败。
        return server  # 新增代码+DesktopGUIComputerUseWorkbenchTest：返回 server 供测试关闭；如果没有这行代码，调用方拿不到端口。
    # 新增代码+DesktopGUIComputerUseWorkbenchTest：helper 段结束，_start_server 到此结束；如果没有边界说明，用户不容易看出它只负责启动服务。

    def _url(self, server, path: str) -> str:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：helper 段开始，拼接测试 URL；如果没有这段，随机端口读取会散落重复。
        host, port = server.server_address  # 新增代码+DesktopGUIComputerUseWorkbenchTest：读取 server 实际地址；如果没有这行代码，port=0 场景无法请求。
        return f"http://{host}:{port}{path}"  # 新增代码+DesktopGUIComputerUseWorkbenchTest：返回完整 URL；如果没有这行代码，urllib 没有目标地址。
    # 新增代码+DesktopGUIComputerUseWorkbenchTest：helper 段结束，_url 到此结束；如果没有边界说明，用户不容易看出它只负责拼接 URL。

    def _post_json(self, server, path: str, body: dict[str, object] | None = None) -> dict[str, object]:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：helper 段开始，发送带 token 的 JSON POST；如果没有这段，三个 endpoint 测试会重复认证逻辑。
        request = urllib.request.Request(self._url(server, path), data=json.dumps(body or {}).encode("utf-8"), method="POST", headers={"Content-Type": "application/json", "X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUIComputerUseWorkbenchTest：构造认证 POST 请求；如果没有这行代码，bridge 会按未授权拒绝。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：发送请求并读取响应；如果没有这行代码，测试不会真正触发 handler。
            return json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIComputerUseWorkbenchTest：解析 JSON 响应；如果没有这行代码，断言无法读取字段。
    # 新增代码+DesktopGUIComputerUseWorkbenchTest：helper 段结束，_post_json 到此结束；如果没有边界说明，用户不容易看出它只负责认证 POST。

    def test_workbench_payload_reuses_status_events_and_hides_internal_paths(self) -> None:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：测试段开始，验证 workbench payload 字段和脱敏；如果没有这段，GUI 可能暴露 state_path 或丢最近观察。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：创建临时 workspace；如果没有这行代码，事件测试会污染真实项目。
            workspace = Path(directory)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：把临时目录转成 Path；如果没有这行代码，store 路径会不稳定。
            status_store = StatusEventStore(workspace / "memory" / "status")  # 新增代码+DesktopGUIComputerUseWorkbenchTest：创建真实事件 store；如果没有这行代码，最近观察没有事实源。
            status_store.append("computer_use_observe", {"tool_name": "mcp__computer-use__observe", "message": "屏幕已观察", "low_level_event_count": 0})  # 新增代码+DesktopGUIComputerUseWorkbenchTest：写入观察事件；如果没有这行代码，last_observation 空态无法验证。
            status_store.append("tool_result_seen", {"tool_name": "普通工具", "message": "不应该污染 Computer Use"})  # 新增代码+DesktopGUIComputerUseWorkbenchTest：写入普通工具结果；如果没有这行代码，泛用事件过滤回归不会被发现。
            payload = build_gui_computer_use_workbench_payload(workspace)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：构建工作台 payload；如果没有这行代码，无法验证后端合同。
        serialized = json.dumps(payload, ensure_ascii=False)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：序列化 payload 方便查内部路径；如果没有这行代码，泄漏断言会重复转换。
        self.assertEqual(payload["permission_mode"], "manual")  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认权限模式为手动；如果没有这行断言，危险动作可能被误理解为自动执行。
        self.assertIs(payload["abort_available"], True)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认中止入口可用；如果没有这行断言，前端可能隐藏急停按钮。
        self.assertIn("allowed_action_classes", payload)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认允许动作字段存在；如果没有这行断言，面板无法展示模式范围。
        self.assertEqual(payload["last_observation"]["message"], "屏幕已观察")  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认最近观察来自 Computer Use 事件；如果没有这行断言，普通事件可能污染摘要。
        self.assertNotIn("不应该污染", json.dumps(payload["last_action_result"], ensure_ascii=False))  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认普通工具结果没有污染最近动作；如果没有这行断言，用户会看到错误来源。
        self.assertNotIn("state_path", serialized)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认内部状态路径不泄漏；如果没有这行断言，本机文件路径可能进入 GUI。
    # 新增代码+DesktopGUIComputerUseWorkbenchTest：测试段结束，payload 脱敏合同到此结束；如果没有边界说明，用户不容易看出覆盖范围。

    def test_action_payloads_open_observe_mode_and_abort_without_low_level_events(self) -> None:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：测试段开始，验证申请、观察、中止动作合同；如果没有这段，按钮可能绕开既有 mode store。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：创建临时 workspace；如果没有这行代码，动作测试会污染真实模式状态。
            workspace = Path(directory)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：把临时目录转成 Path；如果没有这行代码，mode store 路径不稳定。
            with patch("learning_agent.app.gui_computer_use.request_computer_use_access", return_value=self._fake_access_report()):  # 新增代码+DesktopGUIComputerUseWorkbenchTest：打桩 request_access；如果没有这行代码，测试会受当前桌面窗口影响。
                request_payload = build_gui_computer_use_action_payload("request-access", workspace, {"apps": ["Notepad"]})  # 新增代码+DesktopGUIComputerUseWorkbenchTest：执行申请权限动作；如果没有这行代码，无法验证 request-access 响应。
            observe_payload = build_gui_computer_use_action_payload("observe", workspace, {})  # 新增代码+DesktopGUIComputerUseWorkbenchTest：执行只读观察刷新；如果没有这行代码，无法验证 observe 响应。
            abort_payload = build_gui_computer_use_action_payload("abort", workspace, {})  # 新增代码+DesktopGUIComputerUseWorkbenchTest：执行中止动作；如果没有这行代码，无法验证 abort 响应。
        self.assertEqual(request_payload["status"], "accepted")  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认申请进入 accepted；如果没有这行断言，前端无法显示成功状态。
        self.assertEqual(request_payload["computer_use"]["mode"], "observe")  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认申请只打开 observe 模式；如果没有这行断言，GUI 可能误开 full 控制。
        self.assertEqual(observe_payload["status"], "observed")  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认观察刷新成功；如果没有这行断言，观察按钮语义不清。
        self.assertEqual(abort_payload["status"], "stopped")  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认中止进入 stopped；如果没有这行断言，急停按钮可能无效。
        self.assertIs(abort_payload["computer_use"]["stopped"], True)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认 stopped 状态进入 workbench；如果没有这行断言，右栏可能仍显示可用。
        self.assertEqual(request_payload["low_level_event_count"], 0)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认申请不产生鼠标键盘事件；如果没有这行断言，安全验收没有事实依据。
        self.assertEqual(observe_payload["low_level_event_count"], 0)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认观察不产生鼠标键盘事件；如果没有这行断言，只读语义可能回归。
        self.assertEqual(abort_payload["low_level_event_count"], 0)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认中止只写状态不执行低层动作；如果没有这行断言，用户无法放心点击急停。
    # 新增代码+DesktopGUIComputerUseWorkbenchTest：测试段结束，动作 payload 合同到此结束；如果没有边界说明，用户不容易看出安全动作范围。

    def test_computer_use_http_routes_require_token_and_return_v2_payloads(self) -> None:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：测试段开始，验证三个 HTTP endpoint 和 token 门禁；如果没有这段，Electron 按钮可能收到 404 或未授权形状漂移。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：创建临时 workspace；如果没有这行代码，HTTP 测试会污染真实 memory。
            workspace = Path(directory)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：规范化 workspace；如果没有这行代码，server 构造会收到裸字符串。
            server = self._start_server(workspace)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：启动真实 bridge；如果没有这行代码，HTTP 路由无法验收。
            try:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确保 server 最终关闭；如果没有这行代码，失败时端口会残留。
                missing = urllib.request.Request(self._url(server, "/v2/gui/computer-use/observe"), data=b"{}", method="POST", headers={"Content-Type": "application/json"})  # 新增代码+DesktopGUIComputerUseWorkbenchTest：构造缺 token 请求；如果没有这行代码，无法验证门禁。
                with self.assertRaises(urllib.error.HTTPError) as rejected:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：断言缺 token 被拒；如果没有这行代码，未授权访问可能误过。
                    urllib.request.urlopen(missing, timeout=5)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：发送缺 token 请求；如果没有这行代码，拒绝路径不会执行。
                with patch("learning_agent.app.gui_computer_use.request_computer_use_access", return_value=self._fake_access_report()):  # 新增代码+DesktopGUIComputerUseWorkbenchTest：打桩桌面授权申请；如果没有这行代码，测试可能依赖当前窗口清单。
                    request_access = self._post_json(server, "/v2/gui/computer-use/request-access", {"mode": "observe"})  # 新增代码+DesktopGUIComputerUseWorkbenchTest：请求申请权限 endpoint；如果没有这行代码，无法验证路由。
                observe = self._post_json(server, "/v2/gui/computer-use/observe")  # 新增代码+DesktopGUIComputerUseWorkbenchTest：请求观察 endpoint；如果没有这行代码，无法验证路由。
                abort = self._post_json(server, "/v2/gui/computer-use/abort")  # 新增代码+DesktopGUIComputerUseWorkbenchTest：请求中止 endpoint；如果没有这行代码，无法验证路由。
            finally:  # 新增代码+DesktopGUIComputerUseWorkbenchTest：清理 server；如果没有这行代码，测试进程可能挂住。
                server.shutdown()  # 新增代码+DesktopGUIComputerUseWorkbenchTest：停止 serve_forever；如果没有这行代码，后台线程可能继续运行。
                server.server_close()  # 新增代码+DesktopGUIComputerUseWorkbenchTest：释放 socket；如果没有这行代码，Windows 随机端口可能残留。
        self.assertEqual(rejected.exception.code, 401)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认缺 token 状态码为 401；如果没有这行断言，本机安全边界可能失效。
        self.assertIs(request_access["ok"], True)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认 request-access 返回成功形状；如果没有这行断言，前端无法消费 payload。
        self.assertEqual(request_access["schema_version"], 2)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认 V2 协议版本；如果没有这行断言，client 类型可能漂移。
        self.assertEqual(observe["action"], "observe")  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认 observe action 字段；如果没有这行断言，前端无法解释按钮结果。
        self.assertEqual(abort["action"], "abort")  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认 abort action 字段；如果没有这行断言，中止反馈可能错位。
        self.assertIn("computer_use", abort)  # 新增代码+DesktopGUIComputerUseWorkbenchTest：确认动作响应携带最新 workbench；如果没有这行断言，前端需要额外请求刷新。
    # 新增代码+DesktopGUIComputerUseWorkbenchTest：测试段结束，HTTP 路由合同到此结束；如果没有边界说明，用户不容易看出三条路由覆盖范围。


if __name__ == "__main__":  # 新增代码+DesktopGUIComputerUseWorkbenchTest：允许直接运行本文件；如果没有这行代码，手动调试时不会进入 unittest。
    unittest.main()  # 新增代码+DesktopGUIComputerUseWorkbenchTest：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
