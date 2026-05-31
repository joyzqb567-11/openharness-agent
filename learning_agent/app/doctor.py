"""MCP Doctor 应用入口，把诊断命令从巨型主文件中拆出来。"""  # 新增代码+AppSplit: 说明本模块承载 doctor 入口；若没有这行代码，用户排查 MCP 仍会回到 learning_agent.py。
from __future__ import annotations  # 新增代码+AppSplit: 允许类型注解延迟解析；若没有这行代码，类型提示在部分运行顺序下可能提前求值。

from pathlib import Path  # 新增代码+AppSplit: 使用 Path 标注工作区路径；若没有这行代码，Windows 路径处理语义不清楚。

try:  # 新增代码+AppSplit: 优先按包路径导入 MCP doctor 实现；若没有这行代码，包运行模式下 doctor 入口无法复用 mcp 层。
    from learning_agent.mcp.doctor import run_mcp_doctor as run_mcp_doctor_from_mcp  # 新增代码+AppSplit: 导入 mcp 层诊断函数；若没有这行代码，app.doctor 只是空壳不能诊断。
except ModuleNotFoundError as error:  # 新增代码+AppSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 模式可能找不到 learning_agent.mcp。
    if error.name not in {"learning_agent", "learning_agent.mcp", "learning_agent.mcp.doctor"}:  # 新增代码+AppSplit: 只允许目标路径缺失时 fallback；若没有这行代码，mcp 内部真实 bug 会被误吞。
        raise  # 新增代码+AppSplit: 重新抛出真实导入错误；若没有这行代码，诊断层问题会被伪装成脚本路径问题。
    from mcp.doctor import run_mcp_doctor as run_mcp_doctor_from_mcp  # 新增代码+AppSplit: 脚本模式从同目录 mcp 包导入；若没有这行代码，直接运行 learning_agent.py 时 doctor 会断开。


def run_mcp_doctor(workspace: str | Path) -> str:  # 新增代码+AppSplit: 提供 app 层 doctor 入口；若没有这行代码，CLI 无法从 app 层调用诊断。
    return run_mcp_doctor_from_mcp(workspace)  # 新增代码+AppSplit: 委托 mcp 层执行真实诊断；若没有这行代码，doctor 命令不会返回 MCP 启动和工具报告。
