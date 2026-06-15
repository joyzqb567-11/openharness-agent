"""Computer Use post-parity 顶层治理矩阵。"""  # 新增代码+PostParityBaseline：说明本文件负责 post-parity 新阶段的最高层门禁；如果没有这一行，读者无法一眼看出模块职责。
from __future__ import annotations  # 新增代码+PostParityBaseline：启用延迟注解解析，减少类型注解在不同 Python 版本下的兼容风险；如果没有这一行，后续更复杂类型可能更容易触发解析问题。

import argparse  # 新增代码+PostParityFinalGate：导入命令行参数解析器；如果没有这行代码，真实终端无法用 --evidence-file 明确传入最终证据。
import json  # 新增代码+PostParityFinalGate：导入 JSON 解析器；如果没有这行代码，最终 CLI 无法读取结构化证据文件和事件日志。
import os  # 新增代码+PostParityFinalGate：导入环境变量读取能力；如果没有这行代码，CLI 无法从验收控制器环境读取真实终端事件日志路径。
from pathlib import Path  # 新增代码+PostParityFinalGate：导入跨平台路径对象；如果没有这行代码，证据文件和事件日志路径处理会更容易出错。
from typing import Any  # 新增代码+PostParityBaseline：导入动态报告字段类型；如果没有这一行，矩阵函数无法清楚表达 evidence/report 是结构化动态数据。

from learning_agent.computer_use_mcp_v2.windows_runtime.post_parity_workflow_matrix import evaluate_post_parity_workflow_matrix  # 新增代码+PostParityWorkflowMatrix：导入真实工作流矩阵评估函数；如果没有这一行，post-parity 总矩阵不能直接消费 workflow evidence 列表。


POST_PARITY_MARKER = "COMPUTER_USE_POST_PARITY_READY"  # 新增代码+PostParityBaseline：定义 post-parity 矩阵稳定 marker；如果没有这一行，真实终端和测试无法用固定锚点识别新阶段结果。
TOP_LEVEL_PARITY_MARKER = "COMPUTER_USE_TOP_LEVEL_GOVERNANCE_READY"  # 新增代码+PostParityBaseline：定义旧 parity 顶层矩阵 marker；如果没有这一行，新矩阵无法确认自己站在已通过的旧地基上。


# 新增代码+PostParityBaseline：函数段开始，_post_parity_safe_dict 负责把动态 evidence 安全整理成字典；如果没有这段函数，坏输入可能让矩阵异常中断而不是诚实失败。
def _post_parity_safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+PostParityBaseline：声明动态值转字典函数；如果没有这一行，每个门禁都要重复写 isinstance 判断。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+PostParityBaseline：只有字典输入才复制返回，否则给空字典；如果没有这一行，字符串或列表可能污染矩阵判断。
# 新增代码+PostParityBaseline：函数段结束，_post_parity_safe_dict 到此结束；如果没有这个边界说明，初学者不容易看出动态输入清洗范围。


# 新增代码+PostParityBaseline：函数段开始，_post_parity_bool_gate 负责读取子证据的 passed 字段；如果没有这段函数，多个 gate 的 bool 规则会分散且容易不一致。
def _post_parity_bool_gate(evidence: Any) -> bool:  # 新增代码+PostParityBaseline：声明通用 gate 判断函数；如果没有这一行，调用方无法统一判断子证据是否通过。
    evidence_dict = _post_parity_safe_dict(evidence)  # 新增代码+PostParityBaseline：先把输入清洗为字典；如果没有这一行，非字典输入会在 get 调用时出错。
    return evidence_dict.get("passed") is True  # 新增代码+PostParityBaseline：只有明确 `passed is True` 才通过；如果没有这一行，字符串 true 或其它真值可能造成假阳性。
# 新增代码+PostParityBaseline：函数段结束，_post_parity_bool_gate 到此结束；如果没有这个边界说明，初学者不容易看出通用 gate 规则范围。


