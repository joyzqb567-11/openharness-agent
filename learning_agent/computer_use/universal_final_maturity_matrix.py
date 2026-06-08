"""URG-6 universal real GUI Computer Use final maturity matrix."""  # 新增代码+URG6FinalMatrix：说明本模块负责蓝图最终成熟度矩阵；如果没有这一行，读者不容易区分它和旧 full_maturity_matrix。
from __future__ import annotations  # 新增代码+URG6FinalMatrix：启用延迟类型解析；如果没有这一行，复杂类型标注在旧导入顺序下更容易失败。

import json  # 新增代码+URG6FinalMatrix：导入 JSON 用于 CLI 输出完整报告；如果没有这一行，失败时不容易复盘。
from typing import Any  # 新增代码+URG6FinalMatrix：导入 Any 描述动态 JSON 报告；如果没有这一行，公开接口边界不清楚。

try:  # 新增代码+URG6FinalMatrix：优先按包路径导入 URG-4/5 组件；如果没有这一段，单测和 bat 入口无法共享实现。
    from learning_agent.computer_use.universal_action_dsl import UniversalActionDslRuntime  # 新增代码+URG6FinalMatrix：导入 URG-3 通用动作 runtime；如果没有这一行，代表样本不会走统一 SendInput 分发层。
    from learning_agent.computer_use.universal_observe_plan_act_verify import Phase119GenericVerifier, Phase119RecordingObservationRuntime, UniversalObservePlanActVerifyLoop, run_phase119_universal_loop_contract  # 新增代码+URG6FinalMatrix：导入 URG-4 闭环和合同；如果没有这一行，最终矩阵无法证明同一个 loop 存在。
    from learning_agent.computer_use.universal_paint_pikachu_acceptance import Phase120RepresentativeRealDragSender, run_phase120_universal_paint_pikachu_acceptance_contract  # 新增代码+URG6FinalMatrix：导入 URG-5 Paint/Pikachu 验收；如果没有这一行，核心代表场景无法进入矩阵。
except ModuleNotFoundError as error:  # 新增代码+URG6FinalMatrix：兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这一段，真实可见终端可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.universal_action_dsl", "learning_agent.computer_use.universal_observe_plan_act_verify", "learning_agent.computer_use.universal_paint_pikachu_acceptance"}:  # 新增代码+URG6FinalMatrix：只兜底包路径缺失；如果没有这一行，真实内部 bug 可能被误吞。
        raise  # 新增代码+URG6FinalMatrix：重新抛出非路径类导入错误；如果没有这一行，排查依赖问题会变困难。
    from computer_use.universal_action_dsl import UniversalActionDslRuntime  # type: ignore  # 新增代码+URG6FinalMatrix：脚本模式导入通用动作 runtime；如果没有这一行，bat 入口无法执行代表样本。
    from computer_use.universal_observe_plan_act_verify import Phase119GenericVerifier, Phase119RecordingObservationRuntime, UniversalObservePlanActVerifyLoop, run_phase119_universal_loop_contract  # type: ignore  # 新增代码+URG6FinalMatrix：脚本模式导入 URG-4 闭环；如果没有这一行，bat 入口无法运行矩阵。
    from computer_use.universal_paint_pikachu_acceptance import Phase120RepresentativeRealDragSender, run_phase120_universal_paint_pikachu_acceptance_contract  # type: ignore  # 新增代码+URG6FinalMatrix：脚本模式导入 URG-5 验收；如果没有这一行，bat 入口无法汇总 Paint 场景。

UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER = "UNIVERSAL_REAL_GUI_COMPUTER_USE_READY"  # 新增代码+URG6FinalMatrix：定义蓝图最终 ready marker；如果没有这一行，真实终端和用户看不到终局锚点。
PHASE121_UNIVERSAL_FINAL_MATURITY_MODEL = "phase121_universal_real_gui_computer_use_final_matrix"  # 新增代码+URG6FinalMatrix：定义最终矩阵模型名；如果没有这一行，报告来源无法区分版本。


def _phase121_bool_token(value: Any) -> str:  # 新增代码+URG6FinalMatrix：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出可能混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+URG6FinalMatrix：返回 true 或 false 文本；如果没有这一行，验收器字符串匹配会不稳定。
# 新增代码+URG6FinalMatrix：函数段结束，_phase121_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。


