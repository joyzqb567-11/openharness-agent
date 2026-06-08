"""Windows Computer Use 应用候选清单清洗模块。"""  # 新增代码+AppNames：说明本模块只负责枚举和清洗应用名；如果没有这一行，读者容易误以为这里会直接控制软件。
from __future__ import annotations  # 新增代码+AppNames：启用延迟类型注解；如果没有这一行，旧版运行环境解析复杂类型时更容易出问题。

import os  # 新增代码+AppNames：读取 Windows 开始菜单相关环境变量；如果没有这一行，真实机器枚举只能靠测试注入。
import unicodedata  # 新增代码+AppNames：判断 Unicode 字符类别；如果没有这一行，中文应用名和英文应用名无法用同一套安全规则清洗。
from pathlib import Path  # 新增代码+AppNames：用 Path 读取开始菜单快捷方式；如果没有这一行，Windows 路径拼接会更脆弱。
from typing import Any  # 新增代码+AppNames：描述 JSON 风格候选字典；如果没有这一行，接口含义对初学者不够清楚。

APP_CATALOG_MAX_COUNT = 50  # 新增代码+AppNames：限制最多交给模型 50 个应用候选；如果没有这一行，大量本机软件会撑爆 prompt 并分散模型注意力。
APP_NAME_MAX_CHARS = 40  # 新增代码+AppNames：限制单个应用显示名长度；如果没有这一行，异常长的快捷方式名可能污染模型上下文。
APP_NAME_ALLOWED_PUNCTUATION = set(" _.&'()+-")  # 新增代码+AppNames：允许常见应用名里的安全标点；如果没有这一行，Visual Studio Code 这类名字会被过度过滤。
APP_NAME_NOISE_TOKENS = ("helper", "agent", "service", "uninstaller", "uninstall", "updater", "update", "background", "runtime broker")  # 新增代码+AppNames：过滤后台组件和卸载器噪声；如果没有这一行，模型可能选择不能代表用户意图的后台程序。
APP_NAME_HIGH_RISK_TOKENS = ("powershell", "pwsh", "cmd", "terminal", "wt", "regedit", "registry", "control", "settings", "mmc", "taskmgr", "administrator", "credential", "password", "security", "firewall", "defender", "services")  # 新增代码+AppNames：过滤高风险系统工具；如果没有这一行，应用清单可能把终端或安全设置暴露成普通候选。
APP_NAME_COMMON_HINTS = (  # 新增代码+AppNames：公共安全别名表开始；如果没有这一行，常见系统应用在开始菜单枚举失败时缺少稳定启动提示。
    {"display_name": "Paint", "app_name": "mspaint", "executable": "mspaint.exe", "source": "common_system_hint", "aliases": ("画图", "画图软件", "paint", "mspaint", "mspaint.exe")},  # 新增代码+AppNames：提供 Paint 的稳定启动别名；如果没有这一行，中文“画图”可能继续被原样传给 launcher。
    {"display_name": "Notepad", "app_name": "notepad", "executable": "notepad.exe", "source": "common_system_hint", "aliases": ("记事本", "notepad", "notepad.exe")},  # 新增代码+AppNames：提供 Notepad 的稳定启动别名；如果没有这一行，中文“记事本”任务可能缺少规范 app_name。
    {"display_name": "Calculator", "app_name": "calc", "executable": "calc.exe", "source": "common_system_hint", "aliases": ("计算器", "calculator", "calc", "calc.exe")},  # 新增代码+AppNames：提供 Calculator 的稳定启动别名；如果没有这一行，计算器任务可能在中文名和 exe 名之间摇摆。
)  # 新增代码+AppNames：公共安全别名表结束；如果没有这一行，Python 语法不完整。


def _app_names_collapse_spaces(text: str) -> str:  # 新增代码+AppNames：函数段开始，压缩应用名里的连续空白；如果没有这段函数，候选去重和匹配会被多余空格干扰。
    return " ".join(str(text or "").strip().split())  # 新增代码+AppNames：返回压缩后的文本；如果没有这一行，`Visual   Studio` 和 `Visual Studio` 会被当成不同名字。
