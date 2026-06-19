from __future__ import annotations  # 新增代码+LayeredDesktopTaskLoopTest：启用延迟类型注解；如果没有这一行，fake 类互相引用时在旧解释器上更容易导入失败。

from typing import Any  # 新增代码+LayeredDesktopTaskLoopTest：导入动态 JSON 类型；如果没有这一行，fake runtime 的返回值边界不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import DesktopTaskPlan, StagePlan  # 新增代码+LayeredDesktopTaskLoopTest：导入通用阶段模型；如果没有这一行，测试会退回散乱字典而不能验证真实模型路径。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_task_loop import UniversalStageTaskLoop  # 新增代码+LayeredDesktopTaskLoopTest：导入真实分阶段任务循环；如果没有这一行，测试无法覆盖 planner 到 verifier 的主链路。


class FakeLayeredPlanner:  # 新增代码+LayeredDesktopTaskLoopTest：类段开始，模拟独立规划层输出通用阶段；如果没有这个 fake，测试会依赖模型或真实 prompt 解析。
    def plan(self, prompt: str, context: dict[str, Any]) -> DesktopTaskPlan:  # 新增代码+LayeredDesktopTaskLoopTest：函数段开始，返回固定但通用的桌面任务计划；如果没有这段函数，StageLoop 没有可执行计划。
        target_ref = "target-text-editor"  # 新增代码+LayeredDesktopTaskLoopTest：定义稳定目标引用；如果没有这一行，批执行器无法验证一对一窗口绑定。
        return DesktopTaskPlan(  # 新增代码+LayeredDesktopTaskLoopTest：构造真实 DesktopTaskPlan；如果没有这一行，测试无法证明模型对象能贯穿主循环。
            objective="输入 hello everyone 并保存",  # 新增代码+LayeredDesktopTaskLoopTest：写入低敏任务目标；如果没有这一行，报告缺少用户意图摘要。
            task_kind="text_entry",  # 新增代码+LayeredDesktopTaskLoopTest：声明通用文本输入任务；如果没有这一行，能力兜底和编译器无法选择文本批。
            targets=({"target_id": target_ref, "resolved_target_ref": target_ref, "capability_hint": "text_input_surface"},),  # 新增代码+LayeredDesktopTaskLoopTest：声明一个通用文本目标；如果没有这一行，目标 session 无法建立。
            resources=({"resource_kind": "file", "name": "layered-test.txt", "location_hint": "desktop"},),  # 新增代码+LayeredDesktopTaskLoopTest：声明保存资源；如果没有这一行，验证层无法知道任务包含提交资源。
            success_criteria=("requested_text_visible", "resource_commit_verified"),  # 新增代码+LayeredDesktopTaskLoopTest：声明机器可验收标准；如果没有这一行，最终验证可能只看阶段数量。
            stages=(  # 新增代码+LayeredDesktopTaskLoopTest：函数段内定义阶段列表；如果没有这一段，任务不会按启动、输入、保存、验证推进。
                StagePlan(stage_id="prepare-target", stage_kind="prepare_target", target_ref=target_ref, verifier={"fresh_resource_required": True}),  # 新增代码+LayeredDesktopTaskLoopTest：准备并绑定新目标；如果没有这一行，旧窗口接管问题不会被主循环覆盖。
                StagePlan(stage_id="probe-capability", stage_kind="probe_capabilities", target_ref=target_ref),  # 新增代码+LayeredDesktopTaskLoopTest：探测能力阶段；如果没有这一行，观察层到能力画像链路缺测试覆盖。
                StagePlan(stage_id="type-content", stage_kind="perform_content_work", target_ref=target_ref, verifier={"requested_text": "hello everyone"}),  # 新增代码+LayeredDesktopTaskLoopTest：文本输入阶段；如果没有这一行，批执行器不会生成 type_text 动作。
                StagePlan(stage_id="save-resource", stage_kind="commit_resource", target_ref=target_ref),  # 新增代码+LayeredDesktopTaskLoopTest：保存阶段；如果没有这一行，通用保存批和保存验证不会被覆盖。
                StagePlan(stage_id="verify-result", stage_kind="verify_result", target_ref=target_ref),  # 新增代码+LayeredDesktopTaskLoopTest：最终验证阶段；如果没有这一行，任务可能在未验证时被误判完成。
            ),  # 新增代码+LayeredDesktopTaskLoopTest：阶段列表结束；如果没有这一行，Python 元组语法不完整。
            prompt_signature="layered-text-entry",  # 新增代码+LayeredDesktopTaskLoopTest：写入脱敏签名；如果没有这一行，报告难以关联测试计划。
            layer_skill_metadata={"intent_understanding": {"layer_name": "intent_understanding"}, "stage_planning": {"layer_name": "stage_planning"}},  # 新增代码+LayeredDesktopTaskLoopTest：模拟分层 skill 元数据；如果没有这一行，desktop_task 外层无法验证 skill 接线透传。
        )  # 新增代码+LayeredDesktopTaskLoopTest：计划对象构造结束；如果没有这一行，Python 调用语法不完整。
    # 新增代码+LayeredDesktopTaskLoopTest：函数段结束，FakeLayeredPlanner.plan 到此结束；如果没有这个边界说明，用户不容易看出规划 fake 范围。
