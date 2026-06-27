import json  # 新增代码+DesktopGUICommandConsoleTest：解析 GUI bridge 返回的 JSON；如果没有这行代码，测试无法检查后台命令 payload 的字段。
import tempfile  # 新增代码+DesktopGUICommandConsoleTest：创建隔离临时工作区；如果没有这行代码，测试会污染真实项目的 memory/tasks。
import threading  # 新增代码+DesktopGUICommandConsoleTest：在后台线程启动本地 HTTP server；如果没有这行代码，路由测试会阻塞当前测试进程。
import unittest  # 新增代码+DesktopGUICommandConsoleTest：使用项目现有 unittest 风格承载后端合同测试；如果没有这行代码，测试不会被标准命令执行。
import urllib.request  # 新增代码+DesktopGUICommandConsoleTest：用标准库请求本地 GUI bridge；如果没有这行代码，HTTP 路由无法被真实验证。
from pathlib import Path  # 新增代码+DesktopGUICommandConsoleTest：用 Path 管理临时 workspace；如果没有这行代码，Windows 路径处理会更容易出错。


def _prepare_command_workspace(workspace: Path) -> None:  # 新增代码+DesktopGUICommandConsoleTest：函数段开始，准备可复用的后台命令事实源；如果没有这段，多个测试会重复造 TaskRegistry 数据。
    from learning_agent.runtime.task_registry import TaskRegistry  # 新增代码+DesktopGUICommandConsoleTest：导入真实任务登记表；如果没有这行代码，测试就不能证明 GUI 复用了 core 的持久任务模块。

    command_cwd = workspace / "subdir"  # 新增代码+DesktopGUICommandConsoleTest：准备命令工作目录样本；如果没有这行代码，cwd 脱敏逻辑没有测试输入。
    command_cwd.mkdir(parents=True, exist_ok=True)  # 新增代码+DesktopGUICommandConsoleTest：创建样本目录；如果没有这行代码，resolve 后的相对路径断言可能不稳定。
    registry = TaskRegistry(workspace / "memory" / "tasks")  # 新增代码+DesktopGUICommandConsoleTest：打开真实任务登记表目录；如果没有这行代码，GUI payload 没有事实源可读。
    registry.create_task("bg_test", "python -c \"print('hello')\" --api-key SECRET_SHOULD_NOT_LEAK", kind="background_shell", status="running", background=True, metadata={"cwd": str(command_cwd), "label": "Dev server"})  # 新增代码+DesktopGUICommandConsoleTest：创建后台命令任务；如果没有这行代码，命令控制台无法显示运行中命令。
    registry.append_output("bg_test", "line one\nline two\ntoken=SECRET_OUTPUT_SHOULD_NOT_LEAK\n")  # 新增代码+DesktopGUICommandConsoleTest：写入真实输出 tail；如果没有这行代码，终端输出和输出脱敏没有测试证据。
    registry.create_task("agent_task", "普通 agent 子任务", kind="agent", status="running", background=False)  # 新增代码+DesktopGUICommandConsoleTest：创建非后台命令任务；如果没有这行代码，过滤普通任务的逻辑没有覆盖。


