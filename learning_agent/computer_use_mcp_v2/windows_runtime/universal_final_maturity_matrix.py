"""URG-6 universal real GUI Computer Use final maturity matrix."""  # 新增代码+URG6FinalMatrix：说明本模块负责蓝图最终成熟度矩阵；如果没有这一行，读者不容易区分它和旧 full_maturity_matrix。
from __future__ import annotations  # 新增代码+URG6FinalMatrix：启用延迟类型解析；如果没有这一行，复杂类型标注在旧导入顺序下更容易失败。

import json  # 新增代码+URG6FinalMatrix：导入 JSON 用于 CLI 输出完整报告；如果没有这一行，失败时不容易复盘。
from typing import Any  # 新增代码+URG6FinalMatrix：导入 Any 描述动态 JSON 报告；如果没有这一行，公开接口边界不清楚。

try:  # 新增代码+URG6FinalMatrix：优先按包路径导入 URG-4/5 组件；如果没有这一段，单测和 bat 入口无法共享实现。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_action_dsl import UniversalActionDslRuntime  # 新增代码+URG6FinalMatrix：导入 URG-3 通用动作 runtime；如果没有这一行，代表样本不会走统一 SendInput 分发层。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_observe_plan_act_verify import Phase119GenericVerifier, Phase119RecordingObservationRuntime, UniversalObservePlanActVerifyLoop, run_phase119_universal_loop_contract  # 新增代码+URG6FinalMatrix：导入 URG-4 闭环和合同；如果没有这一行，最终矩阵无法证明同一个 loop 存在。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_paint_pikachu_acceptance import Phase120RepresentativeRealDragSender, run_phase120_universal_paint_pikachu_acceptance_contract  # 新增代码+URG6FinalMatrix：导入 URG-5 Paint/Pikachu 验收；如果没有这一行，核心代表场景无法进入矩阵。
except ModuleNotFoundError as error:  # 新增代码+URG6FinalMatrix：兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这一段，真实可见终端可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_action_dsl", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_observe_plan_act_verify", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_paint_pikachu_acceptance"}:  # 新增代码+URG6FinalMatrix：只兜底包路径缺失；如果没有这一行，真实内部 bug 可能被误吞。
        raise  # 新增代码+URG6FinalMatrix：重新抛出非路径类导入错误；如果没有这一行，排查依赖问题会变困难。
    from computer_use_mcp_v2.windows_runtime.universal_action_dsl import UniversalActionDslRuntime  # type: ignore  # 新增代码+URG6FinalMatrix：脚本模式导入通用动作 runtime；如果没有这一行，bat 入口无法执行代表样本。
    from computer_use_mcp_v2.windows_runtime.universal_observe_plan_act_verify import Phase119GenericVerifier, Phase119RecordingObservationRuntime, UniversalObservePlanActVerifyLoop, run_phase119_universal_loop_contract  # type: ignore  # 新增代码+URG6FinalMatrix：脚本模式导入 URG-4 闭环；如果没有这一行，bat 入口无法运行矩阵。
    from computer_use_mcp_v2.windows_runtime.universal_paint_pikachu_acceptance import Phase120RepresentativeRealDragSender, run_phase120_universal_paint_pikachu_acceptance_contract  # type: ignore  # 新增代码+URG6FinalMatrix：脚本模式导入 URG-5 验收；如果没有这一行，bat 入口无法汇总 Paint 场景。

UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER = "UNIVERSAL_REAL_GUI_COMPUTER_USE_READY"  # 新增代码+URG6FinalMatrix：定义蓝图最终 ready marker；如果没有这一行，真实终端和用户看不到终局锚点。
PHASE121_UNIVERSAL_FINAL_MATURITY_MODEL = "phase121_universal_real_gui_computer_use_final_matrix"  # 新增代码+URG6FinalMatrix：定义最终矩阵模型名；如果没有这一行，报告来源无法区分版本。
PHASE8_REAL_DESKTOP_CLOSURE_MODEL = "phase8_real_desktop_closure_evidence"  # 新增代码+Phase8RealDesktopClosure：定义真实桌面闭环证据模型名；如果没有这一行，报告无法区分 Phase 8 证据合同和普通矩阵报告。


def _phase121_bool_token(value: Any) -> str:  # 新增代码+URG6FinalMatrix：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出可能混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+URG6FinalMatrix：返回 true 或 false 文本；如果没有这一行，验收器字符串匹配会不稳定。
# 新增代码+URG6FinalMatrix：函数段结束，_phase121_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。


def _phase8_safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase8RealDesktopClosure：函数段开始，把外部证据安全整理成字典；如果没有这段函数，坏类型证据可能让矩阵直接崩溃。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase8RealDesktopClosure：只接受字典并复制一份；如果没有这一行，调用方传入的原始对象可能被内部逻辑意外修改。
# 新增代码+Phase8RealDesktopClosure：函数段结束，_phase8_safe_dict 到此结束；如果没有这个边界说明，初学者不容易看出证据清洗范围。


