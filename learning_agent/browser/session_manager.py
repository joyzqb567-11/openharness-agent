"""浏览器 session manager，统一管理浏览器模式、可见性和 tab 状态。"""  # 新增代码+BrowserSessionManager: 说明本文件是 Stage 3 的 session 生命周期边界；若没有这行代码，浏览器状态会继续散落。

from __future__ import annotations  # 新增代码+BrowserSessionManager: 延迟解析类型注解；若没有这行代码，自身类型引用更容易受定义顺序影响。

import secrets  # 新增代码+BrowserSessionManager: 生成 session id 需要随机后缀；若没有这行代码，多次浏览器会话可能撞名。
from pathlib import Path  # 新增代码+BrowserSessionManager: 可选路径输入需要 Path 规范化；若没有这行代码，profile 路径脱敏不稳定。
from typing import Any  # 新增代码+BrowserSessionManager: snapshot/health_report 返回通用 JSON 字段；若没有这行代码，类型边界不清楚。

try:  # 修改代码+BrowserSessionManager: 优先按 learning_agent 包路径导入依赖；若没有这行代码，正常包运行时无法复用统一 runtime 模型。
    from learning_agent.browser.runtime_models import BrowserSession, BrowserTab, now_ms  # 修改代码+BrowserSessionManager: 复用 runtime 协议层的 session/tab 模型；若没有这行代码，协议对象会分裂。
    from learning_agent.browser.tab_registry import BrowserTabRegistry  # 修改代码+BrowserSessionManager: 复用 tab registry 管 tab id 和 active 状态；若没有这行代码，session manager 会重复实现 tab 逻辑。
except ModuleNotFoundError as import_error:  # 新增代码+BrowserSessionManager: 兼容 MCP server 直接脚本启动；若没有这行代码，stdio 模式可能找不到 learning_agent 包。
    if import_error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.runtime_models", "learning_agent.browser.tab_registry"}:  # 新增代码+BrowserSessionManager: 只允许路径缺失时 fallback；若没有这行代码，依赖内部 bug 会被误吞。
        raise  # 新增代码+BrowserSessionManager: 重新抛出真实内部导入错误；若没有这行代码，错误会被伪装成脚本模式问题。
    from browser.runtime_models import BrowserSession, BrowserTab, now_ms  # 新增代码+BrowserSessionManager: 脚本模式下从同级 browser 包导入模型；若没有这行代码，直接运行 MCP server 时 manager 不可用。
    from browser.tab_registry import BrowserTabRegistry  # 新增代码+BrowserSessionManager: 脚本模式下导入 tab registry；若没有这行代码，直接运行 MCP server 时无法登记 tabs。

SESSION_MODE_INDEPENDENT = "independent_chromium"  # 新增代码+BrowserSessionManager: 定义独立 Chromium 模式常量；若没有这行代码，字符串会散落在 server 和测试。
SESSION_MODE_VISIBLE = "visible_chromium"  # 新增代码+BrowserSessionManager: 定义可见 Chromium 模式常量；若没有这行代码，窗口模式状态没有统一名称。
SESSION_MODE_REAL_CHROME = "real_chrome_cdp"  # 新增代码+BrowserSessionManager: 定义真实 Chrome CDP 模式常量；若没有这行代码，真实 Chrome 状态和旧 real_chrome 文本会混乱。


