"""Compile universal Computer Use stages into executable action batches."""  # 新增代码+StageBatchCompiler：说明本文件负责阶段到批动作编译；如果没有这行代码，读者会误以为这里直接控制具体软件。
from __future__ import annotations  # 新增代码+StageBatchCompiler：启用延迟类型解析；如果没有这行代码，类型注解更容易在导入阶段失败。

from typing import Any, Mapping  # 新增代码+StageBatchCompiler：导入 JSON 风格类型；如果没有这行代码，观察帧和 verifier 配置边界不清。

from learning_agent.computer_use_mcp_v2.windows_runtime.capability_profile import AppCapabilityProfile  # 新增代码+StageBatchCompiler：导入通用能力画像；如果没有这行代码，编译器会回到应用名判断。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import ActionBatch, StagePlan  # 新增代码+StageBatchCompiler：导入阶段和批模型；如果没有这行代码，编译结果会变成散乱 dict。


EXISTING_RESOURCE_TITLE_MARKERS = (".txt", ".md", ".doc", ".docx", ".rtf", ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".svg", ".pdf", ".xlsx", ".xls", ".ppt", ".pptx", ".csv", ".json", ".py", ".js", ".ts", ".html", ".css")  # 新增代码+FreshResource：定义通用文件标题标记；如果没有这行代码，新启动窗口恢复旧文件时阶段层无法识别已有资源。
FRESH_RESOURCE_TITLE_MARKERS = ("untitled", "new", "blank", "无标题", "未命名", "新建")  # 新增代码+FreshResource：定义通用新资源标题标记；如果没有这行代码，空白新文档可能被误判为旧资源。


def _stage_compiler_safe_int(value: Any, default: int) -> int:  # 新增代码+StageBatchCompiler：函数段开始，安全读取尺寸数值；如果没有这段函数，坏观察帧会让编译器崩溃。
    try:  # 新增代码+StageBatchCompiler：尝试转换整数；如果没有这行代码，字符串尺寸无法兼容。
        return int(value)  # 新增代码+StageBatchCompiler：返回整数值；如果没有这行代码，调用方拿不到坐标基准。
    except (TypeError, ValueError):  # 新增代码+StageBatchCompiler：捕获空值和非数字；如果没有这行代码，坏字段会中断整个任务。
        return int(default)  # 新增代码+StageBatchCompiler：返回兜底值；如果没有这行代码，编译器无法保守继续。
# 新增代码+StageBatchCompiler：函数段结束，_stage_compiler_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出数值兜底范围。


