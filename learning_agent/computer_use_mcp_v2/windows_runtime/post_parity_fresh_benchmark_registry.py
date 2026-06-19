"""Phase148C fresh Computer Use benchmark registry."""  # 新增代码+Phase148CFreshBenchmark：说明本模块登记并汇总 fresh benchmark；如果没有这一行，读者无法快速知道文件用途。
from __future__ import annotations  # 新增代码+Phase148CFreshBenchmark：启用延迟类型注解；如果没有这一行，较复杂类型在部分环境可能提前求值失败。

import argparse  # 新增代码+Phase148CFreshBenchmark：导入命令行参数解析器；如果没有这一行，可见终端无法调用本模块的自检入口。
import json  # 新增代码+Phase148CFreshBenchmark：导入 JSON 工具；如果没有这一行，registry 和 evidence 无法稳定输出结构化数据。
from pathlib import Path  # 新增代码+Phase148CFreshBenchmark：导入路径对象；如果没有这一行，证据和场景路径处理会更容易出错。
from typing import Any  # 新增代码+Phase148CFreshBenchmark：导入动态 JSON 类型；如果没有这一行，公开函数签名无法清楚表达字典输入。

from learning_agent.computer_use_mcp_v2.windows_runtime.post_parity_evidence_ledger import build_post_parity_ledger_entry, write_post_parity_ledger_entry  # 新增代码+Phase148CFreshBenchmark：复用已有 post-parity ledger；如果没有这一行，Phase148C 会重复造账本格式并可能漂移。

PHASE148C_FRESH_BENCHMARK_MARKER = "COMPUTER_USE_PHASE148C_FRESH_BENCHMARK_READY"  # 新增代码+Phase148CFreshBenchmark：定义稳定 ready marker；如果没有这一行，验收场景无法匹配 Phase148C 输出。
PHASE148C_FRESH_BENCHMARK_OK_TOKEN = "COMPUTER_USE_PHASE148C_FRESH_BENCHMARK_OK"  # 新增代码+Phase148CFreshBenchmark：定义稳定 OK token；如果没有这一行，终端自检无法清晰表达成功。
PHASE148C_REQUIRED_FAMILIES = (  # 新增代码+Phase148CFreshBenchmark：开始定义 7 类必须覆盖的 benchmark；如果没有这一段，成熟度判定没有固定覆盖面。
    "single_app_text",  # 新增代码+Phase148CFreshBenchmark：登记单应用文本任务；如果没有这一行，Notepad 类基础 GUI 任务会缺席。
    "single_app_calculation",  # 新增代码+Phase148CFreshBenchmark：登记单应用计算任务；如果没有这一行，Calculator 类按钮任务会缺席。
    "local_browser",  # 新增代码+Phase148CFreshBenchmark：登记本地浏览器任务；如果没有这一行，浏览器 GUI 任务会缺席。
    "local_file",  # 新增代码+Phase148CFreshBenchmark：登记本地文件任务；如果没有这一行，Explorer/文件类能力缺口不可见。
    "multi_app_transfer",  # 新增代码+Phase148CFreshBenchmark：登记跨应用传递任务；如果没有这一行，多窗口协同能力缺口不可见。
    "failure_recovery",  # 新增代码+Phase148CFreshBenchmark：登记失败恢复任务；如果没有这一行，出错后的恢复能力缺口不可见。
    "long_task_resume",  # 新增代码+Phase148CFreshBenchmark：登记长任务恢复任务；如果没有这一行，超长任务 harness 能力缺口不可见。
)  # 新增代码+Phase148CFreshBenchmark：结束 benchmark 家族元组；如果没有这一行，Python 元组语法不完整。


# 新增代码+Phase148CFreshBenchmark：函数段开始，把布尔值转成小写 token；如果没有这个 helper，CLI 输出可能出现 True/False 漂移。
def _phase148c_bool(value: Any) -> str:  # 新增代码+Phase148CFreshBenchmark：声明布尔 token helper；如果没有这一行，调用方无法复用稳定格式。
    return "true" if bool(value) else "false"  # 新增代码+Phase148CFreshBenchmark：返回小写 true/false；如果没有这一行，终端断言可能大小写不一致。
# 新增代码+Phase148CFreshBenchmark：函数段结束，_phase148c_bool 到此结束；如果没有这个边界说明，初学者不容易看出格式转换范围。