# 新增代码+PostParityWorkflowMatrix：函数段开始，_post_parity_workflow_gate_report 统一整理 workflow matrix evidence；如果没有这段函数，治理矩阵只能接收预先汇总好的 dict，不能直接消费工作流 evidence 列表。
def _post_parity_workflow_gate_report(evidence: Any) -> dict[str, Any]:  # 新增代码+PostParityWorkflowMatrix：声明 workflow evidence 规范化函数；如果没有这一行，主矩阵无法复用列表/字典双输入逻辑。
    if isinstance(evidence, list):  # 新增代码+PostParityWorkflowMatrix：如果输入是 workflow evidence 列表；如果没有这一行，Phase144 的列表接入测试无法通过。
        return evaluate_post_parity_workflow_matrix(evidence)  # 新增代码+PostParityWorkflowMatrix：调用真实工作流矩阵评估；如果没有这一行，列表不会被转换成 gate report。
    if isinstance(evidence, dict):  # 新增代码+PostParityWorkflowMatrix：如果输入已经是汇总报告；如果没有这一行，后续 final gate 无法直接传入预计算矩阵结果。
        return evidence  # 新增代码+PostParityWorkflowMatrix：原样返回汇总报告；如果没有这一行，dict evidence 会被误判缺失。
    return {"passed": False, "hard_fail_reasons": ["workflow_matrix_missing"]}  # 新增代码+PostParityWorkflowMatrix：缺失或坏类型时返回失败报告；如果没有这一行，坏输入可能被当成空通过。
# 新增代码+PostParityWorkflowMatrix：函数段结束，_post_parity_workflow_gate_report 到此结束；如果没有这个边界说明，初学者不容易看出 workflow evidence 规范化范围。


# 新增代码+PostParityBaseline：函数段开始，_is_prior_parity_floor_valid 判断旧顶层治理证据是否足够可信；如果没有这段函数，新阶段可能脱离已通过的 parity 地基。
def _is_prior_parity_floor_valid(evidence: Any) -> bool:  # 新增代码+PostParityBaseline：声明旧 parity floor 校验函数；如果没有这一行，post-parity 主函数无法复用这项安全判断。
    evidence_dict = _post_parity_safe_dict(evidence)  # 新增代码+PostParityBaseline：清洗旧证据输入；如果没有这一行，坏证据结构会让矩阵崩溃。
    return (  # 新增代码+PostParityBaseline：开始组合旧 parity floor 的三项必要条件；如果没有这一行，判断逻辑不够清晰。
        evidence_dict.get("passed") is True  # 新增代码+PostParityBaseline：要求旧顶层矩阵总结果已经通过；如果没有这一行，失败的旧矩阵也可能被当作地基。
        and evidence_dict.get("marker") == TOP_LEVEL_PARITY_MARKER  # 新增代码+PostParityBaseline：要求旧证据 marker 精确匹配；如果没有这一行，任意 passed 报告都可能冒充旧顶层治理。
        and evidence_dict.get("visible_terminal_e2e_gate") is True  # 新增代码+PostParityBaseline：要求旧阶段真实可见终端门禁通过；如果没有这一行，规则十七的旧地基可能被绕过。
    )  # 新增代码+PostParityBaseline：结束旧 parity floor 条件组合；如果没有这一行，Python 表达式语法不完整。
# 新增代码+PostParityBaseline：函数段结束，_is_prior_parity_floor_valid 到此结束；如果没有这个边界说明，初学者不容易看出旧地基校验范围。


# 新增代码+PostParityBaseline：函数段开始，_append_missing_gate_reason 根据 gate 状态写入失败原因；如果没有这段函数，失败原因列表会散落重复逻辑。
def _append_missing_gate_reason(hard_fail_reasons: list[str], gate_passed: bool, reason: str) -> None:  # 新增代码+PostParityBaseline：声明失败原因追加函数；如果没有这一行，主函数要重复写 if 判断。
    if not gate_passed:  # 新增代码+PostParityBaseline：只有 gate 未通过时才记录原因；如果没有这一行，通过的 gate 也会误写失败原因。
        hard_fail_reasons.append(reason)  # 新增代码+PostParityBaseline：把失败原因追加到列表；如果没有这一行，用户无法知道矩阵为什么没通过。
# 新增代码+PostParityBaseline：函数段结束，_append_missing_gate_reason 到此结束；如果没有这个边界说明，初学者不容易看出失败原因写入范围。


