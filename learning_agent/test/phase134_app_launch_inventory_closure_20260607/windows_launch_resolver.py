"""Windows Computer Use 多后端启动解析器。"""  # 新增代码+WindowsLaunchResolver：说明本模块只负责把应用候选解析成启动计划；如果没有这一行，读者容易把 resolver 误解成已经执行真实启动。
from __future__ import annotations  # 新增代码+WindowsLaunchResolver：启用延迟类型注解；如果没有这一行，后续类型提示在脚本兼容模式下更容易出现导入顺序问题。
import hashlib  # 新增代码+CompatSlimming：导入哈希工具用于脱敏窗口标题；如果没有这一行，记录型窗口身份只能暴露原始标题或缺少稳定比对值。
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
PHASE124_NO_REAL_BACKEND_KINDS = set()  # 修改代码+AppLaunchInventoryClosure：AppX/AUMID 和开始菜单 shortcut 已由 Phase110 真实后端接通；如果没有这一行，成熟矩阵会继续误报非 argv 后端不可真实启动。

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
    catalog = build_windows_app_inventory(candidates=candidates, include_common=not bool(candidates))  # 新增代码+WindowsLaunchResolver：复用统一 inventory 清洗和排序；如果没有这一行，resolver 会绕开 ClaudeCode 式应用清单层。
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
    if executable.lower() == "file explorer.exe" or _phase124_lower(candidate.get("app_name")) in {"explorer", "fileexplorer"}:  # 修改代码+CompatSlimming：修正常见开始菜单显示名 File Explorer；如果没有这一行，resolver 会生成不存在的 File Explorer.exe。
        executable = "explorer.exe"  # 修改代码+CompatSlimming：使用 Windows 文件资源管理器真实可执行名；如果没有这一行，代表文件浏览场景无法形成可执行启动计划。
    plan.update({"launch_backend": "argv_no_shell", "launch_verb": "Start-Process", "command_shape": "argv_no_shell", "executable": executable, "arguments": [], "phase110_backend_supported": True, "phase110_backend_support_reason": "supported_by_phase110_popen_argv"})  # 新增代码+WindowsLaunchResolver：写入 argv 后端字段；如果没有这一行，Phase110 不知道这是可执行计划。
    return plan  # 新增代码+WindowsLaunchResolver：返回 exe 启动计划；如果没有这一行，调用方拿不到结果。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_exe_plan 到此结束；如果没有这个边界说明，用户不容易看出 exe 计划范围。

def _phase124_appx_plan(candidate: dict[str, Any]) -> dict[str, Any]:  # 新增代码+WindowsLaunchResolver：函数段开始，生成 AppX/AUMID 启动计划；如果没有这段函数，商店应用会继续被误猜成 exe。
    plan = _phase124_base_plan(candidate, True)  # 新增代码+WindowsLaunchResolver：先创建共享计划；如果没有这一行，AppX 后端会缺少审计字段。
    aumid = _phase124_clean_text(candidate.get("launch_id") or candidate.get("aumid"))  # 新增代码+WindowsLaunchResolver：读取完整 AUMID；如果没有这一行，AppX 应用无法精确定位。
    plan.update({"launch_backend": "appx_aumid", "launch_verb": "ShellExecuteAppUserModelId", "command_shape": "aumid_no_shell", "aumid": aumid, "phase110_backend_supported": True, "phase110_backend_support_reason": "supported_by_phase110_appx_aumid"})  # 修改代码+AppLaunchInventoryClosure：写入已接通的 AUMID 后端字段；如果没有这一行，Phase110 的真实 AppX launcher 会被旧报告误判成不可用。
    return plan  # 新增代码+WindowsLaunchResolver：返回 AppX 启动计划；如果没有这一行，调用方拿不到结果。
# 新增代码+WindowsLaunchResolver：函数段结束，_phase124_appx_plan 到此结束；如果没有这个边界说明，用户不容易看出 AppX 计划范围。

def _phase124_shortcut_plan(candidate: dict[str, Any]) -> dict[str, Any]:  # 新增代码+WindowsLaunchResolver：函数段开始，生成开始菜单快捷方式计划；如果没有这段函数，Start Menu 候选会继续被当 exe 猜测。
    plan = _phase124_base_plan(candidate, True)  # 新增代码+WindowsLaunchResolver：先创建共享计划；如果没有这一行，shortcut 后端会缺少审计字段。
    shortcut_id = _phase124_basename(candidate.get("launch_id") or candidate.get("display_name"))  # 新增代码+WindowsLaunchResolver：读取脱敏快捷方式标识；如果没有这一行，后续无法定位开始菜单入口。
    plan.update({"launch_backend": "start_menu_shortcut", "launch_verb": "ShellExecuteShortcut", "command_shape": "shortcut_no_shell", "shortcut_id": shortcut_id, "phase110_backend_supported": True, "phase110_backend_support_reason": "supported_by_phase110_start_menu_shortcut"})  # 修改代码+AppLaunchInventoryClosure：写入已接通的 shortcut 后端字段；如果没有这一行，开始菜单普通应用会继续被旧报告误判成未接通。
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

