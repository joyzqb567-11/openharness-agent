import unittest  # 新增代码+真实模型GUI适配器测试：使用标准库测试真实模型 GUI adapter 合同；如果没有这一行，pytest 无法收集 unittest 测试。


class FakeModelMessage:  # 新增代码+真实模型GUI适配器测试：类段开始，模拟模型返回消息；如果没有这个类，测试必须依赖真实 OpenAI 或 Codex CLI。
    def __init__(self, text: str = "", tool_calls: list[object] | None = None) -> None:  # 新增代码+真实模型GUI适配器测试：函数段开始，保存假模型文本和工具调用；如果没有这段，测试不能构造不同模型结果。
        self.text = text  # 新增代码+真实模型GUI适配器测试：保存模型文本；如果没有这一行，adapter 无法读取最终回答。
        self.tool_calls = tool_calls or []  # 新增代码+真实模型GUI适配器测试：保存工具调用列表；如果没有这一行，adapter 无法识别暂未接线的工具调用。
    # 新增代码+真实模型GUI适配器测试：函数段结束，FakeModelMessage.__init__ 到此结束；如果没有这个边界说明，用户不容易看出假消息字段范围。
# 新增代码+真实模型GUI适配器测试：类段结束，FakeModelMessage 到此结束；如果没有这个边界说明，用户不容易看出测试替身范围。


class FakeChatModel:  # 新增代码+真实模型GUI适配器测试：类段开始，模拟 CodexCliChatModel 的 chat 接口；如果没有这个类，测试会错误地访问真实网络或真实 CLI。
    def __init__(self, message: FakeModelMessage) -> None:  # 新增代码+真实模型GUI适配器测试：函数段开始，注入本次要返回的假消息；如果没有这段，测试不能控制模型输出。
        self.message = message  # 新增代码+真实模型GUI适配器测试：保存假消息；如果没有这一行，chat 调用没有返回内容。
        self.messages_seen: list[list[dict[str, object]]] = []  # 新增代码+真实模型GUI适配器测试：记录 adapter 传给模型的 messages；如果没有这一行，测试无法确认 prompt 真正进入模型。
        self.tools_seen: list[list[dict[str, object]]] = []  # 新增代码+真实模型GUI适配器测试：记录 adapter 传给模型的 tools；如果没有这一行，测试无法确认当前最小版本没有伪造工具。
    # 新增代码+真实模型GUI适配器测试：函数段结束，FakeChatModel.__init__ 到此结束；如果没有这个边界说明，用户不容易看出假模型状态范围。

    def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> FakeModelMessage:  # 新增代码+真实模型GUI适配器测试：函数段开始，模拟模型 chat 方法；如果没有这段，adapter 无法被像真实模型一样调用。
        self.messages_seen.append(messages)  # 新增代码+真实模型GUI适配器测试：记录收到的 messages；如果没有这一行，测试不能判断 adapter 是否传入用户 prompt。
        self.tools_seen.append(tools)  # 新增代码+真实模型GUI适配器测试：记录收到的 tools；如果没有这一行，测试不能判断 adapter 是否误接工具。
        return self.message  # 新增代码+真实模型GUI适配器测试：返回预设消息；如果没有这一行，adapter 会拿不到模型结果。
    # 新增代码+真实模型GUI适配器测试：函数段结束，FakeChatModel.chat 到此结束；如果没有这个边界说明，用户不容易看出模型替身调用范围。
# 新增代码+真实模型GUI适配器测试：类段结束，FakeChatModel 到此结束；如果没有这个边界说明，用户不容易看出测试替身范围。


