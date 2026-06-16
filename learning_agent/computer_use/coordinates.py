"""Windows Computer Use DPI、多显示器和坐标模型。"""  # 新增代码+Phase39WindowsCoordinates: 说明本文件集中处理坐标空间；如果没有本文件，动作策略会继续把逻辑坐标和物理坐标混在一起。
from __future__ import annotations  # 新增代码+Phase39WindowsCoordinates: 延迟解析类型注解；如果没有这行代码，旧导入路径遇到前向类型时更容易失败。

from typing import Any  # 新增代码+Phase39WindowsCoordinates: 引入通用 JSON 值类型；如果没有这行代码，窗口和显示器输入边界不清楚。

PHASE39_WINDOWS_COORDINATES_MARKER = "PHASE39_WINDOWS_COORDINATES_READY"  # 新增代码+Phase39WindowsCoordinates: 固定 Phase39 验收 marker；如果没有这行代码，真实终端验收无法稳定匹配阶段完成信号。
PHASE39_WINDOWS_COORDINATES_OK_TOKEN = "PHASE39_WINDOWS_COORDINATES_OK"  # 新增代码+Phase39WindowsCoordinates: 固定 Phase39 自检 OK token；如果没有这行代码，验收无法区分普通输出和自检成功。
PHASE39_COORDINATE_MODEL = "phase39_windows_coordinate_model"  # 新增代码+Phase39WindowsCoordinates: 固定坐标模型版本；如果没有这行代码，审计证据无法说明坐标由哪套规则生成。
SCREENSHOT_COORDINATE_MODEL = "claudecode_parity_screenshot_coordinate_mapping_v1"  # 新增代码+ClaudeCodeParityScreenshot: 定义截图坐标映射合同版本；如果没有这行代码，后续 zoom 和审计无法判断截图 scale 字段属于哪个稳定协议。
PHASE39_ACTIONS_EXPANDED = False  # 新增代码+Phase39WindowsCoordinates: 明确本阶段只改坐标模型不扩大动作范围；如果没有这行代码，用户可能误解为新增了更多真实动作。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，safe_float 用于安全读取缩放和坐标数字；如果没有这段函数，坏输入会让坐标模型崩溃。
def safe_float(value: Any, default: float = 0.0) -> float:  # 新增代码+Phase39WindowsCoordinates: 定义安全浮点转换函数；如果没有这行代码，每个缩放读取点都要重复 try/except。
    try:  # 新增代码+Phase39WindowsCoordinates: 尝试把输入转成 float；如果没有这行代码，字符串数字无法兼容。
        return float(value)  # 新增代码+Phase39WindowsCoordinates: 返回浮点数；如果没有这行代码，坐标和缩放无法参与计算。
    except (TypeError, ValueError):  # 新增代码+Phase39WindowsCoordinates: 捕获空值和非数字文本；如果没有这行代码，模型输入稍坏就会抛异常。
        return float(default)  # 新增代码+Phase39WindowsCoordinates: 返回默认值兜底；如果没有这行代码，调用方无法继续生成安全上下文。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，safe_float 到此结束；如果没有这个边界说明，初学者不容易看出转换 helper 的范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，safe_int 用于把计算结果变成 Windows 后端需要的整数像素；如果没有这段函数，坐标可能以浮点传给鼠标键盘后端。
def safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase39WindowsCoordinates: 定义安全整数转换函数；如果没有这行代码，物理像素取整规则会分散到各处。
    try:  # 新增代码+Phase39WindowsCoordinates: 尝试把输入转成浮点再四舍五入；如果没有这行代码，字符串或浮点坐标无法统一处理。
        return int(round(float(value)))  # 新增代码+Phase39WindowsCoordinates: 返回四舍五入后的整数；如果没有这行代码，DPI 后的像素可能带小数导致后端失败。
    except (TypeError, ValueError):  # 新增代码+Phase39WindowsCoordinates: 捕获坏输入；如果没有这行代码，坐标模型会因为单个坏字段中断。
        return int(default)  # 新增代码+Phase39WindowsCoordinates: 返回默认整数；如果没有这行代码，调用方拿不到兜底坐标。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，safe_int 到此结束；如果没有这个边界说明，读者不容易看出取整 helper 的范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，rect_from_mapping 用于规范化 left/top/right/bottom；如果没有这段函数，窗口矩形和显示器矩形会有多套读取规则。
