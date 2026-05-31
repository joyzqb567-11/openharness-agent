"""模型接口定义。"""  # 新增代码+ModelsSplit: 这个文件只放模型共同接口；若没有这个文件，模型边界仍会散落在主入口。

from __future__ import annotations  # 新增代码+ModelsSplit: 延迟解析类型注解；若没有这行代码，前向引用和脚本模式导入更容易受顺序影响。

from typing import Any, Protocol  # 新增代码+ModelsSplit: 导入通用 JSON 类型和协议基类；若没有这行代码，ChatModel 无法声明标准 chat 接口。

try:  # 新增代码+ModelsSplit: 包运行模式下从 core.messages 读取统一消息结构；若没有这行代码，模型接口会重新定义消息类型。
    from learning_agent.core.messages import ModelMessage  # 新增代码+ModelsSplit: 导入模型返回消息对象；若没有这行代码，ChatModel.chat 无法表达返回值类型。
except ModuleNotFoundError as error:  # 新增代码+ModelsSplit: 捕获直接运行脚本时包名不可用的情况；若没有这行代码，bat 入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.core", "learning_agent.core.messages"}:  # 新增代码+ModelsSplit: 只允许路径缺失时 fallback；若没有这行代码，core 内部真实错误会被误吞。
        raise  # 新增代码+ModelsSplit: 重新抛出真实导入错误；若没有这行代码，排查模型接口问题会很困难。
    from core.messages import ModelMessage  # 新增代码+ModelsSplit: 脚本运行模式下从同目录 core 包导入消息对象；若没有这行代码，直接执行 learning_agent.py 会找不到 ModelMessage。


class ChatModel(Protocol):  # 新增代码+ModelsSplit: 定义所有模型适配器必须实现的最小接口；若没有这行代码，LearningAgent 无法用统一方式调用不同模型。
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelMessage:  # 新增代码+ModelsSplit: 声明模型接收消息和工具列表并返回统一消息；若没有这行代码，模型替换会缺少稳定契约。
        ...  # 新增代码+ModelsSplit: Protocol 只声明接口不实现逻辑；若没有这行代码，Python 类体为空会语法错误。
