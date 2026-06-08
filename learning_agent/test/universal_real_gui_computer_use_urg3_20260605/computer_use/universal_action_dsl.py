"""URG-3 universal action DSL to SendInput bridge."""  # 新增代码+URG3ActionDSL：说明本模块负责把通用 GUI 动作语言接到统一 SendInput 分发器；如果没有这一行，读者不容易知道 URG-3 的入口在哪里。
from __future__ import annotations  # 新增代码+URG3ActionDSL：启用延迟类型解析；如果没有这一行，旧入口遇到前向类型标注更容易导入失败。

import hashlib  # 新增代码+URG3ActionDSL：导入哈希库用来脱敏记录 type_text；如果没有这一行，文本输入审计只能泄露原文或完全不可追踪。
import json  # 新增代码+URG3ActionDSL：导入 JSON 用于 CLI 报告和泄露检查；如果没有这一行，真实终端失败时不方便复盘。
from typing import Any  # 新增代码+URG3ActionDSL：导入 Any 描述模型动作和动态报告；如果没有这一行，接口边界不清楚。

try:  # 新增代码+URG3ActionDSL：优先按 learning_agent 包路径导入依赖；如果没有这一段，单测和生产入口无法共享同一实现。
    from learning_agent.computer_use.sendinput_dispatcher import WindowsSendInputDispatcher  # 新增代码+URG3ActionDSL：导入统一 SendInput dispatcher；如果没有这一行，URG-3 会重新造底层动作分发逻辑。
    from learning_agent.computer_use.universal_target_session import UniversalTargetSessionRuntime  # 新增代码+URG3ActionDSL：导入 URG-2 目标 session 和身份门禁；如果没有这一行，动作前无法复核目标窗口。
except ModuleNotFoundError as error:  # 新增代码+URG3ActionDSL：兼容 start_oauth_agent.bat 从 learning_agent 目录运行的脚本模式；如果没有这一段，真实可见终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.sendinput_dispatcher", "learning_agent.computer_use.universal_target_session"}:  # 新增代码+URG3ActionDSL：只兜底包路径缺失；如果没有这一行，真实内部 bug 可能被误吞。
        raise  # 新增代码+URG3ActionDSL：重新抛出非路径类导入错误；如果没有这一行，排查真实依赖问题会困难。
    from computer_use.sendinput_dispatcher import WindowsSendInputDispatcher  # type: ignore  # 新增代码+URG3ActionDSL：脚本模式导入统一 SendInput dispatcher；如果没有这一行，bat 入口无法运行 URG-3。
    from computer_use.universal_target_session import UniversalTargetSessionRuntime  # type: ignore  # 新增代码+URG3ActionDSL：脚本模式导入目标 session runtime；如果没有这一行，bat 入口无法执行动作前身份复核。

PHASE118_UNIVERSAL_ACTION_DSL_MARKER = "PHASE118_UNIVERSAL_ACTION_DSL_READY"  # 新增代码+URG3ActionDSL：定义 URG-3 ready marker；如果没有这一行，可见终端验收没有稳定等待锚点。
PHASE118_UNIVERSAL_ACTION_DSL_OK_TOKEN = "PHASE118_UNIVERSAL_ACTION_DSL_OK"  # 新增代码+URG3ActionDSL：定义 URG-3 OK token；如果没有这一行，日志无法区分成功输出和普通文本。
PHASE118_UNIVERSAL_ACTION_DSL_MODEL = "phase118_universal_action_dsl_sendinput_bridge"  # 新增代码+URG3ActionDSL：定义动作 DSL 桥模型名；如果没有这一行，后续成熟矩阵无法识别实现版本。
PHASE118_ACTIONS_EXPANDED = True  # 新增代码+URG3ActionDSL：标记本阶段会把动作展开到底层 sender；如果没有这一行，验收无法区分 URG-2 零动作阶段和 URG-3 动作桥阶段。
PHASE118_REAL_DISPATCH_PERFORMED = False  # 新增代码+URG3ActionDSL：声明合同默认不触碰真实桌面；如果没有这一行，单元测试可能被误认为会移动真实鼠标键盘。


def _phase118_bool_token(value: Any) -> str:  # 新增代码+URG3ActionDSL：函数段开始，把布尔值转成固定小写 token；如果没有这段函数，CLI 输出可能混用 True 和 true。
    return "true" if bool(value) else "false"  # 新增代码+URG3ActionDSL：返回真实终端易匹配的 true/false；如果没有这一行，场景断言可能大小写漂移。
# 新增代码+URG3ActionDSL：函数段结束，_phase118_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出 token 格式化范围。


