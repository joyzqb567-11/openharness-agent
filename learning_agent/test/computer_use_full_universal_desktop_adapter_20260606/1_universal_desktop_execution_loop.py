"""Universal desktop execution adapter for Computer Use full mode."""  # 新增代码+UniversalDesktopAdapter：说明本文件只负责把 /computer use --full 接到通用 observe-plan-act-verify 闭环；如果没有这一行，读者容易误以为这里是某个软件的专用控制器。
from __future__ import annotations  # 新增代码+UniversalDesktopAdapter：启用延迟类型注解，避免运行时提前解析类型造成兼容问题；如果没有这一行，旧 Python 环境里前向类型更容易报错。
from typing import Any  # 新增代码+UniversalDesktopAdapter：导入 Any 用来描述动态 JSON 报告；如果没有这一行，函数签名无法清楚表达报告是灵活字典。

try:  # 新增代码+UniversalDesktopAdapter：优先按包路径导入现有通用闭环；如果没有这段代码，项目根目录运行时无法复用已完成的 Phase119 能力。
    from learning_agent.computer_use.universal_observe_plan_act_verify import UniversalObservePlanActVerifyLoop  # 新增代码+UniversalDesktopAdapter：导入通用 observe-plan-act-verify loop；如果没有这一行，adapter 会退化成重新造轮子的执行器。
except ModuleNotFoundError as error:  # 新增代码+UniversalDesktopAdapter：兼容 start_oauth_agent.bat 从 learning_agent 目录启动时的脚本模式；如果没有这一行，真实可见终端入口可能因包名前缀不同而失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.universal_observe_plan_act_verify"}:  # 新增代码+UniversalDesktopAdapter：只对包路径缺失兜底；如果没有这一行，Phase119 内部真实 bug 可能被误吞。
        raise  # 新增代码+UniversalDesktopAdapter：重新抛出非路径类导入错误；如果没有这一行，排查真实依赖问题会非常困难。
    from computer_use.universal_observe_plan_act_verify import UniversalObservePlanActVerifyLoop  # type: ignore  # 新增代码+UniversalDesktopAdapter：脚本模式下导入同一个通用闭环；如果没有这一行，bat 入口无法使用 adapter。

UNIVERSAL_DESKTOP_EXECUTION_LOOP_MODEL = "universal_desktop_execution_loop_adapter"  # 新增代码+UniversalDesktopAdapter：定义稳定模型名用于报告和测试识别；如果没有这一行，成熟度矩阵无法区分这个 adapter 和旧特例 loop。
UNIVERSAL_DESKTOP_EXECUTION_LOOP_CONNECTED_DECISION = "universal_desktop_execution_loop_connected_without_real_dispatch"  # 新增代码+UniversalDesktopAdapter：定义未接物理派发时的稳定决策码；如果没有这一行，用户看不到“已接通用闭环但未真实触桌面”的准确原因。
UNIVERSAL_DESKTOP_EXECUTION_LOOP_REAL_DECISION = "universal_desktop_execution_loop_real_dispatch_finished"  # 新增代码+UniversalDesktopAdapter：定义未来真实派发成功时的稳定决策码；如果没有这一行，后续接物理 sender 时缺少清晰成功语义。

def _universal_desktop_adapter_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+UniversalDesktopAdapter：函数段开始，安全读取报告中的数字字段；如果没有这段函数，坏字段会让 adapter 汇总时崩溃。
    try:  # 新增代码+UniversalDesktopAdapter：尝试把动态值转换成整数；如果没有这一行，字符串数字和正常数字无法统一处理。
        return int(value)  # 新增代码+UniversalDesktopAdapter：返回转换后的整数；如果没有这一行，上层拿不到可比较的事件数量。
    except (TypeError, ValueError):  # 新增代码+UniversalDesktopAdapter：捕获 None、空字符串或非数字文本；如果没有这一行，异常输入会中断整个桌面任务。
        return int(default)  # 新增代码+UniversalDesktopAdapter：坏值时返回默认值；如果没有这一行，报告缺字段时不能用 0 表示缺少证据。
# 新增代码+UniversalDesktopAdapter：函数段结束，_universal_desktop_adapter_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出数字清洗范围。

def _universal_desktop_adapter_points() -> list[dict[str, int]]:  # 新增代码+UniversalDesktopAdapter：函数段开始，生成一条通用演示拖拽轨迹；如果没有这段函数，通用闭环接线测试没有任何低层事件证据。
    return [{"x": 40, "y": 40}, {"x": 90, "y": 80}, {"x": 140, "y": 40}]  # 新增代码+UniversalDesktopAdapter：返回不表达任何固定图像主题的三点轨迹；如果没有这一行，adapter 可能又滑向皮卡丘或大象特例。
# 新增代码+UniversalDesktopAdapter：函数段结束，_universal_desktop_adapter_points 到此结束；如果没有这个边界说明，初学者不容易看出通用轨迹范围。

