import tempfile  # 新增代码+RealHarnessPermissionTest：创建隔离 workspace；如果没有这一行，权限测试会污染真实项目。
import threading  # 新增代码+RealHarnessPermissionTest：模拟 GUI 弹窗异步回答；如果没有这一行，无法测试等待中的权限握手。
import time  # 新增代码+RealHarnessPermissionTest：轮询等待权限请求出现；如果没有这一行，测试会和后台线程抢时序。
import unittest  # 新增代码+RealHarnessPermissionTest：使用标准库 unittest 编写合同测试；如果没有这一行，测试不会被收集。
from pathlib import Path  # 新增代码+RealHarnessPermissionTest：处理临时文件路径；如果没有这一行，断言文件是否落盘会不清楚。

from learning_agent.app.gui_agent_adapter import DefaultHarnessGuiAgentAdapter, GuiAgentRunRequest  # 新增代码+RealHarnessPermissionTest：导入真实 adapter shell 和请求对象；如果没有这一行，写工具权限无法走 GUI 边界。
from learning_agent.app.gui_bridge import GuiMessage, GuiRunManager, GuiTurn  # 新增代码+RealHarnessPermissionTest：导入 GUI 生命周期对象；如果没有这一行，无法直接构造权限等待状态。
from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+RealHarnessPermissionTest：构造假模型工具调用；如果没有这一行，测试需要真实模型。
from learning_agent.models.fake import ToolCallingFakeModel  # 新增代码+RealHarnessPermissionTest：使用离线假模型；如果没有这一行，测试需要联网。


def _request() -> GuiAgentRunRequest:  # 新增代码+RealHarnessPermissionTest：函数段开始，构造权限请求里的 GUI run 身份；如果没有这段，多处测试会重复样板。
    return GuiAgentRunRequest(session_id="session_perm", turn_id="turn_perm", run_id="run_perm", prompt="permission", workspace=".")  # 新增代码+RealHarnessPermissionTest：返回稳定 request；如果没有这一行，权限回调没有 turn/run/session id。
# 新增代码+RealHarnessPermissionTest：函数段结束，_request 到此结束；如果没有这个边界说明，用户不容易看出它只负责测试输入。


def _prepare_manager(workspace: str) -> GuiRunManager:  # 新增代码+RealHarnessPermissionTest：函数段开始，准备带运行中 turn 的 manager；如果没有这段，权限登记找不到关联消息。
    manager = GuiRunManager(Path(workspace))  # 新增代码+RealHarnessPermissionTest：创建 GUI run manager；如果没有这一行，权限事件没有状态存储。
    turn = GuiTurn(turn_id="turn_perm", run_id="run_perm", session_id="session_perm", prompt="permission", status="running")  # 新增代码+RealHarnessPermissionTest：构造运行中 turn；如果没有这一行，record_permission_required 不能同步 needs_permission。
    session = manager._session("session_perm")  # 新增代码+RealHarnessPermissionTest：创建关联 session；如果没有这一行，助手消息无法同步状态。
    session.messages.append(GuiMessage(id="msg_perm", role="assistant", text="", turn_id="turn_perm", status="running"))  # 新增代码+RealHarnessPermissionTest：添加助手占位消息；如果没有这一行，权限等待文案不会写入消息。
    manager.turns[turn.turn_id] = turn  # 新增代码+RealHarnessPermissionTest：把 turn 放进 manager；如果没有这一行，权限请求无法关联 turn。
    manager.cancel_events[turn.turn_id] = threading.Event()  # 新增代码+RealHarnessPermissionTest：创建取消信号；如果没有这一行，取消权限等待无法测试。
    manager.active_turn_id = turn.turn_id  # 新增代码+RealHarnessPermissionTest：标记当前 active turn；如果没有这一行，拒绝后释放 busy 的路径没有目标。
    return manager  # 新增代码+RealHarnessPermissionTest：返回准备好的 manager；如果没有这一行，测试拿不到对象。
# 新增代码+RealHarnessPermissionTest：函数段结束，_prepare_manager 到此结束；如果没有这个边界说明，用户不容易看出它只负责准备状态。


