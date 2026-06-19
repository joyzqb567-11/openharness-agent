"""Computer Use actionability 自动恢复决策。"""  # 新增代码+AutoObserveRecovery：说明本模块只负责把可机器恢复的 pending 转成恢复计划；如果没有这一行，维护者容易把桌面执行逻辑误放进这里。
from __future__ import annotations  # 新增代码+AutoObserveRecovery：延迟解析类型注解；如果没有这一行，dataclass 类型在脚本模式下更容易受导入顺序影响。

from dataclasses import dataclass, field  # 新增代码+AutoObserveRecovery：导入 dataclass 和默认字典工厂；如果没有这一行，恢复计划需要手写初始化样板。
from typing import Any  # 新增代码+AutoObserveRecovery：导入宽松 JSON 类型；如果没有这一行，runtime_state 和 arguments 的接口边界不清楚。

try:  # 新增代码+AutoObserveRecovery：优先按包路径导入 actionability 协议；如果没有这一段，包运行模式下无法复用稳定 marker 和归一化逻辑。
    from learning_agent.core.actionability_state import ACTIONABILITY_LAST_BLOCK_KEY, DESKTOP_ACTION_REQUIRED_MARKER, normalize_actionability_tool_name  # 新增代码+AutoObserveRecovery：导入 pending 判断需要的常量和工具名归一函数；如果没有这一行，恢复层会手写脆弱字符串和匹配规则。
except ModuleNotFoundError as error:  # 新增代码+AutoObserveRecovery：兼容 start_oauth_agent.bat 脚本模式缺少 learning_agent 包名前缀；如果没有这一段，直接脚本运行可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.actionability_state"}:  # 新增代码+AutoObserveRecovery：只允许目标包路径缺失时 fallback；如果没有这一行，actionability_state 内部真实 bug 会被误吞。
        raise  # 新增代码+AutoObserveRecovery：非路径问题继续抛出；如果没有这一行，真实导入错误会被伪装成脚本模式问题。
    from core.actionability_state import ACTIONABILITY_LAST_BLOCK_KEY, DESKTOP_ACTION_REQUIRED_MARKER, normalize_actionability_tool_name  # 新增代码+AutoObserveRecovery：脚本模式下从同级 core 包导入协议；如果没有这一行，bat 入口无法使用恢复模块。


AUTO_OBSERVE_RECOVERY_ATTEMPTS_KEY = "actionability_auto_observe_recovery_attempts"  # 新增代码+AutoObserveRecovery：保存自动 observe 尝试次数的 runtime_state 键；如果没有这一行，observe 失败可能无限自动重试。
AUTO_OBSERVE_RECOVERY_DEFAULT_MAX_ATTEMPTS = 1  # 新增代码+AutoObserveRecovery：默认每个 pending 只自动补一次 observe；如果没有这一行，复杂任务容易在恢复层循环。


@dataclass(frozen=True)  # 新增代码+AutoObserveRecovery：让恢复计划不可变，避免主循环执行时被误改；如果没有这一行，测试和运行时可能共享可变对象。
class ActionabilityRecoveryPlan:  # 新增代码+AutoObserveRecovery：函数段开始，定义自动恢复计划数据结构；如果没有这个类，主循环只能传松散字典且容易漏字段。
    should_recover: bool  # 新增代码+AutoObserveRecovery：声明是否应该自动执行恢复；如果没有这一行，调用方无法区分可恢复和不可恢复状态。
    tool_name: str = ""  # 新增代码+AutoObserveRecovery：保存要合成的工具名；如果没有这一行，主循环不知道该调用 observe 还是其他工具。
    arguments: dict[str, Any] = field(default_factory=dict)  # 新增代码+AutoObserveRecovery：保存合成工具参数；如果没有这一行，observe 目标和原因无法传给工具。
    reason: str = ""  # 新增代码+AutoObserveRecovery：保存决策原因；如果没有这一行，debug 和 acceptance 无法解释为什么恢复或拒绝恢复。
    recovery_key: str = ""  # 新增代码+AutoObserveRecovery：保存尝试计数键；如果没有这一行，重复保护无法按目标窗口隔离。
    max_attempts: int = AUTO_OBSERVE_RECOVERY_DEFAULT_MAX_ATTEMPTS  # 新增代码+AutoObserveRecovery：保存本计划最大尝试次数；如果没有这一行，调用方无法审计预算。
    # 新增代码+AutoObserveRecovery：函数段结束，ActionabilityRecoveryPlan 到此结束；如果没有这个边界说明，用户不容易看出计划字段范围。


