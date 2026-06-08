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
    from learning_agent.computer_use.persistent_grants import WindowsComputerUsePersistentGrantStore  # 新增代码+Phase93UniversalLiveExecutionGate：复用 Phase60 持久授权事实源；如果没有这行代码，真实执行门禁没有可审计授权来源。
    from learning_agent.computer_use.production_live_control import WindowsProductionComputerUseHostAdapter  # 新增代码+Phase93UniversalLiveExecutionGate：复用 Phase76-89 生产 host adapter；如果没有这行代码，Phase93 无法连接生产级桥接结构。
    from learning_agent.computer_use.real_app_safety_boundary import WindowsRealAppSafetyBoundary  # 新增代码+Phase93UniversalLiveExecutionGate：复用 Phase72 真实应用安全边界；如果没有这行代码，危险窗口和未授权窗口无法统一拒绝。
    from learning_agent.computer_use.universal_mode import UniversalWindowsComputerUseRuntime  # 新增代码+Phase93UniversalLiveExecutionGate：复用 Phase92 单一通用 prompt mode；如果没有这行代码，Phase93 可能重复造一个偏离主线的 runtime。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase93UniversalLiveExecutionGate：复用项目原子 JSON 写入工具；如果没有这行代码，验收报告可能半写损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase93UniversalLiveExecutionGate：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，真实可见终端入口可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase93UniversalLiveExecutionGate：只对包路径缺失做 fallback；如果没有这行代码，真实内部 bug 会被误吞。
        raise  # 新增代码+Phase93UniversalLiveExecutionGate：重新抛出非路径类导入错误；如果没有这行代码，依赖内部错误会被隐藏。
    from computer_use.closed_loop_executor import WindowsClosedLoopComputerExecutor  # type: ignore  # 新增代码+Phase93UniversalLiveExecutionGate：脚本模式复用 Phase68 闭环执行器；如果没有这行代码，bat 入口无法运行 Phase93。
    from computer_use.generic_control_actions import Phase70RecordingHighLevelTool, WindowsGenericControlActionRuntime  # type: ignore  # 新增代码+Phase93UniversalLiveExecutionGate：脚本模式复用 Phase70 通用动作层；如果没有这行代码，bat 入口缺少通用控制能力。
    from computer_use.generic_input_actions import Phase71RecordingInputSender, WindowsGenericInputActionRuntime  # type: ignore  # 新增代码+Phase93UniversalLiveExecutionGate：脚本模式复用 Phase71 输入事件层；如果没有这行代码，bat 入口缺少通用输入能力。
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
    def __init__(self, window: dict[str, Any], safety_boundary: WindowsRealAppSafetyBoundary, grant_store: WindowsComputerUsePersistentGrantStore, session_id: str, control_runtime: WindowsGenericControlActionRuntime, input_runtime: WindowsGenericInputActionRuntime, request_real_actions: bool) -> None:  # 新增代码+Phase93UniversalLiveExecutionGate：定义初始化方法；如果没有这行代码，actor 无法获得所需依赖。
        self.window = dict(window)  # 新增代码+Phase93UniversalLiveExecutionGate：复制目标窗口；如果没有这行代码，外部窗口对象变化会污染目标身份。
        self.safety_boundary = safety_boundary  # 新增代码+Phase93UniversalLiveExecutionGate：保存安全边界；如果没有这行代码，动作前无法统一授权和风险检查。
        self.grant_store = grant_store  # 新增代码+Phase93UniversalLiveExecutionGate：保存授权 store；如果没有这行代码，动作器无法判断是否有用户授权。
        self.session_id = str(session_id)  # 新增代码+Phase93UniversalLiveExecutionGate：保存 session id；如果没有这行代码，授权匹配没有会话维度。
        self.control_runtime = control_runtime  # 新增代码+Phase93UniversalLiveExecutionGate：保存通用控件动作 runtime；如果没有这行代码，点击路径会绕过 Phase70。
        self.input_runtime = input_runtime  # 新增代码+Phase93UniversalLiveExecutionGate：保存通用输入 runtime；如果没有这行代码，滚动/拖拽等事件会绕过 Phase71。
        self.request_real_actions = bool(request_real_actions)  # 新增代码+Phase93UniversalLiveExecutionGate：保存是否请求真实动作；如果没有这行代码，默认安全模式无法和授权记录模式区分。
        self.action_reports: list[dict[str, Any]] = []  # 新增代码+Phase93UniversalLiveExecutionGate：保存动作报告；如果没有这行代码，合同无法统计记录型执行是否进入动作层。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，_Phase93ClosedLoopActor.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，act 在真实发送前强制走安全边界；如果没有这段函数，授权和目标检查无法挡住低层动作。
    def act(self, step: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase93UniversalLiveExecutionGate：定义动作方法；如果没有这行代码，闭环执行器无法进入 act 阶段。
        operation = str(step.get("operation", ""))  # 新增代码+Phase93UniversalLiveExecutionGate：读取当前操作名；如果没有这行代码，报告无法说明执行了哪一步。
        if not self.request_real_actions:  # 新增代码+Phase93UniversalLiveExecutionGate：默认不执行真实动作；如果没有这行代码，普通 prompt 可能误触本机。
            report = {"acted": False, "operation": operation, "decision": "real_actions_disabled_by_default", "low_level_event_count": 0, "recording_dispatch_only": True, "real_dispatch_allowed": False}  # 新增代码+Phase93UniversalLiveExecutionGate：构造默认阻断报告；如果没有这行代码，预览模式没有可审计结果。
            self.action_reports.append(report)  # 新增代码+Phase93UniversalLiveExecutionGate：保存默认阻断报告；如果没有这行代码，合同无法复盘预览路径。
            return report  # 新增代码+Phase93UniversalLiveExecutionGate：返回默认阻断结果；如果没有这行代码，预览模式会继续走授权动作。
        decision = self.safety_boundary.evaluate(self.window, "click", self.grant_store, self.session_id)  # 新增代码+Phase93UniversalLiveExecutionGate：在动作前评估安全边界；如果没有这行代码，授权和危险窗口拦截会被绕过。
        if not bool(decision.get("allowed")):  # 新增代码+Phase93UniversalLiveExecutionGate：检查安全边界是否放行；如果没有这行代码，拒绝结果也可能继续执行。
            report = {"acted": False, "operation": operation, "decision": str(decision.get("decision", "")), "safety_decision": decision, "low_level_event_count": _phase93_low_level_count(decision), "recording_dispatch_only": True, "real_dispatch_allowed": False}  # 新增代码+Phase93UniversalLiveExecutionGate：构造安全拒绝报告；如果没有这行代码，拒绝原因和零事件证据会丢失。
            self.action_reports.append(report)  # 新增代码+Phase93UniversalLiveExecutionGate：保存安全拒绝报告；如果没有这行代码，合同无法复盘拒绝路径。
            return report  # 新增代码+Phase93UniversalLiveExecutionGate：返回安全拒绝结果；如果没有这行代码，拒绝后仍会进入动作层。
        click = self.control_runtime.click_by_visual_point(self.window, {"x": 260, "y": 220}, "phase93 generic visual target")  # 新增代码+Phase93UniversalLiveExecutionGate：用 Phase70 记录型通用点击证明动作层接入；如果没有这行代码，授权后链路没有通用点击证据。
        scroll = self.input_runtime.scroll_at(self.window, 260, 220, -120)  # 新增代码+Phase93UniversalLiveExecutionGate：用 Phase71 记录型滚动证明输入层接入；如果没有这行代码，授权后链路没有通用输入证据。
        report = {"acted": True, "operation": operation, "decision": "authorized_recording_dispatch", "safety_decision": decision, "generic_control_result": click, "generic_input_result": scroll, "high_level_event_count": int(click.get("high_level_event_count", 0) or 0), "input_event_count": int(scroll.get("input_event_count", 0) or 0), "low_level_event_count": 0, "recording_dispatch_only": True, "real_dispatch_allowed": False, "observation_id": observation.get("observation_id", "")}  # 新增代码+Phase93UniversalLiveExecutionGate：构造授权记录型动作报告；如果没有这行代码，合同无法证明只记录不物理发送。
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
    def __init__(self, base_dir: str | Path | None = None, phase92_runtime: UniversalWindowsComputerUseRuntime | None = None, safety_boundary: WindowsRealAppSafetyBoundary | None = None, grant_store: WindowsComputerUsePersistentGrantStore | None = None, host_adapter: WindowsProductionComputerUseHostAdapter | None = None) -> None:  # 新增代码+Phase93UniversalLiveExecutionGate：定义初始化参数；如果没有这行代码，测试无法注入隔离目录和替身依赖。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_PHASE93_UNIVERSAL_LIVE_EXECUTION_ROOT / f"session-{int(time.time() * 1000)}"  # 新增代码+Phase93UniversalLiveExecutionGate：确定运行根目录；如果没有这行代码，多次运行会互相污染。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase93UniversalLiveExecutionGate：确保根目录存在；如果没有这行代码，报告落盘会失败。
        self.phase92_runtime = phase92_runtime or UniversalWindowsComputerUseRuntime(base_dir=self.base_dir / "phase92")  # 新增代码+Phase93UniversalLiveExecutionGate：创建或复用 Phase92 通用 runtime；如果没有这行代码，prompt mode 主线断开。
        self.safety_boundary = safety_boundary or WindowsRealAppSafetyBoundary()  # 新增代码+Phase93UniversalLiveExecutionGate：创建或复用安全边界；如果没有这行代码，真实执行前没有授权和危险窗口检查。
        self.grant_store = grant_store or WindowsComputerUsePersistentGrantStore(base_dir=self.base_dir / "grants")  # 新增代码+Phase93UniversalLiveExecutionGate：创建隔离授权 store；如果没有这行代码，授权事实源会污染全局。
        self.host_adapter = host_adapter or WindowsProductionComputerUseHostAdapter()  # 新增代码+Phase93UniversalLiveExecutionGate：创建生产 host adapter；如果没有这行代码，Phase93 缺少生产桥接状态。
        self.closed_loop_executor = WindowsClosedLoopComputerExecutor()  # 新增代码+Phase93UniversalLiveExecutionGate：创建闭环执行器；如果没有这行代码，observe-act-verify-recover 不能统一执行。
        self.high_level_tool = Phase70RecordingHighLevelTool()  # 新增代码+Phase93UniversalLiveExecutionGate：创建记录型高层工具；如果没有这行代码，默认合同可能误触真实桌面。
        self.input_sender = Phase71RecordingInputSender()  # 新增代码+Phase93UniversalLiveExecutionGate：创建记录型输入 sender；如果没有这行代码，输入事件没有安全记录出口。
        self.control_runtime = WindowsGenericControlActionRuntime(high_level_tool=self.high_level_tool)  # 新增代码+Phase93UniversalLiveExecutionGate：把 Phase70 接到记录型工具；如果没有这行代码，通用点击路径没有统一桥接。
        self.input_runtime = WindowsGenericInputActionRuntime(sender=self.input_sender)  # 新增代码+Phase93UniversalLiveExecutionGate：把 Phase71 接到记录型 sender；如果没有这行代码，通用输入路径没有统一桥接。
    # 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，UniversalWindowsLiveExecutionGate.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    # 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，status 返回 Phase93 组合状态；如果没有这段函数，CLI 和测试要重复拼装组件事实。
    def status(self) -> dict[str, Any]:  # 新增代码+Phase93UniversalLiveExecutionGate：定义状态方法；如果没有这行代码，外部无法低成本检查 runtime 架构。
        return {"marker": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER, "ok_token": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN, "model": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MODEL, "uses_phase92_universal_runtime": isinstance(self.phase92_runtime, UniversalWindowsComputerUseRuntime), "single_universal_live_loop": True, "prompt_to_observe_plan_act_verify": True, "no_per_app_controller": True, "representative_apps_are_acceptance_only": True, "uses_closed_loop_executor": isinstance(self.closed_loop_executor, WindowsClosedLoopComputerExecutor), "uses_generic_action_layer": isinstance(self.control_runtime, WindowsGenericControlActionRuntime) and isinstance(self.input_runtime, WindowsGenericInputActionRuntime), "uses_real_app_safety_boundary": isinstance(self.safety_boundary, WindowsRealAppSafetyBoundary), "uses_production_host_adapter": isinstance(self.host_adapter, WindowsProductionComputerUseHostAdapter), "requires_explicit_user_authorization": True, "real_actions_default_disabled": PHASE93_REAL_ACTIONS_DEFAULT_DISABLED, "uncontrolled_actions_expanded": PHASE93_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+Phase93UniversalLiveExecutionGate：返回固定合同状态；如果没有这行代码，验收 token 缺少统一事实源。
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
        if bool(request_real_actions):  # 新增代码+Phase93UniversalLiveExecutionGate：只有明确请求时才写入记录型授权；如果没有这行代码，默认预览也可能被授权。
            self._approve_recording_window(window, session_id)  # 新增代码+Phase93UniversalLiveExecutionGate：写入短期记录型授权；如果没有这行代码，授权正例不会通过安全边界。
        task_plan = {"steps": [{"operation": "observe_generic_target", "action_kind": "observe"}, {"operation": "click_generic_target", "action_kind": "write"}, {"operation": "verify_generic_target", "action_kind": "verify"}]}  # 新增代码+Phase93UniversalLiveExecutionGate：构造最小 observe-act-verify 计划；如果没有这行代码，闭环执行器没有可运行步骤。
        actor = _Phase93ClosedLoopActor(window, self.safety_boundary, self.grant_store, session_id, self.control_runtime, self.input_runtime, bool(request_real_actions))  # 新增代码+Phase93UniversalLiveExecutionGate：创建动作器并注入安全和通用动作层；如果没有这行代码，闭环无法执行授权检查。
        loop = self.closed_loop_executor.run(task_plan, _Phase93ClosedLoopObserver(window), actor, _Phase93ClosedLoopVerifier(), _Phase93ClosedLoopRecoverer())  # 新增代码+Phase93UniversalLiveExecutionGate：运行通用闭环；如果没有这行代码，Phase93 只是静态声明而不是执行结构。
        status = self.status()  # 新增代码+Phase93UniversalLiveExecutionGate：读取组合状态；如果没有这行代码，报告要重复拼装固定字段。
        authorized_recording_loop_ready = bool(request_real_actions and any(report.get("acted") and report.get("recording_dispatch_only") and int(report.get("high_level_event_count", 0) or 0) > 0 and int(report.get("input_event_count", 0) or 0) > 0 and _phase93_low_level_count(report) == 0 for report in actor.action_reports))  # 新增代码+Phase93UniversalLiveExecutionGate：判断授权记录型闭环是否就绪；如果没有这行代码，合同无法证明授权后进入动作层但不物理发送。
        report = {"ok": bool(phase92_report.get("ok") and loop.get("closed_loop_execution")), "marker": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER, "ok_token": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN, "model": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MODEL, "prompt_sha256_16": prompt_digest, "prompt_text_included": False, "prompt_length": len(prompt_text), "raw_prompt_hidden": True, "phase92_model": phase92_report.get("model", ""), "phase92_ok": bool(phase92_report.get("ok")), "phase92_prompt_digest": phase92_report.get("prompt_sha256_16", ""), "loop": loop, "loop_event_count": len(loop.get("events", []) or []), "real_actions_requested": bool(request_real_actions), "real_action_decision": "authorized_recording_only" if bool(request_real_actions) else "preview_only_default_disabled", "authorized_recording_loop_ready": authorized_recording_loop_ready, "recording_dispatch_only": True, "real_dispatch_performed": False, "uses_phase92_universal_runtime": bool(status["uses_phase92_universal_runtime"]), "single_universal_live_loop": bool(status["single_universal_live_loop"]), "prompt_to_observe_plan_act_verify": bool(status["prompt_to_observe_plan_act_verify"]), "no_per_app_controller": bool(status["no_per_app_controller"]), "representative_apps_are_acceptance_only": bool(status["representative_apps_are_acceptance_only"]), "uses_closed_loop_executor": bool(status["uses_closed_loop_executor"]), "uses_generic_action_layer": bool(status["uses_generic_action_layer"]), "uses_real_app_safety_boundary": bool(status["uses_real_app_safety_boundary"]), "uses_production_host_adapter": bool(status["uses_production_host_adapter"]), "requires_explicit_user_authorization": bool(status["requires_explicit_user_authorization"]), "real_actions_default_disabled": bool(status["real_actions_default_disabled"]), "uncontrolled_actions_expanded": bool(status["uncontrolled_actions_expanded"])}  # 新增代码+Phase93UniversalLiveExecutionGate：构造脱敏运行报告；如果没有这行代码，测试和 agent 工具拿不到统一结果。
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
    authorized = runtime.run_prompt("请打开 computer use，在授权后走一次记录型通用点击和滚动闭环。", request_real_actions=True)  # 新增代码+Phase93UniversalLiveExecutionGate：运行授权记录型 prompt；如果没有这行代码，授权后动作层接入没有证据。
    privacy = runtime.run_prompt("phase93-contract-secret prompt should never appear in reports", request_real_actions=False)  # 新增代码+Phase93UniversalLiveExecutionGate：运行隐私检查 prompt；如果没有这行代码，raw_prompt_hidden 可能只是口头声明。
    unauthorized = runtime.unauthorized_window_refusal()  # 新增代码+Phase93UniversalLiveExecutionGate：验证未授权窗口拒绝；如果没有这行代码，默认授权门禁没有证据。
    unsafe = runtime.unsafe_window_refusal()  # 新增代码+Phase93UniversalLiveExecutionGate：验证危险窗口拒绝；如果没有这行代码，高风险窗口拦截没有证据。
    drift = runtime.target_drift_refusal()  # 新增代码+Phase93UniversalLiveExecutionGate：验证目标漂移拒绝；如果没有这行代码，目标身份保护没有证据。
    status = runtime.status()  # 新增代码+Phase93UniversalLiveExecutionGate：读取 runtime 状态；如果没有这行代码，报告需要重复拼装固定字段。
    serialized_without_raw = json.dumps({"preview": preview, "authorized": authorized, "privacy": privacy}, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase93UniversalLiveExecutionGate：序列化报告子集做隐私扫描；如果没有这行代码，嵌套原文泄露难以发现。
    raw_prompt_hidden = "phase93-contract-secret" not in serialized_without_raw and "prompt should never appear" not in serialized_without_raw  # 新增代码+Phase93UniversalLiveExecutionGate：确认隐私 prompt 没进入报告；如果没有这行代码，隐私门禁无法自动判断。
    report_path = root / "reports" / "phase93_universal_live_execution_gate_report.json"  # 新增代码+Phase93UniversalLiveExecutionGate：定义报告路径；如果没有这行代码，验收证据没有稳定落点。
    passed = bool(preview.get("ok") and authorized.get("ok") and authorized.get("authorized_recording_loop_ready") and status.get("uses_phase92_universal_runtime") and status.get("single_universal_live_loop") and status.get("prompt_to_observe_plan_act_verify") and status.get("no_per_app_controller") and status.get("representative_apps_are_acceptance_only") and status.get("uses_closed_loop_executor") and status.get("uses_generic_action_layer") and status.get("uses_real_app_safety_boundary") and status.get("uses_production_host_adapter") and status.get("requires_explicit_user_authorization") and status.get("real_actions_default_disabled") and unauthorized.get("unauthorized_window_zero_events") and unsafe.get("unsafe_window_zero_events") and drift.get("target_drift_zero_events") and raw_prompt_hidden and not status.get("uncontrolled_actions_expanded"))  # 新增代码+Phase93UniversalLiveExecutionGate：汇总合同通过条件；如果没有这行代码，main 无法用退出码表达成败。
    report = {"marker": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER, "ok_token": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN, "model": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MODEL, "passed": passed, "uses_phase92_universal_runtime": bool(status["uses_phase92_universal_runtime"]), "single_universal_live_loop": bool(status["single_universal_live_loop"]), "prompt_to_observe_plan_act_verify": bool(status["prompt_to_observe_plan_act_verify"]), "no_per_app_controller": bool(status["no_per_app_controller"]), "representative_apps_are_acceptance_only": bool(status["representative_apps_are_acceptance_only"]), "uses_closed_loop_executor": bool(status["uses_closed_loop_executor"]), "uses_generic_action_layer": bool(status["uses_generic_action_layer"]), "uses_real_app_safety_boundary": bool(status["uses_real_app_safety_boundary"]), "uses_production_host_adapter": bool(status["uses_production_host_adapter"]), "requires_explicit_user_authorization": bool(status["requires_explicit_user_authorization"]), "real_actions_default_disabled": bool(status["real_actions_default_disabled"]), "authorized_recording_loop_ready": bool(authorized.get("authorized_recording_loop_ready")), "unauthorized_window_zero_events": bool(unauthorized.get("unauthorized_window_zero_events")), "unsafe_window_zero_events": bool(unsafe.get("unsafe_window_zero_events")), "target_drift_zero_events": bool(drift.get("target_drift_zero_events")), "raw_prompt_hidden": raw_prompt_hidden, "uncontrolled_actions_expanded": bool(status["uncontrolled_actions_expanded"]), "report_path": str(report_path), "preview_report": preview, "authorized_report": authorized, "unauthorized_report": unauthorized, "unsafe_report": unsafe, "target_drift_report": drift}  # 新增代码+Phase93UniversalLiveExecutionGate：构造完整合同报告；如果没有这行代码，测试和人工验收拿不到统一证据。
    atomic_write_json(report_path, report)  # 新增代码+Phase93UniversalLiveExecutionGate：原子写入报告；如果没有这行代码，异常中断时可能留下半个 JSON。
    return report  # 新增代码+Phase93UniversalLiveExecutionGate：返回报告给测试和 CLI；如果没有这行代码，调用方拿不到验收结果。
# 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，run_phase93_universal_live_execution_gate_contract 到此结束；如果没有这个边界说明，初学者不容易看出总合同范围。


# 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，phase93_cli_line 输出固定 token 行；如果没有这段函数，真实终端验收需要解析复杂 JSON。
def phase93_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase93UniversalLiveExecutionGate：定义 CLI 格式化函数；如果没有这行代码，场景配置无法用简单 token 匹配。
    return f"{PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER} {PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN} uses_phase92_universal_runtime={_phase93_bool_token(report.get('uses_phase92_universal_runtime'))} single_universal_live_loop={_phase93_bool_token(report.get('single_universal_live_loop'))} prompt_to_observe_plan_act_verify={_phase93_bool_token(report.get('prompt_to_observe_plan_act_verify'))} no_per_app_controller={_phase93_bool_token(report.get('no_per_app_controller'))} representative_apps_are_acceptance_only={_phase93_bool_token(report.get('representative_apps_are_acceptance_only'))} uses_closed_loop_executor={_phase93_bool_token(report.get('uses_closed_loop_executor'))} uses_generic_action_layer={_phase93_bool_token(report.get('uses_generic_action_layer'))} uses_real_app_safety_boundary={_phase93_bool_token(report.get('uses_real_app_safety_boundary'))} uses_production_host_adapter={_phase93_bool_token(report.get('uses_production_host_adapter'))} requires_explicit_user_authorization={_phase93_bool_token(report.get('requires_explicit_user_authorization'))} real_actions_default_disabled={_phase93_bool_token(report.get('real_actions_default_disabled'))} authorized_recording_loop_ready={_phase93_bool_token(report.get('authorized_recording_loop_ready'))} unauthorized_window_zero_events={_phase93_bool_token(report.get('unauthorized_window_zero_events'))} unsafe_window_zero_events={_phase93_bool_token(report.get('unsafe_window_zero_events'))} target_drift_zero_events={_phase93_bool_token(report.get('target_drift_zero_events'))} raw_prompt_hidden={_phase93_bool_token(report.get('raw_prompt_hidden'))} uncontrolled_actions_expanded={_phase93_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase93UniversalLiveExecutionGate：返回固定顺序 token 行；如果没有这行代码，验收脚本很容易因为字段顺序漂移失败。
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


__all__ = ["DEFAULT_PHASE93_UNIVERSAL_LIVE_EXECUTION_ROOT", "PHASE93_REAL_ACTIONS_DEFAULT_DISABLED", "PHASE93_UNCONTROLLED_ACTIONS_EXPANDED", "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER", "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MODEL", "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN", "UniversalWindowsLiveExecutionGate", "main", "phase93_cli_line", "run_phase93_universal_live_execution_gate_contract"]  # 新增代码+Phase93UniversalLiveExecutionGate：限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase93UniversalLiveExecutionGate：允许直接运行本模块；如果没有这行代码，初学者无法用 python 文件方式手动执行 Phase93 自检。
    raise SystemExit(main())  # 新增代码+Phase93UniversalLiveExecutionGate：调用 main 并传递退出码；如果没有这行代码，直接运行文件不会执行验收。
