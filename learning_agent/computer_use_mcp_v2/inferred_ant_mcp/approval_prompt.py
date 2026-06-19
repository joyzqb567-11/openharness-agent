"""Computer Use MCP v2 授权审批提示构造器。"""  # 修改代码+PermissionUIPrompt：说明本文件只负责生成用户可读权限 UI；如果没有这行代码，权限提示职责会继续混在 request_access 里。
from __future__ import annotations  # 修改代码+PermissionUIPrompt：延迟解析类型注解；如果没有这行代码，后续前向类型扩展更容易导入失败。

from typing import Any  # 修改代码+PermissionUIPrompt：导入通用 JSON 类型；如果没有这行代码，apps、flags 和 warnings 的嵌套结构类型不清楚。


PROMPT_REASON_LIMIT = 240  # 新增代码+PermissionUIPrompt：限制授权原因最大显示长度；如果没有这行代码，模型可能用超长 reason 刷屏真实终端。

GRANT_FLAG_LABELS = {  # 新增代码+PermissionUIPrompt：定义 grant flags 的中文展示名；如果没有这段字典，用户只能看到不易理解的英文内部字段。
    "clipboardRead": "读取剪贴板",  # 新增代码+PermissionUIPrompt：说明 clipboardRead 的用户含义；如果没有这一行，读取剪贴板风险不够直观。
    "clipboardWrite": "写入剪贴板",  # 新增代码+PermissionUIPrompt：说明 clipboardWrite 的用户含义；如果没有这一行，写入剪贴板风险不够直观。
    "systemKeyCombos": "系统组合键",  # 新增代码+PermissionUIPrompt：说明 systemKeyCombos 的用户含义；如果没有这一行，Alt+Tab 等高风险按键不够直观。
}  # 新增代码+PermissionUIPrompt：grant flags 中文展示名字典结束；如果没有这行代码，Python 字典语法不完整。

SENTINEL_RISK_TEXT = {  # 新增代码+PermissionUIPrompt：定义高风险分类的中文解释；如果没有这段字典，PowerShell 等只会显示英文分类。
    "shell": "shell，可以运行命令、修改文件、启动程序",  # 新增代码+PermissionUIPrompt：解释 shell 风险；如果没有这一行，用户不知道终端类应用为什么危险。
    "filesystem": "文件系统，可以浏览、打开、移动或删除文件",  # 新增代码+PermissionUIPrompt：解释文件系统风险；如果没有这一行，用户不知道资源管理器为什么危险。
    "system_settings": "系统设置或注册表，可能改变 Windows 配置",  # 新增代码+PermissionUIPrompt：解释系统设置风险；如果没有这一行，用户不知道注册表为什么危险。
}  # 新增代码+PermissionUIPrompt：高风险分类解释字典结束；如果没有这行代码，Python 字典语法不完整。

SENTINEL_ADVICE_TEXT = {  # 新增代码+PermissionUIPrompt：定义高风险分类的用户建议；如果没有这段字典，提示只能描述风险但不给决策建议。
    "shell": "除非你明确知道 agent 要执行什么命令，否则建议拒绝。",  # 新增代码+PermissionUIPrompt：给 shell 风险建议；如果没有这一行，用户可能轻易批准命令终端。
    "filesystem": "除非任务确实需要管理文件，否则建议先改用受控测试文件或拒绝。",  # 新增代码+PermissionUIPrompt：给文件系统风险建议；如果没有这一行，用户可能把私有文件暴露给桌面自动化。
    "system_settings": "除非你明确要修改系统配置，否则建议拒绝。",  # 新增代码+PermissionUIPrompt：给系统设置风险建议；如果没有这一行，用户可能误批准注册表或控制面板操作。
}  # 新增代码+PermissionUIPrompt：高风险建议字典结束；如果没有这行代码，Python 字典语法不完整。


def _safe_text(value: Any, limit: int = PROMPT_REASON_LIMIT) -> str:  # 新增代码+PermissionUIPrompt：函数段开始，清理并裁剪用户可见文本；如果没有这段函数，超长 reason 或奇怪对象会污染权限 UI。
    text = str(value or "").strip()  # 新增代码+PermissionUIPrompt：把输入转成去空白文本；如果没有这行代码，None 或对象 repr 可能直接进入终端。
    if len(text) <= limit:  # 新增代码+PermissionUIPrompt：检查文本是否在安全长度内；如果没有这行代码，短文本也会被不必要地裁剪。
        return text  # 新增代码+PermissionUIPrompt：短文本原样返回；如果没有这行代码，正常申请原因会丢失。
    return text[:limit].rstrip() + "...（已截断）"  # 新增代码+PermissionUIPrompt：裁剪长文本并明确标注；如果没有这行代码，用户不知道权限原因被缩短。
