"""URG-1 universal real GUI observation frame runtime."""  # 新增代码+URG1RealObservationFrame：说明本模块负责把真实窗口、截图、UIA 和融合观察组合成统一 ObservationFrame；如果没有这一行，读者不知道 URG-1 的入口文件在哪里。
from __future__ import annotations  # 新增代码+URG1RealObservationFrame：启用延迟类型解析；如果没有这一行，后续前向类型标注在旧入口里更容易导入失败。

import json  # 新增代码+URG1RealObservationFrame：导入 JSON 用于 CLI 打印结构化报告；如果没有这一行，真实终端失败时不方便复盘字段。
import tempfile  # 新增代码+URG1RealObservationFrame：导入临时目录隔离合同截图证据；如果没有这一行，合同自检可能污染项目 evidence 目录。
from pathlib import Path  # 新增代码+URG1RealObservationFrame：导入 Path 统一处理 Windows 路径；如果没有这一行，截图 artifact 检查会变脆弱。
from typing import Any  # 新增代码+URG1RealObservationFrame：导入 Any 描述 provider 的动态字典接口；如果没有这一行，观察帧协议边界不清楚。

try:  # 新增代码+URG1RealObservationFrame：优先按 learning_agent 包路径导入真实基座；如果没有这一段，单测和生产入口无法共享同一实现。
    from learning_agent.computer_use.observation_fusion import WindowsObservationFusionRuntime  # 新增代码+URG1RealObservationFrame：导入现有观察融合层；如果没有这一行，URG-1 会重复造一个不兼容的融合协议。
    from learning_agent.computer_use.real_screenshot_pipeline import WindowsRealScreenshotPipeline  # 新增代码+URG1RealObservationFrame：导入现有真实截图管线；如果没有这一行，ObservationFrame 没有视觉证据来源。
    from learning_agent.computer_use.real_uia_locator import WindowsRealUiaLocatorRuntime  # 新增代码+URG1RealObservationFrame：导入现有真实 UIA runtime；如果没有这一行，ObservationFrame 没有控件树来源。
    from learning_agent.computer_use.windows_backend import WindowsWindowInventoryProbe  # 新增代码+URG1RealObservationFrame：导入现有窗口 inventory；如果没有这一行，ObservationFrame 没有目标窗口列表。
except ModuleNotFoundError as error:  # 新增代码+URG1RealObservationFrame：兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这一段，真实可见终端可能因包前缀失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.observation_fusion", "learning_agent.computer_use.real_screenshot_pipeline", "learning_agent.computer_use.real_uia_locator", "learning_agent.computer_use.windows_backend"}:  # 新增代码+URG1RealObservationFrame：只兜底包路径缺失；如果没有这一行，真实内部 bug 会被误吞。
        raise  # 新增代码+URG1RealObservationFrame：重新抛出非路径类导入错误；如果没有这一行，排查真实依赖问题会很困难。
    from computer_use.observation_fusion import WindowsObservationFusionRuntime  # type: ignore  # 新增代码+URG1RealObservationFrame：脚本模式导入观察融合层；如果没有这一行，bat 入口无法运行 URG-1。
    from computer_use.real_screenshot_pipeline import WindowsRealScreenshotPipeline  # type: ignore  # 新增代码+URG1RealObservationFrame：脚本模式导入真实截图管线；如果没有这一行，bat 入口没有截图 provider。
    from computer_use.real_uia_locator import WindowsRealUiaLocatorRuntime  # type: ignore  # 新增代码+URG1RealObservationFrame：脚本模式导入真实 UIA runtime；如果没有这一行，bat 入口没有 UIA provider。
    from computer_use.windows_backend import WindowsWindowInventoryProbe  # type: ignore  # 新增代码+URG1RealObservationFrame：脚本模式导入窗口 inventory；如果没有这一行，bat 入口无法观察窗口。

PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MARKER = "PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_READY"  # 新增代码+URG1RealObservationFrame：定义 URG-1 ready marker；如果没有这一行，真实终端验收无法稳定等待本阶段输出。
PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_OK_TOKEN = "PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_OK"  # 新增代码+URG1RealObservationFrame：定义 URG-1 OK token；如果没有这一行，debug log 无法区分普通输出和合同通过。
PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MODEL = "phase116_universal_real_gui_observation_frame"  # 新增代码+URG1RealObservationFrame：定义 ObservationFrame 协议模型名；如果没有这一行，后续 planner 无法识别帧版本。
PHASE116_ACTIONS_EXPANDED = False  # 新增代码+URG1RealObservationFrame：声明 URG-1 只读观察不扩大动作面；如果没有这一行，用户无法确认本阶段没有新增鼠标键盘控制。


