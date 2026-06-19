"""Computer Use MCP v2 结构化权限决策模型。"""  # 新增代码+PermissionUIDecision：说明本文件集中处理权限回调结果；如果没有这行代码，bool、dict 和默认拒绝逻辑会散落在 permissions.py。
from __future__ import annotations  # 新增代码+PermissionUIDecision：延迟解析类型注解；如果没有这行代码，后续前向类型扩展更容易导入失败。

from datetime import datetime, timezone  # 新增代码+PermissionUIDecision：导入 UTC 时间工具；如果没有这行代码，授权审计无法记录稳定时间戳。
from typing import Any  # 新增代码+PermissionUIDecision：导入通用 JSON 类型；如果没有这行代码，决策输入输出边界不清楚。


PROMPT_VERSION = "windows-permission-ui-v1"  # 新增代码+PermissionUIDecision：定义权限提示版本；如果没有这行代码，审计记录无法知道用户看到哪版 UI。


def _timestamp_utc() -> str:  # 新增代码+PermissionUIDecision：函数段开始，生成 UTC 审计时间；如果没有这段函数，每个决策会用不同格式记录时间。
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")  # 新增代码+PermissionUIDecision：返回 ISO UTC 时间；如果没有这行代码，授权记录缺少可排序时间戳。
# 新增代码+PermissionUIDecision：函数段结束，_timestamp_utc 到此结束；如果没有这个边界说明，用户不容易看出时间戳生成范围。


def _copy_apps(apps: list[dict[str, str]]) -> list[dict[str, str]]:  # 新增代码+PermissionUIDecision：函数段开始，复制 app 列表；如果没有这段函数，决策对象可能共享并污染调用方输入。
    return [dict(app) for app in list(apps or []) if isinstance(app, dict)]  # 新增代码+PermissionUIDecision：只复制字典 app；如果没有这行代码，坏类型可能进入审计 payload。
# 新增代码+PermissionUIDecision：函数段结束，_copy_apps 到此结束；如果没有这个边界说明，用户不容易看出 app 复制范围。


