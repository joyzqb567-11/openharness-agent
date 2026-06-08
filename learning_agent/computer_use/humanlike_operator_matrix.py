"""Phase75 final Humanlike Windows Operator matrix."""  # 新增代码+Phase75HumanlikeMatrix: 标明本文件负责汇总 Phase65-74 的最终拟人 Windows Operator 门禁；如果没有这行代码，读者不知道最终验收入口在哪里。
from __future__ import annotations  # 新增代码+Phase75HumanlikeMatrix: 启用延迟类型注解；如果没有这行代码，未来前向类型标注更容易在运行时导入失败。

import json  # 新增代码+Phase75HumanlikeMatrix: 导入 JSON 用于 CLI 打印结构化报告；如果没有这行代码，真实终端失败时不易复盘。
from pathlib import Path  # 新增代码+Phase75HumanlikeMatrix: 导入 Path 统一处理 Windows 证据目录和场景路径；如果没有这行代码，路径拼接容易出错。
from typing import Any  # 新增代码+Phase75HumanlikeMatrix: 导入 Any 描述各阶段动态报告；如果没有这行代码，函数边界不容易读懂。

from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase75HumanlikeMatrix: 复用原子 JSON 写入工具保存最终矩阵证据；如果没有这行代码，崩溃时可能留下半个矩阵文件。


PHASE75_HUMANLIKE_WINDOWS_OPERATOR_MARKER = "PHASE75_HUMANLIKE_WINDOWS_OPERATOR_READY"  # 新增代码+Phase75HumanlikeMatrix: 定义 Phase75 ready marker；如果没有这行代码，真实终端验收没有稳定锚点。
PHASE75_HUMANLIKE_WINDOWS_OPERATOR_OK_TOKEN = "PHASE75_HUMANLIKE_WINDOWS_OPERATOR_OK"  # 新增代码+Phase75HumanlikeMatrix: 定义 Phase75 OK token；如果没有这行代码，debug log 无法区分最终矩阵通过和普通输出。
PHASE75_HUMANLIKE_WINDOWS_OPERATOR_MODEL = "phase75_humanlike_windows_operator_final_matrix"  # 新增代码+Phase75HumanlikeMatrix: 定义最终矩阵模型名；如果没有这行代码，报告无法说明使用哪套验收规则。
PHASE75_EXPECTED_PHASE_IDS = tuple(str(phase_id) for phase_id in range(65, 75))  # 新增代码+Phase75HumanlikeMatrix: 固定最终矩阵必须覆盖 Phase65-74；如果没有这行代码，阶段顺序和数量会漂移。
PHASE75_EXPECTED_PHASE_COUNT = len(PHASE75_EXPECTED_PHASE_IDS)  # 新增代码+Phase75HumanlikeMatrix: 固定 Phase65-74 共十个输入阶段；如果没有这行代码，漏跑阶段也可能误判完整。
PHASE75_ACTIONS_EXPANDED = False  # 新增代码+Phase75HumanlikeMatrix: 明确 Phase75 自身不新增真实桌面动作；如果没有这行代码，用户可能误以为最终矩阵会直接控制电脑。
DEFAULT_PHASE75_HUMANLIKE_OPERATOR_MATRIX_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "humanlike_operator_matrix"  # 新增代码+Phase75HumanlikeMatrix: 定义默认最终矩阵证据目录；如果没有这行代码，CLI 自检输出会散落。
DEFAULT_PHASE75_SCENARIO_PATH = Path(__file__).resolve().parents[1] / "acceptance_controller" / "scenarios" / "agent_capability_phase75_humanlike_operator_matrix.json"  # 新增代码+Phase75HumanlikeMatrix: 定义真实可见终端场景路径；如果没有这行代码，最终矩阵无法检查场景门禁是否存在。
PHASE75_PHASE_LABELS = {"65": "phase65_humanlike_operator_contract", "66": "phase66_observation_fusion", "67": "phase67_prompt_task_planner", "68": "phase68_closed_loop_executor", "69": "phase69_app_window_control", "70": "phase70_generic_control_actions", "71": "phase71_generic_input_actions", "72": "phase72_real_app_safety_boundary", "73": "phase73_app_memory", "74": "phase74_representative_e2e"}  # 新增代码+Phase75HumanlikeMatrix: 定义每个阶段的稳定标签；如果没有这行代码，外部 agent 难以阅读失败阶段。