# 新增代码+PostParityBaseline：函数段开始，run_computer_use_post_parity_governance_matrix 运行 post-parity 新顶层矩阵；如果没有这段函数，测试、CLI 和后续验收都没有统一入口。
def run_computer_use_post_parity_governance_matrix(  # 新增代码+PostParityBaseline：声明 post-parity 矩阵主函数；如果没有这一行，外部无法触发新阶段治理判断。
    *,  # 新增代码+PostParityBaseline：要求所有 evidence 参数必须用关键字传入；如果没有这一行，调用方容易因为参数顺序写错导致门禁误判。
    top_level_parity_evidence: dict[str, Any] | None = None,  # 新增代码+PostParityBaseline：接收旧 parity 顶层证据；如果没有这一行，新矩阵无法确认旧地基是否通过。
    workflow_matrix_evidence: dict[str, Any] | None = None,  # 新增代码+PostParityBaseline：接收真实工作流矩阵证据；如果没有这一行，post-parity 无法验证复杂任务覆盖。
    ledger_evidence: dict[str, Any] | None = None,  # 新增代码+PostParityBaseline：接收 evidence ledger 证据；如果没有这一行，结构化证据账本不会影响最终结果。
    triage_evidence: dict[str, Any] | None = None,  # 新增代码+PostParityBaseline：接收 failure triage 证据；如果没有这一行，失败分类能力不会进入治理矩阵。
    self_improvement_evidence: dict[str, Any] | None = None,  # 新增代码+PostParityBaseline：接收自我改进 dry-run 证据；如果没有这一行，自我改进能力不会被门禁约束。
    visible_terminal_evidence: dict[str, Any] | None = None,  # 新增代码+PostParityBaseline：接收最终真实可见终端证据；如果没有这一行，规则十七无法进入 post-parity 最终门禁。
) -> dict[str, Any]:  # 新增代码+PostParityBaseline：声明返回结构化报告；如果没有这一行，调用方无法通过类型提示知道会拿到字典报告。
    parity_floor_gate = _is_prior_parity_floor_valid(top_level_parity_evidence)  # 新增代码+PostParityBaseline：计算旧 parity 地基门禁；如果没有这一行，新阶段可能绕过已证明的成熟底线。
    workflow_matrix_report = _post_parity_workflow_gate_report(workflow_matrix_evidence)  # 新增代码+PostParityWorkflowMatrix：把 workflow evidence 列表或报告统一成矩阵报告；如果没有这一行，总矩阵不能消费 Phase144 证据。
    real_world_workflow_matrix = _post_parity_bool_gate(workflow_matrix_report)  # 修改代码+PostParityWorkflowMatrix：用规范化后的 workflow report 计算门禁；如果没有这一行，列表形式工作流证据不会让 gate 变 true。
    evidence_ledger_gate = _post_parity_bool_gate(ledger_evidence)  # 新增代码+PostParityBaseline：计算证据账本门禁；如果没有这一行，结构化证据保存能力不会被检查。
    failure_triage_gate = _post_parity_bool_gate(triage_evidence)  # 新增代码+PostParityBaseline：计算失败分类门禁；如果没有这一行，失败复盘能力不会被检查。
    self_improvement_dry_run_gate = _post_parity_bool_gate(self_improvement_evidence)  # 新增代码+PostParityBaseline：计算安全自我改进 dry-run 门禁；如果没有这一行，自我改进提案能力不会被检查。
    visible_terminal_e2e_gate = _post_parity_bool_gate(visible_terminal_evidence)  # 新增代码+PostParityBaseline：计算真实可见终端最终门禁；如果没有这一行，post-parity 可能被自动化测试单独假通过。
    hard_fail_reasons: list[str] = []  # 新增代码+PostParityBaseline：初始化失败原因列表；如果没有这一行，用户无法看到每个未完成 gate 的原因。
    _append_missing_gate_reason(hard_fail_reasons, parity_floor_gate, "top_level_parity_evidence_missing")  # 新增代码+PostParityBaseline：记录旧 parity 地基缺失；如果没有这一行，缺少前置成熟证据时原因不明确。
    _append_missing_gate_reason(hard_fail_reasons, real_world_workflow_matrix, "real_world_workflow_matrix_missing")  # 新增代码+PostParityBaseline：记录真实工作流矩阵缺失；如果没有这一行，下一步缺口不清楚。
    _append_missing_gate_reason(hard_fail_reasons, evidence_ledger_gate, "evidence_ledger_missing")  # 新增代码+PostParityBaseline：记录证据账本缺失；如果没有这一行，ledger 阶段缺口不会暴露。
    _append_missing_gate_reason(hard_fail_reasons, failure_triage_gate, "failure_triage_missing")  # 新增代码+PostParityBaseline：记录失败分类缺失；如果没有这一行，triage 阶段缺口不会暴露。
    _append_missing_gate_reason(hard_fail_reasons, self_improvement_dry_run_gate, "self_improvement_dry_run_missing")  # 新增代码+PostParityBaseline：记录自我改进 dry-run 缺失；如果没有这一行，自我进化闭环缺口不会暴露。
    _append_missing_gate_reason(hard_fail_reasons, visible_terminal_e2e_gate, "visible_terminal_e2e_missing")  # 新增代码+PostParityBaseline：记录最终可见终端缺失；如果没有这一行，规则十七缺口不会暴露。
    passed = not hard_fail_reasons  # 新增代码+PostParityBaseline：只有没有任何失败原因才总通过；如果没有这一行，矩阵无法给出总结果。
    return {  # 新增代码+PostParityBaseline：开始返回完整矩阵报告；如果没有这一行，调用方拿不到结构化结果。
        "marker": POST_PARITY_MARKER,  # 新增代码+PostParityBaseline：输出稳定 post-parity marker；如果没有这一行，真实终端和测试无法识别本矩阵。
        "passed": passed,  # 新增代码+PostParityBaseline：输出总通过状态；如果没有这一行，最终验收无法判断是否完成。
        "parity_floor_gate": parity_floor_gate,  # 新增代码+PostParityBaseline：输出旧 parity 地基门禁；如果没有这一行，用户看不出是否站在已完成的旧顶层治理上。
        "real_world_workflow_matrix": real_world_workflow_matrix,  # 新增代码+PostParityBaseline：输出真实工作流矩阵门禁；如果没有这一行，复杂任务覆盖状态不可见。
        "evidence_ledger_gate": evidence_ledger_gate,  # 新增代码+PostParityBaseline：输出证据账本门禁；如果没有这一行，结构化 evidence 能力不可见。
        "failure_triage_gate": failure_triage_gate,  # 新增代码+PostParityBaseline：输出失败分类门禁；如果没有这一行，排障能力状态不可见。
        "self_improvement_dry_run_gate": self_improvement_dry_run_gate,  # 新增代码+PostParityBaseline：输出自我改进 dry-run 门禁；如果没有这一行，自我开发闭环状态不可见。
        "visible_terminal_e2e_gate": visible_terminal_e2e_gate,  # 新增代码+PostParityBaseline：输出最终真实可见终端门禁；如果没有这一行，规则十七无法被矩阵消费者读取。
        "hard_fail_reasons": hard_fail_reasons,  # 新增代码+PostParityBaseline：输出所有失败原因；如果没有这一行，用户和后续 agent 无法知道下一步该做什么。
        "reports": {"workflow_matrix": workflow_matrix_report},  # 新增代码+PostParityWorkflowMatrix：挂载 workflow matrix 子报告；如果没有这一行，workflow gate 失败时无法审计具体原因。
    }  # 新增代码+PostParityBaseline：结束完整矩阵报告；如果没有这一行，Python 字典语法不完整。
