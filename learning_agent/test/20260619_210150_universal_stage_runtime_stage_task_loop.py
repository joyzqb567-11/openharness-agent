"""Universal stage-level desktop task loop for Computer Use full mode."""  # 新增代码+StageTaskLoop：说明本文件负责通用阶段任务运行；如果没有这行代码，读者会误以为这是单应用自动化。
from __future__ import annotations  # 新增代码+StageTaskLoop：启用延迟类型解析；如果没有这行代码，类型注解更容易在导入阶段失败。

from typing import Any, Callable, Mapping  # 新增代码+StageTaskLoop：导入动态依赖类型；如果没有这行代码，依赖注入边界不清楚。

from .batch_executor import UniversalActionBatchExecutor  # 新增代码+StageTaskLoop：导入批执行器；如果没有这行代码，阶段无法批量执行。
from .capability_profile import AppCapabilityProfile, build_capability_profile  # 新增代码+StageTaskLoop：导入能力画像构建；如果没有这行代码，阶段编译会回到应用名判断。
from .stage_batch_compiler import compile_stage_to_batch  # 新增代码+StageTaskLoop：导入阶段批编译器；如果没有这行代码，StagePlan 无法转成 ActionBatch。
from .stage_models import DesktopTaskPlan, DesktopTaskRunState, StagePlan, StageResult, desktop_task_plan_to_dict, stage_result_to_dict  # 新增代码+StageTaskLoop：导入通用模型和序列化 helper；如果没有这行代码，报告会变成散乱字段。
from .stage_planner import UniversalDesktopStagePlanner  # 新增代码+StageTaskLoop：导入通用阶段 planner；如果没有这行代码，用户 prompt 无法形成阶段计划。
from .stage_verifier import UniversalStageVerifier  # 新增代码+StageTaskLoop：导入阶段验收器；如果没有这行代码，循环无法判断完成。
from .universal_action_dsl import UniversalActionDslRuntime  # 新增代码+StageTaskLoop：导入现有动作 DSL runtime；如果没有这行代码，批执行会绕过已有 SendInput 桥。
from .universal_real_observation import UniversalRealObservationFrameRuntime  # 新增代码+StageTaskLoop：导入真实只读观察 runtime；如果没有这行代码，生产路径没有观察层。
from .universal_target_session import UniversalTargetSessionRuntime  # 新增代码+StageTaskLoop：导入现有目标 session runtime；如果没有这行代码，生产路径无法绑定 target_ref。


def _stage_loop_bool_policy(policy: str, moment: str) -> bool:  # 新增代码+StageTaskLoop：函数段开始，判断阶段是否需要某个边界观察；如果没有这段函数，观察策略会散落。
    normalized = str(policy or "").strip().lower()  # 新增代码+StageTaskLoop：清洗观察策略；如果没有这行代码，大小写和空白会影响判断。
    return normalized in {moment, "before_and_after_stage"} or (moment == "before_stage" and normalized == "before_each_critical_action")  # 新增代码+StageTaskLoop：返回是否需要观察；如果没有这行代码，阶段会过度观察或漏观察。
# 新增代码+StageTaskLoop：函数段结束，_stage_loop_bool_policy 到此结束；如果没有这个边界说明，初学者不容易看出策略判断范围。


def _stage_loop_session_target_window(session: Mapping[str, Any]) -> dict[str, Any]:  # 新增代码+StageTaskLoop：函数段开始，读取 session 里的目标窗口；如果没有这段函数，观察层拿不到绑定窗口。
    window = session.get("target_window", {}) if isinstance(session, Mapping) else {}  # 新增代码+StageTaskLoop：读取目标窗口字段；如果没有这行代码，None session 会崩溃。
    return dict(window) if isinstance(window, Mapping) else {}  # 新增代码+StageTaskLoop：返回窗口副本；如果没有这行代码，观察或执行可能污染原 session。
