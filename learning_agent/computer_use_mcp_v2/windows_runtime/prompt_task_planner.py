"""Windows Computer Use Phase67 deterministic prompt task planner."""  # 新增代码+Phase67PromptTaskPlanner: 标明本文件负责 Phase67 从自然语言 prompt 生成任务计划；如果没有这行代码，读者不知道规划器入口在哪里。
from __future__ import annotations  # 新增代码+Phase67PromptTaskPlanner: 启用延迟类型解析；如果没有这行代码，未来前向类型标注更容易在旧入口导入失败。

import json  # 新增代码+Phase67PromptTaskPlanner: 导入 JSON 用于 CLI 输出结构化报告；如果没有这行代码，真实终端失败时不容易复盘计划字段。
from typing import Any  # 新增代码+Phase67PromptTaskPlanner: 导入 Any 描述 JSON 风格计划对象；如果没有这行代码，函数边界不清楚。

PHASE67_PROMPT_TASK_PLANNER_MARKER = "PHASE67_PROMPT_TASK_PLANNER_READY"  # 新增代码+Phase67PromptTaskPlanner: 定义 Phase67 ready marker；如果没有这行代码，真实终端验收没有稳定锚点。
PHASE67_PROMPT_TASK_PLANNER_OK_TOKEN = "PHASE67_PROMPT_TASK_PLANNER_OK"  # 新增代码+Phase67PromptTaskPlanner: 定义 Phase67 OK token；如果没有这行代码，debug log 无法区分规划器通过和普通输出。
PHASE67_PROMPT_TASK_PLANNER_MODEL = "phase67_windows_prompt_task_planner"  # 新增代码+Phase67PromptTaskPlanner: 定义规划器协议模型名；如果没有这行代码，后续执行器无法识别计划版本。
PHASE67_ACTIONS_EXPANDED = False  # 新增代码+Phase67PromptTaskPlanner: 明确 Phase67 只生成计划不扩大真实桌面动作；如果没有这行代码，安全审计无法确认本阶段没有新增输入能力。
PHASE67_HIGH_RISK_KEYWORDS = ("password", "payment", "admin", "administrator", "captcha", "login", "security", "credential", "token", "密码", "支付", "付款", "管理员", "验证码", "登录", "登陆", "安全", "凭据", "口令", "令牌")  # 新增代码+Phase67PromptTaskPlanner: 定义高风险关键词；如果没有这行代码，密码、支付、管理员等 prompt 无法先进入确认门禁。
PHASE67_PAINT_KEYWORDS = ("mspaint", "paint", "画图", "绘图", "皮卡丘", "pikachu", "卡通电气鼠")  # 新增代码+Phase67PromptTaskPlanner: 定义 Paint/皮卡丘关键词；如果没有这行代码，用户的代表性绘图场景无法被识别。
PHASE67_NOTEPAD_KEYWORDS = ("notepad", "记事本", "文本", "txt", "输入", "保存")  # 新增代码+Phase67PromptTaskPlanner: 定义记事本/文本任务关键词；如果没有这行代码，普通文本编辑 prompt 可能无法生成工作流。


# 新增代码+Phase67PromptTaskPlanner: 函数段开始，_phase67_bool_token 把布尔值转成小写验收 token；如果没有这段函数，CLI 输出会混用 True/False 和 true/false，作者意图是让真实终端断言稳定。
def _phase67_bool_token(value: Any) -> str:  # 新增代码+Phase67PromptTaskPlanner: 定义布尔 token helper；如果没有这行代码，多处输出会重复写转换逻辑。
    return "true" if bool(value) else "false"  # 新增代码+Phase67PromptTaskPlanner: 返回小写布尔文本；如果没有这行代码，场景 JSON 的 token 匹配可能失败。
# 新增代码+Phase67PromptTaskPlanner: 函数段结束，_phase67_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