# 新增代码+PostParityBaseline：函数段结束，run_computer_use_post_parity_governance_matrix 到此结束；如果没有这个边界说明，初学者不容易看出矩阵主入口范围。

FINAL_VISIBLE_TERMINAL_REQUIRED_STATES = (  # 新增代码+PostParityFinalGate：定义最终 CLI 运行时必须已经出现的真实终端事件；如果没有这段常量，visible terminal gate 没有稳定验收标准。
    "agent_ready_for_user_prompt",  # 新增代码+PostParityFinalGate：要求 agent 真实启动并准备接收用户 prompt；如果没有这行代码，旧日志或未启动窗口可能误过。
    "user_prompt_received",  # 新增代码+PostParityFinalGate：要求真实终端确实收到当前测试 prompt；如果没有这行代码，CLI 在非交互环境里也可能冒充通过。
)  # 新增代码+PostParityFinalGate：结束必需状态元组；如果没有这行代码，Python 语法不完整。

# 新增代码+PostParityFinalGate：函数段开始，_post_parity_bool_text 把布尔值转成小写 token；如果没有这段函数，最终 summary line 可能出现 True/False 导致验收不稳定。
def _post_parity_bool_text(value: Any) -> str:  # 新增代码+PostParityFinalGate：声明布尔 token 转换函数；如果没有这行代码，summary line 每个字段都要重复写转换。
    return "true" if value is True else "false"  # 新增代码+PostParityFinalGate：只有明确 True 才输出 true；如果没有这行代码，字符串 true 或非空对象可能被误判。
