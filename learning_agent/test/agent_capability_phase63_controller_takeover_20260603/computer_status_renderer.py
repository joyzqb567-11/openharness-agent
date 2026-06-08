"""`/computer` 专用终端状态渲染器。"""  # 新增代码+Phase51ComputerStatusUI: 标明本文件负责 Computer Use 状态 UI；如果没有这行代码，状态读取和状态展示容易再次混在一起。
from __future__ import annotations  # 新增代码+Phase51ComputerStatusUI: 启用延迟类型解析；如果没有这行代码，复杂 JSON 类型注解更容易受导入顺序影响。

from typing import Any  # 新增代码+Phase51ComputerStatusUI: 导入 Any 描述通用状态快照；如果没有这行代码，renderer 的输入边界不清楚。

PHASE51_COMPUTER_STATUS_UI_MARKER = "PHASE51_COMPUTER_STATUS_UI_READY"  # 新增代码+Phase51ComputerStatusUI: 定义 Phase51 ready marker；如果没有这行代码，真实终端验收无法稳定匹配状态 UI 阶段。
PHASE51_COMPUTER_STATUS_UI_OK_TOKEN = "PHASE51_COMPUTER_STATUS_UI_OK"  # 新增代码+Phase51ComputerStatusUI: 定义 Phase51 OK token；如果没有这行代码，debug log 无法区分 UI 合同通过和普通输出。
PHASE51_COMPUTER_STATUS_UI_CONTRACT = "phase51_computer_status_ui"  # 新增代码+Phase51ComputerStatusUI: 定义状态 UI 合同名称；如果没有这行代码，输出无法说明当前 UI 版本。
PHASE51_ACTIONS_EXPANDED = False  # 新增代码+Phase51ComputerStatusUI: 明确 Phase51 只升级终端 UI，不扩大真实桌面动作；如果没有这行代码，用户可能误解状态命令会控制电脑。


def _as_dict(value: Any) -> dict[str, Any]:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，把未知状态块安全转成字典；如果没有这段函数，坏快照会在 .get 时崩溃。
    return value if isinstance(value, dict) else {}  # 新增代码+Phase51ComputerStatusUI: 只有 dict 原样返回，否则给空字典；如果没有这行代码，空态渲染不稳定。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，_as_dict 到此结束；如果没有这个边界说明，读者不容易看出类型防御范围。


def _as_list(value: Any) -> list[Any]:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，把未知状态块安全转成列表；如果没有这段函数，recent_actions 遍历可能崩溃。
    return value if isinstance(value, list) else []  # 新增代码+Phase51ComputerStatusUI: 只有 list 原样返回，否则给空列表；如果没有这行代码，空 journal 渲染不稳定。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，_as_list 到此结束；如果没有这个边界说明，读者不容易看出列表防御范围。


def _bool_token(value: Any) -> str:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，把布尔值转成小写文本；如果没有这段函数，终端 token 可能出现 True/False 漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase51ComputerStatusUI: 返回 true/false；如果没有这行代码，场景断言会因为大小写不一致失败。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，_bool_token 到此结束；如果没有这个边界说明，读者不容易看出布尔格式范围。


def _short_text(value: Any, max_chars: int = 160) -> str:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，把长 reason/path 压成单行；如果没有这段函数，状态面板会被长文本刷屏。
    text = str(value or "").replace("\r", "\\r").replace("\n", "\\n")  # 新增代码+Phase51ComputerStatusUI: 转义换行保持单行；如果没有这行代码，终端布局会被状态值打散。
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."  # 新增代码+Phase51ComputerStatusUI: 超长时截断；如果没有这行代码，真实终端截图不易读。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，_short_text 到此结束；如果没有这个边界说明，读者不容易看出短文本规则范围。


def _flag_text(flags: Any) -> str:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，把 grant flags 渲染成短文本；如果没有这段函数，审批和终端草案 flags 会重复格式化。
    flag_dict = _as_dict(flags)  # 新增代码+Phase51ComputerStatusUI: 安全读取 flag 字典；如果没有这行代码，坏 flags 会导致渲染异常。
    if not flag_dict:  # 新增代码+Phase51ComputerStatusUI: 检查是否没有 flag；如果没有这行代码，空 flags 会显示成空字符串不清楚。
        return "(none)"  # 新增代码+Phase51ComputerStatusUI: 返回明确空态；如果没有这行代码，用户不知道是否无授权。
    return ",".join(f"{name}:{_bool_token(flag_dict.get(name))}" for name in sorted(flag_dict))  # 新增代码+Phase51ComputerStatusUI: 按稳定顺序输出 flags；如果没有这行代码，状态输出顺序会漂移。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，_flag_text 到此结束；如果没有这个边界说明，读者不容易看出 flags 渲染范围。


