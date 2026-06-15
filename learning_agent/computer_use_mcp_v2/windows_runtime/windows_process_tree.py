"""Windows 启动器进程到真实应用窗口的通用绑定 helper。"""  # 新增代码+ExternalAppWindowBinding：说明本模块处理 .lnk 启动器、多进程应用和真实窗口 pid 不同的问题；如果没有这一行，读者不知道网易云音乐这类问题的入口在哪里。
from __future__ import annotations  # 新增代码+ExternalAppWindowBinding：启用延迟类型解析；如果没有这一行，未来前向类型标注可能在运行时报错。

import re  # 新增代码+ExternalAppWindowBinding：导入正则用于清洗 exe、lnk 和标题文本；如果没有这一行，别名归一化只能靠脆弱字符串替换。
from typing import Any  # 新增代码+ExternalAppWindowBinding：导入 Any 描述 Windows 窗口和启动报告的动态字典；如果没有这一行，helper 签名可读性较差。


KNOWN_WINDOWS_LAUNCH_SUFFIXES = (".exe", ".lnk", ".appref-ms", ".url")  # 新增代码+ExternalAppWindowBinding：列出常见启动器和可执行文件后缀；如果没有这一行，网易云音乐.lnk 不能归一成网易云音乐。


def _safe_binding_text(value: Any) -> str:  # 新增代码+ExternalAppWindowBinding：函数段开始，把动态字段清洗成单行文本；如果没有这段函数，None 或换行会污染匹配逻辑。
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+ExternalAppWindowBinding：返回去掉换行的短文本；如果没有这一行，窗口标题里的换行可能破坏别名判断。
# 新增代码+ExternalAppWindowBinding：函数段结束，_safe_binding_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清洗范围。


def _basename_without_path(value: Any) -> str:  # 新增代码+ExternalAppWindowBinding：函数段开始，从路径或快捷方式名里取最后一段；如果没有这段函数，完整路径会干扰窗口标题匹配。
    text = _safe_binding_text(value)  # 新增代码+ExternalAppWindowBinding：先统一清洗输入文本；如果没有这一行，None 路径会导致后续处理不稳定。
    parts = re.split(r"[\\/]+", text)  # 新增代码+ExternalAppWindowBinding：同时按反斜杠和斜杠拆分路径；如果没有这一行，Windows 路径无法取文件名。
    return parts[-1].strip() if parts else text  # 新增代码+ExternalAppWindowBinding：返回最后一段文件名；如果没有这一行，别名可能包含 C:\Program Files 之类噪声。
# 新增代码+ExternalAppWindowBinding：函数段结束，_basename_without_path 到此结束；如果没有这个边界说明，初学者不容易看出路径裁剪范围。


def strip_windows_launch_suffix(value: Any) -> str:  # 新增代码+ExternalAppWindowBinding：函数段开始，去掉 exe/lnk 等启动后缀；如果没有这段函数，快捷方式名和真实窗口标题无法稳定匹配。
    text = _basename_without_path(value)  # 新增代码+ExternalAppWindowBinding：先取文件名避免后缀清理影响目录；如果没有这一行，目录名里带点号会被误处理。
    lowered = text.casefold()  # 新增代码+ExternalAppWindowBinding：生成小写版本用于不区分大小写比较；如果没有这一行，EXE/LNK 大小写会影响匹配。
    for suffix in KNOWN_WINDOWS_LAUNCH_SUFFIXES:  # 新增代码+ExternalAppWindowBinding：遍历所有已知后缀；如果没有这一行，只能处理单一种后缀。
        if lowered.endswith(suffix):  # 新增代码+ExternalAppWindowBinding：判断文件名是否带该后缀；如果没有这一行，后缀清理会盲目截断。
            return text[: -len(suffix)].strip()  # 新增代码+ExternalAppWindowBinding：返回去掉后缀的名称；如果没有这一行，网易云音乐.lnk 无法变成网易云音乐。
    return text  # 新增代码+ExternalAppWindowBinding：没有已知后缀时保持原文本；如果没有这一行，无后缀应用名会隐式返回 None。
# 新增代码+ExternalAppWindowBinding：函数段结束，strip_windows_launch_suffix 到此结束；如果没有这个边界说明，初学者不容易看出后缀处理范围。


