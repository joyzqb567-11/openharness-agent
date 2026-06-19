"""测试 Computer Use 动作门禁要求 target_ref 一对一绑定。"""  # 新增代码+FreshTargetTargetRefGateTest：说明本测试覆盖权限前 target_ref 门禁；如果没有这一行，读者不清楚测试目标。
from __future__ import annotations  # 新增代码+FreshTargetTargetRefGateTest：启用延迟类型注解；如果没有这一行，旧解释路径可能受类型顺序影响。

from typing import Any  # 新增代码+FreshTargetTargetRefGateTest：导入 Any 描述 fake controller 动态字段；如果没有这一行，测试 helper 类型不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.action_gates import computer_use_agent_owned_launch_rejection, computer_use_observe_before_action_rejection  # 修改代码+ObserveBeforeActionPendingTest：同时导入先观察门禁；如果没有这一行，测试无法覆盖盲动拒绝写入 pending marker。


class _Registry:  # 新增代码+FreshTargetTargetRefGateTest：类段开始，模拟目标注册表；如果没有这个类，多目标数量无法测试。
    def __init__(self, count: int) -> None:  # 新增代码+FreshTargetTargetRefGateTest：函数段开始，保存目标数量；如果没有这段函数，fake registry 没有状态。
        self._count = count  # 新增代码+FreshTargetTargetRefGateTest：保存有效目标数量；如果没有这一行，target_count 无法返回预期值。
    # 新增代码+FreshTargetTargetRefGateTest：函数段结束，_Registry.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def target_count(self) -> int:  # 新增代码+FreshTargetTargetRefGateTest：函数段开始，返回目标数量；如果没有这段函数，action gate 无法判断多目标。
        return self._count  # 新增代码+FreshTargetTargetRefGateTest：返回构造时保存的数量；如果没有这一行，多目标拒绝测试没有事实依据。
    # 新增代码+FreshTargetTargetRefGateTest：函数段结束，_Registry.target_count 到此结束；如果没有这个边界说明，用户不容易看出计数范围。
# 新增代码+FreshTargetTargetRefGateTest：类段结束，_Registry 到此结束；如果没有这个边界说明，用户不容易看出 fake registry 范围。


class _Controller:  # 新增代码+FreshTargetTargetRefGateTest：类段开始，模拟已有 agent-owned 目标的 controller；如果没有这个类，门禁会认为尚未 launch_app。
    def __init__(self, count: int = 1) -> None:  # 新增代码+FreshTargetTargetRefGateTest：函数段开始，装配 active window 和 registry；如果没有这段函数，fake controller 不完整。
        self.active_agent_owned_target_window = {"app_id": "notepad.exe", "window_id": "hwnd:1"}  # 新增代码+FreshTargetTargetRefGateTest：提供已绑定窗口事实；如果没有这一行，门禁会返回先 launch_app。
        self.target_registry = _Registry(count)  # 新增代码+FreshTargetTargetRefGateTest：提供目标数量接口；如果没有这一行，多目标判断无法覆盖。
    # 新增代码+FreshTargetTargetRefGateTest：函数段结束，_Controller.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 controller 夹具范围。
# 新增代码+FreshTargetTargetRefGateTest：类段结束，_Controller 到此结束；如果没有这个边界说明，用户不容易看出 fake controller 范围。


def _context() -> dict[str, Any]:  # 新增代码+FreshTargetTargetRefGateTest：函数段开始，生成 full Computer Use 上下文；如果没有这段函数，每个测试会重复写上下文。
    return {"active": True, "requires_gui_actions": True, "target_app_hint": "notepad"}  # 新增代码+FreshTargetTargetRefGateTest：返回会启用动作门禁的上下文；如果没有这一行，门禁不会参与测试。
# 新增代码+FreshTargetTargetRefGateTest：函数段结束，_context 到此结束；如果没有这个边界说明，用户不容易看出上下文内容。