# 新增代码+PostParityFinalGate：函数段结束，_post_parity_bool_text 到此结束；如果没有这个边界说明，初学者不容易看出 token 规则范围。

# 新增代码+PostParityFinalGate：函数段开始，_post_parity_failure 返回统一失败证据；如果没有这段函数，事件日志失败分支会重复且格式不一致。
def _post_parity_failure(reason: str, **extra: Any) -> dict[str, Any]:  # 新增代码+PostParityFinalGate：声明失败证据构造函数；如果没有这行代码，调用方无法稳定拿到 hard_fail_reasons。
    report = {"passed": False, "hard_fail_reasons": [reason]}  # 新增代码+PostParityFinalGate：创建基础失败报告；如果没有这行代码，失败时没有统一字段。
    report.update(extra)  # 新增代码+PostParityFinalGate：补充事件日志路径、状态等审计信息；如果没有这行代码，失败证据缺少定位线索。
    return report  # 新增代码+PostParityFinalGate：返回失败报告；如果没有这行代码，调用方拿不到失败对象。
# 新增代码+PostParityFinalGate：函数段结束，_post_parity_failure 到此结束；如果没有这个边界说明，初学者不容易看出失败报告构造范围。

# 新增代码+PostParityFinalGate：函数段开始，load_post_parity_evidence_file 读取最终证据 JSON；如果没有这段函数，CLI 无法消费 Phase140-146 的汇总证据。
def load_post_parity_evidence_file(evidence_file_path: str) -> dict[str, Any]:  # 新增代码+PostParityFinalGate：声明证据文件读取函数；如果没有这行代码，main 需要直接写文件解析细节。
    path = Path(evidence_file_path)  # 新增代码+PostParityFinalGate：把字符串路径转成 Path；如果没有这行代码，后续 exists/read_text 调用不稳定。
    if not path.exists():  # 新增代码+PostParityFinalGate：检查证据文件是否存在；如果没有这行代码，缺文件会变成低层异常而不是清晰失败。
        return {"__load_error__": f"evidence_file_missing:{path}"}  # 新增代码+PostParityFinalGate：返回可审计缺文件错误；如果没有这行代码，最终 CLI 失败原因不清楚。
    try:  # 新增代码+PostParityFinalGate：开始 JSON 解析保护；如果没有这行代码，坏 JSON 会让真实终端直接崩溃。
        payload = json.loads(path.read_text(encoding="utf-8"))  # 新增代码+PostParityFinalGate：读取并解析 UTF-8 JSON；如果没有这行代码，最终证据无法进入治理矩阵。
    except json.JSONDecodeError as error:  # 新增代码+PostParityFinalGate：捕获 JSON 格式错误；如果没有这行代码，坏证据文件不会形成可读失败报告。
        return {"__load_error__": f"evidence_file_invalid_json:{error}"}  # 新增代码+PostParityFinalGate：返回 JSON 解析错误；如果没有这行代码，用户不知道证据文件哪里坏了。
    return payload if isinstance(payload, dict) else {"__load_error__": "evidence_file_not_object"}  # 新增代码+PostParityFinalGate：只接受顶层对象；如果没有这行代码，数组或字符串证据可能污染矩阵。
# 新增代码+PostParityFinalGate：函数段结束，load_post_parity_evidence_file 到此结束；如果没有这个边界说明，初学者不容易看出证据文件读取范围。

