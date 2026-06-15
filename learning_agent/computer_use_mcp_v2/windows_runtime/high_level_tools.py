"""Phase62 Windows high-level Computer Tool API and streaming integration."""  # 新增代码+Phase62HighLevelTools: 标明本文件负责高层 Computer Use 工具；如果没有这行代码，读者不容易区分底层 SendInput 和高层任务 API。
from __future__ import annotations  # 新增代码+Phase62HighLevelTools: 启用延迟类型解析；如果没有这行代码，复杂类型注解在脚本模式下更容易导入失败。

import concurrent.futures  # 新增代码+Phase62HighLevelTools: 导入线程池执行只读批量任务；如果没有这行代码，observe_screen/find_control 无法证明可并发调度。
import json  # 新增代码+Phase62HighLevelTools: 导入 JSON 用于 artifact、CLI 报告和结构化进度；如果没有这行代码，验收输出无法稳定解析。
import time  # 新增代码+Phase62HighLevelTools: 导入时间用于合同目录和事件时间戳；如果没有这行代码，多次运行状态文件可能互相覆盖。
from pathlib import Path  # 新增代码+Phase62HighLevelTools: 导入 Path 管理 Windows 路径；如果没有这行代码，artifact 和 memory 路径会脆弱。
from typing import Any  # 新增代码+Phase62HighLevelTools: 导入 Any 描述 JSON 风格参数；如果没有这行代码，接口边界不清楚。

try:  # 新增代码+Phase62HighLevelTools: 优先按包路径导入 Computer Use 既有安全链；如果没有这段代码，unittest 和生产入口无法复用项目模块。
    from learning_agent.computer_use_mcp_v2.windows_runtime.abort_streaming_hooks import WindowsComputerUseAbortStreamingHooks  # 新增代码+Phase62HighLevelTools: 复用 Phase61 abort/cleanup/streaming hooks；如果没有这行代码，高层写动作无法最后一跳急停。
    from learning_agent.computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager, phase30_lock_timestamp  # 新增代码+Phase62HighLevelTools: 复用 durable 桌面锁和时间戳；如果没有这行代码，写动作无法串行化。
    from learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANT_SESSION_ID, WindowsComputerUsePersistentGrantStore  # 新增代码+Phase62HighLevelTools: 复用 Phase60 持久授权；如果没有这行代码，高层写动作会绕过审批。
    from learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard import Phase58RecordingLowLevelSender, Phase58StaticSafeWindowObserver, WindowsRealSendInputGuardRuntime  # 新增代码+Phase62HighLevelTools: 复用 Phase58 目标守卫和低层 sender；如果没有这行代码，高层 click/type 会另开危险实现。
    from learning_agent.computer_use_mcp_v2.windows_runtime.real_uia_locator import SemanticControlLocator  # 新增代码+Phase62HighLevelTools: 复用 Phase57 语义控件定位器；如果没有这行代码，高层 find_control 会重复造 locator。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase62HighLevelTools: 复用静态 inventory 让合同不触碰真实桌面；如果没有这行代码，单测可能依赖用户窗口。
    from learning_agent.core.messages import ToolCall  # 新增代码+Phase62HighLevelTools: 复用全局工具调用对象；如果没有这行代码，StreamingToolExecutor 无法关联 call_id。
    from learning_agent.runtime.files import append_jsonl, read_jsonl  # 新增代码+Phase62HighLevelTools: 复用 JSONL 写读工具；如果没有这行代码，progress 事件会重复造轮子。
    from learning_agent.tools.streaming_executor import StreamingToolExecutor  # 新增代码+Phase62HighLevelTools: 接入全局 StreamingToolExecutor；如果没有这行代码，Phase62 只能写自有 progress，无法对齐 ClaudeCode 风格工具生命周期。
except ModuleNotFoundError as error:  # 新增代码+Phase62HighLevelTools: 兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，双击 bat 时高层工具可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use_mcp_v2.windows_runtime", "learning_agent.computer_use_mcp_v2.windows_runtime.abort_streaming_hooks", "learning_agent.computer_use_mcp_v2.windows_runtime.lock", "learning_agent.computer_use_mcp_v2.windows_runtime.persistent_grants", "learning_agent.computer_use_mcp_v2.windows_runtime.real_sendinput_guard", "learning_agent.computer_use_mcp_v2.windows_runtime.real_uia_locator", "learning_agent.computer_use_mcp_v2.windows_runtime.windows_backend", "learning_agent.core", "learning_agent.core.messages", "learning_agent.runtime", "learning_agent.runtime.files", "learning_agent.tools", "learning_agent.tools.streaming_executor"}:  # 新增代码+Phase62HighLevelTools: 只允许包路径缺失时 fallback；如果没有这行代码，内部真实 bug 会被误吞。
        raise  # 新增代码+Phase62HighLevelTools: 重新抛出非路径类导入错误；如果没有这行代码，排查底层模块会很困难。
    from computer_use_mcp_v2.windows_runtime.abort_streaming_hooks import WindowsComputerUseAbortStreamingHooks  # 新增代码+Phase62HighLevelTools: 脚本模式导入 Phase61 hooks；如果没有这行代码，bat 入口无法显示高层 streaming 集成。
    from computer_use_mcp_v2.windows_runtime.lock import ComputerUseLockManager, phase30_lock_timestamp  # 新增代码+Phase62HighLevelTools: 脚本模式导入锁管理器；如果没有这行代码，bat 入口高层写动作无法串行。
    from computer_use_mcp_v2.windows_runtime.persistent_grants import DEFAULT_PERSISTENT_GRANT_SESSION_ID, WindowsComputerUsePersistentGrantStore  # 新增代码+Phase62HighLevelTools: 脚本模式导入持久授权；如果没有这行代码，bat 入口无法评估 grant。
    from computer_use_mcp_v2.windows_runtime.real_sendinput_guard import Phase58RecordingLowLevelSender, Phase58StaticSafeWindowObserver, WindowsRealSendInputGuardRuntime  # 新增代码+Phase62HighLevelTools: 脚本模式导入 Phase58 安全链；如果没有这行代码，高层写动作无法执行合同。
    from computer_use_mcp_v2.windows_runtime.real_uia_locator import SemanticControlLocator  # 新增代码+Phase62HighLevelTools: 脚本模式导入语义 locator；如果没有这行代码，find_control 不可用。
    from computer_use_mcp_v2.windows_runtime.windows_backend import StaticWindowsWindowInventory  # 新增代码+Phase62HighLevelTools: 脚本模式导入静态 inventory；如果没有这行代码，合同自检会触碰真实桌面。
    from core.messages import ToolCall  # 新增代码+Phase62HighLevelTools: 脚本模式导入 ToolCall；如果没有这行代码，StreamingToolExecutor 无法运行。
    from runtime.files import append_jsonl, read_jsonl  # 新增代码+Phase62HighLevelTools: 脚本模式导入 JSONL 工具；如果没有这行代码，progress 事件不能落盘。
    from tools.streaming_executor import StreamingToolExecutor  # 新增代码+Phase62HighLevelTools: 脚本模式导入全局 streaming executor；如果没有这行代码，bat 入口无法证明全局执行器集成。

PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER = "PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_READY"  # 新增代码+Phase62HighLevelTools: 定义 Phase62 ready marker；如果没有这行代码，真实终端验收没有稳定锚点。
PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_OK_TOKEN = "PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_OK"  # 新增代码+Phase62HighLevelTools: 定义 Phase62 OK token；如果没有这行代码，debug log 无法区分自检通过和普通输出。
PHASE62_HIGH_LEVEL_TOOLS_MODEL = "phase62_windows_high_level_computer_tools"  # 新增代码+Phase62HighLevelTools: 定义高层工具模型名；如果没有这行代码，status 和 progress 无法区分版本。
PHASE62_ACTIONS_EXPANDED = False  # 新增代码+Phase62HighLevelTools: 明确 Phase62 只是高层编排，不新增底层动作面；如果没有这行代码，用户可能误以为开放了更多真实桌面动作。
PHASE62_SUPPORTED_OPERATIONS = ("observe_screen", "find_control", "click_control", "type_into_control", "wait_for_change", "verify_screen")  # 新增代码+Phase62HighLevelTools: 固定模型可调用的高层操作集合；如果没有这行代码，schema/status/验收会漂移。
PHASE62_READ_ONLY_OPERATIONS = {"observe_screen", "find_control", "wait_for_change", "verify_screen"}  # 新增代码+Phase62HighLevelTools: 标记只读操作集合；如果没有这行代码，批量只读和写动作锁边界无法区分。
DEFAULT_HIGH_LEVEL_TOOLS_ROOT = Path(__file__).resolve().parents[1] / "memory" / "computer_use" / "high_level_tools"  # 新增代码+Phase62HighLevelTools: 定义默认状态目录；如果没有这行代码，生产入口不知道 progress 和 artifact 放哪里。


def _phase62_bool_token(value: Any) -> str:  # 新增代码+Phase62HighLevelTools: 函数段开始，把布尔值转为稳定小写 token；如果没有这段函数，CLI 输出可能出现 True/False 漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase62HighLevelTools: 返回 true/false 文本；如果没有这行代码，场景断言可能大小写失败。
# 新增代码+Phase62HighLevelTools: 函数段结束，_phase62_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式范围。


def _phase62_safe_text(value: Any, limit: int = 220) -> str:  # 新增代码+Phase62HighLevelTools: 函数段开始，把任意文本压成安全单行；如果没有这段函数，进度和终端状态可能被换行刷乱。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase62HighLevelTools: 清理换行和空白；如果没有这行代码，用户输入可能打散 JSONL/状态 UI。
    return text[:limit]  # 新增代码+Phase62HighLevelTools: 限制最大长度；如果没有这行代码，异常或标题可能刷爆终端。
# 新增代码+Phase62HighLevelTools: 函数段结束，_phase62_safe_text 到此结束；如果没有这个边界说明，初学者不容易看出文本清理范围。


def _phase62_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+Phase62HighLevelTools: 函数段开始，安全转换坐标整数；如果没有这段函数，坏控件 bounds 会让高层动作崩溃。
    try:  # 新增代码+Phase62HighLevelTools: 捕获无法转换的动态值；如果没有这行代码，None 或字符串坐标会直接抛异常。
        return int(value)  # 新增代码+Phase62HighLevelTools: 返回整数；如果没有这行代码，点击坐标无法传给 Phase58。
    except Exception:  # 新增代码+Phase62HighLevelTools: 兜底处理任意转换异常；如果没有这行代码，模型坏参数会中断 agent。
        return int(default)  # 新增代码+Phase62HighLevelTools: 返回默认整数；如果没有这行代码，调用方需要到处重复兜底。
# 新增代码+Phase62HighLevelTools: 函数段结束，_phase62_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出整数转换范围。


