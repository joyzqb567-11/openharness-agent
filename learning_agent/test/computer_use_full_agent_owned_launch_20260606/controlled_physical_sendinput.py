"""Windows 受控物理 SendInput sender 适配层。"""  # 新增代码+Phase95ControlledPhysicalSendInput：说明本模块负责把 Phase94 授权后的低层事件接到受控物理后端；如果没有这行代码，读者不清楚本文件不是新的高层规划器。
from __future__ import annotations  # 新增代码+Phase95ControlledPhysicalSendInput：启用延迟类型解析；如果没有这行代码，复杂类型注解在旧导入顺序下更容易出错。

import hashlib  # 新增代码+Phase95ControlledPhysicalSendInput：导入哈希工具用于脱敏文本和标题；如果没有这行代码，报告要么泄露明文要么缺少可复盘指纹。
import json  # 新增代码+Phase95ControlledPhysicalSendInput：导入 JSON 用于合同报告和泄露扫描；如果没有这行代码，CLI 和测试无法稳定处理嵌套结果。
import os  # 新增代码+Phase95ControlledPhysicalSendInput：导入 os 读取显式真实 SendInput 环境门；如果没有这行代码，启用方式会分散且不可审计。
import sys  # 新增代码+Phase95ControlledPhysicalSendInput：导入 sys 判断当前平台；如果没有这行代码，非 Windows 上可能误触 Win32 后端。
import time  # 新增代码+Phase95ControlledPhysicalSendInput：导入 time 生成隔离合同目录；如果没有这行代码，多次验收可能互相污染。
from pathlib import Path  # 新增代码+Phase95ControlledPhysicalSendInput：导入 Path 统一处理 Windows 路径；如果没有这行代码，报告路径拼接会更脆弱。
from typing import Any  # 新增代码+Phase95ControlledPhysicalSendInput：导入 Any 描述 JSON 风格动态字典；如果没有这行代码，接口边界对初学者不清晰。

try:  # 新增代码+Phase95ControlledPhysicalSendInput：优先按包路径导入项目内组件；如果没有这段代码，单元测试和生产入口不能共享同一实现。
    from learning_agent.computer_use.authorized_real_dispatch import WindowsAuthorizedRealDispatchCandidate, run_phase94_authorized_real_dispatch_candidate_contract  # 新增代码+Phase95ControlledPhysicalSendInput：复用 Phase94 授权和目标复核；如果没有这行代码，Phase95 可能绕开已有安全门。
    from learning_agent.computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # 新增代码+Phase95ControlledPhysicalSendInput：复用项目现有 Computer Use 运行目录；如果没有这行代码，报告落点会散乱。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase95ControlledPhysicalSendInput：复用原子 JSON 写入工具；如果没有这行代码，验收报告可能半写损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase95ControlledPhysicalSendInput：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，真实终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase95ControlledPhysicalSendInput：只对包前缀缺失做 fallback；如果没有这行代码，内部真实 bug 可能被误吞。
        raise  # 新增代码+Phase95ControlledPhysicalSendInput：重新抛出非路径类导入错误；如果没有这行代码，排查底层模块问题会很困难。
    from computer_use.authorized_real_dispatch import WindowsAuthorizedRealDispatchCandidate, run_phase94_authorized_real_dispatch_candidate_contract  # type: ignore  # 新增代码+Phase95ControlledPhysicalSendInput：脚本模式复用 Phase94；如果没有这行代码，bat 入口无法跑合同。
    from computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # type: ignore  # 新增代码+Phase95ControlledPhysicalSendInput：脚本模式复用默认目录；如果没有这行代码，报告目录无法稳定定位。
    from runtime.files import atomic_write_json  # type: ignore  # 新增代码+Phase95ControlledPhysicalSendInput：脚本模式复用原子写入；如果没有这行代码，bat 验收报告可能写坏。

PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_MARKER = "PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_READY"  # 新增代码+Phase95ControlledPhysicalSendInput：定义 Phase95 ready marker；如果没有这行代码，真实终端验收没有稳定等待锚点。
PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_OK_TOKEN = "PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_OK"  # 新增代码+Phase95ControlledPhysicalSendInput：定义 Phase95 OK token；如果没有这行代码，日志无法区分普通输出和验收成功。
PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_MODEL = "phase95_controlled_physical_sendinput"  # 新增代码+Phase95ControlledPhysicalSendInput：定义报告模型名；如果没有这行代码，状态矩阵无法区分当前合同版本。
PHASE95_REAL_SENDINPUT_ENV = "LEARNING_AGENT_PHASE95_ENABLE_REAL_SENDINPUT"  # 新增代码+Phase95ControlledPhysicalSendInput：定义真实 SendInput 环境门；如果没有这行代码，生产启用方式会漂移且难审计。
PHASE95_REAL_SENDINPUT_DEFAULT_DISABLED = True  # 新增代码+Phase95ControlledPhysicalSendInput：声明真实物理派发默认关闭；如果没有这行代码，用户可能误以为普通运行会控制桌面。
PHASE95_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase95ControlledPhysicalSendInput：声明本阶段没有开放无授权动作面；如果没有这行代码，能力边界容易被误读。
DEFAULT_PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_ROOT = DEFAULT_PERSISTENT_GRANTS_ROOT.parent / "phase95_controlled_physical_sendinput"  # 新增代码+Phase95ControlledPhysicalSendInput：定义默认报告根目录；如果没有这行代码，验收证据没有固定落点。
PHASE95_SUPPORTED_LOW_LEVEL_TYPES = ("set_foreground", "mouse_move", "mouse_down", "mouse_up", "mouse_wheel", "keyboard_text", "unicode_text", "key_down", "key_up")  # 修改代码+RealLaunchTargetSession：低层白名单加入前台窗口事件；如果没有这一项，agent 启动的窗口不能在真实输入前置前。
PHASE95_RAW_TEXT_KEYS = ("text", "raw_text", "value", "characters", "unicode")  # 新增代码+Phase95ControlledPhysicalSendInput：定义禁止出现在事件里的明文字段；如果没有这行代码，用户输入可能被下放到日志或后端。
PHASE95_FORBIDDEN_TARGET_TOKENS = ("codex", "terminal", "powershell", "cmd.exe", "windows terminal", "password", "auth", "login", "captcha", "security", "admin", "uac", "credential", "验证码", "密码", "认证")  # 新增代码+Phase95ControlledPhysicalSendInput：定义高风险目标关键词；如果没有这行代码，终端、认证或安全窗口可能被误操作。