# 新增代码+PostParityFinalGate：函数段开始，build_post_parity_visible_terminal_evidence 从事件日志生成真实终端证据；如果没有这段函数，最终 gate 只能依赖静态 JSON 假证据。
def build_post_parity_visible_terminal_evidence(event_log_path: str | None) -> dict[str, Any]:  # 新增代码+PostParityFinalGate：声明真实终端事件日志复验函数；如果没有这行代码，CLI 无法证明自己运行在 acceptance controller 启动的窗口中。
    if not event_log_path:  # 新增代码+PostParityFinalGate：检查事件日志路径是否为空；如果没有这行代码，缺少真实终端上下文会被忽略。
        return _post_parity_failure("visible_terminal_event_log_missing")  # 新增代码+PostParityFinalGate：缺路径直接失败；如果没有这行代码，非真实终端运行也可能通过。
    path = Path(event_log_path)  # 新增代码+PostParityFinalGate：把事件日志路径转成 Path；如果没有这行代码，文件存在性和读取不方便。
    if not path.exists():  # 新增代码+PostParityFinalGate：检查事件日志文件是否存在；如果没有这行代码，错误路径会导致低层异常。
        return _post_parity_failure("visible_terminal_event_log_missing", event_log=str(path))  # 新增代码+PostParityFinalGate：返回缺事件日志失败；如果没有这行代码，用户无法定位日志路径。
    states: list[str] = []  # 新增代码+PostParityFinalGate：准备收集事件状态；如果没有这行代码，后续无法判断 required states。
    invalid_line_count = 0  # 新增代码+PostParityFinalGate：准备统计坏 JSONL 行；如果没有这行代码，损坏事件日志可能被忽略。
    for line in path.read_text(encoding="utf-8").splitlines():  # 新增代码+PostParityFinalGate：逐行读取事件日志；如果没有这行代码，JSONL 事件无法被复验。
        if not line.strip():  # 新增代码+PostParityFinalGate：跳过空行；如果没有这行代码，空行会被当成坏 JSON。
            continue  # 新增代码+PostParityFinalGate：继续下一行；如果没有这行代码，空行仍会进入解析逻辑。
        try:  # 新增代码+PostParityFinalGate：保护单行 JSON 解析；如果没有这行代码，一行损坏会让整个 CLI 崩溃。
            event = json.loads(line)  # 新增代码+PostParityFinalGate：解析单行事件；如果没有这行代码，无法读取 state 字段。
        except json.JSONDecodeError:  # 新增代码+PostParityFinalGate：捕获坏 JSONL 行；如果没有这行代码，坏日志不会变成结构化失败。
            invalid_line_count += 1  # 新增代码+PostParityFinalGate：累计坏行数量；如果没有这行代码，日志完整性不可审计。
            continue  # 新增代码+PostParityFinalGate：继续读取后续行；如果没有这行代码，一个坏行会阻止收集其他证据。
        state = str(_post_parity_safe_dict(event).get("state", ""))  # 新增代码+PostParityFinalGate：安全读取 state 字段；如果没有这行代码，坏事件对象会导致异常。
        if state:  # 新增代码+PostParityFinalGate：只记录非空状态；如果没有这行代码，空状态会污染状态列表。
            states.append(state)  # 新增代码+PostParityFinalGate：加入状态列表；如果没有这行代码，required states 永远无法通过。
    missing_states = [state for state in FINAL_VISIBLE_TERMINAL_REQUIRED_STATES if state not in states]  # 新增代码+PostParityFinalGate：计算缺失的真实终端状态；如果没有这行代码，窗口启动和 prompt 接收无法复验。
    if invalid_line_count:  # 新增代码+PostParityFinalGate：检查是否存在坏 JSONL 行；如果没有这行代码，损坏日志可能仍然通过。
        return _post_parity_failure("visible_terminal_event_log_invalid", event_log=str(path), states=states, invalid_line_count=invalid_line_count)  # 新增代码+PostParityFinalGate：坏日志直接失败并返回审计信息；如果没有这行代码，日志质量无门禁。
    if missing_states:  # 新增代码+PostParityFinalGate：检查必需状态是否缺失；如果没有这行代码，不完整真实终端流程也会通过。
        return _post_parity_failure("visible_terminal_required_states_missing", event_log=str(path), states=states, missing_states=missing_states)  # 新增代码+PostParityFinalGate：缺状态直接失败；如果没有这行代码，验收无法定位缺哪个状态。
    return {"passed": True, "event_log": str(path), "states": states, "hard_fail_reasons": []}  # 新增代码+PostParityFinalGate：返回通过的真实终端证据；如果没有这行代码，最终 gate 无法变成 true。
