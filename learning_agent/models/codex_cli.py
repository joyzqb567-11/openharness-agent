"""Codex CLI 模型适配器导出。"""  # 新增代码+ModelsSplit: 给 Codex CLI 桥接模型提供稳定模块路径；若没有这个文件，测试注入类型仍会绑在主入口。

from .adapters import CodexCliChatModel, RunCodexFunction  # 新增代码+ModelsSplit: 从集中适配器实现导出 CLI 模型和运行函数类型；若没有这行代码，阶段 3 计划要求的模块路径不可用。

__all__ = ["CodexCliChatModel", "RunCodexFunction"]  # 新增代码+ModelsSplit: 明确本模块公开对象；若没有这行代码，后续修 CLI 模型时边界不清楚。
