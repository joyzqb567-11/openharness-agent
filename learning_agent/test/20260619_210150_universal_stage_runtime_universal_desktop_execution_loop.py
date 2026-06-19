"""Universal desktop execution adapter for Computer Use full mode."""  # 新增代码+UniversalDesktopAdapter：说明本文件只负责把 /computer use --full 接到通用 observe-plan-act-verify 闭环；如果没有这一行，读者容易误以为这里是某个软件的专用控制器。
from __future__ import annotations  # 新增代码+UniversalDesktopAdapter：启用延迟类型注解，避免运行时提前解析类型造成兼容问题；如果没有这一行，旧 Python 环境里前向类型更容易报错。
import hashlib  # 新增代码+VisualPlannerLoop：导入哈希工具生成脱敏 prompt 签名；如果没有这一行，adapter 只能保留原文或无法让用户意图影响 planner。
from typing import Any  # 新增代码+UniversalDesktopAdapter：导入 Any 用来描述动态 JSON 报告；如果没有这一行，函数签名无法清楚表达报告是灵活字典。

try:  # 新增代码+UniversalDesktopAdapter：优先按包路径导入现有通用闭环；如果没有这段代码，项目根目录运行时无法复用已完成的 Phase119 能力。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_action_dsl import UniversalActionDslRuntime  # 新增代码+ControlledPhysicalAdapter：导入通用动作 DSL 以便注入受控物理 sender；如果没有这一行，adapter 构造时只能使用默认 recording sender。
    from learning_agent.computer_use_mcp_v2.windows_runtime.natural_language_semantic_planner import phase123_semantic_intent_from_prompt  # 新增代码+GenericSemanticPlanner：导入通用自然语言语义抽取入口；如果没有这一行，adapter 无法把 Notepad/浏览器等非绘图任务转成统一意图。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_observe_plan_act_verify import Phase120VisualTaskPlanner, UniversalObservePlanActVerifyLoop  # 修改代码+VisualPlannerLoop：导入通用 loop 和视觉 planner；如果没有这一行，adapter 仍会只用旧静态动作复制器。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_real_observation import PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MODEL, UniversalRealObservationFrameRuntime  # 新增代码+RealObservationAdapter：导入真实只读 ObservationFrame runtime 和模型名；如果没有这一行，默认 full 路径会继续只能接录制观察。
    from learning_agent.computer_use_mcp_v2.windows_runtime.stage_task_loop import UniversalStageTaskLoop  # 新增代码+StageTaskAdapter：导入通用阶段任务循环；如果没有这一行，生产 full mode 无法从 primitive loop 升级到阶段批执行。
    from learning_agent.computer_use_mcp_v2.windows_runtime.universal_target_session import UniversalTargetSessionRuntime  # 新增代码+RealLaunchTargetSession：导入通用目标 session runtime；如果没有这一行，adapter 无法显式启用真实应用启动。
    from learning_agent.computer_use_mcp_v2.windows_runtime.visual_semantic_planner import phase122_visual_intent_from_prompt  # 新增代码+VisualSemanticPlanner：导入脱敏视觉意图抽取函数；如果没有这一行，adapter 无法把中文房子 prompt 传给语义 planner。
    from learning_agent.computer_use_mcp_v2.windows_runtime.paint_pikachu_real_loop import WindowsPaintPikachuRealExecutionLoop  # 新增代码+FullPaintDrawingBridge：导入受支持 Paint 绘图真实闭环；如果没有这一行，默认 /computer use --full 无法打开真实 Paint 绘制已支持对象。
except ModuleNotFoundError as error:  # 新增代码+UniversalDesktopAdapter：兼容 start_oauth_agent.bat 从 learning_agent 目录启动时的脚本模式；如果没有这一行，真实可见终端入口可能因包名前缀不同而失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_action_dsl", "learning_agent.computer_use_mcp_v2.windows_runtime.natural_language_semantic_planner", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_observe_plan_act_verify", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_real_observation", "learning_agent.computer_use_mcp_v2.windows_runtime.stage_task_loop", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_target_session", "learning_agent.computer_use_mcp_v2.windows_runtime.visual_semantic_planner", "learning_agent.computer_use_mcp_v2.windows_runtime.paint_pikachu_real_loop"}:  # 修改代码+StageTaskAdapter：脚本模式兜底名单加入阶段任务循环；如果没有这一行，bat 入口可能因新模块包前缀失败。
        raise  # 新增代码+UniversalDesktopAdapter：重新抛出非路径类导入错误；如果没有这一行，排查真实依赖问题会非常困难。
    from computer_use_mcp_v2.windows_runtime.universal_action_dsl import UniversalActionDslRuntime  # type: ignore  # 新增代码+ControlledPhysicalAdapter：脚本模式导入通用动作 DSL；如果没有这一行，真实终端入口无法创建注入 sender 的动作 runtime。
    from computer_use_mcp_v2.windows_runtime.natural_language_semantic_planner import phase123_semantic_intent_from_prompt  # type: ignore  # 新增代码+GenericSemanticPlanner：脚本模式导入通用语义抽取入口；如果没有这一行，真实 bat 入口无法识别非绘图桌面任务。
    from computer_use_mcp_v2.windows_runtime.universal_observe_plan_act_verify import Phase120VisualTaskPlanner, UniversalObservePlanActVerifyLoop  # type: ignore  # 修改代码+VisualPlannerLoop：脚本模式下导入视觉 planner 和通用闭环；如果没有这一行，真实 bat 入口不会走新规划器。
    from computer_use_mcp_v2.windows_runtime.universal_real_observation import PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MODEL, UniversalRealObservationFrameRuntime  # type: ignore  # 新增代码+RealObservationAdapter：脚本模式导入真实只读观察 runtime；如果没有这一行，可见终端默认路径仍会回到录制观察。
    from computer_use_mcp_v2.windows_runtime.stage_task_loop import UniversalStageTaskLoop  # type: ignore  # 新增代码+StageTaskAdapter：脚本模式导入通用阶段任务循环；如果没有这一行，真实终端入口无法使用阶段批执行。
    from computer_use_mcp_v2.windows_runtime.universal_target_session import UniversalTargetSessionRuntime  # type: ignore  # 新增代码+RealLaunchTargetSession：脚本模式导入目标 session runtime；如果没有这一行，真实终端入口无法启用真实启动。
    from computer_use_mcp_v2.windows_runtime.visual_semantic_planner import phase122_visual_intent_from_prompt  # type: ignore  # 新增代码+VisualSemanticPlanner：脚本模式导入脱敏视觉意图抽取函数；如果没有这一行，真实终端入口不能识别房子语义。
    from computer_use_mcp_v2.windows_runtime.paint_pikachu_real_loop import WindowsPaintPikachuRealExecutionLoop  # type: ignore  # 新增代码+FullPaintDrawingBridge：脚本模式导入 Paint 绘图闭环；如果没有这一行，start_oauth_agent.bat 下无法真实打开 Paint 绘制已支持对象。

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

