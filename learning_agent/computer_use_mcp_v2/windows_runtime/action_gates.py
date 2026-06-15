"""Computer Use 动作门禁和完成门工具。"""  # 新增代码+AgentPySplitPhase4: 说明本文件只负责 Computer Use 动作前拦截和完成收束；如果没有这行代码，代码小白打开文件时不知道本模块学习入口。

from __future__ import annotations  # 新增代码+AgentPySplitPhase4: 允许类型注解延迟解析；如果没有这行代码，复杂类型在旧运行方式下更容易受定义顺序影响。

import json  # 新增代码+AgentPySplitPhase4: 用来把门禁报告转成模型可读 JSON 文本；如果没有这行代码，拒绝原因无法稳定返回给模型。
from typing import Any, Callable  # 新增代码+AgentPySplitPhase4: 导入通用数据类型和回调类型；如果没有这行代码，模块接口不容易看出依赖边界。


RecordObservation = Callable[[str, dict[str, Any]], None]  # 新增代码+AgentPySplitPhase4: 定义观察记录回调类型；如果没有这行代码，新模块会被迫直接依赖 LearningAgent 类。

COMPUTER_USE_MOUSE_KEYBOARD_ACTIONS = {"move_mouse", "click", "double_click", "triple_click", "mouse_down", "mouse_up", "drag_path", "type_text", "press_key", "hold_key", "scroll"}  # 修改代码+ClaudeCodeParity: 集中保存会真实改变桌面的鼠标键盘动作并包含新增 parity 动作；如果没有这行代码，三击、按下、释放、按住键可能绕过 full 模式安全门禁。
COMPUTER_USE_COMPLETION_CHANGE_ACTIONS = {"drag_path", "click", "double_click", "triple_click", "mouse_down", "mouse_up", "type_text", "press_key", "hold_key", "scroll"}  # 修改代码+ClaudeCodeParity: 集中保存完成门需要拦截的继续改变桌面动作并包含新增 parity 动作；如果没有这行代码，任务该收束时仍可能继续三击、按下、释放或按住键。


# 新增代码+AgentPySplitPhase4: 函数段开始，computer_use_full_mode_requires_model_visible_observation 判断 full GUI 动作是否必须先看截图；如果没有这段函数，提示词里的“先观察”无法变成硬门禁。
def computer_use_full_mode_requires_model_visible_observation(action_name: str, desktop_task_context: Any) -> bool:  # 新增代码+AgentPySplitPhase4: 定义观察门禁适用性入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    if not isinstance(desktop_task_context, dict):  # 新增代码+AgentPySplitPhase4: 防御异常上下文形状；如果没有这行代码，外部状态污染可能导致门禁崩溃。
        return False  # 新增代码+AgentPySplitPhase4: 上下文异常时不启用本门禁；如果没有这行代码，普通任务可能被错误拦截。
    if not bool(desktop_task_context.get("active", False)):  # 新增代码+AgentPySplitPhase4: 只在 /computer use --full 激活的桌面任务中启用；如果没有这行代码，兼容工具测试和普通调用会被过度限制。
        return False  # 新增代码+AgentPySplitPhase4: 非 full 桌面任务不强制截图观察；如果没有这行代码，旧接口兼容性会被破坏。
    if not bool(desktop_task_context.get("requires_gui_actions", False)):  # 新增代码+AgentPySplitPhase4: 只对确实需要 GUI 动作的任务启用；如果没有这行代码，状态查询类任务也可能被误拦。
        return False  # 新增代码+AgentPySplitPhase4: 非 GUI 动作任务不拦截；如果没有这行代码，解释类任务可能无法继续。
    return action_name in COMPUTER_USE_MOUSE_KEYBOARD_ACTIONS  # 新增代码+AgentPySplitPhase4: 鼠标键盘类动作必须先看屏幕，截图类动作不拦；如果没有这行代码，盲点、盲打和盲拖仍可能发生。
# 新增代码+AgentPySplitPhase4: 函数段结束，computer_use_full_mode_requires_model_visible_observation 到此结束；如果没有这个边界说明，用户不容易看出观察门禁适用范围。


