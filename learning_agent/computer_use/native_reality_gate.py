"""Windows Computer Use Phase54 原生依赖与权限现实门禁。"""  # 新增代码+Phase54WindowsNativeRealityGate: 标明本文件负责诚实检查 Windows 原生能力前置条件；如果没有这行代码，读者不知道 native_dependency_report.json 从哪里生成。
from __future__ import annotations  # 新增代码+Phase54WindowsNativeRealityGate: 启用延迟类型解析；如果没有这行代码，旧运行路径遇到前向类型标注时更容易导入失败。

import importlib.util  # 新增代码+Phase54WindowsNativeRealityGate: 导入模块探测工具；如果没有这行代码，无法安全判断 uiautomation/comtypes/winrt 是否安装。
import json  # 新增代码+Phase54WindowsNativeRealityGate: 导入 JSON 工具用于写 native_dependency_report.json；如果没有这行代码，报告无法结构化落盘。
import shutil  # 新增代码+Phase54WindowsNativeRealityGate: 导入命令探测工具；如果没有这行代码，无法安全判断 powershell/dotnet 是否可用。
import sys  # 新增代码+Phase54WindowsNativeRealityGate: 导入平台信息；如果没有这行代码，非 Windows 环境可能被误判成可运行 Windows 原生能力。
import time  # 新增代码+Phase54WindowsNativeRealityGate: 导入时间工具生成报告时间戳；如果没有这行代码，落盘报告无法审计新旧。
from pathlib import Path  # 新增代码+Phase54WindowsNativeRealityGate: 导入 Path 处理报告路径；如果没有这行代码，Windows 路径拼接会更脆弱。
from typing import Any, Callable  # 新增代码+Phase54WindowsNativeRealityGate: 导入通用类型和可注入探针类型；如果没有这行代码，测试 seam 边界不清楚。

PHASE54_WINDOWS_NATIVE_REALITY_GATE_MARKER = "PHASE54_WINDOWS_NATIVE_REALITY_GATE_READY"  # 新增代码+Phase54WindowsNativeRealityGate: 定义 Phase54 ready marker；如果没有这行代码，真实终端验收无法稳定等待本阶段输出。
PHASE54_WINDOWS_NATIVE_REALITY_GATE_OK_TOKEN = "PHASE54_WINDOWS_NATIVE_REALITY_GATE_OK"  # 新增代码+Phase54WindowsNativeRealityGate: 定义 Phase54 OK token；如果没有这行代码，日志无法区分现实门禁通过和普通文本。
PHASE54_NATIVE_REALITY_GATE_MODEL = "phase54_windows_native_reality_gate"  # 新增代码+Phase54WindowsNativeRealityGate: 定义现实门禁模型名；如果没有这行代码，报告无法说明当前使用哪套检查规则。
PHASE54_NATIVE_DEPENDENCY_REPORT_FILENAME = "native_dependency_report.json"  # 新增代码+Phase54WindowsNativeRealityGate: 定义落盘报告文件名；如果没有这行代码，后续 phase 和用户无法用固定路径找报告。
PHASE54_EXPECTED_DEPENDENCY_COUNT = 9  # 新增代码+Phase54WindowsNativeRealityGate: 固定九类原生依赖/能力检查；如果没有这行代码，漏检也可能误通过。
PHASE54_ACTIONS_EXPANDED = False  # 新增代码+Phase54WindowsNativeRealityGate: 明确 Phase54 不扩大真实桌面动作面；如果没有这行代码，用户可能误以为依赖检查会控制电脑。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，_bool_token 把布尔值转成验收器稳定匹配的小写 token；如果没有这段函数，CLI 可能混用 True/False 和 true/false，作者意图是让真实终端断言稳定。
def _bool_token(value: Any) -> str:  # 新增代码+Phase54WindowsNativeRealityGate: 定义布尔 token helper；如果没有这行代码，多处输出会重复写转换逻辑。
    return "true" if bool(value) else "false"  # 新增代码+Phase54WindowsNativeRealityGate: 返回小写布尔文本；如果没有这行代码，场景 JSON 的 token 匹配可能失败。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，phase54_utc_timestamp 生成报告时间；如果没有这段函数，native_dependency_report.json 缺少可审计时间，作者意图是让用户知道报告是否新鲜。
