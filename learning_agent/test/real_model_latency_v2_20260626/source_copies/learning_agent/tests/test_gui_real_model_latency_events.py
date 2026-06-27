import unittest  # 新增代码+真实模型延迟可观测性测试：使用标准库 unittest 承载 GUI 真实模型事件测试；如果没有这行，pytest 无法自动收集这些合同测试。

from learning_agent.models.streaming import ModelStreamEvent  # 新增代码+真实模型延迟可观测性测试：复用后端流式模型事件对象；如果没有这行，测试会继续用松散 dict，无法锁定 Task 1 的协议。


class FakeStreamingModel:  # 新增代码+真实模型延迟可观测性测试：类段开始，模拟会逐步吐出状态和文本的真实模型；如果没有这个类，测试只能依赖真实 OpenAI 网络。
    def __init__(self, events: list[ModelStreamEvent]) -> None:  # 新增代码+真实模型延迟可观测性测试：函数段开始，保存本次要回放的模型事件；如果没有这段，测试无法控制连接、首 token、完成的顺序。
        self.events = events  # 新增代码+真实模型延迟可观测性测试：保存流式事件脚本；如果没有这行，stream_chat 没有可回放的数据源。
        self.messages_seen: list[list[dict[str, object]]] = []  # 新增代码+真实模型延迟可观测性测试：记录 adapter 传入的消息；如果没有这行，测试无法证明用户 prompt 真正进入模型层。
        self.contexts_seen: list[tuple[str, str, str]] = []  # 新增代码+真实模型延迟可观测性测试：记录 turn/provider/model 上下文；如果没有这行，测试无法证明底部模型选择被传入流式模型。
    # 新增代码+真实模型延迟可观测性测试：函数段结束，FakeStreamingModel.__init__ 到此结束；如果没有这个边界说明，用户不容易看出假模型状态范围。

    def stream_chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]], *, turn_id: str, provider_id: str, model_id: str):  # 新增代码+真实模型延迟可观测性测试：函数段开始，模拟真实流式聊天接口；如果没有这段，adapter 只能继续走阻塞式 chat。
        self.messages_seen.append(messages)  # 新增代码+真实模型延迟可观测性测试：记录用户消息；如果没有这行，prompt 丢失也不会被测试发现。
        self.contexts_seen.append((turn_id, provider_id, model_id))  # 新增代码+真实模型延迟可观测性测试：记录调用上下文；如果没有这行，模型路由信息丢失也不会被测试发现。
        for event in self.events:  # 新增代码+真实模型延迟可观测性测试：逐个回放模型事件；如果没有这行，GUI 无法收到连接和首 token 阶段。
            yield event  # 新增代码+真实模型延迟可观测性测试：把事件交给 adapter；如果没有这行，测试永远看不到流式输出。
    # 新增代码+真实模型延迟可观测性测试：函数段结束，FakeStreamingModel.stream_chat 到此结束；如果没有这个边界说明，用户不容易看出模型流式替身范围。
# 新增代码+真实模型延迟可观测性测试：类段结束，FakeStreamingModel 到此结束；如果没有这个边界说明，用户不容易看出测试替身范围。


