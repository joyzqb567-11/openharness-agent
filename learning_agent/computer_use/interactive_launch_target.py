"""交互式 `/computer launch <目标>` 的受控目标解析器。"""  # 新增代码+Phase107InteractiveLaunchTarget：说明本模块只负责把用户输入解析成安全目标；如果没有这行代码，读者会误以为这里负责真实启动应用。
from __future__ import annotations  # 新增代码+Phase107InteractiveLaunchTarget：启用延迟类型注解；如果没有这行代码，后续类型扩展更容易遇到导入顺序问题。

from typing import Any  # 新增代码+Phase107InteractiveLaunchTarget：导入 Any 描述 JSON 风格报告字段；如果没有这行代码，解析器接口对初学者不清晰。

PHASE107_INTERACTIVE_LAUNCH_TARGET_MARKER = "PHASE107_INTERACTIVE_LAUNCH_TARGET_READY"  # 新增代码+Phase107InteractiveLaunchTarget：定义 Phase107 ready marker；如果没有这行代码，测试和真实终端无法稳定定位目标解析结果。
PHASE107_INTERACTIVE_LAUNCH_TARGET_OK_TOKEN = "PHASE107_INTERACTIVE_LAUNCH_TARGET_OK"  # 新增代码+Phase107InteractiveLaunchTarget：定义 Phase107 成功 token；如果没有这行代码，解析成功和普通日志无法区分。
PHASE107_INTERACTIVE_LAUNCH_TARGET_MODEL = "phase107_interactive_launch_target"  # 新增代码+Phase107InteractiveLaunchTarget：定义报告模型名；如果没有这行代码，后续矩阵无法区分解析器版本。
PHASE107_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase107InteractiveLaunchTarget：声明本阶段没有扩张无边界动作；如果没有这行代码，full 模式可能被误读成任意应用控制。
PHASE107_REAL_LAUNCH_SUPPORTED_TARGETS = {"notepad"}  # 新增代码+Phase107InteractiveLaunchTarget：声明当前真实受控启动只支持 Notepad；如果没有这行代码，calc/mspaint 可能被误认为已能真实打开。
PHASE107_TARGET_ALIASES = {"notepad": "notepad", "notepad.exe": "notepad", "记事本": "notepad", "文本编辑器": "notepad", "mspaint": "mspaint", "mspaint.exe": "mspaint", "paint": "mspaint", "画图": "mspaint", "画图工具": "mspaint", "calc": "calc", "calc.exe": "calc", "calculator": "calc", "计算器": "calc"}  # 新增代码+Phase107InteractiveLaunchTarget：定义普通应用别名到规范目标的映射；如果没有这行代码，用户自然输入无法被稳定识别。
PHASE107_HIGH_RISK_TOKENS = ("powershell", "pwsh", "cmd", "terminal", "wt", "regedit", "registry", "control", "settings", "mmc", "taskmgr", "admin", "credential", "password", "security", "firewall")  # 新增代码+Phase107InteractiveLaunchTarget：定义高风险目标关键字；如果没有这行代码，终端、注册表和系统设置类目标可能进入启动链。


def _phase107_bool_token(value: Any) -> str:  # 新增代码+Phase107InteractiveLaunchTarget：函数段开始，把布尔值转成稳定小写文本；如果没有这段函数，CLI 输出会混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+Phase107InteractiveLaunchTarget：返回 true 或 false；如果没有这行代码，场景断言容易因大小写漂移失败。
# 新增代码+Phase107InteractiveLaunchTarget：函数段结束，_phase107_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


def _phase107_normalize_target(raw_target: Any) -> str:  # 新增代码+Phase107InteractiveLaunchTarget：函数段开始，规范化用户输入目标；如果没有这段函数，大小写、空格和引号会影响解析。
    text = str(raw_target or "").strip().lower()  # 新增代码+Phase107InteractiveLaunchTarget：转成小写并去掉首尾空格；如果没有这行代码，` Calc ` 和 `calc` 会被当成不同目标。
    text = text.strip("\"'`")  # 新增代码+Phase107InteractiveLaunchTarget：去掉常见包裹引号；如果没有这行代码，用户复制带引号的目标会被误判未知。
    return text  # 新增代码+Phase107InteractiveLaunchTarget：返回规范目标文本；如果没有这行代码，调用方拿不到清洗结果。
