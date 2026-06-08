"""浏览器 provider 协议模型。"""  # 新增代码+BrowserProviderRouter: 说明本文件只定义 provider 类型和路由结果；若没有这行代码，执行逻辑容易混入协议层。
from __future__ import annotations  # 新增代码+BrowserProviderRouter: 延迟解析类型注解；若没有这行代码，类之间互相引用时更脆弱。

from dataclasses import dataclass  # 新增代码+BrowserProviderRouter: 使用 dataclass 表示小型决策对象；若没有这行代码，需要手写初始化样板代码。
from enum import Enum  # 新增代码+BrowserProviderRouter: 使用枚举固定 provider 名称；若没有这行代码，字符串拼写错误难以及早发现。
from typing import Any, Protocol  # 修改代码+BrowserProviderAdapters: 增加 Protocol 用于定义 provider 执行接口；若没有这行代码，adapter 只能靠口头约定接口。


class BrowserProviderKind(str, Enum):  # 新增代码+BrowserProviderRouter: 定义浏览器 provider 类型；若没有这个类，路由器只能使用容易拼错的裸字符串。
    VISIBLE_CHROMIUM = "visible_chromium"  # 新增代码+BrowserProviderRouter: 表示隔离可见 Chromium；若没有这项，公开网页和本地调试没有默认 provider。
    REAL_CHROME_CDP = "real_chrome_cdp"  # 新增代码+BrowserProviderRouter: 表示真实 Chrome CDP 调试路线；若没有这项，显式 CDP 请求无法表达。
    CHROME_EXTENSION = "chrome_extension"  # 新增代码+BrowserProviderRouter: 表示 Chrome 插件 provider；若没有这项，登录态和当前 Chrome 路线无法表达。
    UNAVAILABLE = "unavailable"  # 新增代码+BrowserProviderRouter: 表示没有可安全执行的 provider；若没有这项，插件不可用时容易静默降级。


class BrowserProvider(Protocol):  # 新增代码+BrowserProviderAdapters: 定义所有 provider adapter 必须满足的最小执行协议；若没有这个类，server 无法用统一方式调用不同底层浏览器。
    @property  # 新增代码+BrowserProviderAdapters: 把 kind 暴露成只读属性；若没有这行代码，registry 无法按 provider 类型注册 adapter。
    def kind(self) -> BrowserProviderKind:  # 新增代码+BrowserProviderAdapters: 返回 provider 类型；若没有这行代码，router 决策无法对应具体 adapter。
        ...  # 新增代码+BrowserProviderAdapters: Protocol 占位表示实现类必须提供；若没有这行代码，接口定义语法不完整。

    def health(self) -> "BrowserProviderHealth":  # 新增代码+BrowserProviderAdapters: 返回 provider 当前健康状态；若没有这行代码，registry 无法从 adapter 自动刷新健康。
        ...  # 新增代码+BrowserProviderAdapters: Protocol 占位表示实现类必须提供；若没有这行代码，接口定义语法不完整。

    def supports_tool(self, tool_name: str) -> bool:  # 新增代码+BrowserProviderAdapters: 判断 provider 是否支持某个统一 browser 工具；若没有这行代码，server 可能把工具发给错误轨道。
        ...  # 新增代码+BrowserProviderAdapters: Protocol 占位表示实现类必须提供；若没有这行代码，接口定义语法不完整。

    def execute_tool(self, tool_name: str, arguments: dict[str, object]) -> str:  # 新增代码+BrowserProviderAdapters: 通过 provider 执行统一 browser 工具；若没有这行代码，adapter 只有状态没有执行能力。
        ...  # 新增代码+BrowserProviderAdapters: Protocol 占位表示实现类必须提供；若没有这行代码，接口定义语法不完整。


@dataclass(frozen=True)  # 新增代码+BrowserProviderRouter: 冻结健康状态对象避免路由中被意外修改；若没有这行代码，测试和事件可能看到被污染的状态。
class BrowserProviderHealth:  # 新增代码+BrowserProviderRouter: 表示某个 provider 当前是否可用；若没有这个类，路由器无法区分插件未安装和可用。
    kind: BrowserProviderKind  # 新增代码+BrowserProviderRouter: 保存 provider 类型；若没有这行代码，健康状态无法对应具体 provider。
    available: bool  # 新增代码+BrowserProviderRouter: 保存是否可用；若没有这行代码，路由器无法判断能否选择。
    reason: str = ""  # 新增代码+BrowserProviderRouter: 保存不可用或可用原因；若没有这行代码，状态输出不可审计。
    metadata: dict[str, Any] | None = None  # 新增代码+Phase19BrowserRouting: 保存 provider 健康状态的扩展证据，例如是否配对和支持哪些工具；如果没有这行代码，router 只能粗糙判断 available，无法做生产级路由。

    @classmethod  # 新增代码+BrowserProviderRouter: 提供可读构造入口；若没有这行代码，测试会重复传 available=True。
    def available(cls, kind: BrowserProviderKind, reason: str = "available", metadata: dict[str, Any] | None = None) -> "BrowserProviderHealth":  # 修改代码+Phase19BrowserRouting: 构造可用健康状态并允许携带审计 metadata；如果没有这行代码，插件配对和工具能力无法传给 router。
        return cls(kind=kind, available=True, reason=reason, metadata=dict(metadata or {}))  # 修改代码+Phase19BrowserRouting: 返回可用状态并复制 metadata 防止调用方后续污染；如果没有这行代码，health 的证据字段可能被外部误改。

    @classmethod  # 新增代码+BrowserProviderRouter: 提供不可用构造入口；若没有这行代码，测试会重复传 available=False。
    def unavailable(cls, kind: BrowserProviderKind, reason: str, metadata: dict[str, Any] | None = None) -> "BrowserProviderHealth":  # 修改代码+Phase19BrowserRouting: 构造不可用健康状态并允许携带失败证据；如果没有这行代码，未配对、工具不支持等原因无法被上层审计。
        return cls(kind=kind, available=False, reason=str(reason), metadata=dict(metadata or {}))  # 修改代码+Phase19BrowserRouting: 返回不可用状态并复制 metadata；如果没有这行代码，不可用分支会丢失诊断字段。


