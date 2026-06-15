"""Phase138 受控 Windows Paint 真实绘图合同。"""  # 新增代码+Phase138PaintLiveDraw：说明本模块只负责 Paint 代表应用验收；如果没有这一行，读者容易误以为这里是 Paint 专用产品控制器。
from __future__ import annotations  # 新增代码+Phase138PaintLiveDraw：启用延迟类型解析；如果没有这一行，旧入口遇到复杂类型标注时更容易导入失败。
import hashlib  # 新增代码+Phase138PaintLiveDraw：导入哈希库用于截图和标题脱敏指纹；如果没有这一行，报告无法安全证明前后状态不同。
import json  # 新增代码+Phase138PaintLiveDraw：导入 JSON 用于报告写入和泄露扫描；如果没有这一行，合同结果无法稳定落盘。
import os  # 新增代码+Phase138PaintLiveDraw：导入 os 用于读取双环境门；如果没有这一行，真实 Paint 路径无法被显式开关控制。
import subprocess  # 新增代码+Phase138PaintLiveDraw：导入 subprocess 用于启动 mspaint.exe；如果没有这一行，验收无法自己打开受控 Paint。
import sys  # 新增代码+Phase138PaintLiveDraw：导入 sys 用于平台判断；如果没有这一行，非 Windows 环境可能误触发 Win32 行为。
import time  # 新增代码+Phase138PaintLiveDraw：导入 time 用于轮询窗口、等待绘图落盘和生成隔离目录；如果没有这一行，真实绘图节奏会不稳定。
from pathlib import Path  # 新增代码+Phase138PaintLiveDraw：导入 Path 统一处理 Windows 路径；如果没有这一行，报告路径和截图路径会更脆弱。
from typing import Any  # 新增代码+Phase138PaintLiveDraw：导入 Any 描述动态 JSON 报告；如果没有这一行，公开接口边界不清楚。

try:  # 新增代码+Phase138PaintLiveDraw：优先按包路径导入项目内组件；如果没有这段代码，单测和真实终端不能共享同一套实现。
    from learning_agent.computer_use_mcp_v2.windows_runtime.drawing_primitives import build_pikachu_drag_plan, expand_drag_path_to_low_level_events  # 新增代码+Phase138PaintLiveDraw：复用通用皮卡丘拖拽 primitive；如果没有这一行，Paint 验收会退回硬编码坐标。
    from learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # 新增代码+Phase138PaintLiveDraw：复用现有 Computer Use 运行根目录；如果没有这一行，Paint 报告会散落到未知位置。
    from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+Phase138PaintLiveDraw：复用真实 SendInput sender；如果没有这一行，Paint 动作可能退回假 sender。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_real_observation import UniversalRealObservationFrameRuntime  # 新增代码+Phase138PaintLiveDraw：复用真实观察帧生成截图/UIA/window 状态摘要；如果没有这一行，Phase8 证据会缺观察链。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase138PaintLiveDraw：复用真实窗口枚举器；如果没有这一行，driver 无法定位 Paint 窗口。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase138PaintLiveDraw：复用原子 JSON 写入；如果没有这一行，验收中断可能留下半截报告。
except ModuleNotFoundError as error:  # 新增代码+Phase138PaintLiveDraw：兼容 start_oauth_agent.bat 可能从 learning_agent 目录直接运行；如果没有这段代码，真实可见终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.drawing_primitives", "learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants", "learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_real_observation", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase138PaintLiveDraw：只兜底包路径缺失，避免吞掉真实内部 bug；如果没有这一行，依赖内部错误会被误判为脚本模式问题。
        raise  # 新增代码+Phase138PaintLiveDraw：重新抛出非路径类导入错误；如果没有这一行，排查底层模块 bug 会很困难。
    from computer_use_mcp_v2.windows_runtime.drawing_primitives import build_pikachu_drag_plan, expand_drag_path_to_low_level_events  # type: ignore  # 新增代码+Phase138PaintLiveDraw：脚本模式下复用通用绘图 primitive；如果没有这一行，bat 入口无法生成拖拽计划。
    from computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # type: ignore  # 新增代码+Phase138PaintLiveDraw：脚本模式下复用运行根目录；如果没有这一行，bat 入口无法定位报告目录。
    from computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # type: ignore  # 新增代码+Phase138PaintLiveDraw：脚本模式下导入真实 sender；如果没有这一行，bat 入口无法发送真实鼠标拖拽。
    from computer_use_mcp_v2.windows_runtime.universal_real_observation import UniversalRealObservationFrameRuntime  # type: ignore  # 新增代码+Phase138PaintLiveDraw：脚本模式下导入观察帧 runtime；如果没有这一行，bat 入口无法形成观察证据。
    from computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # type: ignore  # 新增代码+Phase138PaintLiveDraw：脚本模式下导入窗口枚举器；如果没有这一行，bat 入口无法找到 Paint。
    from runtime.files import atomic_write_json  # type: ignore  # 新增代码+Phase138PaintLiveDraw：脚本模式下导入原子写入；如果没有这一行，报告可能写坏。

PHASE138_CONTROLLED_PAINT_LIVE_DRAW_MARKER = "PHASE138_CONTROLLED_PAINT_LIVE_DRAW_READY"  # 新增代码+Phase138PaintLiveDraw：定义真实终端验收等待的 ready marker；如果没有这一行，controller 没有稳定锚点。
PHASE138_CONTROLLED_PAINT_LIVE_DRAW_OK_TOKEN = "PHASE138_CONTROLLED_PAINT_LIVE_DRAW_OK"  # 新增代码+Phase138PaintLiveDraw：定义成功 token；如果没有这一行，失败和成功输出无法稳定区分。
PHASE138_CONTROLLED_PAINT_LIVE_DRAW_MODEL = "phase138_controlled_paint_live_draw"  # 新增代码+Phase138PaintLiveDraw：定义报告模型名；如果没有这一行，后续矩阵无法识别合同版本。
PHASE138_REAL_PAINT_DRAW_ENV = "LEARNING_AGENT_PHASE138_ENABLE_REAL_PAINT_DRAW"  # 新增代码+Phase138PaintLiveDraw：定义允许真实 Paint 动作的第二道门；如果没有这一行，真实桌面动作缺少显式授权。
PHASE138_REAL_PAINT_DRAW_REQUEST_ENV = "LEARNING_AGENT_PHASE138_RUN_REAL_PAINT_DRAW"  # 新增代码+Phase138PaintLiveDraw：定义请求真实 Paint 动作的第一道门；如果没有这一行，CLI 无法表达本次确实要跑真实路径。
PHASE138_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase138PaintLiveDraw：声明本合同没有开放无边界桌面动作；如果没有这一行，能力范围容易被误读成泛化放权。
PHASE138_MAX_REAL_DRAG_PATHS = 6  # 新增代码+Phase138PaintLiveDraw：限制真实验收最多执行前 6 条皮卡丘笔画；如果没有这一行，真实 Paint 事件过多会拖慢验收并增加副作用窗口。
DEFAULT_PHASE138_CONTROLLED_PAINT_LIVE_DRAW_ROOT = DEFAULT_PERSISTENT_GRANTS_ROOT.parent / "phase138_controlled_paint_live_draw"  # 新增代码+Phase138PaintLiveDraw：定义默认报告根目录；如果没有这一行，真实验收证据没有固定落点。

def _phase138_bool_token(value: Any) -> str:  # 新增代码+Phase138PaintLiveDraw：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+Phase138PaintLiveDraw：返回 true 或 false 文本；如果没有这一行，验收脚本的字符串匹配会不稳定。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。

def _phase138_env_enabled(name: str) -> bool:  # 新增代码+Phase138PaintLiveDraw：函数段开始，统一判断环境变量是否显式为真；如果没有这段函数，双门解析会散落重复。
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase138PaintLiveDraw：只接受明确真值；如果没有这一行，模糊环境值可能误开真实桌面动作。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_env_enabled 到此结束；如果没有这个边界说明，初学者不容易看出环境门范围。

