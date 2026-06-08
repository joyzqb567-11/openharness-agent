"""Windows Computer Use Phase52 生产级总矩阵。"""  # 新增代码+Phase52WindowsProductionMatrix: 标明本文件负责汇总 Phase43-51 的生产级门禁；如果没有这行代码，读者不知道最终验收入口在哪里。
from __future__ import annotations  # 新增代码+Phase52WindowsProductionMatrix: 启用延迟类型解析；如果没有这行代码，旧 Python 路径遇到前向类型注解时更容易导入失败。
import json  # 新增代码+Phase52WindowsProductionMatrix: 导入 JSON 工具用于 CLI 打印结构化报告；如果没有这行代码，失败时不容易复盘每个阶段的明细。
from typing import Any  # 新增代码+Phase52WindowsProductionMatrix: 导入 Any 描述各阶段动态报告；如果没有这行代码，函数边界会缺少清晰的类型提示。

PHASE52_WINDOWS_PRODUCTION_MATRIX_MARKER = "PHASE52_WINDOWS_PRODUCTION_MATRIX_READY"  # 新增代码+Phase52WindowsProductionMatrix: 定义 Phase52 ready marker；如果没有这行代码，真实终端验收没有稳定等待锚点。
PHASE52_WINDOWS_PRODUCTION_MATRIX_OK_TOKEN = "PHASE52_WINDOWS_PRODUCTION_MATRIX_OK"  # 新增代码+Phase52WindowsProductionMatrix: 定义 Phase52 OK token；如果没有这行代码，日志无法区分总矩阵通过和普通输出。
PHASE52_PRODUCTION_MATRIX_MODEL = "phase52_windows_production_matrix"  # 新增代码+Phase52WindowsProductionMatrix: 定义总矩阵模型名；如果没有这行代码，报告无法说明当前使用哪套总验收规则。
PHASE52_ACTIONS_EXPANDED = False  # 新增代码+Phase52WindowsProductionMatrix: 明确 Phase52 自身不扩大生产默认动作面；如果没有这行代码，用户可能误以为最终矩阵又放开了新动作。
PHASE52_EXPECTED_PHASE_COUNT = 9  # 新增代码+Phase52WindowsProductionMatrix: 固定 Phase43-51 一共九个阶段；如果没有这行代码，漏跑阶段也可能被误判为完整。

# 新增代码+Phase52WindowsProductionMatrix: 函数段开始，_bool_token 把布尔值转成验收器稳定匹配的小写 token；如果没有这段函数，CLI 输出可能混用 True/False 和 true/false，作者意图是让真实终端断言稳定。
def _bool_token(value: Any) -> str:  # 新增代码+Phase52WindowsProductionMatrix: 定义布尔 token helper；如果没有这行代码，多处输出会重复写转换逻辑。
    return "true" if bool(value) else "false"  # 新增代码+Phase52WindowsProductionMatrix: 返回小写布尔文本；如果没有这行代码，场景 JSON 的 token 匹配可能失败。
# 新增代码+Phase52WindowsProductionMatrix: 函数段结束，_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。

