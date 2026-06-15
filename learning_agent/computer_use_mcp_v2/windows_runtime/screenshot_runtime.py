"""Windows Computer Use screenshot runtime."""  # 新增代码+Phase45WindowsScreenshotRuntime: 说明本文件负责统一真实 Windows 截图运行时；如果没有这个文件，WGC/GDI/provider/evidence 会继续分散在多个入口里。
from __future__ import annotations  # 新增代码+Phase45WindowsScreenshotRuntime: 启用延迟类型解析；如果没有这行代码，旧运行路径遇到前向类型标注更容易导入失败。

import json  # 新增代码+Phase45WindowsScreenshotRuntime: 用于 CLI 输出结构化报告；如果没有这行代码，真实终端验收只能看到零散文本。
import sys  # 新增代码+Phase45WindowsScreenshotRuntime: 用于判断当前平台是否 Windows；如果没有这行代码，非 Windows 环境可能误触发 Win32 截图逻辑。
import tempfile  # 新增代码+Phase45WindowsScreenshotRuntime: 用于自检时创建隔离 evidence 目录；如果没有这行代码，自检会污染真实项目证据目录。
from pathlib import Path  # 新增代码+Phase45WindowsScreenshotRuntime: 用于管理截图 artifact 路径；如果没有这行代码，路径拼接会更脆弱。
from typing import Any  # 新增代码+Phase45WindowsScreenshotRuntime: 用于标注 JSON 风格输入输出；如果没有这行代码，接口边界不清楚。

try:  # 新增代码+Phase45WindowsScreenshotRuntime: 优先按包模式导入截图、evidence 和 provider 合同；如果没有这行代码，unittest 和生产入口不能复用已有模块。
    from learning_agent.computer_use_mcp_v2.windows_runtime.evidence import ComputerUseEvidenceStore  # 新增代码+Phase45WindowsScreenshotRuntime: 导入 evidence store；如果没有这行代码，截图 bytes 无法落盘成 artifact。
    from learning_agent.computer_use_mcp_v2.windows_runtime.helper_client import WindowObservationPayload  # 新增代码+Phase45WindowsScreenshotRuntime: 导入统一 observation payload；如果没有这行代码，runtime 无法复用 Phase29/41 证据链。
    from learning_agent.computer_use_mcp_v2.windows_runtime.native_helper import NativeWindowCaptureResult, Win32GdiWindowCaptureProvider, parse_hwnd_from_window  # 新增代码+Phase45WindowsScreenshotRuntime: 导入截图结果、GDI fallback 和 hwnd 解析；如果没有这行代码，runtime 无法连接真实 Win32 截图能力。
    from learning_agent.computer_use_mcp_v2.windows_runtime.wgc_capture import WindowsGraphicsCaptureProvider  # 新增代码+Phase45WindowsScreenshotRuntime: 导入 WGC provider 合同；如果没有这行代码，runtime 无法表达 WGC 优先、GDI 保底的生产顺序。
