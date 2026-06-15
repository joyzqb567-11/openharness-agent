"""Phase150 controlled live GUI failure recovery benchmark."""  # 新增代码+Phase150FailureRecovery：说明本模块负责受控真实 GUI 失败恢复验收；如果没有这一行，维护者不容易区分它和旧的 contract-only 场景。
from __future__ import annotations  # 新增代码+Phase150FailureRecovery：启用延迟类型解析；如果没有这一行，复杂前向类型在导入时更容易失败。

import hashlib  # 新增代码+Phase150FailureRecovery：导入哈希工具；如果没有这一行，报告只能泄露恢复文本或完全无法关联恢复输入。
import json  # 新增代码+Phase150FailureRecovery：导入 JSON 工具；如果没有这一行，CLI 无法打印结构化脱敏报告。
import os  # 新增代码+Phase150FailureRecovery：导入环境变量工具；如果没有这一行，双门禁无法从真实终端环境读取。
import shutil  # 新增代码+Phase150FailureRecovery：导入浏览器查找工具；如果没有这一行，无法从 PATH 兜底查找 Edge/Chrome。
import subprocess  # 新增代码+Phase150FailureRecovery：导入进程启动工具；如果没有这一行，真实受控 Browser 无法启动。
import sys  # 新增代码+Phase150FailureRecovery：导入平台信息；如果没有这一行，非 Windows 环境可能误调用 Win32 GUI。
import time  # 新增代码+Phase150FailureRecovery：导入等待工具；如果没有这一行，窗口启动、关闭和标题刷新会被过早检查。
from pathlib import Path  # 新增代码+Phase150FailureRecovery：导入路径对象；如果没有这一行，受控运行目录和本地页面路径容易拼错。
from typing import Any  # 新增代码+Phase150FailureRecovery：导入通用类型；如果没有这一行，JSON 风格报告的输入输出边界不清楚。

try:  # 新增代码+Phase150FailureRecovery：优先按包模式导入项目内依赖；如果没有这段代码，单元测试和 python -m 路径无法共享实现。
    from learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # 新增代码+Phase150FailureRecovery：复用 computer_use memory 根路径；如果没有这一行，真实恢复验收可能写到用户目录。
    from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+Phase150FailureRecovery：复用真实 SendInput sender；如果没有这一行，恢复动作只会启动应用而不会触达 GUI。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase150FailureRecovery：复用真实只读窗口枚举；如果没有这一行，动作前后无法复核目标窗口。
except ModuleNotFoundError as error:  # 新增代码+Phase150FailureRecovery：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，真实可见终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants", "learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend"}:  # 新增代码+Phase150FailureRecovery：只兜底包路径缺失；如果没有这一行，依赖内部 bug 会被误吞。
        raise  # 新增代码+Phase150FailureRecovery：重新抛出真正的内部导入错误；如果没有这一行，排查会被错误 fallback 掩盖。
    from computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # type: ignore  # 新增代码+Phase150FailureRecovery：脚本模式复用 memory 根路径；如果没有这一行，bat 入口无法定位受控目录。
    from computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # type: ignore  # 新增代码+Phase150FailureRecovery：脚本模式复用真实 SendInput sender；如果没有这一行，bat 入口无法发真实恢复输入。
    from computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # type: ignore  # 新增代码+Phase150FailureRecovery：脚本模式复用窗口枚举；如果没有这一行，bat 入口无法复核目标窗口。

PHASE150_CONTROLLED_FAILURE_RECOVERY_MARKER = "PHASE150_CONTROLLED_FAILURE_RECOVERY_READY"  # 新增代码+Phase150FailureRecovery：定义 ready marker；如果没有这一行，真实终端验收没有稳定锚点。
PHASE150_CONTROLLED_FAILURE_RECOVERY_OK_TOKEN = "PHASE150_CONTROLLED_FAILURE_RECOVERY_OK"  # 新增代码+Phase150FailureRecovery：定义 OK token；如果没有这一行，Phase148C 场景无法稳定匹配成功。
PHASE150_CONTROLLED_FAILURE_RECOVERY_MODEL = "phase150_controlled_failure_recovery"  # 新增代码+Phase150FailureRecovery：定义模型名；如果没有这一行，报告无法区分本阶段证据版本。
PHASE150_REAL_FAILURE_RECOVERY_ENV = "LEARNING_AGENT_PHASE150_ENABLE_REAL_FAILURE_RECOVERY"  # 新增代码+Phase150FailureRecovery：定义强制启用真实 GUI 的门禁变量；如果没有这一行，真实桌面动作可能被默认打开。
PHASE150_REAL_FAILURE_RECOVERY_REQUEST_ENV = "LEARNING_AGENT_PHASE150_RUN_REAL_FAILURE_RECOVERY"  # 新增代码+Phase150FailureRecovery：定义请求运行真实 GUI 的变量；如果没有这一行，CLI 无法显式表达本次要跑真实验收。
PHASE150_FAILURE_TARGET_TITLE = "PHASE150_FAILURE_RECOVERY_TARGET"  # 新增代码+Phase150FailureRecovery：定义 Browser 目标页初始标题；如果没有这一行，窗口识别没有本阶段专属线索。
PHASE150_FAILURE_OK_TITLE = "PHASE150_FAILURE_RECOVERY_OK"  # 新增代码+Phase150FailureRecovery：定义恢复成功后的标题；如果没有这一行，结果验证只能靠猜测。
PHASE150_FAILURE_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase150FailureRecovery：声明没有扩展到不受控高风险动作；如果没有这一行，成熟度矩阵无法判断安全边界。
DEFAULT_PHASE150_CONTROLLED_FAILURE_RECOVERY_ROOT = DEFAULT_PERSISTENT_GRANTS_ROOT.parent / "post_parity" / "phase150_controlled_failure_recovery"  # 新增代码+Phase150FailureRecovery：定义默认受控运行根目录；如果没有这一行，真实恢复操作可能落到用户目录。


def _phase150_failure_bool_token(value: Any) -> str:  # 新增代码+Phase150FailureRecovery：函数段开始，把布尔值转成小写验收 token；如果没有这段函数，终端输出会混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+Phase150FailureRecovery：返回 true 或 false；如果没有这一行，acceptance controller 字符串匹配会不稳定。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


def _phase150_failure_env_enabled(name: str) -> bool:  # 新增代码+Phase150FailureRecovery：函数段开始，读取环境变量门禁；如果没有这段函数，每个入口都要重复判断字符串真假。
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase150FailureRecovery：只接受明确真值；如果没有这一行，随便设置任意文本也可能打开真实桌面动作。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_env_enabled 到此结束；如果没有这个边界说明，初学者不容易看出门禁解析范围。


def _phase150_failure_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase150FailureRecovery：函数段开始，安全转换 hwnd、pid 和计数；如果没有这段函数，坏窗口字段可能让真实验收崩溃。
    try:  # 新增代码+Phase150FailureRecovery：捕获动态输入的转换异常；如果没有这一行，None 或脏字符串会直接抛错。
        return int(value)  # 新增代码+Phase150FailureRecovery：返回整数；如果没有这一行，SendInput 和 Win32 close 不能使用句柄。
    except Exception:  # 新增代码+Phase150FailureRecovery：把所有转换异常视为安全兜底；如果没有这一行，坏字段会中断 agent。
        return int(default)  # 新增代码+Phase150FailureRecovery：返回默认值；如果没有这一行，调用方要重复写兜底逻辑。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出转换范围。


