"""Deterministic intent understanding layer for universal Computer Use."""  # 新增代码+IntentUnderstandingLayer：说明本文件负责用户意图结构化，不负责执行动作；如果没有这行代码，读者可能把低层动作规划写进这里。
from __future__ import annotations  # 新增代码+IntentUnderstandingLayer：启用延迟类型解析；如果没有这行代码，类型注解在脚本入口更容易失败。

import re  # 新增代码+IntentUnderstandingLayer：导入正则抽取文件名和引号文本；如果没有这行代码，确定性解析会很脆弱。
from typing import Any, Mapping  # 新增代码+IntentUnderstandingLayer：导入 JSON 风格类型；如果没有这行代码，接口边界不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.layer_contracts import IntentUnderstandingResult  # 新增代码+IntentUnderstandingLayer：导入 intent 契约；如果没有这行代码，输出会变成散乱字典。
from learning_agent.computer_use_mcp_v2.windows_runtime.layer_skill_loader import load_layer_skill  # 新增代码+IntentUnderstandingLayer：导入内部层 skill loader；如果没有这行代码，结果无法带 prompt 版本元数据。


TEXT_APP_HINT_TERMS = ("文本编辑", "记事", "文档", "text editor", "editor", "notepad")  # 新增代码+IntentUnderstandingLayer：定义文本软件提示词；如果没有这行代码，用户说文本软件时无法提取目标提示。
DRAWING_APP_HINT_TERMS = ("绘图", "画图", "绘画", "drawing", "paint", "canvas")  # 新增代码+IntentUnderstandingLayer：定义绘图软件提示词；如果没有这行代码，绘图任务无法提取目标提示。
NAVIGATION_APP_HINT_TERMS = ("浏览器", "网页", "搜索", "browser", "web", "chrome", "edge")  # 新增代码+IntentUnderstandingLayer：定义导航软件提示词；如果没有这行代码，浏览任务无法提取目标提示。
SINGLE_INSTANCE_TERMS = ("只能开一个", "单实例", "已有窗口", "existing window", "single instance")  # 新增代码+IntentUnderstandingLayer：定义单实例或旧窗口线索；如果没有这行代码，授权判断缺输入。
EXISTING_GRANT_TERMS = ("授权使用已有", "允许使用已有", "复用已有", "use existing", "reuse existing", "authorized existing")  # 新增代码+IntentUnderstandingLayer：定义显式允许旧窗口线索；如果没有这行代码，单实例应用无法安全放行。
RISK_TERMS = ("删除", "支付", "转账", "提交订单", "delete", "pay", "transfer", "purchase")  # 新增代码+IntentUnderstandingLayer：定义高风险词；如果没有这行代码，风险级别无法提高。
TEXT_PAYLOAD_PATTERNS = (r"`([^`]{1,240})`", r"“([^”]{1,240})”", r"\"([^\"]{1,240})\"", r"输入(?:文本|内容)?[ ：:]*([A-Za-z0-9 _.,!?-]{1,160})")  # 新增代码+IntentUnderstandingLayer：定义正文抽取模式；如果没有这行代码，文本输入内容会丢失。
ARTIFACT_PATTERN = re.compile(r"([\w\u4e00-\u9fff-]+\.(?:txt|md|png|jpg|jpeg|bmp|csv|xlsx|docx|pptx|pdf))", re.IGNORECASE)  # 新增代码+IntentUnderstandingLayer：定义常见产物文件名模式；如果没有这行代码，保存请求缺文件名。


def _intent_text(value: Any) -> str:  # 新增代码+IntentUnderstandingLayer：函数段开始，清洗用户 prompt；如果没有这段函数，换行和空白会影响解析。
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())  # 新增代码+IntentUnderstandingLayer：返回单行文本；如果没有这行代码，正则和 contains 判断不稳定。
# 新增代码+IntentUnderstandingLayer：函数段结束，_intent_text 到此结束；如果没有这个边界说明，用户不容易看出清洗范围。


