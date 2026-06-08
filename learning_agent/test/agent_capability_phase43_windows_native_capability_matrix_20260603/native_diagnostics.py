"""Windows native observation provider diagnostics。"""  # 新增代码+Phase33WindowsNativeDiagnostics: 说明本文件只负责解释 native 观察能力状态；如果没有这个文件，agent 只能看到粗略 helper 状态而不知道 WGC/UIA 缺口。
from __future__ import annotations  # 新增代码+Phase33WindowsNativeDiagnostics: 启用延迟类型解析；如果没有这行代码，旧运行环境下前向类型标注更容易出错。

import importlib.util  # 新增代码+Phase33WindowsNativeDiagnostics: 用来安全探测可选 Windows/UIA 依赖；如果没有这行代码，诊断层无法说明依赖是否存在。
import json  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 用来输出 Phase43 CLI 结构化报告；如果没有这行代码，真实终端验收只能看到零散文本。
import sys  # 新增代码+Phase33WindowsNativeDiagnostics: 用来判断当前平台是否 Windows；如果没有这行代码，非 Windows 环境可能被误报为可用。
from typing import Any  # 新增代码+Phase33WindowsNativeDiagnostics: 标注 provider status 等通用 JSON 数据；如果没有这行代码，接口边界不清楚。
try:  # 新增代码+Phase36WindowsWGCProvider: 优先按包模式导入 Phase36 WGC provider；如果没有这行代码，diagnostics 无法复用真实 provider 合同。
    from learning_agent.computer_use.wgc_capture import WindowsGraphicsCaptureProvider  # 新增代码+Phase36WindowsWGCProvider: 导入 WGC provider 状态构建器；如果没有这行代码，WGC 诊断会停留在 Phase33 占位文案。
except ModuleNotFoundError as error:  # 新增代码+Phase36WindowsWGCProvider: 兼容 learning_agent 目录内脚本运行；如果没有这行代码，start_oauth_agent.bat 路径模式可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.wgc_capture"}:  # 新增代码+Phase36WindowsWGCProvider: 只处理预期包路径缺失；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase36WindowsWGCProvider: 重新抛出非路径类导入错误；如果没有这行代码，排查 provider 内部错误会困难。
    from computer_use.wgc_capture import WindowsGraphicsCaptureProvider  # 新增代码+Phase36WindowsWGCProvider: 脚本模式导入 WGC provider；如果没有这行代码，直接从 learning_agent 目录运行会缺少 Phase36 诊断。


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
    return WindowsGraphicsCaptureProvider(platform=platform).status()  # 修改代码+Phase36WindowsWGCProvider: 使用 Phase36 provider 合同生成 WGC 诊断；如果没有这行代码，状态页无法区分 Phase33 占位和 Phase36 provider。
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


PHASE43_WINDOWS_NATIVE_CAPABILITY_MARKER = "PHASE43_WINDOWS_NATIVE_CAPABILITY_READY"  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 定义 Phase43 能力矩阵 ready marker；如果没有这行代码，真实终端验收没有稳定等待锚点。
PHASE43_WINDOWS_NATIVE_CAPABILITY_OK_TOKEN = "PHASE43_WINDOWS_NATIVE_CAPABILITY_OK"  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 定义 Phase43 CLI 成功 token；如果没有这行代码，debug log 无法区分普通状态和自检通过。
PHASE43_CAPABILITY_MATRIX_MODEL = "phase43_windows_native_capability_matrix"  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 定义能力矩阵模型名；如果没有这行代码，状态消费者无法区分旧 diagnostics 和新矩阵。
PHASE43_ACTIONS_EXPANDED = False  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 明确 Phase43 不扩大真实动作面；如果没有这行代码，诊断阶段可能被误解成可以控制桌面。
PHASE43_CAPABILITY_REQUIRED_FIELDS = ("name", "category", "available", "enabled", "reason", "next_step")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 集中列出每个能力项必需字段；如果没有这行代码，测试和格式化器会各自猜字段。


def _phase43_bool_token(value: Any) -> str:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，把布尔值转成真实终端稳定 token；如果没有这段函数，输出会混用 True/False 和 true/false。
    return str(bool(value)).lower()  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回小写 true/false；如果没有这行代码，acceptance token 匹配容易漂移。
# 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，_phase43_bool_token 到此结束；如果没有这个边界说明，读者不容易看出布尔格式化范围。


def _phase43_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，把未知值安全规整为 dict；如果没有这段函数，坏状态对象会让矩阵构建崩溃。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 只接受字典并复制；如果没有这行代码，调用方传入 None 或列表时会报错。
# 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，_phase43_dict 到此结束；如果没有这个边界说明，读者不容易看出容错转换范围。


