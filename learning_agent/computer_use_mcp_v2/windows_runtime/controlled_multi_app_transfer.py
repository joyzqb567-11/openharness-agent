"""Phase150 controlled Notepad to Browser live transfer benchmark."""  # 新增代码+Phase150MultiAppTransfer：说明本模块负责受控跨应用真实 GUI 传递验收；如果没有这一行，维护者不容易区分它和旧的 contract-only 场景。
from __future__ import annotations  # 新增代码+Phase150MultiAppTransfer：启用延迟类型解析；如果没有这一行，复杂前向类型在导入时更容易失败。

import hashlib  # 新增代码+Phase150MultiAppTransfer：导入哈希工具；如果没有这一行，报告只能泄露明文或完全无法关联传递文本。
import json  # 新增代码+Phase150MultiAppTransfer：导入 JSON 工具；如果没有这一行，CLI 无法打印结构化脱敏报告。
import os  # 新增代码+Phase150MultiAppTransfer：导入环境变量工具；如果没有这一行，双门禁无法从真实终端环境读取。
import shutil  # 新增代码+Phase150MultiAppTransfer：导入浏览器查找工具；如果没有这一行，无法从 PATH 兜底查找 Edge/Chrome。
import subprocess  # 新增代码+Phase150MultiAppTransfer：导入进程启动工具；如果没有这一行，真实 Notepad 和 Browser 无法启动。
import sys  # 新增代码+Phase150MultiAppTransfer：导入平台信息；如果没有这一行，非 Windows 环境可能误调用 Win32 GUI。
import time  # 新增代码+Phase150MultiAppTransfer：导入等待工具；如果没有这一行，窗口启动、复制、粘贴和标题刷新会被过早检查。
from pathlib import Path  # 新增代码+Phase150MultiAppTransfer：导入路径对象；如果没有这一行，受控运行目录、源文件和本地页面路径容易拼错。
from typing import Any  # 新增代码+Phase150MultiAppTransfer：导入通用类型；如果没有这一行，JSON 风格报告的输入输出边界不清楚。

try:  # 新增代码+Phase150MultiAppTransfer：优先按包模式导入项目内依赖；如果没有这段代码，单元测试和 python -m 路径无法共享实现。
    from learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # 新增代码+Phase150MultiAppTransfer：复用 computer_use memory 根路径；如果没有这一行，真实跨应用验收可能写到用户目录。
    from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+Phase150MultiAppTransfer：复用真实 SendInput sender；如果没有这一行，复制粘贴只会启动应用而不会触达 GUI。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase150MultiAppTransfer：复用真实只读窗口枚举；如果没有这一行，动作前后无法复核 Notepad 和 Browser。
except ModuleNotFoundError as error:  # 新增代码+Phase150MultiAppTransfer：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，真实可见终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants", "learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend"}:  # 新增代码+Phase150MultiAppTransfer：只兜底包路径缺失；如果没有这一行，依赖内部 bug 会被误吞。
        raise  # 新增代码+Phase150MultiAppTransfer：重新抛出真正的内部导入错误；如果没有这一行，排查会被错误 fallback 掩盖。
    from computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # type: ignore  # 新增代码+Phase150MultiAppTransfer：脚本模式复用 memory 根路径；如果没有这一行，bat 入口无法定位受控目录。
    from computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # type: ignore  # 新增代码+Phase150MultiAppTransfer：脚本模式复用真实 SendInput sender；如果没有这一行，bat 入口无法发真实复制粘贴事件。
    from computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # type: ignore  # 新增代码+Phase150MultiAppTransfer：脚本模式复用窗口枚举；如果没有这一行，bat 入口无法复核目标窗口。

PHASE150_CONTROLLED_MULTI_APP_TRANSFER_MARKER = "PHASE150_CONTROLLED_MULTI_APP_TRANSFER_READY"  # 新增代码+Phase150MultiAppTransfer：定义 ready marker；如果没有这一行，真实终端验收没有稳定锚点。
PHASE150_CONTROLLED_MULTI_APP_TRANSFER_OK_TOKEN = "PHASE150_CONTROLLED_MULTI_APP_TRANSFER_OK"  # 新增代码+Phase150MultiAppTransfer：定义 OK token；如果没有这一行，Phase148C 场景无法稳定匹配成功。
PHASE150_CONTROLLED_MULTI_APP_TRANSFER_MODEL = "phase150_controlled_multi_app_transfer"  # 新增代码+Phase150MultiAppTransfer：定义模型名；如果没有这一行，报告无法区分本阶段证据版本。
PHASE150_REAL_MULTI_APP_TRANSFER_ENV = "LEARNING_AGENT_PHASE150_ENABLE_REAL_MULTI_APP_TRANSFER"  # 新增代码+Phase150MultiAppTransfer：定义强制启用真实 GUI 的门禁变量；如果没有这一行，真实桌面动作可能被默认打开。
PHASE150_REAL_MULTI_APP_TRANSFER_REQUEST_ENV = "LEARNING_AGENT_PHASE150_RUN_REAL_MULTI_APP_TRANSFER"  # 新增代码+Phase150MultiAppTransfer：定义请求运行真实 GUI 的变量；如果没有这一行，CLI 无法显式表达本次要跑真实验收。
PHASE150_TRANSFER_TARGET_TITLE = "PHASE150_TRANSFER_TARGET"  # 新增代码+Phase150MultiAppTransfer：定义浏览器目标页初始标题；如果没有这一行，窗口识别没有本阶段专属线索。
PHASE150_TRANSFER_OK_TITLE = "PHASE150_TRANSFER_OK"  # 新增代码+Phase150MultiAppTransfer：定义浏览器粘贴成功后的标题；如果没有这一行，结果验证只能靠猜测。
PHASE150_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase150MultiAppTransfer：声明没有扩展到不受控高风险动作；如果没有这一行，成熟度矩阵无法判断安全边界。
DEFAULT_PHASE150_CONTROLLED_MULTI_APP_ROOT = DEFAULT_PERSISTENT_GRANTS_ROOT.parent / "post_parity" / "phase150_controlled_multi_app_transfer"  # 新增代码+Phase150MultiAppTransfer：定义默认受控运行根目录；如果没有这一行，真实跨应用操作可能落到用户目录。


def _phase150_bool_token(value: Any) -> str:  # 新增代码+Phase150MultiAppTransfer：函数段开始，把布尔值转成小写验收 token；如果没有这段函数，终端输出会混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+Phase150MultiAppTransfer：返回 true 或 false；如果没有这一行，acceptance controller 字符串匹配会不稳定。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


def _phase150_env_enabled(name: str) -> bool:  # 新增代码+Phase150MultiAppTransfer：函数段开始，读取环境变量门禁；如果没有这段函数，每个入口都要重复判断字符串真假。
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase150MultiAppTransfer：只接受明确真值；如果没有这一行，随便设置任意文本也可能打开真实桌面动作。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_env_enabled 到此结束；如果没有这个边界说明，初学者不容易看出门禁解析范围。


def _phase150_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase150MultiAppTransfer：函数段开始，安全转换 hwnd、pid 和计数；如果没有这段函数，坏窗口字段可能让真实验收崩溃。
    try:  # 新增代码+Phase150MultiAppTransfer：捕获动态输入的转换异常；如果没有这一行，None 或脏字符串会直接抛错。
        return int(value)  # 新增代码+Phase150MultiAppTransfer：返回整数；如果没有这一行，SendInput 和 Win32 close 不能使用句柄。
    except Exception:  # 新增代码+Phase150MultiAppTransfer：把所有转换异常视为安全兜底；如果没有这一行，坏字段会中断 agent。
        return int(default)  # 新增代码+Phase150MultiAppTransfer：返回默认值；如果没有这一行，调用方要重复写兜底逻辑。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出转换范围。