def phase54_utc_timestamp() -> str:  # 新增代码+Phase54WindowsNativeRealityGate: 定义 UTC 时间戳 helper；如果没有这行代码，各处会重复拼接时间格式。
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # 新增代码+Phase54WindowsNativeRealityGate: 返回稳定 UTC 字符串；如果没有这行代码，报告时间格式会漂移。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，phase54_utc_timestamp 到此结束；如果没有这个边界说明，初学者不容易看出时间 helper 的边界。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，phase54_module_available 安全探测 Python 模块是否存在；如果没有这段函数，缺依赖会变成 ImportError，作者意图是诚实报告 missing 而不是崩溃。
def phase54_module_available(module_name: str) -> bool:  # 新增代码+Phase54WindowsNativeRealityGate: 定义模块可用性探针；如果没有这行代码，依赖检查无法被单元测试注入。
    try:  # 新增代码+Phase54WindowsNativeRealityGate: 捕获 find_spec 可能抛出的异常；如果没有这行代码，缺父包时状态查询会崩溃。
        return importlib.util.find_spec(module_name) is not None  # 新增代码+Phase54WindowsNativeRealityGate: 返回模块是否可发现；如果没有这行代码，报告不知道依赖是否安装。
    except (ImportError, ModuleNotFoundError, ValueError):  # 新增代码+Phase54WindowsNativeRealityGate: 处理可选依赖缺失或坏模块名；如果没有这行代码，探测失败无法优雅降级。
        return False  # 新增代码+Phase54WindowsNativeRealityGate: 异常时诚实返回不可用；如果没有这行代码，依赖缺失可能被误判。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，phase54_module_available 到此结束；如果没有这个边界说明，初学者不容易看出模块探测范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，phase54_command_available 安全探测命令是否存在；如果没有这段函数，PowerShell/.NET 可用性无法进入报告，作者意图是不执行安装只做存在性检查。
def phase54_command_available(command_name: str) -> bool:  # 新增代码+Phase54WindowsNativeRealityGate: 定义命令可用性探针；如果没有这行代码，测试无法注入 powershell/dotnet 状态。
    return shutil.which(command_name) is not None  # 新增代码+Phase54WindowsNativeRealityGate: 用 PATH 查找命令；如果没有这行代码，报告无法判断命令是否可用。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，phase54_command_available 到此结束；如果没有这个边界说明，初学者不容易看出命令探测范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，_ctypes_function_exists 检查 Windows DLL 函数是否可解析；如果没有这段函数，SendInput/RegisterHotKey/PrintWindow 只能靠猜，作者意图是只读探测 API 不调用动作。
def _ctypes_function_exists(library_name: str, function_name: str, platform: str) -> bool:  # 新增代码+Phase54WindowsNativeRealityGate: 定义 Win32 API 存在性探针；如果没有这行代码，API 检查无法被统一复用。
    if platform != "win32":  # 新增代码+Phase54WindowsNativeRealityGate: 非 Windows 平台直接返回不可用；如果没有这行代码，ctypes.windll 在非 Windows 会报错。
        return False  # 新增代码+Phase54WindowsNativeRealityGate: 返回不可用；如果没有这行代码，跨平台运行会误触 Windows DLL。
    try:  # 新增代码+Phase54WindowsNativeRealityGate: 捕获 DLL 或函数解析异常；如果没有这行代码，API 探测失败会让报告崩溃。
        import ctypes  # 新增代码+Phase54WindowsNativeRealityGate: 延迟导入 ctypes；如果没有这行代码，无法访问 Windows DLL。
        library = getattr(ctypes.windll, library_name)  # 新增代码+Phase54WindowsNativeRealityGate: 获取目标 DLL；如果没有这行代码，函数检查没有入口。
        getattr(library, function_name)  # 新增代码+Phase54WindowsNativeRealityGate: 尝试解析目标函数；如果没有这行代码，无法知道 API 是否存在。
        return True  # 新增代码+Phase54WindowsNativeRealityGate: 函数可解析时返回可用；如果没有这行代码，成功探测无法表达。
    except Exception:  # 新增代码+Phase54WindowsNativeRealityGate: 捕获所有 ctypes 探测异常；如果没有这行代码，系统差异会中断报告生成。
        return False  # 新增代码+Phase54WindowsNativeRealityGate: 探测失败时诚实返回不可用；如果没有这行代码，坏 API 状态可能误报。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，_ctypes_function_exists 到此结束；如果没有这个边界说明，初学者不容易看出 API 探测范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，phase54_api_available 汇总 Win32 原生 API 存在性；如果没有这段函数，报告无法覆盖截图、输入、热键和通知前置条件，作者意图是只读探测不执行动作。
