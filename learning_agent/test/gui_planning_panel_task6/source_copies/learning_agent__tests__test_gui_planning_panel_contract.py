import json  # 新增代码+DesktopGUIPlanningTest：用于写入 todo_state.json 并检查 payload 是否泄漏敏感字段；如果没有这行，测试无法覆盖 JSON 合同。
import tempfile  # 新增代码+DesktopGUIPlanningTest：用于创建隔离工作区；如果没有这行，测试会污染真实项目目录。
import threading  # 新增代码+DesktopGUIPlanningTest：用于启动真实 GUI bridge HTTP server；如果没有这行，路由测试无法并发响应。
import unittest  # 新增代码+DesktopGUIPlanningTest：使用标准库测试框架；如果没有这行，测试类无法运行。
import urllib.request  # 新增代码+DesktopGUIPlanningTest：用于真实请求本地 HTTP endpoint；如果没有这行，路由接线不会被验证。
from pathlib import Path  # 新增代码+DesktopGUIPlanningTest：用于规范化临时工作区路径；如果没有这行，测试传参会退化为字符串。

from learning_agent.runtime.task_registry import TaskRegistry  # 新增代码+DesktopGUIPlanningTest：复用真实持久任务登记表；如果没有这行，测试无法证明 GUI 读取 task_list 事实源。
from learning_agent.runtime.team_registry import TeamRegistry  # 新增代码+DesktopGUIPlanningTest：复用真实持久 team 登记表；如果没有这行，测试无法证明 GUI 读取 list_peers 事实源。
from learning_agent.tasks.team import TeamMessage, TeamPeer  # 新增代码+DesktopGUIPlanningTest：复用真实 team 数据结构；如果没有这行，测试会另造 peer/message 形状。


def _prepare_planning_workspace(workspace: Path) -> None:  # 新增代码+DesktopGUIPlanningTest：函数段开始，创建可被 planning payload 读取的真实运行时状态；如果没有这段，两个测试会重复准备数据。
    (workspace / "todo_state.json").write_text(json.dumps({"todos": [{"id": "todo_a", "content": "接入 planning GUI", "status": "in_progress", "priority": "high", "secret": "SECRET_SHOULD_NOT_RENDER"}, {"id": "todo_b", "content": "验证空态", "status": "pending", "priority": "medium"}]}, ensure_ascii=False), encoding="utf-8")  # 新增代码+DesktopGUIPlanningTest：写入真实 todo_state.json；如果没有这行，todo 区无法验证持久读取和字段白名单。
    task_registry = TaskRegistry(workspace / "memory" / "tasks")  # 新增代码+DesktopGUIPlanningTest：打开真实任务登记表目录；如果没有这行，无法创建可恢复任务记录。
    task_registry.create_task("task_a", "实现计划协作面板", status="running", background=True, metadata={"label": "Planning Panel"})  # 新增代码+DesktopGUIPlanningTest：创建运行中任务；如果没有这行，active_task_count 无法验证。
    task_registry.create_task("task_b", "历史完成任务", status="completed", background=False, metadata={"label": "Done Task"})  # 新增代码+DesktopGUIPlanningTest：创建完成任务；如果没有这行，状态统计覆盖不完整。
    team_registry = TeamRegistry(workspace / "memory" / "team")  # 新增代码+DesktopGUIPlanningTest：打开真实 team 登记表目录；如果没有这行，无法创建可恢复 peer。
    message = TeamMessage(message_id="message_a", sender="planner", content="请检查 task_a", created_at="2026-06-27T00:00:00Z")  # 新增代码+DesktopGUIPlanningTest：创建未确认消息；如果没有这行，pending_peer_message_count 无法验证。
    peer = TeamPeer(peer_id="peer_a", name="Reviewer", role="reviewer", status="running", notes="负责检查 GUI", inbox=[message], bound_task_id="task_a", bound_task_started_at="2026-06-27T00:00:00Z")  # 新增代码+DesktopGUIPlanningTest：创建绑定任务的 peer；如果没有这行，team 到 task 的链路无法验证。
    team_registry.save_peer(peer)  # 新增代码+DesktopGUIPlanningTest：保存 peer 到真实 registry；如果没有这行，planning payload 读不到团队状态。
# 新增代码+DesktopGUIPlanningTest：函数段结束，_prepare_planning_workspace 到此结束；如果没有边界说明，测试数据准备范围不清楚。


