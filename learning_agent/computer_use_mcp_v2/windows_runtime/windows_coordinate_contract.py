"""Cua Driver 借鉴的 Windows 坐标与目标身份合同。"""  # 新增代码+CuaDriverBorrowing：说明本模块专门收口坐标空间和目标身份规则；如果没有这一行，读者不知道该文件为何存在。
from __future__ import annotations  # 新增代码+CuaDriverBorrowing：启用延迟类型解析；如果没有这一行，部分类型标注在旧入口下可能提前求值失败。

from typing import Any, Mapping  # 新增代码+CuaDriverBorrowing：导入通用映射类型；如果没有这一行，本模块无法用清晰类型表达外部传入的字典数据。

CUA_DRIVER_BORROWING_COORDINATE_CONTRACT_MODEL = "cua_driver_borrowing_coordinate_contract_v1"  # 新增代码+CuaDriverBorrowing：标记当前坐标合同版本；如果没有这一行，日志和测试无法确认正在使用哪版规则。
WINDOW_LOCAL = "window_local"  # 新增代码+CuaDriverBorrowing：定义窗口局部坐标名称；如果没有这一行，调用方容易把 x/y 误解成屏幕坐标。
SCREEN_PHYSICAL = "screen_physical"  # 新增代码+CuaDriverBorrowing：定义屏幕物理坐标名称；如果没有这一行，跨 DPI 或窗口偏移时没有稳定输出标签。
SCREENSHOT_LOCAL = "screenshot_local"  # 新增代码+CuaDriverBorrowing：定义截图局部坐标名称；如果没有这一行，视觉模型返回的截图坐标没有明确归类。


# 新增代码+CuaDriverBorrowing：函数段开始，_safe_int 把外部输入尽量转成整数；如果没有这段函数，坐标和 pid 的字符串输入会在比较时漂移。
def _safe_int(value: Any) -> int | None:  # 新增代码+CuaDriverBorrowing：定义安全整数转换入口；如果没有这一行，后续函数只能重复写脆弱转换逻辑。
    try:  # 新增代码+CuaDriverBorrowing：开始捕获转换异常；如果没有这一行，坏输入会直接抛异常打断 agent。
        return int(value)  # 新增代码+CuaDriverBorrowing：返回整数形式；如果没有这一行，字符串数字无法参与坐标计算或 pid 比较。
    except (TypeError, ValueError):  # 新增代码+CuaDriverBorrowing：捕获无法转换的输入；如果没有这一行，None 或非数字文本会导致崩溃。
        return None  # 新增代码+CuaDriverBorrowing：用 None 表示转换失败；如果没有这一行，调用方无法失败关闭。
# 新增代码+CuaDriverBorrowing：函数段结束，_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出转换逻辑范围。


# 新增代码+CuaDriverBorrowing：函数段开始，_mapping_get_any 从多个候选键读取同一个语义字段；如果没有这段函数，pid/window_id 的兼容字段会散落各处。
def _mapping_get_any(data: Mapping[str, Any], *keys: str) -> Any:  # 新增代码+CuaDriverBorrowing：定义多键读取入口；如果没有这一行，调用方不能统一处理 pid/process_id/processId。
    for key in keys:  # 新增代码+CuaDriverBorrowing：逐个尝试候选键；如果没有这一行，只有第一个键会被识别。
        if key in data:  # 新增代码+CuaDriverBorrowing：确认当前键存在；如果没有这一行，缺失键会被误当成有效值。
            return data[key]  # 新增代码+CuaDriverBorrowing：返回第一个命中的值；如果没有这一行，兼容读取不会产生结果。
    return None  # 新增代码+CuaDriverBorrowing：所有候选都缺失时返回 None；如果没有这一行，调用方无法区分缺字段和空字符串。
# 新增代码+CuaDriverBorrowing：函数段结束，_mapping_get_any 到此结束；如果没有这个边界说明，初学者不容易看出兼容读取范围。