# 新增代码+AppNames：函数段结束，_app_names_collapse_spaces 到此结束；如果没有这个边界说明，用户不容易看出空白清洗范围。


def _app_names_executable_basename(value: Any) -> str:  # 新增代码+AppNames：函数段开始，把路径或名字转成 exe 基名；如果没有这段函数，模型提示可能泄露完整本机路径。
    text = str(value or "").strip().strip("\"'`")  # 新增代码+AppNames：去掉外层引号和空白；如果没有这一行，带引号路径会生成不稳定 app_name。
    if not text:  # 新增代码+AppNames：检查空输入；如果没有这一行，空字符串可能被补成 `.exe`。
        return ""  # 新增代码+AppNames：空输入返回空；如果没有这一行，调用方无法识别缺少可执行名。
    name = text.replace("\\", "/").rsplit("/", 1)[-1].strip()  # 新增代码+AppNames：只保留最后的文件名；如果没有这一行，C 盘用户名路径可能进入模型上下文。
    return name  # 新增代码+AppNames：返回基名；如果没有这一行，后续 app_name 无法生成。
# 新增代码+AppNames：函数段结束，_app_names_executable_basename 到此结束；如果没有这个边界说明，用户不容易看出路径脱敏范围。


def _app_names_app_name_from_executable(value: Any, fallback: str = "") -> str:  # 新增代码+AppNames：函数段开始，生成模型应传给 launch_app 的短 app_name；如果没有这段函数，模型仍会拿长显示名或中文名启动应用。
    name = _app_names_executable_basename(value)  # 新增代码+AppNames：先取可执行文件基名；如果没有这一行，完整路径可能影响 app_name。
    stem = name[:-4] if name.lower().endswith(".exe") else name  # 新增代码+AppNames：去掉 exe 后缀得到稳定短名；如果没有这一行，模型可能传 `mspaint.exe` 和 `mspaint` 两种形态。
    safe = _app_names_collapse_spaces(stem or fallback).lower()  # 新增代码+AppNames：压缩空白并转小写；如果没有这一行，大小写差异会破坏去重和匹配。
    return safe.replace(" ", "") if safe and all(ord(char) < 128 for char in safe) else safe  # 新增代码+AppNames：英文 app_name 去空格保持启动稳定；如果没有这一行，`visual studio code` 可能不能作为启动名。
# 新增代码+AppNames：函数段结束，_app_names_app_name_from_executable 到此结束；如果没有这个边界说明，用户不容易看出 app_name 生成范围。


def _app_names_has_only_safe_chars(text: str) -> bool:  # 新增代码+AppNames：函数段开始，检查显示名是否只包含安全字符；如果没有这段函数，换行和提示注入符号可能进入模型提示。
    if any(char in "\r\n\t<>`{}[]|;" for char in text):  # 新增代码+AppNames：拒绝明显危险或会破坏提示结构的字符；如果没有这一行，应用名可以伪造多行指令。
        return False  # 新增代码+AppNames：命中危险字符直接拒绝；如果没有这一行，后续格式化会把脏名字交给模型。
    for char in text:  # 新增代码+AppNames：逐字符检查 Unicode 类别；如果没有这一行，中文和英文无法兼容判断。
        category = unicodedata.category(char)  # 新增代码+AppNames：读取字符类别；如果没有这一行，无法区分文字数字和控制符。
        if category[0] in {"L", "N", "M"} or char in APP_NAME_ALLOWED_PUNCTUATION:  # 新增代码+AppNames：允许文字、数字、组合标记和安全标点；如果没有这一行，正常应用名会被误删。
            continue  # 新增代码+AppNames：安全字符继续检查下一个；如果没有这一行，循环无法表达通过逻辑。
        return False  # 新增代码+AppNames：遇到不安全字符拒绝；如果没有这一行，未知符号可能进入模型上下文。
    return True  # 新增代码+AppNames：所有字符安全才通过；如果没有这一行，安全应用名也会被误判失败。
# 新增代码+AppNames：函数段结束，_app_names_has_only_safe_chars 到此结束；如果没有这个边界说明，用户不容易看出字符安全范围。


