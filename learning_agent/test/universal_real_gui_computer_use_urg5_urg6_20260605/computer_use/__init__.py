"""Computer Use package exports."""  # 修改代码+URG4ObservePlanActVerify：说明本文件只负责包级公开 API 导出；如果没有这行代码，读者不容易区分导出文件和业务实现文件。
from learning_agent.computer_use.mode_session import DEFAULT_MODE_SESSION_ID  # 修改代码+URG4ObservePlanActVerify：继续导出 Phase98 默认 session id；如果没有这行代码，旧的 full-mode session 调用会断。
from learning_agent.computer_use.mode_session import DEFAULT_MODE_SESSION_ROOT  # 修改代码+URG4ObservePlanActVerify：继续导出 Phase98 默认 session 根目录；如果没有这行代码，旧代码无法定位模式状态。
from learning_agent.computer_use.mode_session import PHASE98_COMPUTER_USE_MODE_MODEL  # 修改代码+URG4ObservePlanActVerify：继续导出 Phase98 模型名；如果没有这行代码，状态 UI 和测试会缺少稳定模型字段。
from learning_agent.computer_use.mode_session import PHASE98_COMPUTER_USE_MODE_OK  # 修改代码+URG4ObservePlanActVerify：继续导出 Phase98 OK token；如果没有这行代码，旧验收场景可能无法匹配 full mode 成功。
from learning_agent.computer_use.mode_session import PHASE98_COMPUTER_USE_MODE_READY  # 修改代码+URG4ObservePlanActVerify：继续导出 Phase98 ready marker；如果没有这行代码，旧可见终端场景会缺少等待锚点。
from learning_agent.computer_use.mode_session import ComputerUseModeSessionStore  # 修改代码+URG4ObservePlanActVerify：继续导出 full-mode session store；如果没有这行代码，交互命令无法复用包级入口。
from learning_agent.computer_use.universal_live_execution import UniversalWindowsLiveExecutionGate  # 修改代码+URG4ObservePlanActVerify：继续导出 Phase93/102 通用 live execution gate；如果没有这行代码，既有通用执行入口会断。
from learning_agent.computer_use.universal_real_observation import PHASE116_ACTIONS_EXPANDED  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-1 动作扩展边界；如果没有这行代码，外部无法确认观察阶段没有动作。
from learning_agent.computer_use.universal_real_observation import PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MARKER  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-1 ready marker；如果没有这行代码，观察帧验收无法从包级入口读取 marker。
from learning_agent.computer_use.universal_real_observation import PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MODEL  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-1 模型名；如果没有这行代码，后续矩阵无法识别观察帧版本。
from learning_agent.computer_use.universal_real_observation import PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_OK_TOKEN  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-1 OK token；如果没有这行代码，观察帧验收无法匹配成功。
from learning_agent.computer_use.universal_real_observation import UniversalRealObservationFrameRuntime  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-1 runtime；如果没有这行代码，后续闭环无法从包级入口组合观察层。
from learning_agent.computer_use.universal_real_observation import run_universal_real_observation_frame_contract  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-1 合同自检；如果没有这行代码，外部无法复用观察帧验收事实源。
from learning_agent.computer_use.universal_real_observation import universal_real_observation_frame_cli_line  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-1 CLI 行生成器；如果没有这行代码，场景文件容易重复拼接 token。
from learning_agent.computer_use.universal_target_session import PHASE117_ACTIONS_EXPANDED  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-2 动作扩展边界；如果没有这行代码，目标 session 阶段零动作事实不可见。
from learning_agent.computer_use.universal_target_session import PHASE117_UNIVERSAL_TARGET_SESSION_MARKER  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-2 ready marker；如果没有这行代码，目标 session 验收无法读取 marker。
from learning_agent.computer_use.universal_target_session import PHASE117_UNIVERSAL_TARGET_SESSION_MODEL  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-2 模型名；如果没有这行代码，动作层无法稳定引用目标 session 版本。
from learning_agent.computer_use.universal_target_session import PHASE117_UNIVERSAL_TARGET_SESSION_OK_TOKEN  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-2 OK token；如果没有这行代码，目标 session 验收无法匹配成功。
from learning_agent.computer_use.universal_target_session import UniversalTargetSessionRuntime  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-2 runtime；如果没有这行代码，动作层和闭环层无法复用身份守卫。
from learning_agent.computer_use.universal_target_session import phase117_universal_target_session_cli_line  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-2 CLI 行生成器；如果没有这行代码，场景文件容易重复拼接 token。
from learning_agent.computer_use.universal_target_session import run_phase117_universal_target_session_contract  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-2 合同自检；如果没有这行代码，外部无法复用目标身份事实源。
from learning_agent.computer_use.universal_action_dsl import PHASE118_ACTIONS_EXPANDED  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-3 动作扩展标记；如果没有这行代码，外部无法确认动作桥阶段已扩展到 sender。
from learning_agent.computer_use.universal_action_dsl import PHASE118_REAL_DISPATCH_PERFORMED  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-3 真实派发边界；如果没有这行代码，外部无法区分记录合同和物理派发。
from learning_agent.computer_use.universal_action_dsl import PHASE118_UNIVERSAL_ACTION_DSL_MARKER  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-3 ready marker；如果没有这行代码，动作 DSL 验收无法读取 marker。
from learning_agent.computer_use.universal_action_dsl import PHASE118_UNIVERSAL_ACTION_DSL_MODEL  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-3 模型名；如果没有这行代码，闭环层无法稳定引用动作 DSL 版本。
from learning_agent.computer_use.universal_action_dsl import PHASE118_UNIVERSAL_ACTION_DSL_OK_TOKEN  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-3 OK token；如果没有这行代码，动作 DSL 验收无法匹配成功。
from learning_agent.computer_use.universal_action_dsl import Phase118RecordingLowLevelSender  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-3 记录型低层 sender；如果没有这行代码，测试无法安全观察低层事件。
from learning_agent.computer_use.universal_action_dsl import UniversalActionDslRuntime  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-3 runtime；如果没有这行代码，闭环层无法复用动作桥。
from learning_agent.computer_use.universal_action_dsl import phase118_universal_action_dsl_cli_line  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-3 CLI 行生成器；如果没有这行代码，场景文件容易重复拼接 token。
from learning_agent.computer_use.universal_action_dsl import run_phase118_universal_action_dsl_contract  # 修改代码+URG4ObservePlanActVerify：继续导出 URG-3 合同自检；如果没有这行代码，闭环层无法继承安全事实。
from learning_agent.computer_use.universal_observe_plan_act_verify import PHASE119_REAL_DISPATCH_PERFORMED  # 新增代码+URG4ObservePlanActVerify：导出 URG-4 真实派发边界；如果没有这行代码，外部无法确认闭环合同默认不触碰桌面。
from learning_agent.computer_use.universal_observe_plan_act_verify import PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MARKER  # 新增代码+URG4ObservePlanActVerify：导出 URG-4 ready marker；如果没有这行代码，可见终端验收无法从包级入口读取 marker。
from learning_agent.computer_use.universal_observe_plan_act_verify import PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MODEL  # 新增代码+URG4ObservePlanActVerify：导出 URG-4 模型名；如果没有这行代码，最终矩阵无法识别闭环版本。
from learning_agent.computer_use.universal_observe_plan_act_verify import PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_OK_TOKEN  # 新增代码+URG4ObservePlanActVerify：导出 URG-4 OK token；如果没有这行代码，可见终端验收无法匹配成功。
from learning_agent.computer_use.universal_observe_plan_act_verify import Phase119GenericPlanner  # 新增代码+URG4ObservePlanActVerify：导出 URG-4 通用 planner；如果没有这行代码，外部无法替换或复用规划层。
from learning_agent.computer_use.universal_observe_plan_act_verify import Phase119GenericVerifier  # 新增代码+URG4ObservePlanActVerify：导出 URG-4 通用 verifier；如果没有这行代码，外部无法替换或复用验证层。
from learning_agent.computer_use.universal_observe_plan_act_verify import Phase119RecordingObservationRuntime  # 新增代码+URG4ObservePlanActVerify：导出 URG-4 安全记录观察 runtime；如果没有这行代码，测试无法安全组合闭环。
from learning_agent.computer_use.universal_observe_plan_act_verify import UniversalObservePlanActVerifyLoop  # 新增代码+URG4ObservePlanActVerify：导出 URG-4 闭环 runtime；如果没有这行代码，外部只能硬编码内部模块路径。
from learning_agent.computer_use.universal_observe_plan_act_verify import phase119_universal_loop_cli_line  # 新增代码+URG4ObservePlanActVerify：导出 URG-4 CLI 行生成器；如果没有这行代码，场景文件容易重复拼接 token。
from learning_agent.computer_use.universal_observe_plan_act_verify import run_phase119_universal_loop_contract  # 新增代码+URG4ObservePlanActVerify：导出 URG-4 合同自检；如果没有这行代码，测试和可见终端无法复用同一事实源。
from learning_agent.computer_use.universal_paint_pikachu_acceptance import PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MARKER  # 新增代码+URG5PaintPikachu：导出 URG-5 ready marker；如果没有这行代码，包级使用者无法读取 Paint/Pikachu 验收锚点。
from learning_agent.computer_use.universal_paint_pikachu_acceptance import PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MODEL  # 新增代码+URG5PaintPikachu：导出 URG-5 模型名；如果没有这行代码，最终矩阵无法从包级入口识别版本。
from learning_agent.computer_use.universal_paint_pikachu_acceptance import PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_OK_TOKEN  # 新增代码+URG5PaintPikachu：导出 URG-5 OK token；如果没有这行代码，外部验收无法稳定匹配成功。
from learning_agent.computer_use.universal_paint_pikachu_acceptance import Phase120PaintObservationRuntime  # 新增代码+URG5PaintPikachu：导出 Paint 代表观察 runtime；如果没有这行代码，外部无法复用画布观察样本。
from learning_agent.computer_use.universal_paint_pikachu_acceptance import Phase120PaintVerifier  # 新增代码+URG5PaintPikachu：导出 Paint 代表验证器；如果没有这行代码，外部无法复用画布变化验证。
from learning_agent.computer_use.universal_paint_pikachu_acceptance import Phase120PikachuPlanner  # 新增代码+URG5PaintPikachu：导出皮卡丘通用 planner；如果没有这行代码，外部无法复用绘图计划到 DSL 的转换。
from learning_agent.computer_use.universal_paint_pikachu_acceptance import Phase120RepresentativeRealDragSender  # 新增代码+URG5PaintPikachu：导出代表低层拖拽 sender；如果没有这行代码，最终矩阵无法复用真实派发证据。
from learning_agent.computer_use.universal_paint_pikachu_acceptance import phase120_universal_paint_pikachu_cli_line  # 新增代码+URG5PaintPikachu：导出 URG-5 CLI 行生成器；如果没有这行代码，场景文件容易重复拼接 token。
from learning_agent.computer_use.universal_paint_pikachu_acceptance import run_phase120_universal_paint_pikachu_acceptance_contract  # 新增代码+URG5PaintPikachu：导出 URG-5 合同入口；如果没有这行代码，外部无法复用 Paint/Pikachu 验收事实。
from learning_agent.computer_use.universal_final_maturity_matrix import PHASE121_UNIVERSAL_FINAL_MATURITY_MODEL  # 新增代码+URG6FinalMatrix：导出 URG-6 最终矩阵模型名；如果没有这行代码，包级状态无法识别最终矩阵版本。
from learning_agent.computer_use.universal_final_maturity_matrix import UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER  # 新增代码+URG6FinalMatrix：导出蓝图最终 marker；如果没有这行代码，外部无法读取终局锚点。
from learning_agent.computer_use.universal_final_maturity_matrix import phase121_universal_final_maturity_cli_line  # 新增代码+URG6FinalMatrix：导出最终矩阵 CLI 行生成器；如果没有这行代码，场景文件容易重复拼接 token。
from learning_agent.computer_use.universal_final_maturity_matrix import run_phase121_universal_final_maturity_matrix  # 新增代码+URG6FinalMatrix：导出最终矩阵入口；如果没有这行代码，外部无法运行 URG-6 汇总。

