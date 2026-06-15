"""Computer Use 最终回答证据摘要工具。"""  # 新增代码+AgentPySplitPhase5: 说明本文件只负责给 full 桌面任务最终回答补充证据摘要；如果没有这行代码，代码小白打开文件时不知道模块用途。

from __future__ import annotations  # 新增代码+AgentPySplitPhase5: 允许类型注解延迟解析；如果没有这行代码，复杂注解在旧运行方式下更容易受导入顺序影响。

from typing import Any  # 新增代码+AgentPySplitPhase5: 导入通用 JSON 风格数据类型；如果没有这行代码，函数接口不容易表达 observation_events 这类动态结构。

from .action_gates import computer_use_data_has_model_visible_image, computer_use_full_recent_events_after_mode_open  # 新增代码+AgentPySplitPhase5: 复用 Phase4 已拆出的截图证据判断和 full 会话窗口切分；如果没有这行代码，最终证据摘要会复制一份门禁逻辑。


# 新增代码+AgentPySplitPhase5: 函数段开始，computer_use_full_final_answer_summary_context_active 判断最终回答是否属于 full GUI 桌面任务；如果没有这段函数，普通文本回答可能被旧桌面证据污染。
def computer_use_full_final_answer_summary_context_active(desktop_task_context: Any) -> bool:  # 新增代码+AgentPySplitPhase5: 定义最终证据摘要适用性入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    if not isinstance(desktop_task_context, dict):  # 新增代码+AgentPySplitPhase5: 防御异常上下文形状；如果没有这一行，外部注入坏状态可能让最终回答崩溃。
        return False  # 新增代码+AgentPySplitPhase5: 上下文坏掉时不补摘要；如果没有这一行，普通回答可能被误判为桌面任务。
    return bool(desktop_task_context.get("active", False)) and bool(desktop_task_context.get("requires_gui_actions", False))  # 新增代码+AgentPySplitPhase5: 只给需要 GUI 动作的桌面任务补强；如果没有这一行，解释类任务会得到无关证据摘要。
# 新增代码+AgentPySplitPhase5: 函数段结束，computer_use_full_final_answer_summary_context_active 到此结束；如果没有这个边界说明，读者不容易看出补强适用范围。


# 新增代码+AgentPySplitPhase5: 函数段开始，computer_use_full_extract_window_summary 从工具结果中提取窗口身份；如果没有这段函数，最终回答无法说明真实控制的是哪个应用窗口。
def computer_use_full_extract_window_summary(data: dict[str, Any]) -> dict[str, str]:  # 新增代码+AgentPySplitPhase5: 定义窗口摘要提取入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    for key in ("target_window", "window"):  # 新增代码+AgentPySplitPhase5: 按常见字段顺序查找窗口摘要；如果没有这一行，不同后端返回字段会被漏掉。
        candidate = data.get(key, {})  # 新增代码+AgentPySplitPhase5: 读取候选窗口字典；如果没有这一行，后续无法判断 app_id/window_id。
        if not isinstance(candidate, dict):  # 新增代码+AgentPySplitPhase5: 跳过非字典窗口字段；如果没有这一行，字符串窗口字段会触发属性错误。
            continue  # 新增代码+AgentPySplitPhase5: 继续检查下一个字段；如果没有这一行，一个坏字段会终止提取。
        app_id = str(candidate.get("app_id", "") or candidate.get("process_name", "") or "").strip()  # 新增代码+AgentPySplitPhase5: 提取 app_id 或进程名；如果没有这一行，最终摘要无法指出 mspaintapp 等身份。
        window_id = str(candidate.get("window_id", "") or candidate.get("hwnd", "") or "").strip()  # 新增代码+AgentPySplitPhase5: 提取窗口 id；如果没有这一行，用户无法区分是否绑定到具体窗口。
        title = str(candidate.get("title_preview", "") or candidate.get("title", "") or "").strip()  # 新增代码+AgentPySplitPhase5: 提取窗口标题预览；如果没有这一行，最终摘要缺少可读窗口线索。
        if app_id or window_id or title:  # 新增代码+AgentPySplitPhase5: 只有拿到至少一个有效字段才返回；如果没有这一行，空窗口会覆盖已有证据。
            return {"app_id": app_id, "window_id": window_id, "title": title}  # 新增代码+AgentPySplitPhase5: 返回标准化窗口摘要；如果没有这一行，调用方需要重复处理字段差异。
    return {}  # 新增代码+AgentPySplitPhase5: 没有窗口证据时返回空字典；如果没有这一行，函数可能隐式返回 None 让调用方判断变复杂。
