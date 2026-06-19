"""Reflection and sanitized learning layer for universal Computer Use."""  # 新增代码+ReflectionLearningLayer：说明本文件只负责失败反思和脱敏学习；如果没有这行代码，读者容易误以为这里会直接控制桌面。
from __future__ import annotations  # 新增代码+ReflectionLearningLayer：启用延迟类型解析；如果没有这行代码，类型注解在旧启动方式下更容易受导入顺序影响。

import json  # 新增代码+ReflectionLearningLayer：导入 JSON 用于压缩证据和写入 JSONL；如果没有这行代码，学习记录无法稳定序列化。
from pathlib import Path  # 新增代码+ReflectionLearningLayer：导入 Path 管理 runtime_learning 路径；如果没有这行代码，Windows 路径拼接更容易出错。
from typing import Any, Mapping  # 新增代码+ReflectionLearningLayer：导入宽松 JSON 类型；如果没有这行代码，阶段结果和观察事实接口边界不清。

from learning_agent.computer_use_mcp_v2.windows_runtime.layer_contracts import ReflectionLearningResult  # 新增代码+ReflectionLearningLayer：复用分层反思结果契约；如果没有这行代码，反思层会返回散乱 dict。
from learning_agent.computer_use_mcp_v2.windows_runtime.layer_skill_loader import load_layer_skill  # 新增代码+ReflectionLearningLayer：加载内部 reflection skill 元数据；如果没有这行代码，报告无法证明使用了哪版反思提示。
from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import StageResult  # 新增代码+ReflectionLearningLayer：导入阶段结果模型；如果没有这行代码，类型边界不清楚。
from learning_agent.runtime.files import append_jsonl, read_jsonl  # 新增代码+ReflectionLearningLayer：复用项目安全 JSONL 读写工具；如果没有这行代码，学习记录落盘会重复实现。


DEFAULT_RUNTIME_LEARNING_ROOT = Path(__file__).resolve().parents[1] / "runtime_learning"  # 新增代码+ReflectionLearningLayer：定义 Computer Use 内部学习目录；如果没有这行代码，学习文件可能散落到主 agent 记忆里。
DEFAULT_PATTERNS_PATH = DEFAULT_RUNTIME_LEARNING_ROOT / "patterns.jsonl"  # 新增代码+ReflectionLearningLayer：定义重复失败模式 JSONL 文件；如果没有这行代码，学习记录没有固定位置。
SENSITIVE_LEARNING_KEYS = frozenset({"prompt", "raw_prompt", "screenshot", "image", "clipboard", "password", "secret", "token", "credential", "document_content", "raw_text", "text", "file_path", "path"})  # 新增代码+ReflectionLearningLayer：定义学习层绝不保存的敏感字段；如果没有这行代码，失败经验可能泄露用户内容。
PATH_MARKERS = (":\\", ":/", "\\users\\", "/users/", "\\desktop\\", "/desktop/", "\\documents\\", "/documents/")  # 新增代码+ReflectionLearningLayer：定义常见本机私有路径标记；如果没有这行代码，字符串路径可能被写入学习文件。
REPAIR_STRATEGIES = {"wrong_region": "reobserve_and_recompile_batch", "target_drift": "reacquire_target_or_request_user", "batch_too_small": "compile_larger_stage_batch", "save_dialog_unhandled": "handle_save_dialog_or_request_user", "missing_content": "reobserve_and_recompile_content_batch", "capability_unknown": "replan_with_capability_probe"}  # 新增代码+ReflectionLearningLayer：定义失败分类到修复策略的通用映射；如果没有这行代码，反思结果只会描述失败而不会指导下一步。