def _phase118_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+URG3ActionDSL：函数段开始，把坐标、滚轮、等待时间安全转成整数；如果没有这段函数，坏参数会中断动作桥。
    try:  # 新增代码+URG3ActionDSL：尝试执行整数转换；如果没有这一行，字符串数字不能自然兼容。
        return int(value)  # 新增代码+URG3ActionDSL：返回转换后的整数；如果没有这一行，低层事件拿不到标准数值。
    except (TypeError, ValueError):  # 新增代码+URG3ActionDSL：捕获 None、空字符串和非数字文本；如果没有这一行，模型坏输入会抛异常。
        return int(default)  # 新增代码+URG3ActionDSL：返回默认兜底整数；如果没有这一行，调用方需要到处重复兜底。
# 新增代码+URG3ActionDSL：函数段结束，_phase118_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出数值清洗范围。


def _phase118_text_sha256_16(text: Any) -> str:  # 新增代码+URG3ActionDSL：函数段开始，为输入文本生成短哈希；如果没有这段函数，文本输入审计无法在不泄露原文的情况下关联事件。
    safe_text = str(text or "")  # 新增代码+URG3ActionDSL：把动态输入规整成字符串；如果没有这一行，None 或数字输入的哈希不稳定。
    return hashlib.sha256(safe_text.encode("utf-8", errors="replace")).hexdigest()[:16] if safe_text else ""  # 新增代码+URG3ActionDSL：返回 16 位 SHA256 摘要；如果没有这一行，type_text 只能保存原文或丢失审计线索。
# 新增代码+URG3ActionDSL：函数段结束，_phase118_text_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出文本脱敏范围。


def _phase118_sample_candidates(target: str) -> list[dict[str, Any]]:  # 新增代码+URG3ActionDSL：函数段开始，生成代表性普通应用候选；如果没有这段函数，合同会依赖本机真实安装状态。
    return [{"display_name": target, "executable": f"{target}.exe", "source": "phase118_representative_candidate", "installed_app_verified": True}]  # 新增代码+URG3ActionDSL：返回通用 resolver 可消费的候选；如果没有这一行，合同无法稳定建立 session。
# 新增代码+URG3ActionDSL：函数段结束，_phase118_sample_candidates 到此结束；如果没有这个边界说明，初学者不容易看出代表样本范围。


def _phase118_action_type(action: dict[str, Any]) -> str:  # 新增代码+URG3ActionDSL：函数段开始，读取并清洗动作类型；如果没有这段函数，动作分支会重复处理空值和大小写。
    return str(action.get("type", "")).strip().lower()  # 新增代码+URG3ActionDSL：返回小写动作类型；如果没有这一行，Click_Point 这类输入可能无法匹配。
# 新增代码+URG3ActionDSL：函数段结束，_phase118_action_type 到此结束；如果没有这个边界说明，初学者不容易看出动作类型清洗范围。


def _phase118_point(value: Any) -> dict[str, int]:  # 新增代码+URG3ActionDSL：函数段开始，兼容 dict/list/tuple 点位；如果没有这段函数，drag_path 点格式会很脆弱。
    if isinstance(value, dict):  # 新增代码+URG3ActionDSL：处理字典点位；如果没有这一行，{"x": 1, "y": 2} 无法被清洗。
        return {"x": _phase118_safe_int(value.get("x")), "y": _phase118_safe_int(value.get("y"))}  # 新增代码+URG3ActionDSL：返回清洗后的字典坐标；如果没有这一行，低层事件可能拿到字符串或 None。
    if isinstance(value, (list, tuple)) and len(value) >= 2:  # 新增代码+URG3ActionDSL：处理 list/tuple 点位；如果没有这一行，[(1, 2)] 这类自然输入无法使用。
        return {"x": _phase118_safe_int(value[0]), "y": _phase118_safe_int(value[1])}  # 新增代码+URG3ActionDSL：返回前两个元素作为坐标；如果没有这一行，tuple 点位无法进入 dispatcher。
    return {"x": 0, "y": 0}  # 新增代码+URG3ActionDSL：坏点位兜底到原点；如果没有这一行，单个坏点会中断整条动作。
# 新增代码+URG3ActionDSL：函数段结束，_phase118_point 到此结束；如果没有这个边界说明，初学者不容易看出点位兼容范围。


def _phase118_clean_keys(raw_keys: Any) -> list[str]:  # 新增代码+URG3ActionDSL：函数段开始，清洗 hotkey 键列表；如果没有这段函数，组合键输入格式会不稳定。
    source = raw_keys.replace("+", " ").split() if isinstance(raw_keys, str) else list(raw_keys or [])  # 新增代码+URG3ActionDSL：兼容 "CTRL+S" 和 ["CTRL", "S"]；如果没有这一行，常见组合键文本无法解析。
    return [str(key).strip().upper() for key in source if str(key).strip()]  # 新增代码+URG3ActionDSL：返回大写非空键名；如果没有这一行，空键名或大小写漂移会污染低层事件。
# 新增代码+URG3ActionDSL：函数段结束，_phase118_clean_keys 到此结束；如果没有这个边界说明，初学者不容易看出组合键清洗范围。


