"""Phase71 generic hotkey, menu, scroll, and drag event builders."""  # 新增代码+Phase71GenericInputActions: 标明本文件负责通用输入事件构建；如果没有这行代码，读者不容易区分 Phase71 和真实 SendInput 派发层。
from __future__ import annotations  # 新增代码+Phase71GenericInputActions: 启用延迟类型注解，避免运行时因为类型提示互相引用而导入失败；如果没有这行代码，后续扩展 runtime 类型时更容易遇到循环导入。

import json  # 新增代码+Phase71GenericInputActions: 导入 JSON 用于稳定打印合同报告；如果没有这行代码，CLI 失败时不易复盘结构化结果。
from typing import Any  # 新增代码+Phase71GenericInputActions: 导入 Any 描述 JSON 风格窗口、点位和事件参数；如果没有这行代码，接口边界不容易读懂。


PHASE71_GENERIC_INPUT_ACTIONS_MARKER = "PHASE71_GENERIC_INPUT_ACTIONS_READY"  # 新增代码+Phase71GenericInputActions: 定义真实终端验收 ready 标记；如果没有这行代码，controller 无法稳定识别 Phase71 输出。
PHASE71_GENERIC_INPUT_ACTIONS_OK_TOKEN = "PHASE71_GENERIC_INPUT_ACTIONS_OK"  # 新增代码+Phase71GenericInputActions: 定义真实终端验收 OK 标记；如果没有这行代码，用户无法一眼确认本阶段合同通过。
PHASE71_GENERIC_INPUT_ACTIONS_MODEL = "phase71_windows_generic_input_actions"  # 新增代码+Phase71GenericInputActions: 定义本阶段能力模型名称；如果没有这行代码，后续矩阵无法统一引用 Phase71 能力。
PHASE71_ACTIONS_EXPANDED = False  # 新增代码+Phase71GenericInputActions: 明确 Phase71 不新增真实桌面动作面；如果没有这行代码，事件构建器可能被误认为已经能真实派发。
PHASE71_FORBIDDEN_HOTKEY_COMBOS = {frozenset({"ctrl", "alt", "delete"}), frozenset({"win", "r"}), frozenset({"win", "x"}), frozenset({"ctrl", "shift", "esc"})}  # 新增代码+Phase71GenericInputActions: 固定禁止系统级热键组合；如果没有这行代码，Ctrl+Alt+Delete、Win+R 等高风险入口可能被构建。
PHASE71_SYSTEM_LEVEL_KEYS = {"win"}  # 新增代码+Phase71GenericInputActions: 标记所有 Windows 键组合都属于系统级动作；如果没有这行代码，未列出的 Win 热键可能绕过本阶段边界。
PHASE71_KEY_ALIASES = {"control": "ctrl", "ctrl": "ctrl", "alt": "alt", "shift": "shift", "windows": "win", "window": "win", "win": "win", "meta": "win", "cmd": "win", "command": "win", "delete": "delete", "del": "delete", "escape": "esc", "esc": "esc", "return": "enter", "enter": "enter", "spacebar": "space", "space": "space"}  # 新增代码+Phase71GenericInputActions: 统一常见按键别名；如果没有这行代码，Win/Windows 或 Del/Delete 会被当成不同键。


def _phase71_bool_token(value: Any) -> str:  # 新增代码+Phase71GenericInputActions: 函数段开始，把布尔值转换成验收 token 需要的小写 true/false；如果没有这个函数，CLI 输出容易出现 True/False 漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase71GenericInputActions: 返回稳定小写布尔字符串；如果没有这行代码，真实终端场景 token 无法稳定匹配。
# 新增代码+Phase71GenericInputActions: 函数段结束，_phase71_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出 token 转换范围。


def _phase71_safe_text(value: Any, limit: int = 160) -> str:  # 新增代码+Phase71GenericInputActions: 函数段开始，把任意文本压成安全单行；如果没有这个函数，菜单路径或键名可能破坏日志格式。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase71GenericInputActions: 清理换行和首尾空白；如果没有这行代码，用户输入可能打散事件 JSON。
    return text[: max(0, int(limit))]  # 新增代码+Phase71GenericInputActions: 限制最大长度；如果没有这行代码，长菜单名可能刷爆终端。
# 新增代码+Phase71GenericInputActions: 函数段结束，_phase71_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清理范围。


def _phase71_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase71GenericInputActions: 函数段开始，把坐标和滚轮值安全转换成整数；如果没有这个函数，坏点位会让事件构建崩溃。
    try:  # 新增代码+Phase71GenericInputActions: 捕获无法转换的动态值；如果没有这行代码，None 或字符串坐标会直接抛异常。
        return int(value)  # 新增代码+Phase71GenericInputActions: 返回整数；如果没有这行代码，事件坐标无法稳定。
    except Exception:  # 新增代码+Phase71GenericInputActions: 兜底处理任意转换异常；如果没有这行代码，模型坏参数会中断 agent。
        return int(default)  # 新增代码+Phase71GenericInputActions: 返回默认整数；如果没有这行代码，调用方需要到处重复兜底。
