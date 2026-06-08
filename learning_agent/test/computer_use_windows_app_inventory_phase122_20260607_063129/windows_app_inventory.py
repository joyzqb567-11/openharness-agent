"""Windows Computer Use 应用清单融合层。"""  # 新增代码+WindowsAppInventory：说明本模块是 Windows 版 ClaudeCode appNames 策略适配层；如果没有这一行，读者容易误以为这里直接执行桌面动作。
from __future__ import annotations  # 新增代码+WindowsAppInventory：启用延迟类型注解；如果没有这一行，复杂类型在较旧解释路径下更容易解析失败。

import os  # 新增代码+WindowsAppInventory：读取 Windows 开始菜单环境变量；如果没有这一行，真实枚举无法找到用户和公共开始菜单目录。
import unicodedata  # 新增代码+WindowsAppInventory：检查 Unicode 字符类别；如果没有这一行，中文应用名和英文应用名无法共享安全字符规则。
from pathlib import Path  # 新增代码+WindowsAppInventory：用 Path 处理 Windows 路径和快捷方式文件名；如果没有这一行，路径拼接会更脆弱。
from typing import Any  # 新增代码+WindowsAppInventory：描述 JSON 风格候选字典；如果没有这一行，接口意图对初学者不够清楚。

APP_INVENTORY_MAX_COUNT = 50  # 新增代码+WindowsAppInventory：限制最多给模型 50 个应用候选；如果没有这一行，海量本机应用会撑大 prompt 并分散模型注意力。
APP_INVENTORY_NAME_MAX_CHARS = 40  # 新增代码+WindowsAppInventory：限制单个应用显示名长度；如果没有这一行，异常长名称会污染模型上下文。
APP_INVENTORY_ALLOWED_PUNCTUATION = set(" _.&'()+-")  # 新增代码+WindowsAppInventory：允许正常应用名常见标点；如果没有这一行，Visual Studio Code 等名字会被误删。
APP_INVENTORY_SOURCE_PRIORITY = {"common_system_hint": 0, "start_menu": 10, "app_paths_registry": 20, "appx_package": 30, "running_window": 40, "uninstall_registry": 80, "generic_fallback": 90, "unknown": 99}  # 新增代码+WindowsAppInventory：定义多源去重优先级；如果没有这一行，卸载注册表记录可能覆盖真实可启动入口。
APP_INVENTORY_BLOCKED_EXACT_NAMES = {"run", "computer management", "event viewer", "disk cleanup", "remote desktop connection", "steps recorder", "memory diagnostics tool", "odbc data sources (32-bit)", "odbc data sources (64-bit)", "iscsi initiator", "dfrgui", "magnify", "narrator", "on-screen keyboard", "voiceaccess", "livecaptions", "performance monitor", "print management", "recoverydrive", "resource monitor", "system configuration", "system information", "task scheduler"}  # 新增代码+WindowsAppInventory：精确拦截系统/辅助/管理入口；如果没有这一行，模型候选会混入不适合普通任务优先打开的工具。
APP_INVENTORY_NOISE_TOKENS = ("helper", "agent", "service", "installer", "install", "uninstaller", "uninstall", "updater", "update", "redistributable", "background", "runtime broker", "documentation", "release notes", "manuals", "help", "official website", "website", "卸载", "修复", "官网", "配置")  # 修改代码+WindowsAppInventory：过滤后台组件、安装维护、运行库、网站入口和帮助文档噪声；如果没有这一行，模型可能打开维护入口或网页快捷方式而不是应用本体。
APP_INVENTORY_HIGH_RISK_TOKENS = ("powershell", "pwsh", "cmd", "command prompt", "command line", "terminal", "bash", "verifier", "debuggable", "wt", "regedit", "registry", "control", "settings", "mmc", "taskmgr", "administrator", "administrative tools", "credential", "password", "security", "firewall", "defender", "services", "wsl", "system tools", "windows tools")  # 修改代码+WindowsAppInventory：过滤终端、命令行资料、调试验证和系统安全工具；如果没有这一行，模型可能把高风险或诊断工具当普通应用。
APP_INVENTORY_COMMON_HINTS = (  # 新增代码+WindowsAppInventory：常用系统应用兜底清单开始；如果没有这一行，枚举失败时 Paint 等基础工具缺少稳定提示。
    {"display_name": "Paint", "app_name": "mspaint", "launch_id": "mspaint.exe", "launch_kind": "exe", "source": "common_system_hint", "aliases": ("画图", "画图软件", "paint", "mspaint", "mspaint.exe")},  # 新增代码+WindowsAppInventory：提供 Paint 稳定启动候选；如果没有这一行，中文画图任务可能继续传错 app 名。
    {"display_name": "Notepad", "app_name": "notepad", "launch_id": "notepad.exe", "launch_kind": "exe", "source": "common_system_hint", "aliases": ("记事本", "notepad", "notepad.exe")},  # 新增代码+WindowsAppInventory：提供 Notepad 稳定启动候选；如果没有这一行，记事本文本任务可能缺少规范入口。
    {"display_name": "Calculator", "app_name": "calc", "launch_id": "calc.exe", "launch_kind": "exe", "source": "common_system_hint", "aliases": ("计算器", "calculator", "calc", "calc.exe")},  # 新增代码+WindowsAppInventory：提供 Calculator 稳定启动候选；如果没有这一行，计算器任务可能在 AppX 和 exe 名之间摇摆。
)  # 新增代码+WindowsAppInventory：常用系统应用兜底清单结束；如果没有这一行，Python 语法不完整。