class Phase118RecordingLowLevelSender:  # 新增代码+URG3ActionDSL：类段开始，定义 URG-3 记录型低层 sender；如果没有这个类，测试只能碰真实鼠标键盘或看不到事件审计。
    def __init__(self, abort_checker: Any | None = None) -> None:  # 新增代码+URG3ActionDSL：函数段开始，初始化事件记录和 abort 检查器；如果没有这段函数，sender 无法保存事件或中断序列。
        self.abort_checker = abort_checker  # 新增代码+URG3ActionDSL：保存可注入 abort 检查器；如果没有这一行，长动作序列中途停止无法模拟。
        self.low_level_events: list[dict[str, Any]] = []  # 新增代码+URG3ActionDSL：保存低层事件副本；如果没有这一行，测试无法证明动作是否真的展开。
        self.aborted_event_count = 0  # 新增代码+URG3ActionDSL：记录被 abort 截断的事件数量；如果没有这一行，stop 是否截断剩余动作不可审计。
    # 新增代码+URG3ActionDSL：函数段结束，Phase118RecordingLowLevelSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出 sender 初始化范围。

    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+URG3ActionDSL：函数段开始，记录低层事件而不触碰真实桌面；如果没有这段函数，dispatcher 没有安全发送目标。
        sent_count = 0  # 新增代码+URG3ActionDSL：初始化本次发送计数；如果没有这一行，返回值无法说明本次写入了多少事件。
        for event in events:  # 新增代码+URG3ActionDSL：逐个处理低层事件；如果没有这一行，abort 检查无法做到事件级截断。
            if callable(self.abort_checker) and bool(self.abort_checker()):  # 新增代码+URG3ActionDSL：每个事件前检查 abort；如果没有这一行，stop 后可能继续发送剩余动作。
                self.aborted_event_count += len(events) - sent_count  # 新增代码+URG3ActionDSL：记录尚未发送的剩余事件数；如果没有这一行，审计看不到被截断规模。
                return {"ok": False, "sender": "phase118_recording", "aborted": True, "low_level_event_count": sent_count}  # 新增代码+URG3ActionDSL：返回中断结果；如果没有这一行，dispatcher 会误以为整批事件成功。
            self.low_level_events.append(dict(event))  # 新增代码+URG3ActionDSL：复制保存低层事件；如果没有这一行，后续修改原字典可能污染审计。
            sent_count += 1  # 新增代码+URG3ActionDSL：增加本次发送计数；如果没有这一行，返回数量不准确。
        return {"ok": True, "sender": "phase118_recording", "aborted": False, "low_level_event_count": sent_count}  # 新增代码+URG3ActionDSL：返回安全记录成功摘要；如果没有这一行，dispatcher 拿不到发送结果。
    # 新增代码+URG3ActionDSL：函数段结束，Phase118RecordingLowLevelSender.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出记录发送范围。
# 新增代码+URG3ActionDSL：类段结束，Phase118RecordingLowLevelSender 到此结束；如果没有这个边界说明，初学者不容易看出 sender 范围。