# 新增代码+Phase71GenericInputActions: 函数段结束，_phase71_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出整数转换范围。


def _phase71_event(event_type: str, **payload: Any) -> dict[str, Any]:  # 新增代码+Phase71GenericInputActions: 函数段开始，生成统一事件字典；如果没有这个函数，事件字段会在各个 builder 里漂移。
    event = {"type": _phase71_safe_text(event_type, 80), "real_dispatch_allowed": False}  # 新增代码+Phase71GenericInputActions: 写入事件类型并明确禁止真实派发；如果没有这行代码，Phase71 可能被误接到真实输入后端。
    event.update(payload)  # 新增代码+Phase71GenericInputActions: 合并事件专属字段；如果没有这行代码，坐标、按键或菜单项会丢失。
    return event  # 新增代码+Phase71GenericInputActions: 返回规范事件；如果没有这行代码，调用方拿不到事件对象。
# 新增代码+Phase71GenericInputActions: 函数段结束，_phase71_event 到此结束；如果没有这个边界说明，初学者不容易看出事件构造范围。


def _phase71_normalize_key(key: Any) -> str:  # 新增代码+Phase71GenericInputActions: 函数段开始，规范化单个键名；如果没有这个函数，Ctrl/S 等键名大小写和别名会不稳定。
    raw = _phase71_safe_text(key, 80).lower()  # 新增代码+Phase71GenericInputActions: 把键名清理并转小写；如果没有这行代码，大小写差异会影响禁止热键判断。
    return PHASE71_KEY_ALIASES.get(raw, raw)  # 新增代码+Phase71GenericInputActions: 返回别名映射后的键名；如果没有这行代码，Windows/Win 或 Del/Delete 可能绕过检查。
# 新增代码+Phase71GenericInputActions: 函数段结束，_phase71_normalize_key 到此结束；如果没有这个边界说明，初学者不容易看出键名规范范围。


def _phase71_normalize_keys(keys: Any) -> list[str]:  # 新增代码+Phase71GenericInputActions: 函数段开始，规范化按键列表；如果没有这个函数，热键 builder 和门禁会重复清洗逻辑。
    raw_keys = keys if isinstance(keys, list) else []  # 新增代码+Phase71GenericInputActions: 只接受列表形式的热键；如果没有这行代码，字符串会被逐字符拆开。
    normalized = [_phase71_normalize_key(key) for key in raw_keys]  # 新增代码+Phase71GenericInputActions: 逐个规范化按键；如果没有这行代码，热键事件无法稳定。
    return [key for key in normalized if key]  # 新增代码+Phase71GenericInputActions: 去掉空键；如果没有这行代码，空字符串可能生成无意义事件。
# 新增代码+Phase71GenericInputActions: 函数段结束，_phase71_normalize_keys 到此结束；如果没有这个边界说明，初学者不容易看出按键列表规范范围。


def _phase71_is_forbidden_hotkey(keys: list[str]) -> bool:  # 新增代码+Phase71GenericInputActions: 函数段开始，判断热键是否属于本阶段禁止组合；如果没有这个函数，危险系统热键会散落判断。
    key_set = frozenset(keys)  # 新增代码+Phase71GenericInputActions: 转成集合便于无序匹配组合；如果没有这行代码，Ctrl+Alt+Delete 的顺序变化可能绕过门禁。
    if key_set in PHASE71_FORBIDDEN_HOTKEY_COMBOS:  # 新增代码+Phase71GenericInputActions: 检查明确禁止的系统组合；如果没有这行代码，蓝图列出的危险热键无法阻断。
        return True  # 新增代码+Phase71GenericInputActions: 返回禁止成立；如果没有这行代码，显式危险组合会继续生成事件。
    return bool(PHASE71_SYSTEM_LEVEL_KEYS.intersection(key_set))  # 新增代码+Phase71GenericInputActions: 阻断所有 Windows 键组合；如果没有这行代码，未列出的 Win 热键可能打开系统入口。
# 新增代码+Phase71GenericInputActions: 函数段结束，_phase71_is_forbidden_hotkey 到此结束；如果没有这个边界说明，初学者不容易看出禁止热键范围。