except ModuleNotFoundError as error:  # 新增代码+Phase45WindowsScreenshotRuntime: 兼容 start_oauth_agent.bat 脚本模式；如果没有这行代码，直接运行 learning_agent 目录时可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.evidence", "learning_agent.computer_use_mcp_v2.windows_runtime.helper_client", "learning_agent.computer_use_mcp_v2.windows_runtime.native_helper", "learning_agent.computer_use_mcp_v2.windows_runtime.wgc_capture"}:  # 新增代码+Phase45WindowsScreenshotRuntime: 只允许目标包路径缺失时 fallback；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase45WindowsScreenshotRuntime: 重新抛出非路径类导入错误；如果没有这行代码，排查 provider 内部错误会困难。
    from computer_use_mcp_v2.windows_runtime.evidence import ComputerUseEvidenceStore  # 新增代码+Phase45WindowsScreenshotRuntime: 脚本模式导入 evidence store；如果没有这行代码，bat 入口无法保存截图 artifact。
    from computer_use_mcp_v2.windows_runtime.helper_client import WindowObservationPayload  # 新增代码+Phase45WindowsScreenshotRuntime: 脚本模式导入 observation payload；如果没有这行代码，bat 入口无法构造 evidence 输入。
    from computer_use_mcp_v2.windows_runtime.native_helper import NativeWindowCaptureResult, Win32GdiWindowCaptureProvider, parse_hwnd_from_window  # 新增代码+Phase45WindowsScreenshotRuntime: 脚本模式导入 GDI fallback 和 hwnd 解析；如果没有这行代码，bat 入口无法使用 Win32 截图保底能力。
    from computer_use_mcp_v2.windows_runtime.wgc_capture import WindowsGraphicsCaptureProvider  # 新增代码+Phase45WindowsScreenshotRuntime: 脚本模式导入 WGC provider；如果没有这行代码，bat 入口无法报告 WGC 优先链路。

PHASE45_WINDOWS_SCREENSHOT_RUNTIME_MARKER = "PHASE45_WINDOWS_SCREENSHOT_RUNTIME_READY"  # 新增代码+Phase45WindowsScreenshotRuntime: 定义 Phase45 ready marker；如果没有这行代码，真实终端验收没有稳定等待锚点。
PHASE45_WINDOWS_SCREENSHOT_RUNTIME_OK_TOKEN = "PHASE45_WINDOWS_SCREENSHOT_RUNTIME_OK"  # 新增代码+Phase45WindowsScreenshotRuntime: 定义 Phase45 OK token；如果没有这行代码，日志无法区分运行完成和真正通过。
PHASE45_SCREENSHOT_RUNTIME_MODEL = "phase45_windows_screenshot_runtime"  # 新增代码+Phase45WindowsScreenshotRuntime: 定义截图运行时模型名；如果没有这行代码，后续状态和 evidence 难以区分版本。
PHASE45_ACTIONS_EXPANDED = False  # 新增代码+Phase45WindowsScreenshotRuntime: 明确 Phase45 只读截图不扩大鼠标键盘动作；如果没有这行代码，安全审计无法确认边界。


def _phase45_bool_token(value: Any) -> str:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，把布尔值转成验收友好的小写文本；如果没有这段函数，CLI token 大小写容易漂移。
    return str(bool(value)).lower()  # 新增代码+Phase45WindowsScreenshotRuntime: 返回 true/false；如果没有这行代码，场景断言可能因 True/False 失败。
# 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，_phase45_bool_token 到此结束；如果没有这个边界说明，读者不容易看出布尔格式范围。


def _provider_status(provider: Any) -> dict[str, Any]:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，安全读取 provider.status；如果没有这段函数，坏 provider 会拖垮整个截图状态页。
    if hasattr(provider, "status"):  # 新增代码+Phase45WindowsScreenshotRuntime: 检查 provider 是否提供状态方法；如果没有这行代码，普通对象会触发 AttributeError。
        status = provider.status()  # 新增代码+Phase45WindowsScreenshotRuntime: 调用 provider 状态；如果没有这行代码，provider 链无法展示可用性。
        return dict(status) if isinstance(status, dict) else {}  # 新增代码+Phase45WindowsScreenshotRuntime: 只接受 dict 状态；如果没有这行代码，异常返回类型会污染状态结构。
    return {}  # 新增代码+Phase45WindowsScreenshotRuntime: 没有 status 时返回空状态；如果没有这行代码，调用方需要到处兜底。
# 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，_provider_status 到此结束；如果没有这个边界说明，读者不容易看出状态读取范围。