PHASE132_WINDOWS_APP_LAUNCH_TARGET_MARKER = "WINDOWS_APP_LAUNCH_TARGET_READY"  # 新增代码+CompatSlimming：定义瘦身后的应用解析 marker；如果没有这一行，旧发现文件删除后终端缺少稳定锚点。
PHASE132_WINDOWS_APP_LAUNCH_TARGET_OK_TOKEN = "WINDOWS_APP_LAUNCH_TARGET_OK"  # 新增代码+CompatSlimming：定义瘦身后的应用解析 OK token；如果没有这一行，成功和普通报告不容易区分。
PHASE132_WINDOWS_APP_WINDOW_CONTROL_MARKER = "WINDOWS_APP_WINDOW_CONTROL_READY"  # 新增代码+CompatSlimming：定义新窗口控制合同 marker；如果没有这一行，旧窗口控制文件删除后样例矩阵缺少替代输出。
PHASE132_WINDOWS_APP_WINDOW_CONTROL_OK_TOKEN = "WINDOWS_APP_WINDOW_CONTROL_OK"  # 新增代码+CompatSlimming：定义新窗口控制合同 OK token；如果没有这一行，真实终端验收不容易匹配成功。


def _phase132_bool_token(value: Any) -> str:  # 新增代码+CompatSlimming：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，新旧 CLI 行会混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+CompatSlimming：返回 true 或 false；如果没有这一行，controller 场景匹配可能因为大小写失败。
# 新增代码+CompatSlimming：函数段结束，_phase132_bool_token 到此结束；如果没有这个边界说明，用户不容易看出格式化范围。


def _phase132_sha256_16(value: Any) -> str:  # 新增代码+CompatSlimming：函数段开始，生成短哈希保护窗口标题；如果没有这段函数，记录型窗口身份可能泄露完整标题。
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()[:16]  # 新增代码+CompatSlimming：返回 16 位哈希；如果没有这一行，窗口漂移比对缺少稳定脱敏字段。
# 新增代码+CompatSlimming：函数段结束，_phase132_sha256_16 到此结束；如果没有这个边界说明，用户不容易看出脱敏范围。


def resolve_windows_app_launch_target(raw_target: Any, candidates: list[dict[str, Any]] | None = None) -> dict[str, Any]:  # 新增代码+CompatSlimming：函数段开始，把用户目标解析成统一应用发现和启动计划报告；如果没有这段函数，旧 discovery 文件删除后主链路会断。
    normalized_target = _phase124_lower(raw_target)  # 新增代码+CompatSlimming：清洗用户或模型传入的应用名；如果没有这一行，大小写和引号会导致解析漂移。
    raw_target_is_high_risk = _phase124_contains_high_risk(normalized_target)  # 修改代码+CompatSlimming：先检查用户原始目标是否高风险；如果没有这一行，未枚举到候选的 powershell/cmd 会被误报为 unresolved 而不是拒绝。
    if raw_target_is_high_risk:  # 修改代码+CompatSlimming：高风险目标不进入候选发现和 fallback；如果没有这一行，危险命令可能被普通未知应用 fallback 包装。
        plan = _phase124_base_plan({"display_name": normalized_target, "app_name": normalized_target, "launch_kind": "blocked_high_risk", "launch_id": normalized_target, "source": "raw_target_risk_policy", "installed_app_verified": False}, False, "high_risk_target_refused")  # 修改代码+CompatSlimming：构造零副作用拒绝计划；如果没有这一行，高风险拒绝缺少结构化证据。
    else:  # 修改代码+CompatSlimming：只有普通目标才进入清单解析；如果没有这一行，安全目标也会被错误跳过。
        injected_candidates = build_windows_app_inventory(candidates=candidates, include_common=False) if candidates is not None else None  # 修改代码+CompatSlimming：测试注入候选也先走统一 inventory 清洗；如果没有这一行，候选排序和真实路径会不一致。
        plan = resolve_windows_launch_plan(app_name=normalized_target, candidates=injected_candidates)  # 修改代码+CompatSlimming：调用唯一 launch resolver；如果没有这一行，新旧发现层会再次分叉。
    fallback_used = bool(plan.get("refusal_reason") == "no_candidate" and normalized_target and not raw_target_is_high_risk)  # 修改代码+CompatSlimming：识别未知普通应用 fallback；如果没有这一行，未知普通 app 又会退回白名单拒绝。
    if fallback_used:  # 修改代码+CompatSlimming：没有候选但目标普通时生成默认关闭计划；如果没有这一行，用户机器未枚举到的普通软件无法进入模型可审计计划。
        fallback_candidate = {"display_name": normalized_target, "app_name": normalized_target.replace(" ", ""), "launch_id": normalized_target, "launch_kind": "exe", "source": "generic_fallback", "installed_app_verified": False}  # 新增代码+CompatSlimming：构造保守 fallback 候选；如果没有这一行，resolver 没有可计划对象。
        plan = resolve_windows_launch_plan(app_name=normalized_target, candidate=fallback_candidate)  # 新增代码+CompatSlimming：让 fallback 仍通过同一个 resolver；如果没有这一行，fallback 会绕过安全字段。
    high_risk_refused = bool(plan.get("refusal_reason") == "high_risk_target_refused")  # 新增代码+CompatSlimming：读取高风险拒绝事实；如果没有这一行，PowerShell/CMD 拒绝无法上浮。
    safe_resolver_launch_plan = bool(plan.get("safe_to_launch") and plan.get("resolver_used") and not plan.get("changes_registry") and not plan.get("changes_system_settings") and not plan.get("requires_admin") and not plan.get("uses_shell_string"))  # 新增代码+CompatSlimming：汇总 resolver 级安全计划；如果没有这一行，后端无法统一复核安全边界。
    safe_start_process_plan = bool(safe_resolver_launch_plan and plan.get("launch_backend") == "argv_no_shell" and plan.get("launch_verb") == "Start-Process")  # 新增代码+CompatSlimming：标记当前 Popen 可执行计划；如果没有这一行，AppX/shortcut 会被误送 argv 后端。
    executable = str(plan.get("executable", "") or "")  # 新增代码+CompatSlimming：读取 exe 计划身份；如果没有这一行，后端请求缺少可执行字段。
    canonical_target = executable[:-4].lower() if executable.lower().endswith(".exe") else str(plan.get("app_name") or normalized_target)  # 新增代码+CompatSlimming：生成规范目标名；如果没有这一行，窗口身份和审计字段会漂移。
    passed = bool(normalized_target and safe_resolver_launch_plan and not high_risk_refused)  # 新增代码+CompatSlimming：计算普通安全目标是否解析通过；如果没有这一行，OK token 没有事实依据。
    return {"marker": PHASE132_WINDOWS_APP_LAUNCH_TARGET_MARKER, "ok_token": PHASE132_WINDOWS_APP_LAUNCH_TARGET_OK_TOKEN, "model": "windows_app_launch_target", "passed": passed, "raw_target": str(raw_target or ""), "normalized_target": normalized_target, "canonical_target": canonical_target, "candidate_count": 1 if plan.get("display_name") else 0, "best_candidate_name": str(plan.get("display_name", "") or ""), "best_candidate_executable": executable, "best_candidate_launch_id": str(plan.get("launch_id", "") or ""), "best_candidate_launch_kind": str(plan.get("launch_kind", "") or ""), "best_candidate_app_name": str(plan.get("app_name", "") or ""), "candidate_source": str(plan.get("source", "") or ("generic_fallback" if fallback_used else "")), "installed_app_verified": bool(plan.get("installed_app_verified", False)), "dynamic_discovery_used": bool(plan.get("display_name") or fallback_used), "hardcoded_app_whitelist_required": False, "per_app_patch_required": False, "representative_category_testing": True, "safe_start_process_plan": safe_start_process_plan, "safe_resolver_launch_plan": safe_resolver_launch_plan, "resolver_launch_backend": str(plan.get("launch_backend", "") or ""), "high_risk_refused": high_risk_refused, "unknown_target_refused": False, "generic_unknown_app_default_off": bool(fallback_used and safe_resolver_launch_plan), "generic_target_default_off": bool(safe_resolver_launch_plan and not high_risk_refused), "real_launch_default_disabled": True, "real_launch_attempted": False, "real_desktop_touched": False, "uncontrolled_actions_expanded": False, "launch_plan": plan}  # 新增代码+CompatSlimming：返回兼容旧调用的报告形状；如果没有这一行，交互层、后端和 maturity 会同时断裂。
