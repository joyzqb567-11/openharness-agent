"""Computer Use task-local harness context for layered desktop work."""  # 新增代码+LayeredHarnessContext：说明本文件只保存 Computer Use 桌面任务上下文；如果没有这行代码，后续层会把状态散落到各处。
from __future__ import annotations  # 新增代码+LayeredHarnessContext：启用延迟类型解析；如果没有这行代码，数据类互相引用时更容易遇到导入顺序问题。

import uuid  # 新增代码+LayeredHarnessContext：导入 UUID 生成稳定 task_id；如果没有这行代码，每个桌面任务无法得到唯一追踪编号。
from dataclasses import dataclass, field, replace  # 新增代码+LayeredHarnessContext：导入数据类和不可变更新工具；如果没有这行代码，上下文更新会变成易错的手写字典。
from typing import Any, Mapping  # 新增代码+LayeredHarnessContext：导入 JSON 风格类型；如果没有这行代码，公开接口的动态字段边界不清楚。


SENSITIVE_CONTEXT_KEYS = frozenset({"raw_screenshot", "raw_screenshot_b64", "screenshot_bytes", "raw_private_text", "raw_prompt", "clipboard_text", "password", "secret"})  # 新增代码+LayeredHarnessContext：集中列出禁止进入 JSON 证据的敏感键；如果没有这行代码，截图或私密文本可能进入长期日志。
WRITE_ACTION_CLASSES = frozenset({"type_text", "keyboard", "mouse", "drag", "save", "write", "clipboard_write", "batch_write"})  # 新增代码+LayeredHarnessContext：定义需要 target_ref 的写动作类别；如果没有这行代码，真实桌面动作可能缺少目标窗口绑定。


def _harness_text(value: Any) -> str:  # 新增代码+LayeredHarnessContext：函数段开始，把动态文本清理成单行；如果没有这段函数，task_id 和 stage_id 可能带换行污染证据。
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())  # 新增代码+LayeredHarnessContext：返回去掉换行和多余空白的文本；如果没有这行代码，JSON 证据会更难读。
# 新增代码+LayeredHarnessContext：函数段结束，_harness_text 到此结束；如果没有这个边界说明，用户不容易看出清洗范围。


def _harness_tuple(value: Any) -> tuple[str, ...]:  # 新增代码+LayeredHarnessContext：函数段开始，把列表类输入转成不可变文本元组；如果没有这段函数，外部可变列表会污染上下文。
    return tuple(item for item in (_harness_text(part) for part in list(value or ())) if item)  # 新增代码+LayeredHarnessContext：过滤空文本并返回元组；如果没有这行代码，allowed_target_refs 可能包含空字符串。
# 新增代码+LayeredHarnessContext：函数段结束，_harness_tuple 到此结束；如果没有这个边界说明，用户不容易看出元组转换范围。


def _sanitize_for_harness_json(value: Any) -> Any:  # 新增代码+LayeredHarnessContext：函数段开始，递归移除敏感证据；如果没有这段函数，原始截图和私密正文可能被保存。
    if isinstance(value, Mapping):  # 新增代码+LayeredHarnessContext：先处理字典结构；如果没有这行代码，嵌套证据无法逐键脱敏。
        clean: dict[str, Any] = {}  # 新增代码+LayeredHarnessContext：准备脱敏后的字典；如果没有这行代码，处理结果没有容器。
        for key, item in value.items():  # 新增代码+LayeredHarnessContext：遍历输入字典；如果没有这行代码，无法检查每个字段名。
            key_text = _harness_text(key)  # 新增代码+LayeredHarnessContext：把字段名转为可比较文本；如果没有这行代码，非字符串 key 会导致匹配不稳。
            if key_text.lower() in SENSITIVE_CONTEXT_KEYS:  # 新增代码+LayeredHarnessContext：命中敏感键时跳过；如果没有这行代码，禁止字段会进入输出。
                continue  # 新增代码+LayeredHarnessContext：不保存当前敏感字段；如果没有这行代码，脱敏规则不会生效。
            clean[key_text] = _sanitize_for_harness_json(item)  # 新增代码+LayeredHarnessContext：递归保存脱敏后的值；如果没有这行代码，嵌套字段不会被清理。
        return clean  # 新增代码+LayeredHarnessContext：返回脱敏字典；如果没有这行代码，调用方拿不到处理结果。
    if isinstance(value, (list, tuple, set)):  # 新增代码+LayeredHarnessContext：处理列表、元组和集合；如果没有这行代码，列表中的敏感字典不会被递归处理。
        return [_sanitize_for_harness_json(item) for item in value]  # 新增代码+LayeredHarnessContext：返回脱敏列表；如果没有这行代码，序列无法 JSON 化。
    return value  # 新增代码+LayeredHarnessContext：普通值原样返回；如果没有这行代码，数值和布尔字段会丢失。