def _stage_compiler_window_size(observation_frame: Mapping[str, Any]) -> tuple[int, int]:  # 新增代码+StageBatchCompiler：函数段开始，从观察帧读取窗口尺寸；如果没有这段函数，指针路径无法按窗口缩放。
    canvas_regions = observation_frame.get("canvas_regions", []) if isinstance(observation_frame, Mapping) else []  # 新增代码+ObservationFactsCompiler：优先读取结构化画布区域；如果没有这行代码，facts 输入会退回默认窗口尺寸。
    if isinstance(canvas_regions, list) and canvas_regions:  # 新增代码+ObservationFactsCompiler：检查 facts 是否提供画布区域；如果没有这行代码，空列表会导致索引错误。
        bounds = canvas_regions[0].get("bounds", {}) if isinstance(canvas_regions[0], Mapping) else {}  # 新增代码+ObservationFactsCompiler：读取第一个画布区域边界；如果没有这行代码，绘图批无法按画布缩放。
        width_from_canvas = _stage_compiler_safe_int(bounds.get("width", 0), 0)  # 新增代码+ObservationFactsCompiler：读取画布宽度；如果没有这行代码，facts 中 width 不会生效。
        height_from_canvas = _stage_compiler_safe_int(bounds.get("height", 0), 0)  # 新增代码+ObservationFactsCompiler：读取画布高度；如果没有这行代码，facts 中 height 不会生效。
        if width_from_canvas > 0 and height_from_canvas > 0:  # 新增代码+ObservationFactsCompiler：确认画布尺寸有效；如果没有这行代码，坏 facts 会覆盖安全默认值。
            return max(320, width_from_canvas), max(240, height_from_canvas)  # 新增代码+ObservationFactsCompiler：返回画布尺寸；如果没有这行代码，绘图阶段无法利用结构化观察事实。
    target_window = observation_frame.get("target_window", {}) if isinstance(observation_frame, Mapping) else {}  # 新增代码+StageBatchCompiler：读取目标窗口摘要；如果没有这行代码，编译器没有窗口来源。
    rect = target_window.get("rect", {}) if isinstance(target_window, Mapping) else {}  # 新增代码+StageBatchCompiler：读取窗口矩形；如果没有这行代码，尺寸推导无输入。
    width = max(320, _stage_compiler_safe_int(rect.get("width", 0), 800))  # 新增代码+StageBatchCompiler：读取或兜底窗口宽度；如果没有这行代码，路径可能落到窗口外。
    height = max(240, _stage_compiler_safe_int(rect.get("height", 0), 500))  # 新增代码+StageBatchCompiler：读取或兜底窗口高度；如果没有这行代码，路径可能落到工具栏或窗口外。
    return width, height  # 新增代码+StageBatchCompiler：返回尺寸元组；如果没有这行代码，调用方拿不到坐标。
# 新增代码+StageBatchCompiler：函数段结束，_stage_compiler_window_size 到此结束；如果没有这个边界说明，初学者不容易看出尺寸推导范围。


def _stage_compiler_target_title(observation_frame: Mapping[str, Any]) -> str:  # 新增代码+FreshResource：函数段开始，从观察帧读取目标窗口标题；如果没有这段函数，编译器不知道当前资源是不是旧文件。
    target_window = observation_frame.get("target_window", {}) if isinstance(observation_frame, Mapping) else {}  # 新增代码+FreshResource：读取目标窗口摘要；如果没有这行代码，标题读取没有来源。
    if not isinstance(target_window, Mapping):  # 新增代码+FreshResource：检查目标窗口是否是字典；如果没有这行代码，坏观察帧会导致属性读取异常。
        return ""  # 新增代码+FreshResource：窗口摘要异常时返回空标题；如果没有这行代码，准备阶段无法保守继续。
    title = target_window.get("title_preview", target_window.get("title", ""))  # 新增代码+FreshResource：优先读取脱敏短标题再读取完整标题；如果没有这行代码，观察层不同字段会互不兼容。
    return str(title or "").strip()  # 新增代码+FreshResource：返回清洗后的标题；如果没有这行代码，空白标题和 None 会污染判断。
# 新增代码+FreshResource：函数段结束，_stage_compiler_target_title 到此结束；如果没有这个边界说明，初学者不容易看出标题来源范围。


def _stage_compiler_title_looks_fresh(title: str) -> bool:  # 新增代码+FreshResource：函数段开始，判断标题是否像新资源；如果没有这段函数，已有资源和空白资源会混在一起。
    normalized = str(title or "").strip().lower()  # 新增代码+FreshResource：清洗并小写标题；如果没有这行代码，中英文大小写和空白会影响判断。
    if not normalized:  # 新增代码+FreshResource：空标题无法证明是旧文件；如果没有这行代码，无标题窗口可能被误触发新建。
        return True  # 新增代码+FreshResource：空标题按可继续处理；如果没有这行代码，弱观察会阻塞所有通用任务。
    return any(marker in normalized for marker in FRESH_RESOURCE_TITLE_MARKERS)  # 新增代码+FreshResource：命中新建类词则认为资源新鲜；如果没有这行代码，通用新文档会被误判成旧文档。
# 新增代码+FreshResource：函数段结束，_stage_compiler_title_looks_fresh 到此结束；如果没有这个边界说明，初学者不容易看出新资源判断范围。


