"""Computer Use full 模式最终成熟度矩阵。"""  # 新增代码+FullMaturityMatrix：说明本模块只负责汇总成熟度事实；如果没有这一行，读者可能误以为这里会直接控制真实桌面。
from __future__ import annotations  # 新增代码+FullMaturityMatrix：启用延迟类型注解；如果没有这一行，部分类型在旧导入顺序下可能提前解析失败。

import json  # 新增代码+FullMaturityMatrix：导入 JSON 工具用于 CLI 输出完整报告；如果没有这一行，真实终端只能看到短 token 而缺少可排查细节。
from typing import Any  # 新增代码+FullMaturityMatrix：导入 Any 表达 JSON 风格动态报告；如果没有这一行，函数签名对初学者不够清楚。

try:  # 新增代码+FullMaturityMatrix：优先按 learning_agent 包路径导入既有成熟合同；如果没有这一行，项目根运行时无法复用前 6 项任务事实。
    from learning_agent.computer_use.closed_loop_executor import phase114_verified_action_gate  # 新增代码+FullMaturityMatrix：导入 Task6 已验证窗口动作门禁；如果没有这一行，矩阵无法证明动作前必须验证窗口身份。
    from learning_agent.computer_use.full_maturity_contract import COMPUTER_USE_FULL_MATURE_MARKER, COMPUTER_USE_FULL_MATURE_OK_TOKEN, run_computer_use_full_maturity_contract  # 新增代码+FullMaturityMatrix：导入 M0 产品契约标记和报告入口；如果没有这一行，最终矩阵会重复定义成熟 token。
    from learning_agent.computer_use.generic_app_discovery import resolve_generic_app_launch_target  # 新增代码+FullMaturityMatrix：导入 Task1 通用发现入口；如果没有这一行，矩阵无法证明不需要硬编码应用白名单。
    from learning_agent.computer_use.generic_launch_backend import run_phase110_generic_launch_backend_contract  # 新增代码+FullMaturityMatrix：导入 Task2 通用启动后端合同；如果没有这一行，矩阵无法证明授权后端已经接通。
    from learning_agent.computer_use.owned_resource_registry import run_phase112_owned_resource_registry_contract  # 新增代码+FullMaturityMatrix：导入 Task4 自有资源清理合同；如果没有这一行，矩阵无法证明 cleanup/recovery 已闭合。
    from learning_agent.computer_use.target_identity import build_owned_target_identity, run_phase111_target_identity_contract, verify_owned_target_identity  # 新增代码+FullMaturityMatrix：导入 Task3 目标身份构建和验证工具；如果没有这一行，矩阵无法证明动作绑定的是自有窗口。
except ModuleNotFoundError as error:  # 新增代码+FullMaturityMatrix：兼容 start_oauth_agent.bat 从 learning_agent 目录启动的脚本模式；如果没有这一行，真实可见终端可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.closed_loop_executor", "learning_agent.computer_use.full_maturity_contract", "learning_agent.computer_use.generic_app_discovery", "learning_agent.computer_use.generic_launch_backend", "learning_agent.computer_use.owned_resource_registry", "learning_agent.computer_use.target_identity"}:  # 新增代码+FullMaturityMatrix：只兜底包路径缺失；如果没有这一行，内部真实 bug 可能被错误隐藏。
        raise  # 新增代码+FullMaturityMatrix：重新抛出非路径类导入错误；如果没有这一行，排查成熟矩阵失败会变得困难。
    from computer_use.closed_loop_executor import phase114_verified_action_gate  # type: ignore  # 新增代码+FullMaturityMatrix：脚本模式导入同一 Task6 门禁；如果没有这一行，双击 bat 后 maturity 命令不可用。
    from computer_use.full_maturity_contract import COMPUTER_USE_FULL_MATURE_MARKER, COMPUTER_USE_FULL_MATURE_OK_TOKEN, run_computer_use_full_maturity_contract  # type: ignore  # 新增代码+FullMaturityMatrix：脚本模式导入同一 M0 契约；如果没有这一行，真实终端无法输出最终 token。
    from computer_use.generic_app_discovery import resolve_generic_app_launch_target  # type: ignore  # 新增代码+FullMaturityMatrix：脚本模式导入同一通用发现入口；如果没有这一行，真实终端无法证明非白名单路线。
    from computer_use.generic_launch_backend import run_phase110_generic_launch_backend_contract  # type: ignore  # 新增代码+FullMaturityMatrix：脚本模式导入同一通用后端合同；如果没有这一行，真实终端无法检查启动后端成熟度。
    from computer_use.owned_resource_registry import run_phase112_owned_resource_registry_contract  # type: ignore  # 新增代码+FullMaturityMatrix：脚本模式导入同一清理合同；如果没有这一行，真实终端无法检查 cleanup/recovery。
    from computer_use.target_identity import build_owned_target_identity, run_phase111_target_identity_contract, verify_owned_target_identity  # type: ignore  # 新增代码+FullMaturityMatrix：脚本模式导入同一目标身份工具；如果没有这一行，真实终端无法检查窗口身份门禁。