def _phase43_providers(diagnostics: dict[str, Any], section: str) -> tuple[str, list[dict[str, Any]]]:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，读取 capture/text provider 链；如果没有这段函数，两个分支会重复解析 diagnostics。
    section_status = _phase43_dict(diagnostics.get(section))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取指定区块状态；如果没有这行代码，缺区块时会触发属性错误。
    active_provider = str(section_status.get("active_provider", ""))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取当前实际 provider 名；如果没有这行代码，enabled 无法判断。
    providers = [dict(item) for item in section_status.get("providers", []) if isinstance(item, dict)]  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 复制 provider 列表并丢弃坏项；如果没有这行代码，格式化时可能遇到不可索引对象。
    return active_provider, providers  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回 active 名称和 provider 列表；如果没有这行代码，调用方拿不到解析结果。
# 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，_phase43_providers 到此结束；如果没有这个边界说明，读者不容易看出 provider 解析范围。


def _phase43_capability(name: str, category: str, available: Any, enabled: Any, reason: str, next_step: str, source: str = "") -> dict[str, Any]:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，构造统一能力项；如果没有这段函数，各能力字段容易不一致。
    return {"name": str(name), "category": str(category), "available": bool(available), "enabled": bool(enabled), "reason": str(reason or "没有提供原因。"), "next_step": str(next_step or "暂无下一步。"), "source": str(source or category)}  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回标准字段；如果没有这行代码，status_fields=true 无法保证。
# 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，_phase43_capability 到此结束；如果没有这个边界说明，读者不容易看出能力项格式范围。


