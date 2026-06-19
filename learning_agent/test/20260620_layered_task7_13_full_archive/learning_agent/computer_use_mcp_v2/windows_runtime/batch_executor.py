"""Execute universal Computer Use action batches through the existing DSL runtime."""  # 新增代码+BatchExecutor：说明本文件只编排批执行，不直接控制具体软件；如果没有这行代码，读者会误以为这里绕过底层安全层。
from __future__ import annotations  # 新增代码+BatchExecutor：启用延迟类型解析；如果没有这行代码，类型注解更容易导入失败。

from typing import Any, Mapping  # 新增代码+BatchExecutor：导入 JSON 风格类型；如果没有这行代码，session 和结果接口不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.stage_models import ActionBatch, StageResult  # 新增代码+BatchExecutor：导入批和阶段结果模型；如果没有这行代码，执行器会返回散乱 dict。


def _batch_executor_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+BatchExecutor：函数段开始，安全读取事件数字段；如果没有这段函数，坏 sender 报告会让批执行崩溃。
    try:  # 新增代码+BatchExecutor：尝试转整数；如果没有这行代码，字符串数字无法兼容。
        return int(value)  # 新增代码+BatchExecutor：返回整数；如果没有这行代码，调用方无法累计事件数。
    except (TypeError, ValueError):  # 新增代码+BatchExecutor：捕获空值和非数字；如果没有这行代码，单个坏字段会中断任务。
        return int(default)  # 新增代码+BatchExecutor：返回默认值；如果没有这行代码，缺字段无法按 0 处理。
# 新增代码+BatchExecutor：函数段结束，_batch_executor_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出数字清洗范围。


def _batch_executor_event_limit(batch: ActionBatch, default_limit: int) -> int:  # 新增代码+BatchEventLimit：函数段开始，读取当前批允许的低层事件上限；如果没有这段函数，大批动作可能无限拖拽或键入。
    raw_limit = dict(batch.guardrails).get("max_low_level_events", default_limit)  # 新增代码+BatchEventLimit：优先读取批 guardrail 里的上限；如果没有这行代码，单个阶段无法按风险缩小事件预算。
    limit = _batch_executor_safe_int(raw_limit, default_limit)  # 新增代码+BatchEventLimit：把上限清洗成整数；如果没有这行代码，字符串或坏值会导致比较异常。
    return max(1, limit)  # 新增代码+BatchEventLimit：至少允许一个事件，避免配置成 0 后所有批都无法执行；如果没有这行代码，误配置会让 Computer Use 全部停摆。
# 新增代码+BatchEventLimit：函数段结束，_batch_executor_event_limit 到此结束；如果没有这个边界说明，用户不容易看出事件预算来源。


def _batch_executor_stage_id(batch: ActionBatch) -> str:  # 新增代码+BatchExecutor：函数段开始，从批里推导阶段 id；如果没有这段函数，阶段结果无法映射回计划。
    return str(dict(batch.guardrails).get("stage_id", batch.batch_id) or batch.batch_id)  # 新增代码+BatchExecutor：优先使用 guardrail 里的阶段 id；如果没有这行代码，结果只能显示批 id。
# 新增代码+BatchExecutor：函数段结束，_batch_executor_stage_id 到此结束；如果没有这个边界说明，初学者不容易看出阶段 id 来源。


def _batch_executor_current_window(session: Mapping[str, Any]) -> dict[str, Any]:  # 新增代码+BatchExecutor：函数段开始，读取当前目标窗口；如果没有这段函数，target verifier 没有窗口输入。
    window = session.get("target_window", {}) if isinstance(session, Mapping) else {}  # 新增代码+BatchExecutor：读取 session 里的目标窗口；如果没有这行代码，复核无法比较窗口身份。
    return dict(window) if isinstance(window, Mapping) else {}  # 新增代码+BatchExecutor：返回窗口副本；如果没有这行代码，外部对象可能被 dispatch 修改。
# 新增代码+BatchExecutor：函数段结束，_batch_executor_current_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口读取范围。


def _batch_executor_critical_action(batch: ActionBatch, action: Mapping[str, Any]) -> bool:  # 新增代码+BatchExecutor：函数段开始，判断是否需要额外复核的关键动作；如果没有这段函数，保存等关键动作缺二次门禁。
    action_type = str(action.get("type", "") or "").lower()  # 新增代码+BatchExecutor：读取动作类型；如果没有这行代码，关键动作判断无输入。
    return bool(action.get("critical", False) or (batch.batch_kind == "file_save_batch" and action_type == "hotkey"))  # 新增代码+BatchExecutor：保存快捷键和显式关键动作需二次复核；如果没有这行代码，关键提交前可能不验目标。