def sanitize_app_display_name(raw: Any) -> str:  # 新增代码+AppNames：函数段开始，清洗人类可读应用名；如果没有这段函数，应用清单会把开始菜单原始名字直接交给模型。
    text = str(raw or "").strip().strip("\"'`")  # 新增代码+AppNames：去掉空白和外层引号；如果没有这一行，复制来的名字会产生重复候选。
    if any(char in "\r\n\t" for char in text):  # 新增代码+AppNames：拒绝多行或制表符名字；如果没有这一行，恶意快捷方式名可以注入额外提示。
        return ""  # 新增代码+AppNames：危险空白直接清空；如果没有这一行，脏名字可能继续进入候选。
    text = _app_names_collapse_spaces(text)  # 新增代码+AppNames：压缩普通空白；如果没有这一行，去重和格式化不稳定。
    if not text or len(text) > APP_NAME_MAX_CHARS:  # 新增代码+AppNames：拒绝空名字和过长名字；如果没有这一行，异常候选会污染 prompt。
        return ""  # 新增代码+AppNames：非法长度返回空；如果没有这一行，调用方无法统一过滤。
    if not _app_names_has_only_safe_chars(text):  # 新增代码+AppNames：执行安全字符检查；如果没有这一行，提示注入符号可能保留下来。
        return ""  # 新增代码+AppNames：不安全名字返回空；如果没有这一行，过滤层无法剔除危险名称。
    return text  # 新增代码+AppNames：返回清洗后的显示名；如果没有这一行，所有安全候选都会丢失。
# 新增代码+AppNames：函数段结束，sanitize_app_display_name 到此结束；如果没有这个边界说明，用户不容易看出显示名清洗范围。


def _app_names_contains_token(tokens: tuple[str, ...], *values: Any) -> bool:  # 新增代码+AppNames：函数段开始，统一检查风险或噪声关键词；如果没有这段函数，多个过滤点会重复写不一致逻辑。
    haystack = " ".join(str(value or "").lower() for value in values)  # 新增代码+AppNames：合并候选各字段为小写文本；如果没有这一行，只查显示名会漏掉 executable 风险。
    return any(token in haystack for token in tokens)  # 新增代码+AppNames：命中任意关键词即返回真；如果没有这一行，调用方无法快速判断候选类别。
# 新增代码+AppNames：函数段结束，_app_names_contains_token 到此结束；如果没有这个边界说明，用户不容易看出关键词检查范围。


def _app_names_candidate_from_mapping(candidate: dict[str, Any], default_source: str) -> dict[str, Any]:  # 新增代码+AppNames：函数段开始，把不同来源候选规范成统一字典；如果没有这段函数，开始菜单、注册表和测试注入会产生不同字段。
    display = sanitize_app_display_name(candidate.get("display_name") or candidate.get("name") or candidate.get("app_name") or candidate.get("executable"))  # 新增代码+AppNames：读取并清洗显示名；如果没有这一行，模型可见名称不受控。
    executable = _app_names_executable_basename(candidate.get("executable") or candidate.get("target") or candidate.get("path") or display)  # 新增代码+AppNames：读取可执行基名但不保留原始路径；如果没有这一行，启动名和脱敏都会缺失。
    app_name = str(candidate.get("app_name") or _app_names_app_name_from_executable(executable, fallback=display)).strip().lower()  # 新增代码+AppNames：生成稳定 app_name；如果没有这一行，模型不知道 launch_app 应传什么。
    source = str(candidate.get("source") or default_source).strip() or default_source  # 新增代码+AppNames：记录候选来源；如果没有这一行，模型和调试信息不知道候选来自哪里。
    aliases = tuple(str(alias).strip().lower() for alias in candidate.get("aliases", ()) if str(alias).strip())  # 新增代码+AppNames：保留可匹配别名但不直接展示为路径；如果没有这一行，中文提示无法解析到公共别名。
    return {"display_name": display, "app_name": app_name, "executable": executable, "source": source, "aliases": aliases, "installed_app_verified": bool(candidate.get("installed_app_verified", source not in {"common_system_hint", "generic_fallback"}))}  # 新增代码+AppNames：返回统一候选；如果没有这一行，后续过滤和格式化没有共同数据结构。