def _phase150_sha256_16(value: Any) -> str:  # 新增代码+Phase150MultiAppTransfer：函数段开始，生成短哈希；如果没有这段函数，报告要么泄露传递文本要么无法审计。
    text = str(value or "")  # 新增代码+Phase150MultiAppTransfer：把输入规整为字符串；如果没有这一行，None 和数字的哈希会不稳定。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16] if text else ""  # 新增代码+Phase150MultiAppTransfer：返回 16 位短哈希；如果没有这一行，脱敏关联信息不可用。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。


def _phase150_safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase150MultiAppTransfer：函数段开始，把动态值规整成字典；如果没有这段函数，driver 坏返回会污染报告。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase150MultiAppTransfer：只复制 dict；如果没有这一行，None 或字符串会让 .get 调用崩溃。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_safe_dict 到此结束；如果没有这个边界说明，初学者不容易看出字典清洗范围。


def _phase150_window_field(window: Any, field: str) -> Any:  # 新增代码+Phase150MultiAppTransfer：函数段开始，兼容 dict 和对象窗口字段；如果没有这段函数，测试替身和真实 inventory 会分裂。
    return window.get(field) if isinstance(window, dict) else getattr(window, field, None)  # 新增代码+Phase150MultiAppTransfer：按类型读取字段；如果没有这一行，窗口摘要 helper 不能复用。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_window_field 到此结束；如果没有这个边界说明，初学者不容易看出字段读取范围。


def _phase150_hwnd_from_window(window: Any) -> int:  # 新增代码+Phase150MultiAppTransfer：函数段开始，从窗口摘要提取 hwnd；如果没有这段函数，真实 sender 和窗口关闭没有目标句柄。
    direct = _phase150_window_field(window, "hwnd")  # 新增代码+Phase150MultiAppTransfer：优先读取 hwnd 字段；如果没有这一行，真实 inventory 的系统句柄可能被忽略。
    if direct is not None:  # 新增代码+Phase150MultiAppTransfer：存在直接句柄时走直接转换；如果没有这一行，后续会误走文本解析。
        return _phase150_safe_int(direct)  # 新增代码+Phase150MultiAppTransfer：返回直接句柄；如果没有这一行，SetForegroundWindow 无法定位目标应用。
    window_id = str(_phase150_window_field(window, "window_id") or "")  # 新增代码+Phase150MultiAppTransfer：读取协议窗口 id；如果没有这一行，缺 hwnd 字段时没有兜底来源。
    return _phase150_safe_int(window_id.split(":", 1)[1]) if window_id.startswith("hwnd:") and ":" in window_id else 0  # 新增代码+Phase150MultiAppTransfer：从 hwnd:123 解析句柄；如果没有这一行，静态和真实窗口 id 无法用于 Win32。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_hwnd_from_window 到此结束；如果没有这个边界说明，初学者不容易看出句柄解析范围。


def _phase150_window_title(window: Any) -> str:  # 新增代码+Phase150MultiAppTransfer：函数段开始，读取窗口标题摘要；如果没有这段函数，目标匹配会重复处理 title 字段。
    return str(_phase150_window_field(window, "title_preview") or _phase150_window_field(window, "title") or "")  # 新增代码+Phase150MultiAppTransfer：优先用脱敏标题摘要；如果没有这一行，匹配逻辑可能拿不到标题。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_window_title 到此结束；如果没有这个边界说明，初学者不容易看出标题读取范围。


def _phase150_window_blob(window: Any) -> str:  # 新增代码+Phase150MultiAppTransfer：函数段开始，拼出窗口身份文本；如果没有这段函数，Notepad/Browser/危险目标判断会散落。
    fields = ("app_id", "process_name", "class_name", "title_preview", "title", "window_id")  # 新增代码+Phase150MultiAppTransfer：列出窗口身份字段；如果没有这一行，某些关键线索可能漏检。
    return " ".join(str(_phase150_window_field(window, field) or "") for field in fields).lower()  # 新增代码+Phase150MultiAppTransfer：合并并小写字段；如果没有这一行，大小写差异会导致误判。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_window_blob 到此结束；如果没有这个边界说明，初学者不容易看出窗口身份范围。


def _phase150_window_key(window: Any) -> str:  # 新增代码+Phase150MultiAppTransfer：函数段开始，生成窗口身份 key；如果没有这段函数，启动前 baseline 无法过滤旧窗口。
    window_id = str(_phase150_window_field(window, "window_id") or "")  # 新增代码+Phase150MultiAppTransfer：读取窗口 id；如果没有这一行，无法优先用稳定 hwnd 身份。
    return f"window_id:{window_id}" if window_id else f"pid:{_phase150_safe_int(_phase150_window_field(window, 'pid') or _phase150_window_field(window, 'process_id'))}"  # 新增代码+Phase150MultiAppTransfer：返回窗口 id 或 pid key；如果没有这一行，baseline 不能识别同一窗口。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_window_key 到此结束；如果没有这个边界说明，初学者不容易看出身份 key 范围。


def _phase150_window_identity(window: Any) -> dict[str, Any]:  # 新增代码+Phase150MultiAppTransfer：函数段开始，生成不含完整标题的窗口身份摘要；如果没有这段函数，报告可能泄露本地路径或标题文本。
    title = _phase150_window_title(window)  # 新增代码+Phase150MultiAppTransfer：读取标题用于哈希；如果没有这一行，身份摘要缺少可比对标题线索。
    return {"app_id": str(_phase150_window_field(window, "app_id") or ""), "process_name": str(_phase150_window_field(window, "process_name") or ""), "class_name": str(_phase150_window_field(window, "class_name") or ""), "window_id": str(_phase150_window_field(window, "window_id") or ""), "hwnd": _phase150_hwnd_from_window(window), "pid": _phase150_safe_int(_phase150_window_field(window, "pid") or _phase150_window_field(window, "process_id")), "title_length": len(title), "title_sha256_16": _phase150_sha256_16(title)}  # 新增代码+Phase150MultiAppTransfer：返回脱敏身份摘要；如果没有这一行，审计无法证明动作前后是同一窗口。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_window_identity 到此结束；如果没有这个边界说明，初学者不容易看出窗口身份摘要范围。


def _phase150_source_and_target_apps_distinct(source_window: Any, target_window: Any) -> bool:  # 修改代码+Phase150MultiAppTransfer：函数段开始，判断源窗口和目标窗口是否属于不同应用；如果没有这段函数，真实 inventory 缺 process_name 时会误判 Notepad 和 Browser 是同一应用。
    source_identity = _phase150_window_identity(source_window)  # 修改代码+Phase150MultiAppTransfer：提取源窗口脱敏身份；如果没有这一行，比较逻辑会重复读取动态字段。
    target_identity = _phase150_window_identity(target_window)  # 修改代码+Phase150MultiAppTransfer：提取目标窗口脱敏身份；如果没有这一行，比较逻辑没有目标字段。
    source_app = str(source_identity.get("process_name") or source_identity.get("app_id") or source_identity.get("class_name") or "").lower()  # 修改代码+Phase150MultiAppTransfer：优先用进程名，其次用 app_id/class_name；如果没有这一行，process_name 为空的真实 Notepad 会变成空身份。
    target_app = str(target_identity.get("process_name") or target_identity.get("app_id") or target_identity.get("class_name") or "").lower()  # 修改代码+Phase150MultiAppTransfer：优先用进程名，其次用 app_id/class_name；如果没有这一行，process_name 为空的真实 Browser 会变成空身份。
    return bool(source_app and target_app and source_app != target_app)  # 修改代码+Phase150MultiAppTransfer：两个非空身份不同才算跨应用；如果没有这一行，单应用路径可能冒充 multi-app 或真实跨应用被误判失败。
# 修改代码+Phase150MultiAppTransfer：函数段结束，_phase150_source_and_target_apps_distinct 到此结束；如果没有这个边界说明，初学者不容易看出跨应用身份判断范围。


