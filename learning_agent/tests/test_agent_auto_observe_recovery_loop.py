"""LearningAgent 主循环自动 observe 恢复测试。"""  # 新增代码+AutoObserveRecovery：说明本文件验证主循环自动补 observe；如果没有这一行，读者不知道测试为何需要假模型和假工具。
from __future__ import annotations  # 新增代码+AutoObserveRecovery：延迟解析类型注解；如果没有这一行，测试里的类型写法更容易受导入顺序影响。

from pathlib import Path  # 新增代码+AutoObserveRecovery：导入 Path 处理临时工作区；如果没有这一行，测试函数无法清楚标注 tmp_path 类型。
from typing import Any  # 新增代码+AutoObserveRecovery：导入 Any 标注事件和工具参数；如果没有这一行，假执行器的宽松结构没有类型边界。

import learning_agent.core.agent as agent_module  # 新增代码+AutoObserveRecovery：导入 agent 模块以便 monkeypatch 工具编排器；如果没有这一行，测试无法拦截真实桌面工具。
from learning_agent.core.actionability_state import DESKTOP_ACTION_REQUIRED_MARKER  # 新增代码+AutoObserveRecovery：导入桌面动作要求 marker；如果没有这一行，假工具输出会手写脆弱字符串。
from learning_agent.core.agent import LearningAgent  # 新增代码+AutoObserveRecovery：导入真实主循环对象；如果没有这一行，测试只能测脱离系统的 helper。
from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+AutoObserveRecovery：导入模型消息和工具调用结构；如果没有这一行，假模型剧本无法表达工具调用。
from learning_agent.models.fake import ToolCallingFakeModel  # 新增代码+AutoObserveRecovery：导入顺序假模型；如果没有这一行，测试会依赖真实模型。


def _observe_before_action_output() -> str:  # 新增代码+AutoObserveRecovery：函数段开始，构造动作前必须 observe 的工具输出；如果没有这段函数，测试会重复脆弱协议文本。
    return "\n".join(  # 新增代码+AutoObserveRecovery：按真实工具输出格式拼接多行协议；如果没有这一行，解析器无法按行识别 marker。
        [  # 新增代码+AutoObserveRecovery：协议行列表开始；如果没有这一行，Python 列表语法不完整。
            DESKTOP_ACTION_REQUIRED_MARKER,  # 新增代码+AutoObserveRecovery：写入桌面动作要求 marker；如果没有这一行，record_tool_result 不会生成 pending。
            "actionability_kind=desktop_observe_before_action",  # 新增代码+AutoObserveRecovery：声明这是动作前观察要求；如果没有这一行，恢复层不会把它当成可自动恢复。
            "next_required_tool=mcp__computer-use__observe",  # 新增代码+AutoObserveRecovery：声明下一步必须 observe；如果没有这一行，恢复层不知道该合成哪个工具。
            "next_required_action=get_window_state",  # 新增代码+AutoObserveRecovery：声明 observe 的具体动作；如果没有这一行，恢复层可能生成错误参数。
            "target_ref=cu-target-test-0001",  # 新增代码+AutoObserveRecovery：保留目标窗口引用；如果没有这一行，多窗口任务会失去绑定。
            "low_level_event_count=0",  # 新增代码+AutoObserveRecovery：证明被拒动作没有触发真实输入；如果没有这一行，安全证据不完整。
        ]  # 新增代码+AutoObserveRecovery：协议行列表结束；如果没有这一行，Python 列表语法不完整。
    )  # 新增代码+AutoObserveRecovery：字符串拼接结束；如果没有这一行，函数不会返回完整文本。
    # 新增代码+AutoObserveRecovery：函数段结束，_observe_before_action_output 到此结束；如果没有这个边界说明，用户不容易看出假工具输出范围。


