"""Post-parity Computer Use 自我改进 dry-run 提案。"""  # 新增代码+PostParitySelfImprovement：说明本文件只负责生成安全改进建议；如果没有这一行，读者可能误以为这里会自动修改生产代码。
from __future__ import annotations  # 新增代码+PostParitySelfImprovement：启用稳定的注解解析；如果没有这一行，后续类型注解在部分环境下可能更容易出兼容问题。

from typing import Any  # 新增代码+PostParitySelfImprovement：导入动态 ledger entry 类型；如果没有这一行，函数签名无法清楚表达输入是结构化动态数据。


SAFE_CATEGORY_TO_FILE = {  # 新增代码+PostParitySelfImprovement：定义允许 dry-run 处理的失败分类到建议文件映射；如果没有这一段，提案可能指向危险或无关代码。
    "action_dispatched_but_no_state_change": "learning_agent/computer_use_mcp_v2/windows_runtime/post_parity_workflow_matrix.py",  # 新增代码+PostParitySelfImprovement：动作无效果类问题建议先看 workflow matrix；如果没有这一行，常见执行后无变化失败没有安全提案。
    "verifier_rejected": "learning_agent/computer_use_mcp_v2/windows_runtime/post_parity_workflow_matrix.py",  # 新增代码+PostParitySelfImprovement：verifier 拒绝类问题建议先看 workflow matrix；如果没有这一行，验收失败没有安全提案。
    "target_drift": "learning_agent/computer_use_mcp_v2/windows_runtime/post_parity_failure_triage.py",  # 新增代码+PostParitySelfImprovement：目标漂移类问题建议先看 triage 分类；如果没有这一行，漂移失败没有安全提案。
    "observation_missing": "learning_agent/computer_use_mcp_v2/windows_runtime/post_parity_workflow_matrix.py",  # 新增代码+PostParitySelfImprovement：观察缺失类问题建议先看 workflow matrix；如果没有这一行，观察失败没有安全提案。
}  # 新增代码+PostParitySelfImprovement：结束安全映射字典；如果没有这一行，Python 语法不完整。


UNSAFE_SCENARIO_TOKENS = (  # 新增代码+PostParitySelfImprovement：定义危险场景关键词；如果没有这一段，登录/支付/管理员类失败可能被错误建议自动修复。
    "login",  # 新增代码+PostParitySelfImprovement：登录关键词；如果没有这一行，登录类场景可能被 dry-run 处理。
    "password",  # 新增代码+PostParitySelfImprovement：密码关键词；如果没有这一行，密码类场景可能被 dry-run 处理。
    "bank",  # 新增代码+PostParitySelfImprovement：银行关键词；如果没有这一行，金融类场景可能被 dry-run 处理。
    "payment",  # 新增代码+PostParitySelfImprovement：支付关键词；如果没有这一行，支付类场景可能被 dry-run 处理。
    "uac",  # 新增代码+PostParitySelfImprovement：UAC 关键词；如果没有这一行，管理员安全弹窗类场景可能被 dry-run 处理。
    "admin",  # 新增代码+PostParitySelfImprovement：管理员关键词；如果没有这一行，管理员场景可能被 dry-run 处理。
)  # 新增代码+PostParitySelfImprovement：结束危险关键词元组；如果没有这一行，Python 语法不完整。


# 新增代码+PostParitySelfImprovement：函数段开始，_scenario_looks_unsafe 判断场景 ID 是否明显危险；如果没有这段函数，dry-run 可能处理不该碰的任务。
def _scenario_looks_unsafe(scenario_id: str) -> bool:  # 新增代码+PostParitySelfImprovement：声明危险场景判断函数；如果没有这一行，主函数无法复用安全边界。
    normalized = str(scenario_id).lower()  # 新增代码+PostParitySelfImprovement：把场景 ID 转小写；如果没有这一行，大小写变化会绕过关键词检查。
    return any(token in normalized for token in UNSAFE_SCENARIO_TOKENS)  # 新增代码+PostParitySelfImprovement：命中任一危险词就拒绝；如果没有这一行，危险场景不会被识别。
# 新增代码+PostParitySelfImprovement：函数段结束，_scenario_looks_unsafe 到此结束；如果没有这个边界说明，初学者不容易看出危险场景判断范围。


# 新增代码+PostParitySelfImprovement：函数段开始，_failure 统一返回 dry-run 拒绝报告；如果没有这段函数，拒绝分支会重复且结构可能不一致。
def _failure(reason: str) -> dict[str, Any]:  # 新增代码+PostParitySelfImprovement：声明失败报告构造函数；如果没有这一行，主函数无法快速生成稳定拒绝结果。
    return {"passed": False, "hard_fail_reasons": [reason], "production_code_edited": False}  # 新增代码+PostParitySelfImprovement：返回失败且明确未改生产代码；如果没有这一行，调用方看不出 dry-run 是否越权。