class RealModelLatencyEventsTest(unittest.TestCase):  # 新增代码+真实模型延迟可观测性测试：测试类段开始，锁定真实模型 adapter 的延迟阶段事件；如果没有这个类，GUI 慢在哪里仍然没有自动化保护。
    def _make_request(self):  # 新增代码+真实模型延迟可观测性测试：helper 段开始，创建带 provider/model 的真实 GUI 请求；如果没有这段，每个测试都要重复构造字段。
        from learning_agent.app.gui_agent_adapter import GuiAgentRunRequest  # 新增代码+真实模型延迟可观测性测试：延迟导入请求类型；如果没有这行，测试无法按正式 adapter 合同发起 run。

        return GuiAgentRunRequest(session_id="session_latency", turn_id="turn_latency", run_id="run_latency", prompt="你好", mode="real", provider_id="openai", model_id="gpt-5.5", reasoning_effort="ultra", permission_mode="full-access")  # 新增代码+真实模型延迟可观测性测试：返回完整真实模型请求；如果没有这行，adapter 没有可观测的模型路由上下文。
    # 新增代码+真实模型延迟可观测性测试：helper 段结束，_make_request 到此结束；如果没有这个边界说明，用户不容易看出请求构造范围。

    def test_real_adapter_forwards_streaming_model_phases_before_final_text(self) -> None:  # 新增代码+真实模型延迟可观测性测试：测试函数开始，验证模型阶段先于最终正文进入 GUI；如果没有这段，用户仍可能等待两分钟却只看到 running。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+真实模型延迟可观测性测试：导入被测真实 adapter；如果没有这行，测试没有执行对象。

        request = self._make_request()  # 新增代码+真实模型延迟可观测性测试：创建本轮 GUI 请求；如果没有这行，后续事件无法绑定 run/turn。
        model = FakeStreamingModel([  # 新增代码+真实模型延迟可观测性测试：构造会先发连接状态再发文本的假模型；如果没有这行，测试不能复现慢请求的中间状态。
            ModelStreamEvent("status", "connecting", "正在连接 OpenAI", 1.0, 15, 1, request.turn_id, "openai", "gpt-5.5"),  # 新增代码+真实模型延迟可观测性测试：模拟连接中状态；如果没有这行，adapter 的 status 冒泡不会被验证。
            ModelStreamEvent("delta", "first_delta", "你好", 2.0, 30, 2, request.turn_id, "openai", "gpt-5.5"),  # 新增代码+真实模型延迟可观测性测试：模拟首个模型增量；如果没有这行，首 token 可观测性不会被验证。
            ModelStreamEvent("completed", "completed", "完成", 3.0, 40, 3, request.turn_id, "openai", "gpt-5.5"),  # 新增代码+真实模型延迟可观测性测试：模拟模型完成；如果没有这行，完成阶段不会被验证。
        ])  # 新增代码+真实模型延迟可观测性测试：假模型事件列表结束；如果没有这行，Python 语法不完整。
        events: list[dict[str, object]] = []  # 新增代码+真实模型延迟可观测性测试：收集 adapter 发给 GUI 的事件；如果没有这行，断言无法观察输出。
        adapter = RealModelGuiAgentAdapter(model_factory=lambda: model, connected_provider_reader=lambda: True)  # 新增代码+真实模型延迟可观测性测试：注入假流式模型和已连接状态；如果没有这行，测试会访问真实 OAuth 或真实网络。
        result = adapter.run(request, events.append, lambda: False)  # 新增代码+真实模型延迟可观测性测试：执行真实 adapter；如果没有这行，测试没有行为样本。
        event_kinds = [event["kind"] for event in events]  # 新增代码+真实模型延迟可观测性测试：提取 GUI 事件名；如果没有这行，后续断言会重复遍历事件。
        self.assertEqual("completed", result.status)  # 新增代码+真实模型延迟可观测性测试：确认流式模型轮次完成；如果没有这行，adapter 失败也可能被误认为有可观测阶段。
        self.assertEqual("你好", result.final_text)  # 新增代码+真实模型延迟可观测性测试：确认最终文本来自模型 delta；如果没有这行，adapter 可能只发状态不累积正文。
        self.assertEqual(["turn_started", "model_call_started", "model_call_status", "model_first_delta", "message_delta", "message_completed", "model_call_completed"], event_kinds)  # 新增代码+真实模型延迟可观测性测试：锁定 GUI 可见事件顺序；如果没有这行，阶段事件可能出现在最终文本之后而失去价值。
        self.assertEqual("connecting", events[2]["payload"]["phase"])  # 新增代码+真实模型延迟可观测性测试：确认状态事件保留模型阶段；如果没有这行，前端无法显示卡在连接还是卡在首 token。
        self.assertEqual(15, events[2]["payload"]["elapsed_ms"])  # 新增代码+真实模型延迟可观测性测试：确认状态事件保留耗时；如果没有这行，右侧诊断面板无法解释慢在哪里。
        self.assertEqual("gpt-5.5", events[3]["payload"]["model_id"])  # 新增代码+真实模型延迟可观测性测试：确认首 token 事件携带模型名；如果没有这行，用户无法确认真实调用的是底部选中的模型。
        self.assertEqual([[{"role": "user", "content": "你好"}]], model.messages_seen)  # 新增代码+真实模型延迟可观测性测试：确认用户 prompt 传入流式模型；如果没有这行，固定假输出也可能通过测试。
        self.assertEqual([("turn_latency", "openai", "gpt-5.5")], model.contexts_seen)  # 新增代码+真实模型延迟可观测性测试：确认 turn/provider/model 上下文传入模型；如果没有这行，stale 事件过滤和模型路由都没有保障。
    # 新增代码+真实模型延迟可观测性测试：测试函数结束，test_real_adapter_forwards_streaming_model_phases_before_final_text 到此结束；如果没有这个边界说明，用户不容易看出阶段冒泡测试范围。

    def test_real_adapter_ignores_stale_stream_events_from_other_turns(self) -> None:  # 新增代码+真实模型延迟可观测性测试：测试函数开始，验证旧 turn 的流式事件不会污染当前 GUI；如果没有这段，取消后的旧输出可能写进新消息。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+真实模型延迟可观测性测试：导入被测真实 adapter；如果没有这行，测试没有执行对象。

        request = self._make_request()  # 新增代码+真实模型延迟可观测性测试：创建当前 turn 请求；如果没有这行，stale 过滤没有当前基准。
        model = FakeStreamingModel([  # 新增代码+真实模型延迟可观测性测试：构造混有旧 turn 和当前 turn 的事件流；如果没有这行，stale 过滤没有输入样本。
            ModelStreamEvent("delta", "first_delta", "旧输出", 1.0, 10, 1, "old_turn", "openai", "gpt-5.5"),  # 新增代码+真实模型延迟可观测性测试：模拟旧 turn 遗留增量；如果没有这行，污染风险不会被覆盖。
            ModelStreamEvent("delta", "first_delta", "新输出", 2.0, 20, 2, request.turn_id, "openai", "gpt-5.5"),  # 新增代码+真实模型延迟可观测性测试：模拟当前 turn 首个增量；如果没有这行，adapter 无法完成当前回答。
            ModelStreamEvent("completed", "completed", "完成", 3.0, 30, 3, request.turn_id, "openai", "gpt-5.5"),  # 新增代码+真实模型延迟可观测性测试：模拟当前 turn 完成；如果没有这行，adapter 会停在 running。
        ])  # 新增代码+真实模型延迟可观测性测试：假模型事件列表结束；如果没有这行，Python 语法不完整。
        events: list[dict[str, object]] = []  # 新增代码+真实模型延迟可观测性测试：收集 GUI 事件；如果没有这行，无法断言旧输出是否漏出。
        adapter = RealModelGuiAgentAdapter(model_factory=lambda: model, connected_provider_reader=lambda: True)  # 新增代码+真实模型延迟可观测性测试：注入混合事件流假模型；如果没有这行，测试会访问真实模型。
        result = adapter.run(request, events.append, lambda: False)  # 新增代码+真实模型延迟可观测性测试：执行真实 adapter；如果没有这行，stale 过滤没有行为样本。
        deltas = [event["payload"]["text_delta"] for event in events if event["kind"] == "message_delta"]  # 新增代码+真实模型延迟可观测性测试：提取所有正文增量；如果没有这行，旧输出污染无法被准确定位。
        self.assertEqual("completed", result.status)  # 新增代码+真实模型延迟可观测性测试：确认过滤旧事件后当前 turn 仍能完成；如果没有这行，过滤逻辑可能误杀当前事件。
        self.assertEqual(["新输出"], deltas)  # 新增代码+真实模型延迟可观测性测试：确认只有当前 turn 文本进入 GUI；如果没有这行，旧 turn 输出会悄悄污染当前会话。
        self.assertEqual("新输出", result.final_text)  # 新增代码+真实模型延迟可观测性测试：确认最终文本不含旧输出；如果没有这行，message_delta 过滤和 final_text 累积可能不一致。
    # 新增代码+真实模型延迟可观测性测试：测试函数结束，test_real_adapter_ignores_stale_stream_events_from_other_turns 到此结束；如果没有这个边界说明，用户不容易看出 stale 事件防护范围。

    def test_cancelled_turn_ignores_late_delta_and_emits_cancelled_state(self) -> None:  # 新增代码+真实模型取消竞态测试：测试函数开始，验证取消后迟到 delta 不进入聊天区；如果没有这段，用户点取消后仍可能看到旧输出。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+真实模型取消竞态测试：导入真实 adapter；如果没有这行，测试没有执行对象。

        request = self._make_request()  # 新增代码+真实模型取消竞态测试：创建待取消的 GUI 请求；如果没有这行，事件没有 turn/run 归属。
        model = FakeStreamingModel([ModelStreamEvent("delta", "first_delta", "取消后的旧输出", 1.0, 10, 1, request.turn_id, "openai", "gpt-5.5")])  # 新增代码+真实模型取消竞态测试：模拟取消后模型才吐出迟到 delta；如果没有这行，竞态风险没有输入样本。
        events: list[dict[str, object]] = []  # 新增代码+真实模型取消竞态测试：收集 adapter 事件；如果没有这行，无法检查迟到输出是否泄漏。
        adapter = RealModelGuiAgentAdapter(model_factory=lambda: model, connected_provider_reader=lambda: True)  # 新增代码+真实模型取消竞态测试：注入假模型和已连接状态；如果没有这行，测试会触碰真实网络。
        result = adapter.run(request, events.append, lambda: True)  # 新增代码+真实模型取消竞态测试：用始终已取消的信号执行 adapter；如果没有这行，取消路径不会被触发。
        event_kinds = [event["kind"] for event in events]  # 新增代码+真实模型取消竞态测试：提取事件类型；如果没有这行，后续断言会重复遍历。
        leaked_deltas = [event for event in events if event["kind"] == "message_delta"]  # 新增代码+真实模型取消竞态测试：提取可能泄漏的正文增量；如果没有这行，旧输出污染难以判断。
        self.assertEqual("cancelled", result.status)  # 新增代码+真实模型取消竞态测试：确认 adapter 返回取消终态；如果没有这行，取消可能被误当完成。
        self.assertIn("model_call_status", event_kinds)  # 新增代码+真实模型取消竞态测试：确认先发取消请求状态；如果没有这行，右侧状态条看不到取消已进入后端。
        self.assertIn("turn_cancelled", event_kinds)  # 新增代码+真实模型取消竞态测试：确认发出取消终态事件；如果没有这行，前端可能停在 cancelling。
        self.assertEqual([], leaked_deltas)  # 新增代码+真实模型取消竞态测试：确认取消后的旧 delta 没有进入消息区；如果没有这行，迟到输出会污染当前会话。
    # 新增代码+真实模型取消竞态测试：测试函数结束，test_cancelled_turn_ignores_late_delta_and_emits_cancelled_state 到此结束；如果没有这个边界说明，用户不容易看出取消竞态范围。

    def test_real_adapter_passes_cancel_checker_to_cancellable_streaming_model(self) -> None:  # 新增代码+CodexCliCancelBridgeTest：测试函数开始，验证 adapter 会把 GUI 取消回调传给支持它的模型；如果没有这段，Codex CLI 进程级取消可能再次断线。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+CodexCliCancelBridgeTest：导入真实 adapter；如果没有这行，测试没有执行对象。

        class CancellableStreamingModel:  # 新增代码+CodexCliCancelBridgeTest：类段开始，模拟支持 is_cancelled 的 Codex CLI 模型；如果没有这个类，测试无法证明 adapter 传参。
            def __init__(self) -> None:  # 新增代码+CodexCliCancelBridgeTest：函数段开始，准备记录收到的取消回调；如果没有这段，断言没有观察点。
                self.cancel_checker_seen = None  # 新增代码+CodexCliCancelBridgeTest：保存模型收到的取消回调；如果没有这一行，测试无法确认传参是否发生。
            # 新增代码+CodexCliCancelBridgeTest：函数段结束，CancellableStreamingModel.__init__ 到此结束；如果没有边界说明，用户不容易看出初始化范围。

            def stream_chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]], *, turn_id: str, provider_id: str, model_id: str, is_cancelled=None):  # 新增代码+CodexCliCancelBridgeTest：函数段开始，声明可接收 is_cancelled 的流式模型入口；如果没有这段，adapter 没有可传取消回调的目标。
                del messages, tools, provider_id, model_id  # 新增代码+CodexCliCancelBridgeTest：明确测试模型不需要这些参数；如果没有这一行，读者会误以为它们影响断言。
                self.cancel_checker_seen = is_cancelled  # 新增代码+CodexCliCancelBridgeTest：记录 adapter 传入的取消回调；如果没有这一行，测试无法锁定取消链路。
                yield ModelStreamEvent("status", "connecting", "正在连接", 1.0, 10, 1, turn_id, "openai", "gpt-5.5")  # 新增代码+CodexCliCancelBridgeTest：发出一个当前 turn 状态事件触发 adapter 消费；如果没有这一行，adapter 不会进入取消检查分支。
            # 新增代码+CodexCliCancelBridgeTest：函数段结束，CancellableStreamingModel.stream_chat 到此结束；如果没有边界说明，用户不容易看出它只验证传参。
        # 新增代码+CodexCliCancelBridgeTest：类段结束，CancellableStreamingModel 到此结束；如果没有边界说明，用户不容易看出测试替身范围。

        request = self._make_request()  # 新增代码+CodexCliCancelBridgeTest：创建真实 GUI 请求；如果没有这行，adapter 没有 turn/provider/model 上下文。
        model = CancellableStreamingModel()  # 新增代码+CodexCliCancelBridgeTest：创建支持取消回调的假模型；如果没有这一行，测试没有传参接收者。
        events: list[dict[str, object]] = []  # 新增代码+CodexCliCancelBridgeTest：收集 adapter 事件；如果没有这行，无法确认取消终态。
        cancel_checks = {"count": 0}  # 新增代码+CodexCliCancelBridgeTest：记录 adapter 已经检查取消几次；如果没有这一行，测试会在模型调用前就被早取消拦截。
        def cancel_after_model_starts() -> bool:  # 新增代码+CodexCliCancelBridgeTest：函数段开始，第一次检查不取消、进入模型后再取消；如果没有这段，无法验证 is_cancelled 是否传到模型层。
            cancel_checks["count"] += 1  # 新增代码+CodexCliCancelBridgeTest：累计检查次数；如果没有这一行，函数无法区分早检查和流式检查。
            return cancel_checks["count"] >= 2  # 新增代码+CodexCliCancelBridgeTest：第二次及以后才返回取消；如果没有这一行，adapter 会在模型创建前直接取消。
        # 新增代码+CodexCliCancelBridgeTest：函数段结束，cancel_after_model_starts 到此结束；如果没有边界说明，用户不容易看出它只控制测试时序。
        result = RealModelGuiAgentAdapter(model_factory=lambda: model, connected_provider_reader=lambda: True).run(request, events.append, cancel_after_model_starts)  # 修改代码+CodexCliCancelBridgeTest：用进入模型后才生效的取消信号执行 adapter；如果没有这一行，取消链路不会被触发。
        self.assertIsNotNone(model.cancel_checker_seen)  # 新增代码+CodexCliCancelBridgeTest：确认模型收到了取消回调；如果没有这一行，adapter 可能仍没有把按钮连到模型层。
        self.assertEqual("cancelled", result.status)  # 新增代码+CodexCliCancelBridgeTest：确认 adapter 把本轮闭合为取消；如果没有这一行，GUI 可能停在 running 或 failed。
        self.assertIn("turn_cancelled", [event["kind"] for event in events])  # 新增代码+CodexCliCancelBridgeTest：确认取消终态写入 GUI 事件；如果没有这一行，前端状态机无法更新。
    # 新增代码+CodexCliCancelBridgeTest：测试函数结束，test_real_adapter_passes_cancel_checker_to_cancellable_streaming_model 到此结束；如果没有边界说明，用户不容易看出 adapter 到模型的取消合同。

    def test_new_turn_can_stream_after_previous_cancelled_turn(self) -> None:  # 新增代码+真实模型取消竞态测试：测试函数开始，验证取消旧 turn 后新 turn 仍可正常流式输出；如果没有这段，取消信号可能误伤下一轮。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+真实模型取消竞态测试：导入真实 adapter；如果没有这行，测试没有执行对象。

        cancelled_request = self._make_request()  # 新增代码+真实模型取消竞态测试：创建旧的取消请求；如果没有这行，第一轮没有 turn 基准。
        cancelled_model = FakeStreamingModel([ModelStreamEvent("delta", "first_delta", "旧输出", 1.0, 10, 1, cancelled_request.turn_id, "openai", "gpt-5.5")])  # 新增代码+真实模型取消竞态测试：模拟旧 turn 迟到输出；如果没有这行，旧 turn 污染风险没有输入。
        cancelled_events: list[dict[str, object]] = []  # 新增代码+真实模型取消竞态测试：收集旧 turn 事件；如果没有这行，无法独立验证旧轮。
        RealModelGuiAgentAdapter(model_factory=lambda: cancelled_model, connected_provider_reader=lambda: True).run(cancelled_request, cancelled_events.append, lambda: True)  # 新增代码+真实模型取消竞态测试：执行旧的已取消 turn；如果没有这行，下一轮不是真正经过取消后场景。
        new_request = self._make_request()  # 新增代码+真实模型取消竞态测试：创建新 turn 请求；如果没有这行，新轮没有独立上下文。
        new_request.turn_id = "turn_after_cancel"  # 新增代码+真实模型取消竞态测试：给新 turn 一个不同 id；如果没有这行，测试不能证明取消信号按 turn 隔离。
        new_request.run_id = "run_after_cancel"  # 新增代码+真实模型取消竞态测试：给新 run 一个不同 id；如果没有这行，事件归属不够清楚。
        new_model = FakeStreamingModel([ModelStreamEvent("delta", "first_delta", "新输出", 2.0, 20, 1, new_request.turn_id, "openai", "gpt-5.5"), ModelStreamEvent("completed", "completed", "完成", 3.0, 30, 2, new_request.turn_id, "openai", "gpt-5.5")])  # 新增代码+真实模型取消竞态测试：模拟新 turn 正常流式输出和完成；如果没有这行，无法证明取消后仍能继续使用模型。
        new_events: list[dict[str, object]] = []  # 新增代码+真实模型取消竞态测试：收集新 turn 事件；如果没有这行，无法检查新输出。
        result = RealModelGuiAgentAdapter(model_factory=lambda: new_model, connected_provider_reader=lambda: True).run(new_request, new_events.append, lambda: False)  # 新增代码+真实模型取消竞态测试：执行新 turn 且不取消；如果没有这行，取消隔离没有行为样本。
        new_deltas = [event["payload"]["text_delta"] for event in new_events if event["kind"] == "message_delta"]  # 新增代码+真实模型取消竞态测试：提取新 turn 文本增量；如果没有这行，输出是否正常无法判断。
        self.assertEqual("completed", result.status)  # 新增代码+真实模型取消竞态测试：确认新 turn 能完成；如果没有这行，取消可能让后续运行一直失败。
        self.assertEqual(["新输出"], new_deltas)  # 新增代码+真实模型取消竞态测试：确认新 turn 输出正常且不含旧输出；如果没有这行，取消隔离失效会漏掉。
    # 新增代码+真实模型取消竞态测试：测试函数结束，test_new_turn_can_stream_after_previous_cancelled_turn 到此结束；如果没有这个边界说明，用户不容易看出跨 turn 取消隔离范围。

    def test_real_adapter_fast_fails_disconnected_provider_without_creating_model(self) -> None:  # 新增代码+ModelFailureState测试：测试函数开始，验证未连接 provider 会快速失败且不创建模型；如果没有这段，GUI 可能继续慢慢启动 codex.exe。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+ModelFailureState测试：导入真实 adapter；如果没有这行，测试没有执行对象。
        request = self._make_request()  # 新增代码+ModelFailureState测试：创建带 OpenAI 模型上下文的请求；如果没有这行，门禁测试没有 provider/model 输入。
        factory_calls: list[str] = []  # 新增代码+ModelFailureState测试：记录模型工厂是否被调用；如果没有这行，无法证明未连接时没有启动模型。
        def factory():  # 新增代码+ModelFailureState测试：函数段开始，创建会记录调用的模型工厂；如果没有这段，测试无法捕捉错误的模型创建。
            factory_calls.append("called")  # 新增代码+ModelFailureState测试：记录一次工厂调用；如果没有这行，断言无法判断是否启动模型。
            return FakeStreamingModel([])  # 新增代码+ModelFailureState测试：返回空假模型；如果没有这行，签名虽然存在但无法完成返回。
        # 新增代码+ModelFailureState测试：函数段结束，factory 到此结束；如果没有边界说明，用户不容易看出它只是探针。
        events: list[dict[str, object]] = []  # 新增代码+ModelFailureState测试：收集 adapter 发给 GUI 的事件；如果没有这行，无法验证用户可见错误。
        adapter = RealModelGuiAgentAdapter(model_factory=factory, connected_provider_reader=lambda: False)  # 新增代码+ModelFailureState测试：注入未连接状态；如果没有这行，测试会访问真实 OAuth。
        result = adapter.run(request, events.append, lambda: False)  # 新增代码+ModelFailureState测试：执行真实 adapter；如果没有这行，测试没有行为样本。
        self.assertEqual("failed", result.status)  # 新增代码+ModelFailureState测试：确认未连接会失败；如果没有这行，假成功无法被发现。
        self.assertEqual("real_model_not_connected", result.error_code)  # 新增代码+ModelFailureState测试：确认错误码稳定；如果没有这行，前端无法机器处理未连接。
        self.assertIn("请先连接 OpenAI", result.error_message)  # 新增代码+ModelFailureState测试：确认中文可读提示；如果没有这行，用户会继续看到英文内部错误。
        self.assertEqual([], factory_calls)  # 新增代码+ModelFailureState测试：确认模型工厂没有被调用；如果没有这行，未连接仍可能启动 codex.exe。
    # 新增代码+ModelFailureState测试：测试函数结束，test_real_adapter_fast_fails_disconnected_provider_without_creating_model 到此结束；如果没有边界说明，用户不容易看出快速失败范围。

    def test_real_adapter_records_unsupported_chatgpt_oauth_model_failure(self) -> None:  # 新增代码+ModelFailureState测试：测试函数开始，验证 ChatGPT OAuth 拒绝模型时会记录 model_unsupported；如果没有这段，底部模型菜单无法标记不可用模型。
        from learning_agent.app.gui_agent_adapter import RealModelGuiAgentAdapter  # 新增代码+ModelFailureState测试：导入真实 adapter；如果没有这行，测试没有执行对象。
        request = self._make_request()  # 新增代码+ModelFailureState测试：创建真实模型请求；如果没有这行，模型失败没有上下文。
        request.model_id = "gpt-4.1"  # 新增代码+ModelFailureState测试：模拟用户选择 OAuth 账号不支持的模型；如果没有这行，失败记录无法验证具体模型。
        raw_error = '{"detail":"The gpt-4.1 model is not supported when using Codex with a ChatGPT account."}'  # 新增代码+ModelFailureState测试：构造 Codex/OpenAI 常见不支持错误；如果没有这行，分类逻辑没有事实样本。
        model = FakeStreamingModel([ModelStreamEvent("error", "failed", raw_error, 1.0, 42, 1, request.turn_id, "openai", "gpt-4.1")])  # 新增代码+ModelFailureState测试：构造只返回错误的流式模型；如果没有这行，adapter 不会进入 error 分支。
        recorded: list[tuple[str, str, str, str]] = []  # 新增代码+ModelFailureState测试：收集失败记录器收到的参数；如果没有这行，无法证明 provider/model/error_kind 被写出。
        events: list[dict[str, object]] = []  # 新增代码+ModelFailureState测试：收集 GUI 事件；如果没有这行，无法验证状态面板 metadata。
        adapter = RealModelGuiAgentAdapter(model_factory=lambda: model, connected_provider_reader=lambda: True, model_failure_recorder=lambda provider, model_id, kind, message: recorded.append((provider, model_id, kind, message)))  # 新增代码+ModelFailureState测试：注入已连接状态和记录器；如果没有这行，测试会访问真实模型或真实配置文件。
        result = adapter.run(request, events.append, lambda: False)  # 新增代码+ModelFailureState测试：执行真实 adapter；如果没有这行，测试没有行为样本。
        failed_events = [event for event in events if event["kind"] == "model_call_failed"]  # 新增代码+ModelFailureState测试：提取模型失败事件；如果没有这行，metadata 断言会很混乱。
        self.assertEqual("failed", result.status)  # 新增代码+ModelFailureState测试：确认 turn 失败；如果没有这行，错误可能被误当完成。
        self.assertEqual("model_unsupported", result.error_code)  # 新增代码+ModelFailureState测试：确认错误码是模型不支持；如果没有这行，前端无法区分普通失败。
        self.assertEqual("model_unsupported", recorded[0][2])  # 新增代码+ModelFailureState测试：确认记录器收到 error_kind；如果没有这行，provider catalog 无法按蓝图保存失败种类。
        self.assertEqual(("openai", "gpt-4.1"), (recorded[0][0], recorded[0][1]))  # 新增代码+ModelFailureState测试：确认记录器收到 provider 和 model；如果没有这行，失败标记可能挂到错误模型。
        self.assertEqual("model_unsupported", failed_events[0]["payload"]["metadata"]["error_kind"])  # 新增代码+ModelFailureState测试：确认 GUI 事件也带稳定错误种类；如果没有这行，右侧状态面板无法解释失败类型。
    # 新增代码+ModelFailureState测试：测试函数结束，test_real_adapter_records_unsupported_chatgpt_oauth_model_failure 到此结束；如果没有边界说明，用户不容易看出模型不支持记录范围。
# 新增代码+真实模型延迟可观测性测试：测试类段结束，RealModelLatencyEventsTest 到此结束；如果没有这个边界说明，用户不容易看出本文件覆盖范围。


if __name__ == "__main__":  # 新增代码+真实模型延迟可观测性测试：允许直接运行本测试文件；如果没有这行，手动排查时不会自动启动 unittest。
    unittest.main()  # 新增代码+真实模型延迟可观测性测试：启动 unittest 主程序；如果没有这行，直接运行文件不会执行测试。