COMPUTER_USE_FULL_MATURITY_MATRIX_MODEL = "computer_use_full_maturity_matrix"  # 新增代码+FullMaturityMatrix：定义最终矩阵模型名；如果没有这一行，报告来源无法和 M0 单项契约区分。


def _computer_use_full_matrix_bool_token(value: Any) -> str:  # 新增代码+FullMaturityMatrix：函数段开始，把布尔值转成稳定小写 token；如果没有这个函数，终端输出会因 True/False 大小写漂移。
    return "true" if bool(value) else "false"  # 新增代码+FullMaturityMatrix：返回 true 或 false 文本；如果没有这一行，验收器无法稳定匹配矩阵字段。
# 新增代码+FullMaturityMatrix：函数段结束，_computer_use_full_matrix_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


def _computer_use_full_matrix_sample_window() -> dict[str, Any]:  # 新增代码+FullMaturityMatrix：函数段开始，构造无桌面副作用的可信窗口样本；如果没有这个函数，矩阵可能依赖用户本机是否打开某个应用。
    return {"pid": 8601, "hwnd": 18601, "window_id": "hwnd:18601", "process_name": "Obsidian.exe", "process_path": r"C:\Users\joyzq\AppData\Local\Obsidian\Obsidian.exe", "title_preview": "Vault - Obsidian", "app_id": "Obsidian.exe"}  # 新增代码+FullMaturityMatrix：返回真实风格但不触碰桌面的窗口记录；如果没有这一行，目标身份验证缺少稳定输入。
# 新增代码+FullMaturityMatrix：函数段结束，_computer_use_full_matrix_sample_window 到此结束；如果没有这个边界说明，初学者不容易看出样本窗口范围。


def _computer_use_full_matrix_verified_window_report() -> dict[str, Any]:  # 新增代码+FullMaturityMatrix：函数段开始，用合成样本证明动作必须绑定已验证自有窗口；如果没有这个函数，矩阵只能相信 Task6 常量而没有可运行证据。
    launch_result = {"process_id": 8601, "process_executable": "Obsidian.exe", "process_path": r"C:\Users\joyzq\AppData\Local\Obsidian\Obsidian.exe", "owned_process_registered": True, "cleanup_registered": True}  # 新增代码+FullMaturityMatrix：构造自有进程样本；如果没有这一行，窗口身份没有进程基准。
    window = _computer_use_full_matrix_sample_window()  # 新增代码+FullMaturityMatrix：读取稳定窗口样本；如果没有这一行，身份构建和动作门禁没有同一窗口输入。
    owned = build_owned_target_identity(launch_result, window)  # 新增代码+FullMaturityMatrix：构建自有目标身份；如果没有这一行，矩阵无法证明目标从启动结果绑定而来。
    verification = verify_owned_target_identity(owned, window).to_report()  # 新增代码+FullMaturityMatrix：对同一窗口做动作前验证；如果没有这一行，动作前门禁没有 allowed 证据。
    gate = phase114_verified_action_gate(session_id="computer-use-full-maturity-matrix", window_identity=owned.window.to_report(), target_identity_verification=verification, require_verified_identity=True)  # 新增代码+FullMaturityMatrix：运行 Task6 统一动作门禁；如果没有这一行，点击和输入层的 verified window 要求无法被矩阵引用。
    gate["target_identity_report"] = owned.to_report()  # 新增代码+FullMaturityMatrix：附加期望目标身份报告；如果没有这一行，排查时看不到门禁基准。
    gate["target_identity_verification"] = verification  # 新增代码+FullMaturityMatrix：附加动作前验证报告；如果没有这一行，排查时看不到 allowed 和 drift 字段。
    gate["real_desktop_touched"] = False  # 新增代码+FullMaturityMatrix：声明该验证只用合成样本不碰真实桌面；如果没有这一行，只读矩阵可能被误认为触发了桌面动作。
    return gate  # 新增代码+FullMaturityMatrix：返回已验证窗口动作报告；如果没有这一行，上层拿不到 Task6 事实。
