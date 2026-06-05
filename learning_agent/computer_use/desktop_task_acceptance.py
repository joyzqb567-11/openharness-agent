"""Desktop Task Router 成熟验收评估器。"""  # 新增代码+DesktopTaskAcceptance：说明本模块只负责评估桌面任务是否真的走 GUI 路线；如果没有这一行，读者容易把这里误解成真实桌面操作器。
from __future__ import annotations  # 新增代码+DesktopTaskAcceptance：启用延迟类型注解解析；如果没有这一行，后续类型提示在不同 Python 版本下更容易出现兼容问题。

from typing import Any  # 新增代码+DesktopTaskAcceptance：导入 Any 表示证据字典里的动态字段；如果没有这一行，函数类型提示无法描述 JSON 风格输入。

SCRIPT_TOOL_NAMES = {  # 新增代码+DesktopTaskAcceptance：集合段开始，列出会执行脚本或命令的工具名；如果没有这个集合，评估器不知道哪些工具可能绕过 GUI。
    "bash",  # 新增代码+DesktopTaskAcceptance：把 bash 视为脚本工具；如果没有这一行，之前真实失败的 bash 绕路不会被识别。
    "powershell",  # 新增代码+DesktopTaskAcceptance：把 powershell 视为脚本工具；如果没有这一行，Windows 下生成图片再打开软件的路线可能漏网。
    "pwsh",  # 新增代码+DesktopTaskAcceptance：把 PowerShell Core 的 pwsh 视为脚本工具；如果没有这一行，换个命令名就能绕过检测。
    "cmd",  # 新增代码+DesktopTaskAcceptance：把 cmd 视为脚本工具；如果没有这一行，批处理命令生成最终作品时无法被拦住。
    "python",  # 新增代码+DesktopTaskAcceptance：把 python 视为脚本工具；如果没有这一行，Python 生成图片文件可能被误判为 GUI 操作。
    "node",  # 新增代码+DesktopTaskAcceptance：把 node 视为脚本工具；如果没有这一行，Node 脚本生成图片文件可能被误判为 GUI 操作。
}  # 新增代码+DesktopTaskAcceptance：集合段结束，脚本工具名到此固定；如果没有这个边界说明，代码小白不容易看出脚本工具范围。

FINAL_ARTIFACT_ROUTE_TRACES = (  # 新增代码+DesktopTaskAcceptance：元组段开始，列出“脚本生成最终作品”常见痕迹；如果没有这个元组，只看到脚本工具还不能判断它是否绕过 GUI 成品。
    "system.drawing",  # 新增代码+DesktopTaskAcceptance：识别 .NET 画图 API；如果没有这一行，PowerShell 用 System.Drawing 生成图片会漏检。
    "start-process mspaint",  # 新增代码+DesktopTaskAcceptance：识别生成文件后启动 Paint 的路线；如果没有这一行，打开最终 PNG 的行为可能被误判为 GUI 绘图。
    "mspaint.exe",  # 新增代码+DesktopTaskAcceptance：识别命令行启动画图软件；如果没有这一行，Start-Process 或 cmd 打开 Paint 的痕迹可能漏掉。
    "pikachu_for_paint.png",  # 新增代码+DesktopTaskAcceptance：识别这次真实失败产生的最终图片文件名；如果没有这一行，当前回归样本不能被稳定冻结。
    "generate image",  # 新增代码+DesktopTaskAcceptance：识别英文生成图片描述；如果没有这一行，英文命令生成最终图像可能漏检。
    "generated image",  # 新增代码+DesktopTaskAcceptance：识别英文已生成图片描述；如果没有这一行，日志式命令内容可能漏检。
    "draw image",  # 新增代码+DesktopTaskAcceptance：识别英文画图最终制品描述；如果没有这一行，脚本画图路线可能被误判。
    "create image",  # 新增代码+DesktopTaskAcceptance：识别英文创建图片描述；如果没有这一行，常见脚本生成图片命令可能漏检。
    "save image",  # 新增代码+DesktopTaskAcceptance：识别英文保存图片描述；如果没有这一行，脚本保存最终作品可能不被识别。
    "png",  # 新增代码+DesktopTaskAcceptance：识别 PNG 最终图片文件痕迹；如果没有这一行，脚本制品文件名不固定时可能漏检。
    "jpg",  # 新增代码+DesktopTaskAcceptance：识别 JPG 最终图片文件痕迹；如果没有这一行，换成 jpg 后可能绕过检测。
    "jpeg",  # 新增代码+DesktopTaskAcceptance：识别 JPEG 最终图片文件痕迹；如果没有这一行，换成 jpeg 后可能绕过检测。
    "生成图片",  # 新增代码+DesktopTaskAcceptance：识别中文“生成图片”；如果没有这一行，中文脚本描述会漏检。
    "生成图像",  # 新增代码+DesktopTaskAcceptance：识别中文“生成图像”；如果没有这一行，中文图像生成描述会漏检。
    "画图",  # 新增代码+DesktopTaskAcceptance：识别中文“画图”；如果没有这一行，中文自然语言命令痕迹会漏检。
    "最终作品",  # 新增代码+DesktopTaskAcceptance：识别中文最终制品说法；如果没有这一行，评估器难以抓住“成品绕路”的语义。
)  # 修改代码+DesktopTaskAcceptance：用元组右括号正确结束最终制品痕迹列表；如果没有这一行，模块会因为括号不匹配无法导入。

