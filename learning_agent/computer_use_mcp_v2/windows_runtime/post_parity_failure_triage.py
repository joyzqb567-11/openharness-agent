"""Post-parity Computer Use 失败分类。"""  # 新增代码+PostParityFailureTriage：说明本文件负责把失败证据分类成稳定原因；如果没有这一行，读者无法快速理解模块职责。
from __future__ import annotations  # 新增代码+PostParityFailureTriage：启用稳定的注解解析；如果没有这一行，后续类型注解在部分环境下可能更容易出兼容问题。

from typing import Any  # 新增代码+PostParityFailureTriage：导入动态证据类型；如果没有这一行，triage 函数无法清楚表达输入是动态 evidence 字典。


POST_PARITY_FAILURE_CATEGORIES = (  # 新增代码+PostParityFailureTriage：定义稳定失败分类集合；如果没有这一段，失败原因名字会漂移，无法做统计和复盘。
    "permission_or_policy_blocked",  # 新增代码+PostParityFailureTriage：权限或策略阻断分类；如果没有这一行，授权失败会和普通执行失败混在一起。
    "target_not_found",  # 新增代码+PostParityFailureTriage：目标未找到分类；如果没有这一行，窗口定位失败无法被明确记录。
    "target_drift",  # 新增代码+PostParityFailureTriage：目标漂移分类；如果没有这一行，动作落错窗口风险无法被明确记录。
    "observation_missing",  # 新增代码+PostParityFailureTriage：观察缺失分类；如果没有这一行，没看见屏幕就动作的风险不会被突出。
    "action_not_dispatched",  # 新增代码+PostParityFailureTriage：动作未派发分类；如果没有这一行，底层输入没发生会被误诊。
    "action_dispatched_but_no_state_change",  # 新增代码+PostParityFailureTriage：动作发生但状态未变分类；如果没有这一行，执行和验证之间的缺口无法被定位。
    "verifier_rejected",  # 新增代码+PostParityFailureTriage：verifier 拒绝分类；如果没有这一行，验收失败无法稳定记录。
    "cleanup_failed",  # 新增代码+PostParityFailureTriage：清理失败分类；如果没有这一行，环境污染风险不会进入失败统计。
    "visible_terminal_gate_failed",  # 新增代码+PostParityFailureTriage：真实可见终端门禁失败分类；如果没有这一行，规则十七失败无法被单独识别。
    "scenario_contract_invalid",  # 新增代码+PostParityFailureTriage：场景证据合同无效分类；如果没有这一行，未知证据结构可能被强行猜测根因。
)  # 新增代码+PostParityFailureTriage：结束分类元组；如果没有这一行，Python 元组语法不完整。


# 新增代码+PostParityFailureTriage：函数段开始，_triage_result 统一生成分类结果；如果没有这段函数，每个分支会重复写 category/reason/root_cause_confirmed。
def _triage_result(category: str, reason: str, confirmed: bool) -> dict[str, Any]:  # 新增代码+PostParityFailureTriage：声明结果构造函数；如果没有这一行，主函数无法复用稳定输出结构。
    return {  # 新增代码+PostParityFailureTriage：开始返回分类结果字典；如果没有这一行，函数没有输出对象。
        "category": category,  # 新增代码+PostParityFailureTriage：写入稳定分类名；如果没有这一行，调用方无法统计失败类型。
        "reason": reason,  # 新增代码+PostParityFailureTriage：写入人类可读原因；如果没有这一行，用户看不懂失败分类为什么成立。
        "root_cause_confirmed": bool(confirmed),  # 新增代码+PostParityFailureTriage：写入根因是否已确认；如果没有这一行，系统可能把猜测和事实混在一起。
    }  # 新增代码+PostParityFailureTriage：结束结果字典；如果没有这一行，Python 语法不完整。
# 新增代码+PostParityFailureTriage：函数段结束，_triage_result 到此结束；如果没有这个边界说明，初学者不容易看出结果构造范围。