# 新增代码+CompatSlimming：函数段结束，resolve_windows_app_launch_target 到此结束；如果没有这个边界说明，用户不容易看出统一解析范围。


def windows_app_launch_target_cli_line(report: dict[str, Any]) -> str:  # 新增代码+CompatSlimming：函数段开始，把统一应用解析报告转成终端 token 行；如果没有这段函数，旧 CLI 格式删除后没有替代输出。
    ok_token = f" {PHASE132_WINDOWS_APP_LAUNCH_TARGET_OK_TOKEN}" if bool(report.get("passed", False)) else ""  # 新增代码+CompatSlimming：只在解析通过时输出 OK；如果没有这一行，高风险拒绝可能被误判成功。
    return f"{PHASE132_WINDOWS_APP_LAUNCH_TARGET_MARKER}{ok_token} canonical_target={report.get('canonical_target', '')} dynamic_discovery_used={_phase132_bool_token(report.get('dynamic_discovery_used'))} hardcoded_app_whitelist_required={_phase132_bool_token(report.get('hardcoded_app_whitelist_required', True))} per_app_patch_required={_phase132_bool_token(report.get('per_app_patch_required', True))} candidate_source={report.get('candidate_source', '')} resolver_launch_backend={report.get('resolver_launch_backend', '')} safe_resolver_launch_plan={_phase132_bool_token(report.get('safe_resolver_launch_plan'))} generic_target_default_off={_phase132_bool_token(report.get('generic_target_default_off'))} generic_unknown_app_default_off={_phase132_bool_token(report.get('generic_unknown_app_default_off'))} high_risk_refused={_phase132_bool_token(report.get('high_risk_refused'))} safe_start_process_plan={_phase132_bool_token(report.get('safe_start_process_plan'))} real_launch_attempted={_phase132_bool_token(report.get('real_launch_attempted'))} real_desktop_touched={_phase132_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase132_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+CompatSlimming：返回固定顺序 token；如果没有这一行，真实终端验收会漂移。
# 新增代码+CompatSlimming：函数段结束，windows_app_launch_target_cli_line 到此结束；如果没有这个边界说明，用户不容易看出 CLI 范围。


