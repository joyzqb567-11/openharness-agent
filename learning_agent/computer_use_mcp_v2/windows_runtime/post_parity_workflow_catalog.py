"""Post-parity Computer Use 受控工作流目录。"""  # 新增代码+PostParityWorkflowCatalog：说明本文件负责列出 post-parity 阶段的受控真实任务样本；如果没有这一行，读者无法快速理解模块职责。
from __future__ import annotations  # 新增代码+PostParityWorkflowCatalog：启用稳定的注解解析行为；如果没有这一行，后续复杂类型在部分环境中可能更容易出现兼容问题。

from typing import Any  # 新增代码+PostParityWorkflowCatalog：导入动态字典字段类型；如果没有这一行，校验函数无法清楚标注工作流结构是动态数据。


REQUIRED_WORKFLOW_KEYS = {  # 新增代码+PostParityWorkflowCatalog：定义每个工作流必须具备的字段集合；如果没有这一段，catalog 可能混入缺少安全合同的任务。
    "id",  # 新增代码+PostParityWorkflowCatalog：要求每个工作流有稳定 ID；如果没有这一行，ledger 和矩阵无法稳定引用场景。
    "family",  # 新增代码+PostParityWorkflowCatalog：要求声明工作流家族；如果没有这一行，矩阵无法判断单应用、多应用、本地浏览器覆盖。
    "target_apps",  # 新增代码+PostParityWorkflowCatalog：要求声明目标应用；如果没有这一行，执行器无法提前做权限和目标身份约束。
    "allowed_temp_roots",  # 新增代码+PostParityWorkflowCatalog：要求声明允许写入的临时根目录；如果没有这一行，任务可能写到用户隐私路径。
    "verifier_expectations",  # 新增代码+PostParityWorkflowCatalog：要求声明验收期望；如果没有这一行，执行完之后不知道怎样判断成功。
    "cleanup_required",  # 新增代码+PostParityWorkflowCatalog：要求声明必须清理；如果没有这一行，工作流可能污染用户环境。
    "target_identity_required",  # 新增代码+PostParityWorkflowCatalog：要求声明必须验证目标身份；如果没有这一行，真实动作可能落到错误窗口。
    "visible_terminal_required",  # 新增代码+PostParityWorkflowCatalog：要求声明必须真实可见终端验收；如果没有这一行，规则十七可能被跳过。
    "risk_level",  # 新增代码+PostParityWorkflowCatalog：要求声明风险级别；如果没有这一行，危险任务可能混入第一批 post-parity 样本。
}  # 新增代码+PostParityWorkflowCatalog：结束必填字段集合；如果没有这一行，Python 集合语法不完整。


POST_PARITY_WORKFLOW_IDS = (  # 新增代码+PostParityWorkflowCatalog：定义默认工作流 ID 顺序；如果没有这一段，矩阵和测试无法稳定知道 catalog 里应该有哪些任务。
    "post_parity_local_text_edit",  # 新增代码+PostParityWorkflowCatalog：本地文本编辑工作流 ID；如果没有这一行，Notepad 类普通任务缺少代表样本。
    "post_parity_local_calculation_to_text",  # 新增代码+PostParityWorkflowCatalog：计算结果写入文本工作流 ID；如果没有这一行，Calculator 到文本的跨任务样本缺失。
    "post_parity_local_browser_click",  # 新增代码+PostParityWorkflowCatalog：本地浏览器点击工作流 ID；如果没有这一行，浏览器本地页面样本缺失。
    "post_parity_local_file_roundtrip",  # 新增代码+PostParityWorkflowCatalog：本地文件往返工作流 ID；如果没有这一行，文件系统普通操作样本缺失。
    "post_parity_browser_plus_notepad_summary",  # 新增代码+PostParityWorkflowCatalog：浏览器加 Notepad 多应用工作流 ID；如果没有这一行，跨应用协调样本缺失。
)  # 新增代码+PostParityWorkflowCatalog：结束默认 ID 元组；如果没有这一行，Python 元组语法不完整。


