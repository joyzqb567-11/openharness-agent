"""Display pinning and coordinate conversion helpers for Windows Computer Use."""  # 新增代码+Phase3DisplayPin：说明本文件负责显示器固定和坐标换算；如果没有这一行，用户不知道这个模块不是直接点击桌面的动作层。
from __future__ import annotations  # 新增代码+Phase3DisplayPin：启用延迟类型解析；如果没有这一行，类型注解在旧导入顺序下更容易出错。

from typing import Any  # 新增代码+Phase3DisplayPin：导入 Any 描述 JSON 风格 display/context 数据；如果没有这一行，函数签名无法表达外部输入可能来自不同工具层。

try:  # 新增代码+Phase3DisplayPin：优先使用包路径导入 session store；如果没有这一段，单元测试和包运行会重复写导入逻辑。
    from learning_agent.computer_use_mcp_v2.windows_runtime.session_context import ComputerUseSessionContextStore  # 新增代码+Phase3DisplayPin：复用统一 session 事实源；如果没有这一行，display pin 状态会散落到临时变量里。
except ModuleNotFoundError as error:  # 新增代码+Phase3DisplayPin：兼容 start_oauth_agent.bat 可能采用的脚本模式；如果没有这一段，真实终端入口在不同工作目录下可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime"}:  # 新增代码+Phase3DisplayPin：只对包根缺失做兜底；如果没有这一行，真实依赖错误会被误吞。
        raise  # 新增代码+Phase3DisplayPin：重新抛出非路径类错误；如果没有这一行，内部 bug 会被隐藏。
    from computer_use_mcp_v2.windows_runtime.session_context import ComputerUseSessionContextStore  # type: ignore  # 新增代码+Phase3DisplayPin：脚本模式下复用同一个 session store；如果没有这一行，bat 入口无法保存显示器状态。

PHASE3_DISPLAY_COORDINATE_MODEL = "phase3_display_coordinate_session"  # 新增代码+Phase3DisplayPin：定义坐标模型名；如果没有这一行，审计结果无法说明坐标来自哪套规则。


def _phase3_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase3DisplayPin：函数段开始，把外部数值安全转成整数；如果没有这段函数，坏坐标输入可能让换算崩溃。
    try:  # 新增代码+Phase3DisplayPin：进入安全转换区；如果没有这一行，字符串或 None 会直接抛错。
        return int(round(float(value)))  # 新增代码+Phase3DisplayPin：先转浮点再四舍五入成整数；如果没有这一行，高 DPI 小数坐标无法稳定落到像素。
    except (TypeError, ValueError):  # 新增代码+Phase3DisplayPin：捕获空值和非数字文本；如果没有这一行，坏输入会中断整个 agent 回合。
        return int(default)  # 新增代码+Phase3DisplayPin：返回兜底整数；如果没有这一行，失败路径没有安全结果。
# 新增代码+Phase3DisplayPin：函数段结束，_phase3_safe_int 到此结束；如果没有这个边界说明，用户不容易看出整数清理范围。


def _phase3_safe_float(value: Any, default: float = 1.0) -> float:  # 新增代码+Phase3DisplayPin：函数段开始，把外部数值安全转成浮点数；如果没有这段函数，坏缩放输入可能让坐标换算失败。
    try:  # 新增代码+Phase3DisplayPin：进入安全转换区；如果没有这一行，字符串或 None 会直接抛错。
        converted = float(value)  # 新增代码+Phase3DisplayPin：尝试转成浮点数；如果没有这一行，缩放比例无法参与计算。
    except (TypeError, ValueError):  # 新增代码+Phase3DisplayPin：捕获空值和非数字文本；如果没有这一行，坏 display 元数据会打断流程。
        converted = float(default)  # 新增代码+Phase3DisplayPin：使用默认缩放；如果没有这一行，失败路径没有可用比例。
    return converted if converted > 0 else float(default)  # 新增代码+Phase3DisplayPin：禁止 0 或负缩放；如果没有这一行，坐标换算可能除以 0 或反向漂移。
# 新增代码+Phase3DisplayPin：函数段结束，_phase3_safe_float 到此结束；如果没有这个边界说明，用户不容易看出缩放清理范围。


