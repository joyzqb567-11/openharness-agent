"""Post-parity Computer Use 真实工作流矩阵。"""  # 新增代码+PostParityWorkflowMatrix：说明本文件负责评估受控真实工作流覆盖；如果没有这一行，读者无法快速理解模块职责。
from __future__ import annotations  # 新增代码+PostParityWorkflowMatrix：启用稳定的注解解析；如果没有这一行，后续类型注解可能在部分环境下兼容性更差。

from typing import Any  # 新增代码+PostParityWorkflowMatrix：导入动态 evidence 类型；如果没有这一行，矩阵函数无法清楚表达输入是结构化动态数据。


SINGLE_APP_FAMILIES = {"local_text", "local_calculation", "local_file"}  # 新增代码+PostParityWorkflowMatrix：定义可算作单应用/基础本地任务的家族；如果没有这一行，矩阵无法判断 single-app 覆盖。


# 新增代码+PostParityWorkflowMatrix：函数段开始，_accepted_workflow 判断单条 workflow evidence 是否满足闭环合同；如果没有这段函数，矩阵会重复且容易漏掉安全字段。
def _accepted_workflow(item: dict[str, Any]) -> bool:  # 新增代码+PostParityWorkflowMatrix：声明单条 evidence 接收判断函数；如果没有这一行，调用方无法统一判断工作流是否有效。
    return (  # 新增代码+PostParityWorkflowMatrix：开始组合 accepted workflow 必要条件；如果没有这一行，闭环合同不够清晰。
        item.get("accepted") is True  # 新增代码+PostParityWorkflowMatrix：要求 verifier 接受工作流；如果没有这一行，失败样本也可能被计入覆盖。
        and item.get("before_observation") is True  # 新增代码+PostParityWorkflowMatrix：要求动作前观察存在；如果没有这一行，agent 没看见目标也可能通过。
        and item.get("after_observation") is True  # 新增代码+PostParityWorkflowMatrix：要求动作后观察存在；如果没有这一行，无法证明动作后状态。
        and item.get("target_identity_verified") is True  # 新增代码+PostParityWorkflowMatrix：要求目标身份已验证；如果没有这一行，动作落错窗口也可能通过。
        and item.get("physical_dispatch") is True  # 新增代码+PostParityWorkflowMatrix：要求真实物理派发；如果没有这一行，recording-only 路径可能冒充真实动作。
        and item.get("verifier_decision") == "accepted"  # 新增代码+PostParityWorkflowMatrix：要求 verifier 明确 accepted；如果没有这一行，模糊结论可能被误接收。
        and item.get("cleanup_completed") is True  # 新增代码+PostParityWorkflowMatrix：要求 cleanup 完成；如果没有这一行，污染用户环境的任务也可能通过。
        and item.get("ledger_entry_written") is True  # 新增代码+PostParityWorkflowMatrix：要求 ledger 记录已写入；如果没有这一行，证据无法长期追溯。
    )  # 新增代码+PostParityWorkflowMatrix：结束 accepted workflow 条件组合；如果没有这一行，Python 表达式语法不完整。
# 新增代码+PostParityWorkflowMatrix：函数段结束，_accepted_workflow 到此结束；如果没有这个边界说明，初学者不容易看出单条证据接收规则范围。


