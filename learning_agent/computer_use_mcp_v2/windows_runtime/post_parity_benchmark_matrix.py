"""Post-parity Computer Use 真实任务 benchmark 扩容矩阵。"""  # 新增代码+Phase148BBenchmark：说明本文件负责评估 Phase148B 的真实任务覆盖面；如果没有这行代码，读者无法快速知道模块用途。
from __future__ import annotations  # 新增代码+Phase148BBenchmark：启用稳定的延迟注解解析；如果没有这行代码，较复杂类型注解在部分环境里更容易出现兼容问题。

import argparse  # 新增代码+Phase148BBenchmark：导入命令行参数解析器；如果没有这行代码，真实终端无法通过参数传入 benchmark 证据文件。
import json  # 新增代码+Phase148BBenchmark：导入 JSON 解析工具；如果没有这行代码，矩阵无法读取结构化 evidence 文件。
from pathlib import Path  # 新增代码+Phase148BBenchmark：导入路径对象；如果没有这行代码，文件存在性和读取逻辑会更容易写错。
from typing import Any  # 新增代码+Phase148BBenchmark：导入动态字典类型；如果没有这行代码，公开函数无法清晰表达接收结构化证据。

POST_PARITY_BENCHMARK_MARKER = "COMPUTER_USE_POST_PARITY_BENCHMARK_READY"  # 新增代码+Phase148BBenchmark：定义稳定终端 marker；如果没有这行代码，acceptance controller 无法可靠匹配 Phase148B 成功输出。
REQUIRED_BENCHMARK_FAMILIES = (  # 新增代码+Phase148BBenchmark：定义必须覆盖的 benchmark 类型集合；如果没有这段代码，真实任务扩容没有清晰标准。
    "single_app_text",  # 新增代码+Phase148BBenchmark：要求覆盖单应用文本任务；如果没有这行代码，Notepad 类基础任务可能缺席。
    "single_app_calculation",  # 新增代码+Phase148BBenchmark：要求覆盖单应用计算任务；如果没有这行代码，Calculator 类按钮网格任务可能缺席。
    "local_browser",  # 新增代码+Phase148BBenchmark：要求覆盖本地浏览器页面任务；如果没有这行代码，浏览器 GUI 能力可能缺席。
    "local_file",  # 新增代码+Phase148BBenchmark：要求覆盖本地文件任务；如果没有这行代码，Explorer/文件往返能力可能缺席。
    "multi_app_transfer",  # 新增代码+Phase148BBenchmark：要求覆盖跨应用信息转移；如果没有这行代码，多窗口协作能力可能缺席。
    "failure_recovery",  # 新增代码+Phase148BBenchmark：要求覆盖失败恢复任务；如果没有这行代码，agent 出错后的复原能力不可见。
    "long_task_resume",  # 新增代码+Phase148BBenchmark：要求覆盖长任务恢复任务；如果没有这行代码，长任务 harness 能力不可见。
)  # 新增代码+Phase148BBenchmark：结束必须类型元组；如果没有这行代码，Python 元组语法不完整。
REQUIRED_BENCHMARK_KEYS = {  # 新增代码+Phase148BBenchmark：定义 benchmark catalog 必填字段；如果没有这段代码，目录里可能混入缺少安全合同的任务。
    "id",  # 新增代码+Phase148BBenchmark：要求每个 benchmark 有稳定 ID；如果没有这行代码，证据和目录无法可靠关联。
    "family",  # 新增代码+Phase148BBenchmark：要求每个 benchmark 声明任务类型；如果没有这行代码，覆盖面无法统计。
    "target_apps",  # 新增代码+Phase148BBenchmark：要求声明目标应用；如果没有这行代码，权限和目标身份边界不清楚。
    "risk_level",  # 新增代码+Phase148BBenchmark：要求声明风险等级；如果没有这行代码，高风险任务可能混入默认集合。
    "visible_terminal_required",  # 新增代码+Phase148BBenchmark：要求声明真实可见终端验收；如果没有这行代码，规则十七可能被绕过。
    "cleanup_required",  # 新增代码+Phase148BBenchmark：要求声明清理；如果没有这行代码，benchmark 可能污染用户环境。
    "evidence_requirements",  # 新增代码+Phase148BBenchmark：要求声明证据要求；如果没有这行代码，执行后不知道该收集什么。
    "stop_conditions",  # 新增代码+Phase148BBenchmark：要求声明停止条件；如果没有这行代码，登录/支付/UAC 等危险边界不清楚。
}  # 新增代码+Phase148BBenchmark：结束 catalog 必填字段集合；如果没有这行代码，Python 集合语法不完整。


