"""Phase58 Windows real SendInput target guard."""  # 新增代码+Phase58RealSendInputGuard: 标明本文件负责受控真实 SendInput 动作路径；如果没有这行代码，读者不容易区分 Phase47 fake dispatcher 和 Phase58 真实守卫。
from __future__ import annotations  # 新增代码+Phase58RealSendInputGuard: 启用延迟类型解析；如果没有这行代码，旧运行路径遇到前向类型标注时更容易导入失败。

import hashlib  # 新增代码+Phase58RealSendInputGuard: 导入 hashlib 生成文本和窗口短哈希；如果没有这行代码，审计只能保存原文或完全不可追踪。
import json  # 新增代码+Phase58RealSendInputGuard: 导入 JSON 用于 CLI 报告和泄露检查；如果没有这行代码，真实终端验收无法输出结构化结果。
import sys  # 新增代码+Phase58RealSendInputGuard: 导入 sys 判断 Windows 平台；如果没有这行代码，非 Windows 环境可能误触发系统 API。
import time  # 新增代码+Phase58RealSendInputGuard: 导入 time 用于真实 smoke 等待窗口状态变化；如果没有这行代码，动作后观察可能太早。
from typing import Any  # 新增代码+Phase58RealSendInputGuard: 导入 Any 标注 JSON 风格参数；如果没有这行代码，runtime 输入输出边界不清楚。

try:  # 新增代码+Phase58RealSendInputGuard: 优先按包模式导入 Phase57/28 能力；如果没有这段代码，单测和生产入口无法复用已有安全窗口与 inventory。
    from learning_agent.computer_use.real_uia_locator import Phase57DedicatedSafeWindowLauncher, WindowsRealUiaLocatorRuntime, _phase57_find_safe_edit_control, _poll_phase57_safe_window  # 新增代码+Phase58RealSendInputGuard: 复用 Phase57 自建安全窗口、真实 UIA 和安全窗口轮询；如果没有这行代码，Phase58 会重复造窗口和定位逻辑。
    from learning_agent.computer_use.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase58RealSendInputGuard: 复用真实 Win32 只读窗口枚举；如果没有这行代码，真实 smoke 找不到自建窗口。
except ModuleNotFoundError as error:  # 新增代码+Phase58RealSendInputGuard: 兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这段代码，脚本模式可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.real_uia_locator", "learning_agent.computer_use.windows_backend"}:  # 新增代码+Phase58RealSendInputGuard: 只允许包路径缺失时 fallback；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase58RealSendInputGuard: 重新抛出非路径类导入错误；如果没有这行代码，排查 Phase57 或 inventory 内部错误会困难。
    from computer_use.real_uia_locator import Phase57DedicatedSafeWindowLauncher, WindowsRealUiaLocatorRuntime, _phase57_find_safe_edit_control, _poll_phase57_safe_window  # 新增代码+Phase58RealSendInputGuard: 脚本模式复用安全窗口和 UIA runtime；如果没有这行代码，bat 入口无法运行真实 smoke。
    from computer_use.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase58RealSendInputGuard: 脚本模式复用窗口枚举；如果没有这行代码，bat 入口无法定位自建窗口。

PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_MARKER = "PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_READY"  # 新增代码+Phase58RealSendInputGuard: 定义 Phase58 ready marker；如果没有这行代码，真实终端验收没有稳定等待锚点。
PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_OK_TOKEN = "PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_OK"  # 新增代码+Phase58RealSendInputGuard: 定义 Phase58 OK token；如果没有这行代码，debug log 无法区分自检通过和普通输出。
PHASE58_REAL_SENDINPUT_GUARD_MODEL = "phase58_windows_real_sendinput_guard"  # 新增代码+Phase58RealSendInputGuard: 定义 runtime 模型名；如果没有这行代码，状态和证据无法区分版本。
PHASE58_SUPPORTED_ACTIONS = ("move_mouse", "click", "type_text")  # 新增代码+Phase58RealSendInputGuard: 限定 Phase58 极窄真实动作集合；如果没有这行代码，模型可能传入未审计动作。
PHASE58_ACTIONS_EXPANDED = True  # 新增代码+Phase58RealSendInputGuard: 标记 Phase58 已在安全窗口内打开受控真实动作；如果没有这行代码，最终矩阵无法说明动作面状态。


def _phase58_bool_token(value: Any) -> str:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，把布尔值转成验收友好的小写 token；如果没有这段函数，CLI 输出可能混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+Phase58RealSendInputGuard: 返回 true/false 文本；如果没有这行代码，场景 token 匹配会不稳定。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，_phase58_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


def _phase58_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，安全转换坐标、hwnd 和计数；如果没有这段函数，坏模型参数会让动作路径崩溃。
    try:  # 新增代码+Phase58RealSendInputGuard: 捕获无法转换的动态输入；如果没有这行代码，None 或字符串坐标会直接抛异常。
        return int(value)  # 新增代码+Phase58RealSendInputGuard: 返回整数值；如果没有这行代码，SendInput 坐标和句柄无法使用。
    except Exception:  # 新增代码+Phase58RealSendInputGuard: 捕获所有转换异常作为安全兜底；如果没有这行代码，坏输入会中断 agent。
        return int(default)  # 新增代码+Phase58RealSendInputGuard: 返回默认值；如果没有这行代码，调用方需要重复兜底。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，_phase58_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出转换范围。


def _phase58_sha256_16(value: Any) -> str:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，生成短哈希用于文本和窗口摘要；如果没有这段函数，审计无法安全关联输入。
    text = str(value or "")  # 新增代码+Phase58RealSendInputGuard: 把输入规整成字符串；如果没有这行代码，None 或数字的哈希不稳定。
    if not text:  # 新增代码+Phase58RealSendInputGuard: 空值不生成哈希；如果没有这行代码，空输入也会看起来像有内容。
        return ""  # 新增代码+Phase58RealSendInputGuard: 返回空哈希；如果没有这行代码，调用方无法区分空输入。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase58RealSendInputGuard: 返回前 16 位 SHA256；如果没有这行代码，安全短指纹不可用。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，_phase58_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。


def _phase58_window_title(window: dict[str, Any]) -> str:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，读取窗口标题摘要；如果没有这段函数，安全判断会重复处理 title/title_preview。
    return str(window.get("title_preview", window.get("title", "")) or "")  # 新增代码+Phase58RealSendInputGuard: 返回优先 title_preview 的标题；如果没有这行代码，目标守卫可能拿不到窗口名。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，_phase58_window_title 到此结束；如果没有这个边界说明，初学者不容易看出标题读取范围。


def _phase58_hwnd(window: dict[str, Any]) -> int:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，从 hwnd 或 window_id 解析窗口句柄；如果没有这段函数，SetForegroundWindow 没有目标。
    if window.get("hwnd") is not None:  # 新增代码+Phase58RealSendInputGuard: 优先使用明确 hwnd 字段；如果没有这行代码，真实 inventory 的句柄可能被忽略。
        return _phase58_safe_int(window.get("hwnd"))  # 新增代码+Phase58RealSendInputGuard: 返回 hwnd 整数；如果没有这行代码，调用方拿不到系统句柄。
    text = str(window.get("window_id", "") or "")  # 新增代码+Phase58RealSendInputGuard: 读取 window_id 文本；如果没有这行代码，缺 hwnd 时无法从协议 id 兜底。
    return _phase58_safe_int(text.split(":", 1)[1]) if text.startswith("hwnd:") and ":" in text else 0  # 新增代码+Phase58RealSendInputGuard: 从 hwnd:123 解析句柄；如果没有这行代码，静态和真实窗口 id 无法用于系统 API。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，_phase58_hwnd 到此结束；如果没有这个边界说明，初学者不容易看出句柄解析范围。