# 新增代码+PostParityFinalGate：函数段结束，build_post_parity_visible_terminal_evidence 到此结束；如果没有这个边界说明，初学者不容易看出事件日志复验范围。

# 新增代码+PostParityFinalGate：函数段开始，build_post_parity_report_from_file 把文件证据和事件日志装配成最终矩阵报告；如果没有这段函数，main 会把装配逻辑写散。
def build_post_parity_report_from_file(evidence_file_path: str, visible_terminal_event_log_path: str | None = None) -> dict[str, Any]:  # 新增代码+PostParityFinalGate：声明最终报告装配函数；如果没有这行代码，测试和 CLI 不能复用同一逻辑。
    evidence = load_post_parity_evidence_file(evidence_file_path)  # 新增代码+PostParityFinalGate：读取最终证据文件；如果没有这行代码，Phase140-146 的证据不会进入最终矩阵。
    if "__load_error__" in evidence:  # 新增代码+PostParityFinalGate：检查证据文件读取错误；如果没有这行代码，缺文件或坏 JSON 会被当成普通证据。
        return run_computer_use_post_parity_governance_matrix(visible_terminal_evidence=_post_parity_failure(str(evidence["__load_error__"])))  # 新增代码+PostParityFinalGate：返回失败矩阵报告；如果没有这行代码，CLI 无法用统一 summary line 暴露证据文件错误。
    event_log_path = visible_terminal_event_log_path or os.environ.get("LEARNING_AGENT_ACCEPTANCE_EVENT_LOG")  # 新增代码+PostParityFinalGate：优先使用参数，其次使用验收控制器环境变量；如果没有这行代码，真实终端场景需要硬编码日志路径。
    visible_terminal_evidence = build_post_parity_visible_terminal_evidence(event_log_path)  # 新增代码+PostParityFinalGate：从当前事件日志构造真实终端证据；如果没有这行代码，final gate 可能被静态 JSON 冒充。
    return run_computer_use_post_parity_governance_matrix(  # 新增代码+PostParityFinalGate：把全部证据交给治理矩阵；如果没有这行代码，CLI 不会得到最终报告。
        top_level_parity_evidence=_post_parity_safe_dict(evidence.get("top_level_parity_evidence")),  # 新增代码+PostParityFinalGate：传入旧 parity 地基证据；如果没有这行代码，parity_floor_gate 会失败。
        workflow_matrix_evidence=evidence.get("workflow_matrix_evidence"),  # 新增代码+PostParityFinalGate：传入真实工作流矩阵证据；如果没有这行代码，real_world_workflow_matrix 会失败。
        ledger_evidence=_post_parity_safe_dict(evidence.get("ledger_evidence")),  # 新增代码+PostParityFinalGate：传入证据账本证据；如果没有这行代码，evidence_ledger_gate 会失败。
        triage_evidence=_post_parity_safe_dict(evidence.get("triage_evidence")),  # 新增代码+PostParityFinalGate：传入失败分诊证据；如果没有这行代码，failure_triage_gate 会失败。
        self_improvement_evidence=_post_parity_safe_dict(evidence.get("self_improvement_evidence")),  # 新增代码+PostParityFinalGate：传入自我改进 dry-run 证据；如果没有这行代码，self_improvement_dry_run_gate 会失败。
        visible_terminal_evidence=visible_terminal_evidence,  # 新增代码+PostParityFinalGate：传入从当前事件日志计算出的真实终端证据；如果没有这行代码，visible_terminal_e2e_gate 会失败。
    )  # 新增代码+PostParityFinalGate：结束治理矩阵调用；如果没有这行代码，Python 语法不完整。
# 新增代码+PostParityFinalGate：函数段结束，build_post_parity_report_from_file 到此结束；如果没有这个边界说明，初学者不容易看出最终证据装配范围。