# 新增代码+Phase148BBenchmark：函数段开始，_benchmark_case 统一构造受控 benchmark 条目；如果没有这段函数，7 类任务会重复写大量安全字段且容易漏项。
def _benchmark_case(benchmark_id: str, family: str, target_apps: list[str], prompt: str) -> dict[str, Any]:  # 新增代码+Phase148BBenchmark：声明 benchmark 条目构造函数；如果没有这行代码，目录构造没有统一入口。
    return {  # 新增代码+Phase148BBenchmark：开始返回 benchmark 字典；如果没有这行代码，函数不会产生目录条目。
        "id": benchmark_id,  # 新增代码+Phase148BBenchmark：写入稳定 benchmark ID；如果没有这行代码，证据无法回指具体任务。
        "family": family,  # 新增代码+Phase148BBenchmark：写入任务类型；如果没有这行代码，矩阵无法统计覆盖面。
        "target_apps": list(target_apps),  # 新增代码+Phase148BBenchmark：写入目标应用副本；如果没有这行代码，调用方修改原列表可能污染 catalog。
        "risk_level": "controlled_local",  # 新增代码+Phase148BBenchmark：限制为受控本地任务；如果没有这行代码，登录、支付或管理员任务可能混入默认 benchmark。
        "visible_terminal_required": True,  # 新增代码+Phase148BBenchmark：强制真实可见终端验收；如果没有这行代码，自动化日志可能冒充最终验收。
        "cleanup_required": True,  # 新增代码+Phase148BBenchmark：强制 cleanup；如果没有这行代码，真实桌面或临时目录可能被污染。
        "evidence_requirements": [  # 新增代码+Phase148BBenchmark：开始声明证据要求列表；如果没有这行代码，执行方不知道要收集哪些证据。
            "before_observation",  # 新增代码+Phase148BBenchmark：要求动作前观察；如果没有这行代码，agent 未观察目标也可能通过。
            "after_observation",  # 新增代码+Phase148BBenchmark：要求动作后观察；如果没有这行代码，状态变化无法证明。
            "target_identity_verified",  # 新增代码+Phase148BBenchmark：要求目标身份验证；如果没有这行代码，动作可能落错窗口。
            "physical_dispatch",  # 新增代码+Phase148BBenchmark：要求真实派发；如果没有这行代码，脚本假动作可能冒充 Computer Use。
            "ledger_entry_written",  # 新增代码+Phase148BBenchmark：要求账本记录；如果没有这行代码，证据无法长期追踪。
            "visible_terminal_verified",  # 新增代码+Phase148BBenchmark：要求终端验收；如果没有这行代码，规则十七可能失效。
        ],  # 新增代码+Phase148BBenchmark：结束证据要求列表；如果没有这行代码，Python 列表语法不完整。
        "stop_conditions": [  # 新增代码+Phase148BBenchmark：开始声明停止条件；如果没有这行代码，危险任务边界不清楚。
            "login_or_private_account",  # 新增代码+Phase148BBenchmark：遇到登录或私有账号停止；如果没有这行代码，隐私边界可能被突破。
            "payment_or_money_movement",  # 新增代码+Phase148BBenchmark：遇到支付或资金流转停止；如果没有这行代码，财务风险可能进入 benchmark。
            "uac_or_admin_window",  # 新增代码+Phase148BBenchmark：遇到 UAC 或管理员窗口停止；如果没有这行代码，权限边界可能被绕过。
            "private_user_data",  # 新增代码+Phase148BBenchmark：遇到用户私密数据停止；如果没有这行代码，证据可能收集敏感内容。
        ],  # 新增代码+Phase148BBenchmark：结束停止条件列表；如果没有这行代码，Python 列表语法不完整。
        "real_user_prompt": prompt,  # 新增代码+Phase148BBenchmark：保存真实用户风格 prompt；如果没有这行代码，后续执行者不知道该如何触发任务。
    }  # 新增代码+Phase148BBenchmark：结束 benchmark 字典；如果没有这行代码，Python 字典语法不完整。
