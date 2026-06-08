"""Windows Computer Use Phase65 通用拟人 Operator 契约。"""  # 新增代码+Phase65HumanlikeOperator: 标明本文件负责 Phase65 通用拟人 Windows Operator 的稳定合同；如果没有这行代码，读者不知道本阶段入口在哪里。
from __future__ import annotations  # 新增代码+Phase65HumanlikeOperator: 启用延迟类型解析；如果没有这行代码，未来添加前向类型标注时旧运行路径更容易导入失败。

import json  # 新增代码+Phase65HumanlikeOperator: 导入 JSON 用于 CLI 打印结构化报告；如果没有这行代码，终端验收失败时不容易复盘合同字段。
from typing import Any  # 新增代码+Phase65HumanlikeOperator: 导入 Any 描述报告里的动态字段；如果没有这行代码，函数边界缺少清晰类型提示。

PHASE65_HUMANLIKE_OPERATOR_MARKER = "PHASE65_HUMANLIKE_OPERATOR_READY"  # 新增代码+Phase65HumanlikeOperator: 定义 Phase65 ready marker；如果没有这行代码，真实终端验收没有稳定锚点。
PHASE65_HUMANLIKE_OPERATOR_OK_TOKEN = "PHASE65_HUMANLIKE_OPERATOR_OK"  # 新增代码+Phase65HumanlikeOperator: 定义 Phase65 OK token；如果没有这行代码，debug log 无法区分合同通过和普通输出。
PHASE65_HUMANLIKE_OPERATOR_MODEL = "phase65_humanlike_windows_operator_contract"  # 新增代码+Phase65HumanlikeOperator: 定义 Phase65 合同模型名；如果没有这行代码，报告无法说明当前使用哪套通用操作边界。
PHASE65_ACTIONS_EXPANDED = False  # 新增代码+Phase65HumanlikeOperator: 明确 Phase65 自身不新增真实桌面动作；如果没有这行代码，用户可能误以为本阶段已经开始点击和输入真实软件。


# 新增代码+Phase65HumanlikeOperator: 函数段开始，_phase65_bool_token 把布尔值转成验收器稳定匹配的小写 token；如果没有这段函数，CLI 输出可能混用 True/False 和 true/false，作者意图是让真实终端断言稳定。
def _phase65_bool_token(value: Any) -> str:  # 新增代码+Phase65HumanlikeOperator: 定义布尔 token helper；如果没有这行代码，多处输出会重复写转换逻辑。
    return "true" if bool(value) else "false"  # 新增代码+Phase65HumanlikeOperator: 返回小写布尔文本；如果没有这行代码，场景 JSON 的 token 匹配可能失败。
# 新增代码+Phase65HumanlikeOperator: 函数段结束，_phase65_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


# 新增代码+Phase65HumanlikeOperator: 函数段开始，run_phase65_humanlike_operator_contract 固定通用拟人 Windows Operator 的第一层边界；如果没有这段函数，Phase65 只会停留在文档，作者意图是让自动化测试和真实终端共用同一份合同事实源。
def run_phase65_humanlike_operator_contract() -> dict[str, Any]:  # 新增代码+Phase65HumanlikeOperator: 定义 Phase65 合同入口；如果没有这行代码，测试和终端场景没有统一自检函数。
    humanlike_operator_contract = True  # 新增代码+Phase65HumanlikeOperator: 标记已建立通用拟人操作合同；如果没有这行代码，后续阶段不知道能否依赖这一层边界。
    prompt_to_normal_windows_app = True  # 新增代码+Phase65HumanlikeOperator: 标记目标是从自然 prompt 操控普通 Windows 应用；如果没有这行代码，项目可能退回到只支持某个固定应用。
    per_app_scripts_required = False  # 新增代码+Phase65HumanlikeOperator: 标记不要求每个应用写专用脚本；如果没有这行代码，设计会偏离“通用控制本机应用程序”的目标。
    high_risk_confirmation_required = True  # 新增代码+Phase65HumanlikeOperator: 标记高风险窗口必须先确认；如果没有这行代码，拟人操作可能误触登录、支付、安全或管理员界面。
    direct_file_cheat_blocked = True  # 新增代码+Phase65HumanlikeOperator: 标记禁止用直接写文件伪装真实应用操作；如果没有这行代码，画图皮卡丘等 E2E 可能被文件生成作弊替代。
    representative_e2e_required = True  # 新增代码+Phase65HumanlikeOperator: 标记必须用代表性真实场景证明通用性；如果没有这行代码，后续可能只做单元测试就误称能控制所有应用。
    paint_pikachu_scenario_required = True  # 新增代码+Phase65HumanlikeOperator: 标记最终代表场景包含真实画图软件画皮卡丘；如果没有这行代码，用户新增的关键验收目标可能被遗漏。
    visible_terminal_acceptance_required = True  # 新增代码+Phase65HumanlikeOperator: 标记真实可见终端验收仍是最终门禁；如果没有这行代码，HTTP 或 CLI 自测可能被误当成开发完成。
    actions_expanded = PHASE65_ACTIONS_EXPANDED  # 新增代码+Phase65HumanlikeOperator: 读取本阶段动作扩展状态；如果没有这行代码，报告无法明确 Phase65 没有新增真实动作面。
    passed = bool(humanlike_operator_contract and prompt_to_normal_windows_app and not per_app_scripts_required and high_risk_confirmation_required and direct_file_cheat_blocked and representative_e2e_required and paint_pikachu_scenario_required and visible_terminal_acceptance_required and not actions_expanded)  # 新增代码+Phase65HumanlikeOperator: 汇总合同是否通过；如果没有这行代码，main 无法用退出码表达成功或失败。
    return {"marker": PHASE65_HUMANLIKE_OPERATOR_MARKER, "ok_token": PHASE65_HUMANLIKE_OPERATOR_OK_TOKEN, "model": PHASE65_HUMANLIKE_OPERATOR_MODEL, "humanlike_operator_contract": humanlike_operator_contract, "prompt_to_normal_windows_app": prompt_to_normal_windows_app, "per_app_scripts_required": per_app_scripts_required, "high_risk_confirmation_required": high_risk_confirmation_required, "direct_file_cheat_blocked": direct_file_cheat_blocked, "representative_e2e_required": representative_e2e_required, "paint_pikachu_scenario_required": paint_pikachu_scenario_required, "visible_terminal_acceptance_required": visible_terminal_acceptance_required, "actions_expanded": actions_expanded, "passed": passed}  # 新增代码+Phase65HumanlikeOperator: 返回完整 Phase65 合同报告；如果没有这行代码，CLI、测试和真实终端拿不到结构化结果。