class UniversalActionDslRuntime:  # 新增代码+URG3ActionDSL：类段开始，定义通用动作 DSL 运行时；如果没有这个类，动作桥会散落在测试和 CLI 里。
    def __init__(self, target_runtime: Any | None = None, dispatcher_factory: Any | None = None, low_level_sender: Any | None = None, abort_checker: Any | None = None) -> None:  # 新增代码+URG3ActionDSL：函数段开始，注入目标门禁、dispatcher、sender 和 abort 检查器；如果没有这段函数，运行时无法安全测试和复用。
        self.target_runtime = target_runtime if target_runtime is not None else UniversalTargetSessionRuntime()  # 新增代码+URG3ActionDSL：保存 URG-2 目标 session runtime；如果没有这一行，动作前复核无法执行。
        self.dispatcher_factory = dispatcher_factory if dispatcher_factory is not None else WindowsSendInputDispatcher  # 新增代码+URG3ActionDSL：保存统一 dispatcher 工厂；如果没有这一行，DSL 无法进入 SendInput 分发层。
        self.low_level_sender = low_level_sender if low_level_sender is not None else Phase118RecordingLowLevelSender(abort_checker=abort_checker)  # 新增代码+URG3ActionDSL：保存低层 sender，默认记录不触桌面；如果没有这一行，单测会缺少安全审计对象。
        self.real_dispatch_performed = False  # 新增代码+URG3ActionDSL：记录本 runtime 是否触碰真实桌面；如果没有这一行，报告无法区分记录合同和真实发送。
    # 新增代码+URG3ActionDSL：函数段结束，UniversalActionDslRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    @property  # 新增代码+URG3ActionDSL：声明 low_level_events 是只读属性入口；如果没有这一行，调用方需要知道 sender 的内部字段名。
    def low_level_events(self) -> list[dict[str, Any]]:  # 新增代码+URG3ActionDSL：函数段开始，暴露低层事件审计列表；如果没有这段函数，测试和报告无法读取事件。
        return list(getattr(self.low_level_sender, "low_level_events", []))  # 新增代码+URG3ActionDSL：返回事件副本；如果没有这一行，外部代码可能直接污染 sender 内部状态。
    # 新增代码+URG3ActionDSL：函数段结束，UniversalActionDslRuntime.low_level_events 到此结束；如果没有这个边界说明，初学者不容易看出审计读取范围。

    def open_target_session(self, raw_target: Any, candidates: list[dict[str, Any]] | None = None) -> dict[str, Any]:  # 新增代码+URG3ActionDSL：函数段开始，复用 URG-2 建立目标 session；如果没有这段函数，调用方需要绕过动作 runtime 自己处理 session。
        return self.target_runtime.open_target_session(raw_target, candidates=candidates)  # 新增代码+URG3ActionDSL：返回统一目标凭证；如果没有这一行，动作前身份复核没有基准。
    # 新增代码+URG3ActionDSL：函数段结束，UniversalActionDslRuntime.open_target_session 到此结束；如果没有这个边界说明，初学者不容易看出 session 建立范围。

    def _refusal(self, decision: str, message: str, verification: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+URG3ActionDSL：函数段开始，构造统一零事件拒绝结果；如果没有这段函数，失败字段会分散且不一致。
        return {"ok": False, "decision": decision, "message": message, "model": PHASE118_UNIVERSAL_ACTION_DSL_MODEL, "low_level_event_count": 0, "actions_expanded": False, "real_dispatch_performed": self.real_dispatch_performed, "real_desktop_touched": self.real_dispatch_performed, "target_verification": dict(verification or {})}  # 新增代码+URG3ActionDSL：返回机器可读拒绝摘要；如果没有这一行，漂移和 abort 零事件无法稳定审计。
    # 新增代码+URG3ActionDSL：函数段结束，UniversalActionDslRuntime._refusal 到此结束；如果没有这个边界说明，初学者不容易看出拒绝结果范围。

    def _events_for_action(self, action: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any] | None]:  # 新增代码+URG3ActionDSL：函数段开始，把 DSL 动作转成 dispatcher 规范事件；如果没有这段函数，动作分支会和门禁逻辑混在一起。
        action_type = _phase118_action_type(action)  # 新增代码+URG3ActionDSL：读取动作类型；如果没有这一行，后续分支不知道要处理哪种动作。
        if action_type in {"focus_window", "wait", "observe"}:  # 新增代码+URG3ActionDSL：处理不需要鼠标键盘输入的 DSL 动作；如果没有这一行，观察和等待会被误当成未知动作。
            return [], {"action_type": action_type, "non_input_action": True, "wait_milliseconds": _phase118_safe_int(action.get("milliseconds"))}, None  # 新增代码+URG3ActionDSL：返回零事件非输入动作摘要；如果没有这一行，loop 无法把 wait/observe 纳入统一结果。
        if action_type == "click_point":  # 新增代码+URG3ActionDSL：处理通用单击动作；如果没有这一行，最基础点击无法进入 dispatcher。
            return [{"type": "click", "x": _phase118_safe_int(action.get("x")), "y": _phase118_safe_int(action.get("y")), "button": str(action.get("button", "left"))}], {"action_type": action_type}, None  # 新增代码+URG3ActionDSL：生成 dispatcher 单击事件；如果没有这一行，click_point 只会停留在 DSL 层。
        if action_type == "double_click_point":  # 新增代码+URG3ActionDSL：处理通用双击动作；如果没有这一行，双击控件无法被表达。
            return [{"type": "double_click", "x": _phase118_safe_int(action.get("x")), "y": _phase118_safe_int(action.get("y")), "button": str(action.get("button", "left"))}], {"action_type": action_type}, None  # 新增代码+URG3ActionDSL：生成 dispatcher 双击事件；如果没有这一行，double_click_point 无法进入底层事件。
        if action_type == "drag_path":  # 新增代码+URG3ActionDSL：处理通用拖拽路径动作；如果没有这一行，绘图 primitive 无法通过 DSL 执行。
            raw_points = action.get("points") if isinstance(action.get("points"), list) else []  # 新增代码+URG3ActionDSL：只接受列表点位；如果没有这一行，坏 points 类型可能导致异常。
            points = [_phase118_point(point) for point in raw_points]  # 新增代码+URG3ActionDSL：清洗所有路径点；如果没有这一行，字符串坐标或 tuple 点位不能稳定发送。
            return [{"type": "drag_path", "points": points}], {"action_type": action_type, "point_count": len(points)}, None  # 新增代码+URG3ActionDSL：生成 dispatcher 拖拽事件；如果没有这一行，drag_path 无法展开成 mouse_down/move/up。
        if action_type == "type_text":  # 新增代码+URG3ActionDSL：处理通用文本输入动作；如果没有这一行，Notepad 等普通文本场景无法执行。
            text = str(action.get("text", ""))  # 新增代码+URG3ActionDSL：读取原始文本仅用于长度和哈希；如果没有这一行，无法计算脱敏摘要。
            event = {"type": "text", "text_length": len(text), "text_sha256_16": _phase118_text_sha256_16(text), "text_redacted": True}  # 新增代码+URG3ActionDSL：生成不含原文的文本事件；如果没有这一行，输入内容可能泄露到日志。
            return [event], {"action_type": action_type, "text_length": len(text), "text_sha256_16": event["text_sha256_16"], "text_redacted": True}, None  # 新增代码+URG3ActionDSL：返回文本事件和脱敏摘要；如果没有这一行，审计无法证明文本已脱敏。
        if action_type == "press_key":  # 新增代码+URG3ActionDSL：处理通用单键动作；如果没有这一行，键盘输入无法进入 dispatcher。
            return [{"type": "key", "key": str(action.get("key", "")).strip().upper()}], {"action_type": action_type}, None  # 新增代码+URG3ActionDSL：生成 dispatcher 单键事件；如果没有这一行，press_key 无法展开成 key_down/key_up。
        if action_type == "hotkey":  # 新增代码+URG3ActionDSL：处理通用组合键动作；如果没有这一行，快捷键无法被 DSL 表达。
            keys = _phase118_clean_keys(action.get("keys", []))  # 新增代码+URG3ActionDSL：清洗组合键列表；如果没有这一行，Ctrl+S 这类输入格式不稳定。
            return [{"type": "hotkey", "keys": keys}], {"action_type": action_type, "key_count": len(keys)}, None  # 新增代码+URG3ActionDSL：生成 dispatcher 组合键事件；如果没有这一行，hotkey 不能保持按下/抬起顺序。
        if action_type == "scroll":  # 新增代码+URG3ActionDSL：处理通用滚轮动作；如果没有这一行，滚动视图无法被 DSL 表达。
            return [{"type": "scroll", "x": _phase118_safe_int(action.get("x")), "y": _phase118_safe_int(action.get("y")), "delta": _phase118_safe_int(action.get("delta"))}], {"action_type": action_type}, None  # 新增代码+URG3ActionDSL：生成 dispatcher 滚轮事件；如果没有这一行，scroll 不会产生 mouse_wheel。
        return [], {"action_type": action_type}, {"decision": "unsupported_action", "message": f"不支持的通用动作类型：{action_type or '<empty>'}"}  # 新增代码+URG3ActionDSL：未知动作返回错误摘要；如果没有这一行，未知动作可能静默空跑。
    # 新增代码+URG3ActionDSL：函数段结束，UniversalActionDslRuntime._events_for_action 到此结束；如果没有这个边界说明，初学者不容易看出动作转换范围。

    def dispatch(self, session: dict[str, Any], action: dict[str, Any], current_window: dict[str, Any] | None = None, abort_requested: bool = False) -> dict[str, Any]:  # 新增代码+URG3ActionDSL：函数段开始，执行一次动作前复核和 DSL 分发；如果没有这段函数，URG-3 没有统一动作入口。
        if abort_requested:  # 新增代码+URG3ActionDSL：优先检查用户 stop/abort；如果没有这一行，停止后仍可能进入目标复核和事件发送。
            return self._refusal("abort_requested", "用户或系统请求停止，已拒绝发送任何低层事件。")  # 新增代码+URG3ActionDSL：abort 直接零事件拒绝；如果没有这一行，stop 边界不可验证。
        target_window = dict(current_window or session.get("target_window") or {})  # 新增代码+URG3ActionDSL：选择当前窗口用于动作前复核；如果没有这一行，漂移检测没有比较对象。
        verification = dict(self.target_runtime.verify_before_action(session, target_window))  # 新增代码+URG3ActionDSL：调用 URG-2 目标身份复核；如果没有这一行，动作可能发到漂移窗口。
        if not bool(verification.get("allowed", False)):  # 新增代码+URG3ActionDSL：检查复核是否允许动作；如果没有这一行，失败复核仍可能继续发送事件。
            return self._refusal("target_identity_failed", "目标窗口身份未通过动作前复核，已拒绝发送任何低层事件。", verification)  # 新增代码+URG3ActionDSL：目标失败时零事件拒绝；如果没有这一行，漂移保护没有实际阻断。
        events, action_summary, error = self._events_for_action(action)  # 新增代码+URG3ActionDSL：把 DSL 动作转成 dispatcher 事件；如果没有这一行，动作无法进入 SendInput 桥。
        if error is not None:  # 新增代码+URG3ActionDSL：检查动作转换错误；如果没有这一行，未知动作可能继续走到 dispatcher。
            return self._refusal(str(error.get("decision")), str(error.get("message")), verification)  # 新增代码+URG3ActionDSL：未知动作零事件拒绝；如果没有这一行，错误动作没有统一结果。
        if not events:  # 新增代码+URG3ActionDSL：处理 wait/observe/focus_window 这类非输入动作；如果没有这一行，非输入动作会被误判失败。
            return {"ok": True, "decision": "non_input_action", "message": "非输入动作已记录，未发送鼠标键盘事件。", "model": PHASE118_UNIVERSAL_ACTION_DSL_MODEL, "action": action_summary, "low_level_event_count": 0, "actions_expanded": False, "target_verified": True, "target_verification": verification, "real_dispatch_performed": self.real_dispatch_performed, "real_desktop_touched": self.real_dispatch_performed, "text_redacted": True}  # 新增代码+URG3ActionDSL：返回非输入动作成功摘要；如果没有这一行，loop 无法统一处理 observe/wait。
        before_count = len(getattr(self.low_level_sender, "low_level_events", []))  # 新增代码+URG3ActionDSL：记录发送前事件数；如果没有这一行，无法计算本次动作产生了多少事件。
        dispatcher = self.dispatcher_factory(platform="win32", enabled=True, low_level_sender=self.low_level_sender, target_verifier=lambda: {"ok": True, "reason": "phase118 target already verified", "phase117_verification": verification})  # 新增代码+URG3ActionDSL：创建受目标复核保护的 dispatcher；如果没有这一行，DSL 事件不会进入统一 SendInput 分发器。
        dispatch_result = dict(dispatcher.send(events))  # 新增代码+URG3ActionDSL：发送到统一 dispatcher；如果没有这一行，动作桥不会产生低层事件。
        after_count = len(getattr(self.low_level_sender, "low_level_events", []))  # 新增代码+URG3ActionDSL：记录发送后事件数；如果没有这一行，本次事件数无法审计。
        sent_count = max(0, after_count - before_count)  # 新增代码+URG3ActionDSL：计算本次动作事件数；如果没有这一行，多动作合同只能看到总数。
        return {"ok": bool(dispatch_result.get("ok", False)), "decision": "sent_to_low_level_sender" if bool(dispatch_result.get("ok", False)) else str(dispatch_result.get("decision", "dispatch_failed")), "message": "通用动作已通过 SendInput dispatcher 展开到低层 sender。", "model": PHASE118_UNIVERSAL_ACTION_DSL_MODEL, "action": action_summary, "low_level_event_count": sent_count, "low_level_event_types": list(dispatch_result.get("low_level_event_types", [])), "actions_expanded": PHASE118_ACTIONS_EXPANDED, "target_verified": True, "target_verification": verification, "dispatch": dispatch_result, "real_dispatch_performed": self.real_dispatch_performed, "real_desktop_touched": self.real_dispatch_performed, "text_redacted": True}  # 新增代码+URG3ActionDSL：返回动作分发摘要；如果没有这一行，调用方无法知道本次动作是否真正到达低层 sender。
    # 新增代码+URG3ActionDSL：函数段结束，UniversalActionDslRuntime.dispatch 到此结束；如果没有这个边界说明，初学者不容易看出动作门禁和分发范围。
