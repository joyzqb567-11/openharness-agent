"""真实 Chrome CDP provider adapter。"""  # 新增代码+BrowserProviderAdapters: 说明本文件把现有真实 Chrome CDP 工具迁入 provider；若没有这行代码，CDP 轨道边界不清楚。
from __future__ import annotations  # 新增代码+BrowserProviderAdapters: 延迟解析类型注解；若没有这行代码，后续扩展类型时更脆弱。

from .protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderAdapters: 导入 provider 健康状态和类型；若没有这行代码，adapter 无法声明 CDP 轨道。


REAL_CHROME_CDP_TOOLS = {  # 新增代码+BrowserProviderAdapters: 定义 CDP provider 支持的统一工具名；若没有这行代码，server 无法判断哪些工具走 CDP。
    "browser_connect_real_chrome",  # 新增代码+BrowserProviderAdapters: 真实 Chrome 连接入口属于 CDP provider；若没有这项，连接工具仍旁路执行。
    "browser_tabs_context",  # 新增代码+BrowserTabsContextStage4: 真实 Chrome 标签页上下文属于 CDP provider；若没有这项，登录态任务无法通过 provider 声明先读 tab。
    "browser_disconnect_real_chrome",  # 新增代码+BrowserProviderAdapters: 真实 Chrome 断开入口属于 CDP provider；若没有这项，释放连接仍旁路执行。
    "browser_profile_status",  # 新增代码+BrowserProviderAdapters: 真实 Chrome/profile 状态属于 CDP provider；若没有这项，状态查询仍旁路执行。
}  # 新增代码+BrowserProviderAdapters: 结束工具集合；若没有这行代码，Python 集合语法不完整。


class RealChromeCdpProvider:  # 新增代码+BrowserProviderAdapters: 定义真实 Chrome CDP provider adapter；若没有这个类，Stage 2 无法把 CDP 能力迁入 provider。
    kind = BrowserProviderKind.REAL_CHROME_CDP  # 新增代码+BrowserProviderAdapters: 声明 provider 类型；若没有这行代码，registry 无法按 real_chrome_cdp 注册。

    def __init__(self, backend: object) -> None:  # 新增代码+BrowserProviderAdapters: 接收现有 BrowserAutomationServer 作为 backend；若没有这行代码，adapter 没有旧 CDP handler 可委托。
        self.backend = backend  # 新增代码+BrowserProviderAdapters: 保存 backend 引用；若没有这行代码，execute_tool 无法调用旧真实 Chrome 方法。

    def health(self) -> BrowserProviderHealth:  # 新增代码+BrowserProviderAdapters: 返回 CDP provider 健康状态；若没有这行代码，router 无法知道 CDP adapter 已接入。
        return BrowserProviderHealth.available(self.kind, "real_chrome_cdp_adapter_ready")  # 新增代码+BrowserProviderAdapters: adapter 存在即表示 CDP 入口可路由；若没有这行代码，显式 CDP 请求会被判不可用。

    def supports_tool(self, tool_name: str) -> bool:  # 新增代码+BrowserProviderAdapters: 判断工具是否属于 CDP provider；若没有这行代码，server 可能把普通工具误发给 CDP。
        return tool_name in REAL_CHROME_CDP_TOOLS  # 新增代码+BrowserProviderAdapters: 使用固定集合判断支持范围；若没有这行代码，CDP 工具边界不可审计。

    def execute_tool(self, tool_name: str, arguments: dict[str, object]) -> str:  # 新增代码+BrowserProviderAdapters: 通过 provider 执行真实 Chrome CDP 工具；若没有这行代码，adapter 只有状态没有执行能力。
        if not self.supports_tool(tool_name):  # 新增代码+BrowserProviderAdapters: 拦截不属于 CDP 的工具；若没有这行代码，CDP provider 可能误执行普通页面动作。
            raise RuntimeError(f"real_chrome_cdp provider 不支持工具：{tool_name}")  # 新增代码+BrowserProviderAdapters: 返回清楚的不支持错误；若没有这行代码，排查会变成 AttributeError。
        handler = getattr(self.backend, tool_name)  # 新增代码+BrowserProviderAdapters: 从旧 server 取同名 CDP handler；若没有这行代码，adapter 无法复用已验证实现。
        return str(handler(arguments))  # 新增代码+BrowserProviderAdapters: 返回旧 handler 文本结果并规范成字符串；若没有这行代码，MCP 输出兼容性会被破坏。
