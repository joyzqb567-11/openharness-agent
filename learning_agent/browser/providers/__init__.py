"""浏览器 provider 包公开入口。"""  # 新增代码+BrowserProviderRouter: 说明本包承载双轨浏览器 provider 抽象；若没有这行代码，维护者不知道 provider 边界。
from .protocol import BrowserProvider, BrowserProviderDecision, BrowserProviderHealth, BrowserProviderKind  # 修改代码+BrowserProviderAdapters: 导出 provider 执行协议和路由模型；若没有这行代码，外部代码无法统一标注 adapter。
from .chrome_extension import ChromeExtensionProvider  # 新增代码+ChromeExtensionStage5: 导出 Chrome 插件只读 provider；若没有这行代码，server 需要深入子模块导入插件 adapter。
from .provider_events import build_provider_decision_event  # 新增代码+BrowserProviderRouter: 导出 provider 决策事件 helper；若没有这行代码，调用方难以从包入口复用事件格式。
from .real_chrome_cdp import RealChromeCdpProvider  # 新增代码+BrowserProviderAdapters: 导出真实 Chrome CDP provider adapter；若没有这行代码，server 和测试要深入子模块导入。
from .registry import BrowserProviderRegistry  # 新增代码+BrowserProviderRouter: 导出 provider 注册表；若没有这行代码，状态 API 难以统一查询健康状态。
from .router import BrowserProviderRouter  # 新增代码+BrowserProviderRouter: 导出 provider 路由器；若没有这行代码，调用方无法从包入口使用路由规则。
from .tool_surface import browser_tool_surface_hint, is_provider_control_tool_name, is_provider_specific_tool_name, normalized_browser_tool_name  # 新增代码+BrowserToolSurfaceStage3: 导出工具表面 helper；若没有这行代码，MCP registry 和测试要深入子模块导入。
from .visible_chromium import VisibleChromiumProvider  # 新增代码+BrowserProviderAdapters: 导出可见 Chromium provider adapter；若没有这行代码，server 和测试要深入子模块导入。

__all__ = ["BrowserProvider", "BrowserProviderDecision", "BrowserProviderHealth", "BrowserProviderKind", "BrowserProviderRegistry", "BrowserProviderRouter", "ChromeExtensionProvider", "RealChromeCdpProvider", "VisibleChromiumProvider", "browser_tool_surface_hint", "build_provider_decision_event", "is_provider_control_tool_name", "is_provider_specific_tool_name", "normalized_browser_tool_name"]  # 修改代码+ChromeExtensionStage5: 固定公开 API 并加入 ChromeExtensionProvider；若没有这行代码，外部 agent 难以判断哪些名字稳定。
