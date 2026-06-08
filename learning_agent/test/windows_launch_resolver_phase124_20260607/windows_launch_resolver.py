"""Windows Computer Use 多后端启动解析器。"""  # 新增代码+WindowsLaunchResolver：说明本模块只负责把应用候选解析成启动计划；如果没有这一行，读者容易把 resolver 误解成已经执行真实启动。
from __future__ import annotations  # 新增代码+WindowsLaunchResolver：启用延迟类型注解；如果没有这一行，后续类型提示在脚本兼容模式下更容易出现导入顺序问题。
from typing import Any  # 新增代码+WindowsLaunchResolver：导入 Any 描述 JSON 风格候选和报告；如果没有这一行，接口输入输出含义不清楚。

try:  # 新增代码+WindowsLaunchResolver：优先按包路径导入统一应用清单；如果没有这一行，项目根目录运行时无法复用 Phase122 inventory。
    from learning_agent.computer_use.windows_app_inventory import build_windows_app_inventory  # 新增代码+WindowsLaunchResolver：读取统一 Windows 应用清单构造器；如果没有这一行，resolver 会重新发明一套候选清洗逻辑。
except ModuleNotFoundError as error:  # 新增代码+WindowsLaunchResolver：兼容 start_oauth_agent.bat 的脚本式导入；如果没有这一行，真实可见终端入口可能因为包路径不同失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.windows_app_inventory"}:  # 新增代码+WindowsLaunchResolver：只兜底包路径缺失；如果没有这一行，inventory 内部真实 bug 会被误吞。
        raise  # 新增代码+WindowsLaunchResolver：重新抛出真实内部错误；如果没有这一行，排查 resolver 失败会被隐藏。
    from computer_use.windows_app_inventory import build_windows_app_inventory  # type: ignore  # 新增代码+WindowsLaunchResolver：脚本模式导入统一 inventory；如果没有这一行，bat 启动方式下 resolver 不可用。

PHASE124_WINDOWS_LAUNCH_RESOLVER_MARKER = "PHASE124_WINDOWS_LAUNCH_RESOLVER_READY"  # 新增代码+WindowsLaunchResolver：定义 resolver ready 标记；如果没有这一行，测试和终端输出无法稳定识别本阶段能力。
PHASE124_WINDOWS_LAUNCH_RESOLVER_OK_TOKEN = "PHASE124_WINDOWS_LAUNCH_RESOLVER_OK"  # 新增代码+WindowsLaunchResolver：定义 resolver 成功 token；如果没有这一行，成功计划和普通报告难以区分。
PHASE124_WINDOWS_LAUNCH_RESOLVER_MODEL = "phase124_windows_launch_resolver"  # 新增代码+WindowsLaunchResolver：定义报告模型名；如果没有这一行，能力矩阵无法区分 resolver 版本。
PHASE124_HIGH_RISK_TOKENS = ("powershell", "pwsh", "cmd", "terminal", "wt", "regedit", "registry", "control", "settings", "mmc", "taskmgr", "admin", "administrator", "credential", "password", "security", "firewall", "defender", "services")  # 新增代码+WindowsLaunchResolver：定义启动解析阶段的高风险词；如果没有这一行，动态发现可能把终端或系统工具当普通应用计划。
PHASE124_LAUNCHABLE_KINDS = {"exe", "start_process_exe", "appx", "aumid", "shortcut"}  # 新增代码+WindowsLaunchResolver：定义 resolver 认为可形成启动计划的类型；如果没有这一行，未知类型可能被含糊放行。
PHASE124_NO_REAL_BACKEND_KINDS = {"appx_aumid", "start_menu_shortcut"}  # 新增代码+WindowsLaunchResolver：标记当前 Phase110 尚未真实接通的后端；如果没有这一行，后续 Popen 后端可能误吃非 argv 计划。

def _phase124_clean_text(value: Any) -> str:  # 新增代码+WindowsLaunchResolver：函数段开始，清洗 resolver 中使用的短文本；如果没有这段函数，大小写、引号和空格会让匹配不稳定。
    text = str(value or "").strip().strip("\"'`")  # 新增代码+WindowsLaunchResolver：去掉空白和常见包裹引号；如果没有这一行，复制来的 `"calc"` 会被当成不同应用。
    return " ".join(text.split())  # 新增代码+WindowsLaunchResolver：压缩连续空白；如果没有这一行，候选匹配和风险检查会因为多空格漂移。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_clean_text 到此结束；如果没有这个边界说明，用户不容易看出文本清洗范围。

