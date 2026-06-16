"""Computer Use MCP v2 鼠标键盘动作。"""  # 新增代码+ComputerUseMcpV2：说明本文件管理真实桌面原子动作；如果没有这行代码，动作逻辑会混入 runtime。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，参数边界不清楚。

from .errors import error_result  # 新增代码+ComputerUseMcpV2：导入失败结果；如果没有这行代码，动作失败格式会漂移。
from .result_blocks import success_result  # 新增代码+ComputerUseMcpV2：导入成功结果；如果没有这行代码，动作成功格式会漂移。
from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入上下文；如果没有这行代码，host 动作能力无法注入。

MUTATING_ACTION_TOOL_NAMES = {  # 新增代码+ClaudeCodeParity：集中列出必须由 host 执行的桌面写动作；如果没有这个集合，无 host 分支会继续把真实动作伪装成安全成功。
    "mouse_move",  # 新增代码+ClaudeCodeParity：鼠标移动会改变真实桌面光标位置；如果没有这一项，无 host mouse_move 可能继续假成功。
    "left_click",  # 新增代码+ClaudeCodeParity：左键点击会触发真实桌面动作；如果没有这一项，无 host left_click 会继续假成功。
    "double_click",  # 新增代码+ClaudeCodeParity：双击会触发真实桌面动作；如果没有这一项，无 host double_click 会继续假成功。
    "right_click",  # 新增代码+ClaudeCodeParity：右键点击会触发真实桌面动作；如果没有这一项，无 host right_click 会继续假成功。
    "type",  # 新增代码+ClaudeCodeParity：文本输入会改变真实应用内容；如果没有这一项，无 host type 会继续假成功。
    "key",  # 新增代码+ClaudeCodeParity：按键会改变真实应用状态；如果没有这一项，无 host key 会继续假成功。
    "scroll",  # 新增代码+ClaudeCodeParity：滚动会改变真实界面位置；如果没有这一项，无 host scroll 会继续假成功。
    "hold_key",  # 新增代码+ClaudeCodeParity：按住按键属于真实键盘副作用；如果没有这一项，无 host hold_key 可能被误报成功。
    "left_click_drag",  # 新增代码+ClaudeCodeParity：拖拽属于真实鼠标副作用；如果没有这一项，无 host left_click_drag 可能被误报成功。
    "middle_click",  # 新增代码+ClaudeCodeParity：中键点击属于真实鼠标副作用；如果没有这一项，无 host middle_click 可能被误报成功。
    "triple_click",  # 新增代码+ClaudeCodeParity：三击属于真实鼠标副作用；如果没有这一项，无 host triple_click 可能被误报成功。
    "left_mouse_down",  # 新增代码+ClaudeCodeParity：左键按下会改变鼠标状态；如果没有这一项，无 host left_mouse_down 可能被误报成功。
    "left_mouse_up",  # 新增代码+ClaudeCodeParity：左键释放会改变鼠标状态；如果没有这一项，无 host left_mouse_up 可能被误报成功。
}  # 新增代码+ClaudeCodeParity：桌面写动作集合结束；如果没有这一行，Python 集合语法不完整。