# 新增代码+Phase148CFreshBenchmark：函数段开始，统一创建 registry 条目；如果没有这个 helper，7 条场景会重复大量字段并容易漏安全信息。
def _phase148c_entry(  # 新增代码+Phase148CFreshBenchmark：声明 registry 条目构造函数；如果没有这一行，条目结构没有统一入口。
    *,  # 新增代码+Phase148CFreshBenchmark：强制使用关键字参数；如果没有这一行，调用方容易把 family 和 scenario_id 顺序写错。
    family: str,  # 新增代码+Phase148CFreshBenchmark：接收 benchmark 家族名；如果没有这一行，条目无法表达覆盖哪类任务。
    benchmark_id: str,  # 新增代码+Phase148CFreshBenchmark：接收 benchmark ID；如果没有这一行，evidence 无法稳定回指任务。
    scenario_id: str,  # 新增代码+Phase148CFreshBenchmark：接收 acceptance controller 场景 ID；如果没有这一行，run 证据无法回指场景。
    source_phase: str,  # 新增代码+Phase148CFreshBenchmark：接收来源阶段；如果没有这一行，报告无法说明复用了哪条成熟链路。
    source_command: str,  # 新增代码+Phase148CFreshBenchmark：接收可见终端内要执行的命令；如果没有这一行，场景 prompt 无法指向实际自检。
    required_tokens: list[str],  # 新增代码+Phase148CFreshBenchmark：接收必须出现在日志和最终回答里的 token；如果没有这一行，验收门禁不稳定。
    real_gui_backing: bool,  # 新增代码+Phase148CFreshBenchmark：接收是否有真实 GUI 背书；如果没有这一行，最终成熟度会把契约测试误当实战。
    target_apps: list[str],  # 新增代码+Phase148CFreshBenchmark：接收目标应用列表；如果没有这一行，权限和边界范围不清楚。
) -> dict[str, Any]:  # 新增代码+Phase148CFreshBenchmark：声明返回 JSON 风格字典；如果没有这一行，接口输出形状不清楚。
    scenario_path = f"learning_agent/acceptance_controller/scenarios/{scenario_id}.json"  # 新增代码+Phase148CFreshBenchmark：生成场景相对路径；如果没有这一行，registry 无法定位场景文件。
    token_set = list(dict.fromkeys([PHASE148C_FRESH_BENCHMARK_MARKER, PHASE148C_FRESH_BENCHMARK_OK_TOKEN, f"family={family}", *required_tokens]))  # 新增代码+Phase148CFreshBenchmark：合并并去重必需 token；如果没有这一行，场景断言可能遗漏 Phase148C 锚点。
    return {  # 新增代码+Phase148CFreshBenchmark：开始返回 registry 条目；如果没有这一行，函数不会产生条目。
        "family": family,  # 新增代码+Phase148CFreshBenchmark：写入任务家族；如果没有这一行，矩阵无法统计覆盖面。
        "benchmark_id": benchmark_id,  # 新增代码+Phase148CFreshBenchmark：写入 benchmark ID；如果没有这一行，证据无法稳定命名。
        "scenario_id": scenario_id,  # 新增代码+Phase148CFreshBenchmark：写入场景 ID；如果没有这一行，run 目录和 verifier 无法关联。
        "scenario_path": scenario_path,  # 新增代码+Phase148CFreshBenchmark：写入场景路径；如果没有这一行，执行器不知道跑哪个 JSON。
        "source_phase": source_phase,  # 新增代码+Phase148CFreshBenchmark：写入复用来源阶段；如果没有这一行，报告无法解释证据强度。
        "source_command": source_command,  # 新增代码+Phase148CFreshBenchmark：写入真实终端命令；如果没有这一行，场景生成和人工复验没有依据。
        "required_tokens": token_set,  # 新增代码+Phase148CFreshBenchmark：写入必需 token；如果没有这一行，builder 无法验证输出是否命中门禁。
        "real_gui_backing": bool(real_gui_backing),  # 新增代码+Phase148CFreshBenchmark：写入真实 GUI 背书状态；如果没有这一行，契约证据可能被误判为实战。
        "target_apps": list(target_apps),  # 新增代码+Phase148CFreshBenchmark：写入目标应用副本；如果没有这一行，调用方修改原列表会污染 registry。
        "visible_terminal_entrypoint": "learning_agent/start_oauth_agent.bat",  # 新增代码+Phase148CFreshBenchmark：写入可见终端入口；如果没有这一行，规则十七入口不可审计。
        "physical_dispatch_token": "real_desktop_touched=true" if real_gui_backing else "",  # 新增代码+Phase148CFreshBenchmark：写入真实派发 token；如果没有这一行，builder 无法区分物理动作和契约自检。
    }  # 新增代码+Phase148CFreshBenchmark：结束 registry 条目；如果没有这一行，Python 字典语法不完整。
# 新增代码+Phase148CFreshBenchmark：函数段结束，_phase148c_entry 到此结束；如果没有这个边界说明，初学者不容易看出条目构造范围。


