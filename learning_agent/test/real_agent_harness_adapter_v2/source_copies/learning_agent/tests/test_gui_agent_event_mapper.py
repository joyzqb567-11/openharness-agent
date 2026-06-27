import json  # 新增代码+RealHarnessTraceReplay：读取 JSONL 轨迹样本；如果没有这一行，fixture 无法被解析成 AgentEvent。
import tempfile  # 新增代码+RealHarnessTraceReplay：创建临时 workspace 用于路径脱敏测试；如果没有这一行，测试会依赖真实项目路径。
import unittest  # 新增代码+RealHarnessTraceReplay：使用标准库 unittest 组织合同测试；如果没有这一行，测试类无法运行。
from pathlib import Path  # 新增代码+RealHarnessTraceReplay：定位 fixture 目录和临时文件路径；如果没有这一行，Windows 路径拼接更容易出错。

from learning_agent.app.gui_agent_event_mapper import agent_event_to_gui_events, redact_gui_agent_payload  # 新增代码+RealHarnessTraceReplay：导入被测映射器和脱敏器；如果没有这一行，测试没有目标函数。
from learning_agent.core.events import AgentEvent  # 新增代码+RealHarnessTraceReplay：导入 core 事件类型；如果没有这一行，fixture 只能当普通 dict 测。


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "gui_agent_traces"  # 新增代码+RealHarnessTraceReplay：集中定位 JSONL fixture；如果没有这一行，每个测试都要重复拼路径。


def _load_trace(name: str) -> list[AgentEvent]:  # 新增代码+RealHarnessTraceReplay：函数段开始，读取单个 JSONL trace；如果没有这段，测试会重复解析逻辑。
    path = FIXTURE_DIR / name  # 新增代码+RealHarnessTraceReplay：拼出样本文件路径；如果没有这一行，调用方只能传完整路径。
    events: list[AgentEvent] = []  # 新增代码+RealHarnessTraceReplay：保存解析后的 AgentEvent；如果没有这一行，循环没有结果容器。
    for line in path.read_text(encoding="utf-8").splitlines():  # 新增代码+RealHarnessTraceReplay：逐行读取 JSONL；如果没有这一行，多事件 trace 无法回放。
        if not line.strip():  # 新增代码+RealHarnessTraceReplay：跳过空行；如果没有这一行，空白会触发 JSON 解析错误。
            continue  # 新增代码+RealHarnessTraceReplay：空行继续下一行；如果没有这一行，后续解析会失败。
        events.append(AgentEvent(**json.loads(line)))  # 新增代码+RealHarnessTraceReplay：把 JSON 行转成 AgentEvent；如果没有这一行，映射器拿不到标准事件对象。
    return events  # 新增代码+RealHarnessTraceReplay：返回完整事件列表；如果没有这一行，测试无法断言映射结果。
# 新增代码+RealHarnessTraceReplay：函数段结束，_load_trace 到此结束；如果没有这个边界说明，用户不容易看出它只负责读取样本。


def _map_trace(name: str, user_cancelled: bool = False, workspace: str = "") -> list[dict[str, object]]:  # 新增代码+RealHarnessTraceReplay：函数段开始，把 JSONL trace 映射成 GUI events；如果没有这段，每个测试都要重复 sequence 计算。
    gui_events: list[dict[str, object]] = []  # 新增代码+RealHarnessTraceReplay：保存所有 GUI 事件；如果没有这一行，映射结果没有容器。
    next_sequence = 1  # 新增代码+RealHarnessTraceReplay：初始化 GUI 事件序号；如果没有这一行，测试无法确认 sequence 连续。
    for agent_event in _load_trace(name):  # 新增代码+RealHarnessTraceReplay：逐个回放 core 事件；如果没有这一行，只会测试第一条事件。
        mapped = agent_event_to_gui_events(agent_event, run_id="gui_run", turn_id="gui_turn", sequence_start=next_sequence, workspace=workspace, user_cancelled=user_cancelled)  # 新增代码+RealHarnessTraceReplay：调用真实映射器；如果没有这一行，测试不会覆盖被测逻辑。
        gui_events.extend(mapped)  # 新增代码+RealHarnessTraceReplay：累加映射结果；如果没有这一行，多事件输出会丢失。
        next_sequence += len(mapped)  # 新增代码+RealHarnessTraceReplay：推进下一批 GUI sequence；如果没有这一行，后续事件序号会重复。
    return gui_events  # 新增代码+RealHarnessTraceReplay：返回完整 GUI 事件列表；如果没有这一行，测试无法断言 kind。
