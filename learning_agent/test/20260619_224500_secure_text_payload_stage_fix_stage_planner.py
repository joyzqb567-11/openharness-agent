"""Universal prompt-to-stage planner for Windows Computer Use tasks."""  # 新增代码+UniversalStagePlanner：说明本文件负责自然语言到通用阶段计划；如果没有这行代码，读者会误以为这里是某个应用控制器。
from __future__ import annotations  # 新增代码+UniversalStagePlanner：启用延迟类型解析；如果没有这行代码，模型类型互相引用时更容易导入失败。

import hashlib  # 新增代码+UniversalStagePlanner：导入哈希工具生成脱敏 prompt 签名；如果没有这行代码，运行证据无法区分任务且保护原文。
from typing import Any, Mapping  # 新增代码+UniversalStagePlanner：导入动态语义输入类型；如果没有这行代码，planner 接口边界不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import DesktopTaskPlan, StagePlan  # 新增代码+UniversalStagePlanner：导入通用阶段模型；如果没有这行代码，planner 会退回散乱 dict。


TEXT_TERMS = ("文本", "输入", "键入", "写入", "整理", "记录", "保存到桌面", "text", "type", "write", "enter")  # 新增代码+UniversalStagePlanner：定义文本类任务语义词；如果没有这行代码，文本任务无法泛化识别。
DRAWING_TERMS = ("绘图", "绘制", "画", "上色", "颜色", "图片", "图像", "draw", "drawing", "color", "image")  # 新增代码+UniversalStagePlanner：定义绘图类任务语义词；如果没有这行代码，绘图任务会回到具体软件判断。
NAVIGATION_TERMS = ("浏览", "搜索", "网页", "网址", "查看结果", "navigation", "search", "web", "url", "page")  # 新增代码+UniversalStagePlanner：定义导航类任务语义词；如果没有这行代码，浏览任务只能靠浏览器应用名。
MULTI_TARGET_TERMS = ("同时", "两个", "两个本机", "多个", "另一个", "整理到", "multi", "two", "multiple")  # 新增代码+UniversalStagePlanner：定义多目标任务语义词；如果没有这行代码，多窗口任务会被压成单窗口。
SAVE_TERMS = ("保存", "存到", "导出", "save", "export")  # 新增代码+UniversalStagePlanner：定义提交资源语义词；如果没有这行代码，保存阶段可能缺失。
UNKNOWN_TERMS = ("未知", "没说名字", "任意软件", "unknown", "unspecified")  # 新增代码+UniversalStagePlanner：定义未知目标语义词；如果没有这行代码，未知 GUI 可能被误判为可直接执行。
TEXT_PAYLOAD_PREFIXES = ("输入", "键入", "写入", "填写", "type", "write", "enter")  # 新增代码+UniversalStagePlanner：定义文本内容前缀；如果没有这行代码，planner 只能知道“要输入”，不知道要输入什么。
TEXT_PAYLOAD_STOPS = ("然后", "最后", "并", "且", "之后", "保存", "导出", "，", "。", ",", ";", "；", ".")  # 新增代码+UniversalStagePlanner：定义文本内容终止词；如果没有这行代码，planner 会把后续操作也误当成要输入的正文。
TEXT_PAYLOAD_STRIP_CHARS = " ：:，,。.;；\"'`“”()[]{}<>"  # 修改代码+TextPayloadExtraction：统一正文候选两端可剥离符号；如果没有这行代码，右括号这类尾部说明可能被误当正文。
TEXT_PAYLOAD_LEADING_NOISE = ("exactly", "内容", "正文")  # 修改代码+TextPayloadExtraction：定义输入动词后的说明性噪声词；如果没有这行代码，英文 prompt 的 exactly 会混进待输入正文。


def _stage_planner_text(value: Any) -> str:  # 新增代码+UniversalStagePlanner：函数段开始，清洗 prompt 文本；如果没有这段函数，None 和换行会污染目标摘要。
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())[:1000]  # 新增代码+UniversalStagePlanner：返回单行限长文本；如果没有这行代码，超长 prompt 会撑大计划证据。
# 新增代码+UniversalStagePlanner：函数段结束，_stage_planner_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清洗范围。


