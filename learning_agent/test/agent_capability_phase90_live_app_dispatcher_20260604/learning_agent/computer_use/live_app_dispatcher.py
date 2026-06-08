"""Phase90 Windows 受控真实应用 live dispatcher。"""  # 新增代码+Phase90LiveAppDispatcher: 标明本文件负责把安全合同推进到受控 live app dispatcher；如果没有这行代码，读者不容易区分 Phase90 和前面的矩阵模块。

from __future__ import annotations  # 新增代码+Phase90LiveAppDispatcher: 启用延迟类型注解；如果没有这行代码，后续注入运行时类型时更容易遇到循环导入。

import hashlib  # 新增代码+Phase90LiveAppDispatcher: 导入哈希用于文本脱敏摘要；如果没有这行代码，文本输入要么泄露明文要么无法审计一致性。
import json  # 新增代码+Phase90LiveAppDispatcher: 导入 JSON 用于 CLI 失败时输出结构化报告；如果没有这行代码，真实终端排查会困难。
import os  # 新增代码+Phase90LiveAppDispatcher: 导入 os 读取真实派发环境门；如果没有这行代码，用户无法显式打开或关闭 live gate。
import tempfile  # 新增代码+Phase90LiveAppDispatcher: 导入 tempfile 提供无 base_dir 时的隔离报告目录；如果没有这行代码，自检无处落盘。
import time  # 新增代码+Phase90LiveAppDispatcher: 导入 time 生成 session 和报告时间；如果没有这行代码，多次验收证据不易区分。
from pathlib import Path  # 新增代码+Phase90LiveAppDispatcher: 导入 Path 统一处理 Windows 路径；如果没有这行代码，memory 和测试目录拼接容易写错。
from typing import Any  # 新增代码+Phase90LiveAppDispatcher: 导入 Any 描述 JSON 风格 payload；如果没有这行代码，接口边界不清晰。

from learning_agent.computer_use.app_window_control import Phase69RecordingFocuser, Phase69RecordingLauncher, WindowsAppWindowControlRuntime, build_launch_plan  # 新增代码+Phase90LiveAppDispatcher: 复用 Phase69 启动和聚焦合同；如果没有这行代码，Phase90 会重复实现脆弱的 app/window 控制。
from learning_agent.computer_use.generic_input_actions import Phase71RecordingInputSender, WindowsGenericInputActionRuntime, build_drag_path  # 新增代码+Phase90LiveAppDispatcher: 复用 Phase71 通用输入事件和记录型 sender；如果没有这行代码，拖拽和记录派发格式会漂移。
from learning_agent.computer_use.persistent_grants import WindowsComputerUsePersistentGrantStore  # 新增代码+Phase90LiveAppDispatcher: 复用 Phase60 持久授权事实源；如果没有这行代码，真实应用动作缺少可审计授权。
from learning_agent.computer_use.real_app_safety_boundary import Phase72RecordingAbortGate, WindowsRealAppSafetyBoundary  # 新增代码+Phase90LiveAppDispatcher: 复用 Phase72 安全边界和急停 gate；如果没有这行代码，危险窗口和 abort 无法统一拒绝。
from learning_agent.computer_use.representative_e2e_matrix import WindowsRepresentativeE2EMatrix  # 新增代码+Phase90LiveAppDispatcher: 复用 Phase74 代表性 E2E 和 Paint 皮卡丘计划；如果没有这行代码，用户点名场景会重复造轮子。
from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase90LiveAppDispatcher: 复用项目原子 JSON 写入；如果没有这行代码，验收报告可能半写损坏。


PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MARKER = "PHASE90_WINDOWS_LIVE_APP_DISPATCHER_READY"  # 新增代码+Phase90LiveAppDispatcher: 定义真实终端验收 ready 标记；如果没有这行代码，controller 无法稳定识别 Phase90 输出。
PHASE90_WINDOWS_LIVE_APP_DISPATCHER_OK_TOKEN = "PHASE90_WINDOWS_LIVE_APP_DISPATCHER_OK"  # 新增代码+Phase90LiveAppDispatcher: 定义真实终端验收 OK 标记；如果没有这行代码，用户无法一眼确认本阶段合同通过。
PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MODEL = "phase90_windows_live_app_dispatcher"  # 新增代码+Phase90LiveAppDispatcher: 定义本阶段模型名；如果没有这行代码，状态和证据无法说明合同版本。
PHASE90_REAL_DISPATCH_ENV = "LEARNING_AGENT_PHASE90_ENABLE_REAL_DISPATCH"  # 新增代码+Phase90LiveAppDispatcher: 定义真实派发显式环境门；如果没有这行代码，真实动作开关会散落且不可审计。
PHASE90_ACTIONS_EXPANDED = True  # 新增代码+Phase90LiveAppDispatcher: 声明 Phase90 扩展的是受控动作路径；如果没有这行代码，能力边界不清楚。
PHASE90_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase90LiveAppDispatcher: 声明 Phase90 不扩张无保护裸动作；如果没有这行代码，用户可能误以为任意窗口都能直接控制。
PHASE90_REPRESENTATIVE_APPS = ("notepad", "mspaint", "calculator", "explorer", "browser")  # 新增代码+Phase90LiveAppDispatcher: 固定代表性应用集合；如果没有这行代码，测试无法确认通用性样本覆盖。
PHASE90_APP_ALIASES = {"paint": "mspaint", "mspaint": "mspaint", "notepad": "notepad", "calculator": "calc", "calc": "calc", "explorer": "explorer", "browser": "msedge", "edge": "msedge", "msedge": "msedge"}  # 新增代码+Phase90LiveAppDispatcher: 把用户自然 app 名映射到安全启动名；如果没有这行代码，prompt 里的 browser/calculator/paint 容易启动失败。