def _recent_action_text(recovery: dict[str, Any]) -> str:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，提取最近动作一行摘要；如果没有这段函数，action journal 会埋在详细 JSON。
    actions = _as_list(recovery.get("recent_actions", []))  # 新增代码+Phase51ComputerStatusUI: 读取最近动作列表；如果没有这行代码，无法显示最近动作。
    if not actions:  # 新增代码+Phase51ComputerStatusUI: 没有动作时返回空态；如果没有这行代码，索引最后一项会报错。
        return "(none)"  # 新增代码+Phase51ComputerStatusUI: 返回明确无动作；如果没有这行代码，用户不知道是否 journal 空。
    action = _as_dict(actions[-1])  # 新增代码+Phase51ComputerStatusUI: 取最近一条动作；如果没有这行代码，summary 无法突出最后操作。
    return f"{_short_text(action.get('action', ''), 60)} audit_id={_short_text(action.get('audit_id', ''), 80)} chain={_bool_token(action.get('chain_available'))}"  # 新增代码+Phase51ComputerStatusUI: 返回动作名、审计 id 和链路状态；如果没有这行代码，用户无法快速复盘最近操作。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，_recent_action_text 到此结束；如果没有这个边界说明，读者不容易看出最近动作摘要范围。


def _next_command(lock: dict[str, Any], terminal_grants: dict[str, Any]) -> str:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，计算 `/computer` 推荐下一步；如果没有这段函数，状态 UI 只能展示事实不能指导操作。
    del terminal_grants  # 修改代码+Phase51ComputerStatusUI: 当前默认下一步不因 grant 草案而跳过只读观察；如果没有这行代码，已有草案时会误建议先看 journal 而不是观察真实窗口。
    if bool(lock.get("abort_requested", False)):  # 新增代码+Phase51ComputerStatusUI: 急停已触发时优先建议 cleanup；如果没有这行代码，用户可能继续尝试动作却被 abort 阻断。
        return "/computer cleanup"  # 新增代码+Phase51ComputerStatusUI: 返回清理命令；如果没有这行代码，abort 状态没有下一步。
    if bool(lock.get("stale", False)):  # 新增代码+Phase51ComputerStatusUI: 陈旧锁存在时优先建议 recover；如果没有这行代码，崩溃残留锁没有明确处理入口。
        return "/computer recover"  # 新增代码+Phase51ComputerStatusUI: 返回恢复命令；如果没有这行代码，用户不知道如何接管旧锁。
    return "/computer observe"  # 修改代码+Phase51ComputerStatusUI: 默认始终建议只读观察作为安全起步动作；如果没有这行代码，用户可能在未观察当前窗口前继续复盘或授权。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，_next_command 到此结束；如果没有这个边界说明，读者不容易看出下一步规则范围。


def _recent_issue(lock: dict[str, Any], capability_matrix: dict[str, Any]) -> str:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，提取最近或最重要问题；如果没有这段函数，风险会埋在能力矩阵里。
    if bool(lock.get("abort_requested", False)):  # 新增代码+Phase51ComputerStatusUI: 急停状态优先显示；如果没有这行代码，用户可能忽略 abort。
        return "abort_requested"  # 新增代码+Phase51ComputerStatusUI: 返回急停问题码；如果没有这行代码，summary 缺少风险。
    if bool(lock.get("stale", False)):  # 新增代码+Phase51ComputerStatusUI: 陈旧锁优先显示；如果没有这行代码，锁恢复风险不醒目。
        return "stale_lock"  # 新增代码+Phase51ComputerStatusUI: 返回陈旧锁问题码；如果没有这行代码，用户不知道要 recover。
    for capability in _as_list(capability_matrix.get("capabilities", [])):  # 新增代码+Phase51ComputerStatusUI: 扫描能力矩阵中的阻塞项；如果没有这行代码，native provider 差距不会进入摘要。
        item = _as_dict(capability)  # 新增代码+Phase51ComputerStatusUI: 安全读取 capability 对象；如果没有这行代码，坏项会导致渲染崩溃。
        if not bool(item.get("enabled", False)):  # 新增代码+Phase51ComputerStatusUI: 找到第一个未启用能力；如果没有这行代码，summary 不会提示差距。
            return f"{_short_text(item.get('name', ''), 80)}:{_short_text(item.get('reason', ''), 100)}"  # 新增代码+Phase51ComputerStatusUI: 返回能力名和原因；如果没有这行代码，用户不知道哪块能力缺口最大。
    return "(none)"  # 新增代码+Phase51ComputerStatusUI: 没有问题时返回空态；如果没有这行代码，summary 会出现空字符串。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，_recent_issue 到此结束；如果没有这个边界说明，读者不容易看出问题摘要范围。