def rect_from_mapping(value: Any) -> dict[str, int]:  # 新增代码+Phase39WindowsCoordinates: 定义矩形归一化函数；如果没有这行代码，坏 rect 会污染后续计算。
    raw_rect = value if isinstance(value, dict) else {}  # 新增代码+Phase39WindowsCoordinates: 只信任 dict 形式矩形；如果没有这行代码，字符串或 None 会导致 get 调用失败。
    return {"left": safe_int(raw_rect.get("left")), "top": safe_int(raw_rect.get("top")), "right": safe_int(raw_rect.get("right")), "bottom": safe_int(raw_rect.get("bottom"))}  # 新增代码+Phase39WindowsCoordinates: 返回标准四边矩形；如果没有这行代码，坐标模型无法统一读取边界。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，rect_from_mapping 到此结束；如果没有这个边界说明，读者不容易看出矩形归一化范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，rect_width 用于计算矩形宽度；如果没有这段函数，缩放推导会重复写 right-left。
def rect_width(rect: dict[str, int]) -> int:  # 新增代码+Phase39WindowsCoordinates: 定义宽度计算函数；如果没有这行代码，宽度计算可能出现负值。
    return max(0, safe_int(rect.get("right")) - safe_int(rect.get("left")))  # 新增代码+Phase39WindowsCoordinates: 返回非负宽度；如果没有这行代码，异常矩形会影响 DPI 推导。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，rect_width 到此结束；如果没有这个边界说明，读者不容易看出宽度 helper 的范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，rect_height 用于计算矩形高度；如果没有这段函数，缩放推导会重复写 bottom-top。
def rect_height(rect: dict[str, int]) -> int:  # 新增代码+Phase39WindowsCoordinates: 定义高度计算函数；如果没有这行代码，高度计算可能出现负值。
    return max(0, safe_int(rect.get("bottom")) - safe_int(rect.get("top")))  # 新增代码+Phase39WindowsCoordinates: 返回非负高度；如果没有这行代码，异常矩形会影响 DPI 推导。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，rect_height 到此结束；如果没有这个边界说明，读者不容易看出高度 helper 的范围。