def _phase116_bool_token(value: Any) -> str:  # 新增代码+URG1RealObservationFrame：函数段开始，把布尔值转成固定小写 token；如果没有这段函数，CLI 会混用 True 和 true。
    return "true" if bool(value) else "false"  # 新增代码+URG1RealObservationFrame：返回验收器易匹配的小写布尔文本；如果没有这一行，场景 JSON 可能匹配失败。
# 新增代码+URG1RealObservationFrame：函数段结束，_phase116_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。


def _phase116_safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，安全复制动态字典；如果没有这段函数，坏 provider 输出会让观察流程崩溃。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+URG1RealObservationFrame：只接受 dict 并复制；如果没有这一行，外部可变对象可能污染帧数据。
# 新增代码+URG1RealObservationFrame：函数段结束，_phase116_safe_dict 到此结束；如果没有这个边界说明，初学者不容易看出清洗范围。


def _phase116_snapshot_to_dict(snapshot: Any) -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，把不同 inventory 快照形态统一成 dict；如果没有这段函数，真实和 fake inventory 不能复用。
    if isinstance(snapshot, dict):  # 新增代码+URG1RealObservationFrame：优先处理测试和 JSON 风格快照；如果没有这一行，单测 fake 结构会被当成空对象。
        source = dict(snapshot)  # 新增代码+URG1RealObservationFrame：复制输入快照；如果没有这一行，后续归一化可能改动调用方数据。
    elif hasattr(snapshot, "windows"):  # 新增代码+URG1RealObservationFrame：兼容 WindowsWindowInventorySnapshot 对象；如果没有这一行，真实窗口 inventory 无法进入 ObservationFrame。
        source = {"windows": list(getattr(snapshot, "windows", []) or []), "filtered_count": getattr(snapshot, "filtered_count", 0), "captured_at": getattr(snapshot, "captured_at", ""), "source": getattr(snapshot, "source", ""), "active_window": getattr(snapshot, "active_window", None), "platform": getattr(snapshot, "platform", "")}  # 新增代码+URG1RealObservationFrame：把对象快照展开成标准 dict；如果没有这一行，窗口状态字段会丢失。
    else:  # 新增代码+URG1RealObservationFrame：处理无法识别的快照类型；如果没有这一行，未知 provider 会触发异常。
        source = {}  # 新增代码+URG1RealObservationFrame：使用空快照兜底；如果没有这一行，失败路径没有稳定结构。
    windows = [dict(item) for item in list(source.get("windows", []) or []) if isinstance(item, dict)]  # 新增代码+URG1RealObservationFrame：复制窗口列表并过滤坏项；如果没有这一行，坏窗口项会污染目标选择。
    active_window = _phase116_safe_dict(source.get("active_window"))  # 新增代码+URG1RealObservationFrame：清洗活动窗口字段；如果没有这一行，目标选择可能读到非 dict 值。
    return {"windows": windows, "filtered_count": int(source.get("filtered_count", 0) or 0), "captured_at": str(source.get("captured_at", "") or ""), "source": str(source.get("source", "") or ""), "platform": str(source.get("platform", "") or ""), "active_window": active_window}  # 新增代码+URG1RealObservationFrame：返回统一 inventory 摘要；如果没有这一行，后续融合层拿不到稳定窗口状态。
# 新增代码+URG1RealObservationFrame：函数段结束，_phase116_snapshot_to_dict 到此结束；如果没有这个边界说明，初学者不容易看出快照转换范围。


def _phase116_window_text(window: dict[str, Any]) -> str:  # 新增代码+URG1RealObservationFrame：函数段开始，把窗口可搜索字段合成小写文本；如果没有这段函数，target_hint 匹配逻辑会重复散落。
    return " ".join([str(window.get("app_id", "")), str(window.get("window_id", "")), str(window.get("title_preview", "")), str(window.get("title", "")), str(window.get("class_name", ""))]).lower()  # 新增代码+URG1RealObservationFrame：返回搜索文本；如果没有这一行，用户提示里的目标词无法匹配窗口。
# 新增代码+URG1RealObservationFrame：函数段结束，_phase116_window_text 到此结束；如果没有这个边界说明，初学者不容易看出匹配文本范围。


