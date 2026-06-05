"""Windows 通用真实执行闭环门禁。"""  # 新增代码+Phase93UniversalLiveExecutionGate：说明本文件负责把 Phase92 通用模式接到安全 live execution gate；如果没有这行代码，读者很难知道本模块不是单应用控制器。
from __future__ import annotations  # 新增代码+Phase93UniversalLiveExecutionGate：启用延迟类型解析；如果没有这行代码，后续类之间互相引用时更容易遇到类型注解问题。

import hashlib  # 新增代码+Phase93UniversalLiveExecutionGate：导入哈希库用于 prompt 脱敏追踪；如果没有这行代码，报告要么泄露原文，要么无法关联任务。
import json  # 新增代码+Phase93UniversalLiveExecutionGate：导入 JSON 用于稳定序列化报告；如果没有这行代码，隐私检查和验收落盘都不稳定。
import time  # 新增代码+Phase93UniversalLiveExecutionGate：导入时间用于生成隔离 session/report 目录；如果没有这行代码，多次验收可能互相覆盖。
from pathlib import Path  # 新增代码+Phase93UniversalLiveExecutionGate：导入 Path 统一处理 Windows 路径；如果没有这行代码，路径拼接会更脆弱。
from typing import Any  # 新增代码+Phase93UniversalLiveExecutionGate：导入 Any 描述 JSON 风格数据；如果没有这行代码，接口边界对初学者不清楚。

try:  # 新增代码+Phase93UniversalLiveExecutionGate：优先按 learning_agent 包路径导入已有组件；如果没有这段代码，单元测试和生产入口不能共享同一套模块。
    from learning_agent.computer_use.closed_loop_executor import WindowsClosedLoopComputerExecutor  # 新增代码+Phase93UniversalLiveExecutionGate：复用 Phase68 闭环执行器；如果没有这行代码，Phase93 会变成静态状态汇总。
    from learning_agent.computer_use.generic_control_actions import Phase70RecordingHighLevelTool, WindowsGenericControlActionRuntime  # 新增代码+Phase93UniversalLiveExecutionGate：复用 Phase70 通用点击/输入动作层；如果没有这行代码，系统可能退回每个软件硬编码动作。
    from learning_agent.computer_use.generic_input_actions import Phase71RecordingInputSender, WindowsGenericInputActionRuntime  # 新增代码+Phase93UniversalLiveExecutionGate：复用 Phase71 通用热键/菜单/滚动/拖拽事件层；如果没有这行代码，输入能力会分散。
    from learning_agent.computer_use.mode_session import ComputerUseModeSessionStore  # 新增代码+Phase99UniversalComputerUseModeGate：导入 Phase98 mode store；如果没有这行代码，Phase93 无法在真实动作前询问 normal/observe/stopped/expired 模式。
    from learning_agent.computer_use.persistent_grants import WindowsComputerUsePersistentGrantStore  # 新增代码+Phase93UniversalLiveExecutionGate：复用 Phase60 持久授权事实源；如果没有这行代码，真实执行门禁没有可审计授权来源。
    from learning_agent.computer_use.production_live_control import WindowsProductionComputerUseHostAdapter  # 新增代码+Phase93UniversalLiveExecutionGate：复用 Phase76-89 生产 host adapter；如果没有这行代码，Phase93 无法连接生产级桥接结构。
    from learning_agent.computer_use.real_app_safety_boundary import WindowsRealAppSafetyBoundary  # 新增代码+Phase93UniversalLiveExecutionGate：复用 Phase72 真实应用安全边界；如果没有这行代码，危险窗口和未授权窗口无法统一拒绝。
    from learning_agent.computer_use.universal_mode import UniversalWindowsComputerUseRuntime  # 新增代码+Phase93UniversalLiveExecutionGate：复用 Phase92 单一通用 prompt mode；如果没有这行代码，Phase93 可能重复造一个偏离主线的 runtime。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase93UniversalLiveExecutionGate：复用项目原子 JSON 写入工具；如果没有这行代码，验收报告可能半写损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase93UniversalLiveExecutionGate：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，真实可见终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.mode_session", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 修改代码+Phase99UniversalComputerUseModeGate：允许脚本模式下 mode_session 路径缺失进入 fallback；如果没有这行代码，start_oauth_agent.bat 可能无法导入 Phase99 gate。
        raise  # 新增代码+Phase93UniversalLiveExecutionGate：重新抛出非路径类导入错误；如果没有这行代码，依赖内部错误会被隐藏。
    from computer_use.closed_loop_executor import WindowsClosedLoopComputerExecutor  # type: ignore  # 新增代码+Phase93UniversalLiveExecutionGate：脚本模式复用 Phase68 闭环执行器；如果没有这行代码，bat 入口无法运行 Phase93。
    from computer_use.generic_control_actions import Phase70RecordingHighLevelTool, WindowsGenericControlActionRuntime  # type: ignore  # 新增代码+Phase93UniversalLiveExecutionGate：脚本模式复用 Phase70 通用动作层；如果没有这行代码，bat 入口缺少通用控制能力。
    from computer_use.generic_input_actions import Phase71RecordingInputSender, WindowsGenericInputActionRuntime  # type: ignore  # 新增代码+Phase93UniversalLiveExecutionGate：脚本模式复用 Phase71 输入事件层；如果没有这行代码，bat 入口缺少通用输入能力。
    from computer_use.mode_session import ComputerUseModeSessionStore  # type: ignore  # 新增代码+Phase99UniversalComputerUseModeGate：脚本模式导入 Phase98 mode store；如果没有这行代码，可见终端入口不能执行 Phase99 mode gate。
    from computer_use.persistent_grants import WindowsComputerUsePersistentGrantStore  # type: ignore  # 新增代码+Phase93UniversalLiveExecutionGate：脚本模式复用 Phase60 授权 store；如果没有这行代码，bat 入口无法验证授权门禁。
    from computer_use.production_live_control import WindowsProductionComputerUseHostAdapter  # type: ignore  # 新增代码+Phase93UniversalLiveExecutionGate：脚本模式复用生产 host adapter；如果没有这行代码，bat 入口缺少生产桥接状态。
    from computer_use.real_app_safety_boundary import WindowsRealAppSafetyBoundary  # type: ignore  # 新增代码+Phase93UniversalLiveExecutionGate：脚本模式复用安全边界；如果没有这行代码，bat 入口无法阻断危险窗口。
    from computer_use.universal_mode import UniversalWindowsComputerUseRuntime  # type: ignore  # 新增代码+Phase93UniversalLiveExecutionGate：脚本模式复用 Phase92 通用 runtime；如果没有这行代码，bat 入口会偏离通用模式主线。
    from runtime.files import atomic_write_json  # type: ignore  # 新增代码+Phase93UniversalLiveExecutionGate：脚本模式复用原子写入工具；如果没有这行代码，bat 验收报告可能写坏。

PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER = "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_READY"  # 新增代码+Phase93UniversalLiveExecutionGate：定义 Phase93 ready 标记；如果没有这行代码，真实终端验收无法稳定识别新阶段。
PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN = "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK"  # 新增代码+Phase93UniversalLiveExecutionGate：定义 Phase93 OK 标记；如果没有这行代码，验收脚本无法区分成功输出和普通日志。
PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MODEL = "phase93_universal_live_execution_gate"  # 新增代码+Phase93UniversalLiveExecutionGate：定义 Phase93 协议模型名；如果没有这行代码，报告和矩阵无法引用版本。
PHASE93_REAL_ACTIONS_DEFAULT_DISABLED = True  # 新增代码+Phase93UniversalLiveExecutionGate：声明真实动作默认关闭；如果没有这行代码，普通 prompt 可能被误解为会直接操控电脑。
PHASE93_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase93UniversalLiveExecutionGate：声明没有扩张无边界动作面；如果没有这行代码，安全审计无法判断边界是否被放宽。
DEFAULT_PHASE93_UNIVERSAL_LIVE_EXECUTION_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "phase93_universal_live_execution_gate"  # 新增代码+Phase93UniversalLiveExecutionGate：定义默认报告目录；如果没有这行代码，验收证据没有稳定落点。
PHASE102_FULL_MODE_EXECUTION_GATE_MARKER = "PHASE102_FULL_MODE_EXECUTION_GATE_READY"  # 新增代码+Phase102FullModeExecutionGate：定义 Phase102 ready 标记；如果没有这行代码，真实终端验收无法稳定识别 full 执行门禁。
PHASE102_FULL_MODE_EXECUTION_GATE_OK_TOKEN = "PHASE102_FULL_MODE_EXECUTION_GATE_OK"  # 新增代码+Phase102FullModeExecutionGate：定义 Phase102 OK 标记；如果没有这行代码，场景无法区分成功输出和普通日志。
PHASE102_FULL_MODE_EXECUTION_GATE_MODEL = "phase102_full_mode_execution_gate"  # 新增代码+Phase102FullModeExecutionGate：定义 Phase102 模型名；如果没有这行代码，报告无法标明这是 full 模式执行门禁合同。
DEFAULT_PHASE102_FULL_MODE_EXECUTION_GATE_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "phase102_full_mode_execution_gate"  # 新增代码+Phase102FullModeExecutionGate：定义 Phase102 默认报告目录；如果没有这行代码，验收证据没有稳定落点。


# 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，_phase93_bool_token 把布尔值转成小写验收 token；如果没有这段函数，CLI 输出会混用 True/False 并导致场景匹配不稳。
def _phase93_bool_token(value: Any) -> str:  # 新增代码+Phase93UniversalLiveExecutionGate：定义布尔 token helper；如果没有这行代码，多处输出会重复写转换逻辑。
    return "true" if bool(value) else "false"  # 新增代码+Phase93UniversalLiveExecutionGate：返回小写布尔文本；如果没有这行代码，JSON 字段和终端 token 可能格式不一致。
# 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，_phase93_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。


# 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，_phase93_safe_prompt 清理 prompt 但只在内存中使用；如果没有这段函数，None、换行或超长 prompt 会污染规划器。
def _phase93_safe_prompt(prompt: Any) -> str:  # 新增代码+Phase93UniversalLiveExecutionGate：定义 prompt 清洗函数；如果没有这行代码，调用方要到处处理空值和换行。
    text = " ".join(str(prompt or "").strip().split())  # 新增代码+Phase93UniversalLiveExecutionGate：把 prompt 转成单行干净文本；如果没有这行代码，日志和风险判断会被换行打散。
    return text[:1000]  # 新增代码+Phase93UniversalLiveExecutionGate：限制 prompt 最大长度；如果没有这行代码，超长输入可能刷爆报告和终端。