def _phase124_lower(value: Any) -> str:  # 新增代码+WindowsLaunchResolver：函数段开始，把任意值清洗成小写；如果没有这段函数，匹配逻辑会重复写清洗代码。
    return _phase124_clean_text(value).lower()  # 新增代码+WindowsLaunchResolver：返回小写清洗文本；如果没有这一行，大小写差异会导致候选无法命中。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_lower 到此结束；如果没有这个边界说明，用户不容易看出大小写规范范围。

def _phase124_basename(value: Any) -> str:  # 新增代码+WindowsLaunchResolver：函数段开始，从路径或标识中取安全基名；如果没有这段函数，报告可能泄露长路径或把路径当 exe。
    text = _phase124_clean_text(value)  # 新增代码+WindowsLaunchResolver：先清洗输入文本；如果没有这一行，带引号路径会污染基名。
    return text.replace("\\", "/").rsplit("/", 1)[-1].strip()  # 新增代码+WindowsLaunchResolver：只取最后一段名称；如果没有这一行，Start Menu 路径和 App Paths 路径会进入模型可见计划。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_basename 到此结束；如果没有这个边界说明，用户不容易看出基名处理范围。

def _phase124_candidate_texts(candidate: dict[str, Any]) -> list[str]:  # 新增代码+WindowsLaunchResolver：函数段开始，收集候选可匹配文本；如果没有这段函数，display/app/alias/launch_id 匹配会分散在多处。
    values = [candidate.get("display_name", ""), candidate.get("app_name", ""), candidate.get("launch_id", ""), candidate.get("executable", "")]  # 新增代码+WindowsLaunchResolver：收集核心身份字段；如果没有这一行，用户输入可能只能命中一个字段。
    aliases = candidate.get("aliases", ()) or ()  # 新增代码+WindowsLaunchResolver：读取候选别名集合；如果没有这一行，中文别名和英文别名无法参与匹配。
    return [_phase124_lower(value) for value in [*values, *list(aliases)] if _phase124_clean_text(value)]  # 新增代码+WindowsLaunchResolver：返回非空小写文本列表；如果没有这一行，匹配函数拿不到统一输入。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_candidate_texts 到此结束；如果没有这个边界说明，用户不容易看出候选文本范围。

def _phase124_contains_high_risk(*values: Any) -> bool:  # 新增代码+WindowsLaunchResolver：函数段开始，检查启动目标是否包含高风险词；如果没有这段函数，resolver 会削弱原有安全边界。
    haystack = " ".join(_phase124_lower(value) for value in values)  # 新增代码+WindowsLaunchResolver：合并所有身份字段；如果没有这一行，只检查用户输入会漏掉候选自身风险。
    return any(token in haystack for token in PHASE124_HIGH_RISK_TOKENS)  # 新增代码+WindowsLaunchResolver：命中任一风险词就拒绝；如果没有这一行，PowerShell/CMD 等目标可能进入启动计划。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_contains_high_risk 到此结束；如果没有这个边界说明，用户不容易看出风险检查范围。

def _phase124_match_score(query: str, candidate: dict[str, Any]) -> int:  # 新增代码+WindowsLaunchResolver：函数段开始，为候选计算匹配分；如果没有这段函数，多个来源候选无法稳定排序。
    if not query:  # 新增代码+WindowsLaunchResolver：检查空查询；如果没有这一行，空输入可能误选第一个应用。
        return 0  # 新增代码+WindowsLaunchResolver：空查询不得分；如果没有这一行，缺少目标也会产生计划。
    texts = _phase124_candidate_texts(candidate)  # 新增代码+WindowsLaunchResolver：读取候选匹配文本；如果没有这一行，后续无法统一比较。
    if query in texts:  # 新增代码+WindowsLaunchResolver：优先精确匹配；如果没有这一行，calc 可能输给较长的包含匹配。
        return 100  # 新增代码+WindowsLaunchResolver：精确命中最高分；如果没有这一行，排序不够稳定。
    if any(query in text or text in query for text in texts):  # 新增代码+WindowsLaunchResolver：允许包含匹配；如果没有这一行，中文短词或 exe 短名可能无法命中。
        return 50  # 新增代码+WindowsLaunchResolver：包含匹配给中等分；如果没有这一行，相关候选无法被选中。
    return 0  # 新增代码+WindowsLaunchResolver：没有匹配时返回 0；如果没有这一行，函数没有稳定默认值。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_match_score 到此结束；如果没有这个边界说明，用户不容易看出匹配打分范围。