def phase54_api_available(api_name: str, platform: str | None = None) -> bool:  # 新增代码+Phase54WindowsNativeRealityGate: 定义 API 可用性探针；如果没有这行代码，测试无法注入 API 状态。
    current_platform = platform or sys.platform  # 新增代码+Phase54WindowsNativeRealityGate: 读取当前平台或测试注入平台；如果没有这行代码，跨平台测试无法稳定。
    if api_name == "win32_gdi_capture_api":  # 新增代码+Phase54WindowsNativeRealityGate: 检查 GDI/PrintWindow 截图 API；如果没有这行代码，fallback 截图前置条件会漏检。
        return _ctypes_function_exists("user32", "PrintWindow", current_platform) and _ctypes_function_exists("gdi32", "BitBlt", current_platform)  # 新增代码+Phase54WindowsNativeRealityGate: 同时要求 PrintWindow 和 BitBlt；如果没有这行代码，部分截图 API 缺失会被误报。
    if api_name == "windows_sendinput_api":  # 新增代码+Phase54WindowsNativeRealityGate: 检查 SendInput API；如果没有这行代码，真实输入前置条件会漏检。
        return _ctypes_function_exists("user32", "SendInput", current_platform)  # 新增代码+Phase54WindowsNativeRealityGate: 只解析 SendInput 不发送事件；如果没有这行代码，检查会变成危险动作。
    if api_name == "global_hotkey_api":  # 新增代码+Phase54WindowsNativeRealityGate: 检查全局热键 API；如果没有这行代码，Escape/abort 热键前置条件会漏检。
        return _ctypes_function_exists("user32", "RegisterHotKey", current_platform) and _ctypes_function_exists("user32", "UnregisterHotKey", current_platform)  # 新增代码+Phase54WindowsNativeRealityGate: 要求注册和注销热键都存在；如果没有这行代码，清理边界会缺失。
    if api_name == "toast_notification_api":  # 新增代码+Phase54WindowsNativeRealityGate: 检查 toast 通知基础能力；如果没有这行代码，用户通知前置条件会漏检。
        return current_platform == "win32" and (phase54_command_available("powershell.exe") or phase54_command_available("pwsh"))  # 新增代码+Phase54WindowsNativeRealityGate: 用 PowerShell 作为通知桥存在性信号；如果没有这行代码，通知状态无法表达。
    if api_name == "windows_graphics_capture_runtime":  # 新增代码+Phase54WindowsNativeRealityGate: 检查 WGC runtime 占位信号；如果没有这行代码，WGC 绑定和 runtime 无法分开表达。
        return current_platform == "win32"  # 新增代码+Phase54WindowsNativeRealityGate: Windows 平台具备 runtime 前提，但仍需 Python 绑定和实现；如果没有这行代码，WGC 缺口无法细分。
    return False  # 新增代码+Phase54WindowsNativeRealityGate: 未知 API 返回不可用；如果没有这行代码，拼写错误可能误报可用。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，phase54_api_available 到此结束；如果没有这个边界说明，初学者不容易看出 API 探测范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，phase54_windows_build_report 生成 Windows build 摘要；如果没有这段函数，报告无法解释系统版本边界，作者意图是只读记录不改系统。
def phase54_windows_build_report(platform: str | None = None) -> dict[str, Any]:  # 新增代码+Phase54WindowsNativeRealityGate: 定义 Windows build 报告函数；如果没有这行代码，报告缺少 OS 版本事实。
    current_platform = platform or sys.platform  # 新增代码+Phase54WindowsNativeRealityGate: 读取当前平台或测试注入平台；如果没有这行代码，测试无法稳定模拟。
    if current_platform != "win32":  # 新增代码+Phase54WindowsNativeRealityGate: 非 Windows 平台只报告不支持；如果没有这行代码，getwindowsversion 在非 Windows 会不可用。
        return {"platform": current_platform, "platform_supported": False, "major": 0, "minor": 0, "build": 0, "display": current_platform, "next_step": "只在 Windows 上运行真实 OS 级 Computer Use；当前平台只能做合同自检。"}  # 新增代码+Phase54WindowsNativeRealityGate: 返回非 Windows 摘要；如果没有这行代码，跨平台报告不清楚。
    version = sys.getwindowsversion()  # 新增代码+Phase54WindowsNativeRealityGate: 读取 Windows 版本结构；如果没有这行代码，build 号无法记录。
    return {"platform": current_platform, "platform_supported": True, "major": int(version.major), "minor": int(version.minor), "build": int(version.build), "display": f"{version.major}.{version.minor}.{version.build}", "next_step": "若后续 WGC/UIA/hotkey 不可用，请优先核对 Windows 版本、权限和 Python 依赖，而不是让 fake provider 冒充真实通过。"}  # 新增代码+Phase54WindowsNativeRealityGate: 返回 Windows build 摘要；如果没有这行代码，用户看不到系统版本线索。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，phase54_windows_build_report 到此结束；如果没有这个边界说明，初学者不容易看出 OS build 范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，_dependency_item 统一构造依赖项；如果没有这段函数，九个依赖项字段会散落重复，作者意图是保证 status/next_step/install_attempted 字段一致。
