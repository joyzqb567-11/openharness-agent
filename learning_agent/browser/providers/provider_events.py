"""浏览器 provider 事件 helper。"""  # 新增代码+BrowserProviderRouter: 说明本文件负责 provider 事件格式；若没有这行代码，事件 payload 会散落在多个模块。
from __future__ import annotations  # 新增代码+BrowserProviderRouter: 延迟解析类型注解；若没有这行代码，类型引用顺序更脆弱。

from .protocol import BrowserProviderDecision  # 新增代码+BrowserProviderRouter: 导入路由决策对象；若没有这行代码，helper 无法读取决策字段。


def build_provider_decision_event(decision: BrowserProviderDecision) -> dict[str, object]:  # 新增代码+BrowserProviderRouter: 把路由决策转换为事件 payload；若没有这行代码，调用方会重复拼字段。
    return decision.to_event_payload()  # 新增代码+BrowserProviderRouter: 复用决策对象的稳定序列化；若没有这行代码，事件 helper 没有实际输出。
