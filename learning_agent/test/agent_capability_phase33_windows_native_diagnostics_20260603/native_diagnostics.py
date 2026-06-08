"""Windows native observation provider diagnostics。"""  # 新增代码+Phase33WindowsNativeDiagnostics: 说明本文件只负责解释 native 观察能力状态；如果没有这个文件，agent 只能看到粗略 helper 状态而不知道 WGC/UIA 缺口。
from __future__ import annotations  # 新增代码+Phase33WindowsNativeDiagnostics: 启用延迟类型解析；如果没有这行代码，旧运行环境下前向类型标注更容易出错。

import importlib.util  # 新增代码+Phase33WindowsNativeDiagnostics: 用来安全探测可选 Windows/UIA 依赖；如果没有这行代码，诊断层无法说明依赖是否存在。
import sys  # 新增代码+Phase33WindowsNativeDiagnostics: 用来判断当前平台是否 Windows；如果没有这行代码，非 Windows 环境可能被误报为可用。
from typing import Any  # 新增代码+Phase33WindowsNativeDiagnostics: 标注 provider status 等通用 JSON 数据；如果没有这行代码，接口边界不清楚。


def _module_available(module_name: str) -> bool:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，安全判断可选模块是否存在；如果没有这段函数，依赖探测异常可能拖垮 status。
    try:  # 新增代码+Phase33WindowsNativeDiagnostics: 捕获 find_spec 过程中可能出现的导入异常；如果没有这行代码，缺少父模块时诊断会崩溃。
        return importlib.util.find_spec(module_name) is not None  # 新增代码+Phase33WindowsNativeDiagnostics: 返回模块是否可发现；如果没有这行代码，诊断层不知道依赖是否安装。
    except (ImportError, ModuleNotFoundError, ValueError):  # 新增代码+Phase33WindowsNativeDiagnostics: 捕获缺少依赖或模块名异常；如果没有这行代码，可选依赖缺失会变成硬错误。
        return False  # 新增代码+Phase33WindowsNativeDiagnostics: 依赖不可安全发现时返回 False；如果没有这行代码，用户会看到异常而不是可读诊断。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，_module_available 到此结束；如果没有这个边界说明，读者不容易看出依赖探测范围。


def _safe_provider_status(provider: Any) -> dict[str, Any]:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，安全读取 provider.status；如果没有这段函数，状态读取逻辑会在多个地方重复。
    if hasattr(provider, "status"):  # 新增代码+Phase33WindowsNativeDiagnostics: 检查 provider 是否提供 status 方法；如果没有这行代码，普通对象会触发 AttributeError。
        status = provider.status()  # 新增代码+Phase33WindowsNativeDiagnostics: 调用 provider 自身状态；如果没有这行代码，active provider 的真实名称和原因无法进入诊断。
        return dict(status) if isinstance(status, dict) else {}  # 新增代码+Phase33WindowsNativeDiagnostics: 只接受 dict 状态；如果没有这行代码，异常返回值可能污染诊断结构。
    return {}  # 新增代码+Phase33WindowsNativeDiagnostics: 没有 status 时返回空状态；如果没有这行代码，调用方需要自己兜底。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，_safe_provider_status 到此结束；如果没有这个边界说明，读者不容易看出状态读取范围。


def _provider_name(status: dict[str, Any], fallback: str) -> str:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，统一提取 provider 名称；如果没有这段函数，backend/name 字段会到处手写。
    return str(status.get("backend") or status.get("name") or fallback)  # 新增代码+Phase33WindowsNativeDiagnostics: 优先使用 backend/name 并兜底；如果没有这行代码，active provider 名称可能为空。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，_provider_name 到此结束；如果没有这个边界说明，读者不容易看出名称提取范围。


def _append_unique_provider(providers: list[dict[str, Any]], provider: dict[str, Any]) -> None:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，按 name 去重追加 provider；如果没有这段函数，fake provider 与 fallback 同名时会重复显示。
    names = {str(item.get("name", "")) for item in providers}  # 新增代码+Phase33WindowsNativeDiagnostics: 收集已有 provider 名称；如果没有这行代码，去重无法判断。
    if str(provider.get("name", "")) not in names:  # 新增代码+Phase33WindowsNativeDiagnostics: 只有新名称才追加；如果没有这行代码，状态列表可能出现重复项。
        providers.append(provider)  # 新增代码+Phase33WindowsNativeDiagnostics: 追加唯一 provider；如果没有这行代码，active provider 可能不会进入诊断链。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，_append_unique_provider 到此结束；如果没有这个边界说明，读者不容易看出去重范围。