# 新增代码+AgentPySplitPhase4: 函数段开始，computer_use_data_has_model_visible_image 统一判断工具 data 是否有模型可见截图；如果没有这段函数，observe 和 action 的截图证据会继续用两套标准。
def computer_use_data_has_model_visible_image(data: Any) -> bool:  # 新增代码+AgentPySplitPhase4: 定义模型可见截图判断入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    if not isinstance(data, dict):  # 新增代码+AgentPySplitPhase4: 先确认 data 是字典；如果没有这行代码，字符串或 None 会触发属性错误。
        return False  # 新增代码+AgentPySplitPhase4: 异常 data 不能当作视觉证据；如果没有这行代码，坏工具结果可能误放行真实动作。
    state = data.get("state", {}) if isinstance(data.get("state", {}), dict) else {}  # 新增代码+AgentPySplitPhase4: 读取顶层窗口状态；如果没有这行代码，只在 state 内暴露截图字段的观察会被误判无图。
    image_result_count = int(data.get("image_result_count", 0) or state.get("image_result_count", 0) or 0)  # 新增代码+AgentPySplitPhase4: 统计顶层模型可见图片块数量；如果没有这行代码，只有截图路径没有图片块的结果会被误当成模型已看见。
    screenshot_captured = bool(data.get("screenshot_captured", False) or state.get("screenshot_captured", False))  # 新增代码+AgentPySplitPhase4: 检查顶层真实截图是否捕获；如果没有这行代码，空图片计数异常可能误放行。
    if image_result_count > 0 and screenshot_captured:  # 新增代码+AgentPySplitPhase4: 顶层同时有截图和图片块时算模型可见；如果没有这行代码，普通 mcp__computer-use__observe 成功结果会失效。
        return True  # 新增代码+AgentPySplitPhase4: 找到顶层有效视觉证据后返回成功；如果没有这行代码，已经看过屏幕的动作会被一直拦住。
    for evidence_key in ("before_evidence", "after_evidence"):  # 新增代码+AgentPySplitPhase4: 继续检查真实动作自带的前后截图证据；如果没有这行代码，真实 SendInput 动作回灌的截图会被完成门忽略。
        evidence = data.get(evidence_key, {})  # 新增代码+AgentPySplitPhase4: 读取某个动作证据块；如果没有这行代码，无法检查 before_evidence 或 after_evidence。
        if not isinstance(evidence, dict):  # 新增代码+AgentPySplitPhase4: 防御异常证据形状；如果没有这行代码，字符串证据会导致属性错误。
            continue  # 新增代码+AgentPySplitPhase4: 跳过异常证据块；如果没有这行代码，坏证据会中断整个主循环。
        evidence_state = evidence.get("state", {}) if isinstance(evidence.get("state", {}), dict) else {}  # 新增代码+AgentPySplitPhase4: 读取证据内嵌窗口状态；如果没有这行代码，真实截图字段藏在 state 内时会被漏掉。
        evidence_image_count = int(evidence.get("image_result_count", 0) or evidence_state.get("image_result_count", 0) or 0)  # 新增代码+AgentPySplitPhase4: 统计证据块里可回灌模型的图片数量；如果没有这行代码，动作截图只会成为文件路径而不是可见证据。
        evidence_captured = bool(evidence.get("captured", False) or evidence.get("screenshot_captured", False) or evidence_state.get("screenshot_captured", False))  # 新增代码+AgentPySplitPhase4: 确认证据确实捕获截图；如果没有这行代码，只有结构壳子的证据会误放行。
        if evidence_image_count > 0 and evidence_captured:  # 新增代码+AgentPySplitPhase4: 证据块同时有截图和图片块才算模型可见；如果没有这行代码，真实终端 action.before_evidence 不能推进 observe-plan-act loop。
            return True  # 新增代码+AgentPySplitPhase4: 找到动作内嵌视觉证据后返回成功；如果没有这行代码，完成门会继续等一个已经不必要的 observe。
    return False  # 新增代码+AgentPySplitPhase4: 没有任何有效截图证据时返回失败；如果没有这行代码，函数缺少明确否定结果。