# 新增代码+CuaDriverBorrowing：函数段开始，_rect_from_window 解析窗口矩形；如果没有这段函数，窗口局部坐标无法稳定加上窗口原点。
def _rect_from_window(window: Mapping[str, Any]) -> Mapping[str, Any] | None:  # 新增代码+CuaDriverBorrowing：定义窗口矩形提取入口；如果没有这一行，调用方不知道函数期待窗口字典。
    rect = window.get("rect")  # 新增代码+CuaDriverBorrowing：优先读取 rect 字段；如果没有这一行，常见窗口结构无法被识别。
    if isinstance(rect, Mapping):  # 新增代码+CuaDriverBorrowing：确认 rect 是映射对象；如果没有这一行，字符串或列表会被误当成矩形。
        return rect  # 新增代码+CuaDriverBorrowing：返回有效矩形；如果没有这一行，坐标转换拿不到 left/top。
    bounds = window.get("bounds")  # 新增代码+CuaDriverBorrowing：兼容读取 bounds 字段；如果没有这一行，UIA 节点风格窗口数据无法复用。
    if isinstance(bounds, Mapping):  # 新增代码+CuaDriverBorrowing：确认 bounds 是映射对象；如果没有这一行，错误结构会进入坐标计算。
        return bounds  # 新增代码+CuaDriverBorrowing：返回兼容矩形；如果没有这一行，使用 bounds 的调用方会转换失败。
    return None  # 新增代码+CuaDriverBorrowing：没有可用矩形时返回 None；如果没有这一行，调用方无法失败关闭。
# 新增代码+CuaDriverBorrowing：函数段结束，_rect_from_window 到此结束；如果没有这个边界说明，初学者不容易看出矩形解析范围。


# 新增代码+CuaDriverBorrowing：函数段开始，window_local_to_screen 将窗口内坐标转换为屏幕物理坐标；如果没有这段函数，动作层容易把相对坐标当绝对坐标误点。
def window_local_to_screen(window: Mapping[str, Any], x: Any, y: Any) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义窗口坐标转换入口；如果没有这一行，外部无法复用统一转换规则。
    rect = _rect_from_window(window)  # 新增代码+CuaDriverBorrowing：读取窗口矩形；如果没有这一行，坐标没有窗口原点。
    local_x = _safe_int(x)  # 新增代码+CuaDriverBorrowing：把局部 x 转为整数；如果没有这一行，字符串数字不能安全相加。
    local_y = _safe_int(y)  # 新增代码+CuaDriverBorrowing：把局部 y 转为整数；如果没有这一行，字符串数字不能安全相加。
    left = _safe_int(rect.get("left") if rect is not None else None)  # 新增代码+CuaDriverBorrowing：读取窗口左边界；如果没有这一行，屏幕 x 没有偏移基准。
    top = _safe_int(rect.get("top") if rect is not None else None)  # 新增代码+CuaDriverBorrowing：读取窗口上边界；如果没有这一行，屏幕 y 没有偏移基准。
    if local_x is None or local_y is None or left is None or top is None:  # 新增代码+CuaDriverBorrowing：检查转换必需字段；如果没有这一行，坏输入会产生错误坐标。
        return {"ok": False, "reason": "window_rect_or_coordinate_invalid", "coordinate_space": SCREEN_PHYSICAL}  # 新增代码+CuaDriverBorrowing：失败关闭并说明原因；如果没有这一行，调用方不知道为什么不能点击。
    return {"x": left + local_x, "y": top + local_y, "coordinate_space": SCREEN_PHYSICAL}  # 新增代码+CuaDriverBorrowing：返回屏幕物理坐标；如果没有这一行，窗口内点击无法落到正确屏幕点。
# 新增代码+CuaDriverBorrowing：函数段结束，window_local_to_screen 到此结束；如果没有这个边界说明，初学者不容易看出坐标转换范围。


