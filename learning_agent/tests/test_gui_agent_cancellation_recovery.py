import tempfile  # 新增代码+RealHarnessCancelRecoveryTest：创建隔离 workspace；如果没有这一行，恢复测试会污染真实项目。
import time  # 新增代码+RealHarnessCancelRecoveryTest：让慢流式假模型产生可取消窗口；如果没有这一行，取消测试可能瞬间完成。
import unittest  # 新增代码+RealHarnessCancelRecoveryTest：使用标准库 unittest 编写 Phase 5 测试；如果没有这一行，测试不会被收集。
from pathlib import Path  # 新增代码+RealHarnessCancelRecoveryTest：处理临时目录和文件路径；如果没有这一行，workspace 传参不稳定。
from typing import Any  # 新增代码+RealHarnessCancelRecoveryTest：标注假模型 chat/stream 入参；如果没有这一行，类型边界不清楚。

from learning_agent.app.gui_agent_adapter import DefaultHarnessGuiAgentAdapter, GuiAgentRunRequest  # 新增代码+RealHarnessCancelRecoveryTest：导入真实 adapter shell 和请求对象；如果没有这一行，取消测试无法走真实主循环。
from learning_agent.app.gui_bridge import GuiMessage, GuiRunManager, GuiTurn  # 新增代码+RealHarnessCancelRecoveryTest：导入 GUI 状态对象；如果没有这一行，恢复测试无法构造落盘 running turn。
from learning_agent.core.messages import ModelMessage  # 新增代码+RealHarnessCancelRecoveryTest：构造流式完成消息；如果没有这一行，慢模型无法结束。
from learning_agent.models.base import ModelStreamEvent  # 新增代码+RealHarnessCancelRecoveryTest：构造模型流式事件；如果没有这一行，慢模型无法模拟 text_delta。


class SlowStreamingModel:  # 新增代码+RealHarnessCancelRecoveryTest：类段开始，模拟会产生多个 delta 的模型；如果没有这个类，取消测试只能覆盖瞬时 chat。
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelMessage:  # 新增代码+RealHarnessCancelRecoveryTest：提供兼容 ChatModel 接口；如果没有这段，协议检查和读者会困惑模型能力。
        del messages, tools  # 新增代码+RealHarnessCancelRecoveryTest：明确普通 chat 不会被使用；如果没有这一行，参数看起来像遗漏。
        return ModelMessage(text="SHOULD_NOT_USE_CHAT")  # 新增代码+RealHarnessCancelRecoveryTest：兜底返回文本；如果没有这一行，意外走 chat 时会抛异常而不是给出证据。
    # 新增代码+RealHarnessCancelRecoveryTest：函数段结束，SlowStreamingModel.chat 到此结束；如果没有这个边界说明，用户不容易看出 chat 是兜底。

    def stream_chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]):  # 新增代码+RealHarnessCancelRecoveryTest：函数段开始，提供真实流式事件；如果没有这段，adapter 不能在 delta 间检查取消。
        del messages, tools  # 新增代码+RealHarnessCancelRecoveryTest：假模型不读取上下文和工具表；如果没有这一行，读者会以为这里要真实推理。
        yield ModelStreamEvent(event_type="text_delta", text_delta="part-1")  # 新增代码+RealHarnessCancelRecoveryTest：发出第一段可见文本；如果没有这一行，取消触发器没有事件依据。
        time.sleep(0.05)  # 新增代码+RealHarnessCancelRecoveryTest：制造取消窗口；如果没有这一行，主线程可能来不及观察首个 delta。
        yield ModelStreamEvent(event_type="text_delta", text_delta="part-2")  # 新增代码+RealHarnessCancelRecoveryTest：发出第二段文本让 adapter 检测取消；如果没有这一行，stop_event 很难进入 core。
        yield ModelStreamEvent(event_type="model_message_completed", model_message=ModelMessage(text="SHOULD_BE_CANCELLED"))  # 新增代码+RealHarnessCancelRecoveryTest：给 core 一个完成事件；如果没有这一行，流式模型会被合成但取消路径不完整。
    # 新增代码+RealHarnessCancelRecoveryTest：函数段结束，SlowStreamingModel.stream_chat 到此结束；如果没有这个边界说明，用户不容易看出慢流式范围。
# 新增代码+RealHarnessCancelRecoveryTest：类段结束，SlowStreamingModel 到此结束；如果没有这个边界说明，用户不容易看出它只服务取消测试。