# 新增代码+LayeredHarnessContext：函数段结束，_sanitize_for_harness_json 到此结束；如果没有这个边界说明，用户不容易看出脱敏范围。


@dataclass(frozen=True)  # 新增代码+LayeredHarnessContext：声明权限状态不可变；如果没有这行代码，运行中权限可能被其它层偷偷改掉。
class ComputerUsePermissionState:  # 新增代码+LayeredHarnessContext：类段开始，保存当前 Computer Use 权限事实；如果没有这个类，full mode、授权窗口和动作类别会分散。
    full_mode_enabled: bool = False  # 新增代码+LayeredHarnessContext：记录是否进入 full mode；如果没有这行代码，桌面任务无法判断是否允许真实动作。
    request_access_granted: bool = False  # 新增代码+LayeredHarnessContext：记录 request_access 是否通过；如果没有这行代码，工具授权状态无法进入上下文。
    allowed_target_refs: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+LayeredHarnessContext：保存允许操作的 target_ref；如果没有这行代码，多窗口任务无法限制目标。
    allowed_action_classes: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+LayeredHarnessContext：保存允许的动作类别；如果没有这行代码，安全层无法解释哪些动作被授权。
    user_granted_existing_target_refs: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+LayeredHarnessContext：保存用户明确授权复用的旧窗口；如果没有这行代码，单实例应用授权无法审计。

    def __post_init__(self) -> None:  # 新增代码+LayeredHarnessContext：函数段开始，规范化权限字段；如果没有这段函数，外部列表和空字符串会污染状态。
        object.__setattr__(self, "allowed_target_refs", _harness_tuple(self.allowed_target_refs))  # 新增代码+LayeredHarnessContext：固定允许目标元组；如果没有这行代码，目标列表可能被外部修改。
        object.__setattr__(self, "allowed_action_classes", _harness_tuple(self.allowed_action_classes))  # 新增代码+LayeredHarnessContext：固定动作类别元组；如果没有这行代码，权限类别比较不稳定。
        object.__setattr__(self, "user_granted_existing_target_refs", _harness_tuple(self.user_granted_existing_target_refs))  # 新增代码+LayeredHarnessContext：固定旧窗口授权元组；如果没有这行代码，授权状态可能含空值。
    # 新增代码+LayeredHarnessContext：函数段结束，ComputerUsePermissionState.__post_init__ 到此结束；如果没有这个边界说明，用户不容易看出权限规范化范围。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LayeredHarnessContext：函数段开始，把权限状态转成 JSON 字典；如果没有这段函数，报告层只能直接访问内部属性。
        return {"full_mode_enabled": self.full_mode_enabled, "request_access_granted": self.request_access_granted, "allowed_target_refs": list(self.allowed_target_refs), "allowed_action_classes": list(self.allowed_action_classes), "user_granted_existing_target_refs": list(self.user_granted_existing_target_refs)}  # 新增代码+LayeredHarnessContext：返回低敏权限字段；如果没有这行代码，acceptance 日志缺少授权事实。
    # 新增代码+LayeredHarnessContext：函数段结束，ComputerUsePermissionState.to_dict 到此结束；如果没有这个边界说明，用户不容易看出权限序列化范围。
# 新增代码+LayeredHarnessContext：类段结束，ComputerUsePermissionState 到此结束；如果没有这个边界说明，用户不容易看出权限类范围。