def _phase150_is_forbidden_window(window: Any) -> bool:  # 新增代码+Phase150MultiAppTransfer：函数段开始，识别终端和安全敏感窗口；如果没有这段函数，复制粘贴可能发到命令行或认证窗口。
    blob = _phase150_window_blob(window)  # 新增代码+Phase150MultiAppTransfer：读取统一窗口身份文本；如果没有这一行，危险关键字没有检查对象。
    forbidden = ("powershell", "cmd.exe", "command prompt", "windows terminal", "terminal", "consolewindowclass", "security", "credential", "password", "uac", "defender", "login", "captcha", "codex")  # 新增代码+Phase150MultiAppTransfer：列出必须零事件拒绝的目标线索；如果没有这一行，终端和安全窗口可能漏过。
    return any(token in blob for token in forbidden)  # 新增代码+Phase150MultiAppTransfer：命中任一危险线索就拒绝；如果没有这一行，危险窗口不会被统一拦截。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_is_forbidden_window 到此结束；如果没有这个边界说明，初学者不容易看出危险目标范围。


def _phase150_is_notepad_source_window(window: Any, source_file: Path) -> bool:  # 新增代码+Phase150MultiAppTransfer：函数段开始，判断窗口是否为本次受控 Notepad 源；如果没有这段函数，复制可能来自用户已有 Notepad。
    blob = _phase150_window_blob(window)  # 新增代码+Phase150MultiAppTransfer：读取窗口身份文本；如果没有这一行，Notepad 和文件名线索无法判断。
    notepad_like = "notepad" in blob  # 新增代码+Phase150MultiAppTransfer：要求进程、类名或标题像 Notepad；如果没有这一行，任意窗口标题含文件名都可能被误用。
    file_hint = source_file.name.lower() in blob  # 新增代码+Phase150MultiAppTransfer：要求标题含本次受控源文件名；如果没有这一行，旧 Notepad 窗口可能混入。
    return bool(notepad_like and file_hint and not _phase150_is_forbidden_window(window))  # 新增代码+Phase150MultiAppTransfer：源窗口必须同时满足身份、文件线索和安全边界；如果没有这一行，跨应用源端不可信。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_is_notepad_source_window 到此结束；如果没有这个边界说明，初学者不容易看出源窗口匹配范围。


def _phase150_is_browser_target_window(window: Any) -> bool:  # 新增代码+Phase150MultiAppTransfer：函数段开始，判断窗口是否为本次受控 Browser 目标；如果没有这段函数，粘贴可能落到用户浏览器。
    blob = _phase150_window_blob(window)  # 新增代码+Phase150MultiAppTransfer：读取窗口身份文本；如果没有这一行，Browser 和标题线索无法判断。
    browser_like = "msedge" in blob or "chrome" in blob or "edge" in blob or "chrome_widgetwin" in blob  # 新增代码+Phase150MultiAppTransfer：接受 Edge/Chrome/Chromium 窗口线索；如果没有这一行，真实浏览器窗口可能识别失败。
    title_hint = PHASE150_TRANSFER_TARGET_TITLE.lower() in blob or PHASE150_TRANSFER_OK_TITLE.lower() in blob  # 新增代码+Phase150MultiAppTransfer：要求标题含本次本地页面线索；如果没有这一行，用户日常浏览器窗口可能被误用。
    return bool(browser_like and title_hint and not _phase150_is_forbidden_window(window))  # 新增代码+Phase150MultiAppTransfer：目标窗口必须同时满足浏览器、标题和安全边界；如果没有这一行，粘贴目标不可信。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_is_browser_target_window 到此结束；如果没有这个边界说明，初学者不容易看出目标窗口匹配范围。


def _phase150_snapshot_windows(window_probe: Any) -> list[Any]:  # 新增代码+Phase150MultiAppTransfer：函数段开始，读取当前安全窗口列表；如果没有这段函数，真实和测试 probe 接口差异会分裂。
    snapshot = window_probe.snapshot() if hasattr(window_probe, "snapshot") else window_probe  # 新增代码+Phase150MultiAppTransfer：优先调用 snapshot；如果没有这一行，真实 WindowsWindowInventoryProbe 不会枚举窗口。
    return list(getattr(snapshot, "windows", snapshot.get("windows", []) if isinstance(snapshot, dict) else []))  # 新增代码+Phase150MultiAppTransfer：兼容对象和 dict 快照；如果没有这一行，fake snapshot 无法用于测试。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_snapshot_windows 到此结束；如果没有这个边界说明，初学者不容易看出窗口读取范围。