def test_raw_window_write_requires_target_ref_before_permission() -> None:  # 新增代码+FreshTargetTargetRefGateTest：函数段开始，验证 raw window 缺 target_ref 前置拒绝；如果没有这段测试，旧窗口可能先弹权限。
    observations: list[tuple[str, dict[str, Any]]] = []  # 新增代码+FreshTargetTargetRefGateTest：保存门禁观察记录；如果没有这一行，测试无法确认拒绝事件被记录。
    result = computer_use_agent_owned_launch_rejection(  # 新增代码+FreshTargetTargetRefGateTest：调用被测门禁；如果没有这一行，测试没有实际行为。
        "press_key",  # 新增代码+FreshTargetTargetRefGateTest：模拟真实键盘写动作；如果没有这一行，门禁可能不适用。
        {"window": {"app_id": "Notepad.exe", "window_id": "hwnd:old"}, "key": "CTRL+N"},  # 新增代码+FreshTargetTargetRefGateTest：传入 raw window 且故意不带 target_ref；如果没有这一行，风险场景不存在。
        _context(),  # 新增代码+FreshTargetTargetRefGateTest：传入 full 模式上下文；如果没有这一行，门禁不会启用。
        _Controller(),  # 新增代码+FreshTargetTargetRefGateTest：传入已有目标 controller；如果没有这一行，测试会落到先 launch_app 拒绝。
        lambda kind, payload: observations.append((kind, payload)),  # 新增代码+FreshTargetTargetRefGateTest：记录观察事件；如果没有这一行，拒绝证据不可断言。
    )  # 新增代码+FreshTargetTargetRefGateTest：结束门禁调用；如果没有这一行，Python 语法不完整。
    assert result is not None  # 新增代码+FreshTargetTargetRefGateTest：确认门禁拒绝；如果没有这一行，缺 target_ref 会继续弹权限。
    assert "target_ref_required_for_bound_window_action" in result  # 新增代码+FreshTargetTargetRefGateTest：确认拒绝原因稳定；如果没有这一行，模型可能不知道如何纠正。
    assert observations[0][0] == "computer_use_target_ref_required_for_bound_window_action"  # 新增代码+FreshTargetTargetRefGateTest：确认拒绝事件写入观察日志；如果没有这一行，验收缺审计证据。
# 新增代码+FreshTargetTargetRefGateTest：函数段结束，test_raw_window_write_requires_target_ref_before_permission 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_multi_target_write_requires_target_ref_even_without_raw_window() -> None:  # 新增代码+FreshTargetTargetRefGateTest：函数段开始，验证多目标缺 target_ref 前置拒绝；如果没有这段测试，多应用任务会误用最近窗口。
    observations: list[tuple[str, dict[str, Any]]] = []  # 新增代码+FreshTargetTargetRefGateTest：保存观察记录；如果没有这一行，拒绝事件不可断言。
    result = computer_use_agent_owned_launch_rejection(  # 新增代码+FreshTargetTargetRefGateTest：调用被测门禁；如果没有这一行，测试没有实际行为。
        "type_text",  # 新增代码+FreshTargetTargetRefGateTest：模拟文本输入动作；如果没有这一行，测试不覆盖写入路径。
        {"text": "hello"},  # 新增代码+FreshTargetTargetRefGateTest：故意不带 target_ref；如果没有这一行，多目标歧义不存在。
        _context(),  # 新增代码+FreshTargetTargetRefGateTest：传入 full 模式上下文；如果没有这一行，门禁不会启用。
        _Controller(count=2),  # 新增代码+FreshTargetTargetRefGateTest：模拟两个有效目标；如果没有这一行，多目标拒绝不会触发。
        lambda kind, payload: observations.append((kind, payload)),  # 新增代码+FreshTargetTargetRefGateTest：记录观察事件；如果没有这一行，测试无法确认日志。
    )  # 新增代码+FreshTargetTargetRefGateTest：结束门禁调用；如果没有这一行，Python 语法不完整。
    assert result is not None  # 新增代码+FreshTargetTargetRefGateTest：确认多目标缺 target_ref 被拒绝；如果没有这一行，动作可能打到错误软件。
    assert observations[0][1]["active_target_count"] == 2  # 新增代码+FreshTargetTargetRefGateTest：确认报告里保留目标数量；如果没有这一行，模型看不出为什么必须指定。
# 新增代码+FreshTargetTargetRefGateTest：函数段结束，test_multi_target_write_requires_target_ref_even_without_raw_window 到此结束；如果没有这个边界说明，用户不容易看出多目标范围。