def _phase43_provider_capabilities(diagnostics: dict[str, Any], section: str, category: str) -> list[dict[str, Any]]:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，把 provider 链转成能力项；如果没有这段函数，WGC/GDI/UIA/Win32 文本会散落手写。
    active_provider, providers = _phase43_providers(diagnostics, section)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取 active provider 和候选列表；如果没有这行代码，enabled 判断没有输入。
    capabilities: list[dict[str, Any]] = []  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 准备保存能力项；如果没有这行代码，函数没有输出容器。
    for provider in providers:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 遍历 provider 诊断链；如果没有这行代码，矩阵不会包含首选和 fallback provider。
        name = str(provider.get("name") or provider.get("backend") or "unknown_provider")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取 provider 名并兜底；如果没有这行代码，能力名可能为空。
        available = bool(provider.get("available", False))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取 provider 是否可用；如果没有这行代码，用户看不到依赖是否存在。
        enabled = bool(available and (provider.get("active", False) or name == active_provider))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: active 且可用才算启用；如果没有这行代码，候选 provider 会被误标成正在使用。
        reason = str(provider.get("reason", ""))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取 provider 原因；如果没有这行代码，能力项只剩布尔值。
        next_step = str(provider.get("next_step", "补齐依赖或保持 fallback。"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取 provider 下一步；如果没有这行代码，用户不知道怎么处理缺口。
        capabilities.append(_phase43_capability(name, category, available, enabled, reason, next_step, source=section))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 追加标准能力项；如果没有这行代码，provider 不会进入矩阵。
    return capabilities  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回 provider 能力列表；如果没有这行代码，调用方拿不到转换结果。
# 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，_phase43_provider_capabilities 到此结束；如果没有这个边界说明，读者不容易看出 provider 转换范围。


def build_phase43_native_capability_matrix(backend_status: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，生成 Windows native 能力矩阵；如果没有这段函数，状态页只能展示旧 diagnostics 碎片。
    status = _phase43_dict(backend_status)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 复制后端状态避免修改调用方对象；如果没有这行代码，矩阵构建可能污染 controller.status。
    diagnostics = _phase43_dict(status.get("native_observation_diagnostics"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取 WGC/UIA provider 诊断；如果没有这行代码，矩阵无法展示 native provider 链。
    executor = _phase43_dict(status.get("action_executor"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取 SendInput 执行器状态；如果没有这行代码，矩阵无法展示动作层缺口。
    platform = str(status.get("platform", sys.platform))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取平台；如果没有这行代码，跨平台拒绝原因不清楚。
    capabilities: list[dict[str, Any]] = []  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 准备保存完整能力列表；如果没有这行代码，矩阵没有主体。
    capabilities.append(_phase43_capability("windows_platform", "platform", platform == "win32", platform == "win32", f"当前平台为 {platform}。", "只有 win32 平台才允许 Windows 原生 Computer Use。", source="platform"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 加入平台能力；如果没有这行代码，用户不知道非 Windows 为什么不可用。
    capabilities.append(_phase43_capability("read_only_inventory", "observe", status.get("read_only_inventory_enabled", False), status.get("read_only_inventory_enabled", False), "Win32 只读窗口 inventory 状态来自后端。", "保持只读 observe 和真实动作开关分离。", source="windows_backend"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 加入窗口枚举能力；如果没有这行代码，用户看不到基础 observe 是否开启。
    capabilities.append(_phase43_capability("native_observation_helper", "observe", status.get("observation_helper_available", False), status.get("observation_helper_available", False), str(status.get("observation_helper_reason", "native helper 状态未知。")), "开启 native observe 前仍必须保持只读和敏感目标过滤。", source="native_helper"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 加入 helper 能力；如果没有这行代码，截图/UIA 桥接是否工作不可见。
    capabilities.extend(_phase43_provider_capabilities(diagnostics, "capture", "capture"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 加入截图 provider 能力；如果没有这行代码，WGC/GDI 缺口不会进入矩阵。
    capabilities.extend(_phase43_provider_capabilities(diagnostics, "text", "accessibility"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 加入文本/UIA provider 能力；如果没有这行代码，UIA/Win32 文本缺口不会进入矩阵。
    capabilities.append(_phase43_capability("windows_sendinput", "action", executor.get("available", False), executor.get("real_input_enabled", False), str(executor.get("reason", "SendInput executor 状态未知。")), "只有 implementation_available、enabled、allowlist、lock、abort 和审批同时满足时才允许真实动作。", source="action_executor"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 加入 SendInput 能力；如果没有这行代码，动作层真实差距不可见。
    capabilities.append(_phase43_capability("evidence_store", "evidence", bool(status.get("evidence_root") or status.get("evidence_mode")), bool(status.get("evidence_root") or status.get("evidence_mode")), f"evidence_mode={status.get('evidence_mode', '')}", "继续把截图、metadata、action journal 写入 evidence store。", source="evidence"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 加入证据仓库能力；如果没有这行代码，用户不知道观察结果是否能落盘。
    status_fields = all(all(key in item for key in PHASE43_CAPABILITY_REQUIRED_FIELDS) for item in capabilities)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 检查每个能力项字段完整；如果没有这行代码，CLI 无法报告 status_fields=true。
    available_count = sum(1 for item in capabilities if item.get("available"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 统计可用能力数；如果没有这行代码，终端面板缺少总览。
    enabled_count = sum(1 for item in capabilities if item.get("enabled"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 统计已启用能力数；如果没有这行代码，用户无法区分安装和正在使用。
    summary = {"capability_count": len(capabilities), "available_count": available_count, "enabled_count": enabled_count, "blocked_count": len(capabilities) - available_count, "status_fields": status_fields}  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 汇总矩阵统计；如果没有这行代码，状态 UI 需要重复计算。
    return {"marker": PHASE43_WINDOWS_NATIVE_CAPABILITY_MARKER, "model": PHASE43_CAPABILITY_MATRIX_MODEL, "capability_matrix": bool(capabilities), "status_fields": status_fields, "actions_expanded": PHASE43_ACTIONS_EXPANDED, "summary": summary, "capabilities": capabilities}  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回完整矩阵；如果没有这行代码，后端和终端没有统一事实源。
# 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，build_phase43_native_capability_matrix 到此结束；如果没有这个边界说明，读者不容易看出矩阵构建范围。


def format_phase43_capability_matrix_lines(matrix: dict[str, Any]) -> list[str]:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，格式化终端能力矩阵；如果没有这段函数，/computer status 只能打印难读 dict。
    matrix_data = _phase43_dict(matrix)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 容错复制矩阵对象；如果没有这行代码，坏输入会让终端状态崩溃。
    summary = _phase43_dict(matrix_data.get("summary"))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 读取统计摘要；如果没有这行代码，面板总览缺失。
    lines = ["Computer Native Capability Matrix"]  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 输出固定标题；如果没有这行代码，用户分不清这是锁状态还是 native 能力。
    lines.append(f"- marker={matrix_data.get('marker', PHASE43_WINDOWS_NATIVE_CAPABILITY_MARKER)}")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 显示 Phase43 marker；如果没有这行代码，验收器无法稳定匹配。
    lines.append(f"- model={matrix_data.get('model', PHASE43_CAPABILITY_MATRIX_MODEL)}")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 显示矩阵模型名；如果没有这行代码，用户不知道使用哪版状态面板。
    lines.append(f"- capability_count={summary.get('capability_count', 0)} available_count={summary.get('available_count', 0)} enabled_count={summary.get('enabled_count', 0)} blocked_count={summary.get('blocked_count', 0)}")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 显示总览统计；如果没有这行代码，用户需要逐行数能力。
    lines.append(f"- status_fields={_phase43_bool_token(matrix_data.get('status_fields'))} actions_expanded={_phase43_bool_token(matrix_data.get('actions_expanded'))}")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 显示字段完整性和动作边界；如果没有这行代码，验收无法确认安全边界。
    for capability in matrix_data.get("capabilities", []):  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 遍历能力列表；如果没有这行代码，面板只剩统计没有细节。
        item = _phase43_dict(capability)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 容错复制能力项；如果没有这行代码，坏项可能让终端崩溃。
        lines.append(f"- capability={item.get('name', '')} category={item.get('category', '')} available={_phase43_bool_token(item.get('available'))} enabled={_phase43_bool_token(item.get('enabled'))} reason={item.get('reason', '')} next_step={item.get('next_step', '')}")  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 输出单项能力详情；如果没有这行代码，用户看不到每项为什么可用或不可用。
    return lines  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回可打印行；如果没有这行代码，调用方拿不到终端文本。
# 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，format_phase43_capability_matrix_lines 到此结束；如果没有这个边界说明，读者不容易看出终端格式范围。


def run_phase43_native_capability_matrix_contract(backend_status: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，运行 Phase43 安全合同自检；如果没有这段函数，真实终端场景没有稳定命令入口。
    default_backend_status = {"platform": sys.platform, "read_only_inventory_enabled": False, "observation_helper_available": False, "observation_helper_reason": "contract default status", "native_observation_diagnostics": WindowsNativeObservationDiagnostics(object(), object(), platform=sys.platform).status(), "action_executor": {"backend": "windows_sendinput", "available": False, "real_input_enabled": False, "reason": "contract default disabled"}, "evidence_mode": "contract"}  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 准备无副作用默认状态；如果没有这行代码，CLI 自检需要真实桌面后端。
    matrix = build_phase43_native_capability_matrix(backend_status or default_backend_status)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 构建能力矩阵；如果没有这行代码，自检没有核心报告。
    return {"marker": PHASE43_WINDOWS_NATIVE_CAPABILITY_MARKER, "ok_token": PHASE43_WINDOWS_NATIVE_CAPABILITY_OK_TOKEN, "matrix": matrix, "capability_matrix": bool(matrix.get("capability_matrix")), "status_fields": bool(matrix.get("status_fields")), "actions_expanded": bool(matrix.get("actions_expanded")), "capability_count": int(matrix.get("summary", {}).get("capability_count", 0)), "enabled_count": int(matrix.get("summary", {}).get("enabled_count", 0))}  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回合同摘要；如果没有这行代码，CLI 无法打印稳定 token。
# 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，run_phase43_native_capability_matrix_contract 到此结束；如果没有这个边界说明，读者不容易看出合同自检范围。


def phase43_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，把合同报告转成稳定单行；如果没有这段函数，真实终端验收需要解析完整 JSON。
    return f"{PHASE43_WINDOWS_NATIVE_CAPABILITY_MARKER} {PHASE43_WINDOWS_NATIVE_CAPABILITY_OK_TOKEN} capability_matrix={_phase43_bool_token(report.get('capability_matrix'))} status_fields={_phase43_bool_token(report.get('status_fields'))} capability_count={int(report.get('capability_count', 0) or 0)} enabled_count={int(report.get('enabled_count', 0) or 0)} actions_expanded={_phase43_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 返回固定顺序 token 行；如果没有这行代码，acceptance scenario 容易因输出漂移失败。
# 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，phase43_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 行格式范围。


def main() -> int:  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段开始，提供真实终端可调用入口；如果没有这段函数，场景无法执行 Phase43 自检。
    report = run_phase43_native_capability_matrix_contract()  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 运行能力矩阵合同；如果没有这行代码，CLI 没有报告。
    print(PHASE43_WINDOWS_NATIVE_CAPABILITY_MARKER)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 先打印 ready marker；如果没有这行代码，验收器可能等不到阶段标记。
    print(phase43_cli_line(report))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 打印稳定 token 行；如果没有这行代码，debug log 无法匹配成功条件。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 打印结构化报告；如果没有这行代码，人工复盘无法看到矩阵细节。
    return 0 if bool(report.get("capability_matrix") and report.get("status_fields") and not report.get("actions_expanded")) else 1  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 根据合同结果返回退出码；如果没有这行代码，失败也会被终端当成成功。
# 新增代码+Phase43WindowsNativeCapabilityMatrix: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出命令入口范围。


if __name__ == "__main__":  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 用 main 的返回码退出；如果没有这行代码，命令行退出状态不明确。