# 新增代码+Phase148BBenchmark：函数段结束，_benchmark_case 到此结束；如果没有这段边界说明，初学者不容易看出构造逻辑范围。


# 新增代码+Phase148BBenchmark：函数段开始，get_default_post_parity_benchmark_catalog 返回 Phase148B 默认任务目录；如果没有这段函数，benchmark 扩容没有统一来源。
def get_default_post_parity_benchmark_catalog() -> list[dict[str, Any]]:  # 新增代码+Phase148BBenchmark：声明默认 catalog 读取函数；如果没有这行代码，测试和运行时无法读取 benchmark 清单。
    return [  # 新增代码+Phase148BBenchmark：开始返回 7 类 benchmark 列表；如果没有这行代码，函数不会返回任何任务。
        _benchmark_case("phase148b_single_app_text", "single_app_text", ["notepad"], "请在受控 Notepad 里写一行测试文本，然后保存到项目临时证据目录。"),  # 新增代码+Phase148BBenchmark：登记文本任务；如果没有这行代码，单应用文本覆盖缺失。
        _benchmark_case("phase148b_single_app_calculation", "single_app_calculation", ["calculator"], "请在受控 Calculator 里完成一个简单计算，并用可见证据证明结果。"),  # 新增代码+Phase148BBenchmark：登记计算任务；如果没有这行代码，计算类桌面控制覆盖缺失。
        _benchmark_case("phase148b_local_browser", "local_browser", ["browser"], "请打开受控本地网页并点击页面按钮，确认页面状态发生变化。"),  # 新增代码+Phase148BBenchmark：登记本地浏览器任务；如果没有这行代码，浏览器 GUI 覆盖缺失。
        _benchmark_case("phase148b_local_file", "local_file", ["explorer", "notepad"], "请在受控临时目录创建文件、查看文件、再完成清理。"),  # 新增代码+Phase148BBenchmark：登记文件任务；如果没有这行代码，文件系统 GUI 覆盖缺失。
        _benchmark_case("phase148b_multi_app_transfer", "multi_app_transfer", ["browser", "notepad"], "请从受控本地网页读取一段信息，再写入受控 Notepad。"),  # 新增代码+Phase148BBenchmark：登记跨应用转移任务；如果没有这行代码，多应用协作覆盖缺失。
        _benchmark_case("phase148b_failure_recovery", "failure_recovery", ["notepad"], "请模拟一次找不到目标控件的失败，并恢复到可继续执行的安全状态。"),  # 新增代码+Phase148BBenchmark：登记失败恢复任务；如果没有这行代码，失败后复原能力覆盖缺失。
        _benchmark_case("phase148b_long_task_resume", "long_task_resume", ["notepad", "browser"], "请模拟长任务中断后读取 ledger 并继续完成剩余步骤。"),  # 新增代码+Phase148BBenchmark：登记长任务恢复任务；如果没有这行代码，长任务 harness 覆盖缺失。
    ]  # 新增代码+Phase148BBenchmark：结束 benchmark 列表；如果没有这行代码，Python 列表语法不完整。
# 新增代码+Phase148BBenchmark：函数段结束，get_default_post_parity_benchmark_catalog 到此结束；如果没有这段边界说明，初学者不容易看出目录范围。