def _graphics_capture_probe(platform: str) -> dict[str, Any]:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，生成 Windows.Graphics.Capture 诊断项；如果没有这段函数，agent 不知道首选截图能力缺口。
    dependency_available = platform == "win32" and (_module_available("winrt.windows.graphics.capture") or _module_available("winsdk.windows.graphics.capture"))  # 新增代码+Phase33WindowsNativeDiagnostics: 探测可能的 WGC Python 绑定；如果没有这行代码，诊断无法说明依赖是否具备。
    reason = "Windows.Graphics.Capture Python 绑定可发现，但 Phase33 仍未把它设为默认截图执行器。" if dependency_available else "未发现可用 Windows.Graphics.Capture Python 绑定，当前仍依赖 GDI fallback。"  # 新增代码+Phase33WindowsNativeDiagnostics: 生成 WGC 可读原因；如果没有这行代码，用户不知道为什么没有 WGC。
    return {"name": "windows_graphics_capture", "role": "capture", "preferred": True, "active": False, "available": dependency_available, "priority": 10, "dependency": "winrt 或 winsdk Windows.Graphics.Capture 绑定", "reason": reason, "next_step": "后续阶段接入 WGC provider 后，可在遮挡窗口和高 DPI 场景获得更可靠截图。"}  # 新增代码+Phase33WindowsNativeDiagnostics: 返回 WGC 诊断项；如果没有这行代码，provider 链缺少首选截图能力说明。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，_graphics_capture_probe 到此结束；如果没有这个边界说明，读者不容易看出 WGC 探测范围。


def _uiautomation_probe(platform: str) -> dict[str, Any]:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，生成 UIAutomationClient 诊断项；如果没有这段函数，agent 不知道完整控件树读取缺口。
    dependency_available = platform == "win32" and (_module_available("uiautomation") or _module_available("comtypes"))  # 新增代码+Phase33WindowsNativeDiagnostics: 探测常见 UIA Python 依赖；如果没有这行代码，诊断无法说明 UIA 环境是否具备。
    reason = "UIAutomation 相关 Python 依赖可发现，但 Phase33 仍未把它设为默认文本执行器。" if dependency_available else "未发现可用 UIAutomation Python 依赖，当前仍依赖 Win32 标题/子控件文本 fallback。"  # 新增代码+Phase33WindowsNativeDiagnostics: 生成 UIA 可读原因；如果没有这行代码，用户不知道为什么没有控件树。
    return {"name": "uiautomation_client", "role": "text", "preferred": True, "active": False, "available": dependency_available, "priority": 10, "dependency": "uiautomation 或 comtypes", "reason": reason, "next_step": "后续阶段接入 UIAutomationClient provider 后，可读取更完整控件树、焦点控件和文档文本。"}  # 新增代码+Phase33WindowsNativeDiagnostics: 返回 UIA 诊断项；如果没有这行代码，provider 链缺少首选文本能力说明。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，_uiautomation_probe 到此结束；如果没有这个边界说明，读者不容易看出 UIA 探测范围。


def _fallback_provider(name: str, role: str, reason: str, priority: int) -> dict[str, Any]:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，生成内置 fallback provider 诊断项；如果没有这段函数，GDI/Win32 fallback 说明会散落重复。
    return {"name": name, "role": role, "preferred": False, "active": False, "available": True, "priority": priority, "dependency": "Windows Win32 API", "reason": reason, "next_step": "作为安全 fallback 保留；当首选 provider 接入后仍用于降级。"}  # 新增代码+Phase33WindowsNativeDiagnostics: 返回 fallback 诊断项；如果没有这行代码，用户看不到当前可工作的保底能力。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，_fallback_provider 到此结束；如果没有这个边界说明，读者不容易看出 fallback 构造范围。


def _active_provider(status: dict[str, Any], role: str, fallback: str, priority: int) -> dict[str, Any]:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，把当前 provider.status 转成诊断项；如果没有这段函数，active provider 无法统一显示。
    name = _provider_name(status, fallback)  # 新增代码+Phase33WindowsNativeDiagnostics: 提取 provider 名称；如果没有这行代码，active provider 字段可能为空。
    return {"name": name, "role": role, "preferred": False, "active": True, "available": bool(status.get("available", False)), "priority": priority, "dependency": str(status.get("dependency", "当前已注入 provider")), "reason": str(status.get("reason", "")), "next_step": "当前实际使用的 provider；如需更强能力，请优先补齐首选 provider。"}  # 新增代码+Phase33WindowsNativeDiagnostics: 返回 active provider 诊断项；如果没有这行代码，状态无法说明当前到底是谁在工作。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，_active_provider 到此结束；如果没有这个边界说明，读者不容易看出 active 构造范围。