# 新增代码+AgentPySplitPhase5: 函数段结束，computer_use_full_extract_window_summary 到此结束；如果没有这个边界说明，读者不容易看出窗口证据提取范围。


# 新增代码+AgentPySplitPhase5: 函数段开始，computer_use_full_extract_screenshot_path 从工具结果中提取截图路径；如果没有这段函数，最终回答只能说有截图却不能给出证据位置。
def computer_use_full_extract_screenshot_path(data: dict[str, Any]) -> str:  # 新增代码+AgentPySplitPhase5: 定义截图路径提取入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    direct_path = str(data.get("screenshot_path", "") or "").strip()  # 新增代码+AgentPySplitPhase5: 优先读取顶层截图路径；如果没有这一行，observe 返回的最终截图路径会被漏掉。
    if direct_path:  # 新增代码+AgentPySplitPhase5: 如果顶层路径存在就直接使用；如果没有这一行，后续嵌套检查可能覆盖更准确的最终截图。
        return direct_path  # 新增代码+AgentPySplitPhase5: 返回最直接的截图路径；如果没有这一行，调用方拿不到路径。
    state = data.get("state", {}) if isinstance(data.get("state", {}), dict) else {}  # 新增代码+AgentPySplitPhase5: 读取状态块里的截图字段；如果没有这一行，某些 observe 后端的截图路径会被漏掉。
    state_path = str(state.get("screenshot_path", "") or "").strip()  # 新增代码+AgentPySplitPhase5: 提取状态块截图路径；如果没有这一行，内嵌路径无法进入最终摘要。
    if state_path:  # 新增代码+AgentPySplitPhase5: 如果状态块路径存在就使用；如果没有这一行，函数会继续不必要地查找嵌套证据。
        return state_path  # 新增代码+AgentPySplitPhase5: 返回状态块截图路径；如果没有这一行，最终摘要缺少图片位置。
    for evidence_key in ("after_evidence", "before_evidence"):  # 新增代码+AgentPySplitPhase5: 按最终优先顺序查找动作前后截图；如果没有这一行，action 自带截图不会进入最终摘要。
        evidence = data.get(evidence_key, {})  # 新增代码+AgentPySplitPhase5: 读取某个动作证据块；如果没有这一行，无法访问 image_results。
        if not isinstance(evidence, dict):  # 新增代码+AgentPySplitPhase5: 跳过异常证据块；如果没有这一行，坏数据会让最终回答崩溃。
            continue  # 新增代码+AgentPySplitPhase5: 继续检查下一个证据块；如果没有这一行，异常块会中断路径提取。
        evidence_path = str(evidence.get("screenshot_path", "") or "").strip()  # 新增代码+AgentPySplitPhase5: 先读证据块顶层路径；如果没有这一行，直接保存的动作截图路径会被漏掉。
        if evidence_path:  # 新增代码+AgentPySplitPhase5: 证据块路径存在时使用；如果没有这一行，函数会继续查找较弱路径。
            return evidence_path  # 新增代码+AgentPySplitPhase5: 返回动作证据路径；如果没有这一行，最终摘要无法引用动作截图。
        image_results = evidence.get("image_results", [])  # 新增代码+AgentPySplitPhase5: 读取模型可见图片块列表；如果没有这一行，PNG artifact 路径无法被发现。
        if not isinstance(image_results, list):  # 新增代码+AgentPySplitPhase5: 防御 image_results 不是列表；如果没有这一行，遍历字符串会产生错误路径。
            continue  # 新增代码+AgentPySplitPhase5: 跳过异常图片列表；如果没有这一行，坏图片结构会污染最终摘要。
        for image_result in reversed(image_results):  # 新增代码+AgentPySplitPhase5: 优先使用最新图片块；如果没有这一行，最终摘要可能指向过早截图。
            if not isinstance(image_result, dict):  # 新增代码+AgentPySplitPhase5: 跳过异常图片项；如果没有这一行，非字典图片项会触发属性错误。
                continue  # 新增代码+AgentPySplitPhase5: 继续检查前一个图片项；如果没有这一行，坏图片项会中断提取。
            artifact_path = str(image_result.get("artifact_path", "") or "").strip()  # 新增代码+AgentPySplitPhase5: 读取图片 artifact 路径；如果没有这一行，最终摘要无法引用已落盘截图。
            if artifact_path:  # 新增代码+AgentPySplitPhase5: 找到路径后返回；如果没有这一行，空路径可能覆盖真实证据。
                return artifact_path  # 新增代码+AgentPySplitPhase5: 返回图片 artifact 路径；如果没有这一行，调用方拿不到截图位置。
    return ""  # 新增代码+AgentPySplitPhase5: 没有截图路径时返回空字符串；如果没有这一行，调用方无法稳定判断是否有路径。
