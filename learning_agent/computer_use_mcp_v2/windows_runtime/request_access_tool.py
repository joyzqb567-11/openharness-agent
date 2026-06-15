"""Computer Use request_access 只读申请工具。"""  # 新增代码+RequestAccessToolSurface: 说明本文件只负责创建授权申请报告；如果没有这一行，用户不容易看出它不会直接控制桌面。
from __future__ import annotations  # 新增代码+RequestAccessToolSurface: 延迟解析类型注解；如果没有这一行，旧解释器或循环类型引用更容易导入失败。

from typing import Any  # 新增代码+RequestAccessToolSurface: 引入通用 JSON 值类型；如果没有这一行，函数参数和返回结构的边界不清楚。

from .windows_app_inventory import APP_INVENTORY_HIGH_RISK_TOKENS, query_windows_app_inventory  # 新增代码+RequestAccessToolSurface: 复用现有普通应用清单和高风险过滤；如果没有这一行，request_access 会绕开已确认的应用安全层。

REQUEST_ACCESS_MARKER = "COMPUTER_USE_REQUEST_ACCESS_READY"  # 新增代码+RequestAccessToolSurface: 定义稳定验收标记；如果没有这一行，测试和真实终端输出难以确认走到新工具。
REQUEST_ACCESS_MODEL = "computer_use_request_access_tool_surface"  # 新增代码+RequestAccessToolSurface: 定义报告模型名；如果没有这一行，后续矩阵不容易区分工具面阶段和授权阶段。
REQUEST_ACCESS_DEFAULT_HINT_QUERIES = ("notepad", "mspaint", "calculator")  # 新增代码+RequestAccessToolSurface: 定义无指定应用时的安全提示候选；如果没有这一行，空请求时模型拿不到可学习的普通应用示例。


# 新增代码+RequestAccessToolSurface: 函数段开始，_request_access_text 把任意输入安全转成短文本；如果没有这段函数，后续字段规范化会重复且容易把 None 写进报告。
def _request_access_text(value: Any) -> str:  # 新增代码+RequestAccessToolSurface: 声明文本规范化函数；如果没有这一行，调用方每处都要手写 str/strip 逻辑。
    return str(value or "").strip()  # 新增代码+RequestAccessToolSurface: 返回去空白后的文本；如果没有这一行，空值和多余空白会污染申请理由和应用名。
# 新增代码+RequestAccessToolSurface: 函数段结束，_request_access_text 到此结束；如果没有这个边界说明，用户不容易看出它只做文本清洗。


# 新增代码+RequestAccessToolSurface: 函数段开始，_request_access_unique_texts 提取去重后的字符串列表；如果没有这段函数，模型传单字符串或列表时会出现不一致行为。
def _request_access_unique_texts(values: Any) -> list[str]:  # 新增代码+RequestAccessToolSurface: 声明列表规范化函数；如果没有这一行，requested_apps 的输入形态会不稳定。
    raw_values = [values] if isinstance(values, str) else values if isinstance(values, list) else []  # 新增代码+RequestAccessToolSurface: 兼容单字符串、数组和异常输入；如果没有这一行，模型传单个 app 名时会被误当空列表。
    seen: set[str] = set()  # 新增代码+RequestAccessToolSurface: 保存大小写无关去重键；如果没有这一行，同一个应用可能重复出现在申请报告。
    result: list[str] = []  # 新增代码+RequestAccessToolSurface: 保存清洗后的应用名；如果没有这一行，函数没有稳定返回容器。
    for item in raw_values:  # 新增代码+RequestAccessToolSurface: 遍历原始输入值；如果没有这一行，列表里的多个应用无法逐个处理。
        text = _request_access_text(item)  # 新增代码+RequestAccessToolSurface: 清洗单个应用名；如果没有这一行，空白和 None 会进入后续风险判断。
        normalized = text.casefold()  # 新增代码+RequestAccessToolSurface: 生成大小写无关去重键；如果没有这一行，Notepad 和 notepad 会被当作两个目标。
        if text and normalized not in seen:  # 新增代码+RequestAccessToolSurface: 只保留非空且未出现的应用名；如果没有这一行，报告会包含空目标或重复目标。
            seen.add(normalized)  # 新增代码+RequestAccessToolSurface: 记录已出现应用；如果没有这一行，后续重复项无法被识别。
            result.append(text)  # 新增代码+RequestAccessToolSurface: 写入清洗后的应用名；如果没有这一行，函数永远返回空列表。
    return result  # 新增代码+RequestAccessToolSurface: 返回去重后的应用名列表；如果没有这一行，调用方拿不到规范化结果。