def _provider_name(provider: Any, fallback: str = "unknown_capture_provider") -> str:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，提取 provider 名称；如果没有这段函数，审计里的 provider 字段会不稳定。
    status = _provider_status(provider)  # 新增代码+Phase45WindowsScreenshotRuntime: 先读取 provider 状态；如果没有这行代码，名称无法复用 backend/name 字段。
    return str(status.get("backend") or status.get("name") or fallback)  # 新增代码+Phase45WindowsScreenshotRuntime: 返回 backend/name 或兜底名；如果没有这行代码，provider 名称可能为空。
# 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，_provider_name 到此结束；如果没有这个边界说明，读者不容易看出名称提取范围。


def _coerce_capture_result(raw_result: Any, backend: str) -> NativeWindowCaptureResult:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，把 provider 返回值转成统一截图结果；如果没有这段函数，未来 WGC/GDI 返回结构变化会破坏 runtime。
    if isinstance(raw_result, NativeWindowCaptureResult):  # 新增代码+Phase45WindowsScreenshotRuntime: 识别已有统一结果；如果没有这行代码，标准 provider 也会被当成失败。
        return raw_result  # 新增代码+Phase45WindowsScreenshotRuntime: 原样返回统一结果；如果没有这行代码，provider 成功结果会被丢弃。
    if isinstance(raw_result, dict):  # 新增代码+Phase45WindowsScreenshotRuntime: 支持轻量 dict 返回；如果没有这行代码，未来外部 helper 接入要写额外适配层。
        return NativeWindowCaptureResult(captured=bool(raw_result.get("captured", False)), screenshot_bytes=bytes(raw_result.get("screenshot_bytes", b"")), screenshot_format=str(raw_result.get("screenshot_format", "")), screenshot_width=int(raw_result.get("screenshot_width", 0) or 0), screenshot_height=int(raw_result.get("screenshot_height", 0) or 0), backend=backend, reason=str(raw_result.get("reason", "")))  # 新增代码+Phase45WindowsScreenshotRuntime: 把 dict 转为统一结果；如果没有这行代码，evidence store 无法稳定读取字段。
    return NativeWindowCaptureResult(captured=False, backend=backend, reason="provider 返回了不支持的截图结果类型。")  # 新增代码+Phase45WindowsScreenshotRuntime: 不支持类型时诚实失败；如果没有这行代码，坏结果可能伪装成空截图。
# 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，_coerce_capture_result 到此结束；如果没有这个边界说明，读者不容易看出结果转换范围。


def _default_phase45_providers(platform: str) -> list[Any]:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，构造默认截图 provider 链；如果没有这段函数，生产和测试入口会重复拼 WGC/GDI 顺序。
    return [WindowsGraphicsCaptureProvider(platform=platform), Win32GdiWindowCaptureProvider(platform=platform)]  # 新增代码+Phase45WindowsScreenshotRuntime: 返回 WGC 优先、GDI 保底链；如果没有这行代码，真实 Windows 截图缺少统一生产顺序。
# 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，_default_phase45_providers 到此结束；如果没有这个边界说明，读者不容易看出默认 provider 范围。


