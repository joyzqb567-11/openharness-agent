"""Computer Use MCP v2 授权工具。"""  # 新增代码+ComputerUseMcpV2：说明本文件处理 request_access 和授权状态；如果没有这行代码，权限逻辑会混入动作执行。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，参数类型不清楚。

from .approval_prompt import build_computer_use_approval_prompt  # 新增代码+PermissionApprovalPrompt：导入集中审批提示构造器；如果没有这行代码，request_access 会继续手写 prompt 并难以测试。
from .claudecode_protocol import CLAUDECODE_APPS_FIELD, CLAUDECODE_GRANT_FLAGS_FIELD, default_grant_flags, normalize_app_identity, sentinel_warning_for_app  # 新增代码+ClaudeCodePermissionParity：导入 ClaudeCode 权限字段和风险 helper；如果没有这行代码，权限层会继续只理解旧 applications。
from .errors import error_result  # 新增代码+ComputerUseMcpV2：导入统一失败结果；如果没有这行代码，授权拒绝格式会漂移。
from .result_blocks import success_result  # 新增代码+ComputerUseMcpV2：导入统一成功结果；如果没有这行代码，授权成功格式会漂移。
from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入上下文；如果没有这行代码，权限工具拿不到回调和状态。


def _grant_flags_from_arguments(arguments: dict[str, Any]) -> dict[str, bool]:  # 新增代码+ClaudeCodePermissionParity：函数段开始，合并 ClaudeCode grantFlags 和默认值；如果没有这段函数，授权开关会在 request/list 间漂移。
    flags = default_grant_flags()  # 新增代码+ClaudeCodePermissionParity：从安全默认值开始；如果没有这行代码，缺字段时可能默认放开敏感能力。
    raw_flags = arguments.get(CLAUDECODE_GRANT_FLAGS_FIELD, {})  # 新增代码+ClaudeCodePermissionParity：读取 ClaudeCode grantFlags 输入；如果没有这行代码，模型传入的剪贴板授权会被忽略。
    if isinstance(raw_flags, dict):  # 新增代码+ClaudeCodePermissionParity：只接受对象形态 flags；如果没有这行代码，字符串或列表可能污染授权状态。
        for key in flags:  # 新增代码+ClaudeCodePermissionParity：只允许已知授权开关；如果没有这行代码，未知权限字段会进入状态。
            if key in raw_flags:  # 新增代码+ClaudeCodePermissionParity：检查调用方是否覆盖该开关；如果没有这行代码，所有默认值都会被重写。
                flags[key] = bool(raw_flags.get(key))  # 新增代码+ClaudeCodePermissionParity：保存布尔化授权开关；如果没有这行代码，JSON 中的 truthy/falsy 值无法稳定使用。
    return flags  # 新增代码+ClaudeCodePermissionParity：返回合并后的授权开关；如果没有这行代码，request_access 拿不到 grant flags。
# 新增代码+ClaudeCodePermissionParity：函数段结束，_grant_flags_from_arguments 到此结束；如果没有这个边界说明，用户不容易看出授权开关合并范围。


def _apps_from_arguments(arguments: dict[str, Any]) -> list[dict[str, str]]:  # 新增代码+ClaudeCodePermissionParity：函数段开始，读取并规范化 apps/applications；如果没有这段函数，权限层会重复处理旧新字段。
    raw_apps = arguments.get(CLAUDECODE_APPS_FIELD, arguments.get("applications", []))  # 新增代码+ClaudeCodePermissionParity：优先读取 ClaudeCode apps，兼容旧 applications；如果没有这行代码，旧 prompt 或新 prompt 至少一边会失效。
    return [normalize_app_identity(app) for app in list(raw_apps or [])]  # 新增代码+ClaudeCodePermissionParity：返回规范化 app 对象列表；如果没有这行代码，后续状态会混合字符串和对象。
# 新增代码+ClaudeCodePermissionParity：函数段结束，_apps_from_arguments 到此结束；如果没有这个边界说明，用户不容易看出 app 读取范围。


def _permission_payload(context: ComputerUseMcpV2Context, reason: str, granted: bool) -> dict[str, Any]:  # 新增代码+ClaudeCodePermissionParity：函数段开始，生成 ClaudeCode-compatible 权限结果；如果没有这段函数，request/list 会返回不同形状。
    applications = [app.get("displayName", "") for app in context.allowed_apps]  # 新增代码+ClaudeCodePermissionParity：生成旧 applications 兼容列表；如果没有这行代码，历史调用方无法读取授权应用名。
    return {"allowedApps": list(context.allowed_apps), "applications": applications, "grantFlags": dict(context.grant_flags), "sentinelWarnings": list(context.sentinel_warnings), "deniedApps": list(context.denied_apps), "reason": reason, "granted": bool(granted), "grants": dict(context.grants)}  # 新增代码+ClaudeCodePermissionParity：返回新旧字段并存的权限摘要；如果没有这行代码，模型和旧 adapter 会各读一套不一致结果。
# 新增代码+ClaudeCodePermissionParity：函数段结束，_permission_payload 到此结束；如果没有这个边界说明，用户不容易看出权限返回结构范围。