def _dependency_item(name: str, category: str, installed: bool, platform_supported: bool, enabled: bool, required_for: str, next_step: str) -> dict[str, Any]:  # 新增代码+Phase54WindowsNativeRealityGate: 定义依赖项构造函数；如果没有这行代码，字段完整性难以保证。
    available = bool(installed and platform_supported)  # 新增代码+Phase54WindowsNativeRealityGate: 只有安装且平台支持才算可用；如果没有这行代码，非 Windows 也可能误报依赖可用。
    status = "ready" if available else ("missing" if platform_supported else "blocked")  # 新增代码+Phase54WindowsNativeRealityGate: 生成 ready/missing/blocked 状态；如果没有这行代码，缺依赖和平台不支持无法区分。
    return {"name": name, "category": category, "installed": bool(installed), "available": available, "enabled": bool(enabled and available), "status": status, "blocked": status != "ready", "required_for": required_for, "next_step": next_step, "install_attempted": False, "system_settings_changed": False}  # 新增代码+Phase54WindowsNativeRealityGate: 返回标准依赖项；如果没有这行代码，报告无法证明没有自动安装或改设置。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，_dependency_item 到此结束；如果没有这个边界说明，初学者不容易看出依赖项构造范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，build_phase54_native_dependency_report 生成完整依赖报告；如果没有这段函数，测试、CLI 和终端 UI 没有统一事实源，作者意图是诚实列出能用和缺失项。