# 新增代码+Phase67PromptTaskPlanner: 函数段开始，_phase67_prompt_text 清理用户 prompt；如果没有这段函数，None、空白或超长 prompt 会污染计划对象，作者意图是给规则规划器稳定输入。
def _phase67_prompt_text(prompt: Any) -> str:  # 新增代码+Phase67PromptTaskPlanner: 定义 prompt 清理函数；如果没有这行代码，planner 需要到处处理 None 和空白。
    text = " ".join(str(prompt or "").strip().split())  # 新增代码+Phase67PromptTaskPlanner: 把 prompt 转成单行干净文本；如果没有这行代码，换行和多空格会影响关键词识别。
    return text[:1000]  # 新增代码+Phase67PromptTaskPlanner: 限制 prompt 长度；如果没有这行代码，超长输入会挤占合同报告和终端输出。
# 新增代码+Phase67PromptTaskPlanner: 函数段结束，_phase67_prompt_text 到此结束；如果没有这个边界说明，初学者不容易看出 prompt 清理范围。


# 新增代码+Phase67PromptTaskPlanner: 函数段开始，_phase67_contains_any 判断文本是否命中任一关键词；如果没有这段函数，分类逻辑会重复写 any/lower，作者意图是让风险和应用识别稳定。
def _phase67_contains_any(text: str, keywords: tuple[str, ...]) -> bool:  # 新增代码+Phase67PromptTaskPlanner: 定义关键词匹配函数；如果没有这行代码，planner 的分类判断会散落。
    lowered = str(text or "").lower()  # 新增代码+Phase67PromptTaskPlanner: 转小写便于英文关键词匹配；如果没有这行代码，Paint/paint 大小写差异会影响识别。
    return any(keyword.lower() in lowered or keyword in text for keyword in keywords)  # 新增代码+Phase67PromptTaskPlanner: 返回是否命中关键词；如果没有这行代码，调用方拿不到分类结果。
# 新增代码+Phase67PromptTaskPlanner: 函数段结束，_phase67_contains_any 到此结束；如果没有这个边界说明，初学者不容易看出关键词判断范围。


# 新增代码+Phase67PromptTaskPlanner: 函数段开始，_phase67_step 构造闭环执行器可消费的单步计划；如果没有这段函数，每一步字段容易不一致，作者意图是强制每步都有 expected_result、risk_level 和 checkpoint。
def _phase67_step(step_id: int, operation: str, target: str, expected_result: str, checkpoint: str, risk_level: str = "normal", action_kind: str = "plan") -> dict[str, Any]:  # 新增代码+Phase67PromptTaskPlanner: 定义步骤构造函数；如果没有这行代码，计划步骤结构会漂移。
    return {"step_id": int(step_id), "operation": str(operation), "target": str(target), "action_kind": str(action_kind), "expected_result": str(expected_result), "risk_level": str(risk_level), "checkpoint": str(checkpoint), "requires_confirmation": str(risk_level) == "high"}  # 新增代码+Phase67PromptTaskPlanner: 返回完整步骤字典；如果没有这行代码，闭环执行器拿不到统一字段。
# 新增代码+Phase67PromptTaskPlanner: 函数段结束，_phase67_step 到此结束；如果没有这个边界说明，初学者不容易看出步骤构造范围。


# 新增代码+Phase67PromptTaskPlanner: 函数段开始，_phase67_all_steps_have 检查所有步骤是否包含必需字段；如果没有这段函数，合同报告会重复写三次遍历，作者意图是让验收字段统一。
def _phase67_all_steps_have(plans: list[dict[str, Any]], key: str) -> bool:  # 新增代码+Phase67PromptTaskPlanner: 定义步骤字段检查函数；如果没有这行代码，报告无法稳定判断 expected/risk/checkpoint。
    return all(bool(step.get(key)) for plan in plans for step in list(plan.get("steps", []) or []))  # 新增代码+Phase67PromptTaskPlanner: 返回所有步骤是否都有指定字段；如果没有这行代码，缺字段计划可能误过。
# 新增代码+Phase67PromptTaskPlanner: 函数段结束，_phase67_all_steps_have 到此结束；如果没有这个边界说明，初学者不容易看出字段检查范围。


