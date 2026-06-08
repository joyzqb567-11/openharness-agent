"""Phase96 受控物理 SendInput live smoke 合同。"""  # 新增代码+Phase96ControlledPhysicalLiveSmoke：说明本模块负责把 Phase95 受控物理 sender 接到专用安全窗口验收；如果没有这行代码，读者不容易区分 Phase95 adapter 和 Phase96 live smoke。
from __future__ import annotations  # 新增代码+Phase96ControlledPhysicalLiveSmoke：启用延迟类型解析；如果没有这行代码，部分前向类型标注在旧导入顺序下更容易失败。

import json  # 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 JSON 用于报告脱敏扫描和 CLI 输出；如果没有这行代码，验收失败时不容易复盘结构化事实。
import os  # 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 os 读取真实派发显式环境门；如果没有这行代码，真实桌面动作开关会分散且不可审计。
import sys  # 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 sys 判断当前平台；如果没有这行代码，非 Windows 环境可能误走 Win32 路径。
import time  # 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 time 生成隔离报告目录和短等待；如果没有这行代码，多次验收证据容易互相覆盖。
from pathlib import Path  # 新增代码+Phase96ControlledPhysicalLiveSmoke：导入 Path 统一处理 Windows 路径；如果没有这行代码，报告路径拼接会更脆弱。
from typing import Any, Callable  # 新增代码+Phase96ControlledPhysicalLiveSmoke：导入动态 JSON 类型和可注入 runner 类型；如果没有这行代码，公共接口边界不清楚。

try:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：优先按包路径导入项目组件；如果没有这段代码，单元测试和生产入口不能共享同一实现。
    from learning_agent.computer_use.controlled_physical_sendinput import Phase95RecordingSendInputBackend, WindowsControlledPhysicalSendInputSender  # 新增代码+Phase96ControlledPhysicalLiveSmoke：复用 Phase95 受控物理 sender；如果没有这行代码，Phase96 可能绕开安全链路。
    from learning_agent.computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # 新增代码+Phase96ControlledPhysicalLiveSmoke：复用项目 Computer Use 运行根目录；如果没有这行代码，验收报告落点会分散。
    from learning_agent.computer_use.real_sendinput_guard import WindowsSendInputLowLevelSender, run_phase58_real_sendinput_guard_smoke  # 新增代码+Phase96ControlledPhysicalLiveSmoke：复用 Phase58 真实 SendInput 和键盘 guard；如果没有这行代码，Phase96 会重复造轮子。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase96ControlledPhysicalLiveSmoke：复用原子 JSON 写入；如果没有这行代码，报告可能半写损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，真实终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：只对包前缀缺失做 fallback；如果没有这行代码，内部真实 bug 可能被误吞。
        raise  # 新增代码+Phase96ControlledPhysicalLiveSmoke：重抛非路径类导入错误；如果没有这行代码，排查底层模块问题会很困难。
    from computer_use.controlled_physical_sendinput import Phase95RecordingSendInputBackend, WindowsControlledPhysicalSendInputSender  # type: ignore  # 新增代码+Phase96ControlledPhysicalLiveSmoke：脚本模式复用 Phase95 sender；如果没有这行代码，bat 入口无法运行合同。
    from computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # type: ignore  # 新增代码+Phase96ControlledPhysicalLiveSmoke：脚本模式复用默认目录；如果没有这行代码，报告目录无法稳定定位。
    from computer_use.real_sendinput_guard import WindowsSendInputLowLevelSender, run_phase58_real_sendinput_guard_smoke  # type: ignore  # 新增代码+Phase96ControlledPhysicalLiveSmoke：脚本模式复用 Phase58；如果没有这行代码，bat 入口无法验证真实输入 guard。
    from runtime.files import atomic_write_json  # type: ignore  # 新增代码+Phase96ControlledPhysicalLiveSmoke：脚本模式复用原子写入；如果没有这行代码，bat 验收报告可能写坏。

PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_MARKER = "PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_READY"  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义 Phase96 ready marker；如果没有这行代码，真实终端验收没有稳定等待锚点。
PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_OK_TOKEN = "PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_OK"  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义 Phase96 OK token；如果没有这行代码，日志无法区分成功合同和普通输出。
PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_MODEL = "phase96_controlled_physical_live_smoke"  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义报告模型名；如果没有这行代码，状态矩阵无法区分当前合同版本。
PHASE96_REAL_SENDINPUT_LIVE_SMOKE_ENV = "LEARNING_AGENT_PHASE96_ENABLE_REAL_SENDINPUT_LIVE_SMOKE"  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义真实 SendInput live smoke 环境门；如果没有这行代码，生产启用方式不可审计。
PHASE96_REAL_SENDINPUT_LIVE_SMOKE_REQUEST_ENV = "LEARNING_AGENT_PHASE96_RUN_REAL_SMOKE"  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义 CLI 请求真实 smoke 的环境门；如果没有这行代码，终端无法显式进入真实路径。
PHASE96_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase96ControlledPhysicalLiveSmoke：声明 Phase96 没有开放无边界桌面控制；如果没有这行代码，能力范围容易被误读。
DEFAULT_PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_ROOT = DEFAULT_PERSISTENT_GRANTS_ROOT.parent / "phase96_controlled_physical_live_smoke"  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义默认报告根目录；如果没有这行代码，验收证据没有固定落点。

def _phase96_bool_token(value: Any) -> str:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回 true 或 false 文本；如果没有这行代码，验收脚本匹配会不稳定。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，_phase96_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。

def _phase96_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，安全转换坐标和计数；如果没有这段函数，坏输入会让真实路径崩溃。
    try:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：尝试把动态值转成整数；如果没有这行代码，字符串坐标无法兼容。
        return int(value)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回转换后的整数；如果没有这行代码，后端拿不到可用坐标。
    except (TypeError, ValueError):  # 新增代码+Phase96ControlledPhysicalLiveSmoke：捕获 None 和非数字文本；如果没有这行代码，坏字段会中断 agent。
        return int(default)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回默认值兜底；如果没有这行代码，调用方需要到处写容错。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，_phase96_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出容错范围。