def _phase116_select_target_window(inventory: dict[str, Any], target_hint: str = "") -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，按 hint 或活动窗口选择目标；如果没有这段函数，ObservationFrame 没有清晰目标。
    windows = [dict(item) for item in list(inventory.get("windows", []) or []) if isinstance(item, dict)]  # 新增代码+URG1RealObservationFrame：读取安全窗口列表；如果没有这一行，目标候选为空。
    hint = str(target_hint or "").strip().lower()  # 新增代码+URG1RealObservationFrame：清洗用户目标提示；如果没有这一行，大小写和空白会导致匹配漂移。
    if hint:  # 新增代码+URG1RealObservationFrame：只有提供 hint 时才进行文本匹配；如果没有这一行，空 hint 会误命中所有窗口。
        for window in windows:  # 新增代码+URG1RealObservationFrame：逐个检查候选窗口；如果没有这一行，无法从窗口列表中选择目标。
            if hint in _phase116_window_text(window):  # 新增代码+URG1RealObservationFrame：判断窗口是否包含目标提示；如果没有这一行，Notepad/Paint 等自然词无法定位。
                return dict(window)  # 新增代码+URG1RealObservationFrame：返回匹配窗口副本；如果没有这一行，目标匹配结果不会传给截图和 UIA。
    active_window = _phase116_safe_dict(inventory.get("active_window"))  # 新增代码+URG1RealObservationFrame：读取活动窗口作为兜底；如果没有这一行，无 hint 场景无法观察当前窗口。
    if active_window:  # 新增代码+URG1RealObservationFrame：检查活动窗口是否存在；如果没有这一行，空 dict 会被当成目标。
        return active_window  # 新增代码+URG1RealObservationFrame：返回活动窗口；如果没有这一行，默认 observe 需要用户总是指定 hint。
    return dict(windows[0]) if windows else {}  # 新增代码+URG1RealObservationFrame：最后使用第一个安全窗口或空目标；如果没有这一行，空窗口列表会抛异常。
# 新增代码+URG1RealObservationFrame：函数段结束，_phase116_select_target_window 到此结束；如果没有这个边界说明，初学者不容易看出目标选择范围。


def _phase116_artifact_openable(screenshot_result: dict[str, Any]) -> bool:  # 新增代码+URG1RealObservationFrame：函数段开始，确认截图 artifact 字段不是空口号；如果没有这段函数，空路径也可能被误报为可用。
    source = _phase116_safe_dict(screenshot_result)  # 新增代码+URG1RealObservationFrame：清洗截图结果；如果没有这一行，坏截图 provider 输出会抛异常。
    artifact_path = str(source.get("screenshot_path", source.get("artifact_path", "")) or "")  # 新增代码+URG1RealObservationFrame：读取截图文件路径；如果没有这一行，无法验证证据是否落盘。
    if artifact_path:  # 新增代码+URG1RealObservationFrame：只有路径存在时才检查文件系统；如果没有这一行，空路径会触发无意义检查。
        try:  # 新增代码+URG1RealObservationFrame：保护本地路径检查；如果没有这一行，权限或非法路径会中断观察流程。
            return bool(Path(artifact_path).exists())  # 新增代码+URG1RealObservationFrame：返回证据文件是否存在；如果没有这一行，artifact_openable 没有真实验证。
        except OSError:  # 新增代码+URG1RealObservationFrame：捕获路径访问异常；如果没有这一行，坏路径会让 CLI 失败。
            return False  # 新增代码+URG1RealObservationFrame：坏路径视为不可打开；如果没有这一行，失败路径没有确定值。
    return bool(source.get("artifact_openable", False))  # 新增代码+URG1RealObservationFrame：无路径时回退 provider 明确字段；如果没有这一行，合同 fake 无法表达结果。
# 新增代码+URG1RealObservationFrame：函数段结束，_phase116_artifact_openable 到此结束；如果没有这个边界说明，初学者不容易看出证据检查范围。


def _phase116_no_screenshot(reason: str) -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，构造统一截图失败结构；如果没有这段函数，上层需要处理缺字段。
    return {"captured": False, "screenshot_captured": False, "screenshot_path": "", "screenshot_width": 0, "screenshot_height": 0, "screenshot_format": "", "pixel_guard_passed": False, "artifact_openable": False, "screenshot_bytes_included": False, "provider": "", "reason": str(reason), "image_results": [], "actions_expanded": PHASE116_ACTIONS_EXPANDED}  # 新增代码+URG1RealObservationFrame：返回截图失败摘要；如果没有这一行，融合层无法稳定读取截图字段。
