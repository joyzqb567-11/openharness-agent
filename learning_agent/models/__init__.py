# 新增代码+模块化重构: models 包用于承载 OpenAI、Codex CLI 和 Codex OAuth 模型适配器；如果没有这个包，模型调用问题仍然需要翻 learning_agent.py。
from .base import ChatModel  # 修改代码+ModelsSplit: 导出模型接口；若没有这行代码，调用方无法从 models 包顶层拿到统一模型协议。
from .codex_cli import CodexCliChatModel, RunCodexFunction  # 修改代码+ModelsSplit: 导出 Codex CLI 模型；若没有这行代码，CLI 桥接入口不方便复用。
from .codex_oauth import CodexOAuthChatModel, LoginCallbackFunction, PostJsonFunction  # 修改代码+ModelsSplit: 导出 OAuth/API 模型；若没有这行代码，OAuth 入口不方便复用。
from .oauth_tokens import CodexOAuthTokenStore, CodexOAuthTokens  # 修改代码+ModelsSplit: 导出 token 数据和存储；若没有这行代码，token 问题无法从包顶层定位。
from .openai_chat import OpenAIChatModel  # 修改代码+ModelsSplit: 导出默认 OpenAI-compatible 模型；若没有这行代码，默认模型入口不方便复用。

__all__ = [  # 修改代码+ModelsSplit: 明确 models 包顶层公开对象；若没有这行代码，后续架构索引无法快速列出模型层 API。
    "ChatModel",  # 修改代码+ModelsSplit: 公开模型接口名称；若没有这行代码，from learning_agent.models import * 不会包含接口。
    "CodexCliChatModel",  # 修改代码+ModelsSplit: 公开 CLI 模型名称；若没有这行代码，顶层导出不完整。
    "CodexOAuthChatModel",  # 修改代码+ModelsSplit: 公开 OAuth 模型名称；若没有这行代码，顶层导出不完整。
    "CodexOAuthTokenStore",  # 修改代码+ModelsSplit: 公开 token 存储名称；若没有这行代码，顶层导出不完整。
    "CodexOAuthTokens",  # 修改代码+ModelsSplit: 公开 token 数据名称；若没有这行代码，顶层导出不完整。
    "LoginCallbackFunction",  # 修改代码+ModelsSplit: 公开登录回调类型；若没有这行代码，测试注入边界不完整。
    "OpenAIChatModel",  # 修改代码+ModelsSplit: 公开 OpenAI 模型名称；若没有这行代码，顶层导出不完整。
    "PostJsonFunction",  # 修改代码+ModelsSplit: 公开 HTTP POST 回调类型；若没有这行代码，测试注入边界不完整。
    "RunCodexFunction",  # 修改代码+ModelsSplit: 公开 CLI 运行函数类型；若没有这行代码，测试注入边界不完整。
]  # 修改代码+ModelsSplit: 结束公开对象列表；若没有这行代码，Python 列表语法不完整。
