"""Computer Use MCP v2 鼠标键盘动作。"""  # 新增代码+ComputerUseMcpV2：说明本文件管理真实桌面原子动作；如果没有这行代码，动作逻辑会混入 runtime。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

import time  # 新增代码+ComputerUseMcpV2：导入时间模块用于双击间隔；如果没有这行代码，双击无法有最小间隔。
from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，参数边界不清楚。

from .coordinates import int_coordinate  # 新增代码+ComputerUseMcpV2：导入坐标清洗；如果没有这行代码，鼠标坐标可能因坏输入崩溃。
from .errors import error_result  # 新增代码+ComputerUseMcpV2：导入失败结果；如果没有这行代码，动作失败格式会漂移。
from .result_blocks import success_result  # 新增代码+ComputerUseMcpV2：导入成功结果；如果没有这行代码，动作成功格式会漂移。
from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入上下文；如果没有这行代码，host 动作能力无法注入。


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
    return success_result(tool_name, payload, legacy_adapter_used=legacy_adapter_used)  # 新增代码+McpHostFailureFix: host 未失败时沿用成功包装；如果没有这一行，正常 cursor/click host 结果会丢失统一 runtime 字段。
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
    if tool_name in {"mouse_move", "left_click", "double_click", "right_click", "scroll"}:  # 新增代码+ComputerUseMcpV2：识别鼠标类动作；如果没有这行代码，鼠标动作会被误判未知。
        x = int_coordinate(arguments.get("x"))  # 新增代码+ComputerUseMcpV2：读取 x 坐标；如果没有这行代码，鼠标动作没有横坐标。
        y = int_coordinate(arguments.get("y"))  # 新增代码+ComputerUseMcpV2：读取 y 坐标；如果没有这行代码，鼠标动作没有纵坐标。
        if tool_name == "double_click":  # 新增代码+ComputerUseMcpV2：识别双击动作；如果没有这行代码，双击不会包含间隔摘要。
            time.sleep(0.05)  # 新增代码+ComputerUseMcpV2：提供最小双击间隔；如果没有这行代码，某些后端难以区分双击。
        return success_result(tool_name, {"x": x, "y": y, "backend": "computer_use_mcp_v2_noop_safe"})  # 新增代码+ComputerUseMcpV2：返回安全摘要；如果没有这行代码，无 host 时鼠标动作会崩溃。
    if tool_name == "type":  # 新增代码+ComputerUseMcpV2：识别文本输入；如果没有这行代码，type 会被误判未知。
        text = str(arguments.get("text", ""))  # 新增代码+ComputerUseMcpV2：读取输入文本；如果没有这行代码，无法计算长度。
        return success_result(tool_name, {"text_length": len(text), "backend": "computer_use_mcp_v2_noop_safe"})  # 新增代码+ComputerUseMcpV2：返回脱敏长度；如果没有这行代码，文本输入结果可能泄露全文或为空。
    if tool_name == "key":  # 新增代码+ComputerUseMcpV2：识别按键动作；如果没有这行代码，key 会被误判未知。
        return success_result(tool_name, {"keys": list(arguments.get("keys", []) or []), "backend": "computer_use_mcp_v2_noop_safe"})  # 新增代码+ComputerUseMcpV2：返回按键摘要；如果没有这行代码，模型无法确认按键已处理。
    return error_result(tool_name, f"unknown_v2_action:{tool_name}", error_class="unknown_tool")  # 新增代码+ComputerUseMcpV2：返回未知动作；如果没有这行代码，函数会隐式返回 None。
# 新增代码+ComputerUseMcpV2：函数段结束，perform_action 到此结束；如果没有这个边界说明，用户不容易看出动作分发范围。