def _reflection_clean_text(value: Any, limit: int = 180) -> str:  # 新增代码+ReflectionLearningLayer：函数段开始，清洗短文本证据；如果没有这段函数，证据摘要可能包含换行和长内容。
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())  # 新增代码+ReflectionLearningLayer：把动态值转成单行文本；如果没有这行代码，JSONL 会被长多行文本污染。
    lowered = text.lower()  # 新增代码+ReflectionLearningLayer：准备小写文本用于路径检测；如果没有这行代码，Windows 路径大小写可能漏判。
    if any(marker in lowered for marker in PATH_MARKERS):  # 新增代码+ReflectionLearningLayer：检测字符串是否像本机私有路径；如果没有这行代码，桌面文件路径可能进入学习记录。
        return "<redacted_path>"  # 新增代码+ReflectionLearningLayer：用脱敏占位替代私有路径；如果没有这行代码，学习文件会泄露用户目录。
    return text[:limit]  # 新增代码+ReflectionLearningLayer：限制文本长度；如果没有这行代码，大段内容会挤爆学习记录。
# 新增代码+ReflectionLearningLayer：函数段结束，_reflection_clean_text 到此结束；如果没有这个边界说明，用户不容易看出文本脱敏范围。


def _reflection_sanitize_payload(payload: Any) -> Any:  # 新增代码+ReflectionLearningLayer：函数段开始，递归脱敏学习候选；如果没有这段函数，敏感字段可能被原样写盘。
    if isinstance(payload, Mapping):  # 新增代码+ReflectionLearningLayer：处理字典对象；如果没有这行代码，嵌套证据无法按字段脱敏。
        sanitized: dict[str, Any] = {}  # 新增代码+ReflectionLearningLayer：准备脱敏后的字典；如果没有这行代码，递归结果没有容器。
        for key, value in payload.items():  # 新增代码+ReflectionLearningLayer：遍历每个字段；如果没有这行代码，字段级规则无法执行。
            clean_key = _reflection_clean_text(key, 80)  # 新增代码+ReflectionLearningLayer：清洗字段名；如果没有这行代码，非字符串 key 可能影响比较。
            if clean_key.lower() in SENSITIVE_LEARNING_KEYS:  # 新增代码+ReflectionLearningLayer：敏感字段直接替换；如果没有这行代码，prompt、截图或剪贴板可能落盘。
                sanitized[clean_key] = "<redacted_sensitive_field>"  # 新增代码+ReflectionLearningLayer：写入脱敏占位；如果没有这行代码，读者不知道字段被故意隐藏。
                continue  # 新增代码+ReflectionLearningLayer：跳过敏感字段原值；如果没有这行代码，后续仍会递归保存明文。
            sanitized[clean_key] = _reflection_sanitize_payload(value)  # 新增代码+ReflectionLearningLayer：递归普通字段；如果没有这行代码，嵌套路径或敏感字段会漏掉。
        return sanitized  # 新增代码+ReflectionLearningLayer：返回脱敏字典；如果没有这行代码，字典分支没有结果。
    if isinstance(payload, (list, tuple)):  # 新增代码+ReflectionLearningLayer：处理列表和元组；如果没有这行代码，列表里的敏感字段无法递归。
        return [_reflection_sanitize_payload(item) for item in payload]  # 新增代码+ReflectionLearningLayer：返回脱敏列表；如果没有这行代码，数组证据会原样保留。
    if isinstance(payload, str):  # 新增代码+ReflectionLearningLayer：处理字符串；如果没有这行代码，路径字符串无法脱敏。
        return _reflection_clean_text(payload)  # 新增代码+ReflectionLearningLayer：返回清洗后的短字符串；如果没有这行代码，长文本会进入学习记录。
    if isinstance(payload, (int, float, bool)) or payload is None:  # 新增代码+ReflectionLearningLayer：允许简单 JSON 原子值；如果没有这行代码，数字计数会被错误转成字符串。
        return payload  # 新增代码+ReflectionLearningLayer：返回原子值；如果没有这行代码，学习统计会失去类型。
    return _reflection_clean_text(payload)  # 新增代码+ReflectionLearningLayer：其它对象转短文本兜底；如果没有这行代码，不可 JSON 对象会写入失败。
