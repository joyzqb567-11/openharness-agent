"""通用资源身份识别 helper。"""  # 新增代码+ResourceIdentity：说明本模块只提供可选资源证据；如果没有这一行，读者可能误以为它是控制门禁。

from __future__ import annotations  # 新增代码+ResourceIdentity：启用延迟类型解析；如果没有这一行，未来类型注解更容易受导入顺序影响。

from typing import Any  # 新增代码+ResourceIdentity：导入 Any 表示窗口和 hint 都来自松散工具输入；如果没有这一行，函数边界不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.window_text_safety import sanitize_window_text  # 新增代码+ResourceIdentity：复用窗口文本清洗；如果没有这一行，资源标题可能携带 prompt 注入符号。


DOCUMENT_LIKE_APP_TOKENS = ("notepad", "word", "excel", "powerpnt", "code", "chrome", "msedge")  # 新增代码+ResourceIdentity：声明常见文档/页面类应用 token；如果没有这一行，helper 无法判断哪些应用可能有资源标题。
RESOURCE_USER_ACTION_REQUIRED_MARKER = "OPENHARNESS_DESKTOP_RESOURCE_USER_ACTION_REQUIRED"  # 新增代码+ResourceFreshness：声明资源旧内容需要用户介入的稳定 marker；如果没有这一行，旧文档恢复无法进入可收敛的安全阻断。
BLANK_RESOURCE_TITLE_TOKENS = ("notepad", "untitled - notepad", "无标题 - 记事本", "未命名 - 记事本")  # 新增代码+ResourceFreshness：声明常见空白文档标题；如果没有这一行，新空白窗口会被误判成旧资源。


def _safe_resource_text(value: Any) -> str:  # 新增代码+ResourceFreshness：函数段开始，把资源相关文本清洗成小写字符串；如果没有这段函数，标题和 hint 的比较会重复且容易漏掉注入清洗。
    return sanitize_window_text(value).lower()  # 新增代码+ResourceFreshness：复用窗口文本安全清洗并小写；如果没有这一行，大小写和危险字符会影响资源判断。
# 新增代码+ResourceFreshness：函数段结束，_safe_resource_text 到此结束；如果没有这个边界说明，用户不容易看出文本清洗范围。


def _is_document_like_app(app_id: str, process_name: str) -> bool:  # 新增代码+ResourceFreshness：函数段开始，判断应用是否像文档或页面容器；如果没有这段函数，资源判断会散落在多个调用点。
    app_text = f"{app_id} {process_name}".lower()  # 新增代码+ResourceFreshness：组合应用 id 和进程名；如果没有这一行，真实窗口只提供其中一个字段时会漏判。
    return any(token in app_text for token in DOCUMENT_LIKE_APP_TOKENS)  # 新增代码+ResourceFreshness：按通用 token 判断文档类应用；如果没有这一行，Notepad/Word/浏览器这类资源容器无法识别。
# 新增代码+ResourceFreshness：函数段结束，_is_document_like_app 到此结束；如果没有这个边界说明，用户不容易看出文档类判断范围。


def _is_blank_resource_title(title: str, app_id: str) -> bool:  # 新增代码+ResourceFreshness：函数段开始，判断窗口标题是否表示新空白资源；如果没有这段函数，任务会把空白窗口和旧文档混在一起。
    clean_title = str(title or "").strip().lower()  # 新增代码+ResourceFreshness：清理标题并小写；如果没有这一行，空格和大小写会影响空白识别。
    clean_app_id = str(app_id or "").strip().lower()  # 新增代码+ResourceFreshness：清理应用身份；如果没有这一行，app_id 为空时会影响 Notepad 兜底判断。
    if not clean_title:  # 新增代码+ResourceFreshness：没有标题时不能证明是空白资源；如果没有这一行，空标题可能被误当成安全新文档。
        return False  # 新增代码+ResourceFreshness：返回非空白；如果没有这一行，函数缺少空标题安全出口。
    if clean_title in BLANK_RESOURCE_TITLE_TOKENS:  # 新增代码+ResourceFreshness：命中明确空白标题时允许；如果没有这一行，Untitled/无标题标题无法被识别。
        return True  # 新增代码+ResourceFreshness：返回空白资源；如果没有这一行，明确空白标题仍会走旧资源阻断。
    if clean_title.startswith("untitled") or "无标题" in clean_title or "未命名" in clean_title:  # 新增代码+ResourceFreshness：兼容带应用后缀或本地化的空白标题；如果没有这一行，不同系统语言会误挡。
        return True  # 新增代码+ResourceFreshness：返回空白资源；如果没有这一行，本地化空白标题无法继续动作。
    if "notepad" in clean_app_id and clean_title == "notepad":  # 新增代码+ResourceFreshness：兼容部分 Notepad 初始窗口只显示应用名；如果没有这一行，新窗口可能被误判旧资源。
        return True  # 新增代码+ResourceFreshness：返回空白资源；如果没有这一行，Windows 版本差异会导致压力测试卡住。
    return False  # 新增代码+ResourceFreshness：其他标题默认不是空白资源；如果没有这一行，函数缺少安全默认值。
