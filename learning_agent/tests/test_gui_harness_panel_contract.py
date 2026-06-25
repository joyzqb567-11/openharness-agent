import json  # 新增代码+DesktopGUIHarnessPanelTest：解析 HTTP JSON 响应；如果没有这行代码，测试无法检查 Harness 面板 payload 字段。
import tempfile  # 新增代码+DesktopGUIHarnessPanelTest：创建隔离工作区；如果没有这行代码，测试会污染真实项目 memory。
import threading  # 新增代码+DesktopGUIHarnessPanelTest：后台启动本地 bridge server；如果没有这行代码，HTTP 请求会被 serve_forever 阻塞。
import unittest  # 新增代码+DesktopGUIHarnessPanelTest：使用 unittest 承载蓝图要求的后端合同测试；如果没有这行代码，测试不会被标准命令收集。
import urllib.request  # 新增代码+DesktopGUIHarnessPanelTest：使用标准库请求本地 bridge；如果没有这行代码，测试需要额外 HTTP 依赖。
from pathlib import Path  # 新增代码+DesktopGUIHarnessPanelTest：使用 Path 管理临时 workspace；如果没有这行代码，Windows 路径拼接容易出错。

from learning_agent.harness.models import HarnessRun, HarnessStage  # 新增代码+DesktopGUIHarnessPanelTest：导入真实 harness run/stage 模型；如果没有这行代码，测试只能造不可信的散装 dict。
from learning_agent.harness.store import HarnessStore  # 新增代码+DesktopGUIHarnessPanelTest：导入真实 harness store；如果没有这行代码，测试无法证明端点读取持久事实源。
from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+DesktopGUIHarnessPanelTest：导入真实 runtime queue；如果没有这行代码，队列条目字段无法验收。
from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DesktopGUIHarnessPanelTest：导入真实状态事件 store；如果没有这行代码，checkpoint 事件顺序无法验收。


