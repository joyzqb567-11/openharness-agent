"""Verify universal Computer Use stages from observation evidence."""  # 新增代码+StageVerifier：说明本文件负责阶段完成判断；如果没有这行代码，读者会误以为事件发送等于任务完成。
from __future__ import annotations  # 新增代码+StageVerifier：启用延迟类型解析；如果没有这行代码，类型注解更容易在导入阶段失败。

import json  # 新增代码+StageVerifier：导入 JSON 用于压缩观察帧搜索；如果没有这行代码，嵌套观察文本难以统一检查。
from typing import Any, Mapping  # 新增代码+StageVerifier：导入 JSON 风格类型；如果没有这行代码，观察帧和计划接口不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import DesktopTaskPlan, StagePlan, StageResult  # 新增代码+StageVerifier：导入通用计划、阶段和结果模型；如果没有这行代码，验收器无法返回统一状态。


def _stage_verifier_blob(frame: Mapping[str, Any]) -> str:  # 新增代码+StageVerifier：函数段开始，把观察帧压成可搜索文本；如果没有这段函数，嵌套 UIA 文本难以匹配。
    try:  # 新增代码+StageVerifier：尝试 JSON 序列化观察帧；如果没有这行代码，dict 观察无法统一处理。
        return json.dumps(frame, ensure_ascii=False, sort_keys=True, default=str).lower()  # 新增代码+StageVerifier：返回小写观察文本；如果没有这行代码，文本匹配会受大小写影响。
    except TypeError:  # 新增代码+StageVerifier：处理不可序列化对象；如果没有这行代码，坏观察帧会中断验收。
        return str(frame).lower()  # 新增代码+StageVerifier：回退字符串表示；如果没有这行代码，坏观察帧没有可搜索内容。
# 新增代码+StageVerifier：函数段结束，_stage_verifier_blob 到此结束；如果没有这个边界说明，初学者不容易看出观察文本范围。


def _stage_verifier_truthy(frame: Mapping[str, Any], keys: tuple[str, ...]) -> bool:  # 新增代码+StageVerifier：函数段开始，检查观察帧是否含任一真值字段；如果没有这段函数，多处完成判断会重复。
    return any(bool(frame.get(key, False)) for key in keys)  # 新增代码+StageVerifier：任一字段为真即通过；如果没有这行代码，调用方无法简洁表达观察证据。
# 新增代码+StageVerifier：函数段结束，_stage_verifier_truthy 到此结束；如果没有这个边界说明，初学者不容易看出真值字段范围。


def _stage_verifier_saved(frame: Mapping[str, Any]) -> bool:  # 新增代码+LayeredVerifierCriteria：函数段开始，统一判断资源是否已经保存；如果没有这段函数，最终验收和保存阶段会各自猜保存字段。
    save_dialog_state = frame.get("save_dialog_state", {}) if isinstance(frame.get("save_dialog_state", {}), Mapping) else {}  # 新增代码+LayeredVerifierCriteria：读取结构化保存对话框状态；如果没有这行代码，ObservationFacts 的保存完成字段不会被最终验收使用。
    return _stage_verifier_truthy(frame, ("saved_resource_exists", "save_dialog_completed", "resource_commit_verified", "file_saved", "document_saved")) or bool(save_dialog_state.get("completed", False))  # 新增代码+LayeredVerifierCriteria：返回保存是否完成；如果没有这行代码，最终阶段可能把未保存任务误判成功。
# 新增代码+LayeredVerifierCriteria：函数段结束，_stage_verifier_saved 到此结束；如果没有这个边界说明，用户不容易看出保存验证范围。


def _stage_verifier_text_visible(frame: Mapping[str, Any], requested_text: str = "") -> bool:  # 新增代码+LayeredVerifierCriteria：函数段开始，统一判断文本是否可见；如果没有这段函数，文本成功标准会和文本阶段验证不一致。
    requested = str(requested_text or "").lower()  # 新增代码+LayeredVerifierCriteria：清洗期望文本；如果没有这行代码，大小写会影响匹配。
    blob = _stage_verifier_blob(frame)  # 新增代码+LayeredVerifierCriteria：把观察事实压成可搜索文本；如果没有这行代码，嵌套 UIA 文本无法匹配成功标准。
    visible_text = str(frame.get("visible_text_summary", frame.get("visible_text", frame.get("text_content", ""))) or "").strip()  # 新增代码+LayeredVerifierCriteria：读取结构化可见文本；如果没有这行代码，ObservationFacts 的文本摘要不会进入最终验收。
    return bool(frame.get("requested_text_visible", False) or frame.get("text_content_matches", False) or (requested and requested in blob) or (not requested and visible_text))  # 新增代码+LayeredVerifierCriteria：返回文本是否满足；如果没有这行代码，最终阶段只能看 observe 是否成功。