MATURITY_REQUIREMENTS = (  # 新增代码+DesktopTaskAcceptance：元组段开始，列出桌面任务成熟验收必须满足的字段规则；如果没有这个元组，验收条件会散落在函数里难维护。
    ("desktop_task_router_used", "is_true"),  # 新增代码+DesktopTaskAcceptance：要求桌面任务路由已使用；如果没有这一行，普通工具循环可能被误判为成熟路线。
    ("computer_use_gui_route_used", "is_true"),  # 新增代码+DesktopTaskAcceptance：要求 Computer Use GUI 路线已使用；如果没有这一行，脚本或普通工具路线可能混进来。
    ("bash_final_artifact_route_used", "is_false"),  # 新增代码+DesktopTaskAcceptance：要求没有 bash 最终制品路线；如果没有这一行，上次失败路线没有明确门禁。
    ("forbidden_script_generation_used", "is_false"),  # 新增代码+DesktopTaskAcceptance：要求没有禁止脚本生成最终作品；如果没有这一行，任何脚本成品绕路都可能通过。
    ("owned_window_verified", "is_true"),  # 新增代码+DesktopTaskAcceptance：要求已验证 agent 自有窗口；如果没有这一行，动作可能落到用户已有窗口或错误窗口。
    ("gui_action_count", "positive_int"),  # 新增代码+DesktopTaskAcceptance：要求 GUI 动作次数大于 0；如果没有这一行，零 GUI 操作也可能通过。
    ("low_level_event_count", "positive_int"),  # 新增代码+DesktopTaskAcceptance：要求底层鼠标键盘事件大于 0；如果没有这一行，无法证明真实 Computer Use 输入发生。
    ("post_action_screenshot_exists", "is_true"),  # 新增代码+DesktopTaskAcceptance：要求动作后截图存在；如果没有这一行，验收缺少可复盘视觉证据。
)  # 新增代码+DesktopTaskAcceptance：元组段结束，成熟验收条件到此固定；如果没有这个边界说明，代码小白不容易看出必填条件范围。


def _desktop_task_acceptance_text(value: Any) -> str:  # 新增代码+DesktopTaskAcceptance：函数段开始，把任意证据值转成小写文本；如果没有这段函数，工具名和命令内容的大小写差异会让检测不稳定。
    return str(value or "").lower()  # 新增代码+DesktopTaskAcceptance：把 None 兜底为空字符串并转小写；如果没有这一行，缺字段或大小写不同会导致识别失败。
# 新增代码+DesktopTaskAcceptance：函数段结束，_desktop_task_acceptance_text 到此结束；如果没有这个边界说明，代码小白不容易看出文本归一化范围。


