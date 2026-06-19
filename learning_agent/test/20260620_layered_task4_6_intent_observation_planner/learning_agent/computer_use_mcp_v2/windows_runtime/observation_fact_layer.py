"""Structured observation fact extraction for layered Computer Use."""  # 新增代码+ObservationFactLayer：说明本文件把原始观察转成 facts；如果没有这行代码，后续层会继续直接消费截图/UIA 原始帧。
from __future__ import annotations  # 新增代码+ObservationFactLayer：启用延迟类型解析；如果没有这行代码，类型注解更容易在脚本入口失败。

from typing import Any, Mapping  # 新增代码+ObservationFactLayer：导入 JSON 风格类型；如果没有这行代码，观察帧接口不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.capability_profile import AppCapabilityProfile, build_capability_profile  # 新增代码+ObservationFactLayer：复用能力画像构建器；如果没有这行代码，facts 和 profile 会漂移。
from learning_agent.computer_use_mcp_v2.windows_runtime.layer_contracts import ObservationFacts  # 新增代码+ObservationFactLayer：导入观察事实契约；如果没有这行代码，输出会是散乱字典。


def _fact_text(value: Any) -> str:  # 新增代码+ObservationFactLayer：函数段开始，清洗观察摘要文本；如果没有这段函数，UIA 文本可能多行污染证据。
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())[:240]  # 新增代码+ObservationFactLayer：返回限长单行文本；如果没有这行代码，facts 可能泄露长文档内容。
# 新增代码+ObservationFactLayer：函数段结束，_fact_text 到此结束；如果没有这个边界说明，用户不容易看出文本清洗范围。


def _fact_collect_nodes(value: Any) -> list[dict[str, Any]]:  # 新增代码+ObservationFactLayer：函数段开始，递归收集 UIA/视觉节点；如果没有这段函数，嵌套观察帧无法提取区域。
    if isinstance(value, Mapping):  # 新增代码+ObservationFactLayer：处理字典节点；如果没有这行代码，根节点无法读取。
        nodes = [dict(value)]  # 新增代码+ObservationFactLayer：保存当前节点副本；如果没有这行代码，根节点能力会丢失。
        for key in ("children", "items", "nodes", "uia_tree", "uia_elements", "elements", "visual_regions"):  # 新增代码+ObservationFactLayer：遍历常见子节点字段；如果没有这行代码，不同观察源无法统一。
            nodes.extend(_fact_collect_nodes(value.get(key, [])))  # 新增代码+ObservationFactLayer：递归收集子节点；如果没有这行代码，深层控件会漏掉。
        return nodes  # 新增代码+ObservationFactLayer：返回节点列表；如果没有这行代码，调用方拿不到结果。
    if isinstance(value, list | tuple):  # 新增代码+ObservationFactLayer：处理列表或元组；如果没有这行代码，UIA 列表无法展开。
        nodes: list[dict[str, Any]] = []  # 新增代码+ObservationFactLayer：初始化节点容器；如果没有这行代码，循环结果无处保存。
        for item in value:  # 新增代码+ObservationFactLayer：逐项递归；如果没有这行代码，只能处理空列表。
            nodes.extend(_fact_collect_nodes(item))  # 新增代码+ObservationFactLayer：追加子节点；如果没有这行代码，嵌套结构会丢失。
        return nodes  # 新增代码+ObservationFactLayer：返回展开后的节点；如果没有这行代码，调用方拿不到列表。
    return []  # 新增代码+ObservationFactLayer：非结构值返回空；如果没有这行代码，函数可能返回 None。
# 新增代码+ObservationFactLayer：函数段结束，_fact_collect_nodes 到此结束；如果没有这个边界说明，用户不容易看出节点收集范围。


def _fact_bounds(node: Mapping[str, Any]) -> dict[str, Any]:  # 新增代码+ObservationFactLayer：函数段开始，读取节点边界；如果没有这段函数，区域 facts 缺坐标范围。
    bounds = node.get("bounds", node.get("rect", {})) if isinstance(node, Mapping) else {}  # 新增代码+ObservationFactLayer：兼容 bounds 和 rect 字段；如果没有这行代码，不同观察源无法统一。
    return dict(bounds) if isinstance(bounds, Mapping) else {}  # 新增代码+ObservationFactLayer：返回边界副本或空字典；如果没有这行代码，坏字段会导致异常。
# 新增代码+ObservationFactLayer：函数段结束，_fact_bounds 到此结束；如果没有这个边界说明，用户不容易看出边界读取范围。


def _fact_region(node: Mapping[str, Any], region_kind: str) -> dict[str, Any]:  # 新增代码+ObservationFactLayer：函数段开始，把节点转成低敏区域事实；如果没有这段函数，区域输出字段会不一致。
    return {"region_kind": region_kind, "name": _fact_text(node.get("name", node.get("role", "")))[:80], "bounds": _fact_bounds(node)}  # 新增代码+ObservationFactLayer：返回区域类型、短名和边界；如果没有这行代码，批编译缺通用区域信息。
# 新增代码+ObservationFactLayer：函数段结束，_fact_region 到此结束；如果没有这个边界说明，用户不容易看出区域转换范围。


