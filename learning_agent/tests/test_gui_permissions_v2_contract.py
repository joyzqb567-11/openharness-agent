import tempfile  # 新增代码+DesktopGUIPermissionsV2Test：创建临时 workspace；如果没有这行，权限 V2 测试会污染真实项目 memory。
import unittest  # 新增代码+DesktopGUIPermissionsV2Test：使用 unittest 写蓝图要求的合同测试；如果没有这行，测试命令无法发现这些验收。
from pathlib import Path  # 新增代码+DesktopGUIPermissionsV2Test：用 Path 管理临时目录；如果没有这行，Windows 路径拼接会更脆弱。

from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DesktopGUIPermissionsV2Test：读取后端状态事件流；如果没有这行，测试无法确认 trace panel 可见事件。


class GuiPermissionsV2ContractTests(unittest.TestCase):  # 新增代码+DesktopGUIPermissionsV2Test：测试类段开始，锁住权限 V2 合同；如果没有这个类，蓝图里的权限验收没有自动化保护。
    def test_permission_request_payload_has_v2_fields_and_redacts_sensitive_text(self) -> None:  # 新增代码+DesktopGUIPermissionsV2Test：测试方法段开始，验证字段完整和脱敏；如果没有这段，GUI 可能暴露本机路径或密钥。
        from learning_agent.app.gui_permissions import normalize_permission_request_fields, permission_payload_from_request  # 新增代码+DesktopGUIPermissionsV2Test：导入待实现 helper；如果没有这行，测试无法驱动后端抽象。
        from types import SimpleNamespace  # 新增代码+DesktopGUIPermissionsV2Test：创建轻量对象模拟权限请求；如果没有这行，helper 单元测试需要依赖 bridge dataclass。

        fields = normalize_permission_request_fields(  # 新增代码+DesktopGUIPermissionsV2Test：构造带敏感内容的权限字段；如果没有这行，无法验证规范化入口。
            request_id=" perm_v2 ",  # 新增代码+DesktopGUIPermissionsV2Test：传入带空格的 request_id；如果没有这行，测试覆盖不到 id 清理。
            turn_id=" turn_v2 ",  # 新增代码+DesktopGUIPermissionsV2Test：传入带空格的 turn_id；如果没有这行，测试覆盖不到 turn 清理。
            run_id="run_v2",  # 新增代码+DesktopGUIPermissionsV2Test：传入 run_id；如果没有这行，测试无法确认 trace 聚合字段保留。
            session_id="session_v2",  # 新增代码+DesktopGUIPermissionsV2Test：传入 session_id；如果没有这行，测试无法确认会话归属字段保留。
            tool_name="mcp__computer-use__open_application",  # 新增代码+DesktopGUIPermissionsV2Test：传入工具名；如果没有这行，测试无法确认 V2 工具来源字段。
            app_name="PowerShell",  # 新增代码+DesktopGUIPermissionsV2Test：传入应用名；如果没有这行，测试无法确认用户可读来源字段。
            reason=r"需要读取 C:\Users\joyzq\.ssh\id_rsa 并使用 sk-secret-token",  # 新增代码+DesktopGUIPermissionsV2Test：传入敏感路径和密钥；如果没有这行，脱敏测试没有危险样本。
            risk_summary=r"可能访问 C:\Users\joyzq\Desktop\secret.txt 和 Bearer abc123xyz",  # 新增代码+DesktopGUIPermissionsV2Test：传入风险摘要敏感样本；如果没有这行，风险文案脱敏没有覆盖。
            created_at=123.5,  # 新增代码+DesktopGUIPermissionsV2Test：固定创建时间；如果没有这行，断言时间字段会不稳定。
        )  # 新增代码+DesktopGUIPermissionsV2Test：字段构造结束；如果没有这行，函数调用语法不完整。
        payload = permission_payload_from_request(SimpleNamespace(**fields))  # 新增代码+DesktopGUIPermissionsV2Test：把规范化字段转成事件 payload；如果没有这行，无法验证对外合同。

        self.assertEqual(payload["request_id"], "perm_v2")  # 新增代码+DesktopGUIPermissionsV2Test：确认 request_id 已清理；如果没有这行，空格问题可能漏掉。
        self.assertEqual(payload["turn_id"], "turn_v2")  # 新增代码+DesktopGUIPermissionsV2Test：确认 turn_id 已清理；如果没有这行，turn 归属可能错位。
        self.assertEqual(payload["run_id"], "run_v2")  # 新增代码+DesktopGUIPermissionsV2Test：确认 run_id 保留；如果没有这行，trace panel 可能无法按 run 聚合。
        self.assertEqual(payload["tool_name"], "mcp__computer-use__open_application")  # 新增代码+DesktopGUIPermissionsV2Test：确认工具名保留；如果没有这行，用户不知道哪个工具要权限。
        self.assertEqual(payload["created_at"], 123.5)  # 新增代码+DesktopGUIPermissionsV2Test：确认创建时间保留；如果没有这行，审计排序可能退化。
        self.assertIn("PowerShell", payload["action_summary"])  # 新增代码+DesktopGUIPermissionsV2Test：确认动作摘要包含应用名；如果没有这行，弹窗标题会太抽象。
        self.assertNotIn("C:\\Users\\joyzq", payload["reason"])  # 新增代码+DesktopGUIPermissionsV2Test：确认原因不暴露本机路径；如果没有这行，隐私泄露可能漏检。
        self.assertNotIn("sk-secret-token", payload["reason"])  # 新增代码+DesktopGUIPermissionsV2Test：确认原因不暴露密钥；如果没有这行，密钥泄露可能漏检。
        self.assertNotIn("Bearer abc123xyz", payload["risk_summary"])  # 新增代码+DesktopGUIPermissionsV2Test：确认风险摘要不暴露 bearer token；如果没有这行，风险文案可能泄露凭证。
    # 新增代码+DesktopGUIPermissionsV2Test：测试方法段结束；如果没有这个边界，初学者不易看出字段与脱敏验收范围。

    def test_decision_normalization_and_duplicate_answer_keep_first_result(self) -> None:  # 新增代码+DesktopGUIPermissionsV2Test：测试方法段开始，验证决策规范化和重复保护；如果没有这段，双击按钮可能改写审计结果。
        from learning_agent.app.gui_bridge import GuiBridgeError, GuiRunManager  # 新增代码+DesktopGUIPermissionsV2Test：导入权限管理和结构化错误；如果没有这行，测试无法直接检查后端合同。
        from learning_agent.app.gui_permissions import normalize_permission_decision  # 新增代码+DesktopGUIPermissionsV2Test：导入决策规范化 helper；如果没有这行，大小写和别名合同没有覆盖。

        self.assertEqual(normalize_permission_decision(" APPROVED "), "approve")  # 新增代码+DesktopGUIPermissionsV2Test：确认允许别名归一；如果没有这行，前端文案变化可能被后端拒绝。
        self.assertEqual(normalize_permission_decision("Rejected"), "deny")  # 新增代码+DesktopGUIPermissionsV2Test：确认拒绝别名归一；如果没有这行，拒绝别名可能写入失败。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIPermissionsV2Test：创建临时 workspace；如果没有这行，权限状态会写入真实目录。
            manager = GuiRunManager(Path(directory))  # 新增代码+DesktopGUIPermissionsV2Test：创建被测管理器；如果没有这行，测试没有业务对象。
            manager.record_permission_required("perm_twice", app_name="Chrome", tool_name="browser.open", reason="需要打开网页", risk_summary="低风险")  # 新增代码+DesktopGUIPermissionsV2Test：登记 pending 权限；如果没有这行，决策会变成 404。
            first_payload = manager.decide_permission("perm_twice", decision="APPROVED", reason="第一次点击允许")  # 新增代码+DesktopGUIPermissionsV2Test：第一次允许；如果没有这行，重复决策没有基准。
            with self.assertRaises(GuiBridgeError) as context:  # 新增代码+DesktopGUIPermissionsV2Test：期待第二次回答被拒；如果没有这行，409 合同无法断言。
                manager.decide_permission("perm_twice", decision="deny", reason="第二次点击拒绝")  # 新增代码+DesktopGUIPermissionsV2Test：第二次回答同一请求；如果没有这行，无法触发重复保护。
            stored_permission = manager.permissions["perm_twice"]  # 新增代码+DesktopGUIPermissionsV2Test：读取已保存权限；如果没有这行，无法确认首次结果未被改写。

        self.assertEqual(first_payload["decision"], "approve")  # 新增代码+DesktopGUIPermissionsV2Test：确认首次结果为允许；如果没有这行，规范化可能没有生效。
        self.assertEqual(context.exception.code, "permission_already_answered")  # 新增代码+DesktopGUIPermissionsV2Test：确认重复回答结构化错误码；如果没有这行，前端无法稳定提示。
        self.assertEqual(stored_permission.decision, "approve")  # 新增代码+DesktopGUIPermissionsV2Test：确认重复拒绝没有覆盖首次允许；如果没有这行，审计结果可能被双击改写。
    # 新增代码+DesktopGUIPermissionsV2Test：测试方法段结束；如果没有这个边界，初学者不易看出重复决策验收范围。

    def test_manager_permission_request_contains_v2_audit_fields(self) -> None:  # 新增代码+DesktopGUIPermissionsV2Test：测试方法段开始，验证 manager 发出的权限事件字段；如果没有这段，bridge 可能绕过 helper。
        from learning_agent.app.gui_bridge import GuiMessage, GuiRunManager, GuiSession, GuiTurn  # 新增代码+DesktopGUIPermissionsV2Test：导入 GUI 状态数据结构；如果没有这行，测试无法模拟运行中 turn。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIPermissionsV2Test：创建临时 workspace；如果没有这行，事件流会污染真实项目。
            workspace = Path(directory)  # 新增代码+DesktopGUIPermissionsV2Test：转成 Path；如果没有这行，后续路径拼接会重复转换。
            manager = GuiRunManager(workspace)  # 新增代码+DesktopGUIPermissionsV2Test：创建被测管理器；如果没有这行，测试没有后端状态对象。
            turn = GuiTurn(turn_id="turn_v2", run_id="run_v2", session_id="session_v2", prompt="需要权限", status="running")  # 新增代码+DesktopGUIPermissionsV2Test：构造运行中 turn；如果没有这行，权限请求缺少 run/session 来源。
            manager.turns[turn.turn_id] = turn  # 新增代码+DesktopGUIPermissionsV2Test：登记 turn；如果没有这行，record_permission_required 找不到关联状态。
            manager.sessions[turn.session_id] = GuiSession(session_id=turn.session_id, messages=[GuiMessage(id="msg_v2", role="assistant", text="", turn_id=turn.turn_id, status="running")], last_turn_id=turn.turn_id)  # 新增代码+DesktopGUIPermissionsV2Test：登记助手占位消息；如果没有这行，needs_permission 不会同步到消息。
            manager.record_permission_required("perm_v2", turn_id=turn.turn_id, app_name="PowerShell", tool_name="mcp__computer-use__run", reason="需要执行命令", risk_summary="可能修改文件")  # 新增代码+DesktopGUIPermissionsV2Test：登记 V2 权限请求；如果没有这行，事件流没有权限事件。
            events = StatusEventStore(workspace / "memory" / "status").list_events()  # 新增代码+DesktopGUIPermissionsV2Test：读取事件流；如果没有这行，无法检查对外 payload。

        permission_event = next(event for event in events if event.event_type == "permission_required")  # 新增代码+DesktopGUIPermissionsV2Test：找到权限请求事件；如果没有这行，断言会混到生命周期事件。
        self.assertEqual(permission_event.payload["request_id"], "perm_v2")  # 新增代码+DesktopGUIPermissionsV2Test：确认请求 id；如果没有这行，前端无法定位请求。
        self.assertEqual(permission_event.payload["turn_id"], "turn_v2")  # 新增代码+DesktopGUIPermissionsV2Test：确认 turn id；如果没有这行，弹窗提交会错位。
        self.assertEqual(permission_event.payload["run_id"], "run_v2")  # 新增代码+DesktopGUIPermissionsV2Test：确认 run id；如果没有这行，trace panel 聚合会缺字段。
        self.assertEqual(permission_event.payload["tool_name"], "mcp__computer-use__run")  # 新增代码+DesktopGUIPermissionsV2Test：确认工具名；如果没有这行，用户看不到工具来源。
        self.assertIn("created_at", permission_event.payload)  # 新增代码+DesktopGUIPermissionsV2Test：确认创建时间；如果没有这行，审计排序缺依据。
        self.assertIn("action_summary", permission_event.payload)  # 新增代码+DesktopGUIPermissionsV2Test：确认动作摘要；如果没有这行，前端弹窗只能拼字段。
    # 新增代码+DesktopGUIPermissionsV2Test：测试方法段结束；如果没有这个边界，初学者不易看出 manager 合同验收范围。

    def test_denied_permission_emits_visible_thread_failure_and_trace_event(self) -> None:  # 新增代码+DesktopGUIPermissionsV2Test：测试方法段开始，验证拒绝权限后的可见失败与审计事件；如果没有这段，用户拒绝后任务可能静默悬挂。
        from learning_agent.app.gui_bridge import GuiMessage, GuiRunManager, GuiSession, GuiTurn  # 新增代码+DesktopGUIPermissionsV2Test：导入 GUI 状态数据结构；如果没有这行，测试无法模拟等待权限的 turn。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+DesktopGUIPermissionsV2Test：创建临时 workspace；如果没有这行，事件会写入真实项目。
            workspace = Path(directory)  # 新增代码+DesktopGUIPermissionsV2Test：转成 Path；如果没有这行，事件路径拼接会重复转换。
            manager = GuiRunManager(workspace)  # 新增代码+DesktopGUIPermissionsV2Test：创建被测管理器；如果没有这行，测试没有权限状态对象。
            turn = GuiTurn(turn_id="turn_deny", run_id="run_deny", session_id="session_deny", prompt="需要危险权限", status="running")  # 新增代码+DesktopGUIPermissionsV2Test：构造运行中 turn；如果没有这行，拒绝权限无法转成失败终态。
            manager.turns[turn.turn_id] = turn  # 新增代码+DesktopGUIPermissionsV2Test：登记 turn；如果没有这行，权限拒绝找不到运行对象。
            manager.sessions[turn.session_id] = GuiSession(session_id=turn.session_id, messages=[GuiMessage(id="msg_deny", role="assistant", text="", turn_id=turn.turn_id, status="running")], last_turn_id=turn.turn_id)  # 新增代码+DesktopGUIPermissionsV2Test：登记助手消息；如果没有这行，失败文案无法同步到线程消息。
            manager.record_permission_required("perm_deny_visible", turn_id=turn.turn_id, app_name="PowerShell", tool_name="mcp__computer-use__run", reason="需要执行命令", risk_summary="高风险")  # 新增代码+DesktopGUIPermissionsV2Test：登记待拒绝权限；如果没有这行，拒绝决策没有目标。
            manager.decide_permission("perm_deny_visible", turn_id=turn.turn_id, decision="deny", reason="用户拒绝危险操作")  # 新增代码+DesktopGUIPermissionsV2Test：执行拒绝；如果没有这行，不会产生失败和审计事件。
            events = StatusEventStore(workspace / "memory" / "status").list_events()  # 新增代码+DesktopGUIPermissionsV2Test：读取事件流；如果没有这行，无法验证可见事件。

        event_types = [event.event_type for event in events]  # 新增代码+DesktopGUIPermissionsV2Test：提取事件类型；如果没有这行，多个断言要重复遍历。
        self.assertIn("gui_turn_failed", event_types)  # 新增代码+DesktopGUIPermissionsV2Test：确认主线程可见失败事件；如果没有这行，拒绝权限不会显示在对话中。
        self.assertIn("permission_answered", event_types)  # 新增代码+DesktopGUIPermissionsV2Test：确认 trace panel 可见审计事件；如果没有这行，用户无法复盘拒绝决策。
    # 新增代码+DesktopGUIPermissionsV2Test：测试方法段结束；如果没有这个边界，初学者不易看出拒绝权限验收范围。


if __name__ == "__main__":  # 新增代码+DesktopGUIPermissionsV2Test：允许直接运行本测试文件；如果没有这行，手动调试只能用模块命令。
    unittest.main()  # 新增代码+DesktopGUIPermissionsV2Test：启动 unittest；如果没有这行，直接运行文件不会执行测试。