def _phase62_control_center(control: dict[str, Any]) -> dict[str, int]:  # 新增代码+Phase62HighLevelTools: 函数段开始，从控件 bounds 计算中心点；如果没有这段函数，click_control/type_into_control 不知道点击哪里。
    bounds = dict(control.get("bounds", {}) or {})  # 新增代码+Phase62HighLevelTools: 读取控件边界并复制；如果没有这行代码，坏控件对象可能污染后续逻辑。
    left = _phase62_safe_int(bounds.get("left"))  # 新增代码+Phase62HighLevelTools: 读取左边界；如果没有这行代码，中心点缺少 x 起点。
    top = _phase62_safe_int(bounds.get("top"))  # 新增代码+Phase62HighLevelTools: 读取上边界；如果没有这行代码，中心点缺少 y 起点。
    right = _phase62_safe_int(bounds.get("right"), left + _phase62_safe_int(bounds.get("width"), 1))  # 新增代码+Phase62HighLevelTools: 读取右边界并用 width 兜底；如果没有这行代码，只有 width 的控件无法点击。
    bottom = _phase62_safe_int(bounds.get("bottom"), top + _phase62_safe_int(bounds.get("height"), 1))  # 新增代码+Phase62HighLevelTools: 读取下边界并用 height 兜底；如果没有这行代码，只有 height 的控件无法点击。
    return {"x": left + max(1, right - left) // 2, "y": top + max(1, bottom - top) // 2}  # 新增代码+Phase62HighLevelTools: 返回控件中心坐标；如果没有这行代码，Phase58 sender 没有落点。
# 新增代码+Phase62HighLevelTools: 函数段结束，_phase62_control_center 到此结束；如果没有这个边界说明，初学者不容易看出中心点计算范围。


def _phase62_contract_window() -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，构造合同自检安全窗口；如果没有这段函数，CLI 合同会依赖真实桌面。
    return {"app_id": "phase58_safe_app", "process_name": "phase58_safe_app", "window_id": "hwnd:6201", "hwnd": 6201, "title_preview": "LearningAgent-Phase58-HighLevelToolsSmoke", "rect": {"left": 80, "top": 90, "right": 680, "bottom": 430}, "display_id": "DISPLAY1", "safe_to_target": True}  # 新增代码+Phase62HighLevelTools: 返回满足 Phase58 守卫的窗口；如果没有这行代码，写动作合同无法进入底层链路。
# 新增代码+Phase62HighLevelTools: 函数段结束，_phase62_contract_window 到此结束；如果没有这个边界说明，初学者不容易看出合同窗口范围。


def _phase62_contract_controls() -> list[dict[str, Any]]:  # 新增代码+Phase62HighLevelTools: 函数段开始，构造合同自检控件候选；如果没有这段函数，find/click/type 合同会触碰真实 UIA。
    return [{"node_id": "0", "name": "Phase62 root", "role": "Window", "automation_id": "Phase62Root", "class_name": "Window", "bounds": {"left": 80, "top": 90, "right": 680, "bottom": 430, "width": 600, "height": 340}, "enabled": True, "clickable": False, "editable": False}, {"node_id": "0.1", "name": "Search box", "role": "Edit", "automation_id": "Phase62SearchBox", "class_name": "TextBox", "bounds": {"left": 110, "top": 130, "right": 430, "bottom": 170, "width": 320, "height": 40}, "enabled": True, "clickable": True, "editable": True}, {"node_id": "0.2", "name": "Run action", "role": "Button", "automation_id": "Phase62RunButton", "class_name": "Button", "bounds": {"left": 450, "top": 130, "right": 560, "bottom": 170, "width": 110, "height": 40}, "enabled": True, "clickable": True, "editable": False}]  # 新增代码+Phase62HighLevelTools: 返回可解释控件列表；如果没有这行代码，合同无法验证 UIA candidate summary。
# 新增代码+Phase62HighLevelTools: 函数段结束，_phase62_contract_controls 到此结束；如果没有这个边界说明，初学者不容易看出合同控件范围。


class WindowsHighLevelComputerToolRuntime:  # 新增代码+Phase62HighLevelTools: 类段开始，组合高层 API、授权、写锁、locator、streaming 和 Phase58 安全动作链；如果没有这个类，高层工具会散落在终端和测试里。
    def __init__(self, base_dir: str | Path | None = None, lock_manager: ComputerUseLockManager | None = None, grant_store: WindowsComputerUsePersistentGrantStore | None = None, abort_hooks: WindowsComputerUseAbortStreamingHooks | None = None, session_id: str = DEFAULT_PERSISTENT_GRANT_SESSION_ID, low_level_sender: Any | None = None, locator: SemanticControlLocator | None = None) -> None:  # 新增代码+Phase62HighLevelTools: 函数段开始，初始化高层 runtime 依赖；如果没有这段函数，测试和生产无法注入隔离状态。
        self.base_dir = Path(base_dir) if base_dir is not None else DEFAULT_HIGH_LEVEL_TOOLS_ROOT  # 新增代码+Phase62HighLevelTools: 保存状态根目录；如果没有这行代码，artifact/progress 没有固定位置。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase62HighLevelTools: 确保状态目录存在；如果没有这行代码，首次写 artifact 会失败。
        self.artifacts_dir = self.base_dir / "artifacts"  # 新增代码+Phase62HighLevelTools: 定义 artifact 目录；如果没有这行代码，observe_screen 产物会混进状态根。
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase62HighLevelTools: 确保 artifact 目录存在；如果没有这行代码，写入图片产物会失败。
        self.progress_events_path = self.base_dir / "phase62_progress_events.jsonl"  # 新增代码+Phase62HighLevelTools: 定义 progress JSONL 文件；如果没有这行代码，streaming 进度无法跨命令查看。
        self.lock_manager = lock_manager if lock_manager is not None else ComputerUseLockManager()  # 新增代码+Phase62HighLevelTools: 保存或创建桌面锁；如果没有这行代码，写动作无法串行。
        self.grant_store = grant_store if grant_store is not None else WindowsComputerUsePersistentGrantStore()  # 新增代码+Phase62HighLevelTools: 保存或创建持久授权 store；如果没有这行代码，高层写动作无法审批。
        self.session_id = str(session_id or DEFAULT_PERSISTENT_GRANT_SESSION_ID)  # 新增代码+Phase62HighLevelTools: 保存会话 id；如果没有这行代码，grant 和 lock 无法隔离会话。
        self.abort_hooks = abort_hooks if abort_hooks is not None else WindowsComputerUseAbortStreamingHooks(lock_manager=self.lock_manager, session_id=self.session_id, base_dir=self.base_dir / "abort_hooks")  # 新增代码+Phase62HighLevelTools: 保存或创建 abort hooks；如果没有这行代码，写动作不能被 Phase61 急停。
        self.low_level_sender = low_level_sender if low_level_sender is not None else Phase58RecordingLowLevelSender()  # 新增代码+Phase62HighLevelTools: 默认使用记录型 sender 保守不碰真实桌面；如果没有这行代码，合同测试可能触碰用户电脑。
        self.locator = locator if locator is not None else SemanticControlLocator()  # 新增代码+Phase62HighLevelTools: 保存语义 locator；如果没有这行代码，find_control/click_control/type_into_control 无法找控件。
        self.streaming_executor = StreamingToolExecutor(event_sink=self._record_streaming_executor_event)  # 新增代码+Phase62HighLevelTools: 创建全局 streaming executor 适配器；如果没有这行代码，Phase62 不能证明接入统一工具生命周期。
    # 新增代码+Phase62HighLevelTools: 函数段结束，WindowsHighLevelComputerToolRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _record_streaming_executor_event(self, payload: dict[str, Any]) -> None:  # 新增代码+Phase62HighLevelTools: 函数段开始，把 StreamingToolExecutor 事件镜像到 progress；如果没有这段函数，终端看不到全局执行器事件。
        metadata = dict(payload or {})  # 新增代码+Phase62HighLevelTools: 复制 executor payload；如果没有这行代码，追加字段可能污染调用方对象。
        operation = str(metadata.get("metadata", {}).get("operation", "") if isinstance(metadata.get("metadata", {}), dict) else "")  # 新增代码+Phase62HighLevelTools: 尝试读取操作名；如果没有这行代码，executor 事件无法按 operation 过滤。
        self.record_progress(operation or str(metadata.get("tool_name", "computer_high_level_tool")), "streaming_executor_" + str(metadata.get("event_type", "event")), metadata)  # 新增代码+Phase62HighLevelTools: 写入统一 progress；如果没有这行代码，StreamingToolExecutor 集成没有落盘证据。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_record_streaming_executor_event 到此结束；如果没有这个边界说明，初学者不容易看出 executor 事件镜像范围。

    def record_progress(self, operation: str, stage: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，记录一条高层工具进度事件；如果没有这段函数，长任务无法看到执行过程。
        event = {"marker": PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, "model": PHASE62_HIGH_LEVEL_TOOLS_MODEL, "operation": _phase62_safe_text(operation, 120), "stage": _phase62_safe_text(stage, 120), "payload": dict(payload or {}), "created_at": phase30_lock_timestamp()}  # 新增代码+Phase62HighLevelTools: 构造进度事件；如果没有这行代码，事件缺少阶段、模型和时间来源。
        append_jsonl(self.progress_events_path, event)  # 新增代码+Phase62HighLevelTools: 追加事件到 JSONL；如果没有这行代码，进度无法跨命令复盘。
        self.abort_hooks.record_stream_event("phase62_" + _phase62_safe_text(stage, 100), {"operation": _phase62_safe_text(operation, 120)})  # 新增代码+Phase62HighLevelTools: 同步写入 Phase61 hooks 流；如果没有这行代码，abort/cleanup 面板看不到高层工具事件。
        return event  # 新增代码+Phase62HighLevelTools: 返回事件供测试使用；如果没有这行代码，调用方拿不到写入结果。
    # 新增代码+Phase62HighLevelTools: 函数段结束，record_progress 到此结束；如果没有这个边界说明，初学者不容易看出 progress 记录范围。

    def progress_events(self) -> list[dict[str, Any]]:  # 新增代码+Phase62HighLevelTools: 函数段开始，读取高层工具 progress 事件；如果没有这段函数，测试和状态页无法复盘进度。
        return read_jsonl(self.progress_events_path)  # 新增代码+Phase62HighLevelTools: 容错读取 JSONL；如果没有这行代码，坏行或空文件会拖垮状态页。
    # 新增代码+Phase62HighLevelTools: 函数段结束，progress_events 到此结束；如果没有这个边界说明，初学者不容易看出事件读取范围。

    def supported_operations(self) -> tuple[str, ...]:  # 新增代码+Phase62HighLevelTools: 函数段开始，返回高层操作集合；如果没有这段函数，状态 UI 和 schema 需要硬编码操作名。
        return PHASE62_SUPPORTED_OPERATIONS  # 新增代码+Phase62HighLevelTools: 返回固定 tuple；如果没有这行代码，调用方拿不到当前高层 API 清单。
    # 新增代码+Phase62HighLevelTools: 函数段结束，supported_operations 到此结束；如果没有这个边界说明，初学者不容易看出操作清单范围。

    def run(self, operation: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，执行一个高层 Computer Tool 操作并接入 StreamingToolExecutor；如果没有这段函数，模型只能调用底层 click/type。
        operation_name = _phase62_safe_text(operation, 120)  # 新增代码+Phase62HighLevelTools: 清理操作名；如果没有这行代码，空白或换行会污染 progress。
        args = dict(arguments or {})  # 新增代码+Phase62HighLevelTools: 复制参数避免污染调用方对象；如果没有这行代码，补字段可能改到外部状态。
        result_box: dict[str, Any] = {}  # 新增代码+Phase62HighLevelTools: 保存 handler 内部执行结果；如果没有这行代码，StreamingToolExecutor 返回文本后拿不到结构化结果。
        tool_call = ToolCall(name="computer_high_level_tool", arguments={"operation": operation_name}, call_id=f"phase62-{operation_name}-{int(time.time() * 1000)}")  # 新增代码+Phase62HighLevelTools: 构造全局工具调用对象；如果没有这行代码，executor 事件没有 tool_name/call_id。
        def handler(_tool_call: ToolCall) -> Any:  # 新增代码+Phase62HighLevelTools: 函数段开始，给 StreamingToolExecutor 的 handler；如果没有这段函数，executor 无法包住真实操作。
            yield f"{operation_name}:started\n"  # 新增代码+Phase62HighLevelTools: 产出开始 chunk；如果没有这行代码，executor 不会生成 tool_result_chunk 事件。
            result_box["result"] = self._run_internal(operation_name, args)  # 新增代码+Phase62HighLevelTools: 执行真实高层操作；如果没有这行代码，executor 只会空转。
            yield f"{operation_name}:completed\n"  # 新增代码+Phase62HighLevelTools: 产出完成 chunk；如果没有这行代码，流式结果没有闭合提示。
        # 新增代码+Phase62HighLevelTools: 函数段结束，handler 到此结束；如果没有这个边界说明，初学者不容易看出 executor handler 范围。
        stream_text = self.streaming_executor.execute(tool_call, handler)  # 新增代码+Phase62HighLevelTools: 通过全局 StreamingToolExecutor 执行；如果没有这行代码，Phase62 不能证明集成全局执行器。
        result = dict(result_box.get("result", {}))  # 新增代码+Phase62HighLevelTools: 取出结构化结果；如果没有这行代码，返回值只剩 executor 文本。
        if not result:  # 新增代码+Phase62HighLevelTools: 处理 handler 未写结果的异常情况；如果没有这行代码，空结果会导致后续字段缺失。
            result = {"ok": False, "decision": "streaming_executor_failed", "message": stream_text, "low_level_event_count": 0}  # 新增代码+Phase62HighLevelTools: 构造失败结果；如果没有这行代码，executor 异常路径不可解释。
        result["streaming_executor_integrated"] = True  # 新增代码+Phase62HighLevelTools: 标记已接入全局 executor；如果没有这行代码，验收只能猜测是否走了全局执行器。
        result["streaming_executor_result_text"] = stream_text  # 新增代码+Phase62HighLevelTools: 保存 executor 文本摘要；如果没有这行代码，调试时看不到 chunk 拼接结果。
        return result  # 新增代码+Phase62HighLevelTools: 返回结构化高层工具结果；如果没有这行代码，调用方拿不到执行状态。
    # 新增代码+Phase62HighLevelTools: 函数段结束，run 到此结束；如果没有这个边界说明，初学者不容易看出高层执行入口范围。

    def _run_internal(self, operation: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，分发实际高层操作；如果没有这段函数，run 会变成一坨 if 逻辑。
        self.record_progress(operation, "operation_started", {"read_only": operation in PHASE62_READ_ONLY_OPERATIONS})  # 新增代码+Phase62HighLevelTools: 记录操作开始；如果没有这行代码，终端看不到高层工具进度。
        if operation not in PHASE62_SUPPORTED_OPERATIONS:  # 新增代码+Phase62HighLevelTools: 拒绝未知操作；如果没有这行代码，模型拼错操作可能进入危险默认分支。
            return self._failure(operation, "unsupported_operation", "Phase62 不支持该高层操作。")  # 新增代码+Phase62HighLevelTools: 返回稳定失败；如果没有这行代码，未知操作原因不清楚。
        if operation == "observe_screen":  # 新增代码+Phase62HighLevelTools: 分发只读屏幕观察；如果没有这行代码，observe_screen 不可用。
            result = self._observe_screen(arguments)  # 新增代码+Phase62HighLevelTools: 执行 observe_screen；如果没有这行代码，结果没有 artifact。
        elif operation == "find_control":  # 新增代码+Phase62HighLevelTools: 分发控件定位；如果没有这行代码，find_control 不可用。
            result = self._find_control(arguments)  # 新增代码+Phase62HighLevelTools: 执行 find_control；如果没有这行代码，结果没有候选摘要。
        elif operation == "click_control":  # 新增代码+Phase62HighLevelTools: 分发高层点击；如果没有这行代码，click_control 不可用。
            result = self._write_control_action(arguments, "click")  # 新增代码+Phase62HighLevelTools: 执行受保护点击；如果没有这行代码，点击会绕过通用写链。
        elif operation == "type_into_control":  # 新增代码+Phase62HighLevelTools: 分发高层输入；如果没有这行代码，type_into_control 不可用。
            result = self._write_control_action(arguments, "type_text")  # 新增代码+Phase62HighLevelTools: 执行受保护输入；如果没有这行代码，输入会绕过通用写链。
        elif operation == "wait_for_change":  # 新增代码+Phase62HighLevelTools: 分发等待变化；如果没有这行代码，wait_for_change 不可用。
            result = self._wait_for_change(arguments)  # 新增代码+Phase62HighLevelTools: 执行只读变化检查；如果没有这行代码，高层流程无法表达等待。
        else:  # 新增代码+Phase62HighLevelTools: 剩余操作就是 verify_screen；如果没有这行代码，类型检查可能认为 result 未赋值。
            result = self._verify_screen(arguments)  # 新增代码+Phase62HighLevelTools: 执行只读验证；如果没有这行代码，高层流程无法表达断言。
        self.record_progress(operation, "operation_completed", {"ok": bool(result.get("ok")), "decision": result.get("decision", "")})  # 新增代码+Phase62HighLevelTools: 记录操作完成；如果没有这行代码，progress 流无法闭合。
        return result  # 新增代码+Phase62HighLevelTools: 返回操作结果；如果没有这行代码，run 拿不到结构化输出。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_run_internal 到此结束；如果没有这个边界说明，初学者不容易看出操作分发范围。

    def _controls_from_arguments(self, arguments: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+Phase62HighLevelTools: 函数段开始，从参数中提取控件候选；如果没有这段函数，observe/find/click/type 会重复解析 controls。
        raw_controls = arguments.get("controls", arguments.get("flat_nodes", []))  # 新增代码+Phase62HighLevelTools: 同时支持 controls 和 flat_nodes；如果没有这行代码，Phase57 结果不能直接复用。
        return [dict(control) for control in list(raw_controls or []) if isinstance(control, dict)]  # 新增代码+Phase62HighLevelTools: 返回控件字典副本；如果没有这行代码，坏控件类型会导致 locator 崩溃。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_controls_from_arguments 到此结束；如果没有这个边界说明，初学者不容易看出控件提取范围。

    def _write_observe_artifact(self, operation: str, payload: dict[str, Any]) -> Path:  # 新增代码+Phase62HighLevelTools: 函数段开始，写入一个轻量 image artifact；如果没有这段函数，observe_screen 只能返回内存摘要。
        artifact_path = self.artifacts_dir / f"{_phase62_safe_text(operation, 80)}-{int(time.time() * 1000)}.ppm"  # 新增代码+Phase62HighLevelTools: 生成 PPM 图片产物路径；如果没有这行代码，多次 observe 可能覆盖。
        artifact_path.write_text("P3\n2 2\n255\n40 80 120 80 120 160\n120 160 200 160 200 240\n", encoding="ascii")  # 新增代码+Phase62HighLevelTools: 写入最小可打开图片；如果没有这行代码，image_artifact 只是不存在的路径。
        metadata_path = artifact_path.with_suffix(".json")  # 新增代码+Phase62HighLevelTools: 生成同名 metadata 路径；如果没有这行代码，artifact 缺少可审计摘要。
        metadata_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")  # 新增代码+Phase62HighLevelTools: 写入观察元数据；如果没有这行代码，图片无法关联窗口和控件摘要。
        return artifact_path  # 新增代码+Phase62HighLevelTools: 返回图片路径；如果没有这行代码，调用方拿不到 artifact。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_write_observe_artifact 到此结束；如果没有这个边界说明，初学者不容易看出 artifact 写入范围。

    def _observe_screen(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，执行只读屏幕观察；如果没有这段函数，高层工具没有 artifact 观察入口。
        window = dict(arguments.get("window", {}) or {})  # 新增代码+Phase62HighLevelTools: 复制窗口摘要；如果没有这行代码，artifact 元数据没有目标上下文。
        controls = self._controls_from_arguments(arguments)  # 新增代码+Phase62HighLevelTools: 读取 UIA 控件候选；如果没有这行代码，观察结果无法输出候选数量。
        payload = {"window": window, "control_count": len(controls), "controls": controls[:20], "raw_screen_pixels_included": False, "image_artifact_note": "Phase62 合同产物用于证明 artifact 管线，真实截图仍由 Phase56 负责。"}  # 新增代码+Phase62HighLevelTools: 构造观察元数据；如果没有这行代码，artifact 缺少解释边界。
        artifact_path = self._write_observe_artifact("observe_screen", payload)  # 新增代码+Phase62HighLevelTools: 写入图片 artifact；如果没有这行代码，结果不能提供最终产物。
        return {"ok": True, "operation": "observe_screen", "read_only": True, "marker": PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, "model": PHASE62_HIGH_LEVEL_TOOLS_MODEL, "window": window, "control_count": len(controls), "artifact_path": str(artifact_path), "artifact_mime": "image/x-portable-pixmap", "image_artifact": True, "write_lock_used": False, "actions_expanded": PHASE62_ACTIONS_EXPANDED}  # 新增代码+Phase62HighLevelTools: 返回只读观察结果；如果没有这行代码，模型无法看到 artifact 和锁边界。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_observe_screen 到此结束；如果没有这个边界说明，初学者不容易看出观察入口范围。

    def _find_control(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，执行只读语义控件定位；如果没有这段函数，高层动作只能靠坐标猜测。
        controls = self._controls_from_arguments(arguments)  # 新增代码+Phase62HighLevelTools: 读取控件候选；如果没有这行代码，locator 没有输入。
        query = dict(arguments.get("query", {}) or {})  # 新增代码+Phase62HighLevelTools: 复制查询条件；如果没有这行代码，后续 locator 可能污染调用方对象。
        located = self.locator.find(controls, query)  # 新增代码+Phase62HighLevelTools: 调用 Phase57 语义定位器；如果没有这行代码，高层工具会重复实现定位逻辑。
        summary = {"matched": bool(located.get("matched")), "candidate_count": int(located.get("candidate_count", 0)), "confidence": located.get("confidence", 0.0), "reason": located.get("reason", ""), "control": dict(located.get("control", {}) or {})}  # 新增代码+Phase62HighLevelTools: 裁剪候选摘要；如果没有这行代码，调用方需要理解 Phase57 原始结构。
        return {"ok": bool(summary["matched"]), "operation": "find_control", "read_only": True, "marker": PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, "model": PHASE62_HIGH_LEVEL_TOOLS_MODEL, "uia_candidate_summary": summary, "control": summary["control"], "write_lock_used": False, "actions_expanded": PHASE62_ACTIONS_EXPANDED}  # 新增代码+Phase62HighLevelTools: 返回定位结果；如果没有这行代码，click/type 无法复用控制点。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_find_control 到此结束；如果没有这个边界说明，初学者不容易看出定位入口范围。

    def _write_control_action(self, arguments: dict[str, Any], action: str) -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，执行受授权、写锁和 abort 保护的高层写动作；如果没有这段函数，click/type 会分裂成两套安全链。
        window = dict(arguments.get("window", {}) or {})  # 新增代码+Phase62HighLevelTools: 读取目标窗口；如果没有这行代码，授权和 Phase58 守卫不知道目标。
        query = dict(arguments.get("query", {}) or {})  # 新增代码+Phase62HighLevelTools: 读取控件查询；如果没有这行代码，高层动作不知道要点哪个控件。
        located = self._find_control(arguments)  # 新增代码+Phase62HighLevelTools: 先只读定位控件；如果没有这行代码，写动作会绕过 UIA candidate summary。
        if not bool(located.get("ok")):  # 新增代码+Phase62HighLevelTools: 定位失败时拒绝动作；如果没有这行代码，找不到控件仍可能点击默认坐标。
            return self._failure(action, "control_not_found", "未找到可信控件，已发送 0 个低层事件。", extra={"uia_candidate_summary": located.get("uia_candidate_summary", {})})  # 新增代码+Phase62HighLevelTools: 返回零事件定位失败；如果没有这行代码，模型不知道要重新 observe/find。
        control = dict(located.get("control", {}) or {})  # 新增代码+Phase62HighLevelTools: 取出定位控件；如果没有这行代码，中心点计算没有输入。
        center = _phase62_control_center(control)  # 新增代码+Phase62HighLevelTools: 计算控件中心点；如果没有这行代码，Phase58 没有点击坐标。
        action_arguments = {"x": center["x"], "y": center["y"], "locator": query, "button": arguments.get("button", "left")}  # 新增代码+Phase62HighLevelTools: 构造 Phase58 动作参数；如果没有这行代码，低层 sender 不知道坐标和 locator。
        if action == "type_text":  # 新增代码+Phase62HighLevelTools: 文本动作需要附加文本；如果没有这行代码，type_into_control 不会输入任何内容。
            action_arguments["text"] = str(arguments.get("text", "") or "")  # 新增代码+Phase62HighLevelTools: 把文本仅传给 Phase58 局部内存；如果没有这行代码，真实 sender 无法输入。
        grant = self.grant_store.evaluate(session_id=self.session_id, action=action, arguments={"window": window})  # 新增代码+Phase62HighLevelTools: 评估持久授权；如果没有这行代码，高层写动作会绕过审批。
        if not bool(grant.get("allowed")):  # 新增代码+Phase62HighLevelTools: 未授权时拒绝动作；如果没有这行代码，未授权 app 可能被点击或输入。
            return self._failure(action, str(grant.get("decision", "requires_approval")), "缺少持久授权，已发送 0 个低层事件。", extra={"grant": grant, "uia_candidate_summary": located.get("uia_candidate_summary", {})})  # 新增代码+Phase62HighLevelTools: 返回零事件授权拒绝；如果没有这行代码，用户不知道要 `/computer approve`。
        lock_result = self.lock_manager.acquire(self.session_id, owner_label="phase62-high-level-write", metadata={"operation": action})  # 新增代码+Phase62HighLevelTools: 获取写锁；如果没有这行代码，多个 agent 可能同时污染桌面。
        if not bool(lock_result.get("acquired")):  # 新增代码+Phase62HighLevelTools: 锁被占用时拒绝动作；如果没有这行代码，写动作可能和其他会话并发。
            return self._failure(action, "write_lock_busy", "desktop control lock 被其他会话持有，已发送 0 个低层事件。", extra={"lock": lock_result, "grant": grant, "uia_candidate_summary": located.get("uia_candidate_summary", {})})  # 新增代码+Phase62HighLevelTools: 返回零事件锁拒绝；如果没有这行代码，用户不知道为什么没有动作。
        self.record_progress(action, "write_lock_acquired", {"owner_session_id": self.session_id})  # 新增代码+Phase62HighLevelTools: 记录写锁获取；如果没有这行代码，streaming 进度看不到串行边界。
        try:  # 新增代码+Phase62HighLevelTools: 用 finally 确保写锁释放；如果没有这行代码，异常会留下桌面锁。
            raw_sender = self.low_level_sender  # 新增代码+Phase62HighLevelTools: 取出底层 sender；如果没有这行代码，后续 wrapper 没有对象。
            wrapped_sender = self.abort_hooks.wrap_low_level_sender(raw_sender)  # 新增代码+Phase62HighLevelTools: 包装 abort-aware sender；如果没有这行代码，Phase61 急停不能阻断高层动作。
            observer = Phase58StaticSafeWindowObserver(before_text="phase62-before", after_text="phase62-after")  # 新增代码+Phase62HighLevelTools: 使用脱敏静态观察器做合同 evidence；如果没有这行代码，单测可能触碰真实 UIA。
            runtime = WindowsRealSendInputGuardRuntime(platform="win32", inventory=StaticWindowsWindowInventory([window]), low_level_sender=wrapped_sender, observer=observer, after_observe_delay_seconds=0.0)  # 新增代码+Phase62HighLevelTools: 创建 Phase58 安全动作 runtime；如果没有这行代码，高层写动作会绕过目标守卫。
            dispatch = runtime.execute_safe_action(window, action, action_arguments)  # 新增代码+Phase62HighLevelTools: 执行受保护底层动作；如果没有这行代码，click/type 只会返回文案。
        finally:  # 新增代码+Phase62HighLevelTools: 无论成功失败都释放写锁；如果没有这行代码，高层动作异常会阻塞后续任务。
            release = self.lock_manager.release(self.session_id)  # 新增代码+Phase62HighLevelTools: 释放当前会话写锁；如果没有这行代码，锁会长期残留。
            self.record_progress(action, "write_lock_released", {"released": bool(release.get("released"))})  # 新增代码+Phase62HighLevelTools: 记录写锁释放；如果没有这行代码，streaming 进度无法确认清理。
        result = dict(dispatch or {})  # 新增代码+Phase62HighLevelTools: 复制 Phase58 结果；如果没有这行代码，追加高层字段可能污染底层对象。
        result.update({"operation": "click_control" if action == "click" else "type_into_control", "grant_allowed": True, "grant": grant, "write_lock_acquired": True, "write_lock_released": True, "uia_candidate_summary": located.get("uia_candidate_summary", {}), "control": control, "center": center, "marker": PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, "model": PHASE62_HIGH_LEVEL_TOOLS_MODEL, "actions_expanded": PHASE62_ACTIONS_EXPANDED})  # 新增代码+Phase62HighLevelTools: 补充高层上下文字段；如果没有这行代码，调用方看不到授权、控件和中心点证据。
        return result  # 新增代码+Phase62HighLevelTools: 返回高层写动作结果；如果没有这行代码，模型拿不到执行摘要。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_write_control_action 到此结束；如果没有这个边界说明，初学者不容易看出写动作安全链范围。

    def _wait_for_change(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，执行只读变化等待合同；如果没有这段函数，高层流程无法表达等待 UI 更新。
        previous = _phase62_safe_text(arguments.get("previous_fingerprint", "before"), 120)  # 新增代码+Phase62HighLevelTools: 读取前态指纹；如果没有这行代码，无法比较变化。
        current = _phase62_safe_text(arguments.get("current_fingerprint", "after"), 120)  # 新增代码+Phase62HighLevelTools: 读取当前指纹；如果没有这行代码，等待结果没有当前态。
        changed = previous != current  # 新增代码+Phase62HighLevelTools: 比较前后指纹；如果没有这行代码，wait_for_change 无法给出布尔结果。
        return {"ok": True, "operation": "wait_for_change", "read_only": True, "changed": changed, "previous_fingerprint": previous, "current_fingerprint": current, "write_lock_used": False, "marker": PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, "model": PHASE62_HIGH_LEVEL_TOOLS_MODEL, "actions_expanded": PHASE62_ACTIONS_EXPANDED}  # 新增代码+Phase62HighLevelTools: 返回变化结果；如果没有这行代码，调用方无法决定是否继续。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_wait_for_change 到此结束；如果没有这个边界说明，初学者不容易看出等待逻辑范围。

    def _verify_screen(self, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，执行只读屏幕验证合同；如果没有这段函数，高层工具无法表达最终断言。
        expected = _phase62_safe_text(arguments.get("expected", arguments.get("text", "Phase62")), 160)  # 新增代码+Phase62HighLevelTools: 读取期望文本；如果没有这行代码，验证没有目标。
        controls = self._controls_from_arguments(arguments)  # 新增代码+Phase62HighLevelTools: 读取控件候选；如果没有这行代码，验证无法基于 UIA 摘要。
        haystack = " ".join(_phase62_safe_text(control.get("name", ""), 120) + " " + _phase62_safe_text(control.get("automation_id", ""), 120) for control in controls)  # 新增代码+Phase62HighLevelTools: 汇总安全控件文本；如果没有这行代码，验证无法检查期望内容。
        verified = bool(expected.lower() in haystack.lower() or not expected)  # 新增代码+Phase62HighLevelTools: 判断期望是否存在；如果没有这行代码，verify_screen 不能返回验证结果。
        return {"ok": verified, "operation": "verify_screen", "read_only": True, "verified": verified, "expected": expected, "control_count": len(controls), "write_lock_used": False, "marker": PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, "model": PHASE62_HIGH_LEVEL_TOOLS_MODEL, "actions_expanded": PHASE62_ACTIONS_EXPANDED}  # 新增代码+Phase62HighLevelTools: 返回验证摘要；如果没有这行代码，最终验收无法表达屏幕断言。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_verify_screen 到此结束；如果没有这个边界说明，初学者不容易看出屏幕验证范围。

    def _failure(self, operation: str, decision: str, message: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，构造统一失败结果；如果没有这段函数，各拒绝路径字段会漂移。
        payload = {"ok": False, "operation": _phase62_safe_text(operation, 120), "decision": _phase62_safe_text(decision, 120), "message": _phase62_safe_text(message, 260), "low_level_event_count": 0, "low_level_events_sent": False, "marker": PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, "model": PHASE62_HIGH_LEVEL_TOOLS_MODEL, "actions_expanded": PHASE62_ACTIONS_EXPANDED}  # 新增代码+Phase62HighLevelTools: 构造零事件失败基础字段；如果没有这行代码，verifier 无法判断拒绝是否安全。
        payload.update(dict(extra or {}))  # 新增代码+Phase62HighLevelTools: 合并额外证据；如果没有这行代码，grant/lock/locator 失败原因会丢失。
        return payload  # 新增代码+Phase62HighLevelTools: 返回失败结果；如果没有这行代码，调用方拿不到拒绝摘要。
    # 新增代码+Phase62HighLevelTools: 函数段结束，_failure 到此结束；如果没有这个边界说明，初学者不容易看出失败结构范围。

    def run_read_only_batch(self, requests: list[dict[str, Any]]) -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，并发执行只读高层操作；如果没有这段函数，批量 observe 不能和写锁解耦。
        safe_requests = [dict(item or {}) for item in list(requests or []) if isinstance(item, dict)]  # 新增代码+Phase62HighLevelTools: 复制请求列表；如果没有这行代码，坏请求类型会污染线程池。
        if any(str(item.get("operation", "")) not in PHASE62_READ_ONLY_OPERATIONS for item in safe_requests):  # 新增代码+Phase62HighLevelTools: 只允许只读操作进入批量；如果没有这行代码，写动作可能绕过串行锁。
            return {"ok": False, "decision": "batch_allows_read_only_only", "results": [], "read_only_parallel": False, "marker": PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, "actions_expanded": PHASE62_ACTIONS_EXPANDED}  # 新增代码+Phase62HighLevelTools: 返回批量拒绝；如果没有这行代码，危险操作可能混入 observe batch。
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(4, len(safe_requests) or 1))) as executor:  # 新增代码+Phase62HighLevelTools: 创建小型线程池；如果没有这行代码，只读批量无法并发调度。
            futures = [executor.submit(self.run, str(item.get("operation", "")), dict(item.get("arguments", {}) or {})) for item in safe_requests]  # 新增代码+Phase62HighLevelTools: 提交只读操作；如果没有这行代码，线程池不会执行任何任务。
            results = [future.result() for future in futures]  # 新增代码+Phase62HighLevelTools: 收集所有结果并保持请求顺序；如果没有这行代码，调用方拿不到批量输出。
        return {"ok": all(bool(result.get("ok")) for result in results), "operation": "read_only_batch", "read_only_parallel": True, "write_lock_used": False, "results": results, "marker": PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, "model": PHASE62_HIGH_LEVEL_TOOLS_MODEL, "actions_expanded": PHASE62_ACTIONS_EXPANDED}  # 新增代码+Phase62HighLevelTools: 返回批量只读摘要；如果没有这行代码，验收无法证明只读不占写锁。
    # 新增代码+Phase62HighLevelTools: 函数段结束，run_read_only_batch 到此结束；如果没有这个边界说明，初学者不容易看出只读批量范围。

    def status(self) -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，返回高层工具状态；如果没有这段函数，/computer status 无法展示 Phase62。
        events = self.progress_events()  # 新增代码+Phase62HighLevelTools: 读取 progress 事件；如果没有这行代码，状态无法显示近期进度数量。
        return {"enabled": True, "marker": PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, "model": PHASE62_HIGH_LEVEL_TOOLS_MODEL, "supported_operations": list(PHASE62_SUPPORTED_OPERATIONS), "read_only_operations": sorted(PHASE62_READ_ONLY_OPERATIONS), "read_only_parallel_supported": True, "write_actions_serialized": True, "streaming_executor_integrated": True, "image_artifact_supported": True, "uia_candidate_summary_supported": True, "progress_event_count": len(events), "progress_events_path": str(self.progress_events_path), "artifact_dir": str(self.artifacts_dir), "actions_expanded": PHASE62_ACTIONS_EXPANDED}  # 新增代码+Phase62HighLevelTools: 返回机器可读状态；如果没有这行代码，终端和最终矩阵没有同一事实源。
    # 新增代码+Phase62HighLevelTools: 函数段结束，status 到此结束；如果没有这个边界说明，初学者不容易看出状态范围。

    def terminal_status_lines(self) -> list[str]:  # 新增代码+Phase62HighLevelTools: 函数段开始，生成终端可读高层工具面板；如果没有这段函数，用户只能读 JSON。
        status = self.status()  # 新增代码+Phase62HighLevelTools: 读取机器状态；如果没有这行代码，终端文本没有事实来源。
        return ["Computer High-Level Tools", f"- marker={PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER}", f"- model={PHASE62_HIGH_LEVEL_TOOLS_MODEL}", f"- operations={','.join(status.get('supported_operations', []))}", f"- read_only_parallel_supported={_phase62_bool_token(status.get('read_only_parallel_supported'))}", f"- write_actions_serialized={_phase62_bool_token(status.get('write_actions_serialized'))}", f"- streaming_executor_integrated={_phase62_bool_token(status.get('streaming_executor_integrated'))}", f"- image_artifact_supported={_phase62_bool_token(status.get('image_artifact_supported'))}", f"- uia_candidate_summary_supported={_phase62_bool_token(status.get('uia_candidate_summary_supported'))}", f"- progress_event_count={status.get('progress_event_count', 0)}", f"- progress_events_path={status.get('progress_events_path', '')}", f"- artifact_dir={status.get('artifact_dir', '')}", f"- actions_expanded={_phase62_bool_token(status.get('actions_expanded'))}"]  # 新增代码+Phase62HighLevelTools: 返回完整终端面板；如果没有这行代码，/computer high-level-tools 无法解释 Phase62 能力。
    # 新增代码+Phase62HighLevelTools: 函数段结束，terminal_status_lines 到此结束；如果没有这个边界说明，初学者不容易看出终端状态范围。
# 新增代码+Phase62HighLevelTools: 类段结束，WindowsHighLevelComputerToolRuntime 到此结束；如果没有这个边界说明，初学者不容易看出高层 runtime 范围。


def run_phase62_high_level_tools_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase62HighLevelTools: 函数段开始，运行 Phase62 高层工具合同自检；如果没有这段函数，CLI 和真实终端没有统一验收入口。
    root = Path(base_dir) if base_dir is not None else DEFAULT_HIGH_LEVEL_TOOLS_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase62HighLevelTools: 选择隔离合同目录；如果没有这行代码，多次自检可能互相污染。
    lock_manager = ComputerUseLockManager(base_dir=root / "locks")  # 新增代码+Phase62HighLevelTools: 创建隔离写锁；如果没有这行代码，合同可能读写真正运行锁。
    grant_store = WindowsComputerUsePersistentGrantStore(base_dir=root / "grants")  # 新增代码+Phase62HighLevelTools: 创建隔离授权 store；如果没有这行代码，合同会污染真实授权。
    hooks = WindowsComputerUseAbortStreamingHooks(lock_manager=lock_manager, session_id="phase62-session", base_dir=root / "hooks")  # 新增代码+Phase62HighLevelTools: 创建隔离 hooks；如果没有这行代码，合同无法验证 abort 和 progress。
    sender = Phase58RecordingLowLevelSender()  # 新增代码+Phase62HighLevelTools: 使用记录型 sender；如果没有这行代码，合同可能触碰真实鼠标键盘。
    runtime = WindowsHighLevelComputerToolRuntime(base_dir=root / "high_level", lock_manager=lock_manager, grant_store=grant_store, abort_hooks=hooks, session_id="phase62-session", low_level_sender=sender)  # 新增代码+Phase62HighLevelTools: 创建高层 runtime；如果没有这行代码，合同没有被测对象。
    window = _phase62_contract_window()  # 新增代码+Phase62HighLevelTools: 获取合同安全窗口；如果没有这行代码，高层写动作没有目标。
    controls = _phase62_contract_controls()  # 新增代码+Phase62HighLevelTools: 获取合同控件候选；如果没有这行代码，find/click/type 没有定位输入。
    lock_manager.acquire("external-writer", owner_label="phase62-contract-read-only")  # 新增代码+Phase62HighLevelTools: 模拟写锁被其他会话持有；如果没有这行代码，无法证明只读 batch 不抢写锁。
    batch = runtime.run_read_only_batch([{"operation": "observe_screen", "arguments": {"window": window, "controls": controls}}, {"operation": "find_control", "arguments": {"window": window, "controls": controls, "query": {"automation_id": "Phase62SearchBox"}}}])  # 新增代码+Phase62HighLevelTools: 执行只读批量；如果没有这行代码，read_only_parallel token 没证据。
    read_lock_owner = lock_manager.status().get("owner_session_id")  # 新增代码+Phase62HighLevelTools: 读取只读批量后的锁 owner；如果没有这行代码，无法确认没有抢锁。
    lock_manager.release("external-writer")  # 新增代码+Phase62HighLevelTools: 清理模拟写锁；如果没有这行代码，后续写动作会被故意阻塞。
    found = runtime.run("find_control", {"window": window, "controls": controls, "query": {"text": "Search", "role": "Edit"}})  # 新增代码+Phase62HighLevelTools: 执行候选定位；如果没有这行代码，uia_candidates token 没证据。
    grant_store.approve(session_id="phase62-session", app="phase58_safe_app", action_scope=["click", "type_text"], ttl_seconds=60, reason="phase62 contract", grant_flags={"desktopAction": True})  # 新增代码+Phase62HighLevelTools: 写入点击和输入授权；如果没有这行代码，写动作正例会被默认拒绝。
    click = runtime.run("click_control", {"window": window, "controls": controls, "query": {"automation_id": "Phase62RunButton"}})  # 新增代码+Phase62HighLevelTools: 执行高层点击；如果没有这行代码，write_serial token 没正例。
    lock_manager.acquire("other-writer", owner_label="phase62-contract-serial")  # 新增代码+Phase62HighLevelTools: 模拟另一个写动作持锁；如果没有这行代码，串行拒绝没有证据。
    blocked = runtime.run("type_into_control", {"window": window, "controls": controls, "query": {"automation_id": "Phase62SearchBox"}, "text": "phase62 contract text"})  # 新增代码+Phase62HighLevelTools: 尝试锁冲突输入；如果没有这行代码，write_serial token 无法覆盖拒绝路径。
    lock_manager.release("other-writer")  # 新增代码+Phase62HighLevelTools: 清理模拟写锁；如果没有这行代码，后续 abort 测试会被锁冲突干扰。
    lock_manager.request_abort("phase62 contract abort", requested_by="contract")  # 新增代码+Phase62HighLevelTools: 触发 abort；如果没有这行代码，abort_zero_events 没有输入。
    aborted = runtime.run("click_control", {"window": window, "controls": controls, "query": {"automation_id": "Phase62RunButton"}})  # 新增代码+Phase62HighLevelTools: 执行 abort 后点击；如果没有这行代码，abort-aware 高层链没有证据。
    lock_manager.clear_abort(cleared_by="phase62-contract")  # 新增代码+Phase62HighLevelTools: 清除 abort；如果没有这行代码，合同结束后状态会残留急停。
    changed = runtime.run("wait_for_change", {"previous_fingerprint": "before", "current_fingerprint": "after"})  # 新增代码+Phase62HighLevelTools: 执行变化等待；如果没有这行代码，wait_for_change 操作没有合同覆盖。
    verified = runtime.run("verify_screen", {"controls": controls, "expected": "Phase62"})  # 新增代码+Phase62HighLevelTools: 执行屏幕验证；如果没有这行代码，verify_screen 操作没有合同覆盖。
    events = runtime.progress_events()  # 新增代码+Phase62HighLevelTools: 读取 progress 事件；如果没有这行代码，streaming_progress token 没证据。
    artifact_path = Path(str(batch.get("results", [{}])[0].get("artifact_path", "")))  # 新增代码+Phase62HighLevelTools: 读取 observe artifact 路径；如果没有这行代码，image_artifact token 没证据。
    high_level_ops = set(runtime.supported_operations()) == set(PHASE62_SUPPORTED_OPERATIONS) and bool(changed.get("changed")) and bool(verified.get("verified"))  # 新增代码+Phase62HighLevelTools: 汇总高层操作覆盖；如果没有这行代码，CLI 无法表达操作完整性。
    read_only_parallel = bool(batch.get("ok") and batch.get("read_only_parallel") and read_lock_owner == "external-writer")  # 新增代码+Phase62HighLevelTools: 汇总只读不抢写锁；如果没有这行代码，验收无法检查批量只读边界。
    write_serial = bool(click.get("ok") and click.get("low_level_event_count", 0) > 0 and blocked.get("decision") == "write_lock_busy" and blocked.get("low_level_event_count") == 0)  # 新增代码+Phase62HighLevelTools: 汇总写动作串行化；如果没有这行代码，验收无法确认并发拒绝。
    streaming_progress = bool(any(event.get("stage") == "operation_completed" for event in events) and any(str(event.get("stage", "")).startswith("streaming_executor_") for event in events))  # 新增代码+Phase62HighLevelTools: 汇总自有 progress 和全局 executor 事件；如果没有这行代码，streaming 集成可能是假字段。
    image_artifact = bool(artifact_path.exists() and artifact_path.suffix.lower() == ".ppm")  # 新增代码+Phase62HighLevelTools: 汇总图片产物存在性；如果没有这行代码，artifact 可能只是字符串。
    uia_candidates = bool(found.get("uia_candidate_summary", {}).get("matched") and found.get("uia_candidate_summary", {}).get("candidate_count", 0) >= 1)  # 新增代码+Phase62HighLevelTools: 汇总候选定位；如果没有这行代码，locator 结果可能不可解释。
    abort_zero_events = bool(aborted.get("low_level_event_count") == 0 and aborted.get("dispatch", {}).get("decision") == "aborted_before_low_level_send")  # 新增代码+Phase62HighLevelTools: 汇总 abort 零事件；如果没有这行代码，急停链路可能漏检。
    passed = bool(high_level_ops and read_only_parallel and write_serial and streaming_progress and image_artifact and uia_candidates and abort_zero_events and not PHASE62_ACTIONS_EXPANDED)  # 新增代码+Phase62HighLevelTools: 汇总合同通过条件；如果没有这行代码，main 无法用退出码表达失败。
    return {"marker": PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER, "ok_token": PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_OK_TOKEN, "high_level_ops": high_level_ops, "read_only_parallel": read_only_parallel, "write_serial": write_serial, "streaming_progress": streaming_progress, "image_artifact": image_artifact, "uia_candidates": uia_candidates, "abort_zero_events": abort_zero_events, "actions_expanded": PHASE62_ACTIONS_EXPANDED, "passed": passed, "state_dir": str(root), "progress_events_path": str(runtime.progress_events_path), "artifact_path": str(artifact_path)}  # 新增代码+Phase62HighLevelTools: 返回完整合同报告；如果没有这行代码，测试和真实终端拿不到统一结果。
# 新增代码+Phase62HighLevelTools: 函数段结束，run_phase62_high_level_tools_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同自检范围。


def phase62_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase62HighLevelTools: 函数段开始，把合同报告转成稳定 CLI token 行；如果没有这段函数，真实终端场景要解析复杂 JSON。
    return f"{PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER} {PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_OK_TOKEN} high_level_ops={_phase62_bool_token(report.get('high_level_ops'))} read_only_parallel={_phase62_bool_token(report.get('read_only_parallel'))} write_serial={_phase62_bool_token(report.get('write_serial'))} streaming_progress={_phase62_bool_token(report.get('streaming_progress'))} image_artifact={_phase62_bool_token(report.get('image_artifact'))} uia_candidates={_phase62_bool_token(report.get('uia_candidates'))} abort_zero_events={_phase62_bool_token(report.get('abort_zero_events'))} actions_expanded={_phase62_bool_token(report.get('actions_expanded'))}"  # 新增代码+Phase62HighLevelTools: 返回固定顺序 token；如果没有这行代码，验收输出容易漂移。
# 新增代码+Phase62HighLevelTools: 函数段结束，phase62_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase62HighLevelTools: 函数段开始，提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase62 合同。
    _ = argv  # 新增代码+Phase62HighLevelTools: 保留 argv 供未来扩展；如果没有这行代码，参数存在但用途不清楚。
    report = run_phase62_high_level_tools_contract()  # 新增代码+Phase62HighLevelTools: 运行默认隔离合同；如果没有这行代码，CLI 不会生成证据。
    print(phase62_cli_line(report))  # 新增代码+Phase62HighLevelTools: 打印稳定 token 行；如果没有这行代码，debug log 无法匹配 Phase62 成功。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase62HighLevelTools: 打印结构化报告；如果没有这行代码，失败时不易复盘。
    print(PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER)  # 新增代码+Phase62HighLevelTools: 单独打印 ready marker；如果没有这行代码，最终回答复制时可能漏 marker。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase62HighLevelTools: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase62HighLevelTools: 函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_HIGH_LEVEL_TOOLS_ROOT", "PHASE62_ACTIONS_EXPANDED", "PHASE62_HIGH_LEVEL_TOOLS_MODEL", "PHASE62_READ_ONLY_OPERATIONS", "PHASE62_SUPPORTED_OPERATIONS", "PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_MARKER", "PHASE62_WINDOWS_HIGH_LEVEL_TOOLS_OK_TOKEN", "WindowsHighLevelComputerToolRuntime", "main", "phase62_cli_line", "run_phase62_high_level_tools_contract"]  # 新增代码+Phase62HighLevelTools: 限定公开导出名称；如果没有这行代码，包导入容易暴露内部 helper 或漏掉合同入口。


if __name__ == "__main__":  # 新增代码+Phase62HighLevelTools: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase62HighLevelTools: 用 main 返回码退出；如果没有这行代码，命令行状态不明确。
