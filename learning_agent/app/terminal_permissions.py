"""终端权限确认与客户模式自动授权运行时。"""  # 新增代码+AgentPyPhaseJTerminalPermissions: 把真实终端权限交互从 agent.py 移到 app 层；若没有这个文件，主入口会继续承载权限提示、自动授权和验收事件细节。
from __future__ import annotations  # 新增代码+AgentPyPhaseJTerminalPermissions: 延迟解析类型注解，降低脚本模式导入顺序风险；若没有这行代码，部分类型注解可能在导入时过早求值。
from typing import Any  # 新增代码+AgentPyPhaseJTerminalPermissions: 为权限 payload 标注通用 JSON 字典类型；若没有这行代码，函数签名难以表达结构化事件形状。

try:  # 新增代码+AgentPyPhaseJTerminalPermissions: 包运行模式下导入浏览器权限、验收事件和权限 payload helper；若没有这行代码，app 层权限模块无法复用现有事实源。
    from learning_agent.browser.permissions import customer_mode_can_auto_approve_terminal_permission, dangerously_skip_permission_reason, dangerously_skip_permissions_enabled  # 新增代码+AgentPyPhaseJTerminalPermissions: 复用 browser.permissions 中的危险模式和客户模式判断；若没有这行代码，终端权限会重复维护一套安全规则。
    from learning_agent.observability.acceptance_events import emit_acceptance_event  # 新增代码+AgentPyPhaseJTerminalPermissions: 导入验收事件输出函数；若没有这行代码，controller 无法观察权限请求和自动授权。
    from learning_agent.observability.permission_events import build_permission_event_payload as build_permission_event_payload_from_observability  # 新增代码+AgentPyPhaseJTerminalPermissions: 导入结构化权限 payload 构造器；若没有这行代码，终端权限只能靠原始字符串审计。
except ModuleNotFoundError as error:  # 新增代码+AgentPyPhaseJTerminalPermissions: 兼容 start_oauth_agent.bat 直接脚本模式；若没有这行代码，缺少 learning_agent 包名前缀时会启动失败。
    if error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.permissions", "learning_agent.observability", "learning_agent.observability.acceptance_events", "learning_agent.observability.permission_events"}:  # 新增代码+AgentPyPhaseJTerminalPermissions: 只允许路径前缀差异进入 fallback；若没有这行代码，真实导入 bug 会被误吞。
        raise  # 新增代码+AgentPyPhaseJTerminalPermissions: 重新抛出非目标路径导入错误；若没有这行代码，排查权限模块内部问题会很困难。
    from browser.permissions import customer_mode_can_auto_approve_terminal_permission, dangerously_skip_permission_reason, dangerously_skip_permissions_enabled  # 新增代码+AgentPyPhaseJTerminalPermissions: 脚本模式下复用同级 browser.permissions；若没有这行代码，bat 入口无法判断危险模式和客户模式。
    from observability.acceptance_events import emit_acceptance_event  # 新增代码+AgentPyPhaseJTerminalPermissions: 脚本模式下导入验收事件输出函数；若没有这行代码，bat 入口权限事件无法落盘。
    from observability.permission_events import build_permission_event_payload as build_permission_event_payload_from_observability  # 新增代码+AgentPyPhaseJTerminalPermissions: 脚本模式下导入权限 payload helper；若没有这行代码，bat 入口权限事件缺少结构化字段。

_DANGEROUS_PERMISSION_NOTICE_PRINTED = False  # 新增代码+AgentPyPhaseJTerminalPermissions: 记录本进程是否已显示危险调试提示；若没有这行代码，长任务会反复刷同一条权限提示。


def build_permission_event_payload(action: str) -> dict[str, Any]:  # 新增代码+AgentPyPhaseJTerminalPermissions: 函数段开始，把人类可读权限文本转成可审计 payload；若没有这段函数，controller 只能靠 contains 猜权限类型。
    return build_permission_event_payload_from_observability(action)  # 新增代码+AgentPyPhaseJTerminalPermissions: 委托 observability 层解析权限文本；若没有这行代码，本模块会重复实现 payload 解析。
# 新增代码+AgentPyPhaseJTerminalPermissions: 函数段结束，build_permission_event_payload 到此结束；若没有这个边界说明，用户不容易看出这里只做 payload 解析委托。


def customer_mode_can_auto_approve_permission(permission_payload: dict[str, Any]) -> bool:  # 新增代码+AgentPyPhaseJTerminalPermissions: 函数段开始，判断客户终端模式是否能自动允许本次权限；若没有这段函数，MCP 启动仍会要求用户输入 y。
    return customer_mode_can_auto_approve_terminal_permission(permission_payload)  # 新增代码+AgentPyPhaseJTerminalPermissions: 委托 browser.permissions 的客户模式白名单；若没有这行代码，终端权限会复制并分叉白名单规则。
# 新增代码+AgentPyPhaseJTerminalPermissions: 函数段结束，customer_mode_can_auto_approve_permission 到此结束；若没有这个边界说明，用户不容易看出客户模式判断范围。


