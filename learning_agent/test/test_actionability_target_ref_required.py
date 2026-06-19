from learning_agent.core.actionability_state import pending_actionability_argument_mismatch  # 新增代码+FreshTargetPolicy：导入 pending 参数门禁函数；如果没有这一行，测试无法验证 target_ref 缺失会被阻断。


def test_desktop_pending_requires_target_ref_when_action_is_window_bound() -> None:  # 新增代码+FreshTargetPolicy：函数段开始，验证桌面动作必须显式携带 target_ref；如果没有这段测试，压力测试里漏写窗口 ID 的回归不会被发现。
    pending = {  # 新增代码+FreshTargetPolicy：构造桌面 pending 状态；如果没有这一行，门禁函数没有可比对的目标状态。
        "next_allowed_tools": "mcp__computer-use__key",  # 新增代码+FreshTargetPolicy：声明下一步允许调用 key 工具；如果没有这一行，测试不会进入正确工具的参数检查分支。
        "target_ref": "cu-target-test-0001",  # 新增代码+FreshTargetPolicy：模拟 launch_app 返回的一对一窗口 ID；如果没有这一行，门禁不知道应该强制哪个窗口。
    }  # 新增代码+FreshTargetPolicy：pending 状态构造结束；如果没有这一行，Python 字典语法不完整。
    mismatch = pending_actionability_argument_mismatch("mcp__computer-use__key", {"key": "CTRL+S"}, pending)  # 新增代码+FreshTargetPolicy：模拟模型调用 key 但漏写 target_ref；如果没有这一行，测试无法触发缺参门禁。
    assert "target_ref 参数缺失" in mismatch  # 新增代码+FreshTargetPolicy：确认错误指出缺少 target_ref；如果没有这一行，测试无法证明拒绝原因清楚。
    assert "cu-target-test-0001" in mismatch  # 新增代码+FreshTargetPolicy：确认错误带出正确窗口 ID；如果没有这一行，模型收到纠偏后仍不知道补什么参数。
    # 新增代码+FreshTargetPolicy：函数段结束，test_desktop_pending_requires_target_ref_when_action_is_window_bound 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_desktop_pending_accepts_matching_target_ref() -> None:  # 新增代码+FreshTargetPolicy：函数段开始，验证携带正确 target_ref 时不误拦；如果没有这段测试，门禁可能把正确动作也挡住。
    pending = {  # 新增代码+FreshTargetPolicy：构造带目标窗口的 pending 状态；如果没有这一行，正例测试没有目标依据。
        "next_allowed_tools": "mcp__computer-use__type",  # 新增代码+FreshTargetPolicy：声明下一步允许文本输入；如果没有这一行，测试不会进入桌面 type 分支。
        "target_ref": "cu-target-test-0002",  # 新增代码+FreshTargetPolicy：模拟新的窗口绑定 ID；如果没有这一行，正例不能证明 ID 匹配。
    }  # 新增代码+FreshTargetPolicy：pending 状态构造结束；如果没有这一行，Python 字典语法不完整。
    mismatch = pending_actionability_argument_mismatch("mcp__computer-use__type", {"text": "hello everyone", "target_ref": "cu-target-test-0002"}, pending)  # 新增代码+FreshTargetPolicy：模拟模型按要求带上 target_ref；如果没有这一行，测试无法验证正常放行。
    assert mismatch == ""  # 新增代码+FreshTargetPolicy：确认正确参数不会产生不匹配；如果没有这一行，门禁可能过度阻断正常任务。
    # 新增代码+FreshTargetPolicy：函数段结束，test_desktop_pending_accepts_matching_target_ref 到此结束；如果没有这个边界说明，用户不容易看出正例范围。


def test_browser_pending_does_not_require_desktop_target_ref() -> None:  # 新增代码+FreshTargetPolicy：函数段开始，验证浏览器动作不受桌面 target_ref 必填集合误伤；如果没有这段测试，网页任务可能被桌面策略挡住。
    pending = {  # 新增代码+FreshTargetPolicy：构造浏览器 pending 状态；如果没有这一行，测试无法区分浏览器和桌面工具。
        "next_required_tool": "browser_type",  # 新增代码+FreshTargetPolicy：声明浏览器输入工具；如果没有这一行，测试不会进入浏览器工具匹配。
        "target_ref": "cu-target-desktop-should-not-apply",  # 新增代码+FreshTargetPolicy：故意放入桌面字段；如果没有这一行，无法证明浏览器不会被这个字段误伤。
    }  # 新增代码+FreshTargetPolicy：pending 状态构造结束；如果没有这一行，Python 字典语法不完整。
    mismatch = pending_actionability_argument_mismatch("mcp__browser_automation__browser_type", {"text": "hello"}, pending)  # 新增代码+FreshTargetPolicy：模拟浏览器输入没有 target_ref；如果没有这一行，测试无法验证浏览器兼容性。
    assert mismatch == ""  # 新增代码+FreshTargetPolicy：确认浏览器动作不会被桌面窗口 ID 策略误拦；如果没有这一行，跨工具任务可能被错误阻断。
    # 新增代码+FreshTargetPolicy：函数段结束，test_browser_pending_does_not_require_desktop_target_ref 到此结束；如果没有这个边界说明，用户不容易看出兼容范围。
