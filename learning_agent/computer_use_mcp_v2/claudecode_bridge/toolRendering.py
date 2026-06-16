"""Computer Use MCP v2 工具渲染桥接。"""  # 修改代码+ClaudeCodeToolRenderingParity：说明本文件对应 ClaudeCode toolRendering.tsx；如果没有这行代码，工具展示职责没有同构位置。
from __future__ import annotations  # 修改代码+ClaudeCodeToolRenderingParity：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

import json  # 修改代码+ClaudeCodeToolRenderingParity：导入 JSON 用于稳定渲染复杂字段；如果没有这行代码，对象字段无法安全展示。
from typing import Any  # 修改代码+ClaudeCodeToolRenderingParity：导入通用类型；如果没有这行代码，渲染函数参数边界不清楚。

CLAUDECODE_RENDER_FIELD_NAMES: tuple[str, ...] = ("coordinate", "start_coordinate", "region", "direction", "amount", "text", "duration", "bundle_id", "apps", "actions")  # 新增代码+ClaudeCodeToolRenderingParity：集中列出 ClaudeCode 可见字段名；如果没有这行代码，字段显示顺序会漂移并漏掉蓝图要求字段。

RESULT_SUMMARY: dict[str, str] = {  # 新增代码+ClaudeCodeToolRenderingParity：函数段开始，保存非 verbose 结果摘要；如果没有这组映射，工具完成提示只能显示整段 JSON。
    "screenshot": "Captured",  # 新增代码+ClaudeCodeToolRenderingParity：截图完成摘要；如果没有这一项，screenshot 结果无法对齐 ClaudeCode 简短提示。
    "zoom": "Captured",  # 新增代码+ClaudeCodeToolRenderingParity：局部放大完成摘要；如果没有这一项，zoom 结果无法对齐 ClaudeCode 简短提示。
    "request_access": "Access updated",  # 新增代码+ClaudeCodeToolRenderingParity：授权更新摘要；如果没有这一项，request_access 结果会缺少可读完成提示。
    "left_click": "Clicked",  # 新增代码+ClaudeCodeToolRenderingParity：左键点击摘要；如果没有这一项，点击工具结果不会有简短提示。
    "right_click": "Clicked",  # 新增代码+ClaudeCodeToolRenderingParity：右键点击摘要；如果没有这一项，右键工具结果不会有简短提示。
    "middle_click": "Clicked",  # 新增代码+ClaudeCodeToolRenderingParity：中键点击摘要；如果没有这一项，中键工具结果不会有简短提示。
    "double_click": "Clicked",  # 新增代码+ClaudeCodeToolRenderingParity：双击摘要；如果没有这一项，双击工具结果不会有简短提示。
    "triple_click": "Clicked",  # 新增代码+ClaudeCodeToolRenderingParity：三击摘要；如果没有这一项，三击工具结果不会有简短提示。
    "type": "Typed",  # 新增代码+ClaudeCodeToolRenderingParity：文本输入摘要；如果没有这一项，输入工具结果不会有简短提示。
    "key": "Pressed",  # 新增代码+ClaudeCodeToolRenderingParity：按键摘要；如果没有这一项，按键工具结果不会有简短提示。
    "hold_key": "Pressed",  # 新增代码+ClaudeCodeToolRenderingParity：长按按键摘要；如果没有这一项，hold_key 工具结果不会有简短提示。
    "scroll": "Scrolled",  # 新增代码+ClaudeCodeToolRenderingParity：滚动摘要；如果没有这一项，滚动工具结果不会有简短提示。
    "left_click_drag": "Dragged",  # 新增代码+ClaudeCodeToolRenderingParity：拖拽摘要；如果没有这一项，拖拽工具结果不会有简短提示。
    "open_application": "Opened",  # 新增代码+ClaudeCodeToolRenderingParity：打开应用摘要；如果没有这一项，启动工具结果不会有简短提示。
}  # 新增代码+ClaudeCodeToolRenderingParity：结果摘要映射结束；如果没有这行代码，Python 字典语法不完整。


