"""OS 级 Computer Use 控制器。"""  # 新增代码+OSComputerUse: 集中管理桌面控制的安全边界；若没有这个文件，桌面动作会散落在 agent 方法里难以审计。

from __future__ import annotations  # 新增代码+OSComputerUse: 延迟解析类型注解；若没有这行代码，Protocol 等注解在旧执行路径中更容易产生导入顺序问题。

import os  # 新增代码+Phase8ProductionEdges: 读取显式启用真实 Windows 后端的环境变量；如果没有这行代码，Computer Use 后端无法做到默认安全关闭。
import sys  # 新增代码+Phase8ProductionEdges: 判断当前平台是否为 Windows；如果没有这行代码，非 Windows 环境可能误报支持真实桌面控制。
from dataclasses import dataclass  # 新增代码+OSComputerUse: 使用 dataclass 表达动作结果；若没有这行代码，结果对象需要手写大量样板代码。
from typing import Any, Protocol  # 新增代码+OSComputerUse: 引入通用 JSON 参数和后端协议类型；若没有这行代码，控制器边界不清楚。

try:  # 新增代码+Phase27ComputerUse: 包运行模式下导入窗口协议模型；如果没有这行代码，控制器无法使用强类型窗口引用。
    from learning_agent.computer_use_mcp_v2.windows_runtime.action_policy import build_action_evidence, prepare_action_arguments, redact_action_arguments  # 新增代码+Phase30ComputerUseActionGate: 导入动作策略、坐标转换和脱敏 helper；如果没有这行代码，controller 会继续直接保存原始动作参数。
    from learning_agent.computer_use_mcp_v2.windows_runtime.audit import ComputerUseAuditStore  # 新增代码+Phase31ComputerUseLockAbortEvidence: 导入落盘审计仓库；如果没有这行代码，动作前后证据只能停留在内存结果里。
    from learning_agent.computer_use_mcp_v2.windows_runtime.evidence import ComputerUseEvidenceStore, collect_image_result_blocks, format_image_result_lines  # 修改代码+Phase41WindowsImageResults: 导入证据仓库和图片结果格式化 helper；如果没有这行代码，controller 无法把截图 artifact 转成模型可见图片区。
    from learning_agent.computer_use_mcp_v2.windows_runtime.helper_client import NullWindowObservationHelper  # 新增代码+Phase29ComputerUse: 导入默认窗口观察 helper；如果没有这行代码，未配置截图 helper 时后端无法优雅降级。
    from learning_agent.computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager  # 新增代码+Phase30ComputerUseActionGate: 导入 durable lock 管理器；如果没有这行代码，动作无法要求当前会话持有桌面锁。
    from learning_agent.computer_use_mcp_v2.windows_runtime.models import build_window_ref, window_ref_identity  # 新增代码+Phase27ComputerUse: 读取窗口构造和身份键 helper；如果没有这行代码，未知窗口校验只能继续依赖松散 dict。
    from learning_agent.computer_use_mcp_v2.windows_runtime.native_diagnostics import build_phase43_native_capability_matrix  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 导入 Phase43 原生能力矩阵构建器；如果没有这行代码，Windows 后端 status 无法展示统一能力矩阵。
    from learning_agent.computer_use_mcp_v2.windows_runtime.native_helper import WindowsNativeWindowObservationHelper  # 新增代码+Phase32WindowsNativeHelper: 导入 Windows native 只读观察 helper；如果没有这行代码，显式 opt-in 后仍无法启用截图/文本桥接。
    from learning_agent.computer_use_mcp_v2.windows_runtime.cursor_overlay import ComputerUseCursorOverlayLowLevelSender  # 新增代码+ComputerUseCursorOverlay: 导入 Computer Use 鼠标来源橙色叠加层包装器；如果没有这行代码，用户无法肉眼区分真实鼠标动作是不是 Computer Use 内置工具发出的。
    from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+RealComputerActionExecutor: 导入真实低层 Windows 输入 sender；如果没有这行代码，默认真实后端只能创建合同层，无法真正触发鼠标键盘。
    from learning_agent.computer_use_mcp_v2.windows_runtime.sendinput_dispatcher import WindowsSendInputDispatcher  # 新增代码+RealComputerActionExecutor: 导入 Phase47 通用 dispatcher；如果没有这行代码，高层 click/type/key 事件不会展开成低层 SendInput 序列。
    from learning_agent.computer_use_mcp_v2.windows_runtime.sendinput_executor import WindowsSendInputExecutor  # 新增代码+Phase37WindowsSendInputExecutor: 导入 SendInput 动作执行器合同；如果没有这行代码，Windows 后端会继续依赖旧 mouse_event 路径。
    from learning_agent.computer_use_mcp_v2.windows_runtime.fresh_target_policy import decide_fresh_target_preflight, decide_recovery_after_drift  # 新增代码+FreshTargetPolicy：导入通用新目标预检和漂移恢复策略；如果没有这一行，controller 只能靠提示词避免旧窗口。
    from learning_agent.computer_use_mcp_v2.windows_runtime.target_lease import WRITE_ACTIONS_REQUIRING_LEASE, build_target_lease, target_lease_from_dict, verify_target_lease_before_action  # 新增代码+ControllerTargetLease：导入通用目标租约构造和动作前校验；如果没有这一行，controller 仍只能校验窗口字段，不能校验控制权限来源。
    from learning_agent.computer_use_mcp_v2.windows_runtime.target_registry import ComputerUseTargetRegistry  # 新增代码+TargetRegistryRootRemediation: 导入 session 目标窗口注册表；如果没有这一行，controller 仍只能依赖模型手动携带 target_window。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase28ComputerUse: 导入真实 Windows 只读窗口 inventory probe；如果没有这行代码，Windows 后端无法执行 list_windows/list_apps。
except ModuleNotFoundError as error:  # 新增代码+Phase27ComputerUse: 捕获直接脚本运行时包名不可用的情况；如果没有这行代码，start_oauth_agent.bat 的脚本模式可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.action_policy", "learning_agent.computer_use_mcp_v2.windows_runtime.audit", "learning_agent.computer_use_mcp_v2.windows_runtime.cursor_overlay", "learning_agent.computer_use_mcp_v2.windows_runtime.evidence", "learning_agent.computer_use_mcp_v2.windows_runtime.fresh_target_policy", "learning_agent.computer_use_mcp_v2.windows_runtime.helper_client", "learning_agent.computer_use_mcp_v2.windows_runtime.lock", "learning_agent.computer_use_mcp_v2.windows_runtime.models", "learning_agent.computer_use_mcp_v2.windows_runtime.native_diagnostics", "learning_agent.computer_use_mcp_v2.windows_runtime.native_helper", "learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard", "learning_agent.computer_use_mcp_v2.windows_runtime.sendinput_dispatcher", "learning_agent.computer_use_mcp_v2.windows_runtime.sendinput_executor", "learning_agent.computer_use_mcp_v2.windows_runtime.target_lease", "learning_agent.computer_use_mcp_v2.windows_runtime.target_registry", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend"}:  # 修改代码+FreshTargetPolicy：允许 fresh_target_policy 在脚本模式 fallback；如果没有这一行，start_oauth_agent.bat 会把包名前缀差异误当成真实导入 bug。
        raise  # 新增代码+Phase27ComputerUse: 重新抛出真实导入错误；如果没有这行代码，排查协议模型问题会很困难。
    from computer_use_mcp_v2.windows_runtime.action_policy import build_action_evidence, prepare_action_arguments, redact_action_arguments  # 新增代码+Phase30ComputerUseActionGate: 脚本模式下导入动作策略 helper；如果没有这行代码，bat 入口无法加载 Phase 30 坐标转换和脱敏逻辑。
    from computer_use_mcp_v2.windows_runtime.audit import ComputerUseAuditStore  # 新增代码+Phase31ComputerUseLockAbortEvidence: 脚本模式下导入落盘审计仓库；如果没有这行代码，bat 入口无法保存动作证据链。
    from computer_use_mcp_v2.windows_runtime.evidence import ComputerUseEvidenceStore, collect_image_result_blocks, format_image_result_lines  # 修改代码+Phase41WindowsImageResults: 脚本模式导入图片结果 helper；如果没有这行代码，bat 入口无法输出 Phase41 图片区块。
    from computer_use_mcp_v2.windows_runtime.helper_client import NullWindowObservationHelper  # 新增代码+Phase29ComputerUse: 脚本模式下导入默认观察 helper；如果没有这行代码，bat 入口无法加载 Phase 29 后端。
    from computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager  # 新增代码+Phase30ComputerUseActionGate: 脚本模式下导入 durable lock 管理器；如果没有这行代码，bat 入口无法执行持锁门禁。
    from computer_use_mcp_v2.windows_runtime.models import build_window_ref, window_ref_identity  # 新增代码+Phase27ComputerUse: 脚本模式下从本地 computer_use 包导入模型；如果没有这行代码，bat 入口无法加载 Phase 27 协议。
    from computer_use_mcp_v2.windows_runtime.native_diagnostics import build_phase43_native_capability_matrix  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 脚本模式导入 Phase43 能力矩阵；如果没有这行代码，start_oauth_agent.bat 无法显示矩阵状态。
    from computer_use_mcp_v2.windows_runtime.native_helper import WindowsNativeWindowObservationHelper  # 新增代码+Phase32WindowsNativeHelper: 脚本模式下导入 native helper；如果没有这行代码，bat 入口无法启用 Phase32 只读桥接。
    from computer_use_mcp_v2.windows_runtime.cursor_overlay import ComputerUseCursorOverlayLowLevelSender  # type: ignore  # 新增代码+ComputerUseCursorOverlay: 脚本模式导入橙色鼠标来源叠加层包装器；如果没有这行代码，bat 入口真实鼠标动作无法显示 Computer Use 来源标识。
    from computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # type: ignore  # 新增代码+RealComputerActionExecutor: 脚本模式导入真实低层 sender；如果没有这行代码，bat 入口的真实动作后端没有物理输入实现。
    from computer_use_mcp_v2.windows_runtime.sendinput_dispatcher import WindowsSendInputDispatcher  # type: ignore  # 新增代码+RealComputerActionExecutor: 脚本模式导入通用 dispatcher；如果没有这行代码，bat 入口无法把高层动作展开到底层事件。
    from computer_use_mcp_v2.windows_runtime.sendinput_executor import WindowsSendInputExecutor  # 新增代码+Phase37WindowsSendInputExecutor: 脚本模式下导入 SendInput 执行器；如果没有这行代码，start_oauth_agent.bat 无法加载 Phase37 动作层。
    from computer_use_mcp_v2.windows_runtime.fresh_target_policy import decide_fresh_target_preflight, decide_recovery_after_drift  # type: ignore  # 新增代码+FreshTargetPolicy：脚本模式导入通用新目标策略；如果没有这一行，真实可见终端入口无法阻断旧窗口。
    from computer_use_mcp_v2.windows_runtime.target_lease import WRITE_ACTIONS_REQUIRING_LEASE, build_target_lease, target_lease_from_dict, verify_target_lease_before_action  # type: ignore  # 新增代码+ControllerTargetLease：脚本模式导入通用目标租约 helper；如果没有这一行，真实可见终端入口无法执行 TargetLease 门禁。
    from computer_use_mcp_v2.windows_runtime.target_registry import ComputerUseTargetRegistry  # type: ignore  # 新增代码+TargetRegistryRootRemediation: 脚本模式导入 session 目标窗口注册表；如果没有这一行，bat 入口无法使用 target_ref 修复。
    from computer_use_mcp_v2.windows_runtime.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase28ComputerUse: 脚本模式下导入 Windows inventory probe；如果没有这行代码，bat 入口无法加载 Phase 28 只读窗口枚举。


COMPUTER_USE_OPT_IN_ENV_VAR = "LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE"  # 新增代码+Phase20ComputerUse: 集中保存真实桌面控制的启用环境变量名；如果没有这行代码，状态输出和工厂逻辑可能写出不一致的开关名。
COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR = "LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE"  # 新增代码+Phase28ComputerUse: 集中保存只读窗口观察的启用环境变量名；如果没有这行代码，用户只能为了观察窗口而误开真实鼠标键盘动作。
COMPUTER_USE_NATIVE_OBSERVE_OPT_IN_ENV_VAR = "LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE"  # 新增代码+Phase32WindowsNativeHelper: 集中保存 native 截图/文本只读 helper 开关；如果没有这行代码，只读 inventory 可能被误扩大为读取屏幕内容。
COMPUTER_USE_REAL_LAUNCH_ENV_VAR = "LEARNING_AGENT_PHASE105_ENABLE_FULL_MODE_CONTROLLED_REAL_LAUNCH"  # 新增代码+ModelLoopLaunchAppTool: 集中保存模型主循环 launch_app 真实启动开关；如果没有这行代码，controller 无法把 full 模式授权传给通用目标 session。
def _build_real_windows_action_executor(platform: str | None = None) -> WindowsSendInputExecutor:  # 新增代码+RealComputerActionExecutor: 函数段开始，构造默认真实 Windows 输入执行链；如果没有这段函数，真实后端只能停在 implementation_available=false 的合同层。
    current_platform = platform or sys.platform  # 新增代码+RealComputerActionExecutor: 记录当前平台并允许测试注入；如果没有这行代码，单元测试无法稳定模拟 Windows 路径。
    low_level_sender = WindowsSendInputLowLevelSender(platform=current_platform)  # 新增代码+RealComputerActionExecutor: 创建 Phase58 真实低层 sender；如果没有这行代码，dispatcher 展开事件后没有触达系统鼠标键盘的最后一跳。
    overlay_low_level_sender = ComputerUseCursorOverlayLowLevelSender(low_level_sender, platform=current_platform)  # 新增代码+ComputerUseCursorOverlay: 在真实低层 sender 外包一层橙色鼠标来源标识；如果没有这行代码，用户看不出鼠标动作是否由 Computer Use 内部工具触发。
    dispatcher = WindowsSendInputDispatcher(platform=current_platform, enabled=True, low_level_sender=overlay_low_level_sender)  # 修改代码+ComputerUseCursorOverlay: 把带可视标识的低层 sender 接到 Phase47 dispatcher；如果没有这行代码，标识层会创建但不会进入真实动作链路。
    return WindowsSendInputExecutor(platform=current_platform, enabled=True, sendinput_impl=dispatcher)  # 新增代码+RealComputerActionExecutor: 返回注入 dispatcher 的 Phase37 executor；如果没有这行代码，Windows 后端状态仍会显示 implementation_available=false。
# 新增代码+RealComputerActionExecutor: 函数段结束，_build_real_windows_action_executor 到此结束；如果没有这个边界说明，初学者不容易看出真实输入接线范围。


def _build_default_target_session_runtime(environ: dict[str, str] | None = None) -> Any:  # 新增代码+ModelLoopLaunchAppTool: 函数段开始，构造 launch_app 使用的通用目标 session；如果没有这段函数，controller 会重新发明一套应用启动逻辑。
    source = os.environ if environ is None else environ  # 新增代码+ModelLoopLaunchAppTool: 读取真实环境或测试注入环境；如果没有这行代码，单元测试无法稳定控制真实启动开关。
    real_launch_enabled = str(source.get(COMPUTER_USE_REAL_LAUNCH_ENV_VAR, "")).lower() in {"1", "true", "yes"}  # 新增代码+ModelLoopLaunchAppTool: 判断 full 模式真实启动门是否开启；如果没有这行代码，launch_app 要么永远录制要么永远真实启动。
    try:  # 新增代码+ModelLoopLaunchAppTool: 优先按包模式导入通用目标 session；如果没有这行代码，正常包运行时无法复用 Phase117 目标绑定能力。
        from learning_agent.computer_use_mcp_v2.windows_runtime.universal_target_session import UniversalTargetSessionRuntime  # 新增代码+ModelLoopLaunchAppTool: 读取现有通用 session runtime；如果没有这行代码，controller 会绕开已有防漂移和自有窗口绑定。
    except ModuleNotFoundError as error:  # 新增代码+ModelLoopLaunchAppTool: 兼容 start_oauth_agent.bat 脚本模式包名前缀不同；如果没有这段代码，真实可见终端可能因为导入路径失败。
        if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_target_session"}:  # 新增代码+ModelLoopLaunchAppTool: 只对目标包路径缺失做 fallback；如果没有这行代码，模块内部真实错误会被误吞。
            raise  # 新增代码+ModelLoopLaunchAppTool: 重新抛出非路径类错误；如果没有这行代码，排查启动 runtime bug 会很困难。
        from computer_use_mcp_v2.windows_runtime.universal_target_session import UniversalTargetSessionRuntime  # type: ignore  # 新增代码+ModelLoopLaunchAppTool: 脚本模式导入同一个 runtime；如果没有这行代码，bat 入口无法执行 launch_app。
    return UniversalTargetSessionRuntime(enable_real_launch=bool(real_launch_enabled and sys.platform == "win32"))  # 新增代码+ModelLoopLaunchAppTool: 返回按门禁决定真实/录制的目标 session；如果没有这行代码，模型主循环拿不到应用窗口凭证。
# 新增代码+ModelLoopLaunchAppTool: 函数段结束，_build_default_target_session_runtime 到此结束；如果没有这个边界说明，读者不容易看出 launch_app runtime 构造范围。


@dataclass(frozen=True)  # 新增代码+OSComputerUse: 让动作结果不可变，避免调用方事后改写审计事实；若没有这行代码，结果对象可能被无意污染。
class ComputerUseActionResult:  # 新增代码+OSComputerUse: 定义 Computer Use 动作统一返回结构；若没有这段代码，状态、错误和数据会以散乱字符串传递。
    ok: bool  # 新增代码+OSComputerUse: 表示动作是否成功；若没有这行代码，调用方无法稳定判断成功失败。
    message: str  # 新增代码+OSComputerUse: 保存给模型和用户看的中文说明；若没有这行代码，失败原因会丢失。
    data: dict[str, Any]  # 新增代码+OSComputerUse: 保存结构化附加数据；若没有这行代码，截图摘要、坐标或后端状态无法机器读取。

    def to_text(self, tool_name: str = "mcp__computer-use__computer_batch") -> str:  # 修改代码+ComputerUseMcpV2ResidualCleanup：默认显示 v2 MCP batch 名称；如果没有这行代码，忘记传 tool_name 的调用方会继续把旧 computer_action 暴露到输出文本。
        status = "成功" if self.ok else "失败"  # 新增代码+OSComputerUse: 把布尔状态转换成用户容易理解的中文词；若没有这行代码，输出不够直观。
        base_text = f"{tool_name} {status}：{self.message}\n数据：{self.data}"  # 修改代码+Phase41WindowsImageResults: 先保留原始工具文本；如果没有这行代码，旧调用方会丢失结构化数据回显。
        image_result_lines = format_image_result_lines(collect_image_result_blocks(self.data))  # 新增代码+Phase41WindowsImageResults: 从结果数据中收集并格式化图片块；如果没有这行代码，模型仍要从巨大 dict 里寻找截图路径。
        if image_result_lines:  # 新增代码+Phase41WindowsImageResults: 只有存在图片块时追加图片区；如果没有这行代码，普通动作结果会多出空图片区噪音。
            return base_text + "\n" + "\n".join(image_result_lines)  # 新增代码+Phase41WindowsImageResults: 返回原始结果加稳定图片区；如果没有这行代码，截图 artifact 不会成为模型可见的独立结果块。
        return base_text  # 修改代码+Phase41WindowsImageResults: 无图片块时保持原格式；如果没有这行代码，非截图结果会没有返回值。