# 新增代码+ClaudeCodeParityScreenshot: 函数段开始，build_screenshot_coordinate_mapping 只描述“窗口逻辑坐标如何换成截图像素坐标”；如果没有这段函数，result、image_result 和 metadata 会各自猜 scale，作者意图是给后续 zoom 复用同一个稳定合同。
def build_screenshot_coordinate_mapping(window: Any, screenshot_width: Any, screenshot_height: Any) -> dict[str, Any]:  # 新增代码+ClaudeCodeParityScreenshot: 定义截图坐标映射 helper；如果没有这行代码，evidence 层无法复用坐标模块的安全兜底规则。
    raw_window = window if isinstance(window, dict) else {}  # 新增代码+ClaudeCodeParityScreenshot: 只信任 dict 窗口对象；如果没有这行代码，None 或字符串窗口会导致 rect 读取异常。
    window_rect = rect_from_mapping(raw_window.get("rect", {}))  # 新增代码+ClaudeCodeParityScreenshot: 归一化窗口逻辑 rect；如果没有这行代码，scale 计算会直接依赖不稳定原始字段。
    window_width = rect_width(window_rect)  # 新增代码+ClaudeCodeParityScreenshot: 计算窗口逻辑宽度；如果没有这行代码，scale_x 没有可靠分母。
    window_height = rect_height(window_rect)  # 新增代码+ClaudeCodeParityScreenshot: 计算窗口逻辑高度；如果没有这行代码，scale_y 没有可靠分母。
    pixel_width = max(0, safe_int(screenshot_width))  # 新增代码+ClaudeCodeParityScreenshot: 归一化截图像素宽度并避免负数；如果没有这行代码，坏 provider 尺寸可能污染 metadata。
    pixel_height = max(0, safe_int(screenshot_height))  # 新增代码+ClaudeCodeParityScreenshot: 归一化截图像素高度并避免负数；如果没有这行代码，坏 provider 尺寸可能污染 metadata。
    valid = window_width > 0 and window_height > 0 and pixel_width > 0 and pixel_height > 0  # 新增代码+ClaudeCodeParityScreenshot: 判断是否具备真实可换算尺寸；如果没有这行代码，零宽高会触发除零或产生误导 scale。
    scale_x = round(pixel_width / window_width, 6) if valid else 1.0  # 新增代码+ClaudeCodeParityScreenshot: 计算窗口相对逻辑 x 到截图像素 x 的比例；如果没有这行代码，后续 zoom 无法精确换算横向坐标。
    scale_y = round(pixel_height / window_height, 6) if valid else 1.0  # 新增代码+ClaudeCodeParityScreenshot: 计算窗口相对逻辑 y 到截图像素 y 的比例；如果没有这行代码，后续 zoom 无法精确换算纵向坐标。
    fallback_reason = "" if valid else "invalid_window_rect_or_screenshot_size"  # 新增代码+ClaudeCodeParityScreenshot: 记录安全兜底原因；如果没有这行代码，审计时不知道为什么 scale 回落到 1.0。
    window_logical_rect = {"left": window_rect["left"], "top": window_rect["top"], "right": window_rect["right"], "bottom": window_rect["bottom"], "width": window_width, "height": window_height}  # 新增代码+ClaudeCodeParityScreenshot: 输出带宽高的窗口逻辑 rect；如果没有这行代码，调用方需要重复计算窗口尺寸。
    screenshot_pixel_rect = {"left": 0, "top": 0, "right": pixel_width, "bottom": pixel_height, "width": pixel_width, "height": pixel_height}  # 新增代码+ClaudeCodeParityScreenshot: 输出截图像素 rect；如果没有这行代码，模型只知道尺寸但不知道截图坐标原点。
    return {"model": SCREENSHOT_COORDINATE_MODEL, "source": "window_rect_and_screenshot_size", "coordinate_space": "window_relative_logical_to_screenshot_pixel", "valid": valid, "fallback_reason": fallback_reason, "window_logical_rect": window_logical_rect, "screenshot_pixel_rect": screenshot_pixel_rect, "screenshot_pixel_size": {"width": pixel_width, "height": pixel_height}, "window_relative_logical_to_screenshot_pixel": {"source": "window_rect_and_screenshot_size", "coordinate_space": "window_relative_logical", "target_coordinate_space": "screenshot_pixel", "scale_x": scale_x, "scale_y": scale_y, "offset_x": 0.0, "offset_y": 0.0}}  # 新增代码+ClaudeCodeParityScreenshot: 返回完整映射合同；如果没有这行代码，result、图片块和 metadata 无法共享同一份 scale 说明。
# 新增代码+ClaudeCodeParityScreenshot: 函数段结束，build_screenshot_coordinate_mapping 到此结束；如果没有这个边界说明，用户不容易看出截图映射 helper 的范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，scaled_rect 用于把逻辑矩形换算成物理矩形；如果没有这段函数，窗口状态无法报告物理边界。
def scaled_rect(rect: dict[str, int], display: dict[str, Any]) -> dict[str, int]:  # 新增代码+Phase39WindowsCoordinates: 定义矩形缩放函数；如果没有这行代码，高 DPI 窗口边界无法统一生成。
    logical_display = rect_from_mapping(display.get("logical_rect", {}))  # 新增代码+Phase39WindowsCoordinates: 读取显示器逻辑矩形；如果没有这行代码，无法计算窗口相对显示器原点的位置。
    physical_display = rect_from_mapping(display.get("physical_rect", {}))  # 新增代码+Phase39WindowsCoordinates: 读取显示器物理矩形；如果没有这行代码，无法把相对坐标放回物理屏幕。
    scale = dict(display.get("dpi_scale", {"x": 1.0, "y": 1.0}))  # 新增代码+Phase39WindowsCoordinates: 读取 x/y 缩放；如果没有这行代码，缩放时只能假设 1.0。
    return {"left": physical_display["left"] + safe_int((rect["left"] - logical_display["left"]) * safe_float(scale.get("x"), 1.0)), "top": physical_display["top"] + safe_int((rect["top"] - logical_display["top"]) * safe_float(scale.get("y"), 1.0)), "right": physical_display["left"] + safe_int((rect["right"] - logical_display["left"]) * safe_float(scale.get("x"), 1.0)), "bottom": physical_display["top"] + safe_int((rect["bottom"] - logical_display["top"]) * safe_float(scale.get("y"), 1.0))}  # 新增代码+Phase39WindowsCoordinates: 返回物理矩形；如果没有这行代码，窗口状态无法解释截图和动作像素边界。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，scaled_rect 到此结束；如果没有这个边界说明，读者不容易看出矩形换算范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，display_contains_point 用于判断逻辑坐标属于哪块显示器；如果没有这段函数，多显示器选择会退化成固定第一块屏。