# 新增代码+ReflectionLearningLayer：函数段结束，_reflection_sanitize_payload 到此结束；如果没有这个边界说明，用户不容易看出脱敏范围。


def _reflection_blob(*values: Any) -> str:  # 新增代码+ReflectionLearningLayer：函数段开始，把失败证据压成小写搜索文本；如果没有这段函数，失败分类逻辑会到处重复。
    parts: list[str] = []  # 新增代码+ReflectionLearningLayer：准备文本片段列表；如果没有这行代码，后续无法累计多来源证据。
    for value in values:  # 新增代码+ReflectionLearningLayer：逐个处理传入证据；如果没有这行代码，只能看单一字段。
        try:  # 新增代码+ReflectionLearningLayer：优先 JSON 化结构证据；如果没有这行代码，字典和列表搜索不稳定。
            parts.append(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))  # 新增代码+ReflectionLearningLayer：把结构证据转成稳定文本；如果没有这行代码，失败分类可能漏掉嵌套 decision。
        except TypeError:  # 新增代码+ReflectionLearningLayer：处理不可序列化对象；如果没有这行代码，坏证据会中断反思层。
            parts.append(str(value))  # 新增代码+ReflectionLearningLayer：回退普通字符串；如果没有这行代码，异常对象没有可搜索内容。
    return " ".join(parts).lower()  # 新增代码+ReflectionLearningLayer：返回小写搜索文本；如果没有这行代码，分类匹配受大小写影响。
# 新增代码+ReflectionLearningLayer：函数段结束，_reflection_blob 到此结束；如果没有这个边界说明，用户不容易看出证据压缩范围。


def _reflection_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+ReflectionLearningLayer：函数段开始，安全读取计数字段；如果没有这段函数，坏 evidence 会让反思层崩溃。
    try:  # 新增代码+ReflectionLearningLayer：尝试转整数；如果没有这行代码，字符串数字无法兼容。
        return int(value)  # 新增代码+ReflectionLearningLayer：返回整数；如果没有这行代码，批大小判断无输入。
    except (TypeError, ValueError):  # 新增代码+ReflectionLearningLayer：捕获空值和非数字；如果没有这行代码，缺字段会中断反思。
        return int(default)  # 新增代码+ReflectionLearningLayer：返回默认值；如果没有这行代码，调用方还要自己兜底。
# 新增代码+ReflectionLearningLayer：函数段结束，_reflection_safe_int 到此结束；如果没有这个边界说明，用户不容易看出数字清洗范围。