def build_phase54_native_dependency_report(platform: str | None = None, module_available: Callable[[str], bool] | None = None, command_available: Callable[[str], bool] | None = None, api_available: Callable[[str], bool] | None = None) -> dict[str, Any]:  # 新增代码+Phase54WindowsNativeRealityGate: 定义报告构造入口；如果没有这行代码，后续只能在 main 里硬写探测逻辑。
    current_platform = platform or sys.platform  # 新增代码+Phase54WindowsNativeRealityGate: 读取当前平台或测试注入平台；如果没有这行代码，报告无法跨平台解释。
    platform_supported = current_platform == "win32"  # 新增代码+Phase54WindowsNativeRealityGate: 判断是否 Windows；如果没有这行代码，依赖状态无法区分平台阻断。
    module_checker = module_available or phase54_module_available  # 新增代码+Phase54WindowsNativeRealityGate: 选择真实或注入模块探针；如果没有这行代码，单元测试无法稳定模拟依赖。
    command_checker = command_available or phase54_command_available  # 新增代码+Phase54WindowsNativeRealityGate: 选择真实或注入命令探针；如果没有这行代码，PowerShell/.NET 测试会依赖机器状态。
    api_checker = api_available or (lambda name: phase54_api_available(name, current_platform))  # 新增代码+Phase54WindowsNativeRealityGate: 选择真实或注入 API 探针；如果没有这行代码，Win32 API 测试会触碰真实系统状态。
    wgc_binding_installed = any(module_checker(name) for name in ("winrt.windows.graphics.capture", "winsdk.windows.graphics.capture"))  # 新增代码+Phase54WindowsNativeRealityGate: 检查可接受 WGC Python 绑定；如果没有这行代码，真实截图首选依赖会漏检。
    powershell_installed = command_checker("powershell.exe") or command_checker("pwsh")  # 新增代码+Phase54WindowsNativeRealityGate: 检查 PowerShell 是否可执行；如果没有这行代码，通知和脚本桥依赖会漏检。
    dotnet_installed = command_checker("dotnet") or powershell_installed  # 新增代码+Phase54WindowsNativeRealityGate: 检查 .NET runtime 信号；如果没有这行代码，PowerShell/.NET 能力无法表达。
    dependencies = [  # 新增代码+Phase54WindowsNativeRealityGate: 依赖列表开始；如果没有这段列表，报告没有主体。
        _dependency_item("uiautomation", "uia", module_checker("uiautomation"), platform_supported, True, "real_uia_tree", "安装并验证 uiautomation 后，Phase57 才能声明真实 UIA 控件树。"),  # 新增代码+Phase54WindowsNativeRealityGate: 加入 uiautomation 依赖；如果没有这行代码，UIA 主依赖会漏检。
        _dependency_item("comtypes", "uia", module_checker("comtypes"), platform_supported, True, "uia_com_bridge", "安装并验证 comtypes 后，UIAutomation COM fallback 才有基础。"),  # 新增代码+Phase54WindowsNativeRealityGate: 加入 comtypes 依赖；如果没有这行代码，UIA COM fallback 会漏检。
        _dependency_item("windows_graphics_capture_binding", "capture", wgc_binding_installed and api_checker("windows_graphics_capture_runtime"), platform_supported, True, "real_wgc_capture", "安装 winrt 或 winsdk WGC 绑定并接入真实 capture_impl 后，Phase56 才能声明 WGC 可用。"),  # 新增代码+Phase54WindowsNativeRealityGate: 加入 WGC 绑定依赖；如果没有这行代码，真实截图首选 provider 会漏检。
        _dependency_item("win32_gdi_capture_api", "capture", api_checker("win32_gdi_capture_api"), platform_supported, True, "gdi_fallback_capture", "保留 GDI fallback，但它不能替代 WGC 的首选能力和像素守卫。"),  # 新增代码+Phase54WindowsNativeRealityGate: 加入 GDI fallback API；如果没有这行代码，截图保底能力不可见。
        _dependency_item("windows_sendinput_api", "input", api_checker("windows_sendinput_api"), platform_supported, False, "real_sendinput_actions", "即使 SendInput API 存在，也必须等待 opt-in、allowlist、target guard 和审批同时通过。"),  # 新增代码+Phase54WindowsNativeRealityGate: 加入 SendInput API；如果没有这行代码，真实输入前置条件不可见。
        _dependency_item("powershell", "runtime", powershell_installed, platform_supported, True, "helper_scripts_and_notifications", "确保 powershell.exe 或 pwsh 可用；本阶段不会修改执行策略或安装模块。"),  # 新增代码+Phase54WindowsNativeRealityGate: 加入 PowerShell 依赖；如果没有这行代码，helper 脚本和通知桥前置条件会漏检。
        _dependency_item("dotnet_runtime", "runtime", dotnet_installed, platform_supported, True, "native_helper_v2", "确保 .NET runtime 或 PowerShell 承载能力可用；本阶段不会安装 .NET。"),  # 新增代码+Phase54WindowsNativeRealityGate: 加入 .NET runtime 信号；如果没有这行代码，native helper v2 前置条件会漏检。
        _dependency_item("global_hotkey_api", "abort", api_checker("global_hotkey_api"), platform_supported, False, "global_abort_hotkey", "Phase61 才能注册/注销热键；本阶段只检查 API 是否存在。"),  # 新增代码+Phase54WindowsNativeRealityGate: 加入全局热键 API；如果没有这行代码，Escape/abort 前置条件会漏检。
        _dependency_item("toast_notification_api", "notification", api_checker("toast_notification_api") or powershell_installed, platform_supported, False, "desktop_notifications", "Phase61 才能接入 toast 或通知桥；本阶段只报告能力，不发通知。"),  # 新增代码+Phase54WindowsNativeRealityGate: 加入通知能力；如果没有这行代码，用户可见通知前置条件会漏检。
    ]  # 新增代码+Phase54WindowsNativeRealityGate: 依赖列表结束；如果没有这行代码，Python 列表无法闭合。
    windows_build = phase54_windows_build_report(current_platform)  # 新增代码+Phase54WindowsNativeRealityGate: 读取 Windows build 摘要；如果没有这行代码，系统版本线索不会进入报告。
    missing_count = sum(1 for item in dependencies if item["status"] == "missing")  # 新增代码+Phase54WindowsNativeRealityGate: 统计缺失依赖数；如果没有这行代码，CLI 无法展示缺口规模。
    blocked_count = sum(1 for item in dependencies if item["blocked"])  # 新增代码+Phase54WindowsNativeRealityGate: 统计 blocked/missing 总数；如果没有这行代码，用户无法快速判断风险。
    ready_count = sum(1 for item in dependencies if item["status"] == "ready")  # 新增代码+Phase54WindowsNativeRealityGate: 统计已具备依赖数；如果没有这行代码，报告缺少正向进度。
    real_capabilities = {"real_uia_ready": any(item["name"] == "uiautomation" and item["status"] == "ready" for item in dependencies), "wgc_binding_ready": any(item["name"] == "windows_graphics_capture_binding" and item["status"] == "ready" for item in dependencies), "gdi_fallback_ready": any(item["name"] == "win32_gdi_capture_api" and item["status"] == "ready" for item in dependencies), "sendinput_api_ready": any(item["name"] == "windows_sendinput_api" and item["status"] == "ready" for item in dependencies), "hotkey_api_ready": any(item["name"] == "global_hotkey_api" and item["status"] == "ready" for item in dependencies)}  # 新增代码+Phase54WindowsNativeRealityGate: 汇总关键真实能力前置条件；如果没有这行代码，后续 Phase56-61 需要重复扫描依赖列表。
    return {"marker": PHASE54_WINDOWS_NATIVE_REALITY_GATE_MARKER, "ok_token": PHASE54_WINDOWS_NATIVE_REALITY_GATE_OK_TOKEN, "model": PHASE54_NATIVE_REALITY_GATE_MODEL, "generated_at": phase54_utc_timestamp(), "platform": current_platform, "windows_build": windows_build, "dependencies": dependencies, "dependency_count": len(dependencies), "ready_count": ready_count, "missing_count": missing_count, "blocked_count": blocked_count, "real_capabilities": real_capabilities, "install_attempted": False, "system_settings_changed": False, "actions_expanded": PHASE54_ACTIONS_EXPANDED, "report_written": False, "report_path": "", "passed": len(dependencies) == PHASE54_EXPECTED_DEPENDENCY_COUNT and not PHASE54_ACTIONS_EXPANDED}  # 新增代码+Phase54WindowsNativeRealityGate: 返回完整报告；如果没有这行代码，调用方拿不到结构化现实门禁结果。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，build_phase54_native_dependency_report 到此结束；如果没有这个边界说明，初学者不容易看出报告构造范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，_report_path 计算 native_dependency_report.json 路径；如果没有这段函数，CLI 和 /computer 命令会把报告写到不同位置，作者意图是统一落盘约定。