def _profile_to_dict(profile: AppCapabilityProfile) -> dict[str, Any]:  # 新增代码+ObservationFactLayer：函数段开始，把能力画像转成 JSON 字典；如果没有这段函数，facts 无法保存 profile。
    return {"has_text_input": profile.has_text_input, "has_canvas_like_region": profile.has_canvas_like_region, "has_menu_bar": profile.has_menu_bar, "has_toolbar": profile.has_toolbar, "has_file_save_surface": profile.has_file_save_surface, "has_browser_navigation_surface": profile.has_browser_navigation_surface, "has_grid_or_table": profile.has_grid_or_table, "has_modal_dialog": profile.has_modal_dialog, "supports_keyboard_shortcuts_likely": profile.supports_keyboard_shortcuts_likely, "single_instance_suspected": profile.single_instance_suspected, "unknown_capabilities": profile.unknown_capabilities, "evidence": list(profile.evidence)}  # 新增代码+ObservationFactLayer：返回能力字段；如果没有这行代码，batch compiler 不能从 facts 读取能力。
# 新增代码+ObservationFactLayer：函数段结束，_profile_to_dict 到此结束；如果没有这个边界说明，用户不容易看出画像序列化范围。


def build_observation_facts(observation_frame: Mapping[str, Any] | None) -> ObservationFacts:  # 新增代码+ObservationFactLayer：函数段开始，从原始观察帧生成结构化 facts；如果没有这段函数，规划/验证层会继续吃原始截图。
    frame = observation_frame if isinstance(observation_frame, Mapping) else {}  # 新增代码+ObservationFactLayer：规范化观察帧；如果没有这行代码，None 输入会崩溃。
    nodes = _fact_collect_nodes(frame)  # 新增代码+ObservationFactLayer：收集所有节点；如果没有这行代码，区域提取没有输入。
    profile = build_capability_profile(frame)  # 新增代码+ObservationFactLayer：构建能力画像；如果没有这行代码，facts 缺 capability_profile。
    editable = [_fact_region(node, "editable") for node in nodes if any(term in _fact_text(node.get("control_type", node.get("role", ""))).lower() for term in ("edit", "text", "input", "document"))]  # 新增代码+ObservationFactLayer：提取可编辑区域；如果没有这行代码，文本阶段缺事实。
    canvas = [_fact_region(node, "canvas") for node in nodes if any(term in _fact_text(node.get("role", node.get("control_type", ""))).lower() for term in ("canvas", "content", "drawing", "image", "surface")) or bool(node.get("blank_ratio", 0))]  # 新增代码+ObservationFactLayer：提取画布区域；如果没有这行代码，绘图阶段缺事实。
    menus = [_fact_region(node, "menu") for node in nodes if "menu" in _fact_text(node.get("control_type", node.get("role", ""))).lower()]  # 新增代码+ObservationFactLayer：提取菜单区域；如果没有这行代码，菜单操作缺事实。
    toolbars = [_fact_region(node, "toolbar") for node in nodes if any(term in _fact_text(node.get("control_type", node.get("role", ""))).lower() for term in ("toolbar", "ribbon"))]  # 新增代码+ObservationFactLayer：提取工具栏区域；如果没有这行代码，工具选择缺事实。
    dialogs = [_fact_region(node, "dialog") for node in nodes if "dialog" in _fact_text(node.get("control_type", node.get("role", ""))).lower() or bool(node.get("modal", False))]  # 新增代码+ObservationFactLayer：提取模态对话框；如果没有这行代码，保存弹窗可能被忽略。
    target_window = frame.get("target_window", {}) if isinstance(frame.get("target_window", {}), Mapping) else {}  # 新增代码+ObservationFactLayer：读取目标窗口摘要；如果没有这行代码，facts 无法判断窗口身份。
    freshness = "fresh_agent_owned_window" if bool(frame.get("fresh_agent_owned_window") or frame.get("target_identity_verified") and not frame.get("target_window_existed_before_launch")) else "stale_user_owned_window" if bool(frame.get("target_window_existed_before_launch") or frame.get("user_preexisting_window_present")) else "unknown"  # 新增代码+ObservationFactLayer：推导目标窗口新鲜度；如果没有这行代码，旧窗口和新窗口无法区分。
    visible_summary = _fact_text(frame.get("visible_text_summary", frame.get("visible_text", frame.get("text_content", ""))))  # 新增代码+ObservationFactLayer：读取低敏可见文本摘要；如果没有这行代码，文本验证缺摘要。
    visual_summary = _fact_text(frame.get("visual_change_summary", "canvas_changed" if frame.get("canvas_changed_after_actions") else ""))  # 新增代码+ObservationFactLayer：读取视觉变化摘要；如果没有这行代码，绘图验证缺摘要。
    return ObservationFacts(active_target_ref=_fact_text(frame.get("target_ref", target_window.get("target_ref", ""))), target_identity_verified=bool(frame.get("target_identity_verified") or frame.get("target_window_identity_present") or frame.get("visible_window_verified")), target_window_freshness=freshness, editable_regions=tuple(editable), canvas_regions=tuple(canvas), menu_regions=tuple(menus), toolbar_regions=tuple(toolbars), modal_dialogs=tuple(dialogs), save_dialog_state={"open": bool(frame.get("save_dialog_open", False)), "completed": bool(frame.get("save_dialog_completed", False) or frame.get("saved_resource_exists", False))}, document_dirty_state=_fact_text(frame.get("document_dirty_state", "unknown")) or "unknown", visible_text_summary=visible_summary, visual_change_summary=visual_summary, capability_profile=_profile_to_dict(profile))  # 新增代码+ObservationFactLayer：返回结构化观察事实；如果没有这行代码，后续层拿不到统一 facts。
# 新增代码+ObservationFactLayer：函数段结束，build_observation_facts 到此结束；如果没有这个边界说明，用户不容易看出 facts 构建范围。


__all__ = ["build_observation_facts"]  # 新增代码+ObservationFactLayer：声明公开接口；如果没有这行代码，通配导入会暴露内部 helper。
