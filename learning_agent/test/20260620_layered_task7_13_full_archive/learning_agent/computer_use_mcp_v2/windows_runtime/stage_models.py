"""Universal Computer Use stage planning data models."""  # 新增代码+UniversalStageModels：说明本文件只定义通用阶段模型；如果没有这行代码，读者会误以为这里包含具体软件控制逻辑。
from __future__ import annotations  # 新增代码+UniversalStageModels：启用延迟类型解析；如果没有这行代码，类之间互相引用时更容易出现导入顺序问题。

from dataclasses import dataclass, field  # 新增代码+UniversalStageModels：导入数据类工具减少样板代码；如果没有这行代码，模型字段校验会分散。
from typing import Any, Mapping  # 新增代码+UniversalStageModels：导入 JSON 风格类型；如果没有这行代码，公开接口边界不清楚。


STAGE_RESULT_STATUSES = frozenset({"completed", "needs_repair", "needs_user", "blocked", "failed"})  # 新增代码+UniversalStageModels：定义阶段结果允许状态；如果没有这行代码，最终门禁会收到随意字符串。
WRITE_BATCH_SUFFIXES = ("_batch",)  # 新增代码+UniversalStageModels：定义可执行批命名约定；如果没有这行代码，target_ref 门禁无法统一判断。
NON_TARGET_BATCH_KINDS = {"probe_batch", "planning_batch"}  # 新增代码+UniversalStageModels：定义无需目标窗口的安全批类型；如果没有这行代码，探测阶段会被误判为写动作。


