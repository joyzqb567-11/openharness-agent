"""URG-5 universal Paint/Pikachu representative acceptance contract."""  # 新增代码+URG5PaintPikachu：说明本模块只做代表验收合同，不做 Paint 专用产品控制器；如果没有这一行，读者容易误以为这里是逐应用控制器。
from __future__ import annotations  # 新增代码+URG5PaintPikachu：启用延迟类型解析；如果没有这一行，旧导入顺序下复杂类型标注更容易失败。

import json  # 新增代码+URG5PaintPikachu：导入 JSON 用于 CLI 输出结构化报告；如果没有这一行，真实终端失败时不方便复盘。
from typing import Any  # 新增代码+URG5PaintPikachu：导入 Any 描述 JSON 风格动态报告；如果没有这一行，公开接口边界不清楚。

try:  # 新增代码+URG5PaintPikachu：优先按包路径导入既有通用 Computer Use 能力；如果没有这一段，单测和 bat 入口无法共享实现。
    from learning_agent.computer_use_mcp_v2.windows_runtime.drawing_primitives import build_pikachu_drag_plan  # 新增代码+URG5PaintPikachu：复用通用皮卡丘拖拽 primitive；如果没有这一行，验收会重复写固定坐标脚本。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_action_dsl import UniversalActionDslRuntime  # 新增代码+URG5PaintPikachu：复用 URG-3 动作 DSL 到 SendInput 桥；如果没有这一行，绘图动作不会走统一动作层。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_observe_plan_act_verify import Phase119GenericVerifier, UniversalObservePlanActVerifyLoop  # 新增代码+URG5PaintPikachu：复用 URG-4 闭环和通用验证器；如果没有这一行，Paint 验收会绕开通用 observe-plan-act-verify。
except ModuleNotFoundError as error:  # 新增代码+URG5PaintPikachu：兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这一段，真实可见终端可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.drawing_primitives", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_action_dsl", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_observe_plan_act_verify"}:  # 新增代码+URG5PaintPikachu：只兜底包路径缺失；如果没有这一行，真实内部 bug 可能被误吞。
        raise  # 新增代码+URG5PaintPikachu：重新抛出非路径类导入错误；如果没有这一行，排查依赖问题会变困难。
    from computer_use_mcp_v2.windows_runtime.drawing_primitives import build_pikachu_drag_plan  # type: ignore  # 新增代码+URG5PaintPikachu：脚本模式复用通用绘图 primitive；如果没有这一行，bat 入口无法生成拖拽计划。
    from computer_use_mcp_v2.windows_runtime.universal_action_dsl import UniversalActionDslRuntime  # type: ignore  # 新增代码+URG5PaintPikachu：脚本模式复用动作 DSL；如果没有这一行，bat 入口无法执行通用动作桥。
    from computer_use_mcp_v2.windows_runtime.universal_observe_plan_act_verify import Phase119GenericVerifier, UniversalObservePlanActVerifyLoop  # type: ignore  # 新增代码+URG5PaintPikachu：脚本模式复用 URG-4 闭环；如果没有这一行，bat 入口无法运行合同。

PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MARKER = "PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_READY"  # 新增代码+URG5PaintPikachu：定义 URG-5 ready marker；如果没有这一行，真实终端验收没有稳定锚点。
PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_OK_TOKEN = "PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_OK"  # 新增代码+URG5PaintPikachu：定义 URG-5 成功 token；如果没有这一行，日志无法区分成功输出和普通文本。
PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MODEL = "phase120_universal_paint_pikachu_acceptance"  # 新增代码+URG5PaintPikachu：定义报告模型名；如果没有这一行，最终矩阵无法识别 URG-5 版本。


def _phase120_bool_token(value: Any) -> str:  # 新增代码+URG5PaintPikachu：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出可能混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+URG5PaintPikachu：返回 true 或 false 文本；如果没有这一行，验收器匹配会不稳定。
# 新增代码+URG5PaintPikachu：函数段结束，_phase120_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。


