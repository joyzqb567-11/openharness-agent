"""FreshTarget 旧窗口用户动作阻断的回归测试。"""  # 新增代码+FreshTargetUserAction：说明本文件验证旧窗口拒绝后的收敛行为；如果没有这行代码，读者不知道这些测试为什么存在。
from __future__ import annotations  # 新增代码+FreshTargetUserAction：延迟解析类型注解；如果没有这行代码，未来测试类型写法更容易受导入顺序影响。

from learning_agent.core.actionability_state import DESKTOP_RESOURCE_PREPARATION_OBSERVE_REQUIRED_MARKER, DESKTOP_USER_ACTION_REQUIRED_MARKER, get_last_actionability_block, get_pending_actionability, pending_actionability_argument_mismatch, record_actionability_from_tool_result, should_block_tool_for_user_action_required, user_action_required_message  # 修改代码+ResourcePreparationConvergence：导入资源准备 observe-required marker 和参数门禁；如果没有这一行，测试无法证明 Ctrl+N 后会强制 observe 而不是终止或继续输入。
from learning_agent.core.convergence_controller import assess_before_model, decide_tool_call, record_tool_result  # 新增代码+FreshTargetUserAction：导入收敛控制入口；如果没有这一行，测试无法覆盖模型反复 launch 的真实上层路径。
from learning_agent.core.task_state import TaskState  # 新增代码+FreshTargetUserAction：导入任务状态对象；如果没有这一行，收敛器无法生成和真实 agent 一致的任务摘要。


def _fresh_target_user_action_output(target_app: str = "notepad") -> str:  # 新增代码+FreshTargetUserAction：函数段开始，构造 FreshTarget 旧窗口拒绝的工具输出；如果没有这段函数，两个测试会重复脆弱字符串。
    return "\n".join(  # 新增代码+FreshTargetUserAction：把协议行拼成真实工具文本；如果没有这一行，解析器无法按行读取 marker。
        [  # 新增代码+FreshTargetUserAction：协议行列表开始；如果没有这一行，Python 列表语法不完整。
            "open_application failed：当前是 Computer Use 功能，检测到目标软件已经打开；请先手动关闭该软件，或在提示词中明确授权使用已有窗口后重新开启。",  # 新增代码+FreshTargetUserAction：保留用户可读拒绝说明；如果没有这一行，测试不能验证最终提示语义。
            DESKTOP_USER_ACTION_REQUIRED_MARKER,  # 新增代码+FreshTargetUserAction：写入待实现的稳定 marker；如果没有这一行，actionability_state 不会进入用户动作阻断态。
            "actionability_kind=fresh_target_existing_window_user_action_required",  # 新增代码+FreshTargetUserAction：说明阻断来自旧窗口默认拒绝；如果没有这一行，收敛器无法区分普通失败和用户动作要求。
            f"target_app={target_app}",  # 新增代码+FreshTargetUserAction：保存目标应用名；如果没有这一行，重复 launch 门禁无法确认是不是同一个软件。
            "fresh_target_decision=existing_target_window_requires_user_close_or_authorize",  # 新增代码+FreshTargetUserAction：保存 FreshTarget 决策码；如果没有这一行，最终解释缺少稳定原因。
            "retry_launch_allowed=false",  # 新增代码+FreshTargetUserAction：声明默认不允许继续重试启动；如果没有这一行，模型会继续 open_application 循环。
            "next_required_response=ask_user_to_close_or_authorize",  # 新增代码+FreshTargetUserAction：声明下一步应回答用户；如果没有这一行，模型不知道该停止工具并解释。
            "requires_user_to_close_existing_app=true",  # 新增代码+FreshTargetUserAction：声明用户可以通过关闭旧窗口恢复；如果没有这一行，最终提示不够可操作。
            "allows_explicit_existing_window_authorization=true",  # 新增代码+FreshTargetUserAction：声明用户也可以显式授权已有窗口；如果没有这一行，微信等单实例应用没有恢复路径。
            "existing_target_window_count=1",  # 新增代码+FreshTargetUserAction：保存发现的旧窗口数量；如果没有这一行，验收日志无法证明旧窗口确实存在。
            "low_level_event_count=0",  # 新增代码+FreshTargetUserAction：证明拒绝路径没有触发鼠标键盘事件；如果没有这一行，安全验收无法确认零污染。
        ]  # 新增代码+FreshTargetUserAction：协议行列表结束；如果没有这一行，Python 列表语法不完整。
    )  # 新增代码+FreshTargetUserAction：字符串拼接结束；如果没有这一行，测试 helper 不会返回完整文本。
    # 新增代码+FreshTargetUserAction：函数段结束，_fresh_target_user_action_output 到此结束；如果没有这个边界说明，用户不容易看出 helper 范围。


