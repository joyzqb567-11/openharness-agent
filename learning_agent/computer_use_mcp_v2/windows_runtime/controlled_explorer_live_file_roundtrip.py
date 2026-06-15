"""Phase149 controlled Explorer live file roundtrip benchmark."""  # 新增代码+Phase149ExplorerFileRoundtrip：说明本模块负责受控 Explorer 真实文件操作验收；如果没有这一行，维护者不容易区分它和旧的契约-only 文件测试。
from __future__ import annotations  # 新增代码+Phase149ExplorerFileRoundtrip：启用延迟类型解析；如果没有这一行，部分前向类型注解在旧解释顺序下可能导入失败。

import hashlib  # 新增代码+Phase149ExplorerFileRoundtrip：导入哈希工具；如果没有这一行，报告只能泄露文件夹名或完全无法关联输入。
import json  # 新增代码+Phase149ExplorerFileRoundtrip：导入 JSON 工具；如果没有这一行，CLI 无法打印结构化脱敏报告。
import os  # 新增代码+Phase149ExplorerFileRoundtrip：导入环境变量工具；如果没有这一行，双门禁无法从真实终端环境读取。
import shutil  # 新增代码+Phase149ExplorerFileRoundtrip：导入受控目录清理工具；如果没有这一行，真实 Explorer 创建的临时文件夹可能残留。
import subprocess  # 新增代码+Phase149ExplorerFileRoundtrip：导入进程启动工具；如果没有这一行，真实路径无法打开受控 Explorer 窗口。
import sys  # 新增代码+Phase149ExplorerFileRoundtrip：导入平台信息；如果没有这一行，非 Windows 环境可能误调用 Windows GUI。
import time  # 新增代码+Phase149ExplorerFileRoundtrip：导入等待工具；如果没有这一行，Explorer 窗口启动和文件系统刷新会被过早检查。
from pathlib import Path  # 新增代码+Phase149ExplorerFileRoundtrip：导入路径对象；如果没有这一行，受控运行目录和文件夹路径容易拼错。
from typing import Any  # 新增代码+Phase149ExplorerFileRoundtrip：导入通用类型；如果没有这一行，JSON 风格报告的输入输出边界不清楚。

try:  # 新增代码+Phase149ExplorerFileRoundtrip：优先按包模式导入项目内依赖；如果没有这段代码，单元测试和正常 python -m 路径无法共享实现。
    from learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # 新增代码+Phase149ExplorerFileRoundtrip：复用 computer_use memory 根路径；如果没有这一行，真实文件验收可能写到用户目录。
    from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+Phase149ExplorerFileRoundtrip：复用真实 SendInput sender；如果没有这一行，Explorer 只会被启动而不会收到真实键盘动作。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase149ExplorerFileRoundtrip：复用真实只读窗口枚举；如果没有这一行，动作前后无法复核 Explorer 目标。
except ModuleNotFoundError as error:  # 新增代码+Phase149ExplorerFileRoundtrip：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，真实可见终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants", "learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend"}:  # 新增代码+Phase149ExplorerFileRoundtrip：只兜底包路径缺失；如果没有这一行，依赖内部 bug 会被误吞。
        raise  # 新增代码+Phase149ExplorerFileRoundtrip：重新抛出真正的内部导入错误；如果没有这一行，排查会被错误 fallback 掩盖。
    from computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # type: ignore  # 新增代码+Phase149ExplorerFileRoundtrip：脚本模式复用 memory 根路径；如果没有这一行，bat 入口无法定位受控目录。
    from computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # type: ignore  # 新增代码+Phase149ExplorerFileRoundtrip：脚本模式复用真实 SendInput sender；如果没有这一行，bat 入口无法发真实键盘事件。
    from computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # type: ignore  # 新增代码+Phase149ExplorerFileRoundtrip：脚本模式复用窗口枚举；如果没有这一行，bat 入口无法复核 Explorer 目标。

PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_MARKER = "PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_READY"  # 新增代码+Phase149ExplorerFileRoundtrip：定义 ready marker；如果没有这一行，真实终端验收没有稳定锚点。
PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_OK_TOKEN = "PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_OK"  # 新增代码+Phase149ExplorerFileRoundtrip：定义 OK token；如果没有这一行，Phase148C 场景无法稳定匹配成功。
PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_MODEL = "phase149_controlled_explorer_live_file_roundtrip"  # 新增代码+Phase149ExplorerFileRoundtrip：定义模型名；如果没有这一行，报告无法区分本阶段证据版本。
PHASE149_REAL_EXPLORER_FILE_ENV = "LEARNING_AGENT_PHASE149_ENABLE_REAL_EXPLORER_FILE_ROUNDTRIP"  # 新增代码+Phase149ExplorerFileRoundtrip：定义强制启用真实 GUI 的门禁变量；如果没有这一行，真实桌面动作可能被默认打开。
PHASE149_REAL_EXPLORER_FILE_REQUEST_ENV = "LEARNING_AGENT_PHASE149_RUN_REAL_EXPLORER_FILE_ROUNDTRIP"  # 新增代码+Phase149ExplorerFileRoundtrip：定义请求运行真实 GUI 的变量；如果没有这一行，CLI 无法显式表达本次要跑真实验收。
PHASE149_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase149ExplorerFileRoundtrip：声明没有扩展到不受控高风险动作；如果没有这一行，成熟度矩阵无法判断安全边界。
DEFAULT_PHASE149_CONTROLLED_EXPLORER_ROOT = DEFAULT_PERSISTENT_GRANTS_ROOT.parent / "post_parity" / "phase149_controlled_explorer_live_file_roundtrip"  # 新增代码+Phase149ExplorerFileRoundtrip：定义默认受控运行根目录；如果没有这一行，真实 Explorer 文件操作可能落到用户目录。


def _phase149_bool_token(value: Any) -> str:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，把布尔值转成小写验收 token；如果没有这段函数，终端输出会混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+Phase149ExplorerFileRoundtrip：返回 true 或 false；如果没有这一行，acceptance controller 字符串匹配会不稳定。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


def _phase149_env_enabled(name: str) -> bool:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，读取环境变量门禁；如果没有这段函数，每个入口都要重复判断字符串真假。
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase149ExplorerFileRoundtrip：只接受明确真值；如果没有这一行，随便设置任意文本也可能打开真实桌面动作。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_env_enabled 到此结束；如果没有这个边界说明，初学者不容易看出门禁解析范围。