def _report_path(output_root: Path | str | None = None) -> Path:  # 新增代码+Phase54WindowsNativeRealityGate: 定义报告路径 helper；如果没有这行代码，路径逻辑会散落重复。
    root = Path(output_root) if output_root is not None else Path("memory") / "computer_use"  # 新增代码+Phase54WindowsNativeRealityGate: 使用传入目录或默认 memory/computer_use；如果没有这行代码，默认报告位置不明确。
    return root / PHASE54_NATIVE_DEPENDENCY_REPORT_FILENAME  # 新增代码+Phase54WindowsNativeRealityGate: 返回固定文件名路径；如果没有这行代码，后续 phase 找不到报告。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，_report_path 到此结束；如果没有这个边界说明，初学者不容易看出报告路径范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，write_phase54_native_dependency_report 把报告安全落盘；如果没有这段函数，交付物 native_dependency_report.json 不会生成，作者意图是让终端、用户和后续 phase 共用同一文件。
def write_phase54_native_dependency_report(report: dict[str, Any], output_root: Path | str | None = None) -> dict[str, Any]:  # 新增代码+Phase54WindowsNativeRealityGate: 定义报告写入函数；如果没有这行代码，run 函数需要手写文件逻辑。
    report_path = _report_path(output_root)  # 新增代码+Phase54WindowsNativeRealityGate: 计算报告路径；如果没有这行代码，写入目标不确定。
    updated = dict(report)  # 新增代码+Phase54WindowsNativeRealityGate: 复制报告避免污染调用方输入；如果没有这行代码，失败路径可能改坏原对象。
    updated["report_path"] = str(report_path)  # 新增代码+Phase54WindowsNativeRealityGate: 写入报告路径字段；如果没有这行代码，用户不知道文件保存在哪里。
    try:  # 新增代码+Phase54WindowsNativeRealityGate: 捕获目录创建或写文件异常；如果没有这行代码，磁盘问题会直接崩溃 agent。
        report_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase54WindowsNativeRealityGate: 创建报告目录；如果没有这行代码，首次运行时写文件会失败。
        updated["report_written"] = True  # 新增代码+Phase54WindowsNativeRealityGate: 写入前先标记将要写入成功状态；如果没有这行代码，落盘内容里 report_written 会一直是 false。
        updated["passed"] = bool(updated.get("passed") and updated.get("report_written") and not updated.get("install_attempted") and not updated.get("system_settings_changed") and not updated.get("actions_expanded"))  # 新增代码+Phase54WindowsNativeRealityGate: 汇总写入后的通过条件；如果没有这行代码，报告可能忽略写文件失败或安全边界变化。
        report_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")  # 新增代码+Phase54WindowsNativeRealityGate: 写入 UTF-8 JSON 报告；如果没有这行代码，native_dependency_report.json 不会生成。
        return updated  # 新增代码+Phase54WindowsNativeRealityGate: 返回带路径和写入状态的报告；如果没有这行代码，调用方拿不到最终状态。
    except Exception as error:  # 新增代码+Phase54WindowsNativeRealityGate: 捕获写入异常；如果没有这行代码，权限或路径错误会让终端崩溃。
        updated["report_written"] = False  # 新增代码+Phase54WindowsNativeRealityGate: 写入失败时诚实标记；如果没有这行代码，失败可能伪装成成功。
        updated["write_error"] = type(error).__name__  # 新增代码+Phase54WindowsNativeRealityGate: 只记录异常类型避免泄露本地细节；如果没有这行代码，用户不知道失败类别。
        updated["passed"] = False  # 新增代码+Phase54WindowsNativeRealityGate: 写入失败时合同不通过；如果没有这行代码，缺少交付文件仍可能误过。
        return updated  # 新增代码+Phase54WindowsNativeRealityGate: 返回失败报告；如果没有这行代码，调用方拿不到错误状态。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，write_phase54_native_dependency_report 到此结束；如果没有这个边界说明，初学者不容易看出落盘范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，run_phase54_native_reality_gate_contract 执行报告构造和落盘；如果没有这段函数，测试、CLI 和真实终端没有统一入口，作者意图是诚实门禁一处运行。
