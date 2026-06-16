"""Computer Use MCP v2 观察工具。"""  # 新增代码+ComputerUseMcpV2：说明本文件管理 observe/screenshot；如果没有这行代码，观察逻辑会混入动作执行。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型引用可能提前求值。

from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，观察结果边界不清楚。

from .errors import error_result  # 新增代码+ClaudeCodeZoom: 导入统一失败结果用于 zoom 无 host 场景；如果没有这一行，zoom 缺宿主时只能伪装成普通 captured=false。
from .result_blocks import success_result  # 新增代码+ComputerUseMcpV2：导入统一成功结果；如果没有这行代码，观察输出会漂移。
from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入上下文；如果没有这行代码，host 观察能力无法注入。


def observe(context: ComputerUseMcpV2Context, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，执行 observe/screenshot；如果没有这段函数，模型无法获取桌面状态。
    host_method_name = "zoom" if tool_name == "zoom" else "observe"  # 新增代码+ClaudeCodeZoom: zoom 仍是观察语义但必须调用宿主 zoom 能力；如果没有这一行，局部放大会退化成普通 observe。
    host_method = getattr(context.host, host_method_name, None) if context.host is not None else None  # 修改代码+ClaudeCodeZoom: 按工具选择 host.observe 或 host.zoom；如果没有这行代码，zoom 无法保留独立宿主接口。
    if tool_name == "zoom" and not callable(host_method):  # 新增代码+ClaudeCodeZoom: zoom 缺少宿主实现时给明确失败；如果没有这一行，局部放大会被当作普通无截图观察成功。
        result = error_result("zoom", "zoom_unavailable_without_host", error_class="host_unavailable")  # 新增代码+ClaudeCodeZoom: 构造 host 不可用错误；如果没有这一行，模型无法判断需要 Windows host 才能缩放。
        result["payload"] = {"requires_host": True, "desktop_action_performed": False}  # 新增代码+ClaudeCodeZoom: 明确 zoom 没有执行桌面副作用；如果没有这一行，验收可能误以为发生了动作。
        return result  # 新增代码+ClaudeCodeZoom: 返回 zoom 无 host 错误；如果没有这一行，函数会继续走普通 observe 兜底。
    raw_payload = host_method(arguments) if callable(host_method) else {"captured": False, "reason": "no_host_observer_bound"}  # 修改代码+ClaudeCodeZoom：先保存 host 原始观察或 zoom 结果；如果没有这一行，非字典结果会再次被 dict(...) 误转并崩溃。
    payload = dict(raw_payload) if isinstance(raw_payload, dict) else {"captured": False, "reason": "host_observer_returned_non_dict", "host_result_type": type(raw_payload).__name__}  # 修改代码+ComputerUseMcpV2HostAdapter：只接受字典结果并给非字典结果稳定摘要；如果没有这一行，旧 controller 对象会让 observe 输出非 JSON 错误。
    if callable(context.record_observation):  # 新增代码+ComputerUseMcpV2：检查是否存在 observation 回调；如果没有这行代码，None 回调会导致异常。
        context.record_observation("computer_use_mcp_v2_observe", payload)  # 新增代码+ComputerUseMcpV2：把观察证据写回 agent；如果没有这行代码，主循环看不到观察结果。
    return success_result(tool_name, payload, legacy_adapter_used=bool(payload.get("legacy_adapter_used", False)))  # 修改代码+ComputerUseMcpV2HostAdapter：返回观察摘要并透出旧 adapter 来源；如果没有这一行，observe 即使复用旧截图链也会被顶层误判。
# 新增代码+ComputerUseMcpV2：函数段结束，observe 到此结束；如果没有这个边界说明，用户不容易看出观察范围。
