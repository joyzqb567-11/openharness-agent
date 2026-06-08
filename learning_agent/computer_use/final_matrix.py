"""Windows Computer Use 最终矩阵验收。"""  # 新增代码+Phase42WindowsFinalMatrix: 集中运行 Phase35-41 的安全合同总验收；如果没有这个文件，最终验收会散落在 JSON 和手写命令里难以复盘。

from __future__ import annotations  # 新增代码+Phase42WindowsFinalMatrix: 延迟解析类型注解；如果没有这行代码，旧入口遇到前向类型时更容易导入失败。

import json  # 新增代码+Phase42WindowsFinalMatrix: 读取最终验收矩阵 JSON；如果没有这行代码，模块无法验证矩阵文件内容。
from pathlib import Path  # 新增代码+Phase42WindowsFinalMatrix: 处理矩阵路径；如果没有这行代码，路径拼接会变成脆弱字符串。
from typing import Any  # 新增代码+Phase42WindowsFinalMatrix: 标注通用报告字典；如果没有这行代码，函数边界不清楚。


PHASE42_WINDOWS_COMPUTER_USE_FINAL_MARKER = "PHASE42_WINDOWS_COMPUTER_USE_FINAL_READY"  # 新增代码+Phase42WindowsFinalMatrix: 定义最终矩阵 ready marker；如果没有这行代码，可见终端验收没有稳定等待锚点。
PHASE42_WINDOWS_COMPUTER_USE_FINAL_OK_TOKEN = "PHASE42_WINDOWS_COMPUTER_USE_FINAL_OK"  # 新增代码+Phase42WindowsFinalMatrix: 定义最终矩阵 OK token；如果没有这行代码，debug log 无法区分合同通过和普通回答。
PHASE42_MATRIX_MODEL = "phase42_windows_computer_use_final_matrix"  # 新增代码+Phase42WindowsFinalMatrix: 定义最终矩阵模型名；如果没有这行代码，报告无法说明使用哪版总验收规则。
PHASE42_ACTIONS_EXPANDED = False  # 新增代码+Phase42WindowsFinalMatrix: 明确最终矩阵不扩大真实桌面动作面；如果没有这行代码，用户可能误以为 Phase42 新增控制能力。
DEFAULT_PHASE42_MATRIX_PATH = Path(__file__).resolve().parents[1] / "acceptance_controller" / "final_acceptance_matrix_phase42_windows_computer_use.json"  # 新增代码+Phase42WindowsFinalMatrix: 定义默认矩阵 JSON 路径；如果没有这行代码，测试和 CLI 要重复硬编码路径。
EXPECTED_PHASE42_PHASES = [35, 36, 37, 38, 39, 40, 41]  # 新增代码+Phase42WindowsFinalMatrix: 定义最终矩阵必须覆盖的阶段编号；如果没有这行代码，漏跑某个阶段不容易被发现。


# 新增代码+Phase42WindowsFinalMatrix: 函数段开始，_bool_token 把布尔值转成验收器稳定匹配的小写 token；如果没有这段函数，CLI 行可能混用 True/False 和 true/false，作者意图是让真实终端断言稳定。
def _bool_token(value: Any) -> str:  # 新增代码+Phase42WindowsFinalMatrix: 定义布尔 token helper；如果没有这行代码，多个输出字段会重复写转换逻辑。
    return str(bool(value)).lower()  # 新增代码+Phase42WindowsFinalMatrix: 返回小写布尔文本；如果没有这行代码，场景 JSON 的 token 匹配可能失败。
# 新增代码+Phase42WindowsFinalMatrix: 函数段结束，_bool_token 到此结束；如果没有这个结束标记，学习者不容易看出布尔格式边界。