@dataclass(frozen=True)  # 新增代码+LayeredHarnessContext：声明工具使用上下文不可变；如果没有这行代码，一个批执行过程中字段可能被改写。
class ComputerUseToolUseContext:  # 新增代码+LayeredHarnessContext：类段开始，保存一次动作批或工具调用的局部上下文；如果没有这个类，批动作缺少 ClaudeCode 风格 tool-use 边界。
    tool_use_id: str  # 新增代码+LayeredHarnessContext：保存工具调用 id；如果没有这行代码，失败结果无法对应工具调用。
    stage_id: str  # 新增代码+LayeredHarnessContext：保存所属阶段 id；如果没有这行代码，批结果无法回填阶段。
    batch_id: str = ""  # 新增代码+LayeredHarnessContext：保存批 id；如果没有这行代码，批执行日志无法定位。
    target_ref: str = ""  # 新增代码+LayeredHarnessContext：保存目标窗口引用；如果没有这行代码，写动作可能默认打到当前焦点。
    action_class: str = ""  # 新增代码+LayeredHarnessContext：保存动作类别；如果没有这行代码，安全检查不知道这是读还是写。
    write_operation: bool = False  # 新增代码+LayeredHarnessContext：显式记录是否写桌面；如果没有这行代码，target_ref 门禁只能猜。
    metadata: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayeredHarnessContext：保存低敏工具元数据；如果没有这行代码，工具结果反馈会丢失。

    def __post_init__(self) -> None:  # 新增代码+LayeredHarnessContext：函数段开始，校验工具使用上下文；如果没有这段函数，非法写批会进入执行层。
        cleaned_target_ref = _harness_text(self.target_ref)  # 新增代码+LayeredHarnessContext：清理目标引用；如果没有这行代码，空白 target_ref 可能绕过判断。
        cleaned_action_class = _harness_text(self.action_class)  # 新增代码+LayeredHarnessContext：清理动作类别；如果没有这行代码，类别比较会不稳定。
        is_write = bool(self.write_operation or cleaned_action_class.lower() in WRITE_ACTION_CLASSES)  # 新增代码+LayeredHarnessContext：统一判断是否写动作；如果没有这行代码，type_text 这类写动作可能未声明就绕过。
        if is_write and not cleaned_target_ref:  # 新增代码+LayeredHarnessContext：写动作必须有 target_ref；如果没有这行代码，Computer Use 可能误操作旧窗口。
            raise ValueError("target_ref is required for write action batches")  # 新增代码+LayeredHarnessContext：直接拒绝缺目标写批；如果没有这行代码，错误会延迟到真实桌面动作。
        object.__setattr__(self, "tool_use_id", _harness_text(self.tool_use_id) or f"tool-{uuid.uuid4().hex[:12]}")  # 新增代码+LayeredHarnessContext：补齐并清洗工具 id；如果没有这行代码，空 id 会让日志难以追踪。
        object.__setattr__(self, "stage_id", _harness_text(self.stage_id))  # 新增代码+LayeredHarnessContext：清洗阶段 id；如果没有这行代码，阶段关联可能带空白。
        object.__setattr__(self, "batch_id", _harness_text(self.batch_id))  # 新增代码+LayeredHarnessContext：清洗批 id；如果没有这行代码，批日志不稳定。
        object.__setattr__(self, "target_ref", cleaned_target_ref)  # 新增代码+LayeredHarnessContext：写回目标引用；如果没有这行代码，内部仍保留脏值。
        object.__setattr__(self, "action_class", cleaned_action_class)  # 新增代码+LayeredHarnessContext：写回动作类别；如果没有这行代码，序列化会保留脏值。
        object.__setattr__(self, "write_operation", is_write)  # 新增代码+LayeredHarnessContext：写回统一后的写动作标记；如果没有这行代码，后续证据可能和实际不一致。
        object.__setattr__(self, "metadata", _sanitize_for_harness_json(dict(self.metadata or {})))  # 新增代码+LayeredHarnessContext：保存脱敏元数据；如果没有这行代码，工具上下文可能带入截图或私密文本。
    # 新增代码+LayeredHarnessContext：函数段结束，ComputerUseToolUseContext.__post_init__ 到此结束；如果没有这个边界说明，用户不容易看出工具上下文校验范围。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LayeredHarnessContext：函数段开始，把工具上下文转成 JSON 字典；如果没有这段函数，工具反馈无法稳定落盘。
        return {"tool_use_id": self.tool_use_id, "stage_id": self.stage_id, "batch_id": self.batch_id, "target_ref": self.target_ref, "action_class": self.action_class, "write_operation": self.write_operation, "metadata": dict(self.metadata)}  # 新增代码+LayeredHarnessContext：返回低敏工具上下文字段；如果没有这行代码，acceptance 无法检查 target_ref 门禁。
    # 新增代码+LayeredHarnessContext：函数段结束，ComputerUseToolUseContext.to_dict 到此结束；如果没有这个边界说明，用户不容易看出工具上下文序列化范围。