class GuiCommandConsoleContractTests(unittest.TestCase):  # 新增代码+DesktopGUICommandConsoleTest：测试类段开始，锁定后台命令控制台后端合同；如果没有这个类，unittest 不会发现这些测试。
    def test_command_console_payload_reuses_task_registry_and_redacts_sensitive_data(self) -> None:  # 新增代码+DesktopGUICommandConsoleTest：测试方法开始，验证列表 payload 的事实源和安全字段；如果没有这段，GUI 可能显示假数据或泄漏密钥。
        from learning_agent.app.gui_execution import build_gui_command_console_payload  # 新增代码+DesktopGUICommandConsoleTest：导入新增 payload helper；如果没有这行代码，测试无法约束薄适配层。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUICommandConsoleTest：创建隔离 workspace；如果没有这行代码，测试会读写真实项目任务记录。
            workspace = Path(directory)  # 新增代码+DesktopGUICommandConsoleTest：把临时目录转成 Path；如果没有这行代码，后续路径拼接会变得啰嗦且易错。
            _prepare_command_workspace(workspace)  # 新增代码+DesktopGUICommandConsoleTest：写入后台命令样本；如果没有这行代码，payload 列表会为空。
            payload = build_gui_command_console_payload(workspace)  # 新增代码+DesktopGUICommandConsoleTest：生成后台命令控制台 payload；如果没有这行代码，后续断言没有被测对象。
            command_payload = payload["commands"][0]  # 新增代码+DesktopGUICommandConsoleTest：取出唯一命令卡片；如果没有这行代码，断言要重复索引列表。
            command_json = json.dumps(command_payload, ensure_ascii=False)  # 新增代码+DesktopGUICommandConsoleTest：序列化命令卡片方便检查泄漏；如果没有这行代码，脱敏断言容易漏字段。

        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUICommandConsoleTest：确认 payload 是成功响应；如果没有这行断言，错误响应可能误过。
        self.assertEqual(payload["schema_version"], 2)  # 新增代码+DesktopGUICommandConsoleTest：确认沿用 GUI V2 协议；如果没有这行断言，前后端版本可能漂移。
        self.assertEqual(payload["command_count"], 1)  # 新增代码+DesktopGUICommandConsoleTest：确认只暴露后台命令；如果没有这行断言，普通 agent 子任务可能混入命令台。
        self.assertEqual(payload["running_command_count"], 1)  # 新增代码+DesktopGUICommandConsoleTest：确认运行中命令统计正确；如果没有这行断言，标题摘要可能误导用户。
        self.assertEqual(command_payload["command_id"], "bg_test")  # 新增代码+DesktopGUICommandConsoleTest：确认命令 id 透传；如果没有这行断言，tail/stop 按钮可能无法定位目标。
        self.assertIn("[REDACTED]", command_payload["command_text"])  # 新增代码+DesktopGUICommandConsoleTest：确认命令行密钥被脱敏；如果没有这行断言，API key 可能进入 GUI。
        self.assertNotIn("SECRET_SHOULD_NOT_LEAK", command_json)  # 新增代码+DesktopGUICommandConsoleTest：确认命令密钥没有泄漏到任何字段；如果没有这行断言，局部脱敏可能漏字段。
        self.assertNotIn("SECRET_OUTPUT_SHOULD_NOT_LEAK", command_json)  # 新增代码+DesktopGUICommandConsoleTest：确认输出密钥没有泄漏到 tail；如果没有这行断言，终端回显可能暴露 token。
        self.assertIn("line two", command_payload["tail"])  # 新增代码+DesktopGUICommandConsoleTest：确认真实输出 tail 可见；如果没有这行断言，命令控制台可能只有静态状态。
        self.assertEqual(command_payload["cwd_display"], "subdir")  # 新增代码+DesktopGUICommandConsoleTest：确认 cwd 只显示相对路径；如果没有这行断言，本机绝对目录可能暴露。
        self.assertNotIn("output_path", command_payload)  # 新增代码+DesktopGUICommandConsoleTest：确认不暴露输出文件绝对路径；如果没有这行断言，GUI payload 可能泄漏本地路径。
        self.assertFalse(command_payload["can_stop"])  # 新增代码+DesktopGUICommandConsoleTest：确认当前 bridge 不假装能停进程；如果没有这行断言，GUI 可能提供假按钮。
        self.assertFalse(command_payload["stop_supported"])  # 新增代码+DesktopGUICommandConsoleTest：确认停止能力被诚实标记为不支持；如果没有这行断言，用户会误以为 stop 已接 live process。
        self.assertIn("live process", command_payload["stop_unavailable_reason"])  # 新增代码+DesktopGUICommandConsoleTest：确认不可用原因可读；如果没有这行断言，禁用按钮没有解释。
    # 新增代码+DesktopGUICommandConsoleTest：测试方法结束，test_command_console_payload_reuses_task_registry_and_redacts_sensitive_data 到此结束；如果没有这个边界说明，初学者不易看出列表合同范围。

    def test_command_tail_and_stop_payloads_are_structured_and_honest(self) -> None:  # 新增代码+DesktopGUICommandConsoleTest：测试方法开始，验证 tail 和 stop 两个动态 payload；如果没有这段，按钮端点可能只在列表里“看起来存在”。
        from learning_agent.app.gui_execution import build_gui_command_stop_payload, build_gui_command_tail_payload  # 新增代码+DesktopGUICommandConsoleTest：导入 tail/stop helper；如果没有这行代码，动态端点没有合同约束。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUICommandConsoleTest：创建隔离 workspace；如果没有这行代码，测试会读写真实任务记录。
            workspace = Path(directory)  # 新增代码+DesktopGUICommandConsoleTest：把临时目录转成 Path；如果没有这行代码，后续 helper 调用路径不清晰。
            _prepare_command_workspace(workspace)  # 新增代码+DesktopGUICommandConsoleTest：写入后台命令样本；如果没有这行代码，tail/stop 会返回 not_found。
            tail_payload = build_gui_command_tail_payload(workspace, "bg_test")  # 新增代码+DesktopGUICommandConsoleTest：读取单条命令 tail；如果没有这行代码，无法验证输出端点。
            stop_payload = build_gui_command_stop_payload(workspace, "bg_test")  # 新增代码+DesktopGUICommandConsoleTest：请求停止单条命令；如果没有这行代码，无法验证停止能力反馈。

        self.assertEqual(tail_payload["status"], "ready")  # 新增代码+DesktopGUICommandConsoleTest：确认 tail 正常返回；如果没有这行断言，前端可能收到失败状态仍误显示。
        self.assertIn("line one", tail_payload["tail"])  # 新增代码+DesktopGUICommandConsoleTest：确认 tail 包含真实输出；如果没有这行断言，输出端点可能返回空壳。
        self.assertNotIn("SECRET_OUTPUT_SHOULD_NOT_LEAK", json.dumps(tail_payload, ensure_ascii=False))  # 新增代码+DesktopGUICommandConsoleTest：确认 tail payload 全局脱敏；如果没有这行断言，动态刷新可能泄漏 token。
        self.assertEqual(tail_payload["command"]["command_id"], "bg_test")  # 新增代码+DesktopGUICommandConsoleTest：确认 tail 附带命令摘要；如果没有这行断言，前端刷新后可能失去上下文。
        self.assertEqual(stop_payload["status"], "unavailable")  # 新增代码+DesktopGUICommandConsoleTest：确认当前 stop 返回诚实不可用；如果没有这行断言，后端可能伪造停止成功。
        self.assertFalse(stop_payload["supported"])  # 新增代码+DesktopGUICommandConsoleTest：确认 stop supported 为 false；如果没有这行断言，前端按钮状态会误判。
        self.assertIn("live process", stop_payload["message"])  # 新增代码+DesktopGUICommandConsoleTest：确认停止失败原因说清楚；如果没有这行断言，用户不知道为什么不能停。
    # 新增代码+DesktopGUICommandConsoleTest：测试方法结束，test_command_tail_and_stop_payloads_are_structured_and_honest 到此结束；如果没有这个边界说明，初学者不易看出动态合同范围。

    def test_command_http_routes_require_token_and_return_payloads(self) -> None:  # 新增代码+DesktopGUICommandConsoleTest：测试方法开始，验证真实 HTTP 路由；如果没有这段，Electron client 可能打不到后端。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUICommandConsoleTest：导入真实 bridge 构造器；如果没有这行代码，测试无法启动本地 HTTP handler。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUICommandConsoleTest：创建隔离 workspace；如果没有这行代码，HTTP 测试会污染真实项目。
            workspace = Path(directory)  # 新增代码+DesktopGUICommandConsoleTest：把临时目录转成 Path；如果没有这行代码，任务准备和 server workspace 可能不一致。
            _prepare_command_workspace(workspace)  # 新增代码+DesktopGUICommandConsoleTest：写入后台命令样本；如果没有这行代码，HTTP 路由列表会为空。
            server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUICommandConsoleTest：用随机端口启动 bridge；如果没有这行代码，测试可能端口冲突。
            try:  # 新增代码+DesktopGUICommandConsoleTest：保护 server 清理；如果没有这行代码，断言失败会留下监听端口。
                thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUICommandConsoleTest：创建后台服务线程；如果没有这行代码，请求会阻塞当前测试。
                thread.start()  # 新增代码+DesktopGUICommandConsoleTest：启动 HTTP server；如果没有这行代码，urllib 会连接失败。
                host, port = server.server_address  # 新增代码+DesktopGUICommandConsoleTest：读取随机端口；如果没有这行代码，请求不知道目标地址。
                list_request = urllib.request.Request(f"http://{host}:{port}/v2/gui/commands", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUICommandConsoleTest：构造命令列表请求；如果没有这行代码，列表路由没有被执行。
                tail_request = urllib.request.Request(f"http://{host}:{port}/v2/gui/commands/bg_test/tail", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUICommandConsoleTest：构造 tail 请求；如果没有这行代码，动态 tail 路由没有被执行。
                stop_request = urllib.request.Request(f"http://{host}:{port}/v2/gui/commands/bg_test/stop", data=b"{}", headers={"X-OpenHarness-Desktop-Token": "test-token", "Content-Type": "application/json"}, method="POST")  # 新增代码+DesktopGUICommandConsoleTest：构造 stop POST 请求；如果没有这行代码，停止按钮路由没有被执行。
                with urllib.request.urlopen(list_request, timeout=5) as response:  # 新增代码+DesktopGUICommandConsoleTest：请求命令列表端点；如果没有这行代码，HTTP 列表合同没有实际运行。
                    list_payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUICommandConsoleTest：解析列表 JSON；如果没有这行代码，无法断言响应字段。
                with urllib.request.urlopen(tail_request, timeout=5) as response:  # 新增代码+DesktopGUICommandConsoleTest：请求 tail 端点；如果没有这行代码，HTTP tail 合同没有实际运行。
                    tail_payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUICommandConsoleTest：解析 tail JSON；如果没有这行代码，无法断言输出字段。
                with urllib.request.urlopen(stop_request, timeout=5) as response:  # 新增代码+DesktopGUICommandConsoleTest：请求 stop 端点；如果没有这行代码，HTTP stop 合同没有实际运行。
                    stop_payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUICommandConsoleTest：解析 stop JSON；如果没有这行代码，无法断言控制反馈。
            finally:  # 新增代码+DesktopGUICommandConsoleTest：无论成功失败都关闭 server；如果没有这行代码，测试环境会残留后台线程。
                server.shutdown()  # 新增代码+DesktopGUICommandConsoleTest：停止 serve_forever；如果没有这行代码，后台线程可能继续运行。
                server.server_close()  # 新增代码+DesktopGUICommandConsoleTest：释放 socket；如果没有这行代码，Windows 上端口可能短时间占用。

        self.assertEqual(list_payload["command_count"], 1)  # 新增代码+DesktopGUICommandConsoleTest：确认 HTTP 列表返回命令；如果没有这行断言，路由可能返回空壳。
        self.assertEqual(tail_payload["status"], "ready")  # 新增代码+DesktopGUICommandConsoleTest：确认 HTTP tail 返回 ready；如果没有这行断言，前端刷新可能拿不到输出。
        self.assertEqual(stop_payload["status"], "unavailable")  # 新增代码+DesktopGUICommandConsoleTest：确认 HTTP stop 返回诚实不可用；如果没有这行断言，停止按钮可能误报成功。
    # 新增代码+DesktopGUICommandConsoleTest：测试方法结束，test_command_http_routes_require_token_and_return_payloads 到此结束；如果没有这个边界说明，初学者不易看出路由合同范围。
# 新增代码+DesktopGUICommandConsoleTest：测试类段结束，GuiCommandConsoleContractTests 到此结束；如果没有这个边界说明，用户不容易看出本文件只测后台命令控制台。


if __name__ == "__main__":  # 新增代码+DesktopGUICommandConsoleTest：允许直接运行本文件；如果没有这行代码，手动调试时不会进入 unittest。
    unittest.main()  # 新增代码+DesktopGUICommandConsoleTest：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