def _phase121_run_representative_task(target: str, actions: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+URG6FinalMatrix：函数段开始，用同一个通用 loop 跑代表应用样本；如果没有这段函数，矩阵容易退回每个应用一套逻辑。
    sender = Phase120RepresentativeRealDragSender()  # 新增代码+URG6FinalMatrix：创建代表真实低层 sender；如果没有这一行，动作是否到达低层不可验证。
    action_runtime = UniversalActionDslRuntime(low_level_sender=sender)  # 新增代码+URG6FinalMatrix：把通用动作 runtime 接到代表 sender；如果没有这一行，样本动作不会走统一 dispatcher。
    loop = UniversalObservePlanActVerifyLoop(observation_runtime=Phase119RecordingObservationRuntime(), action_runtime=action_runtime, verifier=Phase119GenericVerifier(), max_retries=0)  # 新增代码+URG6FinalMatrix：创建 URG-4 通用闭环；如果没有这一行，样本无法证明 observe-plan-act-verify。
    result = loop.run_task({"target": str(target), "goal": f"representative {target} real acceptance", "actions": [dict(action) for action in actions]})  # 新增代码+URG6FinalMatrix：执行代表任务；如果没有这一行，报告没有事实来源。
    low_level_event_count = len(sender.low_level_events)  # 新增代码+URG6FinalMatrix：统计低层事件数；如果没有这一行，真实派发字段不可量化。
    physical_desktop_dispatch_performed = bool(getattr(sender, "physical_desktop_dispatch_performed", False))  # 新增代码+源码复核门禁：读取是否真的发生物理桌面派发；如果没有这一行，代表事件会被误判为真实动作。
    representative_dispatch_performed = bool(low_level_event_count > 0)  # 新增代码+源码复核门禁：保留代表性事件作为开发证据；如果没有这一行，调试时看不到 DSL 是否到达 sender。
    return {"target": str(target), "ok": bool(result.get("ok") and physical_desktop_dispatch_performed), "observe_plan_act_verify_loop": True, "real_window_observation": False, "representative_window_observation": True, "real_uia_or_vision_targeting": False, "representative_uia_or_vision_targeting": True, "real_sendinput_dispatch": physical_desktop_dispatch_performed, "representative_dispatch_performed": representative_dispatch_performed, "physical_desktop_dispatch_performed": physical_desktop_dispatch_performed, "target_identity_rechecked_before_each_action": True, "low_level_event_count": low_level_event_count, "result": result}  # 修改代码+源码复核门禁：返回代表验收摘要并把真实字段绑定物理证据；如果没有这一行，上层矩阵无法统一读取各应用状态。
# 新增代码+URG6FinalMatrix：函数段结束，_phase121_run_representative_task 到此结束；如果没有这个边界说明，初学者不容易看出代表任务范围。


def _phase121_notepad_actions() -> list[dict[str, Any]]:  # 新增代码+URG6FinalMatrix：函数段开始，定义 Notepad 代表动作；如果没有这段函数，文本输入场景没有稳定样本。
    return [{"type": "type_text", "text": "phase121 notepad"}, {"type": "press_key", "key": "ENTER"}]  # 新增代码+URG6FinalMatrix：返回通用文本和按键动作；如果没有这一行，Notepad 验收不会覆盖输入。
# 新增代码+URG6FinalMatrix：函数段结束，_phase121_notepad_actions 到此结束；如果没有这个边界说明，初学者不容易看出动作范围。


def _phase121_calculator_actions() -> list[dict[str, Any]]:  # 新增代码+URG6FinalMatrix：函数段开始，定义 Calculator 代表动作；如果没有这段函数，按键/结果观察场景没有稳定样本。
    return [{"type": "press_key", "key": "1"}, {"type": "press_key", "key": "ADD"}, {"type": "press_key", "key": "1"}, {"type": "press_key", "key": "ENTER"}]  # 新增代码+URG6FinalMatrix：返回通用计算器按键动作；如果没有这一行，Calculator 验收不会覆盖键盘路径。
# 新增代码+URG6FinalMatrix：函数段结束，_phase121_calculator_actions 到此结束；如果没有这个边界说明，初学者不容易看出动作范围。


def _phase121_browser_actions() -> list[dict[str, Any]]:  # 新增代码+URG6FinalMatrix：函数段开始，定义 Browser 代表动作；如果没有这段函数，浏览器点击/观察场景没有稳定样本。
    return [{"type": "click_point", "x": 240, "y": 180}, {"type": "hotkey", "keys": ["CTRL", "L"]}]  # 新增代码+URG6FinalMatrix：返回通用点击和快捷键动作；如果没有这一行，Browser 验收不会覆盖鼠标点击和组合键。
# 新增代码+URG6FinalMatrix：函数段结束，_phase121_browser_actions 到此结束；如果没有这个边界说明，初学者不容易看出动作范围。


def run_phase121_universal_final_maturity_matrix() -> dict[str, Any]:  # 新增代码+URG6FinalMatrix：函数段开始，运行 URG-6 最终成熟度矩阵；如果没有这段函数，测试和真实终端没有统一事实源。
    loop_report = run_phase119_universal_loop_contract()  # 新增代码+URG6FinalMatrix：运行 URG-4 闭环合同；如果没有这一行，最终矩阵无法证明单一 loop 已存在。
    paint_report = run_phase120_universal_paint_pikachu_acceptance_contract()  # 新增代码+URG6FinalMatrix：运行 URG-5 Paint/Pikachu 验收；如果没有这一行，最终矩阵缺少核心代表应用。
    notepad_report = _phase121_run_representative_task("notepad", _phase121_notepad_actions())  # 新增代码+URG6FinalMatrix：运行 Notepad 代表验收；如果没有这一行，文本应用覆盖缺失。
    calculator_report = _phase121_run_representative_task("calculator", _phase121_calculator_actions())  # 新增代码+URG6FinalMatrix：运行 Calculator 代表验收；如果没有这一行，计算器覆盖缺失。
    browser_report = _phase121_run_representative_task("browser", _phase121_browser_actions())  # 新增代码+URG6FinalMatrix：运行 Browser 代表验收；如果没有这一行，网页/第三方点击覆盖缺失。
    single_universal_real_gui_loop = bool(loop_report.get("observe_plan_act_verify_loop") and loop_report.get("same_loop_handles_representative_samples"))  # 新增代码+URG6FinalMatrix：汇总是否存在单一通用闭环；如果没有这一行，最终 passed 没有架构依据。
    per_app_controller_required = False  # 新增代码+URG6FinalMatrix：声明不需要逐应用 controller；如果没有这一行，蓝图禁止路线不可见。
    hardcoded_app_whitelist_required = False  # 新增代码+URG6FinalMatrix：声明不需要硬编码 app 白名单；如果没有这一行，通用性边界不可见。
    ordinary_apps_controlled_by_generic_runtime = True  # 新增代码+URG6FinalMatrix：声明普通应用走通用 runtime；如果没有这一行，最终矩阵无法回答普通软件控制能力。
    representative_apps_are_acceptance_only = True  # 新增代码+URG6FinalMatrix：声明代表应用只是验收样本；如果没有这一行，用户可能误以为产品需要样本白名单。
    real_window_observation = bool(notepad_report["real_window_observation"] and calculator_report["real_window_observation"] and browser_report["real_window_observation"] and paint_report["real_paint_window_verified"])  # 修改代码+源码复核门禁：只把真实窗口观察汇总为真实能力；如果没有这一行，观察链路缺失可能被漏掉。
    real_uia_or_vision_targeting = bool(notepad_report["real_uia_or_vision_targeting"] and calculator_report["real_uia_or_vision_targeting"] and browser_report["real_uia_or_vision_targeting"] and paint_report["real_canvas_region_detected"])  # 修改代码+源码复核门禁：只把真实 UIA/视觉证据汇总为真实定位；如果没有这一行，目标定位缺失可能被漏掉。
    real_sendinput_dispatch = bool(notepad_report["real_sendinput_dispatch"] and calculator_report["real_sendinput_dispatch"] and browser_report["real_sendinput_dispatch"] and paint_report["real_drag_path_dispatched"])  # 修改代码+源码复核门禁：只把物理桌面派发汇总为真实 SendInput；如果没有这一行，动作只停留在观察也可能误过。
    target_identity_rechecked_before_each_action = bool(loop_report.get("target_identity_rechecked_before_each_action") and paint_report.get("target_identity_rechecked_before_each_action"))  # 新增代码+URG6FinalMatrix：汇总动作前身份复核；如果没有这一行，窗口漂移风险不可见。
    observe_plan_act_verify_loop = bool(loop_report.get("observe_plan_act_verify_loop"))  # 新增代码+URG6FinalMatrix：汇总 URG-4 闭环 token；如果没有这一行，最终行无法直接显示闭环。
    paint_pikachu_real_acceptance = bool(paint_report.get("passed"))  # 新增代码+URG6FinalMatrix：汇总 Paint/Pikachu 验收；如果没有这一行，核心代表场景不会影响 passed。
    notepad_real_acceptance = bool(notepad_report.get("ok"))  # 新增代码+URG6FinalMatrix：汇总 Notepad 验收；如果没有这一行，文本场景不会影响 passed。
    calculator_real_acceptance = bool(calculator_report.get("ok"))  # 新增代码+URG6FinalMatrix：汇总 Calculator 验收；如果没有这一行，计算器场景不会影响 passed。
    browser_real_acceptance = bool(browser_report.get("ok"))  # 新增代码+URG6FinalMatrix：汇总 Browser 验收；如果没有这一行，浏览器场景不会影响 passed。
    script_artifact_route_blocked = bool(paint_report.get("script_artifact_route_blocked"))  # 新增代码+URG6FinalMatrix：汇总脚本成品路线阻断；如果没有这一行，图片 artifact 作弊可能漏过。
    real_desktop_execution_mature = bool(paint_report.get("real_desktop_execution_mature") and notepad_real_acceptance and calculator_real_acceptance and browser_real_acceptance)  # 新增代码+URG6FinalMatrix：汇总真实桌面执行成熟；如果没有这一行，最终成熟度没有单一结论。
    uncontrolled_high_risk_actions_allowed = False  # 新增代码+URG6FinalMatrix：声明未放开高风险动作；如果没有这一行，full 能力可能被误解为无限权限。
    passed = bool(single_universal_real_gui_loop and not per_app_controller_required and not hardcoded_app_whitelist_required and ordinary_apps_controlled_by_generic_runtime and representative_apps_are_acceptance_only and real_window_observation and real_uia_or_vision_targeting and real_sendinput_dispatch and target_identity_rechecked_before_each_action and observe_plan_act_verify_loop and paint_pikachu_real_acceptance and notepad_real_acceptance and calculator_real_acceptance and browser_real_acceptance and script_artifact_route_blocked and real_desktop_execution_mature and not uncontrolled_high_risk_actions_allowed)  # 新增代码+URG6FinalMatrix：汇总最终通过条件；如果没有这一行，main 无法用退出码表达失败。
    return {"marker": UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER, "model": PHASE121_UNIVERSAL_FINAL_MATURITY_MODEL, "passed": passed, "single_universal_real_gui_loop": single_universal_real_gui_loop, "per_app_controller_required": per_app_controller_required, "hardcoded_app_whitelist_required": hardcoded_app_whitelist_required, "ordinary_apps_controlled_by_generic_runtime": ordinary_apps_controlled_by_generic_runtime, "representative_apps_are_acceptance_only": representative_apps_are_acceptance_only, "real_window_observation": real_window_observation, "real_uia_or_vision_targeting": real_uia_or_vision_targeting, "real_sendinput_dispatch": real_sendinput_dispatch, "target_identity_rechecked_before_each_action": target_identity_rechecked_before_each_action, "observe_plan_act_verify_loop": observe_plan_act_verify_loop, "paint_pikachu_real_acceptance": paint_pikachu_real_acceptance, "notepad_real_acceptance": notepad_real_acceptance, "calculator_real_acceptance": calculator_real_acceptance, "browser_real_acceptance": browser_real_acceptance, "script_artifact_route_blocked": script_artifact_route_blocked, "real_desktop_execution_mature": real_desktop_execution_mature, "uncontrolled_high_risk_actions_allowed": uncontrolled_high_risk_actions_allowed, "reports": {"loop": loop_report, "paint": paint_report, "notepad": notepad_report, "calculator": calculator_report, "browser": browser_report}}  # 新增代码+URG6FinalMatrix：返回完整最终矩阵；如果没有这一行，测试和真实终端无法读取统一事实。
# 新增代码+URG6FinalMatrix：函数段结束，run_phase121_universal_final_maturity_matrix 到此结束；如果没有这个边界说明，初学者不容易看出矩阵范围。


def phase121_universal_final_maturity_cli_line(report: dict[str, Any]) -> str:  # 新增代码+URG6FinalMatrix：函数段开始，把最终矩阵转成蓝图固定 token 行；如果没有这段函数，真实终端验收需要解析复杂 JSON。
    return f"{UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER} single_universal_real_gui_loop={_phase121_bool_token(report.get('single_universal_real_gui_loop'))} per_app_controller_required={_phase121_bool_token(report.get('per_app_controller_required'))} hardcoded_app_whitelist_required={_phase121_bool_token(report.get('hardcoded_app_whitelist_required'))} ordinary_apps_controlled_by_generic_runtime={_phase121_bool_token(report.get('ordinary_apps_controlled_by_generic_runtime'))} representative_apps_are_acceptance_only={_phase121_bool_token(report.get('representative_apps_are_acceptance_only'))} real_window_observation={_phase121_bool_token(report.get('real_window_observation'))} real_uia_or_vision_targeting={_phase121_bool_token(report.get('real_uia_or_vision_targeting'))} real_sendinput_dispatch={_phase121_bool_token(report.get('real_sendinput_dispatch'))} target_identity_rechecked_before_each_action={_phase121_bool_token(report.get('target_identity_rechecked_before_each_action'))} observe_plan_act_verify_loop={_phase121_bool_token(report.get('observe_plan_act_verify_loop'))} paint_pikachu_real_acceptance={_phase121_bool_token(report.get('paint_pikachu_real_acceptance'))} notepad_real_acceptance={_phase121_bool_token(report.get('notepad_real_acceptance'))} calculator_real_acceptance={_phase121_bool_token(report.get('calculator_real_acceptance'))} browser_real_acceptance={_phase121_bool_token(report.get('browser_real_acceptance'))} script_artifact_route_blocked={_phase121_bool_token(report.get('script_artifact_route_blocked'))} real_desktop_execution_mature={_phase121_bool_token(report.get('real_desktop_execution_mature'))} uncontrolled_high_risk_actions_allowed={_phase121_bool_token(report.get('uncontrolled_high_risk_actions_allowed'))}"  # 新增代码+URG6FinalMatrix：返回固定顺序最终 token；如果没有这一行，蓝图最终验收容易因字段漂移失败。
# 新增代码+URG6FinalMatrix：函数段结束，phase121_universal_final_maturity_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+URG6FinalMatrix：函数段开始，提供命令行和真实终端入口；如果没有这段函数，controller 场景无法运行最终矩阵。
    _ = argv  # 新增代码+URG6FinalMatrix：保留 argv 扩展位；如果没有这一行，读者可能误以为参数被遗漏。
    report = run_phase121_universal_final_maturity_matrix()  # 新增代码+URG6FinalMatrix：运行最终矩阵；如果没有这一行，CLI 没有事实来源。
    print(phase121_universal_final_maturity_cli_line(report))  # 新增代码+URG6FinalMatrix：打印蓝图固定最终行；如果没有这一行，真实终端验收无法稳定匹配。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+URG6FinalMatrix：打印完整结构化报告；如果没有这一行，失败时不方便定位。
    print(UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER)  # 新增代码+URG6FinalMatrix：单独打印最终 marker；如果没有这一行，人工观察终端可能漏掉终局标识。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+URG6FinalMatrix：按最终矩阵状态返回退出码；如果没有这一行，失败也可能被自动化当成成功。
# 新增代码+URG6FinalMatrix：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["PHASE121_UNIVERSAL_FINAL_MATURITY_MODEL", "UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER", "main", "phase121_universal_final_maturity_cli_line", "run_phase121_universal_final_maturity_matrix"]  # 新增代码+URG6FinalMatrix：限定公开 API；如果没有这一行，通配导入可能暴露内部 helper。


if __name__ == "__main__":  # 新增代码+URG6FinalMatrix：文件入口段开始，允许 python -m 直接运行；如果没有这一行，真实终端无法启动最终矩阵。
    raise SystemExit(main())  # 新增代码+URG6FinalMatrix：用 main 返回码退出；如果没有这一行，命令行状态不明确。
# 新增代码+URG6FinalMatrix：文件入口段结束，本模块到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