# 新增代码+AgentPySplitPhase5: 函数段结束，computer_use_full_extract_screenshot_path 到此结束；如果没有这个边界说明，读者不容易看出截图路径提取范围。


# 新增代码+AgentPySplitPhase5: 函数段开始，computer_use_full_collect_final_answer_evidence 汇总当前 full 会话的真实桌面证据；如果没有这段函数，最终回答只能依赖模型自觉复述工具结果。
def computer_use_full_collect_final_answer_evidence(desktop_task_context: Any, observation_events: Any) -> dict[str, Any]:  # 新增代码+AgentPySplitPhase5: 定义最终回答证据收集入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    summary: dict[str, Any] = {"available": False, "target_app": "", "app_id": "", "window_id": "", "title": "", "screenshot": False, "screenshot_path": "", "real_desktop_touched": False, "low_level_event_count": 0, "successful_action_count": 0}  # 新增代码+AgentPySplitPhase5: 初始化证据摘要结构；如果没有这一行，各字段会散落导致最终格式不稳定。
    if not computer_use_full_final_answer_summary_context_active(desktop_task_context):  # 新增代码+AgentPySplitPhase5: 确认本轮确实是 full GUI 桌面任务；如果没有这一行，普通聊天也可能追加过期桌面证据。
        return summary  # 新增代码+AgentPySplitPhase5: 非桌面任务直接返回空摘要；如果没有这一行，后续会误扫旧 observation。
    for event in computer_use_full_recent_events_after_mode_open(observation_events)[-120:]:  # 新增代码+AgentPySplitPhase5: 只扫描当前 full 会话最近 120 条事件；如果没有这一行，长期任务会变慢且可能混入旧证据。
        if event.get("kind") not in {"computer_use_action", "computer_use_observe"}:  # 新增代码+AgentPySplitPhase5: 只汇总真实桌面动作和观察；如果没有这一行，状态/日志事件会污染最终摘要。
            continue  # 新增代码+AgentPySplitPhase5: 跳过无关事件；如果没有这一行，后续读取 payload 会遇到不同结构。
        payload = event.get("payload", {})  # 新增代码+AgentPySplitPhase5: 读取 observation 载荷；如果没有这一行，无法判断 ok 和 data。
        if not isinstance(payload, dict) or not bool(payload.get("ok", False)):  # 新增代码+AgentPySplitPhase5: 只接受成功的 Computer Use 结果；如果没有这一行，失败动作也会被当成完成证据。
            continue  # 新增代码+AgentPySplitPhase5: 跳过失败或异常载荷；如果没有这一行，坏事件可能误导最终回答。
        data = payload.get("data", {})  # 新增代码+AgentPySplitPhase5: 读取控制器返回的结构化 data；如果没有这一行，窗口、截图和低层事件都无从提取。
        if not isinstance(data, dict):  # 新增代码+AgentPySplitPhase5: 防御 data 不是字典；如果没有这一行，字符串工具结果会让摘要崩溃。
            continue  # 新增代码+AgentPySplitPhase5: 跳过异常 data；如果没有这一行，最终回答出口可能被坏工具结果打断。
        summary["available"] = True  # 新增代码+AgentPySplitPhase5: 标记已经找到本轮真实桌面证据；如果没有这一行，后续即使提取到字段也不会追加摘要。
        target_app = str(data.get("target_app", "") or data.get("app_name", "") or data.get("app", "") or "").strip()  # 新增代码+AgentPySplitPhase5: 提取目标应用名；如果没有这一行，最终摘要可能缺少 mspaint 等用户可读 app。
        if target_app:  # 新增代码+AgentPySplitPhase5: 只有非空应用名才覆盖摘要；如果没有这一行，空字段会抹掉已有应用名。
            summary["target_app"] = target_app  # 新增代码+AgentPySplitPhase5: 保存最新有效目标应用名；如果没有这一行，最终回答无法说明控制了哪个软件。
        window_summary = computer_use_full_extract_window_summary(data)  # 新增代码+AgentPySplitPhase5: 从 data 提取窗口身份；如果没有这一行，app_id/window_id 证据无法进入摘要。
        if window_summary.get("app_id"):  # 新增代码+AgentPySplitPhase5: 如果有 app_id 就保存；如果没有这一行，mspaintapp:pid 这类硬身份会丢失。
            summary["app_id"] = window_summary["app_id"]  # 新增代码+AgentPySplitPhase5: 记录 app_id；如果没有这一行，验收和排查无法确认目标进程。
        if window_summary.get("window_id"):  # 新增代码+AgentPySplitPhase5: 如果有 window_id 就保存；如果没有这一行，最终摘要缺少窗口绑定证据。
            summary["window_id"] = window_summary["window_id"]  # 新增代码+AgentPySplitPhase5: 记录 window_id；如果没有这一行，无法区分 agent-owned 窗口和旧窗口。
        if window_summary.get("title"):  # 新增代码+AgentPySplitPhase5: 如果有标题预览就保存；如果没有这一行，用户可读窗口线索会缺失。
            summary["title"] = window_summary["title"]  # 新增代码+AgentPySplitPhase5: 记录窗口标题；如果没有这一行，最终回答不够可理解。
        dispatch = data.get("dispatch", {}) if isinstance(data.get("dispatch", {}), dict) else {}  # 新增代码+AgentPySplitPhase5: 读取底层调度摘要；如果没有这一行，low_level_event_count 可能从嵌套字段漏掉。
        low_level_count = int(dispatch.get("low_level_event_count", data.get("low_level_event_count", 0)) or 0)  # 新增代码+AgentPySplitPhase5: 提取本次低层输入事件数；如果没有这一行，真实鼠标键盘证据无法量化。
        if low_level_count > 0:  # 新增代码+AgentPySplitPhase5: 只有正数才累加；如果没有这一行，空动作会影响真实触碰判断。
            summary["low_level_event_count"] = int(summary["low_level_event_count"]) + low_level_count  # 新增代码+AgentPySplitPhase5: 累加低层输入事件数；如果没有这一行，多次动作的真实证据会被低估。
            summary["successful_action_count"] = int(summary["successful_action_count"]) + 1  # 新增代码+AgentPySplitPhase5: 累加成功真实动作数；如果没有这一行，最终摘要无法说明动作规模。
        if bool(data.get("real_desktop_touched", False)) or bool(data.get("real_input_enabled", False)) or low_level_count > 0:  # 新增代码+AgentPySplitPhase5: 判断是否真实触碰桌面；如果没有这一行，最终回答无法区分模拟和物理输入。
            summary["real_desktop_touched"] = True  # 新增代码+AgentPySplitPhase5: 保存真实桌面触碰标记；如果没有这一行，验收字段 real_desktop_touched 会缺失。
        if computer_use_data_has_model_visible_image(data) or bool(data.get("screenshot_captured", False)) or bool(data.get("screenshot_path", "")):  # 新增代码+AgentPySplitPhase5: 判断是否存在截图/图片证据；如果没有这一行，最终回答可能漏掉模型已观察屏幕的事实。
            summary["screenshot"] = True  # 新增代码+AgentPySplitPhase5: 标记截图证据存在；如果没有这一行，验收字段 screenshot 会缺失。
        screenshot_path = computer_use_full_extract_screenshot_path(data)  # 新增代码+AgentPySplitPhase5: 提取可引用截图路径；如果没有这一行，最终摘要只能泛泛说有截图。
        if screenshot_path:  # 新增代码+AgentPySplitPhase5: 只有找到路径时才覆盖；如果没有这一行，空路径会抹掉已有最终截图。
            summary["screenshot_path"] = screenshot_path  # 新增代码+AgentPySplitPhase5: 保存最新截图路径；如果没有这一行，用户无法定位证据图。
    if not summary["target_app"] and "mspaint" in str(summary["app_id"]).lower():  # 新增代码+AgentPySplitPhase5: 从 app_id 反推 Paint 应用名；如果没有这一行，真实 mspaintapp:pid 可能不满足 mspaint 验收字段。
        summary["target_app"] = "mspaint"  # 新增代码+AgentPySplitPhase5: 补全标准目标应用名；如果没有这一行，最终回答可能只含 mspaintapp 而没有 mspaint。
    return summary  # 新增代码+AgentPySplitPhase5: 返回最终证据摘要；如果没有这一行，最终回答补强逻辑拿不到数据。