# 新增代码+Phase148BBenchmark：函数段开始，validate_post_parity_benchmark_case 校验单个 catalog 条目；如果没有这段函数，坏任务可能混入 benchmark 目录。
def validate_post_parity_benchmark_case(item: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase148BBenchmark：声明 catalog 校验函数；如果没有这行代码，测试和运行时无法复用校验逻辑。
    missing = sorted(REQUIRED_BENCHMARK_KEYS - set(item))  # 新增代码+Phase148BBenchmark：计算缺失字段；如果没有这行代码，缺项原因无法被清楚报告。
    risk_ok = item.get("risk_level") == "controlled_local"  # 新增代码+Phase148BBenchmark：校验风险等级；如果没有这行代码，高风险条目可能被接受。
    terminal_ok = item.get("visible_terminal_required") is True  # 新增代码+Phase148BBenchmark：校验真实终端要求；如果没有这行代码，规则十七可能被弱化。
    cleanup_ok = item.get("cleanup_required") is True  # 新增代码+Phase148BBenchmark：校验清理要求；如果没有这行代码，污染环境的任务可能被接受。
    valid = not missing and risk_ok and terminal_ok and cleanup_ok  # 新增代码+Phase148BBenchmark：汇总校验结果；如果没有这行代码，调用方无法知道条目是否有效。
    return {"valid": valid, "missing": missing, "risk_ok": risk_ok, "terminal_ok": terminal_ok, "cleanup_ok": cleanup_ok}  # 新增代码+Phase148BBenchmark：返回结构化校验报告；如果没有这行代码，坏条目无法被定位。
# 新增代码+Phase148BBenchmark：函数段结束，validate_post_parity_benchmark_case 到此结束；如果没有这段边界说明，初学者不容易看出校验范围。


# 新增代码+Phase148BBenchmark：函数段开始，_accepted_benchmark 判断单条 evidence 是否满足闭环合同；如果没有这段函数，不完整证据可能被误计入覆盖。
def _accepted_benchmark(item: dict[str, Any]) -> bool:  # 新增代码+Phase148BBenchmark：声明单条证据接受函数；如果没有这行代码，矩阵无法复用统一接受规则。
    return (  # 新增代码+Phase148BBenchmark：开始组合所有必需证据条件；如果没有这行代码，判断逻辑不完整。
        item.get("accepted") is True  # 新增代码+Phase148BBenchmark：要求 verifier 接受；如果没有这行代码，失败样本也可能计入覆盖。
        and item.get("before_observation") is True  # 新增代码+Phase148BBenchmark：要求动作前观察；如果没有这行代码，未观察目标也可能通过。
        and item.get("after_observation") is True  # 新增代码+Phase148BBenchmark：要求动作后观察；如果没有这行代码，状态变化无法证明。
        and item.get("target_identity_verified") is True  # 新增代码+Phase148BBenchmark：要求目标身份验证；如果没有这行代码，错误窗口动作可能通过。
        and item.get("physical_dispatch") is True  # 新增代码+Phase148BBenchmark：要求真实物理派发；如果没有这行代码，脚本假动作可能通过。
        and item.get("verifier_decision") == "accepted"  # 新增代码+Phase148BBenchmark：要求验收裁决明确 accepted；如果没有这行代码，模糊状态可能通过。
        and item.get("cleanup_completed") is True  # 新增代码+Phase148BBenchmark：要求清理完成；如果没有这行代码，污染环境的任务可能通过。
        and item.get("ledger_entry_written") is True  # 新增代码+Phase148BBenchmark：要求账本记录；如果没有这行代码，证据不可追踪。
        and item.get("visible_terminal_verified") is True  # 新增代码+Phase148BBenchmark：要求真实可见终端验收；如果没有这行代码，规则十七无法进入 benchmark。
        and item.get("safety_boundary_respected") is True  # 新增代码+Phase148BBenchmark：要求安全边界被遵守；如果没有这行代码，高风险任务可能混入通过集合。
    )  # 新增代码+Phase148BBenchmark：结束条件组合；如果没有这行代码，Python 表达式语法不完整。
# 新增代码+Phase148BBenchmark：函数段结束，_accepted_benchmark 到此结束；如果没有这段边界说明，初学者不容易看出接受规则范围。


# 新增代码+Phase148BBenchmark：函数段开始，evaluate_post_parity_benchmark_matrix 评估 7 类真实任务 benchmark 覆盖；如果没有这段函数，Phase148B 没有核心矩阵。
def evaluate_post_parity_benchmark_matrix(benchmark_evidence: list[dict[str, Any]] | None) -> dict[str, Any]:  # 新增代码+Phase148BBenchmark：声明 benchmark 矩阵评估入口；如果没有这行代码，外部无法运行 Phase148B。
    evidence = list(benchmark_evidence or [])  # 新增代码+Phase148BBenchmark：把输入规范成列表；如果没有这行代码，None 输入会导致迭代异常。
    hard_fail_reasons: list[str] = []  # 新增代码+Phase148BBenchmark：初始化硬失败原因；如果没有这行代码，用户不知道矩阵为什么失败。
    catalog = get_default_post_parity_benchmark_catalog()  # 新增代码+Phase148BBenchmark：读取默认 catalog；如果没有这行代码，矩阵无法确认目录本身是否完整。
    catalog_checks = [validate_post_parity_benchmark_case(item) for item in catalog]  # 新增代码+Phase148BBenchmark：校验目录每一项；如果没有这行代码，坏目录也可能继续评估。
    benchmark_catalog_gate = all(check["valid"] for check in catalog_checks)  # 新增代码+Phase148BBenchmark：汇总 catalog gate；如果没有这行代码，目录缺陷不会影响总结果。
    if not benchmark_catalog_gate:  # 新增代码+Phase148BBenchmark：检查目录 gate 是否失败；如果没有这行代码，失败原因不会写入报告。
        hard_fail_reasons.append("benchmark_catalog_invalid")  # 新增代码+Phase148BBenchmark：记录目录无效；如果没有这行代码，排查时不知道是目录问题。
    if any(item.get("visible_terminal_verified") is False for item in evidence):  # 新增代码+Phase148BBenchmark：检查显式缺少真实终端的证据；如果没有这行代码，规则十七缺口不会被点名。
        hard_fail_reasons.append("benchmark_visible_terminal_missing")  # 新增代码+Phase148BBenchmark：记录真实终端缺失；如果没有这行代码，终端验收缺口不清楚。
    if any(item.get("cleanup_completed") is False for item in evidence):  # 新增代码+Phase148BBenchmark：检查显式清理失败；如果没有这行代码，环境污染风险不会被点名。
        hard_fail_reasons.append("benchmark_cleanup_missing")  # 新增代码+Phase148BBenchmark：记录清理缺失；如果没有这行代码，cleanup 问题不清楚。
    if any(item.get("physical_dispatch") is False for item in evidence):  # 新增代码+Phase148BBenchmark：检查显式未真实派发；如果没有这行代码，假动作风险不会被点名。
        hard_fail_reasons.append("benchmark_dispatch_missing")  # 新增代码+Phase148BBenchmark：记录派发缺失；如果没有这行代码，真实动作缺口不清楚。
    if any(item.get("safety_boundary_respected") is False for item in evidence):  # 新增代码+Phase148BBenchmark：检查显式越过安全边界；如果没有这行代码，高风险任务可能悄悄进入报告。
        hard_fail_reasons.append("benchmark_safety_boundary_breached")  # 新增代码+Phase148BBenchmark：记录安全边界失败；如果没有这行代码，风险原因不清楚。
    accepted = [item for item in evidence if _accepted_benchmark(item)]  # 新增代码+Phase148BBenchmark：筛选完整合格证据；如果没有这行代码，不完整样本也可能计入覆盖。
    covered_families = sorted({str(item.get("family")) for item in accepted})  # 新增代码+Phase148BBenchmark：统计已覆盖类型；如果没有这行代码，用户看不到当前覆盖面。
    missing_families = [family for family in REQUIRED_BENCHMARK_FAMILIES if family not in covered_families]  # 新增代码+Phase148BBenchmark：计算缺失类型；如果没有这行代码，下一步补哪里不清楚。
    if missing_families:  # 新增代码+Phase148BBenchmark：检查是否仍有缺失类型；如果没有这行代码，缺口不会进入失败原因。
        hard_fail_reasons.append("benchmark_required_families_missing")  # 新增代码+Phase148BBenchmark：记录覆盖类型缺失；如果没有这行代码，覆盖不足不清楚。
    evidence_contract_gate = not missing_families and bool(accepted)  # 新增代码+Phase148BBenchmark：计算证据合同 gate；如果没有这行代码，矩阵没有覆盖充分性判断。
    safety_boundary_gate = not any(item.get("safety_boundary_respected") is False for item in evidence)  # 新增代码+Phase148BBenchmark：计算安全边界 gate；如果没有这行代码，高风险越界不会影响报告字段。
    visible_terminal_coverage_gate = bool(accepted) and all(item.get("visible_terminal_verified") is True for item in accepted)  # 新增代码+Phase148BBenchmark：计算真实终端覆盖 gate；如果没有这行代码，终端验收覆盖状态不可见。
    passed = not hard_fail_reasons and benchmark_catalog_gate and evidence_contract_gate and safety_boundary_gate and visible_terminal_coverage_gate  # 新增代码+Phase148BBenchmark：汇总总通过状态；如果没有这行代码，Phase148B 无法给出最终结论。
    return {  # 新增代码+Phase148BBenchmark：开始返回结构化报告；如果没有这行代码，调用方拿不到矩阵结果。
        "marker": POST_PARITY_BENCHMARK_MARKER,  # 新增代码+Phase148BBenchmark：输出稳定 marker；如果没有这行代码，真实终端无法锚定 Phase148B。
        "passed": passed,  # 新增代码+Phase148BBenchmark：输出总通过状态；如果没有这行代码，验收器无法判断成功或失败。
        "required_family_count": len(REQUIRED_BENCHMARK_FAMILIES),  # 新增代码+Phase148BBenchmark：输出必需类型数量；如果没有这行代码，用户不知道 benchmark 规模。
        "accepted_count": len(accepted),  # 新增代码+Phase148BBenchmark：输出合格证据数量；如果没有这行代码，覆盖规模不可见。
        "covered_families": covered_families,  # 新增代码+Phase148BBenchmark：输出已覆盖类型；如果没有这行代码，用户无法检查覆盖内容。
        "missing_families": missing_families,  # 新增代码+Phase148BBenchmark：输出缺失类型；如果没有这行代码，下一步修复方向不明确。
        "benchmark_catalog_gate": benchmark_catalog_gate,  # 新增代码+Phase148BBenchmark：输出目录 gate；如果没有这行代码，目录成熟度不可见。
        "evidence_contract_gate": evidence_contract_gate,  # 新增代码+Phase148BBenchmark：输出证据合同 gate；如果没有这行代码，证据成熟度不可见。
        "safety_boundary_gate": safety_boundary_gate,  # 新增代码+Phase148BBenchmark：输出安全边界 gate；如果没有这行代码，安全状态不可见。
        "visible_terminal_coverage_gate": visible_terminal_coverage_gate,  # 新增代码+Phase148BBenchmark：输出可见终端覆盖 gate；如果没有这行代码，规则十七状态不可见。
        "hard_fail_reasons": hard_fail_reasons,  # 新增代码+Phase148BBenchmark：输出失败原因；如果没有这行代码，后续 agent 不知道要补什么。
    }  # 新增代码+Phase148BBenchmark：结束报告字典；如果没有这行代码，Python 字典语法不完整。
# 新增代码+Phase148BBenchmark：函数段结束，evaluate_post_parity_benchmark_matrix 到此结束；如果没有这段边界说明，初学者不容易看出评估范围。


# 新增代码+Phase148BBenchmark：函数段开始，load_post_parity_benchmark_evidence_file 读取 benchmark 证据文件；如果没有这段函数，CLI 无法消费 Phase148B evidence。
def load_post_parity_benchmark_evidence_file(evidence_file_path: str) -> dict[str, Any]:  # 新增代码+Phase148BBenchmark：声明证据文件读取函数；如果没有这行代码，测试和 CLI 无法复用读取逻辑。
    path = Path(evidence_file_path)  # 新增代码+Phase148BBenchmark：把字符串路径转为 Path；如果没有这行代码，后续 exists/read_text 调用不方便。
    if not path.exists():  # 新增代码+Phase148BBenchmark：检查证据文件是否存在；如果没有这行代码，缺文件会变成底层异常。
        return {"benchmark_evidence": [], "load_error": f"evidence_file_missing:{path}"}  # 新增代码+Phase148BBenchmark：返回结构化缺文件错误；如果没有这行代码，终端输出无法说明失败原因。
    try:  # 新增代码+Phase148BBenchmark：开始 JSON 解析保护；如果没有这行代码，坏 JSON 会让真实终端直接崩溃。
        payload = json.loads(path.read_text(encoding="utf-8-sig"))  # 新增代码+Phase148BBenchmark：读取并解析 UTF-8/带 BOM JSON；如果没有这行代码，证据文件无法进入矩阵。
    except json.JSONDecodeError as error:  # 新增代码+Phase148BBenchmark：捕获 JSON 格式错误；如果没有这行代码，坏证据不会形成可读失败报告。
        return {"benchmark_evidence": [], "load_error": f"evidence_file_invalid_json:{error}"}  # 新增代码+Phase148BBenchmark：返回结构化解析错误；如果没有这行代码，用户不知道文件哪里坏。
    if not isinstance(payload, dict):  # 新增代码+Phase148BBenchmark：确认顶层是对象；如果没有这行代码，数组或字符串可能污染矩阵输入。
        return {"benchmark_evidence": [], "load_error": "evidence_file_not_object"}  # 新增代码+Phase148BBenchmark：返回顶层类型错误；如果没有这行代码，坏结构不清楚。
    evidence = payload.get("benchmark_evidence")  # 新增代码+Phase148BBenchmark：读取 benchmark_evidence 字段；如果没有这行代码，矩阵拿不到核心证据列表。
    return payload if isinstance(evidence, list) else {"benchmark_evidence": [], "load_error": "benchmark_evidence_not_list"}  # 新增代码+Phase148BBenchmark：只接受列表证据；如果没有这行代码，坏字段可能被误用。
# 新增代码+Phase148BBenchmark：函数段结束，load_post_parity_benchmark_evidence_file 到此结束；如果没有这段边界说明，初学者不容易看出读取范围。


# 新增代码+Phase148BBenchmark：函数段开始，format_post_parity_benchmark_summary_line 生成真实终端稳定单行 token；如果没有这段函数，验收器无法可靠匹配输出。
def format_post_parity_benchmark_summary_line(report: dict[str, Any]) -> str:  # 新增代码+Phase148BBenchmark：声明摘要格式化函数；如果没有这行代码，CLI 和测试无法共用输出格式。
    return (  # 新增代码+Phase148BBenchmark：开始拼接固定顺序摘要行；如果没有这行代码，返回表达式不完整。
        f"{POST_PARITY_BENCHMARK_MARKER} passed={str(report.get('passed') is True).lower()} "  # 新增代码+Phase148BBenchmark：输出 marker 和总状态；如果没有这行代码，终端缺少主锚点。
        f"required_family_count={report.get('required_family_count', 0)} "  # 新增代码+Phase148BBenchmark：输出必需类型数量；如果没有这行代码，终端看不到 benchmark 规模。
        f"accepted_count={report.get('accepted_count', 0)} "  # 新增代码+Phase148BBenchmark：输出合格证据数量；如果没有这行代码，终端看不到实际覆盖条数。
        f"benchmark_catalog_gate={str(report.get('benchmark_catalog_gate') is True).lower()} "  # 新增代码+Phase148BBenchmark：输出目录 gate；如果没有这行代码，目录成熟度不在终端可见。
        f"evidence_contract_gate={str(report.get('evidence_contract_gate') is True).lower()} "  # 新增代码+Phase148BBenchmark：输出证据 gate；如果没有这行代码，证据成熟度不在终端可见。
        f"safety_boundary_gate={str(report.get('safety_boundary_gate') is True).lower()} "  # 新增代码+Phase148BBenchmark：输出安全 gate；如果没有这行代码，安全边界不在终端可见。
        f"visible_terminal_coverage_gate={str(report.get('visible_terminal_coverage_gate') is True).lower()}"  # 新增代码+Phase148BBenchmark：输出终端覆盖 gate；如果没有这行代码，规则十七不在最终 token 中。
    )  # 新增代码+Phase148BBenchmark：结束摘要行拼接；如果没有这行代码，Python 表达式语法不完整。
# 新增代码+Phase148BBenchmark：函数段结束，format_post_parity_benchmark_summary_line 到此结束；如果没有这段边界说明，初学者不容易看出输出范围。


# 新增代码+Phase148BBenchmark：函数段开始，main 提供真实终端可运行 CLI；如果没有这段函数，acceptance controller 无法要求 agent 执行 Phase148B gate。
def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase148BBenchmark：声明 CLI 入口；如果没有这行代码，python -m 无法稳定返回验收退出码。
    parser = argparse.ArgumentParser(description="Run Computer Use post-parity benchmark expansion matrix.")  # 新增代码+Phase148BBenchmark：创建参数解析器；如果没有这行代码，参数错误没有清晰提示。
    parser.add_argument("--evidence-file", required=True)  # 新增代码+Phase148BBenchmark：要求传入 evidence 文件；如果没有这行代码，CLI 可能无证据假运行。
    args = parser.parse_args(argv)  # 新增代码+Phase148BBenchmark：解析命令行参数；如果没有这行代码，CLI 不知道用户传了什么。
    evidence = load_post_parity_benchmark_evidence_file(args.evidence_file)  # 新增代码+Phase148BBenchmark：读取证据文件；如果没有这行代码，矩阵没有输入。
    report = evaluate_post_parity_benchmark_matrix(evidence.get("benchmark_evidence"))  # 新增代码+Phase148BBenchmark：运行 benchmark 矩阵；如果没有这行代码，CLI 不会产生判断。
    print(format_post_parity_benchmark_summary_line(report))  # 新增代码+Phase148BBenchmark：打印稳定摘要行；如果没有这行代码，真实终端没有可匹配成功 token。
    print(json.dumps(report, ensure_ascii=False, indent=2))  # 新增代码+Phase148BBenchmark：打印完整报告；如果没有这行代码，失败时缺少细节供排查。
    return 0 if report.get("passed") is True else 1  # 新增代码+Phase148BBenchmark：用退出码表达成败；如果没有这行代码，自动化无法可靠判断结果。
# 新增代码+Phase148BBenchmark：函数段结束，main 到此结束；如果没有这段边界说明，初学者不容易看出 CLI 范围。


if __name__ == "__main__":  # 新增代码+Phase148BBenchmark：模块入口段开始，允许 python -m 直接运行；如果没有这行代码，真实终端无法直接启动本矩阵。
    raise SystemExit(main())  # 新增代码+Phase148BBenchmark：执行 main 并返回退出码；如果没有这行代码，CLI 不会真正运行。
# 新增代码+Phase148BBenchmark：模块入口段结束，本文件到此结束；如果没有这段说明，初学者不容易看出直接运行范围。
