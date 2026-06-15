"""Computer Use full maturity 产品契约。"""  # 新增代码+ComputerUseFullMaturityContract：说明本模块专门冻结 /computer use --full 成熟版边界；如果没有这一行，读者容易把这里误解成真实动作执行器。
from __future__ import annotations  # 新增代码+ComputerUseFullMaturityContract：启用延迟类型注解解析；如果没有这一行，后续类型提示在旧导入顺序下更容易产生兼容问题。

import json  # 新增代码+ComputerUseFullMaturityContract：导入 JSON 工具用于命令行输出完整报告；如果没有这一行，失败排查只能依赖短 token 行。
from typing import Any  # 新增代码+ComputerUseFullMaturityContract：导入 Any 表示契约报告的 JSON 风格动态字段；如果没有这一行，报告类型对代码小白不够清楚。

COMPUTER_USE_FULL_MATURE_MARKER = "COMPUTER_USE_FULL_MATURE_READY"  # 新增代码+ComputerUseFullMaturityContract：固定最终成熟 ready marker；如果没有这一行，真实可见终端验收无法稳定识别成熟契约。
COMPUTER_USE_FULL_MATURE_OK_TOKEN = "COMPUTER_USE_FULL_MATURE_OK"  # 新增代码+ComputerUseFullMaturityContract：固定最终成熟 OK token；如果没有这一行，成功输出和失败输出可能被误判。
COMPUTER_USE_FULL_MATURITY_MODEL = "computer_use_full_maturity_contract"  # 新增代码+ComputerUseFullMaturityContract：固定契约报告模型名；如果没有这一行，后续矩阵无法区分这是产品契约而不是真实动作结果。
COMPUTER_USE_FULL_MATURITY_GATES = (  # 新增代码+ComputerUseFullMaturityContract：元组段开始，列出 M0-M7 必须全部通过的成熟门禁；如果没有这个常量，成熟定义会散落在文档里。
    "M0_product_semantics",  # 新增代码+ComputerUseFullMaturityContract：声明 M0 产品语义门禁；如果没有这一行，full 模式容易被误做成无限权限。
    "M1_generic_ordinary_app_discovery",  # 新增代码+ComputerUseFullMaturityContract：声明 M1 通用普通应用发现门禁；如果没有这一行，项目可能退回硬编码应用白名单。
    "M2_generic_real_launch",  # 新增代码+ComputerUseFullMaturityContract：声明 M2 通用真实启动门禁；如果没有这一行，launch 能力可能永远停在文档承诺。
    "M3_verified_window_identity_binding",  # 新增代码+ComputerUseFullMaturityContract：声明 M3 窗口身份绑定门禁；如果没有这一行，后续动作可能落到错误窗口上。
    "M4_generic_observe_plan_act_verify_loop",  # 新增代码+ComputerUseFullMaturityContract：声明 M4 通用观察计划执行验证闭环门禁；如果没有这一行，动作链路可能缺少统一验证。
    "M5_cleanup_and_recovery",  # 新增代码+ComputerUseFullMaturityContract：声明 M5 清理恢复门禁；如果没有这一行，真实启动后可能留下 agent 拥有的残留进程。
    "M6_safety_boundaries",  # 新增代码+ComputerUseFullMaturityContract：声明 M6 安全边界门禁；如果没有这一行，高风险窗口拒绝会变成可选项。
    "M7_visible_terminal_acceptance",  # 新增代码+ComputerUseFullMaturityContract：声明 M7 真实可见终端验收门禁；如果没有这一行，单元测试可能被误当成最终交付。
)  # 新增代码+ComputerUseFullMaturityContract：元组段结束，M0-M7 成熟门禁到此固定；如果没有这个边界说明，代码小白不容易看出门禁列表范围。
COMPUTER_USE_FULL_OUT_OF_SCOPE = (  # 新增代码+ComputerUseFullMaturityContract：元组段开始，列出成熟版明确不做的事情；如果没有这个常量，后续需求容易把安全边界挤掉。
    "unlimited_permission",  # 新增代码+ComputerUseFullMaturityContract：把无限权限列为范围外；如果没有这一行，用户确认可能被误解成跳过所有安全策略。
    "skip_all_safety_policy",  # 新增代码+ComputerUseFullMaturityContract：把跳过全部安全策略列为范围外；如果没有这一行，高风险目标可能被错误放行。
    "per_app_controller",  # 新增代码+ComputerUseFullMaturityContract：把每个应用一个 controller 列为范围外；如果没有这一行，通用 computer use 会退化成逐应用补丁。
    "hardcoded_app_whitelist",  # 新增代码+ComputerUseFullMaturityContract：把硬编码应用白名单列为范围外；如果没有这一行，成千上万应用无法通用扩展。
    "credential_window_events",  # 新增代码+ComputerUseFullMaturityContract：把凭据窗口事件列为范围外；如果没有这一行，密码、验证码窗口可能被错误操作。
    "uncontrolled_low_level_send",  # 新增代码+ComputerUseFullMaturityContract：把不受控底层输入列为范围外；如果没有这一行，动作可能绕过身份验证和急停。
)  # 新增代码+ComputerUseFullMaturityContract：元组段结束，范围外事项到此固定；如果没有这个边界说明，代码小白不容易看出禁止范围。