def _copy_warnings(sentinel_warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:  # 新增代码+PermissionUIDecision：函数段开始，复制风险提示列表；如果没有这段函数，审计对象可能共享原始 warning。
    return [dict(warning) for warning in list(sentinel_warnings or []) if isinstance(warning, dict)]  # 新增代码+PermissionUIDecision：只复制字典 warning；如果没有这行代码，坏类型可能进入审计 payload。
# 新增代码+PermissionUIDecision：函数段结束，_copy_warnings 到此结束；如果没有这个边界说明，用户不容易看出 warning 复制范围。


def _filter_grant_flags(requested_flags: dict[str, bool], raw_flags: Any) -> dict[str, bool]:  # 新增代码+PermissionUIDecision：函数段开始，按已知请求 flags 过滤回调 flags；如果没有这段函数，未知权限字段会污染状态。
    safe_requested = {str(key): bool(value) for key, value in dict(requested_flags or {}).items()}  # 新增代码+PermissionUIDecision：复制请求 flags；如果没有这行代码，后续合并可能修改调用方字典。
    if not isinstance(raw_flags, dict):  # 新增代码+PermissionUIDecision：检查结构化回调是否真的给了对象；如果没有这行代码，列表或字符串可能导致异常。
        return safe_requested  # 新增代码+PermissionUIDecision：缺少结构化 flags 时保留请求值；如果没有这行代码，批准路径可能丢掉全部权限。
    filtered = dict(safe_requested)  # 新增代码+PermissionUIDecision：从请求 flags 开始合并；如果没有这行代码，未提到的权限会被误清空。
    for key in safe_requested:  # 新增代码+PermissionUIDecision：只遍历已知请求字段；如果没有这行代码，未知 flag 会被带进状态。
        if key in raw_flags:  # 新增代码+PermissionUIDecision：仅覆盖结构化回调明确给出的字段；如果没有这行代码，所有字段都会被默认覆盖。
            filtered[key] = bool(raw_flags.get(key))  # 新增代码+PermissionUIDecision：写入布尔化 flag；如果没有这行代码，JSON truthy/falsy 值无法稳定使用。
    return filtered  # 新增代码+PermissionUIDecision：返回过滤后的 flags；如果没有这行代码，调用方拿不到合并结果。
# 新增代码+PermissionUIDecision：函数段结束，_filter_grant_flags 到此结束；如果没有这个边界说明，用户不容易看出 flag 过滤范围。


def approved_decision(requested_apps: list[dict[str, str]], requested_flags: dict[str, bool], sentinel_warnings: list[dict[str, Any]], *, source: str, reason: str = "", decision: str = "allow_for_session", grant_flags: dict[str, bool] | None = None) -> dict[str, Any]:  # 新增代码+PermissionUIDecision：函数段开始，生成批准决策；如果没有这段函数，批准 payload 会在多个地方手写且不一致。
    safe_flags = dict(grant_flags if grant_flags is not None else requested_flags)  # 新增代码+PermissionUIDecision：确定实际授权 flags；如果没有这行代码，批准决策缺少危险权限结果。
    return {  # 新增代码+PermissionUIDecision：开始返回结构化批准对象；如果没有这行代码，调用方无法拿到稳定字典。
        "approved": True,  # 新增代码+PermissionUIDecision：标记本次允许；如果没有这一行，permissions.py 无法判断是否写入授权。
        "decision": str(decision or "allow_for_session"),  # 新增代码+PermissionUIDecision：保存决策类型；如果没有这一行，审计无法区分普通批准和降权批准。
        "grantedApps": _copy_apps(requested_apps),  # 新增代码+PermissionUIDecision：保存批准应用；如果没有这一行，后续 allowed_apps 可能为空。
        "deniedApps": [],  # 新增代码+PermissionUIDecision：批准时没有拒绝应用；如果没有这一行，payload 形状会漂移。
        "grantFlags": {str(key): bool(value) for key, value in safe_flags.items()},  # 新增代码+PermissionUIDecision：保存实际授权 flags；如果没有这一行，后续剪贴板和系统键权限无法审计。
        "sentinelWarnings": _copy_warnings(sentinel_warnings),  # 新增代码+PermissionUIDecision：保存风险提示快照；如果没有这一行，审计看不到高风险上下文。
        "reason": str(reason or ""),  # 新增代码+PermissionUIDecision：保存结构化原因；如果没有这一行，拒绝或降权原因会丢失。
        "source": str(source or "structured_callback"),  # 新增代码+PermissionUIDecision：保存决策来源；如果没有这一行，无法区分终端 bool 和未来结构化 UI。
        "promptVersion": PROMPT_VERSION,  # 新增代码+PermissionUIDecision：保存提示版本；如果没有这一行，审计无法知道用户看到哪版文案。
        "timestampUtc": _timestamp_utc(),  # 新增代码+PermissionUIDecision：保存 UTC 时间；如果没有这一行，长任务无法追踪授权时序。
    }  # 新增代码+PermissionUIDecision：结构化批准对象结束；如果没有这行代码，Python 字典语法不完整。
# 新增代码+PermissionUIDecision：函数段结束，approved_decision 到此结束；如果没有这个边界说明，用户不容易看出批准决策构造范围。


def denied_decision(requested_apps: list[dict[str, str]], requested_flags: dict[str, bool], sentinel_warnings: list[dict[str, Any]], *, source: str, reason: str = "", decision: str = "deny") -> dict[str, Any]:  # 新增代码+PermissionUIDecision：函数段开始，生成拒绝决策；如果没有这段函数，拒绝 payload 会缺少统一审计字段。
    return {  # 新增代码+PermissionUIDecision：开始返回结构化拒绝对象；如果没有这行代码，调用方无法拿到稳定字典。
        "approved": False,  # 新增代码+PermissionUIDecision：标记本次拒绝；如果没有这一行，permissions.py 可能误写授权。
        "decision": str(decision or "deny"),  # 新增代码+PermissionUIDecision：保存拒绝类型；如果没有这一行，用户拒绝和默认拒绝无法区分。
        "grantedApps": [],  # 新增代码+PermissionUIDecision：拒绝时没有批准应用；如果没有这一行，payload 形状会漂移。
        "deniedApps": _copy_apps(requested_apps),  # 新增代码+PermissionUIDecision：保存被拒绝应用；如果没有这一行，审计不知道用户拒绝了什么。
        "grantFlags": {},  # 新增代码+PermissionUIDecision：拒绝时不授予任何危险权限；如果没有这一行，拒绝后可能残留 flags。
        "requestedGrantFlags": {str(key): bool(value) for key, value in dict(requested_flags or {}).items()},  # 新增代码+PermissionUIDecision：保存原始请求 flags；如果没有这一行，用户看不到被拒绝的权限范围。
        "sentinelWarnings": _copy_warnings(sentinel_warnings),  # 新增代码+PermissionUIDecision：保存风险提示快照；如果没有这一行，高风险拒绝缺少上下文。
        "reason": str(reason or ""),  # 新增代码+PermissionUIDecision：保存拒绝原因；如果没有这一行，调用方不知道为什么被拒绝。
        "source": str(source or "structured_callback"),  # 新增代码+PermissionUIDecision：保存拒绝来源；如果没有这一行，审计无法定位用户拒绝或系统拒绝。
        "promptVersion": PROMPT_VERSION,  # 新增代码+PermissionUIDecision：保存提示版本；如果没有这一行，审计无法知道用户看到哪版 UI。
        "timestampUtc": _timestamp_utc(),  # 新增代码+PermissionUIDecision：保存 UTC 时间；如果没有这一行，长任务无法追踪拒绝时序。
    }  # 新增代码+PermissionUIDecision：结构化拒绝对象结束；如果没有这行代码，Python 字典语法不完整。
# 新增代码+PermissionUIDecision：函数段结束，denied_decision 到此结束；如果没有这个边界说明，用户不容易看出拒绝决策构造范围。


def default_denied_decision(requested_apps: list[dict[str, str]], requested_flags: dict[str, bool], sentinel_warnings: list[dict[str, Any]], reason: str) -> dict[str, Any]:  # 新增代码+PermissionUIDecision：函数段开始，生成无交互默认拒绝；如果没有这段函数，缺 callback 时容易静默允许。
    return denied_decision(requested_apps, requested_flags, sentinel_warnings, source="noninteractive_default_deny", reason=reason, decision="noninteractive_default_deny")  # 新增代码+PermissionUIDecision：返回带无交互来源的拒绝；如果没有这行代码，默认拒绝无法被审计。
# 新增代码+PermissionUIDecision：函数段结束，default_denied_decision 到此结束；如果没有这个边界说明，用户不容易看出默认拒绝构造范围。


def normalize_permission_decision(raw_decision: Any, requested_apps: list[dict[str, str]], requested_flags: dict[str, bool], sentinel_warnings: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+PermissionUIDecision：函数段开始，统一 bool 和 dict 权限回调结果；如果没有这段函数，permissions.py 会继续混合 UI、解析和写状态职责。
    if isinstance(raw_decision, bool):  # 新增代码+PermissionUIDecision：先兼容旧 bool 回调；如果没有这行代码，真实终端 y/N 入口会被破坏。
        if raw_decision:  # 新增代码+PermissionUIDecision：判断 bool True；如果没有这行代码，批准和拒绝无法分支。
            return approved_decision(requested_apps, requested_flags, sentinel_warnings, source="legacy_bool_callback")  # 新增代码+PermissionUIDecision：bool True 转会话批准；如果没有这行代码，旧允许回调无法写入新审计合同。
        return denied_decision(requested_apps, requested_flags, sentinel_warnings, source="legacy_bool_callback", decision="deny")  # 新增代码+PermissionUIDecision：bool False 转拒绝；如果没有这行代码，旧拒绝回调无法写入新审计合同。
    if isinstance(raw_decision, dict):  # 新增代码+PermissionUIDecision：处理未来结构化回调；如果没有这行代码，权限 UI 无法表达降权授权。
        approved = bool(raw_decision.get("approved", raw_decision.get("allowed", False)))  # 新增代码+PermissionUIDecision：读取 approved/allowed 兼容字段；如果没有这行代码，结构化决策无法判断方向。
        source = str(raw_decision.get("source") or "structured_callback")  # 新增代码+PermissionUIDecision：读取来源并兜底；如果没有这行代码，审计来源会为空。
        reason = str(raw_decision.get("reason") or "")  # 新增代码+PermissionUIDecision：读取结构化原因；如果没有这行代码，降权或拒绝解释会丢失。
        if not approved:  # 新增代码+PermissionUIDecision：处理结构化拒绝；如果没有这行代码，拒绝 dict 可能继续走批准路径。
            return denied_decision(requested_apps, requested_flags, sentinel_warnings, source=source, reason=reason, decision=str(raw_decision.get("decision") or "deny"))  # 新增代码+PermissionUIDecision：返回结构化拒绝；如果没有这行代码，dict 拒绝缺少稳定 payload。
        safe_flags = _filter_grant_flags(requested_flags, raw_decision.get("grantFlags"))  # 新增代码+PermissionUIDecision：过滤结构化 flags；如果没有这行代码，未知权限字段会污染状态。
        decision_name = str(raw_decision.get("decision") or ("allow_with_reduced_flags" if safe_flags != dict(requested_flags or {}) else "allow_for_session"))  # 新增代码+PermissionUIDecision：自动判断是否降权；如果没有这行代码，用户关闭部分 flag 后审计仍显示普通批准。
        return approved_decision(requested_apps, requested_flags, sentinel_warnings, source=source, reason=reason, decision=decision_name, grant_flags=safe_flags)  # 新增代码+PermissionUIDecision：返回结构化批准；如果没有这行代码，dict 批准无法进入统一合同。
    return denied_decision(requested_apps, requested_flags, sentinel_warnings, source="unexpected_callback_value", reason=f"unsupported_permission_decision:{type(raw_decision).__name__}", decision="deny")  # 新增代码+PermissionUIDecision：未知返回值默认拒绝；如果没有这行代码，坏回调结果可能被 bool() 误放行。
# 新增代码+PermissionUIDecision：函数段结束，normalize_permission_decision 到此结束；如果没有这个边界说明，用户不容易看出权限决策归一化范围。
