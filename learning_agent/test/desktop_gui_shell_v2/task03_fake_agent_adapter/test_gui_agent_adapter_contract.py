import tempfile  # 新增代码+GuiAgentAdapterContractTest：创建临时工作区测试 bridge manager；如果没有这一行，测试会污染真实 memory。
import time  # 新增代码+GuiAgentAdapterContractTest：等待异步 run manager 写事件；如果没有这一行，测试会和后台线程抢时序。
import unittest  # 新增代码+GuiAgentAdapterContractTest：使用标准库 unittest 承载 adapter 合同；如果没有这一行，蓝图命令无法收集测试。
from pathlib import Path  # 新增代码+GuiAgentAdapterContractTest：使用 Path 定位临时工作区和 golden fixture；如果没有这一行，路径拼接容易出错。


class GuiAgentAdapterContractTest(unittest.TestCase):  # 新增代码+GuiAgentAdapterContractTest：测试类段开始，锁定 GUI agent adapter 边界；如果没有这个类，fake/real adapter 边界不会被自动验证。
    def _collect_fake_events(self, prompt: str, trace_id: str = "", cancel_after_delta: bool = False):  # 新增代码+GuiAgentAdapterContractTest：helper 段开始，运行 fake adapter 并收集事件；如果没有这段，各测试会重复样板代码。
        from learning_agent.app.gui_agent_adapter import FakeStreamingGuiAgentAdapter, GuiAgentRunRequest  # 新增代码+GuiAgentAdapterContractTest：导入待实现 fake adapter 和请求对象；如果没有这一行，测试没有被测对象。

        events: list[dict[str, object]] = []  # 新增代码+GuiAgentAdapterContractTest：保存 adapter emit 的事件；如果没有这一行，后续无法断言顺序。
        request = GuiAgentRunRequest(session_id="session_a", turn_id="turn_a", run_id="run_a", prompt=prompt, trace_id=trace_id)  # 新增代码+GuiAgentAdapterContractTest：构造 GUI run 请求；如果没有这一行，adapter 不知道本轮身份。
        def emit_event(event: dict[str, object]) -> None:  # 新增代码+GuiAgentAdapterContractTest：函数段开始，收集 adapter 事件；如果没有这段，adapter 输出无法被测试观察。
            events.append(event)  # 新增代码+GuiAgentAdapterContractTest：追加事件；如果没有这一行，事件会丢失。
        # 新增代码+GuiAgentAdapterContractTest：函数段结束，emit_event 到此结束；如果没有这个边界说明，用户不容易看出收集范围。
        def is_cancelled() -> bool:  # 新增代码+GuiAgentAdapterContractTest：函数段开始，模拟取消信号；如果没有这段，取消路径无法稳定测试。
            return cancel_after_delta and any(event.get("kind") == "message_delta" for event in events)  # 新增代码+GuiAgentAdapterContractTest：在首个 delta 后返回取消；如果没有这一行，adapter 不会进入 deterministic cancel 路径。
        # 新增代码+GuiAgentAdapterContractTest：函数段结束，is_cancelled 到此结束；如果没有这个边界说明，用户不容易看出取消条件。
        result = FakeStreamingGuiAgentAdapter().run(request, emit_event, is_cancelled)  # 新增代码+GuiAgentAdapterContractTest：执行 fake adapter；如果没有这一行，测试没有行为。
        return result, events  # 新增代码+GuiAgentAdapterContractTest：返回结果和事件；如果没有这一行，调用方拿不到断言对象。
    # 新增代码+GuiAgentAdapterContractTest：helper 段结束，_collect_fake_events 到此结束；如果没有这个边界说明，用户不容易看出 fake 收集范围。

    def test_fake_streaming_adapter_emits_started_delta_and_completed(self) -> None:  # 新增代码+GuiAgentAdapterContractTest：测试函数开始，验证 fake adapter 正常流式事件；如果没有这段，V2-Core 没有稳定流式基线。
        result, events = self._collect_fake_events("请分析当前项目")  # 新增代码+GuiAgentAdapterContractTest：运行普通 prompt；如果没有这一行，后续没有事件样本。
        self.assertEqual("completed", result.status)  # 新增代码+GuiAgentAdapterContractTest：确认结果完成；如果没有这一行，adapter 可能只发事件不返回终态。
        self.assertEqual("turn_started", events[0]["kind"])  # 新增代码+GuiAgentAdapterContractTest：确认第一条是 turn_started；如果没有这一行，前端无法识别运行起点。
        self.assertIn("message_delta", [event["kind"] for event in events])  # 新增代码+GuiAgentAdapterContractTest：确认至少一个 delta；如果没有这一行，GUI 可能退回等待最终答案。
        self.assertEqual("message_completed", events[-1]["kind"])  # 新增代码+GuiAgentAdapterContractTest：确认最后完成；如果没有这一行，线程会停在 running。
    # 新增代码+GuiAgentAdapterContractTest：测试函数结束，test_fake_streaming_adapter_emits_started_delta_and_completed 到此结束；如果没有这个边界说明，用户不容易看出流式合同范围。

    def test_fake_streaming_adapter_propagates_cancellation(self) -> None:  # 新增代码+GuiAgentAdapterContractTest：测试函数开始，验证 fake adapter 可取消；如果没有这段，取消按钮语义无法在 V2-Core 固定。
        result, events = self._collect_fake_events("请执行一个较长任务", cancel_after_delta=True)  # 新增代码+GuiAgentAdapterContractTest：在首个 delta 后模拟取消；如果没有这一行，取消路径不会触发。
        self.assertEqual("cancelled", result.status)  # 新增代码+GuiAgentAdapterContractTest：确认结果取消；如果没有这一行，adapter 可能继续完成。
        self.assertEqual("turn_cancelled", events[-1]["kind"])  # 新增代码+GuiAgentAdapterContractTest：确认最后事件是 turn_cancelled；如果没有这一行，前端无法进入取消终态。
    # 新增代码+GuiAgentAdapterContractTest：测试函数结束，test_fake_streaming_adapter_propagates_cancellation 到此结束；如果没有这个边界说明，用户不容易看出取消合同范围。

    def test_fake_streaming_adapter_converts_deterministic_exception_to_failed_event(self) -> None:  # 新增代码+GuiAgentAdapterContractTest：测试函数开始，验证 fake adapter 失败语义；如果没有这段，异常可能变成线程崩溃。
        result, events = self._collect_fake_events("__adapter_fail__ 请触发失败")  # 新增代码+GuiAgentAdapterContractTest：运行 deterministic failure prompt；如果没有这一行，失败路径没有输入。
        self.assertEqual("failed", result.status)  # 新增代码+GuiAgentAdapterContractTest：确认结果失败；如果没有这一行，失败可能被误判完成。
        self.assertEqual("adapter_failed", result.error_code)  # 新增代码+GuiAgentAdapterContractTest：确认稳定错误码；如果没有这一行，前端无法机器处理。
        self.assertEqual("turn_failed", events[-1]["kind"])  # 新增代码+GuiAgentAdapterContractTest：确认发出 turn_failed；如果没有这一行，GUI 状态机不会进入失败态。
    # 新增代码+GuiAgentAdapterContractTest：测试函数结束，test_fake_streaming_adapter_converts_deterministic_exception_to_failed_event 到此结束；如果没有这个边界说明，用户不容易看出失败合同范围。

    def test_fake_streaming_adapter_replays_golden_trace(self) -> None:  # 新增代码+GuiAgentAdapterContractTest：测试函数开始，验证 fake adapter 可回放 golden trace；如果没有这段，前端和 bridge 测试无法共享固定事件语料。
        result, events = self._collect_fake_events("请分析当前项目是什么项目，并列出模块组成。", trace_id="GT-001")  # 新增代码+GuiAgentAdapterContractTest：请求回放 GT-001；如果没有这一行，replay 路径没有输入。
        self.assertEqual("completed", result.status)  # 新增代码+GuiAgentAdapterContractTest：确认 golden trace 回放完成；如果没有这一行，fixture 回放可能停在中间。
        self.assertEqual(["turn_started", "message_delta", "message_completed"], [event["kind"] for event in events])  # 新增代码+GuiAgentAdapterContractTest：确认回放事件顺序；如果没有这一行，fixture 可能被乱序使用。
    # 新增代码+GuiAgentAdapterContractTest：测试函数结束，test_fake_streaming_adapter_replays_golden_trace 到此结束；如果没有这个边界说明，用户不容易看出 golden replay 合同范围。

    def test_default_harness_adapter_is_feature_flagged_unavailable(self) -> None:  # 新增代码+GuiAgentAdapterContractTest：测试函数开始，验证真实 harness adapter 仍未接入；如果没有这段，V2-Core 可能意外导入真实模型运行时。
        from learning_agent.app.gui_agent_adapter import DefaultHarnessGuiAgentAdapter, GuiAgentRunRequest  # 新增代码+GuiAgentAdapterContractTest：导入真实 adapter shell 和请求对象；如果没有这一行，测试没有被测对象。

        events: list[dict[str, object]] = []  # 新增代码+GuiAgentAdapterContractTest：保存真实 adapter shell 事件；如果没有这一行，无法断言失败事件。
        request = GuiAgentRunRequest(session_id="session_a", turn_id="turn_a", run_id="run_a", prompt="真实 harness 模式")  # 新增代码+GuiAgentAdapterContractTest：构造真实 adapter 请求；如果没有这一行，adapter 没有身份字段。
        result = DefaultHarnessGuiAgentAdapter(enabled=False).run(request, events.append, lambda: False)  # 新增代码+GuiAgentAdapterContractTest：运行禁用状态的真实 adapter shell；如果没有这一行，无法验证 feature flag 边界。
        self.assertEqual("failed", result.status)  # 新增代码+GuiAgentAdapterContractTest：确认未启用时失败；如果没有这一行，真实 adapter 可能假成功。
        self.assertEqual("adapter_unavailable", result.error_code)  # 新增代码+GuiAgentAdapterContractTest：确认稳定 unavailable 错误码；如果没有这一行，前端无法给出正确提示。
        self.assertEqual("turn_failed", events[-1]["kind"])  # 新增代码+GuiAgentAdapterContractTest：确认发出 turn_failed；如果没有这一行，GUI 不知道真实 adapter 被禁用。
    # 新增代码+GuiAgentAdapterContractTest：测试函数结束，test_default_harness_adapter_is_feature_flagged_unavailable 到此结束；如果没有这个边界说明，用户不容易看出真实 adapter 边界。

    def test_gui_run_manager_uses_fake_adapter_by_default(self) -> None:  # 新增代码+GuiAgentAdapterContractTest：测试函数开始，验证 bridge run manager 默认进入 fake adapter；如果没有这段，bridge 可能仍只返回同步 V1 answer_runner。
        from learning_agent.app.gui_bridge import GuiRunManager  # 新增代码+GuiAgentAdapterContractTest：导入 run manager；如果没有这一行，测试无法验证 bridge 接线。

        with tempfile.TemporaryDirectory() as directory:  # 新增代码+GuiAgentAdapterContractTest：创建临时 workspace；如果没有这一行，事件会写到真实 memory。
            manager = GuiRunManager(Path(directory))  # 新增代码+GuiAgentAdapterContractTest：创建默认 manager；如果没有这一行，测试没有 bridge 对象。
            response = manager.start_message("default", "请分析当前项目")  # 新增代码+GuiAgentAdapterContractTest：提交 GUI prompt；如果没有这一行，fake adapter 不会运行。
            turn_id = str(response["turn_id"])  # 新增代码+GuiAgentAdapterContractTest：保存 turn id；如果没有这一行，事件匹配没有目标。
            deadline = time.time() + 3.0  # 新增代码+GuiAgentAdapterContractTest：设置异步等待截止时间；如果没有这一行，失败时可能无限等待。
            event_types: list[str] = []  # 新增代码+GuiAgentAdapterContractTest：保存观察到的事件类型；如果没有这一行，无法断言 message_delta。
            while time.time() < deadline:  # 新增代码+GuiAgentAdapterContractTest：轮询等待后台 worker；如果没有这一行，测试会抢在事件写入前失败。
                event_types = [event.event_type for event in manager.event_store.list_events(limit=50) if event.turn_id == turn_id]  # 新增代码+GuiAgentAdapterContractTest：读取当前 turn 事件；如果没有这一行，无法观察 fake adapter 输出。
                if "message_delta" in event_types and "gui_turn_completed" in event_types:  # 新增代码+GuiAgentAdapterContractTest：等待 V2 delta 和 V1 兼容完成事件都出现；如果没有这一行，测试无法证明双轨事件。
                    break  # 新增代码+GuiAgentAdapterContractTest：满足条件后停止等待；如果没有这一行，测试会浪费时间。
                time.sleep(0.03)  # 新增代码+GuiAgentAdapterContractTest：短暂等待后台线程；如果没有这一行，循环会空转占 CPU。
        self.assertIn("message_delta", event_types)  # 新增代码+GuiAgentAdapterContractTest：确认默认路径发出 fake streaming delta；如果没有这一行，V2-Core 不具备流式基线。
        self.assertIn("gui_turn_completed", event_types)  # 新增代码+GuiAgentAdapterContractTest：确认仍保留 V1 完成事件；如果没有这一行，旧 GUI 生命周期测试会被破坏。
    # 新增代码+GuiAgentAdapterContractTest：测试函数结束，test_gui_run_manager_uses_fake_adapter_by_default 到此结束；如果没有这个边界说明，用户不容易看出 bridge 接线合同范围。
# 新增代码+GuiAgentAdapterContractTest：测试类段结束，GuiAgentAdapterContractTest 到此结束；如果没有这个边界说明，用户不容易看出本文件只测 adapter 边界。


if __name__ == "__main__":  # 新增代码+GuiAgentAdapterContractTest：允许直接运行本测试文件；如果没有这一行，手动排查时不会启动 unittest。
    unittest.main()  # 新增代码+GuiAgentAdapterContractTest：启动 unittest 主程序；如果没有这一行，直接运行文件不会执行测试。