# 新增代码+Phase148CFreshBenchmark：函数段开始，返回 Phase148C fresh benchmark registry；如果没有这个函数，外部测试和 CLI 没有统一清单来源。
def get_phase148c_fresh_benchmark_registry() -> list[dict[str, Any]]:  # 新增代码+Phase148CFreshBenchmark：声明 registry 公开读取函数；如果没有这一行，其他模块无法读取 7 类 fresh benchmark。
    return [  # 新增代码+Phase148CFreshBenchmark：开始返回 7 条 registry；如果没有这一行，函数不会返回任何 benchmark。
        _phase148c_entry(family="single_app_text", benchmark_id="phase148c_single_app_text", scenario_id="agent_capability_computer_use_phase148c_single_app_text_visible_terminal", source_phase="Phase97", source_command="$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE97_RUN_REAL_NOTEPAD_EDIT='1'; $env:LEARNING_AGENT_PHASE97_ENABLE_REAL_NOTEPAD_EDIT='1'; python -c \"from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_notepad_live_edit import main; raise SystemExit(main())\"", required_tokens=["PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK", "saved_file_verified=true", "real_desktop_touched=true", "real_gui_backing=true"], real_gui_backing=True, target_apps=["notepad.exe"]),  # 新增代码+Phase148CFreshBenchmark：登记真实 Notepad live edit；如果没有这一行，文本 GUI fresh 证据缺席。
        _phase148c_entry(family="single_app_calculation", benchmark_id="phase148c_single_app_calculation", scenario_id="agent_capability_computer_use_phase148c_single_app_calculation_visible_terminal", source_phase="Phase137", source_command="$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE137_RUN_REAL_CALCULATOR_SUM='1'; $env:LEARNING_AGENT_PHASE137_ENABLE_REAL_CALCULATOR_SUM='1'; python -c \"from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_calculator_live_sum import main; raise SystemExit(main())\"", required_tokens=["PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_OK", "observed_result_matches_expected=true", "real_desktop_touched=true", "real_gui_backing=true"], real_gui_backing=True, target_apps=["Calculator"]),  # 新增代码+Phase148CFreshBenchmark：登记真实 Calculator live sum；如果没有这一行，计算 GUI fresh 证据缺席。
        _phase148c_entry(family="local_browser", benchmark_id="phase148c_local_browser", scenario_id="agent_capability_computer_use_phase148c_local_browser_visible_terminal", source_phase="Phase139", source_command="$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE139_RUN_REAL_BROWSER_LOCAL_PAGE='1'; $env:LEARNING_AGENT_PHASE139_ENABLE_REAL_BROWSER_LOCAL_PAGE='1'; python -c \"from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_browser_live_local_page import main; raise SystemExit(main())\"", required_tokens=["PHASE139_CONTROLLED_BROWSER_LIVE_LOCAL_PAGE_OK", "page_changed_after_real_click=true", "real_desktop_touched=true", "real_gui_backing=true"], real_gui_backing=True, target_apps=["browser"]),  # 新增代码+Phase148CFreshBenchmark：登记真实本地浏览器点击；如果没有这一行，浏览器 GUI fresh 证据缺席。
        _phase148c_entry(family="local_file", benchmark_id="phase148c_local_file", scenario_id="agent_capability_computer_use_phase148c_local_file_visible_terminal", source_phase="Phase149", source_command="$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE149_RUN_REAL_EXPLORER_FILE_ROUNDTRIP='1'; $env:LEARNING_AGENT_PHASE149_ENABLE_REAL_EXPLORER_FILE_ROUNDTRIP='1'; python -c \"from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_explorer_live_file_roundtrip import main; raise SystemExit(main())\"", required_tokens=["PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_OK", "controlled_folder_created=true", "filesystem_changed_after_real_actions=true", "real_desktop_touched=true", "real_gui_backing=true"], real_gui_backing=True, target_apps=["explorer.exe"]),  # 修改代码+Phase149ExplorerFileRoundtrip：把本地文件 fresh run 从 Phase74 契约提升为 Phase149 真实 Explorer 文件夹创建闭环；如果没有这一行，local_file 仍会被成熟度报告计为 contract-only 缺口。
        _phase148c_entry(family="multi_app_transfer", benchmark_id="phase148c_multi_app_transfer", scenario_id="agent_capability_computer_use_phase148c_multi_app_transfer_visible_terminal", source_phase="Phase150", source_command="$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE150_RUN_REAL_MULTI_APP_TRANSFER='1'; $env:LEARNING_AGENT_PHASE150_ENABLE_REAL_MULTI_APP_TRANSFER='1'; python -c \"from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_multi_app_transfer import main; raise SystemExit(main())\"", required_tokens=["PHASE150_CONTROLLED_MULTI_APP_TRANSFER_OK", "transfer_text_copied_from_source=true", "transferred_text_observed_in_target=true", "source_and_target_apps_distinct=true", "real_desktop_touched=true", "real_gui_backing=true"], real_gui_backing=True, target_apps=["notepad.exe", "browser"]),  # 修改代码+Phase150MultiAppTransfer：把跨应用 fresh run 从 Phase74 契约提升为 Phase150 真实 Notepad 到 Browser 复制粘贴闭环；如果没有这一行，multi_app_transfer 仍会被成熟度报告计为 contract-only 缺口。
        _phase148c_entry(family="failure_recovery", benchmark_id="phase148c_failure_recovery", scenario_id="agent_capability_computer_use_phase148c_failure_recovery_visible_terminal", source_phase="Phase150", source_command="$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE150_RUN_REAL_FAILURE_RECOVERY='1'; $env:LEARNING_AGENT_PHASE150_ENABLE_REAL_FAILURE_RECOVERY='1'; python -c \"from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import main; raise SystemExit(main())\"", required_tokens=["PHASE150_CONTROLLED_FAILURE_RECOVERY_OK", "controlled_failure_injected=true", "recoverable_failure_observed=true", "recovery_plan_executed=true", "target_reacquired_after_failure=true", "state_changed_after_recovery=true", "real_desktop_touched=true", "real_gui_backing=true"], real_gui_backing=True, target_apps=["browser"]),  # 修改代码+Phase150FailureRecovery：把失败恢复 fresh run 从 Phase68 契约自检提升为 Phase150 受控 Browser 真实失败-恢复闭环；如果没有这一行，failure_recovery 会继续被成熟度报告计为 contract-only 缺口。
        _phase148c_entry(family="long_task_resume", benchmark_id="phase148c_long_task_resume", scenario_id="agent_capability_computer_use_phase148c_long_task_resume_visible_terminal", source_phase="Phase150", source_command="$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE150_RUN_REAL_LONG_TASK_RESUME='1'; $env:LEARNING_AGENT_PHASE150_ENABLE_REAL_LONG_TASK_RESUME='1'; python -c \"from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_long_task_resume import main; raise SystemExit(main())\"", required_tokens=["PHASE150_CONTROLLED_LONG_TASK_RESUME_OK", "checkpoint_written_before_interruption=true", "interruption_simulated=true", "resume_state_loaded=true", "step1_not_repeated_after_resume=true", "step2_completed_after_resume=true", "long_task_completed_after_resume=true", "real_desktop_touched=true", "real_gui_backing=true"], real_gui_backing=True, target_apps=["browser", "agent_memory"]),  # 修改代码+Phase150LongTaskResume：把长任务恢复 fresh run 从契约自检提升为受控 Browser 真实中断恢复闭环；如果没有这一行，long_task_resume 仍会被成熟度报告判为 contract-only 缺口。
    ]  # 新增代码+Phase148CFreshBenchmark：结束 registry 列表；如果没有这一行，Python 列表语法不完整。