def _intent_contains_any(text: str, terms: tuple[str, ...]) -> bool:  # 新增代码+IntentUnderstandingLayer：函数段开始，判断文本是否命中任一词；如果没有这段函数，多处会重复大小写逻辑。
    lowered = text.lower()  # 新增代码+IntentUnderstandingLayer：生成小写文本；如果没有这行代码，英文大小写会影响匹配。
    return any(term.lower() in lowered for term in terms)  # 新增代码+IntentUnderstandingLayer：任一词命中即返回真；如果没有这行代码，调用方无法简洁判断。
# 新增代码+IntentUnderstandingLayer：函数段结束，_intent_contains_any 到此结束；如果没有这个边界说明，用户不容易看出匹配范围。


def _intent_task_kind(text: str) -> str:  # 新增代码+IntentUnderstandingLayer：函数段开始，提取通用任务类型；如果没有这段函数，planner 会继续自己重复解析。
    if _intent_contains_any(text, ("同时", "多个", "另一个", "multi", "multiple", "two")):  # 新增代码+IntentUnderstandingLayer：多目标语义优先；如果没有这行代码，多应用任务会被压成单窗口。
        return "multi_app"  # 新增代码+IntentUnderstandingLayer：返回多应用任务；如果没有这行代码，目标拆分无法进行。
    if _intent_contains_any(text, DRAWING_APP_HINT_TERMS + ("绘制", "画", "上色", "draw", "color")):  # 新增代码+IntentUnderstandingLayer：识别绘图任务；如果没有这行代码，绘图会变成未知 GUI。
        return "drawing"  # 新增代码+IntentUnderstandingLayer：返回绘图任务；如果没有这行代码，stage planner 无法选择画布阶段。
    if _intent_contains_any(text, NAVIGATION_APP_HINT_TERMS + ("网址", "查看结果", "search", "url", "page")):  # 新增代码+IntentUnderstandingLayer：识别导航任务；如果没有这行代码，浏览任务缺通用类型。
        return "navigation"  # 新增代码+IntentUnderstandingLayer：返回导航任务；如果没有这行代码，planner 无法选择导航阶段。
    if _intent_contains_any(text, TEXT_APP_HINT_TERMS + ("输入", "键入", "写入", "type", "write", "enter")):  # 新增代码+IntentUnderstandingLayer：识别文本任务；如果没有这行代码，文本输入会变未知。
        return "text_entry"  # 新增代码+IntentUnderstandingLayer：返回文本任务；如果没有这行代码，批编译器缺文本语义。
    return "unknown_gui"  # 新增代码+IntentUnderstandingLayer：无明确线索时保持未知；如果没有这行代码，系统可能盲动未知软件。
# 新增代码+IntentUnderstandingLayer：函数段结束，_intent_task_kind 到此结束；如果没有这个边界说明，用户不容易看出任务类型范围。