# 新增代码+PostParityFailureTriage：函数段开始，triage_post_parity_failure 根据证据分类失败；如果没有这段函数，post-parity 失败复盘无法自动化。
def triage_post_parity_failure(evidence: dict[str, Any]) -> dict[str, Any]:  # 新增代码+PostParityFailureTriage：声明失败分类主函数；如果没有这一行，外部无法调用 triage 逻辑。
    if evidence.get("policy_blocked") is True:  # 新增代码+PostParityFailureTriage：优先检查权限或策略阻断；如果没有这一行，安全策略失败可能被误诊为执行失败。
        return _triage_result("permission_or_policy_blocked", "policy gate blocked the workflow", True)  # 新增代码+PostParityFailureTriage：返回已确认的策略阻断；如果没有这一行，权限失败没有稳定输出。
    if evidence.get("target_found") is False:  # 新增代码+PostParityFailureTriage：检查目标是否未找到；如果没有这一行，窗口定位失败无法分类。
        return _triage_result("target_not_found", "target window was not found", True)  # 新增代码+PostParityFailureTriage：返回已确认的目标未找到；如果没有这一行，目标缺失没有稳定输出。
    if evidence.get("target_drift") is True:  # 新增代码+PostParityFailureTriage：检查目标漂移；如果没有这一行，焦点漂移无法分类。
        return _triage_result("target_drift", "target identity drifted before action", True)  # 新增代码+PostParityFailureTriage：返回已确认的目标漂移；如果没有这一行，漂移失败没有稳定输出。
    if evidence.get("before_observation") is False:  # 新增代码+PostParityFailureTriage：检查动作前观察缺失；如果没有这一行，观察链路断裂无法分类。
        return _triage_result("observation_missing", "before observation is missing", True)  # 新增代码+PostParityFailureTriage：返回已确认的观察缺失；如果没有这一行，观察失败没有稳定输出。
    if evidence.get("physical_dispatch") is False:  # 新增代码+PostParityFailureTriage：检查真实物理派发是否缺失；如果没有这一行，SendInput 未发生无法分类。
        return _triage_result("action_not_dispatched", "physical dispatch did not happen", True)  # 新增代码+PostParityFailureTriage：返回已确认的动作未派发；如果没有这一行，动作失败没有稳定输出。
    if evidence.get("state_changed_after_action") is False:  # 新增代码+PostParityFailureTriage：检查动作后状态是否未变化；如果没有这一行，派发后无效果无法分类。
        return _triage_result(  # 新增代码+PostParityFailureTriage：开始返回动作无状态变化结果；如果没有这一行，多行返回结构不清晰。
            "action_dispatched_but_no_state_change",  # 新增代码+PostParityFailureTriage：写入动作已派发但状态未变分类；如果没有这一行，分类名缺失。
            "action dispatched but verifier saw no state change",  # 新增代码+PostParityFailureTriage：写入人类可读原因；如果没有这一行，用户不知道为什么归类。
            True,  # 新增代码+PostParityFailureTriage：声明该根因已由 evidence 确认；如果没有这一行，事实和猜测边界不清晰。
        )  # 新增代码+PostParityFailureTriage：结束动作无状态变化结果；如果没有这一行，函数调用语法不完整。
    if evidence.get("verifier_decision") == "rejected":  # 新增代码+PostParityFailureTriage：检查 verifier 是否拒绝；如果没有这一行，验收拒绝无法分类。
        return _triage_result("verifier_rejected", "verifier rejected the outcome", True)  # 新增代码+PostParityFailureTriage：返回已确认的 verifier 拒绝；如果没有这一行，验收失败没有稳定输出。
    if evidence.get("cleanup_completed") is False:  # 新增代码+PostParityFailureTriage：检查 cleanup 是否失败；如果没有这一行，清理失败无法分类。
        return _triage_result("cleanup_failed", "cleanup did not complete", True)  # 新增代码+PostParityFailureTriage：返回已确认的 cleanup 失败；如果没有这一行，环境污染风险无法稳定输出。
    if evidence.get("visible_terminal_e2e") is False:  # 新增代码+PostParityFailureTriage：检查真实可见终端门禁是否失败；如果没有这一行，规则十七失败无法分类。
        return _triage_result("visible_terminal_gate_failed", "visible terminal gate failed", True)  # 新增代码+PostParityFailureTriage：返回已确认的可见终端失败；如果没有这一行，最终门禁失败没有稳定输出。
    return _triage_result("scenario_contract_invalid", "evidence contract is incomplete", False)  # 新增代码+PostParityFailureTriage：未知结构只报合同无效且不确认根因；如果没有这一行，系统会把猜测当结论。
# 新增代码+PostParityFailureTriage：函数段结束，triage_post_parity_failure 到此结束；如果没有这个边界说明，初学者不容易看出失败分类主逻辑范围。