def _phase71_point(point: Any) -> dict[str, int]:  # 新增代码+Phase71GenericInputActions: 函数段开始，把任意点位规范成 x/y 整数；如果没有这个函数，拖拽和滚轮坐标格式会混乱。
    raw_point = point if isinstance(point, dict) else {}  # 新增代码+Phase71GenericInputActions: 只接受字典点位；如果没有这行代码，坏输入会触发难懂异常。
    return {"x": _phase71_safe_int(raw_point.get("x", 0)), "y": _phase71_safe_int(raw_point.get("y", 0))}  # 新增代码+Phase71GenericInputActions: 返回标准点位；如果没有这行代码，鼠标事件缺少可用坐标。
# 新增代码+Phase71GenericInputActions: 函数段结束，_phase71_point 到此结束；如果没有这个边界说明，初学者不容易看出点位规范范围。


def build_hotkey_events(keys: list[str]) -> list[dict[str, Any]]:  # 新增代码+Phase71GenericInputActions: 函数段开始，构造热键按下和抬起事件；如果没有这个函数，普通保存/复制等热键无法表达。
    normalized_keys = _phase71_normalize_keys(keys)  # 新增代码+Phase71GenericInputActions: 规范化热键列表；如果没有这行代码，事件键名可能大小写漂移。
    down_events = [_phase71_event("key_down", key=key) for key in normalized_keys]  # 新增代码+Phase71GenericInputActions: 按用户顺序生成按下事件；如果没有这行代码，热键不会开始。
    up_events = [_phase71_event("key_up", key=key) for key in reversed(normalized_keys)]  # 新增代码+Phase71GenericInputActions: 反向生成抬起事件；如果没有这行代码，修饰键可能过早抬起或不闭合。
    return down_events + up_events  # 新增代码+Phase71GenericInputActions: 返回完整热键事件序列；如果没有这行代码，调用方拿不到可发送事件。
# 新增代码+Phase71GenericInputActions: 函数段结束，build_hotkey_events 到此结束；如果没有这个边界说明，初学者不容易看出热键构建范围。


def build_scroll_events(x: int, y: int, delta: int) -> list[dict[str, Any]]:  # 新增代码+Phase71GenericInputActions: 函数段开始，构造指定坐标滚轮事件；如果没有这个函数，滚动无法表达目标位置。
    safe_x = _phase71_safe_int(x)  # 新增代码+Phase71GenericInputActions: 规范化 x 坐标；如果没有这行代码，鼠标移动事件横坐标不稳定。
    safe_y = _phase71_safe_int(y)  # 新增代码+Phase71GenericInputActions: 规范化 y 坐标；如果没有这行代码，鼠标移动事件纵坐标不稳定。
    safe_delta = _phase71_safe_int(delta)  # 新增代码+Phase71GenericInputActions: 规范化滚轮 delta；如果没有这行代码，滚轮方向和幅度不稳定。
    return [_phase71_event("mouse_move", x=safe_x, y=safe_y), _phase71_event("mouse_wheel", x=safe_x, y=safe_y, delta=safe_delta)]  # 新增代码+Phase71GenericInputActions: 返回先移动再滚动的事件；如果没有这行代码，滚轮可能作用于错误位置。
# 新增代码+Phase71GenericInputActions: 函数段结束，build_scroll_events 到此结束；如果没有这个边界说明，初学者不容易看出滚轮构建范围。


def build_drag_path(points: list[dict[str, int]]) -> list[dict[str, Any]]:  # 新增代码+Phase71GenericInputActions: 函数段开始，构造连续拖拽鼠标路径；如果没有这个函数，画图和选择区域无法表达拖拽。
    safe_points = [_phase71_point(point) for point in list(points or []) if isinstance(point, dict)]  # 新增代码+Phase71GenericInputActions: 清洗路径点；如果没有这行代码，坏点位可能污染鼠标事件。
    if len(safe_points) < 2:  # 新增代码+Phase71GenericInputActions: 检查是否至少有起点和终点；如果没有这行代码，单点拖拽会生成不完整事件。
        return []  # 新增代码+Phase71GenericInputActions: 点数不足时返回空事件；如果没有这行代码，调用方无法做零事件拒绝。
    events = [_phase71_event("mouse_move", x=safe_points[0]["x"], y=safe_points[0]["y"], path_index=0), _phase71_event("mouse_down", button="left", x=safe_points[0]["x"], y=safe_points[0]["y"])]  # 新增代码+Phase71GenericInputActions: 先移动到起点并按下鼠标；如果没有这行代码，拖拽会从未知位置开始。
    for index, point in enumerate(safe_points[1:], start=1):  # 新增代码+Phase71GenericInputActions: 遍历后续路径点；如果没有这行代码，拖拽不会形成连续轨迹。
        events.append(_phase71_event("mouse_move", x=point["x"], y=point["y"], path_index=index))  # 新增代码+Phase71GenericInputActions: 追加每个中间点移动；如果没有这行代码，绘制路径会丢点。
    events.append(_phase71_event("mouse_up", button="left", x=safe_points[-1]["x"], y=safe_points[-1]["y"]))  # 新增代码+Phase71GenericInputActions: 在终点抬起鼠标；如果没有这行代码，拖拽动作不会闭合。
    return events  # 新增代码+Phase71GenericInputActions: 返回完整拖拽路径事件；如果没有这行代码，调用方拿不到可审计轨迹。
