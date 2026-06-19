"""JSON contracts for layered Computer Use runtime results."""  # 新增代码+LayerContracts：说明本文件只定义通用层结果契约；如果没有这行代码，维护者可能把应用自动化逻辑写进模型类。
from __future__ import annotations  # 新增代码+LayerContracts：启用延迟类型解析；如果没有这行代码，类型引用在导入阶段更容易失败。

from dataclasses import dataclass, field  # 新增代码+LayerContracts：导入数据类工具；如果没有这行代码，契约类会充满重复样板。
from typing import Any, Mapping  # 新增代码+LayerContracts：导入 JSON 风格动态类型；如果没有这行代码，契约边界不清楚。


GENERIC_TASK_KINDS = frozenset({"text_entry", "drawing", "navigation", "multi_app", "unknown_gui", "form_entry", "menu_operation", "file_management"})  # 新增代码+LayerContracts：定义通用任务类型，不包含具体软件；如果没有这行代码，planner 会继续按应用名分支。
GENERIC_STAGE_KINDS = frozenset({"prepare_target", "probe_capabilities", "prepare_resource", "perform_text_work", "perform_canvas_work", "perform_form_work", "perform_navigation_work", "perform_menu_work", "perform_content_work", "commit_resource", "verify_result", "cleanup_or_restore", "needs_user"})  # 新增代码+LayerContracts：定义通用阶段类型；如果没有这行代码，阶段计划缺少统一词表。
GENERIC_FAILURE_CLASSES = frozenset({"wrong_region", "target_drift", "batch_too_small", "save_dialog_unhandled", "missing_content", "capability_unknown", "permission_missing", "user_action_required"})  # 新增代码+LayerContracts：定义通用失败分类；如果没有这行代码，reflection 会写散乱自然语言。


def _contract_text(value: Any) -> str:  # 新增代码+LayerContracts：函数段开始，把动态文本清理成单行；如果没有这段函数，JSON 证据会被换行污染。
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())  # 新增代码+LayerContracts：返回单行文本；如果没有这行代码，契约字段可能带隐藏空白。
# 新增代码+LayerContracts：函数段结束，_contract_text 到此结束；如果没有这个边界说明，用户不容易看出清洗范围。


def _contract_tuple_text(value: Any) -> tuple[str, ...]:  # 新增代码+LayerContracts：函数段开始，把文本列表规范成元组；如果没有这段函数，外部可变列表会污染契约对象。
    return tuple(item for item in (_contract_text(part) for part in list(value or ())) if item)  # 新增代码+LayerContracts：过滤空文本并返回元组；如果没有这行代码，成功标准可能含空值。
# 新增代码+LayerContracts：函数段结束，_contract_tuple_text 到此结束；如果没有这个边界说明，用户不容易看出文本列表范围。


def _contract_tuple_dict(value: Any) -> tuple[dict[str, Any], ...]:  # 新增代码+LayerContracts：函数段开始，把字典列表规范成元组；如果没有这段函数，目标和区域列表可能被外部改写。
    return tuple(dict(item) for item in list(value or ()) if isinstance(item, Mapping))  # 新增代码+LayerContracts：复制每个字典项；如果没有这行代码，调用方传入的对象会被间接污染。
# 新增代码+LayerContracts：函数段结束，_contract_tuple_dict 到此结束；如果没有这个边界说明，用户不容易看出字典列表范围。


def _contract_dict(value: Any) -> dict[str, Any]:  # 新增代码+LayerContracts：函数段开始，把映射规范成普通 dict；如果没有这段函数，Mapping 子类可能在 JSON 化时出错。
    return dict(value or {}) if isinstance(value, Mapping) else {}  # 新增代码+LayerContracts：返回字典副本或空字典；如果没有这行代码，None 会导致调用方异常。
# 新增代码+LayerContracts：函数段结束，_contract_dict 到此结束；如果没有这个边界说明，用户不容易看出字典规范范围。