def _inventory_collapse_spaces(text: Any) -> str:  # 新增代码+WindowsAppInventory：函数段开始，压缩应用名空白；如果没有这段函数，去重和匹配会被多余空格干扰。
    return " ".join(str(text or "").strip().split())  # 新增代码+WindowsAppInventory：返回压缩后的文本；如果没有这一行，同一应用的多个空格版本会被当成不同候选。
# 新增代码+WindowsAppInventory：函数段结束，_inventory_collapse_spaces 到此结束；如果没有这个边界说明，用户不容易看出空白清洗范围。


def _inventory_basename(value: Any) -> str:  # 新增代码+WindowsAppInventory：函数段开始，把路径或快捷方式名变成基名；如果没有这段函数，模型提示可能泄露完整本机路径。
    text = str(value or "").strip().strip("\"'`")  # 新增代码+WindowsAppInventory：清除外层空白和引号；如果没有这一行，带引号路径会生成不稳定启动名。
    if not text:  # 新增代码+WindowsAppInventory：检查空值；如果没有这一行，空字符串可能被当成有效路径。
        return ""  # 新增代码+WindowsAppInventory：空值返回空；如果没有这一行，调用方无法识别缺少启动标识。
    return text.replace("\\", "/").rsplit("/", 1)[-1].strip()  # 新增代码+WindowsAppInventory：只保留最后一段名称；如果没有这一行，用户目录和完整路径可能进入模型上下文。
# 新增代码+WindowsAppInventory：函数段结束，_inventory_basename 到此结束；如果没有这个边界说明，用户不容易看出路径脱敏范围。


def _inventory_app_name_from_launch_id(launch_id: Any, fallback: Any = "") -> str:  # 新增代码+WindowsAppInventory：函数段开始，生成模型可传的短 app_name；如果没有这段函数，模型可能继续使用长显示名或路径。
    base = _inventory_basename(launch_id)  # 新增代码+WindowsAppInventory：先取启动标识基名；如果没有这一行，完整路径会影响 app_name。
    stem = base[:-4] if base.lower().endswith(".exe") else base  # 新增代码+WindowsAppInventory：去掉 exe 后缀；如果没有这一行，mspaint 和 mspaint.exe 会混用。
    safe = _inventory_collapse_spaces(stem or fallback).lower()  # 新增代码+WindowsAppInventory：压缩空白并转小写；如果没有这一行，大小写和多空格会破坏去重。
    return safe.replace(" ", "") if safe and all(ord(char) < 128 for char in safe) else safe  # 新增代码+WindowsAppInventory：英文短名去空格便于启动；如果没有这一行，Visual Studio Code 可能生成带空格 app_name。
# 新增代码+WindowsAppInventory：函数段结束，_inventory_app_name_from_launch_id 到此结束；如果没有这个边界说明，用户不容易看出 app_name 生成范围。