def _stage_planner_contains_any(text: str, terms: tuple[str, ...]) -> bool:  # 新增代码+UniversalStagePlanner：函数段开始，判断文本是否命中语义词；如果没有这段函数，多处分支会重复写包含逻辑。
    lowered = text.lower()  # 新增代码+UniversalStagePlanner：准备小写文本兼容英文；如果没有这行代码，英文大小写会影响识别。
    return any(term.lower() in lowered or term in text for term in terms)  # 新增代码+UniversalStagePlanner：任一语义词命中即返回真；如果没有这行代码，调用方拿不到统一布尔值。
# 新增代码+UniversalStagePlanner：函数段结束，_stage_planner_contains_any 到此结束；如果没有这个边界说明，初学者不容易看出语义匹配范围。


def _stage_planner_trim_payload_noise(candidate: str) -> str:  # 修改代码+TextPayloadExtraction：函数段开始，剥离正文候选前后的提示词和标点；如果没有这段函数，type exactly 会把 exactly 当成正文。
    cleaned = str(candidate or "").strip(TEXT_PAYLOAD_STRIP_CHARS)  # 修改代码+TextPayloadExtraction：先去掉候选两端的普通标点；如果没有这行代码，单独的右括号可能通过长度检查。
    lowered = cleaned.lower()  # 修改代码+TextPayloadExtraction：准备小写版本匹配英文噪声词；如果没有这行代码，Exactly 大小写会影响抽取。
    for noise in TEXT_PAYLOAD_LEADING_NOISE:  # 修改代码+TextPayloadExtraction：逐个处理允许剥离的说明词；如果没有这行代码，正文清洗规则无法扩展。
        noise_lower = noise.lower()  # 修改代码+TextPayloadExtraction：把噪声词转成小写；如果没有这行代码，英文大小写不一致会漏处理。
        if lowered.startswith(noise_lower):  # 修改代码+TextPayloadExtraction：只剥离出现在候选开头的说明词；如果没有这行代码，中间正文可能被误删。
            cleaned = cleaned[len(noise):].strip(TEXT_PAYLOAD_STRIP_CHARS)  # 修改代码+TextPayloadExtraction：删除说明词并再次剥标点；如果没有这行代码，exactly: 后面的冒号会残留。
            lowered = cleaned.lower()  # 修改代码+TextPayloadExtraction：更新小写缓存继续处理后续说明词；如果没有这行代码，多个噪声词连续时无法正确清洗。
    return cleaned  # 修改代码+TextPayloadExtraction：返回清洗后的正文候选；如果没有这行代码，调用方拿不到可执行文本。
# 修改代码+TextPayloadExtraction：函数段结束，_stage_planner_trim_payload_noise 到此结束；如果没有这个边界说明，初学者不容易看出清洗范围。


def _stage_planner_candidate_has_text(candidate: str) -> bool:  # 修改代码+TextPayloadExtraction：函数段开始，判断候选是否真含文字或数字；如果没有这段函数，单独符号会被误当正文。
    compact = str(candidate or "").strip(TEXT_PAYLOAD_STRIP_CHARS)  # 修改代码+TextPayloadExtraction：再次剥离候选外层标点；如果没有这行代码，")" 这类候选会误过非空判断。
    if not compact:  # 修改代码+TextPayloadExtraction：空候选直接拒绝；如果没有这行代码，空字符串可能进入 type_text。
        return False  # 修改代码+TextPayloadExtraction：返回无正文；如果没有这行代码，后续生成器会在空文本上空跑。
    return any(character.isalnum() or "\u4e00" <= character <= "\u9fff" for character in compact)  # 修改代码+TextPayloadExtraction：要求至少有字母数字或中文；如果没有这行代码，纯标点会污染执行层。
# 修改代码+TextPayloadExtraction：函数段结束，_stage_planner_candidate_has_text 到此结束；如果没有这个边界说明，初学者不容易看出正文有效性规则。


def _stage_planner_signature(text: str) -> str:  # 新增代码+UniversalStagePlanner：函数段开始，生成脱敏签名；如果没有这段函数，证据只能保存原始 prompt 或无法区分任务。
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]  # 新增代码+UniversalStagePlanner：返回短哈希签名；如果没有这行代码，日志关联键不稳定。
# 新增代码+UniversalStagePlanner：函数段结束，_stage_planner_signature 到此结束；如果没有这个边界说明，初学者不容易看出签名来源。