# 新增代码+Phase52WindowsProductionMatrix: 函数段开始，_phase52_import_contracts 延迟导入 Phase43-51 合同；如果没有这段函数，模块导入时会急切加载所有阶段并增加循环依赖风险，作者意图是只在总验收运行时加载依赖。
def _phase52_import_contracts() -> dict[str, Any]:  # 新增代码+Phase52WindowsProductionMatrix: 定义合同导入 helper；如果没有这行代码，run 函数会堆满重复导入代码。
    try:  # 新增代码+Phase52WindowsProductionMatrix: 优先按 learning_agent 包模式导入；如果没有这行代码，正常 unittest 和项目根目录运行无法加载阶段合同。
        from learning_agent.app.computer_status_renderer import phase51_cli_line, run_phase51_computer_status_ui_contract  # 新增代码+Phase52WindowsProductionMatrix: 导入 Phase51 状态 UI 合同；如果没有这行代码，总矩阵无法覆盖终端状态面板。
        from learning_agent.computer_use.native_diagnostics import phase43_cli_line, run_phase43_native_capability_matrix_contract  # 新增代码+Phase52WindowsProductionMatrix: 导入 Phase43 原生能力矩阵合同；如果没有这行代码，总矩阵无法覆盖诊断层。
        from learning_agent.computer_use.native_host import phase44_cli_line, run_phase44_native_host_contract  # 新增代码+Phase52WindowsProductionMatrix: 导入 Phase44 native host 合同；如果没有这行代码，总矩阵无法覆盖 host 协议。
        from learning_agent.computer_use.screenshot_runtime import phase45_cli_line, run_phase45_screenshot_runtime_contract  # 新增代码+Phase52WindowsProductionMatrix: 导入 Phase45 截图 runtime 合同；如果没有这行代码，总矩阵无法覆盖截图和 artifact。
        from learning_agent.computer_use.security_policy import phase48_cli_line, run_phase48_security_policy_contract  # 新增代码+Phase52WindowsProductionMatrix: 导入 Phase48 安全策略合同；如果没有这行代码，总矩阵无法覆盖授权和高风险默认拒绝。
        from learning_agent.computer_use.sendinput_dispatcher import phase47_cli_line, run_phase47_sendinput_dispatcher_contract  # 新增代码+Phase52WindowsProductionMatrix: 导入 Phase47 SendInput dispatcher 合同；如果没有这行代码，总矩阵无法覆盖动作分发器。
        from learning_agent.computer_use.session_runtime import phase50_cli_line, run_phase50_recovery_contract  # 新增代码+Phase52WindowsProductionMatrix: 导入 Phase50 恢复 runtime 合同；如果没有这行代码，总矩阵无法覆盖 stale lock 和 journal。
        from learning_agent.computer_use.tool_surface import phase49_cli_line, run_phase49_tool_surface_contract  # 新增代码+Phase52WindowsProductionMatrix: 导入 Phase49 工具面合同；如果没有这行代码，总矩阵无法覆盖兼容工具入口。
        from learning_agent.computer_use.uia_tree import phase46_cli_line, run_phase46_uia_tree_contract  # 新增代码+Phase52WindowsProductionMatrix: 导入 Phase46 UIA tree 合同；如果没有这行代码，总矩阵无法覆盖控件树观察。
    except ModuleNotFoundError as error:  # 新增代码+Phase52WindowsProductionMatrix: 兼容 start_oauth_agent.bat 从 learning_agent 目录运行时包前缀不可用；如果没有这行代码，真实终端入口可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.app", "learning_agent.app.computer_status_renderer", "learning_agent.computer_use", "learning_agent.computer_use.native_diagnostics", "learning_agent.computer_use.native_host", "learning_agent.computer_use.screenshot_runtime", "learning_agent.computer_use.security_policy", "learning_agent.computer_use.sendinput_dispatcher", "learning_agent.computer_use.session_runtime", "learning_agent.computer_use.tool_surface", "learning_agent.computer_use.uia_tree"}:  # 新增代码+Phase52WindowsProductionMatrix: 只允许目标包路径缺失时 fallback；如果没有这行代码，真实内部 bug 会被误吞。
            raise  # 新增代码+Phase52WindowsProductionMatrix: 重新抛出非路径类导入错误；如果没有这行代码，排查阶段合同 bug 会很困难。
        from app.computer_status_renderer import phase51_cli_line, run_phase51_computer_status_ui_contract  # 新增代码+Phase52WindowsProductionMatrix: 脚本模式导入 Phase51 合同；如果没有这行代码，bat 入口无法运行状态 UI 总验收。
        from computer_use.native_diagnostics import phase43_cli_line, run_phase43_native_capability_matrix_contract  # 新增代码+Phase52WindowsProductionMatrix: 脚本模式导入 Phase43 合同；如果没有这行代码，bat 入口无法运行原生能力总验收。
        from computer_use.native_host import phase44_cli_line, run_phase44_native_host_contract  # 新增代码+Phase52WindowsProductionMatrix: 脚本模式导入 Phase44 合同；如果没有这行代码，bat 入口无法运行 native host 总验收。
        from computer_use.screenshot_runtime import phase45_cli_line, run_phase45_screenshot_runtime_contract  # 新增代码+Phase52WindowsProductionMatrix: 脚本模式导入 Phase45 合同；如果没有这行代码，bat 入口无法运行截图 runtime 总验收。
        from computer_use.security_policy import phase48_cli_line, run_phase48_security_policy_contract  # 新增代码+Phase52WindowsProductionMatrix: 脚本模式导入 Phase48 合同；如果没有这行代码，bat 入口无法运行安全策略总验收。
        from computer_use.sendinput_dispatcher import phase47_cli_line, run_phase47_sendinput_dispatcher_contract  # 新增代码+Phase52WindowsProductionMatrix: 脚本模式导入 Phase47 合同；如果没有这行代码，bat 入口无法运行 dispatcher 总验收。
        from computer_use.session_runtime import phase50_cli_line, run_phase50_recovery_contract  # 新增代码+Phase52WindowsProductionMatrix: 脚本模式导入 Phase50 合同；如果没有这行代码，bat 入口无法运行恢复 runtime 总验收。
        from computer_use.tool_surface import phase49_cli_line, run_phase49_tool_surface_contract  # 新增代码+Phase52WindowsProductionMatrix: 脚本模式导入 Phase49 合同；如果没有这行代码，bat 入口无法运行工具面总验收。
        from computer_use.uia_tree import phase46_cli_line, run_phase46_uia_tree_contract  # 新增代码+Phase52WindowsProductionMatrix: 脚本模式导入 Phase46 合同；如果没有这行代码，bat 入口无法运行 UIA tree 总验收。
    return {"phase43_cli_line": phase43_cli_line, "run_phase43_native_capability_matrix_contract": run_phase43_native_capability_matrix_contract, "phase44_cli_line": phase44_cli_line, "run_phase44_native_host_contract": run_phase44_native_host_contract, "phase45_cli_line": phase45_cli_line, "run_phase45_screenshot_runtime_contract": run_phase45_screenshot_runtime_contract, "phase46_cli_line": phase46_cli_line, "run_phase46_uia_tree_contract": run_phase46_uia_tree_contract, "phase47_cli_line": phase47_cli_line, "run_phase47_sendinput_dispatcher_contract": run_phase47_sendinput_dispatcher_contract, "phase48_cli_line": phase48_cli_line, "run_phase48_security_policy_contract": run_phase48_security_policy_contract, "phase49_cli_line": phase49_cli_line, "run_phase49_tool_surface_contract": run_phase49_tool_surface_contract, "phase50_cli_line": phase50_cli_line, "run_phase50_recovery_contract": run_phase50_recovery_contract, "phase51_cli_line": phase51_cli_line, "run_phase51_computer_status_ui_contract": run_phase51_computer_status_ui_contract}  # 新增代码+Phase52WindowsProductionMatrix: 返回所有阶段合同入口；如果没有这行代码，调用方无法统一执行 Phase43-51 自检。