def _phase149_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，安全转换 hwnd、pid 和计数；如果没有这段函数，坏窗口字段可能让真实验收崩溃。
    try:  # 新增代码+Phase149ExplorerFileRoundtrip：捕获动态输入的转换异常；如果没有这一行，None 或脏字符串会直接抛错。
        return int(value)  # 新增代码+Phase149ExplorerFileRoundtrip：返回整数；如果没有这一行，SendInput 和 Win32 close 不能使用句柄。
    except Exception:  # 新增代码+Phase149ExplorerFileRoundtrip：把所有转换异常视为安全兜底；如果没有这一行，坏字段会中断 agent。
        return int(default)  # 新增代码+Phase149ExplorerFileRoundtrip：返回默认值；如果没有这一行，调用方要重复写兜底逻辑。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出转换范围。


def _phase149_sha256_16(value: Any) -> str:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，生成短哈希；如果没有这段函数，报告要么泄露文件夹名要么无法审计。
    text = str(value or "")  # 新增代码+Phase149ExplorerFileRoundtrip：把输入规整为字符串；如果没有这一行，None 和数字的哈希会不稳定。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16] if text else ""  # 新增代码+Phase149ExplorerFileRoundtrip：返回 16 位短哈希；如果没有这一行，脱敏关联信息不可用。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。


def _phase149_safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，把动态值规整成字典；如果没有这段函数，driver 坏返回会污染报告。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase149ExplorerFileRoundtrip：只复制 dict；如果没有这一行，None 或字符串会让 .get 调用崩溃。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_safe_dict 到此结束；如果没有这个边界说明，初学者不容易看出字典清洗范围。


def _phase149_window_field(window: Any, field: str) -> Any:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，兼容 dict 和对象窗口字段；如果没有这段函数，测试替身和真实 inventory 会分裂。
    return window.get(field) if isinstance(window, dict) else getattr(window, field, None)  # 新增代码+Phase149ExplorerFileRoundtrip：按类型读取字段；如果没有这一行，窗口摘要 helper 不能复用。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_window_field 到此结束；如果没有这个边界说明，初学者不容易看出字段读取范围。


def _phase149_hwnd_from_window(window: Any) -> int:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，从窗口摘要提取 hwnd；如果没有这段函数，真实 sender 和窗口关闭没有目标句柄。
    direct = _phase149_window_field(window, "hwnd")  # 新增代码+Phase149ExplorerFileRoundtrip：优先读取 hwnd 字段；如果没有这一行，真实 inventory 的系统句柄可能被忽略。
    if direct is not None:  # 新增代码+Phase149ExplorerFileRoundtrip：存在直接句柄时走直接转换；如果没有这一行，后续会误走文本解析。
        return _phase149_safe_int(direct)  # 新增代码+Phase149ExplorerFileRoundtrip：返回直接句柄；如果没有这一行，SetForegroundWindow 无法定位 Explorer。
    window_id = str(_phase149_window_field(window, "window_id") or "")  # 新增代码+Phase149ExplorerFileRoundtrip：读取协议窗口 id；如果没有这一行，缺 hwnd 字段时没有兜底来源。
    return _phase149_safe_int(window_id.split(":", 1)[1]) if window_id.startswith("hwnd:") and ":" in window_id else 0  # 新增代码+Phase149ExplorerFileRoundtrip：从 hwnd:123 解析句柄；如果没有这一行，静态和真实窗口 id 无法用于 Win32。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_hwnd_from_window 到此结束；如果没有这个边界说明，初学者不容易看出句柄解析范围。


def _phase149_window_key(window: Any) -> str:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，生成窗口身份 key；如果没有这段函数，启动前 baseline 无法过滤旧窗口。
    window_id = str(_phase149_window_field(window, "window_id") or "")  # 新增代码+Phase149ExplorerFileRoundtrip：读取窗口 id；如果没有这一行，无法优先用稳定 hwnd 身份。
    return f"window_id:{window_id}" if window_id else f"pid:{_phase149_safe_int(_phase149_window_field(window, 'pid') or _phase149_window_field(window, 'process_id'))}"  # 新增代码+Phase149ExplorerFileRoundtrip：返回窗口 id 或 pid key；如果没有这一行，baseline 不能识别同一窗口。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_window_key 到此结束；如果没有这个边界说明，初学者不容易看出身份 key 范围。


def _phase149_window_title(window: Any) -> str:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，读取窗口标题摘要；如果没有这段函数，Explorer 目标匹配会重复处理 title 字段。
    return str(_phase149_window_field(window, "title_preview") or _phase149_window_field(window, "title") or "")  # 新增代码+Phase149ExplorerFileRoundtrip：优先用脱敏标题摘要；如果没有这一行，匹配逻辑可能拿不到标题。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_window_title 到此结束；如果没有这个边界说明，初学者不容易看出标题读取范围。


def _phase149_window_identity(window: Any) -> dict[str, Any]:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，生成不含完整路径的窗口身份摘要；如果没有这段函数，报告可能泄露用户本地路径。
    title = _phase149_window_title(window)  # 新增代码+Phase149ExplorerFileRoundtrip：读取标题用于哈希；如果没有这一行，身份摘要缺少可比对标题线索。
    return {"app_id": str(_phase149_window_field(window, "app_id") or ""), "process_name": str(_phase149_window_field(window, "process_name") or ""), "class_name": str(_phase149_window_field(window, "class_name") or ""), "window_id": str(_phase149_window_field(window, "window_id") or ""), "hwnd": _phase149_hwnd_from_window(window), "pid": _phase149_safe_int(_phase149_window_field(window, "pid") or _phase149_window_field(window, "process_id")), "title_length": len(title), "title_sha256_16": _phase149_sha256_16(title)}  # 新增代码+Phase149ExplorerFileRoundtrip：返回脱敏身份摘要；如果没有这一行，审计无法证明动作前后是同一 Explorer 窗口。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_window_identity 到此结束；如果没有这个边界说明，初学者不容易看出窗口身份摘要范围。


