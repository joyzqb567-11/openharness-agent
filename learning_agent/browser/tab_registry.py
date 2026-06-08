"""浏览器 tab registry，用稳定 id 管理页面生命周期。"""  # 新增代码+BrowserSessionManager: 说明本文件只负责 tab id 和 tab 摘要管理；若没有这行代码，tab 逻辑会继续散落在 MCP server。

from __future__ import annotations  # 新增代码+BrowserSessionManager: 延迟解析类型注解；若没有这行代码，未来类型引用更容易受定义顺序影响。

import re  # 新增代码+BrowserSessionManager: 清洗 session id 生成安全 tab id 需要正则；若没有这行代码，特殊字符可能进入文件或事件 id。
from typing import Any  # 新增代码+BrowserSessionManager: tab 元数据可能包含通用 JSON 值；若没有这行代码，类型边界不清楚。

try:  # 修改代码+BrowserSessionManager: 优先按包路径导入 runtime 模型；若没有这行代码，作为 learning_agent 包运行时会找不到统一协议对象。
    from learning_agent.browser.runtime_models import BrowserTab, now_ms  # 修改代码+BrowserSessionManager: 复用 BrowserTab 协议模型和毫秒时间；若没有这行代码，tab registry 会和 runtime 协议分裂。
except ModuleNotFoundError as import_error:  # 新增代码+BrowserSessionManager: 兼容 MCP server 直接作为脚本运行；若没有这行代码，stdio 启动时可能因为包路径不同而失败。
    if import_error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.runtime_models"}:  # 新增代码+BrowserSessionManager: 只允许包路径缺失时 fallback；若没有这行代码，runtime_models 内部真实 bug 会被误吞。
        raise  # 新增代码+BrowserSessionManager: 重新抛出内部导入错误；若没有这行代码，排查会被错误 fallback 误导。
    from browser.runtime_models import BrowserTab, now_ms  # 新增代码+BrowserSessionManager: 脚本模式下从同级 browser 包导入模型；若没有这行代码，直接启动 server 时 session manager 不可用。


def sanitize_tab_id_prefix(value: str) -> str:  # 新增代码+BrowserSessionManager: 清洗 session id 用作 tab id 前缀；若没有这行代码，空格和冒号可能污染 tab id。
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value or "").strip())  # 新增代码+BrowserSessionManager: 把非安全字符替换成下划线；若没有这行代码，外部状态消费者解析 id 会更脆弱。
    return cleaned or "browser_session"  # 新增代码+BrowserSessionManager: 空值兜底为固定前缀；若没有这行代码，tab id 可能以空字符串开头。


