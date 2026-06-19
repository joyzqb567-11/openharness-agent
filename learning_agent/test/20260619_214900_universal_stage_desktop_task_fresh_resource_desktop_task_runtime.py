"""Computer Use full 自然语言桌面任务运行时。"""  # 新增代码+DesktopTaskRuntime：说明本模块负责把自然语言桌面任务编排成 GUI 证据链；如果没有这一行，读者容易误以为这里是某个 Paint 专用脚本。
from __future__ import annotations  # 新增代码+DesktopTaskRuntime：启用延迟类型注解；如果没有这一行，类方法返回自身类型时在不同 Python 版本里更容易出错。

import json  # 新增代码+DesktopTaskRuntime：导入 JSON 用于命令行输出完整报告；如果没有这一行，真实终端失败时只能看短 token。
import tempfile  # 新增代码+DesktopTaskRuntime：导入临时目录工具隔离单元测试状态；如果没有这一行，测试 full mode 状态可能污染用户真实 session。
from pathlib import Path  # 新增代码+DesktopTaskRuntime：导入 Path 统一处理 Windows 路径；如果没有这一行，证据目录拼接会更脆弱。
from typing import Any  # 新增代码+DesktopTaskRuntime：导入 Any 描述 JSON 风格动态报告；如果没有这一行，公开接口的字段边界不清楚。

try:  # 新增代码+DesktopTaskRuntime：优先使用包路径导入既有 Computer Use 组件；如果没有这段代码，项目根运行时无法复用现有模块。
    from learning_agent.computer_use_mcp_v2.windows_runtime.desktop_task_acceptance import evaluate_desktop_task_acceptance  # 新增代码+DesktopTaskRuntime：复用 Task 1 验收器；如果没有这一行，运行时会重复实现成熟门禁且容易漂移。
    from learning_agent.computer_use_mcp_v2.windows_runtime.desktop_task_router import DesktopTaskIntent, classify_desktop_task  # 新增代码+DesktopTaskRuntime：复用 Task 2 自然语言分类器；如果没有这一行，运行时无法知道普通 prompt 是否需要 GUI 路由。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_launch_resolver import resolve_generic_app_launch_target  # 修改代码+CompatSlimming：从统一 resolver 读取通用应用解析；如果没有这一行，旧 discovery 文件删除后 runtime 会断。
    from learning_agent.computer_use_mcp_v2.windows_runtime.generic_launch_backend import prepare_phase109_generic_real_launch_candidate  # 修改代码+CompatSlimming：从通用启动后端读取真实启动候选；如果没有这一行，旧 candidate 文件删除后窗口绑定证据会断。
    from learning_agent.computer_use_mcp_v2.windows_runtime.mode_session import ComputerUseModeSessionStore  # 新增代码+DesktopTaskRuntime：复用 Phase98 full mode session；如果没有这一行，/computer use --full 会变成无事实来源的文字开关。
    from learning_agent.computer_use_mcp_v2.windows_runtime.representative_e2e_matrix import WindowsRepresentativeE2EMatrix  # 新增代码+DesktopTaskRuntime：复用 Phase74 Paint/Pikachu 代表性 GUI 动作证据；如果没有这一行，Task 4 没有绘图动作证据来源。
except ModuleNotFoundError as error:  # 新增代码+DesktopTaskRuntime：兼容 start_oauth_agent.bat 从 learning_agent 目录启动的脚本模式；如果没有这段代码，真实可见终端可能因包名前缀不同而导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.desktop_task_acceptance", "learning_agent.computer_use_mcp_v2.windows_runtime.desktop_task_router", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_launch_resolver", "learning_agent.computer_use_mcp_v2.windows_runtime.generic_launch_backend", "learning_agent.computer_use_mcp_v2.windows_runtime.mode_session", "learning_agent.computer_use_mcp_v2.windows_runtime.representative_e2e_matrix"}:  # 修改代码+CompatSlimming：只在新核心模块包路径缺失时兜底；如果没有这一行，内部真实 bug 会被错误吞掉。
        raise  # 新增代码+DesktopTaskRuntime：重新抛出真实内部导入错误；如果没有这一行，排查依赖模块问题会非常困难。
    from computer_use_mcp_v2.windows_runtime.desktop_task_acceptance import evaluate_desktop_task_acceptance  # type: ignore  # 新增代码+DesktopTaskRuntime：脚本模式复用同一验收器；如果没有这一行，bat 入口无法评估 GUI 路由成熟条件。
    from computer_use_mcp_v2.windows_runtime.desktop_task_router import DesktopTaskIntent, classify_desktop_task  # type: ignore  # 新增代码+DesktopTaskRuntime：脚本模式复用同一分类器；如果没有这一行，bat 入口无法识别自然语言桌面任务。
    from computer_use_mcp_v2.windows_runtime.windows_launch_resolver import resolve_generic_app_launch_target  # type: ignore  # 修改代码+CompatSlimming：脚本模式从统一 resolver 读取通用应用解析；如果没有这一行，bat 入口会丢失泛化应用能力。
    from computer_use_mcp_v2.windows_runtime.generic_launch_backend import prepare_phase109_generic_real_launch_candidate  # type: ignore  # 修改代码+CompatSlimming：脚本模式从通用启动后端读取候选；如果没有这一行，bat 入口无法构造自有窗口证据。
    from computer_use_mcp_v2.windows_runtime.mode_session import ComputerUseModeSessionStore  # type: ignore  # 新增代码+DesktopTaskRuntime：脚本模式复用 full mode session；如果没有这一行，bat 入口无法读取授权状态。
    from computer_use_mcp_v2.windows_runtime.representative_e2e_matrix import WindowsRepresentativeE2EMatrix  # type: ignore  # 新增代码+DesktopTaskRuntime：脚本模式复用代表性 E2E 证据；如果没有这一行，bat 入口无法生成 Paint/Pikachu 动作证据。

COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_READY = "COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_READY"  # 新增代码+DesktopTaskRuntime：定义 Task 4 稳定 ready marker；如果没有这一行，真实终端验收无法可靠定位桌面任务运行时输出。
COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK = "COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK"  # 新增代码+DesktopTaskRuntime：定义 Task 4 成功 token；如果没有这一行，用户和 controller 无法区分成功报告与普通日志。
COMPUTER_USE_FULL_DESKTOP_TASK_RUNTIME_MODEL = "computer_use_full_desktop_task_runtime"  # 新增代码+DesktopTaskRuntime：定义报告模型名；如果没有这一行，后续成熟矩阵无法区分这是运行时证据而不是单项合同。
DEFAULT_DESKTOP_TASK_RUNTIME_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "desktop_task_runtime"  # 新增代码+DesktopTaskRuntime：定义默认受控证据目录；如果没有这一行，运行时证据会散落且难以审计。
_PAINT_APP_HINTS = {"画图", "paint", "Paint", "mspaint", "Microsoft Paint"}  # 新增代码+DesktopTaskRuntime：集中列出 Paint 类目标提示；如果没有这一行，中文画图和英文 Paint 可能不能映射到同一通用目标。


def _desktop_task_runtime_computer_use_locks_root(workspace: str | Path) -> Path:  # 新增代码+DesktopTaskModeStoreAlignment: 函数段开始，按交互层同款规则计算 Computer Use 锁目录；如果没有这段函数，desktop_task 会读写和 /computer use 不同的 mode store。
    workspace_path = Path(workspace)  # 新增代码+DesktopTaskModeStoreAlignment: 把 workspace 统一转成 Path；如果没有这一行，字符串路径无法安全拼接子目录。
    if workspace_path.name == "learning_agent":  # 新增代码+DesktopTaskModeStoreAlignment: 识别 start_oauth_agent.bat 传入 learning_agent 目录的真实终端场景；如果没有这一行，路径会变成双层 learning_agent。
        return workspace_path / "memory" / "computer_use" / "locks"  # 新增代码+DesktopTaskModeStoreAlignment: 返回包目录 workspace 的锁目录；如果没有这一行，高层工具会读不到真实终端打开的 full 状态。
    return workspace_path / "learning_agent" / "memory" / "computer_use" / "locks"  # 新增代码+DesktopTaskModeStoreAlignment: 返回 repo 根 workspace 的锁目录；如果没有这一行，从仓库根启动的测试会找错 mode_sessions。
# 新增代码+DesktopTaskModeStoreAlignment: 函数段结束，_desktop_task_runtime_computer_use_locks_root 到此结束；如果没有这个边界说明，用户不容易看出这是和 interactive.py 对齐的路径逻辑。


def _desktop_task_runtime_bool_token(value: Any) -> str:  # 新增代码+DesktopTaskRuntime：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会出现 True/False 大小写漂移。
    return "true" if bool(value) else "false"  # 新增代码+DesktopTaskRuntime：返回 true 或 false；如果没有这一行，真实终端场景匹配容易失败。
# 新增代码+DesktopTaskRuntime：函数段结束，_desktop_task_runtime_bool_token 到此结束；如果没有这个边界说明，代码小白不容易看出布尔格式化范围。


def _desktop_task_runtime_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+DesktopTaskRuntime：函数段开始，安全读取动作计数字段；如果没有这段函数，坏计数可能让运行时崩溃。
    try:  # 新增代码+DesktopTaskRuntime：尝试把输入转成整数；如果没有这一行，字符串数字和坏值无法被统一处理。
        return int(value)  # 新增代码+DesktopTaskRuntime：返回转换后的整数；如果没有这一行，调用方拿不到可比较计数。
    except (TypeError, ValueError):  # 新增代码+DesktopTaskRuntime：捕获 None、空串、列表等不能转整数的坏值；如果没有这一行，报告字段异常会中断整条任务。
        return default  # 新增代码+DesktopTaskRuntime：坏值时返回默认值；如果没有这一行，运行时无法用 0 表示缺失证据。
# 新增代码+DesktopTaskRuntime：函数段结束，_desktop_task_runtime_safe_int 到此结束；如果没有这个边界说明，代码小白不容易看出计数防线范围。


def _desktop_task_runtime_target_from_intent(intent: DesktopTaskIntent) -> str:  # 新增代码+DesktopTaskRuntime：函数段开始，把分类意图转成通用应用发现目标；如果没有这段函数，中文画图提示不能稳定进入 mspaint 候选。
    target_hint = str(intent.target_app_hint or "").strip()  # 新增代码+DesktopTaskRuntime：读取并清理目标应用提示；如果没有这一行，空格或 None 会影响映射。
    if target_hint in _PAINT_APP_HINTS or target_hint.lower() in {"paint", "mspaint"}:  # 新增代码+DesktopTaskRuntime：把中英文 Paint 提示统一映射为 mspaint；如果没有这一行，中文“画图”会被当成未知 exe。
        return "mspaint"  # 新增代码+DesktopTaskRuntime：返回 Windows 画图的通用目标名；如果没有这一行，Phase108/109 不能稳定生成 Paint 启动候选。
    if target_hint:  # 新增代码+DesktopTaskRuntime：如果有非 Paint 目标提示就保留；如果没有这一行，泛化本地应用目标会丢失。
        return target_hint  # 新增代码+DesktopTaskRuntime：返回分类器提取到的目标提示；如果没有这一行，未知普通应用无法进入通用发现。
    return "desktop_app"  # 新增代码+DesktopTaskRuntime：缺少目标时用保守占位；如果没有这一行，Phase108 会收到空目标并生成不可解释失败。
# 新增代码+DesktopTaskRuntime：函数段结束，_desktop_task_runtime_target_from_intent 到此结束；如果没有这个边界说明，代码小白不容易看出目标映射范围。


