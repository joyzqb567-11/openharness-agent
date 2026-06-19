"""测试已有 target_ref 时重复 launch_app 会在权限前被拒绝。"""  # 新增代码+FreshTargetRepeatedLaunchGateTest：说明本文件覆盖重复启动门禁；如果没有这一行，读者不清楚测试目的。
from __future__ import annotations  # 新增代码+FreshTargetRepeatedLaunchGateTest：启用延迟类型注解；如果没有这一行，旧解释路径可能受类型顺序影响。

from typing import Any  # 新增代码+FreshTargetRepeatedLaunchGateTest：导入 Any 描述观察 payload；如果没有这一行，测试类型边界不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.agent_tools import _desktop_redundant_launch_rejection_text  # 新增代码+FreshTargetRepeatedLaunchGateTest：导入被测内部门禁；如果没有这一行，测试无法验证权限前拒绝。


class _Registry:  # 新增代码+FreshTargetRepeatedLaunchGateTest：类段开始，模拟目标注册表；如果没有这个类，测试无法返回已有 target_ref。
    def resolve_target_label(self, label: str) -> dict[str, Any]:  # 新增代码+FreshTargetRepeatedLaunchGateTest：函数段开始，按应用标签返回目标；如果没有这段函数，被测门禁找不到已有目标。
        return {"allowed": label.lower() in {"notepad", "notepad.exe"}, "target_ref": "cu-target-1"}  # 新增代码+FreshTargetRepeatedLaunchGateTest：对 notepad 返回有效 target_ref；如果没有这一行，重复启动拒绝不会触发。
    # 新增代码+FreshTargetRepeatedLaunchGateTest：函数段结束，_Registry.resolve_target_label 到此结束；如果没有这个边界说明，用户不容易看出 fake 查询范围。
# 新增代码+FreshTargetRepeatedLaunchGateTest：类段结束，_Registry 到此结束；如果没有这个边界说明，用户不容易看出 fake registry 范围。


class _Controller:  # 新增代码+FreshTargetRepeatedLaunchGateTest：类段开始，模拟带 target_registry 的 controller；如果没有这个类，被测函数没有 controller 输入。
    target_registry = _Registry()  # 新增代码+FreshTargetRepeatedLaunchGateTest：挂载 fake 注册表；如果没有这一行，重复启动门禁会按兼容路径放行。
# 新增代码+FreshTargetRepeatedLaunchGateTest：类段结束，_Controller 到此结束；如果没有这个边界说明，用户不容易看出 fake controller 范围。


def test_redundant_launch_rejected_before_permission_with_existing_target_ref() -> None:  # 新增代码+FreshTargetRepeatedLaunchGateTest：函数段开始，验证已有 target_ref 的重复 launch 拒绝；如果没有这段测试，压力场景可能回到反复弹权限。
    observations: list[tuple[str, dict[str, Any]]] = []  # 新增代码+FreshTargetRepeatedLaunchGateTest：记录观察事件；如果没有这一行，拒绝日志无法断言。
    traces: list[tuple[str, dict[str, Any]]] = []  # 新增代码+FreshTargetRepeatedLaunchGateTest：记录 runtime trace；如果没有这一行，零事件证据无法断言。
    result = _desktop_redundant_launch_rejection_text(  # 新增代码+FreshTargetRepeatedLaunchGateTest：调用被测门禁；如果没有这一行，测试没有实际行为。
        "launch_app",  # 新增代码+FreshTargetRepeatedLaunchGateTest：模拟重复打开应用动作；如果没有这一行，门禁不会适用。
        {"app_name": "notepad", "target_app": "notepad"},  # 新增代码+FreshTargetRepeatedLaunchGateTest：传入同一目标应用；如果没有这一行，注册表无法命中。
        _Controller(),  # 新增代码+FreshTargetRepeatedLaunchGateTest：传入已有 target_ref 的 controller；如果没有这一行，重复判断没有事实来源。
        lambda kind, payload: observations.append((kind, payload)),  # 新增代码+FreshTargetRepeatedLaunchGateTest：收集观察事件；如果没有这一行，审计输出不可验证。
        lambda kind, payload: traces.append((kind, payload)),  # 新增代码+FreshTargetRepeatedLaunchGateTest：收集 trace 事件；如果没有这一行，零事件输出不可验证。
    )  # 新增代码+FreshTargetRepeatedLaunchGateTest：结束门禁调用；如果没有这一行，Python 语法不完整。
    assert result is not None  # 新增代码+FreshTargetRepeatedLaunchGateTest：确认重复 launch 被拒绝；如果没有这一行，权限前门禁可能失效。
    assert "existing_target_ref_must_be_used_before_relaunch" in result  # 新增代码+FreshTargetRepeatedLaunchGateTest：确认拒绝 token 稳定；如果没有这一行，模型纠偏不可机器判断。
    assert observations[0][1]["target_ref"] == "cu-target-1"  # 新增代码+FreshTargetRepeatedLaunchGateTest：确认报告告诉模型使用哪个 target_ref；如果没有这一行，模型仍可能不知道下一步。
    assert traces[0][1]["low_level_event_count"] == 0  # 新增代码+FreshTargetRepeatedLaunchGateTest：确认拒绝零桌面事件；如果没有这一行，安全验收缺关键证据。
# 新增代码+FreshTargetRepeatedLaunchGateTest：函数段结束，test_redundant_launch_rejected_before_permission_with_existing_target_ref 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_explicit_new_target_request_bypasses_redundant_launch_gate() -> None:  # 新增代码+FreshTargetRepeatedLaunchGateTest：函数段开始，验证显式新目标不会被误挡；如果没有这段测试，多窗口合法场景可能被破坏。
    result = _desktop_redundant_launch_rejection_text(  # 新增代码+FreshTargetRepeatedLaunchGateTest：调用被测门禁；如果没有这一行，测试没有实际行为。
        "launch_app",  # 新增代码+FreshTargetRepeatedLaunchGateTest：模拟打开应用动作；如果没有这一行，门禁不适用。
        {"app_name": "notepad", "force_new_target": True},  # 新增代码+FreshTargetRepeatedLaunchGateTest：显式要求新目标；如果没有这一行，测试不覆盖放行条件。
        _Controller(),  # 新增代码+FreshTargetRepeatedLaunchGateTest：传入已有 target_ref 的 controller；如果没有这一行，放行不是在重复场景里发生。
        lambda _kind, _payload: None,  # 新增代码+FreshTargetRepeatedLaunchGateTest：提供空观察回调；如果没有这一行，函数签名不完整。
        lambda _kind, _payload: None,  # 新增代码+FreshTargetRepeatedLaunchGateTest：提供空 trace 回调；如果没有这一行，函数签名不完整。
    )  # 新增代码+FreshTargetRepeatedLaunchGateTest：结束门禁调用；如果没有这一行，Python 语法不完整。
    assert result is None  # 新增代码+FreshTargetRepeatedLaunchGateTest：确认显式新目标请求可以继续；如果没有这一行，复杂多窗口任务会被过度拦截。
# 新增代码+FreshTargetRepeatedLaunchGateTest：函数段结束，test_explicit_new_target_request_bypasses_redundant_launch_gate 到此结束；如果没有这个边界说明，用户不容易看出放行范围。