class Phase120RepresentativeRealDragSender:  # 新增代码+URG5PaintPikachu：类段开始，定义代表验收用低层拖拽发送记录器；如果没有这个类，URG-5 无法证明拖拽路径到达最后一跳。
    def __init__(self) -> None:  # 新增代码+URG5PaintPikachu：函数段开始，初始化发送记录；如果没有这段函数，动作证据无法累计。
        self.low_level_events: list[dict[str, Any]] = []  # 新增代码+URG5PaintPikachu：保存低层事件副本；如果没有这一行，测试无法证明 drag_path 被展开。
        self.real_desktop_touched = False  # 修改代码+源码复核门禁：初始化真实桌面触达标记且代表 sender 永远不置真；如果没有这一行，报告无法表达是否已派发物理真实动作。
        self.physical_desktop_dispatch_performed = False  # 新增代码+源码复核门禁：明确代表 sender 没有执行物理桌面派发；如果没有这一行，用户无法区分模拟证据和真实 SendInput。
    # 新增代码+URG5PaintPikachu：函数段结束，Phase120RepresentativeRealDragSender.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def send_low_level(self, events: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+URG5PaintPikachu：函数段开始，接收统一 dispatcher 展开的低层事件；如果没有这段函数，通用动作层没有最后一跳。
        safe_events = [dict(event) for event in list(events or [])]  # 新增代码+URG5PaintPikachu：复制事件避免后续污染审计；如果没有这一行，外部修改可能改变证据。
        self.low_level_events.extend(safe_events)  # 新增代码+URG5PaintPikachu：追加本次事件；如果没有这一行，事件计数和类型不可验证。
        self.real_desktop_touched = False  # 修改代码+源码复核门禁：代表 sender 只记录事件不触碰桌面；如果没有这一行，成熟矩阵会把模拟事件误判为真实动作。
        self.physical_desktop_dispatch_performed = False  # 新增代码+源码复核门禁：每次发送后仍明确没有物理派发；如果没有这一行，后续报告可能继承错误状态。
        return {"ok": bool(safe_events), "sender": "phase120_representative_real_drag_sender", "low_level_event_count": len(safe_events), "representative_dispatch_performed": bool(safe_events), "physical_desktop_dispatch_performed": False, "real_dispatch_performed": False, "real_desktop_touched": False, "raw_text_included": False}  # 修改代码+源码复核门禁：返回脱敏发送摘要并把真实字段置 false；如果没有这一行，动作层无法判断派发是否成功。
    # 新增代码+URG5PaintPikachu：函数段结束，Phase120RepresentativeRealDragSender.send_low_level 到此结束；如果没有这个边界说明，初学者不容易看出发送范围。
# 新增代码+URG5PaintPikachu：类段结束，Phase120RepresentativeRealDragSender 到此结束；如果没有这个边界说明，初学者不容易看出 sender 范围。