def _runtime_dict(runtime_state: dict[str, Any] | None) -> dict[str, Any]:  # 新增代码+AutoObserveRecovery：函数段开始，安全取得可写 runtime_state；如果没有这段函数，None 状态会让恢复计数崩溃。
    return runtime_state if isinstance(runtime_state, dict) else {}  # 新增代码+AutoObserveRecovery：字典原样返回，否则返回空字典；如果没有这一行，调用方需要到处防御 None。
    # 新增代码+AutoObserveRecovery：函数段结束，_runtime_dict 到此结束；如果没有这个边界说明，用户不容易看出它只做安全适配。


def _blocked_plan(reason: str, recovery_key: str = "", max_attempts: int = AUTO_OBSERVE_RECOVERY_DEFAULT_MAX_ATTEMPTS) -> ActionabilityRecoveryPlan:  # 新增代码+AutoObserveRecovery：函数段开始，构造不可恢复计划；如果没有这段函数，多个拒绝分支会重复样板字段。
    return ActionabilityRecoveryPlan(False, reason=reason, recovery_key=recovery_key, max_attempts=max_attempts)  # 新增代码+AutoObserveRecovery：返回带原因的 false 计划；如果没有这一行，调用方拿不到稳定拒绝原因。
    # 新增代码+AutoObserveRecovery：函数段结束，_blocked_plan 到此结束；如果没有这个边界说明，用户不容易看出拒绝计划构造范围。


def _user_action_block_active(runtime_state: dict[str, Any] | None) -> bool:  # 新增代码+AutoObserveRecovery：函数段开始，判断 FreshTarget 用户动作阻断是否存在；如果没有这段函数，自动 observe 可能绕过旧窗口硬停止。
    state = _runtime_dict(runtime_state)  # 新增代码+AutoObserveRecovery：读取运行态字典；如果没有这一行，后续无法读取最近阻断。
    block = state.get(ACTIONABILITY_LAST_BLOCK_KEY)  # 新增代码+AutoObserveRecovery：读取最近 actionability 阻断；如果没有这一行，恢复层不知道是否应停止工具。
    if not isinstance(block, dict):  # 新增代码+AutoObserveRecovery：非字典阻断视为无效；如果没有这一行，坏状态可能触发属性访问错误。
        return False  # 新增代码+AutoObserveRecovery：没有有效阻断时允许继续判断恢复；如果没有这一行，函数缺少安全出口。
    return str(block.get("block_class", "") or "") == "user_action_required"  # 新增代码+AutoObserveRecovery：只有用户动作阻断才禁止自动恢复；如果没有这一行，工具失败也可能被误当硬停止。
    # 新增代码+AutoObserveRecovery：函数段结束，_user_action_block_active 到此结束；如果没有这个边界说明，用户不容易看出硬停止判定范围。


def _recovery_attempt_count(runtime_state: dict[str, Any] | None, recovery_key: str) -> int:  # 新增代码+AutoObserveRecovery：函数段开始，读取某个恢复目标已尝试次数；如果没有这段函数，预算判断会散落。
    state = _runtime_dict(runtime_state)  # 新增代码+AutoObserveRecovery：取得运行态；如果没有这一行，尝试次数字典没有来源。
    attempts = state.get(AUTO_OBSERVE_RECOVERY_ATTEMPTS_KEY)  # 新增代码+AutoObserveRecovery：读取尝试次数字典；如果没有这一行，预算无法跨步骤生效。
    if not isinstance(attempts, dict):  # 新增代码+AutoObserveRecovery：异常状态按零次处理；如果没有这一行，坏状态会让 int 转换崩溃。
        return 0  # 新增代码+AutoObserveRecovery：返回零次尝试；如果没有这一行，函数缺少异常状态出口。
    return int(attempts.get(recovery_key, 0) or 0)  # 新增代码+AutoObserveRecovery：读取并规范化计数；如果没有这一行，字符串或 None 计数会影响预算判断。
    # 新增代码+AutoObserveRecovery：函数段结束，_recovery_attempt_count 到此结束；如果没有这个边界说明，用户不容易看出计数读取范围。