# 新增代码+RequestAccessToolSurface: 函数段结束，_request_access_unique_texts 到此结束；如果没有这个边界说明，用户不容易看出去重范围。


# 新增代码+RequestAccessToolSurface: 函数段开始，_request_access_bool 读取可选布尔授权标志；如果没有这段函数，布尔字段会因为字符串 true/false 表达不一致。
def _request_access_bool(value: Any) -> bool:  # 新增代码+RequestAccessToolSurface: 声明布尔规范化函数；如果没有这一行，clipboard 等申请标志无法稳定解析。
    if isinstance(value, bool):  # 新增代码+RequestAccessToolSurface: 优先处理真正布尔值；如果没有这一行，False 可能被字符串规则误判。
        return value  # 新增代码+RequestAccessToolSurface: 原样返回布尔值；如果没有这一行，标准布尔输入无法保留。
    text = _request_access_text(value).casefold()  # 新增代码+RequestAccessToolSurface: 把非布尔输入转成小写文本；如果没有这一行，字符串 true/yes 无法被识别。
    return text in {"1", "true", "yes", "y", "on"}  # 新增代码+RequestAccessToolSurface: 只把明确肯定值视为 true；如果没有这一行，任意非空字符串都可能误开授权标志。
# 新增代码+RequestAccessToolSurface: 函数段结束，_request_access_bool 到此结束；如果没有这个边界说明，用户不容易看出布尔解析很保守。


# 新增代码+RequestAccessToolSurface: 函数段开始，_request_access_clamped_max_results 限制提示数量；如果没有这段函数，模型可能要求过多候选撑爆上下文。
def _request_access_clamped_max_results(value: Any) -> int:  # 新增代码+RequestAccessToolSurface: 声明数量限制函数；如果没有这一行，safe_app_hints 的长度缺少统一边界。
    try:  # 新增代码+RequestAccessToolSurface: 尝试把输入转成整数；如果没有这一行，异常输入会直接抛错。
        count = int(value)  # 新增代码+RequestAccessToolSurface: 读取调用方指定数量；如果没有这一行，用户传入 max_results 不会生效。
    except (TypeError, ValueError):  # 新增代码+RequestAccessToolSurface: 捕获缺省或非法数量；如果没有这一行，坏参数会让 request_access 崩溃。
        count = 6  # 新增代码+RequestAccessToolSurface: 使用小而够用的默认数量；如果没有这一行，非法输入时没有兜底。
    return max(1, min(count, 12))  # 新增代码+RequestAccessToolSurface: 把数量限制在 1 到 12；如果没有这一行，提示可能为空或过长。
# 新增代码+RequestAccessToolSurface: 函数段结束，_request_access_clamped_max_results 到此结束；如果没有这个边界说明，用户不容易看出数量限制来源。


# 新增代码+RequestAccessToolSurface: 函数段开始，_request_access_is_high_risk_app 判断请求目标是否危险；如果没有这段函数，PowerShell/CMD 可能混进普通授权提示。
def _request_access_is_high_risk_app(app_name: str) -> bool:  # 新增代码+RequestAccessToolSurface: 声明高风险应用判断函数；如果没有这一行，过滤逻辑没有集中入口。
    normalized = app_name.casefold()  # 新增代码+RequestAccessToolSurface: 使用大小写无关比较；如果没有这一行，PowerShell 大小写变化可能绕过过滤。
    return any(token in normalized for token in APP_INVENTORY_HIGH_RISK_TOKENS)  # 新增代码+RequestAccessToolSurface: 复用 inventory 的风险词；如果没有这一行，request_access 会和 discover 安全规则不一致。