def _phase150_failure_sha256_16(value: Any) -> str:  # 新增代码+Phase150FailureRecovery：函数段开始，生成短哈希；如果没有这段函数，报告要么泄露恢复文本要么无法审计。
    text = str(value or "")  # 新增代码+Phase150FailureRecovery：把输入规整为字符串；如果没有这一行，None 和数字的哈希会不稳定。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16] if text else ""  # 新增代码+Phase150FailureRecovery：返回 16 位短哈希；如果没有这一行，脱敏关联信息不可用。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。


def _phase150_failure_safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase150FailureRecovery：函数段开始，把动态值规整成字典；如果没有这段函数，driver 坏返回会污染报告。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase150FailureRecovery：只复制 dict；如果没有这一行，None 或字符串会让 .get 调用崩溃。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_safe_dict 到此结束；如果没有这个边界说明，初学者不容易看出字典清洗范围。


def _phase150_failure_window_field(window: Any, field: str) -> Any:  # 新增代码+Phase150FailureRecovery：函数段开始，兼容 dict 和对象窗口字段；如果没有这段函数，测试替身和真实 inventory 会分裂。
    return window.get(field) if isinstance(window, dict) else getattr(window, field, None)  # 新增代码+Phase150FailureRecovery：按类型读取字段；如果没有这一行，窗口摘要 helper 不能复用。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_window_field 到此结束；如果没有这个边界说明，初学者不容易看出字段读取范围。


def _phase150_failure_hwnd_from_window(window: Any) -> int:  # 新增代码+Phase150FailureRecovery：函数段开始，从窗口摘要提取 hwnd；如果没有这段函数，真实 sender 和窗口关闭没有目标句柄。
    direct = _phase150_failure_window_field(window, "hwnd")  # 新增代码+Phase150FailureRecovery：优先读取 hwnd 字段；如果没有这一行，真实 inventory 的系统句柄可能被忽略。
    if direct is not None:  # 新增代码+Phase150FailureRecovery：存在直接句柄时走直接转换；如果没有这一行，后续会误走文本解析。
        return _phase150_failure_safe_int(direct)  # 新增代码+Phase150FailureRecovery：返回直接句柄；如果没有这一行，SetForegroundWindow 无法定位目标应用。
    window_id = str(_phase150_failure_window_field(window, "window_id") or "")  # 新增代码+Phase150FailureRecovery：读取协议窗口 id；如果没有这一行，缺 hwnd 字段时没有兜底来源。
    return _phase150_failure_safe_int(window_id.split(":", 1)[1]) if window_id.startswith("hwnd:") and ":" in window_id else 0  # 新增代码+Phase150FailureRecovery：从 hwnd:123 解析句柄；如果没有这一行，静态和真实窗口 id 无法用于 Win32。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_hwnd_from_window 到此结束；如果没有这个边界说明，初学者不容易看出句柄解析范围。


def _phase150_failure_window_title(window: Any) -> str:  # 新增代码+Phase150FailureRecovery：函数段开始，读取窗口标题摘要；如果没有这段函数，目标匹配会重复处理 title 字段。
    return str(_phase150_failure_window_field(window, "title_preview") or _phase150_failure_window_field(window, "title") or "")  # 新增代码+Phase150FailureRecovery：优先用脱敏标题摘要；如果没有这一行，匹配逻辑可能拿不到标题。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_window_title 到此结束；如果没有这个边界说明，初学者不容易看出标题读取范围。


def _phase150_failure_window_blob(window: Any) -> str:  # 新增代码+Phase150FailureRecovery：函数段开始，拼出窗口身份文本；如果没有这段函数，Browser/危险目标判断会散落。
    fields = ("app_id", "process_name", "class_name", "title_preview", "title", "window_id")  # 新增代码+Phase150FailureRecovery：列出窗口身份字段；如果没有这一行，某些关键线索可能漏检。
    return " ".join(str(_phase150_failure_window_field(window, field) or "") for field in fields).lower()  # 新增代码+Phase150FailureRecovery：合并并小写字段；如果没有这一行，大小写差异会导致误判。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_window_blob 到此结束；如果没有这个边界说明，初学者不容易看出窗口身份范围。


def _phase150_failure_window_key(window: Any) -> str:  # 新增代码+Phase150FailureRecovery：函数段开始，生成窗口身份 key；如果没有这段函数，启动前 baseline 无法过滤旧窗口。
    window_id = str(_phase150_failure_window_field(window, "window_id") or "")  # 新增代码+Phase150FailureRecovery：读取窗口 id；如果没有这一行，无法优先用稳定 hwnd 身份。
    return f"window_id:{window_id}" if window_id else f"pid:{_phase150_failure_safe_int(_phase150_failure_window_field(window, 'pid') or _phase150_failure_window_field(window, 'process_id'))}"  # 新增代码+Phase150FailureRecovery：返回窗口 id 或 pid key；如果没有这一行，baseline 不能识别同一窗口。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_window_key 到此结束；如果没有这个边界说明，初学者不容易看出身份 key 范围。


def _phase150_failure_window_identity(window: Any) -> dict[str, Any]:  # 新增代码+Phase150FailureRecovery：函数段开始，生成不含完整标题的窗口身份摘要；如果没有这段函数，报告可能泄露本地路径或标题文本。
    title = _phase150_failure_window_title(window)  # 新增代码+Phase150FailureRecovery：读取标题用于哈希；如果没有这一行，身份摘要缺少可比对标题线索。
    return {"app_id": str(_phase150_failure_window_field(window, "app_id") or ""), "process_name": str(_phase150_failure_window_field(window, "process_name") or ""), "class_name": str(_phase150_failure_window_field(window, "class_name") or ""), "window_id": str(_phase150_failure_window_field(window, "window_id") or ""), "hwnd": _phase150_failure_hwnd_from_window(window), "pid": _phase150_failure_safe_int(_phase150_failure_window_field(window, "pid") or _phase150_failure_window_field(window, "process_id")), "title_length": len(title), "title_sha256_16": _phase150_failure_sha256_16(title)}  # 新增代码+Phase150FailureRecovery：返回脱敏身份摘要；如果没有这一行，审计无法证明动作前后是同一类受控目标。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_window_identity 到此结束；如果没有这个边界说明，初学者不容易看出窗口身份摘要范围。


def _phase150_failure_is_forbidden_window(window: Any) -> bool:  # 新增代码+Phase150FailureRecovery：函数段开始，识别终端和安全敏感窗口；如果没有这段函数，恢复输入可能发到命令行或认证窗口。
    blob = _phase150_failure_window_blob(window)  # 新增代码+Phase150FailureRecovery：读取统一窗口身份文本；如果没有这一行，危险关键字没有检查对象。
    forbidden = ("powershell", "cmd.exe", "command prompt", "windows terminal", "terminal", "consolewindowclass", "security", "credential", "password", "uac", "defender", "login", "captcha", "codex")  # 新增代码+Phase150FailureRecovery：列出必须零事件拒绝的目标线索；如果没有这一行，终端和安全窗口可能漏过。
    return any(token in blob for token in forbidden)  # 新增代码+Phase150FailureRecovery：命中任一危险线索就拒绝；如果没有这一行，危险窗口不会被统一拦截。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_is_forbidden_window 到此结束；如果没有这个边界说明，初学者不容易看出危险目标范围。