# 新增代码+Phase67PromptTaskPlanner: 函数段开始，classify_risk 对 prompt 做高风险分类；如果没有这段函数，密码、支付、管理员等敏感请求可能直接进入执行计划，作者意图是让确认门禁早于动作规划。
def classify_risk(prompt: str) -> dict[str, Any]:  # 新增代码+Phase67PromptTaskPlanner: 定义风险分类入口；如果没有这行代码，测试和 planner 无法复用同一风险规则。
    text = _phase67_prompt_text(prompt)  # 新增代码+Phase67PromptTaskPlanner: 清理 prompt；如果没有这行代码，关键词匹配会受空白和 None 影响。
    lowered = text.lower()  # 新增代码+Phase67PromptTaskPlanner: 转小写便于英文高风险词匹配；如果没有这行代码，Admin/ADMIN 可能绕过规则。
    matched = [keyword for keyword in PHASE67_HIGH_RISK_KEYWORDS if keyword.lower() in lowered or keyword in text]  # 新增代码+Phase67PromptTaskPlanner: 收集命中的高风险关键词；如果没有这行代码，用户不知道为什么需要确认。
    requires_confirmation = bool(matched)  # 新增代码+Phase67PromptTaskPlanner: 命中高风险词就要求确认；如果没有这行代码，危险 prompt 可能继续被普通规划。
    risk_level = "high" if requires_confirmation else "normal"  # 新增代码+Phase67PromptTaskPlanner: 生成风险级别；如果没有这行代码，步骤无法继承风险。
    return {"risk_level": risk_level, "requires_confirmation": requires_confirmation, "matched_keywords": matched, "reason": "high_risk_keyword_match" if requires_confirmation else "normal_user_authorized_task"}  # 新增代码+Phase67PromptTaskPlanner: 返回结构化风险报告；如果没有这行代码，调用方拿不到分类结果。
# 新增代码+Phase67PromptTaskPlanner: 函数段结束，classify_risk 到此结束；如果没有这个边界说明，初学者不容易看出风险分类范围。


