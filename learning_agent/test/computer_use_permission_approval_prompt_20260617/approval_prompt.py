"""Computer Use MCP v2 授权审批提示构造器。"""  # 新增代码+PermissionApprovalPrompt：说明本文件只负责生成用户可见授权提示；如果没有这行代码，权限提示逻辑会继续散落在 request_access 中。
from __future__ import annotations  # 新增代码+PermissionApprovalPrompt：延迟解析类型注解；如果没有这行代码，后续前向类型扩展更容易导入失败。

import json  # 新增代码+PermissionApprovalPrompt：导入 JSON 用于稳定格式化授权范围；如果没有这行代码，prompt 内容可能变成不可读的 Python repr。
from typing import Any  # 新增代码+PermissionApprovalPrompt：导入通用 JSON 类型；如果没有这行代码，apps 和 warnings 的嵌套结构类型不清楚。


def build_computer_use_approval_prompt(apps: list[dict[str, str]], applications: list[str], grant_flags: dict[str, bool], sentinel_warnings: list[dict[str, Any]], reason: str) -> str:  # 新增代码+PermissionApprovalPrompt：函数段开始，生成 ClaudeCode-compatible 授权提示；如果没有这段函数，request_access 会继续手写 JSON 字符串。
    payload: dict[str, Any] = {  # 新增代码+PermissionApprovalPrompt：创建提示 payload；如果没有这行代码，授权提示无法稳定包含多类字段。
        "apps": [dict(app) for app in apps],  # 新增代码+PermissionApprovalPrompt：复制 ClaudeCode app 对象；如果没有这行代码，用户看不到 bundleId/displayName 等新字段。
        "applications": list(applications),  # 新增代码+PermissionApprovalPrompt：保留旧 applications 字符串列表；如果没有这行代码，旧提示语义会被新字段完全替代。
        "grantFlags": dict(grant_flags),  # 新增代码+PermissionApprovalPrompt：复制细粒度授权开关；如果没有这行代码，用户看不到剪贴板和系统组合键权限。
        "sentinelWarnings": [dict(warning) for warning in sentinel_warnings],  # 新增代码+PermissionApprovalPrompt：复制高风险应用提示；如果没有这行代码，shell/文件系统/系统设置风险不会显示。
        "reason": str(reason or ""),  # 新增代码+PermissionApprovalPrompt：保存授权申请原因；如果没有这行代码，用户不知道为什么要批准 Computer Use。
    }  # 新增代码+PermissionApprovalPrompt：提示 payload 字典结束；如果没有这行代码，Python 字典语法不完整。
    return "Computer Use v2 请求控制应用：\n" + json.dumps(payload, ensure_ascii=False, indent=2)  # 新增代码+PermissionApprovalPrompt：返回中文标题加格式化 JSON；如果没有这行代码，ask_permission 没有可读提示文本。
# 新增代码+PermissionApprovalPrompt：函数段结束，build_computer_use_approval_prompt 到此结束；如果没有这个边界说明，用户不容易看出审批提示构造范围。
