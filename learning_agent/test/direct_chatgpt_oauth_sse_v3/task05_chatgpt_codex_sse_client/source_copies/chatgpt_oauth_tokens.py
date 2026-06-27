"""ChatGPT OAuth token 数据边界。"""  # 新增代码+DirectChatGptSseClient: 这个模块把 GUI 直连 OAuth token 形状独立出来；如果没有这行代码，后续 Direct SSE 客户端会继续依赖旧 adapters.py 的内部类。

from __future__ import annotations  # 新增代码+DirectChatGptSseClient: 延迟解析类型注解；如果没有这行代码，Python 老版本类型前向引用更容易出错。

from dataclasses import dataclass  # 新增代码+DirectChatGptSseClient: 使用 dataclass 表达 token 数据；如果没有这行代码，需要手写重复初始化代码。
from typing import Any  # 新增代码+DirectChatGptSseClient: 导入通用对象类型；如果没有这行代码，from_mapping 的输入类型无法清楚表达。


@dataclass(frozen=True)  # 新增代码+DirectChatGptSseClient: token bundle 创建后不可变；如果没有这行代码，调用链中可能误改 access_token。
class ChatGptOAuthTokenBundle:  # 新增代码+DirectChatGptSseClient: 函数段开始，保存 Direct ChatGPT OAuth SSE 所需 token；如果没有这个类，GUI 直连链路没有清晰认证数据边界，本段到 from_mapping 返回结束。
    access_token: str  # 新增代码+DirectChatGptSseClient: 保存短期访问 token；如果没有这行代码，客户端无法写 Authorization 请求头。
    refresh_token: str = ""  # 新增代码+DirectChatGptSseClient: 保存可选 refresh token；如果没有这行代码，后续刷新链路没有标准字段。
    account_id: str | None = None  # 新增代码+DirectChatGptSseClient: 保存 ChatGPT 账号/组织 id；如果没有这行代码，多账号场景无法写 ChatGPT-Account-Id。
    expires_at_ms: int = 0  # 新增代码+DirectChatGptSseClient: 保存毫秒级过期时间；如果没有这行代码，后续无法判断 token 是否需要刷新。

    @classmethod  # 新增代码+DirectChatGptSseClient: 允许从 JSON 字典安全创建 token bundle；如果没有这行代码，调用方会到处重复字段清洗。
    def from_mapping(cls, payload: dict[str, Any]) -> "ChatGptOAuthTokenBundle":  # 新增代码+DirectChatGptSseClient: 函数段开始，把通用字典转成 token bundle；如果没有这个函数，secret store 读取结果不能稳定进入客户端，本段到 return 结束。
        access_token = str(payload.get("access_token", "") or "").strip()  # 新增代码+DirectChatGptSseClient: 清理 access_token；如果没有这行代码，空白 token 会被当成可用 token。
        refresh_token = str(payload.get("refresh_token", "") or "").strip()  # 新增代码+DirectChatGptSseClient: 清理 refresh_token；如果没有这行代码，刷新字段可能携带无意义空白。
        account_id = str(payload.get("account_id", "") or "").strip() or None  # 新增代码+DirectChatGptSseClient: 清理 account_id 并把空值转 None；如果没有这行代码，请求头可能写入空账号。
        raw_expires_at = payload.get("expires_at_ms", payload.get("expires_at", 0))  # 新增代码+DirectChatGptSseClient: 兼容 expires_at_ms 和旧 expires_at 字段；如果没有这行代码，旧 token 文件无法被直连客户端识别。
        try:  # 新增代码+DirectChatGptSseClient: 捕获非法过期时间；如果没有这行代码，坏配置会让 GUI 请求直接崩溃。
            expires_at_ms = int(raw_expires_at or 0)  # 新增代码+DirectChatGptSseClient: 转换毫秒时间戳；如果没有这行代码，后续比较过期时间会拿到字符串。
        except (TypeError, ValueError):  # 新增代码+DirectChatGptSseClient: 处理 None、对象或非数字字符串；如果没有这行代码，坏 token 会抛出底层异常。
            expires_at_ms = 0  # 新增代码+DirectChatGptSseClient: 非法过期时间按已过期处理；如果没有这行代码，调用方无法安全兜底。
        return cls(access_token=access_token, refresh_token=refresh_token, account_id=account_id, expires_at_ms=expires_at_ms)  # 新增代码+DirectChatGptSseClient: 返回清洗后的 token bundle；如果没有这行代码，from_mapping 没有产物。


__all__ = ["ChatGptOAuthTokenBundle"]  # 新增代码+DirectChatGptSseClient: 明确本模块公开对象；如果没有这行代码，导入边界不清晰。