# 新增代码+CuaDriverBorrowing：函数段开始，target_identity_from_mapping 统一提取 pid/window_id；如果没有这段函数，动作层会出现多套目标身份格式。
def target_identity_from_mapping(data: Mapping[str, Any] | None) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义目标身份提取入口；如果没有这一行，调用方无法把不同字典规范化。
    source = data or {}  # 新增代码+CuaDriverBorrowing：把 None 转为空字典；如果没有这一行，缺目标时会直接异常。
    process_id = _safe_int(_mapping_get_any(source, "pid", "process_id", "processId"))  # 新增代码+CuaDriverBorrowing：兼容提取进程 id；如果没有这一行，同一进程可能因字段名不同被误拒绝。
    window_id = _mapping_get_any(source, "window_id", "windowId", "hwnd", "target_window_id")  # 新增代码+CuaDriverBorrowing：兼容提取窗口 id；如果没有这一行，同一窗口可能因字段名不同无法比较。
    if window_id is not None and not isinstance(window_id, str):  # 新增代码+CuaDriverBorrowing：检查窗口 id 是否需要转文本；如果没有这一行，数字 hwnd 和文本 hwnd 比较会漂移。
        window_id = str(window_id)  # 新增代码+CuaDriverBorrowing：把窗口 id 统一成文本；如果没有这一行，不同来源的 hwnd 类型会不一致。
    return {"pid": process_id, "window_id": window_id}  # 新增代码+CuaDriverBorrowing：返回统一身份结构；如果没有这一行，严格匹配函数没有稳定输入。
# 新增代码+CuaDriverBorrowing：函数段结束，target_identity_from_mapping 到此结束；如果没有这个边界说明，初学者不容易看出目标身份提取范围。


# 新增代码+CuaDriverBorrowing：函数段开始，strict_target_identity_matches 严格比较动作目标是否仍是观察目标；如果没有这段函数，agent 可能在窗口切换后误操作。
def strict_target_identity_matches(expected: Mapping[str, Any] | None, actual: Mapping[str, Any] | None) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义严格身份比较入口；如果没有这一行，外部无法得到稳定 ok/reason 结果。
    expected_identity = target_identity_from_mapping(expected)  # 新增代码+CuaDriverBorrowing：规范化预期目标；如果没有这一行，字段名差异会影响比较。
    actual_identity = target_identity_from_mapping(actual)  # 新增代码+CuaDriverBorrowing：规范化实际目标；如果没有这一行，当前窗口身份无法稳定比较。
    if expected_identity["pid"] is None or expected_identity["window_id"] is None:  # 新增代码+CuaDriverBorrowing：检查预期身份是否完整；如果没有这一行，缺目标时可能误退到活动窗口。
        return {"ok": False, "reason": "target_identity_incomplete", "expected": expected_identity, "actual": actual_identity}  # 新增代码+CuaDriverBorrowing：失败关闭并返回证据；如果没有这一行，调用方无法解释缺哪个身份字段。
    if actual_identity["pid"] is None or actual_identity["window_id"] is None:  # 新增代码+CuaDriverBorrowing：检查实际身份是否完整；如果没有这一行，无法确认当前窗口时仍可能继续执行。
        return {"ok": False, "reason": "target_identity_incomplete", "expected": expected_identity, "actual": actual_identity}  # 新增代码+CuaDriverBorrowing：失败关闭并返回证据；如果没有这一行，动作层无法向用户说明当前目标不可验证。
    if expected_identity != actual_identity:  # 新增代码+CuaDriverBorrowing：比较 pid 和 window_id 是否完全一致；如果没有这一行，跨进程或跨窗口误操作不会被拦住。
        return {"ok": False, "reason": "target_identity_mismatch", "expected": expected_identity, "actual": actual_identity}  # 新增代码+CuaDriverBorrowing：返回不匹配原因；如果没有这一行，调用方无法决定重新观察或停止。
    return {"ok": True, "reason": "target_identity_match", "expected": expected_identity, "actual": actual_identity}  # 新增代码+CuaDriverBorrowing：确认身份一致；如果没有这一行，合法动作无法继续。
# 新增代码+CuaDriverBorrowing：函数段结束，strict_target_identity_matches 到此结束；如果没有这个边界说明，初学者不容易看出严格匹配范围。


