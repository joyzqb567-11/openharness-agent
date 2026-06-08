"""Visual semantic planner for generic Computer Use drawing tasks."""  # 新增代码+VisualSemanticPlanner：说明本模块负责把脱敏自然语言意图变成通用视觉 primitive；如果没有这一行，读者不容易知道本文件不是 Paint 专用控制器。
from __future__ import annotations  # 新增代码+VisualSemanticPlanner：启用延迟类型注解，避免旧 Python 在导入时提前解析复杂类型；如果没有这一行，后续类型标注兼容性会更差。
from typing import Any  # 新增代码+VisualSemanticPlanner：导入 Any 描述动态任务、观察帧和动作字典；如果没有这一行，函数签名无法清楚表达 JSON 风格输入输出。

PHASE122_VISUAL_SEMANTIC_PLANNER_MODEL = "phase122_visual_semantic_planner"  # 新增代码+VisualSemanticPlanner：定义语义规划层模型名；如果没有这一行，报告无法区分“接线 planner”和“语义 primitive planner”。

def _phase122_safe_int(value: Any, default: int) -> int:  # 新增代码+VisualSemanticPlanner：函数段开始，安全地把观察字段转成整数；如果没有这段函数，坏 observation 会让语义规划直接崩溃。
    try:  # 新增代码+VisualSemanticPlanner：尝试执行整数转换；如果没有这一行，字符串形式的数字无法被统一处理。
        return int(value)  # 新增代码+VisualSemanticPlanner：返回转换后的整数；如果没有这一行，坐标和画布尺寸没有可计算数值。
    except (TypeError, ValueError):  # 新增代码+VisualSemanticPlanner：捕获空值或非数字文本；如果没有这一行，一个坏字段就会中断整次桌面任务。
        return int(default)  # 新增代码+VisualSemanticPlanner：坏值时使用默认值兜底；如果没有这一行，planner 无法在不完整观察帧下继续工作。
# 新增代码+VisualSemanticPlanner：函数段结束，_phase122_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出安全整数转换范围。

def _phase122_dimension(rect: dict[str, Any], size_key: str, start_key: str, end_key: str, default: int) -> int:  # 新增代码+VisualSemanticPlanner：函数段开始，从 width/height 或边界差推导尺寸；如果没有这段函数，真实 Paint 只给 left/right/top/bottom 时会再次画偏。
    explicit_size = _phase122_safe_int(rect.get(size_key), 0)  # 新增代码+VisualSemanticPlanner：优先读取显式尺寸；如果没有这一行，记录型 observation 的标准 width/height 会被忽略。
    if explicit_size > 0:  # 新增代码+VisualSemanticPlanner：判断显式尺寸是否有效；如果没有这一行，0 或坏值可能被当成真实尺寸。
        return explicit_size  # 新增代码+VisualSemanticPlanner：返回显式尺寸；如果没有这一行，正常 observation 会被不必要地重新推导。
    start = _phase122_safe_int(rect.get(start_key), 0)  # 新增代码+VisualSemanticPlanner：读取左边或上边界；如果没有这一行，无法从真实窗口边界推导尺寸。
    end = _phase122_safe_int(rect.get(end_key), 0)  # 新增代码+VisualSemanticPlanner：读取右边或下边界；如果没有这一行，无法知道窗口跨度。
    inferred_size = end - start  # 新增代码+VisualSemanticPlanner：用边界差计算尺寸；如果没有这一行，planner 会回到错误默认画布大小。
    return inferred_size if inferred_size > 0 else int(default)  # 新增代码+VisualSemanticPlanner：返回有效推导尺寸或默认值；如果没有这一行，坏 rect 会让坐标计算失去兜底。
# 新增代码+VisualSemanticPlanner：函数段结束，_phase122_dimension 到此结束；如果没有这个边界说明，初学者不容易看出尺寸推导范围。

