"""Compile universal Computer Use stages into executable action batches."""  # 新增代码+StageBatchCompiler：说明本文件负责阶段到批动作编译；如果没有这行代码，读者会误以为这里直接控制具体软件。
from __future__ import annotations  # 新增代码+StageBatchCompiler：启用延迟类型解析；如果没有这行代码，类型注解更容易在导入阶段失败。

from typing import Any, Mapping  # 新增代码+StageBatchCompiler：导入 JSON 风格类型；如果没有这行代码，观察帧和 verifier 配置边界不清。

from learning_agent.computer_use_mcp_v2.windows_runtime.capability_profile import AppCapabilityProfile  # 新增代码+StageBatchCompiler：导入通用能力画像；如果没有这行代码，编译器会回到应用名判断。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import ActionBatch, StagePlan  # 新增代码+StageBatchCompiler：导入阶段和批模型；如果没有这行代码，编译结果会变成散乱 dict。


def _stage_compiler_safe_int(value: Any, default: int) -> int:  # 新增代码+StageBatchCompiler：函数段开始，安全读取尺寸数值；如果没有这段函数，坏观察帧会让编译器崩溃。
    try:  # 新增代码+StageBatchCompiler：尝试转换整数；如果没有这行代码，字符串尺寸无法兼容。
        return int(value)  # 新增代码+StageBatchCompiler：返回整数值；如果没有这行代码，调用方拿不到坐标基准。
    except (TypeError, ValueError):  # 新增代码+StageBatchCompiler：捕获空值和非数字；如果没有这行代码，坏字段会中断整个任务。
        return int(default)  # 新增代码+StageBatchCompiler：返回兜底值；如果没有这行代码，编译器无法保守继续。
# 新增代码+StageBatchCompiler：函数段结束，_stage_compiler_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出数值兜底范围。


def _stage_compiler_window_size(observation_frame: Mapping[str, Any]) -> tuple[int, int]:  # 新增代码+StageBatchCompiler：函数段开始，从观察帧读取窗口尺寸；如果没有这段函数，指针路径无法按窗口缩放。
    target_window = observation_frame.get("target_window", {}) if isinstance(observation_frame, Mapping) else {}  # 新增代码+StageBatchCompiler：读取目标窗口摘要；如果没有这行代码，编译器没有窗口来源。
    rect = target_window.get("rect", {}) if isinstance(target_window, Mapping) else {}  # 新增代码+StageBatchCompiler：读取窗口矩形；如果没有这行代码，尺寸推导无输入。
    width = max(320, _stage_compiler_safe_int(rect.get("width", 0), 800))  # 新增代码+StageBatchCompiler：读取或兜底窗口宽度；如果没有这行代码，路径可能落到窗口外。
    height = max(240, _stage_compiler_safe_int(rect.get("height", 0), 500))  # 新增代码+StageBatchCompiler：读取或兜底窗口高度；如果没有这行代码，路径可能落到工具栏或窗口外。
    return width, height  # 新增代码+StageBatchCompiler：返回尺寸元组；如果没有这行代码，调用方拿不到坐标。
# 新增代码+StageBatchCompiler：函数段结束，_stage_compiler_window_size 到此结束；如果没有这个边界说明，初学者不容易看出尺寸推导范围。


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
    if stage.stage_kind == "prepare_target":  # 新增代码+StageBatchCompiler：准备阶段只聚焦目标；如果没有这行代码，准备阶段会缺少可执行批。
        return ActionBatch(batch_id=f"{stage.stage_id}_prepare", batch_kind="window_management_batch", target_ref=stage.target_ref, actions=({"type": "focus_window"},), guardrails={"stage_kind": stage.stage_kind})  # 新增代码+StageBatchCompiler：返回窗口管理批；如果没有这行代码，目标准备无法进入执行器。
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