def _phase3_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase3DisplayPin：函数段开始，把外部对象安全复制成字典；如果没有这段函数，坏 display/context 类型可能污染后续逻辑。
    return dict(value or {}) if isinstance(value, dict) else {}  # 新增代码+Phase3DisplayPin：只接受 dict 并复制；如果没有这一行，列表或字符串会让字段读取崩溃。
# 新增代码+Phase3DisplayPin：函数段结束，_phase3_dict 到此结束；如果没有这个边界说明，用户不容易看出字典清理范围。


def _phase3_rect(value: Any) -> dict[str, int]:  # 新增代码+Phase3DisplayPin：函数段开始，规范化显示器矩形；如果没有这段函数，不同工具层的 x/y/width 写法无法统一。
    raw = _phase3_dict(value)  # 新增代码+Phase3DisplayPin：复制原始矩形字典；如果没有这一行，后续读取可能直接操作外部对象。
    left = _phase3_safe_int(raw.get("left", raw.get("x", 0)))  # 新增代码+Phase3DisplayPin：读取左边界或 x；如果没有这一行，多屏原点会丢失。
    top = _phase3_safe_int(raw.get("top", raw.get("y", 0)))  # 新增代码+Phase3DisplayPin：读取上边界或 y；如果没有这一行，纵向屏幕偏移会丢失。
    right = _phase3_safe_int(raw.get("right", left + _phase3_safe_int(raw.get("width", 0))))  # 新增代码+Phase3DisplayPin：读取右边界或用宽度推导；如果没有这一行，矩形宽度无法计算。
    bottom = _phase3_safe_int(raw.get("bottom", top + _phase3_safe_int(raw.get("height", 0))))  # 新增代码+Phase3DisplayPin：读取下边界或用高度推导；如果没有这一行，矩形高度无法计算。
    return {"left": left, "top": top, "right": max(right, left + 1), "bottom": max(bottom, top + 1)}  # 新增代码+Phase3DisplayPin：返回至少 1 像素的矩形；如果没有这一行，零尺寸屏幕会导致除零。
# 新增代码+Phase3DisplayPin：函数段结束，_phase3_rect 到此结束；如果没有这个边界说明，用户不容易看出矩形清理范围。


def _phase3_rect_size(rect: dict[str, int]) -> dict[str, int]:  # 新增代码+Phase3DisplayPin：函数段开始，从矩形计算宽高；如果没有这段函数，多个地方会重复写边界相减。
    return {"width": max(1, int(rect["right"] - rect["left"])), "height": max(1, int(rect["bottom"] - rect["top"]))}  # 新增代码+Phase3DisplayPin：返回最小 1 的宽高；如果没有这一行，截图或显示器尺寸为 0 时会除零。
# 新增代码+Phase3DisplayPin：函数段结束，_phase3_rect_size 到此结束；如果没有这个边界说明，用户不容易看出尺寸推导范围。


def _phase3_display_id(display: Any) -> str:  # 新增代码+Phase3DisplayPin：函数段开始，提取稳定显示器身份；如果没有这段函数，多屏状态无法判断哪块屏幕消失。
    raw = _phase3_dict(display)  # 新增代码+Phase3DisplayPin：复制显示器元数据；如果没有这一行，字段读取会直接依赖外部对象。
    text = str(raw.get("display_id") or raw.get("id") or raw.get("name") or "primary").strip()  # 新增代码+Phase3DisplayPin：按常见字段提取显示器 id；如果没有这一行，不同后端命名无法兼容。
    return text or "primary"  # 新增代码+Phase3DisplayPin：空 id 回退 primary；如果没有这一行，空字符串会让 pin 清理误判。
# 新增代码+Phase3DisplayPin：函数段结束，_phase3_display_id 到此结束；如果没有这个边界说明，用户不容易看出显示器身份规则。