# 新增代码+CuaDriverBorrowing：函数段开始，_present_coordinate_spaces 判断请求里出现了哪些坐标空间；如果没有这段函数，混用坐标字段无法被稳定拒绝。
def _present_coordinate_spaces(arguments: Mapping[str, Any]) -> list[str]:  # 新增代码+CuaDriverBorrowing：定义坐标空间识别入口；如果没有这一行，规范化函数无法知道 payload 使用了哪类坐标。
    spaces: list[str] = []  # 新增代码+CuaDriverBorrowing：初始化出现的坐标空间列表；如果没有这一行，后续追加没有容器。
    explicit_space = arguments.get("coordinate_space")  # 新增代码+CuaDriverBorrowing：读取显式坐标空间；如果没有这一行，模型主动声明的空间会被忽略。
    if explicit_space in {WINDOW_LOCAL, SCREEN_PHYSICAL, SCREENSHOT_LOCAL}:  # 新增代码+CuaDriverBorrowing：只接受已知坐标空间；如果没有这一行，未知字符串会污染合同。
        spaces.append(str(explicit_space))  # 新增代码+CuaDriverBorrowing：记录显式坐标空间；如果没有这一行，显式声明不会参与混用判断。
    if "x" in arguments or "y" in arguments:  # 新增代码+CuaDriverBorrowing：识别窗口局部坐标字段；如果没有这一行，常规 x/y 不会被纳入合同。
        spaces.append(WINDOW_LOCAL)  # 新增代码+CuaDriverBorrowing：记录窗口局部坐标；如果没有这一行，x/y 可能被误当作任意坐标。
    if "screen_x" in arguments or "screen_y" in arguments:  # 新增代码+CuaDriverBorrowing：识别屏幕物理坐标字段；如果没有这一行，screen_x/screen_y 混用不会被发现。
        spaces.append(SCREEN_PHYSICAL)  # 新增代码+CuaDriverBorrowing：记录屏幕物理坐标；如果没有这一行，绝对坐标没有明确标签。
    if "screenshot_x" in arguments or "screenshot_y" in arguments:  # 新增代码+CuaDriverBorrowing：识别截图局部坐标字段；如果没有这一行，视觉截图坐标混用不会被发现。
        spaces.append(SCREENSHOT_LOCAL)  # 新增代码+CuaDriverBorrowing：记录截图局部坐标；如果没有这一行，截图坐标无法进入规范化。
    return list(dict.fromkeys(spaces))  # 新增代码+CuaDriverBorrowing：按出现顺序去重返回；如果没有这一行，显式声明和字段一致时会被误判混用。
# 新增代码+CuaDriverBorrowing：函数段结束，_present_coordinate_spaces 到此结束；如果没有这个边界说明，初学者不容易看出坐标空间识别范围。


# 新增代码+CuaDriverBorrowing：函数段开始，_coordinates_for_space 根据空间读取具体 x/y；如果没有这段函数，规范化函数会混杂大量分支难以维护。
def _coordinates_for_space(arguments: Mapping[str, Any], coordinate_space: str) -> tuple[int | None, int | None]:  # 新增代码+CuaDriverBorrowing：定义按空间读取坐标入口；如果没有这一行，调用方不能统一取出 x/y。
    if coordinate_space == SCREEN_PHYSICAL:  # 新增代码+CuaDriverBorrowing：判断是否为屏幕物理坐标；如果没有这一行，screen_x/screen_y 不会被正确读取。
        return _safe_int(arguments.get("screen_x", arguments.get("x"))), _safe_int(arguments.get("screen_y", arguments.get("y")))  # 新增代码+CuaDriverBorrowing：读取屏幕坐标并兼容显式空间下的 x/y；如果没有这一行，显式 screen_physical 的 payload 可能失效。
    if coordinate_space == SCREENSHOT_LOCAL:  # 新增代码+CuaDriverBorrowing：判断是否为截图局部坐标；如果没有这一行，视觉坐标不会被正确读取。
        return _safe_int(arguments.get("screenshot_x", arguments.get("x"))), _safe_int(arguments.get("screenshot_y", arguments.get("y")))  # 新增代码+CuaDriverBorrowing：读取截图坐标并兼容显式空间下的 x/y；如果没有这一行，截图坐标无法规范化。
    return _safe_int(arguments.get("x")), _safe_int(arguments.get("y"))  # 新增代码+CuaDriverBorrowing：默认读取窗口局部 x/y；如果没有这一行，常规点击参数无法继续。
