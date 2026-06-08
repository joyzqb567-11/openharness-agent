"""Windows Computer Use Phase66 observation fusion runtime."""  # 新增代码+Phase66ObservationFusion: 标明本文件负责 Phase66 多来源观察融合；如果没有这行代码，读者不知道统一观察对象入口在哪里。
from __future__ import annotations  # 新增代码+Phase66ObservationFusion: 启用延迟类型解析；如果没有这行代码，未来前向类型标注更容易在旧入口导入失败。

import json  # 新增代码+Phase66ObservationFusion: 导入 JSON 用于 CLI 输出结构化报告和合同泄露检查；如果没有这行代码，真实终端失败时不容易复盘。
from typing import Any  # 新增代码+Phase66ObservationFusion: 导入 Any 描述 JSON 风格观察对象；如果没有这行代码，接口边界不清楚。

try:  # 新增代码+Phase66ObservationFusion: 优先按 learning_agent 包路径复用既有脱敏函数；如果没有这段代码，unittest 和生产入口不能共享 evidence 过滤逻辑。
    from learning_agent.computer_use.evidence import filter_accessibility_text  # 新增代码+Phase66ObservationFusion: 导入 UIA 文本过滤函数；如果没有这行代码，融合层可能把 password/token 类控件文本泄露出去。
except ModuleNotFoundError as error:  # 新增代码+Phase66ObservationFusion: 兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这段代码，真实可见终端可能因包名前缀失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.evidence"}:  # 新增代码+Phase66ObservationFusion: 只允许包路径缺失时 fallback；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase66ObservationFusion: 重新抛出非路径类导入错误；如果没有这行代码，排查 evidence 内部问题会困难。
    from computer_use.evidence import filter_accessibility_text  # 新增代码+Phase66ObservationFusion: 脚本模式导入 UIA 文本过滤函数；如果没有这行代码，bat 入口无法安全脱敏。

PHASE66_OBSERVATION_FUSION_MARKER = "PHASE66_OBSERVATION_FUSION_READY"  # 新增代码+Phase66ObservationFusion: 定义 Phase66 ready marker；如果没有这行代码，真实终端验收没有稳定锚点。
PHASE66_OBSERVATION_FUSION_OK_TOKEN = "PHASE66_OBSERVATION_FUSION_OK"  # 新增代码+Phase66ObservationFusion: 定义 Phase66 OK token；如果没有这行代码，debug log 无法区分合同通过和普通输出。
PHASE66_OBSERVATION_FUSION_MODEL = "phase66_windows_observation_fusion"  # 新增代码+Phase66ObservationFusion: 定义融合观察协议模型名；如果没有这行代码，后续规划器无法识别观察对象版本。
PHASE66_ACTIONS_EXPANDED = False  # 新增代码+Phase66ObservationFusion: 明确 Phase66 只读融合观察不扩大桌面动作；如果没有这行代码，安全审计无法确认本阶段没有新增真实输入能力。
FusedComputerObservation = dict[str, Any]  # 新增代码+Phase66ObservationFusion: 定义融合观察字典合同别名；如果没有这行代码，调用方不容易看出 observe 返回的是稳定结构。


# 新增代码+Phase66ObservationFusion: 函数段开始，_phase66_bool_token 把布尔值转成小写验收 token；如果没有这段函数，CLI 输出会混用 True/False 和 true/false，作者意图是让真实终端断言稳定。
def _phase66_bool_token(value: Any) -> str:  # 新增代码+Phase66ObservationFusion: 定义布尔 token helper；如果没有这行代码，多处输出会重复写转换逻辑。
    return "true" if bool(value) else "false"  # 新增代码+Phase66ObservationFusion: 返回小写布尔文本；如果没有这行代码，场景 JSON 的 token 匹配可能失败。
# 新增代码+Phase66ObservationFusion: 函数段结束，_phase66_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


# 新增代码+Phase66ObservationFusion: 函数段开始，_phase66_safe_int 把动态字段安全转成整数；如果没有这段函数，坏截图尺寸或 UIA 坐标会让融合流程崩溃，作者意图是让观察层对 provider 输出温和兜底。
def _phase66_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase66ObservationFusion: 定义安全整数转换函数；如果没有这行代码，width/height/node_count 转换逻辑会散落。
    try:  # 新增代码+Phase66ObservationFusion: 捕获不能转整数的动态值；如果没有这行代码，None 或异常字符串会抛出异常。
        return int(value)  # 新增代码+Phase66ObservationFusion: 返回整数值；如果没有这行代码，调用方拿不到统一数字。
    except Exception:  # 新增代码+Phase66ObservationFusion: 捕获所有转换异常作为兜底；如果没有这行代码，坏 provider 输出会中断 agent。
        return int(default)  # 新增代码+Phase66ObservationFusion: 返回默认整数；如果没有这行代码，失败分支没有稳定值。