# 新增代码+LayeredHarnessContext：类段结束，ComputerUseToolUseContext 到此结束；如果没有这个边界说明，用户不容易看出工具上下文类范围。


@dataclass(frozen=True)  # 新增代码+LayeredHarnessContext：声明任务上下文不可变；如果没有这行代码，阶段运行时可能意外改掉历史状态。
class ComputerUseTaskContext:  # 新增代码+LayeredHarnessContext：类段开始，保存一个桌面任务的局部上下文；如果没有这个类，理解、规划、观察、执行和验证层没有共同状态。
    task_id: str = ""  # 新增代码+LayeredHarnessContext：保存桌面任务 id；如果没有这行代码，跨阶段日志无法归属同一任务。
    current_stage_id: str = ""  # 新增代码+LayeredHarnessContext：保存当前阶段 id；如果没有这行代码，工具结果反馈无法知道当前执行到哪一步。
    allowed_target_refs: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+LayeredHarnessContext：保存本任务允许目标；如果没有这行代码，写批难以限制到目标窗口。
    permission_state: ComputerUsePermissionState = field(default_factory=ComputerUsePermissionState)  # 新增代码+LayeredHarnessContext：保存权限状态；如果没有这行代码，task context 无法表达 full/request_access。
    verifier_state: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayeredHarnessContext：保存 verifier 低敏状态；如果没有这行代码，失败或完成证据不能反馈给下一轮。
    reflection_state: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayeredHarnessContext：保存 reflection 低敏状态；如果没有这行代码，失败后的修复学习无法回到计划层。
    stage_results: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)  # 新增代码+LayeredHarnessContext：保存阶段结果摘要；如果没有这行代码，任务进度状态无法像 ClaudeCode harness 那样持续展示。

    def __post_init__(self) -> None:  # 新增代码+LayeredHarnessContext：函数段开始，规范化任务上下文字段；如果没有这段函数，空 id 和可变输入会污染状态。
        object.__setattr__(self, "task_id", _harness_text(self.task_id) or f"cu-task-{uuid.uuid4().hex}")  # 新增代码+LayeredHarnessContext：生成或清洗稳定 task_id；如果没有这行代码，新任务无法被追踪。
        object.__setattr__(self, "current_stage_id", _harness_text(self.current_stage_id))  # 新增代码+LayeredHarnessContext：清洗当前阶段；如果没有这行代码，阶段字段可能带换行。
        object.__setattr__(self, "allowed_target_refs", _harness_tuple(self.allowed_target_refs))  # 新增代码+LayeredHarnessContext：固定允许目标元组；如果没有这行代码，外部列表可能改变任务权限。
        object.__setattr__(self, "verifier_state", _sanitize_for_harness_json(dict(self.verifier_state or {})))  # 新增代码+LayeredHarnessContext：脱敏 verifier 状态；如果没有这行代码，原始截图或私密文本可能进入上下文。
        object.__setattr__(self, "reflection_state", _sanitize_for_harness_json(dict(self.reflection_state or {})))  # 新增代码+LayeredHarnessContext：脱敏 reflection 状态；如果没有这行代码，失败学习可能保存用户隐私。
        object.__setattr__(self, "stage_results", tuple(_sanitize_for_harness_json(dict(item)) for item in self.stage_results if isinstance(item, Mapping)))  # 新增代码+LayeredHarnessContext：脱敏并固定阶段结果；如果没有这行代码，阶段结果可能保存原始证据。
    # 新增代码+LayeredHarnessContext：函数段结束，ComputerUseTaskContext.__post_init__ 到此结束；如果没有这个边界说明，用户不容易看出任务上下文规范化范围。

    def with_stage(self, stage_id: str) -> "ComputerUseTaskContext":  # 新增代码+LayeredHarnessContext：函数段开始，返回切换阶段后的新上下文；如果没有这段函数，调用方可能手写 dict 破坏 task_id 稳定性。
        return replace(self, current_stage_id=_harness_text(stage_id))  # 新增代码+LayeredHarnessContext：仅更新阶段并保留原 task_id；如果没有这行代码，阶段切换可能生成新任务。
    # 新增代码+LayeredHarnessContext：函数段结束，ComputerUseTaskContext.with_stage 到此结束；如果没有这个边界说明，用户不容易看出阶段切换范围。

    def with_verifier_state(self, verifier_state: Mapping[str, Any]) -> "ComputerUseTaskContext":  # 新增代码+LayeredHarnessContext：函数段开始，返回带新 verifier 状态的上下文；如果没有这段函数，验证结果无法反馈给后续层。
        return replace(self, verifier_state=dict(verifier_state or {}))  # 新增代码+LayeredHarnessContext：复制 verifier 状态并触发脱敏；如果没有这行代码，调用方可能污染原上下文。
    # 新增代码+LayeredHarnessContext：函数段结束，ComputerUseTaskContext.with_verifier_state 到此结束；如果没有这个边界说明，用户不容易看出 verifier 更新范围。

    def with_reflection_state(self, reflection_state: Mapping[str, Any]) -> "ComputerUseTaskContext":  # 新增代码+LayeredHarnessContext：函数段开始，返回带新 reflection 状态的上下文；如果没有这段函数，失败反思无法进入下一轮计划。
        return replace(self, reflection_state=dict(reflection_state or {}))  # 新增代码+LayeredHarnessContext：复制 reflection 状态并触发脱敏；如果没有这行代码，调用方可能保存敏感原始证据。
    # 新增代码+LayeredHarnessContext：函数段结束，ComputerUseTaskContext.with_reflection_state 到此结束；如果没有这个边界说明，用户不容易看出 reflection 更新范围。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LayeredHarnessContext：函数段开始，把任务上下文转成低敏 JSON 字典；如果没有这段函数，报告层无法稳定输出。
        return _sanitize_for_harness_json({"task_id": self.task_id, "current_stage_id": self.current_stage_id, "allowed_target_refs": list(self.allowed_target_refs), "permission_state": self.permission_state.to_dict(), "verifier_state": dict(self.verifier_state), "reflection_state": dict(self.reflection_state), "stage_results": [dict(item) for item in self.stage_results]})  # 新增代码+LayeredHarnessContext：返回脱敏后的上下文证据；如果没有这行代码，acceptance controller 无法审计任务状态。
    # 新增代码+LayeredHarnessContext：函数段结束，ComputerUseTaskContext.to_dict 到此结束；如果没有这个边界说明，用户不容易看出任务上下文序列化范围。