# 新增代码+ResourceFreshness：函数段结束，_is_blank_resource_title 到此结束；如果没有这个边界说明，用户不容易看出空白标题识别范围。


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


def build_resource_freshness(target_window: dict[str, Any], requested_resource_hint: Any = "", requires_new_resource: bool = False, allow_existing_resource: bool = False) -> dict[str, Any]:  # 新增代码+ResourceFreshness：函数段开始，判断当前窗口资源是否适合继续写入；如果没有这段函数，通用 Computer Use 只能绑定应用，不能防止写进旧文档。
    window = dict(target_window or {})  # 新增代码+ResourceFreshness：复制窗口事实避免污染调用方；如果没有这一行，后续补审计字段可能改坏原始窗口。
    hint = _safe_resource_text(requested_resource_hint)  # 新增代码+ResourceFreshness：清洗用户期望资源名；如果没有这一行，文件名比较会受大小写和危险字符影响。
    title = _safe_resource_text(window.get("title_preview") or window.get("title") or window.get("window_title"))  # 新增代码+ResourceFreshness：清洗窗口标题；如果没有这一行，旧文档标题无法安全比较。
    app_id = _safe_resource_text(window.get("app_id") or window.get("app") or window.get("target_app"))  # 新增代码+ResourceFreshness：清洗应用身份；如果没有这一行，报告无法判断文档容器。
    process_name = _safe_resource_text(window.get("process_name") or window.get("process") or window.get("exe"))  # 新增代码+ResourceFreshness：清洗进程身份；如果没有这一行，只有 process_name 的真实窗口会漏判。
    document_like = _is_document_like_app(app_id, process_name)  # 新增代码+ResourceFreshness：判断是否文档/页面类应用；如果没有这一行，未知普通应用会被过度资源门禁。
    resource_matches_hint = bool(hint and hint in title)  # 新增代码+ResourceFreshness：判断标题是否已经匹配用户目标资源；如果没有这一行，已保存到 1.txt 的窗口仍可能被误挡。
    blank_resource = _is_blank_resource_title(title, app_id or process_name)  # 新增代码+ResourceFreshness：判断当前资源是否是新空白；如果没有这一行，空白窗口和旧文档无法区分。
    report = {  # 新增代码+ResourceFreshness：准备结构化判断报告；如果没有这一行，调用方拿不到机器可读状态。
        "allowed": True,  # 新增代码+ResourceFreshness：默认允许，只有证据明确旧资源风险时阻断；如果没有这一行，未知应用会被过度保守卡死。
        "marker": "",  # 新增代码+ResourceFreshness：默认没有阻断 marker；如果没有这一行，正常路径可能被误解析为用户动作要求。
        "decision": "resource_freshness_not_required",  # 新增代码+ResourceFreshness：默认决策码；如果没有这一行，报告缺少稳定解释。
        "document_like": document_like,  # 新增代码+ResourceFreshness：保存文档类判断；如果没有这一行，调试时看不出为什么触发资源门禁。
        "resource_matches_hint": resource_matches_hint,  # 新增代码+ResourceFreshness：保存目标资源匹配结果；如果没有这一行，无法区分“已是目标文件”和“新空白”。
        "blank_resource": blank_resource,  # 新增代码+ResourceFreshness：保存空白资源判断；如果没有这一行，允许继续编辑的理由不可审计。
        "requested_resource_hint": hint,  # 新增代码+ResourceFreshness：保存清洗后的用户资源提示；如果没有这一行，验收日志无法复盘目标文件名。
        "title_preview": title,  # 新增代码+ResourceFreshness：保存清洗后的窗口标题；如果没有这一行，旧资源判断没有证据。
        "app_id": app_id,  # 新增代码+ResourceFreshness：保存应用身份；如果没有这一行，报告缺少目标软件线索。
        "process_name": process_name,  # 新增代码+ResourceFreshness：保存进程身份；如果没有这一行，报告缺少真实进程线索。
        "low_level_event_count": 0,  # 新增代码+ResourceFreshness：声明判断本身不触发键鼠事件；如果没有这一行，安全验收无法证明零事件阻断。
    }  # 新增代码+ResourceFreshness：报告字典结束；如果没有这一行，Python 语法不完整。
    if not document_like:  # 新增代码+ResourceFreshness：非文档类应用不强制资源新鲜度；如果没有这一行，未知应用会被文档规则误伤。
        return report  # 新增代码+ResourceFreshness：直接返回默认允许；如果没有这一行，普通应用无法继续通用 Computer Use。
    if resource_matches_hint:  # 新增代码+ResourceFreshness：标题已经是用户目标资源时允许；如果没有这一行，保存后继续验证会被误挡。
        report["decision"] = "requested_resource_ready"  # 新增代码+ResourceFreshness：写入目标资源已就绪决策；如果没有这一行，日志无法解释为什么允许。
        return report  # 新增代码+ResourceFreshness：返回允许报告；如果没有这一行，后续旧资源分支可能误挡。
    if requires_new_resource and blank_resource:  # 新增代码+ResourceFreshness：任务要求新资源且窗口为空白时允许；如果没有这一行，干净新窗口无法输入内容。
        report["decision"] = "fresh_blank_resource_ready"  # 新增代码+ResourceFreshness：写入新空白就绪决策；如果没有这一行，模型看不出下一步可以编辑。
        return report  # 新增代码+ResourceFreshness：返回允许报告；如果没有这一行，空白窗口会继续落入旧资源判断。
    if requires_new_resource and not allow_existing_resource and title and not blank_resource:  # 新增代码+ResourceFreshness：任务要求新资源但标题显示已有资源时阻断；如果没有这一行，agent 可能写入用户旧文档。
        report["allowed"] = False  # 新增代码+ResourceFreshness：标记不允许继续写动作；如果没有这一行，调用方无法执行硬门禁。
        report["marker"] = RESOURCE_USER_ACTION_REQUIRED_MARKER  # 新增代码+ResourceFreshness：写入资源用户动作 marker；如果没有这一行，收敛层无法稳定停止重试。
        report["decision"] = "restored_existing_resource_requires_new_blank_or_authorization"  # 新增代码+ResourceFreshness：写入旧资源恢复决策码；如果没有这一行，用户看不到为什么被阻断。
        report["block_class"] = "user_action_required"  # 新增代码+ResourceFreshness：复用现有用户动作阻断分类；如果没有这一行，收敛器无法按终止态处理。
        report["next_required_response"] = "ask_user_to_create_blank_or_authorize_existing_resource"  # 新增代码+ResourceFreshness：给模型稳定下一步响应类型；如果没有这一行，模型可能继续反复打开应用。
        return report  # 新增代码+ResourceFreshness：返回阻断报告；如果没有这一行，旧资源风险不会生效。
    report["decision"] = "resource_freshness_observed"  # 新增代码+ResourceFreshness：文档类但未要求新资源时记录已观察；如果没有这一行，报告会停留在默认不可诊断状态。
    return report  # 新增代码+ResourceFreshness：返回最终允许报告；如果没有这一行，函数缺少默认出口。
# 新增代码+ResourceFreshness：函数段结束，build_resource_freshness 到此结束；如果没有这个边界说明，用户不容易看出资源新鲜度判断范围。


__all__ = ["RESOURCE_USER_ACTION_REQUIRED_MARKER", "build_resource_freshness", "build_resource_identity"]  # 修改代码+ResourceFreshness：声明公开 helper 和 marker；如果没有这一行，adapter、controller 和测试无法稳定导入资源新鲜度能力。