def phase122_visual_intent_from_prompt(prompt: str) -> dict[str, Any]:  # 新增代码+VisualSemanticPlanner：函数段开始，从原始 prompt 抽取脱敏视觉意图；如果没有这段函数，adapter 只能传哈希，planner 不知道用户想画什么。
    text = str(prompt or "")  # 新增代码+VisualSemanticPlanner：把用户输入统一为字符串；如果没有这一行，None prompt 会污染后续匹配。
    lower_text = text.lower()  # 新增代码+VisualSemanticPlanner：准备英文小写文本；如果没有这一行，英文 house/home 匹配会受大小写影响。
    subject = "generic"  # 新增代码+VisualSemanticPlanner：默认主题设为 generic；如果没有这一行，未知图像任务没有安全兜底。
    if any(token in text for token in ("房子", "房屋", "屋子", "小屋")) or any(token in lower_text for token in ("house", "home", "cabin")):  # 新增代码+VisualSemanticPlanner：识别房屋类主题；如果没有这一行，用户让画房子仍会退回通用脸。
        subject = "house"  # 新增代码+VisualSemanticPlanner：把房屋类 prompt 归一成 house；如果没有这一行，后续 planner 没有稳定主题键。
    return {"model": PHASE122_VISUAL_SEMANTIC_PLANNER_MODEL, "subject": subject, "drawing_requested": True, "raw_prompt_included": False, "known_subject": subject != "generic"}  # 新增代码+VisualSemanticPlanner：返回不含原文的结构化意图；如果没有这一行，adapter 无法在保护隐私的同时传递语义。
# 新增代码+VisualSemanticPlanner：函数段结束，phase122_visual_intent_from_prompt 到此结束；如果没有这个边界说明，初学者不容易看出 prompt 脱敏范围。

def _phase122_canvas_box(task: dict[str, Any], observation_frame: dict[str, Any]) -> dict[str, int]:  # 新增代码+VisualSemanticPlanner：函数段开始，根据观察帧估算安全画布区域；如果没有这段函数，语义 primitive 可能画到工具栏或画布外。
    target_window = observation_frame.get("target_window", {}) if isinstance(observation_frame, dict) else {}  # 新增代码+VisualSemanticPlanner：读取目标窗口摘要；如果没有这一行，planner 无法根据真实窗口规划坐标。
    rect = target_window.get("rect", {}) if isinstance(target_window, dict) else {}  # 新增代码+VisualSemanticPlanner：读取窗口矩形；如果没有这一行，画布尺寸只能依赖魔法数。
    width = max(260, _phase122_dimension(rect, "width", "left", "right", 900))  # 新增代码+VisualSemanticPlanner：计算窗口宽度并设置下限；如果没有这一行，小窗口或坏 rect 会生成负坐标。
    height = max(220, _phase122_dimension(rect, "height", "top", "bottom", 620))  # 新增代码+VisualSemanticPlanner：计算窗口高度并设置下限；如果没有这一行，纵向坐标会失去安全范围。
    app_hint = str(target_window.get("app_id", "") if isinstance(target_window, dict) else "").lower()  # 新增代码+VisualSemanticPlanner：读取应用提示；如果没有这一行，Paint 画布避让规则无法启用。
    paint_canvas_mode = "paint" in app_hint or str(task.get("target", "")).lower() == "mspaint"  # 新增代码+VisualSemanticPlanner：判断是否是 Paint 画布任务；如果没有这一行，planner 会把 Paint 工具栏当成可绘制区域。
    left = int(width * 0.26) if paint_canvas_mode else int(width * 0.12)  # 新增代码+VisualSemanticPlanner：估算可绘制左边界；如果没有这一行，房子左墙可能落到工具区。
    top = int(height * 0.28) if paint_canvas_mode else int(height * 0.18)  # 新增代码+VisualSemanticPlanner：估算可绘制上边界；如果没有这一行，房顶可能画到功能区。
    right = max(left + 220, width - int(width * 0.12))  # 新增代码+VisualSemanticPlanner：估算可绘制右边界；如果没有这一行，主体宽度没有右侧约束。
    bottom = max(top + 180, height - int(height * 0.12))  # 新增代码+VisualSemanticPlanner：估算可绘制下边界；如果没有这一行，门和墙体可能画到窗口底部外。
    return {"left": left, "top": top, "right": right, "bottom": bottom, "width": right - left, "height": bottom - top}  # 新增代码+VisualSemanticPlanner：返回统一画布盒子；如果没有这一行，后续 primitive 没有共同坐标基准。
# 新增代码+VisualSemanticPlanner：函数段结束，_phase122_canvas_box 到此结束；如果没有这个边界说明，初学者不容易看出画布估算范围。