# 新增代码+CuaDriverBorrowing：函数段结束，_coordinates_for_space 到此结束；如果没有这个边界说明，初学者不容易看出坐标读取范围。


# 新增代码+CuaDriverBorrowing：函数段开始，normalize_coordinate_request 将外部坐标 payload 规范化；如果没有这段函数，动作执行层会重复处理易错坐标组合。
def normalize_coordinate_request(arguments: Mapping[str, Any]) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义坐标请求规范化入口；如果没有这一行，外部无法得到稳定 ok/reason 输出。
    spaces = _present_coordinate_spaces(arguments)  # 新增代码+CuaDriverBorrowing：识别 payload 中的坐标空间；如果没有这一行，无法判断是否混用。
    if len(spaces) > 1:  # 新增代码+CuaDriverBorrowing：检查是否同时出现多个坐标空间；如果没有这一行，模型混传坐标会继续执行。
        return {"ok": False, "reason": "mixed_coordinate_spaces", "coordinate_spaces": spaces}  # 新增代码+CuaDriverBorrowing：拒绝混用坐标并返回证据；如果没有这一行，误点风险无法被上层解释。
    coordinate_space = spaces[0] if spaces else WINDOW_LOCAL  # 新增代码+CuaDriverBorrowing：没有显式字段时默认窗口局部坐标；如果没有这一行，传统 x/y 调用无法保持兼容。
    x, y = _coordinates_for_space(arguments, coordinate_space)  # 新增代码+CuaDriverBorrowing：读取对应空间的坐标值；如果没有这一行，规范化结果没有坐标。
    if x is None or y is None:  # 新增代码+CuaDriverBorrowing：检查坐标是否完整有效；如果没有这一行，缺 x 或缺 y 也可能进入动作层。
        return {"ok": False, "reason": "coordinate_incomplete", "coordinate_space": coordinate_space, "x": x, "y": y}  # 新增代码+CuaDriverBorrowing：失败关闭并说明缺坐标；如果没有这一行，调用方无法提示模型补参。
    return {"ok": True, "reason": "coordinate_normalized", "coordinate_space": coordinate_space, "x": x, "y": y}  # 新增代码+CuaDriverBorrowing：返回规范化坐标；如果没有这一行，动作层拿不到统一格式。
# 新增代码+CuaDriverBorrowing：函数段结束，normalize_coordinate_request 到此结束；如果没有这个边界说明，初学者不容易看出坐标规范化范围。


__all__ = [  # 新增代码+CuaDriverBorrowing：声明公开 API 开始；如果没有这一行，外部不清楚哪些名字是稳定接口。
    "CUA_DRIVER_BORROWING_COORDINATE_CONTRACT_MODEL",  # 新增代码+CuaDriverBorrowing：公开合同版本；如果没有这一行，测试和诊断无法读取版本标记。
    "WINDOW_LOCAL",  # 新增代码+CuaDriverBorrowing：公开窗口局部坐标常量；如果没有这一行，调用方只能硬编码字符串。
    "SCREEN_PHYSICAL",  # 新增代码+CuaDriverBorrowing：公开屏幕物理坐标常量；如果没有这一行，调用方只能硬编码字符串。
    "SCREENSHOT_LOCAL",  # 新增代码+CuaDriverBorrowing：公开截图局部坐标常量；如果没有这一行，调用方只能硬编码字符串。
    "normalize_coordinate_request",  # 新增代码+CuaDriverBorrowing：公开坐标规范化函数；如果没有这一行，上层无法按合同调用。
    "strict_target_identity_matches",  # 新增代码+CuaDriverBorrowing：公开严格身份匹配函数；如果没有这一行，上层无法复用目标校验。
    "target_identity_from_mapping",  # 新增代码+CuaDriverBorrowing：公开目标身份提取函数；如果没有这一行，日志和测试无法规范化目标字段。
    "window_local_to_screen",  # 新增代码+CuaDriverBorrowing：公开窗口坐标转换函数；如果没有这一行，动作层无法复用转换规则。
]  # 新增代码+CuaDriverBorrowing：声明公开 API 结束；如果没有这一行，公开列表语法不完整。