def _host_required_result(tool_name: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeParity：函数段开始，生成缺少 host 时的明确失败结果；如果没有这段函数，各写动作会重复手写且容易漏 payload。
    result = error_result(tool_name, f"host_required_for_desktop_action:{tool_name}", error_class="host_required")  # 新增代码+ClaudeCodeParity：创建统一 host_required 错误；如果没有这一行，模型无法区分缺 host 和未知工具。
    result["payload"] = {"requires_host": True, "desktop_action_performed": False}  # 新增代码+ClaudeCodeParity：明确说明需要 host 且没有执行真实桌面动作；如果没有这一行，验收可能误判桌面已经被操作。
    return result  # 新增代码+ClaudeCodeParity：返回带 payload 的失败结果；如果没有这一行，调用方拿不到错误对象。
# 新增代码+ClaudeCodeParity：函数段结束，_host_required_result 到此结束；如果没有这个边界说明，用户不容易看出缺 host 失败格式范围。


def _host_call(context: ComputerUseMcpV2Context, method_name: str, *args: Any, **kwargs: Any) -> dict[str, Any] | None:  # 新增代码+ComputerUseMcpV2：函数段开始，调用注入 host 方法；如果没有这段函数，每个动作都要重复 getattr/callable 判断。
    method = getattr(context.host, method_name, None) if context.host is not None else None  # 新增代码+ComputerUseMcpV2：读取 host 方法；如果没有这行代码，动作无法使用成熟宿主实现。
    return dict(method(*args, **kwargs) or {}) if callable(method) else None  # 新增代码+ComputerUseMcpV2：调用 host 或返回 None；如果没有这行代码，runtime 无法区分 host 有无实现。
# 新增代码+ComputerUseMcpV2：函数段结束，_host_call 到此结束；如果没有这个边界说明，用户不容易看出 host 调用范围。


def _host_payload_result(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpHostFailureFix: 函数段开始，把 host payload 转成顶层 v2 结果；如果没有这段函数，host 拒绝仍可能被包装成成功。
    legacy_adapter_used = bool(payload.get("legacy_adapter_used", False))  # 新增代码+McpHostFailureFix: 读取旧 adapter 来源标记；如果没有这一行，失败路径会丢失真实执行来源。
    nested_result = payload.get("legacy_result") if isinstance(payload.get("legacy_result"), dict) else {}  # 新增代码+McpHostFailureFix: 读取旧 session adapter 内层结果；如果没有这一行，真实失败类别可能藏在 legacy_result 里拿不到。
    if payload.get("ok") is False:  # 新增代码+McpHostFailureFix: host 明确失败时进入失败包装；如果没有这一行，下层 ok=false 会被顶层 success_result 改成 ok=true。
        reason = str(payload.get("reason") or payload.get("message") or nested_result.get("reason") or nested_result.get("payload", {}).get("legacy_text", "") or "host_adapter_rejected")  # 新增代码+McpHostFailureFix: 提取可读失败原因；如果没有这一行，模型只知道失败但不知道为什么失败。
        error_class = str(payload.get("error_class") or nested_result.get("error_class") or "host_adapter_rejected")  # 新增代码+McpHostFailureFix: 保留旧门禁失败类别；如果没有这一行，恢复逻辑无法区分缺窗口和普通 host 错误。
        return {"ok": False, "runtime": "computer_use_mcp_v2", "legacy_adapter_used": legacy_adapter_used, "tool_name": str(tool_name), "reason": reason, "error_class": error_class, "payload": dict(payload)}  # 新增代码+McpHostFailureFix: 返回顶层失败结果且保留原始 payload；如果没有这一行，验收事件会再次误报动作成功。
    content = payload.get("content") if isinstance(payload.get("content"), list) else None  # 新增代码+ClaudeCodeContentParity：透传 host 已生成的 content blocks；如果没有这行代码，host 级图片或文本块会被成功包装吞掉。
    debug = payload.get("debug") if isinstance(payload.get("debug"), dict) else None  # 新增代码+ClaudeCodeContentParity：透传 host 已生成的 debug 证据；如果没有这行代码，artifact_path 等调试信息会丢失。
    return success_result(tool_name, payload, legacy_adapter_used=legacy_adapter_used, content=content, debug=debug)  # 修改代码+ClaudeCodeContentParity: host 未失败时沿用成功包装并保留 content/debug；如果没有这一行，正常 cursor/click host 结果会丢失统一 runtime 字段或新协议块。
# 新增代码+McpHostFailureFix: 函数段结束，_host_payload_result 到此结束；如果没有这个边界说明，用户不容易看出 host payload 包装范围。


def cursor_position(context: ComputerUseMcpV2Context) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，读取光标位置；如果没有这段函数，cursor_position 无法执行。
    payload = _host_call(context, "cursor_position")  # 新增代码+ComputerUseMcpV2：优先调用 host 光标读取；如果没有这行代码，测试 fake host 无法接管。
    if payload is not None:  # 新增代码+ComputerUseMcpV2：检查 host 是否返回结果；如果没有这行代码，None 会被当成结果。
        return _host_payload_result("cursor_position", payload)  # 修改代码+McpHostFailureFix: 统一传播 host 成功或失败；如果没有这一行，cursor_position host 拒绝也可能被包装成成功。
    try:  # 新增代码+ComputerUseMcpV2：尝试调用 Windows API；如果没有这行代码，非 Windows 会直接崩溃。
        import ctypes  # 新增代码+ComputerUseMcpV2：延迟导入 ctypes；如果没有这行代码，无法读取真实 Windows 光标坐标。
        class _Point(ctypes.Structure):  # 新增代码+ComputerUseMcpV2：定义 POINT 结构；如果没有这段类，GetCursorPos 没有输出容器。
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]  # 新增代码+ComputerUseMcpV2：声明 x/y 字段；如果没有这行代码，Windows API 无法写入坐标。
        point = _Point()  # 新增代码+ComputerUseMcpV2：创建 POINT 实例；如果没有这行代码，API 调用没有目标。
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))  # type: ignore[attr-defined]  # 新增代码+ComputerUseMcpV2：读取系统光标坐标；如果没有这行代码，工具拿不到真实位置。
        return success_result("cursor_position", {"x": int(point.x), "y": int(point.y), "backend": "windows_user32"})  # 新增代码+ComputerUseMcpV2：返回真实坐标；如果没有这行代码，模型无法使用读取结果。
    except Exception as error:  # 新增代码+ComputerUseMcpV2：捕获平台和 API 异常；如果没有这行代码，非 Windows 测试会崩溃。
        return error_result("cursor_position", str(error), error_class="cursor_position_unavailable")  # 新增代码+ComputerUseMcpV2：返回不可用原因；如果没有这行代码，模型不知道如何恢复。