# 新增代码+PostParityFinalGate：函数段开始，format_post_parity_summary_line 生成最终可见终端稳定单行 token；如果没有这段函数，debug log 和最终回答无法用同一行证明结果。
def format_post_parity_summary_line(report: dict[str, Any]) -> str:  # 新增代码+PostParityFinalGate：声明 summary line 格式化函数；如果没有这行代码，测试和 CLI 没有稳定输出入口。
    return (  # 新增代码+PostParityFinalGate：开始拼接固定顺序 summary line；如果没有这行代码，返回表达式不完整。
        f"{POST_PARITY_MARKER} passed={_post_parity_bool_text(report.get('passed'))} "  # 新增代码+PostParityFinalGate：输出 marker 和总通过状态；如果没有这行代码，最终验收缺少主锚点。
        f"real_world_workflow_matrix={_post_parity_bool_text(report.get('real_world_workflow_matrix'))} "  # 新增代码+PostParityFinalGate：输出真实工作流矩阵状态；如果没有这行代码，复杂场景成熟度不可见。
        f"evidence_ledger_gate={_post_parity_bool_text(report.get('evidence_ledger_gate'))} "  # 新增代码+PostParityFinalGate：输出证据账本状态；如果没有这行代码，证据链成熟度不可见。
        f"failure_triage_gate={_post_parity_bool_text(report.get('failure_triage_gate'))} "  # 新增代码+PostParityFinalGate：输出失败分诊状态；如果没有这行代码，排障成熟度不可见。
        f"self_improvement_dry_run_gate={_post_parity_bool_text(report.get('self_improvement_dry_run_gate'))} "  # 新增代码+PostParityFinalGate：输出自我改进 dry-run 状态；如果没有这行代码，自我开发闭环状态不可见。
        f"visible_terminal_e2e_gate={_post_parity_bool_text(report.get('visible_terminal_e2e_gate'))}"  # 新增代码+PostParityFinalGate：输出最终真实可见终端状态；如果没有这行代码，规则十七无法进入最终 token。
    )  # 新增代码+PostParityFinalGate：结束 summary line 拼接；如果没有这行代码，Python 表达式不完整。
# 新增代码+PostParityFinalGate：函数段结束，format_post_parity_summary_line 到此结束；如果没有这个边界说明，初学者不容易看出最终 token 范围。

# 新增代码+PostParityFinalGate：函数段开始，main 提供真实终端可直接运行的 CLI；如果没有这段函数，acceptance controller 无法要求 agent 执行最终矩阵命令。
def main(argv: list[str] | None = None) -> int:  # 新增代码+PostParityFinalGate：声明 CLI 入口并支持测试传参；如果没有这行代码，python -m 模块没有可控主流程。
    parser = argparse.ArgumentParser(description="Run Computer Use post-parity final governance matrix.")  # 新增代码+PostParityFinalGate：创建参数解析器；如果没有这行代码，CLI 参数错误不会有清晰提示。
    parser.add_argument("--evidence-file", required=True)  # 新增代码+PostParityFinalGate：要求传入最终证据文件；如果没有这行代码，CLI 可能在没有 Phase140-146 证据时假运行。
    parser.add_argument("--visible-terminal-event-log", default=None)  # 新增代码+PostParityFinalGate：允许显式传入当前真实终端事件日志；如果没有这行代码，最终场景只能依赖环境变量。
    args = parser.parse_args(argv)  # 新增代码+PostParityFinalGate：解析参数；如果没有这行代码，CLI 不知道用户传了什么。
    report = build_post_parity_report_from_file(args.evidence_file, args.visible_terminal_event_log)  # 新增代码+PostParityFinalGate：从证据文件和事件日志构建最终报告；如果没有这行代码，main 没有判断依据。
    print(format_post_parity_summary_line(report))  # 新增代码+PostParityFinalGate：打印验收器和最终回答都能复制的稳定 summary line；如果没有这行代码，debug log 无法证明门禁结果。
    return 0 if report.get("passed") is True else 1  # 新增代码+PostParityFinalGate：通过返回 0，失败返回 1；如果没有这行代码，真实终端命令无法用退出码表达结果。
# 新增代码+PostParityFinalGate：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 主流程范围。

if __name__ == "__main__":  # 新增代码+PostParityFinalGate：模块入口段开始，允许 `python -m learning_agent.computer_use_mcp_v2.windows_runtime.post_parity_governance_matrix` 直接运行；如果没有这行代码，真实终端无法直接启动最终矩阵。
    raise SystemExit(main())  # 新增代码+PostParityFinalGate：使用 main 的退出码结束进程；如果没有这行代码，CLI 不会执行最终门禁。
# 新增代码+PostParityFinalGate：模块入口段结束，本模块到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