def _observe_success_output() -> str:  # 新增代码+AutoObserveRecovery：函数段开始，构造 observe 成功输出；如果没有这段函数，测试无法证明 pending 会被 observe 清理。
    return "\n".join(  # 新增代码+AutoObserveRecovery：按工具输出格式拼接多行文本；如果没有这一行，主循环拿不到模型可见观察结果。
        [  # 新增代码+AutoObserveRecovery：输出行列表开始；如果没有这一行，Python 列表语法不完整。
            "observe ok",  # 新增代码+AutoObserveRecovery：表示观察成功；如果没有这一行，工具结果会过于空洞。
            "image_result_count=1",  # 新增代码+AutoObserveRecovery：模拟截图证据计数字段；如果没有这一行，runtime trace 难以识别截图已返回。
            "screenshot_returned_to_model=true",  # 新增代码+AutoObserveRecovery：模拟模型可见截图证据；如果没有这一行，测试不能覆盖证据链意图。
        ]  # 新增代码+AutoObserveRecovery：输出行列表结束；如果没有这一行，Python 列表语法不完整。
    )  # 新增代码+AutoObserveRecovery：字符串拼接结束；如果没有这一行，函数不会返回完整文本。
    # 新增代码+AutoObserveRecovery：函数段结束，_observe_success_output 到此结束；如果没有这个边界说明，用户不容易看出成功输出范围。


