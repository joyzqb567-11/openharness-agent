"""Computer Use MCP v2 Windows host adapter 桥接。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode hostAdapter.ts；如果没有这行代码，宿主适配职责没有固定位置。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用类型；如果没有这行代码，host adapter 方法边界不清楚。


class WindowsHostAdapter:  # 新增代码+ComputerUseMcpV2：类段开始，提供最小 Windows host 适配器；如果没有这段类，独立 stdio server 没有默认 host 对象。
    def cursor_position(self) -> dict[str, int]:  # 新增代码+ComputerUseMcpV2：函数段开始，读取光标位置；如果没有这段函数，cursor_position 只能走 runtime fallback。
        from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.actions import cursor_position  # 新增代码+ComputerUseMcpV2：延迟导入动作实现避免循环；如果没有这行代码，默认 host 无法复用读取逻辑。
        result = cursor_position(type("_Context", (), {"host": None})())  # 新增代码+ComputerUseMcpV2：构造最小上下文调用 fallback；如果没有这行代码，host 自己没有读坐标实现。
        payload = result.get("payload", {}) if isinstance(result, dict) else {}  # 新增代码+ComputerUseMcpV2：读取 payload；如果没有这行代码，结果结构不同会崩溃。
        return {"x": int(payload.get("x", 0)), "y": int(payload.get("y", 0))}  # 新增代码+ComputerUseMcpV2：返回 x/y 坐标；如果没有这行代码，调用方拿不到稳定坐标。
    # 新增代码+ComputerUseMcpV2：函数段结束，cursor_position 到此结束；如果没有这个边界说明，用户不容易看出默认 host 坐标范围。

    def observe(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，返回最小观察摘要；如果没有这段函数，独立 server observe 会报告无 host。
        return {"captured": False, "reason": "default_windows_host_adapter_has_no_screenshot_backend", "arguments": dict(arguments)}  # 新增代码+ComputerUseMcpV2：返回无截图后端摘要；如果没有这行代码，observe 无法稳定运行。
    # 新增代码+ComputerUseMcpV2：函数段结束，observe 到此结束；如果没有这个边界说明，用户不容易看出默认观察范围。
# 新增代码+ComputerUseMcpV2：类段结束，WindowsHostAdapter 到此结束；如果没有这个边界说明，用户不容易看出 host adapter 范围。