# 新增代码+ComputerUseMcpV2：函数段结束，cursor_position 到此结束；如果没有这个边界说明，用户不容易看出光标读取范围。


def perform_action(context: ComputerUseMcpV2Context, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，执行鼠标键盘动作；如果没有这段函数，left_click/type/key 等无法运行。
    if tool_name == "cursor_position":  # 新增代码+ComputerUseMcpV2：处理只读光标工具；如果没有这行代码，cursor_position 会落入动作分支。
        return cursor_position(context)  # 新增代码+ComputerUseMcpV2：返回光标位置结果；如果没有这行代码，只读工具无法复用专门实现。
    payload = _host_call(context, tool_name, arguments)  # 新增代码+ComputerUseMcpV2：优先调用同名 host 方法；如果没有这行代码，成熟宿主无法接管原子动作。
    if payload is not None:  # 新增代码+ComputerUseMcpV2：检查 host 是否处理动作；如果没有这行代码，host 结果会被忽略。
        return _host_payload_result(tool_name, payload)  # 修改代码+McpHostFailureFix: 统一传播 host 成功或失败；如果没有这一行，left_click 被旧门禁拒绝时仍会显示 ok=true。
    if tool_name in MUTATING_ACTION_TOOL_NAMES:  # 新增代码+ClaudeCodeParity：无 host 且工具是写动作时统一失败；如果没有这一行，真实桌面动作会继续 noop 假成功。
        return _host_required_result(tool_name)  # 新增代码+ClaudeCodeParity：返回 host_required 且声明未操作桌面；如果没有这一行，验收无法区分失败和已执行。
    if tool_name == "zoom":  # 新增代码+ClaudeCodeParity：显式处理 zoom 只读工具的无 host 场景；如果没有这一行，公开的 zoom 工具会被误报为 unknown_tool。
        result = error_result("zoom", "zoom_unavailable_without_host", error_class="host_unavailable")  # 新增代码+ClaudeCodeParity：返回 zoom 缺少宿主实现的清晰错误；如果没有这一行，模型只能看到未知工具而不是缺后端。
        result["payload"] = {"requires_host": True, "desktop_action_performed": False}  # 新增代码+ClaudeCodeParity：说明 zoom 没有修改桌面且需要 host 提供观察能力；如果没有这一行，读者会难以判断是否发生副作用。
        return result  # 新增代码+ClaudeCodeParity：返回 zoom 无 host 错误；如果没有这一行，函数会继续落入 unknown_tool。
    return error_result(tool_name, f"unknown_v2_action:{tool_name}", error_class="unknown_tool")  # 新增代码+ComputerUseMcpV2：返回未知动作；如果没有这行代码，函数会隐式返回 None。
# 新增代码+ComputerUseMcpV2：函数段结束，perform_action 到此结束；如果没有这个边界说明，用户不容易看出动作分发范围。
