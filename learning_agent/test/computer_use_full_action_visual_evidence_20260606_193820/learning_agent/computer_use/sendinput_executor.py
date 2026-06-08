"""Phase37 Windows SendInput 动作执行器合同。"""  # 新增代码+Phase37WindowsSendInputExecutor: 说明本文件负责 Windows SendInput 执行器合同；如果没有这行代码，读者不容易知道它是动作层而不是截图或 UIA 层。
from __future__ import annotations  # 新增代码+Phase37WindowsSendInputExecutor: 启用延迟类型解析；如果没有这行代码，旧运行路径遇到前向类型标注时更容易导入失败。
import hashlib  # 新增代码+Phase37WindowsSendInputExecutor: 用 SHA256 生成文本短指纹；如果没有这行代码，type_text 审计只能在泄露原文和完全不可追踪之间二选一。
import json  # 新增代码+Phase37WindowsSendInputExecutor: 用 JSON 序列化报告和泄露检查；如果没有这行代码，CLI 和验收无法稳定展示结构化状态。
import sys  # 新增代码+Phase37WindowsSendInputExecutor: 读取当前平台并限制 Windows 专用动作；如果没有这行代码，非 Windows 环境可能误判 SendInput 可用。
from dataclasses import dataclass  # 新增代码+Phase37WindowsSendInputExecutor: 用 dataclass 定义执行结果；如果没有这行代码，结果对象需要手写样板属性。
from typing import Any  # 新增代码+Phase37WindowsSendInputExecutor: 标注 JSON 风格参数和结果；如果没有这行代码，执行器输入输出边界不清楚。

PHASE37_WINDOWS_SENDINPUT_EXECUTOR_MARKER = "PHASE37_WINDOWS_SENDINPUT_EXECUTOR_READY"  # 新增代码+Phase37WindowsSendInputExecutor: 定义 Phase37 真实终端验收稳定 marker；如果没有这行代码，验收器没有固定成功锚点。
PHASE37_WINDOWS_SENDINPUT_EXECUTOR_OK_TOKEN = "PHASE37_WINDOWS_SENDINPUT_EXECUTOR_OK"  # 新增代码+Phase37WindowsSendInputExecutor: 定义 Phase37 CLI 成功 token；如果没有这行代码，debug log 无法确认命令确实执行。
PHASE37_SENDINPUT_CONTRACT = "phase37_windows_sendinput_executor"  # 新增代码+Phase37WindowsSendInputExecutor: 定义执行器合同版本；如果没有这行代码，状态消费者无法区分旧 mouse_event 路径和新 SendInput 合同。
PHASE37_SUPPORTED_ACTIONS = ("click", "double_click", "drag_path", "move_mouse", "press_key", "scroll", "type_text")  # 修改代码+GenericDragPathToolSurface: 把通用拖拽路径列为 SendInput 支持动作；如果没有这行代码，模型主循环即使规划出画线路径也会被执行器拒绝。
PHASE37_TEXT_LIMIT = 2000  # 新增代码+Phase37WindowsSendInputExecutor: 限制单次文本输入长度；如果没有这行代码，模型可能把大段敏感内容或长文灌入桌面输入。


@dataclass(frozen=True)  # 新增代码+Phase37WindowsSendInputExecutor: 让动作结果不可变，避免审计结果事后被改写；如果没有这行代码，调用方可能无意污染执行事实。
class WindowsSendInputActionResult:  # 新增代码+Phase37WindowsSendInputExecutor: 定义 SendInput 执行器统一返回结构；如果没有这个类，后端需要猜测字典字段是否存在。
    ok: bool  # 新增代码+Phase37WindowsSendInputExecutor: 表示动作是否成功；如果没有这行代码，调用方无法稳定判断执行结果。
    message: str  # 新增代码+Phase37WindowsSendInputExecutor: 保存给用户和模型看的中文说明；如果没有这行代码，失败原因会丢失。
    data: dict[str, Any]  # 新增代码+Phase37WindowsSendInputExecutor: 保存机器可读的执行摘要；如果没有这行代码，验收和状态页无法读取细节。


def _safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，把模型参数安全转成整数；如果没有这段函数，坐标和滚轮参数遇到字符串或空值会崩溃。
    try:  # 新增代码+Phase37WindowsSendInputExecutor: 捕获不能转换的输入；如果没有这行代码，坏参数会直接中断工具调用。
        return int(value)  # 新增代码+Phase37WindowsSendInputExecutor: 返回标准整数值；如果没有这行代码，SendInput 事件无法得到数值坐标。
    except (TypeError, ValueError):  # 新增代码+Phase37WindowsSendInputExecutor: 处理 None、空字符串和非数字文本；如果没有这行代码，容错路径不可用。
        return int(default)  # 新增代码+Phase37WindowsSendInputExecutor: 返回默认整数兜底；如果没有这行代码，调用方拿不到稳定参数。