# 新增代码+AgentPySplitPhase4: 函数段结束，computer_use_data_has_model_visible_image 到此结束；如果没有这个边界说明，用户不容易看出截图证据统一判断范围。


# 新增代码+AgentPySplitPhase4: 函数段开始，computer_use_has_recent_model_visible_observation 检查最近是否有模型可见截图；如果没有这段函数，动作层无法知道模型是否真正看过屏幕。
def computer_use_has_recent_model_visible_observation(observation_events: Any) -> bool:  # 新增代码+AgentPySplitPhase4: 定义最近视觉观察判断入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    event_snapshot = list(observation_events or [])  # 新增代码+AgentPySplitPhase4: 复制事件列表避免遍历时被外层追加影响；如果没有这行代码，长任务事件写入可能让判断不稳定。
    for event in reversed(event_snapshot[-80:]):  # 新增代码+AgentPySplitPhase4: 从最近事件倒序查找并限制 80 条；如果没有这行代码，多轮真实绘图会拖慢门禁判断。
        if not isinstance(event, dict):  # 新增代码+AgentPySplitPhase4: 防御异常事件形状；如果没有这行代码，坏事件会触发属性错误。
            continue  # 新增代码+AgentPySplitPhase4: 跳过异常事件；如果没有这行代码，单个坏事件会中断门禁。
        if event.get("kind") not in {"computer_use_observe", "computer_use_action"}:  # 新增代码+AgentPySplitPhase4: 同时接受观察事件和带截图的动作事件；如果没有这行代码，动作自带截图不会被主循环承认。
            continue  # 新增代码+AgentPySplitPhase4: 跳过非桌面视觉相关事件；如果没有这行代码，后续字段读取会混入无关结构。
        payload = event.get("payload", {})  # 新增代码+AgentPySplitPhase4: 读取事件载荷；如果没有这行代码，无法判断工具是否成功和是否有图。
        if not isinstance(payload, dict) or not bool(payload.get("ok", False)):  # 新增代码+AgentPySplitPhase4: 只接受成功工具结果；如果没有这行代码，失败 observe/action 也可能放行动作。
            continue  # 新增代码+AgentPySplitPhase4: 跳过失败或异常载荷；如果没有这行代码，坏事件会污染门禁判断。
        if computer_use_data_has_model_visible_image(payload.get("data", {})):  # 新增代码+AgentPySplitPhase4: 用统一 helper 判断 data 或动作证据是否有模型可见截图；如果没有这行代码，真实 before_evidence 无法解锁完成门。
            return True  # 新增代码+AgentPySplitPhase4: 找到有效视觉证据后放行动作或完成门；如果没有这行代码，已经看过屏幕的正常动作会被一直拦住。
    return False  # 新增代码+AgentPySplitPhase4: 最近没有有效截图证据时拒绝动作；如果没有这行代码，函数缺少明确失败结果。
# 新增代码+AgentPySplitPhase4: 函数段结束，computer_use_has_recent_model_visible_observation 到此结束；如果没有这个边界说明，用户不容易看出“看过屏幕”的判定标准。