# 新增代码+Phase66ObservationFusion: 函数段结束，_phase66_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出整数清洗范围。


# 新增代码+Phase66ObservationFusion: 函数段开始，_phase66_safe_text 脱敏并截断模型可见文本；如果没有这段函数，UIA/OCR 字段可能泄露密码或 token，作者意图是让融合对象只保留安全摘要。
def _phase66_safe_text(value: Any, max_length: int = 160) -> tuple[str, int]:  # 新增代码+Phase66ObservationFusion: 定义安全文本 helper；如果没有这行代码，name/automation_id/class_name/OCR 摘要会各自实现过滤。
    raw_text = str(value or "")  # 新增代码+Phase66ObservationFusion: 把输入统一转成字符串；如果没有这行代码，None 或数字文本会让过滤函数行为不稳定。
    filtered = filter_accessibility_text(raw_text, max_length=max_length)  # 新增代码+Phase66ObservationFusion: 调用既有敏感词过滤；如果没有这行代码，password/token 等敏感行可能进入输出。
    if raw_text and not filtered.excerpt and filtered.filtered_line_count > 0:  # 新增代码+Phase66ObservationFusion: 识别整段被过滤的情况；如果没有这行代码，敏感节点会变成空白难以审计。
        return "[filtered]", int(filtered.filtered_line_count)  # 新增代码+Phase66ObservationFusion: 返回占位文本和过滤计数；如果没有这行代码，调用方不知道发生了敏感过滤。
    return filtered.excerpt, int(filtered.filtered_line_count)  # 新增代码+Phase66ObservationFusion: 返回安全摘要和过滤计数；如果没有这行代码，调用方拿不到脱敏结果。
# 新增代码+Phase66ObservationFusion: 函数段结束，_phase66_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出脱敏范围。


# 新增代码+Phase66ObservationFusion: 函数段开始，_phase66_safe_dict 复制动态 dict 输入；如果没有这段函数，坏类型或外部可变对象会污染融合流程，作者意图是让 provider 输出先变成安全副本。
def _phase66_safe_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase66ObservationFusion: 定义安全字典转换函数；如果没有这行代码，每个输入都要重复 isinstance 判断。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+Phase66ObservationFusion: 只接受 dict 并复制；如果没有这行代码，列表/字符串输入会触发字段访问错误。
# 新增代码+Phase66ObservationFusion: 函数段结束，_phase66_safe_dict 到此结束；如果没有这个边界说明，初学者不容易看出动态输入清洗范围。


# 新增代码+Phase66ObservationFusion: 函数段开始，_phase66_normalize_bounds 统一控件边界框格式；如果没有这段函数，UIA provider 的 left/top/width/right 混用会影响后续点击规划，作者意图是给 Phase67+ 一个稳定坐标摘要。
def _phase66_normalize_bounds(bounds: Any) -> dict[str, int]:  # 新增代码+Phase66ObservationFusion: 定义 bounds 标准化函数；如果没有这行代码，融合结果里的坐标字段不稳定。
    source = _phase66_safe_dict(bounds)  # 新增代码+Phase66ObservationFusion: 清洗 bounds 输入；如果没有这行代码，坏 bounds 类型会让坐标读取崩溃。
    left = _phase66_safe_int(source.get("left"))  # 新增代码+Phase66ObservationFusion: 读取左边界；如果没有这行代码，控件 x 起点缺失。
    top = _phase66_safe_int(source.get("top"))  # 新增代码+Phase66ObservationFusion: 读取上边界；如果没有这行代码，控件 y 起点缺失。
    width = max(0, _phase66_safe_int(source.get("width"), _phase66_safe_int(source.get("right")) - left))  # 新增代码+Phase66ObservationFusion: 读取或计算宽度并防止负数；如果没有这行代码，后续布局推理无法知道控件大小。
    height = max(0, _phase66_safe_int(source.get("height"), _phase66_safe_int(source.get("bottom")) - top))  # 新增代码+Phase66ObservationFusion: 读取或计算高度并防止负数；如果没有这行代码，后续布局推理无法知道控件大小。
    right = _phase66_safe_int(source.get("right"), left + width)  # 新增代码+Phase66ObservationFusion: 读取或计算右边界；如果没有这行代码，bounds 不完整。
    bottom = _phase66_safe_int(source.get("bottom"), top + height)  # 新增代码+Phase66ObservationFusion: 读取或计算下边界；如果没有这行代码，bounds 不完整。
    return {"left": left, "top": top, "right": max(right, left + width), "bottom": max(bottom, top + height), "width": width, "height": height}  # 新增代码+Phase66ObservationFusion: 返回标准边界对象；如果没有这行代码，调用方需要兼容多种坐标形态。
# 新增代码+Phase66ObservationFusion: 函数段结束，_phase66_normalize_bounds 到此结束；如果没有这个边界说明，初学者不容易看出边界框标准化范围。


