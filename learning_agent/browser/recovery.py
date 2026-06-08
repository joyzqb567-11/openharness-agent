"""浏览器恢复管理器，把常见失败归类并给出有限重试策略。"""  # 新增代码+BrowserRecoveryStage7: 说明本模块负责失败恢复决策；若没有这行代码，恢复边界不清楚。

from __future__ import annotations  # 新增代码+BrowserRecoveryStage7: 延迟解析类型注解；若没有这行代码，类型引用更脆弱。

from collections import Counter  # 新增代码+BrowserRecoveryStage7: 统计每个动作/错误的恢复次数；若没有这行代码，重试预算需要手写字典逻辑。
from typing import Any  # 新增代码+BrowserRecoveryStage7: 恢复计划是通用 JSON dict；若没有这行代码，类型边界不清楚。

ERROR_PATTERNS = (  # 新增代码+BrowserRecoveryStage7: 定义错误文本到标准错误类型的映射；若没有这行代码，恢复策略只能靠猜。
    ("chrome_disconnected", ("chrome disconnected", "cdp", "browser has been closed")),  # 新增代码+BrowserRecoveryStage7: 匹配真实 Chrome 断连；若没有这行代码，CDP 失败无法重连提示。
    ("page_closed", ("target page has been closed", "page closed", "页面已经关闭")),  # 新增代码+BrowserRecoveryStage7: 匹配页面关闭；若没有这行代码，关闭页面无法建议重开。
    ("context_closed", ("context closed", "browser context closed")),  # 新增代码+BrowserRecoveryStage7: 匹配上下文关闭；若没有这行代码，整组页面失效无法分类。
    ("navigation_timeout", ("waiting for navigation", "navigation timeout", "timeout", "exceeded")),  # 新增代码+BrowserRecoveryStage7: 匹配导航超时；若没有这行代码，慢页面无法选择 reload。
    ("network_idle_timeout", ("networkidle", "network idle")),  # 新增代码+BrowserRecoveryStage7: 匹配网络静默超时；若没有这行代码，等待网络稳定失败无法分类。
    ("locator_not_found", ("locator not found", "找不到元素", "not found", "no element")),  # 新增代码+BrowserRecoveryStage7: 匹配定位失败；若没有这行代码，无法建议重新 snapshot。
    ("click_intercepted", ("intercept", "not receive pointer events", "covered")),  # 新增代码+BrowserRecoveryStage7: 匹配点击被遮挡；若没有这行代码，弹窗遮挡无法建议滚动/等待。
    ("stale_element", ("stale", "detached", "element is not attached")),  # 新增代码+BrowserRecoveryStage7: 匹配元素过期；若没有这行代码，动态页面无法建议重新定位。
    ("download_failed", ("download", "save_as", "下载")),  # 新增代码+BrowserRecoveryStage7: 匹配下载失败；若没有这行代码，下载产物问题无法分类。
    ("permission_denied", ("permission", "not allowed", "未授权", "拒绝")),  # 新增代码+BrowserRecoveryStage7: 匹配权限拒绝；若没有这行代码，站点授权问题无法分类。
)  # 新增代码+BrowserRecoveryStage7: 结束错误映射；若没有这行代码，Python 语法无法闭合。

RECOVERY_STRATEGIES = {  # 新增代码+BrowserRecoveryStage7: 定义错误类型到恢复策略的映射；若没有这行代码，分类后仍不知道怎么做。
    "chrome_disconnected": "reconnect_real_chrome",  # 新增代码+BrowserRecoveryStage7: Chrome 断连建议重连；若没有这行代码，真实浏览器掉线无法恢复。
    "page_closed": "reopen_or_new_page",  # 新增代码+BrowserRecoveryStage7: 页面关闭建议重开；若没有这行代码，关闭页后只能重跑任务。
    "context_closed": "restart_browser_session",  # 新增代码+BrowserRecoveryStage7: 上下文关闭建议重启会话；若没有这行代码，多页失效无法恢复。
    "navigation_timeout": "reload_then_observe",  # 新增代码+BrowserRecoveryStage7: 导航超时建议刷新后观察；若没有这行代码，慢页面无自救路径。
    "network_idle_timeout": "domcontentloaded_then_observe",  # 新增代码+BrowserRecoveryStage7: networkidle 超时降级 DOM 就绪；若没有这行代码，现代网站长连接会误失败。
    "locator_not_found": "refresh_observation_then_relocate",  # 新增代码+BrowserRecoveryStage7: 定位失败建议重新观察；若没有这行代码，动态 DOM 过期无法自愈。
    "click_intercepted": "scroll_wait_then_retry",  # 新增代码+BrowserRecoveryStage7: 点击遮挡建议滚动/等待；若没有这行代码，弹窗或懒加载会卡住。
    "stale_element": "refresh_observation_then_relocate",  # 新增代码+BrowserRecoveryStage7: 元素过期建议重新定位；若没有这行代码，SPA 页面容易失败。
    "download_failed": "retry_download_with_unique_path",  # 新增代码+BrowserRecoveryStage7: 下载失败建议唯一路径重试；若没有这行代码，同名文件冲突无法恢复。
    "permission_denied": "request_site_or_tool_permission",  # 新增代码+BrowserRecoveryStage7: 权限失败建议显式授权；若没有这行代码，安全边界会变成隐式失败。
    "unknown": "observe_and_stop_for_review",  # 新增代码+BrowserRecoveryStage7: 未知错误保守观察后停止；若没有这行代码，未知问题可能无限重试。
}  # 新增代码+BrowserRecoveryStage7: 结束策略映射；若没有这行代码，Python 语法无法闭合。