# 新增代码+FullMaturityMatrix：函数段结束，_computer_use_full_matrix_verified_window_report 到此结束；如果没有这个边界说明，初学者不容易看出动作门禁证据范围。


def _computer_use_full_matrix_generic_safe_discovery() -> dict[str, Any]:  # 新增代码+FullMaturityMatrix：函数段开始，构造普通应用通用发现样本；如果没有这个函数，矩阵会依赖用户机器是否安装指定 app。
    candidates = [{"display_name": "Obsidian", "executable": "Obsidian.exe", "source": "full_maturity_matrix_sample", "installed_app_verified": True}]  # 新增代码+FullMaturityMatrix：提供普通应用候选；如果没有这一行，测试环境可能走 fallback 而不稳定。
    return resolve_generic_app_launch_target("obsidian", candidates=candidates)  # 新增代码+FullMaturityMatrix：运行通用发现解析；如果没有这一行，矩阵无法证明普通应用不靠硬编码白名单。
# 新增代码+FullMaturityMatrix：函数段结束，_computer_use_full_matrix_generic_safe_discovery 到此结束；如果没有这个边界说明，初学者不容易看出普通发现样本范围。


def _computer_use_full_matrix_high_risk_discovery() -> dict[str, Any]:  # 新增代码+FullMaturityMatrix：函数段开始，构造高风险目标拒绝样本；如果没有这个函数，矩阵无法证明 full 不是无限权限。
    candidates = [{"display_name": "Windows PowerShell", "executable": "powershell.exe", "source": "full_maturity_matrix_sample", "installed_app_verified": True}]  # 新增代码+FullMaturityMatrix：提供高风险候选；如果没有这一行，高风险拒绝可能只测试用户输入而漏掉候选名风险。
    return resolve_generic_app_launch_target("powershell", candidates=candidates)  # 新增代码+FullMaturityMatrix：运行高风险解析；如果没有这一行，矩阵无法证明 PowerShell 仍被零副作用拒绝。
# 新增代码+FullMaturityMatrix：函数段结束，_computer_use_full_matrix_high_risk_discovery 到此结束；如果没有这个边界说明，初学者不容易看出高风险样本范围。


def _computer_use_full_matrix_any_true(*reports: dict[str, Any], field: str) -> bool:  # 新增代码+FullMaturityMatrix：函数段开始，汇总多个报告里的危险布尔字段；如果没有这个函数，负向字段容易手写漏项。
    return any(bool(report.get(field, False)) for report in reports)  # 新增代码+FullMaturityMatrix：只要任一报告为真就返回真；如果没有这一行，某个阶段触碰桌面或扩大动作面可能被漏掉。
# 新增代码+FullMaturityMatrix：函数段结束，_computer_use_full_matrix_any_true 到此结束；如果没有这个边界说明，初学者不容易看出负向字段汇总范围。