# 新增代码+Phase66ObservationFusion: 函数段开始，_phase66_sanitize_uia_nodes 把 UIA 扁平节点清洗成安全摘要；如果没有这段函数，控件名称和 automation_id 可能泄露敏感信息，作者意图是融合层只输出可定位但低泄露的节点。
def _phase66_sanitize_uia_nodes(nodes: Any) -> tuple[list[dict[str, Any]], int]:  # 新增代码+Phase66ObservationFusion: 定义 UIA 节点清洗函数；如果没有这行代码，runtime.observe 会堆满重复脱敏代码。
    safe_nodes: list[dict[str, Any]] = []  # 新增代码+Phase66ObservationFusion: 准备保存安全节点列表；如果没有这行代码，函数没有输出容器。
    filtered_count = 0  # 新增代码+Phase66ObservationFusion: 初始化敏感过滤计数；如果没有这行代码，用户无法审计过滤发生次数。
    for node in list(nodes or []):  # 新增代码+Phase66ObservationFusion: 遍历动态节点列表；如果没有这行代码，UIA 节点不会进入融合对象。
        source = _phase66_safe_dict(node)  # 新增代码+Phase66ObservationFusion: 清洗单个节点；如果没有这行代码，坏节点会触发字段访问错误。
        name, name_filtered = _phase66_safe_text(source.get("name"), max_length=160)  # 新增代码+Phase66ObservationFusion: 脱敏控件名称；如果没有这行代码，窗口标题或密码字段可能泄露。
        automation_id, automation_filtered = _phase66_safe_text(source.get("automation_id"), max_length=120)  # 新增代码+Phase66ObservationFusion: 脱敏 automation_id；如果没有这行代码，敏感自动化标识可能进入模型上下文。
        class_name, class_filtered = _phase66_safe_text(source.get("class_name"), max_length=120)  # 新增代码+Phase66ObservationFusion: 脱敏类名；如果没有这行代码，异常类名或敏感文本可能污染输出。
        filtered_count += name_filtered + automation_filtered + class_filtered  # 新增代码+Phase66ObservationFusion: 累加过滤次数；如果没有这行代码，融合报告不知道隐藏了多少敏感字段。
        safe_nodes.append({"node_id": str(source.get("node_id", "")), "name": name, "role": str(source.get("role", "Unknown") or "Unknown"), "automation_id": automation_id, "class_name": class_name, "bounds": _phase66_normalize_bounds(source.get("bounds")), "enabled": bool(source.get("enabled", True)), "clickable": bool(source.get("clickable", False)), "editable": bool(source.get("editable", False))})  # 新增代码+Phase66ObservationFusion: 保存安全控件摘要；如果没有这行代码，后续规划器拿不到可定位控件候选。
    return safe_nodes, filtered_count  # 新增代码+Phase66ObservationFusion: 返回安全节点和过滤计数；如果没有这行代码，调用方拿不到清洗结果。
# 新增代码+Phase66ObservationFusion: 函数段结束，_phase66_sanitize_uia_nodes 到此结束；如果没有这个边界说明，初学者不容易看出 UIA 节点脱敏范围。


