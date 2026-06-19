"""Build generic capability profiles from Computer Use observation frames."""  # 新增代码+CapabilityProfile：说明本文件把观察帧转成通用能力画像；如果没有这行代码，读者容易误以为这里是应用适配器。
from __future__ import annotations  # 新增代码+CapabilityProfile：启用延迟类型解析；如果没有这行代码，类型注解在旧入口导入时更容易失败。

import re  # 新增代码+CapabilityProfile：导入正则用于清洗证据文本；如果没有这行代码，窗口或控件文本可能带入噪声。
from dataclasses import dataclass, field  # 新增代码+CapabilityProfile：导入数据类工具；如果没有这行代码，能力字段会变成散乱字典。
from typing import Any, Mapping  # 新增代码+CapabilityProfile：导入 JSON 风格类型；如果没有这行代码，观察帧接口不清楚。


TEXT_CONTROL_MARKERS = ("edit", "textbox", "text", "document", "input")  # 新增代码+CapabilityProfile：定义通用文本控件标记；如果没有这行代码，文本能力只能靠应用名判断。
CANVAS_ROLE_MARKERS = ("canvas", "pane", "custom", "content", "drawing", "surface", "image")  # 新增代码+CapabilityProfile：定义通用画布区域标记；如果没有这行代码，绘图能力无法从视觉区域识别。
MENU_MARKERS = ("menu", "menubar")  # 新增代码+CapabilityProfile：定义菜单控件标记；如果没有这行代码，保存等菜单命令缺少能力来源。
TOOLBAR_MARKERS = ("toolbar", "tool bar", "ribbon")  # 新增代码+CapabilityProfile：定义工具栏控件标记；如果没有这行代码，画笔或格式按钮能力不可见。
MODAL_MARKERS = ("dialog", "modal", "window")  # 新增代码+CapabilityProfile：定义弹窗控件标记；如果没有这行代码，保存对话框和确认框难以识别。
NAV_TEXT_MARKERS = ("address", "search", "url", "location", "query")  # 新增代码+CapabilityProfile：定义导航输入语义标记；如果没有这行代码，搜索/地址栏只能靠浏览器名。
NAV_BUTTON_MARKERS = ("go", "back", "forward", "refresh", "reload", "search", "next")  # 新增代码+CapabilityProfile：定义导航按钮语义标记；如果没有这行代码，导航表面不能从控件组合推出。
SAVE_MARKERS = ("save", "保存", "另存", "file name", "filename")  # 新增代码+CapabilityProfile：定义保存相关通用语义；如果没有这行代码，提交资源阶段缺少能力信号。


@dataclass(frozen=True)  # 新增代码+CapabilityProfile：声明能力画像不可变；如果没有这行代码，后续层可能意外改写观察结论。
class AppCapabilityProfile:  # 新增代码+CapabilityProfile：类段开始，表示目标窗口的通用能力；如果没有这个类，planner 会回到应用名特判。
    has_text_input: bool = False  # 新增代码+CapabilityProfile：标记是否有文本输入能力；如果没有这行代码，文本批无法安全生成。
    has_canvas_like_region: bool = False  # 新增代码+CapabilityProfile：标记是否有画布类区域；如果没有这行代码，绘图批无法安全生成。
    has_menu_bar: bool = False  # 新增代码+CapabilityProfile：标记是否有菜单栏；如果没有这行代码，菜单命令保存路径缺少能力依据。
    has_toolbar: bool = False  # 新增代码+CapabilityProfile：标记是否有工具栏；如果没有这行代码，工具选择类动作缺少依据。
    has_file_save_surface: bool = False  # 新增代码+CapabilityProfile：标记是否有保存表面；如果没有这行代码，提交资源阶段只能猜。
    has_browser_navigation_surface: bool = False  # 新增代码+CapabilityProfile：标记是否有导航/搜索表面；如果没有这行代码，通用浏览任务只能按 app 名判断。
    has_grid_or_table: bool = False  # 新增代码+CapabilityProfile：标记是否有表格能力；如果没有这行代码，表格类软件无法泛化。
    has_modal_dialog: bool = False  # 新增代码+CapabilityProfile：标记是否有弹窗；如果没有这行代码，保存/确认阶段无法识别阻塞对话框。
    supports_keyboard_shortcuts_likely: bool = False  # 新增代码+CapabilityProfile：标记是否可能支持快捷键；如果没有这行代码，Ctrl+S 等通用策略缺置信号。
    single_instance_suspected: bool = False  # 新增代码+CapabilityProfile：标记是否疑似单实例；如果没有这行代码，旧窗口授权策略缺少输入。
    unknown_capabilities: bool = False  # 新增代码+CapabilityProfile：标记能力未知；如果没有这行代码，未知软件可能被误当可执行。
    evidence: tuple[str, ...] = field(default_factory=tuple)  # 新增代码+CapabilityProfile：保存短证据；如果没有这行代码，验收失败时无法解释画像来源。