class WindowsNativeObservationDiagnostics:  # 新增代码+Phase33WindowsNativeDiagnostics: 定义 Windows native 观察诊断构建器；如果没有这个类，helper.status 无法输出统一诊断结构。
    def __init__(self, capture_provider: Any, text_provider: Any, platform: str | None = None) -> None:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，保存 provider 和平台；如果没有这段函数，诊断构建器不知道要解释哪个 provider。
        self.capture_provider = capture_provider  # 新增代码+Phase33WindowsNativeDiagnostics: 保存当前截图 provider；如果没有这行代码，active capture provider 无法进入诊断。
        self.text_provider = text_provider  # 新增代码+Phase33WindowsNativeDiagnostics: 保存当前文本 provider；如果没有这行代码，active text provider 无法进入诊断。
        self.platform = platform or sys.platform  # 新增代码+Phase33WindowsNativeDiagnostics: 保存平台名称；如果没有这行代码，诊断无法区分 Windows 与非 Windows。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，WindowsNativeObservationDiagnostics.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase33WindowsNativeDiagnostics: 函数段开始，构建完整诊断状态；如果没有这段函数，状态页无法解释 native provider 缺口。
        capture_status = _safe_provider_status(self.capture_provider)  # 新增代码+Phase33WindowsNativeDiagnostics: 读取当前截图 provider 状态；如果没有这行代码，active capture provider 不能被识别。
        text_status = _safe_provider_status(self.text_provider)  # 新增代码+Phase33WindowsNativeDiagnostics: 读取当前文本 provider 状态；如果没有这行代码，active text provider 不能被识别。
        capture_providers: list[dict[str, Any]] = [_graphics_capture_probe(self.platform), _fallback_provider("win32_gdi_printwindow", "capture", "当前 Phase32/Phase33 保底截图能力，使用 PrintWindow/BitBlt，遮挡和特殊窗口可能失败。", 90)]  # 新增代码+Phase33WindowsNativeDiagnostics: 建立截图 provider 优先级链；如果没有这行代码，agent 看不到 WGC 到 GDI 的差距。
        text_providers: list[dict[str, Any]] = [_uiautomation_probe(self.platform), _fallback_provider("win32_window_text", "text", "当前 Phase32/Phase33 保底文本能力，只读取窗口标题和部分子控件文本。", 90)]  # 新增代码+Phase33WindowsNativeDiagnostics: 建立文本 provider 优先级链；如果没有这行代码，agent 看不到 UIA 到 Win32 文本的差距。
        active_capture = _active_provider(capture_status, "capture", "unknown_capture_provider", 50)  # 新增代码+Phase33WindowsNativeDiagnostics: 构造 active 截图 provider 诊断项；如果没有这行代码，fake/注入 provider 不会进入状态。
        active_text = _active_provider(text_status, "text", "unknown_text_provider", 50)  # 新增代码+Phase33WindowsNativeDiagnostics: 构造 active 文本 provider 诊断项；如果没有这行代码，fake/注入 provider 不会进入状态。
        _append_unique_provider(capture_providers, active_capture)  # 新增代码+Phase33WindowsNativeDiagnostics: 把 active 截图 provider 去重加入链路；如果没有这行代码，状态可能只显示候选而不显示实际 provider。
        _append_unique_provider(text_providers, active_text)  # 新增代码+Phase33WindowsNativeDiagnostics: 把 active 文本 provider 去重加入链路；如果没有这行代码，状态可能只显示候选而不显示实际 provider。
        return {"diagnostics_version": "phase33_windows_native_diagnostics", "platform": self.platform, "safe_observe_only": True, "real_input_actions_expanded": False, "native_observe_opt_in_env_var": "LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE", "capture": {"preferred_provider": "windows_graphics_capture", "active_provider": active_capture["name"], "providers": capture_providers}, "text": {"preferred_provider": "uiautomation_client", "active_provider": active_text["name"], "providers": text_providers}, "permission_diagnostics": {"requires_native_observe_opt_in": True, "requires_user_visible_desktop_session": True, "requires_admin": False, "wgc_user_consent_may_be_required": True}, "recommendations": ["先保持 Phase33 只读诊断边界，不扩大真实鼠标键盘动作。", "下一阶段再接入真正 Windows.Graphics.Capture provider。", "下一阶段再接入真正 UIAutomationClient provider。"]}  # 新增代码+Phase33WindowsNativeDiagnostics: 返回完整诊断 JSON；如果没有这行代码，/computer 状态无法机器读取 Phase33 缺口。
    # 新增代码+Phase33WindowsNativeDiagnostics: 函数段结束，WindowsNativeObservationDiagnostics.status 到此结束；如果没有这个边界说明，读者不容易看出诊断输出范围。