def _phase3_scale_from_display(display: dict[str, Any], logical_rect: dict[str, int], physical_rect: dict[str, int]) -> dict[str, float]:  # 新增代码+Phase3DisplayPin：函数段开始，计算 DPI 缩放；如果没有这段函数，高 DPI 坐标会从截图位置漂移。
    scale_source = _phase3_dict(display.get("dpi_scale") or display.get("scale"))  # 新增代码+Phase3DisplayPin：优先读取后端提供的缩放字段；如果没有这一行，已知 DPI 信息会被浪费。
    logical_size = _phase3_rect_size(logical_rect)  # 新增代码+Phase3DisplayPin：计算逻辑宽高；如果没有这一行，缺少显式缩放时无法从矩形推导比例。
    physical_size = _phase3_rect_size(physical_rect)  # 新增代码+Phase3DisplayPin：计算物理宽高；如果没有这一行，缺少显式缩放时无法从物理矩形推导比例。
    inferred_x = physical_size["width"] / logical_size["width"]  # 新增代码+Phase3DisplayPin：从宽度推导横向缩放；如果没有这一行，只有物理矩形时无法处理 DPI。
    inferred_y = physical_size["height"] / logical_size["height"]  # 新增代码+Phase3DisplayPin：从高度推导纵向缩放；如果没有这一行，只有物理矩形时无法处理 DPI。
    return {"x": _phase3_safe_float(scale_source.get("x", scale_source.get("width", inferred_x)), inferred_x), "y": _phase3_safe_float(scale_source.get("y", scale_source.get("height", inferred_y)), inferred_y)}  # 新增代码+Phase3DisplayPin：返回最终 x/y 缩放；如果没有这一行，坐标换算没有 DPI 基准。
# 新增代码+Phase3DisplayPin：函数段结束，_phase3_scale_from_display 到此结束；如果没有这个边界说明，用户不容易看出缩放来源范围。


def _phase3_infer_physical_rect(display: dict[str, Any], logical_rect: dict[str, int]) -> dict[str, int]:  # 新增代码+Phase3DisplayPin：函数段开始，补齐物理矩形；如果没有这段函数，部分后端只给逻辑矩形时无法换算物理坐标。
    if isinstance(display.get("physical_rect"), dict):  # 新增代码+Phase3DisplayPin：优先使用真实物理矩形；如果没有这一行，可靠的后端事实可能被重复推导覆盖。
        return _phase3_rect(display.get("physical_rect"))  # 新增代码+Phase3DisplayPin：规范化并返回物理矩形；如果没有这一行，物理原点和边界无法进入 pin 状态。
    scale_source = _phase3_dict(display.get("dpi_scale") or display.get("scale"))  # 新增代码+Phase3DisplayPin：读取缩放来源用于推导物理尺寸；如果没有这一行，缺少 physical_rect 时只能假设 1 倍。
    scale_x = _phase3_safe_float(scale_source.get("x", scale_source.get("width", 1.0)), 1.0)  # 新增代码+Phase3DisplayPin：读取横向缩放；如果没有这一行，推导物理宽度没有比例。
    scale_y = _phase3_safe_float(scale_source.get("y", scale_source.get("height", 1.0)), 1.0)  # 新增代码+Phase3DisplayPin：读取纵向缩放；如果没有这一行，推导物理高度没有比例。
    return {"left": _phase3_safe_int(logical_rect["left"] * scale_x), "top": _phase3_safe_int(logical_rect["top"] * scale_y), "right": _phase3_safe_int(logical_rect["right"] * scale_x), "bottom": _phase3_safe_int(logical_rect["bottom"] * scale_y)}  # 新增代码+Phase3DisplayPin：用逻辑矩形和缩放推导物理矩形；如果没有这一行，坐标换算缺少物理屏幕目标。
# 新增代码+Phase3DisplayPin：函数段结束，_phase3_infer_physical_rect 到此结束；如果没有这个边界说明，用户不容易看出物理矩形推导范围。


def _phase3_screenshot_dims(value: Any, logical_rect: dict[str, int]) -> dict[str, int]:  # 新增代码+Phase3DisplayPin：函数段开始，规范化截图尺寸；如果没有这段函数，模型坐标无法按截图比例映射回屏幕。
    raw = _phase3_dict(value)  # 新增代码+Phase3DisplayPin：复制截图尺寸输入；如果没有这一行，字段读取会直接依赖外部对象。
    fallback = _phase3_rect_size(logical_rect)  # 新增代码+Phase3DisplayPin：用逻辑显示器尺寸作为兜底；如果没有这一行，缺少截图尺寸时会除零。
    width = _phase3_safe_int(raw.get("width", raw.get("w", fallback["width"])), fallback["width"])  # 新增代码+Phase3DisplayPin：读取截图宽度；如果没有这一行，横向模型坐标无法按比例换算。
    height = _phase3_safe_int(raw.get("height", raw.get("h", fallback["height"])), fallback["height"])  # 新增代码+Phase3DisplayPin：读取截图高度；如果没有这一行，纵向模型坐标无法按比例换算。
    return {"width": max(1, width), "height": max(1, height)}  # 新增代码+Phase3DisplayPin：返回最小 1 的截图尺寸；如果没有这一行，坏输入会导致除零。