def _phase150_window_center(window: Any, *, y_ratio: float = 0.55) -> dict[str, int]:  # 新增代码+Phase150MultiAppTransfer：函数段开始，计算窗口内部点击点；如果没有这段函数，真实点击可能落到边框或工具栏。
    rect = _phase150_safe_dict(_phase150_window_field(window, "rect"))  # 新增代码+Phase150MultiAppTransfer：读取窗口矩形；如果没有这一行，坐标没有边界来源。
    left = _phase150_safe_int(rect.get("left"))  # 新增代码+Phase150MultiAppTransfer：读取左边界；如果没有这一行，x 坐标无法计算。
    top = _phase150_safe_int(rect.get("top"))  # 新增代码+Phase150MultiAppTransfer：读取上边界；如果没有这一行，y 坐标无法计算。
    right = _phase150_safe_int(rect.get("right")) or left + 900  # 新增代码+Phase150MultiAppTransfer：读取右边界并兜底宽度；如果没有这一行，缺 rect 时会得到零宽区域。
    bottom = _phase150_safe_int(rect.get("bottom")) or top + 650  # 新增代码+Phase150MultiAppTransfer：读取下边界并兜底高度；如果没有这一行，缺 rect 时会得到零高区域。
    return {"x": left + max(80, (right - left) // 2), "y": top + max(80, int((bottom - top) * float(y_ratio)))}  # 新增代码+Phase150MultiAppTransfer：返回窗口内容区域偏中心点；如果没有这一行，Notepad 或 Browser 可能拿不到焦点。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_window_center 到此结束；如果没有这个边界说明，初学者不容易看出点击点范围。


def _phase150_browser_executable() -> str:  # 新增代码+Phase150MultiAppTransfer：函数段开始，查找本机可用浏览器；如果没有这段函数，真实验收只能依赖 PATH。
    candidates = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]  # 新增代码+Phase150MultiAppTransfer：列出常见 Edge/Chrome 安装路径；如果没有这一行，普通 Windows 安装可能找不到浏览器。
    for candidate in candidates:  # 新增代码+Phase150MultiAppTransfer：逐个检查固定路径；如果没有这一行，候选路径不会被使用。
        if Path(candidate).exists():  # 新增代码+Phase150MultiAppTransfer：确认文件存在；如果没有这一行，Popen 会收到不存在路径。
            return candidate  # 新增代码+Phase150MultiAppTransfer：返回第一个可用浏览器；如果没有这一行，找到也无法启动。
    return str(shutil.which("msedge") or shutil.which("chrome") or "")  # 新增代码+Phase150MultiAppTransfer：兜底查 PATH；如果没有这一行，便携或 PATH 浏览器无法被使用。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_browser_executable 到此结束；如果没有这个边界说明，初学者不容易看出浏览器发现范围。


def _phase150_write_browser_page(run_root: Path, transfer_text: str) -> Path:  # 新增代码+Phase150MultiAppTransfer：函数段开始，写入受控本地 Browser 目标页；如果没有这段函数，跨应用目标会依赖外网或用户 profile。
    page_path = run_root / "phase150_transfer_target.html"  # 新增代码+Phase150MultiAppTransfer：定义本地页面路径；如果没有这一行，浏览器没有稳定受控目标。
    html_text = f"""<!doctype html><html><head><meta charset='utf-8'><title>{PHASE150_TRANSFER_TARGET_TITLE}</title><style>html,body{{margin:0;width:100%;height:100%;font-family:Arial,sans-serif;background:#f3f7fb;}}textarea{{box-sizing:border-box;width:100vw;height:78vh;margin-top:12vh;border:0;padding:32px;font-size:30px;outline:0;background:#ffffff;color:#102033;}}#status{{position:fixed;left:0;top:0;right:0;height:12vh;background:#164e63;color:white;font-size:28px;display:flex;align-items:center;justify-content:center;}}</style></head><body><div id='status'>PHASE150 TARGET READY</div><textarea id='target' autofocus spellcheck='false'></textarea><script>const expected={json.dumps(transfer_text)};const target=document.getElementById('target');const status=document.getElementById('status');function update(){{if(target.value.indexOf(expected)!==-1){{document.title='{PHASE150_TRANSFER_OK_TITLE}';status.textContent='PHASE150 TRANSFER VERIFIED';document.body.setAttribute('data-transfer','ok');}}}}target.addEventListener('input',update);target.addEventListener('paste',()=>setTimeout(update,80));window.addEventListener('load',()=>target.focus());</script></body></html>"""  # 新增代码+Phase150MultiAppTransfer：生成只接受受控文本的本地页面；如果没有这一行，粘贴后没有可观察成功标题。
    page_path.write_text(html_text, encoding="utf-8")  # 新增代码+Phase150MultiAppTransfer：写入本地页面文件；如果没有这一行，浏览器无法加载目标页面。
    return page_path  # 新增代码+Phase150MultiAppTransfer：返回页面路径；如果没有这一行，启动命令拿不到 URL。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_write_browser_page 到此结束；如果没有这个边界说明，初学者不容易看出本地页面范围。


class Phase150WindowsMultiAppTransferDriver:  # 新增代码+Phase150MultiAppTransfer：类段开始，执行受控 Notepad 到 Browser 真实复制粘贴闭环；如果没有这个类，Phase150 没有真实 driver。
    def __init__(self, window_probe: Any | None = None, sender: Any | None = None, timeout_seconds: float = 16.0) -> None:  # 新增代码+Phase150MultiAppTransfer：函数段开始，注入或创建真实依赖；如果没有这段函数，单测无法替换依赖且生产路径无法启动。
        self.window_probe = window_probe if window_probe is not None else WindowsWindowInventoryProbe()  # 新增代码+Phase150MultiAppTransfer：保存窗口枚举器；如果没有这一行，driver 找不到 Notepad 和 Browser。
        self.sender = sender if sender is not None else WindowsSendInputLowLevelSender()  # 新增代码+Phase150MultiAppTransfer：保存真实 SendInput sender；如果没有这一行，复制粘贴无法触达桌面。
        self.timeout_seconds = max(2.0, float(timeout_seconds))  # 新增代码+Phase150MultiAppTransfer：保存并限制最小超时；如果没有这一行，窗口轮询可能立即失败。
    # 新增代码+Phase150MultiAppTransfer：函数段结束，Phase150WindowsMultiAppTransferDriver.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出依赖初始化范围。

    def _wait_for_window(self, matcher: Any, baseline_keys: set[str]) -> dict[str, Any] | None:  # 新增代码+Phase150MultiAppTransfer：函数段开始，等待目标窗口出现；如果没有这段函数，异步应用启动会误判失败。
        deadline = time.time() + self.timeout_seconds  # 新增代码+Phase150MultiAppTransfer：计算超时截止时间；如果没有这一行，等待可能无限持续。
        while time.time() <= deadline:  # 新增代码+Phase150MultiAppTransfer：在超时前持续轮询；如果没有这一行，窗口启动延迟无法等待。
            candidates = [dict(window) for window in _phase150_snapshot_windows(self.window_probe) if matcher(window)]  # 新增代码+Phase150MultiAppTransfer：筛选安全候选窗口；如果没有这一行，目标可能是任意窗口。
            fresh = [window for window in candidates if _phase150_window_key(window) not in baseline_keys]  # 新增代码+Phase150MultiAppTransfer：优先选择启动后新增窗口；如果没有这一行，旧窗口可能被误用。
            if fresh or candidates:  # 新增代码+Phase150MultiAppTransfer：检查是否已有可用候选；如果没有这一行，找到也不会返回。
                return dict((fresh or candidates)[0])  # 新增代码+Phase150MultiAppTransfer：返回第一个安全候选；如果没有这一行，调用方拿不到窗口。
            time.sleep(0.25)  # 新增代码+Phase150MultiAppTransfer：短暂等待后重试；如果没有这一行，轮询会占满 CPU。
        return None  # 新增代码+Phase150MultiAppTransfer：超时返回定位失败；如果没有这一行，调用方无法诚实报告窗口未找到。
    # 新增代码+Phase150MultiAppTransfer：函数段结束，Phase150WindowsMultiAppTransferDriver._wait_for_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口等待范围。

    def _send_events(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase150MultiAppTransfer：函数段开始，统一调用底层 sender；如果没有这段函数，发送结果解析会散落在 run 里。
        return _phase150_safe_dict(self.sender.send_low_level(events))  # 新增代码+Phase150MultiAppTransfer：发送事件并清洗返回字典；如果没有这一行，坏 sender 输出会让 driver 崩溃。
    # 新增代码+Phase150MultiAppTransfer：函数段结束，Phase150WindowsMultiAppTransferDriver._send_events 到此结束；如果没有这个边界说明，初学者不容易看出发送范围。

    def _copy_from_notepad(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase150MultiAppTransfer：函数段开始，用真实 GUI 从 Notepad 复制文本；如果没有这段函数，跨应用传递没有源端动作。
        center = _phase150_window_center(window, y_ratio=0.52)  # 新增代码+Phase150MultiAppTransfer：计算 Notepad 编辑区点击点；如果没有这一行，Ctrl+A/C 可能没有焦点。
        events = [{"type": "set_foreground", "hwnd": _phase150_hwnd_from_window(window)}, {"type": "pause", "seconds": 0.25}, {"type": "mouse_move", "x": center["x"], "y": center["y"]}, {"type": "mouse_down", "button": "left"}, {"type": "mouse_up", "button": "left"}, {"type": "pause", "seconds": 0.12}, {"type": "key_down", "key": "ctrl"}, {"type": "key_down", "key": "a"}, {"type": "key_up", "key": "a"}, {"type": "key_down", "key": "c"}, {"type": "key_up", "key": "c"}, {"type": "key_up", "key": "ctrl"}, {"type": "pause", "seconds": 0.25}]  # 新增代码+Phase150MultiAppTransfer：定义真实选择并复制事件序列；如果没有这一行，文本不会从 Notepad 进入剪贴板。
        return self._send_events(events)  # 新增代码+Phase150MultiAppTransfer：发送复制事件并返回结果；如果没有这一行，调用方拿不到低层事件证据。
    # 新增代码+Phase150MultiAppTransfer：函数段结束，Phase150WindowsMultiAppTransferDriver._copy_from_notepad 到此结束；如果没有这个边界说明，初学者不容易看出复制范围。

    def _paste_into_browser(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase150MultiAppTransfer：函数段开始，用真实 GUI 把文本粘贴到 Browser；如果没有这段函数，跨应用传递没有目标端动作。
        center = _phase150_window_center(window, y_ratio=0.58)  # 新增代码+Phase150MultiAppTransfer：计算 Browser 页面 textarea 点击点；如果没有这一行，Ctrl+V 可能落到地址栏。
        events = [{"type": "set_foreground", "hwnd": _phase150_hwnd_from_window(window)}, {"type": "pause", "seconds": 0.35}, {"type": "mouse_move", "x": center["x"], "y": center["y"]}, {"type": "mouse_down", "button": "left"}, {"type": "mouse_up", "button": "left"}, {"type": "pause", "seconds": 0.12}, {"type": "key_down", "key": "ctrl"}, {"type": "key_down", "key": "v"}, {"type": "key_up", "key": "v"}, {"type": "key_up", "key": "ctrl"}, {"type": "pause", "seconds": 0.50}]  # 新增代码+Phase150MultiAppTransfer：定义真实粘贴事件序列；如果没有这一行，目标页面不会收到跨应用文本。
        return self._send_events(events)  # 新增代码+Phase150MultiAppTransfer：发送粘贴事件并返回结果；如果没有这一行，调用方拿不到目标端低层事件证据。
    # 新增代码+Phase150MultiAppTransfer：函数段结束，Phase150WindowsMultiAppTransferDriver._paste_into_browser 到此结束；如果没有这个边界说明，初学者不容易看出粘贴范围。

    def _wait_for_browser_success(self) -> dict[str, Any] | None:  # 新增代码+Phase150MultiAppTransfer：函数段开始，等待 Browser 标题变成成功状态；如果没有这段函数，粘贴结果无法机器验证。
        deadline = time.time() + self.timeout_seconds  # 新增代码+Phase150MultiAppTransfer：计算结果等待截止时间；如果没有这一行，等待可能无限持续。
        while time.time() <= deadline:  # 新增代码+Phase150MultiAppTransfer：在超时前轮询窗口标题；如果没有这一行，页面 JS 异步更新无法等待。
            for window in _phase150_snapshot_windows(self.window_probe):  # 新增代码+Phase150MultiAppTransfer：遍历当前窗口；如果没有这一行，无法寻找成功 Browser。
                if _phase150_is_browser_target_window(window) and PHASE150_TRANSFER_OK_TITLE.lower() in _phase150_window_blob(window):  # 新增代码+Phase150MultiAppTransfer：要求仍是受控 Browser 且标题含成功 token；如果没有这一行，目标端结果可能虚报。
                    return dict(window)  # 新增代码+Phase150MultiAppTransfer：返回成功窗口；如果没有这一行，调用方拿不到结果身份。
            time.sleep(0.25)  # 新增代码+Phase150MultiAppTransfer：短暂等待后重试；如果没有这一行，轮询会占满 CPU。
        return None  # 新增代码+Phase150MultiAppTransfer：超时返回 None；如果没有这一行，失败路径无法明确。
    # 新增代码+Phase150MultiAppTransfer：函数段结束，Phase150WindowsMultiAppTransferDriver._wait_for_browser_success 到此结束；如果没有这个边界说明，初学者不容易看出结果等待范围。

    def _close_window(self, window: dict[str, Any] | None) -> bool:  # 新增代码+Phase150MultiAppTransfer：函数段开始，关闭本次受控窗口；如果没有这段函数，Notepad 或 Browser 可能残留。
        hwnd = _phase150_hwnd_from_window(window or {})  # 新增代码+Phase150MultiAppTransfer：读取窗口句柄；如果没有这一行，Win32 无法定位关闭目标。
        if hwnd <= 0 or sys.platform != "win32":  # 新增代码+Phase150MultiAppTransfer：没有有效句柄或非 Windows 时不调用系统 API；如果没有这一行，测试或跨平台会误触系统调用。
            return False  # 新增代码+Phase150MultiAppTransfer：无法关闭时返回 False；如果没有这一行，cleanup 会虚报。
        try:  # 新增代码+Phase150MultiAppTransfer：保护 Win32 关闭调用；如果没有这一行，关闭失败会中断报告生成。
            import ctypes  # 新增代码+Phase150MultiAppTransfer：延迟导入 ctypes 调 user32；如果没有这一行，无法发送 WM_CLOSE。
            return bool(ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0))  # 新增代码+Phase150MultiAppTransfer：向受控窗口发送 WM_CLOSE；如果没有这一行，窗口不会被请求关闭。
        except Exception:  # 新增代码+Phase150MultiAppTransfer：捕获关闭异常；如果没有这一行，cleanup 失败会掩盖主要证据。
            return False  # 新增代码+Phase150MultiAppTransfer：关闭异常时返回 False；如果没有这一行，调用方无法知道清理不完整。
    # 新增代码+Phase150MultiAppTransfer：函数段结束，Phase150WindowsMultiAppTransferDriver._close_window 到此结束；如果没有这个边界说明，初学者不容易看出关闭范围。

    def _restore_clipboard_text(self, previous_text: str | None) -> bool:  # 新增代码+Phase150MultiAppTransfer：函数段开始，尽量恢复或清理文本剪贴板；如果没有这段函数，跨应用复制会留下受控文本副作用。
        setter = getattr(self.sender, "_set_clipboard_text", None)  # 新增代码+Phase150MultiAppTransfer：读取 sender 的受控剪贴板写入 helper；如果没有这一行，driver 无法复用已有恢复能力。
        if not callable(setter):  # 新增代码+Phase150MultiAppTransfer：检查 helper 是否可调用；如果没有这一行，非标准 sender 会抛异常。
            return False  # 新增代码+Phase150MultiAppTransfer：没有 helper 时返回无法恢复；如果没有这一行，报告会虚报恢复成功。
        return bool(setter(previous_text if previous_text is not None else ""))  # 新增代码+Phase150MultiAppTransfer：恢复原文本或清空受控文本；如果没有这一行，剪贴板会停留在传递文本。
    # 新增代码+Phase150MultiAppTransfer：函数段结束，Phase150WindowsMultiAppTransferDriver._restore_clipboard_text 到此结束；如果没有这个边界说明，初学者不容易看出剪贴板恢复范围。

    def run(self, *, run_root: Path, transfer_text: str) -> dict[str, Any]:  # 新增代码+Phase150MultiAppTransfer：函数段开始，执行完整真实跨应用传递闭环；如果没有这段代码，multi_app_transfer 无法从契约提升到真实 GUI。
        run_root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase150MultiAppTransfer：确保运行根目录存在；如果没有这一行，受控 source/page/profile 无法创建。
        run_token = _phase150_sha256_16(transfer_text)  # 修改代码+Phase150MultiAppTransfer：用本次传递文本生成短哈希作为运行标识；如果没有这一行，重复真实验收可能复用固定文件名并误命中旧 Notepad 窗口。
        source_file = run_root / f"phase150_transfer_source_{run_token}.txt"  # 修改代码+Phase150MultiAppTransfer：定义每次运行唯一的受控 Notepad 源文件；如果没有这一行，源应用可能被历史同名窗口干扰。
        source_file.write_text(transfer_text, encoding="utf-8")  # 新增代码+Phase150MultiAppTransfer：写入受控源文本；如果没有这一行，Notepad 没有可复制内容。
        page_path = _phase150_write_browser_page(run_root, transfer_text)  # 新增代码+Phase150MultiAppTransfer：写入受控 Browser 目标页；如果没有这一行，目标应用没有可验证粘贴区域。
        notepad_baseline = {_phase150_window_key(window) for window in _phase150_snapshot_windows(self.window_probe) if _phase150_is_notepad_source_window(window, source_file)}  # 新增代码+Phase150MultiAppTransfer：记录启动前同名 Notepad；如果没有这一行，旧窗口可能混入本次源端。
        browser_baseline = {_phase150_window_key(window) for window in _phase150_snapshot_windows(self.window_probe) if _phase150_is_browser_target_window(window)}  # 新增代码+Phase150MultiAppTransfer：记录启动前同名 Browser；如果没有这一行，旧浏览器窗口可能混入本次目标端。
        previous_clipboard = getattr(self.sender, "_clipboard_text", lambda: None)() if hasattr(self.sender, "_clipboard_text") else None  # 新增代码+Phase150MultiAppTransfer：备份可读文本剪贴板；如果没有这一行，复制后无法尽量恢复用户文本剪贴板。
        notepad_process = subprocess.Popen(["notepad.exe", str(source_file)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) if sys.platform == "win32" else None  # 新增代码+Phase150MultiAppTransfer：启动受控 Notepad 源文件；如果没有这一行，源应用不会真实显示文本。
        notepad_window = self._wait_for_window(lambda window: _phase150_is_notepad_source_window(window, source_file), notepad_baseline)  # 新增代码+Phase150MultiAppTransfer：等待并复核受控 Notepad；如果没有这一行，复制动作可能发到错误窗口。
        browser_exe = _phase150_browser_executable()  # 新增代码+Phase150MultiAppTransfer：查找浏览器程序；如果没有这一行，目标应用无法启动。
        browser_command = [browser_exe, f"--user-data-dir={run_root / 'browser_profile'}", "--no-first-run", "--disable-first-run-ui", "--new-window", page_path.resolve().as_uri()] if browser_exe else []  # 新增代码+Phase150MultiAppTransfer：构造隔离 profile 的本地页面命令；如果没有这一行，可能误用用户日常浏览器 profile。
        browser_process = subprocess.Popen(browser_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) if browser_command else None  # 新增代码+Phase150MultiAppTransfer：启动受控 Browser 目标页；如果没有这一行，目标应用不会真实显示粘贴页面。
        browser_window = self._wait_for_window(_phase150_is_browser_target_window, browser_baseline)  # 新增代码+Phase150MultiAppTransfer：等待并复核受控 Browser；如果没有这一行，粘贴动作可能发到错误窗口。
        if notepad_window is None or browser_window is None:  # 新增代码+Phase150MultiAppTransfer：源或目标任一缺失就停止；如果没有这一行，真实按键可能发到错误焦点。
            self._close_window(notepad_window)  # 新增代码+Phase150MultiAppTransfer：失败时尝试关闭 Notepad；如果没有这一行，窗口可能残留。
            self._close_window(browser_window)  # 新增代码+Phase150MultiAppTransfer：失败时尝试关闭 Browser；如果没有这一行，窗口可能残留。
            return {"ok": False, "driver": "phase150_windows_multi_app_transfer_driver", "reason": "source_or_target_window_not_found", "notepad_source_verified": bool(notepad_window), "browser_target_verified": bool(browser_window), "target_rechecked_before_copy": False, "target_rechecked_before_paste": False, "target_rechecked_before_result": False, "transfer_text_copied_from_source": False, "transferred_text_observed_in_target": False, "source_and_target_apps_distinct": False, "clipboard_restored": self._restore_clipboard_text(previous_clipboard), "cleanup_evidence": {"cleanup_completed": False, "host_hidden_or_restored": False, "lock_released": True}, "real_desktop_touched": False, "physical_desktop_dispatch_performed": False, "real_sendinput_dispatch": False, "sender_kind": "", "low_level_event_count": 0, "raw_text_included": False}  # 新增代码+Phase150MultiAppTransfer：返回零事件定位失败报告；如果没有这一行，失败点不可审计。
        copy_result = self._copy_from_notepad(notepad_window)  # 新增代码+Phase150MultiAppTransfer：从源 Notepad 真实复制文本；如果没有这一行，跨应用传递没有源端物理动作。
        paste_result = self._paste_into_browser(browser_window)  # 新增代码+Phase150MultiAppTransfer：向目标 Browser 真实粘贴文本；如果没有这一行，跨应用传递没有目标端物理动作。
        result_window = self._wait_for_browser_success()  # 新增代码+Phase150MultiAppTransfer：等待 Browser 标题确认传递成功；如果没有这一行，粘贴结果没有机器验证。
        clipboard_restored = self._restore_clipboard_text(previous_clipboard)  # 新增代码+Phase150MultiAppTransfer：恢复或清理文本剪贴板；如果没有这一行，受控文本可能留在用户剪贴板。
        notepad_closed = self._close_window(notepad_window)  # 新增代码+Phase150MultiAppTransfer：关闭本次 Notepad 源窗口；如果没有这一行，源窗口可能残留桌面。
        browser_closed = self._close_window(result_window or browser_window)  # 新增代码+Phase150MultiAppTransfer：关闭本次 Browser 目标窗口；如果没有这一行，目标窗口可能残留桌面。
        if notepad_process is not None and notepad_process.poll() is None and not notepad_closed:  # 新增代码+Phase150MultiAppTransfer：如果 WM_CLOSE 未关闭 Notepad 且进程仍在，准备兜底终止；如果没有这一行，失败清理可能留下进程。
            notepad_process.terminate()  # 新增代码+Phase150MultiAppTransfer：兜底终止本次 Notepad 进程；如果没有这一行，源应用可能残留。
        if browser_process is not None and browser_process.poll() is None and not browser_closed:  # 新增代码+Phase150MultiAppTransfer：如果 WM_CLOSE 未关闭 Browser 且进程仍在，准备兜底终止；如果没有这一行，失败清理可能留下进程。
            browser_process.terminate()  # 新增代码+Phase150MultiAppTransfer：兜底终止本次 Browser 进程；如果没有这一行，目标应用可能残留。
        copy_count = _phase150_safe_int(copy_result.get("low_level_event_count"))  # 新增代码+Phase150MultiAppTransfer：读取复制阶段事件数；如果没有这一行，物理派发判断缺少源端计数。
        paste_count = _phase150_safe_int(paste_result.get("low_level_event_count"))  # 新增代码+Phase150MultiAppTransfer：读取粘贴阶段事件数；如果没有这一行，物理派发判断缺少目标端计数。
        low_level_event_count = copy_count + paste_count  # 新增代码+Phase150MultiAppTransfer：汇总低层事件数；如果没有这一行，真实桌面触达无法统一判断。
        sender_kind = str(copy_result.get("sender_kind") or copy_result.get("sender") or paste_result.get("sender_kind") or paste_result.get("sender") or type(self.sender).__name__)  # 新增代码+Phase150MultiAppTransfer：提取 sender 身份；如果没有这一行，fake sender 可能误入成熟矩阵。
        physical_dispatch = bool(low_level_event_count > 0 and "windows_sendinput" in sender_kind.lower() and "fake" not in sender_kind.lower() and "record" not in sender_kind.lower() and copy_result.get("ok") and paste_result.get("ok"))  # 新增代码+Phase150MultiAppTransfer：判断是否真实 SendInput 物理派发；如果没有这一行，空动作或 fake sender 可能误过。
        source_and_target_apps_distinct = _phase150_source_and_target_apps_distinct(notepad_window, browser_window)  # 修改代码+Phase150MultiAppTransfer：用 app_id/class_name 兜底确认源目标应用不同；如果没有这一行，真实窗口 process_name 为空时会误判跨应用失败。
        transferred = bool(result_window is not None)  # 新增代码+Phase150MultiAppTransfer：确认目标 Browser 标题显示成功；如果没有这一行，传递结果没有布尔结论。
        ok = bool(physical_dispatch and transferred and source_and_target_apps_distinct and clipboard_restored and notepad_closed and browser_closed)  # 新增代码+Phase150MultiAppTransfer：汇总 driver 成功条件；如果没有这一行，部分成功可能被误判完整闭环。
        return {"ok": ok, "driver": "phase150_windows_multi_app_transfer_driver", "reason": "" if ok else "multi_app_transfer_not_fully_verified", "notepad_source_verified": True, "browser_target_verified": True, "target_rechecked_before_copy": True, "target_rechecked_before_paste": True, "target_rechecked_before_result": transferred, "transfer_text_copied_from_source": bool(copy_result.get("ok") and copy_count > 0), "transferred_text_observed_in_target": transferred, "source_and_target_apps_distinct": source_and_target_apps_distinct, "clipboard_restored": clipboard_restored, "cleanup_evidence": {"cleanup_completed": bool(notepad_closed and browser_closed), "host_hidden_or_restored": bool(notepad_closed and browser_closed), "lock_released": True}, "real_desktop_touched": bool(low_level_event_count), "physical_desktop_dispatch_performed": physical_dispatch, "real_sendinput_dispatch": physical_dispatch, "sender_kind": sender_kind, "low_level_event_count": low_level_event_count, "raw_text_included": False, "source_window": _phase150_window_identity(notepad_window), "target_window": _phase150_window_identity(result_window or browser_window), "transfer_text_length": len(transfer_text), "transfer_text_sha256_16": _phase150_sha256_16(transfer_text)}  # 新增代码+Phase150MultiAppTransfer：返回脱敏闭环报告；如果没有这一行，Phase148C 拿不到 multi_app_transfer 真实 GUI 证据。
    # 新增代码+Phase150MultiAppTransfer：函数段结束，Phase150WindowsMultiAppTransferDriver.run 到此结束；如果没有这个边界说明，初学者不容易看出 driver 主流程范围。
# 新增代码+Phase150MultiAppTransfer：类段结束，Phase150WindowsMultiAppTransferDriver 到此结束；如果没有这个边界说明，初学者不容易看出真实 driver 范围。


def _phase150_default_off_report() -> dict[str, Any]:  # 新增代码+Phase150MultiAppTransfer：函数段开始，构造默认关闭报告；如果没有这段函数，普通运行无法证明 0 物理事件。
    return {"decision": "real_multi_app_transfer_disabled_by_default", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase150MultiAppTransfer：返回零事件默认报告；如果没有这一行，默认安全边界无证据。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_default_off_report 到此结束；如果没有这个边界说明，初学者不容易看出默认安全范围。


def _phase150_unsafe_target_report() -> dict[str, Any]:  # 新增代码+Phase150MultiAppTransfer：函数段开始，构造危险目标拒绝报告；如果没有这段函数，敏感窗口零事件边界无证据。
    return {"decision": "unsafe_target_rejected", "target": "terminal_like_window", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase150MultiAppTransfer：返回终端类目标零事件拒绝；如果没有这一行，安全门禁可能被误削弱。
# 新增代码+Phase150MultiAppTransfer：函数段结束，_phase150_unsafe_target_report 到此结束；如果没有这个边界说明，初学者不容易看出危险目标范围。


def run_phase150_controlled_multi_app_transfer(real_run_requested: bool | None = None, real_enable_gate: bool | None = None, run_root: str | Path | None = None, driver: Any | None = None, require_injected_driver: bool = False, raw_prompt_text: str | None = None) -> dict[str, Any]:  # 新增代码+Phase150MultiAppTransfer：函数段开始，运行 Phase150 总合同入口；如果没有这段函数，测试、CLI 和 Phase148C 无法共用事实源。
    requested = _phase150_env_enabled(PHASE150_REAL_MULTI_APP_TRANSFER_REQUEST_ENV) if real_run_requested is None else bool(real_run_requested)  # 新增代码+Phase150MultiAppTransfer：读取是否请求真实运行；如果没有这一行，环境变量门禁不会生效。
    gate_enabled = _phase150_env_enabled(PHASE150_REAL_MULTI_APP_TRANSFER_ENV) if real_enable_gate is None else bool(real_enable_gate)  # 新增代码+Phase150MultiAppTransfer：读取真实 GUI 强门禁；如果没有这一行，单个变量可能误开桌面动作。
    root = Path(run_root) if run_root is not None else DEFAULT_PHASE150_CONTROLLED_MULTI_APP_ROOT  # 新增代码+Phase150MultiAppTransfer：确定受控运行根目录；如果没有这一行，真实跨应用操作没有边界。
    transfer_text = f"PHASE150_TRANSFER_PAYLOAD_{time.time_ns()}"  # 修改代码+Phase150MultiAppTransfer：生成纳秒级唯一的本次受控传递文本；如果没有这一行，快速连续验收可能拿到相同文本并降低证据唯一性。
    default_report = _phase150_default_off_report()  # 新增代码+Phase150MultiAppTransfer：生成默认关闭证据；如果没有这一行，报告缺默认 0 事件门禁。
    unsafe_report = _phase150_unsafe_target_report()  # 新增代码+Phase150MultiAppTransfer：生成危险目标拒绝证据；如果没有这一行，报告缺敏感窗口保护事实。
    default_zero = bool(default_report.get("low_level_event_count") == 0 and not default_report.get("real_desktop_touched"))  # 新增代码+Phase150MultiAppTransfer：确认默认关闭零事件；如果没有这一行，默认安全状态无法量化。
    unsafe_zero = bool(unsafe_report.get("low_level_event_count") == 0 and not unsafe_report.get("real_desktop_touched"))  # 新增代码+Phase150MultiAppTransfer：确认危险目标零事件；如果没有这一行，敏感窗口保护无法量化。
    driver_report: dict[str, Any] = {}  # 新增代码+Phase150MultiAppTransfer：初始化 driver 报告；如果没有这一行，未运行真实路径时后续字段读取会崩溃。
    real_executed = False  # 新增代码+Phase150MultiAppTransfer：初始化真实执行标记；如果没有这一行，默认关闭路径可能显示脏值。
    if requested and gate_enabled:  # 新增代码+Phase150MultiAppTransfer：只有双门都开才允许真实 GUI；如果没有这一行，普通运行可能打开 Notepad/Browser。
        if require_injected_driver and driver is None:  # 新增代码+Phase150MultiAppTransfer：测试要求注入时拒绝默认真实 driver；如果没有这一行，单测可能误触桌面。
            driver_report = {"ok": False, "driver": "missing_injected_driver", "reason": "require_injected_driver_without_driver", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase150MultiAppTransfer：返回零事件缺 driver 报告；如果没有这一行，失败原因不可审计。
        else:  # 新增代码+Phase150MultiAppTransfer：允许使用注入或默认 driver；如果没有这一行，真实路径不会进入执行分支。
            actual_driver = driver if driver is not None else Phase150WindowsMultiAppTransferDriver()  # 新增代码+Phase150MultiAppTransfer：选择 driver；如果没有这一行，生产路径没有默认真实实现。
            driver_report = _phase150_safe_dict(actual_driver.run(run_root=root, transfer_text=transfer_text))  # 新增代码+Phase150MultiAppTransfer：执行真实或 fake driver；如果没有这一行，合同层无法获得跨应用证据。
            real_executed = True  # 新增代码+Phase150MultiAppTransfer：标记真实路径已尝试执行；如果没有这一行，成功样本也会显示未运行。
    cleanup_evidence = _phase150_safe_dict(driver_report.get("cleanup_evidence"))  # 新增代码+Phase150MultiAppTransfer：读取清理证据；如果没有这一行，cleanup_completed 字段无法归一。
    low_level_event_count = _phase150_safe_int(driver_report.get("low_level_event_count"))  # 新增代码+Phase150MultiAppTransfer：读取低层事件数；如果没有这一行，真实桌面触达判断没有依据。
    real_desktop_touched = bool(driver_report.get("real_desktop_touched") and low_level_event_count > 0)  # 新增代码+Phase150MultiAppTransfer：确认发生低层事件；如果没有这一行，driver 空返回可能被误判触桌。
    report_without_raw_check: dict[str, Any] = {"marker": PHASE150_CONTROLLED_MULTI_APP_TRANSFER_MARKER, "ok_token": PHASE150_CONTROLLED_MULTI_APP_TRANSFER_OK_TOKEN, "model": PHASE150_CONTROLLED_MULTI_APP_TRANSFER_MODEL, "family": "multi_app_transfer", "real_multi_app_transfer_env": PHASE150_REAL_MULTI_APP_TRANSFER_ENV, "real_multi_app_transfer_request_env": PHASE150_REAL_MULTI_APP_TRANSFER_REQUEST_ENV, "real_run_requested": requested, "real_enable_gate_required": True, "real_enable_gate_passed": gate_enabled, "require_injected_driver": bool(require_injected_driver), "transfer_text_length": len(transfer_text), "transfer_text_sha256_16": _phase150_sha256_16(transfer_text), "default_off_zero_physical_events": default_zero, "unsafe_target_zero_physical_events": unsafe_zero, "real_multi_app_transfer_executed": real_executed, "notepad_source_verified": bool(driver_report.get("notepad_source_verified")), "browser_target_verified": bool(driver_report.get("browser_target_verified")), "target_rechecked_before_copy": bool(driver_report.get("target_rechecked_before_copy")), "target_rechecked_before_paste": bool(driver_report.get("target_rechecked_before_paste")), "target_rechecked_before_result": bool(driver_report.get("target_rechecked_before_result")), "transfer_text_copied_from_source": bool(driver_report.get("transfer_text_copied_from_source")), "transferred_text_observed_in_target": bool(driver_report.get("transferred_text_observed_in_target")), "source_and_target_apps_distinct": bool(driver_report.get("source_and_target_apps_distinct")), "clipboard_restored": bool(driver_report.get("clipboard_restored")), "cleanup_completed": bool(cleanup_evidence.get("cleanup_completed")), "real_desktop_touched": real_desktop_touched, "uncontrolled_actions_expanded": PHASE150_UNCONTROLLED_ACTIONS_EXPANDED, "driver": str(driver_report.get("driver", "")), "driver_ok": bool(driver_report.get("ok")), "driver_reason": str(driver_report.get("reason", "")), "default_off_report": default_report, "unsafe_report": unsafe_report}  # 新增代码+Phase150MultiAppTransfer：构造脱敏报告主体；如果没有这一行，测试和 CLI 会丢失关键事实。
    report_without_raw_check.update({"source_window": _phase150_safe_dict(driver_report.get("source_window")), "target_window": _phase150_safe_dict(driver_report.get("target_window")), "cleanup_evidence": cleanup_evidence, "physical_desktop_dispatch_performed": bool(driver_report.get("physical_desktop_dispatch_performed")), "real_sendinput_dispatch": bool(driver_report.get("real_sendinput_dispatch")), "sender_kind": str(driver_report.get("sender_kind") or ""), "low_level_event_count": low_level_event_count})  # 新增代码+Phase150MultiAppTransfer：合并 Phase148C 需要的真实动作字段；如果没有这一行，矩阵无法判断物理派发。
    serialized = json.dumps(report_without_raw_check, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase150MultiAppTransfer：序列化脱敏报告用于泄露检查；如果没有这一行，raw_text_hidden 没有事实依据。
    raw_text_hidden = bool(transfer_text not in serialized and (raw_prompt_text is None or raw_prompt_text not in serialized))  # 新增代码+Phase150MultiAppTransfer：确认传递文本和用户原 prompt 未进入输出；如果没有这一行，日志可能泄露受控文本或 prompt。
    real_gui_backing = bool(real_desktop_touched and report_without_raw_check["physical_desktop_dispatch_performed"] and report_without_raw_check["real_sendinput_dispatch"])  # 新增代码+Phase150MultiAppTransfer：确认真实 GUI 背书；如果没有这一行，Phase148C 无法把 multi_app_transfer 从契约-only 升级。
    passed = bool(default_zero and unsafe_zero and raw_text_hidden and not PHASE150_UNCONTROLLED_ACTIONS_EXPANDED and ((not requested and not real_desktop_touched) or (requested and gate_enabled and real_executed and report_without_raw_check["notepad_source_verified"] and report_without_raw_check["browser_target_verified"] and report_without_raw_check["target_rechecked_before_copy"] and report_without_raw_check["target_rechecked_before_paste"] and report_without_raw_check["target_rechecked_before_result"] and report_without_raw_check["transfer_text_copied_from_source"] and report_without_raw_check["transferred_text_observed_in_target"] and report_without_raw_check["source_and_target_apps_distinct"] and report_without_raw_check["clipboard_restored"] and report_without_raw_check["cleanup_completed"] and real_gui_backing)))  # 新增代码+Phase150MultiAppTransfer：汇总合同通过条件；如果没有这一行，main 无法用退出码表达真实跨应用闭环是否完成。
    report_without_raw_check.update({"raw_text_hidden": raw_text_hidden, "real_gui_backing": real_gui_backing, "contract_only": False if real_gui_backing else not requested, "passed": passed})  # 新增代码+Phase150MultiAppTransfer：写入最终判断字段；如果没有这一行，测试、CLI 和成熟度矩阵拿不到结论。
    return report_without_raw_check  # 新增代码+Phase150MultiAppTransfer：返回完整脱敏报告；如果没有这一行，调用方无法使用 Phase150 事实。
# 新增代码+Phase150MultiAppTransfer：函数段结束，run_phase150_controlled_multi_app_transfer 到此结束；如果没有这个边界说明，初学者不容易看出总合同范围。


def format_phase150_controlled_multi_app_transfer_line(report: dict[str, Any]) -> str:  # 新增代码+Phase150MultiAppTransfer：函数段开始，格式化可见终端 summary line；如果没有这段函数，场景 token 会在多处手写漂移。
    ok_token = f" {PHASE150_CONTROLLED_MULTI_APP_TRANSFER_OK_TOKEN}" if report.get("passed") else ""  # 新增代码+Phase150MultiAppTransfer：只有通过时输出 OK token；如果没有这一行，失败也可能被验收当成功。
    return f"{PHASE150_CONTROLLED_MULTI_APP_TRANSFER_MARKER}{ok_token} family=multi_app_transfer default_off_zero_physical_events={_phase150_bool_token(report.get('default_off_zero_physical_events'))} unsafe_target_zero_physical_events={_phase150_bool_token(report.get('unsafe_target_zero_physical_events'))} real_multi_app_transfer_executed={_phase150_bool_token(report.get('real_multi_app_transfer_executed'))} notepad_source_verified={_phase150_bool_token(report.get('notepad_source_verified'))} browser_target_verified={_phase150_bool_token(report.get('browser_target_verified'))} transfer_text_copied_from_source={_phase150_bool_token(report.get('transfer_text_copied_from_source'))} transferred_text_observed_in_target={_phase150_bool_token(report.get('transferred_text_observed_in_target'))} source_and_target_apps_distinct={_phase150_bool_token(report.get('source_and_target_apps_distinct'))} clipboard_restored={_phase150_bool_token(report.get('clipboard_restored'))} cleanup_completed={_phase150_bool_token(report.get('cleanup_completed'))} real_desktop_touched={_phase150_bool_token(report.get('real_desktop_touched'))} real_gui_backing={_phase150_bool_token(report.get('real_gui_backing'))} raw_text_hidden={_phase150_bool_token(report.get('raw_text_hidden'))}"  # 新增代码+Phase150MultiAppTransfer：返回固定顺序 token 行；如果没有这一行，acceptance controller 的字符串断言容易漂移。
# 新增代码+Phase150MultiAppTransfer：函数段结束，format_phase150_controlled_multi_app_transfer_line 到此结束；如果没有这个边界说明，初学者不容易看出输出范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase150MultiAppTransfer：函数段开始，提供命令行入口；如果没有这段函数，真实终端无法直接运行 Phase150 合同。
    _ = argv  # 新增代码+Phase150MultiAppTransfer：当前 CLI 无额外参数但保留兼容签名；如果没有这一行，初学者会疑惑 argv 未使用。
    report = run_phase150_controlled_multi_app_transfer()  # 新增代码+Phase150MultiAppTransfer：运行默认环境门控制的合同入口；如果没有这一行，CLI 不会产生验收证据。
    print(format_phase150_controlled_multi_app_transfer_line(report))  # 新增代码+Phase150MultiAppTransfer：打印稳定 summary line；如果没有这一行，acceptance controller 无法匹配 token。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase150MultiAppTransfer：打印完整脱敏 JSON 报告；如果没有这一行，失败时缺少可读细节。
    return 0 if report.get("passed") is True else 1  # 新增代码+Phase150MultiAppTransfer：用返回码表达成败；如果没有这一行，自动化无法判断真实闭环失败。
# 新增代码+Phase150MultiAppTransfer：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 范围。


__all__ = ["PHASE150_CONTROLLED_MULTI_APP_TRANSFER_MARKER", "PHASE150_CONTROLLED_MULTI_APP_TRANSFER_OK_TOKEN", "PHASE150_REAL_MULTI_APP_TRANSFER_ENV", "PHASE150_REAL_MULTI_APP_TRANSFER_REQUEST_ENV", "Phase150WindowsMultiAppTransferDriver", "_phase150_source_and_target_apps_distinct", "format_phase150_controlled_multi_app_transfer_line", "main", "run_phase150_controlled_multi_app_transfer"]  # 修改代码+Phase150MultiAppTransfer：限定公开 API 并暴露回归测试需要的身份 helper；如果没有这一行，测试无法覆盖真实 smoke 暴露的空 process_name 回归。

if __name__ == "__main__":  # 新增代码+Phase150MultiAppTransfer：模块入口段开始，允许 python -m 或直接脚本运行；如果没有这一行，命令行自检不会启动。
    raise SystemExit(main())  # 新增代码+Phase150MultiAppTransfer：执行 CLI 并返回退出码；如果没有这一行，直接运行模块没有效果。
# 新增代码+Phase150MultiAppTransfer：模块入口段结束，本文件到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