# 新增代码+Phase52WindowsProductionMatrix: 函数段结束，_phase52_import_contracts 到此结束；如果没有这个边界说明，初学者不容易看出导入兼容层范围。

# 新增代码+Phase52WindowsProductionMatrix: 函数段开始，run_phase52_production_matrix_contract 汇总 Phase43-51 合同；如果没有这段函数，Phase52 只是静态文件，作者意图是做一个可由自动化和真实终端共同调用的生产总门禁。
def run_phase52_production_matrix_contract() -> dict[str, Any]:  # 新增代码+Phase52WindowsProductionMatrix: 定义 Phase52 总合同入口；如果没有这行代码，测试和终端场景没有统一自检函数。
    contracts = _phase52_import_contracts()  # 新增代码+Phase52WindowsProductionMatrix: 加载各阶段合同函数；如果没有这行代码，后续无法调用 Phase43-51 自检。
    phase43_report = contracts["run_phase43_native_capability_matrix_contract"]()  # 新增代码+Phase52WindowsProductionMatrix: 运行 Phase43 原生能力矩阵；如果没有这行代码，总矩阵无法确认诊断层仍可用。
    phase44_report = contracts["run_phase44_native_host_contract"]()  # 新增代码+Phase52WindowsProductionMatrix: 运行 Phase44 native host 合同；如果没有这行代码，总矩阵无法确认 host 协议仍可用。
    phase45_report = contracts["run_phase45_screenshot_runtime_contract"]()  # 新增代码+Phase52WindowsProductionMatrix: 运行 Phase45 截图 runtime 合同；如果没有这行代码，总矩阵无法确认截图和 evidence 仍可用。
    phase46_report = contracts["run_phase46_uia_tree_contract"]()  # 新增代码+Phase52WindowsProductionMatrix: 运行 Phase46 UIA tree 合同；如果没有这行代码，总矩阵无法确认控件树观察仍可用。
    phase47_report = contracts["run_phase47_sendinput_dispatcher_contract"]()  # 新增代码+Phase52WindowsProductionMatrix: 运行 Phase47 dispatcher 合同；如果没有这行代码，总矩阵无法确认动作分发层仍可用。
    phase48_report = contracts["run_phase48_security_policy_contract"]()  # 新增代码+Phase52WindowsProductionMatrix: 运行 Phase48 安全策略合同；如果没有这行代码，总矩阵无法确认授权和拒绝门禁仍可用。
    phase49_report = contracts["run_phase49_tool_surface_contract"]()  # 新增代码+Phase52WindowsProductionMatrix: 运行 Phase49 工具面合同；如果没有这行代码，总矩阵无法确认兼容工具名仍可用。
    phase50_report = contracts["run_phase50_recovery_contract"]()  # 新增代码+Phase52WindowsProductionMatrix: 运行 Phase50 恢复 runtime 合同；如果没有这行代码，总矩阵无法确认 stale/cleanup/journal 仍可用。
    phase51_report = contracts["run_phase51_computer_status_ui_contract"]()  # 新增代码+Phase52WindowsProductionMatrix: 运行 Phase51 终端状态 UI 合同；如果没有这行代码，总矩阵无法确认可见状态面板仍可用。
    phase_reports = {"43": phase43_report, "44": phase44_report, "45": phase45_report, "46": phase46_report, "47": phase47_report, "48": phase48_report, "49": phase49_report, "50": phase50_report, "51": phase51_report}  # 新增代码+Phase52WindowsProductionMatrix: 汇总所有阶段报告；如果没有这行代码，失败时不知道哪个阶段掉链子。
    phase_lines = [contracts["phase43_cli_line"](phase43_report), contracts["phase44_cli_line"](phase44_report), contracts["phase45_cli_line"](phase45_report), contracts["phase46_cli_line"](phase46_report), contracts["phase47_cli_line"](phase47_report), contracts["phase48_cli_line"](phase48_report), contracts["phase49_cli_line"](phase49_report), contracts["phase50_cli_line"](phase50_report), contracts["phase51_cli_line"](phase51_report)]  # 新增代码+Phase52WindowsProductionMatrix: 收集每个阶段的稳定 CLI token 行；如果没有这行代码，总报告缺少可审计证据。
    native_capability = bool(phase43_report.get("capability_matrix") and phase43_report.get("status_fields"))  # 新增代码+Phase52WindowsProductionMatrix: 汇总 Phase43 是否通过；如果没有这行代码，总矩阵无法发现原生诊断层缺口。
    native_host = bool(phase44_report.get("health") and phase44_report.get("messages") and phase44_report.get("safe_action_refused"))  # 新增代码+Phase52WindowsProductionMatrix: 汇总 Phase44 是否通过；如果没有这行代码，host 协议和安全拒绝可能漏验。
    screenshot_runtime = bool(phase45_report.get("capture") and phase45_report.get("artifact") and phase45_report.get("fallback") and phase45_report.get("host_capture") and phase45_report.get("raw_bytes_hidden"))  # 新增代码+Phase52WindowsProductionMatrix: 汇总 Phase45 是否通过；如果没有这行代码，截图、artifact、fallback 和脱敏可能漏验。
    uia_tree = bool(phase46_report.get("tree") and phase46_report.get("bounds") and phase46_report.get("controls") and phase46_report.get("redacted") and phase46_report.get("host_observe"))  # 新增代码+Phase52WindowsProductionMatrix: 汇总 Phase46 是否通过；如果没有这行代码，控件树、坐标和脱敏可能漏验。
    sendinput_dispatcher = bool(phase47_report.get("dispatch") and phase47_report.get("all_actions") and phase47_report.get("target_check") and phase47_report.get("host_action") and phase47_report.get("raw_text_hidden"))  # 新增代码+Phase52WindowsProductionMatrix: 汇总 Phase47 是否通过；如果没有这行代码，动作分发、目标校验和文本脱敏可能漏验。
    security_policy = bool(phase48_report.get("grant_classes") and phase48_report.get("high_risk_default") and phase48_report.get("clipboard") and phase48_report.get("controller_policy") and phase48_report.get("terminal_status"))  # 新增代码+Phase52WindowsProductionMatrix: 汇总 Phase48 是否通过；如果没有这行代码，安全策略缺口可能被隐藏。
    tool_surface = bool(phase49_report.get("legacy_tools") and phase49_report.get("compat_tools") and phase49_report.get("same_controller") and phase49_report.get("catalog"))  # 新增代码+Phase52WindowsProductionMatrix: 汇总 Phase49 是否通过；如果没有这行代码，兼容工具入口可能漏验。
    recovery_runtime = bool(phase50_report.get("stale_recovered") and phase50_report.get("cleanup_state") and phase50_report.get("action_journal") and phase50_report.get("terminal_commands"))  # 新增代码+Phase52WindowsProductionMatrix: 汇总 Phase50 是否通过；如果没有这行代码，恢复和审计日志可能漏验。
    status_ui = bool(phase51_report.get("summary") and phase51_report.get("next_command") and phase51_report.get("commands") and phase51_report.get("grant_revoke"))  # 新增代码+Phase52WindowsProductionMatrix: 汇总 Phase51 是否通过；如果没有这行代码，终端 UI 可见性可能漏验。
    dispatcher_actions_expanded = bool(phase47_report.get("actions_expanded"))  # 新增代码+Phase52WindowsProductionMatrix: 记录 Phase47 已经扩展动作分发器这一事实；如果没有这行代码，Phase52 会丢失对既有动作面的审计信息。
    actions_expanded = bool(PHASE52_ACTIONS_EXPANDED)  # 新增代码+Phase52WindowsProductionMatrix: 表示 Phase52 自身没有新增生产默认动作面；如果没有这行代码，最终 token 的安全语义不稳定。
    phase_count = len(phase_reports)  # 新增代码+Phase52WindowsProductionMatrix: 计算实际覆盖阶段数；如果没有这行代码，少跑阶段无法进入总门禁判断。
    passed = bool(phase_count == PHASE52_EXPECTED_PHASE_COUNT and native_capability and native_host and screenshot_runtime and uia_tree and sendinput_dispatcher and security_policy and tool_surface and recovery_runtime and status_ui and dispatcher_actions_expanded and not actions_expanded)  # 新增代码+Phase52WindowsProductionMatrix: 汇总最终通过条件；如果没有这行代码，main 无法用退出码表达总矩阵成功或失败。
    return {"marker": PHASE52_WINDOWS_PRODUCTION_MATRIX_MARKER, "ok_token": PHASE52_WINDOWS_PRODUCTION_MATRIX_OK_TOKEN, "model": PHASE52_PRODUCTION_MATRIX_MODEL, "phase_count": phase_count, "native_capability": native_capability, "native_host": native_host, "screenshot_runtime": screenshot_runtime, "uia_tree": uia_tree, "sendinput_dispatcher": sendinput_dispatcher, "security_policy": security_policy, "tool_surface": tool_surface, "recovery_runtime": recovery_runtime, "status_ui": status_ui, "dispatcher_actions_expanded": dispatcher_actions_expanded, "actions_expanded": actions_expanded, "passed": passed, "phase_lines": phase_lines, "phase_reports": phase_reports}  # 新增代码+Phase52WindowsProductionMatrix: 返回完整总矩阵报告；如果没有这行代码，CLI 和测试拿不到结构化结果。