# 新增代码+PostParityWorkflowCatalog：函数段开始，_workflow 统一构造受控本地工作流；如果没有这段函数，五个工作流会重复大量安全字段且容易写漏。
def _workflow(workflow_id: str, family: str, target_apps: list[str], verifier_expectations: list[str]) -> dict[str, Any]:  # 新增代码+PostParityWorkflowCatalog：声明工作流构造函数；如果没有这一行，调用方无法用统一入口生成工作流字典。
    return {  # 新增代码+PostParityWorkflowCatalog：开始返回工作流字典；如果没有这一行，函数不会产出 catalog 项。
        "id": workflow_id,  # 新增代码+PostParityWorkflowCatalog：写入稳定工作流 ID；如果没有这一行，ledger 和矩阵无法关联场景。
        "family": family,  # 新增代码+PostParityWorkflowCatalog：写入工作流家族；如果没有这一行，覆盖矩阵无法判断任务类型。
        "target_apps": list(target_apps),  # 新增代码+PostParityWorkflowCatalog：写入目标应用列表副本；如果没有这一行，权限和目标身份策略没有输入。
        "allowed_temp_roots": ["learning_agent/memory/computer_use/post_parity"],  # 新增代码+PostParityWorkflowCatalog：限制工作流只能写项目内受控 evidence 区；如果没有这一行，测试可能碰到用户隐私路径。
        "verifier_expectations": list(verifier_expectations),  # 新增代码+PostParityWorkflowCatalog：写入验收期望列表副本；如果没有这一行，执行结果没有明确判断标准。
        "cleanup_required": True,  # 新增代码+PostParityWorkflowCatalog：要求工作流完成后清理；如果没有这一行，真实桌面或临时目录可能被污染。
        "target_identity_required": True,  # 新增代码+PostParityWorkflowCatalog：要求每次真实动作前验证目标身份；如果没有这一行，焦点漂移风险会被漏掉。
        "visible_terminal_required": True,  # 新增代码+PostParityWorkflowCatalog：要求走真实可见终端验收；如果没有这一行，后续可能用普通 CLI 冒充成熟。
        "risk_level": "controlled_local",  # 新增代码+PostParityWorkflowCatalog：标记为受控本地风险；如果没有这一行，登录/支付/UAC 等高风险任务可能混入当前蓝图。
    }  # 新增代码+PostParityWorkflowCatalog：结束工作流字典；如果没有这一行，Python 语法不完整。
# 新增代码+PostParityWorkflowCatalog：函数段结束，_workflow 到此结束；如果没有这个边界说明，初学者不容易看出工作流构造范围。