def _stage_planner_requested_text(text: str) -> str:  # 新增代码+UniversalStagePlanner：函数段开始，从通用文本任务里抽取要输入的正文；如果没有这段函数，批执行器会退回 sample text 或无法验收。
    lowered = text.lower()  # 新增代码+UniversalStagePlanner：准备小写文本用于英文前缀匹配；如果没有这行代码，Type/type 之类大小写会漏识别。
    best_candidate = ""  # 新增代码+UniversalStagePlanner：初始化候选正文；如果没有这行代码，未命中前缀时返回值不稳定。
    for prefix in TEXT_PAYLOAD_PREFIXES:  # 新增代码+UniversalStagePlanner：遍历通用输入前缀；如果没有这行代码，中英文输入动词不能统一处理。
        prefix_lower = prefix.lower()  # 修改代码+TextPayloadExtraction：缓存小写前缀；如果没有这行代码，循环里会重复转换且不易阅读。
        search_from = 0  # 修改代码+TextPayloadExtraction：从 prompt 开头开始扫描所有命中；如果没有这行代码，只看最后一次 write 会误抓 direct file write)。
        while True:  # 修改代码+TextPayloadExtraction：持续查找同一个前缀的所有出现位置；如果没有这行代码，早期有效正文可能被后续说明覆盖。
            index = lowered.find(prefix_lower, search_from)  # 修改代码+TextPayloadExtraction：查找当前前缀的下一个位置；如果没有这行代码，无法区分正文命中和后续说明命中。
            if index < 0:  # 修改代码+TextPayloadExtraction：没有更多命中时停止当前前缀；如果没有这行代码，扫描会无限循环。
                break  # 修改代码+TextPayloadExtraction：退出当前前缀扫描；如果没有这行代码，未命中分支无法收束。
            search_from = index + max(1, len(prefix))  # 修改代码+TextPayloadExtraction：推进搜索位置避免重复命中；如果没有这行代码，同一前缀会反复找到自己。
            candidate = text[index + len(prefix):].strip(TEXT_PAYLOAD_STRIP_CHARS)  # 修改代码+TextPayloadExtraction：截取前缀后的正文候选；如果没有这行代码，正文会带着动词和标点。
            for stop in TEXT_PAYLOAD_STOPS:  # 新增代码+UniversalStagePlanner：逐个检查后续动作边界；如果没有这行代码，保存、拖动等后续步骤会混进正文。
                stop_index = candidate.find(stop)  # 新增代码+UniversalStagePlanner：查找终止词位置；如果没有这行代码，无法知道正文在哪里结束。
                if stop_index > 0:  # 新增代码+UniversalStagePlanner：只在终止词出现在正文后方时切分；如果没有这行代码，开头标点可能误删全部内容。
                    candidate = candidate[:stop_index].strip(TEXT_PAYLOAD_STRIP_CHARS)  # 修改代码+TextPayloadExtraction：切掉后续动作说明并统一剥符号；如果没有这行代码，正文会包含任务控制语句。
            candidate = _stage_planner_trim_payload_noise(candidate)  # 修改代码+TextPayloadExtraction：去掉 exactly 等说明词；如果没有这行代码，真实英文验收 prompt 会输入多余词。
            if 0 < len(candidate) <= 160 and _stage_planner_candidate_has_text(candidate):  # 修改代码+TextPayloadExtraction：只接受短且确实含文字的候选；如果没有这行代码，")" 会覆盖 hello everyone。
                best_candidate = candidate  # 新增代码+UniversalStagePlanner：保存当前候选；如果没有这行代码，最后一个更精确的输入片段无法覆盖旧候选。
    return best_candidate  # 新增代码+UniversalStagePlanner：返回抽取到的正文；如果没有这行代码，文本阶段无法把用户意图传给执行层和验收层。
# 新增代码+UniversalStagePlanner：函数段结束，_stage_planner_requested_text 到此结束；如果没有这个边界说明，初学者不容易看出正文抽取范围。