# 新增代码+Phase107InteractiveLaunchTarget：函数段结束，_phase107_normalize_target 到此结束；如果没有这个边界说明，初学者不容易看出清洗范围。


def _phase107_contains_high_risk_token(target: str) -> bool:  # 新增代码+Phase107InteractiveLaunchTarget：函数段开始，判断目标是否命中高风险关键字；如果没有这段函数，高风险判断会散落在调用方。
    lowered = str(target or "").lower()  # 新增代码+Phase107InteractiveLaunchTarget：再次小写化作为防御；如果没有这行代码，大小写可能绕过风险词。
    return any(token in lowered for token in PHASE107_HIGH_RISK_TOKENS)  # 新增代码+Phase107InteractiveLaunchTarget：返回是否命中风险词；如果没有这行代码，powershell/cmd/regedit 等不会被拦截。
# 新增代码+Phase107InteractiveLaunchTarget：函数段结束，_phase107_contains_high_risk_token 到此结束；如果没有这个边界说明，初学者不容易看出风险词范围。


def _phase107_report(raw_target: Any, normalized_target: str, canonical_target: str, decision: str, interactive_target_resolved: bool, safe_known_ordinary_app: bool, high_risk_refused: bool, unknown_target_refused: bool) -> dict[str, Any]:  # 新增代码+Phase107InteractiveLaunchTarget：函数段开始，构造统一目标解析报告；如果没有这段函数，成功和拒绝字段容易不一致。
    real_launch_supported = bool(canonical_target in PHASE107_REAL_LAUNCH_SUPPORTED_TARGETS)  # 新增代码+Phase107InteractiveLaunchTarget：判断当前目标是否已有真实受控启动链；如果没有这行代码，普通识别和真实支持会混淆。
    passed = bool(interactive_target_resolved and safe_known_ordinary_app and not high_risk_refused and not unknown_target_refused)  # 新增代码+Phase107InteractiveLaunchTarget：只有安全普通目标解析成功才算通过；如果没有这行代码，高风险拒绝可能误带成功 token。
    return {"marker": PHASE107_INTERACTIVE_LAUNCH_TARGET_MARKER, "ok_token": PHASE107_INTERACTIVE_LAUNCH_TARGET_OK_TOKEN, "model": PHASE107_INTERACTIVE_LAUNCH_TARGET_MODEL, "passed": passed, "raw_target": str(raw_target or ""), "normalized_target": normalized_target, "canonical_target": canonical_target, "decision": decision, "interactive_target_resolved": interactive_target_resolved, "safe_known_ordinary_app": safe_known_ordinary_app, "high_risk_refused": high_risk_refused, "unknown_target_refused": unknown_target_refused, "real_launch_supported": real_launch_supported, "real_desktop_touched": False, "uncontrolled_actions_expanded": PHASE107_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+Phase107InteractiveLaunchTarget：返回完整解析事实；如果没有这行代码，测试和终端无法共享同一合同。
# 新增代码+Phase107InteractiveLaunchTarget：函数段结束，_phase107_report 到此结束；如果没有这个边界说明，初学者不容易看出报告构造范围。


def resolve_interactive_launch_target(raw_target: Any) -> dict[str, Any]:  # 新增代码+Phase107InteractiveLaunchTarget：函数段开始，解析用户输入的启动目标；如果没有这段函数，`/computer launch` 只能硬编码 Notepad。
    normalized = _phase107_normalize_target(raw_target)  # 新增代码+Phase107InteractiveLaunchTarget：先清洗用户输入；如果没有这行代码，别名和风险判断不稳定。
    if not normalized:  # 新增代码+Phase107InteractiveLaunchTarget：检查是否没有目标；如果没有这行代码，空目标可能误走默认应用。
        return _phase107_report(raw_target, normalized, "", "phase107_empty_target_refused", False, False, False, True)  # 新增代码+Phase107InteractiveLaunchTarget：返回空目标拒绝；如果没有这行代码，用户缺参时原因不可见。
    if _phase107_contains_high_risk_token(normalized):  # 新增代码+Phase107InteractiveLaunchTarget：先拦截高风险关键字；如果没有这行代码，powershell/cmd 可能被别名逻辑漏掉。
        return _phase107_report(raw_target, normalized, normalized, "phase107_high_risk_target_refused", False, False, True, False)  # 新增代码+Phase107InteractiveLaunchTarget：返回高风险零副作用拒绝；如果没有这行代码，拒绝路径没有稳定字段。
    canonical = PHASE107_TARGET_ALIASES.get(normalized, "")  # 新增代码+Phase107InteractiveLaunchTarget：按别名表查规范目标；如果没有这行代码，中文和常见英文别名无法识别。
    if not canonical:  # 新增代码+Phase107InteractiveLaunchTarget：检查是否未知普通目标；如果没有这行代码，未知 exe 可能被误当成安全目标。
        return _phase107_report(raw_target, normalized, normalized, "phase107_unknown_target_refused", False, False, False, True)  # 新增代码+Phase107InteractiveLaunchTarget：返回未知目标拒绝；如果没有这行代码，用户不知道为什么没启动。
    return _phase107_report(raw_target, normalized, canonical, "phase107_target_resolved", True, True, False, False)  # 新增代码+Phase107InteractiveLaunchTarget：返回安全普通目标解析结果；如果没有这行代码，调用方无法区分 notepad/calc/mspaint。
# 新增代码+Phase107InteractiveLaunchTarget：函数段结束，resolve_interactive_launch_target 到此结束；如果没有这个边界说明，初学者不容易看出解析入口范围。


def phase107_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase107InteractiveLaunchTarget：函数段开始，把目标解析报告转成稳定 token 行；如果没有这段函数，可见终端验收要解析复杂 JSON。
    ok_token = f" {PHASE107_INTERACTIVE_LAUNCH_TARGET_OK_TOKEN}" if bool(report.get("passed", False)) else ""  # 新增代码+Phase107InteractiveLaunchTarget：只在安全普通目标解析成功时输出 OK；如果没有这行代码，高风险拒绝可能被误判成功。
    return f"{PHASE107_INTERACTIVE_LAUNCH_TARGET_MARKER}{ok_token} canonical_target={report.get('canonical_target', '')} interactive_target_resolved={_phase107_bool_token(report.get('interactive_target_resolved', False))} safe_known_ordinary_app={_phase107_bool_token(report.get('safe_known_ordinary_app', False))} high_risk_refused={_phase107_bool_token(report.get('high_risk_refused', False))} unknown_target_refused={_phase107_bool_token(report.get('unknown_target_refused', False))} real_launch_supported={_phase107_bool_token(report.get('real_launch_supported', False))} real_desktop_touched={_phase107_bool_token(report.get('real_desktop_touched', False))} uncontrolled_actions_expanded={_phase107_bool_token(report.get('uncontrolled_actions_expanded', False))}"  # 新增代码+Phase107InteractiveLaunchTarget：返回固定顺序 token；如果没有这行代码，测试和场景会因字段顺序漂移不稳定。
# 新增代码+Phase107InteractiveLaunchTarget：函数段结束，phase107_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 输出范围。


__all__ = ["PHASE107_INTERACTIVE_LAUNCH_TARGET_MARKER", "PHASE107_INTERACTIVE_LAUNCH_TARGET_MODEL", "PHASE107_INTERACTIVE_LAUNCH_TARGET_OK_TOKEN", "PHASE107_REAL_LAUNCH_SUPPORTED_TARGETS", "PHASE107_TARGET_ALIASES", "PHASE107_UNCONTROLLED_ACTIONS_EXPANDED", "phase107_cli_line", "resolve_interactive_launch_target"]  # 新增代码+Phase107InteractiveLaunchTarget：限定公开导出名称；如果没有这行代码，通配导入会暴露内部 helper。
