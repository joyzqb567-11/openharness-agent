"""应用入口层包，使用惰性导入避免 CLI 与 core 循环依赖。"""  # 修改代码+LegacyEntryCut: 说明 app 包不在导入时加载重模块；若没有这行代码，维护者可能重新加入顶层循环导入。
from __future__ import annotations  # 修改代码+LegacyEntryCut: 延迟解析类型注解；若没有这行代码，入口包装函数的类型以后更容易受导入顺序影响。

from typing import Any  # 修改代码+LegacyEntryCut: main 包装函数需要接收任意 CLI 参数；若没有这行代码，惰性门面的类型边界不清楚。


def main(*args: Any, **kwargs: Any) -> None:  # 修改代码+LegacyEntryCut: 惰性转发到 app.cli.main；若没有这行代码，from learning_agent.app import main 会重新触发循环导入。
    try:  # 修改代码+LegacyEntryCut: 优先按正式包路径导入 CLI 主入口；若没有这行代码，包运行模式没有 app 主函数。
        from learning_agent.app.cli import main as app_main  # 修改代码+LegacyEntryCut: 在调用时才导入 CLI；若没有这行代码，导入 app 包本身会加载过多依赖。
    except ModuleNotFoundError as error:  # 修改代码+LegacyEntryCut: 捕获脚本模式下包路径暂不可用的情况；若没有这行代码，直接运行时 app 包可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.app", "learning_agent.app.cli"}:  # 修改代码+LegacyEntryCut: 只允许目标路径缺失时 fallback；若没有这行代码，CLI 内部真实 bug 会被误吞。
            raise  # 修改代码+LegacyEntryCut: 重新抛出真实导入错误；若没有这行代码，排查 app 层问题会更困难。
        from app.cli import main as app_main  # 修改代码+LegacyEntryCut: 脚本模式下从同目录 app 包导入 CLI；若没有这行代码，直接运行时没有 app 主函数。
    app_main(*args, **kwargs)  # 修改代码+LegacyEntryCut: 转发调用参数给 CLI 主入口；若没有这行代码，外部传入 argv 或依赖注入不会生效。


def run_mcp_doctor(workspace: str) -> str:  # 修改代码+LegacyEntryCut: 惰性转发到 app.doctor.run_mcp_doctor；若没有这行代码，app 包顶层 doctor 会继续提前加载 MCP。
    try:  # 修改代码+LegacyEntryCut: 优先按正式包路径导入 doctor 入口；若没有这行代码，包运行模式没有诊断入口。
        from learning_agent.app.doctor import run_mcp_doctor as app_run_mcp_doctor  # 修改代码+LegacyEntryCut: 在调用时才导入 doctor；若没有这行代码，导入 app 包本身会加载 MCP 依赖。
    except ModuleNotFoundError as error:  # 修改代码+LegacyEntryCut: 捕获脚本模式下包路径暂不可用的情况；若没有这行代码，直接运行时 doctor 入口可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.app", "learning_agent.app.doctor"}:  # 修改代码+LegacyEntryCut: 只允许目标路径缺失时 fallback；若没有这行代码，doctor 内部真实 bug 会被误吞。
            raise  # 修改代码+LegacyEntryCut: 重新抛出真实导入错误；若没有这行代码，MCP 诊断问题会被隐藏。
        from app.doctor import run_mcp_doctor as app_run_mcp_doctor  # 修改代码+LegacyEntryCut: 脚本模式下从同目录 app 包导入 doctor；若没有这行代码，直接运行时没有诊断入口。
    return app_run_mcp_doctor(workspace)  # 修改代码+LegacyEntryCut: 返回 doctor 报告文本；若没有这行代码，调用方拿不到诊断结果。


__all__ = [  # 修改代码+LegacyEntryCut: 明确 app 包公开 API；若没有这行代码，架构索引无法快速列出入口层能力。
    "main",  # 修改代码+LegacyEntryCut: 公开惰性 CLI 主入口；若没有这行代码，from learning_agent.app import * 不会包含启动入口。
    "run_mcp_doctor",  # 修改代码+LegacyEntryCut: 公开惰性 MCP 诊断入口；若没有这行代码，doctor 能力不会被包顶层暴露。
]  # 修改代码+LegacyEntryCut: 结束公开 API 列表；若没有这行代码，Python 列表语法不完整。