def display_contains_point(display: dict[str, Any], x: int, y: int) -> bool:  # 新增代码+Phase39WindowsCoordinates: 定义显示器包含点判断；如果没有这行代码，负坐标副屏无法被正确选中。
    rect = rect_from_mapping(display.get("logical_rect", {}))  # 新增代码+Phase39WindowsCoordinates: 读取显示器逻辑矩形；如果没有这行代码，无法比较坐标范围。
    return rect["left"] <= x < rect["right"] and rect["top"] <= y < rect["bottom"]  # 新增代码+Phase39WindowsCoordinates: 判断点是否落在显示器内；如果没有这行代码，模型无法安全选择显示器。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，display_contains_point 到此结束；如果没有这个边界说明，读者不容易看出显示器匹配范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，normalize_display 用于统一显示器元数据；如果没有这段函数，不同来源的 DPI/display 字段会产生不同格式。
def normalize_display(raw_display: Any, window_rect: dict[str, int]) -> dict[str, Any]:  # 新增代码+Phase39WindowsCoordinates: 定义显示器归一化函数；如果没有这行代码，坐标模型无法容忍缺失 display 字段。
    source = raw_display if isinstance(raw_display, dict) else {}  # 新增代码+Phase39WindowsCoordinates: 只信任 dict 显示器数据；如果没有这行代码，坏输入会导致 get 调用失败。
    logical_rect = rect_from_mapping(source.get("logical_rect", source.get("rect", {"left": 0, "top": 0, "right": max(1, window_rect["right"]), "bottom": max(1, window_rect["bottom"])})))  # 新增代码+Phase39WindowsCoordinates: 读取逻辑显示器范围并提供兜底；如果没有这行代码，缺 display 时坐标模型无法运行。
    raw_scale_x = source.get("scale_x", source.get("scale", None))  # 新增代码+Phase39WindowsCoordinates: 读取 x 缩放候选；如果没有这行代码，显式 scale 字段不会生效。
    raw_scale_y = source.get("scale_y", source.get("scale", None))  # 新增代码+Phase39WindowsCoordinates: 读取 y 缩放候选；如果没有这行代码，显式 scale 字段不会生效。
    physical_rect = rect_from_mapping(source.get("physical_rect", {}))  # 新增代码+Phase39WindowsCoordinates: 读取物理显示器范围；如果没有这行代码，无法从物理尺寸反推缩放。
    logical_width = max(1, rect_width(logical_rect))  # 新增代码+Phase39WindowsCoordinates: 计算逻辑宽度并避免除零；如果没有这行代码，坏显示器矩形会导致除零。
    logical_height = max(1, rect_height(logical_rect))  # 新增代码+Phase39WindowsCoordinates: 计算逻辑高度并避免除零；如果没有这行代码，坏显示器矩形会导致除零。
    scale_x = safe_float(raw_scale_x, 0.0) or (rect_width(physical_rect) / logical_width if rect_width(physical_rect) else 1.0)  # 新增代码+Phase39WindowsCoordinates: 优先用显式缩放，否则用物理/逻辑宽度推导；如果没有这行代码，高 DPI 无法自动解释。
    scale_y = safe_float(raw_scale_y, 0.0) or (rect_height(physical_rect) / logical_height if rect_height(physical_rect) else 1.0)  # 新增代码+Phase39WindowsCoordinates: 优先用显式缩放，否则用物理/逻辑高度推导；如果没有这行代码，纵向缩放无法解释。
    if rect_width(physical_rect) <= 0 or rect_height(physical_rect) <= 0:  # 新增代码+Phase39WindowsCoordinates: 判断物理矩形是否缺失；如果没有这行代码，缺字段会保留零尺寸物理屏。
        physical_rect = {"left": safe_int(logical_rect["left"] * scale_x), "top": safe_int(logical_rect["top"] * scale_y), "right": safe_int(logical_rect["right"] * scale_x), "bottom": safe_int(logical_rect["bottom"] * scale_y)}  # 新增代码+Phase39WindowsCoordinates: 用逻辑矩形和缩放推导物理矩形；如果没有这行代码，默认路径没有物理坐标范围。
    return {"display_id": str(source.get("display_id", source.get("id", "primary")) or "primary"), "logical_rect": logical_rect, "physical_rect": physical_rect, "dpi_scale": {"x": round(float(scale_x), 4), "y": round(float(scale_y), 4)}}  # 新增代码+Phase39WindowsCoordinates: 返回统一显示器对象；如果没有这行代码，后续上下文没有稳定字段。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，normalize_display 到此结束；如果没有这个边界说明，读者不容易看出显示器归一化范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，display_candidates_for_window 用于收集可选显示器；如果没有这段函数，窗口里的 display/displays 字段无法兼容。
