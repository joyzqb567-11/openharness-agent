"""Computer Use MCP v2 统一运行时分发。"""  # 新增代码+ComputerUseMcpV2：说明本文件是 stdio 和 agent-side 共用执行入口；如果没有这行代码，两个入口可能分裂。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，循环导入更容易失败。

import time  # 新增代码+ComputerUseMcpV2：导入时间模块用于 wait；如果没有这行代码，wait 工具无法真正等待。
from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，runtime 参数边界不清楚。

from .actions import perform_action  # 新增代码+ComputerUseMcpV2：导入鼠标键盘动作；如果没有这行代码，动作类工具无法执行。
from .applications import open_application  # 新增代码+ComputerUseMcpV2：导入应用启动；如果没有这行代码，open_application 无法分发。
from .batch import run_batch  # 新增代码+ComputerUseMcpV2：导入批量执行；如果没有这行代码，computer_batch 无法执行。
from .build_tools import COMPUTER_USE_MCP_TOOL_NAMES, FORBIDDEN_LEGACY_RAW_TOOL_NAMES  # 新增代码+ComputerUseMcpV2：导入允许和禁止工具清单；如果没有这行代码，runtime 无法做硬边界判断。
from .clipboard import read_clipboard, write_clipboard  # 新增代码+ComputerUseMcpV2：导入剪贴板读写；如果没有这行代码，剪贴板工具无法执行。
from .errors import error_result  # 新增代码+ComputerUseMcpV2：导入统一失败结果；如果没有这行代码，runtime 失败格式会漂移。
from .observation import observe  # 新增代码+ComputerUseMcpV2：导入观察工具；如果没有这行代码，observe/screenshot 无法执行。
from .permissions import list_granted_applications, request_access  # 新增代码+ComputerUseMcpV2：导入权限工具；如果没有这行代码，授权类工具无法执行。
from .result_blocks import success_result  # 新增代码+ComputerUseMcpV2：导入统一成功结果；如果没有这行代码，wait 等工具会手写结果。
from .telemetry import emit_acceptance, record_trace  # 新增代码+ComputerUseMcpV2：导入 trace 和验收事件；如果没有这行代码，执行证据链不会写入。
from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入上下文并在本模块重导出；如果没有这行代码，测试和 wrapper 无法构造上下文。


def normalize_tool_name(tool_name: str) -> str:  # 新增代码+ComputerUseMcpV2：函数段开始，统一处理前缀工具名；如果没有这段函数，mcp__computer-use__xxx 和 xxx 会分裂。
    return str(tool_name or "").strip().removeprefix("mcp__computer-use__")  # 新增代码+ComputerUseMcpV2：去掉 registry 前缀；如果没有这行代码，agent-side 调用会被误判未知。
# 新增代码+ComputerUseMcpV2：函数段结束，normalize_tool_name 到此结束；如果没有这个边界说明，用户不容易看出命名规范范围。