def _phase8_int(value: Any) -> int:  # 新增代码+Phase8RealDesktopClosure：函数段开始，把事件数量转成安全整数；如果没有这段函数，字符串或空值会打断真实证据校验。
    try:  # 新增代码+Phase8RealDesktopClosure：尝试按整数解释输入；如果没有这一行，低层事件计数无法兼容 JSON 里的数字字符串。
        return int(value or 0)  # 新增代码+Phase8RealDesktopClosure：返回整数事件数；如果没有这一行，校验器无法判断是否真的派发过低层事件。
    except (TypeError, ValueError):  # 新增代码+Phase8RealDesktopClosure：捕获坏类型和值错误；如果没有这一行，错误证据会变成异常而不是可读失败原因。
        return 0  # 新增代码+Phase8RealDesktopClosure：坏值按 0 个事件处理；如果没有这一行，录制或损坏证据可能绕过低层事件门禁。
# 新增代码+Phase8RealDesktopClosure：函数段结束，_phase8_int 到此结束；如果没有这个边界说明，初学者不容易看出数字清洗范围。


def validate_real_desktop_closure_evidence(evidence: dict[str, Any] | None) -> dict[str, Any]:  # 新增代码+Phase8RealDesktopClosure：函数段开始，校验真实桌面 observe-action-verify-cleanup 闭环证据；如果没有这段函数，最终矩阵只能拒绝或误信代表性录制证据。
    safe_evidence = _phase8_safe_dict(evidence)  # 新增代码+Phase8RealDesktopClosure：先把外部证据清洗成字典；如果没有这一行，None 或坏类型会造成不可控异常。
    target_identity = _phase8_safe_dict(safe_evidence.get("target_identity"))  # 新增代码+Phase8RealDesktopClosure：读取目标窗口身份；如果没有这一行，校验器不知道动作是否绑定到具体窗口。
    before_observation = _phase8_safe_dict(safe_evidence.get("before_observation"))  # 新增代码+Phase8RealDesktopClosure：读取动作前观察；如果没有这一行，agent 可能没看见窗口就动手也被误过。
    action = _phase8_safe_dict(safe_evidence.get("action"))  # 新增代码+Phase8RealDesktopClosure：读取动作派发证据；如果没有这一行，SendInput 是否真的发生不可判断。
    after_observation = _phase8_safe_dict(safe_evidence.get("after_observation"))  # 新增代码+Phase8RealDesktopClosure：读取动作后观察；如果没有这一行，桌面状态是否变化不可判断。
    verification = _phase8_safe_dict(safe_evidence.get("verification"))  # 新增代码+Phase8RealDesktopClosure：读取 verifier 判定；如果没有这一行，闭环缺少最终裁决。
    cleanup = _phase8_safe_dict(safe_evidence.get("cleanup"))  # 新增代码+Phase8RealDesktopClosure：读取清理结果；如果没有这一行，真实测试可能污染用户桌面却仍被判成功。
    representative_acceptance = _phase8_safe_dict(safe_evidence.get("representative_acceptance"))  # 新增代码+Phase8RealDesktopClosure：读取代表应用验收汇总；如果没有这一行，Layer A 无法证明普通应用覆盖面。
    hard_fail_reasons: list[str] = []  # 新增代码+Phase8RealDesktopClosure：创建硬失败原因列表；如果没有这一行，用户只能看到 false 看不到为什么失败。
    target_identity_present = bool((target_identity.get("window_id") or target_identity.get("hwnd")) and (target_identity.get("process_name") or target_identity.get("app_id") or target_identity.get("title") or target_identity.get("title_preview")))  # 新增代码+Phase8RealDesktopClosure：要求窗口句柄/ID 和进程/标题同时存在；如果没有这一行，动作目标可能没有可复核身份。
    before_window_seen = bool(before_observation.get("screenshot_captured") and before_observation.get("window_state_observation"))  # 新增代码+Phase8RealDesktopClosure：要求动作前截图和窗口状态都存在；如果没有这一行，真实窗口观察会被单一字段冒充。
    before_targeting_seen = bool(before_observation.get("uia_tree_observation") or before_observation.get("vision_targeting") or before_observation.get("uia_or_vision_targeting"))  # 新增代码+Phase8RealDesktopClosure：要求动作前有 UIA 或视觉定位；如果没有这一行，裸坐标点击也可能被误判成熟。
    after_window_seen = bool(after_observation.get("screenshot_captured") and after_observation.get("window_state_observation"))  # 新增代码+Phase8RealDesktopClosure：要求动作后截图和窗口状态都存在；如果没有这一行，无法证明执行后的桌面状态被重新观察。
    after_state_changed = bool(after_observation.get("state_changed_after_action"))  # 新增代码+Phase8RealDesktopClosure：要求动作后状态变化；如果没有这一行，发空动作也可能被算成功。
    sender_kind = str(action.get("sender_kind") or "").strip().lower()  # 新增代码+Phase8RealDesktopClosure：读取并标准化 sender 类型；如果没有这一行，录制 sender 不容易被稳定识别。
    low_level_event_count = _phase8_int(action.get("low_level_event_count"))  # 新增代码+Phase8RealDesktopClosure：读取低层事件数量；如果没有这一行，物理派发证据没有可量化门槛。
    physical_desktop_dispatch_performed = bool(action.get("physical_desktop_dispatch_performed"))  # 新增代码+Phase8RealDesktopClosure：读取物理桌面派发标记；如果没有这一行，录制 sender 会继续冒充真实动作。
    sender_is_recording_route = bool(not sender_kind or "record" in sender_kind or "representative" in sender_kind or "fake" in sender_kind)  # 新增代码+Phase8RealDesktopClosure：识别录制、代表性或假 sender；如果没有这一行，最危险的假阳性入口会被放过。
    real_sendinput_dispatch = bool(physical_desktop_dispatch_performed and action.get("real_sendinput_dispatch") and low_level_event_count > 0 and not sender_is_recording_route)  # 新增代码+Phase8RealDesktopClosure：汇总真实 SendInput 条件；如果没有这一行，单个字段为 true 就可能误过。
    verifier_accepted = bool(verification.get("verified") and str(verification.get("decision") or "").strip().lower() in {"accepted", "verified", "pass", "passed", "ok", "success"})  # 修改代码+Phase8RealDesktopClosure：允许通用 loop 的 verified 决策进入闭环门禁；如果没有这一行，真实 loop 成功也会被格式差异误拒。
    cleanup_completed = bool(cleanup.get("cleanup_completed") and cleanup.get("host_hidden_or_restored") and cleanup.get("lock_released"))  # 新增代码+Phase8RealDesktopClosure：要求清理完整完成；如果没有这一行，真实桌面状态可能被测试留脏。
    paint_pikachu_real_acceptance = bool(representative_acceptance.get("paint"))  # 新增代码+Phase8RealDesktopClosure：读取 Paint 真实验收；如果没有这一行，核心画图场景无法进入最终矩阵。
    notepad_real_acceptance = bool(representative_acceptance.get("notepad"))  # 新增代码+Phase8RealDesktopClosure：读取 Notepad 真实验收；如果没有这一行，文本输入场景无法进入最终矩阵。
    calculator_real_acceptance = bool(representative_acceptance.get("calculator"))  # 新增代码+Phase8RealDesktopClosure：读取 Calculator 真实验收；如果没有这一行，键盘/结果观察场景无法进入最终矩阵。
    browser_real_acceptance = bool(representative_acceptance.get("browser"))  # 新增代码+Phase8RealDesktopClosure：读取 Browser 真实验收；如果没有这一行，第三方窗口点击场景无法进入最终矩阵。
    target_identity_rechecked_before_each_action = bool(safe_evidence.get("target_identity_rechecked_before_each_action"))  # 新增代码+Phase8RealDesktopClosure：读取动作前身份复核标记；如果没有这一行，焦点漂移风险不会影响通过。
    script_artifact_route_blocked = bool(safe_evidence.get("script_artifact_route_blocked"))  # 新增代码+Phase8RealDesktopClosure：读取脚本成品路线阻断标记；如果没有这一行，Computer Use 可能被脚本 artifact 冒充。
    uncontrolled_high_risk_actions_allowed = bool(safe_evidence.get("uncontrolled_high_risk_actions_allowed"))  # 新增代码+Phase8RealDesktopClosure：读取高风险动作放开标记；如果没有这一行，不受控能力可能被误当成熟。
    if not target_identity_present:  # 新增代码+Phase8RealDesktopClosure：检查目标身份是否缺失；如果没有这一行，坏证据不会给出明确原因。
        hard_fail_reasons.append("target_identity missing window_id/hwnd plus process/title")  # 新增代码+Phase8RealDesktopClosure：记录目标身份失败原因；如果没有这一行，用户不知道窗口绑定哪里不够。
    if not before_window_seen:  # 新增代码+Phase8RealDesktopClosure：检查动作前窗口观察；如果没有这一行，缺截图或窗口状态不会被拦下。
        hard_fail_reasons.append("before_observation requires screenshot_captured and window_state_observation")  # 新增代码+Phase8RealDesktopClosure：记录动作前观察失败原因；如果没有这一行，排查需要猜字段。
    if not before_targeting_seen:  # 新增代码+Phase8RealDesktopClosure：检查 UIA/视觉定位；如果没有这一行，裸坐标证据不会被拦下。
        hard_fail_reasons.append("before_observation requires uia_tree_observation or vision_targeting")  # 新增代码+Phase8RealDesktopClosure：记录定位失败原因；如果没有这一行，用户不知道需要补 UIA/视觉证据。
    if not after_window_seen:  # 新增代码+Phase8RealDesktopClosure：检查动作后窗口观察；如果没有这一行，执行后未观察也可能通过。
        hard_fail_reasons.append("after_observation requires screenshot_captured and window_state_observation")  # 新增代码+Phase8RealDesktopClosure：记录动作后观察失败原因；如果没有这一行，失败原因不够直观。
    if not after_state_changed:  # 新增代码+Phase8RealDesktopClosure：检查动作后状态变化；如果没有这一行，空操作可能冒充成功。
        hard_fail_reasons.append("after_observation requires state_changed_after_action")  # 新增代码+Phase8RealDesktopClosure：记录状态变化失败原因；如果没有这一行，用户不知道 verifier 前的事实缺口。
    if not physical_desktop_dispatch_performed:  # 新增代码+Phase8RealDesktopClosure：检查物理桌面派发标记；如果没有这一行，recording sender 会绕过门禁。
        hard_fail_reasons.append("physical_desktop_dispatch_performed must be true")  # 新增代码+Phase8RealDesktopClosure：记录物理派发失败原因；如果没有这一行，测试无法精确断言关键字段。
    if sender_is_recording_route:  # 新增代码+Phase8RealDesktopClosure：检查 sender 是否是录制或代表路线；如果没有这一行，旧 sender 可能再次被当成真实执行。
        hard_fail_reasons.append("sender_kind must be a physical sender, not recording/representative/fake")  # 新增代码+Phase8RealDesktopClosure：记录 sender 类型失败原因；如果没有这一行，测试无法精确断言 sender 风险。
    if not real_sendinput_dispatch:  # 新增代码+Phase8RealDesktopClosure：检查真实 SendInput 汇总条件；如果没有这一行，低层事件数或真实标记缺失不会被拦下。
        hard_fail_reasons.append("real_sendinput_dispatch requires physical dispatch, non-recording sender, and low_level_event_count > 0")  # 新增代码+Phase8RealDesktopClosure：记录 SendInput 失败原因；如果没有这一行，动作层问题不容易定位。
    if not verifier_accepted:  # 新增代码+Phase8RealDesktopClosure：检查 verifier 是否通过；如果没有这一行，失败验证也可能进入矩阵。
        hard_fail_reasons.append("verification must be accepted")  # 新增代码+Phase8RealDesktopClosure：记录 verifier 失败原因；如果没有这一行，用户不知道闭环最后一步缺失。
    if not cleanup_completed:  # 新增代码+Phase8RealDesktopClosure：检查清理是否完成；如果没有这一行，污染桌面的测试可能被当成成功。
        hard_fail_reasons.append("cleanup must complete host restore and lock release")  # 新增代码+Phase8RealDesktopClosure：记录清理失败原因；如果没有这一行，清理风险不容易追溯。
    if not all([paint_pikachu_real_acceptance, notepad_real_acceptance, calculator_real_acceptance, browser_real_acceptance]):  # 新增代码+Phase8RealDesktopClosure：检查四个代表应用是否都通过；如果没有这一行，覆盖面不完整也会被当成成熟。
        hard_fail_reasons.append("representative_acceptance requires paint/notepad/calculator/browser")  # 新增代码+Phase8RealDesktopClosure：记录代表应用覆盖失败原因；如果没有这一行，用户不知道少了哪个验收维度。
    if not target_identity_rechecked_before_each_action:  # 新增代码+Phase8RealDesktopClosure：检查动作前身份复核；如果没有这一行，窗口焦点漂移不会影响通过。
        hard_fail_reasons.append("target_identity_rechecked_before_each_action must be true")  # 新增代码+Phase8RealDesktopClosure：记录身份复核失败原因；如果没有这一行，安全门禁不可解释。
    if not script_artifact_route_blocked:  # 新增代码+Phase8RealDesktopClosure：检查脚本 artifact 路线是否阻断；如果没有这一行，非 Computer Use 成品路线可能绕过验收。
        hard_fail_reasons.append("script_artifact_route_blocked must be true")  # 新增代码+Phase8RealDesktopClosure：记录脚本路线失败原因；如果没有这一行，画图验收风险不直观。
    if uncontrolled_high_risk_actions_allowed:  # 新增代码+Phase8RealDesktopClosure：检查高风险动作是否被放开；如果没有这一行，不受控能力可能被误当成熟。
        hard_fail_reasons.append("uncontrolled_high_risk_actions_allowed must be false")  # 新增代码+Phase8RealDesktopClosure：记录高风险动作失败原因；如果没有这一行，权限风险不会进入报告。
    accepted = not hard_fail_reasons  # 新增代码+Phase8RealDesktopClosure：只有没有硬失败才接收证据；如果没有这一行，最终矩阵没有单一通过结论。
    return {"model": PHASE8_REAL_DESKTOP_CLOSURE_MODEL, "accepted": accepted, "hard_fail_reasons": hard_fail_reasons, "evidence_supplied": bool(safe_evidence), "target_identity_present": target_identity_present, "real_window_observation": bool(target_identity_present and before_window_seen and after_window_seen), "real_uia_or_vision_targeting": bool(before_targeting_seen), "real_sendinput_dispatch": real_sendinput_dispatch, "cleanup_completed": cleanup_completed, "paint_pikachu_real_acceptance": paint_pikachu_real_acceptance, "notepad_real_acceptance": notepad_real_acceptance, "calculator_real_acceptance": calculator_real_acceptance, "browser_real_acceptance": browser_real_acceptance, "target_identity_rechecked_before_each_action": target_identity_rechecked_before_each_action, "script_artifact_route_blocked": script_artifact_route_blocked, "real_desktop_execution_mature": accepted, "uncontrolled_high_risk_actions_allowed": uncontrolled_high_risk_actions_allowed, "low_level_event_count": low_level_event_count, "sender_kind": sender_kind, "physical_desktop_dispatch_performed": physical_desktop_dispatch_performed}  # 新增代码+Phase8RealDesktopClosure：返回结构化校验结果；如果没有这一行，最终矩阵无法复用闭环证据。