def _stage_planner_task_kind(text: str, semantic_intent: Mapping[str, Any] | None = None) -> str:  # 新增代码+UniversalStagePlanner：函数段开始，提取通用任务类型；如果没有这段函数，planner 会按应用名分支。
    intent_kind = str((semantic_intent or {}).get("task_kind", "") or "").strip().lower()  # 新增代码+UniversalStagePlanner：读取外部语义类型；如果没有这行代码，已有 semantic planner 结果无法复用。
    if _stage_planner_contains_any(text, UNKNOWN_TERMS) and not _stage_planner_contains_any(text, TEXT_TERMS + DRAWING_TERMS + NAVIGATION_TERMS):  # 新增代码+UniversalStagePlanner：明确未知且无其它能力线索时保持未知；如果没有这行代码，未知 GUI 可能被误执行。
        return "unknown_gui"  # 新增代码+UniversalStagePlanner：返回未知 GUI 类型；如果没有这行代码，上层无法进入探测或问用户。
    if _stage_planner_contains_any(text, MULTI_TARGET_TERMS):  # 新增代码+UniversalStagePlanner：多目标语义优先；如果没有这行代码，同时使用两个窗口会被误压成单窗口。
        return "multi_app"  # 新增代码+UniversalStagePlanner：返回多应用通用类型；如果没有这行代码，多 target_ref 无法生成。
    if intent_kind in {"draw", "drawing"} or _stage_planner_contains_any(text, DRAWING_TERMS):  # 新增代码+UniversalStagePlanner：识别绘图任务；如果没有这行代码，绘图任务无法生成画布批阶段。
        return "drawing"  # 新增代码+UniversalStagePlanner：返回通用绘图类型；如果没有这行代码，绘图会走未知 GUI。
    if intent_kind in {"browser_task", "navigation"} or _stage_planner_contains_any(text, NAVIGATION_TERMS):  # 新增代码+UniversalStagePlanner：识别导航任务；如果没有这行代码，搜索查看任务无法泛化。
        return "navigation"  # 新增代码+UniversalStagePlanner：返回通用导航类型；如果没有这行代码，导航批无法生成。
    if intent_kind in {"type_text", "text_entry"} or _stage_planner_contains_any(text, TEXT_TERMS):  # 新增代码+UniversalStagePlanner：识别文本输入任务；如果没有这行代码，文本输入无法生成文本批。
        return "text_entry"  # 新增代码+UniversalStagePlanner：返回通用文本类型；如果没有这行代码，文本任务会被当成未知。
    return "unknown_gui"  # 新增代码+UniversalStagePlanner：缺少明确语义时返回未知；如果没有这行代码，planner 可能伪造可执行计划。
# 新增代码+UniversalStagePlanner：函数段结束，_stage_planner_task_kind 到此结束；如果没有这个边界说明，初学者不容易看出类型判断范围。


def _stage_planner_target(target_id: str, role: str, capability_hint: str) -> dict[str, Any]:  # 新增代码+UniversalStagePlanner：函数段开始，构造通用目标描述；如果没有这段函数，目标字段会在各分支漂移。
    return {"target_id": target_id, "target_role": role, "capability_hint": capability_hint, "resolved_target_ref": target_id, "app_specific_controller": False}  # 新增代码+UniversalStagePlanner：返回通用目标字段；如果没有这行代码，多目标绑定缺稳定键。
# 新增代码+UniversalStagePlanner：函数段结束，_stage_planner_target 到此结束；如果没有这个边界说明，初学者不容易看出目标构造范围。


def _stage_planner_stage(stage_id: str, stage_kind: str, target_ref: str, observation_policy: str, verifier_kind: str = "", verifier_extra: Mapping[str, Any] | None = None) -> StagePlan:  # 新增代码+UniversalStagePlanner：函数段开始，构造通用阶段；如果没有这段函数，阶段字段会重复且易错。
    verifier = {"verifier_kind": verifier_kind or stage_kind}  # 新增代码+UniversalStagePlanner：保存通用 verifier 类型；如果没有这行代码，阶段验收层缺规则提示。
    verifier.update(dict(verifier_extra or {}))  # 新增代码+UniversalStagePlanner：合并阶段专属验收字段；如果没有这行代码，文本正文、导航查询等细节无法传到执行和验证层。
    repair_policy = {"max_repairs": 1, "repair_scope": "stage"}  # 新增代码+UniversalStagePlanner：保存默认阶段级修复策略；如果没有这行代码，失败后可能无限重试。
    return StagePlan(stage_id=stage_id, stage_kind=stage_kind, target_ref=target_ref, observation_policy=observation_policy, verifier=verifier, repair_policy=repair_policy)  # 新增代码+UniversalStagePlanner：返回阶段计划；如果没有这行代码，planner 无法组装任务。