class BrowserTabRegistry:  # 新增代码+BrowserSessionManager: 管理单个 session 内的 tab 列表；若没有这个类，tab id 生成和活动页切换会继续散落。
    def __init__(self, session_id: str) -> None:  # 新增代码+BrowserSessionManager: 初始化 registry 并绑定 session id；若没有这行代码，tab id 无法带 session 前缀。
        self.session_id = sanitize_tab_id_prefix(session_id)  # 新增代码+BrowserSessionManager: 保存清洗后的 session id；若没有这行代码，tab id 可能带非法字符。
        self.next_tab_index = 1  # 新增代码+BrowserSessionManager: 保存下一个 tab 序号；若没有这行代码，同一 session 内 tab id 会重复。
        self.tabs: dict[str, BrowserTab] = {}  # 新增代码+BrowserSessionManager: 保存 tab_id 到 BrowserTab 的映射；若没有这行代码，状态报告无法列出 tabs。
        self.page_keys: dict[str, str] = {}  # 新增代码+BrowserSessionManager: 保存外部页面 key 到 tab_id 的映射；若没有这行代码，重复登记同一页面会产生多个 tab。
        self.active_tab_id = ""  # 新增代码+BrowserSessionManager: 保存当前活动 tab；若没有这行代码，默认操作目标不清楚。

    def register_tab(self, url: str = "", title: str = "", active: bool = True, page_key: str = "") -> BrowserTab:  # 新增代码+BrowserSessionManager: 登记或更新一个 tab；若没有这行代码，session manager 无法接收页面生命周期。
        safe_page_key = str(page_key or "").strip()  # 新增代码+BrowserSessionManager: 清理外部页面 key；若没有这行代码，空白 key 会导致重复登记不稳定。
        if safe_page_key and safe_page_key in self.page_keys:  # 新增代码+BrowserSessionManager: 如果页面已登记就复用旧 tab id；若没有这行代码，同一 Playwright 页面会重复产生 tab。
            tab_id = self.page_keys[safe_page_key]  # 新增代码+BrowserSessionManager: 找到已有 tab id；若没有这行代码，后续无法更新原 tab。
            tab = self.tabs[tab_id]  # 新增代码+BrowserSessionManager: 取出已有 BrowserTab；若没有这行代码，无法更新 URL/title。
            tab.url = str(url or tab.url)  # 新增代码+BrowserSessionManager: 更新 URL 摘要；若没有这行代码，状态报告可能保留旧地址。
            tab.title = str(title or tab.title)  # 新增代码+BrowserSessionManager: 更新标题摘要；若没有这行代码，状态报告可能保留旧标题。
            tab.last_seen_at_ms = now_ms()  # 新增代码+BrowserSessionManager: 刷新最近看到时间；若没有这行代码，健康报告无法判断新旧。
            if active:  # 新增代码+BrowserSessionManager: 调用方要求设为活动页时进入切换；若没有这行代码，重复登记不会更新当前页。
                self.set_active(tab_id)  # 新增代码+BrowserSessionManager: 设置活动 tab；若没有这行代码，默认操作目标不会跟着页面变化。
            return tab  # 新增代码+BrowserSessionManager: 返回复用 tab；若没有这行代码，调用方拿不到稳定 id。
        tab_id = f"{self.session_id}-tab-{self.next_tab_index}"  # 新增代码+BrowserSessionManager: 生成带 session 前缀的 tab id；若没有这行代码，tab id 会跨 session 重复。
        self.next_tab_index += 1  # 新增代码+BrowserSessionManager: 推进下一个 tab 序号；若没有这行代码，下次登记会复用同一个 id。
        tab = BrowserTab(tab_id=tab_id, url=str(url or ""), title=str(title or ""), active=False, last_seen_at_ms=now_ms())  # 新增代码+BrowserSessionManager: 构造 BrowserTab 协议对象；若没有这行代码，registry 没有可落盘状态。
        self.tabs[tab_id] = tab  # 新增代码+BrowserSessionManager: 保存 tab 对象；若没有这行代码，后续无法查找该 tab。
        if safe_page_key:  # 新增代码+BrowserSessionManager: 有外部页面 key 时保存映射；若没有这行代码，重复页面无法复用。
            self.page_keys[safe_page_key] = tab_id  # 新增代码+BrowserSessionManager: 记录 page_key 到 tab_id；若没有这行代码，同一页面事件会重复登记。
        if active or not self.active_tab_id:  # 新增代码+BrowserSessionManager: 新 tab 默认成为当前页，或在无当前页时兜底；若没有这行代码，active_tab_id 可能为空。
            self.set_active(tab_id)  # 新增代码+BrowserSessionManager: 切换活动页并更新 active 标记；若没有这行代码，多 tab 的 active 字段会不一致。
        return tab  # 新增代码+BrowserSessionManager: 返回新 tab；若没有这行代码，调用方拿不到 id。

    def set_active(self, tab_id: str) -> None:  # 新增代码+BrowserSessionManager: 设置当前活动 tab；若没有这行代码，tab 切换逻辑会散落在 server。
        if tab_id not in self.tabs:  # 新增代码+BrowserSessionManager: 不允许切到不存在的 tab；若没有这行代码，active_tab_id 可能指向无效页面。
            return  # 新增代码+BrowserSessionManager: 无效 tab 直接忽略，保护主流程；若没有这行代码，状态更新会抛 KeyError。
        for existing_tab in self.tabs.values():  # 新增代码+BrowserSessionManager: 遍历所有 tab 更新 active 标记；若没有这行代码，可能出现多个当前页。
            existing_tab.active = existing_tab.tab_id == tab_id  # 新增代码+BrowserSessionManager: 只有目标 tab 标为活动；若没有这行代码，状态报告无法判断默认目标。
        self.active_tab_id = tab_id  # 新增代码+BrowserSessionManager: 保存活动 tab id；若没有这行代码，健康报告没有 active_tab_id。

    def tab_id_for_page_key(self, page_key: str) -> str:  # 新增代码+BrowserSessionManager: 根据 Playwright page_id 找到稳定 tab_id；若没有这行代码，server 关闭页面时只能碰 registry 内部字典。
        safe_page_key = str(page_key or "").strip()  # 新增代码+BrowserSessionManager: 清理外部页面 key；若没有这行代码，空格会导致映射查找失败。
        return self.page_keys.get(safe_page_key, "")  # 新增代码+BrowserSessionManager: 返回对应 tab_id 或空字符串；若没有这行代码，调用方无法区分未找到和异常。

    def set_active_by_page_key(self, page_key: str) -> None:  # 新增代码+BrowserSessionManager: 通过 server 的 page_id 切换活动 tab；若没有这行代码，browser_tabs switch 不会同步状态生态。
        tab_id = self.tab_id_for_page_key(page_key)  # 新增代码+BrowserSessionManager: 先把 page_key 转成 tab_id；若没有这行代码，registry 无法使用内部 tab 主键。
        if not tab_id:  # 新增代码+BrowserSessionManager: 没有映射时安全跳过；若没有这行代码，新旧状态不同步时会误报异常。
            return  # 新增代码+BrowserSessionManager: 无映射直接返回；若没有这行代码，后续 set_active 会收到空 id。
        self.set_active(tab_id)  # 新增代码+BrowserSessionManager: 复用 tab_id 切换逻辑；若没有这行代码，多入口 active 规则会不一致。

    def forget_page_key(self, page_key: str) -> None:  # 新增代码+BrowserSessionManager: 通过 server 的 page_id 移除 tab；若没有这行代码，关闭页面不会从 session 状态里消失。
        tab_id = self.tab_id_for_page_key(page_key)  # 新增代码+BrowserSessionManager: 找到 page_key 对应的 tab_id；若没有这行代码，无法定位需要删除的 tab。
        if not tab_id:  # 新增代码+BrowserSessionManager: 不存在映射时安全跳过；若没有这行代码，重复关闭事件可能报错。
            return  # 新增代码+BrowserSessionManager: 无 tab 可删时直接返回；若没有这行代码，后续 forget_tab 会收到空 id。
        self.forget_tab(tab_id)  # 新增代码+BrowserSessionManager: 复用统一删除逻辑；若没有这行代码，page_key 映射和 active 状态不会被一起清理。

    def forget_tab(self, tab_id: str) -> None:  # 新增代码+BrowserSessionManager: 移除关闭的 tab；若没有这行代码，状态报告会显示失效页面。
        if tab_id not in self.tabs:  # 新增代码+BrowserSessionManager: 不存在的 tab 直接忽略；若没有这行代码，重复关闭事件会抛错。
            return  # 新增代码+BrowserSessionManager: 退出无效移除；若没有这行代码，函数会继续访问不存在对象。
        del self.tabs[tab_id]  # 新增代码+BrowserSessionManager: 删除 tab 记录；若没有这行代码，关闭页面仍会留在列表。
        for page_key, mapped_tab_id in list(self.page_keys.items()):  # 新增代码+BrowserSessionManager: 清理 page_key 反向映射；若没有这行代码，旧 page_key 会指向不存在 tab。
            if mapped_tab_id == tab_id:  # 新增代码+BrowserSessionManager: 找到属于被删 tab 的 page_key；若没有这行代码，会误删其他映射。
                del self.page_keys[page_key]  # 新增代码+BrowserSessionManager: 删除旧映射；若没有这行代码，重复登记可能取到坏 tab。
        if self.active_tab_id == tab_id:  # 新增代码+BrowserSessionManager: 如果删除的是当前页要重新选择；若没有这行代码，active_tab_id 会失效。
            self.active_tab_id = next(reversed(self.tabs), "") if self.tabs else ""  # 新增代码+BrowserSessionManager: 切到剩余最后 tab 或清空；若没有这行代码，后续默认操作目标为空乱。
            if self.active_tab_id:  # 新增代码+BrowserSessionManager: 还有剩余 tab 时同步 active 标记；若没有这行代码，新活动页不会标记出来。
                self.set_active(self.active_tab_id)  # 新增代码+BrowserSessionManager: 更新 active 标记；若没有这行代码，状态报告可能没有当前页。

    def to_list(self) -> list[dict[str, Any]]:  # 新增代码+BrowserSessionManager: 返回 tab 列表字典；若没有这行代码，状态和测试要重复转换。
        return [tab.to_dict() for tab in self.tabs.values()]  # 新增代码+BrowserSessionManager: 按登记顺序输出 tab 字段；若没有这行代码，调用方拿不到结构化状态。

    def health_report(self) -> dict[str, Any]:  # 新增代码+BrowserSessionManager: 输出 tab registry 健康摘要；若没有这行代码，session manager 不能聚合 tab_count。
        return {"tab_count": len(self.tabs), "active_tab_id": self.active_tab_id, "tab_ids": list(self.tabs.keys()), "tabs": self.to_list()}  # 新增代码+BrowserSessionManager: 返回机器可读 tab 摘要；若没有这行代码，状态生态缺少 tab 视图。
