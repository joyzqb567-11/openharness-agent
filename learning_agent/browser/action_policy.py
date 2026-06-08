"""浏览器工具动作策略，区分只读并发动作和必须串行的写动作。"""  # 新增代码+BrowserActionStage6: 说明本模块负责动作并发边界；若没有这行代码，策略用途不清楚。

from __future__ import annotations  # 新增代码+BrowserActionStage6: 延迟解析类型注解；若没有这行代码，类型定义更脆弱。

READ_ONLY_BROWSER_TOOLS = {"browser_snapshot", "browser_screenshot", "browser_console", "browser_network", "browser_tabs", "browser_downloads", "browser_plugin_status", "browser_profile_status", "browser_visual_locate"}  # 新增代码+BrowserActionStage6: 定义可并发读取工具；若没有这行代码，状态读取会被错误串行。
WRITE_BROWSER_TOOLS = {"browser_open", "browser_click", "browser_type", "browser_type_secret", "browser_press_key", "browser_wait", "browser_upload_file", "browser_recover_page", "browser_flow_run", "browser_replay", "browser_launch_visible", "browser_connect_real_chrome", "browser_disconnect_real_chrome", "browser_site_grant", "browser_evaluate"}  # 新增代码+BrowserActionStage6: 定义会改变页面或浏览器状态的工具；若没有这行代码，并发写操作会互相打架。


class BrowserActionPolicy:  # 新增代码+BrowserActionStage6: 浏览器工具并发/安全分类器；若没有这个类，执行器无法统一决策。
    def classify(self, tool_name: str) -> str:  # 新增代码+BrowserActionStage6: 返回 read/write/unknown 分类；若没有这行代码，外部状态无法解释策略。
        normalized = str(tool_name)  # 新增代码+BrowserActionStage6: 规范化工具名；若没有这行代码，None 或非字符串会影响集合查找。
        if normalized in READ_ONLY_BROWSER_TOOLS:  # 新增代码+BrowserActionStage6: 检查只读工具；若没有这行代码，snapshot 等会被误判。
            return "read"  # 新增代码+BrowserActionStage6: 返回只读分类；若没有这行代码，调用方不知道可并发。
        if normalized in WRITE_BROWSER_TOOLS:  # 新增代码+BrowserActionStage6: 检查写工具；若没有这行代码，click/type 可能被并发执行。
            return "write"  # 新增代码+BrowserActionStage6: 返回写分类；若没有这行代码，调用方不知道必须串行。
        return "unknown"  # 新增代码+BrowserActionStage6: 未知工具保守处理；若没有这行代码，新工具可能默认放开。

    def is_concurrent_safe(self, tool_name: str) -> bool:  # 新增代码+BrowserActionStage6: 判断工具是否允许并发；若没有这行代码，执行器每次要自己判断。
        return self.classify(tool_name) == "read"  # 新增代码+BrowserActionStage6: 只有只读工具允许并发；若没有这行代码，写工具可能并发污染页面。

    def requires_serial(self, tool_name: str) -> bool:  # 新增代码+BrowserActionStage6: 判断工具是否需要串行；若没有这行代码，调度器无法加锁。
        return not self.is_concurrent_safe(tool_name)  # 新增代码+BrowserActionStage6: 未知和写工具都保守串行；若没有这行代码，新工具可能被误放开。