# 新增代码+AppNames：函数段结束，_app_names_candidate_from_mapping 到此结束；如果没有这个边界说明，用户不容易看出候选规范化范围。


def filter_apps_for_model_description(installed: Any, include_common: bool = True, max_count: int = APP_CATALOG_MAX_COUNT) -> list[dict[str, Any]]:  # 新增代码+AppNames：函数段开始，过滤并去重模型可见候选；如果没有这段函数，模型仍会面对原始混乱应用列表。
    raw_items = list(APP_NAME_COMMON_HINTS) if include_common else []  # 新增代码+AppNames：按需加入常见系统安全别名；如果没有这一行，Paint 等常用应用在枚举失败时没有候选。
    raw_items.extend(list(installed or []))  # 新增代码+AppNames：追加真实枚举或测试注入候选；如果没有这一行，清单不会包含用户安装的软件。
    filtered: list[dict[str, Any]] = []  # 新增代码+AppNames：准备过滤后的候选列表；如果没有这一行，函数无法累计结果。
    seen: set[str] = set()  # 新增代码+AppNames：准备去重集合；如果没有这一行，重复快捷方式会反复进入提示。
    for item in raw_items:  # 新增代码+AppNames：逐个处理候选；如果没有这一行，函数无法过滤列表内容。
        if not isinstance(item, dict):  # 新增代码+AppNames：防御非字典候选；如果没有这一行，坏输入会让清洗流程崩溃。
            continue  # 新增代码+AppNames：跳过非法候选；如果没有这一行，非字典输入无法安全忽略。
        entry = _app_names_candidate_from_mapping(item, "unknown")  # 新增代码+AppNames：规范化候选字段；如果没有这一行，过滤规则无法读取统一字段。
        if not entry["display_name"] or not entry["app_name"]:  # 新增代码+AppNames：拒绝缺少显示名或启动名的候选；如果没有这一行，模型会看到不可用项。
            continue  # 新增代码+AppNames：跳过不可用候选；如果没有这一行，空字段会进入格式化文本。
        if _app_names_contains_token(APP_NAME_HIGH_RISK_TOKENS, entry["display_name"], entry["app_name"], entry["executable"]):  # 新增代码+AppNames：过滤高风险系统工具；如果没有这一行，终端和安全工具可能暴露给模型。
            continue  # 新增代码+AppNames：跳过高风险候选；如果没有这一行，风险过滤没有实际效果。
        if _app_names_contains_token(APP_NAME_NOISE_TOKENS, entry["display_name"], entry["app_name"], entry["executable"]):  # 新增代码+AppNames：过滤 helper/updater/service 噪声；如果没有这一行，模型可能打开后台组件。
            continue  # 新增代码+AppNames：跳过噪声候选；如果没有这一行，噪声过滤没有实际效果。
        key = f"{entry['display_name'].casefold()}::{entry['app_name'].casefold()}"  # 新增代码+AppNames：生成去重键；如果没有这一行，重复快捷方式无法合并。
        if key in seen:  # 新增代码+AppNames：检查是否已见过；如果没有这一行，候选清单会重复。
            continue  # 新增代码+AppNames：跳过重复项；如果没有这一行，模型会看到重复选择。
        seen.add(key)  # 新增代码+AppNames：记录已保留候选；如果没有这一行，后续重复无法识别。
        filtered.append(entry)  # 新增代码+AppNames：保存安全候选；如果没有这一行，函数最终返回空。
        if len(filtered) >= max_count:  # 新增代码+AppNames：达到上限后停止；如果没有这一行，prompt 可能被大量软件清单撑大。
            break  # 新增代码+AppNames：退出循环；如果没有这一行，上限判断不会生效。
    return filtered  # 新增代码+AppNames：返回过滤后的候选；如果没有这一行，调用方拿不到结果。
# 新增代码+AppNames：函数段结束，filter_apps_for_model_description 到此结束；如果没有这个边界说明，用户不容易看出过滤范围。


