"""独立 Computer Use MCP 工具执行器。"""  # 新增代码+ComputerUseMCP：说明本文件负责把 MCP 工具调用转成受控桌面语义；如果没有这行代码，读者难以区分 schema 和执行层。
from __future__ import annotations  # 新增代码+ComputerUseMCP：延迟类型解析以降低导入耦合；如果没有这行代码，部分运行方式可能因类型提前求值失败。

import json  # 新增代码+ComputerUseMCP：导入 JSON 用于稳定返回工具结果；如果没有这行代码，server 无法把结构化结果转成文本。
import time  # 新增代码+ComputerUseMCP：导入时间模块用于 wait 工具；如果没有这行代码，等待工具只能空转或缺实现。
from dataclasses import dataclass, field  # 新增代码+ComputerUseMCP：导入 dataclass 简化运行上下文；如果没有这行代码，上下文对象要手写初始化。
from typing import Any, Callable  # 新增代码+ComputerUseMCP：导入通用类型和回调类型；如果没有这行代码，executor 边界注解不清楚。

try:  # 新增代码+ComputerUseMCP：优先按包路径导入 Computer Use 组件；如果没有这行代码，正常包运行无法找到 controller。
    from learning_agent.computer_use_mcp_v2.windows_runtime.controller import ComputerUseController, build_default_computer_use_backend  # 新增代码+ComputerUseMCP：导入 controller 和默认后端工厂；如果没有这行代码，MCP 动作无法复用现有桌面安全链。
    from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_tool_schemas import SHELL_FORBIDDEN_ARGUMENT_NAMES, SHELL_FORBIDDEN_TOOL_NAMES  # 新增代码+ComputerUseMCP：导入 shell 禁止清单；如果没有这行代码，executor 无法执行边界自检。
    from learning_agent.computer_use_mcp_v2.windows_runtime.request_access_tool import request_computer_use_access  # 新增代码+ComputerUseMCP：导入授权申请纯函数；如果没有这行代码，request_access 会变成空壳。
except ModuleNotFoundError as error:  # 新增代码+ComputerUseMCP：兼容直接脚本模式导入；如果没有这行代码，server 作为文件运行时可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.controller", "learning_agent.computer_use_mcp_v2.windows_runtime.mcp_tool_schemas", "learning_agent.computer_use_mcp_v2.windows_runtime.request_access_tool"}:  # 新增代码+ComputerUseMCP：只吞包路径差异，不吞真实内部错误；如果没有这行代码，真正 bug 会被隐藏。
        raise  # 新增代码+ComputerUseMCP：重新抛出真实导入错误；如果没有这行代码，排查导入问题会很困难。
    from computer_use_mcp_v2.windows_runtime.controller import ComputerUseController, build_default_computer_use_backend  # type: ignore  # 新增代码+ComputerUseMCP：脚本模式导入 controller；如果没有这行代码，bat 或直接运行路径会断开。
    from computer_use_mcp_v2.windows_runtime.mcp_tool_schemas import SHELL_FORBIDDEN_ARGUMENT_NAMES, SHELL_FORBIDDEN_TOOL_NAMES  # type: ignore  # 新增代码+ComputerUseMCP：脚本模式导入禁止清单；如果没有这行代码，直接运行 server 缺少安全边界。
    from computer_use_mcp_v2.windows_runtime.request_access_tool import request_computer_use_access  # type: ignore  # 新增代码+ComputerUseMCP：脚本模式导入授权申请函数；如果没有这行代码，request_access 无法执行。


# 新增代码+ComputerUseMCP：函数段开始，_default_controller_factory 创建默认 controller；如果没有这段函数，运行上下文无法懒加载现有桌面后端。
def _default_controller_factory() -> ComputerUseController:  # 新增代码+ComputerUseMCP：声明默认 controller 工厂；如果没有这行代码，executor 初始化要在全局导入时碰真实后端。
    return ComputerUseController(build_default_computer_use_backend())  # 新增代码+ComputerUseMCP：复用现有安全默认后端；如果没有这行代码，MCP 会绕开原有 Computer Use 门禁。
# 新增代码+ComputerUseMCP：函数段结束，_default_controller_factory 到此结束；如果没有这个边界说明，初学者不容易看出默认后端创建范围。


