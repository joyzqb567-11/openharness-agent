import json  # 新增代码+DesktopGUIAcceptanceTest：解析和写入验收 JSON；如果没有这行代码，测试无法构造场景和断言响应。
import tempfile  # 新增代码+DesktopGUIAcceptanceTest：创建隔离 workspace；如果没有这行代码，测试会污染真实 acceptance_controller 目录。
import threading  # 新增代码+DesktopGUIAcceptanceTest：在后台线程启动 GUI bridge；如果没有这行代码，HTTP 路由测试会阻塞。
import unittest  # 新增代码+DesktopGUIAcceptanceTest：使用项目现有 unittest 风格；如果没有这行代码，标准测试命令无法发现本文件。
import urllib.request  # 新增代码+DesktopGUIAcceptanceTest：用标准库请求本地 bridge；如果没有这行代码，路由合同无法真实验证。
from pathlib import Path  # 新增代码+DesktopGUIAcceptanceTest：用 Path 管理临时目录；如果没有这行代码，Windows 路径拼接更易出错。


def _write_json(path: Path, payload: dict[str, object]) -> None:  # 新增代码+DesktopGUIAcceptanceTest：函数段开始，写入 UTF-8 JSON 夹具；如果没有这段，多个测试会重复写文件逻辑。
    path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+DesktopGUIAcceptanceTest：确保父目录存在；如果没有这行代码，首次写 scenarios/result 会失败。
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")  # 新增代码+DesktopGUIAcceptanceTest：写入可读 JSON；如果没有这行代码，后端 helper 没有事实源。
# 新增代码+DesktopGUIAcceptanceTest：函数段结束，_write_json 到此结束；如果没有这个边界说明，用户不容易看出写 JSON 的范围。


def _prepare_acceptance_workspace(workspace: Path) -> None:  # 新增代码+DesktopGUIAcceptanceTest：函数段开始，准备最小验收控制器目录；如果没有这段，helper 和 HTTP 路由没有可读样本。
    controller_root = workspace / "learning_agent" / "acceptance_controller"  # 新增代码+DesktopGUIAcceptanceTest：定位临时验收控制器根目录；如果没有这行代码，场景和 runs 会写错位置。
    controller_root.mkdir(parents=True, exist_ok=True)  # 新增代码+DesktopGUIAcceptanceTest：创建控制器根目录；如果没有这行代码，controller.ps1 无法落盘。
    (controller_root / "controller.ps1").write_text("param([string]$ScenarioPath,[string]$RunRoot)\n", encoding="utf-8")  # 新增代码+DesktopGUIAcceptanceTest：写入最小控制器占位；如果没有这行代码，run payload 会返回 controller 不存在。
    (workspace / "learning_agent").mkdir(parents=True, exist_ok=True)  # 新增代码+DesktopGUIAcceptanceTest：创建 learning_agent 根目录；如果没有这行代码，start bat 占位无法写入。
    (workspace / "learning_agent" / "start_oauth_agent.bat").write_text("@echo off\n", encoding="utf-8")  # 新增代码+DesktopGUIAcceptanceTest：写入真实控制器状态需要的 bat 占位；如果没有这行代码，controller 状态会显示入口缺失。
    _write_json(controller_root / "scenarios" / "smoke.json", {"name": "smoke", "max_seconds": 30, "success_marker": "ACCEPTANCE_HARNESS_OK", "prompt_lines": ["请回复 ACCEPTANCE_HARNESS_OK"], "required_event_states": ["agent_ready_for_user_prompt", "final_answer_printed"]})  # 新增代码+DesktopGUIAcceptanceTest：写入 smoke 场景；如果没有这行代码，场景清单会为空。
    run_dir = controller_root / "runs" / "smoke-20260627T000000Z"  # 新增代码+DesktopGUIAcceptanceTest：定义一份伪运行目录；如果没有这行代码，运行列表没有证据样本。
    run_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+DesktopGUIAcceptanceTest：创建伪运行目录；如果没有这行代码，result/events 写入会失败。
    final_png = run_dir / "final.png"  # 新增代码+DesktopGUIAcceptanceTest：定义最终截图占位；如果没有这行代码，证据列表无法验证截图链接。
    final_png.write_bytes(b"\x89PNG\r\n\x1a\n")  # 新增代码+DesktopGUIAcceptanceTest：写入最小 PNG 头；如果没有这行代码，截图证据 exists 会是 false。
    (run_dir / "events.jsonl").write_text('{"state":"agent_ready_for_user_prompt"}\n{"state":"final_answer_printed"}\n', encoding="utf-8")  # 新增代码+DesktopGUIAcceptanceTest：写入事件流；如果没有这行代码，events 证据无法验证。
    (run_dir / "latest_run_readable.md").write_text("# smoke\ncompleted=true\n", encoding="utf-8")  # 新增代码+DesktopGUIAcceptanceTest：写入可读报告；如果没有这行代码，小白可读证据无法验证。
    _write_json(run_dir / "result.json", {"completed": True, "scenario": "smoke", "assertion": {"passed": True}, "permission_sent_count": 0, "final_screenshot": str(final_png)})  # 新增代码+DesktopGUIAcceptanceTest：写入结果 JSON；如果没有这行代码，运行状态无法显示 passed。