def build_desktop_observe_recovery_plan(pending: dict[str, str], runtime_state: dict[str, Any] | None) -> ActionabilityRecoveryPlan:  # 新增代码+AutoObserveRecovery：函数段开始，把桌面 observe-required pending 转成自动恢复计划；如果没有这段函数，主循环仍只能靠模型自己听提示。
    if not pending:  # 新增代码+AutoObserveRecovery：没有 pending 时不能恢复；如果没有这一行，普通工具结果可能误触发 observe。
        return _blocked_plan("no_pending_actionability")  # 新增代码+AutoObserveRecovery：返回无 pending 原因；如果没有这一行，调用方不知道为什么不恢复。
    if _user_action_block_active(runtime_state):  # 新增代码+AutoObserveRecovery：用户动作阻断优先级最高；如果没有这一行，旧窗口拒绝可能被自动 observe 绕过。
        return _blocked_plan("user_action_required_block_active")  # 新增代码+AutoObserveRecovery：返回硬停止原因；如果没有这一行，调试日志难以解释拒绝恢复。
    if str(pending.get("marker", "") or "") != DESKTOP_ACTION_REQUIRED_MARKER:  # 新增代码+AutoObserveRecovery：只恢复桌面动作要求 marker；如果没有这一行，浏览器或资源阻断可能被错误接管。
        return _blocked_plan("pending_marker_not_desktop_action_required")  # 新增代码+AutoObserveRecovery：返回 marker 不匹配原因；如果没有这一行，调用方无法区分协议类别。
    if str(pending.get("actionability_kind", "") or "") != "desktop_observe_before_action":  # 新增代码+AutoObserveRecovery：只恢复动作前观察要求；如果没有这一行，其他桌面 pending 可能被误执行 observe。
        return _blocked_plan("pending_kind_not_desktop_observe_before_action")  # 新增代码+AutoObserveRecovery：返回类型不匹配原因；如果没有这一行，日志无法定位为何不恢复。
    required_tool = normalize_actionability_tool_name(str(pending.get("next_required_tool", "") or ""))  # 新增代码+AutoObserveRecovery：归一化下一步工具名；如果没有这一行，完整 MCP 名无法匹配 observe。
    if required_tool != "observe":  # 新增代码+AutoObserveRecovery：只有下一步确实是 observe 才能自动补；如果没有这一行，运行时可能合成错误工具。
        return _blocked_plan("pending_required_tool_not_observe")  # 新增代码+AutoObserveRecovery：返回工具不匹配原因；如果没有这一行，拒绝原因不稳定。
    required_action = str(pending.get("next_required_action", "") or "").strip()  # 新增代码+AutoObserveRecovery：读取 observe 的具体 action；如果没有这一行，无法确认是否安全合成 get_window_state。
    if required_action and required_action != "get_window_state":  # 新增代码+AutoObserveRecovery：只允许空 action 或窗口状态观察；如果没有这一行，未来未知 observe 动作可能被错误自动执行。
        return _blocked_plan("pending_required_action_not_get_window_state")  # 新增代码+AutoObserveRecovery：返回 action 不匹配原因；如果没有这一行，日志无法解释拒绝。
    target_ref = str(pending.get("target_ref", "") or "").strip()  # 新增代码+AutoObserveRecovery：读取目标窗口引用；如果没有这一行，多窗口恢复无法绑定正确窗口。
    if not target_ref:  # 新增代码+AutoObserveRecovery：缺少目标引用时不自动恢复；如果没有这一行，observe 可能落到错误应用或旧窗口。
        return _blocked_plan("missing_target_ref_for_desktop_observe_recovery")  # 新增代码+AutoObserveRecovery：返回缺 target_ref 原因；如果没有这一行，模型和日志不知道需要补什么。
    recovery_key = f"desktop_observe_before_action:{target_ref}"  # 新增代码+AutoObserveRecovery：按目标窗口构造计数键；如果没有这一行，一个窗口的失败会污染另一个窗口。
    max_attempts = AUTO_OBSERVE_RECOVERY_DEFAULT_MAX_ATTEMPTS  # 新增代码+AutoObserveRecovery：读取默认最大尝试次数；如果没有这一行，后续预算没有统一来源。
    if _recovery_attempt_count(runtime_state, recovery_key) >= max_attempts:  # 新增代码+AutoObserveRecovery：检查是否已经用完预算；如果没有这一行，observe 失败会自动循环。
        return _blocked_plan("auto_recovery_attempt_budget_exhausted", recovery_key=recovery_key, max_attempts=max_attempts)  # 新增代码+AutoObserveRecovery：返回预算耗尽原因；如果没有这一行，调用方无法停止重试。
    arguments = {"action": required_action or "get_window_state", "reason": "auto_recover_observe_before_action", "target_ref": target_ref}  # 新增代码+AutoObserveRecovery：构造合成 observe 参数；如果没有这一行，主循环不知道如何执行恢复。
    return ActionabilityRecoveryPlan(True, tool_name="mcp__computer-use__observe", arguments=arguments, reason="desktop_observe_before_action", recovery_key=recovery_key, max_attempts=max_attempts)  # 新增代码+AutoObserveRecovery：返回可执行恢复计划；如果没有这一行，主循环无法自动补 observe。
    # 新增代码+AutoObserveRecovery：函数段结束，build_desktop_observe_recovery_plan 到此结束；如果没有这个边界说明，用户不容易看出恢复决策范围。


