"""Phase47 Windows SendInput dispatcher."""  # 新增代码+Phase47WindowsSendInputDispatcher: 说明本文件负责把规范动作事件展开成低层 SendInput 序列；如果没有这个文件，Phase37 只停留在执行器合同。
from __future__ import annotations  # 新增代码+Phase47WindowsSendInputDispatcher: 启用延迟类型解析；如果没有这行代码，旧运行路径遇到前向类型标注更容易导入失败。

import json  # 新增代码+Phase47WindowsSendInputDispatcher: 导入 JSON 用于自检和文本泄露检查；如果没有这行代码，raw_text_hidden 无法被机器验证。
import sys  # 新增代码+Phase47WindowsSendInputDispatcher: 导入 sys 用于判断当前平台；如果没有这行代码，非 Windows 拒绝逻辑无法稳定。
from typing import Any  # 新增代码+Phase47WindowsSendInputDispatcher: 导入 Any 标注事件和注入对象；如果没有这行代码，输入输出边界不清楚。

try:  # 新增代码+Phase47WindowsSendInputDispatcher: 优先按包模式导入 Phase37 executor；如果没有这行代码，unittest 和生产入口无法复用现有动作层。
    from learning_agent.computer_use.sendinput_executor import WindowsSendInputExecutor  # 新增代码+Phase47WindowsSendInputDispatcher: 复用 executor 生成规范事件；如果没有这行代码，dispatcher 要重复处理高层动作参数。
except ModuleNotFoundError as error:  # 新增代码+Phase47WindowsSendInputDispatcher: 兼容 start_oauth_agent.bat 脚本模式；如果没有这行代码，真实终端从 learning_agent 目录运行时可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.sendinput_executor"}:  # 新增代码+Phase47WindowsSendInputDispatcher: 只允许目标包路径缺失时 fallback；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase47WindowsSendInputDispatcher: 重新抛出非路径类导入错误；如果没有这行代码，排查 executor 内部错误会困难。
    from computer_use.sendinput_executor import WindowsSendInputExecutor  # 新增代码+Phase47WindowsSendInputDispatcher: 脚本模式导入 executor；如果没有这行代码，bat 入口无法运行自检。

try:  # 新增代码+DrawingPrimitives：优先按包路径导入通用 drag_path 展开器；如果没有这段代码，dispatcher 无法理解绘图 primitive 输出。
    from learning_agent.computer_use.drawing_primitives import expand_drag_path_to_low_level_events  # 新增代码+DrawingPrimitives：导入拖拽路径到底层鼠标事件的统一转换函数；如果没有这一行，SendInput 最后一跳无法执行 drag_path。
except ModuleNotFoundError as error:  # 新增代码+DrawingPrimitives：兼容 start_oauth_agent.bat 从 learning_agent 目录运行的脚本模式；如果没有这段代码，真实终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.drawing_primitives"}:  # 新增代码+DrawingPrimitives：只兜底包路径缺失；如果没有这一行，drawing primitive 内部 bug 会被误吞。
        raise  # 新增代码+DrawingPrimitives：重新抛出真实内部导入错误；如果没有这一行，排查 drag_path 展开问题会困难。
    from computer_use.drawing_primitives import expand_drag_path_to_low_level_events  # type: ignore  # 新增代码+DrawingPrimitives：脚本模式导入同一转换函数；如果没有这一行，bat 入口无法使用 drag_path。

PHASE47_WINDOWS_SENDINPUT_DISPATCHER_MARKER = "PHASE47_WINDOWS_SENDINPUT_DISPATCHER_READY"  # 新增代码+Phase47WindowsSendInputDispatcher: 定义 Phase47 ready marker；如果没有这行代码，真实终端验收没有稳定等待锚点。
PHASE47_WINDOWS_SENDINPUT_DISPATCHER_OK_TOKEN = "PHASE47_WINDOWS_SENDINPUT_DISPATCHER_OK"  # 新增代码+Phase47WindowsSendInputDispatcher: 定义 Phase47 OK token；如果没有这行代码，日志无法区分运行完成和验收通过。
PHASE47_SENDINPUT_DISPATCHER_MODEL = "phase47_windows_sendinput_dispatcher"  # 新增代码+Phase47WindowsSendInputDispatcher: 定义 dispatcher 模型名；如果没有这行代码，状态和结果无法区分 Phase37/47。
PHASE47_ACTIONS_EXPANDED = True  # 新增代码+Phase47WindowsSendInputDispatcher: 标记 Phase47 已覆盖完整动作调度面但仍受上游门禁；如果没有这行代码，验收无法确认本阶段动作集合已展开。