def run_computer_use_full_maturity_matrix() -> dict[str, Any]:  # 新增代码+FullMaturityMatrix：函数段开始，汇总 M0-M7 最终成熟矩阵；如果没有这个函数，蓝图无法停止在一张可验证的最终表上。
    contract_report = run_computer_use_full_maturity_contract()  # 新增代码+FullMaturityMatrix：运行产品语义契约；如果没有这一行，矩阵缺少 full 模式边界事实。
    discovery_report = _computer_use_full_matrix_generic_safe_discovery()  # 新增代码+FullMaturityMatrix：运行普通应用通用发现样本；如果没有这一行，矩阵缺少不靠白名单的证据。
    launch_backend_report = run_phase110_generic_launch_backend_contract()  # 新增代码+FullMaturityMatrix：运行通用启动后端合同；如果没有这一行，矩阵无法证明真实启动后端已接好。
    target_identity_report = run_phase111_target_identity_contract()  # 新增代码+FullMaturityMatrix：运行目标身份合同；如果没有这一行，矩阵无法证明窗口身份和漂移阻断已成熟。
    cleanup_report = run_phase112_owned_resource_registry_contract()  # 新增代码+FullMaturityMatrix：运行自有资源清理合同；如果没有这一行，矩阵无法证明 stop/abort 后可恢复。
    verified_window_report = _computer_use_full_matrix_verified_window_report()  # 新增代码+FullMaturityMatrix：运行已验证窗口动作门禁样本；如果没有这一行，矩阵无法证明动作层绑定目标身份。
    high_risk_report = _computer_use_full_matrix_high_risk_discovery()  # 新增代码+FullMaturityMatrix：运行高风险拒绝样本；如果没有这一行，矩阵无法证明 full 不放开系统工具。
    product_contract = bool(contract_report.get("passed") and not contract_report.get("hardcoded_app_whitelist_required", True) and not contract_report.get("per_app_patch_required", True))  # 新增代码+FullMaturityMatrix：汇总产品契约是否通过；如果没有这一行，最终 passed 无法引用 M0。
    generic_discovery = bool(discovery_report.get("passed") and discovery_report.get("dynamic_discovery_used") and not discovery_report.get("hardcoded_app_whitelist_required", True) and not discovery_report.get("per_app_patch_required", True))  # 新增代码+FullMaturityMatrix：汇总通用发现是否通过；如果没有这一行，逐应用补丁路线可能被误判成熟。
    generic_real_launch = bool(launch_backend_report.get("passed") and launch_backend_report.get("generic_launch_backend_ready") and launch_backend_report.get("generic_real_launch_enabled_when_authorized") and launch_backend_report.get("default_off_zero_events"))  # 新增代码+FullMaturityMatrix：汇总通用真实启动后端是否成熟；如果没有这一行，候选准备和真实后端接通会被混淆。
    verified_window_actions = bool(target_identity_report.get("passed") and verified_window_report.get("actions_require_verified_window") and verified_window_report.get("same_target") and not verified_window_report.get("blocked") and verified_window_report.get("decision") == "target_identity_verified")  # 新增代码+FullMaturityMatrix：汇总动作是否必须验证自有窗口；如果没有这一行，动作漂移风险不会进入最终 passed。
    cleanup_recovery = bool(cleanup_report.get("passed") and cleanup_report.get("cleanup_only_owned_resources") and cleanup_report.get("preexisting_user_windows_preserved") and cleanup_report.get("residual_check_fails_if_owned_process_remains"))  # 新增代码+FullMaturityMatrix：汇总清理恢复是否成熟；如果没有这一行，残留进程风险不会进入最终 passed。
    high_risk_refused = bool(high_risk_report.get("high_risk_refused") and not high_risk_report.get("real_launch_attempted") and not high_risk_report.get("real_desktop_touched"))  # 新增代码+FullMaturityMatrix：汇总高风险拒绝是否零副作用；如果没有这一行，PowerShell 等目标可能被误认为可放行。
    visible_terminal_acceptance = bool(contract_report.get("visible_terminal_acceptance_required", False))  # 新增代码+FullMaturityMatrix：把真实可见终端验收门禁纳入矩阵；如果没有这一行，自动测试可能被误当最终交付。
    hardcoded_app_whitelist_required = bool(contract_report.get("hardcoded_app_whitelist_required", True) or discovery_report.get("hardcoded_app_whitelist_required", True))  # 新增代码+FullMaturityMatrix：汇总是否仍需要硬编码白名单；如果没有这一行，用户指出的设计问题无法量化。
    per_app_patch_required = bool(contract_report.get("per_app_patch_required", True) or discovery_report.get("per_app_patch_required", True))  # 新增代码+FullMaturityMatrix：汇总是否仍需要逐应用补丁；如果没有这一行，项目可能继续无止境堆 phase。
    uncontrolled_actions_expanded = _computer_use_full_matrix_any_true(contract_report, discovery_report, launch_backend_report, target_identity_report, cleanup_report, verified_window_report, high_risk_report, field="uncontrolled_actions_expanded")  # 新增代码+FullMaturityMatrix：汇总是否扩大未受控动作面；如果没有这一行，安全边界退化可能被漏掉。
    real_desktop_touched = _computer_use_full_matrix_any_true(discovery_report, launch_backend_report, target_identity_report, cleanup_report, verified_window_report, high_risk_report, field="real_desktop_touched")  # 新增代码+FullMaturityMatrix：汇总矩阵查询是否触碰真实桌面；如果没有这一行，只读 maturity 命令可能悄悄产生副作用。
    low_level_event_count = int(verified_window_report.get("low_level_event_count", 0) or 0)  # 新增代码+FullMaturityMatrix：统计矩阵自身产生的低层事件数；如果没有这一行，零事件门禁没有数值证据。
    passed = bool(product_contract and generic_discovery and generic_real_launch and verified_window_actions and cleanup_recovery and high_risk_refused and visible_terminal_acceptance and not hardcoded_app_whitelist_required and not per_app_patch_required and not uncontrolled_actions_expanded and not real_desktop_touched and low_level_event_count == 0)  # 新增代码+FullMaturityMatrix：计算最终成熟矩阵是否通过；如果没有这一行，CLI 无法决定是否输出 OK token。
    return {"marker": COMPUTER_USE_FULL_MATURE_MARKER, "ok_token": COMPUTER_USE_FULL_MATURE_OK_TOKEN, "model": COMPUTER_USE_FULL_MATURITY_MATRIX_MODEL, "passed": passed, "product_contract": product_contract, "generic_discovery": generic_discovery, "generic_real_launch": generic_real_launch, "verified_window_actions": verified_window_actions, "cleanup_recovery": cleanup_recovery, "high_risk_refused": high_risk_refused, "visible_terminal_acceptance": visible_terminal_acceptance, "hardcoded_app_whitelist_required": hardcoded_app_whitelist_required, "per_app_patch_required": per_app_patch_required, "uncontrolled_actions_expanded": uncontrolled_actions_expanded, "real_desktop_touched": real_desktop_touched, "low_level_event_count": low_level_event_count, "reports": {"product_contract": contract_report, "generic_discovery": discovery_report, "generic_real_launch": launch_backend_report, "target_identity": target_identity_report, "verified_window_actions": verified_window_report, "cleanup_recovery": cleanup_report, "high_risk_refusal": high_risk_report}}  # 新增代码+FullMaturityMatrix：返回最终结构化矩阵；如果没有这一行，测试、终端和最终验收无法共享同一份事实。