def normalize_process_target_text(value: Any) -> str:  # 新增代码+ExternalAppWindowBinding：函数段开始，生成用于窗口匹配的轻量归一化文本；如果没有这段函数，中文标题、空格和后缀差异会让匹配失败。
    text = strip_windows_launch_suffix(value).casefold()  # 新增代码+ExternalAppWindowBinding：去掉启动后缀并转小写；如果没有这一行，.lnk 和 .exe 差异会继续影响判断。
    return re.sub(r"[\s_\-\.]+", "", text)  # 新增代码+ExternalAppWindowBinding：去掉常见分隔符保留中英文主体；如果没有这一行，Netease Cloud Music 和 neteasecloudmusic 可能不匹配。
# 新增代码+ExternalAppWindowBinding：函数段结束，normalize_process_target_text 到此结束；如果没有这个边界说明，初学者不容易看出归一化范围。


def build_process_window_aliases(target_hint: Any, launch_result: dict[str, Any]) -> list[str]:  # 新增代码+ExternalAppWindowBinding：函数段开始，基于目标名和启动结果生成窗口别名；如果没有这段函数，多进程应用只能靠单一 target_hint 猜。
    raw_candidates = [  # 新增代码+ExternalAppWindowBinding：准备所有可能代表应用身份的原始字段；如果没有这一行，别名来源会分散在调用方。
        target_hint,  # 新增代码+ExternalAppWindowBinding：加入用户或 resolver 的规范目标名；如果没有这一行，英文目标无法参与匹配。
        launch_result.get("process_executable"),  # 新增代码+ExternalAppWindowBinding：加入启动器或可执行文件名；如果没有这一行，网易云音乐.lnk 的中文名会丢失。
        launch_result.get("process_name"),  # 新增代码+ExternalAppWindowBinding：加入启动报告里的进程名；如果没有这一行，后端返回 process_name 时无法复用。
        launch_result.get("display_name"),  # 新增代码+ExternalAppWindowBinding：加入显示名；如果没有这一行，开始菜单应用名无法参与匹配。
        launch_result.get("best_candidate_display_name"),  # 新增代码+ExternalAppWindowBinding：加入发现阶段最佳候选显示名；如果没有这一行，Phase108 的中文名证据可能丢失。
        launch_result.get("best_candidate_executable"),  # 新增代码+ExternalAppWindowBinding：加入发现阶段最佳候选 exe；如果没有这一行，resolver 证据无法参与真实窗口绑定。
    ]  # 新增代码+ExternalAppWindowBinding：结束原始候选列表；如果没有这一行，Python 列表语法不完整。
    aliases: list[str] = []  # 新增代码+ExternalAppWindowBinding：准备去重后的别名列表；如果没有这一行，后续无法稳定追加结果。
    for raw_candidate in raw_candidates:  # 新增代码+ExternalAppWindowBinding：遍历所有可能身份字段；如果没有这一行，只会处理第一个字段。
        for candidate in (_safe_binding_text(raw_candidate), strip_windows_launch_suffix(raw_candidate)):  # 新增代码+ExternalAppWindowBinding：同时保留原名和去后缀名；如果没有这一行，标题带后缀或不带后缀的场景只能命中一种。
            alias = normalize_process_target_text(candidate)  # 新增代码+ExternalAppWindowBinding：把候选变成可比较别名；如果没有这一行，大小写和分隔符差异会影响匹配。
            if len(alias) >= 2 and alias not in aliases:  # 新增代码+ExternalAppWindowBinding：过滤太短别名并去重；如果没有这一行，单字符别名可能误绑定其他窗口。
                aliases.append(alias)  # 新增代码+ExternalAppWindowBinding：保存有效别名；如果没有这一行，匹配函数拿不到任何候选。
    return aliases  # 新增代码+ExternalAppWindowBinding：返回稳定别名列表；如果没有这一行，调用方无法执行窗口匹配。
# 新增代码+ExternalAppWindowBinding：函数段结束，build_process_window_aliases 到此结束；如果没有这个边界说明，初学者不容易看出别名生成范围。