def _reflection_failure_class(verifier_result: StageResult, observation_facts: Mapping[str, Any], action_result: StageResult) -> str:  # 新增代码+ReflectionLearningLayer：函数段开始，按通用证据分类失败；如果没有这段函数，失败后仍会重复同类错误。
    evidence = dict(verifier_result.evidence or {})  # 新增代码+ReflectionLearningLayer：读取 verifier 证据；如果没有这行代码，决策码无法进入分类。
    action_evidence = dict(action_result.evidence or {})  # 新增代码+ReflectionLearningLayer：读取执行层证据；如果没有这行代码，批大小和目标漂移无法分类。
    blob = _reflection_blob(evidence, action_evidence, observation_facts, verifier_result.message)  # 新增代码+ReflectionLearningLayer：合并多来源证据；如果没有这行代码，分类只看局部字段会漏判。
    low_level_count = _reflection_safe_int(action_evidence.get("low_level_event_count", evidence.get("low_level_event_count", 0)))  # 新增代码+ReflectionLearningLayer：读取底层事件数；如果没有这行代码，批太小无法识别。
    primitive_count = _reflection_safe_int(action_evidence.get("primitive_action_count", evidence.get("primitive_action_count", 0)))  # 新增代码+ReflectionLearningLayer：读取 primitive 数；如果没有这行代码，单动作弱批无法识别。
    if "wrong_region" in blob or ("region" in blob and "wrong" in blob):  # 新增代码+ReflectionLearningLayer：优先识别区域错误；如果没有这行代码，点错画布/输入区会被误分成缺内容。
        return "wrong_region"  # 新增代码+ReflectionLearningLayer：返回区域错误分类；如果没有这行代码，修复策略无法要求重新观察和重编译区域。
    if "target_drift" in blob or "wrong_target" in blob or "target_identity_failed" in blob or "target_not_safe" in blob:  # 新增代码+ReflectionLearningLayer：识别目标漂移和身份失败；如果没有这行代码，窗口错绑会被继续重试动作。
        return "target_drift"  # 新增代码+ReflectionLearningLayer：返回目标漂移分类；如果没有这行代码，修复策略不会重新获取目标。
    if "resource_commit_not_verified" in blob or "save_dialog" in blob or "file_save" in blob:  # 新增代码+ReflectionLearningLayer：识别保存对话框或资源提交失败；如果没有这行代码，保存失败会被误当缺内容。
        return "save_dialog_unhandled"  # 新增代码+ReflectionLearningLayer：返回保存处理失败分类；如果没有这行代码，修复策略不会处理保存弹窗。
    if low_level_count <= 1 or primitive_count <= 1 or "batch_too_small" in blob:  # 新增代码+ReflectionLearningLayer：识别批规模过小；如果没有这行代码，复杂绘图只画一条线的问题会反复出现。
        return "batch_too_small"  # 新增代码+ReflectionLearningLayer：返回批太小分类；如果没有这行代码，修复策略不会扩大阶段批。
    if "text_not_visible" in blob or "missing_requirements" in blob or "drawing_visual_evidence_incomplete" in blob or "missing_content" in blob:  # 新增代码+ReflectionLearningLayer：识别内容缺失；如果没有这行代码，文本/绘图未完成无法形成修复策略。
        return "missing_content"  # 新增代码+ReflectionLearningLayer：返回内容缺失分类；如果没有这行代码，下一轮不会围绕缺失内容重新编译。
    return "capability_unknown"  # 新增代码+ReflectionLearningLayer：无法归类时按能力未知处理；如果没有这行代码，反思层会返回空分类。
# 新增代码+ReflectionLearningLayer：函数段结束，_reflection_failure_class 到此结束；如果没有这个边界说明，用户不容易看出失败分类范围。