def dispatch_computer_use_mcp_v2_tool(tool_name: str, arguments: dict[str, Any] | None, context: ComputerUseMcpV2Context | None = None) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，执行一个 v2 MCP 工具；如果没有这段函数，server 和 agent-side wrapper 没有统一入口。
    runtime_context = context or ComputerUseMcpV2Context()  # 新增代码+ComputerUseMcpV2：缺省创建上下文；如果没有这行代码，独立 selftest 调用会失败。
    raw_name = normalize_tool_name(tool_name)  # 新增代码+ComputerUseMcpV2：规范工具名；如果没有这行代码，前缀名无法执行。
    safe_arguments = dict(arguments or {})  # 新增代码+ComputerUseMcpV2：复制参数避免污染调用方对象；如果没有这行代码，batch 或工具可能改写原始输入。
    record_trace(runtime_context, "tool_started", {"tool_name": raw_name, "arguments_keys": sorted(safe_arguments.keys())})  # 新增代码+ComputerUseMcpV2：记录开始事件；如果没有这行代码，trace 无法证明 v2 被调用。
    if raw_name in FORBIDDEN_LEGACY_RAW_TOOL_NAMES:  # 新增代码+ComputerUseMcpV2：硬拒绝旧接口和蓝图外接口；如果没有这行代码，隐藏工具可被直接调用。
        result = error_result(raw_name, f"legacy_or_forbidden_tool:{raw_name}", error_class="legacy_tool_forbidden")  # 新增代码+ComputerUseMcpV2：构造 legacy 拒绝；如果没有这行代码，模型不知道为什么被拒绝。
    elif raw_name not in COMPUTER_USE_MCP_TOOL_NAMES:  # 新增代码+ComputerUseMcpV2：检查是否属于 v2 清单；如果没有这行代码，未知工具可能落入动作层。
        result = error_result(raw_name, f"unknown_computer_use_mcp_v2_tool:{raw_name}", error_class="unknown_tool")  # 新增代码+ComputerUseMcpV2：构造未知工具拒绝；如果没有这行代码，未知调用可能假成功。
    elif raw_name == "request_access":  # 新增代码+ComputerUseMcpV2：分发授权申请；如果没有这行代码，request_access 无法执行。
        result = request_access(runtime_context, safe_arguments)  # 新增代码+ComputerUseMcpV2：执行授权申请；如果没有这行代码，权限回调不会被调用。
    elif raw_name == "list_granted_applications":  # 新增代码+ComputerUseMcpV2：分发授权查询；如果没有这行代码，授权状态无法查看。
        result = list_granted_applications(runtime_context)  # 新增代码+ComputerUseMcpV2：执行授权查询；如果没有这行代码，模型拿不到 grant 摘要。
    elif raw_name in {"observe", "screenshot", "zoom"}:  # 修改代码+ClaudeCodeZoom：把 zoom 纳入只读观察类分发；如果没有这行代码，zoom 虽标 readOnly 但运行时仍像动作工具一样缺观察记录。
        result = observe(runtime_context, raw_name, safe_arguments)  # 新增代码+ComputerUseMcpV2：执行观察；如果没有这行代码，主循环拿不到桌面状态。
    elif raw_name == "wait":  # 新增代码+ComputerUseMcpV2：分发等待工具；如果没有这行代码，wait 会被误判未知。
        seconds = max(0.0, min(float(safe_arguments.get("seconds", 1) or 0), 30.0))  # 新增代码+ComputerUseMcpV2：限制等待时长；如果没有这行代码，模型可能让 server 长时间卡住。
        time.sleep(seconds)  # 新增代码+ComputerUseMcpV2：执行等待；如果没有这行代码，wait 不会给界面加载时间。
        result = success_result("wait", {"waited_seconds": seconds})  # 新增代码+ComputerUseMcpV2：返回等待摘要；如果没有这行代码，模型不知道等待完成。
    elif raw_name == "read_clipboard":  # 新增代码+ComputerUseMcpV2：分发读剪贴板；如果没有这行代码，read_clipboard 无法执行。
        result = read_clipboard(runtime_context)  # 新增代码+ComputerUseMcpV2：执行剪贴板读取；如果没有这行代码，模型拿不到剪贴板内容。
    elif raw_name == "write_clipboard":  # 新增代码+ComputerUseMcpV2：分发写剪贴板；如果没有这行代码，write_clipboard 无法执行。
        result = write_clipboard(runtime_context, str(safe_arguments.get("text", "")))  # 新增代码+ComputerUseMcpV2：执行剪贴板写入；如果没有这行代码，后续读取不会变化。
    elif raw_name == "open_application":  # 新增代码+ComputerUseMcpV2：分发应用启动；如果没有这行代码，open_application 无法执行。
        result = open_application(runtime_context, safe_arguments)  # 新增代码+ComputerUseMcpV2：执行应用启动；如果没有这行代码，目标应用不会打开。
    elif raw_name == "computer_batch":  # 新增代码+ComputerUseMcpV2：分发批量工具；如果没有这行代码，computer_batch 无法执行。
        result = run_batch(runtime_context, safe_arguments, dispatch_computer_use_mcp_v2_tool)  # 新增代码+ComputerUseMcpV2：执行批量动作；如果没有这行代码，多步任务无法顺序执行。
    else:  # 新增代码+ComputerUseMcpV2：剩余都是鼠标键盘动作；如果没有这行代码，动作工具无法进入执行层。
        result = perform_action(runtime_context, raw_name, safe_arguments)  # 新增代码+ComputerUseMcpV2：执行原子动作；如果没有这行代码，click/type/key 等不会运行。
    record_trace(runtime_context, "tool_completed", {"tool_name": raw_name, "ok": bool(result.get("ok")), "error_class": result.get("error_class", "")})  # 新增代码+ComputerUseMcpV2：记录完成事件；如果没有这行代码，trace 看不到结果。
    emit_acceptance(runtime_context, "computer_use_mcp_v2_tool", {"tool_name": raw_name, "ok": bool(result.get("ok"))})  # 新增代码+ComputerUseMcpV2：发送验收事件；如果没有这行代码，真实终端验收难以区分 v2 动作。
    return result  # 新增代码+ComputerUseMcpV2：返回工具结果；如果没有这行代码，调用方拿不到执行输出。
# 新增代码+ComputerUseMcpV2：函数段结束，dispatch_computer_use_mcp_v2_tool 到此结束；如果没有这个边界说明，用户不容易看出 runtime 分发范围。