@dataclass  # 新增代码+ComputerUseMCP：自动生成运行上下文初始化逻辑；如果没有这行代码，context 要手动维护多个可选字段。
class ComputerUseMcpExecutionContext:  # 新增代码+ComputerUseMCP：定义一次 MCP server 执行期共享的上下文；如果没有这段类，controller 和授权状态会散落在函数参数里。
    controller_factory: Callable[[], Any] = _default_controller_factory  # 新增代码+ComputerUseMCP：保存 controller 工厂便于测试注入；如果没有这行代码，单元测试可能误碰真实桌面后端。
    session_adapter: Any | None = None  # 新增代码+McpSessionAdapter: 保存 agent-side session adapter；如果没有这一行，独立 MCP 原子工具无法复用 agent 主循环的权限、观察、trace 和验收回调。
    grants: dict[str, Any] = field(default_factory=dict)  # 新增代码+ComputerUseMCP：保存本 server 进程内的授权摘要；如果没有这行代码，list_granted_applications 没有事实源。
    clipboard_text: str = ""  # 新增代码+ComputerUseMCP：保存受控剪贴板模拟文本；如果没有这行代码，未接真实剪贴板时 write/read 无法形成可测试闭环。
    _controller: Any | None = None  # 新增代码+ComputerUseMCP：缓存 controller 实例；如果没有这行代码，每次工具调用都会重建后端状态。

    # 新增代码+ComputerUseMCP：函数段开始，controller 懒加载并返回 controller；如果没有这段函数，测试和生产都要自己管理 controller 生命周期。
    def controller(self) -> Any:  # 新增代码+ComputerUseMCP：声明 controller 读取入口；如果没有这行代码，执行函数无法拿到桌面控制器。
        if self._controller is None:  # 新增代码+ComputerUseMCP：首次使用时才创建 controller；如果没有这行代码，导入 server 就可能初始化桌面后端。
            self._controller = self.controller_factory()  # 新增代码+ComputerUseMCP：调用可注入工厂生成 controller；如果没有这行代码，测试无法替换为内存后端。
        return self._controller  # 新增代码+ComputerUseMCP：返回缓存 controller；如果没有这行代码，调用方拿不到执行入口。
    # 新增代码+ComputerUseMCP：函数段结束，controller 到此结束；如果没有这个边界说明，初学者不容易看出懒加载范围。


# 新增代码+ComputerUseMCP：函数段开始，_json_result 生成统一结果字典；如果没有这段函数，每个分支会重复拼 ok/tool/result。
def _json_result(tool_name: str, ok: bool, payload: dict[str, Any], *, error_class: str = "") -> dict[str, Any]:  # 新增代码+ComputerUseMCP：声明统一结果 helper；如果没有这行代码，成功和失败输出字段可能漂移。
    result = {"ok": bool(ok), "tool_name": tool_name, "error_class": error_class, "payload": payload}  # 新增代码+ComputerUseMCP：构造机器可读结果；如果没有这行代码，模型难以判断工具是否成功。
    result["text"] = json.dumps(result, ensure_ascii=False, sort_keys=True)  # 新增代码+ComputerUseMCP：生成稳定文本副本；如果没有这行代码，MCP content 返回需要重复序列化。
    return result  # 新增代码+ComputerUseMCP：返回统一结果对象；如果没有这行代码，调用方无法取得执行结果。
# 新增代码+ComputerUseMCP：函数段结束，_json_result 到此结束；如果没有这个边界说明，初学者不容易看出统一输出范围。