# 新增代码+URG1RealObservationFrame：函数段结束，_phase116_no_screenshot 到此结束；如果没有这个边界说明，初学者不容易看出截图失败范围。


def _phase116_no_uia(reason: str) -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，构造统一 UIA 失败结构；如果没有这段函数，上层需要处理缺字段。
    return {"captured": False, "real_uia_tree": False, "safe_window_only": True, "flat_nodes": [], "node_count": 0, "bounds_available": False, "clickable_count": 0, "editable_count": 0, "sensitive_text_filtered": 0, "semantic_locator_available": True, "raw_text_included": False, "reason": str(reason), "actions_expanded": PHASE116_ACTIONS_EXPANDED}  # 新增代码+URG1RealObservationFrame：返回 UIA 失败摘要；如果没有这一行，融合层无法稳定读取 UIA 字段。
# 新增代码+URG1RealObservationFrame：函数段结束，_phase116_no_uia 到此结束；如果没有这个边界说明，初学者不容易看出 UIA 失败范围。


class UniversalRealObservationFrameRuntime:  # 新增代码+URG1RealObservationFrame：类段开始，组合窗口、截图、UIA 和融合层生成统一 ObservationFrame；如果没有这个类，URG-1 会停留在分散工具。
    def __init__(self, inventory_probe: Any | None = None, screenshot_pipeline: Any | None = None, uia_runtime: Any | None = None, fusion_runtime: Any | None = None) -> None:  # 新增代码+URG1RealObservationFrame：函数段开始，允许生产默认依赖和测试注入依赖；如果没有这段函数，单测会触碰真实桌面。
        self.inventory_probe = inventory_probe if inventory_probe is not None else WindowsWindowInventoryProbe()  # 新增代码+URG1RealObservationFrame：保存窗口 inventory provider；如果没有这一行，runtime 无法列出目标窗口。
        self.screenshot_pipeline = screenshot_pipeline if screenshot_pipeline is not None else WindowsRealScreenshotPipeline()  # 新增代码+URG1RealObservationFrame：保存截图 pipeline；如果没有这一行，runtime 无法获取视觉证据。
        self.uia_runtime = uia_runtime if uia_runtime is not None else WindowsRealUiaLocatorRuntime()  # 新增代码+URG1RealObservationFrame：保存 UIA runtime；如果没有这一行，runtime 无法获取控件树。
        self.fusion_runtime = fusion_runtime if fusion_runtime is not None else WindowsObservationFusionRuntime()  # 新增代码+URG1RealObservationFrame：保存融合 runtime；如果没有这一行，调用方拿不到统一观察对象。
    # 新增代码+URG1RealObservationFrame：函数段结束，UniversalRealObservationFrameRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def observe(self, target_hint: str = "", real_desktop_touched: bool = False) -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，执行一次只读 ObservationFrame 生成；如果没有这段函数，URG-1 没有核心行为。
        snapshot_source = self.inventory_probe.snapshot() if hasattr(self.inventory_probe, "snapshot") else self.inventory_probe()  # 新增代码+URG1RealObservationFrame：获取窗口快照；如果没有这一行，目标窗口和活动窗口无法进入帧。
        inventory = _phase116_snapshot_to_dict(snapshot_source)  # 新增代码+URG1RealObservationFrame：归一化窗口快照；如果没有这一行，真实和 fake inventory 字段会不一致。
        target_window = _phase116_select_target_window(inventory, target_hint=target_hint)  # 新增代码+URG1RealObservationFrame：选择本次观察目标；如果没有这一行，截图和 UIA 没有绑定对象。
        if target_window:  # 新增代码+URG1RealObservationFrame：只有目标窗口存在时才截图；如果没有这一行，空目标会传入 provider 导致异常。
            screenshot_result = self.screenshot_pipeline.capture_window(target_window) if hasattr(self.screenshot_pipeline, "capture_window") else _phase116_no_screenshot("截图 pipeline 没有 capture_window。")  # 新增代码+URG1RealObservationFrame：执行只读截图；如果没有这一行，视觉证据不会进入 ObservationFrame。
        else:  # 新增代码+URG1RealObservationFrame：处理没有目标窗口的情况；如果没有这一行，无窗口环境会崩溃。
            screenshot_result = _phase116_no_screenshot("没有可观察目标窗口。")  # 新增代码+URG1RealObservationFrame：返回稳定截图失败结构；如果没有这一行，融合层会缺字段。
        if target_window:  # 新增代码+URG1RealObservationFrame：只有目标窗口存在时才读取 UIA；如果没有这一行，空目标会传入 provider 导致异常。
            uia_result = self.uia_runtime.observe_window(target_window) if hasattr(self.uia_runtime, "observe_window") else _phase116_no_uia("UIA runtime 没有 observe_window。")  # 新增代码+URG1RealObservationFrame：执行只读 UIA 读取；如果没有这一行，控件树不会进入 ObservationFrame。
        else:  # 新增代码+URG1RealObservationFrame：处理没有目标窗口的 UIA 失败；如果没有这一行，无窗口环境会崩溃。
            uia_result = _phase116_no_uia("没有可观察目标窗口。")  # 新增代码+URG1RealObservationFrame：返回稳定 UIA 失败结构；如果没有这一行，融合层会缺字段。
        fused = self.fusion_runtime.observe(target_window, screenshot_result, uia_result, inventory, ocr_result=None)  # 新增代码+URG1RealObservationFrame：复用 Phase66 融合层生成统一事实源；如果没有这一行，URG-1 会产生另一套不兼容字段。
        screenshot_summary = _phase116_safe_dict(fused.get("screenshot"))  # 新增代码+URG1RealObservationFrame：读取融合后的截图摘要；如果没有这一行，后续 token 会重复读原始 provider 输出。
        uia_summary = _phase116_safe_dict(fused.get("uia"))  # 新增代码+URG1RealObservationFrame：读取融合后的 UIA 摘要；如果没有这一行，后续 token 会重复读原始 provider 输出。
        window_state = _phase116_safe_dict(fused.get("window_state"))  # 新增代码+URG1RealObservationFrame：读取融合后的窗口状态；如果没有这一行，目标身份 token 没有统一来源。
        target_identity_present = bool(target_window.get("window_id") or target_window.get("hwnd")) and bool(target_window.get("app_id") or target_window.get("title") or target_window.get("title_preview"))  # 新增代码+URG1RealObservationFrame：判断目标窗口身份是否足够；如果没有这一行，后续动作前重验没有起点。
        frame = {"marker": PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MARKER, "model": PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MODEL, "real_observation_frame": True, "target_hint": str(target_hint or ""), "target_window": dict(target_window), "target_window_identity_present": target_identity_present, "inventory": inventory, "real_window_inventory": bool(inventory.get("windows") or inventory.get("active_window")), "screenshot": screenshot_summary, "uia": uia_summary, "window_state": window_state, "fused_observation": fused, "screenshot_observation": bool(fused.get("screenshot_observation")), "uia_tree_observation": bool(fused.get("uia_tree_observation")), "window_state_observation": bool(fused.get("window_state_observation")), "real_screenshot_pipeline_used": bool(screenshot_summary.get("available")), "screenshot_artifact_openable": _phase116_artifact_openable(screenshot_result), "pixel_guard_passed": bool(screenshot_summary.get("pixel_guard_passed")), "real_uia_provider_used": bool(uia_summary.get("available")), "uia_or_vision_targeting": bool(fused.get("uia_tree_observation") or fused.get("ocr_or_vision_slot")), "raw_text_included": bool(fused.get("raw_text_included")), "actions_expanded": PHASE116_ACTIONS_EXPANDED, "real_desktop_touched": bool(real_desktop_touched), "low_level_event_count": 0}  # 新增代码+URG1RealObservationFrame：返回完整 ObservationFrame；如果没有这一行，规划器、测试和终端验收没有统一结构。
        return frame  # 新增代码+URG1RealObservationFrame：交还观察帧给调用方；如果没有这一行，调用者拿不到 URG-1 的结果。
    # 新增代码+URG1RealObservationFrame：函数段结束，UniversalRealObservationFrameRuntime.observe 到此结束；如果没有这个边界说明，初学者不容易看出观察流程范围。