def _inventory_has_safe_chars(text: str) -> bool:  # 新增代码+WindowsAppInventory：函数段开始，检查应用名字符是否安全；如果没有这段函数，恶意快捷方式名可能注入提示。
    if any(char in "\r\n\t<>`{}[]|;" for char in text):  # 新增代码+WindowsAppInventory：拒绝会破坏提示结构的字符；如果没有这一行，多行应用名可能伪造指令。
        return False  # 新增代码+WindowsAppInventory：命中危险字符直接拒绝；如果没有这一行，危险名称会继续流入模型提示。
    for char in text:  # 新增代码+WindowsAppInventory：逐字符检查 Unicode 类别；如果没有这一行，中文和英文无法兼容过滤。
        category = unicodedata.category(char)  # 新增代码+WindowsAppInventory：读取字符类别；如果没有这一行，无法区分文字数字和控制符。
        if category[0] in {"L", "N", "M"} or char in APP_INVENTORY_ALLOWED_PUNCTUATION:  # 新增代码+WindowsAppInventory：允许文字、数字、组合标记和常见安全标点；如果没有这一行，正常应用名会被误删。
            continue  # 新增代码+WindowsAppInventory：安全字符继续检查；如果没有这一行，循环逻辑无法表达通过。
        return False  # 新增代码+WindowsAppInventory：未知或危险符号拒绝；如果没有这一行，提示注入面会扩大。
    return True  # 新增代码+WindowsAppInventory：所有字符安全才通过；如果没有这一行，正常应用名也会被拒绝。
# 新增代码+WindowsAppInventory：函数段结束，_inventory_has_safe_chars 到此结束；如果没有这个边界说明，用户不容易看出字符过滤范围。


def sanitize_inventory_display_name(raw: Any) -> str:  # 新增代码+WindowsAppInventory：函数段开始，清洗模型可见显示名；如果没有这段函数，原始本机名称会直接进入 prompt。
    text = _inventory_collapse_spaces(str(raw or "").strip().strip("\"'`"))  # 新增代码+WindowsAppInventory：清理引号和多余空白；如果没有这一行，同名应用会因为格式差异重复。
    if not text or len(text) > APP_INVENTORY_NAME_MAX_CHARS:  # 新增代码+WindowsAppInventory：拒绝空名和超长名；如果没有这一行，异常名称会污染候选清单。
        return ""  # 新增代码+WindowsAppInventory：非法长度返回空；如果没有这一行，调用方无法统一跳过。
    if not _inventory_has_safe_chars(text):  # 新增代码+WindowsAppInventory：执行安全字符检查；如果没有这一行，换行/注入符号可能留下。
        return ""  # 新增代码+WindowsAppInventory：不安全名称返回空；如果没有这一行，过滤层不会真正生效。
    return text  # 新增代码+WindowsAppInventory：返回安全显示名；如果没有这一行，安全候选也会丢失。
# 新增代码+WindowsAppInventory：函数段结束，sanitize_inventory_display_name 到此结束；如果没有这个边界说明，用户不容易看出显示名清洗范围。


def _inventory_contains_token(tokens: tuple[str, ...], *values: Any) -> bool:  # 新增代码+WindowsAppInventory：函数段开始，统一匹配风险/噪声词；如果没有这段函数，多处过滤会重复且不一致。
    haystack = " ".join(str(value or "").casefold() for value in values)  # 新增代码+WindowsAppInventory：合并候选字段为小写文本；如果没有这一行，只查显示名会漏掉启动标识里的风险。
    return any(token.casefold() in haystack for token in tokens)  # 新增代码+WindowsAppInventory：任一关键词命中即返回真；如果没有这一行，调用方无法执行过滤判断。
# 新增代码+WindowsAppInventory：函数段结束，_inventory_contains_token 到此结束；如果没有这个边界说明，用户不容易看出关键词过滤范围。