def _wait_for_permission_id(manager: GuiRunManager) -> str:  # 新增代码+RealHarnessPermissionTest：函数段开始，等待权限请求登记；如果没有这段，测试可能在请求出现前就决策。
    deadline = time.time() + 5.0  # 新增代码+RealHarnessPermissionTest：设置等待截止时间；如果没有这一行，失败时测试会无限等待。
    while time.time() < deadline:  # 新增代码+RealHarnessPermissionTest：轮询 pending 权限；如果没有这一行，异步线程结果不可控。
        with manager.lock:  # 新增代码+RealHarnessPermissionTest：读取权限字典时加锁；如果没有这一行，可能读到半状态。
            if manager.permissions:  # 新增代码+RealHarnessPermissionTest：检测是否已有请求；如果没有这一行，无法跳出等待。
                return next(iter(manager.permissions))  # 新增代码+RealHarnessPermissionTest：返回第一个请求 id；如果没有这一行，调用方无法提交决策。
        time.sleep(0.02)  # 新增代码+RealHarnessPermissionTest：短暂休眠避免忙等；如果没有这一行，测试会空转占 CPU。
    raise AssertionError("permission request was not recorded")  # 新增代码+RealHarnessPermissionTest：超时给出明确失败；如果没有这一行，失败原因会模糊。
# 新增代码+RealHarnessPermissionTest：函数段结束，_wait_for_permission_id 到此结束；如果没有这个边界说明，用户不容易看出它只负责等待请求。