# 新增代码+Phase42WindowsFinalMatrix: 函数段开始，load_phase42_final_matrix 读取最终矩阵 JSON；如果没有这段函数，测试和 CLI 无法共用同一份矩阵，作者意图是让 Phase42 以文件作为可审计蓝图。
def load_phase42_final_matrix(matrix_path: Path | str | None = None) -> dict[str, Any]:  # 新增代码+Phase42WindowsFinalMatrix: 定义矩阵读取入口；如果没有这行代码，外部只能手动打开 JSON。
    path = Path(matrix_path) if matrix_path is not None else DEFAULT_PHASE42_MATRIX_PATH  # 新增代码+Phase42WindowsFinalMatrix: 选择传入路径或默认路径；如果没有这行代码，测试不能注入备用矩阵。
    return json.loads(path.read_text(encoding="utf-8"))  # 新增代码+Phase42WindowsFinalMatrix: 读取并解析 UTF-8 JSON；如果没有这行代码，矩阵文件不会参与验收。
# 新增代码+Phase42WindowsFinalMatrix: 函数段结束，load_phase42_final_matrix 到此结束；如果没有这个结束标记，学习者不容易看出矩阵读取边界。


# 新增代码+Phase42WindowsFinalMatrix: 函数段开始，_phase42_import_contracts 延迟导入各阶段安全合同；如果没有这段函数，模块导入时会急切加载所有阶段并增加循环导入风险，作者意图是只在运行总验收时加载依赖。
def _phase42_import_contracts() -> dict[str, Any]:  # 新增代码+Phase42WindowsFinalMatrix: 定义阶段合同导入 helper；如果没有这行代码，run 函数会塞满重复导入代码。
    try:  # 新增代码+Phase42WindowsFinalMatrix: 优先使用包模式导入；如果没有这行代码，正常 unittest 和 agent 入口无法加载阶段合同。
        from learning_agent.computer_use.approval import phase38_cli_line, run_phase38_approval_contract  # 新增代码+Phase42WindowsFinalMatrix: 导入 Phase38 approval 合同；如果没有这行代码，最终矩阵无法覆盖会话授权和禁止目标。
        from learning_agent.computer_use.coordinates import phase39_cli_line, run_phase39_coordinates_contract  # 新增代码+Phase42WindowsFinalMatrix: 导入 Phase39 坐标合同；如果没有这行代码，最终矩阵无法覆盖坐标和窗口状态。
        from learning_agent.computer_use.evidence import phase41_cli_line, run_phase41_image_results_contract  # 新增代码+Phase42WindowsFinalMatrix: 导入 Phase41 图片结果合同；如果没有这行代码，最终矩阵无法覆盖 artifact visibility。
        from learning_agent.computer_use.real_uia_smoke import phase35_cli_line, run_phase35_real_uia_smoke  # 新增代码+Phase42WindowsFinalMatrix: 导入 Phase35 UIA smoke 合同；如果没有这行代码，最终矩阵无法覆盖真实 UIA 依赖诊断边界。
        from learning_agent.computer_use.sendinput_executor import phase37_cli_line, run_phase37_sendinput_executor_contract  # 新增代码+Phase42WindowsFinalMatrix: 导入 Phase37 SendInput 合同；如果没有这行代码，最终矩阵无法覆盖安全假执行动作。
        from learning_agent.computer_use.session_runtime import phase40_cli_line, run_phase40_abort_cleanup_contract  # 新增代码+Phase42WindowsFinalMatrix: 导入 Phase40 runtime 合同；如果没有这行代码，最终矩阵无法覆盖 abort/cleanup。
        from learning_agent.computer_use.wgc_capture import phase36_cli_line, run_phase36_wgc_provider_contract  # 新增代码+Phase42WindowsFinalMatrix: 导入 Phase36 WGC provider 合同；如果没有这行代码，最终矩阵无法覆盖截图 provider 边界。
    except ModuleNotFoundError as error:  # 新增代码+Phase42WindowsFinalMatrix: 兼容 start_oauth_agent.bat 脚本模式下包名前缀不可用；如果没有这行代码，真实终端入口可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.approval", "learning_agent.computer_use.coordinates", "learning_agent.computer_use.evidence", "learning_agent.computer_use.real_uia_smoke", "learning_agent.computer_use.sendinput_executor", "learning_agent.computer_use.session_runtime", "learning_agent.computer_use.wgc_capture"}:  # 新增代码+Phase42WindowsFinalMatrix: 只允许目标包路径缺失时 fallback；如果没有这行代码，真实内部错误会被误吞。
            raise  # 新增代码+Phase42WindowsFinalMatrix: 重新抛出非路径类导入错误；如果没有这行代码，排查阶段合同 bug 会很困难。
        from computer_use.approval import phase38_cli_line, run_phase38_approval_contract  # 新增代码+Phase42WindowsFinalMatrix: 脚本模式导入 Phase38 合同；如果没有这行代码，bat 入口无法运行总验收。
        from computer_use.coordinates import phase39_cli_line, run_phase39_coordinates_contract  # 新增代码+Phase42WindowsFinalMatrix: 脚本模式导入 Phase39 合同；如果没有这行代码，bat 入口无法运行坐标验收。
        from computer_use.evidence import phase41_cli_line, run_phase41_image_results_contract  # 新增代码+Phase42WindowsFinalMatrix: 脚本模式导入 Phase41 合同；如果没有这行代码，bat 入口无法运行图片结果验收。
        from computer_use.real_uia_smoke import phase35_cli_line, run_phase35_real_uia_smoke  # 新增代码+Phase42WindowsFinalMatrix: 脚本模式导入 Phase35 合同；如果没有这行代码，bat 入口无法运行 UIA 诊断。
        from computer_use.sendinput_executor import phase37_cli_line, run_phase37_sendinput_executor_contract  # 新增代码+Phase42WindowsFinalMatrix: 脚本模式导入 Phase37 合同；如果没有这行代码，bat 入口无法运行 SendInput 合同。
        from computer_use.session_runtime import phase40_cli_line, run_phase40_abort_cleanup_contract  # 新增代码+Phase42WindowsFinalMatrix: 脚本模式导入 Phase40 合同；如果没有这行代码，bat 入口无法运行 runtime 合同。
        from computer_use.wgc_capture import phase36_cli_line, run_phase36_wgc_provider_contract  # 新增代码+Phase42WindowsFinalMatrix: 脚本模式导入 Phase36 合同；如果没有这行代码，bat 入口无法运行 WGC 合同。
    return {"phase35_cli_line": phase35_cli_line, "run_phase35_real_uia_smoke": run_phase35_real_uia_smoke, "phase36_cli_line": phase36_cli_line, "run_phase36_wgc_provider_contract": run_phase36_wgc_provider_contract, "phase37_cli_line": phase37_cli_line, "run_phase37_sendinput_executor_contract": run_phase37_sendinput_executor_contract, "phase38_cli_line": phase38_cli_line, "run_phase38_approval_contract": run_phase38_approval_contract, "phase39_cli_line": phase39_cli_line, "run_phase39_coordinates_contract": run_phase39_coordinates_contract, "phase40_cli_line": phase40_cli_line, "run_phase40_abort_cleanup_contract": run_phase40_abort_cleanup_contract, "phase41_cli_line": phase41_cli_line, "run_phase41_image_results_contract": run_phase41_image_results_contract}  # 新增代码+Phase42WindowsFinalMatrix: 返回所有阶段合同入口；如果没有这行代码，调用方无法统一执行阶段自检。