def _desktop_task_runtime_forced_intent(intent: DesktopTaskIntent, target_hint: str) -> DesktopTaskIntent:  # 新增代码+DesktopTaskExplicitTool: 函数段开始，把显式 desktop_task 工具调用升级为桌面任务意图；如果没有这段函数，旧分类器会因乱码或复杂表达误判 not_desktop_task。
    clean_target_hint = str(target_hint or intent.target_app_hint or "desktop_app").strip() or "desktop_app"  # 新增代码+DesktopTaskExplicitTool: 优先使用 MCP 工具传下来的授权目标提示；如果没有这一行，Stage Runtime 可能拿 desktop_app 抽象词去启动。
    if intent.is_desktop_task and intent.target_app_hint == clean_target_hint:  # 新增代码+DesktopTaskExplicitTool: 已经是桌面任务且目标一致时直接复用原结果；如果没有这一行，会创建不必要的新对象。
        return intent  # 新增代码+DesktopTaskExplicitTool: 返回原始分类意图；如果没有这一行，正常中文/英文 prompt 也会被重写原因码。
    return DesktopTaskIntent(  # 新增代码+DesktopTaskExplicitTool: 返回强制桌面任务意图；如果没有这一行，显式高层工具仍可能停在 not_desktop_task。
        is_desktop_task=True,  # 新增代码+DesktopTaskExplicitTool: 标记这次明确进入桌面任务路线；如果没有这一项，run_prompt 会继续直接拒绝 GUI 执行。
        reason=intent.reason if intent.is_desktop_task else "forced_explicit_desktop_task_tool",  # 新增代码+DesktopTaskExplicitTool: 保留正常命中原因或记录显式工具强制原因；如果没有这一项，排查时不知道为什么放行。
        target_app_hint=clean_target_hint,  # 新增代码+DesktopTaskExplicitTool: 写入授权目标提示；如果没有这一项，后续 target_app 会变成 desktop_app。
        task_goal=intent.task_goal if intent.is_desktop_task else "desktop_gui_task",  # 新增代码+DesktopTaskExplicitTool: 复用既有目标摘要或使用泛化 GUI 目标；如果没有这一项，报告缺少脱敏任务目标。
        requires_gui_actions=True,  # 新增代码+DesktopTaskExplicitTool: 明确这条路径需要真实 GUI 动作；如果没有这一项，安全层可能把它当普通记录任务。
        controlled_resource_name=intent.controlled_resource_name,  # 新增代码+DesktopTaskExplicitTool: 保留分类器已提取的受控资源名；如果没有这一项，1.txt 等保存目标会在强制路径丢失。
        controlled_resource_location_hint=intent.controlled_resource_location_hint,  # 新增代码+DesktopTaskExplicitTool: 保留受控资源位置提示；如果没有这一项，桌面保存位置会丢失。
        raw_prompt_included=False,  # 新增代码+DesktopTaskExplicitTool: 明确不在 intent 里保存原始 prompt；如果没有这一项，隐私边界会变模糊。
    )  # 新增代码+DesktopTaskExplicitTool: 强制意图对象构造结束；如果没有这一行，Python 调用语法不完整。
# 新增代码+DesktopTaskExplicitTool: 函数段结束，_desktop_task_runtime_forced_intent 到此结束；如果没有这个边界说明，用户不容易看出强制入口范围。


def _desktop_task_runtime_sum_events(draw_actions: Any) -> int:  # 新增代码+DesktopTaskRuntime：函数段开始，统计代表性 GUI 绘制动作里的底层事件数；如果没有这段函数，低层事件证据会缺失。
    if not isinstance(draw_actions, list):  # 新增代码+DesktopTaskRuntime：确认动作集合是列表；如果没有这一行，坏证据可能被错误遍历。
        return 0  # 新增代码+DesktopTaskRuntime：坏动作集合按 0 处理；如果没有这一行，运行时会抛异常而不是给出缺证据报告。
    return sum(_desktop_task_runtime_safe_int(action.get("event_count", 0)) for action in draw_actions if isinstance(action, dict))  # 新增代码+DesktopTaskRuntime：累加每个笔画的事件数；如果没有这一行，验收器无法确认低层鼠标事件大于 0。
# 新增代码+DesktopTaskRuntime：函数段结束，_desktop_task_runtime_sum_events 到此结束；如果没有这个边界说明，代码小白不容易看出事件统计范围。


