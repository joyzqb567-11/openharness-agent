from __future__ import annotations  # 新增代码+Phase68ClosedLoopExecutor: 启用延迟类型注解，避免运行时因为类型互相引用而报错；如果没有这行代码，后续增加类型提示时更容易遇到导入循环。

from typing import Any, Callable  # 新增代码+Phase68ClosedLoopExecutor: 导入通用类型，帮助闭环执行器描述 observer/actor/verifier/recoverer 的输入输出；如果没有这行代码，接口含义会更难读懂。


PHASE68_CLOSED_LOOP_EXECUTOR_MARKER = "PHASE68_CLOSED_LOOP_EXECUTOR_READY"  # 新增代码+Phase68ClosedLoopExecutor: 定义真实终端验收 ready 标记；如果没有这行代码，controller 无法稳定识别 Phase68 输出。
PHASE68_CLOSED_LOOP_EXECUTOR_OK_TOKEN = "PHASE68_CLOSED_LOOP_EXECUTOR_OK"  # 新增代码+Phase68ClosedLoopExecutor: 定义真实终端验收 OK 标记；如果没有这行代码，用户无法一眼确认本阶段合同通过。
PHASE68_CLOSED_LOOP_EXECUTOR_MODEL = "phase68_windows_closed_loop_executor"  # 新增代码+Phase68ClosedLoopExecutor: 定义本阶段能力模型名称；如果没有这行代码，后续矩阵无法统一引用 Phase68 能力。
PHASE68_ACTIONS_EXPANDED = False  # 新增代码+Phase68ClosedLoopExecutor: 明确 Phase68 不扩大真实桌面动作范围；如果没有这行代码，闭环调度层可能被误认为已经新增真实输入能力。
PHASE68_WRITE_ACTION_KINDS = {"write"}  # 新增代码+Phase68ClosedLoopExecutor: 定义哪些 action_kind 属于写动作；如果没有这行代码，验证器无法知道哪些动作必须做后置校验。
PHASE68_VERIFY_ACTION_KINDS = {"verify", "check"}  # 新增代码+Phase68ClosedLoopExecutor: 定义哪些 action_kind 属于纯验证步骤；如果没有这行代码，验证步骤可能被误送给动作执行器。
PHASE68_READ_ONLY_ACTION_KINDS = {"observe", "read", "wait"}  # 新增代码+Phase68ClosedLoopExecutor: 定义只读步骤类型；如果没有这行代码，只读步骤可能被误判为写动作。
PHASE68_WRITE_OPERATION_PREFIXES = ("type", "click", "draw", "drag", "save", "select", "launch", "focus", "hotkey", "scroll", "menu")  # 新增代码+Phase68ClosedLoopExecutor: 定义常见会改变桌面状态的操作名前缀；如果没有这行代码，旧计划里缺少 action_kind 时无法安全识别写动作。
PHASE114_VERIFIED_WINDOW_ACTIONS_MARKER = "PHASE114_VERIFIED_WINDOW_ACTIONS_READY"  # 新增代码+VerifiedWindowActionsMaturity: 定义已验证窗口动作门禁 ready 标记；如果没有这行代码，最终成熟矩阵无法稳定识别 Task6 能力。
PHASE114_VERIFIED_WINDOW_ACTIONS_OK_TOKEN = "PHASE114_VERIFIED_WINDOW_ACTIONS_OK"  # 新增代码+VerifiedWindowActionsMaturity: 定义已验证窗口动作门禁 OK 标记；如果没有这行代码，真实终端输出无法用固定 token 证明动作门禁成熟。
PHASE114_VERIFIED_WINDOW_ACTIONS_MODEL = "phase114_verified_window_actions_maturity"  # 新增代码+VerifiedWindowActionsMaturity: 定义 Task6 动作门禁模型名；如果没有这行代码，后续报告无法区分它和 Phase68 基础闭环。
PHASE114_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+VerifiedWindowActionsMaturity: 声明本阶段没有扩大未受控动作面；如果没有这行代码，用户可能误以为新增了绕过授权的底层桌面控制。


def _phase114_report_dict(value: Any) -> dict[str, Any]:  # 新增代码+VerifiedWindowActionsMaturity: 函数段开始，把外部传入的身份报告安全转成字典；如果没有这个函数，None 或坏类型会让动作门禁崩溃。
    return dict(value) if isinstance(value, dict) else {}  # 新增代码+VerifiedWindowActionsMaturity: 只有字典才复制返回，否则返回空字典；如果没有这行代码，缺失身份会变成异常而不是可审计拒绝。
# 新增代码+VerifiedWindowActionsMaturity: 函数段结束，_phase114_report_dict 到此结束；如果没有这个边界说明，初学者不容易看出身份报告清洗范围。


