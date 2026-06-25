import json  # 新增代码+GuiDiagnosticsTest：读取 release gate fixture；如果没有这行代码，测试无法写入和校验 JSON 结果。
import tempfile  # 新增代码+GuiDiagnosticsTest：创建隔离临时工作区；如果没有这行代码，测试会污染真实项目目录。
import threading  # 新增代码+GuiDiagnosticsTest：启动真实 HTTP bridge 线程；如果没有这行代码，路由测试无法在后台响应请求。
import time  # 新增代码+GuiDiagnosticsTest：构造固定 uptime；如果没有这行代码，健康检查无法验证运行时长。
import unittest  # 新增代码+GuiDiagnosticsTest：使用项目现有 unittest 风格；如果没有这行代码，测试类无法被 python -m unittest 发现。
import urllib.request  # 新增代码+GuiDiagnosticsTest：请求本地 bridge 端点；如果没有这行代码，HTTP 合同只能停留在 helper 层。
from pathlib import Path  # 新增代码+GuiDiagnosticsTest：用跨平台路径对象创建 fixture；如果没有这行代码，Windows 路径拼接容易出错。
from unittest.mock import patch  # 新增代码+GuiDiagnosticsTest：替换状态快照函数；如果没有这行代码，降级分支无法稳定复现。