# 新增代码+RequestAccessToolSurface: 函数段结束，_request_access_is_high_risk_app 到此结束；如果没有这个边界说明，用户不容易看出危险判断不创建新名单。


# 新增代码+RequestAccessToolSurface: 函数段开始，_request_access_candidate_identity 生成候选去重键；如果没有这段函数，同一个应用可能因为字段不同重复出现。
def _request_access_candidate_identity(candidate: dict[str, Any]) -> str:  # 新增代码+RequestAccessToolSurface: 声明候选身份函数；如果没有这一行，safe_app_hints 去重缺少稳定键。
    display_name = _request_access_text(candidate.get("display_name"))  # 新增代码+RequestAccessToolSurface: 读取展示名；如果没有这一行，候选身份缺少人类可读名称。
    app_name = _request_access_text(candidate.get("app_name"))  # 新增代码+RequestAccessToolSurface: 读取应用名；如果没有这一行，候选身份缺少启动目标。
    launch_id = _request_access_text(candidate.get("launch_id"))  # 新增代码+RequestAccessToolSurface: 读取启动标识；如果没有这一行，同名不同启动项无法区分。
    return f"{display_name}|{app_name}|{launch_id}".casefold()  # 新增代码+RequestAccessToolSurface: 返回大小写无关去重键；如果没有这一行，重复候选无法被稳定合并。
# 新增代码+RequestAccessToolSurface: 函数段结束，_request_access_candidate_identity 到此结束；如果没有这个边界说明，用户不容易看出它只做去重。


# 新增代码+RequestAccessToolSurface: 函数段开始，_request_access_safe_hint_from_candidate 把候选转成模型友好的提示；如果没有这段函数，报告只能暴露原始复杂字典。
def _request_access_safe_hint_from_candidate(candidate: dict[str, Any]) -> str:  # 新增代码+RequestAccessToolSurface: 声明候选提示格式化函数；如果没有这一行，safe_app_hints 没有统一格式。
    display_name = _request_access_text(candidate.get("display_name"))  # 新增代码+RequestAccessToolSurface: 读取安全展示名；如果没有这一行，提示无法显示用户可理解的应用名。
    app_name = _request_access_text(candidate.get("app_name"))  # 新增代码+RequestAccessToolSurface: 读取 app_name；如果没有这一行，后续授权无法引用规范目标。
    launch_kind = _request_access_text(candidate.get("launch_kind")) or "unknown"  # 新增代码+RequestAccessToolSurface: 读取启动类型并兜底；如果没有这一行，提示缺少候选来源说明。
    return f"{display_name} (app_name={app_name}, launch_kind={launch_kind})"  # 新增代码+RequestAccessToolSurface: 返回简短安全提示；如果没有这一行，模型无法从工具结果学习该申请哪个普通应用。
# 新增代码+RequestAccessToolSurface: 函数段结束，_request_access_safe_hint_from_candidate 到此结束；如果没有这个边界说明，用户不容易看出格式化范围。


# 新增代码+RequestAccessToolSurface: 函数段开始，_request_access_candidates_for_query 从 inventory 读取安全候选；如果没有这段函数，request_access 会重复实现应用发现逻辑。
def _request_access_candidates_for_query(query: str, max_results: int) -> list[dict[str, Any]]:  # 新增代码+RequestAccessToolSurface: 声明候选查询函数；如果没有这一行，调用方无法按应用名拿到安全候选。
    report = query_windows_app_inventory(query=query, include_common=True, max_count=max_results)  # 新增代码+RequestAccessToolSurface: 复用统一 inventory 查询；如果没有这一行，安全过滤和普通应用兜底会失效。
    candidates = report.get("candidates", []) if isinstance(report, dict) else []  # 新增代码+RequestAccessToolSurface: 安全读取候选列表；如果没有这一行，异常报告结构会导致类型错误。
    return [candidate for candidate in candidates if isinstance(candidate, dict)]  # 新增代码+RequestAccessToolSurface: 只返回字典候选；如果没有这一行，坏候选会污染后续格式化。
# 新增代码+RequestAccessToolSurface: 函数段结束，_request_access_candidates_for_query 到此结束；如果没有这个边界说明，用户不容易看出它不碰真实桌面。