# 新增代码+AgentPySplitPhase5: 函数段结束，computer_use_full_collect_final_answer_evidence 到此结束；如果没有这个边界说明，读者不容易看出证据汇总范围。


# 新增代码+AgentPySplitPhase5: 函数段开始，computer_use_full_final_answer_with_evidence_summary 给 full 桌面任务最终回答追加真实证据摘要；如果没有这段函数，模型短答会继续让终端体验和验收结果失真。
def computer_use_full_final_answer_with_evidence_summary(answer: str, desktop_task_context: Any, observation_events: Any) -> str:  # 新增代码+AgentPySplitPhase5: 定义最终回答补强入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    summary = computer_use_full_collect_final_answer_evidence(desktop_task_context, observation_events)  # 新增代码+AgentPySplitPhase5: 读取本轮真实桌面证据；如果没有这一行，函数无法知道是否需要补强。
    if not bool(summary.get("available", False)):  # 新增代码+AgentPySplitPhase5: 没有证据时不改答案；如果没有这一行，普通回答会被追加空摘要。
        return answer  # 新增代码+AgentPySplitPhase5: 直接返回原答案；如果没有这一行，无证据场景会继续格式化无意义内容。
    required_tokens = ["computer_use", "screenshot", "real_desktop_touched", "low_level_event_count"]  # 新增代码+AgentPySplitPhase5: 列出真实终端验收和用户理解需要的关键字段；如果没有这一行，缺字段判断会散落且不稳定。
    normalized_answer = answer.lower()  # 新增代码+AgentPySplitPhase5: 把答案转小写用于包含判断；如果没有这一行，大小写差异会导致重复追加摘要。
    app_token = str(summary.get("target_app", "") or summary.get("app_id", "") or "").lower()  # 新增代码+AgentPySplitPhase5: 读取应用字段用于判断答案是否已经提到目标软件；如果没有这一行，已包含 mspaint 的答案也可能被重复补强。
    missing_required = any(token not in normalized_answer for token in required_tokens) or (bool(app_token) and app_token not in normalized_answer)  # 新增代码+AgentPySplitPhase5: 判断模型答案是否缺少关键证据；如果没有这一行，所有 Computer Use 答案都会重复追加摘要。
    if not missing_required:  # 新增代码+AgentPySplitPhase5: 如果模型已经完整复述证据就不再追加；如果没有这一行，成熟模型回答会被冗余污染。
        return answer  # 新增代码+AgentPySplitPhase5: 保持原答案；如果没有这一行，完整答案也会变得啰嗦。
    target_app = str(summary.get("target_app", "") or "unknown_app")  # 新增代码+AgentPySplitPhase5: 准备最终摘要中的应用名；如果没有这一行，格式化时可能出现空白应用。
    app_id = str(summary.get("app_id", "") or "unknown_app_id")  # 新增代码+AgentPySplitPhase5: 准备最终摘要中的 app_id；如果没有这一行，窗口身份为空时格式不稳定。
    window_id = str(summary.get("window_id", "") or "unknown_window_id")  # 新增代码+AgentPySplitPhase5: 准备最终摘要中的 window_id；如果没有这一行，窗口身份行缺少兜底。
    screenshot_path = str(summary.get("screenshot_path", "") or "not_recorded")  # 新增代码+AgentPySplitPhase5: 准备最终摘要中的截图路径；如果没有这一行，截图字段缺少可读兜底。
    real_desktop_touched = "true" if bool(summary.get("real_desktop_touched", False)) else "false"  # 新增代码+AgentPySplitPhase5: 把真实触碰布尔值格式化成稳定 token；如果没有这一行，验收无法稳定匹配 real_desktop_touched=true。
    low_level_event_count = int(summary.get("low_level_event_count", 0) or 0)  # 新增代码+AgentPySplitPhase5: 把低层事件数转成整数；如果没有这一行，None 或字符串会让最终格式不稳定。
    successful_action_count = int(summary.get("successful_action_count", 0) or 0)  # 新增代码+AgentPySplitPhase5: 读取成功动作数；如果没有这一行，用户看不到本轮真实动作规模。
    evidence_lines = [  # 新增代码+AgentPySplitPhase5: 开始构造可读证据摘要行；如果没有这一行，最终回答无法稳定包含验收字段。
        "",  # 新增代码+AgentPySplitPhase5: 追加空行把模型回答和证据摘要隔开；如果没有这一行，短答和摘要会黏在一起难读。
        "Computer Use 真实执行摘要：",  # 新增代码+AgentPySplitPhase5: 用中文标题说明下面是证据不是模型内心思考；如果没有这一行，用户不容易区分结论和证据。
        f"- tool_path=computer_use; target_app={target_app}; app_id={app_id}; window_id={window_id}",  # 新增代码+AgentPySplitPhase5: 输出工具路径和目标窗口身份；如果没有这一行，验收和用户都无法确认真实应用链路。
        f"- screenshot={str(bool(summary.get('screenshot', False))).lower()}; screenshot_path={screenshot_path}",  # 新增代码+AgentPySplitPhase5: 输出截图证据字段；如果没有这一行，最终回答仍可能看不出模型是否观察过屏幕。
        f"- real_desktop_touched={real_desktop_touched}; low_level_event_count={low_level_event_count}; successful_action_count={successful_action_count}",  # 新增代码+AgentPySplitPhase5: 输出真实桌面触碰和低层事件数量；如果没有这一行，模拟/真实动作无法在最终回答里区分。
    ]  # 新增代码+AgentPySplitPhase5: 证据摘要行列表结束；如果没有这一行，Python 列表语法不完整。
    return answer.rstrip() + "\n".join(evidence_lines)  # 新增代码+AgentPySplitPhase5: 把原始答案和证据摘要合并返回；如果没有这一行，补强内容不会进入终端/controller 最终输出。
# 新增代码+AgentPySplitPhase5: 函数段结束，computer_use_full_final_answer_with_evidence_summary 到此结束；如果没有这个边界说明，读者不容易看出最终回答补强范围。