def _phase122_point(x: int, y: int) -> dict[str, int]:  # 新增代码+VisualSemanticPlanner：函数段开始，构造标准点位字典；如果没有这段函数，点结构容易在不同 primitive 间漂移。
    return {"x": int(x), "y": int(y)}  # 新增代码+VisualSemanticPlanner：返回 DSL 可消费的 x/y 点；如果没有这一行，drag_path 无法被动作层展开。
# 新增代码+VisualSemanticPlanner：函数段结束，_phase122_point 到此结束；如果没有这个边界说明，初学者不容易看出点结构范围。

def _phase122_drag(role: str, points: list[dict[str, int]], planner_model: str) -> dict[str, Any]:  # 新增代码+VisualSemanticPlanner：函数段开始，构造带语义角色的 drag_path；如果没有这段函数，测试和日志无法知道每笔代表屋顶还是门窗。
    return {"type": "drag_path", "coordinate_space": "target_window", "visual_planner_action": True, "planner_model": planner_model, "semantic_role": role, "points": list(points)}  # 新增代码+VisualSemanticPlanner：返回通用 DSL 拖拽动作；如果没有这一行，语义计划无法落到真实鼠标路径。
# 新增代码+VisualSemanticPlanner：函数段结束，_phase122_drag 到此结束；如果没有这个边界说明，初学者不容易看出动作构造范围。