# 新增代码+LayeredDesktopTaskLoopTest：类段结束，FakeLayeredPlanner 到此结束；如果没有这个边界说明，用户不容易看出 fake 规划层范围。


class FakeLayeredTargetRuntime:  # 新增代码+LayeredDesktopTaskLoopTest：类段开始，模拟通用目标窗口绑定 runtime；如果没有这个 fake，测试会启动真实软件。
    def open_target_session(self, target_hint: str) -> dict[str, Any]:  # 新增代码+LayeredDesktopTaskLoopTest：函数段开始，返回 agent-owned 目标 session；如果没有这段函数，StageLoop 无法建立 target_ref。
        return {"session_ready": True, "target_identity_bound": True, "target_window_existed_before_launch": False, "target_window": {"hwnd": 101, "title_preview": "Untitled", "rect": {"width": 900, "height": 600}}}  # 新增代码+LayeredDesktopTaskLoopTest：返回新窗口身份事实；如果没有这一行，FreshTarget 和 owned_window 验证无法通过。
    # 新增代码+LayeredDesktopTaskLoopTest：函数段结束，FakeLayeredTargetRuntime.open_target_session 到此结束；如果没有这个边界说明，用户不容易看出启动 fake 范围。

    def verify_before_action(self, session: dict[str, Any], current_window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+LayeredDesktopTaskLoopTest：函数段开始，模拟批前目标复核；如果没有这段函数，批执行器无法覆盖身份门禁。
        return {"allowed": True, "target_identity_verified": True, "target_ref": session.get("target_ref", "")}  # 新增代码+LayeredDesktopTaskLoopTest：返回放行的目标身份结果；如果没有这一行，批执行会被目标复核挡住。
    # 新增代码+LayeredDesktopTaskLoopTest：函数段结束，FakeLayeredTargetRuntime.verify_before_action 到此结束；如果没有这个边界说明，用户不容易看出身份复核 fake 范围。
# 新增代码+LayeredDesktopTaskLoopTest：类段结束，FakeLayeredTargetRuntime 到此结束；如果没有这个边界说明，用户不容易看出目标 runtime fake 范围。


class FakeLayeredObservationRuntime:  # 新增代码+LayeredDesktopTaskLoopTest：类段开始，模拟结构化观察来源；如果没有这个 fake，测试需要真实截图和 UIA。
    def observe(self, target_hint: str, real_desktop_touched: bool = False, target_window: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+LayeredDesktopTaskLoopTest：函数段开始，返回通用观察帧；如果没有这段函数，StageLoop 无法构造 ObservationFacts。
        visible_text = "hello everyone" if real_desktop_touched else ""  # 新增代码+LayeredDesktopTaskLoopTest：动作后才显示请求文本；如果没有这一行，文本验证无法区分前后状态。
        return {  # 新增代码+LayeredDesktopTaskLoopTest：返回原始观察帧；如果没有这一行，观察层没有输入。
            "target_ref": target_hint,  # 新增代码+LayeredDesktopTaskLoopTest：写入目标引用；如果没有这一行，ObservationFacts 缺 active_target_ref。
            "target_identity_verified": True,  # 新增代码+LayeredDesktopTaskLoopTest：写入目标身份事实；如果没有这一行，验证层可能认为目标未绑定。
            "target_window": target_window or {"hwnd": 101, "title_preview": "Untitled", "rect": {"width": 900, "height": 600}},  # 新增代码+LayeredDesktopTaskLoopTest：写入窗口摘要；如果没有这一行，批编译器缺尺寸和标题。
            "uia_tree": [{"control_type": "Edit", "name": "Document", "bounds": {"x": 10, "y": 50, "width": 860, "height": 500}}],  # 新增代码+LayeredDesktopTaskLoopTest：提供通用可编辑区域；如果没有这一行，能力画像可能无法识别文本输入面。
            "visible_text_summary": visible_text,  # 新增代码+LayeredDesktopTaskLoopTest：提供低敏可见文本摘要；如果没有这一行，文本验证不能确认输入结果。
            "saved_resource_exists": bool(real_desktop_touched),  # 新增代码+LayeredDesktopTaskLoopTest：动作后模拟保存资源已存在；如果没有这一行，保存验证无法通过。
            "save_dialog_completed": bool(real_desktop_touched),  # 新增代码+LayeredDesktopTaskLoopTest：动作后模拟保存流程完成；如果没有这一行，commit_resource 阶段会认为保存未完成。
        }  # 新增代码+LayeredDesktopTaskLoopTest：观察帧结束；如果没有这一行，Python 字典语法不完整。
    # 新增代码+LayeredDesktopTaskLoopTest：函数段结束，FakeLayeredObservationRuntime.observe 到此结束；如果没有这个边界说明，用户不容易看出观察 fake 范围。
# 新增代码+LayeredDesktopTaskLoopTest：类段结束，FakeLayeredObservationRuntime 到此结束；如果没有这个边界说明，用户不容易看出观察 runtime fake 范围。


class FakeLayeredActionRuntime:  # 新增代码+LayeredDesktopTaskLoopTest：类段开始，模拟通用动作 DSL runtime；如果没有这个 fake，测试会触发真实 SendInput。
    def __init__(self, target_runtime: FakeLayeredTargetRuntime) -> None:  # 新增代码+LayeredDesktopTaskLoopTest：函数段开始，保存目标 runtime 供批执行器复核；如果没有这段函数，execute_batch 找不到 verify_before_action。
        self.target_runtime = target_runtime  # 新增代码+LayeredDesktopTaskLoopTest：暴露 target_runtime 给 UniversalActionBatchExecutor；如果没有这一行，身份复核只能走缺失兜底。
        self.dispatched_actions: list[dict[str, Any]] = []  # 新增代码+LayeredDesktopTaskLoopTest：记录动作列表；如果没有这一行，测试无法确认批执行真的发生。
    # 新增代码+LayeredDesktopTaskLoopTest：函数段结束，FakeLayeredActionRuntime.__init__ 到此结束；如果没有这个边界说明，用户不容易看出动作 fake 初始化范围。

    def dispatch(self, session: dict[str, Any], action: dict[str, Any], current_window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+LayeredDesktopTaskLoopTest：函数段开始，模拟 primitive 动作分发；如果没有这段函数，真实批执行器无法运行。
        self.dispatched_actions.append(dict(action))  # 新增代码+LayeredDesktopTaskLoopTest：记录动作副本；如果没有这一行，批动作是否执行不可见。
        return {"ok": True, "decision": "fake_action_dispatched", "low_level_event_count": 1}  # 新增代码+LayeredDesktopTaskLoopTest：返回成功和低层事件数；如果没有这一行，StageLoop 无法累计动作证据。
    # 新增代码+LayeredDesktopTaskLoopTest：函数段结束，FakeLayeredActionRuntime.dispatch 到此结束；如果没有这个边界说明，用户不容易看出动作 fake 范围。
# 新增代码+LayeredDesktopTaskLoopTest：类段结束，FakeLayeredActionRuntime 到此结束；如果没有这个边界说明，用户不容易看出动作 runtime fake 范围。


class FakeReflectionLayer:  # 新增代码+LayeredDesktopTaskLoopTest：类段开始，提供不会写磁盘的反思层 fake；如果没有这个 fake，成功测试也会携带真实学习层依赖。
    def reflect_stage_failure(self, stage_id: str, verifier_result: Any, observation_facts: dict[str, Any], action_result: Any) -> Any:  # 新增代码+LayeredDesktopTaskLoopTest：函数段开始，满足反思层接口；如果没有这段函数，失败路径会缺方法。
        raise AssertionError("success path should not invoke reflection")  # 新增代码+LayeredDesktopTaskLoopTest：成功路径不应触发反思；如果没有这一行，误触失败学习不会被发现。
    # 新增代码+LayeredDesktopTaskLoopTest：函数段结束，FakeReflectionLayer.reflect_stage_failure 到此结束；如果没有这个边界说明，用户不容易看出反思 fake 范围。
# 新增代码+LayeredDesktopTaskLoopTest：类段结束，FakeReflectionLayer 到此结束；如果没有这个边界说明，用户不容易看出反思 fake 范围。


def test_layered_stage_loop_completes_text_entry_with_batch_observe_verify_report() -> None:  # 新增代码+LayeredDesktopTaskLoopTest：函数段开始，验证通用分层闭环端到端完成文本任务；如果没有这段测试，planner/observer/batch/verifier 的接线可能静默断开。
    target_runtime = FakeLayeredTargetRuntime()  # 新增代码+LayeredDesktopTaskLoopTest：创建目标 runtime fake；如果没有这一行，StageLoop 无法绑定目标窗口。
    action_runtime = FakeLayeredActionRuntime(target_runtime)  # 新增代码+LayeredDesktopTaskLoopTest：创建动作 runtime fake；如果没有这一行，批执行器没有分发对象。
    loop = UniversalStageTaskLoop(  # 新增代码+LayeredDesktopTaskLoopTest：构造真实 StageLoop 并注入 fake 依赖；如果没有这一行，测试会碰真实桌面或真实模型。
        planner=FakeLayeredPlanner(),  # 新增代码+LayeredDesktopTaskLoopTest：注入规划层 fake；如果没有这一行，测试无法稳定获得五阶段计划。
        observation_runtime=FakeLayeredObservationRuntime(),  # 新增代码+LayeredDesktopTaskLoopTest：注入观察层 fake；如果没有这一行，测试需要真实屏幕事实。
        target_runtime=target_runtime,  # 新增代码+LayeredDesktopTaskLoopTest：注入目标 runtime fake；如果没有这一行，目标绑定不可控。
        action_runtime=action_runtime,  # 新增代码+LayeredDesktopTaskLoopTest：注入动作 runtime fake；如果没有这一行，批执行会调用真实动作 DSL。
        max_stage_repairs=0,  # 新增代码+LayeredDesktopTaskLoopTest：禁止修复重试；如果没有这一行，失败时测试可能隐藏第一现场。
        reflection_layer=FakeReflectionLayer(),  # 新增代码+LayeredDesktopTaskLoopTest：注入无磁盘反思层；如果没有这一行，成功测试会依赖真实学习目录。
    )  # 新增代码+LayeredDesktopTaskLoopTest：StageLoop 构造结束；如果没有这一行，Python 调用语法不完整。
    report = loop.run_desktop_task("请使用本机文本编辑软件输入 hello everyone 并保存", target_hint="text-editor")  # 新增代码+LayeredDesktopTaskLoopTest：执行通用文本桌面任务；如果没有这一行，测试没有被测行为。
    assert report["ok"] is True  # 新增代码+LayeredDesktopTaskLoopTest：断言整项任务完成；如果没有这一行，未完成任务可能被测试放过。
    assert report["universal_stage_task_loop_used"] is True  # 新增代码+LayeredDesktopTaskLoopTest：断言使用新 StageLoop；如果没有这一行，旧路径回归不会被发现。
    assert report["layered_observation_facts_used"] is True  # 新增代码+LayeredDesktopTaskLoopTest：断言观察 facts 层参与；如果没有这一行，观察准确率改造可能被绕过。
    assert report["reflection_learning_layer_used"] is True  # 新增代码+LayeredDesktopTaskLoopTest：断言报告暴露反思层接线；如果没有这一行，失败学习闭环不可见。
    assert report["stage_count"] == 5  # 新增代码+LayeredDesktopTaskLoopTest：断言五个通用阶段全部进入计划；如果没有这一行，任务可能被过度简化。
    assert report["completed_stage_count"] == 5  # 新增代码+LayeredDesktopTaskLoopTest：断言所有阶段完成；如果没有这一行，部分完成可能被误判成功。
    assert report["batch_execution_used"] is True  # 新增代码+LayeredDesktopTaskLoopTest：断言批执行启用；如果没有这一行，系统可能退回每步模型循环。
    assert report["low_level_event_count"] > 0  # 新增代码+LayeredDesktopTaskLoopTest：断言产生低层事件证据；如果没有这一行，口头成功无法被区分。
    assert report["desktop_task_plan"]["layer_skill_metadata"]["intent_understanding"]["layer_name"] == "intent_understanding"  # 新增代码+LayeredDesktopTaskLoopTest：断言分层 skill 元数据透传；如果没有这一行，独立 prompt/skill 接线断裂不可见。
    assert any(action.get("type") == "type_text" for action in action_runtime.dispatched_actions)  # 新增代码+LayeredDesktopTaskLoopTest：断言文本输入动作真正被批执行；如果没有这一行，计划完成可能没有实际输入动作。
    assert any(result["stage_id"] == "verify-result" and result["status"] == "completed" for result in report["stage_results"])  # 新增代码+LayeredDesktopTaskLoopTest：断言最终验证阶段完成；如果没有这一行，任务可能未验证就结束。
# 新增代码+LayeredDesktopTaskLoopTest：函数段结束，test_layered_stage_loop_completes_text_entry_with_batch_observe_verify_report 到此结束；如果没有这个边界说明，用户不容易看出端到端测试范围。