# 新增代码+LayeredHarnessContext：类段结束，ComputerUseTaskContext 到此结束；如果没有这个边界说明，用户不容易看出任务上下文类范围。


@dataclass(frozen=True)  # 新增代码+LayeredHarnessContext：声明 harness 快照不可变；如果没有这行代码，落盘证据可能在生成后被改。
class ComputerUseHarnessSnapshot:  # 新增代码+LayeredHarnessContext：类段开始，组合任务上下文和工具上下文的快照；如果没有这个类，单次工具结果无法带完整任务状态。
    task_context: ComputerUseTaskContext  # 新增代码+LayeredHarnessContext：保存任务级上下文；如果没有这行代码，快照不知道属于哪个桌面任务。
    tool_use_context: ComputerUseToolUseContext | None = None  # 新增代码+LayeredHarnessContext：保存可选工具级上下文；如果没有这行代码，快照无法表达当前批动作。
    evidence: Mapping[str, Any] = field(default_factory=dict)  # 新增代码+LayeredHarnessContext：保存低敏证据摘要；如果没有这行代码，快照无法承载观察或验证反馈。

    def to_dict(self) -> dict[str, Any]:  # 新增代码+LayeredHarnessContext：函数段开始，把快照转成 JSON 字典；如果没有这段函数，运行报告无法统一保存 context。
        return _sanitize_for_harness_json({"task_context": self.task_context.to_dict(), "tool_use_context": self.tool_use_context.to_dict() if self.tool_use_context else None, "evidence": dict(self.evidence or {})})  # 新增代码+LayeredHarnessContext：返回完整脱敏快照；如果没有这行代码，敏感字段可能绕过 task_context 的脱敏。
    # 新增代码+LayeredHarnessContext：函数段结束，ComputerUseHarnessSnapshot.to_dict 到此结束；如果没有这个边界说明，用户不容易看出快照序列化范围。
# 新增代码+LayeredHarnessContext：类段结束，ComputerUseHarnessSnapshot 到此结束；如果没有这个边界说明，用户不容易看出快照类范围。


__all__ = ["ComputerUseHarnessSnapshot", "ComputerUsePermissionState", "ComputerUseTaskContext", "ComputerUseToolUseContext"]  # 新增代码+LayeredHarnessContext：声明公开接口；如果没有这行代码，通配导入会暴露内部脱敏 helper。
