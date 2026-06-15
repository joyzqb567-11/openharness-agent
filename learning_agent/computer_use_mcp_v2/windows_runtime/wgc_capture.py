"""Phase36 Windows.Graphics.Capture provider contract."""  # 新增代码+Phase36WindowsWGCProvider: 说明本文件负责 WGC 截图 provider 合同；如果没有这行代码，读者不容易知道它不是鼠标键盘动作执行器。
from __future__ import annotations  # 新增代码+Phase36WindowsWGCProvider: 启用延迟类型解析；如果没有这行代码，旧运行路径下前向类型标注更容易出错。

import importlib.util  # 新增代码+Phase36WindowsWGCProvider: 用于安全探测 WGC Python 绑定；如果没有这行代码，依赖状态只能靠异常猜测。
import json  # 新增代码+Phase36WindowsWGCProvider: 用于 CLI 输出结构化诊断；如果没有这行代码，真实终端验收只能看散乱文本。
import sys  # 新增代码+Phase36WindowsWGCProvider: 用于读取当前平台；如果没有这行代码，非 Windows 环境可能被误判。
from typing import Any, Callable  # 新增代码+Phase36WindowsWGCProvider: 标注 capture_impl 和 JSON 结构；如果没有这行代码，provider seam 边界不清楚。


PHASE36_WINDOWS_WGC_PROVIDER_MARKER = "PHASE36_WINDOWS_WGC_PROVIDER_READY"  # 新增代码+Phase36WindowsWGCProvider: 定义 Phase36 完成标记；如果没有这行代码，真实终端验收没有稳定匹配点。
PHASE36_WINDOWS_WGC_PROVIDER_OK_TOKEN = "PHASE36_WINDOWS_WGC_PROVIDER_OK"  # 新增代码+Phase36WindowsWGCProvider: 定义 Phase36 命令成功 token；如果没有这行代码，debug log 无法确认命令执行。
PHASE36_WGC_BINDINGS = ("winrt.windows.graphics.capture", "winsdk.windows.graphics.capture")  # 新增代码+Phase36WindowsWGCProvider: 集中列出可接受 WGC 绑定；如果没有这行代码，依赖名称会散落且容易写错。
PHASE36_WGC_CONTRACT = "phase36_windows_graphics_capture_provider"  # 新增代码+Phase36WindowsWGCProvider: 定义 WGC provider 合同版本；如果没有这行代码，状态消费者无法区分 Phase33 占位和 Phase36 合同。


def phase36_module_available(module_name: str) -> bool:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，探测模块是否可发现；如果没有这段函数，依赖检测无法被单元测试注入。
    try:  # 新增代码+Phase36WindowsWGCProvider: 捕获 find_spec 的异常；如果没有这行代码，坏模块名或缺父包会让状态查询崩溃。
        return importlib.util.find_spec(module_name) is not None  # 新增代码+Phase36WindowsWGCProvider: 返回模块是否存在；如果没有这行代码，provider 不知道 WGC 绑定是否安装。
    except (ImportError, ModuleNotFoundError, ValueError):  # 新增代码+Phase36WindowsWGCProvider: 处理可选依赖缺失；如果没有这行代码，缺依赖会变成硬错误。
        return False  # 新增代码+Phase36WindowsWGCProvider: 缺失或异常时诚实返回不可用；如果没有这行代码，诊断可能误报可用。
# 新增代码+Phase36WindowsWGCProvider: 函数段结束，phase36_module_available 到此结束；如果没有这个边界说明，读者不容易看出依赖探测范围。