def _desktop_task_acceptance_tool_text(tool_call: Any) -> tuple[str, str]:  # 新增代码+DesktopTaskAcceptance：函数段开始，从单个工具调用里提取工具名和命令文本；如果没有这段函数，tool_calls 的不同形状会让主函数很乱。
    if not isinstance(tool_call, dict):  # 新增代码+DesktopTaskAcceptance：先确认工具调用是字典；如果没有这一行，遇到异常数据形状会抛错而不是稳定判定。
        return "", ""  # 新增代码+DesktopTaskAcceptance：异常形状返回空工具名和空命令；如果没有这一行，坏数据会中断整个验收。
    tool_name = _desktop_task_acceptance_text(tool_call.get("tool_name") or tool_call.get("name") or tool_call.get("tool"))  # 新增代码+DesktopTaskAcceptance：兼容常见工具名字段；如果没有这一行，不同日志字段名会导致脚本工具漏检。
    command_text = _desktop_task_acceptance_text(tool_call.get("command") or tool_call.get("cmd") or tool_call.get("input") or tool_call.get("arguments"))  # 新增代码+DesktopTaskAcceptance：兼容常见命令内容字段；如果没有这一行，命令痕迹可能藏在别名字段里无法识别。
    return tool_name, command_text  # 新增代码+DesktopTaskAcceptance：返回归一化后的工具名和命令文本；如果没有这一行，调用方拿不到检测所需信息。
# 新增代码+DesktopTaskAcceptance：函数段结束，_desktop_task_acceptance_tool_text 到此结束；如果没有这个边界说明，代码小白不容易看出工具文本提取范围。


def _desktop_task_acceptance_is_script_tool(tool_name: str) -> bool:  # 新增代码+DesktopTaskAcceptance：函数段开始，判断工具名是否属于脚本工具；如果没有这段函数，主函数会重复写工具名匹配逻辑。
    return any(script_tool in tool_name for script_tool in SCRIPT_TOOL_NAMES)  # 新增代码+DesktopTaskAcceptance：只要工具名包含脚本工具关键词就认为有风险；如果没有这一行，bash/powershell 等绕路不会被统一识别。
# 新增代码+DesktopTaskAcceptance：函数段结束，_desktop_task_acceptance_is_script_tool 到此结束；如果没有这个边界说明，代码小白不容易看出脚本工具判断范围。


def _desktop_task_acceptance_has_final_artifact_trace(command_text: str) -> bool:  # 新增代码+DesktopTaskAcceptance：函数段开始，判断命令内容是否包含最终制品路线痕迹；如果没有这段函数，脚本工具和普通只读命令无法区分。
    return any(route_trace in command_text for route_trace in FINAL_ARTIFACT_ROUTE_TRACES)  # 新增代码+DesktopTaskAcceptance：命中任意最终制品词就判为可疑；如果没有这一行，生成图片或打开成品文件的路线无法被抓住。
# 新增代码+DesktopTaskAcceptance：函数段结束，_desktop_task_acceptance_has_final_artifact_trace 到此结束；如果没有这个边界说明，代码小白不容易看出成品痕迹判断范围。