class WindowsScreenshotCaptureRuntime:  # 新增代码+Phase45WindowsScreenshotRuntime: 类段开始，统一 Windows 截图 provider 链和 evidence 落盘；如果没有这个类，截图能力会继续散落在 native helper 和 host 中。
    def __init__(self, providers: list[Any] | None = None, evidence_root: Path | str | None = None, evidence_store: Any | None = None, platform: str | None = None) -> None:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，初始化截图运行时；如果没有这段函数，调用方无法注入 provider 或隔离 evidence。
        self.platform = platform or sys.platform  # 新增代码+Phase45WindowsScreenshotRuntime: 保存平台名；如果没有这行代码，非 Windows 拒绝逻辑无法测试。
        self.providers = list(providers) if providers is not None else _default_phase45_providers(self.platform)  # 新增代码+Phase45WindowsScreenshotRuntime: 保存 provider 链；如果没有这行代码，runtime 没有截图来源。
        self.evidence_store = evidence_store or ComputerUseEvidenceStore(evidence_root=Path(evidence_root) if evidence_root is not None else None)  # 新增代码+Phase45WindowsScreenshotRuntime: 保存 evidence store；如果没有这行代码，截图无法写成本地 artifact。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，WindowsScreenshotCaptureRuntime.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，返回截图运行时状态；如果没有这段函数，/computer 或 host 不能展示截图链路健康度。
        provider_statuses = []  # 新增代码+Phase45WindowsScreenshotRuntime: 准备 provider 状态列表；如果没有这行代码，状态没有容器。
        for provider in self.providers:  # 新增代码+Phase45WindowsScreenshotRuntime: 遍历 provider 链；如果没有这行代码，WGC/GDI 状态无法逐项展示。
            status = _provider_status(provider)  # 新增代码+Phase45WindowsScreenshotRuntime: 安全读取单个 provider 状态；如果没有这行代码，坏 provider 会中断状态。
            status.setdefault("backend", _provider_name(provider))  # 新增代码+Phase45WindowsScreenshotRuntime: 保证 backend 字段存在；如果没有这行代码，状态消费端可能不知道 provider 名。
            provider_statuses.append(status)  # 新增代码+Phase45WindowsScreenshotRuntime: 追加 provider 状态；如果没有这行代码，状态列表永远为空。
        return {"marker": PHASE45_WINDOWS_SCREENSHOT_RUNTIME_MARKER, "model": PHASE45_SCREENSHOT_RUNTIME_MODEL, "platform": self.platform, "provider_count": len(provider_statuses), "providers": provider_statuses, "preferred_provider": provider_statuses[0].get("backend", "") if provider_statuses else "", "fallback_provider": provider_statuses[-1].get("backend", "") if provider_statuses else "", "evidence_root": str(self.evidence_store.evidence_root), "raw_bytes_returned": False, "actions_expanded": PHASE45_ACTIONS_EXPANDED}  # 新增代码+Phase45WindowsScreenshotRuntime: 返回完整状态；如果没有这行代码，截图运行时没有统一事实源。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，WindowsScreenshotCaptureRuntime.status 到此结束；如果没有这个边界说明，读者不容易看出状态范围。

    def _failure(self, reason: str, attempts: list[dict[str, Any]] | None = None) -> dict[str, Any]:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，构造失败响应；如果没有这段函数，各失败分支会重复且格式不一致。
        return {"marker": PHASE45_WINDOWS_SCREENSHOT_RUNTIME_MARKER, "model": PHASE45_SCREENSHOT_RUNTIME_MODEL, "captured": False, "provider": "", "provider_attempts": list(attempts or []), "reason": str(reason), "screenshot_captured": False, "screenshot_path": "", "screenshot_bytes_included": False, "image_results": [], "image_result_count": 0, "actions_expanded": PHASE45_ACTIONS_EXPANDED}  # 新增代码+Phase45WindowsScreenshotRuntime: 返回统一失败结构；如果没有这行代码，host 和测试难以稳定读取失败原因。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，WindowsScreenshotCaptureRuntime._failure 到此结束；如果没有这个边界说明，读者不容易看出失败响应范围。

    def _save_success(self, window: dict[str, Any], capture: NativeWindowCaptureResult, attempts: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，保存成功截图到 evidence；如果没有这段函数，成功截图只能停在内存里。
        payload = WindowObservationPayload(screenshot_bytes=capture.screenshot_bytes, screenshot_format=capture.screenshot_format, screenshot_width=capture.screenshot_width, screenshot_height=capture.screenshot_height, helper_name="phase45_windows_screenshot_runtime", helper_available=True, helper_reason=f"{capture.backend}:{capture.reason}")  # 新增代码+Phase45WindowsScreenshotRuntime: 构造只含截图的 observation payload；如果没有这行代码，evidence store 无法复用已有保存逻辑。
        evidence = self.evidence_store.save_window_state(window=window, payload=payload, fallback_width=capture.screenshot_width, fallback_height=capture.screenshot_height)  # 新增代码+Phase45WindowsScreenshotRuntime: 写入截图 artifact 和 metadata；如果没有这行代码，模型拿不到可打开的图片路径。
        result = dict(evidence)  # 新增代码+Phase45WindowsScreenshotRuntime: 复制 evidence 结果便于追加 runtime 字段；如果没有这行代码，直接修改可能污染调用方预期。
        result["marker"] = PHASE45_WINDOWS_SCREENSHOT_RUNTIME_MARKER  # 新增代码+Phase45WindowsScreenshotRuntime: 写入 Phase45 marker；如果没有这行代码，验收无法识别截图运行时输出。
        result["model"] = PHASE45_SCREENSHOT_RUNTIME_MODEL  # 新增代码+Phase45WindowsScreenshotRuntime: 写入模型名；如果没有这行代码，后续兼容层无法判断协议版本。
        result["captured"] = True  # 新增代码+Phase45WindowsScreenshotRuntime: 标记截图成功；如果没有这行代码，host 只能猜测 screenshot_captured。
        result["provider"] = capture.backend  # 新增代码+Phase45WindowsScreenshotRuntime: 记录成功 provider；如果没有这行代码，审计不知道截图来自 WGC 还是 GDI。
        result["provider_attempts"] = list(attempts)  # 新增代码+Phase45WindowsScreenshotRuntime: 记录 provider 尝试链；如果没有这行代码，fallback 是否发生不可复盘。
        result["screenshot_bytes_included"] = False  # 新增代码+Phase45WindowsScreenshotRuntime: 明确响应不含原始 bytes；如果没有这行代码，调用方无法确认 IPC 安全边界。
        result["actions_expanded"] = PHASE45_ACTIONS_EXPANDED  # 新增代码+Phase45WindowsScreenshotRuntime: 写入动作边界；如果没有这行代码，安全验收无法确认未扩大写动作。
        return result  # 新增代码+Phase45WindowsScreenshotRuntime: 返回带 evidence 和 runtime 字段的结果；如果没有这行代码，调用方拿不到截图摘要。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，WindowsScreenshotCaptureRuntime._save_success 到此结束；如果没有这个边界说明，读者不容易看出成功保存范围。

    def capture_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，按窗口执行只读截图；如果没有这段函数，runtime 只有状态没有截图能力。
        safe_window = dict(window or {})  # 新增代码+Phase45WindowsScreenshotRuntime: 复制窗口输入避免污染调用方对象；如果没有这行代码，后续追加字段可能改到外部状态。
        if self.platform != "win32":  # 新增代码+Phase45WindowsScreenshotRuntime: 非 Windows 平台拒绝真实截图；如果没有这行代码，跨平台测试会误触发 Win32 API。
            return self._failure("当前平台不是 Windows，未调用截图 provider。")  # 新增代码+Phase45WindowsScreenshotRuntime: 返回平台拒绝；如果没有这行代码，用户不知道为什么没有截图。
        hwnd = parse_hwnd_from_window(safe_window)  # 新增代码+Phase45WindowsScreenshotRuntime: 解析窗口句柄；如果没有这行代码，provider 无法知道目标窗口。
        if hwnd <= 0:  # 新增代码+Phase45WindowsScreenshotRuntime: 检查 hwnd 是否有效；如果没有这行代码，0 句柄可能传给系统 API。
            return self._failure("窗口句柄无效，未截图。")  # 新增代码+Phase45WindowsScreenshotRuntime: 返回坏 hwnd 原因；如果没有这行代码，错误目标不可解释。
        attempts: list[dict[str, Any]] = []  # 新增代码+Phase45WindowsScreenshotRuntime: 准备 provider 尝试记录；如果没有这行代码，fallback 过程无法审计。
        for provider in self.providers:  # 新增代码+Phase45WindowsScreenshotRuntime: 按顺序尝试 WGC/GDI provider；如果没有这行代码，只能使用单一截图来源。
            backend = _provider_name(provider)  # 新增代码+Phase45WindowsScreenshotRuntime: 读取 provider 名称；如果没有这行代码，attempt 记录缺来源。
            try:  # 新增代码+Phase45WindowsScreenshotRuntime: 捕获 provider 调用异常；如果没有这行代码，桌面权限或窗口状态异常会拖垮 agent。
                capture = _coerce_capture_result(provider.capture_window(hwnd), backend)  # 新增代码+Phase45WindowsScreenshotRuntime: 调用 provider 并统一结果；如果没有这行代码，截图 provider 链不会执行。
            except Exception as error:  # 新增代码+Phase45WindowsScreenshotRuntime: 捕获 provider 异常；如果没有这行代码，单个 provider 失败会阻止 fallback。
                capture = NativeWindowCaptureResult(captured=False, backend=backend, reason=f"provider 调用失败：{type(error).__name__}")  # 新增代码+Phase45WindowsScreenshotRuntime: 把异常转为失败结果；如果没有这行代码，失败原因不稳定。
            attempts.append({"provider": backend, "captured": bool(capture.captured), "reason": capture.reason})  # 新增代码+Phase45WindowsScreenshotRuntime: 记录本次 provider 结果；如果没有这行代码，审计无法看到尝试链。
            if bool(capture.captured and capture.screenshot_bytes):  # 新增代码+Phase45WindowsScreenshotRuntime: 只有成功且有 bytes 才算可保存截图；如果没有这行代码，空截图会生成误导 artifact。
                return self._save_success(safe_window, capture, attempts)  # 新增代码+Phase45WindowsScreenshotRuntime: 保存并返回成功结果；如果没有这行代码，成功截图无法落盘。
        return self._failure("所有截图 provider 都未能捕获窗口。", attempts)  # 新增代码+Phase45WindowsScreenshotRuntime: 全部失败时返回统一失败；如果没有这行代码，调用方拿不到失败摘要。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，WindowsScreenshotCaptureRuntime.capture_window 到此结束；如果没有这个边界说明，读者不容易看出截图流程范围。
# 新增代码+Phase45WindowsScreenshotRuntime: 类段结束，WindowsScreenshotCaptureRuntime 到此结束；如果没有这个边界说明，读者不容易看出运行时类范围。


class _Phase45ContractProvider:  # 新增代码+Phase45WindowsScreenshotRuntime: 类段开始，定义自检专用 fake provider；如果没有这个类，CLI 自检会触碰真实桌面。
    def __init__(self, backend: str, captured: bool) -> None:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，初始化自检 provider；如果没有这段函数，自检无法模拟 fallback。
        self.backend = backend  # 新增代码+Phase45WindowsScreenshotRuntime: 保存 provider 名；如果没有这行代码，自检结果没有 provider 来源。
        self.captured = captured  # 新增代码+Phase45WindowsScreenshotRuntime: 保存是否成功；如果没有这行代码，自检无法让首选失败 fallback 成功。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，_Phase45ContractProvider.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，返回自检 provider 状态；如果没有这段函数，runtime status 自检缺 provider 信息。
        return {"backend": self.backend, "available": True, "reason": "phase45 contract provider", "contract_ready": True}  # 新增代码+Phase45WindowsScreenshotRuntime: 返回稳定状态；如果没有这行代码，自检状态字段可能缺失。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，_Phase45ContractProvider.status 到此结束；如果没有这个边界说明，读者不容易看出状态范围。

    def capture_window(self, hwnd: int) -> NativeWindowCaptureResult:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，模拟截图；如果没有这段函数，自检无法运行 capture_window。
        if not self.captured:  # 新增代码+Phase45WindowsScreenshotRuntime: 模拟失败 provider；如果没有这行代码，fallback=true 无法被证明。
            return NativeWindowCaptureResult(captured=False, backend=self.backend, reason="phase45 contract preferred provider refused")  # 新增代码+Phase45WindowsScreenshotRuntime: 返回首选失败；如果没有这行代码，自检无法覆盖 fallback。
        return NativeWindowCaptureResult(captured=True, screenshot_bytes=b"phase45-contract-png", screenshot_format="png", screenshot_width=450, screenshot_height=245, backend=self.backend, reason=f"phase45 captured {hwnd}")  # 新增代码+Phase45WindowsScreenshotRuntime: 返回安全 fake bytes；如果没有这行代码，自检没有 artifact 可写。
    # 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，_Phase45ContractProvider.capture_window 到此结束；如果没有这个边界说明，读者不容易看出 fake 截图范围。
# 新增代码+Phase45WindowsScreenshotRuntime: 类段结束，_Phase45ContractProvider 到此结束；如果没有这个边界说明，读者不容易看出自检 provider 范围。


def run_phase45_screenshot_runtime_contract() -> dict[str, Any]:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，运行安全截图运行时自检；如果没有这段函数，真实终端场景没有稳定命令入口。
    from learning_agent.computer_use_mcp_v2.windows_runtime.native_host import InProcessWindowsNativeHostClient, WindowsComputerUseNativeHost  # 新增代码+Phase45WindowsScreenshotRuntime: 延迟导入 native host 避免循环依赖；如果没有这行代码，自检无法证明 host capture 接入。
    window = {"window_id": "hwnd:4501", "hwnd": 4501, "title": "Phase45 Contract Window", "rect": {"left": 10, "top": 20, "right": 460, "bottom": 265}}  # 新增代码+Phase45WindowsScreenshotRuntime: 准备静态窗口输入；如果没有这行代码，自检无法解析 hwnd。
    with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Phase45WindowsScreenshotRuntime: 创建隔离 evidence 目录；如果没有这行代码，自检会污染真实截图目录。
        runtime = WindowsScreenshotCaptureRuntime(providers=[_Phase45ContractProvider("windows_graphics_capture", False), _Phase45ContractProvider("win32_gdi_printwindow", True)], evidence_root=Path(raw_dir), platform="win32")  # 新增代码+Phase45WindowsScreenshotRuntime: 创建 WGC 失败、GDI 成功的运行时；如果没有这行代码，fallback=true 没有证据。
        capture = runtime.capture_window(window)  # 新增代码+Phase45WindowsScreenshotRuntime: 执行安全 fake 截图；如果没有这行代码，artifact=true 无法证明。
        host_runtime = WindowsScreenshotCaptureRuntime(providers=[_Phase45ContractProvider("win32_gdi_printwindow", True)], evidence_root=Path(raw_dir) / "host", platform="win32")  # 新增代码+Phase45WindowsScreenshotRuntime: 准备 host 专用运行时；如果没有这行代码，host_capture=true 没有独立证据。
        host = WindowsComputerUseNativeHost(platform="win32", screenshot_runtime=host_runtime)  # 新增代码+Phase45WindowsScreenshotRuntime: 注入截图运行时到 native host；如果没有这行代码，Phase44 capture 不会走 Phase45 链路。
        host_capture = InProcessWindowsNativeHostClient(host).request({"op": "capture", "window": window})  # 新增代码+Phase45WindowsScreenshotRuntime: 通过 host capture 消息执行截图；如果没有这行代码，host 集成不会被验收。
        artifact = bool(capture.get("screenshot_path") and Path(str(capture.get("screenshot_path"))).exists())  # 新增代码+Phase45WindowsScreenshotRuntime: 检查截图 artifact 真实存在；如果没有这行代码，OK token 可能只证明字典字段存在。
        fallback = bool(capture.get("provider") == "win32_gdi_printwindow" and len(capture.get("provider_attempts", [])) >= 2)  # 新增代码+Phase45WindowsScreenshotRuntime: 检查 fallback 确实发生；如果没有这行代码，首选失败后可能没有走 GDI。
        host_result = host_capture.get("result", {}) if isinstance(host_capture, dict) else {}  # 新增代码+Phase45WindowsScreenshotRuntime: 提取 host capture 结果；如果没有这行代码，host_capture=true 无法稳定判断。
        raw_bytes_hidden = bool(capture.get("screenshot_bytes_included") is False and host_result.get("screenshot_bytes_included") is False)  # 新增代码+Phase45WindowsScreenshotRuntime: 检查直接 runtime 和 host 都不返回原始 bytes；如果没有这行代码，IPC 泄露风险无法验收。
        return {"marker": PHASE45_WINDOWS_SCREENSHOT_RUNTIME_MARKER, "ok_token": PHASE45_WINDOWS_SCREENSHOT_RUNTIME_OK_TOKEN, "capture": bool(capture.get("captured")), "artifact": artifact, "fallback": fallback, "host_capture": bool(host_capture.get("ok") and host_result.get("captured")), "raw_bytes_hidden": raw_bytes_hidden, "actions_expanded": PHASE45_ACTIONS_EXPANDED, "capture_result": capture, "host_capture_result": host_capture}  # 新增代码+Phase45WindowsScreenshotRuntime: 返回完整自检报告；如果没有这行代码，CLI 和测试拿不到统一结果。
# 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，run_phase45_screenshot_runtime_contract 到此结束；如果没有这个边界说明，读者不容易看出自检范围。


def phase45_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，把自检报告转为稳定 token 行；如果没有这段函数，验收场景要解析完整 JSON。
    return f"{PHASE45_WINDOWS_SCREENSHOT_RUNTIME_MARKER} {PHASE45_WINDOWS_SCREENSHOT_RUNTIME_OK_TOKEN} capture={_phase45_bool_token(report.get('capture'))} artifact={_phase45_bool_token(report.get('artifact'))} fallback={_phase45_bool_token(report.get('fallback'))} host_capture={_phase45_bool_token(report.get('host_capture'))} raw_bytes_hidden={_phase45_bool_token(report.get('raw_bytes_hidden'))} actions_expanded={_phase45_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase45WindowsScreenshotRuntime: 返回固定顺序验收行；如果没有这行代码，debug log token 容易漂移。
# 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，phase45_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 格式范围。


def main() -> int:  # 新增代码+Phase45WindowsScreenshotRuntime: 函数段开始，提供命令行自检入口；如果没有这段函数，真实终端无法执行 Phase45 验收命令。
    report = run_phase45_screenshot_runtime_contract()  # 新增代码+Phase45WindowsScreenshotRuntime: 运行安全自检；如果没有这行代码，CLI 没有真实报告。
    print(PHASE45_WINDOWS_SCREENSHOT_RUNTIME_MARKER)  # 新增代码+Phase45WindowsScreenshotRuntime: 打印 ready marker；如果没有这行代码，验收控制器可能等不到阶段标记。
    print(phase45_cli_line(report))  # 新增代码+Phase45WindowsScreenshotRuntime: 打印固定 token 行；如果没有这行代码，debug log 无法确认通过。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase45WindowsScreenshotRuntime: 打印结构化报告；如果没有这行代码，失败时不易复盘。
    return 0 if bool(report.get("capture") and report.get("artifact") and report.get("fallback") and report.get("host_capture") and report.get("raw_bytes_hidden") and report.get("actions_expanded") is False) else 1  # 新增代码+Phase45WindowsScreenshotRuntime: 根据自检布尔值返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase45WindowsScreenshotRuntime: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出命令入口范围。


if __name__ == "__main__":  # 新增代码+Phase45WindowsScreenshotRuntime: 允许直接运行模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase45WindowsScreenshotRuntime: 用 main 的返回码退出；如果没有这行代码，命令行状态不稳定。
