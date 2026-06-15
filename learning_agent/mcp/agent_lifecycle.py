"""MCP lifecycle 与 LearningAgent 状态衔接。"""  # 新增代码+AgentPyPhaseHMcpToolRuntime: 把 MCP 通知刷新从 agent.py 移到 MCP 层；若没有这个文件，主类会继续承载 MCP lifecycle 细节。

from __future__ import annotations  # 新增代码+AgentPyPhaseHMcpToolRuntime: 延迟解析类型注解，降低脚本模式导入顺序风险；若没有这行代码，后续类型扩展可能更脆弱。

from typing import Any  # 新增代码+AgentPyPhaseHMcpToolRuntime: 用 Any 表示传入的 agent duck type；若没有这行代码，本模块会为了类型注解反向导入 LearningAgent。


def refresh_mcp_lifecycle_notifications(agent: Any) -> None:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段开始，消费 MCP list_changed 通知并刷新工具目录缓存；若没有这段函数，外部 MCP 工具变化不会传导到 tool_search 和工具池。
    if not agent.mcp_tools_enabled:  # 新增代码+AgentPyPhaseHMcpToolRuntime: MCP 未启用时不尝试刷新外部目录；若没有这行代码，用户拒绝或启动失败后仍可能触碰外部 client。
        return  # 新增代码+AgentPyPhaseHMcpToolRuntime: 直接跳过刷新；若没有这行代码，后续会访问不可用 registry 状态。
    refresh_method = getattr(agent.mcp_tool_registry, "refresh_from_notifications", None)  # 新增代码+AgentPyPhaseHMcpToolRuntime: 读取 registry 的生命周期刷新入口并兼容旧测试替身；若没有这行代码，缺少方法的 registry 会崩溃。
    if not callable(refresh_method):  # 新增代码+AgentPyPhaseHMcpToolRuntime: 旧 registry 或测试替身不支持通知刷新时跳过；若没有这行代码，兼容性会被破坏。
        return  # 新增代码+AgentPyPhaseHMcpToolRuntime: 没有刷新能力就保持当前 catalog；若没有这行代码，普通无 MCP 场景会失败。
    try:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 捕获 lifecycle refresh 失败并转成 agent 状态；若没有这行代码，单次通知处理异常会中断工具搜索。
        summary = refresh_method()  # 新增代码+AgentPyPhaseHMcpToolRuntime: 消费 pending notifications 并让 registry 必要时重建 tools；若没有这行代码，ToolSearch 仍使用旧工具目录。
    except Exception as error:  # 新增代码+AgentPyPhaseHMcpToolRuntime: 处理外部 server 或 registry 刷新异常；若没有这行代码，用户会看到 Python traceback 或 agent 构造外的崩溃。
        agent.mcp_start_error = f"MCP lifecycle refresh 失败：{error}"  # 新增代码+AgentPyPhaseHMcpToolRuntime: 保存可读失败原因；若没有这行代码，后续 MCP 不可用状态缺少解释。
        return  # 新增代码+AgentPyPhaseHMcpToolRuntime: 刷新失败时保留旧 catalog，避免一次通知错误摧毁本轮工具池；若没有这行代码，异常会继续冒泡。
    if isinstance(summary, dict) and summary.get("refreshed_tools"):  # 新增代码+AgentPyPhaseHMcpToolRuntime: 只有 tools/list_changed 真的重建 registry 时才清 agent catalog cache；若没有这行代码，每轮工具查询都会丢失 runtime gate 修改。
        agent._tool_catalog_cache = None  # 新增代码+AgentPyPhaseHMcpToolRuntime: 清掉 AgentTool 目录缓存，让下一次查询读取最新 MCP schema；若没有这行代码，ToolSearch 会继续返回刷新前的旧工具。
# 新增代码+AgentPyPhaseHMcpToolRuntime: 函数段结束，refresh_mcp_lifecycle_notifications 到此结束；若没有这个边界说明，用户不容易看出 MCP lifecycle 范围。