# 新增代码+Phase52WindowsProductionMatrix: 函数段结束，run_phase52_production_matrix_contract 到此结束；如果没有这个边界说明，初学者不容易看出总验收运行范围。

# 新增代码+Phase52WindowsProductionMatrix: 函数段开始，phase52_cli_line 把总报告转成一行稳定 token；如果没有这段函数，真实终端场景需要解析复杂 JSON，作者意图是让最终回答可复制可验收。
def phase52_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase52WindowsProductionMatrix: 定义 Phase52 CLI 行格式化函数；如果没有这行代码，main 无法打印固定顺序 token。
    return f"{PHASE52_WINDOWS_PRODUCTION_MATRIX_OK_TOKEN} phase_count={int(report.get('phase_count', 0) or 0)} native_capability={_bool_token(report.get('native_capability'))} native_host={_bool_token(report.get('native_host'))} screenshot_runtime={_bool_token(report.get('screenshot_runtime'))} uia_tree={_bool_token(report.get('uia_tree'))} sendinput_dispatcher={_bool_token(report.get('sendinput_dispatcher'))} security_policy={_bool_token(report.get('security_policy'))} tool_surface={_bool_token(report.get('tool_surface'))} recovery_runtime={_bool_token(report.get('recovery_runtime'))} status_ui={_bool_token(report.get('status_ui'))} dispatcher_actions_expanded={_bool_token(report.get('dispatcher_actions_expanded'))} actions_expanded={_bool_token(report.get('actions_expanded'))} marker={PHASE52_WINDOWS_PRODUCTION_MATRIX_MARKER}"  # 新增代码+Phase52WindowsProductionMatrix: 返回固定顺序 token 行；如果没有这行代码，场景断言容易因为输出漂移失败。
