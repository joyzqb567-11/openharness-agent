"""Cua Driver 借鉴的 Windows UIPI 完整性诊断工具。"""  # 新增代码+CuaDriverBorrowing：说明本模块只解释完整性等级和后台派发风险；如果没有这一行，读者不知道该文件为何存在。
from __future__ import annotations  # 新增代码+CuaDriverBorrowing：启用延迟类型解析；如果没有这一行，部分类型标注在旧入口下可能提前求值失败。

from typing import Any  # 新增代码+CuaDriverBorrowing：导入通用类型；如果没有这一行，诊断 payload 的类型边界不清楚。

CUA_DRIVER_BORROWING_INTEGRITY_MODEL = "cua_driver_borrowing_integrity_diagnostics_v1"  # 新增代码+CuaDriverBorrowing：标记当前完整性诊断版本；如果没有这一行，验收矩阵无法确认能力版本。
INTEGRITY_LEVELS = {  # 新增代码+CuaDriverBorrowing：定义 Windows 常见完整性等级排序开始；如果没有这一行，UIPI 高低权限比较没有统一依据。
    "untrusted": 0,  # 新增代码+CuaDriverBorrowing：最低等级；如果没有这一行，极低权限进程无法被排序。
    "low": 1,  # 新增代码+CuaDriverBorrowing：低完整性等级；如果没有这一行，浏览器沙盒等场景无法被解释。
    "medium": 2,  # 新增代码+CuaDriverBorrowing：普通用户完整性等级；如果没有这一行，agent 常见运行等级无法被比较。
    "high": 3,  # 新增代码+CuaDriverBorrowing：管理员完整性等级；如果没有这一行，管理员窗口阻断无法被解释。
    "system": 4,  # 新增代码+CuaDriverBorrowing：系统完整性等级；如果没有这一行，系统窗口风险无法被排序。
}  # 新增代码+CuaDriverBorrowing：定义 Windows 常见完整性等级排序结束；如果没有这一行，字典语法不完整。
DEFAULT_INTEGRITY_LEVEL = "medium"  # 新增代码+CuaDriverBorrowing：未知等级默认按普通用户处理；如果没有这一行，缺诊断数据会导致不可预测排序。


# 新增代码+CuaDriverBorrowing：函数段开始，_normalize_integrity_name 清理完整性等级文本；如果没有这段函数，不同大小写和空值会导致比较漂移。
def _normalize_integrity_name(name: Any) -> str:  # 新增代码+CuaDriverBorrowing：定义完整性等级清理入口；如果没有这一行，调用方只能传完全匹配的小写文本。
    text = str(name or DEFAULT_INTEGRITY_LEVEL).strip().lower()  # 新增代码+CuaDriverBorrowing：把空值和大小写统一处理；如果没有这一行，High/high 会被当成不同等级。
    if text in INTEGRITY_LEVELS:  # 新增代码+CuaDriverBorrowing：检查是否为已知等级；如果没有这一行，未知文本会直接进入排序。
        return text  # 新增代码+CuaDriverBorrowing：返回已知等级文本；如果没有这一行，合法输入无法被保留。
    return DEFAULT_INTEGRITY_LEVEL  # 新增代码+CuaDriverBorrowing：未知等级退回普通用户；如果没有这一行，诊断会因新字符串崩溃或误排。
# 新增代码+CuaDriverBorrowing：函数段结束，_normalize_integrity_name 到此结束；如果没有这个边界说明，初学者不容易看出文本清理范围。


# 新增代码+CuaDriverBorrowing：函数段开始，integrity_rank 返回完整性等级数值；如果没有这段函数，UIPI 诊断无法比较发送方和目标方高低。
def integrity_rank(name: Any) -> int:  # 新增代码+CuaDriverBorrowing：定义完整性等级排序入口；如果没有这一行，外部无法复用统一排序规则。
    normalized = _normalize_integrity_name(name)  # 新增代码+CuaDriverBorrowing：先清理等级名称；如果没有这一行，大小写和空值会导致排序不稳定。
    return INTEGRITY_LEVELS[normalized]  # 新增代码+CuaDriverBorrowing：返回等级数值；如果没有这一行，诊断函数拿不到可比较的数字。
# 新增代码+CuaDriverBorrowing：函数段结束，integrity_rank 到此结束；如果没有这个边界说明，初学者不容易看出等级排序范围。


# 新增代码+CuaDriverBorrowing：函数段开始，_base_payload 构造完整性诊断基础证据；如果没有这段函数，各决策分支字段会不一致。
def _base_payload(sender_integrity: Any, target_integrity: Any, attempted_background: bool) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义基础 payload 构造入口；如果没有这一行，诊断结果缺少统一证据。
    sender = _normalize_integrity_name(sender_integrity)  # 新增代码+CuaDriverBorrowing：清理发送方完整性等级；如果没有这一行，输出会保留脏输入。
    target = _normalize_integrity_name(target_integrity)  # 新增代码+CuaDriverBorrowing：清理目标方完整性等级；如果没有这一行，输出会保留脏输入。
    return {  # 新增代码+CuaDriverBorrowing：返回基础证据字典开始；如果没有这一行，调用方拿不到结构化证据。
        "sender_integrity": sender,  # 新增代码+CuaDriverBorrowing：记录发送方等级；如果没有这一行，用户不知道 agent 当前等级。
        "target_integrity": target,  # 新增代码+CuaDriverBorrowing：记录目标方等级；如果没有这一行，用户不知道目标窗口等级。
        "sender_rank": integrity_rank(sender),  # 新增代码+CuaDriverBorrowing：记录发送方数值等级；如果没有这一行，调试时无法看到比较依据。
        "target_rank": integrity_rank(target),  # 新增代码+CuaDriverBorrowing：记录目标方数值等级；如果没有这一行，调试时无法看到比较依据。
        "attempted_background": bool(attempted_background),  # 新增代码+CuaDriverBorrowing：记录是否尝试后台派发；如果没有这一行，前台/后台语境会丢失。
    }  # 新增代码+CuaDriverBorrowing：返回基础证据字典结束；如果没有这一行，字典语法不完整。