# 新增代码+CapabilityProfile：类段结束，AppCapabilityProfile 到此结束；如果没有这个边界说明，初学者不容易看出能力字段范围。


def _capability_clean_text(value: Any) -> str:  # 新增代码+CapabilityProfile：函数段开始，清洗控件文本；如果没有这段函数，证据可能泄露长标题或换行。
    text = str(value if value is not None else "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+CapabilityProfile：把动态值转成单行；如果没有这行代码，证据字段不稳定。
    text = re.sub(r"\s+", " ", text)[:80]  # 新增代码+CapabilityProfile：压缩空白并限制长度；如果没有这行代码，控件名可能撑爆报告。
    return text  # 新增代码+CapabilityProfile：返回清洗文本；如果没有这行代码，调用方拿不到证据文本。
# 新增代码+CapabilityProfile：函数段结束，_capability_clean_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清洗范围。


def _capability_lower_blob(node: Mapping[str, Any]) -> str:  # 新增代码+CapabilityProfile：函数段开始，把节点核心字段拼成小写文本；如果没有这段函数，多处标记判断会重复。
    parts = [node.get("control_type", ""), node.get("role", ""), node.get("name", ""), node.get("class_name", ""), node.get("automation_id", ""), node.get("localized_control_type", "")]  # 新增代码+CapabilityProfile：收集通用 UIA 字段；如果没有这行代码，能力识别会漏字段。
    return " ".join(_capability_clean_text(part).lower() for part in parts if _capability_clean_text(part))  # 新增代码+CapabilityProfile：返回小写语义文本；如果没有这行代码，标记匹配不能统一大小写。
# 新增代码+CapabilityProfile：函数段结束，_capability_lower_blob 到此结束；如果没有这个边界说明，初学者不容易看出节点文本范围。


def _capability_bounds(node: Mapping[str, Any]) -> dict[str, int]:  # 新增代码+CapabilityProfile：函数段开始，读取控件或区域尺寸；如果没有这段函数，画布判断无法看面积。
    raw = node.get("bounds", node.get("rect", {})) if isinstance(node, Mapping) else {}  # 新增代码+CapabilityProfile：兼容 bounds 和 rect 字段；如果没有这行代码，不同观察源无法复用。
    bounds = raw if isinstance(raw, Mapping) else {}  # 新增代码+CapabilityProfile：确认边界是映射；如果没有这行代码，坏字段会导致异常。
    width = int(bounds.get("width", 0) or max(0, int(bounds.get("right", 0) or 0) - int(bounds.get("left", 0) or 0)))  # 新增代码+CapabilityProfile：读取或推导宽度；如果没有这行代码，大区域无法识别。
    height = int(bounds.get("height", 0) or max(0, int(bounds.get("bottom", 0) or 0) - int(bounds.get("top", 0) or 0)))  # 新增代码+CapabilityProfile：读取或推导高度；如果没有这行代码，大区域无法识别。
    return {"width": width, "height": height, "area": width * height}  # 新增代码+CapabilityProfile：返回尺寸摘要；如果没有这行代码，调用方无法比较面积。
# 新增代码+CapabilityProfile：函数段结束，_capability_bounds 到此结束；如果没有这个边界说明，初学者不容易看出尺寸读取范围。


def _capability_collect_nodes(value: Any) -> list[dict[str, Any]]:  # 新增代码+CapabilityProfile：函数段开始，递归收集 UI 节点；如果没有这段函数，嵌套 UIA 树会被漏掉。
    if isinstance(value, Mapping):  # 新增代码+CapabilityProfile：处理单个映射节点；如果没有这行代码，字典观察帧无法遍历。
        children = []  # 新增代码+CapabilityProfile：初始化子节点列表；如果没有这行代码，递归结果无容器。
        for key in ("children", "items", "nodes", "uia_tree", "uia_elements", "elements", "visual_regions"):  # 新增代码+CapabilityProfile：遍历常见子节点字段；如果没有这行代码，不同观察源无法统一。
            children.extend(_capability_collect_nodes(value.get(key, [])))  # 新增代码+CapabilityProfile：递归收集子节点；如果没有这行代码，深层控件会漏掉。
        return [dict(value), *children]  # 新增代码+CapabilityProfile：返回当前节点加子节点；如果没有这行代码，根节点能力会丢失。
    if isinstance(value, list | tuple):  # 新增代码+CapabilityProfile：处理列表或元组；如果没有这行代码，观察数组无法展开。
        nodes: list[dict[str, Any]] = []  # 新增代码+CapabilityProfile：初始化节点列表；如果没有这行代码，循环无累加容器。
        for item in value:  # 新增代码+CapabilityProfile：逐个处理列表项；如果没有这行代码，只能处理第一个或无处理。
            nodes.extend(_capability_collect_nodes(item))  # 新增代码+CapabilityProfile：递归追加节点；如果没有这行代码，嵌套列表会漏掉。
        return nodes  # 新增代码+CapabilityProfile：返回收集结果；如果没有这行代码，调用方拿不到节点。
    return []  # 新增代码+CapabilityProfile：非结构值返回空；如果没有这行代码，递归可能隐式返回 None。
# 新增代码+CapabilityProfile：函数段结束，_capability_collect_nodes 到此结束；如果没有这个边界说明，初学者不容易看出递归范围。


def _capability_has_marker(text: str, markers: tuple[str, ...]) -> bool:  # 新增代码+CapabilityProfile：函数段开始，统一标记命中判断；如果没有这段函数，大小写和空值处理会重复。
    return any(marker in text for marker in markers)  # 新增代码+CapabilityProfile：任一标记命中即返回真；如果没有这行代码，调用方无法简洁表达能力判断。
# 新增代码+CapabilityProfile：函数段结束，_capability_has_marker 到此结束；如果没有这个边界说明，初学者不容易看出标记判断范围。


def build_capability_profile(observation_frame: Mapping[str, Any] | None) -> AppCapabilityProfile:  # 新增代码+CapabilityProfile：函数段开始，从观察帧生成通用能力画像；如果没有这段函数，上层 planner 仍会靠应用名猜。
    frame = observation_frame if isinstance(observation_frame, Mapping) else {}  # 新增代码+CapabilityProfile：规范化观察帧；如果没有这行代码，None 输入会崩溃。
    nodes = _capability_collect_nodes(frame)  # 新增代码+CapabilityProfile：收集所有 UI/视觉节点；如果没有这行代码，能力判断没有输入。
    evidence: list[str] = []  # 新增代码+CapabilityProfile：初始化短证据列表；如果没有这行代码，用户无法理解画像来源。
    text_input = False  # 新增代码+CapabilityProfile：初始化文本能力；如果没有这行代码，后续判断无默认值。
    canvas_like = False  # 新增代码+CapabilityProfile：初始化画布能力；如果没有这行代码，绘图判断无默认值。
    menu_bar = False  # 新增代码+CapabilityProfile：初始化菜单能力；如果没有这行代码，保存策略无默认值。
    toolbar = False  # 新增代码+CapabilityProfile：初始化工具栏能力；如果没有这行代码，工具选择策略无默认值。
    file_save = False  # 新增代码+CapabilityProfile：初始化保存表面能力；如果没有这行代码，提交资源判断无默认值。
    modal = False  # 新增代码+CapabilityProfile：初始化弹窗能力；如果没有这行代码，阻塞对话框判断无默认值。
    grid_or_table = False  # 新增代码+CapabilityProfile：初始化表格能力；如果没有这行代码，表格任务判断无默认值。
    nav_text = False  # 新增代码+CapabilityProfile：初始化导航输入信号；如果没有这行代码，导航组合判断无输入。
    nav_button = False  # 新增代码+CapabilityProfile：初始化导航按钮信号；如果没有这行代码，导航组合判断无输入。
    for node in nodes:  # 新增代码+CapabilityProfile：遍历所有节点；如果没有这行代码，能力不会被计算。
        blob = _capability_lower_blob(node)  # 新增代码+CapabilityProfile：读取节点语义文本；如果没有这行代码，后续标记无法判断。
        bounds = _capability_bounds(node)  # 新增代码+CapabilityProfile：读取节点尺寸；如果没有这行代码，画布面积无法判断。
        text_input = bool(text_input or _capability_has_marker(blob, TEXT_CONTROL_MARKERS))  # 新增代码+CapabilityProfile：检测文本输入能力；如果没有这行代码，文本阶段无法泛化。
        menu_bar = bool(menu_bar or _capability_has_marker(blob, MENU_MARKERS))  # 新增代码+CapabilityProfile：检测菜单栏能力；如果没有这行代码，菜单保存策略缺依据。
        toolbar = bool(toolbar or _capability_has_marker(blob, TOOLBAR_MARKERS))  # 新增代码+CapabilityProfile：检测工具栏能力；如果没有这行代码，绘图工具选择缺依据。
        file_save = bool(file_save or _capability_has_marker(blob, SAVE_MARKERS))  # 新增代码+CapabilityProfile：检测保存表面能力；如果没有这行代码，保存阶段只能猜。
        modal = bool(modal or _capability_has_marker(blob, MODAL_MARKERS) and "button" in blob)  # 新增代码+CapabilityProfile：检测弹窗线索；如果没有这行代码，确认框可能被忽略。
        grid_or_table = bool(grid_or_table or "grid" in blob or "table" in blob or "dataitem" in blob)  # 新增代码+CapabilityProfile：检测表格线索；如果没有这行代码，表格类窗口无法泛化。
        nav_text = bool(nav_text or (_capability_has_marker(blob, NAV_TEXT_MARKERS) and _capability_has_marker(blob, TEXT_CONTROL_MARKERS)))  # 新增代码+CapabilityProfile：检测导航输入；如果没有这行代码，地址/搜索框无法识别。
        nav_button = bool(nav_button or ("button" in blob and _capability_has_marker(blob, NAV_BUTTON_MARKERS)))  # 新增代码+CapabilityProfile：检测导航按钮；如果没有这行代码，导航表面组合不成立。
        canvas_like = bool(canvas_like or (_capability_has_marker(blob, CANVAS_ROLE_MARKERS) and bounds["area"] >= 120000) or (bounds["area"] >= 300000 and float(node.get("blank_ratio", 0) or 0) >= 0.75))  # 新增代码+CapabilityProfile：检测大画布区域；如果没有这行代码，绘图软件和白板无法泛化。
    if text_input:  # 新增代码+CapabilityProfile：检查是否识别文本能力；如果没有这行代码，证据不会记录文本来源。
        evidence.append("text_input:uiae_or_role")  # 新增代码+CapabilityProfile：记录文本证据；如果没有这行代码，失败复盘看不到原因。
    if canvas_like:  # 新增代码+CapabilityProfile：检查是否识别画布能力；如果没有这行代码，证据不会记录画布来源。
        evidence.append("canvas:large_region")  # 新增代码+CapabilityProfile：记录画布证据；如果没有这行代码，绘图能力不可解释。
    if nav_text and nav_button:  # 新增代码+CapabilityProfile：检查导航输入和按钮是否同时存在；如果没有这行代码，单个搜索词可能误判导航表面。
        evidence.append("navigation:input_and_buttons")  # 新增代码+CapabilityProfile：记录导航证据；如果没有这行代码，导航任务无法解释。
    if file_save:  # 新增代码+CapabilityProfile：检查保存表面；如果没有这行代码，保存证据不会出现。
        evidence.append("save:surface_or_command")  # 新增代码+CapabilityProfile：记录保存证据；如果没有这行代码，提交资源阶段不可解释。
    shortcut_likely = bool(text_input or canvas_like or menu_bar or toolbar or nav_text)  # 新增代码+CapabilityProfile：估计快捷键支持；如果没有这行代码，批编译无法选择 Ctrl+S 等保守策略。
    unknown = not any([text_input, canvas_like, menu_bar, toolbar, file_save, modal, grid_or_table, nav_text and nav_button])  # 新增代码+CapabilityProfile：能力全无时标记未知；如果没有这行代码，未知软件可能被误操作。
    return AppCapabilityProfile(has_text_input=text_input, has_canvas_like_region=canvas_like, has_menu_bar=menu_bar, has_toolbar=toolbar, has_file_save_surface=file_save, has_browser_navigation_surface=bool(nav_text and nav_button), has_grid_or_table=grid_or_table, has_modal_dialog=modal, supports_keyboard_shortcuts_likely=shortcut_likely, single_instance_suspected=bool(frame.get("single_instance_suspected", False)), unknown_capabilities=unknown, evidence=tuple(evidence))  # 新增代码+CapabilityProfile：返回通用能力画像；如果没有这行代码，上层无法获得画像。
# 新增代码+CapabilityProfile：函数段结束，build_capability_profile 到此结束；如果没有这个边界说明，初学者不容易看出画像生成范围。


__all__ = ["AppCapabilityProfile", "build_capability_profile"]  # 新增代码+CapabilityProfile：声明公开接口；如果没有这行代码，通配导入会暴露内部 helper。