def _stage_compiler_title_looks_existing_resource(title: str) -> bool:  # 新增代码+FreshResource：函数段开始，判断标题是否像已打开的用户文件；如果没有这段函数，新进程恢复旧文档会绕过 FreshTarget。
    normalized = str(title or "").strip().lower()  # 新增代码+FreshResource：清洗并小写标题；如果没有这行代码，扩展名判断会不稳定。
    if _stage_compiler_title_looks_fresh(normalized):  # 新增代码+FreshResource：先排除明显新资源；如果没有这行代码，含 new 的标题可能被误判旧文件。
        return False  # 新增代码+FreshResource：新资源不触发二次新建；如果没有这行代码，空白窗口会多按一次新建。
    return any(marker in normalized for marker in EXISTING_RESOURCE_TITLE_MARKERS)  # 新增代码+FreshResource：标题含常见扩展名则视为已有资源；如果没有这行代码，旧文件标题无法触发通用新建。
# 新增代码+FreshResource：函数段结束，_stage_compiler_title_looks_existing_resource 到此结束；如果没有这个边界说明，初学者不容易看出旧资源判断范围。


def _stage_compiler_prepare_actions(stage: StagePlan, observation_frame: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:  # 新增代码+FreshResource：函数段开始，生成通用目标准备动作；如果没有这段函数，准备阶段只能聚焦窗口，无法清理旧资源状态。
    actions: list[dict[str, Any]] = [{"type": "focus_window"}]  # 新增代码+FreshResource：准备动作始终先聚焦目标窗口；如果没有这行代码，后续新建快捷键可能发到错误窗口。
    title = _stage_compiler_target_title(observation_frame)  # 新增代码+FreshResource：读取当前目标标题；如果没有这行代码，无法判断是否恢复了旧文件。
    fresh_required = bool(stage.verifier.get("fresh_resource_required", False))  # 新增代码+FreshResource：读取 planner 声明的新资源要求；如果没有这行代码，所有准备阶段都会被错误新建。
    if fresh_required and _stage_compiler_title_looks_existing_resource(title):  # 新增代码+FreshResource：只有要求新资源且标题像旧文件时才触发；如果没有这行代码，通用任务会接管恢复的旧文件。
        actions.append({"type": "hotkey", "keys": ["CTRL", "N"], "critical": True})  # 新增代码+FreshResource：通过应用内通用新建快捷键创建新资源；如果没有这行代码，新窗口仍可能停留在旧文件内容上。
        actions.append({"type": "wait", "milliseconds": 300})  # 新增代码+FreshResource：等待应用完成新建资源切换；如果没有这行代码，后续输入可能抢在新资源创建前发生。
        actions.append({"type": "observe"})  # 新增代码+FreshResource：追加观察确认资源状态；如果没有这行代码，阶段证据无法解释为什么已脱离旧文件。
    return tuple(actions)  # 新增代码+FreshResource：返回准备动作批；如果没有这行代码，编译器拿不到最终动作列表。
# 新增代码+FreshResource：函数段结束，_stage_compiler_prepare_actions 到此结束；如果没有这个边界说明，初学者不容易看出目标准备范围。


def _stage_compiler_prepare_guardrails(stage: StagePlan, observation_frame: Mapping[str, Any]) -> dict[str, Any]:  # 新增代码+FreshResource：函数段开始，生成准备阶段安全证据；如果没有这段函数，验收无法看到新资源判断原因。
    title = _stage_compiler_target_title(observation_frame)  # 新增代码+FreshResource：读取窗口标题用于证据；如果没有这行代码，报告无法解释是否看到了旧资源标题。
    fresh_required = bool(stage.verifier.get("fresh_resource_required", False))  # 新增代码+FreshResource：读取新资源要求用于证据；如果没有这行代码，报告不知道为何触发新建。
    existing_detected = bool(fresh_required and _stage_compiler_title_looks_existing_resource(title))  # 新增代码+FreshResource：记录是否发现已有资源；如果没有这行代码，acceptance 难以定位旧文件恢复问题。
    return {"stage_kind": stage.stage_kind, "fresh_resource_required": fresh_required, "existing_resource_title_detected": existing_detected, "observed_title_preview": title[:120], "generic_new_resource_shortcut": existing_detected}  # 新增代码+FreshResource：返回通用安全证据；如果没有这行代码，准备批缺少可审计 guardrail。
# 新增代码+FreshResource：函数段结束，_stage_compiler_prepare_guardrails 到此结束；如果没有这个边界说明，初学者不容易看出准备证据范围。


def _stage_compiler_text_actions(stage: StagePlan) -> tuple[dict[str, Any], ...]:  # 新增代码+StageBatchCompiler：函数段开始，生成通用文本输入动作；如果没有这段函数，文本阶段会退回逐步模型调用。
    requested_text = str(stage.verifier.get("requested_text", "sample text") or "sample text")  # 新增代码+StageBatchCompiler：读取阶段要求输入的文本；如果没有这行代码，type_text 动作缺内容。
    return ({"type": "focus_window"}, {"type": "type_text", "text": requested_text})  # 新增代码+StageBatchCompiler：返回聚焦加输入动作；如果没有这行代码，文本可能输入到错误焦点。
# 新增代码+StageBatchCompiler：函数段结束，_stage_compiler_text_actions 到此结束；如果没有这个边界说明，初学者不容易看出文本动作范围。


def _stage_compiler_drawing_actions(observation_frame: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:  # 新增代码+StageBatchCompiler：函数段开始，生成通用多路径指针动作；如果没有这段函数，复杂图形会退化成单线条。
    width, height = _stage_compiler_window_size(observation_frame)  # 新增代码+StageBatchCompiler：读取窗口尺寸；如果没有这行代码，路径没有缩放基准。
    left = int(width * 0.24)  # 新增代码+StageBatchCompiler：估算可操作区域左边界；如果没有这行代码，路径可能压到工具区。
    top = int(height * 0.24)  # 新增代码+StageBatchCompiler：估算可操作区域上边界；如果没有这行代码，路径可能压到菜单区。
    right = int(width * 0.82)  # 新增代码+StageBatchCompiler：估算可操作区域右边界；如果没有这行代码，主体宽度不足。
    bottom = int(height * 0.82)  # 新增代码+StageBatchCompiler：估算可操作区域下边界；如果没有这行代码，主体高度不足。
    mid_x = (left + right) // 2  # 新增代码+StageBatchCompiler：计算中心横坐标；如果没有这行代码，结构路径无法对齐。
    mid_y = (top + bottom) // 2  # 新增代码+StageBatchCompiler：计算中心纵坐标；如果没有这行代码，结构路径无法对齐。
    return ({"type": "focus_window"}, {"type": "drag_path", "coordinate_space": "target_window", "points": [{"x": mid_x, "y": top}, {"x": right, "y": mid_y}, {"x": mid_x, "y": bottom}, {"x": left, "y": mid_y}, {"x": mid_x, "y": top}]}, {"type": "drag_path", "coordinate_space": "target_window", "points": [{"x": left, "y": top}, {"x": right, "y": bottom}]}, {"type": "drag_path", "coordinate_space": "target_window", "points": [{"x": right, "y": top}, {"x": left, "y": bottom}]}, {"type": "drag_path", "coordinate_space": "target_window", "points": [{"x": mid_x - 40, "y": mid_y}, {"x": mid_x + 40, "y": mid_y}]})  # 新增代码+StageBatchCompiler：返回多条结构化拖拽路径；如果没有这行代码，绘图阶段无法一次性完成轮廓批。
# 新增代码+StageBatchCompiler：函数段结束，_stage_compiler_drawing_actions 到此结束；如果没有这个边界说明，初学者不容易看出绘制动作范围。


def _stage_compiler_navigation_actions(stage: StagePlan) -> tuple[dict[str, Any], ...]:  # 新增代码+StageBatchCompiler：函数段开始，生成通用导航动作；如果没有这段函数，搜索/导航任务只能靠具体浏览器控制器。
    query = str(stage.verifier.get("query", stage.verifier.get("requested_text", "")) or "")  # 新增代码+StageBatchCompiler：读取导航查询文本；如果没有这行代码，导航批没有输入内容。
    actions = [{"type": "focus_window"}]  # 新增代码+StageBatchCompiler：先聚焦目标窗口；如果没有这行代码，键盘输入可能落到其它窗口。
    if query:  # 新增代码+StageBatchCompiler：检查是否有查询文本；如果没有这行代码，空查询也会发送无意义输入。
        actions.append({"type": "type_text", "text": query})  # 新增代码+StageBatchCompiler：追加通用文本输入；如果没有这行代码，导航任务无法输入查询。
        actions.append({"type": "press_key", "key": "ENTER"})  # 新增代码+StageBatchCompiler：追加确认键；如果没有这行代码，搜索或导航不会提交。
    actions.append({"type": "observe"})  # 新增代码+StageBatchCompiler：追加观察动作；如果没有这行代码，导航后无法在阶段边界验证。
    return tuple(actions)  # 新增代码+StageBatchCompiler：返回导航动作元组；如果没有这行代码，调用方拿不到批动作。
# 新增代码+StageBatchCompiler：函数段结束，_stage_compiler_navigation_actions 到此结束；如果没有这个边界说明，初学者不容易看出导航动作范围。


def _stage_compiler_save_actions() -> tuple[dict[str, Any], ...]:  # 新增代码+StageBatchCompiler：函数段开始，生成通用应用内保存动作；如果没有这段函数，保存阶段可能被文件系统直写替代。
    return ({"type": "focus_window"}, {"type": "hotkey", "keys": ["CTRL", "S"]}, {"type": "wait", "milliseconds": 300}, {"type": "observe"})  # 新增代码+StageBatchCompiler：返回聚焦、保存快捷键、等待和观察；如果没有这行代码，保存无法通过应用界面完成。
# 新增代码+StageBatchCompiler：函数段结束，_stage_compiler_save_actions 到此结束；如果没有这个边界说明，初学者不容易看出保存动作范围。


def compile_stage_to_batch(stage: StagePlan, observation_frame: Mapping[str, Any], capability_profile: AppCapabilityProfile) -> ActionBatch:  # 新增代码+StageBatchCompiler：函数段开始，把通用阶段编译成一个动作批；如果没有这段函数，阶段内无法批量执行。
    if stage.stage_kind == "probe_capabilities":  # 新增代码+StageBatchCompiler：能力探测阶段不发送写动作；如果没有这行代码，探测可能误变成真实输入。
        return ActionBatch(batch_id=f"{stage.stage_id}_probe", batch_kind="probe_batch", target_ref=stage.target_ref, actions=({"type": "observe"},), guardrails={"stage_kind": stage.stage_kind})  # 新增代码+StageBatchCompiler：返回观察型探测批；如果没有这行代码，探测阶段无动作证据。
    if stage.stage_kind == "prepare_target":  # 新增代码+FreshResource：准备阶段负责聚焦并按需进入新资源；如果没有这行代码，准备阶段会缺少可执行批。
        return ActionBatch(batch_id=f"{stage.stage_id}_prepare", batch_kind="window_management_batch", target_ref=stage.target_ref, actions=_stage_compiler_prepare_actions(stage, observation_frame), guardrails=_stage_compiler_prepare_guardrails(stage, observation_frame))  # 新增代码+FreshResource：返回带新资源门禁的窗口管理批；如果没有这行代码，新进程恢复旧文件时仍会被当成可写新目标。
    if stage.stage_kind == "commit_resource":  # 新增代码+StageBatchCompiler：提交资源阶段走通用保存批；如果没有这行代码，保存任务可能早停。
        return ActionBatch(batch_id=f"{stage.stage_id}_save", batch_kind="file_save_batch", target_ref=stage.target_ref, actions=_stage_compiler_save_actions(), guardrails={"stage_kind": stage.stage_kind, "no_direct_file_write": True})  # 新增代码+StageBatchCompiler：返回应用内保存批；如果没有这行代码，保存可能绕过 GUI。
    if stage.stage_kind == "verify_result":  # 新增代码+StageBatchCompiler：验证阶段只观察；如果没有这行代码，验证可能误发输入动作。
        return ActionBatch(batch_id=f"{stage.stage_id}_verify", batch_kind="probe_batch", target_ref=stage.target_ref, actions=({"type": "observe"},), guardrails={"stage_kind": stage.stage_kind})  # 新增代码+StageBatchCompiler：返回观察验证批；如果没有这行代码，final gate 缺观察证据。
    if stage.stage_kind != "perform_content_work":  # 新增代码+StageBatchCompiler：未知阶段不伪造写动作；如果没有这行代码，错误阶段可能被当成文本或绘图执行。
        return ActionBatch(batch_id=f"{stage.stage_id}_probe", batch_kind="probe_batch", target_ref=stage.target_ref, actions=({"type": "observe"},), guardrails={"stage_kind": stage.stage_kind, "unknown_stage_kind": True})  # 新增代码+StageBatchCompiler：未知阶段保守观察；如果没有这行代码，未知阶段可能危险执行。
    if capability_profile.has_text_input:  # 新增代码+StageBatchCompiler：文本能力优先编译文本批；如果没有这行代码，文本输入任务无法批量完成。
        return ActionBatch(batch_id=f"{stage.stage_id}_text", batch_kind="text_entry_batch", target_ref=stage.target_ref, actions=_stage_compiler_text_actions(stage), guardrails={"stage_kind": stage.stage_kind, "capability": "text_input"})  # 新增代码+StageBatchCompiler：返回文本输入批；如果没有这行代码，文本阶段无可执行批。
    if capability_profile.has_canvas_like_region:  # 新增代码+StageBatchCompiler：画布能力编译指针路径批；如果没有这行代码，图形任务无法批量执行。
        return ActionBatch(batch_id=f"{stage.stage_id}_pointer", batch_kind="pointer_path_batch", target_ref=stage.target_ref, actions=_stage_compiler_drawing_actions(observation_frame), guardrails={"stage_kind": stage.stage_kind, "capability": "canvas_like_region"})  # 新增代码+StageBatchCompiler：返回多路径批；如果没有这行代码，复杂图形会只剩单步动作。
    if capability_profile.has_browser_navigation_surface:  # 新增代码+StageBatchCompiler：导航能力编译导航批；如果没有这行代码，导航任务无法泛化。
        return ActionBatch(batch_id=f"{stage.stage_id}_navigation", batch_kind="navigation_batch", target_ref=stage.target_ref, actions=_stage_compiler_navigation_actions(stage), guardrails={"stage_kind": stage.stage_kind, "capability": "navigation_surface"})  # 新增代码+StageBatchCompiler：返回导航批；如果没有这行代码，搜索任务无法批量提交。
    return ActionBatch(batch_id=f"{stage.stage_id}_probe", batch_kind="probe_batch", target_ref=stage.target_ref, actions=({"type": "observe"},), guardrails={"stage_kind": stage.stage_kind, "unknown_capabilities": True})  # 新增代码+StageBatchCompiler：能力未知时只观察不写入；如果没有这行代码，未知软件会被盲操作。
# 新增代码+StageBatchCompiler：函数段结束，compile_stage_to_batch 到此结束；如果没有这个边界说明，初学者不容易看出编译范围。


__all__ = ["compile_stage_to_batch"]  # 新增代码+StageBatchCompiler：声明公开接口；如果没有这行代码，通配导入会暴露内部 helper。