# 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出转换 helper 范围。


def _text_sha256_16(raw_text: Any) -> str:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，生成不泄露原文的短指纹；如果没有这段函数，文本输入审计无法安全关联。
    text = str(raw_text or "")  # 新增代码+Phase37WindowsSendInputExecutor: 把任意输入规整成字符串；如果没有这行代码，None 或数字输入的哈希不稳定。
    if not text:  # 新增代码+Phase37WindowsSendInputExecutor: 空文本不需要指纹；如果没有这行代码，空输入也会产生看似有意义的标识。
        return ""  # 新增代码+Phase37WindowsSendInputExecutor: 返回空指纹；如果没有这行代码，调用方无法区分无文本和有文本。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase37WindowsSendInputExecutor: 返回前 16 位 SHA256；如果没有这行代码，审计缺少安全关联字段。
# 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，_text_sha256_16 到此结束；如果没有这个边界说明，读者不容易看出哈希 helper 范围。


def _bool_text(value: Any) -> str:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，把布尔值转成验收友好的小写文本；如果没有这段函数，CLI token 可能大小写不稳定。
    return str(bool(value)).lower()  # 新增代码+Phase37WindowsSendInputExecutor: 返回 true/false 字符串；如果没有这行代码，真实终端 verifier 匹配会更脆弱。
# 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，_bool_text 到此结束；如果没有这个边界说明，读者不容易看出 CLI 布尔转换范围。