def emit_permission_auto_approved(action: str, permission_payload: dict[str, Any], reason: str) -> None:  # 新增代码+AgentPyPhaseJTerminalPermissions: 函数段开始，统一发送自动授权审计事件；若没有这段函数，危险模式和客户模式会各自拼事件。
    auto_payload = dict(permission_payload)  # 新增代码+AgentPyPhaseJTerminalPermissions: 复制权限 payload，避免污染调用方对象；若没有这行代码，后续复用 payload 可能被自动授权字段污染。
    auto_payload["action"] = action  # 新增代码+AgentPyPhaseJTerminalPermissions: 保留原始动作文本方便人类复盘；若没有这行代码，审计事件会缺少完整上下文。
    auto_payload["allowed"] = True  # 新增代码+AgentPyPhaseJTerminalPermissions: 标记本次自动授权结果为允许；若没有这行代码，controller 无法判断自动授权方向。
    auto_payload["auto_approved"] = True  # 新增代码+AgentPyPhaseJTerminalPermissions: 标记这不是用户手动输入 y；若没有这行代码，复盘时会误以为有人手工批准。
    auto_payload["reason"] = reason  # 新增代码+AgentPyPhaseJTerminalPermissions: 写入自动授权原因；若没有这行代码，审计日志无法解释为什么放行。
    emit_acceptance_event("permission_auto_approved", auto_payload)  # 新增代码+AgentPyPhaseJTerminalPermissions: 写入验收事件但不触发 permission_required；若没有这行代码，controller 无法证明无 y 模式生效。
# 新增代码+AgentPyPhaseJTerminalPermissions: 函数段结束，emit_permission_auto_approved 到此结束；若没有这个边界说明，用户不容易看出自动授权事件的固定字段。


def ask_permission_from_terminal(action: str) -> bool:  # 新增代码+AgentPyPhaseJTerminalPermissions: 函数段开始，普通命令行权限确认入口；若没有这段函数，未知或敏感操作没有人工确认兜底。
    permission_payload = build_permission_event_payload(action)  # 新增代码+AgentPyPhaseJTerminalPermissions: 生成结构化权限 payload；若没有这行代码，permission_required 事件只有原始文本。
    if dangerously_skip_permissions_enabled():  # 新增代码+AgentPyPhaseJTerminalPermissions: 危险调试模式下不等待用户输入 y/N；若没有这行代码，本地真实浏览器调试会被权限焦点反复打断。
        target = str(permission_payload.get("tool_name") or permission_payload.get("permission_kind") or "terminal_permission")  # 新增代码+AgentPyPhaseJTerminalPermissions: 提取本次自动允许对象名称；若没有这行代码，审计原因会太模糊。
        emit_permission_auto_approved(action, permission_payload, dangerously_skip_permission_reason(target))  # 新增代码+AgentPyPhaseJTerminalPermissions: 写入危险模式自动授权事件；若没有这行代码，controller 无法证明危险模式没有人工输入。
        return True  # 新增代码+AgentPyPhaseJTerminalPermissions: 直接允许本次操作继续执行；若没有这行代码，危险模式开关不会真正跳过权限。
    emit_acceptance_event("permission_required", permission_payload)  # 新增代码+AgentPyPhaseJTerminalPermissions: 等待用户授权前写结构化状态事件；若没有这行代码，外部 controller 无法按工具名和 URL 参数精确授权。
    answer = input(f"允许 agent 执行这个操作吗？\n{action}\n[y/N] ").strip().lower()  # 新增代码+AgentPyPhaseJTerminalPermissions: 在真实终端向用户显示动作并读取 y/N；若没有这行代码，人工权限确认没有输入来源。
    allowed = answer in {"y", "yes"}  # 新增代码+AgentPyPhaseJTerminalPermissions: 把用户回答转换成布尔结果；若没有这行代码，返回值和审计事件容易不一致。
    answered_payload = dict(permission_payload)  # 新增代码+AgentPyPhaseJTerminalPermissions: 复制 payload 作为回答事件基础；若没有这行代码，permission_answered 会丢失工具名和参数。
    answered_payload["allowed"] = allowed  # 新增代码+AgentPyPhaseJTerminalPermissions: 把用户是否允许写入回答事件；若没有这行代码，controller 无法确认 y/n 结果。
    emit_acceptance_event("permission_answered", answered_payload)  # 新增代码+AgentPyPhaseJTerminalPermissions: 用户回答后写结构化结果事件；若没有这行代码，外部 agent 无法把 y/n 对应到具体工具和参数。
    return allowed  # 新增代码+AgentPyPhaseJTerminalPermissions: 返回用户授权结果；若没有这行代码，调用方无法决定是否执行敏感操作。
# 新增代码+AgentPyPhaseJTerminalPermissions: 函数段结束，ask_permission_from_terminal 到此结束；若没有这个边界说明，用户不容易看出人工权限确认完整流程。