def _phase95_bool_token(value: Any) -> str:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+Phase95ControlledPhysicalSendInput：返回 true 或 false 文本；如果没有这行代码，验收脚本匹配会不稳定。
# 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，_phase95_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。


def _phase95_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，安全转换坐标和滚轮值；如果没有这段函数，坏输入会让事件构造崩溃。
    try:  # 新增代码+Phase95ControlledPhysicalSendInput：尝试按整数读取输入；如果没有这行代码，字符串坐标无法兼容。
        return int(value)  # 新增代码+Phase95ControlledPhysicalSendInput：返回转换后的整数；如果没有这行代码，后端拿不到可用坐标。
    except (TypeError, ValueError):  # 新增代码+Phase95ControlledPhysicalSendInput：捕获 None 和非数字文本；如果没有这行代码，坏参数会中断 agent。
        return int(default)  # 新增代码+Phase95ControlledPhysicalSendInput：返回默认值兜底；如果没有这行代码，调用方需要到处写容错。
# 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，_phase95_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出容错范围。


def _phase95_sha256_16(value: Any) -> str:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，生成短哈希用于脱敏审计；如果没有这段函数，报告无法既不泄露又可复盘。
    text = str(value or "")  # 新增代码+Phase95ControlledPhysicalSendInput：把输入规整成字符串；如果没有这行代码，None 或数字无法稳定哈希。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16] if text else ""  # 新增代码+Phase95ControlledPhysicalSendInput：返回前 16 位哈希或空串；如果没有这行代码，脱敏指纹不可用。
# 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，_phase95_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。


def _phase95_event_type(event: dict[str, Any]) -> str:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，兼容 Phase94 的 kind 和旧 sender 的 type；如果没有这段函数，Phase94 事件会被误判为未知。
    return str(event.get("kind") or event.get("type") or "").strip()  # 新增代码+Phase95ControlledPhysicalSendInput：优先读取 kind 再读 type；如果没有这行代码，事件类型字段漂移会导致拒绝。
# 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，_phase95_event_type 到此结束；如果没有这个边界说明，初学者不容易看出兼容范围。


def _phase95_target_identity(window: dict[str, Any]) -> dict[str, str]:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，生成不含完整标题的目标身份；如果没有这段函数，事件无法证明发往哪个窗口。
    title = str(window.get("title_preview") or window.get("title") or "")  # 新增代码+Phase95ControlledPhysicalSendInput：读取标题只用于哈希；如果没有这行代码，目标标题变化无法参与审计。
    return {"app_id": str(window.get("app_id") or window.get("process_name") or "").lower(), "process_name": str(window.get("process_name") or window.get("app_id") or "").lower(), "window_id": str(window.get("window_id") or window.get("hwnd") or ""), "display_id": str(window.get("display_id") or window.get("monitor_id") or ""), "title_sha256_16": _phase95_sha256_16(title)}  # 新增代码+Phase95ControlledPhysicalSendInput：返回脱敏目标身份；如果没有这行代码，后端审计会缺少目标边界。
# 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，_phase95_target_identity 到此结束；如果没有这个边界说明，初学者不容易看出身份字段范围。