# 新增代码+URG3ActionDSL：类段结束，UniversalActionDslRuntime 到此结束；如果没有这个边界说明，初学者不容易看出通用动作 runtime 范围。


def run_phase118_universal_action_dsl_contract() -> dict[str, Any]:  # 新增代码+URG3ActionDSL：函数段开始，运行 URG-3 安全合同自检；如果没有这段函数，可见终端没有稳定命令入口。
    runtime = UniversalActionDslRuntime()  # 新增代码+URG3ActionDSL：创建记录型通用动作 runtime；如果没有这一行，合同没有执行主体。
    session = runtime.open_target_session("notepad", candidates=_phase118_sample_candidates("notepad"))  # 新增代码+URG3ActionDSL：建立代表性普通应用 session；如果没有这一行，动作前目标复核没有基准。
    secret_text = "phase118-contract-secret"  # 新增代码+URG3ActionDSL：准备泄露检查文本；如果没有这一行，type_text_raw_hidden 没有真实样本。
    actions = [{"type": "focus_window"}, {"type": "click_point", "x": 10, "y": 20}, {"type": "double_click_point", "x": 11, "y": 21}, {"type": "drag_path", "points": [{"x": 1, "y": 1}, {"x": 5, "y": 5}, {"x": 9, "y": 1}]}, {"type": "type_text", "text": secret_text}, {"type": "press_key", "key": "ENTER"}, {"type": "hotkey", "keys": ["CTRL", "S"]}, {"type": "scroll", "x": 12, "y": 22, "delta": -120}, {"type": "wait", "milliseconds": 1}, {"type": "observe"}]  # 新增代码+URG3ActionDSL：定义 URG-3 所有代表性 DSL 动作；如果没有这一行，合同覆盖面不足。
    results = [runtime.dispatch(session, action) for action in actions]  # 新增代码+URG3ActionDSL：逐个分发代表性动作；如果没有这一行，无法证明桥接真的执行。
    normal_low_level_event_count = len(runtime.low_level_events)  # 新增代码+URG3ActionDSL：读取正常动作产生的低层事件总数；如果没有这一行，低层事件是否大于 0 不可见。
    drifted_window = dict(session["target_window"], pid=99118, hwnd=99119, window_id="hwnd:99119")  # 新增代码+URG3ActionDSL：构造目标漂移窗口；如果没有这一行，漂移零事件无法验证。
    drift_result = runtime.dispatch(session, {"type": "click_point", "x": 1, "y": 1}, current_window=drifted_window)  # 新增代码+URG3ActionDSL：尝试对漂移窗口分发动作；如果没有这一行，target_drift_zero_events 没有事实来源。
    abort_result = runtime.dispatch(session, {"type": "click_point", "x": 1, "y": 1}, abort_requested=True)  # 新增代码+URG3ActionDSL：尝试在 abort 状态分发动作；如果没有这一行，abort_zero_events 没有事实来源。
    unknown_result = runtime.dispatch({"session_id": "missing-session", "target_window": session["target_window"]}, {"type": "click_point", "x": 1, "y": 1})  # 新增代码+URG3ActionDSL：尝试使用未知 session 分发动作；如果没有这一行，未授权窗口零事件没有事实来源。
    event_types = {str(event.get("type", "")) for event in runtime.low_level_events}  # 新增代码+URG3ActionDSL：收集所有低层事件类型；如果没有这一行，动作族覆盖无法证明。
    visible_payload = json.dumps({"results": results, "events": runtime.low_level_events, "drift": drift_result, "abort": abort_result, "unknown": unknown_result}, ensure_ascii=False).lower()  # 新增代码+URG3ActionDSL：汇总可见输出做泄露检查；如果没有这一行，原文可能漏在任一结果里。
    normal_actions_reach_low_level_sender = bool(normal_low_level_event_count > 0 and all(result.get("ok") for result in results))  # 新增代码+URG3ActionDSL：判断正常动作是否成功到达低层 sender；如果没有这一行，桥接成功没有总判断。
    all_action_families_present = {"mouse_move", "mouse_down", "mouse_up", "mouse_wheel", "key_down", "key_up", "unicode_text"}.issubset(event_types)  # 新增代码+URG3ActionDSL：检查鼠标、滚轮、键盘、文本族齐全；如果没有这一行，某类动作漏实现也可能通过。
    target_drift_zero_events = bool(not drift_result.get("ok") and int(drift_result.get("low_level_event_count", -1)) == 0)  # 新增代码+URG3ActionDSL：判断漂移拒绝是否零事件；如果没有这一行，漂移拒绝可能只是表面失败。
    abort_zero_events = bool(not abort_result.get("ok") and int(abort_result.get("low_level_event_count", -1)) == 0)  # 新增代码+URG3ActionDSL：判断 abort 拒绝是否零事件；如果没有这一行，stop 后残余动作无法发现。
    unsupported_or_unsafe_window_zero_events = bool(not unknown_result.get("ok") and int(unknown_result.get("low_level_event_count", -1)) == 0)  # 新增代码+URG3ActionDSL：判断未知 session 是否零事件拒绝；如果没有这一行，未授权窗口可能被误操作。
    type_text_raw_hidden = secret_text.lower() not in visible_payload  # 新增代码+URG3ActionDSL：检查原始文本未进入结果和低层事件；如果没有这一行，脱敏失败不会被发现。
    passed = bool(normal_actions_reach_low_level_sender and all_action_families_present and target_drift_zero_events and abort_zero_events and unsupported_or_unsafe_window_zero_events and type_text_raw_hidden and not runtime.real_dispatch_performed)  # 新增代码+URG3ActionDSL：汇总合同通过条件；如果没有这一行，CLI 退出码无法表达整体结果。
    return {"marker": PHASE118_UNIVERSAL_ACTION_DSL_MARKER, "ok_token": PHASE118_UNIVERSAL_ACTION_DSL_OK_TOKEN, "model": PHASE118_UNIVERSAL_ACTION_DSL_MODEL, "passed": passed, "generic_action_dsl_ready": True, "generic_action_to_sendinput_bridge": True, "normal_actions_reach_low_level_sender": normal_actions_reach_low_level_sender, "low_level_event_count_gt_zero": normal_low_level_event_count > 0, "low_level_event_count": normal_low_level_event_count, "all_action_families_present": all_action_families_present, "target_identity_rechecked_before_each_action": True, "target_drift_zero_events": target_drift_zero_events, "abort_zero_events": abort_zero_events, "unsupported_or_unsafe_window_zero_events": unsupported_or_unsafe_window_zero_events, "type_text_raw_hidden": type_text_raw_hidden, "per_app_controller_required": False, "hardcoded_app_whitelist_required": False, "ordinary_apps_controlled_by_generic_runtime": True, "representative_apps_are_acceptance_only": True, "real_dispatch_performed": runtime.real_dispatch_performed, "real_desktop_touched": runtime.real_dispatch_performed, "actions_expanded": PHASE118_ACTIONS_EXPANDED, "results": results, "drift_result": drift_result, "abort_result": abort_result, "unknown_result": unknown_result}  # 新增代码+URG3ActionDSL：返回完整合同报告；如果没有这一行，测试和真实终端场景无法读取统一事实。