class GuiPlanningPanelContractTest(unittest.TestCase):  # 新增代码+DesktopGUIPlanningTest：测试类段开始，验证 GUI planning 合同；如果没有这段，Task 6 后端合同没有自动化保护。
    def test_planning_payload_reuses_todo_task_and_team_state(self) -> None:  # 新增代码+DesktopGUIPlanningTest：测试方法开始，验证 payload 复用 runtime 状态；如果没有这段，GUI 可能回到硬编码空壳。
        from learning_agent.app.gui_toolchain import build_gui_planning_payload  # 新增代码+DesktopGUIPlanningTest：导入被测 helper；如果没有这行，测试没有目标函数。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIPlanningTest：创建临时 workspace；如果没有这行，测试会污染真实文件。
            workspace = Path(directory)  # 新增代码+DesktopGUIPlanningTest：把临时目录转为 Path；如果没有这行，后续路径拼接不清晰。
            _prepare_planning_workspace(workspace)  # 新增代码+DesktopGUIPlanningTest：写入真实 todo/task/team 状态；如果没有这行，payload 没有数据可读。
            payload = build_gui_planning_payload(workspace)  # 新增代码+DesktopGUIPlanningTest：生成 planning payload；如果没有这行，后续断言没有输入。
        serialized = json.dumps(payload, ensure_ascii=False)  # 新增代码+DesktopGUIPlanningTest：序列化完整 payload；如果没有这行，深层字段泄漏不易检查。
        self.assertTrue(payload["ok"])  # 新增代码+DesktopGUIPlanningTest：确认响应成功；如果没有这行，错误 payload 可能误过。
        self.assertEqual(payload["todo_count"], 2)  # 新增代码+DesktopGUIPlanningTest：确认 todo 数量来自 todo_state.json；如果没有这行，todo 读取可能断开。
        self.assertEqual(payload["task_count"], 2)  # 新增代码+DesktopGUIPlanningTest：确认任务数量来自 TaskRegistry；如果没有这行，task_list 事实源可能断开。
        self.assertEqual(payload["active_task_count"], 1)  # 新增代码+DesktopGUIPlanningTest：确认活动任务统计；如果没有这行，运行中任务摘要可能错误。
        self.assertEqual(payload["peer_count"], 1)  # 新增代码+DesktopGUIPlanningTest：确认 peer 数量来自 TeamRegistry；如果没有这行，list_peers 事实源可能断开。
        self.assertEqual(payload["pending_peer_message_count"], 1)  # 新增代码+DesktopGUIPlanningTest：确认未确认消息统计；如果没有这行，read_peer_messages 状态可能不可见。
        self.assertIn("learning_agent.runtime.task_registry", serialized)  # 新增代码+DesktopGUIPlanningTest：确认 payload 标注复用任务模块；如果没有这行，用户无法验收复用关系。
        self.assertNotIn("SECRET_SHOULD_NOT_RENDER", serialized)  # 新增代码+DesktopGUIPlanningTest：确认未知 todo secret 不渲染；如果没有这行，字段白名单回归难以及时发现。
    # 新增代码+DesktopGUIPlanningTest：测试方法结束，test_planning_payload_reuses_todo_task_and_team_state 到此结束；如果没有边界说明，测试范围不清楚。

    def test_planning_bridge_route_returns_payload(self) -> None:  # 新增代码+DesktopGUIPlanningTest：测试方法开始，验证 HTTP endpoint 接线；如果没有这段，Electron 可能拿不到 planning payload。
        from learning_agent.app.gui_bridge import create_gui_bridge_server  # 新增代码+DesktopGUIPlanningTest：导入真实 bridge server；如果没有这行，无法测试 HTTP 路由。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIPlanningTest：创建临时 workspace；如果没有这行，测试会污染真实状态。
            workspace = Path(directory)  # 新增代码+DesktopGUIPlanningTest：把临时目录转为 Path；如果没有这行，后续路径拼接不清晰。
            _prepare_planning_workspace(workspace)  # 新增代码+DesktopGUIPlanningTest：写入真实运行时状态；如果没有这行，route 只能返回空态。
            server = create_gui_bridge_server(workspace=workspace, host="127.0.0.1", port=0, token="test-token")  # 新增代码+DesktopGUIPlanningTest：启动随机端口 bridge；如果没有这行，HTTP 请求没有目标。
            thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+DesktopGUIPlanningTest：创建后台服务线程；如果没有这行，urlopen 会连接不到 server。
            thread.start()  # 新增代码+DesktopGUIPlanningTest：启动服务线程；如果没有这行，路由不会响应。
            try:  # 新增代码+DesktopGUIPlanningTest：确保 server 最终关闭；如果没有这行，测试失败时端口可能残留。
                host, port = server.server_address  # 新增代码+DesktopGUIPlanningTest：读取随机端口；如果没有这行，请求 URL 无法构造。
                request = urllib.request.Request(f"http://{host}:{port}/v2/gui/planning", headers={"X-OpenHarness-Desktop-Token": "test-token"})  # 新增代码+DesktopGUIPlanningTest：构造带 token 的 GET 请求；如果没有这行，安全门禁会拒绝。
                with urllib.request.urlopen(request, timeout=5) as response:  # 新增代码+DesktopGUIPlanningTest：发送请求并读取响应；如果没有这行，路由接线不会执行。
                    payload = json.loads(response.read().decode("utf-8"))  # 新增代码+DesktopGUIPlanningTest：解析 JSON 响应；如果没有这行，后续无法断言字段。
            finally:  # 新增代码+DesktopGUIPlanningTest：清理 HTTP server；如果没有这行，测试进程可能不退出。
                server.shutdown()  # 新增代码+DesktopGUIPlanningTest：停止 server；如果没有这行，后台线程会继续占端口。
                server.server_close()  # 新增代码+DesktopGUIPlanningTest：关闭监听 socket；如果没有这行，Windows 可能短时间占用端口。
        self.assertTrue(payload["ok"])  # 新增代码+DesktopGUIPlanningTest：确认 HTTP payload 成功；如果没有这行，错误页可能误过。
        self.assertEqual(payload["todo_count"], 2)  # 新增代码+DesktopGUIPlanningTest：确认 route 返回 todo 状态；如果没有这行，路由可能没接 helper。
        self.assertEqual(payload["peer_count"], 1)  # 新增代码+DesktopGUIPlanningTest：确认 route 返回 team 状态；如果没有这行，路由可能没读 registry。
    # 新增代码+DesktopGUIPlanningTest：测试方法结束，test_planning_bridge_route_returns_payload 到此结束；如果没有边界说明，测试范围不清楚。


if __name__ == "__main__":  # 新增代码+DesktopGUIPlanningTest：允许直接运行本测试文件；如果没有这行，手动调试需要记 unittest 模块参数。
    unittest.main()  # 新增代码+DesktopGUIPlanningTest：启动 unittest；如果没有这行，直接运行文件不会执行测试。