# 新增代码+PermissionUIPrompt：函数段结束，_safe_text 到此结束；如果没有这个边界说明，用户不容易看出文本清理范围。


def _flag_value_text(value: bool) -> str:  # 新增代码+PermissionUIPrompt：函数段开始，把布尔值转成中文是否；如果没有这段函数，UI 会混用 True/False 和中文。
    return "是" if bool(value) else "否"  # 新增代码+PermissionUIPrompt：返回用户容易理解的是/否；如果没有这行代码，危险权限状态不够直观。
# 新增代码+PermissionUIPrompt：函数段结束，_flag_value_text 到此结束；如果没有这个边界说明，用户不容易看出布尔展示范围。


def _warning_key(value: dict[str, Any]) -> tuple[str, str]:  # 新增代码+PermissionUIPrompt：函数段开始，生成 sentinel warning 匹配 key；如果没有这段函数，风险提示和应用行难以对应。
    display_name = str(value.get("displayName", "") or "").lower().strip()  # 新增代码+PermissionUIPrompt：读取小写展示名；如果没有这行代码，按显示名匹配风险会失败。
    bundle_id = str(value.get("bundleId", "") or "").lower().strip()  # 新增代码+PermissionUIPrompt：读取小写应用身份；如果没有这行代码，按 exe 身份匹配风险会失败。
    return display_name, bundle_id  # 新增代码+PermissionUIPrompt：返回稳定匹配 key；如果没有这行代码，调用方拿不到匹配结果。
# 新增代码+PermissionUIPrompt：函数段结束，_warning_key 到此结束；如果没有这个边界说明，用户不容易看出 warning 匹配范围。


def _warning_for_app(app: dict[str, str], sentinel_warnings: list[dict[str, Any]]) -> dict[str, Any] | None:  # 新增代码+PermissionUIPrompt：函数段开始，为某个应用找到风险提示；如果没有这段函数，应用列表里的风险只能显示普通。
    app_key = _warning_key(app)  # 新增代码+PermissionUIPrompt：生成应用匹配 key；如果没有这行代码，后续无法比较展示名和身份。
    for warning in sentinel_warnings:  # 新增代码+PermissionUIPrompt：遍历高风险提示；如果没有这行代码，sentinelWarnings 不会被应用到 UI。
        if _warning_key(warning) == app_key:  # 新增代码+PermissionUIPrompt：检查 warning 是否属于当前应用；如果没有这行代码，多个应用的风险可能串行。
            return dict(warning)  # 新增代码+PermissionUIPrompt：返回 warning 副本；如果没有这行代码，调用方可能意外修改原始列表。
    return None  # 新增代码+PermissionUIPrompt：没有风险时返回 None；如果没有这行代码，函数可能隐式返回导致语义不清楚。
# 新增代码+PermissionUIPrompt：函数段结束，_warning_for_app 到此结束；如果没有这个边界说明，用户不容易看出 app 风险匹配范围。


def _risk_text(warning: dict[str, Any] | None) -> str:  # 新增代码+PermissionUIPrompt：函数段开始，把 sentinel warning 转成用户可读风险；如果没有这段函数，风险分类会只剩英文标签。
    if warning is None:  # 新增代码+PermissionUIPrompt：判断是否没有高风险提示；如果没有这行代码，普通应用会被误当成未知风险。
        return "普通桌面应用"  # 新增代码+PermissionUIPrompt：普通应用显示低风险说明；如果没有这行代码，用户看不到普通目标和高风险目标的区别。
    category = str(warning.get("category", "") or "").strip()  # 新增代码+PermissionUIPrompt：读取风险分类；如果没有这行代码，风险说明无法按类型选择。
    return SENTINEL_RISK_TEXT.get(category, f"{category or '未知'} 风险应用")  # 新增代码+PermissionUIPrompt：返回中文风险说明并兜底未知分类；如果没有这行代码，新分类会显示空风险。
# 新增代码+PermissionUIPrompt：函数段结束，_risk_text 到此结束；如果没有这个边界说明，用户不容易看出风险文案生成范围。