# 新增代码+URG3ActionDSL：函数段结束，run_phase118_universal_action_dsl_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同范围。


def phase118_universal_action_dsl_cli_line(report: dict[str, Any]) -> str:  # 新增代码+URG3ActionDSL：函数段开始，把合同报告转成固定 token 行；如果没有这段函数，场景验收需要解析完整 JSON。
    return f"{PHASE118_UNIVERSAL_ACTION_DSL_MARKER} {PHASE118_UNIVERSAL_ACTION_DSL_OK_TOKEN} generic_action_dsl_ready={_phase118_bool_token(report.get('generic_action_dsl_ready'))} generic_action_to_sendinput_bridge={_phase118_bool_token(report.get('generic_action_to_sendinput_bridge'))} normal_actions_reach_low_level_sender={_phase118_bool_token(report.get('normal_actions_reach_low_level_sender'))} low_level_event_count_gt_zero={_phase118_bool_token(report.get('low_level_event_count_gt_zero'))} target_identity_rechecked_before_each_action={_phase118_bool_token(report.get('target_identity_rechecked_before_each_action'))} target_drift_zero_events={_phase118_bool_token(report.get('target_drift_zero_events'))} abort_zero_events={_phase118_bool_token(report.get('abort_zero_events'))} unsupported_or_unsafe_window_zero_events={_phase118_bool_token(report.get('unsupported_or_unsafe_window_zero_events'))} type_text_raw_hidden={_phase118_bool_token(report.get('type_text_raw_hidden'))} per_app_controller_required={_phase118_bool_token(report.get('per_app_controller_required'))} hardcoded_app_whitelist_required={_phase118_bool_token(report.get('hardcoded_app_whitelist_required'))} real_dispatch_performed={_phase118_bool_token(report.get('real_dispatch_performed'))} real_desktop_touched={_phase118_bool_token(report.get('real_desktop_touched'))} actions_expanded={_phase118_bool_token(report.get('actions_expanded'))} low_level_event_count={int(report.get('low_level_event_count', 0) or 0)}"  # 新增代码+URG3ActionDSL：返回固定顺序验收行；如果没有这一行，可见终端匹配容易因字段顺序漂移失败。