# 新增代码+Phase3DisplayPin：函数段结束，_phase3_screenshot_dims 到此结束；如果没有这个边界说明，用户不容易看出截图尺寸清理范围。


def normalize_pinned_display(display: Any, screenshot_dims: Any) -> dict[str, Any]:  # 新增代码+Phase3DisplayPin：函数段开始，生成可持久化的固定显示器状态；如果没有这段函数，pin 状态会因后端字段差异而不稳定。
    display_dict = _phase3_dict(display)  # 新增代码+Phase3DisplayPin：复制显示器输入；如果没有这一行，后续规范化可能污染调用方对象。
    logical_rect = _phase3_rect(display_dict.get("logical_rect") or display_dict.get("bounds") or display_dict.get("rect"))  # 新增代码+Phase3DisplayPin：读取逻辑屏幕矩形；如果没有这一行，模型截图坐标没有逻辑原点。
    physical_rect = _phase3_infer_physical_rect(display_dict, logical_rect)  # 新增代码+Phase3DisplayPin：读取或推导物理屏幕矩形；如果没有这一行，真实点击坐标没有物理目标。
    scale = _phase3_scale_from_display(display_dict, logical_rect, physical_rect)  # 新增代码+Phase3DisplayPin：计算 DPI 缩放；如果没有这一行，高 DPI 点击会漂移。
    dims = _phase3_screenshot_dims(screenshot_dims, logical_rect)  # 新增代码+Phase3DisplayPin：规范化截图尺寸；如果没有这一行，模型坐标比例无法复现。
    origin = {"logical_x": logical_rect["left"], "logical_y": logical_rect["top"], "physical_x": physical_rect["left"], "physical_y": physical_rect["top"]}  # 新增代码+Phase3DisplayPin：保存逻辑和物理原点；如果没有这一行，多屏副屏偏移会丢失。
    return {"display_id": _phase3_display_id(display_dict), "logical_rect": logical_rect, "physical_rect": physical_rect, "dpi_scale": scale, "display_origin": origin, "screenshot_dims": dims, "coordinate_model": PHASE3_DISPLAY_COORDINATE_MODEL}  # 新增代码+Phase3DisplayPin：返回完整可审计显示器状态；如果没有这一行，session context 没有稳定 pin 事实。
# 新增代码+Phase3DisplayPin：函数段结束，normalize_pinned_display 到此结束；如果没有这个边界说明，用户不容易看出显示器规范化范围。


def pin_display_for_screenshot(store: ComputerUseSessionContextStore, session_id: Any, display: Any, screenshot_dims: Any) -> dict[str, Any]:  # 新增代码+Phase3DisplayPin：函数段开始，把一次截图绑定到具体显示器；如果没有这段函数，多屏任务会丢失截图来自哪块屏。
    pinned_display = normalize_pinned_display(display, screenshot_dims)  # 新增代码+Phase3DisplayPin：生成规范化显示器状态；如果没有这一行，落盘字段会不完整。
    dims = dict(pinned_display["screenshot_dims"])  # 新增代码+Phase3DisplayPin：复制截图尺寸；如果没有这一行，context 写入可能共享内部对象。
    context = store.bind_context(session_id, selected_display=pinned_display, last_screenshot_dims=dims, display_pinned=True, display_origin=dict(pinned_display["display_origin"]), display_scale=dict(pinned_display["dpi_scale"]))  # 新增代码+Phase3DisplayPin：把 pin 状态写入 session context；如果没有这一行，后续动作无法复用同一显示器坐标。
    return {"display_pinned": True, "session_id": context["session_id"], "selected_display": pinned_display, "last_screenshot_dims": dims, "coordinate_model": PHASE3_DISPLAY_COORDINATE_MODEL}  # 新增代码+Phase3DisplayPin：返回本次 pin 摘要；如果没有这一行，调用方无法确认状态已经落盘。