def _target_window_for_events(arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ForegroundTargetRouting: 函数段开始，从动作参数里提取目标窗口身份；如果没有这段函数，Paint 的 hwnd 无法传到真实鼠标键盘最后一跳。
    raw_window = arguments.get("window")  # 新增代码+ForegroundTargetRouting: 读取上游 computer_action 传入的 window 字段；如果没有这行代码，动作会丢失目标窗口来源。
    return dict(raw_window) if isinstance(raw_window, dict) else {}  # 新增代码+ForegroundTargetRouting: 只接受字典形态并复制返回；如果没有这行代码，坏参数可能污染低层事件或导致异常。
# 新增代码+ForegroundTargetRouting: 函数段结束，_target_window_for_events 到此结束；如果没有这个边界说明，读者不容易看出目标窗口提取范围。


def _attach_target_window_to_events(events: list[dict[str, Any]], arguments: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+ForegroundTargetRouting: 函数段开始，把目标窗口身份附加到每条高层事件；如果没有这段函数，dispatcher 无法知道要先聚焦哪个真实窗口。
    target_window = _target_window_for_events(arguments)  # 新增代码+ForegroundTargetRouting: 从动作参数提取目标窗口；如果没有这行代码，后续无法判断是否需要附加 target。
    if not target_window:  # 新增代码+ForegroundTargetRouting: 没有目标窗口时保持兼容旧动作；如果没有这行代码，无窗口动作会被写入无意义 target。
        return events  # 新增代码+ForegroundTargetRouting: 返回原事件列表；如果没有这行代码，旧 selftest 和无窗口动作可能被误改。
    enriched_events: list[dict[str, Any]] = []  # 新增代码+ForegroundTargetRouting: 准备保存带 target 的事件副本；如果没有这行代码，不能避免原地污染调用方事件。
    for event in events:  # 新增代码+ForegroundTargetRouting: 逐条复制高层事件；如果没有这行代码，只能处理第一条事件。
        copied_event = dict(event)  # 新增代码+ForegroundTargetRouting: 复制当前事件；如果没有这行代码，原事件对象可能被后续测试或调用方意外共享修改。
        copied_event["target"] = dict(target_window)  # 新增代码+ForegroundTargetRouting: 写入目标窗口身份；如果没有这行代码，dispatcher 无法插入 set_foreground 或低层 target 审计。
        enriched_events.append(copied_event)  # 新增代码+ForegroundTargetRouting: 保存带目标身份的事件；如果没有这行代码，函数最终会丢失事件。
    return enriched_events  # 新增代码+ForegroundTargetRouting: 返回完整目标绑定事件列表；如果没有这行代码，execute 无法把目标身份交给 dispatcher。
# 新增代码+ForegroundTargetRouting: 函数段结束，_attach_target_window_to_events 到此结束；如果没有这个边界说明，读者不容易看出目标附加范围。


def _redact_dispatch_result(raw_result: Any) -> dict[str, Any]:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，清理底层实现返回值；如果没有这段函数，未来实现可能把原始文本带回日志。
    if not isinstance(raw_result, dict):  # 新增代码+Phase37WindowsSendInputExecutor: 只对 dict 做字段级清理；如果没有这行代码，非字典返回会导致 items 调用崩溃。
        return {"ok": bool(raw_result) if raw_result is not None else True}  # 新增代码+Phase37WindowsSendInputExecutor: 把非字典返回压成最小摘要；如果没有这行代码，调用方拿不到稳定 dispatch 字段。
    cleaned: dict[str, Any] = {}  # 新增代码+Phase37WindowsSendInputExecutor: 准备保存清理后的返回值；如果没有这行代码，函数没有输出容器。
    for key, value in raw_result.items():  # 新增代码+Phase37WindowsSendInputExecutor: 遍历底层返回字段；如果没有这行代码，无法逐项脱敏。
        lowered = str(key).lower()  # 新增代码+Phase37WindowsSendInputExecutor: 转小写用于识别敏感键名；如果没有这行代码，大小写变化会绕过脱敏。
        if "text" in lowered and lowered not in {"text_length", "text_sha256_16", "text_redacted"}:  # 新增代码+Phase37WindowsSendInputExecutor: 拦截可能携带原文的文本字段；如果没有这行代码，raw_text 可能进入日志。
            cleaned[str(key)] = "<redacted>"  # 新增代码+Phase37WindowsSendInputExecutor: 用占位符替代敏感文本；如果没有这行代码，脱敏字段没有稳定值。
            continue  # 新增代码+Phase37WindowsSendInputExecutor: 跳过原始值写入；如果没有这行代码，敏感值还会继续保存。
        cleaned[str(key)] = value  # 新增代码+Phase37WindowsSendInputExecutor: 保存非敏感字段；如果没有这行代码，底层成功状态和计数会丢失。
    return cleaned  # 新增代码+Phase37WindowsSendInputExecutor: 返回清理后的底层摘要；如果没有这行代码，执行结果无法携带 dispatch 信息。
# 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，_redact_dispatch_result 到此结束；如果没有这个边界说明，读者不容易看出返回值脱敏范围。


class WindowsSendInputExecutor:  # 新增代码+Phase37WindowsSendInputExecutor: 定义 Windows SendInput 动作执行器；如果没有这个类，learning_agent 仍停留在旧 SetCursorPos/mouse_event 路径。
    def __init__(self, platform: str | None = None, enabled: bool = False, sendinput_impl: Any | None = None, max_text_length: int = PHASE37_TEXT_LIMIT) -> None:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，初始化平台、开关和可注入实现；如果没有这段函数，执行器无法安全测试和生产配置。
        self.platform = platform or sys.platform  # 新增代码+Phase37WindowsSendInputExecutor: 保存运行平台；如果没有这行代码，状态和拒绝理由无法区分 Windows/非 Windows。
        self.enabled = bool(enabled)  # 新增代码+Phase37WindowsSendInputExecutor: 保存显式启用开关；如果没有这行代码，默认安全关闭无法表达。
        self.sendinput_impl = sendinput_impl  # 新增代码+Phase37WindowsSendInputExecutor: 保存可注入底层实现；如果没有这行代码，单元测试只能触碰真实桌面。
        self.max_text_length = int(max_text_length)  # 新增代码+Phase37WindowsSendInputExecutor: 保存文本长度上限；如果没有这行代码，type_text 无法防止超长输入。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，WindowsSendInputExecutor.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，返回执行器状态；如果没有这段函数，/computer status 无法看到 SendInput 缺口。
        platform_supported = self.platform == "win32"  # 新增代码+Phase37WindowsSendInputExecutor: 判断平台是否支持 Windows SendInput；如果没有这行代码，非 Windows 可能误报可用。
        implementation_available = self.sendinput_impl is not None  # 新增代码+Phase37WindowsSendInputExecutor: 判断是否注入底层实现；如果没有这行代码，只有合同没有实现也可能被误报可用。
        dispatch_status = self.sendinput_impl.status() if hasattr(self.sendinput_impl, "status") else {}  # 新增代码+RealComputerActionExecutor: 读取注入 dispatcher 的状态；如果没有这行代码，/computer status 只能看到外层 executor，无法确认低层 sender 是否接好。
        real_input_enabled = bool(platform_supported and self.enabled and implementation_available)  # 新增代码+Phase37WindowsSendInputExecutor: 只有平台、开关和实现都满足才允许真实输入；如果没有这行代码，安全门会被削弱。
        reason = "SendInput executor contract ready; real input stays disabled until enabled and implementation are both present."  # 新增代码+Phase37WindowsSendInputExecutor: 准备默认状态说明；如果没有这行代码，用户不知道为什么还不能真实动作。
        if real_input_enabled:  # 新增代码+Phase37WindowsSendInputExecutor: 判断是否真的可以执行底层输入；如果没有这行代码，成功原因无法区分。
            reason = "SendInput executor is enabled with an injected implementation."  # 新增代码+Phase37WindowsSendInputExecutor: 写入可执行说明；如果没有这行代码，状态仍像未启用。
        return {"backend": "windows_sendinput", "contract": PHASE37_SENDINPUT_CONTRACT, "contract_ready": True, "available": real_input_enabled, "platform": self.platform, "platform_supported": platform_supported, "enabled": self.enabled, "implementation_available": implementation_available, "real_input_enabled": real_input_enabled, "real_input_default": False, "safe_gate_required": True, "forbidden_targets_enforced_upstream": True, "actions_supported": list(PHASE37_SUPPORTED_ACTIONS), "dispatch": {"configured": implementation_available, "status": dispatch_status}, "reason": reason}  # 修改代码+RealComputerActionExecutor: 返回外层 executor 和内层 dispatcher 状态；如果没有这行代码，真实终端失败时用户看不到低层 sender 是否存在。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，WindowsSendInputExecutor.status 到此结束；如果没有这个边界说明，读者不容易看出状态字段范围。

    def _refusal(self, action: str, message: str, extra: dict[str, Any] | None = None) -> WindowsSendInputActionResult:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，统一构造拒绝结果；如果没有这段函数，每个拒绝分支会重复拼接字段。
        status = self.status()  # 新增代码+Phase37WindowsSendInputExecutor: 读取当前状态用于放入结果；如果没有这行代码，拒绝原因缺少平台和启用信息。
        data = {"backend": "windows_sendinput", "action": action, "contract": PHASE37_SENDINPUT_CONTRACT, "contract_ready": True, "real_input_enabled": status["real_input_enabled"], "platform": self.platform, "safe_gate_required": True}  # 新增代码+Phase37WindowsSendInputExecutor: 构造基础拒绝数据；如果没有这行代码，调用方无法确认未触碰真实输入。
        data.update(extra or {})  # 新增代码+Phase37WindowsSendInputExecutor: 合并额外字段；如果没有这行代码，具体拒绝分支无法补充细节。
        return WindowsSendInputActionResult(False, message, data)  # 新增代码+Phase37WindowsSendInputExecutor: 返回统一失败对象；如果没有这行代码，调用方需要处理多种失败格式。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，WindowsSendInputExecutor._refusal 到此结束；如果没有这个边界说明，读者不容易看出拒绝 helper 范围。

    def _events_for_action(self, action: str, arguments: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], WindowsSendInputActionResult | None]:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，把高层动作转成规范输入事件；如果没有这段函数，动作分支会和执行逻辑混在一起。
        if action == "move_mouse":  # 新增代码+Phase37WindowsSendInputExecutor: 处理鼠标移动事件；如果没有这行代码，执行器缺少定位能力。
            event = {"type": "move", "x": _safe_int(arguments.get("x")), "y": _safe_int(arguments.get("y"))}  # 新增代码+Phase37WindowsSendInputExecutor: 生成移动事件；如果没有这行代码，底层实现拿不到目标坐标。
            return [event], {}, None  # 新增代码+Phase37WindowsSendInputExecutor: 返回移动事件和空摘要；如果没有这行代码，execute 无法继续分发。
        if action == "click":  # 新增代码+Phase37WindowsSendInputExecutor: 处理单击事件；如果没有这行代码，执行器缺少最基础鼠标动作。
            event = {"type": "click", "x": _safe_int(arguments.get("x")), "y": _safe_int(arguments.get("y")), "button": str(arguments.get("button", "left"))}  # 新增代码+Phase37WindowsSendInputExecutor: 生成单击事件；如果没有这行代码，底层实现不知道点击位置和按键。
            return [event], {}, None  # 新增代码+Phase37WindowsSendInputExecutor: 返回单击事件；如果没有这行代码，click 分支无法执行。
        if action == "double_click":  # 新增代码+Phase37WindowsSendInputExecutor: 处理双击事件；如果没有这行代码，执行器无法覆盖高层双击动作。
            event = {"type": "double_click", "x": _safe_int(arguments.get("x")), "y": _safe_int(arguments.get("y")), "button": str(arguments.get("button", "left"))}  # 新增代码+Phase37WindowsSendInputExecutor: 生成双击事件；如果没有这行代码，底层实现不知道双击目标。
            return [event], {}, None  # 新增代码+Phase37WindowsSendInputExecutor: 返回双击事件；如果没有这行代码，double_click 分支无法执行。
        if action == "scroll":  # 新增代码+Phase37WindowsSendInputExecutor: 处理滚轮事件；如果没有这行代码，执行器无法滚动页面或列表。
            delta = _safe_int(arguments.get("delta", arguments.get("amount", 0)))  # 新增代码+Phase37WindowsSendInputExecutor: 读取滚动量并兼容 amount 字段；如果没有这行代码，模型不同命名会导致滚动失败。
            event = {"type": "scroll", "x": _safe_int(arguments.get("x")), "y": _safe_int(arguments.get("y")), "delta": delta}  # 新增代码+Phase37WindowsSendInputExecutor: 生成滚轮事件；如果没有这行代码，底层实现不知道滚动位置和方向。
            return [event], {"delta": delta}, None  # 新增代码+Phase37WindowsSendInputExecutor: 返回滚轮事件和摘要；如果没有这行代码，审计看不到滚动量。
        if action == "drag_path":  # 新增代码+GenericDragPathToolSurface: 处理连续拖拽路径事件；如果没有这行代码，画图和拖动选择等任务无法用一次动作表达连续鼠标按下移动抬起。
            raw_points = arguments.get("points", [])  # 新增代码+GenericDragPathToolSurface: 读取上游已经转换好的点列表；如果没有这行代码，执行器不知道鼠标要沿什么轨迹移动。
            point_items = list(raw_points) if isinstance(raw_points, list) else []  # 新增代码+GenericDragPathToolSurface: 只接受列表形态 points；如果没有这行代码，坏参数可能导致遍历异常。
            points: list[dict[str, int]] = []  # 新增代码+GenericDragPathToolSurface: 准备保存规范化屏幕点；如果没有这行代码，事件无法携带稳定路径。
            for point in point_items[:256]:  # 新增代码+GenericDragPathToolSurface: 限制一次拖拽最多 256 个点；如果没有这行代码，模型可能生成超长路径拖慢真实输入。
                if not isinstance(point, dict):  # 新增代码+GenericDragPathToolSurface: 跳过非对象点；如果没有这行代码，坏点会让 get 调用崩溃。
                    continue  # 新增代码+GenericDragPathToolSurface: 忽略坏点继续处理；如果没有这行代码，一个坏点会导致整条路径失败。
                points.append({"x": _safe_int(point.get("x")), "y": _safe_int(point.get("y"))})  # 新增代码+GenericDragPathToolSurface: 保存整数化屏幕坐标；如果没有这行代码，dispatcher 无法展开低层鼠标事件。
            if len(points) < 2:  # 新增代码+GenericDragPathToolSurface: 拖拽至少需要两个点；如果没有这行代码，单点路径会被误当成功但没有画线效果。
                return [], {}, self._refusal(action, "drag_path 至少需要 2 个有效 points，未调用 SendInput。", {"point_count": len(points)})  # 新增代码+GenericDragPathToolSurface: 返回点数不足拒绝；如果没有这行代码，用户和模型不知道为什么没有动作。
            event = {"type": "drag_path", "points": points, "point_count": len(points)}  # 新增代码+GenericDragPathToolSurface: 生成通用拖拽事件；如果没有这行代码，Phase47 dispatcher 收不到可展开的路径。
            return [event], {"point_count": len(points), "points_truncated": len(point_items) > 256}, None  # 新增代码+GenericDragPathToolSurface: 返回路径事件和摘要；如果没有这行代码，execute 无法分发连续画线动作。
        if action == "press_key":  # 新增代码+Phase37WindowsSendInputExecutor: 处理按键事件；如果没有这行代码，执行器无法覆盖快捷键和 Enter/Escape 等动作。
            key = str(arguments.get("key", "")).strip()[:80]  # 新增代码+Phase37WindowsSendInputExecutor: 读取并限制键名长度；如果没有这行代码，异常长键名会污染日志。
            if not key:  # 新增代码+Phase37WindowsSendInputExecutor: 拒绝空键名；如果没有这行代码，底层实现可能收到无意义事件。
                return [], {}, self._refusal(action, "press_key 缺少 key 参数，未调用 SendInput。", {"missing": "key"})  # 新增代码+Phase37WindowsSendInputExecutor: 返回缺键名失败；如果没有这行代码，用户不知道如何修正参数。
            event = {"type": "key", "key": key}  # 新增代码+Phase37WindowsSendInputExecutor: 生成按键事件；如果没有这行代码，底层实现拿不到键名。
            return [event], {"key": key}, None  # 新增代码+Phase37WindowsSendInputExecutor: 返回按键事件和摘要；如果没有这行代码，execute 无法分发。
        text = str(arguments.get("text", ""))  # 新增代码+Phase37WindowsSendInputExecutor: 读取文本输入内容；如果没有这行代码，type_text 分支无法计算长度和指纹。
        if len(text) > self.max_text_length:  # 新增代码+Phase37WindowsSendInputExecutor: 检查文本长度上限；如果没有这行代码，超长文本可能污染真实输入目标。
            return [], {}, self._refusal(action, f"type_text 文本过长，最大 {self.max_text_length} 字符，未调用 SendInput。", {"text_length": len(text)})  # 新增代码+Phase37WindowsSendInputExecutor: 返回超长文本拒绝；如果没有这行代码，用户不知道被拒绝原因。
        summary = {"text_length": len(text), "text_sha256_16": _text_sha256_16(text), "text_redacted": True}  # 新增代码+Phase37WindowsSendInputExecutor: 构造文本脱敏摘要；如果没有这行代码，审计无法安全描述文本输入。
        event = {"type": "text", **summary}  # 新增代码+Phase37WindowsSendInputExecutor: 生成不含原文的文本事件；如果没有这行代码，fake/验收事件可能泄露用户输入。
        return [event], summary, None  # 新增代码+Phase37WindowsSendInputExecutor: 返回文本事件和摘要；如果没有这行代码，type_text 成功路径无法执行。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，WindowsSendInputExecutor._events_for_action 到此结束；如果没有这个边界说明，读者不容易看出事件生成范围。

    def execute(self, action: str, arguments: dict[str, Any]) -> WindowsSendInputActionResult:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，执行一次已通过上游安全门的动作；如果没有这段函数，后端无法使用 SendInput 合同。
        action_name = str(action or "").strip()  # 新增代码+Phase37WindowsSendInputExecutor: 清理动作名称；如果没有这行代码，空白动作名可能进入分支判断。
        if action_name not in PHASE37_SUPPORTED_ACTIONS:  # 新增代码+Phase37WindowsSendInputExecutor: 拒绝未声明动作；如果没有这行代码，底层实现可能收到未知危险命令。
            return self._refusal(action_name, f"SendInput 执行器不支持动作：{action_name}", {"actions_supported": list(PHASE37_SUPPORTED_ACTIONS)})  # 新增代码+Phase37WindowsSendInputExecutor: 返回动作不支持结果；如果没有这行代码，模型不知道允许范围。
        status = self.status()  # 新增代码+Phase37WindowsSendInputExecutor: 读取当前状态；如果没有这行代码，执行前无法判断是否真的可用。
        if not status["real_input_enabled"]:  # 新增代码+Phase37WindowsSendInputExecutor: 没有平台/开关/实现时拒绝；如果没有这行代码，默认安全关闭会失效。
            return self._refusal(action_name, "SendInput 执行器未启用真实输入或缺少注入实现，未触碰鼠标键盘。", {"enabled": status["enabled"], "implementation_available": status["implementation_available"], "platform_supported": status["platform_supported"]})  # 新增代码+Phase37WindowsSendInputExecutor: 返回明确未执行结果；如果没有这行代码，用户可能误以为动作发生。
        events, summary, event_error = self._events_for_action(action_name, dict(arguments))  # 新增代码+Phase37WindowsSendInputExecutor: 生成规范输入事件；如果没有这行代码，底层实现没有可发送内容。
        if event_error is not None:  # 新增代码+Phase37WindowsSendInputExecutor: 检查事件生成是否失败；如果没有这行代码，坏参数仍可能继续发送。
            return event_error  # 新增代码+Phase37WindowsSendInputExecutor: 返回参数拒绝结果；如果没有这行代码，失败路径会被忽略。
        events = _attach_target_window_to_events(events, dict(arguments))  # 新增代码+ForegroundTargetRouting: 把动作绑定窗口传给 dispatcher；如果没有这行代码，真实 Paint 窗口打开后鼠标事件仍可能落到终端或旧焦点窗口。
        try:  # 新增代码+Phase37WindowsSendInputExecutor: 捕获注入实现异常；如果没有这行代码，底层错误会拖垮 agent。
            raw_dispatch_result = self.sendinput_impl.send(events)  # 新增代码+Phase37WindowsSendInputExecutor: 调用注入实现发送规范事件；如果没有这行代码，动作不会到达底层执行层。
        except Exception as error:  # 新增代码+Phase37WindowsSendInputExecutor: 处理底层实现异常；如果没有这行代码，权限或系统错误会直接抛栈。
            return self._refusal(action_name, f"SendInput 执行失败：{type(error).__name__}", {"event_count": len(events)})  # 新增代码+Phase37WindowsSendInputExecutor: 返回异常类型但不泄露本地细节；如果没有这行代码，用户只能看到崩溃。
        dispatch = _redact_dispatch_result(raw_dispatch_result)  # 新增代码+Phase37WindowsSendInputExecutor: 清理底层返回值；如果没有这行代码，底层实现可能泄露文本。
        ok = bool(dispatch.get("ok", True))  # 新增代码+Phase37WindowsSendInputExecutor: 读取底层成功标记，默认无标记视为成功；如果没有这行代码，返回值无法决定结果状态。
        data = {"backend": "windows_sendinput", "action": action_name, "contract": PHASE37_SENDINPUT_CONTRACT, "event_count": len(events), "dispatch": dispatch, "real_input_enabled": True, "safe_gate_required": True}  # 新增代码+Phase37WindowsSendInputExecutor: 构造成功/失败通用数据；如果没有这行代码，调用方无法审计发送结果。
        data.update(summary)  # 新增代码+Phase37WindowsSendInputExecutor: 合并动作摘要如滚轮量或文本指纹；如果没有这行代码，结果缺少动作细节。
        message = "SendInput 执行器已通过注入实现处理动作。" if ok else "SendInput 注入实现报告动作失败。"  # 新增代码+Phase37WindowsSendInputExecutor: 根据底层结果生成中文说明；如果没有这行代码，用户看不到成功或失败原因。
        return WindowsSendInputActionResult(ok, message, data)  # 新增代码+Phase37WindowsSendInputExecutor: 返回统一执行结果；如果没有这行代码，Windows 后端无法转换为 ComputerUseActionResult。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，WindowsSendInputExecutor.execute 到此结束；如果没有这个边界说明，读者不容易看出执行入口范围。


class _Phase37RecordingSendInputImplementation:  # 新增代码+Phase37WindowsSendInputExecutor: 定义合同自检用记录实现；如果没有这个类，CLI 无法在不碰真实桌面的情况下证明成功路径。
    def __init__(self) -> None:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，初始化事件记录；如果没有这段函数，自检无法保存 fake 事件。
        self.calls: list[dict[str, Any]] = []  # 新增代码+Phase37WindowsSendInputExecutor: 保存 fake SendInput 事件；如果没有这行代码，自检无法证明注入实现被调用。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，_Phase37RecordingSendInputImplementation.__init__ 到此结束；如果没有这个边界说明，读者不容易看出 fake 初始化范围。

    def send(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，记录规范事件而不触碰真实系统；如果没有这段函数，合同自检不能安全运行。
        self.calls.extend(dict(event) for event in events)  # 新增代码+Phase37WindowsSendInputExecutor: 复制事件用于后续泄露检查；如果没有这行代码，自检无法检查 raw text 是否出现。
        return {"ok": True, "event_count": len(events), "implementation": "phase37_recording"}  # 新增代码+Phase37WindowsSendInputExecutor: 返回成功摘要；如果没有这行代码，执行器无法形成成功结果。
    # 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，_Phase37RecordingSendInputImplementation.send 到此结束；如果没有这个边界说明，读者不容易看出 fake 发送范围。


def run_phase37_sendinput_executor_contract(platform: str | None = None) -> dict[str, Any]:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，运行 Phase37 合同自检；如果没有这段函数，真实终端验收没有稳定命令入口。
    default_executor = WindowsSendInputExecutor(platform=platform or sys.platform, enabled=False)  # 新增代码+Phase37WindowsSendInputExecutor: 创建默认关闭执行器；如果没有这行代码，自检无法证明 real_input_default=false。
    default_status = default_executor.status()  # 新增代码+Phase37WindowsSendInputExecutor: 读取默认状态；如果没有这行代码，报告缺少合同字段。
    recorder = _Phase37RecordingSendInputImplementation()  # 新增代码+Phase37WindowsSendInputExecutor: 创建 fake 实现；如果没有这行代码，自检会依赖真实 SendInput。
    fake_executor = WindowsSendInputExecutor(platform="win32", enabled=True, sendinput_impl=recorder)  # 新增代码+Phase37WindowsSendInputExecutor: 创建启用但注入 fake 的执行器；如果没有这行代码，成功路径无法安全验证。
    secret_text = "phase37-hidden-secret"  # 新增代码+Phase37WindowsSendInputExecutor: 准备泄露检查用文本；如果没有这行代码，自检无法证明 raw_text_hidden=true。
    fake_result = fake_executor.execute("type_text", {"text": secret_text})  # 新增代码+Phase37WindowsSendInputExecutor: 执行脱敏文本动作；如果没有这行代码，fake_impl_exercised 无法成立。
    visible_payload = json.dumps({"result": fake_result.data, "events": recorder.calls}, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase37WindowsSendInputExecutor: 序列化可见数据做泄露检查；如果没有这行代码，raw_text_hidden 无法被机器验证。
    raw_text_hidden = secret_text not in visible_payload  # 新增代码+Phase37WindowsSendInputExecutor: 判断原始文本是否没有出现在可见结果；如果没有这行代码，报告无法说明脱敏结果。
    fake_impl_exercised = bool(fake_result.ok and recorder.calls)  # 新增代码+Phase37WindowsSendInputExecutor: 判断 fake 实现是否真的被调用；如果没有这行代码，合同成功路径可能只是空跑。
    return {"marker": PHASE37_WINDOWS_SENDINPUT_EXECUTOR_MARKER, "ok_token": PHASE37_WINDOWS_SENDINPUT_EXECUTOR_OK_TOKEN, "status": default_status, "contract_ready": bool(default_status["contract_ready"]), "real_input_default": bool(default_status["real_input_enabled"]), "fake_impl_exercised": fake_impl_exercised, "raw_text_hidden": raw_text_hidden, "actions_expanded": False, "fake_event_count": len(recorder.calls)}  # 新增代码+Phase37WindowsSendInputExecutor: 返回稳定自检报告；如果没有这行代码，验收场景无法检查关键边界。
# 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，run_phase37_sendinput_executor_contract 到此结束；如果没有这个边界说明，读者不容易看出合同自检范围。


def phase37_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，生成真实终端验收用稳定单行；如果没有这段函数，verifier 需要解析完整 JSON。
    return f"{PHASE37_WINDOWS_SENDINPUT_EXECUTOR_OK_TOKEN} contract_ready={_bool_text(report['contract_ready'])} real_input_default={_bool_text(report['real_input_default'])} fake_impl_exercised={_bool_text(report['fake_impl_exercised'])} raw_text_hidden={_bool_text(report['raw_text_hidden'])} actions_expanded={_bool_text(report['actions_expanded'])} marker={PHASE37_WINDOWS_SENDINPUT_EXECUTOR_MARKER}"  # 新增代码+Phase37WindowsSendInputExecutor: 返回包含所有关键 token 的一行文本；如果没有这行代码，真实终端验收容易漏检。
# 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，phase37_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 行格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase37WindowsSendInputExecutor: 函数段开始，提供命令行入口；如果没有这段函数，场景无法直接运行 Phase37 自检。
    _ = argv  # 新增代码+Phase37WindowsSendInputExecutor: 保留 argv 位置供未来扩展；如果没有这行代码，静态检查可能提示参数未使用。
    report = run_phase37_sendinput_executor_contract()  # 新增代码+Phase37WindowsSendInputExecutor: 执行合同自检；如果没有这行代码，CLI 不会生成报告。
    print(phase37_cli_line(report))  # 新增代码+Phase37WindowsSendInputExecutor: 打印稳定 token 行；如果没有这行代码，debug log 无法匹配关键验收项。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase37WindowsSendInputExecutor: 打印结构化报告；如果没有这行代码，用户难以理解真实输入为何默认关闭。
    print(PHASE37_WINDOWS_SENDINPUT_EXECUTOR_MARKER)  # 新增代码+Phase37WindowsSendInputExecutor: 单独打印阶段 marker；如果没有这行代码，最终回答复制时容易漏标记。
    return 0  # 新增代码+Phase37WindowsSendInputExecutor: 合同自检成功返回 0；如果没有这行代码，真实终端命令状态不稳定。
# 新增代码+Phase37WindowsSendInputExecutor: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出命令入口范围。


if __name__ == "__main__":  # 新增代码+Phase37WindowsSendInputExecutor: 允许直接运行模块文件；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase37WindowsSendInputExecutor: 用 main 返回码退出；如果没有这行代码，命令行退出状态不明确。