def request_access(context: ComputerUseMcpV2Context, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，执行授权申请；如果没有这段函数，模型无法通过 v2 请求权限。
    apps = _apps_from_arguments(arguments)  # 修改代码+ClaudeCodePermissionParity：读取 ClaudeCode apps 并兼容旧 applications；如果没有这行代码，app allowlist 无法保存 bundleId/displayName。
    applications = [app.get("displayName", "") for app in apps]  # 修改代码+ClaudeCodePermissionParity：生成旧 applications 字符串列表；如果没有这行代码，旧回调和审计会丢应用名。
    grant_flags = _grant_flags_from_arguments(arguments)  # 新增代码+ClaudeCodePermissionParity：读取细粒度授权开关；如果没有这行代码，剪贴板和系统组合键权限无法表达。
    sentinel_warnings = [warning for warning in (sentinel_warning_for_app(app) for app in apps) if warning is not None]  # 新增代码+ClaudeCodePermissionParity：生成高风险应用提示；如果没有这行代码，PowerShell 等风险不会提示。
    reason = str(arguments.get("reason", "") or "")  # 新增代码+ComputerUseMcpV2：读取申请原因；如果没有这行代码，用户无法知道为什么要授权。
    prompt = build_computer_use_approval_prompt(apps=apps, applications=applications, grant_flags=grant_flags, sentinel_warnings=sentinel_warnings, reason=reason)  # 修改代码+PermissionApprovalPrompt：生成包含 allowlist、flags 和风险提示的授权提示；如果没有这行代码，用户看不到完整授权范围。
    allowed = bool(context.ask_permission(prompt)) if callable(context.ask_permission) else True  # 新增代码+ComputerUseMcpV2：调用 agent 权限回调或独立模式默认记录；如果没有这行代码，授权无法进入主循环确认。
    if not allowed:  # 新增代码+ComputerUseMcpV2：检查用户是否拒绝；如果没有这行代码，拒绝也会被当成授权。
        context.denied_apps = apps  # 新增代码+ClaudeCodePermissionParity：保存被拒绝应用；如果没有这行代码，拒绝审计无法知道用户拒绝了哪些目标。
        result = error_result("request_access", "user_denied_computer_use_v2_access", error_class="permission_denied")  # 修改代码+ClaudeCodePermissionParity：返回权限拒绝结果；如果没有这行代码，模型不知道授权没有成功。
        result["payload"] = {"deniedApps": list(context.denied_apps), "sentinelWarnings": sentinel_warnings, "reason": reason}  # 新增代码+ClaudeCodePermissionParity：给拒绝结果附加 ClaudeCode-compatible payload；如果没有这行代码，调用方无法读取拒绝目标。
        return result  # 新增代码+ClaudeCodePermissionParity：返回带 payload 的拒绝结果；如果没有这行代码，函数会继续保存授权。
    context.allowed_apps = apps  # 新增代码+ClaudeCodePermissionParity：保存 ClaudeCode 风格 app allowlist；如果没有这行代码，list_granted_applications 无法返回 allowedApps。
    context.grant_flags = grant_flags  # 新增代码+ClaudeCodePermissionParity：保存细粒度授权开关；如果没有这行代码，后续剪贴板/组合键无法检查授权。
    context.sentinel_warnings = sentinel_warnings  # 新增代码+ClaudeCodePermissionParity：保存风险提示；如果没有这行代码，授权查询无法提示 shell/system settings 风险。
    context.denied_apps = []  # 新增代码+ClaudeCodePermissionParity：授权成功时清空拒绝列表；如果没有这行代码，旧拒绝状态可能污染当前授权。
    context.grants["applications"] = applications  # 新增代码+ComputerUseMcpV2：保存授权应用摘要；如果没有这行代码，list_granted_applications 看不到授权范围。
    context.grants["allowedApps"] = list(context.allowed_apps)  # 新增代码+ClaudeCodePermissionParity：在旧 grants 中保存 allowedApps；如果没有这行代码，旧读取方拿不到 ClaudeCode app 对象。
    context.grants["grantFlags"] = dict(context.grant_flags)  # 新增代码+ClaudeCodePermissionParity：在旧 grants 中保存 grantFlags；如果没有这行代码，旧读取方拿不到细粒度授权。
    context.grants["sentinelWarnings"] = list(context.sentinel_warnings)  # 新增代码+ClaudeCodePermissionParity：在旧 grants 中保存风险提示；如果没有这行代码，审计侧读不到风险分类。
    context.grants["reason"] = reason  # 新增代码+ComputerUseMcpV2：保存授权原因；如果没有这行代码，审计缺少申请目的。
    return success_result("request_access", _permission_payload(context, reason, True))  # 修改代码+ClaudeCodePermissionParity：返回新旧字段并存的授权成功摘要；如果没有这行代码，模型无法按 ClaudeCode 结构继续下一步。
# 新增代码+ComputerUseMcpV2：函数段结束，request_access 到此结束；如果没有这个边界说明，用户不容易看出授权申请范围。


def list_granted_applications(context: ComputerUseMcpV2Context) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，查询授权状态；如果没有这段函数，模型无法确认当前权限。
    return success_result("list_granted_applications", _permission_payload(context, str(context.grants.get("reason", "") or ""), bool(context.allowed_apps)))  # 修改代码+ClaudeCodePermissionParity：返回 ClaudeCode-compatible 授权状态并保留旧 grants；如果没有这行代码，模型查询不到 allowedApps/grantFlags。
# 新增代码+ComputerUseMcpV2：函数段结束，list_granted_applications 到此结束；如果没有这个边界说明，用户不容易看出授权查询范围。