class ComputerUseBackend(Protocol):  # 新增代码+OSComputerUse: 定义真实/测试桌面后端必须实现的接口；若没有这段代码，后续接 Windows 后端没有稳定契约。
    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 要求后端报告可用状态；若没有这行代码，状态工具无法知道后端是否能控制桌面。
        ...  # 新增代码+OSComputerUse: Protocol 方法占位；若没有这行代码，接口声明语法不完整。

    def observe(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase27ComputerUse: 要求后端实现只读观察协议；如果没有这行代码，controller 无法在动作前列出或校验窗口。
        ...  # 新增代码+Phase27ComputerUse: Protocol 方法占位；如果没有这行代码，接口声明语法不完整。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+OSComputerUse: 要求后端执行已通过安全检查的动作；若没有这行代码，控制器无法调用真实实现。
        ...  # 新增代码+OSComputerUse: Protocol 方法占位；若没有这行代码，接口声明语法不完整。


class UnavailableComputerUseBackend:  # 新增代码+OSComputerUse: 默认不可用后端，保证未配置时绝不控制真实桌面；若没有这段代码，项目初始化时可能找不到安全默认值。
    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 返回默认后端状态；若没有这段代码，computer_status 无法说明为什么不可用。
        return {"available": False, "backend": "unavailable", "reason": f"未设置 {COMPUTER_USE_OPT_IN_ENV_VAR}=1 或 {COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR}=1，OS Computer Use 默认安全关闭。", "real_actions_enabled": False, "read_only_inventory_enabled": False, "opt_in_env_var": COMPUTER_USE_OPT_IN_ENV_VAR, "observe_opt_in_env_var": COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR, "opt_in_enabled": False, "platform": sys.platform}  # 修改代码+Phase28ComputerUse: 同时说明真实动作开关和只读观察开关；如果没有这行代码，用户不知道如何只启用安全窗口 inventory。

    def observe(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase27ComputerUse: 默认后端拒绝只读桌面观察；如果没有这段代码，未启用时 observe 可能返回误导性空数据。
        return ComputerUseActionResult(False, "OS Computer Use 后端尚未启用，未读取任何真实窗口信息。", {"action": action, "backend": "unavailable", "windows": []})  # 新增代码+Phase27ComputerUse: 返回清楚的未启用观察结果；如果没有这行代码，模型可能误以为桌面没有窗口。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+OSComputerUse: 拒绝所有真实桌面动作；若没有这段代码，默认后端可能意外执行副作用。
        return ComputerUseActionResult(False, "OS Computer Use 后端尚未启用，未执行任何真实桌面操作。", {"action": action, "backend": "unavailable"})  # 新增代码+OSComputerUse: 返回清楚拒绝结果；若没有这行代码，模型可能误以为动作已执行。


class MemoryComputerUseBackend:  # 新增代码+OSComputerUse: 测试专用后端，只记录动作不碰真实桌面；若没有这段代码，自动化测试无法验证成功路径。
    def __init__(self, windows: list[dict[str, Any]] | None = None, window_states: dict[tuple[str, str], dict[str, Any]] | None = None) -> None:  # 修改代码+Phase27ComputerUse: 初始化动作列表和可观察窗口目录；如果没有这段代码，Phase 27 无法测试窗口身份协议。
        self.actions: list[dict[str, Any]] = []  # 新增代码+OSComputerUse: 保存每次动作参数副本；若没有这行代码，测试无法证明动作被传递到后端。
        self.windows: list[dict[str, str]] = []  # 新增代码+Phase27ComputerUse: 保存规范化后的可观察窗口；如果没有这行代码，list_windows 无法返回稳定目标。
        for raw_window in windows or []:  # 新增代码+Phase27ComputerUse: 遍历测试传入的窗口描述；如果没有这行代码，内存后端无法加载已知窗口。
            window_ref = build_window_ref(raw_window)  # 新增代码+Phase27ComputerUse: 把松散窗口 dict 转成强类型引用；如果没有这行代码，窗口身份可能缺少 app_id/window_id。
            if window_ref is not None:  # 新增代码+Phase27ComputerUse: 只保留身份完整的窗口；如果没有这行代码，坏窗口会进入可信目录。
                self.windows.append(window_ref.to_dict())  # 新增代码+Phase27ComputerUse: 保存可序列化窗口引用；如果没有这行代码，observe 结果无法返回窗口列表。
        self.window_states: dict[tuple[str, str], dict[str, Any]] = dict(window_states or {})  # 新增代码+Phase27ComputerUse: 保存可选窗口状态覆盖；如果没有这行代码，测试无法模拟焦点、截图等观察状态。

    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 返回测试后端状态；若没有这段代码，controller.status 无法在测试中表现为可用。
        return {"available": True, "backend": "memory", "reason": "测试后端只记录动作，不控制真实桌面。", "real_actions_enabled": False, "read_only_inventory_enabled": True, "opt_in_env_var": COMPUTER_USE_OPT_IN_ENV_VAR, "observe_opt_in_env_var": COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR, "opt_in_enabled": False, "platform": sys.platform, "evidence_mode": "memory_only", "window_count": len(self.windows)}  # 修改代码+Phase28ComputerUse: 在测试状态里报告只读 inventory 和已知窗口数量；如果没有这行代码，调试时看不出 observe 能力边界。

    def _find_window(self, raw_window: Any) -> dict[str, str] | None:  # 新增代码+Phase27ComputerUse: 在内存窗口目录中查找目标窗口；如果没有这段函数，observe 和 action 校验会重复写匹配逻辑。
        window_ref = build_window_ref(raw_window)  # 新增代码+Phase27ComputerUse: 先把输入转换成强类型窗口引用；如果没有这行代码，缺字段窗口可能进入匹配流程。
        if window_ref is None:  # 新增代码+Phase27ComputerUse: 判断窗口引用是否有效；如果没有这行代码，坏参数会导致身份键生成失败。
            return None  # 新增代码+Phase27ComputerUse: 无效窗口直接返回未找到；如果没有这行代码，调用方无法区分未知和异常。
        target_identity = window_ref_identity(window_ref)  # 新增代码+Phase27ComputerUse: 生成目标窗口身份键；如果没有这行代码，匹配逻辑会散落重复。
        for known_window in self.windows:  # 新增代码+Phase27ComputerUse: 遍历已知窗口目录；如果没有这行代码，后端无法判断目标是否可信。
            known_ref = build_window_ref(known_window)  # 新增代码+Phase27ComputerUse: 把目录项转换为窗口引用；如果没有这行代码，目录项字段变化会影响匹配。
            if known_ref is not None and window_ref_identity(known_ref) == target_identity:  # 新增代码+Phase27ComputerUse: 比较 app_id/window_id 是否完全一致；如果没有这行代码，伪造标题可能绕过校验。
                return dict(known_window)  # 新增代码+Phase27ComputerUse: 返回窗口副本避免外部修改目录；如果没有这行代码，调用方可能污染内存后端状态。
        return None  # 新增代码+Phase27ComputerUse: 没找到时返回 None；如果没有这行代码，未知窗口无法被明确拒绝。

    def observe(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase27ComputerUse: 实现内存后端只读观察协议；如果没有这段代码，Phase 27 无法验证 observe/action 分离。
        if action == "list_windows":  # 新增代码+Phase27ComputerUse: 处理列出窗口动作；如果没有这行代码，模型无法发现可控制目标。
            return ComputerUseActionResult(True, "测试后端已返回已知窗口列表。", {"action": action, "backend": "memory", "windows": [dict(window) for window in self.windows]})  # 新增代码+Phase27ComputerUse: 返回窗口列表副本；如果没有这行代码，调用方无法拿到可信窗口引用。
        if action == "list_apps":  # 新增代码+Phase27ComputerUse: 处理列出应用动作；如果没有这行代码，模型无法先按应用粗略选择目标。
            app_ids = sorted({window["app_id"] for window in self.windows})  # 新增代码+Phase27ComputerUse: 从窗口目录提取应用身份；如果没有这行代码，应用列表无法生成。
            apps = [{"app_id": app_id, "window_count": sum(1 for window in self.windows if window["app_id"] == app_id)} for app_id in app_ids]  # 新增代码+Phase27ComputerUse: 生成应用和窗口数量摘要；如果没有这行代码，模型不知道每个应用有几个窗口。
            return ComputerUseActionResult(True, "测试后端已返回应用列表。", {"action": action, "backend": "memory", "apps": apps})  # 新增代码+Phase27ComputerUse: 返回应用观察结果；如果没有这行代码，list_apps 没有输出。
        if action == "get_active_window":  # 新增代码+Phase27ComputerUse: 处理活动窗口查询；如果没有这行代码，模型无法知道当前默认焦点目标。
            active_window = dict(self.windows[0]) if self.windows else None  # 新增代码+Phase27ComputerUse: 在测试后端用第一个窗口模拟活动窗口；如果没有这行代码，活动窗口观察没有确定行为。
            return ComputerUseActionResult(active_window is not None, "测试后端已返回活动窗口。" if active_window else "测试后端没有已知活动窗口。", {"action": action, "backend": "memory", "window": active_window})  # 新增代码+Phase27ComputerUse: 返回活动窗口或空结果；如果没有这行代码，调用方无法判断是否有焦点窗口。
        if action == "get_window_state":  # 新增代码+Phase27ComputerUse: 处理指定窗口状态查询；如果没有这行代码，动作前无法验证目标窗口仍存在。
            known_window = self._find_window(arguments.get("window"))  # 新增代码+Phase27ComputerUse: 查找传入窗口是否在可信目录；如果没有这行代码，未知窗口会被当作可观察。
            if known_window is None:  # 新增代码+Phase27ComputerUse: 判断窗口是否未知；如果没有这行代码，未知窗口不会被拒绝。
                return ComputerUseActionResult(False, "未知窗口：请先调用 mcp__computer-use__observe 获取可信 window 引用。", {"action": action, "backend": "memory"})  # 修改代码+McpObservedWindowFix: 返回 v2 工具面未知窗口错误；如果没有这行代码，模型会被隐藏旧观察接口名称引回不可见接口。
            known_ref = build_window_ref(known_window)  # 新增代码+Phase27ComputerUse: 把已知窗口转换成引用对象；如果没有这行代码，状态覆盖无法生成身份键。
            state = dict(self.window_states.get(window_ref_identity(known_ref), {})) if known_ref is not None else {}  # 新增代码+Phase27ComputerUse: 读取测试注入的窗口状态；如果没有这行代码，状态观察无法携带模拟证据。
            state.setdefault("window", known_window)  # 新增代码+Phase27ComputerUse: 确保状态里包含窗口引用；如果没有这行代码，调用方拿不到当前状态对应的窗口。
            state.setdefault("screenshot_id", "")  # 新增代码+Phase27ComputerUse: 提供截图证据占位；如果没有这行代码，后续真实截图字段没有稳定位置。
            state.setdefault("accessibility_excerpt", "")  # 新增代码+Phase27ComputerUse: 提供可访问性摘要占位；如果没有这行代码，后续 UIA 文本没有稳定位置。
            return ComputerUseActionResult(True, "测试后端已返回窗口状态。", {"action": action, "backend": "memory", "state": state})  # 新增代码+Phase27ComputerUse: 返回窗口状态结果；如果没有这行代码，get_window_state 没有成功输出。
        return ComputerUseActionResult(False, f"测试后端暂不支持观察动作：{action}", {"action": action, "backend": "memory"})  # 新增代码+Phase27ComputerUse: 拒绝未知观察动作；如果没有这行代码，observe 错误会静默失败。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+OSComputerUse: 记录已确认动作；若没有这段代码，成功路径没有可验证行为。
        payload = redact_action_arguments(action, arguments)  # 修改代码+Phase30ComputerUseActionGate: 保存脱敏后的动作参数副本；若没有这行代码，内存后端测试日志可能保存原始密码或 token。
        self.actions.append(payload)  # 修改代码+Phase30ComputerUseActionGate: 保存脱敏动作记录；若没有这行代码，测试和审计无法追踪执行历史且不能证明文本已被清理。
        data = {"action": action, "backend": "memory", "count": len(self.actions)}  # 修改代码+Phase20ComputerUse: 先准备可扩展的成功数据字典；如果没有这行代码，截图证据字段难以按动作类型追加。
        if action == "screenshot":  # 新增代码+Phase20ComputerUse: 只为截图动作补充证据摘要；如果没有这行代码，验收无法证明这次动作属于屏幕观察。
            data["evidence"] = {"kind": "screenshot", "backend": "memory", "captured": False, "reason": "内存后端只记录截图请求，不读取真实屏幕。"}  # 新增代码+Phase20ComputerUse: 明确测试截图没有触碰真实桌面；如果没有这行代码，用户可能把内存证据误认为真实截图文件。
        return ComputerUseActionResult(True, f"测试后端已记录动作：{action}", data)  # 修改代码+Phase20ComputerUse: 返回包含可选证据字段的成功结果；如果没有这行代码，调用方不知道后端是否收到动作。


class WindowsComputerUseBackend:  # 新增代码+Phase8ProductionEdges: 提供显式启用后的 Windows OS 控制后端；如果没有这段代码，Computer Use 只能停留在占位状态。
    def __init__(self, inventory: Any | None = None, real_actions_enabled: bool = True, evidence_store: Any | None = None, observation_helper: Any | None = None, action_executor: Any | None = None) -> None:  # 修改代码+Phase37WindowsSendInputExecutor: 初始化 Windows 后端并允许注入 SendInput 执行器；如果没有这段代码，后端无法用安全合同替代旧 mouse_event 路径。
        self.inventory = inventory or WindowsWindowInventoryProbe()  # 新增代码+Phase28ComputerUse: 保存真实或静态窗口 inventory；如果没有这行代码，observe 无法读取窗口快照。
        self.real_actions_enabled = real_actions_enabled  # 新增代码+Phase28ComputerUse: 保存真实动作是否启用；如果没有这行代码，只读模式无法阻止 click/move_mouse。
        self.evidence_store = evidence_store or ComputerUseEvidenceStore()  # 新增代码+Phase29ComputerUse: 保存窗口状态证据仓库；如果没有这行代码，截图和 metadata 没有落盘位置。
        self.observation_helper = observation_helper or NullWindowObservationHelper()  # 新增代码+Phase29ComputerUse: 保存截图/UIA helper；如果没有这行代码，未配置 helper 时 get_window_state 会崩溃。
        self.action_executor = action_executor or WindowsSendInputExecutor(enabled=real_actions_enabled)  # 新增代码+Phase37WindowsSendInputExecutor: 保存 SendInput 动作执行器且默认真实实现为空；如果没有这行代码，真实动作仍会走旧 Win32 mouse_event 分支。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase8ProductionEdges: 返回 Windows 后端状态；如果没有这段代码，用户无法确认真实后端是否启用。
        inventory_status = self.inventory.status() if hasattr(self.inventory, "status") else {}  # 新增代码+Phase28ComputerUse: 读取 inventory 状态；如果没有这行代码，状态无法说明 helper 或平台边界。
        evidence_status = self.evidence_store.status() if hasattr(self.evidence_store, "status") else {}  # 新增代码+Phase29ComputerUse: 读取证据仓库状态；如果没有这行代码，status 无法告诉用户 evidence 保存目录。
        helper_status = self.observation_helper.status() if hasattr(self.observation_helper, "status") else {}  # 新增代码+Phase29ComputerUse: 读取观察 helper 状态；如果没有这行代码，status 无法说明截图/UIA 能力边界。
        native_observation_diagnostics = helper_status.get("diagnostics", {}) if isinstance(helper_status, dict) else {}  # 新增代码+Phase33WindowsNativeDiagnostics: 提取 helper 诊断对象；如果没有这行代码，backend.status 无法把 WGC/UIA 缺口透传给 /computer。
        action_executor_status = self.action_executor.status() if hasattr(self.action_executor, "status") else {}  # 新增代码+Phase37WindowsSendInputExecutor: 读取 SendInput 执行器状态；如果没有这行代码，用户无法看出真实动作层是否仍缺实现。
        status = {"available": sys.platform == "win32" or bool(inventory_status.get("available")), "backend": "windows_ctypes", "reason": "Windows 后端已启用只读窗口 inventory 和窗口状态证据落盘；真实鼠标键盘动作现在通过 Phase37 SendInput 执行器合同控制。", "real_actions_enabled": bool(self.real_actions_enabled and sys.platform == "win32"), "read_only_inventory_enabled": True, "opt_in_env_var": COMPUTER_USE_OPT_IN_ENV_VAR, "observe_opt_in_env_var": COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR, "opt_in_enabled": bool(self.real_actions_enabled), "platform": sys.platform, "evidence_mode": evidence_status.get("evidence_mode", "window_state_artifact"), "evidence_root": evidence_status.get("evidence_root", ""), "inventory_source": inventory_status.get("source", ""), "observation_helper": helper_status.get("helper", ""), "observation_helper_available": bool(helper_status.get("available", False)), "observation_helper_reason": str(helper_status.get("reason", "")), "native_observation_diagnostics": native_observation_diagnostics, "native_helper_available": bool(inventory_status.get("native_helper_available", False)), "native_helper_reason": str(inventory_status.get("native_helper_reason", "Phase 28 只读 inventory 已接入；完整 helper 尚未接入。")), "action_executor_backend": action_executor_status.get("backend", ""), "action_executor": action_executor_status}  # 修改代码+Phase43WindowsNativeCapabilityMatrix: 先构造 Windows 后端状态字典；如果没有这行代码，Phase43 无法在同一事实源上追加能力矩阵。
        status["native_capability_matrix"] = build_phase43_native_capability_matrix(status)  # 新增代码+Phase43WindowsNativeCapabilityMatrix: 把 WGC/UIA/SendInput/evidence 能力矩阵加入后端状态；如果没有这行代码，computer_status 看不到统一可用/启用/下一步矩阵。
        return status  # 修改代码+Phase43WindowsNativeCapabilityMatrix: 返回带 Phase43 能力矩阵的状态；如果没有这行代码，调用方拿不到 status 结果。

    def observe(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase27ComputerUse: 提供 Windows 后端只读观察占位；如果没有这段代码，控制器无法统一调用 observe 协议。
        snapshot = self.inventory.snapshot()  # 新增代码+Phase28ComputerUse: 获取只读窗口快照；如果没有这行代码，list_windows/list_apps/get_window_state 没有数据来源。
        base_data = {"action": action, "backend": "windows_ctypes", "platform": sys.platform, "captured_at": snapshot.captured_at, "source": snapshot.source, "filtered_count": snapshot.filtered_count}  # 新增代码+Phase28ComputerUse: 准备通用观察元数据；如果没有这行代码，每个 observe 分支会重复拼接字段。
        if action == "list_windows":  # 新增代码+Phase28ComputerUse: 处理只读窗口列表；如果没有这行代码，模型无法发现可观察窗口。
            data = dict(base_data)  # 新增代码+Phase28ComputerUse: 复制通用数据避免污染其他分支；如果没有这行代码，分支会共享可变对象。
            data["windows"] = [dict(window) for window in snapshot.windows]  # 新增代码+Phase28ComputerUse: 返回安全窗口列表副本；如果没有这行代码，调用方无法拿到窗口引用。
            return ComputerUseActionResult(True, "Windows 只读窗口列表已返回。", data)  # 新增代码+Phase28ComputerUse: 返回 list_windows 成功结果；如果没有这行代码，观察工具没有输出。
        if action == "list_apps":  # 新增代码+Phase28ComputerUse: 处理只读应用列表；如果没有这行代码，模型无法按应用选择窗口。
            data = dict(base_data)  # 新增代码+Phase28ComputerUse: 复制通用数据；如果没有这行代码，apps 分支会污染基础数据。
            data["apps"] = snapshot.apps()  # 新增代码+Phase28ComputerUse: 返回应用分组摘要；如果没有这行代码，list_apps 没有结果。
            return ComputerUseActionResult(True, "Windows 只读应用列表已返回。", data)  # 新增代码+Phase28ComputerUse: 返回 list_apps 成功结果；如果没有这行代码，工具调用无法完成。
        if action == "get_active_window":  # 新增代码+Phase28ComputerUse: 处理活动窗口查询；如果没有这行代码，模型无法知道当前安全活动窗口。
            data = dict(base_data)  # 新增代码+Phase28ComputerUse: 复制通用数据；如果没有这行代码，活动窗口分支会共享可变对象。
            data["window"] = dict(snapshot.active_window) if snapshot.active_window else None  # 新增代码+Phase28ComputerUse: 返回活动窗口副本或 None；如果没有这行代码，调用方无法判断当前焦点。
            return ComputerUseActionResult(snapshot.active_window is not None, "Windows 活动窗口已返回。" if snapshot.active_window else "未找到安全活动窗口。", data)  # 新增代码+Phase28ComputerUse: 返回活动窗口结果；如果没有这行代码，get_active_window 没有统一反馈。
        if action == "get_window_state":  # 新增代码+Phase28ComputerUse: 处理窗口状态查询；如果没有这行代码，动作前无法读取窗口相对几何。
            known_window = snapshot.find_window(arguments.get("window"))  # 新增代码+Phase28ComputerUse: 验证请求窗口是否在快照里；如果没有这行代码，模型可能查询伪造窗口。
            if known_window is None:  # 新增代码+Phase28ComputerUse: 判断窗口是否未知；如果没有这行代码，未知窗口会被当作可观察。
                return ComputerUseActionResult(False, "未知窗口：请先调用 mcp__computer-use__observe 获取可信 window 引用。", base_data)  # 修改代码+McpObservedWindowFix: 返回 v2 工具面未知窗口错误；如果没有这行代码，模型会被隐藏旧观察接口名称引回不可见接口。
            rect = dict(known_window.get("rect", {}))  # 新增代码+Phase28ComputerUse: 读取窗口矩形；如果没有这行代码，状态无法计算截图尺寸。
            width = max(0, int(rect.get("right", 0)) - int(rect.get("left", 0)))  # 新增代码+Phase28ComputerUse: 计算窗口宽度；如果没有这行代码，截图占位尺寸会缺失。
            height = max(0, int(rect.get("bottom", 0)) - int(rect.get("top", 0)))  # 新增代码+Phase28ComputerUse: 计算窗口高度；如果没有这行代码，窗口相对坐标无法判断边界。
            payload = self.observation_helper.observe_window(known_window)  # 新增代码+Phase29ComputerUse: 调用截图/UIA helper 获取窗口观察 payload；如果没有这行代码，get_window_state 仍停留在 Phase 28 占位。
            evidence = self.evidence_store.save_window_state(window=known_window, payload=payload, fallback_width=width, fallback_height=height)  # 新增代码+Phase29ComputerUse: 保存截图和 UIA metadata artifact；如果没有这行代码，窗口状态没有可审计证据文件。
            state = {"window": known_window, "screenshot_id": evidence["screenshot_id"], "screenshot_path": evidence["screenshot_path"], "screenshot_captured": evidence["screenshot_captured"], "screenshot_width": evidence["screenshot_width"], "screenshot_height": evidence["screenshot_height"], "screenshot_origin": {"x": int(rect.get("left", 0)), "y": int(rect.get("top", 0))}, "accessibility_excerpt": evidence["accessibility_excerpt"], "accessibility_truncated": evidence["accessibility_truncated"], "accessibility_filtered_line_count": evidence["accessibility_filtered_line_count"], "focused_element": evidence["focused_element"], "selected_text_preview": evidence["selected_text_preview"], "document_text_preview": evidence["document_text_preview"], "evidence_id": evidence["evidence_id"], "evidence_path": evidence["evidence_path"], "helper_name": evidence["helper_name"], "helper_available": evidence["helper_available"], "helper_reason": evidence["helper_reason"]}  # 修改代码+Phase29ComputerUse: 返回带 evidence 文件和 bounded UIA 摘要的窗口状态；如果没有这行代码，模型无法审计截图和文本来源。
            state["image_results"] = list(evidence.get("image_results", []))  # 新增代码+Phase41WindowsImageResults: 把 evidence 图片块同步进窗口状态；如果没有这行代码，调用方必须重新扫描底层 evidence。
            state["image_result_count"] = int(evidence.get("image_result_count", 0) or 0)  # 新增代码+Phase41WindowsImageResults: 把图片块数量同步进状态；如果没有这行代码，终端无法快速确认截图数量。
            try:  # 新增代码+Phase39WindowsCoordinates: 在窗口状态分支内导入坐标模型，避免影响其它 Computer Use 入口；如果没有这行代码，状态输出无法补充 DPI 和多显示器上下文。
                from learning_agent.computer_use_mcp_v2.windows_runtime.coordinates import build_coordinate_context  # 新增代码+Phase39WindowsCoordinates: 包模式导入坐标换算函数；如果没有这行代码，get_window_state 无法计算 coordinate_context。
            except ModuleNotFoundError as error:  # 新增代码+Phase39WindowsCoordinates: 捕获 start_oauth_agent 脚本模式下包名前缀不可用；如果没有这行代码，真实终端入口可能导入失败。
                if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.coordinates"}:  # 新增代码+Phase39WindowsCoordinates: 只允许目标包路径缺失时 fallback；如果没有这行代码，坐标模块内部 bug 会被误吞。
                    raise  # 新增代码+Phase39WindowsCoordinates: 重新抛出非路径类导入错误；如果没有这行代码，排查真实错误会很困难。
                from computer_use_mcp_v2.windows_runtime.coordinates import build_coordinate_context  # 新增代码+Phase39WindowsCoordinates: 脚本模式导入坐标换算函数；如果没有这行代码，bat 入口无法返回 Phase39 状态字段。
            coordinate_context = build_coordinate_context(known_window, 0, 0)  # 新增代码+Phase39WindowsCoordinates: 以窗口左上角为基准生成状态坐标上下文；如果没有这行代码，截图原点和动作坐标没有统一解释。
            state["coordinate_context"] = coordinate_context  # 新增代码+Phase39WindowsCoordinates: 把完整坐标上下文放进 state；如果没有这行代码，模型无法看到窗口逻辑/物理边界。
            state["coordinate_model"] = coordinate_context.get("model", "")  # 新增代码+Phase39WindowsCoordinates: 在 state 中暴露模型名；如果没有这行代码，终端输出不容易确认 Phase39 是否生效。
            state["dpi_scale"] = dict(coordinate_context.get("dpi_scale", {}))  # 新增代码+Phase39WindowsCoordinates: 在 state 中暴露 DPI 缩放；如果没有这行代码，高 DPI 问题排查需要打开深层对象。
            state["window_logical_rect"] = dict(coordinate_context.get("window_logical_rect", {}))  # 新增代码+Phase39WindowsCoordinates: 在 state 中暴露窗口逻辑矩形；如果没有这行代码，截图边界只能从旧 rect 间接推导。
            state["window_physical_rect"] = dict(coordinate_context.get("window_physical_rect", {}))  # 新增代码+Phase39WindowsCoordinates: 在 state 中暴露窗口物理矩形；如果没有这行代码，真实像素边界无法直接审计。
            data = dict(base_data)  # 新增代码+Phase28ComputerUse: 复制通用数据；如果没有这行代码，状态分支会污染基础对象。
            data["state"] = state  # 新增代码+Phase28ComputerUse: 写入窗口状态；如果没有这行代码，调用方拿不到状态主体。
            data["image_results"] = list(state.get("image_results", []))  # 新增代码+Phase41WindowsImageResults: 在顶层同步图片块；如果没有这行代码，模型和验收脚本需要深入 state 才能找到截图。
            data["image_result_count"] = int(state.get("image_result_count", 0) or 0)  # 新增代码+Phase41WindowsImageResults: 在顶层同步图片数量；如果没有这行代码，终端状态无法直接显示图片结果数。
            data["coordinate_context"] = coordinate_context  # 新增代码+Phase39WindowsCoordinates: 顶层同步坐标上下文，方便测试和终端状态读取；如果没有这行代码，调用方必须深入 state 查找。
            data["coordinate_model"] = coordinate_context.get("model", "")  # 新增代码+Phase39WindowsCoordinates: 顶层同步坐标模型名；如果没有这行代码，验收脚本不容易快速断言 Phase39 生效。
            data["dpi_scale"] = dict(coordinate_context.get("dpi_scale", {}))  # 新增代码+Phase39WindowsCoordinates: 顶层同步 DPI 缩放；如果没有这行代码，终端状态无法直观看到缩放信息。
            return ComputerUseActionResult(True, "Windows 只读窗口状态已返回。", data)  # 新增代码+Phase28ComputerUse: 返回窗口状态成功结果；如果没有这行代码，get_window_state 没有反馈。
        return ComputerUseActionResult(False, f"Windows 后端暂不支持观察动作：{action}", base_data)  # 新增代码+Phase28ComputerUse: 拒绝未知观察动作；如果没有这行代码，observe 错误可能静默失败。

    def execute(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase8ProductionEdges: 执行已通过控制器确认的 Windows 动作；如果没有这段代码，真实后端无法接收动作。
        if not self.real_actions_enabled:  # 新增代码+Phase28ComputerUse: 只读 inventory 模式拒绝所有真实动作；如果没有这行代码，为了观察窗口可能误触发鼠标键盘。
            return ComputerUseActionResult(False, "Windows Computer Use 当前是只读 inventory 模式，不执行鼠标、键盘或窗口动作。", {"backend": "windows_ctypes", "action": action, "read_only_inventory_enabled": True})  # 新增代码+Phase28ComputerUse: 返回只读拒绝结果；如果没有这行代码，模型不知道动作为什么被拒绝。
        if sys.platform != "win32":  # 新增代码+Phase8ProductionEdges: 非 Windows 平台直接拒绝；如果没有这行代码，调用 Win32 API 会崩溃。
            return ComputerUseActionResult(False, "Windows Computer Use 后端只能在 Windows 上执行。", {"backend": "windows_ctypes", "platform": sys.platform})  # 新增代码+Phase8ProductionEdges: 返回清楚的平台拒绝信息；如果没有这行代码，用户只能看到底层异常。
        if action == "screenshot":  # 新增代码+Phase8ProductionEdges: 处理屏幕观察动作；如果没有这行代码，OS 后端没有基础显示器信息入口。
            import ctypes  # 修改代码+Phase37WindowsSendInputExecutor: 仅为屏幕尺寸占位延迟导入 ctypes；如果没有这行代码，screenshot 仍拿不到主屏幕尺寸。
            user32 = ctypes.windll.user32  # 修改代码+Phase37WindowsSendInputExecutor: 仅在截图尺寸分支获取 user32；如果没有这行代码，尺寸读取没有系统入口。
            width = int(user32.GetSystemMetrics(0))  # 新增代码+Phase8ProductionEdges: 读取主屏幕宽度；如果没有这行代码，截图状态缺少尺寸证据。
            height = int(user32.GetSystemMetrics(1))  # 新增代码+Phase8ProductionEdges: 读取主屏幕高度；如果没有这行代码，截图状态缺少尺寸证据。
            return ComputerUseActionResult(True, "Windows 屏幕尺寸已读取；完整截图文件保存将在后续阶段接入。", {"backend": "windows_ctypes", "action": action, "width": width, "height": height, "evidence": {"kind": "screenshot", "backend": "windows_ctypes", "captured": False, "width": width, "height": height, "reason": "Phase 20 只记录屏幕尺寸证据，尚不保存完整截图文件。"}})  # 修改代码+Phase20ComputerUse: 返回可审计屏幕尺寸和截图证据边界；如果没有这行代码，观察动作没有可追踪证据。
        executor_result = self.action_executor.execute(action, dict(arguments))  # 新增代码+Phase37WindowsSendInputExecutor: 把鼠标键盘动作交给 SendInput 执行器；如果没有这行代码，后端仍会使用旧 mouse_event 路径或继续缺动作。
        return ComputerUseActionResult(executor_result.ok, executor_result.message, dict(executor_result.data))  # 新增代码+Phase37WindowsSendInputExecutor: 把执行器结果转换为控制器统一结果；如果没有这行代码，ComputerUseController 无法附加 audit/evidence。


def build_default_computer_use_backend(environ: dict[str, str] | None = None) -> ComputerUseBackend:  # 新增代码+Phase8ProductionEdges: 集中决定默认 Computer Use 后端；如果没有这段代码，启用真实桌面控制的策略会散落在各处。
    source = os.environ if environ is None else environ  # 新增代码+Phase8ProductionEdges: 支持测试传入假环境；如果没有这行代码，测试会污染真实环境变量。
    enabled = str(source.get(COMPUTER_USE_OPT_IN_ENV_VAR, "")).lower() in {"1", "true", "yes"}  # 修改代码+Phase20ComputerUse: 使用统一常量读取真实桌面控制开关；如果没有这行代码，状态提示和实际开关可能不一致。
    observe_enabled = str(source.get(COMPUTER_USE_OBSERVE_OPT_IN_ENV_VAR, "")).lower() in {"1", "true", "yes"}  # 新增代码+Phase28ComputerUse: 读取只读窗口观察开关；如果没有这行代码，用户无法只启用安全 inventory。
    native_observe_enabled = str(source.get(COMPUTER_USE_NATIVE_OBSERVE_OPT_IN_ENV_VAR, "")).lower() in {"1", "true", "yes"}  # 新增代码+Phase32WindowsNativeHelper: 读取 native 截图/文本只读 helper 开关；如果没有这行代码，只读 inventory 会和真实屏幕读取边界混在一起。
    observation_helper = WindowsNativeWindowObservationHelper() if native_observe_enabled and sys.platform == "win32" else None  # 新增代码+Phase32WindowsNativeHelper: 仅在显式 opt-in 且 Windows 时创建 native helper；如果没有这行代码，用户无法安全区分枚举窗口和读取屏幕内容。
    if enabled and sys.platform == "win32":  # 新增代码+Phase8ProductionEdges: 同时满足启用和 Windows 才返回真实后端；如果没有这行代码，非 Windows 会误入 Windows API。
        action_executor = _build_real_windows_action_executor(sys.platform)  # 新增代码+RealComputerActionExecutor: 为默认真实后端创建 Phase37->Phase47->Phase58 输入链；如果没有这行代码，真实终端会继续显示 implementation_available=false。
        return WindowsComputerUseBackend(real_actions_enabled=True, observation_helper=observation_helper, action_executor=action_executor)  # 修改代码+RealComputerActionExecutor: 返回已注入真实动作执行器的 Windows 后端；如果没有这行代码，模型调用 computer_action 仍无法真正发送鼠标键盘。
    if observe_enabled and sys.platform == "win32":  # 新增代码+Phase28ComputerUse: 只读观察开关开启且平台是 Windows 时返回只读后端；如果没有这行代码，用户只能通过高风险动作开关观察窗口。
        return WindowsComputerUseBackend(real_actions_enabled=False, observation_helper=observation_helper)  # 修改代码+Phase32WindowsNativeHelper: 返回只读后端并仅在 native opt-in 时挂载 helper；如果没有这行代码，/computer observe 无法安全启用截图/文本证据。
    return UnavailableComputerUseBackend()  # 新增代码+Phase8ProductionEdges: 默认安全关闭；如果没有这行代码，未配置时没有安全兜底。


class ComputerUseController:  # 新增代码+OSComputerUse: 在 agent 和后端之间提供安全控制层；若没有这段代码，真实桌面操作缺少统一确认和参数校验。
    ALLOWED_ACTIONS: set[str] = {"screenshot", "launch_app", "move_mouse", "click", "double_click", "triple_click", "mouse_down", "mouse_up", "drag_path", "type_text", "press_key", "hold_key", "scroll"}  # 修改代码+ClaudeCodeParity: 允许 session adapter 新增 parity action 通过真实 v2 controller；如果没有这行代码，adapter 映射会在 allowed_actions 门禁处被拒绝。
    OBSERVE_ACTIONS: set[str] = {"list_apps", "list_windows", "get_active_window", "get_window_state"}  # 新增代码+Phase27ComputerUse: 限定只读观察动作集合；如果没有这行代码，observe 可能被滥用成任意桌面命令。
    MAX_TEXT_LENGTH: int = 2000  # 新增代码+OSComputerUse: 限制一次输入文本长度；若没有这行代码，模型可能一次性向桌面注入过长文本。

    def __init__(self, backend: ComputerUseBackend | None = None, lock_manager: ComputerUseLockManager | None = None, owner_session_id: str = "learning-agent-default-session", auto_acquire_lock: bool | None = None, audit_store: ComputerUseAuditStore | None = None, approval_model: Any | None = None, target_session_runtime: Any | None = None) -> None:  # 修改代码+ModelLoopLaunchAppTool: 初始化控制器并允许注入通用目标 session；如果没有这个参数，launch_app 单测和生产路由会被迫走旁路。
        self.backend = backend or build_default_computer_use_backend()  # 修改代码+Phase8ProductionEdges: 通过工厂选择默认安全关闭或显式启用的 Windows 后端；如果没有这行代码，真实后端无法受环境变量控制。
        self.lock_manager = lock_manager if lock_manager is not None else (ComputerUseLockManager() if backend is None else None)  # 新增代码+Phase30ComputerUseActionGate: 生产默认启用 durable lock，注入测试后端时保持旧兼容；如果没有这行代码，真实 agent 默认动作没有当前锁门禁。
        self.owner_session_id = str(owner_session_id or "learning-agent-default-session")  # 新增代码+Phase30ComputerUseActionGate: 保存当前控制器会话 id；如果没有这行代码，锁管理器无法判断谁在请求桌面控制。
        self.auto_acquire_lock = bool(auto_acquire_lock) if auto_acquire_lock is not None else bool(backend is None and lock_manager is None)  # 新增代码+Phase30ComputerUseActionGate: 默认生产路径可在无人持锁时自动获取锁，测试注入路径保持手动；如果没有这行代码，真实 agent 可能永远卡在缺锁。
        self.audit_store = audit_store if audit_store is not None else (ComputerUseAuditStore() if backend is None else None)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 生产默认启用落盘审计而测试注入后端默认不写磁盘；如果没有这行代码，真实动作无法形成长期证据链。
        self.approval_model = approval_model  # 新增代码+Phase38WindowsComputerApproval: 保存可选审批模型；如果没有这行代码，注入的 session allowlist 不会参与动作门禁。
        self.target_session_runtime = target_session_runtime  # 新增代码+ModelLoopLaunchAppTool: 保存可选通用目标 session runtime；如果没有这行代码，launch_app 无法复用已有启动和自有窗口绑定能力。
        self.target_registry = ComputerUseTargetRegistry(session_id=self.owner_session_id)  # 新增代码+TargetRegistryRootRemediation: 创建 session 目标窗口注册表；如果没有这一行，launch_app 后仍只能让模型复制原始 target_window。
        self.active_agent_owned_target_window: dict[str, Any] = {}  # 新增代码+ModelLoopLaunchAppTool: 保存最近 launch_app 绑定的 agent-owned 窗口；如果没有这行代码，后续动作可能漂移回用户旧窗口。
        self.active_target_lease: dict[str, Any] = {}  # 新增代码+ControllerTargetLease：保存最近 launch_app 生成的通用目标租约；如果没有这一行，显式 window 写动作无法和当前会话权限绑定。
        self.audit_log: list[dict[str, Any]] = []  # 新增代码+Phase20ComputerUse: 保存本控制器生命周期里的桌面动作审计事件；如果没有这行代码，被拒绝或执行过的动作无法在状态里复盘。

    def status(self) -> dict[str, Any]:  # 新增代码+OSComputerUse: 返回 Computer Use 当前状态；若没有这段代码，computer_status 工具没有实现来源。
        backend_status = self.backend.status()  # 新增代码+OSComputerUse: 向后端读取状态；若没有这行代码，状态输出无法反映真实后端。
        audit_status = {"event_count": len(self.audit_log), "last_event": dict(self.audit_log[-1]) if self.audit_log else None, "store": self.audit_store.status() if self.audit_store is not None else {"enabled": False, "reason": "测试注入后端未配置落盘审计。"}}  # 修改代码+Phase31ComputerUseLockAbortEvidence: 汇总内存审计和可选落盘位置；如果没有这行代码，用户看不到 evidence chain 保存在哪里。
        lock_status = self.lock_manager.status() if self.lock_manager is not None else {"enabled": False, "reason": "测试注入后端未配置 durable lock。"}  # 新增代码+Phase30ComputerUseActionGate: 读取锁状态或说明未启用；如果没有这行代码，用户看不到当前锁/abort 边界。
        approval_status = self.approval_model.status() if self.approval_model is not None and hasattr(self.approval_model, "status") else {"enabled": False, "reason": "未配置 Phase38 approval 模型。"}  # 新增代码+Phase38WindowsComputerApproval: 读取审批模型状态或说明未启用；如果没有这行代码，用户无法知道当前动作是否受 session allowlist 保护。
        return {"tool": "computer_use", "actions": sorted(self.ALLOWED_ACTIONS), "observe_actions": sorted(self.OBSERVE_ACTIONS), "backend": backend_status, "audit": audit_status, "lock": lock_status, "approval": approval_status, "target_registry": self.target_registry.snapshot(), "active_target_lease": dict(self.active_target_lease), "owner_session_id": self.owner_session_id, "auto_acquire_lock": self.auto_acquire_lock}  # 修改代码+ControllerTargetLease：返回写动作、只读观察、后端、审计、锁、approval、target registry、当前租约和自动取锁策略；如果没有这一行，模型无法区分当前 target_ref 是否持有有效租约。

    def clear_target_leases(self) -> dict[str, Any]:  # 新增代码+TargetLeaseCleanup：函数段开始，清空 controller 当前目标租约和 registry；如果没有这段函数，回合结束后旧窗口租约可能继续影响下一轮。
        self.active_agent_owned_target_window = {}  # 新增代码+TargetLeaseCleanup：清空 agent-owned 窗口基准；如果没有这一行，旧窗口漂移门禁会污染新任务。
        self.active_target_lease = {}  # 新增代码+TargetLeaseCleanup：清空 active TargetLease；如果没有这一行，显式 window 路径可能继续使用过期权限。
        return self.target_registry.clear()  # 新增代码+TargetLeaseCleanup：委托 registry 清空所有 target_ref；如果没有这一行，旧 target_ref 仍可解析到旧窗口。
    # 新增代码+TargetLeaseCleanup：函数段结束，clear_target_leases 到此结束；如果没有这个边界说明，读者不容易看出 controller cleanup 范围。

    def _record_audit(self, action: str, allowed: bool, reason: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase20ComputerUse: 记录一次桌面动作安全判断；如果没有这段函数，拒绝和执行结果无法获得统一审计 id。
        backend_status = self.backend.status()  # 新增代码+Phase20ComputerUse: 读取后端名称写入审计事件；如果没有这行代码，事后不知道动作由哪个后端处理。
        safe_arguments = redact_action_arguments(action, arguments)  # 新增代码+Phase30ComputerUseActionGate: 先把审计参数脱敏；如果没有这行代码，原始 text 可能进入 audit_log。
        event = {"audit_id": f"computer-audit-{len(self.audit_log) + 1}", "action": action, "allowed": allowed, "reason": reason, "backend": backend_status.get("backend"), "has_coordinates": "x" in safe_arguments or "y" in safe_arguments, "text_length": int(safe_arguments.get("text_length", 0)), "text_sha256_16": str(safe_arguments.get("text_sha256_16", "")), "owner_session_id": self.owner_session_id, "argument_summary": safe_arguments}  # 修改代码+Phase30ComputerUseActionGate: 只记录必要元数据和脱敏摘要；如果没有这行代码，审计日志要么不可追踪要么可能泄露敏感内容。
        self.audit_log.append(event)  # 新增代码+Phase20ComputerUse: 把事件加入审计日志；如果没有这行代码，status 里看不到最近发生的安全判断。
        return event  # 新增代码+Phase20ComputerUse: 返回事件方便结果携带同一个审计 id；如果没有这行代码，工具返回无法和审计日志关联。

    def _with_audit(self, result: ComputerUseActionResult, event: dict[str, Any], action_evidence: dict[str, Any] | None = None) -> ComputerUseActionResult:  # 修改代码+Phase30ComputerUseActionGate: 把审计 id 和可选动作证据附加到动作结果里；如果没有这段函数，调用方需要自己拼接审计字段且容易遗漏。
        data = dict(result.data)  # 新增代码+Phase20ComputerUse: 复制结果数据避免直接修改冻结结果里的原始字典；如果没有这行代码，审计字段可能污染后端返回对象。
        data["audit_id"] = event["audit_id"]  # 新增代码+Phase20ComputerUse: 在结果中写入审计 id；如果没有这行代码，用户无法把这次结果对应到状态审计事件。
        if action_evidence is not None:  # 新增代码+Phase30ComputerUseActionGate: 只有写动作准备了证据时才附加 envelope；如果没有这行代码，observe 结果会被错误加入动作证据。
            evidence = dict(action_evidence)  # 新增代码+Phase30ComputerUseActionGate: 复制证据对象避免污染调用方传入数据；如果没有这行代码，后续修改可能影响审计事实。
            evidence["audit_id"] = event["audit_id"]  # 新增代码+Phase30ComputerUseActionGate: 把同一个 audit_id 写入证据；如果没有这行代码，结果和证据无法一一对应。
            for evidence_key in ("before_evidence", "after_evidence"):  # 新增代码+Phase31ComputerUseLockAbortEvidence: 遍历动作前后证据；如果没有这行代码，before/after 子证据可能缺少同一个 audit_id。
                if isinstance(evidence.get(evidence_key), dict):  # 新增代码+Phase31ComputerUseLockAbortEvidence: 只处理字典形态的子证据；如果没有这行代码，异常类型会在复制时出错。
                    nested_evidence = dict(evidence[evidence_key])  # 新增代码+Phase31ComputerUseLockAbortEvidence: 复制子证据避免修改原对象；如果没有这行代码，调用方传入证据可能被意外污染。
                    nested_evidence["audit_id"] = event["audit_id"]  # 新增代码+Phase31ComputerUseLockAbortEvidence: 给子证据补同一个审计 id；如果没有这行代码，before/after 无法独立追溯到动作。
                    evidence[evidence_key] = nested_evidence  # 新增代码+Phase31ComputerUseLockAbortEvidence: 写回补齐后的子证据；如果没有这行代码，结果仍会保留旧的空 audit_id。
            if self.audit_store is not None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 检查是否配置了落盘审计仓库；如果没有这行代码，测试注入路径会误写真实磁盘。
                disk_record = self.audit_store.record_event(event, evidence)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 保存审计事件和证据链；如果没有这行代码，动作完成后没有可打开的链路文件。
                data["audit_events_path"] = disk_record.get("events_path", "")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 把事件日志路径返回给调用方；如果没有这行代码，用户不知道事件写到了哪里。
                if disk_record.get("chain_path"):  # 新增代码+Phase31ComputerUseLockAbortEvidence: 检查动作证据链是否保存成功；如果没有这行代码，空链路路径也可能被当作有效证据。
                    evidence["chain_path"] = disk_record["chain_path"]  # 新增代码+Phase31ComputerUseLockAbortEvidence: 把证据链路径写进动作证据；如果没有这行代码，结果和落盘链路会断开。
                    data["audit_chain_path"] = disk_record["chain_path"]  # 新增代码+Phase31ComputerUseLockAbortEvidence: 在结果顶层也暴露链路路径；如果没有这行代码，终端 UI 很难直接显示链路位置。
            data["action_evidence"] = evidence  # 新增代码+Phase30ComputerUseActionGate: 将动作证据放进结果数据；如果没有这行代码，模型和用户看不到坐标、锁和窗口证据。
        elif self.audit_store is not None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 对 observe 和拒绝事件也保存审计事件；如果没有这行代码，只有成功动作有磁盘轨迹。
            disk_record = self.audit_store.record_event(event)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 保存无动作证据的普通事件；如果没有这行代码，状态查询和拒绝门禁无法长期复盘。
            data["audit_events_path"] = disk_record.get("events_path", "")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回事件日志路径；如果没有这行代码，用户不知道普通事件写到了哪里。
        return ComputerUseActionResult(result.ok, result.message, data)  # 新增代码+Phase20ComputerUse: 返回带审计 id 的新结果；如果没有这行代码，ComputerUseActionResult 的不可变约束会被破坏。

    def _capture_action_window_evidence(self, phase: str, audit_id: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段开始，采集动作前后窗口状态证据；如果没有这段函数，动作证据只有计划参数没有前后现场。
        raw_window = arguments.get("window")  # 新增代码+Phase31ComputerUseLockAbortEvidence: 读取动作绑定窗口；如果没有这行代码，证据采集不知道要观察哪个窗口。
        if raw_window is None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 判断动作是否没有窗口目标；如果没有这行代码，旧截图动作可能因无窗口而报错。
            return {"audit_id": audit_id, "phase": phase, "captured": False, "reason": "missing_window"}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回未采集原因；如果没有这行代码，证据链会缺少解释。
        window_ref = build_window_ref(raw_window)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 把窗口参数转换成强类型引用；如果没有这行代码，坏窗口字段会直接传给后端。
        if window_ref is None:  # 新增代码+Phase31ComputerUseLockAbortEvidence: 判断窗口引用是否无效；如果没有这行代码，无效窗口可能导致 observe 失败异常。
            return {"audit_id": audit_id, "phase": phase, "captured": False, "reason": "invalid_window"}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回无效窗口原因；如果没有这行代码，证据链无法解释为何没有现场状态。
        probe = self.backend.observe("get_window_state", {"window": window_ref.to_dict(), "validation_only": True, "evidence_phase": phase})  # 新增代码+Phase31ComputerUseLockAbortEvidence: 通过只读 observe 获取窗口状态；如果没有这行代码，before/after 只是空壳字段。
        state_payload = probe.data.get("state", {}) if isinstance(probe.data, dict) else {}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 安全读取后端返回状态；如果没有这行代码，异常 data 类型会破坏动作执行。
        state = dict(state_payload) if isinstance(state_payload, dict) else {}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 复制状态字典避免污染后端结果；如果没有这行代码，后续审计脱敏可能改到原对象。
        return {"audit_id": audit_id, "phase": phase, "captured": bool(probe.ok), "message": probe.message, "window": window_ref.to_dict(), "backend": probe.data.get("backend", "") if isinstance(probe.data, dict) else "", "state": state}  # 新增代码+Phase31ComputerUseLockAbortEvidence: 返回可落盘的现场证据；如果没有这行代码，审计链不能说明动作前后看到什么。
    # 新增代码+Phase31ComputerUseLockAbortEvidence: 函数段结束，_capture_action_window_evidence 到此结束；如果没有这个边界说明，初学者不容易看出证据采集范围。

    def observe(self, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+Phase27ComputerUse: 执行一次只读桌面观察；如果没有这段代码，computer_observe 工具没有统一安全入口。
        action = str(arguments.get("action", "")).strip()  # 新增代码+Phase27ComputerUse: 读取并清理观察动作名；如果没有这行代码，空白动作名会进入后端。
        audit_action = f"observe:{action}"  # 新增代码+Phase27ComputerUse: 给审计动作名加 observe 前缀；如果没有这行代码，观察审计和写动作审计会混在一起。
        if action not in self.OBSERVE_ACTIONS:  # 新增代码+Phase27ComputerUse: 拒绝未知观察动作；如果没有这行代码，模型可能通过 observe 传入未设计命令。
            result = ComputerUseActionResult(False, f"不支持的 Computer Use 观察动作：{action}", {"allowed_observe_actions": sorted(self.OBSERVE_ACTIONS)})  # 新增代码+Phase27ComputerUse: 构造未知观察动作拒绝结果；如果没有这行代码，错误缺少可操作提示。
            event = self._record_audit(audit_action, False, result.message, arguments)  # 新增代码+Phase27ComputerUse: 记录 observe 拒绝审计；如果没有这行代码，只读工具异常不会进入状态摘要。
            return self._with_audit(result, event)  # 新增代码+Phase27ComputerUse: 返回带审计 id 的 observe 拒绝结果；如果没有这行代码，工具输出无法关联审计。
        observe_drift_rejection = self._reject_agent_owned_target_drift(audit_action, arguments)  # 新增代码+ComputerUseSessionTargetGuard：在只读观察前复用 agent-owned 目标窗口漂移门禁；如果没有这行代码，模型仍能观察旧窗口截图并把旧内容当成本轮任务上下文。
        if observe_drift_rejection is not None:  # 新增代码+ComputerUseSessionTargetGuard：判断本次观察是否命中了旧窗口漂移；如果没有这行代码，拒绝结果会被忽略继续读取旧窗口。
            return observe_drift_rejection  # 新增代码+ComputerUseSessionTargetGuard：直接返回拒绝且不调用后端 observe；如果没有这行代码，旧窗口截图仍会进入模型主循环。
        result = self.backend.observe(action, dict(arguments))  # 新增代码+Phase27ComputerUse: 把合法只读观察交给后端；如果没有这行代码，observe 永远不会读取窗口目录。
        event = self._record_audit(audit_action, result.ok, result.message, arguments)  # 新增代码+Phase27ComputerUse: 记录 observe 成功或失败审计；如果没有这行代码，窗口观察缺少复盘轨迹。
        return self._with_audit(result, event)  # 新增代码+Phase27ComputerUse: 返回带审计 id 的 observe 结果；如果没有这行代码，状态和结果无法互相定位。

    def _reject_unapproved_action(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult | None:  # 新增代码+Phase38WindowsComputerApproval: 函数段开始，在后端执行前执行 approval 检查；如果没有这段函数，高风险窗口可能通过已有锁门禁后仍被后端执行。
        if self.approval_model is None or not hasattr(self.approval_model, "evaluate"):  # 新增代码+Phase38WindowsComputerApproval: 没有配置审批模型时保持旧路径兼容；如果没有这行代码，未启用 Phase38 的测试和旧调用会被误拦截。
            return None  # 新增代码+Phase38WindowsComputerApproval: 返回 None 表示 approval 不拦截；如果没有这行代码，正常动作会卡在空模型路径。
        if action == "screenshot":  # 新增代码+Phase38WindowsComputerApproval: 只读截图不进入写动作审批；如果没有这行代码，观察能力可能被错误要求会话授权。
            return None  # 新增代码+Phase38WindowsComputerApproval: 放行只读截图到后续路径；如果没有这行代码，状态观察会退化。
        approval = self.approval_model.evaluate(action, dict(arguments))  # 新增代码+Phase38WindowsComputerApproval: 让 approval 模型评估动作和窗口；如果没有这行代码，session allowlist 和禁止目标规则不会生效。
        if bool(approval.get("allowed", False)):  # 新增代码+Phase38WindowsComputerApproval: 判断审批是否允许；如果没有这行代码，允许动作也会被误拒绝。
            return None  # 新增代码+Phase38WindowsComputerApproval: 审批通过时继续后续窗口、锁和后端流程；如果没有这行代码，授权 app 仍无法执行动作。
        result = ComputerUseActionResult(False, "Computer Use approval 未通过，已拒绝执行桌面动作。", {"action": action, "approval": approval})  # 新增代码+Phase38WindowsComputerApproval: 构造审批拒绝结果；如果没有这行代码，用户看不到拒绝原因和目标摘要。
        event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase38WindowsComputerApproval: 记录审批拒绝审计；如果没有这行代码，approval 拦截无法在 status 和磁盘日志中复盘。
        return self._with_audit(result, event)  # 新增代码+Phase38WindowsComputerApproval: 返回带审计 id 的审批拒绝结果；如果没有这行代码，调用方无法把拒绝结果和审计事件关联。
    # 新增代码+Phase38WindowsComputerApproval: 函数段结束，_reject_unapproved_action 到此结束；如果没有这个边界说明，读者不容易看出 approval 拦截范围。

    def _target_resolution_recovery_actions(self) -> list[str]:  # 新增代码+TargetRegistryRootRemediation: 函数段开始，集中声明目标解析失败后的安全恢复动作；如果没有这段函数，多个拒绝路径会各自写一份不一致建议。
        return ["observe", "launch_app"]  # 新增代码+TargetRegistryRootRemediation: 只建议重新观察或重新启动绑定；如果没有这一行，模型可能继续尝试真实鼠标键盘动作。
    # 新增代码+TargetRegistryRootRemediation: 函数段结束，_target_resolution_recovery_actions 到此结束；如果没有这个边界说明，读者不容易看出恢复建议范围。

    def _target_resolution_failure_result(self, action: str, arguments: dict[str, Any], resolution: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+TargetRegistryRootRemediation: 函数段开始，把 target_ref 解析失败转成 controller 拒绝结果；如果没有这段函数，坏 ref 可能继续进入后端。
        data = {"action": action, "resolved_target_ref": str(resolution.get("target_ref", "")), "resolved_target_window_present": False, "target_resolution_source": "rejected", "target_resolution_error": str(resolution.get("error", resolution.get("decision", "target_resolution_failed"))), "low_level_event_count": 0, "recovery_next_allowed_actions": list(resolution.get("recovery_next_allowed_actions", self._target_resolution_recovery_actions()))}  # 修改代码+TargetRegistryRootRemediation: 构造机器可读拒绝数据并优先透传 error；如果没有这一行，模型看不到 target_ref_not_found 这类可恢复原因。
        result = ComputerUseActionResult(False, "目标窗口引用无法解析，已拒绝桌面动作以避免操作错误窗口。", data)  # 新增代码+TargetRegistryRootRemediation: 构造拒绝结果；如果没有这一行，错误 target_ref 可能表现成普通后端失败。
        event = self._record_audit(action, False, result.message, arguments)  # 新增代码+TargetRegistryRootRemediation: 记录目标解析失败审计；如果没有这一行，S2/S4 失败后无法复盘 ref 为什么被拒绝。
        return self._with_audit(result, event)  # 新增代码+TargetRegistryRootRemediation: 返回带 audit_id 的拒绝结果；如果没有这一行，工具输出无法关联审计日志。
    # 新增代码+TargetRegistryRootRemediation: 函数段结束，_target_resolution_failure_result 到此结束；如果没有这个边界说明，读者不容易看出拒绝结果构造范围。

    def _target_lease_report_from_resolution(self, action: str, target_resolution: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ControllerTargetLease：函数段开始，从目标解析结果恢复当前动作应使用的租约；如果没有这段函数，租约读取会散落在多个分支里。
        if action not in WRITE_ACTIONS_REQUIRING_LEASE:  # 新增代码+ControllerTargetLease：只对会写桌面的动作要求租约；如果没有这一行，截图和启动应用会被错误要求已有租约。
            return {}  # 新增代码+ControllerTargetLease：非写动作返回空租约；如果没有这一行，调用方需要额外处理 None。
        embedded_lease = target_resolution.get("target_lease", {})  # 新增代码+ControllerTargetLease：先读取目标解析阶段附带的租约；如果没有这一行，显式解析结果里的 lease 会被忽略。
        if isinstance(embedded_lease, dict) and embedded_lease:  # 新增代码+ControllerTargetLease：确认嵌入租约是非空字典；如果没有这一行，坏类型可能进入 TargetLease 恢复。
            return dict(embedded_lease)  # 新增代码+ControllerTargetLease：返回嵌入租约副本；如果没有这一行，后续修改可能污染 registry 里的审计事实。
        target_ref = str(target_resolution.get("target_ref", "") or "").strip()  # 新增代码+ControllerTargetLease：读取解析出的 target_ref；如果没有这一行，无法从 registry 回查租约。
        if target_ref:  # 新增代码+ControllerTargetLease：只有存在 target_ref 时才查 registry；如果没有这一行，空 ref 会产生无意义查询。
            ref_resolution = self.target_registry.resolve_target_ref(target_ref)  # 新增代码+ControllerTargetLease：通过 registry 回查目标记录；如果没有这一行，target_ref 成功解析后仍拿不到 lease。
            target_payload = dict(ref_resolution.get("target", {})) if isinstance(ref_resolution.get("target", {}), dict) else {}  # 新增代码+ControllerTargetLease：安全读取 registry 目标记录；如果没有这一行，坏返回值会导致动作崩溃。
            registry_lease = target_payload.get("lease", {})  # 新增代码+ControllerTargetLease：读取 registry 托管的租约；如果没有这一行，旧 target_ref 和新租约无法关联。
            if isinstance(registry_lease, dict) and registry_lease:  # 新增代码+ControllerTargetLease：确认 registry lease 可用；如果没有这一行，空租约会被误当成有效权限。
                return dict(registry_lease)  # 新增代码+ControllerTargetLease：返回 registry lease 副本；如果没有这一行，后续校验可能修改原记录。
        if self.active_target_lease:  # 新增代码+ControllerTargetLease：显式 window 路径没有 ref 时回退到当前 active lease；如果没有这一行，错误窗口漂移无法拿到基准租约。
            return dict(self.active_target_lease)  # 新增代码+ControllerTargetLease：返回当前 active lease 副本；如果没有这一行，显式窗口写动作无法执行通用租约比较。
        return {}  # 新增代码+ControllerTargetLease：没有任何租约来源时返回空字典；如果没有这一行，调用方无法稳定判断缺租约。
    # 新增代码+ControllerTargetLease：函数段结束，_target_lease_report_from_resolution 到此结束；如果没有这个边界说明，读者不容易看出租约来源顺序。

    def _reject_invalid_target_lease(self, action: str, arguments: dict[str, Any], target_resolution: dict[str, Any]) -> ComputerUseActionResult | None:  # 新增代码+ControllerTargetLease：函数段开始，在真实后端前执行通用目标租约门禁；如果没有这段函数，target_ref 只代表窗口，不代表有权控制。
        if action not in WRITE_ACTIONS_REQUIRING_LEASE:  # 新增代码+ControllerTargetLease：非写动作不进入租约门禁；如果没有这一行，截图和 launch_app 会被错误阻断。
            return None  # 新增代码+ControllerTargetLease：返回 None 表示不拦截；如果没有这一行，execute 无法继续正常流程。
        lease_report = self._target_lease_report_from_resolution(action, target_resolution)  # 新增代码+ControllerTargetLease：恢复本动作应使用的租约；如果没有这一行，后续无法判断目标权限。
        target_ref = str(target_resolution.get("target_ref", "") or "").strip()  # 新增代码+ControllerTargetLease：读取当前解析出的目标引用；如果没有这一行，缺租约拒绝无法说明哪个 ref 有问题。
        lease_required = bool(lease_report or target_ref or self.active_target_lease)  # 新增代码+ControllerTargetLease：只有 target_ref 或 active lease 场景强制租约；如果没有这一行，旧的无 target 测试路径会被无谓打断。
        if not lease_required:  # 新增代码+ControllerTargetLease：兼容完全没有目标会话的旧路径；如果没有这一行，尚未迁移的只测 controller 用例会全部失败。
            return None  # 新增代码+ControllerTargetLease：没有租约需求时放行到既有门禁；如果没有这一行，旧路径无法继续执行。
        current_window = dict(arguments.get("window", {})) if isinstance(arguments.get("window", {}), dict) else {}  # 新增代码+ControllerTargetLease：读取当前动作窗口；如果没有这一行，租约校验不知道本次动作打算操作哪里。
        if not lease_report:  # 新增代码+ControllerTargetLease：检查是否缺少租约；如果没有这一行，空租约会继续进入后端。
            verification_report = {"allowed": False, "decision": "target_lease_missing", "target_drift_blocks_action": True, "low_level_event_count": 0, "expected": {}, "current": current_window}  # 新增代码+ControllerTargetLease：构造缺租约拒绝报告；如果没有这一行，模型看不到需要重新 launch_app 建立租约。
            target_resolution["target_lease_verification"] = verification_report  # 新增代码+ControllerTargetLease：把拒绝报告回填到解析对象；如果没有这一行，后续结果无法统一附加租约证据。
            data = {"action": action, "resolved_target_ref": target_ref, "target_lease": {}, "target_lease_verification": verification_report, "target_drift_blocks_action": True, "low_level_event_count": 0, "recovery_next_allowed_actions": self._target_resolution_recovery_actions()}  # 新增代码+ControllerTargetLease：构造零事件拒绝数据；如果没有这一行，压力测试无法证明无租约目标没有触发后端。
            result = ComputerUseActionResult(False, "目标窗口缺少有效 TargetLease，已拒绝桌面写动作以避免接管错误窗口。", data)  # 新增代码+ControllerTargetLease：返回缺租约拒绝；如果没有这一行，旧 registry 记录可能继续写入用户窗口。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+ControllerTargetLease：记录缺租约审计；如果没有这一行，真实终端无法复盘为什么没有执行。
            return self._with_audit(result, event)  # 新增代码+ControllerTargetLease：返回带 audit_id 的拒绝结果；如果没有这一行，工具输出无法关联状态审计。
        lease = target_lease_from_dict(lease_report)  # 新增代码+ControllerTargetLease：把租约字典恢复成强类型对象；如果没有这一行，动作前验证只能读松散 dict。
        verification = verify_target_lease_before_action(lease=lease, current_window=current_window, action=action)  # 新增代码+ControllerTargetLease：执行通用动作前租约验证；如果没有这一行，pid/hwnd 漂移不会在 SendInput 前被阻断。
        verification_report = verification.to_dict()  # 新增代码+ControllerTargetLease：把验证结果转换成可返回字典；如果没有这一行，工具结果无法携带机器可读原因。
        target_resolution["target_lease"] = lease.to_dict()  # 新增代码+ControllerTargetLease：把规范化租约放回解析结果；如果没有这一行，成功结果不会说明使用了哪份租约。
        target_resolution["target_lease_verification"] = verification_report  # 新增代码+ControllerTargetLease：把验证报告放回解析结果；如果没有这一行，成功和失败结果缺少统一字段。
        if verification.allowed:  # 新增代码+ControllerTargetLease：检查租约是否允许本次动作；如果没有这一行，拒绝和放行分支无法区分。
            return None  # 新增代码+ControllerTargetLease：租约通过时不拦截；如果没有这一行，正常写动作无法到达后端。
        recovery = decide_recovery_after_drift(target_ref or lease.target_ref, verification_report.get("decision", "target_lease_drift_rejected"))  # 新增代码+FreshTargetPolicy：生成漂移后的安全恢复建议；如果没有这一行，模型可能继续尝试坏 target_ref。
        invalidation = self.target_registry.invalidate_target(target_ref or lease.target_ref, reason=verification_report.get("decision", "target_lease_drift_rejected")) if bool(verification_report.get("target_drift_blocks_action")) else {}  # 新增代码+FreshTargetPolicy：漂移类拒绝时失效 target_ref；如果没有这一行，坏引用会在下一步继续可用。
        if bool(invalidation.get("invalidated")) and str(self.active_target_lease.get("target_ref", "")) == str(target_ref or lease.target_ref):  # 新增代码+FreshTargetPolicy：检查当前 active lease 是否就是失效目标；如果没有这一行，active 状态可能继续指向旧窗口。
            self.active_target_lease = {}  # 新增代码+FreshTargetPolicy：清空 active lease；如果没有这一行，显式 window 路径可能继续借旧租约。
            self.active_agent_owned_target_window = {}  # 新增代码+FreshTargetPolicy：清空 active 窗口基准；如果没有这一行，旧漂移门禁会影响下一轮目标。
        target_resolution["target_invalidated"] = dict(invalidation) if isinstance(invalidation, dict) else {}  # 新增代码+FreshTargetPolicy：把失效报告回填到解析结果；如果没有这一行，最终数据看不到 target_ref 已作废。
        data = {"action": action, "resolved_target_ref": target_ref or lease.target_ref, "target_lease": lease.to_dict(), "target_lease_verification": verification_report, "target_invalidated": dict(invalidation) if isinstance(invalidation, dict) else {}, "fresh_target_recovery": dict(recovery), "target_drift_blocks_action": bool(verification_report.get("target_drift_blocks_action")), "low_level_event_count": 0, "recovery_next_allowed_actions": list(recovery.get("recovery_next_allowed_actions", self._target_resolution_recovery_actions()))}  # 修改代码+FreshTargetPolicy：构造租约失败零事件数据并携带失效恢复报告；如果没有这一行，错窗口拒绝无法展示 expected/current 和下一步。
        result = ComputerUseActionResult(False, "TargetLease 校验未通过，已拒绝桌面写动作以避免操作错误窗口。", data)  # 新增代码+ControllerTargetLease：返回租约漂移拒绝；如果没有这一行，错误窗口仍可能进入真实后端。
        event = self._record_audit(action, False, result.message, arguments)  # 新增代码+ControllerTargetLease：记录租约拒绝审计；如果没有这一行，状态里无法解释动作为什么被拦。
        return self._with_audit(result, event)  # 新增代码+ControllerTargetLease：返回带 audit_id 的拒绝结果；如果没有这一行，工具输出和审计无法关联。
    # 新增代码+ControllerTargetLease：函数段结束，_reject_invalid_target_lease 到此结束；如果没有这个边界说明，读者不容易看出租约门禁范围。

    def _resolve_action_target(self, action: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+TargetRegistryRootRemediation: 函数段开始，在真实动作前统一解析 target_ref/window/active target；如果没有这段函数，S2 仍会依赖模型手动复制窗口。
        resolved_arguments = dict(arguments)  # 新增代码+TargetRegistryRootRemediation: 复制动作参数用于注入 window；如果没有这一行，目标解析会直接污染调用方原始参数。
        if action in {"screenshot", "launch_app"}:  # 新增代码+TargetRegistryRootRemediation: 截图和启动动作不需要已有目标；如果没有这一行，launch_app 会在创建目标前被要求已有目标。
            return {"ok": True, "arguments": resolved_arguments, "source": "not_required", "target_ref": "", "target_window_present": False, "error": "", "recovery_next_allowed_actions": []}  # 新增代码+TargetRegistryRootRemediation: 返回不需要目标的解析结果；如果没有这一行，调用方要特殊处理 None。
        raw_target_ref = resolved_arguments.get("target_ref")  # 新增代码+TargetRegistryRootRemediation: 读取模型传入的稳定 target_ref；如果没有这一行，显式 ref 路径无法优先解析。
        if str(raw_target_ref or "").strip():  # 新增代码+TargetRegistryRootRemediation: 只有非空 target_ref 才走 ref 解析；如果没有这一行，空字符串会被当作坏 ref 拒绝旧兼容路径。
            ref_resolution = self.target_registry.resolve_target_ref(raw_target_ref)  # 新增代码+TargetRegistryRootRemediation: 通过 session registry 解析 ref；如果没有这一行，target_ref 不能恢复成真实 window。
            if not bool(ref_resolution.get("ok")):  # 新增代码+TargetRegistryRootRemediation: 检查 ref 是否解析成功；如果没有这一行，坏 ref 会继续进入后端。
                return {"ok": False, "arguments": resolved_arguments, "source": "rejected", "target_ref": str(ref_resolution.get("target_ref", raw_target_ref)), "target_window_present": False, "error": str(ref_resolution.get("decision", "target_ref_not_found")), "recovery_next_allowed_actions": list(ref_resolution.get("recovery_next_allowed_actions", self._target_resolution_recovery_actions()))}  # 新增代码+TargetRegistryRootRemediation: 返回坏 ref 拒绝报告；如果没有这一行，低层事件可能被错误触发。
            target_payload = dict(ref_resolution.get("target", {})) if isinstance(ref_resolution.get("target", {}), dict) else {}  # 新增代码+TargetRegistryRootRemediation: 读取解析成功的 target 记录；如果没有这一行，无法安全取出 window。
            resolved_window = dict(target_payload.get("window", {})) if isinstance(target_payload.get("window", {}), dict) else dict(target_payload.get("raw_window", {}))  # 新增代码+TargetRegistryRootRemediation: 取出后端可用 window 字典；如果没有这一行，controller 仍缺少真实窗口参数。
            requested_window_ref = build_window_ref(resolved_arguments.get("window"))  # 新增代码+ControllerTargetLease：读取 target_ref 同时携带的显式窗口；如果没有这一行，错误旧窗口会被 target_ref 静默覆盖。
            resolved_window_ref = build_window_ref(resolved_window)  # 新增代码+ControllerTargetLease：把 registry 窗口转成可比较身份；如果没有这一行，无法判断显式窗口是否和租约目标冲突。
            if requested_window_ref is not None and resolved_window_ref is not None and window_ref_identity(requested_window_ref) != window_ref_identity(resolved_window_ref):  # 新增代码+ControllerTargetLease：发现 target_ref 与显式 window 指向不同窗口；如果没有这一行，模型传错 window 时会被覆盖成成功路径。
                return {"ok": True, "arguments": resolved_arguments, "source": "explicit_ref_conflicting_window", "target_ref": str(ref_resolution.get("target_ref", raw_target_ref)), "target_window_present": True, "target_lease": dict(target_payload.get("lease", {})) if isinstance(target_payload.get("lease", {}), dict) else {}, "error": "target_ref_window_conflict", "recovery_next_allowed_actions": []}  # 新增代码+ControllerTargetLease：保留显式冲突 window 交给 lease 门禁零事件拒绝；如果没有这一行，restored Notepad 会绕过漂移检测。
            resolved_arguments["window"] = resolved_window  # 新增代码+TargetRegistryRootRemediation: 把 ref 解析出的 window 注入参数；如果没有这一行，后端仍收不到目标窗口。
            return {"ok": True, "arguments": resolved_arguments, "source": "explicit_ref", "target_ref": str(ref_resolution.get("target_ref", raw_target_ref)), "target_window_present": bool(resolved_window), "error": "", "recovery_next_allowed_actions": []}  # 新增代码+TargetRegistryRootRemediation: 返回显式 ref 解析成功报告；如果没有这一行，结果契约缺少目标来源。
        raw_window = resolved_arguments.get("window")  # 新增代码+TargetRegistryRootRemediation: 读取模型显式传入的窗口；如果没有这一行，无法区分显式 window 和缺失 window。
        window_ref = build_window_ref(raw_window)  # 新增代码+TargetRegistryRootRemediation: 尝试把显式 window 转成强类型引用；如果没有这一行，坏 window 也可能被当作已解析目标。
        if window_ref is not None:  # 新增代码+TargetRegistryRootRemediation: 显式 window 身份完整时保留旧兼容路径；如果没有这一行，手动 window 调用会被无谓改写。
            active_target = self.target_registry.get_active_target()  # 新增代码+TargetRegistryRootRemediation: 读取 active target 用于补充 ref；如果没有这一行，显式 window 成功结果没有 ref 可追踪。
            active_window = dict(active_target.get("window", {})) if isinstance(active_target, dict) and isinstance(active_target.get("window", {}), dict) else {}  # 新增代码+TargetRegistryRootRemediation: 读取 active target 的 raw window；如果没有这一行，无法判断显式 window 是否就是 active target。
            active_ref = build_window_ref(active_window)  # 新增代码+TargetRegistryRootRemediation: 把 active window 转成强类型引用；如果没有这一行，身份比较没有统一键。
            matched_active_ref = str(active_target.get("target_ref", "")) if active_ref is not None and window_ref_identity(active_ref) == window_ref_identity(window_ref) else ""  # 新增代码+TargetRegistryRootRemediation: 如果显式 window 等于 active target 就补充 target_ref；如果没有这一行，结果里缺少 resolved_target_ref。
            return {"ok": True, "arguments": resolved_arguments, "source": "explicit_window", "target_ref": matched_active_ref, "target_window_present": True, "error": "", "recovery_next_allowed_actions": []}  # 新增代码+TargetRegistryRootRemediation: 返回显式 window 解析成功报告；如果没有这一行，结果契约无法说明目标来源。
        implicit_resolution = self.target_registry.resolve_implicit_target()  # 新增代码+FreshTargetPolicy：尝试安全解析唯一有效目标；如果没有这一行，多目标时会继续默认使用 active 窗口。
        if bool(implicit_resolution.get("ok")):  # 新增代码+FreshTargetPolicy：只有唯一有效目标时才允许隐式注入；如果没有这一行，单目标兼容路径会失效。
            target_payload = dict(implicit_resolution.get("target", {})) if isinstance(implicit_resolution.get("target", {}), dict) else {}  # 新增代码+FreshTargetPolicy：读取唯一 target 记录；如果没有这一行，无法取出真实窗口。
            implicit_window = dict(target_payload.get("window", {})) if isinstance(target_payload.get("window", {}), dict) else dict(target_payload.get("raw_window", {}))  # 新增代码+FreshTargetPolicy：取出后端可用 window；如果没有这一行，后续动作仍缺目标窗口。
            if implicit_window:  # 新增代码+FreshTargetPolicy：确认窗口非空再注入；如果没有这一行，空 target 会绕过后续校验。
                resolved_arguments["window"] = implicit_window  # 新增代码+FreshTargetPolicy：把唯一目标窗口注入动作参数；如果没有这一行，简单任务漏写 window 会失败。
                return {"ok": True, "arguments": resolved_arguments, "source": "implicit_single_target", "target_ref": str(implicit_resolution.get("target_ref", "")), "target_window_present": True, "target_lease": dict(target_payload.get("lease", {})) if isinstance(target_payload.get("lease", {}), dict) else {}, "error": "", "recovery_next_allowed_actions": []}  # 新增代码+FreshTargetPolicy：返回唯一目标注入报告；如果没有这一行，结果无法说明为何可隐式操作。
        if str(implicit_resolution.get("decision", "")) != "target_ref_missing":  # 新增代码+FreshTargetPolicy：多目标或失效歧义时必须拒绝；如果没有这一行，复杂任务可能误打最近窗口。
            return {"ok": False, "arguments": resolved_arguments, "source": "rejected", "target_ref": "", "target_window_present": False, "error": str(implicit_resolution.get("decision", "target_ref_required")), "recovery_next_allowed_actions": list(implicit_resolution.get("recovery_next_allowed_actions", self._target_resolution_recovery_actions()))}  # 新增代码+FreshTargetPolicy：返回多目标需要 target_ref 的拒绝；如果没有这一行，模型不知道要补 target_ref。
        return {"ok": True, "arguments": resolved_arguments, "source": "legacy_no_target", "target_ref": "", "target_window_present": False, "error": "", "recovery_next_allowed_actions": self._target_resolution_recovery_actions()}  # 新增代码+TargetRegistryRootRemediation: 没有 registry 目标时保持旧兼容路径；如果没有这一行，未启用 full mode 的旧测试会被突然拒绝。
    # 新增代码+TargetRegistryRootRemediation: 函数段结束，_resolve_action_target 到此结束；如果没有这个边界说明，读者不容易看出目标解析顺序。

    def _with_target_resolution(self, result: ComputerUseActionResult, resolution: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+TargetRegistryRootRemediation: 函数段开始，把目标解析证据附加到动作结果；如果没有这段函数，ok=true 但 target_window_present=false 的模糊结果会复发。
        data = dict(result.data)  # 新增代码+TargetRegistryRootRemediation: 复制结果数据避免修改原对象；如果没有这一行，后端返回可能被意外污染。
        dispatch = data.get("dispatch", {}) if isinstance(data.get("dispatch", {}), dict) else {}  # 新增代码+TargetRegistryRootRemediation: 读取可选 dispatch 摘要；如果没有这一行，真实低层事件数量可能藏在嵌套字段里。
        low_level_event_count = int(data.get("low_level_event_count", dispatch.get("low_level_event_count", 0)) or 0)  # 新增代码+TargetRegistryRootRemediation: 规范化低层事件数量；如果没有这一行，结果契约缺少可审计动作量。
        data["resolved_target_ref"] = str(resolution.get("target_ref", ""))  # 新增代码+TargetRegistryRootRemediation: 写入解析后的 target_ref；如果没有这一行，模型无法把动作和 launch_app 目标关联。
        data["resolved_target_window_present"] = bool(resolution.get("target_window_present", False))  # 新增代码+TargetRegistryRootRemediation: 写入是否解析出窗口；如果没有这一行，ok=true 但无目标的状态不可见。
        data["target_resolution_source"] = str(resolution.get("source", ""))  # 新增代码+TargetRegistryRootRemediation: 写入目标来源；如果没有这一行，无法区分 explicit_ref、active_session 和 legacy_no_target。
        data["target_resolution_error"] = str(resolution.get("error", ""))  # 新增代码+TargetRegistryRootRemediation: 写入解析错误；如果没有这一行，失败路径没有机器可读原因。
        data["low_level_event_count"] = low_level_event_count  # 新增代码+TargetRegistryRootRemediation: 确保顶层有低层事件数量；如果没有这一行，验收器可能读不到 dispatch 内的真实计数。
        data["recovery_next_allowed_actions"] = list(resolution.get("recovery_next_allowed_actions", []))  # 新增代码+TargetRegistryRootRemediation: 写入安全恢复建议；如果没有这一行，模型可能继续尝试危险动作。
        if isinstance(resolution.get("target_lease"), dict):  # 新增代码+ControllerTargetLease：检查目标解析是否带有规范化租约；如果没有这一行，成功写动作无法展示权限来源。
            data["target_lease"] = dict(resolution.get("target_lease", {}))  # 新增代码+ControllerTargetLease：把租约报告附加到结果；如果没有这一行，用户看不到本次动作使用了哪份 lease。
        if isinstance(resolution.get("target_lease_verification"), dict):  # 新增代码+ControllerTargetLease：检查目标解析是否带有租约验证报告；如果没有这一行，成功路径缺少 target_lease_verified 证据。
            data["target_lease_verification"] = dict(resolution.get("target_lease_verification", {}))  # 新增代码+ControllerTargetLease：把租约验证附加到结果；如果没有这一行，压力测试无法断言写动作前确实校验过。
        return ComputerUseActionResult(result.ok, result.message, data)  # 新增代码+TargetRegistryRootRemediation: 返回附加目标解析证据的新结果；如果没有这一行，调用方拿不到更新后的 data。
    # 新增代码+TargetRegistryRootRemediation: 函数段结束，_with_target_resolution 到此结束；如果没有这个边界说明，读者不容易看出结果契约补充范围。

    def _reject_unknown_window_target(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult | None:  # 新增代码+Phase27ComputerUse: 在写动作前拦截未知窗口目标；如果没有这段函数，模型可能把鼠标键盘动作发给伪造窗口。
        raw_window = arguments.get("window")  # 新增代码+Phase27ComputerUse: 读取可选窗口目标；如果没有这行代码，控制器无法知道动作是否声明了目标窗口。
        if raw_window is None:  # 新增代码+Phase27ComputerUse: 兼容旧动作调用没有 window 的情况；如果没有这行代码，Phase 20 旧测试会被误拒绝。
            return None  # 新增代码+Phase27ComputerUse: 没有窗口目标时不做未知窗口校验；如果没有这行代码，旧坐标动作无法继续兼容。
        window_ref = build_window_ref(raw_window)  # 新增代码+Phase27ComputerUse: 将传入窗口目标转换成强类型引用；如果没有这行代码，缺 app_id/window_id 的目标可能绕过校验。
        if window_ref is None:  # 新增代码+Phase27ComputerUse: 判断窗口引用是否完整；如果没有这行代码，半截窗口目标会进入后端。
            result = ComputerUseActionResult(False, "未知窗口目标：window 必须包含 app_id 和 window_id。", {"action": action})  # 新增代码+Phase27ComputerUse: 返回窗口字段缺失错误；如果没有这行代码，模型不知道如何修正参数。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase27ComputerUse: 记录窗口字段缺失拒绝；如果没有这行代码，拒绝原因不会进入审计日志。
            return self._with_audit(result, event)  # 新增代码+Phase27ComputerUse: 返回带审计 id 的拒绝结果；如果没有这行代码，调用方无法关联这次拦截。
        probe = self.backend.observe("get_window_state", {"window": window_ref.to_dict(), "validation_only": True})  # 新增代码+Phase27ComputerUse: 用只读状态查询验证窗口仍在可信目录；如果没有这行代码，未知窗口不能在动作前被发现。
        if probe.ok:  # 新增代码+Phase27ComputerUse: 后端确认窗口存在时放行动作；如果没有这行代码，已知窗口也会被误拒绝。
            return None  # 新增代码+Phase27ComputerUse: 返回 None 表示没有拦截；如果没有这行代码，execute 无法继续到后端。
        result = ComputerUseActionResult(False, "未知窗口目标，已拒绝执行桌面动作；请先调用 mcp__computer-use__observe 获取可信 window。", {"action": action, "window": window_ref.to_dict(), "observe_message": probe.message})  # 修改代码+McpObservedWindowFix: 返回 v2 工具面未知窗口拒绝结果；如果没有这行代码，模型会被隐藏旧观察接口名称引回不可见接口。
        event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase27ComputerUse: 记录未知窗口拒绝审计；如果没有这行代码，安全拦截无法复盘。
        return self._with_audit(result, event)  # 新增代码+Phase27ComputerUse: 返回带审计 id 的未知窗口拒绝；如果没有这行代码，结果和审计无法关联。

    def _reject_agent_owned_target_drift(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult | None:  # 新增代码+ModelLoopLaunchAppTool: 函数段开始，阻断 launch_app 后动作漂移到旧窗口；如果没有这段函数，模型会在打开新 Paint 后继续误操作用户旧 Paint。
        if action in {"screenshot", "launch_app"}:  # 新增代码+ModelLoopLaunchAppTool: 截图和启动动作不做目标漂移拦截；如果没有这行代码，启动前还没有 active target 时会被误拒绝。
            return None  # 新增代码+ModelLoopLaunchAppTool: 返回 None 表示不拦截；如果没有这行代码，调用方无法继续正常分支。
        if str(arguments.get("target_ref", "") or "").strip():  # 新增代码+FreshTargetPolicy：显式 target_ref 动作交给 TargetLease 精确校验；如果没有这一行，多目标任务会被旧 active 窗口门禁误拦。
            return None  # 新增代码+FreshTargetPolicy：不重复执行 active 窗口漂移拦截；如果没有这一行，合法非 active target 可能被拒绝。
        active_window = dict(self.active_agent_owned_target_window or {})  # 新增代码+ModelLoopLaunchAppTool: 读取当前 agent-owned 目标窗口副本；如果没有这行代码，后续比较可能被外部字典污染。
        if not active_window:  # 新增代码+ModelLoopLaunchAppTool: 没有 launch_app 目标时保持旧兼容；如果没有这行代码，普通手动授权窗口会全部被拒绝。
            return None  # 新增代码+ModelLoopLaunchAppTool: 没有 active target 不拦截；如果没有这行代码，未使用 launch_app 的旧路径会失效。
        raw_window = arguments.get("window")  # 新增代码+ModelLoopLaunchAppTool: 读取本次动作声明的窗口；如果没有这行代码，无法判断是否漂移。
        window_ref = build_window_ref(raw_window)  # 新增代码+ModelLoopLaunchAppTool: 转成强类型窗口引用；如果没有这行代码，松散窗口字段比较容易漏判。
        active_ref = build_window_ref(active_window)  # 新增代码+ModelLoopLaunchAppTool: 转成 active target 引用；如果没有这行代码，active 窗口比较没有统一身份键。
        if window_ref is None or active_ref is None:  # 新增代码+ModelLoopLaunchAppTool: 窗口字段不完整时交给原未知窗口门禁处理；如果没有这行代码，None 身份比较会抛异常。
            return None  # 新增代码+ModelLoopLaunchAppTool: 不在这里重复处理缺字段；如果没有这行代码，错误提示会分裂成两套。
        if window_ref_identity(window_ref) == window_ref_identity(active_ref):  # 新增代码+ModelLoopLaunchAppTool: 只有同一窗口身份才允许继续；如果没有这行代码，正确 target_window 也会被误拒绝。
            return None  # 新增代码+ModelLoopLaunchAppTool: 目标一致不拦截；如果没有这行代码，agent-owned 正常动作无法执行。
        result = ComputerUseActionResult(False, "检测到目标窗口漂移：已拒绝操作非当前 launch_app 创建的 agent-owned 窗口。请改用 launch_app 返回的 target_window。", {"action": action, "active_target_window": active_window, "requested_window": window_ref.to_dict(), "target_drift_blocks_action": True, "low_level_event_count": 0})  # 新增代码+ModelLoopLaunchAppTool: 构造漂移拒绝报告；如果没有这行代码，模型不知道该回到哪个窗口。
        event = self._record_audit(action, False, result.message, arguments)  # 新增代码+ModelLoopLaunchAppTool: 记录漂移拒绝审计；如果没有这行代码，真实终端无法解释为什么没动鼠标。
        return self._with_audit(result, event)  # 新增代码+ModelLoopLaunchAppTool: 返回带审计 id 的漂移拒绝；如果没有这行代码，工具输出和审计无法关联。
    # 新增代码+ModelLoopLaunchAppTool: 函数段结束，_reject_agent_owned_target_drift 到此结束；如果没有这个边界说明，读者不容易看出漂移门禁范围。

    def _launch_app_clean_target_candidate(self, raw_value: Any) -> str:  # 新增代码+ModelLoopLaunchAppTool: 函数段开始，筛选 launch_app 的干净应用名；如果没有这段函数，模型可能把整段解释文字当成 exe 名启动。
        text = str(raw_value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+ModelLoopLaunchAppTool: 把候选目标压成单行文本；如果没有这行代码，换行污染无法被稳定识别。
        if not text:  # 新增代码+ModelLoopLaunchAppTool: 检查空候选；如果没有这行代码，空字符串可能进入启动后端。
            return ""  # 新增代码+ModelLoopLaunchAppTool: 空候选直接丢弃；如果没有这行代码，调用方会误以为已有目标。
        recovered_prefix = self._launch_app_safe_prefix_from_polluted_candidate(text)  # 新增代码+LaunchTargetRepairPollution: 先尝试从真实模型污染串恢复安全应用前缀；如果没有这行代码，`mspaint}}]...Need valid JSON` 会被整体丢弃导致启动失败。
        if recovered_prefix:  # 新增代码+LaunchTargetRepairPollution: 只有命中受控安全别名时才恢复；如果没有这行代码，空恢复结果可能被误当成应用名。
            return recovered_prefix  # 新增代码+LaunchTargetRepairPollution: 返回干净应用别名给启动 runtime；如果没有这行代码，后续长度和符号门禁仍会拒绝真实 mspaint 意图。
        if len(text) > 80:  # 新增代码+ModelLoopLaunchAppTool: 拒绝明显不像应用名的长文本；如果没有这行代码，模型历史回答可能被当成启动目标。
            return ""  # 新增代码+ModelLoopLaunchAppTool: 长文本候选丢弃；如果没有这行代码，安全 resolver 会收到污染目标并拒绝真实启动。
        normalized_text = text.lower()  # 新增代码+LaunchTargetPollutionGate: 准备小写版本用于判断 .exe 后缀；如果没有这行代码，大小写不同的 EXE 名可能被误判。
        if "." in text and not normalized_text.endswith(".exe"):  # 新增代码+LaunchTargetPollutionGate: 拒绝带句点但不是 exe 文件名的候选；如果没有这行代码，`mspaint画图软件画一棵树.` 会被当成应用名。
            return ""  # 新增代码+LaunchTargetPollutionGate: 丢弃句子型候选；如果没有这行代码，启动后端会继续收到自然语言任务句。
        has_ascii_letter = any("a" <= character.lower() <= "z" for character in text)  # 新增代码+LaunchTargetPollutionGate: 检查候选里是否有英文字母；如果没有这行代码，无法识别 `mspaint` 这类英文别名和中文句子的混合污染。
        has_cjk_character = any("\u4e00" <= character <= "\u9fff" for character in text)  # 新增代码+LaunchTargetPollutionGate: 检查候选里是否有中文字符；如果没有这行代码，无法发现英文应用名后面粘了中文任务描述。
        if has_ascii_letter and has_cjk_character:  # 新增代码+LaunchTargetPollutionGate: 拒绝英文应用名和中文任务句混在一起的候选；如果没有这行代码，`mspaint画图软件画一棵树` 会盖过干净 app 字段。
            return ""  # 新增代码+LaunchTargetPollutionGate: 丢弃混合语言污染候选；如果没有这行代码，真实验收会再次尝试启动不存在的 exe。
        sentence_punctuation = ("，", "。", "；", "！", "？", "、")  # 新增代码+LaunchTargetPollutionGate: 标记中文任务句常见标点；如果没有这行代码，真实日志里的“mspaint，画一棵树。”会被误当成应用名。
        if any(token in text for token in sentence_punctuation):  # 新增代码+LaunchTargetPollutionGate: 拒绝包含中文句子标点的候选；如果没有这行代码，模型自然语言说明仍可能污染 launch_app 目标。
            return ""  # 新增代码+LaunchTargetPollutionGate: 丢弃中文句子型候选；如果没有这行代码，Start-Process 会尝试启动不存在的长中文 exe。
        ascii_sentence_punctuation = (",", ";", "!", "?")  # 新增代码+LaunchTargetPollutionGate: 标记英文任务句常见标点；如果没有这行代码，`mspaintowy?` 这类坏候选可能被当成应用名。
        if any(token in text for token in ascii_sentence_punctuation):  # 新增代码+LaunchTargetPollutionGate: 拒绝包含英文句子标点的候选；如果没有这行代码，模型猜错的带问号目标会进入启动后端。
            return ""  # 新增代码+LaunchTargetPollutionGate: 丢弃英文句子型候选；如果没有这行代码，错误字段可能阻断后续干净字段。
        if any(token in text for token in ("`", "{", "}", "[", "]", "\"", "'", "：", ":")):  # 新增代码+ModelLoopLaunchAppTool: 拒绝包含代码/JSON/说明符号的候选；如果没有这行代码，工具调用片段可能混进 app 名。
            return ""  # 新增代码+ModelLoopLaunchAppTool: 符号污染候选丢弃；如果没有这行代码，启动后端可能收到危险或无效目标。
        if len(text.split()) > 3:  # 新增代码+ModelLoopLaunchAppTool: 拒绝超过三个词的候选；如果没有这行代码，句子型文本可能伪装成应用名。
            return ""  # 新增代码+ModelLoopLaunchAppTool: 词数过多候选丢弃；如果没有这行代码，普通解释句可能被送去启动。
        return text  # 新增代码+ModelLoopLaunchAppTool: 返回通过筛选的应用名；如果没有这行代码，干净的 paint/mspaint/notepad 也无法启动。
    # 新增代码+ModelLoopLaunchAppTool: 函数段结束，_launch_app_clean_target_candidate 到此结束；如果没有这个边界说明，读者不容易看出启动目标筛选范围。

    def _launch_app_safe_prefix_from_polluted_candidate(self, text: str) -> str:  # 新增代码+LaunchTargetRepairPollution: 函数段开始，从模型 JSON 修复污染串中恢复受控应用别名；如果没有这段函数，真实终端里 mspaint 前缀会被坏尾巴拖成缺参失败。
        normalized_text = text.lower()  # 新增代码+LaunchTargetRepairPollution: 统一小写用于匹配安全别名；如果没有这行代码，`MSPAINT}}]` 这类大小写变化无法恢复。
        safe_aliases = ("mspaint.exe", "notepad.exe", "calc.exe", "obsidian.exe", "mspaint", "notepad", "paint", "calc", "obsidian")  # 新增代码+LaunchTargetRepairPollution: 只允许项目已验证过的普通应用别名前缀；如果没有这行代码，任意文本前缀都可能被误恢复成启动目标。
        pollution_markers = ("}", "]", "{", "[", "need valid json", "i accidentally", "final", "json", "，", "。", "；", "！", "？", "、", ",", ";", "!", "?", "：", ":")  # 新增代码+LaunchTargetRepairPollution: 定义真实日志和模型自我纠错常见污染信号；如果没有这行代码，函数无法区分污染尾巴和真实应用名。
        for alias in safe_aliases:  # 新增代码+LaunchTargetRepairPollution: 逐个尝试最长优先的安全别名；如果没有这行代码，无法从 mspaint/notepad 等目标中选择命中的别名。
            if normalized_text == alias:  # 新增代码+LaunchTargetRepairPollution: 完全等于安全别名时直接接受；如果没有这行代码，干净别名会继续走后面的污染判断。
                return alias  # 新增代码+LaunchTargetRepairPollution: 返回规范小写别名；如果没有这行代码，完全匹配也无法快速返回。
            if not normalized_text.startswith(alias):  # 新增代码+LaunchTargetRepairPollution: 当前安全别名不是前缀时跳过；如果没有这行代码，所有 alias 都会误处理同一个文本。
                continue  # 新增代码+LaunchTargetRepairPollution: 继续检查下一个安全别名；如果没有这行代码，第一个不匹配别名会中断恢复。
            tail = text[len(alias) :].strip()  # 新增代码+LaunchTargetRepairPollution: 取出安全前缀后面的尾巴；如果没有这行代码，无法判断后半段是污染还是合法应用名。
            if not tail:  # 新增代码+LaunchTargetRepairPollution: 没有尾巴说明就是干净前缀；如果没有这行代码，空尾巴会继续做无意义污染匹配。
                return alias  # 新增代码+LaunchTargetRepairPollution: 返回干净安全别名；如果没有这行代码，干净前缀可能被后续逻辑误拒绝。
            first_tail_character = tail[0]  # 新增代码+LaunchTargetRepairPollution: 读取尾巴第一个字符；如果没有这行代码，无法拒绝 `mspainting` 这类普通单词扩展。
            if first_tail_character.isalnum() or first_tail_character in {"_", "-"}:  # 新增代码+LaunchTargetRepairPollution: 字母数字或连接符紧跟别名时视为另一个名称；如果没有这行代码，`mspaintowy` 可能被误恢复成 mspaint。
                continue  # 新增代码+LaunchTargetRepairPollution: 跳过这种不安全前缀恢复；如果没有这行代码，模型猜错的应用名会被强行改成安全别名。
            lowered_tail = tail.lower()  # 新增代码+LaunchTargetRepairPollution: 小写尾巴用于匹配英文污染词；如果没有这行代码，`Need valid JSON` 大小写变化会漏判。
            if any(marker in lowered_tail or marker in tail for marker in pollution_markers):  # 新增代码+LaunchTargetRepairPollution: 只有尾巴含污染信号才恢复；如果没有这行代码，普通未知应用名可能被过度截断。
                return alias  # 新增代码+LaunchTargetRepairPollution: 返回安全应用别名；如果没有这行代码，真实 mspaint 污染串仍不能恢复。
        return ""  # 新增代码+LaunchTargetRepairPollution: 没有安全恢复结果时返回空；如果没有这行代码，调用方无法区分未命中和命中空目标。
    # 新增代码+LaunchTargetRepairPollution: 函数段结束，_launch_app_safe_prefix_from_polluted_candidate 到此结束；如果没有这个边界说明，用户不容易看出恢复逻辑的安全边界。

    def _launch_app_target_from_arguments(self, arguments: dict[str, Any]) -> str:  # 修改代码+ModelLoopLaunchAppTool: 函数段开始，从动作参数里提取干净应用名；如果没有这段函数，模型不同字段习惯会导致启动目标丢失。
        for field_name in ("target_app", "app", "target", "app_name", "text"):  # 修改代码+LaunchTargetPollutionGate: 优先使用更像结构化别名的字段，再回退到容易被自然语言污染的 app_name；如果没有这行代码，污染 app_name 会盖过干净 target_app。
            candidate = self._launch_app_clean_target_candidate(arguments.get(field_name))  # 修改代码+ModelLoopLaunchAppTool: 清洗当前候选字段；如果没有这行代码，污染的 app_name 会盖过干净的 target_app。
            if candidate:  # 修改代码+ModelLoopLaunchAppTool: 只接受通过安全筛选的候选；如果没有这行代码，坏字段仍会抢先返回。
                return candidate  # 修改代码+ModelLoopLaunchAppTool: 返回第一个干净应用名；如果没有这行代码，controller 不知道该启动哪个软件。
        return ""  # 新增代码+ModelLoopLaunchAppTool: 没有任何字段时返回空字符串；如果没有这行代码，调用方无法稳定生成缺参错误。
    # 新增代码+ModelLoopLaunchAppTool: 函数段结束，_launch_app_target_from_arguments 到此结束；如果没有这个边界说明，读者不容易看出目标提取范围。

    def _get_target_session_runtime(self) -> Any:  # 新增代码+ModelLoopLaunchAppTool: 函数段开始，懒加载 launch_app 的通用目标 session runtime；如果没有这段函数，controller 初始化时会过早加载启动依赖。
        if self.target_session_runtime is None:  # 新增代码+ModelLoopLaunchAppTool: 检查是否已有注入 runtime；如果没有这行代码，测试注入会被生产 runtime 覆盖。
            self.target_session_runtime = _build_default_target_session_runtime()  # 新增代码+ModelLoopLaunchAppTool: 构造默认通用目标 session；如果没有这行代码，生产路径无法执行 launch_app。
        return self.target_session_runtime  # 新增代码+ModelLoopLaunchAppTool: 返回可调用 runtime；如果没有这行代码，调用方拿不到执行主体。
    # 新增代码+ModelLoopLaunchAppTool: 函数段结束，_get_target_session_runtime 到此结束；如果没有这个边界说明，读者不容易看出 runtime 懒加载范围。

    def _fresh_target_visible_windows(self) -> list[dict[str, Any]]:  # 新增代码+FreshTargetPolicy：函数段开始，读取启动前可见窗口列表；如果没有这段函数，launch_app 无法先发现用户已打开的软件。
        probe = self.backend.observe("list_windows", {"validation_only": True, "reason": "fresh_target_preflight"})  # 新增代码+FreshTargetPolicy：通过只读后端获取窗口列表；如果没有这一行，controller 只能盲目启动并可能接管旧窗口。
        if not probe.ok:  # 新增代码+FreshTargetPolicy：只在后端明确成功时使用窗口列表；如果没有这一行，失败结果可能被误当成空桌面。
            return []  # 新增代码+FreshTargetPolicy：后端不可用时交给启动后门禁兜底；如果没有这一行，预检失败会中断所有通用应用。
        raw_windows = probe.data.get("windows", []) if isinstance(probe.data, dict) else []  # 新增代码+FreshTargetPolicy：从观察结果读取 windows 字段；如果没有这一行，坏 data 类型会让预检崩溃。
        return [dict(window) for window in list(raw_windows or []) if isinstance(window, dict)]  # 新增代码+FreshTargetPolicy：返回窗口字典副本列表；如果没有这一行，策略可能污染后端观察结果。
    # 新增代码+FreshTargetPolicy：函数段结束，_fresh_target_visible_windows 到此结束；如果没有这个边界说明，用户不容易看出预检观察范围。

    def _execute_launch_app_action(self, action: str, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+ModelLoopLaunchAppTool: 函数段开始，执行模型主循环的启动应用动作；如果没有这段函数，launch_app 会被错误交给鼠标键盘后端。
        target_app = self._launch_app_target_from_arguments(arguments)  # 新增代码+ModelLoopLaunchAppTool: 提取模型要打开的软件名；如果没有这行代码，通用 session 不知道启动哪个应用。
        if not target_app:  # 新增代码+ModelLoopLaunchAppTool: 检查应用名是否缺失；如果没有这行代码，空目标可能进入通用发现并产生误导报告。
            result = ComputerUseActionResult(False, "launch_app 缺少 app_name/target_app/app/target 参数，已拒绝启动应用。", {"action": action, "required_any_of": ["app_name", "target_app", "app", "target"]})  # 新增代码+ModelLoopLaunchAppTool: 构造缺参拒绝结果；如果没有这行代码，模型不知道如何修正工具调用。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+ModelLoopLaunchAppTool: 记录缺参审计；如果没有这行代码，真实终端无法复盘为什么没启动。
            return self._with_audit(result, event)  # 新增代码+ModelLoopLaunchAppTool: 返回带审计 id 的缺参结果；如果没有这行代码，工具输出无法关联日志。
        if self.lock_manager is not None and not self.lock_manager.has_lock(self.owner_session_id) and self.auto_acquire_lock:  # 新增代码+ModelLoopLaunchAppTool: 真实启动前尝试获取桌面控制锁；如果没有这行代码，多个会话可能同时启动和控制应用。
            acquire_result = self.lock_manager.acquire(self.owner_session_id, owner_label="learning_agent_controller")  # 新增代码+ModelLoopLaunchAppTool: 以当前 controller 会话取锁；如果没有这行代码，后续 has_lock 仍然失败。
            if not acquire_result.get("acquired", False):  # 新增代码+ModelLoopLaunchAppTool: 判断自动取锁是否失败；如果没有这行代码，抢锁失败也可能继续启动应用。
                result = ComputerUseActionResult(False, "无法获取 desktop control lock，已拒绝启动应用。", {"action": action, "target_app": target_app, "lock": acquire_result.get("status", {})})  # 新增代码+ModelLoopLaunchAppTool: 构造取锁失败结果；如果没有这行代码，模型不知道启动为何被拒绝。
                event = self._record_audit(action, False, result.message, arguments)  # 新增代码+ModelLoopLaunchAppTool: 记录取锁失败审计；如果没有这行代码，锁冲突无法复盘。
                return self._with_audit(result, event)  # 新增代码+ModelLoopLaunchAppTool: 返回带审计 id 的取锁失败结果；如果没有这行代码，工具输出无法关联日志。
        if self.lock_manager is not None and not self.lock_manager.has_lock(self.owner_session_id):  # 新增代码+ModelLoopLaunchAppTool: 启动前要求当前会话持锁；如果没有这行代码，真实启动可能绕过桌面控制互斥。
            result = ComputerUseActionResult(False, "缺少当前会话的 desktop control lock，已拒绝启动应用。", {"action": action, "target_app": target_app, "lock": self.lock_manager.status()})  # 新增代码+ModelLoopLaunchAppTool: 构造缺锁拒绝结果；如果没有这行代码，模型看不到该如何恢复。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+ModelLoopLaunchAppTool: 记录缺锁审计；如果没有这行代码，安全拒绝不会进入状态摘要。
            return self._with_audit(result, event)  # 新增代码+ModelLoopLaunchAppTool: 返回带审计 id 的缺锁结果；如果没有这行代码，调用方无法关联审计。
        if self.lock_manager is not None and self.lock_manager.is_abort_requested():  # 新增代码+ModelLoopLaunchAppTool: 启动前检查急停标记；如果没有这行代码，用户 abort 后仍可能打开新软件。
            result = ComputerUseActionResult(False, "desktop control abort flag 已触发，已拒绝启动应用。", {"action": action, "target_app": target_app, "abort": self.lock_manager.abort_status()})  # 新增代码+ModelLoopLaunchAppTool: 构造急停拒绝结果；如果没有这行代码，abort 拦截没有稳定返回。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+ModelLoopLaunchAppTool: 记录急停拒绝审计；如果没有这行代码，用户无法确认 abort 生效。
            return self._with_audit(result, event)  # 新增代码+ModelLoopLaunchAppTool: 返回带审计 id 的急停结果；如果没有这行代码，工具输出无法关联日志。
        prelaunch_windows = self._fresh_target_visible_windows()  # 新增代码+FreshTargetPolicy：启动前读取当前可见窗口；如果没有这一行，controller 无法发现目标软件已经打开。
        explicit_existing_window_request = bool(arguments.get("explicit_existing_window_request") or arguments.get("use_existing_window") or arguments.get("reuse_existing_window"))  # 新增代码+FreshTargetPolicy：识别用户是否明确要求使用已有窗口；如果没有这一行，所有旧窗口都会被默认当未授权。
        user_authorized_window = bool(arguments.get("user_authorized_window", False))  # 新增代码+FreshTargetPolicy：读取用户是否授权已有窗口；如果没有这一行，controller 无法区分授权旧窗口和误接管。
        fresh_preflight = decide_fresh_target_preflight(target_app, prelaunch_windows, explicit_existing_window_request=explicit_existing_window_request, user_authorized_window=user_authorized_window)  # 新增代码+FreshTargetPolicy：执行启动前 FreshTarget 硬门禁；如果没有这一行，旧窗口风险只能靠动态提示词约束。
        if not bool(fresh_preflight.get("allowed", False)):  # 新增代码+FreshTargetPolicy：检查预检是否拒绝本次启动；如果没有这一行，拒绝报告会被忽略继续启动。
            data = {"action": action, "action_class": "launch_app", "target_app": target_app, "fresh_target_preflight": dict(fresh_preflight), "fresh_target_decision": str(fresh_preflight.get("decision", "")), "fresh_target_class": str(fresh_preflight.get("fresh_target_class", "")), "existing_target_window_count": int(fresh_preflight.get("existing_target_window_count", 0) or 0), "requires_user_to_close_existing_app": bool(fresh_preflight.get("requires_user_to_close_existing_app", False)), "allows_explicit_existing_window_authorization": bool(fresh_preflight.get("allows_explicit_existing_window_authorization", False)), "target_ref": "", "target_lease": {}, "target_resolution_source": "fresh_target_preflight_rejected", "target_resolution_error": str(fresh_preflight.get("decision", "")), "recovery_next_allowed_actions": ["observe", "launch_app"], "real_desktop_touched": False, "low_level_event_count": 0}  # 新增代码+FreshTargetPolicy：构造旧窗口预检零事件拒绝数据；如果没有这一行，模型不知道如何恢复。
            result = ComputerUseActionResult(False, str(fresh_preflight.get("message") or "检测到目标软件已有窗口，已拒绝默认接管旧窗口。"), data)  # 新增代码+FreshTargetPolicy：返回中文拒绝说明；如果没有这一行，用户只会看到模糊失败。
            event = self._record_audit(action, False, result.message, {"action": action, "target_app": target_app, "fresh_target_decision": fresh_preflight.get("decision", "")})  # 新增代码+FreshTargetPolicy：记录预检拒绝审计；如果没有这一行，状态里无法复盘为什么没启动。
            return self._with_audit(result, event)  # 新增代码+FreshTargetPolicy：返回带 audit_id 的预检拒绝；如果没有这一行，工具输出无法关联审计。
        runtime = self._get_target_session_runtime()  # 新增代码+ModelLoopLaunchAppTool: 获取通用目标 session runtime；如果没有这行代码，启动动作没有执行主体。
        open_method = getattr(runtime, "open_target_session", None)  # 新增代码+ModelLoopLaunchAppTool: 读取 runtime 的统一启动/绑定入口；如果没有这行代码，坏 runtime 会变成难懂异常。
        if not callable(open_method):  # 新增代码+ModelLoopLaunchAppTool: 检查 runtime 是否实现入口；如果没有这行代码，错误注入对象可能让 agent 崩溃。
            result = ComputerUseActionResult(False, "launch_app 失败：target session runtime 缺少 open_target_session 方法。", {"action": action, "target_app": target_app})  # 新增代码+ModelLoopLaunchAppTool: 构造 runtime 缺失结果；如果没有这行代码，用户看不到修复方向。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+ModelLoopLaunchAppTool: 记录 runtime 缺失审计；如果没有这行代码，状态里没有失败原因。
            return self._with_audit(result, event)  # 新增代码+ModelLoopLaunchAppTool: 返回带审计 id 的 runtime 缺失结果；如果没有这行代码，工具输出无法关联日志。
        session_report = dict(open_method(target_app, user_authorized_window=user_authorized_window))  # 修改代码+FreshTargetPolicy：调用通用目标 session 并传入用户授权状态；如果没有这行代码，授权旧窗口和默认旧窗口会被混淆。
        session_report.setdefault("fresh_target_preflight", dict(fresh_preflight))  # 新增代码+FreshTargetPolicy：把启动前预检报告写入 session；如果没有这一行，最终结果缺少旧窗口预检证据。
        session_report.setdefault("fresh_target_decision", str(fresh_preflight.get("decision", "")))  # 新增代码+FreshTargetPolicy：缺启动后字段时用预检决策兜底；如果没有这一行，fake runtime 的租约会缺 FreshTarget token。
        session_report.setdefault("fresh_target_class", str(fresh_preflight.get("fresh_target_class", "")))  # 新增代码+FreshTargetPolicy：缺启动后分类时用预检分类兜底；如果没有这一行，测试 runtime 输出不完整。
        session_report.setdefault("fresh_target_identity_verified", bool(fresh_preflight.get("allowed", False)))  # 新增代码+FreshTargetPolicy：缺启动后验证时用预检通过状态兜底；如果没有这一行，租约报告会缺新鲜度字段。
        session_report.setdefault("target_window_existed_before_launch", False)  # 新增代码+FreshTargetPolicy：缺启动后字段时默认未发现旧窗口；如果没有这一行，压力测试字段可能不存在。
        launch_ok = bool(session_report.get("session_ready"))  # 新增代码+ModelLoopLaunchAppTool: 读取 session 是否就绪；如果没有这行代码，后续无法统一判断启动成功。
        target_window = dict(session_report.get("target_window", {}) or {})  # 新增代码+TargetRegistryRootRemediation: 复制 launch_app 绑定出的目标窗口；如果没有这一行，后续 registry 和兼容字段会反复读取原始可变报告。
        target_ref = ""  # 新增代码+TargetRegistryRootRemediation: 先准备空 target_ref 兼容失败启动；如果没有这一行，失败路径仍可能引用未定义变量。
        target_lease = {}  # 新增代码+ControllerTargetLease：先准备空租约兼容失败启动；如果没有这一行，失败路径无法稳定返回 target_lease 字段。
        if launch_ok and target_window:  # 修改代码+TargetRegistryRootRemediation: 只在 session 成功且有窗口时注册 active target；如果没有这一行，空窗口也会污染 registry。
            lease_origin = "user_granted_existing_window" if bool(arguments.get("user_authorized_window", False)) else "agent_owned_launch"  # 新增代码+ControllerTargetLease：区分用户授权旧窗口和 agent 自启动窗口；如果没有这一行，controller 会误把两类权限来源混在一起。
            draft_lease = build_target_lease(session_id=self.owner_session_id, target_ref="", origin=lease_origin, launch_result=session_report, target_window=target_window, user_granted_existing_window=bool(arguments.get("user_authorized_window", False)))  # 新增代码+ControllerTargetLease：先构造不带 ref 的租约草稿；如果没有这一行，registry 无法同时托管窗口和权限凭证。
            target_ref = self.target_registry.register_target(target_window, source_action="launch_app", lease=draft_lease)  # 修改代码+ControllerTargetLease：把 raw target_window 和租约托管成短 ref；如果没有这一行，模型后续仍要复制大窗口字典且缺少权限来源。
            active_target = self.target_registry.get_active_target()  # 新增代码+ControllerTargetLease：读取 registry 回填 target_ref 后的目标记录；如果没有这一行，返回给模型的 lease 可能缺少最终 ref。
            target_lease = dict(active_target.get("lease", {})) if isinstance(active_target, dict) and isinstance(active_target.get("lease", {}), dict) else draft_lease.to_dict()  # 新增代码+ControllerTargetLease：取得最终租约报告；如果没有这一行，controller 结果和 registry 记录可能不一致。
            self.active_target_lease = dict(target_lease)  # 新增代码+ControllerTargetLease：保存当前 active lease 供显式 window 写动作校验；如果没有这一行，错误窗口漂移没有权限基准。
            self.active_agent_owned_target_window = dict(target_window)  # 修改代码+TargetRegistryRootRemediation: 保存本次 agent-owned target_window；如果没有这行代码，后续漂移门禁没有基准。
            session_report["target_ref"] = target_ref  # 新增代码+TargetRegistryRootRemediation: 把短 ref 回写进 session 报告；如果没有这一行，日志里无法追踪 launch 生成了哪个 ref。
            session_report["target_lease"] = dict(target_lease)  # 新增代码+ControllerTargetLease：把租约回写进 session 报告；如果没有这一行，launch_app 审计里看不到权限凭证。
        fresh_target_freshness = dict(session_report.get("fresh_target_freshness", {})) if isinstance(session_report.get("fresh_target_freshness", {}), dict) else {}  # 新增代码+FreshTargetPolicy：读取启动后 FreshTarget 报告；如果没有这一行，data 需要重复解析 session 嵌套对象。
        data = {"action": action, "action_class": "launch_app", "target_app": target_app, "session": session_report, "fresh_target_preflight": dict(fresh_preflight), "fresh_target_freshness": fresh_target_freshness, "fresh_target_decision": str(session_report.get("fresh_target_decision", fresh_preflight.get("decision", ""))), "fresh_target_class": str(session_report.get("fresh_target_class", fresh_preflight.get("fresh_target_class", ""))), "fresh_target_identity_verified": bool(session_report.get("fresh_target_identity_verified", False)), "target_window_existed_before_launch": bool(session_report.get("target_window_existed_before_launch", False)), "old_window_default_takeover": bool(session_report.get("target_window_existed_before_launch", False) and not user_authorized_window), "target_ref": target_ref, "target_lease": target_lease, "resolved_target_ref": target_ref, "resolved_target_window_present": bool(target_window), "target_resolution_source": "launch_app" if launch_ok and target_window else "launch_app_failed", "target_resolution_error": "" if launch_ok and target_window else str(session_report.get("fresh_target_decision") or "target_window_missing"), "recovery_next_allowed_actions": [] if launch_ok and target_window else self._target_resolution_recovery_actions(), "target_window": target_window, "proxy_window_bound": bool(session_report.get("proxy_window_bound")), "proxy_window_binding": session_report.get("proxy_window_binding", {}), "window_binding_reason": str(session_report.get("window_binding_reason", "")), "window_binding_confidence": str(session_report.get("window_binding_confidence", "")), "external_app_window_bound": bool(launch_ok and target_window), "real_desktop_touched": bool(session_report.get("real_desktop_touched")), "low_level_event_count": int(session_report.get("low_level_event_count", 0) or 0)}  # 修改代码+FreshTargetPolicy：生成带 target_ref、target_lease 和 FreshTarget 证据的启动结果；如果没有这一行，模型不知道下一步可用短 ref，也看不到新旧窗口来源。
        message = "应用启动并完成目标窗口绑定。" if launch_ok else "应用启动或目标窗口绑定失败。"  # 新增代码+ModelLoopLaunchAppTool: 生成简明中文结果；如果没有这行代码，用户只能读复杂 JSON 判断成败。
        result = ComputerUseActionResult(launch_ok, message, data)  # 新增代码+ModelLoopLaunchAppTool: 构造统一动作结果；如果没有这行代码，controller 无法复用 to_text/audit 流程。
        event = self._record_audit(action, result.ok, result.message, {"action": action, "target_app": target_app})  # 新增代码+ModelLoopLaunchAppTool: 记录脱敏启动审计；如果没有这行代码，启动应用事实不会进入状态摘要。
        return self._with_audit(result, event)  # 新增代码+ModelLoopLaunchAppTool: 返回带审计 id 的启动结果；如果没有这行代码，模型无法把启动结果和审计关联。
    # 新增代码+ModelLoopLaunchAppTool: 函数段结束，_execute_launch_app_action 到此结束；如果没有这个边界说明，读者不容易看出启动动作范围。

    def execute(self, arguments: dict[str, Any]) -> ComputerUseActionResult:  # 新增代码+OSComputerUse: 执行一次经过安全检查的桌面动作；若没有这段代码，computer_action 工具没有统一入口。
        action = str(arguments.get("action", "")).strip()  # 新增代码+OSComputerUse: 读取并清理动作名；若没有这行代码，空白动作名会进入后端。
        if action not in self.ALLOWED_ACTIONS:  # 新增代码+OSComputerUse: 拒绝未知动作；若没有这行代码，后端可能收到未设计过的危险指令。
            result = ComputerUseActionResult(False, f"不支持的 Computer Use 动作：{action}", {"allowed_actions": sorted(self.ALLOWED_ACTIONS)})  # 修改代码+Phase20ComputerUse: 先构造拒绝结果再附加审计 id；如果没有这行代码，未知动作拒绝无法被追踪。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase20ComputerUse: 记录未知动作拒绝事件；如果没有这行代码，高风险异常调用不会进入审计日志。
            return self._with_audit(result, event)  # 修改代码+Phase20ComputerUse: 返回带审计 id 的拒绝结果；如果没有这行代码，工具输出和审计日志无法关联。
        if arguments.get("confirm_desktop_control") is not True:  # 新增代码+OSComputerUse: 要求模型显式承认这是桌面控制；若没有这行代码，高风险动作可能被无意触发。
            result = ComputerUseActionResult(False, "缺少 confirm_desktop_control=true，已拒绝执行真实桌面动作。", {"action": action})  # 修改代码+Phase20ComputerUse: 先构造缺少确认的拒绝结果；如果没有这行代码，确认门禁失败没有稳定结果对象。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase20ComputerUse: 记录缺少确认的拒绝事件；如果没有这行代码，安全门禁触发后无法复盘原因。
            return self._with_audit(result, event)  # 修改代码+Phase20ComputerUse: 返回带审计 id 的门禁拒绝结果；如果没有这行代码，用户无法定位这次拒绝事件。
        if action == "launch_app":  # 新增代码+ModelLoopLaunchAppTool: 将启动应用动作分发到通用目标 session；如果没有这行代码，launch_app 会错误进入鼠标键盘后端或窗口校验。
            return self._execute_launch_app_action(action, arguments)  # 新增代码+ModelLoopLaunchAppTool: 返回启动/绑定结果；如果没有这行代码，模型无法自己打开 Paint 等本机应用。
        text = str(arguments.get("text", ""))  # 新增代码+OSComputerUse: 读取可选输入文本；若没有这行代码，type_text 长度无法被检查。
        if action == "type_text" and len(text) > self.MAX_TEXT_LENGTH:  # 新增代码+OSComputerUse: 限制输入文本长度；若没有这行代码，过长文本可能污染桌面输入目标。
            result = ComputerUseActionResult(False, f"type_text 文本过长，最多 {self.MAX_TEXT_LENGTH} 字符。", {"action": action, "text_length": len(text)})  # 修改代码+Phase20ComputerUse: 先构造长度拒绝结果；如果没有这行代码，过长文本拒绝无法携带审计 id。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase20ComputerUse: 记录文本过长拒绝事件；如果没有这行代码，输入保护触发后无法审计。
            return self._with_audit(result, event)  # 修改代码+Phase20ComputerUse: 返回带审计 id 的长度拒绝结果；如果没有这行代码，调用方无法关联保护事件。
        target_resolution = self._resolve_action_target(action, arguments)  # 新增代码+TargetRegistryRootRemediation: 在所有写动作安全门禁前统一解析目标；如果没有这一行，S2 仍会因为模型漏传 window 而失败。
        if not bool(target_resolution.get("ok", False)):  # 新增代码+TargetRegistryRootRemediation: 判断 target_ref/window 解析是否失败；如果没有这一行，坏 target_ref 可能继续进入真实后端。
            return self._target_resolution_failure_result(action, arguments, target_resolution)  # 新增代码+TargetRegistryRootRemediation: 结构化拒绝错误目标且不派发底层事件；如果没有这一行，失败路径无法给模型恢复动作。
        arguments = dict(target_resolution.get("arguments", arguments))  # 新增代码+TargetRegistryRootRemediation: 用注入后的参数继续后续门禁和执行；如果没有这一行，active target 只会出现在报告里而不会传给后端。
        lease_rejection = self._reject_invalid_target_lease(action, arguments, target_resolution)  # 新增代码+ControllerTargetLease：在 approval、漂移和后端执行前先校验通用目标租约；如果没有这一行，target_ref 可以绕过权限来源直接写窗口。
        if lease_rejection is not None:  # 新增代码+ControllerTargetLease：判断 TargetLease 门禁是否拒绝本次动作；如果没有这一行，拒绝结果会被忽略。
            return lease_rejection  # 新增代码+ControllerTargetLease：直接返回租约拒绝且不调用真实后端；如果没有这一行，错窗口仍可能收到鼠标键盘事件。
        approval_rejection = self._reject_unapproved_action(action, arguments)  # 新增代码+Phase38WindowsComputerApproval: 在真实后端前先执行 approval 拦截；如果没有这行代码，禁止目标和未授权 app 仍可能进入后端。
        if approval_rejection is not None:  # 新增代码+Phase38WindowsComputerApproval: 判断 approval 是否拒绝本次动作；如果没有这行代码，拒绝结果会被忽略。
            return approval_rejection  # 新增代码+Phase38WindowsComputerApproval: 返回审批拒绝而不调用后端；如果没有这行代码，表面拒绝但后端仍可能执行。
        drift_rejection = self._reject_agent_owned_target_drift(action, arguments)  # 新增代码+ModelLoopLaunchAppTool: 在窗口存在性校验前阻断漂移到旧窗口；如果没有这行代码，模型会在新开窗口后误操作旧 Paint。
        if drift_rejection is not None:  # 新增代码+ModelLoopLaunchAppTool: 判断是否命中 agent-owned 目标漂移；如果没有这行代码，拒绝结果会被忽略。
            return drift_rejection  # 新增代码+ModelLoopLaunchAppTool: 返回漂移拒绝且不调用后端；如果没有这行代码，拒绝后仍可能发送鼠标键盘事件。
        window_rejection = self._reject_unknown_window_target(action, arguments)  # 新增代码+Phase27ComputerUse: 在执行写动作前检查窗口目标是否可信；如果没有这行代码，未知窗口可能被传给真实后端。
        if window_rejection is not None:  # 新增代码+Phase27ComputerUse: 判断窗口校验是否产生拒绝结果；如果没有这行代码，拒绝结果会被忽略。
            return window_rejection  # 新增代码+Phase27ComputerUse: 返回未知窗口拒绝而不调用后端；如果没有这行代码，后端仍可能执行危险动作。
        if self.lock_manager is not None and action != "screenshot" and arguments.get("window") is None:  # 新增代码+Phase30ComputerUseActionGate: 在启用锁门禁时要求写动作绑定可信窗口；如果没有这行代码，真实鼠标键盘可能回到全屏裸坐标模式。
            result = ComputerUseActionResult(False, "缺少可信 window：启用 Phase 30 动作门禁后，请先调用 mcp__computer-use__observe 获取窗口目标。", {"action": action})  # 修改代码+McpObservedWindowFix: 构造缺少窗口的 v2 工具面拒绝结果；如果没有这行代码，模型会被隐藏旧观察接口名称引回不可见接口。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase30ComputerUseActionGate: 记录缺少窗口的拒绝审计；如果没有这行代码，门禁拒绝无法复盘。
            return self._with_audit(result, event)  # 新增代码+Phase30ComputerUseActionGate: 返回带审计 id 的拒绝结果；如果没有这行代码，工具输出无法关联状态审计。
        if self.lock_manager is not None and not self.lock_manager.has_lock(self.owner_session_id) and self.auto_acquire_lock:  # 新增代码+Phase30ComputerUseActionGate: 生产默认路径在无人持有时尝试自动取锁；如果没有这行代码，真实 agent 默认动作会永远缺少当前锁。
            acquire_result = self.lock_manager.acquire(self.owner_session_id, owner_label="learning_agent_controller")  # 新增代码+Phase30ComputerUseActionGate: 用当前会话获取 durable lock；如果没有这行代码，后续 has_lock 仍然失败。
            if not acquire_result.get("acquired", False):  # 新增代码+Phase30ComputerUseActionGate: 判断自动取锁是否被其他 session 拒绝；如果没有这行代码，抢锁失败可能继续执行动作。
                result = ComputerUseActionResult(False, "无法获取 desktop control lock，已拒绝执行桌面动作。", {"action": action, "lock": acquire_result.get("status", {})})  # 新增代码+Phase30ComputerUseActionGate: 构造自动取锁失败结果；如果没有这行代码，模型不知道动作为何被拦截。
                event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase30ComputerUseActionGate: 记录取锁失败审计；如果没有这行代码，锁冲突无法复盘。
                return self._with_audit(result, event)  # 新增代码+Phase30ComputerUseActionGate: 返回带审计 id 的取锁失败结果；如果没有这行代码，工具输出无法关联审计。
        if self.lock_manager is not None and not self.lock_manager.has_lock(self.owner_session_id):  # 新增代码+Phase30ComputerUseActionGate: 要求当前会话持有 durable desktop lock；如果没有这行代码，两个会话可能同时控制桌面。
            lock_status = self.lock_manager.status()  # 新增代码+Phase30ComputerUseActionGate: 读取当前锁状态用于返回给模型；如果没有这行代码，用户不知道是谁持有锁。
            result = ComputerUseActionResult(False, "缺少当前会话的 desktop control lock，已拒绝执行桌面动作。", {"action": action, "lock": lock_status})  # 新增代码+Phase30ComputerUseActionGate: 构造缺锁拒绝结果；如果没有这行代码，锁门禁失败没有可读解释。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase30ComputerUseActionGate: 记录缺锁拒绝审计；如果没有这行代码，安全拦截无法在 status 中复盘。
            return self._with_audit(result, event)  # 新增代码+Phase30ComputerUseActionGate: 返回带审计 id 的缺锁结果；如果没有这行代码，调用方无法关联这次拦截。
        if self.lock_manager is not None and self.lock_manager.is_abort_requested():  # 新增代码+Phase30ComputerUseActionGate: 在调用后端前检查急停标记；如果没有这行代码，用户请求 abort 后下一次动作仍可能执行。
            abort_status = self.lock_manager.abort_status()  # 新增代码+Phase30ComputerUseActionGate: 读取 abort 摘要用于结果说明；如果没有这行代码，模型不知道急停原因。
            result = ComputerUseActionResult(False, "desktop control abort flag 已触发，已拒绝执行下一次桌面动作。", {"action": action, "abort": abort_status})  # 新增代码+Phase30ComputerUseActionGate: 构造急停拒绝结果；如果没有这行代码，abort 拦截没有稳定返回对象。
            event = self._record_audit(action, False, result.message, arguments)  # 新增代码+Phase30ComputerUseActionGate: 记录急停拒绝审计；如果没有这行代码，用户无法确认 abort 生效。
            return self._with_audit(result, event)  # 新增代码+Phase30ComputerUseActionGate: 返回带审计 id 的急停结果；如果没有这行代码，调用方无法关联这次中止。
        lock_status = self.lock_manager.status() if self.lock_manager is not None else {"enabled": False, "owner_session_id": self.owner_session_id}  # 新增代码+Phase30ComputerUseActionGate: 准备动作证据里的锁状态；如果没有这行代码，action evidence 无法说明持锁会话。
        prepared_action = prepare_action_arguments(action, arguments)  # 新增代码+Phase30ComputerUseActionGate: 转换窗口相对坐标并准备后端参数；如果没有这行代码，真实后端可能收到错误坐标空间。
        backend_arguments = dict(prepared_action["backend_arguments"])  # 新增代码+Phase30ComputerUseActionGate: 复制最终后端参数；如果没有这行代码，后续审计和后端可能共享可变对象。
        before_evidence = self._capture_action_window_evidence("before", "", arguments)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 在后端执行前采集窗口状态；如果没有这行代码，动作证据无法证明执行前现场。
        result = self.backend.execute(action, backend_arguments)  # 修改代码+Phase30ComputerUseActionGate: 把通过门禁且已转换坐标的动作交给后端；若没有这行代码，Computer Use 永远不会执行到后端。
        after_evidence = self._capture_action_window_evidence("after", "", arguments)  # 新增代码+Phase31ComputerUseLockAbortEvidence: 在后端执行后采集窗口状态；如果没有这行代码，动作证据无法证明执行后现场。
        action_evidence = build_action_evidence(action, arguments, prepared_action, lock_status)  # 新增代码+Phase30ComputerUseActionGate: 生成动作证据 envelope；如果没有这行代码，结果无法关联窗口、坐标、锁和策略版本。
        action_evidence["before_evidence"] = before_evidence  # 新增代码+Phase31ComputerUseLockAbortEvidence: 把动作前现场放进证据 envelope；如果没有这行代码，落盘链路没有 before 节点。
        action_evidence["after_evidence"] = after_evidence  # 新增代码+Phase31ComputerUseLockAbortEvidence: 把动作后现场放进证据 envelope；如果没有这行代码，落盘链路没有 after 节点。
        event = self._record_audit(action, result.ok, result.message, backend_arguments)  # 修改代码+Phase30ComputerUseActionGate: 记录脱敏后的最终后端参数；如果没有这行代码，已允许动作没有安全审计闭环。
        audited_result = self._with_audit(result, event, action_evidence)  # 新增代码+TargetRegistryRootRemediation: 先保留原有审计和动作证据；如果没有这一行，追加目标解析信息时可能丢失 audit_id。
        return self._with_target_resolution(audited_result, target_resolution)  # 修改代码+TargetRegistryRootRemediation: 返回同时包含审计和目标解析证据的结果；如果没有这一行，ok=true 仍可能看不出打到了哪个窗口。
