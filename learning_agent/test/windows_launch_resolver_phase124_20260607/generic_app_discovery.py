"""Phase108 通用 Windows 应用发现与默认关闭启动合同。"""  # 新增代码+Phase108GenericAppDiscovery：说明本模块负责通用发现和安全计划，不负责真实打开应用；如果没有这行代码，读者容易误以为这里已经无限制控制本机应用。
from __future__ import annotations  # 新增代码+Phase108GenericAppDiscovery：启用延迟类型注解；如果没有这行代码，后续类型提示在旧导入顺序下更容易遇到解析问题。

import os  # 新增代码+Phase108GenericAppDiscovery：读取 Windows Start Menu 环境变量；如果没有这行代码，模块只能依赖测试注入候选，缺少真实本机发现入口。
from pathlib import Path  # 新增代码+Phase108GenericAppDiscovery：用 Path 扫描只读开始菜单快捷方式；如果没有这行代码，路径拼接会更脆弱。
from typing import Any  # 新增代码+Phase108GenericAppDiscovery：描述 JSON 风格报告和候选字典；如果没有这行代码，接口含义对初学者不清楚。

try:  # 新增代码+Phase108GenericAppDiscovery：优先按标准包路径导入 Phase69 启动计划；如果没有这行代码，项目根运行时无法复用已有安全计划。
    from learning_agent.computer_use.windows_app_inventory import build_windows_app_inventory  # 修改代码+WindowsAppInventory：复用唯一 Windows 应用清单融合层；如果没有这一行，Phase108 会继续维护第二套应用发现逻辑。
    from learning_agent.computer_use.windows_launch_resolver import resolve_windows_launch_plan  # 新增代码+WindowsLaunchResolver：复用 Phase124 多后端启动解析器；如果没有这一行，Phase108 会继续把 AppX/shortcut 误压成 exe。
except ModuleNotFoundError as error:  # 新增代码+Phase108GenericAppDiscovery：兼容 start_oauth_agent.bat 从 learning_agent 目录启动的脚本模式；如果没有这行代码，真实可见终端可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.windows_app_inventory", "learning_agent.computer_use.windows_launch_resolver"}:  # 修改代码+WindowsLaunchResolver：只兜底包路径缺失；如果没有这一行，resolver 或 inventory 内部真实 bug 会被误吞。
        raise  # 新增代码+Phase108GenericAppDiscovery：重新抛出真实内部错误；如果没有这行代码，排查安全计划失败会很困难。
    from computer_use.windows_app_inventory import build_windows_app_inventory  # type: ignore  # 修改代码+WindowsAppInventory：脚本模式导入统一 Windows inventory；如果没有这一行，bat 入口会重新分叉出旧式发现逻辑。
    from computer_use.windows_launch_resolver import resolve_windows_launch_plan  # type: ignore  # 新增代码+WindowsLaunchResolver：脚本模式导入 Phase124 resolver；如果没有这一行，bat 入口仍会走旧 exe 猜测计划。

PHASE108_GENERIC_APP_DISCOVERY_MARKER = "PHASE108_GENERIC_APP_DISCOVERY_READY"  # 新增代码+Phase108GenericAppDiscovery：定义 Phase108 ready marker；如果没有这行代码，测试和真实终端无法稳定定位通用发现输出。
PHASE108_GENERIC_APP_DISCOVERY_OK_TOKEN = "PHASE108_GENERIC_APP_DISCOVERY_OK"  # 新增代码+Phase108GenericAppDiscovery：定义 Phase108 成功 token；如果没有这行代码，成功输出和普通日志无法区分。
PHASE108_GENERIC_APP_DISCOVERY_MODEL = "phase108_generic_app_discovery"  # 新增代码+Phase108GenericAppDiscovery：定义报告模型名；如果没有这行代码，后续能力矩阵无法区分 Phase108 报告版本。
PHASE108_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase108GenericAppDiscovery：声明本阶段没有扩张为无边界动作；如果没有这行代码，full 模式容易被误读成任意控制本机。
PHASE108_HIGH_RISK_TOKENS = ("powershell", "pwsh", "cmd", "terminal", "wt", "regedit", "registry", "control", "settings", "mmc", "taskmgr", "admin", "administrator", "credential", "password", "security", "firewall", "defender", "services")  # 新增代码+Phase108GenericAppDiscovery：定义通用发现后的高风险关键词；如果没有这行代码，动态发现可能把终端或系统工具当普通 app 放行。
PHASE108_START_MENU_SUFFIXES = (".lnk", ".appref-ms")  # 新增代码+Phase108GenericAppDiscovery：定义只读扫描的开始菜单快捷方式类型；如果没有这行代码，本机应用发现不知道要看哪些文件。
PHASE108_MAX_START_MENU_CANDIDATES = 500  # 新增代码+Phase108GenericAppDiscovery：限制只读扫描数量避免大目录拖慢 agent；如果没有这行代码，异常庞大的开始菜单可能让命令卡住。


