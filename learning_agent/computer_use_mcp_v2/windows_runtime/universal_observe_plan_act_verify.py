"""URG-4 universal observe-plan-act-verify loop runtime."""  # 新增代码+URG4ObservePlanActVerify：说明本模块负责把观察、目标身份、动作 DSL 和验证器组合成一个通用闭环；如果没有这行代码，读者不容易知道 URG-4 的入口在哪里。
from __future__ import annotations  # 新增代码+URG4ObservePlanActVerify：启用延迟类型解析；如果没有这行代码，旧入口在读取前向类型标注时更容易导入失败。
import json  # 新增代码+URG4ObservePlanActVerify：导入 JSON 用于 CLI 输出结构化报告；如果没有这行代码，真实终端失败时不方便复盘字段。
from typing import Any  # 新增代码+URG4ObservePlanActVerify：导入 Any 描述动态任务、观察帧和动作报告；如果没有这行代码，注入式接口边界不清楚。
try:  # 新增代码+URG4ObservePlanActVerify：优先按 learning_agent 包路径导入已完成的 URG-1/3 能力；如果没有这段代码，单测和真实 bat 入口无法共享实现。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_action_dsl import UniversalActionDslRuntime, run_phase118_universal_action_dsl_contract  # 新增代码+URG4ObservePlanActVerify：导入 URG-3 动作 DSL 和安全合同；如果没有这行代码，闭环会绕过已验收的动作桥。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_real_observation import UniversalRealObservationFrameRuntime  # 新增代码+URG4ObservePlanActVerify：导入 URG-1 ObservationFrame runtime 类型；如果没有这行代码，闭环和观察帧之间没有明确组合关系。
    from learning_agent.computer_use_mcp_v2.windows_runtime.visual_semantic_planner import phase122_plan_visual_semantic_task  # 新增代码+VisualSemanticPlanner：导入语义视觉规划入口；如果没有这一行，Phase120 planner 仍无法把 house 等意图变成屋顶墙体门窗 primitive。
    from learning_agent.computer_use_mcp_v2.windows_runtime.natural_language_semantic_planner import phase123_plan_semantic_desktop_task  # 新增代码+GenericSemanticPlanner：导入通用自然语言语义规划入口；如果没有这一行，非绘图任务会继续被误塞进视觉画线 planner。
except ModuleNotFoundError as error:  # 新增代码+URG4ObservePlanActVerify：兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这段代码，真实可见终端可能因包前缀失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_action_dsl", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_real_observation", "learning_agent.computer_use_mcp_v2.windows_runtime.visual_semantic_planner", "learning_agent.computer_use_mcp_v2.windows_runtime.natural_language_semantic_planner"}:  # 修改代码+GenericSemanticPlanner：只兜底包路径缺失并允许脚本模式导入通用语义 planner；如果没有这一行，bat 入口可能因为新模块包前缀无法启动。
        raise  # 新增代码+URG4ObservePlanActVerify：重新抛出非路径类导入错误；如果没有这行代码，排查真实依赖问题会变困难。
    from computer_use_mcp_v2.windows_runtime.universal_action_dsl import UniversalActionDslRuntime, run_phase118_universal_action_dsl_contract  # type: ignore  # 新增代码+URG4ObservePlanActVerify：脚本模式导入 URG-3 动作桥；如果没有这行代码，bat 入口无法执行闭环。
    from computer_use_mcp_v2.windows_runtime.universal_real_observation import UniversalRealObservationFrameRuntime  # type: ignore  # 新增代码+URG4ObservePlanActVerify：脚本模式导入 URG-1 观察帧类型；如果没有这行代码，bat 入口缺少观察层引用。
    from computer_use_mcp_v2.windows_runtime.visual_semantic_planner import phase122_plan_visual_semantic_task  # type: ignore  # 新增代码+VisualSemanticPlanner：脚本模式导入语义视觉规划入口；如果没有这一行，真实终端入口不会使用 house primitive。
    from computer_use_mcp_v2.windows_runtime.natural_language_semantic_planner import phase123_plan_semantic_desktop_task  # type: ignore  # 新增代码+GenericSemanticPlanner：脚本模式导入通用自然语言语义规划入口；如果没有这一行，真实终端入口无法处理打开应用等非绘图任务。

PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MARKER = "PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_READY"  # 新增代码+URG4ObservePlanActVerify：定义 URG-4 ready marker；如果没有这行代码，可见终端验收没有稳定等待锚点。
PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_OK_TOKEN = "PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_OK"  # 新增代码+URG4ObservePlanActVerify：定义 URG-4 OK token；如果没有这行代码，验收器无法区分成功输出和普通日志。
PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MODEL = "phase119_universal_observe_plan_act_verify_loop"  # 新增代码+URG4ObservePlanActVerify：定义闭环协议模型名；如果没有这行代码，后续矩阵无法识别 URG-4 实现版本。
PHASE120_VISUAL_TASK_PLANNER_MODEL = "phase120_visual_task_planner"  # 新增代码+VisualPlannerLoop：定义视觉任务规划器模型名；如果没有这一行，终端和矩阵无法区分新视觉规划器与旧静态动作复制器。
PHASE119_REAL_DISPATCH_PERFORMED = False  # 新增代码+URG4ObservePlanActVerify：声明合同默认不触碰真实桌面；如果没有这行代码，单测可能被误解为会真实移动鼠标键盘。


def _phase119_bool_token(value: Any) -> str:  # 新增代码+URG4ObservePlanActVerify：函数段开始，把布尔值转成固定小写 token；如果没有这段函数，CLI 可能混用 True 和 true。
    return "true" if bool(value) else "false"  # 新增代码+URG4ObservePlanActVerify：返回验收器容易匹配的小写布尔文本；如果没有这行代码，场景断言可能因大小写失败。
# 新增代码+URG4ObservePlanActVerify：函数段结束，_phase119_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出 token 格式化范围。


def _phase119_safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase8RealDesktopClosure：函数段开始，把 loop 输出里的动态字段安全整理为字典；如果没有这段函数，坏证据可能让 Phase 8 builder 直接崩溃。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase8RealDesktopClosure：只复制字典输入；如果没有这一行，外部传入的原始对象可能被后续逻辑污染。
# 新增代码+Phase8RealDesktopClosure：函数段结束，_phase119_safe_dict 到此结束；如果没有这个边界说明，初学者不容易看出字典清洗范围。


def _phase119_safe_int(value: Any) -> int:  # 新增代码+Phase8RealDesktopClosure：函数段开始，把 loop 里的事件数量安全转成整数；如果没有这段函数，字符串或空值会破坏证据转换。
    try:  # 新增代码+Phase8RealDesktopClosure：尝试按整数解释输入；如果没有这一行，JSON 字符串数字不能自然进入门禁。
        return int(value or 0)  # 新增代码+Phase8RealDesktopClosure：返回标准整数；如果没有这一行，低层事件数量不能被最终矩阵稳定读取。
    except (TypeError, ValueError):  # 新增代码+Phase8RealDesktopClosure：捕获坏类型和值错误；如果没有这一行，坏证据会变成异常而不是失败证据。
        return 0  # 新增代码+Phase8RealDesktopClosure：坏值按 0 个事件处理；如果没有这一行，损坏证据可能绕过低层事件门槛。
# 新增代码+Phase8RealDesktopClosure：函数段结束，_phase119_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出数字清洗范围。