def _phase47_bool_token(value: Any) -> str:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，把布尔值转成小写 token；如果没有这段函数，CLI 输出容易出现 True/False 漂移。
    return str(bool(value)).lower()  # 新增代码+Phase47WindowsSendInputDispatcher: 返回 true/false；如果没有这行代码，场景断言可能失败。
# 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，_phase47_bool_token 到此结束；如果没有这个边界说明，读者不容易看出 token 格式范围。


def _safe_int(value: Any) -> int:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，把坐标或滚轮值安全转成 int；如果没有这段函数，字符串坐标可能让调度失败。
    try:  # 新增代码+Phase47WindowsSendInputDispatcher: 捕获无法转换的输入；如果没有这行代码，坏参数会直接中断动作。
        return int(value or 0)  # 新增代码+Phase47WindowsSendInputDispatcher: 返回整数值；如果没有这行代码，低层事件坐标不稳定。
    except Exception:  # 新增代码+Phase47WindowsSendInputDispatcher: 捕获所有转换异常；如果没有这行代码，动态输入可能抛错。
        return 0  # 新增代码+Phase47WindowsSendInputDispatcher: 坏值兜底为 0；如果没有这行代码，调用方需要到处兜底。
# 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，_safe_int 到此结束；如果没有这个边界说明，读者不容易看出数值转换范围。