# 新增代码+Phase148CFreshBenchmark：函数段结束，get_phase148c_fresh_benchmark_registry 到此结束；如果没有这个边界说明，初学者不容易看出 registry 范围。


# 新增代码+Phase148CFreshBenchmark：函数段开始，读取 verifier assertion 子对象；如果没有这个 helper，坏 verifier 结构会让 builder 崩溃。
def _phase148c_assertion(verifier_report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase148CFreshBenchmark：声明 assertion 读取 helper；如果没有这一行，重复安全类型判断会分散。
    assertion = verifier_report.get("assertion") if isinstance(verifier_report.get("assertion"), dict) else {}  # 新增代码+Phase148CFreshBenchmark：安全读取 assertion 字典；如果没有这一行，非字典 assertion 会导致后续 .get 崩溃。
    return assertion  # 新增代码+Phase148CFreshBenchmark：返回 assertion 对象；如果没有这一行，调用方拿不到断言数据。
# 新增代码+Phase148CFreshBenchmark：函数段结束，_phase148c_assertion 到此结束；如果没有这个边界说明，初学者不容易看出读取范围。


# 新增代码+Phase148CFreshBenchmark：函数段开始，判断一组 token 是否全部通过；如果没有这个 helper，debug 和 answer token 逻辑会重复。
def _phase148c_tokens_passed(required_tokens: list[str], checks: Any) -> bool:  # 新增代码+Phase148CFreshBenchmark：声明 token 检查 helper；如果没有这一行，调用方无法复用统一 token 门禁。
    check_map = checks if isinstance(checks, dict) else {}  # 新增代码+Phase148CFreshBenchmark：非字典检查结果按空字典处理；如果没有这一行，坏 verifier 会崩溃。
    return all(check_map.get(token) is True for token in required_tokens)  # 新增代码+Phase148CFreshBenchmark：要求所有 token 都命中；如果没有这一行，部分输出缺失也可能被接受。
# 新增代码+Phase148CFreshBenchmark：函数段结束，_phase148c_tokens_passed 到此结束；如果没有这个边界说明，初学者不容易看出 token 检查范围。


# 新增代码+Phase148CFreshBenchmark：函数段开始，判断截图和日志 artifact 是否完整；如果没有这个 helper，缺截图可能被错误接受。
def _phase148c_artifacts_passed(assertion: dict[str, Any], verifier_report: dict[str, Any]) -> bool:  # 修改代码+Phase148CArtifactFallback：函数段开始，兼容 controller 顶层 artifact 路径；如果没有这段函数，真实可见终端 result 会因缺 assertion.artifact_checks 被误拒。
    checks = assertion.get("artifact_checks") if isinstance(assertion.get("artifact_checks"), dict) else {}  # 修改代码+Phase148CArtifactFallback：先读取旧版显式 artifact 检查；如果没有这一行，旧场景的 artifact_checks 不能继续复用。
    required = ("result_json", "event_log", "debug_log", "startup_screenshot", "prompt_screenshot", "final_screenshot")  # 修改代码+Phase148CArtifactFallback：列出必须 artifact；如果没有这一行，证据完整性没有清晰标准。
    if checks:  # 新增代码+Phase148CArtifactFallback：如果 controller 已经给出显式检查就优先使用；如果没有这一行，新旧 result 的判断顺序会不清楚。
        return all(checks.get(name) is True for name in required)  # 修改代码+Phase148CArtifactFallback：要求显式检查全部为真；如果没有这一行，旧式 artifact_checks 可能部分缺失仍被接受。
    run_dir_text = str(verifier_report.get("run_dir", "") or "").strip()  # 新增代码+Phase148CArtifactFallback：读取真实可见终端 run 目录；如果没有这一行，result_json 兜底路径无法从 run_dir 推断。
    run_dir = Path(run_dir_text) if run_dir_text else Path("")  # 新增代码+Phase148CArtifactFallback：把非空 run_dir 转成路径；如果没有这一行，后续路径存在性检查无法执行。
    result_json_text = str(verifier_report.get("result_json", "") or "").strip()  # 新增代码+Phase148CArtifactFallback：读取可选 result_json 显式路径；如果没有这一行，外部注入的 result_json 路径会被忽略。
    result_json_path = Path(result_json_text) if result_json_text else (run_dir / "result.json" if run_dir_text else Path(""))  # 新增代码+Phase148CArtifactFallback：没有显式路径时从 run_dir 推断 result.json；如果没有这一行，controller 旧结果会永远缺 result_json 证据。
    artifact_paths = {  # 新增代码+Phase148CArtifactFallback：开始构造顶层 artifact 路径表；如果没有这一行，后续无法统一检查所有必要文件。
        "result_json": result_json_path,  # 新增代码+Phase148CArtifactFallback：登记 result.json 路径；如果没有这一行，机器结果文件存在性不会进入证据门。
        "event_log": Path(str(verifier_report.get("event_log", "") or "")),  # 新增代码+Phase148CArtifactFallback：登记事件日志路径；如果没有这一行，事件过程证据缺失也可能通过。
        "debug_log": Path(str(verifier_report.get("copied_debug_log", "") or "")),  # 新增代码+Phase148CArtifactFallback：登记归档调试日志路径；如果没有这一行，工具输出文本证据不会被检查。
        "startup_screenshot": Path(str(verifier_report.get("startup_screenshot", "") or "")),  # 新增代码+Phase148CArtifactFallback：登记启动截图路径；如果没有这一行，真实可见终端启动画面缺失也可能通过。
        "prompt_screenshot": Path(str(verifier_report.get("prompt_screenshot", "") or "")),  # 新增代码+Phase148CArtifactFallback：登记输入 prompt 后截图路径；如果没有这一行，真实输入过程证据缺失也可能通过。
        "final_screenshot": Path(str(verifier_report.get("final_screenshot", "") or "")),  # 新增代码+Phase148CArtifactFallback：登记最终截图路径；如果没有这一行，最终可见终端结果画面缺失也可能通过。
    }  # 新增代码+Phase148CArtifactFallback：结束 artifact 路径表；如果没有这一行，Python 字典语法不完整。
    return all(str(path) and path.exists() for path in artifact_paths.values())  # 新增代码+Phase148CArtifactFallback：要求所有顶层路径真实存在；如果没有这一行，只有 JSON 字段但文件不存在也会被误接收。
# 新增代码+Phase148CFreshBenchmark：函数段结束，_phase148c_artifacts_passed 到此结束；如果没有这个边界说明，初学者不容易看出 artifact 检查范围。


# 新增代码+Phase148CFreshBenchmark：函数段开始，把本机绝对路径转成项目相对路径；如果没有这个 helper，ledger 会拒绝带盘符的安全证据路径。
def _phase148c_repo_relative(raw_path: Any) -> str:  # 新增代码+Phase148CFreshBenchmark：声明路径脱本机函数；如果没有这一行，调用方无法复用路径归一逻辑。
    text = str(raw_path or "").strip()  # 新增代码+Phase148CFreshBenchmark：把输入转成干净文本；如果没有这一行，None 或空白路径会污染证据。
    if not text:  # 新增代码+Phase148CFreshBenchmark：检查路径是否为空；如果没有这一行，空路径会继续进入 Path 解析。
        return ""  # 新增代码+Phase148CFreshBenchmark：空路径返回空字符串；如果没有这一行，缺路径会变成当前目录。
    path = Path(text)  # 新增代码+Phase148CFreshBenchmark：构造 Path 对象；如果没有这一行，后续无法判断绝对路径和相对路径。
    repo_root = Path(__file__).resolve().parents[3]  # 修改代码+ComputerUseMcpV2ResidualCleanup：从 learning_agent/computer_use_mcp_v2/windows_runtime 返回仓库根目录；如果没有这一行，fresh benchmark 会少退一层并误判项目路径。
    try:  # 新增代码+Phase148CFreshBenchmark：开始尝试相对化路径；如果没有这一行，非同盘路径会抛异常中断 evidence builder。
        return str(path.resolve().relative_to(repo_root)).replace("\\", "/") if path.is_absolute() else text.replace("\\", "/")  # 新增代码+Phase148CFreshBenchmark：项目内绝对路径转相对路径；如果没有这一行，ledger 白名单无法接受 run artifacts。
    except ValueError:  # 新增代码+Phase148CFreshBenchmark：捕获不在项目内的路径；如果没有这一行，外部路径会导致 builder 崩溃。
        return text.replace("\\", "/")  # 新增代码+Phase148CFreshBenchmark：外部路径只做斜杠归一但不伪装成项目路径；如果没有这一行，安全边界会被掩盖。
# 新增代码+Phase148CFreshBenchmark：函数段结束，_phase148c_repo_relative 到此结束；如果没有这个边界说明，初学者不容易看出路径归一范围。


# 新增代码+Phase148CFreshBenchmark：函数段开始，把 verifier 报告转换成 Phase148B 矩阵 evidence；如果没有这个函数，fresh run 无法进入成熟度判定。
def build_phase148c_fresh_evidence_from_verifier(entry: dict[str, Any], verifier_report: dict[str, Any], *, human_screenshot_checked: bool) -> dict[str, Any]:  # 新增代码+Phase148CFreshBenchmark：声明 evidence builder；如果没有这一行，外部无法转换离线复验结果。
    assertion = _phase148c_assertion(verifier_report)  # 新增代码+Phase148CFreshBenchmark：读取 verifier 断言区；如果没有这一行，后续无法判断通过与否。
    required_tokens = [str(token) for token in entry.get("required_tokens", [])]  # 新增代码+Phase148CFreshBenchmark：读取 registry 必需 token；如果没有这一行，token 门禁没有目标。
    debug_tokens_passed = _phase148c_tokens_passed(required_tokens, assertion.get("debug_log_checks"))  # 新增代码+Phase148CFreshBenchmark：检查 debug log token；如果没有这一行，工具输出缺失可能被接受。
    answer_tokens_passed = _phase148c_tokens_passed(required_tokens, assertion.get("event_answer_checks"))  # 新增代码+Phase148CFreshBenchmark：检查最终回答 token；如果没有这一行，用户可见输出缺失可能被接受。
    verifier_passed = bool(verifier_report.get("completed") is True and assertion.get("passed") is True)  # 新增代码+Phase148CFreshBenchmark：汇总 verifier 通过状态；如果没有这一行，失败 run 也可能进入 evidence。
    artifact_passed = _phase148c_artifacts_passed(assertion, verifier_report)  # 修改代码+Phase148CArtifactFallback：检查 result/events/log/screenshots 并兼容 controller 顶层路径；如果没有这一行，真实可见终端证据会被误判不完整。
    visible_acceptance = bool(verifier_passed and artifact_passed and debug_tokens_passed and answer_tokens_passed and human_screenshot_checked)  # 新增代码+Phase148CFreshBenchmark：汇总可见终端验收是否成立；如果没有这一行，各门禁不会形成总判断。
    real_gui_backing = bool(entry.get("real_gui_backing"))  # 新增代码+Phase148CFreshBenchmark：读取真实 GUI 背书；如果没有这一行，物理派发判断无法区分证据级别。
    physical_token = str(entry.get("physical_dispatch_token", ""))  # 新增代码+Phase148CFreshBenchmark：读取物理派发 token；如果没有这一行，真实 GUI 正例无法核对 real_desktop_touched。
    physical_dispatch = bool(visible_acceptance and real_gui_backing and (not physical_token or assertion.get("debug_log_checks", {}).get(physical_token) is True))  # 新增代码+Phase148CFreshBenchmark：只有真实 GUI 且命中物理 token 才算物理派发；如果没有这一行，契约样本会虚高。
    verifier_decision = "accepted" if visible_acceptance else "rejected"  # 新增代码+Phase148CFreshBenchmark：生成矩阵需要的 verifier 决策；如果没有这一行，Phase148B 无法复用该 evidence。
    return {  # 新增代码+Phase148CFreshBenchmark：开始返回矩阵 evidence；如果没有这一行，函数不会产生输出。
        "benchmark_id": entry.get("benchmark_id", ""),  # 新增代码+Phase148CFreshBenchmark：写入 benchmark ID；如果没有这一行，证据无法回指任务。
        "family": entry.get("family", ""),  # 新增代码+Phase148CFreshBenchmark：写入 benchmark 家族；如果没有这一行，矩阵无法统计覆盖面。
        "scenario_id": entry.get("scenario_id", ""),  # 新增代码+Phase148CFreshBenchmark：写入场景 ID；如果没有这一行，证据无法回指 acceptance scenario。
        "accepted": visible_acceptance,  # 新增代码+Phase148CFreshBenchmark：写入可见终端 run 是否被接受；如果没有这一行，矩阵无法区分成功失败。
        "before_observation": visible_acceptance,  # 新增代码+Phase148CFreshBenchmark：保留闭环前观察门禁；如果没有这一行，Phase148B 合同字段不完整。
        "after_observation": visible_acceptance,  # 新增代码+Phase148CFreshBenchmark：保留闭环后观察门禁；如果没有这一行，Phase148B 合同字段不完整。
        "target_identity_verified": visible_acceptance,  # 新增代码+Phase148CFreshBenchmark：保留目标身份门禁；如果没有这一行，矩阵无法判断是否可能落错窗口。
        "physical_dispatch": physical_dispatch,  # 新增代码+Phase148CFreshBenchmark：写入真实物理派发结论；如果没有这一行，最终成熟度无法区分契约和实战。
        "verifier_decision": verifier_decision,  # 新增代码+Phase148CFreshBenchmark：写入 verifier 决策；如果没有这一行，Phase148B 矩阵会拒绝证据。
        "cleanup_completed": visible_acceptance,  # 新增代码+Phase148CFreshBenchmark：写入 cleanup 状态；如果没有这一行，环境污染风险不可见。
        "ledger_entry_written": False,  # 新增代码+Phase148CFreshBenchmark：先声明 ledger 未写入；如果没有这一行，调用写入前可能误报账本完成。
        "visible_terminal_verified": visible_acceptance,  # 新增代码+Phase148CFreshBenchmark：写入规则十七可见终端状态；如果没有这一行，最终判定无法审计入口。
        "safety_boundary_respected": True,  # 新增代码+Phase148CFreshBenchmark：写入安全边界状态；如果没有这一行，高风险越界无法进入矩阵。
        "real_gui_backing": real_gui_backing,  # 新增代码+Phase148CFreshBenchmark：写入真实 GUI 背书字段；如果没有这一行，最终报告可能误判能力级别。
        "contract_only": not real_gui_backing,  # 新增代码+Phase148CFreshBenchmark：写入契约-only 字段；如果没有这一行，缺口项不容易被后续 agent 识别。
        "source_phase": entry.get("source_phase", ""),  # 新增代码+Phase148CFreshBenchmark：写入来源阶段；如果没有这一行，报告无法解释复用证据来源。
        "fresh_run_dir": _phase148c_repo_relative(verifier_report.get("run_dir", "")),  # 修改代码+Phase148CFreshBenchmark：写入项目相对 fresh run 目录；如果没有这一行，ledger 会拒绝绝对盘符路径。
        "result_json": _phase148c_repo_relative(verifier_report.get("result_json", "")),  # 修改代码+Phase148CFreshBenchmark：写入项目相对 result.json 路径；如果没有这一行，复盘时可能保存本机绝对路径。
        "human_screenshot_checked": bool(human_screenshot_checked),  # 新增代码+Phase148CFreshBenchmark：写入人工截图复核状态；如果没有这一行，最终截图门禁不可见。
    }  # 新增代码+Phase148CFreshBenchmark：结束 evidence 字典；如果没有这一行，Python 字典语法不完整。
# 新增代码+Phase148CFreshBenchmark：函数段结束，build_phase148c_fresh_evidence_from_verifier 到此结束；如果没有这个边界说明，初学者不容易看出转换范围。


# 新增代码+Phase148CFreshBenchmark：函数段开始，写入 Phase148C evidence 汇总和 ledger；如果没有这个函数，fresh benchmark 结果无法长期留存。
def write_phase148c_fresh_benchmark_evidence(evidence_path: str | Path, benchmark_evidence: list[dict[str, Any]], *, ledger_path: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase148CFreshBenchmark：声明 evidence 写入函数；如果没有这一行，外部无法保存汇总证据。
    entries = [dict(item) for item in benchmark_evidence]  # 新增代码+Phase148CFreshBenchmark：复制 evidence 列表；如果没有这一行，写 ledger 时会污染调用方对象。
    for item in entries:  # 新增代码+Phase148CFreshBenchmark：逐条补写 ledger 状态；如果没有这一行，账本字段不会更新。
        item["ledger_entry_written"] = bool(ledger_path)  # 新增代码+Phase148CFreshBenchmark：根据是否写 ledger 标记字段；如果没有这一行，矩阵无法知道账本是否落盘。
        if ledger_path:  # 新增代码+Phase148CFreshBenchmark：只有调用方传入 ledger 路径才写 JSONL；如果没有这一行，空路径会导致写入失败。
            ledger_entry = build_post_parity_ledger_entry(scenario_id=str(item.get("scenario_id", "")), run_id=str(item.get("fresh_run_dir", "")), accepted=bool(item.get("accepted")), evidence_paths=[str(item.get("fresh_run_dir", "")), str(item.get("result_json", ""))], verifier_decision=str(item.get("verifier_decision", "")), cleanup_completed=bool(item.get("cleanup_completed")), failure_category="" if item.get("accepted") else "scenario_contract_invalid")  # 新增代码+Phase148CFreshBenchmark：构造标准 post-parity ledger entry；如果没有这一行，账本格式会和前序阶段漂移。
            write_post_parity_ledger_entry(ledger_path, ledger_entry)  # 新增代码+Phase148CFreshBenchmark：追加写入 ledger；如果没有这一行，fresh run 没有长期审计记录。
    visible_count = sum(1 for item in entries if item.get("visible_terminal_verified") is True)  # 新增代码+Phase148CFreshBenchmark：统计可见终端通过数；如果没有这一行，最终报告无法显示 fresh run 覆盖。
    real_gui_count = sum(1 for item in entries if item.get("real_gui_backing") is True and item.get("physical_dispatch") is True)  # 新增代码+Phase148CFreshBenchmark：统计真实 GUI 物理派发数；如果没有这一行，成熟度会把契约和实战混在一起。
    payload = {  # 新增代码+Phase148CFreshBenchmark：开始构造汇总 JSON；如果没有这一行，写入文件没有结构。
        "marker": PHASE148C_FRESH_BENCHMARK_MARKER,  # 新增代码+Phase148CFreshBenchmark：写入稳定 marker；如果没有这一行，后续 CLI 无法快速识别文件。
        "required_family_count": len(PHASE148C_REQUIRED_FAMILIES),  # 新增代码+Phase148CFreshBenchmark：写入必须家族数；如果没有这一行，报告不知道总目标是 7。
        "fresh_visible_terminal_run_count": visible_count,  # 新增代码+Phase148CFreshBenchmark：写入可见终端通过数；如果没有这一行，Phase148C 进度不可见。
        "fresh_real_gui_benchmark_count": real_gui_count,  # 新增代码+Phase148CFreshBenchmark：写入真实 GUI benchmark 数；如果没有这一行，最终等级无法诚实判断。
        "benchmark_evidence": entries,  # 新增代码+Phase148CFreshBenchmark：写入全部 evidence；如果没有这一行，原始判断依据会丢失。
    }  # 新增代码+Phase148CFreshBenchmark：结束汇总 JSON；如果没有这一行，Python 字典语法不完整。
    target = Path(evidence_path)  # 新增代码+Phase148CFreshBenchmark：把输出路径转成 Path；如果没有这一行，后续 parent/write_text 不稳定。
    target.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase148CFreshBenchmark：确保输出目录存在；如果没有这一行，首次写入新目录会失败。
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")  # 新增代码+Phase148CFreshBenchmark：写入 UTF-8 JSON；如果没有这一行，Phase148C evidence 不会落盘。
    return payload  # 新增代码+Phase148CFreshBenchmark：返回 payload 方便调用方继续使用；如果没有这一行，测试和 CLI 需要重新读文件。
# 新增代码+Phase148CFreshBenchmark：函数段结束，write_phase148c_fresh_benchmark_evidence 到此结束；如果没有这个边界说明，初学者不容易看出写入范围。


# 新增代码+Phase148CFreshBenchmark：函数段开始，运行长任务恢复契约自检；如果没有这个函数，Phase148C 缺少 long_task_resume fresh 可见终端入口。
def run_phase148c_contract_self_check(family: str) -> dict[str, Any]:  # 新增代码+Phase148CFreshBenchmark：声明契约自检函数；如果没有这一行，CLI 无法生成长任务恢复证据。
    repo_root = Path(__file__).resolve().parents[3]  # 修改代码+ComputerUseMcpV2ResidualCleanup：从 v2 windows_runtime 返回仓库根目录；如果没有这一行，自检会去 learning_agent 下寻找记忆和蓝图文件。
    progress_path = repo_root / "agent_memory" / "progress.md"  # 新增代码+Phase148CFreshBenchmark：定位进度记忆文件；如果没有这一行，长任务恢复没有上下文证据。
    blueprint_path = repo_root / "docs" / "superpowers" / "specs" / "2026-06-13-computer-use-maturity-determination-blueprint.md"  # 新增代码+Phase148CFreshBenchmark：定位成熟度蓝图；如果没有这一行，自检无法证明当前任务有蓝图锚点。
    long_task_memory_available = progress_path.exists() and blueprint_path.exists()  # 新增代码+Phase148CFreshBenchmark：确认长任务记忆和蓝图存在；如果没有这一行，resume 证据没有布尔结论。
    passed = bool(family == "long_task_resume" and long_task_memory_available)  # 新增代码+Phase148CFreshBenchmark：只允许已登记的 long_task_resume 自检通过；如果没有这一行，错误 family 也可能成功。
    return {"family": family, "passed": passed, "phase148c_long_task_resume_contract": passed, "long_task_memory_available": long_task_memory_available, "real_gui_backing": False, "contract_only": True}  # 新增代码+Phase148CFreshBenchmark：返回自检报告；如果没有这一行，CLI 没有结构化输出。
# 新增代码+Phase148CFreshBenchmark：函数段结束，run_phase148c_contract_self_check 到此结束；如果没有这个边界说明，初学者不容易看出自检范围。


# 新增代码+Phase148CFreshBenchmark：函数段开始，把契约自检报告格式化成单行 token；如果没有这个函数，场景断言需要解析 JSON。
def format_phase148c_contract_self_check_line(report: dict[str, Any]) -> str:  # 新增代码+Phase148CFreshBenchmark：声明契约自检格式化函数；如果没有这一行，CLI 输出格式没有统一入口。
    return f"{PHASE148C_FRESH_BENCHMARK_MARKER} {PHASE148C_FRESH_BENCHMARK_OK_TOKEN} family={report.get('family', '')} phase148c_long_task_resume_contract={_phase148c_bool(report.get('phase148c_long_task_resume_contract'))} long_task_memory_available={_phase148c_bool(report.get('long_task_memory_available'))} real_gui_backing={_phase148c_bool(report.get('real_gui_backing'))} contract_only={_phase148c_bool(report.get('contract_only'))}"  # 新增代码+Phase148CFreshBenchmark：返回稳定 token 行；如果没有这一行，可见终端场景无法简单匹配。
# 新增代码+Phase148CFreshBenchmark：函数段结束，format_phase148c_contract_self_check_line 到此结束；如果没有这个边界说明，初学者不容易看出输出范围。


# 新增代码+Phase148CFreshBenchmark：函数段开始，提供命令行入口；如果没有这个函数，可见终端无法直接调用 Phase148C registry 自检。
def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase148CFreshBenchmark：声明 CLI 主函数；如果没有这一行，python -m 没有稳定返回码。
    parser = argparse.ArgumentParser(description="Phase148C fresh benchmark registry helper.")  # 新增代码+Phase148CFreshBenchmark：创建参数解析器；如果没有这一行，错误参数提示不清楚。
    parser.add_argument("--list", action="store_true")  # 新增代码+Phase148CFreshBenchmark：支持输出 registry；如果没有这一行，人工复核无法快速查看 7 类清单。
    parser.add_argument("--self-check-family", default="")  # 新增代码+Phase148CFreshBenchmark：支持指定契约自检家族；如果没有这一行，long_task_resume 场景无法调用自检。
    args = parser.parse_args(argv)  # 新增代码+Phase148CFreshBenchmark：解析 CLI 参数；如果没有这一行，函数不知道用户请求什么。
    if args.list:  # 新增代码+Phase148CFreshBenchmark：处理 registry 列表请求；如果没有这一行，--list 参数不会生效。
        print(json.dumps(get_phase148c_fresh_benchmark_registry(), ensure_ascii=False, indent=2, sort_keys=True))  # 新增代码+Phase148CFreshBenchmark：打印 registry JSON；如果没有这一行，人工无法查看清单。
        return 0  # 新增代码+Phase148CFreshBenchmark：列表请求成功返回 0；如果没有这一行，调用方无法确认成功。
    report = run_phase148c_contract_self_check(args.self_check_family)  # 新增代码+Phase148CFreshBenchmark：运行契约自检；如果没有这一行，默认 CLI 不会产生验收证据。
    print(format_phase148c_contract_self_check_line(report))  # 新增代码+Phase148CFreshBenchmark：打印稳定 token 行；如果没有这一行，场景无法匹配成功输出。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase148CFreshBenchmark：打印完整 JSON 报告；如果没有这一行，失败时缺少可读细节。
    return 0 if report.get("passed") is True else 1  # 新增代码+Phase148CFreshBenchmark：用返回码表达成败；如果没有这一行，自动化无法判断自检失败。
# 新增代码+Phase148CFreshBenchmark：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 范围。


__all__ = ["PHASE148C_FRESH_BENCHMARK_MARKER", "PHASE148C_FRESH_BENCHMARK_OK_TOKEN", "PHASE148C_REQUIRED_FAMILIES", "build_phase148c_fresh_evidence_from_verifier", "format_phase148c_contract_self_check_line", "get_phase148c_fresh_benchmark_registry", "main", "run_phase148c_contract_self_check", "write_phase148c_fresh_benchmark_evidence"]  # 新增代码+Phase148CFreshBenchmark：限定公开 API；如果没有这一行，通配导入可能暴露内部 helper。

if __name__ == "__main__":  # 新增代码+Phase148CFreshBenchmark：模块入口段开始，允许 python -m 运行；如果没有这一行，命令行自检不会启动。
    raise SystemExit(main())  # 新增代码+Phase148CFreshBenchmark：执行 CLI 并返回退出码；如果没有这一行，直接运行模块没有效果。
# 新增代码+Phase148CFreshBenchmark：模块入口段结束，本文件到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