def _compact_json(value: Any) -> str:  # 新增代码+ClaudeCodeToolRenderingParity：函数段开始，把复杂值转成短 JSON；如果没有这段函数，apps/actions/region 等字段会在显示时格式不稳定。
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))  # 新增代码+ClaudeCodeToolRenderingParity：返回无多余空格的 JSON；如果没有这行代码，渲染输出会更长且难以断言。
# 新增代码+ClaudeCodeToolRenderingParity：函数段结束，_compact_json 到此结束；如果没有这个边界说明，用户不容易看出复杂字段格式化范围。


def _truncate_text(text: str, max_chars: int = 40) -> str:  # 新增代码+ClaudeCodeToolRenderingParity：函数段开始，截断长文本字段；如果没有这段函数，type/write_clipboard 的摘要可能撑爆终端行。
    safe_text = str(text or "")  # 新增代码+ClaudeCodeToolRenderingParity：把输入稳定转成字符串；如果没有这行代码，None 或数字文本会导致长度判断不清楚。
    return safe_text if len(safe_text) <= max_chars else safe_text[: max_chars - 1] + "..."  # 新增代码+ClaudeCodeToolRenderingParity：超长时截断并保留省略号；如果没有这行代码，长文本会完整进入工具摘要。
# 新增代码+ClaudeCodeToolRenderingParity：函数段结束，_truncate_text 到此结束；如果没有这个边界说明，用户不容易看出截断规则范围。


def _format_coordinate(value: Any) -> str:  # 新增代码+ClaudeCodeToolRenderingParity：函数段开始，格式化 coordinate/start_coordinate；如果没有这段函数，坐标数组显示会和 ClaudeCode 不一致。
    if isinstance(value, (list, tuple)) and len(value) >= 2:  # 新增代码+ClaudeCodeToolRenderingParity：接受 [x,y] 或 (x,y)；如果没有这行代码，标准 ClaudeCode 坐标无法格式化。
        return f"({value[0]}, {value[1]})"  # 新增代码+ClaudeCodeToolRenderingParity：返回 ClaudeCode 风格坐标文本；如果没有这行代码，坐标会退回 JSON。
    return _compact_json(value) if value is not None else ""  # 新增代码+ClaudeCodeToolRenderingParity：非空异常值用 JSON 兜底；如果没有这行代码，坏坐标会静默丢失。
# 新增代码+ClaudeCodeToolRenderingParity：函数段结束，_format_coordinate 到此结束；如果没有这个边界说明，用户不容易看出坐标格式化范围。


def _format_field_value(field_name: str, value: Any) -> str:  # 新增代码+ClaudeCodeToolRenderingParity：函数段开始，按 ClaudeCode 字段语义格式化单个值；如果没有这段函数，字段展示会散落在主函数里。
    if field_name in {"coordinate", "start_coordinate"}:  # 新增代码+ClaudeCodeToolRenderingParity：坐标字段走专门格式；如果没有这行代码，坐标不会显示为 (x, y)。
        return _format_coordinate(value)  # 新增代码+ClaudeCodeToolRenderingParity：返回坐标文本；如果没有这行代码，调用方拿不到格式化坐标。
    if field_name == "text":  # 新增代码+ClaudeCodeToolRenderingParity：文本字段需要截断并加引号；如果没有这行代码，长输入会完整显示。
        return f'"{_truncate_text(str(value or ""))}"'  # 新增代码+ClaudeCodeToolRenderingParity：返回带引号的短文本；如果没有这行代码，模型/用户难以区分文本边界。
    if field_name == "apps" and isinstance(value, list):  # 新增代码+ClaudeCodeToolRenderingParity：授权 app 列表走名称摘要；如果没有这行代码，request_access 会显示过长对象。
        names = [str(item.get("displayName", item.get("name", item.get("bundleId", ""))) or "") for item in value if isinstance(item, dict)]  # 新增代码+ClaudeCodeToolRenderingParity：提取 displayName/name/bundleId；如果没有这行代码，app 名称无法变成可读列表。
        return ", ".join(name for name in names if name)  # 新增代码+ClaudeCodeToolRenderingParity：合并非空应用名；如果没有这行代码，应用列表摘要无法展示。
    if field_name == "actions" and isinstance(value, list):  # 新增代码+ClaudeCodeToolRenderingParity：批量动作字段走数量摘要；如果没有这行代码，computer_batch 会显示完整动作数组。
        return f"{len(value)} actions"  # 新增代码+ClaudeCodeToolRenderingParity：返回动作数量；如果没有这行代码，批量工具摘要不够简洁。
    return _compact_json(value) if isinstance(value, (dict, list, tuple)) else str(value)  # 新增代码+ClaudeCodeToolRenderingParity：复杂值用 JSON、简单值用字符串；如果没有这行代码，字段格式会不稳定。