def phase36_dependency_status(module_available: Callable[[str], bool] | None = None, platform: str | None = None) -> dict[str, Any]:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，返回 WGC 依赖状态；如果没有这段函数，CLI 和 provider 会重复判断逻辑。
    current_platform = platform or sys.platform  # 新增代码+Phase36WindowsWGCProvider: 确定当前平台；如果没有这行代码，测试无法注入 win32/linux 场景。
    checker = module_available or phase36_module_available  # 新增代码+Phase36WindowsWGCProvider: 选择真实或注入的模块探测函数；如果没有这行代码，单元测试无法稳定模拟依赖。
    available_bindings = [binding for binding in PHASE36_WGC_BINDINGS if checker(binding)]  # 新增代码+Phase36WindowsWGCProvider: 收集可用绑定；如果没有这行代码，用户不知道哪个绑定被发现。
    dependency_available = current_platform == "win32" and bool(available_bindings)  # 新增代码+Phase36WindowsWGCProvider: 只有 Windows 且绑定存在才算依赖可用；如果没有这行代码，非 Windows 可能误报可用。
    return {"platform": current_platform, "platform_supported": current_platform == "win32", "dependency_reported": True, "dependency_available": dependency_available, "preferred_binding": "|".join(PHASE36_WGC_BINDINGS), "available_bindings": available_bindings}  # 新增代码+Phase36WindowsWGCProvider: 返回稳定依赖状态；如果没有这行代码，验收无法检查 dependency_reported=true。
# 新增代码+Phase36WindowsWGCProvider: 函数段结束，phase36_dependency_status 到此结束；如果没有这个边界说明，读者不容易看出依赖状态范围。


def _capture_result(**kwargs: Any) -> Any:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，创建统一 NativeWindowCaptureResult；如果没有这段函数，WGC provider 会和 GDI 截图合同分裂。
    from learning_agent.computer_use_mcp_v2.windows_runtime.native_helper import NativeWindowCaptureResult  # 新增代码+Phase36WindowsWGCProvider: 延迟导入截图结果避免 native_diagnostics 循环导入；如果没有这行代码，WGC 与 native_helper 可能互相卡住。

    return NativeWindowCaptureResult(**kwargs)  # 新增代码+Phase36WindowsWGCProvider: 返回统一截图结果对象；如果没有这行代码，调用方无法复用 Phase32 evidence store。
# 新增代码+Phase36WindowsWGCProvider: 函数段结束，_capture_result 到此结束；如果没有这个边界说明，读者不容易看出结果构造范围。


def _coerce_capture_result(raw_result: Any) -> Any:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，把注入实现结果转为统一截图合同；如果没有这段函数，测试 seam 和未来真实实现返回值会不兼容。
    from learning_agent.computer_use_mcp_v2.windows_runtime.native_helper import NativeWindowCaptureResult  # 新增代码+Phase36WindowsWGCProvider: 延迟导入结果类型用于 isinstance；如果没有这行代码，无法识别已有统一结果。

    if isinstance(raw_result, NativeWindowCaptureResult):  # 新增代码+Phase36WindowsWGCProvider: 已经是统一结果时直接处理；如果没有这行代码，真实实现返回统一对象也会被误转。
        return NativeWindowCaptureResult(captured=raw_result.captured, screenshot_bytes=raw_result.screenshot_bytes, screenshot_format=raw_result.screenshot_format, screenshot_width=raw_result.screenshot_width, screenshot_height=raw_result.screenshot_height, backend="windows_graphics_capture", reason=raw_result.reason)  # 新增代码+Phase36WindowsWGCProvider: 覆盖 backend 为 WGC；如果没有这行代码，注入实现可能污染后端名。
    if isinstance(raw_result, dict):  # 新增代码+Phase36WindowsWGCProvider: 支持 dict 结果方便未来 helper/测试接入；如果没有这行代码，轻量实现无法复用。
        return NativeWindowCaptureResult(captured=bool(raw_result.get("captured", False)), screenshot_bytes=bytes(raw_result.get("screenshot_bytes", b"")), screenshot_format=str(raw_result.get("screenshot_format", "")), screenshot_width=int(raw_result.get("screenshot_width", 0)), screenshot_height=int(raw_result.get("screenshot_height", 0)), backend="windows_graphics_capture", reason=str(raw_result.get("reason", "")))  # 新增代码+Phase36WindowsWGCProvider: 将 dict 转为统一结果；如果没有这行代码，evidence store 无法稳定读取字段。
    if isinstance(raw_result, bytes):  # 新增代码+Phase36WindowsWGCProvider: 支持 bytes 结果作为最小截图输出；如果没有这行代码，简单实现必须包一层 dict。
        return NativeWindowCaptureResult(captured=bool(raw_result), screenshot_bytes=raw_result, screenshot_format="png", screenshot_width=0, screenshot_height=0, backend="windows_graphics_capture", reason="WGC capture implementation returned raw bytes.")  # 新增代码+Phase36WindowsWGCProvider: 将 bytes 转成 PNG 占位结果；如果没有这行代码，原始 bytes 无法进入统一合同。
    return NativeWindowCaptureResult(backend="windows_graphics_capture", reason="WGC capture implementation returned unsupported result type.")  # 新增代码+Phase36WindowsWGCProvider: 不支持类型时诚实失败；如果没有这行代码，坏结果可能污染截图证据。