def test_agent_auto_runs_observe_after_observe_before_action_required(monkeypatch: Any, tmp_path: Path) -> None:  # 新增代码+AutoObserveRecovery：函数段开始，验证主循环会自动补 observe；如果没有这段测试，模型重试 open/key 的问题没有端到端保护。
    first_tool_call = ToolCall(name="mcp__computer-use__key", arguments={"key": "enter", "target_ref": "cu-target-test-0001"})  # 新增代码+AutoObserveRecovery：准备一个会被动作门禁拒绝的 Computer Use 动作；如果没有这一行，主循环不会进入 observe-required 分支。
    fake_model = ToolCallingFakeModel([ModelMessage(tool_calls=[first_tool_call]), ModelMessage(text="AUTO_OBSERVE_DONE")])  # 新增代码+AutoObserveRecovery：安排模型先请求动作再最终回答；如果没有这一行，测试会依赖真实模型判断。
    agent = LearningAgent(model=fake_model, workspace=tmp_path, ask_permission=lambda _reason: True, debug_enabled=False)  # 新增代码+AutoObserveRecovery：创建真实 agent 但关闭 debug；如果没有这一行，测试无法跑真实 run_events。
    executed_tool_names: list[str] = []  # 新增代码+AutoObserveRecovery：记录真实执行器收到的工具名；如果没有这一行，测试无法证明 observe 是运行时补的。
    cleanup_calls: list[str] = []  # 新增代码+AutoObserveRecovery：记录 cleanup 调用；如果没有这一行，测试无法避免真实 cleanup 触碰桌面状态。

    def fake_execute_tool_calls(_agent: LearningAgent, tool_calls: list[ToolCall]) -> list[str]:  # 新增代码+AutoObserveRecovery：函数段开始，用假执行器替代真实桌面工具；如果没有这段函数，测试会真的调用 Computer Use。
        outputs: list[str] = []  # 新增代码+AutoObserveRecovery：准备按顺序返回工具输出；如果没有这一行，主循环拿不到结果列表。
        for tool_call in tool_calls:  # 新增代码+AutoObserveRecovery：遍历本批工具调用；如果没有这一行，假执行器不能处理动作和自动 observe 两种工具。
            executed_tool_names.append(tool_call.name)  # 新增代码+AutoObserveRecovery：记录执行顺序；如果没有这一行，测试无法证明自动 observe 发生在同一运行里。
            if tool_call.name == "mcp__computer-use__key":  # 新增代码+AutoObserveRecovery：识别第一次模型请求的动作工具；如果没有这一行，假输出不能触发 pending。
                outputs.append(_observe_before_action_output())  # 新增代码+AutoObserveRecovery：返回 observe-required marker；如果没有这一行，主循环不会进入自动恢复。
                continue  # 新增代码+AutoObserveRecovery：当前工具已处理，继续下一个；如果没有这一行，后面分支可能追加额外输出。
            if tool_call.name == "mcp__computer-use__observe":  # 新增代码+AutoObserveRecovery：识别运行时应该合成的 observe 工具；如果没有这一行，自动恢复无法返回成功证据。
                assert tool_call.arguments["action"] == "get_window_state"  # 新增代码+AutoObserveRecovery：确认合成 observe 参数正确；如果没有这一行，主循环可能补了错误动作。
                assert tool_call.arguments["target_ref"] == "cu-target-test-0001"  # 新增代码+AutoObserveRecovery：确认合成 observe 保留目标窗口；如果没有这一行，多窗口安全边界会断。
                outputs.append(_observe_success_output())  # 新增代码+AutoObserveRecovery：返回 observe 成功输出；如果没有这一行，pending 无法被清理。
                continue  # 新增代码+AutoObserveRecovery：当前工具已处理，继续下一个；如果没有这一行，未知工具兜底会污染输出。
            outputs.append(f"unexpected tool {tool_call.name}")  # 新增代码+AutoObserveRecovery：未知工具返回可读文本；如果没有这一行，测试排错会只看到空输出。
        return outputs  # 新增代码+AutoObserveRecovery：返回按顺序排列的工具结果；如果没有这一行，主循环无法回填结果。
        # 新增代码+AutoObserveRecovery：函数段结束，fake_execute_tool_calls 到此结束；如果没有这个边界说明，用户不容易看出假执行器范围。

    def fake_cleanup(_computer_use_used: bool, reason: str) -> dict[str, object]:  # 新增代码+AutoObserveRecovery：函数段开始，替代真实 cleanup；如果没有这段函数，单元测试可能触碰真实 Computer Use 会话。
        cleanup_calls.append(reason)  # 新增代码+AutoObserveRecovery：记录 cleanup 原因；如果没有这一行，测试无法确认 finally 仍然执行。
        return {"cleanup_completed": True, "reason": reason}  # 新增代码+AutoObserveRecovery：返回成功 cleanup 报告；如果没有这一行，主循环 observation 可能记录异常。
        # 新增代码+AutoObserveRecovery：函数段结束，fake_cleanup 到此结束；如果没有这个边界说明，用户不容易看出 cleanup 替身范围。

    monkeypatch.setattr(agent_module, "execute_tool_calls_from_orchestrator", fake_execute_tool_calls)  # 新增代码+AutoObserveRecovery：把主循环工具编排器替换成假执行器；如果没有这一行，测试会调用真实工具。
    monkeypatch.setattr(agent, "_run_computer_use_turn_cleanup_if_needed", fake_cleanup)  # 新增代码+AutoObserveRecovery：把 cleanup 替换成记录器；如果没有这一行，测试可能改动真实桌面锁状态。
    events = list(agent.run_events("请使用本机真实画图软件画一条线", max_turns=3))  # 新增代码+AutoObserveRecovery：运行真实主循环；如果没有这一行，测试没有端到端行为。
    event_types = [event.event_type for event in events]  # 新增代码+AutoObserveRecovery：提取事件名列表；如果没有这一行，断言需要重复遍历事件对象。
    assert executed_tool_names == ["mcp__computer-use__key", "mcp__computer-use__observe"]  # 新增代码+AutoObserveRecovery：确认模型只请求 key，observe 由运行时自动补；如果没有这一行，核心 bug 可能复发。
    assert "computer_use_auto_recovery_observe" in event_types  # 新增代码+AutoObserveRecovery：确认自动恢复有可观察事件；如果没有这一行，acceptance 无法审计恢复动作。
    assert any(event.payload.get("text") == "AUTO_OBSERVE_DONE" for event in events if event.event_type == "run_completed")  # 新增代码+AutoObserveRecovery：确认自动 observe 后模型能继续最终回答；如果没有这一行，恢复可能打断主循环。
    assert cleanup_calls  # 新增代码+AutoObserveRecovery：确认 finally cleanup 仍被调用；如果没有这一行，自动恢复可能绕过清理生命周期。
    # 新增代码+AutoObserveRecovery：函数段结束，test_agent_auto_runs_observe_after_observe_before_action_required 到此结束；如果没有这个边界说明，用户不容易看出端到端测试范围。