__all__: list[str] = []  # 修改代码+URG4ObservePlanActVerify：初始化公开名称列表；如果没有这行代码，后续 extend 会因为变量不存在而失败。
__all__.extend(["DEFAULT_MODE_SESSION_ID", "DEFAULT_MODE_SESSION_ROOT", "PHASE98_COMPUTER_USE_MODE_MODEL", "PHASE98_COMPUTER_USE_MODE_OK", "PHASE98_COMPUTER_USE_MODE_READY", "ComputerUseModeSessionStore"])  # 修改代码+URG4ObservePlanActVerify：公开 Phase98 session 名称；如果没有这行代码，老的包级导入回归会失败。
__all__.extend(["UniversalWindowsLiveExecutionGate"])  # 修改代码+URG4ObservePlanActVerify：公开通用 live execution gate；如果没有这行代码，已有 Phase93/102 包级 API 会消失。
__all__.extend(["PHASE116_ACTIONS_EXPANDED", "PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MARKER", "PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_MODEL", "PHASE116_UNIVERSAL_REAL_OBSERVATION_FRAME_OK_TOKEN", "UniversalRealObservationFrameRuntime", "run_universal_real_observation_frame_contract", "universal_real_observation_frame_cli_line"])  # 修改代码+URG4ObservePlanActVerify：公开 URG-1 观察帧名称；如果没有这行代码，通配导入会漏掉观察能力。
__all__.extend(["PHASE117_ACTIONS_EXPANDED", "PHASE117_UNIVERSAL_TARGET_SESSION_MARKER", "PHASE117_UNIVERSAL_TARGET_SESSION_MODEL", "PHASE117_UNIVERSAL_TARGET_SESSION_OK_TOKEN", "UniversalTargetSessionRuntime", "phase117_universal_target_session_cli_line", "run_phase117_universal_target_session_contract"])  # 修改代码+URG4ObservePlanActVerify：公开 URG-2 目标 session 名称；如果没有这行代码，通配导入会漏掉目标身份能力。
__all__.extend(["PHASE118_ACTIONS_EXPANDED", "PHASE118_REAL_DISPATCH_PERFORMED", "PHASE118_UNIVERSAL_ACTION_DSL_MARKER", "PHASE118_UNIVERSAL_ACTION_DSL_MODEL", "PHASE118_UNIVERSAL_ACTION_DSL_OK_TOKEN", "Phase118RecordingLowLevelSender", "UniversalActionDslRuntime", "phase118_universal_action_dsl_cli_line", "run_phase118_universal_action_dsl_contract"])  # 修改代码+URG4ObservePlanActVerify：公开 URG-3 动作 DSL 名称；如果没有这行代码，通配导入会漏掉动作桥能力。
__all__.extend(["PHASE119_REAL_DISPATCH_PERFORMED", "PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MARKER", "PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_MODEL", "PHASE119_UNIVERSAL_OBSERVE_PLAN_ACT_VERIFY_OK_TOKEN", "Phase119GenericPlanner", "Phase119GenericVerifier", "Phase119RecordingObservationRuntime", "UniversalObservePlanActVerifyLoop", "phase119_universal_loop_cli_line", "run_phase119_universal_loop_contract"])  # 新增代码+URG4ObservePlanActVerify：公开 URG-4 闭环名称；如果没有这行代码，通配导入会漏掉 observe-plan-act-verify 能力。
__all__.extend(["PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MARKER", "PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_MODEL", "PHASE120_UNIVERSAL_PAINT_PIKACHU_ACCEPTANCE_OK_TOKEN", "Phase120PaintObservationRuntime", "Phase120PaintVerifier", "Phase120PikachuPlanner", "Phase120RepresentativeRealDragSender", "phase120_universal_paint_pikachu_cli_line", "run_phase120_universal_paint_pikachu_acceptance_contract"])  # 新增代码+URG5PaintPikachu：公开 URG-5 Paint/Pikachu 验收名称；如果没有这行代码，通配导入会漏掉代表验收能力。
__all__.extend(["PHASE121_UNIVERSAL_FINAL_MATURITY_MODEL", "UNIVERSAL_REAL_GUI_COMPUTER_USE_MARKER", "phase121_universal_final_maturity_cli_line", "run_phase121_universal_final_maturity_matrix"])  # 新增代码+URG6FinalMatrix：公开 URG-6 最终矩阵名称；如果没有这行代码，通配导入会漏掉最终成熟度入口。