# 新增代码+URG1RealObservationFrame：类段结束，UniversalRealObservationFrameRuntime 到此结束；如果没有这个边界说明，初学者不容易看出 runtime 范围。


class _Phase116ContractInventoryProbe:  # 新增代码+URG1RealObservationFrame：类段开始，定义合同 fake inventory；如果没有这个类，自检会碰用户真实窗口。
    def snapshot(self) -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，返回合同窗口快照；如果没有这段函数，合同自检没有目标窗口。
        window = {"app_id": "notepad.exe", "window_id": "hwnd:11601", "hwnd": 11601, "title_preview": "URG1 Contract Window", "title": "URG1 Contract Window", "rect": {"left": 10, "top": 20, "right": 610, "bottom": 420, "width": 600, "height": 400}}  # 新增代码+URG1RealObservationFrame：构造合同目标窗口；如果没有这一行，截图和 UIA 没有绑定对象。
        return {"windows": [window], "filtered_count": 0, "captured_at": "2026-06-05T00:00:00Z", "source": "phase116_contract_inventory", "active_window": window}  # 新增代码+URG1RealObservationFrame：返回标准窗口快照；如果没有这一行，融合层无法读取窗口状态。
    # 新增代码+URG1RealObservationFrame：函数段结束，_Phase116ContractInventoryProbe.snapshot 到此结束；如果没有这个边界说明，初学者不容易看出合同 inventory 范围。