def _phase96_gate_enabled(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，统一判断真实 live smoke 环境门；如果没有这段函数，启用逻辑会散落在代码里。
    if explicit_value is not None:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：测试或上层显式传值时优先使用；如果没有这行代码，单元测试无法安全覆盖真实路径。
        return bool(explicit_value)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回显式布尔值；如果没有这行代码，注入开关不会生效。
    return str(os.environ.get(PHASE96_REAL_SENDINPUT_LIVE_SMOKE_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：只接受明确真值环境变量；如果没有这行代码，模糊环境值可能误开真实输入。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，_phase96_gate_enabled 到此结束；如果没有这个边界说明，初学者不容易看出环境门范围。

def _phase96_request_real_smoke(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，统一判断本次是否请求真实 smoke；如果没有这段函数，CLI 和测试请求方式会漂移。
    if explicit_value is not None:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：调用方显式传值时优先使用；如果没有这行代码，单元测试不能避免读取真实环境。
        return bool(explicit_value)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回显式请求值；如果没有这行代码，测试参数不会生效。
    return str(os.environ.get(PHASE96_REAL_SENDINPUT_LIVE_SMOKE_REQUEST_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：读取 CLI 请求环境门；如果没有这行代码，真实终端无法显式触发 live smoke。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，_phase96_request_real_smoke 到此结束；如果没有这个边界说明，初学者不容易看出请求门范围。

def _phase96_safe_target_window(window_id: str = "phase96-safe-window") -> dict[str, Any]:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，构造 Phase95 可接受的专用安全目标身份；如果没有这段函数，真实 click 事件可能缺少目标边界。
    return {"app_id": "phase96_controlled_safe_window", "process_name": "phase96_controlled_safe_window", "window_id": str(window_id), "display_id": "DISPLAY1", "title_preview": "LearningAgent-Phase96-ControlledPhysicalLiveSmoke"}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回非终端非认证目标摘要；如果没有这行代码，Phase95 可能按危险目标拒绝自建安全窗口。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，_phase96_safe_target_window 到此结束；如果没有这个边界说明，初学者不容易看出目标身份范围。

class Phase96RealSendInputLowLevelBackend:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：类段开始，包装真实 WindowsSendInputLowLevelSender 并补充真实副作用标记；如果没有这个类，Phase96 real path 可能只返回低层 sender 名称。
    requires_raw_text = False  # 新增代码+Phase96ControlledPhysicalLiveSmoke：声明本后端不接收原始文本；如果没有这行代码，Phase95 会担心 raw text 泄露而拒绝事件。
    def __init__(self, platform: str | None = None) -> None:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，保存运行平台；如果没有这段函数，测试无法注入平台。
        self.platform = platform or sys.platform  # 新增代码+Phase96ControlledPhysicalLiveSmoke：记录平台默认值；如果没有这行代码，非 Windows 检查可能不稳定。
    # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，Phase96RealSendInputLowLevelBackend.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。
    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，把事件转给真实 low-level sender；如果没有这段函数，Phase96 不能触达真实 SendInput。
        sender = WindowsSendInputLowLevelSender(platform=self.platform)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建真实 Windows 低层 sender；如果没有这行代码，物理派发不会发生。
        result = dict(sender.send_low_level(events))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：执行真实低层事件并复制结果；如果没有这行代码，后续不能脱敏补充字段。
        real_touch = bool(result.get("ok") and _phase96_safe_int(result.get("low_level_event_count")) > 0 and result.get("sender") == "windows_sendinput_low_level")  # 新增代码+Phase96ControlledPhysicalLiveSmoke：根据真实 sender 标识和事件数判断桌面副作用；如果没有这行代码，报告层会低估真实派发。
        result["real_desktop_touched"] = real_touch  # 新增代码+Phase96ControlledPhysicalLiveSmoke：写入真实桌面触碰标记；如果没有这行代码，上层无法区别 fake 与真实 sender。
        result["real_dispatch_performed"] = real_touch  # 新增代码+Phase96ControlledPhysicalLiveSmoke：写入真实派发发生标记；如果没有这行代码，Phase95 兼容字段可能为空。
        result["raw_text_included"] = False  # 新增代码+Phase96ControlledPhysicalLiveSmoke：明确结果不含原始文本；如果没有这行代码，隐私验收无法稳定判断。
        return result  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回补充后的脱敏结果；如果没有这行代码，调用方拿不到发送事实。
    # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，Phase96RealSendInputLowLevelBackend.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出真实 sender 范围。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：类段结束，Phase96RealSendInputLowLevelBackend 到此结束；如果没有这个边界说明，初学者不容易看出 backend 范围。

def _phase96_run_static_mouse_bridge(low_level_backend: Any, platform: str | None = None) -> dict[str, Any]:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，用注入后端验证 Phase95 mouse bridge；如果没有这段函数，单测无法不碰桌面地覆盖显式路径。
    sender = WindowsControlledPhysicalSendInputSender(low_level_backend=low_level_backend, platform=platform or "win32", default_enable_physical_dispatch=True)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建显式启用的 Phase95 sender；如果没有这行代码，Phase96 可能绕开受控 sender。
    window = _phase96_safe_target_window()  # 新增代码+Phase96ControlledPhysicalLiveSmoke：构造安全目标身份；如果没有这行代码，Phase95 目标校验没有输入。
    events = sender.contract_events(window, "click", {"x": 333, "y": 222})  # 新增代码+Phase96ControlledPhysicalLiveSmoke：构造鼠标点击低层事件；如果没有这行代码，后端不会收到可验证事件。
    result = sender.send_low_level(events, enable_physical_dispatch=True)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：通过 Phase95 发送事件；如果没有这行代码，bridge 没有事实来源。
    return {"executed": True, "safe_window_only": True, "phase95_controlled_sender_reused": bool(result.get("controlled_physical_sender_ready")), "phase95_physical_mouse_bridge": bool(result.get("ok") and result.get("real_desktop_touched")), "real_desktop_touched": bool(result.get("real_desktop_touched")), "low_level_event_count": _phase96_safe_int(result.get("low_level_event_count")), "event_types": list(result.get("event_types", [])), "result": result}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回脱敏 bridge 摘要；如果没有这行代码，合同无法判断是否成功。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，_phase96_run_static_mouse_bridge 到此结束；如果没有这个边界说明，初学者不容易看出静态 bridge 范围。

def _phase96_run_real_mouse_bridge(platform: str | None = None) -> dict[str, Any]:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，在专用安全窗口中执行真实鼠标 bridge；如果没有这段函数，Phase96 只能停留在 fake 后端。
    current_platform = platform or sys.platform  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确定当前平台；如果没有这行代码，非 Windows 兜底不稳定。
    if current_platform != "win32":  # 新增代码+Phase96ControlledPhysicalLiveSmoke：只允许 Windows 真实 SendInput；如果没有这行代码，其他系统可能误调用 Win32 API。
        return {"executed": False, "platform_supported": False, "safe_window_only": True, "phase95_physical_mouse_bridge": False, "real_desktop_touched": False, "reason": "platform_not_windows"}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回平台不支持且零副作用；如果没有这行代码，失败原因不清楚。
    from learning_agent.computer_use.real_sendinput_guard import Phase58UiaSafeWindowObserver  # 新增代码+Phase96ControlledPhysicalLiveSmoke：延迟导入 UIA observer；如果没有这行代码，真实窗口坐标无法定位。
    from learning_agent.computer_use.real_uia_locator import Phase57DedicatedSafeWindowLauncher, _phase57_find_safe_edit_control, _poll_phase57_safe_window  # 新增代码+Phase96ControlledPhysicalLiveSmoke：延迟导入专用安全窗口工具；如果没有这行代码，真实动作没有隔离目标。
    from learning_agent.computer_use.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase96ControlledPhysicalLiveSmoke：延迟导入真实窗口枚举；如果没有这行代码，无法找到自建安全窗口。
    launcher = Phase57DedicatedSafeWindowLauncher(marker_text="LearningAgent Phase96 controlled physical live smoke", title_prefix="LearningAgent-Phase96-ControlledPhysicalLiveSmoke")  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建 Phase96 专用安全窗口；如果没有这行代码，真实点击可能落到用户窗口。
    target = launcher.launch()  # 新增代码+Phase96ControlledPhysicalLiveSmoke：启动安全窗口；如果没有这行代码，真实 smoke 没有可操作目标。
    try:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：包住窗口发现、定位和发送流程；如果没有这行代码，异常会绕过清理。
        inventory = WindowsWindowInventoryProbe()  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建真实窗口枚举器；如果没有这行代码，无法复核目标身份。
        window = _poll_phase57_safe_window(inventory, str(target.get("title_hint", "")), 8.0, 0.25)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：等待自建安全窗口出现；如果没有这行代码，窗口启动延迟会导致误失败。
        if window is None:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：检查是否找到窗口；如果没有这行代码，后续可能对空目标发事件。
            return {"executed": False, "platform_supported": True, "safe_window_found": False, "safe_window_only": True, "phase95_physical_mouse_bridge": False, "real_desktop_touched": False, "reason": "phase96_safe_window_not_found"}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回未找到窗口且零事件；如果没有这行代码，失败不可解释。
        observer = Phase58UiaSafeWindowObserver()  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建 UIA observer；如果没有这行代码，点击坐标只能猜。
        observed = observer.uia_runtime.observe_window(window)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：读取安全窗口控件树；如果没有这行代码，无法定位文本框中心。
        edit_match = _phase57_find_safe_edit_control(observed.get("flat_nodes", []))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：寻找安全文本框；如果没有这行代码，点击可能落不到可见控件。
        bounds = dict(edit_match.get("control", {}).get("bounds", {}) if isinstance(edit_match.get("control", {}), dict) else {})  # 新增代码+Phase96ControlledPhysicalLiveSmoke：提取控件边界；如果没有这行代码，坐标计算没有来源。
        center_x = _phase96_safe_int(bounds.get("left")) + max(5, _phase96_safe_int(bounds.get("width")) // 2)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：计算点击中心 x；如果没有这行代码，鼠标事件可能落到窗口外。
        center_y = _phase96_safe_int(bounds.get("top")) + max(5, _phase96_safe_int(bounds.get("height")) // 2)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：计算点击中心 y；如果没有这行代码，鼠标事件可能落到窗口外。
        backend = Phase96RealSendInputLowLevelBackend(platform=current_platform)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建真实 SendInput backend；如果没有这行代码，Phase95 事件不会触达系统。
        sender = WindowsControlledPhysicalSendInputSender(low_level_backend=backend, platform=current_platform, default_enable_physical_dispatch=True)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建受控 Phase95 sender；如果没有这行代码，真实事件会绕开安全校验。
        safe_window = _phase96_safe_target_window(str(window.get("window_id") or window.get("hwnd") or "phase96-live-window"))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：构造专用安全目标身份；如果没有这行代码，Phase95 无法审计目标边界。
        events = sender.contract_events(safe_window, "click", {"x": center_x, "y": center_y})  # 新增代码+Phase96ControlledPhysicalLiveSmoke：生成真实鼠标点击事件；如果没有这行代码，真实 backend 没有输入。
        result = sender.send_low_level(events, enable_physical_dispatch=True)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：通过 Phase95 受控路径发送真实鼠标事件；如果没有这行代码，Phase96 无法证明 live mouse bridge。
        return {"executed": True, "platform_supported": True, "safe_window_found": True, "safe_window_only": True, "phase95_controlled_sender_reused": bool(result.get("controlled_physical_sender_ready")), "phase95_physical_mouse_bridge": bool(result.get("ok") and result.get("real_desktop_touched")), "real_desktop_touched": bool(result.get("real_desktop_touched")), "low_level_event_count": _phase96_safe_int(result.get("low_level_event_count")), "event_types": list(result.get("event_types", [])), "result": result}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回真实鼠标 bridge 摘要；如果没有这行代码，合同无法判断真实路径。
    except Exception as error:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：捕获真实窗口和输入异常；如果没有这行代码，权限或焦点问题会让命令崩溃。
        return {"executed": False, "platform_supported": True, "safe_window_only": True, "phase95_physical_mouse_bridge": False, "real_desktop_touched": False, "reason": f"phase96_real_mouse_bridge_error:{type(error).__name__}"}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回异常类型但不泄露本地细节；如果没有这行代码，失败难以审计。
    finally:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：无论成功失败都清理安全窗口；如果没有这行代码，验收窗口可能残留。
        launcher.cleanup()  # 新增代码+Phase96ControlledPhysicalLiveSmoke：关闭自建安全窗口；如果没有这行代码，真实验收会留下临时窗口。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，_phase96_run_real_mouse_bridge 到此结束；如果没有这个边界说明，初学者不容易看出真实 mouse bridge 范围。

def _phase96_run_keyboard_guard(phase58_smoke_runner: Callable[[], dict[str, Any]] | None = None) -> dict[str, Any]:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，复用 Phase58 键盘真实 guard；如果没有这段函数，Phase96 只能证明鼠标不能证明键盘。
    runner = phase58_smoke_runner or run_phase58_real_sendinput_guard_smoke  # 新增代码+Phase96ControlledPhysicalLiveSmoke：选择注入 runner 或真实 Phase58 runner；如果没有这行代码，测试和生产无法共享入口。
    report = dict(runner())  # 新增代码+Phase96ControlledPhysicalLiveSmoke：执行并复制键盘 guard 报告；如果没有这行代码，Phase96 没有键盘路径证据。
    return {"executed": True, "phase58_keyboard_guard_reused": bool(report.get("real_smoke") and report.get("safe_window_only") and report.get("raw_text_hidden")), "safe_window_only": bool(report.get("safe_window_only", True)), "low_level_event_count": _phase96_safe_int(report.get("low_level_event_count")), "raw_text_hidden": bool(report.get("raw_text_hidden", True)), "report": report}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回键盘 guard 摘要；如果没有这行代码，合同无法汇总键盘证据。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，_phase96_run_keyboard_guard 到此结束；如果没有这个边界说明，初学者不容易看出键盘 guard 范围。

def run_phase96_controlled_physical_live_smoke_contract(base_dir: str | Path | None = None, real_smoke: bool | None = None, allow_real_gate: bool | None = None, low_level_backend: Any | None = None, phase58_smoke_runner: Callable[[], dict[str, Any]] | None = None, platform: str | None = None) -> dict[str, Any]:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，运行 Phase96 总合同；如果没有这段函数，测试和真实终端没有统一入口。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase96ControlledPhysicalLiveSmoke：选择隔离合同目录；如果没有这行代码，多次运行会互相污染。
    root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建合同目录；如果没有这行代码，报告写入会失败。
    requested = _phase96_request_real_smoke(real_smoke)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：判断是否请求真实路径；如果没有这行代码，默认和真实 smoke 会混在一起。
    gate_enabled = _phase96_gate_enabled(allow_real_gate)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：判断真实环境门是否打开；如果没有这行代码，真实动作缺少第二道确认。
    default_backend = Phase95RecordingSendInputBackend(physical_dispatch=True)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建默认关闭测试后端；如果没有这行代码，默认门禁没有副作用证据。
    default_sender = WindowsControlledPhysicalSendInputSender(low_level_backend=default_backend, platform=platform or "win32")  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建默认关闭 Phase95 sender；如果没有这行代码，默认关闭逻辑没有被测对象。
    default_events = default_sender.contract_events(_phase96_safe_target_window(), "click", {"x": 10, "y": 10})  # 新增代码+Phase96ControlledPhysicalLiveSmoke：构造默认关闭下的有效事件；如果没有这行代码，零事件可能只是因为输入为空。
    default_result = default_sender.send_low_level(default_events, enable_physical_dispatch=False)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：执行默认关闭路径；如果没有这行代码，default_off_zero 没有事实来源。
    unsafe_backend = Phase95RecordingSendInputBackend(physical_dispatch=True)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建危险目标测试后端；如果没有这行代码，危险目标拦截没有副作用证据。
    unsafe_sender = WindowsControlledPhysicalSendInputSender(low_level_backend=unsafe_backend, platform=platform or "win32", default_enable_physical_dispatch=True)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：创建显式启用 sender 用于危险目标负例；如果没有这行代码，危险目标测试没有压力。
    unsafe_event = {"kind": "mouse_move", "x": 1, "y": 1, "target": {"app_id": "powershell.exe", "process_name": "powershell.exe", "window_id": "hwnd:9601", "title_sha256_16": "unsafe"}}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：构造终端类危险目标；如果没有这行代码，unsafe_zero 没有样本。
    unsafe_result = unsafe_sender.send_low_level([unsafe_event], enable_physical_dispatch=True)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：执行危险目标路径；如果没有这行代码，危险拦截没有结果。
    default_zero = bool(default_result.get("decision") == "real_sendinput_disabled_by_default" and default_backend.send_count == 0 and default_result.get("low_level_event_count") == 0)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认默认关闭零事件；如果没有这行代码，安全默认值不可量化。
    unsafe_zero = bool(unsafe_result.get("decision") == "unsafe_target_rejected" and unsafe_backend.send_count == 0 and unsafe_result.get("low_level_event_count") == 0)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认危险目标零事件；如果没有这行代码，高风险拦截不可量化。
    if requested and gate_enabled:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：只有请求门和环境门同时打开才执行真实路径；如果没有这行代码，真实输入可能被单一开关误触发。
        mouse_report = _phase96_run_static_mouse_bridge(low_level_backend, platform=platform) if low_level_backend is not None else _phase96_run_real_mouse_bridge(platform=platform)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：按注入后端或真实窗口执行 mouse bridge；如果没有这行代码，测试和生产不能共享合同。
        keyboard_report = _phase96_run_keyboard_guard(phase58_smoke_runner)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：执行或注入键盘 guard；如果没有这行代码，Phase96 缺少键盘路径证据。
    elif requested and not gate_enabled:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：请求真实路径但未打开环境门时拒绝；如果没有这行代码，用户可能误以为已经真实验收。
        mouse_report = {"executed": False, "safe_window_only": True, "phase95_controlled_sender_reused": True, "phase95_physical_mouse_bridge": False, "real_desktop_touched": False, "reason": "phase96_real_gate_disabled"}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回 gate 拒绝 mouse 摘要；如果没有这行代码，失败原因不清楚。
        keyboard_report = {"executed": False, "phase58_keyboard_guard_reused": False, "safe_window_only": True, "raw_text_hidden": True, "reason": "phase96_real_gate_disabled"}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回 gate 拒绝 keyboard 摘要；如果没有这行代码，键盘路径失败原因不清楚。
    else:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：默认安全合同不跑真实路径；如果没有这行代码，普通测试可能触碰桌面。
        mouse_report = {"executed": False, "safe_window_only": True, "phase95_controlled_sender_reused": True, "phase95_physical_mouse_bridge": False, "real_desktop_touched": False, "reason": "real_smoke_not_requested"}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回未请求 mouse 摘要；如果没有这行代码，默认输出不清楚。
        keyboard_report = {"executed": False, "phase58_keyboard_guard_reused": False, "safe_window_only": True, "raw_text_hidden": True, "reason": "real_smoke_not_requested"}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回未请求 keyboard 摘要；如果没有这行代码，默认输出不清楚。
    serialized = json.dumps({"default": default_result, "unsafe": unsafe_result, "mouse": mouse_report, "keyboard": keyboard_report}, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：序列化子报告做泄露扫描；如果没有这行代码，嵌套 secret 可能漏检。
    raw_text_hidden = bool("phase96-secret-text" not in serialized and mouse_report.get("result", {}).get("raw_text_hidden", True) and keyboard_report.get("raw_text_hidden", True))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认输出不含测试原文；如果没有这行代码，隐私门禁不可量化。
    real_executed = bool(mouse_report.get("executed") and keyboard_report.get("executed"))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认真实请求路径两部分都执行；如果没有这行代码，半执行可能被误判成功。
    mouse_bridge = bool(mouse_report.get("phase95_physical_mouse_bridge"))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：提取鼠标 bridge 成功标记；如果没有这行代码，passed 条件会变得难读。
    keyboard_guard = bool(keyboard_report.get("phase58_keyboard_guard_reused"))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：提取键盘 guard 成功标记；如果没有这行代码，passed 条件会变得难读。
    real_desktop_touched = bool(mouse_report.get("real_desktop_touched"))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：汇总真实桌面副作用；如果没有这行代码，报告不能表达真实路径是否发生。
    safe_window_only = bool(mouse_report.get("safe_window_only", True) and keyboard_report.get("safe_window_only", True))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：确认两条真实路径都只碰安全窗口；如果没有这行代码，目标边界不可见。
    report_path = root / "reports" / "phase96_controlled_physical_live_smoke_report.json"  # 新增代码+Phase96ControlledPhysicalLiveSmoke：定义报告路径；如果没有这行代码，验收证据没有固定文件。
    passed = bool(default_zero and unsafe_zero and raw_text_hidden and safe_window_only and not PHASE96_UNCONTROLLED_ACTIONS_EXPANDED and ((not requested and not real_desktop_touched) or (requested and gate_enabled and real_executed and mouse_bridge and keyboard_guard and real_desktop_touched)))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：汇总通过条件；如果没有这行代码，main 无法用退出码表达失败。
    report = {"marker": PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_MARKER, "ok_token": PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_OK_TOKEN, "model": PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_MODEL, "passed": passed, "real_sendinput_live_smoke_env": PHASE96_REAL_SENDINPUT_LIVE_SMOKE_ENV, "real_sendinput_live_smoke_request_env": PHASE96_REAL_SENDINPUT_LIVE_SMOKE_REQUEST_ENV, "real_smoke_requested": requested, "real_enable_gate_required": True, "real_enable_gate_passed": gate_enabled, "real_smoke_executed": real_executed, "phase95_controlled_sender_reused": bool(mouse_report.get("phase95_controlled_sender_reused", True)), "phase95_physical_mouse_bridge": mouse_bridge, "phase58_keyboard_guard_reused": keyboard_guard, "default_off_zero_physical_events": default_zero, "unsafe_target_zero_physical_events": unsafe_zero, "safe_window_only": safe_window_only, "raw_text_hidden": raw_text_hidden, "real_desktop_touched": real_desktop_touched, "uncontrolled_actions_expanded": PHASE96_UNCONTROLLED_ACTIONS_EXPANDED, "report_path": str(report_path), "default_off_report": default_result, "unsafe_report": unsafe_result, "mouse_bridge_report": mouse_report, "keyboard_guard_report": keyboard_report}  # 新增代码+Phase96ControlledPhysicalLiveSmoke：构造完整脱敏报告；如果没有这行代码，测试和真实终端拿不到统一事实。
    atomic_write_json(report_path, report)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：原子写入报告文件；如果没有这行代码，异常中断可能留下半个 JSON。
    return report  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回合同报告；如果没有这行代码，调用方无法读取验收结果。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，run_phase96_controlled_physical_live_smoke_contract 到此结束；如果没有这个边界说明，初学者不容易看出总合同范围。

def phase96_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，把报告转成真实终端稳定 token 行；如果没有这段函数，验收器需要解析复杂 JSON。
    return f"{PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_MARKER} {PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_OK_TOKEN} default_off_zero_physical_events={_phase96_bool_token(report.get('default_off_zero_physical_events'))} unsafe_target_zero_physical_events={_phase96_bool_token(report.get('unsafe_target_zero_physical_events'))} phase95_controlled_sender_reused={_phase96_bool_token(report.get('phase95_controlled_sender_reused'))} phase95_physical_mouse_bridge={_phase96_bool_token(report.get('phase95_physical_mouse_bridge'))} phase58_keyboard_guard_reused={_phase96_bool_token(report.get('phase58_keyboard_guard_reused'))} real_enable_gate_required={_phase96_bool_token(report.get('real_enable_gate_required'))} real_smoke_executed={_phase96_bool_token(report.get('real_smoke_executed'))} safe_window_only={_phase96_bool_token(report.get('safe_window_only'))} raw_text_hidden={_phase96_bool_token(report.get('raw_text_hidden'))} real_desktop_touched={_phase96_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase96_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase96ControlledPhysicalLiveSmoke：返回固定顺序 token；如果没有这行代码，真实终端验收容易因输出漂移失败。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，phase96_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。

def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段开始，提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase96 合同。
    _ = argv  # 新增代码+Phase96ControlledPhysicalLiveSmoke：保留 argv 扩展位；如果没有这行代码，读者可能误以为参数被遗漏。
    report = run_phase96_controlled_physical_live_smoke_contract()  # 新增代码+Phase96ControlledPhysicalLiveSmoke：按环境门运行合同；如果没有这行代码，CLI 不会产生验收事实。
    print(phase96_cli_line(report))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：打印稳定 token 行；如果没有这行代码，验收脚本无法快速匹配成功条件。
    print(json.dumps({"report_path": report.get("report_path"), "passed": report.get("passed"), "real_smoke_executed": report.get("real_smoke_executed")}, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase96ControlledPhysicalLiveSmoke：打印短 JSON 方便定位证据；如果没有这行代码，失败时不容易找到报告文件。
    print(PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_MARKER)  # 新增代码+Phase96ControlledPhysicalLiveSmoke：单独打印 ready marker；如果没有这行代码，人工观察终端时容易漏标识。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase96ControlledPhysicalLiveSmoke：按合同结果返回退出码；如果没有这行代码，失败也可能被自动化当成成功。
# 新增代码+Phase96ControlledPhysicalLiveSmoke：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。

__all__ = ["DEFAULT_PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_ROOT", "PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_MARKER", "PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_MODEL", "PHASE96_CONTROLLED_PHYSICAL_LIVE_SMOKE_OK_TOKEN", "PHASE96_REAL_SENDINPUT_LIVE_SMOKE_ENV", "PHASE96_REAL_SENDINPUT_LIVE_SMOKE_REQUEST_ENV", "PHASE96_UNCONTROLLED_ACTIONS_EXPANDED", "Phase96RealSendInputLowLevelBackend", "main", "phase96_cli_line", "run_phase96_controlled_physical_live_smoke_contract"]  # 新增代码+Phase96ControlledPhysicalLiveSmoke：限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。

if __name__ == "__main__":  # 新增代码+Phase96ControlledPhysicalLiveSmoke：允许直接运行模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase96ControlledPhysicalLiveSmoke：用 main 返回码退出；如果没有这行代码，命令行状态不明确。