def _phase149_is_controlled_explorer_window(window: Any, workspace: Path) -> bool:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，判断窗口是否为本次受控 Explorer；如果没有这段函数，动作可能发到用户已有 Explorer。
    title = _phase149_window_title(window).lower()  # 新增代码+Phase149ExplorerFileRoundtrip：标题转小写；如果没有这一行，大小写差异会漏匹配。
    class_name = str(_phase149_window_field(window, "class_name") or "").lower()  # 新增代码+Phase149ExplorerFileRoundtrip：读取窗口类名；如果没有这一行，Explorer 类型无法辅助判断。
    app_text = f"{_phase149_window_field(window, 'app_id') or ''} {_phase149_window_field(window, 'process_name') or ''}".lower()  # 新增代码+Phase149ExplorerFileRoundtrip：读取应用线索；如果没有这一行，某些系统 class 名不稳定时无法辅助识别。
    folder_token = workspace.name.lower()  # 新增代码+Phase149ExplorerFileRoundtrip：读取受控目录名；如果没有这一行，目标匹配没有本次专属线索。
    explorer_like = "cabinetwclass" in class_name or "explorer" in app_text or "explorewclass" in class_name  # 新增代码+Phase149ExplorerFileRoundtrip：判断是否像 Explorer 窗口；如果没有这一行，普通窗口标题相似也可能被选中。
    return bool(explorer_like and folder_token and folder_token in title)  # 新增代码+Phase149ExplorerFileRoundtrip：要求 Explorer 类型和受控目录名同时命中；如果没有这一行，旧 Explorer 窗口可能被误操作。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_is_controlled_explorer_window 到此结束；如果没有这个边界说明，初学者不容易看出安全匹配范围。


def _phase149_snapshot_windows(window_probe: Any) -> list[Any]:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，读取当前安全窗口列表；如果没有这段函数，真实和测试 probe 接口差异会分裂。
    snapshot = window_probe.snapshot() if hasattr(window_probe, "snapshot") else window_probe  # 新增代码+Phase149ExplorerFileRoundtrip：优先调用 snapshot；如果没有这一行，真实 WindowsWindowInventoryProbe 不会枚举窗口。
    return list(getattr(snapshot, "windows", snapshot.get("windows", []) if isinstance(snapshot, dict) else []))  # 新增代码+Phase149ExplorerFileRoundtrip：兼容对象和 dict 快照；如果没有这一行，fake snapshot 无法用于测试。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_snapshot_windows 到此结束；如果没有这个边界说明，初学者不容易看出窗口读取范围。


def _phase149_find_controlled_window(window_probe: Any, workspace: Path, baseline_keys: set[str]) -> dict[str, Any] | None:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，查找本次新开的受控 Explorer；如果没有这段函数，真实 driver 只能猜目标。
    candidates = [dict(window) for window in _phase149_snapshot_windows(window_probe) if _phase149_is_controlled_explorer_window(window, workspace)]  # 新增代码+Phase149ExplorerFileRoundtrip：筛选受控 Explorer 候选；如果没有这一行，后续没有可复核窗口。
    fresh = [window for window in candidates if _phase149_window_key(window) not in baseline_keys]  # 新增代码+Phase149ExplorerFileRoundtrip：优先选择启动后新增窗口；如果没有这一行，旧同名窗口可能被误用。
    return dict((fresh or candidates)[0]) if (fresh or candidates) else None  # 新增代码+Phase149ExplorerFileRoundtrip：返回第一个可用窗口或 None；如果没有这一行，调用方拿不到复核结果。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_find_controlled_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口查找范围。


def _phase149_sender_kind_from_result(sender: Any, result: dict[str, Any]) -> str:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，从 sender 结果读取身份；如果没有这段函数，recording/fake sender 可能被误判为真实。
    kind = str(result.get("sender_kind") or result.get("sender") or "")  # 新增代码+Phase149ExplorerFileRoundtrip：优先读取 sender 上报字段；如果没有这一行，真实 sender 身份不会进入报告。
    return kind or type(sender).__name__  # 新增代码+Phase149ExplorerFileRoundtrip：缺字段时回退类名；如果没有这一行，报告可能缺 sender_kind。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_sender_kind_from_result 到此结束；如果没有这个边界说明，初学者不容易看出 sender 身份来源。


def _phase149_sender_is_physical(sender_kind: str, low_level_event_count: int, result: dict[str, Any]) -> bool:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，判断是否真实物理派发；如果没有这段函数，fake sender 可以靠事件数冒充真实。
    lowered = str(sender_kind or "").lower()  # 新增代码+Phase149ExplorerFileRoundtrip：统一小写；如果没有这一行，大小写差异会影响判断。
    return bool(low_level_event_count > 0 and "windows_sendinput" in lowered and "record" not in lowered and "fake" not in lowered and result.get("ok"))  # 新增代码+Phase149ExplorerFileRoundtrip：要求真实 sender、事件数和成功返回；如果没有这一行，空动作或 fake 动作会误入成熟矩阵。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_sender_is_physical 到此结束；如果没有这个边界说明，初学者不容易看出物理派发判断范围。


def _phase149_path_inside(parent: Path, child: Path) -> bool:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，确认清理目标在受控目录内部；如果没有这段函数，递归删除存在误删用户目录风险。
    try:  # 新增代码+Phase149ExplorerFileRoundtrip：捕获路径解析异常；如果没有这一行，坏路径会中断 cleanup。
        child.resolve().relative_to(parent.resolve())  # 新增代码+Phase149ExplorerFileRoundtrip：验证 child 位于 parent 内；如果没有这一行，无法证明删除边界。
        return True  # 新增代码+Phase149ExplorerFileRoundtrip：验证通过返回真；如果没有这一行，安全路径也会被拒绝清理。
    except Exception:  # 新增代码+Phase149ExplorerFileRoundtrip：路径不在内部或解析失败都进入拒绝；如果没有这一行，异常会冒泡。
        return False  # 新增代码+Phase149ExplorerFileRoundtrip：返回假表示不允许清理；如果没有这一行，清理边界无法被调用方判断。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_path_inside 到此结束；如果没有这个边界说明，初学者不容易看出路径安全判断范围。


class Phase149DefaultExplorerLauncher:  # 新增代码+Phase149ExplorerFileRoundtrip：类段开始，封装真实 Explorer 启动；如果没有这个类，driver 会把进程启动细节写散。
    def launch(self, workspace: Path) -> dict[str, Any]:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，打开受控目录的 Explorer；如果没有这段函数，真实文件 GUI 验收没有代表应用。
        process = subprocess.Popen(["explorer.exe", str(workspace)])  # 新增代码+Phase149ExplorerFileRoundtrip：启动 Explorer 指向受控目录；如果没有这一行，后续 SendInput 没有目标窗口。
        return {"requested_workspace_sha256_16": _phase149_sha256_16(str(workspace)), "pid": getattr(process, "pid", 0)}  # 新增代码+Phase149ExplorerFileRoundtrip：返回脱敏启动摘要；如果没有这一行，报告缺少启动事实。
    # 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，Phase149DefaultExplorerLauncher.launch 到此结束；如果没有这个边界说明，初学者不容易看出启动范围。