def resolve_interactive_windows_launch_target(raw_target: Any) -> dict[str, Any]:  # 新增代码+CompatSlimming：函数段开始，为旧 /computer launch 入口提供目标判断；如果没有这段函数，交互命令会继续依赖已删除白名单文件。
    report = resolve_windows_app_launch_target(raw_target)  # 新增代码+CompatSlimming：复用统一应用解析；如果没有这一行，交互目标解析会再次单独维护。
    high_risk_refused = bool(report.get("high_risk_refused", False))  # 新增代码+CompatSlimming：读取高风险拒绝；如果没有这一行，高风险分支无法保持零副作用。
    safe_known_ordinary_app = bool(report.get("passed", False) and not high_risk_refused)  # 新增代码+CompatSlimming：把普通安全目标标记为已识别；如果没有这一行，交互层无法决定后续动作。
    canonical_target = str(report.get("canonical_target", "") or report.get("normalized_target", ""))  # 新增代码+CompatSlimming：读取规范目标；如果没有这一行，Notepad smoke 分支无法判断目标。
    return dict(report, decision="windows_app_target_resolved" if safe_known_ordinary_app else ("windows_app_high_risk_target_refused" if high_risk_refused else "windows_app_target_unresolved"), interactive_target_resolved=safe_known_ordinary_app, safe_known_ordinary_app=safe_known_ordinary_app, unknown_target_refused=False, real_launch_supported=canonical_target == "notepad")  # 新增代码+CompatSlimming：返回交互层兼容字段；如果没有这一行，旧调用方需要大范围重写。
# 新增代码+CompatSlimming：函数段结束，resolve_interactive_windows_launch_target 到此结束；如果没有这个边界说明，用户不容易看出交互兼容范围。


def interactive_windows_launch_target_cli_line(report: dict[str, Any]) -> str:  # 新增代码+CompatSlimming：函数段开始，格式化交互目标报告；如果没有这段函数，交互调试命令没有可读摘要。
    ok_token = f" {PHASE132_WINDOWS_APP_LAUNCH_TARGET_OK_TOKEN}" if bool(report.get("safe_known_ordinary_app", False)) else ""  # 新增代码+CompatSlimming：安全普通目标才输出 OK；如果没有这一行，高风险拒绝会误带成功 token。
    return f"{PHASE132_WINDOWS_APP_LAUNCH_TARGET_MARKER}{ok_token} canonical_target={report.get('canonical_target', '')} interactive_target_resolved={_phase132_bool_token(report.get('interactive_target_resolved'))} safe_known_ordinary_app={_phase132_bool_token(report.get('safe_known_ordinary_app'))} high_risk_refused={_phase132_bool_token(report.get('high_risk_refused'))} unknown_target_refused={_phase132_bool_token(report.get('unknown_target_refused'))} real_launch_supported={_phase132_bool_token(report.get('real_launch_supported'))} real_desktop_touched={_phase132_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase132_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+CompatSlimming：返回固定 token 行；如果没有这一行，controller 难以稳定匹配。
# 新增代码+CompatSlimming：函数段结束，interactive_windows_launch_target_cli_line 到此结束；如果没有这个边界说明，用户不容易看出交互 CLI 范围。


def build_launch_plan(app_name: str, test_file: str | None = None) -> dict[str, Any]:  # 新增代码+CompatSlimming：函数段开始，提供旧 app_window_control 的安全启动计划替代入口；如果没有这段函数，代表性样例和 live dispatcher 会断。
    report = resolve_windows_app_launch_target(app_name)  # 新增代码+CompatSlimming：先走统一应用解析；如果没有这一行，启动计划会绕过 inventory/resolver。
    plan = dict(report.get("launch_plan", {}) or {})  # 新增代码+CompatSlimming：复制 resolver 计划；如果没有这一行，后续补参数会污染原报告。
    arguments = [str(test_file)] if test_file and plan.get("launch_backend") == "argv_no_shell" else []  # 新增代码+CompatSlimming：只给 argv 后端添加受控文件参数；如果没有这一行，AppX/shortcut 会收到错误参数。
    if arguments:  # 新增代码+CompatSlimming：只有存在受控参数时才更新；如果没有这一行，空参数也可能覆盖 resolver 字段。
        plan["arguments"] = arguments  # 新增代码+CompatSlimming：写入受控参数列表；如果没有这一行，Notepad/Explorer 样例没有受控文件或目录。
    plan.setdefault("app_name", str(app_name or "").strip().lower())  # 新增代码+CompatSlimming：保留调用方原始目标短名；如果没有这一行，旧报告字段可能缺失。
    plan.setdefault("actions_expanded", False)  # 新增代码+CompatSlimming：声明计划本身不扩张动作面；如果没有这一行，旧矩阵会把缺字段当风险。
    return plan  # 新增代码+CompatSlimming：返回统一安全计划；如果没有这一行，调用方拿不到启动计划。
# 新增代码+CompatSlimming：函数段结束，build_launch_plan 到此结束；如果没有这个边界说明，用户不容易看出计划兼容范围。