def window_matches_process_alias(window: dict[str, Any], aliases: list[str]) -> bool:  # 新增代码+ExternalAppWindowBinding：函数段开始，判断窗口标题或进程字段是否命中别名；如果没有这段函数，真实窗口 pid 不同就无法通用绑定。
    if not aliases:  # 新增代码+ExternalAppWindowBinding：没有别名时不能匹配任何窗口；如果没有这一行，空别名可能导致误绑定。
        return False  # 新增代码+ExternalAppWindowBinding：返回不匹配；如果没有这一行，安全边界会过宽。
    if int(window.get("hwnd", 0) or 0) <= 0:  # 新增代码+ExternalAppWindowBinding：必须有真实窗口句柄才允许匹配；如果没有这一行，后台进程可能被当成可操作窗口。
        return False  # 新增代码+ExternalAppWindowBinding：无 hwnd 时拒绝匹配；如果没有这一行，代理绑定缺少真实控制对象。
    text_sources = [window.get("title_preview"), window.get("title"), window.get("process_name"), window.get("app_id"), window.get("class_name")]  # 新增代码+ExternalAppWindowBinding：收集窗口可读文本字段；如果没有这一行，窗口标题和进程名无法一起参与判断。
    normalized_texts = [normalize_process_target_text(text) for text in text_sources if _safe_binding_text(text)]  # 新增代码+ExternalAppWindowBinding：归一化窗口文本并过滤空值；如果没有这一行，None 字段会污染匹配。
    return any(alias in text or text in alias for alias in aliases for text in normalized_texts if text)  # 新增代码+ExternalAppWindowBinding：只要别名和窗口文本互相包含就认为命中；如果没有这一行，中文标题“网易云音乐”和快捷方式“网易云音乐.lnk”不会绑定。
# 新增代码+ExternalAppWindowBinding：函数段结束，window_matches_process_alias 到此结束；如果没有这个边界说明，初学者不容易看出窗口匹配范围。


def build_proxy_window_binding_report(window: dict[str, Any], launch_result: dict[str, Any], process_id: int, reason: str = "alias_match") -> dict[str, Any]:  # 新增代码+ExternalAppWindowBinding：函数段开始，生成代理窗口绑定审计报告；如果没有这段函数，网易云音乐窗口绑定后仍缺少可解释证据。
    window_pid = int(window.get("pid", window.get("window_process_id", 0)) or 0)  # 新增代码+ExternalAppWindowBinding：读取真实窗口 pid；如果没有这一行，报告看不到真实窗口属于哪个进程。
    window_hwnd = int(window.get("hwnd", 0) or 0)  # 新增代码+ExternalAppWindowBinding：读取真实窗口句柄；如果没有这一行，报告无法证明绑定到可见窗口。
    return {  # 新增代码+ExternalAppWindowBinding：返回统一审计字段；如果没有这一行，controller 和测试无法读取绑定详情。
        "proxy_window_bound": True,  # 新增代码+ExternalAppWindowBinding：明确这是代理窗口绑定；如果没有这一行，验收无法区分 pid 精确绑定和代理绑定。
        "binding_reason": str(reason or "alias_match"),  # 新增代码+ExternalAppWindowBinding：记录绑定原因；如果没有这一行，复盘时不知道为什么允许 pid 不同。
        "confidence": "medium",  # 新增代码+ExternalAppWindowBinding：记录保守置信度；如果没有这一行，用户无法理解这不是凭空接管任意窗口。
        "launcher_pid": int(process_id or 0),  # 新增代码+ExternalAppWindowBinding：记录 agent 启动器 pid；如果没有这一行，无法追溯启动链。
        "launcher_executable": str(launch_result.get("process_executable", "") or ""),  # 新增代码+ExternalAppWindowBinding：记录启动器名称；如果没有这一行，.lnk 代理事实不可见。
        "window_pid": window_pid,  # 新增代码+ExternalAppWindowBinding：记录真实窗口 pid；如果没有这一行，多进程差异不可审计。
        "window_hwnd": window_hwnd,  # 新增代码+ExternalAppWindowBinding：记录真实窗口句柄；如果没有这一行，后续无法核对目标窗口。
        "window_title": _safe_binding_text(window.get("title_preview") or window.get("title")),  # 新增代码+ExternalAppWindowBinding：记录窗口标题摘要；如果没有这一行，用户看不到绑定的是哪个窗口。
        "window_process_name": _safe_binding_text(window.get("process_name")),  # 新增代码+ExternalAppWindowBinding：记录真实窗口进程名；如果没有这一行，报告无法解释 pid 对应程序。
    }  # 新增代码+ExternalAppWindowBinding：结束审计报告字典；如果没有这一行，Python 字典语法不完整。
# 新增代码+ExternalAppWindowBinding：函数段结束，build_proxy_window_binding_report 到此结束；如果没有这个边界说明，初学者不容易看出审计字段范围。


__all__ = ["build_process_window_aliases", "build_proxy_window_binding_report", "normalize_process_target_text", "strip_windows_launch_suffix", "window_matches_process_alias"]  # 新增代码+ExternalAppWindowBinding：限定公开导出；如果没有这一行，外部可能误用内部清洗 helper。