# 新增代码+Phase42WindowsFinalMatrix: 函数段结束，_phase42_import_contracts 到此结束；如果没有这个结束标记，学习者不容易看出导入边界。


# 新增代码+Phase42WindowsFinalMatrix: 函数段开始，_phase42_matrix_ready 校验矩阵 JSON 基本结构；如果没有这段函数，动态验收可能在矩阵漏项时仍然通过，作者意图是让最终矩阵文件本身也成为门禁。
def _phase42_matrix_ready(matrix: dict[str, Any]) -> bool:  # 新增代码+Phase42WindowsFinalMatrix: 定义矩阵结构检查函数；如果没有这行代码，run 函数会内联复杂条件。
    phases = [entry.get("phase") for entry in matrix.get("phases", []) if isinstance(entry, dict)]  # 新增代码+Phase42WindowsFinalMatrix: 提取阶段编号；如果没有这行代码，无法判断 Phase35-41 是否齐全。
    checks = {entry.get("check") for entry in matrix.get("safe_e2e_checks", []) if isinstance(entry, dict)}  # 新增代码+Phase42WindowsFinalMatrix: 提取 E2E 检查名；如果没有这行代码，无法判断最终场景覆盖面。
    required_checks = {"observe", "evidence", "approval", "gated_refusal", "safe_action", "abort_cleanup", "artifact_visibility"}  # 新增代码+Phase42WindowsFinalMatrix: 定义最终矩阵必须覆盖的能力；如果没有这行代码，漏掉某项也可能过。
    return phases == EXPECTED_PHASE42_PHASES and required_checks.issubset(checks) and matrix.get("acceptance_marker") == PHASE42_WINDOWS_COMPUTER_USE_FINAL_MARKER  # 新增代码+Phase42WindowsFinalMatrix: 返回矩阵是否满足结构门禁；如果没有这行代码，CLI 无法报告 matrix=true/false。