# 新增代码+AgentPySplitPhase4: 函数段开始，computer_use_observe_before_action_rejection 生成先观察拒绝结果；如果没有这段函数，盲动拦截会散落在 agent.py 主流程里。
def computer_use_observe_before_action_rejection(action_name: str, arguments: dict[str, Any], desktop_task_context: Any, observation_events: Any, record_observation: RecordObservation) -> str | None:  # 新增代码+AgentPySplitPhase4: 定义观察门禁拒绝入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    if not computer_use_full_mode_requires_model_visible_observation(action_name, desktop_task_context):  # 新增代码+AgentPySplitPhase4: 先判断当前动作是否需要观察门禁；如果没有这行代码，所有动作都会被不必要检查。
        return None  # 新增代码+AgentPySplitPhase4: 不需要门禁时返回 None；如果没有这行代码，调用方无法区分放行和拒绝。
    if computer_use_has_recent_model_visible_observation(observation_events):  # 新增代码+AgentPySplitPhase4: 已经有模型可见截图观察时放行；如果没有这行代码，正常 observe-plan-act 会被卡死。
        return None  # 新增代码+AgentPySplitPhase4: 返回 None 表示不拦截；如果没有这行代码，调用方无法继续权限和 controller 路径。
    report = {"ok": False, "decision": "observe_before_action_required", "action": action_name, "reason": "full 模式下鼠标键盘动作前必须先让模型看到真实截图观察。", "next_tools": ["mcp__computer-use__observe"], "required_observe_action": "get_window_state", "argument_preview": {"has_window": isinstance(arguments.get("window"), dict), "has_coordinates": "x" in arguments or "y" in arguments, "has_points": bool(arguments.get("points"))}}  # 新增代码+AgentPySplitPhase4: 构造模型可读纠偏报告；如果没有这行代码，模型不知道该先调用哪个观察工具。
    record_observation("computer_use_observe_before_action_required", report)  # 新增代码+AgentPySplitPhase4: 把盲动拦截写入观察日志；如果没有这行代码，真实终端排查不知道为何没有执行鼠标键盘。
    return "Computer Use full 模式已拒绝盲目桌面动作：请先观察屏幕和目标窗口，再执行鼠标键盘动作。\n请先调用 mcp__computer-use__observe，action=get_window_state，并使用返回的截图继续规划。\n" + json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+AgentPySplitPhase4: 返回中文说明和结构化 JSON 给模型自我纠正；如果没有这行代码，模型可能继续重复盲动。
# 新增代码+AgentPySplitPhase4: 函数段结束，computer_use_observe_before_action_rejection 到此结束；如果没有这个边界说明，用户不容易看出拒绝结果的范围。


# 新增代码+AgentPySplitPhase4: 函数段开始，computer_use_full_mode_requires_agent_owned_launch 判断动作是否必须先 launch_app；如果没有这段函数，模型可能操作用户旧窗口。
def computer_use_full_mode_requires_agent_owned_launch(action_name: str, desktop_task_context: Any) -> bool:  # 新增代码+AgentPySplitPhase4: 定义 agent-owned 启动门禁适用性入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    if not isinstance(desktop_task_context, dict):  # 新增代码+AgentPySplitPhase4: 防御异常上下文类型；如果没有这行代码，外部状态污染可能让门禁抛异常。
        return False  # 新增代码+AgentPySplitPhase4: 上下文异常时不启用本门禁；如果没有这行代码，普通工具调用可能被误拦。
    if not bool(desktop_task_context.get("active", False)):  # 新增代码+AgentPySplitPhase4: 只在 full 桌面任务激活时启用；如果没有这行代码，普通 mcp__computer-use__open_application 单测和兼容旧调用会被过度限制。
        return False  # 新增代码+AgentPySplitPhase4: 非 full 桌面任务不要求先 launch_app；如果没有这行代码，旧协议无法继续兼容。
    if not bool(desktop_task_context.get("requires_gui_actions", False)):  # 新增代码+AgentPySplitPhase4: 只对需要真实 GUI 动作的任务启用；如果没有这行代码，状态查询类桌面任务也可能被误拦。
        return False  # 新增代码+AgentPySplitPhase4: 非 GUI 动作任务不要求启动软件；如果没有这行代码，解释类任务会被卡住。
    target_app_hint = str(desktop_task_context.get("target_app_hint", "") or "").strip()  # 修改代码+GenericLocalAppLaunchGate: 先提取目标应用提示再判断是否具体；如果没有这一行，local_app 这类占位词会被误当作真实应用。
    if not target_app_hint:  # 修改代码+GenericLocalAppLaunchGate: 只在自然语言识别到具体目标本机应用时启用；如果没有这行代码，纯鼠标坐标实验可能被错误要求启动应用。
        return False  # 新增代码+AgentPySplitPhase4: 没有目标应用线索时保持旧路径兼容；如果没有这行代码，开放式桌面任务会被过早收窄。
    if target_app_hint.lower() in {"local_app", "unknown_app", "unknown", "unknown_app_id"}:  # 新增代码+GenericLocalAppLaunchGate: 泛化占位词不代表可启动应用；如果没有这一行，overlay/坐标类任务会被错误要求 launch_app。
        return False  # 新增代码+GenericLocalAppLaunchGate: 对泛化本地应用占位保持观察后可动作路径；如果没有这一行，安全鼠标移动验证无法触发真实低层 sender。
    return action_name in COMPUTER_USE_MOUSE_KEYBOARD_ACTIONS  # 新增代码+AgentPySplitPhase4: 鼠标键盘动作必须等 launch_app 成功，截图和 launch_app 本身不拦；如果没有这行代码，未启动软件前仍可能真实点击旧窗口。