# 新增代码+RequestAccessToolSurface: 函数段开始，_request_access_safe_app_hints 生成安全应用建议；如果没有这段函数，授权申请结果无法指导模型避开高风险应用。
def _request_access_safe_app_hints(requested_apps: list[str], max_results: int) -> tuple[list[str], list[dict[str, Any]], list[str]]:  # 新增代码+RequestAccessToolSurface: 声明安全提示生成函数；如果没有这一行，报告无法同时返回文本提示、结构化应用和拒绝目标。
    queries = requested_apps or list(REQUEST_ACCESS_DEFAULT_HINT_QUERIES)  # 新增代码+RequestAccessToolSurface: 有请求则按请求查，无请求则给普通应用示例；如果没有这一行，空请求拿不到任何候选。
    denied_requested_apps = [app_name for app_name in requested_apps if _request_access_is_high_risk_app(app_name)]  # 新增代码+RequestAccessToolSurface: 记录被风险词拒绝的请求目标；如果没有这一行，PowerShell 被过滤后用户不知道原因。
    safe_hints: list[str] = []  # 新增代码+RequestAccessToolSurface: 保存模型可读安全提示；如果没有这一行，函数没有地方累计提示文本。
    safe_apps: list[dict[str, Any]] = []  # 新增代码+RequestAccessToolSurface: 保存结构化安全候选；如果没有这一行，后续 Phase 2 无法复用候选字段。
    seen: set[str] = set()  # 新增代码+RequestAccessToolSurface: 保存候选去重键；如果没有这一行，同一应用可能重复展示。
    for query in queries:  # 新增代码+RequestAccessToolSurface: 按请求或默认查询逐项查找；如果没有这一行，多个目标无法生成对应提示。
        if _request_access_is_high_risk_app(query):  # 新增代码+RequestAccessToolSurface: 跳过高风险查询本身；如果没有这一行，PowerShell 这类目标可能进入 inventory 查询。
            continue  # 新增代码+RequestAccessToolSurface: 继续处理其他普通应用；如果没有这一行，一个危险目标会阻断整个申请提示生成。
        for candidate in _request_access_candidates_for_query(query, max_results):  # 新增代码+RequestAccessToolSurface: 遍历 inventory 返回的候选；如果没有这一行，无法把 Notepad 等普通应用放入提示。
            identity = _request_access_candidate_identity(candidate)  # 新增代码+RequestAccessToolSurface: 生成候选去重键；如果没有这一行，重复候选无法被过滤。
            display_name = _request_access_text(candidate.get("display_name"))  # 新增代码+RequestAccessToolSurface: 读取候选展示名；如果没有这一行，空候选可能被展示。
            app_name = _request_access_text(candidate.get("app_name"))  # 新增代码+RequestAccessToolSurface: 读取候选 app_name；如果没有这一行，授权候选缺少可执行目标。
            risk_text = f"{display_name} {app_name} {_request_access_text(candidate.get('launch_id'))}"  # 新增代码+RequestAccessToolSurface: 拼出风险检查文本；如果没有这一行，候选内部高风险字段无法统一检查。
            if not display_name or not app_name or identity in seen or _request_access_is_high_risk_app(risk_text):  # 新增代码+RequestAccessToolSurface: 过滤空候选、重复候选和危险候选；如果没有这一行，提示会出现无效或危险应用。
                continue  # 新增代码+RequestAccessToolSurface: 跳过不合格候选；如果没有这一行，后续会把它们加入安全提示。
            seen.add(identity)  # 新增代码+RequestAccessToolSurface: 记录已使用候选；如果没有这一行，重复候选会继续出现。
            safe_apps.append({"display_name": display_name, "app_name": app_name, "launch_kind": _request_access_text(candidate.get("launch_kind")), "source": _request_access_text(candidate.get("source"))})  # 新增代码+RequestAccessToolSurface: 保存脱敏后的候选字段；如果没有这一行，Phase 2 不能复用候选做授权范围。
            safe_hints.append(_request_access_safe_hint_from_candidate(candidate))  # 新增代码+RequestAccessToolSurface: 保存模型可读提示；如果没有这一行，测试和模型看不到 Notepad 等安全应用。
            if len(safe_hints) >= max_results:  # 新增代码+RequestAccessToolSurface: 检查是否达到提示上限；如果没有这一行，多个查询可能返回过多内容。
                return safe_hints, safe_apps, denied_requested_apps  # 新增代码+RequestAccessToolSurface: 达到上限就提前返回；如果没有这一行，数量限制不会严格生效。
    return safe_hints, safe_apps, denied_requested_apps  # 新增代码+RequestAccessToolSurface: 返回安全提示、候选和拒绝目标；如果没有这一行，调用方拿不到申请报告材料。