def _universal_desktop_adapter_observation_frames(loop_report: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+RealObservationAdapter：函数段开始，从 loop_report 中收集动作前后观察帧；如果没有这个函数，adapter 无法诚实统计是否真的使用了只读屏幕/窗口观察。
    frames: list[dict[str, Any]] = []  # 新增代码+RealObservationAdapter：创建观察帧列表；如果没有这一行，后续遍历没有稳定容器。
    for attempt in list(loop_report.get("attempts", []) or []):  # 新增代码+RealObservationAdapter：逐个读取闭环尝试记录；如果没有这一行，只能看到顶层结果，看不到每轮观察。
        if not isinstance(attempt, dict):  # 新增代码+RealObservationAdapter：跳过坏格式 attempt；如果没有这一行，异常报告可能让汇总崩溃。
            continue  # 新增代码+RealObservationAdapter：忽略非字典记录并继续；如果没有这一行，单个坏项会中断整个桌面任务报告。
        for frame_key in ("before_observation", "after_observation"):  # 新增代码+RealObservationAdapter：检查每轮尝试的前后观察；如果没有这一行，任务级观察会被漏掉。
            frame = attempt.get(frame_key)  # 新增代码+RealObservationAdapter：读取当前观察字段；如果没有这一行，无法判断字段是否存在。
            if isinstance(frame, dict):  # 新增代码+RealObservationAdapter：只收集字典形态的观察帧；如果没有这一行，字符串或空值会污染统计。
                frames.append(dict(frame))  # 新增代码+RealObservationAdapter：复制观察帧进入列表；如果没有这一行，后续修改可能影响原始 loop_report。
        for step in list(attempt.get("steps", []) or []):  # 新增代码+RealObservationAdapter：逐个读取动作级记录；如果没有这一行，每个动作前后的实时观察会被漏掉。
            if not isinstance(step, dict):  # 新增代码+RealObservationAdapter：跳过坏格式 step；如果没有这一行，异常动作记录可能让统计失败。
                continue  # 新增代码+RealObservationAdapter：忽略非字典动作记录；如果没有这一行，后续 get 调用可能报错。
            for frame_key in ("before_observation", "after_observation"):  # 新增代码+RealObservationAdapter：检查动作前后观察；如果没有这一行，闭环是否持续看屏幕无法被证明。
                frame = step.get(frame_key)  # 新增代码+RealObservationAdapter：读取动作级观察字段；如果没有这一行，无法提取当前帧。
                if isinstance(frame, dict):  # 新增代码+RealObservationAdapter：确认观察帧是字典；如果没有这一行，坏值会污染统计。
                    frames.append(dict(frame))  # 新增代码+RealObservationAdapter：复制动作级观察帧；如果没有这一行，真实 observation 证据无法进入 adapter 汇总。
    return frames  # 新增代码+RealObservationAdapter：返回收集到的全部观察帧；如果没有这一行，调用方拿不到统计输入。
# 新增代码+RealObservationAdapter：函数段结束，_universal_desktop_adapter_observation_frames 到此结束；如果没有这个边界说明，初学者不容易看出观察帧收集范围。

def _universal_desktop_adapter_observation_summary(loop_report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+RealObservationAdapter：函数段开始，把观察帧压缩成可验收字段；如果没有这个函数，终端输出只能翻很长 JSON 才知道是否真的看屏幕。
    frames = _universal_desktop_adapter_observation_frames(loop_report)  # 新增代码+RealObservationAdapter：读取闭环中的全部观察帧；如果没有这一行，summary 没有事实来源。
    real_model_used = any(frame.get("model") == PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MODEL for frame in frames)  # 新增代码+RealObservationAdapter：检查是否出现 URG-1 真实观察帧模型；如果没有这一行，录制帧也会被误算成真实观察。
    return {"observation_frame_count": len(frames), "real_observation_runtime_used": real_model_used, "real_observation_frame_used": any(bool(frame.get("real_observation_frame")) for frame in frames), "read_only_real_observation_used": bool(real_model_used and not loop_report.get("real_dispatch_performed", False)), "real_screenshot_pipeline_used": any(bool(frame.get("real_screenshot_pipeline_used")) for frame in frames), "real_uia_provider_used": any(bool(frame.get("real_uia_provider_used")) for frame in frames), "screenshot_observation": any(bool(frame.get("screenshot_observation")) for frame in frames), "uia_tree_observation": any(bool(frame.get("uia_tree_observation")) for frame in frames), "window_state_observation": any(bool(frame.get("window_state_observation")) for frame in frames), "uia_or_vision_targeting": any(bool(frame.get("uia_or_vision_targeting")) for frame in frames)}  # 新增代码+RealObservationAdapter：返回终端和矩阵可直接读取的观察汇总；如果没有这一行，用户无法一眼区分真实只读观察和录制观察。
# 新增代码+RealObservationAdapter：函数段结束，_universal_desktop_adapter_observation_summary 到此结束；如果没有这个边界说明，初学者不容易看出观察汇总范围。

def _universal_desktop_adapter_sender_reports(loop_report: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+ControlledPhysicalAdapter：函数段开始，从 loop_report 里收集每个动作的低层 sender 报告；如果没有这段函数，adapter 无法判断受控 sender 是否真的被使用。
    reports: list[dict[str, Any]] = []  # 新增代码+ControlledPhysicalAdapter：准备保存 sender 报告列表；如果没有这一行，后续遍历没有容器。
    for attempt in list(loop_report.get("attempts", []) or []):  # 新增代码+ControlledPhysicalAdapter：逐轮读取闭环尝试记录；如果没有这一行，只能看到顶层结果而看不到动作级 sender。
        if not isinstance(attempt, dict):  # 新增代码+ControlledPhysicalAdapter：跳过坏格式尝试记录；如果没有这一行，异常报告可能打断汇总。
            continue  # 新增代码+ControlledPhysicalAdapter：忽略非字典 attempt；如果没有这一行，后续 get 调用可能报错。
        for step in list(attempt.get("steps", []) or []):  # 新增代码+ControlledPhysicalAdapter：逐个读取动作步骤；如果没有这一行，多动作任务的 sender 事实会漏掉。
            if not isinstance(step, dict):  # 新增代码+ControlledPhysicalAdapter：跳过坏格式 step；如果没有这一行，异常步骤会打断汇总。
                continue  # 新增代码+ControlledPhysicalAdapter：忽略非字典 step；如果没有这一行，后续读取 dispatch 可能失败。
            dispatch = step.get("dispatch", {})  # 新增代码+ControlledPhysicalAdapter：读取动作分发结果；如果没有这一行，sender 报告没有来源。
            if not isinstance(dispatch, dict):  # 新增代码+ControlledPhysicalAdapter：确认 dispatch 是字典；如果没有这一行，坏值可能污染报告。
                continue  # 新增代码+ControlledPhysicalAdapter：忽略非字典 dispatch；如果没有这一行，后续嵌套读取会报错。
            inner_dispatch = dispatch.get("dispatch", {})  # 新增代码+ControlledPhysicalAdapter：读取 URG-3 内部 dispatcher 报告；如果没有这一行，拿不到 Phase47 的 sender 字段。
            if not isinstance(inner_dispatch, dict):  # 新增代码+ControlledPhysicalAdapter：确认内部 dispatch 是字典；如果没有这一行，坏值可能导致异常。
                continue  # 新增代码+ControlledPhysicalAdapter：忽略非字典内部 dispatch；如果没有这一行，后续 sender 读取会失败。
            sender = inner_dispatch.get("sender", {})  # 新增代码+ControlledPhysicalAdapter：读取最后一跳 sender 报告；如果没有这一行，无法证明受控物理 sender 是否被触达。
            if isinstance(sender, dict):  # 新增代码+ControlledPhysicalAdapter：只收集字典形态 sender 报告；如果没有这一行，字符串或空值会污染汇总。
                reports.append(dict(sender))  # 新增代码+ControlledPhysicalAdapter：复制保存 sender 报告；如果没有这一行，后续修改可能影响原始 loop_report。
    return reports  # 新增代码+ControlledPhysicalAdapter：返回所有动作的 sender 报告；如果没有这一行，adapter 报告无法形成受控 sender 汇总。
# 新增代码+ControlledPhysicalAdapter：函数段结束，_universal_desktop_adapter_sender_reports 到此结束；如果没有这个边界说明，初学者不容易看出 sender 报告收集范围。

def _universal_desktop_adapter_controlled_sender_summary(loop_report: dict[str, Any], configured: bool) -> dict[str, Any]:  # 新增代码+ControlledPhysicalAdapter：函数段开始，生成受控物理 sender 汇总字段；如果没有这段函数，用户无法区分“已配置、已使用、已触桌面”三件事。
    sender_reports = _universal_desktop_adapter_sender_reports(loop_report)  # 新增代码+ControlledPhysicalAdapter：收集动作级 sender 报告；如果没有这一行，summary 没有事实来源。
    controlled_used = any(str(report.get("sender", "")) == "phase95_controlled_physical_sendinput" or bool(report.get("controlled_physical_sender_ready")) for report in sender_reports)  # 新增代码+ControlledPhysicalAdapter：判断是否走过 Phase95 受控 sender；如果没有这一行，配置了但未使用的问题不可见。
    backend_reached = any(bool(report.get("backend_dispatch_performed")) for report in sender_reports)  # 新增代码+ControlledPhysicalAdapter：判断最后一跳后端是否收到事件；如果没有这一行，sender 可能只做表面验证。
    real_touched = any(bool(report.get("real_desktop_touched") or report.get("real_dispatch_performed")) for report in sender_reports)  # 新增代码+ControlledPhysicalAdapter：判断 sender 是否声明真实桌面触碰；如果没有这一行，fake 后端和真实后端会混淆。
    return {"controlled_physical_sender_configured": bool(configured), "controlled_physical_sender_used": bool(controlled_used), "controlled_physical_backend_reached": bool(backend_reached), "controlled_physical_sender_real_desktop_touched": bool(real_touched), "controlled_physical_dispatch_default_off": not bool(configured)}  # 新增代码+ControlledPhysicalAdapter：返回 adapter 可直接展示的受控 sender 汇总；如果没有这一行，用户看不到当前物理派发接线状态。
# 新增代码+ControlledPhysicalAdapter：函数段结束，_universal_desktop_adapter_controlled_sender_summary 到此结束；如果没有这个边界说明，初学者不容易看出受控 sender 汇总范围。


def _universal_desktop_adapter_stage_action_reports(stage_report: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+StageTaskAdapter：函数段开始，从阶段报告里提取动作级结果；如果没有这段函数，adapter 无法汇总 stage loop 的真实派发证据。
    reports: list[dict[str, Any]] = []  # 新增代码+StageTaskAdapter：初始化动作结果列表；如果没有这一行，后续遍历没有稳定容器。
    for result in list(stage_report.get("stage_results", []) or []):  # 新增代码+StageTaskAdapter：遍历每个阶段结果；如果没有这一行，只能看到顶层 stage_count，看不到动作执行事实。
        if not isinstance(result, dict):  # 新增代码+StageTaskAdapter：跳过坏格式阶段结果；如果没有这一行，异常字段会导致 get 调用失败。
            continue  # 新增代码+StageTaskAdapter：继续处理其它阶段；如果没有这一行，一个坏阶段会中断整个汇总。
        evidence = result.get("evidence", {})  # 新增代码+StageTaskAdapter：读取阶段证据；如果没有这一行，动作结果没有来源。
        if not isinstance(evidence, dict):  # 新增代码+StageTaskAdapter：确认阶段证据是字典；如果没有这一行，坏证据可能污染报告。
            continue  # 新增代码+StageTaskAdapter：跳过坏证据；如果没有这一行，后续读取 action_results 会报错。
        for action_report in list(evidence.get("action_results", []) or []):  # 新增代码+StageTaskAdapter：遍历阶段内 primitive 动作结果；如果没有这一行，adapter 无法判断是否真的发送了输入。
            if isinstance(action_report, dict):  # 新增代码+StageTaskAdapter：只收集字典动作结果；如果没有这一行，字符串或空值会污染汇总。
                reports.append(dict(action_report))  # 新增代码+StageTaskAdapter：复制动作结果；如果没有这一行，后续处理可能修改原始阶段报告。
    return reports  # 新增代码+StageTaskAdapter：返回所有动作结果；如果没有这一行，调用方拿不到 stage loop 派发事实。
# 新增代码+StageTaskAdapter：函数段结束，_universal_desktop_adapter_stage_action_reports 到此结束；如果没有这个边界说明，初学者不容易看出动作提取范围。


def _universal_desktop_adapter_stage_sender_summary(stage_report: dict[str, Any], configured: bool) -> dict[str, Any]:  # 新增代码+StageTaskAdapter：函数段开始，汇总阶段循环里的受控 sender 和真实派发；如果没有这段函数，stage loop 顶层报告会缺少物理执行事实。
    action_reports = _universal_desktop_adapter_stage_action_reports(stage_report)  # 新增代码+StageTaskAdapter：读取动作级结果；如果没有这一行，summary 没有证据来源。
    sender_reports: list[dict[str, Any]] = []  # 新增代码+StageTaskAdapter：初始化 sender 报告列表；如果没有这一行，后续无法汇总后端状态。
    for action_report in action_reports:  # 新增代码+StageTaskAdapter：逐个处理动作报告；如果没有这一行，多个 primitive 的 sender 事实会丢失。
        dispatch = action_report.get("dispatch", {})  # 新增代码+StageTaskAdapter：读取动作分发结果；如果没有这一行，sender 嵌套报告没有来源。
        if isinstance(dispatch, dict) and isinstance(dispatch.get("sender", {}), dict):  # 新增代码+StageTaskAdapter：确认 dispatch 里有 sender 字典；如果没有这一行，坏格式会让汇总误判。
            sender_reports.append(dict(dispatch.get("sender", {})))  # 新增代码+StageTaskAdapter：保存 sender 报告；如果没有这一行，受控 sender 是否被使用不可见。
    real_dispatch = any(bool(report.get("real_desktop_touched") or report.get("real_dispatch_performed")) for report in action_reports + sender_reports)  # 新增代码+StageTaskAdapter：汇总是否真实触达桌面；如果没有这一行，stage loop 可能被误当 recording 或误当真实。
    controlled_used = any(str(report.get("sender", "")) == "phase95_controlled_physical_sendinput" or bool(report.get("controlled_physical_sender_ready")) for report in sender_reports)  # 新增代码+StageTaskAdapter：判断受控 sender 是否参与；如果没有这一行，adapter 无法证明阶段批仍经过安全 sender。
    backend_reached = any(bool(report.get("backend_dispatch_performed")) for report in sender_reports)  # 新增代码+StageTaskAdapter：判断底层后端是否收到事件；如果没有这一行，sender 可能只做了表面检查。
    return {"real_dispatch_performed": bool(real_dispatch), "real_desktop_touched": bool(real_dispatch), "controlled_physical_sender_configured": bool(configured), "controlled_physical_sender_used": bool(controlled_used), "controlled_physical_backend_reached": bool(backend_reached), "controlled_physical_sender_real_desktop_touched": bool(real_dispatch), "controlled_physical_dispatch_default_off": not bool(configured)}  # 新增代码+StageTaskAdapter：返回 stage loop 物理派发汇总；如果没有这一行，桌面任务 runtime 无法判断真实动作是否成熟。
# 新增代码+StageTaskAdapter：函数段结束，_universal_desktop_adapter_stage_sender_summary 到此结束；如果没有这个边界说明，初学者不容易看出 sender 汇总范围。


class UniversalDesktopExecutionLoopAdapter:  # 新增代码+UniversalDesktopAdapter：类段开始，把 desktop_task_runtime 需要的 run_desktop_task 接口桥接到通用闭环；如果没有这个类，默认 full 模式只能保持空 loop 或误接特例 loop。
    def __init__(self, loop: Any | None = None, observation_runtime: Any | None = None, use_real_observation: bool = True, controlled_physical_sender: Any | None = None, enable_real_target_launch: bool = False, target_runtime: Any | None = None, enable_supported_paint_drawing: bool = False, supported_paint_drawing_loop: Any | None = None, planner: Any | None = None, stage_task_loop: Any | None = None, use_stage_task_loop: bool | None = None) -> None:  # 修改代码+StageTaskAdapter：函数段开始，允许生产 full 路径显式启用阶段任务循环；如果没有这个参数，adapter 无法把复杂 GUI 任务从 primitive loop 迁移出来。
        real_observation_runtime = observation_runtime if observation_runtime is not None else UniversalRealObservationFrameRuntime()  # 新增代码+RealObservationAdapter：构造或复用真实只读观察 runtime；如果没有这一行，默认 full 路径仍会停在录制观察层。
        resolved_target_runtime = target_runtime if target_runtime is not None else (UniversalTargetSessionRuntime(enable_real_launch=True) if enable_real_target_launch else None)  # 新增代码+RealLaunchTargetSession：真实启动模式创建真实 target session runtime；如果没有这一行，生产 full 仍会伪造目标窗口。
        controlled_action_runtime = UniversalActionDslRuntime(target_runtime=resolved_target_runtime, low_level_sender=controlled_physical_sender) if (controlled_physical_sender is not None or resolved_target_runtime is not None) else None  # 修改代码+RealLaunchTargetSession：配置目标 runtime 或受控 sender 时创建专用动作 runtime；如果没有这一行，真实启动和物理 sender 不会进入 loop。
        resolved_planner = planner if planner is not None else Phase120VisualTaskPlanner()  # 新增代码+VisualPlannerLoop：默认使用视觉任务 planner；如果没有这一行，/computer use --full 会继续执行固定样本动作。
        default_loop = UniversalObservePlanActVerifyLoop(observation_runtime=real_observation_runtime, action_runtime=controlled_action_runtime, planner=resolved_planner, max_retries=0) if use_real_observation else UniversalObservePlanActVerifyLoop(action_runtime=controlled_action_runtime, planner=resolved_planner, max_retries=0)  # 修改代码+VisualPlannerLoop：默认闭环同时接观察层、动作层和视觉 planner；如果没有这一行，真实路线不会形成 observe-plan-act。
        self.loop = loop if loop is not None else default_loop  # 修改代码+RealObservationAdapter：优先使用外部注入 loop，否则使用真实只读观察闭环；如果没有这一行，测试和未来物理 sender 接入无法替换整条 loop。
        stage_loop_should_run = bool(stage_task_loop is not None or (bool(enable_real_target_launch) if use_stage_task_loop is None else bool(use_stage_task_loop)))  # 新增代码+StageTaskAdapter：生产真实启动路径默认启用阶段循环；如果没有这一行，full mode 会继续用 primitive loop 处理复杂任务。
        self.stage_task_loop = stage_task_loop if stage_task_loop is not None else (UniversalStageTaskLoop(observation_runtime=real_observation_runtime, target_runtime=resolved_target_runtime, action_runtime=controlled_action_runtime) if stage_loop_should_run else None)  # 新增代码+StageTaskAdapter：创建或保存阶段任务循环；如果没有这一行，adapter 无法调用新规划-观察-批执行 runtime。
        self.stage_task_loop_enabled = self.stage_task_loop is not None  # 新增代码+StageTaskAdapter：记录阶段循环是否启用；如果没有这一行，报告无法说明当前走的是新路径还是兼容旧路径。
        self.controlled_physical_sender_configured = controlled_physical_sender is not None  # 新增代码+ControlledPhysicalAdapter：记录本 adapter 是否配置受控 sender；如果没有这一行，最终报告无法解释为什么没有使用 Phase95。
        self.real_target_launch_enabled = bool(enable_real_target_launch)  # 新增代码+RealLaunchTargetSession：记录 adapter 是否启用真实目标启动；如果没有这一行，最终报告无法证明是否要求 agent 自己打开软件。
        self.supported_paint_drawing_loop = supported_paint_drawing_loop if supported_paint_drawing_loop is not None else (WindowsPaintPikachuRealExecutionLoop() if enable_supported_paint_drawing else None)  # 新增代码+FullPaintDrawingBridge：仅在显式开启时创建真实 Paint 绘图闭环；如果没有这一行，生产 full 路径无法处理猫/大象/皮卡丘真实绘图。
        self.supported_paint_drawing_enabled = self.supported_paint_drawing_loop is not None  # 新增代码+FullPaintDrawingBridge：记录本 adapter 是否启用受支持 Paint 绘图桥；如果没有这一行，报告无法解释为什么同一 adapter 有时会真实打开 Paint。
    # 新增代码+UniversalDesktopAdapter：函数段结束，UniversalDesktopExecutionLoopAdapter.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出依赖注入范围。

    def _task_from_prompt(self, target_app: str, prompt: str) -> dict[str, Any]:  # 新增代码+UniversalDesktopAdapter：函数段开始，把自然语言任务包装成通用 DSL 任务；如果没有这段函数，desktop runtime 无法把用户意图交给 Phase119。
        safe_target = str(target_app or "desktop_app").strip() or "desktop_app"  # 新增代码+UniversalDesktopAdapter：清洗目标应用名并提供兜底；如果没有这一行，空目标会让 session 建立报告不稳定。
        safe_prompt = str(prompt or "")  # 新增代码+UniversalDesktopAdapter：把用户输入统一成字符串；如果没有这一行，None 输入会污染报告和哈希字段。
        prompt_signature = hashlib.sha256(safe_prompt.encode("utf-8", "replace")).hexdigest()[:16]  # 新增代码+VisualPlannerLoop：生成不泄露原文的 prompt 签名；如果没有这一行，planner 无法在保护原文的同时区分不同任务。
        semantic_intent = phase123_semantic_intent_from_prompt(safe_prompt, safe_target)  # 新增代码+GenericSemanticPlanner：先抽取通用任务意图；如果没有这一行，Notepad/浏览器等任务仍会被误当成视觉绘图任务。
        visual_intent = phase122_visual_intent_from_prompt(safe_prompt) if str(semantic_intent.get("task_kind", "")) == "draw" else {"subject": "generic", "drawing_requested": False, "raw_prompt_included": False, "known_subject": False}  # 修改代码+GenericSemanticPlanner：只有绘图任务才抽取视觉主题；如果没有这一行，打开记事本也会携带误导性的绘图意图。
        visual_requested = str(semantic_intent.get("task_kind", "")) == "draw"  # 新增代码+GenericSemanticPlanner：把是否需要视觉绘图规划写成显式布尔值；如果没有这一行，非绘图任务会继续触发 drag_path 兜底。
        return {"target": safe_target, "goal": "natural_language_desktop_task", "raw_prompt_included": False, "prompt_length": len(safe_prompt), "prompt_signature": prompt_signature, "semantic_intent": dict(semantic_intent), "semantic_task_kind": str(semantic_intent.get("task_kind", "")), "visual_planning_requested": visual_requested, "visual_subject_hint": str(visual_intent.get("subject", "generic")), "visual_intent": dict(visual_intent), "natural_language_planner_ready": True, "subject_specific_planning": False}  # 修改代码+GenericSemanticPlanner：返回通用语义意图和仅绘图时的视觉意图；如果没有这一行，adapter 会继续把所有自然语言硬塞进视觉 planner。
    # 新增代码+UniversalDesktopAdapter：函数段结束，UniversalDesktopExecutionLoopAdapter._task_from_prompt 到此结束；如果没有这个边界说明，初学者不容易看出任务包装范围。

    def run_desktop_task(self, target_app: str, prompt: str) -> dict[str, Any]:  # 新增代码+UniversalDesktopAdapter：函数段开始，提供 desktop_task_runtime 调用的统一入口；如果没有这段函数，默认 runtime 拿到 adapter 也无法执行。
        if self.stage_task_loop is not None:  # 新增代码+StageTaskAdapter：生产阶段循环启用时优先走通用 stage runtime；如果没有这一行，复杂任务会继续落回 primitive loop。
            stage_report = dict(self.stage_task_loop.run_desktop_task(prompt, target_hint=target_app))  # 新增代码+StageTaskAdapter：运行通用阶段计划、观察、批执行和验证；如果没有这一行，新 runtime 不会被主入口调用。
            sender_summary = _universal_desktop_adapter_stage_sender_summary(stage_report, self.controlled_physical_sender_configured)  # 新增代码+StageTaskAdapter：汇总阶段批的受控 sender 和真实派发证据；如果没有这一行，desktop_task_runtime 无法判断真实动作。
            low_level_event_count = _universal_desktop_adapter_safe_int(stage_report.get("low_level_event_count", 0))  # 新增代码+StageTaskAdapter：读取阶段循环低层事件数；如果没有这一行，GUI 路由证据缺动作规模。
            primitive_action_count = _universal_desktop_adapter_safe_int(stage_report.get("primitive_action_count", 0))  # 新增代码+StageTaskAdapter：读取阶段循环 primitive 数；如果没有这一行，旧 gui_action_count 字段无法兼容。
            adapter_ok = bool(stage_report.get("desktop_task_completed") and low_level_event_count > 0 and stage_report.get("owned_window_verified", False))  # 新增代码+StageTaskAdapter：只有阶段完成、有事件、有目标身份才算 adapter 成功；如果没有这一行，未完成阶段可能被误报成功。
            adapter_report = dict(stage_report)  # 新增代码+StageTaskAdapter：先复制阶段报告；如果没有这一行，后续兼容字段会直接污染原始 stage_report。
            adapter_report.update({"decision": str(stage_report.get("decision", "desktop_task_incomplete")), "model": UNIVERSAL_DESKTOP_EXECUTION_LOOP_MODEL, "target_app": str(target_app or ""), "prompt_length": len(str(prompt or "")), "computer_use_gui_route_used": bool(low_level_event_count > 0), "owned_window_verified": bool(stage_report.get("owned_window_verified", False)), "gui_action_count": primitive_action_count, "low_level_event_count": low_level_event_count, "recording_mode": not bool(sender_summary.get("real_dispatch_performed", False)), "real_target_launch_enabled": self.real_target_launch_enabled, "universal_desktop_execution_loop_used": True, "observe_plan_act_verify_loop": False, "stage_task_loop_primary": True, "planner_model": "universal_desktop_stage_planner", "planned_action_count": primitive_action_count, "visual_planner_connected": False, "visual_planner_used": False, "visual_planner_mature": False, "natural_language_planner_ready": True, "subject_specific_planning": False, "per_app_controller_required": False, "hardcoded_app_whitelist_required": False, "forbidden_script_generation_used": False, "bash_final_artifact_route_used": False, "forbidden_script_artifact_route_blocked": True, "physical_dispatch_required": True, "post_action_observation_exists": bool(stage_report.get("observation_frame_count", 0))})  # 新增代码+StageTaskAdapter：补齐旧运行时和验收器需要的顶层字段；如果没有这一行，现有 CLI/矩阵无法读取新 stage 证据。
            adapter_report.update(sender_summary)  # 新增代码+StageTaskAdapter：合并受控 sender 和真实派发摘要；如果没有这一行，真实动作路径是否触达后端不可见。
            adapter_report["ok"] = adapter_ok  # 新增代码+StageTaskAdapter：使用 adapter 严格成功条件覆盖 stage 自身 ok；如果没有这一行，只有阶段完成但无真实目标/事件也可能误成功。
            return adapter_report  # 新增代码+StageTaskAdapter：返回兼容旧字段和新阶段字段的报告；如果没有这一行，final gate 和可见终端都拿不到完整证据。
        if self.supported_paint_drawing_loop is not None and str(target_app or "").strip().lower() == "mspaint":  # 新增代码+FullPaintDrawingBridge：Paint 绘图任务先尝试已支持对象真实闭环；如果没有这一行，猫/大象/皮卡丘会落回只观察不派发的通用样本。
            paint_report = dict(self.supported_paint_drawing_loop.run_desktop_task(target_app, prompt))  # 新增代码+FullPaintDrawingBridge：调用真实 Paint loop 并复制报告；如果没有这一行，adapter 不能把自然语言绘图任务交给真实桌面。
            if str(paint_report.get("decision", "")) != "paint_drawing_subject_not_supported":  # 新增代码+FullPaintDrawingBridge：只在对象已支持时直接返回 Paint 结果；如果没有这一行，未知对象也会被 Paint 拒绝报告吞掉而无法进入通用回退。
                paint_report["universal_desktop_execution_loop_used"] = True  # 新增代码+FullPaintDrawingBridge：标记请求仍经过 full adapter 主入口；如果没有这一行，终端报告会看不出这是 /computer use --full 默认链路。
                paint_report["supported_paint_drawing_bridge_used"] = True  # 新增代码+FullPaintDrawingBridge：标记本次使用的是有限 Paint 绘图桥；如果没有这一行，用户可能误以为已经具备任意绘图能力。
                paint_report["subject_specific_planning"] = True  # 新增代码+FullPaintDrawingBridge：诚实标记当前仍是对象特定计划；如果没有这一行，成熟度会被误读成通用自然语言规划。
                paint_report["natural_language_planner_ready"] = False  # 新增代码+FullPaintDrawingBridge：声明任意自然语言视觉规划器尚未完成；如果没有这一行，报告会高估当前能力边界。
                paint_report["per_app_controller_required"] = False  # 新增代码+FullPaintDrawingBridge：说明这里是 full adapter 显式桥接而非重新要求用户批准每个 app；如果没有这一行，后续可能误退回 per-app allowlist 设计。
                paint_report["hardcoded_app_whitelist_required"] = False  # 新增代码+FullPaintDrawingBridge：说明启动仍走通用发现和安全后端；如果没有这一行，报告会让人误解为硬编码白名单方案复活。
                return paint_report  # 新增代码+FullPaintDrawingBridge：返回真实 Paint 执行报告；如果没有这一行，已经成功画猫也会继续落入通用录制路径。
        task = self._task_from_prompt(target_app, prompt)  # 新增代码+UniversalDesktopAdapter：构造通用 DSL 任务；如果没有这一行，loop 没有目标、目标和动作输入。
        loop_report = dict(self.loop.run_task(task))  # 新增代码+UniversalDesktopAdapter：调用现有通用 observe-plan-act-verify 闭环；如果没有这一行，adapter 只是空壳不会触达通用链路。
        real_dispatch_performed = bool(loop_report.get("real_dispatch_performed", False))  # 新增代码+UniversalDesktopAdapter：读取是否真的派发到物理桌面；如果没有这一行，报告会把录制事件和真实事件混淆。
        low_level_event_count = _universal_desktop_adapter_safe_int(loop_report.get("low_level_event_count", 0))  # 新增代码+UniversalDesktopAdapter：汇总通用 DSL 产生的底层事件数；如果没有这一行，用户看不到动作链路是否真的展开。
        session = dict(loop_report.get("session", {}) if isinstance(loop_report.get("session", {}), dict) else {})  # 新增代码+UniversalDesktopAdapter：读取通用 session 证据；如果没有这一行，owned_window_verified 无法从闭环结果推导。
        observation_summary = _universal_desktop_adapter_observation_summary(loop_report)  # 新增代码+RealObservationAdapter：汇总真实只读 observation 证据；如果没有这一行，报告无法证明本阶段已经先补上“眼睛”。
        controlled_sender_summary = _universal_desktop_adapter_controlled_sender_summary(loop_report, self.controlled_physical_sender_configured)  # 新增代码+ControlledPhysicalAdapter：汇总受控 sender 接线状态；如果没有这一行，用户无法看到 Phase95 是否接到主链路。
        return {"ok": bool(loop_report.get("ok") and real_dispatch_performed), "decision": UNIVERSAL_DESKTOP_EXECUTION_LOOP_REAL_DECISION if real_dispatch_performed else UNIVERSAL_DESKTOP_EXECUTION_LOOP_CONNECTED_DECISION, "model": UNIVERSAL_DESKTOP_EXECUTION_LOOP_MODEL, "target_app": str(target_app or ""), "prompt_length": len(str(prompt or "")), "computer_use_gui_route_used": bool(low_level_event_count > 0), "owned_window_verified": bool(session.get("target_identity_verification", {}).get("target_identity_verified", True) if isinstance(session.get("target_identity_verification", {}), dict) else bool(session)), "gui_action_count": _universal_desktop_adapter_safe_int(loop_report.get("planned_action_count", 0)), "low_level_event_count": low_level_event_count, "real_dispatch_performed": real_dispatch_performed, "real_desktop_touched": real_dispatch_performed, "recording_mode": not real_dispatch_performed, "real_target_launch_enabled": self.real_target_launch_enabled, "real_launch_performed": bool(session.get("real_launch_performed")), "backend_launch_performed": bool(session.get("backend_launch_performed")), "process_started": bool(session.get("process_started")), "owned_process_registered": bool(session.get("owned_process_registered")), "visible_window_verified": bool(session.get("visible_window_verified")), "universal_desktop_execution_loop_used": True, "observe_plan_act_verify_loop": True, "planner_model": str(loop_report.get("planner_model", "")), "planned_action_count": _universal_desktop_adapter_safe_int(loop_report.get("planned_action_count", 0)), "visual_planner_connected": bool(loop_report.get("visual_planner_connected", False)), "visual_planner_used": bool(loop_report.get("visual_planner_used", False)), "visual_planner_mature": False, "natural_language_planner_ready": bool(loop_report.get("visual_planner_connected", False)), "subject_specific_planning": False, "per_app_controller_required": False, "hardcoded_app_whitelist_required": False, "forbidden_script_generation_used": False, "bash_final_artifact_route_used": False, "forbidden_script_artifact_route_blocked": True, "physical_dispatch_required": True, "post_action_observation_exists": bool(loop_report.get("attempts")), **observation_summary, **controlled_sender_summary, "loop_report": loop_report}  # 修改代码+VisualPlannerLoop：返回真实启动、窗口绑定、观察、受控 sender 和视觉 planner 汇总；如果没有这一行，终端验收无法证明自然语言任务进入通用视觉规划 loop。
    # 新增代码+UniversalDesktopAdapter：函数段结束，UniversalDesktopExecutionLoopAdapter.run_desktop_task 到此结束；如果没有这个边界说明，初学者不容易看出执行入口范围。
# 新增代码+UniversalDesktopAdapter：类段结束，UniversalDesktopExecutionLoopAdapter 到此结束；如果没有这个边界说明，初学者不容易看出 adapter 只是一层桥接。

__all__ = ["UNIVERSAL_DESKTOP_EXECUTION_LOOP_CONNECTED_DECISION", "UNIVERSAL_DESKTOP_EXECUTION_LOOP_MODEL", "UNIVERSAL_DESKTOP_EXECUTION_LOOP_REAL_DECISION", "UniversalDesktopExecutionLoopAdapter"]  # 新增代码+UniversalDesktopAdapter：声明公开 API；如果没有这一行，通配导入可能暴露内部 helper 并增加误接风险。