# 新增代码+Phase71GenericInputActions: 函数段结束，build_drag_path 到此结束；如果没有这个边界说明，初学者不容易看出拖拽构建范围。


def build_menu_sequence(menu_path: list[str]) -> list[dict[str, Any]]:  # 新增代码+Phase71GenericInputActions: 函数段开始，构造菜单路径导航事件；如果没有这个函数，菜单点击只能靠不稳定坐标。
    safe_path = [_phase71_safe_text(item, 120) for item in list(menu_path or []) if _phase71_safe_text(item, 120)]  # 新增代码+Phase71GenericInputActions: 清洗菜单路径项；如果没有这行代码，空菜单名会生成无意义事件。
    if not safe_path:  # 新增代码+Phase71GenericInputActions: 检查菜单路径是否为空；如果没有这行代码，空菜单也会生成提交事件。
        return []  # 新增代码+Phase71GenericInputActions: 空路径返回空事件；如果没有这行代码，调用方无法做零事件拒绝。
    events = [_phase71_event("menu_open", path_length=len(safe_path), root=safe_path[0])]  # 新增代码+Phase71GenericInputActions: 先生成菜单打开事件；如果没有这行代码，菜单导航没有入口。
    for index, label in enumerate(safe_path):  # 新增代码+Phase71GenericInputActions: 遍历菜单路径项；如果没有这行代码，菜单项不会被逐级记录。
        events.append(_phase71_event("menu_item", index=index, label=label))  # 新增代码+Phase71GenericInputActions: 记录当前菜单项；如果没有这行代码，下游不知道要选哪个菜单。
    events.append(_phase71_event("menu_commit", label=safe_path[-1], path=" > ".join(safe_path)))  # 新增代码+Phase71GenericInputActions: 生成菜单确认事件；如果没有这行代码，菜单导航不会闭合。
    return events  # 新增代码+Phase71GenericInputActions: 返回完整菜单事件序列；如果没有这行代码，调用方拿不到菜单路径。
# 新增代码+Phase71GenericInputActions: 函数段结束，build_menu_sequence 到此结束；如果没有这个边界说明，初学者不容易看出菜单构建范围。


class Phase71RecordingInputSender:  # 新增代码+Phase71GenericInputActions: 类段开始，提供记录型输入 sender；如果没有这个类，合同测试可能触碰真实鼠标键盘。
    def __init__(self) -> None:  # 新增代码+Phase71GenericInputActions: 函数段开始，初始化事件记录；如果没有这个函数，测试无法统计 sender 收到多少事件。
        self.events: list[dict[str, Any]] = []  # 新增代码+Phase71GenericInputActions: 保存输入事件副本；如果没有这行代码，零事件门禁无法被验证。
    # 新增代码+Phase71GenericInputActions: 函数段结束，Phase71RecordingInputSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def send_input_events(self, window: dict[str, Any], events: list[dict[str, Any]], reason: str = "") -> dict[str, Any]:  # 新增代码+Phase71GenericInputActions: 函数段开始，记录输入事件而不真实派发；如果没有这个函数，Phase71 无法证明事件形状。
        safe_window = dict(window or {})  # 新增代码+Phase71GenericInputActions: 复制窗口上下文；如果没有这行代码，记录过程可能污染调用方对象。
        safe_events = [dict(event) for event in list(events or []) if isinstance(event, dict)]  # 新增代码+Phase71GenericInputActions: 复制事件列表；如果没有这行代码，外部修改可能影响审计记录。
        for event in safe_events:  # 新增代码+Phase71GenericInputActions: 遍历待记录事件；如果没有这行代码，事件无法补充窗口摘要。
            event["window_id"] = _phase71_safe_text(safe_window.get("window_id", ""), 120)  # 新增代码+Phase71GenericInputActions: 写入脱敏窗口 id；如果没有这行代码，事件无法追踪目标窗口。
            event["real_dispatch_allowed"] = False  # 新增代码+Phase71GenericInputActions: 再次强制标记不允许真实派发；如果没有这行代码，调用方错误事件可能打开真实动作面。
        self.events.extend(safe_events)  # 新增代码+Phase71GenericInputActions: 保存事件；如果没有这行代码，测试无法检查事件形状。
        return {"ok": bool(safe_events), "input_event_count": len(safe_events), "sender": "phase71_recording_input_sender", "real_dispatch_allowed": False, "reason": _phase71_safe_text(reason, 160), "actions_expanded": PHASE71_ACTIONS_EXPANDED}  # 新增代码+Phase71GenericInputActions: 返回记录摘要；如果没有这行代码，runtime 拿不到发送结果。
    # 新增代码+Phase71GenericInputActions: 函数段结束，Phase71RecordingInputSender.send_input_events 到此结束；如果没有这个边界说明，初学者不容易看出记录发送范围。