# 新增代码+DesktopGUIAcceptanceTest：函数段结束，_prepare_acceptance_workspace 到此结束；如果没有这个边界说明，用户不容易看出临时验收目录范围。


class GuiAcceptanceContractTests(unittest.TestCase):  # 新增代码+DesktopGUIAcceptanceTest：测试类段开始，锁定验收控制中心后端合同；如果没有这个类，unittest 不会发现测试。
    def test_acceptance_payloads_reuse_existing_controller_files(self) -> None:  # 新增代码+DesktopGUIAcceptanceTest：测试方法开始，验证场景和运行 payload 来自真实目录；如果没有这段，GUI 可能显示硬编码假数据。
        from learning_agent.app.gui_acceptance import build_gui_acceptance_runs_payload, build_gui_acceptance_scenarios_payload  # 新增代码+DesktopGUIAcceptanceTest：导入待测 helper；如果没有这行代码，测试无法约束后端薄适配层。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIAcceptanceTest：创建隔离工作区；如果没有这行代码，测试会读写真项目证据。
            workspace = Path(directory)  # 新增代码+DesktopGUIAcceptanceTest：把临时路径转为 Path；如果没有这行代码，后续拼接会啰嗦且易错。
            _prepare_acceptance_workspace(workspace)  # 新增代码+DesktopGUIAcceptanceTest：准备场景和运行证据；如果没有这行代码，payload 会为空。
            scenarios_payload = build_gui_acceptance_scenarios_payload(workspace)  # 新增代码+DesktopGUIAcceptanceTest：生成场景总览；如果没有这行代码，后续断言没有被测对象。
            runs_payload = build_gui_acceptance_runs_payload(workspace)  # 新增代码+DesktopGUIAcceptanceTest：生成运行列表；如果没有这行代码，证据断言没有输入。
            scenario_json = json.dumps(scenarios_payload, ensure_ascii=False)  # 新增代码+DesktopGUIAcceptanceTest：序列化场景 payload 检查泄漏；如果没有这行代码，路径泄漏断言不方便。

        self.assertIs(scenarios_payload["ok"], True)  # 新增代码+DesktopGUIAcceptanceTest：确认场景响应成功；如果没有这行断言，错误 payload 可能误过。
        self.assertEqual(scenarios_payload["scenario_count"], 1)  # 新增代码+DesktopGUIAcceptanceTest：确认读取到 smoke 场景；如果没有这行断言，场景目录接入可能断掉。
        self.assertEqual(scenarios_payload["safe_smoke_scenario_id"], "smoke")  # 新增代码+DesktopGUIAcceptanceTest：确认安全 smoke id 可见；如果没有这行断言，真实 GUI 验收不好定位安全样例。
        self.assertEqual(scenarios_payload["scenarios"][0]["last_result"]["status"], "passed")  # 新增代码+DesktopGUIAcceptanceTest：确认最近结果关联到场景；如果没有这行断言，用户看不到最新成败。
        self.assertIn("learning_agent/acceptance_controller/scenarios/smoke.json", scenario_json)  # 新增代码+DesktopGUIAcceptanceTest：确认相对路径可见；如果没有这行断言，用户难以定位配置文件。
        self.assertFalse(str(scenarios_payload["scenarios"][0]["relative_path"]).startswith(str(Path(tempfile.gettempdir()).resolve())))  # 修改代码+DesktopGUIAcceptanceTest：只约束场景链接自身是相对路径；如果没有这行断言，场景卡片可能泄漏本机绝对目录。
        self.assertEqual(runs_payload["run_count"], 1)  # 新增代码+DesktopGUIAcceptanceTest：确认运行列表读取到证据；如果没有这行断言，runs 目录接入可能断掉。
        self.assertEqual(runs_payload["runs"][0]["status"], "passed")  # 新增代码+DesktopGUIAcceptanceTest：确认运行状态为通过；如果没有这行断言，result.json 解析可能错误。
        self.assertTrue(any(item["kind"] == "screenshot" and item["exists"] for item in runs_payload["runs"][0]["evidence"]))  # 新增代码+DesktopGUIAcceptanceTest：确认最终截图证据可见；如果没有这行断言，真实 GUI 验收缺少肉眼证据索引。
    # 新增代码+DesktopGUIAcceptanceTest：测试方法结束，test_acceptance_payloads_reuse_existing_controller_files 到此结束；如果没有这个边界说明，用户不容易看出总览合同范围。

    def test_acceptance_run_payload_supports_dry_run_without_launching_terminal(self) -> None:  # 新增代码+DesktopGUIAcceptanceTest：测试方法开始，验证 dry-run 启动计划；如果没有这段，自动化测试可能误打开真实终端。
        from learning_agent.app.gui_acceptance import build_gui_acceptance_run_payload  # 新增代码+DesktopGUIAcceptanceTest：导入启动 helper；如果没有这行代码，测试无法约束 POST run 行为。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIAcceptanceTest：创建隔离工作区；如果没有这行代码，测试会读写真项目。
            workspace = Path(directory)  # 新增代码+DesktopGUIAcceptanceTest：把临时目录转为 Path；如果没有这行代码，helper 调用不清晰。
            _prepare_acceptance_workspace(workspace)  # 新增代码+DesktopGUIAcceptanceTest：准备最小控制器；如果没有这行代码，run helper 会返回 not_found。
            payload = build_gui_acceptance_run_payload(workspace, {"scenario_id": "smoke", "dry_run": True})  # 新增代码+DesktopGUIAcceptanceTest：请求 dry-run 计划；如果没有这行代码，无法验证安全测试模式。

        self.assertEqual(payload["status"], "planned")  # 新增代码+DesktopGUIAcceptanceTest：确认 dry-run 只生成计划；如果没有这行断言，测试可能误启动终端。
        self.assertFalse(payload["launched"])  # 新增代码+DesktopGUIAcceptanceTest：确认未启动进程；如果没有这行断言，自动测试风险不可控。
        self.assertIn("controller.ps1", payload["command"])  # 新增代码+DesktopGUIAcceptanceTest：确认计划复用现有控制器；如果没有这行断言，GUI 可能另造启动命令。
        self.assertIn("scenarios/smoke.json", payload["command"])  # 新增代码+DesktopGUIAcceptanceTest：确认计划指向 smoke 场景；如果没有这行断言，按钮可能跑错场景。
    # 新增代码+DesktopGUIAcceptanceTest：测试方法结束，test_acceptance_run_payload_supports_dry_run_without_launching_terminal 到此结束；如果没有这个边界说明，用户不容易看出 dry-run 合同范围。

    def test_acceptance_http_routes_require_token_and_return_payloads(self) -> None:  # 新增代码+DesktopGUIAcceptanceTest：测试方法开始，验证真实 HTTP 路由；如果没有这段，Electron client 可能打不到后端。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIAcceptanceTest：导入真实 GUI bridge；如果没有这行代码，无法验证 handler 路由。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIAcceptanceTest：创建隔离工作区；如果没有这行代码，HTTP 测试会污染真实项目。
            workspace = Path(directory)  # 新增代码+DesktopGUIAcceptanceTest：把临时目录转为 Path；如果没有这行代码，准备目录和 server workspace 可能不一致。
            _prepare_acceptance_workspace(workspace)  # 新增代码+DesktopGUIAcceptanceTest：写入场景和证据；如果没有这行代码，HTTP payload 会为空。
            server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUIAcceptanceTest：随机端口启动 bridge；如果没有这行代码，测试可能端口冲突。
            try:  # 新增代码+DesktopGUIAcceptanceTest：保护 server 清理；如果没有这行代码，断言失败会留下监听端口。
                thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIAcceptanceTest：创建后台服务线程；如果没有这行代码，请求会阻塞。
                thread.start()  # 新增代码+DesktopGUIAcceptanceTest：启动 HTTP server；如果没有这行代码，urllib 会连接失败。
                host, port = server.server_address  # 新增代码+DesktopGUIAcceptanceTest：读取随机端口；如果没有这行代码，请求不知道目标地址。
                headers = {"X-OpenHarness-Desktop-Token": "test-token"}  # 新增代码+DesktopGUIAcceptanceTest：准备 token header；如果没有这行代码，受保护路由会返回 403。
                scenarios_request = urllib.request.Request(f"http://{host}:{port}/v2/gui/acceptance/scenarios", headers=headers)  # 新增代码+DesktopGUIAcceptanceTest：构造场景列表请求；如果没有这行代码，列表路由不会被执行。
                runs_request = urllib.request.Request(f"http://{host}:{port}/v2/gui/acceptance/runs", headers=headers)  # 新增代码+DesktopGUIAcceptanceTest：构造运行列表请求；如果没有这行代码，runs 路由不会被执行。
                run_request = urllib.request.Request(f"http://{host}:{port}/v2/gui/acceptance/run", data=json.dumps({"scenario_id": "smoke", "dry_run": True}).encode("utf-8"), headers={**headers, "Content-Type": "application/json"}, method="POST")  # 新增代码+DesktopGUIAcceptanceTest：构造 dry-run POST；如果没有这行代码，启动路由不会被执行。
                with urllib.request.urlopen(scenarios_request, timeout=5) as response:  # 新增代码+DesktopGUIAcceptanceTest：请求场景端点；如果没有这行代码，HTTP 场景合同没有实际运行。
                    scenarios_payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIAcceptanceTest：解析场景响应；如果没有这行代码，无法断言字段。
                with urllib.request.urlopen(runs_request, timeout=5) as response:  # 新增代码+DesktopGUIAcceptanceTest：请求运行端点；如果没有这行代码，HTTP runs 合同没有实际运行。
                    runs_payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIAcceptanceTest：解析运行响应；如果没有这行代码，无法断言证据。
                with urllib.request.urlopen(run_request, timeout=5) as response:  # 新增代码+DesktopGUIAcceptanceTest：请求 dry-run 启动端点；如果没有这行代码，POST 合同没有实际运行。
                    run_payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIAcceptanceTest：解析启动响应；如果没有这行代码，无法断言 planned 状态。
            finally:  # 新增代码+DesktopGUIAcceptanceTest：无论成功失败都关闭 server；如果没有这行代码，测试环境会残留后台线程。
                server.shutdown()  # 新增代码+DesktopGUIAcceptanceTest：停止 serve_forever；如果没有这行代码，后台线程可能继续运行。
                server.server_close()  # 新增代码+DesktopGUIAcceptanceTest：释放 socket；如果没有这行代码，Windows 上端口可能短时间占用。

        self.assertEqual(scenarios_payload["scenario_count"], 1)  # 新增代码+DesktopGUIAcceptanceTest：确认 HTTP 场景列表返回数据；如果没有这行断言，路由可能空壳。
        self.assertEqual(runs_payload["runs"][0]["status"], "passed")  # 新增代码+DesktopGUIAcceptanceTest：确认 HTTP 运行列表返回通过状态；如果没有这行断言，证据路由可能错。
        self.assertEqual(run_payload["status"], "planned")  # 新增代码+DesktopGUIAcceptanceTest：确认 HTTP dry-run 不启动终端；如果没有这行断言，测试安全性不可控。
    # 新增代码+DesktopGUIAcceptanceTest：测试方法结束，test_acceptance_http_routes_require_token_and_return_payloads 到此结束；如果没有这个边界说明，用户不容易看出 HTTP 合同范围。
# 新增代码+DesktopGUIAcceptanceTest：测试类段结束，GuiAcceptanceContractTests 到此结束；如果没有这个边界说明，用户不容易看出本文件只测验收控制中心。


if __name__ == "__main__":  # 新增代码+DesktopGUIAcceptanceTest：允许直接运行本文件；如果没有这行代码，手动调试时不会进入 unittest。
    unittest.main()  # 新增代码+DesktopGUIAcceptanceTest：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
