"""Tool Executor v2 的权限决策对象和默认决策函数。"""  # 新增代码+Stage15E: 把权限输出统一成结构化对象；若没有这个文件，执行器只能靠散乱字符串判断权限。

from __future__ import annotations  # 新增代码+Stage15E: 延迟解析类型注解；若没有这行代码，跨模块类型引用更容易受顺序影响。

from dataclasses import dataclass  # 新增代码+Stage15E: 快速定义权限决策对象；若没有这行代码，需要手写重复初始化逻辑。
from typing import Any  # 新增代码+Stage15E: agent、tool_call 和 catalog_tool 都来自不同层；若没有这行代码，类型边界不清楚。


@dataclass(frozen=True)  # 新增代码+Stage15E: 让权限决策不可变；若没有这行代码，后续代码可能误改已记录的决策。
class ToolPermissionDecision:  # 新增代码+Stage15E: 表示一次工具权限判断结果；若没有这个类，执行器无法稳定表达 allow/deny/ask/auto_allow。
    status: str  # 新增代码+Stage15E: 保存权限状态，例如 allow、deny、ask、auto_allow；若没有这行代码，调用方不知道决策类型。
    allowed: bool  # 新增代码+Stage15E: 保存是否允许继续执行；若没有这行代码，执行器无法决定是否调用工具。
    reason: str = ""  # 新增代码+Stage15E: 保存可读原因；若没有这行代码，审计事件无法解释为什么允许或拒绝。


def decide_tool_permission(agent: Any, tool_call: Any, catalog_tool: Any) -> ToolPermissionDecision:  # 新增代码+Stage15E: 根据工具元数据生成统一权限决策；若没有这行代码，执行器会继续把权限逻辑写在分发流程里。
    permission_mode = str(getattr(catalog_tool, "permission_mode", "ask") or "ask")  # 新增代码+Stage15E: 从 AgentTool 读取权限模式并兜底 ask；若没有这行代码，未知工具可能没有保守默认。
    if permission_mode == "auto_allow":  # 新增代码+Stage15E: 处理明确自动允许的只读工具；若没有这行代码，read 等安全工具会产生不必要拦截。
        return ToolPermissionDecision(status="auto_allow", allowed=True, reason="tool metadata marked auto_allow")  # 新增代码+Stage15E: 返回自动允许决策；若没有这行代码，执行器无法继续执行安全工具。
    if permission_mode == "allow":  # 新增代码+Stage15E: 处理显式允许模式；若没有这行代码，后续策略无法表达无需询问但非自动的工具。
        return ToolPermissionDecision(status="allow", allowed=True, reason="tool metadata marked allow")  # 新增代码+Stage15E: 返回允许决策；若没有这行代码，allow 模式无法生效。
    if permission_mode == "deny":  # 新增代码+Stage15E: 处理显式拒绝模式；若没有这行代码，权限拒绝可能只被记录但不阻断。
        return ToolPermissionDecision(status="deny", allowed=False, reason="tool metadata marked deny")  # 新增代码+Stage15E: 返回拒绝决策；若没有这行代码，危险工具无法被统一阻断。
    if permission_mode == "ask":  # 新增代码+Stage15E: 处理默认询问模式；若没有这行代码，未知工具无法进入保守权限通道。
        return ToolPermissionDecision(status="ask", allowed=True, reason="tool metadata requests existing tool-specific permission flow")  # 新增代码+Stage15E: 暂由既有工具 handler 负责真正询问；若没有这行代码，write/edit/bash 会被新增层重复弹窗。
    return ToolPermissionDecision(status="deny", allowed=False, reason=f"unknown permission_mode={permission_mode}")  # 新增代码+Stage15E: 未知权限模式保守拒绝；若没有这行代码，拼写错误可能绕过权限层。