def _resource_preparation_observe_required_output() -> str:  # 新增代码+ResourcePreparationConvergence：函数段开始，构造 Ctrl+N 后必须 observe 的工具输出；如果没有这段函数，测试会重复脆弱 marker 文本。
    return "\n".join(  # 新增代码+ResourcePreparationConvergence：把协议行拼成真实工具文本；如果没有这一行，解析器无法按行读取 marker。
        [  # 新增代码+ResourcePreparationConvergence：协议行列表开始；如果没有这一行，Python 列表语法不完整。
            DESKTOP_RESOURCE_PREPARATION_OBSERVE_REQUIRED_MARKER,  # 新增代码+ResourcePreparationConvergence：写入待解析的准备观察 marker；如果没有这一行，actionability_state 不会保存 observe pending。
            "actionability_kind=desktop_resource_preparation_observe_required",  # 新增代码+ResourcePreparationConvergence：说明这是资源准备后的观察要求；如果没有这一行，pending 类型不可诊断。
            "block_class=observe_required",  # 新增代码+ResourcePreparationConvergence：保存阻断分类；如果没有这一行，日志无法区分用户动作和观察动作。
            "block_reason=resource_preparation_pending_requires_observe",  # 新增代码+ResourcePreparationConvergence：保存稳定阻断原因；如果没有这一行，模型不知道为什么不能继续输入。
            "next_required_tool=mcp__computer-use__observe",  # 新增代码+ResourcePreparationConvergence：强制下一步调用 observe；如果没有这一行，收敛层不知道该让模型做什么。
            "target_ref=cu-target-test-0001",  # 新增代码+ResourcePreparationConvergence：保存目标窗口 ID；如果没有这一行，多窗口场景的 observe 可能看错目标。
            "low_level_event_count=0",  # 新增代码+ResourcePreparationConvergence：证明本次拒绝没有底层动作；如果没有这一行，真实验收无法确认安全。
        ]  # 新增代码+ResourcePreparationConvergence：协议行列表结束；如果没有这一行，Python 列表语法不完整。
    )  # 新增代码+ResourcePreparationConvergence：字符串拼接结束；如果没有这一行，helper 不会返回完整文本。
    # 新增代码+ResourcePreparationConvergence：函数段结束，_resource_preparation_observe_required_output 到此结束；如果没有这个边界说明，用户不容易看出 helper 范围。