def classify_browser_error(error_text: Any) -> str:  # 新增代码+BrowserRecoveryStage7: 把浏览器异常文本归一化为错误类型；若没有这行代码，恢复策略无法稳定选择。
    lowered = str(error_text).lower()  # 新增代码+BrowserRecoveryStage7: 小写错误文本便于匹配；若没有这行代码，大小写变化会漏判。
    for error_type, markers in ERROR_PATTERNS:  # 新增代码+BrowserRecoveryStage7: 遍历已知错误模式；若没有这行代码，分类不会执行。
        if any(marker in lowered for marker in markers):  # 新增代码+BrowserRecoveryStage7: 任一关键词命中即分类；若没有这行代码，错误文本无法映射。
            return error_type  # 新增代码+BrowserRecoveryStage7: 返回标准错误类型；若没有这行代码，调用方拿不到分类。
    return "unknown"  # 新增代码+BrowserRecoveryStage7: 未匹配时返回 unknown；若没有这行代码，未知错误没有保守策略。


class BrowserRecoveryManager:  # 新增代码+BrowserRecoveryStage7: 管理恢复策略和重试预算；若没有这个类，恢复会无限或散落。
    def __init__(self, max_attempts_per_error: int = 2) -> None:  # 新增代码+BrowserRecoveryStage7: 初始化每类错误最大尝试次数；若没有这行代码，调用方无法配置预算。
        self.max_attempts_per_error = max(0, int(max_attempts_per_error))  # 新增代码+BrowserRecoveryStage7: 保存非负预算；若没有这行代码，负数会让预算语义混乱。
        self.attempts: Counter[tuple[str, str]] = Counter()  # 新增代码+BrowserRecoveryStage7: 统计 action/error 组合次数；若没有这行代码，预算无法按错误隔离。

    def plan_recovery(self, action_id: str, error_text: Any) -> dict[str, Any]:  # 新增代码+BrowserRecoveryStage7: 为一次失败生成恢复计划；若没有这行代码，执行器不知道下一步该做什么。
        error_type = classify_browser_error(error_text)  # 新增代码+BrowserRecoveryStage7: 分类错误；若没有这行代码，策略映射没有输入。
        key = (str(action_id), error_type)  # 新增代码+BrowserRecoveryStage7: 构造预算键；若没有这行代码，不同动作会互相消耗预算。
        self.attempts[key] += 1  # 新增代码+BrowserRecoveryStage7: 记录本次恢复尝试；若没有这行代码，预算不会推进。
        allowed = self.attempts[key] <= self.max_attempts_per_error  # 新增代码+BrowserRecoveryStage7: 判断是否仍在预算内；若没有这行代码，恢复可能无限执行。
        strategy = RECOVERY_STRATEGIES.get(error_type, RECOVERY_STRATEGIES["unknown"])  # 新增代码+BrowserRecoveryStage7: 读取恢复策略；若没有这行代码，分类后没有行动建议。
        return {"allowed": allowed, "error_type": error_type, "strategy": strategy if allowed else "stop_for_review", "attempt": self.attempts[key], "max_attempts": self.max_attempts_per_error, "reason": "allowed" if allowed else "retry budget exhausted"}  # 新增代码+BrowserRecoveryStage7: 返回结构化计划；若没有这行代码，调用方无法审计恢复决策。