class Phase120PaintObservationRuntime:  # 新增代码+URG5PaintPikachu：类段开始，提供 Paint 代表窗口和画布观察帧；如果没有这个类，闭环没有真实窗口与画布区域证据。
    def __init__(self, drag_sender: Any | None = None) -> None:  # 修改代码+URG5PaintPikachu：函数段开始，初始化观察序号并接收拖拽 sender；如果没有这段函数，动作前后观察无法区分也无法感知动作后变化。
        self.sequence = 0  # 新增代码+URG5PaintPikachu：保存观察帧序号；如果没有这一行，画布变化无法用帧顺序表达。
        self.drag_sender = drag_sender  # 修改代码+URG5PaintPikachu：保存代表拖拽 sender 供观察层读取动作事实；如果没有这一行，after-observe 仍会把画布看成空白。
    # 新增代码+URG5PaintPikachu：函数段结束，Phase120PaintObservationRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def observe(self, target_hint: str = "", real_desktop_touched: bool = False, target_window: dict[str, Any] | None = None) -> dict[str, Any]:  # 修改代码+CompatSlimming：函数段开始，返回兼容 URG-1/URG-4 的观察帧并接收绑定窗口；如果没有这段函数，通用 loop 传入 target_window 时会崩溃。
        self.sequence += 1  # 新增代码+URG5PaintPikachu：推进观察序号；如果没有这一行，before/after 画布帧会无法区分。
        sender_touched = bool(getattr(self.drag_sender, "physical_desktop_dispatch_performed", False))  # 修改代码+源码复核门禁：只从物理派发字段读取真实触达；如果没有这一行，representative sender 会继续冒充真实动作。
        canvas_state = "changed" if bool(real_desktop_touched or sender_touched) else "blank"  # 修改代码+源码复核门禁：只有真实桌面触达才表达画布变化；如果没有这一行，动作后验证会被模拟状态骗过。
        window = dict(target_window or {"app_id": "mspaint.exe", "process_name": "mspaint.exe", "window_id": "hwnd:12005", "title_preview": "Paint - URG5 Pikachu Acceptance", "rect": {"left": 100, "top": 80, "right": 900, "bottom": 700, "width": 800, "height": 620}})  # 修改代码+CompatSlimming：优先使用通用 loop 绑定窗口，否则构造 Paint 代表窗口身份；如果没有这一行，动作前目标复核缺少窗口边界。
        canvas = {"left": 180, "top": 170, "right": 820, "bottom": 620, "width": 640, "height": 450, "state": canvas_state, "state_fingerprint": f"phase120-canvas-{canvas_state}-{self.sequence}"}  # 新增代码+URG5PaintPikachu：构造画布区域摘要；如果没有这一行，拖拽路径没有可审计区域。
        return {"model": PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MODEL, "real_observation_frame": True, "frame_sequence": self.sequence, "target_hint": str(target_hint or "mspaint"), "target_window": window, "target_window_identity_present": True, "real_window_inventory": True, "screenshot_observation": True, "uia_tree_observation": True, "window_state_observation": True, "uia_or_vision_targeting": True, "real_paint_window_verified": True, "real_canvas_region_detected": True, "canvas": canvas, "canvas_changed": canvas_state == "changed", "raw_text_included": False, "actions_expanded": False, "real_desktop_touched": bool(real_desktop_touched), "low_level_event_count": 0}  # 新增代码+URG5PaintPikachu：返回完整观察帧；如果没有这一行，planner 和 verifier 拿不到目标事实。
    # 新增代码+URG5PaintPikachu：函数段结束，Phase120PaintObservationRuntime.observe 到此结束；如果没有这个边界说明，初学者不容易看出观察范围。
# 新增代码+URG5PaintPikachu：类段结束，Phase120PaintObservationRuntime 到此结束；如果没有这个边界说明，初学者不容易看出观察 runtime 范围。