def _stage_models_clean_text(value: Any) -> str:  # 新增代码+UniversalStageModels：函数段开始，清洗动态文本；如果没有这段函数，None 和换行会污染证据字段。
    return str(value if value is not None else "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+UniversalStageModels：返回单行文本；如果没有这行代码，stage_id 和 target_ref 可能带入不可见字符。
# 新增代码+UniversalStageModels：函数段结束，_stage_models_clean_text 到此结束；如果没有这个边界说明，初学者不容易看出清洗范围。


def _stage_models_tuple_of_dicts(value: Any) -> tuple[dict[str, Any], ...]:  # 新增代码+UniversalStageModels：函数段开始，把动态列表转为字典元组；如果没有这段函数，可变输入会污染模型内部。
    return tuple(dict(item) for item in list(value or []) if isinstance(item, Mapping))  # 新增代码+UniversalStageModels：只保留映射项并复制；如果没有这行代码，坏列表元素会导致运行时异常。
# 新增代码+UniversalStageModels：函数段结束，_stage_models_tuple_of_dicts 到此结束；如果没有这个边界说明，初学者不容易看出列表规范化范围。


def _stage_models_tuple_of_text(value: Any) -> tuple[str, ...]:  # 新增代码+UniversalStageModels：函数段开始，把动态列表转为文本元组；如果没有这段函数，成功标准会保持可变状态。
    return tuple(_stage_models_clean_text(item) for item in list(value or []) if _stage_models_clean_text(item))  # 新增代码+UniversalStageModels：过滤空文本并返回元组；如果没有这行代码，空成功标准会干扰 verifier。
# 新增代码+UniversalStageModels：函数段结束，_stage_models_tuple_of_text 到此结束；如果没有这个边界说明，初学者不容易看出文本列表范围。


@dataclass(frozen=True)  # 新增代码+UniversalStageModels：声明动作批是不可变数据类；如果没有这行代码，执行中可能被其它层偷偷改掉。
class ActionBatch:  # 新增代码+UniversalStageModels：类段开始，表示一个阶段内可批量执行的通用动作；如果没有这个类，primitive 会继续散落在模型循环里。
    batch_id: str  # 新增代码+UniversalStageModels：保存批 id；如果没有这行代码，失败批次无法定位。
    batch_kind: str  # 新增代码+UniversalStageModels：保存批类型；如果没有这行代码，执行器不知道按文本、指针还是保存策略处理。
    target_ref: str  # 新增代码+UniversalStageModels：保存一对一目标窗口引用；如果没有这行代码，批动作可能写到错误窗口。
    actions: tuple[dict[str, Any], ...]  # 新增代码+UniversalStageModels：保存 primitive 动作列表；如果没有这行代码，执行器没有要执行的动作。
    guardrails: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+UniversalStageModels：保存批级安全约束；如果没有这行代码，关键动作缺少身份和事件上限证据。

    def __post_init__(self) -> None:  # 新增代码+UniversalStageModels：函数段开始，校验动作批字段；如果没有这段函数，非法批会进入真实执行层。
        cleaned_batch_id = _stage_models_clean_text(self.batch_id)  # 新增代码+UniversalStageModels：清洗批 id；如果没有这行代码，空白 id 可能伪装成有效值。
        cleaned_batch_kind = _stage_models_clean_text(self.batch_kind)  # 新增代码+UniversalStageModels：清洗批类型；如果没有这行代码，批类型匹配会受空白影响。
        cleaned_target_ref = _stage_models_clean_text(self.target_ref)  # 新增代码+UniversalStageModels：清洗目标引用；如果没有这行代码，一对一窗口绑定判断不稳定。
        if not cleaned_batch_id:  # 新增代码+UniversalStageModels：检查批 id 是否为空；如果没有这行代码，日志无法定位失败批。
            raise ValueError("batch_id is required")  # 新增代码+UniversalStageModels：空批 id 直接失败；如果没有这行代码，非法模型会继续运行。
        if not cleaned_batch_kind:  # 新增代码+UniversalStageModels：检查批类型是否为空；如果没有这行代码，执行器无法选择策略。
            raise ValueError("batch_kind is required")  # 新增代码+UniversalStageModels：空批类型直接失败；如果没有这行代码，后续会出现更难懂的错误。
        if cleaned_batch_kind.endswith(WRITE_BATCH_SUFFIXES) and cleaned_batch_kind not in NON_TARGET_BATCH_KINDS and not cleaned_target_ref:  # 新增代码+UniversalStageModels：写批必须绑定目标窗口；如果没有这行代码，Computer Use 可能默认接管当前焦点。
            raise ValueError("target_ref is required for executable batches")  # 新增代码+UniversalStageModels：缺目标引用直接失败；如果没有这行代码，安全门禁会后移到更危险的位置。
        object.__setattr__(self, "batch_id", cleaned_batch_id)  # 新增代码+UniversalStageModels：写回清洗后的批 id；如果没有这行代码，模型内部仍保留脏文本。
        object.__setattr__(self, "batch_kind", cleaned_batch_kind)  # 新增代码+UniversalStageModels：写回清洗后的批类型；如果没有这行代码，序列化输出不稳定。
        object.__setattr__(self, "target_ref", cleaned_target_ref)  # 新增代码+UniversalStageModels：写回清洗后的目标引用；如果没有这行代码，target_ref 比较可能失败。
        object.__setattr__(self, "actions", _stage_models_tuple_of_dicts(self.actions))  # 新增代码+UniversalStageModels：复制动作列表为元组；如果没有这行代码，外部可变列表会污染批。
        object.__setattr__(self, "guardrails", dict(self.guardrails or {}))  # 新增代码+UniversalStageModels：复制安全约束；如果没有这行代码，外部字典修改会改变运行中批。
    # 新增代码+UniversalStageModels：函数段结束，ActionBatch.__post_init__ 到此结束；如果没有这个边界说明，初学者不容易看出批校验范围。
# 新增代码+UniversalStageModels：类段结束，ActionBatch 到此结束；如果没有这个边界说明，初学者不容易看出动作批范围。


@dataclass(frozen=True)  # 新增代码+UniversalStageModels：声明阶段计划不可变；如果没有这行代码，执行过程中计划可能被意外改写。
class StagePlan:  # 新增代码+UniversalStageModels：类段开始，表示通用桌面任务中的一个阶段；如果没有这个类，无法按阶段观察和批执行。
    stage_id: str  # 新增代码+UniversalStageModels：保存阶段 id；如果没有这行代码，失败修复无法指向具体阶段。
    stage_kind: str  # 新增代码+UniversalStageModels：保存阶段类型；如果没有这行代码，编译器不知道准备、执行、保存或验证。
    target_ref: str = ""  # 新增代码+UniversalStageModels：保存阶段绑定目标；如果没有这行代码，多窗口任务无法约束写入对象。
    observation_policy: str = "before_and_after_stage"  # 新增代码+UniversalStageModels：保存阶段观察策略；如果没有这行代码，系统会退回每步观察或盲执行。
    batch: ActionBatch | None = None  # 新增代码+UniversalStageModels：保存阶段批动作；如果没有这行代码，阶段无法交给批执行器。
    input_contract: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayeredStagePlanner：保存阶段输入契约；如果没有这行代码，批编译器不知道本阶段依赖哪些观察事实。
    output_contract: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayeredStagePlanner：保存阶段输出契约；如果没有这行代码，verifier 难以知道阶段应产生什么结果。
    batch_intent: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayeredStagePlanner：保存阶段批执行意图；如果没有这行代码，批编译器只能从 stage_kind 粗糙猜动作。
    verification_contract: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayeredStagePlanner：保存阶段验证契约；如果没有这行代码，验证层只能读旧 verifier 字段。
    verifier: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+UniversalStageModels：保存阶段验收规则；如果没有这行代码，完成判断会靠最终口头描述。
    repair_policy: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+UniversalStageModels：保存阶段修复策略；如果没有这行代码，失败后容易无限重试。

    def __post_init__(self) -> None:  # 新增代码+UniversalStageModels：函数段开始，校验阶段字段；如果没有这段函数，空阶段会进入运行时。
        cleaned_stage_id = _stage_models_clean_text(self.stage_id)  # 新增代码+UniversalStageModels：清洗阶段 id；如果没有这行代码，空白 id 会绕过校验。
        cleaned_stage_kind = _stage_models_clean_text(self.stage_kind)  # 新增代码+UniversalStageModels：清洗阶段类型；如果没有这行代码，阶段匹配不稳定。
        if not cleaned_stage_id:  # 新增代码+UniversalStageModels：检查阶段 id 是否为空；如果没有这行代码，阶段证据无法定位。
            raise ValueError("stage_id is required")  # 新增代码+UniversalStageModels：空阶段 id 直接失败；如果没有这行代码，最终报告会出现无名阶段。
        if not cleaned_stage_kind:  # 新增代码+UniversalStageModels：检查阶段类型是否为空；如果没有这行代码，编译器无法选择策略。
            raise ValueError("stage_kind is required")  # 新增代码+UniversalStageModels：空阶段类型直接失败；如果没有这行代码，后续错误会更隐蔽。
        object.__setattr__(self, "stage_id", cleaned_stage_id)  # 新增代码+UniversalStageModels：写回清洗后的阶段 id；如果没有这行代码，序列化会保留脏值。
        object.__setattr__(self, "stage_kind", cleaned_stage_kind)  # 新增代码+UniversalStageModels：写回清洗后的阶段类型；如果没有这行代码，运行时比较可能失败。
        object.__setattr__(self, "target_ref", _stage_models_clean_text(self.target_ref))  # 新增代码+UniversalStageModels：写回清洗后的目标引用；如果没有这行代码，多目标映射不稳定。
        object.__setattr__(self, "observation_policy", _stage_models_clean_text(self.observation_policy) or "before_and_after_stage")  # 新增代码+UniversalStageModels：写回观察策略并兜底；如果没有这行代码，空策略会导致盲执行。
        object.__setattr__(self, "input_contract", dict(self.input_contract or {}))  # 新增代码+LayeredStagePlanner：复制输入契约；如果没有这行代码，外部字典会污染阶段计划。
        object.__setattr__(self, "output_contract", dict(self.output_contract or {}))  # 新增代码+LayeredStagePlanner：复制输出契约；如果没有这行代码，阶段完成要求可能被外部改写。
        object.__setattr__(self, "batch_intent", dict(self.batch_intent or {}))  # 新增代码+LayeredStagePlanner：复制批执行意图；如果没有这行代码，编译器看到的意图可能漂移。
        object.__setattr__(self, "verification_contract", dict(self.verification_contract or {}))  # 新增代码+LayeredStagePlanner：复制验证契约；如果没有这行代码，验证规则可能被外部改掉。
        object.__setattr__(self, "verifier", dict(self.verifier or {}))  # 新增代码+UniversalStageModels：复制 verifier 配置；如果没有这行代码，外部字典会污染阶段。
        object.__setattr__(self, "repair_policy", dict(self.repair_policy or {}))  # 新增代码+UniversalStageModels：复制修复配置；如果没有这行代码，重试规则可能被外部改掉。
    # 新增代码+UniversalStageModels：函数段结束，StagePlan.__post_init__ 到此结束；如果没有这个边界说明，初学者不容易看出阶段校验范围。
# 新增代码+UniversalStageModels：类段结束，StagePlan 到此结束；如果没有这个边界说明，初学者不容易看出阶段计划范围。


@dataclass(frozen=True)  # 新增代码+UniversalStageModels：声明任务计划不可变；如果没有这行代码，执行层可能改变原始计划。
class DesktopTaskPlan:  # 新增代码+UniversalStageModels：类段开始，表示用户桌面任务的通用阶段计划；如果没有这个类，复杂任务无法保持整体目标。
    objective: str  # 新增代码+UniversalStageModels：保存脱敏目标描述；如果没有这行代码，计划没有用户目标锚点。
    task_kind: str  # 新增代码+UniversalStageModels：保存通用任务类型；如果没有这行代码，运行时会退回应用特判。
    targets: tuple[dict[str, Any], ...] = field(default_factory=tuple)  # 新增代码+UniversalStageModels：保存目标描述集合；如果没有这行代码，多应用任务无法表达。
    resources: tuple[dict[str, Any], ...] = field(default_factory=tuple)  # 新增代码+UniversalStageModels：保存资源描述集合；如果没有这行代码，保存/文件类任务缺上下文。
    success_criteria: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+UniversalStageModels：保存机器可验收标准；如果没有这行代码，final gate 无法判断完成。
    stages: tuple[StagePlan, ...] = field(default_factory=tuple)  # 新增代码+UniversalStageModels：保存有序阶段；如果没有这行代码，任务无法按阶段推进。
    prompt_signature: str = ""  # 新增代码+UniversalStageModels：保存脱敏 prompt 签名；如果没有这行代码，日志无法区分任务且不泄露原文。
    layer_skill_metadata: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayeredStagePlanner：保存内部层 prompt 元数据；如果没有这行代码，报告无法证明使用了哪个 Computer Use 层版本。

    def __post_init__(self) -> None:  # 新增代码+UniversalStageModels：函数段开始，校验任务计划字段；如果没有这段函数，空计划会被当成可执行。
        cleaned_task_kind = _stage_models_clean_text(self.task_kind)  # 新增代码+UniversalStageModels：清洗任务类型；如果没有这行代码，泛化判断会受空白影响。
        if not cleaned_task_kind:  # 新增代码+UniversalStageModels：检查任务类型是否为空；如果没有这行代码，运行时无法选择阶段策略。
            raise ValueError("task_kind is required")  # 新增代码+UniversalStageModels：空任务类型直接失败；如果没有这行代码，错误会延迟到执行层。
        object.__setattr__(self, "objective", _stage_models_clean_text(self.objective))  # 新增代码+UniversalStageModels：写回清洗后的目标；如果没有这行代码，证据摘要可能带换行。
        object.__setattr__(self, "task_kind", cleaned_task_kind)  # 新增代码+UniversalStageModels：写回清洗后的任务类型；如果没有这行代码，报告字段不稳定。
        object.__setattr__(self, "targets", _stage_models_tuple_of_dicts(self.targets))  # 新增代码+UniversalStageModels：复制目标描述为元组；如果没有这行代码，外部可变列表会污染计划。
        object.__setattr__(self, "resources", _stage_models_tuple_of_dicts(self.resources))  # 新增代码+UniversalStageModels：复制资源描述为元组；如果没有这行代码，资源证据可能被外部改掉。
        object.__setattr__(self, "success_criteria", _stage_models_tuple_of_text(self.success_criteria))  # 新增代码+UniversalStageModels：复制成功标准为文本元组；如果没有这行代码，验收标准可能为空字符串。
        object.__setattr__(self, "stages", tuple(self.stages or ()))  # 新增代码+UniversalStageModels：固定阶段列表；如果没有这行代码，运行中计划可能被追加。
        object.__setattr__(self, "prompt_signature", _stage_models_clean_text(self.prompt_signature))  # 新增代码+UniversalStageModels：清洗 prompt 签名；如果没有这行代码，日志关联键不稳定。
        object.__setattr__(self, "layer_skill_metadata", dict(self.layer_skill_metadata or {}))  # 新增代码+LayeredStagePlanner：复制层元数据；如果没有这行代码，外部修改会污染计划证据。
    # 新增代码+UniversalStageModels：函数段结束，DesktopTaskPlan.__post_init__ 到此结束；如果没有这个边界说明，初学者不容易看出计划校验范围。
# 新增代码+UniversalStageModels：类段结束，DesktopTaskPlan 到此结束；如果没有这个边界说明，初学者不容易看出任务计划范围。


@dataclass(frozen=True)  # 新增代码+UniversalStageModels：声明阶段结果不可变；如果没有这行代码，验收证据可能被后续层改写。
class StageResult:  # 新增代码+UniversalStageModels：类段开始，表示阶段执行或验证结果；如果没有这个类，final gate 没有统一输入。
    status: str  # 新增代码+UniversalStageModels：保存阶段状态；如果没有这行代码，无法区分完成、修复、用户处理和失败。
    stage_id: str  # 新增代码+UniversalStageModels：保存阶段 id；如果没有这行代码，结果无法映射回计划。
    evidence: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+UniversalStageModels：保存阶段证据；如果没有这行代码，验收无法解释为什么通过或失败。
    message: str = ""  # 新增代码+UniversalStageModels：保存给用户或调试的短消息；如果没有这行代码，失败原因难以读懂。

    def __post_init__(self) -> None:  # 新增代码+UniversalStageModels：函数段开始，校验阶段结果；如果没有这段函数，乱状态会进入最终门禁。
        cleaned_status = _stage_models_clean_text(self.status)  # 新增代码+UniversalStageModels：清洗状态文本；如果没有这行代码，状态比较不稳定。
        if cleaned_status not in STAGE_RESULT_STATUSES:  # 新增代码+UniversalStageModels：检查状态是否在允许集合；如果没有这行代码，final gate 可能误判完成。
            raise ValueError(f"status must be one of {sorted(STAGE_RESULT_STATUSES)}")  # 新增代码+UniversalStageModels：非法状态直接失败；如果没有这行代码，错误会变成静默跳过。
        object.__setattr__(self, "status", cleaned_status)  # 新增代码+UniversalStageModels：写回清洗后的状态；如果没有这行代码，序列化状态可能带空白。
        object.__setattr__(self, "stage_id", _stage_models_clean_text(self.stage_id))  # 新增代码+UniversalStageModels：写回清洗后的阶段 id；如果没有这行代码，结果和计划无法稳定匹配。
        object.__setattr__(self, "evidence", dict(self.evidence or {}))  # 新增代码+UniversalStageModels：复制证据字典；如果没有这行代码，外部修改会污染结果。
        object.__setattr__(self, "message", _stage_models_clean_text(self.message))  # 新增代码+UniversalStageModels：清洗消息；如果没有这行代码，报告可能出现多行噪声。
    # 新增代码+UniversalStageModels：函数段结束，StageResult.__post_init__ 到此结束；如果没有这个边界说明，初学者不容易看出结果校验范围。
# 新增代码+UniversalStageModels：类段结束，StageResult 到此结束；如果没有这个边界说明，初学者不容易看出阶段结果范围。


@dataclass(frozen=True)  # 新增代码+UniversalStageModels：声明任务运行状态不可变快照；如果没有这行代码，多目标运行证据会散落。
class DesktopTaskRunState:  # 新增代码+UniversalStageModels：类段开始，表示一次桌面任务运行中的目标映射；如果没有这个类，多窗口任务难以保证一对一。
    target_sessions_by_ref: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+UniversalStageModels：保存 target_ref 到 session 的映射；如果没有这行代码，多窗口任务会共享错误窗口。
    active_target_ref: str = ""  # 新增代码+UniversalStageModels：保存当前活动目标；如果没有这行代码，切换窗口后无法审计。
    stage_target_ref: str = ""  # 新增代码+UniversalStageModels：保存当前阶段目标；如果没有这行代码，阶段写入对象无法验证。
    user_granted_existing_target_refs: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+UniversalStageModels：保存用户授权的已有窗口；如果没有这行代码，单实例 app 授权无法表达。
    blocked_target_refs: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+UniversalStageModels：保存被阻断目标；如果没有这行代码，后续阶段可能重复尝试危险窗口。

    def __post_init__(self) -> None:  # 新增代码+UniversalStageModels：函数段开始，规范化运行状态；如果没有这段函数，状态字段会保持外部可变对象。
        object.__setattr__(self, "target_sessions_by_ref", dict(self.target_sessions_by_ref or {}))  # 新增代码+UniversalStageModels：复制目标 session 映射；如果没有这行代码，外部修改会影响运行状态。
        object.__setattr__(self, "active_target_ref", _stage_models_clean_text(self.active_target_ref))  # 新增代码+UniversalStageModels：清洗活动目标；如果没有这行代码，比较会不稳定。
        object.__setattr__(self, "stage_target_ref", _stage_models_clean_text(self.stage_target_ref))  # 新增代码+UniversalStageModels：清洗阶段目标；如果没有这行代码，阶段证据会漂移。
        object.__setattr__(self, "user_granted_existing_target_refs", _stage_models_tuple_of_text(self.user_granted_existing_target_refs))  # 新增代码+UniversalStageModels：规范化授权目标；如果没有这行代码，授权集合可能含空值。
        object.__setattr__(self, "blocked_target_refs", _stage_models_tuple_of_text(self.blocked_target_refs))  # 新增代码+UniversalStageModels：规范化阻断目标；如果没有这行代码，阻断集合可能含空值。
    # 新增代码+UniversalStageModels：函数段结束，DesktopTaskRunState.__post_init__ 到此结束；如果没有这个边界说明，初学者不容易看出运行状态范围。
# 新增代码+UniversalStageModels：类段结束，DesktopTaskRunState 到此结束；如果没有这个边界说明，初学者不容易看出运行快照范围。


def action_batch_to_dict(batch: ActionBatch) -> dict[str, Any]:  # 新增代码+UniversalStageModels：函数段开始，序列化动作批；如果没有这段函数，批证据无法稳定落盘。
    return {"batch_id": batch.batch_id, "batch_kind": batch.batch_kind, "target_ref": batch.target_ref, "actions": [dict(action) for action in batch.actions], "guardrails": dict(batch.guardrails)}  # 新增代码+UniversalStageModels：返回 JSON 安全字典；如果没有这行代码，acceptance 无法读取批字段。
# 新增代码+UniversalStageModels：函数段结束，action_batch_to_dict 到此结束；如果没有这个边界说明，初学者不容易看出批序列化范围。


def action_batch_from_dict(payload: Mapping[str, Any] | None) -> ActionBatch | None:  # 新增代码+UniversalStageModels：函数段开始，反序列化动作批；如果没有这段函数，计划证据无法恢复成模型。
    if not isinstance(payload, Mapping):  # 新增代码+UniversalStageModels：检查输入是否是映射；如果没有这行代码，None 批会导致异常。
        return None  # 新增代码+UniversalStageModels：空批返回 None；如果没有这行代码，准备阶段无法无批存在。
    return ActionBatch(batch_id=payload.get("batch_id", ""), batch_kind=payload.get("batch_kind", ""), target_ref=payload.get("target_ref", ""), actions=tuple(payload.get("actions", []) or ()), guardrails=dict(payload.get("guardrails", {}) or {}))  # 新增代码+UniversalStageModels：构造动作批；如果没有这行代码，反序列化不能恢复嵌套对象。
# 新增代码+UniversalStageModels：函数段结束，action_batch_from_dict 到此结束；如果没有这个边界说明，初学者不容易看出批反序列化范围。


def stage_plan_to_dict(stage: StagePlan) -> dict[str, Any]:  # 新增代码+UniversalStageModels：函数段开始，序列化阶段计划；如果没有这段函数，阶段证据无法进入 JSON。
    return {"stage_id": stage.stage_id, "stage_kind": stage.stage_kind, "target_ref": stage.target_ref, "observation_policy": stage.observation_policy, "batch": action_batch_to_dict(stage.batch) if stage.batch is not None else None, "input_contract": dict(stage.input_contract), "output_contract": dict(stage.output_contract), "batch_intent": dict(stage.batch_intent), "verification_contract": dict(stage.verification_contract), "verifier": dict(stage.verifier), "repair_policy": dict(stage.repair_policy)}  # 修改代码+LayeredStagePlanner：返回包含分层契约的阶段字典；如果没有这些字段，运行报告无法审计规划质量。
# 新增代码+UniversalStageModels：函数段结束，stage_plan_to_dict 到此结束；如果没有这个边界说明，初学者不容易看出阶段序列化范围。


def stage_plan_from_dict(payload: Mapping[str, Any]) -> StagePlan:  # 新增代码+UniversalStageModels：函数段开始，反序列化阶段计划；如果没有这段函数，落盘计划无法恢复。
    return StagePlan(stage_id=payload.get("stage_id", ""), stage_kind=payload.get("stage_kind", ""), target_ref=payload.get("target_ref", ""), observation_policy=payload.get("observation_policy", "before_and_after_stage"), batch=action_batch_from_dict(payload.get("batch")), input_contract=dict(payload.get("input_contract", {}) or {}), output_contract=dict(payload.get("output_contract", {}) or {}), batch_intent=dict(payload.get("batch_intent", {}) or {}), verification_contract=dict(payload.get("verification_contract", {}) or {}), verifier=dict(payload.get("verifier", {}) or {}), repair_policy=dict(payload.get("repair_policy", {}) or {}))  # 修改代码+LayeredStagePlanner：恢复分层契约字段；如果没有这些字段，落盘计划无法完整回放。
# 新增代码+UniversalStageModels：函数段结束，stage_plan_from_dict 到此结束；如果没有这个边界说明，初学者不容易看出阶段反序列化范围。


def desktop_task_plan_to_dict(plan: DesktopTaskPlan) -> dict[str, Any]:  # 新增代码+UniversalStageModels：函数段开始，序列化桌面任务计划；如果没有这段函数，任务计划无法写入验收证据。
    return {"objective": plan.objective, "task_kind": plan.task_kind, "targets": [dict(target) for target in plan.targets], "resources": [dict(resource) for resource in plan.resources], "success_criteria": list(plan.success_criteria), "stages": [stage_plan_to_dict(stage) for stage in plan.stages], "prompt_signature": plan.prompt_signature, "layer_skill_metadata": dict(plan.layer_skill_metadata)}  # 修改代码+LayeredStagePlanner：返回带层 prompt 元数据的计划；如果没有这行代码，acceptance 无法确认 layered planner 已接线。
# 新增代码+UniversalStageModels：函数段结束，desktop_task_plan_to_dict 到此结束；如果没有这个边界说明，初学者不容易看出计划序列化范围。


def desktop_task_plan_from_dict(payload: Mapping[str, Any]) -> DesktopTaskPlan:  # 新增代码+UniversalStageModels：函数段开始，反序列化桌面任务计划；如果没有这段函数，测试和回放无法恢复计划。
    return DesktopTaskPlan(objective=payload.get("objective", ""), task_kind=payload.get("task_kind", ""), targets=tuple(payload.get("targets", []) or ()), resources=tuple(payload.get("resources", []) or ()), success_criteria=tuple(payload.get("success_criteria", []) or ()), stages=tuple(stage_plan_from_dict(stage) for stage in list(payload.get("stages", []) or []) if isinstance(stage, Mapping)), prompt_signature=payload.get("prompt_signature", ""), layer_skill_metadata=dict(payload.get("layer_skill_metadata", {}) or {}))  # 修改代码+LayeredStagePlanner：恢复层 prompt 元数据；如果没有这行代码，计划回放会丢失分层证据。
# 新增代码+UniversalStageModels：函数段结束，desktop_task_plan_from_dict 到此结束；如果没有这个边界说明，初学者不容易看出计划反序列化范围。


def stage_result_to_dict(result: StageResult) -> dict[str, Any]:  # 新增代码+UniversalStageModels：函数段开始，序列化阶段结果；如果没有这段函数，final gate 证据无法落盘。
    return {"status": result.status, "stage_id": result.stage_id, "evidence": dict(result.evidence), "message": result.message}  # 新增代码+UniversalStageModels：返回阶段结果字典；如果没有这行代码，验收报告无法读取状态。
# 新增代码+UniversalStageModels：函数段结束，stage_result_to_dict 到此结束；如果没有这个边界说明，初学者不容易看出结果序列化范围。


__all__ = ["ActionBatch", "DesktopTaskPlan", "DesktopTaskRunState", "StagePlan", "StageResult", "STAGE_RESULT_STATUSES", "action_batch_from_dict", "action_batch_to_dict", "desktop_task_plan_from_dict", "desktop_task_plan_to_dict", "stage_plan_from_dict", "stage_plan_to_dict", "stage_result_to_dict"]  # 新增代码+UniversalStageModels：声明公开接口；如果没有这行代码，通配导入会暴露内部 helper。