def test_user_action_required_marker_records_terminal_block_not_pending() -> None:  # 新增代码+FreshTargetUserAction：函数段开始，验证旧窗口拒绝会记录终止阻断而不是 pending；如果没有这段测试，模型重试 launch 的 bug 会缺少底层回归保护。
    runtime_state: dict[str, object] = {}  # 新增代码+FreshTargetUserAction：准备空运行态；如果没有这一行，测试没有地方保存 actionability 状态。
    record_actionability_from_tool_result("mcp__computer-use__open_application", _fresh_target_user_action_output(), runtime_state)  # 新增代码+FreshTargetUserAction：模拟工具返回旧窗口拒绝；如果没有这一行，marker 解析路径没有被触发。
    block = get_last_actionability_block(runtime_state)  # 新增代码+FreshTargetUserAction：读取最近阻断；如果没有这一行，测试无法判断 marker 是否被保存成终止态。
    assert get_pending_actionability(runtime_state) == {}  # 新增代码+FreshTargetUserAction：确认没有 pending 下一步工具；如果没有这一行，旧窗口拒绝仍可能诱导继续调用工具。
    assert block["marker"] == DESKTOP_USER_ACTION_REQUIRED_MARKER  # 新增代码+FreshTargetUserAction：确认阻断 marker 正确；如果没有这一行，普通失败可能冒充用户动作要求。
    assert block["block_class"] == "user_action_required"  # 新增代码+FreshTargetUserAction：确认阻断分类是用户动作要求；如果没有这一行，收敛器无法决定最终回答用户。
    assert block["target_app"] == "notepad"  # 新增代码+FreshTargetUserAction：确认目标应用被保存；如果没有这一行，通用重复启动门禁无法按应用匹配。
    assert block["retry_launch_allowed"] == "false"  # 新增代码+FreshTargetUserAction：确认默认不允许继续启动；如果没有这一行，重复 open_application 会继续发生。
    reason = should_block_tool_for_user_action_required("mcp__computer-use__open_application", {"app_name": "notepad"}, block)  # 新增代码+FreshTargetUserAction：模拟模型再次启动同一应用；如果没有这一行，测试不能覆盖截图里的重试行为。
    assert "请先手动关闭" in reason  # 新增代码+FreshTargetUserAction：确认阻断原因会要求用户关闭旧窗口；如果没有这一行，模型可能只看到技术错误。
    assert "明确授权" in user_action_required_message(block)  # 新增代码+FreshTargetUserAction：确认最终提示包含授权恢复路径；如果没有这一行，单实例应用会被永久卡住。
    # 新增代码+FreshTargetUserAction：函数段结束，test_user_action_required_marker_records_terminal_block_not_pending 到此结束；如果没有这个边界说明，用户不容易看出底层状态测试范围。


def test_resource_preparation_observe_required_marker_records_pending_observe() -> None:  # 新增代码+ResourcePreparationConvergence：函数段开始，验证 Ctrl+N 后的 observe-required marker 会保存成 pending；如果没有这段测试，模型可能继续输入而不是观察确认。
    runtime_state: dict[str, object] = {}  # 新增代码+ResourcePreparationConvergence：准备空运行态；如果没有这一行，测试没有地方保存 pending 状态。
    record_actionability_from_tool_result("mcp__computer-use__type", _resource_preparation_observe_required_output(), runtime_state)  # 新增代码+ResourcePreparationConvergence：模拟 type 被准备状态拦截；如果没有这一行，marker 解析路径不会触发。
    pending = get_pending_actionability(runtime_state)  # 新增代码+ResourcePreparationConvergence：读取保存后的 pending；如果没有这一行，测试无法判断下一步是否被强制 observe。
    assert get_last_actionability_block(runtime_state) == {}  # 新增代码+ResourcePreparationConvergence：确认这不是终止用户动作阻断；如果没有这一行，Ctrl+N 后会错误要求用户介入。
    assert pending["marker"] == DESKTOP_RESOURCE_PREPARATION_OBSERVE_REQUIRED_MARKER  # 新增代码+ResourcePreparationConvergence：确认 marker 被保存为 pending；如果没有这一行，普通 pending 可能冒充通过。
    assert pending["next_required_tool"] == "mcp__computer-use__observe"  # 新增代码+ResourcePreparationConvergence：确认下一步被强制成 observe；如果没有这一行，模型仍可能继续 type/key。
    assert pending["target_ref"] == "cu-target-test-0001"  # 新增代码+ResourcePreparationConvergence：确认目标窗口 ID 被保留；如果没有这一行，多窗口 observe 会丢绑定。
    assert pending["low_level_event_count"] == "0"  # 新增代码+ResourcePreparationConvergence：确认零事件证据被保存；如果没有这一行，验收日志无法证明拒绝安全。
    assert pending_actionability_argument_mismatch("mcp__computer-use__observe", {}, pending) == ""  # 新增代码+ResourcePreparationConvergence：确认 observe 可以靠 adapter 的 active target 自动绑定，不因缺 target_ref 被过度拦截；如果没有这一行，模型会被卡在无法 observe。
    # 新增代码+ResourcePreparationConvergence：函数段结束，test_resource_preparation_observe_required_marker_records_pending_observe 到此结束；如果没有这个边界说明，用户不容易看出 pending observe 测试范围。