def _inventory_entry_from_mapping(candidate: dict[str, Any], default_source: str = "unknown") -> dict[str, Any]:  # 新增代码+WindowsAppInventory：函数段开始，把任意来源候选规范成统一结构；如果没有这段函数，多源枚举会产生不同字段。
    source = str(candidate.get("source") or default_source or "unknown").strip()  # 新增代码+WindowsAppInventory：读取来源名称；如果没有这一行，后续优先级和调试信息无法判断来源。
    launch_kind = str(candidate.get("launch_kind") or ("appx" if source == "appx_package" else "exe")).strip()  # 新增代码+WindowsAppInventory：读取启动类型；如果没有这一行，resolver 不知道候选应该用 exe 还是 AppX。
    display = sanitize_inventory_display_name(candidate.get("display_name") or candidate.get("name") or candidate.get("app_name") or candidate.get("launch_id") or candidate.get("executable"))  # 新增代码+WindowsAppInventory：清洗显示名；如果没有这一行，模型可见名字不受控。
    launch_id = str(candidate.get("launch_id") or candidate.get("executable") or candidate.get("target") or candidate.get("path") or display).strip()  # 新增代码+WindowsAppInventory：读取启动标识但不直接展示原始路径；如果没有这一行，启动 resolver 没有目标。
    app_name = str(candidate.get("app_name") or _inventory_app_name_from_launch_id(launch_id, fallback=display)).strip().lower()  # 新增代码+WindowsAppInventory：生成短 app_name；如果没有这一行，模型不知道调用 launch_app 时传什么。
    aliases = tuple(str(alias).strip().lower() for alias in candidate.get("aliases", ()) if str(alias).strip())  # 新增代码+WindowsAppInventory：保留别名用于解析；如果没有这一行，中文“画图”等别名无法复用。
    return {"display_name": display, "app_name": app_name, "launch_id": _inventory_basename(launch_id) if launch_kind in {"exe", "shortcut"} else launch_id, "launch_kind": launch_kind, "source": source, "aliases": aliases, "source_priority": APP_INVENTORY_SOURCE_PRIORITY.get(source, APP_INVENTORY_SOURCE_PRIORITY["unknown"]), "installed_app_verified": bool(candidate.get("installed_app_verified", source not in {"common_system_hint", "generic_fallback", "unknown"}))}  # 新增代码+WindowsAppInventory：返回统一候选字典；如果没有这一行，后续清洗、去重和格式化没有共同协议。
# 新增代码+WindowsAppInventory：函数段结束，_inventory_entry_from_mapping 到此结束；如果没有这个边界说明，用户不容易看出候选规范化范围。


def _inventory_is_model_visible_app(entry: dict[str, Any]) -> bool:  # 新增代码+WindowsAppInventory：函数段开始，判断候选是否应给模型看；如果没有这段函数，风险过滤和噪声过滤会散落各处。
    if not entry.get("display_name") or not entry.get("app_name"):  # 新增代码+WindowsAppInventory：拒绝缺少核心字段的候选；如果没有这一行，模型会看到不可启动或不可读项。
        return False  # 新增代码+WindowsAppInventory：核心字段缺失时不可见；如果没有这一行，坏候选会进入清单。
    if str(entry.get("display_name", "")).casefold() in APP_INVENTORY_BLOCKED_EXACT_NAMES or str(entry.get("app_name", "")).casefold() in APP_INVENTORY_BLOCKED_EXACT_NAMES:  # 新增代码+WindowsAppInventory：精确拦截短系统工具名；如果没有这一行，Run 这类短词很难靠风险词稳定过滤。
        return False  # 新增代码+WindowsAppInventory：命中精确黑名单则不可见；如果没有这一行，黑名单不会生效。
    if _inventory_contains_token(APP_INVENTORY_HIGH_RISK_TOKENS, entry.get("display_name"), entry.get("app_name"), entry.get("launch_id")):  # 新增代码+WindowsAppInventory：检查终端/安全/系统工具风险；如果没有这一行，高风险工具会混入普通应用。
        return False  # 新增代码+WindowsAppInventory：高风险候选不可见；如果没有这一行，模型可能选择终端工具。
    if _inventory_contains_token(APP_INVENTORY_NOISE_TOKENS, entry.get("display_name"), entry.get("app_name"), entry.get("launch_id")):  # 新增代码+WindowsAppInventory：检查安装器、卸载器、帮助文档等噪声；如果没有这一行，维护入口会污染清单。
        return False  # 新增代码+WindowsAppInventory：噪声候选不可见；如果没有这一行，模型可能选择错误入口。
    return True  # 新增代码+WindowsAppInventory：通过所有检查后可见；如果没有这一行，正常应用也无法进入清单。
# 新增代码+WindowsAppInventory：函数段结束，_inventory_is_model_visible_app 到此结束；如果没有这个边界说明，用户不容易看出可见性过滤范围。