# 新增代码+Phase42WindowsFinalMatrix: 函数段结束，_phase42_matrix_ready 到此结束；如果没有这个结束标记，学习者不容易看出矩阵检查边界。


# 新增代码+Phase42WindowsFinalMatrix: 函数段开始，run_phase42_final_matrix_contract 运行 Phase35-41 安全合同总验收；如果没有这段函数，Phase42 只是静态文件，作者意图是做一个不触碰真实桌面的动态 E2E 安全矩阵。
def run_phase42_final_matrix_contract(matrix_path: Path | str | None = None) -> dict[str, Any]:  # 新增代码+Phase42WindowsFinalMatrix: 定义最终矩阵合同入口；如果没有这行代码，测试和终端场景没有统一自检函数。
    matrix = load_phase42_final_matrix(matrix_path)  # 新增代码+Phase42WindowsFinalMatrix: 读取最终矩阵文件；如果没有这行代码，动态验收不受蓝图约束。
    contracts = _phase42_import_contracts()  # 新增代码+Phase42WindowsFinalMatrix: 加载各阶段合同函数；如果没有这行代码，无法调用 Phase35-41 自检。
    phase35_result = contracts["run_phase35_real_uia_smoke"](module_available=lambda _name: False, platform="win32")  # 新增代码+Phase42WindowsFinalMatrix: 运行 Phase35 依赖诊断安全路径；如果没有这行代码，最终矩阵无法覆盖 UIA smoke 边界且可能打开真实窗口。
    phase35_data = phase35_result.to_dict()  # 新增代码+Phase42WindowsFinalMatrix: 转成字典便于总报告判断；如果没有这行代码，dataclass 字段不便统一处理。
    phase36_report = contracts["run_phase36_wgc_provider_contract"](module_available=lambda _name: False, platform="win32")  # 新增代码+Phase42WindowsFinalMatrix: 运行 Phase36 WGC 合同诊断安全路径；如果没有这行代码，最终矩阵无法覆盖 capture provider 边界。
    phase37_report = contracts["run_phase37_sendinput_executor_contract"](platform="win32")  # 新增代码+Phase42WindowsFinalMatrix: 运行 Phase37 SendInput 合同但默认不启用真实输入；如果没有这行代码，最终矩阵无法覆盖安全动作执行器。
    phase38_report = contracts["run_phase38_approval_contract"]()  # 新增代码+Phase42WindowsFinalMatrix: 运行 Phase38 approval 合同；如果没有这行代码，最终矩阵无法覆盖 allowlist 和 forbidden target。
    phase39_report = contracts["run_phase39_coordinates_contract"]()  # 新增代码+Phase42WindowsFinalMatrix: 运行 Phase39 坐标合同；如果没有这行代码，最终矩阵无法覆盖 DPI/多显示器和窗口状态。
    phase40_report = contracts["run_phase40_abort_cleanup_contract"]()  # 新增代码+Phase42WindowsFinalMatrix: 运行 Phase40 abort/cleanup 合同；如果没有这行代码，最终矩阵无法覆盖 runtime cleanup。
    phase41_report = contracts["run_phase41_image_results_contract"]()  # 新增代码+Phase42WindowsFinalMatrix: 运行 Phase41 图片结果合同；如果没有这行代码，最终矩阵无法覆盖 artifact visibility。
    phase_lines = [contracts["phase35_cli_line"](phase35_result), contracts["phase36_cli_line"](phase36_report), contracts["phase37_cli_line"](phase37_report), contracts["phase38_cli_line"](phase38_report), contracts["phase39_cli_line"](phase39_report), contracts["phase40_cli_line"](phase40_report), contracts["phase41_cli_line"](phase41_report)]  # 新增代码+Phase42WindowsFinalMatrix: 收集每个阶段的稳定 CLI 行；如果没有这行代码，最终报告无法给出可审计 token 证据。
    phase_reports = {"35": phase35_data, "36": phase36_report, "37": phase37_report, "38": phase38_report, "39": phase39_report, "40": phase40_report, "41": phase41_report}  # 新增代码+Phase42WindowsFinalMatrix: 汇总阶段报告；如果没有这行代码，调试失败时不知道哪个阶段掉链子。
    matrix_ready = _phase42_matrix_ready(matrix)  # 新增代码+Phase42WindowsFinalMatrix: 检查矩阵文件是否完整；如果没有这行代码，静态矩阵缺项不会影响结果。
    observe = bool(phase39_report.get("window_state") and phase41_report.get("image_block"))  # 新增代码+Phase42WindowsFinalMatrix: 汇总 observe 覆盖结果；如果没有这行代码，最终报告无法说明只读观察是否成立。
    evidence = bool(phase41_report.get("artifact") and phase41_report.get("image_block"))  # 新增代码+Phase42WindowsFinalMatrix: 汇总 evidence 覆盖结果；如果没有这行代码，截图 artifact 和 image block 可能不在总门禁里。
    approval = bool(phase38_report.get("allowlist") and phase38_report.get("grant_flags"))  # 新增代码+Phase42WindowsFinalMatrix: 汇总 approval 覆盖结果；如果没有这行代码，会话授权成功路径可能漏验。
    gated_refusal = bool(phase38_report.get("forbidden_blocked") and not phase37_report.get("real_input_default"))  # 新增代码+Phase42WindowsFinalMatrix: 汇总门禁拒绝覆盖结果；如果没有这行代码，禁止目标和默认禁用真实输入可能漏验。
    safe_action = bool(phase37_report.get("fake_impl_exercised") and phase37_report.get("raw_text_hidden"))  # 新增代码+Phase42WindowsFinalMatrix: 汇总安全假执行动作覆盖结果；如果没有这行代码，执行器合同可能只检查状态。
    abort_cleanup = bool(phase40_report.get("abort") and phase40_report.get("cleanup") and phase40_report.get("notifications"))  # 新增代码+Phase42WindowsFinalMatrix: 汇总 abort/cleanup 覆盖结果；如果没有这行代码，运行时中断清理不在最终门禁里。
    artifact_visibility = bool(phase41_report.get("agent_artifact") and phase41_report.get("sensitive_text_hidden"))  # 新增代码+Phase42WindowsFinalMatrix: 汇总 artifact 可见和脱敏结果；如果没有这行代码，Phase41 成果可能漏验。
    actions_expanded = any(bool(report.get("actions_expanded", False)) for report in phase_reports.values())  # 新增代码+Phase42WindowsFinalMatrix: 汇总阶段是否扩大动作面；如果没有这行代码，某个阶段误改安全边界不会反映到最终报告。
    passed = bool(matrix_ready and observe and evidence and approval and gated_refusal and safe_action and abort_cleanup and artifact_visibility and not actions_expanded)  # 新增代码+Phase42WindowsFinalMatrix: 汇总最终通过条件；如果没有这行代码，main 无法设置正确退出码。
    return {"marker": PHASE42_WINDOWS_COMPUTER_USE_FINAL_MARKER, "ok_token": PHASE42_WINDOWS_COMPUTER_USE_FINAL_OK_TOKEN, "model": PHASE42_MATRIX_MODEL, "phase_count": len(phase_reports), "matrix_ready": matrix_ready, "observe": observe, "evidence": evidence, "approval": approval, "gated_refusal": gated_refusal, "safe_action": safe_action, "abort_cleanup": abort_cleanup, "artifact_visibility": artifact_visibility, "actions_expanded": actions_expanded or PHASE42_ACTIONS_EXPANDED, "passed": passed, "phase_lines": phase_lines, "phase_reports": phase_reports}  # 新增代码+Phase42WindowsFinalMatrix: 返回最终矩阵报告；如果没有这行代码，CLI 和测试拿不到结构化结果。