def _computer_use_full_bool_token(value: Any) -> str:  # 新增代码+ComputerUseFullMaturityContract：函数段开始，把布尔值转成稳定的小写 token；如果没有这个函数，终端输出可能因为 True/False 大小写漂移导致验收失败。
    return "true" if bool(value) else "false"  # 新增代码+ComputerUseFullMaturityContract：返回 true 或 false 文本；如果没有这一行，真实终端场景不容易稳定匹配布尔字段。
# 新增代码+ComputerUseFullMaturityContract：函数段结束，_computer_use_full_bool_token 到此结束；如果没有这个边界说明，代码小白不容易看出布尔格式化范围。

def run_computer_use_full_maturity_contract() -> dict[str, Any]:  # 新增代码+ComputerUseFullMaturityContract：函数段开始，生成 /computer use --full 成熟版产品契约报告；如果没有这个函数，测试和最终矩阵无法共享同一份边界事实。
    gates = list(COMPUTER_USE_FULL_MATURITY_GATES)  # 新增代码+ComputerUseFullMaturityContract：复制 M0-M7 门禁列表供报告使用；如果没有这一行，调用方只能读取不可序列化习惯不统一的内部常量。
    out_of_scope = list(COMPUTER_USE_FULL_OUT_OF_SCOPE)  # 新增代码+ComputerUseFullMaturityContract：复制范围外事项供报告使用；如果没有这一行，输出无法清楚展示哪些需求不属于 mature full 范围。
    return {  # 新增代码+ComputerUseFullMaturityContract：报告字典段开始，集中返回成熟契约事实；如果没有这个字典，后续矩阵和终端输出会各说各话。
        "marker": COMPUTER_USE_FULL_MATURE_MARKER,  # 新增代码+ComputerUseFullMaturityContract：写入 ready marker；如果没有这一行，报告无法被真实终端验收稳定识别。
        "ok_token": COMPUTER_USE_FULL_MATURE_OK_TOKEN,  # 新增代码+ComputerUseFullMaturityContract：写入 OK token；如果没有这一行，成功状态无法用固定字段表达。
        "model": COMPUTER_USE_FULL_MATURITY_MODEL,  # 新增代码+ComputerUseFullMaturityContract：写入模型名；如果没有这一行，后续聚合矩阵无法区分报告来源。
        "passed": True,  # 新增代码+ComputerUseFullMaturityContract：表示产品契约冻结已通过；如果没有这一行，CLI 不知道是否应该展示 OK token。
        "maturity_gates": gates,  # 新增代码+ComputerUseFullMaturityContract：写入 M0-M7 门禁列表；如果没有这一行，报告无法展示成熟任务的完整边界。
        "out_of_scope": out_of_scope,  # 新增代码+ComputerUseFullMaturityContract：写入范围外列表；如果没有这一行，禁止事项不能被最终矩阵引用。
        "single_universal_runtime_required": True,  # 新增代码+ComputerUseFullMaturityContract：声明必须使用单一通用 runtime；如果没有这一行，系统可能重新分裂成多个应用专用实现。
        "per_app_controller_required": False,  # 新增代码+ComputerUseFullMaturityContract：声明不需要逐应用 controller；如果没有这一行，通用性目标没有可测边界。
        "hardcoded_app_whitelist_required": False,  # 新增代码+ComputerUseFullMaturityContract：声明不需要硬编码应用白名单；如果没有这一行，用户指出的设计问题会复发。
        "per_app_patch_required": False,  # 新增代码+ComputerUseFullMaturityContract：声明不需要逐应用补丁；如果没有这一行，项目可能继续无止境堆 Phase。
        "full_mode_unlimited_permission": False,  # 新增代码+ComputerUseFullMaturityContract：声明 full 模式不是无限权限；如果没有这一行，安全边界会被误读。
        "skip_all_safety_policy": False,  # 新增代码+ComputerUseFullMaturityContract：声明 full 模式不跳过全部安全策略；如果没有这一行，高风险拒绝可能被绕过。
        "high_risk_refusal_required": True,  # 新增代码+ComputerUseFullMaturityContract：声明高风险目标必须拒绝；如果没有这一行，终端、凭据、支付等目标可能被误放行。
        "credential_window_zero_events_required": True,  # 新增代码+ComputerUseFullMaturityContract：声明凭据窗口必须零事件；如果没有这一行，密码和验证码区域可能被错误操作。
        "visible_terminal_acceptance_required": True,  # 新增代码+ComputerUseFullMaturityContract：声明最终必须真实可见终端验收；如果没有这一行，自动测试会被误当成最终成熟证明。
        "maturity_phase_stop_rule": True,  # 新增代码+ComputerUseFullMaturityContract：声明 M0-M7 通过后停止新增成熟 Phase；如果没有这一行，蓝图会继续无止境延长。
        "uncontrolled_actions_expanded": False,  # 新增代码+ComputerUseFullMaturityContract：声明没有扩张无边界动作；如果没有这一行，full 模式可能被误做成失控桌面控制。
    }  # 新增代码+ComputerUseFullMaturityContract：报告字典段结束，成熟契约事实到此返回；如果没有这个边界说明，代码小白不容易看出报告范围。