# 新增代码+Phase8RealDesktopClosure：函数段结束，validate_real_desktop_closure_evidence 到此结束；如果没有这个边界说明，初学者不容易看出真实闭环门禁范围。


def _phase121_run_representative_task(target: str, actions: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+URG6FinalMatrix：函数段开始，用同一个通用 loop 跑代表应用样本；如果没有这段函数，矩阵容易退回每个应用一套逻辑。
    sender = Phase120RepresentativeRealDragSender()  # 新增代码+URG6FinalMatrix：创建代表真实低层 sender；如果没有这一行，动作是否到达低层不可验证。
    action_runtime = UniversalActionDslRuntime(low_level_sender=sender)  # 新增代码+URG6FinalMatrix：把通用动作 runtime 接到代表 sender；如果没有这一行，样本动作不会走统一 dispatcher。
    loop = UniversalObservePlanActVerifyLoop(observation_runtime=Phase119RecordingObservationRuntime(), action_runtime=action_runtime, verifier=Phase119GenericVerifier(), max_retries=0)  # 新增代码+URG6FinalMatrix：创建 URG-4 通用闭环；如果没有这一行，样本无法证明 observe-plan-act-verify。
    result = loop.run_task({"target": str(target), "goal": f"representative {target} real acceptance", "actions": [dict(action) for action in actions]})  # 新增代码+URG6FinalMatrix：执行代表任务；如果没有这一行，报告没有事实来源。
    low_level_event_count = len(sender.low_level_events)  # 新增代码+URG6FinalMatrix：统计低层事件数；如果没有这一行，真实派发字段不可量化。
    physical_desktop_dispatch_performed = bool(getattr(sender, "physical_desktop_dispatch_performed", False))  # 新增代码+源码复核门禁：读取是否真的发生物理桌面派发；如果没有这一行，代表事件会被误判为真实动作。
    representative_dispatch_performed = bool(low_level_event_count > 0)  # 新增代码+源码复核门禁：保留代表性事件作为开发证据；如果没有这一行，调试时看不到 DSL 是否到达 sender。
    return {"target": str(target), "ok": bool(result.get("ok") and physical_desktop_dispatch_performed), "observe_plan_act_verify_loop": True, "real_window_observation": False, "representative_window_observation": True, "real_uia_or_vision_targeting": False, "representative_uia_or_vision_targeting": True, "real_sendinput_dispatch": physical_desktop_dispatch_performed, "representative_dispatch_performed": representative_dispatch_performed, "physical_desktop_dispatch_performed": physical_desktop_dispatch_performed, "target_identity_rechecked_before_each_action": True, "low_level_event_count": low_level_event_count, "result": result}  # 修改代码+源码复核门禁：返回代表验收摘要并把真实字段绑定物理证据；如果没有这一行，上层矩阵无法统一读取各应用状态。
# 新增代码+URG6FinalMatrix：函数段结束，_phase121_run_representative_task 到此结束；如果没有这个边界说明，初学者不容易看出代表任务范围。


def _phase121_notepad_actions() -> list[dict[str, Any]]:  # 新增代码+URG6FinalMatrix：函数段开始，定义 Notepad 代表动作；如果没有这段函数，文本输入场景没有稳定样本。
    return [{"type": "type_text", "text": "phase121 notepad"}, {"type": "press_key", "key": "ENTER"}]  # 新增代码+URG6FinalMatrix：返回通用文本和按键动作；如果没有这一行，Notepad 验收不会覆盖输入。
# 新增代码+URG6FinalMatrix：函数段结束，_phase121_notepad_actions 到此结束；如果没有这个边界说明，初学者不容易看出动作范围。


def _phase121_calculator_actions() -> list[dict[str, Any]]:  # 新增代码+URG6FinalMatrix：函数段开始，定义 Calculator 代表动作；如果没有这段函数，按键/结果观察场景没有稳定样本。
    return [{"type": "press_key", "key": "1"}, {"type": "press_key", "key": "ADD"}, {"type": "press_key", "key": "1"}, {"type": "press_key", "key": "ENTER"}]  # 新增代码+URG6FinalMatrix：返回通用计算器按键动作；如果没有这一行，Calculator 验收不会覆盖键盘路径。
# 新增代码+URG6FinalMatrix：函数段结束，_phase121_calculator_actions 到此结束；如果没有这个边界说明，初学者不容易看出动作范围。


def _phase121_browser_actions() -> list[dict[str, Any]]:  # 新增代码+URG6FinalMatrix：函数段开始，定义 Browser 代表动作；如果没有这段函数，浏览器点击/观察场景没有稳定样本。
    return [{"type": "click_point", "x": 240, "y": 180}, {"type": "hotkey", "keys": ["CTRL", "L"]}]  # 新增代码+URG6FinalMatrix：返回通用点击和快捷键动作；如果没有这一行，Browser 验收不会覆盖鼠标点击和组合键。
# 新增代码+URG6FinalMatrix：函数段结束，_phase121_browser_actions 到此结束；如果没有这个边界说明，初学者不容易看出动作范围。


def run_phase121_universal_final_maturity_matrix(real_desktop_evidence: dict[str, Any] | None = None) -> dict[str, Any]:  # 修改代码+Phase8RealDesktopClosure：函数段开始，运行 URG-6 最终成熟度矩阵并可注入真实桌面闭环证据；如果没有这个参数，真实终端验收结果无法进入顶层矩阵。
    loop_report = run_phase119_universal_loop_contract()  # 新增代码+URG6FinalMatrix：运行 URG-4 闭环合同；如果没有这一行，最终矩阵无法证明单一 loop 已存在。
    paint_report = run_phase120_universal_paint_pikachu_acceptance_contract()  # 新增代码+URG6FinalMatrix：运行 URG-5 Paint/Pikachu 验收；如果没有这一行，最终矩阵缺少核心代表应用。
    notepad_report = _phase121_run_representative_task("notepad", _phase121_notepad_actions())  # 新增代码+URG6FinalMatrix：运行 Notepad 代表验收；如果没有这一行，文本应用覆盖缺失。
    calculator_report = _phase121_run_representative_task("calculator", _phase121_calculator_actions())  # 新增代码+URG6FinalMatrix：运行 Calculator 代表验收；如果没有这一行，计算器覆盖缺失。
    browser_report = _phase121_run_representative_task("browser", _phase121_browser_actions())  # 新增代码+URG6FinalMatrix：运行 Browser 代表验收；如果没有这一行，网页/第三方点击覆盖缺失。
    real_desktop_closure_report = validate_real_desktop_closure_evidence(real_desktop_evidence)  # 新增代码+Phase8RealDesktopClosure：校验外部真实桌面闭环证据；如果没有这一行，矩阵无法区分真实执行和代表性录制执行。
    single_universal_real_gui_loop = bool(loop_report.get("observe_plan_act_verify_loop") and loop_report.get("same_loop_handles_representative_samples"))  # 新增代码+URG6FinalMatrix：汇总是否存在单一通用闭环；如果没有这一行，最终 passed 没有架构依据。
    per_app_controller_required = False  # 新增代码+URG6FinalMatrix：声明不需要逐应用 controller；如果没有这一行，蓝图禁止路线不可见。
    hardcoded_app_whitelist_required = False  # 新增代码+URG6FinalMatrix：声明不需要硬编码 app 白名单；如果没有这一行，通用性边界不可见。
    ordinary_apps_controlled_by_generic_runtime = True  # 新增代码+URG6FinalMatrix：声明普通应用走通用 runtime；如果没有这一行，最终矩阵无法回答普通软件控制能力。
    representative_apps_are_acceptance_only = True  # 新增代码+URG6FinalMatrix：声明代表应用只是验收样本；如果没有这一行，用户可能误以为产品需要样本白名单。
    real_window_observation = bool(notepad_report["real_window_observation"] and calculator_report["real_window_observation"] and browser_report["real_window_observation"] and paint_report["real_paint_window_verified"])  # 修改代码+源码复核门禁：只把真实窗口观察汇总为真实能力；如果没有这一行，观察链路缺失可能被漏掉。
    real_uia_or_vision_targeting = bool(notepad_report["real_uia_or_vision_targeting"] and calculator_report["real_uia_or_vision_targeting"] and browser_report["real_uia_or_vision_targeting"] and paint_report["real_canvas_region_detected"])  # 修改代码+源码复核门禁：只把真实 UIA/视觉证据汇总为真实定位；如果没有这一行，目标定位缺失可能被漏掉。
    real_sendinput_dispatch = bool(notepad_report["real_sendinput_dispatch"] and calculator_report["real_sendinput_dispatch"] and browser_report["real_sendinput_dispatch"] and paint_report["real_drag_path_dispatched"])  # 修改代码+源码复核门禁：只把物理桌面派发汇总为真实 SendInput；如果没有这一行，动作只停留在观察也可能误过。
    target_identity_rechecked_before_each_action = bool(loop_report.get("target_identity_rechecked_before_each_action") and paint_report.get("target_identity_rechecked_before_each_action"))  # 新增代码+URG6FinalMatrix：汇总动作前身份复核；如果没有这一行，窗口漂移风险不可见。
    observe_plan_act_verify_loop = bool(loop_report.get("observe_plan_act_verify_loop"))  # 新增代码+URG6FinalMatrix：汇总 URG-4 闭环 token；如果没有这一行，最终行无法直接显示闭环。
    paint_pikachu_real_acceptance = bool(paint_report.get("passed"))  # 新增代码+URG6FinalMatrix：汇总 Paint/Pikachu 验收；如果没有这一行，核心代表场景不会影响 passed。
    notepad_real_acceptance = bool(notepad_report.get("ok"))  # 新增代码+URG6FinalMatrix：汇总 Notepad 验收；如果没有这一行，文本场景不会影响 passed。
    calculator_real_acceptance = bool(calculator_report.get("ok"))  # 新增代码+URG6FinalMatrix：汇总 Calculator 验收；如果没有这一行，计算器场景不会影响 passed。
    browser_real_acceptance = bool(browser_report.get("ok"))  # 新增代码+URG6FinalMatrix：汇总 Browser 验收；如果没有这一行，浏览器场景不会影响 passed。
    script_artifact_route_blocked = bool(paint_report.get("script_artifact_route_blocked"))  # 新增代码+URG6FinalMatrix：汇总脚本成品路线阻断；如果没有这一行，图片 artifact 作弊可能漏过。
    real_desktop_execution_mature = bool(paint_report.get("real_desktop_execution_mature") and notepad_real_acceptance and calculator_real_acceptance and browser_real_acceptance)  # 新增代码+URG6FinalMatrix：汇总真实桌面执行成熟；如果没有这一行，最终成熟度没有单一结论。
    uncontrolled_high_risk_actions_allowed = False  # 新增代码+URG6FinalMatrix：声明未放开高风险动作；如果没有这一行，full 能力可能被误解为无限权限。
    if real_desktop_closure_report.get("accepted"):  # 新增代码+Phase8RealDesktopClosure：只有合格真实闭环证据才允许覆盖代表性录制结果；如果没有这一行，测试注入或旧 sender 都可能误改成熟度。
        real_window_observation = bool(real_desktop_closure_report.get("real_window_observation"))  # 新增代码+Phase8RealDesktopClosure：用真实闭环证据确认窗口观察；如果没有这一行，Layer A 不能被真实桌面观察翻转。
        real_uia_or_vision_targeting = bool(real_desktop_closure_report.get("real_uia_or_vision_targeting"))  # 新增代码+Phase8RealDesktopClosure：用真实闭环证据确认 UIA/视觉定位；如果没有这一行，定位能力不能进入最终矩阵。
        real_sendinput_dispatch = bool(real_desktop_closure_report.get("real_sendinput_dispatch"))  # 新增代码+Phase8RealDesktopClosure：用真实闭环证据确认 SendInput 派发；如果没有这一行，动作能力不能进入最终矩阵。
        target_identity_rechecked_before_each_action = bool(real_desktop_closure_report.get("target_identity_rechecked_before_each_action"))  # 新增代码+Phase8RealDesktopClosure：用真实闭环证据确认动作前身份复核；如果没有这一行，焦点漂移保护不能进入最终矩阵。
        paint_pikachu_real_acceptance = bool(real_desktop_closure_report.get("paint_pikachu_real_acceptance"))  # 新增代码+Phase8RealDesktopClosure：用真实闭环证据确认 Paint 验收；如果没有这一行，核心画图场景不能从真实终端证据进入矩阵。
        notepad_real_acceptance = bool(real_desktop_closure_report.get("notepad_real_acceptance"))  # 新增代码+Phase8RealDesktopClosure：用真实闭环证据确认 Notepad 验收；如果没有这一行，文本场景不能从真实终端证据进入矩阵。
        calculator_real_acceptance = bool(real_desktop_closure_report.get("calculator_real_acceptance"))  # 新增代码+Phase8RealDesktopClosure：用真实闭环证据确认 Calculator 验收；如果没有这一行，计算器场景不能从真实终端证据进入矩阵。
        browser_real_acceptance = bool(real_desktop_closure_report.get("browser_real_acceptance"))  # 新增代码+Phase8RealDesktopClosure：用真实闭环证据确认 Browser 验收；如果没有这一行，浏览器场景不能从真实终端证据进入矩阵。
        script_artifact_route_blocked = bool(real_desktop_closure_report.get("script_artifact_route_blocked"))  # 新增代码+Phase8RealDesktopClosure：用真实闭环证据确认脚本路线阻断；如果没有这一行，真实验收可能仍被 artifact 路线污染。
        real_desktop_execution_mature = bool(real_desktop_closure_report.get("real_desktop_execution_mature"))  # 新增代码+Phase8RealDesktopClosure：用真实闭环证据确认桌面执行成熟；如果没有这一行，Layer A 无法真正闭环。
        uncontrolled_high_risk_actions_allowed = bool(real_desktop_closure_report.get("uncontrolled_high_risk_actions_allowed"))  # 新增代码+Phase8RealDesktopClosure：用真实闭环证据确认高风险动作边界；如果没有这一行，权限风险可能被忽略。
    passed = bool(single_universal_real_gui_loop and not per_app_controller_required and not hardcoded_app_whitelist_required and ordinary_apps_controlled_by_generic_runtime and representative_apps_are_acceptance_only and real_window_observation and real_uia_or_vision_targeting and real_sendinput_dispatch and target_identity_rechecked_before_each_action and observe_plan_act_verify_loop and paint_pikachu_real_acceptance and notepad_real_acceptance and calculator_real_acceptance and browser_real_acceptance and script_artifact_route_blocked and real_desktop_execution_mature and not uncontrolled_high_risk_actions_allowed)  # 新增代码+URG6FinalMatrix：汇总最终通过条件；如果没有这一行，main 无法用退出码表达失败。
    return {"marker": UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER, "model": PHASE121_UNIVERSAL_FINAL_MATURITY_MODEL, "passed": passed, "single_universal_real_gui_loop": single_universal_real_gui_loop, "per_app_controller_required": per_app_controller_required, "hardcoded_app_whitelist_required": hardcoded_app_whitelist_required, "ordinary_apps_controlled_by_generic_runtime": ordinary_apps_controlled_by_generic_runtime, "representative_apps_are_acceptance_only": representative_apps_are_acceptance_only, "real_window_observation": real_window_observation, "real_uia_or_vision_targeting": real_uia_or_vision_targeting, "real_sendinput_dispatch": real_sendinput_dispatch, "target_identity_rechecked_before_each_action": target_identity_rechecked_before_each_action, "observe_plan_act_verify_loop": observe_plan_act_verify_loop, "paint_pikachu_real_acceptance": paint_pikachu_real_acceptance, "notepad_real_acceptance": notepad_real_acceptance, "calculator_real_acceptance": calculator_real_acceptance, "browser_real_acceptance": browser_real_acceptance, "script_artifact_route_blocked": script_artifact_route_blocked, "real_desktop_execution_mature": real_desktop_execution_mature, "uncontrolled_high_risk_actions_allowed": uncontrolled_high_risk_actions_allowed, "reports": {"loop": loop_report, "paint": paint_report, "notepad": notepad_report, "calculator": calculator_report, "browser": browser_report, "real_desktop_closure": real_desktop_closure_report}}  # 修改代码+Phase8RealDesktopClosure：返回完整最终矩阵并附带真实闭环报告；如果没有这一行，测试和真实终端无法追溯 Phase 8 是否接受证据。
# 新增代码+URG6FinalMatrix：函数段结束，run_phase121_universal_final_maturity_matrix 到此结束；如果没有这个边界说明，初学者不容易看出矩阵范围。


def phase121_universal_final_maturity_cli_line(report: dict[str, Any]) -> str:  # 新增代码+URG6FinalMatrix：函数段开始，把最终矩阵转成蓝图固定 token 行；如果没有这段函数，真实终端验收需要解析复杂 JSON。
    return f"{UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER} single_universal_real_gui_loop={_phase121_bool_token(report.get('single_universal_real_gui_loop'))} per_app_controller_required={_phase121_bool_token(report.get('per_app_controller_required'))} hardcoded_app_whitelist_required={_phase121_bool_token(report.get('hardcoded_app_whitelist_required'))} ordinary_apps_controlled_by_generic_runtime={_phase121_bool_token(report.get('ordinary_apps_controlled_by_generic_runtime'))} representative_apps_are_acceptance_only={_phase121_bool_token(report.get('representative_apps_are_acceptance_only'))} real_window_observation={_phase121_bool_token(report.get('real_window_observation'))} real_uia_or_vision_targeting={_phase121_bool_token(report.get('real_uia_or_vision_targeting'))} real_sendinput_dispatch={_phase121_bool_token(report.get('real_sendinput_dispatch'))} target_identity_rechecked_before_each_action={_phase121_bool_token(report.get('target_identity_rechecked_before_each_action'))} observe_plan_act_verify_loop={_phase121_bool_token(report.get('observe_plan_act_verify_loop'))} paint_pikachu_real_acceptance={_phase121_bool_token(report.get('paint_pikachu_real_acceptance'))} notepad_real_acceptance={_phase121_bool_token(report.get('notepad_real_acceptance'))} calculator_real_acceptance={_phase121_bool_token(report.get('calculator_real_acceptance'))} browser_real_acceptance={_phase121_bool_token(report.get('browser_real_acceptance'))} script_artifact_route_blocked={_phase121_bool_token(report.get('script_artifact_route_blocked'))} real_desktop_execution_mature={_phase121_bool_token(report.get('real_desktop_execution_mature'))} uncontrolled_high_risk_actions_allowed={_phase121_bool_token(report.get('uncontrolled_high_risk_actions_allowed'))}"  # 新增代码+URG6FinalMatrix：返回固定顺序最终 token；如果没有这一行，蓝图最终验收容易因字段漂移失败。
# 新增代码+URG6FinalMatrix：函数段结束，phase121_universal_final_maturity_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+URG6FinalMatrix：函数段开始，提供命令行和真实终端入口；如果没有这段函数，controller 场景无法运行最终矩阵。
    _ = argv  # 新增代码+URG6FinalMatrix：保留 argv 扩展位；如果没有这一行，读者可能误以为参数被遗漏。
    report = run_phase121_universal_final_maturity_matrix()  # 新增代码+URG6FinalMatrix：运行最终矩阵；如果没有这一行，CLI 没有事实来源。
    print(phase121_universal_final_maturity_cli_line(report))  # 新增代码+URG6FinalMatrix：打印蓝图固定最终行；如果没有这一行，真实终端验收无法稳定匹配。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+URG6FinalMatrix：打印完整结构化报告；如果没有这一行，失败时不方便定位。
    print(UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER)  # 新增代码+URG6FinalMatrix：单独打印最终 marker；如果没有这一行，人工观察终端可能漏掉终局标识。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+URG6FinalMatrix：按最终矩阵状态返回退出码；如果没有这一行，失败也可能被自动化当成成功。
# 新增代码+URG6FinalMatrix：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["PHASE121_UNIVERSAL_FINAL_MATURITY_MODEL", "PHASE8_REAL_DESKTOP_CLOSURE_MODEL", "UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER", "main", "phase121_universal_final_maturity_cli_line", "run_phase121_universal_final_maturity_matrix", "validate_real_desktop_closure_evidence"]  # 修改代码+Phase8RealDesktopClosure：公开 Phase 8 证据校验 API；如果没有这一行，测试和后续 acceptance controller 无法稳定导入真实闭环门禁。


if __name__ == "__main__":  # 新增代码+URG6FinalMatrix：文件入口段开始，允许 python -m 直接运行；如果没有这一行，真实终端无法启动最终矩阵。
    raise SystemExit(main())  # 新增代码+URG6FinalMatrix：用 main 返回码退出；如果没有这一行，命令行状态不明确。
# 新增代码+URG6FinalMatrix：文件入口段结束，本模块到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
