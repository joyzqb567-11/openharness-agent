"""通用资源身份识别 helper。"""  # 新增代码+ResourceIdentity：说明本模块只提供可选资源证据；如果没有这一行，读者可能误以为它是控制门禁。

from __future__ import annotations  # 新增代码+ResourceIdentity：启用延迟类型解析；如果没有这一行，未来类型注解更容易受导入顺序影响。

from typing import Any  # 新增代码+ResourceIdentity：导入 Any 表示窗口和 hint 都来自松散工具输入；如果没有这一行，函数边界不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.window_text_safety import sanitize_window_text  # 新增代码+ResourceIdentity：复用窗口文本清洗；如果没有这一行，资源标题可能携带 prompt 注入符号。


DOCUMENT_LIKE_APP_TOKENS = ("notepad", "word", "excel", "powerpnt", "code", "chrome", "msedge")  # 新增代码+ResourceIdentity：声明常见文档/页面类应用 token；如果没有这一行，helper 无法判断哪些应用可能有资源标题。


def build_resource_identity(target_window: dict[str, Any], requested_resource_hint: Any = "") -> dict[str, Any]:  # 新增代码+ResourceIdentity：函数段开始，生成可选资源身份报告；如果没有这段函数，Notepad 文件名等证据只能写成应用专用补丁。
    window = dict(target_window or {})  # 新增代码+ResourceIdentity：复制窗口输入避免污染调用方对象；如果没有这一行，清洗和规范化可能改坏原始窗口事实。
    hint = sanitize_window_text(requested_resource_hint).lower()  # 新增代码+ResourceIdentity：清洗并小写用户资源提示；如果没有这一行，大小写和注入符号会影响匹配。
    title = sanitize_window_text(window.get("title_preview") or window.get("title")).lower()  # 新增代码+ResourceIdentity：清洗并小写窗口标题；如果没有这一行，窗口标题里的文件名无法安全比对。
    app_id = sanitize_window_text(window.get("app_id") or window.get("process_name")).lower()  # 新增代码+ResourceIdentity：清洗并小写应用身份；如果没有这一行，helper 无法判断应用是否像文档容器。
    if not hint:  # 新增代码+ResourceIdentity：检查用户是否提供资源提示；如果没有这一行，空 hint 可能被误判匹配所有标题。
        return {"available": False, "required_for_generic_control": False, "resource_matches_hint": False, "document_like": False, "app_id": app_id, "title_preview": title, "requested_resource_hint": hint, "reason": "resource_hint_missing"}  # 新增代码+ResourceIdentity：缺 hint 时返回可选不可用；如果没有这一行，通用控制可能被错误要求文件名证据。
    document_like = any(token in app_id for token in DOCUMENT_LIKE_APP_TOKENS)  # 新增代码+ResourceIdentity：判断应用是否通常承载文档或页面资源；如果没有这一行，未知应用会被误当成可识别资源。
    resource_matches = bool(hint and hint in title)  # 新增代码+ResourceIdentity：判断标题是否包含用户资源提示；如果没有这一行，报告无法说明当前窗口是否像目标文件。
    return {  # 新增代码+ResourceIdentity：返回结构化资源身份报告；如果没有这一行，调用方拿不到机器可读证据。
        "available": bool(document_like),  # 新增代码+ResourceIdentity：说明该应用是否支持通用资源观察；如果没有这一行，用户不知道资源证据是否可用。
        "required_for_generic_control": False,  # 新增代码+ResourceIdentity：明确资源身份不是通用控制硬门禁；如果没有这一行，未来改动可能把它误用成应用白名单。
        "resource_matches_hint": resource_matches,  # 新增代码+ResourceIdentity：说明标题是否匹配资源提示；如果没有这一行，文件名/页面名漂移不可见。
        "document_like": document_like,  # 新增代码+ResourceIdentity：返回文档类判断；如果没有这一行，调试时看不出为何 available 为真或假。
        "app_id": app_id,  # 新增代码+ResourceIdentity：返回清洗后的应用身份；如果没有这一行，报告缺少判断依据。
        "title_preview": title,  # 新增代码+ResourceIdentity：返回清洗后的标题摘要；如果没有这一行，报告缺少匹配依据。
        "requested_resource_hint": hint,  # 新增代码+ResourceIdentity：返回清洗后的用户资源提示；如果没有这一行，报告无法复盘匹配输入。
        "reason": "resource_identity_observed" if document_like else "resource_identity_not_supported_for_app",  # 新增代码+ResourceIdentity：返回稳定原因 token；如果没有这一行，模型无法解释资源身份状态。
    }  # 新增代码+ResourceIdentity：结束资源身份报告；如果没有这一行，Python 字典语法不完整。
# 新增代码+ResourceIdentity：函数段结束，build_resource_identity 到此结束；如果没有这个边界说明，读者不容易看出资源身份范围。


__all__ = ["build_resource_identity"]  # 新增代码+ResourceIdentity：声明公开 helper；如果没有这一行，其他模块不清楚稳定导出入口。
