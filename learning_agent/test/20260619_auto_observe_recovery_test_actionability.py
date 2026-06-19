"""Computer Use 自动 observe 恢复的纯状态测试。"""  # 新增代码+AutoObserveRecovery：说明本测试文件只验证运行时恢复决策；如果没有这一行，读者不知道这些测试为什么不打开真实桌面。
from __future__ import annotations  # 新增代码+AutoObserveRecovery：延迟解析类型注解；如果没有这一行，后续类型写法在旧运行方式下更容易受导入顺序影响。

from learning_agent.core.actionability_recovery import build_desktop_observe_recovery_plan, record_recovery_attempt  # 新增代码+AutoObserveRecovery：导入待实现的恢复决策入口；如果没有这一行，测试无法证明 observe-before-action 会被运行时接管。
from learning_agent.core.actionability_state import ACTIONABILITY_LAST_BLOCK_KEY, DESKTOP_ACTION_REQUIRED_MARKER, DESKTOP_USER_ACTION_REQUIRED_MARKER  # 新增代码+AutoObserveRecovery：导入稳定协议常量；如果没有这一行，测试会手写脆弱字符串。


def _desktop_observe_required_pending() -> dict[str, str]:  # 新增代码+AutoObserveRecovery：函数段开始，构造桌面动作前必须 observe 的 pending；如果没有这段函数，多个测试会重复协议字段。
    return {  # 新增代码+AutoObserveRecovery：返回 pending 字典；如果没有这一行，调用方拿不到可复用状态。
        "marker": DESKTOP_ACTION_REQUIRED_MARKER,  # 新增代码+AutoObserveRecovery：声明这是桌面动作要求 marker；如果没有这一行，恢复层无法确认来源是桌面协议。
        "actionability_kind": "desktop_observe_before_action",  # 新增代码+AutoObserveRecovery：声明必须先观察再动作；如果没有这一行，恢复层无法区分其他 pending。
        "next_required_tool": "mcp__computer-use__observe",  # 新增代码+AutoObserveRecovery：声明下一步工具是 observe；如果没有这一行，恢复层不知道该合成哪个工具调用。
        "next_required_action": "get_window_state",  # 新增代码+AutoObserveRecovery：声明 observe 的具体动作；如果没有这一行，恢复层可能生成过宽泛的观察调用。
        "target_ref": "cu-target-test-0001",  # 新增代码+AutoObserveRecovery：保存目标窗口引用；如果没有这一行，多窗口场景可能观察错窗口。
        "low_level_event_count": "0",  # 新增代码+AutoObserveRecovery：保存拒绝路径的零事件证据；如果没有这一行，测试不能证明恢复前没有污染桌面。
    }  # 新增代码+AutoObserveRecovery：pending 字典结束；如果没有这一行，Python 字典语法不完整。
    # 新增代码+AutoObserveRecovery：函数段结束，_desktop_observe_required_pending 到此结束；如果没有这个边界说明，用户不容易看出 helper 范围。


def test_desktop_observe_required_pending_builds_recovery_plan() -> None:  # 新增代码+AutoObserveRecovery：函数段开始，验证 observe-before-action 会生成自动恢复计划；如果没有这段测试，运行时可能继续依赖模型自觉调用 observe。
    runtime_state: dict[str, object] = {}  # 新增代码+AutoObserveRecovery：准备空运行态；如果没有这一行，恢复层没有地方读取尝试次数。
    plan = build_desktop_observe_recovery_plan(_desktop_observe_required_pending(), runtime_state)  # 新增代码+AutoObserveRecovery：请求恢复计划；如果没有这一行，测试无法触发待实现逻辑。
    assert plan.should_recover is True  # 新增代码+AutoObserveRecovery：确认应该自动恢复；如果没有这一行，测试不能捕捉模型重试循环问题。
    assert plan.tool_name == "mcp__computer-use__observe"  # 新增代码+AutoObserveRecovery：确认合成工具是 MCP observe；如果没有这一行，主循环可能生成错误工具名。
    assert plan.arguments["action"] == "get_window_state"  # 新增代码+AutoObserveRecovery：确认观察动作是窗口状态；如果没有这一行，恢复可能拿不到必要截图和窗口证据。
    assert plan.arguments["target_ref"] == "cu-target-test-0001"  # 新增代码+AutoObserveRecovery：确认目标窗口引用被保留；如果没有这一行，多应用任务会丢失一对一绑定。
    assert plan.arguments["reason"] == "auto_recover_observe_before_action"  # 新增代码+AutoObserveRecovery：确认恢复原因可审计；如果没有这一行，日志难以说明 observe 是运行时自动补的。
    assert plan.recovery_key == "desktop_observe_before_action:cu-target-test-0001"  # 新增代码+AutoObserveRecovery：确认尝试计数键稳定；如果没有这一行，重复保护可能跨目标互相污染。
    assert plan.max_attempts == 1  # 新增代码+AutoObserveRecovery：确认默认只自动补一次；如果没有这一行，observe 失败可能变成无限循环。
    # 新增代码+AutoObserveRecovery：函数段结束，test_desktop_observe_required_pending_builds_recovery_plan 到此结束；如果没有这个边界说明，用户不容易看出成功路径断言范围。