# 新增代码+FullMaturityMatrix：函数段结束，run_computer_use_full_maturity_matrix 到此结束；如果没有这个边界说明，初学者不容易看出最终矩阵汇总范围。


def computer_use_full_maturity_cli_line(report: dict[str, Any]) -> str:  # 新增代码+FullMaturityMatrix：函数段开始，把最终矩阵转成稳定终端 token 行；如果没有这个函数，真实可见终端验收需要解析复杂 JSON。
    ok_token = f" {COMPUTER_USE_FULL_MATURE_OK_TOKEN}" if bool(report.get("passed", False)) else ""  # 新增代码+FullMaturityMatrix：只在矩阵通过时追加 OK token；如果没有这一行，失败报告也可能被误判成功。
    return f"{COMPUTER_USE_FULL_MATURE_MARKER}{ok_token} product_contract={_computer_use_full_matrix_bool_token(report.get('product_contract', False))} generic_discovery={_computer_use_full_matrix_bool_token(report.get('generic_discovery', False))} generic_real_launch={_computer_use_full_matrix_bool_token(report.get('generic_real_launch', False))} verified_window_actions={_computer_use_full_matrix_bool_token(report.get('verified_window_actions', False))} cleanup_recovery={_computer_use_full_matrix_bool_token(report.get('cleanup_recovery', False))} high_risk_refused={_computer_use_full_matrix_bool_token(report.get('high_risk_refused', False))} visible_terminal_acceptance={_computer_use_full_matrix_bool_token(report.get('visible_terminal_acceptance', False))} hardcoded_app_whitelist_required={_computer_use_full_matrix_bool_token(report.get('hardcoded_app_whitelist_required', True))} per_app_patch_required={_computer_use_full_matrix_bool_token(report.get('per_app_patch_required', True))} uncontrolled_actions_expanded={_computer_use_full_matrix_bool_token(report.get('uncontrolled_actions_expanded', True))} real_desktop_touched={_computer_use_full_matrix_bool_token(report.get('real_desktop_touched', True))} low_level_event_count={int(report.get('low_level_event_count', 0) or 0)}"  # 新增代码+FullMaturityMatrix：返回固定顺序最终 token 行；如果没有这一行，真实终端验收会因输出漂移不稳定。