class GuiHarnessPanelContractTests(unittest.TestCase):  # 新增代码+DesktopGUIHarnessPanelTest：测试类段开始，锁定 V2 Harness 面板后端合同；如果没有这个类，unittest 不会执行这些验收。
    def _seed_workspace(self, workspace: Path) -> None:  # 新增代码+DesktopGUIHarnessPanelTest：helper 段开始，写入长任务、队列和 checkpoint 测试事实；如果没有这段，每个测试都要重复准备复杂状态。
        stages = [HarnessStage(name="设计蓝图", prompt="输出 GUI 蓝图"), HarnessStage(name="实现界面", prompt="实现 HarnessPanel")]  # 新增代码+DesktopGUIHarnessPanelTest：构造两个阶段；如果没有这行代码，active goal 和 checkpoint 没有阶段来源。
        stages[0].status = "completed"  # 新增代码+DesktopGUIHarnessPanelTest：标记第一阶段已完成；如果没有这行代码，checkpoint 顺序不够真实。
        stages[0].checkpoint = "蓝图已经通过评估。"  # 新增代码+DesktopGUIHarnessPanelTest：写入第一阶段 checkpoint；如果没有这行代码，面板没有已完成恢复点。
        stages[1].status = "running"  # 新增代码+DesktopGUIHarnessPanelTest：标记第二阶段正在运行；如果没有这行代码，active goal 无法显示 running step。
        stages[1].checkpoint = "正在实现 HarnessPanel。"  # 新增代码+DesktopGUIHarnessPanelTest：写入第二阶段 checkpoint；如果没有这行代码，last_progress 没有当前进展。
        run = HarnessRun.create("goal_gui_v2", "完成 Codex 风格桌面 GUI V2 Harness 面板", stages)  # 新增代码+DesktopGUIHarnessPanelTest：创建真实 harness run；如果没有这行代码，状态快照没有 active goal。
        run.status = "running"  # 新增代码+DesktopGUIHarnessPanelTest：标记 run 为运行中；如果没有这行代码，端点可能不会把它选为当前目标。
        run.current_stage_index = 1  # 新增代码+DesktopGUIHarnessPanelTest：把当前阶段指向实现界面；如果没有这行代码，running_step 会显示错误阶段。
        HarnessStore(workspace / "memory" / "harness").save_run(run)  # 新增代码+DesktopGUIHarnessPanelTest：把 run 落盘到统一 harness store；如果没有这行代码，HTTP 端点读取不到目标。
        RuntimeCommandQueue(workspace / "memory" / "runtime").enqueue_prompt("排队的后续验收 prompt", priority="later")  # 新增代码+DesktopGUIHarnessPanelTest：写入 runtime 队列条目；如果没有这行代码，queue 状态没有样本。
        status_store = StatusEventStore(workspace / "memory" / "status")  # 新增代码+DesktopGUIHarnessPanelTest：创建状态事件 store；如果没有这行代码，checkpoint 事件没有落盘位置。
        status_store.append("harness_checkpoint", {"stage_name": "设计蓝图", "checkpoint": "事件 checkpoint 1"}, run_id="goal_gui_v2")  # 新增代码+DesktopGUIHarnessPanelTest：写入第一条 checkpoint 事件；如果没有这行代码，事件顺序断言没有第一项。
        status_store.append("harness_checkpoint", {"stage_name": "实现界面", "checkpoint": "事件 checkpoint 2"}, run_id="goal_gui_v2")  # 新增代码+DesktopGUIHarnessPanelTest：写入第二条 checkpoint 事件；如果没有这行代码，事件顺序断言没有第二项。
        status_store.append("harness_blocked", {"blocked_reason": "等待用户确认是否启用真实暂停能力。"}, run_id="goal_gui_v2")  # 新增代码+DesktopGUIHarnessPanelTest：写入阻塞原因事件；如果没有这行代码，blocked_warning 没有样本。
    # 新增代码+DesktopGUIHarnessPanelTest：helper 段结束，_seed_workspace 到此结束；如果没有边界说明，初学者不易看出它只负责测试数据。

    def _start_server(self, workspace: Path):  # 新增代码+DesktopGUIHarnessPanelTest：helper 段开始，启动带 token 的测试 server；如果没有这段，每个 HTTP 测试都要重复线程逻辑。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIHarnessPanelTest：导入 GUI bridge server 工厂；如果没有这行代码，测试无法启动真实路由。

        server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUIHarnessPanelTest：绑定随机端口并固定 token；如果没有这行代码，测试容易端口冲突。
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIHarnessPanelTest：创建后台服务线程；如果没有这行代码，urlopen 会连接不到 server。
        thread.start()  # 新增代码+DesktopGUIHarnessPanelTest：启动 server 线程；如果没有这行代码，请求会失败。
        return server  # 新增代码+DesktopGUIHarnessPanelTest：返回 server 供测试拼 URL 和关闭；如果没有这行代码，调用方拿不到端口。
    # 新增代码+DesktopGUIHarnessPanelTest：helper 段结束，_start_server 到此结束；如果没有边界说明，初学者不易看出它只负责启动服务。

    def _url(self, server, path: str) -> str:  # 新增代码+DesktopGUIHarnessPanelTest：helper 段开始，拼接随机端口 URL；如果没有这段，HTTP 路径会散落重复。
        host, port = server.server_address  # 新增代码+DesktopGUIHarnessPanelTest：读取真实监听地址；如果没有这行代码，端口 0 场景无法请求。
        return f"http://{host}:{port}{path}"  # 新增代码+DesktopGUIHarnessPanelTest：返回完整 URL；如果没有这行代码，urllib 没有目标地址。
    # 新增代码+DesktopGUIHarnessPanelTest：helper 段结束，_url 到此结束；如果没有边界说明，初学者不易看出它只负责拼 URL。

    def _get_json(self, server, path: str) -> dict[str, object]:  # 新增代码+DesktopGUIHarnessPanelTest：helper 段开始，发送带 token 的 GET；如果没有这段，状态请求会重复写法。
        request = urllib.request.Request(self._url(server, path), headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUIHarnessPanelTest：构造认证 GET 请求；如果没有这行代码，安全门禁会返回 401。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUIHarnessPanelTest：发送请求并读取响应；如果没有这行代码，测试不会真正触发 endpoint。
            return json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIHarnessPanelTest：解析 JSON 响应；如果没有这行代码，断言无法读取字段。
    # 新增代码+DesktopGUIHarnessPanelTest：helper 段结束，_get_json 到此结束；如果没有边界说明，初学者不易看出它只负责 GET。

    def _post_json(self, server, path: str) -> dict[str, object]:  # 新增代码+DesktopGUIHarnessPanelTest：helper 段开始，发送带 token 的 POST；如果没有这段，pause/resume 请求会重复写法。
        request = urllib.request.Request(self._url(server, path), data=b"{}", method="POST", headers={"Content-Type": "application/json", "X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUIHarnessPanelTest：构造认证 JSON POST；如果没有这行代码，控制端点会被门禁拒绝。
        with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUIHarnessPanelTest：发送 POST 请求；如果没有这行代码，测试不会真正验证路由。
            return json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIHarnessPanelTest：解析 JSON 响应；如果没有这行代码，断言无法读取字段。
    # 新增代码+DesktopGUIHarnessPanelTest：helper 段结束，_post_json 到此结束；如果没有边界说明，初学者不易看出它只负责 POST。

    def test_harness_status_endpoint_returns_goal_queue_and_checkpoints(self) -> None:  # 新增代码+DesktopGUIHarnessPanelTest：测试段开始，验证 active goal、queue 和 checkpoint 合同；如果没有这段，HarnessPanel 可能只有空壳数据。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIHarnessPanelTest：创建临时 workspace；如果没有这行代码，测试会污染真实项目。
            workspace = Path(directory)  # 新增代码+DesktopGUIHarnessPanelTest：把临时目录转成 Path；如果没有这行代码，后续路径拼接不稳定。
            self._seed_workspace(workspace)  # 新增代码+DesktopGUIHarnessPanelTest：写入测试事实；如果没有这行代码，端点只能返回空状态。
            server = self._start_server(workspace)  # 新增代码+DesktopGUIHarnessPanelTest：启动真实 bridge；如果没有这行代码，HTTP 路由无法验收。
            try:  # 新增代码+DesktopGUIHarnessPanelTest：确保 server 最终关闭；如果没有这行代码，失败时会残留端口。
                payload = self._get_json(server, "/v2/gui/harness/status")  # 新增代码+DesktopGUIHarnessPanelTest：请求 V2 Harness 状态；如果没有这行代码，无法验证路由。
            finally:  # 新增代码+DesktopGUIHarnessPanelTest：清理 server；如果没有这行代码，测试可能挂住。
                server.shutdown()  # 新增代码+DesktopGUIHarnessPanelTest：停止 serve_forever；如果没有这行代码，后台线程可能继续运行。
                server.server_close()  # 新增代码+DesktopGUIHarnessPanelTest：释放 socket；如果没有这行代码，Windows 端口可能短时占用。
        self.assertIs(payload["ok"], True)  # 新增代码+DesktopGUIHarnessPanelTest：确认成功 payload；如果没有这行断言，错误响应可能误过。
        self.assertEqual(payload["active_goal"]["run_id"], "goal_gui_v2")  # 新增代码+DesktopGUIHarnessPanelTest：确认当前目标来自真实 run；如果没有这行断言，active_goal 可能选错。
        self.assertEqual(payload["active_goal"]["running_step"], "实现界面")  # 新增代码+DesktopGUIHarnessPanelTest：确认 running step 来自 current_stage_index；如果没有这行断言，恢复点可能显示错误阶段。
        self.assertTrue(any(item["status"] == "queued" for item in payload["queue"]))  # 新增代码+DesktopGUIHarnessPanelTest：确认队列条目携带状态；如果没有这行断言，queue 可能只有文本没有生命周期。
        event_checkpoints = [item for item in payload["checkpoints"] if item.get("source") == "event"]  # 新增代码+DesktopGUIHarnessPanelTest：提取事件型 checkpoint；如果没有这行代码，顺序断言会混入阶段 checkpoint。
        self.assertEqual([item["checkpoint"] for item in event_checkpoints], ["事件 checkpoint 1", "事件 checkpoint 2"])  # 新增代码+DesktopGUIHarnessPanelTest：确认 checkpoint 事件按写入顺序出现；如果没有这行断言，时间线乱序不会被发现。
        self.assertIn("暂停能力", payload["blocked_reason"])  # 新增代码+DesktopGUIHarnessPanelTest：确认阻塞原因可见；如果没有这行断言，blocked warning 可能没有数据。
    # 新增代码+DesktopGUIHarnessPanelTest：测试段结束，状态端点合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。

    def test_harness_pause_resume_return_structured_capability_response(self) -> None:  # 新增代码+DesktopGUIHarnessPanelTest：测试段开始，验证 pause/resume 控制返回结构化响应；如果没有这段，前端按钮可能只收到 404。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIHarnessPanelTest：创建临时 workspace；如果没有这行代码，测试会污染真实状态。
            server = self._start_server(Path(directory))  # 新增代码+DesktopGUIHarnessPanelTest：启动真实 bridge；如果没有这行代码，POST 路由无法验收。
            try:  # 新增代码+DesktopGUIHarnessPanelTest：确保 server 最终关闭；如果没有这行代码，失败时会残留端口。
                pause = self._post_json(server, "/v2/gui/harness/pause")  # 新增代码+DesktopGUIHarnessPanelTest：请求暂停；如果没有这行代码，无法验证 pause 路由。
                resume = self._post_json(server, "/v2/gui/harness/resume")  # 新增代码+DesktopGUIHarnessPanelTest：请求恢复；如果没有这行代码，无法验证 resume 路由。
            finally:  # 新增代码+DesktopGUIHarnessPanelTest：清理 server；如果没有这行代码，测试可能挂住。
                server.shutdown()  # 新增代码+DesktopGUIHarnessPanelTest：停止 serve_forever；如果没有这行代码，后台线程可能继续运行。
                server.server_close()  # 新增代码+DesktopGUIHarnessPanelTest：释放 socket；如果没有这行代码，Windows 端口可能短时占用。
        self.assertEqual(pause["action"], "pause")  # 新增代码+DesktopGUIHarnessPanelTest：确认 pause 动作被结构化返回；如果没有这行断言，前端无法区分控制类型。
        self.assertEqual(resume["action"], "resume")  # 新增代码+DesktopGUIHarnessPanelTest：确认 resume 动作被结构化返回；如果没有这行断言，前端无法区分控制类型。
        self.assertIs(pause["supported"], False)  # 新增代码+DesktopGUIHarnessPanelTest：确认未支持状态明确；如果没有这行断言，前端可能误显示可用按钮。
        self.assertEqual(resume["status"], "unsupported")  # 新增代码+DesktopGUIHarnessPanelTest：确认恢复返回稳定状态；如果没有这行断言，按钮失败原因不可读。
    # 新增代码+DesktopGUIHarnessPanelTest：测试段结束，控制响应合同到此结束；如果没有边界说明，初学者不易看出覆盖范围。


if __name__ == "__main__":  # 新增代码+DesktopGUIHarnessPanelTest：允许直接运行本文件；如果没有这行代码，手动调试时不会进入 unittest。
    unittest.main()  # 新增代码+DesktopGUIHarnessPanelTest：启动 unittest runner；如果没有这行代码，直接运行文件不会执行测试。