def format_apps_for_model_description(apps: Any) -> str:  # 新增代码+AppNames：函数段开始，把候选清单压成模型可读提示；如果没有这段函数，主循环只能拿 Python 字典而不是稳定说明。
    entries = filter_apps_for_model_description(apps, include_common=False)  # 新增代码+AppNames：格式化前再次做安全过滤；如果没有这一行，外部直接传入脏数据时会绕过清洗。
    if not entries:  # 新增代码+AppNames：处理空候选清单；如果没有这一行，模型看不到“清单为空”的明确状态。
        return "Available desktop application candidates (cleaned model hints, not a hard whitelist): none."  # 新增代码+AppNames：返回空清单说明；如果没有这一行，空候选可能被误解为 bug。
    parts = [f"{entry['display_name']} [app_name={entry['app_name']}, source={entry['source']}]" for entry in entries]  # 新增代码+AppNames：生成不含原始路径的简洁候选片段；如果没有这一行，模型无法快速选择 app_name。
    return "Available desktop application candidates (cleaned model hints, not a hard whitelist): " + "; ".join(parts) + "."  # 新增代码+AppNames：返回单行模型提示；如果没有这一行，主循环无法获得清单文本。
# 新增代码+AppNames：函数段结束，format_apps_for_model_description 到此结束；如果没有这个边界说明，用户不容易看出模型提示格式范围。