# 新增代码+LayeredVerifierCriteria：函数段结束，_stage_verifier_text_visible 到此结束；如果没有这个边界说明，用户不容易看出文本验证范围。


def _stage_verifier_drawing_visible(frame: Mapping[str, Any]) -> bool:  # 新增代码+LayeredVerifierCriteria：函数段开始，统一判断绘图是否可见；如果没有这段函数，最终验收可能忽略画布内容质量。
    visual_summary = str(frame.get("visual_change_summary", "") or "").lower()  # 新增代码+LayeredVerifierCriteria：读取视觉变化摘要；如果没有这行代码，ObservationFacts 的视觉摘要不会参与判断。
    changed = _stage_verifier_truthy(frame, ("canvas_changed_after_actions", "canvas_changed", "canvas_not_blank")) or "canvas_changed" in visual_summary or "changed" in visual_summary  # 新增代码+LayeredVerifierCriteria：判断画布是否变化；如果没有这行代码，鼠标事件可能被误当绘图完成。
    structure = bool(frame.get("visual_primitives") or frame.get("visual_structure_present") or frame.get("colored_region_count", 0) or "structure" in visual_summary or "color" in visual_summary)  # 新增代码+LayeredVerifierCriteria：判断是否有结构或颜色；如果没有这行代码，单条乱线可能被误当复杂绘图完成。
    return bool(changed and structure)  # 新增代码+LayeredVerifierCriteria：同时满足变化和结构才算绘图可见；如果没有这行代码，最终阶段质量门槛过低。
# 新增代码+LayeredVerifierCriteria：函数段结束，_stage_verifier_drawing_visible 到此结束；如果没有这个边界说明，用户不容易看出绘图验证范围。


def _stage_verifier_missing_success_criteria(plan: DesktopTaskPlan, stage: StagePlan, after: Mapping[str, Any]) -> list[str]:  # 新增代码+LayeredVerifierCriteria：函数段开始，根据 intent 成功标准找缺失项；如果没有这段函数，verifier 只会按 stage_kind 粗略验收。
    criteria = [str(item or "").strip().lower() for item in list(plan.success_criteria or ()) if str(item or "").strip()]  # 新增代码+LayeredVerifierCriteria：读取并清洗成功标准；如果没有这行代码，空标准会污染缺失判断。
    verifier = dict(stage.verifier or {})  # 新增代码+LayeredVerifierCriteria：读取阶段 verifier 配置；如果没有这行代码，requested_text 不能参与文本判断。
    missing: list[str] = []  # 新增代码+LayeredVerifierCriteria：初始化缺失列表；如果没有这行代码，函数无法累计多个未满足标准。
    for criterion in criteria:  # 新增代码+LayeredVerifierCriteria：逐条检查成功标准；如果没有这行代码，只能检查第一条或完全不检查。
        if any(token in criterion for token in ("resource_commit_verified", "saved_to_desktop", "saved", "save")) and not _stage_verifier_saved(after):  # 新增代码+LayeredVerifierCriteria：保存类标准必须有保存观察证据；如果没有这行代码，按下 Ctrl+S 会被误当保存完成。
            missing.append(criterion)  # 新增代码+LayeredVerifierCriteria：记录缺失保存标准；如果没有这行代码，日志无法告诉用户缺哪项。
        if any(token in criterion for token in ("requested_text_visible", "text_visible", "text_entered", "content_visible")) and not _stage_verifier_text_visible(after, str(verifier.get("requested_text", ""))):  # 新增代码+LayeredVerifierCriteria：文本类标准必须有可见文本证据；如果没有这行代码，输入失败可能被 final。
            missing.append(criterion)  # 新增代码+LayeredVerifierCriteria：记录缺失文本标准；如果没有这行代码，反思层不知道修什么。
        if any(token in criterion for token in ("drawing_visible", "canvas_changed", "visual_structure", "colored_region")) and not _stage_verifier_drawing_visible(after):  # 新增代码+LayeredVerifierCriteria：绘图类标准必须有视觉证据；如果没有这行代码，复杂绘图会被低层事件数误导。
            missing.append(criterion)  # 新增代码+LayeredVerifierCriteria：记录缺失绘图标准；如果没有这行代码，后续修复缺少明确目标。
    return missing  # 新增代码+LayeredVerifierCriteria：返回所有缺失标准；如果没有这行代码，调用方拿不到判断结果。