def display_candidates_for_window(window: dict[str, Any], window_rect: dict[str, int]) -> list[dict[str, Any]]:  # 新增代码+Phase39WindowsCoordinates: 定义候选显示器收集函数；如果没有这行代码，多显示器数据来源会分散。
    raw_displays = window.get("displays") if isinstance(window.get("displays"), list) else []  # 新增代码+Phase39WindowsCoordinates: 读取 displays 列表；如果没有这行代码，真实多显示器列表无法参与选择。
    if not raw_displays and isinstance(window.get("display"), dict):  # 新增代码+Phase39WindowsCoordinates: 没有列表但有单个 display 时使用它；如果没有这行代码，静态测试和普通窗口元数据会被忽略。
        raw_displays = [window.get("display")]  # 新增代码+Phase39WindowsCoordinates: 把单个 display 包装成列表；如果没有这行代码，后续统一处理无法进行。
    if not raw_displays:  # 新增代码+Phase39WindowsCoordinates: 如果窗口没有显示器数据则进入兜底；如果没有这行代码，默认路径会没有候选显示器。
        raw_displays = [{"display_id": "primary", "logical_rect": {"left": 0, "top": 0, "right": max(1, window_rect["right"]), "bottom": max(1, window_rect["bottom"])}, "scale": 1.0}]  # 新增代码+Phase39WindowsCoordinates: 构造主屏 1.0 缩放兜底；如果没有这行代码，旧 Phase30 窗口会无法换算。
    return [normalize_display(display, window_rect) for display in raw_displays]  # 新增代码+Phase39WindowsCoordinates: 返回归一化候选列表；如果没有这行代码，调用方拿不到统一显示器对象。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，display_candidates_for_window 到此结束；如果没有这个边界说明，读者不容易看出显示器候选范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，select_display_for_point 用于从候选显示器里选中逻辑点所在屏幕；如果没有这段函数，多显示器坐标无法稳定落屏。
def select_display_for_point(displays: list[dict[str, Any]], logical_x: int, logical_y: int) -> dict[str, Any]:  # 新增代码+Phase39WindowsCoordinates: 定义显示器选择函数；如果没有这行代码，坐标模型不知道该用哪块屏的缩放。
    for display in displays:  # 新增代码+Phase39WindowsCoordinates: 遍历候选显示器；如果没有这行代码，只能使用第一块屏幕。
        if display_contains_point(display, logical_x, logical_y):  # 新增代码+Phase39WindowsCoordinates: 检查逻辑点是否位于该显示器；如果没有这行代码，负坐标和副屏会被误判。
            return display  # 新增代码+Phase39WindowsCoordinates: 返回命中的显示器；如果没有这行代码，匹配结果无法交给后续换算。
    return displays[0] if displays else normalize_display({}, {"left": 0, "top": 0, "right": max(1, logical_x), "bottom": max(1, logical_y)})  # 新增代码+Phase39WindowsCoordinates: 无匹配时安全退回第一块或默认显示器；如果没有这行代码，空候选会导致异常。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，select_display_for_point 到此结束；如果没有这个边界说明，读者不容易看出显示器选择范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，build_coordinate_context 是 Phase39 的核心 API；如果没有这段函数，动作和状态无法共享同一套坐标解释。
