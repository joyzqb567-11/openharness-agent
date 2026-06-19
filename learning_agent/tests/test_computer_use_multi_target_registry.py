"""测试 Computer Use 多目标 registry 行为。"""  # 新增代码+FreshTargetRegistryTest：说明本文件验证 target_ref 注册表的多目标和失效逻辑；如果没有这一行，读者不容易知道测试目标。
from __future__ import annotations  # 新增代码+FreshTargetRegistryTest：启用延迟类型注解；如果没有这一行，测试在旧路径下可能受类型导入顺序影响。

from typing import Any  # 新增代码+FreshTargetRegistryTest：导入 Any 表示窗口字典的动态字段；如果没有这一行，测试 helper 类型不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.target_registry import ComputerUseTargetRegistry  # 新增代码+FreshTargetRegistryTest：导入被测目标注册表；如果没有这一行，测试无法覆盖 registry 底座。


def _window(app_id: str, pid: int, hwnd: int) -> dict[str, Any]:  # 新增代码+FreshTargetRegistryTest：函数段开始，构造目标窗口；如果没有这段函数，测试会重复写窗口字段。
    return {  # 新增代码+FreshTargetRegistryTest：返回窗口字典；如果没有这一行，registry 没有目标输入。
        "app_id": app_id,  # 新增代码+FreshTargetRegistryTest：保存应用身份；如果没有这一行，目标记录无法说明属于哪个应用。
        "process_name": app_id,  # 新增代码+FreshTargetRegistryTest：保存进程名；如果没有这一行，标签解析缺少进程线索。
        "pid": pid,  # 新增代码+FreshTargetRegistryTest：保存进程 id；如果没有这一行，窗口身份缺少进程维度。
        "window_id": f"hwnd:{hwnd}",  # 新增代码+FreshTargetRegistryTest：保存窗口 id；如果没有这一行，target_ref 无法还原窗口。
        "hwnd": hwnd,  # 新增代码+FreshTargetRegistryTest：保存窗口句柄；如果没有这一行，漂移报告缺少 hwnd。
        "title_preview": f"{app_id} window",  # 新增代码+FreshTargetRegistryTest：保存标题摘要；如果没有这一行，标签解析和状态报告不可读。
    }  # 新增代码+FreshTargetRegistryTest：结束窗口字典；如果没有这一行，Python 语法不完整。
# 新增代码+FreshTargetRegistryTest：函数段结束，_window 到此结束；如果没有这个边界说明，用户不容易看出窗口夹具范围。


def test_registry_resolves_single_target_implicitly() -> None:  # 新增代码+FreshTargetRegistryTest：函数段开始，验证只有一个目标时可隐式解析；如果没有这段测试，简单任务可能被无谓要求 target_ref。
    registry = ComputerUseTargetRegistry(session_id="single-target-test")  # 新增代码+FreshTargetRegistryTest：创建独立 registry；如果没有这一行，测试没有被测对象。
    target_ref = registry.register_target(_window("notepad.exe", 101, 201), lease={"target_ref": "", "origin": "agent_owned_launch"})  # 新增代码+FreshTargetRegistryTest：注册一个目标；如果没有这一行，隐式解析没有候选。
    resolved = registry.resolve_implicit_target()  # 新增代码+FreshTargetRegistryTest：执行隐式解析；如果没有这一行，测试无法检查单目标兼容。
    assert resolved["ok"] is True  # 新增代码+FreshTargetRegistryTest：确认单目标可解析；如果没有这一行，简单任务兼容可能丢失。
    assert resolved["target_ref"] == target_ref  # 新增代码+FreshTargetRegistryTest：确认解析出的 ref 是唯一目标；如果没有这一行，registry 可能返回错误目标。
    assert resolved["decision"] == "resolved_implicit_single_target"  # 新增代码+FreshTargetRegistryTest：确认决策 token 稳定；如果没有这一行，controller 无法可靠解释来源。