# 新增代码+FullMaturityMatrix：函数段结束，computer_use_full_maturity_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式化范围。


def computer_use_full_maturity_main(argv: list[str] | None = None) -> int:  # 新增代码+FullMaturityMatrix：函数段开始，提供命令行自检入口；如果没有这个函数，用户不能直接运行模块查看最终矩阵。
    _ = argv  # 新增代码+FullMaturityMatrix：保留 argv 扩展位；如果没有这一行，读者可能误以为命令行参数被遗漏处理。
    report = run_computer_use_full_maturity_matrix()  # 新增代码+FullMaturityMatrix：生成最终成熟矩阵；如果没有这一行，CLI 没有事实来源。
    print(computer_use_full_maturity_cli_line(report))  # 新增代码+FullMaturityMatrix：打印稳定 token 行；如果没有这一行，真实终端验收不能快速匹配最终状态。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+FullMaturityMatrix：打印完整 JSON 报告；如果没有这一行，失败排查缺少每项子报告。
    return 0 if bool(report.get("passed", False)) else 1  # 新增代码+FullMaturityMatrix：按矩阵通过状态返回退出码；如果没有这一行，自动化无法区分成功和失败。
# 新增代码+FullMaturityMatrix：函数段结束，computer_use_full_maturity_main 到此结束；如果没有这个边界说明，初学者不容易看出脚本入口范围。


main = computer_use_full_maturity_main  # 新增代码+FullMaturityMatrix：提供常规 main 别名；如果没有这一行，python 模块运行入口和公开函数命名会不一致。

__all__ = ["COMPUTER_USE_FULL_MATURITY_MATRIX_MODEL", "computer_use_full_maturity_cli_line", "computer_use_full_maturity_main", "main", "run_computer_use_full_maturity_matrix"]  # 新增代码+FullMaturityMatrix：限定公开 API；如果没有这一行，通配导入可能暴露内部样本 helper。

if __name__ == "__main__":  # 新增代码+FullMaturityMatrix：文件入口段开始，允许直接运行本模块；如果没有这一行，python 文件方式不会执行自检。
    raise SystemExit(computer_use_full_maturity_main())  # 新增代码+FullMaturityMatrix：用矩阵入口退出；如果没有这一行，命令行状态码不会反映成熟度。
# 新增代码+FullMaturityMatrix：文件入口段结束，直接运行模块到此结束；如果没有这个边界说明，初学者不容易看出脚本执行范围。
