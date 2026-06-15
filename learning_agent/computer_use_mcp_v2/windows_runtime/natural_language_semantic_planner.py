"""Generic natural language semantic planner for Computer Use full mode."""  # 新增代码+GenericSemanticPlanner：说明本文件负责把普通自然语言先转成通用任务意图；如果没有这一行，读者容易误以为这里还是 Paint 专用逻辑。
from __future__ import annotations  # 新增代码+GenericSemanticPlanner：启用延迟类型注解；如果没有这一行，旧 Python 环境更容易在导入阶段解析类型失败。
from typing import Any  # 新增代码+GenericSemanticPlanner：导入 Any 描述动态 JSON 字段；如果没有这一行，函数签名无法清楚表达灵活输入输出。

PHASE123_GENERIC_SEMANTIC_PLANNER_MODEL = "phase123_generic_natural_language_semantic_planner"  # 新增代码+GenericSemanticPlanner：定义通用语义 planner 模型名；如果没有这一行，报告无法区分通用语义层和旧视觉特例层。

_PHASE123_OPEN_TERMS = ("打开", "启动", "运行", "使用", "open", "launch", "start", "use")  # 新增代码+GenericSemanticPlanner：集中列出打开或使用应用的自然语言动词；如果没有这一行，open_app 判断会散落且难维护。
_PHASE123_DRAW_TERMS = ("画", "绘制", "draw", "paint")  # 新增代码+GenericSemanticPlanner：集中列出绘图任务动词；如果没有这一行，draw 任务无法从通用语义层被识别出来。
_PHASE123_TYPE_TERMS = ("输入", "键入", "写入", "type", "write", "enter")  # 新增代码+GenericSemanticPlanner：集中列出文本输入动词；如果没有这一行，Notepad 等键盘任务无法被标成 type_text。
_PHASE123_CLICK_TERMS = ("点击", "单击", "click")  # 新增代码+GenericSemanticPlanner：集中列出点击动词；如果没有这一行，点击类 GUI 任务无法形成统一意图。
_PHASE123_BROWSER_TERMS = ("浏览器", "网页", "搜索", "browser", "web", "search", "chrome", "edge")  # 新增代码+GenericSemanticPlanner：集中列出浏览器相关线索；如果没有这一行，浏览器任务只能落入泛化未知任务。


def _phase123_text(prompt: Any) -> str:  # 新增代码+GenericSemanticPlanner：函数段开始，把任意输入转成可匹配文本；如果没有这段函数，None 或非字符串 prompt 会让 planner 判断不稳定。
    return str(prompt or "").strip()  # 新增代码+GenericSemanticPlanner：返回去掉首尾空白的字符串；如果没有这一行，空格和 None 会污染后续关键词判断。
# 新增代码+GenericSemanticPlanner：函数段结束，_phase123_text 到此结束；如果没有这个边界说明，代码小白不容易看出文本清洗范围。


def _phase123_contains_any(text: str, terms: tuple[str, ...]) -> bool:  # 新增代码+GenericSemanticPlanner：函数段开始，统一判断中英文关键词是否出现；如果没有这段函数，多处分支会重复写包含逻辑。
    lower_text = text.lower()  # 新增代码+GenericSemanticPlanner：准备小写文本兼容英文大小写；如果没有这一行，Open/open 会被当成不同输入。
    return any(term in text or term in lower_text for term in terms)  # 新增代码+GenericSemanticPlanner：只要任一关键词出现就命中；如果没有这一行，调用方拿不到统一布尔结果。
# 新增代码+GenericSemanticPlanner：函数段结束，_phase123_contains_any 到此结束；如果没有这个边界说明，代码小白不容易看出关键词判断范围。