def test_single_target_without_raw_window_keeps_implicit_compatibility() -> None:  # 新增代码+FreshTargetTargetRefGateTest：函数段开始，验证单目标无 raw window 仍兼容；如果没有这段测试，旧单目标流程可能被过度收紧。
    result = computer_use_agent_owned_launch_rejection(  # 新增代码+FreshTargetTargetRefGateTest：调用被测门禁；如果没有这一行，测试没有实际行为。
        "type_text",  # 新增代码+FreshTargetTargetRefGateTest：模拟文本输入动作；如果没有这一行，测试不覆盖写入类动作。
        {"text": "hello"},  # 新增代码+FreshTargetTargetRefGateTest：不带 raw window 和 target_ref；如果没有这一行，兼容路径不成立。
        _context(),  # 新增代码+FreshTargetTargetRefGateTest：传入 full 模式上下文；如果没有这一行，门禁不会启用。
        _Controller(count=1),  # 新增代码+FreshTargetTargetRefGateTest：模拟只有一个有效目标；如果没有这一行，无法验证隐式单目标兼容。
        lambda _kind, _payload: None,  # 新增代码+FreshTargetTargetRefGateTest：提供空观察回调；如果没有这一行，函数签名不完整。
    )  # 新增代码+FreshTargetTargetRefGateTest：结束门禁调用；如果没有这一行，Python 语法不完整。
    assert result is None  # 新增代码+FreshTargetTargetRefGateTest：确认单目标无 raw window 仍放行给 controller；如果没有这一行，兼容路径可能被误杀。
# 新增代码+FreshTargetTargetRefGateTest：函数段结束，test_single_target_without_raw_window_keeps_implicit_compatibility 到此结束；如果没有这个边界说明，用户不容易看出兼容范围。


def test_observe_before_action_rejection_sets_actionability_pending_marker() -> None:  # 新增代码+ObserveBeforeActionPendingTest：函数段开始，验证盲动拒绝会要求下一步 observe；如果没有这段测试，模型可能再次用 Done 假结束。
    observations: list[tuple[str, dict[str, Any]]] = []  # 新增代码+ObserveBeforeActionPendingTest：保存拒绝观察记录；如果没有这一行，测试无法确认门禁事件被记录。
    result = computer_use_observe_before_action_rejection(  # 新增代码+ObserveBeforeActionPendingTest：调用先观察门禁；如果没有这一行，测试没有实际行为。
        "type_text",  # 新增代码+ObserveBeforeActionPendingTest：模拟会改变桌面的文本输入动作；如果没有这一行，观察门禁不会覆盖真实风险动作。
        {"window": {"app_id": "Notepad.exe", "window_id": "hwnd:1"}, "text": "hello"},  # 新增代码+ObserveBeforeActionPendingTest：传入目标窗口和文本；如果没有这一行，报告里无法体现窗口动作场景。
        _context(),  # 新增代码+ObserveBeforeActionPendingTest：传入 full Computer Use 上下文；如果没有这一行，观察门禁不会启用。
        [],  # 新增代码+ObserveBeforeActionPendingTest：不给最近可见截图事件；如果没有这一行，门禁会认为已经观察过而放行。
        lambda kind, payload: observations.append((kind, payload)),  # 新增代码+ObserveBeforeActionPendingTest：记录观察事件；如果没有这一行，审计路径无法断言。
    )  # 新增代码+ObserveBeforeActionPendingTest：结束门禁调用；如果没有这一行，Python 语法不完整。
    assert result is not None  # 新增代码+ObserveBeforeActionPendingTest：确认盲动被拒绝；如果没有这一行，后续 marker 断言没有意义。
    assert "OPENHARNESS_DESKTOP_ACTION_REQUIRED" in result  # 新增代码+ObserveBeforeActionPendingTest：确认结果会被 actionability 解析；如果没有这一行，收束器不会保存 pending。
    assert "next_required_tool=observe" in result  # 新增代码+ObserveBeforeActionPendingTest：确认下一步工具是 observe；如果没有这一行，模型不知道该调用什么。
    assert "next_required_action=get_window_state" in result  # 新增代码+ObserveBeforeActionPendingTest：确认 observe 必须读取窗口状态；如果没有这一行，模型可能做无关观察。
    assert observations[0][0] == "computer_use_observe_before_action_required"  # 新增代码+ObserveBeforeActionPendingTest：确认拒绝事件写入观察日志；如果没有这一行，真实验收缺排查证据。
    # 新增代码+ObserveBeforeActionPendingTest：函数段结束，test_observe_before_action_rejection_sets_actionability_pending_marker 到此结束；如果没有这个边界说明，用户不容易看出测试范围。
