"""Computer Use MCP v2 授权工具。"""  # 新增代码+ComputerUseMcpV2：说明本文件处理 request_access 和授权状态；如果没有这行代码，权限逻辑会混入动作执行。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，参数类型不清楚。

from .approval_decision import default_denied_decision, denied_decision, normalize_permission_decision  # 新增代码+PermissionUIDecision：导入结构化权限决策 helper；如果没有这行代码，request_access 会继续用 bool 和默认允许混在一起。
from .approval_prompt import build_computer_use_approval_prompt  # 修改代码+PermissionUIPrompt：导入集中审批提示构造器；如果没有这行代码，request_access 会继续手写 prompt 并难以测试。
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


def _last_permission_decision(context: ComputerUseMcpV2Context) -> dict[str, Any]:  # 新增代码+PermissionUIAuditContract：函数段开始，读取最近一次权限决策；如果没有这段函数，payload 里最近决策字段会重复拼装。
    decisions = list(getattr(context, "permission_decisions", []) or [])  # 新增代码+PermissionUIAuditContract：读取并复制决策列表；如果没有这行代码，缺字段旧 context 会导致查询崩溃。
    return dict(decisions[-1]) if decisions else {}  # 新增代码+PermissionUIAuditContract：返回最近决策副本或空字典；如果没有这行代码，调用方拿不到稳定结果。
# 新增代码+PermissionUIAuditContract：函数段结束，_last_permission_decision 到此结束；如果没有这个边界说明，用户不容易看出最近决策读取范围。


def _record_permission_decision(context: ComputerUseMcpV2Context, decision: dict[str, Any]) -> dict[str, Any]:  # 新增代码+PermissionUIAuditContract：函数段开始，把本次权限决策写入 context；如果没有这段函数，授权和拒绝无法被 list_granted 审计。
    safe_decision = dict(decision or {})  # 新增代码+PermissionUIAuditContract：复制决策对象；如果没有这行代码，后续修改可能污染原始决策。
    context.permission_decisions.append(safe_decision)  # 新增代码+PermissionUIAuditContract：追加到本会话审计列表；如果没有这行代码，多轮权限请求无法追踪。
    context.permission_decisions = context.permission_decisions[-50:]  # 新增代码+PermissionUIAuditContract：限制审计列表长度；如果没有这行代码，超长任务可能无限增长内存。
    return safe_decision  # 新增代码+PermissionUIAuditContract：返回保存后的决策副本；如果没有这行代码，调用方还要重新复制。
# 新增代码+PermissionUIAuditContract：函数段结束，_record_permission_decision 到此结束；如果没有这个边界说明，用户不容易看出权限审计写入范围。


def _permission_payload(context: ComputerUseMcpV2Context, reason: str, granted: bool, decision: dict[str, Any] | None = None) -> dict[str, Any]:  # 修改代码+PermissionUIAuditContract：函数段开始，生成 ClaudeCode-compatible 权限结果和 UI 审计字段；如果没有这段函数，request/list 会返回不同形状。
    applications = [app.get("displayName", "") for app in context.allowed_apps]  # 新增代码+ClaudeCodePermissionParity：生成旧 applications 兼容列表；如果没有这行代码，历史调用方无法读取授权应用名。
    active_decision = dict(decision or _last_permission_decision(context))  # 新增代码+PermissionUIAuditContract：读取当前决策或最近决策；如果没有这行代码，payload 审计字段无法统一。
    permission_decisions = [dict(item) for item in list(context.permission_decisions or [])]  # 新增代码+PermissionUIAuditContract：复制所有权限决策；如果没有这行代码，list_granted 无法展示历史审计。
    return {"allowedApps": list(context.allowed_apps), "applications": applications, "grantFlags": dict(context.grant_flags), "sentinelWarnings": list(context.sentinel_warnings), "deniedApps": list(context.denied_apps), "reason": reason, "granted": bool(granted), "grants": dict(context.grants), "decision": str(active_decision.get("decision", "")), "source": str(active_decision.get("source", "")), "promptVersion": str(active_decision.get("promptVersion", "")), "timestampUtc": str(active_decision.get("timestampUtc", "")), "permissionDecisions": permission_decisions, "lastPermissionDecision": active_decision}  # 修改代码+PermissionUIAuditContract：返回授权状态和审计字段；如果没有这行代码，模型和用户无法解释当前权限来源。
# 修改代码+PermissionUIAuditContract：函数段结束，_permission_payload 到此结束；如果没有这个边界说明，用户不容易看出权限返回结构范围。