def _format_application_rows(apps: list[dict[str, str]], applications: list[str], sentinel_warnings: list[dict[str, Any]]) -> str:  # 新增代码+PermissionUIPrompt：函数段开始，格式化目标应用列表；如果没有这段函数，build 函数会堆满字符串拼接。
    safe_apps = [dict(app) for app in apps]  # 新增代码+PermissionUIPrompt：复制 app 对象列表；如果没有这行代码，后续处理可能修改调用方输入。
    if not safe_apps:  # 新增代码+PermissionUIPrompt：兼容只有旧 applications 的输入；如果没有这行代码，旧调用方会显示空应用。
        safe_apps = [{"displayName": str(name), "bundleId": str(name)} for name in applications]  # 新增代码+PermissionUIPrompt：把旧应用名转成显示对象；如果没有这行代码，旧字段无法进入面板。
    if not safe_apps:  # 新增代码+PermissionUIPrompt：处理完全没有目标应用的情况；如果没有这行代码，列表为空时 UI 会缺一块。
        return "- 未声明具体应用，建议拒绝后让 agent 重新说明目标。"  # 新增代码+PermissionUIPrompt：给缺目标请求安全建议；如果没有这行代码，用户无法判断空授权范围。
    rows: list[str] = []  # 新增代码+PermissionUIPrompt：准备应用行列表；如果没有这行代码，循环结果没有保存位置。
    for index, app in enumerate(safe_apps, start=1):  # 新增代码+PermissionUIPrompt：按序号遍历应用；如果没有这行代码，多个目标无法逐个展示。
        display_name = _safe_text(app.get("displayName") or app.get("name") or app.get("bundleId") or "未命名应用", 80)  # 新增代码+PermissionUIPrompt：生成安全展示名；如果没有这行代码，空名称或过长名称会污染 UI。
        bundle_id = _safe_text(app.get("bundleId") or app.get("bundle_id") or display_name, 120)  # 新增代码+PermissionUIPrompt：生成安全应用身份；如果没有这行代码，用户无法核对 exe 或 bundle 身份。
        warning = _warning_for_app(app, sentinel_warnings)  # 新增代码+PermissionUIPrompt：查找当前应用风险；如果没有这行代码，风险说明无法贴到对应应用。
        rows.append(f"{index}. {display_name}\n   身份: {bundle_id}\n   风险: {_risk_text(warning)}")  # 新增代码+PermissionUIPrompt：写入三行应用摘要；如果没有这行代码，用户看不到目标、身份和风险。
    return "\n".join(rows)  # 新增代码+PermissionUIPrompt：返回应用列表文本；如果没有这行代码，build 函数拿不到面板内容。
# 新增代码+PermissionUIPrompt：函数段结束，_format_application_rows 到此结束；如果没有这个边界说明，用户不容易看出应用列表格式化范围。


def _format_grant_flags(grant_flags: dict[str, bool]) -> str:  # 新增代码+PermissionUIPrompt：函数段开始，格式化危险权限开关；如果没有这段函数，用户只能看到英文 JSON 字段。
    rows: list[str] = []  # 新增代码+PermissionUIPrompt：准备权限行列表；如果没有这行代码，循环结果没有保存位置。
    for flag_name, label in GRANT_FLAG_LABELS.items():  # 新增代码+PermissionUIPrompt：按固定顺序遍历已知权限；如果没有这行代码，权限显示顺序会漂移。
        rows.append(f"- {label} ({flag_name}): {_flag_value_text(bool(grant_flags.get(flag_name, False)))}")  # 新增代码+PermissionUIPrompt：加入中文名、英文名和是否启用；如果没有这行代码，用户看不懂每个 flag 状态。
    return "\n".join(rows)  # 新增代码+PermissionUIPrompt：返回权限列表文本；如果没有这行代码，build 函数拿不到危险权限面板。
# 新增代码+PermissionUIPrompt：函数段结束，_format_grant_flags 到此结束；如果没有这个边界说明，用户不容易看出 grant flag 格式化范围。


def _format_sentinel_warnings(sentinel_warnings: list[dict[str, Any]]) -> str:  # 新增代码+PermissionUIPrompt：函数段开始，格式化高风险应用安全建议；如果没有这段函数，shell/file/system_settings 风险不会单独提醒。
    if not sentinel_warnings:  # 新增代码+PermissionUIPrompt：判断是否没有高风险应用；如果没有这行代码，普通请求也会输出空建议。
        return "安全建议:\n- 未发现 shell、文件系统或系统设置类高风险应用。"  # 新增代码+PermissionUIPrompt：普通场景给出简短安全说明；如果没有这行代码，用户不知道是否有高风险。
    rows = ["安全建议:"]  # 新增代码+PermissionUIPrompt：准备安全建议标题；如果没有这行代码，高风险提示没有明确区域。
    for warning in sentinel_warnings:  # 新增代码+PermissionUIPrompt：逐个格式化风险提示；如果没有这行代码，多个高风险应用只会显示一个或不显示。
        category = str(warning.get("category", "") or "").strip()  # 新增代码+PermissionUIPrompt：读取风险分类；如果没有这行代码，无法选择对应建议。
        display_name = _safe_text(warning.get("displayName") or warning.get("bundleId") or "未知应用", 80)  # 新增代码+PermissionUIPrompt：读取风险应用名；如果没有这行代码，建议不知道指向哪个应用。
        advice = SENTINEL_ADVICE_TEXT.get(category, "请确认任务必要性后再允许。")  # 新增代码+PermissionUIPrompt：读取分类建议并兜底；如果没有这行代码，未知分类没有用户建议。
        rows.append(f"- {display_name}: {_risk_text(warning)}。{advice}")  # 新增代码+PermissionUIPrompt：加入应用风险和建议；如果没有这行代码，用户无法据此决定是否拒绝。
    return "\n".join(rows)  # 新增代码+PermissionUIPrompt：返回安全建议文本；如果没有这行代码，build 函数拿不到高风险区域。