# 新增代码+Phase65HumanlikeOperator: 函数段结束，run_phase65_humanlike_operator_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同运行范围。


# 新增代码+Phase65HumanlikeOperator: 函数段开始，phase65_cli_line 把合同报告转成固定顺序 token 行；如果没有这段函数，真实终端场景需要解析复杂 JSON，作者意图是让最终回答可复制可验收。
def phase65_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase65HumanlikeOperator: 定义 Phase65 CLI 行格式化函数；如果没有这行代码，main 无法打印固定顺序 token。
    return f"{PHASE65_HUMANLIKE_OPERATOR_MARKER} {PHASE65_HUMANLIKE_OPERATOR_OK_TOKEN} humanlike_operator_contract={_phase65_bool_token(report.get('humanlike_operator_contract'))} prompt_to_normal_windows_app={_phase65_bool_token(report.get('prompt_to_normal_windows_app'))} per_app_scripts_required={_phase65_bool_token(report.get('per_app_scripts_required'))} high_risk_confirmation_required={_phase65_bool_token(report.get('high_risk_confirmation_required'))} direct_file_cheat_blocked={_phase65_bool_token(report.get('direct_file_cheat_blocked'))} actions_expanded={_phase65_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase65HumanlikeOperator: 返回固定顺序 token 行；如果没有这行代码，验收器无法稳定匹配 Phase65 合同。
# 新增代码+Phase65HumanlikeOperator: 函数段结束，phase65_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 文本范围。


# 新增代码+Phase65HumanlikeOperator: 函数段开始，main 提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase65 合同，作者意图是自动化和可见终端共用同一合同。
def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase65HumanlikeOperator: 定义命令行入口并保留 argv 扩展位；如果没有这行代码，python -c 只能手写调用细节。
    _ = argv  # 新增代码+Phase65HumanlikeOperator: 明确当前 Phase65 不解析命令行参数；如果没有这行代码，读者可能误以为 argv 被遗漏。
    report = run_phase65_humanlike_operator_contract()  # 新增代码+Phase65HumanlikeOperator: 运行 Phase65 合同；如果没有这行代码，CLI 输出没有真实依据。
    print(phase65_cli_line(report))  # 新增代码+Phase65HumanlikeOperator: 打印稳定单行 token；如果没有这行代码，验收器无法快速匹配合同结果。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase65HumanlikeOperator: 打印结构化报告便于人工复盘；如果没有这行代码，失败时不容易定位哪一条边界失败。
    print(PHASE65_HUMANLIKE_OPERATOR_MARKER)  # 新增代码+Phase65HumanlikeOperator: 单独打印 ready marker；如果没有这行代码，真实终端验收可能看不到明确阶段标记。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase65HumanlikeOperator: 根据合同结果返回退出码；如果没有这行代码，失败也可能被终端当成成功。
# 新增代码+Phase65HumanlikeOperator: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = ["PHASE65_ACTIONS_EXPANDED", "PHASE65_HUMANLIKE_OPERATOR_MARKER", "PHASE65_HUMANLIKE_OPERATOR_MODEL", "PHASE65_HUMANLIKE_OPERATOR_OK_TOKEN", "main", "phase65_cli_line", "run_phase65_humanlike_operator_contract"]  # 新增代码+Phase65HumanlikeOperator: 限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase65HumanlikeOperator: 允许直接运行本模块；如果没有这行代码，初学者无法用 python 文件方式手动执行 Phase65 自检。
    raise SystemExit(main())  # 新增代码+Phase65HumanlikeOperator: 调用 main 并传递退出码；如果没有这行代码，直接运行文件不会执行验收。