# 新增代码+AgentPySplitPhase4: 函数段结束，computer_use_full_mode_requires_agent_owned_launch 到此结束；如果没有这个边界说明，用户不容易看出先启动门禁适用范围。


# 新增代码+AgentPySplitPhase4: 函数段开始，computer_use_has_agent_owned_launch_target 检查 controller 是否已有自有窗口；如果没有这段函数，动作层不知道是否真正绑定了软件。
def computer_use_has_agent_owned_launch_target(controller: Any) -> bool:  # 新增代码+AgentPySplitPhase4: 定义 agent-owned 目标窗口判断入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    active_window = getattr(controller, "active_agent_owned_target_window", {}) if controller is not None else {}  # 新增代码+AgentPySplitPhase4: 读取 controller 中 launch_app 成功后保存的窗口；如果没有这行代码，无法区分用户旧窗口和 agent 自己打开的窗口。
    return isinstance(active_window, dict) and bool(active_window.get("app_id")) and bool(active_window.get("window_id"))  # 新增代码+AgentPySplitPhase4: 只有同时有 app_id 和 window_id 才算可操作目标；如果没有这行代码，空字典或半截窗口可能误放行。
# 新增代码+AgentPySplitPhase4: 函数段结束，computer_use_has_agent_owned_launch_target 到此结束；如果没有这个边界说明，用户不容易看出 agent-owned 判断标准。


# 新增代码+AgentPySplitPhase4: 函数段开始，computer_use_agent_owned_launch_rejection 生成先 launch_app 拒绝结果；如果没有这段函数，模型可能未打开软件就操作旧窗口。
def computer_use_agent_owned_launch_rejection(action_name: str, arguments: dict[str, Any], desktop_task_context: Any, controller: Any, record_observation: RecordObservation) -> str | None:  # 新增代码+AgentPySplitPhase4: 定义先启动门禁拒绝入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    if not computer_use_full_mode_requires_agent_owned_launch(action_name, desktop_task_context):  # 新增代码+AgentPySplitPhase4: 先判断本动作是否需要 agent-owned 启动门禁；如果没有这行代码，所有 Computer Use 动作都会被不必要检查。
        return None  # 新增代码+AgentPySplitPhase4: 不需要门禁时返回 None；如果没有这行代码，调用方无法继续正常路径。
    if computer_use_has_agent_owned_launch_target(controller):  # 新增代码+AgentPySplitPhase4: 已经有 launch_app 绑定窗口时放行；如果没有这行代码，成功打开软件后仍无法操作。
        return None  # 新增代码+AgentPySplitPhase4: 返回 None 表示继续权限和 controller 路径；如果没有这行代码，正常动作会被误拒绝。
    safe_context = desktop_task_context if isinstance(desktop_task_context, dict) else {}  # 新增代码+AgentPySplitPhase4: 读取脱敏任务上下文用于提示目标应用；如果没有这行代码，拒绝信息缺少该启动哪个软件。
    target_app_hint = str(safe_context.get("target_app_hint", "") or "").strip()  # 新增代码+AgentPySplitPhase4: 提取目标应用提示；如果没有这行代码，模型不知道 launch_app 应传什么 app_name。
    report = {"ok": False, "decision": "agent_owned_launch_required", "action": action_name, "reason": "full 本机应用任务必须先用 launch_app 打开并绑定 agent-owned 目标窗口，不能直接操作旧窗口。", "next_tools": ["mcp__computer-use__open_application"], "required_action": "launch_app", "target_app_hint": target_app_hint, "argument_preview": {"has_window": isinstance(arguments.get("window"), dict), "has_coordinates": "x" in arguments or "y" in arguments, "has_points": bool(arguments.get("points"))}}  # 新增代码+AgentPySplitPhase4: 构造模型可读纠偏报告；如果没有这行代码，模型不知道应先打开软件而不是继续点击。
    record_observation("computer_use_agent_owned_launch_required", report)  # 新增代码+AgentPySplitPhase4: 把先启动门禁写入观察日志；如果没有这行代码，真实终端排查不知道为什么没有执行鼠标键盘。
    return "Computer Use full 模式已拒绝操作非 agent-owned 目标窗口：请先调用 mcp__computer-use__open_application，action=launch_app，传入 app_name/target_app 打开并绑定目标软件。\n" + json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+AgentPySplitPhase4: 返回中文说明和 JSON 给模型纠偏；如果没有这行代码，模型可能继续对旧窗口做动作。