# 新增代码+Phase71GenericInputActions: 类段结束，Phase71RecordingInputSender 到此结束；如果没有这个边界说明，初学者不容易看出记录型 sender 范围。


class WindowsGenericInputActionRuntime:  # 新增代码+Phase71GenericInputActions: 类段开始，提供热键、菜单、滚轮和拖拽的通用 runtime；如果没有这个类，Phase68 闭环执行器不能表达这些输入动作。
    def __init__(self, sender: Any | None = None) -> None:  # 新增代码+Phase71GenericInputActions: 函数段开始，注入记录型或未来真实 sender；如果没有这个函数，测试和生产无法替换执行后端。
        self.sender = sender if sender is not None else Phase71RecordingInputSender()  # 新增代码+Phase71GenericInputActions: 默认使用记录型 sender；如果没有这行代码，默认构造可能误触真实桌面。
    # 新增代码+Phase71GenericInputActions: 函数段结束，WindowsGenericInputActionRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _send(self, window: dict[str, Any], operation: str, events: list[dict[str, Any]], extra: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase71GenericInputActions: 函数段开始，统一记录事件并生成报告；如果没有这个函数，各动作返回字段会漂移。
        safe_events = [dict(event) for event in list(events or []) if isinstance(event, dict)]  # 新增代码+Phase71GenericInputActions: 复制事件列表；如果没有这行代码，后续补字段可能污染 builder 输出。
        if not safe_events:  # 新增代码+Phase71GenericInputActions: 检查是否没有可记录事件；如果没有这行代码，空动作可能误报成功。
            return {"ok": False, "operation": operation, "decision": "empty_input_events", "input_event_count": 0, "zero_event_refusal": True, "real_dispatch_allowed": False, "marker": PHASE71_GENERIC_INPUT_ACTIONS_MARKER, "model": PHASE71_GENERIC_INPUT_ACTIONS_MODEL, "actions_expanded": PHASE71_ACTIONS_EXPANDED}  # 新增代码+Phase71GenericInputActions: 返回零事件拒绝；如果没有这行代码，空路径会产生不清楚失败。
        send_method = getattr(self.sender, "send_input_events", None)  # 新增代码+Phase71GenericInputActions: 读取 sender 接口；如果没有这行代码，注入对象无法被调用。
        if not callable(send_method):  # 新增代码+Phase71GenericInputActions: 检查 sender 是否实现记录方法；如果没有这行代码，错误适配器会产生难懂异常。
            return {"ok": False, "operation": operation, "decision": "sender_missing_send_input_events", "input_event_count": 0, "zero_event_refusal": True, "real_dispatch_allowed": False, "marker": PHASE71_GENERIC_INPUT_ACTIONS_MARKER, "model": PHASE71_GENERIC_INPUT_ACTIONS_MODEL, "actions_expanded": PHASE71_ACTIONS_EXPANDED}  # 新增代码+Phase71GenericInputActions: 返回接口缺失拒绝；如果没有这行代码，调用方无法安全降级。
        dispatch = dict(send_method(dict(window or {}), safe_events, operation) or {})  # 新增代码+Phase71GenericInputActions: 调用记录型 sender；如果没有这行代码，事件不会进入统一记录。
        result = {"ok": bool(dispatch.get("ok")), "operation": operation, "input_event_count": int(dispatch.get("input_event_count", len(safe_events)) or 0), "events_preview": safe_events[:8], "sender_result": dispatch, "zero_event_refusal": False, "real_dispatch_allowed": False, "marker": PHASE71_GENERIC_INPUT_ACTIONS_MARKER, "model": PHASE71_GENERIC_INPUT_ACTIONS_MODEL, "actions_expanded": PHASE71_ACTIONS_EXPANDED}  # 新增代码+Phase71GenericInputActions: 构造统一动作报告；如果没有这行代码，闭环执行器拿不到事件摘要。
        result.update(dict(extra or {}))  # 新增代码+Phase71GenericInputActions: 合并动作专属字段；如果没有这行代码，hotkey/menu/drag 标志会丢失。
        return result  # 新增代码+Phase71GenericInputActions: 返回动作报告；如果没有这行代码，调用方拿不到结果。
    # 新增代码+Phase71GenericInputActions: 函数段结束，WindowsGenericInputActionRuntime._send 到此结束；如果没有这个边界说明，初学者不容易看出统一发送范围。

    def send_hotkey(self, window: dict[str, Any], keys: list[str]) -> dict[str, Any]:  # 新增代码+Phase71GenericInputActions: 函数段开始，记录普通热键动作；如果没有这个函数，Ctrl+S/Ctrl+C 等通用动作无法表达。
        normalized_keys = _phase71_normalize_keys(keys)  # 新增代码+Phase71GenericInputActions: 规范化热键列表；如果没有这行代码，禁止热键判断不稳定。
        if _phase71_is_forbidden_hotkey(normalized_keys):  # 新增代码+Phase71GenericInputActions: 检查是否为系统级危险热键；如果没有这行代码，Win+R 等组合可能被发送。
            return {"ok": False, "operation": "hotkey", "decision": "forbidden_system_hotkey", "keys": normalized_keys, "hotkey_action": False, "forbidden_system_hotkeys_blocked": True, "input_event_count": 0, "zero_event_refusal": True, "real_dispatch_allowed": False, "marker": PHASE71_GENERIC_INPUT_ACTIONS_MARKER, "model": PHASE71_GENERIC_INPUT_ACTIONS_MODEL, "actions_expanded": PHASE71_ACTIONS_EXPANDED}  # 新增代码+Phase71GenericInputActions: 返回零事件危险热键拒绝；如果没有这行代码，系统入口可能被误打开。
        events = build_hotkey_events(normalized_keys)  # 新增代码+Phase71GenericInputActions: 构造热键事件；如果没有这行代码，普通热键没有事件序列。
        return self._send(window, "hotkey", events, {"hotkey_action": True, "keys": normalized_keys, "forbidden_system_hotkeys_blocked": False})  # 新增代码+Phase71GenericInputActions: 记录热键并返回报告；如果没有这行代码，调用方拿不到热键结果。
    # 新增代码+Phase71GenericInputActions: 函数段结束，WindowsGenericInputActionRuntime.send_hotkey 到此结束；如果没有这个边界说明，初学者不容易看出热键动作范围。

    def navigate_menu(self, window: dict[str, Any], menu_path: list[str]) -> dict[str, Any]:  # 新增代码+Phase71GenericInputActions: 函数段开始，记录菜单路径导航；如果没有这个函数，菜单操作只能靠坐标猜测。
        events = build_menu_sequence(menu_path)  # 新增代码+Phase71GenericInputActions: 构造菜单事件；如果没有这行代码，菜单路径无法变成协议。
        return self._send(window, "menu_navigation", events, {"menu_navigation": True, "menu_path": [_phase71_safe_text(item, 120) for item in list(menu_path or [])]})  # 新增代码+Phase71GenericInputActions: 记录菜单导航并返回报告；如果没有这行代码，调用方拿不到菜单结果。
    # 新增代码+Phase71GenericInputActions: 函数段结束，WindowsGenericInputActionRuntime.navigate_menu 到此结束；如果没有这个边界说明，初学者不容易看出菜单动作范围。

    def scroll_at(self, window: dict[str, Any], x: int, y: int, delta: int) -> dict[str, Any]:  # 新增代码+Phase71GenericInputActions: 函数段开始，记录指定坐标滚轮动作；如果没有这个函数，滚动无法绑定到目标区域。
        events = build_scroll_events(x, y, delta)  # 新增代码+Phase71GenericInputActions: 构造滚轮事件；如果没有这行代码，滚动动作没有协议。
        return self._send(window, "scroll", events, {"scroll_action": True, "x": _phase71_safe_int(x), "y": _phase71_safe_int(y), "delta": _phase71_safe_int(delta)})  # 新增代码+Phase71GenericInputActions: 记录滚轮并返回报告；如果没有这行代码，调用方拿不到滚动结果。
    # 新增代码+Phase71GenericInputActions: 函数段结束，WindowsGenericInputActionRuntime.scroll_at 到此结束；如果没有这个边界说明，初学者不容易看出滚轮动作范围。

    def drag_path(self, window: dict[str, Any], points: list[dict[str, int]]) -> dict[str, Any]:  # 新增代码+Phase71GenericInputActions: 函数段开始，记录连续拖拽动作；如果没有这个函数，画图和选择区域无法表达。
        events = build_drag_path(points)  # 新增代码+Phase71GenericInputActions: 构造拖拽事件；如果没有这行代码，拖拽动作没有协议。
        move_count = len([event for event in events if event.get("type") == "mouse_move"])  # 新增代码+Phase71GenericInputActions: 统计移动点数量；如果没有这行代码，无法证明路径连续。
        return self._send(window, "drag", events, {"drag_action": True, "continuous_mouse_path": move_count >= 2, "path_point_count": move_count})  # 新增代码+Phase71GenericInputActions: 记录拖拽并返回报告；如果没有这行代码，调用方拿不到拖拽结果。
    # 新增代码+Phase71GenericInputActions: 函数段结束，WindowsGenericInputActionRuntime.drag_path 到此结束；如果没有这个边界说明，初学者不容易看出拖拽动作范围。