def run_phase54_native_reality_gate_contract(platform: str | None = None, module_available: Callable[[str], bool] | None = None, command_available: Callable[[str], bool] | None = None, api_available: Callable[[str], bool] | None = None, output_root: Path | str | None = None, write_report: bool = True) -> dict[str, Any]:  # 新增代码+Phase54WindowsNativeRealityGate: 定义 Phase54 合同入口；如果没有这行代码，自动化和终端场景无法调用本阶段自检。
    report = build_phase54_native_dependency_report(platform=platform, module_available=module_available, command_available=command_available, api_available=api_available)  # 新增代码+Phase54WindowsNativeRealityGate: 生成依赖现实报告；如果没有这行代码，run 函数没有事实来源。
    if write_report:  # 新增代码+Phase54WindowsNativeRealityGate: 检查是否需要落盘；如果没有这行代码，测试无法关闭或控制报告写入。
        return write_phase54_native_dependency_report(report, output_root=output_root)  # 新增代码+Phase54WindowsNativeRealityGate: 写入报告并返回最终状态；如果没有这行代码，交付物不会生成。
    report["report_path"] = str(_report_path(output_root))  # 新增代码+Phase54WindowsNativeRealityGate: 即使不写文件也给出预期路径；如果没有这行代码，调用方无法知道默认位置。
    report["passed"] = bool(report.get("passed") and not report.get("install_attempted") and not report.get("system_settings_changed") and not report.get("actions_expanded"))  # 新增代码+Phase54WindowsNativeRealityGate: 汇总不落盘模式下的合同状态；如果没有这行代码，安全边界变化可能被忽略。
    return report  # 新增代码+Phase54WindowsNativeRealityGate: 返回内存报告；如果没有这行代码，调用方拿不到结果。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，run_phase54_native_reality_gate_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同入口范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，phase54_cli_line 把报告转成一行稳定 token；如果没有这段函数，真实终端场景需要解析复杂 JSON，作者意图是让最终回答可复制可验收。
def phase54_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase54WindowsNativeRealityGate: 定义 Phase54 CLI 行格式化函数；如果没有这行代码，main 无法打印固定顺序 token。
    return f"{PHASE54_WINDOWS_NATIVE_REALITY_GATE_OK_TOKEN} dependency_count={int(report.get('dependency_count', 0) or 0)} ready_count={int(report.get('ready_count', 0) or 0)} missing_count={int(report.get('missing_count', 0) or 0)} blocked_count={int(report.get('blocked_count', 0) or 0)} report_written={_bool_token(report.get('report_written'))} install_attempted={_bool_token(report.get('install_attempted'))} system_settings_changed={_bool_token(report.get('system_settings_changed'))} actions_expanded={_bool_token(report.get('actions_expanded'))} marker={PHASE54_WINDOWS_NATIVE_REALITY_GATE_MARKER}"  # 新增代码+Phase54WindowsNativeRealityGate: 返回固定顺序 token 行；如果没有这行代码，场景断言容易因为输出漂移失败。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，phase54_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 文本范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，format_phase54_native_reality_gate_lines 渲染 /computer native-gate 可读面板；如果没有这段函数，用户只能看 JSON，作者意图是让代码小白也能看懂缺哪个依赖和下一步。