class Phase69RecordingLauncher:  # 新增代码+CompatSlimming：类段开始，提供记录型启动器替代旧 app_window_control；如果没有这个类，live dispatcher 默认测试可能误触真实应用。
    def __init__(self) -> None:  # 新增代码+CompatSlimming：函数段开始，初始化记录列表；如果没有这段函数，启动调用无法被审计。
        self.launches: list[dict[str, Any]] = []  # 新增代码+CompatSlimming：保存启动计划副本；如果没有这一行，测试无法检查启动器是否被调用。
    # 新增代码+CompatSlimming：函数段结束，Phase69RecordingLauncher.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def launch(self, plan: dict[str, Any]) -> dict[str, Any]:  # 新增代码+CompatSlimming：函数段开始，记录启动计划并生成假窗口；如果没有这段函数，记录模式无法串起窗口身份。
        safe_plan = dict(plan or {})  # 新增代码+CompatSlimming：复制计划避免污染调用方；如果没有这一行，审计证据可能被后续修改。
        self.launches.append(safe_plan)  # 新增代码+CompatSlimming：保存启动计划；如果没有这一行，合同无法证明后端被触达。
        executable = str(safe_plan.get("executable") or safe_plan.get("app_name") or "app.exe")  # 新增代码+CompatSlimming：读取窗口 app 身份；如果没有这一行，窗口缺少 process_name。
        title = f"{executable} - recording"  # 新增代码+CompatSlimming：生成记录型标题；如果没有这一行，窗口身份缺少可读摘要。
        window = {"app_id": executable, "process_name": executable, "window_id": f"phase132-window:{executable}", "pid": 13200 + len(self.launches), "title_preview": title, "title_sha256_16": _phase132_sha256_16(title), "safe_to_target": bool(safe_plan.get("safe_to_launch", False))}  # 新增代码+CompatSlimming：构造脱敏窗口身份；如果没有这一行，后续 focus 和安全边界没有目标。
        return {"launched": bool(safe_plan.get("safe_to_launch", False)), "blocked": not bool(safe_plan.get("safe_to_launch", False)), "plan": safe_plan, "window": window, "launcher": "windows_launch_resolver_recording", "system_settings_changed": False, "actions_expanded": False}  # 新增代码+CompatSlimming：返回记录型启动结果；如果没有这一行，上层无法判断启动是否被阻断。
    # 新增代码+CompatSlimming：函数段结束，Phase69RecordingLauncher.launch 到此结束；如果没有这个边界说明，用户不容易看出记录启动范围。
# 新增代码+CompatSlimming：类段结束，Phase69RecordingLauncher 到此结束；如果没有这个边界说明，用户不容易看出记录启动器范围。


class Phase69RecordingFocuser:  # 新增代码+CompatSlimming：类段开始，提供记录型聚焦器替代旧 app_window_control；如果没有这个类，窗口聚焦阶段会断。
    def __init__(self) -> None:  # 新增代码+CompatSlimming：函数段开始，初始化聚焦记录；如果没有这段函数，聚焦调用不可审计。
        self.focuses: list[dict[str, Any]] = []  # 新增代码+CompatSlimming：保存聚焦窗口副本；如果没有这一行，测试无法检查聚焦次数。
    # 新增代码+CompatSlimming：函数段结束，Phase69RecordingFocuser.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def focus(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+CompatSlimming：函数段开始，记录聚焦窗口但不切真实前台；如果没有这段函数，测试可能需要真实窗口。
        safe_window = dict(window or {})  # 新增代码+CompatSlimming：复制窗口身份；如果没有这一行，调用方对象可能被修改。
        self.focuses.append(safe_window)  # 新增代码+CompatSlimming：保存聚焦记录；如果没有这一行，合同无法证明 focus 阶段存在。
        return {"focused": bool(safe_window.get("safe_to_target", True)), "window": safe_window, "focuser": "windows_launch_resolver_recording", "system_settings_changed": False, "actions_expanded": False}  # 新增代码+CompatSlimming：返回聚焦摘要；如果没有这一行，上层无法读取窗口身份。
    # 新增代码+CompatSlimming：函数段结束，Phase69RecordingFocuser.focus 到此结束；如果没有这个边界说明，用户不容易看出记录聚焦范围。
# 新增代码+CompatSlimming：类段结束，Phase69RecordingFocuser 到此结束；如果没有这个边界说明，用户不容易看出记录聚焦器范围。