def _phase150_failure_is_browser_target_window(window: Any) -> bool:  # 新增代码+Phase150FailureRecovery：函数段开始，判断窗口是否为本次受控 Browser 目标；如果没有这段函数，恢复输入可能落到用户浏览器。
    blob = _phase150_failure_window_blob(window)  # 新增代码+Phase150FailureRecovery：读取窗口身份文本；如果没有这一行，Browser 和标题线索无法判断。
    browser_like = "msedge" in blob or "chrome" in blob or "edge" in blob or "chrome_widgetwin" in blob  # 新增代码+Phase150FailureRecovery：接受 Edge/Chrome/Chromium 窗口线索；如果没有这一行，真实浏览器窗口可能识别失败。
    title_hint = PHASE150_FAILURE_TARGET_TITLE.lower() in blob or PHASE150_FAILURE_OK_TITLE.lower() in blob  # 新增代码+Phase150FailureRecovery：要求标题含本次本地页面线索；如果没有这一行，用户日常浏览器窗口可能被误用。
    return bool(browser_like and title_hint and not _phase150_failure_is_forbidden_window(window))  # 新增代码+Phase150FailureRecovery：目标窗口必须同时满足浏览器、标题和安全边界；如果没有这一行，恢复目标不可信。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_is_browser_target_window 到此结束；如果没有这个边界说明，初学者不容易看出目标窗口匹配范围。


def _phase150_failure_snapshot_windows(window_probe: Any) -> list[Any]:  # 新增代码+Phase150FailureRecovery：函数段开始，读取当前安全窗口列表；如果没有这段函数，真实和测试 probe 接口差异会分裂。
    snapshot = window_probe.snapshot() if hasattr(window_probe, "snapshot") else window_probe  # 新增代码+Phase150FailureRecovery：优先调用 snapshot；如果没有这一行，真实 WindowsWindowInventoryProbe 不会枚举窗口。
    return list(getattr(snapshot, "windows", snapshot.get("windows", []) if isinstance(snapshot, dict) else []))  # 新增代码+Phase150FailureRecovery：兼容对象和 dict 快照；如果没有这一行，fake snapshot 无法用于测试。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_snapshot_windows 到此结束；如果没有这个边界说明，初学者不容易看出窗口读取范围。