def _phase58_identity(window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，构造目标窗口身份摘要；如果没有这段函数，动作前后无法证明是同一窗口。
    title = _phase58_window_title(window)  # 新增代码+Phase58RealSendInputGuard: 读取标题摘要；如果没有这行代码，身份缺少可读窗口线索。
    identity = {"window_id": str(window.get("window_id", "")), "hwnd": _phase58_hwnd(window), "app_id": str(window.get("app_id", "")), "pid": _phase58_safe_int(window.get("pid")), "title_sha256_16": _phase58_sha256_16(title), "title_length": len(title)}  # 新增代码+Phase58RealSendInputGuard: 返回不含完整标题的身份摘要；如果没有这行代码，审计要么泄露标题要么无法比对。
    return identity  # 新增代码+Phase58RealSendInputGuard: 返回身份字典；如果没有这行代码，目标守卫拿不到比较对象。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，_phase58_identity 到此结束；如果没有这个边界说明，初学者不容易看出身份摘要范围。


def _phase58_target_is_safe(window: dict[str, Any]) -> tuple[bool, str]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，判断目标是否为 Phase58 自有安全窗口；如果没有这段函数，终端或认证窗口可能被误操作。
    title = _phase58_window_title(window).lower()  # 新增代码+Phase58RealSendInputGuard: 标题转小写用于匹配；如果没有这行代码，大小写差异会绕过安全判断。
    app_id = str(window.get("app_id", "") or "").lower()  # 新增代码+Phase58RealSendInputGuard: 读取 app_id 辅助识别；如果没有这行代码，终端进程名无法参与拒绝。
    if "learningagent-phase58" in title:  # 新增代码+Phase58RealSendInputGuard: 只允许 Phase58 自建安全窗口；如果没有这行代码，真实动作会开放到普通用户窗口。
        return True, "target_is_phase58_safe_window"  # 新增代码+Phase58RealSendInputGuard: 返回允许原因；如果没有这行代码，审计无法解释为什么可以发送。
    forbidden = ("codex", "terminal", "powershell", "cmd.exe", "windows terminal", "password", "auth", "login", "captcha", "验证码", "密码", "security", "admin")  # 新增代码+Phase58RealSendInputGuard: 定义禁止目标关键词；如果没有这行代码，高风险窗口边界不生效。
    combined = f"{title} {app_id}"  # 新增代码+Phase58RealSendInputGuard: 合并标题和 app 便于统一检查；如果没有这行代码，判断逻辑会重复。
    if any(token in combined for token in forbidden):  # 新增代码+Phase58RealSendInputGuard: 检查是否命中禁止目标；如果没有这行代码，终端和认证窗口可能被点击。
        return False, "target_is_forbidden_sensitive_or_terminal"  # 新增代码+Phase58RealSendInputGuard: 返回禁止原因；如果没有这行代码，拒绝结果不可解释。
    return False, "phase58_allows_only_own_safe_window"  # 新增代码+Phase58RealSendInputGuard: 默认拒绝普通窗口；如果没有这行代码，目标面会过宽。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，_phase58_target_is_safe 到此结束；如果没有这个边界说明，初学者不容易看出安全判断范围。


def _phase58_observation_summary(raw_text: Any, *, source: str, control: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，把观察到的文本压成脱敏摘要；如果没有这段函数，type_text 前后证据可能泄露原文。
    text = str(raw_text or "")  # 新增代码+Phase58RealSendInputGuard: 把观察文本规整成字符串；如果没有这行代码，None 无法计算长度和哈希。
    safe_control = dict(control or {})  # 新增代码+Phase58RealSendInputGuard: 复制控件摘要；如果没有这行代码，调用方对象可能被污染。
    safe_control.pop("name", None)  # 新增代码+Phase58RealSendInputGuard: 删除可能包含输入文本的 name 字段；如果没有这行代码，UIA 控件名可能泄露输入原文。
    safe_control["name_included"] = False  # 新增代码+Phase58RealSendInputGuard: 明确声明不返回控件原始名称；如果没有这行代码，审计无法确认脱敏边界。
    return {"source": str(source), "text_length": len(text), "text_sha256_16": _phase58_sha256_16(text), "state_fingerprint": _phase58_sha256_16(f"{source}:{len(text)}:{_phase58_sha256_16(text)}"), "raw_text_included": False, "control": safe_control}  # 新增代码+Phase58RealSendInputGuard: 返回只含长度和哈希的观察摘要；如果没有这行代码，before/after 无法安全比较。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，_phase58_observation_summary 到此结束；如果没有这个边界说明，初学者不容易看出观察脱敏范围。


class Phase58RecordingLowLevelSender:  # 新增代码+Phase58RealSendInputGuard: 类段开始，定义单测和合同用低层 sender；如果没有这个类，测试只能触碰真实鼠标键盘。
    requires_raw_text = False  # 新增代码+Phase58RealSendInputGuard: 声明 fake sender 不需要原始文本；如果没有这行代码，runtime 可能把原文传给测试记录器。

    def __init__(self) -> None:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，初始化低层事件记录；如果没有这段函数，测试无法确认发送了多少事件。
        self.low_level_events: list[dict[str, Any]] = []  # 新增代码+Phase58RealSendInputGuard: 保存低层事件副本；如果没有这行代码，零事件门禁无法被验证。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，Phase58RecordingLowLevelSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，记录低层事件而不碰系统；如果没有这段函数，单测没有安全发送替身。
        self.low_level_events.extend(dict(event) for event in events)  # 新增代码+Phase58RealSendInputGuard: 复制事件到记录器；如果没有这行代码，测试无法检查事件类型和数量。
        return {"ok": True, "low_level_event_count": len(events), "sender": "phase58_recording", "raw_text_included": False}  # 新增代码+Phase58RealSendInputGuard: 返回成功摘要且不含原文；如果没有这行代码，runtime 无法形成发送结果。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，Phase58RecordingLowLevelSender.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出 fake 发送范围。
# 新增代码+Phase58RealSendInputGuard: 类段结束，Phase58RecordingLowLevelSender 到此结束；如果没有这个边界说明，初学者不容易看出 fake sender 范围。


class Phase58StaticSafeWindowObserver:  # 新增代码+Phase58RealSendInputGuard: 类段开始，定义测试用前后观察器；如果没有这个类，单测无法证明 before/after evidence 变化。
    def __init__(self, before_text: str = "phase58-before", after_text: str = "phase58-after") -> None:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，保存前后观察文本；如果没有这段函数，观察器没有可控状态。
        self.before_text = str(before_text)  # 新增代码+Phase58RealSendInputGuard: 保存动作前文本；如果没有这行代码，before 观察没有内容。
        self.after_text = str(after_text)  # 新增代码+Phase58RealSendInputGuard: 保存动作后文本；如果没有这行代码，after 观察无法模拟变化。
        self.calls = 0  # 新增代码+Phase58RealSendInputGuard: 记录观察次数；如果没有这行代码，无法决定返回 before 还是 after。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，Phase58StaticSafeWindowObserver.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def observe_window(self, window: dict[str, Any], locator_query: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，返回脱敏观察摘要；如果没有这段函数，runtime 无法采集测试 evidence。
        _ = window  # 新增代码+Phase58RealSendInputGuard: 明确静态观察器不依赖真实窗口；如果没有这行代码，读者可能误以为这里读取桌面。
        _ = locator_query  # 新增代码+Phase58RealSendInputGuard: 明确静态观察器不依赖 locator；如果没有这行代码，参数用途不清楚。
        self.calls += 1  # 新增代码+Phase58RealSendInputGuard: 增加观察次数；如果没有这行代码，前后状态不会切换。
        text = self.before_text if self.calls == 1 else self.after_text  # 新增代码+Phase58RealSendInputGuard: 第一次返回 before，之后返回 after；如果没有这行代码，动作后变化无法模拟。
        return _phase58_observation_summary(text, source="phase58_static_observer", control={"role": "Edit", "automation_id": "Phase58Editor"})  # 新增代码+Phase58RealSendInputGuard: 返回脱敏摘要；如果没有这行代码，before/after 证据可能包含原文。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，Phase58StaticSafeWindowObserver.observe_window 到此结束；如果没有这个边界说明，初学者不容易看出观察范围。
# 新增代码+Phase58RealSendInputGuard: 类段结束，Phase58StaticSafeWindowObserver 到此结束；如果没有这个边界说明，初学者不容易看出静态观察器范围。


class Phase58UiaSafeWindowObserver:  # 新增代码+Phase58RealSendInputGuard: 类段开始，定义真实 UIA 安全窗口观察器；如果没有这个类，真实 SendInput 后无法复验窗口状态。
    def __init__(self, uia_runtime: Any | None = None) -> None:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，保存可注入 UIA runtime；如果没有这段函数，测试和真实路径无法共享观察接口。
        self.uia_runtime = uia_runtime or WindowsRealUiaLocatorRuntime()  # 新增代码+Phase58RealSendInputGuard: 默认复用 Phase57 PowerShell/.NET UIA runtime；如果没有这行代码，真实观察没有后端。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，Phase58UiaSafeWindowObserver.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def observe_window(self, window: dict[str, Any], locator_query: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，读取安全窗口并只返回脱敏摘要；如果没有这段函数，after evidence 可能泄露输入文字。
        query = dict(locator_query or {"class_name": "EDIT"})  # 新增代码+Phase58RealSendInputGuard: 默认查找编辑控件；如果没有这行代码，真实 smoke 不知道哪个控件代表文本框。
        observed = self.uia_runtime.find_control(dict(window), query)  # 新增代码+Phase58RealSendInputGuard: 通过 Phase57 runtime 读取并定位控件；如果没有这行代码，真实复验没有 UIA 证据。
        locator = dict(observed.get("locator", {}) if isinstance(observed, dict) else {})  # 新增代码+Phase58RealSendInputGuard: 提取定位结果；如果没有这行代码，后续拿不到匹配控件。
        control = dict(locator.get("control", {}) if isinstance(locator.get("control", {}), dict) else {})  # 新增代码+Phase58RealSendInputGuard: 提取控件摘要；如果没有这行代码，观察摘要缺少 bounds 和 role。
        text_candidate = str(control.get("name", ""))  # 新增代码+Phase58RealSendInputGuard: 只在内存中读取控件 name 用于哈希；如果没有这行代码，无法判断文本是否变化。
        summary = _phase58_observation_summary(text_candidate, source="phase58_uia_observer", control=control)  # 新增代码+Phase58RealSendInputGuard: 生成不含原文的观察摘要；如果没有这行代码，UIA name 可能进入结果。
        summary["captured"] = bool(observed.get("captured"))  # 新增代码+Phase58RealSendInputGuard: 记录 UIA 是否采集成功；如果没有这行代码，复验无法区分空观察。
        summary["matched"] = bool(locator.get("matched"))  # 新增代码+Phase58RealSendInputGuard: 记录是否定位到控件；如果没有这行代码，真实 smoke 无法确认目标控件。
        summary["reason"] = str(locator.get("reason", observed.get("reason", "")))  # 新增代码+Phase58RealSendInputGuard: 保留不含原文的定位理由；如果没有这行代码，失败不易排查。
        return summary  # 新增代码+Phase58RealSendInputGuard: 返回安全观察摘要；如果没有这行代码，runtime 拿不到 before/after。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，Phase58UiaSafeWindowObserver.observe_window 到此结束；如果没有这个边界说明，初学者不容易看出 UIA 观察范围。
# 新增代码+Phase58RealSendInputGuard: 类段结束，Phase58UiaSafeWindowObserver 到此结束；如果没有这个边界说明，初学者不容易看出真实观察器范围。


class WindowsSendInputLowLevelSender:  # 新增代码+Phase58RealSendInputGuard: 类段开始，定义真实 Windows 低层发送器；如果没有这个类，Phase58 只能停留在 fake sender 合同。
    requires_raw_text = True  # 新增代码+Phase58RealSendInputGuard: 声明真实 sender 需要在内存中接收原文才能发 Unicode；如果没有这行代码，runtime 会只传哈希导致无法真实输入。

    def __init__(self, platform: str | None = None) -> None:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，保存平台；如果没有这段函数，非 Windows 拒绝路径不可测试。
        self.platform = platform or sys.platform  # 新增代码+Phase58RealSendInputGuard: 保存平台名；如果没有这行代码，sender 不知道当前系统是否支持 Win32 API。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsSendInputLowLevelSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，发送低层输入事件；如果没有这段函数，真实动作不会触达系统。
        if self.platform != "win32":  # 新增代码+Phase58RealSendInputGuard: 非 Windows 直接拒绝；如果没有这行代码，跨平台调用 ctypes.windll 会崩溃。
            return {"ok": False, "decision": "platform_not_windows", "low_level_event_count": 0, "raw_text_included": False}  # 新增代码+Phase58RealSendInputGuard: 返回零事件失败；如果没有这行代码，调用方无法确认未触碰系统。
        sent_count = 0  # 新增代码+Phase58RealSendInputGuard: 初始化已处理事件计数；如果没有这行代码，结果无法说明动作规模。
        event_types: list[str] = []  # 新增代码+Phase58RealSendInputGuard: 保存事件类型摘要；如果没有这行代码，审计看不到发送了哪些动作族。
        for event in list(events or []):  # 新增代码+Phase58RealSendInputGuard: 遍历低层事件；如果没有这行代码，sender 不会处理任何输入。
            event_type = str(event.get("type", ""))  # 新增代码+Phase58RealSendInputGuard: 读取事件类型；如果没有这行代码，分支无法判断动作。
            event_types.append(event_type)  # 新增代码+Phase58RealSendInputGuard: 记录事件类型；如果没有这行代码，结果缺少摘要。
            if event_type == "set_foreground":  # 新增代码+Phase58RealSendInputGuard: 处理前台窗口切换；如果没有这行代码，文本可能发不到安全窗口。
                sent_count += 1 if self._set_foreground(_phase58_safe_int(event.get("hwnd"))) else 0  # 新增代码+Phase58RealSendInputGuard: 将自建窗口置前；如果没有这行代码，安全窗口可能没有焦点。
            elif event_type == "mouse_move":  # 新增代码+Phase58RealSendInputGuard: 处理鼠标移动；如果没有这行代码，点击无法落到控件中心。
                sent_count += 1 if self._set_cursor(_phase58_safe_int(event.get("x")), _phase58_safe_int(event.get("y"))) else 0  # 新增代码+Phase58RealSendInputGuard: 移动鼠标到指定坐标；如果没有这行代码，后续点击位置不可控。
            elif event_type == "mouse_down":  # 新增代码+Phase58RealSendInputGuard: 处理鼠标按下；如果没有这行代码，click 动作不完整。
                sent_count += 1 if self._send_mouse_button(str(event.get("button", "left")), down=True) else 0  # 新增代码+Phase58RealSendInputGuard: 发送鼠标按下；如果没有这行代码，控件不会收到点击。
            elif event_type == "mouse_up":  # 新增代码+Phase58RealSendInputGuard: 处理鼠标抬起；如果没有这行代码，click 动作不完整。
                sent_count += 1 if self._send_mouse_button(str(event.get("button", "left")), down=False) else 0  # 新增代码+Phase58RealSendInputGuard: 发送鼠标抬起；如果没有这行代码，点击不会完成。
            elif event_type == "unicode_text":  # 新增代码+Phase58RealSendInputGuard: 处理 Unicode 文本输入；如果没有这行代码，type_text 无法真实写入。
                sent_count += self._send_unicode_text(str(event.get("text", "")))  # 新增代码+Phase58RealSendInputGuard: 逐字符发送 Unicode；如果没有这行代码，文本输入只有哈希没有真实效果。
        return {"ok": sent_count > 0, "low_level_event_count": sent_count, "low_level_event_types": event_types, "sender": "windows_sendinput_low_level", "raw_text_included": False}  # 新增代码+Phase58RealSendInputGuard: 返回不含原文的发送摘要；如果没有这行代码，runtime 无法审计发送结果。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsSendInputLowLevelSender.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出真实发送范围。

    def _set_foreground(self, hwnd: int) -> bool:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，把自建窗口置为前台；如果没有这段函数，文本可能打到旧焦点窗口。
        if hwnd <= 0:  # 新增代码+Phase58RealSendInputGuard: 检查 hwnd 是否有效；如果没有这行代码，0 句柄可能发给系统 API。
            return False  # 新增代码+Phase58RealSendInputGuard: 无效句柄直接失败；如果没有这行代码，调用方无法知道未聚焦。
        import ctypes  # 新增代码+Phase58RealSendInputGuard: 延迟导入 ctypes；如果没有这行代码，无法调用 user32.dll。
        return bool(ctypes.windll.user32.SetForegroundWindow(hwnd))  # 新增代码+Phase58RealSendInputGuard: 调用 Win32 前台窗口 API；如果没有这行代码，安全窗口不一定接收输入。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsSendInputLowLevelSender._set_foreground 到此结束；如果没有这个边界说明，初学者不容易看出聚焦范围。

    def _set_cursor(self, x: int, y: int) -> bool:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，把鼠标移动到目标点；如果没有这段函数，点击无法命中安全控件。
        import ctypes  # 新增代码+Phase58RealSendInputGuard: 延迟导入 ctypes；如果没有这行代码，无法调用 user32.dll。
        return bool(ctypes.windll.user32.SetCursorPos(int(x), int(y)))  # 新增代码+Phase58RealSendInputGuard: 调用系统光标移动；如果没有这行代码，按钮事件会在旧位置发生。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsSendInputLowLevelSender._set_cursor 到此结束；如果没有这个边界说明，初学者不容易看出移动范围。

    def _send_mouse_button(self, button: str, down: bool) -> bool:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，用 SendInput 发送鼠标按键；如果没有这段函数，click 无法走 SendInput 路径。
        import ctypes  # 新增代码+Phase58RealSendInputGuard: 延迟导入 ctypes；如果没有这行代码，无法构造 INPUT 结构。
        flag = 0x0002 if button.lower() == "left" and down else 0x0004 if button.lower() == "left" else 0x0008 if down else 0x0010  # 新增代码+Phase58RealSendInputGuard: 选择左/右键按下抬起 flag；如果没有这行代码，SendInput 不知道执行哪个按钮动作。
        extra_type = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong  # 新增代码+Phase58RealSendInputGuard: 选择 ULONG_PTR 宽度；如果没有这行代码，64 位 Windows 结构大小可能错误。
        class MOUSEINPUT(ctypes.Structure):  # 新增代码+Phase58RealSendInputGuard: 定义 SendInput 鼠标结构；如果没有这个类，无法调用 SendInput。
            _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", extra_type)]  # 新增代码+Phase58RealSendInputGuard: 定义鼠标字段；如果没有这行代码，结构和 Win32 API 不匹配。
        class INPUTUNION(ctypes.Union):  # 新增代码+Phase58RealSendInputGuard: 定义 INPUT union；如果没有这个类，SendInput 结构缺少 mi 分支。
            _fields_ = [("mi", MOUSEINPUT)]  # 新增代码+Phase58RealSendInputGuard: 只声明鼠标分支；如果没有这行代码，按钮事件无法放入 INPUT。
        class INPUT(ctypes.Structure):  # 新增代码+Phase58RealSendInputGuard: 定义 INPUT 结构；如果没有这个类，SendInput 参数无法构造。
            _fields_ = [("type", ctypes.c_ulong), ("union", INPUTUNION)]  # 新增代码+Phase58RealSendInputGuard: type=0 表示鼠标输入；如果没有这行代码，系统无法识别事件类型。
        input_item = INPUT(0, INPUTUNION(mi=MOUSEINPUT(0, 0, 0, flag, 0, extra_type(0))))  # 新增代码+Phase58RealSendInputGuard: 构造单个鼠标 INPUT；如果没有这行代码，SendInput 没有事件可发。
        sent = ctypes.windll.user32.SendInput(1, ctypes.byref(input_item), ctypes.sizeof(INPUT))  # 新增代码+Phase58RealSendInputGuard: 调用 SendInput 发送按钮事件；如果没有这行代码，click 不会发生。
        return sent == 1  # 新增代码+Phase58RealSendInputGuard: 返回是否成功发送一个事件；如果没有这行代码，调用方无法判断失败。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsSendInputLowLevelSender._send_mouse_button 到此结束；如果没有这个边界说明，初学者不容易看出鼠标 SendInput 范围。

    def _send_unicode_text(self, text: str) -> int:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，用 SendInput Unicode 键盘事件输入文本；如果没有这段函数，type_text 没有真实写入能力。
        import ctypes  # 新增代码+Phase58RealSendInputGuard: 延迟导入 ctypes；如果没有这行代码，无法构造 KEYBDINPUT。
        extra_type = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong  # 新增代码+Phase58RealSendInputGuard: 选择 ULONG_PTR 宽度；如果没有这行代码，键盘结构大小可能错误。
        class MOUSEINPUT(ctypes.Structure):  # 修改代码+Phase58RealSendInputGuard: 在键盘发送路径也声明鼠标分支以撑满 Win32 INPUT union 尺寸；如果没有这行代码，64 位 Windows 会因为 cbSize 偏小拒收 Unicode 键盘事件。
            _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", extra_type)]  # 修改代码+Phase58RealSendInputGuard: 复用系统鼠标结构作为 union 最大分支；如果没有这行代码，SendInput 键盘结构大小可能小于系统要求。
        class KEYBDINPUT(ctypes.Structure):  # 新增代码+Phase58RealSendInputGuard: 定义键盘输入结构；如果没有这个类，无法发送 Unicode 字符。
            _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", extra_type)]  # 新增代码+Phase58RealSendInputGuard: 定义键盘字段；如果没有这行代码，SendInput 结构不匹配。
        class INPUTUNION(ctypes.Union):  # 新增代码+Phase58RealSendInputGuard: 定义 INPUT union；如果没有这个类，键盘事件无法装入 INPUT。
            _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]  # 修改代码+Phase58RealSendInputGuard: 同时声明鼠标和键盘分支来匹配 Win32 INPUT union 的真实大小；如果没有这行代码，Unicode 文本可能显示发送成功路径但实际 0 个键盘事件被接收。
        class INPUT(ctypes.Structure):  # 新增代码+Phase58RealSendInputGuard: 定义 INPUT 结构；如果没有这个类，SendInput 参数无法构造。
            _fields_ = [("type", ctypes.c_ulong), ("union", INPUTUNION)]  # 新增代码+Phase58RealSendInputGuard: type=1 表示键盘输入；如果没有这行代码，系统无法识别事件类型。
        sent_count = 0  # 新增代码+Phase58RealSendInputGuard: 初始化成功事件计数；如果没有这行代码，返回值无法说明输入规模。
        for char in text:  # 新增代码+Phase58RealSendInputGuard: 遍历每个 Unicode 字符；如果没有这行代码，文本不会被拆成键盘事件。
            code = ord(char)  # 新增代码+Phase58RealSendInputGuard: 读取字符码点；如果没有这行代码，KEYBDINPUT 没有 scan code。
            for flags in (0x0004, 0x0004 | 0x0002):  # 新增代码+Phase58RealSendInputGuard: 发送 Unicode 按下和抬起；如果没有这行代码，应用可能只看到半个按键。
                input_item = INPUT(1, INPUTUNION(ki=KEYBDINPUT(0, code, flags, 0, extra_type(0))))  # 新增代码+Phase58RealSendInputGuard: 构造键盘 INPUT；如果没有这行代码，SendInput 没有键盘事件可发。
                sent = ctypes.windll.user32.SendInput(1, ctypes.byref(input_item), ctypes.sizeof(INPUT))  # 新增代码+Phase58RealSendInputGuard: 调用 SendInput 发送字符事件；如果没有这行代码，文本不会输入。
                sent_count += 1 if sent == 1 else 0  # 新增代码+Phase58RealSendInputGuard: 统计成功事件；如果没有这行代码，结果无法判断发送是否发生。
        return sent_count  # 新增代码+Phase58RealSendInputGuard: 返回成功发送的键盘事件数量；如果没有这行代码，runtime 无法审计文本输入。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsSendInputLowLevelSender._send_unicode_text 到此结束；如果没有这个边界说明，初学者不容易看出 Unicode SendInput 范围。
# 新增代码+Phase58RealSendInputGuard: 类段结束，WindowsSendInputLowLevelSender 到此结束；如果没有这个边界说明，初学者不容易看出真实 sender 范围。


class WindowsRealSendInputGuardRuntime:  # 新增代码+Phase58RealSendInputGuard: 类段开始，组合目标守卫、低层 sender 和前后观察；如果没有这个类，真实动作路径会散落在 CLI 里。
    def __init__(self, platform: str | None = None, inventory: Any | None = None, low_level_sender: Any | None = None, observer: Any | None = None, after_observe_delay_seconds: float = 0.2) -> None:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，初始化 runtime 依赖；如果没有这段函数，测试和真实 smoke 无法注入安全替身。
        self.platform = platform or sys.platform  # 新增代码+Phase58RealSendInputGuard: 保存平台；如果没有这行代码，平台拒绝路径无法测试。
        self.inventory = inventory or WindowsWindowInventoryProbe()  # 新增代码+Phase58RealSendInputGuard: 保存窗口 inventory；如果没有这行代码，目标复验无法读取当前窗口。
        self.low_level_sender = low_level_sender or WindowsSendInputLowLevelSender(platform=self.platform)  # 新增代码+Phase58RealSendInputGuard: 保存低层 sender；如果没有这行代码，真实动作没有发送层。
        self.observer = observer or Phase58UiaSafeWindowObserver()  # 新增代码+Phase58RealSendInputGuard: 保存前后观察器；如果没有这行代码，动作后无法验收状态变化。
        self.after_observe_delay_seconds = float(after_observe_delay_seconds)  # 新增代码+Phase58RealSendInputGuard: 保存动作后等待时间；如果没有这行代码，UIA 可能在窗口更新前读取。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsRealSendInputGuardRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，返回 runtime 状态；如果没有这段函数，状态 UI 和矩阵无法读取 Phase58 能力。
        return {"marker": PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_MARKER, "model": PHASE58_REAL_SENDINPUT_GUARD_MODEL, "platform": self.platform, "platform_supported": self.platform == "win32", "supported_actions": list(PHASE58_SUPPORTED_ACTIONS), "safe_window_only": True, "actions_expanded": PHASE58_ACTIONS_EXPANDED, "sender": type(self.low_level_sender).__name__, "observer": type(self.observer).__name__}  # 新增代码+Phase58RealSendInputGuard: 返回机器可读状态；如果没有这行代码，外部 agent 不知道本阶段边界。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsRealSendInputGuardRuntime.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def execute_safe_action(self, window: dict[str, Any], action: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，执行一次受目标守卫保护的动作；如果没有这段函数，Phase58 没有统一入口。
        action_name = str(action or "").strip()  # 新增代码+Phase58RealSendInputGuard: 清理动作名；如果没有这行代码，空白动作会进入分支。
        args = dict(arguments or {})  # 新增代码+Phase58RealSendInputGuard: 复制参数避免污染调用方对象；如果没有这行代码，脱敏或补字段可能改到外部状态。
        guard = self._verify_target(dict(window or {}))  # 新增代码+Phase58RealSendInputGuard: 在任何发送前复验目标；如果没有这行代码，低层事件可能打到漂移窗口。
        if action_name not in PHASE58_SUPPORTED_ACTIONS:  # 新增代码+Phase58RealSendInputGuard: 拒绝未审计动作；如果没有这行代码，未知动作可能进入低层 sender。
            return self._failure(action_name, "unsupported_phase58_action", "Phase58 只允许 move_mouse/click/type_text。", guard)  # 新增代码+Phase58RealSendInputGuard: 返回零事件拒绝；如果没有这行代码，调用方不知道动作为何被拒绝。
        if self.platform != "win32":  # 新增代码+Phase58RealSendInputGuard: 非 Windows 直接拒绝；如果没有这行代码，跨平台会调用 Win32 API。
            return self._failure(action_name, "platform_not_windows", "当前平台不是 Windows，未发送低层事件。", guard)  # 新增代码+Phase58RealSendInputGuard: 返回平台拒绝；如果没有这行代码，失败原因不清楚。
        if not guard.get("ok"):  # 新增代码+Phase58RealSendInputGuard: 目标守卫失败时直接返回；如果没有这行代码，拒绝目标仍可能发送事件。
            return self._failure(action_name, str(guard.get("decision", "target_guard_failed")), "目标守卫失败，已发送 0 个低层事件。", guard)  # 新增代码+Phase58RealSendInputGuard: 返回零事件目标拒绝；如果没有这行代码，门禁失败不透明。
        before = self._observe("before", guard["window"], args)  # 新增代码+Phase58RealSendInputGuard: 动作前观察安全窗口；如果没有这行代码，证据链缺少 before。
        events = self._build_low_level_events(action_name, args, guard["window"])  # 新增代码+Phase58RealSendInputGuard: 构造低层事件；如果没有这行代码，sender 没有可发送内容。
        if not events:  # 新增代码+Phase58RealSendInputGuard: 检查是否没有低层事件；如果没有这行代码，空动作可能误报成功。
            return self._failure(action_name, "no_low_level_events", "没有可发送事件，已发送 0 个低层事件。", guard, before=before)  # 新增代码+Phase58RealSendInputGuard: 返回零事件拒绝；如果没有这行代码，用户不知道参数缺失。
        dispatch = self.low_level_sender.send_low_level(events)  # 新增代码+Phase58RealSendInputGuard: 调用低层 sender；如果没有这行代码，动作不会发生。
        time.sleep(max(0.0, self.after_observe_delay_seconds))  # 新增代码+Phase58RealSendInputGuard: 等待 UI 状态更新；如果没有这行代码，after 观察可能读到旧状态。
        after = self._observe("after", guard["window"], args)  # 新增代码+Phase58RealSendInputGuard: 动作后重新观察安全窗口；如果没有这行代码，无法证明动作效果。
        low_level_event_count = int(dispatch.get("low_level_event_count", len(events)) if isinstance(dispatch, dict) else len(events))  # 新增代码+Phase58RealSendInputGuard: 读取发送计数；如果没有这行代码，结果无法说明低层副作用规模。
        after_state_changed = before.get("state_fingerprint") != after.get("state_fingerprint")  # 新增代码+Phase58RealSendInputGuard: 比较前后状态指纹；如果没有这行代码，验收无法确认窗口状态变化。
        result = {"ok": bool(dispatch.get("ok", False)) if isinstance(dispatch, dict) else False, "marker": PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_MARKER, "model": PHASE58_REAL_SENDINPUT_GUARD_MODEL, "action": action_name, "target_guard_passed": True, "target_guard": self._redact_guard(guard), "safe_window_only": True, "low_level_event_count": low_level_event_count, "low_level_events_sent": low_level_event_count > 0, "before": before, "after": after, "before_after_observed": bool(before.get("observed") and after.get("observed")), "after_state_changed": after_state_changed, "dispatch": self._redact_dispatch(dispatch), "raw_text_hidden": True, "actions_expanded": PHASE58_ACTIONS_EXPANDED}  # 新增代码+Phase58RealSendInputGuard: 构造不含原文的执行结果；如果没有这行代码，CLI 和 verifier 无法读取统一事实。
        if action_name == "type_text":  # 新增代码+Phase58RealSendInputGuard: 文本动作补充脱敏摘要；如果没有这行代码，审计不知道输入规模。
            result.update({"text_length": len(str(args.get("text", "") or "")), "text_sha256_16": _phase58_sha256_16(args.get("text", "")), "text_redacted": True})  # 新增代码+Phase58RealSendInputGuard: 只保存长度和哈希；如果没有这行代码，文本审计要么泄露原文要么不可追踪。
        return result  # 新增代码+Phase58RealSendInputGuard: 返回执行摘要；如果没有这行代码，调用方拿不到结果。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsRealSendInputGuardRuntime.execute_safe_action 到此结束；如果没有这个边界说明，初学者不容易看出动作流程范围。

    def _verify_target(self, requested_window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，复验当前窗口仍是同一个安全目标；如果没有这段函数，旧窗口引用可能打到错误窗口。
        safe, safe_reason = _phase58_target_is_safe(requested_window)  # 新增代码+Phase58RealSendInputGuard: 检查请求窗口标题是否安全；如果没有这行代码，普通窗口可能进入发送链。
        if not safe:  # 新增代码+Phase58RealSendInputGuard: 请求窗口本身不安全时拒绝；如果没有这行代码，终端窗口可能被后续快照误放行。
            return {"ok": False, "decision": safe_reason, "low_level_event_count": 0, "requested_identity": _phase58_identity(requested_window)}  # 新增代码+Phase58RealSendInputGuard: 返回零事件拒绝摘要；如果没有这行代码，调用方无法审计拒绝目标。
        snapshot = self.inventory.snapshot()  # 新增代码+Phase58RealSendInputGuard: 读取当前窗口快照；如果没有这行代码，目标漂移无法发现。
        actual = snapshot.find_window(requested_window) if hasattr(snapshot, "find_window") else None  # 新增代码+Phase58RealSendInputGuard: 按 app_id/window_id 查找当前窗口；如果没有这行代码，无法验证窗口仍存在。
        if actual is None:  # 新增代码+Phase58RealSendInputGuard: 当前快照找不到目标时拒绝；如果没有这行代码，关闭的窗口仍可能收到旧坐标动作。
            return {"ok": False, "decision": "target_not_found_in_current_inventory", "low_level_event_count": 0, "requested_identity": _phase58_identity(requested_window)}  # 新增代码+Phase58RealSendInputGuard: 返回找不到目标；如果没有这行代码，失败不可解释。
        requested_identity = _phase58_identity(requested_window)  # 新增代码+Phase58RealSendInputGuard: 构造请求身份；如果没有这行代码，无法比较标题哈希。
        actual_identity = _phase58_identity(actual)  # 新增代码+Phase58RealSendInputGuard: 构造当前身份；如果没有这行代码，无法检查窗口是否漂移。
        if requested_identity.get("title_sha256_16") != actual_identity.get("title_sha256_16"):  # 新增代码+Phase58RealSendInputGuard: 检查标题是否仍一致；如果没有这行代码，同 hwnd/title 变化可能被误放行。
            return {"ok": False, "decision": "target_title_changed_before_send", "low_level_event_count": 0, "requested_identity": requested_identity, "actual_identity": actual_identity}  # 新增代码+Phase58RealSendInputGuard: 返回标题漂移拒绝；如果没有这行代码，动作可能打到被复用窗口。
        return {"ok": True, "decision": "target_guard_passed", "window": dict(actual), "requested_identity": requested_identity, "actual_identity": actual_identity, "safe_reason": safe_reason}  # 新增代码+Phase58RealSendInputGuard: 返回通过结果和当前窗口；如果没有这行代码，执行流程拿不到可信窗口。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsRealSendInputGuardRuntime._verify_target 到此结束；如果没有这个边界说明，初学者不容易看出目标复验范围。

    def _observe(self, phase: str, window: dict[str, Any], arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，执行 before/after 观察；如果没有这段函数，证据字段会重复且不一致。
        locator_query = dict(arguments.get("locator", {"class_name": "EDIT"}) if isinstance(arguments.get("locator", {"class_name": "EDIT"}), dict) else {"class_name": "EDIT"})  # 新增代码+Phase58RealSendInputGuard: 读取或默认编辑控件定位条件；如果没有这行代码，真实复验可能定位不到文本框。
        observed = self.observer.observe_window(dict(window), locator_query=locator_query) if hasattr(self.observer, "observe_window") else _phase58_observation_summary("", source="missing_observer")  # 新增代码+Phase58RealSendInputGuard: 调用观察器并兜底；如果没有这行代码，before/after 会因观察器缺失崩溃。
        result = dict(observed if isinstance(observed, dict) else {})  # 新增代码+Phase58RealSendInputGuard: 复制观察结果；如果没有这行代码，追加 phase 可能污染 observer 返回对象。
        result["phase"] = str(phase)  # 新增代码+Phase58RealSendInputGuard: 标记 before 或 after；如果没有这行代码，审计链不知道观察时机。
        result["observed"] = True  # 新增代码+Phase58RealSendInputGuard: 标记观察已执行；如果没有这行代码，before_after token 无法判断。
        result["raw_text_included"] = False  # 新增代码+Phase58RealSendInputGuard: 强制声明不含原文；如果没有这行代码，安全边界不明显。
        return result  # 新增代码+Phase58RealSendInputGuard: 返回观察摘要；如果没有这行代码，动作结果缺少 evidence。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsRealSendInputGuardRuntime._observe 到此结束；如果没有这个边界说明，初学者不容易看出观察包装范围。

    def _build_low_level_events(self, action: str, arguments: dict[str, Any], window: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，构造低层事件且控制文本原文是否传给真实 sender；如果没有这段函数，动作展开会散落在 execute 中。
        events: list[dict[str, Any]] = []  # 新增代码+Phase58RealSendInputGuard: 初始化事件列表；如果没有这行代码，后续无法追加事件。
        include_raw_text = bool(getattr(self.low_level_sender, "requires_raw_text", False))  # 新增代码+Phase58RealSendInputGuard: 只有真实 sender 才接收内存原文；如果没有这行代码，测试记录器可能保存文本原文。
        if include_raw_text and _phase58_hwnd(window) > 0:  # 新增代码+Phase58RealSendInputGuard: 真实 sender 有 hwnd 时先聚焦安全窗口；如果没有这行代码，输入可能发到旧焦点。
            events.append({"type": "set_foreground", "hwnd": _phase58_hwnd(window)})  # 新增代码+Phase58RealSendInputGuard: 加入前台窗口事件；如果没有这行代码，安全窗体不一定接收键盘。
        if action in {"move_mouse", "click", "type_text"} and "x" in arguments and "y" in arguments:  # 新增代码+Phase58RealSendInputGuard: 有坐标时先移动鼠标；如果没有这行代码，点击或聚焦无法命中目标。
            events.append({"type": "mouse_move", "x": _phase58_safe_int(arguments.get("x")), "y": _phase58_safe_int(arguments.get("y"))})  # 新增代码+Phase58RealSendInputGuard: 记录移动事件；如果没有这行代码，sender 不知道目标坐标。
        if action == "click":  # 新增代码+Phase58RealSendInputGuard: 处理点击动作；如果没有这行代码，click 不会生成按键事件。
            events.extend([{"type": "mouse_down", "button": str(arguments.get("button", "left"))}, {"type": "mouse_up", "button": str(arguments.get("button", "left"))}])  # 新增代码+Phase58RealSendInputGuard: 添加按下和抬起；如果没有这行代码，点击动作不完整。
        if action == "type_text" and "x" in arguments and "y" in arguments:  # 新增代码+Phase58RealSendInputGuard: 文本动作有坐标时先点击输入框聚焦；如果没有这行代码，文本可能进不到安全控件。
            events.extend([{"type": "mouse_down", "button": "left"}, {"type": "mouse_up", "button": "left"}])  # 新增代码+Phase58RealSendInputGuard: 添加一次安全控件点击；如果没有这行代码，文本框可能没有焦点。
        if action == "type_text":  # 新增代码+Phase58RealSendInputGuard: 处理文本输入事件；如果没有这行代码，type_text 不会生成键盘事件。
            text = str(arguments.get("text", "") or "")  # 新增代码+Phase58RealSendInputGuard: 读取原始文本但只保存在局部内存；如果没有这行代码，真实 sender 无法输入。
            text_event = {"type": "unicode_text", "text_length": len(text), "text_sha256_16": _phase58_sha256_16(text), "text_redacted": True}  # 新增代码+Phase58RealSendInputGuard: 默认构造脱敏文本事件；如果没有这行代码，fake sender 会缺少文本规模。
            if include_raw_text:  # 新增代码+Phase58RealSendInputGuard: 只有真实 sender 才需要原文；如果没有这行代码，测试事件会泄露原文。
                text_event["text"] = text  # 新增代码+Phase58RealSendInputGuard: 在内存事件中交给真实 sender；如果没有这行代码，SendInput 无法逐字符输入。
            events.append(text_event)  # 新增代码+Phase58RealSendInputGuard: 添加文本事件；如果没有这行代码，type_text 没有低层动作。
        return events  # 新增代码+Phase58RealSendInputGuard: 返回低层事件列表；如果没有这行代码，sender 无法执行。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsRealSendInputGuardRuntime._build_low_level_events 到此结束；如果没有这个边界说明，初学者不容易看出事件构造范围。

    def _redact_guard(self, guard: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，裁剪目标守卫结果；如果没有这段函数，完整窗口标题可能进入输出。
        return {"ok": bool(guard.get("ok")), "decision": str(guard.get("decision", "")), "requested_identity": dict(guard.get("requested_identity", {})), "actual_identity": dict(guard.get("actual_identity", {})), "safe_reason": str(guard.get("safe_reason", ""))}  # 新增代码+Phase58RealSendInputGuard: 返回不含完整标题的守卫摘要；如果没有这行代码，审计可能泄露窗口标题。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsRealSendInputGuardRuntime._redact_guard 到此结束；如果没有这个边界说明，初学者不容易看出守卫脱敏范围。

    def _redact_dispatch(self, dispatch: Any) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，裁剪低层 sender 返回；如果没有这段函数，真实 sender 未来可能把原文带回。
        data = dict(dispatch) if isinstance(dispatch, dict) else {"ok": bool(dispatch)}  # 新增代码+Phase58RealSendInputGuard: 规整 sender 返回；如果没有这行代码，非 dict 返回会污染结果。
        data.pop("text", None)  # 新增代码+Phase58RealSendInputGuard: 删除可能存在的文本字段；如果没有这行代码，底层实现变化可能泄露原文。
        data.pop("raw_text", None)  # 新增代码+Phase58RealSendInputGuard: 删除兼容 raw_text 字段；如果没有这行代码，换名字段仍可能外泄。
        data["raw_text_included"] = False  # 新增代码+Phase58RealSendInputGuard: 明确低层结果不含原文；如果没有这行代码，验收无法稳定判断。
        return data  # 新增代码+Phase58RealSendInputGuard: 返回脱敏 dispatch；如果没有这行代码，execute 结果缺少发送摘要。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsRealSendInputGuardRuntime._redact_dispatch 到此结束；如果没有这个边界说明，初学者不容易看出发送结果脱敏范围。

    def _failure(self, action: str, decision: str, message: str, guard: dict[str, Any], before: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，构造统一零事件失败结果；如果没有这段函数，门禁失败字段会漂移。
        return {"ok": False, "marker": PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_MARKER, "model": PHASE58_REAL_SENDINPUT_GUARD_MODEL, "action": str(action), "decision": str(decision), "message": str(message), "target_guard_passed": False, "target_guard": self._redact_guard(guard), "safe_window_only": True, "low_level_event_count": 0, "low_level_events_sent": False, "forbidden_zero_events": True, "before": dict(before or {}), "after": {}, "before_after_observed": False, "after_state_changed": False, "raw_text_hidden": True, "actions_expanded": PHASE58_ACTIONS_EXPANDED}  # 新增代码+Phase58RealSendInputGuard: 返回统一失败摘要；如果没有这行代码，verifier 无法确认拒绝时 0 事件。
    # 新增代码+Phase58RealSendInputGuard: 函数段结束，WindowsRealSendInputGuardRuntime._failure 到此结束；如果没有这个边界说明，初学者不容易看出失败结构范围。
# 新增代码+Phase58RealSendInputGuard: 类段结束，WindowsRealSendInputGuardRuntime 到此结束；如果没有这个边界说明，初学者不容易看出 runtime 范围。


def _phase58_contract_window() -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，构造合同自检安全窗口；如果没有这段函数，单测和 CLI 合同会依赖真实桌面。
    return {"app_id": "phase58_safe_app", "window_id": "hwnd:5801", "hwnd": 5801, "pid": 580, "title_preview": "LearningAgent-Phase58-RealSendInputGuardSmoke", "rect": {"left": 100, "top": 120, "right": 740, "bottom": 520}, "safe_to_target": True}  # 新增代码+Phase58RealSendInputGuard: 返回自有安全窗口样本；如果没有这行代码，合同没有可信目标。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，_phase58_contract_window 到此结束；如果没有这个边界说明，初学者不容易看出合同窗口范围。


def run_phase58_real_sendinput_guard_smoke(platform: str | None = None, timeout_seconds: float = 8.0) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，运行真实安全窗口 SendInput smoke；如果没有这段函数，Phase58 无法证明真实动作路径。
    current_platform = platform or sys.platform  # 新增代码+Phase58RealSendInputGuard: 确定平台；如果没有这行代码，测试无法注入平台。
    if current_platform != "win32":  # 新增代码+Phase58RealSendInputGuard: 非 Windows 诚实返回未运行；如果没有这行代码，跨平台会误触 Win32 API。
        return {"real_smoke": False, "platform_supported": False, "safe_window_only": True, "reason": "当前平台不是 Windows，未运行真实 SendInput smoke。", "actions_expanded": PHASE58_ACTIONS_EXPANDED}  # 新增代码+Phase58RealSendInputGuard: 返回平台不支持；如果没有这行代码，失败原因不清楚。
    launcher = Phase57DedicatedSafeWindowLauncher(marker_text="LearningAgent Phase58 real SendInput guard smoke", title_prefix="LearningAgent-Phase58-RealSendInputGuardSmoke")  # 新增代码+Phase58RealSendInputGuard: 创建 Phase58 自有安全窗口；如果没有这行代码，真实动作没有隔离目标。
    target = launcher.launch()  # 新增代码+Phase58RealSendInputGuard: 启动安全窗口；如果没有这行代码，真实 smoke 没有窗口可操作。
    try:  # 新增代码+Phase58RealSendInputGuard: 包住真实窗口查找、动作和观察；如果没有这行代码，异常会绕过清理。
        inventory = WindowsWindowInventoryProbe()  # 新增代码+Phase58RealSendInputGuard: 创建真实窗口枚举器；如果没有这行代码，无法复查目标身份。
        window = _poll_phase57_safe_window(inventory, str(target.get("title_hint", "")), timeout_seconds, 0.25)  # 新增代码+Phase58RealSendInputGuard: 等待自建安全窗口出现；如果没有这行代码，窗口启动延迟会误失败。
        if window is None:  # 新增代码+Phase58RealSendInputGuard: 检查是否找到窗口；如果没有这行代码，后续会对空目标发送。
            return {"real_smoke": False, "platform_supported": True, "safe_window_found": False, "safe_window_only": True, "reason": "未找到 Phase58 自有安全窗口，未发送低层事件。", "actions_expanded": PHASE58_ACTIONS_EXPANDED}  # 新增代码+Phase58RealSendInputGuard: 返回未找到结果；如果没有这行代码，失败不可解释。
        observer = Phase58UiaSafeWindowObserver()  # 新增代码+Phase58RealSendInputGuard: 创建真实 UIA 观察器；如果没有这行代码，动作前后无法复验。
        first_observe = observer.uia_runtime.observe_window(window)  # 新增代码+Phase58RealSendInputGuard: 读取安全窗口控件树用于定位文本框；如果没有这行代码，真实输入坐标只能猜。
        edit_match = _phase57_find_safe_edit_control(first_observe.get("flat_nodes", []))  # 新增代码+Phase58RealSendInputGuard: 定位安全文本框；如果没有这行代码，type_text 可能没有焦点目标。
        bounds = dict(edit_match.get("control", {}).get("bounds", {}) if isinstance(edit_match.get("control", {}), dict) else {})  # 新增代码+Phase58RealSendInputGuard: 提取文本框边界；如果没有这行代码，无法计算点击中心。
        center_x = _phase58_safe_int(bounds.get("left")) + max(5, _phase58_safe_int(bounds.get("width")) // 2)  # 新增代码+Phase58RealSendInputGuard: 计算文本框中心 x；如果没有这行代码，点击可能落不到输入框。
        center_y = _phase58_safe_int(bounds.get("top")) + max(5, _phase58_safe_int(bounds.get("height")) // 2)  # 新增代码+Phase58RealSendInputGuard: 计算文本框中心 y；如果没有这行代码，点击可能落不到输入框。
        runtime = WindowsRealSendInputGuardRuntime(platform=current_platform, inventory=inventory, observer=observer)  # 新增代码+Phase58RealSendInputGuard: 创建真实 sender runtime；如果没有这行代码，动作不会走真实 SendInput。
        secret_text = f" phase58-{int(time.time())}"  # 新增代码+Phase58RealSendInputGuard: 准备仅用于内存输入的短文本；如果没有这行代码，after_changed 不容易验证。
        result = runtime.execute_safe_action(window, "type_text", {"text": secret_text, "x": center_x, "y": center_y, "locator": {"class_name": "EDIT"}})  # 新增代码+Phase58RealSendInputGuard: 对自有安全文本框执行真实文本输入；如果没有这行代码，real_smoke 没有动作证据。
        serialized = json.dumps(result, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase58RealSendInputGuard: 序列化结果检查原文泄露；如果没有这行代码，raw_text_hidden 无法验证。
        return {"real_smoke": bool(result.get("ok") and result.get("low_level_event_count", 0) > 0 and result.get("after_state_changed")), "platform_supported": True, "safe_window_found": True, "safe_window_only": True, "target_guard": bool(result.get("target_guard_passed")), "before_after": bool(result.get("before_after_observed")), "after_changed": bool(result.get("after_state_changed")), "low_level_event_count": int(result.get("low_level_event_count", 0) or 0), "raw_text_hidden": secret_text not in serialized, "result": result, "actions_expanded": PHASE58_ACTIONS_EXPANDED}  # 新增代码+Phase58RealSendInputGuard: 返回不含原文的真实 smoke 摘要；如果没有这行代码，CLI 无法证明真实路径。
    except Exception as error:  # 新增代码+Phase58RealSendInputGuard: 捕获真实 smoke 异常；如果没有这行代码，权限或焦点问题会让命令崩溃。
        return {"real_smoke": False, "platform_supported": True, "safe_window_found": False, "safe_window_only": True, "reason": f"Phase58 真实 SendInput smoke 异常：{type(error).__name__}", "actions_expanded": PHASE58_ACTIONS_EXPANDED}  # 新增代码+Phase58RealSendInputGuard: 返回异常类型但不泄露本地细节；如果没有这行代码，用户只能看到堆栈。
    finally:  # 新增代码+Phase58RealSendInputGuard: 无论成功失败都清理安全窗口；如果没有这行代码，测试窗体可能残留。
        launcher.cleanup()  # 新增代码+Phase58RealSendInputGuard: 关闭自建安全窗口；如果没有这行代码，真实验收会留下窗口。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，run_phase58_real_sendinput_guard_smoke 到此结束；如果没有这个边界说明，初学者不容易看出真实 smoke 范围。


def run_phase58_real_sendinput_guard_contract(real_smoke: bool = True) -> dict[str, Any]:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，运行合同自检和可选真实 smoke；如果没有这段函数，CLI 和测试没有统一入口。
    from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase58RealSendInputGuard: 延迟导入静态 inventory 避免脚本模式循环；如果没有这行代码，合同无法构造可信快照。
    safe_window = _phase58_contract_window()  # 新增代码+Phase58RealSendInputGuard: 获取合同安全窗口；如果没有这行代码，自检没有目标。
    safe_sender = Phase58RecordingLowLevelSender()  # 新增代码+Phase58RealSendInputGuard: 创建安全 fake sender；如果没有这行代码，合同可能触碰真实桌面。
    safe_runtime = WindowsRealSendInputGuardRuntime(platform="win32", inventory=StaticWindowsWindowInventory([safe_window]), low_level_sender=safe_sender, observer=Phase58StaticSafeWindowObserver(before_text="before", after_text="after"))  # 新增代码+Phase58RealSendInputGuard: 创建可通过目标守卫的 runtime；如果没有这行代码，合同无法验证成功路径。
    safe_result = safe_runtime.execute_safe_action(safe_window, "click", {"x": 111, "y": 222})  # 新增代码+Phase58RealSendInputGuard: 执行 fake 点击；如果没有这行代码，target_guard 和 low_level_events 没有证据。
    forbidden_window = {"app_id": "powershell.exe", "window_id": "hwnd:9999", "title_preview": "Windows PowerShell", "rect": {"left": 0, "top": 0, "right": 800, "bottom": 400}}  # 新增代码+Phase58RealSendInputGuard: 构造禁止窗口；如果没有这行代码，零事件拒绝没有输入。
    forbidden_sender = Phase58RecordingLowLevelSender()  # 新增代码+Phase58RealSendInputGuard: 创建禁止路径 fake sender；如果没有这行代码，无法确认未发送事件。
    forbidden_runtime = WindowsRealSendInputGuardRuntime(platform="win32", inventory=StaticWindowsWindowInventory([forbidden_window]), low_level_sender=forbidden_sender, observer=Phase58StaticSafeWindowObserver())  # 新增代码+Phase58RealSendInputGuard: 创建禁止窗口 runtime；如果没有这行代码，拒绝路径无法运行。
    forbidden_result = forbidden_runtime.execute_safe_action(forbidden_window, "click", {"x": 1, "y": 1})  # 新增代码+Phase58RealSendInputGuard: 尝试禁止点击；如果没有这行代码，forbidden_zero_events 无法验证。
    text_secret = "phase58-contract-secret"  # 新增代码+Phase58RealSendInputGuard: 准备泄露检查原文；如果没有这行代码，raw_text_hidden 没有明确对象。
    text_sender = Phase58RecordingLowLevelSender()  # 新增代码+Phase58RealSendInputGuard: 创建文本 fake sender；如果没有这行代码，无法检查文本事件脱敏。
    text_runtime = WindowsRealSendInputGuardRuntime(platform="win32", inventory=StaticWindowsWindowInventory([safe_window]), low_level_sender=text_sender, observer=Phase58StaticSafeWindowObserver(before_text="before", after_text="after"))  # 新增代码+Phase58RealSendInputGuard: 创建文本 runtime；如果没有这行代码，type_text 合同无法运行。
    text_result = text_runtime.execute_safe_action(safe_window, "type_text", {"text": text_secret, "x": 120, "y": 140})  # 新增代码+Phase58RealSendInputGuard: 执行 fake 文本动作；如果没有这行代码，文本脱敏没有证据。
    real_report = run_phase58_real_sendinput_guard_smoke() if real_smoke else {"real_smoke": False, "skipped": True, "safe_window_only": True, "raw_text_hidden": True, "actions_expanded": PHASE58_ACTIONS_EXPANDED}  # 新增代码+Phase58RealSendInputGuard: 按需运行真实 smoke；如果没有这行代码，单测无法跳过真实桌面。
    visible_payload = json.dumps({"safe": safe_result, "forbidden": forbidden_result, "text": text_result, "safe_events": safe_sender.low_level_events, "text_events": text_sender.low_level_events, "real": real_report}, ensure_ascii=False, sort_keys=True).lower()  # 新增代码+Phase58RealSendInputGuard: 汇总可见输出做泄露检查；如果没有这行代码，原文可能漏到某个字段。
    target_guard = bool(safe_result.get("target_guard_passed") and (not real_smoke or real_report.get("target_guard")))  # 新增代码+Phase58RealSendInputGuard: 汇总目标守卫通过；如果没有这行代码，真实 smoke 目标失败可能被漏掉。
    low_level_events = bool(safe_result.get("low_level_event_count", 0) > 0 and (not real_smoke or real_report.get("low_level_event_count", 0) > 0))  # 新增代码+Phase58RealSendInputGuard: 汇总低层事件确实发送；如果没有这行代码，空动作可能误过。
    forbidden_zero_events = bool(forbidden_result.get("low_level_event_count") == 0 and forbidden_sender.low_level_events == [])  # 新增代码+Phase58RealSendInputGuard: 检查禁止目标零事件；如果没有这行代码，表面拒绝仍可能有副作用。
    before_after = bool(safe_result.get("before_after_observed") and (not real_smoke or real_report.get("before_after")))  # 新增代码+Phase58RealSendInputGuard: 汇总前后观察；如果没有这行代码，证据链缺口可能漏掉。
    after_changed = bool(safe_result.get("after_state_changed") and (not real_smoke or real_report.get("after_changed")))  # 新增代码+Phase58RealSendInputGuard: 汇总动作后状态变化；如果没有这行代码，验收无法证明真实效果。
    raw_text_hidden = bool(text_secret not in visible_payload and real_report.get("raw_text_hidden", True))  # 修改代码+Phase58RealSendInputGuard: 只检查真实输入原文没有进入可见输出；如果没有这行代码，字段名 raw_text_hidden 会被误判成泄露，导致安全自检假失败。
    passed = bool(target_guard and low_level_events and forbidden_zero_events and before_after and after_changed and raw_text_hidden and (not real_smoke or real_report.get("real_smoke")) and PHASE58_ACTIONS_EXPANDED)  # 新增代码+Phase58RealSendInputGuard: 汇总通过条件；如果没有这行代码，CLI 无法用退出码表达失败。
    return {"marker": PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_MARKER, "ok_token": PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_OK_TOKEN, "target_guard": target_guard, "low_level_events": low_level_events, "forbidden_zero_events": forbidden_zero_events, "before_after": before_after, "after_changed": after_changed, "raw_text_hidden": raw_text_hidden, "safe_window_only": True, "real_smoke": bool(real_report.get("real_smoke", False)), "actions_expanded": PHASE58_ACTIONS_EXPANDED, "passed": passed, "safe_result": safe_result, "forbidden_result": forbidden_result, "text_result": text_result, "real_report": real_report}  # 新增代码+Phase58RealSendInputGuard: 返回完整但脱敏的合同报告；如果没有这行代码，测试和真实终端拿不到统一事实。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，run_phase58_real_sendinput_guard_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase58_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，把报告转成稳定 token 行；如果没有这段函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_MARKER} {PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_OK_TOKEN} target_guard={_phase58_bool_token(report.get('target_guard'))} low_level_events={_phase58_bool_token(report.get('low_level_events'))} forbidden_zero_events={_phase58_bool_token(report.get('forbidden_zero_events'))} before_after={_phase58_bool_token(report.get('before_after'))} after_changed={_phase58_bool_token(report.get('after_changed'))} raw_text_hidden={_phase58_bool_token(report.get('raw_text_hidden'))} safe_window_only={_phase58_bool_token(report.get('safe_window_only'))} real_smoke={_phase58_bool_token(report.get('real_smoke'))} actions_expanded={_phase58_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase58RealSendInputGuard: 返回固定顺序 token；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，phase58_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase58RealSendInputGuard: 函数段开始，提供命令行入口；如果没有这段函数，真实终端无法执行 Phase58 验收。
    _ = argv  # 新增代码+Phase58RealSendInputGuard: 保留 argv 供未来扩展；如果没有这行代码，静态检查可能提示参数未使用。
    report = run_phase58_real_sendinput_guard_contract(real_smoke=True)  # 新增代码+Phase58RealSendInputGuard: 执行合同和真实安全窗口 SendInput smoke；如果没有这行代码，CLI 不会证明真实路径。
    print(phase58_cli_line(report))  # 新增代码+Phase58RealSendInputGuard: 打印稳定 token 行；如果没有这行代码，debug log 无法匹配验收项。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase58RealSendInputGuard: 打印脱敏结构化报告；如果没有这行代码，失败时不易复盘。
    print(PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_MARKER)  # 新增代码+Phase58RealSendInputGuard: 单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase58RealSendInputGuard: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase58RealSendInputGuard: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["PHASE58_ACTIONS_EXPANDED", "PHASE58_REAL_SENDINPUT_GUARD_MODEL", "PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_MARKER", "PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_OK_TOKEN", "Phase58RecordingLowLevelSender", "Phase58StaticSafeWindowObserver", "Phase58UiaSafeWindowObserver", "WindowsRealSendInputGuardRuntime", "WindowsSendInputLowLevelSender", "main", "phase58_cli_line", "run_phase58_real_sendinput_guard_contract", "run_phase58_real_sendinput_guard_smoke"]  # 新增代码+Phase58RealSendInputGuard: 限定公开导出名称；如果没有这行代码，包导入容易暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase58RealSendInputGuard: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase58RealSendInputGuard: 用 main 返回码退出；如果没有这行代码，命令行状态不明确。