class GuiAgentPermissionHandshakeTest(unittest.TestCase):  # 新增代码+RealHarnessPermissionTest：测试类段开始，覆盖真实 adapter 权限握手；如果没有这个类，Phase 4 没有自动验收。
    def test_adapter_permission_request_returns_true_after_gui_approve(self) -> None:  # 新增代码+RealHarnessPermissionTest：测试函数开始，验证 GUI 允许会放行 core 权限；如果没有这段，approve 按钮可能只是前端效果。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessPermissionTest：创建隔离 workspace；如果没有这一行，状态文件会污染真实项目。
            manager = _prepare_manager(directory)  # 新增代码+RealHarnessPermissionTest：准备运行中 manager；如果没有这一行，权限请求没有归属。
            result: dict[str, bool] = {}  # 新增代码+RealHarnessPermissionTest：保存线程返回值；如果没有这一行，主线程拿不到权限结果。
            worker = threading.Thread(target=lambda: result.update(ok=manager._ask_permission_for_adapter(_request(), "需要写入文件。")))  # 新增代码+RealHarnessPermissionTest：启动同步权限等待；如果没有这一行，无法模拟真实 core ask_permission。
            worker.start()  # 新增代码+RealHarnessPermissionTest：运行权限等待线程；如果没有这一行，权限请求不会登记。
            request_id = _wait_for_permission_id(manager)  # 新增代码+RealHarnessPermissionTest：等待请求 id；如果没有这一行，决策可能打到空请求。
            manager.decide_permission(request_id, turn_id="turn_perm", decision="approve", reason="测试允许")  # 新增代码+RealHarnessPermissionTest：模拟 GUI 点击允许；如果没有这一行，权限等待不会返回 True。
            worker.join(timeout=5.0)  # 新增代码+RealHarnessPermissionTest：等待权限线程结束；如果没有这一行，测试可能在结果写入前断言。
            event_types = [event.event_type for event in manager.event_store.list_events(limit=20)]  # 新增代码+RealHarnessPermissionTest：读取事件流；如果没有这一行，无法确认弹窗事件写入。
        self.assertTrue(result.get("ok"))  # 新增代码+RealHarnessPermissionTest：确认 approve 放行 core；如果没有这一行，权限握手可能总是拒绝。
        self.assertIn("permission_requested", event_types)  # 新增代码+RealHarnessPermissionTest：确认真实权限请求事件写入；如果没有这一行，GUI 弹窗没有标准来源。
        self.assertIn("permission_answered", event_types)  # 新增代码+RealHarnessPermissionTest：确认回答审计事件写入；如果没有这一行，允许操作无法复盘。
    # 新增代码+RealHarnessPermissionTest：测试函数结束，test_adapter_permission_request_returns_true_after_gui_approve 到此结束；如果没有这个边界说明，用户不容易看出允许路径范围。

    def test_adapter_permission_request_returns_false_after_gui_deny(self) -> None:  # 新增代码+RealHarnessPermissionTest：测试函数开始，验证 GUI 拒绝会阻止 core 权限；如果没有这段，deny 按钮可能不生效。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessPermissionTest：创建隔离 workspace；如果没有这一行，状态文件会污染真实项目。
            manager = _prepare_manager(directory)  # 新增代码+RealHarnessPermissionTest：准备运行中 manager；如果没有这一行，权限请求没有归属。
            result: dict[str, bool] = {}  # 新增代码+RealHarnessPermissionTest：保存线程返回值；如果没有这一行，主线程拿不到权限结果。
            worker = threading.Thread(target=lambda: result.update(ok=manager._ask_permission_for_adapter(_request(), "需要写入文件。")))  # 新增代码+RealHarnessPermissionTest：启动同步权限等待；如果没有这一行，无法模拟真实 core ask_permission。
            worker.start()  # 新增代码+RealHarnessPermissionTest：运行权限等待线程；如果没有这一行，权限请求不会登记。
            request_id = _wait_for_permission_id(manager)  # 新增代码+RealHarnessPermissionTest：等待请求 id；如果没有这一行，决策可能打到空请求。
            manager.decide_permission(request_id, turn_id="turn_perm", decision="deny", reason="测试拒绝")  # 新增代码+RealHarnessPermissionTest：模拟 GUI 点击拒绝；如果没有这一行，权限等待不会返回 False。
            worker.join(timeout=5.0)  # 新增代码+RealHarnessPermissionTest：等待权限线程结束；如果没有这一行，测试可能在结果写入前断言。
        self.assertFalse(result.get("ok"))  # 新增代码+RealHarnessPermissionTest：确认 deny 阻止 core；如果没有这一行，危险工具可能继续执行。
        self.assertEqual("failed", manager.turns["turn_perm"].status)  # 新增代码+RealHarnessPermissionTest：确认拒绝同步为 turn failed；如果没有这一行，GUI 可能继续显示等待。
    # 新增代码+RealHarnessPermissionTest：测试函数结束，test_adapter_permission_request_returns_false_after_gui_deny 到此结束；如果没有这个边界说明，用户不容易看出拒绝路径范围。

    def test_adapter_permission_request_returns_false_when_turn_cancelled(self) -> None:  # 新增代码+RealHarnessPermissionTest：测试函数开始，验证取消会结束权限等待；如果没有这段，cancel 可能被权限弹窗卡住。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessPermissionTest：创建隔离 workspace；如果没有这一行，状态文件会污染真实项目。
            manager = _prepare_manager(directory)  # 新增代码+RealHarnessPermissionTest：准备运行中 manager；如果没有这一行，权限请求没有归属。
            result: dict[str, bool] = {}  # 新增代码+RealHarnessPermissionTest：保存线程返回值；如果没有这一行，主线程拿不到权限结果。
            worker = threading.Thread(target=lambda: result.update(ok=manager._ask_permission_for_adapter(_request(), "需要写入文件。")))  # 新增代码+RealHarnessPermissionTest：启动同步权限等待；如果没有这一行，无法模拟真实 core ask_permission。
            worker.start()  # 新增代码+RealHarnessPermissionTest：运行权限等待线程；如果没有这一行，权限请求不会登记。
            _wait_for_permission_id(manager)  # 新增代码+RealHarnessPermissionTest：确认请求已经进入等待；如果没有这一行，取消可能先于登记发生。
            manager.cancel_events["turn_perm"].set()  # 新增代码+RealHarnessPermissionTest：模拟 GUI 取消本轮；如果没有这一行，权限等待不会被唤醒。
            worker.join(timeout=5.0)  # 新增代码+RealHarnessPermissionTest：等待权限线程结束；如果没有这一行，测试可能过早断言。
        self.assertFalse(result.get("ok"))  # 新增代码+RealHarnessPermissionTest：确认取消按拒绝处理；如果没有这一行，取消后工具可能继续执行。
    # 新增代码+RealHarnessPermissionTest：测试函数结束，test_adapter_permission_request_returns_false_when_turn_cancelled 到此结束；如果没有这个边界说明，用户不容易看出取消权限路径范围。

    def test_write_file_tool_does_not_run_when_gui_permission_denies(self) -> None:  # 新增代码+RealHarnessPermissionTest：测试函数开始，验证写工具被拒绝时不落盘；如果没有这段，真实 agent 可能绕过 GUI 权限写文件。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessPermissionTest：创建隔离 workspace；如果没有这一行，写文件测试可能污染项目。
            target_path = Path(directory) / "denied.txt"  # 新增代码+RealHarnessPermissionTest：准备目标文件路径；如果没有这一行，后续无法断言是否写入。
            write_call = ToolCall(name="write_file", arguments={"path": "denied.txt", "content": "SHOULD_NOT_EXIST"}, call_id="call_write_1")  # 新增代码+RealHarnessPermissionTest：构造写文件工具调用；如果没有这一行，真实权限链不会触发。
            fake_model = ToolCallingFakeModel([ModelMessage(tool_calls=[write_call]), ModelMessage(text="WRITE_DENIED_DONE")])  # 新增代码+RealHarnessPermissionTest：安排假模型先写再回答；如果没有这一行，主循环不会经过写工具。
            request = GuiAgentRunRequest(session_id="session_write", turn_id="turn_write", run_id="run_write", prompt="写入 denied.txt", workspace=directory, provider_id="test-fake")  # 新增代码+RealHarnessPermissionTest：构造真实 adapter 请求；如果没有这一行，adapter 没有工作区。
            events: list[dict[str, object]] = []  # 新增代码+RealHarnessPermissionTest：保存 GUI 事件；如果没有这一行，无法确认工具轨迹。
            adapter = DefaultHarnessGuiAgentAdapter(enabled=True, model_factory=lambda _request: fake_model, permission_requester=lambda _request, _text: False, max_turns=2, allowed_tool_names={"write_file"})  # 新增代码+RealHarnessPermissionTest：启用真实 adapter 并拒绝 GUI 权限；如果没有这一行，写工具可能实际落盘。
            result = adapter.run(request, events.append, lambda: False)  # 新增代码+RealHarnessPermissionTest：运行真实主循环；如果没有这一行，拒绝写入路径不会被测试。
        event_kinds = [str(event.get("kind", "")) for event in events]  # 新增代码+RealHarnessPermissionTest：提取事件类型；如果没有这一行，工具事件断言会难读。
        self.assertEqual("completed", result.status)  # 新增代码+RealHarnessPermissionTest：确认 agent 能从拒绝结果恢复并结束；如果没有这一行，拒绝后主循环可能卡住。
        self.assertFalse(target_path.exists())  # 新增代码+RealHarnessPermissionTest：确认被拒绝文件没有创建；如果没有这一行，安全门禁没有实证。
        self.assertIn("tool_started", event_kinds)  # 新增代码+RealHarnessPermissionTest：确认 GUI 看得到写工具尝试；如果没有这一行，用户不知道 agent 尝试了什么。
        self.assertIn("tool_finished", event_kinds)  # 新增代码+RealHarnessPermissionTest：确认 GUI 看得到写工具拒绝结果；如果没有这一行，TracePanel 会停在 running。
    # 新增代码+RealHarnessPermissionTest：测试函数结束，test_write_file_tool_does_not_run_when_gui_permission_denies 到此结束；如果没有这个边界说明，用户不容易看出写入拒绝范围。
# 新增代码+RealHarnessPermissionTest：测试类段结束，GuiAgentPermissionHandshakeTest 到此结束；如果没有这个边界说明，用户不容易看出本文件覆盖 Phase 4。


if __name__ == "__main__":  # 新增代码+RealHarnessPermissionTest：允许直接运行本测试文件；如果没有这一行，手动排查时不会启动 unittest。
    unittest.main()  # 新增代码+RealHarnessPermissionTest：执行测试主程序；如果没有这一行，直接运行文件不会跑测试。