def _phase108_bool_token(value: Any) -> str:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会混用 True/False 影响验收匹配。
    return "true" if bool(value) else "false"  # 新增代码+Phase108GenericAppDiscovery：返回 true 或 false；如果没有这行代码，场景断言容易因为大小写漂移失败。
# 新增代码+Phase108GenericAppDiscovery：函数段结束，_phase108_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


def _phase108_normalize_query(value: Any) -> str:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，清洗用户输入的应用名；如果没有这段函数，大小写、引号和空格会让发现结果不稳定。
    text = str(value or "").strip().strip("\"'`")  # 新增代码+Phase108GenericAppDiscovery：去掉首尾空白和常见包裹引号；如果没有这行代码，复制来的 `"obsidian"` 会被当成不同目标。
    return " ".join(text.split()).lower()  # 新增代码+Phase108GenericAppDiscovery：压缩连续空白并转小写；如果没有这行代码，`Visual   Studio` 这类输入不容易匹配候选。
# 新增代码+Phase108GenericAppDiscovery：函数段结束，_phase108_normalize_query 到此结束；如果没有这个边界说明，初学者不容易看出查询清洗范围。


def _phase108_executable_name(value: Any) -> str:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，把候选路径或名称转成可审计 exe 名；如果没有这段函数，报告可能暴露长路径或丢失 exe 后缀。
    text = str(value or "").strip().strip("\"'`")  # 新增代码+Phase108GenericAppDiscovery：先清理候选可执行文本；如果没有这行代码，带引号的路径会生成错误计划。
    if not text:  # 新增代码+Phase108GenericAppDiscovery：检查空候选；如果没有这行代码，空字符串可能被补成 `.exe`。
        return ""  # 新增代码+Phase108GenericAppDiscovery：空候选直接返回空；如果没有这行代码，调用方无法区分缺失目标。
    filename = text.replace("\\", "/").rsplit("/", 1)[-1].strip()  # 新增代码+Phase108GenericAppDiscovery：从 Windows 或普通路径中取文件名；如果没有这行代码，完整路径会影响风险词和计划字段。
    if not filename.lower().endswith(".exe"):  # 新增代码+Phase108GenericAppDiscovery：检查是否缺少 exe 后缀；如果没有这行代码，计划可能依赖 Windows 环境解析而不够稳定。
        filename = f"{filename}.exe"  # 新增代码+Phase108GenericAppDiscovery：为普通应用名补齐 exe 后缀；如果没有这行代码，Obsidian 这类名称无法形成一致启动计划。
    return filename  # 新增代码+Phase108GenericAppDiscovery：返回规范可执行文件名；如果没有这行代码，调用方拿不到启动计划输入。
# 新增代码+Phase108GenericAppDiscovery：函数段结束，_phase108_executable_name 到此结束；如果没有这个边界说明，初学者不容易看出可执行名规范化范围。