def build_windows_app_inventory(candidates: list[dict[str, Any]] | None = None, include_common: bool = True, max_count: int = APP_INVENTORY_MAX_COUNT) -> list[dict[str, Any]]:  # 新增代码+WindowsAppInventory：函数段开始，融合多源 Windows 应用候选；如果没有这段函数，OpenHarness 只能在各处重复猜 app 名。
    raw_items = list(APP_INVENTORY_COMMON_HINTS) if include_common else []  # 新增代码+WindowsAppInventory：按需加入常用系统应用兜底；如果没有这一行，枚举失败时 Paint 等常用目标缺少入口。
    raw_items.extend(list(candidates) if candidates is not None else discover_windows_app_inventory_sources())  # 新增代码+WindowsAppInventory：追加注入候选或真实枚举候选；如果没有这一行，inventory 没有真实来源。
    best_by_key: dict[str, dict[str, Any]] = {}  # 新增代码+WindowsAppInventory：准备按名称去重后的最佳候选；如果没有这一行，多源候选无法合并。
    for item in raw_items:  # 新增代码+WindowsAppInventory：逐个处理候选；如果没有这一行，函数不会清洗任何来源。
        if not isinstance(item, dict):  # 新增代码+WindowsAppInventory：防御非字典坏输入；如果没有这一行，坏候选会让流程崩溃。
            continue  # 新增代码+WindowsAppInventory：跳过非法候选；如果没有这一行，非字典输入无法安全忽略。
        entry = _inventory_entry_from_mapping(item)  # 新增代码+WindowsAppInventory：规范化候选；如果没有这一行，过滤和去重无法共享字段。
        if not _inventory_is_model_visible_app(entry):  # 新增代码+WindowsAppInventory：过滤不可给模型看的风险/噪声项；如果没有这一行，清单会混入终端、卸载器等入口。
            continue  # 新增代码+WindowsAppInventory：跳过不可见候选；如果没有这一行，过滤函数不会生效。
        key = str(entry["display_name"]).casefold()  # 新增代码+WindowsAppInventory：用显示名作为跨来源产品去重键；如果没有这一行，卸载注册表和开始菜单同名项会重复。
        current = best_by_key.get(key)  # 新增代码+WindowsAppInventory：读取当前最佳候选；如果没有这一行，无法比较来源优先级。
        if current is None or int(entry["source_priority"]) < int(current["source_priority"]):  # 新增代码+WindowsAppInventory：优先保留更可启动、更可信来源；如果没有这一行，卸载记录可能覆盖开始菜单入口。
            best_by_key[key] = entry  # 新增代码+WindowsAppInventory：保存当前最佳候选；如果没有这一行，去重结果不会更新。
    return sorted(best_by_key.values(), key=lambda entry: (int(entry["source_priority"]), str(entry["display_name"]).casefold()))[:max_count]  # 新增代码+WindowsAppInventory：按来源优先级和名称排序并截断；如果没有这一行，输出顺序和 prompt 长度不稳定。
# 新增代码+WindowsAppInventory：函数段结束，build_windows_app_inventory 到此结束；如果没有这个边界说明，用户不容易看出多源融合范围。


def format_windows_app_inventory_for_model(apps: Any) -> str:  # 新增代码+WindowsAppInventory：函数段开始，把 inventory 转成模型提示；如果没有这段函数，主循环只能拿原始字典。
    entries = build_windows_app_inventory(list(apps or []), include_common=False)  # 新增代码+WindowsAppInventory：格式化前重新清洗一次候选；如果没有这一行，外部脏数据可能绕过过滤。
    if not entries:  # 新增代码+WindowsAppInventory：处理空清单；如果没有这一行，模型看不到明确状态。
        return "Available desktop application candidates (cleaned model hints, not a hard whitelist): none."  # 新增代码+WindowsAppInventory：返回空清单提示；如果没有这一行，空结果可能被误解为异常。
    parts = [f"{entry['display_name']} [app_name={entry['app_name']}, launch_kind={entry['launch_kind']}, source={entry['source']}]" for entry in entries]  # 新增代码+WindowsAppInventory：生成不含路径的候选片段；如果没有这一行，模型无法快速选择启动方式。
    return "Available desktop application candidates (cleaned model hints, not a hard whitelist): " + "; ".join(parts) + "."  # 新增代码+WindowsAppInventory：返回 ClaudeCode 风格单行提示；如果没有这一行，主循环无法获得可读清单。
# 新增代码+WindowsAppInventory：函数段结束，format_windows_app_inventory_for_model 到此结束；如果没有这个边界说明，用户不容易看出模型提示范围。