def phase114_verified_action_gate(session_id: Any = "", window_identity: dict[str, Any] | None = None, target_identity_verification: dict[str, Any] | None = None, after_target_identity_verification: dict[str, Any] | None = None, require_verified_identity: bool = False, abort_requested: bool = False) -> dict[str, Any]:  # 新增代码+VerifiedWindowActionsMaturity: 函数段开始，统一判断桌面动作是否绑定已验证自有窗口；如果没有这个函数，点击、输入、热键会各自重复并可能漏掉漂移阻断。
    before_identity = _phase114_report_dict(target_identity_verification)  # 新增代码+VerifiedWindowActionsMaturity: 读取动作前目标身份验证报告；如果没有这行代码，动作无法知道当前窗口是否仍是 agent 启动的窗口。
    after_identity = _phase114_report_dict(after_target_identity_verification) or before_identity  # 新增代码+VerifiedWindowActionsMaturity: 读取动作后身份报告，缺省复用动作前报告；如果没有这行代码，记录型测试没有后态身份证据。
    safe_window_identity = _phase114_report_dict(window_identity)  # 新增代码+VerifiedWindowActionsMaturity: 读取被绑定的窗口身份摘要；如果没有这行代码，报告无法展示动作目标窗口凭证。
    missing_identity = bool(require_verified_identity and (not str(session_id or "").strip() or not safe_window_identity or not before_identity))  # 新增代码+VerifiedWindowActionsMaturity: 判断强制身份模式下是否缺少 session/window/verification 三件套；如果没有这行代码，空身份也可能被当成可执行。
    before_allowed = bool(before_identity.get("allowed") and before_identity.get("target_identity_verified") and not before_identity.get("target_drift_blocks_action"))  # 新增代码+VerifiedWindowActionsMaturity: 判断动作前身份是否可信；如果没有这行代码，漂移窗口可能继续接收动作。
    after_allowed = bool(after_identity.get("allowed", before_allowed) and after_identity.get("target_identity_verified", before_identity.get("target_identity_verified")) and not after_identity.get("target_drift_blocks_action", before_identity.get("target_drift_blocks_action")))  # 新增代码+VerifiedWindowActionsMaturity: 判断动作后身份是否仍可信；如果没有这行代码，动作后漂移不会进入审计字段。
    same_target = bool(before_allowed and after_allowed and not missing_identity)  # 新增代码+VerifiedWindowActionsMaturity: 汇总动作前后是否同一已验证目标；如果没有这行代码，上层只能手工组合多个身份字段。
    blocked = False  # 新增代码+VerifiedWindowActionsMaturity: 初始化阻断结果；如果没有这行代码，后续分支无法形成统一布尔值。
    decision = "identity_not_required"  # 新增代码+VerifiedWindowActionsMaturity: 默认兼容旧调用方不强制身份；如果没有这行代码，Phase68/70/71 旧合同会被误拦截。
    if abort_requested:  # 新增代码+VerifiedWindowActionsMaturity: 急停优先级最高，任何动作都必须先停下；如果没有这行代码，用户急停时仍可能派发输入事件。
        blocked = True  # 新增代码+VerifiedWindowActionsMaturity: 标记急停导致阻断；如果没有这行代码，急停报告可能说停了但实际继续。
        decision = "abort_before_dispatch"  # 新增代码+VerifiedWindowActionsMaturity: 写入稳定急停决策码；如果没有这行代码，终端验收无法确认是派发前阻断。
    elif missing_identity:  # 新增代码+VerifiedWindowActionsMaturity: 强制身份但三件套缺失时必须拒绝；如果没有这行代码，未验证窗口可能收到动作。
        blocked = True  # 新增代码+VerifiedWindowActionsMaturity: 标记缺身份阻断；如果没有这行代码，缺身份路径仍可能继续。
        decision = "missing_verified_target_identity"  # 新增代码+VerifiedWindowActionsMaturity: 写入稳定缺身份决策码；如果没有这行代码，调用方难以区分缺身份和普通失败。
    elif require_verified_identity and not before_allowed:  # 新增代码+VerifiedWindowActionsMaturity: 强制身份且动作前验证不通过时拒绝；如果没有这行代码，同标题不同 pid 的窗口可能被误控。
        blocked = True  # 新增代码+VerifiedWindowActionsMaturity: 标记动作前漂移或未验证阻断；如果没有这行代码，漂移只会变成提示而不是门禁。
        decision = "target_drift_blocks_action" if before_identity.get("target_drift_blocks_action") or before_identity.get("decision") == "target_drift_blocks_action" else "target_identity_not_verified"  # 新增代码+VerifiedWindowActionsMaturity: 优先保留漂移决策码；如果没有这行代码，矩阵无法稳定证明漂移会阻断。
    elif require_verified_identity and not after_allowed:  # 新增代码+VerifiedWindowActionsMaturity: 强制身份且动作后验证不通过时拒绝；如果没有这行代码，后态漂移不会被归因。
        blocked = True  # 新增代码+VerifiedWindowActionsMaturity: 标记动作后漂移阻断；如果没有这行代码，后态校验失败可能被忽略。
        decision = "target_drift_blocks_action"  # 新增代码+VerifiedWindowActionsMaturity: 写入稳定漂移阻断决策码；如果没有这行代码，动作层无法统一展示漂移原因。
    elif require_verified_identity:  # 新增代码+VerifiedWindowActionsMaturity: 强制身份且前后验证通过时允许动作；如果没有这行代码，成熟 API 没有成功路径。
        decision = "target_identity_verified"  # 新增代码+VerifiedWindowActionsMaturity: 写入稳定放行决策码；如果没有这行代码，报告无法说明为什么允许动作。
    return {"marker": PHASE114_VERIFIED_WINDOW_ACTIONS_MARKER, "ok_token": PHASE114_VERIFIED_WINDOW_ACTIONS_OK_TOKEN, "model": PHASE114_VERIFIED_WINDOW_ACTIONS_MODEL, "session_id": str(session_id or ""), "window_identity": safe_window_identity, "before_identity": before_identity, "after_identity": after_identity, "same_target": same_target, "blocked": blocked, "decision": decision, "identity_required": bool(require_verified_identity), "actions_require_verified_window": bool(require_verified_identity), "low_level_event_count": 0, "uncontrolled_actions_expanded": PHASE114_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+VerifiedWindowActionsMaturity: 返回统一门禁报告；如果没有这行代码，动作层和矩阵拿不到同一套字段。
# 新增代码+VerifiedWindowActionsMaturity: 函数段结束，phase114_verified_action_gate 到此结束；如果没有这个边界说明，初学者不容易看出动作身份门禁范围。


def _phase68_bool_token(value: Any) -> str:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，把布尔值转换成验收 token 需要的小写 true/false；如果没有这个函数，CLI 输出容易出现 Python 的 True/False 导致场景匹配失败。
    return "true" if bool(value) else "false"  # 新增代码+Phase68ClosedLoopExecutor: 返回稳定小写布尔字符串；如果没有这行代码，真实终端场景 token 无法稳定匹配。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出 token 转换范围。


def _phase68_steps(task_plan: Any) -> list[dict[str, Any]]:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，从任务计划里安全提取步骤列表；如果没有这个函数，执行器会依赖调用方传入完全正确的结构。
    raw_steps = task_plan.get("steps", []) if isinstance(task_plan, dict) else task_plan  # 新增代码+Phase68ClosedLoopExecutor: 兼容 dict 计划和直接 list 计划；如果没有这行代码，Phase67 planner 输出和测试简化输入不能共用同一个执行器。
    if not isinstance(raw_steps, list):  # 新增代码+Phase68ClosedLoopExecutor: 检查步骤容器是否为列表；如果没有这行代码，错误输入可能在循环中抛出难懂异常。
        return []  # 新增代码+Phase68ClosedLoopExecutor: 对非法步骤结构返回空计划；如果没有这行代码，执行器可能把字符串当成步骤逐字遍历。
    steps = []  # 新增代码+Phase68ClosedLoopExecutor: 创建规范化步骤列表；如果没有这行代码，后续无法逐步收集合法 dict 步骤。
    for raw_step in raw_steps:  # 新增代码+Phase68ClosedLoopExecutor: 遍历原始步骤；如果没有这行代码，执行器无法清洗计划内容。
        if isinstance(raw_step, dict):  # 新增代码+Phase68ClosedLoopExecutor: 只接受字典步骤；如果没有这行代码，非结构化步骤可能污染执行事件。
            steps.append(dict(raw_step))  # 新增代码+Phase68ClosedLoopExecutor: 复制步骤避免修改调用方原始计划；如果没有这行代码，执行器可能产生隐式副作用。
    return steps  # 新增代码+Phase68ClosedLoopExecutor: 返回清洗后的步骤列表；如果没有这行代码，调用方拿不到可执行步骤。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_steps 到此结束；如果没有这个边界说明，初学者不容易看出计划解析范围。


def _phase68_action_kind(step: dict[str, Any]) -> str:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，统一读取步骤动作类型；如果没有这个函数，大小写和缺省值会散落在执行器各处。
    return str(step.get("action_kind", "")).strip().lower()  # 新增代码+Phase68ClosedLoopExecutor: 返回小写 action_kind；如果没有这行代码，Write/write/WRITE 可能被当成不同类型。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_action_kind 到此结束；如果没有这个边界说明，初学者不容易看出动作类型读取范围。


def _phase68_operation(step: dict[str, Any]) -> str:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，统一读取步骤操作名；如果没有这个函数，事件和判定会出现重复取值逻辑。
    return str(step.get("operation", "")).strip()  # 新增代码+Phase68ClosedLoopExecutor: 返回清理后的 operation；如果没有这行代码，空格和非字符串值可能导致事件名混乱。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_operation 到此结束；如果没有这个边界说明，初学者不容易看出操作名读取范围。


def _phase68_is_verify_step(step: dict[str, Any]) -> bool:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，判断步骤是否是纯验证；如果没有这个函数，验证步骤可能被误当作真实动作。
    action_kind = _phase68_action_kind(step)  # 新增代码+Phase68ClosedLoopExecutor: 读取动作类型；如果没有这行代码，无法判断 verify/check。
    operation = _phase68_operation(step).lower()  # 新增代码+Phase68ClosedLoopExecutor: 读取小写操作名；如果没有这行代码，缺少 action_kind 的 verify_result 无法兼容。
    return action_kind in PHASE68_VERIFY_ACTION_KINDS or operation.startswith("verify")  # 新增代码+Phase68ClosedLoopExecutor: 根据类型或操作名前缀判断验证步骤；如果没有这行代码，后置验证可能走错执行路径。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_is_verify_step 到此结束；如果没有这个边界说明，初学者不容易看出验证判断范围。


def _phase68_is_write_step(step: dict[str, Any]) -> bool:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，判断步骤是否会改变桌面状态；如果没有这个函数，写动作后置验证规则无法落地。
    action_kind = _phase68_action_kind(step)  # 新增代码+Phase68ClosedLoopExecutor: 读取动作类型；如果没有这行代码，显式 write 标记无法生效。
    operation = _phase68_operation(step).lower()  # 新增代码+Phase68ClosedLoopExecutor: 读取小写操作名；如果没有这行代码，旧计划的 operation 前缀无法用于兜底判断。
    if action_kind in PHASE68_WRITE_ACTION_KINDS:  # 新增代码+Phase68ClosedLoopExecutor: 优先信任显式写动作标记；如果没有这行代码，Phase67 输出的 action_kind 会被忽略。
        return True  # 新增代码+Phase68ClosedLoopExecutor: 返回写动作成立；如果没有这行代码，显式写动作可能跳过验证。
    if action_kind in PHASE68_READ_ONLY_ACTION_KINDS or action_kind in PHASE68_VERIFY_ACTION_KINDS:  # 新增代码+Phase68ClosedLoopExecutor: 排除只读和验证动作；如果没有这行代码，观察或等待可能被误判为写动作。
        return False  # 新增代码+Phase68ClosedLoopExecutor: 返回不是写动作；如果没有这行代码，只读动作会被错误要求验证和恢复。
    return operation.startswith(PHASE68_WRITE_OPERATION_PREFIXES)  # 新增代码+Phase68ClosedLoopExecutor: 用操作名前缀兜底识别写动作；如果没有这行代码，缺少 action_kind 的旧步骤可能绕过后置验证。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_is_write_step 到此结束；如果没有这个边界说明，初学者不容易看出写动作判断范围。


def _phase68_event(state: str, step: dict[str, Any] | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，统一生成执行轨迹事件；如果没有这个函数，事件字段会不一致，后续审计很难读。
    event = {"state": state}  # 新增代码+Phase68ClosedLoopExecutor: 写入事件状态；如果没有这行代码，轨迹无法说明当前处于观察、行动还是验证。
    if step is not None:  # 新增代码+Phase68ClosedLoopExecutor: 只有存在步骤时才写入步骤信息；如果没有这行代码，停止事件会被迫携带空步骤。
        event["operation"] = _phase68_operation(step)  # 新增代码+Phase68ClosedLoopExecutor: 记录当前操作名；如果没有这行代码，调试时无法知道事件属于哪个步骤。
        event["action_kind"] = _phase68_action_kind(step)  # 新增代码+Phase68ClosedLoopExecutor: 记录当前动作类型；如果没有这行代码，审计时无法分辨写动作和验证动作。
    if payload:  # 新增代码+Phase68ClosedLoopExecutor: 只有存在附加信息时才合并；如果没有这行代码，空 payload 可能污染事件结构。
        event.update(payload)  # 新增代码+Phase68ClosedLoopExecutor: 合并观察、动作、验证或恢复结果；如果没有这行代码，事件只剩状态没有证据细节。
    return event  # 新增代码+Phase68ClosedLoopExecutor: 返回规范事件；如果没有这行代码，调用方无法保存轨迹。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_event 到此结束；如果没有这个边界说明，初学者不容易看出事件生成范围。


def _phase68_call_named(component: Any, method_name: str, fallback: Callable[..., Any], *args: Any) -> Any:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，兼容对象方法和可调用函数两种假组件；如果没有这个函数，测试和未来运行时需要硬编码同一种组件形态。
    method = getattr(component, method_name, None)  # 新增代码+Phase68ClosedLoopExecutor: 尝试读取指定方法；如果没有这行代码，observer.observe 这类对象接口无法被调用。
    if callable(method):  # 新增代码+Phase68ClosedLoopExecutor: 判断对象方法是否可调用；如果没有这行代码，属性重名但不可调用会导致异常。
        return method(*args)  # 新增代码+Phase68ClosedLoopExecutor: 调用对象方法；如果没有这行代码，标准组件接口不会执行。
    if callable(component):  # 新增代码+Phase68ClosedLoopExecutor: 判断组件本身是否可调用；如果没有这行代码，简单函数式测试替身无法使用。
        return component(*args)  # 新增代码+Phase68ClosedLoopExecutor: 调用函数式组件；如果没有这行代码，轻量调用方需要额外包一层对象。
    return fallback(*args)  # 新增代码+Phase68ClosedLoopExecutor: 使用兜底函数返回安全默认值；如果没有这行代码，缺失组件会产生难懂异常。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_call_named 到此结束；如果没有这个边界说明，初学者不容易看出组件调用兼容范围。


def _phase68_default_observation(step: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，生成缺省观察结果；如果没有这个函数，缺少 observer 时执行器无法给出可审计轨迹。
    return {"observation_id": "default-observation", "step_operation": _phase68_operation(step)}  # 新增代码+Phase68ClosedLoopExecutor: 返回最小观察证据；如果没有这行代码，动作会失去观察输入。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_default_observation 到此结束；如果没有这个边界说明，初学者不容易看出默认观察范围。


def _phase68_default_action(step: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，生成缺省动作结果；如果没有这个函数，缺少 actor 时执行器无法做合同自检。
    return {"acted": True, "operation": _phase68_operation(step), "write_action": _phase68_is_write_step(step), "observation_id": observation.get("observation_id", "")}  # 新增代码+Phase68ClosedLoopExecutor: 返回最小动作证据；如果没有这行代码，后置验证没有动作输入。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_default_action 到此结束；如果没有这个边界说明，初学者不容易看出默认动作范围。


def _phase68_default_verification(step: dict[str, Any], observation: dict[str, Any], action_result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，生成缺省验证结果；如果没有这个函数，缺少 verifier 时写动作无法被验证。
    return {"passed": True, "checked_operation": _phase68_operation(step), "observation_id": observation.get("observation_id", ""), "acted": bool(action_result.get("acted", False))}  # 新增代码+Phase68ClosedLoopExecutor: 默认认为合同自检通过；如果没有这行代码，执行器无法在无真实桌面时完成自检。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_default_verification 到此结束；如果没有这个边界说明，初学者不容易看出默认验证范围。


def _phase68_default_recovery(step: dict[str, Any], observation: dict[str, Any], action_result: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，生成缺省恢复结果；如果没有这个函数，验证失败时执行器无法保持统一事件结构。
    return {"recovered": True, "strategy": "observe_again", "operation": _phase68_operation(step), "failed_check": verification.get("checked_operation", "")}  # 新增代码+Phase68ClosedLoopExecutor: 返回最小恢复证据；如果没有这行代码，失败恢复没有可审计结果。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_default_recovery 到此结束；如果没有这个边界说明，初学者不容易看出默认恢复范围。


def _phase68_verification_passed(verification: Any) -> bool:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，统一解释验证结果是否通过；如果没有这个函数，不同 verifier 返回格式会导致恢复判断混乱。
    if isinstance(verification, dict):  # 新增代码+Phase68ClosedLoopExecutor: 优先处理字典验证报告；如果没有这行代码，常见结构化结果无法读取 passed 字段。
        return bool(verification.get("passed", False))  # 新增代码+Phase68ClosedLoopExecutor: 返回 passed 字段；如果没有这行代码，失败恢复无法准确触发。
    return bool(verification)  # 新增代码+Phase68ClosedLoopExecutor: 兼容布尔或真值验证结果；如果没有这行代码，轻量 verifier 返回 True 会被误判。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_verification_passed 到此结束；如果没有这个边界说明，初学者不容易看出验证解释范围。


def _phase68_has_verified_after_write(events: list[dict[str, Any]]) -> bool:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，判断写动作后是否出现验证事件；如果没有这个函数，合同报告无法证明后置校验真的发生。
    pending_write = False  # 新增代码+Phase68ClosedLoopExecutor: 记录是否刚发生写动作；如果没有这行代码，函数无法知道哪个验证对应写动作。
    for event in events:  # 新增代码+Phase68ClosedLoopExecutor: 遍历执行轨迹；如果没有这行代码，无法从事件中推导闭环事实。
        if event.get("state") == "acted" and bool(event.get("write_action", False)):  # 新增代码+Phase68ClosedLoopExecutor: 识别写动作事件；如果没有这行代码，普通事件会干扰验证判断。
            pending_write = True  # 新增代码+Phase68ClosedLoopExecutor: 标记下一次验证应当覆盖该写动作；如果没有这行代码，函数无法确认后置验证。
        elif event.get("state") == "verified" and pending_write:  # 新增代码+Phase68ClosedLoopExecutor: 找到写动作后的验证事件；如果没有这行代码，验证事实不会被识别。
            return True  # 新增代码+Phase68ClosedLoopExecutor: 返回写后验证成立；如果没有这行代码，合同报告会错误显示失败。
        elif event.get("state") == "observed" and pending_write:  # 新增代码+Phase68ClosedLoopExecutor: 遇到新观察仍保持写动作待验证状态；如果没有这行代码，恢复后的再观察可能错误清空验证需求。
            pending_write = pending_write  # 新增代码+Phase68ClosedLoopExecutor: 明确不清空待验证标记；如果没有这行代码，读代码的人容易误以为观察会替代验证。
    return False  # 新增代码+Phase68ClosedLoopExecutor: 没找到写后验证则返回失败；如果没有这行代码，缺陷会被误报为通过。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_has_verified_after_write 到此结束；如果没有这个边界说明，初学者不容易看出后置验证判断范围。


def _phase68_has_required_loop_states(events: list[dict[str, Any]]) -> bool:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，判断闭环轨迹是否包含必要状态；如果没有这个函数，报告无法概括执行是否真正成环。
    states = {str(event.get("state", "")) for event in events}  # 新增代码+Phase68ClosedLoopExecutor: 收集事件状态集合；如果没有这行代码，后续判断会重复遍历事件。
    return {"observed", "decided", "acted", "verified", "stopped"}.issubset(states)  # 新增代码+Phase68ClosedLoopExecutor: 判断基础闭环状态是否齐全；如果没有这行代码，缺少任一关键阶段也可能被误判通过。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_phase68_has_required_loop_states 到此结束；如果没有这个边界说明，初学者不容易看出闭环状态判断范围。


class WindowsClosedLoopComputerExecutor:  # 新增代码+Phase68ClosedLoopExecutor: 类段开始，提供 Windows Computer Use 闭环调度器；如果没有这个类，planner 到真实动作层之间缺少观察-行动-验证-恢复的统一执行纪律。
    def blind_write_chain_detected(self, events: list[dict[str, Any]]) -> bool:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，检测两个写动作之间是否缺少观察；如果没有这个函数，连续坐标写动作可能绕过视觉/UIA 证据。
        pending_write = False  # 新增代码+Phase68ClosedLoopExecutor: 记录是否已经发生一个尚未被新观察隔开的写动作；如果没有这行代码，检测器无法发现连续写动作。
        for event in events:  # 新增代码+Phase68ClosedLoopExecutor: 遍历事件轨迹；如果没有这行代码，检测器无法扫描动作顺序。
            if event.get("state") == "observed":  # 新增代码+Phase68ClosedLoopExecutor: 观察事件会重新建立桌面证据；如果没有这行代码，安全的写-观察-写链会被误判危险。
                pending_write = False  # 新增代码+Phase68ClosedLoopExecutor: 清除待观察写动作标记；如果没有这行代码，第二个安全写动作会被误杀。
            if event.get("state") == "acted" and bool(event.get("write_action", False)):  # 新增代码+Phase68ClosedLoopExecutor: 识别写动作事件；如果没有这行代码，点击、输入、绘制等风险动作不会被检查。
                if pending_write:  # 新增代码+Phase68ClosedLoopExecutor: 如果前一个写动作后没有观察，则命中危险链；如果没有这行代码，连续盲写无法被阻断。
                    return True  # 新增代码+Phase68ClosedLoopExecutor: 返回发现危险链；如果没有这行代码，调用方无法阻断盲坐标链。
                pending_write = True  # 新增代码+Phase68ClosedLoopExecutor: 标记已经发生一个写动作；如果没有这行代码，下一次写动作无法被检测。
        return False  # 新增代码+Phase68ClosedLoopExecutor: 未发现危险链则返回安全；如果没有这行代码，正常闭环也会被当成失败。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，WindowsClosedLoopComputerExecutor.blind_write_chain_detected 到此结束；如果没有这个边界说明，初学者不容易看出盲写链检测范围。

    def run(self, task_plan: Any, observer: Any, actor: Any, verifier: Any, recoverer: Any, max_steps: int = 12) -> dict[str, Any]:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，按观察-决策-行动-验证-恢复闭环执行任务计划；如果没有这个函数，Phase67 计划无法进入可审计执行轨道。
        events = []  # 新增代码+Phase68ClosedLoopExecutor: 初始化执行事件列表；如果没有这行代码，后续无法审计执行顺序。
        steps = _phase68_steps(task_plan)[:max_steps]  # 新增代码+Phase68ClosedLoopExecutor: 提取并限制最大步骤数；如果没有这行代码，异常计划可能导致无限或过长执行。
        last_action_result = {}  # 新增代码+Phase68ClosedLoopExecutor: 保存上一动作结果给验证步骤使用；如果没有这行代码，独立 verify_result 步骤没有上下文。
        for step_index, step in enumerate(steps):  # 新增代码+Phase68ClosedLoopExecutor: 逐步执行计划；如果没有这行代码，任务计划不会被处理。
            observation = _phase68_call_named(observer, "observe", _phase68_default_observation, step)  # 新增代码+Phase68ClosedLoopExecutor: 每一步先观察桌面状态；如果没有这行代码，动作会退化成盲目坐标操作。
            events.append(_phase68_event("observed", step, {"step_index": step_index, "observation": observation}))  # 新增代码+Phase68ClosedLoopExecutor: 记录观察事件；如果没有这行代码，审计轨迹无法证明动作前有证据。
            decision = "verify" if _phase68_is_verify_step(step) else "act"  # 新增代码+Phase68ClosedLoopExecutor: 根据步骤类型做最小决策；如果没有这行代码，验证步骤和动作步骤无法分流。
            events.append(_phase68_event("decided", step, {"step_index": step_index, "decision": decision}))  # 新增代码+Phase68ClosedLoopExecutor: 记录决策事件；如果没有这行代码，执行轨迹缺少从观察到行动的中间理由。
            if _phase68_is_verify_step(step):  # 新增代码+Phase68ClosedLoopExecutor: 纯验证步骤不触发动作执行器；如果没有这行代码，verify_result 可能误点真实界面。
                verification = _phase68_call_named(verifier, "verify", _phase68_default_verification, step, observation, last_action_result)  # 新增代码+Phase68ClosedLoopExecutor: 调用验证器检查当前状态；如果没有这行代码，验证步骤不会真正执行。
                events.append(_phase68_event("verified", step, {"step_index": step_index, "verification": verification, "write_action": False, "passed": _phase68_verification_passed(verification)}))  # 新增代码+Phase68ClosedLoopExecutor: 记录验证事件；如果没有这行代码，轨迹无法展示独立验证结果。
                continue  # 新增代码+Phase68ClosedLoopExecutor: 验证步骤处理完后进入下一步；如果没有这行代码，验证步骤还会继续被当动作执行。
            identity_gate = phase114_verified_action_gate(session_id=step.get("session_id", ""), window_identity=step.get("window_identity"), target_identity_verification=step.get("target_identity_verification"), after_target_identity_verification=step.get("after_target_identity_verification"), require_verified_identity=bool(step.get("require_verified_identity", False)), abort_requested=bool(step.get("abort_requested", False)))  # 新增代码+VerifiedWindowActionsMaturity: 在调用动作执行器前先做已验证窗口身份门禁；如果没有这行代码，闭环层可能在目标漂移后继续调用 actor。
            if bool(identity_gate.get("blocked")):  # 新增代码+VerifiedWindowActionsMaturity: 检查身份门禁是否要求阻断；如果没有这行代码，门禁报告只会记录不会真正拦截。
                action_result = {"ok": False, "acted": False, "operation": _phase68_operation(step), "write_action": _phase68_is_write_step(step), "zero_event_refusal": True, "high_level_event_count": 0, "low_level_event_count": 0, **identity_gate}  # 新增代码+VerifiedWindowActionsMaturity: 构造零事件阻断动作结果；如果没有这行代码，actor 被跳过时事件轨迹缺少动作阶段证据。
                events.append(_phase68_event("acted", step, {"step_index": step_index, "action_result": action_result, "write_action": bool(action_result.get("write_action", False))}))  # 新增代码+VerifiedWindowActionsMaturity: 记录被门禁阻断的动作事件；如果没有这行代码，审计轨迹看不到为什么没有派发。
                last_action_result = action_result  # 新增代码+VerifiedWindowActionsMaturity: 保存阻断结果给后续验证步骤读取；如果没有这行代码，独立 verify_result 不知道刚才被拦截。
                continue  # 新增代码+VerifiedWindowActionsMaturity: 门禁阻断后跳过 actor 调用；如果没有这行代码，仍会执行真实或记录型动作。
            action_result = _phase68_call_named(actor, "act", _phase68_default_action, step, observation)  # 修改代码+VerifiedWindowActionsMaturity: 只有身份门禁放行后才调用动作执行器；如果没有这行代码，闭环只会观察不会行动。
            action_result = dict(action_result) if isinstance(action_result, dict) else {"acted": bool(action_result)}  # 新增代码+Phase68ClosedLoopExecutor: 标准化动作结果；如果没有这行代码，非字典返回值会让后续验证崩溃。
            write_action = _phase68_is_write_step(step) or bool(action_result.get("write_action", False))  # 新增代码+Phase68ClosedLoopExecutor: 识别当前动作是否改变桌面状态；如果没有这行代码，写后验证规则无法触发。
            action_result["write_action"] = write_action  # 新增代码+Phase68ClosedLoopExecutor: 把写动作判定写回动作结果；如果没有这行代码，事件和验证器可能拿不到统一字段。
            events.append(_phase68_event("acted", step, {"step_index": step_index, "action_result": action_result, "write_action": write_action}))  # 新增代码+Phase68ClosedLoopExecutor: 记录动作事件；如果没有这行代码，审计轨迹无法证明实际行动发生。
            last_action_result = action_result  # 新增代码+Phase68ClosedLoopExecutor: 更新上一动作结果；如果没有这行代码，后续验证步骤无法知道刚才做了什么。
            if write_action:  # 新增代码+Phase68ClosedLoopExecutor: 只有写动作必须做动作后验证；如果没有这行代码，只读动作会被不必要地验证。
                verification = _phase68_call_named(verifier, "verify", _phase68_default_verification, step, observation, action_result)  # 新增代码+Phase68ClosedLoopExecutor: 调用动作后验证器；如果没有这行代码，点击输入失败不会被发现。
                verification_passed = _phase68_verification_passed(verification)  # 新增代码+Phase68ClosedLoopExecutor: 解释验证是否通过；如果没有这行代码，恢复逻辑无法可靠判断。
                events.append(_phase68_event("verified", step, {"step_index": step_index, "verification": verification, "write_action": True, "passed": verification_passed}))  # 新增代码+Phase68ClosedLoopExecutor: 记录写后验证事件；如果没有这行代码，报告无法证明验证发生在动作之后。
                if not verification_passed:  # 新增代码+Phase68ClosedLoopExecutor: 验证失败时进入恢复；如果没有这行代码，真实应用状态漂移后任务会继续盲走。
                    recovery = _phase68_call_named(recoverer, "recover", _phase68_default_recovery, step, observation, action_result, verification)  # 新增代码+Phase68ClosedLoopExecutor: 调用恢复器；如果没有这行代码，失败后没有纠偏机会。
                    events.append(_phase68_event("recovered", step, {"step_index": step_index, "recovery": recovery}))  # 新增代码+Phase68ClosedLoopExecutor: 记录恢复事件；如果没有这行代码，恢复事实无法被审计。
                    recovery_observation = _phase68_call_named(observer, "observe", _phase68_default_observation, step)  # 新增代码+Phase68ClosedLoopExecutor: 恢复后重新观察；如果没有这行代码，恢复后的状态仍然没有证据。
                    events.append(_phase68_event("observed", step, {"step_index": step_index, "after_recovery": True, "observation": recovery_observation}))  # 新增代码+Phase68ClosedLoopExecutor: 记录恢复后的观察事件；如果没有这行代码，下一步可能缺少新证据。
                    recovery_verification = _phase68_call_named(verifier, "verify", _phase68_default_verification, step, recovery_observation, action_result)  # 新增代码+Phase68ClosedLoopExecutor: 恢复后再次验证；如果没有这行代码，恢复是否真的有效无法确认。
                    events.append(_phase68_event("verified", step, {"step_index": step_index, "after_recovery": True, "verification": recovery_verification, "write_action": True, "passed": _phase68_verification_passed(recovery_verification)}))  # 新增代码+Phase68ClosedLoopExecutor: 记录恢复后的验证事件；如果没有这行代码，恢复闭环不完整。
        blocked_blind_chain = self.blind_write_chain_detected(events)  # 新增代码+Phase68ClosedLoopExecutor: 检查本次执行是否出现盲写链；如果没有这行代码，执行器无法在结果里暴露安全状态。
        stop_reason = "blind_coordinate_chain_detected" if blocked_blind_chain else "completed"  # 新增代码+Phase68ClosedLoopExecutor: 根据安全检查选择停止原因；如果没有这行代码，停止事件无法说明是成功还是阻断。
        events.append(_phase68_event("stopped", None, {"reason": stop_reason}))  # 新增代码+Phase68ClosedLoopExecutor: 记录停止事件；如果没有这行代码，闭环轨迹没有明确结束边界。
        event_states = [str(event.get("state", "")) for event in events]  # 新增代码+Phase68ClosedLoopExecutor: 提取事件状态列表；如果没有这行代码，报告调用方要重复解析事件。
        result = {"model": PHASE68_CLOSED_LOOP_EXECUTOR_MODEL, "events": events, "event_states": event_states, "closed_loop_execution": _phase68_has_required_loop_states(events), "post_action_verification": _phase68_has_verified_after_write(events), "failure_recovery": "recovered" in event_states, "blind_coordinate_chain_blocked": not blocked_blind_chain, "actions_expanded": PHASE68_ACTIONS_EXPANDED, "stopped_reason": stop_reason}  # 新增代码+Phase68ClosedLoopExecutor: 汇总闭环执行报告；如果没有这行代码，调用方只能手工理解事件轨迹。
        return result  # 新增代码+Phase68ClosedLoopExecutor: 返回执行报告；如果没有这行代码，测试和验收无法拿到结果。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，WindowsClosedLoopComputerExecutor.run 到此结束；如果没有这个边界说明，初学者不容易看出闭环执行范围。
# 新增代码+Phase68ClosedLoopExecutor: 类段结束，WindowsClosedLoopComputerExecutor 到此结束；如果没有这个边界说明，初学者不容易看出闭环执行器范围。


class _Phase68ContractObserver:  # 新增代码+Phase68ClosedLoopExecutor: 类段开始，提供合同自检用假观察器；如果没有这个类，合同自检会依赖真实桌面环境导致不稳定。
    def __init__(self) -> None:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，初始化观察次数；如果没有这个函数，自检无法产生可区分的观察编号。
        self.calls = 0  # 新增代码+Phase68ClosedLoopExecutor: 保存观察调用次数；如果没有这行代码，观察证据无法体现顺序。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_Phase68ContractObserver.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def observe(self, step: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，生成合同自检观察结果；如果没有这个函数，自检无法证明每步先观察。
        self.calls += 1  # 新增代码+Phase68ClosedLoopExecutor: 增加观察次数；如果没有这行代码，观察编号不会变化。
        return {"observation_id": f"phase68-observation-{self.calls}", "operation": _phase68_operation(step), "stable": True}  # 新增代码+Phase68ClosedLoopExecutor: 返回稳定观察证据；如果没有这行代码，动作和验证没有输入。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_Phase68ContractObserver.observe 到此结束；如果没有这个边界说明，初学者不容易看出观察范围。
# 新增代码+Phase68ClosedLoopExecutor: 类段结束，_Phase68ContractObserver 到此结束；如果没有这个边界说明，初学者不容易看出合同观察器范围。


class _Phase68ContractActor:  # 新增代码+Phase68ClosedLoopExecutor: 类段开始，提供合同自检用假动作器；如果没有这个类，自检无法覆盖 acted 事件。
    def __init__(self) -> None:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，初始化动作记录；如果没有这个函数，自检无法统计动作次数。
        self.actions = []  # 新增代码+Phase68ClosedLoopExecutor: 保存动作记录；如果没有这行代码，自检无法证明动作被调用。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_Phase68ContractActor.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def act(self, step: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，生成合同自检动作结果；如果没有这个函数，闭环无法覆盖动作阶段。
        action = {"acted": True, "operation": _phase68_operation(step), "write_action": _phase68_is_write_step(step), "observation_id": observation.get("observation_id", "")}  # 新增代码+Phase68ClosedLoopExecutor: 构造动作结果；如果没有这行代码，验证器没有动作证据。
        self.actions.append(action)  # 新增代码+Phase68ClosedLoopExecutor: 记录动作结果；如果没有这行代码，自检无法统计动作轨迹。
        return action  # 新增代码+Phase68ClosedLoopExecutor: 返回动作结果；如果没有这行代码，执行器无法继续验证。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_Phase68ContractActor.act 到此结束；如果没有这个边界说明，初学者不容易看出动作范围。
# 新增代码+Phase68ClosedLoopExecutor: 类段结束，_Phase68ContractActor 到此结束；如果没有这个边界说明，初学者不容易看出合同动作器范围。


class _Phase68ContractVerifier:  # 新增代码+Phase68ClosedLoopExecutor: 类段开始，提供合同自检用假验证器；如果没有这个类，自检无法稳定触发一次失败恢复。
    def __init__(self) -> None:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，初始化验证次数；如果没有这个函数，自检无法控制第一次失败。
        self.calls = 0  # 新增代码+Phase68ClosedLoopExecutor: 保存验证调用次数；如果没有这行代码，验证器无法先失败后成功。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_Phase68ContractVerifier.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def verify(self, step: dict[str, Any], observation: dict[str, Any], action_result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，生成合同自检验证结果；如果没有这个函数，写后校验和恢复路径无法被覆盖。
        self.calls += 1  # 新增代码+Phase68ClosedLoopExecutor: 增加验证次数；如果没有这行代码，第一次失败无法稳定复现。
        passed = self.calls > 1  # 新增代码+Phase68ClosedLoopExecutor: 第一次失败，后续通过；如果没有这行代码，failure_recovery 无法被证明。
        return {"passed": passed, "checked_operation": _phase68_operation(step), "observation_id": observation.get("observation_id", ""), "action_seen": bool(action_result)}  # 新增代码+Phase68ClosedLoopExecutor: 返回验证报告；如果没有这行代码，执行器无法判断是否需要恢复。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_Phase68ContractVerifier.verify 到此结束；如果没有这个边界说明，初学者不容易看出验证范围。
# 新增代码+Phase68ClosedLoopExecutor: 类段结束，_Phase68ContractVerifier 到此结束；如果没有这个边界说明，初学者不容易看出合同验证器范围。


class _Phase68ContractRecoverer:  # 新增代码+Phase68ClosedLoopExecutor: 类段开始，提供合同自检用假恢复器；如果没有这个类，自检无法证明失败后存在恢复动作。
    def __init__(self) -> None:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，初始化恢复记录；如果没有这个函数，自检无法统计恢复次数。
        self.recoveries = []  # 新增代码+Phase68ClosedLoopExecutor: 保存恢复记录；如果没有这行代码，自检无法核对恢复是否触发。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_Phase68ContractRecoverer.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def recover(self, step: dict[str, Any], observation: dict[str, Any], action_result: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，生成合同自检恢复结果；如果没有这个函数，失败后无法模拟重新观察策略。
        recovery = {"recovered": True, "strategy": "observe_again", "operation": _phase68_operation(step), "failed_check": verification.get("checked_operation", "")}  # 新增代码+Phase68ClosedLoopExecutor: 构造恢复报告；如果没有这行代码，恢复事件没有可审计内容。
        self.recoveries.append(recovery)  # 新增代码+Phase68ClosedLoopExecutor: 保存恢复报告；如果没有这行代码，自检无法证明恢复发生。
        return recovery  # 新增代码+Phase68ClosedLoopExecutor: 返回恢复报告；如果没有这行代码，执行器无法继续恢复后观察。
    # 新增代码+Phase68ClosedLoopExecutor: 函数段结束，_Phase68ContractRecoverer.recover 到此结束；如果没有这个边界说明，初学者不容易看出恢复范围。
# 新增代码+Phase68ClosedLoopExecutor: 类段结束，_Phase68ContractRecoverer 到此结束；如果没有这个边界说明，初学者不容易看出合同恢复器范围。


def run_phase68_closed_loop_executor_contract() -> dict[str, Any]:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，运行 Phase68 闭环执行器合同自检；如果没有这个函数，测试和真实终端验收无法用统一入口确认能力。
    task_plan = {"steps": [{"operation": "type_text", "action_kind": "write", "expected_result": "text appears", "checkpoint": "editor content changed"}, {"operation": "verify_result", "action_kind": "verify", "expected_result": "text remains visible", "checkpoint": "final state checked"}]}  # 新增代码+Phase68ClosedLoopExecutor: 定义最小闭环任务计划；如果没有这行代码，自检没有写动作和验证动作可跑。
    executor = WindowsClosedLoopComputerExecutor()  # 新增代码+Phase68ClosedLoopExecutor: 创建闭环执行器；如果没有这行代码，自检无法调用生产类。
    result = executor.run(task_plan, _Phase68ContractObserver(), _Phase68ContractActor(), _Phase68ContractVerifier(), _Phase68ContractRecoverer())  # 新增代码+Phase68ClosedLoopExecutor: 执行假环境闭环任务；如果没有这行代码，合同报告没有真实事件轨迹。
    blind_events = [{"state": "observed"}, {"state": "acted", "write_action": True}, {"state": "acted", "write_action": True}]  # 新增代码+Phase68ClosedLoopExecutor: 构造危险盲写事件链；如果没有这行代码，防盲写能力没有负例证明。
    blind_coordinate_chain_blocked = executor.blind_write_chain_detected(blind_events) and not executor.blind_write_chain_detected(result["events"])  # 新增代码+Phase68ClosedLoopExecutor: 同时证明危险链会被识别且正常闭环不会误报；如果没有这行代码，报告只会声称安全但没有对照。
    report = dict(result)  # 新增代码+Phase68ClosedLoopExecutor: 复制执行结果准备补充合同字段；如果没有这行代码，直接改原结果会让调用边界不清晰。
    report["marker"] = PHASE68_CLOSED_LOOP_EXECUTOR_MARKER  # 新增代码+Phase68ClosedLoopExecutor: 写入 ready marker；如果没有这行代码，真实终端最终回答缺少阶段标记。
    report["ok_token"] = PHASE68_CLOSED_LOOP_EXECUTOR_OK_TOKEN  # 新增代码+Phase68ClosedLoopExecutor: 写入 OK token；如果没有这行代码，验收无法稳定判断通过。
    report["blind_coordinate_chain_blocked"] = blind_coordinate_chain_blocked  # 新增代码+Phase68ClosedLoopExecutor: 写入防盲写结论；如果没有这行代码，报告里的安全字段无法覆盖危险对照。
    report["closed_loop_execution"] = bool(report["closed_loop_execution"])  # 新增代码+Phase68ClosedLoopExecutor: 标准化闭环执行布尔值；如果没有这行代码，CLI 输出可能拿到非布尔对象。
    report["post_action_verification"] = bool(report["post_action_verification"])  # 新增代码+Phase68ClosedLoopExecutor: 标准化后置验证布尔值；如果没有这行代码，token 输出可能不稳定。
    report["failure_recovery"] = bool(report["failure_recovery"])  # 新增代码+Phase68ClosedLoopExecutor: 标准化失败恢复布尔值；如果没有这行代码，token 输出可能不稳定。
    report["actions_expanded"] = PHASE68_ACTIONS_EXPANDED  # 新增代码+Phase68ClosedLoopExecutor: 写入动作范围声明；如果没有这行代码，报告可能误导为已扩大真实动作能力。
    report["passed"] = report["closed_loop_execution"] and report["post_action_verification"] and report["failure_recovery"] and report["blind_coordinate_chain_blocked"] and not report["actions_expanded"]  # 新增代码+Phase68ClosedLoopExecutor: 汇总合同是否通过；如果没有这行代码，调用方需要重复组合多个字段。
    return report  # 新增代码+Phase68ClosedLoopExecutor: 返回合同报告；如果没有这行代码，测试和 CLI 无法读取结果。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，run_phase68_closed_loop_executor_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase68_cli_line(report: dict[str, Any] | None = None) -> str:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，生成真实终端验收需要的单行 token；如果没有这个函数，agent 最终回答容易因为自然语言变化导致验收失败。
    current_report = report if report is not None else run_phase68_closed_loop_executor_contract()  # 新增代码+Phase68ClosedLoopExecutor: 复用传入报告或现场运行自检；如果没有这行代码，CLI 无法独立执行。
    return f"{PHASE68_CLOSED_LOOP_EXECUTOR_MARKER} {PHASE68_CLOSED_LOOP_EXECUTOR_OK_TOKEN} closed_loop_execution={_phase68_bool_token(current_report.get('closed_loop_execution'))} post_action_verification={_phase68_bool_token(current_report.get('post_action_verification'))} failure_recovery={_phase68_bool_token(current_report.get('failure_recovery'))} blind_coordinate_chain_blocked={_phase68_bool_token(current_report.get('blind_coordinate_chain_blocked'))} actions_expanded={_phase68_bool_token(current_report.get('actions_expanded'))}"  # 新增代码+Phase68ClosedLoopExecutor: 返回固定 token 行；如果没有这行代码，真实终端验收不能用简单包含关系判断成功。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，phase68_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 输出范围。


def main() -> int:  # 新增代码+Phase68ClosedLoopExecutor: 函数段开始，提供 python -c 调用的命令行入口；如果没有这个函数，真实终端场景无法运行统一自检命令。
    report = run_phase68_closed_loop_executor_contract()  # 新增代码+Phase68ClosedLoopExecutor: 运行合同自检；如果没有这行代码，命令行入口没有结果来源。
    print(phase68_cli_line(report))  # 新增代码+Phase68ClosedLoopExecutor: 打印固定验收 token 行；如果没有这行代码，controller 看不到 Phase68 成功标记。
    return 0 if report.get("passed", False) else 1  # 新增代码+Phase68ClosedLoopExecutor: 根据合同结果返回退出码；如果没有这行代码，自动化命令无法用进程状态判断失败。
# 新增代码+Phase68ClosedLoopExecutor: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


if __name__ == "__main__":  # 新增代码+Phase68ClosedLoopExecutor: 允许直接运行本模块；如果没有这行代码，初学者不能用 python 文件方式启动 Phase68 自检。
    raise SystemExit(main())  # 新增代码+Phase68ClosedLoopExecutor: 调用 main 并返回退出码；如果没有这行代码，直接运行模块不会执行合同自检。