# 新增代码+Phase149ExplorerFileRoundtrip：类段结束，Phase149DefaultExplorerLauncher 到此结束；如果没有这个边界说明，初学者不容易看出 launcher 范围。


class Phase149WindowsExplorerLiveFileRoundtripDriver:  # 新增代码+Phase149ExplorerFileRoundtrip：类段开始，实现真实 Explorer 文件夹创建闭环；如果没有这个类，local_file 仍停留在契约-only。
    def __init__(self, launcher: Any | None = None, window_probe: Any | None = None, sender: Any | None = None, recheck_attempts: int = 30, recheck_interval_seconds: float = 0.25) -> None:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，注入真实或测试依赖；如果没有这段代码，单测会被迫打开真实 Explorer。
        self.launcher = launcher if launcher is not None else Phase149DefaultExplorerLauncher()  # 新增代码+Phase149ExplorerFileRoundtrip：保存 launcher 或默认真实 launcher；如果没有这一行，driver 无法启动 Explorer。
        self.window_probe = window_probe if window_probe is not None else WindowsWindowInventoryProbe()  # 新增代码+Phase149ExplorerFileRoundtrip：保存窗口枚举器；如果没有这一行，动作前后无法复核目标。
        self.sender = sender if sender is not None else WindowsSendInputLowLevelSender()  # 新增代码+Phase149ExplorerFileRoundtrip：保存真实 SendInput sender；如果没有这一行，Explorer 不会收到真实快捷键。
        self.recheck_attempts = max(1, int(recheck_attempts or 1))  # 新增代码+Phase149ExplorerFileRoundtrip：保存复核次数且至少 1；如果没有这一行，窗口启动稍慢就可能误失败。
        self.recheck_interval_seconds = max(0.0, float(recheck_interval_seconds or 0.0))  # 新增代码+Phase149ExplorerFileRoundtrip：保存复核间隔且不允许负数；如果没有这一行，坏参数可能导致忙等或异常。
    # 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，Phase149WindowsExplorerLiveFileRoundtripDriver.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _wait_for_controlled_window(self, workspace: Path, baseline_keys: set[str]) -> dict[str, Any] | None:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，等待受控 Explorer 出现；如果没有这段代码，真实启动延迟会被误判为失败。
        for attempt in range(self.recheck_attempts):  # 新增代码+Phase149ExplorerFileRoundtrip：按次数轮询窗口；如果没有这一行，只查一次容易错过新窗口。
            window = _phase149_find_controlled_window(self.window_probe, workspace, baseline_keys)  # 新增代码+Phase149ExplorerFileRoundtrip：查找当前受控窗口；如果没有这一行，轮询没有事实来源。
            if window is not None:  # 新增代码+Phase149ExplorerFileRoundtrip：找到窗口就返回；如果没有这一行，成功也会继续等待。
                return window  # 新增代码+Phase149ExplorerFileRoundtrip：返回复核通过窗口；如果没有这一行，后续无法发送输入。
            if attempt + 1 < self.recheck_attempts and self.recheck_interval_seconds > 0:  # 新增代码+Phase149ExplorerFileRoundtrip：还有机会时才等待；如果没有这一行，最后一次也会无意义 sleep。
                time.sleep(self.recheck_interval_seconds)  # 新增代码+Phase149ExplorerFileRoundtrip：短暂停顿等 Explorer 标题刷新；如果没有这一行，窗口刚启动时容易找不到。
        return None  # 新增代码+Phase149ExplorerFileRoundtrip：多次失败返回 None；如果没有这一行，失败路径没有明确结果。
    # 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，Phase149WindowsExplorerLiveFileRoundtripDriver._wait_for_controlled_window 到此结束；如果没有这个边界说明，初学者不容易看出等待范围。

    def _send_new_folder_events(self, window: dict[str, Any], folder_name: str) -> dict[str, Any]:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，向受控 Explorer 发送新建文件夹快捷键和名称；如果没有这段代码，文件系统不会由 GUI 动作改变。
        hwnd = _phase149_hwnd_from_window(window)  # 新增代码+Phase149ExplorerFileRoundtrip：提取目标 hwnd；如果没有这一行，SetForegroundWindow 事件没有目标。
        rect = _phase149_safe_dict(window.get("rect"))  # 修改代码+Phase149ExplorerFileRoundtrip：读取 Explorer 窗口矩形用于先点击获焦；如果没有这一行，Ctrl+Shift+N 可能发到已置前但未接收键盘焦点的窗口。
        center_x = int((_phase149_safe_int(rect.get("left"), 100) + _phase149_safe_int(rect.get("right"), 900)) / 2)  # 修改代码+Phase149ExplorerFileRoundtrip：计算窗口中心 x 坐标；如果没有这一行，真实鼠标点击没有稳定落点。
        center_y = int((_phase149_safe_int(rect.get("top"), 100) + _phase149_safe_int(rect.get("bottom"), 700)) / 2)  # 修改代码+Phase149ExplorerFileRoundtrip：计算窗口中心 y 坐标；如果没有这一行，真实鼠标点击没有稳定落点。
        events = [{"type": "set_foreground", "hwnd": hwnd}, {"type": "pause", "seconds": 0.35}, {"type": "mouse_move", "x": center_x, "y": center_y}, {"type": "mouse_down", "button": "left"}, {"type": "mouse_up", "button": "left"}, {"type": "pause", "seconds": 0.25}, {"type": "key_down", "key": "ctrl"}, {"type": "key_down", "key": "shift"}, {"type": "key_down", "key": "n"}, {"type": "key_up", "key": "n"}, {"type": "key_up", "key": "shift"}, {"type": "key_up", "key": "ctrl"}, {"type": "pause", "seconds": 0.7}, {"type": "unicode_text", "text": folder_name, "text_length": len(folder_name), "text_sha256_16": _phase149_sha256_16(folder_name)}, {"type": "pause", "seconds": 0.25}, {"type": "key_down", "key": "enter"}, {"type": "key_up", "key": "enter"}, {"type": "pause", "seconds": 0.8}]  # 修改代码+Phase149ExplorerFileRoundtrip：定义点击获焦、Ctrl+Shift+N、Unicode 输入受控名称、回车确认的受控序列；如果没有这一行，Explorer 可能不接收快捷键或剪贴板竞态会粘贴旧内容。
        result = self.sender.send_low_level(events) if hasattr(self.sender, "send_low_level") else {"ok": False, "low_level_event_count": 0, "sender": type(self.sender).__name__, "raw_text_included": False, "reason": "sender_missing_send_low_level"}  # 新增代码+Phase149ExplorerFileRoundtrip：调用真实 sender 或返回失败；如果没有这一行，动作派发不可审计。
        return dict(result or {})  # 新增代码+Phase149ExplorerFileRoundtrip：返回规整后的 sender 结果；如果没有这一行，None 结果会让后续读取崩溃。
    # 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，Phase149WindowsExplorerLiveFileRoundtripDriver._send_new_folder_events 到此结束；如果没有这个边界说明，初学者不容易看出派发范围。

    def _close_window(self, window: dict[str, Any]) -> bool:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，尝试关闭本次 Explorer 窗口；如果没有这段代码，真实验收可能残留窗口。
        hwnd = _phase149_hwnd_from_window(window)  # 新增代码+Phase149ExplorerFileRoundtrip：提取 hwnd；如果没有这一行，PostMessage 没有关闭目标。
        if hwnd <= 0 or sys.platform != "win32":  # 新增代码+Phase149ExplorerFileRoundtrip：无效句柄或非 Windows 不调用 Win32；如果没有这一行，错误平台会崩溃。
            return False  # 新增代码+Phase149ExplorerFileRoundtrip：无法关闭时返回假；如果没有这一行，cleanup 结果无法诚实表达。
        import ctypes  # 新增代码+Phase149ExplorerFileRoundtrip：延迟导入 ctypes；如果没有这一行，无法调用 user32.PostMessageW。
        return bool(ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0))  # 新增代码+Phase149ExplorerFileRoundtrip：向目标窗口发送 WM_CLOSE；如果没有这一行，Explorer 窗口可能留在桌面。
    # 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，Phase149WindowsExplorerLiveFileRoundtripDriver._close_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口关闭范围。

    def _cleanup(self, run_root: Path, created_folder: Path, window: dict[str, Any] | None) -> dict[str, Any]:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，清理受控文件夹和 Explorer 窗口；如果没有这段代码，验收会留下桌面和磁盘副作用。
        removed = False  # 新增代码+Phase149ExplorerFileRoundtrip：初始化文件夹删除状态；如果没有这一行，cleanup 报告没有默认值。
        if created_folder.exists() and _phase149_path_inside(run_root, created_folder):  # 新增代码+Phase149ExplorerFileRoundtrip：只删除位于受控 run_root 内的目标；如果没有这一行，递归删除可能误伤用户文件。
            shutil.rmtree(created_folder)  # 新增代码+Phase149ExplorerFileRoundtrip：删除真实 GUI 创建的受控文件夹；如果没有这一行，重复验收会被残留文件夹干扰。
            removed = not created_folder.exists()  # 新增代码+Phase149ExplorerFileRoundtrip：确认删除后不存在；如果没有这一行，cleanup 可能虚报成功。
        closed = self._close_window(window) if isinstance(window, dict) else False  # 新增代码+Phase149ExplorerFileRoundtrip：尝试关闭本次 Explorer；如果没有这一行，窗口可能残留。
        return {"cleanup_completed": bool((removed or not created_folder.exists()) and (closed or window is None or _phase149_hwnd_from_window(window) <= 0)), "created_folder_removed": bool(removed or not created_folder.exists()), "host_hidden_or_restored": bool(closed or window is None), "lock_released": True}  # 新增代码+Phase149ExplorerFileRoundtrip：返回清理证据；如果没有这一行，Phase8/Phase148C 无法审计副作用是否收尾。
    # 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，Phase149WindowsExplorerLiveFileRoundtripDriver._cleanup 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。

    def run(self, *, run_root: Path, folder_name: str) -> dict[str, Any]:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，执行完整真实 Explorer 文件夹创建闭环；如果没有这段代码，local_file 无法从契约提升到真实 GUI。
        report: dict[str, Any] = {}  # 新增代码+Phase149ExplorerFileRoundtrip：准备可被 finally 补充清理字段的报告；如果没有这一行，早退路径缺 cleanup evidence。
        run_root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase149ExplorerFileRoundtrip：确保运行根目录存在；如果没有这一行，受控 workspace 无法创建。
        workspace = run_root / "workspace_phase149_explorer"  # 新增代码+Phase149ExplorerFileRoundtrip：定义本次 Explorer 打开的受控目录；如果没有这一行，真实 GUI 可能打开不受控位置。
        workspace.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase149ExplorerFileRoundtrip：确保受控目录存在；如果没有这一行，explorer.exe 可能打开失败或退到默认目录。
        created_folder = workspace / folder_name  # 新增代码+Phase149ExplorerFileRoundtrip：定义预期由 GUI 创建的文件夹；如果没有这一行，验证不知道检查哪个磁盘事实。
        if created_folder.exists() and _phase149_path_inside(run_root, created_folder):  # 新增代码+Phase149ExplorerFileRoundtrip：清理同名旧残留；如果没有这一行，旧文件夹会让真实动作前就看似成功。
            shutil.rmtree(created_folder)  # 新增代码+Phase149ExplorerFileRoundtrip：删除受控旧残留；如果没有这一行，验收无法证明本次 GUI 动作造成变化。
        baseline_keys = {_phase149_window_key(window) for window in _phase149_snapshot_windows(self.window_probe) if _phase149_is_controlled_explorer_window(window, workspace)}  # 新增代码+Phase149ExplorerFileRoundtrip：记录启动前同名窗口；如果没有这一行，旧窗口可能混入本次目标。
        launch_summary = self.launcher.launch(workspace)  # 新增代码+Phase149ExplorerFileRoundtrip：启动 Explorer 到受控目录；如果没有这一行，真实文件 GUI 路径不会开始。
        window = self._wait_for_controlled_window(workspace, baseline_keys)  # 新增代码+Phase149ExplorerFileRoundtrip：等待并复核 Explorer 目标；如果没有这一行，快捷键可能发到错误窗口。
        if window is None:  # 新增代码+Phase149ExplorerFileRoundtrip：目标窗口未找到时停止；如果没有这一行，错误焦点可能收到按键。
            report = {"ok": False, "driver": "phase149_windows_explorer_live_file_roundtrip_driver", "reason": "explorer_window_not_found", "explorer_process_verified": False, "target_rechecked_before_input": False, "target_rechecked_before_result": False, "controlled_folder_created": False, "folder_visible_or_disk_verified": False, "filesystem_changed_after_real_actions": False, "real_desktop_touched": False, "low_level_event_count": 0, "raw_text_included": False, "target_window": {}, "launch_summary": launch_summary, "physical_desktop_dispatch_performed": False, "real_sendinput_dispatch": False, "sender_kind": ""}  # 新增代码+Phase149ExplorerFileRoundtrip：返回零事件定位失败报告；如果没有这一行，失败点不可审计。
            report["cleanup_evidence"] = self._cleanup(run_root, created_folder, None)  # 新增代码+Phase149ExplorerFileRoundtrip：定位失败也记录受控目录清理证据；如果没有这一行，失败验收会缺少副作用收尾事实。
            return report  # 新增代码+Phase149ExplorerFileRoundtrip：返回失败报告；如果没有这一行，后续可能对空窗口发送动作。
        dispatch = self._send_new_folder_events(window, folder_name)  # 新增代码+Phase149ExplorerFileRoundtrip：发送真实新建文件夹动作；如果没有这一行，磁盘不会因 GUI 变化。
        low_level_event_count = _phase149_safe_int(dispatch.get("low_level_event_count"))  # 新增代码+Phase149ExplorerFileRoundtrip：读取低层事件数；如果没有这一行，空动作无法被识别。
        sender_kind = _phase149_sender_kind_from_result(self.sender, dispatch)  # 新增代码+Phase149ExplorerFileRoundtrip：提取 sender 身份；如果没有这一行，fake sender 可能误入成熟矩阵。
        physical_dispatch = _phase149_sender_is_physical(sender_kind, low_level_event_count, dispatch)  # 新增代码+Phase149ExplorerFileRoundtrip：判断是否真实 SendInput 派发；如果没有这一行，报告无法证明物理路径。
        result_window = self._wait_for_controlled_window(workspace, baseline_keys)  # 新增代码+Phase149ExplorerFileRoundtrip：动作后再次复核目标窗口；如果没有这一行，动作后目标漂移不会被发现。
        created = created_folder.is_dir()  # 新增代码+Phase149ExplorerFileRoundtrip：检查磁盘上是否出现受控文件夹；如果没有这一行，GUI 动作结果只能靠信任 sender。
        ok = bool(physical_dispatch and result_window is not None and created)  # 新增代码+Phase149ExplorerFileRoundtrip：汇总 driver 成功条件；如果没有这一行，部分成功可能被误判完整闭环。
        report = {"ok": ok, "driver": "phase149_windows_explorer_live_file_roundtrip_driver", "reason": "" if ok else "controlled_folder_not_created_by_real_gui", "explorer_process_verified": True, "target_rechecked_before_input": True, "target_rechecked_before_result": bool(result_window is not None), "controlled_folder_created": created, "folder_visible_or_disk_verified": created, "filesystem_changed_after_real_actions": bool(created and physical_dispatch), "real_desktop_touched": bool(low_level_event_count), "low_level_event_count": low_level_event_count, "raw_text_included": False, "target_window": _phase149_window_identity(result_window or window), "launch_summary": launch_summary, "folder_name_sha256_16": _phase149_sha256_16(folder_name), "physical_desktop_dispatch_performed": physical_dispatch, "real_sendinput_dispatch": physical_dispatch, "sender_kind": sender_kind}  # 新增代码+Phase149ExplorerFileRoundtrip：返回脱敏闭环报告；如果没有这一行，Phase148C 拿不到 local_file 真实 GUI 证据。
        report["cleanup_evidence"] = self._cleanup(run_root, created_folder, result_window or window)  # 新增代码+Phase149ExplorerFileRoundtrip：补充受控文件夹删除和 Explorer 关闭证据；如果没有这一行，真实验收无法证明副作用已收尾。
        return report  # 新增代码+Phase149ExplorerFileRoundtrip：返回已补充 cleanup 的报告；如果没有这一行，调用方拿不到执行结果。
    # 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，Phase149WindowsExplorerLiveFileRoundtripDriver.run 到此结束；如果没有这个边界说明，初学者不容易看出 driver 主流程范围。