def _inventory_start_menu_roots() -> list[Path]:  # 新增代码+WindowsAppInventory：函数段开始，收集开始菜单目录；如果没有这段函数，真实枚举缺少 Windows 用户可见应用来源。
    roots: list[Path] = []  # 新增代码+WindowsAppInventory：准备目录列表；如果没有这一行，无法累计多个来源。
    appdata = os.environ.get("APPDATA", "")  # 新增代码+WindowsAppInventory：读取当前用户 AppData；如果没有这一行，用户级快捷方式会漏掉。
    program_data = os.environ.get("ProgramData", "")  # 新增代码+WindowsAppInventory：读取公共 ProgramData；如果没有这一行，全局快捷方式会漏掉。
    if appdata:  # 新增代码+WindowsAppInventory：只在变量存在时加入用户目录；如果没有这一行，空路径会误指当前目录。
        roots.append(Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")  # 新增代码+WindowsAppInventory：加入用户开始菜单；如果没有这一行，当前用户安装应用发现率下降。
    if program_data:  # 新增代码+WindowsAppInventory：只在变量存在时加入公共目录；如果没有这一行，空路径会造成误扫。
        roots.append(Path(program_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs")  # 新增代码+WindowsAppInventory：加入公共开始菜单；如果没有这一行，系统级应用发现率下降。
    return roots  # 新增代码+WindowsAppInventory：返回目录列表；如果没有这一行，扫描函数没有输入。
# 新增代码+WindowsAppInventory：函数段结束，_inventory_start_menu_roots 到此结束；如果没有这个边界说明，用户不容易看出目录来源。


def _inventory_discover_start_menu(max_scan: int = 500) -> list[dict[str, Any]]:  # 新增代码+WindowsAppInventory：函数段开始，枚举开始菜单快捷方式；如果没有这段函数，Windows 可启动入口少一大块。
    entries: list[dict[str, Any]] = []  # 新增代码+WindowsAppInventory：准备候选列表；如果没有这一行，扫描结果无法保存。
    scanned = 0  # 新增代码+WindowsAppInventory：记录扫描数量；如果没有这一行，大目录上限无法执行。
    for root in _inventory_start_menu_roots():  # 新增代码+WindowsAppInventory：遍历开始菜单目录；如果没有这一行，函数不会扫描任何目录。
        if not root.exists():  # 新增代码+WindowsAppInventory：跳过不存在目录；如果没有这一行，某些 Windows 配置会抛错。
            continue  # 新增代码+WindowsAppInventory：继续下个目录；如果没有这一行，不存在目录会中断扫描。
        for shortcut in root.rglob("*"):  # 新增代码+WindowsAppInventory：递归读取快捷方式；如果没有这一行，子文件夹应用会漏掉。
            if scanned >= max_scan:  # 新增代码+WindowsAppInventory：达到扫描上限时停止；如果没有这一行，异常大目录会拖慢 agent。
                return entries  # 新增代码+WindowsAppInventory：返回已发现结果；如果没有这一行，上限不会生效。
            scanned += 1  # 新增代码+WindowsAppInventory：推进扫描计数；如果没有这一行，上限判断不会变化。
            if shortcut.suffix.lower() not in {".lnk", ".appref-ms"}:  # 新增代码+WindowsAppInventory：只保留快捷方式；如果没有这一行，普通文件可能被当成应用。
                continue  # 新增代码+WindowsAppInventory：跳过非快捷方式；如果没有这一行，清单噪声会增加。
            entries.append({"display_name": shortcut.stem, "launch_id": shortcut.stem, "launch_kind": "exe", "source": "start_menu", "installed_app_verified": True})  # 新增代码+WindowsAppInventory：保存脱敏开始菜单候选；如果没有这一行，开始菜单来源不会进入 inventory。
    return entries  # 新增代码+WindowsAppInventory：返回开始菜单候选；如果没有这一行，调用方拿不到结果。
# 新增代码+WindowsAppInventory：函数段结束，_inventory_discover_start_menu 到此结束；如果没有这个边界说明，用户不容易看出开始菜单枚举范围。


def _inventory_discover_app_paths() -> list[dict[str, Any]]:  # 新增代码+WindowsAppInventory：函数段开始，枚举 App Paths 注册表；如果没有这段函数，不在开始菜单里的可执行别名会漏掉。
    try:  # 新增代码+WindowsAppInventory：尝试导入 Windows 注册表模块；如果没有这一行，非 Windows 环境会直接崩溃。
        import winreg  # type: ignore  # 新增代码+WindowsAppInventory：导入 winreg 做只读枚举；如果没有这一行，无法读取 App Paths。
    except (ImportError, ModuleNotFoundError):  # 新增代码+WindowsAppInventory：兼容非 Windows 环境；如果没有这一行，跨平台测试会失败。
        return []  # 新增代码+WindowsAppInventory：不可用时软降级为空；如果没有这一行，枚举失败会中断主流程。
    entries: list[dict[str, Any]] = []  # 新增代码+WindowsAppInventory：准备候选列表；如果没有这一行，注册表结果无法保存。
    roots = ((winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths"), (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths"))  # 新增代码+WindowsAppInventory：定义用户级和机器级 App Paths；如果没有这一行，只能枚举单一范围。
    for hive, subkey in roots:  # 新增代码+WindowsAppInventory：遍历注册表根；如果没有这一行，不会读取任何 App Paths。
        try:  # 新增代码+WindowsAppInventory：尝试打开注册表键；如果没有这一行，缺失键会中断流程。
            with winreg.OpenKey(hive, subkey) as key:  # 新增代码+WindowsAppInventory：只读打开 App Paths；如果没有这一行，无法枚举子项。
                index = 0  # 新增代码+WindowsAppInventory：初始化索引；如果没有这一行，循环没有起点。
                while index < 500:  # 新增代码+WindowsAppInventory：限制最多读取 500 项；如果没有这一行，异常注册表可能拖慢启动。
                    try:  # 新增代码+WindowsAppInventory：读取子项名；如果没有这一行，枚举结束无法安全处理。
                        name = winreg.EnumKey(key, index)  # 新增代码+WindowsAppInventory：读取 exe 子项名；如果没有这一行，候选没有启动标识。
                    except OSError:  # 新增代码+WindowsAppInventory：枚举结束时退出；如果没有这一行，正常结束会变成异常。
                        break  # 新增代码+WindowsAppInventory：停止当前根扫描；如果没有这一行，循环无法结束。
                    entries.append({"display_name": Path(name).stem, "launch_id": name, "launch_kind": "exe", "source": "app_paths_registry", "installed_app_verified": True})  # 新增代码+WindowsAppInventory：保存 App Paths 候选；如果没有这一行，注册表来源不会进入 inventory。
                    index += 1  # 新增代码+WindowsAppInventory：推进索引；如果没有这一行，循环会卡住。
        except OSError:  # 新增代码+WindowsAppInventory：忽略不存在或无权限键；如果没有这一行，普通用户权限可能让枚举失败。
            continue  # 新增代码+WindowsAppInventory：继续下一个根；如果没有这一行，单个根失败会停止全部枚举。
    return entries  # 新增代码+WindowsAppInventory：返回 App Paths 候选；如果没有这一行，调用方拿不到结果。
# 新增代码+WindowsAppInventory：函数段结束，_inventory_discover_app_paths 到此结束；如果没有这个边界说明，用户不容易看出 App Paths 枚举范围。


def _inventory_discover_uninstall_registry() -> list[dict[str, Any]]:  # 新增代码+WindowsAppInventory：函数段开始，枚举卸载注册表显示名；如果没有这段函数，设置页类产品记录无法作为辅助源。
    try:  # 新增代码+WindowsAppInventory：尝试导入注册表模块；如果没有这一行，非 Windows 环境会崩溃。
        import winreg  # type: ignore  # 新增代码+WindowsAppInventory：导入 winreg 读取 Uninstall 键；如果没有这一行，无法靠注册表补足设置页来源。
    except (ImportError, ModuleNotFoundError):  # 新增代码+WindowsAppInventory：兼容非 Windows 环境；如果没有这一行，跨平台测试会失败。
        return []  # 新增代码+WindowsAppInventory：不可用时返回空；如果没有这一行，枚举失败会中断主流程。
    entries: list[dict[str, Any]] = []  # 新增代码+WindowsAppInventory：准备产品记录列表；如果没有这一行，扫描结果无法保存。
    roots = ((winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"), (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"), (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"))  # 新增代码+WindowsAppInventory：定义设置页常用卸载注册表来源；如果没有这一行，会漏掉 32 位或用户级安装记录。
    for hive, subkey in roots:  # 新增代码+WindowsAppInventory：遍历卸载注册表根；如果没有这一行，不会读取任何产品记录。
        try:  # 新增代码+WindowsAppInventory：尝试打开根键；如果没有这一行，缺失键会中断流程。
            with winreg.OpenKey(hive, subkey) as key:  # 新增代码+WindowsAppInventory：只读打开卸载键；如果没有这一行，无法枚举子项。
                index = 0  # 新增代码+WindowsAppInventory：初始化索引；如果没有这一行，循环没有起点。
                while index < 1000:  # 新增代码+WindowsAppInventory：限制最多读取 1000 项；如果没有这一行，异常注册表可能拖慢 agent。
                    try:  # 新增代码+WindowsAppInventory：读取产品子项；如果没有这一行，枚举结束无法安全处理。
                        child = winreg.EnumKey(key, index)  # 新增代码+WindowsAppInventory：读取子项名；如果没有这一行，无法打开具体产品项。
                    except OSError:  # 新增代码+WindowsAppInventory：枚举结束时退出；如果没有这一行，正常结束会被当成错误。
                        break  # 新增代码+WindowsAppInventory：停止当前根扫描；如果没有这一行，循环无法结束。
                    index += 1  # 新增代码+WindowsAppInventory：推进索引；如果没有这一行，循环会卡住。
                    try:  # 新增代码+WindowsAppInventory：尝试打开产品子项；如果没有这一行，单个坏项会中断整个枚举。
                        with winreg.OpenKey(key, child) as child_key:  # 新增代码+WindowsAppInventory：只读打开产品项；如果没有这一行，无法读取 DisplayName。
                            display_name, _kind = winreg.QueryValueEx(child_key, "DisplayName")  # 新增代码+WindowsAppInventory：读取设置页显示名；如果没有这一行，卸载注册表来源没有可读名称。
                    except OSError:  # 新增代码+WindowsAppInventory：忽略缺少 DisplayName 的项；如果没有这一行，普通组件项会导致异常。
                        continue  # 新增代码+WindowsAppInventory：继续下一个产品项；如果没有这一行，单项失败会停止全部扫描。
                    entries.append({"display_name": display_name, "launch_id": display_name, "launch_kind": "uninstall_record", "source": "uninstall_registry", "installed_app_verified": True})  # 新增代码+WindowsAppInventory：保存设置页类产品记录作为低优先级辅助源；如果没有这一行，设置页来源无法参与融合。
        except OSError:  # 新增代码+WindowsAppInventory：忽略不存在或无权限根；如果没有这一行，普通用户权限可能让枚举失败。
            continue  # 新增代码+WindowsAppInventory：继续下一个根；如果没有这一行，单个根失败会停止全部枚举。
    return entries  # 新增代码+WindowsAppInventory：返回卸载注册表候选；如果没有这一行，调用方拿不到设置页辅助源。
# 新增代码+WindowsAppInventory：函数段结束，_inventory_discover_uninstall_registry 到此结束；如果没有这个边界说明，用户不容易看出设置页辅助源范围。


def discover_windows_app_inventory_sources() -> list[dict[str, Any]]:  # 新增代码+WindowsAppInventory：函数段开始，聚合真实 Windows 多源枚举；如果没有这段函数，调用方必须知道每个底层来源。
    entries: list[dict[str, Any]] = []  # 新增代码+WindowsAppInventory：准备聚合列表；如果没有这一行，多个来源无法合并。
    entries.extend(_inventory_discover_start_menu())  # 新增代码+WindowsAppInventory：加入开始菜单候选；如果没有这一行，可启动快捷方式来源会缺失。
    entries.extend(_inventory_discover_app_paths())  # 新增代码+WindowsAppInventory：加入 App Paths 候选；如果没有这一行，注册表启动别名会缺失。
    entries.extend(_inventory_discover_uninstall_registry())  # 新增代码+WindowsAppInventory：加入卸载注册表辅助候选；如果没有这一行，设置页类产品记录无法辅助补全。
    return entries  # 新增代码+WindowsAppInventory：返回聚合原始候选；如果没有这一行，调用方拿不到任何真实枚举结果。
# 新增代码+WindowsAppInventory：函数段结束，discover_windows_app_inventory_sources 到此结束；如果没有这个边界说明，用户不容易看出真实枚举入口。


__all__ = ["APP_INVENTORY_MAX_COUNT", "build_windows_app_inventory", "discover_windows_app_inventory_sources", "format_windows_app_inventory_for_model", "sanitize_inventory_display_name"]  # 新增代码+WindowsAppInventory：限定公开 API；如果没有这一行，通配导入会暴露内部 helper。