class GuiAgentCancellationRecoveryTest(unittest.TestCase):  # 新增代码+RealHarnessCancelRecoveryTest：测试类段开始，覆盖取消和重启恢复；如果没有这个类，Phase 5 没有自动验收。
    def test_real_harness_adapter_returns_cancelled_after_streaming_delta(self) -> None:  # 新增代码+RealHarnessCancelRecoveryTest：测试函数开始，验证真实 adapter 流式取消；如果没有这段，取消可能只在假路径有效。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessCancelRecoveryTest：创建隔离 workspace；如果没有这一行，agent 会写真实 memory。
            request = GuiAgentRunRequest(session_id="session_cancel", turn_id="turn_cancel", run_id="run_cancel", prompt="请流式输出后取消", workspace=directory, provider_id="test-fake")  # 新增代码+RealHarnessCancelRecoveryTest：构造真实 adapter 请求；如果没有这一行，adapter 没有运行身份。
            events: list[dict[str, object]] = []  # 新增代码+RealHarnessCancelRecoveryTest：保存 GUI 事件；如果没有这一行，取消条件无法观察 delta。
            adapter = DefaultHarnessGuiAgentAdapter(enabled=True, model_factory=lambda _request: SlowStreamingModel(), max_turns=2)  # 新增代码+RealHarnessCancelRecoveryTest：启用真实 adapter 并注入慢流式模型；如果没有这一行，测试无法稳定触发取消。
            result = adapter.run(request, events.append, lambda: any(event.get("kind") == "message_delta" for event in events))  # 新增代码+RealHarnessCancelRecoveryTest：首个 delta 出现后报告取消；如果没有这一行，adapter 会正常完成。
        event_kinds = [str(event.get("kind", "")) for event in events]  # 新增代码+RealHarnessCancelRecoveryTest：提取事件类型；如果没有这一行，断言会难读。
        self.assertEqual("cancelled", result.status)  # 新增代码+RealHarnessCancelRecoveryTest：确认 adapter 终态为 cancelled；如果没有这一行，取消可能被误当完成。
        self.assertIn("turn_cancelled", event_kinds)  # 新增代码+RealHarnessCancelRecoveryTest：确认 GUI 事件流有取消终态；如果没有这一行，前端会停在 running。
        self.assertIn("message_delta", event_kinds)  # 新增代码+RealHarnessCancelRecoveryTest：确认取消前保留可见输出；如果没有这一行，用户看不到已生成内容。
    # 新增代码+RealHarnessCancelRecoveryTest：测试函数结束，test_real_harness_adapter_returns_cancelled_after_streaming_delta 到此结束；如果没有这个边界说明，用户不容易看出取消验收范围。

    def test_gui_run_manager_reconciles_running_turns_after_restart(self) -> None:  # 新增代码+RealHarnessCancelRecoveryTest：测试函数开始，验证重启后清理 running turn；如果没有这段，旧运行态会永久悬挂。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessCancelRecoveryTest：创建隔离 workspace；如果没有这一行，state.json 会污染真实项目。
            first_manager = GuiRunManager(Path(directory))  # 新增代码+RealHarnessCancelRecoveryTest：创建首次 manager；如果没有这一行，无法写入旧状态。
            turn = GuiTurn(turn_id="turn_orphan", run_id="run_orphan", session_id="session_orphan", prompt="orphan", status="running")  # 新增代码+RealHarnessCancelRecoveryTest：构造模拟崩溃前 running turn；如果没有这一行，恢复逻辑没有目标。
            session = first_manager._session("session_orphan")  # 新增代码+RealHarnessCancelRecoveryTest：创建关联会话；如果没有这一行，消息状态无法恢复。
            session.messages.append(GuiMessage(id="msg_orphan", role="assistant", text="", turn_id="turn_orphan", status="running"))  # 新增代码+RealHarnessCancelRecoveryTest：添加运行中助手消息；如果没有这一行，恢复无法同步消息。
            session.last_turn_id = turn.turn_id  # 新增代码+RealHarnessCancelRecoveryTest：记录最近 turn；如果没有这一行，resume 不知道最新轮次。
            first_manager.turns[turn.turn_id] = turn  # 新增代码+RealHarnessCancelRecoveryTest：保存 orphan turn；如果没有这一行，state 里没有运行态。
            first_manager.active_turn_id = turn.turn_id  # 新增代码+RealHarnessCancelRecoveryTest：模拟崩溃前 active turn；如果没有这一行，恢复 active 清理没有证据。
            first_manager._save_state()  # 新增代码+RealHarnessCancelRecoveryTest：把 running 状态落盘；如果没有这一行，第二个 manager 读不到旧状态。
            second_manager = GuiRunManager(Path(directory))  # 新增代码+RealHarnessCancelRecoveryTest：模拟 GUI bridge 重启；如果没有这一行，恢复逻辑不会执行。
        recovered_turn = second_manager.turns["turn_orphan"]  # 新增代码+RealHarnessCancelRecoveryTest：读取恢复后的 turn；如果没有这一行，后续断言没有对象。
        recovered_message = second_manager.sessions["session_orphan"].messages[0]  # 新增代码+RealHarnessCancelRecoveryTest：读取恢复后的助手消息；如果没有这一行，无法验证消息同步。
        self.assertIsNone(second_manager.active_turn_id)  # 新增代码+RealHarnessCancelRecoveryTest：确认重启后 active 锁释放；如果没有这一行，新 prompt 可能永久 busy。
        self.assertEqual("failed", recovered_turn.status)  # 新增代码+RealHarnessCancelRecoveryTest：确认 orphan running 变成 failed；如果没有这一行，旧任务会一直运行中。
        self.assertIn("已中断", recovered_turn.error)  # 新增代码+RealHarnessCancelRecoveryTest：确认失败原因可读；如果没有这一行，用户不知道发生了重启恢复。
        self.assertEqual("failed", recovered_message.status)  # 新增代码+RealHarnessCancelRecoveryTest：确认助手消息状态同步；如果没有这一行，消息卡仍会显示 running。
        self.assertIn("已中断", recovered_message.text)  # 新增代码+RealHarnessCancelRecoveryTest：确认助手消息有恢复说明；如果没有这一行，用户只能看到空白失败。
    # 新增代码+RealHarnessCancelRecoveryTest：测试函数结束，test_gui_run_manager_reconciles_running_turns_after_restart 到此结束；如果没有这个边界说明，用户不容易看出恢复验收范围。
# 新增代码+RealHarnessCancelRecoveryTest：测试类段结束，GuiAgentCancellationRecoveryTest 到此结束；如果没有这个边界说明，用户不容易看出本文件覆盖 Phase 5。


if __name__ == "__main__":  # 新增代码+RealHarnessCancelRecoveryTest：允许直接运行本测试文件；如果没有这一行，手动排查时不会启动 unittest。
    unittest.main()  # 新增代码+RealHarnessCancelRecoveryTest：执行测试主程序；如果没有这一行，直接运行文件不会跑测试。