def _phase75_bool_token(value: Any) -> str:  # 新增代码+Phase75HumanlikeMatrix: 函数段开始，把布尔值转换成验收 token 需要的小写 true/false；如果没有这个函数，CLI 输出容易出现 True/False 漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase75HumanlikeMatrix: 返回稳定小写布尔字符串；如果没有这行代码，真实终端场景 token 无法稳定匹配。
# 新增代码+Phase75HumanlikeMatrix: 函数段结束，_phase75_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


def _phase75_import_contracts() -> dict[str, Any]:  # 新增代码+Phase75HumanlikeMatrix: 函数段开始，延迟导入 Phase65-74 合同入口；如果没有这段函数，模块导入时会急切加载所有阶段并增加循环依赖风险。
    from learning_agent.computer_use.app_memory import phase73_cli_line, run_phase73_app_memory_contract  # 新增代码+Phase75HumanlikeMatrix: 导入 Phase73 app memory 合同；如果没有这行代码，最终矩阵无法覆盖自学习记忆边界。
    from learning_agent.computer_use.windows_launch_resolver import phase69_cli_line, run_phase69_app_window_control_contract  # 新增代码+Phase75HumanlikeMatrix: 导入 Phase69 app/window 合同；如果没有这行代码，最终矩阵无法覆盖应用启动和窗口聚焦。
    from learning_agent.computer_use.closed_loop_executor import phase68_cli_line, run_phase68_closed_loop_executor_contract  # 新增代码+Phase75HumanlikeMatrix: 导入 Phase68 闭环执行合同；如果没有这行代码，最终矩阵无法覆盖观察-动作-验证-恢复。
    from learning_agent.computer_use.generic_control_actions import phase70_cli_line, run_phase70_generic_control_actions_contract  # 新增代码+Phase75HumanlikeMatrix: 导入 Phase70 通用控件动作合同；如果没有这行代码，最终矩阵无法覆盖通用点击/输入/视觉兜底。
    from learning_agent.computer_use.generic_input_actions import phase71_cli_line, run_phase71_generic_input_actions_contract  # 新增代码+Phase75HumanlikeMatrix: 导入 Phase71 通用输入动作合同；如果没有这行代码，最终矩阵无法覆盖热键、菜单、滚轮和拖拽。
    from learning_agent.computer_use.humanlike_operator_contract import phase65_cli_line, run_phase65_humanlike_operator_contract  # 新增代码+Phase75HumanlikeMatrix: 导入 Phase65 通用拟人合同；如果没有这行代码，最终矩阵没有设计边界来源。
    from learning_agent.computer_use.observation_fusion import phase66_cli_line, run_phase66_observation_fusion_contract  # 新增代码+Phase75HumanlikeMatrix: 导入 Phase66 观察融合合同；如果没有这行代码，最终矩阵无法覆盖多源观察层。
    from learning_agent.computer_use.prompt_task_planner import phase67_cli_line, run_phase67_prompt_task_planner_contract  # 新增代码+Phase75HumanlikeMatrix: 导入 Phase67 prompt 规划合同；如果没有这行代码，最终矩阵无法覆盖 prompt 到步骤计划。
    from learning_agent.computer_use.real_app_safety_boundary import phase72_cli_line, run_phase72_real_app_safety_boundary_contract  # 新增代码+Phase75HumanlikeMatrix: 导入 Phase72 真实应用安全边界合同；如果没有这行代码，最终矩阵无法覆盖授权、急停和高风险拒绝。
    from learning_agent.computer_use.representative_e2e_matrix import phase74_cli_line, run_phase74_representative_e2e_contract  # 新增代码+Phase75HumanlikeMatrix: 导入 Phase74 代表性 E2E 合同；如果没有这行代码，最终矩阵无法覆盖 Paint 皮卡丘和代表性应用。
    return {"phase65_cli_line": phase65_cli_line, "run_phase65_humanlike_operator_contract": run_phase65_humanlike_operator_contract, "phase66_cli_line": phase66_cli_line, "run_phase66_observation_fusion_contract": run_phase66_observation_fusion_contract, "phase67_cli_line": phase67_cli_line, "run_phase67_prompt_task_planner_contract": run_phase67_prompt_task_planner_contract, "phase68_cli_line": phase68_cli_line, "run_phase68_closed_loop_executor_contract": run_phase68_closed_loop_executor_contract, "phase69_cli_line": phase69_cli_line, "run_phase69_app_window_control_contract": run_phase69_app_window_control_contract, "phase70_cli_line": phase70_cli_line, "run_phase70_generic_control_actions_contract": run_phase70_generic_control_actions_contract, "phase71_cli_line": phase71_cli_line, "run_phase71_generic_input_actions_contract": run_phase71_generic_input_actions_contract, "phase72_cli_line": phase72_cli_line, "run_phase72_real_app_safety_boundary_contract": run_phase72_real_app_safety_boundary_contract, "phase73_cli_line": phase73_cli_line, "run_phase73_app_memory_contract": run_phase73_app_memory_contract, "phase74_cli_line": phase74_cli_line, "run_phase74_representative_e2e_contract": run_phase74_representative_e2e_contract}  # 新增代码+Phase75HumanlikeMatrix: 返回所有阶段合同入口；如果没有这行代码，run 函数无法统一执行 Phase65-74 自检。
