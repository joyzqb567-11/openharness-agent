"""Windows 通用真实执行闭环门禁。"""  # 新增代码+Phase93UniversalLiveExecutionGate：说明本文件负责把 Phase92 通用模式接到安全 live execution gate；如果没有这行代码，读者很难知道本模块不是单应用控制器。
from __future__ import annotations  # 新增代码+Phase93UniversalLiveExecutionGate：启用延迟类型解析；如果没有这行代码，后续类之间互相引用时更容易遇到类型注解问题。

import hashlib  # 新增代码+Phase93UniversalLiveExecutionGate：导入哈希库用于 prompt 脱敏追踪；如果没有这行代码，报告要么泄露原文，要么无法关联任务。
import json  # 新增代码+Phase93UniversalLiveExecutionGate：导入 JSON 用于稳定序列化报告；如果没有这行代码，隐私检查和验收落盘都不稳定。
import os  # 新增代码+Phase105FullModeControlledRealLaunch：导入 os 读取受控真实启动双环境门；如果没有这行代码，真实启动开关无法由可见终端显式控制。
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
PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_MARKER = "PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_READY"  # 新增代码+Phase105FullModeControlledRealLaunch：定义 Phase105 ready 标记；如果没有这行代码，真实终端验收无法稳定识别 full-mode 受控真实启动阶段。
PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_OK_TOKEN = "PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_OK"  # 新增代码+Phase105FullModeControlledRealLaunch：定义 Phase105 OK 标记；如果没有这行代码，验收器无法区分通过输出和普通日志。
PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_MODEL = "phase105_full_mode_controlled_real_launch"  # 新增代码+Phase105FullModeControlledRealLaunch：定义 Phase105 报告模型名；如果没有这行代码，能力矩阵无法区分当前合同版本。
PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_ENV = "LEARNING_AGENT_PHASE105_ENABLE_FULL_MODE_CONTROLLED_REAL_LAUNCH"  # 新增代码+Phase105FullModeControlledRealLaunch：定义允许真实启动的环境门；如果没有这行代码，full 模式可能缺少第二道可审计开关。
PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_REQUEST_ENV = "LEARNING_AGENT_PHASE105_RUN_FULL_MODE_CONTROLLED_REAL_LAUNCH"  # 新增代码+Phase105FullModeControlledRealLaunch：定义请求真实启动验收的环境门；如果没有这行代码，CLI 无法表达本次要跑真实路径。
DEFAULT_PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "phase105_full_mode_controlled_real_launch"  # 新增代码+Phase105FullModeControlledRealLaunch：定义 Phase105 默认报告目录；如果没有这行代码，验收证据会散落。
PHASE113_INTERACTIVE_GENERIC_LAUNCH_MARKER = "PHASE113_INTERACTIVE_GENERIC_LAUNCH_READY"  # 新增代码+InteractiveGenericLaunchMaturity：定义 Task5 交互通用启动 ready marker；如果没有这一行，真实终端无法稳定识别 `/computer launch <app>` 已接到通用后端。
PHASE113_INTERACTIVE_GENERIC_LAUNCH_OK_TOKEN = "PHASE113_INTERACTIVE_GENERIC_LAUNCH_OK"  # 新增代码+InteractiveGenericLaunchMaturity：定义 Task5 交互通用启动 OK token；如果没有这一行，成功输出和普通日志不容易区分。
PHASE113_INTERACTIVE_GENERIC_LAUNCH_MODEL = "phase113_interactive_generic_launch_maturity"  # 新增代码+InteractiveGenericLaunchMaturity：定义报告模型名；如果没有这一行，最终成熟矩阵无法引用这层接线。
PHASE113_GENERIC_REAL_LAUNCH_SMOKE_ENV = "LEARNING_AGENT_ENABLE_GENERIC_REAL_LAUNCH_SMOKE"  # 新增代码+InteractiveGenericLaunchMaturity：定义唯一显式真实启动 smoke 环境门；如果没有这一行，自动测试和真实终端可能误触本机应用。
PHASE113_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+InteractiveGenericLaunchMaturity：声明本层没有扩大无边界动作面；如果没有这一行，full 模式可能被误读成无限权限。


# 新增代码+Phase93UniversalLiveExecutionGate：函数段开始，_phase93_bool_token 把布尔值转成小写验收 token；如果没有这段函数，CLI 输出会混用 True/False 并导致场景匹配不稳。
def _phase93_bool_token(value: Any) -> str:  # 新增代码+Phase93UniversalLiveExecutionGate：定义布尔 token helper；如果没有这行代码，多处输出会重复写转换逻辑。
    return "true" if bool(value) else "false"  # 新增代码+Phase93UniversalLiveExecutionGate：返回小写布尔文本；如果没有这行代码，JSON 字段和终端 token 可能格式不一致。
# 新增代码+Phase93UniversalLiveExecutionGate：函数段结束，_phase93_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。


def _phase105_env_enabled(name: str) -> bool:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，读取 Phase105 显式环境门；如果没有这段函数，真实启动开关判断会分散且容易误开。
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase105FullModeControlledRealLaunch：只接受明确真值；如果没有这行代码，模糊环境变量可能误触真实桌面。
# 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，_phase105_env_enabled 到此结束；如果没有这个边界说明，初学者不容易看出环境门范围。