def test_convergence_blocks_repeated_open_application_after_user_action_required() -> None:  # 新增代码+FreshTargetUserAction：函数段开始，验证旧窗口拒绝后收敛器会拦截重复启动；如果没有这段测试，截图里的循环不会被上层发现。
    runtime_state: dict[str, object] = {}  # 新增代码+FreshTargetUserAction：准备运行态；如果没有这一行，record_tool_result 和 decide_tool_call 无法共享阻断信息。
    task_state = TaskState.from_user_input("请打开本地真实记事本，并输入 hello everyone。")  # 新增代码+FreshTargetUserAction：构造真实用户风格任务；如果没有这一行，收敛提示缺少原始目标。
    tool_call = {"name": "mcp__computer-use__open_application", "arguments": {"app_name": "notepad"}}  # 新增代码+FreshTargetUserAction：模拟模型调用启动应用工具；如果没有这一行，测试无法覆盖重复 open_application。
    record_tool_result(tool_call, _fresh_target_user_action_output(), task_state, runtime_state)  # 新增代码+FreshTargetUserAction：先记录第一次旧窗口拒绝结果；如果没有这一行，后续决策不知道用户动作阻断已经发生。
    assessment = assess_before_model(task_state, [], runtime_state)  # 新增代码+FreshTargetUserAction：模拟下一轮模型调用前评估；如果没有这一行，测试无法证明模型会收到停止工具的提醒。
    assert assessment.should_inject_message is True  # 新增代码+FreshTargetUserAction：确认会注入提醒；如果没有这一行，模型可能继续自己决定调用工具。
    assert assessment.reason == "fresh_target_user_action_requires_final_answer"  # 新增代码+FreshTargetUserAction：确认注入原因稳定；如果没有这一行，验收日志无法识别这个专门门禁。
    decision = decide_tool_call(tool_call, task_state, runtime_state)  # 新增代码+FreshTargetUserAction：模拟模型仍然再次调用 open_application；如果没有这一行，测试不能覆盖真实截图中的重复行为。
    assert decision.execute_real_tool is False  # 新增代码+FreshTargetUserAction：确认重复启动不会真实执行；如果没有这一行，旧窗口状态下仍可能继续启动或污染桌面。
    assert decision.reason == "fresh_target_user_action_required"  # 新增代码+FreshTargetUserAction：确认阻断原因稳定；如果没有这一行，debug 日志无法统计此类问题。
    assert "请先手动关闭" in str(decision.synthetic_output)  # 新增代码+FreshTargetUserAction：确认合成输出提醒用户关闭旧窗口；如果没有这一行，最终回答可能仍然跑偏。
    assert "low_level_event_count=0" in str(decision.synthetic_output)  # 新增代码+FreshTargetUserAction：确认阻断输出保留零事件证据；如果没有这一行，安全验收无法确认没有底层动作。
    assert decision.injected_message is not None  # 新增代码+FreshTargetUserAction：确认给模型注入收束消息；如果没有这一行，模型可能看不到为什么不该继续工具。
    assert "最终回答" in decision.injected_message["content"]  # 新增代码+FreshTargetUserAction：确认注入消息要求最终答复用户；如果没有这一行，模型可能继续寻找其他工具。
    # 新增代码+FreshTargetUserAction：函数段结束，test_convergence_blocks_repeated_open_application_after_user_action_required 到此结束；如果没有这个边界说明，用户不容易看出上层收敛测试范围。
