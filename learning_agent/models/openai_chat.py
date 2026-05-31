"""OpenAI-compatible 模型适配器导出。"""  # 新增代码+ModelsSplit: 给默认 OpenAI 模型提供稳定模块路径；若没有这个文件，外部只能继续从主入口导入。

from .adapters import OpenAIChatModel  # 新增代码+ModelsSplit: 从集中适配器实现导出 OpenAIChatModel；若没有这行代码，阶段 3 计划要求的模块路径不可用。

__all__ = ["OpenAIChatModel"]  # 新增代码+ModelsSplit: 明确本模块公开对象；若没有这行代码，后续自动文档和索引不容易判断导出边界。