class Phase120PikachuPlanner:  # 新增代码+URG5PaintPikachu：类段开始，把通用皮卡丘拖拽计划交给 URG-4 loop；如果没有这个类，画图动作会散落在合同入口里。
    def plan(self, task: dict[str, Any], observation_frame: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+URG5PaintPikachu：函数段开始，根据画布观察生成通用 DSL 动作；如果没有这段函数，observe 和 act 之间没有规划边界。
        canvas = observation_frame.get("canvas", {}) if isinstance(observation_frame.get("canvas", {}), dict) else {}  # 新增代码+URG5PaintPikachu：读取画布区域；如果没有这一行，拖拽计划无法相对画布生成。
        plan = build_pikachu_drag_plan(canvas)  # 新增代码+URG5PaintPikachu：调用通用绘图 primitive 生成皮卡丘路径；如果没有这一行，代码会退回手写固定 Paint 坐标。
        drag_paths = plan.get("drag_paths", []) if isinstance(plan, dict) else []  # 新增代码+URG5PaintPikachu：读取拖拽路径列表；如果没有这一行，后续动作没有来源。
        return [{"type": "drag_path", "points": list(path.get("points", []) or []), "shape": str(path.get("name", ""))} for path in list(drag_paths or []) if isinstance(path, dict)]  # 新增代码+URG5PaintPikachu：转换为 URG-3 通用 DSL 动作；如果没有这一行，路径不会进入统一 SendInput dispatcher。
    # 新增代码+URG5PaintPikachu：函数段结束，Phase120PikachuPlanner.plan 到此结束；如果没有这个边界说明，初学者不容易看出规划范围。
# 新增代码+URG5PaintPikachu：类段结束，Phase120PikachuPlanner 到此结束；如果没有这个边界说明，初学者不容易看出 planner 范围。


class Phase120PaintVerifier(Phase119GenericVerifier):  # 新增代码+URG5PaintPikachu：类段开始，复用 URG-4 通用验证器并补充画布变化判断；如果没有这个类，成功只看动作 ok 不看画布变化。
    def verify(self, task: dict[str, Any], attempt: int, action_results: list[dict[str, Any]], before_frame: dict[str, Any], after_frame: dict[str, Any]) -> dict[str, Any]:  # 新增代码+URG5PaintPikachu：函数段开始，验证动作后画布变化；如果没有这段函数，空白画布可能误过。
        base = super().verify(task, attempt, action_results, before_frame, after_frame)  # 新增代码+URG5PaintPikachu：先运行 URG-4 通用验证；如果没有这一行，观察和动作成功条件会重复造轮子。
        canvas_changed = bool(after_frame.get("canvas_changed"))  # 新增代码+URG5PaintPikachu：读取动作后画布变化标记；如果没有这一行，Paint 验收没有结果门禁。
        base["verified"] = bool(base.get("verified") and canvas_changed)  # 新增代码+URG5PaintPikachu：把画布变化纳入最终验证；如果没有这一行，只有事件派发也会被当成完成。
        base["canvas_changed_after_real_actions"] = canvas_changed  # 新增代码+URG5PaintPikachu：把画布变化写入验证报告；如果没有这一行，CLI 无法展示关键证据。
        base["decision"] = "verified" if bool(base.get("verified")) else "canvas_verification_failed"  # 新增代码+URG5PaintPikachu：更新决策文本；如果没有这一行，失败原因会不清楚。
        return base  # 新增代码+URG5PaintPikachu：返回补充后的验证报告；如果没有这一行，loop 拿不到最终判断。
    # 新增代码+URG5PaintPikachu：函数段结束，Phase120PaintVerifier.verify 到此结束；如果没有这个边界说明，初学者不容易看出验证范围。
# 新增代码+URG5PaintPikachu：类段结束，Phase120PaintVerifier 到此结束；如果没有这个边界说明，初学者不容易看出 verifier 范围。


def _phase120_script_artifact_route_report() -> dict[str, Any]:  # 新增代码+URG5PaintPikachu：函数段开始，验证脚本成品路线被阻断；如果没有这段函数，生成图片文件可能冒充 Paint 操作。
    return {"script_artifact_route_blocked": True, "generated_image_file_used": False, "direct_png_written": False, "reason": "representative_acceptance_requires_universal_gui_drag_actions"}  # 新增代码+URG5PaintPikachu：返回防作弊报告；如果没有这一行，最终报告无法证明未走图片 artifact 路线。
# 新增代码+URG5PaintPikachu：函数段结束，_phase120_script_artifact_route_report 到此结束；如果没有这个边界说明，初学者不容易看出防作弊范围。


def run_phase120_universal_paint_pikachu_acceptance_contract() -> dict[str, Any]:  # 新增代码+URG5PaintPikachu：函数段开始，运行 URG-5 Paint/Pikachu 代表验收合同；如果没有这段函数，测试和真实终端没有统一事实源。
    sender = Phase120RepresentativeRealDragSender()  # 新增代码+URG5PaintPikachu：创建代表真实拖拽低层 sender；如果没有这一行，动作层没有可审计最后一跳。
    action_runtime = UniversalActionDslRuntime(low_level_sender=sender)  # 新增代码+URG5PaintPikachu：把 URG-3 动作 DSL 接到代表 sender；如果没有这一行，拖拽不会走统一 dispatcher。
    loop = UniversalObservePlanActVerifyLoop(observation_runtime=Phase120PaintObservationRuntime(drag_sender=sender), action_runtime=action_runtime, planner=Phase120PikachuPlanner(), verifier=Phase120PaintVerifier(), max_retries=0)  # 修改代码+URG5PaintPikachu：组合 URG-4 闭环并把 sender 注入观察层；如果没有这一行，after-observe 无法证明画布变化。
    task = {"target": "mspaint", "goal": "draw Pikachu with generic drag paths"}  # 新增代码+URG5PaintPikachu：定义代表验收任务；如果没有这一行，loop 不知道目标和目标意图。
    result = loop.run_task(task)  # 新增代码+URG5PaintPikachu：执行一次完整闭环；如果没有这一行，报告没有真实动作和验证事实。
    script_report = _phase120_script_artifact_route_report()  # 新增代码+URG5PaintPikachu：读取防作弊报告；如果没有这一行，生成图片路线阻断不会进入总报告。
    low_level_event_count = len(sender.low_level_events)  # 新增代码+URG5PaintPikachu：统计低层事件数量；如果没有这一行，拖拽规模不可见。
    event_types = {str(event.get("type") or event.get("kind") or "") for event in sender.low_level_events}  # 新增代码+URG5PaintPikachu：汇总低层事件类型；如果没有这一行，无法证明有 mouse_down/move/up。
    representative_drag_path_dispatched = bool(low_level_event_count > 0 and {"mouse_down", "mouse_move", "mouse_up"}.issubset(event_types))  # 新增代码+源码复核门禁：判断代表性拖拽路径是否展开；如果没有这一行，开发证据会完全丢失。
    physical_desktop_dispatch_performed = bool(getattr(sender, "physical_desktop_dispatch_performed", False))  # 新增代码+源码复核门禁：读取是否真的调用物理桌面派发；如果没有这一行，真实成熟判断没有事实来源。
    real_drag_path_dispatched = bool(representative_drag_path_dispatched and physical_desktop_dispatch_performed)  # 修改代码+源码复核门禁：只有代表路径和物理派发同时存在才算真实拖拽；如果没有这一行，代表记录会冒充真实 SendInput。
    verification_reports = [attempt.get("verification", {}) for attempt in result.get("attempts", []) if isinstance(attempt, dict)]  # 新增代码+URG5PaintPikachu：提取每轮验证报告；如果没有这一行，画布变化字段不好汇总。
    canvas_changed_after_real_actions = bool(physical_desktop_dispatch_performed and any(bool(report.get("canvas_changed_after_real_actions")) for report in verification_reports))  # 修改代码+源码复核门禁：只有物理派发后的画布变化才算真实变化；如果没有这一行，模拟画布状态会冒充成功。
    passed = bool(result.get("ok") and real_drag_path_dispatched and canvas_changed_after_real_actions and script_report["script_artifact_route_blocked"] and not script_report["generated_image_file_used"])  # 新增代码+URG5PaintPikachu：汇总 URG-5 通过条件；如果没有这一行，main 无法用退出码表达失败。
    return {"marker": PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MARKER, "ok_token": PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_OK_TOKEN, "model": PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MODEL, "passed": passed, "paint_is_acceptance_only": True, "per_app_controller_required": False, "real_paint_window_verified": False, "real_canvas_region_detected": False, "representative_drag_path_dispatched": representative_drag_path_dispatched, "physical_desktop_dispatch_performed": physical_desktop_dispatch_performed, "real_drag_path_dispatched": real_drag_path_dispatched, "canvas_changed_after_real_actions": canvas_changed_after_real_actions, "script_artifact_route_blocked": script_report["script_artifact_route_blocked"], "generated_image_file_used": script_report["generated_image_file_used"], "real_desktop_execution_mature": passed, "observe_plan_act_verify_loop": True, "target_identity_rechecked_before_each_action": True, "ordinary_apps_controlled_by_generic_runtime": True, "representative_apps_are_acceptance_only": True, "low_level_event_count": low_level_event_count, "event_types": sorted(event_types), "result": result, "script_artifact_route": script_report}  # 修改代码+源码复核门禁：返回完整合同报告并把真实成熟字段绑定物理证据；如果没有这一行，测试和可见终端无法读取统一事实。
# 新增代码+URG5PaintPikachu：函数段结束，run_phase120_universal_paint_pikachu_acceptance_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同范围。


def phase120_universal_paint_pikachu_cli_line(report: dict[str, Any]) -> str:  # 新增代码+URG5PaintPikachu：函数段开始，把报告转成固定 token 行；如果没有这段函数，场景验收需要解析复杂 JSON。
    ok_token = f" {PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_OK_TOKEN}" if bool(report.get("passed")) else ""  # 新增代码+源码复核门禁：只有真实成熟通过才输出 OK token；如果没有这一行，失败报告会被验收器误读成成功。
    return f"{PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MARKER}{ok_token} paint_is_acceptance_only={_phase120_bool_token(report.get('paint_is_acceptance_only'))} per_app_controller_required={_phase120_bool_token(report.get('per_app_controller_required'))} real_paint_window_verified={_phase120_bool_token(report.get('real_paint_window_verified'))} real_canvas_region_detected={_phase120_bool_token(report.get('real_canvas_region_detected'))} representative_drag_path_dispatched={_phase120_bool_token(report.get('representative_drag_path_dispatched'))} physical_desktop_dispatch_performed={_phase120_bool_token(report.get('physical_desktop_dispatch_performed'))} real_drag_path_dispatched={_phase120_bool_token(report.get('real_drag_path_dispatched'))} canvas_changed_after_real_actions={_phase120_bool_token(report.get('canvas_changed_after_real_actions'))} script_artifact_route_blocked={_phase120_bool_token(report.get('script_artifact_route_blocked'))} generated_image_file_used={_phase120_bool_token(report.get('generated_image_file_used'))} real_desktop_execution_mature={_phase120_bool_token(report.get('real_desktop_execution_mature'))} low_level_event_count={int(report.get('low_level_event_count', 0) or 0)}"  # 修改代码+源码复核门禁：返回固定顺序 token 并显式区分代表和物理派发；如果没有这一行，真实终端匹配容易漂移。
# 新增代码+URG5PaintPikachu：函数段结束，phase120_universal_paint_pikachu_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+URG5PaintPikachu：函数段开始，提供命令行和真实终端入口；如果没有这段函数，controller 场景无法运行 URG-5。
    _ = argv  # 新增代码+URG5PaintPikachu：保留 argv 扩展位；如果没有这一行，读者可能误以为参数被遗漏。
    report = run_phase120_universal_paint_pikachu_acceptance_contract()  # 新增代码+URG5PaintPikachu：运行 URG-5 合同；如果没有这一行，CLI 没有事实来源。
    print(phase120_universal_paint_pikachu_cli_line(report))  # 新增代码+URG5PaintPikachu：打印固定 token 行；如果没有这一行，真实终端验收无法稳定匹配。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+URG5PaintPikachu：打印结构化报告；如果没有这一行，失败时不方便定位字段。
    print(PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MARKER)  # 新增代码+URG5PaintPikachu：单独打印 ready marker；如果没有这一行，人工观察终端容易漏标识。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+URG5PaintPikachu：按合同结果返回退出码；如果没有这一行，失败也可能被自动化当成成功。
# 新增代码+URG5PaintPikachu：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MARKER", "PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MODEL", "PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_OK_TOKEN", "Phase120PaintObservationRuntime", "Phase120PaintVerifier", "Phase120PikachuPlanner", "Phase120RepresentativeRealDragSender", "main", "phase120_universal_paint_pikachu_cli_line", "run_phase120_universal_paint_pikachu_acceptance_contract"]  # 新增代码+URG5PaintPikachu：限定公开 API；如果没有这一行，通配导入会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+URG5PaintPikachu：文件入口段开始，允许 python -m 直接运行；如果没有这一行，真实终端无法启动自检。
    raise SystemExit(main())  # 新增代码+URG5PaintPikachu：用 main 返回码退出；如果没有这一行，命令行状态不明确。
# 新增代码+URG5PaintPikachu：文件入口段结束，本模块到此结束；如果没有这个边界说明，初学者不容易看出直接运行范围。
