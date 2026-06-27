import json  # 新增代码+DesktopGUIMemoryPanelTest：序列化 payload 用于泄露扫描；如果没有这行，测试无法检查嵌套字段是否含秘密。
import tempfile  # 新增代码+DesktopGUIMemoryPanelTest：创建隔离 workspace；如果没有这行，测试会污染真实项目目录。
import threading  # 新增代码+DesktopGUIMemoryPanelTest：启动真实 HTTP bridge 线程；如果没有这行，路由测试无法发请求。
import unittest  # 新增代码+DesktopGUIMemoryPanelTest：使用项目现有 unittest 风格；如果没有这行，测试类无法被 python -m unittest 发现。
import urllib.error  # 新增代码+DesktopGUIMemoryPanelTest：捕获未授权 HTTP 错误；如果没有这行，401 合同无法断言。
import urllib.request  # 新增代码+DesktopGUIMemoryPanelTest：请求本地 bridge endpoint；如果没有这行，HTTP 合同只能停留在 helper 层。
from pathlib import Path  # 新增代码+DesktopGUIMemoryPanelTest：构造跨平台路径；如果没有这行，Windows 路径拼接容易出错。


class GuiMemoryPanelContractTest(unittest.TestCase):  # 新增代码+DesktopGUIMemoryPanelTest：测试类段开始，锁定记忆、prompt、notebook GUI 合同；如果没有这段，Memory 面板后端可能悄悄退化。
    def test_memory_summary_reads_agent_memory_without_secrets_or_absolute_paths(self) -> None:  # 新增代码+DesktopGUIMemoryPanelTest：测试记忆摘要安全性；如果没有这段，GUI 可能显示完整 token 或本机路径。
        from learning_agent.app.gui_memory import build_gui_memory_summary_payload  # 新增代码+DesktopGUIMemoryPanelTest：导入被测 helper；如果没有这行，测试没有目标函数。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIMemoryPanelTest：创建临时工作区；如果没有这行，测试会依赖真实 repo 状态。
            workspace = Path(directory)  # 新增代码+DesktopGUIMemoryPanelTest：把临时目录转成 Path；如果没有这行，后续路径拼接不清楚。
            memory_root = workspace / "agent_memory"  # 新增代码+DesktopGUIMemoryPanelTest：定位 agent_memory；如果没有这行，fixture 文件无法放到真实约定位置。
            memory_root.mkdir()  # 新增代码+DesktopGUIMemoryPanelTest：创建 agent_memory 目录；如果没有这行，写入 context/progress/bugs 会失败。
            (memory_root / "context.md").write_text("# Context\n当前目标：接入 Memory GUI。\nBearer sk-secret H:/private/token.txt\n", encoding="utf-8")  # 新增代码+DesktopGUIMemoryPanelTest：写入含秘密的 context fixture；如果没有这行，脱敏断言没有输入。
            (memory_root / "progress.md").write_text("# Progress\n- Task 10 正在进行。\n- 最近一步：MemoryPanel。\n", encoding="utf-8")  # 新增代码+DesktopGUIMemoryPanelTest：写入 progress fixture；如果没有这行，进度摘要无法断言。
            (memory_root / "bugs.md").write_text("# Bugs\n暂无阻塞。\n", encoding="utf-8")  # 新增代码+DesktopGUIMemoryPanelTest：写入 bugs fixture；如果没有这行，风险摘要无法断言。
            payload = build_gui_memory_summary_payload(workspace)  # 新增代码+DesktopGUIMemoryPanelTest：生成 memory payload；如果没有这行，后续断言没有输入。

        serialized = json.dumps(payload, ensure_ascii=False)  # 新增代码+DesktopGUIMemoryPanelTest：序列化整包做安全扫描；如果没有这行，嵌套泄露可能漏过。
        self.assertTrue(payload["ok"])  # 新增代码+DesktopGUIMemoryPanelTest：确认 helper 返回成功；如果没有这行，错误 payload 也可能误过。
        self.assertEqual(payload["context_summary"]["status"], "ready")  # 新增代码+DesktopGUIMemoryPanelTest：确认 context 文件被读取；如果没有这行，面板可能显示空态。
        self.assertIn("Task 10", " ".join(payload["progress_summary"]["preview_lines"]))  # 新增代码+DesktopGUIMemoryPanelTest：确认 progress 最新行进入摘要；如果没有这行，长任务进度可能不可见。
        self.assertNotIn("sk-secret", serialized)  # 新增代码+DesktopGUIMemoryPanelTest：确认 OpenAI 风格密钥被脱敏；如果没有这行，secret 泄露回归无法发现。
        self.assertNotIn("H:/private", serialized)  # 新增代码+DesktopGUIMemoryPanelTest：确认本机绝对路径被脱敏；如果没有这行，路径隐私泄露无法发现。
        self.assertNotIn(str(Path(tempfile.gettempdir())), serialized)  # 新增代码+DesktopGUIMemoryPanelTest：确认 payload 不携带临时目录绝对路径；如果没有这行，workspace 路径可能泄露。

    def test_prompt_and_notebook_status_reuse_real_tool_catalog(self) -> None:  # 新增代码+DesktopGUIMemoryPanelTest：测试 prompt/token/notebook 工具状态；如果没有这段，面板可能显示硬编码假接入。
        from learning_agent.app.gui_memory import build_gui_notebook_status_payload, build_gui_prompt_status_payload  # 新增代码+DesktopGUIMemoryPanelTest：导入被测 helper；如果没有这行，测试没有目标函数。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIMemoryPanelTest：创建临时工作区；如果没有这行，notebook 扫描会碰真实仓库。
            workspace = Path(directory)  # 新增代码+DesktopGUIMemoryPanelTest：把目录转成 Path；如果没有这行，后续写 notebook 不清楚。
            (workspace / "demo.ipynb").write_text(json.dumps({"nbformat": 4, "nbformat_minor": 5, "cells": []}), encoding="utf-8")  # 新增代码+DesktopGUIMemoryPanelTest：写入最小 notebook；如果没有这行，notebook_count 无法验证。
            prompt_payload = build_gui_prompt_status_payload(workspace)  # 新增代码+DesktopGUIMemoryPanelTest：生成 prompt/token payload；如果没有这行，预算断言没有输入。
            notebook_payload = build_gui_notebook_status_payload(workspace)  # 新增代码+DesktopGUIMemoryPanelTest：生成 notebook payload；如果没有这行，notebook 断言没有输入。

        self.assertTrue(prompt_payload["prompt_surface"]["available"])  # 新增代码+DesktopGUIMemoryPanelTest：确认 prompt_surface_report 在真实 catalog 中；如果没有这行，报告工具缺失不会被发现。
        self.assertTrue(prompt_payload["token_budget"]["available"])  # 新增代码+DesktopGUIMemoryPanelTest：确认 token_budget_report 在真实 catalog 中；如果没有这行，token 面板可能是假数据。
        self.assertGreaterEqual(prompt_payload["context_budget"]["max_messages"], 3)  # 新增代码+DesktopGUIMemoryPanelTest：确认预算阈值来自真实保护函数；如果没有这行，异常小阈值可能进入 GUI。
        self.assertGreaterEqual(notebook_payload["notebook_count"], 1)  # 新增代码+DesktopGUIMemoryPanelTest：确认 notebook 扫描发现 fixture；如果没有这行，扫描接线可能断开。
        self.assertTrue(any(item["name"] == "notebook_read" and item["available"] for item in notebook_payload["tools"]))  # 新增代码+DesktopGUIMemoryPanelTest：确认 notebook_read 可见；如果没有这行，读取工具缺失不会被发现。
        self.assertFalse(notebook_payload["edit_exposed_in_gui"])  # 新增代码+DesktopGUIMemoryPanelTest：确认第一版 GUI 不开放编辑；如果没有这行，read-only 边界可能被误改。

    def test_memory_http_routes_require_token_and_return_safe_payloads(self) -> None:  # 新增代码+DesktopGUIMemoryPanelTest：测试真实 HTTP 路由；如果没有这段，helper 正确但 bridge 未接线也会漏过。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIMemoryPanelTest：导入 bridge server 构造器；如果没有这行，无法启动本地 HTTP server。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIMemoryPanelTest：创建临时 workspace；如果没有这行，HTTP 测试会读真实项目状态。
            workspace = Path(directory)  # 新增代码+DesktopGUIMemoryPanelTest：转成 Path；如果没有这行，路径参数不清楚。
            (workspace / "agent_memory").mkdir()  # 新增代码+DesktopGUIMemoryPanelTest：创建记忆目录；如果没有这行，memory endpoint 只能返回全缺失状态。
            (workspace / "agent_memory" / "progress.md").write_text("# Progress\nHTTP route ready\n", encoding="utf-8")  # 新增代码+DesktopGUIMemoryPanelTest：写入进度 fixture；如果没有这行，HTTP payload 无可见内容。
            server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUIMemoryPanelTest：启动随机端口 bridge；如果没有这行，路由没有服务端。
            thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIMemoryPanelTest：创建后台服务线程；如果没有这行，urllib 请求无人响应。
            thread.start()  # 新增代码+DesktopGUIMemoryPanelTest：启动 HTTP server；如果没有这行，请求会连接失败。
            host, port = server.server_address  # 新增代码+DesktopGUIMemoryPanelTest：读取随机端口；如果没有这行，测试不知道请求地址。
            try:  # 新增代码+DesktopGUIMemoryPanelTest：保护 server 关闭；如果没有这行，失败时线程可能残留。
                with self.assertRaises(urllib.error.HTTPError) as unauthorized_context:  # 新增代码+DesktopGUIMemoryPanelTest：断言无 token 会失败；如果没有这行，鉴权退化无法发现。
                    urllib.request.urlopen(f"http://{host}:{port}/v2/gui/memory/summary", timeout=5)  # 新增代码+DesktopGUIMemoryPanelTest：发起未授权请求；如果没有这行，401 合同没有触发点。
                self.assertEqual(unauthorized_context.exception.code, 401)  # 新增代码+DesktopGUIMemoryPanelTest：确认失败码是 401；如果没有这行，403/404 等错误会误过。
                payloads = []  # 新增代码+DesktopGUIMemoryPanelTest：准备收集三个 endpoint 响应；如果没有这行，循环结果无处保存。
                for path in ("/v2/gui/memory/summary", "/v2/gui/prompt/status", "/v2/gui/notebook/status"):  # 新增代码+DesktopGUIMemoryPanelTest：遍历三个新增路由；如果没有这行，只会测到其中一个 endpoint。
                    request = urllib.request.Request(f"http://{host}:{port}{path}", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUIMemoryPanelTest：构造带 token 请求；如果没有这行，授权路由无法通过。
                    with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUIMemoryPanelTest：请求新增 endpoint；如果没有这行，bridge 接线不会执行。
                        payloads.append(json.loads(response.read().decode("utf-8")))  # 新增代码+DesktopGUIMemoryPanelTest：解析 JSON 响应；如果没有这行，后续无法断言字段。
            finally:  # 新增代码+DesktopGUIMemoryPanelTest：无论断言是否失败都清理 server；如果没有这行，后台线程可能挂住测试。
                server.shutdown()  # 新增代码+DesktopGUIMemoryPanelTest：停止 HTTP server；如果没有这行，测试进程可能一直监听。
                server.server_close()  # 新增代码+DesktopGUIMemoryPanelTest：释放 socket；如果没有这行，Windows 上端口资源可能延迟释放。
                thread.join(timeout=5)  # 新增代码+DesktopGUIMemoryPanelTest：等待线程退出；如果没有这行，后台线程可能残留到下个测试。

        self.assertEqual([payload["ok"] for payload in payloads], [True, True, True])  # 新增代码+DesktopGUIMemoryPanelTest：确认三个路由都返回成功 payload；如果没有这行，404 或错误响应可能漏过。
        self.assertIn("HTTP route ready", json.dumps(payloads[0], ensure_ascii=False))  # 新增代码+DesktopGUIMemoryPanelTest：确认 memory route 读取真实 fixture；如果没有这行，路由可能返回空假数据。


if __name__ == "__main__":  # 新增代码+DesktopGUIMemoryPanelTest：允许直接运行测试文件；如果没有这行，手动调试需要额外记 unittest 命令。
    unittest.main()  # 新增代码+DesktopGUIMemoryPanelTest：启动 unittest；如果没有这行，直接 python 文件不会执行测试。