# 新增代码+Phase67PromptTaskPlanner: 类段开始，WindowsPromptTaskPlanner 把 prompt 转成通用 observe/act/verify 任务计划；如果没有这个类，Phase68 闭环执行器只能直接面对自然语言，作者意图是先规划再执行。
class WindowsPromptTaskPlanner:  # 新增代码+Phase67PromptTaskPlanner: 定义 Windows prompt 任务规划器；如果没有这行代码，调用方没有统一 planner 对象。
    def __init__(self, model: str = PHASE67_PROMPT_TASK_PLANNER_MODEL) -> None:  # 新增代码+Phase67PromptTaskPlanner: 函数段开始，初始化规划器模型名；如果没有这段函数，状态无法说明计划协议版本。
        self.model = str(model or PHASE67_PROMPT_TASK_PLANNER_MODEL)  # 新增代码+Phase67PromptTaskPlanner: 保存模型名并兜底默认值；如果没有这行代码，计划对象缺少版本锚点。
    # 新增代码+Phase67PromptTaskPlanner: 函数段结束，WindowsPromptTaskPlanner.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def plan(self, prompt: str) -> dict[str, Any]:  # 新增代码+Phase67PromptTaskPlanner: 函数段开始，把用户 prompt 转成确定性任务计划；如果没有这段函数，后续执行器没有结构化步骤输入。
        text = _phase67_prompt_text(prompt)  # 新增代码+Phase67PromptTaskPlanner: 清理 prompt 输入；如果没有这行代码，分类和输出会受空白影响。
        risk = classify_risk(text)  # 新增代码+Phase67PromptTaskPlanner: 先做风险分类；如果没有这行代码，高风险动作可能排在确认之前。
        if bool(risk.get("requires_confirmation")):  # 新增代码+Phase67PromptTaskPlanner: 高风险 prompt 优先进入确认计划；如果没有这行代码，危险场景会继续生成动作步骤。
            return self._finalize_plan(text, "generic", "high_risk_confirmation", self._high_risk_steps(risk), risk, representative_scenario=False)  # 新增代码+Phase67PromptTaskPlanner: 返回高风险确认计划；如果没有这行代码，用户确认门禁不会生效。
        if _phase67_contains_any(text, PHASE67_PAINT_KEYWORDS):  # 新增代码+Phase67PromptTaskPlanner: 判断是否是 Paint/皮卡丘绘图需求；如果没有这行代码，代表性 Paint 场景无法识别。
            return self._finalize_plan(text, "mspaint", "paint_pikachu_drawing", self._paint_pikachu_steps(), risk, representative_scenario=True)  # 新增代码+Phase67PromptTaskPlanner: 返回 Paint 皮卡丘计划；如果没有这行代码，Phase74 代表场景没有规划入口。
        if _phase67_contains_any(text, PHASE67_NOTEPAD_KEYWORDS):  # 新增代码+Phase67PromptTaskPlanner: 判断是否是记事本/文本任务；如果没有这行代码，普通文本编辑 prompt 无法生成专门工作流。
            return self._finalize_plan(text, "notepad", "text_editing", self._notepad_steps(text), risk, representative_scenario=False)  # 新增代码+Phase67PromptTaskPlanner: 返回记事本文本计划；如果没有这行代码，文本任务会退回过粗泛化计划。
        return self._finalize_plan(text, "generic", "generic_windows_task", self._generic_steps(), risk, representative_scenario=False)  # 新增代码+Phase67PromptTaskPlanner: 返回通用 Windows 任务计划；如果没有这行代码，未知 prompt 会没有计划结果。
    # 新增代码+Phase67PromptTaskPlanner: 函数段结束，WindowsPromptTaskPlanner.plan 到此结束；如果没有这个边界说明，初学者不容易看出主规划流程范围。

    def _high_risk_steps(self, risk: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+Phase67PromptTaskPlanner: 函数段开始，生成高风险确认步骤；如果没有这段函数，危险请求可能没有明确停止点。
        reason = ",".join(list(risk.get("matched_keywords", []) or [])) or "high_risk"  # 新增代码+Phase67PromptTaskPlanner: 生成可读风险原因；如果没有这行代码，用户不知道为什么被要求确认。
        return [_phase67_step(1, "request_user_confirmation", "user", f"用户明确确认高风险请求后才允许继续，原因={reason}", "确认请求被展示且没有执行真实动作", "high", "approval"), _phase67_step(2, "stop_before_action", "computer", "在确认前不启动、不点击、不输入、不保存", "低层事件数量保持为 0", "high", "guard")]  # 新增代码+Phase67PromptTaskPlanner: 返回高风险停止计划；如果没有这行代码，确认门禁没有结构化步骤。
    # 新增代码+Phase67PromptTaskPlanner: 函数段结束，WindowsPromptTaskPlanner._high_risk_steps 到此结束；如果没有这个边界说明，初学者不容易看出高风险计划范围。

    def _paint_pikachu_steps(self) -> list[dict[str, Any]]:  # 新增代码+Phase67PromptTaskPlanner: 函数段开始，生成 Paint 皮卡丘代表场景的通用步骤；如果没有这段函数，用户新增的画图验收目标没有规划模板。
        return [_phase67_step(1, "launch_app", "mspaint", "画图软件窗口可见且成为目标窗口", "窗口标题或 app_id 指向 mspaint", "normal", "prepare"), _phase67_step(2, "observe_window", "mspaint", "获得截图、UIA 和窗口状态融合观察", "fused_observation 可用且目标未漂移", "normal", "observe"), _phase67_step(3, "identify_canvas", "paint_canvas", "识别可绘制画布区域", "画布候选具有 bounds 或视觉区域", "normal", "observe"), _phase67_step(4, "select_tool", "brush_or_pencil", "选择可连续绘制的画笔工具", "工具选择后仍聚焦 Paint", "normal", "plan"), _phase67_step(5, "select_color", "yellow", "选择黄色用于皮卡丘主体", "颜色状态或后续像素验证显示黄色可用", "normal", "plan"), _phase67_step(6, "draw_body", "paint_canvas", "绘制黄色圆形或椭圆主体", "画布出现黄色主体区域", "normal", "write"), _phase67_step(7, "select_color", "black", "选择黑色用于耳尖、眼睛和轮廓", "颜色状态或后续像素验证显示黑色可用", "normal", "plan"), _phase67_step(8, "draw_face_and_ears", "paint_canvas", "绘制黑色耳尖、眼睛和嘴巴", "画布出现面部和耳朵特征", "normal", "write"), _phase67_step(9, "select_color", "red", "选择红色用于脸颊", "颜色状态或后续像素验证显示红色可用", "normal", "plan"), _phase67_step(10, "draw_cheeks", "paint_canvas", "绘制左右红色脸颊", "画布出现红色脸颊元素", "normal", "write"), _phase67_step(11, "draw_tail", "paint_canvas", "绘制闪电形尾巴", "画布出现可识别的闪电尾巴", "normal", "write"), _phase67_step(12, "save_artifact", "paint_file", "通过应用保存绘图结果和证据", "保存路径或文件对话完成且不是直接生成图片作弊", "normal", "write"), _phase67_step(13, "verify_visual_result", "paint_canvas_or_saved_file", "验证黄色主体、黑色耳尖、红色脸颊和尾巴存在", "视觉证据满足 mspaint_pikachu_scenario", "normal", "verify")]  # 新增代码+Phase67PromptTaskPlanner: 返回 Paint 通用步骤列表；如果没有这行代码，代表场景计划为空。
    # 新增代码+Phase67PromptTaskPlanner: 函数段结束，WindowsPromptTaskPlanner._paint_pikachu_steps 到此结束；如果没有这个边界说明，初学者不容易看出 Paint 规划范围。

    def _notepad_steps(self, prompt: str) -> list[dict[str, Any]]:  # 新增代码+Phase67PromptTaskPlanner: 函数段开始，生成记事本文本任务通用步骤；如果没有这段函数，普通文本应用任务无法演示通用性。
        _ = prompt  # 新增代码+Phase67PromptTaskPlanner: 保留 prompt 扩展位；如果没有这行代码，读者可能误以为函数遗漏输入用途。
        return [_phase67_step(1, "launch_app", "notepad", "记事本窗口可见且成为目标窗口", "窗口标题或 app_id 指向 notepad", "normal", "prepare"), _phase67_step(2, "observe_window", "notepad", "获得文本编辑区候选", "UIA 或截图显示可编辑区域", "normal", "observe"), _phase67_step(3, "focus_text_area", "notepad_editor", "文本输入焦点进入编辑区", "光标或 UIA 焦点位于编辑控件", "normal", "plan"), _phase67_step(4, "type_text", "notepad_editor", "用户要求的文本被输入到编辑区", "后置观察能看到目标文本摘要", "normal", "write"), _phase67_step(5, "save_document", "notepad_file", "通过应用保存文档", "保存对话或文件状态显示完成", "normal", "write"), _phase67_step(6, "verify_result", "notepad_file_or_editor", "验证文本内容和保存状态", "观察结果匹配用户要求", "normal", "verify")]  # 新增代码+Phase67PromptTaskPlanner: 返回记事本通用步骤列表；如果没有这行代码，文本任务计划为空。
    # 新增代码+Phase67PromptTaskPlanner: 函数段结束，WindowsPromptTaskPlanner._notepad_steps 到此结束；如果没有这个边界说明，初学者不容易看出记事本规划范围。

    def _generic_steps(self) -> list[dict[str, Any]]:  # 新增代码+Phase67PromptTaskPlanner: 函数段开始，生成未知普通 Windows 任务的通用步骤；如果没有这段函数，未识别 prompt 会完全没有计划。
        return [_phase67_step(1, "infer_target_app", "prompt", "从 prompt 推断目标普通应用或请求澄清", "目标应用候选存在或需要用户补充", "normal", "plan"), _phase67_step(2, "observe_window", "target_window", "观察目标窗口状态和控件候选", "fused_observation 可用于下一步", "normal", "observe"), _phase67_step(3, "build_action_candidates", "target_window", "生成可验证的候选动作而不是盲坐标链", "每个动作都绑定 expected_result", "normal", "plan"), _phase67_step(4, "verify_result", "target_window", "执行后必须观察并验证结果", "结果和 prompt 目标一致", "normal", "verify")]  # 新增代码+Phase67PromptTaskPlanner: 返回通用计划步骤；如果没有这行代码，未知 prompt 无法进入闭环。
    # 新增代码+Phase67PromptTaskPlanner: 函数段结束，WindowsPromptTaskPlanner._generic_steps 到此结束；如果没有这个边界说明，初学者不容易看出通用规划范围。

    def _finalize_plan(self, prompt: str, app: str, task_type: str, steps: list[dict[str, Any]], risk: dict[str, Any], representative_scenario: bool) -> dict[str, Any]:  # 新增代码+Phase67PromptTaskPlanner: 函数段开始，补齐计划公共字段；如果没有这段函数，不同 app 计划会出现字段漂移。
        return {"marker": PHASE67_PROMPT_TASK_PLANNER_MARKER, "model": self.model, "prompt": str(prompt), "app": str(app), "task_type": str(task_type), "prompt_task_plan": True, "steps": list(steps), "step_count": len(steps), "risk_level": str(risk.get("risk_level", "normal")), "risk_reasons": list(risk.get("matched_keywords", []) or []), "requires_confirmation": bool(risk.get("requires_confirmation")), "high_risk_confirmation": bool(risk.get("requires_confirmation")), "representative_scenario": bool(representative_scenario), "paint_pikachu_scenario": bool(representative_scenario and app == "mspaint"), "per_app_script": False, "deterministic_rule_planner": True, "llm_called": False, "actions_expanded": PHASE67_ACTIONS_EXPANDED}  # 新增代码+Phase67PromptTaskPlanner: 返回完整计划对象；如果没有这行代码，测试和后续执行器拿不到统一字段。
    # 新增代码+Phase67PromptTaskPlanner: 函数段结束，WindowsPromptTaskPlanner._finalize_plan 到此结束；如果没有这个边界说明，初学者不容易看出公共字段补齐范围。
# 新增代码+Phase67PromptTaskPlanner: 类段结束，WindowsPromptTaskPlanner 到此结束；如果没有这个边界说明，初学者不容易看出规划器类范围。


# 新增代码+Phase67PromptTaskPlanner: 函数段开始，run_phase67_prompt_task_planner_contract 运行 Phase67 合同自检；如果没有这段函数，CLI、测试和真实终端没有统一事实源。
def run_phase67_prompt_task_planner_contract() -> dict[str, Any]:  # 新增代码+Phase67PromptTaskPlanner: 定义 Phase67 合同入口；如果没有这行代码，测试和场景无法调用同一逻辑。
    planner = WindowsPromptTaskPlanner()  # 新增代码+Phase67PromptTaskPlanner: 创建确定性规则规划器；如果没有这行代码，合同没有 planner 实例。
    notepad_plan = planner.plan("打开记事本，输入 hello phase67，然后保存")  # 新增代码+Phase67PromptTaskPlanner: 生成记事本合同计划；如果没有这行代码，文本应用路径没有合同证据。
    paint_plan = planner.plan("打开画图软件，画一个简化皮卡丘并保存")  # 新增代码+Phase67PromptTaskPlanner: 生成 Paint 皮卡丘合同计划；如果没有这行代码，代表绘图场景没有合同证据。
    high_risk_plan = planner.plan("用管理员权限打开支付页面并输入密码")  # 新增代码+Phase67PromptTaskPlanner: 生成高风险合同计划；如果没有这行代码，确认门禁没有合同证据。
    plans = [notepad_plan, paint_plan, high_risk_plan]  # 新增代码+Phase67PromptTaskPlanner: 汇总三个合同计划；如果没有这行代码，后续检查需要重复传参。
    prompt_task_plan = all(bool(plan.get("prompt_task_plan")) and bool(plan.get("steps")) for plan in plans)  # 新增代码+Phase67PromptTaskPlanner: 判断所有 prompt 都生成步骤计划；如果没有这行代码，空计划可能误过。
    expected_result_per_step = _phase67_all_steps_have(plans, "expected_result")  # 新增代码+Phase67PromptTaskPlanner: 检查每步预期结果；如果没有这行代码，闭环执行器缺少验收目标。
    risk_level_per_step = _phase67_all_steps_have(plans, "risk_level")  # 新增代码+Phase67PromptTaskPlanner: 检查每步风险级别；如果没有这行代码，高风险步骤可能漏标。
    checkpoint_per_step = _phase67_all_steps_have(plans, "checkpoint")  # 新增代码+Phase67PromptTaskPlanner: 检查每步检查点；如果没有这行代码，失败恢复缺少锚点。
    paint_operations = {str(step.get("operation", "")) for step in list(paint_plan.get("steps", []) or [])}  # 新增代码+Phase67PromptTaskPlanner: 收集 Paint 操作名；如果没有这行代码，代表场景判断需要重复遍历。
    paint_pikachu_prompt = bool(paint_plan.get("app") == "mspaint" and paint_plan.get("representative_scenario") and {"identify_canvas", "select_color", "draw_body", "draw_tail", "save_artifact", "verify_visual_result"}.issubset(paint_operations))  # 新增代码+Phase67PromptTaskPlanner: 判断 Paint 皮卡丘计划是否完整；如果没有这行代码，少关键步骤仍可能通过。
    high_risk_confirmation = bool(high_risk_plan.get("requires_confirmation") and high_risk_plan.get("steps", [{}])[0].get("operation") == "request_user_confirmation")  # 新增代码+Phase67PromptTaskPlanner: 判断高风险确认是否排在第一步；如果没有这行代码，危险动作可能在确认前出现。
    deterministic_rule_planner = all(bool(plan.get("deterministic_rule_planner")) and not bool(plan.get("llm_called")) for plan in plans)  # 新增代码+Phase67PromptTaskPlanner: 确认合同没有调用 LLM；如果没有这行代码，单测可能变得不稳定。
    per_app_scripts_required = any(bool(plan.get("per_app_script")) for plan in plans)  # 新增代码+Phase67PromptTaskPlanner: 检查是否退回应用专用脚本；如果没有这行代码，通用拟人目标可能漂移。
    passed = bool(prompt_task_plan and expected_result_per_step and risk_level_per_step and checkpoint_per_step and paint_pikachu_prompt and high_risk_confirmation and deterministic_rule_planner and not per_app_scripts_required and not PHASE67_ACTIONS_EXPANDED)  # 新增代码+Phase67PromptTaskPlanner: 汇总合同通过条件；如果没有这行代码，main 无法用退出码表达成功或失败。
    return {"marker": PHASE67_PROMPT_TASK_PLANNER_MARKER, "ok_token": PHASE67_PROMPT_TASK_PLANNER_OK_TOKEN, "model": PHASE67_PROMPT_TASK_PLANNER_MODEL, "prompt_task_plan": prompt_task_plan, "expected_result_per_step": expected_result_per_step, "risk_level_per_step": risk_level_per_step, "checkpoint_per_step": checkpoint_per_step, "paint_pikachu_prompt": paint_pikachu_prompt, "high_risk_confirmation": high_risk_confirmation, "deterministic_rule_planner": deterministic_rule_planner, "per_app_scripts_required": per_app_scripts_required, "actions_expanded": PHASE67_ACTIONS_EXPANDED, "passed": passed, "plans": {"notepad": notepad_plan, "paint_pikachu": paint_plan, "high_risk": high_risk_plan}}  # 新增代码+Phase67PromptTaskPlanner: 返回完整合同报告；如果没有这行代码，CLI、测试和真实终端拿不到结构化结果。
# 新增代码+Phase67PromptTaskPlanner: 函数段结束，run_phase67_prompt_task_planner_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同运行范围。


# 新增代码+Phase67PromptTaskPlanner: 函数段开始，phase67_cli_line 把合同报告转成固定顺序 token 行；如果没有这段函数，真实终端场景需要解析复杂 JSON，作者意图是让最终回答可复制可验收。
def phase67_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase67PromptTaskPlanner: 定义 Phase67 CLI 行格式化函数；如果没有这行代码，main 无法打印固定顺序 token。
    return f"{PHASE67_PROMPT_TASK_PLANNER_MARKER} {PHASE67_PROMPT_TASK_PLANNER_OK_TOKEN} prompt_task_plan={_phase67_bool_token(report.get('prompt_task_plan'))} expected_result_per_step={_phase67_bool_token(report.get('expected_result_per_step'))} risk_level_per_step={_phase67_bool_token(report.get('risk_level_per_step'))} checkpoint_per_step={_phase67_bool_token(report.get('checkpoint_per_step'))} paint_pikachu_prompt={_phase67_bool_token(report.get('paint_pikachu_prompt'))} high_risk_confirmation={_phase67_bool_token(report.get('high_risk_confirmation'))} actions_expanded={_phase67_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase67PromptTaskPlanner: 返回固定顺序 token 行；如果没有这行代码，验收器无法稳定匹配 Phase67 合同。
# 新增代码+Phase67PromptTaskPlanner: 函数段结束，phase67_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 文本范围。


# 新增代码+Phase67PromptTaskPlanner: 函数段开始，main 提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase67 合同，作者意图是自动化和可见终端共用同一合同。
def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase67PromptTaskPlanner: 定义命令行入口并保留 argv 扩展位；如果没有这行代码，python -c 只能手写调用细节。
    _ = argv  # 新增代码+Phase67PromptTaskPlanner: 明确当前 Phase67 不解析命令行参数；如果没有这行代码，读者可能误以为 argv 被遗漏。
    report = run_phase67_prompt_task_planner_contract()  # 新增代码+Phase67PromptTaskPlanner: 运行 Phase67 合同；如果没有这行代码，CLI 输出没有真实依据。
    print(phase67_cli_line(report))  # 新增代码+Phase67PromptTaskPlanner: 打印稳定单行 token；如果没有这行代码，验收器无法快速匹配合同结果。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase67PromptTaskPlanner: 打印结构化报告便于人工复盘；如果没有这行代码，失败时不容易定位哪条规划边界失败。
    print(PHASE67_PROMPT_TASK_PLANNER_MARKER)  # 新增代码+Phase67PromptTaskPlanner: 单独打印 ready marker；如果没有这行代码，真实终端验收可能看不到明确阶段标记。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase67PromptTaskPlanner: 根据合同结果返回退出码；如果没有这行代码，失败也可能被终端当成成功。
# 新增代码+Phase67PromptTaskPlanner: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = ["PHASE67_ACTIONS_EXPANDED", "PHASE67_PROMPT_TASK_PLANNER_MARKER", "PHASE67_PROMPT_TASK_PLANNER_MODEL", "PHASE67_PROMPT_TASK_PLANNER_OK_TOKEN", "WindowsPromptTaskPlanner", "classify_risk", "main", "phase67_cli_line", "run_phase67_prompt_task_planner_contract"]  # 新增代码+Phase67PromptTaskPlanner: 限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase67PromptTaskPlanner: 允许直接运行本模块；如果没有这行代码，初学者无法用 python 文件方式手动执行 Phase67 自检。
    raise SystemExit(main())  # 新增代码+Phase67PromptTaskPlanner: 调用 main 并传递退出码；如果没有这行代码，直接运行文件不会执行验收。