def _phase122_house_actions(box: dict[str, int], planner_model: str) -> list[dict[str, Any]]:  # 新增代码+VisualSemanticPlanner：函数段开始，把 house 主题拆成房屋 primitive；如果没有这段函数，房子 prompt 仍会画成通用几何脸。
    center_x = (box["left"] + box["right"]) // 2  # 新增代码+VisualSemanticPlanner：计算画布中心 x；如果没有这一行，屋顶和墙体无法对齐。
    roof_top = box["top"] + max(35, box["height"] // 10)  # 新增代码+VisualSemanticPlanner：计算屋顶顶点 y；如果没有这一行，屋顶可能太贴近工具栏。
    roof_left = center_x - max(120, box["width"] // 5)  # 新增代码+VisualSemanticPlanner：计算屋顶左檐 x；如果没有这一行，屋顶没有稳定宽度。
    roof_right = center_x + max(120, box["width"] // 5)  # 新增代码+VisualSemanticPlanner：计算屋顶右檐 x；如果没有这一行，屋顶无法形成三角形。
    wall_top = roof_top + max(90, box["height"] // 7)  # 新增代码+VisualSemanticPlanner：计算墙体顶部 y；如果没有这一行，屋顶和墙体会重叠或断开。
    wall_bottom = min(box["bottom"] - 45, wall_top + max(150, box["height"] // 4))  # 新增代码+VisualSemanticPlanner：计算墙体底部 y；如果没有这一行，房子主体可能超出画布。
    wall_left = center_x - max(95, box["width"] // 7)  # 新增代码+VisualSemanticPlanner：计算墙体左边 x；如果没有这一行，墙体无法跟屋顶居中。
    wall_right = center_x + max(95, box["width"] // 7)  # 新增代码+VisualSemanticPlanner：计算墙体右边 x；如果没有这一行，墙体宽度不稳定。
    door_left = center_x - max(25, (wall_right - wall_left) // 10)  # 新增代码+VisualSemanticPlanner：计算门左边 x；如果没有这一行，门无法居中。
    door_right = center_x + max(25, (wall_right - wall_left) // 10)  # 新增代码+VisualSemanticPlanner：计算门右边 x；如果没有这一行，门没有可见宽度。
    door_top = wall_bottom - max(80, (wall_bottom - wall_top) // 2)  # 新增代码+VisualSemanticPlanner：计算门顶部 y；如果没有这一行，门可能太矮不可识别。
    window_top = wall_top + max(30, (wall_bottom - wall_top) // 5)  # 新增代码+VisualSemanticPlanner：计算窗户顶部 y；如果没有这一行，窗户可能贴到屋顶线。
    window_size = max(32, min(56, (wall_right - wall_left) // 5))  # 新增代码+VisualSemanticPlanner：计算窗户尺寸；如果没有这一行，窗户可能过小或过大。
    left_window_x = wall_left + max(35, (wall_right - wall_left) // 5)  # 新增代码+VisualSemanticPlanner：计算左窗左上 x；如果没有这一行，左窗缺少稳定位置。
    right_window_x = wall_right - max(35, (wall_right - wall_left) // 5) - window_size  # 新增代码+VisualSemanticPlanner：计算右窗左上 x；如果没有这一行，右窗可能跑出墙体。
    return [{"type": "focus_window", "visual_planner_action": True, "planner_model": planner_model, "semantic_role": "focus_target"}, _phase122_drag("house_roof", [_phase122_point(roof_left, wall_top), _phase122_point(center_x, roof_top), _phase122_point(roof_right, wall_top)], planner_model), _phase122_drag("house_body", [_phase122_point(wall_left, wall_top), _phase122_point(wall_right, wall_top), _phase122_point(wall_right, wall_bottom), _phase122_point(wall_left, wall_bottom), _phase122_point(wall_left, wall_top)], planner_model), _phase122_drag("house_door", [_phase122_point(door_left, wall_bottom), _phase122_point(door_left, door_top), _phase122_point(door_right, door_top), _phase122_point(door_right, wall_bottom)], planner_model), _phase122_drag("house_window_left", [_phase122_point(left_window_x, window_top), _phase122_point(left_window_x + window_size, window_top), _phase122_point(left_window_x + window_size, window_top + window_size), _phase122_point(left_window_x, window_top + window_size), _phase122_point(left_window_x, window_top)], planner_model), _phase122_drag("house_window_right", [_phase122_point(right_window_x, window_top), _phase122_point(right_window_x + window_size, window_top), _phase122_point(right_window_x + window_size, window_top + window_size), _phase122_point(right_window_x, window_top + window_size), _phase122_point(right_window_x, window_top)], planner_model), {"type": "observe", "visual_planner_action": True, "planner_model": planner_model, "semantic_role": "post_semantic_observe"}]  # 新增代码+VisualSemanticPlanner：返回房屋动作序列；如果没有这一行，planner 无法真实执行屋顶、墙体、门窗计划。
# 新增代码+VisualSemanticPlanner：函数段结束，_phase122_house_actions 到此结束；如果没有这个边界说明，初学者不容易看出房屋 primitive 范围。

def phase122_plan_visual_semantic_task(task: dict[str, Any], observation_frame: dict[str, Any], planner_model: str) -> list[dict[str, Any]]:  # 新增代码+VisualSemanticPlanner：函数段开始，按结构化意图生成视觉动作；如果没有这段函数，Phase120 只能保留旧通用脸逻辑。
    intent = task.get("visual_intent", {}) if isinstance(task, dict) else {}  # 新增代码+VisualSemanticPlanner：读取 adapter 传来的脱敏意图；如果没有这一行，planner 无法知道主题来源。
    subject = str(task.get("visual_subject_hint") or (intent.get("subject") if isinstance(intent, dict) else "") or "generic").strip().lower()  # 新增代码+VisualSemanticPlanner：统一读取视觉主题；如果没有这一行，house 分支不会被触发。
    box = _phase122_canvas_box(task, observation_frame)  # 新增代码+VisualSemanticPlanner：计算安全画布盒子；如果没有这一行，所有 primitive 都缺少坐标基准。
    if subject == "house":  # 新增代码+VisualSemanticPlanner：判断是否使用房屋 primitive；如果没有这一行，房子 prompt 仍会落到通用分支。
        return _phase122_house_actions(box, planner_model)  # 新增代码+VisualSemanticPlanner：返回房屋动作计划；如果没有这一行，测试要求的屋顶、墙体、门窗不会出现。
    return []  # 新增代码+VisualSemanticPlanner：未知主题交回旧 planner 兜底；如果没有这一行，未支持主题可能被误报为空成功或错误房子。
# 新增代码+VisualSemanticPlanner：函数段结束，phase122_plan_visual_semantic_task 到此结束；如果没有这个边界说明，初学者不容易看出语义规划入口范围。

__all__ = ["PHASE122_VISUAL_SEMANTIC_PLANNER_MODEL", "phase122_plan_visual_semantic_task", "phase122_visual_intent_from_prompt"]  # 新增代码+VisualSemanticPlanner：声明公开 API；如果没有这一行，通配导入会暴露内部 helper 或漏掉主入口。