def _phase150_failure_window_center(window: Any, *, y_ratio: float = 0.58) -> dict[str, int]:  # 新增代码+Phase150FailureRecovery：函数段开始，计算窗口内部点击点；如果没有这段函数，真实点击可能落到地址栏或边框。
    rect = _phase150_failure_safe_dict(_phase150_failure_window_field(window, "rect"))  # 新增代码+Phase150FailureRecovery：读取窗口矩形；如果没有这一行，坐标没有边界来源。
    left = _phase150_failure_safe_int(rect.get("left"))  # 新增代码+Phase150FailureRecovery：读取左边界；如果没有这一行，x 坐标无法计算。
    top = _phase150_failure_safe_int(rect.get("top"))  # 新增代码+Phase150FailureRecovery：读取上边界；如果没有这一行，y 坐标无法计算。
    right = _phase150_failure_safe_int(rect.get("right")) or left + 900  # 新增代码+Phase150FailureRecovery：读取右边界并兜底宽度；如果没有这一行，缺 rect 时会得到零宽区域。
    bottom = _phase150_failure_safe_int(rect.get("bottom")) or top + 650  # 新增代码+Phase150FailureRecovery：读取下边界并兜底高度；如果没有这一行，缺 rect 时会得到零高区域。
    return {"x": left + max(80, (right - left) // 2), "y": top + max(80, int((bottom - top) * float(y_ratio)))}  # 新增代码+Phase150FailureRecovery：返回页面内容区偏中心点；如果没有这一行，textarea 可能拿不到焦点。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_window_center 到此结束；如果没有这个边界说明，初学者不容易看出点击点范围。


def _phase150_failure_browser_executable() -> str:  # 新增代码+Phase150FailureRecovery：函数段开始，查找本机可用浏览器；如果没有这段函数，真实验收只能依赖 PATH。
    candidates = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]  # 新增代码+Phase150FailureRecovery：列出常见 Edge/Chrome 安装路径；如果没有这一行，普通 Windows 安装可能找不到浏览器。
    for candidate in candidates:  # 新增代码+Phase150FailureRecovery：逐个检查固定路径；如果没有这一行，候选路径不会被使用。
        if Path(candidate).exists():  # 新增代码+Phase150FailureRecovery：确认文件存在；如果没有这一行，Popen 会收到不存在路径。
            return candidate  # 新增代码+Phase150FailureRecovery：返回第一个可用浏览器；如果没有这一行，找到也无法启动。
    return str(shutil.which("msedge") or shutil.which("chrome") or "")  # 新增代码+Phase150FailureRecovery：兜底查 PATH；如果没有这一行，便携或 PATH 浏览器无法被使用。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_browser_executable 到此结束；如果没有这个边界说明，初学者不容易看出浏览器发现范围。


def _phase150_failure_write_page(run_root: Path, recovery_text: str) -> Path:  # 新增代码+Phase150FailureRecovery：函数段开始，写入受控本地 Browser 目标页；如果没有这段函数，恢复目标会依赖外网或用户 profile。
    page_path = run_root / "phase150_failure_recovery_target.html"  # 新增代码+Phase150FailureRecovery：定义本地页面路径；如果没有这一行，浏览器没有稳定受控目标。
    html_text = f"""<!doctype html><html><head><meta charset='utf-8'><title>{PHASE150_FAILURE_TARGET_TITLE}</title><style>html,body{{margin:0;width:100%;height:100%;font-family:Arial,sans-serif;background:#f7fafc;}}textarea{{box-sizing:border-box;width:100vw;height:78vh;margin-top:12vh;border:0;padding:32px;font-size:30px;outline:0;background:#ffffff;color:#172033;}}#status{{position:fixed;left:0;top:0;right:0;height:12vh;background:#1d4ed8;color:white;font-size:28px;display:flex;align-items:center;justify-content:center;}}</style></head><body><div id='status'>PHASE150 FAILURE TARGET READY</div><textarea id='target' autofocus spellcheck='false'></textarea><script>const expected={json.dumps(recovery_text)};const target=document.getElementById('target');const status=document.getElementById('status');function update(){{if(target.value.indexOf(expected)!==-1){{document.title='{PHASE150_FAILURE_OK_TITLE}';status.textContent='PHASE150 FAILURE RECOVERY VERIFIED';document.body.setAttribute('data-recovery','ok');}}}}target.addEventListener('input',update);window.addEventListener('load',()=>target.focus());</script></body></html>"""  # 新增代码+Phase150FailureRecovery：生成只接受受控恢复文本的本地页面；如果没有这一行，恢复后没有可观察成功标题。
    page_path.write_text(html_text, encoding="utf-8")  # 新增代码+Phase150FailureRecovery：写入本地页面文件；如果没有这一行，浏览器无法加载目标页面。
    return page_path  # 新增代码+Phase150FailureRecovery：返回页面路径；如果没有这一行，启动命令拿不到 URL。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_write_page 到此结束；如果没有这个边界说明，初学者不容易看出本地页面范围。


class Phase150WindowsFailureRecoveryDriver:  # 新增代码+Phase150FailureRecovery：类段开始，执行受控 Browser 目标失效后重新获取并恢复的真实 GUI 闭环；如果没有这个类，failure_recovery 没有真实 driver。
    def __init__(self, window_probe: Any | None = None, sender: Any | None = None, timeout_seconds: float = 16.0) -> None:  # 新增代码+Phase150FailureRecovery：函数段开始，注入或创建真实依赖；如果没有这段函数，单测无法替换依赖且生产路径无法启动。
        self.window_probe = window_probe if window_probe is not None else WindowsWindowInventoryProbe()  # 新增代码+Phase150FailureRecovery：保存窗口枚举器；如果没有这一行，driver 找不到受控 Browser。
        self.sender = sender if sender is not None else WindowsSendInputLowLevelSender()  # 新增代码+Phase150FailureRecovery：保存真实 SendInput sender；如果没有这一行，恢复输入无法触达桌面。
        self.timeout_seconds = max(2.0, float(timeout_seconds))  # 新增代码+Phase150FailureRecovery：保存并限制最小超时；如果没有这一行，窗口轮询可能立即失败。
    # 新增代码+Phase150FailureRecovery：函数段结束，Phase150WindowsFailureRecoveryDriver.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出依赖初始化范围。

    def _wait_for_window(self, matcher: Any, baseline_keys: set[str]) -> dict[str, Any] | None:  # 新增代码+Phase150FailureRecovery：函数段开始，等待目标窗口出现；如果没有这段函数，异步浏览器启动会误判失败。
        deadline = time.time() + self.timeout_seconds  # 新增代码+Phase150FailureRecovery：计算超时截止时间；如果没有这一行，等待可能无限持续。
        while time.time() <= deadline:  # 新增代码+Phase150FailureRecovery：在超时前持续轮询；如果没有这一行，窗口启动延迟无法等待。
            candidates = [dict(window) for window in _phase150_failure_snapshot_windows(self.window_probe) if matcher(window)]  # 新增代码+Phase150FailureRecovery：筛选安全候选窗口；如果没有这一行，目标可能是任意窗口。
            fresh = [window for window in candidates if _phase150_failure_window_key(window) not in baseline_keys]  # 新增代码+Phase150FailureRecovery：优先选择启动后新增窗口；如果没有这一行，旧窗口可能被误用。
            if fresh or candidates:  # 新增代码+Phase150FailureRecovery：检查是否已有可用候选；如果没有这一行，找到也不会返回。
                return dict((fresh or candidates)[0])  # 新增代码+Phase150FailureRecovery：返回第一个安全候选；如果没有这一行，调用方拿不到窗口。
            time.sleep(0.25)  # 新增代码+Phase150FailureRecovery：短暂等待后重试；如果没有这一行，轮询会占满 CPU。
        return None  # 新增代码+Phase150FailureRecovery：超时返回定位失败；如果没有这一行，调用方无法诚实报告窗口未找到。
    # 新增代码+Phase150FailureRecovery：函数段结束，Phase150WindowsFailureRecoveryDriver._wait_for_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口等待范围。

    def _wait_until_window_missing(self, window: dict[str, Any]) -> bool:  # 新增代码+Phase150FailureRecovery：函数段开始，等待被故意关闭的目标从 inventory 消失；如果没有这段函数，失败观察只能靠猜测。
        target_key = _phase150_failure_window_key(window)  # 新增代码+Phase150FailureRecovery：记录要消失的窗口身份；如果没有这一行，等待时不知道检查哪个窗口。
        deadline = time.time() + self.timeout_seconds  # 新增代码+Phase150FailureRecovery：计算超时截止时间；如果没有这一行，等待可能无限持续。
        while time.time() <= deadline:  # 新增代码+Phase150FailureRecovery：在超时前持续轮询；如果没有这一行，窗口关闭延迟无法等待。
            still_present = any(_phase150_failure_window_key(candidate) == target_key for candidate in _phase150_failure_snapshot_windows(self.window_probe))  # 新增代码+Phase150FailureRecovery：检查原窗口是否仍在；如果没有这一行，失败观察没有事实来源。
            if not still_present:  # 新增代码+Phase150FailureRecovery：窗口已经消失时说明失败可观察；如果没有这一行，成功消失也会继续等待。
                return True  # 新增代码+Phase150FailureRecovery：返回失败已观察；如果没有这一行，调用方无法进入恢复阶段。
            time.sleep(0.25)  # 新增代码+Phase150FailureRecovery：短暂等待后重试；如果没有这一行，轮询会占满 CPU。
        return False  # 新增代码+Phase150FailureRecovery：超时仍存在则返回失败未观察；如果没有这一行，调用方无法诚实拒绝。
    # 新增代码+Phase150FailureRecovery：函数段结束，Phase150WindowsFailureRecoveryDriver._wait_until_window_missing 到此结束；如果没有这个边界说明，初学者不容易看出失败观察范围。

    def _send_events(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase150FailureRecovery：函数段开始，统一调用底层 sender；如果没有这段函数，发送结果解析会散落在 run 里。
        return _phase150_failure_safe_dict(self.sender.send_low_level(events))  # 新增代码+Phase150FailureRecovery：发送事件并清洗返回字典；如果没有这一行，坏 sender 输出会让 driver 崩溃。
    # 新增代码+Phase150FailureRecovery：函数段结束，Phase150WindowsFailureRecoveryDriver._send_events 到此结束；如果没有这个边界说明，初学者不容易看出发送范围。

    def _close_window(self, window: dict[str, Any] | None) -> bool:  # 新增代码+Phase150FailureRecovery：函数段开始，关闭本次受控窗口；如果没有这段函数，初始失败窗口或恢复窗口可能残留。
        hwnd = _phase150_failure_hwnd_from_window(window or {})  # 新增代码+Phase150FailureRecovery：读取窗口句柄；如果没有这一行，Win32 无法定位关闭目标。
        if hwnd <= 0 or sys.platform != "win32":  # 新增代码+Phase150FailureRecovery：没有有效句柄或非 Windows 时不调用系统 API；如果没有这一行，测试或跨平台会误触系统调用。
            return False  # 新增代码+Phase150FailureRecovery：无法关闭时返回 False；如果没有这一行，cleanup 会虚报。
        try:  # 新增代码+Phase150FailureRecovery：保护 Win32 关闭调用；如果没有这一行，关闭失败会中断报告生成。
            import ctypes  # 新增代码+Phase150FailureRecovery：延迟导入 ctypes 调 user32；如果没有这一行，无法发送 WM_CLOSE。
            return bool(ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0))  # 新增代码+Phase150FailureRecovery：向受控窗口发送 WM_CLOSE；如果没有这一行，窗口不会被请求关闭。
        except Exception:  # 新增代码+Phase150FailureRecovery：捕获关闭异常；如果没有这一行，cleanup 失败会掩盖主要证据。
            return False  # 新增代码+Phase150FailureRecovery：关闭异常时返回 False；如果没有这一行，调用方无法知道清理不完整。
    # 新增代码+Phase150FailureRecovery：函数段结束，Phase150WindowsFailureRecoveryDriver._close_window 到此结束；如果没有这个边界说明，初学者不容易看出关闭范围。

    def _launch_browser(self, run_root: Path, page_path: Path, profile_name: str) -> subprocess.Popen[Any] | None:  # 新增代码+Phase150FailureRecovery：函数段开始，启动隔离 Browser 目标；如果没有这段函数，run 主流程会重复拼接命令。
        browser_exe = _phase150_failure_browser_executable()  # 新增代码+Phase150FailureRecovery：查找浏览器程序；如果没有这一行，目标应用无法启动。
        if not browser_exe:  # 新增代码+Phase150FailureRecovery：没有浏览器时停止启动；如果没有这一行，Popen 会收到空命令。
            return None  # 新增代码+Phase150FailureRecovery：返回无法启动；如果没有这一行，调用方无法报告 browser_missing。
        command = [browser_exe, f"--user-data-dir={run_root / profile_name}", "--no-first-run", "--disable-first-run-ui", "--new-window", page_path.resolve().as_uri()]  # 新增代码+Phase150FailureRecovery：构造隔离 profile 的本地页面命令；如果没有这一行，可能误用用户日常浏览器 profile。
        return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) if sys.platform == "win32" else None  # 新增代码+Phase150FailureRecovery：只在 Windows 启动真实 Browser；如果没有这一行，非 Windows 会误报真实 GUI。
    # 新增代码+Phase150FailureRecovery：函数段结束，Phase150WindowsFailureRecoveryDriver._launch_browser 到此结束；如果没有这个边界说明，初学者不容易看出浏览器启动范围。

    def _recover_into_browser(self, window: dict[str, Any], recovery_text: str) -> dict[str, Any]:  # 新增代码+Phase150FailureRecovery：函数段开始，用真实 GUI 在重新获取的 Browser 中输入恢复文本；如果没有这段函数，恢复没有实际动作。
        center = _phase150_failure_window_center(window, y_ratio=0.58)  # 新增代码+Phase150FailureRecovery：计算 Browser 页面 textarea 点击点；如果没有这一行，文本可能落到地址栏。
        events = [{"type": "set_foreground", "hwnd": _phase150_failure_hwnd_from_window(window)}, {"type": "pause", "seconds": 0.35}, {"type": "mouse_move", "x": center["x"], "y": center["y"]}, {"type": "mouse_down", "button": "left"}, {"type": "mouse_up", "button": "left"}, {"type": "pause", "seconds": 0.12}, {"type": "unicode_text", "text": recovery_text}, {"type": "pause", "seconds": 0.50}]  # 新增代码+Phase150FailureRecovery：定义真实点击并输入恢复文本事件；如果没有这一行，目标页面不会收到恢复动作。
        return self._send_events(events)  # 新增代码+Phase150FailureRecovery：发送恢复事件并返回结果；如果没有这一行，调用方拿不到低层事件证据。
    # 新增代码+Phase150FailureRecovery：函数段结束，Phase150WindowsFailureRecoveryDriver._recover_into_browser 到此结束；如果没有这个边界说明，初学者不容易看出恢复输入范围。

    def _wait_for_recovery_success(self) -> dict[str, Any] | None:  # 新增代码+Phase150FailureRecovery：函数段开始，等待 Browser 标题变成恢复成功状态；如果没有这段函数，恢复结果无法机器验证。
        deadline = time.time() + self.timeout_seconds  # 新增代码+Phase150FailureRecovery：计算结果等待截止时间；如果没有这一行，等待可能无限持续。
        while time.time() <= deadline:  # 新增代码+Phase150FailureRecovery：在超时前轮询窗口标题；如果没有这一行，页面 JS 异步更新无法等待。
            for window in _phase150_failure_snapshot_windows(self.window_probe):  # 新增代码+Phase150FailureRecovery：遍历当前窗口；如果没有这一行，无法寻找成功 Browser。
                if _phase150_failure_is_browser_target_window(window) and PHASE150_FAILURE_OK_TITLE.lower() in _phase150_failure_window_blob(window):  # 新增代码+Phase150FailureRecovery：要求仍是受控 Browser 且标题含成功 token；如果没有这一行，恢复结果可能虚报。
                    return dict(window)  # 新增代码+Phase150FailureRecovery：返回成功窗口；如果没有这一行，调用方拿不到结果身份。
            time.sleep(0.25)  # 新增代码+Phase150FailureRecovery：短暂等待后重试；如果没有这一行，轮询会占满 CPU。
        return None  # 新增代码+Phase150FailureRecovery：超时返回 None；如果没有这一行，失败路径无法明确。
    # 新增代码+Phase150FailureRecovery：函数段结束，Phase150WindowsFailureRecoveryDriver._wait_for_recovery_success 到此结束；如果没有这个边界说明，初学者不容易看出结果等待范围。

    def run(self, *, run_root: Path, recovery_text: str) -> dict[str, Any]:  # 新增代码+Phase150FailureRecovery：函数段开始，执行完整真实失败恢复闭环；如果没有这段代码，failure_recovery 无法从契约提升到真实 GUI。
        run_root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase150FailureRecovery：确保运行根目录存在；如果没有这一行，受控页面和 profile 无法创建。
        page_path = _phase150_failure_write_page(run_root, recovery_text)  # 新增代码+Phase150FailureRecovery：写入受控 Browser 目标页；如果没有这一行，恢复目标没有可验证输入区域。
        initial_baseline = {_phase150_failure_window_key(window) for window in _phase150_failure_snapshot_windows(self.window_probe) if _phase150_failure_is_browser_target_window(window)}  # 新增代码+Phase150FailureRecovery：记录启动前同名 Browser；如果没有这一行，旧窗口可能混入本次初始目标。
        initial_process = self._launch_browser(run_root, page_path, "browser_profile_initial")  # 新增代码+Phase150FailureRecovery：启动第一次受控 Browser；如果没有这一行，无法制造目标失效。
        initial_window = self._wait_for_window(_phase150_failure_is_browser_target_window, initial_baseline)  # 新增代码+Phase150FailureRecovery：等待并复核初始受控目标；如果没有这一行，关闭动作可能发到错误窗口。
        if initial_window is None:  # 新增代码+Phase150FailureRecovery：初始目标缺失就停止；如果没有这一行，后续失败制造没有对象。
            return {"ok": False, "driver": "phase150_windows_failure_recovery_driver", "reason": "initial_browser_window_not_found", "controlled_failure_injected": False, "recoverable_failure_observed": False, "recovery_plan_executed": False, "target_reacquired_after_failure": False, "target_rechecked_before_recovery": False, "target_rechecked_before_result": False, "state_changed_after_recovery": False, "cleanup_evidence": {"cleanup_completed": False, "host_hidden_or_restored": False, "lock_released": True}, "real_desktop_touched": False, "physical_desktop_dispatch_performed": False, "real_sendinput_dispatch": False, "sender_kind": "", "low_level_event_count": 0, "raw_text_included": False}  # 新增代码+Phase150FailureRecovery：返回零事件定位失败报告；如果没有这一行，失败点不可审计。
        close_requested = self._close_window(initial_window)  # 新增代码+Phase150FailureRecovery：故意关闭初始目标制造可恢复失败；如果没有这一行，任务不会经历失败。
        recoverable_failure_observed = self._wait_until_window_missing(initial_window)  # 新增代码+Phase150FailureRecovery：观察初始窗口确实消失；如果没有这一行，恢复不是基于真实失败。
        if initial_process is not None and initial_process.poll() is None and not recoverable_failure_observed:  # 新增代码+Phase150FailureRecovery：如果窗口仍未消失且进程还在，准备兜底终止；如果没有这一行，失败注入可能留下窗口。
            initial_process.terminate()  # 新增代码+Phase150FailureRecovery：兜底终止本次初始 Browser 进程；如果没有这一行，受控失败窗口可能残留。
            recoverable_failure_observed = self._wait_until_window_missing(initial_window)  # 新增代码+Phase150FailureRecovery：终止后再次观察窗口消失；如果没有这一行，兜底关闭没有验证。
        recovery_baseline = {_phase150_failure_window_key(window) for window in _phase150_failure_snapshot_windows(self.window_probe) if _phase150_failure_is_browser_target_window(window)}  # 新增代码+Phase150FailureRecovery：记录恢复前同名 Browser；如果没有这一行，恢复目标可能误用残留窗口。
        recovery_process = self._launch_browser(run_root, page_path, "browser_profile_recovery") if recoverable_failure_observed else None  # 新增代码+Phase150FailureRecovery：只在观察到失败后启动恢复目标；如果没有这一行，未确认失败也可能继续误报恢复。
        recovery_window = self._wait_for_window(_phase150_failure_is_browser_target_window, recovery_baseline) if recovery_process is not None else None  # 新增代码+Phase150FailureRecovery：等待并复核恢复目标；如果没有这一行，恢复输入可能发到错误窗口。
        if recovery_window is None:  # 新增代码+Phase150FailureRecovery：恢复目标缺失时停止；如果没有这一行，后续输入会没有安全目标。
            return {"ok": False, "driver": "phase150_windows_failure_recovery_driver", "reason": "recovery_browser_window_not_found", "controlled_failure_injected": bool(close_requested), "recoverable_failure_observed": bool(recoverable_failure_observed), "recovery_plan_executed": False, "target_reacquired_after_failure": False, "target_rechecked_before_recovery": False, "target_rechecked_before_result": False, "state_changed_after_recovery": False, "cleanup_evidence": {"cleanup_completed": False, "host_hidden_or_restored": False, "lock_released": True}, "real_desktop_touched": False, "physical_desktop_dispatch_performed": False, "real_sendinput_dispatch": False, "sender_kind": "", "low_level_event_count": 0, "raw_text_included": False}  # 新增代码+Phase150FailureRecovery：返回恢复目标缺失报告；如果没有这一行，失败点不可审计。
        recovery_result = self._recover_into_browser(recovery_window, recovery_text)  # 新增代码+Phase150FailureRecovery：对重新获取的目标执行真实恢复输入；如果没有这一行，恢复没有物理动作。
        result_window = self._wait_for_recovery_success()  # 新增代码+Phase150FailureRecovery：等待页面标题确认恢复成功；如果没有这一行，恢复结果没有机器验证。
        recovery_closed = self._close_window(result_window or recovery_window)  # 新增代码+Phase150FailureRecovery：关闭本次恢复 Browser 目标窗口；如果没有这一行，目标窗口可能残留桌面。
        if recovery_process is not None and recovery_process.poll() is None and not recovery_closed:  # 新增代码+Phase150FailureRecovery：如果 WM_CLOSE 未关闭恢复 Browser 且进程仍在，准备兜底终止；如果没有这一行，失败清理可能留下进程。
            recovery_process.terminate()  # 新增代码+Phase150FailureRecovery：兜底终止本次恢复 Browser 进程；如果没有这一行，目标应用可能残留。
        low_level_event_count = _phase150_failure_safe_int(recovery_result.get("low_level_event_count"))  # 新增代码+Phase150FailureRecovery：读取恢复阶段低层事件数；如果没有这一行，物理派发判断缺少计数。
        sender_kind = str(recovery_result.get("sender_kind") or recovery_result.get("sender") or type(self.sender).__name__)  # 新增代码+Phase150FailureRecovery：提取 sender 身份；如果没有这一行，fake sender 可能误入成熟矩阵。
        physical_dispatch = bool(low_level_event_count > 0 and "windows_sendinput" in sender_kind.lower() and "fake" not in sender_kind.lower() and "record" not in sender_kind.lower() and recovery_result.get("ok"))  # 新增代码+Phase150FailureRecovery：判断是否真实 SendInput 物理派发；如果没有这一行，空动作或 fake sender 可能误过。
        state_changed = bool(result_window is not None)  # 新增代码+Phase150FailureRecovery：确认目标页面标题显示恢复成功；如果没有这一行，恢复结果没有布尔结论。
        ok = bool(close_requested and recoverable_failure_observed and physical_dispatch and state_changed and recovery_closed)  # 新增代码+Phase150FailureRecovery：汇总 driver 成功条件；如果没有这一行，部分成功可能被误判完整闭环。
        return {"ok": ok, "driver": "phase150_windows_failure_recovery_driver", "reason": "" if ok else "failure_recovery_not_fully_verified", "controlled_failure_injected": bool(close_requested), "recoverable_failure_observed": bool(recoverable_failure_observed), "recovery_plan_executed": True, "target_reacquired_after_failure": True, "target_rechecked_before_recovery": True, "target_rechecked_before_result": state_changed, "state_changed_after_recovery": state_changed, "cleanup_evidence": {"cleanup_completed": bool(recovery_closed), "host_hidden_or_restored": bool(recovery_closed), "lock_released": True}, "real_desktop_touched": bool(low_level_event_count), "physical_desktop_dispatch_performed": physical_dispatch, "real_sendinput_dispatch": physical_dispatch, "sender_kind": sender_kind, "low_level_event_count": low_level_event_count, "raw_text_included": False, "initial_window": _phase150_failure_window_identity(initial_window), "recovery_window": _phase150_failure_window_identity(result_window or recovery_window), "recovery_text_length": len(recovery_text), "recovery_text_sha256_16": _phase150_failure_sha256_16(recovery_text)}  # 新增代码+Phase150FailureRecovery：返回脱敏闭环报告；如果没有这一行，Phase148C 拿不到 failure_recovery 真实 GUI 证据。
    # 新增代码+Phase150FailureRecovery：函数段结束，Phase150WindowsFailureRecoveryDriver.run 到此结束；如果没有这个边界说明，初学者不容易看出 driver 主流程范围。