# 新增代码+StageTaskLoop：函数段结束，_stage_loop_session_target_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口读取范围。


def _stage_loop_result_dicts(results: list[StageResult]) -> list[dict[str, Any]]:  # 新增代码+StageTaskLoop：函数段开始，序列化阶段结果列表；如果没有这段函数，报告无法 JSON 化。
    return [stage_result_to_dict(result) for result in results]  # 新增代码+StageTaskLoop：返回结果字典列表；如果没有这行代码，acceptance controller 无法读取阶段结果。
# 新增代码+StageTaskLoop：函数段结束，_stage_loop_result_dicts 到此结束；如果没有这个边界说明，初学者不容易看出结果序列化范围。


class UniversalStageTaskLoop:  # 新增代码+StageTaskLoop：类段开始，通用阶段级桌面任务循环；如果没有这个类，复杂 Computer Use 会继续由 primitive 循环驱动。
    def __init__(self, planner: Any | None = None, observation_runtime: Any | None = None, target_runtime: Any | None = None, capability_profile_builder: Callable[[Mapping[str, Any]], AppCapabilityProfile] | None = None, batch_compiler: Callable[[StagePlan, Mapping[str, Any], AppCapabilityProfile], Any] | None = None, batch_executor: Any | None = None, stage_verifier: Any | None = None, max_stage_repairs: int = 1, action_runtime: Any | None = None) -> None:  # 新增代码+StageTaskLoop：函数段开始，注入所有阶段运行依赖；如果没有这段函数，测试和生产无法替换观察/执行层。
        self.planner = planner if planner is not None else UniversalDesktopStagePlanner()  # 新增代码+StageTaskLoop：保存或创建通用 planner；如果没有这行代码，prompt 无法进入阶段计划。
        self.observation_runtime = observation_runtime if observation_runtime is not None else UniversalRealObservationFrameRuntime()  # 新增代码+StageTaskLoop：保存或创建观察 runtime；如果没有这行代码，阶段边界没有屏幕事实。
        self.target_runtime = target_runtime if target_runtime is not None else UniversalTargetSessionRuntime(enable_real_launch=True)  # 新增代码+StageTaskLoop：保存或创建目标 runtime；如果没有这行代码，写动作无法绑定 agent-owned target。
        resolved_action_runtime = action_runtime if action_runtime is not None else UniversalActionDslRuntime(target_runtime=self.target_runtime)  # 新增代码+StageTaskLoop：复用外部动作 runtime 或创建默认 DSL；如果没有这行代码，adapter 注入的受控物理 sender 无法进入阶段批执行。
        self.capability_profile_builder = capability_profile_builder if capability_profile_builder is not None else build_capability_profile  # 新增代码+StageTaskLoop：保存能力画像 builder；如果没有这行代码，阶段编译缺观察能力输入。
        self.batch_compiler = batch_compiler if batch_compiler is not None else compile_stage_to_batch  # 新增代码+StageTaskLoop：保存批编译函数；如果没有这行代码，StagePlan 无法执行。
        self.batch_executor = batch_executor if batch_executor is not None else UniversalActionBatchExecutor(resolved_action_runtime)  # 新增代码+StageTaskLoop：保存批执行器；如果没有这行代码，批动作无法分发到 DSL runtime。
        self.stage_verifier = stage_verifier if stage_verifier is not None else UniversalStageVerifier()  # 新增代码+StageTaskLoop：保存阶段验收器；如果没有这行代码，循环无法判断完成。
        self.max_stage_repairs = max(0, int(max_stage_repairs))  # 新增代码+StageTaskLoop：保存非负修复预算；如果没有这行代码，坏参数可能导致无限重试。
    # 新增代码+StageTaskLoop：函数段结束，UniversalStageTaskLoop.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出依赖注入范围。

    def _open_target_sessions(self, plan: DesktopTaskPlan, target_hint: str = "") -> DesktopTaskRunState:  # 新增代码+StageTaskLoop：函数段开始，为计划目标建立 session 映射；如果没有这段函数，多目标任务无法一对一绑定。
        sessions: dict[str, Any] = {}  # 新增代码+StageTaskLoop：初始化 target_ref 到 session 的映射；如果没有这行代码，后续阶段无法查找目标。
        blocked_refs: list[str] = []  # 新增代码+StageTaskLoop：保存需要用户授权的目标；如果没有这行代码，旧用户窗口会继续进入动作批。
        granted_refs: list[str] = []  # 新增代码+StageTaskLoop：保存用户已授权复用的已有窗口；如果没有这行代码，单实例应用授权状态无法进入 run state。
        launch_hint = str(target_hint or "").strip()  # 新增代码+StageTaskLoop：读取 adapter 传入的通用启动提示；如果没有这行代码，生产路径会拿 text_input_surface 去当应用名启动。
        for target in plan.targets:  # 新增代码+StageTaskLoop：逐个处理目标描述；如果没有这行代码，只有第一个目标会被绑定。
            target_ref = str(target.get("resolved_target_ref", target.get("target_id", "")) or target.get("target_id", ""))  # 新增代码+StageTaskLoop：读取目标引用；如果没有这行代码，目标映射没有键。
            raw_target = launch_hint if launch_hint and len(plan.targets) == 1 else str(target.get("capability_hint", target_ref) or target_ref)  # 新增代码+StageTaskLoop：单目标生产任务优先用真实启动提示，多目标仍保留能力目标；如果没有这行代码，通用 planner 会和启动 resolver 脱节。
            session = dict(self.target_runtime.open_target_session(raw_target))  # 新增代码+StageTaskLoop：调用现有目标 runtime 建立 session；如果没有这行代码，动作无法绑定窗口。
            session["target_ref"] = target_ref  # 新增代码+StageTaskLoop：把计划 target_ref 写入 session；如果没有这行代码，批执行无法校验一对一目标。
            preexisting_window = bool(session.get("target_window_existed_before_launch") or session.get("user_preexisting_window_present"))  # 新增代码+StageTaskLoop：读取目标是否是用户已有窗口；如果没有这行代码，FreshTarget 拒绝事实不会进入阶段层。
            user_granted = bool(session.get("user_granted_existing_window") or session.get("user_authorized_window") or session.get("user_granted_existing_target"))  # 新增代码+StageTaskLoop：读取用户是否授权复用旧窗口；如果没有这行代码，单实例应用授权无法放行。
            if preexisting_window and not user_granted:  # 新增代码+StageTaskLoop：未授权旧窗口必须阻断；如果没有这行代码，stage loop 会继续默认接管用户窗口。
                blocked_refs.append(target_ref)  # 新增代码+StageTaskLoop：记录阻断目标；如果没有这行代码，后续阶段不知道哪个 target_ref 需要用户动作。
            if preexisting_window and user_granted:  # 新增代码+StageTaskLoop：已有窗口已授权时记录授权目标；如果没有这行代码，run state 无法审计单实例授权。
                granted_refs.append(target_ref)  # 新增代码+StageTaskLoop：记录授权目标；如果没有这行代码，最终报告缺 user_granted_existing_target_refs。
            sessions[target_ref] = session  # 新增代码+StageTaskLoop：保存 session 映射；如果没有这行代码，阶段无法查找目标。
        active = next(iter(sessions.keys()), "")  # 新增代码+StageTaskLoop：读取默认活动目标；如果没有这行代码，运行状态缺 active_target_ref。
        return DesktopTaskRunState(target_sessions_by_ref=sessions, active_target_ref=active, user_granted_existing_target_refs=tuple(granted_refs), blocked_target_refs=tuple(blocked_refs))  # 新增代码+StageTaskLoop：返回运行状态快照；如果没有这行代码，调用方拿不到 target map 和旧窗口阻断状态。
    # 新增代码+StageTaskLoop：函数段结束，UniversalStageTaskLoop._open_target_sessions 到此结束；如果没有这个边界说明，初学者不容易看出目标绑定范围。

    def _observe(self, target_ref: str, session: Mapping[str, Any], real_desktop_touched: bool) -> dict[str, Any]:  # 新增代码+StageTaskLoop：函数段开始，执行一次阶段边界观察；如果没有这段函数，观察调用签名会散落。
        observer = getattr(self.observation_runtime, "observe")  # 新增代码+StageTaskLoop：读取观察方法；如果没有这行代码，无法调用注入观察层。
        try:  # 新增代码+StageTaskLoop：优先调用支持绑定窗口的新观察协议；如果没有这行代码，旧 fake 或旧 runtime 兼容性差。
            return dict(observer(target_hint=target_ref, real_desktop_touched=real_desktop_touched, target_window=_stage_loop_session_target_window(session)))  # 新增代码+StageTaskLoop：返回带目标窗口的观察帧；如果没有这行代码，planner 可能看到旧窗口。
        except TypeError:  # 新增代码+StageTaskLoop：兼容只接受 target_hint 的观察 fake；如果没有这行代码，简单测试注入会失败。
            return dict(observer(target_hint=target_ref))  # 新增代码+StageTaskLoop：用旧签名观察；如果没有这行代码，旧观察层无法接入。
    # 新增代码+StageTaskLoop：函数段结束，UniversalStageTaskLoop._observe 到此结束；如果没有这个边界说明，初学者不容易看出观察范围。

    def _profile_for_stage(self, plan: DesktopTaskPlan, frame: Mapping[str, Any]) -> AppCapabilityProfile:  # 新增代码+StageTaskLoop：函数段开始，为阶段生成能力画像并按任务类型保守兜底；如果没有这段函数，测试和弱观察会卡在未知能力。
        profile = self.capability_profile_builder(frame)  # 新增代码+StageTaskLoop：调用能力画像 builder；如果没有这行代码，编译器没有能力输入。
        if not profile.unknown_capabilities:  # 新增代码+StageTaskLoop：已有明确能力时直接返回；如果没有这行代码，兜底会覆盖真实观察。
            return profile  # 新增代码+StageTaskLoop：返回真实能力画像；如果没有这行代码，真实观察结论会丢失。
        if plan.task_kind == "text_entry":  # 新增代码+StageTaskLoop：文本任务弱观察时兜底文本能力；如果没有这行代码，文本任务会卡在 probe。
            return AppCapabilityProfile(has_text_input=True, supports_keyboard_shortcuts_likely=True, evidence=("planner_fallback:text_input",))  # 新增代码+StageTaskLoop：返回文本兜底画像；如果没有这行代码，文本批无法生成。
        if plan.task_kind == "drawing":  # 新增代码+StageTaskLoop：绘图任务弱观察时兜底画布能力；如果没有这行代码，绘图任务无法生成路径批。
            return AppCapabilityProfile(has_canvas_like_region=True, supports_keyboard_shortcuts_likely=True, evidence=("planner_fallback:canvas",))  # 新增代码+StageTaskLoop：返回画布兜底画像；如果没有这行代码，绘图批无法生成。
        if plan.task_kind == "navigation":  # 新增代码+StageTaskLoop：导航任务弱观察时兜底导航能力；如果没有这行代码，导航批无法生成。
            return AppCapabilityProfile(has_text_input=True, has_browser_navigation_surface=True, supports_keyboard_shortcuts_likely=True, evidence=("planner_fallback:navigation",))  # 新增代码+StageTaskLoop：返回导航兜底画像；如果没有这行代码，导航任务会停在未知。
        return profile  # 新增代码+StageTaskLoop：未知任务保持未知能力；如果没有这行代码，未知 GUI 可能被误写。
    # 新增代码+StageTaskLoop：函数段结束，UniversalStageTaskLoop._profile_for_stage 到此结束；如果没有这个边界说明，初学者不容易看出画像兜底范围。

    def run_desktop_task(self, prompt: str, target_hint: str = "") -> dict[str, Any]:  # 新增代码+StageTaskLoop：函数段开始，运行完整通用桌面任务；如果没有这段函数，adapter 无法调用阶段运行时。
        plan = self.planner.plan(prompt, {"target_hint": target_hint})  # 新增代码+StageTaskLoop：生成通用阶段计划；如果没有这行代码，任务没有阶段结构。
        run_state = self._open_target_sessions(plan, target_hint=target_hint)  # 新增代码+StageTaskLoop：建立目标 session 映射并传入启动提示；如果没有这行代码，真实 full mode 可能无法打开用户想要的软件。
        stage_results: list[StageResult] = []  # 新增代码+StageTaskLoop：初始化阶段结果；如果没有这行代码，报告无法汇总完成数。
        observation_count = 0  # 新增代码+StageTaskLoop：初始化观察计数；如果没有这行代码，阶段边界观察不可验收。
        batch_count = 0  # 新增代码+StageTaskLoop：初始化批计数；如果没有这行代码，批执行是否启用不可见。
        primitive_count = 0  # 新增代码+StageTaskLoop：初始化 primitive 计数；如果没有这行代码，动作规模不可见。
        low_level_count = 0  # 新增代码+StageTaskLoop：初始化低层事件计数；如果没有这行代码，真实输入规模不可见。
        max_repairs_reached = False  # 新增代码+StageTaskLoop：初始化修复预算标记；如果没有这行代码，失败原因不清楚。
        needs_user = False  # 新增代码+StageTaskLoop：初始化用户介入标记；如果没有这行代码，最终回答无法区分阻断原因。
        for stage in plan.stages:  # 新增代码+StageTaskLoop：按顺序执行阶段；如果没有这行代码，任务不会推进。
            session = dict(run_state.target_sessions_by_ref.get(stage.target_ref, {}))  # 新增代码+StageTaskLoop：读取阶段目标 session；如果没有这行代码，阶段可能找错窗口。
            if stage.target_ref in set(run_state.blocked_target_refs):  # 新增代码+StageTaskLoop：检查阶段目标是否因旧窗口未授权被阻断；如果没有这行代码，用户已有窗口仍会被动作层尝试。
                needs_user = True  # 新增代码+StageTaskLoop：记录需要用户处理；如果没有这行代码，最终报告无法提示用户关闭或授权窗口。
                stage_results.append(StageResult(status="needs_user", stage_id=stage.stage_id, evidence={"decision": "user_owned_existing_window_requires_grant", "target_ref": stage.target_ref}, message="目标窗口已存在且未获得用户授权，已停止桌面动作。"))  # 新增代码+StageTaskLoop：保存阻断阶段结果；如果没有这行代码，final gate 看不到旧窗口阻断原因。
                break  # 新增代码+StageTaskLoop：停止后续阶段；如果没有这行代码，后续写入阶段可能继续污染旧窗口。
            if stage.stage_kind == "needs_user":  # 新增代码+StageTaskLoop：检查 planner 是否明确要求用户介入；如果没有这行代码，未知 GUI 可能继续进入工具执行。
                needs_user = True  # 新增代码+StageTaskLoop：记录需要用户；如果没有这行代码，最终报告无法解释为什么停止。
                stage_results.append(StageResult(status="needs_user", stage_id=stage.stage_id, evidence={"decision": "planner_requested_user_input", "stage_kind": stage.stage_kind}, message="阶段计划要求用户补充信息或授权，已停止桌面动作。"))  # 新增代码+StageTaskLoop：保存用户介入结果；如果没有这行代码，final gate 看不到停止原因。
                break  # 新增代码+StageTaskLoop：停止后续阶段；如果没有这行代码，未知任务仍可能执行危险动作。
            repairs = 0  # 新增代码+StageTaskLoop：初始化当前阶段修复次数；如果没有这行代码，bounded repair 无法计算。
            while True:  # 新增代码+StageTaskLoop：允许阶段有限修复重跑；如果没有这行代码，needs_repair 无法局部重试。
                before_frame = self._observe(stage.target_ref, session, low_level_count > 0) if _stage_loop_bool_policy(stage.observation_policy, "before_stage") else {}  # 新增代码+StageTaskLoop：按策略执行前置观察；如果没有这行代码，批编译缺屏幕状态。
                observation_count += 1 if before_frame else 0  # 新增代码+StageTaskLoop：累计前置观察；如果没有这行代码，观察证据数量不准。
                profile = self._profile_for_stage(plan, before_frame)  # 新增代码+StageTaskLoop：构建能力画像；如果没有这行代码，批编译没有能力输入。
                batch = self.batch_compiler(stage, before_frame, profile)  # 新增代码+StageTaskLoop：把阶段编译为动作批；如果没有这行代码，阶段无法执行。
                batch_count += 1  # 新增代码+StageTaskLoop：累计批执行尝试；如果没有这行代码，批执行是否启用不可见。
                execution_result = self.batch_executor.execute_batch(session, batch)  # 新增代码+StageTaskLoop：执行动作批；如果没有这行代码，阶段不会触达动作层。
                primitive_count += int(execution_result.evidence.get("primitive_action_count", 0) or 0)  # 新增代码+StageTaskLoop：累计 primitive 数；如果没有这行代码，动作规模不可见。
                low_level_count += int(execution_result.evidence.get("low_level_event_count", 0) or 0)  # 新增代码+StageTaskLoop：累计底层事件数；如果没有这行代码，真实输入证据不可见。
                after_frame = self._observe(stage.target_ref, session, low_level_count > 0) if _stage_loop_bool_policy(stage.observation_policy, "after_stage") else {}  # 新增代码+StageTaskLoop：按策略执行后置观察；如果没有这行代码，verifier 缺完成证据。
                observation_count += 1 if after_frame else 0  # 新增代码+StageTaskLoop：累计后置观察；如果没有这行代码，观察数量不准。
                verified = self.stage_verifier.verify_stage(plan, stage, before_frame, after_frame, execution_result)  # 新增代码+StageTaskLoop：调用阶段验收器；如果没有这行代码，任务是否完成只能靠动作结果猜。
                if verified.status == "needs_repair" and repairs < self.max_stage_repairs:  # 新增代码+StageTaskLoop：检查是否允许局部修复；如果没有这行代码，失败阶段无法重试或会无限重试。
                    repairs += 1  # 新增代码+StageTaskLoop：增加修复次数；如果没有这行代码，修复预算不会推进。
                    continue  # 新增代码+StageTaskLoop：重跑当前阶段；如果没有这行代码，needs_repair 不会触发修复。
                if verified.status == "needs_repair":  # 新增代码+StageTaskLoop：检查修复后仍未完成；如果没有这行代码，预算耗尽不可见。
                    max_repairs_reached = True  # 新增代码+StageTaskLoop：标记修复预算耗尽；如果没有这行代码，报告无法解释未完成。
                if verified.status == "needs_user":  # 新增代码+StageTaskLoop：检查是否需要用户介入；如果没有这行代码，用户阻断不会停止工具。
                    needs_user = True  # 新增代码+StageTaskLoop：标记需要用户；如果没有这行代码，最终回答无法提示用户。
                stage_results.append(verified)  # 新增代码+StageTaskLoop：保存阶段结果；如果没有这行代码，报告无法汇总阶段。
                break  # 新增代码+StageTaskLoop：退出当前阶段循环；如果没有这行代码，已完成阶段会重复执行。
            if stage_results[-1].status in {"blocked", "failed", "needs_user", "needs_repair"}:  # 新增代码+StageTaskLoop：遇到不可继续状态时停止后续阶段；如果没有这行代码，失败后可能继续污染桌面。
                break  # 新增代码+StageTaskLoop：停止任务循环；如果没有这行代码，后续阶段会在坏状态下执行。
        completed_stage_count = sum(1 for result in stage_results if result.status == "completed")  # 新增代码+StageTaskLoop：统计完成阶段数；如果没有这行代码，final gate 缺关键字段。
        target_sessions = list(run_state.target_sessions_by_ref.values())  # 新增代码+StageTaskLoop：收集所有目标 session；如果没有这行代码，报告无法汇总窗口绑定事实。
        owned_window_verified = bool(target_sessions and all(bool(dict(session).get("target_identity_bound") or dict(session).get("target_identity_verified") or dict(session).get("visible_window_verified") or dict(session).get("session_ready")) for session in target_sessions if isinstance(session, Mapping)))  # 新增代码+StageTaskLoop：汇总目标窗口是否已被绑定；如果没有这行代码，adapter 只能猜测动作是否有目标身份。
        target_ref_one_to_one = bool(len(run_state.target_sessions_by_ref) == len(set(run_state.target_sessions_by_ref.keys())))  # 新增代码+StageTaskLoop：确认 target_ref 没有重复；如果没有这行代码，多目标写入可能共享错误窗口还不被发现。
        desktop_task_completed = bool(completed_stage_count == len(plan.stages) and len(plan.stages) > 0)  # 新增代码+StageTaskLoop：判断任务是否整体完成；如果没有这行代码，最终回答无法依据结构化结果。
        desktop_task_incomplete = not desktop_task_completed  # 新增代码+StageTaskLoop：判断任务是否未完成；如果没有这行代码，final gate 需要反推。
        return {"model": "universal_stage_task_loop", "ok": desktop_task_completed, "decision": "desktop_task_completed" if desktop_task_completed else "desktop_task_incomplete", "universal_stage_task_loop_used": True, "desktop_task_plan_created": True, "desktop_task_plan": desktop_task_plan_to_dict(plan), "stage_count": len(plan.stages), "completed_stage_count": completed_stage_count, "stage_results": _stage_loop_result_dicts(stage_results), "desktop_task_completed": desktop_task_completed, "desktop_task_incomplete": desktop_task_incomplete, "stage_boundary_observation_used": observation_count > 0, "observation_frame_count": observation_count, "batch_execution_used": batch_count > 0, "batch_count": batch_count, "primitive_action_count": primitive_count, "low_level_event_count": low_level_count, "max_stage_repairs_reached": max_repairs_reached, "needs_user": needs_user, "owned_window_verified": owned_window_verified, "target_ref_one_to_one": target_ref_one_to_one, "target_session_count": len(run_state.target_sessions_by_ref), "run_state": {"target_sessions_by_ref": list(run_state.target_sessions_by_ref.keys()), "active_target_ref": run_state.active_target_ref, "stage_target_ref": run_state.stage_target_ref, "user_granted_existing_target_refs": list(run_state.user_granted_existing_target_refs), "blocked_target_refs": list(run_state.blocked_target_refs)}}  # 新增代码+StageTaskLoop：返回结构化任务报告；如果没有这行代码，adapter 和 final gate 拿不到阶段证据。
    # 新增代码+StageTaskLoop：函数段结束，UniversalStageTaskLoop.run_desktop_task 到此结束；如果没有这个边界说明，初学者不容易看出主循环范围。
# 新增代码+StageTaskLoop：类段结束，UniversalStageTaskLoop 到此结束；如果没有这个边界说明，初学者不容易看出阶段运行时范围。


__all__ = ["UniversalStageTaskLoop"]  # 新增代码+StageTaskLoop：声明公开接口；如果没有这行代码，通配导入会暴露内部 helper。