class RealModelGuiAgentAdapterTest(unittest.TestCase):  # 新增代码+真实模型GUI适配器测试：测试类段开始，锁定 GUI 到真实模型的最小合同；如果没有这个类，fake streaming 可能长期冒充真实模型。
    def _make_request(self, prompt: str = "你好"):  # 新增代码+真实模型GUI适配器测试：helper 段开始，创建 GUI run 请求；如果没有这段，每个测试都要重复构造字段。
        from learning_agent.app.gui_agent_adapter import GuiAgentRunRequest  # 新增代码+真实模型GUI适配器测试：导入请求对象；如果没有这一行，测试无法按正式接口发起 run。

        return GuiAgentRunRequest(session_id="session_real", turn_id="turn_real", run_id="run_real", prompt=prompt, mode="real")  # 新增代码+真实模型GUI适配器测试：返回真实模式请求；如果没有这一行，adapter 不知道本轮身份和输入。
    # 新增代码+真实模型GUI适配器测试：helper 段结束，_make_request 到此结束；如果没有这个边界说明，用户不容易看出请求构造范围。

    def test_real_adapter_emits_completed_events_with_fake_model(self) -> None:  # 新增代码+真实模型GUI适配器测试：测试函数开始，验证真实 adapter 能把模型文本变成 GUI 事件；如果没有这段，完成路径可能仍是 fake streaming。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+真实模型GUI适配器测试：导入待实现真实 adapter；如果没有这一行，测试没有被测对象。

        events: list[dict[str, object]] = []  # 新增代码+真实模型GUI适配器测试：保存 adapter 发出的事件；如果没有这一行，测试无法检查 GUI 可见事件顺序。
        fake_model = FakeChatModel(FakeModelMessage(text="真实模型路径回答"))  # 新增代码+真实模型GUI适配器测试：构造可控假模型；如果没有这一行，测试会依赖外部模型服务。
        adapter = RealModelGuiAgentAdapter(model_factory=lambda: fake_model, connected_provider_reader=lambda: True)  # 新增代码+真实模型GUI适配器测试：注入假模型和已连接状态；如果没有这一行，测试不能隔离真实 OAuth。
        result = adapter.run(self._make_request("你好"), events.append, lambda: False)  # 新增代码+真实模型GUI适配器测试：执行真实 adapter；如果没有这一行，测试没有行为。
        self.assertEqual("completed", result.status)  # 新增代码+真实模型GUI适配器测试：确认结果完成；如果没有这一行，adapter 可能只发事件不返回终态。
        self.assertEqual("真实模型路径回答", result.final_text)  # 新增代码+真实模型GUI适配器测试：确认最终文本来自模型；如果没有这一行，fake 文案可能混进真实路径。
        self.assertNotIn("fake streaming", result.final_text)  # 新增代码+真实模型GUI适配器测试：确认没有退回 fake streaming；如果没有这一行，用户会误以为已连接真实模型。
        self.assertEqual(["turn_started", "message_delta", "message_completed"], [event["kind"] for event in events])  # 新增代码+真实模型GUI适配器测试：确认 GUI 事件顺序；如果没有这一行，前端状态机可能看不到流式和完成。
        self.assertEqual([[{"role": "user", "content": "你好"}]], fake_model.messages_seen)  # 新增代码+真实模型GUI适配器测试：确认 prompt 真正传入模型；如果没有这一行，adapter 可能输出固定文本。
        self.assertEqual([[]], fake_model.tools_seen)  # 新增代码+真实模型GUI适配器测试：确认 V1A 不伪造工具；如果没有这一行，未接线工具可能被误送给模型。
    # 新增代码+真实模型GUI适配器测试：测试函数结束，test_real_adapter_emits_completed_events_with_fake_model 到此结束；如果没有这个边界说明，用户不容易看出完成合同范围。

    def test_real_adapter_fails_when_provider_is_not_connected(self) -> None:  # 新增代码+真实模型GUI适配器测试：测试函数开始，验证未连接提供商时不会偷偷调用模型；如果没有这段，用户未授权也可能触发真实调用。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+真实模型GUI适配器测试：导入待实现真实 adapter；如果没有这一行，测试没有被测对象。

        events: list[dict[str, object]] = []  # 新增代码+真实模型GUI适配器测试：保存失败事件；如果没有这一行，测试无法确认前端能看到错误。
        fake_model = FakeChatModel(FakeModelMessage(text="不应该被调用"))  # 新增代码+真实模型GUI适配器测试：构造不应被调用的假模型；如果没有这一行，测试不能证明连接门禁生效。
        adapter = RealModelGuiAgentAdapter(model_factory=lambda: fake_model, connected_provider_reader=lambda: False)  # 新增代码+真实模型GUI适配器测试：注入未连接状态；如果没有这一行，测试无法覆盖授权门禁。
        result = adapter.run(self._make_request("你好"), events.append, lambda: False)  # 新增代码+真实模型GUI适配器测试：执行真实 adapter；如果没有这一行，测试没有行为。
        self.assertEqual("failed", result.status)  # 新增代码+真实模型GUI适配器测试：确认未连接时失败；如果没有这一行，GUI 可能显示假成功。
        self.assertEqual("real_model_not_connected", result.error_code)  # 新增代码+真实模型GUI适配器测试：确认稳定错误码；如果没有这一行，前端无法引导用户去连接 OpenAI。
        self.assertEqual("turn_failed", events[-1]["kind"])  # 新增代码+真实模型GUI适配器测试：确认发出失败事件；如果没有这一行，前端状态机不会进入 failed。
        self.assertEqual([], fake_model.messages_seen)  # 新增代码+真实模型GUI适配器测试：确认未授权时没有调用模型；如果没有这一行，可能泄露 prompt 到未授权后端。
    # 新增代码+真实模型GUI适配器测试：测试函数结束，test_real_adapter_fails_when_provider_is_not_connected 到此结束；如果没有这个边界说明，用户不容易看出连接门禁范围。

    def test_real_adapter_fails_fast_when_model_requests_tools_before_tool_bridge_exists(self) -> None:  # 新增代码+真实模型GUI适配器测试：测试函数开始，验证工具调用未接线时显式失败；如果没有这段，模型工具调用可能被静默丢弃。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+真实模型GUI适配器测试：导入待实现真实 adapter；如果没有这一行，测试没有被测对象。

        events: list[dict[str, object]] = []  # 新增代码+真实模型GUI适配器测试：保存失败事件；如果没有这一行，测试无法检查错误码。
        fake_model = FakeChatModel(FakeModelMessage(tool_calls=[object()]))  # 新增代码+真实模型GUI适配器测试：构造请求工具调用的假模型；如果没有这一行，未接线工具路径无法测试。
        adapter = RealModelGuiAgentAdapter(model_factory=lambda: fake_model, connected_provider_reader=lambda: True)  # 新增代码+真实模型GUI适配器测试：注入已连接状态；如果没有这一行，测试会停在连接门禁。
        result = adapter.run(self._make_request("请读取文件"), events.append, lambda: False)  # 新增代码+真实模型GUI适配器测试：执行会产生工具调用的模型轮次；如果没有这一行，测试没有行为。
        self.assertEqual("failed", result.status)  # 新增代码+真实模型GUI适配器测试：确认工具调用未接线时失败；如果没有这一行，GUI 可能显示空回答。
        self.assertEqual("real_model_tools_not_connected", result.error_code)  # 新增代码+真实模型GUI适配器测试：确认稳定错误码；如果没有这一行，后续 V1B 无法锁住风险。
        self.assertEqual("turn_failed", events[-1]["kind"])  # 新增代码+真实模型GUI适配器测试：确认最后事件是失败；如果没有这一行，前端可能一直等待工具结果。
    # 新增代码+真实模型GUI适配器测试：测试函数结束，test_real_adapter_fails_fast_when_model_requests_tools_before_tool_bridge_exists 到此结束；如果没有这个边界说明，用户不容易看出工具门禁范围。

    def test_real_adapter_cancel_before_model_call_emits_turn_cancelled(self) -> None:  # 新增代码+真实模型GUI适配器测试：测试函数开始，验证模型调用前取消不会访问模型；如果没有这段，用户取消后仍可能产生真实后端调用。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+真实模型GUI适配器测试：导入真实 adapter；如果没有这一行，测试没有被测对象。

        events: list[dict[str, object]] = []  # 新增代码+真实模型GUI适配器测试：保存取消事件；如果没有这一行，测试无法检查事件顺序。
        fake_model = FakeChatModel(FakeModelMessage(text="不应该被调用"))  # 新增代码+真实模型GUI适配器测试：构造不应被调用的模型；如果没有这一行，无法证明取消门禁生效。
        adapter = RealModelGuiAgentAdapter(model_factory=lambda: fake_model, connected_provider_reader=lambda: True)  # 新增代码+真实模型GUI适配器测试：注入已连接状态；如果没有这一行，测试会停在未连接失败。
        result = adapter.run(self._make_request("请取消"), events.append, lambda: True)  # 新增代码+真实模型GUI适配器测试：在模型调用前就返回取消；如果没有这一行，取消路径没有行为。
        self.assertEqual("cancelled", result.status)  # 新增代码+真实模型GUI适配器测试：确认结果取消；如果没有这一行，取消可能被误判失败或完成。
        self.assertEqual(["turn_started", "turn_cancelled"], [event["kind"] for event in events])  # 新增代码+真实模型GUI适配器测试：确认只发启动和取消；如果没有这一行，取消前可能已经发出模型文本。
        self.assertEqual([], fake_model.messages_seen)  # 新增代码+真实模型GUI适配器测试：确认未调用模型；如果没有这一行，取消前调用后端的问题会漏掉。
    # 新增代码+真实模型GUI适配器测试：测试函数结束，test_real_adapter_cancel_before_model_call_emits_turn_cancelled 到此结束；如果没有这个边界说明，用户不容易看出前置取消范围。

    def test_real_adapter_cancel_after_model_call_before_completion(self) -> None:  # 新增代码+真实模型GUI适配器测试：测试函数开始，验证模型返回后取消不会写完成；如果没有这段，用户取消可能被最终回答覆盖。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+真实模型GUI适配器测试：导入真实 adapter；如果没有这一行，测试没有被测对象。

        events: list[dict[str, object]] = []  # 新增代码+真实模型GUI适配器测试：保存事件；如果没有这一行，测试无法确认没有 completed。
        fake_model = FakeChatModel(FakeModelMessage(text="模型已经返回但不应完成"))  # 新增代码+真实模型GUI适配器测试：构造会返回文本的模型；如果没有这一行，无法覆盖模型后取消。
        adapter = RealModelGuiAgentAdapter(model_factory=lambda: fake_model, connected_provider_reader=lambda: True)  # 新增代码+真实模型GUI适配器测试：注入已连接状态；如果没有这一行，测试不能进入模型调用后。
        def is_cancelled() -> bool:  # 新增代码+真实模型GUI适配器测试：函数段开始，模型调用后才返回取消；如果没有这段，无法模拟真实长请求完成后的取消竞态。
            return bool(fake_model.messages_seen)  # 新增代码+真实模型GUI适配器测试：模型已被调用后视为取消；如果没有这一行，取消条件不会触发。
        # 新增代码+真实模型GUI适配器测试：函数段结束，is_cancelled 到此结束；如果没有这个边界说明，用户不容易看出取消触发条件。
        result = adapter.run(self._make_request("请在模型返回后取消"), events.append, is_cancelled)  # 新增代码+真实模型GUI适配器测试：执行后置取消场景；如果没有这一行，测试没有行为。
        self.assertEqual("cancelled", result.status)  # 新增代码+真实模型GUI适配器测试：确认结果取消；如果没有这一行，后置取消可能被覆盖成 completed。
        self.assertEqual(["turn_started", "turn_cancelled"], [event["kind"] for event in events])  # 新增代码+真实模型GUI适配器测试：确认没有 message_completed；如果没有这一行，取消竞态可能漏掉。
        self.assertEqual(1, len(fake_model.messages_seen))  # 新增代码+真实模型GUI适配器测试：确认模型确实被调用过；如果没有这一行，测试会退化成前置取消。
    # 新增代码+真实模型GUI适配器测试：测试函数结束，test_real_adapter_cancel_after_model_call_before_completion 到此结束；如果没有这个边界说明，用户不容易看出后置取消范围。

    def test_real_adapter_remote_error_emits_turn_failed_without_fake_fallback(self) -> None:  # 新增代码+真实模型GUI适配器测试：测试函数开始，验证远端错误不会回退 fake；如果没有这段，真实失败可能被假回答掩盖。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+真实模型GUI适配器测试：导入真实 adapter；如果没有这一行，测试没有被测对象。

        class FailingChatModel:  # 新增代码+真实模型GUI适配器测试：类段开始，模拟远端模型失败；如果没有这个类，测试无法稳定触发 remote 500。
            def chat(self, _messages, _tools):  # 新增代码+真实模型GUI适配器测试：函数段开始，模拟 chat 抛错；如果没有这段，远端失败路径无法覆盖。
                raise RuntimeError("remote 500")  # 新增代码+真实模型GUI适配器测试：抛出远端错误；如果没有这一行，adapter 不会进入异常处理。
            # 新增代码+真实模型GUI适配器测试：函数段结束，FailingChatModel.chat 到此结束；如果没有这个边界说明，用户不容易看出失败来源。
        # 新增代码+真实模型GUI适配器测试：类段结束，FailingChatModel 到此结束；如果没有这个边界说明，用户不容易看出失败替身范围。

        events: list[dict[str, object]] = []  # 新增代码+真实模型GUI适配器测试：保存失败事件；如果没有这一行，测试无法检查事件流。
        adapter = RealModelGuiAgentAdapter(model_factory=FailingChatModel, connected_provider_reader=lambda: True)  # 新增代码+真实模型GUI适配器测试：注入失败模型；如果没有这一行，测试无法触发远端错误。
        result = adapter.run(self._make_request("触发远端错误"), events.append, lambda: False)  # 新增代码+真实模型GUI适配器测试：执行失败场景；如果没有这一行，测试没有行为。
        self.assertEqual("failed", result.status)  # 新增代码+真实模型GUI适配器测试：确认结果失败；如果没有这一行，远端错误可能被误判完成。
        self.assertEqual("real_model_failed", result.error_code)  # 新增代码+真实模型GUI适配器测试：确认稳定错误码；如果没有这一行，前端无法区分真实模型失败。
        self.assertNotIn("fake streaming", result.error_message)  # 新增代码+真实模型GUI适配器测试：确认没有 fake fallback 文案；如果没有这一行，模拟回复可能混入失败路径。
        self.assertNotIn("message_completed", [event["kind"] for event in events])  # 新增代码+真实模型GUI适配器测试：确认失败时不发完成；如果没有这一行，前端可能同时看到失败和完成。
        self.assertEqual("turn_failed", events[-1]["kind"])  # 新增代码+真实模型GUI适配器测试：确认最后事件是失败；如果没有这一行，GUI 状态机不会进入 failed。
    # 新增代码+真实模型GUI适配器测试：测试函数结束，test_real_adapter_remote_error_emits_turn_failed_without_fake_fallback 到此结束；如果没有这个边界说明，用户不容易看出远端失败范围。

    def test_real_adapter_long_answer_chunks_delta_without_losing_text(self) -> None:  # 新增代码+真实模型GUI适配器测试：测试函数开始，验证长回答会拆成多个 delta 且不丢字；如果没有这段，长回复可能撑爆单个 GUI 事件。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+真实模型GUI适配器测试：导入真实 adapter；如果没有这一行，测试没有被测对象。

        events: list[dict[str, object]] = []  # 新增代码+真实模型GUI适配器测试：保存长文本事件；如果没有这一行，测试无法拼回 delta。
        long_text = "真实模型长回答-" * 12 + "END"  # 新增代码+真实模型GUI适配器测试：构造长回答文本；如果没有这一行，切片逻辑可能只测到单块。
        fake_model = FakeChatModel(FakeModelMessage(text=long_text))  # 新增代码+真实模型GUI适配器测试：构造返回长文本的假模型；如果没有这一行，测试会依赖真实模型。
        adapter = RealModelGuiAgentAdapter(model_factory=lambda: fake_model, connected_provider_reader=lambda: True, delta_chunk_size=16)  # 新增代码+真实模型GUI适配器测试：使用小切片强制多个 delta；如果没有这一行，默认大小可能让测试只有一个 delta。
        result = adapter.run(self._make_request("请输出长回答"), events.append, lambda: False)  # 新增代码+真实模型GUI适配器测试：执行长文本场景；如果没有这一行，测试没有行为。
        deltas = [event["payload"]["text_delta"] for event in events if event["kind"] == "message_delta"]  # 新增代码+真实模型GUI适配器测试：提取所有文本增量；如果没有这一行，无法确认拼接结果。
        self.assertEqual("completed", result.status)  # 新增代码+真实模型GUI适配器测试：确认长回答完成；如果没有这一行，切片过程可能中途失败。
        self.assertGreaterEqual(len(deltas), 2)  # 新增代码+真实模型GUI适配器测试：确认至少拆成两块；如果没有这一行，长回答仍可能单事件输出。
        self.assertEqual(long_text, "".join(str(delta) for delta in deltas))  # 新增代码+真实模型GUI适配器测试：确认 delta 拼接无损；如果没有这一行，前端可能显示缺字或乱序。
        self.assertTrue(result.final_text.endswith("END"))  # 新增代码+真实模型GUI适配器测试：确认最终文本尾部保留；如果没有这一行，长回答结尾截断会漏掉。
    # 新增代码+真实模型GUI适配器测试：测试函数结束，test_real_adapter_long_answer_chunks_delta_without_losing_text 到此结束；如果没有这个边界说明，用户不容易看出长文本合同范围。
# 新增代码+真实模型GUI适配器测试：测试类段结束，RealModelGuiAgentAdapterTest 到此结束；如果没有这个边界说明，用户不容易看出测试文件范围。


if __name__ == "__main__":  # 新增代码+真实模型GUI适配器测试：允许直接运行本文件；如果没有这一行，手动排查时不会自动启动 unittest。
    unittest.main()  # 新增代码+真实模型GUI适配器测试：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行测试。