def _phase138_request_real_run(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase138PaintLiveDraw：函数段开始，判断本次是否请求真实 Paint；如果没有这段函数，测试参数和环境变量入口会漂移。
    if explicit_value is not None:  # 新增代码+Phase138PaintLiveDraw：调用方传入显式值时优先使用；如果没有这一行，单测无法稳定覆盖真实请求分支。
        return bool(explicit_value)  # 新增代码+Phase138PaintLiveDraw：返回显式请求布尔值；如果没有这一行，传参不会生效。
    return _phase138_env_enabled(PHASE138_REAL_PAINT_DRAW_REQUEST_ENV)  # 新增代码+Phase138PaintLiveDraw：没有显式值时读取请求环境门；如果没有这一行，CLI 无法请求真实 Paint 路径。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_request_real_run 到此结束；如果没有这个边界说明，初学者不容易看出请求门范围。

def _phase138_real_gate_enabled(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase138PaintLiveDraw：函数段开始，判断真实 Paint 是否被允许；如果没有这段函数，第二道安全门会分散且难审计。
    if explicit_value is not None:  # 新增代码+Phase138PaintLiveDraw：调用方传入显式允许值时优先使用；如果没有这一行，单测无法安全打开 gated 分支。
        return bool(explicit_value)  # 新增代码+Phase138PaintLiveDraw：返回显式允许布尔值；如果没有这一行，传参不会生效。
    return _phase138_env_enabled(PHASE138_REAL_PAINT_DRAW_ENV)  # 新增代码+Phase138PaintLiveDraw：没有显式值时读取允许环境门；如果没有这一行，CLI 真实路径缺少第二道确认。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_real_gate_enabled 到此结束；如果没有这个边界说明，初学者不容易看出允许门范围。

def _phase138_sha256_16(value: Any) -> str:  # 新增代码+Phase138PaintLiveDraw：函数段开始，生成短哈希用于脱敏审计；如果没有这段函数，报告无法安全证明读到过某些内容。
    text = str(value or "")  # 新增代码+Phase138PaintLiveDraw：把动态输入规整成字符串；如果没有这一行，None 或数字输入的哈希不稳定。
    if not text:  # 新增代码+Phase138PaintLiveDraw：空值不生成哈希；如果没有这一行，空输入也会看起来像有内容。
        return ""  # 新增代码+Phase138PaintLiveDraw：返回空哈希；如果没有这一行，调用方无法区分空值。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase138PaintLiveDraw：返回前 16 位 SHA256；如果没有这一行，脱敏指纹不可用。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。

def _phase138_file_sha256_16(path_text: Any) -> str:  # 新增代码+Phase138PaintLiveDraw：函数段开始，读取截图文件并生成短哈希；如果没有这段函数，前后截图差异只能靠字段自报。
    path = Path(str(path_text or ""))  # 新增代码+Phase138PaintLiveDraw：把动态路径转换为 Path；如果没有这一行，字符串和 Path 输入会分裂。
    if not str(path_text or "") or not path.exists():  # 新增代码+Phase138PaintLiveDraw：检查路径是否真实存在；如果没有这一行，坏路径会抛异常或误生成哈希。
        return ""  # 新增代码+Phase138PaintLiveDraw：截图不存在时返回空指纹；如果没有这一行，调用方无法安全判断缺证据。
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]  # 新增代码+Phase138PaintLiveDraw：返回截图文件 bytes 的短哈希；如果没有这一行，前后截图无法机器比较。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_file_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出截图哈希范围。

def _phase138_safe_int(value: Any) -> int:  # 新增代码+Phase138PaintLiveDraw：函数段开始，把动态值安全转成整数；如果没有这段函数，坏 JSON 字段可能让合同崩溃。
    try:  # 新增代码+Phase138PaintLiveDraw：捕获无法转换的输入；如果没有这一行，坏窗口字段会抛异常。
        return int(value or 0)  # 新增代码+Phase138PaintLiveDraw：返回整数或 0；如果没有这一行，低层事件计数和 hwnd 无法稳定使用。
    except (TypeError, ValueError):  # 新增代码+Phase138PaintLiveDraw：处理坏类型和值错误；如果没有这一行，动态证据不能容错。
        return 0  # 新增代码+Phase138PaintLiveDraw：坏值按 0 处理；如果没有这一行，调用方要重复兜底。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出整数清洗范围。

def _phase138_safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，把外部值安全整理成字典；如果没有这段函数，坏 driver 输出会让 builder 崩溃。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase138PaintLiveDraw：只接受 dict 并复制；如果没有这一行，外部可变对象可能污染内部报告。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_safe_dict 到此结束；如果没有这个边界说明，初学者不容易看出字典清洗范围。

def _phase138_get_window_field(window: Any, name: str) -> Any:  # 新增代码+Phase138PaintLiveDraw：函数段开始，统一读取 dict 或对象窗口字段；如果没有这段函数，fake 和真实窗口读取会分裂。
    if isinstance(window, dict):  # 新增代码+Phase138PaintLiveDraw：优先处理 dict 窗口；如果没有这一行，注入测试窗口无法读取。
        return window.get(name)  # 新增代码+Phase138PaintLiveDraw：从字典读取字段；如果没有这一行，dict 会被当成普通对象。
    return getattr(window, name, None)  # 新增代码+Phase138PaintLiveDraw：从对象属性读取字段；如果没有这一行，未来对象窗口无法复用。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_get_window_field 到此结束；如果没有这个边界说明，初学者不容易看出字段读取范围。

def _phase138_hwnd_from_window(window: Any) -> int:  # 新增代码+Phase138PaintLiveDraw：函数段开始，从窗口摘要里取 hwnd；如果没有这段函数，SetForegroundWindow 没有目标。
    explicit_hwnd = _phase138_safe_int(_phase138_get_window_field(window, "hwnd"))  # 新增代码+Phase138PaintLiveDraw：优先读取 hwnd 字段；如果没有这一行，真实 inventory 的句柄可能被忽略。
    if explicit_hwnd > 0:  # 新增代码+Phase138PaintLiveDraw：检查显式 hwnd 是否有效；如果没有这一行，0 句柄会被误用。
        return explicit_hwnd  # 新增代码+Phase138PaintLiveDraw：返回真实 hwnd；如果没有这一行，后续只能解析 window_id。
    window_id = str(_phase138_get_window_field(window, "window_id") or "")  # 新增代码+Phase138PaintLiveDraw：读取 window_id 作为兜底；如果没有这一行，只有 hwnd:123 形式的窗口无法使用。
    return _phase138_safe_int(window_id.split(":", 1)[1]) if window_id.startswith("hwnd:") and ":" in window_id else 0  # 新增代码+Phase138PaintLiveDraw：从 hwnd:123 解析句柄；如果没有这一行，协议窗口 id 无法转 Win32 句柄。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_hwnd_from_window 到此结束；如果没有这个边界说明，初学者不容易看出 hwnd 解析范围。

def _phase138_window_text_blob(window: Any) -> str:  # 新增代码+Phase138PaintLiveDraw：函数段开始，拼出用于识别 Paint 的窗口文本；如果没有这段函数，目标识别逻辑会散落。
    fields = ["app_id", "process_name", "class_name", "title_preview", "title", "window_id"]  # 新增代码+Phase138PaintLiveDraw：列出身份判断需要的字段；如果没有这一行，某些窗口线索可能漏检。
    return " ".join(str(_phase138_get_window_field(window, field) or "") for field in fields).lower()  # 新增代码+Phase138PaintLiveDraw：合并并小写窗口字段；如果没有这一行，大小写差异会导致误判。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_window_text_blob 到此结束；如果没有这个边界说明，初学者不容易看出窗口识别文本范围。

def _phase138_is_forbidden_window(window: Any) -> bool:  # 新增代码+Phase138PaintLiveDraw：函数段开始，识别终端和安全敏感窗口；如果没有这段函数，鼠标可能被发到命令行或安全窗口。
    blob = _phase138_window_text_blob(window)  # 新增代码+Phase138PaintLiveDraw：读取统一窗口文本；如果没有这一行，危险关键字没有检查对象。
    forbidden_tokens = ("powershell", "cmd.exe", "command prompt", "windows terminal", "terminal", "consolewindowclass", "security", "credential", "password", "uac", "defender", "login", "captcha", "codex")  # 新增代码+Phase138PaintLiveDraw：定义必须零事件拒绝的目标线索；如果没有这一行，终端和安全窗口可能漏过。
    return any(token in blob for token in forbidden_tokens)  # 新增代码+Phase138PaintLiveDraw：命中任一危险线索就拒绝；如果没有这一行，危险窗口不会被统一拦截。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_is_forbidden_window 到此结束；如果没有这个边界说明，初学者不容易看出危险目标范围。

def _phase138_is_paint_window(window: Any) -> bool:  # 新增代码+Phase138PaintLiveDraw：函数段开始，判断窗口是否像 Windows Paint；如果没有这段函数，拖拽可能发到错误窗口。
    blob = _phase138_window_text_blob(window)  # 新增代码+Phase138PaintLiveDraw：读取窗口身份文本；如果没有这一行，判断没有输入。
    has_paint_identity = bool("mspaint" in blob or "paint" in blob or "画图" in blob)  # 新增代码+Phase138PaintLiveDraw：接受英文 Paint、mspaint 和中文画图线索；如果没有这一行，中文系统或 UWP 类名可能识别失败。
    return bool(has_paint_identity and not _phase138_is_forbidden_window(window))  # 新增代码+Phase138PaintLiveDraw：同时要求 Paint 身份且非敏感目标；如果没有这一行，危险窗口可能绕过安全边界。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_is_paint_window 到此结束；如果没有这个边界说明，初学者不容易看出 Paint 目标边界。

def _phase138_window_identity(window: Any) -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，生成不含完整标题正文的窗口身份摘要；如果没有这段函数，报告可能泄露窗口标题或缺可审计身份。
    title = str(_phase138_get_window_field(window, "title_preview") or _phase138_get_window_field(window, "title") or "")  # 新增代码+Phase138PaintLiveDraw：读取标题只用于长度和哈希；如果没有这一行，目标身份缺少标题线索。
    return {"app_id": str(_phase138_get_window_field(window, "app_id") or ""), "process_name": str(_phase138_get_window_field(window, "process_name") or ""), "class_name": str(_phase138_get_window_field(window, "class_name") or ""), "window_id": str(_phase138_get_window_field(window, "window_id") or ""), "hwnd": _phase138_hwnd_from_window(window), "pid": _phase138_safe_int(_phase138_get_window_field(window, "pid") or _phase138_get_window_field(window, "process_id")), "title_preview": "Paint" if ("paint" in title.lower() or "画图" in title) else "", "title_length": len(title), "title_sha256_16": _phase138_sha256_16(title), "rect": _phase138_safe_dict(_phase138_get_window_field(window, "rect"))}  # 新增代码+Phase138PaintLiveDraw：返回脱敏身份摘要；如果没有这一行，Phase8 无法确认动作绑定到具体窗口。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_window_identity 到此结束；如果没有这个边界说明，初学者不容易看出身份摘要范围。

def _phase138_window_key(window: Any) -> str:  # 新增代码+Phase138PaintLiveDraw：函数段开始，提取窗口硬身份键；如果没有这段函数，启动前后窗口去重会散落重复。
    window_id = str(_phase138_get_window_field(window, "window_id") or "")  # 新增代码+Phase138PaintLiveDraw：优先读取 window_id；如果没有这一行，hwnd 场景缺少最稳身份。
    if window_id:  # 新增代码+Phase138PaintLiveDraw：有 window_id 时直接使用；如果没有这一行，真实窗口会退到较弱 pid。
        return f"window_id:{window_id}"  # 新增代码+Phase138PaintLiveDraw：返回 window_id 键；如果没有这一行，baseline 无法识别同一个窗口。
    pid = _phase138_safe_int(_phase138_get_window_field(window, "pid") or _phase138_get_window_field(window, "process_id"))  # 新增代码+Phase138PaintLiveDraw：缺 window_id 时读取 pid；如果没有这一行，部分 fake/未来快照无法形成身份。
    return f"pid:{pid}" if pid else ""  # 新增代码+Phase138PaintLiveDraw：返回 pid 键或空键；如果没有这一行，调用方无法区分无身份窗口。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_window_key 到此结束；如果没有这个边界说明，初学者不容易看出窗口键范围。

def _phase138_snapshot_windows(snapshot: Any) -> list[Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，从不同快照形态取窗口列表；如果没有这段函数，真实 probe 和 fake probe 可能不兼容。
    if isinstance(snapshot, dict):  # 新增代码+Phase138PaintLiveDraw：支持字典快照；如果没有这一行，测试或未来 JSON 快照无法读取。
        return list(snapshot.get("windows") or [])  # 新增代码+Phase138PaintLiveDraw：返回字典里的 windows 列表；如果没有这一行，字典快照会被当成空。
    return list(getattr(snapshot, "windows", []) or [])  # 新增代码+Phase138PaintLiveDraw：返回对象快照里的 windows 列表；如果没有这一行，WindowsWindowInventorySnapshot 无法使用。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_snapshot_windows 到此结束；如果没有这个边界说明，初学者不容易看出快照读取范围。

def _phase138_default_off_report() -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，生成默认关闭零事件证据；如果没有这段函数，安全默认值只能靠口头承诺。
    return {"decision": "real_paint_draw_disabled_by_default", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase138PaintLiveDraw：返回默认关闭证据；如果没有这一行，报告无法证明普通运行不会碰桌面。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_default_off_report 到此结束；如果没有这个边界说明，初学者不容易看出默认安全范围。

def _phase138_unsafe_target_report() -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，生成危险目标零事件证据；如果没有这段函数，终端窗口拒绝没有审计样本。
    return {"decision": "unsafe_target_rejected", "target": "terminal_like_window", "low_level_event_count": 0, "real_desktop_touched": False}  # 新增代码+Phase138PaintLiveDraw：返回危险目标拒绝证据；如果没有这一行，报告无法证明不会向终端发鼠标事件。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_unsafe_target_report 到此结束；如果没有这个边界说明，初学者不容易看出危险目标检查范围。

def _phase138_report_raw_hidden(report_without_raw_check: dict[str, Any], raw_prompt_text: str | None) -> bool:  # 新增代码+Phase138PaintLiveDraw：函数段开始，检查报告没有用户原始 prompt；如果没有这段函数，隐私门禁没有统一事实检查。
    raw_prompt = str(raw_prompt_text or "")  # 新增代码+Phase138PaintLiveDraw：规整可选 prompt 文本；如果没有这一行，None 会导致 in 检查异常。
    serialized = json.dumps(report_without_raw_check, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase138PaintLiveDraw：序列化报告用于全文扫描；如果没有这一行，嵌套字段泄露可能漏检。
    return bool(not raw_prompt or raw_prompt not in serialized)  # 新增代码+Phase138PaintLiveDraw：原始 prompt 不存在才通过；如果没有这一行，用户敏感输入可能写入 artifact。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_report_raw_hidden 到此结束；如果没有这个边界说明，初学者不容易看出脱敏检查范围。

def _phase138_observation_summary(frame: dict[str, Any], state_changed_after_action: bool = False) -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，把真实观察帧压成 Phase8 友好摘要；如果没有这段函数，报告会过大或泄露细节。
    safe_frame = _phase138_safe_dict(frame)  # 新增代码+Phase138PaintLiveDraw：清洗观察帧；如果没有这一行，坏观察 provider 输出会导致异常。
    screenshot = _phase138_safe_dict(safe_frame.get("screenshot"))  # 新增代码+Phase138PaintLiveDraw：读取截图摘要；如果没有这一行，截图路径和像素 guard 不好复用。
    artifact_path = str(screenshot.get("artifact_path") or "")  # 新增代码+Phase138PaintLiveDraw：读取融合层保留的截图 artifact 路径；如果没有这一行，前后截图无法机器比较。
    artifact_hash = _phase138_file_sha256_16(artifact_path)  # 新增代码+Phase138PaintLiveDraw：生成截图短哈希；如果没有这一行，状态变化只能靠肉眼确认。
    return {"screenshot_captured": bool(safe_frame.get("screenshot_observation") or safe_frame.get("screenshot_artifact_openable")), "uia_tree_observation": bool(safe_frame.get("uia_tree_observation") or safe_frame.get("uia_or_vision_targeting")), "window_state_observation": bool(safe_frame.get("window_state_observation") or safe_frame.get("real_window_inventory")), "state_changed_after_action": bool(state_changed_after_action), "raw_text_included": bool(safe_frame.get("raw_text_included")), "observation_frame_model": str(safe_frame.get("model", "")), "screenshot_artifact_openable": bool(safe_frame.get("screenshot_artifact_openable") or screenshot.get("artifact_openable")), "pixel_guard_passed": bool(safe_frame.get("pixel_guard_passed") or screenshot.get("pixel_guard_passed")), "screenshot_artifact_path": artifact_path, "screenshot_sha256_16": artifact_hash}  # 新增代码+Phase138PaintLiveDraw：返回脱敏观察摘要；如果没有这一行，最终矩阵拿不到前后观察字段。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_observation_summary 到此结束；如果没有这个边界说明，初学者不容易看出观察摘要范围。

def _phase138_phase8_observation(source: dict[str, Any], include_state_change: bool = False) -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，把本合同观察字段转成 Phase8 字段；如果没有这段函数，builder 格式会漂移。
    observation = {"screenshot_captured": bool(source.get("screenshot_captured")), "uia_tree_observation": bool(source.get("uia_tree_observation") or source.get("uia_or_vision_targeting") or source.get("vision_targeting")), "window_state_observation": bool(source.get("window_state_observation"))}  # 新增代码+Phase138PaintLiveDraw：转换基础观察字段；如果没有这一行，前后观察无法进入最终矩阵。
    if include_state_change:  # 新增代码+Phase138PaintLiveDraw：只有 after 观察需要状态变化字段；如果没有这一行，before 也会出现无意义变化字段。
        observation["state_changed_after_action"] = bool(source.get("state_changed_after_action"))  # 新增代码+Phase138PaintLiveDraw：添加动作后状态变化；如果没有这一行，Phase8 会拒绝缺少变化证据。
    return observation  # 新增代码+Phase138PaintLiveDraw：返回 Phase8 观察摘要；如果没有这一行，builder 调用没有结果。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_phase8_observation 到此结束；如果没有这个边界说明，初学者不容易看出观察转换范围。

def _phase138_phase8_target_identity(target_window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，把目标窗口摘要转成 Phase8 身份；如果没有这段函数，最终矩阵无法确认目标。
    return {"window_id": str(target_window.get("window_id") or ""), "hwnd": _phase138_safe_int(target_window.get("hwnd")), "process_name": str(target_window.get("process_name") or target_window.get("app_id") or "mspaint.exe"), "title_preview": str(target_window.get("title_preview") or "Paint")}  # 新增代码+Phase138PaintLiveDraw：返回 Phase8 需要的目标字段；如果没有这一行，target_identity 会缺 id 或进程/标题线索。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_phase8_target_identity 到此结束；如果没有这个边界说明，初学者不容易看出目标转换范围。

def _phase138_sender_kind_from_result(sender: Any, result: dict[str, Any]) -> str:  # 新增代码+Phase138PaintLiveDraw：函数段开始，从发送结果提取 sender 身份；如果没有这段函数，fake 和真实 sender 难区分。
    kind = str(result.get("sender_kind") or result.get("sender") or "")  # 新增代码+Phase138PaintLiveDraw：优先读取 sender 上报字段；如果没有这一行，真实 sender 身份不会进入报告。
    return kind or type(sender).__name__  # 新增代码+Phase138PaintLiveDraw：没有字段时回退类名；如果没有这一行，报告可能缺 sender_kind。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_sender_kind_from_result 到此结束；如果没有这个边界说明，初学者不容易看出 sender 身份来源。

def _phase138_sender_is_physical(sender_kind: str, low_level_event_count: int, result: dict[str, Any]) -> bool:  # 新增代码+Phase138PaintLiveDraw：函数段开始，判断 sender 是否真实物理派发；如果没有这段函数，记录器可能冒充真实鼠标。
    lowered = str(sender_kind or "").lower()  # 新增代码+Phase138PaintLiveDraw：标准化 sender 名称；如果没有这一行，大小写会影响判断。
    return bool(low_level_event_count > 0 and "windows_sendinput" in lowered and "record" not in lowered and "fake" not in lowered and result.get("ok"))  # 新增代码+Phase138PaintLiveDraw：要求事件数、真实 sender 名称和发送成功；如果没有这一行，空动作或 fake sender 可能误过。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_sender_is_physical 到此结束；如果没有这个边界说明，初学者不容易看出真实 sender 判断范围。

def _phase138_canvas_rect(window: dict[str, Any]) -> dict[str, int]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，根据 Paint 窗口粗略估算画布安全区域；如果没有这段函数，鼠标拖拽可能打到工具栏。
    rect = _phase138_safe_dict(window.get("rect"))  # 新增代码+Phase138PaintLiveDraw：读取窗口矩形；如果没有这一行，坐标计算没有边界输入。
    left = _phase138_safe_int(rect.get("left"))  # 新增代码+Phase138PaintLiveDraw：读取窗口左边界；如果没有这一行，画布 x 起点无法计算。
    top = _phase138_safe_int(rect.get("top"))  # 新增代码+Phase138PaintLiveDraw：读取窗口上边界；如果没有这一行，画布 y 起点无法计算。
    right = _phase138_safe_int(rect.get("right"),) or left + 1000  # 新增代码+Phase138PaintLiveDraw：读取窗口右边界并兜底宽度；如果没有这一行，缺 rect 时会得到零宽区域。
    bottom = _phase138_safe_int(rect.get("bottom")) or top + 700  # 新增代码+Phase138PaintLiveDraw：读取窗口下边界并兜底高度；如果没有这一行，缺 rect 时会得到零高区域。
    width = max(300, right - left)  # 新增代码+Phase138PaintLiveDraw：计算窗口宽度且设下限；如果没有这一行，小窗口会导致画布区域过窄。
    height = max(240, bottom - top)  # 新增代码+Phase138PaintLiveDraw：计算窗口高度且设下限；如果没有这一行，小窗口会导致画布区域过矮。
    canvas_left = left + max(260, width // 5)  # 新增代码+Phase138PaintLiveDraw：避开 Paint 左侧和顶部工具区域；如果没有这一行，第一笔可能画到工具栏。
    canvas_top = top + max(240, height // 4)  # 新增代码+Phase138PaintLiveDraw：避开 Paint ribbon 菜单区；如果没有这一行，拖拽可能无法落到画布。
    canvas_right = max(canvas_left + 240, right - max(80, width // 12))  # 新增代码+Phase138PaintLiveDraw：保留右侧安全边距；如果没有这一行，笔画可能越过窗口边界。
    canvas_bottom = max(canvas_top + 180, bottom - max(80, height // 10))  # 新增代码+Phase138PaintLiveDraw：保留下方安全边距；如果没有这一行，笔画可能落到状态栏。
    return {"left": canvas_left, "top": canvas_top, "right": canvas_right, "bottom": canvas_bottom, "width": canvas_right - canvas_left, "height": canvas_bottom - canvas_top}  # 新增代码+Phase138PaintLiveDraw：返回画布估算区域；如果没有这一行，绘图 primitive 没有坐标输入。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_canvas_rect 到此结束；如果没有这个边界说明，初学者不容易看出画布估算范围。

def _phase138_attach_target(events: list[dict[str, Any]], window: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，把脱敏目标身份附加到低层事件；如果没有这段函数，事件审计看不出绑定窗口。
    target = _phase138_window_identity(window)  # 新增代码+Phase138PaintLiveDraw：生成目标身份摘要；如果没有这一行，事件没有可审计目标。
    enriched: list[dict[str, Any]] = []  # 新增代码+Phase138PaintLiveDraw：准备保存事件副本；如果没有这一行，不能避免污染原事件。
    for event in list(events or []):  # 新增代码+Phase138PaintLiveDraw：逐条复制事件；如果没有这一行，只能给第一条事件加目标。
        copied = dict(event)  # 新增代码+Phase138PaintLiveDraw：复制当前事件；如果没有这一行，原始 primitive 结果会被原地修改。
        copied["target"] = dict(target)  # 新增代码+Phase138PaintLiveDraw：写入脱敏目标身份；如果没有这一行，最后一跳缺少窗口边界证据。
        copied["real_dispatch_allowed"] = True  # 新增代码+Phase138PaintLiveDraw：标记本合同双门打开后允许真实发送；如果没有这一行，审计看不出这批事件不是普通记录路径。
        enriched.append(copied)  # 新增代码+Phase138PaintLiveDraw：保存处理后的事件；如果没有这一行，事件列表会丢失。
    return enriched  # 新增代码+Phase138PaintLiveDraw：返回带目标身份的事件列表；如果没有这一行，sender 拿不到要发送的事件。
# 新增代码+Phase138PaintLiveDraw：函数段结束，_phase138_attach_target 到此结束；如果没有这个边界说明，初学者不容易看出事件绑定范围。

class Phase138WindowsPaintLiveDrawDriver:  # 新增代码+Phase138PaintLiveDraw：类段开始，执行受控真实 Paint 绘图验收；如果没有这个类，CLI 双门打开后没有真实 driver。
    def __init__(self, inventory: Any | None = None, sender: Any | None = None, observation_runtime: Any | None = None, launch_command: list[str] | None = None, timeout_seconds: float = 12.0) -> None:  # 新增代码+Phase138PaintLiveDraw：函数段开始，注入或创建真实依赖；如果没有这段函数，单测无法替换依赖且生产路径无法启动。
        self.inventory = inventory if inventory is not None else WindowsWindowInventoryProbe()  # 新增代码+Phase138PaintLiveDraw：保存窗口枚举器；如果没有这一行，driver 找不到 Paint。
        self.sender = sender if sender is not None else WindowsSendInputLowLevelSender()  # 新增代码+Phase138PaintLiveDraw：保存真实 SendInput sender；如果没有这一行，鼠标拖拽无法触达桌面。
        self.observation_runtime = observation_runtime if observation_runtime is not None else UniversalRealObservationFrameRuntime(inventory_probe=self.inventory)  # 新增代码+Phase138PaintLiveDraw：保存真实观察 runtime 并共享 inventory；如果没有这一行，前后观察可能看不同事实源。
        self.launch_command = list(launch_command or ["mspaint.exe"])  # 新增代码+Phase138PaintLiveDraw：保存启动命令；如果没有这一行，driver 不知道如何打开 Paint。
        self.timeout_seconds = max(1.0, float(timeout_seconds))  # 新增代码+Phase138PaintLiveDraw：保存并限制最小超时；如果没有这一行，窗口轮询可能立即失败。
    # 新增代码+Phase138PaintLiveDraw：函数段结束，Phase138WindowsPaintLiveDrawDriver.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出依赖初始化范围。

    def _snapshot_windows(self) -> list[Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，读取当前窗口列表；如果没有这段函数，poll 和 recheck 会重复处理快照格式。
        return _phase138_snapshot_windows(self.inventory.snapshot())  # 新增代码+Phase138PaintLiveDraw：返回快照中的窗口列表；如果没有这一行，driver 没有真实窗口事实。
    # 新增代码+Phase138PaintLiveDraw：函数段结束，Phase138WindowsPaintLiveDrawDriver._snapshot_windows 到此结束；如果没有这个边界说明，初学者不容易看出快照范围。

    def _poll_paint_window(self, baseline_keys: set[str]) -> tuple[dict[str, Any] | None, bool]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，等待新 Paint 窗口出现；如果没有这段函数，启动延迟会误判失败。
        deadline = time.time() + self.timeout_seconds  # 新增代码+Phase138PaintLiveDraw：计算超时截止时间；如果没有这一行，等待可能无限持续。
        while time.time() <= deadline:  # 新增代码+Phase138PaintLiveDraw：在超时前持续轮询；如果没有这一行，异步启动窗口无法等待。
            candidates = [window for window in self._snapshot_windows() if _phase138_is_paint_window(window)]  # 新增代码+Phase138PaintLiveDraw：筛选 Paint 候选窗口；如果没有这一行，目标可能是任意窗口。
            new_candidates = [window for window in candidates if _phase138_window_key(window) and _phase138_window_key(window) not in baseline_keys]  # 新增代码+Phase138PaintLiveDraw：优先选择启动后新增窗口；如果没有这一行，可能误用用户原有 Paint。
            if new_candidates:  # 新增代码+Phase138PaintLiveDraw：检查是否找到本次新增 Paint；如果没有这一行，找到也不会返回。
                return dict(new_candidates[0]), True  # 新增代码+Phase138PaintLiveDraw：返回新增 Paint 且标记 owned；如果没有这一行，后续无法清理本次窗口。
            time.sleep(0.25)  # 新增代码+Phase138PaintLiveDraw：短暂等待后重试；如果没有这一行，轮询会占满 CPU。
        return None, False  # 新增代码+Phase138PaintLiveDraw：超时返回定位失败；如果没有这一行，调用方无法诚实报告窗口未找到。
    # 新增代码+Phase138PaintLiveDraw：函数段结束，Phase138WindowsPaintLiveDrawDriver._poll_paint_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口轮询范围。

    def _recheck_target(self, window: dict[str, Any]) -> dict[str, Any] | None:  # 新增代码+Phase138PaintLiveDraw：函数段开始，动作前后复核目标仍是同一个 Paint；如果没有这段函数，焦点或 hwnd 漂移无法拦截。
        current = self.inventory.snapshot()  # 新增代码+Phase138PaintLiveDraw：重新读取真实窗口快照；如果没有这一行，复核只会看旧数据。
        found = current.find_window(window) if hasattr(current, "find_window") else None  # 新增代码+Phase138PaintLiveDraw：按 app_id/window_id 查找目标；如果没有这一行，无法绑定原窗口身份。
        if isinstance(found, dict) and _phase138_is_paint_window(found):  # 新增代码+Phase138PaintLiveDraw：确认找到的窗口仍像 Paint；如果没有这一行，旧 hwnd 可能打到错误窗口。
            return dict(found)  # 新增代码+Phase138PaintLiveDraw：返回复核后的窗口副本；如果没有这一行，调用方拿不到最新 rect。
        wanted_key = _phase138_window_key(window)  # 新增代码+Phase138PaintLiveDraw：读取原窗口身份键作为兜底；如果没有这一行，缺 find_window 的 fake 快照无法复核。
        for candidate in _phase138_snapshot_windows(current):  # 新增代码+Phase138PaintLiveDraw：遍历当前窗口候选；如果没有这一行，兜底匹配无法执行。
            if wanted_key and _phase138_window_key(candidate) == wanted_key and _phase138_is_paint_window(candidate):  # 新增代码+Phase138PaintLiveDraw：同时匹配身份和 Paint 类型；如果没有这一行，标题相似窗口可能混淆。
                return dict(candidate)  # 新增代码+Phase138PaintLiveDraw：返回匹配窗口副本；如果没有这一行，复核结果不会交给调用方。
        return None  # 新增代码+Phase138PaintLiveDraw：没有找到时返回 None；如果没有这一行，调用方无法拒绝发送。
    # 新增代码+Phase138PaintLiveDraw：函数段结束，Phase138WindowsPaintLiveDrawDriver._recheck_target 到此结束；如果没有这个边界说明，初学者不容易看出复核范围。

    def _prepare_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，尽量最大化并置前 Paint 窗口；如果没有这段函数，小窗口画布太小会导致拖拽落错。
        hwnd = _phase138_hwnd_from_window(window)  # 新增代码+Phase138PaintLiveDraw：读取窗口句柄；如果没有这一行，Win32 无法定位目标。
        if hwnd > 0 and sys.platform == "win32":  # 新增代码+Phase138PaintLiveDraw：只有 Windows 且 hwnd 有效才调用 Win32；如果没有这一行，跨平台测试会误触系统 API。
            try:  # 新增代码+Phase138PaintLiveDraw：保护最大化调用；如果没有这一行，窗口管理异常会中断验收。
                import ctypes  # 新增代码+Phase138PaintLiveDraw：延迟导入 ctypes 调用 user32；如果没有这一行，无法最大化窗口。
                ctypes.windll.user32.ShowWindow(hwnd, 3)  # 新增代码+Phase138PaintLiveDraw：最大化 Paint 窗口；如果没有这一行，画布区域可能太小或被工具栏占据。
                ctypes.windll.user32.SetForegroundWindow(hwnd)  # 新增代码+Phase138PaintLiveDraw：把 Paint 置前；如果没有这一行，鼠标事件可能发到旧焦点窗口。
                time.sleep(0.7)  # 新增代码+Phase138PaintLiveDraw：等待窗口完成最大化；如果没有这一行，马上截图和拖拽可能使用旧 rect。
            except Exception:  # 新增代码+Phase138PaintLiveDraw：忽略窗口准备异常并交给后续复核；如果没有这一行，非核心准备失败会盖住主报告。
                pass  # 新增代码+Phase138PaintLiveDraw：保持 driver 继续用原窗口尝试；如果没有这一行，except 语法不完整。
        return self._recheck_target(window) or dict(window)  # 新增代码+Phase138PaintLiveDraw：返回准备后的最新窗口或原窗口；如果没有这一行，调用方无法拿到最大化后的 rect。
    # 新增代码+Phase138PaintLiveDraw：函数段结束，Phase138WindowsPaintLiveDrawDriver._prepare_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口准备范围。

    def _observe_window(self, window: dict[str, Any], state_changed_after_action: bool = False) -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，执行真实只读观察并压缩摘要；如果没有这段函数，报告缺前后观察证据。
        try:  # 新增代码+Phase138PaintLiveDraw：保护真实观察 provider；如果没有这一行，截图或 UIA 异常会让清理无法运行。
            frame = self.observation_runtime.observe(target_hint="paint", real_desktop_touched=state_changed_after_action, target_window=window)  # 新增代码+Phase138PaintLiveDraw：观察绑定 Paint 窗口；如果没有这一行，观察可能选错同名窗口。
            return _phase138_observation_summary(frame, state_changed_after_action=state_changed_after_action)  # 新增代码+Phase138PaintLiveDraw：返回脱敏观察摘要；如果没有这一行，报告会过大或格式不兼容。
        except Exception as error:  # 新增代码+Phase138PaintLiveDraw：捕获观察异常；如果没有这一行，真实桌面权限问题会中断合同。
            return {"screenshot_captured": False, "uia_tree_observation": False, "window_state_observation": False, "state_changed_after_action": bool(state_changed_after_action), "raw_text_included": False, "screenshot_artifact_path": "", "screenshot_sha256_16": "", "reason": f"phase138_observation_failed:{type(error).__name__}"}  # 新增代码+Phase138PaintLiveDraw：诚实返回观察失败类型；如果没有这一行，调用方无法知道证据缺口。
    # 新增代码+Phase138PaintLiveDraw：函数段结束，Phase138WindowsPaintLiveDrawDriver._observe_window 到此结束；如果没有这个边界说明，初学者不容易看出观察范围。

    def _dispatch_pikachu_drag_plan(self, window: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，发送受控皮卡丘拖拽计划；如果没有这段函数，Paint 不会真实绘图。
        hwnd = _phase138_hwnd_from_window(window)  # 新增代码+Phase138PaintLiveDraw：读取目标窗口 hwnd；如果没有这一行，无法把 Paint 置前。
        canvas = _phase138_canvas_rect(window)  # 新增代码+Phase138PaintLiveDraw：估算 Paint 画布区域；如果没有这一行，绘图 primitive 没有落点。
        plan = build_pikachu_drag_plan(canvas)  # 新增代码+Phase138PaintLiveDraw：复用通用皮卡丘拖拽计划；如果没有这一行，Phase138 会退回专用路径。
        drag_paths = [dict(path) for path in list(plan.get("drag_paths", []) or [])[:PHASE138_MAX_REAL_DRAG_PATHS] if isinstance(path, dict)]  # 新增代码+Phase138PaintLiveDraw：只取前几条代表性笔画；如果没有这一行，真实事件过多会拖慢可见终端验收。
        events: list[dict[str, Any]] = [{"type": "set_foreground", "hwnd": hwnd}, {"type": "pause", "seconds": 0.25}]  # 新增代码+Phase138PaintLiveDraw：先聚焦窗口并等待；如果没有这一行，第一笔可能发到旧焦点。
        for path in drag_paths:  # 新增代码+Phase138PaintLiveDraw：逐条处理皮卡丘笔画；如果没有这一行，计划不会变成低层事件。
            events.extend(expand_drag_path_to_low_level_events(list(path.get("points", []) or [])))  # 新增代码+Phase138PaintLiveDraw：把单条笔画展开成鼠标移动/按下/抬起；如果没有这一行，drag_path 只是描述不会执行。
            events.append({"type": "pause", "seconds": 0.04})  # 新增代码+Phase138PaintLiveDraw：每条笔画后短暂停顿；如果没有这一行，Paint 可能吞掉连续过密的拖拽。
        events = _phase138_attach_target(events, window)  # 新增代码+Phase138PaintLiveDraw：给事件写入目标身份；如果没有这一行，审计无法证明事件绑定同一窗口。
        result = self.sender.send_low_level(events) if hasattr(self.sender, "send_low_level") else {"ok": False, "low_level_event_count": 0, "sender": type(self.sender).__name__, "raw_text_included": False, "reason": "sender_missing_send_low_level"}  # 新增代码+Phase138PaintLiveDraw：调用真实 sender 或返回失败；如果没有这一行，动作派发结果不可审计。
        plan_summary = {"drawing_subject": "pikachu", "drawing_primitive_used": True, "drag_path_count": len(drag_paths), "planned_low_level_event_count": len(events), "canvas": canvas, "direct_image_file_cheat": False, "image_file_written": False}  # 新增代码+Phase138PaintLiveDraw：返回不含图片文件的计划摘要；如果没有这一行，报告无法证明没有脚本 artifact 路线。
        return _phase138_safe_dict(result), plan_summary  # 新增代码+Phase138PaintLiveDraw：返回 sender 结果和计划摘要；如果没有这一行，调用方无法汇总动作事实。
    # 新增代码+Phase138PaintLiveDraw：函数段结束，Phase138WindowsPaintLiveDrawDriver._dispatch_pikachu_drag_plan 到此结束；如果没有这个边界说明，初学者不容易看出绘图发送范围。

    def _cleanup_window(self, window: dict[str, Any], owned_window: bool) -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，清理本次拥有的 Paint 窗口；如果没有这段函数，验收可能污染用户桌面。
        pid = _phase138_safe_int(window.get("pid") or window.get("window_process_id") or window.get("process_id"))  # 新增代码+Phase138PaintLiveDraw：读取窗口进程 id；如果没有这一行，终止本次 Paint 没有目标。
        if not owned_window or pid <= 0 or sys.platform != "win32":  # 新增代码+Phase138PaintLiveDraw：非本次窗口或无 pid 时不强行关闭；如果没有这一行，可能关闭用户原有 Paint。
            return {"cleanup_completed": True, "host_hidden_or_restored": True, "lock_released": True, "owned_window": bool(owned_window), "close_attempted": False}  # 新增代码+Phase138PaintLiveDraw：返回未关闭但已恢复边界的证据；如果没有这一行，已有窗口场景会被误清理。
        try:  # 新增代码+Phase138PaintLiveDraw：保护 Win32 进程终止调用；如果没有这一行，清理异常会盖过验收结果。
            import ctypes  # 新增代码+Phase138PaintLiveDraw：延迟导入 ctypes 调用 kernel32；如果没有这一行，无法按 pid 关闭自有 Paint。
            handle = ctypes.windll.kernel32.OpenProcess(0x0001, False, pid)  # 新增代码+Phase138PaintLiveDraw：打开仅终止权限的进程句柄；如果没有这一行，无法避免 Paint 保存提示残留窗口。
            terminated = bool(handle and ctypes.windll.kernel32.TerminateProcess(handle, 0))  # 新增代码+Phase138PaintLiveDraw：终止本次启动的 Paint 进程；如果没有这一行，画完后的保存提示可能卡在桌面。
            if handle:  # 新增代码+Phase138PaintLiveDraw：检查是否拿到句柄；如果没有这一行，CloseHandle 可能收到空句柄。
                ctypes.windll.kernel32.CloseHandle(handle)  # 新增代码+Phase138PaintLiveDraw：释放进程句柄；如果没有这一行，测试进程会泄露系统句柄。
            time.sleep(0.5)  # 新增代码+Phase138PaintLiveDraw：等待窗口消失；如果没有这一行，马上复查可能误判未清理。
            still_there = self._recheck_target(window) is not None  # 新增代码+Phase138PaintLiveDraw：检查目标窗口是否仍存在；如果没有这一行，cleanup_completed 没有事实依据。
            return {"cleanup_completed": bool(terminated and not still_there), "host_hidden_or_restored": bool(terminated), "lock_released": True, "owned_window": True, "close_attempted": True}  # 新增代码+Phase138PaintLiveDraw：返回清理证据；如果没有这一行，Phase8 无法判断是否污染桌面。
        except Exception as error:  # 新增代码+Phase138PaintLiveDraw：捕获清理异常；如果没有这一行，失败清理会让 CLI 崩溃。
            return {"cleanup_completed": False, "host_hidden_or_restored": False, "lock_released": True, "owned_window": True, "close_attempted": True, "reason": f"phase138_cleanup_failed:{type(error).__name__}"}  # 新增代码+Phase138PaintLiveDraw：返回清理失败摘要；如果没有这一行，用户不知道是否残留窗口。
    # 新增代码+Phase138PaintLiveDraw：函数段结束，Phase138WindowsPaintLiveDrawDriver._cleanup_window 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。

    def run(self, *, run_root: Path, subject: str) -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，执行完整真实 Paint 绘图闭环；如果没有这段函数，合同无法触达真实代表应用。
        run_root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase138PaintLiveDraw：确保运行目录存在；如果没有这一行，报告附属证据可能无法写入。
        baseline_keys = {_phase138_window_key(window) for window in self._snapshot_windows() if _phase138_window_key(window)}  # 新增代码+Phase138PaintLiveDraw：记录启动前窗口集合；如果没有这一行，无法区分本次新开的 Paint。
        process = None  # 新增代码+Phase138PaintLiveDraw：初始化进程对象；如果没有这一行，启动失败路径无法安全引用变量。
        try:  # 新增代码+Phase138PaintLiveDraw：保护启动和动作全过程；如果没有这一行，异常会绕过结构化失败报告。
            process = subprocess.Popen(self.launch_command, shell=False)  # 新增代码+Phase138PaintLiveDraw：启动 Windows Paint；如果没有这一行，真实窗口不会出现。
            window, owned_window = self._poll_paint_window(baseline_keys)  # 新增代码+Phase138PaintLiveDraw：等待并定位 Paint 窗口；如果没有这一行，后续动作没有目标。
            if window is None:  # 新增代码+Phase138PaintLiveDraw：检查是否定位失败；如果没有这一行，None 会进入 SendInput。
                return {"ok": False, "driver": "phase138_windows_paint_live_draw_driver", "reason": "paint_window_not_found", "paint_process_verified": False, "target_rechecked_before_input": False, "target_rechecked_before_result": False, "drawing_plan_executed": False, "canvas_changed_after_real_actions": False, "screenshot_before_after_different": False, "real_desktop_touched": False, "low_level_event_count": 0, "raw_text_included": False, "target_window": {}, "before_observation": {}, "after_observation": {}, "cleanup_evidence": {"cleanup_completed": True, "host_hidden_or_restored": True, "lock_released": True}, "physical_desktop_dispatch_performed": False, "real_sendinput_dispatch": False, "sender_kind": "", "plan_summary": {}}  # 新增代码+Phase138PaintLiveDraw：返回定位失败摘要；如果没有这一行，调用方无法审计失败点。
            prepared_window = self._prepare_window(window)  # 新增代码+Phase138PaintLiveDraw：最大化并置前 Paint；如果没有这一行，画布坐标可能过小或过旧。
            paint_verified = _phase138_is_paint_window(prepared_window)  # 新增代码+Phase138PaintLiveDraw：确认目标像 Paint；如果没有这一行，可能向错误窗口发鼠标。
            input_window = self._recheck_target(prepared_window) if paint_verified else None  # 新增代码+Phase138PaintLiveDraw：输入前复核目标仍存在；如果没有这一行，焦点漂移风险无法拦截。
            before_observation = self._observe_window(input_window or prepared_window, state_changed_after_action=False) if input_window else {}  # 新增代码+Phase138PaintLiveDraw：动作前观察 Paint；如果没有这一行，闭环缺少 before 证据。
            dispatch_result, plan_summary = self._dispatch_pikachu_drag_plan(input_window) if input_window else ({"ok": False, "low_level_event_count": 0, "sender": type(self.sender).__name__, "raw_text_included": False}, {})  # 新增代码+Phase138PaintLiveDraw：只有复核通过才发送拖拽；如果没有这一行，错误目标也可能收到事件。
            time.sleep(1.0)  # 新增代码+Phase138PaintLiveDraw：等待 Paint 渲染笔画；如果没有这一行，动作后截图可能太早。
            result_window = self._recheck_target(input_window) if input_window else None  # 新增代码+Phase138PaintLiveDraw：读取结果前再次复核目标；如果没有这一行，结果可能来自错误窗口。
            low_level_event_count = _phase138_safe_int(dispatch_result.get("low_level_event_count"))  # 新增代码+Phase138PaintLiveDraw：读取低层事件数量；如果没有这一行，空动作可能被误过。
            sender_kind = _phase138_sender_kind_from_result(self.sender, dispatch_result)  # 新增代码+Phase138PaintLiveDraw：提取 sender 身份；如果没有这一行，报告无法证明是不是真实 SendInput。
            physical_dispatch = _phase138_sender_is_physical(sender_kind, low_level_event_count, dispatch_result)  # 新增代码+Phase138PaintLiveDraw：判断是否真实物理派发；如果没有这一行，recording sender 可冒充真实。
            after_observation = self._observe_window(result_window or input_window or prepared_window, state_changed_after_action=bool(dispatch_result.get("ok") and physical_dispatch)) if result_window else {}  # 新增代码+Phase138PaintLiveDraw：动作后重新观察 Paint；如果没有这一行，闭环缺少 after 证据。
            screenshot_before_after_different = bool(before_observation.get("screenshot_sha256_16") and after_observation.get("screenshot_sha256_16") and before_observation.get("screenshot_sha256_16") != after_observation.get("screenshot_sha256_16"))  # 新增代码+Phase138PaintLiveDraw：比较前后截图哈希；如果没有这一行，画布变化只能靠 driver 自报。
            canvas_changed = bool(physical_dispatch and screenshot_before_after_different)  # 新增代码+Phase138PaintLiveDraw：只有真实派发且截图变化才算画布变化；如果没有这一行，空截图或 fake sender 可能误过。
            cleanup_evidence = self._cleanup_window(result_window or input_window or prepared_window, owned_window=owned_window)  # 新增代码+Phase138PaintLiveDraw：清理本次窗口；如果没有这一行，Paint 可能残留在桌面。
            return {"ok": bool(paint_verified and input_window and result_window and subject == "pikachu" and plan_summary.get("drawing_primitive_used") and canvas_changed), "driver": "phase138_windows_paint_live_draw_driver", "reason": "" if canvas_changed else "paint_canvas_change_not_observed", "paint_process_verified": bool(paint_verified), "target_rechecked_before_input": bool(input_window), "target_rechecked_before_result": bool(result_window), "drawing_plan_executed": bool(plan_summary.get("drawing_primitive_used") and plan_summary.get("drag_path_count", 0)), "canvas_changed_after_real_actions": canvas_changed, "screenshot_before_after_different": screenshot_before_after_different, "target_window": _phase138_window_identity(result_window or input_window or prepared_window), "before_observation": before_observation, "after_observation": after_observation, "cleanup_evidence": cleanup_evidence, "real_desktop_touched": bool(low_level_event_count), "physical_desktop_dispatch_performed": physical_dispatch, "real_sendinput_dispatch": physical_dispatch, "sender_kind": sender_kind, "low_level_event_count": low_level_event_count, "raw_text_included": False, "plan_summary": plan_summary}  # 新增代码+Phase138PaintLiveDraw：返回脱敏闭环报告；如果没有这一行，合同层拿不到真实执行事实。
        except Exception as error:  # 新增代码+Phase138PaintLiveDraw：捕获真实路径异常；如果没有这一行，CLI 会输出堆栈而不是结构化失败。
            return {"ok": False, "driver": "phase138_windows_paint_live_draw_driver", "reason": f"phase138_driver_failed:{type(error).__name__}", "paint_process_verified": False, "target_rechecked_before_input": False, "target_rechecked_before_result": False, "drawing_plan_executed": False, "canvas_changed_after_real_actions": False, "screenshot_before_after_different": False, "real_desktop_touched": False, "low_level_event_count": 0, "raw_text_included": False, "target_window": {}, "before_observation": {}, "after_observation": {}, "cleanup_evidence": {"cleanup_completed": False, "host_hidden_or_restored": False, "lock_released": True}, "physical_desktop_dispatch_performed": False, "real_sendinput_dispatch": False, "sender_kind": "", "plan_summary": {}}  # 新增代码+Phase138PaintLiveDraw：返回异常失败摘要；如果没有这一行，验收失败难以定位。
        finally:  # 新增代码+Phase138PaintLiveDraw：最后兜底处理启动进程对象；如果没有这一行，经典 mspaint.exe 进程可能残留。
            if process is not None and process.poll() is None:  # 新增代码+Phase138PaintLiveDraw：只有进程仍在运行时才尝试等待；如果没有这一行，已退出进程会被误处理。
                try:  # 新增代码+Phase138PaintLiveDraw：保护短等待；如果没有这一行，进程状态异常会盖过主报告。
                    process.wait(timeout=0.2)  # 新增代码+Phase138PaintLiveDraw：给进程自然退出机会；如果没有这一行，可能过早 terminate。
                except Exception:  # 新增代码+Phase138PaintLiveDraw：忽略兜底等待异常；如果没有这一行，清理分支可能抛出无关错误。
                    pass  # 新增代码+Phase138PaintLiveDraw：保持主报告为准；如果没有这一行，except 语法不完整。
    # 新增代码+Phase138PaintLiveDraw：函数段结束，Phase138WindowsPaintLiveDrawDriver.run 到此结束；如果没有这个边界说明，初学者不容易看出真实闭环范围。
# 新增代码+Phase138PaintLiveDraw：类段结束，Phase138WindowsPaintLiveDrawDriver 到此结束；如果没有这个边界说明，初学者不容易看出真实 driver 范围。

def build_phase138_paint_real_desktop_closure_evidence(report: dict[str, Any] | None, representative_acceptance: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，把 Paint 成功报告接成 Phase8 最终矩阵证据；如果没有这段函数，局部验收无法进入 Layer A。
    safe_report = _phase138_safe_dict(report)  # 新增代码+Phase138PaintLiveDraw：清洗合同报告；如果没有这一行，None 或坏类型会让 builder 崩溃。
    target_window = _phase138_safe_dict(safe_report.get("target_window"))  # 新增代码+Phase138PaintLiveDraw：读取目标窗口摘要；如果没有这一行，target_identity 没有来源。
    before_observation = _phase138_safe_dict(safe_report.get("before_observation"))  # 新增代码+Phase138PaintLiveDraw：读取动作前观察；如果没有这一行，Phase8 before 字段为空。
    after_observation = _phase138_safe_dict(safe_report.get("after_observation"))  # 新增代码+Phase138PaintLiveDraw：读取动作后观察；如果没有这一行，Phase8 after 字段为空。
    cleanup_evidence = _phase138_safe_dict(safe_report.get("cleanup_evidence"))  # 新增代码+Phase138PaintLiveDraw：读取清理证据；如果没有这一行，Phase8 cleanup 字段为空。
    report_success = bool(safe_report.get("passed") and safe_report.get("real_paint_draw_executed") and safe_report.get("paint_process_verified") and safe_report.get("target_rechecked_before_input") and safe_report.get("target_rechecked_before_result") and safe_report.get("drawing_plan_executed") and safe_report.get("canvas_changed_after_real_actions") and safe_report.get("screenshot_before_after_different") and safe_report.get("raw_text_hidden"))  # 新增代码+Phase138PaintLiveDraw：汇总能进入最终矩阵的强条件；如果没有这一行，部分成功会被误当完整闭环。
    representatives = _phase138_safe_dict(representative_acceptance)  # 新增代码+Phase138PaintLiveDraw：复制外部代表应用验收汇总；如果没有这一行，Notepad/Calculator/Browser 的上游验收无法保留。
    representatives["paint"] = bool(report_success)  # 新增代码+Phase138PaintLiveDraw：用 Paint 本合同成功覆盖 Paint 代表位；如果没有这一行，Paint 缺口不会缩小。
    sender_kind = str(safe_report.get("sender_kind") or "").lower()  # 新增代码+Phase138PaintLiveDraw：读取 sender 类型；如果没有这一行，action 字段无法归一。
    normalized_sender_kind = "windows_sendinput" if sender_kind == "windows_sendinput_low_level" else sender_kind  # 新增代码+Phase138PaintLiveDraw：把底层 sender 名称归一成矩阵稳定值；如果没有这一行，最终矩阵和测试字段会漂移。
    return {"target_identity": _phase138_phase8_target_identity(target_window), "before_observation": _phase138_phase8_observation(before_observation), "action": {"physical_desktop_dispatch_performed": bool(report_success and safe_report.get("physical_desktop_dispatch_performed")), "real_sendinput_dispatch": bool(report_success and safe_report.get("real_sendinput_dispatch")), "sender_kind": normalized_sender_kind, "low_level_event_count": _phase138_safe_int(safe_report.get("low_level_event_count"))}, "after_observation": _phase138_phase8_observation(after_observation, include_state_change=True), "verification": {"verified": report_success, "decision": "accepted" if report_success else "rejected", "reason": str(safe_report.get("driver_reason") or safe_report.get("reason") or "phase138_paint_contract")}, "cleanup": {"cleanup_completed": bool(cleanup_evidence.get("cleanup_completed")), "host_hidden_or_restored": bool(cleanup_evidence.get("host_hidden_or_restored")), "lock_released": bool(cleanup_evidence.get("lock_released"))}, "representative_acceptance": representatives, "target_identity_rechecked_before_each_action": bool(safe_report.get("target_rechecked_before_input") and safe_report.get("target_rechecked_before_result")), "script_artifact_route_blocked": bool(not safe_report.get("uncontrolled_actions_expanded")), "uncontrolled_high_risk_actions_allowed": bool(safe_report.get("uncontrolled_actions_expanded"))}  # 新增代码+Phase138PaintLiveDraw：返回 Phase8 校验器需要的完整闭环形状；如果没有这一行，最终矩阵无法判断 Paint 是否真的成熟。
# 新增代码+Phase138PaintLiveDraw：函数段结束，build_phase138_paint_real_desktop_closure_evidence 到此结束；如果没有这个边界说明，初学者不容易看出 Phase8 接入范围。

def run_phase138_controlled_paint_live_draw_contract(base_dir: str | Path | None = None, real_run: bool | None = None, allow_real_gate: bool | None = None, paint_driver: Any | None = None, require_injected_driver: bool = False, raw_prompt_text: str | None = None) -> dict[str, Any]:  # 新增代码+Phase138PaintLiveDraw：函数段开始，运行 Phase138 总合同入口；如果没有这段函数，测试和 CLI 没有统一事实源。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE138_CONTROLLED_PAINT_LIVE_DRAW_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase138PaintLiveDraw：选择隔离运行目录；如果没有这一行，多次运行可能互相覆盖。
    root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase138PaintLiveDraw：创建运行目录；如果没有这一行，报告写入会失败。
    subject = "pikachu"  # 新增代码+Phase138PaintLiveDraw：固定受控绘图主题；如果没有这一行，用户 prompt 可能被误当作任意绘图命令。
    requested = _phase138_request_real_run(real_run)  # 新增代码+Phase138PaintLiveDraw：判断本次是否请求真实路径；如果没有这一行，默认和显式路径会混淆。
    gate_enabled = _phase138_real_gate_enabled(allow_real_gate)  # 新增代码+Phase138PaintLiveDraw：判断真实路径是否被第二道门允许；如果没有这一行，真实桌面动作缺少双确认。
    default_report = _phase138_default_off_report()  # 新增代码+Phase138PaintLiveDraw：收集默认关闭证据；如果没有这一行，默认安全字段没有事实来源。
    unsafe_report = _phase138_unsafe_target_report()  # 新增代码+Phase138PaintLiveDraw：收集危险目标拒绝证据；如果没有这一行，unsafe 字段没有事实来源。
    default_zero = bool(default_report.get("low_level_event_count") == 0 and not default_report.get("real_desktop_touched"))  # 新增代码+Phase138PaintLiveDraw：确认默认关闭没有物理事件；如果没有这一行，默认安全值无法量化。
    unsafe_zero = bool(unsafe_report.get("low_level_event_count") == 0 and not unsafe_report.get("real_desktop_touched"))  # 新增代码+Phase138PaintLiveDraw：确认危险目标没有物理事件；如果没有这一行，危险拦截值无法量化。
    driver_report: dict[str, Any] = {"ok": False, "driver": "not_requested", "reason": "real_paint_draw_not_requested", "real_desktop_touched": False, "raw_text_included": False}  # 新增代码+Phase138PaintLiveDraw：准备默认不执行 driver 报告；如果没有这一行，默认关闭路径缺少统一字段。
    if requested and gate_enabled and paint_driver is not None:  # 新增代码+Phase138PaintLiveDraw：只有请求门、允许门、注入 driver 同时存在才执行注入路径；如果没有这一行，单测可能误触真实桌面。
        driver_report = dict(paint_driver.run(run_root=root, subject=subject))  # 新增代码+Phase138PaintLiveDraw：调用注入 driver；如果没有这一行，fake 合同不能提供成功事实。
    elif requested and gate_enabled and require_injected_driver:  # 新增代码+Phase138PaintLiveDraw：要求注入 driver 但没提供时安全失败；如果没有这一行，fake-only 测试可能绕到真实桌面。
        driver_report = {"ok": False, "driver": "missing_injected_driver", "reason": "require_injected_driver_without_driver", "real_desktop_touched": False, "raw_text_included": False}  # 新增代码+Phase138PaintLiveDraw：记录缺少注入 driver 且不触桌面；如果没有这一行，失败原因不清楚。
    elif requested and gate_enabled:  # 新增代码+Phase138PaintLiveDraw：双门打开且无注入时使用真实 driver；如果没有这一行，真实可见终端验收无法跑 Paint。
        driver_report = Phase138WindowsPaintLiveDrawDriver().run(run_root=root, subject=subject)  # 新增代码+Phase138PaintLiveDraw：执行生产真实 Paint 闭环；如果没有这一行，CLI 只能停在占位失败。
    elif requested and not gate_enabled:  # 新增代码+Phase138PaintLiveDraw：请求真实但允许门关闭时拒绝；如果没有这一行，用户可能误以为单门即可触发真实桌面。
        driver_report = {"ok": False, "driver": "gate_rejected", "reason": "phase138_real_gate_disabled", "real_desktop_touched": False, "raw_text_included": False}  # 新增代码+Phase138PaintLiveDraw：记录 gate 拒绝且不触桌面；如果没有这一行，拒绝原因不清楚。
    real_executed = bool(requested and gate_enabled and driver_report.get("ok"))  # 新增代码+Phase138PaintLiveDraw：汇总真实 Paint 是否成功执行；如果没有这一行，CLI token 无法表达代表应用通过。
    real_desktop_touched = bool(driver_report.get("real_desktop_touched"))  # 新增代码+Phase138PaintLiveDraw：保留任何真实桌面触达事实；如果没有这一行，失败/半执行副作用可能被隐藏。
    report_path = root / "reports" / "phase138_controlled_paint_live_draw_report.json"  # 新增代码+Phase138PaintLiveDraw：定义合同报告路径；如果没有这一行，验收失败时很难找证据。
    report_without_raw_check: dict[str, Any] = {"marker": PHASE138_CONTROLLED_PAINT_LIVE_DRAW_MARKER, "ok_token": PHASE138_CONTROLLED_PAINT_LIVE_DRAW_OK_TOKEN, "model": PHASE138_CONTROLLED_PAINT_LIVE_DRAW_MODEL, "real_paint_draw_env": PHASE138_REAL_PAINT_DRAW_ENV, "real_paint_draw_request_env": PHASE138_REAL_PAINT_DRAW_REQUEST_ENV, "real_run_requested": requested, "real_enable_gate_required": True, "real_enable_gate_passed": gate_enabled, "require_injected_driver": bool(require_injected_driver), "drawing_subject": subject, "default_off_zero_physical_events": default_zero, "unsafe_target_zero_physical_events": unsafe_zero, "real_paint_draw_executed": real_executed, "paint_process_verified": bool(driver_report.get("paint_process_verified")), "target_rechecked_before_input": bool(driver_report.get("target_rechecked_before_input")), "target_rechecked_before_result": bool(driver_report.get("target_rechecked_before_result")), "drawing_plan_executed": bool(driver_report.get("drawing_plan_executed")), "canvas_changed_after_real_actions": bool(driver_report.get("canvas_changed_after_real_actions")), "screenshot_before_after_different": bool(driver_report.get("screenshot_before_after_different")), "real_desktop_touched": real_desktop_touched, "uncontrolled_actions_expanded": PHASE138_UNCONTROLLED_ACTIONS_EXPANDED, "driver": str(driver_report.get("driver", "")), "driver_ok": bool(driver_report.get("ok")), "driver_reason": str(driver_report.get("reason", "")), "default_off_report": default_report, "unsafe_report": unsafe_report}  # 新增代码+Phase138PaintLiveDraw：构造脱敏报告主体；如果没有这一行，测试和 CLI 会丢失关键事实。
    report_without_raw_check.update({"target_window": _phase138_safe_dict(driver_report.get("target_window")), "before_observation": _phase138_safe_dict(driver_report.get("before_observation")), "after_observation": _phase138_safe_dict(driver_report.get("after_observation")), "cleanup_evidence": _phase138_safe_dict(driver_report.get("cleanup_evidence")), "physical_desktop_dispatch_performed": bool(driver_report.get("physical_desktop_dispatch_performed")), "real_sendinput_dispatch": bool(driver_report.get("real_sendinput_dispatch")), "sender_kind": str(driver_report.get("sender_kind") or ""), "low_level_event_count": _phase138_safe_int(driver_report.get("low_level_event_count")), "plan_summary": _phase138_safe_dict(driver_report.get("plan_summary"))})  # 新增代码+Phase138PaintLiveDraw：合并 Phase8 关键证据字段；如果没有这一行，builder 无法恢复真实闭环。
    raw_text_hidden = bool(_phase138_report_raw_hidden(report_without_raw_check, raw_prompt_text) and not driver_report.get("raw_text_included"))  # 新增代码+Phase138PaintLiveDraw：检查原始 prompt 没有进入报告；如果没有这一行，隐私门禁无法落地。
    passed = bool(default_zero and unsafe_zero and raw_text_hidden and not PHASE138_UNCONTROLLED_ACTIONS_EXPANDED and ((not requested and not report_without_raw_check["real_desktop_touched"]) or (requested and gate_enabled and real_executed and report_without_raw_check["paint_process_verified"] and report_without_raw_check["target_rechecked_before_input"] and report_without_raw_check["target_rechecked_before_result"] and report_without_raw_check["drawing_plan_executed"] and report_without_raw_check["canvas_changed_after_real_actions"] and report_without_raw_check["screenshot_before_after_different"])))  # 新增代码+Phase138PaintLiveDraw：汇总合同通过条件；如果没有这一行，main 无法用退出码表达成功或失败。
    report = dict(report_without_raw_check, raw_text_hidden=raw_text_hidden, passed=passed, report_path=str(report_path))  # 新增代码+Phase138PaintLiveDraw：补齐最终报告字段；如果没有这一行，调用方拿不到 passed、脱敏和路径。
    atomic_write_json(report_path, report)  # 新增代码+Phase138PaintLiveDraw：原子写入报告文件；如果没有这一行，验收和排查没有落盘证据。
    return report  # 新增代码+Phase138PaintLiveDraw：返回合同报告；如果没有这一行，测试和 CLI 无法读取结果。
# 新增代码+Phase138PaintLiveDraw：函数段结束，run_phase138_controlled_paint_live_draw_contract 到此结束；如果没有这个边界说明，初学者不容易看出总合同范围。

def phase138_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase138PaintLiveDraw：函数段开始，把报告转成真实终端稳定 token 行；如果没有这段函数，验收器必须解析复杂 JSON。
    ok_token = f" {PHASE138_CONTROLLED_PAINT_LIVE_DRAW_OK_TOKEN}" if bool(report.get("passed")) else ""  # 新增代码+Phase138PaintLiveDraw：仅在合同通过时输出 OK token；如果没有这一行，失败报告会误带成功锚点。
    return f"{PHASE138_CONTROLLED_PAINT_LIVE_DRAW_MARKER}{ok_token} default_off_zero_physical_events={_phase138_bool_token(report.get('default_off_zero_physical_events'))} unsafe_target_zero_physical_events={_phase138_bool_token(report.get('unsafe_target_zero_physical_events'))} real_enable_gate_required={_phase138_bool_token(report.get('real_enable_gate_required'))} real_paint_draw_executed={_phase138_bool_token(report.get('real_paint_draw_executed'))} paint_process_verified={_phase138_bool_token(report.get('paint_process_verified'))} target_rechecked_before_input={_phase138_bool_token(report.get('target_rechecked_before_input'))} target_rechecked_before_result={_phase138_bool_token(report.get('target_rechecked_before_result'))} drawing_plan_executed={_phase138_bool_token(report.get('drawing_plan_executed'))} canvas_changed_after_real_actions={_phase138_bool_token(report.get('canvas_changed_after_real_actions'))} screenshot_before_after_different={_phase138_bool_token(report.get('screenshot_before_after_different'))} raw_text_hidden={_phase138_bool_token(report.get('raw_text_hidden'))} real_desktop_touched={_phase138_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase138_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase138PaintLiveDraw：返回固定顺序 token 行；如果没有这一行，真实可见终端场景匹配会漂移。
# 新增代码+Phase138PaintLiveDraw：函数段结束，phase138_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。

def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase138PaintLiveDraw：函数段开始，提供命令行入口；如果没有这段函数，真实终端无法直接运行 Phase138 合同。
    _ = argv  # 新增代码+Phase138PaintLiveDraw：保留 argv 扩展位；如果没有这一行，读者可能误以为命令参数被遗漏。
    report = run_phase138_controlled_paint_live_draw_contract()  # 新增代码+Phase138PaintLiveDraw：按环境双门运行合同；如果没有这一行，CLI 不会产生验收事实。
    print(phase138_cli_line(report))  # 新增代码+Phase138PaintLiveDraw：打印稳定 token 行；如果没有这一行，验收脚本无法快速匹配成功条件。
    print(json.dumps({"report_path": report.get("report_path"), "passed": report.get("passed"), "real_paint_draw_executed": report.get("real_paint_draw_executed")}, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase138PaintLiveDraw：打印短 JSON 方便定位报告；如果没有这一行，失败时不容易找到证据文件。
    print(PHASE138_CONTROLLED_PAINT_LIVE_DRAW_MARKER)  # 新增代码+Phase138PaintLiveDraw：单独打印 marker 方便人工观察；如果没有这一行，可见终端里阶段标识不够醒目。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase138PaintLiveDraw：按 passed 返回退出码；如果没有这一行，失败合同可能被自动化误判为成功。
# 新增代码+Phase138PaintLiveDraw：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。

__all__ = ["DEFAULT_PHASE138_CONTROLLED_PAINT_LIVE_DRAW_ROOT", "PHASE138_CONTROLLED_PAINT_LIVE_DRAW_MARKER", "PHASE138_CONTROLLED_PAINT_LIVE_DRAW_MODEL", "PHASE138_CONTROLLED_PAINT_LIVE_DRAW_OK_TOKEN", "PHASE138_REAL_PAINT_DRAW_ENV", "PHASE138_REAL_PAINT_DRAW_REQUEST_ENV", "PHASE138_UNCONTROLLED_ACTIONS_EXPANDED", "Phase138WindowsPaintLiveDrawDriver", "build_phase138_paint_real_desktop_closure_evidence", "main", "phase138_cli_line", "run_phase138_controlled_paint_live_draw_contract"]  # 新增代码+Phase138PaintLiveDraw：限定公开导出名称；如果没有这一行，from module import * 会暴露内部 helper。

if __name__ == "__main__":  # 新增代码+Phase138PaintLiveDraw：允许直接运行模块；如果没有这一行，python 文件方式不会启动合同。
    raise SystemExit(main())  # 新增代码+Phase138PaintLiveDraw：使用 main 返回码退出；如果没有这一行，命令行状态不明确。
# 新增代码+Phase138PaintLiveDraw：文件入口段结束，本模块到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