# 新增代码+UniversalStagePlanner：函数段结束，_stage_planner_stage 到此结束；如果没有这个边界说明，初学者不容易看出阶段构造范围。


class UniversalDesktopStagePlanner:  # 新增代码+UniversalStagePlanner：类段开始，定义通用桌面阶段规划器；如果没有这个类，full mode 无法拥有上层阶段计划。
    model = "universal_desktop_stage_planner"  # 新增代码+UniversalStagePlanner：暴露稳定模型名；如果没有这行代码，验收报告无法确认使用新规划器。

    def plan(self, prompt: str, semantic_intent: Mapping[str, Any] | None = None) -> DesktopTaskPlan:  # 新增代码+UniversalStagePlanner：函数段开始，把用户 prompt 转成通用阶段计划；如果没有这段函数，任务会继续由 primitive 循环驱动。
        text = _stage_planner_text(prompt)  # 新增代码+UniversalStagePlanner：清洗 prompt；如果没有这行代码，分类和签名会不稳定。
        task_kind = _stage_planner_task_kind(text, semantic_intent)  # 新增代码+UniversalStagePlanner：提取通用任务类型；如果没有这行代码，后续阶段无法选择模板。
        targets = self._targets_for_kind(task_kind)  # 新增代码+UniversalStagePlanner：生成目标描述；如果没有这行代码，多窗口和单窗口任务无法表达。
        stages = self._stages_for_kind(task_kind, text)  # 新增代码+UniversalStagePlanner：生成带任务上下文的通用阶段序列；如果没有这行代码，文本正文等阶段细节会丢失。
        criteria = self._success_criteria_for_kind(task_kind, text)  # 新增代码+UniversalStagePlanner：生成机器可读成功标准；如果没有这行代码，final gate 缺完成依据。
        resources = self._resources_for_prompt(text)  # 新增代码+UniversalStagePlanner：生成资源描述；如果没有这行代码，保存/导出阶段缺上下文。
        return DesktopTaskPlan(objective=text[:160], task_kind=task_kind, targets=tuple(targets), resources=tuple(resources), success_criteria=tuple(criteria), stages=tuple(stages), prompt_signature=_stage_planner_signature(text))  # 新增代码+UniversalStagePlanner：返回完整计划；如果没有这行代码，上层拿不到阶段模型。
    # 新增代码+UniversalStagePlanner：函数段结束，UniversalDesktopStagePlanner.plan 到此结束；如果没有这个边界说明，初学者不容易看出主规划范围。

    def _targets_for_kind(self, task_kind: str) -> list[dict[str, Any]]:  # 新增代码+UniversalStagePlanner：函数段开始，按通用任务类型生成目标描述；如果没有这段函数，目标数量逻辑会散落。
        if task_kind == "multi_app":  # 新增代码+UniversalStagePlanner：处理多窗口任务；如果没有这行代码，两个窗口无法分开绑定。
            return [_stage_planner_target("target_1", "source_or_navigation", "navigation_or_readable_surface"), _stage_planner_target("target_2", "destination_or_text", "text_input_surface")]  # 新增代码+UniversalStagePlanner：返回两个通用目标；如果没有这行代码，多窗口写入会共享目标。
        hint = "text_input_surface" if task_kind == "text_entry" else "canvas_like_surface" if task_kind == "drawing" else "navigation_surface" if task_kind == "navigation" else "unknown_gui_surface"  # 新增代码+UniversalStagePlanner：选择通用能力提示；如果没有这行代码，target 缺少能力期望。
        return [_stage_planner_target("target_1", "primary", hint)]  # 新增代码+UniversalStagePlanner：返回单目标描述；如果没有这行代码，单应用任务缺目标。
    # 新增代码+UniversalStagePlanner：函数段结束，UniversalDesktopStagePlanner._targets_for_kind 到此结束；如果没有这个边界说明，初学者不容易看出目标生成范围。

    def _stages_for_kind(self, task_kind: str, text: str = "") -> list[StagePlan]:  # 新增代码+UniversalStagePlanner：函数段开始，按通用任务类型生成阶段；如果没有这段函数，阶段序列无法复用。
        if task_kind == "unknown_gui":  # 新增代码+UniversalStagePlanner：未知任务只允许准备和探测；如果没有这行代码，未知软件可能被盲写。
            return [_stage_planner_stage("stage_001_prepare_target", "prepare_target", "target_1", "before_stage"), _stage_planner_stage("stage_002_probe_capabilities", "probe_capabilities", "target_1", "before_and_after_stage"), _stage_planner_stage("stage_003_needs_user", "needs_user", "target_1", "none")]  # 新增代码+UniversalStagePlanner：返回未知任务保守阶段；如果没有这行代码，未知任务没有停止点。
        if task_kind == "multi_app":  # 新增代码+UniversalStagePlanner：多窗口任务需要分别准备和写入；如果没有这行代码，多目标阶段无法生成。
            return [_stage_planner_stage("stage_001_prepare_source", "prepare_target", "target_1", "before_stage"), _stage_planner_stage("stage_002_probe_source", "probe_capabilities", "target_1", "before_stage"), _stage_planner_stage("stage_003_prepare_destination", "prepare_target", "target_2", "before_stage", verifier_extra={"fresh_resource_required": True}), _stage_planner_stage("stage_004_probe_destination", "probe_capabilities", "target_2", "before_stage"), _stage_planner_stage("stage_005_read_source", "perform_content_work", "target_1", "before_and_after_stage"), _stage_planner_stage("stage_006_write_destination", "perform_content_work", "target_2", "before_and_after_stage"), _stage_planner_stage("stage_007_commit_destination", "commit_resource", "target_2", "before_and_after_stage"), _stage_planner_stage("stage_008_verify_result", "verify_result", "target_2", "after_stage")]  # 新增代码+FreshResource：返回多目标阶段序列并要求写入目标是新资源；如果没有这行代码，跨窗口整理可能写进旧文件。
        commit_needed = task_kind in {"text_entry", "drawing"}  # 新增代码+UniversalStagePlanner：文本和绘图默认需要保存提交；如果没有这行代码，保存任务可能漏掉提交阶段。
        prepare_extra = {"fresh_resource_required": True} if task_kind in {"text_entry", "drawing"} else {}  # 新增代码+FreshResource：文本和绘图需要新资源承载输出；如果没有这行代码，新进程恢复旧文件时执行层不知道要先新建资源。
        perform_extra = {"requested_text": _stage_planner_requested_text(text)} if task_kind == "text_entry" else {}  # 新增代码+UniversalStagePlanner：为文本阶段附带要输入的正文；如果没有这行代码，批执行器不知道用户要输入 hello everyone 还是其它内容。
        stages = [_stage_planner_stage("stage_001_prepare_target", "prepare_target", "target_1", "before_stage", verifier_extra=prepare_extra), _stage_planner_stage("stage_002_probe_capabilities", "probe_capabilities", "target_1", "before_stage"), _stage_planner_stage("stage_003_perform_content_work", "perform_content_work", "target_1", "before_and_after_stage", verifier_extra=perform_extra)]  # 新增代码+FreshResource：构造基础三阶段并把新资源要求传给准备阶段；如果没有这行代码，执行层无法区分写入任务和只读任务。
        if commit_needed:  # 新增代码+UniversalStagePlanner：检查是否需要资源提交；如果没有这行代码，导航类任务会被强制保存。
            stages.append(_stage_planner_stage("stage_004_commit_resource", "commit_resource", "target_1", "before_and_after_stage"))  # 新增代码+UniversalStagePlanner：追加保存阶段；如果没有这行代码，文本/绘图任务会早停。
        stages.append(_stage_planner_stage("stage_005_verify_result" if commit_needed else "stage_004_verify_result", "verify_result", "target_1", "after_stage"))  # 新增代码+UniversalStagePlanner：追加验证阶段；如果没有这行代码，任务完成无法机器确认。
        return stages  # 新增代码+UniversalStagePlanner：返回阶段列表；如果没有这行代码，调用方拿不到阶段。
    # 新增代码+UniversalStagePlanner：函数段结束，UniversalDesktopStagePlanner._stages_for_kind 到此结束；如果没有这个边界说明，初学者不容易看出阶段模板范围。

    def _success_criteria_for_kind(self, task_kind: str, text: str) -> list[str]:  # 新增代码+UniversalStagePlanner：函数段开始，生成成功标准；如果没有这段函数，stage verifier 缺少验收目标。
        criteria = ["target_identity_verified", "stage_verifier_completed"]  # 新增代码+UniversalStagePlanner：添加所有任务通用标准；如果没有这行代码，窗口身份和阶段完成不会进入验收。
        if task_kind == "text_entry":  # 新增代码+UniversalStagePlanner：处理文本任务标准；如果没有这行代码，文本输入是否完成无法确认。
            criteria.append("requested_text_visible_or_saved")  # 新增代码+UniversalStagePlanner：添加文本可见或已保存标准；如果没有这行代码，文本任务可能只发送事件就成功。
        if task_kind == "drawing":  # 新增代码+UniversalStagePlanner：处理绘图任务标准；如果没有这行代码，画布变化无法成为验收条件。
            criteria.append("canvas_changed_with_visual_structure")  # 新增代码+UniversalStagePlanner：添加画布变化和结构标准；如果没有这行代码，单线条也可能误过。
        if task_kind == "navigation":  # 新增代码+UniversalStagePlanner：处理导航任务标准；如果没有这行代码，搜索/查看结果无法验收。
            criteria.append("navigation_result_visible")  # 新增代码+UniversalStagePlanner：添加导航结果可见标准；如果没有这行代码，导航任务可能只打开窗口就成功。
        if _stage_planner_contains_any(text, SAVE_TERMS):  # 新增代码+UniversalStagePlanner：检查用户是否要求保存；如果没有这行代码，资源提交标准无法按 prompt 增强。
            criteria.append("resource_commit_verified")  # 新增代码+UniversalStagePlanner：添加保存完成标准；如果没有这行代码，保存任务可能不验证文件或应用状态。
        return criteria  # 新增代码+UniversalStagePlanner：返回成功标准；如果没有这行代码，调用方拿不到列表。
    # 新增代码+UniversalStagePlanner：函数段结束，UniversalDesktopStagePlanner._success_criteria_for_kind 到此结束；如果没有这个边界说明，初学者不容易看出标准生成范围。

    def _resources_for_prompt(self, text: str) -> list[dict[str, Any]]:  # 新增代码+UniversalStagePlanner：函数段开始，从 prompt 生成通用资源提示；如果没有这段函数，保存阶段缺资源上下文。
        if not _stage_planner_contains_any(text, SAVE_TERMS):  # 新增代码+UniversalStagePlanner：检查是否没有保存语义；如果没有这行代码，所有任务都会生成资源。
            return []  # 新增代码+UniversalStagePlanner：无保存语义返回空资源；如果没有这行代码，导航任务会多出文件要求。
        location_hint = "desktop" if "桌面" in text.lower() or "desktop" in text.lower() else "user_requested_location"  # 新增代码+UniversalStagePlanner：提取通用保存位置提示；如果没有这行代码，保存阶段缺目标位置。
        return [{"resource_id": "resource_1", "resource_kind": "user_artifact", "location_hint": location_hint, "commit_required": True}]  # 新增代码+UniversalStagePlanner：返回通用资源描述；如果没有这行代码，commit_resource 阶段缺资源证据。
    # 新增代码+UniversalStagePlanner：函数段结束，UniversalDesktopStagePlanner._resources_for_prompt 到此结束；如果没有这个边界说明，初学者不容易看出资源生成范围。
# 新增代码+UniversalStagePlanner：类段结束，UniversalDesktopStagePlanner 到此结束；如果没有这个边界说明，初学者不容易看出 planner 范围。


__all__ = ["UniversalDesktopStagePlanner"]  # 新增代码+UniversalStagePlanner：声明公开接口；如果没有这行代码，通配导入会暴露内部 helper。