# 新增代码+FreshTargetRegistryTest：函数段结束，test_registry_resolves_single_target_implicitly 到此结束；如果没有这个边界说明，用户不容易看出单目标范围。


def test_registry_rejects_implicit_resolution_when_multiple_targets_exist() -> None:  # 新增代码+FreshTargetRegistryTest：函数段开始，验证多目标必须显式 target_ref；如果没有这段测试，复杂任务可能误用 active 窗口。
    registry = ComputerUseTargetRegistry(session_id="multi-target-test")  # 新增代码+FreshTargetRegistryTest：创建独立 registry；如果没有这一行，测试没有被测对象。
    registry.register_target(_window("notepad.exe", 101, 201), lease={"origin": "agent_owned_launch"})  # 新增代码+FreshTargetRegistryTest：注册第一个目标；如果没有这一行，多目标场景不成立。
    registry.register_target(_window("mspaint.exe", 102, 202), lease={"origin": "agent_owned_launch"})  # 新增代码+FreshTargetRegistryTest：注册第二个目标；如果没有这一行，隐式解析不会歧义。
    resolved = registry.resolve_implicit_target()  # 新增代码+FreshTargetRegistryTest：尝试隐式解析；如果没有这一行，多目标拒绝不会触发。
    assert resolved["ok"] is False  # 新增代码+FreshTargetRegistryTest：确认多目标隐式解析被拒绝；如果没有这一行，动作可能打到错误窗口。
    assert resolved["decision"] == "multiple_active_targets_require_target_ref"  # 新增代码+FreshTargetRegistryTest：确认拒绝 token 稳定；如果没有这一行，模型不知道要补 target_ref。
    assert resolved["low_level_event_count"] == 0  # 新增代码+FreshTargetRegistryTest：确认 registry 判断零事件；如果没有这一行，安全门禁可能带副作用。
# 新增代码+FreshTargetRegistryTest：函数段结束，test_registry_rejects_implicit_resolution_when_multiple_targets_exist 到此结束；如果没有这个边界说明，用户不容易看出多目标范围。


def test_registry_invalidates_target_ref_after_drift() -> None:  # 新增代码+FreshTargetRegistryTest：函数段开始，验证 target_ref 可被失效；如果没有这段测试，漂移后的坏 ref 可能继续可解析。
    registry = ComputerUseTargetRegistry(session_id="invalidate-target-test")  # 新增代码+FreshTargetRegistryTest：创建独立 registry；如果没有这一行，测试没有状态容器。
    target_ref = registry.register_target(_window("notepad.exe", 101, 201), lease={"origin": "agent_owned_launch"})  # 新增代码+FreshTargetRegistryTest：注册一个目标；如果没有这一行，失效没有对象。
    invalidated = registry.invalidate_target(target_ref, reason="target_lease_drift_rejected")  # 新增代码+FreshTargetRegistryTest：执行 target 失效；如果没有这一行，测试无法证明漂移恢复。
    resolved = registry.resolve_target_ref(target_ref)  # 新增代码+FreshTargetRegistryTest：再次解析同一个 ref；如果没有这一行，失效状态无法断言。
    assert invalidated["invalidated"] is True  # 新增代码+FreshTargetRegistryTest：确认失效调用成功；如果没有这一行，replace 更新可能没有生效。
    assert resolved["ok"] is False  # 新增代码+FreshTargetRegistryTest：确认失效后不再允许解析；如果没有这一行，坏 ref 仍可能继续动作。
    assert resolved["decision"] == "target_ref_invalidated"  # 新增代码+FreshTargetRegistryTest：确认失效拒绝 token 稳定；如果没有这一行，恢复路径不明确。
    assert registry.get_active_target() is None  # 新增代码+FreshTargetRegistryTest：确认 active target 被清空；如果没有这一行，漏传 target_ref 时还会注入旧窗口。
# 新增代码+FreshTargetRegistryTest：函数段结束，test_registry_invalidates_target_ref_after_drift 到此结束；如果没有这个边界说明，用户不容易看出失效范围。