def _phase119_latest_attempt(loop_result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase8RealDesktopClosure：函数段开始，从 loop 报告取最后一次尝试；如果没有这段函数，重试场景会难以确定最终证据来源。
    attempts = [dict(attempt) for attempt in list(loop_result.get("attempts", []) or []) if isinstance(attempt, dict)]  # 新增代码+Phase8RealDesktopClosure：复制并过滤尝试列表；如果没有这一行，坏 attempt 会污染证据转换。
    return attempts[-1] if attempts else {}  # 新增代码+Phase8RealDesktopClosure：返回最后一次尝试或空字典；如果没有这一行，空 attempts 会导致索引错误。
# 新增代码+Phase8RealDesktopClosure：函数段结束，_phase119_latest_attempt 到此结束；如果没有这个边界说明，初学者不容易看出尝试选择范围。


def _phase119_latest_step(attempt: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase8RealDesktopClosure：函数段开始，从一次尝试里取最后一个动作步骤；如果没有这段函数，多动作场景无法提取最终派发证据。
    steps = [dict(step) for step in list(attempt.get("steps", []) or []) if isinstance(step, dict)]  # 新增代码+Phase8RealDesktopClosure：复制并过滤步骤列表；如果没有这一行，坏 step 会让 builder 崩溃。
    return steps[-1] if steps else {}  # 新增代码+Phase8RealDesktopClosure：返回最后一步或空字典；如果没有这一行，空步骤会导致索引错误。
# 新增代码+Phase8RealDesktopClosure：函数段结束，_phase119_latest_step 到此结束；如果没有这个边界说明，初学者不容易看出动作步骤选择范围。


def _phase119_frame_to_phase8_observation(frame: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase8RealDesktopClosure：函数段开始，把 ObservationFrame 压缩成 Phase 8 证据字段；如果没有这段函数，最终矩阵要理解太多内部观察字段。
    return {"screenshot_captured": bool(frame.get("screenshot_captured") or frame.get("screenshot_observation") or frame.get("real_screenshot_pipeline_used")), "uia_tree_observation": bool(frame.get("uia_tree_observation") or frame.get("real_uia_provider_used") or frame.get("uia_or_vision_targeting")), "window_state_observation": bool(frame.get("window_state_observation") or frame.get("real_window_inventory")), "state_changed_after_action": bool(frame.get("state_changed_after_action") or frame.get("canvas_changed") or frame.get("real_desktop_touched"))}  # 新增代码+Phase8RealDesktopClosure：返回最终矩阵需要的观察摘要；如果没有这一行，before/after 证据格式会漂移。
# 新增代码+Phase8RealDesktopClosure：函数段结束，_phase119_frame_to_phase8_observation 到此结束；如果没有这个边界说明，初学者不容易看出观察字段映射范围。


def build_real_desktop_closure_evidence_from_loop_result(loop_result: dict[str, Any], representative_acceptance: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase8RealDesktopClosure：函数段开始，把通用 loop 报告转换成最终矩阵可校验的真实桌面闭环证据；如果没有这段函数，真实终端验收只能手写拼接证据。
    safe_result = _phase119_safe_dict(loop_result)  # 新增代码+Phase8RealDesktopClosure：清洗 loop 报告；如果没有这一行，None 或坏类型会导致转换崩溃。
    attempt = _phase119_latest_attempt(safe_result)  # 新增代码+Phase8RealDesktopClosure：提取最终尝试；如果没有这一行，重试后的最终结果无法被优先使用。
    step = _phase119_latest_step(attempt)  # 新增代码+Phase8RealDesktopClosure：提取最终动作步骤；如果没有这一行，真实派发证据没有稳定来源。
    before_frame = _phase119_safe_dict(step.get("before_observation") or attempt.get("before_observation"))  # 新增代码+Phase8RealDesktopClosure：读取动作前观察帧；如果没有这一行，证据缺少 observe 阶段。
    after_frame = _phase119_safe_dict(step.get("after_observation") or attempt.get("after_observation"))  # 新增代码+Phase8RealDesktopClosure：读取动作后观察帧；如果没有这一行，证据缺少 after-observe 阶段。
    dispatch = _phase119_safe_dict(step.get("dispatch"))  # 新增代码+Phase8RealDesktopClosure：读取动作派发报告；如果没有这一行，SendInput 证据无法进入最终矩阵。
    sender_report = _phase119_safe_dict(dispatch.get("sender"))  # 新增代码+Phase8RealDesktopClosure：读取 sender 内层报告；如果没有这一行，真实 Windows sender 的字段可能被埋掉。
    cleanup = _phase119_safe_dict(safe_result.get("cleanup"))  # 新增代码+Phase8RealDesktopClosure：读取清理报告；如果没有这一行，真实闭环缺少 cleanup 阶段。
    verification = _phase119_safe_dict(attempt.get("verification"))  # 新增代码+Phase8RealDesktopClosure：读取 verifier 报告；如果没有这一行，最终矩阵不知道 loop 为什么判定成功。
    target_window = _phase119_safe_dict(after_frame.get("target_window") or before_frame.get("target_window") or safe_result.get("session", {}).get("target_window") if isinstance(safe_result.get("session", {}), dict) else {})  # 新增代码+Phase8RealDesktopClosure：优先从观察帧提取目标窗口身份；如果没有这一行，动作证据无法绑定到窗口。
    low_level_event_count = max(_phase119_safe_int(dispatch.get("low_level_event_count")), _phase119_safe_int(sender_report.get("low_level_event_count")), _phase119_safe_int(safe_result.get("low_level_event_count")))  # 新增代码+Phase8RealDesktopClosure：汇总低层事件数量；如果没有这一行，真实 sender 返回事件数时可能被漏掉。
    sender_kind = str(dispatch.get("sender_kind") or sender_report.get("sender") or sender_report.get("backend") or "").strip().lower()  # 新增代码+Phase8RealDesktopClosure：读取 sender 类型；如果没有这一行，最终矩阵无法区分 windows_sendinput 和 recording。
    sender_kind = "windows_sendinput" if sender_kind == "windows_sendinput_low_level" else sender_kind  # 新增代码+Phase8RealDesktopClosure：把底层 Windows sender 名称归一成矩阵稳定值；如果没有这一行，测试和终端 token 容易漂移。
    physical_desktop_dispatch_performed = bool(dispatch.get("physical_desktop_dispatch_performed") or dispatch.get("real_dispatch_performed") or dispatch.get("real_desktop_touched") or sender_report.get("physical_desktop_dispatch_performed") or sender_report.get("real_dispatch_performed") or sender_report.get("real_desktop_touched") or safe_result.get("real_dispatch_performed") or safe_result.get("real_desktop_touched"))  # 新增代码+Phase8RealDesktopClosure：汇总真实物理派发事实；如果没有这一行，真实 SendInput 已发生也可能被转换成 false。
    return {"target_identity": {"window_id": str(target_window.get("window_id") or target_window.get("hwnd") or ""), "process_name": str(target_window.get("process_name") or target_window.get("app_id") or ""), "title_preview": str(target_window.get("title_preview") or target_window.get("title") or "")}, "before_observation": _phase119_frame_to_phase8_observation(before_frame), "action": {"physical_desktop_dispatch_performed": physical_desktop_dispatch_performed, "real_sendinput_dispatch": bool(physical_desktop_dispatch_performed), "sender_kind": sender_kind, "low_level_event_count": low_level_event_count}, "after_observation": _phase119_frame_to_phase8_observation(after_frame), "verification": {"verified": bool(verification.get("verified") or safe_result.get("ok")), "decision": str(verification.get("decision") or safe_result.get("decision") or "verified"), "reason": str(verification.get("reason") or "converted_from_universal_loop_result")}, "cleanup": {"cleanup_completed": bool(cleanup.get("cleanup_completed")), "host_hidden_or_restored": bool(cleanup.get("host_hidden_or_restored")), "lock_released": bool(cleanup.get("lock_released"))}, "representative_acceptance": dict(representative_acceptance or {}), "target_identity_rechecked_before_each_action": bool(safe_result.get("target_identity_rechecked_before_each_action", True)), "script_artifact_route_blocked": bool(safe_result.get("script_artifact_route_blocked", True)), "uncontrolled_high_risk_actions_allowed": bool(safe_result.get("uncontrolled_high_risk_actions_allowed", False))}  # 新增代码+Phase8RealDesktopClosure：返回最终矩阵可消费的证据对象；如果没有这一行，真实 loop 结果无法接到 Layer A。
# 新增代码+Phase8RealDesktopClosure：函数段结束，build_real_desktop_closure_evidence_from_loop_result 到此结束；如果没有这个边界说明，初学者不容易看出 Phase 8 接线范围。


def _phase119_sample_candidates(target: str) -> list[dict[str, Any]]:  # 新增代码+URG4ObservePlanActVerify：函数段开始，为代表样本构造通用发现候选；如果没有这段函数，合同会依赖本机真实安装状态。
    safe_target = str(target or "target").strip() or "target"  # 新增代码+URG4ObservePlanActVerify：清理目标名并提供兜底值；如果没有这行代码，空目标会生成坏候选。
    return [{"display_name": safe_target, "executable": f"{safe_target}.exe", "source": "phase119_representative_candidate", "installed_app_verified": True}]  # 新增代码+URG4ObservePlanActVerify：返回 Phase108/117 可消费的候选；如果没有这行代码，目标 session 无法稳定建立。
# 新增代码+URG4ObservePlanActVerify：函数段结束，_phase119_sample_candidates 到此结束；如果没有这个边界说明，初学者不容易看出样本候选范围。


class Phase119RecordingObservationRuntime:  # 新增代码+URG4ObservePlanActVerify：类段开始，提供安全记录型观察帧 runtime；如果没有这个类，合同自检会触碰真实屏幕状态。
    def __init__(self) -> None:  # 新增代码+URG4ObservePlanActVerify：函数段开始，初始化观察序号；如果没有这段函数，前后观察无法证明顺序。
        self.sequence = 0  # 新增代码+URG4ObservePlanActVerify：保存观察帧递增序号；如果没有这行代码，before/after 观察可能无法区分。
    # 新增代码+URG4ObservePlanActVerify：函数段结束，Phase119RecordingObservationRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def observe(self, target_hint: str = "", real_desktop_touched: bool = False, target_window: dict[str, Any] | None = None) -> dict[str, Any]:  # 修改代码+BoundObservationTarget：函数段开始，生成兼容 URG-1 的安全观察帧并接受绑定窗口；如果没有 target_window 参数，真实 loop 无法把 agent-owned 目标交给观察层。
        self.sequence += 1  # 新增代码+URG4ObservePlanActVerify：推进观察序号；如果没有这行代码，动作前后观察会看起来像同一帧。
        target = str(target_hint or "sample").strip() or "sample"  # 新增代码+URG4ObservePlanActVerify：清理目标提示词；如果没有这行代码，报告可能出现空目标。
        window = dict(target_window or {})  # 新增代码+BoundObservationTarget：优先使用 loop 传来的已绑定目标窗口；如果没有这一行，记录型观察也会重新生成窗口造成测试无法覆盖绑定语义。
        if not window:  # 新增代码+BoundObservationTarget：没有绑定窗口时才走旧录制兜底；如果没有这一行，合同样本会缺少默认窗口。
            window = {"app_id": f"{target}.exe", "window_id": f"phase119-window-{self.sequence}", "title_preview": f"Phase119 {target} Window", "rect": {"left": 10, "top": 20, "right": 610, "bottom": 420, "width": 600, "height": 400}}  # 修改代码+BoundObservationTarget：构造通用窗口摘要；如果没有这行代码，未绑定观察帧缺少目标窗口身份。
        return {"model": PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MODEL, "real_observation_frame": True, "frame_sequence": self.sequence, "target_hint": target, "target_window": window, "target_window_identity_present": True, "real_window_inventory": True, "screenshot_observation": True, "uia_tree_observation": True, "window_state_observation": True, "uia_or_vision_targeting": True, "screenshot_artifact_openable": True, "pixel_guard_passed": True, "raw_text_included": False, "actions_expanded": False, "real_desktop_touched": bool(real_desktop_touched), "low_level_event_count": 0}  # 修改代码+BoundObservationTarget：返回包含绑定窗口的安全观察帧；如果没有这行代码，planner 和 verifier 可能基于错误窗口输入。
    # 新增代码+URG4ObservePlanActVerify：函数段结束，Phase119RecordingObservationRuntime.observe 到此结束；如果没有这个边界说明，初学者不容易看出观察范围。
# 新增代码+URG4ObservePlanActVerify：类段结束，Phase119RecordingObservationRuntime 到此结束；如果没有这个边界说明，初学者不容易看出 fake 观察 runtime 范围。


class Phase119GenericPlanner:  # 新增代码+URG4ObservePlanActVerify：类段开始，定义不依赖具体应用 controller 的通用 planner；如果没有这个类，闭环容易退回硬编码执行列表。
    def plan(self, task: dict[str, Any], observation_frame: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+URG4ObservePlanActVerify：函数段开始，根据任务和观察帧返回 DSL 动作；如果没有这段函数，observe 和 act 之间没有规划边界。
        _ = observation_frame  # 新增代码+URG4ObservePlanActVerify：保留观察帧参数以表明 planner 以后按观察决策；如果没有这行代码，读者会以为观察帧没有被纳入接口。
        actions = task.get("actions", [])  # 新增代码+URG4ObservePlanActVerify：读取任务提供的通用 DSL 动作；如果没有这行代码，代表样本无法表达不同任务意图。
        return [dict(action) for action in list(actions or []) if isinstance(action, dict)]  # 新增代码+URG4ObservePlanActVerify：复制并过滤动作列表；如果没有这行代码，坏动作或外部可变对象可能污染闭环。
    # 新增代码+URG4ObservePlanActVerify：函数段结束，Phase119GenericPlanner.plan 到此结束；如果没有这个边界说明，初学者不容易看出规划范围。
# 新增代码+URG4ObservePlanActVerify：类段结束，Phase119GenericPlanner 到此结束；如果没有这个边界说明，初学者不容易看出 planner 范围。


def _phase120_visual_planner_safe_int(value: Any, default: int) -> int:  # 新增代码+VisualPlannerLoop：函数段开始，把观察帧里的尺寸字段安全转成整数；如果没有这段函数，坏观察帧会让视觉规划器直接崩溃。
    try:  # 新增代码+VisualPlannerLoop：尝试执行整数转换；如果没有这一行，字符串数字和整数无法被统一处理。
        return int(value)  # 新增代码+VisualPlannerLoop：返回转换后的整数；如果没有这一行，后续坐标计算没有可用数值。
    except (TypeError, ValueError):  # 新增代码+VisualPlannerLoop：捕获空值或非数字文本；如果没有这一行，单个坏字段会中断整个桌面任务。
        return int(default)  # 新增代码+VisualPlannerLoop：坏值时返回兜底尺寸；如果没有这一行，planner 无法继续生成保守动作。
# 新增代码+VisualPlannerLoop：函数段结束，_phase120_visual_planner_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出数值兜底范围。


def _phase120_visual_planner_seed(signature: str) -> int:  # 新增代码+VisualPlannerLoop：函数段开始，从脱敏 prompt 签名生成稳定种子；如果没有这段函数，不同用户意图无法影响规划形状。
    cleaned = str(signature or "visual-task").strip() or "visual-task"  # 新增代码+VisualPlannerLoop：清理签名并提供兜底；如果没有这一行，空签名会导致所有任务退化成同一形状。
    return sum((index + 1) * ord(character) for index, character in enumerate(cleaned))  # 新增代码+VisualPlannerLoop：用字符位置和字符码生成稳定整数；如果没有这一行，planner 无法在不保留原文的前提下产生差异化动作。
# 新增代码+VisualPlannerLoop：函数段结束，_phase120_visual_planner_seed 到此结束；如果没有这个边界说明，初学者不容易看出脱敏种子的来源。


def _phase120_visual_planner_dimension(rect: dict[str, Any], size_key: str, start_key: str, end_key: str, default: int) -> int:  # 新增代码+VisualPlannerCanvas：函数段开始，从 width/height 或 left/right 边界推导窗口尺寸；如果没有这段函数，真实 observation 只有边界字段时会退回错误默认尺寸。
    explicit_size = _phase120_visual_planner_safe_int(rect.get(size_key), 0)  # 新增代码+VisualPlannerCanvas：优先读取显式 width/height；如果没有这一行，记录型 observation 的标准尺寸字段会被忽略。
    if explicit_size > 0:  # 新增代码+VisualPlannerCanvas：检查显式尺寸是否有效；如果没有这一行，0 或坏值可能被当成真实尺寸。
        return explicit_size  # 新增代码+VisualPlannerCanvas：返回显式尺寸；如果没有这一行，已有安全观察帧会被不必要地重新推导。
    start = _phase120_visual_planner_safe_int(rect.get(start_key), 0)  # 新增代码+VisualPlannerCanvas：读取左/上边界；如果没有这一行，无法从真实窗口 rect 推导尺寸。
    end = _phase120_visual_planner_safe_int(rect.get(end_key), 0)  # 新增代码+VisualPlannerCanvas：读取右/下边界；如果没有这一行，无法知道窗口跨度。
    inferred_size = end - start  # 新增代码+VisualPlannerCanvas：用边界差计算尺寸；如果没有这一行，真实 Paint 窗口会继续使用 900x620 兜底。
    return inferred_size if inferred_size > 0 else int(default)  # 新增代码+VisualPlannerCanvas：返回有效推导尺寸或默认值；如果没有这一行，坏 rect 会让后续坐标计算失去兜底。
# 新增代码+VisualPlannerCanvas：函数段结束，_phase120_visual_planner_dimension 到此结束；如果没有这个边界说明，初学者不容易看出尺寸推导范围。


class Phase120VisualTaskPlanner(Phase119GenericPlanner):  # 新增代码+VisualPlannerLoop：类段开始，定义接入通用 loop 的视觉任务规划器；如果没有这个类，自然语言绘图仍只能靠静态 actions 或对象特例。
    model = PHASE120_VISUAL_TASK_PLANNER_MODEL  # 新增代码+VisualPlannerLoop：暴露稳定模型名；如果没有这一行，报告无法追踪当前使用的是哪一代 planner。
    visual_planner = True  # 新增代码+VisualPlannerLoop：标记本类是视觉规划器；如果没有这一行，loop 无法在报告里区分通用复制 planner 和视觉 planner。

    def plan(self, task: dict[str, Any], observation_frame: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+VisualPlannerLoop：函数段开始，根据自然语言视觉任务和观察帧生成可执行动作；如果没有这段函数，observe 到 act 之间仍没有真实规划。
        static_actions = super().plan(task, observation_frame)  # 新增代码+VisualPlannerLoop：先读取显式静态 actions 以兼容旧合同样本；如果没有这一行，已有 Notepad/Calculator 合同会被新 planner 破坏。
        generic_semantic_actions = phase123_plan_semantic_desktop_task(task, observation_frame, self.model)  # 新增代码+GenericSemanticPlanner：优先让通用语义 planner 处理打开应用、浏览器、泛化 GUI 等非绘图意图；如果没有这一行，所有自然语言任务都会继续被画线 fallback 污染。
        if generic_semantic_actions:  # 新增代码+GenericSemanticPlanner：检查通用语义 planner 是否已经产出动作；如果没有这一行，open_app 这类任务仍可能继续掉到绘图分支。
            return generic_semantic_actions  # 新增代码+GenericSemanticPlanner：返回聚焦和观察等通用桌面动作；如果没有这一行，非绘图任务不能进入 observe-plan-act loop 的正确分支。
        visual_requested = bool(task.get("visual_planning_requested"))  # 修改代码+GenericSemanticPlanner：只有明确声明绘图/视觉规划时才进入视觉画线分支；如果没有这一行，打开记事本也会被误画线。
        if static_actions and not visual_requested:  # 新增代码+VisualPlannerLoop：非视觉任务继续使用旧静态 DSL；如果没有这一行，代表样本和外部调用兼容性会下降。
            return static_actions  # 新增代码+VisualPlannerLoop：返回旧动作副本；如果没有这一行，普通应用控制会被绘图 planner 污染。
        semantic_actions = phase122_plan_visual_semantic_task(task, observation_frame, self.model)  # 新增代码+VisualSemanticPlanner：先尝试用脱敏语义意图生成可解释 primitive；如果没有这一行，房子 prompt 会继续退回通用脸。
        if semantic_actions:  # 新增代码+VisualSemanticPlanner：检查语义 planner 是否已经生成动作；如果没有这一行，空计划也可能被当成可执行结果。
            return semantic_actions  # 新增代码+VisualSemanticPlanner：返回屋顶、墙体、门窗等语义动作；如果没有这一行，语义计划不会进入通用 observe-plan-act loop。
        target_window = observation_frame.get("target_window", {}) if isinstance(observation_frame, dict) else {}  # 新增代码+VisualPlannerLoop：读取当前观察帧里的目标窗口；如果没有这一行，planner 无法基于屏幕状态设定坐标范围。
        rect = target_window.get("rect", {}) if isinstance(target_window, dict) else {}  # 新增代码+VisualPlannerLoop：读取窗口矩形；如果没有这一行，坐标会退回不透明魔法数。
        width = max(260, _phase120_visual_planner_dimension(rect, "width", "left", "right", 900))  # 修改代码+VisualPlannerCanvas：从 width 或 right-left 得到真实窗口宽度；如果没有这一行，真实 Paint 会退回 900 默认宽度导致笔画偏左。
        height = max(220, _phase120_visual_planner_dimension(rect, "height", "top", "bottom", 620))  # 修改代码+VisualPlannerCanvas：从 height 或 bottom-top 得到真实窗口高度；如果没有这一行，真实 Paint 会退回 620 默认高度导致笔画偏上。
        seed = _phase120_visual_planner_seed(str(task.get("prompt_signature", "")) or str(task.get("prompt_length", "")))  # 新增代码+VisualPlannerLoop：用脱敏签名生成任务相关种子；如果没有这一行，画猫、画房子、画星星会继续变成同一条固定线。
        app_hint = str(target_window.get("app_id", "") if isinstance(target_window, dict) else "").lower()  # 新增代码+VisualPlannerCanvas：读取目标应用提示用于选择画布安全区；如果没有这一行，Paint 的工具栏区域无法被避开。
        paint_canvas_mode = "paint" in app_hint or str(task.get("target", "")).lower() == "mspaint"  # 新增代码+VisualPlannerCanvas：判断当前是否是 Paint 类画布任务；如果没有这一行，planner 不能对 Paint 功能区做保守避让。
        canvas_left = int(width * 0.26) if paint_canvas_mode else int(width * 0.12)  # 新增代码+VisualPlannerCanvas：估算可绘制画布左边界；如果没有这一行，真实 Paint 的左侧工具区会吞掉主体笔画。
        canvas_top = int(height * 0.28) if paint_canvas_mode else int(height * 0.18)  # 新增代码+VisualPlannerCanvas：估算可绘制画布上边界；如果没有这一行，真实 Paint 的顶部功能区会吞掉主体笔画。
        canvas_right = max(canvas_left + 220, width - int(width * 0.12))  # 新增代码+VisualPlannerCanvas：估算可绘制画布右边界；如果没有这一行，中心和半径没有右侧边界约束。
        canvas_bottom = max(canvas_top + 180, height - int(height * 0.12))  # 新增代码+VisualPlannerCanvas：估算可绘制画布下边界；如果没有这一行，纵向笔画可能压到窗口底部或越界。
        center_x = max(canvas_left + 120, min(canvas_right - 120, (canvas_left + canvas_right) // 2 + (seed % 71) - 35))  # 修改代码+VisualPlannerCanvas：在画布安全区内计算横向中心；如果没有这一行，主体仍可能落到左上角工具区。
        center_y = max(canvas_top + 100, min(canvas_bottom - 100, (canvas_top + canvas_bottom) // 2 + (seed % 53) - 20))  # 修改代码+VisualPlannerCanvas：在画布安全区内计算纵向中心；如果没有这一行，真实 Paint 中主体会贴近功能区。
        radius_x = max(70, min(220, (canvas_right - canvas_left) // 5 + (seed % 29)))  # 修改代码+VisualPlannerCanvas：根据画布安全宽度计算横向半径；如果没有这一行，大窗口仍可能只画很小一段。
        radius_y = max(60, min(170, (canvas_bottom - canvas_top) // 5 + (seed % 23)))  # 修改代码+VisualPlannerCanvas：根据画布安全高度计算纵向半径；如果没有这一行，纵向覆盖不足会继续像短线。
        actions = [{"type": "focus_window", "visual_planner_action": True, "planner_model": self.model}]  # 新增代码+VisualPlannerLoop：先聚焦目标窗口；如果没有这一行，后续鼠标事件可能落到旧焦点窗口。
        actions.append({"type": "drag_path", "coordinate_space": "target_window", "visual_planner_action": True, "planner_model": self.model, "points": [{"x": center_x - radius_x, "y": center_y}, {"x": center_x - radius_x // 2, "y": center_y - radius_y}, {"x": center_x + radius_x // 2, "y": center_y - radius_y}, {"x": center_x + radius_x, "y": center_y}, {"x": center_x + radius_x // 2, "y": center_y + radius_y}, {"x": center_x - radius_x // 2, "y": center_y + radius_y}, {"x": center_x - radius_x, "y": center_y}]})  # 新增代码+VisualPlannerLoop：生成主体轮廓拖拽动作；如果没有这一行，视觉任务不会产生真实可执行绘图笔画。
        actions.append({"type": "drag_path", "coordinate_space": "target_window", "visual_planner_action": True, "planner_model": self.model, "points": [{"x": center_x - radius_x // 2, "y": center_y - radius_y // 3}, {"x": center_x - radius_x // 3, "y": center_y - radius_y // 2}, {"x": center_x - radius_x // 4, "y": center_y - radius_y // 3}]})  # 新增代码+VisualPlannerLoop：生成左侧内部细节笔画；如果没有这一行，视觉规划只会画空轮廓，难以证明多步计划。
        actions.append({"type": "drag_path", "coordinate_space": "target_window", "visual_planner_action": True, "planner_model": self.model, "points": [{"x": center_x + radius_x // 2, "y": center_y - radius_y // 3}, {"x": center_x + radius_x // 3, "y": center_y - radius_y // 2}, {"x": center_x + radius_x // 4, "y": center_y - radius_y // 3}]})  # 新增代码+VisualPlannerLoop：生成右侧内部细节笔画；如果没有这一行，左右结构不会被 planner 表达。
        actions.append({"type": "drag_path", "coordinate_space": "target_window", "visual_planner_action": True, "planner_model": self.model, "points": [{"x": center_x - radius_x // 4, "y": center_y + radius_y // 4}, {"x": center_x, "y": center_y + radius_y // 3}, {"x": center_x + radius_x // 4, "y": center_y + radius_y // 4}]})  # 新增代码+VisualPlannerLoop：生成底部细节笔画；如果没有这一行，planner 无法展示观察后多笔纠偏的基本形状能力。
        actions.append({"type": "observe", "visual_planner_action": True, "planner_model": self.model})  # 新增代码+VisualPlannerLoop：安排动作后的观察；如果没有这一行，闭环末端缺少显式观察动作。
        return actions  # 新增代码+VisualPlannerLoop：返回由观察帧和任务签名生成的动作列表；如果没有这一行，loop 拿不到可执行计划。
    # 新增代码+VisualPlannerLoop：函数段结束，Phase120VisualTaskPlanner.plan 到此结束；如果没有这个边界说明，初学者不容易看出视觉规划范围。
# 新增代码+VisualPlannerLoop：类段结束，Phase120VisualTaskPlanner 到此结束；如果没有这个边界说明，初学者不容易看出视觉 planner 范围。


class Phase119GenericVerifier:  # 新增代码+URG4ObservePlanActVerify：类段开始，定义通用验证器；如果没有这个类，动作后是否继续只能靠固定脚本判断。
    def verify(self, task: dict[str, Any], attempt: int, action_results: list[dict[str, Any]], before_frame: dict[str, Any], after_frame: dict[str, Any]) -> dict[str, Any]:  # 新增代码+URG4ObservePlanActVerify：函数段开始，根据观察和动作结果判断下一步；如果没有这段函数，闭环没有 verify 决策点。
        _ = attempt  # 新增代码+URG4ObservePlanActVerify：保留尝试次数参数给未来策略使用；如果没有这行代码，重试上下文无法进入 verifier 接口。
        forced_failure = bool(task.get("force_verification_failure"))  # 新增代码+URG4ObservePlanActVerify：读取测试用强制失败标记；如果没有这行代码，失败退出路径难以稳定验证。
        observations_ok = bool(before_frame.get("real_observation_frame") and after_frame.get("real_observation_frame"))  # 新增代码+URG4ObservePlanActVerify：确认动作前后都有观察帧；如果没有这行代码，缺观察也可能被误判成功。
        actions_ok = all(bool(result.get("ok")) for result in action_results) if action_results else True  # 新增代码+URG4ObservePlanActVerify：确认动作执行结果全部成功；如果没有这行代码，失败动作可能继续进入成功路径。
        verified = bool(observations_ok and actions_ok and not forced_failure)  # 新增代码+URG4ObservePlanActVerify：计算本轮是否通过验证；如果没有这行代码，verify 决策没有单一事实来源。
        return {"verified": verified, "decision": "verified" if verified else "verification_failed", "next_step": "complete" if verified else "retry_or_stop", "visual_or_uia_verification": observations_ok, "actions_ok": actions_ok, "forced_failure": forced_failure}  # 新增代码+URG4ObservePlanActVerify：返回通用验证摘要；如果没有这行代码，loop 不知道继续、重试还是停止。
    # 新增代码+URG4ObservePlanActVerify：函数段结束，Phase119GenericVerifier.verify 到此结束；如果没有这个边界说明，初学者不容易看出验证范围。
# 新增代码+URG4ObservePlanActVerify：类段结束，Phase119GenericVerifier 到此结束；如果没有这个边界说明，初学者不容易看出 verifier 范围。


class UniversalObservePlanActVerifyLoop:  # 新增代码+URG4ObservePlanActVerify：类段开始，组合观察、规划、动作、验证和清理的通用闭环；如果没有这个类，URG-4 只会是一组散落 helper。
    def __init__(self, observation_runtime: Any | None = None, action_runtime: Any | None = None, planner: Any | None = None, verifier: Any | None = None, max_retries: int = 1) -> None:  # 新增代码+URG4ObservePlanActVerify：函数段开始，允许注入各层依赖；如果没有这段函数，测试会被迫触碰真实桌面或无法替换策略。
        self.observation_runtime = observation_runtime if observation_runtime is not None else Phase119RecordingObservationRuntime()  # 新增代码+URG4ObservePlanActVerify：保存观察层，默认安全记录模式；如果没有这行代码，合同自检可能依赖真实屏幕。
        self.action_runtime = action_runtime if action_runtime is not None else UniversalActionDslRuntime()  # 新增代码+URG4ObservePlanActVerify：保存 URG-3 动作 runtime；如果没有这行代码，闭环不会到达 DSL-to-SendInput 桥。
        self.planner = planner if planner is not None else Phase119GenericPlanner()  # 新增代码+URG4ObservePlanActVerify：保存通用 planner；如果没有这行代码，observe 到 act 之间没有可替换决策层。
        self.verifier = verifier if verifier is not None else Phase119GenericVerifier()  # 新增代码+URG4ObservePlanActVerify：保存通用 verifier；如果没有这行代码，动作后没有统一验证决策。
        self.max_retries = max(0, int(max_retries))  # 新增代码+URG4ObservePlanActVerify：保存非负重试上限；如果没有这行代码，坏参数可能导致无限循环或负数逻辑。
        self.real_dispatch_performed = False  # 新增代码+URG4ObservePlanActVerify：记录本 loop 是否真实派发；如果没有这行代码，报告无法表达安全边界。
    # 新增代码+URG4ObservePlanActVerify：函数段结束，UniversalObservePlanActVerifyLoop.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _observe(self, target: str, target_window: dict[str, Any] | None = None) -> dict[str, Any]:  # 修改代码+BoundObservationTarget：函数段开始，统一调用观察 runtime 并传入绑定窗口；如果没有 target_window，真实观察层只能按 target_hint 猜窗口。
        return dict(self.observation_runtime.observe(target_hint=target, real_desktop_touched=self.real_dispatch_performed, target_window=dict(target_window or {})))  # 修改代码+BoundObservationTarget：返回观察帧副本并固定 agent-owned 目标；如果没有这一行，真实桌面旧窗口可能污染 planner。
    # 新增代码+URG4ObservePlanActVerify：函数段结束，UniversalObservePlanActVerifyLoop._observe 到此结束；如果没有这个边界说明，初学者不容易看出观察调用范围。

    def _cleanup(self, session: dict[str, Any], reason: str) -> dict[str, Any]:  # 新增代码+URG4ObservePlanActVerify：函数段开始，生成失败或完成后的清理摘要；如果没有这段函数，失败退出没有统一 cleanup 证据。
        return {"cleanup_completed": True, "session_id": str(session.get("session_id", "")), "reason": str(reason or ""), "real_desktop_touched": self.real_dispatch_performed}  # 新增代码+URG4ObservePlanActVerify：返回清理报告；如果没有这行代码，验收无法确认失败后已经收束状态。
    # 新增代码+URG4ObservePlanActVerify：函数段结束，UniversalObservePlanActVerifyLoop._cleanup 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。

    def run_task(self, task: dict[str, Any]) -> dict[str, Any]:  # 新增代码+URG4ObservePlanActVerify：函数段开始，执行一个自然语言任务对应的通用闭环；如果没有这段函数，URG-4 没有可复用入口。
        target = str(task.get("target", "notepad") or "notepad")  # 新增代码+URG4ObservePlanActVerify：读取目标名称；如果没有这行代码，target session 没有输入来源。
        session = dict(self.action_runtime.open_target_session(target, candidates=_phase119_sample_candidates(target)))  # 新增代码+URG4ObservePlanActVerify：通过 URG-3/2 建立目标 session；如果没有这行代码，动作前身份复核没有基础。
        attempts: list[dict[str, Any]] = []  # 新增代码+URG4ObservePlanActVerify：初始化每次尝试的证据列表；如果没有这行代码，失败或重试无法复盘。
        total_low_level_event_count = 0  # 新增代码+URG4ObservePlanActVerify：初始化底层事件总数；如果没有这行代码，报告无法证明正常路径到达 sender。
        planner_model = str(getattr(self.planner, "model", self.planner.__class__.__name__))  # 新增代码+VisualPlannerLoop：读取 planner 模型名用于报告；如果没有这一行，终端无法确认本轮到底用哪个规划器。
        visual_planner_connected = bool(getattr(self.planner, "visual_planner", False))  # 新增代码+VisualPlannerLoop：判断视觉 planner 是否已注入 loop；如果没有这一行，接线状态无法被测试和 maturity 读取。
        visual_planner_used = False  # 新增代码+VisualPlannerLoop：初始化本轮视觉 planner 使用标记；如果没有这一行，报告无法区分“已接线”和“已实际用到”。
        planned_action_count = 0  # 新增代码+VisualPlannerLoop：初始化 planner 产出的动作数量；如果没有这一行，空计划也可能不被发现。
        for attempt_index in range(self.max_retries + 1):  # 新增代码+URG4ObservePlanActVerify：按首试加有限重试执行；如果没有这行代码，失败任务没有 bounded retry。
            before_frame = self._observe(target, session.get("target_window") if isinstance(session.get("target_window"), dict) else {})  # 修改代码+BoundObservationTarget：任务尝试开始前观察已绑定窗口；如果没有这一行，planner 可能看到旧 Paint 窗口。
            actions = self.planner.plan(task, before_frame)  # 新增代码+URG4ObservePlanActVerify：根据任务和观察帧生成动作；如果没有这行代码，loop 只会盲目执行静态逻辑。
            planned_action_count += len(actions)  # 新增代码+VisualPlannerLoop：累计 planner 产出的动作数；如果没有这一行，报告无法证明规划器确实给了动作。
            visual_planner_used = bool(visual_planner_used or any(bool(action.get("visual_planner_action")) for action in actions if isinstance(action, dict)))  # 新增代码+VisualPlannerLoop：检查动作是否来自视觉 planner；如果没有这一行，静态旧动作可能被误报成视觉规划。
            action_results: list[dict[str, Any]] = []  # 新增代码+URG4ObservePlanActVerify：初始化本轮动作结果；如果没有这行代码，verifier 拿不到动作事实。
            step_records: list[dict[str, Any]] = []  # 新增代码+URG4ObservePlanActVerify：初始化动作级观察证据；如果没有这行代码，每个动作前后观察不可审计。
            for action in actions:  # 新增代码+URG4ObservePlanActVerify：逐个处理通用 DSL 动作；如果没有这行代码，动作序列无法执行。
                action_before = self._observe(target, session.get("target_window") if isinstance(session.get("target_window"), dict) else {})  # 修改代码+BoundObservationTarget：动作前重新观察已绑定窗口；如果没有这一行，动作前证据可能来自错误窗口。
                dispatch_result = dict(self.action_runtime.dispatch(session, action, current_window=session.get("target_window")))  # 新增代码+URG4ObservePlanActVerify：通过 URG-3 分发动作并复核目标；如果没有这行代码，闭环不会真正 act。
                self.real_dispatch_performed = bool(self.real_dispatch_performed or dispatch_result.get("real_dispatch_performed") or dispatch_result.get("real_desktop_touched") or getattr(self.action_runtime, "real_dispatch_performed", False))  # 修改代码+RealPhysicalFullMode：把动作 runtime 和 sender 返回的真实派发事实同步到 loop 顶层；如果没有这一行，真实鼠标键盘已经发生时终端仍会误报 real_dispatch_performed=false。
                action_after = self._observe(target, session.get("target_window") if isinstance(session.get("target_window"), dict) else {})  # 修改代码+BoundObservationTarget：动作后再次观察已绑定窗口；如果没有这一行，验证可能看错旧窗口状态。
                total_low_level_event_count += int(dispatch_result.get("low_level_event_count", 0) or 0)  # 新增代码+URG4ObservePlanActVerify：累计本动作底层事件数；如果没有这行代码，最终矩阵看不到动作规模。
                action_results.append(dispatch_result)  # 新增代码+URG4ObservePlanActVerify：保存动作结果给 verifier；如果没有这行代码，失败动作可能被忽略。
                step_records.append({"action": dict(action), "before_observation": action_before, "dispatch": dispatch_result, "after_observation": action_after})  # 新增代码+URG4ObservePlanActVerify：保存动作级完整证据；如果没有这行代码，前后观察链无法落盘。
            after_frame = self._observe(target, session.get("target_window") if isinstance(session.get("target_window"), dict) else {})  # 修改代码+BoundObservationTarget：整轮动作完成后观察已绑定窗口；如果没有这一行，最终验证可能混入桌面其它同名窗口。
            verification = dict(self.verifier.verify(task, attempt_index, action_results, before_frame, after_frame))  # 新增代码+URG4ObservePlanActVerify：调用通用 verifier 决定下一步；如果没有这行代码，loop 无法根据结果继续或停止。
            attempts.append({"attempt_index": attempt_index, "before_observation": before_frame, "steps": step_records, "after_observation": after_frame, "verification": verification})  # 新增代码+URG4ObservePlanActVerify：保存本轮完整证据；如果没有这行代码，失败时无法复盘尝试过程。
            if bool(verification.get("verified")):  # 新增代码+URG4ObservePlanActVerify：检查验证是否通过；如果没有这行代码，成功任务也会继续重试。
                cleanup = self._cleanup(session, "verified")  # 新增代码+URG4ObservePlanActVerify：成功后执行统一清理摘要；如果没有这行代码，完成路径没有收束证据。
                return {"ok": True, "decision": "verified", "model": PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MODEL, "target": target, "session": session, "attempt_count": len(attempts), "attempts": attempts, "cleanup_completed": cleanup["cleanup_completed"], "cleanup": cleanup, "low_level_event_count": total_low_level_event_count, "before_after_observation_per_action": all(bool(step.get("before_observation")) and bool(step.get("after_observation")) for attempt in attempts for step in attempt.get("steps", [])), "verification_decides_next_step": True, "planner_model": planner_model, "planned_action_count": planned_action_count, "visual_planner_connected": visual_planner_connected, "visual_planner_used": visual_planner_used, "real_dispatch_performed": self.real_dispatch_performed, "real_desktop_touched": self.real_dispatch_performed}  # 修改代码+VisualPlannerLoop：返回成功任务报告并暴露 planner 接线证据；如果没有这行代码，调用方无法知道动作是否来自视觉规划器。
        cleanup = self._cleanup(session, "verification_failed")  # 新增代码+URG4ObservePlanActVerify：失败重试耗尽后执行清理摘要；如果没有这行代码，失败路径没有收束证据。
        evidence_count = sum(2 + (2 * len(attempt.get("steps", []))) for attempt in attempts)  # 新增代码+URG4ObservePlanActVerify：计算观察证据数量；如果没有这行代码，失败时证据链规模不可见。
        return {"ok": False, "decision": "verification_failed", "model": PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MODEL, "target": target, "session": session, "attempt_count": len(attempts), "attempts": attempts, "cleanup_completed": cleanup["cleanup_completed"], "cleanup": cleanup, "evidence_count": evidence_count, "low_level_event_count": total_low_level_event_count, "before_after_observation_per_action": all(bool(step.get("before_observation")) and bool(step.get("after_observation")) for attempt in attempts for step in attempt.get("steps", [])), "verification_decides_next_step": True, "planner_model": planner_model, "planned_action_count": planned_action_count, "visual_planner_connected": visual_planner_connected, "visual_planner_used": visual_planner_used, "real_dispatch_performed": self.real_dispatch_performed, "real_desktop_touched": self.real_dispatch_performed}  # 修改代码+VisualPlannerLoop：返回失败任务报告并保留 planner 证据；如果没有这行代码，失败时无法判断是规划、动作还是验证出问题。
    # 新增代码+URG4ObservePlanActVerify：函数段结束，UniversalObservePlanActVerifyLoop.run_task 到此结束；如果没有这个边界说明，初学者不容易看出闭环执行范围。
# 新增代码+URG4ObservePlanActVerify：类段结束，UniversalObservePlanActVerifyLoop 到此结束；如果没有这个边界说明，初学者不容易看出通用 loop 范围。


def _phase119_contract_tasks() -> list[dict[str, Any]]:  # 新增代码+URG4ObservePlanActVerify：函数段开始，定义代表样本任务数据；如果没有这段函数，合同样本会散落且难以确认不是产品分支。
    return [{"target": "notepad", "goal": "enter text with generic DSL", "actions": [{"type": "type_text", "text": "phase119 sample"}, {"type": "press_key", "key": "ENTER"}]}, {"target": "calc", "goal": "enter expression with generic keys", "actions": [{"type": "press_key", "key": "1"}, {"type": "press_key", "key": "ADD"}, {"type": "press_key", "key": "1"}]}, {"target": "mspaint", "goal": "draw a generic stroke", "actions": [{"type": "drag_path", "points": [{"x": 10, "y": 10}, {"x": 30, "y": 30}, {"x": 50, "y": 10}]}]}]  # 新增代码+URG4ObservePlanActVerify：返回 Notepad/Calculator/Paint 代表样本且仅作为验收数据；如果没有这行代码，无法证明同一 loop 覆盖多样任务。
# 新增代码+URG4ObservePlanActVerify：函数段结束，_phase119_contract_tasks 到此结束；如果没有这个边界说明，初学者不容易看出样本数据范围。


def run_phase119_universal_loop_contract() -> dict[str, Any]:  # 新增代码+URG4ObservePlanActVerify：函数段开始，运行 URG-4 安全合同自检；如果没有这段函数，测试、CLI 和可见终端没有统一事实来源。
    loop = UniversalObservePlanActVerifyLoop(max_retries=1)  # 新增代码+URG4ObservePlanActVerify：创建安全记录型闭环；如果没有这行代码，合同没有执行主体。
    sample_results = [loop.run_task(task) for task in _phase119_contract_tasks()]  # 新增代码+URG4ObservePlanActVerify：用同一个 loop 执行三个代表样本；如果没有这行代码，通用性没有事实证据。
    failure_result = loop.run_task({"target": "notepad", "goal": "forced failure", "actions": [{"type": "click_point", "x": 1, "y": 1}], "force_verification_failure": True})  # 新增代码+URG4ObservePlanActVerify：执行强制失败样本验证 bounded retry；如果没有这行代码，失败退出路径没有合同证据。
    safety_report = run_phase118_universal_action_dsl_contract()  # 新增代码+URG4ObservePlanActVerify：复用 URG-3 安全合同确认漂移和 abort 零事件；如果没有这行代码，URG-4 报告不能继承动作层安全事实。
    sample_ok = all(bool(item.get("ok")) for item in sample_results)  # 新增代码+URG4ObservePlanActVerify：汇总代表样本是否都成功；如果没有这行代码，单个失败可能被忽略。
    before_after_observation_per_action = all(bool(item.get("before_after_observation_per_action")) for item in sample_results)  # 新增代码+URG4ObservePlanActVerify：汇总每个动作前后观察是否齐全；如果没有这行代码，证据链可能缺口。
    low_level_event_count = sum(int(item.get("low_level_event_count", 0) or 0) for item in sample_results)  # 新增代码+URG4ObservePlanActVerify：汇总正常样本底层事件数；如果没有这行代码，act 是否发生不可见。
    bounded_retry = bool((not failure_result.get("ok")) and int(failure_result.get("attempt_count", 0) or 0) == 2)  # 新增代码+URG4ObservePlanActVerify：确认失败样本首试加一次重试后停止；如果没有这行代码，重试上限没有机器事实。
    failure_exits_with_evidence_and_cleanup = bool(failure_result.get("cleanup_completed") and int(failure_result.get("evidence_count", 0) or 0) >= 2)  # 新增代码+URG4ObservePlanActVerify：确认失败会携带证据并清理；如果没有这行代码，失败路径容易留下半状态。
    passed = bool(sample_ok and before_after_observation_per_action and bounded_retry and failure_exits_with_evidence_and_cleanup and bool(safety_report.get("target_drift_zero_events")) and bool(safety_report.get("abort_zero_events")) and low_level_event_count > 0 and not PHASE119_REAL_DISPATCH_PERFORMED)  # 新增代码+URG4ObservePlanActVerify：汇总 URG-4 合同通过条件；如果没有这行代码，CLI 退出码无法表达整体结果。
    return {"marker": PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MARKER, "ok_token": PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_OK_TOKEN, "model": PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MODEL, "passed": passed, "observe_plan_act_verify_loop": True, "before_after_observation_per_action": before_after_observation_per_action, "verification_decides_next_step": True, "bounded_retry": bounded_retry, "failure_exits_with_evidence_and_cleanup": failure_exits_with_evidence_and_cleanup, "same_loop_handles_representative_samples": sample_ok, "notepad_sample_passed": bool(sample_results[0].get("ok")), "calculator_sample_passed": bool(sample_results[1].get("ok")), "paint_sample_passed": bool(sample_results[2].get("ok")), "per_app_controller_required": False, "hardcoded_app_whitelist_required": False, "ordinary_apps_controlled_by_generic_runtime": True, "representative_apps_are_acceptance_only": True, "target_identity_rechecked_before_each_action": True, "target_drift_zero_events": bool(safety_report.get("target_drift_zero_events")), "abort_zero_events": bool(safety_report.get("abort_zero_events")), "low_level_event_count_gt_zero": low_level_event_count > 0, "low_level_event_count": low_level_event_count, "real_dispatch_performed": PHASE119_REAL_DISPATCH_PERFORMED, "real_desktop_touched": PHASE119_REAL_DISPATCH_PERFORMED, "sample_results": sample_results, "failure_result": failure_result}  # 新增代码+URG4ObservePlanActVerify：返回完整合同报告；如果没有这行代码，测试和可见终端无法读取统一事实。
# 新增代码+URG4ObservePlanActVerify：函数段结束，run_phase119_universal_loop_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase119_universal_loop_cli_line(report: dict[str, Any]) -> str:  # 新增代码+URG4ObservePlanActVerify：函数段开始，把合同报告转成固定 token 行；如果没有这段函数，可见终端场景和测试会重复拼接。
    return f"{PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MARKER} {PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_OK_TOKEN} observe_plan_act_verify_loop={_phase119_bool_token(report.get('observe_plan_act_verify_loop'))} before_after_observation_per_action={_phase119_bool_token(report.get('before_after_observation_per_action'))} verification_decides_next_step={_phase119_bool_token(report.get('verification_decides_next_step'))} bounded_retry={_phase119_bool_token(report.get('bounded_retry'))} failure_exits_with_evidence_and_cleanup={_phase119_bool_token(report.get('failure_exits_with_evidence_and_cleanup'))} same_loop_handles_representative_samples={_phase119_bool_token(report.get('same_loop_handles_representative_samples'))} notepad_sample_passed={_phase119_bool_token(report.get('notepad_sample_passed'))} calculator_sample_passed={_phase119_bool_token(report.get('calculator_sample_passed'))} paint_sample_passed={_phase119_bool_token(report.get('paint_sample_passed'))} per_app_controller_required={_phase119_bool_token(report.get('per_app_controller_required'))} hardcoded_app_whitelist_required={_phase119_bool_token(report.get('hardcoded_app_whitelist_required'))} target_identity_rechecked_before_each_action={_phase119_bool_token(report.get('target_identity_rechecked_before_each_action'))} target_drift_zero_events={_phase119_bool_token(report.get('target_drift_zero_events'))} abort_zero_events={_phase119_bool_token(report.get('abort_zero_events'))} low_level_event_count_gt_zero={_phase119_bool_token(report.get('low_level_event_count_gt_zero'))} real_dispatch_performed={_phase119_bool_token(report.get('real_dispatch_performed'))} real_desktop_touched={_phase119_bool_token(report.get('real_desktop_touched'))} low_level_event_count={int(report.get('low_level_event_count', 0) or 0)}"  # 新增代码+URG4ObservePlanActVerify：返回固定顺序 token 行；如果没有这行代码，验收匹配容易因字段顺序漂移失败。
# 新增代码+URG4ObservePlanActVerify：函数段结束，phase119_universal_loop_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+URG4ObservePlanActVerify：函数段开始，提供命令行和真实可见终端统一入口；如果没有这段函数，controller 场景无法运行 URG-4。
    _ = argv  # 新增代码+URG4ObservePlanActVerify：保留未来参数扩展位；如果没有这行代码，读者可能误以为 argv 被遗漏。
    report = run_phase119_universal_loop_contract()  # 新增代码+URG4ObservePlanActVerify：运行 URG-4 合同；如果没有这行代码，CLI 没有结构化报告来源。
    print(phase119_universal_loop_cli_line(report))  # 新增代码+URG4ObservePlanActVerify：打印固定 token 行；如果没有这行代码，真实终端验收无法稳定匹配。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+URG4ObservePlanActVerify：打印完整 JSON 报告；如果没有这行代码，失败时不方便定位字段。
    print(PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MARKER)  # 新增代码+URG4ObservePlanActVerify：单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+URG4ObservePlanActVerify：按合同结果返回退出码；如果没有这行代码，失败也可能被终端当成成功。
# 新增代码+URG4ObservePlanActVerify：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = ["PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MARKER", "PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MODEL", "PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_OK_TOKEN", "PHASE119_REAL_DISPATCH_PERFORMED", "PHASE120_VISUAL_TASK_PLANNER_MODEL", "Phase119GenericPlanner", "Phase119GenericVerifier", "Phase119RecordingObservationRuntime", "Phase120VisualTaskPlanner", "UniversalObservePlanActVerifyLoop", "build_real_desktop_closure_evidence_from_loop_result", "main", "phase119_universal_loop_cli_line", "run_phase119_universal_loop_contract"]  # 修改代码+Phase8RealDesktopClosure：公开 loop 结果转真实闭环证据的函数；如果没有这一行，最终矩阵和测试无法稳定接入 Phase 8 证据。


if __name__ == "__main__":  # 新增代码+URG4ObservePlanActVerify：文件入口段开始，允许 `python -m` 直接运行；如果没有这行代码，真实终端无法直接调用本模块。
    raise SystemExit(main())  # 新增代码+URG4ObservePlanActVerify：调用 main 并传递退出码；如果没有这行代码，直接运行文件不会执行合同。
# 新增代码+URG4ObservePlanActVerify：文件入口段结束，本模块到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
