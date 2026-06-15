"""core 包承载 agent 主循环、消息结构和配置解析的轻量门面。"""  # 修改代码+LegacyEntryCut: 说明 core 包顶层不会立即导入 agent 主实现；若没有这行代码，维护者可能重新制造 app/core 循环依赖。
from __future__ import annotations  # 修改代码+LegacyEntryCut: 延迟解析类型注解；若没有这行代码，惰性导出类型以后更容易受导入顺序影响。

from typing import Any  # 修改代码+LegacyEntryCut: __getattr__ 需要返回不同类型的公开对象；若没有这行代码，惰性门面类型边界不清楚。

try:  # 修改代码+LegacyEntryCut: 优先按正式包路径导入轻量配置和消息对象；若没有这行代码，正常包导入无法从 core 顶层读取基础类型。
    from learning_agent.core.config import AgentRuntimeConfig, MainArgs  # 修改代码+LegacyEntryCut: 导出运行配置数据结构；若没有这行代码，配置层公共入口仍要绕到子模块。
    from learning_agent.core.messages import ModelMessage, ToolCall  # 修改代码+LegacyEntryCut: 导出模型消息和工具调用结构；若没有这行代码，消息结构入口会分散。
except ModuleNotFoundError as error:  # 修改代码+LegacyEntryCut: 捕获脚本模式下包路径不可用的情况；若没有这行代码，本地 MCP server 直接运行会导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.config", "learning_agent.core.messages"}:  # 修改代码+LegacyEntryCut: 只允许包路径缺失时 fallback；若没有这行代码，core 内部真实 bug 会被误吞。
        raise  # 修改代码+LegacyEntryCut: 非路径导入错误继续抛出；若没有这行代码，真实问题会被伪装成脚本模式。
    from core.config import AgentRuntimeConfig, MainArgs  # 修改代码+LegacyEntryCut: 脚本模式下导出运行配置数据结构；若没有这行代码，直接运行时配置类型会断开。
    from core.messages import ModelMessage, ToolCall  # 修改代码+LegacyEntryCut: 脚本模式下导出消息结构；若没有这行代码，直接运行时模型消息类型会断开。


def __getattr__(name: str) -> Any:  # 修改代码+LegacyEntryCut: 惰性导出重型 agent 对象；若没有这行代码，from learning_agent.core import LearningAgent 会失效或触发循环导入。
    if name in {"LearningAgent", "ToolCallingFakeModel"}:  # 修改代码+LegacyEntryCut: 只对主 agent 和假模型启用惰性加载；若没有这行代码，未知名字也可能被错误吞掉。
        try:  # 修改代码+LegacyEntryCut: 优先按正式包路径导入核心实现；若没有这行代码，包运行模式无法读取主 agent。
            from learning_agent.core.agent import LearningAgent  # 修改代码+AgentPyPhaseKFakeModel: 调用时才导入主 agent 类；若没有这行代码，core 包门面无法返回 LearningAgent。
            from learning_agent.models.fake import ToolCallingFakeModel  # 修改代码+AgentPyPhaseKFakeModel: 调用时从模型层导入测试假模型；若没有这行代码，core 包门面会重新依赖 agent.py 的假模型实现。
        except ModuleNotFoundError as error:  # 修改代码+LegacyEntryCut: 捕获脚本模式下包路径不可用的情况；若没有这行代码，直接运行时 core 顶层惰性导入可能失败。
            if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.agent", "learning_agent.models", "learning_agent.models.fake"}:  # 修改代码+AgentPyPhaseKFakeModel: 只允许目标路径缺失时 fallback，并覆盖新的假模型模块；若没有这行代码，models.fake 的脚本模式兼容会失败或真实 bug 被误吞。
                raise  # 修改代码+LegacyEntryCut: 重新抛出真实导入错误；若没有这行代码，排查核心实现问题会更困难。
            from core.agent import LearningAgent  # 修改代码+AgentPyPhaseKFakeModel: 脚本模式下从同目录 core 包导入主 agent；若没有这行代码，MCP server 直接运行会找不到核心类。
            from models.fake import ToolCallingFakeModel  # 修改代码+AgentPyPhaseKFakeModel: 脚本模式下从模型层导入测试假模型；若没有这行代码，直接运行入口无法继续兼容假模型。
        return {"LearningAgent": LearningAgent, "ToolCallingFakeModel": ToolCallingFakeModel}[name]  # 修改代码+LegacyEntryCut: 按请求名字返回对应对象；若没有这行代码，惰性导入无法把名字映射到对象。
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")  # 修改代码+LegacyEntryCut: 对未知属性保持标准 Python 错误；若没有这行代码，拼错名字会被静默忽略。


__all__ = [  # 修改代码+LegacyEntryCut: 明确 core 包对外稳定导出的符号；若没有这行代码，star import 的边界不清楚。
    "AgentRuntimeConfig",  # 修改代码+LegacyEntryCut: 允许外部从 core 包读取运行配置类型；若没有这行代码，配置对象不在公共索引里。
    "LearningAgent",  # 修改代码+LegacyEntryCut: 允许外部从 core 包惰性读取主 agent 类；若没有这行代码，修 bug 时仍要找子模块路径。
    "MainArgs",  # 修改代码+LegacyEntryCut: 允许外部从 core 包读取 CLI 参数类型；若没有这行代码，入口解析类型不在公共索引里。
    "ModelMessage",  # 修改代码+LegacyEntryCut: 允许外部从 core 包读取模型消息类型；若没有这行代码，测试和模型层需要绕远路导入。
    "ToolCall",  # 修改代码+LegacyEntryCut: 允许外部从 core 包读取工具调用类型；若没有这行代码，工具调用结构不在公共索引里。
    "ToolCallingFakeModel",  # 修改代码+LegacyEntryCut: 允许测试从 core 包惰性读取假模型；若没有这行代码，测试仍要找子模块路径。
]  # 修改代码+LegacyEntryCut: core 包导出列表结束；若没有这行代码，Python 列表语法不完整。