# 新增代码+AgentPySplitPhase4: 函数段结束，computer_use_agent_owned_launch_rejection 到此结束；如果没有这个边界说明，用户不容易看出启动门禁拒绝范围。


# 新增代码+AgentPySplitPhase4: 函数段开始，computer_use_full_recent_events_after_mode_open 取最近一次 full mode 后事件；如果没有这段函数，完成门可能把旧任务动作算进本轮。
def computer_use_full_recent_events_after_mode_open(observation_events: Any) -> list[dict[str, Any]]:  # 新增代码+AgentPySplitPhase4: 定义当前 full 会话事件窗口入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    event_snapshot = list(observation_events or [])  # 新增代码+AgentPySplitPhase4: 复制观察事件列表；如果没有这行代码，调用方遍历时可能被外层追加影响。
    start_index = 0  # 新增代码+AgentPySplitPhase4: 默认从全部观察事件开始统计；如果没有这行代码，没有 mode 事件的单元测试会拿不到数据。
    for index, event in enumerate(event_snapshot):  # 新增代码+AgentPySplitPhase4: 遍历观察事件寻找最近的 mode 事件；如果没有这行代码，无法切分当前 full 会话。
        event_dict = event if isinstance(event, dict) else {}  # 新增代码+AgentPySplitPhase4: 防御异常事件形状；如果没有这行代码，坏事件会让窗口切分崩溃。
        if event_dict.get("kind") == "computer_use_mode":  # 新增代码+AgentPySplitPhase4: 只把 full mode 状态事件当作会话边界；如果没有这行代码，普通工具事件会误重置统计窗口。
            start_index = index + 1  # 新增代码+AgentPySplitPhase4: 从 mode 事件之后开始统计动作；如果没有这行代码，本轮之前的动作可能污染完成判断。
    return [event for event in event_snapshot[start_index:] if isinstance(event, dict)]  # 新增代码+AgentPySplitPhase4: 返回当前 full 会话内的字典事件副本；如果没有这行代码，调用方无法安全遍历。
# 新增代码+AgentPySplitPhase4: 函数段结束，computer_use_full_recent_events_after_mode_open 到此结束；如果没有这个边界说明，读者不容易看出事件窗口范围。