def _phase124_select_candidate(app_name: Any, candidates: list[dict[str, Any]] | None) -> dict[str, Any]:  # 新增代码+WindowsLaunchResolver：函数段开始，从候选清单中选择启动目标；如果没有这段函数，resolver 只能处理外部指定单个候选。
    query = _phase124_lower(app_name)  # 新增代码+WindowsLaunchResolver：清洗用户或模型给出的 app 名；如果没有这一行，大小写和空格会导致匹配失败。
    catalog = build_windows_app_inventory(candidates=candidates, include_common=True)  # 新增代码+WindowsLaunchResolver：复用统一 inventory 清洗和排序；如果没有这一行，resolver 会绕开 ClaudeCode 式应用清单层。
    scored = [(entry, _phase124_match_score(query, entry)) for entry in catalog]  # 新增代码+WindowsLaunchResolver：给每个候选计算匹配分；如果没有这一行，无法选择最相关应用。
    matching = [item for item in scored if item[1] > 0]  # 新增代码+WindowsLaunchResolver：只保留命中候选；如果没有这一行，错误应用可能被默认选中。
    matching.sort(key=lambda item: (-item[1], int(item[0].get("source_priority", 99)), str(item[0].get("display_name", "")).casefold()))  # 新增代码+WindowsLaunchResolver：按匹配分、来源优先级和名称排序；如果没有这一行，卸载记录可能覆盖真实入口。
    return dict(matching[0][0]) if matching else {}  # 新增代码+WindowsLaunchResolver：返回最佳候选副本或空字典；如果没有这一行，调用方无法区分命中和未命中。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_select_candidate 到此结束；如果没有这个边界说明，用户不容易看出候选选择范围。

def _phase124_base_plan(candidate: dict[str, Any], safe_to_launch: bool, refusal_reason: str = "") -> dict[str, Any]:  # 新增代码+WindowsLaunchResolver：函数段开始，生成所有后端共享的计划字段；如果没有这段函数，各后端报告会漂移。
    return {"marker": PHASE124_WINDOWS_LAUNCH_RESOLVER_MARKER, "ok_token": PHASE124_WINDOWS_LAUNCH_RESOLVER_OK_TOKEN if safe_to_launch else "", "model": PHASE124_WINDOWS_LAUNCH_RESOLVER_MODEL, "resolver_used": True, "safe_to_launch": bool(safe_to_launch), "refusal_reason": str(refusal_reason or ""), "display_name": str(candidate.get("display_name", "") or ""), "app_name": str(candidate.get("app_name", "") or ""), "launch_kind": str(candidate.get("launch_kind", "") or ""), "launch_id": str(candidate.get("launch_id", "") or ""), "source": str(candidate.get("source", "") or ""), "installed_app_verified": bool(candidate.get("installed_app_verified", False)), "launch_backend": "", "launch_verb": "", "command_shape": "", "executable": "", "arguments": [], "aumid": "", "shortcut_id": "", "changes_registry": False, "changes_system_settings": False, "requires_admin": False, "uses_shell_string": False, "actions_expanded": False, "not_hard_whitelist": True, "phase110_backend_supported": False, "phase110_backend_support_reason": ""}  # 新增代码+WindowsLaunchResolver：返回通用结构化计划；如果没有这一行，Phase108/Phase110 无法共享同一事实格式。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_base_plan 到此结束；如果没有这个边界说明，用户不容易看出共享字段范围。