# 新增代码+RequestAccessToolSurface: 函数段结束，_request_access_safe_app_hints 到此结束；如果没有这个边界说明，用户不容易看出安全提示生成范围。


# 新增代码+RequestAccessToolSurface: 函数段开始，request_computer_use_access 创建只读授权申请报告；如果没有这段函数，模型没有 ClaudeCode 风格的 Computer Use 授权申请入口。
def request_computer_use_access(arguments: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+RequestAccessToolSurface: 声明 request_access 主入口；如果没有这一行，测试和 executor 无法调用该工具。
    safe_arguments = dict(arguments or {})  # 新增代码+RequestAccessToolSurface: 复制参数避免修改调用方对象；如果没有这一行，工具内部处理可能污染原始参数。
    requested_apps = _request_access_unique_texts(safe_arguments.get("requested_apps", safe_arguments.get("apps", [])))  # 新增代码+RequestAccessToolSurface: 读取并清洗申请应用；如果没有这一行，工具不知道模型想申请哪些目标。
    reason = _request_access_text(safe_arguments.get("reason"))  # 新增代码+RequestAccessToolSurface: 读取申请原因；如果没有这一行，用户无法判断 agent 为什么要请求桌面控制。
    session_id = _request_access_text(safe_arguments.get("session_id"))  # 新增代码+RequestAccessToolSurface: 读取可选会话标识但不创建授权；如果没有这一行，后续 Phase 2 难以接入会话维度。
    max_results = _request_access_clamped_max_results(safe_arguments.get("max_results", 6))  # 新增代码+RequestAccessToolSurface: 读取安全提示数量上限；如果没有这一行，输出长度不可控。
    safe_hints, safe_apps, denied_requested_apps = _request_access_safe_app_hints(requested_apps, max_results)  # 新增代码+RequestAccessToolSurface: 生成普通应用提示并过滤危险目标；如果没有这一行，request_access 不能体现安全边界。
    requested_grant_flags = {"clipboard_read": _request_access_bool(safe_arguments.get("clipboard_read")), "clipboard_write": _request_access_bool(safe_arguments.get("clipboard_write")), "risky_key_combos": _request_access_bool(safe_arguments.get("risky_key_combos"))}  # 新增代码+RequestAccessToolSurface: 记录模型想申请的可选权限标志；如果没有这一行，后续授权阶段不知道要不要放开剪贴板或高风险快捷键。
    return {"marker": REQUEST_ACCESS_MARKER, "model": REQUEST_ACCESS_MODEL, "access_request_created": True, "grant_created": False, "grant_scope_enforced": False, "phase": "phase1_tool_surface_only", "requested_apps": requested_apps, "denied_requested_apps": denied_requested_apps, "safe_app_hints": safe_hints, "safe_apps": safe_apps, "reason": reason, "session_id": session_id, "requested_grant_flags": requested_grant_flags, "next_phase_required": "phase2_session_grant_lifecycle"}  # 新增代码+RequestAccessToolSurface: 返回只创建申请、不创建授权的结构化报告；如果没有这一行，工具调用没有稳定结果且可能被误解为已授权。
# 新增代码+RequestAccessToolSurface: 函数段结束，request_computer_use_access 到此结束；如果没有这个边界说明，用户不容易看出 Phase 1 只做到工具面。


__all__ = ["REQUEST_ACCESS_MARKER", "REQUEST_ACCESS_MODEL", "request_computer_use_access"]  # 新增代码+RequestAccessToolSurface: 导出稳定 API；如果没有这一行，后续模块不清楚哪些名字可以正式依赖。