@dataclass(frozen=True)  # 新增代码+BrowserProviderRouter: 冻结决策对象避免执行层改写审计事实；若没有这行代码，event payload 可能和真实选择不一致。
class BrowserProviderDecision:  # 新增代码+BrowserProviderRouter: 表示一次 provider 路由决策；若没有这个类，路由器返回松散 dict 难以维护。
    provider: BrowserProviderKind  # 新增代码+BrowserProviderRouter: 保存最终选择的 provider；若没有这行代码，调用方不知道走哪条路。
    reason: str  # 新增代码+BrowserProviderRouter: 保存选择原因；若没有这行代码，用户无法理解为什么选择这条路线。
    tool_name: str  # 新增代码+BrowserProviderRouter: 保存触发决策的工具名；若没有这行代码，事件日志无法关联工具。
    reason_code: str = "provider_selected"  # 新增代码+BrowserProviderRouter: 保存稳定机器可读原因码；若没有这行代码，外部 agent 只能解析自然语言原因。
    fallback_provider: BrowserProviderKind = BrowserProviderKind.UNAVAILABLE  # 新增代码+BrowserProviderRouter: 保存可选 fallback；若没有这行代码，插件不可用时无法提示 CDP 可选。
    requires_user_confirmation: bool = False  # 新增代码+BrowserProviderRouter: 标记是否需要用户确认；若没有这行代码，高风险降级可能直接执行。
    metadata: dict[str, Any] | None = None  # 新增代码+BrowserProviderRouter: 保存额外审计字段；若没有这行代码，未来扩展会破坏构造签名。

    def to_event_payload(self) -> dict[str, Any]:  # 新增代码+BrowserProviderRouter: 把决策转成可写入 JSONL 的 payload；若没有这行代码，事件写入会在各处重复。
        return {  # 新增代码+BrowserProviderRouter: 返回稳定字典结构；若没有这行代码，函数没有可用输出。
            "schema_version": 1,  # 新增代码+BrowserProviderRouter: 写入事件 payload 版本；若没有这行代码，未来协议变化无法兼容解析。
            "provider": self.provider.value,  # 新增代码+BrowserProviderRouter: 写入最终 provider 字符串；若没有这行代码，状态 API 无法显示选择结果。
            "reason": self.reason,  # 新增代码+BrowserProviderRouter: 写入选择原因；若没有这行代码，审计无法解释路由。
            "reason_code": self.reason_code,  # 新增代码+BrowserProviderRouter: 写入稳定原因码；若没有这行代码，外部 agent 难以可靠判断分支。
            "tool_name": self.tool_name,  # 新增代码+BrowserProviderRouter: 写入工具名；若没有这行代码，无法知道哪个动作触发选择。
            "fallback_provider": self.fallback_provider.value,  # 新增代码+BrowserProviderRouter: 写入 fallback provider；若没有这行代码，用户不知道可选降级路线。
            "requires_user_confirmation": self.requires_user_confirmation,  # 新增代码+BrowserProviderRouter: 写入确认需求；若没有这行代码，高风险门禁不可见。
            "metadata": _json_safe(dict(self.metadata or {})),  # 修改代码+BrowserProviderRouter: 写入 JSON 安全扩展字段；若没有这行代码，不可序列化对象可能破坏 JSONL。
        }  # 新增代码+BrowserProviderRouter: 结束 payload；若没有这行代码，Python 字典语法不完整。


def _json_safe(value: Any) -> Any:  # 新增代码+BrowserProviderRouter: 把 metadata 转成 JSON 可序列化结构；若没有这行代码，event log 写入可能因对象类型失败。
    if value is None or isinstance(value, (str, int, float, bool)):  # 新增代码+BrowserProviderRouter: 原生 JSON 标量可直接返回；若没有这行代码，普通字段会被不必要字符串化。
        return value  # 新增代码+BrowserProviderRouter: 返回安全标量；若没有这行代码，标量分支没有结果。
    if isinstance(value, dict):  # 新增代码+BrowserProviderRouter: 字典需要递归清理键和值；若没有这行代码，嵌套 metadata 无法保留结构。
        return {str(key): _json_safe(item) for key, item in value.items()}  # 新增代码+BrowserProviderRouter: 返回字符串键和安全值；若没有这行代码，非字符串键或对象值可能破坏 JSON。
    if isinstance(value, (list, tuple)):  # 新增代码+BrowserProviderRouter: 列表和元组可以按顺序递归清理；若没有这行代码，数组 metadata 可能被整体字符串化。
        return [_json_safe(item) for item in value]  # 新增代码+BrowserProviderRouter: 返回 JSON 数组；若没有这行代码，数组结构无法保留。
    if isinstance(value, set):  # 新增代码+BrowserProviderRouter: 集合不是 JSON 类型，需要稳定转换；若没有这行代码，set 会导致序列化失败。
        return [_json_safe(item) for item in sorted(value, key=lambda item: str(item))]  # 新增代码+BrowserProviderRouter: 按字符串排序后返回数组；若没有这行代码，集合输出顺序不可预测。
    return str(value)  # 新增代码+BrowserProviderRouter: 兜底把未知对象转字符串；若没有这行代码，不可序列化对象会抛错。