# 新增代码+Phase71GenericInputActions: 类段结束，WindowsGenericInputActionRuntime 到此结束；如果没有这个边界说明，初学者不容易看出通用输入 runtime 范围。


def _phase71_contract_window() -> dict[str, Any]:  # 新增代码+Phase71GenericInputActions: 函数段开始，构造合同自检窗口；如果没有这个函数，合同样本会散落在多处。
    return {"app_id": "phase58_safe_app", "process_name": "phase58_safe_app", "window_id": "hwnd:7101", "hwnd": 7101, "title_preview": "LearningAgent-Phase71-GenericInputActions", "safe_to_target": True}  # 新增代码+Phase71GenericInputActions: 返回安全记录型窗口；如果没有这行代码，合同动作没有目标上下文。
# 新增代码+Phase71GenericInputActions: 函数段结束，_phase71_contract_window 到此结束；如果没有这个边界说明，初学者不容易看出合同窗口范围。


def run_phase71_generic_input_actions_contract() -> dict[str, Any]:  # 新增代码+Phase71GenericInputActions: 函数段开始，运行 Phase71 通用输入动作合同自检；如果没有这个函数，CLI 和真实终端没有统一验收入口。
    sender = Phase71RecordingInputSender()  # 新增代码+Phase71GenericInputActions: 创建记录型 sender；如果没有这行代码，合同可能触碰真实鼠标键盘。
    runtime = WindowsGenericInputActionRuntime(sender=sender)  # 新增代码+Phase71GenericInputActions: 创建通用输入 runtime；如果没有这行代码，合同没有被测对象。
    window = _phase71_contract_window()  # 新增代码+Phase71GenericInputActions: 获取合同窗口；如果没有这行代码，动作缺少目标上下文。
    hotkey = runtime.send_hotkey(window, ["ctrl", "s"])  # 新增代码+Phase71GenericInputActions: 执行普通热键正例；如果没有这行代码，hotkey_action token 没证据。
    menu = runtime.navigate_menu(window, ["File", "Save As"])  # 新增代码+Phase71GenericInputActions: 执行菜单导航正例；如果没有这行代码，menu_navigation token 没证据。
    scroll = runtime.scroll_at(window, 320, 240, -480)  # 新增代码+Phase71GenericInputActions: 执行滚轮正例；如果没有这行代码，scroll_action token 没证据。
    drag = runtime.drag_path(window, [{"x": 10, "y": 20}, {"x": 30, "y": 40}, {"x": 60, "y": 70}])  # 新增代码+Phase71GenericInputActions: 执行拖拽正例；如果没有这行代码，drag_action token 没证据。
    event_count_before_forbidden = len(sender.events)  # 新增代码+Phase71GenericInputActions: 记录危险热键前事件数量；如果没有这行代码，无法证明拒绝路径零事件。
    forbidden_results = [runtime.send_hotkey(window, combo) for combo in (["ctrl", "alt", "delete"], ["win", "r"], ["win", "x"], ["ctrl", "shift", "esc"])]  # 新增代码+Phase71GenericInputActions: 覆盖蓝图列出的危险热键；如果没有这行代码，禁止组合 token 没证据。
    hotkey_action = bool(hotkey.get("ok") and hotkey.get("hotkey_action") and hotkey.get("input_event_count", 0) >= 4)  # 新增代码+Phase71GenericInputActions: 汇总热键能力；如果没有这行代码，CLI 无法表达热键是否完整。
    menu_navigation = bool(menu.get("ok") and menu.get("menu_navigation") and any(event.get("type") == "menu_commit" for event in sender.events))  # 新增代码+Phase71GenericInputActions: 汇总菜单导航能力；如果没有这行代码，菜单可能只是文案。
    scroll_action = bool(scroll.get("ok") and scroll.get("scroll_action") and any(event.get("type") == "mouse_wheel" for event in sender.events))  # 新增代码+Phase71GenericInputActions: 汇总滚轮能力；如果没有这行代码，滚动事件缺失不会暴露。
    drag_action = bool(drag.get("ok") and drag.get("drag_action") and any(event.get("type") == "mouse_down" for event in sender.events) and any(event.get("type") == "mouse_up" for event in sender.events))  # 新增代码+Phase71GenericInputActions: 汇总拖拽能力；如果没有这行代码，拖拽不闭合可能漏过。
    continuous_mouse_path = bool(drag.get("continuous_mouse_path") and drag.get("path_point_count", 0) >= 3)  # 新增代码+Phase71GenericInputActions: 汇总连续路径能力；如果没有这行代码，拖拽可能退化成跳点。
    forbidden_system_hotkeys_blocked = bool(all(not result.get("ok") and result.get("input_event_count") == 0 and result.get("forbidden_system_hotkeys_blocked") for result in forbidden_results) and len(sender.events) == event_count_before_forbidden)  # 新增代码+Phase71GenericInputActions: 汇总危险热键零事件拒绝；如果没有这行代码，系统热键风险不可见。
    real_dispatch_blocked = bool(all(event.get("real_dispatch_allowed") is False for event in sender.events))  # 新增代码+Phase71GenericInputActions: 确认所有事件仍禁止真实派发；如果没有这行代码，本阶段可能提前扩大动作面。
    passed = bool(hotkey_action and menu_navigation and scroll_action and drag_action and continuous_mouse_path and forbidden_system_hotkeys_blocked and real_dispatch_blocked and not PHASE71_ACTIONS_EXPANDED)  # 新增代码+Phase71GenericInputActions: 汇总合同通过条件；如果没有这行代码，main 无法用退出码表达失败。
    return {"marker": PHASE71_GENERIC_INPUT_ACTIONS_MARKER, "ok_token": PHASE71_GENERIC_INPUT_ACTIONS_OK_TOKEN, "model": PHASE71_GENERIC_INPUT_ACTIONS_MODEL, "hotkey_action": hotkey_action, "menu_navigation": menu_navigation, "scroll_action": scroll_action, "drag_action": drag_action, "continuous_mouse_path": continuous_mouse_path, "forbidden_system_hotkeys_blocked": forbidden_system_hotkeys_blocked, "real_dispatch_blocked": real_dispatch_blocked, "actions_expanded": PHASE71_ACTIONS_EXPANDED, "passed": passed, "results": {"hotkey": hotkey, "menu": menu, "scroll": scroll, "drag": drag, "forbidden": forbidden_results}, "recorded_event_count": len(sender.events), "events_preview": sender.events[:12]}  # 新增代码+Phase71GenericInputActions: 返回完整合同报告；如果没有这行代码，测试和 CLI 拿不到统一结果。