# 新增代码+ClaudeCodeToolSurface：函数段开始，_unsupported_result 生成明确 unsupported 响应；如果没有这段函数，预留工具可能被误报成 controller_rejected 或假成功。
def _unsupported_result(tool_name: str, reason: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeToolSurface：声明不支持工具的统一返回入口；如果没有这行代码，每个预留工具会手写不同错误格式。
    return _json_result(tool_name, False, {"reason": reason, "supported": False}, error_class="unsupported_computer_use_tool")  # 新增代码+ClaudeCodeToolSurface：返回机器可读 unsupported 结果；如果没有这行代码，模型无法区分参数错和后端暂未实现。
# 新增代码+ClaudeCodeToolSurface：函数段结束，_unsupported_result 到此结束；如果没有这个边界说明，用户不容易看出预留工具失败格式。

# 新增代码+ClaudeCodeToolSurface：函数段开始，_cursor_position_result 读取当前 Windows 光标位置；如果没有这段函数，cursor_position 只能落到未知 controller 动作。
def _cursor_position_result(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeToolSurface：声明光标位置读取入口；如果没有这行代码，call_computer_use_mcp_tool 无法处理只读位置工具。
    try:  # 新增代码+ClaudeCodeToolSurface：用 try 捕获非 Windows 或 ctypes 不可用场景；如果没有这行代码，cursor_position 可能让 MCP server 崩溃。
        import ctypes  # 新增代码+ClaudeCodeToolSurface：延迟导入 ctypes 调用 Windows API；如果没有这行代码，无法从真实系统读取鼠标坐标。
        class _Point(ctypes.Structure):  # 新增代码+ClaudeCodeToolSurface：声明 Windows POINT 结构；如果没有这段类，GetCursorPos 没有稳定的坐标输出容器。
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]  # 新增代码+ClaudeCodeToolSurface：定义 x/y 两个 long 字段；如果没有这行代码，Windows API 不知道往哪里写坐标。
        point = _Point()  # 新增代码+ClaudeCodeToolSurface：创建 POINT 实例接收坐标；如果没有这行代码，GetCursorPos 没有输出对象。
        ok = bool(ctypes.windll.user32.GetCursorPos(ctypes.byref(point)))  # type: ignore[attr-defined]  # 新增代码+ClaudeCodeToolSurface：调用 User32 读取当前光标位置；如果没有这行代码，工具不会返回真实坐标。
        if ok:  # 新增代码+ClaudeCodeToolSurface：只有系统调用成功才返回坐标；如果没有这行代码，失败时可能读取到默认 0,0。
            return _json_result(tool_name, True, {"x": int(point.x), "y": int(point.y), "backend": "windows_user32", "reason": arguments.get("reason", "")})  # 新增代码+ClaudeCodeToolSurface：返回真实坐标和后端来源；如果没有这行代码，模型无法知道当前鼠标位置。
    except Exception as error:  # 新增代码+ClaudeCodeToolSurface：捕获平台或 API 异常并转成失败结果；如果没有这行代码，非 Windows 测试会被异常打断。
        return _json_result(tool_name, False, {"reason": str(error), "backend": "windows_user32"}, error_class="cursor_position_unavailable")  # 新增代码+ClaudeCodeToolSurface：返回不可用原因；如果没有这行代码，模型无法恢复或改用观察工具。
    return _json_result(tool_name, False, {"reason": "GetCursorPos returned false", "backend": "windows_user32"}, error_class="cursor_position_unavailable")  # 新增代码+ClaudeCodeToolSurface：处理 API 返回 false 的情况；如果没有这行代码，失败分支会隐式返回 None。
# 新增代码+ClaudeCodeToolSurface：函数段结束，_cursor_position_result 到此结束；如果没有这个边界说明，用户不容易看出光标读取范围。


# 新增代码+ComputerUseMCP：函数段开始，_contains_forbidden_argument_key 递归检查危险参数名；如果没有这段函数，batch 或嵌套参数可绕过顶层检查。
def _contains_forbidden_argument_key(value: Any) -> bool:  # 新增代码+ComputerUseMCP：声明递归参数检查入口；如果没有这行代码，executor 无法发现嵌套 command/script 字段。
    if isinstance(value, dict):  # 新增代码+ComputerUseMCP：处理 JSON 对象；如果没有这行代码，字典里的危险键不会被检查。
        for key, item in value.items():  # 新增代码+ComputerUseMCP：遍历每个键值；如果没有这行代码，只能检查整个对象字符串。
            if str(key).strip().lower() in SHELL_FORBIDDEN_ARGUMENT_NAMES:  # 新增代码+ComputerUseMCP：命中禁止字段名时拒绝；如果没有这行代码，command 字段可能进入桌面 MCP。
                return True  # 新增代码+ComputerUseMCP：返回发现危险字段；如果没有这行代码，检查结果无法上报。
            if _contains_forbidden_argument_key(item):  # 新增代码+ComputerUseMCP：继续检查嵌套值；如果没有这行代码，batch.steps.arguments.command 会漏掉。
                return True  # 新增代码+ComputerUseMCP：子层命中时向上传递；如果没有这行代码，递归结果会丢失。
    if isinstance(value, list):  # 新增代码+ComputerUseMCP：处理 JSON 数组；如果没有这行代码，批量步骤列表不会被检查。
        return any(_contains_forbidden_argument_key(item) for item in value)  # 新增代码+ComputerUseMCP：检查列表每一项；如果没有这行代码，危险字段可藏在数组元素中。
    return False  # 新增代码+ComputerUseMCP：非容器类型默认安全；如果没有这行代码，函数没有稳定布尔返回。
# 新增代码+ComputerUseMCP：函数段结束，_contains_forbidden_argument_key 到此结束；如果没有这个边界说明，初学者不容易看出递归检查范围。


# 新增代码+ComputerUseMCP：函数段开始，_reject_shell_surface 对工具名和参数做硬拒绝；如果没有这段函数，Computer Use MCP 可能被误用为命令执行入口。
def _reject_shell_surface(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:  # 新增代码+ComputerUseMCP：声明 shell 面拒绝 helper；如果没有这行代码，每个工具分支都要重复安全检查。
    normalized_name = str(tool_name or "").strip().lower()  # 新增代码+ComputerUseMCP：规范化工具名用于比较；如果没有这行代码，大小写变化可能绕过检查。
    if normalized_name in SHELL_FORBIDDEN_TOOL_NAMES:  # 新增代码+ComputerUseMCP：拒绝命令类工具名；如果没有这行代码，bash/powershell 可能被误路由。
        return _json_result(tool_name, False, {"reason": "Computer Use MCP 不暴露命令执行工具。"}, error_class="shell_tool_forbidden")  # 新增代码+ComputerUseMCP：返回结构化拒绝；如果没有这行代码，模型不知道为什么失败。
    if _contains_forbidden_argument_key(arguments):  # 新增代码+ComputerUseMCP：拒绝命令类参数名；如果没有这行代码，模型可能通过 command/script 参数绕过工具名限制。
        return _json_result(tool_name, False, {"reason": "Computer Use MCP 参数中禁止出现命令执行字段。"}, error_class="shell_argument_forbidden")  # 新增代码+ComputerUseMCP：返回结构化参数拒绝；如果没有这行代码，拒绝原因不可审计。
    return None  # 新增代码+ComputerUseMCP：没有命中危险面则允许继续；如果没有这行代码，调用方无法区分安全和拒绝。
# 新增代码+ComputerUseMCP：函数段结束，_reject_shell_surface 到此结束；如果没有这个边界说明，初学者不容易看出安全拒绝范围。


# 新增代码+ComputerUseMCP：函数段开始，_result_from_controller 调用 controller 并包装结果；如果没有这段函数，动作分支会重复 to_text/data 处理。
def _result_from_controller(context: ComputerUseMcpExecutionContext, tool_name: str, controller_arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMCP：声明 controller 适配 helper；如果没有这行代码，MCP 工具无法复用现有 controller。
    result = context.controller().execute(controller_arguments)  # 新增代码+ComputerUseMCP：调用现有 Computer Use controller；如果没有这行代码，MCP 会绕开安全门禁和审计链。
    payload = {"message": getattr(result, "message", ""), "data": getattr(result, "data", {}), "controller_action": controller_arguments.get("action", "")}  # 新增代码+ComputerUseMCP：整理 controller 返回内容；如果没有这行代码，模型拿不到动作和数据。
    return _json_result(tool_name, bool(getattr(result, "ok", False)), payload, error_class="" if bool(getattr(result, "ok", False)) else "controller_rejected")  # 新增代码+ComputerUseMCP：返回统一结果；如果没有这行代码，失败状态可能被当成成功文本。
# 新增代码+ComputerUseMCP：函数段结束，_result_from_controller 到此结束；如果没有这个边界说明，初学者不容易看出 controller 转接范围。


# 新增代码+ComputerUseMCP：函数段开始，_normalize_request_access 把 MCP 参数转成旧 request_access 纯函数参数；如果没有这段函数，授权申请会和既有安全提示分裂。
def _normalize_request_access(arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMCP：声明授权参数转换入口；如果没有这行代码，request_access_tool 收不到 expected 字段。
    applications = arguments.get("applications", [])  # 新增代码+ComputerUseMCP：读取 MCP 风格应用列表；如果没有这行代码，授权目标会丢失。
    return {  # 新增代码+ComputerUseMCP：开始返回旧工具兼容参数；如果没有这行代码，转换结果无法构造。
        "requested_apps": applications if isinstance(applications, list) else [],  # 新增代码+ComputerUseMCP：传递请求应用列表；如果没有这行代码，报告不会显示目标应用。
        "reason": str(arguments.get("reason", "")),  # 新增代码+ComputerUseMCP：传递申请原因；如果没有这行代码，用户看不到授权目的。
        "duration_seconds": arguments.get("duration_seconds", 600),  # 新增代码+ComputerUseMCP：传递授权时长；如果没有这行代码，时长会退回默认且不可见。
        "allow_mouse": bool(arguments.get("allow_mouse", True)),  # 新增代码+ComputerUseMCP：传递鼠标权限位；如果没有这行代码，报告无法体现鼠标需求。
        "allow_keyboard": bool(arguments.get("allow_keyboard", True)),  # 新增代码+ComputerUseMCP：传递键盘权限位；如果没有这行代码，报告无法体现键盘需求。
        "allow_clipboard": bool(arguments.get("allow_clipboard", False)),  # 新增代码+ComputerUseMCP：传递剪贴板权限位；如果没有这行代码，复制粘贴风险不可见。
    }  # 新增代码+ComputerUseMCP：结束旧工具兼容参数；如果没有这行代码，Python 字典语法不完整。
# 新增代码+ComputerUseMCP：函数段结束，_normalize_request_access 到此结束；如果没有这个边界说明，初学者不容易看出参数转换范围。


# 新增代码+ComputerUseMCP：函数段开始，_controller_arguments_for_tool 把 MCP 工具转成 controller action；如果没有这段函数，桌面语义会散落在各分支里。
def _controller_arguments_for_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMCP：声明动作映射入口；如果没有这行代码，open/click/type 等工具无法进入 controller。
    if tool_name in {"screenshot", "observe"}:  # 修改代码+ClaudeCodeToolSurface：screenshot 和 observe 共用只读截图动作；如果没有这行代码，observe 会落入未知动作。
        return {"action": "screenshot", "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 修改代码+ClaudeCodeToolSurface：返回截图动作参数；如果没有这行代码，controller 会因缺动作名拒绝。
    if tool_name == "zoom":  # 新增代码+ClaudeCodeToolSurface：把局部放大观察映射为带区域信息的截图动作；如果没有这行代码，zoom 会被 controller 当成未知动作。
        return {"action": "screenshot", "confirm_desktop_control": True, "region": {"x": arguments.get("x"), "y": arguments.get("y"), "width": arguments.get("width", 400), "height": arguments.get("height", 300)}, "zoom": True, "reason": arguments.get("reason", "")}  # 新增代码+ClaudeCodeToolSurface：携带区域和 zoom 标志给后端；如果没有这行代码，局部观察会丢失坐标范围。
    if tool_name == "open_application":  # 新增代码+ComputerUseMCP：映射打开应用工具；如果没有这行代码，open_application 不会复用 launch_app。
        return {"action": "launch_app", "target_app": arguments.get("app_name", ""), "app_name": arguments.get("app_name", ""), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ComputerUseMCP：返回启动应用参数；如果没有这行代码，controller 找不到目标应用。
    if tool_name == "mouse_move":  # 新增代码+ComputerUseMCP：映射鼠标移动工具；如果没有这行代码，mouse_move 不会复用 move_mouse。
        return {"action": "move_mouse", "x": arguments.get("x"), "y": arguments.get("y"), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ComputerUseMCP：返回移动参数；如果没有这行代码，坐标不会传给 controller。
    if tool_name in {"click", "left_click", "middle_click"}:  # 修改代码+ClaudeCodeToolSurface：兼容旧 click、新 left_click 和预留 middle_click；如果没有这行代码，新点击名无法复用真实动作链。
        button = "middle" if tool_name == "middle_click" else arguments.get("button", "left")  # 新增代码+ClaudeCodeToolSurface：middle_click 固定中键，其余默认左键；如果没有这行代码，中键预留工具会被错误当左键。
        return {"action": "click", "x": arguments.get("x"), "y": arguments.get("y"), "button": button, "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 修改代码+ClaudeCodeToolSurface：返回点击参数；如果没有这行代码，controller 无法知道点击位置。
    if tool_name == "double_click":  # 新增代码+ComputerUseMCP：映射双击工具；如果没有这行代码，double_click 不会进入 controller。
        return {"action": "double_click", "x": arguments.get("x"), "y": arguments.get("y"), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ComputerUseMCP：返回双击参数；如果没有这行代码，坐标会丢失。
    if tool_name == "right_click":  # 新增代码+ComputerUseMCP：映射右键工具；如果没有这行代码，right_click 会因为 controller 无该动作而直接失败。
        return {"action": "click", "x": arguments.get("x"), "y": arguments.get("y"), "button": "right", "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ComputerUseMCP：用 click+right 表达右键；如果没有这行代码，右键无法复用现有点击链。
    if tool_name == "type":  # 新增代码+ComputerUseMCP：映射文本输入工具；如果没有这行代码，type 不会复用 type_text。
        return {"action": "type_text", "text": arguments.get("text", ""), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ComputerUseMCP：返回输入参数；如果没有这行代码，文本不会传给 controller。
    if tool_name == "key":  # 新增代码+ComputerUseMCP：映射按键工具；如果没有这行代码，key 不会复用 press_key。
        keys = arguments.get("keys", [])  # 新增代码+ComputerUseMCP：读取按键数组；如果没有这行代码，组合键无法处理。
        return {"action": "press_key", "key": "+".join(str(key) for key in keys) if isinstance(keys, list) else str(keys), "keys": keys, "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ComputerUseMCP：返回按键参数；如果没有这行代码，controller 无法收到按键。
    if tool_name == "hold_key":  # 新增代码+ClaudeCodeToolSurface：映射按住按键工具；如果没有这行代码，hold_key 会被当成未知动作。
        keys = arguments.get("keys", [])  # 新增代码+ClaudeCodeToolSurface：读取要按住的按键数组；如果没有这行代码，组合按住动作无法表达。
        return {"action": "press_key", "key": "+".join(str(key) for key in keys) if isinstance(keys, list) else str(keys), "keys": keys, "hold_duration_seconds": arguments.get("duration_seconds", 1), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ClaudeCodeToolSurface：用 press_key 后端承载按住语义和时长提示；如果没有这行代码，后端拿不到时长。
    if tool_name == "scroll":  # 新增代码+ComputerUseMCP：映射滚动工具；如果没有这行代码，scroll 不会进入 controller。
        return {"action": "scroll", "x": arguments.get("x"), "y": arguments.get("y"), "delta_y": arguments.get("delta_y", -500), "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ComputerUseMCP：返回滚动参数；如果没有这行代码，滚动方向会丢失。
    if tool_name == "left_click_drag":  # 新增代码+ClaudeCodeToolSurface：映射左键拖拽工具；如果没有这行代码，绘图和拖放不能走独立 MCP 原子工具。
        points = [{"x": arguments.get("start_x"), "y": arguments.get("start_y")}, {"x": arguments.get("end_x"), "y": arguments.get("end_y")}]  # 新增代码+ClaudeCodeToolSurface：把起点终点转成 drag_path 点列；如果没有这行代码，现有 controller 无法识别 start/end 字段。
        return {"action": "drag_path", "points": points, "duration_seconds": arguments.get("duration_seconds", 0.5), "button": "left", "confirm_desktop_control": True, "reason": arguments.get("reason", "")}  # 新增代码+ClaudeCodeToolSurface：调用已有拖拽路径动作；如果没有这行代码，真实后端不会收到可执行拖拽语义。
    return {"action": tool_name, "confirm_desktop_control": True}  # 新增代码+ComputerUseMCP：未知映射保守交给 controller 拒绝；如果没有这行代码，函数可能返回 None 造成异常。
# 新增代码+ComputerUseMCP：函数段结束，_controller_arguments_for_tool 到此结束；如果没有这个边界说明，初学者不容易看出动作映射范围。


# 新增代码+ComputerUseMCP：函数段开始，call_computer_use_mcp_tool 执行单个 MCP 工具；如果没有这段函数，stdio server 和测试没有统一执行入口。
def call_computer_use_mcp_tool(tool_name: str, arguments: dict[str, Any] | None = None, context: ComputerUseMcpExecutionContext | None = None) -> dict[str, Any]:  # 新增代码+ComputerUseMCP：声明公开执行入口；如果没有这行代码，server 无法分发 tools/call。
    safe_arguments = dict(arguments or {})  # 新增代码+ComputerUseMCP：复制参数避免污染调用方对象；如果没有这行代码，后续补字段可能改掉原始请求。
    runtime = context or ComputerUseMcpExecutionContext()  # 新增代码+ComputerUseMCP：没有传入上下文时创建默认上下文；如果没有这行代码，独立调用会失败。
    if runtime.session_adapter is not None and str(tool_name or "").strip() == "computer_batch":  # 新增代码+McpSessionAdapter: agent 绑定存在时让 batch 先交给 adapter 做逐步拒绝；如果没有这一行，嵌套 command 会被顶层模糊拒绝且无法证明第二步未执行。
        return runtime.session_adapter.call_atomic_tool(tool_name, safe_arguments)  # 新增代码+McpSessionAdapter: 复用同一个 session adapter 执行 batch；如果没有这一行，batch 会绕开 agent-side 回调和共享状态。
    rejection = _reject_shell_surface(tool_name, safe_arguments)  # 新增代码+ComputerUseMCP：先执行 shell 面硬拒绝；如果没有这行代码，危险参数可能进入后续分发。
    if rejection is not None:  # 新增代码+ComputerUseMCP：判断是否命中危险面；如果没有这行代码，拒绝结果会被忽略。
        return rejection  # 新增代码+ComputerUseMCP：直接返回拒绝不触碰 controller；如果没有这行代码，shell 绕路仍可能继续执行。
    if runtime.session_adapter is not None:  # 新增代码+McpSessionAdapter: agent 绑定存在时优先走 session adapter；如果没有这一行，MCP 原子工具仍会绕开 ask_permission、record_observation、record_runtime_trace 等主循环能力。
        return runtime.session_adapter.call_atomic_tool(tool_name, safe_arguments)  # 新增代码+McpSessionAdapter: 把原子工具交给 adapter 执行；如果没有这一行，click/type 等工具会继续直连独立 controller。
    if tool_name == "request_access":  # 新增代码+ComputerUseMCP：处理授权申请工具；如果没有这行代码，request_access 会落入未知分支。
        report = request_computer_use_access(_normalize_request_access(safe_arguments))  # 新增代码+ComputerUseMCP：复用既有授权申请报告；如果没有这行代码，MCP 申请入口会和旧安全提示分裂。
        runtime.grants["last_request"] = report  # 新增代码+ComputerUseMCP：保存最近授权申请摘要；如果没有这行代码，list_granted_applications 看不到申请上下文。
        return _json_result(tool_name, True, report)  # 新增代码+ComputerUseMCP：返回授权申请报告；如果没有这行代码，模型拿不到请求结果。
    if tool_name == "list_granted_applications":  # 新增代码+ComputerUseMCP：处理授权查询工具；如果没有这行代码，该工具会被误判未知。
        return _json_result(tool_name, True, {"grants": runtime.grants, "grant_created": False})  # 新增代码+ComputerUseMCP：返回当前进程内授权摘要；如果没有这行代码，模型无法确认当前权限状态。
    if tool_name == "cursor_position":  # 新增代码+ClaudeCodeToolSurface：处理读取当前鼠标位置工具；如果没有这行代码，cursor_position 会错误进入 controller 动作。
        return _cursor_position_result(tool_name, safe_arguments)  # 新增代码+ClaudeCodeToolSurface：返回真实光标坐标或明确不可用原因；如果没有这行代码，模型无法得到位置反馈。
    if tool_name == "wait":  # 新增代码+ComputerUseMCP：处理等待工具；如果没有这行代码，wait 会错误进入 controller。
        seconds = max(0.0, min(float(safe_arguments.get("seconds", 1) or 0), 30.0))  # 新增代码+ComputerUseMCP：限制等待秒数；如果没有这行代码，模型可能让 server 长时间卡住。
        time.sleep(seconds)  # 新增代码+ComputerUseMCP：真实等待指定时间；如果没有这行代码，wait 不会给界面加载留时间。
        return _json_result(tool_name, True, {"waited_seconds": seconds, "reason": safe_arguments.get("reason", "")})  # 新增代码+ComputerUseMCP：返回等待结果；如果没有这行代码，模型不知道等待已完成。
    if tool_name == "read_clipboard":  # 新增代码+ClaudeCodeToolSurface：处理只读剪贴板工具；如果没有这行代码，read_clipboard 会落入旧混合 clipboard 或未知动作。
        return _json_result(tool_name, True, {"operation": "read", "text": runtime.clipboard_text, "backend": "mcp_memory_clipboard", "reason": safe_arguments.get("reason", "")})  # 新增代码+ClaudeCodeToolSurface：返回受控内存剪贴板文本；如果没有这行代码，剪贴板读写测试无法形成闭环。
    if tool_name == "write_clipboard":  # 新增代码+ClaudeCodeToolSurface：处理写剪贴板工具；如果没有这行代码，write_clipboard 无法产生后续可读状态。
        runtime.clipboard_text = str(safe_arguments.get("text", ""))  # 新增代码+ClaudeCodeToolSurface：保存受控内存剪贴板文本；如果没有这行代码，read_clipboard 读不回上次写入。
        return _json_result(tool_name, True, {"operation": "write", "text_length": len(runtime.clipboard_text), "backend": "mcp_memory_clipboard", "reason": safe_arguments.get("reason", "")})  # 新增代码+ClaudeCodeToolSurface：返回写入摘要而不回显全部文本；如果没有这行代码，模型无法确认写入长度。
    if tool_name == "clipboard":  # 新增代码+ComputerUseMCP：处理剪贴板工具；如果没有这行代码，clipboard 会错误进入 controller。
        operation = str(safe_arguments.get("operation", "")).strip().lower()  # 新增代码+ComputerUseMCP：读取剪贴板操作；如果没有这行代码，无法区分读写。
        if operation == "write":  # 新增代码+ComputerUseMCP：处理写入剪贴板；如果没有这行代码，写入请求没有效果。
            runtime.clipboard_text = str(safe_arguments.get("text", ""))  # 新增代码+ComputerUseMCP：保存模拟剪贴板文本；如果没有这行代码，read 无法读回上次 write。
            return _json_result(tool_name, True, {"operation": "write", "text_length": len(runtime.clipboard_text), "backend": "mcp_memory_clipboard"})  # 新增代码+ComputerUseMCP：返回写入摘要；如果没有这行代码，模型不知道写入长度。
        if operation == "read":  # 新增代码+ComputerUseMCP：处理读取剪贴板；如果没有这行代码，读取请求会被误报未知。
            return _json_result(tool_name, True, {"operation": "read", "text": runtime.clipboard_text, "backend": "mcp_memory_clipboard"})  # 新增代码+ComputerUseMCP：返回模拟剪贴板文本；如果没有这行代码，复制保存流程无法在测试中闭环。
        return _json_result(tool_name, False, {"reason": "clipboard.operation 必须是 read 或 write。"}, error_class="invalid_clipboard_operation")  # 新增代码+ComputerUseMCP：拒绝非法剪贴板操作；如果没有这行代码，错误参数会悄悄失败。
    if tool_name == "computer_batch":  # 新增代码+ComputerUseMCP：处理批量工具；如果没有这行代码，多步请求无法顺序执行。
        return _call_batch(safe_arguments, runtime)  # 新增代码+ComputerUseMCP：委托批量 helper；如果没有这行代码，批量逻辑会挤在主函数中。
    if tool_name in {"triple_click", "left_mouse_down", "left_mouse_up"}:  # 新增代码+ClaudeCodeToolSurface：处理暂未接入真实低层后端的预留工具；如果没有这行代码，预留工具会落到 controller 并返回不清晰错误。
        return _unsupported_result(tool_name, f"{tool_name} 已预留工具名，但当前 Computer Use 后端尚未接入真实低层事件实现。")  # 新增代码+ClaudeCodeToolSurface：明确告诉模型该工具暂不可用；如果没有这行代码，模型可能把失败误判成参数错误。
    controller_arguments = _controller_arguments_for_tool(tool_name, safe_arguments)  # 新增代码+ComputerUseMCP：把 MCP 工具映射到 controller action；如果没有这行代码，无法复用现有安全链。
    return _result_from_controller(runtime, tool_name, controller_arguments)  # 新增代码+ComputerUseMCP：调用 controller 并返回统一结果；如果没有这行代码，桌面动作不会执行。
# 新增代码+ComputerUseMCP：函数段结束，call_computer_use_mcp_tool 到此结束；如果没有这个边界说明，初学者不容易看出工具分发范围。


# 新增代码+ComputerUseMCP：函数段开始，_call_batch 顺序执行批量步骤；如果没有这段函数，computer_batch 无法复用单步分发和安全检查。
def _call_batch(arguments: dict[str, Any], runtime: ComputerUseMcpExecutionContext) -> dict[str, Any]:  # 新增代码+ComputerUseMCP：声明批量执行 helper；如果没有这行代码，batch 分支没有实现入口。
    steps = arguments.get("steps", [])  # 新增代码+ComputerUseMCP：读取步骤列表；如果没有这行代码，批量工具不知道要做什么。
    stop_on_error = bool(arguments.get("stop_on_error", True))  # 新增代码+ComputerUseMCP：读取失败是否停止；如果没有这行代码，批量失败策略不可控。
    if not isinstance(steps, list):  # 新增代码+ComputerUseMCP：校验 steps 必须是列表；如果没有这行代码，坏参数会在遍历时崩溃。
        return _json_result("computer_batch", False, {"reason": "steps 必须是数组。"}, error_class="invalid_batch_steps")  # 新增代码+ComputerUseMCP：返回参数错误；如果没有这行代码，模型无法修正 steps 类型。
    results: list[dict[str, Any]] = []  # 新增代码+ComputerUseMCP：准备保存每一步结果；如果没有这行代码，批量执行后无法汇总。
    for index, raw_step in enumerate(steps):  # 新增代码+ComputerUseMCP：按顺序遍历步骤；如果没有这行代码，batch 不会执行任何步骤。
        step = raw_step if isinstance(raw_step, dict) else {}  # 新增代码+ComputerUseMCP：防御非字典步骤；如果没有这行代码，坏步骤会触发属性错误。
        step_name = str(step.get("tool_name") or step.get("name") or "")  # 新增代码+ComputerUseMCP：读取步骤工具名；如果没有这行代码，batch 无法知道调用哪个工具。
        step_arguments = step.get("arguments", {}) if isinstance(step.get("arguments", {}), dict) else {}  # 新增代码+ComputerUseMCP：读取步骤参数；如果没有这行代码，参数会丢失或崩溃。
        step_result = call_computer_use_mcp_tool(step_name, step_arguments, runtime)  # 新增代码+ComputerUseMCP：复用单步执行入口；如果没有这行代码，batch 会绕开 shell 拒绝和 controller 映射。
        step_result["batch_index"] = index  # 新增代码+ComputerUseMCP：记录步骤序号；如果没有这行代码，失败时难以定位是哪一步。
        results.append(step_result)  # 新增代码+ComputerUseMCP：保存步骤结果；如果没有这行代码，最终报告没有明细。
        if stop_on_error and not bool(step_result.get("ok")):  # 新增代码+ComputerUseMCP：失败且要求停止时中断；如果没有这行代码，后续步骤可能在错误状态下继续动桌面。
            break  # 新增代码+ComputerUseMCP：停止批量循环；如果没有这行代码，stop_on_error 不会生效。
    return _json_result("computer_batch", all(bool(item.get("ok")) for item in results), {"results": results, "step_count": len(results)})  # 新增代码+ComputerUseMCP：返回批量汇总；如果没有这行代码，调用方拿不到整体成功状态。
# 新增代码+ComputerUseMCP：函数段结束，_call_batch 到此结束；如果没有这个边界说明，初学者不容易看出批量执行范围。