# 新增代码+Phase150FailureRecovery：类段结束，Phase150WindowsFailureRecoveryDriver 到此结束；如果没有这个边界说明，初学者不容易看出真实 driver 范围。


def _phase150_failure_default_off_report() -> dict[str, Any]:  # 新增代码+Phase150FailureRecovery：函数段开始，构造默认关闭报告；如果没有这段函数，普通运行无法证明 0 物理事件。
    return {"decision": "real_failure_recovery_disabled_by_default", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase150FailureRecovery：返回零事件默认报告；如果没有这一行，默认安全边界无证据。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_default_off_report 到此结束；如果没有这个边界说明，初学者不容易看出默认安全范围。


def _phase150_failure_unsafe_target_report() -> dict[str, Any]:  # 新增代码+Phase150FailureRecovery：函数段开始，构造危险目标拒绝报告；如果没有这段函数，敏感窗口零事件边界无证据。
    return {"decision": "unsafe_target_rejected", "target": "terminal_like_window", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase150FailureRecovery：返回终端类目标零事件拒绝；如果没有这一行，安全门禁可能被误削弱。
# 新增代码+Phase150FailureRecovery：函数段结束，_phase150_failure_unsafe_target_report 到此结束；如果没有这个边界说明，初学者不容易看出危险目标范围。


def run_phase150_controlled_failure_recovery(real_run_requested: bool | None = None, real_enable_gate: bool | None = None, run_root: str | Path | None = None, driver: Any | None = None, require_injected_driver: bool = False, raw_prompt_text: str | None = None) -> dict[str, Any]:  # 新增代码+Phase150FailureRecovery：函数段开始，运行 Phase150 失败恢复总合同入口；如果没有这段函数，测试、CLI 和 Phase148C 无法共用事实源。
    requested = _phase150_failure_env_enabled(PHASE150_REAL_FAILURE_RECOVERY_REQUEST_ENV) if real_run_requested is None else bool(real_run_requested)  # 新增代码+Phase150FailureRecovery：读取是否请求真实运行；如果没有这一行，环境变量门禁不会生效。
    gate_enabled = _phase150_failure_env_enabled(PHASE150_REAL_FAILURE_RECOVERY_ENV) if real_enable_gate is None else bool(real_enable_gate)  # 新增代码+Phase150FailureRecovery：读取真实 GUI 强门禁；如果没有这一行，单个变量可能误开桌面动作。
    root = Path(run_root) if run_root is not None else DEFAULT_PHASE150_CONTROLLED_FAILURE_RECOVERY_ROOT  # 新增代码+Phase150FailureRecovery：确定受控运行根目录；如果没有这一行，真实恢复操作没有边界。
    recovery_text = f"PHASE150_FAILURE_RECOVERY_PAYLOAD_{time.time_ns()}"  # 新增代码+Phase150FailureRecovery：生成纳秒级唯一的本次受控恢复文本；如果没有这一行，快速连续验收可能拿到相同文本并降低证据唯一性。
    default_report = _phase150_failure_default_off_report()  # 新增代码+Phase150FailureRecovery：生成默认关闭证据；如果没有这一行，报告缺默认 0 事件门禁。
    unsafe_report = _phase150_failure_unsafe_target_report()  # 新增代码+Phase150FailureRecovery：生成危险目标拒绝证据；如果没有这一行，报告缺敏感窗口保护事实。
    default_zero = bool(default_report.get("low_level_event_count") == 0 and not default_report.get("real_desktop_touched"))  # 新增代码+Phase150FailureRecovery：确认默认关闭零事件；如果没有这一行，默认安全状态无法量化。
    unsafe_zero = bool(unsafe_report.get("low_level_event_count") == 0 and not unsafe_report.get("real_desktop_touched"))  # 新增代码+Phase150FailureRecovery：确认危险目标零事件；如果没有这一行，敏感窗口保护无法量化。
    selected_driver = driver if driver is not None else (Phase150WindowsFailureRecoveryDriver() if requested and gate_enabled and not require_injected_driver else None)  # 新增代码+Phase150FailureRecovery：只有请求且门禁通过时才创建真实 driver；如果没有这一行，普通调用可能触碰桌面。
    driver_report = _phase150_failure_safe_dict(selected_driver.run(run_root=root, recovery_text=recovery_text)) if selected_driver is not None else {}  # 新增代码+Phase150FailureRecovery：执行 driver 或保持空报告；如果没有这一行，真实路径不会产生证据。
    cleanup_evidence = _phase150_failure_safe_dict(driver_report.get("cleanup_evidence"))  # 新增代码+Phase150FailureRecovery：读取 driver 清理证据；如果没有这一行，cleanup_completed 无法汇总。
    real_executed = bool(requested and gate_enabled and selected_driver is not None and driver_report)  # 新增代码+Phase150FailureRecovery：确认真实恢复路径是否执行；如果没有这一行，报告无法区分未请求和失败。
    real_desktop_touched = bool(driver_report.get("real_desktop_touched"))  # 新增代码+Phase150FailureRecovery：读取真实桌面触达事实；如果没有这一行，物理派发 token 无法生成。
    real_gui_backing = bool(driver_report.get("physical_desktop_dispatch_performed") and driver_report.get("real_sendinput_dispatch") and str(driver_report.get("sender_kind", "")).lower().find("windows_sendinput") >= 0)  # 新增代码+Phase150FailureRecovery：确认真实 GUI 背书来自 SendInput；如果没有这一行，fake driver 可能被误认为生产真实路径。
    report_without_raw_check: dict[str, Any] = {"marker": PHASE150_CONTROLLED_FAILURE_RECOVERY_MARKER, "ok_token": PHASE150_CONTROLLED_FAILURE_RECOVERY_OK_TOKEN, "model": PHASE150_CONTROLLED_FAILURE_RECOVERY_MODEL, "family": "failure_recovery", "failure_recovery": bool(driver_report.get("ok")), "real_failure_recovery_env": PHASE150_REAL_FAILURE_RECOVERY_ENV, "real_failure_recovery_request_env": PHASE150_REAL_FAILURE_RECOVERY_REQUEST_ENV, "real_run_requested": requested, "real_enable_gate_required": True, "real_enable_gate_passed": gate_enabled, "require_injected_driver": bool(require_injected_driver), "recovery_text_length": len(recovery_text), "recovery_text_sha256_16": _phase150_failure_sha256_16(recovery_text), "default_off_zero_physical_events": default_zero, "unsafe_target_zero_physical_events": unsafe_zero, "real_failure_recovery_executed": real_executed, "controlled_failure_injected": bool(driver_report.get("controlled_failure_injected")), "recoverable_failure_observed": bool(driver_report.get("recoverable_failure_observed")), "recovery_plan_executed": bool(driver_report.get("recovery_plan_executed")), "target_reacquired_after_failure": bool(driver_report.get("target_reacquired_after_failure")), "target_rechecked_before_recovery": bool(driver_report.get("target_rechecked_before_recovery")), "target_rechecked_before_result": bool(driver_report.get("target_rechecked_before_result")), "state_changed_after_recovery": bool(driver_report.get("state_changed_after_recovery")), "cleanup_completed": bool(cleanup_evidence.get("cleanup_completed")), "real_desktop_touched": real_desktop_touched, "uncontrolled_actions_expanded": PHASE150_FAILURE_UNCONTROLLED_ACTIONS_EXPANDED, "driver": str(driver_report.get("driver", "")), "driver_ok": bool(driver_report.get("ok")), "driver_reason": str(driver_report.get("reason", "")), "default_off_report": default_report, "unsafe_report": unsafe_report}  # 新增代码+Phase150FailureRecovery：构造脱敏报告主体；如果没有这一行，测试和 CLI 会丢失关键事实。
    serialized = json.dumps(report_without_raw_check, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase150FailureRecovery：序列化报告用于检查原文泄露；如果没有这一行，嵌套字段里的泄露可能漏检。
    raw_text_hidden = bool(recovery_text not in serialized and (not raw_prompt_text or raw_prompt_text not in serialized) and not driver_report.get("raw_text_included"))  # 新增代码+Phase150FailureRecovery：确认恢复明文和用户原始 prompt 未进入报告；如果没有这一行，验收 artifact 可能泄露文本。
    passed = bool(default_zero and unsafe_zero and raw_text_hidden and not PHASE150_FAILURE_UNCONTROLLED_ACTIONS_EXPANDED and ((not requested and not real_desktop_touched) or (requested and gate_enabled and real_executed and report_without_raw_check["controlled_failure_injected"] and report_without_raw_check["recoverable_failure_observed"] and report_without_raw_check["recovery_plan_executed"] and report_without_raw_check["target_reacquired_after_failure"] and report_without_raw_check["target_rechecked_before_recovery"] and report_without_raw_check["target_rechecked_before_result"] and report_without_raw_check["state_changed_after_recovery"] and report_without_raw_check["cleanup_completed"] and real_gui_backing)))  # 新增代码+Phase150FailureRecovery：汇总合同通过条件；如果没有这一行，main 无法用退出码表达真实失败恢复闭环是否完成。
    return {**report_without_raw_check, "passed": passed, "real_gui_backing": real_gui_backing, "raw_text_hidden": raw_text_hidden, "driver_report": driver_report}  # 新增代码+Phase150FailureRecovery：返回完整脱敏报告；如果没有这一行，测试和 CLI 拿不到最终结论。
# 新增代码+Phase150FailureRecovery：函数段结束，run_phase150_controlled_failure_recovery 到此结束；如果没有这个边界说明，初学者不容易看出合同入口范围。


def format_phase150_controlled_failure_recovery_line(report: dict[str, Any]) -> str:  # 新增代码+Phase150FailureRecovery：函数段开始，把报告格式化成可见终端稳定 token 行；如果没有这段函数，scenario 只能解析 JSON。
    ok_token = f" {PHASE150_CONTROLLED_FAILURE_RECOVERY_OK_TOKEN}" if report.get("passed") else ""  # 新增代码+Phase150FailureRecovery：只有通过时输出 OK token；如果没有这一行，失败也可能被验收当成功。
    return f"{PHASE150_CONTROLLED_FAILURE_RECOVERY_MARKER}{ok_token} family=failure_recovery failure_recovery={_phase150_failure_bool_token(report.get('failure_recovery'))} default_off_zero_physical_events={_phase150_failure_bool_token(report.get('default_off_zero_physical_events'))} unsafe_target_zero_physical_events={_phase150_failure_bool_token(report.get('unsafe_target_zero_physical_events'))} real_failure_recovery_executed={_phase150_failure_bool_token(report.get('real_failure_recovery_executed'))} controlled_failure_injected={_phase150_failure_bool_token(report.get('controlled_failure_injected'))} recoverable_failure_observed={_phase150_failure_bool_token(report.get('recoverable_failure_observed'))} recovery_plan_executed={_phase150_failure_bool_token(report.get('recovery_plan_executed'))} target_reacquired_after_failure={_phase150_failure_bool_token(report.get('target_reacquired_after_failure'))} target_rechecked_before_recovery={_phase150_failure_bool_token(report.get('target_rechecked_before_recovery'))} target_rechecked_before_result={_phase150_failure_bool_token(report.get('target_rechecked_before_result'))} state_changed_after_recovery={_phase150_failure_bool_token(report.get('state_changed_after_recovery'))} cleanup_completed={_phase150_failure_bool_token(report.get('cleanup_completed'))} real_desktop_touched={_phase150_failure_bool_token(report.get('real_desktop_touched'))} real_gui_backing={_phase150_failure_bool_token(report.get('real_gui_backing'))} raw_text_hidden={_phase150_failure_bool_token(report.get('raw_text_hidden'))}"  # 新增代码+Phase150FailureRecovery：返回固定顺序 token 行；如果没有这一行，acceptance controller 的字符串断言容易漂移。
# 新增代码+Phase150FailureRecovery：函数段结束，format_phase150_controlled_failure_recovery_line 到此结束；如果没有这个边界说明，初学者不容易看出输出范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase150FailureRecovery：函数段开始，提供命令行入口；如果没有这段函数，真实终端无法直接运行 Phase150 failure_recovery 合同。
    _ = argv  # 新增代码+Phase150FailureRecovery：当前 CLI 暂无参数但保留签名；如果没有这一行，读者会误以为遗漏参数解析。
    report = run_phase150_controlled_failure_recovery()  # 新增代码+Phase150FailureRecovery：运行总合同；如果没有这一行，CLI 不会产生验收报告。
    print(format_phase150_controlled_failure_recovery_line(report))  # 新增代码+Phase150FailureRecovery：打印稳定 token 行；如果没有这一行，可见终端无法让 controller 匹配成功。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, default=str))  # 新增代码+Phase150FailureRecovery：打印完整脱敏 JSON；如果没有这一行，失败排查缺少结构化细节。
    return 0 if report.get("passed") else 1  # 新增代码+Phase150FailureRecovery：用退出码表达合同成败；如果没有这一行，自动化无法区分成功失败。
# 新增代码+Phase150FailureRecovery：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 范围。


__all__ = ["DEFAULT_PHASE150_CONTROLLED_FAILURE_RECOVERY_ROOT", "PHASE150_CONTROLLED_FAILURE_RECOVERY_MARKER", "PHASE150_CONTROLLED_FAILURE_RECOVERY_MODEL", "PHASE150_CONTROLLED_FAILURE_RECOVERY_OK_TOKEN", "PHASE150_FAILURE_UNCONTROLLED_ACTIONS_EXPANDED", "PHASE150_REAL_FAILURE_RECOVERY_ENV", "PHASE150_REAL_FAILURE_RECOVERY_REQUEST_ENV", "Phase150WindowsFailureRecoveryDriver", "format_phase150_controlled_failure_recovery_line", "main", "run_phase150_controlled_failure_recovery"]  # 新增代码+Phase150FailureRecovery：限定公开 API；如果没有这一行，通配导入可能暴露内部 helper。
if __name__ == "__main__":  # 新增代码+Phase150FailureRecovery：模块入口段开始，允许 python -m 运行；如果没有这一行，命令行自检不会启动。
    raise SystemExit(main())  # 新增代码+Phase150FailureRecovery：执行 CLI 并返回退出码；如果没有这一行，直接运行模块没有效果。
# 新增代码+Phase150FailureRecovery：模块入口段结束，本文件到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