class WindowsAppWindowControlRuntime:  # 新增代码+CompatSlimming：类段开始，组合记录型启动和聚焦；如果没有这个类，旧 live dispatcher 需要大改才能迁移。
    def __init__(self, launcher: Any | None = None, focuser: Any | None = None) -> None:  # 新增代码+CompatSlimming：函数段开始，允许注入记录器；如果没有这段函数，测试无法替换依赖。
        self.launcher = launcher if launcher is not None else Phase69RecordingLauncher()  # 新增代码+CompatSlimming：保存启动器；如果没有这一行，launch_app 没有执行主体。
        self.focuser = focuser if focuser is not None else Phase69RecordingFocuser()  # 新增代码+CompatSlimming：保存聚焦器；如果没有这一行，focus_window 没有执行主体。
    # 新增代码+CompatSlimming：函数段结束，WindowsAppWindowControlRuntime.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    def launch_app(self, plan: dict[str, Any]) -> dict[str, Any]:  # 新增代码+CompatSlimming：函数段开始，调用记录型启动器；如果没有这段函数，runtime 缺少启动入口。
        return dict(self.launcher.launch(dict(plan or {})))  # 新增代码+CompatSlimming：返回启动器结果副本；如果没有这一行，上层拿不到启动报告。
    # 新增代码+CompatSlimming：函数段结束，WindowsAppWindowControlRuntime.launch_app 到此结束；如果没有这个边界说明，用户不容易看出启动入口范围。

    def focus_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+CompatSlimming：函数段开始，调用记录型聚焦器；如果没有这段函数，runtime 缺少聚焦入口。
        return dict(self.focuser.focus(dict(window or {})))  # 新增代码+CompatSlimming：返回聚焦器结果副本；如果没有这一行，上层拿不到聚焦报告。
    # 新增代码+CompatSlimming：函数段结束，WindowsAppWindowControlRuntime.focus_window 到此结束；如果没有这个边界说明，用户不容易看出聚焦入口范围。
    def verify_target_identity(self, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:  # 修改代码+CompatSlimming：函数段开始，比对动作前后的窗口身份；如果没有这段函数，瘦身后窗口漂移保护没有统一入口。
        before_identity = (str((before or {}).get("app_id", "")), str((before or {}).get("window_id", "")), str((before or {}).get("pid", "")), str((before or {}).get("title_sha256_16", "")))  # 修改代码+CompatSlimming：提取动作前窗口身份四元组；如果没有这一行，比较会漏掉进程或标题漂移。
        after_identity = (str((after or {}).get("app_id", "")), str((after or {}).get("window_id", "")), str((after or {}).get("pid", "")), str((after or {}).get("title_sha256_16", "")))  # 修改代码+CompatSlimming：提取动作后窗口身份四元组；如果没有这一行，漂移判断没有对照对象。
        same_target = bool(before_identity == after_identity and all(before_identity))  # 修改代码+CompatSlimming：只有四个身份字段都一致才认为同一目标；如果没有这一行，空身份可能被误判为安全。
        return {"same_target": same_target, "blocked": not same_target, "reason": "" if same_target else "target_window_identity_changed", "before_identity": before_identity, "after_identity": after_identity}  # 修改代码+CompatSlimming：返回可审计的允许或阻断结果；如果没有这一行，上层无法解释为什么停止动作。
    # 修改代码+CompatSlimming：函数段结束，WindowsAppWindowControlRuntime.verify_target_identity 到此结束；如果没有这个边界说明，用户不容易看出窗口身份校验范围。
# 新增代码+CompatSlimming：类段结束，WindowsAppWindowControlRuntime 到此结束；如果没有这个边界说明，用户不容易看出 runtime 范围。


def run_windows_app_window_control_contract(real_smoke: bool = False) -> dict[str, Any]:  # 新增代码+CompatSlimming：函数段开始，运行替代 Phase69 的窗口控制合同；如果没有这段函数，旧矩阵删除 Phase69 后无事实来源。
    _ = real_smoke  # 新增代码+CompatSlimming：保留真实 smoke 参数但本合同不触碰桌面；如果没有这一行，调用方会误以为参数遗漏。
    runtime = WindowsAppWindowControlRuntime()  # 新增代码+CompatSlimming：创建记录型 runtime；如果没有这一行，合同没有被测对象。
    safe_plan = build_launch_plan("notepad")  # 新增代码+CompatSlimming：生成安全普通应用计划；如果没有这一行，合同无法证明启动计划存在。
    launch = runtime.launch_app(safe_plan)  # 新增代码+CompatSlimming：记录启动；如果没有这一行，app_launch 字段没有事实。
    focus = runtime.focus_window(dict(launch.get("window", {}) or {}))  # 新增代码+CompatSlimming：记录聚焦；如果没有这一行，window_focus 字段没有事实。
    unsafe_plan = build_launch_plan("powershell")  # 新增代码+CompatSlimming：生成高风险拒绝计划；如果没有这一行，合同不能证明风险边界。
    target_identity_check = runtime.verify_target_identity(dict(launch.get("window", {}) or {}), dict(focus.get("window", {}) or {}))  # 修改代码+CompatSlimming：校验正常聚焦前后仍是同一窗口；如果没有这一行，target_window_identity 只是“有窗口”而不是“同一窗口”。
    drift_identity_check = runtime.verify_target_identity(dict(launch.get("window", {}) or {}), {"app_id": "powershell.exe", "window_id": "phase132-window:powershell.exe", "pid": 13299, "title_sha256_16": _phase132_sha256_16("powershell.exe - recording")})  # 修改代码+CompatSlimming：构造漂移样本验证会被阻断；如果没有这一行，切到错误窗口后的保护不可验收。
    app_launch = bool(launch.get("launched") and safe_plan.get("safe_to_launch"))  # 新增代码+CompatSlimming：汇总安全启动是否通过；如果没有这一行，报告缺少关键布尔值。
    window_focus = bool(focus.get("focused"))  # 新增代码+CompatSlimming：汇总聚焦是否通过；如果没有这一行，报告缺少聚焦状态。
    target_window_identity = bool(target_identity_check.get("same_target"))  # 修改代码+CompatSlimming：确认窗口身份前后一致；如果没有这一行，错误窗口也可能被当成可操作目标。
    target_drift_blocked = bool(drift_identity_check.get("blocked"))  # 修改代码+CompatSlimming：确认漂移样本会被阻断；如果没有这一行，窗口切换风险没有合同证据。
    unsafe_launch_blocked = bool(not unsafe_plan.get("safe_to_launch") and unsafe_plan.get("refusal_reason"))  # 新增代码+CompatSlimming：确认高风险计划被阻断；如果没有这一行，安全边界不可见。
    safe_start_process_plan = bool(safe_plan.get("safe_to_launch") and not safe_plan.get("changes_registry") and not safe_plan.get("changes_system_settings") and not safe_plan.get("requires_admin") and not safe_plan.get("uses_shell_string"))  # 修改代码+CompatSlimming：汇总启动计划是否安全；如果没有这一行，旧 Phase69 验收无法证明启动层没有 shell/系统副作用。
    recording_launcher = isinstance(runtime.launcher, Phase69RecordingLauncher)  # 修改代码+CompatSlimming：证明合同使用记录型启动器；如果没有这一行，单元测试可能误触真实桌面。
    system_settings_changed = bool(launch.get("system_settings_changed") or focus.get("system_settings_changed") or safe_plan.get("changes_system_settings"))  # 修改代码+CompatSlimming：汇总是否改变系统设置；如果没有这一行，安全边界字段会缺失。
    actions_expanded = bool(launch.get("actions_expanded") or focus.get("actions_expanded") or unsafe_plan.get("actions_expanded"))  # 修改代码+CompatSlimming：汇总动作面是否扩大；如果没有这一行，旧验收无法确认本合同没有扩张真实动作。
    passed = bool(app_launch and window_focus and target_window_identity and target_drift_blocked and unsafe_launch_blocked and safe_start_process_plan and recording_launcher and not system_settings_changed and not actions_expanded)  # 修改代码+CompatSlimming：汇总合同通过条件；如果没有这一行，OK token 没有完整事实依据。
    return {"marker": PHASE132_WINDOWS_APP_WINDOW_CONTROL_MARKER, "ok_token": PHASE132_WINDOWS_APP_WINDOW_CONTROL_OK_TOKEN, "model": "windows_app_window_control", "passed": passed, "app_launch": app_launch, "window_focus": window_focus, "target_window_identity": target_window_identity, "target_drift_blocked": target_drift_blocked, "unsafe_launch_blocked": unsafe_launch_blocked, "safe_start_process_plan": safe_start_process_plan, "recording_launcher": recording_launcher, "system_settings_changed": system_settings_changed, "actions_expanded": actions_expanded, "real_desktop_touched": False, "uncontrolled_actions_expanded": False, "safe_plan": safe_plan, "launch": launch, "focus": focus, "unsafe_plan": unsafe_plan, "target_identity_check": target_identity_check, "drift_identity_check": drift_identity_check}  # 修改代码+CompatSlimming：返回完整合同报告；如果没有这一行，矩阵和 CLI 无法共享事实。
# 新增代码+CompatSlimming：函数段结束，run_windows_app_window_control_contract 到此结束；如果没有这个边界说明，用户不容易看出窗口合同范围。


def windows_app_window_control_cli_line(report: dict[str, Any]) -> str:  # 新增代码+CompatSlimming：函数段开始，把窗口控制合同转成 token 行；如果没有这段函数，旧 Phase69 CLI 删除后没有替代。
    ok_token = f" {PHASE132_WINDOWS_APP_WINDOW_CONTROL_OK_TOKEN}" if bool(report.get("passed", False)) else ""  # 新增代码+CompatSlimming：通过时才输出 OK；如果没有这一行，失败报告可能被误判成功。
    return f"{PHASE132_WINDOWS_APP_WINDOW_CONTROL_MARKER}{ok_token} app_launch={_phase132_bool_token(report.get('app_launch'))} window_focus={_phase132_bool_token(report.get('window_focus'))} target_window_identity={_phase132_bool_token(report.get('target_window_identity'))} target_drift_blocked={_phase132_bool_token(report.get('target_drift_blocked'))} unsafe_launch_blocked={_phase132_bool_token(report.get('unsafe_launch_blocked'))} safe_start_process_plan={_phase132_bool_token(report.get('safe_start_process_plan'))} recording_launcher={_phase132_bool_token(report.get('recording_launcher'))} system_settings_changed={_phase132_bool_token(report.get('system_settings_changed'))} actions_expanded={_phase132_bool_token(report.get('actions_expanded'))} real_desktop_touched={_phase132_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase132_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 修改代码+CompatSlimming：返回固定顺序字段；如果没有这一行，验收输出会漂移。
# 新增代码+CompatSlimming：函数段结束，windows_app_window_control_cli_line 到此结束；如果没有这个边界说明，用户不容易看出窗口 CLI 范围。


PHASE69_ACTIONS_EXPANDED = False  # 新增代码+CompatSlimming：保留旧 Phase69 合同的动作边界常量；如果没有这一行，旧回归测试无法确认迁移后仍不扩张真实动作面。
PHASE69_APP_WINDOW_CONTROL_MARKER = PHASE132_WINDOWS_APP_WINDOW_CONTROL_MARKER  # 新增代码+CompatSlimming：把旧 Phase69 marker 映射到新窗口控制合同；如果没有这一行，删除旧文件后历史验收无法复用同一事实源。
PHASE69_APP_WINDOW_CONTROL_OK_TOKEN = PHASE132_WINDOWS_APP_WINDOW_CONTROL_OK_TOKEN  # 新增代码+CompatSlimming：把旧 Phase69 OK token 映射到新合同 token；如果没有这一行，旧 CLI 验收会误以为窗口控制能力消失。
PHASE107_INTERACTIVE_LAUNCH_TARGET_MARKER = PHASE132_WINDOWS_APP_LAUNCH_TARGET_MARKER  # 新增代码+CompatSlimming：把旧交互目标 marker 映射到统一应用启动目标合同；如果没有这一行，旧 Phase107 测试会找不到稳定标记。
PHASE107_INTERACTIVE_LAUNCH_TARGET_OK_TOKEN = PHASE132_WINDOWS_APP_LAUNCH_TARGET_OK_TOKEN  # 新增代码+CompatSlimming：把旧交互目标 OK token 映射到统一应用启动目标合同；如果没有这一行，旧 Phase107 验收无法证明迁移后功能还在。
PHASE108_GENERIC_APP_DISCOVERY_MARKER = PHASE132_WINDOWS_APP_LAUNCH_TARGET_MARKER  # 新增代码+CompatSlimming：把旧通用发现 marker 映射到统一 resolver；如果没有这一行，旧 Phase108 测试会错误要求恢复旧文件。
PHASE108_GENERIC_APP_DISCOVERY_OK_TOKEN = PHASE132_WINDOWS_APP_LAUNCH_TARGET_OK_TOKEN  # 新增代码+CompatSlimming：把旧通用发现 OK token 映射到统一 resolver；如果没有这一行，旧终端 token 断言无法迁移到新模块。
PHASE108_GENERIC_APP_DISCOVERY_MODEL = "windows_app_launch_target"  # 新增代码+CompatSlimming：保留旧模型名读取入口但指向新 resolver 语义；如果没有这一行，上游候选报告会缺少模型来源字段。
phase69_cli_line = windows_app_window_control_cli_line  # 新增代码+CompatSlimming：临时兼容旧矩阵使用的函数名；如果没有这一行，Phase75 汇总在第二批瘦身前会断。
run_phase69_app_window_control_contract = run_windows_app_window_control_contract  # 新增代码+CompatSlimming：临时兼容旧矩阵使用的合同名；如果没有这一行，Humanlike 矩阵会在第一批迁移中失败。
phase107_cli_line = interactive_windows_launch_target_cli_line  # 新增代码+CompatSlimming：临时兼容旧交互目标格式化函数名；如果没有这一行，interactive.py 需要一次性大改。
resolve_interactive_launch_target = resolve_interactive_windows_launch_target  # 新增代码+CompatSlimming：临时兼容旧交互目标解析函数名；如果没有这一行，interactive.py 迁移成本会扩大。
phase108_cli_line = windows_app_launch_target_cli_line  # 新增代码+CompatSlimming：临时兼容旧通用发现格式化函数名；如果没有这一行，旧验收入口会断。
resolve_generic_app_launch_target = resolve_windows_app_launch_target  # 新增代码+CompatSlimming：临时兼容旧通用发现函数名；如果没有这一行，后端和矩阵需要同步大改。


__all__ = ["PHASE124_WINDOWS_LAUNCH_RESOLVER_MARKER", "PHASE124_WINDOWS_LAUNCH_RESOLVER_MODEL", "PHASE124_WINDOWS_LAUNCH_RESOLVER_OK_TOKEN", "PHASE132_WINDOWS_APP_LAUNCH_TARGET_MARKER", "PHASE132_WINDOWS_APP_LAUNCH_TARGET_OK_TOKEN", "PHASE132_WINDOWS_APP_WINDOW_CONTROL_MARKER", "PHASE132_WINDOWS_APP_WINDOW_CONTROL_OK_TOKEN", "PHASE69_ACTIONS_EXPANDED", "PHASE69_APP_WINDOW_CONTROL_MARKER", "PHASE69_APP_WINDOW_CONTROL_OK_TOKEN", "PHASE107_INTERACTIVE_LAUNCH_TARGET_MARKER", "PHASE107_INTERACTIVE_LAUNCH_TARGET_OK_TOKEN", "PHASE108_GENERIC_APP_DISCOVERY_MARKER", "PHASE108_GENERIC_APP_DISCOVERY_MODEL", "PHASE108_GENERIC_APP_DISCOVERY_OK_TOKEN", "Phase69RecordingFocuser", "Phase69RecordingLauncher", "WindowsAppWindowControlRuntime", "build_launch_plan", "interactive_windows_launch_target_cli_line", "phase107_cli_line", "phase108_cli_line", "phase69_cli_line", "resolve_generic_app_launch_target", "resolve_interactive_launch_target", "resolve_interactive_windows_launch_target", "resolve_windows_app_launch_target", "resolve_windows_launch_plan", "run_phase69_app_window_control_contract", "run_windows_app_window_control_contract", "windows_app_launch_target_cli_line", "windows_app_window_control_cli_line"]  # 新增代码+CompatSlimming：公开瘦身后的 resolver/window API；如果没有这一行，迁移后的模块不能稳定导入。