class BrowserSessionManager:  # 新增代码+BrowserSessionManager: 管理当前浏览器 session 和 tab registry；若没有这个类，session 生命周期仍散落在 MCP server。
    def __init__(self) -> None:  # 新增代码+BrowserSessionManager: 初始化 manager 默认断开状态；若没有这行代码，调用方无法创建对象。
        self.session_counter = 0  # 新增代码+BrowserSessionManager: 保存会话序号；若没有这行代码，session id 只能完全随机且不易读。
        self.current_session: BrowserSession | None = None  # 新增代码+BrowserSessionManager: 保存当前 session 对象；若没有这行代码，状态报告没有根。
        self.tab_registry: BrowserTabRegistry | None = None  # 新增代码+BrowserSessionManager: 保存当前 tab registry；若没有这行代码，register_tab 无法工作。
        self.profile_summary = ""  # 新增代码+BrowserSessionManager: 保存脱敏 profile 摘要；若没有这行代码，真实 Chrome 状态无法显示 profile 范围。
        self.profile_scope = ""  # 新增代码+BrowserSessionManager: 保存 profile 范围名；若没有这行代码，debug profile 和 daily profile 无法区分。

    def start_session(self, mode: str = SESSION_MODE_INDEPENDENT, visible: bool = False, headless: bool = True, session_id: str | None = None) -> BrowserSession:  # 新增代码+BrowserSessionManager: 启动新浏览器 session；若没有这行代码，tab id 无法按 session 隔离。
        self.session_counter += 1  # 新增代码+BrowserSessionManager: 每次启动推进序号；若没有这行代码，默认 session id 可能重复。
        safe_session_id = session_id or f"browser_session_{self.session_counter}_{secrets.token_hex(4)}"  # 新增代码+BrowserSessionManager: 生成可读且低碰撞 session id；若没有这行代码，调用方必须手写唯一 id。
        self.current_session = BrowserSession(session_id=safe_session_id, mode=str(mode or SESSION_MODE_INDEPENDENT), connected=True, visible=bool(visible), headless=bool(headless), current_tab_id="", tabs=[], created_at_ms=now_ms(), updated_at_ms=now_ms())  # 新增代码+BrowserSessionManager: 构造 runtime 协议 session；若没有这行代码，状态无法落盘或输出。
        self.tab_registry = BrowserTabRegistry(safe_session_id)  # 新增代码+BrowserSessionManager: 为新 session 创建独立 tab registry；若没有这行代码，tab id 会跨 session 复用。
        self.profile_summary = ""  # 新增代码+BrowserSessionManager: 新 session 默认清空 profile 摘要；若没有这行代码，独立 Chromium 可能显示旧真实 Chrome profile。
        self.profile_scope = ""  # 新增代码+BrowserSessionManager: 新 session 默认清空 profile scope；若没有这行代码，状态会继承旧 scope。
        return self.current_session  # 新增代码+BrowserSessionManager: 返回新 session；若没有这行代码，调用方拿不到 session id。

    def ensure_session(self, mode: str = SESSION_MODE_INDEPENDENT, visible: bool = False, headless: bool = True) -> BrowserSession:  # 新增代码+BrowserSessionManager: 确保有当前 session；若没有这行代码，状态工具初始化前会报空对象。
        if self.current_session is None:  # 新增代码+BrowserSessionManager: 没有 session 时自动创建；若没有这行代码，首次状态查看 tab_count 会失败。
            return self.start_session(mode=mode, visible=visible, headless=headless)  # 新增代码+BrowserSessionManager: 用调用方给出的模式创建 session；若没有这行代码，默认值无法传入。
        return self.current_session  # 新增代码+BrowserSessionManager: 已有 session 时直接返回；若没有这行代码，函数无返回。

    def end_session(self, reason: str = "") -> None:  # 新增代码+BrowserSessionManager: 结束当前 session 并保留 manager 可复用；若没有这行代码，断开/重启无法清理状态。
        if self.current_session is not None:  # 新增代码+BrowserSessionManager: 只有存在 session 才需要更新；若没有这行代码，空状态结束会抛错。
            self.current_session.connected = False  # 新增代码+BrowserSessionManager: 标记 session 已断开；若没有这行代码，健康报告会误报可用。
            self.current_session.updated_at_ms = now_ms()  # 新增代码+BrowserSessionManager: 刷新断开时间；若没有这行代码，状态时间线不完整。
            self.current_session.metadata = {"end_reason": reason} if hasattr(self.current_session, "metadata") else {}  # 新增代码+BrowserSessionManager: 兼容未来 metadata 字段并记录原因；若没有这行代码，断开原因无法扩展。
        self.current_session = None  # 新增代码+BrowserSessionManager: 清空当前 session；若没有这行代码，下一次启动可能复用旧会话。
        self.tab_registry = None  # 新增代码+BrowserSessionManager: 清空 tab registry；若没有这行代码，新 session 可能继承旧 tabs。
        self.profile_summary = ""  # 新增代码+BrowserSessionManager: 清空 profile 摘要；若没有这行代码，断开后仍显示旧 profile。
        self.profile_scope = ""  # 新增代码+BrowserSessionManager: 清空 profile scope；若没有这行代码，断开后仍显示旧范围。

    def register_tab(self, url: str = "", title: str = "", active: bool = True, page_key: str = "") -> BrowserTab:  # 新增代码+BrowserSessionManager: 登记当前 session 的 tab；若没有这行代码，server 无法把页面生命周期交给 manager。
        session = self.ensure_session()  # 新增代码+BrowserSessionManager: 确保存在 session；若没有这行代码，直接登记 tab 会访问空 registry。
        if self.tab_registry is None:  # 新增代码+BrowserSessionManager: 防御 registry 被意外清空；若没有这行代码，异常状态会抛 AttributeError。
            self.tab_registry = BrowserTabRegistry(session.session_id)  # 新增代码+BrowserSessionManager: 重建 registry；若没有这行代码，session 无法继续登记 tab。
        tab = self.tab_registry.register_tab(url=url, title=title, active=active, page_key=page_key)  # 新增代码+BrowserSessionManager: 委托 registry 生成或复用 tab；若没有这行代码，tab id 规则不会统一。
        session.current_tab_id = self.tab_registry.active_tab_id  # 新增代码+BrowserSessionManager: 同步 session 当前 tab id；若没有这行代码，BrowserSession 和 registry 状态会分裂。
        session.tabs = [BrowserTab.from_dict(item) for item in self.tab_registry.to_list()]  # 新增代码+BrowserSessionManager: 同步结构化 tab 列表；若没有这行代码，session snapshot 看不到 tabs。
        session.updated_at_ms = now_ms()  # 新增代码+BrowserSessionManager: 刷新 session 更新时间；若没有这行代码，状态新旧不可判断。
        return tab  # 新增代码+BrowserSessionManager: 返回登记后的 tab；若没有这行代码，调用方拿不到 tab_id。

    def forget_tab(self, tab_id: str) -> None:  # 新增代码+BrowserSessionManager: 移除关闭 tab 并同步 session；若没有这行代码，关闭页面仍会显示在状态里。
        if self.tab_registry is None or self.current_session is None:  # 新增代码+BrowserSessionManager: 没有 session 时直接跳过；若没有这行代码，关闭事件可能在清理后抛错。
            return  # 新增代码+BrowserSessionManager: 无状态时安全退出；若没有这行代码，函数会继续访问 None。
        self.tab_registry.forget_tab(tab_id)  # 新增代码+BrowserSessionManager: 委托 registry 删除 tab；若没有这行代码，映射无法清理。
        self.current_session.current_tab_id = self.tab_registry.active_tab_id  # 新增代码+BrowserSessionManager: 同步活动 tab；若没有这行代码，session 可能指向已关闭 tab。
        self.current_session.tabs = [BrowserTab.from_dict(item) for item in self.tab_registry.to_list()]  # 新增代码+BrowserSessionManager: 同步 tab 列表；若没有这行代码，snapshot 会显示旧 tab。
        self.current_session.updated_at_ms = now_ms()  # 新增代码+BrowserSessionManager: 刷新更新时间；若没有这行代码，状态时间线不更新。

    def set_active_by_page_key(self, page_key: str) -> None:  # 新增代码+BrowserSessionManager: 按 server 的 page_id 同步活动 tab；若没有这行代码，切换标签页后状态生态仍显示旧页面。
        if self.tab_registry is None or self.current_session is None:  # 新增代码+BrowserSessionManager: 没有 session 时直接跳过；若没有这行代码，关闭或切换事件可能访问 None。
            return  # 新增代码+BrowserSessionManager: 无状态时安全退出；若没有这行代码，函数会继续访问空 registry。
        self.tab_registry.set_active_by_page_key(page_key)  # 新增代码+BrowserSessionManager: 委托 registry 用 page_key 切 active；若没有这行代码，page_id 和 tab_id 无法对齐。
        self.current_session.current_tab_id = self.tab_registry.active_tab_id  # 新增代码+BrowserSessionManager: 同步 session 当前 tab；若没有这行代码，snapshot 会显示旧 active_tab_id。
        self.current_session.tabs = [BrowserTab.from_dict(item) for item in self.tab_registry.to_list()]  # 新增代码+BrowserSessionManager: 同步最新 tab 列表；若没有这行代码，active 标记不会进入状态输出。
        self.current_session.updated_at_ms = now_ms()  # 新增代码+BrowserSessionManager: 刷新更新时间；若没有这行代码，状态观察者不知道刚刚发生切换。

    def forget_page_key(self, page_key: str) -> None:  # 新增代码+BrowserSessionManager: 按 server 的 page_id 移除 tab；若没有这行代码，页面关闭事件无法清理 session 状态。
        if self.tab_registry is None or self.current_session is None:  # 新增代码+BrowserSessionManager: 没有 session 时直接跳过；若没有这行代码，清理过程可能抛 AttributeError。
            return  # 新增代码+BrowserSessionManager: 无状态时安全退出；若没有这行代码，后续会访问空对象。
        self.tab_registry.forget_page_key(page_key)  # 新增代码+BrowserSessionManager: 委托 registry 删除 page_key 对应 tab；若没有这行代码，关闭页面仍会留在 tab_count。
        self.current_session.current_tab_id = self.tab_registry.active_tab_id  # 新增代码+BrowserSessionManager: 同步剩余活动 tab；若没有这行代码，session 可能指向已关闭页面。
        self.current_session.tabs = [BrowserTab.from_dict(item) for item in self.tab_registry.to_list()]  # 新增代码+BrowserSessionManager: 同步删除后的 tab 列表；若没有这行代码，状态输出仍显示旧 tab。
        self.current_session.updated_at_ms = now_ms()  # 新增代码+BrowserSessionManager: 刷新更新时间；若没有这行代码，状态时间线不会记录关闭动作。

    def record_real_chrome_profile(self, profile_directory: str, profile_scope: str, user_data_dir: str | Path | None = None) -> None:  # 新增代码+BrowserSessionManager: 记录真实 Chrome profile 的脱敏摘要；若没有这行代码，状态可能保存完整用户路径。
        del user_data_dir  # 新增代码+BrowserSessionManager: 明确不保存完整 User Data 路径；若没有这行代码，读者可能误以为路径会进入状态。
        safe_profile = str(profile_directory or "Default").strip() or "Default"  # 新增代码+BrowserSessionManager: 规范化 profile 目录名；若没有这行代码，空 profile 会让摘要不清楚。
        safe_scope = str(profile_scope or "unknown_scope").strip() or "unknown_scope"  # 新增代码+BrowserSessionManager: 规范化 profile 范围；若没有这行代码，状态无法区分 daily/debug。
        self.profile_scope = safe_scope  # 新增代码+BrowserSessionManager: 保存范围名；若没有这行代码，health_report 无法输出 profile_scope。
        self.profile_summary = f"{safe_profile} ({safe_scope})"  # 新增代码+BrowserSessionManager: 只保存安全摘要；若没有这行代码，真实 Chrome 状态缺少 profile 来源。
        if self.current_session is not None:  # 新增代码+BrowserSessionManager: 有 session 时刷新更新时间；若没有这行代码，profile 更新不会反映到状态时间。
            self.current_session.updated_at_ms = now_ms()  # 新增代码+BrowserSessionManager: 刷新 session 更新时间；若没有这行代码，状态新旧不可判断。

    def snapshot(self) -> dict[str, Any]:  # 新增代码+BrowserSessionManager: 输出完整 session 快照；若没有这行代码，status/CLI/API 要重复拼字段。
        report = self.health_report()  # 新增代码+BrowserSessionManager: 先取健康报告基础字段；若没有这行代码，snapshot 和 health_report 会分裂。
        report["profile_summary"] = self.profile_summary  # 新增代码+BrowserSessionManager: 加入脱敏 profile 摘要；若没有这行代码，真实 Chrome 来源不可见。
        report["profile_scope"] = self.profile_scope  # 新增代码+BrowserSessionManager: 加入 profile scope；若没有这行代码，debug/daily 范围不可读。
        return report  # 新增代码+BrowserSessionManager: 返回机器可读快照；若没有这行代码，调用方拿不到状态。

    def health_report(self) -> dict[str, Any]:  # 新增代码+BrowserSessionManager: 输出状态生态所需健康字段；若没有这行代码，browser_plugin_status 无法统一展示。
        if self.current_session is None:  # 新增代码+BrowserSessionManager: 没有 session 时返回断开报告；若没有这行代码，首次状态查看会报错。
            return {"session_id": "", "mode": "disconnected", "connected": False, "visible": False, "headless": True, "tab_count": 0, "active_tab_id": "", "tab_ids": [], "tabs": [], "profile_summary": self.profile_summary, "profile_scope": self.profile_scope}  # 新增代码+BrowserSessionManager: 返回断开状态字段；若没有这行代码，状态消费者要处理缺字段。
        tab_report = self.tab_registry.health_report() if self.tab_registry is not None else {"tab_count": 0, "active_tab_id": "", "tab_ids": [], "tabs": []}  # 新增代码+BrowserSessionManager: 读取 tab 健康摘要；若没有这行代码，session 报告缺 tab 信息。
        return {"session_id": self.current_session.session_id, "mode": self.current_session.mode, "connected": self.current_session.connected, "visible": self.current_session.visible, "headless": self.current_session.headless, "tab_count": tab_report["tab_count"], "active_tab_id": tab_report["active_tab_id"], "tab_ids": tab_report["tab_ids"], "tabs": tab_report["tabs"], "profile_summary": self.profile_summary, "profile_scope": self.profile_scope}  # 新增代码+BrowserSessionManager: 返回完整健康字段；若没有这行代码，状态生态缺少 session 关键信息。
