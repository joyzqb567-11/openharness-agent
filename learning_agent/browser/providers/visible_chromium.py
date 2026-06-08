"""可见 Chromium provider adapter。"""  # 新增代码+BrowserProviderAdapters: 说明本文件把现有 Playwright/Chromium 工具迁入 provider；若没有这行代码，执行边界不清楚。
from __future__ import annotations  # 新增代码+BrowserProviderAdapters: 延迟解析类型注解；若没有这行代码，后续 object 类型扩展更脆弱。

from .protocol import BrowserProviderHealth, BrowserProviderKind  # 新增代码+BrowserProviderAdapters: 导入 provider 健康状态和类型；若没有这行代码，adapter 无法声明自己是哪条轨道。


VISIBLE_CHROMIUM_TOOLS = {  # 新增代码+BrowserProviderAdapters: 定义可见 Chromium adapter 支持的统一工具名；若没有这行代码，server 无法判断哪些工具可委托。
    "browser_open",  # 新增代码+BrowserProviderAdapters: 打开页面沿用现有 Playwright handler；若没有这项，公开网页无法通过 provider 执行。
    "browser_launch_visible",  # 新增代码+BrowserProviderAdapters: 可见窗口启动属于独立 Chromium 轨道；若没有这项，真实可见验收无法经过 provider。
    "browser_snapshot",  # 新增代码+BrowserProviderAdapters: 页面快照属于可见 Chromium 轨道；若没有这项，读页面仍绕过 provider。
    "browser_click",  # 新增代码+BrowserProviderAdapters: 点击动作迁入可见 Chromium provider；若没有这项，写动作仍旁路执行。
    "browser_type",  # 新增代码+BrowserProviderAdapters: 普通输入迁入可见 Chromium provider；若没有这项，表单输入仍旁路执行。
    "browser_type_secret",  # 新增代码+BrowserProviderAdapters: 敏感输入仍复用现有脱敏 handler；若没有这项，登录测试会绕过 provider。
    "browser_press_key",  # 新增代码+BrowserProviderAdapters: 按键动作迁入可见 Chromium provider；若没有这项，键盘操作仍旁路执行。
    "browser_wait",  # 新增代码+BrowserProviderAdapters: 等待工具迁入 provider 便于验收无浏览器依赖路径；若没有这项，Stage 2 真实终端难以轻量验证。
    "browser_screenshot",  # 新增代码+BrowserProviderAdapters: 截图工具迁入 provider；若没有这项，视觉证据仍旁路执行。
    "browser_tabs",  # 新增代码+BrowserProviderAdapters: 标签管理迁入 provider；若没有这项，多标签状态仍旁路执行。
    "browser_tabs_context",  # 新增代码+BrowserTabsContextStage4: 标签页上下文合同迁入 provider；若没有这项，真实执行层会回退旁路而缺少 provider 能力声明。
    "browser_console",  # 新增代码+BrowserProviderAdapters: console 读取迁入 provider；若没有这项，调试日志仍旁路执行。
    "browser_network",  # 新增代码+BrowserProviderAdapters: network 读取迁入 provider；若没有这项，网络摘要仍旁路执行。
    "browser_upload_file",  # 新增代码+BrowserProviderAdapters: 上传工具保留在可见 Chromium provider；若没有这项，文件上传仍旁路执行。
    "browser_downloads",  # 新增代码+BrowserProviderAdapters: 下载记录迁入 provider；若没有这项，下载状态仍旁路执行。
    "browser_evaluate",  # 新增代码+BrowserProviderAdapters: JS 执行迁入 provider 但仍由旧安全策略把关；若没有这项，脚本工具仍旁路执行。
    "browser_close",  # 新增代码+BrowserProviderAdapters: 关闭页面迁入 provider；若没有这项，资源释放仍旁路执行。
    "browser_recover_page",  # 新增代码+BrowserProviderAdapters: 页面恢复迁入 provider；若没有这项，失败恢复仍旁路执行。
    "browser_visual_locate",  # 新增代码+BrowserProviderAdapters: 视觉定位迁入 provider；若没有这项，复杂页面定位仍旁路执行。
    "browser_flow_run",  # 新增代码+BrowserProviderAdapters: 复杂流程迁入 provider；若没有这项，长流程仍旁路执行。
    "browser_replay",  # 新增代码+BrowserProviderAdapters: 回放规划迁入 provider；若没有这项，任务回放仍旁路执行。
    "browser_plugin_status",  # 新增代码+BrowserProviderAdapters: 当前兼容状态仍由可见 Chromium runtime 报告；若没有这项，状态工具会旁路。
    "browser_site_grant",  # 新增代码+BrowserProviderAdapters: 站点授权旧 handler 暂归入可见 Chromium runtime；若没有这项，权限状态仍旁路。
}  # 新增代码+BrowserProviderAdapters: 结束工具集合；若没有这行代码，Python 集合语法不完整。


class VisibleChromiumProvider:  # 新增代码+BrowserProviderAdapters: 定义可见 Chromium provider adapter；若没有这个类，Stage 2 无法把现有 Playwright 能力迁入 provider。
    kind = BrowserProviderKind.VISIBLE_CHROMIUM  # 新增代码+BrowserProviderAdapters: 声明 provider 类型；若没有这行代码，registry 无法按 visible_chromium 注册。

    def __init__(self, backend: object) -> None:  # 新增代码+BrowserProviderAdapters: 接收现有 BrowserAutomationServer 作为 backend；若没有这行代码，adapter 没有旧 handler 可委托。
        self.backend = backend  # 新增代码+BrowserProviderAdapters: 保存 backend 引用；若没有这行代码，execute_tool 无法调用旧 server 方法。

    def health(self) -> BrowserProviderHealth:  # 新增代码+BrowserProviderAdapters: 返回 provider 健康状态；若没有这行代码，router 无法知道可见 Chromium 可用。
        return BrowserProviderHealth.available(self.kind, "visible_chromium_adapter_ready")  # 新增代码+BrowserProviderAdapters: adapter 存在即表示可路由到旧 handler；若没有这行代码，公开网页默认路线会不可用。

    def supports_tool(self, tool_name: str) -> bool:  # 新增代码+BrowserProviderAdapters: 判断工具是否属于可见 Chromium 轨道；若没有这行代码，server 可能把工具发给错误 provider。
        return tool_name in VISIBLE_CHROMIUM_TOOLS  # 新增代码+BrowserProviderAdapters: 使用固定集合判断支持范围；若没有这行代码，工具能力边界不可审计。

    def execute_tool(self, tool_name: str, arguments: dict[str, object]) -> str:  # 新增代码+BrowserProviderAdapters: 通过 provider 执行统一 browser 工具；若没有这行代码，adapter 不能替代 dispatch。
        if not self.supports_tool(tool_name):  # 新增代码+BrowserProviderAdapters: 拦截不属于本 provider 的工具；若没有这行代码，错误工具可能落到 backend 任意方法。
            raise RuntimeError(f"visible_chromium provider 不支持工具：{tool_name}")  # 新增代码+BrowserProviderAdapters: 返回清楚的不支持错误；若没有这行代码，排查会变成 AttributeError。
        handler = getattr(self.backend, tool_name)  # 新增代码+BrowserProviderAdapters: 从旧 server 取同名 handler；若没有这行代码，adapter 无法复用现有实现。
        return str(handler(arguments))  # 新增代码+BrowserProviderAdapters: 返回旧 handler 文本结果并规范成字符串；若没有这行代码，MCP 输出兼容性会被破坏。