class GuiDiagnosticsContractTest(unittest.TestCase):  # 新增代码+GuiDiagnosticsTest：测试类段开始，锁定 V2 设置和诊断后端合同；如果没有这段测试，诊断面板可能泄露 token 或本地路径。
    def test_health_payload_contains_schema_uptime_workspace_and_flags(self) -> None:  # 新增代码+GuiDiagnosticsTest：验证健康 payload 基本字段；如果没有这段测试，前端设置页可能拿不到版本、工作区和能力开关。
        from learning_agent.app.gui_diagnostics import build_gui_health_payload  # 新增代码+GuiDiagnosticsTest：导入计划新增的健康 helper；如果没有这行代码，测试没有被测目标。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiDiagnosticsTest：创建临时 workspace；如果没有这行代码，测试会依赖开发者本机目录。
            started_at = time.time() - 12.0  # 新增代码+GuiDiagnosticsTest：伪造已启动 12 秒；如果没有这行代码，uptime 断言会不稳定。
            payload = build_gui_health_payload(Path(directory), started_at=started_at, now=started_at + 12.0)  # 新增代码+GuiDiagnosticsTest：生成健康 payload；如果没有这行代码，后续断言没有输入。

        self.assertTrue(payload["ok"])  # 新增代码+GuiDiagnosticsTest：确认健康端点标记成功；如果没有这行代码，失败 payload 也可能误过测试。
        self.assertGreaterEqual(payload["schema_version"], 2)  # 新增代码+GuiDiagnosticsTest：确认 V2 schema；如果没有这行代码，前端可能接到旧协议。
        self.assertEqual(payload["uptime_seconds"], 12.0)  # 新增代码+GuiDiagnosticsTest：确认 uptime 可预测；如果没有这行代码，诊断页运行时长可能没有事实来源。
        self.assertTrue(str(payload["workspace"]).endswith(Path(directory).name))  # 新增代码+GuiDiagnosticsTest：确认 workspace 来自传入目录；如果没有这行代码，健康检查可能展示错误项目。
        self.assertTrue(payload["feature_flags"]["diagnostics"])  # 新增代码+GuiDiagnosticsTest：确认诊断能力开关存在；如果没有这行代码，前端无法按能力显示面板。

    def test_diagnostics_redacts_token_and_local_secret_paths(self) -> None:  # 新增代码+GuiDiagnosticsTest：验证脱敏函数；如果没有这段测试，诊断包可能把 token 或本地绝对路径暴露给用户。
        from learning_agent.app.gui_diagnostics import redact_diagnostic_text  # 新增代码+GuiDiagnosticsTest：导入脱敏 helper；如果没有这行代码，测试没有被测目标。

        raw = "Bearer sk-test123 X-OpenHarness-Desktop-Token: abc123 C:/Users/joyzq/secret/status.lock H:/codexworkplace/private/token.txt"  # 新增代码+GuiDiagnosticsTest：构造包含 token 和路径的文本；如果没有这行代码，脱敏覆盖不够真实。
        safe = redact_diagnostic_text(raw)  # 新增代码+GuiDiagnosticsTest：执行脱敏；如果没有这行代码，后续断言没有被测结果。

        self.assertNotIn("sk-test123", safe)  # 新增代码+GuiDiagnosticsTest：确认 Bearer token 被移除；如果没有这行代码，密钥泄露可能漏过。
        self.assertNotIn("abc123", safe)  # 新增代码+GuiDiagnosticsTest：确认 header token 被移除；如果没有这行代码，本地 bridge token 可能泄露。
        self.assertNotIn("joyzq", safe)  # 新增代码+GuiDiagnosticsTest：确认用户名路径被移除；如果没有这行代码，本机隐私路径可能泄露。
        self.assertNotIn("codexworkplace", safe)  # 新增代码+GuiDiagnosticsTest：确认工作区绝对路径被移除；如果没有这行代码，诊断包会暴露本地目录结构。
        self.assertIn("[redacted", safe)  # 新增代码+GuiDiagnosticsTest：确认替换痕迹清晰；如果没有这行代码，用户不知道文本已被安全处理。

    def test_diagnostics_payload_degrades_with_safe_message(self) -> None:  # 新增代码+GuiDiagnosticsTest：验证状态快照失败时的安全降级；如果没有这段测试，诊断页可能显示原始异常。
        from learning_agent.app.gui_diagnostics import build_gui_diagnostics_payload  # 新增代码+GuiDiagnosticsTest：导入诊断 payload helper；如果没有这行代码，测试没有被测目标。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiDiagnosticsTest：创建临时 workspace；如果没有这行代码，测试会依赖真实项目目录。
            with patch("learning_agent.app.gui_diagnostics.build_status_snapshot", side_effect=PermissionError("C:/Users/joyzq/secret/status.lock")):  # 新增代码+GuiDiagnosticsTest：模拟快照读取失败且错误含本机路径；如果没有这行代码，降级分支无法稳定覆盖。
                payload = build_gui_diagnostics_payload(Path(directory), bridge_token="abc123", last_error="Bearer sk-secret C:/Users/joyzq/secret")  # 新增代码+GuiDiagnosticsTest：生成降级诊断 payload；如果没有这行代码，后续断言没有输入。

        serialized = json.dumps(payload, ensure_ascii=False)  # 新增代码+GuiDiagnosticsTest：序列化整包做泄露扫描；如果没有这行代码，嵌套字段泄露可能漏过。
        self.assertTrue(payload["status_degraded"])  # 新增代码+GuiDiagnosticsTest：确认降级标记为真；如果没有这行代码，UI 可能误显示正常。
        self.assertEqual(payload["safe_error"], "状态快照暂时不可读。")  # 新增代码+GuiDiagnosticsTest：确认只显示安全文案；如果没有这行代码，原始异常可能进入界面。
        self.assertNotIn("abc123", serialized)  # 新增代码+GuiDiagnosticsTest：确认 bridge token 未进入诊断包；如果没有这行代码，安全边界会退化。
        self.assertNotIn("sk-secret", serialized)  # 新增代码+GuiDiagnosticsTest：确认 last_error 里的密钥被脱敏；如果没有这行代码，错误文本可能泄露凭据。
        self.assertNotIn("joyzq", serialized)  # 新增代码+GuiDiagnosticsTest：确认本机用户名未进入诊断包；如果没有这行代码，路径隐私会泄露。

    def test_diagnostics_reads_last_release_gate_result_when_present(self) -> None:  # 新增代码+GuiDiagnosticsTest：验证最近 release gate 结果读取；如果没有这段测试，诊断页无法展示最后验收状态。
        from learning_agent.app.gui_diagnostics import build_gui_diagnostics_payload  # 新增代码+GuiDiagnosticsTest：导入诊断 payload helper；如果没有这行代码，测试没有被测目标。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiDiagnosticsTest：创建临时 workspace；如果没有这行代码，fixture 会污染真实项目。
            workspace = Path(directory)  # 新增代码+GuiDiagnosticsTest：把临时目录转为 Path；如果没有这行代码，后续路径拼接不清晰。
            gate_path = workspace / "memory" / "gui_bridge" / "release_gate_result.json"  # 新增代码+GuiDiagnosticsTest：使用诊断模块约定位置；如果没有这行代码，测试无法证明读取路径。
            gate_path.parent.mkdir(parents=True)  # 新增代码+GuiDiagnosticsTest：创建 release gate 目录；如果没有这行代码，写入 fixture 会失败。
            gate_path.write_text(json.dumps({"ok": True, "status": "passed", "created_at": "2026-06-25T00:00:00Z", "summary": "all green"}), encoding="utf-8")  # 新增代码+GuiDiagnosticsTest：写入 gate 结果；如果没有这行代码，诊断 payload 只能返回 not_run。
            with patch("learning_agent.app.gui_diagnostics.build_status_snapshot", return_value={"status": {"events": []}}):  # 新增代码+GuiDiagnosticsTest：固定快照成功返回；如果没有这行代码，测试会依赖真实运行状态。
                payload = build_gui_diagnostics_payload(workspace)  # 新增代码+GuiDiagnosticsTest：生成诊断 payload；如果没有这行代码，后续断言没有输入。

        self.assertTrue(payload["release_gate"]["present"])  # 新增代码+GuiDiagnosticsTest：确认识别到 gate 结果；如果没有这行代码，缺失读取也可能误过。
        self.assertEqual(payload["release_gate"]["status"], "passed")  # 新增代码+GuiDiagnosticsTest：确认状态透传；如果没有这行代码，诊断页可能显示错误验收状态。
        self.assertEqual(payload["release_gate"]["summary"], "all green")  # 新增代码+GuiDiagnosticsTest：确认摘要透传；如果没有这行代码，用户看不到最近 gate 结论。

    def test_diagnostics_http_routes_require_token_and_return_safe_payload(self) -> None:  # 新增代码+GuiDiagnosticsTest：验证真实 HTTP 路由；如果没有这段测试，helper 正确但 bridge 未接线也会漏过。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+GuiDiagnosticsTest：导入 HTTP server 构造器；如果没有这行代码，测试无法启动本地 bridge。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiDiagnosticsTest：创建临时 workspace；如果没有这行代码，HTTP 测试会污染真实项目。
            server = create_gui_bridge_server(workspace=Path(directory), host="127.0.0.1", port=0, token="test-token")  # 新增代码+GuiDiagnosticsTest：绑定随机端口并设置 token；如果没有这行代码，测试无法验证鉴权。
            thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+GuiDiagnosticsTest：创建后台 server 线程；如果没有这行代码，请求会无人响应。
            thread.start()  # 新增代码+GuiDiagnosticsTest：启动 HTTP server；如果没有这行代码，urllib 会连接失败。
            host, port = server.server_address  # 新增代码+GuiDiagnosticsTest：读取随机端口；如果没有这行代码，测试不知道请求地址。
            try:  # 新增代码+GuiDiagnosticsTest：保护 server 关闭；如果没有这行代码，失败时后台线程可能残留。
                health_request = urllib.request.Request(f"http://{host}:{port}/v2/gui/health", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+GuiDiagnosticsTest：构造 V2 health 请求；如果没有这行代码，无法验证健康路由。
                with urllib.request.urlopen(health_request, timeout=5) as response:  # 新增代码+GuiDiagnosticsTest：请求 health endpoint；如果没有这行代码，路由接线不会被执行。
                    health_payload = json.loads(response.read().decode("utf-8"))  # 新增代码+GuiDiagnosticsTest：解析 health JSON；如果没有这行代码，后续无法断言字段。
                diagnostics_request = urllib.request.Request(f"http://{host}:{port}/v2/gui/diagnostics", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+GuiDiagnosticsTest：构造 V2 diagnostics 请求；如果没有这行代码，无法验证诊断路由。
                with urllib.request.urlopen(diagnostics_request, timeout=5) as response:  # 新增代码+GuiDiagnosticsTest：请求 diagnostics endpoint；如果没有这行代码，路由接线不会被执行。
                    diagnostics_payload = json.loads(response.read().decode("utf-8"))  # 新增代码+GuiDiagnosticsTest：解析 diagnostics JSON；如果没有这行代码，后续无法断言字段。
            finally:  # 新增代码+GuiDiagnosticsTest：无论请求成功失败都关闭 server；如果没有这行代码，测试进程可能挂住。
                server.shutdown()  # 新增代码+GuiDiagnosticsTest：停止 HTTP server；如果没有这行代码，后台线程会继续监听。
                server.server_close()  # 新增代码+GuiDiagnosticsTest：释放 socket；如果没有这行代码，Windows 上端口资源可能延迟释放。
                thread.join(timeout=5)  # 新增代码+GuiDiagnosticsTest：等待后台线程退出；如果没有这行代码，测试结束时可能还有运行线程。

        self.assertTrue(health_payload["ok"])  # 新增代码+GuiDiagnosticsTest：确认 health 路由返回成功；如果没有这行代码，错误 JSON 也可能误过。
        self.assertTrue(diagnostics_payload["ok"])  # 新增代码+GuiDiagnosticsTest：确认 diagnostics 路由返回成功；如果没有这行代码，错误 JSON 也可能误过。
        self.assertIn("release_gate", diagnostics_payload)  # 新增代码+GuiDiagnosticsTest：确认 HTTP payload 包含 release gate；如果没有这行代码，前端诊断页拿不到验收状态。


if __name__ == "__main__":  # 新增代码+GuiDiagnosticsTest：允许直接运行本测试文件；如果没有这行代码，手动调试需要记住 unittest 命令。
    unittest.main()  # 新增代码+GuiDiagnosticsTest：启动 unittest；如果没有这行代码，直接 python 文件不会执行测试。