# 新增代码+Phase42WindowsFinalMatrix: 函数段结束，run_phase42_final_matrix_contract 到此结束；如果没有这个结束标记，学习者不容易看出总验收边界。


# 新增代码+Phase42WindowsFinalMatrix: 函数段开始，phase42_cli_line 把最终报告转成一行稳定 token；如果没有这段函数，真实终端场景需要解析复杂 JSON，作者意图是让最终回答可复制可验收。
def phase42_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase42WindowsFinalMatrix: 定义最终 CLI 行格式化函数；如果没有这行代码，main 无法打印固定顺序 token。
    return f"{PHASE42_WINDOWS_COMPUTER_USE_FINAL_MARKER} {PHASE42_WINDOWS_COMPUTER_USE_FINAL_OK_TOKEN} phase_count={int(report.get('phase_count', 0) or 0)} matrix={_bool_token(report.get('matrix_ready'))} observe={_bool_token(report.get('observe'))} evidence={_bool_token(report.get('evidence'))} approval={_bool_token(report.get('approval'))} gated_refusal={_bool_token(report.get('gated_refusal'))} safe_action={_bool_token(report.get('safe_action'))} abort_cleanup={_bool_token(report.get('abort_cleanup'))} artifact_visibility={_bool_token(report.get('artifact_visibility'))} actions_expanded={_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase42WindowsFinalMatrix: 返回固定顺序最终 token 行；如果没有这行代码，验收器无法稳定匹配输出。