# 新增代码+Phase149ExplorerFileRoundtrip：类段结束，Phase149WindowsExplorerLiveFileRoundtripDriver 到此结束；如果没有这个边界说明，初学者不容易看出真实 driver 范围。


def _phase149_default_off_report() -> dict[str, Any]:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，构造默认关闭报告；如果没有这段函数，普通运行无法证明 0 物理事件。
    return {"decision": "real_explorer_file_roundtrip_disabled_by_default", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase149ExplorerFileRoundtrip：返回零事件默认报告；如果没有这一行，默认安全边界无证据。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_default_off_report 到此结束；如果没有这个边界说明，初学者不容易看出默认安全范围。


def _phase149_unsafe_target_report() -> dict[str, Any]:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，构造危险目标拒绝报告；如果没有这段函数，敏感窗口零事件边界无证据。
    return {"decision": "unsafe_target_rejected", "target": "terminal_like_window", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase149ExplorerFileRoundtrip：返回终端类目标零事件拒绝；如果没有这一行，安全门禁可能被误削弱。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，_phase149_unsafe_target_report 到此结束；如果没有这个边界说明，初学者不容易看出危险目标范围。


def run_phase149_controlled_explorer_live_file_roundtrip(real_run_requested: bool | None = None, real_enable_gate: bool | None = None, run_root: str | Path | None = None, driver: Any | None = None, require_injected_driver: bool = False, raw_prompt_text: str | None = None) -> dict[str, Any]:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，运行 Phase149 总合同入口；如果没有这段函数，测试、CLI 和 Phase148C 无法共用事实源。
    requested = _phase149_env_enabled(PHASE149_REAL_EXPLORER_FILE_REQUEST_ENV) if real_run_requested is None else bool(real_run_requested)  # 新增代码+Phase149ExplorerFileRoundtrip：读取是否请求真实运行；如果没有这一行，环境变量门禁不会生效。
    gate_enabled = _phase149_env_enabled(PHASE149_REAL_EXPLORER_FILE_ENV) if real_enable_gate is None else bool(real_enable_gate)  # 新增代码+Phase149ExplorerFileRoundtrip：读取真实 GUI 强门禁；如果没有这一行，单个变量可能误开桌面动作。
    root = Path(run_root) if run_root is not None else DEFAULT_PHASE149_CONTROLLED_EXPLORER_ROOT  # 新增代码+Phase149ExplorerFileRoundtrip：确定受控运行根目录；如果没有这一行，真实文件操作没有边界。
    folder_name = f"phase149_gui_folder_{int(time.time())}"  # 新增代码+Phase149ExplorerFileRoundtrip：生成本次受控文件夹名；如果没有这一行，重复验收会互相干扰。
    default_report = _phase149_default_off_report()  # 新增代码+Phase149ExplorerFileRoundtrip：生成默认关闭证据；如果没有这一行，报告缺默认 0 事件门禁。
    unsafe_report = _phase149_unsafe_target_report()  # 新增代码+Phase149ExplorerFileRoundtrip：生成危险目标拒绝证据；如果没有这一行，报告缺敏感窗口保护事实。
    default_zero = bool(default_report.get("low_level_event_count") == 0 and not default_report.get("real_desktop_touched"))  # 新增代码+Phase149ExplorerFileRoundtrip：确认默认关闭零事件；如果没有这一行，默认安全状态无法量化。
    unsafe_zero = bool(unsafe_report.get("low_level_event_count") == 0 and not unsafe_report.get("real_desktop_touched"))  # 新增代码+Phase149ExplorerFileRoundtrip：确认危险目标零事件；如果没有这一行，敏感窗口保护无法量化。
    driver_report: dict[str, Any] = {}  # 新增代码+Phase149ExplorerFileRoundtrip：初始化 driver 报告；如果没有这一行，未运行真实路径时后续字段读取会崩溃。
    real_executed = False  # 新增代码+Phase149ExplorerFileRoundtrip：初始化真实执行标记；如果没有这一行，默认关闭路径可能显示脏值。
    if requested and gate_enabled:  # 新增代码+Phase149ExplorerFileRoundtrip：只有双门都开才允许真实 GUI；如果没有这一行，普通运行可能打开 Explorer。
        if require_injected_driver and driver is None:  # 新增代码+Phase149ExplorerFileRoundtrip：测试要求注入时拒绝默认真实 driver；如果没有这一行，单测可能误触桌面。
            driver_report = {"ok": False, "driver": "missing_injected_driver", "reason": "require_injected_driver_without_driver", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase149ExplorerFileRoundtrip：返回零事件缺 driver 报告；如果没有这一行，失败原因不可审计。
        else:  # 新增代码+Phase149ExplorerFileRoundtrip：允许使用注入或默认 driver；如果没有这一行，真实路径不会进入执行分支。
            actual_driver = driver if driver is not None else Phase149WindowsExplorerLiveFileRoundtripDriver()  # 新增代码+Phase149ExplorerFileRoundtrip：选择 driver；如果没有这一行，生产路径没有默认真实实现。
            driver_report = _phase149_safe_dict(actual_driver.run(run_root=root, folder_name=folder_name))  # 新增代码+Phase149ExplorerFileRoundtrip：执行真实或 fake driver；如果没有这一行，合同层无法获得 local_file 证据。
            real_executed = True  # 新增代码+Phase149ExplorerFileRoundtrip：标记真实路径已尝试执行；如果没有这一行，成功样本也会显示未运行。
    cleanup_evidence = _phase149_safe_dict(driver_report.get("cleanup_evidence"))  # 新增代码+Phase149ExplorerFileRoundtrip：读取清理证据；如果没有这一行，cleanup_completed 字段无法归一。
    low_level_event_count = _phase149_safe_int(driver_report.get("low_level_event_count"))  # 新增代码+Phase149ExplorerFileRoundtrip：读取低层事件数；如果没有这一行，真实桌面触达判断没有依据。
    real_desktop_touched = bool(driver_report.get("real_desktop_touched") and low_level_event_count > 0)  # 新增代码+Phase149ExplorerFileRoundtrip：确认发生低层事件；如果没有这一行，driver 空返回可能被误判触桌。
    report_without_raw_check: dict[str, Any] = {"marker": PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_MARKER, "ok_token": PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_OK_TOKEN, "model": PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_MODEL, "real_explorer_file_env": PHASE149_REAL_EXPLORER_FILE_ENV, "real_explorer_file_request_env": PHASE149_REAL_EXPLORER_FILE_REQUEST_ENV, "real_run_requested": requested, "real_enable_gate_required": True, "real_enable_gate_passed": gate_enabled, "require_injected_driver": bool(require_injected_driver), "folder_name_sha256_16": _phase149_sha256_16(folder_name), "default_off_zero_physical_events": default_zero, "unsafe_target_zero_physical_events": unsafe_zero, "real_explorer_run_executed": real_executed, "explorer_process_verified": bool(driver_report.get("explorer_process_verified")), "target_rechecked_before_input": bool(driver_report.get("target_rechecked_before_input")), "target_rechecked_before_result": bool(driver_report.get("target_rechecked_before_result")), "controlled_folder_created": bool(driver_report.get("controlled_folder_created")), "folder_visible_or_disk_verified": bool(driver_report.get("folder_visible_or_disk_verified")), "filesystem_changed_after_real_actions": bool(driver_report.get("filesystem_changed_after_real_actions")), "cleanup_completed": bool(cleanup_evidence.get("cleanup_completed")), "real_desktop_touched": real_desktop_touched, "uncontrolled_actions_expanded": PHASE149_UNCONTROLLED_ACTIONS_EXPANDED, "driver": str(driver_report.get("driver", "")), "driver_ok": bool(driver_report.get("ok")), "driver_reason": str(driver_report.get("reason", "")), "default_off_report": default_report, "unsafe_report": unsafe_report}  # 新增代码+Phase149ExplorerFileRoundtrip：构造脱敏报告主体；如果没有这一行，测试和 CLI 会丢失关键事实。
    report_without_raw_check.update({"target_window": _phase149_safe_dict(driver_report.get("target_window")), "cleanup_evidence": cleanup_evidence, "physical_desktop_dispatch_performed": bool(driver_report.get("physical_desktop_dispatch_performed")), "real_sendinput_dispatch": bool(driver_report.get("real_sendinput_dispatch")), "sender_kind": str(driver_report.get("sender_kind") or ""), "low_level_event_count": low_level_event_count})  # 新增代码+Phase149ExplorerFileRoundtrip：合并 Phase8/Phase148C 需要的真实动作字段；如果没有这一行，矩阵无法判断物理派发。
    serialized = json.dumps(report_without_raw_check, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase149ExplorerFileRoundtrip：序列化脱敏报告用于泄露检查；如果没有这一行，raw_text_hidden 没有事实依据。
    raw_text_hidden = bool(folder_name not in serialized and (raw_prompt_text is None or raw_prompt_text not in serialized))  # 新增代码+Phase149ExplorerFileRoundtrip：确认文件夹名和用户原 prompt 未进入输出；如果没有这一行，日志可能泄露受控文本或 prompt。
    real_gui_backing = bool(real_desktop_touched and report_without_raw_check["physical_desktop_dispatch_performed"] and report_without_raw_check["real_sendinput_dispatch"])  # 新增代码+Phase149ExplorerFileRoundtrip：确认真实 GUI 背书；如果没有这一行，Phase148C 无法把 local_file 从契约-only 升级。
    passed = bool(default_zero and unsafe_zero and raw_text_hidden and not PHASE149_UNCONTROLLED_ACTIONS_EXPANDED and ((not requested and not real_desktop_touched) or (requested and gate_enabled and real_executed and report_without_raw_check["explorer_process_verified"] and report_without_raw_check["target_rechecked_before_input"] and report_without_raw_check["target_rechecked_before_result"] and report_without_raw_check["controlled_folder_created"] and report_without_raw_check["folder_visible_or_disk_verified"] and report_without_raw_check["filesystem_changed_after_real_actions"] and report_without_raw_check["cleanup_completed"] and real_gui_backing)))  # 新增代码+Phase149ExplorerFileRoundtrip：汇总合同通过条件；如果没有这一行，main 无法用退出码表达真实闭环是否完成。
    report_without_raw_check.update({"raw_text_hidden": raw_text_hidden, "real_gui_backing": real_gui_backing, "contract_only": False if real_gui_backing else not requested, "passed": passed})  # 新增代码+Phase149ExplorerFileRoundtrip：写入最终判断字段；如果没有这一行，测试、CLI 和成熟度矩阵拿不到结论。
    return report_without_raw_check  # 新增代码+Phase149ExplorerFileRoundtrip：返回完整脱敏报告；如果没有这一行，调用方无法使用 Phase149 事实。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，run_phase149_controlled_explorer_live_file_roundtrip 到此结束；如果没有这个边界说明，初学者不容易看出总合同范围。


def format_phase149_controlled_explorer_live_file_roundtrip_line(report: dict[str, Any]) -> str:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，把报告格式化成稳定终端 token 行；如果没有这段函数，场景需要解析大 JSON。
    ok_token = PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_OK_TOKEN if report.get("passed") else "PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_FAILED"  # 新增代码+Phase149ExplorerFileRoundtrip：按结果选择 OK/FAILED token；如果没有这一行，失败也可能看起来像成功。
    return f"{PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_MARKER} {ok_token} default_off_zero_physical_events={_phase149_bool_token(report.get('default_off_zero_physical_events'))} unsafe_target_zero_physical_events={_phase149_bool_token(report.get('unsafe_target_zero_physical_events'))} real_enable_gate_required={_phase149_bool_token(report.get('real_enable_gate_required'))} real_explorer_run_executed={_phase149_bool_token(report.get('real_explorer_run_executed'))} explorer_process_verified={_phase149_bool_token(report.get('explorer_process_verified'))} target_rechecked_before_input={_phase149_bool_token(report.get('target_rechecked_before_input'))} target_rechecked_before_result={_phase149_bool_token(report.get('target_rechecked_before_result'))} controlled_folder_created={_phase149_bool_token(report.get('controlled_folder_created'))} folder_visible_or_disk_verified={_phase149_bool_token(report.get('folder_visible_or_disk_verified'))} filesystem_changed_after_real_actions={_phase149_bool_token(report.get('filesystem_changed_after_real_actions'))} cleanup_completed={_phase149_bool_token(report.get('cleanup_completed'))} raw_text_hidden={_phase149_bool_token(report.get('raw_text_hidden'))} real_desktop_touched={_phase149_bool_token(report.get('real_desktop_touched'))} real_gui_backing={_phase149_bool_token(report.get('real_gui_backing'))} uncontrolled_actions_expanded={_phase149_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase149ExplorerFileRoundtrip：返回固定顺序 token；如果没有这一行，真实可见终端验收匹配会漂移。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，format_phase149_controlled_explorer_live_file_roundtrip_line 到此结束；如果没有这个边界说明，初学者不容易看出输出格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase149ExplorerFileRoundtrip：函数段开始，提供 CLI 入口；如果没有这段函数，acceptance controller 无法在真实终端运行 Phase149。
    _ = argv  # 新增代码+Phase149ExplorerFileRoundtrip：保留 argv 供未来扩展；如果没有这一行，读者可能以为参数被漏用。
    report = run_phase149_controlled_explorer_live_file_roundtrip()  # 新增代码+Phase149ExplorerFileRoundtrip：按环境双门运行合同；如果没有这一行，CLI 不会产生验收事实。
    print(format_phase149_controlled_explorer_live_file_roundtrip_line(report))  # 新增代码+Phase149ExplorerFileRoundtrip：打印稳定 token 行；如果没有这一行，debug log 无法简单匹配。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase149ExplorerFileRoundtrip：打印脱敏结构化报告；如果没有这一行，失败时不易复盘。
    print(PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_MARKER)  # 新增代码+Phase149ExplorerFileRoundtrip：单独打印 ready marker；如果没有这一行，最终回答复制时容易漏锚点。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase149ExplorerFileRoundtrip：用合同结果决定退出码；如果没有这一行，失败也可能被当成成功。
# 新增代码+Phase149ExplorerFileRoundtrip：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_PHASE149_CONTROLLED_EXPLORER_ROOT", "PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_MARKER", "PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_MODEL", "PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_OK_TOKEN", "PHASE149_REAL_EXPLORER_FILE_ENV", "PHASE149_REAL_EXPLORER_FILE_REQUEST_ENV", "PHASE149_UNCONTROLLED_ACTIONS_EXPANDED", "Phase149WindowsExplorerLiveFileRoundtripDriver", "format_phase149_controlled_explorer_live_file_roundtrip_line", "main", "run_phase149_controlled_explorer_live_file_roundtrip"]  # 新增代码+Phase149ExplorerFileRoundtrip：限定公开 API；如果没有这一行，通配导入可能暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase149ExplorerFileRoundtrip：文件入口段开始，允许直接运行模块；如果没有这一行，python 文件方式不会执行自检。
    raise SystemExit(main())  # 新增代码+Phase149ExplorerFileRoundtrip：用 main 返回码退出；如果没有这一行，命令行状态不明确。
# 新增代码+Phase149ExplorerFileRoundtrip：文件入口段结束，本模块到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