@dataclass(frozen=True)  # 新增代码+LayerContracts：声明 intent 结果不可变；如果没有这行代码，后续层可能改写用户意图。
class IntentUnderstandingResult:  # 新增代码+LayerContracts：类段开始，保存意图理解层结构化结果；如果没有这个类，planner 会继续重复解析 prompt。
    objective: str  # 新增代码+LayerContracts：保存脱敏目标；如果没有这行代码，计划没有用户目标锚点。
    task_kind: str  # 新增代码+LayerContracts：保存通用任务类型；如果没有这行代码，阶段规划无法选择策略。
    target_app_hints: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存用户提供的软件提示；如果没有这行代码，启动层缺候选线索。
    required_targets: tuple[dict[str, Any], ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存目标需求；如果没有这行代码，多窗口任务无法表达。
    content_payloads: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存要输入或使用的内容；如果没有这行代码，文本任务会丢失正文。
    artifact_requests: tuple[dict[str, Any], ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存输出文件或资源要求；如果没有这行代码，保存阶段缺上下文。
    success_criteria: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存机器可验证成功标准；如果没有这行代码，final gate 无法区分完成和未完成。
    requires_fresh_resource: bool = False  # 新增代码+LayerContracts：记录是否需要新资源；如果没有这行代码，旧窗口/旧文档可能被默认接管。
    allows_existing_user_window: bool = False  # 新增代码+LayerContracts：记录用户是否显式授权旧窗口；如果没有这行代码，单实例应用无法安全放行。
    risk_level: str = "low"  # 新增代码+LayerContracts：保存风险级别；如果没有这行代码，高风险任务不能触发更严观察。
    needs_clarification: bool = False  # 新增代码+LayerContracts：保存是否需要澄清；如果没有这行代码，未知任务可能被盲动。
    layer_skill_metadata: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayerContracts：保存 prompt 元数据不保存正文；如果没有这行代码，无法审计层版本。

    def __post_init__(self) -> None:  # 新增代码+LayerContracts：函数段开始，规范化 intent 字段；如果没有这段函数，动态输入会污染契约。
        object.__setattr__(self, "objective", _contract_text(self.objective))  # 新增代码+LayerContracts：清洗目标文本；如果没有这行代码，目标摘要可能带换行。
        object.__setattr__(self, "task_kind", _contract_text(self.task_kind))  # 新增代码+LayerContracts：清洗任务类型；如果没有这行代码，类型匹配会漂移。
        object.__setattr__(self, "target_app_hints", _contract_tuple_text(self.target_app_hints))  # 新增代码+LayerContracts：规范软件提示；如果没有这行代码，提示列表可被外部改写。
        object.__setattr__(self, "required_targets", _contract_tuple_dict(self.required_targets))  # 新增代码+LayerContracts：规范目标需求；如果没有这行代码，多目标结构可能不是 JSON 安全。
        object.__setattr__(self, "content_payloads", _contract_tuple_text(self.content_payloads))  # 新增代码+LayerContracts：规范内容载荷；如果没有这行代码，正文列表可能含空值。
        object.__setattr__(self, "artifact_requests", _contract_tuple_dict(self.artifact_requests))  # 新增代码+LayerContracts：规范产物请求；如果没有这行代码，保存信息可能变成可变对象。
        object.__setattr__(self, "success_criteria", _contract_tuple_text(self.success_criteria))  # 新增代码+LayerContracts：规范成功标准；如果没有这行代码，verifier 会收到脏输入。
        object.__setattr__(self, "risk_level", _contract_text(self.risk_level) or "low")  # 新增代码+LayerContracts：清洗风险级别并兜底；如果没有这行代码，空风险会影响策略。
        object.__setattr__(self, "layer_skill_metadata", _contract_dict(self.layer_skill_metadata))  # 新增代码+LayerContracts：复制 prompt 元数据；如果没有这行代码，外部修改会污染证据。
    # 新增代码+LayerContracts：函数段结束，IntentUnderstandingResult.__post_init__ 到此结束；如果没有这个边界说明，用户不容易看出 intent 规范范围。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LayerContracts：函数段开始，序列化 intent 结果；如果没有这段函数，测试和证据无法 round-trip。
        return {"objective": self.objective, "task_kind": self.task_kind, "target_app_hints": list(self.target_app_hints), "required_targets": [dict(item) for item in self.required_targets], "content_payloads": list(self.content_payloads), "artifact_requests": [dict(item) for item in self.artifact_requests], "success_criteria": list(self.success_criteria), "requires_fresh_resource": self.requires_fresh_resource, "allows_existing_user_window": self.allows_existing_user_window, "risk_level": self.risk_level, "needs_clarification": self.needs_clarification, "layer_skill_metadata": dict(self.layer_skill_metadata)}  # 新增代码+LayerContracts：返回 JSON 安全字典；如果没有这行代码，运行报告无法保存 intent。
    # 新增代码+LayerContracts：函数段结束，IntentUnderstandingResult.to_dict 到此结束；如果没有这个边界说明，用户不容易看出 intent 序列化范围。

    @classmethod  # 新增代码+LayerContracts：声明反序列化是类方法；如果没有这行代码，调用方要手工恢复字段。
    def from_dict(cls, payload: Mapping[str, Any]) -> "IntentUnderstandingResult":  # 新增代码+LayerContracts：函数段开始，从 JSON 字典恢复 intent；如果没有这段函数，落盘证据无法回放。
        return cls(**_contract_dict(payload))  # 新增代码+LayerContracts：用字典字段构造结果；如果没有这行代码，round-trip 测试无法通过。
    # 新增代码+LayerContracts：函数段结束，IntentUnderstandingResult.from_dict 到此结束；如果没有这个边界说明，用户不容易看出 intent 恢复范围。
# 新增代码+LayerContracts：类段结束，IntentUnderstandingResult 到此结束；如果没有这个边界说明，用户不容易看出 intent 契约范围。


@dataclass(frozen=True)  # 新增代码+LayerContracts：声明观察事实不可变；如果没有这行代码，观察事实可能被执行层改写。
class ObservationFacts:  # 新增代码+LayerContracts：类段开始，保存结构化观察事实；如果没有这个类，planner/verifier 会反复读取原始截图。
    active_target_ref: str = ""  # 新增代码+LayerContracts：保存当前目标引用；如果没有这行代码，观察事实不能绑定窗口。
    target_identity_verified: bool = False  # 新增代码+LayerContracts：保存目标身份是否确认；如果没有这行代码，批执行无法判断窗口是否安全。
    target_window_freshness: str = "unknown"  # 新增代码+LayerContracts：保存窗口新鲜度；如果没有这行代码，旧窗口和新窗口无法区分。
    editable_regions: tuple[dict[str, Any], ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存可编辑区域；如果没有这行代码，文本批缺定位依据。
    canvas_regions: tuple[dict[str, Any], ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存画布区域；如果没有这行代码，绘图批缺定位依据。
    menu_regions: tuple[dict[str, Any], ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存菜单区域；如果没有这行代码，菜单任务缺能力事实。
    toolbar_regions: tuple[dict[str, Any], ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存工具栏区域；如果没有这行代码，绘图和编辑工具无法避让或选择。
    modal_dialogs: tuple[dict[str, Any], ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存模态对话框；如果没有这行代码，保存/权限弹窗会被忽略。
    save_dialog_state: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayerContracts：保存保存对话框状态；如果没有这行代码，提交资源阶段无法验证。
    document_dirty_state: str = "unknown"  # 新增代码+LayerContracts：保存文档脏状态；如果没有这行代码，保存前后变化难以判断。
    visible_text_summary: str = ""  # 新增代码+LayerContracts：保存低敏可见文本摘要；如果没有这行代码，文本验证只能靠原始 OCR。
    visual_change_summary: str = ""  # 新增代码+LayerContracts：保存视觉变化摘要；如果没有这行代码，绘图验证缺事实。
    capability_profile: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayerContracts：保存能力画像；如果没有这行代码，batch compiler 会退回应用名判断。

    def __post_init__(self) -> None:  # 新增代码+LayerContracts：函数段开始，规范化观察事实；如果没有这段函数，观察层输出会保持可变结构。
        object.__setattr__(self, "active_target_ref", _contract_text(self.active_target_ref))  # 新增代码+LayerContracts：清洗 target_ref；如果没有这行代码，目标比较不稳定。
        object.__setattr__(self, "target_window_freshness", _contract_text(self.target_window_freshness) or "unknown")  # 新增代码+LayerContracts：清洗窗口新鲜度；如果没有这行代码，空值会传播。
        object.__setattr__(self, "editable_regions", _contract_tuple_dict(self.editable_regions))  # 新增代码+LayerContracts：规范可编辑区域；如果没有这行代码，区域列表可能被外部改。
        object.__setattr__(self, "canvas_regions", _contract_tuple_dict(self.canvas_regions))  # 新增代码+LayerContracts：规范画布区域；如果没有这行代码，区域列表可能不安全。
        object.__setattr__(self, "menu_regions", _contract_tuple_dict(self.menu_regions))  # 新增代码+LayerContracts：规范菜单区域；如果没有这行代码，菜单事实可能不是 JSON 安全。
        object.__setattr__(self, "toolbar_regions", _contract_tuple_dict(self.toolbar_regions))  # 新增代码+LayerContracts：规范工具栏区域；如果没有这行代码，工具栏事实可能被外部改。
        object.__setattr__(self, "modal_dialogs", _contract_tuple_dict(self.modal_dialogs))  # 新增代码+LayerContracts：规范对话框事实；如果没有这行代码，弹窗列表可能不安全。
        object.__setattr__(self, "save_dialog_state", _contract_dict(self.save_dialog_state))  # 新增代码+LayerContracts：规范保存对话框状态；如果没有这行代码，保存验证字段会漂移。
        object.__setattr__(self, "document_dirty_state", _contract_text(self.document_dirty_state) or "unknown")  # 新增代码+LayerContracts：规范文档脏状态；如果没有这行代码，空值会影响 verifier。
        object.__setattr__(self, "visible_text_summary", _contract_text(self.visible_text_summary))  # 新增代码+LayerContracts：清洗可见文本摘要；如果没有这行代码，摘要可能带私密多行内容。
        object.__setattr__(self, "visual_change_summary", _contract_text(self.visual_change_summary))  # 新增代码+LayerContracts：清洗视觉摘要；如果没有这行代码，报告可能难读。
        object.__setattr__(self, "capability_profile", _contract_dict(self.capability_profile))  # 新增代码+LayerContracts：复制能力画像；如果没有这行代码，外部修改会污染事实。
    # 新增代码+LayerContracts：函数段结束，ObservationFacts.__post_init__ 到此结束；如果没有这个边界说明，用户不容易看出观察事实规范范围。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LayerContracts：函数段开始，序列化观察事实；如果没有这段函数，stage loop 无法把 facts 放入报告。
        return {"active_target_ref": self.active_target_ref, "target_identity_verified": self.target_identity_verified, "target_window_freshness": self.target_window_freshness, "editable_regions": [dict(item) for item in self.editable_regions], "canvas_regions": [dict(item) for item in self.canvas_regions], "menu_regions": [dict(item) for item in self.menu_regions], "toolbar_regions": [dict(item) for item in self.toolbar_regions], "modal_dialogs": [dict(item) for item in self.modal_dialogs], "save_dialog_state": dict(self.save_dialog_state), "document_dirty_state": self.document_dirty_state, "visible_text_summary": self.visible_text_summary, "visual_change_summary": self.visual_change_summary, "capability_profile": dict(self.capability_profile)}  # 新增代码+LayerContracts：返回 JSON 安全事实；如果没有这行代码，观察层结果无法 round-trip。
    # 新增代码+LayerContracts：函数段结束，ObservationFacts.to_dict 到此结束；如果没有这个边界说明，用户不容易看出观察序列化范围。

    @classmethod  # 新增代码+LayerContracts：声明反序列化是类方法；如果没有这行代码，调用方需要知道所有字段。
    def from_dict(cls, payload: Mapping[str, Any]) -> "ObservationFacts":  # 新增代码+LayerContracts：函数段开始，从 JSON 字典恢复观察事实；如果没有这段函数，测试无法 round-trip。
        return cls(**_contract_dict(payload))  # 新增代码+LayerContracts：用字典字段构造结果；如果没有这行代码，落盘事实无法恢复。
    # 新增代码+LayerContracts：函数段结束，ObservationFacts.from_dict 到此结束；如果没有这个边界说明，用户不容易看出观察恢复范围。
# 新增代码+LayerContracts：类段结束，ObservationFacts 到此结束；如果没有这个边界说明，用户不容易看出观察契约范围。


@dataclass(frozen=True)  # 新增代码+LayerContracts：声明阶段规划结果不可变；如果没有这行代码，执行层可能改写计划。
class StagePlanningResult:  # 新增代码+LayerContracts：类段开始，保存阶段规划层结果；如果没有这个类，planner 输出会继续是散乱 dict。
    objective: str  # 新增代码+LayerContracts：保存目标摘要；如果没有这行代码，计划没有用户意图锚点。
    task_kind: str  # 新增代码+LayerContracts：保存通用任务类型；如果没有这行代码，阶段质量无法检查。
    stages: tuple[dict[str, Any], ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存阶段字典列表；如果没有这行代码，多阶段计划无法表达。
    success_criteria: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存成功标准；如果没有这行代码，verifier 缺目标。
    layer_skill_metadata: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayerContracts：保存层 prompt 元数据；如果没有这行代码，报告无法说明版本。

    def __post_init__(self) -> None:  # 新增代码+LayerContracts：函数段开始，规范化规划结果；如果没有这段函数，阶段列表会保持可变。
        object.__setattr__(self, "objective", _contract_text(self.objective))  # 新增代码+LayerContracts：清洗目标；如果没有这行代码，报告会带多余空白。
        object.__setattr__(self, "task_kind", _contract_text(self.task_kind))  # 新增代码+LayerContracts：清洗任务类型；如果没有这行代码，类型比较不稳定。
        object.__setattr__(self, "stages", _contract_tuple_dict(self.stages))  # 新增代码+LayerContracts：规范阶段列表；如果没有这行代码，外部可变列表会污染计划。
        object.__setattr__(self, "success_criteria", _contract_tuple_text(self.success_criteria))  # 新增代码+LayerContracts：规范成功标准；如果没有这行代码，空标准会进入 verifier。
        object.__setattr__(self, "layer_skill_metadata", _contract_dict(self.layer_skill_metadata))  # 新增代码+LayerContracts：复制元数据；如果没有这行代码，外部修改会污染证据。
    # 新增代码+LayerContracts：函数段结束，StagePlanningResult.__post_init__ 到此结束；如果没有这个边界说明，用户不容易看出规划规范范围。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LayerContracts：函数段开始，序列化规划结果；如果没有这段函数，计划无法写入证据。
        return {"objective": self.objective, "task_kind": self.task_kind, "stages": [dict(item) for item in self.stages], "success_criteria": list(self.success_criteria), "layer_skill_metadata": dict(self.layer_skill_metadata)}  # 新增代码+LayerContracts：返回 JSON 安全字典；如果没有这行代码，round-trip 不能验证。
    # 新增代码+LayerContracts：函数段结束，StagePlanningResult.to_dict 到此结束；如果没有这个边界说明，用户不容易看出规划序列化范围。

    @classmethod  # 新增代码+LayerContracts：声明反序列化是类方法；如果没有这行代码，调用方恢复时会写重复逻辑。
    def from_dict(cls, payload: Mapping[str, Any]) -> "StagePlanningResult":  # 新增代码+LayerContracts：函数段开始，从 JSON 恢复规划结果；如果没有这段函数，落盘计划无法回放。
        return cls(**_contract_dict(payload))  # 新增代码+LayerContracts：用字典字段构造结果；如果没有这行代码，测试无法 round-trip。
    # 新增代码+LayerContracts：函数段结束，StagePlanningResult.from_dict 到此结束；如果没有这个边界说明，用户不容易看出规划恢复范围。
# 新增代码+LayerContracts：类段结束，StagePlanningResult 到此结束；如果没有这个边界说明，用户不容易看出规划契约范围。


@dataclass(frozen=True)  # 新增代码+LayerContracts：声明阶段验证结果不可变；如果没有这行代码，完成状态可能被后续层改写。
class StageVerificationResult:  # 新增代码+LayerContracts：类段开始，保存 verifier 层结果；如果没有这个类，final gate 难以读取缺口。
    verified: bool  # 新增代码+LayerContracts：保存阶段是否验证通过；如果没有这行代码，完成判断没有主字段。
    missing_requirements: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+LayerContracts：保存缺失要求；如果没有这行代码，未完成原因无法反馈。
    next_required_stage: str = ""  # 新增代码+LayerContracts：保存下一阶段建议；如果没有这行代码，失败后无法收敛到正确阶段。
    needs_reflection: bool = False  # 新增代码+LayerContracts：保存是否需要反思；如果没有这行代码，失败会直接无脑重试。
    needs_user: bool = False  # 新增代码+LayerContracts：保存是否需要用户；如果没有这行代码，旧窗口或权限问题可能被自动重试。
    evidence_summary: str = ""  # 新增代码+LayerContracts：保存低敏证据摘要；如果没有这行代码，用户看不懂为什么失败。
    layer_skill_metadata: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayerContracts：保存层 prompt 元数据；如果没有这行代码，验证版本无法审计。

    def __post_init__(self) -> None:  # 新增代码+LayerContracts：函数段开始，规范化验证字段；如果没有这段函数，缺口列表可能含空值。
        object.__setattr__(self, "missing_requirements", _contract_tuple_text(self.missing_requirements))  # 新增代码+LayerContracts：规范缺失要求；如果没有这行代码，final gate 会收到脏字段。
        object.__setattr__(self, "next_required_stage", _contract_text(self.next_required_stage))  # 新增代码+LayerContracts：清洗下一阶段；如果没有这行代码，阶段 id 比较不稳定。
        object.__setattr__(self, "evidence_summary", _contract_text(self.evidence_summary))  # 新增代码+LayerContracts：清洗证据摘要；如果没有这行代码，报告可能多行泄露。
        object.__setattr__(self, "layer_skill_metadata", _contract_dict(self.layer_skill_metadata))  # 新增代码+LayerContracts：复制元数据；如果没有这行代码，外部修改会污染报告。
    # 新增代码+LayerContracts：函数段结束，StageVerificationResult.__post_init__ 到此结束；如果没有这个边界说明，用户不容易看出验证规范范围。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LayerContracts：函数段开始，序列化验证结果；如果没有这段函数，final gate 无法读 JSON。
        return {"verified": self.verified, "missing_requirements": list(self.missing_requirements), "next_required_stage": self.next_required_stage, "needs_reflection": self.needs_reflection, "needs_user": self.needs_user, "evidence_summary": self.evidence_summary, "layer_skill_metadata": dict(self.layer_skill_metadata)}  # 新增代码+LayerContracts：返回 JSON 安全字典；如果没有这行代码，验证结果无法 round-trip。
    # 新增代码+LayerContracts：函数段结束，StageVerificationResult.to_dict 到此结束；如果没有这个边界说明，用户不容易看出验证序列化范围。

    @classmethod  # 新增代码+LayerContracts：声明反序列化是类方法；如果没有这行代码，调用方会重复写恢复逻辑。
    def from_dict(cls, payload: Mapping[str, Any]) -> "StageVerificationResult":  # 新增代码+LayerContracts：函数段开始，从 JSON 恢复验证结果；如果没有这段函数，测试无法 round-trip。
        return cls(**_contract_dict(payload))  # 新增代码+LayerContracts：用字段构造结果；如果没有这行代码，落盘验证无法恢复。
    # 新增代码+LayerContracts：函数段结束，StageVerificationResult.from_dict 到此结束；如果没有这个边界说明，用户不容易看出验证恢复范围。
# 新增代码+LayerContracts：类段结束，StageVerificationResult 到此结束；如果没有这个边界说明，用户不容易看出验证契约范围。


@dataclass(frozen=True)  # 新增代码+LayerContracts：声明 reflection 结果不可变；如果没有这行代码，学习候选可能被后续层改写。
class ReflectionLearningResult:  # 新增代码+LayerContracts：类段开始，保存失败反思和学习候选；如果没有这个类，失败后只会重复同样动作。
    failure_class: str  # 新增代码+LayerContracts：保存失败分类；如果没有这行代码，经验无法聚合。
    evidence_summary: str = ""  # 新增代码+LayerContracts：保存低敏证据摘要；如果没有这行代码，修复策略缺上下文。
    repair_strategy: str = ""  # 新增代码+LayerContracts：保存修复策略；如果没有这行代码，下一轮规划不知道该改变什么。
    replan_required: bool = False  # 新增代码+LayerContracts：保存是否需要重规划；如果没有这行代码，局部失败和全局失败无法区分。
    user_input_required: bool = False  # 新增代码+LayerContracts：保存是否需要用户输入；如果没有这行代码，外部阻断可能被自动重试。
    learning_candidate: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayerContracts：保存脱敏学习候选；如果没有这行代码，重复失败不能固化经验。
    layer_skill_metadata: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayerContracts：保存层 prompt 元数据；如果没有这行代码，反思版本无法审计。

    def __post_init__(self) -> None:  # 新增代码+LayerContracts：函数段开始，规范化 reflection 字段；如果没有这段函数，失败分类和策略会不稳定。
        object.__setattr__(self, "failure_class", _contract_text(self.failure_class))  # 新增代码+LayerContracts：清洗失败分类；如果没有这行代码，统计会受空白影响。
        object.__setattr__(self, "evidence_summary", _contract_text(self.evidence_summary))  # 新增代码+LayerContracts：清洗证据摘要；如果没有这行代码，摘要可能泄露多行原文。
        object.__setattr__(self, "repair_strategy", _contract_text(self.repair_strategy))  # 新增代码+LayerContracts：清洗修复策略；如果没有这行代码，策略字段可能带无关空白。
        object.__setattr__(self, "learning_candidate", _contract_dict(self.learning_candidate))  # 新增代码+LayerContracts：复制学习候选；如果没有这行代码，外部修改会污染学习结果。
        object.__setattr__(self, "layer_skill_metadata", _contract_dict(self.layer_skill_metadata))  # 新增代码+LayerContracts：复制元数据；如果没有这行代码，外部修改会污染证据。
    # 新增代码+LayerContracts：函数段结束，ReflectionLearningResult.__post_init__ 到此结束；如果没有这个边界说明，用户不容易看出反思规范范围。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LayerContracts：函数段开始，序列化 reflection 结果；如果没有这段函数，学习层无法落盘。
        return {"failure_class": self.failure_class, "evidence_summary": self.evidence_summary, "repair_strategy": self.repair_strategy, "replan_required": self.replan_required, "user_input_required": self.user_input_required, "learning_candidate": dict(self.learning_candidate), "layer_skill_metadata": dict(self.layer_skill_metadata)}  # 新增代码+LayerContracts：返回 JSON 安全字典；如果没有这行代码，reflection 无法 round-trip。
    # 新增代码+LayerContracts：函数段结束，ReflectionLearningResult.to_dict 到此结束；如果没有这个边界说明，用户不容易看出反思序列化范围。

    @classmethod  # 新增代码+LayerContracts：声明反序列化是类方法；如果没有这行代码，调用方恢复学习结果会重复代码。
    def from_dict(cls, payload: Mapping[str, Any]) -> "ReflectionLearningResult":  # 新增代码+LayerContracts：函数段开始，从 JSON 恢复 reflection 结果；如果没有这段函数，学习候选无法回放。
        return cls(**_contract_dict(payload))  # 新增代码+LayerContracts：用字段构造结果；如果没有这行代码，round-trip 测试无法通过。
    # 新增代码+LayerContracts：函数段结束，ReflectionLearningResult.from_dict 到此结束；如果没有这个边界说明，用户不容易看出反思恢复范围。
# 新增代码+LayerContracts：类段结束，ReflectionLearningResult 到此结束；如果没有这个边界说明，用户不容易看出反思契约范围。


__all__ = ["GENERIC_FAILURE_CLASSES", "GENERIC_STAGE_KINDS", "GENERIC_TASK_KINDS", "IntentUnderstandingResult", "ObservationFacts", "ReflectionLearningResult", "StagePlanningResult", "StageVerificationResult"]  # 新增代码+LayerContracts：声明公开接口；如果没有这行代码，通配导入会暴露内部 helper。
