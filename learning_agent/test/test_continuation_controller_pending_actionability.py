from learning_agent.core.continuation_controller import decide_after_model_response  # 新增代码+PendingActionabilityNoFinal：导入模型响应后继续/结束决策函数；如果没有这一行，测试无法覆盖最终回答门禁。
from learning_agent.core.task_state import TaskState  # 新增代码+PendingActionabilityNoFinal：导入任务状态对象；如果没有这一行，决策函数缺少用户目标上下文。


class _ModelResponse:  # 新增代码+PendingActionabilityNoFinal：测试用轻量模型响应类段开始；如果没有这段代码，测试需要依赖真实模型响应对象。
    def __init__(self, tool_calls=None):  # 新增代码+PendingActionabilityNoFinal：允许测试指定是否有工具调用；如果没有这一行，无法模拟“无工具直接 Done.”场景。
        self.tool_calls = list(tool_calls or [])  # 新增代码+PendingActionabilityNoFinal：保存工具调用列表；如果没有这一行，decide_after_model_response 无法读取 tool_calls。
        self.text = "Done."  # 新增代码+PendingActionabilityNoFinal：模拟模型短答；如果没有这一行，测试不能说明 Done. 会被 pending 门禁拦住。
    # 新增代码+PendingActionabilityNoFinal：测试响应类段结束；如果没有这个边界说明，用户不容易看出它只服务本测试文件。


def _task_state():  # 新增代码+PendingActionabilityNoFinal：测试任务状态 helper 段开始；如果没有这段代码，每个测试都要重复构造用户目标。
    return TaskState.from_user_input("请使用 Computer Use 完成真实桌面动作。", session_id="test-session", run_id="test-run")  # 新增代码+PendingActionabilityNoFinal：返回最小有效任务状态；如果没有这一行，决策提示无法包含任务摘要。
    # 新增代码+PendingActionabilityNoFinal：测试任务状态 helper 段结束；如果没有这个边界说明，用户不容易看出复用范围。


def test_pending_actionability_blocks_no_tool_final_answer():  # 新增代码+PendingActionabilityNoFinal：测试有 pending 时不能无工具最终回答；如果没有这段测试，Done. 伪完成 bug 可能复发。
    runtime_state = {  # 新增代码+PendingActionabilityNoFinal：准备运行态字典；如果没有这一行，pending 没有存放位置。
        "actionability_pending": {  # 新增代码+PendingActionabilityNoFinal：模拟底层工具返回的 pending 动作；如果没有这一行，决策函数会按自然结束处理。
            "marker": "OPENHARNESS_DESKTOP_ACTION_REQUIRED",  # 新增代码+PendingActionabilityNoFinal：标记这是桌面动作要求；如果没有这一行，提示缺少协议来源。
            "next_required_tool": "observe",  # 新增代码+PendingActionabilityNoFinal：要求模型下一步必须 observe；如果没有这一行，注入提示没有可执行工具。
            "next_required_action": "get_window_state",  # 新增代码+PendingActionabilityNoFinal：要求 observe 使用窗口状态动作；如果没有这一行，模型可能继续盲目键鼠。
            "actionability_kind": "desktop_observe_before_action",  # 新增代码+PendingActionabilityNoFinal：记录 pending 类型；如果没有这一行，审计看不出这是写前观察门禁。
        },  # 新增代码+PendingActionabilityNoFinal：pending 字典结束；如果没有这一行，Python 语法不完整。
    }  # 新增代码+PendingActionabilityNoFinal：运行态字典结束；如果没有这一行，Python 语法不完整。
    decision = decide_after_model_response(_ModelResponse(), _task_state(), runtime_state)  # 新增代码+PendingActionabilityNoFinal：执行无工具响应决策；如果没有这一行，无法验证门禁结果。
    assert decision.continue_loop is True  # 新增代码+PendingActionabilityNoFinal：确认主循环必须继续；如果没有这一行，测试不能防止 Done. 被当最终回答。
    assert decision.reason == "pending_actionability_no_tool_exit_blocked"  # 新增代码+PendingActionabilityNoFinal：确认命中专用原因码；如果没有这一行，失败时无法区分是哪类收束。
    assert decision.injected_message is not None  # 新增代码+PendingActionabilityNoFinal：确认会给模型注入纠偏提示；如果没有这一行，继续循环也可能没有行动指导。
    assert "next_required_tool" in decision.injected_message["content"]  # 新增代码+PendingActionabilityNoFinal：确认提示包含下一步工具字段；如果没有这一行，模型可能不知道该调用 observe。
    assert runtime_state["pending_actionability_no_tool_exit_count"] == 1  # 新增代码+PendingActionabilityNoFinal：确认无工具结束计数写入运行态；如果没有这一行，反复忽略无法审计。
    # 新增代码+PendingActionabilityNoFinal：测试段结束；如果没有这个边界说明，用户不容易看出断言覆盖范围。


def test_no_pending_actionability_allows_natural_no_tool_exit():  # 新增代码+PendingActionabilityNoFinal：测试没有 pending 时保持自然最终回答；如果没有这段测试，修复可能误伤普通聊天。
    decision = decide_after_model_response(_ModelResponse(), _task_state(), {})  # 新增代码+PendingActionabilityNoFinal：用空运行态执行决策；如果没有这一行，无法验证普通路径。
    assert decision.continue_loop is False  # 新增代码+PendingActionabilityNoFinal：确认无 pending 时仍可结束；如果没有这一行，普通任务可能被无限循环。
    assert decision.reason == "natural_no_tool_exit"  # 新增代码+PendingActionabilityNoFinal：确认保留原有原因码；如果没有这一行，兼容性回归不容易发现。
    # 新增代码+PendingActionabilityNoFinal：测试段结束；如果没有这个边界说明，用户不容易看出普通路径没有改变。


def test_tool_call_response_resets_pending_no_tool_exit_count():  # 新增代码+PendingActionabilityNoFinal：测试模型恢复调用工具后清零计数；如果没有这段测试，计数可能在成功恢复后继续误导审计。
    runtime_state = {"pending_actionability_no_tool_exit_count": 3}  # 新增代码+PendingActionabilityNoFinal：模拟此前已经拦截过三次；如果没有这一行，无法验证清零逻辑。
    decision = decide_after_model_response(_ModelResponse(tool_calls=[object()]), _task_state(), runtime_state)  # 新增代码+PendingActionabilityNoFinal：模拟模型重新请求工具；如果没有这一行，无法触发工具调用路径。
    assert decision.continue_loop is True  # 新增代码+PendingActionabilityNoFinal：确认有工具调用时继续执行工具；如果没有这一行，工具请求可能被误当最终回答。
    assert decision.reason == "model_requested_tool_calls"  # 新增代码+PendingActionabilityNoFinal：确认保留工具调用原因码；如果没有这一行，主循环审计会变模糊。
    assert runtime_state["pending_actionability_no_tool_exit_count"] == 0  # 新增代码+PendingActionabilityNoFinal：确认恢复工具调用后清零；如果没有这一行，后续日志会留下错误风险信号。
    # 新增代码+PendingActionabilityNoFinal：测试段结束；如果没有这个边界说明，用户不容易看出恢复路径覆盖范围。