# 新增代码+Phase42WindowsFinalMatrix: 函数段结束，phase42_cli_line 到此结束；如果没有这个结束标记，学习者不容易看出最终 CLI 文本边界。


# 新增代码+Phase42WindowsFinalMatrix: 函数段开始，main 提供真实终端可调用入口；如果没有这段函数，Phase42 场景无法让 agent 执行最终矩阵自检，作者意图是让自动化和可见终端共用同一合同。
def main() -> int:  # 新增代码+Phase42WindowsFinalMatrix: 定义命令行入口；如果没有这行代码，python -c 只能手写调用细节。
    report = run_phase42_final_matrix_contract()  # 新增代码+Phase42WindowsFinalMatrix: 运行最终矩阵合同；如果没有这行代码，CLI 输出没有真实依据。
    print(PHASE42_WINDOWS_COMPUTER_USE_FINAL_MARKER)  # 新增代码+Phase42WindowsFinalMatrix: 打印 ready marker；如果没有这行代码，可见终端 controller 可能不知道何时检测成功。
    print(phase42_cli_line(report))  # 新增代码+Phase42WindowsFinalMatrix: 打印固定 token 行；如果没有这行代码，用户无法复制最终验收结果。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase42WindowsFinalMatrix: 根据合同结果返回退出码；如果没有这行代码，失败也会被终端当成成功。
# 新增代码+Phase42WindowsFinalMatrix: 函数段结束，main 到此结束；如果没有这个结束标记，学习者不容易看出命令行入口边界。


if __name__ == "__main__":  # 新增代码+Phase42WindowsFinalMatrix: 允许直接运行本模块文件；如果没有这行代码，初学者无法手动执行 Phase42 自检。
    raise SystemExit(main())  # 新增代码+Phase42WindowsFinalMatrix: 调用 main 并传递退出码；如果没有这行代码，直接运行不会执行验收。