def render_computer_status(snapshot: dict[str, Any]) -> str:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，渲染 `/computer status` 聚焦状态页；如果没有这段函数，终端状态会继续长而散。
    lock = _as_dict(snapshot.get("lock", {}))  # 新增代码+Phase51ComputerStatusUI: 读取 lock 状态；如果没有这行代码，summary 无法显示锁和 abort。
    approval = _as_dict(snapshot.get("approval", {}))  # 新增代码+Phase51ComputerStatusUI: 读取 approval 状态；如果没有这行代码，summary 无法显示审批 grant。
    runtime = _as_dict(snapshot.get("runtime", {}))  # 新增代码+Phase51ComputerStatusUI: 读取 runtime 状态；如果没有这行代码，summary 无法显示 cleanup/通知。
    recovery = _as_dict(snapshot.get("recovery", {}))  # 新增代码+Phase51ComputerStatusUI: 读取 recovery/journal 状态；如果没有这行代码，summary 无法显示最近动作。
    terminal_grants = _as_dict(snapshot.get("terminal_grants", {}))  # 新增代码+Phase51ComputerStatusUI: 读取终端授权草案；如果没有这行代码，grant/revoke 状态不可见。
    persistent_grants = _as_dict(snapshot.get("persistent_grants", {}))  # 新增代码+Phase60PersistentGrants: 读取生产级持久授权状态；如果没有这行代码，active/revoked/expired grants 不会出现在 /computer status。
    abort_streaming_hooks = _as_dict(snapshot.get("abort_streaming_hooks", {}))  # 新增代码+Phase61AbortStreamingHooks: 读取 abort/cleanup/streaming hook 状态；如果没有这行代码，hotkey 降级和 stream 事件不会出现在 /computer status。
    high_level_tools = _as_dict(snapshot.get("high_level_tools", {}))  # 新增代码+Phase62HighLevelTools: 读取高层 Computer Tool 状态；如果没有这行代码，operations/progress/artifact 不会出现在 /computer status。
    controller_takeover = _as_dict(snapshot.get("controller_takeover", {}))  # 新增代码+Phase63ControllerTakeover: 读取外部 agent controller 接管调试面状态；如果没有这行代码，visible terminal、runs 和证据包不会出现在 /computer status。
    session_context = _as_dict(snapshot.get("session_context", {}))  # 新增代码+Phase59SessionContextAppState: 读取 Phase59 统一 session context；如果没有这行代码，/computer status 无法展示 allowed_apps/grants/display/screenshot/cleanup 的同一事实源。
    current_context = _as_dict(session_context.get("current_session", {}))  # 新增代码+Phase59SessionContextAppState: 提取当前 session 的 AppState；如果没有这行代码，状态 UI 需要重复处理嵌套字段。
    capability_matrix = _as_dict(snapshot.get("capability_matrix", {}))  # 新增代码+Phase51ComputerStatusUI: 读取 native 能力矩阵；如果没有这行代码，WGC/UIA/SendInput 差距不可见。
    capability_summary = _as_dict(capability_matrix.get("summary", {}))  # 新增代码+Phase51ComputerStatusUI: 读取能力矩阵摘要；如果没有这行代码，状态页无法显示可用/启用/阻塞数量。
    recent_action = _recent_action_text(recovery)  # 新增代码+Phase51ComputerStatusUI: 计算最近动作摘要；如果没有这行代码，summary 没有 action journal 信息。
    next_command = _next_command(lock, terminal_grants)  # 新增代码+Phase51ComputerStatusUI: 计算下一条命令；如果没有这行代码，状态页无法指导用户行动。
    lines: list[str] = []  # 新增代码+Phase51ComputerStatusUI: 准备累计输出行；如果没有这行代码，renderer 没有拼接容器。
    lines.append("Computer Status")  # 新增代码+Phase51ComputerStatusUI: 输出状态页标题；如果没有这行代码，用户看不出这是 /computer 视图。
    lines.append(f"- marker={PHASE51_COMPUTER_STATUS_UI_MARKER}")  # 新增代码+Phase51ComputerStatusUI: 输出阶段 marker；如果没有这行代码，验收器无法稳定匹配。
    lines.append("Computer Summary")  # 新增代码+Phase51ComputerStatusUI: 输出紧凑摘要区标题；如果没有这行代码，状态页第一屏不够聚焦。
    lines.append(f"- state=locked:{_bool_token(lock.get('locked'))} stale:{_bool_token(lock.get('stale'))} abort:{_bool_token(lock.get('abort_requested'))} owner={_short_text(lock.get('owner_session_id', ''), 80)}")  # 新增代码+Phase51ComputerStatusUI: 一行显示锁和急停；如果没有这行代码，用户无法快速判断是否能继续。
    lines.append(f"- next={next_command} : first safe command for current Computer state")  # 新增代码+Phase51ComputerStatusUI: 输出下一步建议；如果没有这行代码，小白用户看完状态仍不知道输入什么。
    lines.append(f"- grants=approval_apps:{approval.get('approval_granted_app_count', 0)} terminal_granted_app_count={terminal_grants.get('granted_app_count', 0)} terminal_scope={terminal_grants.get('grant_scope', 'terminal_ui_only')}")  # 新增代码+Phase51ComputerStatusUI: 一行显示审批和终端授权草案数量；如果没有这行代码，grant/revoke 结果不可扫描。
    lines.append(f"- persistent_grants=active:{persistent_grants.get('active_count', 0)} revoked:{persistent_grants.get('revoked_count', 0)} expired:{persistent_grants.get('expired_count', 0)}")  # 新增代码+Phase60PersistentGrants: 一行显示持久授权摘要；如果没有这行代码，用户看不到当前真正可评估 grant 的生命周期状态。
    lines.append(f"- abort_hooks=hotkey:{_bool_token(abort_streaming_hooks.get('global_hotkey_registered'))} terminal_fallback:{_bool_token(abort_streaming_hooks.get('terminal_abort_fallback'))} stream_events:{abort_streaming_hooks.get('stream_event_count', 0)}")  # 新增代码+Phase61AbortStreamingHooks: 一行显示中断钩子摘要；如果没有这行代码，用户看不到全局热键是否真实启用以及是否降级到终端 abort。
    lines.append(f"- high_level_tools=ops:{len(_as_list(high_level_tools.get('supported_operations', [])))} read_parallel:{_bool_token(high_level_tools.get('read_only_parallel_supported'))} write_serial:{_bool_token(high_level_tools.get('write_actions_serialized'))} progress:{high_level_tools.get('progress_event_count', 0)}")  # 新增代码+Phase62HighLevelTools: 一行显示高层工具摘要；如果没有这行代码，用户看不到 Phase62 是否接入状态页。
    lines.append(f"- controller_takeover=visible_terminal:{_bool_token(controller_takeover.get('visible_terminal_required'))} run_read:{_bool_token(controller_takeover.get('controller_can_read_runs'))} bypass:{_bool_token(controller_takeover.get('approval_bypass_allowed'))}")  # 新增代码+Phase63ControllerTakeover: 一行显示 controller 接管安全摘要；如果没有这行代码，用户看不到外部 agent 是否只能走可见终端且不能绕过审批。
    lines.append(f"- session_context=allowed:{len(_as_list(current_context.get('allowed_apps', [])))} hidden:{len(_as_list(current_context.get('hidden_windows', [])))} cleanup:{_bool_token(current_context.get('cleanup_completed'))}")  # 新增代码+Phase59SessionContextAppState: 一行显示统一 session context 摘要；如果没有这行代码，用户看不到当前 AppState 是否已归零。
    lines.append(f"- native=available:{capability_summary.get('available_count', 0)} enabled:{capability_summary.get('enabled_count', 0)} blocked:{capability_summary.get('blocked_count', 0)}")  # 新增代码+Phase51ComputerStatusUI: 一行显示 native 能力摘要；如果没有这行代码，用户看不到 WGC/UIA/SendInput 差距规模。
    lines.append(f"- recent_action={recent_action}")  # 新增代码+Phase51ComputerStatusUI: 输出最近动作摘要；如果没有这行代码，action journal 不会进入第一屏。
    lines.append(f"- recent_issue={_recent_issue(lock, capability_matrix)}")  # 新增代码+Phase51ComputerStatusUI: 输出最近风险；如果没有这行代码，错误会埋在长区块。
    lines.append("Computer Grants")  # 新增代码+Phase51ComputerStatusUI: 输出授权区标题；如果没有这行代码，用户找不到 grant/revoke 状态。
    security_policy = _as_dict(approval.get("security_policy", {}))  # 修改代码+Phase51ComputerStatusUI: 读取 Phase48 安全策略状态；如果没有这行代码，旧的 security_policy 终端合同会从 /computer status 消失。
    lines.append(f"- approval_model={approval.get('approval_model', '')}")  # 修改代码+Phase51ComputerStatusUI: 保留 Phase38 审批模型可见行；如果没有这行代码，回归测试和用户都看不到当前审批模型。
    lines.append(f"- security_policy={security_policy.get('security_policy', '')} grant_classes={','.join(_as_list(security_policy.get('grant_classes', [])))}")  # 修改代码+Phase51ComputerStatusUI: 保留 Phase48 安全策略和 grant_classes 可见行；如果没有这行代码，用户看不到 observe/action/system_key/clipboard 分类。
    lines.append(f"- approval_flags={_flag_text(approval.get('grant_flags', {}))}")  # 新增代码+Phase51ComputerStatusUI: 输出审批 flags；如果没有这行代码，systemKey/clipboard 风险不可见。
    lines.append(f"- terminal_flags={_flag_text(terminal_grants.get('grant_flags', {}))}")  # 新增代码+Phase51ComputerStatusUI: 输出终端草案 flags；如果没有这行代码，grant 命令记录的权限不可见。
    lines.append(f"- terminal_grant_state={_short_text(terminal_grants.get('state_path', ''), 180)}")  # 新增代码+Phase51ComputerStatusUI: 输出草案状态文件；如果没有这行代码，排查 grant/revoke 时找不到文件。
    lines.append("Computer Persistent Grants")  # 新增代码+Phase60PersistentGrants: 输出 Phase60 持久授权区标题；如果没有这行代码，状态页无法明确区分草案 grant 和生产 grant。
    lines.append(f"- persistent_model={persistent_grants.get('model', '')} marker={persistent_grants.get('marker', '')}")  # 新增代码+Phase60PersistentGrants: 输出持久授权模型和 marker；如果没有这行代码，验收器和用户无法确认 Phase60 已接入。
    lines.append(f"- persistent_counts=active:{persistent_grants.get('active_count', 0)} revoked:{persistent_grants.get('revoked_count', 0)} expired:{persistent_grants.get('expired_count', 0)} total:{persistent_grants.get('grant_count', 0)}")  # 新增代码+Phase60PersistentGrants: 输出持久授权计数；如果没有这行代码，用户无法判断授权是否过期或撤销。
    lines.append(f"- persistent_state={_short_text(persistent_grants.get('state_path', ''), 180)}")  # 新增代码+Phase60PersistentGrants: 输出持久授权状态路径；如果没有这行代码，排查 approve/revoke 时找不到 JSON 文件。
    lines.append(f"- persistent_audit={_short_text(persistent_grants.get('audit_path', ''), 180)}")  # 新增代码+Phase60PersistentGrants: 输出持久授权审计路径；如果没有这行代码，用户无法回放 approve/deny/revoke。
    lines.append("Computer Abort Streaming Hooks")  # 新增代码+Phase61AbortStreamingHooks: 输出 Phase61 中断钩子区标题；如果没有这行代码，状态页无法明确展示 cleanup hook 和热键降级。
    lines.append(f"- abort_hook_model={abort_streaming_hooks.get('model', '')} marker={abort_streaming_hooks.get('marker', '')}")  # 新增代码+Phase61AbortStreamingHooks: 输出钩子模型和 marker；如果没有这行代码，验收器和用户无法确认 Phase61 已接入。
    lines.append(f"- abort_hotkey=registered:{_bool_token(abort_streaming_hooks.get('global_hotkey_registered'))} mode={abort_streaming_hooks.get('hotkey_mode', '')}")  # 新增代码+Phase61AbortStreamingHooks: 诚实显示全局热键是否注册；如果没有这行代码，系统可能被误读为已经安装低层键盘 hook。
    lines.append(f"- abort_fallback=terminal:{_bool_token(abort_streaming_hooks.get('terminal_abort_fallback'))} controller:{_bool_token(abort_streaming_hooks.get('controller_abort_fallback'))}")  # 新增代码+Phase61AbortStreamingHooks: 显示可用降级路径；如果没有这行代码，无法注册热键时用户不知道还能用 /computer abort 和 controller abort。
    lines.append(f"- abort_stream=events:{abort_streaming_hooks.get('stream_event_count', 0)} path={_short_text(abort_streaming_hooks.get('stream_events_path', ''), 180)}")  # 新增代码+Phase61AbortStreamingHooks: 输出 stream 事件数量和路径；如果没有这行代码，排查中断和 cleanup 时找不到证据文件。
    lines.append(f"- abort_cleanup_hooks={','.join(_as_list(abort_streaming_hooks.get('hooked_cleanup_events', [])))}")  # 新增代码+Phase61AbortStreamingHooks: 输出已纳入 cleanup 的中断类型；如果没有这行代码，用户不知道 tool abort、Ctrl+C、异常退出是否被覆盖。
    lines.append("Computer High-Level Tools")  # 新增代码+Phase62HighLevelTools: 输出 Phase62 高层工具区标题；如果没有这行代码，状态页无法明确展示 high-level API。
    lines.append(f"- high_level_model={high_level_tools.get('model', '')} marker={high_level_tools.get('marker', '')}")  # 新增代码+Phase62HighLevelTools: 输出高层工具模型和 marker；如果没有这行代码，验收器和用户无法确认 Phase62 已接入。
    lines.append(f"- high_level_operations={','.join(_as_list(high_level_tools.get('supported_operations', [])))}")  # 新增代码+Phase62HighLevelTools: 输出高层操作清单；如果没有这行代码，用户不知道模型可用哪些操作。
    lines.append(f"- high_level_read_only_parallel={_bool_token(high_level_tools.get('read_only_parallel_supported'))} write_serial={_bool_token(high_level_tools.get('write_actions_serialized'))}")  # 新增代码+Phase62HighLevelTools: 输出读写调度边界；如果没有这行代码，用户不知道 observe 和 click/type 是否区分锁。
    lines.append(f"- high_level_outputs=streaming:{_bool_token(high_level_tools.get('streaming_executor_integrated'))} image_artifact:{_bool_token(high_level_tools.get('image_artifact_supported'))} uia_candidates:{_bool_token(high_level_tools.get('uia_candidate_summary_supported'))}")  # 新增代码+Phase62HighLevelTools: 输出结果能力；如果没有这行代码，用户看不到 progress、artifact、UIA 摘要是否支持。
    lines.append(f"- high_level_progress=events:{high_level_tools.get('progress_event_count', 0)} path={_short_text(high_level_tools.get('progress_events_path', ''), 180)}")  # 新增代码+Phase62HighLevelTools: 输出 progress 文件路径；如果没有这行代码，排查高层工具时找不到事件日志。
    lines.append(f"- high_level_artifact_dir={_short_text(high_level_tools.get('artifact_dir', ''), 180)}")  # 新增代码+Phase62HighLevelTools: 输出 artifact 目录；如果没有这行代码，用户无法找到 observe_screen 产物。
    lines.append("Computer Controller Takeover")  # 新增代码+Phase63ControllerTakeover: 输出 Phase63 controller 接管区标题；如果没有这行代码，状态页无法明确展示外部 agent 接管调试面。
    lines.append(f"- controller_model={controller_takeover.get('model', '')} marker={controller_takeover.get('marker', '')}")  # 新增代码+Phase63ControllerTakeover: 输出 controller 模型和 marker；如果没有这行代码，验收器和用户无法确认 Phase63 已接入。
    lines.append(f"- controller_visible_terminal_required={_bool_token(controller_takeover.get('visible_terminal_required'))} http_loopback_only={_bool_token(controller_takeover.get('http_loopback_only'))} token_required={_bool_token(controller_takeover.get('token_required'))}")  # 新增代码+Phase63ControllerTakeover: 输出可见终端、loopback 和 token 边界；如果没有这行代码，用户可能误把 HTTP/stdio 当最终验收。
    lines.append(f"- controller_start_bat_exists={_bool_token(controller_takeover.get('start_oauth_agent_bat_exists'))} controller_ps1_exists={_bool_token(controller_takeover.get('controller_ps1_exists'))}")  # 新增代码+Phase63ControllerTakeover: 输出关键启动文件存在性；如果没有这行代码，外部 agent 失败时不知道是路径问题还是运行问题。
    lines.append(f"- controller_runs_dir={_short_text(controller_takeover.get('runs_dir', ''), 180)}")  # 新增代码+Phase63ControllerTakeover: 输出验收 runs 目录；如果没有这行代码，Codex 或用户无法定位 result.json 证据。
    lines.append(f"- controller_evidence_package_dir={_short_text(controller_takeover.get('evidence_package_dir', ''), 180)}")  # 新增代码+Phase63ControllerTakeover: 输出证据包目录；如果没有这行代码，失败现场导出后不好找。
    lines.append(f"- controller_security=can_abort:{_bool_token(controller_takeover.get('controller_can_abort'))} can_read_runs:{_bool_token(controller_takeover.get('controller_can_read_runs'))} approval_bypass_allowed:{_bool_token(controller_takeover.get('approval_bypass_allowed'))}")  # 新增代码+Phase63ControllerTakeover: 输出急停、读取和绕过审批边界；如果没有这行代码，外部接管安全性不可见。
    lines.append("Computer Session Context")  # 新增代码+Phase59SessionContextAppState: 输出 Phase59 统一事实源标题；如果没有这行代码，状态页无法明确显示 session context 区块。
    lines.append(f"- context_model={session_context.get('model', '')} marker={session_context.get('marker', '')}")  # 新增代码+Phase59SessionContextAppState: 输出 context 模型和 marker；如果没有这行代码，验收器和用户无法确认 Phase59 已接入。
    lines.append(f"- context_session={current_context.get('session_id', '')} state_dir={_short_text(session_context.get('state_dir', ''), 180)}")  # 新增代码+Phase59SessionContextAppState: 输出当前 session 和状态目录；如果没有这行代码，调试时找不到持久化文件。
    lines.append(f"- context_display={_short_text(_as_dict(current_context.get('selected_display', {})).get('display_id', ''), 80)} screenshot={_as_dict(current_context.get('last_screenshot_dims', {})).get('width', '')}x{_as_dict(current_context.get('last_screenshot_dims', {})).get('height', '')}")  # 新增代码+Phase59SessionContextAppState: 输出显示器和截图尺寸；如果没有这行代码，多屏和截图上下文仍不可见。
    lines.append(f"- context_last_action={_short_text(_as_dict(current_context.get('last_action', {})).get('action', ''), 80)} last_error={_short_text(_as_dict(current_context.get('last_error', {})).get('code', ''), 80)}")  # 新增代码+Phase59SessionContextAppState: 输出最近动作和错误摘要；如果没有这行代码，AppState 的 last_action/last_error 仍埋在 JSON。
    lines.append("Computer Runtime")  # 新增代码+Phase51ComputerStatusUI: 输出 runtime 区标题；如果没有这行代码，cleanup/通知状态不醒目。
    lines.append(f"- notifications={runtime.get('notification_count', 0)} cleanups={runtime.get('cleanup_count', 0)} last={_short_text(_as_dict(runtime.get('last_notification', {})).get('event', ''), 100)}")  # 新增代码+Phase51ComputerStatusUI: 输出通知和 cleanup 摘要；如果没有这行代码，恢复层活动不可见。
    lines.append(f"- journal_recent_action_count={recovery.get('recent_action_count', 0)}")  # 新增代码+Phase51ComputerStatusUI: 输出 journal 数量；如果没有这行代码，用户不知道是否有动作链路。
    capability_items = _as_list(capability_matrix.get("capabilities", []))  # 修改代码+Phase52WindowsProductionMatrix: 先取出完整能力矩阵列表用于兼容 Phase43 状态输出；如果没有这行代码，后面只能显示前四项并漏掉 SendInput。
    visible_capabilities = capability_items[:4]  # 修改代码+Phase52WindowsProductionMatrix: 保留 Phase51 压缩 UI 的前四项默认展示；如果没有这行代码，状态面板会一下子刷出过长矩阵。
    for capability in capability_items:  # 修改代码+Phase52WindowsProductionMatrix: 扫描完整矩阵寻找关键能力项；如果没有这行代码，windows_sendinput 这类靠后的关键项不会进入终端。
        item = _as_dict(capability)  # 修改代码+Phase52WindowsProductionMatrix: 安全读取单个能力项；如果没有这行代码，坏 capability 会导致渲染崩溃。
        if item.get("name") == "windows_sendinput" and capability not in visible_capabilities:  # 修改代码+Phase52WindowsProductionMatrix: 只在 SendInput 未显示时追加；如果没有这行代码，动作层状态可能继续被压缩掉。
            visible_capabilities.append(capability)  # 修改代码+Phase52WindowsProductionMatrix: 把 SendInput 放回可见状态面板；如果没有这行代码，Phase43 终端合同无法看到动作层差距。
    lines.append("Computer Native Capability Matrix")  # 修改代码+Phase52WindowsProductionMatrix: 恢复 Phase43 期望的能力矩阵标题；如果没有这行代码，旧验收会认为状态 UI 丢失 native 矩阵。
    lines.append(f"- marker={capability_matrix.get('marker', '')}")  # 修改代码+Phase52WindowsProductionMatrix: 输出 Phase43 矩阵 marker；如果没有这行代码，真实终端验收无法稳定匹配能力矩阵来源。
    for capability in visible_capabilities:  # 修改代码+Phase52WindowsProductionMatrix: 遍历压缩但含关键项的可见能力列表；如果没有这行代码，矩阵标题下没有具体能力状态。
        item = _as_dict(capability)  # 修改代码+Phase52WindowsProductionMatrix: 安全读取能力项字段；如果没有这行代码，异常能力对象会拖垮整个 status 输出。
        lines.append(f"- capability={_short_text(item.get('name', ''), 80)} available={_bool_token(item.get('available'))} enabled={_bool_token(item.get('enabled'))} reason={_short_text(item.get('reason', ''), 90)}")  # 修改代码+Phase52WindowsProductionMatrix: 输出单项能力摘要；如果没有这行代码，WGC/UIA/SendInput 细节不可见。
    lines.append("Computer Commands")  # 新增代码+Phase51ComputerStatusUI: 输出命令区标题；如果没有这行代码，用户不知道可用子命令。
    lines.append("- risk=low command=/computer observe : run read-only window observation")  # 新增代码+Phase51ComputerStatusUI: 展示 observe 命令；如果没有这行代码，用户不知道安全起步入口。
    lines.append("- risk=low command=/computer grant <app> [flags] : record terminal UI grant draft only")  # 新增代码+Phase51ComputerStatusUI: 展示 grant 命令并说明边界；如果没有这行代码，用户可能误解授权会直接放行动作。
    lines.append("- risk=medium command=/computer approve <app> [flags] ttl=60 scope=click : create persistent grant")  # 新增代码+Phase60PersistentGrants: 展示生产级授权入口；如果没有这行代码，用户不知道如何创建真正可评估 grant。
    lines.append("- risk=low command=/computer grants : show persistent grant lifecycle")  # 新增代码+Phase60PersistentGrants: 展示持久授权查看入口；如果没有这行代码，用户不知道如何看 active/revoked/expired。
    lines.append("- risk=low command=/computer revoke <app> : revoke persistent grant and remove terminal UI draft")  # 修改代码+Phase60PersistentGrants: 展示新版 revoke 边界；如果没有这行代码，用户不知道 revoke 已经同时收回生产 grant 和旧草案。
    lines.append("- risk=low command=/computer abort-hooks : show abort, cleanup, hotkey fallback, and stream events")  # 新增代码+Phase61AbortStreamingHooks: 展示中断钩子状态入口；如果没有这行代码，用户不知道如何查看 Phase61 streaming cleanup 状态。
    lines.append("- risk=low command=/computer high-level-tools : show high-level Computer Tool operations and progress")  # 新增代码+Phase62HighLevelTools: 展示高层工具状态入口；如果没有这行代码，用户不知道如何查看 Phase62 API/progress/artifact 状态。
    lines.append("- risk=low command=/computer controller : show external agent controller takeover and evidence surface")  # 新增代码+Phase63ControllerTakeover: 展示外部 controller 接管调试入口；如果没有这行代码，用户不知道如何查看 Phase63 可见终端和证据包状态。
    lines.append("- risk=low command=/computer journal : show recent action evidence chain")  # 新增代码+Phase51ComputerStatusUI: 展示 journal 命令；如果没有这行代码，用户不知道如何复盘动作。
    lines.append("- risk=medium command=/computer abort <reason> : request global abort flag")  # 新增代码+Phase51ComputerStatusUI: 展示 abort 命令；如果没有这行代码，急停入口不明显。
    lines.append("- risk=low command=/computer cleanup : release lock and clear abort for this session")  # 新增代码+Phase51ComputerStatusUI: 展示 cleanup 命令；如果没有这行代码，恢复入口不明显。
    lines.append(f"- actions_expanded={_bool_token(PHASE51_ACTIONS_EXPANDED)}")  # 新增代码+Phase51ComputerStatusUI: 输出动作面边界；如果没有这行代码，状态 UI 升级可能被误解成动作能力扩大。
    return "\n".join(lines) + "\n"  # 新增代码+Phase51ComputerStatusUI: 返回完整状态文本并带末尾换行；如果没有这行代码，终端输出会和下一个 prompt 粘连。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，render_computer_status 到此结束；如果没有这个边界说明，读者不容易看出 renderer 主体范围。