# 新增代码+Phase36WindowsWGCProvider: 函数段结束，_coerce_capture_result 到此结束；如果没有这个边界说明，读者不容易看出结果转换范围。


class WindowsGraphicsCaptureProvider:  # 新增代码+Phase36WindowsWGCProvider: 定义 WGC 截图 provider；如果没有这个类，learning_agent 没有独立 WGC 合同入口。
    def __init__(self, platform: str | None = None, module_available: Callable[[str], bool] | None = None, capture_impl: Callable[[int], Any] | None = None) -> None:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，初始化平台、依赖探测和可注入实现；如果没有这段函数，测试和未来真实 helper 无法接入。
        self.platform = platform or sys.platform  # 新增代码+Phase36WindowsWGCProvider: 保存平台名称；如果没有这行代码，status 和 capture 无法跨平台拒绝。
        self.module_available = module_available  # 新增代码+Phase36WindowsWGCProvider: 保存可注入依赖探测函数；如果没有这行代码，测试无法模拟 WGC 绑定存在。
        self.capture_impl = capture_impl  # 新增代码+Phase36WindowsWGCProvider: 保存可注入截图实现；如果没有这行代码，Phase36 只能诊断不能覆盖成功合同。
    # 新增代码+Phase36WindowsWGCProvider: 函数段结束，WindowsGraphicsCaptureProvider.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，返回 WGC provider 状态；如果没有这段函数，diagnostics 无法展示 Phase36 合同。
        dependency = phase36_dependency_status(module_available=self.module_available, platform=self.platform)  # 新增代码+Phase36WindowsWGCProvider: 读取依赖状态；如果没有这行代码，provider 可用性无法解释。
        implementation_available = self.capture_impl is not None  # 新增代码+Phase36WindowsWGCProvider: 判断是否注入真实/测试截图实现；如果没有这行代码，只有依赖也会被误当可用。
        available = bool(dependency["dependency_available"] and implementation_available)  # 新增代码+Phase36WindowsWGCProvider: 依赖和实现都存在才可用；如果没有这行代码，合同会虚报真实截图能力。
        reason = "WGC provider contract ready, but fallback is still required until dependency and capture implementation are available."  # 新增代码+Phase36WindowsWGCProvider: 准备默认原因；如果没有这行代码，缺口说明不稳定。
        if available:  # 新增代码+Phase36WindowsWGCProvider: 检查 provider 是否可用；如果没有这行代码，成功原因不会区分。
            reason = "WGC provider dependency and capture implementation are available."  # 新增代码+Phase36WindowsWGCProvider: 设置可用原因；如果没有这行代码，成功状态仍像失败。
        return {"name": "windows_graphics_capture", "backend": "windows_graphics_capture", "role": "capture", "preferred": True, "active": False, "available": available, "contract": PHASE36_WGC_CONTRACT, "contract_ready": True, "dependency_reported": True, "dependency_available": bool(dependency["dependency_available"]), "implementation_available": implementation_available, "fallback_required": not available, "priority": 10, "dependency": dependency["preferred_binding"], "available_bindings": dependency["available_bindings"], "reason": reason, "next_step": "Install or wire a real WGC helper only after explicit user approval; keep GDI fallback until then."}  # 新增代码+Phase36WindowsWGCProvider: 返回机器可读状态；如果没有这行代码，Phase36 无法被验收和诊断复用。
    # 新增代码+Phase36WindowsWGCProvider: 函数段结束，WindowsGraphicsCaptureProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态范围。

    def capture_window(self, hwnd: int) -> Any:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，按合同尝试捕获窗口；如果没有这段函数，provider 只有状态没有截图入口。
        status = self.status()  # 新增代码+Phase36WindowsWGCProvider: 读取当前状态；如果没有这行代码，capture 无法根据依赖和实现拒绝。
        if self.platform != "win32":  # 新增代码+Phase36WindowsWGCProvider: 非 Windows 平台拒绝；如果没有这行代码，跨平台测试可能误触 Windows API。
            return _capture_result(backend="windows_graphics_capture", reason="当前平台不是 Windows，未调用 WGC。")  # 新增代码+Phase36WindowsWGCProvider: 返回平台拒绝结果；如果没有这行代码，用户不知道为何没有截图。
        if int(hwnd or 0) <= 0:  # 新增代码+Phase36WindowsWGCProvider: 拒绝无效窗口句柄；如果没有这行代码，0 句柄可能传给未来 helper。
            return _capture_result(backend="windows_graphics_capture", reason="窗口句柄无效，未调用 WGC。")  # 新增代码+Phase36WindowsWGCProvider: 返回坏句柄原因；如果没有这行代码，错误目标不易排查。
        if not status["dependency_available"]:  # 新增代码+Phase36WindowsWGCProvider: 依赖缺失时拒绝截图；如果没有这行代码，provider 可能用 fake 结果冒充 WGC。
            return _capture_result(backend="windows_graphics_capture", reason="缺少 Windows.Graphics.Capture Python 绑定，未调用 WGC。")  # 新增代码+Phase36WindowsWGCProvider: 返回缺依赖原因；如果没有这行代码，用户不知道需要 fallback。
        if self.capture_impl is None:  # 新增代码+Phase36WindowsWGCProvider: 没有真实实现时拒绝截图；如果没有这行代码，仅依赖存在也会被误当可截图。
            return _capture_result(backend="windows_graphics_capture", reason="WGC provider 合同已建立，但真实 capture_impl 尚未接入。")  # 新增代码+Phase36WindowsWGCProvider: 返回未接实现原因；如果没有这行代码，Phase36 会虚报成熟度。
        try:  # 新增代码+Phase36WindowsWGCProvider: 包住注入实现调用；如果没有这行代码，helper 异常会拖垮 agent。
            return _coerce_capture_result(self.capture_impl(int(hwnd)))  # 新增代码+Phase36WindowsWGCProvider: 调用实现并转成统一合同；如果没有这行代码，成功截图无法进入 evidence。
        except Exception as error:  # 新增代码+Phase36WindowsWGCProvider: 捕获截图实现异常；如果没有这行代码，权限或窗口异常会直接崩溃。
            return _capture_result(backend="windows_graphics_capture", reason=f"WGC 截图失败：{type(error).__name__}")  # 新增代码+Phase36WindowsWGCProvider: 返回异常类型但不泄露本地细节；如果没有这行代码，用户只会看到堆栈。
    # 新增代码+Phase36WindowsWGCProvider: 函数段结束，WindowsGraphicsCaptureProvider.capture_window 到此结束；如果没有这个边界说明，读者不容易看出截图入口范围。