def _intent_target_hints(text: str, task_kind: str) -> tuple[str, ...]:  # 新增代码+IntentUnderstandingLayer：函数段开始，提取用户的软件提示；如果没有这段函数，启动层只能靠抽象任务类型。
    hints: list[str] = []  # 新增代码+IntentUnderstandingLayer：初始化提示列表；如果没有这行代码，无法累加多个目标提示。
    if task_kind == "text_entry" or _intent_contains_any(text, TEXT_APP_HINT_TERMS):  # 新增代码+IntentUnderstandingLayer：检查文本软件线索；如果没有这行代码，文本目标无法写入 hints。
        hints.append("text_editor")  # 新增代码+IntentUnderstandingLayer：记录通用文本编辑器提示；如果没有这行代码，后续启动层缺目标候选。
    if task_kind == "drawing" or _intent_contains_any(text, DRAWING_APP_HINT_TERMS):  # 新增代码+IntentUnderstandingLayer：检查绘图软件线索；如果没有这行代码，绘图目标无法写入 hints。
        hints.append("drawing_app")  # 新增代码+IntentUnderstandingLayer：记录通用绘图软件提示；如果没有这行代码，启动层缺画布应用候选。
    if task_kind == "navigation" or _intent_contains_any(text, NAVIGATION_APP_HINT_TERMS):  # 新增代码+IntentUnderstandingLayer：检查导航软件线索；如果没有这行代码，浏览目标无法写入 hints。
        hints.append("navigation_app")  # 新增代码+IntentUnderstandingLayer：记录通用导航软件提示；如果没有这行代码，启动层缺浏览候选。
    if task_kind == "multi_app" and not hints:  # 新增代码+IntentUnderstandingLayer：多应用但未显式识别目标时兜底；如果没有这行代码，多窗口目标提示可能为空。
        hints.extend(["source_app", "destination_app"])  # 新增代码+IntentUnderstandingLayer：记录源和目的应用提示；如果没有这行代码，多目标 planner 缺目标角色。
    return tuple(dict.fromkeys(hints))  # 新增代码+IntentUnderstandingLayer：去重并保序返回；如果没有这行代码，重复提示会污染证据。
# 新增代码+IntentUnderstandingLayer：函数段结束，_intent_target_hints 到此结束；如果没有这个边界说明，用户不容易看出目标提示范围。


def _intent_content_payloads(text: str) -> tuple[str, ...]:  # 新增代码+IntentUnderstandingLayer：函数段开始，抽取用户要求输入或使用的短内容；如果没有这段函数，文本阶段会丢正文。
    payloads: list[str] = []  # 新增代码+IntentUnderstandingLayer：初始化内容列表；如果没有这行代码，无法累加多种模式。
    for pattern in TEXT_PAYLOAD_PATTERNS:  # 新增代码+IntentUnderstandingLayer：遍历正文模式；如果没有这行代码，正则规则不会执行。
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):  # 新增代码+IntentUnderstandingLayer：查找所有模式命中；如果没有这行代码，只能抽一个或抽不到。
            candidate = _intent_text(match.group(1)).strip(" ：:，,。.;；`\"'“”")  # 新增代码+IntentUnderstandingLayer：清洗正文候选；如果没有这行代码，正文会带提示标点。
            if candidate and len(candidate) <= 200:  # 新增代码+IntentUnderstandingLayer：只保留短内容；如果没有这行代码，整段 prompt 可能被当正文。
                payloads.append(candidate)  # 新增代码+IntentUnderstandingLayer：保存正文候选；如果没有这行代码，抽取结果不会返回。
    return tuple(dict.fromkeys(payloads))  # 新增代码+IntentUnderstandingLayer：去重并返回元组；如果没有这行代码，重复正文会污染结果。
# 新增代码+IntentUnderstandingLayer：函数段结束，_intent_content_payloads 到此结束；如果没有这个边界说明，用户不容易看出正文抽取范围。


def _intent_artifact_requests(text: str) -> tuple[dict[str, Any], ...]:  # 新增代码+IntentUnderstandingLayer：函数段开始，提取输出文件和位置请求；如果没有这段函数，保存阶段缺目标产物。
    location_hint = "desktop" if "桌面" in text.lower() or "desktop" in text.lower() else "user_requested_location"  # 新增代码+IntentUnderstandingLayer：识别保存位置；如果没有这行代码，保存到桌面无法结构化。
    artifacts = [{"filename": match.group(1), "location_hint": location_hint, "commit_required": True} for match in ARTIFACT_PATTERN.finditer(text)]  # 新增代码+IntentUnderstandingLayer：为每个文件名构造产物请求；如果没有这行代码，文件名无法传给后续层。
    if not artifacts and _intent_contains_any(text, ("保存", "存到", "导出", "save", "export")):  # 新增代码+IntentUnderstandingLayer：有保存语义但未给文件名时保留通用产物；如果没有这行代码，提交阶段可能缺资源。
        artifacts.append({"filename": "", "location_hint": location_hint, "commit_required": True})  # 新增代码+IntentUnderstandingLayer：添加无文件名产物请求；如果没有这行代码，verifier 不知道需要保存。
    return tuple(artifacts)  # 新增代码+IntentUnderstandingLayer：返回产物请求元组；如果没有这行代码，调用方拿不到结果。