# 新增代码+LayeredVerifierCriteria：函数段结束，_stage_verifier_missing_success_criteria 到此结束；如果没有这个边界说明，用户不容易看出成功标准检查范围。


def _stage_verifier_needs_repair(stage: StagePlan, reason: str, execution_result: StageResult, evidence: Mapping[str, Any] | None = None) -> StageResult:  # 新增代码+StageVerifier：函数段开始，构造需要修复结果；如果没有这段函数，未完成路径字段会不一致。
    payload = {"decision": reason, "execution_status": execution_result.status, "low_level_event_count": execution_result.evidence.get("low_level_event_count", 0)}  # 新增代码+StageVerifier：构造基础证据；如果没有这行代码，未完成原因不可审计。
    payload.update(dict(evidence or {}))  # 新增代码+StageVerifier：合并附加证据；如果没有这行代码，调用方提供的观察线索会丢失。
    return StageResult(status="needs_repair", stage_id=stage.stage_id, evidence=payload, message="阶段观察证据不足，需要局部修复。")  # 新增代码+StageVerifier：返回需要修复状态；如果没有这行代码，未完成阶段可能误过。
# 新增代码+StageVerifier：函数段结束，_stage_verifier_needs_repair 到此结束；如果没有这个边界说明，初学者不容易看出修复结果范围。