# 新增代码+PermissionUIPrompt：函数段结束，_format_sentinel_warnings 到此结束；如果没有这个边界说明，用户不容易看出 sentinel 建议格式化范围。


def build_computer_use_approval_prompt(apps: list[dict[str, str]], applications: list[str], grant_flags: dict[str, bool], sentinel_warnings: list[dict[str, Any]], reason: str) -> str:  # 修改代码+PermissionUIPrompt：函数段开始，生成 ClaudeCode-compatible 终端授权面板；如果没有这段函数，request_access 会继续把原始 JSON 丢给用户。
    safe_reason = _safe_text(reason) or "agent 未说明申请原因，建议拒绝后要求重新说明。"  # 新增代码+PermissionUIPrompt：生成安全申请原因；如果没有这行代码，空原因或超长原因会降低用户判断质量。
    sections = [  # 新增代码+PermissionUIPrompt：准备面板区块列表；如果没有这行代码，多段文案会散落成难维护字符串。
        "[Computer Use 权限请求]",  # 新增代码+PermissionUIPrompt：面板标题；如果没有这一行，用户无法一眼识别这是桌面控制授权。
        "",  # 新增代码+PermissionUIPrompt：插入空行提升终端可读性；如果没有这一行，标题和正文会挤在一起。
        "Agent 想在本会话中控制以下 Windows 应用:",  # 新增代码+PermissionUIPrompt：说明授权目标范围；如果没有这一行，用户不知道列表含义。
        _format_application_rows(apps, applications, sentinel_warnings),  # 新增代码+PermissionUIPrompt：插入应用、身份和风险列表；如果没有这一行，用户看不到具体目标。
        "",  # 新增代码+PermissionUIPrompt：插入空行分隔应用和权限；如果没有这一行，终端面板不易扫读。
        "本次请求的危险权限:",  # 新增代码+PermissionUIPrompt：标出危险权限区域；如果没有这一行，grant flags 会缺少语境。
        _format_grant_flags(grant_flags),  # 新增代码+PermissionUIPrompt：插入 grant flags 中文说明；如果没有这一行，用户看不懂剪贴板和组合键权限。
        "",  # 新增代码+PermissionUIPrompt：插入空行分隔权限和原因；如果没有这一行，文本会过密。
        "申请原因:",  # 新增代码+PermissionUIPrompt：标出 reason 区域；如果没有这一行，用户不知道下一行是什么。
        safe_reason,  # 新增代码+PermissionUIPrompt：插入裁剪后的申请原因；如果没有这一行，用户不知道为什么要授权。
        "",  # 新增代码+PermissionUIPrompt：插入空行分隔 reason 和建议；如果没有这一行，安全建议不突出。
        _format_sentinel_warnings(sentinel_warnings),  # 新增代码+PermissionUIPrompt：插入高风险安全建议；如果没有这一行，PowerShell 等风险不会被明确提示。
        "",  # 新增代码+PermissionUIPrompt：插入空行分隔建议和选择；如果没有这一行，选择提示不醒目。
        "请选择:",  # 新增代码+PermissionUIPrompt：标出用户选择区域；如果没有这一行，用户不知道下一步该输入什么。
        "y = 允许本会话控制这些应用",  # 新增代码+PermissionUIPrompt：给出允许选项；如果没有这一行，真实终端用户不知道如何批准。
        "n = 拒绝",  # 新增代码+PermissionUIPrompt：给出拒绝选项；如果没有这一行，用户不知道可以拒绝。
    ]  # 新增代码+PermissionUIPrompt：面板区块列表结束；如果没有这行代码，Python 列表语法不完整。
    return "\n".join(sections)  # 修改代码+PermissionUIPrompt：返回完整终端面板；如果没有这行代码，ask_permission 没有可显示文本。
# 修改代码+PermissionUIPrompt：函数段结束，build_computer_use_approval_prompt 到此结束；如果没有这个边界说明，用户不容易看出审批提示构造范围。
