"""Codex OAuth/API 模型适配器导出。"""  # 新增代码+ModelsSplit: 给 OAuth/API 直连模型提供稳定模块路径；若没有这个文件，网页登录和 API 逻辑仍难定位。

from .adapters import CodexOAuthChatModel, LoginCallbackFunction, PostJsonFunction  # 新增代码+ModelsSplit: 从集中适配器实现导出 OAuth 模型和可注入回调类型；若没有这行代码，阶段 3 计划要求的模块路径不可用。

__all__ = ["CodexOAuthChatModel", "LoginCallbackFunction", "PostJsonFunction"]  # 新增代码+ModelsSplit: 明确本模块公开对象；若没有这行代码，后续修 OAuth 模型时边界不清楚。