# 新增代码+BatchExecutor：函数段结束，_batch_executor_critical_action 到此结束；如果没有这个边界说明，初学者不容易看出关键动作范围。


class UniversalActionBatchExecutor:  # 新增代码+BatchExecutor：类段开始，执行一个阶段内的批动作；如果没有这个类，阶段仍会逐 primitive 回到模型循环。
    def __init__(self, action_runtime: Any, max_low_level_events: int = 200) -> None:  # 修改代码+BatchEventLimit：函数段开始，注入现有 DSL runtime 和默认事件上限；如果没有这段函数，执行器会绕过已有 SendInput 和 target 门禁。
        self.action_runtime = action_runtime  # 新增代码+BatchExecutor：保存动作 runtime；如果没有这行代码，execute_batch 无法分发 primitive。
        self.max_low_level_events = max(1, _batch_executor_safe_int(max_low_level_events, 200))  # 新增代码+BatchEventLimit：保存默认低层事件上限；如果没有这行代码，异常大批无法被执行层截停。
    # 新增代码+BatchExecutor：函数段结束，UniversalActionBatchExecutor.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出依赖范围。

    def _verify_target(self, session: Mapping[str, Any]) -> dict[str, Any]:  # 新增代码+BatchExecutor：函数段开始，执行目标身份复核；如果没有这段函数，批前无法保证 target_ref 一对一。
        target_runtime = getattr(self.action_runtime, "target_runtime", None)  # 新增代码+BatchExecutor：读取底层目标 runtime；如果没有这行代码，执行器无法复用已有身份门禁。
        verifier = getattr(target_runtime, "verify_before_action", None)  # 新增代码+BatchExecutor：读取复核函数；如果没有这行代码，无法判断 runtime 是否支持复核。
        if callable(verifier):  # 新增代码+BatchExecutor：只有存在复核函数才调用；如果没有这行代码，缺 verifier 的 fake 或旧 runtime 会崩溃。
            return dict(verifier(dict(session), _batch_executor_current_window(session)))  # 新增代码+BatchExecutor：返回复核报告副本；如果没有这行代码，调用方拿不到 allowed 事实。
        return {"allowed": True, "target_identity_verified": True, "verifier_missing": True}  # 新增代码+BatchExecutor：无复核函数时保守记录缺口但不破坏旧测试；如果没有这行代码，兼容 runtime 无法执行。
    # 新增代码+BatchExecutor：函数段结束，UniversalActionBatchExecutor._verify_target 到此结束；如果没有这个边界说明，初学者不容易看出复核范围。

    def execute_batch(self, session: Mapping[str, Any], batch: ActionBatch) -> StageResult:  # 新增代码+BatchExecutor：函数段开始，执行一个通用动作批；如果没有这段函数，批模型无法真正落地。
        stage_id = _batch_executor_stage_id(batch)  # 新增代码+BatchExecutor：推导阶段 id；如果没有这行代码，结果无法关联计划。
        session_target_ref = str(session.get("target_ref", batch.target_ref) if isinstance(session, Mapping) else batch.target_ref)  # 新增代码+BatchExecutor：读取 session 目标引用；如果没有这行代码，批和 session 无法互相校验。
        if batch.target_ref and session_target_ref and batch.target_ref != session_target_ref:  # 新增代码+BatchExecutor：检查批目标和 session 目标一致；如果没有这行代码，跨窗口批可能误发。
            return StageResult(status="blocked", stage_id=stage_id, evidence={"decision": "target_ref_mismatch", "primitive_action_count": len(batch.actions), "successful_action_count": 0, "low_level_event_count": 0}, message="批目标引用与当前 session 不一致，已拒绝执行。")  # 新增代码+BatchExecutor：返回零动作阻断结果；如果没有这行代码，错误 target_ref 可能继续执行。
        verification = self._verify_target(session)  # 新增代码+BatchExecutor：执行批前目标复核；如果没有这行代码，批执行会绕过身份门禁。
        if not bool(verification.get("allowed", False)):  # 新增代码+BatchExecutor：检查目标复核是否放行；如果没有这行代码，漂移窗口仍可能收到输入。
            return StageResult(status="blocked", stage_id=stage_id, evidence={"decision": "target_identity_failed", "target_verification": verification, "primitive_action_count": len(batch.actions), "successful_action_count": 0, "low_level_event_count": 0}, message="目标窗口身份未通过批前复核。")  # 新增代码+BatchExecutor：返回零动作阻断结果；如果没有这行代码，漂移阻断没有结构化证据。
        event_limit = _batch_executor_event_limit(batch, self.max_low_level_events)  # 新增代码+BatchEventLimit：读取本批事件预算；如果没有这行代码，后续无法判断异常批是否超限。
        results: list[dict[str, Any]] = []  # 新增代码+BatchExecutor：初始化 primitive 结果列表；如果没有这行代码，阶段证据无法复盘每个动作。
        successful_count = 0  # 新增代码+BatchExecutor：初始化成功动作数；如果没有这行代码，部分失败无法统计。
        low_level_count = 0  # 新增代码+BatchExecutor：初始化底层事件数；如果没有这行代码，真实动作规模不可见。
        for action in batch.actions:  # 新增代码+BatchExecutor：逐个分发批内 primitive；如果没有这行代码，批不会执行任何动作。
            if _batch_executor_critical_action(batch, action):  # 新增代码+BatchExecutor：关键动作前二次复核；如果没有这行代码，保存等提交动作缺最后门禁。
                critical_verification = self._verify_target(session)  # 新增代码+BatchExecutor：执行关键动作复核；如果没有这行代码，目标漂移无法在提交前发现。
                if not bool(critical_verification.get("allowed", False)):  # 新增代码+BatchExecutor：检查关键复核是否放行；如果没有这行代码，漂移后仍可能保存到错误窗口。
                    return StageResult(status="blocked", stage_id=stage_id, evidence={"decision": "critical_target_identity_failed", "target_verification": critical_verification, "primitive_action_count": len(batch.actions), "successful_action_count": successful_count, "low_level_event_count": low_level_count, "action_results": results}, message="关键动作前目标身份复核失败。")  # 新增代码+BatchExecutor：返回阻断结果；如果没有这行代码，关键动作失败不可审计。
            dispatch_result = dict(self.action_runtime.dispatch(dict(session), dict(action), current_window=_batch_executor_current_window(session)))  # 新增代码+BatchExecutor：通过既有 DSL runtime 分发动作；如果没有这行代码，批执行会绕过目标复核和 sender。
            results.append(dispatch_result)  # 新增代码+BatchExecutor：保存动作结果；如果没有这行代码，失败无法定位到哪个 primitive。
            low_level_count += _batch_executor_safe_int(dispatch_result.get("low_level_event_count", 0))  # 新增代码+BatchExecutor：累计底层事件；如果没有这行代码，验收无法证明真实事件规模。
            if low_level_count > event_limit:  # 新增代码+BatchEventLimit：执行后立即检查是否超过事件预算；如果没有这行代码，异常 drag 或输入批会继续污染桌面。
                return StageResult(status="blocked", stage_id=stage_id, evidence={"decision": "batch_event_limit_exceeded", "batch_kind": batch.batch_kind, "target_ref": batch.target_ref, "target_verification": verification, "primitive_action_count": len(batch.actions), "successful_action_count": successful_count, "low_level_event_count": low_level_count, "max_low_level_events": event_limit, "action_results": results}, message="动作批超过低层事件预算，已停止剩余动作。")  # 新增代码+BatchEventLimit：返回超限阻断结果；如果没有这行代码，压力测试无法区分失败和无限执行。
            if not bool(dispatch_result.get("ok", False)):  # 新增代码+BatchExecutor：检查 primitive 是否失败；如果没有这行代码，后续动作会继续污染窗口。
                return StageResult(status="failed", stage_id=stage_id, evidence={"decision": str(dispatch_result.get("decision", "dispatch_failed")), "primitive_action_count": len(batch.actions), "successful_action_count": successful_count, "low_level_event_count": low_level_count, "action_results": results}, message="批内 primitive 执行失败，已停止剩余动作。")  # 新增代码+BatchExecutor：返回失败并停止剩余动作；如果没有这行代码，批失败后仍会继续。
            successful_count += 1  # 新增代码+BatchExecutor：成功动作数加一；如果没有这行代码，结果无法区分部分成功和全部成功。
        return StageResult(status="completed", stage_id=stage_id, evidence={"decision": "batch_completed", "batch_kind": batch.batch_kind, "target_ref": batch.target_ref, "target_verification": verification, "primitive_action_count": len(batch.actions), "successful_action_count": successful_count, "low_level_event_count": low_level_count, "action_results": results}, message="动作批已完成。")  # 新增代码+BatchExecutor：返回完成结果；如果没有这行代码，阶段循环拿不到成功证据。
    # 新增代码+BatchExecutor：函数段结束，UniversalActionBatchExecutor.execute_batch 到此结束；如果没有这个边界说明，初学者不容易看出批执行范围。
# 新增代码+BatchExecutor：类段结束，UniversalActionBatchExecutor 到此结束；如果没有这个边界说明，初学者不容易看出执行器范围。


__all__ = ["UniversalActionBatchExecutor"]  # 新增代码+BatchExecutor：声明公开接口；如果没有这行代码，通配导入会暴露内部 helper。