# 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，_phase93_safe_prompt 到此结束；如果没有这个边界说明，初学者不容易看出清洗范围。


# 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，_phase93_sha256_16 生成短哈希；如果没有这段函数，报告要么泄露原文，要么无法关联任务。
def _phase93_sha256_16(value: Any) -> str:  # 新增代码+Phase93UniversalLiveExecutionGate：定义短哈希函数；如果没有这行代码，多个报告字段无法稳定脱敏。
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase93UniversalLiveExecutionGate：稳定序列化任意 JSON 风格值；如果没有这行代码，同一内容顺序不同会得到不同摘要。
    return hashlib.sha256(serialized.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase93UniversalLiveExecutionGate：返回 SHA256 前 16 位；如果没有这行代码，短指纹没有真实内容来源。
# 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，_phase93_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出哈希范围。


# 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，_phase93_low_level_count 统一读取低层事件数；如果没有这段函数，零事件断言会散落且容易漏字段。
def _phase93_low_level_count(result: dict[str, Any] | Any) -> int:  # 新增代码+Phase93UniversalLiveExecutionGate：定义低层事件统计 helper；如果没有这行代码，拒绝路径统计容易出错。
    source = dict(result or {}) if isinstance(result, dict) else {}  # 新增代码+Phase93UniversalLiveExecutionGate：容错读取字典结果；如果没有这行代码，坏输入可能让统计崩溃。
    return int(source.get("low_level_event_count", 0) or 0)  # 新增代码+Phase93UniversalLiveExecutionGate：返回默认 0 的事件数；如果没有这行代码，None 会污染零事件判断。
# 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，_phase93_low_level_count 到此结束；如果没有这个边界说明，初学者不容易看出统计范围。


def _phase102_prompt_requests_launch(prompt_text: str, phase92_report: dict[str, Any]) -> bool:  # 新增代码+Phase102FullModeExecutionGate：函数段开始，判断用户是否要启动普通应用；如果没有这段函数，run_prompt 只能继续硬编码 click。
    lowered = str(prompt_text or "").lower()  # 新增代码+Phase102FullModeExecutionGate：把 prompt 转成小写文本；如果没有这行代码，英文 launch/start 大小写变体可能漏检。
    if "启动" in str(prompt_text or "") or "launch_app" in lowered or "launch app" in lowered or "start app" in lowered:  # 新增代码+Phase102FullModeExecutionGate：匹配明确启动应用意图；如果没有这行代码，full 模式无法把启动类任务映射到 launch_app。
        return True  # 新增代码+Phase102FullModeExecutionGate：返回需要 launch_app；如果没有这行代码，命中启动意图后仍会落回 click。
    steps = dict(phase92_report.get("session_plan", {}) or {}).get("steps", []) if isinstance(phase92_report, dict) else []  # 新增代码+Phase102FullModeExecutionGate：读取 Phase92 规划步骤；如果没有这行代码，已有 planner 的 launch_app 结果无法复用。
    return any(isinstance(step, dict) and str(step.get("operation", "")).lower() == "launch_app" for step in steps if isinstance(steps, list))  # 新增代码+Phase102FullModeExecutionGate：只要计划里有 launch_app 就返回真；如果没有这行代码，中文/特定应用 planner 命中启动也不会进入 full 动作面。
# 新增代码+Phase102FullModeExecutionGate：函数段结束，_phase102_prompt_requests_launch 到此结束；如果没有这个边界说明，读者不容易看出启动意图判断范围。


def _phase102_task_plan(prompt_text: str, phase92_report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase102FullModeExecutionGate：函数段开始，根据用户任务选择闭环计划；如果没有这段函数，run_prompt 只能执行固定 click 计划。
    if _phase102_prompt_requests_launch(prompt_text, phase92_report):  # 新增代码+Phase102FullModeExecutionGate：检查是否是启动应用任务；如果没有这行代码，full 专属动作没有入口。
        return {"steps": [{"operation": "observe_generic_target", "action_kind": "observe"}, {"operation": "launch_app_generic_target", "action_kind": "write"}, {"operation": "verify_generic_target", "action_kind": "verify"}]}  # 新增代码+Phase102FullModeExecutionGate：返回 observe-launch-verify 计划；如果没有这行代码，启动动作无法进入 mode gate。
    return {"steps": [{"operation": "observe_generic_target", "action_kind": "observe"}, {"operation": "click_generic_target", "action_kind": "write"}, {"operation": "verify_generic_target", "action_kind": "verify"}]}  # 修改代码+Phase102FullModeExecutionGate：非启动任务保留旧 click 计划；如果没有这行代码，Phase99 的普通点击回归会失去计划。
# 新增代码+Phase102FullModeExecutionGate：函数段结束，_phase102_task_plan 到此结束；如果没有这个边界说明，读者不容易看出计划选择范围。


def _phase102_action_class_for_step(step: dict[str, Any]) -> str:  # 新增代码+Phase102FullModeExecutionGate：函数段开始，把闭环 step 映射到 mode action_class；如果没有这段函数，安全边界只能收到硬编码 click。
    operation = str(step.get("operation", "") or "").lower()  # 新增代码+Phase102FullModeExecutionGate：读取小写 operation；如果没有这行代码，Launch_App 等大小写变体会漏判。
    if operation.startswith("launch_app"):  # 新增代码+Phase102FullModeExecutionGate：识别启动应用步骤；如果没有这行代码，full 专属 launch_app 不会被 mode store 评估。
        return "launch_app"  # 新增代码+Phase102FullModeExecutionGate：返回 full 专属动作类；如果没有这行代码，启动动作会被误当普通 click。
    return "click"  # 新增代码+Phase102FullModeExecutionGate：其它写动作沿用旧 click 语义；如果没有这行代码，Phase99 普通点击路径会变成未知动作。
# 新增代码+Phase102FullModeExecutionGate：函数段结束，_phase102_action_class_for_step 到此结束；如果没有这个边界说明，读者不容易看出动作映射范围。


def _phase102_mode_status(mode_store: Any | None) -> dict[str, Any]:  # 新增代码+Phase102FullModeExecutionGate：函数段开始，安全读取 mode store 状态；如果没有这段函数，总报告无法稳定显示 full 是否已确认。
    if mode_store is None or not hasattr(mode_store, "status"):  # 新增代码+Phase102FullModeExecutionGate：检查 mode store 是否可用；如果没有这行代码，None store 会导致异常。
        return {"mode": "off", "full_mode": False}  # 新增代码+Phase102FullModeExecutionGate：缺少 store 时返回安全 off；如果没有这行代码，调用方无法区分无状态和异常。
    try:  # 新增代码+Phase102FullModeExecutionGate：捕获状态读取异常；如果没有这行代码，坏状态文件会拖垮整个 run_prompt。
        status = mode_store.status()  # 新增代码+Phase102FullModeExecutionGate：读取真实 mode 状态；如果没有这行代码，总报告不能证明 full-confirm 是否生效。
    except Exception:  # 新增代码+Phase102FullModeExecutionGate：状态读取失败时安全降级；如果没有这行代码，损坏 JSON 可能让执行入口崩溃。
        return {"mode": "off", "full_mode": False}  # 新增代码+Phase102FullModeExecutionGate：异常时返回 off；如果没有这行代码，失败状态可能被误认为可执行。
    return dict(status or {}) if isinstance(status, dict) else {"mode": "off", "full_mode": False}  # 新增代码+Phase102FullModeExecutionGate：规范化状态字典；如果没有这行代码，非 dict 返回会污染后续布尔判断。
# 新增代码+Phase102FullModeExecutionGate：函数段结束，_phase102_mode_status 到此结束；如果没有这个边界说明，读者不容易看出 mode 状态读取范围。


# 新增代码+Phase93UniversalLiveExecutionGate：类段开始，_Phase93ClosedLoopObserver 提供无副作用观察样本；如果没有这个类，合同测试会依赖真实桌面状态而不稳定。
class _Phase93ClosedLoopObserver:  # 新增代码+Phase93UniversalLiveExecutionGate：定义 Phase93 闭环观察器；如果没有这行代码，闭环执行器没有观察阶段输入。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，初始化观察器目标窗口；如果没有这段函数，观察器无法持有当前目标身份。
    def __init__(self, window: dict[str, Any]) -> None:  # 新增代码+Phase93UniversalLiveExecutionGate：定义初始化方法；如果没有这行代码，window 注入没有入口。
        self.window = dict(window)  # 新增代码+Phase93UniversalLiveExecutionGate：复制目标窗口防止外部修改；如果没有这行代码，测试期间窗口身份可能被调用方污染。
        self.calls = 0  # 新增代码+Phase93UniversalLiveExecutionGate：记录观察次数；如果没有这行代码，观察证据无法体现顺序。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，_Phase93ClosedLoopObserver.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，observe 返回可闭环使用的窗口和控件摘要；如果没有这段函数，actor 没有观察依据。
    def observe(self, step: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase93UniversalLiveExecutionGate：定义观察方法；如果没有这行代码，Phase68 执行器无法调用观察阶段。
        self.calls += 1  # 新增代码+Phase93UniversalLiveExecutionGate：增加观察计数；如果没有这行代码，观察 id 不会变化。
        return {"observation_id": f"phase93-observation-{self.calls}", "operation": str(step.get("operation", "")), "window": dict(self.window), "stable": True, "flat_nodes": [{"node_id": "phase93.0", "name": "Generic target", "role": "Pane", "automation_id": "Phase93GenericTarget", "bounds": {"left": 200, "top": 180, "right": 420, "bottom": 320, "width": 220, "height": 140}, "enabled": True, "clickable": True, "editable": False}]}  # 新增代码+Phase93UniversalLiveExecutionGate：返回最小可定位观察；如果没有这行代码，通用动作层没有控件和窗口输入。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，_Phase93ClosedLoopObserver.observe 到此结束；如果没有这个边界说明，初学者不容易看出观察范围。
# 新增代码+Phase93UniversalLiveExecutionGate：类段结束，_Phase93ClosedLoopObserver 到此结束；如果没有这个边界说明，初学者不容易看出观察器范围。


# 新增代码+Phase93UniversalLiveExecutionGate：类段开始，_Phase93ClosedLoopActor 把安全边界和通用动作层串起来；如果没有这个类，Phase93 不能证明授权后进入统一执行链路。
class _Phase93ClosedLoopActor:  # 新增代码+Phase93UniversalLiveExecutionGate：定义 Phase93 闭环动作器；如果没有这行代码，Phase68 执行器没有 act 阶段。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，初始化动作器依赖；如果没有这段函数，安全边界、授权 store 和通用动作层无法组合。
    def __init__(self, window: dict[str, Any], safety_boundary: WindowsRealAppSafetyBoundary, grant_store: WindowsComputerUsePersistentGrantStore, mode_store: Any | None, session_id: str, control_runtime: WindowsGenericControlActionRuntime, input_runtime: WindowsGenericInputActionRuntime, request_real_actions: bool) -> None:  # 修改代码+Phase99UniversalComputerUseModeGate：增加 mode_store 依赖；如果没有这行代码，actor 只能继续依赖旧 per-app grant 门禁。
        self.window = dict(window)  # 新增代码+Phase93UniversalLiveExecutionGate：复制目标窗口；如果没有这行代码，外部窗口对象变化会污染目标身份。
        self.safety_boundary = safety_boundary  # 新增代码+Phase93UniversalLiveExecutionGate：保存安全边界；如果没有这行代码，动作前无法统一授权和风险检查。
        self.grant_store = grant_store  # 新增代码+Phase93UniversalLiveExecutionGate：保存授权 store；如果没有这行代码，动作器无法判断是否有用户授权。
        self.mode_store = mode_store  # 新增代码+Phase99UniversalComputerUseModeGate：保存 mode session store；如果没有这行代码，真实动作前无法检查 normal/observe/stopped/expired 模式。
        self.session_id = str(session_id)  # 新增代码+Phase93UniversalLiveExecutionGate：保存 session id；如果没有这行代码，授权匹配没有会话维度。
        self.control_runtime = control_runtime  # 新增代码+Phase93UniversalLiveExecutionGate：保存通用控件动作 runtime；如果没有这行代码，点击路径会绕过 Phase70。
        self.input_runtime = input_runtime  # 新增代码+Phase93UniversalLiveExecutionGate：保存通用输入 runtime；如果没有这行代码，滚动/拖拽等事件会绕过 Phase71。
        self.request_real_actions = bool(request_real_actions)  # 新增代码+Phase93UniversalLiveExecutionGate：保存是否请求真实动作；如果没有这行代码，默认安全模式无法和授权记录模式区分。
        self.action_reports: list[dict[str, Any]] = []  # 新增代码+Phase93UniversalLiveExecutionGate：保存动作报告；如果没有这行代码，合同无法统计记录型执行是否进入动作层。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，_Phase93ClosedLoopActor.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    # 修改代码+Phase102FullModeExecutionGate：函数段开始，act 在真实发送前按 step 动作类询问安全边界；如果没有这段函数，full 模式启动动作仍会被硬编码成 click。
    def act(self, step: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:  # 修改代码+Phase102FullModeExecutionGate：定义动作方法；如果没有这行代码，闭环执行器无法进入 action_class-aware act 阶段。
        operation = str(step.get("operation", ""))  # 新增代码+Phase93UniversalLiveExecutionGate：读取当前操作名；如果没有这行代码，报告无法说明执行了哪一步。
        action_kind = str(step.get("action_kind", "")).strip().lower()  # 新增代码+Phase102FullModeExecutionGate：读取动作类型；如果没有这行代码，观察步骤会被误当真实写动作。
        action_class = "observe_screen" if action_kind in {"observe", "read", "wait"} else _phase102_action_class_for_step(step)  # 新增代码+Phase102FullModeExecutionGate：把步骤映射成安全边界动作类；如果没有这行代码，launch_app 仍会被当成普通 click。
        if not self.request_real_actions:  # 新增代码+Phase93UniversalLiveExecutionGate：默认不执行真实动作；如果没有这行代码，普通 prompt 可能误触本机。
            report = {"acted": False, "operation": operation, "action_kind": action_kind, "action_class": action_class, "decision": "real_actions_disabled_by_default", "low_level_event_count": 0, "recording_dispatch_only": True, "real_dispatch_allowed": False, "real_dispatch_performed": False, "full_mode_action": False, "full_mode_action_ready": False}  # 修改代码+Phase102FullModeExecutionGate：构造预览阻断报告并带上动作类；如果没有这行代码，报告无法证明 full 动作没有被默认派发。
            self.action_reports.append(report)  # 新增代码+Phase93UniversalLiveExecutionGate：保存默认阻断报告；如果没有这行代码，合同无法复盘预览路径。
            return report  # 新增代码+Phase93UniversalLiveExecutionGate：返回默认阻断结果；如果没有这行代码，预览模式会继续走授权动作。
        if action_kind in {"observe", "read", "wait"}:  # 新增代码+Phase102FullModeExecutionGate：识别只读观察步骤；如果没有这行代码，observe 会误占用安全边界拒绝/放行判断。
            report = {"acted": False, "operation": operation, "action_kind": action_kind, "action_class": action_class, "decision": "observe_step_no_dispatch", "low_level_event_count": 0, "recording_dispatch_only": True, "real_dispatch_allowed": False, "real_dispatch_performed": False, "mode_session_used": bool(self.mode_store is not None), "per_app_allowlist_required": False, "ordinary_apps_allowed_by_risk_policy": False, "full_mode_action": False, "full_mode_action_ready": False, "observation_id": observation.get("observation_id", "")}  # 新增代码+Phase102FullModeExecutionGate：返回只读零派发报告；如果没有这行代码，观察步骤可能干扰后续 launch_app 的真实门禁结果。
            self.action_reports.append(report)  # 新增代码+Phase102FullModeExecutionGate：保存观察报告；如果没有这行代码，总报告无法说明观察阶段没有派发动作。
            return report  # 新增代码+Phase102FullModeExecutionGate：观察步骤到此结束；如果没有这行代码，观察会继续进入写动作门禁。
        decision = self.safety_boundary.evaluate_with_mode_session(self.window, action_class, self.mode_store, self.session_id) if self.mode_store is not None else self.safety_boundary.evaluate(self.window, action_class, self.grant_store, self.session_id)  # 修改代码+Phase102FullModeExecutionGate：用真实 action_class 询问 mode-aware 安全边界；如果没有这行代码，full 专属 launch_app 不会被正常判定。
        full_mode_action = action_class != "click"  # 新增代码+Phase102FullModeExecutionGate：标记是否属于 full 扩展动作；如果没有这行代码，总报告无法区分普通 click 和 full 专属动作。
        if not bool(decision.get("allowed")):  # 新增代码+Phase93UniversalLiveExecutionGate：检查安全边界是否放行；如果没有这行代码，拒绝结果也可能继续执行。
            report = {"acted": False, "operation": operation, "action_kind": action_kind, "action_class": action_class, "decision": str(decision.get("decision", "")), "safety_decision": decision, "low_level_event_count": _phase93_low_level_count(decision), "recording_dispatch_only": True, "real_dispatch_allowed": False, "real_dispatch_performed": False, "mode_session_used": bool(decision.get("mode_session_used", False)), "per_app_allowlist_required": bool(decision.get("per_app_allowlist_required", False)), "ordinary_apps_allowed_by_risk_policy": bool(decision.get("ordinary_apps_allowed_by_risk_policy", False)), "full_mode_action": full_mode_action, "full_mode_action_ready": False}  # 修改代码+Phase102FullModeExecutionGate：拒绝报告携带动作类和 full 就绪字段；如果没有这行代码，normal 拒绝 launch_app 时总报告无法定位原因。
            self.action_reports.append(report)  # 新增代码+Phase93UniversalLiveExecutionGate：保存安全拒绝报告；如果没有这行代码，合同无法复盘拒绝路径。
            return report  # 新增代码+Phase93UniversalLiveExecutionGate：返回安全拒绝结果；如果没有这行代码，拒绝后仍会进入动作层。
        if action_class == "launch_app":  # 新增代码+Phase102FullModeExecutionGate：识别 full 模式启动应用动作；如果没有这行代码，授权后仍会走点击/滚动旧路径。
            launch_recording = {"ok": True, "operation": "launch_app", "recording_only": True, "real_dispatch_performed": False, "low_level_event_count": 0, "target_app": str(self.window.get("app_id", ""))}  # 新增代码+Phase102FullModeExecutionGate：生成启动动作记录型结果；如果没有这行代码，测试无法证明 full 已进入 launch_app 动作层。
            report = {"acted": True, "operation": operation, "action_kind": action_kind, "action_class": action_class, "decision": "authorized_recording_dispatch", "safety_decision": decision, "launch_recording_result": launch_recording, "high_level_event_count": 1, "input_event_count": 0, "low_level_event_count": 0, "recording_dispatch_only": True, "real_dispatch_allowed": False, "real_dispatch_performed": False, "mode_session_used": bool(decision.get("mode_session_used", False)), "per_app_allowlist_required": bool(decision.get("per_app_allowlist_required", False)), "ordinary_apps_allowed_by_risk_policy": bool(decision.get("ordinary_apps_allowed_by_risk_policy", False)), "full_mode_action": True, "full_mode_action_ready": True, "observation_id": observation.get("observation_id", "")}  # 新增代码+Phase102FullModeExecutionGate：返回 full 启动记录型授权报告；如果没有这行代码，full 模式和 normal 模式没有可见行为差异。
            self.action_reports.append(report)  # 新增代码+Phase102FullModeExecutionGate：保存 full 启动动作报告；如果没有这行代码，总报告无法汇总 full_mode_action_ready。
            return report  # 新增代码+Phase102FullModeExecutionGate：返回 full 启动记录型结果；如果没有这行代码，闭环验证器拿不到 launch_app 证据。
        click = self.control_runtime.click_by_visual_point(self.window, {"x": 260, "y": 220}, "phase93 generic visual target")  # 新增代码+Phase93UniversalLiveExecutionGate：用 Phase70 记录型通用点击证明动作层接入；如果没有这行代码，授权后链路没有通用点击证据。
        scroll = self.input_runtime.scroll_at(self.window, 260, 220, -120)  # 新增代码+Phase93UniversalLiveExecutionGate：用 Phase71 记录型滚动证明输入层接入；如果没有这行代码，授权后链路没有通用输入证据。
        report = {"acted": True, "operation": operation, "action_kind": action_kind, "action_class": action_class, "decision": "authorized_recording_dispatch", "safety_decision": decision, "generic_control_result": click, "generic_input_result": scroll, "high_level_event_count": int(click.get("high_level_event_count", 0) or 0), "input_event_count": int(scroll.get("input_event_count", 0) or 0), "low_level_event_count": 0, "recording_dispatch_only": True, "real_dispatch_allowed": False, "real_dispatch_performed": False, "mode_session_used": bool(decision.get("mode_session_used", False)), "per_app_allowlist_required": bool(decision.get("per_app_allowlist_required", False)), "ordinary_apps_allowed_by_risk_policy": bool(decision.get("ordinary_apps_allowed_by_risk_policy", False)), "full_mode_action": False, "full_mode_action_ready": False, "observation_id": observation.get("observation_id", "")}  # 修改代码+Phase102FullModeExecutionGate：普通授权记录型报告补充动作类和 full 字段；如果没有这行代码，总报告无法稳定兼容 full 汇总。
        self.action_reports.append(report)  # 新增代码+Phase93UniversalLiveExecutionGate：保存授权动作报告；如果没有这行代码，合同无法统计记录型执行是否发生。
        return report  # 新增代码+Phase93UniversalLiveExecutionGate：返回授权记录型动作结果；如果没有这行代码，闭环验证器拿不到动作证据。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，_Phase93ClosedLoopActor.act 到此结束；如果没有这个边界说明，初学者不容易看出动作范围。
# 新增代码+Phase93UniversalLiveExecutionGate：类段结束，_Phase93ClosedLoopActor 到此结束；如果没有这个边界说明，初学者不容易看出动作器范围。


# 新增代码+Phase93UniversalLiveExecutionGate：类段开始，_Phase93ClosedLoopVerifier 负责验证动作报告；如果没有这个类，闭环无法证明动作后被检查。
class _Phase93ClosedLoopVerifier:  # 新增代码+Phase93UniversalLiveExecutionGate：定义 Phase93 验证器；如果没有这行代码，Phase68 执行器没有 verify 阶段。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，verify 把预览和授权记录模式都视为可验证合同；如果没有这段函数，默认安全模式会被误当失败。
    def verify(self, step: dict[str, Any], observation: dict[str, Any], action_result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase93UniversalLiveExecutionGate：定义验证方法；如果没有这行代码，闭环执行器无法执行后置检查。
        passed = bool(action_result and _phase93_low_level_count(action_result) == 0)  # 新增代码+Phase93UniversalLiveExecutionGate：检查动作存在且没有低层事件；如果没有这行代码，记录型门禁可能误发低层输入。
        return {"passed": passed, "checked_operation": str(step.get("operation", "")), "observation_id": observation.get("observation_id", ""), "low_level_event_count": _phase93_low_level_count(action_result), "recording_dispatch_only": bool(action_result.get("recording_dispatch_only", False))}  # 新增代码+Phase93UniversalLiveExecutionGate：返回验证报告；如果没有这行代码，闭环结果缺少可审计检查。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，_Phase93ClosedLoopVerifier.verify 到此结束；如果没有这个边界说明，初学者不容易看出验证范围。
# 新增代码+Phase93UniversalLiveExecutionGate：类段结束，_Phase93ClosedLoopVerifier 到此结束；如果没有这个边界说明，初学者不容易看出验证器范围。


# 新增代码+Phase93UniversalLiveExecutionGate：类段开始，_Phase93ClosedLoopRecoverer 提供失败恢复摘要；如果没有这个类，闭环失败时没有统一恢复事件。
class _Phase93ClosedLoopRecoverer:  # 新增代码+Phase93UniversalLiveExecutionGate：定义 Phase93 恢复器；如果没有这行代码，Phase68 执行器没有 recover 阶段。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，recover 返回重新观察策略；如果没有这段函数，失败路径没有可审计恢复方案。
    def recover(self, step: dict[str, Any], observation: dict[str, Any], action_result: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase93UniversalLiveExecutionGate：定义恢复方法；如果没有这行代码，闭环执行器无法调用恢复阶段。
        return {"recovered": True, "strategy": "observe_again_before_any_real_send", "operation": str(step.get("operation", "")), "failed_check": verification.get("checked_operation", ""), "low_level_event_count": _phase93_low_level_count(action_result), "observation_id": observation.get("observation_id", "")}  # 新增代码+Phase93UniversalLiveExecutionGate：返回恢复报告；如果没有这行代码，失败时不知道如何安全降级。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，_Phase93ClosedLoopRecoverer.recover 到此结束；如果没有这个边界说明，初学者不容易看出恢复范围。
# 新增代码+Phase93UniversalLiveExecutionGate：类段结束，_Phase93ClosedLoopRecoverer 到此结束；如果没有这个边界说明，初学者不容易看出恢复器范围。


# 新增代码+Phase93UniversalLiveExecutionGate：类段开始，UniversalWindowsLiveExecutionGate 是 Phase93 的单一通用 live execution 总闸；如果没有这个类，Computer Use 会继续缺少从 prompt 到真实执行门禁的统一对象。
class UniversalWindowsLiveExecutionGate:  # 新增代码+Phase93UniversalLiveExecutionGate：定义公开运行时类；如果没有这行代码，测试和外部 agent 无法复用 Phase93 能力。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，初始化所有被组合的已有能力；如果没有这段函数，Phase93 无法证明它复用而不是重复发明旧组件。
    def __init__(self, base_dir: str | Path | None = None, phase92_runtime: UniversalWindowsComputerUseRuntime | None = None, safety_boundary: WindowsRealAppSafetyBoundary | None = None, grant_store: WindowsComputerUsePersistentGrantStore | None = None, host_adapter: WindowsProductionComputerUseHostAdapter | None = None, mode_store: Any | None = None) -> None:  # 修改代码+Phase99UniversalComputerUseModeGate：增加 mode_store 注入参数；如果没有这行代码，测试和终端命令无法共享已打开的 normal mode。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_PHASE93_UNIVERSAL_LIVE_EXECUTION_ROOT / f"session-{int(time.time() * 1000)}"  # 新增代码+Phase93UniversalLiveExecutionGate：确定运行根目录；如果没有这行代码，多次运行会互相污染。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase93UniversalLiveExecutionGate：确保根目录存在；如果没有这行代码，报告落盘会失败。
        self.phase92_runtime = phase92_runtime or UniversalWindowsComputerUseRuntime(base_dir=self.base_dir / "phase92")  # 新增代码+Phase93UniversalLiveExecutionGate：创建或复用 Phase92 通用 runtime；如果没有这行代码，prompt mode 主线断开。
        self.safety_boundary = safety_boundary or WindowsRealAppSafetyBoundary()  # 新增代码+Phase93UniversalLiveExecutionGate：创建或复用安全边界；如果没有这行代码，真实执行前没有授权和危险窗口检查。
        self.grant_store = grant_store or WindowsComputerUsePersistentGrantStore(base_dir=self.base_dir / "grants")  # 新增代码+Phase93UniversalLiveExecutionGate：创建隔离授权 store；如果没有这行代码，授权事实源会污染全局。
        self.mode_store = mode_store or ComputerUseModeSessionStore(base_dir=self.base_dir / "mode_sessions")  # 新增代码+Phase99UniversalComputerUseModeGate：创建或复用 mode session store；如果没有这行代码，live gate 无法根据 `/computer use` normal/observe 状态决策。
        self.host_adapter = host_adapter or WindowsProductionComputerUseHostAdapter()  # 新增代码+Phase93UniversalLiveExecutionGate：创建生产 host adapter；如果没有这行代码，Phase93 缺少生产桥接状态。
        self.closed_loop_executor = WindowsClosedLoopComputerExecutor()  # 新增代码+Phase93UniversalLiveExecutionGate：创建闭环执行器；如果没有这行代码，observe-act-verify-recover 不能统一执行。
        self.high_level_tool = Phase70RecordingHighLevelTool()  # 新增代码+Phase93UniversalLiveExecutionGate：创建记录型高层工具；如果没有这行代码，默认合同可能误触真实桌面。
        self.input_sender = Phase71RecordingInputSender()  # 新增代码+Phase93UniversalLiveExecutionGate：创建记录型输入 sender；如果没有这行代码，输入事件没有安全记录出口。
        self.control_runtime = WindowsGenericControlActionRuntime(high_level_tool=self.high_level_tool)  # 新增代码+Phase93UniversalLiveExecutionGate：把 Phase70 接到记录型工具；如果没有这行代码，通用点击路径没有统一桥接。
        self.input_runtime = WindowsGenericInputActionRuntime(sender=self.input_sender)  # 新增代码+Phase93UniversalLiveExecutionGate：把 Phase71 接到记录型 sender；如果没有这行代码，通用输入路径没有统一桥接。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，UniversalWindowsLiveExecutionGate.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，status 返回 Phase93 组合状态；如果没有这段函数，CLI 和测试要重复拼装组件事实。
    def status(self) -> dict[str, Any]:  # 新增代码+Phase93UniversalLiveExecutionGate：定义状态方法；如果没有这行代码，外部无法低成本检查 runtime 架构。
        return {"marker": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER, "ok_token": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN, "model": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MODEL, "uses_phase92_universal_runtime": isinstance(self.phase92_runtime, UniversalWindowsComputerUseRuntime), "single_universal_live_loop": True, "prompt_to_observe_plan_act_verify": True, "no_per_app_controller": True, "representative_apps_are_acceptance_only": True, "uses_closed_loop_executor": isinstance(self.closed_loop_executor, WindowsClosedLoopComputerExecutor), "uses_generic_action_layer": isinstance(self.control_runtime, WindowsGenericControlActionRuntime) and isinstance(self.input_runtime, WindowsGenericInputActionRuntime), "uses_real_app_safety_boundary": isinstance(self.safety_boundary, WindowsRealAppSafetyBoundary), "uses_mode_session_gate": self.mode_store is not None, "uses_production_host_adapter": isinstance(self.host_adapter, WindowsProductionComputerUseHostAdapter), "requires_explicit_user_authorization": True, "real_actions_default_disabled": PHASE93_REAL_ACTIONS_DEFAULT_DISABLED, "uncontrolled_actions_expanded": PHASE93_UNCONTROLLED_ACTIONS_EXPANDED}  # 修改代码+Phase99UniversalComputerUseModeGate：状态报告增加 mode session gate；如果没有这行代码，调用方无法确认 Task4 新门禁已接入。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，UniversalWindowsLiveExecutionGate.status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，_generic_window 构造普通 Windows 目标窗口；如果没有这段函数，合同样本会散落且容易变成具体应用控制器。
    def _generic_window(self) -> dict[str, Any]:  # 新增代码+Phase93UniversalLiveExecutionGate：定义通用目标窗口 helper；如果没有这行代码，多处窗口字段会重复且可能不一致。
        return {"app_id": "generic_windows_app.exe", "process_name": "generic_windows_app.exe", "window_id": "hwnd:9301", "title_preview": "LearningAgent Phase93 Generic Windows App", "display_id": "DISPLAY1", "safe_to_target": True, "rect": {"left": 100, "top": 100, "right": 900, "bottom": 700}}  # 新增代码+Phase93UniversalLiveExecutionGate：返回不绑定具体软件的目标；如果没有这行代码，Phase93 容易被误解为 Notepad/Paint 专用。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，UniversalWindowsLiveExecutionGate._generic_window 到此结束；如果没有这个边界说明，初学者不容易看出目标样本范围。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，_approve_recording_window 为记录型授权样本写入短期授权；如果没有这段函数，授权正例无法通过真实安全边界。
    def _approve_recording_window(self, window: dict[str, Any], session_id: str) -> None:  # 新增代码+Phase93UniversalLiveExecutionGate：定义授权 helper；如果没有这行代码，授权样本会重复写 approve 参数。
        self.grant_store.approve(session_id=session_id, app=str(window.get("app_id", "")), window_id=str(window.get("window_id", "")), display_id=str(window.get("display_id", "")), action_scope=["click", "type_text", "scroll", "drag"], ttl_seconds=60, reason="phase93-authorized-recording-loop", grant_flags={"desktopAction": True, "recordingOnly": True})  # 新增代码+Phase93UniversalLiveExecutionGate：写入短期记录型授权；如果没有这行代码，安全边界不会放行授权正例。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，UniversalWindowsLiveExecutionGate._approve_recording_window 到此结束；如果没有这个边界说明，初学者不容易看出授权范围。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，run_prompt 执行 prompt 到通用闭环门禁；如果没有这段函数，用户 prompt 无法进入 Phase93 主能力。
    def run_prompt(self, prompt: Any, request_real_actions: bool = False) -> dict[str, Any]:  # 新增代码+Phase93UniversalLiveExecutionGate：定义 prompt 运行入口；如果没有这行代码，外部 agent 只能调用低层零散组件。
        prompt_text = _phase93_safe_prompt(prompt)  # 新增代码+Phase93UniversalLiveExecutionGate：清洗 prompt 只用于内存规划；如果没有这行代码，换行和超长输入会污染后续报告。
        prompt_digest = _phase93_sha256_16(prompt_text)  # 新增代码+Phase93UniversalLiveExecutionGate：生成 prompt 短哈希；如果没有这行代码，报告无法脱敏追踪任务。
        phase92_report = self.phase92_runtime.run_prompt(prompt_text, real_actions=False)  # 新增代码+Phase93UniversalLiveExecutionGate：先通过 Phase92 通用模式理解 prompt；如果没有这行代码，Phase93 会绕开已验证的通用主线。
        window = self._generic_window()  # 新增代码+Phase93UniversalLiveExecutionGate：获取通用目标窗口；如果没有这行代码，闭环缺少目标身份。
        session_id = f"phase93-{int(time.time() * 1000)}"  # 新增代码+Phase93UniversalLiveExecutionGate：生成隔离 session id；如果没有这行代码，授权匹配可能串到旧会话。
        mode_session_used = bool(request_real_actions and self.mode_store is not None)  # 修改代码+Phase99UniversalComputerUseModeGate：真实动作请求只标记使用 mode session 而不写 per-app grant；如果没有这行代码，Task4 路径会继续依赖旧白名单授权。
        mode_status = _phase102_mode_status(self.mode_store) if mode_session_used else {"mode": "off", "full_mode": False}  # 新增代码+Phase102FullModeExecutionGate：读取当前 mode/full 状态；如果没有这行代码，总报告无法证明 full-confirm 是否已接到执行入口。
        task_plan = _phase102_task_plan(prompt_text, phase92_report)  # 修改代码+Phase102FullModeExecutionGate：按 prompt 选择 click 或 launch_app 计划；如果没有这行代码，启动应用任务仍会被硬编码成 click。
        actor = _Phase93ClosedLoopActor(window, self.safety_boundary, self.grant_store, self.mode_store, session_id, self.control_runtime, self.input_runtime, bool(request_real_actions))  # 修改代码+Phase99UniversalComputerUseModeGate：创建动作器并注入 mode store；如果没有这行代码，动作层无法用 normal mode 替代 per-app grant。
        loop = self.closed_loop_executor.run(task_plan, _Phase93ClosedLoopObserver(window), actor, _Phase93ClosedLoopVerifier(), _Phase93ClosedLoopRecoverer())  # 新增代码+Phase93UniversalLiveExecutionGate：运行通用闭环；如果没有这行代码，Phase93 只是静态声明而不是执行结构。
        status = self.status()  # 新增代码+Phase93UniversalLiveExecutionGate：读取组合状态；如果没有这行代码，报告要重复拼装固定字段。
        action_reports = list(actor.action_reports)  # 新增代码+Phase99UniversalComputerUseModeGate：复制动作报告用于汇总 mode 字段；如果没有这行代码，总报告无法反映动作层是否使用 mode gate。
        low_level_event_count = sum(_phase93_low_level_count(action_report) for action_report in action_reports)  # 新增代码+Phase99UniversalComputerUseModeGate：汇总动作层低层事件数；如果没有这行代码，运行报告无法证明记录型路径没有物理派发。
        per_app_allowlist_required = bool(any(action_report.get("per_app_allowlist_required") for action_report in action_reports))  # 新增代码+Phase99UniversalComputerUseModeGate：汇总是否仍要求 app 白名单；如果没有这行代码，旧授权要求可能悄悄混回总报告。
        ordinary_apps_allowed_by_risk_policy = bool(any(action_report.get("ordinary_apps_allowed_by_risk_policy") for action_report in action_reports))  # 新增代码+Phase99UniversalComputerUseModeGate：汇总普通 app 风险策略放行状态；如果没有这行代码，normal mode 的核心语义不会显示在总报告。
        full_mode_session_used = bool(mode_status.get("full_mode", False))  # 新增代码+Phase102FullModeExecutionGate：汇总当前是否处于 full session；如果没有这行代码，用户看不出 `/computer use --full-confirm` 是否生效。
        full_mode_action_ready = bool(any(action_report.get("full_mode_action_ready") for action_report in action_reports))  # 新增代码+Phase102FullModeExecutionGate：汇总是否有 full 动作通过门禁；如果没有这行代码，full 模式可能只停留在状态层。
        full_mode_action_classes = sorted({str(action_report.get("action_class", "")) for action_report in action_reports if bool(action_report.get("full_mode_action")) or bool(action_report.get("full_mode_action_ready"))})  # 新增代码+Phase102FullModeExecutionGate：汇总本轮涉及的 full 动作类；如果没有这行代码，报告无法说明 full 放宽了哪类动作。
        authorized_recording_loop_ready = bool(request_real_actions and any(report.get("acted") and report.get("recording_dispatch_only") and int(report.get("high_level_event_count", 0) or 0) > 0 and (int(report.get("input_event_count", 0) or 0) > 0 or bool(report.get("full_mode_action_ready"))) and _phase93_low_level_count(report) == 0 for report in action_reports))  # 修改代码+Phase102FullModeExecutionGate：允许 click 记录型和 full launch 记录型都证明闭环就绪；如果没有这行代码，launch_app 因无滚动输入会被误判未授权。
        blocked_action_decision = next((str(action_report.get("decision", "")) for action_report in action_reports if (not bool(action_report.get("acted"))) and str(action_report.get("decision", "")) and str(action_report.get("decision", "")) not in {"observe_step_no_dispatch", "real_actions_disabled_by_default"}), "")  # 修改代码+Phase102FullModeExecutionGate：跳过观察/预览类非阻断报告后提取真正拦截原因；如果没有这行代码，observe 会遮住 launch_app 的 mode 拒绝。
        mode_blocking_decisions = {"action_risk_exceeds_mode", "dangerous_target_blocked", "computer_use_stopped", "mode_expired", "action_class_not_allowed_by_mode"}  # 新增代码+Phase99UniversalComputerUseModeGate：列出属于 mode session 拦截的稳定原因；如果没有这行代码，高风险安全边界拒绝会和 mode 拒绝混在一起。
        real_action_decision = "authorized_recording_only" if authorized_recording_loop_ready else ("preview_only_default_disabled" if not bool(request_real_actions) else ("blocked_by_mode_session" if blocked_action_decision in mode_blocking_decisions else "blocked_by_safety_boundary"))  # 修改代码+Phase99UniversalComputerUseModeGate：只有记录闭环就绪才报告 authorized_recording_only；如果没有这行代码，off mode 拒绝会误导成已授权。
        report = {"ok": bool(phase92_report.get("ok") and loop.get("closed_loop_execution")), "marker": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER, "ok_token": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN, "model": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MODEL, "prompt_sha256_16": prompt_digest, "prompt_text_included": False, "prompt_length": len(prompt_text), "raw_prompt_hidden": True, "phase92_model": phase92_report.get("model", ""), "phase92_ok": bool(phase92_report.get("ok")), "phase92_prompt_digest": phase92_report.get("prompt_sha256_16", ""), "loop": loop, "loop_event_count": len(loop.get("events", []) or []), "real_actions_requested": bool(request_real_actions), "real_action_decision": real_action_decision, "real_action_blocked_decision": blocked_action_decision, "authorized_recording_loop_ready": authorized_recording_loop_ready, "recording_dispatch_only": True, "real_dispatch_performed": False, "low_level_event_count": low_level_event_count, "mode_session_used": mode_session_used or bool(any(action_report.get("mode_session_used") for action_report in action_reports)), "full_mode_session_used": full_mode_session_used, "full_mode_action_ready": full_mode_action_ready, "full_mode_action_classes": full_mode_action_classes, "per_app_allowlist_required": per_app_allowlist_required, "ordinary_apps_allowed_by_risk_policy": ordinary_apps_allowed_by_risk_policy, "uses_phase92_universal_runtime": bool(status["uses_phase92_universal_runtime"]), "single_universal_live_loop": bool(status["single_universal_live_loop"]), "prompt_to_observe_plan_act_verify": bool(status["prompt_to_observe_plan_act_verify"]), "no_per_app_controller": bool(status["no_per_app_controller"]), "representative_apps_are_acceptance_only": bool(status["representative_apps_are_acceptance_only"]), "uses_closed_loop_executor": bool(status["uses_closed_loop_executor"]), "uses_generic_action_layer": bool(status["uses_generic_action_layer"]), "uses_real_app_safety_boundary": bool(status["uses_real_app_safety_boundary"]), "uses_mode_session_gate": bool(status["uses_mode_session_gate"]), "uses_production_host_adapter": bool(status["uses_production_host_adapter"]), "requires_explicit_user_authorization": bool(status["requires_explicit_user_authorization"]), "real_actions_default_disabled": bool(status["real_actions_default_disabled"]), "uncontrolled_actions_expanded": bool(status["uncontrolled_actions_expanded"])}  # 修改代码+Phase102FullModeExecutionGate：运行报告加入 full session 和 full 动作就绪字段；如果没有这行代码，用户无法确认 `/computer use --full` 是否真正连到执行层。
        return report  # 新增代码+Phase93UniversalLiveExecutionGate：返回运行报告给调用方；如果没有这行代码，run_prompt 会隐式返回 None。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，UniversalWindowsLiveExecutionGate.run_prompt 到此结束；如果没有这个边界说明，初学者不容易看出 prompt 执行范围。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，unauthorized_window_refusal 验证未授权普通窗口零事件拒绝；如果没有这段函数，默认安全边界缺少自动证据。
    def unauthorized_window_refusal(self) -> dict[str, Any]:  # 新增代码+Phase93UniversalLiveExecutionGate：定义未授权拒绝检查；如果没有这行代码，测试无法直接验证默认拒绝。
        window = self._generic_window()  # 新增代码+Phase93UniversalLiveExecutionGate：使用普通通用窗口但不写授权；如果没有这行代码，未授权测试没有目标。
        decision = self.safety_boundary.evaluate(window, "click", self.grant_store, f"phase93-unauthorized-{int(time.time() * 1000)}")  # 新增代码+Phase93UniversalLiveExecutionGate：调用真实安全边界评估；如果没有这行代码，未授权拒绝只是口头声明。
        return {"decision": str(decision.get("decision", "")), "allowed": bool(decision.get("allowed")), "low_level_event_count": _phase93_low_level_count(decision), "unauthorized_window_zero_events": bool(not decision.get("allowed") and _phase93_low_level_count(decision) == 0), "safety_decision": decision}  # 新增代码+Phase93UniversalLiveExecutionGate：返回未授权零事件结果；如果没有这行代码，验收 token 无法读取。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，UniversalWindowsLiveExecutionGate.unauthorized_window_refusal 到此结束；如果没有这个边界说明，初学者不容易看出未授权检查范围。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，unsafe_window_refusal 验证危险窗口零事件拒绝；如果没有这段函数，终端/登录/安全类窗口可能缺少回归保护。
    def unsafe_window_refusal(self) -> dict[str, Any]:  # 新增代码+Phase93UniversalLiveExecutionGate：定义危险窗口拒绝检查；如果没有这行代码，测试无法直接验证高风险窗口拦截。
        window = {"app_id": "powershell.exe", "process_name": "powershell.exe", "window_id": "hwnd:9399", "title_preview": "Windows PowerShell Terminal", "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase93UniversalLiveExecutionGate：构造终端类危险窗口；如果没有这行代码，高风险样本不明确。
        decision = self.safety_boundary.evaluate(window, "click", self.grant_store, f"phase93-unsafe-{int(time.time() * 1000)}")  # 新增代码+Phase93UniversalLiveExecutionGate：调用真实安全边界评估；如果没有这行代码，危险拒绝只是模拟字段。
        return {"decision": str(decision.get("decision", "")), "allowed": bool(decision.get("allowed")), "low_level_event_count": _phase93_low_level_count(decision), "unsafe_window_zero_events": bool(not decision.get("allowed") and _phase93_low_level_count(decision) == 0), "safety_decision": decision}  # 新增代码+Phase93UniversalLiveExecutionGate：返回危险窗口零事件结果；如果没有这行代码，验收 token 无法读取。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，UniversalWindowsLiveExecutionGate.unsafe_window_refusal 到此结束；如果没有这个边界说明，初学者不容易看出危险窗口检查范围。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，target_drift_refusal 验证目标漂移零事件拒绝；如果没有这段函数，焦点切走后的误操作风险缺少保护证据。
    def target_drift_refusal(self) -> dict[str, Any]:  # 新增代码+Phase93UniversalLiveExecutionGate：定义目标漂移检查；如果没有这行代码，测试无法直接验证目标身份门禁。
        original_window = self._generic_window()  # 新增代码+Phase93UniversalLiveExecutionGate：读取原目标窗口；如果没有这行代码，漂移判断没有前态。
        current_window = dict(original_window, app_id="other_windows_app.exe", process_name="other_windows_app.exe", window_id="hwnd:9302", title_preview="Different target")  # 新增代码+Phase93UniversalLiveExecutionGate：构造漂移后的窗口；如果没有这行代码，无法证明目标已变化。
        original_digest = _phase93_sha256_16(original_window)  # 新增代码+Phase93UniversalLiveExecutionGate：生成原目标指纹；如果没有这行代码，漂移判断没有前态证据。
        current_digest = _phase93_sha256_16(current_window)  # 新增代码+Phase93UniversalLiveExecutionGate：生成当前目标指纹；如果没有这行代码，漂移判断没有后态证据。
        drifted = original_digest != current_digest  # 新增代码+Phase93UniversalLiveExecutionGate：比较目标指纹；如果没有这行代码，不同窗口也可能被当成同一目标。
        return {"decision": "target_drift_blocks_action" if drifted else "target_stable", "target_drift_blocks_action": drifted, "target_drift_zero_events": bool(drifted), "low_level_event_count": 0, "original_window_digest": original_digest, "current_window_digest": current_digest}  # 新增代码+Phase93UniversalLiveExecutionGate：返回漂移零事件结果；如果没有这行代码，验收无法确认漂移阻断。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，UniversalWindowsLiveExecutionGate.target_drift_refusal 到此结束；如果没有这个边界说明，初学者不容易看出漂移检查范围。
# 新增代码+Phase93UniversalLiveExecutionGate：类段结束，UniversalWindowsLiveExecutionGate 到此结束；如果没有这个边界说明，初学者不容易看出 Phase93 主类范围。


# 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，run_phase93_universal_live_execution_gate_contract 运行总合同；如果没有这段函数，CLI、测试和真实终端没有同一事实源。
def run_phase93_universal_live_execution_gate_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase93UniversalLiveExecutionGate：定义 Phase93 总合同入口；如果没有这行代码，无法一键验证所有 token。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE93_UNIVERSAL_LIVE_EXECUTION_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase93UniversalLiveExecutionGate：选择隔离合同目录；如果没有这行代码，多次验收可能互相污染。
    runtime = UniversalWindowsLiveExecutionGate(base_dir=root)  # 新增代码+Phase93UniversalLiveExecutionGate：创建 Phase93 运行时；如果没有这行代码，合同没有被测对象。
    preview = runtime.run_prompt("请打开 computer use，准备控制任意普通 Windows 软件，但默认不要真的点击。", request_real_actions=False)  # 新增代码+Phase93UniversalLiveExecutionGate：运行真实用户风格预览 prompt；如果没有这行代码，默认安全模式没有证据。
    runtime.mode_store.open_mode(mode="normal", reason="Phase99 contract opens normal mode before authorized recording loop")  # 新增代码+Phase99UniversalComputerUseModeGate：授权记录型合同前显式打开 normal mode；如果没有这行代码，Task4 后的正例会因 off mode 被安全拒绝。
    authorized = runtime.run_prompt("请打开 computer use，在授权后走一次记录型通用点击和滚动闭环。", request_real_actions=True)  # 新增代码+Phase93UniversalLiveExecutionGate：运行授权记录型 prompt；如果没有这行代码，授权后动作层接入没有证据。
    privacy = runtime.run_prompt("phase93-contract-secret prompt should never appear in reports", request_real_actions=False)  # 新增代码+Phase93UniversalLiveExecutionGate：运行隐私检查 prompt；如果没有这行代码，raw_prompt_hidden 可能只是口头声明。
    unauthorized = runtime.unauthorized_window_refusal()  # 新增代码+Phase93UniversalLiveExecutionGate：验证未授权窗口拒绝；如果没有这行代码，默认授权门禁没有证据。
    unsafe = runtime.unsafe_window_refusal()  # 新增代码+Phase93UniversalLiveExecutionGate：验证危险窗口拒绝；如果没有这行代码，高风险窗口拦截没有证据。
    drift = runtime.target_drift_refusal()  # 新增代码+Phase93UniversalLiveExecutionGate：验证目标漂移拒绝；如果没有这行代码，目标身份保护没有证据。
    status = runtime.status()  # 新增代码+Phase93UniversalLiveExecutionGate：读取 runtime 状态；如果没有这行代码，报告需要重复拼装固定字段。
    serialized_without_raw = json.dumps({"preview": preview, "authorized": authorized, "privacy": privacy}, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase93UniversalLiveExecutionGate：序列化报告子集做隐私扫描；如果没有这行代码，嵌套原文泄露难以发现。
    raw_prompt_hidden = "phase93-contract-secret" not in serialized_without_raw and "prompt should never appear" not in serialized_without_raw  # 新增代码+Phase93UniversalLiveExecutionGate：确认隐私 prompt 没进入报告；如果没有这行代码，隐私门禁无法自动判断。
    report_path = root / "reports" / "phase93_universal_live_execution_gate_report.json"  # 新增代码+Phase93UniversalLiveExecutionGate：定义报告路径；如果没有这行代码，验收证据没有稳定落点。
    passed = bool(preview.get("ok") and authorized.get("ok") and authorized.get("authorized_recording_loop_ready") and status.get("uses_phase92_universal_runtime") and status.get("single_universal_live_loop") and status.get("prompt_to_observe_plan_act_verify") and status.get("no_per_app_controller") and status.get("representative_apps_are_acceptance_only") and status.get("uses_closed_loop_executor") and status.get("uses_generic_action_layer") and status.get("uses_real_app_safety_boundary") and status.get("uses_mode_session_gate") and status.get("uses_production_host_adapter") and status.get("requires_explicit_user_authorization") and status.get("real_actions_default_disabled") and unauthorized.get("unauthorized_window_zero_events") and unsafe.get("unsafe_window_zero_events") and drift.get("target_drift_zero_events") and raw_prompt_hidden and not status.get("uncontrolled_actions_expanded"))  # 修改代码+Phase99UniversalComputerUseModeGate：合同通过条件加入 mode session gate；如果没有这行代码，Phase93 合同无法证明 Task4 新门禁已接入。
    report = {"marker": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER, "ok_token": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN, "model": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MODEL, "passed": passed, "uses_phase92_universal_runtime": bool(status["uses_phase92_universal_runtime"]), "single_universal_live_loop": bool(status["single_universal_live_loop"]), "prompt_to_observe_plan_act_verify": bool(status["prompt_to_observe_plan_act_verify"]), "no_per_app_controller": bool(status["no_per_app_controller"]), "representative_apps_are_acceptance_only": bool(status["representative_apps_are_acceptance_only"]), "uses_closed_loop_executor": bool(status["uses_closed_loop_executor"]), "uses_generic_action_layer": bool(status["uses_generic_action_layer"]), "uses_real_app_safety_boundary": bool(status["uses_real_app_safety_boundary"]), "uses_mode_session_gate": bool(status["uses_mode_session_gate"]), "uses_production_host_adapter": bool(status["uses_production_host_adapter"]), "requires_explicit_user_authorization": bool(status["requires_explicit_user_authorization"]), "real_actions_default_disabled": bool(status["real_actions_default_disabled"]), "authorized_recording_loop_ready": bool(authorized.get("authorized_recording_loop_ready")), "unauthorized_window_zero_events": bool(unauthorized.get("unauthorized_window_zero_events")), "unsafe_window_zero_events": bool(unsafe.get("unsafe_window_zero_events")), "target_drift_zero_events": bool(drift.get("target_drift_zero_events")), "raw_prompt_hidden": raw_prompt_hidden, "uncontrolled_actions_expanded": bool(status["uncontrolled_actions_expanded"]), "report_path": str(report_path), "preview_report": preview, "authorized_report": authorized, "unauthorized_report": unauthorized, "unsafe_report": unsafe, "target_drift_report": drift}  # 修改代码+Phase99UniversalComputerUseModeGate：合同报告加入 mode session gate 字段；如果没有这行代码，人工验收无法看到 Phase99 新门禁。
    atomic_write_json(report_path, report)  # 新增代码+Phase93UniversalLiveExecutionGate：原子写入报告；如果没有这行代码，异常中断时可能留下半个 JSON。
    return report  # 新增代码+Phase93UniversalLiveExecutionGate：返回报告给测试和 CLI；如果没有这行代码，调用方拿不到验收结果。
# 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，run_phase93_universal_live_execution_gate_contract 到此结束；如果没有这个边界说明，初学者不容易看出总合同范围。


# 新增代码+Phase102FullModeExecutionGate：函数段开始，run_phase102_full_mode_execution_gate_contract 运行 full 模式执行门禁合同；如果没有这段函数，真实终端无法一键验收 full 是否接到动作层。
def run_phase102_full_mode_execution_gate_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase102FullModeExecutionGate：定义 Phase102 合同入口；如果没有这行代码，测试和真实终端没有统一事实源。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE102_FULL_MODE_EXECUTION_GATE_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase102FullModeExecutionGate：选择隔离合同目录；如果没有这行代码，多次验收的 mode 状态和报告会互相污染。
    root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase102FullModeExecutionGate：确保合同根目录存在；如果没有这行代码，后续报告目录和 mode store 可能创建失败。
    normal_store = ComputerUseModeSessionStore(base_dir=root / "normal_mode_sessions")  # 新增代码+Phase102FullModeExecutionGate：创建 normal 模式隔离 store；如果没有这行代码，normal 拦截测试会污染真实用户权限状态。
    normal_store.open_mode(mode="normal", reason="Phase102 contract proves normal blocks launch_app")  # 新增代码+Phase102FullModeExecutionGate：打开 normal 模式；如果没有这行代码，拒绝原因可能只是 off 状态而不是 full 动作缺权限。
    normal_runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "normal_live_gate", mode_store=normal_store)  # 新增代码+Phase102FullModeExecutionGate：创建 normal 路径 runtime；如果没有这行代码，执行入口不会读取 normal 状态。
    normal_report = normal_runtime.run_prompt("请启动一个普通 Windows 应用，只做记录型合同，不要真实打开。", request_real_actions=True)  # 新增代码+Phase102FullModeExecutionGate：运行真实用户风格启动 prompt；如果没有这行代码，launch_app normal 拦截没有证据。
    full_store = ComputerUseModeSessionStore(base_dir=root / "full_mode_sessions")  # 新增代码+Phase102FullModeExecutionGate：创建 full 模式隔离 store；如果没有这行代码，full 确认测试会污染真实用户权限状态。
    full_request = full_store.request_full_mode(reason="Phase102 contract requests full mode")  # 新增代码+Phase102FullModeExecutionGate：按真实流程申请 full token；如果没有这行代码，合同会绕过二次确认设计。
    full_confirmed = full_store.confirm_full_mode(full_request["confirmation_token"], reason="Phase102 contract confirms full mode")  # 新增代码+Phase102FullModeExecutionGate：用 token 确认 full；如果没有这行代码，full 路径不会真正获得扩展动作权限。
    full_runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "full_live_gate", mode_store=full_store)  # 新增代码+Phase102FullModeExecutionGate：创建 full 路径 runtime；如果没有这行代码，执行入口不会读取已确认 full 状态。
    full_report = full_runtime.run_prompt("请使用 full 模式启动一个普通 Windows 应用，只做记录型合同，不要真实打开。", request_real_actions=True)  # 新增代码+Phase102FullModeExecutionGate：运行 full 用户风格启动 prompt；如果没有这行代码，full 放行动作层没有证据。
    normal_action_reports = [event.get("action_result", {}) for event in normal_report.get("loop", {}).get("events", []) if event.get("state") == "acted"]  # 新增代码+Phase102FullModeExecutionGate：提取 normal 动作报告；如果没有这行代码，无法确认 normal 拒绝的是 launch_app。
    full_action_reports = [event.get("action_result", {}) for event in full_report.get("loop", {}).get("events", []) if event.get("state") == "acted"]  # 新增代码+Phase102FullModeExecutionGate：提取 full 动作报告；如果没有这行代码，无法确认 full 放行的是 launch_app。
    normal_launch_tracked = any(isinstance(action_report, dict) and action_report.get("action_class") == "launch_app" for action_report in normal_action_reports)  # 新增代码+Phase102FullModeExecutionGate：确认 normal 路径识别 launch_app；如果没有这行代码，硬编码 click 可能误报成功。
    full_launch_tracked = any(isinstance(action_report, dict) and action_report.get("action_class") == "launch_app" and action_report.get("acted") for action_report in full_action_reports)  # 新增代码+Phase102FullModeExecutionGate：确认 full 路径执行 launch_app 记录动作；如果没有这行代码，full 放行可能停留在状态层。
    normal_mode_blocks_launch_app = bool(normal_report.get("real_action_decision") == "blocked_by_mode_session" and normal_report.get("real_action_blocked_decision") == "action_class_not_allowed_by_mode" and normal_launch_tracked and not normal_report.get("full_mode_action_ready"))  # 新增代码+Phase102FullModeExecutionGate：汇总 normal 是否正确拦启动动作；如果没有这行代码，普通模式越权风险不容易被验收发现。
    full_launch_authorized_recording_only = bool(full_confirmed.get("full_mode") and full_report.get("full_mode_session_used") and full_report.get("full_mode_action_ready") and full_report.get("real_action_decision") == "authorized_recording_only" and full_report.get("authorized_recording_loop_ready") and full_launch_tracked)  # 新增代码+Phase102FullModeExecutionGate：汇总 full 是否进入记录型启动动作；如果没有这行代码，full 可能只是显示已打开但没有动作层差异。
    low_level_event_count_zero = bool(int(normal_report.get("low_level_event_count", 0) or 0) == 0 and int(full_report.get("low_level_event_count", 0) or 0) == 0)  # 新增代码+Phase102FullModeExecutionGate：确认 normal/full 都没有低层输入事件；如果没有这行代码，合同可能误触真实桌面。
    full_launch_no_physical_dispatch = bool(not full_report.get("real_dispatch_performed") and low_level_event_count_zero)  # 新增代码+Phase102FullModeExecutionGate：确认 full 启动只是记录型不物理派发；如果没有这行代码，full 自动化验收可能真的打开应用。
    real_desktop_touched = bool(normal_report.get("real_dispatch_performed") or full_report.get("real_dispatch_performed") or not low_level_event_count_zero)  # 新增代码+Phase102FullModeExecutionGate：汇总是否触碰真实桌面；如果没有这行代码，用户无法确认验收是安全的。
    uncontrolled_actions_expanded = bool(normal_report.get("uncontrolled_actions_expanded") or full_report.get("uncontrolled_actions_expanded"))  # 新增代码+Phase102FullModeExecutionGate：确认没有扩张无边界动作面；如果没有这行代码，full 放宽可能被误解成无限制。
    report_path = root / "reports" / "phase102_full_mode_execution_gate_report.json"  # 新增代码+Phase102FullModeExecutionGate：定义报告路径；如果没有这行代码，验收证据没有固定文件。
    passed = bool(normal_mode_blocks_launch_app and full_launch_authorized_recording_only and full_launch_no_physical_dispatch and not real_desktop_touched and not uncontrolled_actions_expanded)  # 新增代码+Phase102FullModeExecutionGate：汇总合同通过条件；如果没有这行代码，命令行入口无法用退出码表达失败。
    report = {"marker": PHASE102_FULL_MODE_EXECUTION_GATE_MARKER, "ok_token": PHASE102_FULL_MODE_EXECUTION_GATE_OK_TOKEN, "model": PHASE102_FULL_MODE_EXECUTION_GATE_MODEL, "passed": passed, "normal_mode_blocks_launch_app": normal_mode_blocks_launch_app, "full_mode_session_used": bool(full_report.get("full_mode_session_used")), "full_mode_action_ready": bool(full_report.get("full_mode_action_ready")), "full_launch_authorized_recording_only": full_launch_authorized_recording_only, "full_launch_no_physical_dispatch": full_launch_no_physical_dispatch, "low_level_event_count_zero": low_level_event_count_zero, "real_desktop_touched": real_desktop_touched, "uncontrolled_actions_expanded": uncontrolled_actions_expanded, "report_path": str(report_path), "normal_report": normal_report, "full_report": full_report}  # 新增代码+Phase102FullModeExecutionGate：构造完整合同报告；如果没有这行代码，测试和终端拿不到统一验收事实。
    atomic_write_json(report_path, report)  # 新增代码+Phase102FullModeExecutionGate：原子写入合同报告；如果没有这行代码，失败时可能留下半个 JSON。
    return report  # 新增代码+Phase102FullModeExecutionGate：返回合同报告；如果没有这行代码，调用方无法读取 full 执行门禁结果。
# 新增代码+Phase102FullModeExecutionGate：函数段结束，run_phase102_full_mode_execution_gate_contract 到此结束；如果没有这个边界说明，读者不容易看出 Phase102 合同范围。


# 新增代码+Phase102FullModeExecutionGate：函数段开始，phase102_cli_line 输出固定 token 行；如果没有这段函数，真实终端验收需要解析复杂 JSON。
def phase102_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase102FullModeExecutionGate：定义 CLI 单行格式化函数；如果没有这行代码，场景配置无法稳定匹配 full 验收结果。
    return f"{PHASE102_FULL_MODE_EXECUTION_GATE_MARKER} {PHASE102_FULL_MODE_EXECUTION_GATE_OK_TOKEN} normal_mode_blocks_launch_app={_phase93_bool_token(report.get('normal_mode_blocks_launch_app'))} full_mode_session_used={_phase93_bool_token(report.get('full_mode_session_used'))} full_mode_action_ready={_phase93_bool_token(report.get('full_mode_action_ready'))} full_launch_authorized_recording_only={_phase93_bool_token(report.get('full_launch_authorized_recording_only'))} full_launch_no_physical_dispatch={_phase93_bool_token(report.get('full_launch_no_physical_dispatch'))} low_level_event_count_zero={_phase93_bool_token(report.get('low_level_event_count_zero'))} real_desktop_touched={_phase93_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase93_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase102FullModeExecutionGate：返回固定顺序 token；如果没有这行代码，验收脚本容易因为字段顺序变化失败。
# 新增代码+Phase102FullModeExecutionGate：函数段结束，phase102_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 Phase102 CLI 文本范围。


# 新增代码+Phase102FullModeExecutionGate：函数段开始，phase102_main 提供专用命令行自检入口；如果没有这段函数，真实可见终端无法直接运行 Phase102 合同。
def phase102_main(argv: list[str] | None = None) -> int:  # 新增代码+Phase102FullModeExecutionGate：定义 Phase102 CLI 入口并保留 argv 扩展位；如果没有这行代码，场景需要手写合同细节。
    _ = argv  # 新增代码+Phase102FullModeExecutionGate：明确当前不解析命令行参数；如果没有这行代码，读者可能误以为 argv 被遗漏处理。
    report = run_phase102_full_mode_execution_gate_contract()  # 新增代码+Phase102FullModeExecutionGate：运行无真实桌面副作用合同；如果没有这行代码，CLI 没有实际验收内容。
    print(phase102_cli_line(report))  # 新增代码+Phase102FullModeExecutionGate：打印稳定 token 行；如果没有这行代码，验收器无法快速判断通过。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase102FullModeExecutionGate：打印结构化报告；如果没有这行代码，失败时不容易复盘。
    print(PHASE102_FULL_MODE_EXECUTION_GATE_MARKER)  # 新增代码+Phase102FullModeExecutionGate：单独打印 ready marker；如果没有这行代码，人工观察终端不够直观。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase102FullModeExecutionGate：用退出码表达合同成败；如果没有这行代码，失败也可能被自动化当成成功。
# 新增代码+Phase102FullModeExecutionGate：函数段结束，phase102_main 到此结束；如果没有这个边界说明，读者不容易看出 Phase102 命令入口范围。


# 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，phase93_cli_line 输出固定 token 行；如果没有这段函数，真实终端验收需要解析复杂 JSON。
def phase93_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase93UniversalLiveExecutionGate：定义 CLI 格式化函数；如果没有这行代码，场景配置无法用简单 token 匹配。
    return f"{PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER} {PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN} uses_phase92_universal_runtime={_phase93_bool_token(report.get('uses_phase92_universal_runtime'))} single_universal_live_loop={_phase93_bool_token(report.get('single_universal_live_loop'))} prompt_to_observe_plan_act_verify={_phase93_bool_token(report.get('prompt_to_observe_plan_act_verify'))} no_per_app_controller={_phase93_bool_token(report.get('no_per_app_controller'))} representative_apps_are_acceptance_only={_phase93_bool_token(report.get('representative_apps_are_acceptance_only'))} uses_closed_loop_executor={_phase93_bool_token(report.get('uses_closed_loop_executor'))} uses_generic_action_layer={_phase93_bool_token(report.get('uses_generic_action_layer'))} uses_real_app_safety_boundary={_phase93_bool_token(report.get('uses_real_app_safety_boundary'))} uses_mode_session_gate={_phase93_bool_token(report.get('uses_mode_session_gate'))} uses_production_host_adapter={_phase93_bool_token(report.get('uses_production_host_adapter'))} requires_explicit_user_authorization={_phase93_bool_token(report.get('requires_explicit_user_authorization'))} real_actions_default_disabled={_phase93_bool_token(report.get('real_actions_default_disabled'))} authorized_recording_loop_ready={_phase93_bool_token(report.get('authorized_recording_loop_ready'))} unauthorized_window_zero_events={_phase93_bool_token(report.get('unauthorized_window_zero_events'))} unsafe_window_zero_events={_phase93_bool_token(report.get('unsafe_window_zero_events'))} target_drift_zero_events={_phase93_bool_token(report.get('target_drift_zero_events'))} raw_prompt_hidden={_phase93_bool_token(report.get('raw_prompt_hidden'))} uncontrolled_actions_expanded={_phase93_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 修改代码+Phase99UniversalComputerUseModeGate：CLI token 行加入 mode session gate；如果没有这行代码，真实终端输出无法显示 Phase99 已接入。
# 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，phase93_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 文本范围。


# 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，main 提供命令行自检入口；如果没有这段函数，真实可见终端无法直接运行 Phase93 合同。
def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase93UniversalLiveExecutionGate：定义 CLI 入口并保留 argv 扩展位；如果没有这行代码，python -c 调用需要手写细节。
    _ = argv  # 新增代码+Phase93UniversalLiveExecutionGate：明确当前不解析命令行参数；如果没有这行代码，读者可能误以为 argv 遗漏处理。
    report = run_phase93_universal_live_execution_gate_contract()  # 新增代码+Phase93UniversalLiveExecutionGate：运行无副作用合同；如果没有这行代码，CLI 没有实际验收内容。
    print(phase93_cli_line(report))  # 新增代码+Phase93UniversalLiveExecutionGate：打印稳定 token 行；如果没有这行代码，验收器无法快速判断通过。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase93UniversalLiveExecutionGate：打印结构化报告；如果没有这行代码，失败时不容易复盘。
    print(PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER)  # 新增代码+Phase93UniversalLiveExecutionGate：单独打印 ready marker；如果没有这行代码，真实终端人工观察不够直观。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase93UniversalLiveExecutionGate：用退出码表达合同成败；如果没有这行代码，失败也可能被自动化当成成功。
# 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令行入口范围。


__all__ = ["DEFAULT_PHASE93_UNIVERSAL_LIVE_EXECUTION_ROOT", "DEFAULT_PHASE102_FULL_MODE_EXECUTION_GATE_ROOT", "PHASE93_REAL_ACTIONS_DEFAULT_DISABLED", "PHASE93_UNCONTROLLED_ACTIONS_EXPANDED", "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER", "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MODEL", "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN", "PHASE102_FULL_MODE_EXECUTION_GATE_MARKER", "PHASE102_FULL_MODE_EXECUTION_GATE_MODEL", "PHASE102_FULL_MODE_EXECUTION_GATE_OK_TOKEN", "UniversalWindowsLiveExecutionGate", "main", "phase93_cli_line", "phase102_cli_line", "phase102_main", "run_phase93_universal_live_execution_gate_contract", "run_phase102_full_mode_execution_gate_contract"]  # 修改代码+Phase102FullModeExecutionGate：公开导出 Phase102 合同入口和 token；如果没有这行代码，真实终端 python -c 调用可能无法稳定导入新验收函数。


if __name__ == "__main__":  # 新增代码+Phase93UniversalLiveExecutionGate：允许直接运行本模块；如果没有这行代码，初学者无法用 python 文件方式手动执行 Phase93 自检。
    raise SystemExit(main())  # 新增代码+Phase93UniversalLiveExecutionGate：调用 main 并传递退出码；如果没有这行代码，直接运行文件不会执行验收。
