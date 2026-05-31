# 新增代码+BrowserSplit: browser 包用于承载真实浏览器意图识别、Chrome harness、客户模式授权和搜索流程；如果没有这个包，真实浏览器 bug 会继续散落在主文件里。
from .artifacts import safe_browser_artifact_path, sanitized_artifact_filename  # 新增代码+BrowserSplit: 导出浏览器产物安全路径 helper；如果没有这行代码，截图文件名安全逻辑仍只能从旧 server 内部复用。
from .harness import build_real_browser_task_harness_message  # 新增代码+BrowserSplit: 导出真实浏览器任务 harness 构造器；如果没有这行代码，主 agent 仍要自己拼长规则文本。
from .intent import detect_real_browser_information_task, detect_real_chrome_intent, independent_browser_tool_names, real_chrome_request_blocks_independent_browser  # 新增代码+BrowserSplit: 导出真实浏览器意图和独立浏览器阻断 helper；如果没有这行代码，工具策略仍依赖主文件内部实现。
from .permissions import customer_mode_can_auto_approve_terminal_permission, real_browser_customer_auto_approve_reason, real_browser_customer_mode_active, real_browser_customer_progress_message  # 新增代码+BrowserSplit: 导出客户模式授权 helper；如果没有这行代码，终端和 MCP 授权仍会重复写白名单。
from .search_workflow import GOOGLE_URL_PREFIXES, REAL_BROWSER_ALWAYS_ALLOWED_TOOL_NAMES, REAL_BROWSER_FINAL_ACTION_NAMES, google_url_allowed  # 新增代码+BrowserSplit: 导出搜索流程常量和 URL 白名单；如果没有这行代码，Google 搜索流程规则没有统一入口。

__all__ = [  # 新增代码+BrowserSplit: 明确 browser 包公开 API；如果没有这行代码，外部 agent 难以快速判断这个包哪些名字可以稳定使用。
    "GOOGLE_URL_PREFIXES",  # 新增代码+BrowserSplit: 公开 Google URL 前缀常量；如果没有这行代码，授权测试无法从包入口读取白名单。
    "REAL_BROWSER_ALWAYS_ALLOWED_TOOL_NAMES",  # 新增代码+BrowserSplit: 公开客户模式固定工具白名单；如果没有这行代码，授权边界不便于测试和审计。
    "REAL_BROWSER_FINAL_ACTION_NAMES",  # 新增代码+BrowserSplit: 公开最终答案必须声明的浏览器动作名；如果没有这行代码，harness 验收字段会缺少统一来源。
    "build_real_browser_task_harness_message",  # 新增代码+BrowserSplit: 公开 harness 文本构造函数；如果没有这行代码，主入口无法稳定委托。
    "customer_mode_can_auto_approve_terminal_permission",  # 新增代码+BrowserSplit: 公开终端启动权限自动授权判断；如果没有这行代码，真实场景仍会在 MCP 启动时反复问 y/N。
    "detect_real_browser_information_task",  # 新增代码+BrowserSplit: 公开信息查询类真实浏览器任务识别；如果没有这行代码，外部验收无法单测自然短 prompt。
    "detect_real_chrome_intent",  # 新增代码+BrowserSplit: 公开真实 Chrome 意图识别；如果没有这行代码，工具策略无法复用同一判断。
    "google_url_allowed",  # 新增代码+BrowserSplit: 公开 Google URL 白名单判断；如果没有这行代码，browser_open 的安全放行规则会分散。
    "independent_browser_tool_names",  # 新增代码+BrowserSplit: 公开独立浏览器工具集合；如果没有这行代码，真实 Chrome 前置阻断测试缺少来源。
    "real_browser_customer_auto_approve_reason",  # 新增代码+BrowserSplit: 公开 MCP 工具客户模式授权原因函数；如果没有这行代码，执行层仍要手写白名单分支。
    "real_browser_customer_mode_active",  # 新增代码+BrowserSplit: 公开客户模式是否激活的判断；如果没有这行代码，多个入口会重复拼条件。
    "real_browser_customer_progress_message",  # 新增代码+BrowserSplit: 公开客户可见进度文案函数；如果没有这行代码，真实浏览器动作提示无法统一。
    "real_chrome_request_blocks_independent_browser",  # 新增代码+BrowserSplit: 公开真实 Chrome 请求阻断独立浏览器判断；如果没有这行代码，工具池策略仍难以复用。
    "safe_browser_artifact_path",  # 新增代码+BrowserSplit: 公开浏览器产物安全路径函数；如果没有这行代码，截图路径安全逻辑无法被测试复用。
    "sanitized_artifact_filename",  # 新增代码+BrowserSplit: 公开浏览器产物文件名清洗函数；如果没有这行代码，文件名规则无法独立验证。
]  # 新增代码+BrowserSplit: 结束公开 API 列表；如果没有这行代码，Python 列表语法无法闭合。