# 新增代码+ClaudeCodeToolRenderingParity：函数段结束，_format_field_value 到此结束；如果没有这个边界说明，用户不容易看出字段值格式化范围。


def render_tool_use_message(tool_name: str, arguments: dict[str, Any]) -> str:  # 新增代码+ClaudeCodeToolRenderingParity：函数段开始，用 ClaudeCode 字段名渲染工具调用参数；如果没有这段函数，UI/日志只能显示整段 JSON。
    parts: list[str] = []  # 新增代码+ClaudeCodeToolRenderingParity：准备累积字段片段；如果没有这行代码，多个字段无法有序输出。
    for field_name in CLAUDECODE_RENDER_FIELD_NAMES:  # 新增代码+ClaudeCodeToolRenderingParity：按 ClaudeCode 字段顺序遍历；如果没有这行代码，字段顺序会跟 dict 插入顺序漂移。
        if field_name not in arguments:  # 新增代码+ClaudeCodeToolRenderingParity：跳过本次调用没有的字段；如果没有这行代码，摘要会包含大量空字段。
            continue  # 新增代码+ClaudeCodeToolRenderingParity：继续处理下一个字段；如果没有这行代码，缺字段会进入格式化并产生噪音。
        formatted = _format_field_value(field_name, arguments.get(field_name))  # 新增代码+ClaudeCodeToolRenderingParity：格式化当前字段值；如果没有这行代码，字段无法变成可读文本。
        if formatted:  # 新增代码+ClaudeCodeToolRenderingParity：只输出非空值；如果没有这行代码，空字符串字段会制造多余片段。
            parts.append(f"{field_name}={formatted}")  # 新增代码+ClaudeCodeToolRenderingParity：保留字段名和值；如果没有这行代码，摘要无法证明使用的是 ClaudeCode 字段名。
    return " ".join(parts)  # 新增代码+ClaudeCodeToolRenderingParity：返回完整工具调用摘要；如果没有这行代码，调用方拿不到渲染结果。
# 新增代码+ClaudeCodeToolRenderingParity：函数段结束，render_tool_use_message 到此结束；如果没有这个边界说明，用户不容易看出工具调用渲染范围。


def render_tool_result(result: dict[str, Any], tool_name: str = "") -> str:  # 修改代码+ClaudeCodeToolRenderingParity：函数段开始，把工具结果渲染为简短文本；如果没有这段函数，UI 和日志会各自序列化。
    safe_tool_name = str(tool_name or result.get("tool_name", result.get("tool", "")) or "")  # 新增代码+ClaudeCodeToolRenderingParity：优先读取显式工具名并兼容旧字段；如果没有这行代码，摘要无法按工具类型选择。
    summary = RESULT_SUMMARY.get(safe_tool_name)  # 新增代码+ClaudeCodeToolRenderingParity：读取 ClaudeCode 风格结果摘要；如果没有这行代码，所有工具都会落回 JSON。
    if summary and bool(result.get("ok", False)):  # 新增代码+ClaudeCodeToolRenderingParity：成功且有摘要时使用短文本；如果没有这行代码，成功结果会继续显示大 JSON。
        return summary  # 新增代码+ClaudeCodeToolRenderingParity：返回短摘要；如果没有这行代码，调用方拿不到非 verbose 完成提示。
    return json.dumps(result, ensure_ascii=False, sort_keys=True)  # 修改代码+ClaudeCodeToolRenderingParity：失败或未知工具返回稳定 JSON；如果没有这行代码，失败细节会丢失。
# 修改代码+ClaudeCodeToolRenderingParity：函数段结束，render_tool_result 到此结束；如果没有这个边界说明，用户不容易看出渲染范围。