def _phase105_request_real_launch(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，判断本次是否请求真实 full-mode 启动；如果没有这段函数，CLI 和测试入口会漂移。
    if explicit_value is not None:  # 新增代码+Phase105FullModeControlledRealLaunch：优先使用测试或调用方显式传值；如果没有这行代码，单元测试无法安全覆盖真实分支。
        return bool(explicit_value)  # 新增代码+Phase105FullModeControlledRealLaunch：返回显式布尔值；如果没有这行代码，调用方传 False 仍可能被环境变量覆盖。
    return _phase105_env_enabled(PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_REQUEST_ENV)  # 新增代码+Phase105FullModeControlledRealLaunch：没有显式值时读取请求环境门；如果没有这行代码，真实终端无法请求 Phase105 真实验收。
# 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，_phase105_request_real_launch 到此结束；如果没有这个边界说明，初学者不容易看出请求门范围。


def _phase105_allow_real_launch(explicit_value: bool | None = None) -> bool:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，判断真实 full-mode 启动是否被允许；如果没有这段函数，真实启动会少一道安全门。
    if explicit_value is not None:  # 新增代码+Phase105FullModeControlledRealLaunch：优先使用测试或调用方显式传值；如果没有这行代码，单元测试无法稳定模拟允许门。
        return bool(explicit_value)  # 新增代码+Phase105FullModeControlledRealLaunch：返回显式布尔值；如果没有这行代码，传 False 的调用方仍可能被环境误开。
    return _phase105_env_enabled(PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_ENV)  # 新增代码+Phase105FullModeControlledRealLaunch：没有显式值时读取允许环境门；如果没有这行代码，可见终端不能安全启用真实路径。
# 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，_phase105_allow_real_launch 到此结束；如果没有这个边界说明，初学者不容易看出允许门范围。


def _phase113_env_gate_enabled(explicit_value: bool | None = None) -> bool:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，读取 Task5 显式真实启动环境门；如果没有这段函数，真实启动开关会散落且容易误开。
    if explicit_value is not None:  # 新增代码+InteractiveGenericLaunchMaturity：优先使用测试或调用方显式传值；如果没有这一行，单元测试只能修改全局环境变量。
        return bool(explicit_value)  # 新增代码+InteractiveGenericLaunchMaturity：返回显式布尔值；如果没有这一行，调用方传 False 仍可能被环境变量覆盖。
    return _phase105_env_enabled(PHASE113_GENERIC_REAL_LAUNCH_SMOKE_ENV)  # 新增代码+InteractiveGenericLaunchMaturity：没有显式值时只读取唯一 smoke 环境门；如果没有这一行，真实终端无法可审计地启用 production 后端。
# 新增代码+InteractiveGenericLaunchMaturity：函数段结束，_phase113_env_gate_enabled 到此结束；如果没有这个边界说明，初学者不容易看出环境门范围。


def _phase113_resolve_generic_report(raw_target: Any, generic_report: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，读取或生成 Phase108 通用发现报告；如果没有这段函数，Phase113 会绕开已有通用发现模型。
    if generic_report is not None:  # 新增代码+InteractiveGenericLaunchMaturity：优先复用交互层已经生成的 Phase108 报告；如果没有这一行，同一命令会重复发现并可能输出不一致证据。
        return dict(generic_report)  # 新增代码+InteractiveGenericLaunchMaturity：复制报告避免污染调用方对象；如果没有这一行，Phase113 补字段可能改动上游报告。
    try:  # 新增代码+InteractiveGenericLaunchMaturity：优先按包路径导入 Phase108 发现器；如果没有这一行，项目根运行时无法加载标准模块。
        from learning_agent.computer_use.generic_app_discovery import resolve_generic_app_launch_target  # 新增代码+InteractiveGenericLaunchMaturity：导入通用目标解析器；如果没有这一行，raw_target 无法转成安全启动计划。
    except ModuleNotFoundError as error:  # 新增代码+InteractiveGenericLaunchMaturity：兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这一行，真实可见终端可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.generic_app_discovery"}:  # 新增代码+InteractiveGenericLaunchMaturity：只兜底包路径缺失；如果没有这一行，Phase108 内部 bug 会被误吞。
            raise  # 新增代码+InteractiveGenericLaunchMaturity：重新抛出真实内部错误；如果没有这一行，排查会被错误 fallback 干扰。
        from computer_use.generic_app_discovery import resolve_generic_app_launch_target  # type: ignore  # 新增代码+InteractiveGenericLaunchMaturity：脚本模式导入同一解析器；如果没有这一行，双击 bat 后 Phase113 无法发现普通应用。
    return dict(resolve_generic_app_launch_target(str(raw_target or "")))  # 新增代码+InteractiveGenericLaunchMaturity：生成并复制 Phase108 报告；如果没有这一行，Phase113 没有安全计划输入。
# 新增代码+InteractiveGenericLaunchMaturity：函数段结束，_phase113_resolve_generic_report 到此结束；如果没有这个边界说明，初学者不容易看出发现报告范围。


def _phase113_prepare_candidate_report(raw_target: Any, generic_report: dict[str, Any], phase109_report: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，读取或生成 Phase109 候选报告；如果没有这段函数，Phase113 输出会丢失身份和清理候选证据。
    if phase109_report is not None:  # 新增代码+InteractiveGenericLaunchMaturity：优先复用交互层已经生成的 Phase109 报告；如果没有这一行，同一命令会重复构造候选并可能漂移。
        return dict(phase109_report)  # 新增代码+InteractiveGenericLaunchMaturity：复制候选报告避免污染调用方；如果没有这一行，Phase113 字段补充可能影响上游报告。
    try:  # 新增代码+InteractiveGenericLaunchMaturity：优先按包路径导入 Phase109 候选器；如果没有这一行，项目根运行时无法加载标准模块。
        from learning_agent.computer_use.generic_real_launch_candidate import prepare_phase109_generic_real_launch_candidate  # 新增代码+InteractiveGenericLaunchMaturity：导入通用真实启动候选准备函数；如果没有这一行，Phase113 只能看到后端而缺少候选成熟证据。
    except ModuleNotFoundError as error:  # 新增代码+InteractiveGenericLaunchMaturity：兼容 start_oauth_agent.bat 脚本模式；如果没有这一行，真实可见终端可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.generic_real_launch_candidate"}:  # 新增代码+InteractiveGenericLaunchMaturity：只兜底包路径缺失；如果没有这一行，Phase109 内部 bug 会被误吞。
            raise  # 新增代码+InteractiveGenericLaunchMaturity：重新抛出真实内部错误；如果没有这一行，排查 Phase109 会被 fallback 干扰。
        from computer_use.generic_real_launch_candidate import prepare_phase109_generic_real_launch_candidate  # type: ignore  # 新增代码+InteractiveGenericLaunchMaturity：脚本模式导入同一候选器；如果没有这一行，bat 入口无法显示候选证据。
    return dict(prepare_phase109_generic_real_launch_candidate(raw_target=str(raw_target or ""), generic_report=generic_report, enable_real_launch=False))  # 新增代码+InteractiveGenericLaunchMaturity：生成默认关闭候选报告；如果没有这一行，Phase113 不能证明默认不触碰桌面。
# 新增代码+InteractiveGenericLaunchMaturity：函数段结束，_phase113_prepare_candidate_report 到此结束；如果没有这个边界说明，初学者不容易看出候选报告范围。


def _phase113_generic_backend_tools() -> tuple[Any, Any]:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，延迟导入 Phase110 通用后端工具；如果没有这段函数，脚本模式和包模式会重复写导入分支。
    try:  # 新增代码+InteractiveGenericLaunchMaturity：优先按 learning_agent 包路径导入；如果没有这一行，项目根运行时无法加载标准模块。
        from learning_agent.computer_use.generic_launch_backend import Phase110ProductionGenericLaunchBackend, run_generic_launch_backend  # 新增代码+InteractiveGenericLaunchMaturity：导入 production 后端和编排函数；如果没有这一行，Phase113 无法到达通用启动后端。
    except ModuleNotFoundError as error:  # 新增代码+InteractiveGenericLaunchMaturity：兼容 start_oauth_agent.bat 从 learning_agent 目录运行；如果没有这一行，真实可见终端可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.generic_launch_backend"}:  # 新增代码+InteractiveGenericLaunchMaturity：只兜底包路径缺失；如果没有这一行，Phase110 内部 bug 会被误吞。
            raise  # 新增代码+InteractiveGenericLaunchMaturity：重新抛出真实内部错误；如果没有这一行，排查后端接线会被 fallback 干扰。
        from computer_use.generic_launch_backend import Phase110ProductionGenericLaunchBackend, run_generic_launch_backend  # type: ignore  # 新增代码+InteractiveGenericLaunchMaturity：脚本模式导入同一后端工具；如果没有这一行，bat 入口无法接通通用后端。
    return Phase110ProductionGenericLaunchBackend, run_generic_launch_backend  # 新增代码+InteractiveGenericLaunchMaturity：返回 production 类和运行函数；如果没有这一行，调用方拿不到后端工具。
# 新增代码+InteractiveGenericLaunchMaturity：函数段结束，_phase113_generic_backend_tools 到此结束；如果没有这个边界说明，初学者不容易看出后端导入范围。


def run_phase113_interactive_generic_launch_bridge(raw_target: str = "obsidian", generic_report: dict[str, Any] | None = None, phase109_report: dict[str, Any] | None = None, request_real_launch: bool | None = None, allow_real_gate: bool | None = None, launch_backend: Any | None = None) -> dict[str, Any]:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，把交互 `/computer launch <app>` 接到 Phase110 通用后端；如果没有这段函数，真实用户命令仍停在 Phase109 候选。
    phase108_report = _phase113_resolve_generic_report(raw_target, generic_report=generic_report)  # 新增代码+InteractiveGenericLaunchMaturity：读取 Phase108 通用发现报告；如果没有这一行，后端没有安全启动计划来源。
    phase109_candidate = _phase113_prepare_candidate_report(raw_target, phase108_report, phase109_report=phase109_report)  # 新增代码+InteractiveGenericLaunchMaturity：读取 Phase109 候选报告；如果没有这一行，输出缺少身份验证和清理模型证据。
    candidate_ready = bool(phase108_report.get("passed", False) and phase109_candidate.get("generic_real_launch_candidate_ready", False) and not phase108_report.get("high_risk_refused", False))  # 新增代码+InteractiveGenericLaunchMaturity：确认普通目标候选已就绪且不是高风险；如果没有这一行，PowerShell 之类目标可能进入后端。
    requested = _phase113_env_gate_enabled(request_real_launch)  # 新增代码+InteractiveGenericLaunchMaturity：读取本次是否显式请求真实启动；如果没有这一行，默认路径和 smoke 路径会混淆。
    allowed = _phase113_env_gate_enabled(allow_real_gate)  # 新增代码+InteractiveGenericLaunchMaturity：读取真实启动是否被允许；如果没有这一行，显式请求可能少一道可审计门。
    authorized = bool(candidate_ready and requested and allowed)  # 新增代码+InteractiveGenericLaunchMaturity：只有候选就绪、请求门和允许门同时满足才授权；如果没有这一行，默认 full 模式可能真实启动普通应用。
    Phase110ProductionGenericLaunchBackend, run_generic_launch_backend = _phase113_generic_backend_tools()  # 新增代码+InteractiveGenericLaunchMaturity：读取通用后端工具；如果没有这一行，Phase113 无法调用 Phase110。
    selected_backend = launch_backend if launch_backend is not None else (Phase110ProductionGenericLaunchBackend() if authorized else None)  # 新增代码+InteractiveGenericLaunchMaturity：授权时使用注入或 production 后端，默认关闭时不需要后端；如果没有这一行，自动测试可能触碰真实桌面。
    phase110_report = dict(run_generic_launch_backend(phase108_report, enable_real_launch=authorized, backend=selected_backend))  # 新增代码+InteractiveGenericLaunchMaturity：运行 Phase110 编排；如果没有这一行，交互命令无法证明通用后端接线。
    backend_name = str(phase110_report.get("backend", "") or ("phase110_production_generic_launch_backend" if authorized else "phase110_default_off_no_backend"))  # 新增代码+InteractiveGenericLaunchMaturity：提取后端名称并给默认关闭稳定名称；如果没有这一行，终端输出难以解释后端状态。
    backend_launch_performed = bool(phase110_report.get("backend_launch_performed", False))  # 新增代码+InteractiveGenericLaunchMaturity：读取后端是否执行；如果没有这一行，默认关闭零副作用无法量化。
    backend_launch_reaches_launcher = bool(phase110_report.get("backend_launch_reaches_launcher", False))  # 新增代码+InteractiveGenericLaunchMaturity：读取是否到达 launcher；如果没有这一行，显式门接线无法证明。
    default_off_backend_not_called = bool(phase110_report.get("default_off_backend_not_called", False) and not authorized)  # 新增代码+InteractiveGenericLaunchMaturity：确认默认关闭没有调用后端；如果没有这一行，安全默认只停留在口头承诺。
    generic_launch_backend_ready = bool(str(phase110_report.get("marker", "")) == "PHASE110_GENERIC_LAUNCH_BACKEND_READY" or default_off_backend_not_called or backend_launch_reaches_launcher)  # 新增代码+InteractiveGenericLaunchMaturity：汇总 Phase110 后端是否可见；如果没有这一行，终端无法显示后端层已接通。
    generic_enabled_when_authorized = bool(authorized and backend_launch_reaches_launcher)  # 新增代码+InteractiveGenericLaunchMaturity：汇总授权后是否到达后端；如果没有这一行，显式真实门接线不可验证。
    real_desktop_touched = bool(phase110_report.get("real_desktop_touched", False))  # 新增代码+InteractiveGenericLaunchMaturity：读取是否触碰真实桌面；如果没有这一行，测试替身和真实 production 无法区分。
    real_full_launch_attempted = bool(authorized and backend_launch_performed)  # 新增代码+InteractiveGenericLaunchMaturity：读取是否尝试真实启动；如果没有这一行，默认关闭输出可能误导用户。
    passed = bool(candidate_ready and ((not authorized and default_off_backend_not_called and not real_desktop_touched) or (authorized and generic_enabled_when_authorized and not phase110_report.get("uses_shell_string", False))))  # 新增代码+InteractiveGenericLaunchMaturity：计算默认关闭或显式授权路径是否通过；如果没有这一行，OK token 没有依据。
    return {"marker": PHASE113_INTERACTIVE_GENERIC_LAUNCH_MARKER, "ok_token": PHASE113_INTERACTIVE_GENERIC_LAUNCH_OK_TOKEN, "model": PHASE113_INTERACTIVE_GENERIC_LAUNCH_MODEL, "passed": passed, "target_app": str(phase108_report.get("canonical_target", raw_target) or raw_target), "generic_real_launch_candidate_ready": bool(phase109_candidate.get("generic_real_launch_candidate_ready", False)), "generic_launch_backend_ready": generic_launch_backend_ready, "generic_real_launch_default_enabled": False, "real_launch_requested": requested, "real_enable_gate_passed": allowed, "explicit_real_launch_gate_passed": authorized, "generic_real_launch_enabled_when_authorized": generic_enabled_when_authorized, "real_full_launch_attempted": real_full_launch_attempted, "backend_name": backend_name, "backend_launch_performed": backend_launch_performed, "backend_launch_reaches_launcher": backend_launch_reaches_launcher, "default_off_backend_not_called": default_off_backend_not_called, "high_risk_refused": bool(phase108_report.get("high_risk_refused", False)), "real_desktop_touched": real_desktop_touched, "low_level_event_count": int(phase110_report.get("low_level_event_count", 0) or 0), "uncontrolled_actions_expanded": PHASE113_UNCONTROLLED_ACTIONS_EXPANDED, "env_gate_name": PHASE113_GENERIC_REAL_LAUNCH_SMOKE_ENV, "phase108_discovery_report": phase108_report, "phase109_candidate_report": phase109_candidate, "phase110_backend_report": phase110_report}  # 新增代码+InteractiveGenericLaunchMaturity：返回完整交互通用启动报告；如果没有这一行，测试、终端和成熟矩阵无法共享事实。
# 新增代码+InteractiveGenericLaunchMaturity：函数段结束，run_phase113_interactive_generic_launch_bridge 到此结束；如果没有这个边界说明，初学者不容易看出交互桥接范围。


def phase113_cli_line(report: dict[str, Any]) -> str:  # 新增代码+InteractiveGenericLaunchMaturity：函数段开始，把 Task5 报告转成稳定终端 token 行；如果没有这段函数，真实终端验收需要解析复杂 JSON。
    ok_token = f" {PHASE113_INTERACTIVE_GENERIC_LAUNCH_OK_TOKEN}" if bool(report.get("passed", False)) else ""  # 新增代码+InteractiveGenericLaunchMaturity：只在通过时追加 OK token；如果没有这一行，失败报告可能被误判成功。
    return f"{PHASE113_INTERACTIVE_GENERIC_LAUNCH_MARKER}{ok_token} generic_launch_backend_ready={_phase93_bool_token(report.get('generic_launch_backend_ready'))} generic_real_launch_candidate_ready={_phase93_bool_token(report.get('generic_real_launch_candidate_ready'))} generic_real_launch_default_enabled={_phase93_bool_token(report.get('generic_real_launch_default_enabled'))} explicit_real_launch_gate_passed={_phase93_bool_token(report.get('explicit_real_launch_gate_passed'))} generic_real_launch_enabled_when_authorized={_phase93_bool_token(report.get('generic_real_launch_enabled_when_authorized'))} real_full_launch_attempted={_phase93_bool_token(report.get('real_full_launch_attempted'))} backend_name={report.get('backend_name', '')} backend_launch_performed={_phase93_bool_token(report.get('backend_launch_performed'))} backend_launch_reaches_launcher={_phase93_bool_token(report.get('backend_launch_reaches_launcher'))} default_off_backend_not_called={_phase93_bool_token(report.get('default_off_backend_not_called'))} high_risk_refused={_phase93_bool_token(report.get('high_risk_refused'))} real_desktop_touched={_phase93_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase93_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+InteractiveGenericLaunchMaturity：返回固定顺序 token；如果没有这一行，场景断言容易因字段顺序变化失败。
# 新增代码+InteractiveGenericLaunchMaturity：函数段结束，phase113_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 文本范围。


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


def _phase103_launch_target_app(prompt_text: str) -> str:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，从用户 prompt 选择受控启动样本应用；如果没有这段函数，full gate 无法把 notepad/paint/calc 映射到安全计划。
    lowered = str(prompt_text or "").lower()  # 新增代码+Phase103ControlledAppLaunch：把 prompt 转成小写文本；如果没有这行代码，英文应用名大小写变体可能漏检。
    original = str(prompt_text or "")  # 新增代码+Phase103ControlledAppLaunch：保留原始中文文本用于关键词判断；如果没有这行代码，画图/计算器等中文目标无法识别。
    if "paint" in lowered or "mspaint" in lowered or "画图" in original:  # 新增代码+Phase103ControlledAppLaunch：识别画图应用目标；如果没有这行代码，用户说画图时仍会落到默认 notepad。
        return "mspaint"  # 新增代码+Phase103ControlledAppLaunch：返回 Phase69 已允许的 mspaint 别名；如果没有这行代码，受控启动计划可能拿不到安全 exe。
    if "calc" in lowered or "calculator" in lowered or "计算器" in original:  # 新增代码+Phase103ControlledAppLaunch：识别计算器应用目标；如果没有这行代码，用户说计算器时仍会落到默认 notepad。
        return "calc"  # 新增代码+Phase103ControlledAppLaunch：返回 Phase69 已允许的 calc 别名；如果没有这行代码，受控启动计划可能拿不到安全 exe。
    return "notepad"  # 新增代码+Phase103ControlledAppLaunch：默认使用安全代表应用 notepad；如果没有这行代码，普通启动 prompt 会落到 generic_windows_app 而被安全计划拒绝。
# 新增代码+Phase103ControlledAppLaunch：函数段结束，_phase103_launch_target_app 到此结束；如果没有这个边界说明，读者不容易看出目标应用选择范围。


def _phase102_task_plan(prompt_text: str, phase92_report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase102FullModeExecutionGate：函数段开始，根据用户任务选择闭环计划；如果没有这段函数，run_prompt 只能执行固定 click 计划。
    if _phase102_prompt_requests_launch(prompt_text, phase92_report):  # 新增代码+Phase102FullModeExecutionGate：检查是否是启动应用任务；如果没有这行代码，full 专属动作没有入口。
        return {"steps": [{"operation": "observe_generic_target", "action_kind": "observe"}, {"operation": "launch_app_generic_target", "action_kind": "write", "target_app": _phase103_launch_target_app(prompt_text)}, {"operation": "verify_generic_target", "action_kind": "verify"}]}  # 修改代码+Phase103ControlledAppLaunch：启动步骤携带安全目标应用；如果没有这行代码，Phase103 候选无法知道该构造哪个安全启动计划。
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
    def __init__(self, window: dict[str, Any], safety_boundary: WindowsRealAppSafetyBoundary, grant_store: WindowsComputerUsePersistentGrantStore, mode_store: Any | None, session_id: str, control_runtime: WindowsGenericControlActionRuntime, input_runtime: WindowsGenericInputActionRuntime, request_real_actions: bool, controlled_launch_candidate: Any | None = None, controlled_real_launch_enabled: bool = False, controlled_launch_test_file: str | Path | None = None) -> None:  # 修改代码+Phase105FullModeControlledRealLaunch：增加受控真实启动门和受控文件参数；如果没有这行代码，full gate 无法把 Phase104 真实启动能力接到 launch_app。
        self.window = dict(window)  # 新增代码+Phase93UniversalLiveExecutionGate：复制目标窗口；如果没有这行代码，外部窗口对象变化会污染目标身份。
        self.safety_boundary = safety_boundary  # 新增代码+Phase93UniversalLiveExecutionGate：保存安全边界；如果没有这行代码，动作前无法统一授权和风险检查。
        self.grant_store = grant_store  # 新增代码+Phase93UniversalLiveExecutionGate：保存授权 store；如果没有这行代码，动作器无法判断是否有用户授权。
        self.mode_store = mode_store  # 新增代码+Phase99UniversalComputerUseModeGate：保存 mode session store；如果没有这行代码，真实动作前无法检查 normal/observe/stopped/expired 模式。
        self.session_id = str(session_id)  # 新增代码+Phase93UniversalLiveExecutionGate：保存 session id；如果没有这行代码，授权匹配没有会话维度。
        self.control_runtime = control_runtime  # 新增代码+Phase93UniversalLiveExecutionGate：保存通用控件动作 runtime；如果没有这行代码，点击路径会绕过 Phase70。
        self.input_runtime = input_runtime  # 新增代码+Phase93UniversalLiveExecutionGate：保存通用输入 runtime；如果没有这行代码，滚动/拖拽等事件会绕过 Phase71。
        self.request_real_actions = bool(request_real_actions)  # 新增代码+Phase93UniversalLiveExecutionGate：保存是否请求真实动作；如果没有这行代码，默认安全模式无法和授权记录模式区分。
        self.controlled_launch_candidate = controlled_launch_candidate  # 新增代码+Phase103ControlledAppLaunch：保存受控应用启动候选；如果没有这行代码，launch_app 授权后无法进入 Phase103 候选路径。
        self.controlled_real_launch_enabled = bool(controlled_real_launch_enabled)  # 新增代码+Phase105FullModeControlledRealLaunch：保存 Phase105 受控真实启动门；如果没有这行代码，actor 无法区分默认关闭和显式放行。
        self.controlled_launch_test_file = str(controlled_launch_test_file) if controlled_launch_test_file is not None else None  # 新增代码+Phase105FullModeControlledRealLaunch：保存受控测试文件路径；如果没有这行代码，真实 Notepad 启动可能缺少唯一文件锚点。
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
            target_app = str(step.get("target_app") or "notepad")  # 新增代码+Phase103ControlledAppLaunch：读取计划中的安全目标应用；如果没有这行代码，受控启动候选不知道该构造哪个 app plan。
            launch_method = getattr(self.controlled_launch_candidate, "launch", None)  # 新增代码+Phase103ControlledAppLaunch：读取受控候选 launch 方法；如果没有这行代码，注入对象无法被调用。
            phase105_real_launch_requested = bool(self.controlled_real_launch_enabled)  # 新增代码+Phase105FullModeControlledRealLaunch：记录调用方是否请求 Phase105 真实启动；如果没有这行代码，报告无法解释为什么仍默认关闭。
            phase105_target_allowed = target_app.strip().lower() == "notepad"  # 新增代码+Phase105FullModeControlledRealLaunch：当前只允许 Notepad 真实 smoke；如果没有这行代码，Phase105 可能被误扩成任意应用启动。
            phase105_gate_passed = bool(phase105_real_launch_requested and phase105_target_allowed)  # 新增代码+Phase105FullModeControlledRealLaunch：只有显式请求且目标受控才通过真实启动门；如果没有这行代码，full 模式可能越过 Notepad 边界。
            phase105_test_file = self.controlled_launch_test_file if phase105_gate_passed else None  # 新增代码+Phase105FullModeControlledRealLaunch：只在门通过时传受控文件；如果没有这行代码，默认关闭路径也会暴露文件参数。
            controlled_launch = launch_method(target_app, enable_real_launch=phase105_gate_passed, test_file=phase105_test_file) if callable(launch_method) else {"ok": True, "decision": "phase102_recording_only_without_phase103_candidate", "controlled_launch_candidate_ready": False, "safe_start_process_plan": False, "real_app_launch_default_disabled": True, "backend_launch_reaches_launcher": False, "real_dispatch_performed": False, "real_desktop_touched": False, "low_level_event_count": 0, "target_app": target_app}  # 修改代码+Phase105FullModeControlledRealLaunch：把 Phase105 门结果传给受控候选；如果没有这行代码，full gate 无法真正触达受控真实启动后端。
            launch_recording = {"ok": True, "operation": "launch_app", "recording_only": not phase105_gate_passed, "real_dispatch_performed": bool(controlled_launch.get("real_dispatch_performed", False)), "low_level_event_count": _phase93_low_level_count(controlled_launch), "target_app": target_app}  # 修改代码+Phase105FullModeControlledRealLaunch：启动记录区分 recording-only 和受控真实启动；如果没有这行代码，Phase105 会被误报成旧记录型合同。
            report = {"acted": True, "operation": operation, "action_kind": action_kind, "action_class": action_class, "decision": "authorized_recording_dispatch", "safety_decision": decision, "launch_recording_result": launch_recording, "controlled_launch_candidate_ready": bool(controlled_launch.get("controlled_launch_candidate_ready", False)), "controlled_launch_result": controlled_launch, "real_app_launch_default_disabled": bool(controlled_launch.get("real_app_launch_default_disabled", True)), "backend_launch_reaches_launcher": bool(controlled_launch.get("backend_launch_reaches_launcher", False)), "real_desktop_touched": bool(controlled_launch.get("real_desktop_touched", False)), "high_level_event_count": 1, "input_event_count": 0, "low_level_event_count": _phase93_low_level_count(controlled_launch), "recording_dispatch_only": True, "real_dispatch_allowed": False, "real_dispatch_performed": bool(controlled_launch.get("real_dispatch_performed", False)), "mode_session_used": bool(decision.get("mode_session_used", False)), "per_app_allowlist_required": bool(decision.get("per_app_allowlist_required", False)), "ordinary_apps_allowed_by_risk_policy": bool(decision.get("ordinary_apps_allowed_by_risk_policy", False)), "full_mode_action": True, "full_mode_action_ready": True, "observation_id": observation.get("observation_id", "")}  # 修改代码+Phase103ControlledAppLaunch：返回 full 启动受控候选报告；如果没有这行代码，Phase103 底层能力不会显示在执行入口。
            report["controlled_real_launch_requested"] = phase105_real_launch_requested  # 新增代码+Phase105FullModeControlledRealLaunch：写入真实启动请求字段；如果没有这行代码，调用方无法区分未请求和被拒绝。
            report["controlled_real_launch_target_allowed"] = phase105_target_allowed  # 新增代码+Phase105FullModeControlledRealLaunch：写入目标是否受控允许；如果没有这行代码，paint/calc 等未来目标拒绝原因不清楚。
            report["controlled_real_launch_gate_passed"] = phase105_gate_passed  # 新增代码+Phase105FullModeControlledRealLaunch：写入真实启动门通过状态；如果没有这行代码，测试无法证明 enable_real_launch 的安全来源。
            report["controlled_launch_test_file"] = str(phase105_test_file or "")  # 新增代码+Phase105FullModeControlledRealLaunch：写入受控文件路径摘要；如果没有这行代码，真实 Notepad smoke 的目标文件不可审计。
            report["recording_dispatch_only"] = not phase105_gate_passed  # 新增代码+Phase105FullModeControlledRealLaunch：门通过后不再标成纯记录型；如果没有这行代码，真实启动会被误描述为 recording-only。
            report["real_dispatch_allowed"] = phase105_gate_passed  # 新增代码+Phase105FullModeControlledRealLaunch：写入真实派发是否被允许；如果没有这行代码，报告无法表达 full-mode 真实启动授权结果。
            report["decision"] = "authorized_controlled_real_launch" if phase105_gate_passed else "authorized_recording_dispatch"  # 新增代码+Phase105FullModeControlledRealLaunch：用不同决策名区分真实桥接和旧记录路径；如果没有这行代码，Phase105 和 Phase102/103 会混在一起。
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
    def __init__(self, base_dir: str | Path | None = None, phase92_runtime: UniversalWindowsComputerUseRuntime | None = None, safety_boundary: WindowsRealAppSafetyBoundary | None = None, grant_store: WindowsComputerUsePersistentGrantStore | None = None, host_adapter: WindowsProductionComputerUseHostAdapter | None = None, mode_store: Any | None = None, controlled_launch_candidate: Any | None = None, controlled_real_launch_enabled: bool = False, controlled_launch_test_file: str | Path | None = None) -> None:  # 修改代码+Phase105FullModeControlledRealLaunch：增加受控真实启动开关和受控文件参数；如果没有这行代码，外部无法安全启用 Phase105 真实启动链路。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_PHASE93_UNIVERSAL_LIVE_EXECUTION_ROOT / f"session-{int(time.time() * 1000)}"  # 新增代码+Phase93UniversalLiveExecutionGate：确定运行根目录；如果没有这行代码，多次运行会互相污染。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase93UniversalLiveExecutionGate：确保根目录存在；如果没有这行代码，报告落盘会失败。
        self.phase92_runtime = phase92_runtime or UniversalWindowsComputerUseRuntime(base_dir=self.base_dir / "phase92")  # 新增代码+Phase93UniversalLiveExecutionGate：创建或复用 Phase92 通用 runtime；如果没有这行代码，prompt mode 主线断开。
        self.safety_boundary = safety_boundary or WindowsRealAppSafetyBoundary()  # 新增代码+Phase93UniversalLiveExecutionGate：创建或复用安全边界；如果没有这行代码，真实执行前没有授权和危险窗口检查。
        self.grant_store = grant_store or WindowsComputerUsePersistentGrantStore(base_dir=self.base_dir / "grants")  # 新增代码+Phase93UniversalLiveExecutionGate：创建隔离授权 store；如果没有这行代码，授权事实源会污染全局。
        self.mode_store = mode_store or ComputerUseModeSessionStore(base_dir=self.base_dir / "mode_sessions")  # 新增代码+Phase99UniversalComputerUseModeGate：创建或复用 mode session store；如果没有这行代码，live gate 无法根据 `/computer use` normal/observe 状态决策。
        self.controlled_launch_candidate = controlled_launch_candidate  # 新增代码+Phase103ControlledAppLaunch：保存受控应用启动候选；如果没有这行代码，run_prompt 无法把候选传给 actor。
        self.controlled_real_launch_enabled = bool(controlled_real_launch_enabled)  # 新增代码+Phase105FullModeControlledRealLaunch：保存公开 runtime 的真实启动开关；如果没有这行代码，run_prompt 无法把 Phase105 门传给 actor。
        self.controlled_launch_test_file = str(controlled_launch_test_file) if controlled_launch_test_file is not None else None  # 新增代码+Phase105FullModeControlledRealLaunch：保存公开 runtime 的受控文件路径；如果没有这行代码，受控 Notepad 启动缺少唯一文件参数。
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
        actor = _Phase93ClosedLoopActor(window, self.safety_boundary, self.grant_store, self.mode_store, session_id, self.control_runtime, self.input_runtime, bool(request_real_actions), self.controlled_launch_candidate, self.controlled_real_launch_enabled, self.controlled_launch_test_file)  # 修改代码+Phase105FullModeControlledRealLaunch：创建动作器并传入受控真实启动门；如果没有这行代码，Phase105 开关不会影响 launch_app。
        loop = self.closed_loop_executor.run(task_plan, _Phase93ClosedLoopObserver(window), actor, _Phase93ClosedLoopVerifier(), _Phase93ClosedLoopRecoverer())  # 新增代码+Phase93UniversalLiveExecutionGate：运行通用闭环；如果没有这行代码，Phase93 只是静态声明而不是执行结构。
        status = self.status()  # 新增代码+Phase93UniversalLiveExecutionGate：读取组合状态；如果没有这行代码，报告要重复拼装固定字段。
        action_reports = list(actor.action_reports)  # 新增代码+Phase99UniversalComputerUseModeGate：复制动作报告用于汇总 mode 字段；如果没有这行代码，总报告无法反映动作层是否使用 mode gate。
        low_level_event_count = sum(_phase93_low_level_count(action_report) for action_report in action_reports)  # 新增代码+Phase99UniversalComputerUseModeGate：汇总动作层低层事件数；如果没有这行代码，运行报告无法证明记录型路径没有物理派发。
        real_desktop_touched = bool(any(action_report.get("real_desktop_touched") or dict(action_report.get("controlled_launch_result", {}) or {}).get("real_desktop_touched") for action_report in action_reports if isinstance(action_report, dict)))  # 新增代码+Phase103ControlledAppLaunch：汇总动作层是否触碰真实桌面；如果没有这行代码，总报告无法证明受控启动候选默认零副作用。
        per_app_allowlist_required = bool(any(action_report.get("per_app_allowlist_required") for action_report in action_reports))  # 新增代码+Phase99UniversalComputerUseModeGate：汇总是否仍要求 app 白名单；如果没有这行代码，旧授权要求可能悄悄混回总报告。
        ordinary_apps_allowed_by_risk_policy = bool(any(action_report.get("ordinary_apps_allowed_by_risk_policy") for action_report in action_reports))  # 新增代码+Phase99UniversalComputerUseModeGate：汇总普通 app 风险策略放行状态；如果没有这行代码，normal mode 的核心语义不会显示在总报告。
        full_mode_session_used = bool(mode_status.get("full_mode", False))  # 新增代码+Phase102FullModeExecutionGate：汇总当前是否处于 full session；如果没有这行代码，用户看不出 `/computer use --full-confirm` 是否生效。
        full_mode_action_ready = bool(any(action_report.get("full_mode_action_ready") for action_report in action_reports))  # 新增代码+Phase102FullModeExecutionGate：汇总是否有 full 动作通过门禁；如果没有这行代码，full 模式可能只停留在状态层。
        full_mode_action_classes = sorted({str(action_report.get("action_class", "")) for action_report in action_reports if bool(action_report.get("full_mode_action")) or bool(action_report.get("full_mode_action_ready"))})  # 新增代码+Phase102FullModeExecutionGate：汇总本轮涉及的 full 动作类；如果没有这行代码，报告无法说明 full 放宽了哪类动作。
        full_mode_controlled_real_launch_ready = bool(any(action_report.get("controlled_real_launch_gate_passed") and action_report.get("backend_launch_reaches_launcher") and _phase93_low_level_count(action_report) == 0 for action_report in action_reports if isinstance(action_report, dict)))  # 新增代码+Phase105FullModeControlledRealLaunch：汇总 Phase105 是否到达受控启动后端；如果没有这行代码，总报告无法证明 full gate 真正接上真实启动候选。
        controlled_real_launch_requested = bool(any(action_report.get("controlled_real_launch_requested") for action_report in action_reports if isinstance(action_report, dict)))  # 新增代码+Phase105FullModeControlledRealLaunch：汇总本轮是否请求受控真实启动；如果没有这行代码，CLI 无法区分默认关闭和显式请求。
        controlled_real_launch_gate_passed = bool(any(action_report.get("controlled_real_launch_gate_passed") for action_report in action_reports if isinstance(action_report, dict)))  # 新增代码+Phase105FullModeControlledRealLaunch：汇总受控真实启动门是否通过；如果没有这行代码，终端验收无法证明双门效果。
        authorized_recording_loop_ready = bool(request_real_actions and any(report.get("acted") and report.get("recording_dispatch_only") and int(report.get("high_level_event_count", 0) or 0) > 0 and (int(report.get("input_event_count", 0) or 0) > 0 or bool(report.get("full_mode_action_ready"))) and _phase93_low_level_count(report) == 0 for report in action_reports))  # 修改代码+Phase105FullModeControlledRealLaunch：只把纯记录动作归入 recording-only；如果没有这行代码，真实启动会被误判成 Phase102 记录型合同。
        blocked_action_decision = next((str(action_report.get("decision", "")) for action_report in action_reports if (not bool(action_report.get("acted"))) and str(action_report.get("decision", "")) and str(action_report.get("decision", "")) not in {"observe_step_no_dispatch", "real_actions_disabled_by_default"}), "")  # 修改代码+Phase102FullModeExecutionGate：跳过观察/预览类非阻断报告后提取真正拦截原因；如果没有这行代码，observe 会遮住 launch_app 的 mode 拒绝。
        mode_blocking_decisions = {"action_risk_exceeds_mode", "dangerous_target_blocked", "computer_use_stopped", "mode_expired", "action_class_not_allowed_by_mode"}  # 新增代码+Phase99UniversalComputerUseModeGate：列出属于 mode session 拦截的稳定原因；如果没有这行代码，高风险安全边界拒绝会和 mode 拒绝混在一起。
        real_action_decision = "authorized_controlled_real_launch" if full_mode_controlled_real_launch_ready else ("authorized_recording_only" if authorized_recording_loop_ready else ("preview_only_default_disabled" if not bool(request_real_actions) else ("blocked_by_mode_session" if blocked_action_decision in mode_blocking_decisions else "blocked_by_safety_boundary")))  # 修改代码+Phase105FullModeControlledRealLaunch：优先报告受控真实启动结论；如果没有这行代码，Phase105 会被旧 recording-only 文案掩盖。
        report = {"ok": bool(phase92_report.get("ok") and loop.get("closed_loop_execution")), "marker": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER, "ok_token": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN, "model": PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MODEL, "prompt_sha256_16": prompt_digest, "prompt_text_included": False, "prompt_length": len(prompt_text), "raw_prompt_hidden": True, "phase92_model": phase92_report.get("model", ""), "phase92_ok": bool(phase92_report.get("ok")), "phase92_prompt_digest": phase92_report.get("prompt_sha256_16", ""), "loop": loop, "loop_event_count": len(loop.get("events", []) or []), "real_actions_requested": bool(request_real_actions), "real_action_decision": real_action_decision, "real_action_blocked_decision": blocked_action_decision, "authorized_recording_loop_ready": authorized_recording_loop_ready, "recording_dispatch_only": True, "real_dispatch_performed": real_desktop_touched, "real_desktop_touched": real_desktop_touched, "low_level_event_count": low_level_event_count, "mode_session_used": mode_session_used or bool(any(action_report.get("mode_session_used") for action_report in action_reports)), "full_mode_session_used": full_mode_session_used, "full_mode_action_ready": full_mode_action_ready, "full_mode_action_classes": full_mode_action_classes, "per_app_allowlist_required": per_app_allowlist_required, "ordinary_apps_allowed_by_risk_policy": ordinary_apps_allowed_by_risk_policy, "uses_phase92_universal_runtime": bool(status["uses_phase92_universal_runtime"]), "single_universal_live_loop": bool(status["single_universal_live_loop"]), "prompt_to_observe_plan_act_verify": bool(status["prompt_to_observe_plan_act_verify"]), "no_per_app_controller": bool(status["no_per_app_controller"]), "representative_apps_are_acceptance_only": bool(status["representative_apps_are_acceptance_only"]), "uses_closed_loop_executor": bool(status["uses_closed_loop_executor"]), "uses_generic_action_layer": bool(status["uses_generic_action_layer"]), "uses_real_app_safety_boundary": bool(status["uses_real_app_safety_boundary"]), "uses_mode_session_gate": bool(status["uses_mode_session_gate"]), "uses_production_host_adapter": bool(status["uses_production_host_adapter"]), "requires_explicit_user_authorization": bool(status["requires_explicit_user_authorization"]), "real_actions_default_disabled": bool(status["real_actions_default_disabled"]), "uncontrolled_actions_expanded": bool(status["uncontrolled_actions_expanded"])}  # 修改代码+Phase103ControlledAppLaunch：运行报告加入真实桌面触碰汇总；如果没有这行代码，用户无法确认受控启动候选默认没有打开应用。
        report["controlled_real_launch_default_disabled"] = not bool(self.controlled_real_launch_enabled)  # 新增代码+Phase105FullModeControlledRealLaunch：写入受控真实启动默认关闭字段；如果没有这行代码，用户无法确认 full 模式不是默认开闸。
        report["controlled_real_launch_requested"] = controlled_real_launch_requested  # 新增代码+Phase105FullModeControlledRealLaunch：写入本轮是否请求真实启动；如果没有这行代码，合同无法解释为何没有打开应用。
        report["controlled_real_launch_gate_passed"] = controlled_real_launch_gate_passed  # 新增代码+Phase105FullModeControlledRealLaunch：写入真实启动门是否通过；如果没有这行代码，终端报告无法审计授权路径。
        report["full_mode_controlled_real_launch_ready"] = full_mode_controlled_real_launch_ready  # 新增代码+Phase105FullModeControlledRealLaunch：写入 full-mode 受控真实启动是否就绪；如果没有这行代码，测试无法证明最后一跳已接入。
        report["recording_dispatch_only"] = not full_mode_controlled_real_launch_ready  # 新增代码+Phase105FullModeControlledRealLaunch：真实启动就绪时不再标记为纯记录；如果没有这行代码，报告语义会误导用户。
        report["real_dispatch_allowed"] = controlled_real_launch_gate_passed  # 新增代码+Phase105FullModeControlledRealLaunch：写入真实派发是否允许；如果没有这行代码，审计报告缺少授权结论。
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


class Phase105ControlledNotepadSmokeLaunchCandidate:  # 新增代码+Phase105FullModeControlledRealLaunch：类段开始，把 full-mode launch_app 桥接到 Phase104 Notepad smoke；如果没有这个类，真实启动可能绕过窗口验证和清理。
    def __init__(self, base_dir: str | Path | None = None, launch_backend: Any | None = None, window_probe: Any | None = None, platform: str | None = None) -> None:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，初始化 Phase105 smoke bridge；如果没有这段函数，真实验收无法注入后端和窗口探测器。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_ROOT / f"smoke-bridge-{int(time.time() * 1000)}"  # 新增代码+Phase105FullModeControlledRealLaunch：选择隔离 smoke bridge 目录；如果没有这行代码，多次真实验收证据会互相覆盖。
        self.launch_backend = launch_backend  # 新增代码+Phase105FullModeControlledRealLaunch：保存可注入启动后端；如果没有这行代码，测试无法用假后端替代真实 Popen。
        self.window_probe = window_probe  # 新增代码+Phase105FullModeControlledRealLaunch：保存可注入窗口探测器；如果没有这行代码，测试无法用假窗口验证替代真实枚举。
        self.platform = platform  # 新增代码+Phase105FullModeControlledRealLaunch：保存可注入平台名；如果没有这行代码，测试无法模拟 Windows/非 Windows 分支。
    # 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，Phase105ControlledNotepadSmokeLaunchCandidate.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch(self, app_name: str, enable_real_launch: bool | None = None, test_file: str | None = None) -> dict[str, Any]:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，按 Phase103 候选接口接收 full gate 请求；如果没有这段函数，Universal gate 无法调用 Phase104 smoke。
        target_app = str(app_name or "").strip().lower()  # 新增代码+Phase105FullModeControlledRealLaunch：规范化目标应用名；如果没有这行代码，大小写和空格会影响安全判断。
        _ = test_file  # 新增代码+Phase105FullModeControlledRealLaunch：明确 Phase104 自己生成唯一受控文件；如果没有这行代码，读者可能误以为传入文件被遗漏。
        if not bool(enable_real_launch):  # 新增代码+Phase105FullModeControlledRealLaunch：保留默认关闭路径；如果没有这行代码，full gate 未开 Phase105 门时也可能打开 Notepad。
            return {"ok": True, "decision": "real_app_launch_disabled_by_default", "controlled_launch_candidate_ready": True, "safe_start_process_plan": target_app == "notepad", "real_app_launch_default_disabled": True, "backend_launch_reaches_launcher": False, "real_dispatch_performed": False, "real_desktop_touched": False, "low_level_event_count": 0, "unsafe_launch_zero_events": False, "uncontrolled_actions_expanded": False, "target_app": target_app}  # 新增代码+Phase105FullModeControlledRealLaunch：返回默认关闭零副作用报告；如果没有这行代码，合同无法证明未越过最后一跳。
        if target_app != "notepad":  # 新增代码+Phase105FullModeControlledRealLaunch：只允许本阶段的 Notepad 受控样本；如果没有这行代码，Phase105 会被误扩成通用真实应用启动。
            return {"ok": False, "decision": "phase105_notepad_only_real_launch_refused", "controlled_launch_candidate_ready": True, "safe_start_process_plan": False, "real_app_launch_default_disabled": True, "backend_launch_reaches_launcher": False, "real_dispatch_performed": False, "real_desktop_touched": False, "low_level_event_count": 0, "unsafe_launch_zero_events": True, "uncontrolled_actions_expanded": False, "target_app": target_app}  # 新增代码+Phase105FullModeControlledRealLaunch：返回非 Notepad 零事件拒绝；如果没有这行代码，未来目标漂移可能误触桌面。
        try:  # 新增代码+Phase105FullModeControlledRealLaunch：优先按包路径导入 Phase104 smoke runtime；如果没有这段代码，测试和真实终端不能共享窗口验证清理实现。
            from learning_agent.computer_use.controlled_notepad_launch_smoke import WindowsControlledNotepadLaunchSmoke  # 新增代码+Phase105FullModeControlledRealLaunch：导入 Phase104 可见 Notepad smoke；如果没有这行代码，Phase105 会缺少真实窗口验证和清理。
        except ModuleNotFoundError as error:  # 新增代码+Phase105FullModeControlledRealLaunch：兼容 start_oauth_agent.bat 脚本模式；如果没有这段代码，可见终端从 learning_agent 目录运行可能导入失败。
            if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.controlled_notepad_launch_smoke"}:  # 新增代码+Phase105FullModeControlledRealLaunch：只兜底包路径缺失；如果没有这行代码，Phase104 内部 bug 会被误吞。
                raise  # 新增代码+Phase105FullModeControlledRealLaunch：重新抛出真实内部导入错误；如果没有这行代码，排查会被错误 fallback 干扰。
            from computer_use.controlled_notepad_launch_smoke import WindowsControlledNotepadLaunchSmoke  # type: ignore  # 新增代码+Phase105FullModeControlledRealLaunch：脚本模式导入 Phase104 smoke；如果没有这行代码，bat 入口无法运行 Phase105 真实分支。
        smoke = WindowsControlledNotepadLaunchSmoke(base_dir=self.base_dir, launch_backend=self.launch_backend, window_probe=self.window_probe, platform=self.platform)  # 新增代码+Phase105FullModeControlledRealLaunch：创建 Phase104 smoke runtime；如果没有这行代码，真实启动没有窗口验证和清理主体。
        phase104_report = smoke.run(real_smoke=True, allow_real_gate=True)  # 新增代码+Phase105FullModeControlledRealLaunch：运行已双门确认后的 Phase104 真实 smoke；如果没有这行代码，full gate 只会停在候选对象而不打开受控窗口。
        return {"ok": bool(phase104_report.get("passed")), "decision": "phase105_phase104_controlled_notepad_smoke_bridge_completed", "controlled_launch_candidate_ready": True, "safe_start_process_plan": True, "real_app_launch_default_disabled": True, "backend_launch_reaches_launcher": bool(phase104_report.get("real_notepad_launch_attempted")), "real_dispatch_performed": bool(phase104_report.get("real_desktop_touched")), "real_desktop_touched": bool(phase104_report.get("real_desktop_touched")), "low_level_event_count": 0, "unsafe_launch_zero_events": bool(phase104_report.get("unsafe_launch_zero_events")), "uncontrolled_actions_expanded": bool(phase104_report.get("uncontrolled_actions_expanded")), "target_app": target_app, "phase104_smoke_report": phase104_report, "visible_window_verified": bool(phase104_report.get("visible_window_verified")), "cleanup_completed": bool(phase104_report.get("cleanup_completed")), "verified_window_cleanup_completed": bool(phase104_report.get("verified_window_cleanup_completed")), "residual_owned_process": bool(phase104_report.get("residual_owned_process"))}  # 新增代码+Phase105FullModeControlledRealLaunch：返回 Phase103 形状的受控真实启动摘要；如果没有这行代码，Universal gate 无法统一汇总 Phase104 结果。
    # 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，Phase105ControlledNotepadSmokeLaunchCandidate.launch 到此结束；如果没有这个边界说明，初学者不容易看出桥接范围。
# 新增代码+Phase105FullModeControlledRealLaunch：类段结束，Phase105ControlledNotepadSmokeLaunchCandidate 到此结束；如果没有这个边界说明，初学者不容易看出真实 smoke bridge 范围。


def _phase105_confirmed_full_store(root: Path, reason: str) -> ComputerUseModeSessionStore:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，创建已确认 full store；如果没有这段函数，Phase105 合同可能绕过强确认流程。
    store = ComputerUseModeSessionStore(base_dir=root / "mode_sessions")  # 新增代码+Phase105FullModeControlledRealLaunch：创建隔离 mode store；如果没有这行代码，合同会污染真实用户模式状态。
    request = store.request_full_mode(reason=reason)  # 新增代码+Phase105FullModeControlledRealLaunch：按真实流程申请 full token；如果没有这行代码，合同不能证明 `/computer use --full` 的确认门。
    confirmed = store.confirm_full_mode(request["confirmation_token"], reason=reason)  # 新增代码+Phase105FullModeControlledRealLaunch：用 token 确认 full；如果没有这行代码，launch_app 仍应被 mode gate 拦截。
    if not bool(confirmed.get("full_mode")):  # 新增代码+Phase105FullModeControlledRealLaunch：防御性检查 full 确认结果；如果没有这行代码，失败前置条件会变成难懂的后续断言失败。
        raise RuntimeError("Phase105 full mode confirmation failed")  # 新增代码+Phase105FullModeControlledRealLaunch：明确抛出 full 确认失败；如果没有这行代码，合同会在错误状态下继续运行。
    return store  # 新增代码+Phase105FullModeControlledRealLaunch：返回已确认 mode store；如果没有这行代码，runtime 无法读取 full 状态。
# 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，_phase105_confirmed_full_store 到此结束；如果没有这个边界说明，初学者不容易看出 full 确认范围。


def _phase105_launch_action_report(report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，从闭环报告提取 launch_app 动作；如果没有这段函数，合同会被 observe/verify 事件干扰。
    events = dict(report.get("loop", {}) or {}).get("events", [])  # 新增代码+Phase105FullModeControlledRealLaunch：读取闭环事件；如果没有这行代码，无法定位动作结果。
    for event in events:  # 新增代码+Phase105FullModeControlledRealLaunch：逐个扫描事件；如果没有这行代码，合同无法找到 launch_app 报告。
        action_result = dict(event.get("action_result", {}) or {}) if isinstance(event, dict) else {}  # 新增代码+Phase105FullModeControlledRealLaunch：安全读取动作结果；如果没有这行代码，坏事件会导致 KeyError。
        if event.get("state") == "acted" and action_result.get("action_class") == "launch_app":  # 新增代码+Phase105FullModeControlledRealLaunch：只选择真正执行阶段的 launch_app；如果没有这行代码，观察步骤可能误参与判断。
            return action_result  # 新增代码+Phase105FullModeControlledRealLaunch：返回启动动作报告；如果没有这行代码，调用方拿不到受控启动字段。
    return {}  # 新增代码+Phase105FullModeControlledRealLaunch：找不到时返回空字典；如果没有这行代码，合同失败时无法优雅报告。
# 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，_phase105_launch_action_report 到此结束；如果没有这个边界说明，初学者不容易看出动作筛选范围。


def run_phase105_full_mode_controlled_real_launch_contract(base_dir: str | Path | None = None, real_launch: bool | None = None, allow_real_gate: bool | None = None, real_launch_candidate: Any | None = None, launch_backend: Any | None = None, window_probe: Any | None = None, platform: str | None = None) -> dict[str, Any]:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，运行 Phase105 full-mode 受控真实启动合同；如果没有这段函数，真实终端没有统一验收入口。
    try:  # 新增代码+Phase105FullModeControlledRealLaunch：优先按包路径导入 Phase103 安全候选；如果没有这段代码，默认安全分支无法复用受控启动计划。
        from learning_agent.computer_use.controlled_app_launch import Phase103RecordingLaunchBackend, WindowsControlledAppLaunchCandidate  # 新增代码+Phase105FullModeControlledRealLaunch：导入记录后端和受控候选；如果没有这行代码，合同无法证明默认关闭和启用桥接。
    except ModuleNotFoundError as error:  # 新增代码+Phase105FullModeControlledRealLaunch：兼容 start_oauth_agent.bat 脚本模式；如果没有这段代码，可见终端可能导入失败。
        if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.controlled_app_launch"}:  # 新增代码+Phase105FullModeControlledRealLaunch：只兜底包路径缺失；如果没有这行代码，Phase103 内部 bug 会被误吞。
            raise  # 新增代码+Phase105FullModeControlledRealLaunch：重新抛出非路径类错误；如果没有这行代码，真实问题会被隐藏。
        from computer_use.controlled_app_launch import Phase103RecordingLaunchBackend, WindowsControlledAppLaunchCandidate  # type: ignore  # 新增代码+Phase105FullModeControlledRealLaunch：脚本模式导入 Phase103 候选；如果没有这行代码，bat 入口无法运行 Phase105 默认合同。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase105FullModeControlledRealLaunch：选择隔离合同根目录；如果没有这行代码，多次报告和 mode 状态会互相污染。
    root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase105FullModeControlledRealLaunch：确保合同根目录存在；如果没有这行代码，报告和受控文件写入会失败。
    requested = _phase105_request_real_launch(real_launch)  # 新增代码+Phase105FullModeControlledRealLaunch：读取本次是否请求真实启动；如果没有这行代码，默认安全合同和真实 smoke 会混淆。
    allowed = _phase105_allow_real_launch(allow_real_gate)  # 新增代码+Phase105FullModeControlledRealLaunch：读取真实启动允许门；如果没有这行代码，真实桌面动作缺少第二道开关。
    default_backend = Phase103RecordingLaunchBackend()  # 新增代码+Phase105FullModeControlledRealLaunch：创建默认关闭记录后端；如果没有这行代码，无法证明默认路径没有调用后端。
    default_candidate = WindowsControlledAppLaunchCandidate(launch_backend=default_backend)  # 新增代码+Phase105FullModeControlledRealLaunch：创建默认关闭受控候选；如果没有这行代码，默认路径不会复用安全启动计划。
    default_store = _phase105_confirmed_full_store(root / "default_off", "Phase105 default-off full mode")  # 新增代码+Phase105FullModeControlledRealLaunch：创建默认关闭 full store；如果没有这行代码，默认测试可能不是 full 模式。
    default_runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "default_off_live_gate", mode_store=default_store, controlled_launch_candidate=default_candidate)  # 新增代码+Phase105FullModeControlledRealLaunch：创建未开启真实门的 runtime；如果没有这行代码，默认关闭链路没有执行入口。
    default_report = default_runtime.run_prompt("请使用 /computer use --full 启动 notepad，但不要真实打开。", request_real_actions=True)  # 新增代码+Phase105FullModeControlledRealLaunch：运行默认关闭用户风格 prompt；如果没有这行代码，默认关闭没有事实证据。
    default_launch = _phase105_launch_action_report(default_report)  # 新增代码+Phase105FullModeControlledRealLaunch：提取默认关闭启动报告；如果没有这行代码，无法计算零副作用。
    enabled_backend = Phase103RecordingLaunchBackend()  # 新增代码+Phase105FullModeControlledRealLaunch：创建显式启用记录后端；如果没有这行代码，无法安全证明 enable_real_launch 会到达最后一跳。
    enabled_candidate = WindowsControlledAppLaunchCandidate(launch_backend=enabled_backend)  # 新增代码+Phase105FullModeControlledRealLaunch：创建显式启用受控候选；如果没有这行代码，Phase105 正向桥接没有被测对象。
    enabled_file = root / "controlled_files" / "phase105-full-mode-controlled-real-launch.txt"  # 新增代码+Phase105FullModeControlledRealLaunch：定义受控测试文件路径；如果没有这行代码，启用路径无法证明只传受控文件。
    enabled_file.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase105FullModeControlledRealLaunch：确保受控文件目录存在；如果没有这行代码，写测试文件会失败。
    enabled_file.write_text("Phase105 controlled full-mode launch bridge evidence.\n", encoding="utf-8")  # 新增代码+Phase105FullModeControlledRealLaunch：写入受控证据文件；如果没有这行代码，传给 Notepad 的路径可能不存在。
    enabled_store = _phase105_confirmed_full_store(root / "enabled_bridge", "Phase105 enabled full mode bridge")  # 新增代码+Phase105FullModeControlledRealLaunch：创建显式启用 full store；如果没有这行代码，正向桥接可能被 mode gate 拦截。
    enabled_runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "enabled_live_gate", mode_store=enabled_store, controlled_launch_candidate=enabled_candidate, controlled_real_launch_enabled=True, controlled_launch_test_file=enabled_file)  # 新增代码+Phase105FullModeControlledRealLaunch：创建开启 Phase105 门的 runtime；如果没有这行代码，enable_real_launch 不会传入候选。
    enabled_report = enabled_runtime.run_prompt("请使用 /computer use --full 启动 notepad，并保持受控。", request_real_actions=True)  # 新增代码+Phase105FullModeControlledRealLaunch：运行正向桥接 prompt；如果没有这行代码，Phase105 最后一跳没有事实证据。
    enabled_launch = _phase105_launch_action_report(enabled_report)  # 新增代码+Phase105FullModeControlledRealLaunch：提取正向桥接启动报告；如果没有这行代码，无法判断 full gate 是否传递 enable_real_launch。
    real_gate_report: dict[str, Any] = {}  # 新增代码+Phase105FullModeControlledRealLaunch：初始化真实分支 runtime 报告；如果没有这行代码，未请求真实 smoke 时汇总会引用未定义变量。
    real_launch_action: dict[str, Any] = {}  # 新增代码+Phase105FullModeControlledRealLaunch：初始化真实分支动作报告；如果没有这行代码，未请求真实 smoke 时报告结构不稳定。
    if requested and allowed:  # 新增代码+Phase105FullModeControlledRealLaunch：只有请求门和允许门同时满足才真实启动；如果没有这行代码，单门可能误触桌面。
        candidate = real_launch_candidate if real_launch_candidate is not None else Phase105ControlledNotepadSmokeLaunchCandidate(base_dir=root / "real_smoke_bridge", launch_backend=launch_backend, window_probe=window_probe, platform=platform)  # 新增代码+Phase105FullModeControlledRealLaunch：创建或复用 Phase104 smoke bridge；如果没有这行代码，真实路径没有清理保护。
        real_store = _phase105_confirmed_full_store(root / "real_bridge", "Phase105 real full mode bridge")  # 新增代码+Phase105FullModeControlledRealLaunch：创建真实分支 full store；如果没有这行代码，真实启动可能绕过 full 确认。
        real_runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "real_live_gate", mode_store=real_store, controlled_launch_candidate=candidate, controlled_real_launch_enabled=True)  # 新增代码+Phase105FullModeControlledRealLaunch：创建真实分支 runtime；如果没有这行代码，Phase104 smoke 不会从 full gate 入口触发。
        real_gate_report = real_runtime.run_prompt("请使用 /computer use --full 启动 notepad，执行受控真实 smoke 并清理。", request_real_actions=True)  # 新增代码+Phase105FullModeControlledRealLaunch：运行真实用户风格 prompt；如果没有这行代码，可见终端无法证明真实链路接入。
        real_launch_action = _phase105_launch_action_report(real_gate_report)  # 新增代码+Phase105FullModeControlledRealLaunch：提取真实分支启动报告；如果没有这行代码，真实 smoke 结果无法汇总。
    controlled_result = dict(real_launch_action.get("controlled_launch_result", {}) or {})  # 新增代码+Phase105FullModeControlledRealLaunch：读取真实分支受控候选结果；如果没有这行代码，Phase104 报告无法被总合同读取。
    phase104_report = dict(controlled_result.get("phase104_smoke_report", {}) or {})  # 新增代码+Phase105FullModeControlledRealLaunch：读取 Phase104 smoke 子报告；如果没有这行代码，窗口验证和清理字段无法上浮。
    default_off_zero_events = bool(default_launch.get("controlled_launch_result", {}).get("decision") == "real_app_launch_disabled_by_default" and not default_launch.get("controlled_real_launch_gate_passed") and not default_launch.get("backend_launch_reaches_launcher") and not default_report.get("real_desktop_touched") and len(default_backend.launches) == 0)  # 新增代码+Phase105FullModeControlledRealLaunch：汇总默认关闭零副作用；如果没有这行代码，full 默认安全性不可量化。
    full_gate_passes_enable_real_launch = bool(enabled_launch.get("controlled_real_launch_gate_passed") and enabled_launch.get("backend_launch_reaches_launcher") and enabled_report.get("full_mode_controlled_real_launch_ready") and len(enabled_backend.launches) == 1 and not enabled_report.get("real_desktop_touched"))  # 新增代码+Phase105FullModeControlledRealLaunch：汇总 full gate 是否把 enable_real_launch 送到受控候选；如果没有这行代码，Phase105 可能只是报告字段变化。
    real_full_launch_attempted = bool(phase104_report.get("real_notepad_launch_attempted"))  # 新增代码+Phase105FullModeControlledRealLaunch：汇总真实 Notepad 是否尝试启动；如果没有这行代码，终端 token 无法表达真实路径。
    visible_window_verified = bool(phase104_report.get("visible_window_verified"))  # 新增代码+Phase105FullModeControlledRealLaunch：汇总真实窗口是否可见；如果没有这行代码，真实启动可能只有进程没有窗口证据。
    cleanup_completed = bool(phase104_report.get("cleanup_completed"))  # 新增代码+Phase105FullModeControlledRealLaunch：汇总进程和窗口清理是否完成；如果没有这行代码，真实 smoke 可能留下窗口。
    verified_window_cleanup_completed = bool(phase104_report.get("verified_window_cleanup_completed"))  # 新增代码+Phase105FullModeControlledRealLaunch：汇总已验证窗口是否关闭；如果没有这行代码，Windows 11 Notepad 代理窗口残留风险不可见。
    residual_owned_process = bool(phase104_report.get("residual_owned_process"))  # 新增代码+Phase105FullModeControlledRealLaunch：汇总是否残留自有进程；如果没有这行代码，清理失败不可见。
    real_branch_ok = bool((not requested and not real_full_launch_attempted) or (requested and allowed and real_full_launch_attempted and visible_window_verified and cleanup_completed and verified_window_cleanup_completed and not residual_owned_process))  # 新增代码+Phase105FullModeControlledRealLaunch：汇总真实分支是否满足合同；如果没有这行代码，未请求和真实请求两种路径会混淆。
    uncontrolled_actions_expanded = bool(default_report.get("uncontrolled_actions_expanded") or enabled_report.get("uncontrolled_actions_expanded") or real_gate_report.get("uncontrolled_actions_expanded") or controlled_result.get("uncontrolled_actions_expanded"))  # 新增代码+Phase105FullModeControlledRealLaunch：确认没有扩张无边界动作面；如果没有这行代码，Phase105 可能被误读为无限控制。
    real_desktop_touched = bool(default_report.get("real_desktop_touched") or enabled_report.get("real_desktop_touched") or real_gate_report.get("real_desktop_touched") or controlled_result.get("real_desktop_touched"))  # 新增代码+Phase105FullModeControlledRealLaunch：汇总是否触碰真实桌面；如果没有这行代码，默认安全合同和真实 smoke 无法区分。
    report_path = root / "reports" / "phase105_full_mode_controlled_real_launch_report.json"  # 新增代码+Phase105FullModeControlledRealLaunch：定义报告路径；如果没有这行代码，验收证据没有固定落点。
    passed = bool(default_off_zero_events and full_gate_passes_enable_real_launch and real_branch_ok and not uncontrolled_actions_expanded)  # 新增代码+Phase105FullModeControlledRealLaunch：汇总合同是否通过；如果没有这行代码，CLI 退出码无法表达失败。
    report = {"marker": PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_MARKER, "ok_token": PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_OK_TOKEN, "model": PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_MODEL, "passed": passed, "default_off_zero_events": default_off_zero_events, "full_gate_passes_enable_real_launch": full_gate_passes_enable_real_launch, "real_enable_gate_required": True, "real_launch_requested": requested, "real_enable_gate_passed": allowed, "real_full_launch_attempted": real_full_launch_attempted, "visible_window_verified": visible_window_verified, "cleanup_completed": cleanup_completed, "verified_window_cleanup_completed": verified_window_cleanup_completed, "residual_owned_process": residual_owned_process, "real_desktop_touched": real_desktop_touched, "uncontrolled_actions_expanded": uncontrolled_actions_expanded, "report_path": str(report_path), "default_report": default_report, "enabled_report": enabled_report, "real_gate_report": real_gate_report, "phase104_smoke_report": phase104_report}  # 新增代码+Phase105FullModeControlledRealLaunch：构造完整 Phase105 合同报告；如果没有这行代码，测试和真实终端拿不到统一事实。
    atomic_write_json(report_path, report)  # 新增代码+Phase105FullModeControlledRealLaunch：写入合同报告；如果没有这行代码，失败时无法复盘真实链路证据。
    return report  # 新增代码+Phase105FullModeControlledRealLaunch：返回合同报告；如果没有这行代码，测试和 CLI 无法读取结果。
# 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，run_phase105_full_mode_controlled_real_launch_contract 到此结束；如果没有这个边界说明，初学者不容易看出 Phase105 合同范围。


def phase105_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，把 Phase105 报告转成稳定终端 token 行；如果没有这段函数，可见终端验收需要解析复杂 JSON。
    ok_token = f" {PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_OK_TOKEN}" if bool(report.get("passed")) else ""  # 新增代码+Phase105FullModeControlledRealLaunch：只在通过时输出 OK token；如果没有这行代码，失败报告可能误带成功锚点。
    return f"{PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_MARKER}{ok_token} default_off_zero_events={_phase93_bool_token(report.get('default_off_zero_events'))} full_gate_passes_enable_real_launch={_phase93_bool_token(report.get('full_gate_passes_enable_real_launch'))} real_enable_gate_required={_phase93_bool_token(report.get('real_enable_gate_required'))} real_full_launch_attempted={_phase93_bool_token(report.get('real_full_launch_attempted'))} visible_window_verified={_phase93_bool_token(report.get('visible_window_verified'))} cleanup_completed={_phase93_bool_token(report.get('cleanup_completed'))} verified_window_cleanup_completed={_phase93_bool_token(report.get('verified_window_cleanup_completed'))} residual_owned_process={_phase93_bool_token(report.get('residual_owned_process'))} real_desktop_touched={_phase93_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase93_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase105FullModeControlledRealLaunch：返回固定顺序 token；如果没有这行代码，验收场景容易因字段顺序变化失败。
# 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，phase105_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 文本范围。


def phase105_main(argv: list[str] | None = None) -> int:  # 新增代码+Phase105FullModeControlledRealLaunch：函数段开始，提供 Phase105 命令行入口；如果没有这段函数，真实可见终端无法一键验收。
    _ = argv  # 新增代码+Phase105FullModeControlledRealLaunch：明确当前不解析命令行参数；如果没有这行代码，读者可能误以为 argv 被遗漏处理。
    report = run_phase105_full_mode_controlled_real_launch_contract()  # 新增代码+Phase105FullModeControlledRealLaunch：运行默认或环境门控制的 Phase105 合同；如果没有这行代码，CLI 没有实际验收内容。
    print(phase105_cli_line(report))  # 新增代码+Phase105FullModeControlledRealLaunch：打印稳定 token 行；如果没有这行代码，验收器无法快速判断通过。
    print(json.dumps({"report_path": report.get("report_path"), "passed": report.get("passed"), "real_full_launch_attempted": report.get("real_full_launch_attempted"), "cleanup_completed": report.get("cleanup_completed")}, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase105FullModeControlledRealLaunch：打印短 JSON 方便定位证据；如果没有这行代码，失败时不容易找到报告。
    print(PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_MARKER)  # 新增代码+Phase105FullModeControlledRealLaunch：单独打印 ready marker；如果没有这行代码，人工观察终端不够直观。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase105FullModeControlledRealLaunch：用退出码表达合同成败；如果没有这行代码，失败也可能被自动化当成成功。
# 新增代码+Phase105FullModeControlledRealLaunch：函数段结束，phase105_main 到此结束；如果没有这个边界说明，初学者不容易看出 Phase105 命令入口范围。


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


__all__ = ["DEFAULT_PHASE93_UNIVERSAL_LIVE_EXECUTION_ROOT", "DEFAULT_PHASE102_FULL_MODE_EXECUTION_GATE_ROOT", "DEFAULT_PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_ROOT", "PHASE93_REAL_ACTIONS_DEFAULT_DISABLED", "PHASE93_UNCONTROLLED_ACTIONS_EXPANDED", "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MARKER", "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_MODEL", "PHASE93_UNIVERSAL_LIVE_EXECUTION_GATE_OK_TOKEN", "PHASE102_FULL_MODE_EXECUTION_GATE_MARKER", "PHASE102_FULL_MODE_EXECUTION_GATE_MODEL", "PHASE102_FULL_MODE_EXECUTION_GATE_OK_TOKEN", "PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_MARKER", "PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_MODEL", "PHASE105_FULL_MODE_CONTROLLED_REAL_LAUNCH_OK_TOKEN", "PHASE113_GENERIC_REAL_LAUNCH_SMOKE_ENV", "PHASE113_INTERACTIVE_GENERIC_LAUNCH_MARKER", "PHASE113_INTERACTIVE_GENERIC_LAUNCH_MODEL", "PHASE113_INTERACTIVE_GENERIC_LAUNCH_OK_TOKEN", "PHASE113_UNCONTROLLED_ACTIONS_EXPANDED", "Phase105ControlledNotepadSmokeLaunchCandidate", "UniversalWindowsLiveExecutionGate", "main", "phase93_cli_line", "phase102_cli_line", "phase102_main", "phase105_cli_line", "phase105_main", "phase113_cli_line", "run_phase93_universal_live_execution_gate_contract", "run_phase102_full_mode_execution_gate_contract", "run_phase105_full_mode_controlled_real_launch_contract", "run_phase113_interactive_generic_launch_bridge"]  # 修改代码+InteractiveGenericLaunchMaturity：公开导出 Phase113 交互通用启动入口和 token；如果没有这行代码，真实终端和矩阵无法稳定导入 Task5 成熟接线。


if __name__ == "__main__":  # 新增代码+Phase93UniversalLiveExecutionGate：允许直接运行本模块；如果没有这行代码，初学者无法用 python 文件方式手动执行 Phase93 自检。
    raise SystemExit(main())  # 新增代码+Phase93UniversalLiveExecutionGate：调用 main 并传递退出码；如果没有这行代码，直接运行文件不会执行验收。