def build_coordinate_context(window: Any, relative_x: Any = 0, relative_y: Any = 0) -> dict[str, Any]:  # 新增代码+Phase39WindowsCoordinates: 构建窗口相对、逻辑屏幕、显示器相对和物理屏幕坐标；如果没有这行代码，DPI 坐标无法被统一审计。
    raw_window = window if isinstance(window, dict) else {}  # 新增代码+Phase39WindowsCoordinates: 只信任 dict 窗口对象；如果没有这行代码，坏窗口输入会导致 get 调用失败。
    window_rect = rect_from_mapping(raw_window.get("rect", {}))  # 新增代码+Phase39WindowsCoordinates: 读取窗口逻辑矩形；如果没有这行代码，窗口相对坐标没有原点。
    rel_x = safe_int(relative_x)  # 新增代码+Phase39WindowsCoordinates: 规范化窗口相对 x；如果没有这行代码，字符串坐标无法参与加法。
    rel_y = safe_int(relative_y)  # 新增代码+Phase39WindowsCoordinates: 规范化窗口相对 y；如果没有这行代码，字符串坐标无法参与加法。
    logical_x = safe_int(window_rect.get("left")) + rel_x  # 新增代码+Phase39WindowsCoordinates: 计算逻辑屏幕 x；如果没有这行代码，窗口内坐标不会转换到屏幕空间。
    logical_y = safe_int(window_rect.get("top")) + rel_y  # 新增代码+Phase39WindowsCoordinates: 计算逻辑屏幕 y；如果没有这行代码，窗口内坐标不会转换到屏幕空间。
    displays = display_candidates_for_window(raw_window, window_rect)  # 新增代码+Phase39WindowsCoordinates: 获取归一化显示器候选；如果没有这行代码，DPI 和多显示器元数据无法使用。
    display = select_display_for_point(displays, logical_x, logical_y)  # 新增代码+Phase39WindowsCoordinates: 选择坐标所在显示器；如果没有这行代码，副屏和主屏缩放会混用。
    logical_display = rect_from_mapping(display.get("logical_rect", {}))  # 新增代码+Phase39WindowsCoordinates: 读取显示器逻辑矩形；如果没有这行代码，无法计算 display-relative 逻辑坐标。
    physical_display = rect_from_mapping(display.get("physical_rect", {}))  # 新增代码+Phase39WindowsCoordinates: 读取显示器物理矩形；如果没有这行代码，无法计算物理屏幕坐标。
    scale = dict(display.get("dpi_scale", {"x": 1.0, "y": 1.0}))  # 新增代码+Phase39WindowsCoordinates: 读取 x/y 缩放；如果没有这行代码，物理坐标无法体现 DPI。
    display_relative_x = logical_x - logical_display["left"]  # 新增代码+Phase39WindowsCoordinates: 计算相对显示器原点的逻辑 x；如果没有这行代码，多显示器偏移无法解释。
    display_relative_y = logical_y - logical_display["top"]  # 新增代码+Phase39WindowsCoordinates: 计算相对显示器原点的逻辑 y；如果没有这行代码，多显示器偏移无法解释。
    physical_x = physical_display["left"] + safe_int(display_relative_x * safe_float(scale.get("x"), 1.0))  # 新增代码+Phase39WindowsCoordinates: 计算物理屏幕 x；如果没有这行代码，高 DPI 点击会继续使用逻辑坐标。
    physical_y = physical_display["top"] + safe_int(display_relative_y * safe_float(scale.get("y"), 1.0))  # 新增代码+Phase39WindowsCoordinates: 计算物理屏幕 y；如果没有这行代码，高 DPI 点击会继续使用逻辑坐标。
    return {"model": PHASE39_COORDINATE_MODEL, "source": "window_relative", "space": "physical_screen", "window_relative": {"x": rel_x, "y": rel_y}, "logical_screen": {"x": logical_x, "y": logical_y}, "display_relative_logical": {"x": display_relative_x, "y": display_relative_y}, "physical_screen": {"x": physical_x, "y": physical_y}, "window_logical_rect": window_rect, "window_physical_rect": scaled_rect(window_rect, display), "display": {"display_id": display["display_id"], "logical_rect": display["logical_rect"], "physical_rect": display["physical_rect"]}, "dpi_scale": display["dpi_scale"]}  # 新增代码+Phase39WindowsCoordinates: 返回完整坐标上下文；如果没有这行代码，动作、截图和审计无法共享统一解释。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，build_coordinate_context 到此结束；如果没有这个边界说明，读者不容易看出核心坐标模型范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，run_phase39_coordinates_contract 用于真实终端自检；如果没有这段函数，验收只能依赖单测而不能在 agent 终端打印稳定标记。