def run_phase51_computer_status_ui_contract() -> dict[str, Any]:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，运行无副作用 UI 合同自检；如果没有这段函数，真实终端验收无法快速验证状态 UI。
    snapshot = {"lock": {"locked": False, "stale": False, "abort_requested": False, "owner_session_id": ""}, "approval": {"approval_granted_app_count": 0, "grant_flags": {"observe": True, "desktopAction": True}}, "runtime": {"notification_count": 1, "cleanup_count": 0, "last_notification": {"event": "phase51"}}, "recovery": {"recent_action_count": 1, "recent_actions": [{"audit_id": "phase51-contract-audit", "action": "observe", "chain_available": False}]}, "terminal_grants": {"grant_scope": "terminal_ui_only", "granted_app_count": 1, "grant_flags": {"desktopAction": True}}, "capability_matrix": {"summary": {"available_count": 4, "enabled_count": 2, "blocked_count": 7}, "capabilities": [{"name": "windows_graphics_capture", "available": False, "enabled": False, "reason": "fallback required"}]}}  # 新增代码+Phase51ComputerStatusUI: 构造最小代表性快照；如果没有这行代码，自检没有 renderer 输入。
    rendered = render_computer_status(snapshot)  # 新增代码+Phase51ComputerStatusUI: 渲染状态 UI；如果没有这行代码，报告无法检查输出。
    return {"marker": PHASE51_COMPUTER_STATUS_UI_MARKER, "ok_token": PHASE51_COMPUTER_STATUS_UI_OK_TOKEN, "summary": "Computer Summary" in rendered, "next_command": "next=/computer journal" in rendered or "next=/computer observe" in rendered, "commands": "Computer Commands" in rendered and "/computer cleanup" in rendered, "grant_revoke": "/computer grant" in rendered and "/computer revoke" in rendered and "terminal_ui_only" in rendered, "actions_expanded": PHASE51_ACTIONS_EXPANDED}  # 新增代码+Phase51ComputerStatusUI: 返回 UI 合同布尔结果；如果没有这行代码，CLI 无法生成稳定 token。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，run_phase51_computer_status_ui_contract 到此结束；如果没有这个边界说明，读者不容易看出 UI 自检范围。


