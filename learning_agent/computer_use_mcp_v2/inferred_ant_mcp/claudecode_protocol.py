"""ClaudeCode Computer Use 可观察协议常量。"""  # 新增代码+ClaudeCodeProtocolParity：集中保存 ClaudeCode 风格字段名；如果没有这行代码，schema、normalizer 和测试会各自手写常量。
from __future__ import annotations  # 新增代码+ClaudeCodeProtocolParity：延迟解析类型注解；如果没有这行代码，后续扩展前向类型时更容易导入卡住。

from copy import deepcopy  # 新增代码+ClaudeCodeProtocolParity：导入深拷贝用于返回默认 grant flags；如果没有这行代码，调用方可能改坏全局默认值。
from typing import Any  # 新增代码+ClaudeCodeProtocolParity：导入通用 JSON 类型；如果没有这行代码，协议 helper 的输入输出边界不清楚。

CLAUDECODE_COORDINATE_FIELD = "coordinate"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 坐标字段名；如果没有这行代码，点击和移动工具会继续以 x/y 为主。
CLAUDECODE_START_COORDINATE_FIELD = "start_coordinate"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 拖拽起点字段名；如果没有这行代码，拖拽 schema 会和 ClaudeCode 展示层不一致。
CLAUDECODE_REGION_FIELD = "region"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 局部区域字段名；如果没有这行代码，zoom 会继续以 x/y/width/height 为主。
CLAUDECODE_BUNDLE_ID_FIELD = "bundle_id"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 应用身份字段名；如果没有这行代码，open_application 会继续只暴露 app_name。
CLAUDECODE_APPS_FIELD = "apps"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 授权应用列表字段名；如果没有这行代码，request_access 会继续只暴露 applications。
CLAUDECODE_ACTIONS_FIELD = "actions"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 批量步骤字段名；如果没有这行代码，computer_batch 会和旧 steps 字段混淆。
CLAUDECODE_GRANT_FLAGS_FIELD = "grantFlags"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 授权开关字段名；如果没有这行代码，剪贴板和系统组合键授权无法用同一结构表达。
CLAUDECODE_DISPLAY_NAME_FIELD = "displayName"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 应用展示名字段；如果没有这行代码，授权 UI/审计无法稳定显示应用名。
CLAUDECODE_BUNDLE_ID_CAMEL_FIELD = "bundleId"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode app 对象内 bundleId 字段；如果没有这行代码，apps 对象和 open_application 字段会互相漂移。
CLAUDECODE_TEXT_FIELD = "text"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 按键展示字段名；如果没有这行代码，key/hold_key 仍只能靠 keys 数组。
CLAUDECODE_DURATION_FIELD = "duration"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 按住时长字段名；如果没有这行代码，hold_key 会继续只接受 duration_seconds。
CLAUDECODE_DIRECTION_FIELD = "direction"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 滚动方向字段名；如果没有这行代码，scroll 会继续只接受 delta_y。
CLAUDECODE_AMOUNT_FIELD = "amount"  # 新增代码+ClaudeCodeProtocolParity：定义 ClaudeCode 滚动数量字段名；如果没有这行代码，scroll 无法按 ClaudeCode 风格表达滚动距离。

CLAUDECODE_DEFAULT_GRANT_FLAGS = {  # 新增代码+ClaudeCodeProtocolParity：声明 ClaudeCode 风格授权开关默认值；如果没有这段常量，request_access/list_granted 会返回不稳定字段。
    "clipboardRead": False,  # 新增代码+ClaudeCodeProtocolParity：默认不允许读取剪贴板；如果没有这一行，权限模型可能默认放开敏感读取。
    "clipboardWrite": False,  # 新增代码+ClaudeCodeProtocolParity：默认不允许写入剪贴板；如果没有这一行，权限模型可能默认放开敏感写入。
    "systemKeyCombos": False,  # 新增代码+ClaudeCodeProtocolParity：默认不允许系统级组合键；如果没有这一行，Alt+Tab 等高风险按键无法单独授权。
}  # 新增代码+ClaudeCodeProtocolParity：默认授权开关字典结束；如果没有这行代码，Python 字典语法不完整。

CLAUDECODE_DEFERS_LOCK_TOOLS = {  # 新增代码+ClaudeCodeProtocolParity：声明只检查锁但不获取锁的工具；如果没有这组常量，request/list 会过早占用桌面锁。
    "request_access",  # 新增代码+ClaudeCodeProtocolParity：授权申请只应检查锁；如果没有这一项，请求权限可能错误占用 Computer Use 独占锁。
    "list_granted_applications",  # 新增代码+ClaudeCodeProtocolParity：授权查询只应检查锁；如果没有这一项，读状态也会错误抢锁。
}  # 新增代码+ClaudeCodeProtocolParity：延迟获取锁工具集合结束；如果没有这行代码，Python 集合语法不完整。

WINDOWS_SENTINEL_APP_NAMES = {  # 新增代码+ClaudeCodeProtocolParity：声明 Windows 高风险应用分类；如果没有这段常量，权限提示无法复刻 ClaudeCode sentinel 风险提醒。
    "shell": {"cmd.exe", "powershell.exe", "pwsh.exe", "windows terminal", "wt.exe"},  # 新增代码+ClaudeCodeProtocolParity：标记 shell 类应用；如果没有这一行，命令终端风险会被普通应用提示掩盖。
    "filesystem": {"explorer.exe"},  # 新增代码+ClaudeCodeProtocolParity：标记文件系统类应用；如果没有这一行，资源管理器读写文件风险无法提示。
    "system_settings": {"control.exe", "systemsettings.exe", "regedit.exe"},  # 新增代码+ClaudeCodeProtocolParity：标记系统设置类应用；如果没有这一行，控制面板和注册表风险无法提示。
}  # 新增代码+ClaudeCodeProtocolParity：Windows sentinel 分类结束；如果没有这行代码，Python 字典语法不完整。