def should_print_dangerous_permission_notice_once() -> bool:  # 新增代码+AgentPyPhaseJTerminalPermissions: 函数段开始，判断危险调试提示本进程是否还需要打印；若没有这段函数，长任务每次自动授权都会重复刷屏。
    global _DANGEROUS_PERMISSION_NOTICE_PRINTED  # 新增代码+AgentPyPhaseJTerminalPermissions: 声明要更新模块级去重标记；若没有这行代码，函数内赋值只会创建局部变量。
    if _DANGEROUS_PERMISSION_NOTICE_PRINTED:  # 新增代码+AgentPyPhaseJTerminalPermissions: 检查危险提示是否已经打印过；若没有这行代码，无法区分首次和后续自动授权。
        return False  # 新增代码+AgentPyPhaseJTerminalPermissions: 已打印过则不再显示；若没有这行代码，终端会继续出现重复危险提示。
    _DANGEROUS_PERMISSION_NOTICE_PRINTED = True  # 新增代码+AgentPyPhaseJTerminalPermissions: 标记危险提示已经显示；若没有这行代码，下一次权限请求仍会再次打印。
    return True  # 新增代码+AgentPyPhaseJTerminalPermissions: 首次进入时允许打印；若没有这行代码，用户完全看不到当前处于危险调试模式。
# 新增代码+AgentPyPhaseJTerminalPermissions: 函数段结束，should_print_dangerous_permission_notice_once 到此结束；若没有这个边界说明，用户不容易看出它只负责去重提示。


def ask_permission_from_terminal_customer_mode(action: str, show_progress: bool = True) -> bool:  # 新增代码+AgentPyPhaseJTerminalPermissions: 函数段开始，客户可见终端默认权限入口；若没有这段函数，main() 无法在 JSON 模式关闭进度输出。
    permission_payload = build_permission_event_payload(action)  # 新增代码+AgentPyPhaseJTerminalPermissions: 解析权限动作供白名单判断；若没有这行代码，无法知道本次是不是项目 MCP 启动。
    if dangerously_skip_permissions_enabled():  # 新增代码+AgentPyPhaseJTerminalPermissions: 危险模式优先于客户白名单，所有权限都自动允许；若没有这行代码，非 MCP 启动权限仍可能弹出 y/N。
        target = str(permission_payload.get("tool_name") or permission_payload.get("permission_kind") or "terminal_permission")  # 新增代码+AgentPyPhaseJTerminalPermissions: 读取工具名或权限类型供审计；若没有这行代码，自动授权原因会太模糊。
        emit_permission_auto_approved(action, permission_payload, dangerously_skip_permission_reason(target))  # 新增代码+AgentPyPhaseJTerminalPermissions: 写入危险模式自动授权事件；若没有这行代码，真实验收无法确认权限是自动放开的。
        if show_progress and should_print_dangerous_permission_notice_once():  # 新增代码+AgentPyPhaseJTerminalPermissions: 只在真实人类终端首次展示危险模式提示；若没有这行代码，桌面循环会反复打印同一句授权提示。
            print("Agent > 危险调试模式已开启，本次权限请求已自动允许。", flush=True)  # 新增代码+AgentPyPhaseJTerminalPermissions: 告诉用户当前是全放开调试模式且只提醒一次；若没有这行代码，用户可能不知道权限已自动放开。
        return True  # 新增代码+AgentPyPhaseJTerminalPermissions: 直接允许本次权限请求；若没有这行代码，危险模式不会覆盖客户模式以外的权限。
    if customer_mode_can_auto_approve_permission(permission_payload):  # 新增代码+AgentPyPhaseJTerminalPermissions: 判断是否命中客户模式启动白名单；若没有这行代码，启动 MCP 仍会弹 y/N。
        emit_permission_auto_approved(action, permission_payload, "客户模式默认启动项目内置 MCP server")  # 新增代码+AgentPyPhaseJTerminalPermissions: 记录自动启动审计事件；若没有这行代码，默认放行缺少证据。
        if show_progress:  # 新增代码+AgentPyPhaseJTerminalPermissions: 只有人类可见终端才打印进度；若没有这行代码，--output-json 会混入普通文本导致机器解析失败。
            print("Agent > 正在启动 MCP 工具...", flush=True)  # 新增代码+AgentPyPhaseJTerminalPermissions: 用进度提示替代 y/N 提示；若没有这行代码，用户不知道 agent 正在启动工具。
        return True  # 新增代码+AgentPyPhaseJTerminalPermissions: 返回允许启动；若没有这行代码，LearningAgent 会认为用户拒绝 MCP。
    return ask_permission_from_terminal(action)  # 新增代码+AgentPyPhaseJTerminalPermissions: 未命中白名单时保留原人工授权流程；若没有这行代码，敏感或未知权限没有安全兜底。
# 新增代码+AgentPyPhaseJTerminalPermissions: 函数段结束，ask_permission_from_terminal_customer_mode 到此结束；若没有这个边界说明，用户不容易看出客户模式和人工兜底的边界。