# 新增代码+Phase3DisplayPin：函数段结束，pin_display_for_screenshot 到此结束；如果没有这个边界说明，用户不容易看出 pin 写入范围。


def clear_display_pin_if_missing(store: ComputerUseSessionContextStore, session_id: Any, available_displays: Any) -> dict[str, Any]:  # 新增代码+Phase3DisplayPin：函数段开始，当固定显示器消失时清理旧 pin；如果没有这段函数，拔掉副屏后旧坐标仍可能被使用。
    context = store.snapshot(session_id)  # 新增代码+Phase3DisplayPin：读取当前 session 状态；如果没有这一行，函数不知道是否已经 pin。
    selected_display = _phase3_dict(context.get("selected_display"))  # 新增代码+Phase3DisplayPin：提取已固定显示器；如果没有这一行，坏状态会让清理逻辑崩溃。
    selected_id = _phase3_display_id(selected_display) if selected_display else ""  # 新增代码+Phase3DisplayPin：取得已固定显示器 id；如果没有这一行，无法和当前显示器列表比较。
    available_ids = {_phase3_display_id(item) for item in list(available_displays or []) if isinstance(item, dict)}  # 新增代码+Phase3DisplayPin：收集当前仍存在的显示器 id；如果没有这一行，消失判断没有事实来源。
    if not bool(context.get("display_pinned")) or not selected_id:  # 新增代码+Phase3DisplayPin：没有 pin 时不做清理；如果没有这一行，普通状态可能被误清空。
        return {"display_pin_cleared": False, "reason": "not_pinned", "context": context, "coordinate_model": PHASE3_DISPLAY_COORDINATE_MODEL}  # 新增代码+Phase3DisplayPin：返回未清理报告；如果没有这一行，调用方无法区分无 pin 和清理失败。
    if selected_id in available_ids:  # 新增代码+Phase3DisplayPin：固定显示器仍存在时保留状态；如果没有这一行，多屏正常场景会被误清理。
        return {"display_pin_cleared": False, "reason": "pinned_display_still_available", "context": context, "coordinate_model": PHASE3_DISPLAY_COORDINATE_MODEL}  # 新增代码+Phase3DisplayPin：返回保留报告；如果没有这一行，调用方不知道为什么没有清理。
    updated = store.update_app_state(session_id, selected_display={}, last_screenshot_dims={}, display_pinned=False, display_origin={}, display_scale={"x": 1.0, "y": 1.0})  # 新增代码+Phase3DisplayPin：清掉过期显示器和坐标比例；如果没有这一行，旧副屏坐标会残留到下一次动作。
    return {"display_pin_cleared": True, "reason": "pinned_display_missing", "cleared_display_id": selected_id, "context": updated, "coordinate_model": PHASE3_DISPLAY_COORDINATE_MODEL}  # 新增代码+Phase3DisplayPin：返回清理成功报告；如果没有这一行，调用方无法审计是哪块屏被清掉。
# 新增代码+Phase3DisplayPin：函数段结束，clear_display_pin_if_missing 到此结束；如果没有这个边界说明，用户不容易看出 stale display 清理范围。


def _phase3_clamp(value: int, minimum: int, maximum: int) -> int:  # 新增代码+Phase3DisplayPin：函数段开始，把模型坐标夹在截图范围内；如果没有这段函数，越界点击可能落到目标屏幕外。
    return max(minimum, min(maximum, int(value)))  # 新增代码+Phase3DisplayPin：返回夹紧后的整数；如果没有这一行，越界坐标无法被收敛。
# 新增代码+Phase3DisplayPin：函数段结束，_phase3_clamp 到此结束；如果没有这个边界说明，用户不容易看出边界裁剪范围。