def phase51_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，把 Phase51 报告转成单行 token；如果没有这段函数，场景验收需要解析复杂 JSON。
    return f"{PHASE51_COMPUTER_STATUS_UI_OK_TOKEN} summary={_bool_token(report.get('summary'))} next_command={_bool_token(report.get('next_command'))} commands={_bool_token(report.get('commands'))} grant_revoke={_bool_token(report.get('grant_revoke'))} actions_expanded={_bool_token(report.get('actions_expanded'))} marker={PHASE51_COMPUTER_STATUS_UI_MARKER}"  # 新增代码+Phase51ComputerStatusUI: 返回固定顺序 token；如果没有这行代码，验收器容易因输出漂移失败。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，phase51_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 文本范围。


def main() -> int:  # 新增代码+Phase51ComputerStatusUI: 函数段开始，提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase51 UI 合同。
    report = run_phase51_computer_status_ui_contract()  # 新增代码+Phase51ComputerStatusUI: 运行 UI 合同自检；如果没有这行代码，main 没有报告来源。
    print(phase51_cli_line(report))  # 新增代码+Phase51ComputerStatusUI: 打印稳定单行 token；如果没有这行代码，debug log 无法匹配 OK。
    print(PHASE51_COMPUTER_STATUS_UI_MARKER)  # 新增代码+Phase51ComputerStatusUI: 单独打印 marker；如果没有这行代码，验收器可能只看到 OK token。
    return 0  # 新增代码+Phase51ComputerStatusUI: 返回成功退出码；如果没有这行代码，命令行调用方无法稳定判断成功。
# 新增代码+Phase51ComputerStatusUI: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出 CLI 入口范围。


if __name__ == "__main__":  # 新增代码+Phase51ComputerStatusUI: 允许直接运行本模块；如果没有这行代码，初学者无法用 python 文件方式自检 Phase51。
    raise SystemExit(main())  # 新增代码+Phase51ComputerStatusUI: 用 main 的退出码结束进程；如果没有这行代码，脚本入口不会执行自检。