def _desktop_task_acceptance_detect_script_routes(evidence: dict[str, Any]) -> tuple[bool, bool]:  # 新增代码+DesktopTaskAcceptance：函数段开始，从证据和 tool_calls 中识别禁止脚本路线；如果没有这段函数，主评估器无法冻结上次真实失败。
    forbidden_script_generation_used = bool(evidence.get("forbidden_script_generation_used", False))  # 新增代码+DesktopTaskAcceptance：先尊重上游已经给出的禁止脚本标记；如果没有这一行，上游运行时发现的风险会被丢掉。
    bash_final_artifact_route_used = bool(evidence.get("bash_final_artifact_route_used", False))  # 新增代码+DesktopTaskAcceptance：先尊重上游已经给出的 bash 成品路线标记；如果没有这一行，上游显式标记会失效。
    tool_calls = evidence.get("tool_calls", [])  # 新增代码+DesktopTaskAcceptance：读取工具调用列表；如果没有这一行，评估器无法从真实调用轨迹里补充判断。
    if not isinstance(tool_calls, list):  # 新增代码+DesktopTaskAcceptance：确认工具调用是列表；如果没有这一行，异常 evidence 形状可能让 for 循环误遍历字符串或字典键。
        tool_calls = []  # 新增代码+DesktopTaskAcceptance：异常形状按空列表处理；如果没有这一行，坏数据会干扰验收判断。
    for tool_call in tool_calls:  # 新增代码+DesktopTaskAcceptance：逐条检查工具调用；如果没有这一行，评估器只能看显式字段，无法识别真实绕路痕迹。
        tool_name, command_text = _desktop_task_acceptance_tool_text(tool_call)  # 新增代码+DesktopTaskAcceptance：提取当前工具名和命令文本；如果没有这一行，后续判断没有标准化输入。
        script_tool_used = _desktop_task_acceptance_is_script_tool(tool_name)  # 新增代码+DesktopTaskAcceptance：判断当前工具是否是脚本工具；如果没有这一行，普通 GUI 工具和脚本工具无法区分。
        final_artifact_trace_used = _desktop_task_acceptance_has_final_artifact_trace(command_text)  # 新增代码+DesktopTaskAcceptance：判断命令是否出现最终制品痕迹；如果没有这一行，脚本是否生成最终作品不可知。
        if script_tool_used and final_artifact_trace_used:  # 新增代码+DesktopTaskAcceptance：只有脚本工具加最终制品痕迹同时出现才判为禁止路线；如果没有这一行，普通脚本诊断或普通文字可能被误伤。
            forbidden_script_generation_used = True  # 新增代码+DesktopTaskAcceptance：标记已使用禁止脚本生成最终作品；如果没有这一行，passed 可能错误变成 True。
            bash_final_artifact_route_used = bash_final_artifact_route_used or "bash" in tool_name  # 新增代码+DesktopTaskAcceptance：若工具名含 bash 则标记 bash 最终制品路线；如果没有这一行，上次失败的 bash 专项字段不会被置真。
    return forbidden_script_generation_used, bash_final_artifact_route_used  # 新增代码+DesktopTaskAcceptance：返回两个风险布尔值；如果没有这一行，主评估器拿不到脚本绕路结论。
# 新增代码+DesktopTaskAcceptance：函数段结束，_desktop_task_acceptance_detect_script_routes 到此结束；如果没有这个边界说明，代码小白不容易看出脚本路线检测范围。


def _desktop_task_acceptance_requirement_missing(evidence: dict[str, Any], key: str, rule: str) -> bool:  # 新增代码+DesktopTaskAcceptance：函数段开始，判断单个成熟条件是否缺失；如果没有这段函数，主函数会堆满重复 if。
    value = evidence.get(key)  # 新增代码+DesktopTaskAcceptance：读取当前条件字段值；如果没有这一行，规则判断没有对象。
    if rule == "is_true":  # 新增代码+DesktopTaskAcceptance：处理必须为 True 的条件；如果没有这一行，路由、GUI、窗口和截图要求无法统一判断。
        return not bool(value)  # 新增代码+DesktopTaskAcceptance：不是 True 就算缺失；如果没有这一行，False 或缺字段可能被误判通过。
    if rule == "is_false":  # 新增代码+DesktopTaskAcceptance：处理必须为 False 的条件；如果没有这一行，禁止路线字段无法统一判断。
        return bool(value)  # 新增代码+DesktopTaskAcceptance：为 True 就表示违反条件；如果没有这一行，脚本路线可能通过成熟验收。
    if rule == "positive_int":  # 新增代码+DesktopTaskAcceptance：处理必须大于 0 的计数字段；如果没有这一行，动作次数和事件次数无法统一判断。
        return int(value or 0) <= 0  # 新增代码+DesktopTaskAcceptance：空值或零都算缺失；如果没有这一行，零 GUI/零事件可能被误判通过。
    return True  # 新增代码+DesktopTaskAcceptance：未知规则默认视为缺失；如果没有这一行，写错规则名时可能静默放行。
# 新增代码+DesktopTaskAcceptance：函数段结束，_desktop_task_acceptance_requirement_missing 到此结束；如果没有这个边界说明，代码小白不容易看出单项条件判断范围。