# 新增代码+PostParityWorkflowCatalog：函数段开始，get_default_post_parity_workflow_catalog 返回默认工作流目录；如果没有这段函数，后续矩阵没有统一 catalog 来源。
def get_default_post_parity_workflow_catalog() -> list[dict[str, Any]]:  # 新增代码+PostParityWorkflowCatalog：声明默认 catalog 获取函数；如果没有这一行，测试和运行时代码无法读取默认任务清单。
    return [  # 新增代码+PostParityWorkflowCatalog：开始返回默认工作流列表；如果没有这一行，函数不会返回任何工作流。
        _workflow(  # 新增代码+PostParityWorkflowCatalog：构造本地文本编辑工作流；如果没有这一段，Notepad 类本地文本任务缺少样本。
            "post_parity_local_text_edit",  # 新增代码+PostParityWorkflowCatalog：指定文本工作流 ID；如果没有这一行，工作流无法被 ledger 稳定引用。
            "local_text",  # 新增代码+PostParityWorkflowCatalog：指定文本工作流家族；如果没有这一行，矩阵无法识别它属于单应用样本。
            ["notepad"],  # 新增代码+PostParityWorkflowCatalog：指定目标应用 Notepad；如果没有这一行，权限和目标身份没有应用范围。
            ["controlled_file_contains_expected_text"],  # 新增代码+PostParityWorkflowCatalog：指定文本内容验收期望；如果没有这一行，执行后不知道如何验收。
        ),  # 新增代码+PostParityWorkflowCatalog：结束文本工作流构造；如果没有这一行，列表元素语法不完整。
        _workflow(  # 新增代码+PostParityWorkflowCatalog：构造计算结果写入文本工作流；如果没有这一段，Calculator 到 Notepad 的真实用户样本缺失。
            "post_parity_local_calculation_to_text",  # 新增代码+PostParityWorkflowCatalog：指定计算工作流 ID；如果没有这一行，工作流无法被稳定引用。
            "local_calculation",  # 新增代码+PostParityWorkflowCatalog：指定计算工作流家族；如果没有这一行，矩阵无法识别计算类任务覆盖。
            ["calculator", "notepad"],  # 新增代码+PostParityWorkflowCatalog：指定 Calculator 和 Notepad 两个目标应用；如果没有这一行，跨应用输入输出关系不明确。
            ["calculator_result_matches_expected", "notepad_receives_result"],  # 新增代码+PostParityWorkflowCatalog：指定计算和写入两个验收期望；如果没有这一行，任务是否完成不可验证。
        ),  # 新增代码+PostParityWorkflowCatalog：结束计算工作流构造；如果没有这一行，列表元素语法不完整。
        _workflow(  # 新增代码+PostParityWorkflowCatalog：构造本地浏览器点击工作流；如果没有这一段，Browser 本地页面样本缺失。
            "post_parity_local_browser_click",  # 新增代码+PostParityWorkflowCatalog：指定浏览器工作流 ID；如果没有这一行，工作流无法被 ledger 稳定引用。
            "local_browser",  # 新增代码+PostParityWorkflowCatalog：指定浏览器工作流家族；如果没有这一行，矩阵无法识别本地浏览器覆盖。
            ["browser"],  # 新增代码+PostParityWorkflowCatalog：指定目标应用 Browser；如果没有这一行，权限和目标身份没有应用范围。
            ["local_page_changed_after_real_click"],  # 新增代码+PostParityWorkflowCatalog：指定真实点击后页面变化验收期望；如果没有这一行，浏览器动作是否有效不可验证。
        ),  # 新增代码+PostParityWorkflowCatalog：结束浏览器工作流构造；如果没有这一行，列表元素语法不完整。
        _workflow(  # 新增代码+PostParityWorkflowCatalog：构造本地文件往返工作流；如果没有这一段，文件系统普通任务样本缺失。
            "post_parity_local_file_roundtrip",  # 新增代码+PostParityWorkflowCatalog：指定文件工作流 ID；如果没有这一行，工作流无法被稳定引用。
            "local_file",  # 新增代码+PostParityWorkflowCatalog：指定文件工作流家族；如果没有这一行，矩阵无法识别文件类任务覆盖。
            ["explorer", "notepad"],  # 新增代码+PostParityWorkflowCatalog：指定 Explorer 和 Notepad；如果没有这一行，文件操作与文本查看/编辑目标不明确。
            ["controlled_temp_file_created", "controlled_temp_file_cleaned"],  # 新增代码+PostParityWorkflowCatalog：指定创建和清理验收期望；如果没有这一行，文件残留不会被检查。
        ),  # 新增代码+PostParityWorkflowCatalog：结束文件工作流构造；如果没有这一行，列表元素语法不完整。
        _workflow(  # 新增代码+PostParityWorkflowCatalog：构造浏览器加 Notepad 摘要工作流；如果没有这一段，多应用协调样本缺失。
            "post_parity_browser_plus_notepad_summary",  # 新增代码+PostParityWorkflowCatalog：指定多应用工作流 ID；如果没有这一行，工作流无法被稳定引用。
            "multi_app",  # 新增代码+PostParityWorkflowCatalog：指定多应用家族；如果没有这一行，矩阵无法识别跨应用覆盖。
            ["browser", "notepad"],  # 新增代码+PostParityWorkflowCatalog：指定 Browser 和 Notepad 两个目标应用；如果没有这一行，跨应用任务范围不明确。
            ["browser_local_page_read", "notepad_summary_written"],  # 新增代码+PostParityWorkflowCatalog：指定读取和写入摘要验收期望；如果没有这一行，多应用任务完成标准不明确。
        ),  # 新增代码+PostParityWorkflowCatalog：结束多应用工作流构造；如果没有这一行，列表元素语法不完整。
    ]  # 新增代码+PostParityWorkflowCatalog：结束默认工作流列表；如果没有这一行，Python 列表语法不完整。
# 新增代码+PostParityWorkflowCatalog：函数段结束，get_default_post_parity_workflow_catalog 到此结束；如果没有这个边界说明，初学者不容易看出默认 catalog 范围。


# 新增代码+PostParityWorkflowCatalog：函数段开始，validate_post_parity_workflow 校验工作流是否满足蓝图安全合同；如果没有这段函数，后续无法阻止缺字段或高风险工作流混入。
def validate_post_parity_workflow(workflow: dict[str, Any]) -> dict[str, Any]:  # 新增代码+PostParityWorkflowCatalog：声明工作流校验函数；如果没有这一行，测试和矩阵无法复用同一校验入口。
    missing = sorted(REQUIRED_WORKFLOW_KEYS - set(workflow))  # 新增代码+PostParityWorkflowCatalog：计算缺失必填字段；如果没有这一行，缺字段错误无法精确报告。
    valid = not missing and workflow.get("risk_level") == "controlled_local"  # 新增代码+PostParityWorkflowCatalog：只有字段齐全且风险受控才通过；如果没有这一行，高风险或缺字段任务会被误接收。
    return {"valid": valid, "missing": missing}  # 新增代码+PostParityWorkflowCatalog：返回校验结果和缺失字段；如果没有这一行，调用方不知道校验结论。
# 新增代码+PostParityWorkflowCatalog：函数段结束，validate_post_parity_workflow 到此结束；如果没有这个边界说明，初学者不容易看出校验逻辑范围。