# 新增代码+PostParitySelfImprovement：函数段结束，_failure 到此结束；如果没有这个边界说明，初学者不容易看出拒绝结果构造范围。


# 新增代码+PostParitySelfImprovement：函数段开始，propose_post_parity_self_improvement 从失败账本记录生成安全下一步；如果没有这段函数，自我改进闭环没有 dry-run 入口。
def propose_post_parity_self_improvement(failed_entry: dict[str, Any]) -> dict[str, Any]:  # 新增代码+PostParitySelfImprovement：声明 dry-run 提案主函数；如果没有这一行，外部无法请求安全改进建议。
    scenario_id = str(failed_entry.get("scenario_id", "unknown_scenario"))  # 新增代码+PostParitySelfImprovement：读取场景 ID；如果没有这一行，提案无法绑定具体失败场景。
    if failed_entry.get("sanitized") is not True or _scenario_looks_unsafe(scenario_id):  # 新增代码+PostParitySelfImprovement：拒绝未脱敏或危险场景；如果没有这一行，私密/登录/支付类失败可能被处理。
        return _failure("unsafe_or_unsanitized_failure_entry")  # 新增代码+PostParitySelfImprovement：返回安全拒绝原因；如果没有这一行，危险输入会继续生成提案。
    category = str(failed_entry.get("failure_category", ""))  # 新增代码+PostParitySelfImprovement：读取失败分类；如果没有这一行，提案无法选择建议文件。
    suspected_file = SAFE_CATEGORY_TO_FILE.get(category)  # 新增代码+PostParitySelfImprovement：根据安全映射找建议文件；如果没有这一行，提案可能指向不受控位置。
    if not suspected_file:  # 新增代码+PostParitySelfImprovement：检查分类是否不在安全白名单；如果没有这一行，未知失败分类可能被猜测处理。
        return _failure("failure_category_not_safe_for_dry_run")  # 新增代码+PostParitySelfImprovement：拒绝未知或不安全分类；如果没有这一行，规则十三会被破坏。
    evidence_paths = failed_entry.get("evidence_paths") or [""]  # 新增代码+PostParitySelfImprovement：读取证据路径列表；如果没有这一行，提案缺少支撑证据。
    evidence_path = str(evidence_paths[0]) if evidence_paths else ""  # 新增代码+PostParitySelfImprovement：取第一条证据路径；如果没有这一行，提案里的证据路径可能不是字符串。
    proposed_test_name = f"test_{scenario_id}_state_changes_after_action"  # 新增代码+PostParitySelfImprovement：生成建议红测名称；如果没有这一行，自我改进没有 TDD 起点。
    return {  # 新增代码+PostParitySelfImprovement：开始返回成功提案；如果没有这一行，函数没有标准输出。
        "passed": True,  # 新增代码+PostParitySelfImprovement：声明 dry-run 提案生成成功；如果没有这一行，治理矩阵无法识别 self-improvement gate。
        "proposed_test_name": proposed_test_name,  # 新增代码+PostParitySelfImprovement：写入建议测试名；如果没有这一行，后续开发不知道先写哪个红测。
        "suspected_file": suspected_file,  # 新增代码+PostParitySelfImprovement：写入建议检查文件；如果没有这一行，后续开发缺少落点。
        "evidence_path": evidence_path,  # 新增代码+PostParitySelfImprovement：写入支撑证据路径；如果没有这一行，建议无法追溯事实依据。
        "next_task_summary": f"Add a failing regression for {scenario_id} and prove the verifier rejects {category} before implementing a fix.",  # 新增代码+PostParitySelfImprovement：写入下一步任务摘要；如果没有这一行，提案只有字段没有行动说明。
        "production_code_edited": False,  # 新增代码+PostParitySelfImprovement：明确 dry-run 没有改生产代码；如果没有这一行，自我改进边界不清晰。
        "hard_fail_reasons": [],  # 新增代码+PostParitySelfImprovement：成功提案没有失败原因；如果没有这一行，调用方需要特殊处理缺字段。
    }  # 新增代码+PostParitySelfImprovement：结束提案字典；如果没有这一行，Python 语法不完整。
# 新增代码+PostParitySelfImprovement：函数段结束，propose_post_parity_self_improvement 到此结束；如果没有这个边界说明，初学者不容易看出 dry-run 主逻辑范围。