def model_to_display_coordinates(context: dict[str, Any], model_x: Any, model_y: Any) -> dict[str, Any]:  # 新增代码+Phase3DisplayPin：函数段开始，把模型截图坐标换算到真实显示器坐标；如果没有这段函数，agent 点击会停留在截图坐标而不是屏幕坐标。
    context_dict = _phase3_dict(context)  # 新增代码+Phase3DisplayPin：复制 context 输入；如果没有这一行，坏 context 类型会导致字段读取崩溃。
    display = _phase3_dict(context_dict.get("selected_display"))  # 新增代码+Phase3DisplayPin：读取固定显示器；如果没有这一行，换算不知道坐标属于哪块屏。
    logical_rect = _phase3_rect(display.get("logical_rect"))  # 新增代码+Phase3DisplayPin：读取逻辑屏幕矩形；如果没有这一行，副屏逻辑原点会丢失。
    physical_rect = _phase3_rect(display.get("physical_rect"))  # 新增代码+Phase3DisplayPin：读取物理屏幕矩形；如果没有这一行，高 DPI 物理坐标无法计算。
    screenshot_dims = _phase3_screenshot_dims(context_dict.get("last_screenshot_dims") or display.get("screenshot_dims"), logical_rect)  # 新增代码+Phase3DisplayPin：读取最近截图尺寸；如果没有这一行，模型坐标无法按截图比例映射。
    logical_size = _phase3_rect_size(logical_rect)  # 新增代码+Phase3DisplayPin：计算逻辑显示器宽高；如果没有这一行，逻辑坐标比例无法换算。
    physical_size = _phase3_rect_size(physical_rect)  # 新增代码+Phase3DisplayPin：计算物理显示器宽高；如果没有这一行，物理坐标比例无法换算。
    screenshot_x = _phase3_clamp(_phase3_safe_int(model_x), 0, screenshot_dims["width"])  # 新增代码+Phase3DisplayPin：清理并裁剪模型横坐标；如果没有这一行，越界 x 可能打到屏幕外。
    screenshot_y = _phase3_clamp(_phase3_safe_int(model_y), 0, screenshot_dims["height"])  # 新增代码+Phase3DisplayPin：清理并裁剪模型纵坐标；如果没有这一行，越界 y 可能打到屏幕外。
    logical_offset_x = int(round(screenshot_x * logical_size["width"] / screenshot_dims["width"]))  # 新增代码+Phase3DisplayPin：把截图 x 映射到逻辑屏幕偏移；如果没有这一行，截图比例变化会造成横向漂移。
    logical_offset_y = int(round(screenshot_y * logical_size["height"] / screenshot_dims["height"]))  # 新增代码+Phase3DisplayPin：把截图 y 映射到逻辑屏幕偏移；如果没有这一行，截图比例变化会造成纵向漂移。
    logical_x = logical_rect["left"] + logical_offset_x  # 新增代码+Phase3DisplayPin：叠加逻辑屏幕原点得到逻辑 x；如果没有这一行，副屏左侧偏移会丢失。
    logical_y = logical_rect["top"] + logical_offset_y  # 新增代码+Phase3DisplayPin：叠加逻辑屏幕原点得到逻辑 y；如果没有这一行，纵向屏幕偏移会丢失。
    physical_x = physical_rect["left"] + int(round(logical_offset_x * physical_size["width"] / logical_size["width"]))  # 新增代码+Phase3DisplayPin：按物理/逻辑比例换算物理 x；如果没有这一行，高 DPI 点击会落在错误位置。
    physical_y = physical_rect["top"] + int(round(logical_offset_y * physical_size["height"] / logical_size["height"]))  # 新增代码+Phase3DisplayPin：按物理/逻辑比例换算物理 y；如果没有这一行，高 DPI 点击会落在错误位置。
    return {"display_id": _phase3_display_id(display), "display_pinned": bool(context_dict.get("display_pinned")), "model_screenshot": {"x": screenshot_x, "y": screenshot_y}, "logical_screen": {"x": logical_x, "y": logical_y}, "physical_screen": {"x": physical_x, "y": physical_y}, "coordinate_model": PHASE3_DISPLAY_COORDINATE_MODEL}  # 新增代码+Phase3DisplayPin：返回完整坐标审计结果；如果没有这一行，调用方拿不到可执行物理坐标和解释字段。
# 新增代码+Phase3DisplayPin：函数段结束，model_to_display_coordinates 到此结束；如果没有这个边界说明，用户不容易看出坐标换算范围。


__all__ = ["PHASE3_DISPLAY_COORDINATE_MODEL", "clear_display_pin_if_missing", "model_to_display_coordinates", "normalize_pinned_display", "pin_display_for_screenshot"]  # 新增代码+Phase3DisplayPin：导出稳定 API；如果没有这一行，测试和后续动作层不知道哪些函数是正式入口。