# 新增代码+PostParityWorkflowMatrix：函数段开始，evaluate_post_parity_workflow_matrix 评估三类真实工作流覆盖；如果没有这段函数，post-parity 无法证明复杂任务矩阵。
def evaluate_post_parity_workflow_matrix(workflow_evidence: list[dict[str, Any]] | None) -> dict[str, Any]:  # 新增代码+PostParityWorkflowMatrix：声明工作流矩阵评估函数；如果没有这一行，外部无法得到 workflow gate 报告。
    evidence = list(workflow_evidence or [])  # 新增代码+PostParityWorkflowMatrix：把输入规范成列表；如果没有这一行，None 输入会导致迭代异常。
    hard_fail_reasons: list[str] = []  # 新增代码+PostParityWorkflowMatrix：初始化失败原因列表；如果没有这一行，用户无法知道矩阵为什么失败。
    if any(item.get("cleanup_completed") is False for item in evidence):  # 新增代码+PostParityWorkflowMatrix：检查是否有工作流明确清理失败；如果没有这一行，cleanup 缺口不会被点名。
        hard_fail_reasons.append("workflow_cleanup_missing")  # 新增代码+PostParityWorkflowMatrix：记录 cleanup 缺失原因；如果没有这一行，失败排查不直观。
    if any(item.get("physical_dispatch") is False for item in evidence):  # 新增代码+PostParityWorkflowMatrix：检查是否有工作流明确未派发真实动作；如果没有这一行，假动作缺口不会被点名。
        hard_fail_reasons.append("workflow_dispatch_missing")  # 新增代码+PostParityWorkflowMatrix：记录真实派发缺失原因；如果没有这一行，失败排查不直观。
    accepted = [item for item in evidence if _accepted_workflow(item)]  # 新增代码+PostParityWorkflowMatrix：筛选完全合格的工作流证据；如果没有这一行，不完整样本也可能计入覆盖。
    single_app_workflow_gate = any(item.get("family") in SINGLE_APP_FAMILIES for item in accepted)  # 新增代码+PostParityWorkflowMatrix：计算单应用/基础本地任务覆盖；如果没有这一行，基础任务覆盖不可见。
    multi_app_workflow_gate = any(item.get("family") == "multi_app" for item in accepted)  # 新增代码+PostParityWorkflowMatrix：计算多应用覆盖；如果没有这一行，跨应用协调能力不可见。
    local_browser_workflow_gate = any(item.get("family") == "local_browser" for item in accepted)  # 新增代码+PostParityWorkflowMatrix：计算本地浏览器覆盖；如果没有这一行，浏览器桌面能力不可见。
    if not single_app_workflow_gate:  # 新增代码+PostParityWorkflowMatrix：检查单应用覆盖是否缺失；如果没有这一行，缺口不会写入失败原因。
        hard_fail_reasons.append("single_app_workflow_missing")  # 新增代码+PostParityWorkflowMatrix：记录单应用缺失；如果没有这一行，用户不知道还缺哪类样本。
    if not multi_app_workflow_gate:  # 新增代码+PostParityWorkflowMatrix：检查多应用覆盖是否缺失；如果没有这一行，缺口不会写入失败原因。
        hard_fail_reasons.append("multi_app_workflow_missing")  # 新增代码+PostParityWorkflowMatrix：记录多应用缺失；如果没有这一行，用户不知道还缺跨应用样本。
    if not local_browser_workflow_gate:  # 新增代码+PostParityWorkflowMatrix：检查本地浏览器覆盖是否缺失；如果没有这一行，缺口不会写入失败原因。
        hard_fail_reasons.append("local_browser_workflow_missing")  # 新增代码+PostParityWorkflowMatrix：记录本地浏览器缺失；如果没有这一行，用户不知道还缺浏览器样本。
    return {  # 新增代码+PostParityWorkflowMatrix：开始返回矩阵报告；如果没有这一行，调用方拿不到结构化结果。
        "passed": not hard_fail_reasons,  # 新增代码+PostParityWorkflowMatrix：只有没有失败原因才通过；如果没有这一行，矩阵无法输出总状态。
        "accepted_count": len(accepted),  # 新增代码+PostParityWorkflowMatrix：输出合格工作流数量；如果没有这一行，用户看不到覆盖规模。
        "single_app_workflow_gate": single_app_workflow_gate,  # 新增代码+PostParityWorkflowMatrix：输出单应用 gate；如果没有这一行，基础任务覆盖状态不可见。
        "multi_app_workflow_gate": multi_app_workflow_gate,  # 新增代码+PostParityWorkflowMatrix：输出多应用 gate；如果没有这一行，跨应用覆盖状态不可见。
        "local_browser_workflow_gate": local_browser_workflow_gate,  # 新增代码+PostParityWorkflowMatrix：输出本地浏览器 gate；如果没有这一行，浏览器覆盖状态不可见。
        "hard_fail_reasons": hard_fail_reasons,  # 新增代码+PostParityWorkflowMatrix：输出失败原因；如果没有这一行，后续 agent 不知道下一步补哪里。
    }  # 新增代码+PostParityWorkflowMatrix：结束矩阵报告；如果没有这一行，Python 字典语法不完整。
# 新增代码+PostParityWorkflowMatrix：函数段结束，evaluate_post_parity_workflow_matrix 到此结束；如果没有这个边界说明，初学者不容易看出工作流矩阵范围。