class ComputerUseDesktopTaskRuntime:  # 新增代码+DesktopTaskRuntime：类段开始，编排自然语言桌面任务到 Computer Use GUI 证据链；如果没有这个类，/computer use --full 只有权限状态而没有任务运行时。
    def __init__(self, base_dir: str | Path | None = None, mode_store: ComputerUseModeSessionStore | None = None, real_execution_loop: Any | None = None) -> None:  # 修改代码+源码复核门禁：函数段开始，初始化运行时依赖并允许注入真实执行闭环；如果没有这段函数，调用方无法注入隔离证据目录和 session store。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_DESKTOP_TASK_RUNTIME_ROOT  # 新增代码+DesktopTaskRuntime：选择调用方目录或默认受控目录；如果没有这一行，证据写入位置不稳定。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+DesktopTaskRuntime：确保证据目录存在；如果没有这一行，代表性矩阵首次写 JSON 会失败。
        self.mode_store = mode_store if mode_store is not None else ComputerUseModeSessionStore()  # 新增代码+DesktopTaskRuntime：保存或创建 full mode session store；如果没有这一行，运行时无法读取 /computer use --full-confirm 的真实状态。
        self.real_execution_loop = real_execution_loop  # 新增代码+源码复核门禁：保存可注入真实执行闭环，默认 None 表示不触碰桌面；如果没有这一行，real_actions=True 只能永久硬拒绝。
    # 新增代码+DesktopTaskRuntime：函数段结束，ComputerUseDesktopTaskRuntime.__init__ 到此结束；如果没有这个边界说明，代码小白不容易看出初始化范围。

    @classmethod  # 新增代码+DesktopTaskRuntime：声明测试构造器属于类方法；如果没有这一行，测试需要手工创建并污染真实 session。
    def for_test(cls, full_mode: bool) -> "ComputerUseDesktopTaskRuntime":  # 新增代码+DesktopTaskRuntime：函数段开始，创建隔离的测试运行时；如果没有这段函数，单元测试无法稳定模拟 full mode 开关。
        base_dir = Path(tempfile.mkdtemp(prefix="learning_agent_desktop_task_runtime_"))  # 新增代码+DesktopTaskRuntime：为本次测试创建独立临时目录；如果没有这一行，测试证据和权限文件会互相污染。
        mode_store = ComputerUseModeSessionStore(base_dir=base_dir / "mode_session")  # 新增代码+DesktopTaskRuntime：把模式状态限制在临时目录；如果没有这一行，测试可能改动用户真实 full mode 状态。
        if full_mode:  # 新增代码+DesktopTaskRuntime：只有需要 full 时才走真实二次确认流程；如果没有这一行，false 场景会被错误授权。
            request = mode_store.request_full_mode(reason="Task4 desktop task runtime test")  # 新增代码+DesktopTaskRuntime：按真实流程申请 full mode token；如果没有这一行，测试会绕过产品的确认机制。
            mode_store.confirm_full_mode(request["confirmation_token"], reason="Task4 desktop task runtime test")  # 新增代码+DesktopTaskRuntime：用 token 激活 full mode；如果没有这一行，正向测试仍会被权限门禁拦住。
        return cls(base_dir=base_dir, mode_store=mode_store)  # 新增代码+DesktopTaskRuntime：返回隔离运行时实例；如果没有这一行，测试拿不到可执行对象。
    # 新增代码+DesktopTaskRuntime：函数段结束，ComputerUseDesktopTaskRuntime.for_test 到此结束；如果没有这个边界说明，代码小白不容易看出测试构造范围。

    def _mode_status(self) -> dict[str, Any]:  # 新增代码+DesktopTaskRuntime：函数段开始，读取当前 full mode 状态；如果没有这段函数，权限判断会散落在 run_prompt 里。
        status = self.mode_store.status()  # 新增代码+DesktopTaskRuntime：向 Phase98 store 读取事实状态；如果没有这一行，运行时可能凭空相信 full mode 已开启。
        return dict(status) if isinstance(status, dict) else {}  # 新增代码+DesktopTaskRuntime：返回字典副本并容错坏返回；如果没有这一行，异常 store 形状会污染后续判断。
    # 新增代码+DesktopTaskRuntime：函数段结束，ComputerUseDesktopTaskRuntime._mode_status 到此结束；如果没有这个边界说明，代码小白不容易看出模式读取范围。

    def _full_mode_session_used(self, status: dict[str, Any]) -> bool:  # 新增代码+DesktopTaskRuntime：函数段开始，判断 full mode 是否真正可用；如果没有这段函数，停止或过期状态可能被误当授权。
        return bool(status.get("full_mode", False) and not status.get("stopped", False) and not status.get("expired", False))  # 新增代码+DesktopTaskRuntime：只有 full、未停止、未过期才算可用；如果没有这一行，过期 full 仍可能进入 GUI 路由。
    # 新增代码+DesktopTaskRuntime：函数段结束，ComputerUseDesktopTaskRuntime._full_mode_session_used 到此结束；如果没有这个边界说明，代码小白不容易看出授权判断范围。

    def _base_report(self, intent: DesktopTaskIntent, mode_status: dict[str, Any], target_app: str) -> dict[str, Any]:  # 新增代码+DesktopTaskRuntime：函数段开始，构造所有分支共享的脱敏报告字段；如果没有这段函数，拒绝和成功路径会重复且容易漏字段。
        full_mode_session_used = self._full_mode_session_used(mode_status)  # 新增代码+DesktopTaskRuntime：计算当前是否使用 full session；如果没有这一行，报告无法解释授权状态。
        return {"marker": COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_READY, "ok_token": "", "model": COMPUTER_USE_FULL_DESKTOP_TASK_RUNTIME_MODEL, "passed": False, "decision": "", "desktop_task_router_used": bool(intent.is_desktop_task), "natural_language_desktop_tasks_route_to_computer_use": bool(intent.is_desktop_task and intent.requires_gui_actions), "computer_use_gui_route_used": False, "full_mode_session_used": full_mode_session_used, "target_app": target_app, "intent": intent.to_dict(), "real_desktop_touched": False, "real_actions_supported": False, "recording_mode": True, "forbidden_script_generation_used": False, "bash_final_artifact_route_used": False, "forbidden_script_artifact_route_blocked": True, "owned_window_verified": False, "gui_action_count": 0, "low_level_event_count": 0, "post_action_screenshot_exists": False, "tool_calls": []}  # 修改代码+源码复核门禁：失败默认不携带 OK token；如果没有这一行，report_json 会在 passed=false 时仍显示成功 token 误导用户。
    # 新增代码+DesktopTaskRuntime：函数段结束，ComputerUseDesktopTaskRuntime._base_report 到此结束；如果没有这个边界说明，代码小白不容易看出基础报告范围。

    def _recording_paint_evidence(self) -> dict[str, Any]:  # 新增代码+DesktopTaskRuntime：函数段开始，生成 Paint/Pikachu 录制模式 GUI 动作证据；如果没有这段函数，Task 4 无法证明 GUI 动作链已接上。
        matrix = WindowsRepresentativeE2EMatrix(base_dir=self.base_dir / "representative_e2e")  # 新增代码+DesktopTaskRuntime：创建隔离的代表性 E2E 矩阵；如果没有这一行，Paint 证据无法落到本运行时目录。
        paint_report = matrix.build_paint_pikachu_scenario(real_smoke=False)  # 新增代码+DesktopTaskRuntime：构建不触碰真实桌面的 Paint/Pikachu 动作证据；如果没有这一行，运行时没有绘图动作事实。
        draw_actions = paint_report.get("draw_actions", [])  # 新增代码+DesktopTaskRuntime：读取代表性笔画动作列表；如果没有这一行，动作计数和底层事件数无法计算。
        gui_action_count = len(draw_actions) if isinstance(draw_actions, list) else 0  # 新增代码+DesktopTaskRuntime：统计 GUI 笔画动作数量；如果没有这一行，验收器无法确认 GUI 动作大于 0。
        low_level_event_count = _desktop_task_runtime_sum_events(draw_actions)  # 新增代码+DesktopTaskRuntime：统计鼠标 move/down/up 等低层事件；如果没有这一行，验收器无法确认输入链路证据。
        return {"paint_report": paint_report, "gui_action_count": gui_action_count, "low_level_event_count": low_level_event_count, "post_action_screenshot_exists": bool(paint_report.get("canvas_observed", False)), "post_action_screenshot_source": "recording_contract_canvas_observed", "post_action_visual_evidence_path": str(paint_report.get("artifact_path", "")), "canvas_changed_after_actions": bool(paint_report.get("paint_canvas_not_blank", False)), "pikachu_visual_elements": bool(paint_report.get("pikachu_visual_elements", False)), "humanlike_drawing_actions": bool(paint_report.get("humanlike_drawing_actions", False)), "direct_image_file_cheat": bool(paint_report.get("direct_image_file_cheat", True))}  # 新增代码+DesktopTaskRuntime：返回录制模式绘图证据摘要；如果没有这一行，GUI 路由无法交给验收器判断。
    # 新增代码+DesktopTaskRuntime：函数段结束，ComputerUseDesktopTaskRuntime._recording_paint_evidence 到此结束；如果没有这个边界说明，代码小白不容易看出 Paint 证据范围。

    def _recording_launch_evidence(self, target_app: str) -> dict[str, Any]:  # 新增代码+DesktopTaskRuntime：函数段开始，生成通用应用发现和记录型窗口身份证据；如果没有这段函数，GUI 动作没有自有目标窗口。
        generic_report = resolve_generic_app_launch_target(target_app)  # 新增代码+DesktopTaskRuntime：用 Phase108 解析目标应用；如果没有这一行，运行时会绕开通用发现机制。
        candidate_report = prepare_phase109_generic_real_launch_candidate(raw_target=target_app, generic_report=generic_report, enable_real_launch=True)  # 新增代码+DesktopTaskRuntime：用 Phase109 记录型后端验证自有窗口身份；如果没有这一行，运行时无法证明目标窗口绑定且单元测试不会开真实应用。
        return {"generic_discovery_report": generic_report, "generic_real_launch_candidate_report": candidate_report, "owned_window_verified": bool(candidate_report.get("target_identity_verified", False) and candidate_report.get("visible_window_verified", False) and not candidate_report.get("target_drift_blocks_action", False)), "real_desktop_touched": bool(generic_report.get("real_desktop_touched", False) or candidate_report.get("real_desktop_touched", False))}  # 新增代码+DesktopTaskRuntime：返回发现和窗口身份摘要；如果没有这一行，主运行时拿不到目标绑定结果。
    # 新增代码+DesktopTaskRuntime：函数段结束，ComputerUseDesktopTaskRuntime._recording_launch_evidence 到此结束；如果没有这个边界说明，代码小白不容易看出启动证据范围。

    def _real_execution_report(self, report: dict[str, Any], prompt: str, target_app: str) -> dict[str, Any]:  # 新增代码+源码复核门禁：函数段开始，调用注入的真实执行闭环并汇总报告；如果没有这段函数，real_actions=True 无法从硬拒绝推进到受控真实路径。
        loop = self.real_execution_loop  # 新增代码+源码复核门禁：读取注入的真实执行闭环；如果没有这一行，后续无法判断是否具备真实执行能力。
        if loop is None or not hasattr(loop, "run_desktop_task"):  # 新增代码+源码复核门禁：没有闭环或接口不匹配时安全拒绝；如果没有这一行，None 会导致异常或误触其它对象。
            report["decision"] = "real_actions_not_enabled_in_desktop_task_runtime"  # 修改代码+源码复核门禁：写入真实动作未接线原因码；如果没有这一行，用户看不出为什么没有真实执行。
            report["real_actions_supported"] = False  # 新增代码+源码复核门禁：声明当前实例不支持真实动作；如果没有这一行，调用方会误以为 full mode 已足够。
            return report  # 新增代码+源码复核门禁：返回零副作用报告；如果没有这一行，未接线时可能继续执行未知逻辑。
        loop_report = dict(loop.run_desktop_task(target_app=target_app, prompt=prompt))  # 新增代码+源码复核门禁：调用注入闭环并复制返回报告；如果没有这一行，real_actions=True 没有真实执行事实来源。
        report.update(loop_report)  # 新增代码+源码复核门禁：把真实闭环字段合并到桌面任务报告；如果没有这一行，最终 CLI 看不到真实动作结果。
        report["real_actions_supported"] = True  # 新增代码+源码复核门禁：声明当前实例已接入真实动作闭环；如果没有这一行，用户无法区分硬拒绝和真实执行。
        report["recording_mode"] = False  # 新增代码+源码复核门禁：真实执行路径不是录制模式；如果没有这一行，成熟度会继续混淆 recording 和 real。
        report["computer_use_gui_route_used"] = bool(loop_report.get("computer_use_gui_route_used", loop_report.get("ok", False)))  # 新增代码+源码复核门禁：汇总真实闭环是否走 GUI 路由；如果没有这一行，最终报告可能缺少 GUI route token。
        report["owned_window_verified"] = bool(loop_report.get("owned_window_verified", False))  # 新增代码+源码复核门禁：汇总目标窗口是否验证；如果没有这一行，动作可能缺少目标身份事实。
        report["gui_action_count"] = _desktop_task_runtime_safe_int(loop_report.get("gui_action_count", 0))  # 新增代码+源码复核门禁：汇总真实 GUI 动作数；如果没有这一行，成功可能没有动作规模证据。
        report["low_level_event_count"] = _desktop_task_runtime_safe_int(loop_report.get("low_level_event_count", 0))  # 新增代码+源码复核门禁：汇总真实低层事件数；如果没有这一行，真实动作可能只是口头成功。
        report["real_desktop_touched"] = bool(loop_report.get("real_desktop_touched") or loop_report.get("real_dispatch_performed"))  # 新增代码+源码复核门禁：汇总真实桌面触达事实；如果没有这一行，最终矩阵拿不到真实执行证据。
        report["forbidden_script_artifact_route_blocked"] = not bool(report.get("forbidden_script_generation_used", False) or report.get("bash_final_artifact_route_used", False))  # 新增代码+源码复核门禁：真实路径仍必须阻断脚本成品绕路；如果没有这一行，真实执行可能和脚本作弊混在一起。
        report["passed"] = bool(loop_report.get("ok") and report["computer_use_gui_route_used"] and report["owned_window_verified"] and report["low_level_event_count"] > 0 and report["real_desktop_touched"] and report["forbidden_script_artifact_route_blocked"])  # 新增代码+源码复核门禁：只有真实动作、窗口、事件和防作弊都满足才通过；如果没有这一行，局部成功会被误判成熟。
        report["ok_token"] = COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK if report["passed"] else ""  # 新增代码+源码复核门禁：只有真实执行通过才写 OK token；如果没有这一行，失败 JSON 仍可能暴露成功 token。
        report["decision"] = str(loop_report.get("decision", "real_desktop_task_execution_finished"))  # 新增代码+源码复核门禁：保留真实闭环决策码；如果没有这一行，调用方看不到真实执行的结束原因。
        return report  # 新增代码+源码复核门禁：返回完整真实执行报告；如果没有这一行，run_prompt 拿不到结果。
    # 新增代码+源码复核门禁：函数段结束，ComputerUseDesktopTaskRuntime._real_execution_report 到此结束；如果没有这个边界说明，代码小白不容易看出真实执行汇总范围。

    def _acceptance_report(self, evidence: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopTaskRuntime：函数段开始，把运行时证据交给 Task 1 验收器；如果没有这段函数，运行时可能绕过禁止脚本路线门禁。
        acceptance = evaluate_desktop_task_acceptance(evidence)  # 新增代码+DesktopTaskRuntime：调用统一验收器；如果没有这一行，GUI 路由和脚本绕路判断会分裂。
        checked = dict(evidence)  # 新增代码+DesktopTaskRuntime：复制证据避免修改调用方对象；如果没有这一行，后续合并可能污染原始结构。
        checked["passed"] = bool(acceptance.get("passed", False))  # 新增代码+DesktopTaskRuntime：写入验收是否通过；如果没有这一行，CLI 和测试无法读取最终状态。
        checked["ok_token"] = COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK if checked["passed"] else ""  # 新增代码+源码复核门禁：只有录制验收通过才写 OK token；如果没有这一行，失败 JSON 仍可能暴露成功 token。
        checked["decision"] = "computer_use_gui_route_recording_evidence_ready" if checked["passed"] else str(acceptance.get("decision", ""))  # 新增代码+DesktopTaskRuntime：成功时使用运行时决策码，失败时保留验收失败原因；如果没有这一行，用户看不出这是录制模式 GUI 证据已就绪。
        checked["acceptance"] = acceptance  # 新增代码+DesktopTaskRuntime：保留底层验收结果；如果没有这一行，失败时难以看到缺少哪些成熟字段。
        checked["forbidden_script_generation_used"] = bool(acceptance.get("forbidden_script_generation_used", checked.get("forbidden_script_generation_used", False)))  # 新增代码+DesktopTaskRuntime：同步验收器检测到的禁止脚本标记；如果没有这一行，CLI 可能显示旧字段。
        checked["bash_final_artifact_route_used"] = bool(acceptance.get("bash_final_artifact_route_used", checked.get("bash_final_artifact_route_used", False)))  # 新增代码+DesktopTaskRuntime：同步验收器检测到的 bash 成品路线标记；如果没有这一行，根因字段可能不准确。
        checked["forbidden_script_artifact_route_blocked"] = not bool(checked.get("forbidden_script_generation_used", False) or checked.get("bash_final_artifact_route_used", False))  # 新增代码+DesktopTaskRuntime：计算脚本成品路线是否被阻断；如果没有这一行，用户看不到根因门禁是否仍生效。
        return checked  # 新增代码+DesktopTaskRuntime：返回合并后的最终报告；如果没有这一行，调用方拿不到验收结果。
    # 新增代码+DesktopTaskRuntime：函数段结束，ComputerUseDesktopTaskRuntime._acceptance_report 到此结束；如果没有这个边界说明，代码小白不容易看出验收合并范围。

    def run_prompt(self, prompt: str, real_actions: bool = False, force_desktop_task: bool = False, target_hint: str = "") -> dict[str, Any]:  # 修改代码+DesktopTaskExplicitTool: 函数段开始，把用户 prompt 运行成 Computer Use 桌面任务报告，并允许显式 MCP 工具入口绕开旧误判；如果没有这段函数，desktop_task 会被乱码 prompt 挡住。
        classified_intent = classify_desktop_task(prompt)  # 修改代码+DesktopTaskExplicitTool: 先保守分类自然语言 prompt；如果没有这一行，普通 run_prompt 无法继续防止非桌面任务误触 GUI。
        intent = _desktop_task_runtime_forced_intent(classified_intent, target_hint) if force_desktop_task else classified_intent  # 新增代码+DesktopTaskExplicitTool: 只有显式工具入口才强制桌面任务；如果没有这一行，MCP desktop_task 仍会返回 not_desktop_task。
        target_app = _desktop_task_runtime_target_from_intent(intent)  # 新增代码+DesktopTaskRuntime：把意图目标映射成通用应用发现目标；如果没有这一行，中文画图无法进入 mspaint 链路。
        mode_status = self._mode_status()  # 新增代码+DesktopTaskRuntime：读取当前 full mode session 状态；如果没有这一行，运行时无法执行权限门禁。
        report = self._base_report(intent, mode_status, target_app)  # 新增代码+DesktopTaskRuntime：创建共享报告骨架；如果没有这一行，各分支字段会不一致。
        report["real_actions_requested"] = bool(real_actions)  # 新增代码+DesktopTaskRuntime：记录调用方是否请求真实动作；如果没有这一行，Task 4 录制模式边界不透明。
        if not intent.is_desktop_task:  # 新增代码+DesktopTaskRuntime：非桌面任务直接拒绝进入 GUI 路由；如果没有这一行，代码/文档类 prompt 可能误控制本机。
            report["decision"] = "not_desktop_task"  # 新增代码+DesktopTaskRuntime：写入非桌面任务原因码；如果没有这一行，调用方无法解释为什么没有运行。
            return report  # 新增代码+DesktopTaskRuntime：返回零副作用报告；如果没有这一行，非桌面任务会继续进入后续 GUI 证据链。
        if not report["full_mode_session_used"]:  # 新增代码+DesktopTaskRuntime：full mode 不可用时阻断 GUI 路由；如果没有这一行，普通模式可能误操作本机应用。
            report["decision"] = "computer_use_full_mode_required"  # 新增代码+DesktopTaskRuntime：写入需要 full mode 的稳定原因码；如果没有这一行，用户不知道下一步该先确认 full。
            return report  # 新增代码+DesktopTaskRuntime：返回零真实动作拒绝报告；如果没有这一行，未授权也可能生成动作证据。
        if real_actions:  # 修改代码+源码复核门禁：真实动作请求进入可注入真实执行闭环；如果没有这一行，调用方可能误以为 recording runtime 会真实画图。
            return self._real_execution_report(report, prompt, target_app)  # 修改代码+源码复核门禁：有真实闭环则执行、无闭环则安全拒绝；如果没有这一行，real_actions=True 会永久停在硬拒绝。
        launch_evidence = self._recording_launch_evidence(target_app)  # 新增代码+DesktopTaskRuntime：生成通用发现和记录型窗口证据；如果没有这一行，动作证据没有目标身份。
        paint_evidence = self._recording_paint_evidence() if target_app == "mspaint" else {"paint_report": {}, "gui_action_count": 1, "low_level_event_count": 1, "post_action_screenshot_exists": True, "canvas_changed_after_actions": True, "direct_image_file_cheat": False}  # 新增代码+DesktopTaskRuntime：Paint 走代表性绘图证据，其他应用保留最小录制占位；如果没有这一行，非 Paint 泛化任务无法形成基础 GUI 证据。
        report.update(launch_evidence)  # 新增代码+DesktopTaskRuntime：合并目标发现和窗口身份结果；如果没有这一行，最终报告缺少 owned_window_verified。
        report.update(paint_evidence)  # 新增代码+DesktopTaskRuntime：合并 GUI 动作和视觉证据；如果没有这一行，验收器会认为缺少动作和截图。
        report["computer_use_gui_route_used"] = bool(report.get("owned_window_verified", False) and report.get("gui_action_count", 0) and report.get("low_level_event_count", 0))  # 新增代码+DesktopTaskRuntime：确认 GUI 路由证据是否完整；如果没有这一行，脚本或空动作可能被当成 GUI 路由。
        report["natural_language_desktop_tasks_route_to_computer_use"] = True  # 新增代码+DesktopTaskRuntime：明确自然语言桌面任务已送入 Computer Use；如果没有这一行，CLI 不能证明根因路由被修复。
        report["real_desktop_touched"] = bool(report.get("real_desktop_touched", False))  # 新增代码+DesktopTaskRuntime：规范化真实桌面触碰字段；如果没有这一行，None 或缺字段会让测试判断不稳。
        return self._acceptance_report(report)  # 新增代码+DesktopTaskRuntime：经过统一验收后返回最终报告；如果没有这一行，禁止脚本成品路线不会成为最终门禁。
    # 新增代码+DesktopTaskRuntime：函数段结束，ComputerUseDesktopTaskRuntime.run_prompt 到此结束；如果没有这个边界说明，代码小白不容易看出主运行入口范围。
# 新增代码+DesktopTaskRuntime：类段结束，ComputerUseDesktopTaskRuntime 到此结束；如果没有这个边界说明，代码小白不容易看出运行时类范围。


def computer_use_full_desktop_task_runtime_cli_line(report: dict[str, Any]) -> str:  # 新增代码+DesktopTaskRuntime：函数段开始，把运行时报告转成稳定终端 token 行；如果没有这段函数，真实可见终端验收只能解析复杂 JSON。
    ok_token = f" {COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK}" if bool(report.get("passed", False)) else ""  # 新增代码+DesktopTaskRuntime：只在通过时追加 OK token；如果没有这一行，失败报告可能被误判成功。
    return f"{COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_READY}{ok_token} desktop_task_router={_desktop_task_runtime_bool_token(report.get('desktop_task_router_used', False))} natural_language_desktop_tasks_route_to_computer_use={_desktop_task_runtime_bool_token(report.get('natural_language_desktop_tasks_route_to_computer_use', False))} computer_use_gui_route_used={_desktop_task_runtime_bool_token(report.get('computer_use_gui_route_used', False))} forbidden_script_artifact_route_blocked={_desktop_task_runtime_bool_token(report.get('forbidden_script_artifact_route_blocked', False))} full_mode_session_used={_desktop_task_runtime_bool_token(report.get('full_mode_session_used', False))} owned_window_verified={_desktop_task_runtime_bool_token(report.get('owned_window_verified', False))} real_target_launch_enabled={_desktop_task_runtime_bool_token(report.get('real_target_launch_enabled', False))} real_launch_performed={_desktop_task_runtime_bool_token(report.get('real_launch_performed', False))} backend_launch_performed={_desktop_task_runtime_bool_token(report.get('backend_launch_performed', False))} process_started={_desktop_task_runtime_bool_token(report.get('process_started', False))} owned_process_registered={_desktop_task_runtime_bool_token(report.get('owned_process_registered', False))} visible_window_verified={_desktop_task_runtime_bool_token(report.get('visible_window_verified', False))} visual_planner_connected={_desktop_task_runtime_bool_token(report.get('visual_planner_connected', False))} visual_planner_used={_desktop_task_runtime_bool_token(report.get('visual_planner_used', False))} visual_planner_mature={_desktop_task_runtime_bool_token(report.get('visual_planner_mature', False))} gui_action_count={_desktop_task_runtime_safe_int(report.get('gui_action_count', 0))} low_level_event_count={_desktop_task_runtime_safe_int(report.get('low_level_event_count', 0))} real_desktop_touched={_desktop_task_runtime_bool_token(report.get('real_desktop_touched', True))}"  # 修改代码+VisualPlannerLoop：把 agent 启动、窗口绑定和视觉 planner 证据放进短 token 行；如果没有这一行，真实终端验收会继续看不到 planner 是否进入通用 loop。
# 新增代码+DesktopTaskRuntime：函数段结束，computer_use_full_desktop_task_runtime_cli_line 到此结束；如果没有这个边界说明，代码小白不容易看出 CLI 格式范围。


def build_default_desktop_task_runtime(workspace: str | Path) -> ComputerUseDesktopTaskRuntime:  # 新增代码+RuntimeFactorySlimming：函数段开始，集中构造默认桌面任务 runtime；如果没有这段函数，默认 runtime 工厂会继续挂在 LearningAgent 主类里制造误接风险。
    try:  # 新增代码+RuntimeFactorySlimming：优先用包路径导入真实 sender 和通用 adapter；如果没有这一行，项目根运行时无法构造当前默认 Computer Use 闭环。
        from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_physical_sendinput import WindowsControlledPhysicalSendInputSender  # 新增代码+RuntimeFactorySlimming：导入受控物理 sender；如果没有这一行，默认 runtime 无法经过 Phase95 安全门发送鼠标键盘。
        from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+RuntimeFactorySlimming：导入真实 Windows SendInput 后端；如果没有这一行，受控 sender 背后没有能触达本机桌面的低层实现。
        from learning_agent.computer_use_mcp_v2.windows_runtime.universal_desktop_execution_loop import UniversalDesktopExecutionLoopAdapter  # 新增代码+RuntimeFactorySlimming：导入通用桌面执行 adapter；如果没有这一行，默认 runtime 会退回旧黑盒或空闭环。
    except ModuleNotFoundError as error:  # 新增代码+RuntimeFactorySlimming：兼容 start_oauth_agent.bat 直接从 learning_agent 目录启动；如果没有这一行，脚本模式下模块前缀差异会让工厂不可用。
        if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.controlled_physical_sendinput", "learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard", "learning_agent.computer_use_mcp_v2.windows_runtime.universal_desktop_execution_loop"}:  # 新增代码+RuntimeFactorySlimming：只对包路径缺失做兜底；如果没有这一行，真实内部 bug 会被误吞。
            raise  # 新增代码+RuntimeFactorySlimming：重新抛出非路径类导入错误；如果没有这一行，排查 sender 或 adapter 内部问题会很困难。
        from computer_use_mcp_v2.windows_runtime.controlled_physical_sendinput import WindowsControlledPhysicalSendInputSender  # type: ignore  # 新增代码+RuntimeFactorySlimming：脚本模式导入同一受控 sender；如果没有这一行，真实可见终端入口无法构造默认 sender。
        from computer_use_mcp_v2.windows_runtime.real_sendinput_guard import WindowsSendInputLowLevelSender  # type: ignore  # 新增代码+RuntimeFactorySlimming：脚本模式导入同一 Windows SendInput 后端；如果没有这一行，bat 入口没有物理输入后端。
        from computer_use_mcp_v2.windows_runtime.universal_desktop_execution_loop import UniversalDesktopExecutionLoopAdapter  # type: ignore  # 新增代码+RuntimeFactorySlimming：脚本模式导入同一通用 adapter；如果没有这一行，bat 入口无法接入通用 observe-plan-act loop。
    runtime_root = Path(workspace) / "memory" / "computer_use" / "desktop_task_runtime"  # 新增代码+RuntimeFactorySlimming：把默认 runtime 证据写入调用方 workspace；如果没有这一行，证据会脱离当前 agent 工作目录。
    mode_store_root = _desktop_task_runtime_computer_use_locks_root(workspace).parent / "mode_sessions"  # 新增代码+DesktopTaskModeStoreAlignment: 使用和真实终端 `/computer use --full` 相同的 mode_sessions 目录；如果没有这一行，desktop_task 会误报 computer_use_full_mode_required。
    mode_store = ComputerUseModeSessionStore(base_dir=mode_store_root)  # 新增代码+DesktopTaskModeStoreAlignment: 构造共享模式状态 store；如果没有这一行，高层任务 runtime 看不到 full_mode=true。
    physical_sender_backend = WindowsSendInputLowLevelSender(platform="win32")  # 新增代码+RuntimeFactorySlimming：创建真实 Windows SendInput 底层后端；如果没有这一行，默认 full 模式只能记录动作不能触达桌面。
    controlled_physical_sender = WindowsControlledPhysicalSendInputSender(low_level_backend=physical_sender_backend, platform="win32", default_enable_physical_dispatch=True)  # 新增代码+RuntimeFactorySlimming：把真实后端包进受控 sender 并默认允许 full 授权后的物理派发；如果没有这一行，真实后端不会经过安全目标门禁。
    real_execution_loop = UniversalDesktopExecutionLoopAdapter(controlled_physical_sender=controlled_physical_sender, enable_real_target_launch=True)  # 新增代码+RuntimeFactorySlimming：构造默认通用桌面执行 adapter；如果没有这一行，runtime 不会具备启动、观察和动作闭环。
    return ComputerUseDesktopTaskRuntime(base_dir=runtime_root, mode_store=mode_store, real_execution_loop=real_execution_loop)  # 修改代码+DesktopTaskModeStoreAlignment: 返回接入共享 mode store 和通用 adapter 的 runtime；如果没有这一行，MCP 高层工具会和终端 full 状态脱节。
# 新增代码+RuntimeFactorySlimming：函数段结束，build_default_desktop_task_runtime 到此结束；如果没有这个边界说明，代码小白不容易看出默认 runtime 工厂范围。


def run_computer_use_full_desktop_task_runtime(prompt: str, real_actions: bool = False) -> dict[str, Any]:  # 新增代码+DesktopTaskRuntime：函数段开始，提供轻量函数入口；如果没有这段函数，交互层必须手动创建运行时对象。
    runtime = ComputerUseDesktopTaskRuntime()  # 新增代码+DesktopTaskRuntime：创建默认运行时；如果没有这一行，函数入口没有执行主体。
    return runtime.run_prompt(prompt, real_actions=real_actions)  # 新增代码+DesktopTaskRuntime：返回运行时报告；如果没有这一行，调用方拿不到桌面任务证据。
# 新增代码+DesktopTaskRuntime：函数段结束，run_computer_use_full_desktop_task_runtime 到此结束；如果没有这个边界说明，代码小白不容易看出轻量入口范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+DesktopTaskRuntime：函数段开始，提供命令行自检入口；如果没有这段函数，真实终端无法单独运行 Task 4 合同。
    args = list(argv or [])  # 新增代码+DesktopTaskRuntime：复制参数列表；如果没有这一行，None 参数无法统一处理。
    prompt = " ".join(args).strip() or "请使用本地电脑的画图软件画一个皮卡丘。"  # 新增代码+DesktopTaskRuntime：使用参数 prompt 或默认代表性中文 prompt；如果没有这一行，命令行自检缺少真实用户场景。
    report = run_computer_use_full_desktop_task_runtime(prompt, real_actions=False)  # 新增代码+DesktopTaskRuntime：运行录制模式桌面任务；如果没有这一行，CLI 不会产生报告。
    print(computer_use_full_desktop_task_runtime_cli_line(report))  # 新增代码+DesktopTaskRuntime：打印稳定 token 行；如果没有这一行，真实终端验收无法快速匹配。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+DesktopTaskRuntime：打印完整 JSON 供排查；如果没有这一行，失败时只能看短 token。
    print(COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_READY)  # 新增代码+DesktopTaskRuntime：单独打印 ready marker 便于人工观察；如果没有这一行，可见终端里不容易发现阶段标识。
    return 0 if bool(report.get("passed", False)) else 1  # 新增代码+DesktopTaskRuntime：按报告通过状态返回退出码；如果没有这一行，失败也可能被自动化当成功。
# 新增代码+DesktopTaskRuntime：函数段结束，main 到此结束；如果没有这个边界说明，代码小白不容易看出命令入口范围。


__all__ = ["COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK", "COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_READY", "COMPUTER_USE_FULL_DESKTOP_TASK_RUNTIME_MODEL", "ComputerUseDesktopTaskRuntime", "build_default_desktop_task_runtime", "computer_use_full_desktop_task_runtime_cli_line", "main", "run_computer_use_full_desktop_task_runtime"]  # 修改代码+RuntimeFactorySlimming：公开迁移后的默认 runtime 工厂；如果没有这一行，外部测试和 maturity 矩阵无法稳定引用新入口。


if __name__ == "__main__":  # 新增代码+DesktopTaskRuntime：文件入口段开始，允许 python -m 或直接运行本文件；如果没有这一行，命令行自检不会启动。
    raise SystemExit(main())  # 新增代码+DesktopTaskRuntime：用 main 的返回码退出；如果没有这一行，命令执行状态不明确。
# 新增代码+DesktopTaskRuntime：文件入口段结束，直接运行模块到此结束；如果没有这个边界说明，代码小白不容易看出入口范围。