def _app_names_start_menu_roots() -> list[Path]:  # 新增代码+AppNames：函数段开始，收集 Windows 开始菜单目录；如果没有这段函数，真实本机应用枚举缺少主要来源。
    roots: list[Path] = []  # 新增代码+AppNames：准备目录列表；如果没有这一行，函数无法累计路径。
    appdata = os.environ.get("APPDATA", "")  # 新增代码+AppNames：读取用户级 AppData；如果没有这一行，当前用户安装的快捷方式可能漏掉。
    program_data = os.environ.get("ProgramData", "")  # 新增代码+AppNames：读取全局 ProgramData；如果没有这一行，所有用户可见的快捷方式可能漏掉。
    if appdata:  # 新增代码+AppNames：只在环境变量存在时加入用户级目录；如果没有这一行，空路径会指向当前目录。
        roots.append(Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")  # 新增代码+AppNames：加入用户开始菜单；如果没有这一行，用户安装软件发现率下降。
    if program_data:  # 新增代码+AppNames：只在环境变量存在时加入全局目录；如果没有这一行，空路径会造成误扫。
        roots.append(Path(program_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs")  # 新增代码+AppNames：加入公共开始菜单；如果没有这一行，系统级普通应用发现率下降。
    return roots  # 新增代码+AppNames：返回目录列表；如果没有这一行，枚举函数没有输入。
# 新增代码+AppNames：函数段结束，_app_names_start_menu_roots 到此结束；如果没有这个边界说明，用户不容易看出目录来源范围。


def _app_names_discover_start_menu_entries(max_scan: int = 500) -> list[dict[str, Any]]:  # 新增代码+AppNames：函数段开始，只读枚举开始菜单快捷方式；如果没有这段函数，模型候选无法来自真实本机软件。
    entries: list[dict[str, Any]] = []  # 新增代码+AppNames：准备候选列表；如果没有这一行，扫描结果无法保存。
    scanned = 0  # 新增代码+AppNames：记录扫描数量；如果没有这一行，大目录上限无法执行。
    for root in _app_names_start_menu_roots():  # 新增代码+AppNames：遍历开始菜单目录；如果没有这一行，函数不会扫描任何来源。
        if not root.exists():  # 新增代码+AppNames：跳过不存在目录；如果没有这一行，某些 Windows 配置会抛路径错误。
            continue  # 新增代码+AppNames：继续下一个目录；如果没有这一行，不存在目录会中断枚举。
        for shortcut in root.rglob("*"):  # 新增代码+AppNames：递归读取快捷方式；如果没有这一行，子文件夹应用不会被发现。
            if scanned >= max_scan:  # 新增代码+AppNames：检查扫描上限；如果没有这一行，异常大目录会拖慢 agent。
                return entries  # 新增代码+AppNames：达到上限返回已有候选；如果没有这一行，上限不会停止扫描。
            scanned += 1  # 新增代码+AppNames：累计扫描数量；如果没有这一行，上限判断不会推进。
            if shortcut.suffix.lower() not in {".lnk", ".appref-ms"}:  # 新增代码+AppNames：只收快捷方式；如果没有这一行，普通文档可能被当成应用。
                continue  # 新增代码+AppNames：跳过非快捷方式；如果没有这一行，清单噪声会增多。
            entries.append({"display_name": shortcut.stem, "executable": shortcut.stem, "source": "start_menu", "installed_app_verified": True})  # 新增代码+AppNames：保存脱敏候选，不读取或暴露快捷方式路径；如果没有这一行，开始菜单发现结果不会进入清单。
    return entries  # 新增代码+AppNames：返回开始菜单候选；如果没有这一行，调用方拿不到枚举结果。
# 新增代码+AppNames：函数段结束，_app_names_discover_start_menu_entries 到此结束；如果没有这个边界说明，用户不容易看出开始菜单枚举范围。


def _app_names_discover_app_paths_registry() -> list[dict[str, Any]]:  # 新增代码+AppNames：函数段开始，只读枚举 App Paths 注册表；如果没有这段函数，一些不在开始菜单里的普通应用会漏掉。
    try:  # 新增代码+AppNames：尝试导入 Windows 注册表模块；如果没有这一行，非 Windows 环境会直接崩溃。
        import winreg  # type: ignore  # 新增代码+AppNames：导入 winreg 只读注册表；如果没有这一行，无法读取 App Paths。
    except (ImportError, ModuleNotFoundError):  # 新增代码+AppNames：兼容非 Windows 或精简 Python；如果没有这一行，自动化测试在非 Windows 会失败。
        return []  # 新增代码+AppNames：不可用时返回空；如果没有这一行，枚举会中断主流程。
    entries: list[dict[str, Any]] = []  # 新增代码+AppNames：准备注册表候选列表；如果没有这一行，扫描结果无法保存。
    roots = ((winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths"), (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths"))  # 新增代码+AppNames：定义两个 App Paths 来源；如果没有这一行，只能发现单个注册表范围。
    for hive, subkey in roots:  # 新增代码+AppNames：遍历注册表根；如果没有这一行，函数不会读取任何 App Paths。
        try:  # 新增代码+AppNames：打开注册表路径；如果没有这一行，缺少路径会抛异常中断。
            with winreg.OpenKey(hive, subkey) as key:  # 新增代码+AppNames：只读打开 App Paths；如果没有这一行，无法枚举子项。
                index = 0  # 新增代码+AppNames：初始化子项索引；如果没有这一行，枚举循环没有起点。
                while index < 500:  # 新增代码+AppNames：限制最多读 500 项；如果没有这一行，异常注册表可能拖慢启动。
                    try:  # 新增代码+AppNames：读取单个子项名；如果没有这一行，枚举结束异常无法处理。
                        name = winreg.EnumKey(key, index)  # 新增代码+AppNames：读取 exe 子项名；如果没有这一行，注册表候选没有名称。
                    except OSError:  # 新增代码+AppNames：枚举结束时退出；如果没有这一行，结束会变成错误。
                        break  # 新增代码+AppNames：停止当前注册表根扫描；如果没有这一行，循环无法结束。
                    entries.append({"display_name": Path(name).stem, "executable": name, "source": "app_paths_registry", "installed_app_verified": True})  # 新增代码+AppNames：保存注册表候选但不读取完整路径；如果没有这一行，App Paths 信息不会进入候选清单。
                    index += 1  # 新增代码+AppNames：推进索引；如果没有这一行，循环会卡在同一个子项。
        except OSError:  # 新增代码+AppNames：忽略不存在或无权限读取的注册表根；如果没有这一行，普通用户权限可能让枚举失败。
            continue  # 新增代码+AppNames：继续下一个注册表根；如果没有这一行，单个根失败会停止整个发现。
    return entries  # 新增代码+AppNames：返回注册表候选；如果没有这一行，调用方拿不到结果。
# 新增代码+AppNames：函数段结束，_app_names_discover_app_paths_registry 到此结束；如果没有这个边界说明，用户不容易看出注册表只读枚举范围。


def discover_windows_app_catalog(candidates: list[dict[str, Any]] | None = None, include_common: bool = True, max_count: int = APP_CATALOG_MAX_COUNT) -> list[dict[str, Any]]:  # 新增代码+AppNames：函数段开始，生成清洗后的本机应用候选清单；如果没有这段函数，主循环只能靠猜应用名。
    if candidates is not None:  # 新增代码+AppNames：优先使用测试或上层注入候选；如果没有这一行，测试无法稳定模拟本机应用。
        return filter_apps_for_model_description(candidates, include_common=include_common, max_count=max_count)  # 新增代码+AppNames：过滤注入候选并返回；如果没有这一行，注入路径不会经过同一清洗规则。
    discovered = _app_names_discover_start_menu_entries()  # 新增代码+AppNames：读取开始菜单候选；如果没有这一行，真实本机软件发现来源不足。
    discovered.extend(_app_names_discover_app_paths_registry())  # 新增代码+AppNames：追加 App Paths 注册表候选；如果没有这一行，部分应用无法被发现。
    return filter_apps_for_model_description(discovered, include_common=include_common, max_count=max_count)  # 新增代码+AppNames：统一清洗过滤并返回；如果没有这一行，枚举结果可能包含脏名称和风险项。
# 新增代码+AppNames：函数段结束，discover_windows_app_catalog 到此结束；如果没有这个边界说明，用户不容易看出应用清单生成范围。


def resolve_app_name_hint(target_app_hint: Any, catalog: list[dict[str, Any]] | None = None) -> str:  # 新增代码+AppNames：函数段开始，把用户友好应用提示解析成 app_name；如果没有这段函数，agent.py 会继续维护硬编码别名表。
    query = _app_names_collapse_spaces(str(target_app_hint or "")).lower()  # 新增代码+AppNames：规范化查询文本；如果没有这一行，中文和英文别名匹配会不稳定。
    if not query:  # 新增代码+AppNames：空提示直接返回空；如果没有这一行，空值可能误命中公共候选。
        return ""  # 新增代码+AppNames：返回空 app_name；如果没有这一行，调用方无法判断没有目标应用。
    entries = catalog if catalog is not None else discover_windows_app_catalog(include_common=True)  # 新增代码+AppNames：读取传入或实时清单；如果没有这一行，解析只能靠静态表。
    for entry in entries:  # 新增代码+AppNames：遍历候选；如果没有这一行，函数无法匹配任何应用。
        aliases = set(entry.get("aliases", ()))  # 新增代码+AppNames：读取候选别名集合；如果没有这一行，中文“画图”等别名无法命中。
        aliases.add(str(entry.get("display_name", "")).lower())  # 新增代码+AppNames：把显示名加入匹配范围；如果没有这一行，用户输入应用显示名可能无法解析。
        aliases.add(str(entry.get("app_name", "")).lower())  # 新增代码+AppNames：把 app_name 加入匹配范围；如果没有这一行，mspaint 这类短名无法命中。
        aliases.add(str(entry.get("executable", "")).lower())  # 新增代码+AppNames：把 executable 加入匹配范围；如果没有这一行，mspaint.exe 这类形式无法命中。
        if query in aliases:  # 新增代码+AppNames：检查精确别名命中；如果没有这一行，解析结果永远为空。
            return str(entry.get("app_name", "") or "").strip()  # 新增代码+AppNames：返回稳定 app_name；如果没有这一行，调用方拿不到启动名。
    return ""  # 新增代码+AppNames：未命中返回空；如果没有这一行，调用方可能误用最后一个候选。
# 新增代码+AppNames：函数段结束，resolve_app_name_hint 到此结束；如果没有这个边界说明，用户不容易看出别名解析范围。


__all__ = ["APP_CATALOG_MAX_COUNT", "discover_windows_app_catalog", "filter_apps_for_model_description", "format_apps_for_model_description", "resolve_app_name_hint", "sanitize_app_display_name"]  # 新增代码+AppNames：限定公开 API；如果没有这一行，通配导入会暴露内部 helper。