def run_phase39_coordinates_contract() -> dict[str, Any]:  # 新增代码+Phase39WindowsCoordinates: 运行 DPI、多显示器、动作策略和窗口状态四类合同自检；如果没有这行代码，CLI 输出没有结构化依据。
    primary_window = {"app_id": "notepad.exe", "window_id": "hwnd:3901", "title_preview": "Phase39 Notepad", "rect": {"left": 100, "top": 50, "right": 400, "bottom": 250}, "display": {"display_id": "primary", "logical_rect": {"left": 0, "top": 0, "right": 800, "bottom": 600}, "physical_rect": {"left": 0, "top": 0, "right": 1200, "bottom": 900}, "scale": 1.5}}  # 新增代码+Phase39WindowsCoordinates: 构造 150% 缩放窗口样本；如果没有这行代码，自检无法证明 DPI 换算。
    left_window = {"app_id": "notepad.exe", "window_id": "hwnd:3902", "title_preview": "Phase39 Left Monitor", "rect": {"left": -700, "top": 100, "right": -300, "bottom": 400}, "display": {"display_id": "left-monitor", "logical_rect": {"left": -800, "top": 0, "right": 0, "bottom": 600}, "physical_rect": {"left": -800, "top": 0, "right": 0, "bottom": 600}, "scale": 1.0}}  # 新增代码+Phase39WindowsCoordinates: 构造负坐标副屏窗口样本；如果没有这行代码，自检无法证明多显示器换算。
    dpi_context = build_coordinate_context(primary_window, 10, 20)  # 新增代码+Phase39WindowsCoordinates: 生成 DPI 坐标上下文；如果没有这行代码，自检无法检查物理像素。
    monitor_context = build_coordinate_context(left_window, 25, 40)  # 新增代码+Phase39WindowsCoordinates: 生成副屏坐标上下文；如果没有这行代码，自检无法检查负坐标。
    try:  # 新增代码+Phase39WindowsCoordinates: 延迟导入动作策略和控制器避免模块顶层循环；如果没有这行代码，包导入顺序可能出问题。
        from learning_agent.computer_use.action_policy import prepare_action_arguments  # 新增代码+Phase39WindowsCoordinates: 包模式导入动作策略；如果没有这行代码，自检无法证明执行链接入。
        from learning_agent.computer_use.controller import ComputerUseController, WindowsComputerUseBackend  # 新增代码+Phase39WindowsCoordinates: 包模式导入控制器和 Windows 后端；如果没有这行代码，自检无法证明 observe 状态接入。
        from learning_agent.computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase39WindowsCoordinates: 包模式导入静态 inventory；如果没有这行代码，自检会依赖真实桌面。
    except ModuleNotFoundError as error:  # 新增代码+Phase39WindowsCoordinates: 捕获 start_oauth_agent 脚本模式下包名前缀不可用；如果没有这行代码，真实终端自检可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.action_policy", "learning_agent.computer_use.controller", "learning_agent.computer_use.windows_backend"}:  # 新增代码+Phase39WindowsCoordinates: 只允许目标包路径缺失时 fallback；如果没有这行代码，内部真实 bug 会被误吞。
            raise  # 新增代码+Phase39WindowsCoordinates: 重新抛出非路径类导入错误；如果没有这行代码，排查会被错误 fallback 掩盖。
        from computer_use.action_policy import prepare_action_arguments  # 新增代码+Phase39WindowsCoordinates: 脚本模式导入动作策略；如果没有这行代码，bat 入口自检无法运行。
        from computer_use.controller import ComputerUseController, WindowsComputerUseBackend  # 新增代码+Phase39WindowsCoordinates: 脚本模式导入控制器和 Windows 后端；如果没有这行代码，bat 入口无法验证状态接入。
        from computer_use.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase39WindowsCoordinates: 脚本模式导入静态 inventory；如果没有这行代码，bat 入口无法构造安全窗口。
    prepared = prepare_action_arguments("click", {"window": primary_window, "x": 10, "y": 20})  # 新增代码+Phase39WindowsCoordinates: 通过真实动作策略准备点击参数；如果没有这行代码，自检无法确认后端坐标是物理像素。
    inventory = StaticWindowsWindowInventory([primary_window], captured_at="2026-06-03T00:00:00Z", source="phase39_contract")  # 新增代码+Phase39WindowsCoordinates: 构建静态 inventory；如果没有这行代码，自检会触碰真实桌面。
    backend = WindowsComputerUseBackend(inventory=inventory, real_actions_enabled=False)  # 新增代码+Phase39WindowsCoordinates: 构建只读 Windows 后端；如果没有这行代码，自检无法走 get_window_state。
    result = ComputerUseController(backend=backend).observe({"action": "get_window_state", "window": {"app_id": "notepad.exe", "window_id": "hwnd:3901"}})  # 新增代码+Phase39WindowsCoordinates: 通过控制器读取窗口状态；如果没有这行代码，自检无法证明公开入口带坐标上下文。
    return {"marker": PHASE39_WINDOWS_COORDINATES_MARKER, "dpi": dpi_context["physical_screen"] == {"x": 165, "y": 105}, "multi_monitor": monitor_context["physical_screen"] == {"x": -675, "y": 140}, "action_policy": prepared["backend_arguments"].get("x") == 165 and prepared["coordinate_used"].get("model") == PHASE39_COORDINATE_MODEL, "window_state": bool(result.ok and result.data.get("coordinate_model") == PHASE39_COORDINATE_MODEL), "actions_expanded": PHASE39_ACTIONS_EXPANDED}  # 新增代码+Phase39WindowsCoordinates: 返回自检摘要；如果没有这行代码，CLI 无法打印可验收结果。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，run_phase39_coordinates_contract 到此结束；如果没有这个边界说明，读者不容易看出自检范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，phase39_cli_line 用于生成终端稳定输出；如果没有这段函数，验收 token 可能在不同调用中漂移。