def _phase123_target_from_prompt(text: str, target_app_hint: str = "") -> str:  # 新增代码+GenericSemanticPlanner：函数段开始，从目标提示和 prompt 中归一目标应用；如果没有这段函数，Notepad/画图/浏览器会在不同层使用不同名字。
    hint = str(target_app_hint or "").strip().lower()  # 新增代码+GenericSemanticPlanner：清洗外部传入的目标应用提示；如果没有这一行，大小写和空格会影响目标归一。
    lower_text = text.lower()  # 新增代码+GenericSemanticPlanner：准备小写 prompt 用于英文匹配；如果没有这一行，英文应用名匹配会不稳定。
    if hint in {"mspaint", "paint"} or "画图" in text or "mspaint" in lower_text or "paint" in lower_text:  # 新增代码+GenericSemanticPlanner：识别 Paint/画图目标；如果没有这一行，绘图任务无法稳定启动 mspaint。
        return "mspaint"  # 新增代码+GenericSemanticPlanner：返回 Windows 画图规范目标；如果没有这一行，后续启动层会收到不稳定别名。
    if hint == "notepad" or "记事本" in text or "notepad" in lower_text:  # 新增代码+GenericSemanticPlanner：识别 Notepad/记事本目标；如果没有这一行，用户打开记事本会落成泛化 local_app。
        return "notepad"  # 新增代码+GenericSemanticPlanner：返回 Windows 记事本规范目标；如果没有这一行，后续启动层无法稳定打开 notepad。
    if hint in {"calc", "calculator"} or "计算器" in text or "calculator" in lower_text or "calc" in lower_text:  # 新增代码+GenericSemanticPlanner：识别 Calculator/计算器目标；如果没有这一行，计算器任务无法获得规范目标。
        return "calc"  # 新增代码+GenericSemanticPlanner：返回 Windows 计算器规范目标；如果没有这一行，启动层可能收到中文别名。
    if hint in {"browser", "edge", "chrome"} or _phase123_contains_any(text, _PHASE123_BROWSER_TERMS):  # 新增代码+GenericSemanticPlanner：识别浏览器类目标；如果没有这一行，浏览器任务只能作为未知 GUI 任务。
        return hint or "browser"  # 新增代码+GenericSemanticPlanner：保留具体浏览器提示或使用 browser 泛化目标；如果没有这一行，浏览器分支没有目标名称。
    return hint or "local_app"  # 新增代码+GenericSemanticPlanner：没有明确目标时返回泛化本地应用；如果没有这一行，后续字段会出现空目标。
# 新增代码+GenericSemanticPlanner：函数段结束，_phase123_target_from_prompt 到此结束；如果没有这个边界说明，代码小白不容易看出目标归一范围。


def phase123_semantic_intent_from_prompt(prompt: Any, target_app_hint: str = "") -> dict[str, Any]:  # 新增代码+GenericSemanticPlanner：函数段开始，把用户自然语言转成通用语义意图；如果没有这段函数，/computer use --full 只能继续靠画图特例或固定动作。
    text = _phase123_text(prompt)  # 新增代码+GenericSemanticPlanner：读取清洗后的 prompt 文本用于本轮推断；如果没有这一行，后续所有语义判断没有输入来源。
    target_app = _phase123_target_from_prompt(text, target_app_hint)  # 新增代码+GenericSemanticPlanner：归一目标应用；如果没有这一行，planner 和启动层无法共享同一个目标。
    drawing_requested = _phase123_contains_any(text, _PHASE123_DRAW_TERMS)  # 新增代码+GenericSemanticPlanner：判断用户是否要求绘图；如果没有这一行，绘图任务无法进入 draw 分支。
    typing_requested = _phase123_contains_any(text, _PHASE123_TYPE_TERMS)  # 新增代码+GenericSemanticPlanner：判断用户是否要求键盘输入；如果没有这一行，文本输入任务无法进入 type_text 分支。
    clicking_requested = _phase123_contains_any(text, _PHASE123_CLICK_TERMS)  # 新增代码+GenericSemanticPlanner：判断用户是否要求点击；如果没有这一行，点击任务无法形成语义字段。
    browsing_requested = target_app == "browser" or _phase123_contains_any(text, _PHASE123_BROWSER_TERMS)  # 新增代码+GenericSemanticPlanner：判断用户是否要求浏览器任务；如果没有这一行，网页任务只能混入泛化 GUI。
    open_requested = _phase123_contains_any(text, _PHASE123_OPEN_TERMS)  # 新增代码+GenericSemanticPlanner：判断用户是否要求打开或使用应用；如果没有这一行，open_app 分支不会触发。
    task_kind = "draw" if drawing_requested else "type_text" if typing_requested else "click" if clicking_requested else "browser_task" if browsing_requested else "open_app" if open_requested else "generic_gui_task"  # 新增代码+GenericSemanticPlanner：按动作语义选择通用任务类型；如果没有这一行，后续 planner 只能拿到模糊目标。
    requires_mouse = bool(task_kind in {"draw", "click", "browser_task", "generic_gui_task"})  # 新增代码+GenericSemanticPlanner：记录任务是否可能需要鼠标；如果没有这一行，报告无法说明动作通道预期。
    requires_keyboard = bool(task_kind in {"type_text", "browser_task", "generic_gui_task"})  # 新增代码+GenericSemanticPlanner：记录任务是否可能需要键盘；如果没有这一行，文本和浏览器任务无法表达键盘需求。
    requires_observation = True  # 新增代码+GenericSemanticPlanner：所有真实桌面任务都需要观察；如果没有这一行，observe-plan-act loop 的屏幕监控原则会在语义层丢失。
    return {"model": PHASE123_GENERIC_SEMANTIC_PLANNER_MODEL, "task_kind": task_kind, "target_app": target_app, "drawing_requested": drawing_requested, "typing_requested": typing_requested, "clicking_requested": clicking_requested, "browsing_requested": browsing_requested, "open_requested": open_requested, "requires_mouse": requires_mouse, "requires_keyboard": requires_keyboard, "requires_observation": requires_observation, "raw_prompt_included": False, "planner_backend": "deterministic_semantic_contract", "model_planner_required_for_open_ended_tasks": task_kind in {"browser_task", "generic_gui_task"}}  # 新增代码+GenericSemanticPlanner：返回脱敏通用意图；如果没有这一行，adapter 无法把自然语言交给统一 planner。