# 新增代码+IntentUnderstandingLayer：函数段结束，_intent_artifact_requests 到此结束；如果没有这个边界说明，用户不容易看出产物抽取范围。


def _intent_required_targets(task_kind: str, target_hints: tuple[str, ...]) -> tuple[dict[str, Any], ...]:  # 新增代码+IntentUnderstandingLayer：函数段开始，按任务类型生成目标需求；如果没有这段函数，多目标所有权无法表达。
    if task_kind == "multi_app":  # 新增代码+IntentUnderstandingLayer：多应用任务需要两个目标；如果没有这行代码，多应用会被压成单目标。
        return ({"target_ref": "target_1", "target_role": "source", "target_hint": target_hints[0] if target_hints else "source_app"}, {"target_ref": "target_2", "target_role": "destination", "target_hint": target_hints[-1] if target_hints else "destination_app"})  # 新增代码+IntentUnderstandingLayer：返回源和目的目标；如果没有这行代码，跨应用阶段缺绑定对象。
    return ({"target_ref": "target_1", "target_role": "primary", "target_hint": target_hints[0] if target_hints else task_kind},)  # 新增代码+IntentUnderstandingLayer：返回单主目标；如果没有这行代码，普通任务缺 target_ref。
# 新增代码+IntentUnderstandingLayer：函数段结束，_intent_required_targets 到此结束；如果没有这个边界说明，用户不容易看出目标需求范围。


def _intent_success_criteria(task_kind: str, artifacts: tuple[dict[str, Any], ...], payloads: tuple[str, ...]) -> tuple[str, ...]:  # 新增代码+IntentUnderstandingLayer：函数段开始，生成通用成功标准；如果没有这段函数，验证层缺目标。
    criteria = ["target_identity_verified", "stage_verifier_completed"]  # 新增代码+IntentUnderstandingLayer：加入所有任务通用标准；如果没有这行代码，窗口身份不进入验收。
    if payloads and task_kind == "text_entry":  # 新增代码+IntentUnderstandingLayer：文本任务有正文时添加文本标准；如果没有这行代码，输入内容无法验证。
        criteria.append("requested_text_visible_or_saved")  # 新增代码+IntentUnderstandingLayer：要求正文可见或保存；如果没有这行代码，文本任务可能只发事件就成功。
    if task_kind == "drawing":  # 新增代码+IntentUnderstandingLayer：绘图任务添加视觉标准；如果没有这行代码，绘图任务无法验证质量。
        criteria.append("canvas_changed_with_visual_structure")  # 新增代码+IntentUnderstandingLayer：要求画布变化和结构；如果没有这行代码，单线条也可能误过。
    if task_kind == "navigation":  # 新增代码+IntentUnderstandingLayer：导航任务添加结果标准；如果没有这行代码，导航任务可能只打开窗口。
        criteria.append("navigation_result_visible")  # 新增代码+IntentUnderstandingLayer：要求导航结果可见；如果没有这行代码，搜索任务无法验收。
    if artifacts:  # 新增代码+IntentUnderstandingLayer：有产物请求时添加保存标准；如果没有这行代码，保存缺口不能被 final gate 识别。
        criteria.append("resource_commit_verified")  # 新增代码+IntentUnderstandingLayer：要求资源提交验证；如果没有这行代码，未保存也可能 final。
    return tuple(dict.fromkeys(criteria))  # 新增代码+IntentUnderstandingLayer：去重并返回；如果没有这行代码，重复标准会污染报告。