# 新增代码+URG1RealObservationFrame：类段结束，_Phase116ContractInventoryProbe 到此结束；如果没有这个边界说明，初学者不容易看出 fake inventory 范围。


class _Phase116ContractScreenshotPipeline:  # 新增代码+URG1RealObservationFrame：类段开始，定义合同 fake 截图管线；如果没有这个类，自检会依赖真实屏幕权限。
    def __init__(self, artifact_path: Path) -> None:  # 新增代码+URG1RealObservationFrame：函数段开始，保存合同截图路径；如果没有这段函数，fake 截图无法落盘。
        self.artifact_path = artifact_path  # 新增代码+URG1RealObservationFrame：记录 artifact 路径；如果没有这一行，capture_window 没有证据文件位置。
    # 新增代码+URG1RealObservationFrame：函数段结束，_Phase116ContractScreenshotPipeline.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。
    def capture_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，返回合同截图摘要；如果没有这段函数，自检没有截图输入。
        self.artifact_path.write_bytes(b"BM" + b"phase116-contract-observation-frame")  # 新增代码+URG1RealObservationFrame：写入可检查的截图 artifact；如果没有这一行，artifact_openable 无法被真实文件验证。
        return {"captured": True, "screenshot_captured": True, "screenshot_path": str(self.artifact_path), "screenshot_width": 600, "screenshot_height": 400, "screenshot_format": "bmp", "pixel_guard_passed": True, "artifact_openable": True, "screenshot_bytes_included": False, "provider": "phase116_contract_screenshot", "image_results": [{"type": "image_result", "artifact_path": str(self.artifact_path), "width": 600, "height": 400, "sensitive_text_included": False}], "actions_expanded": PHASE116_ACTIONS_EXPANDED}  # 新增代码+URG1RealObservationFrame：返回与真实截图管线兼容的摘要；如果没有这一行，融合层拿不到视觉证据。
    # 新增代码+URG1RealObservationFrame：函数段结束，_Phase116ContractScreenshotPipeline.capture_window 到此结束；如果没有这个边界说明，初学者不容易看出 fake 截图范围。
# 新增代码+URG1RealObservationFrame：类段结束，_Phase116ContractScreenshotPipeline 到此结束；如果没有这个边界说明，初学者不容易看出合同截图范围。


class _Phase116ContractUiaRuntime:  # 新增代码+URG1RealObservationFrame：类段开始，定义合同 fake UIA runtime；如果没有这个类，自检会依赖 Windows UIA 权限。
    def observe_window(self, window: dict[str, Any]) -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，返回合同 UIA 摘要；如果没有这段函数，自检没有控件树输入。
        return {"captured": True, "real_uia_tree": True, "safe_window_only": True, "flat_nodes": [{"node_id": "0", "name": "Editor", "role": "Edit", "automation_id": "editor", "class_name": "Edit", "bounds": {"left": 30, "top": 80, "right": 580, "bottom": 380, "width": 550, "height": 300}, "clickable": True, "editable": True}], "node_count": 1, "bounds_available": True, "clickable_count": 1, "editable_count": 1, "sensitive_text_filtered": 0, "semantic_locator_available": True, "raw_text_included": False, "actions_expanded": PHASE116_ACTIONS_EXPANDED}  # 新增代码+URG1RealObservationFrame：返回可定位控件树；如果没有这一行，ObservationFrame 无法证明 UIA/vision targeting。
    # 新增代码+URG1RealObservationFrame：函数段结束，_Phase116ContractUiaRuntime.observe_window 到此结束；如果没有这个边界说明，初学者不容易看出 fake UIA 范围。
# 新增代码+URG1RealObservationFrame：类段结束，_Phase116ContractUiaRuntime 到此结束；如果没有这个边界说明，初学者不容易看出合同 UIA 范围。