def request_access(context: ComputerUseMcpV2Context, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，执行授权申请；如果没有这段函数，模型无法通过 v2 请求权限。
    apps = _apps_from_arguments(arguments)  # 修改代码+ClaudeCodePermissionParity：读取 ClaudeCode apps 并兼容旧 applications；如果没有这行代码，app allowlist 无法保存 bundleId/displayName。
    applications = [app.get("displayName", "") for app in apps]  # 修改代码+ClaudeCodePermissionParity：生成旧 applications 字符串列表；如果没有这行代码，旧回调和审计会丢应用名。
    grant_flags = _grant_flags_from_arguments(arguments)  # 新增代码+ClaudeCodePermissionParity：读取细粒度授权开关；如果没有这行代码，剪贴板和系统组合键权限无法表达。
    sentinel_warnings = [warning for warning in (sentinel_warning_for_app(app) for app in apps) if warning is not None]  # 新增代码+ClaudeCodePermissionParity：生成高风险应用提示；如果没有这行代码，PowerShell 等风险不会提示。
    reason = str(arguments.get("reason", "") or "")  # 新增代码+ComputerUseMcpV2：读取申请原因；如果没有这行代码，用户无法知道为什么要授权。
    prompt = build_computer_use_approval_prompt(apps=apps, applications=applications, grant_flags=grant_flags, sentinel_warnings=sentinel_warnings, reason=reason)  # 修改代码+PermissionApprovalPrompt：生成包含 allowlist、flags 和风险提示的授权提示；如果没有这行代码，用户看不到完整授权范围。
    if callable(context.ask_permission):  # 修改代码+PermissionUIDecision：只有真实存在权限回调时才询问用户；如果没有这行代码，无交互场景会继续静默放行。
        try:  # 新增代码+PermissionUIDecision：保护权限回调异常；如果没有这行代码，终端输入异常会变成裸异常而不是权限拒绝。
            raw_decision = context.ask_permission(prompt)  # 修改代码+PermissionUIDecision：调用权限回调并保留 bool 或 dict 原始结果；如果没有这行代码，用户授权无法进入决策模型。
            decision = normalize_permission_decision(raw_decision, apps, grant_flags, sentinel_warnings)  # 新增代码+PermissionUIDecision：把回调结果归一化；如果没有这行代码，后续写状态会继续依赖 bool。
        except Exception as error:  # 新增代码+PermissionUIDecision：捕获权限回调异常；如果没有这行代码，输入流错误会中断整个工具调用。
            decision = denied_decision(apps, grant_flags, sentinel_warnings, source="permission_callback_error", reason=f"{type(error).__name__}: {error}", decision="deny")  # 新增代码+PermissionUIDecision：异常时默认拒绝；如果没有这行代码，坏回调可能导致不安全放行或裸崩溃。
    else:  # 新增代码+PermissionUIDecision：处理没有权限回调的无交互场景；如果没有这行代码，默认拒绝无法落地。
        decision = default_denied_decision(apps, grant_flags, sentinel_warnings, "没有可用的 ask_permission 回调，已按安全默认拒绝。")  # 新增代码+PermissionUIDecision：无回调时生成默认拒绝；如果没有这行代码，standalone 场景会继续静默授权。
    decision = _record_permission_decision(context, decision)  # 新增代码+PermissionUIAuditContract：记录本次权限决策；如果没有这行代码，list_granted 无法展示授权或拒绝历史。
    if not bool(decision.get("approved", False)):  # 修改代码+PermissionUIDecision：检查结构化决策是否拒绝；如果没有这行代码，拒绝 dict 也会被当成授权。
        context.denied_apps = [dict(app) for app in decision.get("deniedApps", apps)]  # 修改代码+PermissionUIDecision：保存被拒绝应用；如果没有这行代码，拒绝审计无法知道用户拒绝了哪些目标。
        result = error_result("request_access", "user_denied_computer_use_v2_access", error_class="permission_denied")  # 修改代码+ClaudeCodePermissionParity：返回权限拒绝结果；如果没有这行代码，模型不知道授权没有成功。
        result["payload"] = {"deniedApps": list(context.denied_apps), "sentinelWarnings": sentinel_warnings, "reason": str(decision.get("reason", reason) or reason), "decision": str(decision.get("decision", "")), "source": str(decision.get("source", "")), "promptVersion": str(decision.get("promptVersion", "")), "timestampUtc": str(decision.get("timestampUtc", "")), "grantFlags": dict(decision.get("grantFlags", {})), "requestedGrantFlags": dict(decision.get("requestedGrantFlags", grant_flags)), "permissionDecision": dict(decision)}  # 修改代码+PermissionUIAuditContract：给拒绝结果附加审计 payload；如果没有这行代码，调用方无法读取拒绝来源、版本和目标。
        return result  # 新增代码+ClaudeCodePermissionParity：返回带 payload 的拒绝结果；如果没有这行代码，函数会继续保存授权。
    granted_apps = [dict(app) for app in decision.get("grantedApps", apps)]  # 新增代码+PermissionUIDecision：读取实际批准应用；如果没有这行代码，结构化回调未来无法表达子集授权。
    granted_flags = dict(decision.get("grantFlags", grant_flags))  # 新增代码+PermissionUIDecision：读取实际批准 flags；如果没有这行代码，降权授权不会影响状态。
    context.allowed_apps = granted_apps  # 修改代码+PermissionUIDecision：保存实际批准 app allowlist；如果没有这行代码，list_granted_applications 无法返回 allowedApps。
    context.grant_flags = granted_flags  # 修改代码+PermissionUIDecision：保存实际批准授权开关；如果没有这行代码，后续剪贴板/组合键无法检查授权。
    context.sentinel_warnings = sentinel_warnings  # 新增代码+ClaudeCodePermissionParity：保存风险提示；如果没有这行代码，授权查询无法提示 shell/system settings 风险。
    context.denied_apps = []  # 新增代码+ClaudeCodePermissionParity：授权成功时清空拒绝列表；如果没有这行代码，旧拒绝状态可能污染当前授权。
    context.grants["applications"] = applications  # 新增代码+ComputerUseMcpV2：保存授权应用摘要；如果没有这行代码，list_granted_applications 看不到授权范围。
    context.grants["allowedApps"] = list(context.allowed_apps)  # 新增代码+ClaudeCodePermissionParity：在旧 grants 中保存 allowedApps；如果没有这行代码，旧读取方拿不到 ClaudeCode app 对象。
    context.grants["grantFlags"] = dict(context.grant_flags)  # 新增代码+ClaudeCodePermissionParity：在旧 grants 中保存 grantFlags；如果没有这行代码，旧读取方拿不到细粒度授权。
    context.grants["sentinelWarnings"] = list(context.sentinel_warnings)  # 新增代码+ClaudeCodePermissionParity：在旧 grants 中保存风险提示；如果没有这行代码，审计侧读不到风险分类。
    context.grants["reason"] = reason  # 新增代码+ComputerUseMcpV2：保存授权原因；如果没有这行代码，审计缺少申请目的。
    context.grants["decision"] = str(decision.get("decision", ""))  # 新增代码+PermissionUIAuditContract：在旧 grants 中保存决策名；如果没有这行代码，旧状态读取方无法看到授权来源。
    context.grants["source"] = str(decision.get("source", ""))  # 新增代码+PermissionUIAuditContract：在旧 grants 中保存来源；如果没有这行代码，旧状态读取方无法区分 bool 和结构化决策。
    context.grants["promptVersion"] = str(decision.get("promptVersion", ""))  # 新增代码+PermissionUIAuditContract：在旧 grants 中保存提示版本；如果没有这行代码，旧审计无法知道 UI 版本。
    context.grants["timestampUtc"] = str(decision.get("timestampUtc", ""))  # 新增代码+PermissionUIAuditContract：在旧 grants 中保存授权时间；如果没有这行代码，旧审计无法排序授权事件。
    return success_result("request_access", _permission_payload(context, reason, True, decision))  # 修改代码+PermissionUIAuditContract：返回新旧字段并存的授权成功摘要和审计字段；如果没有这行代码，模型无法按 ClaudeCode 结构继续下一步。
# 新增代码+ComputerUseMcpV2：函数段结束，request_access 到此结束；如果没有这个边界说明，用户不容易看出授权申请范围。


def list_granted_applications(context: ComputerUseMcpV2Context) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，查询授权状态；如果没有这段函数，模型无法确认当前权限。
    return success_result("list_granted_applications", _permission_payload(context, str(context.grants.get("reason", "") or ""), bool(context.allowed_apps)))  # 修改代码+PermissionUIAuditContract：返回 ClaudeCode-compatible 授权状态、旧 grants 和权限 UI 审计；如果没有这行代码，模型查询不到 allowedApps/grantFlags/decision。
# 新增代码+ComputerUseMcpV2：函数段结束，list_granted_applications 到此结束；如果没有这个边界说明，用户不容易看出授权查询范围。