def run_phase36_wgc_provider_contract(module_available: Callable[[str], bool] | None = None, platform: str | None = None) -> dict[str, Any]:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，执行 Phase36 合同诊断；如果没有这段函数，真实终端验收没有稳定入口。
    provider = WindowsGraphicsCaptureProvider(platform=platform, module_available=module_available)  # 新增代码+Phase36WindowsWGCProvider: 创建默认 WGC provider；如果没有这行代码，状态无法生成。
    status = provider.status()  # 新增代码+Phase36WindowsWGCProvider: 读取 provider 状态；如果没有这行代码，CLI 没有诊断内容。
    invalid_capture = provider.capture_window(0)  # 新增代码+Phase36WindowsWGCProvider: 用无效 hwnd 覆盖安全拒绝路径；如果没有这行代码，capture 合同没有被命令验收。
    return {"marker": PHASE36_WINDOWS_WGC_PROVIDER_MARKER, "ok_token": PHASE36_WINDOWS_WGC_PROVIDER_OK_TOKEN, "status": status, "invalid_capture_reason": invalid_capture.reason, "dependency_reported": bool(status["dependency_reported"]), "capture_contract_ready": bool(status["contract_ready"]), "fallback_required": bool(status["fallback_required"]), "actions_expanded": False, "fake_provider_used": False}  # 新增代码+Phase36WindowsWGCProvider: 返回稳定验收数据；如果没有这行代码，场景无法检查关键边界。