# 新增代码+Phase66ObservationFusion: 类段开始，WindowsObservationFusionRuntime 组合截图、UIA、OCR/vision 插槽和窗口状态；如果没有这个类，Phase67+ 需要直接读多个 provider 输出，作者意图是给拟人操作闭环一个统一观察对象。
class WindowsObservationFusionRuntime:  # 新增代码+Phase66ObservationFusion: 定义观察融合 runtime；如果没有这行代码，测试和生产无法注入多来源观察结果。
    def __init__(self, model: str = PHASE66_OBSERVATION_FUSION_MODEL) -> None:  # 新增代码+Phase66ObservationFusion: 函数段开始，初始化融合协议模型名；如果没有这段函数，runtime 状态无法说明协议版本。
        self.model = str(model or PHASE66_OBSERVATION_FUSION_MODEL)  # 新增代码+Phase66ObservationFusion: 保存模型名并兜底默认值；如果没有这行代码，输出缺少版本锚点。
    # 新增代码+Phase66ObservationFusion: 函数段结束，WindowsObservationFusionRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def observe(self, window: dict[str, Any], screenshot_result: dict[str, Any], uia_result: dict[str, Any], inventory_result: Any, ocr_result: dict[str, Any] | None = None) -> FusedComputerObservation:  # 新增代码+Phase66ObservationFusion: 函数段开始，融合一次只读窗口观察；如果没有这段函数，闭环执行器无法获得单一事实源。
        safe_window = _phase66_safe_dict(window)  # 新增代码+Phase66ObservationFusion: 复制目标窗口引用；如果没有这行代码，融合过程可能污染外部 window 对象。
        screenshot = self._screenshot_summary(screenshot_result)  # 新增代码+Phase66ObservationFusion: 生成截图摘要；如果没有这行代码，视觉证据无法进入融合对象。
        uia = self._uia_summary(uia_result)  # 新增代码+Phase66ObservationFusion: 生成 UIA 摘要；如果没有这行代码，控件树事实无法进入融合对象。
        ocr = self._ocr_summary(ocr_result)  # 新增代码+Phase66ObservationFusion: 生成 OCR/vision 预留槽摘要；如果没有这行代码，后续视觉依赖接入会破坏协议。
        window_state = self._window_state_summary(safe_window, inventory_result)  # 新增代码+Phase66ObservationFusion: 生成窗口状态摘要；如果没有这行代码，目标身份和焦点状态无法进入融合对象。
        screenshot_observation = bool(screenshot.get("available"))  # 新增代码+Phase66ObservationFusion: 汇总截图观察是否可用；如果没有这行代码，CLI token 没有稳定来源。
        uia_tree_observation = bool(uia.get("available"))  # 新增代码+Phase66ObservationFusion: 汇总 UIA 观察是否可用；如果没有这行代码，规划器无法知道控件树是否存在。
        ocr_or_vision_slot = bool(ocr.get("slot_available"))  # 新增代码+Phase66ObservationFusion: 汇总 OCR/vision 插槽是否存在；如果没有这行代码，后续依赖接入状态不可见。
        window_state_observation = bool(window_state.get("available"))  # 新增代码+Phase66ObservationFusion: 汇总窗口状态是否可用；如果没有这行代码，动作前目标确认会缺少事实。
        raw_text_included = bool(uia.get("raw_text_included") or ocr.get("raw_text_included"))  # 新增代码+Phase66ObservationFusion: 检查是否有原始文本泄露；如果没有这行代码，敏感边界无法汇总。
        sensitive_text_boundary = bool(not raw_text_included and not screenshot.get("raw_bytes_included") and not ocr.get("install_attempted"))  # 新增代码+Phase66ObservationFusion: 汇总敏感文本和环境变更边界；如果没有这行代码，验收无法证明没有原文和无安装。
        uia_ocr_vision_fusion = bool(screenshot_observation and uia_tree_observation and ocr_or_vision_slot and window_state_observation)  # 新增代码+Phase66ObservationFusion: 汇总多来源融合是否成立；如果没有这行代码，Phase67 不知道观察层是否完整。
        return {"marker": PHASE66_OBSERVATION_FUSION_MARKER, "model": self.model, "window": dict(safe_window), "screenshot": screenshot, "uia": uia, "ocr": ocr, "window_state": window_state, "screenshot_observation": screenshot_observation, "uia_tree_observation": uia_tree_observation, "ocr_or_vision_slot": ocr_or_vision_slot, "window_state_observation": window_state_observation, "sensitive_text_boundary": sensitive_text_boundary, "uia_ocr_vision_fusion": uia_ocr_vision_fusion, "raw_text_included": raw_text_included, "actions_expanded": PHASE66_ACTIONS_EXPANDED}  # 新增代码+Phase66ObservationFusion: 返回完整融合观察对象；如果没有这行代码，调用方拿不到统一事实源。
    # 新增代码+Phase66ObservationFusion: 函数段结束，WindowsObservationFusionRuntime.observe 到此结束；如果没有这个边界说明，初学者不容易看出融合入口范围。

    def _screenshot_summary(self, screenshot_result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase66ObservationFusion: 函数段开始，压缩截图结果为安全摘要；如果没有这段函数，融合对象可能夹带原始截图 bytes。
        source = _phase66_safe_dict(screenshot_result)  # 新增代码+Phase66ObservationFusion: 清洗截图输入；如果没有这行代码，坏 provider 输出会触发异常。
        image_results = [dict(item) for item in list(source.get("image_results", []) or []) if isinstance(item, dict)]  # 新增代码+Phase66ObservationFusion: 复制图片块列表；如果没有这行代码，image_result 可能被外部修改或坏项污染。
        available = bool(source.get("screenshot_observation") or source.get("screenshot_captured") or source.get("captured") or source.get("artifact_openable") or source.get("pixel_guard_passed"))  # 新增代码+Phase66ObservationFusion: 判断截图观察是否可用；如果没有这行代码，多种 provider 成功字段无法统一。
        return {"available": available, "captured": bool(source.get("screenshot_captured", source.get("captured", available))), "artifact_path": str(source.get("screenshot_path", source.get("artifact_path", "")) or ""), "width": _phase66_safe_int(source.get("screenshot_width", source.get("width"))), "height": _phase66_safe_int(source.get("screenshot_height", source.get("height"))), "format": str(source.get("screenshot_format", source.get("format", "")) or ""), "pixel_guard_passed": bool(source.get("pixel_guard_passed", source.get("pixel_guard", {}).get("passed") if isinstance(source.get("pixel_guard"), dict) else False)), "artifact_openable": bool(source.get("artifact_openable", False)), "image_result_count": len(image_results), "image_results": image_results, "raw_bytes_included": bool(source.get("screenshot_bytes_included", source.get("raw_bytes_included", False)))}  # 新增代码+Phase66ObservationFusion: 返回截图安全摘要；如果没有这行代码，后续观察对象没有稳定图片字段。
    # 新增代码+Phase66ObservationFusion: 函数段结束，WindowsObservationFusionRuntime._screenshot_summary 到此结束；如果没有这个边界说明，初学者不容易看出截图摘要范围。

    def _uia_summary(self, uia_result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase66ObservationFusion: 函数段开始，压缩 UIA 结果为脱敏控件摘要；如果没有这段函数，融合对象可能泄露原始 UIA 文本。
        source = _phase66_safe_dict(uia_result)  # 新增代码+Phase66ObservationFusion: 清洗 UIA 输入；如果没有这行代码，坏 provider 输出会触发异常。
        safe_nodes, filtered_from_nodes = _phase66_sanitize_uia_nodes(source.get("flat_nodes", []))  # 新增代码+Phase66ObservationFusion: 脱敏扁平节点；如果没有这行代码，password/token 类控件名可能泄露。
        node_count = max(_phase66_safe_int(source.get("node_count")), len(safe_nodes))  # 新增代码+Phase66ObservationFusion: 计算节点数量；如果没有这行代码，provider 漏填 node_count 时会显示 0。
        available = bool(source.get("uia_tree_observation") or source.get("captured") or source.get("real_uia_tree") or node_count > 0)  # 新增代码+Phase66ObservationFusion: 判断 UIA 观察是否可用；如果没有这行代码，成功字段不统一。
        sensitive_text_filtered = _phase66_safe_int(source.get("sensitive_text_filtered")) + filtered_from_nodes  # 新增代码+Phase66ObservationFusion: 汇总 provider 和本层过滤计数；如果没有这行代码，脱敏行为不可审计。
        return {"available": available, "captured": bool(source.get("captured", available)), "real_uia_tree": bool(source.get("real_uia_tree", available)), "node_count": node_count, "flat_nodes": safe_nodes, "clickable_count": _phase66_safe_int(source.get("clickable_count"), sum(1 for node in safe_nodes if node.get("clickable"))), "editable_count": _phase66_safe_int(source.get("editable_count"), sum(1 for node in safe_nodes if node.get("editable"))), "bounds_available": bool(source.get("bounds_available") or any(node.get("bounds", {}).get("width") or node.get("bounds", {}).get("height") for node in safe_nodes)), "sensitive_text_filtered": sensitive_text_filtered, "semantic_locator_available": bool(source.get("semantic_locator_available", True)), "raw_text_included": bool(source.get("raw_text_included", False)), "backend": str(source.get("backend", ""))}  # 新增代码+Phase66ObservationFusion: 返回 UIA 安全摘要；如果没有这行代码，后续 planner 拿不到控件候选。
    # 新增代码+Phase66ObservationFusion: 函数段结束，WindowsObservationFusionRuntime._uia_summary 到此结束；如果没有这个边界说明，初学者不容易看出 UIA 摘要范围。

    def _ocr_summary(self, ocr_result: dict[str, Any] | None) -> dict[str, Any]:  # 新增代码+Phase66ObservationFusion: 函数段开始，生成 OCR/vision 预留槽摘要；如果没有这段函数，未来 OCR/vision provider 接入会破坏观察协议。
        source = _phase66_safe_dict(ocr_result)  # 新增代码+Phase66ObservationFusion: 清洗可选 OCR 输入；如果没有这行代码，None 或坏类型会触发异常。
        text_summary, filtered_count = _phase66_safe_text(source.get("text_summary", source.get("text", "")), max_length=240)  # 新增代码+Phase66ObservationFusion: 脱敏 OCR 文本摘要；如果没有这行代码，视觉文字识别可能泄露敏感内容。
        provider_available = bool(source.get("provider_available", source.get("available", False)))  # 新增代码+Phase66ObservationFusion: 读取 provider 可用性；如果没有这行代码，默认槽和真实 provider 无法区分。
        install_attempted = bool(source.get("install_attempted", False))  # 新增代码+Phase66ObservationFusion: 读取是否尝试安装依赖；如果没有这行代码，验收无法证明没有改变本机环境。
        return {"slot_available": True, "provider_available": provider_available, "provider": str(source.get("provider") or ("configured" if provider_available else "not_configured")), "install_attempted": install_attempted, "result_count": _phase66_safe_int(source.get("result_count"), 1 if text_summary else 0), "text_summary": text_summary, "sensitive_text_filtered": filtered_count + _phase66_safe_int(source.get("sensitive_text_filtered")), "raw_text_included": False, "reason": str(source.get("reason") or "OCR/vision slot is reserved; no dependency install attempted by Phase66.")}  # 新增代码+Phase66ObservationFusion: 返回 OCR/vision 插槽摘要；如果没有这行代码，后续视觉依赖状态没有稳定字段。
    # 新增代码+Phase66ObservationFusion: 函数段结束，WindowsObservationFusionRuntime._ocr_summary 到此结束；如果没有这个边界说明，初学者不容易看出 OCR 插槽范围。

    def _window_state_summary(self, window: dict[str, Any], inventory_result: Any) -> dict[str, Any]:  # 新增代码+Phase66ObservationFusion: 函数段开始，生成目标窗口状态摘要；如果没有这段函数，融合对象无法绑定 app_id/window_id/focus 事实。
        inventory = _phase66_safe_dict(inventory_result)  # 新增代码+Phase66ObservationFusion: 优先按 dict 读取 inventory；如果没有这行代码，字典场景无法处理。
        if not inventory and hasattr(inventory_result, "windows"):  # 新增代码+Phase66ObservationFusion: 兼容 WindowsWindowInventorySnapshot 对象；如果没有这行代码，真实 inventory 快照无法直接融合。
            inventory = {"windows": list(getattr(inventory_result, "windows", []) or []), "filtered_count": getattr(inventory_result, "filtered_count", 0), "captured_at": getattr(inventory_result, "captured_at", ""), "source": getattr(inventory_result, "source", ""), "active_window": getattr(inventory_result, "active_window", None)}  # 新增代码+Phase66ObservationFusion: 把快照对象转换成 dict；如果没有这行代码，窗口状态字段会丢失。
        windows = [dict(item) for item in list(inventory.get("windows", []) or []) if isinstance(item, dict)]  # 新增代码+Phase66ObservationFusion: 复制窗口列表；如果没有这行代码，坏窗口项可能污染融合对象。
        active_window = _phase66_safe_dict(inventory.get("active_window")) or dict(window)  # 新增代码+Phase66ObservationFusion: 选择活动窗口或目标窗口兜底；如果没有这行代码，窗口状态可能为空。
        return {"available": bool(active_window or window), "active_window_present": bool(active_window), "window_count": len(windows), "filtered_count": _phase66_safe_int(inventory.get("filtered_count")), "captured_at": str(inventory.get("captured_at", "")), "source": str(inventory.get("source", "")), "app_id": str((active_window or window).get("app_id", "")), "window_id": str((active_window or window).get("window_id", "")), "title_preview": str((active_window or window).get("title_preview", (active_window or window).get("title", "")) or ""), "rect": _phase66_safe_dict((active_window or window).get("rect"))}  # 新增代码+Phase66ObservationFusion: 返回窗口状态摘要；如果没有这行代码，后续动作前目标确认缺少身份字段。
    # 新增代码+Phase66ObservationFusion: 函数段结束，WindowsObservationFusionRuntime._window_state_summary 到此结束；如果没有这个边界说明，初学者不容易看出窗口状态摘要范围。
# 新增代码+Phase66ObservationFusion: 类段结束，WindowsObservationFusionRuntime 到此结束；如果没有这个边界说明，初学者不容易看出观察融合 runtime 范围。


# 新增代码+Phase66ObservationFusion: 函数段开始，_phase66_contract_inputs 构造无副作用合同观察输入；如果没有这段函数，合同自检可能触碰真实桌面，作者意图是用 fake 数据证明融合协议和脱敏边界。
def _phase66_contract_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:  # 新增代码+Phase66ObservationFusion: 定义合同输入构造函数；如果没有这行代码，run 函数会堆满测试数据。
    window = {"app_id": "notepad.exe", "window_id": "hwnd:6601", "title_preview": "LearningAgent-Phase66-Contract", "rect": {"left": 10, "top": 20, "right": 710, "bottom": 520}}  # 新增代码+Phase66ObservationFusion: 构造安全 fake 窗口；如果没有这行代码，窗口状态融合没有目标。
    screenshot = {"screenshot_captured": True, "screenshot_path": "memory/computer_use/phase66/contract.bmp", "screenshot_width": 700, "screenshot_height": 500, "screenshot_format": "bmp", "pixel_guard_passed": True, "artifact_openable": True, "screenshot_bytes_included": False, "image_results": [{"type": "image_result", "artifact_path": "memory/computer_use/phase66/contract.bmp", "width": 700, "height": 500, "sensitive_text_included": False}]}  # 新增代码+Phase66ObservationFusion: 构造 fake 截图摘要；如果没有这行代码，截图观察 token 没有输入。
    uia = {"captured": True, "real_uia_tree": True, "raw_text_included": False, "flat_nodes": [{"node_id": "0", "name": "Document", "role": "Edit", "automation_id": "editor", "class_name": "Edit", "bounds": {"left": 30, "top": 80, "right": 680, "bottom": 480, "width": 650, "height": 400}, "clickable": True, "editable": True}, {"node_id": "1", "name": "password: phase66-contract-secret", "role": "Edit", "automation_id": "secret", "class_name": "Edit", "bounds": {"left": 30, "top": 490, "right": 680, "bottom": 510, "width": 650, "height": 20}, "clickable": True, "editable": True}], "node_count": 2, "clickable_count": 2, "editable_count": 2, "bounds_available": True, "semantic_locator_available": True}  # 新增代码+Phase66ObservationFusion: 构造带敏感节点的 fake UIA 摘要；如果没有这行代码，脱敏合同没有输入。
    inventory = {"windows": [window], "filtered_count": 0, "captured_at": "2026-06-03T12:00:00Z", "source": "phase66_contract_static", "active_window": window}  # 新增代码+Phase66ObservationFusion: 构造 fake 窗口 inventory；如果没有这行代码，窗口状态观察 token 没有输入。
    return window, screenshot, uia, inventory  # 新增代码+Phase66ObservationFusion: 返回四类输入；如果没有这行代码，合同运行拿不到 fake 观察来源。
# 新增代码+Phase66ObservationFusion: 函数段结束，_phase66_contract_inputs 到此结束；如果没有这个边界说明，初学者不容易看出合同输入范围。


# 新增代码+Phase66ObservationFusion: 函数段开始，run_phase66_observation_fusion_contract 运行 Phase66 合同自检；如果没有这段函数，CLI、测试和真实终端没有统一事实源。
def run_phase66_observation_fusion_contract(real_smoke: bool = False) -> dict[str, Any]:  # 新增代码+Phase66ObservationFusion: 定义 Phase66 合同入口；如果没有这行代码，测试和场景无法调用同一逻辑。
    window, screenshot, uia, inventory = _phase66_contract_inputs()  # 新增代码+Phase66ObservationFusion: 获取无副作用 fake 输入；如果没有这行代码，合同自检可能触碰真实桌面。
    runtime = WindowsObservationFusionRuntime()  # 新增代码+Phase66ObservationFusion: 创建融合 runtime；如果没有这行代码，合同无法验证 observe 行为。
    fused = runtime.observe(window, screenshot, uia, inventory, ocr_result=None)  # 新增代码+Phase66ObservationFusion: 执行观察融合；如果没有这行代码，报告没有融合对象。
    serialized = json.dumps(fused, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase66ObservationFusion: 序列化融合对象检查敏感值；如果没有这行代码，嵌套泄露难以发现。
    raw_text_hidden = "phase66-contract-secret" not in serialized and "password: phase66" not in serialized.lower()  # 新增代码+Phase66ObservationFusion: 检查合同敏感原文没有泄露；如果没有这行代码，脱敏失败可能被误过。
    screenshot_observation = bool(fused.get("screenshot_observation"))  # 新增代码+Phase66ObservationFusion: 读取截图观察 token；如果没有这行代码，passed 判断会重复读取嵌套字段。
    uia_tree_observation = bool(fused.get("uia_tree_observation"))  # 新增代码+Phase66ObservationFusion: 读取 UIA 观察 token；如果没有这行代码，passed 判断会重复读取嵌套字段。
    ocr_or_vision_slot = bool(fused.get("ocr_or_vision_slot"))  # 新增代码+Phase66ObservationFusion: 读取 OCR/vision 插槽 token；如果没有这行代码，passed 判断会重复读取嵌套字段。
    window_state_observation = bool(fused.get("window_state_observation"))  # 新增代码+Phase66ObservationFusion: 读取窗口状态 token；如果没有这行代码，passed 判断会重复读取嵌套字段。
    sensitive_text_boundary = bool(fused.get("sensitive_text_boundary") and raw_text_hidden)  # 新增代码+Phase66ObservationFusion: 汇总敏感边界和泄露检查；如果没有这行代码，单看字段可能漏掉序列化泄露。
    uia_ocr_vision_fusion = bool(fused.get("uia_ocr_vision_fusion"))  # 新增代码+Phase66ObservationFusion: 读取融合完成 token；如果没有这行代码，CLI 和 passed 判断缺少统一字段。
    ocr_provider_available = bool(fused.get("ocr", {}).get("provider_available"))  # 新增代码+Phase66ObservationFusion: 读取 OCR provider 可用性；如果没有这行代码，报告无法说明依赖是否已存在。
    ocr_install_attempted = bool(fused.get("ocr", {}).get("install_attempted"))  # 新增代码+Phase66ObservationFusion: 读取 OCR 安装尝试状态；如果没有这行代码，验收无法证明没有自动安装。
    passed = bool(screenshot_observation and uia_tree_observation and ocr_or_vision_slot and window_state_observation and sensitive_text_boundary and uia_ocr_vision_fusion and not ocr_provider_available and not ocr_install_attempted and not PHASE66_ACTIONS_EXPANDED)  # 新增代码+Phase66ObservationFusion: 汇总合同通过条件；如果没有这行代码，main 无法用退出码表达成功或失败。
    return {"marker": PHASE66_OBSERVATION_FUSION_MARKER, "ok_token": PHASE66_OBSERVATION_FUSION_OK_TOKEN, "model": PHASE66_OBSERVATION_FUSION_MODEL, "screenshot_observation": screenshot_observation, "uia_tree_observation": uia_tree_observation, "ocr_or_vision_slot": ocr_or_vision_slot, "ocr_provider_available": ocr_provider_available, "ocr_install_attempted": ocr_install_attempted, "window_state_observation": window_state_observation, "sensitive_text_boundary": sensitive_text_boundary, "raw_text_hidden": raw_text_hidden, "uia_ocr_vision_fusion": uia_ocr_vision_fusion, "real_smoke": bool(real_smoke), "actions_expanded": PHASE66_ACTIONS_EXPANDED, "passed": passed, "fused_observation": fused}  # 新增代码+Phase66ObservationFusion: 返回完整合同报告；如果没有这行代码，CLI、测试和真实终端拿不到结构化结果。
# 新增代码+Phase66ObservationFusion: 函数段结束，run_phase66_observation_fusion_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同运行范围。


# 新增代码+Phase66ObservationFusion: 函数段开始，phase66_cli_line 把合同报告转成固定顺序 token 行；如果没有这段函数，真实终端场景需要解析复杂 JSON，作者意图是让最终回答可复制可验收。
def phase66_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase66ObservationFusion: 定义 Phase66 CLI 行格式化函数；如果没有这行代码，main 无法打印固定顺序 token。
    return f"{PHASE66_OBSERVATION_FUSION_MARKER} {PHASE66_OBSERVATION_FUSION_OK_TOKEN} screenshot_observation={_phase66_bool_token(report.get('screenshot_observation'))} uia_tree_observation={_phase66_bool_token(report.get('uia_tree_observation'))} ocr_or_vision_slot={_phase66_bool_token(report.get('ocr_or_vision_slot'))} window_state_observation={_phase66_bool_token(report.get('window_state_observation'))} sensitive_text_boundary={_phase66_bool_token(report.get('sensitive_text_boundary'))} uia_ocr_vision_fusion={_phase66_bool_token(report.get('uia_ocr_vision_fusion'))} actions_expanded={_phase66_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase66ObservationFusion: 返回固定顺序 token 行；如果没有这行代码，验收器无法稳定匹配 Phase66 合同。
# 新增代码+Phase66ObservationFusion: 函数段结束，phase66_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 文本范围。


# 新增代码+Phase66ObservationFusion: 函数段开始，main 提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase66 合同，作者意图是自动化和可见终端共用同一合同。
def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase66ObservationFusion: 定义命令行入口并保留 argv 扩展位；如果没有这行代码，python -c 只能手写调用细节。
    _ = argv  # 新增代码+Phase66ObservationFusion: 明确当前 Phase66 不解析命令行参数；如果没有这行代码，读者可能误以为 argv 被遗漏。
    report = run_phase66_observation_fusion_contract(real_smoke=False)  # 新增代码+Phase66ObservationFusion: 运行无副作用 Phase66 合同；如果没有这行代码，CLI 输出没有真实依据。
    print(phase66_cli_line(report))  # 新增代码+Phase66ObservationFusion: 打印稳定单行 token；如果没有这行代码，验收器无法快速匹配合同结果。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase66ObservationFusion: 打印结构化报告便于人工复盘；如果没有这行代码，失败时不容易定位哪一条观察边界失败。
    print(PHASE66_OBSERVATION_FUSION_MARKER)  # 新增代码+Phase66ObservationFusion: 单独打印 ready marker；如果没有这行代码，真实终端验收可能看不到明确阶段标记。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase66ObservationFusion: 根据合同结果返回退出码；如果没有这行代码，失败也可能被终端当成成功。
# 新增代码+Phase66ObservationFusion: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = ["FusedComputerObservation", "PHASE66_ACTIONS_EXPANDED", "PHASE66_OBSERVATION_FUSION_MARKER", "PHASE66_OBSERVATION_FUSION_MODEL", "PHASE66_OBSERVATION_FUSION_OK_TOKEN", "WindowsObservationFusionRuntime", "main", "phase66_cli_line", "run_phase66_observation_fusion_contract"]  # 新增代码+Phase66ObservationFusion: 限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase66ObservationFusion: 允许直接运行本模块；如果没有这行代码，初学者无法用 python 文件方式手动执行 Phase66 自检。
    raise SystemExit(main())  # 新增代码+Phase66ObservationFusion: 调用 main 并传递退出码；如果没有这行代码，直接运行文件不会执行验收。