# 新增代码+Phase71GenericInputActions: 函数段结束，run_phase71_generic_input_actions_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase71_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase71GenericInputActions: 函数段开始，把报告转成稳定 token 行；如果没有这个函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE71_GENERIC_INPUT_ACTIONS_MARKER} {PHASE71_GENERIC_INPUT_ACTIONS_OK_TOKEN} hotkey_action={_phase71_bool_token(report.get('hotkey_action'))} menu_navigation={_phase71_bool_token(report.get('menu_navigation'))} scroll_action={_phase71_bool_token(report.get('scroll_action'))} drag_action={_phase71_bool_token(report.get('drag_action'))} continuous_mouse_path={_phase71_bool_token(report.get('continuous_mouse_path'))} forbidden_system_hotkeys_blocked={_phase71_bool_token(report.get('forbidden_system_hotkeys_blocked'))} actions_expanded={_phase71_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase71GenericInputActions: 返回固定顺序 token；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase71GenericInputActions: 函数段结束，phase71_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase71GenericInputActions: 函数段开始，提供命令行入口；如果没有这个函数，真实终端无法执行 Phase71 验收。
    _ = argv  # 新增代码+Phase71GenericInputActions: 保留 argv 以便未来扩展；如果没有这行代码，静态检查可能提示未使用参数。
    report = run_phase71_generic_input_actions_contract()  # 新增代码+Phase71GenericInputActions: 执行合同自检；如果没有这行代码，CLI 不会验证 Phase71 能力。
    print(phase71_cli_line(report))  # 新增代码+Phase71GenericInputActions: 打印稳定 token 行；如果没有这行代码，debug log 无法确认验收结果。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase71GenericInputActions: 打印结构化报告便于失败复盘；如果没有这行代码，失败时不易定位原因。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase71GenericInputActions: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成功。
# 新增代码+Phase71GenericInputActions: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["PHASE71_ACTIONS_EXPANDED", "PHASE71_GENERIC_INPUT_ACTIONS_MARKER", "PHASE71_GENERIC_INPUT_ACTIONS_MODEL", "PHASE71_GENERIC_INPUT_ACTIONS_OK_TOKEN", "Phase71RecordingInputSender", "WindowsGenericInputActionRuntime", "build_drag_path", "build_hotkey_events", "build_menu_sequence", "build_scroll_events", "main", "phase71_cli_line", "run_phase71_generic_input_actions_contract"]  # 新增代码+Phase71GenericInputActions: 限定公开导出名称；如果没有这行代码，包导入容易暴露内部 helper 或漏掉合同入口。


if __name__ == "__main__":  # 新增代码+Phase71GenericInputActions: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase71GenericInputActions: 调用 main 并传递退出码；如果没有这行代码，命令行状态不明确。