class UniversalStageVerifier:  # 新增代码+StageVerifier：类段开始，定义通用阶段验收器；如果没有这个类，阶段循环没有可靠完成判断。
    def verify_stage(self, plan: DesktopTaskPlan, stage: StagePlan, before_frame: Mapping[str, Any], after_frame: Mapping[str, Any], execution_result: StageResult) -> StageResult:  # 新增代码+StageVerifier：函数段开始，根据计划、观察和执行结果判断阶段状态；如果没有这段函数，final gate 没有事实来源。
        _ = before_frame  # 新增代码+StageVerifier：保留前置观察参数供未来差分验证；如果没有这行代码，读者会以为前置观察被遗漏。
        after = after_frame if isinstance(after_frame, Mapping) else {}  # 新增代码+StageVerifier：规范化后置观察；如果没有这行代码，None 观察会导致异常。
        if _stage_verifier_truthy(after, ("target_ambiguous", "target_drift_blocks_action", "wrong_target_visible")):  # 新增代码+StageVerifier：目标不明确或漂移时硬阻断；如果没有这行代码，错误窗口可能被误判完成。
            return StageResult(status="blocked", stage_id=stage.stage_id, evidence={"decision": "target_not_safe_for_verification", "after_observation": dict(after)}, message="目标窗口不明确或发生漂移。")  # 新增代码+StageVerifier：返回阻断结果；如果没有这行代码，目标安全失败不可审计。
        if execution_result.status in {"blocked", "needs_user", "failed"}:  # 新增代码+StageVerifier：执行层已经硬失败时不伪造成功；如果没有这行代码，失败动作可能被观察层误盖过。
            return execution_result  # 新增代码+StageVerifier：直接返回执行结果；如果没有这行代码，底层失败会被重写。
        if stage.stage_kind in {"prepare_target", "probe_capabilities"} and execution_result.status == "completed":  # 新增代码+StageVerifier：准备和探测阶段只要求执行成功；如果没有这行代码，安全阶段会被过度要求业务证据。
            return StageResult(status="completed", stage_id=stage.stage_id, evidence={"decision": "stage_preparation_or_probe_completed", **dict(execution_result.evidence)}, message="准备或探测阶段完成。")  # 新增代码+StageVerifier：返回准备/探测完成；如果没有这行代码，阶段循环会卡在观察类阶段。
        if stage.stage_kind == "commit_resource":  # 新增代码+StageVerifier：保存阶段需要资源提交证据；如果没有这行代码，按下快捷键会被误当保存成功。
            return self._verify_commit_stage(stage, after, execution_result)  # 新增代码+StageVerifier：委托保存验证；如果没有这行代码，保存规则会散落。
        if stage.stage_kind == "verify_result":  # 新增代码+StageVerifier：最终验证阶段检查整体观察是否安全；如果没有这行代码，最终阶段没有明确收束。
            missing = _stage_verifier_missing_success_criteria(plan, stage, after)  # 新增代码+LayeredVerifierCriteria：检查 intent 成功标准是否满足；如果没有这行代码，最终观察成功会掩盖业务未完成。
            if missing:  # 新增代码+LayeredVerifierCriteria：发现缺失标准时不能完成；如果没有这行代码，模型可能 final 一个未保存或未绘制的任务。
                return _stage_verifier_needs_repair(stage, "missing_requirements", execution_result, {"missing_requirements": missing})  # 新增代码+LayeredVerifierCriteria：返回缺失标准证据；如果没有这行代码，final gate 看不到 machine-readable 原因。
            return StageResult(status="completed", stage_id=stage.stage_id, evidence={"decision": "verify_stage_observation_available", **dict(execution_result.evidence)}, message="验证阶段完成。") if execution_result.status == "completed" else execution_result  # 新增代码+StageVerifier：返回验证完成或执行失败；如果没有这行代码，最终阶段可能无结果。
        if stage.stage_kind != "perform_content_work":  # 新增代码+StageVerifier：未知阶段不直接成功；如果没有这行代码，未定义阶段可能误过。
            return _stage_verifier_needs_repair(stage, "unsupported_stage_kind_for_verifier", execution_result)  # 新增代码+StageVerifier：返回需要修复；如果没有这行代码，未知阶段缺保守出口。
        if plan.task_kind == "text_entry":  # 新增代码+StageVerifier：文本任务走文本观察验证；如果没有这行代码，文本完成只能看事件数。
            return self._verify_text_stage(stage, after, execution_result)  # 新增代码+StageVerifier：委托文本验证；如果没有这行代码，文本规则会散落。
        if plan.task_kind == "drawing":  # 新增代码+StageVerifier：绘图任务走画布观察验证；如果没有这行代码，绘图完成只能看鼠标事件。
            return self._verify_drawing_stage(stage, after, execution_result)  # 新增代码+StageVerifier：委托绘图验证；如果没有这行代码，绘图规则会散落。
        if plan.task_kind == "navigation":  # 新增代码+StageVerifier：导航任务走结果可见验证；如果没有这行代码，导航完成可能只打开窗口。
            return self._verify_navigation_stage(stage, after, execution_result)  # 新增代码+StageVerifier：委托导航验证；如果没有这行代码，导航规则会散落。
        if plan.task_kind == "multi_app" and execution_result.status == "completed":  # 新增代码+StageVerifier：多窗口中间阶段先按批结果和目标安全通过；如果没有这行代码，多目标阶段会缺基本验收。
            return StageResult(status="completed", stage_id=stage.stage_id, evidence={"decision": "multi_target_stage_completed", **dict(execution_result.evidence)}, message="多目标阶段完成。")  # 新增代码+StageVerifier：返回多目标阶段完成；如果没有这行代码，多目标任务无法推进。
        return _stage_verifier_needs_repair(stage, "no_generic_completion_evidence", execution_result)  # 新增代码+StageVerifier：默认保守返回需要修复；如果没有这行代码，未知任务可能误成功。
    # 新增代码+StageVerifier：函数段结束，UniversalStageVerifier.verify_stage 到此结束；如果没有这个边界说明，初学者不容易看出主验收范围。

    def _verify_text_stage(self, stage: StagePlan, after: Mapping[str, Any], execution_result: StageResult) -> StageResult:  # 新增代码+StageVerifier：函数段开始，验证文本阶段；如果没有这段函数，文本验收会依赖事件数。
        requested = str(stage.verifier.get("requested_text", "") or "").lower()  # 新增代码+StageVerifier：读取期望文本；如果没有这行代码，无法比对用户要求。
        matched = _stage_verifier_text_visible(after, requested) and execution_result.status == "completed"  # 修改代码+LayeredVerifierCriteria：复用统一文本可见判断并要求执行成功；如果没有这行代码，文本阶段和最终标准会不一致。
        if matched:  # 新增代码+StageVerifier：检查文本是否完成；如果没有这行代码，完成和未完成无法分支。
            return StageResult(status="completed", stage_id=stage.stage_id, evidence={"decision": "text_observation_verified", **dict(execution_result.evidence)}, message="文本阶段已通过观察验证。")  # 新增代码+StageVerifier：返回文本完成；如果没有这行代码，文本阶段无法结束。
        return _stage_verifier_needs_repair(stage, "text_not_visible_after_batch", execution_result)  # 新增代码+StageVerifier：文本不可见则需要修复；如果没有这行代码，文本任务会误完成。
    # 新增代码+StageVerifier：函数段结束，UniversalStageVerifier._verify_text_stage 到此结束；如果没有这个边界说明，初学者不容易看出文本验收范围。

    def _verify_drawing_stage(self, stage: StagePlan, after: Mapping[str, Any], execution_result: StageResult) -> StageResult:  # 新增代码+StageVerifier：函数段开始，验证绘图阶段；如果没有这段函数，绘图验收会只看鼠标事件。
        changed = _stage_verifier_drawing_visible(after)  # 修改代码+LayeredVerifierCriteria：复用统一绘图可见判断；如果没有这行代码，绘图阶段和最终标准会不一致。
        structure = changed  # 修改代码+LayeredVerifierCriteria：保留旧证据字段名并表达结构已满足；如果没有这行代码，旧测试和反思层证据字段会缺失。
        if changed and execution_result.status == "completed":  # 修改代码+LayeredVerifierCriteria：画布满足且执行成功才完成；如果没有这行代码，失败动作可能被旧截图误盖过。
            return StageResult(status="completed", stage_id=stage.stage_id, evidence={"decision": "drawing_observation_verified", **dict(execution_result.evidence)}, message="绘图阶段已通过观察验证。")  # 新增代码+StageVerifier：返回绘图完成；如果没有这行代码，绘图阶段无法结束。
        return _stage_verifier_needs_repair(stage, "drawing_visual_evidence_incomplete", execution_result, {"canvas_changed": changed, "visual_structure": structure})  # 新增代码+StageVerifier：绘图证据不足则需要修复；如果没有这行代码，未完成绘图可能 final。
    # 新增代码+StageVerifier：函数段结束，UniversalStageVerifier._verify_drawing_stage 到此结束；如果没有这个边界说明，初学者不容易看出绘图验收范围。

    def _verify_navigation_stage(self, stage: StagePlan, after: Mapping[str, Any], execution_result: StageResult) -> StageResult:  # 新增代码+StageVerifier：函数段开始，验证导航阶段；如果没有这段函数，导航任务可能只提交了键盘。
        if _stage_verifier_truthy(after, ("navigation_result_visible", "search_results_visible", "page_loaded")) or bool(after.get("visible_text")):  # 新增代码+StageVerifier：检查结果可见或页面加载证据；如果没有这行代码，导航完成无法证明。
            return StageResult(status="completed", stage_id=stage.stage_id, evidence={"decision": "navigation_observation_verified", **dict(execution_result.evidence)}, message="导航阶段已通过观察验证。")  # 新增代码+StageVerifier：返回导航完成；如果没有这行代码，导航阶段无法结束。
        return _stage_verifier_needs_repair(stage, "navigation_result_not_visible", execution_result)  # 新增代码+StageVerifier：导航证据不足则修复；如果没有这行代码，导航失败可能误过。
    # 新增代码+StageVerifier：函数段结束，UniversalStageVerifier._verify_navigation_stage 到此结束；如果没有这个边界说明，初学者不容易看出导航验收范围。

    def _verify_commit_stage(self, stage: StagePlan, after: Mapping[str, Any], execution_result: StageResult) -> StageResult:  # 新增代码+StageVerifier：函数段开始，验证资源提交阶段；如果没有这段函数，保存动作会缺完成证据。
        saved = _stage_verifier_saved(after)  # 修改代码+LayeredVerifierCriteria：复用统一保存判断；如果没有这行代码，保存阶段和最终标准会不一致。
        if saved:  # 新增代码+StageVerifier：检查保存是否完成；如果没有这行代码，完成和未完成无法分支。
            return StageResult(status="completed", stage_id=stage.stage_id, evidence={"decision": "resource_commit_verified", **dict(execution_result.evidence)}, message="资源提交阶段已通过观察验证。")  # 新增代码+StageVerifier：返回保存完成；如果没有这行代码，保存阶段无法结束。
        return _stage_verifier_needs_repair(stage, "resource_commit_not_verified", execution_result)  # 新增代码+StageVerifier：保存未验证则需要修复；如果没有这行代码，文件未保存也可能 final。
    # 新增代码+StageVerifier：函数段结束，UniversalStageVerifier._verify_commit_stage 到此结束；如果没有这个边界说明，初学者不容易看出保存验收范围。
# 新增代码+StageVerifier：类段结束，UniversalStageVerifier 到此结束；如果没有这个边界说明，初学者不容易看出验收器范围。


__all__ = ["UniversalStageVerifier"]  # 新增代码+StageVerifier：声明公开接口；如果没有这行代码，通配导入会暴露内部 helper。