def _phase124_exe_plan(candidate: dict[str, Any]) -> dict[str, Any]:  # 新增代码+WindowsLaunchResolver：函数段开始，生成 exe/argv 启动计划；如果没有这段函数，普通 Win32 应用无法进入安全后端。
    plan = _phase124_base_plan(candidate, True)  # 新增代码+WindowsLaunchResolver：先创建共享计划；如果没有这一行，exe 后端会缺少审计字段。
    executable = _phase124_basename(candidate.get("launch_id") or candidate.get("executable") or candidate.get("app_name") or candidate.get("display_name"))  # 新增代码+WindowsLaunchResolver：从候选身份取 exe 名；如果没有这一行，Popen 后端拿不到目标程序。
    if executable and not executable.lower().endswith(".exe"):  # 新增代码+WindowsLaunchResolver：检查是否缺少 exe 后缀；如果没有这一行，普通短名在旧后端可能不稳定。
        executable = f"{executable}.exe"  # 新增代码+WindowsLaunchResolver：补齐 exe 后缀；如果没有这一行，argv 后端可能依赖环境解析造成漂移。
    plan.update({"launch_backend": "argv_no_shell", "launch_verb": "Start-Process", "command_shape": "argv_no_shell", "executable": executable, "arguments": [], "phase110_backend_supported": True, "phase110_backend_support_reason": "supported_by_phase110_popen_argv"})  # 新增代码+WindowsLaunchResolver：写入 argv 后端字段；如果没有这一行，Phase110 不知道这是可执行计划。
    return plan  # 新增代码+WindowsLaunchResolver：返回 exe 启动计划；如果没有这一行，调用方拿不到结果。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_exe_plan 到此结束；如果没有这个边界说明，用户不容易看出 exe 计划范围。

def _phase124_appx_plan(candidate: dict[str, Any]) -> dict[str, Any]:  # 新增代码+WindowsLaunchResolver：函数段开始，生成 AppX/AUMID 启动计划；如果没有这段函数，商店应用会继续被误猜成 exe。
    plan = _phase124_base_plan(candidate, True)  # 新增代码+WindowsLaunchResolver：先创建共享计划；如果没有这一行，AppX 后端会缺少审计字段。
    aumid = _phase124_clean_text(candidate.get("launch_id") or candidate.get("aumid"))  # 新增代码+WindowsLaunchResolver：读取完整 AUMID；如果没有这一行，AppX 应用无法精确定位。
    plan.update({"launch_backend": "appx_aumid", "launch_verb": "ShellExecuteAppUserModelId", "command_shape": "aumid_no_shell", "aumid": aumid, "phase110_backend_supported": False, "phase110_backend_support_reason": "phase110_popen_backend_does_not_launch_aumid_yet"})  # 新增代码+WindowsLaunchResolver：写入 AUMID 后端字段；如果没有这一行，后续 launcher 不知道该走 AppX 后端且不能误进 Popen。
    return plan  # 新增代码+WindowsLaunchResolver：返回 AppX 启动计划；如果没有这一行，调用方拿不到结果。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_appx_plan 到此结束；如果没有这个边界说明，用户不容易看出 AppX 计划范围。

def _phase124_shortcut_plan(candidate: dict[str, Any]) -> dict[str, Any]:  # 新增代码+WindowsLaunchResolver：函数段开始，生成开始菜单快捷方式计划；如果没有这段函数，Start Menu 候选会继续被当 exe 猜测。
    plan = _phase124_base_plan(candidate, True)  # 新增代码+WindowsLaunchResolver：先创建共享计划；如果没有这一行，shortcut 后端会缺少审计字段。
    shortcut_id = _phase124_basename(candidate.get("launch_id") or candidate.get("display_name"))  # 新增代码+WindowsLaunchResolver：读取脱敏快捷方式标识；如果没有这一行，后续无法定位开始菜单入口。
    plan.update({"launch_backend": "start_menu_shortcut", "launch_verb": "ShellExecuteShortcut", "command_shape": "shortcut_no_shell", "shortcut_id": shortcut_id, "phase110_backend_supported": False, "phase110_backend_support_reason": "phase110_popen_backend_does_not_launch_shortcuts_yet"})  # 新增代码+WindowsLaunchResolver：写入 shortcut 后端字段；如果没有这一行，后续 launcher 无法区分快捷方式和 exe。
    return plan  # 新增代码+WindowsLaunchResolver：返回快捷方式启动计划；如果没有这一行，调用方拿不到结果。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_shortcut_plan 到此结束；如果没有这个边界说明，用户不容易看出 shortcut 计划范围。

