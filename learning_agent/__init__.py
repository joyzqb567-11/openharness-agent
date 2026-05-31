"""learning_agent 包的公开导入门面。"""  # 修改代码+ToolSchemaSplit: 说明这里是包级公开 API；若没有这行代码，维护者不知道这些导出不是旧入口兼容层。
from learning_agent.core.agent import LearningAgent, ToolCallingFakeModel  # 修改代码+ToolSchemaSplit: 从核心模块直接导出 agent 主类和测试假模型；若没有这行代码，外部调用只能绕回旧 learning_agent.py。
from learning_agent.core.messages import ModelMessage, ToolCall  # 修改代码+ToolSchemaSplit: 从消息模块直接导出模型协议对象；若没有这行代码，测试和外部扩展无法构造统一消息。
from learning_agent.models.codex_cli import CodexCliChatModel  # 修改代码+ToolSchemaSplit: 从模型层直接导出 Codex CLI 适配器；若没有这行代码，codex provider 仍依赖旧入口转发。
from learning_agent.models.codex_oauth import CodexOAuthChatModel  # 修改代码+ToolSchemaSplit: 从模型层直接导出 Codex OAuth 适配器；若没有这行代码，OAuth provider 仍依赖旧入口转发。
from learning_agent.models.oauth_tokens import CodexOAuthTokens  # 修改代码+ToolSchemaSplit: 从 token 模块直接导出 OAuth token 数据结构；若没有这行代码，认证测试需要绕回旧入口。
from learning_agent.models.openai_chat import OpenAIChatModel  # 修改代码+ToolSchemaSplit: 从模型层直接导出 OpenAI-compatible 适配器；若没有这行代码，默认模型入口不清晰。

__all__ = [  # 修改代码+ToolSchemaSplit: 明确声明包级公开符号；若没有这行代码，from learning_agent import * 的边界不清晰。
    "CodexCliChatModel",  # 修改代码+ToolSchemaSplit: 对外暴露 Codex CLI 模型；若没有这行代码，旧调用方无法从包门面获得该模型。
    "CodexOAuthChatModel",  # 修改代码+ToolSchemaSplit: 对外暴露 Codex OAuth 模型；若没有这行代码，OAuth 调用方入口会丢失。
    "CodexOAuthTokens",  # 修改代码+ToolSchemaSplit: 对外暴露 OAuth token 数据结构；若没有这行代码，测试和学习入口会丢失。
    "LearningAgent",  # 修改代码+ToolSchemaSplit: 对外暴露 agent 主类；若没有这行代码，包级实例化入口会丢失。
    "ModelMessage",  # 修改代码+ToolSchemaSplit: 对外暴露模型消息结构；若没有这行代码，假模型测试无法构造响应。
    "OpenAIChatModel",  # 修改代码+ToolSchemaSplit: 对外暴露 OpenAI-compatible 模型；若没有这行代码，默认模型调用入口会丢失。
    "ToolCall",  # 修改代码+ToolSchemaSplit: 对外暴露工具调用结构；若没有这行代码，工具调用测试无法构造数据。
    "ToolCallingFakeModel",  # 修改代码+ToolSchemaSplit: 对外暴露测试假模型；若没有这行代码，离线工具循环测试入口会丢失。
]  # 修改代码+ToolSchemaSplit: 结束公开符号列表；若没有这行代码，Python 列表语法不完整。