def phase39_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase39WindowsCoordinates: 把结构化报告转成一行 token 文本；如果没有这行代码，真实终端断言无法简单匹配。
    return f"{PHASE39_WINDOWS_COORDINATES_OK_TOKEN} dpi={str(bool(report.get('dpi'))).lower()} multi_monitor={str(bool(report.get('multi_monitor'))).lower()} action_policy={str(bool(report.get('action_policy'))).lower()} window_state={str(bool(report.get('window_state'))).lower()} actions_expanded={str(bool(report.get('actions_expanded'))).lower()} marker={PHASE39_WINDOWS_COORDINATES_MARKER}"  # 新增代码+Phase39WindowsCoordinates: 返回稳定自检行；如果没有这行代码，acceptance scenario 不知道该查什么。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，phase39_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 文本范围。


# 新增代码+Phase39WindowsCoordinates: 函数段开始，main 是 python -m 入口；如果没有这段函数，真实终端场景无法直接运行 Phase39 自检。
def main() -> int:  # 新增代码+Phase39WindowsCoordinates: 定义命令行入口；如果没有这行代码，验收只能手写 Python 表达式。
    print(phase39_cli_line(run_phase39_coordinates_contract()))  # 新增代码+Phase39WindowsCoordinates: 打印稳定自检 token；如果没有这行代码，真实终端不会出现验收标记。
    return 0  # 新增代码+Phase39WindowsCoordinates: 返回成功退出码；如果没有这行代码，调用方无法稳定判断命令完成。
# 新增代码+Phase39WindowsCoordinates: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出命令行入口范围。


if __name__ == "__main__":  # 新增代码+Phase39WindowsCoordinates: 支持直接执行本模块；如果没有这行代码，python 文件运行时不会触发自检。
    raise SystemExit(main())  # 新增代码+Phase39WindowsCoordinates: 用 main 的返回码退出；如果没有这行代码，命令行场景无法得到稳定退出状态。