# 新增代码+AgentPySplitPhase4: 函数段开始，computer_use_full_successful_real_action_count 统计成功真实桌面动作数量；如果没有这段函数，模型可能无限重复 drag_path。
def computer_use_full_successful_real_action_count(observation_events: Any) -> int:  # 新增代码+AgentPySplitPhase4: 定义真实动作计数入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    count = 0  # 新增代码+AgentPySplitPhase4: 初始化成功动作计数；如果没有这行代码，函数无法累加结果。
    for event in computer_use_full_recent_events_after_mode_open(observation_events)[-80:]:  # 新增代码+AgentPySplitPhase4: 只看最近 80 条事件避免长期会话过慢；如果没有这行代码，长任务日志越积越慢。
        if event.get("kind") != "computer_use_action":  # 新增代码+AgentPySplitPhase4: 只统计桌面动作事件；如果没有这行代码，observe 或 status 会被误算成动作。
            continue  # 新增代码+AgentPySplitPhase4: 跳过非动作事件；如果没有这行代码，后续读取 payload 可能混入无关字段。
        payload = event.get("payload", {})  # 新增代码+AgentPySplitPhase4: 读取动作事件载荷；如果没有这行代码，无法判断动作是否成功。
        if not isinstance(payload, dict) or not bool(payload.get("ok", False)):  # 新增代码+AgentPySplitPhase4: 只统计成功动作；如果没有这行代码，失败或拒绝也会推进完成门。
            continue  # 新增代码+AgentPySplitPhase4: 跳过失败动作；如果没有这行代码，模型可能在没画出东西时被要求结束。
        data = payload.get("data", {})  # 新增代码+AgentPySplitPhase4: 读取 controller 返回数据；如果没有这行代码，无法读取底层输入数量。
        if not isinstance(data, dict):  # 新增代码+AgentPySplitPhase4: 防御异常 data 类型；如果没有这行代码，字符串结果会导致 get 调用异常。
            continue  # 新增代码+AgentPySplitPhase4: 跳过异常数据；如果没有这行代码，完成门可能崩溃。
        dispatch = data.get("dispatch", {}) if isinstance(data.get("dispatch", {}), dict) else {}  # 新增代码+AgentPySplitPhase4: 读取 SendInput 调度摘要；如果没有这行代码，无法区分真实输入和空动作。
        low_level_count = int(dispatch.get("low_level_event_count", data.get("low_level_event_count", 0)) or 0)  # 新增代码+AgentPySplitPhase4: 读取底层输入事件数量；如果没有这行代码，只有表面成功但没有输入的动作也会被算入。
        if low_level_count > 0 or bool(data.get("real_input_enabled", False)):  # 新增代码+AgentPySplitPhase4: 真实动作至少要有底层事件或真实输入标记；如果没有这行代码，纯状态报告可能被误算。
            count += 1  # 新增代码+AgentPySplitPhase4: 成功真实动作计数加一；如果没有这行代码，完成门永远不会触发。
    return count  # 新增代码+AgentPySplitPhase4: 返回成功动作数量；如果没有这行代码，调用方拿不到判断依据。
# 新增代码+AgentPySplitPhase4: 函数段结束，computer_use_full_successful_real_action_count 到此结束；如果没有这个边界说明，读者不容易看出动作计数范围。


# 新增代码+AgentPySplitPhase4: 函数段开始，computer_use_full_completion_action_threshold 按任务类型选择动作收束阈值；如果没有这段函数，简单绘图和复杂任务会混用同一策略。
def computer_use_full_completion_action_threshold(desktop_task_context: Any) -> int:  # 新增代码+AgentPySplitPhase4: 定义完成门阈值入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    if not isinstance(desktop_task_context, dict):  # 新增代码+AgentPySplitPhase4: 防御异常上下文形状；如果没有这行代码，坏状态可能让完成门崩溃。
        return 12  # 新增代码+AgentPySplitPhase4: 上下文异常时使用原保守阈值；如果没有这行代码，异常状态会导致没有返回值。
    task_goal = str(desktop_task_context.get("task_goal", "") or "").strip()  # 新增代码+AgentPySplitPhase4: 读取脱敏任务目标码；如果没有这行代码，函数无法区分简单绘图和其他 GUI 操作。
    if task_goal == "draw_with_local_paint":  # 新增代码+AgentPySplitPhase4: Paint 绘图任务使用更早收束阈值；如果没有这行代码，简单树/猫/房子任务会给模型过多漂移空间。
        return 6  # 新增代码+AgentPySplitPhase4: 六次真实绘制动作后要求模型观察并最终回答；如果没有这行代码，模型可能继续过度美化或改题。
    return 12  # 新增代码+AgentPySplitPhase4: 其他 GUI 任务保留原阈值；如果没有这行代码，复杂非绘图任务可能被过早截断。
# 新增代码+AgentPySplitPhase4: 函数段结束，computer_use_full_completion_action_threshold 到此结束；如果没有这个边界说明，读者不容易看出阈值来源。