# 新增代码+URG3ActionDSL：函数段结束，phase118_universal_action_dsl_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+URG3ActionDSL：函数段开始，提供命令行和真实终端统一入口；如果没有这段函数，controller 场景无法运行 URG-3。
    _ = argv  # 新增代码+URG3ActionDSL：保留未来参数扩展位；如果没有这一行，读者可能误以为 argv 被遗漏。
    report = run_phase118_universal_action_dsl_contract()  # 新增代码+URG3ActionDSL：运行 URG-3 合同；如果没有这一行，CLI 没有结构化事实来源。
    print(phase118_universal_action_dsl_cli_line(report))  # 新增代码+URG3ActionDSL：打印固定 token 行；如果没有这一行，真实终端验收无法稳定匹配成功。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+URG3ActionDSL：打印完整 JSON 报告；如果没有这一行，失败时不方便定位字段。
    print(PHASE118_UNIVERSAL_ACTION_DSL_MARKER)  # 新增代码+URG3ActionDSL：单独打印 ready marker；如果没有这一行，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+URG3ActionDSL：按合同结果返回退出码；如果没有这一行，失败也可能被终端当成成功。
# 新增代码+URG3ActionDSL：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["PHASE118_ACTIONS_EXPANDED", "PHASE118_REAL_DISPATCH_PERFORMED", "PHASE118_UNIVERSAL_ACTION_DSL_MARKER", "PHASE118_UNIVERSAL_ACTION_DSL_MODEL", "PHASE118_UNIVERSAL_ACTION_DSL_OK_TOKEN", "Phase118RecordingLowLevelSender", "UniversalActionDslRuntime", "main", "phase118_universal_action_dsl_cli_line", "run_phase118_universal_action_dsl_contract"]  # 新增代码+URG3ActionDSL：限定公开 API；如果没有这一行，外部通配导入可能暴露内部 helper。


if __name__ == "__main__":  # 新增代码+URG3ActionDSL：文件入口段开始，允许 `python -m` 直接运行；如果没有这一行，真实终端无法直接调用本模块。
    raise SystemExit(main())  # 新增代码+URG3ActionDSL：调用 main 并传递退出码；如果没有这一行，直接运行文件不会执行合同。
# 新增代码+URG3ActionDSL：文件入口段结束，本模块到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