def resolve_windows_launch_plan(app_name: Any = "", candidates: list[dict[str, Any]] | None = None, candidate: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+WindowsLaunchResolver：函数段开始，公开入口，把应用身份解析成多后端启动计划；如果没有这段函数，主链路仍只能猜 exe。
    selected = dict(candidate or {}) if candidate is not None else _phase124_select_candidate(app_name, candidates)  # 新增代码+WindowsLaunchResolver：优先使用明确候选，否则从清单选择；如果没有这一行，resolver 无法同时支持测试注入和真实 discover。
    if not selected:  # 新增代码+WindowsLaunchResolver：检查是否没有候选；如果没有这一行，空目标可能继续生成启动计划。
        return _phase124_base_plan({}, False, "no_candidate")  # 新增代码+WindowsLaunchResolver：返回无候选拒绝；如果没有这一行，调用方不知道失败原因。
    if _phase124_contains_high_risk(app_name, selected.get("display_name"), selected.get("app_name"), selected.get("launch_id"), selected.get("executable")):  # 新增代码+WindowsLaunchResolver：检查用户输入和候选身份风险；如果没有这一行，高风险目标可能绕过旧安全门。
        return _phase124_base_plan(selected, False, "high_risk_target_refused")  # 新增代码+WindowsLaunchResolver：返回高风险拒绝；如果没有这一行，危险候选可能进入真实后端。
    launch_kind = _phase124_lower(selected.get("launch_kind") or "exe")  # 新增代码+WindowsLaunchResolver：读取启动类型；如果没有这一行，resolver 不知道该选择哪个后端。
    if launch_kind in {"exe", "start_process_exe"}:  # 新增代码+WindowsLaunchResolver：判断 Win32 exe 类型；如果没有这一行，普通应用无法走 argv 后端。
        return _phase124_exe_plan(selected)  # 新增代码+WindowsLaunchResolver：返回 exe 计划；如果没有这一行，普通应用会被误拒绝。
    if launch_kind in {"appx", "aumid"}:  # 新增代码+WindowsLaunchResolver：判断 AppX/AUMID 类型；如果没有这一行，商店应用会被误猜成 exe。
        return _phase124_appx_plan(selected)  # 新增代码+WindowsLaunchResolver：返回 AppX 计划；如果没有这一行，Calculator 等 UWP 应用无法保留 AUMID。
    if launch_kind == "shortcut":  # 新增代码+WindowsLaunchResolver：判断开始菜单快捷方式类型；如果没有这一行，快捷方式应用会被误当 exe。
        return _phase124_shortcut_plan(selected)  # 新增代码+WindowsLaunchResolver：返回 shortcut 计划；如果没有这一行，Start Menu 入口无法保留。
    if launch_kind == "uninstall_record":  # 新增代码+WindowsLaunchResolver：判断卸载注册表产品记录；如果没有这一行，设置页记录可能误导启动器。
        return _phase124_base_plan(selected, False, "not_launchable_inventory_record")  # 新增代码+WindowsLaunchResolver：拒绝不可启动记录；如果没有这一行，卸载记录可能进入真实 launcher。
    return _phase124_base_plan(selected, False, "unsupported_launch_kind")  # 新增代码+WindowsLaunchResolver：拒绝未知启动类型；如果没有这一行，未来未知类型会被含糊处理。
# 新增代码+WindowsLaunchResolver：函数段结束，resolve_windows_launch_plan 到此结束；如果没有这个边界说明，用户不容易看出公开解析入口范围。

__all__ = ["PHASE124_WINDOWS_LAUNCH_RESOLVER_MARKER", "PHASE124_WINDOWS_LAUNCH_RESOLVER_MODEL", "PHASE124_WINDOWS_LAUNCH_RESOLVER_OK_TOKEN", "resolve_windows_launch_plan"]  # 新增代码+WindowsLaunchResolver：限定公开 API；如果没有这一行，通配导入会暴露内部 helper。