def default_grant_flags() -> dict[str, bool]:  # 新增代码+ClaudeCodeProtocolParity：函数段开始，返回授权开关默认副本；如果没有这段函数，调用方可能共享并污染全局字典。
    return deepcopy(CLAUDECODE_DEFAULT_GRANT_FLAGS)  # 新增代码+ClaudeCodeProtocolParity：返回深拷贝默认值；如果没有这行代码，某次授权会影响后续会话默认值。
# 新增代码+ClaudeCodeProtocolParity：函数段结束，default_grant_flags 到此结束；如果没有这个边界说明，用户不容易看出默认授权来源。


def normalize_app_identity(raw_app: Any) -> dict[str, str]:  # 新增代码+ClaudeCodeProtocolParity：函数段开始，把字符串或对象应用描述统一成 ClaudeCode app 对象；如果没有这段函数，request_access 会同时处理多种松散形状。
    if isinstance(raw_app, dict):  # 新增代码+ClaudeCodeProtocolParity：先处理 ClaudeCode 风格 app 对象；如果没有这行代码，displayName/bundleId 会被当成普通字符串丢失。
        display_name = str(raw_app.get(CLAUDECODE_DISPLAY_NAME_FIELD) or raw_app.get("display_name") or raw_app.get("name") or raw_app.get(CLAUDECODE_BUNDLE_ID_CAMEL_FIELD) or raw_app.get(CLAUDECODE_BUNDLE_ID_FIELD) or "").strip()  # 新增代码+ClaudeCodeProtocolParity：提取用户可读应用名；如果没有这行代码，授权提示可能没有应用显示名。
        bundle_id = str(raw_app.get(CLAUDECODE_BUNDLE_ID_CAMEL_FIELD) or raw_app.get(CLAUDECODE_BUNDLE_ID_FIELD) or raw_app.get("app_id") or display_name).strip()  # 新增代码+ClaudeCodeProtocolParity：提取应用身份；如果没有这行代码，授权状态无法稳定匹配应用。
        return {CLAUDECODE_DISPLAY_NAME_FIELD: display_name or bundle_id, CLAUDECODE_BUNDLE_ID_CAMEL_FIELD: bundle_id or display_name}  # 新增代码+ClaudeCodeProtocolParity：返回 ClaudeCode app 对象；如果没有这行代码，权限层拿不到规范化结果。
    text = str(raw_app or "").strip()  # 新增代码+ClaudeCodeProtocolParity：把旧字符串应用名清理成文本；如果没有这行代码，旧 applications 列表无法兼容。
    return {CLAUDECODE_DISPLAY_NAME_FIELD: text, CLAUDECODE_BUNDLE_ID_CAMEL_FIELD: text}  # 新增代码+ClaudeCodeProtocolParity：把字符串同时作为展示名和身份；如果没有这行代码，旧 prompt 会丢应用目标。
# 新增代码+ClaudeCodeProtocolParity：函数段结束，normalize_app_identity 到此结束；如果没有这个边界说明，用户不容易看出 app 规范化范围。


def sentinel_warning_for_app(app: dict[str, str]) -> dict[str, str] | None:  # 新增代码+ClaudeCodeProtocolParity：函数段开始，按 Windows app 身份生成风险提示；如果没有这段函数，权限结果无法提示 shell/file/system_settings 风险。
    bundle_id = str(app.get(CLAUDECODE_BUNDLE_ID_CAMEL_FIELD, "") or "").lower().strip()  # 新增代码+ClaudeCodeProtocolParity：读取小写应用身份；如果没有这行代码，大小写不同的 exe 无法命中风险分类。
    display_name = str(app.get(CLAUDECODE_DISPLAY_NAME_FIELD, "") or "").lower().strip()  # 新增代码+ClaudeCodeProtocolParity：读取小写展示名；如果没有这行代码，Windows Terminal 这类展示名无法命中。
    for category, names in WINDOWS_SENTINEL_APP_NAMES.items():  # 新增代码+ClaudeCodeProtocolParity：遍历风险分类；如果没有这行代码，sentinel 名单不会被使用。
        if bundle_id in names or display_name in names:  # 新增代码+ClaudeCodeProtocolParity：检查身份或展示名是否命中；如果没有这行代码，高风险应用不会被标记。
            return {"category": category, CLAUDECODE_DISPLAY_NAME_FIELD: app.get(CLAUDECODE_DISPLAY_NAME_FIELD, ""), CLAUDECODE_BUNDLE_ID_CAMEL_FIELD: app.get(CLAUDECODE_BUNDLE_ID_CAMEL_FIELD, "")}  # 新增代码+ClaudeCodeProtocolParity：返回 ClaudeCode 风格风险摘要；如果没有这行代码，用户看不到具体风险来源。
    return None  # 新增代码+ClaudeCodeProtocolParity：普通应用没有风险提示；如果没有这行代码，函数可能隐式返回 None 不够清楚。
# 新增代码+ClaudeCodeProtocolParity：函数段结束，sentinel_warning_for_app 到此结束；如果没有这个边界说明，用户不容易看出风险分类范围。