def test_user_action_required_block_disables_auto_recovery() -> None:  # 新增代码+AutoObserveRecovery：函数段开始，验证用户动作阻断不会被自动 observe 绕过；如果没有这段测试，旧窗口拒绝可能又被运行时继续工具化。
    runtime_state: dict[str, object] = {ACTIONABILITY_LAST_BLOCK_KEY: {"marker": DESKTOP_USER_ACTION_REQUIRED_MARKER, "block_class": "user_action_required"}}  # 新增代码+AutoObserveRecovery：模拟 FreshTarget 要求用户介入；如果没有这一行，恢复层无法区分硬停止和可自动观察。
    plan = build_desktop_observe_recovery_plan(_desktop_observe_required_pending(), runtime_state)  # 新增代码+AutoObserveRecovery：在用户阻断态下请求恢复计划；如果没有这一行，测试无法证明硬停止优先级。
    assert plan.should_recover is False  # 新增代码+AutoObserveRecovery：确认不会自动恢复；如果没有这一行，运行时可能继续接管旧窗口。
    assert plan.reason == "user_action_required_block_active"  # 新增代码+AutoObserveRecovery：确认拒绝原因稳定；如果没有这一行，调试日志很难判断为什么没有恢复。
    # 新增代码+AutoObserveRecovery：函数段结束，test_user_action_required_block_disables_auto_recovery 到此结束；如果没有这个边界说明，用户不容易看出阻断路径范围。


def test_recovery_attempt_budget_stops_repeated_auto_observe() -> None:  # 新增代码+AutoObserveRecovery：函数段开始，验证自动 observe 有尝试预算；如果没有这段测试，复杂任务里 observe 失败会循环。
    runtime_state: dict[str, object] = {}  # 新增代码+AutoObserveRecovery：准备空运行态；如果没有这一行，测试没有地方保存尝试计数。
    pending = _desktop_observe_required_pending()  # 新增代码+AutoObserveRecovery：准备同一个 pending；如果没有这一行，后续两次计划可能不是同一个恢复目标。
    first_plan = build_desktop_observe_recovery_plan(pending, runtime_state)  # 新增代码+AutoObserveRecovery：第一次请求恢复计划；如果没有这一行，无法获得计数键。
    record_recovery_attempt(runtime_state, first_plan)  # 新增代码+AutoObserveRecovery：记录已经自动恢复过一次；如果没有这一行，第二次不会触发预算限制。
    second_plan = build_desktop_observe_recovery_plan(pending, runtime_state)  # 新增代码+AutoObserveRecovery：第二次请求同一恢复计划；如果没有这一行，测试无法覆盖重复保护。
    assert first_plan.should_recover is True  # 新增代码+AutoObserveRecovery：确认第一次允许恢复；如果没有这一行，测试可能只证明永远不恢复。
    assert second_plan.should_recover is False  # 新增代码+AutoObserveRecovery：确认第二次被预算拦住；如果没有这一行，自动恢复可能无限重试。
    assert second_plan.reason == "auto_recovery_attempt_budget_exhausted"  # 新增代码+AutoObserveRecovery：确认预算耗尽原因稳定；如果没有这一行，acceptance 日志难以统计循环保护。
    # 新增代码+AutoObserveRecovery：函数段结束，test_recovery_attempt_budget_stops_repeated_auto_observe 到此结束；如果没有这个边界说明，用户不容易看出预算测试范围。