# 新增代码+RealHarnessTraceReplay：函数段结束，_map_trace 到此结束；如果没有这个边界说明，用户不容易看出它只负责回放映射。


class GuiAgentEventMapperTest(unittest.TestCase):  # 新增代码+RealHarnessTraceReplay：测试类段开始，覆盖 AgentEvent 到 GUI event 的轨迹合同；如果没有这个类，Phase 2 没有自动验收。
    def test_no_tool_success_trace_maps_to_message_completed_once(self) -> None:  # 新增代码+RealHarnessTraceReplay：测试函数开始，验证无工具成功 trace；如果没有这段，最小 agent 回答路径可能回归。
        gui_events = _map_trace("no_tool_success.jsonl")  # 新增代码+RealHarnessTraceReplay：回放成功样本；如果没有这一行，测试没有输入。
        kinds = [str(event.get("kind", "")) for event in gui_events]  # 新增代码+RealHarnessTraceReplay：提取事件类型；如果没有这一行，断言会难读。
        self.assertEqual(1, kinds.count("model_call_started"))  # 新增代码+RealHarnessTraceReplay：确认模型开始事件存在且唯一；如果没有这一行，状态条可能重复。
        self.assertEqual(2, kinds.count("message_delta"))  # 新增代码+RealHarnessTraceReplay：确认两个增量事件都被保留；如果没有这一行，流式文本可能丢片。
        self.assertEqual(1, kinds.count("message_completed"))  # 新增代码+RealHarnessTraceReplay：确认最终完成事件唯一；如果没有这一行，GUI 可能重复完成。
        self.assertEqual("Hello world", gui_events[-1]["payload"]["final_text"])  # 新增代码+RealHarnessTraceReplay：确认最终文本进入 payload；如果没有这一行，助手消息会空白。
    # 新增代码+RealHarnessTraceReplay：测试函数结束，test_no_tool_success_trace_maps_to_message_completed_once 到此结束；如果没有这个边界说明，用户不容易看出成功路径范围。

    def test_model_failure_trace_maps_to_turn_failed_and_redacts_secret(self) -> None:  # 新增代码+RealHarnessTraceReplay：测试函数开始，验证模型失败和脱敏；如果没有这段，失败可能泄露 token。
        gui_events = _map_trace("model_failure.jsonl")  # 新增代码+RealHarnessTraceReplay：回放失败样本；如果没有这一行，测试没有失败输入。
        failed_event = gui_events[-1]  # 新增代码+RealHarnessTraceReplay：读取最后的失败事件；如果没有这一行，后续断言不清楚。
        self.assertEqual("turn_failed", failed_event["kind"])  # 新增代码+RealHarnessTraceReplay：确认失败映射为 GUI 终态；如果没有这一行，前端可能悬挂。
        self.assertEqual("[redacted]", failed_event["payload"]["access_token"])  # 新增代码+RealHarnessTraceReplay：确认 token 被遮蔽；如果没有这一行，真实 provider token 可能泄露。
    # 新增代码+RealHarnessTraceReplay：测试函数结束，test_model_failure_trace_maps_to_turn_failed_and_redacts_secret 到此结束；如果没有这个边界说明，用户不容易看出失败路径范围。

    def test_cancel_mid_stream_trace_maps_to_turn_cancelled(self) -> None:  # 新增代码+RealHarnessTraceReplay：测试函数开始，验证中途取消 trace；如果没有这段，取消可能被误显示为完成。
        gui_events = _map_trace("cancel_mid_stream.jsonl", user_cancelled=True)  # 新增代码+RealHarnessTraceReplay：以用户取消状态回放样本；如果没有这一行，mapper 不会走取消分支。
        self.assertEqual("turn_cancelled", gui_events[-1]["kind"])  # 新增代码+RealHarnessTraceReplay：确认终态是取消；如果没有这一行，取消按钮语义会错误。
        self.assertEqual("partial", gui_events[-1]["payload"]["final_text"])  # 新增代码+RealHarnessTraceReplay：确认 partial 文本保留；如果没有这一行，用户看不到取消前输出。
    # 新增代码+RealHarnessTraceReplay：测试函数结束，test_cancel_mid_stream_trace_maps_to_turn_cancelled 到此结束；如果没有这个边界说明，用户不容易看出取消路径范围。

    def test_permission_denied_trace_keeps_tool_and_failure_events(self) -> None:  # 新增代码+RealHarnessTraceReplay：测试函数开始，验证权限拒绝 trace；如果没有这段，工具拒绝可能不可见。
        gui_events = _map_trace("permission_denied.jsonl")  # 新增代码+RealHarnessTraceReplay：回放权限拒绝样本；如果没有这一行，测试没有工具拒绝输入。
        kinds = [str(event.get("kind", "")) for event in gui_events]  # 新增代码+RealHarnessTraceReplay：提取事件类型；如果没有这一行，断言会重复遍历。
        self.assertIn("tool_started", kinds)  # 新增代码+RealHarnessTraceReplay：确认工具开始可见；如果没有这一行，TracePanel 没有工具起点。
        self.assertIn("tool_finished", kinds)  # 新增代码+RealHarnessTraceReplay：确认工具结果可见；如果没有这一行，TracePanel 会停在 running。
        self.assertIn("turn_failed", kinds)  # 新增代码+RealHarnessTraceReplay：确认拒绝后进入失败终态；如果没有这一行，GUI 可能继续等待。
    # 新增代码+RealHarnessTraceReplay：测试函数结束，test_permission_denied_trace_keeps_tool_and_failure_events 到此结束；如果没有这个边界说明，用户不容易看出拒绝路径范围。

    def test_read_only_tool_trace_maps_to_tool_finished_and_completed(self) -> None:  # 新增代码+RealHarnessTraceReplay：测试函数开始，验证只读工具成功 trace；如果没有这段，Phase 3 工具卡片缺自动回归。
        gui_events = _map_trace("read_only_tool_success.jsonl")  # 新增代码+RealHarnessTraceReplay：回放只读工具样本；如果没有这一行，测试没有工具成功输入。
        kinds = [str(event.get("kind", "")) for event in gui_events]  # 新增代码+RealHarnessTraceReplay：提取事件类型；如果没有这一行，断言会难读。
        self.assertEqual("read_file", gui_events[1]["payload"]["tool_name"])  # 新增代码+RealHarnessTraceReplay：确认工具名稳定；如果没有这一行，TracePanel 无法显示真实工具。
        self.assertIn("tool_finished", kinds)  # 新增代码+RealHarnessTraceReplay：确认工具完成事件存在；如果没有这一行，工具卡片不会收束。
        self.assertEqual("message_completed", gui_events[-1]["kind"])  # 新增代码+RealHarnessTraceReplay：确认工具后仍完成回答；如果没有这一行，agent 主循环会停在工具后。
    # 新增代码+RealHarnessTraceReplay：测试函数结束，test_read_only_tool_trace_maps_to_tool_finished_and_completed 到此结束；如果没有这个边界说明，用户不容易看出只读工具范围。

    def test_redaction_caps_long_strings_after_workspace_replacement(self) -> None:  # 新增代码+RealHarnessTraceReplay：测试函数开始，验证长输出截断；如果没有这段，stdout/stderr 可能撑爆 GUI。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessTraceReplay：创建临时 workspace；如果没有这一行，路径脱敏没有真实目录。
            long_text = str(Path(directory).resolve()) + "/" + ("x" * 2000)  # 新增代码+RealHarnessTraceReplay：构造含 workspace 的超长文本；如果没有这一行，截断和脱敏无法一起覆盖。
            payload = redact_gui_agent_payload({"stdout": long_text}, directory)  # 新增代码+RealHarnessTraceReplay：执行脱敏和截断；如果没有这一行，断言没有被测结果。
        self.assertIn("[workspace]", payload["stdout"])  # 新增代码+RealHarnessTraceReplay：确认路径被替换；如果没有这一行，本机路径可能泄露。
        self.assertIn("[truncated]", payload["stdout"])  # 新增代码+RealHarnessTraceReplay：确认长文本被截断；如果没有这一行，工具输出可能无限变长。
        self.assertLessEqual(len(payload["stdout"]), 1020)  # 新增代码+RealHarnessTraceReplay：确认截断后长度受控；如果没有这一行，截断标记可能没有实际限制大小。
    # 新增代码+RealHarnessTraceReplay：测试函数结束，test_redaction_caps_long_strings_after_workspace_replacement 到此结束；如果没有这个边界说明，用户不容易看出长度门禁范围。
# 新增代码+RealHarnessTraceReplay：测试类段结束，GuiAgentEventMapperTest 到此结束；如果没有这个边界说明，用户不容易看出本文件覆盖 Phase 2。


if __name__ == "__main__":  # 新增代码+RealHarnessTraceReplay：允许直接运行本测试文件；如果没有这一行，手动排查时不会启动 unittest。
    unittest.main()  # 新增代码+RealHarnessTraceReplay：执行测试主程序；如果没有这一行，直接运行文件不会跑测试。