# 新增代码+AgentPySplitPhase4: 函数段开始，computer_use_full_completion_signal_for_action 在动作足够后提示模型收束；如果没有这段函数，真实桌面已完成后模型仍可能继续加动作。
def computer_use_full_completion_signal_for_action(action_name: str, arguments: dict[str, Any], desktop_task_context: Any, observation_events: Any, record_observation: RecordObservation) -> str | None:  # 新增代码+AgentPySplitPhase4: 定义完成门入口；如果没有这行代码，agent.py 的旧函数没有新模块可以调用。
    safe_context = desktop_task_context if isinstance(desktop_task_context, dict) else {}  # 新增代码+AgentPySplitPhase4: 读取当前桌面任务上下文；如果没有这行代码，完成门无法区分 full 桌面任务和普通动作测试。
    if not bool(safe_context.get("active", False)) or not bool(safe_context.get("requires_gui_actions", False)):  # 新增代码+AgentPySplitPhase4: 只在 full GUI 任务中启用；如果没有这行代码，普通 Computer Use 工具调用可能被错误截断。
        return None  # 新增代码+AgentPySplitPhase4: 非 full GUI 任务不触发完成门；如果没有这行代码，调用方无法继续正常动作。
    if action_name not in COMPUTER_USE_COMPLETION_CHANGE_ACTIONS:  # 新增代码+AgentPySplitPhase4: 只拦截会继续改变桌面的动作；如果没有这行代码，observe 和 launch_app 也可能被错误拦住。
        return None  # 新增代码+AgentPySplitPhase4: 非改变类动作继续放行；如果没有这行代码，模型无法继续观察结果。
    if not computer_use_has_recent_model_visible_observation(observation_events):  # 新增代码+AgentPySplitPhase4: 必须已经有模型可见截图后才允许收敛；如果没有这行代码，模型可能没看过结果就被迫结束。
        return None  # 新增代码+AgentPySplitPhase4: 没有截图证据时继续让模型观察或动作；如果没有这行代码，真实完成缺少视觉依据。
    action_count = computer_use_full_successful_real_action_count(observation_events)  # 新增代码+AgentPySplitPhase4: 统计本轮已经成功执行的真实动作；如果没有这行代码，完成门没有量化依据。
    threshold = computer_use_full_completion_action_threshold(safe_context)  # 新增代码+AgentPySplitPhase4: 根据任务类型选择收束阈值；如果没有这行代码，简单 Paint 绘图仍会等到过多动作后才停止。
    if action_count < threshold:  # 新增代码+AgentPySplitPhase4: 未达到阈值时继续允许模型执行；如果没有这行代码，模型会被过早收敛。
        return None  # 新增代码+AgentPySplitPhase4: 动作数量不足时不拦截；如果没有这行代码，普通三四笔绘图无法继续完善。
    report = {"ok": True, "decision": "computer_use_full_completion_ready", "action": action_name, "successful_real_action_count": action_count, "threshold": threshold, "reason": "已经有模型可见截图，并且真实桌面动作数量足够，继续加笔风险大于收益。", "next_step": "final_answer", "argument_preview": {"has_window": isinstance(arguments.get("window"), dict), "has_points": bool(arguments.get("points"))}}  # 新增代码+AgentPySplitPhase4: 构造模型可读收敛报告；如果没有这行代码，模型不知道为什么不应继续动作。
    record_observation("computer_use_full_completion_ready", report)  # 新增代码+AgentPySplitPhase4: 把完成信号写入观察日志；如果没有这行代码，真实终端失败时无法复盘为什么停止动作。
    return "Computer Use full completion gate: computer_use_full_completion_ready\n请直接输出最终回答，说明已经使用 computer_use_mcp_v2 在真实本机应用中完成任务，并引用 screenshot、real_desktop_touched、low_level_event_count 等已有证据；不要继续调用鼠标键盘动作。\n" + json.dumps(report, ensure_ascii=False, indent=2)  # 新增代码+AgentPySplitPhase4: 返回强收敛文本给模型；如果没有这行代码，模型可能继续请求 drag_path。
# 新增代码+AgentPySplitPhase4: 函数段结束，computer_use_full_completion_signal_for_action 到此结束；如果没有这个边界说明，读者不容易看出完成门范围。