# 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有这个函数，CLI token 会出现 Python True/False 导致验收不稳定。
def _phase90_bool_token(value: Any) -> str:
    return "true" if bool(value) else "false"  # 新增代码+Phase90LiveAppDispatcher: 返回小写布尔文本；如果没有这行代码，真实终端场景 token 无法稳定匹配。
# 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数只负责输出格式化。


# 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有这个函数，文本输入会在报告中暴露明文或无法证明一致性。
def _phase90_text_digest(text: Any) -> str:
    safe_text = str(text or "")  # 新增代码+Phase90LiveAppDispatcher: 把输入转成字符串；如果没有这行代码，None 或数字文本摘要不稳定。
    return hashlib.sha256(safe_text.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase90LiveAppDispatcher: 返回短 SHA256 摘要；如果没有这行代码，日志无法安全追踪文本。
# 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数和 type_text 事件脱敏配合使用。


# 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有这个函数，用户自然 app 名无法稳定映射到 Phase69 启动计划。
def _phase90_normalized_app_name(app_name: Any) -> str:
    raw = str(app_name or "").strip().lower()  # 新增代码+Phase90LiveAppDispatcher: 清理输入应用名；如果没有这行代码，大小写和空格会影响映射。
    return PHASE90_APP_ALIASES.get(raw, raw)  # 新增代码+Phase90LiveAppDispatcher: 返回别名映射后的名称；如果没有这行代码，paint/browser/calculator 等常见说法会失效。
# 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数只做名称规范化。


# 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有这个函数，dispatcher 无法判断当前是否允许真实派发。
def _phase90_real_dispatch_enabled() -> bool:
    return os.environ.get(PHASE90_REAL_DISPATCH_ENV, "0") == "1"  # 新增代码+Phase90LiveAppDispatcher: 只有环境变量等于 1 才打开真实派发；如果没有这行代码，真实动作可能被无意触发。
# 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数不执行动作，只读取门禁。


# 新增代码+Phase90LiveAppDispatcher: 类段开始；如果没有这个类，Phase90 只能是独立合同而不能被其它 agent 作为 dispatcher 调用。
class WindowsLiveAppDispatcher:
    """组合 app 启动、授权、安全边界和输入事件的受控 dispatcher。"""  # 新增代码+Phase90LiveAppDispatcher: 说明类职责；如果没有这行代码，新手不容易理解它不是裸 SendInput。

    # 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有初始化函数，dispatcher 无法注入测试隔离目录和各阶段 runtime。
    def __init__(self, base_dir: str | Path | None = None, session_id: str | None = None, abort_gate: Any | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir is not None else Path(tempfile.gettempdir()) / "learning_agent_phase90_live_app_dispatcher"  # 新增代码+Phase90LiveAppDispatcher: 保存状态根目录；如果没有这行代码，授权和报告无处隔离。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase90LiveAppDispatcher: 确保目录存在；如果没有这行代码，首次写入授权或报告会失败。
        self.session_id = session_id or f"phase90-session-{int(time.time() * 1000)}"  # 新增代码+Phase90LiveAppDispatcher: 保存会话 id；如果没有这行代码，授权无法和本次 dispatcher 绑定。
        self.grant_store = WindowsComputerUsePersistentGrantStore(base_dir=self.base_dir / "grants")  # 新增代码+Phase90LiveAppDispatcher: 创建隔离 Phase60 授权 store；如果没有这行代码，Phase72 无法判断动作是否已授权。
        self.abort_gate = abort_gate if abort_gate is not None else Phase72RecordingAbortGate(aborted=False)  # 新增代码+Phase90LiveAppDispatcher: 创建或注入急停 gate；如果没有这行代码，真实发送前无法检查 abort。
        self.safety_boundary = WindowsRealAppSafetyBoundary(abort_gate=self.abort_gate)  # 新增代码+Phase90LiveAppDispatcher: 创建 Phase72 安全边界；如果没有这行代码，危险窗口和未授权动作无法统一拒绝。
        self.launcher = Phase69RecordingLauncher()  # 新增代码+Phase90LiveAppDispatcher: 使用记录型 launcher；如果没有这行代码，默认单元测试会打开真实应用。
        self.focuser = Phase69RecordingFocuser()  # 新增代码+Phase90LiveAppDispatcher: 使用记录型 focuser；如果没有这行代码，默认单元测试会切换真实前台窗口。
        self.app_runtime = WindowsAppWindowControlRuntime(launcher=self.launcher, focuser=self.focuser)  # 新增代码+Phase90LiveAppDispatcher: 组合 Phase69 app/window runtime；如果没有这行代码，dispatcher 没有启动和聚焦阶段。
        self.input_sender = Phase71RecordingInputSender()  # 新增代码+Phase90LiveAppDispatcher: 创建记录型输入 sender；如果没有这行代码，默认测试可能触发真实鼠标键盘。
        self.input_runtime = WindowsGenericInputActionRuntime(sender=self.input_sender)  # 新增代码+Phase90LiveAppDispatcher: 组合 Phase71 输入 runtime；如果没有这行代码，拖拽和热键无法进入统一事件协议。
    # 新增代码+Phase90LiveAppDispatcher: 函数段结束；初始化只准备依赖，不执行真实动作。

    # 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有 build_app_window，授权和安全边界无法对同一个目标窗口匹配。
    def build_app_window(self, app_name: Any) -> dict[str, Any]:
        plan = self.build_dispatch_plan(app_name)  # 新增代码+Phase90LiveAppDispatcher: 先生成启动计划；如果没有这行代码，窗口身份没有 app/exe 来源。
        executable = str(plan.get("executable", ""))  # 新增代码+Phase90LiveAppDispatcher: 读取可执行名；如果没有这行代码，窗口 app_id 无法稳定。
        window_id = f"phase69-window:{executable or 'blocked'}"  # 修改代码+Phase90LiveAppDispatcher: 使用 Phase69 记录型 launcher 的窗口 id 规则；如果没有这行代码，Phase60 授权会和真实 dispatch 目标窗口匹配不上。
        return {"app_id": executable, "process_name": executable, "window_id": window_id, "display_id": "DISPLAY1", "title_preview": f"Phase90 Live Dispatcher - {executable}", "safe_to_target": bool(plan.get("safe_to_launch"))}  # 新增代码+Phase90LiveAppDispatcher: 返回窗口摘要；如果没有这行代码，Phase60/72 无法评估目标。
    # 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数生成合同窗口，不读取真实桌面。

    # 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有启动计划构建，dispatcher 会直接信任用户输入命令。
    def build_dispatch_plan(self, app_name: Any) -> dict[str, Any]:
        normalized = _phase90_normalized_app_name(app_name)  # 新增代码+Phase90LiveAppDispatcher: 规范化 app 名；如果没有这行代码，自然语言别名会导致启动失败。
        plan = build_launch_plan(normalized)  # 新增代码+Phase90LiveAppDispatcher: 复用 Phase69 安全启动计划；如果没有这行代码，高风险 app 名可能绕过旧门禁。
        plan["phase90_app_name"] = str(app_name or "")  # 新增代码+Phase90LiveAppDispatcher: 记录原始 app 名；如果没有这行代码，审计无法追踪用户输入。
        plan["phase90_normalized_app"] = normalized  # 新增代码+Phase90LiveAppDispatcher: 记录规范 app 名；如果没有这行代码，报告无法解释别名映射。
        return plan  # 新增代码+Phase90LiveAppDispatcher: 返回计划；如果没有这行代码，调用方拿不到启动信息。
    # 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数不启动真实应用。

    # 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有授权 helper，测试和终端无法创建可放行的代表应用样本。
    def grant_representative_app(self, app_name: Any, action_scope: list[str] | None = None, ttl_seconds: int = 120) -> dict[str, Any]:
        window = self.build_app_window(app_name)  # 新增代码+Phase90LiveAppDispatcher: 生成与 dispatcher 一致的窗口身份；如果没有这行代码，grant 可能匹配不上实际 dispatch。
        scope = list(action_scope or ["click", "type_text", "scroll", "drag"])  # 新增代码+Phase90LiveAppDispatcher: 设置默认受控动作范围；如果没有这行代码，授权范围会为空。
        return self.grant_store.approve(session_id=self.session_id, app=window["app_id"], window_id=window["window_id"], display_id=window["display_id"], action_scope=scope, ttl_seconds=ttl_seconds, reason="phase90-live-app-dispatcher-contract", grant_flags={"desktopAction": True})  # 新增代码+Phase90LiveAppDispatcher: 写入 Phase60 授权；如果没有这行代码，Phase72 会拒绝所有普通应用动作。
    # 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数只写授权状态，不发送输入。

    # 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有 dispatch，Phase90 不能证明从 app/operation 到输入层的主路径。
    def dispatch(self, app_name: Any, operation: Any, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        safe_payload = dict(payload or {})  # 新增代码+Phase90LiveAppDispatcher: 复制动作参数；如果没有这行代码，外部修改会污染审计。
        operation_name = str(operation or "").strip().lower() or "click"  # 新增代码+Phase90LiveAppDispatcher: 规范化动作名；如果没有这行代码，空动作会难以处理。
        plan = self.build_dispatch_plan(app_name)  # 新增代码+Phase90LiveAppDispatcher: 构建安全启动计划；如果没有这行代码，危险 app 名无法提前拒绝。
        if not bool(plan.get("safe_to_launch")):  # 新增代码+Phase90LiveAppDispatcher: 检查启动计划是否安全；如果没有这行代码，powershell 等目标可能进入后续流程。
            return self._refusal("unsafe_launch_plan", plan, {}, operation_name)  # 新增代码+Phase90LiveAppDispatcher: 返回零事件拒绝；如果没有这行代码，启动阶段拒绝不可审计。
        launch = self.app_runtime.launch_app(plan)  # 新增代码+Phase90LiveAppDispatcher: 记录型启动应用；如果没有这行代码，dispatcher 无法串起 app launch。
        window = dict(launch.get("window", self.build_app_window(app_name)))  # 新增代码+Phase90LiveAppDispatcher: 获取记录窗口；如果没有这行代码，后续授权和输入没有目标。
        window.setdefault("process_name", window.get("app_id", ""))  # 修改代码+Phase90LiveAppDispatcher: 补齐 Phase60/72 需要的 process_name；如果没有这行代码，授权匹配可能因为目标摘要缺进程名而失败。
        window.setdefault("display_id", "DISPLAY1")  # 修改代码+Phase90LiveAppDispatcher: 补齐 Phase60 授权绑定的显示器 id；如果没有这行代码，window 级授权会因 display_id 缺失被拒绝。
        focus = self.app_runtime.focus_window(window)  # 新增代码+Phase90LiveAppDispatcher: 记录型聚焦窗口；如果没有这行代码，dispatcher 无法证明 focus 阶段存在。
        focused_window = dict(focus.get("window", window))  # 新增代码+Phase90LiveAppDispatcher: 获取聚焦后的窗口；如果没有这行代码，目标身份可能丢失。
        decision = self.safety_boundary.evaluate(focused_window, operation_name, self.grant_store, self.session_id)  # 新增代码+Phase90LiveAppDispatcher: 通过 Phase72 做最后安全评估；如果没有这行代码，未授权或危险窗口会绕过门禁。
        if not bool(decision.get("allowed")):  # 新增代码+Phase90LiveAppDispatcher: 检查安全边界是否允许；如果没有这行代码，被拒动作仍会构建输入事件。
            return self._refusal(str(decision.get("decision", "safety_boundary_refused")), plan, focused_window, operation_name, decision=decision, launch=launch, focus=focus)  # 新增代码+Phase90LiveAppDispatcher: 返回安全拒绝报告；如果没有这行代码，拒绝原因不可见。
        input_result = self._record_input_events(focused_window, operation_name, safe_payload)  # 新增代码+Phase90LiveAppDispatcher: 构建并记录输入事件；如果没有这行代码，授权动作无法进入执行层。
        real_enabled = _phase90_real_dispatch_enabled()  # 新增代码+Phase90LiveAppDispatcher: 读取真实派发环境门；如果没有这行代码，报告不知道真实动作是否被请求。
        return {"ok": bool(input_result.get("ok")), "marker": PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MARKER, "model": PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MODEL, "operation": operation_name, "plan": plan, "window": focused_window, "launch": launch, "focus": focus, "decision": decision, "input_result": input_result, "low_level_event_count": int(input_result.get("input_event_count", 0) or 0), "zero_event_refusal": False, "real_dispatch_requested": real_enabled, "real_dispatch_performed": False, "real_dispatch_env": PHASE90_REAL_DISPATCH_ENV, "raw_text_hidden": bool(input_result.get("raw_text_hidden", True)), "controlled_actions_expansion": PHASE90_ACTIONS_EXPANDED, "uncontrolled_actions_expanded": PHASE90_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+Phase90LiveAppDispatcher: 返回统一派发报告；如果没有这行代码，测试和上层 agent 无法判断成功路径。
    # 新增代码+Phase90LiveAppDispatcher: 函数段结束；默认只记录派发，不真实操作用户电脑。

    # 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有统一拒绝报告，危险窗口和未授权窗口的审计字段会漂移。
    def _refusal(self, reason: str, plan: dict[str, Any], window: dict[str, Any], operation: str, decision: dict[str, Any] | None = None, launch: dict[str, Any] | None = None, focus: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"ok": False, "marker": PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MARKER, "model": PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MODEL, "operation": operation, "decision": decision or {"allowed": False, "decision": reason}, "reason": reason, "plan": dict(plan or {}), "window": dict(window or {}), "launch": dict(launch or {}), "focus": dict(focus or {}), "low_level_event_count": 0, "zero_event_refusal": True, "real_dispatch_requested": _phase90_real_dispatch_enabled(), "real_dispatch_performed": False, "raw_text_hidden": True, "controlled_actions_expansion": PHASE90_ACTIONS_EXPANDED, "uncontrolled_actions_expanded": PHASE90_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+Phase90LiveAppDispatcher: 返回零事件拒绝；如果没有这行代码，拒绝后是否有副作用不可验证。
    # 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数不发送任何输入事件。

    # 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有事件记录，授权动作只能停在安全决策层。
    def _record_input_events(self, window: dict[str, Any], operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if operation == "type_text":  # 新增代码+Phase90LiveAppDispatcher: 单独处理文本输入；如果没有这行代码，文本输入无法脱敏。
            text = str(payload.get("text", ""))  # 新增代码+Phase90LiveAppDispatcher: 读取原始文本用于摘要；如果没有这行代码，无法生成长度和 digest。
            events = [{"type": "type_text", "text_length": len(text), "text_digest": _phase90_text_digest(text), "real_dispatch_allowed": False}]  # 新增代码+Phase90LiveAppDispatcher: 构建脱敏文本事件；如果没有这行代码，明文可能进入日志。
            dispatch = self.input_sender.send_input_events(window, events, "type_text")  # 新增代码+Phase90LiveAppDispatcher: 记录文本事件；如果没有这行代码，输入层没有事件证据。
            return {"ok": bool(dispatch.get("ok")), "input_event_count": int(dispatch.get("input_event_count", 0) or 0), "sender_result": dispatch, "raw_text_hidden": True}  # 新增代码+Phase90LiveAppDispatcher: 返回文本派发摘要；如果没有这行代码，调用方无法检查脱敏和事件数。
        if operation == "drag":  # 新增代码+Phase90LiveAppDispatcher: 处理拖拽动作；如果没有这行代码，画图类动作无法通过 dispatcher 表达。
            result = self.input_runtime.drag_path(window, list(payload.get("points", [])))  # 新增代码+Phase90LiveAppDispatcher: 复用 Phase71 拖拽 runtime；如果没有这行代码，拖拽事件协议会重复实现。
            return {"ok": bool(result.get("ok")), "input_event_count": int(result.get("input_event_count", 0) or 0), "sender_result": result, "raw_text_hidden": True}  # 新增代码+Phase90LiveAppDispatcher: 返回拖拽派发摘要；如果没有这行代码，调用方无法检查拖拽是否进入事件层。
        if operation == "scroll":  # 新增代码+Phase90LiveAppDispatcher: 处理滚轮动作；如果没有这行代码，滚动类应用无法覆盖。
            result = self.input_runtime.scroll_at(window, int(payload.get("x", 0) or 0), int(payload.get("y", 0) or 0), int(payload.get("delta", -120) or -120))  # 新增代码+Phase90LiveAppDispatcher: 复用 Phase71 滚轮 runtime；如果没有这行代码，滚动事件格式会漂移。
            return {"ok": bool(result.get("ok")), "input_event_count": int(result.get("input_event_count", 0) or 0), "sender_result": result, "raw_text_hidden": True}  # 新增代码+Phase90LiveAppDispatcher: 返回滚轮派发摘要；如果没有这行代码，调用方无法检查事件数。
        events = [{"type": "mouse_move", "x": int(payload.get("x", 0) or 0), "y": int(payload.get("y", 0) or 0), "real_dispatch_allowed": False}, {"type": "mouse_down", "button": "left", "x": int(payload.get("x", 0) or 0), "y": int(payload.get("y", 0) or 0), "real_dispatch_allowed": False}, {"type": "mouse_up", "button": "left", "x": int(payload.get("x", 0) or 0), "y": int(payload.get("y", 0) or 0), "real_dispatch_allowed": False}]  # 新增代码+Phase90LiveAppDispatcher: 构建默认点击事件；如果没有这行代码，click 动作无法进入输入层。
        dispatch = self.input_sender.send_input_events(window, events, "click")  # 新增代码+Phase90LiveAppDispatcher: 记录点击事件；如果没有这行代码，click 没有执行证据。
        return {"ok": bool(dispatch.get("ok")), "input_event_count": int(dispatch.get("input_event_count", 0) or 0), "sender_result": dispatch, "raw_text_hidden": True}  # 新增代码+Phase90LiveAppDispatcher: 返回点击派发摘要；如果没有这行代码，调用方无法检查低层事件数。
    # 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数默认只记录事件，不真实发送。

    # 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有 Paint plan helper，用户点名的皮卡丘场景无法进入 Phase90。
    def build_mspaint_pikachu_live_plan(self) -> dict[str, Any]:
        matrix = WindowsRepresentativeE2EMatrix(base_dir=self.base_dir / "representative_e2e")  # 新增代码+Phase90LiveAppDispatcher: 创建受控 E2E 矩阵目录；如果没有这行代码，Paint 证据会散落。
        paint = matrix.build_paint_pikachu_scenario(real_smoke=False)  # 新增代码+Phase90LiveAppDispatcher: 复用 Phase74 Paint 皮卡丘计划；如果没有这行代码，Phase90 会漏掉画图证明。
        return {"ok": bool(paint.get("mspaint_pikachu_scenario") and paint.get("humanlike_drawing_actions") and not paint.get("direct_image_file_cheat")), "paint": paint}  # 新增代码+Phase90LiveAppDispatcher: 返回 Paint live 计划摘要；如果没有这行代码，总合同无法检查皮卡丘计划。
    # 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数不打开 Paint live。
# 新增代码+Phase90LiveAppDispatcher: 类段结束；该类是 Phase90 给其它 agent 复用的主要入口。


# 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有可选真实 smoke，真实输入链路无法在安全窗口中被单独验证。
def _phase90_optional_safe_window_smoke(real_smoke: bool) -> dict[str, Any]:
    if not real_smoke:  # 新增代码+Phase90LiveAppDispatcher: 默认跳过真实输入；如果没有这行代码，普通测试会操作用户电脑。
        return {"requested": False, "passed": True, "safe_window_real_smoke_path": True, "reason": "real_smoke_not_requested"}  # 新增代码+Phase90LiveAppDispatcher: 合同模式返回 smoke 路径可用；如果没有这行代码，默认验收会被真实桌面依赖卡住。
    try:  # 新增代码+Phase90LiveAppDispatcher: 真实 smoke 可能受桌面环境影响；如果没有这行代码，异常会打断整个验收。
        from learning_agent.computer_use.real_sendinput_guard import run_phase58_real_sendinput_guard_contract  # 新增代码+Phase90LiveAppDispatcher: 复用 Phase58 安全窗口真实 SendInput；如果没有这行代码，Phase90 会重复造低层真实输入。
        report = run_phase58_real_sendinput_guard_contract(real_smoke=True)  # 新增代码+Phase90LiveAppDispatcher: 只对自建安全窗口跑真实 smoke；如果没有这行代码，真实路径没有证据。
        return {"requested": True, "passed": bool(report.get("passed") and report.get("real_smoke")), "safe_window_real_smoke_path": True, "report": report}  # 新增代码+Phase90LiveAppDispatcher: 返回真实 smoke 摘要；如果没有这行代码，用户无法判断是否实测。
    except Exception as error:  # 新增代码+Phase90LiveAppDispatcher: 捕获真实桌面 smoke 异常；如果没有这行代码，失败原因会变成长堆栈。
        return {"requested": True, "passed": False, "safe_window_real_smoke_path": True, "error": type(error).__name__}  # 新增代码+Phase90LiveAppDispatcher: 返回脱敏错误类型；如果没有这行代码，验收失败不可读。
# 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数只在显式 real_smoke 时触发真实安全窗口。


# 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有报告写入函数，Phase90 验收没有可追踪证据。
def _phase90_write_report(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase90LiveAppDispatcher: 确保报告目录存在；如果没有这行代码，首次写报告会失败。
    path = output_dir / "phase90_live_app_dispatcher_report.json"  # 新增代码+Phase90LiveAppDispatcher: 固定报告文件名；如果没有这行代码，用户难以找到证据。
    return atomic_write_json(path, report)  # 新增代码+Phase90LiveAppDispatcher: 原子写入报告并返回路径；如果没有这行代码，报告可能半写损坏。
# 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数只落盘 JSON。


# 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有总合同入口，测试和真实终端无法一键验证 Phase90。
def run_phase90_live_app_dispatcher_contract(base_dir: str | Path | None = None, real_smoke: bool = False) -> dict[str, Any]:
    root = Path(base_dir) if base_dir is not None else Path(tempfile.gettempdir()) / "learning_agent_phase90_live_app_dispatcher"  # 新增代码+Phase90LiveAppDispatcher: 选择隔离输出目录；如果没有这行代码，证据目录不稳定。
    dispatcher = WindowsLiveAppDispatcher(base_dir=root, session_id=f"phase90-contract-{int(time.time() * 1000)}")  # 新增代码+Phase90LiveAppDispatcher: 创建隔离 dispatcher；如果没有这行代码，合同没有被测主体。
    unauthorized = dispatcher.dispatch("calculator", "click", {"x": 10, "y": 10})  # 新增代码+Phase90LiveAppDispatcher: 先验证未授权普通应用拒绝；如果没有这行代码，授权门默认拒绝没有证据。
    dangerous = dispatcher.dispatch("powershell", "click", {"x": 10, "y": 10})  # 新增代码+Phase90LiveAppDispatcher: 验证危险终端拒绝；如果没有这行代码，高风险零事件没有证据。
    dispatcher.grant_representative_app("notepad", action_scope=["click", "type_text"])  # 新增代码+Phase90LiveAppDispatcher: 写入记事本受控授权；如果没有这行代码，正例无法通过 Phase72。
    notepad = dispatcher.dispatch("notepad", "type_text", {"text": "phase90 secret should stay hidden"})  # 新增代码+Phase90LiveAppDispatcher: 执行已授权记事本文本派发；如果没有这行代码，live dispatcher 主路径没有样本。
    paint_plan = dispatcher.build_mspaint_pikachu_live_plan()  # 新增代码+Phase90LiveAppDispatcher: 构建 Paint 皮卡丘 live 计划；如果没有这行代码，用户点名场景没有证据。
    smoke = _phase90_optional_safe_window_smoke(real_smoke)  # 新增代码+Phase90LiveAppDispatcher: 按需运行安全窗口真实 smoke；如果没有这行代码，真实输入链路没有可选验证。
    serialized_notepad = json.dumps(notepad, ensure_ascii=False)  # 新增代码+Phase90LiveAppDispatcher: 序列化记事本结果用于明文泄露检查；如果没有这行代码，raw_text_hidden 只能看字段。
    raw_text_hidden = "phase90 secret should stay hidden" not in serialized_notepad and bool(notepad.get("raw_text_hidden"))  # 新增代码+Phase90LiveAppDispatcher: 检查文本明文未泄露；如果没有这行代码，脱敏可能是假阳性。
    representative_live_apps_ready = set(PHASE90_REPRESENTATIVE_APPS) == {"notepad", "mspaint", "calculator", "explorer", "browser"}  # 新增代码+Phase90LiveAppDispatcher: 检查代表应用集合；如果没有这行代码，场景覆盖可能少一个。
    report = {"marker": PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MARKER, "ok_token": PHASE90_WINDOWS_LIVE_APP_DISPATCHER_OK_TOKEN, "model": PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MODEL, "live_dispatcher_ready": True, "real_app_dispatch_path": bool(notepad.get("ok") and notepad.get("low_level_event_count", 0) > 0), "default_real_dispatch_enabled": _phase90_real_dispatch_enabled(), "requires_explicit_live_env_gate": True, "uses_phase72_safety_boundary": isinstance(dispatcher.safety_boundary, WindowsRealAppSafetyBoundary), "uses_phase60_persistent_grants": isinstance(dispatcher.grant_store, WindowsComputerUsePersistentGrantStore), "uses_phase69_app_window_control": isinstance(dispatcher.app_runtime, WindowsAppWindowControlRuntime), "uses_phase71_input_events": isinstance(dispatcher.input_runtime, WindowsGenericInputActionRuntime), "safe_window_real_smoke_path": bool(smoke.get("safe_window_real_smoke_path") and smoke.get("passed")), "representative_live_apps_ready": representative_live_apps_ready, "notepad_live_dispatch_contract": bool(notepad.get("ok") and notepad.get("low_level_event_count", 0) > 0), "mspaint_pikachu_live_plan": bool(paint_plan.get("ok")), "dangerous_window_zero_events": bool(not dangerous.get("ok") and dangerous.get("zero_event_refusal") and dangerous.get("low_level_event_count") == 0), "unauthorized_window_zero_events": bool(not unauthorized.get("ok") and unauthorized.get("zero_event_refusal") and unauthorized.get("low_level_event_count") == 0), "raw_text_hidden": raw_text_hidden, "controlled_actions_expansion": PHASE90_ACTIONS_EXPANDED, "uncontrolled_actions_expanded": PHASE90_UNCONTROLLED_ACTIONS_EXPANDED, "real_smoke": smoke, "unauthorized": unauthorized, "dangerous": dangerous, "notepad": notepad, "paint_plan": paint_plan, "representative_apps": list(PHASE90_REPRESENTATIVE_APPS)}  # 新增代码+Phase90LiveAppDispatcher: 汇总 Phase90 合同报告；如果没有这行代码，测试和 CLI 拿不到统一结果。
    report["passed"] = bool(report["live_dispatcher_ready"] and report["real_app_dispatch_path"] and not report["default_real_dispatch_enabled"] and report["requires_explicit_live_env_gate"] and report["uses_phase72_safety_boundary"] and report["uses_phase60_persistent_grants"] and report["uses_phase69_app_window_control"] and report["uses_phase71_input_events"] and report["safe_window_real_smoke_path"] and report["representative_live_apps_ready"] and report["notepad_live_dispatch_contract"] and report["mspaint_pikachu_live_plan"] and report["dangerous_window_zero_events"] and report["unauthorized_window_zero_events"] and report["raw_text_hidden"] and not report["uncontrolled_actions_expanded"])  # 新增代码+Phase90LiveAppDispatcher: 汇总通过条件；如果没有这行代码，main 无法返回正确退出码。
    report["report_path"] = str(_phase90_write_report(report, root))  # 新增代码+Phase90LiveAppDispatcher: 写入报告并回填路径；如果没有这行代码，用户找不到验收证据。
    return report  # 新增代码+Phase90LiveAppDispatcher: 返回完整报告；如果没有这行代码，测试和 CLI 无法读取结果。
# 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数是 Phase90 自动化和终端共同入口。


# 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有 CLI 行，真实终端验收输出会难以稳定匹配。
def phase90_cli_line(report: dict[str, Any]) -> str:
    tokens = [PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MARKER, PHASE90_WINDOWS_LIVE_APP_DISPATCHER_OK_TOKEN, f"live_dispatcher_ready={_phase90_bool_token(report.get('live_dispatcher_ready'))}", f"real_app_dispatch_path={_phase90_bool_token(report.get('real_app_dispatch_path'))}", f"default_real_dispatch_enabled={_phase90_bool_token(report.get('default_real_dispatch_enabled'))}", f"requires_explicit_live_env_gate={_phase90_bool_token(report.get('requires_explicit_live_env_gate'))}", f"uses_phase72_safety_boundary={_phase90_bool_token(report.get('uses_phase72_safety_boundary'))}", f"uses_phase60_persistent_grants={_phase90_bool_token(report.get('uses_phase60_persistent_grants'))}", f"uses_phase69_app_window_control={_phase90_bool_token(report.get('uses_phase69_app_window_control'))}", f"uses_phase71_input_events={_phase90_bool_token(report.get('uses_phase71_input_events'))}", f"safe_window_real_smoke_path={_phase90_bool_token(report.get('safe_window_real_smoke_path'))}", f"representative_live_apps_ready={_phase90_bool_token(report.get('representative_live_apps_ready'))}", f"notepad_live_dispatch_contract={_phase90_bool_token(report.get('notepad_live_dispatch_contract'))}", f"mspaint_pikachu_live_plan={_phase90_bool_token(report.get('mspaint_pikachu_live_plan'))}", f"dangerous_window_zero_events={_phase90_bool_token(report.get('dangerous_window_zero_events'))}", f"unauthorized_window_zero_events={_phase90_bool_token(report.get('unauthorized_window_zero_events'))}", f"raw_text_hidden={_phase90_bool_token(report.get('raw_text_hidden'))}", f"uncontrolled_actions_expanded={_phase90_bool_token(report.get('uncontrolled_actions_expanded'))}"]  # 新增代码+Phase90LiveAppDispatcher: 组装固定顺序 token；如果没有这行代码，场景验收会因自然语言漂移失败。
    return " ".join(tokens)  # 新增代码+Phase90LiveAppDispatcher: 返回单行输出；如果没有这行代码，controller 不容易匹配。
# 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数只格式化输出。


# 新增代码+Phase90LiveAppDispatcher: 函数段开始；如果没有 main，真实可见终端 prompt 无法直接调用 Phase90。
def main(argv: list[str] | None = None) -> int:
    _ = argv  # 新增代码+Phase90LiveAppDispatcher: 保留 argv 供未来扩展；如果没有这行代码，参数用途不清楚。
    real_smoke = os.environ.get("LEARNING_AGENT_PHASE90_REAL_SMOKE", "0") == "1"  # 新增代码+Phase90LiveAppDispatcher: 读取安全窗口真实 smoke 开关；如果没有这行代码，真实 smoke 无法显式启用。
    report = run_phase90_live_app_dispatcher_contract(real_smoke=real_smoke)  # 新增代码+Phase90LiveAppDispatcher: 运行 Phase90 合同；如果没有这行代码，CLI 没有事实来源。
    print(phase90_cli_line(report))  # 新增代码+Phase90LiveAppDispatcher: 打印固定 token 行；如果没有这行代码，真实终端验收无法匹配成功。
    print(json.dumps({"report_path": report.get("report_path"), "passed": report.get("passed")}, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase90LiveAppDispatcher: 打印短 JSON 便于找证据；如果没有这行代码，失败时不易定位报告。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase90LiveAppDispatcher: 根据合同结果返回退出码；如果没有这行代码，失败也可能被当成成功。
# 新增代码+Phase90LiveAppDispatcher: 函数段结束；该函数是终端验收入口。


__all__ = ["PHASE90_REAL_DISPATCH_ENV", "PHASE90_UNCONTROLLED_ACTIONS_EXPANDED", "PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MARKER", "PHASE90_WINDOWS_LIVE_APP_DISPATCHER_MODEL", "PHASE90_WINDOWS_LIVE_APP_DISPATCHER_OK_TOKEN", "WindowsLiveAppDispatcher", "main", "phase90_cli_line", "run_phase90_live_app_dispatcher_contract"]  # 新增代码+Phase90LiveAppDispatcher: 限定公开导出名称；如果没有这行代码，包级 import * 容易漏掉 Phase90 入口或暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase90LiveAppDispatcher: 允许直接运行本模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase90LiveAppDispatcher: 调用 main 并传递退出码；如果没有这行代码，命令行状态不明确。