class ReflectionLearningLayer:  # 新增代码+ReflectionLearningLayer：类段开始，负责 Computer Use 内部反思和脱敏经验固化；如果没有这个类，失败后只能盲目重试。
    def __init__(self, patterns_path: str | Path | None = None, repeated_threshold: int = 2) -> None:  # 新增代码+ReflectionLearningLayer：函数段开始，初始化学习文件和重复阈值；如果没有这段函数，测试和生产无法指定独立学习位置。
        self.patterns_path = Path(patterns_path) if patterns_path is not None else DEFAULT_PATTERNS_PATH  # 新增代码+ReflectionLearningLayer：保存 JSONL 学习路径；如果没有这行代码，重复模式没有落盘目标。
        self.repeated_threshold = max(2, _reflection_safe_int(repeated_threshold, 2))  # 新增代码+ReflectionLearningLayer：保存至少两次才学习的阈值；如果没有这行代码，单次偶发失败会污染经验库。
        self._failure_counts: dict[str, int] = {}  # 新增代码+ReflectionLearningLayer：保存本进程内失败分类计数；如果没有这行代码，无法判断同类失败是否重复。
        self._skill_metadata = load_layer_skill("reflection_learning").metadata()  # 新增代码+ReflectionLearningLayer：加载反思层 skill 元数据；如果没有这行代码，运行报告无法审计反思层版本。
    # 新增代码+ReflectionLearningLayer：函数段结束，ReflectionLearningLayer.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def reflect_stage_failure(self, stage_id: str, verifier_result: StageResult, observation_facts: Mapping[str, Any], action_result: StageResult) -> ReflectionLearningResult:  # 新增代码+ReflectionLearningLayer：函数段开始，针对一个未完成阶段生成反思结果；如果没有这段函数，stage loop 无法把失败转成修复策略。
        failure_class = _reflection_failure_class(verifier_result, observation_facts, action_result)  # 新增代码+ReflectionLearningLayer：分类本次失败；如果没有这行代码，修复策略无法选择。
        repeated_count = self._failure_counts.get(failure_class, 0) + 1  # 新增代码+ReflectionLearningLayer：累加同类失败次数；如果没有这行代码，重复失败不能被识别。
        self._failure_counts[failure_class] = repeated_count  # 新增代码+ReflectionLearningLayer：写回计数；如果没有这行代码，下一次反思仍会以为第一次失败。
        repair_strategy = REPAIR_STRATEGIES.get(failure_class, "replan_with_capability_probe")  # 新增代码+ReflectionLearningLayer：选择通用修复策略；如果没有这行代码，反思结果缺下一步动作建议。
        candidate = _reflection_sanitize_payload({"failure_class": failure_class, "repair_strategy": repair_strategy, "stage_id": stage_id, "repeated_count": repeated_count, "decision": verifier_result.evidence.get("decision", ""), "low_level_event_count": action_result.evidence.get("low_level_event_count", 0)})  # 新增代码+ReflectionLearningLayer：生成脱敏学习候选；如果没有这行代码，学习层没有可落盘摘要。
        if repeated_count >= self.repeated_threshold:  # 新增代码+ReflectionLearningLayer：只有同类失败重复才固化经验；如果没有这行代码，偶发失败会污染长期学习。
            append_jsonl(self.patterns_path, dict(candidate))  # 新增代码+ReflectionLearningLayer：追加脱敏经验到 JSONL；如果没有这行代码，重复失败不会形成可复用经验。
        evidence_summary = _reflection_clean_text(f"{failure_class}:{verifier_result.evidence.get('decision', '')}:events={action_result.evidence.get('low_level_event_count', 0)}")  # 新增代码+ReflectionLearningLayer：生成低敏证据摘要；如果没有这行代码，报告缺少人可读失败线索。
        return ReflectionLearningResult(failure_class=failure_class, evidence_summary=evidence_summary, repair_strategy=repair_strategy, replan_required=failure_class in {"capability_unknown", "target_drift"}, user_input_required=failure_class == "target_drift" and "user" in _reflection_blob(verifier_result.evidence), learning_candidate=dict(candidate), layer_skill_metadata=dict(self._skill_metadata))  # 新增代码+ReflectionLearningLayer：返回结构化反思结果；如果没有这行代码，stage loop 无法把反思写入报告。
    # 新增代码+ReflectionLearningLayer：函数段结束，ReflectionLearningLayer.reflect_stage_failure 到此结束；如果没有这个边界说明，用户不容易看出反思入口范围。

    def read_patterns(self) -> list[dict[str, Any]]:  # 新增代码+ReflectionLearningLayer：函数段开始，读取已固化的重复失败模式；如果没有这段函数，测试和状态页无法检查学习记录。
        return read_jsonl(self.patterns_path)  # 新增代码+ReflectionLearningLayer：容错读取 JSONL 模式；如果没有这行代码，调用方要重复实现读取逻辑。
    # 新增代码+ReflectionLearningLayer：函数段结束，ReflectionLearningLayer.read_patterns 到此结束；如果没有这个边界说明，用户不容易看出读取范围。
# 新增代码+ReflectionLearningLayer：类段结束，ReflectionLearningLayer 到此结束；如果没有这个边界说明，用户不容易看出反思学习层范围。


__all__ = ["DEFAULT_PATTERNS_PATH", "ReflectionLearningLayer"]  # 新增代码+ReflectionLearningLayer：声明公开接口；如果没有这行代码，通配导入会暴露内部 helper。