def _phase108_contains_high_risk_token(*values: Any) -> bool:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，在用户输入和候选身份里查高风险词；如果没有这段函数，动态发现会削弱原有安全边界。
    haystack = " ".join(str(value or "").lower() for value in values)  # 新增代码+Phase108GenericAppDiscovery：把多个身份字段合并成小写文本；如果没有这行代码，只检查输入会漏掉候选 executable 的风险。
    return any(token in haystack for token in PHASE108_HIGH_RISK_TOKENS)  # 新增代码+Phase108GenericAppDiscovery：命中任何风险词就返回真；如果没有这行代码，PowerShell、CMD、注册表等目标可能进入启动计划。
# 新增代码+Phase108GenericAppDiscovery：函数段结束，_phase108_contains_high_risk_token 到此结束；如果没有这个边界说明，初学者不容易看出风险判断范围。


def _phase108_candidate_from_mapping(candidate: dict[str, Any], default_source: str) -> dict[str, Any]:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，把外部候选规范成统一字段；如果没有这段函数，测试注入、开始菜单扫描和 fallback 形状会不一致。
    display_name = str(candidate.get("display_name") or candidate.get("name") or candidate.get("app_name") or candidate.get("executable") or "").strip()  # 新增代码+Phase108GenericAppDiscovery：读取人类可见应用名；如果没有这行代码，报告会缺少用户能理解的目标名称。
    executable_source = candidate.get("executable") or candidate.get("launch_id") or candidate.get("target") or candidate.get("path") or display_name  # 修改代码+WindowsAppInventory：优先兼容统一 inventory 的 launch_id 字段；如果没有这一行，Phase108 会忽略 inventory 解析出的真实启动标识。
    launch_kind = str(candidate.get("launch_kind") or "start_process_exe").strip() or "start_process_exe"  # 新增代码+WindowsLaunchResolver：保留候选启动类型；如果没有这一行，AppX/shortcut/uninstall_record 会继续被旧逻辑当 exe。
    launch_id = str(candidate.get("launch_id") or executable_source or "").strip()  # 新增代码+WindowsLaunchResolver：保留候选启动标识；如果没有这一行，resolver 拿不到 AUMID、快捷方式或 exe 名。
    executable = _phase108_executable_name(executable_source) if launch_kind in {"exe", "start_process_exe"} else ""  # 修改代码+WindowsLaunchResolver：只有 exe 类型才生成 executable；如果没有这一行，AppX 会被错误补成假 exe。
    app_name = str(candidate.get("app_name") or (executable[:-4].lower() if executable.lower().endswith(".exe") else display_name.lower())).strip().lower()  # 新增代码+WindowsLaunchResolver：保留模型可传的短 app_name；如果没有这一行，Phase108 报告无法稳定描述目标。
    aliases = tuple(str(alias) for alias in (candidate.get("aliases", ()) or ()))  # 新增代码+WindowsLaunchResolver：保留 inventory 别名；如果没有这一行，中文别名和短名匹配会丢失。
    source = str(candidate.get("source") or default_source).strip() or default_source  # 新增代码+Phase108GenericAppDiscovery：记录候选来自哪里；如果没有这行代码，用户无法区分开始菜单、注入候选和 fallback。
    return {"display_name": display_name or executable or launch_id, "app_name": app_name, "executable": executable, "launch_id": launch_id, "source": source, "launch_kind": launch_kind, "aliases": aliases, "installed_app_verified": bool(candidate.get("installed_app_verified", source != "generic_fallback"))}  # 修改代码+WindowsLaunchResolver：返回包含 launch 元数据的统一候选身份；如果没有这行代码，Phase108 会丢掉 resolver 需要的真实应用身份。
# 新增代码+Phase108GenericAppDiscovery：函数段结束，_phase108_candidate_from_mapping 到此结束；如果没有这个边界说明，初学者不容易看出候选规范化范围。