# 新增代码+IntentUnderstandingLayer：函数段结束，_intent_success_criteria 到此结束；如果没有这个边界说明，用户不容易看出成功标准范围。


def understand_desktop_intent(prompt: str, context: Mapping[str, Any] | None = None) -> IntentUnderstandingResult:  # 新增代码+IntentUnderstandingLayer：函数段开始，确定性抽取用户桌面任务意图；如果没有这段函数，planner 会继续重复低质量解析。
    text = _intent_text(prompt)  # 新增代码+IntentUnderstandingLayer：清洗 prompt；如果没有这行代码，分类和抽取会受换行影响。
    prompt_meta = load_layer_skill("intent_understanding").metadata()  # 新增代码+IntentUnderstandingLayer：加载内部层 skill 元数据；如果没有这行代码，结果无法说明 prompt 版本。
    semantic_kind = _intent_text((context or {}).get("task_kind", ""))  # 新增代码+IntentUnderstandingLayer：读取外部已知语义类型；如果没有这行代码，旧 semantic_intent 无法兼容。
    task_kind = semantic_kind if semantic_kind in {"text_entry", "drawing", "navigation", "multi_app", "unknown_gui"} else _intent_task_kind(text)  # 新增代码+IntentUnderstandingLayer：优先复用可信类型再确定性分类；如果没有这行代码，外部语义结果会被忽略。
    target_hints = _intent_target_hints(text, task_kind)  # 新增代码+IntentUnderstandingLayer：提取目标软件提示；如果没有这行代码，启动层缺候选。
    payloads = _intent_content_payloads(text)  # 新增代码+IntentUnderstandingLayer：提取内容载荷；如果没有这行代码，文本阶段缺正文。
    artifacts = _intent_artifact_requests(text)  # 新增代码+IntentUnderstandingLayer：提取产物请求；如果没有这行代码，保存阶段缺资源。
    grants_existing = _intent_contains_any(text, EXISTING_GRANT_TERMS)  # 新增代码+IntentUnderstandingLayer：识别用户是否允许已有窗口；如果没有这行代码，单实例授权无法表达。
    single_instance_mentioned = _intent_contains_any(text, SINGLE_INSTANCE_TERMS)  # 新增代码+IntentUnderstandingLayer：识别单实例或旧窗口风险；如果没有这行代码，FreshTarget 策略缺信号。
    risk_level = "high" if _intent_contains_any(text, RISK_TERMS) else "medium" if single_instance_mentioned else "low"  # 新增代码+IntentUnderstandingLayer：生成风险级别；如果没有这行代码，高风险任务不能收紧策略。
    requires_fresh = bool(task_kind in {"text_entry", "drawing", "multi_app"} and not grants_existing)  # 新增代码+IntentUnderstandingLayer：写入类任务默认要求新资源；如果没有这行代码，旧文件或旧画布可能被接管。
    return IntentUnderstandingResult(objective=text[:180], task_kind=task_kind, target_app_hints=target_hints, required_targets=_intent_required_targets(task_kind, target_hints), content_payloads=payloads, artifact_requests=artifacts, success_criteria=_intent_success_criteria(task_kind, artifacts, payloads), requires_fresh_resource=requires_fresh, allows_existing_user_window=grants_existing, risk_level=risk_level, needs_clarification=bool(task_kind == "unknown_gui" and not target_hints), layer_skill_metadata=prompt_meta)  # 新增代码+IntentUnderstandingLayer：返回结构化意图；如果没有这行代码，后续层拿不到统一契约。
# 新增代码+IntentUnderstandingLayer：函数段结束，understand_desktop_intent 到此结束；如果没有这个边界说明，用户不容易看出意图层范围。


__all__ = ["understand_desktop_intent"]  # 新增代码+IntentUnderstandingLayer：声明公开接口；如果没有这行代码，通配导入会暴露内部 helper。