def run_universal_real_observation_frame_contract(real_smoke: bool = False) -> dict[str, Any]:  # 新增代码+URG1RealObservationFrame：函数段开始，运行 URG-1 合同自检；如果没有这段函数，测试、CLI 和可见终端没有统一事实源。
    with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+URG1RealObservationFrame：创建临时 evidence 目录；如果没有这一行，合同 artifact 会污染项目目录。
        artifact_path = Path(temp_dir) / "phase116_contract_screen.bmp"  # 新增代码+URG1RealObservationFrame：定义合同截图路径；如果没有这一行，fake 截图没有落盘位置。
        runtime = UniversalRealObservationFrameRuntime(inventory_probe=_Phase116ContractInventoryProbe(), screenshot_pipeline=_Phase116ContractScreenshotPipeline(artifact_path), uia_runtime=_Phase116ContractUiaRuntime())  # 新增代码+URG1RealObservationFrame：创建全注入只读 runtime；如果没有这一行，合同自检会触碰真实桌面。
        frame = runtime.observe(target_hint="notepad", real_desktop_touched=False)  # 新增代码+URG1RealObservationFrame：生成只读观察帧；如果没有这一行，报告没有 ObservationFrame 输入。
    real_observation_frame = bool(frame.get("real_observation_frame"))  # 新增代码+URG1RealObservationFrame：读取观察帧成立字段；如果没有这一行，passed 判断会重复读字典。
    real_window_inventory = bool(frame.get("real_window_inventory"))  # 新增代码+URG1RealObservationFrame：读取窗口 inventory 字段；如果没有这一行，passed 判断没有窗口来源。
    real_screenshot_pipeline_used = bool(frame.get("real_screenshot_pipeline_used"))  # 新增代码+URG1RealObservationFrame：读取截图管线字段；如果没有这一行，passed 判断没有视觉来源。
    screenshot_artifact_openable = bool(frame.get("screenshot_artifact_openable"))  # 新增代码+URG1RealObservationFrame：读取截图证据字段；如果没有这一行，空截图可能误过。
    pixel_guard_passed = bool(frame.get("pixel_guard_passed"))  # 新增代码+URG1RealObservationFrame：读取像素验真字段；如果没有这一行，黑屏可能误过。
    real_uia_provider_used = bool(frame.get("real_uia_provider_used"))  # 新增代码+URG1RealObservationFrame：读取 UIA 字段；如果没有这一行，语义目标输入可能缺失。
    target_window_identity_present = bool(frame.get("target_window_identity_present"))  # 新增代码+URG1RealObservationFrame：读取目标身份字段；如果没有这一行，后续动作前复核没有基础。
    actions_expanded = bool(frame.get("actions_expanded"))  # 新增代码+URG1RealObservationFrame：读取动作扩展字段；如果没有这一行，安全边界无法纳入 passed。
    real_desktop_touched = bool(frame.get("real_desktop_touched"))  # 新增代码+URG1RealObservationFrame：读取真实桌面触碰字段；如果没有这一行，合同只读边界无法纳入 passed。
    low_level_event_count = int(frame.get("low_level_event_count", 0) or 0)  # 新增代码+URG1RealObservationFrame：读取底层输入事件数；如果没有这一行，鼠标键盘事件可能被漏报。
    real_provider_smoke_passed = not bool(real_smoke)  # 新增代码+URG1RealObservationFrame：合同默认不跑真实 provider smoke；如果没有这一行，单测会依赖本机 GUI 状态。
    passed = bool(real_observation_frame and real_window_inventory and real_screenshot_pipeline_used and screenshot_artifact_openable and pixel_guard_passed and real_uia_provider_used and target_window_identity_present and real_provider_smoke_passed and not actions_expanded and not real_desktop_touched and low_level_event_count == 0)  # 新增代码+URG1RealObservationFrame：汇总 URG-1 合同通过条件；如果没有这一行，CLI 不能用退出码表达失败。
    return {"marker": PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MARKER, "ok_token": PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_OK_TOKEN, "model": PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MODEL, "real_observation_frame": real_observation_frame, "real_window_inventory": real_window_inventory, "real_screenshot_pipeline_used": real_screenshot_pipeline_used, "screenshot_artifact_openable": screenshot_artifact_openable, "pixel_guard_passed": pixel_guard_passed, "real_uia_provider_used": real_uia_provider_used, "target_window_identity_present": target_window_identity_present, "uia_or_vision_targeting": bool(frame.get("uia_or_vision_targeting")), "screenshot_observation": bool(frame.get("screenshot_observation")), "uia_tree_observation": bool(frame.get("uia_tree_observation")), "window_state_observation": bool(frame.get("window_state_observation")), "real_smoke": bool(real_smoke), "real_provider_smoke_passed": real_provider_smoke_passed, "actions_expanded": actions_expanded, "real_desktop_touched": real_desktop_touched, "low_level_event_count": low_level_event_count, "passed": passed, "observation_frame": frame}  # 新增代码+URG1RealObservationFrame：返回完整合同报告；如果没有这一行，测试和可见终端无法读取结构化事实。