def evaluate_desktop_task_acceptance(evidence: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopTaskAcceptance：函数段开始，评估桌面任务是否满足 mature GUI 路线验收；如果没有这段函数，Task 1 的负向回归没有被测入口。
    checked_evidence = dict(evidence or {})  # 新增代码+DesktopTaskAcceptance：复制输入证据避免原地修改调用方数据；如果没有这一行，评估器可能污染上游运行时记录。
    forbidden_script_generation_used, bash_final_artifact_route_used = _desktop_task_acceptance_detect_script_routes(checked_evidence)  # 新增代码+DesktopTaskAcceptance：识别脚本生成最终作品和 bash 制品路线；如果没有这一行，之前失败路线不会被拦住。
    checked_evidence["forbidden_script_generation_used"] = forbidden_script_generation_used  # 新增代码+DesktopTaskAcceptance：把检测后的禁止脚本结果写回评估副本；如果没有这一行，后续成熟条件仍可能看到旧值。
    checked_evidence["bash_final_artifact_route_used"] = bash_final_artifact_route_used  # 新增代码+DesktopTaskAcceptance：把检测后的 bash 制品结果写回评估副本；如果没有这一行，missing_requirements 不会包含 bash 路线违规。
    missing_requirements = [key for key, rule in MATURITY_REQUIREMENTS if _desktop_task_acceptance_requirement_missing(checked_evidence, key, rule)]  # 新增代码+DesktopTaskAcceptance：按固定成熟条件生成缺失列表；如果没有这一行，调用方不知道哪些验收条件没满足。
    forbidden_route_used = bool(forbidden_script_generation_used or bash_final_artifact_route_used)  # 新增代码+DesktopTaskAcceptance：汇总是否出现任何脚本最终制品绕路；如果没有这一行，decision 无法优先表达根因。
    passed = bool(not forbidden_route_used and not missing_requirements)  # 新增代码+DesktopTaskAcceptance：只有没有禁止路线且没有缺失项才通过；如果没有这一行，评估器无法产出最终通过状态。
    decision = "accepted_desktop_gui_route" if passed else "missing_desktop_task_requirements"  # 新增代码+DesktopTaskAcceptance：先根据是否通过给出默认决策；如果没有这一行，调用方拿不到稳定状态码。
    if forbidden_route_used:  # 新增代码+DesktopTaskAcceptance：脚本最终制品绕路要覆盖普通缺失决策；如果没有这一行，根因会被零 GUI 等次要缺失掩盖。
        decision = "forbidden_script_artifact_route"  # 新增代码+DesktopTaskAcceptance：固定脚本成品绕路失败原因码；如果没有这一行，Task 2/Task 3 无法稳定匹配拒绝结果。
    return {  # 新增代码+DesktopTaskAcceptance：结果字典段开始，返回 Task 1 要求的稳定字段；如果没有这个字典，测试和后续路由器无法读取验收结论。
        "passed": passed,  # 新增代码+DesktopTaskAcceptance：返回是否通过成熟验收；如果没有这一行，调用方不知道任务能否算 GUI 路线成功。
        "decision": decision,  # 新增代码+DesktopTaskAcceptance：返回稳定决策码；如果没有这一行，失败原因只能靠人工猜。
        "forbidden_script_generation_used": forbidden_script_generation_used,  # 新增代码+DesktopTaskAcceptance：返回是否检测到禁止脚本生成最终作品；如果没有这一行，负向回归无法断言核心风险。
        "bash_final_artifact_route_used": bash_final_artifact_route_used,  # 新增代码+DesktopTaskAcceptance：返回是否检测到 bash 最终制品路线；如果没有这一行，上次失败路线缺少专项证据。
        "missing_requirements": missing_requirements,  # 新增代码+DesktopTaskAcceptance：返回缺失成熟条件列表；如果没有这一行，后续修复不知道还差哪些证据。
    }  # 新增代码+DesktopTaskAcceptance：结果字典段结束，桌面任务验收结论到此返回；如果没有这个边界说明，代码小白不容易看出输出范围。
# 新增代码+DesktopTaskAcceptance：函数段结束，evaluate_desktop_task_acceptance 到此结束；如果没有这个边界说明，代码小白不容易看出主评估函数范围。


__all__ = ["evaluate_desktop_task_acceptance"]  # 新增代码+DesktopTaskAcceptance：限定公开导出评估函数；如果没有这一行，通配导入可能暴露内部 helper。