# 新增代码+GenericSemanticPlanner：函数段结束，phase123_semantic_intent_from_prompt 到此结束；如果没有这个边界说明，代码小白不容易看出通用语义提取范围。


def phase123_plan_semantic_desktop_task(task: dict[str, Any], observation_frame: dict[str, Any], planner_model: str) -> list[dict[str, Any]]:  # 新增代码+GenericSemanticPlanner：函数段开始，把通用语义意图转成第一批 observe-plan-act 动作；如果没有这段函数，open_app 等非绘图任务仍会落回视觉兜底。
    _ = observation_frame  # 新增代码+GenericSemanticPlanner：保留观察帧参数以便后续按屏幕状态纠偏；如果没有这一行，读者会误以为通用 planner 不需要观察输入。
    intent = task.get("semantic_intent", {}) if isinstance(task, dict) else {}  # 新增代码+GenericSemanticPlanner：读取 adapter 提供的通用语义意图；如果没有这一行，planner 不知道当前任务类型。
    task_kind = str(intent.get("task_kind", "") if isinstance(intent, dict) else "").strip().lower()  # 新增代码+GenericSemanticPlanner：清洗任务类型字段；如果没有这一行，大小写或空值会让分支不稳定。
    if task_kind == "open_app":  # 新增代码+GenericSemanticPlanner：识别打开应用任务；如果没有这一行，打开 Notepad 会继续进入绘图兜底。
        return [{"type": "focus_window", "semantic_planner_action": True, "planner_model": planner_model, "semantic_role": "open_app_focus_target"}, {"type": "observe", "semantic_planner_action": True, "planner_model": planner_model, "semantic_role": "open_app_post_observe"}]  # 新增代码+GenericSemanticPlanner：返回聚焦和观察动作；如果没有这一行，打开应用后没有状态确认，也不会阻止 drag_path。
    if task_kind in {"browser_task", "generic_gui_task"}:  # 新增代码+GenericSemanticPlanner：识别开放式 GUI 任务；如果没有这一行，未知任务可能被误画成通用图形。
        return [{"type": "focus_window", "semantic_planner_action": True, "planner_model": planner_model, "semantic_role": "generic_gui_focus_target"}, {"type": "observe", "semantic_planner_action": True, "planner_model": planner_model, "semantic_role": "generic_gui_needs_model_planner_observe"}]  # 新增代码+GenericSemanticPlanner：先聚焦和观察并等待后续模型 planner；如果没有这一行，开放任务会被错误绘图兜底。
    return []  # 新增代码+GenericSemanticPlanner：绘图和文本输入暂交给后续专门分支；如果没有这一行，调用方无法继续走既有 draw/type_text 逻辑。
# 新增代码+GenericSemanticPlanner：函数段结束，phase123_plan_semantic_desktop_task 到此结束；如果没有这个边界说明，代码小白不容易看出语义动作规划范围。


__all__ = ["PHASE123_GENERIC_SEMANTIC_PLANNER_MODEL", "phase123_plan_semantic_desktop_task", "phase123_semantic_intent_from_prompt"]  # 新增代码+GenericSemanticPlanner：声明公开 API；如果没有这一行，通配导入会暴露内部 helper 或漏掉主入口。
