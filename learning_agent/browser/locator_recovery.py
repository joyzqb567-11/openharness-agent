"""网页元素恢复定位的通用诊断 helper。"""  # 新增代码+WebChatLocatorRecovery：说明本文件负责把过期 element_id 的恢复定位结果结构化；如果没有这一行，读者不知道这个模块解决什么问题。
from __future__ import annotations  # 新增代码+WebChatLocatorRecovery：启用延迟类型解析；如果没有这一行，未来添加前向类型标注时更容易在运行时报错。

from typing import Any  # 新增代码+WebChatLocatorRecovery：导入 Any 描述浏览器工具传入的动态参数；如果没有这一行，helper 的字典参数类型不清楚。


LOCATOR_RECOVERY_FALLBACK_KEYS = ("selector", "label", "text")  # 新增代码+WebChatLocatorRecovery：定义 element_id 失效后允许回退的通用定位字段；如果没有这一行，恢复策略会散落在 server 里。


def locator_recovery_has_fallback(arguments: dict[str, Any]) -> bool:  # 新增代码+WebChatLocatorRecovery：函数段开始，判断调用参数是否有可恢复定位线索；如果没有这段函数，server 会继续把所有过期 element_id 都当成硬失败。
    return any(str(arguments.get(key, "") or "").strip() for key in LOCATOR_RECOVERY_FALLBACK_KEYS)  # 新增代码+WebChatLocatorRecovery：只要 selector、label 或 text 任一非空就允许恢复；如果没有这一行，网页输入框刷新后无法自救。
# 新增代码+WebChatLocatorRecovery：函数段结束，locator_recovery_has_fallback 到此结束；如果没有这个边界说明，初学者不容易看出 fallback 判断范围。


def locator_recovery_strategy(arguments: dict[str, Any]) -> str:  # 新增代码+WebChatLocatorRecovery：函数段开始，给本次恢复选择一个可读策略名；如果没有这段函数，诊断报告只能看到 true/false 不知道靠什么恢复。
    for key in LOCATOR_RECOVERY_FALLBACK_KEYS:  # 新增代码+WebChatLocatorRecovery：按稳定优先级检查 selector、label、text；如果没有这一行，策略名会随字典顺序变化。
        if str(arguments.get(key, "") or "").strip():  # 新增代码+WebChatLocatorRecovery：检查该字段是否提供了非空值；如果没有这一行，空字符串也可能被误当成策略。
            return key  # 新增代码+WebChatLocatorRecovery：返回第一个可用策略名；如果没有这一行，调用方无法解释恢复依据。
    return "none"  # 新增代码+WebChatLocatorRecovery：没有可用字段时返回 none；如果没有这一行，函数可能隐式返回 None 让报告不稳定。
# 新增代码+WebChatLocatorRecovery：函数段结束，locator_recovery_strategy 到此结束；如果没有这个边界说明，初学者不容易看出策略选择范围。


def build_locator_recovery_report(*, element_id: str, recovered: bool, strategy: str, snapshot_refreshed: bool, reason: str) -> dict[str, Any]:  # 新增代码+WebChatLocatorRecovery：函数段开始，构造统一恢复定位报告；如果没有这段函数，各工具会输出不同字段导致验收难解析。
    return {  # 新增代码+WebChatLocatorRecovery：返回结构化字典供 browser_type 和 browser_click 复用；如果没有这一行，诊断字段无法统一。
        "element_id": str(element_id or ""),  # 新增代码+WebChatLocatorRecovery：记录原始元素 id；如果没有这一行，复盘时不知道哪个引用过期。
        "locator_recovered": bool(recovered),  # 新增代码+WebChatLocatorRecovery：记录是否成功进入恢复分支；如果没有这一行，压力测试无法判断工具是否会自救。
        "locator_recovery_strategy": str(strategy or "none"),  # 新增代码+WebChatLocatorRecovery：记录 selector/label/text 等策略；如果没有这一行，无法区分靠什么定位成功。
        "snapshot_refreshed": bool(snapshot_refreshed),  # 新增代码+WebChatLocatorRecovery：记录是否重新采集页面候选元素；如果没有这一行，无法证明有重新观察页面。
        "reason": str(reason or ""),  # 新增代码+WebChatLocatorRecovery：记录恢复原因；如果没有这一行，用户只会看到机械字段没有解释。
    }  # 新增代码+WebChatLocatorRecovery：结束报告字典；如果没有这一行，Python 字典语法不完整。
# 新增代码+WebChatLocatorRecovery：函数段结束，build_locator_recovery_report 到此结束；如果没有这个边界说明，初学者不容易看出报告字段范围。


def locator_recovery_result_lines(report: dict[str, Any]) -> list[str]:  # 新增代码+WebChatLocatorRecovery：函数段开始，把恢复报告转成稳定文本行；如果没有这段函数，MCP 文本输出难以被验收器匹配。
    return [  # 新增代码+WebChatLocatorRecovery：返回固定顺序的多行 token；如果没有这一行，验收输出可能顺序漂移。
        f"locator_recovered={'true' if bool(report.get('locator_recovered')) else 'false'}",  # 新增代码+WebChatLocatorRecovery：输出是否发生恢复定位；如果没有这一行，S7 R3 看不到核心修复证据。
        f"locator_recovery_strategy={str(report.get('locator_recovery_strategy', 'none') or 'none')}",  # 新增代码+WebChatLocatorRecovery：输出恢复策略；如果没有这一行，失败复盘不知道走了 selector 还是 label。
        f"snapshot_refreshed={'true' if bool(report.get('snapshot_refreshed')) else 'false'}",  # 新增代码+WebChatLocatorRecovery：输出是否刷新快照；如果没有这一行，无法区分主动恢复和简单 fallback。
    ]  # 新增代码+WebChatLocatorRecovery：结束文本行列表；如果没有这一行，Python 列表语法不完整。
# 新增代码+WebChatLocatorRecovery：函数段结束，locator_recovery_result_lines 到此结束；如果没有这个边界说明，初学者不容易看出输出范围。


__all__ = ["LOCATOR_RECOVERY_FALLBACK_KEYS", "build_locator_recovery_report", "locator_recovery_has_fallback", "locator_recovery_result_lines", "locator_recovery_strategy"]  # 新增代码+WebChatLocatorRecovery：限定公开导出；如果没有这一行，外部可能误用内部细节。