def record_recovery_attempt(runtime_state: dict[str, Any] | None, recovery_plan: ActionabilityRecoveryPlan) -> None:  # 新增代码+AutoObserveRecovery：函数段开始，记录一次自动恢复尝试；如果没有这段函数，预算保护不会生效。
    if not recovery_plan.should_recover or not recovery_plan.recovery_key:  # 新增代码+AutoObserveRecovery：不可恢复计划不计数；如果没有这一行，拒绝分支也会消耗预算。
        return  # 新增代码+AutoObserveRecovery：直接退出；如果没有这一行，后续会写入空 recovery_key。
    state = _runtime_dict(runtime_state)  # 新增代码+AutoObserveRecovery：取得可写运行态；如果没有这一行，计数没有保存位置。
    attempts = state.setdefault(AUTO_OBSERVE_RECOVERY_ATTEMPTS_KEY, {})  # 新增代码+AutoObserveRecovery：取得或创建尝试次数字典；如果没有这一行，跨工具结果无法共享预算。
    if not isinstance(attempts, dict):  # 新增代码+AutoObserveRecovery：如果旧状态类型异常则重建；如果没有这一行，坏状态会导致赋值失败。
        attempts = {}  # 新增代码+AutoObserveRecovery：创建新的计数字典；如果没有这一行，无法恢复坏状态。
        state[AUTO_OBSERVE_RECOVERY_ATTEMPTS_KEY] = attempts  # 新增代码+AutoObserveRecovery：写回新的计数字典；如果没有这一行，后续读取仍会看到坏状态。
    attempts[recovery_plan.recovery_key] = int(attempts.get(recovery_plan.recovery_key, 0) or 0) + 1  # 新增代码+AutoObserveRecovery：为当前目标增加一次尝试；如果没有这一行，预算保护不会推进。
    # 新增代码+AutoObserveRecovery：函数段结束，record_recovery_attempt 到此结束；如果没有这个边界说明，用户不容易看出计数写入范围。


def clear_recovery_attempts_for_pending(runtime_state: dict[str, Any] | None, recovery_key: str) -> None:  # 新增代码+AutoObserveRecovery：函数段开始，清理某个 pending 的恢复计数；如果没有这段函数，已完成目标可能长期占用预算。
    state = _runtime_dict(runtime_state)  # 新增代码+AutoObserveRecovery：取得运行态；如果没有这一行，无法读取计数字典。
    attempts = state.get(AUTO_OBSERVE_RECOVERY_ATTEMPTS_KEY)  # 新增代码+AutoObserveRecovery：读取尝试次数字典；如果没有这一行，无法清理指定 key。
    if isinstance(attempts, dict):  # 新增代码+AutoObserveRecovery：只有字典状态才清理；如果没有这一行，异常状态会触发属性错误。
        attempts.pop(str(recovery_key or ""), None)  # 新增代码+AutoObserveRecovery：删除指定恢复计数；如果没有这一行，下一次同目标任务可能被旧预算误挡。
    # 新增代码+AutoObserveRecovery：函数段结束，clear_recovery_attempts_for_pending 到此结束；如果没有这个边界说明，用户不容易看出计数清理范围。


__all__ = [  # 新增代码+AutoObserveRecovery：公开接口清单开始；如果没有这一段，外部模块导入边界不清楚。
    "ActionabilityRecoveryPlan",  # 新增代码+AutoObserveRecovery：导出恢复计划类型；如果没有这一行，主循环和测试无法标注计划对象。
    "AUTO_OBSERVE_RECOVERY_ATTEMPTS_KEY",  # 新增代码+AutoObserveRecovery：导出尝试计数键；如果没有这一行，测试无法验证预算状态。
    "build_desktop_observe_recovery_plan",  # 新增代码+AutoObserveRecovery：导出计划构造函数；如果没有这一行，主循环无法生成自动 observe 调用。
    "clear_recovery_attempts_for_pending",  # 新增代码+AutoObserveRecovery：导出计数清理函数；如果没有这一行，后续生命周期无法清理预算。
    "record_recovery_attempt",  # 新增代码+AutoObserveRecovery：导出计数记录函数；如果没有这一行，主循环无法防止重复自动 observe。
]  # 新增代码+AutoObserveRecovery：公开接口清单结束；如果没有这一行，Python 列表语法不完整。