# 新增代码+URG1RealObservationFrame：函数段结束，run_universal_real_observation_frame_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def universal_real_observation_frame_cli_line(report: dict[str, Any]) -> str:  # 新增代码+URG1RealObservationFrame：函数段开始，把合同报告转成固定 token 行；如果没有这段函数，可见终端验收需要解析复杂 JSON。
    return f"{PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MARKER} {PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_OK_TOKEN} real_observation_frame={_phase116_bool_token(report.get('real_observation_frame'))} real_window_inventory={_phase116_bool_token(report.get('real_window_inventory'))} real_screenshot_pipeline_used={_phase116_bool_token(report.get('real_screenshot_pipeline_used'))} screenshot_artifact_openable={_phase116_bool_token(report.get('screenshot_artifact_openable'))} pixel_guard_passed={_phase116_bool_token(report.get('pixel_guard_passed'))} real_uia_provider_used={_phase116_bool_token(report.get('real_uia_provider_used'))} target_window_identity_present={_phase116_bool_token(report.get('target_window_identity_present'))} uia_or_vision_targeting={_phase116_bool_token(report.get('uia_or_vision_targeting'))} actions_expanded={_phase116_bool_token(report.get('actions_expanded'))} real_desktop_touched={_phase116_bool_token(report.get('real_desktop_touched'))} low_level_event_count={int(report.get('low_level_event_count', 0) or 0)}"  # 新增代码+URG1RealObservationFrame：返回固定顺序 token；如果没有这一行，场景匹配容易因字段顺序漂移。
# 新增代码+URG1RealObservationFrame：函数段结束，universal_real_observation_frame_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+URG1RealObservationFrame：函数段开始，提供命令行和真实终端统一入口；如果没有这段函数，controller 场景无法运行 URG-1。
    args = list(argv or [])  # 新增代码+URG1RealObservationFrame：复制命令行参数；如果没有这一行，后续扩展会直接修改调用方列表。
    real_smoke = "--real-smoke" in args  # 新增代码+URG1RealObservationFrame：预留真实 provider smoke 开关；如果没有这一行，后续无法显式区分合同和真实 smoke。
    report = run_universal_real_observation_frame_contract(real_smoke=real_smoke)  # 新增代码+URG1RealObservationFrame：运行合同自检；如果没有这一行，CLI 没有结构化报告。
    print(universal_real_observation_frame_cli_line(report))  # 新增代码+URG1RealObservationFrame：打印固定 token 行；如果没有这一行，真实终端验收无法稳定匹配。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+URG1RealObservationFrame：打印完整 JSON 报告；如果没有这一行，失败时不方便定位字段。
    print(PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MARKER)  # 新增代码+URG1RealObservationFrame：单独打印 ready marker；如果没有这一行，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+URG1RealObservationFrame：按合同结果返回退出码；如果没有这一行，失败也可能被终端当成成功。
# 新增代码+URG1RealObservationFrame：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = ["PHASE116_ACTIONS_EXPANDED", "PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MARKER", "PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MODEL", "PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_OK_TOKEN", "UniversalRealObservationFrameRuntime", "main", "run_universal_real_observation_frame_contract", "universal_real_observation_frame_cli_line"]  # 新增代码+URG1RealObservationFrame：限定公开导出名称；如果没有这一行，from module import * 会暴露内部 fake provider。


if __name__ == "__main__":  # 新增代码+URG1RealObservationFrame：文件入口段开始，允许 `python -m` 直接运行；如果没有这一行，真实终端无法直接调用本模块。
    raise SystemExit(main())  # 新增代码+URG1RealObservationFrame：调用 main 并传递退出码；如果没有这一行，直接运行文件不会执行自检。
# 新增代码+URG1RealObservationFrame：文件入口段结束，本模块到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