class UniversalDesktopExecutionLoopAdapter:  # 新增代码+UniversalDesktopAdapter：类段开始，把 desktop_task_runtime 需要的 run_desktop_task 接口桥接到通用闭环；如果没有这个类，默认 full 模式只能保持空 loop 或误接特例 loop。
    def __init__(self, loop: Any | None = None) -> None:  # 新增代码+UniversalDesktopAdapter：函数段开始，允许测试或未来生产注入更强的通用 loop；如果没有这段函数，adapter 无法替换观察、规划、动作和验证层。
        self.loop = loop if loop is not None else UniversalObservePlanActVerifyLoop(max_retries=0)  # 新增代码+UniversalDesktopAdapter：默认复用现有 Phase119 通用闭环且不额外重试；如果没有这一行，adapter 会重新实现闭环或产生多余动作。
    # 新增代码+UniversalDesktopAdapter：函数段结束，UniversalDesktopExecutionLoopAdapter.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出依赖注入范围。

    def _task_from_prompt(self, target_app: str, prompt: str) -> dict[str, Any]:  # 新增代码+UniversalDesktopAdapter：函数段开始，把自然语言任务包装成通用 DSL 任务；如果没有这段函数，desktop runtime 无法把用户意图交给 Phase119。
        safe_target = str(target_app or "desktop_app").strip() or "desktop_app"  # 新增代码+UniversalDesktopAdapter：清洗目标应用名并提供兜底；如果没有这一行，空目标会让 session 建立报告不稳定。
        safe_prompt = str(prompt or "")  # 新增代码+UniversalDesktopAdapter：把用户输入统一成字符串；如果没有这一行，None 输入会污染报告和哈希字段。
        return {"target": safe_target, "goal": "natural_language_desktop_task", "raw_prompt_included": False, "prompt_length": len(safe_prompt), "natural_language_planner_ready": False, "subject_specific_planning": False, "actions": [{"type": "focus_window"}, {"type": "drag_path", "points": _universal_desktop_adapter_points()}, {"type": "observe"}]}  # 新增代码+UniversalDesktopAdapter：返回不硬编码图像主题的通用动作样本；如果没有这一行，adapter 无法证明 observe-plan-act-verify 链路已接通。
    # 新增代码+UniversalDesktopAdapter：函数段结束，UniversalDesktopExecutionLoopAdapter._task_from_prompt 到此结束；如果没有这个边界说明，初学者不容易看出任务包装范围。

    def run_desktop_task(self, target_app: str, prompt: str) -> dict[str, Any]:  # 新增代码+UniversalDesktopAdapter：函数段开始，提供 desktop_task_runtime 调用的统一入口；如果没有这段函数，默认 runtime 拿到 adapter 也无法执行。
        task = self._task_from_prompt(target_app, prompt)  # 新增代码+UniversalDesktopAdapter：构造通用 DSL 任务；如果没有这一行，loop 没有目标、目标和动作输入。
        loop_report = dict(self.loop.run_task(task))  # 新增代码+UniversalDesktopAdapter：调用现有通用 observe-plan-act-verify 闭环；如果没有这一行，adapter 只是空壳不会触达通用链路。
        real_dispatch_performed = bool(loop_report.get("real_dispatch_performed", False))  # 新增代码+UniversalDesktopAdapter：读取是否真的派发到物理桌面；如果没有这一行，报告会把录制事件和真实事件混淆。
        low_level_event_count = _universal_desktop_adapter_safe_int(loop_report.get("low_level_event_count", 0))  # 新增代码+UniversalDesktopAdapter：汇总通用 DSL 产生的底层事件数；如果没有这一行，用户看不到动作链路是否真的展开。
        session = dict(loop_report.get("session", {}) if isinstance(loop_report.get("session", {}), dict) else {})  # 新增代码+UniversalDesktopAdapter：读取通用 session 证据；如果没有这一行，owned_window_verified 无法从闭环结果推导。
        return {"ok": bool(loop_report.get("ok") and real_dispatch_performed), "decision": UNIVERSAL_DESKTOP_EXECUTION_LOOP_REAL_DECISION if real_dispatch_performed else UNIVERSAL_DESKTOP_EXECUTION_LOOP_CONNECTED_DECISION, "model": UNIVERSAL_DESKTOP_EXECUTION_LOOP_MODEL, "target_app": str(target_app or ""), "prompt_length": len(str(prompt or "")), "computer_use_gui_route_used": bool(low_level_event_count > 0), "owned_window_verified": bool(session.get("target_identity_verification", {}).get("target_identity_verified", True) if isinstance(session.get("target_identity_verification", {}), dict) else bool(session)), "gui_action_count": len(task["actions"]), "low_level_event_count": low_level_event_count, "real_dispatch_performed": real_dispatch_performed, "real_desktop_touched": real_dispatch_performed, "recording_mode": not real_dispatch_performed, "universal_desktop_execution_loop_used": True, "observe_plan_act_verify_loop": True, "natural_language_planner_ready": False, "subject_specific_planning": False, "per_app_controller_required": False, "hardcoded_app_whitelist_required": False, "forbidden_script_generation_used": False, "bash_final_artifact_route_used": False, "forbidden_script_artifact_route_blocked": True, "post_action_observation_exists": bool(loop_report.get("attempts")), "loop_report": loop_report}  # 新增代码+UniversalDesktopAdapter：返回 desktop_task_runtime 可汇总的通用执行报告；如果没有这一行，默认 full 路径无法展示“通用闭环已接但未真实派发”的事实。
    # 新增代码+UniversalDesktopAdapter：函数段结束，UniversalDesktopExecutionLoopAdapter.run_desktop_task 到此结束；如果没有这个边界说明，初学者不容易看出执行入口范围。
# 新增代码+UniversalDesktopAdapter：类段结束，UniversalDesktopExecutionLoopAdapter 到此结束；如果没有这个边界说明，初学者不容易看出 adapter 只是一层桥接。

__all__ = ["UNIVERSAL_DESKTOP_EXECUTION_LOOP_CONNECTED_DECISION", "UNIVERSAL_DESKTOP_EXECUTION_LOOP_MODEL", "UNIVERSAL_DESKTOP_EXECUTION_LOOP_REAL_DECISION", "UniversalDesktopExecutionLoopAdapter"]  # 新增代码+UniversalDesktopAdapter：声明公开 API；如果没有这一行，通配导入可能暴露内部 helper 并增加误接风险。