def _phase95_real_sendinput_enabled(explicit_value: bool | None = None, default_value: bool | None = None) -> bool:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，统一判断真实物理派发是否启用；如果没有这段函数，启用逻辑会分散。
    if explicit_value is not None:  # 新增代码+Phase95ControlledPhysicalSendInput：调用方显式传值时优先使用；如果没有这行代码，单测和上层 runtime 难以可控覆盖。
        return bool(explicit_value)  # 新增代码+Phase95ControlledPhysicalSendInput：返回显式布尔值；如果没有这行代码，显式开关不会生效。
    if default_value is not None:  # 新增代码+Phase95ControlledPhysicalSendInput：实例默认值存在时使用实例默认值；如果没有这行代码，Phase94 注入 sender 时无法启用正向桥接。
        return bool(default_value)  # 新增代码+Phase95ControlledPhysicalSendInput：返回实例默认布尔值；如果没有这行代码，构造期配置会被忽略。
    return str(os.environ.get(PHASE95_REAL_SENDINPUT_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase95ControlledPhysicalSendInput：仅接受明确真值环境变量；如果没有这行代码，模糊环境值可能误开启真实输入。
# 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，_phase95_real_sendinput_enabled 到此结束；如果没有这个边界说明，初学者不容易看出启用规则。


def _phase95_target_is_unsafe(target: dict[str, Any]) -> tuple[bool, str]:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，识别高风险目标窗口；如果没有这段函数，终端或认证窗口可能被误操作。
    if not isinstance(target, dict) or not target:  # 新增代码+Phase95ControlledPhysicalSendInput：没有目标身份时拒绝；如果没有这行代码，事件可能在焦点漂移后打到未知窗口。
        return True, "missing_target_identity"  # 新增代码+Phase95ControlledPhysicalSendInput：返回缺失身份原因；如果没有这行代码，拒绝原因不清楚。
    combined = " ".join(str(target.get(key, "") or "").lower() for key in ("app_id", "process_name", "title", "title_preview", "window_title", "window_id"))  # 新增代码+Phase95ControlledPhysicalSendInput：合并可见目标线索；如果没有这行代码，风险判断会散落在多个分支。
    if any(token in combined for token in PHASE95_FORBIDDEN_TARGET_TOKENS):  # 新增代码+Phase95ControlledPhysicalSendInput：检查高风险关键词；如果没有这行代码，PowerShell 或登录窗口可能被放行。
        return True, "target_is_forbidden_sensitive_or_terminal"  # 新增代码+Phase95ControlledPhysicalSendInput：返回命中高风险原因；如果没有这行代码，审计无法解释为什么拒绝。
    return False, "target_allowed_by_phase95_sender"  # 新增代码+Phase95ControlledPhysicalSendInput：返回目标允许原因；如果没有这行代码，正向路径缺少可读解释。
# 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，_phase95_target_is_unsafe 到此结束；如果没有这个边界说明，初学者不容易看出目标检查范围。


def _phase95_safe_event_summary(event: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，生成不含明文的事件摘要；如果没有这段函数，拒绝报告可能泄露坏事件内容。
    event_type = _phase95_event_type(event)  # 新增代码+Phase95ControlledPhysicalSendInput：读取事件类型；如果没有这行代码，摘要缺少核心分类。
    target = dict(event.get("target", {})) if isinstance(event.get("target"), dict) else {}  # 新增代码+Phase95ControlledPhysicalSendInput：复制目标身份；如果没有这行代码，调用方对象可能被修改。
    return {"event_type": event_type, "target": {key: str(target.get(key, "")) for key in ("app_id", "process_name", "window_id", "display_id", "title_sha256_16")}, "raw_text_included": False}  # 新增代码+Phase95ControlledPhysicalSendInput：返回脱敏摘要；如果没有这行代码，错误报告要么过少要么泄露。
# 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，_phase95_safe_event_summary 到此结束；如果没有这个边界说明，初学者不容易看出摘要范围。


def _phase95_backend_event(event: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，把 Phase94 kind 事件转成后端更常见的 type 事件；如果没有这段函数，真实 SendInput 后端可能不认识 kind。
    event_type = _phase95_event_type(event)  # 新增代码+Phase95ControlledPhysicalSendInput：读取兼容事件类型；如果没有这行代码，转换分支没有依据。
    clean_event = {key: value for key, value in dict(event).items() if key not in set(PHASE95_RAW_TEXT_KEYS)}  # 新增代码+Phase95ControlledPhysicalSendInput：复制并删除明文字段；如果没有这行代码，坏事件可能继续携带原文。
    clean_event["type"] = event_type  # 新增代码+Phase95ControlledPhysicalSendInput：写入后端通用 type 字段；如果没有这行代码，Phase58 后端无法识别事件。
    clean_event.pop("kind", None)  # 新增代码+Phase95ControlledPhysicalSendInput：删除 Phase94 专用 kind 字段；如果没有这行代码，后端可能收到重复类型字段。
    if event_type == "mouse_wheel" and "delta" not in clean_event and "delta_y" in clean_event:  # 新增代码+Phase95ControlledPhysicalSendInput：兼容 Phase94 的 delta_y；如果没有这行代码，滚轮方向可能丢失。
        clean_event["delta"] = _phase95_safe_int(clean_event.get("delta_y"))  # 新增代码+Phase95ControlledPhysicalSendInput：写入后端常用 delta 字段；如果没有这行代码，滚轮后端可能无法执行。
    return clean_event  # 新增代码+Phase95ControlledPhysicalSendInput：返回安全后端事件；如果没有这行代码，sender 无法调用底层后端。
# 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，_phase95_backend_event 到此结束；如果没有这个边界说明，初学者不容易看出事件转换范围。

def _phase95_backend_reports_real_dispatch(backend_result: dict[str, Any], backend_events: list[dict[str, Any]]) -> bool:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，统一判断后端是否真的触碰桌面；如果没有这段函数，真实 WindowsSendInputLowLevelSender 可能被误判为 fake。
    backend_sender = str(backend_result.get("sender") or backend_result.get("backend") or "").strip().lower()  # 新增代码+Phase96ControlledPhysicalLiveSmoke：读取后端 sender 标识；如果没有这行代码，无法识别真实 low-level sender。
    backend_count = _phase95_safe_int(backend_result.get("low_level_event_count", backend_result.get("backend_event_count", len(backend_events))))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：读取后端确认发送的事件数；如果没有这行代码，真实 sender 名称没有数量证据。
    explicit_real = bool(backend_result.get("real_desktop_touched") or backend_result.get("real_dispatch_performed"))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：保留已有显式真实派发字段；如果没有这行代码，Phase96 包装后端和未来后端的声明会失效。
    inferred_real = bool(backend_sender == "windows_sendinput_low_level" and backend_count > 0 and bool(backend_events))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：根据真实 SendInput sender 标识和事件数做保守推断；如果没有这行代码，Phase58 真实后端会被报告成未触碰桌面。
    return bool(explicit_real or inferred_real)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回真实桌面副作用判断；如果没有这行代码，上层合同无法得到统一事实。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，_phase95_backend_reports_real_dispatch 到此结束；如果没有这个边界说明，初学者不容易看出真实派发推断范围。


class Phase95RecordingSendInputBackend:  # 新增代码+Phase95ControlledPhysicalSendInput：类段开始，定义安全记录后端；如果没有这个类，合同测试可能误触真实鼠标键盘。
    requires_raw_text = False  # 新增代码+Phase95ControlledPhysicalSendInput：声明记录后端不需要原文；如果没有这行代码，sender 可能误以为 fake 后端要明文。

    def __init__(self, physical_dispatch: bool = False) -> None:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，初始化记录后端；如果没有这段函数，测试无法保存后端调用证据。
        self.physical_dispatch = bool(physical_dispatch)  # 新增代码+Phase95ControlledPhysicalSendInput：保存是否模拟物理后端接收；如果没有这行代码，合同无法区分默认关闭和显式桥接。
        self.send_count = 0  # 新增代码+Phase95ControlledPhysicalSendInput：记录调用次数；如果没有这行代码，零副作用无法被验证。
        self.events: list[dict[str, Any]] = []  # 新增代码+Phase95ControlledPhysicalSendInput：保存脱敏事件副本；如果没有这行代码，测试无法检查事件数量和类型。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，Phase95RecordingSendInputBackend.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，记录低层事件而不触碰真实系统；如果没有这段函数，合同没有安全后端替身。
        safe_events = [dict(event) for event in list(events or [])]  # 新增代码+Phase95ControlledPhysicalSendInput：复制事件避免调用方后续修改污染记录；如果没有这行代码，测试证据可能不稳定。
        self.send_count += 1  # 新增代码+Phase95ControlledPhysicalSendInput：记录一次后端调用；如果没有这行代码，默认关闭是否绕过后端不可见。
        self.events.extend(safe_events)  # 新增代码+Phase95ControlledPhysicalSendInput：保存事件副本；如果没有这行代码，后续断言看不到事件细节。
        return {"ok": bool(safe_events), "backend": "phase95_recording_sendinput_backend", "backend_event_count": len(safe_events), "backend_dispatch_performed": bool(self.physical_dispatch and safe_events), "simulated_physical_dispatch": bool(self.physical_dispatch and safe_events), "real_desktop_touched": False, "raw_text_included": False, "event_types": [_phase95_event_type(event) for event in safe_events]}  # 新增代码+Phase95ControlledPhysicalSendInput：返回安全摘要；如果没有这行代码，sender 无法形成审计结果。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，Phase95RecordingSendInputBackend.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出 fake 发送范围。
# 新增代码+Phase95ControlledPhysicalSendInput：类段结束，Phase95RecordingSendInputBackend 到此结束；如果没有这个边界说明，初学者不容易看出记录后端范围。


class WindowsControlledPhysicalSendInputSender:  # 新增代码+Phase95ControlledPhysicalSendInput：类段开始，定义受控物理 sender；如果没有这个类，Phase94 低层事件仍不能进入受控物理后端。
    def __init__(self, low_level_backend: Any | None = None, platform: str | None = None, default_enable_physical_dispatch: bool | None = None) -> None:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，初始化平台、后端和默认开关；如果没有这段函数，sender 无法安全配置。
        self.platform = platform or sys.platform  # 新增代码+Phase95ControlledPhysicalSendInput：保存平台名；如果没有这行代码，非 Windows 拒绝路径不可测试。
        self.low_level_backend = low_level_backend  # 新增代码+Phase95ControlledPhysicalSendInput：保存注入后端；如果没有这行代码，最后一跳没有可调用对象。
        self.default_enable_physical_dispatch = default_enable_physical_dispatch  # 新增代码+Phase95ControlledPhysicalSendInput：保存实例默认启用值；如果没有这行代码，Phase94 注入调用无法显式开启。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，WindowsControlledPhysicalSendInputSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def contract_window(self) -> dict[str, Any]:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，返回合同用普通安全窗口；如果没有这段函数，测试没有稳定目标样本。
        return {"app_id": "notepad.exe", "process_name": "notepad.exe", "window_id": "hwnd:9505", "hwnd": 9505, "title_preview": "LearningAgent Phase95 Controlled Physical SendInput", "display_id": "DISPLAY1", "rect": {"left": 200, "top": 160, "right": 620, "bottom": 420}, "safe_to_target": True}  # 新增代码+Phase95ControlledPhysicalSendInput：返回普通应用窗口样本；如果没有这行代码，正向目标身份不稳定。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，WindowsControlledPhysicalSendInputSender.contract_window 到此结束；如果没有这个边界说明，初学者不容易看出合同目标范围。

    def contract_events(self, window: dict[str, Any], action: str, arguments: dict[str, Any] | None = None) -> list[dict[str, Any]]:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，构造 Phase94 兼容低层事件；如果没有这段函数，测试要复制事件形状。
        args = dict(arguments or {})  # 新增代码+Phase95ControlledPhysicalSendInput：复制参数避免污染调用方对象；如果没有这行代码，后续修改可能改变测试输入。
        target = _phase95_target_identity(dict(window or {}))  # 新增代码+Phase95ControlledPhysicalSendInput：生成脱敏目标身份；如果没有这行代码，事件缺少目标边界。
        action_key = str(action or "").strip().lower()  # 新增代码+Phase95ControlledPhysicalSendInput：规整动作名；如果没有这行代码，大小写和空格会导致分支漂移。
        if action_key == "click":  # 新增代码+Phase95ControlledPhysicalSendInput：处理点击动作；如果没有这行代码，合同不能生成鼠标事件。
            x = _phase95_safe_int(args.get("x"), 320)  # 新增代码+Phase95ControlledPhysicalSendInput：读取点击 x 坐标；如果没有这行代码，点击事件位置不可控。
            y = _phase95_safe_int(args.get("y"), 240)  # 新增代码+Phase95ControlledPhysicalSendInput：读取点击 y 坐标；如果没有这行代码，点击事件位置不可控。
            return [{"kind": "mouse_move", "x": x, "y": y, "target": target}, {"kind": "mouse_down", "button": "left", "x": x, "y": y, "target": target}, {"kind": "mouse_up", "button": "left", "x": x, "y": y, "target": target}]  # 新增代码+Phase95ControlledPhysicalSendInput：返回移动、按下、抬起序列；如果没有这行代码，点击不完整。
        if action_key == "scroll":  # 新增代码+Phase95ControlledPhysicalSendInput：处理滚轮动作；如果没有这行代码，合同无法覆盖滚动事件。
            return [{"kind": "mouse_wheel", "x": _phase95_safe_int(args.get("x"), 320), "y": _phase95_safe_int(args.get("y"), 240), "delta_y": _phase95_safe_int(args.get("delta_y", args.get("delta")), -120), "target": target}]  # 新增代码+Phase95ControlledPhysicalSendInput：返回滚轮事件；如果没有这行代码，滚动后端没有输入。
        if action_key == "type_text":  # 新增代码+Phase95ControlledPhysicalSendInput：处理脱敏文本事件；如果没有这行代码，合同无法验证文本不泄露。
            text = str(args.get("text") or "")  # 新增代码+Phase95ControlledPhysicalSendInput：读取原文仅用于生成哈希；如果没有这行代码，文本事件没有长度和指纹。
            return [{"kind": "keyboard_text", "text_sha256_16": _phase95_sha256_16(text), "text_length": len(text), "target": target}]  # 新增代码+Phase95ControlledPhysicalSendInput：返回不含明文的文本摘要事件；如果没有这行代码，文本输入会泄露或无法审计。
        return []  # 新增代码+Phase95ControlledPhysicalSendInput：未知动作返回空事件；如果没有这行代码，未声明动作可能误进入后端。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，WindowsControlledPhysicalSendInputSender.contract_events 到此结束；如果没有这个边界说明，初学者不容易看出事件构造范围。

    def _refusal(self, decision: str, message: str, event: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，构造统一零事件拒绝结果；如果没有这段函数，失败字段会分散不一致。
        return {"ok": False, "decision": decision, "message": message, "sender": PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_MODEL, "controlled_physical_sender_ready": True, "low_level_event_count": 0, "backend_dispatch_performed": False, "real_dispatch_performed": False, "real_desktop_touched": False, "raw_text_hidden": True, "uncontrolled_actions_expanded": PHASE95_UNCONTROLLED_ACTIONS_EXPANDED, "event": _phase95_safe_event_summary(event or {}) if event is not None else {}}  # 新增代码+Phase95ControlledPhysicalSendInput：返回脱敏拒绝摘要；如果没有这行代码，拒绝路径可能有副作用或泄露。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，WindowsControlledPhysicalSendInputSender._refusal 到此结束；如果没有这个边界说明，初学者不容易看出拒绝格式范围。

    def _backend(self) -> Any | None:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，返回可用后端；如果没有这段函数，真实后端创建逻辑会散落。
        if self.low_level_backend is not None:  # 新增代码+Phase95ControlledPhysicalSendInput：优先使用注入后端；如果没有这行代码，测试和生产无法明确控制最后一跳。
            return self.low_level_backend  # 新增代码+Phase95ControlledPhysicalSendInput：返回注入后端；如果没有这行代码，fake 后端不会生效。
        try:  # 新增代码+Phase95ControlledPhysicalSendInput：按需导入 Phase58 真实 sender；如果没有这行代码，Phase95 不能连接已有真实 SendInput 实现。
            from learning_agent.computer_use.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+Phase95ControlledPhysicalSendInput：导入真实低层 sender；如果没有这行代码，启用真实后端时没有实现来源。
        except ModuleNotFoundError:  # 新增代码+Phase95ControlledPhysicalSendInput：兼容脚本模式导入；如果没有这行代码，bat 入口可能找不到包路径。
            from computer_use.real_sendinput_guard import WindowsSendInputLowLevelSender  # type: ignore  # 新增代码+Phase95ControlledPhysicalSendInput：脚本模式导入真实 sender；如果没有这行代码，脚本入口不能复用真实后端。
        self.low_level_backend = WindowsSendInputLowLevelSender(platform=self.platform)  # 新增代码+Phase95ControlledPhysicalSendInput：延迟创建真实后端；如果没有这行代码，显式启用后仍没有物理发送器。
        return self.low_level_backend  # 新增代码+Phase95ControlledPhysicalSendInput：返回真实后端；如果没有这行代码，调用方拿不到最后一跳。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，WindowsControlledPhysicalSendInputSender._backend 到此结束；如果没有这个边界说明，初学者不容易看出后端选择范围。

    def _validate_events(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，验证事件白名单、目标和脱敏；如果没有这段函数，未知或危险事件可能进入后端。
        if not events:  # 新增代码+Phase95ControlledPhysicalSendInput：空事件直接拒绝；如果没有这行代码，空动作可能被误报成功。
            return self._refusal("no_low_level_events", "没有可发送的低层事件，已拒绝。")  # 新增代码+Phase95ControlledPhysicalSendInput：返回空事件原因；如果没有这行代码，用户看不懂为什么没有动作。
        for event in events:  # 新增代码+Phase95ControlledPhysicalSendInput：逐个检查事件；如果没有这行代码，列表里的坏事件可能漏过。
            event_type = _phase95_event_type(event)  # 新增代码+Phase95ControlledPhysicalSendInput：读取事件类型；如果没有这行代码，白名单无法判断。
            if event_type not in PHASE95_SUPPORTED_LOW_LEVEL_TYPES:  # 新增代码+Phase95ControlledPhysicalSendInput：拒绝未声明类型；如果没有这行代码，未知命令可能进入物理层。
                return self._refusal("unsupported_low_level_event_rejected", f"Phase95 不支持低层事件：{event_type}", event)  # 新增代码+Phase95ControlledPhysicalSendInput：返回未知事件拒绝；如果没有这行代码，失败原因不明确。
            if any(key in event and event.get(key) not in (None, "") for key in PHASE95_RAW_TEXT_KEYS):  # 新增代码+Phase95ControlledPhysicalSendInput：检查事件是否携带明文；如果没有这行代码，用户输入可能进入后端或报告。
                return self._refusal("raw_text_event_rejected", "低层事件包含原始文本，已拒绝。", event)  # 新增代码+Phase95ControlledPhysicalSendInput：返回明文拒绝；如果没有这行代码，隐私门禁没有执行结果。
            unsafe, reason = _phase95_target_is_unsafe(dict(event.get("target", {})) if isinstance(event.get("target"), dict) else {})  # 新增代码+Phase95ControlledPhysicalSendInput：检查目标是否危险；如果没有这行代码，事件可能发往终端或未知窗口。
            if unsafe:  # 新增代码+Phase95ControlledPhysicalSendInput：目标危险时拒绝；如果没有这行代码，风险判断结果会被忽略。
                return self._refusal("unsafe_target_rejected", reason, event)  # 新增代码+Phase95ControlledPhysicalSendInput：返回危险目标拒绝；如果没有这行代码，拒绝原因和零事件不稳定。
        return {"ok": True, "decision": "events_validated", "event_count": len(events)}  # 新增代码+Phase95ControlledPhysicalSendInput：返回验证通过摘要；如果没有这行代码，发送路径无法继续。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，WindowsControlledPhysicalSendInputSender._validate_events 到此结束；如果没有这个边界说明，初学者不容易看出验证范围。

    def send_low_level(self, events: list[dict[str, Any]], enable_physical_dispatch: bool | None = None) -> dict[str, Any]:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，受控发送低层事件；如果没有这段函数，Phase94 不能把事件交到物理后端。
        event_list = [dict(event) for event in list(events or [])]  # 新增代码+Phase95ControlledPhysicalSendInput：复制事件列表避免污染调用方；如果没有这行代码，验证和后端可能修改原始对象。
        enabled = _phase95_real_sendinput_enabled(enable_physical_dispatch, self.default_enable_physical_dispatch)  # 新增代码+Phase95ControlledPhysicalSendInput：计算是否显式启用；如果没有这行代码，默认关闭门禁不会统一生效。
        if not enabled:  # 新增代码+Phase95ControlledPhysicalSendInput：未启用时直接零事件返回；如果没有这行代码，普通运行可能触碰桌面。
            return self._refusal("real_sendinput_disabled_by_default", f"真实 SendInput 默认关闭；需要显式设置 {PHASE95_REAL_SENDINPUT_ENV}=1 或传入启用参数。")  # 新增代码+Phase95ControlledPhysicalSendInput：返回默认关闭原因；如果没有这行代码，用户会误以为动作失败是 bug。
        if self.platform != "win32":  # 新增代码+Phase95ControlledPhysicalSendInput：非 Windows 平台拒绝；如果没有这行代码，ctypes Win32 API 可能崩溃。
            return self._refusal("platform_not_windows", "当前平台不是 Windows，未触碰鼠标键盘。")  # 新增代码+Phase95ControlledPhysicalSendInput：返回平台拒绝；如果没有这行代码，失败原因不清楚。
        validation = self._validate_events(event_list)  # 新增代码+Phase95ControlledPhysicalSendInput：执行白名单、目标和脱敏验证；如果没有这行代码，危险事件可能进入后端。
        if not bool(validation.get("ok")):  # 新增代码+Phase95ControlledPhysicalSendInput：验证失败时拒绝；如果没有这行代码，拒绝结果可能被忽略。
            return validation  # 新增代码+Phase95ControlledPhysicalSendInput：返回零事件拒绝结果；如果没有这行代码，失败分支会继续发送。
        backend = self._backend()  # 新增代码+Phase95ControlledPhysicalSendInput：获取注入或真实后端；如果没有这行代码，最后一跳没有执行对象。
        if backend is None or not hasattr(backend, "send_low_level"):  # 新增代码+Phase95ControlledPhysicalSendInput：检查后端接口；如果没有这行代码，缺后端也可能被误报成功。
            return self._refusal("sendinput_backend_missing", "缺少可调用的 SendInput 后端，未触碰鼠标键盘。")  # 新增代码+Phase95ControlledPhysicalSendInput：返回后端缺失原因；如果没有这行代码，用户无法知道如何配置。
        if bool(getattr(backend, "requires_raw_text", False)) and any(_phase95_event_type(event) in {"keyboard_text", "unicode_text"} for event in event_list):  # 新增代码+Phase95ControlledPhysicalSendInput：真实后端需要明文但事件只有脱敏摘要时拒绝文本；如果没有这行代码，文本输入会失败或诱导泄露。
            return self._refusal("secure_plaintext_text_channel_missing", "真实文本输入需要短生命周期明文通道，本阶段不会把哈希事件当成明文发送。")  # 新增代码+Phase95ControlledPhysicalSendInput：返回文本通道缺失原因；如果没有这行代码，隐私边界可能被拆掉。
        backend_events = [_phase95_backend_event(event) for event in event_list]  # 新增代码+Phase95ControlledPhysicalSendInput：转换为后端事件形状；如果没有这行代码，Phase94 kind 事件可能无法被真实后端识别。
        raw_result = backend.send_low_level(backend_events)  # 新增代码+Phase95ControlledPhysicalSendInput：调用最后一跳后端；如果没有这行代码，Phase95 仍停在 recording-only 前一层。
        backend_result = dict(raw_result) if isinstance(raw_result, dict) else {"ok": bool(raw_result)}  # 新增代码+Phase95ControlledPhysicalSendInput：规整后端结果；如果没有这行代码，非 dict 返回会污染上层。
        event_types = [_phase95_event_type(event) for event in event_list]  # 新增代码+Phase95ControlledPhysicalSendInput：收集事件类型摘要；如果没有这行代码，审计看不到发送了哪些动作族。
        backend_dispatch = bool(backend_result.get("backend_dispatch_performed") or backend_result.get("ok")) and bool(backend_events)  # 新增代码+Phase95ControlledPhysicalSendInput：判断后端是否收到事件；如果没有这行代码，上层无法区分桥接成功和空跑。
        real_desktop_touched = _phase95_backend_reports_real_dispatch(backend_result, backend_events)  # 修改代码+Phase96ControlledPhysicalLiveSmoke：同时支持显式真实标记和 windows_sendinput_low_level 真实后端推断；如果没有这行代码，Phase96 真实 SendInput 路径会被误报为未触碰桌面。
        return {"ok": bool(backend_result.get("ok") and backend_events), "decision": "controlled_physical_sendinput_sent_to_backend", "sender": PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_MODEL, "controlled_physical_sender_ready": True, "low_level_event_count": len(backend_events), "event_types": event_types, "backend_dispatch_performed": backend_dispatch, "real_dispatch_performed": real_desktop_touched, "real_desktop_touched": real_desktop_touched, "raw_text_hidden": True, "uncontrolled_actions_expanded": PHASE95_UNCONTROLLED_ACTIONS_EXPANDED, "backend_result": backend_result}  # 新增代码+Phase95ControlledPhysicalSendInput：返回完整脱敏发送摘要；如果没有这行代码，合同和终端拿不到统一事实。
    # 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，WindowsControlledPhysicalSendInputSender.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出发送范围。
# 新增代码+Phase95ControlledPhysicalSendInput：类段结束，WindowsControlledPhysicalSendInputSender 到此结束；如果没有这个边界说明，初学者不容易看出 sender 范围。


def run_phase95_controlled_physical_sendinput_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，运行 Phase95 总合同；如果没有这段函数，测试和真实终端没有统一入口。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase95ControlledPhysicalSendInput：选择隔离合同目录；如果没有这行代码，多次运行会互相污染。
    root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase95ControlledPhysicalSendInput：创建合同目录；如果没有这行代码，报告写入会失败。
    phase94_report = run_phase94_authorized_real_dispatch_candidate_contract(base_dir=root / "phase94")  # 新增代码+Phase95ControlledPhysicalSendInput：运行 Phase94 合同作为授权候选基线；如果没有这行代码，Phase95 可能没有证明自己复用前置门禁。
    default_backend = Phase95RecordingSendInputBackend(physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：创建默认关闭路径后端；如果没有这行代码，无法证明关闭时不调用后端。
    default_sender = WindowsControlledPhysicalSendInputSender(low_level_backend=default_backend, platform="win32")  # 新增代码+Phase95ControlledPhysicalSendInput：创建默认关闭 sender；如果没有这行代码，安全默认值没有被测对象。
    default_events = default_sender.contract_events(default_sender.contract_window(), "click", {"x": 320, "y": 240})  # 新增代码+Phase95ControlledPhysicalSendInput：准备有效事件；如果没有这行代码，默认零发送可能只是因为没有事件。
    default_off = default_sender.send_low_level(default_events, enable_physical_dispatch=False)  # 新增代码+Phase95ControlledPhysicalSendInput：执行默认关闭路径；如果没有这行代码，default_off_zero 无证据。
    bridge_backend = Phase95RecordingSendInputBackend(physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：创建正向桥接后端；如果没有这行代码，无法证明事件到达最后一跳。
    bridge_sender = WindowsControlledPhysicalSendInputSender(low_level_backend=bridge_backend, platform="win32", default_enable_physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：创建显式启用 sender；如果没有这行代码，Phase94 调用 sender 时仍默认关闭。
    phase94_bridge_runtime = WindowsAuthorizedRealDispatchCandidate(base_dir=root / "phase94_bridge", low_level_sender=bridge_sender)  # 新增代码+Phase95ControlledPhysicalSendInput：把 Phase95 sender 注入 Phase94 runtime；如果没有这行代码，复用 Phase94 只停留在报告层。
    bridge_window = phase94_bridge_runtime.contract_window()  # 新增代码+Phase95ControlledPhysicalSendInput：读取 Phase94 合同窗口；如果没有这行代码，授权和派发没有共同目标。
    phase94_bridge_runtime.authorize_window(bridge_window, session_id="phase95-bridge", action_scope=["click"])  # 新增代码+Phase95ControlledPhysicalSendInput：写入 Phase94 授权；如果没有这行代码，安全边界应拒绝所有真实动作候选。
    bridge_result = phase94_bridge_runtime.dispatch(bridge_window, "click", {"x": 320, "y": 240}, session_id="phase95-bridge", enable_real_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：通过 Phase94 主链路进入 Phase95 sender；如果没有这行代码，授权后桥接能力没有证据。
    unsafe_backend = Phase95RecordingSendInputBackend(physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：创建危险目标后端；如果没有这行代码，无法证明拒绝路径不调用后端。
    unsafe_sender = WindowsControlledPhysicalSendInputSender(low_level_backend=unsafe_backend, platform="win32")  # 新增代码+Phase95ControlledPhysicalSendInput：创建危险目标 sender；如果没有这行代码，危险拦截没有被测对象。
    unsafe_event = {"kind": "mouse_move", "x": 1, "y": 1, "target": {"app_id": "powershell.exe", "process_name": "powershell.exe", "window_id": "hwnd:9501", "title_sha256_16": "unsafe"}}  # 新增代码+Phase95ControlledPhysicalSendInput：构造终端类危险事件；如果没有这行代码，unsafe_zero 没有样本。
    unsafe_result = unsafe_sender.send_low_level([unsafe_event], enable_physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：执行危险目标路径；如果没有这行代码，拒绝没有事实来源。
    unknown_backend = Phase95RecordingSendInputBackend(physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：创建未知事件后端；如果没有这行代码，未知事件拒绝没有副作用证据。
    unknown_sender = WindowsControlledPhysicalSendInputSender(low_level_backend=unknown_backend, platform="win32")  # 新增代码+Phase95ControlledPhysicalSendInput：创建未知事件 sender；如果没有这行代码，白名单测试没有主体。
    unknown_result = unknown_sender.send_low_level([{"kind": "launch_process", "target": unknown_sender.contract_window()}], enable_physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：执行未知事件路径；如果没有这行代码，unsupported_zero 没有结果。
    raw_backend = Phase95RecordingSendInputBackend(physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：创建明文事件后端；如果没有这行代码，明文拒绝没有副作用证据。
    raw_sender = WindowsControlledPhysicalSendInputSender(low_level_backend=raw_backend, platform="win32")  # 新增代码+Phase95ControlledPhysicalSendInput：创建明文事件 sender；如果没有这行代码，隐私门禁没有主体。
    raw_result = raw_sender.send_low_level([{"kind": "keyboard_text", "text": "phase95-secret-text", "target": raw_sender.contract_window()}], enable_physical_dispatch=True)  # 新增代码+Phase95ControlledPhysicalSendInput：执行明文坏事件路径；如果没有这行代码，raw_text_hidden 没有负样本。
    serialized = json.dumps({"default": default_off, "bridge": bridge_result, "unsafe": unsafe_result, "unknown": unknown_result, "raw": raw_result}, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase95ControlledPhysicalSendInput：序列化子报告做泄露扫描；如果没有这行代码，嵌套 secret 可能漏检。
    phase94_reused = bool(phase94_report.get("passed") and phase94_report.get("authorized_low_level_dispatch_reaches_sender") and bridge_result.get("authorized_low_level_dispatch_reaches_sender"))  # 新增代码+Phase95ControlledPhysicalSendInput：判断 Phase94 授权候选是否被复用；如果没有这行代码，桥接架构对齐不可见。
    enabled_backend_receives = bool(bridge_result.get("ok") and bridge_backend.send_count == 1 and bridge_result.get("sender_result", {}).get("backend_dispatch_performed"))  # 新增代码+Phase95ControlledPhysicalSendInput：判断后端是否收到 Phase94 事件；如果没有这行代码，正向桥接可能空跑。
    default_zero = bool(default_off.get("decision") == "real_sendinput_disabled_by_default" and default_backend.send_count == 0 and default_off.get("low_level_event_count") == 0)  # 新增代码+Phase95ControlledPhysicalSendInput：判断默认关闭是否零副作用；如果没有这行代码，安全默认值不可量化。
    unsafe_zero = bool(unsafe_result.get("decision") == "unsafe_target_rejected" and unsafe_backend.send_count == 0 and unsafe_result.get("low_level_event_count") == 0)  # 新增代码+Phase95ControlledPhysicalSendInput：判断危险目标是否零副作用；如果没有这行代码，高风险拦截不可量化。
    unsupported_zero = bool(unknown_result.get("decision") == "unsupported_low_level_event_rejected" and unknown_backend.send_count == 0 and unknown_result.get("low_level_event_count") == 0)  # 新增代码+Phase95ControlledPhysicalSendInput：判断未知事件是否零副作用；如果没有这行代码，事件白名单不可量化。
    raw_text_hidden = bool("phase95-secret-text" not in serialized and raw_result.get("decision") == "raw_text_event_rejected" and raw_backend.send_count == 0)  # 新增代码+Phase95ControlledPhysicalSendInput：判断明文是否没有泄露且没有发送；如果没有这行代码，隐私门禁不可量化。
    real_desktop_touched = bool(bridge_result.get("sender_result", {}).get("real_desktop_touched") or default_off.get("real_desktop_touched") or unsafe_result.get("real_desktop_touched") or unknown_result.get("real_desktop_touched") or raw_result.get("real_desktop_touched"))  # 新增代码+Phase95ControlledPhysicalSendInput：汇总真实桌面副作用；如果没有这行代码，合同可能过度承诺真实控制。
    report_path = root / "reports" / "phase95_controlled_physical_sendinput_report.json"  # 新增代码+Phase95ControlledPhysicalSendInput：定义报告路径；如果没有这行代码，验收证据没有固定文件。
    passed = bool(phase94_reused and enabled_backend_receives and default_zero and unsafe_zero and unsupported_zero and raw_text_hidden and not real_desktop_touched and not PHASE95_UNCONTROLLED_ACTIONS_EXPANDED)  # 新增代码+Phase95ControlledPhysicalSendInput：汇总合同通过条件；如果没有这行代码，main 无法用退出码表达失败。
    report = {"marker": PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_MARKER, "ok_token": PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_OK_TOKEN, "model": PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_MODEL, "passed": passed, "phase94_authorized_candidate_reused": phase94_reused, "controlled_physical_sender_ready": True, "default_off_zero_physical_events": default_zero, "enabled_backend_receives_low_level_events": enabled_backend_receives, "unsafe_target_zero_physical_events": unsafe_zero, "unsupported_event_zero_physical_events": unsupported_zero, "raw_text_hidden": raw_text_hidden, "real_desktop_touched": real_desktop_touched, "real_sendinput_env_gate": PHASE95_REAL_SENDINPUT_ENV, "real_sendinput_default_disabled": PHASE95_REAL_SENDINPUT_DEFAULT_DISABLED, "uncontrolled_actions_expanded": PHASE95_UNCONTROLLED_ACTIONS_EXPANDED, "report_path": str(report_path), "phase94_report_path": str(phase94_report.get("report_path", "")), "default_off_report": default_off, "bridge_report": bridge_result, "unsafe_report": unsafe_result, "unsupported_report": unknown_result, "raw_text_report": raw_result}  # 新增代码+Phase95ControlledPhysicalSendInput：构造完整脱敏报告；如果没有这行代码，测试和真实终端拿不到统一事实。
    atomic_write_json(report_path, report)  # 新增代码+Phase95ControlledPhysicalSendInput：原子写入报告文件；如果没有这行代码，异常中断可能留下半个 JSON。
    return report  # 新增代码+Phase95ControlledPhysicalSendInput：返回合同报告；如果没有这行代码，调用方无法读取验收结果。
# 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，run_phase95_controlled_physical_sendinput_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同范围。


def phase95_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，把报告转成真实终端稳定 token 行；如果没有这段函数，验收器需要解析复杂 JSON。
    return f"{PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_MARKER} {PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_OK_TOKEN} phase94_authorized_candidate_reused={_phase95_bool_token(report.get('phase94_authorized_candidate_reused'))} controlled_physical_sender_ready={_phase95_bool_token(report.get('controlled_physical_sender_ready'))} default_off_zero_physical_events={_phase95_bool_token(report.get('default_off_zero_physical_events'))} enabled_backend_receives_low_level_events={_phase95_bool_token(report.get('enabled_backend_receives_low_level_events'))} unsafe_target_zero_physical_events={_phase95_bool_token(report.get('unsafe_target_zero_physical_events'))} unsupported_event_zero_physical_events={_phase95_bool_token(report.get('unsupported_event_zero_physical_events'))} raw_text_hidden={_phase95_bool_token(report.get('raw_text_hidden'))} real_desktop_touched={_phase95_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase95_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase95ControlledPhysicalSendInput：返回固定顺序 token；如果没有这行代码，真实终端验收容易因输出漂移失败。
# 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，phase95_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase95ControlledPhysicalSendInput：函数段开始，提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase95 合同。
    _ = argv  # 新增代码+Phase95ControlledPhysicalSendInput：保留 argv 扩展位；如果没有这行代码，读者可能误以为参数被遗漏。
    report = run_phase95_controlled_physical_sendinput_contract()  # 新增代码+Phase95ControlledPhysicalSendInput：运行无真实桌面副作用合同；如果没有这行代码，CLI 不会产生验收事实。
    print(phase95_cli_line(report))  # 新增代码+Phase95ControlledPhysicalSendInput：打印稳定 token 行；如果没有这行代码，验收脚本无法快速匹配成功条件。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase95ControlledPhysicalSendInput：打印结构化脱敏报告；如果没有这行代码，失败时不易复盘。
    print(PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_MARKER)  # 新增代码+Phase95ControlledPhysicalSendInput：单独打印 ready marker；如果没有这行代码，人工观察终端时容易漏标识。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase95ControlledPhysicalSendInput：按合同结果返回退出码；如果没有这行代码，失败也可能被自动化当成成功。
# 新增代码+Phase95ControlledPhysicalSendInput：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_ROOT", "PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_MARKER", "PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_MODEL", "PHASE95_CONTROLLED_PHYSICAL_SENDINPUT_OK_TOKEN", "PHASE95_REAL_SENDINPUT_DEFAULT_DISABLED", "PHASE95_REAL_SENDINPUT_ENV", "PHASE95_UNCONTROLLED_ACTIONS_EXPANDED", "Phase95RecordingSendInputBackend", "WindowsControlledPhysicalSendInputSender", "main", "phase95_cli_line", "run_phase95_controlled_physical_sendinput_contract"]  # 新增代码+Phase95ControlledPhysicalSendInput：限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase95ControlledPhysicalSendInput：允许直接运行模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase95ControlledPhysicalSendInput：用 main 返回码退出；如果没有这行代码，命令行状态不明确。