# 新增代码+CuaDriverBorrowing：函数段结束，_base_payload 到此结束；如果没有这个边界说明，初学者不容易看出证据构造范围。


# 新增代码+CuaDriverBorrowing：函数段开始，diagnose_uipi_block 判断后台消息是否可能被 UIPI 阻断；如果没有这段函数，用户只能看到动作失败而不知道权限原因。
def diagnose_uipi_block(sender_integrity: Any, target_integrity: Any, *, attempted_background: bool) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义 UIPI 阻断诊断入口；如果没有这一行，上层无法解释后台派发失败。
    payload = _base_payload(sender_integrity, target_integrity, attempted_background)  # 新增代码+CuaDriverBorrowing：生成基础证据；如果没有这一行，返回结果缺少等级细节。
    if payload["attempted_background"] and payload["sender_rank"] < payload["target_rank"]:  # 新增代码+CuaDriverBorrowing：低权限后台发往高权限时判定为 UIPI 阻断；如果没有这一行，管理员窗口失败会被误归因。
        payload.update({"ok": False, "decision": "integrity_blocked", "reason": "uipi_lower_integrity_sender_to_higher_integrity_target"})  # 新增代码+CuaDriverBorrowing：写入阻断决策；如果没有这一行，调用方无法用稳定字段提示用户。
        return payload  # 新增代码+CuaDriverBorrowing：返回阻断诊断；如果没有这一行，后续允许逻辑会覆盖失败结果。
    payload.update({"ok": True, "decision": "integrity_allows_message", "reason": "integrity_not_lower_than_target_or_not_background"})  # 新增代码+CuaDriverBorrowing：写入允许决策；如果没有这一行，正常同级动作无法继续。
    return payload  # 新增代码+CuaDriverBorrowing：返回允许诊断；如果没有这一行，调用方拿不到结果。
# 新增代码+CuaDriverBorrowing：函数段结束，diagnose_uipi_block 到此结束；如果没有这个边界说明，初学者不容易看出 UIPI 诊断范围。


# 新增代码+CuaDriverBorrowing：函数段开始，background_dispatch_diagnostic 汇总后台可用性和完整性诊断；如果没有这段函数，目标不可用会被误说成权限问题。
def background_dispatch_diagnostic(background_requested: bool, target_available: bool, sender_integrity: Any, target_integrity: Any) -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：定义后台派发诊断入口；如果没有这一行，上层无法一站式解释后台派发是否可行。
    if not background_requested:  # 新增代码+CuaDriverBorrowing：检查是否根本没有请求后台派发；如果没有这一行，前台动作也会被错误做后台诊断。
        return {"ok": True, "decision": "background_not_requested", "reason": "foreground_or_semantic_action_path"}  # 新增代码+CuaDriverBorrowing：返回无需后台派发；如果没有这一行，前台路径会被无意义阻断。
    if not target_available:  # 新增代码+CuaDriverBorrowing：先检查目标窗口或句柄是否可用；如果没有这一行，缺目标会被误归因到 UIPI。
        return {"ok": False, "decision": "background_unavailable", "reason": "target_not_available_for_background_dispatch"}  # 新增代码+CuaDriverBorrowing：返回目标不可用决策；如果没有这一行，用户不知道应重新观察目标。
    return diagnose_uipi_block(sender_integrity, target_integrity, attempted_background=True)  # 新增代码+CuaDriverBorrowing：目标可用后再做 UIPI 诊断；如果没有这一行，高低权限风险不会被解释。
# 新增代码+CuaDriverBorrowing：函数段结束，background_dispatch_diagnostic 到此结束；如果没有这个边界说明，初学者不容易看出后台派发诊断范围。


__all__ = [  # 新增代码+CuaDriverBorrowing：声明公开 API 开始；如果没有这一行，外部不清楚哪些名字是稳定接口。
    "CUA_DRIVER_BORROWING_INTEGRITY_MODEL",  # 新增代码+CuaDriverBorrowing：公开诊断版本；如果没有这一行，验收矩阵无法读取能力标记。
    "background_dispatch_diagnostic",  # 新增代码+CuaDriverBorrowing：公开后台派发诊断入口；如果没有这一行，动作层无法复用综合诊断。
    "diagnose_uipi_block",  # 新增代码+CuaDriverBorrowing：公开 UIPI 阻断诊断入口；如果没有这一行，测试和动作层无法复用权限比较。
    "integrity_rank",  # 新增代码+CuaDriverBorrowing：公开完整性等级排序函数；如果没有这一行，外部无法单独验证等级比较。
]  # 新增代码+CuaDriverBorrowing：声明公开 API 结束；如果没有这一行，公开列表语法不完整。
