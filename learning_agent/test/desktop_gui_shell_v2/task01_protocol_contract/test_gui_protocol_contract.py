import unittest  # 新增代码+GuiV2ProtocolContractTest：使用标准库 unittest 验证 V2 协议合同；如果没有这一行，蓝图指定的测试命令无法收集用例。


class GuiV2ProtocolContractTest(unittest.TestCase):  # 新增代码+GuiV2ProtocolContractTest：测试类段开始，集中锁定桌面 GUI V2 协议形状；如果没有这个类，协议漂移不会被后端测试发现。
    def test_schema_version_is_v2(self) -> None:  # 新增代码+GuiV2ProtocolContractTest：函数段开始，验证协议版本升级到 2；如果没有这段测试，前后端可能继续误用 V1 合同。
        from learning_agent.app import gui_protocol  # 新增代码+GuiV2ProtocolContractTest：导入待实现协议模块；如果没有这一行，测试没有被测对象。

        self.assertEqual(2, gui_protocol.GUI_V2_SCHEMA_VERSION)  # 新增代码+GuiV2ProtocolContractTest：确认 schema_version 为 2；如果没有这一行，V2 前端无法可靠识别后端能力。
    # 新增代码+GuiV2ProtocolContractTest：函数段结束，test_schema_version_is_v2 到此结束；如果没有这个边界说明，用户不容易看出版本测试范围。

    def test_error_response_shape_contains_required_fields(self) -> None:  # 新增代码+GuiV2ProtocolContractTest：函数段开始，验证结构化错误响应；如果没有这段测试，前端会继续只看到 HTTP 状态码。
        from learning_agent.app.gui_protocol import make_error_response  # 新增代码+GuiV2ProtocolContractTest：导入错误响应 helper；如果没有这一行，测试无法锁定错误形状。

        payload = make_error_response("agent_busy", "当前已有任务运行。", request_id="request_123")  # 新增代码+GuiV2ProtocolContractTest：构造一个 V2 错误 payload；如果没有这一行，后续断言没有输入。
        self.assertIs(payload["ok"], False)  # 新增代码+GuiV2ProtocolContractTest：确认错误响应显式 ok=false；如果没有这一行，前端无法用统一字段识别失败。
        self.assertEqual("agent_busy", payload["code"])  # 新增代码+GuiV2ProtocolContractTest：确认保留机器可读 code；如果没有这一行，前端无法区分 busy、not_found、unauthorized。
        self.assertEqual("当前已有任务运行。", payload["message"])  # 新增代码+GuiV2ProtocolContractTest：确认保留人类可读 message；如果没有这一行，GUI 只能显示泛化失败。
        self.assertEqual("request_123", payload["request_id"])  # 新增代码+GuiV2ProtocolContractTest：确认保留 request_id；如果没有这一行，日志和界面无法对齐同一请求。
    # 新增代码+GuiV2ProtocolContractTest：函数段结束，test_error_response_shape_contains_required_fields 到此结束；如果没有这个边界说明，用户不容易看出错误合同范围。

    def test_event_shape_contains_required_fields(self) -> None:  # 新增代码+GuiV2ProtocolContractTest：函数段开始，验证 V2 事件统一形状；如果没有这段测试，状态机可能收到缺字段事件。
        from learning_agent.app.gui_protocol import make_event  # 新增代码+GuiV2ProtocolContractTest：导入事件 helper；如果没有这一行，测试无法锁定事件生成规则。

        event = make_event("turn_started", 7, {"status": "running"}, run_id="run_1", turn_id="turn_1")  # 新增代码+GuiV2ProtocolContractTest：构造一条 V2 事件；如果没有这一行，后续断言没有事件样本。
        self.assertEqual(7, event["sequence"])  # 新增代码+GuiV2ProtocolContractTest：确认事件序号保留；如果没有这一行，前端无法稳定排序。
        self.assertIsInstance(event["event_id"], str)  # 新增代码+GuiV2ProtocolContractTest：确认事件有唯一 id；如果没有这一行，React 列表 key 和去重会不稳定。
        self.assertGreater(len(str(event["event_id"])), 0)  # 新增代码+GuiV2ProtocolContractTest：确认 event_id 不为空；如果没有这一行，空 id 会破坏事件去重。
        self.assertEqual("turn_started", event["kind"])  # 新增代码+GuiV2ProtocolContractTest：确认事件类型保留；如果没有这一行，前端状态机不知道如何处理事件。
        self.assertIsInstance(event["created_at"], str)  # 新增代码+GuiV2ProtocolContractTest：确认事件创建时间是可序列化字符串；如果没有这一行，前端展示时间会缺依据。
        self.assertEqual("run_1", event["run_id"])  # 新增代码+GuiV2ProtocolContractTest：确认 run_id 保留；如果没有这一行，状态面板无法按 run 聚合。
        self.assertEqual("turn_1", event["turn_id"])  # 新增代码+GuiV2ProtocolContractTest：确认 turn_id 保留；如果没有这一行，线程消息无法和事件对齐。
        self.assertEqual({"status": "running"}, event["payload"])  # 新增代码+GuiV2ProtocolContractTest：确认 payload 原样保留；如果没有这一行，事件详情会丢失业务数据。
    # 新增代码+GuiV2ProtocolContractTest：函数段结束，test_event_shape_contains_required_fields 到此结束；如果没有这个边界说明，用户不容易看出事件合同范围。

    def test_message_part_shape_supports_required_part_kinds(self) -> None:  # 新增代码+GuiV2ProtocolContractTest：函数段开始，验证消息片段支持蓝图要求的所有类型；如果没有这段测试，流式文本、工具和错误可能各走各的形状。
        from learning_agent.app.gui_protocol import GUI_V2_MESSAGE_PART_KINDS, make_message_part  # 新增代码+GuiV2ProtocolContractTest：导入消息片段类型和 helper；如果没有这一行，测试无法锁定消息 part 合同。

        required_kinds = {"text_delta", "final_text", "refusal", "tool_call", "tool_result", "error"}  # 新增代码+GuiV2ProtocolContractTest：列出 V2 必须支持的消息片段类型；如果没有这一行，测试目标不清楚。
        self.assertTrue(required_kinds.issubset(GUI_V2_MESSAGE_PART_KINDS))  # 新增代码+GuiV2ProtocolContractTest：确认常量覆盖所有必需类型；如果没有这一行，新增 UI 分支可能缺协议枚举。
        for kind in required_kinds:  # 新增代码+GuiV2ProtocolContractTest：逐个构造消息片段；如果没有这一行，只检查常量无法证明 helper 支持。
            part = make_message_part(kind, {"value": kind})  # 新增代码+GuiV2ProtocolContractTest：构造当前类型的 part；如果没有这一行，后续断言没有具体样本。
            self.assertEqual(kind, part["kind"])  # 新增代码+GuiV2ProtocolContractTest：确认 part kind 保留；如果没有这一行，前端无法根据 kind 渲染。
            self.assertEqual({"value": kind}, part["payload"])  # 新增代码+GuiV2ProtocolContractTest：确认 part payload 保留；如果没有这一行，文本或工具详情会丢失。
    # 新增代码+GuiV2ProtocolContractTest：函数段结束，test_message_part_shape_supports_required_part_kinds 到此结束；如果没有这个边界说明，用户不容易看出消息 part 合同范围。
# 新增代码+GuiV2ProtocolContractTest：测试类段结束，GuiV2ProtocolContractTest 到此结束；如果没有这个边界说明，用户不容易看出本文件只测 V2 协议。


if __name__ == "__main__":  # 新增代码+GuiV2ProtocolContractTest：允许直接运行本测试文件；如果没有这一行，用户手动排查时要记完整模块命令。
    unittest.main()  # 新增代码+GuiV2ProtocolContractTest：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行测试。