# 新增代码+Phase36WindowsWGCProvider: 函数段结束，run_phase36_wgc_provider_contract 到此结束；如果没有这个边界说明，读者不容易看出合同诊断范围。


def phase36_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，生成真实终端验收行；如果没有这段函数，verifier 需要解析完整 JSON。
    return f"{PHASE36_WINDOWS_WGC_PROVIDER_OK_TOKEN} dependency_reported={str(report['dependency_reported']).lower()} capture_contract_ready={str(report['capture_contract_ready']).lower()} fallback_required={str(report['fallback_required']).lower()} actions_expanded={str(report['actions_expanded']).lower()} fake_provider_used={str(report['fake_provider_used']).lower()} marker={PHASE36_WINDOWS_WGC_PROVIDER_MARKER}"  # 新增代码+Phase36WindowsWGCProvider: 返回稳定 token 行；如果没有这行代码，真实终端验收容易漏检边界。
# 新增代码+Phase36WindowsWGCProvider: 函数段结束，phase36_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase36WindowsWGCProvider: 函数段开始，提供命令行入口；如果没有这段函数，场景不能直接运行 Phase36 合同检查。
    _ = argv  # 新增代码+Phase36WindowsWGCProvider: 保留 argv 便于未来扩展；如果没有这行代码，静态检查可能提示未使用参数。
    report = run_phase36_wgc_provider_contract()  # 新增代码+Phase36WindowsWGCProvider: 执行合同诊断；如果没有这行代码，CLI 不会检查 provider 状态。
    print(phase36_cli_line(report))  # 新增代码+Phase36WindowsWGCProvider: 打印稳定验收 token；如果没有这行代码，debug log 匹配不到成功证据。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase36WindowsWGCProvider: 打印结构化报告；如果没有这行代码，用户难以理解 fallback 原因。
    print(PHASE36_WINDOWS_WGC_PROVIDER_MARKER)  # 新增代码+Phase36WindowsWGCProvider: 单独打印阶段标记；如果没有这行代码，最终回答复制时容易漏 marker。
    return 0  # 新增代码+Phase36WindowsWGCProvider: 合同诊断完成即返回成功；如果没有这行代码，诚实缺依赖会被误当命令失败。
# 新增代码+Phase36WindowsWGCProvider: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出命令入口范围。


if __name__ == "__main__":  # 新增代码+Phase36WindowsWGCProvider: 允许直接运行模块；如果没有这行代码，python 文件不会启动 main。
    raise SystemExit(main())  # 新增代码+Phase36WindowsWGCProvider: 使用 main 返回码退出；如果没有这行代码，命令行状态不稳定。