# 新增代码+Phase52WindowsProductionMatrix: 函数段结束，phase52_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 文本范围。

# 新增代码+Phase52WindowsProductionMatrix: 函数段开始，main 提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase52 总矩阵，作者意图是自动化和可见终端共用同一合同。
def main() -> int:  # 新增代码+Phase52WindowsProductionMatrix: 定义命令行入口；如果没有这行代码，python -c 只能手写调用细节。
    report = run_phase52_production_matrix_contract()  # 新增代码+Phase52WindowsProductionMatrix: 运行 Phase52 总矩阵合同；如果没有这行代码，CLI 输出没有真实依据。
    print(phase52_cli_line(report))  # 新增代码+Phase52WindowsProductionMatrix: 打印稳定单行 token；如果没有这行代码，验收器无法快速匹配总结果。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase52WindowsProductionMatrix: 打印结构化报告便于人工复盘；如果没有这行代码，失败时不容易定位哪一阶段失败。
    print(PHASE52_WINDOWS_PRODUCTION_MATRIX_MARKER)  # 新增代码+Phase52WindowsProductionMatrix: 单独打印 ready marker；如果没有这行代码，真实终端验收可能看不到明确阶段标记。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase52WindowsProductionMatrix: 根据总合同结果返回退出码；如果没有这行代码，失败也可能被终端当成成功。
# 新增代码+Phase52WindowsProductionMatrix: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。

if __name__ == "__main__":  # 新增代码+Phase52WindowsProductionMatrix: 允许直接运行本模块；如果没有这行代码，初学者无法用 python 文件方式手动执行 Phase52 自检。
    raise SystemExit(main())  # 新增代码+Phase52WindowsProductionMatrix: 调用 main 并传递退出码；如果没有这行代码，直接运行文件不会执行验收。