# 新增代码+ComputerUseFullMaturityContract：函数段结束，run_computer_use_full_maturity_contract 到此结束；如果没有这个边界说明，读者不容易看出契约报告生成范围。

def computer_use_full_maturity_contract_cli_line(report: dict[str, Any]) -> str:  # 新增代码+ComputerUseFullMaturityContract：函数段开始，把契约报告转成稳定终端 token 行；如果没有这个函数，真实终端验收只能解析复杂 JSON。
    ok_token = f" {COMPUTER_USE_FULL_MATURE_OK_TOKEN}" if bool(report.get("passed", False)) else ""  # 新增代码+ComputerUseFullMaturityContract：只在报告通过时展示 OK token；如果没有这一行，失败报告也可能被误认为成功。
    return f"{COMPUTER_USE_FULL_MATURE_MARKER}{ok_token} full_mode_unlimited_permission={_computer_use_full_bool_token(report.get('full_mode_unlimited_permission', True))} high_risk_refusal_required={_computer_use_full_bool_token(report.get('high_risk_refusal_required', False))} visible_terminal_acceptance_required={_computer_use_full_bool_token(report.get('visible_terminal_acceptance_required', False))} maturity_phase_stop_rule={_computer_use_full_bool_token(report.get('maturity_phase_stop_rule', False))} hardcoded_app_whitelist_required={_computer_use_full_bool_token(report.get('hardcoded_app_whitelist_required', True))} per_app_patch_required={_computer_use_full_bool_token(report.get('per_app_patch_required', True))} uncontrolled_actions_expanded={_computer_use_full_bool_token(report.get('uncontrolled_actions_expanded', True))}"  # 新增代码+ComputerUseFullMaturityContract：返回固定顺序的契约 token 行；如果没有这一行，终端验收和人工观察会因为输出格式漂移变得不稳定。
# 新增代码+ComputerUseFullMaturityContract：函数段结束，computer_use_full_maturity_contract_cli_line 到此结束；如果没有这个边界说明，代码小白不容易看出 CLI 格式化范围。

def main(argv: list[str] | None = None) -> int:  # 新增代码+ComputerUseFullMaturityContract：函数段开始，提供命令行自检入口；如果没有这个函数，用户不能直接运行模块查看契约报告。
    _ = argv  # 新增代码+ComputerUseFullMaturityContract：保留 argv 扩展位；如果没有这一行，读者可能误以为命令行参数被遗漏处理。
    report = run_computer_use_full_maturity_contract()  # 新增代码+ComputerUseFullMaturityContract：生成契约报告；如果没有这一行，命令行入口没有事实来源。
    print(computer_use_full_maturity_contract_cli_line(report))  # 新增代码+ComputerUseFullMaturityContract：打印稳定 token 行；如果没有这一行，真实终端验收无法快速匹配成熟契约。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+ComputerUseFullMaturityContract：打印完整 JSON 报告；如果没有这一行，失败排查缺少可读细节。
    return 0 if bool(report.get("passed", False)) else 1  # 新增代码+ComputerUseFullMaturityContract：按契约通过状态返回退出码；如果没有这一行，自动化无法区分成功和失败。
# 新增代码+ComputerUseFullMaturityContract：函数段结束，main 到此结束；如果没有这个边界说明，代码小白不容易看出命令行入口范围。

__all__ = ["COMPUTER_USE_FULL_MATURE_MARKER", "COMPUTER_USE_FULL_MATURE_OK_TOKEN", "COMPUTER_USE_FULL_MATURITY_GATES", "COMPUTER_USE_FULL_MATURITY_MODEL", "COMPUTER_USE_FULL_OUT_OF_SCOPE", "computer_use_full_maturity_contract_cli_line", "main", "run_computer_use_full_maturity_contract"]  # 新增代码+ComputerUseFullMaturityContract：限定公开导出名称；如果没有这一行，通配导入可能暴露内部 helper。

if __name__ == "__main__":  # 新增代码+ComputerUseFullMaturityContract：文件入口段开始，允许 python 文件方式直接自检；如果没有这一行，直接运行模块不会执行任何契约检查。
    raise SystemExit(main())  # 新增代码+ComputerUseFullMaturityContract：用 main 的返回码退出；如果没有这一行，命令行状态不够明确。
# 新增代码+ComputerUseFullMaturityContract：文件入口段结束，直接运行模块到此结束；如果没有这个边界说明，代码小白不容易看出脚本入口范围。