# 新增代码+Phase75HumanlikeMatrix: 函数段结束，_phase75_import_contracts 到此结束；如果没有这个边界说明，初学者不容易看出合同导入范围。


def _phase75_phase_summary(phase_id: str, report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase75HumanlikeMatrix: 函数段开始，把单阶段报告压缩成总矩阵摘要；如果没有这段函数，失败定位和安全字段会散落。
    actions_expanded = bool(report.get("actions_expanded", False))  # 新增代码+Phase75HumanlikeMatrix: 读取阶段是否自称扩展动作面；如果没有这行代码，无保护扩张无法汇总。
    uncontrolled_actions_expanded = bool(report.get("uncontrolled_actions_expanded", actions_expanded))  # 新增代码+Phase75HumanlikeMatrix: 优先读取阶段自己的无保护扩张字段；如果没有这行代码，Phase72 受控动作扩展可能被误判。
    return {"phase_id": phase_id, "label": PHASE75_PHASE_LABELS.get(phase_id, phase_id), "marker": str(report.get("marker", "")), "ok_token": str(report.get("ok_token", "")), "passed": bool(report.get("passed", False)), "actions_expanded": actions_expanded, "uncontrolled_actions_expanded": uncontrolled_actions_expanded, "state_dir": str(report.get("state_dir", ""))}  # 新增代码+Phase75HumanlikeMatrix: 返回稳定阶段摘要；如果没有这行代码，外部 agent 无法快速知道哪个阶段失败。
# 新增代码+Phase75HumanlikeMatrix: 函数段结束，_phase75_phase_summary 到此结束；如果没有这个边界说明，初学者不容易看出阶段摘要范围。


def run_phase75_humanlike_operator_matrix_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase75HumanlikeMatrix: 函数段开始，运行 Phase75 最终 Humanlike Windows Operator 合同；如果没有这段函数，测试和真实终端没有统一验收入口。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE75_HUMANLIKE_OPERATOR_MATRIX_ROOT  # 新增代码+Phase75HumanlikeMatrix: 选择传入目录或默认目录；如果没有这行代码，测试无法隔离证据目录。
    root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase75HumanlikeMatrix: 确保最终矩阵证据目录存在；如果没有这行代码，子阶段输出目录和矩阵文件写入会失败。
    contracts = _phase75_import_contracts()  # 新增代码+Phase75HumanlikeMatrix: 加载所有阶段合同；如果没有这行代码，最终矩阵没有前置阶段事实源。
    phase65_report = contracts["run_phase65_humanlike_operator_contract"]()  # 新增代码+Phase75HumanlikeMatrix: 运行 Phase65 通用拟人合同；如果没有这行代码，最终矩阵无法验证通用目标和防作弊边界。
    phase66_report = contracts["run_phase66_observation_fusion_contract"](real_smoke=False)  # 新增代码+Phase75HumanlikeMatrix: 运行 Phase66 安全观察融合合同；如果没有这行代码，最终矩阵无法验证观察层。
    phase67_report = contracts["run_phase67_prompt_task_planner_contract"]()  # 新增代码+Phase75HumanlikeMatrix: 运行 Phase67 prompt 规划合同；如果没有这行代码，最终矩阵无法验证 prompt 到步骤计划。
    phase68_report = contracts["run_phase68_closed_loop_executor_contract"]()  # 新增代码+Phase75HumanlikeMatrix: 运行 Phase68 闭环执行合同；如果没有这行代码，最终矩阵无法验证后置校验和恢复。
    phase69_report = contracts["run_phase69_app_window_control_contract"](real_smoke=False)  # 新增代码+Phase75HumanlikeMatrix: 运行 Phase69 应用窗口合同；如果没有这行代码，最终矩阵无法验证启动、聚焦和漂移阻断。
    phase70_report = contracts["run_phase70_generic_control_actions_contract"]()  # 新增代码+Phase75HumanlikeMatrix: 运行 Phase70 通用控件动作合同；如果没有这行代码，最终矩阵无法验证通用点击/输入。
    phase71_report = contracts["run_phase71_generic_input_actions_contract"]()  # 新增代码+Phase75HumanlikeMatrix: 运行 Phase71 通用输入动作合同；如果没有这行代码，最终矩阵无法验证热键、菜单、滚轮和拖拽。
    phase72_report = contracts["run_phase72_real_app_safety_boundary_contract"](base_dir=root / "phase72")  # 新增代码+Phase75HumanlikeMatrix: 运行 Phase72 安全边界合同并隔离授权文件；如果没有这行代码，最终矩阵无法验证授权、急停和高风险拒绝。
    phase73_report = contracts["run_phase73_app_memory_contract"](base_dir=root / "phase73")  # 新增代码+Phase75HumanlikeMatrix: 运行 Phase73 app memory 合同并隔离记忆文件；如果没有这行代码，最终矩阵无法验证非敏感学习边界。
    phase74_report = contracts["run_phase74_representative_e2e_contract"](base_dir=root / "phase74", real_smoke=False)  # 新增代码+Phase75HumanlikeMatrix: 运行 Phase74 代表性 E2E 合同并隔离证据；如果没有这行代码，最终矩阵无法验证 Paint 皮卡丘。
    phase_reports = {"65": phase65_report, "66": phase66_report, "67": phase67_report, "68": phase68_report, "69": phase69_report, "70": phase70_report, "71": phase71_report, "72": phase72_report, "73": phase73_report, "74": phase74_report}  # 新增代码+Phase75HumanlikeMatrix: 汇总所有阶段原始报告；如果没有这行代码，后续聚合无法按阶段索引。
    phase_cli_lines = {"65": contracts["phase65_cli_line"](phase65_report), "66": contracts["phase66_cli_line"](phase66_report), "67": contracts["phase67_cli_line"](phase67_report), "68": contracts["phase68_cli_line"](phase68_report), "69": contracts["phase69_cli_line"](phase69_report), "70": contracts["phase70_cli_line"](phase70_report), "71": contracts["phase71_cli_line"](phase71_report), "72": contracts["phase72_cli_line"](phase72_report), "73": contracts["phase73_cli_line"](phase73_report), "74": contracts["phase74_cli_line"](phase74_report)}  # 新增代码+Phase75HumanlikeMatrix: 收集每个阶段稳定 CLI token 行；如果没有这行代码，总矩阵缺少可审计输出证据。
    phase_results = {phase_id: _phase75_phase_summary(phase_id, phase_reports[phase_id]) for phase_id in PHASE75_EXPECTED_PHASE_IDS}  # 新增代码+Phase75HumanlikeMatrix: 生成压缩阶段摘要；如果没有这行代码，外部 agent 需要解析庞大报告。
    phase_count = len(phase_results)  # 新增代码+Phase75HumanlikeMatrix: 计算实际覆盖阶段数；如果没有这行代码，少跑阶段无法进入总判断。
    all_phase_contracts_passed = bool(phase_count == PHASE75_EXPECTED_PHASE_COUNT and all(bool(phase_results[phase_id]["passed"]) for phase_id in PHASE75_EXPECTED_PHASE_IDS))  # 新增代码+Phase75HumanlikeMatrix: 判断所有阶段合同是否通过；如果没有这行代码，总矩阵可能只看部分高层字段。
    prompt_to_any_normal_app = bool(phase65_report.get("prompt_to_normal_windows_app") and phase67_report.get("prompt_task_plan") and phase69_report.get("app_launch") and not phase65_report.get("per_app_scripts_required") and not phase67_report.get("per_app_scripts_required"))  # 新增代码+Phase75HumanlikeMatrix: 汇总 prompt 到普通应用的通用路线；如果没有这行代码，最终矩阵可能退回每应用脚本。
    humanlike_observe_act_verify_loop = bool(phase65_report.get("humanlike_operator_contract") and phase66_report.get("uia_ocr_vision_fusion") and phase67_report.get("expected_result_per_step") and phase68_report.get("closed_loop_execution") and phase68_report.get("post_action_verification"))  # 新增代码+Phase75HumanlikeMatrix: 汇总拟人观察-动作-验证闭环；如果没有这行代码，最终矩阵可能只有规划没有闭环。
    generic_windows_app_control = bool(phase69_report.get("app_launch") and phase69_report.get("window_focus") and phase69_report.get("target_window_identity") and phase70_report.get("generic_click") and phase70_report.get("generic_type") and phase70_report.get("control_locator") and phase71_report.get("hotkey_action") and phase71_report.get("menu_navigation") and phase71_report.get("scroll_action") and phase71_report.get("drag_action") and phase72_report.get("authorized_real_app_actions"))  # 新增代码+Phase75HumanlikeMatrix: 汇总通用 Windows app 控制能力；如果没有这行代码，窗口、控件、输入或授权任一缺失都可能漏掉。
    per_app_scripts_required = bool(phase65_report.get("per_app_scripts_required") or phase67_report.get("per_app_scripts_required"))  # 新增代码+Phase75HumanlikeMatrix: 汇总是否仍要求应用专用脚本；如果没有这行代码，设计漂移无法进入最终 token。
    uia_ocr_vision_fusion = bool(phase66_report.get("uia_ocr_vision_fusion") and phase66_report.get("sensitive_text_boundary") and phase66_report.get("ocr_or_vision_slot"))  # 新增代码+Phase75HumanlikeMatrix: 汇总 UIA/OCR/vision 融合槽；如果没有这行代码，多源观察能力无法进入最终 token。
    mouse_keyboard_window_control = bool(phase69_report.get("window_focus") and phase70_report.get("high_level_tool_bridge") and phase71_report.get("continuous_mouse_path") and phase72_report.get("controlled_actions_expansion") and not phase72_report.get("uncontrolled_actions_expanded"))  # 新增代码+Phase75HumanlikeMatrix: 汇总鼠标键盘窗口控制协议；如果没有这行代码，输入层和窗口层可能被分开误判。
    failure_recovery = bool(phase68_report.get("failure_recovery") and phase68_report.get("blind_coordinate_chain_blocked"))  # 新增代码+Phase75HumanlikeMatrix: 汇总失败恢复和盲写阻断；如果没有这行代码，恢复能力无法进入最终 token。
    representative_real_apps_passed = bool(phase74_report.get("representative_real_apps_passed"))  # 新增代码+Phase75HumanlikeMatrix: 汇总代表性真实应用矩阵；如果没有这行代码，通用性样本无法进入最终 token。
    mspaint_pikachu_scenario = bool(phase74_report.get("mspaint_pikachu_scenario"))  # 新增代码+Phase75HumanlikeMatrix: 汇总 Paint 皮卡丘场景；如果没有这行代码，用户指定验收目标可能被漏掉。
    real_paint_app_control = bool(phase74_report.get("real_paint_app_control"))  # 新增代码+Phase75HumanlikeMatrix: 汇总真实 Paint 目标控制合同；如果没有这行代码，画图可能被伪场景替代。
    humanlike_drawing_actions = bool(phase74_report.get("humanlike_drawing_actions"))  # 新增代码+Phase75HumanlikeMatrix: 汇总拟人绘制动作证据；如果没有这行代码，Paint 可能不是鼠标轨迹式操作。
    direct_image_file_cheat = bool(phase74_report.get("direct_image_file_cheat") or not phase65_report.get("direct_file_cheat_blocked"))  # 新增代码+Phase75HumanlikeMatrix: 汇总直接图片/文件作弊风险；如果没有这行代码，Paint 验收可能被文件生成冒充。
    abort_safety = bool(phase72_report.get("abort_before_low_level_send"))  # 新增代码+Phase75HumanlikeMatrix: 汇总急停安全；如果没有这行代码，用户中断能力无法进入最终 token。
    high_risk_confirmation = bool(phase65_report.get("high_risk_confirmation_required") and phase67_report.get("high_risk_confirmation") and phase72_report.get("high_risk_default_refusal"))  # 新增代码+Phase75HumanlikeMatrix: 汇总高风险确认和默认拒绝；如果没有这行代码，登录/支付/管理员风险无法进入最终 token。
    visible_terminal_gate = bool(DEFAULT_PHASE75_SCENARIO_PATH.exists() and phase65_report.get("visible_terminal_acceptance_required"))  # 新增代码+Phase75HumanlikeMatrix: 汇总真实可见终端门禁；如果没有这行代码，场景 JSON 缺失也可能被误判完成。
    approval_bypass_blocked = bool(phase72_report.get("approval_bypass_blocked"))  # 新增代码+Phase75HumanlikeMatrix: 汇总审批绕过阻断；如果没有这行代码，外部 agent 伪造授权风险不会进入最终 token。
    uncontrolled_actions_expanded = bool(PHASE75_ACTIONS_EXPANDED or any(bool(phase_results[phase_id]["uncontrolled_actions_expanded"]) for phase_id in PHASE75_EXPECTED_PHASE_IDS if phase_id != "72") or bool(phase72_report.get("uncontrolled_actions_expanded")))  # 新增代码+Phase75HumanlikeMatrix: 判断是否存在无保护动作面扩张；如果没有这行代码，总矩阵无法区分受控能力和危险扩张。
    passed = bool(all_phase_contracts_passed and prompt_to_any_normal_app and humanlike_observe_act_verify_loop and generic_windows_app_control and not per_app_scripts_required and uia_ocr_vision_fusion and mouse_keyboard_window_control and failure_recovery and representative_real_apps_passed and mspaint_pikachu_scenario and real_paint_app_control and humanlike_drawing_actions and not direct_image_file_cheat and abort_safety and high_risk_confirmation and visible_terminal_gate and approval_bypass_blocked and not uncontrolled_actions_expanded)  # 新增代码+Phase75HumanlikeMatrix: 汇总最终通过条件；如果没有这行代码，main 无法用退出码表达失败。
    report = {"marker": PHASE75_HUMANLIKE_WINDOWS_OPERATOR_MARKER, "ok_token": PHASE75_HUMANLIKE_WINDOWS_OPERATOR_OK_TOKEN, "model": PHASE75_HUMANLIKE_WINDOWS_OPERATOR_MODEL, "phase_count": phase_count, "expected_phase_count": PHASE75_EXPECTED_PHASE_COUNT, "all_phase_contracts_passed": all_phase_contracts_passed, "prompt_to_any_normal_app": prompt_to_any_normal_app, "humanlike_observe_act_verify_loop": humanlike_observe_act_verify_loop, "generic_windows_app_control": generic_windows_app_control, "per_app_scripts_required": per_app_scripts_required, "uia_ocr_vision_fusion": uia_ocr_vision_fusion, "mouse_keyboard_window_control": mouse_keyboard_window_control, "failure_recovery": failure_recovery, "representative_real_apps_passed": representative_real_apps_passed, "mspaint_pikachu_scenario": mspaint_pikachu_scenario, "real_paint_app_control": real_paint_app_control, "humanlike_drawing_actions": humanlike_drawing_actions, "direct_image_file_cheat": direct_image_file_cheat, "abort_safety": abort_safety, "high_risk_confirmation": high_risk_confirmation, "visible_terminal_gate": visible_terminal_gate, "approval_bypass_blocked": approval_bypass_blocked, "uncontrolled_actions_expanded": uncontrolled_actions_expanded, "actions_expanded": PHASE75_ACTIONS_EXPANDED, "passed": passed, "phase_results": phase_results, "phase_cli_lines": phase_cli_lines, "state_dir": str(root), "scenario_path": str(DEFAULT_PHASE75_SCENARIO_PATH)}  # 新增代码+Phase75HumanlikeMatrix: 构造完整最终矩阵报告；如果没有这行代码，CLI、测试和真实终端拿不到结构化结果。
    report["matrix_artifact_path"] = str(atomic_write_json(root / "phase75_humanlike_operator_matrix.json", report))  # 新增代码+Phase75HumanlikeMatrix: 原子写入最终矩阵证据文件；如果没有这行代码，外部 agent 无法回放本次聚合结果。
    return report  # 新增代码+Phase75HumanlikeMatrix: 返回最终矩阵报告；如果没有这行代码，测试和 CLI 无法读取结果。
# 新增代码+Phase75HumanlikeMatrix: 函数段结束，run_phase75_humanlike_operator_matrix_contract 到此结束；如果没有这个边界说明，初学者不容易看出最终合同运行范围。


def phase75_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase75HumanlikeMatrix: 函数段开始，把最终矩阵报告转成稳定 CLI token 行；如果没有这个函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE75_HUMANLIKE_WINDOWS_OPERATOR_MARKER} {PHASE75_HUMANLIKE_WINDOWS_OPERATOR_OK_TOKEN} phase_count={int(report.get('phase_count', 0) or 0)} prompt_to_any_normal_app={_phase75_bool_token(report.get('prompt_to_any_normal_app'))} humanlike_observe_act_verify_loop={_phase75_bool_token(report.get('humanlike_observe_act_verify_loop'))} generic_windows_app_control={_phase75_bool_token(report.get('generic_windows_app_control'))} per_app_scripts_required={_phase75_bool_token(report.get('per_app_scripts_required'))} uia_ocr_vision_fusion={_phase75_bool_token(report.get('uia_ocr_vision_fusion'))} mouse_keyboard_window_control={_phase75_bool_token(report.get('mouse_keyboard_window_control'))} failure_recovery={_phase75_bool_token(report.get('failure_recovery'))} representative_real_apps_passed={_phase75_bool_token(report.get('representative_real_apps_passed'))} mspaint_pikachu_scenario={_phase75_bool_token(report.get('mspaint_pikachu_scenario'))} real_paint_app_control={_phase75_bool_token(report.get('real_paint_app_control'))} humanlike_drawing_actions={_phase75_bool_token(report.get('humanlike_drawing_actions'))} direct_image_file_cheat={_phase75_bool_token(report.get('direct_image_file_cheat'))} abort_safety={_phase75_bool_token(report.get('abort_safety'))} high_risk_confirmation={_phase75_bool_token(report.get('high_risk_confirmation'))} visible_terminal_gate={_phase75_bool_token(report.get('visible_terminal_gate'))} approval_bypass_blocked={_phase75_bool_token(report.get('approval_bypass_blocked'))} uncontrolled_actions_expanded={_phase75_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase75HumanlikeMatrix: 返回固定顺序 token 行；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase75HumanlikeMatrix: 函数段结束，phase75_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase75HumanlikeMatrix: 函数段开始，提供命令行入口；如果没有这个函数，真实终端无法直接运行 Phase75 自检。
    _ = argv  # 新增代码+Phase75HumanlikeMatrix: 保留 argv 供未来扩展；如果没有这行代码，参数存在但用途不清楚。
    report = run_phase75_humanlike_operator_matrix_contract()  # 新增代码+Phase75HumanlikeMatrix: 运行最终矩阵合同；如果没有这行代码，CLI 不会生成聚合证据。
    print(phase75_cli_line(report))  # 新增代码+Phase75HumanlikeMatrix: 打印稳定 token 行；如果没有这行代码，debug log 无法匹配 Phase75 成功。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase75HumanlikeMatrix: 打印结构化报告；如果没有这行代码，失败时不易复盘。
    print(PHASE75_HUMANLIKE_WINDOWS_OPERATOR_MARKER)  # 新增代码+Phase75HumanlikeMatrix: 单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase75HumanlikeMatrix: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase75HumanlikeMatrix: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_PHASE75_HUMANLIKE_OPERATOR_MATRIX_ROOT", "DEFAULT_PHASE75_SCENARIO_PATH", "PHASE75_ACTIONS_EXPANDED", "PHASE75_EXPECTED_PHASE_COUNT", "PHASE75_EXPECTED_PHASE_IDS", "PHASE75_HUMANLIKE_WINDOWS_OPERATOR_MARKER", "PHASE75_HUMANLIKE_WINDOWS_OPERATOR_MODEL", "PHASE75_HUMANLIKE_WINDOWS_OPERATOR_OK_TOKEN", "main", "phase75_cli_line", "run_phase75_humanlike_operator_matrix_contract"]  # 新增代码+Phase75HumanlikeMatrix: 限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase75HumanlikeMatrix: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase75HumanlikeMatrix: 用 main 返回码退出；如果没有这行代码，命令行状态不明确。