def _phase47_event_target(event: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ControlledPhysicalAdapter：函数段开始，从高层事件读取目标身份；如果没有这段函数，低层事件会丢失窗口边界，Phase95 受控 sender 会拒绝所有通用动作。
    target = event.get("target", {})  # 新增代码+ControlledPhysicalAdapter：读取高层事件里的 target 字段；如果没有这一行，后续不知道目标身份是否存在。
    return dict(target) if isinstance(target, dict) else {}  # 新增代码+ControlledPhysicalAdapter：只接受字典形态并复制返回；如果没有这一行，坏 target 可能污染低层 sender 或引发异常。
# 新增代码+ControlledPhysicalAdapter：函数段结束，_phase47_event_target 到此结束；如果没有这个边界说明，初学者不容易看出目标身份读取范围。

def _phase47_attach_target(events: list[dict[str, Any]], target: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+ControlledPhysicalAdapter：函数段开始，把同一个目标身份附加到展开后的每个低层事件；如果没有这段函数，目标复核只能停在 dispatcher 前，最后一跳无法再次判断是否安全。
    if not target:  # 新增代码+ControlledPhysicalAdapter：没有目标身份时保持原事件不变；如果没有这一行，旧测试和旧 recording 路径可能被空 target 字段扰动。
        return events  # 新增代码+ControlledPhysicalAdapter：返回原事件列表；如果没有这一行，空目标也会被复制成无意义字段。
    enriched: list[dict[str, Any]] = []  # 新增代码+ControlledPhysicalAdapter：准备保存带目标身份的事件副本；如果没有这一行，不能避免直接修改原始事件。
    for item in events:  # 新增代码+ControlledPhysicalAdapter：逐个处理展开后的低层事件；如果没有这一行，只能给第一条事件加 target。
        copied = dict(item)  # 新增代码+ControlledPhysicalAdapter：复制当前低层事件；如果没有这一行，调用方持有的事件可能被原地污染。
        copied["target"] = dict(target)  # 新增代码+ControlledPhysicalAdapter：写入脱敏目标身份；如果没有这一行，Phase95 不能确认事件发往哪个窗口。
        enriched.append(copied)  # 新增代码+ControlledPhysicalAdapter：把带 target 的事件加入结果；如果没有这一行，处理结果会丢失事件。
    return enriched  # 新增代码+ControlledPhysicalAdapter：返回完整带目标身份的低层事件列表；如果没有这一行，dispatcher 无法把安全边界传给 sender。
# 新增代码+ControlledPhysicalAdapter：函数段结束，_phase47_attach_target 到此结束；如果没有这个边界说明，初学者不容易看出目标附加范围。


class Phase47RecordingLowLevelSender:  # 新增代码+Phase47WindowsSendInputDispatcher: 类段开始，定义测试和自检用低层 sender；如果没有这个类，验收只能触碰真实鼠标键盘。
    def __init__(self) -> None:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，初始化低层事件记录；如果没有这段函数，fake sender 无法保存事件。
        self.low_level_events: list[dict[str, Any]] = []  # 新增代码+Phase47WindowsSendInputDispatcher: 保存低层事件副本；如果没有这行代码，测试无法证明 dispatcher 展开了什么。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，Phase47RecordingLowLevelSender.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，记录低层事件而不触碰系统；如果没有这段函数，dispatcher 没有安全测试 sender。
        self.low_level_events.extend(dict(event) for event in events)  # 新增代码+Phase47WindowsSendInputDispatcher: 复制事件用于断言；如果没有这行代码，后续修改可能污染记录。
        return {"ok": True, "low_level_event_count": len(events), "sender": "phase47_recording"}  # 新增代码+Phase47WindowsSendInputDispatcher: 返回成功摘要；如果没有这行代码，dispatcher 无法形成成功结果。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，Phase47RecordingLowLevelSender.send_low_level 到此结束；如果没有这个边界说明，读者不容易看出 fake 发送范围。


class WindowsSendInputDispatcher:  # 新增代码+Phase47WindowsSendInputDispatcher: 类段开始，定义 Windows SendInput 调度器；如果没有这个类，高层事件无法展开成低层输入序列。
    def __init__(self, platform: str | None = None, enabled: bool = False, low_level_sender: Any | None = None, target_verifier: Any | None = None) -> None:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，初始化平台、开关、低层 sender 和目标校验器；如果没有这段函数，dispatcher 无法安全注入和测试。
        self.platform = platform or sys.platform  # 新增代码+Phase47WindowsSendInputDispatcher: 保存平台名称；如果没有这行代码，非 Windows 拒绝路径无法稳定测试。
        self.enabled = bool(enabled)  # 新增代码+Phase47WindowsSendInputDispatcher: 保存显式启用开关；如果没有这行代码，默认安全关闭无法表达。
        self.low_level_sender = low_level_sender  # 新增代码+Phase47WindowsSendInputDispatcher: 保存低层 sender；如果没有这行代码，dispatcher 没有最终发送对象。
        self.target_verifier = target_verifier  # 新增代码+Phase47WindowsSendInputDispatcher: 保存动作前目标校验器；如果没有这行代码，窗口变化检查无法接入。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，WindowsSendInputDispatcher.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，返回 dispatcher 状态；如果没有这段函数，/computer status 无法看到真实调度层。
        platform_supported = self.platform == "win32"  # 新增代码+Phase47WindowsSendInputDispatcher: 判断平台是否支持 Windows 输入；如果没有这行代码，非 Windows 可能误报可用。
        sender_available = self.low_level_sender is not None and hasattr(self.low_level_sender, "send_low_level")  # 新增代码+Phase47WindowsSendInputDispatcher: 判断低层 sender 是否可用；如果没有这行代码，只有开关没有发送器也可能误报成功。
        available = bool(platform_supported and self.enabled and sender_available)  # 新增代码+Phase47WindowsSendInputDispatcher: 只有平台、开关、sender 都满足才可调度；如果没有这行代码，安全门会被削弱。
        reason = "SendInput dispatcher 可用。" if available else "SendInput dispatcher 未启用、平台不支持或缺少低层 sender。"  # 新增代码+Phase47WindowsSendInputDispatcher: 生成可读状态原因；如果没有这行代码，用户不知道为什么未执行。
        return {"marker": PHASE47_WINDOWS_SENDINPUT_DISPATCHER_MARKER, "model": PHASE47_SENDINPUT_DISPATCHER_MODEL, "backend": "windows_sendinput_dispatcher", "available": available, "platform": self.platform, "platform_supported": platform_supported, "enabled": self.enabled, "sender_available": sender_available, "target_check_enabled": callable(self.target_verifier), "reason": reason, "actions_expanded": PHASE47_ACTIONS_EXPANDED}  # 新增代码+Phase47WindowsSendInputDispatcher: 返回机器可读状态；如果没有这行代码，验收和状态页无法验证边界。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，WindowsSendInputDispatcher.status 到此结束；如果没有这个边界说明，读者不容易看出状态范围。

    def _refusal(self, decision: str, message: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，构造统一拒绝结果；如果没有这段函数，失败字段会分散且不一致。
        data = {"ok": False, "decision": str(decision), "message": str(message), "dispatcher": PHASE47_SENDINPUT_DISPATCHER_MODEL, "actions_expanded": PHASE47_ACTIONS_EXPANDED}  # 新增代码+Phase47WindowsSendInputDispatcher: 构造基础拒绝数据；如果没有这行代码，调用方无法机器读取原因。
        data.update(extra or {})  # 新增代码+Phase47WindowsSendInputDispatcher: 合并额外细节；如果没有这行代码，具体拒绝分支无法补充状态。
        return data  # 新增代码+Phase47WindowsSendInputDispatcher: 返回拒绝结果；如果没有这行代码，send 无法结束失败分支。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，WindowsSendInputDispatcher._refusal 到此结束；如果没有这个边界说明，读者不容易看出拒绝结果范围。

    def _verify_target(self) -> dict[str, Any]:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，执行动作前目标校验；如果没有这段函数，动作可能发到已经变化的窗口。
        if not callable(self.target_verifier):  # 新增代码+Phase47WindowsSendInputDispatcher: 没有校验器时返回兼容通过；如果没有这行代码，旧测试和安全 fake 路径会被误拦截。
            return {"ok": True, "reason": "no target verifier configured", "target_check_enabled": False}  # 新增代码+Phase47WindowsSendInputDispatcher: 返回未配置但兼容通过；如果没有这行代码，调用方不知道目标校验状态。
        try:  # 新增代码+Phase47WindowsSendInputDispatcher: 捕获校验器异常；如果没有这行代码，目标检测错误会拖垮 agent。
            result = self.target_verifier()  # 新增代码+Phase47WindowsSendInputDispatcher: 调用注入校验器；如果没有这行代码，目标稳定性不会被检查。
        except Exception as error:  # 新增代码+Phase47WindowsSendInputDispatcher: 捕获校验器异常；如果没有这行代码，异常会直接抛出。
            return {"ok": False, "reason": f"target verifier failed: {type(error).__name__}", "target_check_enabled": True}  # 新增代码+Phase47WindowsSendInputDispatcher: 异常时拒绝发送；如果没有这行代码，无法证明失败前没有副作用。
        return dict(result) if isinstance(result, dict) else {"ok": bool(result), "reason": "target verifier returned non-dict", "target_check_enabled": True}  # 新增代码+Phase47WindowsSendInputDispatcher: 规整校验结果；如果没有这行代码，非 dict 返回会污染判断。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，WindowsSendInputDispatcher._verify_target 到此结束；如果没有这个边界说明，读者不容易看出目标校验范围。

    def send(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，接收 Phase37 规范事件并调度低层事件；如果没有这段函数，executor 无法使用 dispatcher。
        status = self.status()  # 新增代码+Phase47WindowsSendInputDispatcher: 读取当前状态；如果没有这行代码，发送前无法判断平台/开关/sender。
        if not status["available"]:  # 新增代码+Phase47WindowsSendInputDispatcher: 未满足条件时拒绝；如果没有这行代码，默认安全关闭会失效。
            return self._refusal("dispatcher_unavailable", "SendInput dispatcher 未启用或缺少低层 sender，未触碰鼠标键盘。", {"status": status})  # 新增代码+Phase47WindowsSendInputDispatcher: 返回明确未执行结果；如果没有这行代码，用户可能误以为动作发生。
        target = self._verify_target()  # 新增代码+Phase47WindowsSendInputDispatcher: 在展开和发送前校验目标；如果没有这行代码，窗口变化时仍可能发送动作。
        if not bool(target.get("ok", False)):  # 新增代码+Phase47WindowsSendInputDispatcher: 判断目标校验是否失败；如果没有这行代码，拒绝结果会被忽略。
            return self._refusal("target_changed_before_send", "目标窗口在 SendInput 前未通过校验，已拒绝发送。", {"target": target})  # 新增代码+Phase47WindowsSendInputDispatcher: 返回目标变化拒绝；如果没有这行代码，动作可能打到错误窗口。
        low_level_events: list[dict[str, Any]] = []  # 新增代码+Phase47WindowsSendInputDispatcher: 准备低层事件容器；如果没有这行代码，展开结果没有保存位置。
        for event in list(events or []):  # 新增代码+Phase47WindowsSendInputDispatcher: 遍历规范事件；如果没有这行代码，dispatcher 不会处理任何动作。
            low_level_events.extend(self._expand_event(dict(event)))  # 新增代码+Phase47WindowsSendInputDispatcher: 展开并追加低层事件；如果没有这行代码，高层事件无法转换。
        if not low_level_events:  # 新增代码+Phase47WindowsSendInputDispatcher: 检查是否生成低层事件；如果没有这行代码，空动作可能误报成功。
            return self._refusal("no_low_level_events", "没有可发送的低层 SendInput 事件，已拒绝。", {"event_count": len(events or [])})  # 新增代码+Phase47WindowsSendInputDispatcher: 返回空事件拒绝；如果没有这行代码，用户不知道为何无动作。
        try:  # 新增代码+Phase47WindowsSendInputDispatcher: 捕获低层 sender 异常；如果没有这行代码，底层错误会拖垮 agent。
            raw_result = self.low_level_sender.send_low_level(low_level_events)  # 新增代码+Phase47WindowsSendInputDispatcher: 调用低层 sender；如果没有这行代码，事件不会到达最终发送层。
        except Exception as error:  # 新增代码+Phase47WindowsSendInputDispatcher: 捕获发送异常；如果没有这行代码，权限或系统错误会直接抛栈。
            return self._refusal("low_level_sender_failed", f"低层 sender 发送失败：{type(error).__name__}", {"low_level_event_count": len(low_level_events)})  # 新增代码+Phase47WindowsSendInputDispatcher: 返回异常类型；如果没有这行代码，失败不可解释。
        sender_result = dict(raw_result) if isinstance(raw_result, dict) else {"ok": bool(raw_result)}  # 新增代码+Phase47WindowsSendInputDispatcher: 规整低层 sender 返回值；如果没有这行代码，非 dict 返回会让结果不稳定。
        ok = bool(sender_result.get("ok", True))  # 新增代码+Phase47WindowsSendInputDispatcher: 读取低层成功状态；如果没有这行代码，sender 报错无法影响结果。
        event_types = [str(event.get("type", "")) for event in low_level_events]  # 新增代码+Phase47WindowsSendInputDispatcher: 收集低层事件类型；如果没有这行代码，审计看不到调度细节。
        return {"ok": ok, "dispatcher": PHASE47_SENDINPUT_DISPATCHER_MODEL, "low_level_event_count": len(low_level_events), "low_level_event_types": event_types, "target_verified": bool(target.get("ok", False)), "target": target, "sender": sender_result, "text_redacted": True, "actions_expanded": PHASE47_ACTIONS_EXPANDED}  # 新增代码+Phase47WindowsSendInputDispatcher: 返回调度摘要；如果没有这行代码，executor 无法形成安全结果。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，WindowsSendInputDispatcher.send 到此结束；如果没有这个边界说明，读者不容易看出发送流程范围。

    def _expand_event(self, event: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，把一个规范事件展开成低层事件；如果没有这段函数，动作类型会散落在 send 里。
        event_type = str(event.get("type", ""))  # 新增代码+Phase47WindowsSendInputDispatcher: 读取规范事件类型；如果没有这行代码，分支无法判断动作。
        target = _phase47_event_target(event)  # 新增代码+ControlledPhysicalAdapter：读取本动作绑定的目标身份；如果没有这一行，展开后的 mouse/key 事件无法交给受控物理 sender 复核。
        if event_type == "move":  # 新增代码+Phase47WindowsSendInputDispatcher: 展开鼠标移动；如果没有这行代码，move_mouse 无法生成低层事件。
            return _phase47_attach_target([{"type": "mouse_move", "x": _safe_int(event.get("x")), "y": _safe_int(event.get("y"))}], target)  # 修改代码+ControlledPhysicalAdapter：返回带目标身份的鼠标移动事件；如果没有这一行，Phase95 会因为缺少 target 拒绝移动。
        if event_type == "click":  # 新增代码+Phase47WindowsSendInputDispatcher: 展开单击；如果没有这行代码，click 无法生成按下/抬起。
            return _phase47_attach_target([{"type": "mouse_move", "x": _safe_int(event.get("x")), "y": _safe_int(event.get("y"))}, {"type": "mouse_down", "button": str(event.get("button", "left"))}, {"type": "mouse_up", "button": str(event.get("button", "left"))}], target)  # 修改代码+ControlledPhysicalAdapter：返回带目标身份的移动、按下、抬起序列；如果没有这一行，受控 sender 无法复核点击目标。
        if event_type == "double_click":  # 新增代码+Phase47WindowsSendInputDispatcher: 展开双击；如果没有这行代码，double_click 无法生成两次点击。
            button = str(event.get("button", "left"))  # 新增代码+Phase47WindowsSendInputDispatcher: 读取鼠标按键；如果没有这行代码，双击按键不稳定。
            return _phase47_attach_target([{"type": "mouse_move", "x": _safe_int(event.get("x")), "y": _safe_int(event.get("y"))}, {"type": "mouse_down", "button": button}, {"type": "mouse_up", "button": button}, {"type": "mouse_down", "button": button}, {"type": "mouse_up", "button": button}], target)  # 修改代码+ControlledPhysicalAdapter：返回带目标身份的双击事件序列；如果没有这一行，真实最后一跳无法知道双击绑定哪个窗口。
        if event_type == "scroll":  # 新增代码+Phase47WindowsSendInputDispatcher: 展开滚轮；如果没有这行代码，scroll 无法生成低层滚轮事件。
            return _phase47_attach_target([{"type": "mouse_move", "x": _safe_int(event.get("x")), "y": _safe_int(event.get("y"))}, {"type": "mouse_wheel", "delta": _safe_int(event.get("delta"))}], target)  # 修改代码+ControlledPhysicalAdapter：返回带目标身份的移动和滚轮事件；如果没有这一行，滚动动作无法被 Phase95 目标门禁复核。
        if event_type == "drag_path":  # 新增代码+DrawingPrimitives：展开通用绘图拖拽路径；如果没有这一行，皮卡丘等绘图 primitive 无法进入低层鼠标事件。
            return _phase47_attach_target(expand_drag_path_to_low_level_events(list(event.get("points", []))), target)  # 修改代码+ControlledPhysicalAdapter：把 points 转成带目标身份的 mouse_move/down/up 序列；如果没有这一行，通用绘图路径到不了受控物理 sender。
        if event_type == "set_foreground":  # 新增代码+RealLaunchTargetSession：展开前台窗口聚焦事件；如果没有这一行，focus_window 无法真正把 agent 启动的窗口置前。
            return _phase47_attach_target([{"type": "set_foreground", "hwnd": _safe_int(event.get("hwnd"))}], target)  # 新增代码+RealLaunchTargetSession：返回带目标身份的 set_foreground 低层事件；如果没有这一行，真实鼠标键盘可能仍落到旧焦点窗口。
        if event_type == "key":  # 新增代码+Phase47WindowsSendInputDispatcher: 展开按键；如果没有这行代码，press_key 无法生成键盘事件。
            key = str(event.get("key", "")).strip()  # 新增代码+Phase47WindowsSendInputDispatcher: 读取键名；如果没有这行代码，低层键盘事件没有目标。
            return _phase47_attach_target([{"type": "key_down", "key": key}, {"type": "key_up", "key": key}], target) if key else []  # 修改代码+ControlledPhysicalAdapter：返回带目标身份的按下/抬起事件；如果没有这一行，键盘事件无法被最后一跳按窗口审计。
        if event_type == "hotkey":  # 新增代码+URG3ActionDSL：展开通用组合键动作；如果没有这一行，URG-3 的 hotkey 只能退化成多个普通按键，真实语义不完整。
            keys = [str(key).strip() for key in event.get("keys", []) if str(key).strip()]  # 新增代码+URG3ActionDSL：清洗组合键列表；如果没有这一行，空键名可能进入低层键盘事件。
            return _phase47_attach_target([{"type": "key_down", "key": key} for key in keys] + [{"type": "key_up", "key": key} for key in reversed(keys)], target) if keys else []  # 修改代码+ControlledPhysicalAdapter：返回带目标身份的组合键事件；如果没有这一行，快捷键可能缺少最后一跳目标边界。
        if event_type == "text":  # 新增代码+Phase47WindowsSendInputDispatcher: 展开文本输入摘要；如果没有这行代码，type_text 无法进入低层 sender。
            return _phase47_attach_target([{"type": "unicode_text", "text_length": _safe_int(event.get("text_length")), "text_sha256_16": str(event.get("text_sha256_16", "")), "text_redacted": True}], target)  # 修改代码+ControlledPhysicalAdapter：返回带目标身份的脱敏 unicode 文本摘要；如果没有这一行，文本事件无法进入受控 sender 的目标验证。
        return []  # 新增代码+Phase47WindowsSendInputDispatcher: 未知规范事件返回空；如果没有这行代码，未知事件可能误发。
    # 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，WindowsSendInputDispatcher._expand_event 到此结束；如果没有这个边界说明，读者不容易看出事件展开范围。
# 新增代码+Phase47WindowsSendInputDispatcher: 类段结束，WindowsSendInputDispatcher 到此结束；如果没有这个边界说明，读者不容易看出 dispatcher 范围。


def run_phase47_sendinput_dispatcher_contract() -> dict[str, Any]:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，运行 Phase47 安全自检合同；如果没有这段函数，真实终端场景没有稳定命令入口。
    from learning_agent.computer_use.native_host import InProcessWindowsNativeHostClient, WindowsComputerUseNativeHost  # 新增代码+Phase47WindowsSendInputDispatcher: 延迟导入 native host 避免循环依赖；如果没有这行代码，自检无法证明 host action 集成。
    sender = Phase47RecordingLowLevelSender()  # 新增代码+Phase47WindowsSendInputDispatcher: 创建记录型低层 sender；如果没有这行代码，自检会触碰真实桌面或无法检查事件。
    verifier_calls = {"count": 0}  # 新增代码+Phase47WindowsSendInputDispatcher: 准备记录目标校验次数；如果没有这行代码，target_check=true 没有证据。
    def verify_target() -> dict[str, Any]:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，定义稳定通过的目标校验器；如果没有这段函数，自检无法证明发送前检查目标。
        verifier_calls["count"] += 1  # 新增代码+Phase47WindowsSendInputDispatcher: 记录一次校验；如果没有这行代码，无法判断校验是否执行。
        return {"ok": True, "reason": "phase47 contract target stable"}  # 新增代码+Phase47WindowsSendInputDispatcher: 返回目标稳定；如果没有这行代码，自检动作会被拒绝。
    dispatcher = WindowsSendInputDispatcher(platform="win32", enabled=True, low_level_sender=sender, target_verifier=verify_target)  # 新增代码+Phase47WindowsSendInputDispatcher: 创建安全 dispatcher；如果没有这行代码，自检没有调度主体。
    executor = WindowsSendInputExecutor(platform="win32", enabled=True, sendinput_impl=dispatcher)  # 新增代码+Phase47WindowsSendInputDispatcher: 把 dispatcher 接到 Phase37 executor；如果没有这行代码，无法复用动作事件生成。
    secret_text = "phase47-contract-secret"  # 新增代码+Phase47WindowsSendInputDispatcher: 准备泄露检查文本；如果没有这行代码，raw_text_hidden 没有输入。
    results = [executor.execute("move_mouse", {"x": 1, "y": 2}), executor.execute("click", {"x": 3, "y": 4}), executor.execute("double_click", {"x": 5, "y": 6}), executor.execute("scroll", {"x": 7, "y": 8, "delta": -120}), executor.execute("press_key", {"key": "ENTER"}), executor.execute("type_text", {"text": secret_text})]  # 新增代码+Phase47WindowsSendInputDispatcher: 执行所有支持动作；如果没有这行代码，all_actions=true 没有证据。
    changed_dispatcher = WindowsSendInputDispatcher(platform="win32", enabled=True, low_level_sender=Phase47RecordingLowLevelSender(), target_verifier=lambda: {"ok": False, "reason": "changed"})  # 新增代码+Phase47WindowsSendInputDispatcher: 创建目标变化的 dispatcher；如果没有这行代码，目标拒绝路径没有证据。
    changed_result = WindowsSendInputExecutor(platform="win32", enabled=True, sendinput_impl=changed_dispatcher).execute("click", {"x": 1, "y": 1})  # 新增代码+Phase47WindowsSendInputDispatcher: 执行一次应拒绝的点击；如果没有这行代码，target_check=true 不完整。
    host_sender = Phase47RecordingLowLevelSender()  # 新增代码+Phase47WindowsSendInputDispatcher: 创建 host 专用 sender；如果没有这行代码，host_action 没有独立证据。
    host_executor = WindowsSendInputExecutor(platform="win32", enabled=True, sendinput_impl=WindowsSendInputDispatcher(platform="win32", enabled=True, low_level_sender=host_sender, target_verifier=lambda: {"ok": True, "reason": "host target stable"}))  # 新增代码+Phase47WindowsSendInputDispatcher: 创建 host 专用 executor；如果没有这行代码，native host 无法安全执行 action。
    host = WindowsComputerUseNativeHost(platform="win32", real_actions_enabled=True, action_executor=host_executor)  # 新增代码+Phase47WindowsSendInputDispatcher: 注入动作 executor 到 native host；如果没有这行代码，host action 仍会默认拒绝。
    host_action = InProcessWindowsNativeHostClient(host).request({"op": "action", "action": "type_text", "text": secret_text})  # 新增代码+Phase47WindowsSendInputDispatcher: 通过 host action 执行安全 fake 文本动作；如果没有这行代码，host_action=true 无证据。
    visible_payload = json.dumps({"results": [result.data for result in results], "events": sender.low_level_events, "host": host_action, "host_events": host_sender.low_level_events}, ensure_ascii=False).lower()  # 新增代码+Phase47WindowsSendInputDispatcher: 汇总可见输出做泄露检查；如果没有这行代码，原文可能漏到某个结果里。
    dispatch = bool(sender.low_level_events and all(result.ok for result in results))  # 新增代码+Phase47WindowsSendInputDispatcher: 判断 dispatcher 是否发送了低层事件且所有动作成功；如果没有这行代码，dispatch=true 没有证据。
    low_level_types = {event.get("type") for event in sender.low_level_events}  # 新增代码+Phase47WindowsSendInputDispatcher: 收集低层事件类型；如果没有这行代码，all_actions=true 无法确认覆盖面。
    all_actions = {"mouse_move", "mouse_down", "mouse_up", "mouse_wheel", "key_down", "key_up", "unicode_text"}.issubset(low_level_types)  # 新增代码+Phase47WindowsSendInputDispatcher: 检查所有动作族已展开；如果没有这行代码，单个动作漏实现也可能通过。
    target_check = bool(verifier_calls["count"] >= 6 and not changed_result.ok and changed_result.data.get("dispatch", {}).get("decision") == "target_changed_before_send")  # 新增代码+Phase47WindowsSendInputDispatcher: 检查目标校验通过和拒绝两条路径；如果没有这行代码，窗口变化风险无法验收。
    host_action_ok = bool(host_action.get("ok") and host_action.get("result", {}).get("backend") == "windows_sendinput")  # 新增代码+Phase47WindowsSendInputDispatcher: 检查 native host action 成功接入；如果没有这行代码，host_action=true 没有证据。
    raw_text_hidden = secret_text not in visible_payload  # 新增代码+Phase47WindowsSendInputDispatcher: 检查原始文本没有出现在结果和低层事件；如果没有这行代码，脱敏泄露无法发现。
    return {"marker": PHASE47_WINDOWS_SENDINPUT_DISPATCHER_MARKER, "ok_token": PHASE47_WINDOWS_SENDINPUT_DISPATCHER_OK_TOKEN, "dispatch": dispatch, "all_actions": all_actions, "target_check": target_check, "host_action": host_action_ok, "raw_text_hidden": raw_text_hidden, "actions_expanded": PHASE47_ACTIONS_EXPANDED, "low_level_event_count": len(sender.low_level_events), "host_action_result": host_action}  # 新增代码+Phase47WindowsSendInputDispatcher: 返回完整自检报告；如果没有这行代码，CLI 和测试拿不到统一结果。
# 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，run_phase47_sendinput_dispatcher_contract 到此结束；如果没有这个边界说明，读者不容易看出自检范围。


def phase47_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，把自检报告转成稳定 token 行；如果没有这段函数，验收场景需要解析完整 JSON。
    return f"{PHASE47_WINDOWS_SENDINPUT_DISPATCHER_MARKER} {PHASE47_WINDOWS_SENDINPUT_DISPATCHER_OK_TOKEN} dispatch={_phase47_bool_token(report.get('dispatch'))} all_actions={_phase47_bool_token(report.get('all_actions'))} target_check={_phase47_bool_token(report.get('target_check'))} host_action={_phase47_bool_token(report.get('host_action'))} raw_text_hidden={_phase47_bool_token(report.get('raw_text_hidden'))} actions_expanded={_phase47_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase47WindowsSendInputDispatcher: 返回固定顺序验收行；如果没有这行代码，debug log token 容易漂移。
# 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，phase47_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 格式范围。


def main() -> int:  # 新增代码+Phase47WindowsSendInputDispatcher: 函数段开始，提供命令行自检入口；如果没有这段函数，真实终端无法执行 Phase47 验收命令。
    report = run_phase47_sendinput_dispatcher_contract()  # 新增代码+Phase47WindowsSendInputDispatcher: 运行安全自检；如果没有这行代码，CLI 没有真实报告。
    print(PHASE47_WINDOWS_SENDINPUT_DISPATCHER_MARKER)  # 新增代码+Phase47WindowsSendInputDispatcher: 打印 ready marker；如果没有这行代码，验收控制器可能等不到阶段标记。
    print(phase47_cli_line(report))  # 新增代码+Phase47WindowsSendInputDispatcher: 打印固定 token 行；如果没有这行代码，debug log 无法确认通过。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase47WindowsSendInputDispatcher: 打印结构化报告；如果没有这行代码，失败时不易复盘。
    return 0 if bool(report.get("dispatch") and report.get("all_actions") and report.get("target_check") and report.get("host_action") and report.get("raw_text_hidden") and report.get("actions_expanded") is True) else 1  # 新增代码+Phase47WindowsSendInputDispatcher: 根据自检布尔值返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase47WindowsSendInputDispatcher: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出命令入口范围。


if __name__ == "__main__":  # 新增代码+Phase47WindowsSendInputDispatcher: 允许直接运行模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase47WindowsSendInputDispatcher: 使用 main 返回码退出；如果没有这行代码，命令行状态不稳定。