def _phase108_start_menu_roots() -> list[Path]:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，计算 Windows 开始菜单只读扫描目录；如果没有这段函数，真实本机发现只能靠 fallback。
    roots: list[Path] = []  # 新增代码+Phase108GenericAppDiscovery：准备候选目录列表；如果没有这行代码，后续无法累积多个来源。
    appdata = os.environ.get("APPDATA", "")  # 新增代码+Phase108GenericAppDiscovery：读取当前用户 AppData 路径；如果没有这行代码，用户级开始菜单不会被扫描。
    program_data = os.environ.get("ProgramData", "")  # 新增代码+Phase108GenericAppDiscovery：读取全局 ProgramData 路径；如果没有这行代码，所有用户安装的快捷方式不会被扫描。
    if appdata:  # 新增代码+Phase108GenericAppDiscovery：只有环境变量存在才加入用户目录；如果没有这行代码，空路径会变成当前目录。
        roots.append(Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")  # 新增代码+Phase108GenericAppDiscovery：加入用户级开始菜单目录；如果没有这行代码，当前用户安装应用更难被发现。
    if program_data:  # 新增代码+Phase108GenericAppDiscovery：只有全局路径存在才加入公共目录；如果没有这行代码，空 ProgramData 会造成错误路径。
        roots.append(Path(program_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs")  # 新增代码+Phase108GenericAppDiscovery：加入公共开始菜单目录；如果没有这行代码，系统级普通应用更难被发现。
    return roots  # 新增代码+Phase108GenericAppDiscovery：返回只读扫描目录列表；如果没有这行代码，发现函数拿不到目录。
# 新增代码+Phase108GenericAppDiscovery：函数段结束，_phase108_start_menu_roots 到此结束；如果没有这个边界说明，初学者不容易看出开始菜单目录范围。


def _phase108_discover_start_menu_candidates(query: str) -> list[dict[str, Any]]:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，只读扫描开始菜单候选；如果没有这段函数，Phase108 没有真实本机发现来源。
    matches: list[dict[str, Any]] = []  # 新增代码+Phase108GenericAppDiscovery：准备匹配候选列表；如果没有这行代码，扫描结果无处保存。
    normalized_query = _phase108_normalize_query(query)  # 新增代码+Phase108GenericAppDiscovery：规范查询文本；如果没有这行代码，大小写会影响开始菜单匹配。
    if not normalized_query:  # 新增代码+Phase108GenericAppDiscovery：空查询直接返回；如果没有这行代码，空目标会扫描大量快捷方式。
        return matches  # 新增代码+Phase108GenericAppDiscovery：返回空候选；如果没有这行代码，缺目标命令可能误选第一个应用。
    scanned = 0  # 新增代码+Phase108GenericAppDiscovery：记录扫描数量；如果没有这行代码，数量上限无法执行。
    for root in _phase108_start_menu_roots():  # 新增代码+Phase108GenericAppDiscovery：遍历用户和公共开始菜单目录；如果没有这行代码，本机发现没有目录来源。
        if not root.exists():  # 新增代码+Phase108GenericAppDiscovery：跳过不存在目录；如果没有这行代码，某些 Windows 配置会抛路径错误。
            continue  # 新增代码+Phase108GenericAppDiscovery：继续下一个目录；如果没有这行代码，不存在的目录会中断发现。
        for shortcut in root.rglob("*"):  # 新增代码+Phase108GenericAppDiscovery：递归读取快捷方式文件名；如果没有这行代码，子文件夹里的应用无法被发现。
            if scanned >= PHASE108_MAX_START_MENU_CANDIDATES:  # 新增代码+Phase108GenericAppDiscovery：达到上限就停止；如果没有这行代码，异常大目录可能拖慢命令。
                return matches  # 新增代码+Phase108GenericAppDiscovery：返回已经发现的候选；如果没有这行代码，扫描上限没有效果。
            scanned += 1  # 新增代码+Phase108GenericAppDiscovery：累加扫描数量；如果没有这行代码，上限判断不会推进。
            if shortcut.suffix.lower() not in PHASE108_START_MENU_SUFFIXES:  # 新增代码+Phase108GenericAppDiscovery：只处理快捷方式类型；如果没有这行代码，普通文件夹和文档会被误当应用。
                continue  # 新增代码+Phase108GenericAppDiscovery：跳过非快捷方式；如果没有这行代码，发现列表会混入无关文件。
            display_name = shortcut.stem  # 新增代码+Phase108GenericAppDiscovery：用快捷方式文件名作为显示名；如果没有这行代码，候选没有可读名称。
            if normalized_query not in _phase108_normalize_query(display_name):  # 新增代码+Phase108GenericAppDiscovery：只保留与查询相关的候选；如果没有这行代码，启动命令会看到太多无关应用。
                continue  # 新增代码+Phase108GenericAppDiscovery：跳过不匹配候选；如果没有这行代码，best candidate 可能选错目标。
            matches.append(_phase108_candidate_from_mapping({"display_name": display_name, "executable": display_name, "source": "start_menu", "installed_app_verified": True}, "start_menu"))  # 新增代码+Phase108GenericAppDiscovery：保存开始菜单候选；如果没有这行代码，扫描结果无法进入统一分类。
    return matches  # 新增代码+Phase108GenericAppDiscovery：返回开始菜单匹配结果；如果没有这行代码，调用方拿不到本机候选。
# 新增代码+Phase108GenericAppDiscovery：函数段结束，_phase108_discover_start_menu_candidates 到此结束；如果没有这个边界说明，初学者不容易看出只读扫描范围。


def _phase108_matches_query(query: str, candidate: dict[str, Any]) -> bool:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，判断候选是否匹配用户查询；如果没有这段函数，动态候选无法按目标筛选。
    normalized_query = _phase108_normalize_query(query)  # 新增代码+Phase108GenericAppDiscovery：清洗查询；如果没有这行代码，大小写或空格会影响匹配。
    display = _phase108_normalize_query(candidate.get("display_name", ""))  # 新增代码+Phase108GenericAppDiscovery：清洗显示名；如果没有这行代码，候选名称匹配不稳定。
    app_name = _phase108_normalize_query(candidate.get("app_name", ""))  # 新增代码+WindowsLaunchResolver：清洗 app_name；如果没有这一行，模型传短名时可能无法命中候选。
    executable = _phase108_normalize_query(candidate.get("executable", ""))  # 新增代码+Phase108GenericAppDiscovery：清洗可执行名；如果没有这行代码，只能靠显示名匹配。
    launch_id = _phase108_normalize_query(candidate.get("launch_id", ""))  # 新增代码+WindowsLaunchResolver：清洗 launch_id；如果没有这一行，AUMID 或快捷方式标识无法参与匹配。
    aliases = tuple(_phase108_normalize_query(alias) for alias in (candidate.get("aliases", ()) or ()))  # 新增代码+WindowsLaunchResolver：清洗候选别名；如果没有这一行，中文别名会在 Phase108 被丢弃。
    executable_stem = executable[:-4] if executable.endswith(".exe") else executable  # 新增代码+Phase108GenericAppDiscovery：去掉 exe 后缀得到短名；如果没有这行代码，`obsidian` 和 `obsidian.exe` 不容易互相匹配。
    return bool(normalized_query and (normalized_query in display or normalized_query in app_name or normalized_query in executable or normalized_query in launch_id or normalized_query == executable_stem or normalized_query in aliases))  # 修改代码+WindowsLaunchResolver：返回包含 launch_id/app_name/aliases 的匹配结果；如果没有这一行，AppX 和中文别名可能进不了 Phase108。
# 新增代码+Phase108GenericAppDiscovery：函数段结束，_phase108_matches_query 到此结束；如果没有这个边界说明，初学者不容易看出匹配范围。


def discover_generic_app_candidates(query: Any, candidates: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，发现与查询匹配的普通应用候选；如果没有这段函数，Phase108 只能硬编码单个目标。
    normalized_query = _phase108_normalize_query(query)  # 新增代码+Phase108GenericAppDiscovery：规范用户查询；如果没有这行代码，空白和大小写会影响发现。
    if not normalized_query:  # 新增代码+Phase108GenericAppDiscovery：拒绝空查询；如果没有这行代码，可能误生成默认应用候选。
        return []  # 新增代码+Phase108GenericAppDiscovery：空查询返回空列表；如果没有这行代码，调用方无法识别缺目标。
    if candidates is not None:  # 新增代码+Phase108GenericAppDiscovery：优先使用测试或上层注入的候选源；如果没有这行代码，单元测试无法稳定模拟不同本机应用。
        inventory_candidates = build_windows_app_inventory(candidates=candidates, include_common=False)  # 修改代码+WindowsAppInventory：先用统一 inventory 做多源清洗、去重和来源优先级排序；如果没有这一行，卸载注册表记录可能覆盖可启动入口。
        normalized_candidates = [_phase108_candidate_from_mapping(candidate, "injected") for candidate in inventory_candidates]  # 修改代码+WindowsAppInventory：把统一 inventory 输出转换成 Phase108 报告形状；如果没有这一行，Phase108 下游字段无法保持兼容。
        return [candidate for candidate in normalized_candidates if _phase108_matches_query(normalized_query, candidate)]  # 新增代码+Phase108GenericAppDiscovery：只返回匹配查询的注入候选；如果没有这行代码，错误候选可能被选中。
    inventory_candidates = build_windows_app_inventory(include_common=False)  # 修改代码+WindowsAppInventory：真实路径改为统一 inventory 多源发现；如果没有这一行，Phase108 仍只看开始菜单而无法对齐 ClaudeCode 设计原则。
    discovered = [_phase108_candidate_from_mapping(candidate, "inventory") for candidate in inventory_candidates if _phase108_matches_query(normalized_query, candidate)]  # 修改代码+WindowsAppInventory：从统一 inventory 中筛选匹配目标；如果没有这一行，真实多源清单无法进入 Phase108。
    if discovered:  # 新增代码+Phase108GenericAppDiscovery：如果找到本机候选就直接返回；如果没有这行代码，fallback 会掩盖真实发现结果。
        return discovered  # 新增代码+Phase108GenericAppDiscovery：返回真实发现候选；如果没有这行代码，用户无法看到开始菜单来源。
    return [_phase108_candidate_from_mapping({"display_name": normalized_query, "executable": normalized_query, "source": "generic_fallback", "installed_app_verified": False}, "generic_fallback")]  # 新增代码+Phase108GenericAppDiscovery：没有发现时生成通用 fallback 候选但不真实启动；如果没有这行代码，未知普通 app 会继续被逐个白名单卡住。
# 新增代码+Phase108GenericAppDiscovery：函数段结束，discover_generic_app_candidates 到此结束；如果没有这个边界说明，初学者不容易看出候选发现范围。


def resolve_generic_app_launch_target(raw_target: Any, candidates: list[dict[str, Any]] | None = None) -> dict[str, Any]:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，把用户目标解析成通用启动合同；如果没有这段函数，交互层无法摆脱硬编码 app 白名单。
    normalized_target = _phase108_normalize_query(raw_target)  # 新增代码+Phase108GenericAppDiscovery：清洗用户目标；如果没有这行代码，风险分类和候选匹配不稳定。
    discovered_candidates = discover_generic_app_candidates(normalized_target, candidates=candidates)  # 新增代码+Phase108GenericAppDiscovery：获取动态候选或 fallback 候选；如果没有这行代码，Phase108 没有通用发现事实。
    best_candidate = discovered_candidates[0] if discovered_candidates else {}  # 新增代码+Phase108GenericAppDiscovery：选择第一个匹配候选作为计划目标；如果没有这行代码，报告没有明确目标身份。
    best_display_name = str(best_candidate.get("display_name", "") or "")  # 新增代码+Phase108GenericAppDiscovery：读取候选显示名；如果没有这行代码，输出缺少人类可读目标。
    best_executable = str(best_candidate.get("executable", "") or "")  # 新增代码+Phase108GenericAppDiscovery：读取候选 exe 名；如果没有这行代码，启动计划没有可执行目标。
    best_launch_id = str(best_candidate.get("launch_id", "") or "")  # 新增代码+WindowsLaunchResolver：读取候选启动标识；如果没有这一行，报告无法说明 resolver 实际使用什么身份。
    best_launch_kind = str(best_candidate.get("launch_kind", "") or "")  # 新增代码+WindowsLaunchResolver：读取候选启动类型；如果没有这一行，调试时看不出 exe/AppX/shortcut 差异。
    best_app_name = str(best_candidate.get("app_name", "") or "")  # 新增代码+WindowsLaunchResolver：读取候选短 app_name；如果没有这一行，canonical_target 会继续只依赖 exe。
    high_risk_refused = _phase108_contains_high_risk_token(normalized_target, best_display_name, best_executable, best_launch_id, best_app_name)  # 修改代码+WindowsLaunchResolver：对输入和完整候选身份一起做高风险拒绝；如果没有这一行，AUMID 或 shortcut 中的风险词可能绕过安全策略。
    plan = resolve_windows_launch_plan(app_name=best_app_name or normalized_target, candidate=best_candidate) if best_candidate and not high_risk_refused else {"safe_to_launch": False, "refusal_reason": "high_risk_target_refused" if high_risk_refused else "no_candidate", "launch_backend": "", "resolver_used": False}  # 修改代码+WindowsLaunchResolver：把 Phase108 接到多后端 resolver；如果没有这一行，主链路仍会把 AppX/shortcut 压成 exe。
    safe_start_process_plan = bool(plan.get("safe_to_launch") and plan.get("launch_backend") == "argv_no_shell" and plan.get("launch_verb") == "Start-Process" and not plan.get("changes_registry") and not plan.get("changes_system_settings") and not plan.get("requires_admin") and not plan.get("uses_shell_string"))  # 修改代码+WindowsLaunchResolver：只把 argv_no_shell 算作 Phase110 当前可执行后端；如果没有这一行，AUMID 可能误进 Popen。
    safe_resolver_launch_plan = bool(plan.get("safe_to_launch") and plan.get("resolver_used") and not plan.get("changes_registry") and not plan.get("changes_system_settings") and not plan.get("requires_admin") and not plan.get("uses_shell_string"))  # 新增代码+WindowsLaunchResolver：汇总 resolver 级安全计划；如果没有这一行，AppX/shortcut 这种非 Popen 后端会被错误判失败。
    generic_unknown_app_default_off = bool(best_candidate.get("source") == "generic_fallback" and safe_resolver_launch_plan and not high_risk_refused)  # 修改代码+WindowsLaunchResolver：标记未知普通 app 走 resolver 且默认不启动；如果没有这一行，用户不知道未知应用只是进入计划没有被打开。
    generic_target_default_off = bool(safe_resolver_launch_plan and not high_risk_refused)  # 修改代码+WindowsLaunchResolver：标记任意通用普通目标默认不真实启动；如果没有这一行，非 exe 后端无法用同一个稳定字段验收。
    passed = bool(normalized_target and best_candidate and safe_resolver_launch_plan and not high_risk_refused)  # 修改代码+WindowsLaunchResolver：计算通用合同是否通过；如果没有这一行，AppX/shortcut 计划会被误判为失败。
    canonical_target = best_executable[:-4].lower() if best_executable.lower().endswith(".exe") else (best_app_name or normalized_target)  # 修改代码+WindowsLaunchResolver：优先用 exe 短名，否则用 app_name；如果没有这一行，AppX canonical target 会继续漂移。
    return {"marker": PHASE108_GENERIC_APP_DISCOVERY_MARKER, "ok_token": PHASE108_GENERIC_APP_DISCOVERY_OK_TOKEN, "model": PHASE108_GENERIC_APP_DISCOVERY_MODEL, "passed": passed, "raw_target": str(raw_target or ""), "normalized_target": normalized_target, "canonical_target": canonical_target, "candidate_count": len(discovered_candidates), "best_candidate_name": best_display_name, "best_candidate_executable": best_executable, "best_candidate_launch_id": best_launch_id, "best_candidate_launch_kind": best_launch_kind, "best_candidate_app_name": best_app_name, "candidate_source": str(best_candidate.get("source", "") or ""), "installed_app_verified": bool(best_candidate.get("installed_app_verified", False)), "dynamic_discovery_used": bool(best_candidate), "hardcoded_app_whitelist_required": False, "per_app_patch_required": False, "representative_category_testing": True, "safe_start_process_plan": safe_start_process_plan, "safe_resolver_launch_plan": safe_resolver_launch_plan, "resolver_launch_backend": str(plan.get("launch_backend", "") or ""), "high_risk_refused": high_risk_refused, "unknown_target_refused": not bool(best_candidate), "generic_unknown_app_default_off": generic_unknown_app_default_off, "generic_target_default_off": generic_target_default_off, "real_launch_default_disabled": True, "real_launch_attempted": False, "real_desktop_touched": False, "uncontrolled_actions_expanded": PHASE108_UNCONTROLLED_ACTIONS_EXPANDED, "launch_plan": plan}  # 修改代码+WindowsLaunchResolver：返回完整 Phase108 合同报告并保留 resolver 字段；如果没有这一行，测试、交互层和验收场景无法共享真实启动身份。
# 新增代码+Phase108GenericAppDiscovery：函数段结束，resolve_generic_app_launch_target 到此结束；如果没有这个边界说明，初学者不容易看出通用解析范围。


def phase108_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase108GenericAppDiscovery：函数段开始，把 Phase108 报告转成稳定 token 行；如果没有这段函数，真实可见终端验收只能解析复杂 JSON。
    ok_token = f" {PHASE108_GENERIC_APP_DISCOVERY_OK_TOKEN}" if bool(report.get("passed", False)) else ""  # 新增代码+Phase108GenericAppDiscovery：只在合同通过时追加 OK；如果没有这行代码，高风险拒绝也可能被误判成功。
    return f"{PHASE108_GENERIC_APP_DISCOVERY_MARKER}{ok_token} canonical_target={report.get('canonical_target', '')} dynamic_discovery_used={_phase108_bool_token(report.get('dynamic_discovery_used', False))} hardcoded_app_whitelist_required={_phase108_bool_token(report.get('hardcoded_app_whitelist_required', True))} per_app_patch_required={_phase108_bool_token(report.get('per_app_patch_required', True))} candidate_source={report.get('candidate_source', '')} resolver_launch_backend={report.get('resolver_launch_backend', '')} safe_resolver_launch_plan={_phase108_bool_token(report.get('safe_resolver_launch_plan', False))} generic_target_default_off={_phase108_bool_token(report.get('generic_target_default_off', False))} generic_unknown_app_default_off={_phase108_bool_token(report.get('generic_unknown_app_default_off', False))} high_risk_refused={_phase108_bool_token(report.get('high_risk_refused', False))} safe_start_process_plan={_phase108_bool_token(report.get('safe_start_process_plan', False))} real_launch_attempted={_phase108_bool_token(report.get('real_launch_attempted', False))} real_desktop_touched={_phase108_bool_token(report.get('real_desktop_touched', False))} uncontrolled_actions_expanded={_phase108_bool_token(report.get('uncontrolled_actions_expanded', False))}"  # 修改代码+WindowsLaunchResolver：返回固定顺序 token 并暴露 resolver 后端字段；如果没有这一行，真实终端无法直接证明 Phase108 已接到多后端 resolver。
# 新增代码+Phase108GenericAppDiscovery：函数段结束，phase108_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 输出范围。


__all__ = ["PHASE108_GENERIC_APP_DISCOVERY_MARKER", "PHASE108_GENERIC_APP_DISCOVERY_MODEL", "PHASE108_GENERIC_APP_DISCOVERY_OK_TOKEN", "PHASE108_UNCONTROLLED_ACTIONS_EXPANDED", "discover_generic_app_candidates", "phase108_cli_line", "resolve_generic_app_launch_target"]  # 新增代码+Phase108GenericAppDiscovery：限定公开导出名称；如果没有这行代码，通配导入会暴露内部 helper。