def format_phase54_native_reality_gate_lines(report: dict[str, Any]) -> list[str]:  # 新增代码+Phase54WindowsNativeRealityGate: 定义终端面板渲染函数；如果没有这行代码，/computer native-gate 会缺少人类可读输出。
    lines = ["Computer Native Reality Gate"]  # 新增代码+Phase54WindowsNativeRealityGate: 输出固定标题；如果没有这行代码，用户分不清这是普通状态还是依赖门禁。
    lines.append(f"- marker={report.get('marker', PHASE54_WINDOWS_NATIVE_REALITY_GATE_MARKER)}")  # 新增代码+Phase54WindowsNativeRealityGate: 显示 ready marker；如果没有这行代码，验收器无法稳定匹配本面板。
    lines.append(f"- model={report.get('model', PHASE54_NATIVE_REALITY_GATE_MODEL)}")  # 新增代码+Phase54WindowsNativeRealityGate: 显示模型名；如果没有这行代码，用户不知道当前检查规则版本。
    lines.append(f"- {phase54_cli_line(report)}")  # 新增代码+Phase54WindowsNativeRealityGate: 直接嵌入稳定 token 行；如果没有这行代码，真实终端输出和 CLI 输出可能不一致。
    lines.append(f"- report_path={report.get('report_path', '')}")  # 新增代码+Phase54WindowsNativeRealityGate: 显示落盘报告路径；如果没有这行代码，用户找不到 native_dependency_report.json。
    build = report.get("windows_build", {}) if isinstance(report.get("windows_build"), dict) else {}  # 新增代码+Phase54WindowsNativeRealityGate: 读取 Windows build 字段；如果没有这行代码，坏报告会让面板崩溃。
    lines.append(f"- windows_build={build.get('display', '')} platform_supported={_bool_token(build.get('platform_supported'))}")  # 新增代码+Phase54WindowsNativeRealityGate: 显示系统版本摘要；如果没有这行代码，用户看不到 OS 级前置条件。
    for item in report.get("dependencies", []):  # 新增代码+Phase54WindowsNativeRealityGate: 遍历依赖项渲染摘要；如果没有这行代码，用户只能看到总数看不到缺口。
        item_data = dict(item) if isinstance(item, dict) else {}  # 新增代码+Phase54WindowsNativeRealityGate: 容错复制依赖项；如果没有这行代码，坏输入可能让状态 UI 崩溃。
        lines.append(f"- dependency={item_data.get('name', '')} category={item_data.get('category', '')} status={item_data.get('status', '')} installed={_bool_token(item_data.get('installed'))} enabled={_bool_token(item_data.get('enabled'))} next_step={item_data.get('next_step', '')}")  # 新增代码+Phase54WindowsNativeRealityGate: 输出单项状态和下一步；如果没有这行代码，用户不知道缺依赖如何补齐。
    return lines  # 新增代码+Phase54WindowsNativeRealityGate: 返回可打印行列表；如果没有这行代码，调用方拿不到终端文本。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，format_phase54_native_reality_gate_lines 到此结束；如果没有这个边界说明，初学者不容易看出面板渲染范围。


# 新增代码+Phase54WindowsNativeRealityGate: 函数段开始，main 提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase54 现实门禁，作者意图是自动化和可见终端共用同一合同。
def main() -> int:  # 新增代码+Phase54WindowsNativeRealityGate: 定义命令行入口；如果没有这行代码，python -c 只能手写调用细节。
    report = run_phase54_native_reality_gate_contract()  # 新增代码+Phase54WindowsNativeRealityGate: 运行 Phase54 合同并落盘报告；如果没有这行代码，CLI 输出没有真实依据。
    print(phase54_cli_line(report))  # 新增代码+Phase54WindowsNativeRealityGate: 打印稳定单行 token；如果没有这行代码，验收器无法快速匹配结果。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase54WindowsNativeRealityGate: 打印结构化报告便于人工复盘；如果没有这行代码，失败时不容易定位哪项不合格。
    print(PHASE54_WINDOWS_NATIVE_REALITY_GATE_MARKER)  # 新增代码+Phase54WindowsNativeRealityGate: 单独打印 ready marker；如果没有这行代码，真实终端验收可能看不到明确阶段标记。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase54WindowsNativeRealityGate: 根据合同结果返回退出码；如果没有这行代码，报告写入失败也可能被终端当成成功。
# 新增代码+Phase54WindowsNativeRealityGate: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = ["PHASE54_NATIVE_DEPENDENCY_REPORT_FILENAME", "PHASE54_NATIVE_REALITY_GATE_MODEL", "PHASE54_WINDOWS_NATIVE_REALITY_GATE_MARKER", "PHASE54_WINDOWS_NATIVE_REALITY_GATE_OK_TOKEN", "build_phase54_native_dependency_report", "format_phase54_native_reality_gate_lines", "main", "phase54_api_available", "phase54_cli_line", "phase54_command_available", "phase54_module_available", "phase54_windows_build_report", "run_phase54_native_reality_gate_contract", "write_phase54_native_dependency_report"]  # 新增代码+Phase54WindowsNativeRealityGate: 限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase54WindowsNativeRealityGate: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase54WindowsNativeRealityGate: 调用 main 并传递退出码；如果没有这行代码，命令行退出状态不明确。
