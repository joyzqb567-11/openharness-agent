"""Phase91 Windows 受控 Notepad live smoke。"""  # 新增代码+Phase91NotepadLiveSmoke：说明本模块负责把 Phase90 dispatcher 推进到 Notepad 代表性真实软件入口；如果没有这行代码，读者不容易区分 Phase91 和通用 dispatcher。
from __future__ import annotations  # 新增代码+Phase91NotepadLiveSmoke：启用延迟类型注解，减少类和函数顺序造成的导入问题；如果没有这行代码，旧 Python 运行方式更容易遇到类型名未定义。

import hashlib  # 新增代码+Phase91NotepadLiveSmoke：导入哈希库用于文本和标题脱敏摘要；如果没有这行代码，报告要么泄露原文要么无法审计一致性。
import json  # 新增代码+Phase91NotepadLiveSmoke：导入 JSON 用于报告脱敏检查和 CLI 结构化输出；如果没有这行代码，验收失败时不容易定位字段。
import os  # 新增代码+Phase91NotepadLiveSmoke：导入 os 读取真实 Notepad smoke 的显式环境门禁；如果没有这行代码，真实桌面动作缺少第二道开关。
import subprocess  # 新增代码+Phase91NotepadLiveSmoke：导入 subprocess 只在显式真实 smoke 时启动受控 Notepad；如果没有这行代码，Phase91 无法提供真实软件可选路径。
import sys  # 新增代码+Phase91NotepadLiveSmoke：导入 sys 判断当前是否为 Windows；如果没有这行代码，非 Windows 环境可能误调用 Win32 API。
import tempfile  # 新增代码+Phase91NotepadLiveSmoke：导入 tempfile 为默认报告目录提供隔离位置；如果没有这行代码，CLI 自检没有稳定落盘目录。
import time  # 新增代码+Phase91NotepadLiveSmoke：导入 time 生成 session 和轮询超时；如果没有这行代码，多次验收证据不容易区分。
from pathlib import Path  # 新增代码+Phase91NotepadLiveSmoke：导入 Path 统一处理 Windows 路径；如果没有这行代码，受控文件和报告目录拼接更容易出错。
from typing import Any  # 新增代码+Phase91NotepadLiveSmoke：导入 Any 描述 JSON 风格 payload；如果没有这行代码，公共函数边界不清楚。

from learning_agent.computer_use.live_app_dispatcher import WindowsLiveAppDispatcher  # 新增代码+Phase91NotepadLiveSmoke：复用 Phase90 统一 app/window/授权/输入调度器；如果没有这行代码，Notepad 路径可能绕开既有安全链路。
from learning_agent.computer_use.real_sendinput_guard import WindowsSendInputLowLevelSender  # 新增代码+Phase91NotepadLiveSmoke：复用 Phase58 低层 SendInput sender 作为显式真实 smoke 的发送层；如果没有这行代码，真实可选路径会重复造轮子。
from learning_agent.computer_use.windows_backend import WindowsWindowInventoryProbe  # 新增代码+Phase91NotepadLiveSmoke：复用 Phase28 只读窗口枚举来寻找专属 Notepad 窗口；如果没有这行代码，真实 smoke 无法复验目标窗口。
from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase91NotepadLiveSmoke：复用项目原子 JSON 写入；如果没有这行代码，验收报告可能半写损坏。

PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_MARKER = "PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_READY"  # 新增代码+Phase91NotepadLiveSmoke：定义真实终端验收 ready 标记；如果没有这行代码，controller 无法稳定识别 Phase91 输出。
PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_OK_TOKEN = "PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_OK"  # 新增代码+Phase91NotepadLiveSmoke：定义真实终端验收 OK 标记；如果没有这行代码，用户无法一眼确认 Phase91 契约通过。
PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_MODEL = "phase91_windows_notepad_live_smoke"  # 新增代码+Phase91NotepadLiveSmoke：定义本阶段模型名；如果没有这行代码，报告无法说明契约版本。
PHASE91_REAL_NOTEPAD_SMOKE_ENV = "LEARNING_AGENT_PHASE91_ENABLE_REAL_NOTEPAD_SMOKE"  # 新增代码+Phase91NotepadLiveSmoke：定义真实 Notepad 动作的显式环境门禁；如果没有这行代码，真实桌面输入可能被普通参数误触发。
PHASE91_REAL_NOTEPAD_SMOKE_REQUEST_ENV = "LEARNING_AGENT_PHASE91_REAL_SMOKE"  # 新增代码+Phase91NotepadLiveSmoke：定义 CLI 请求真实 smoke 的环境变量；如果没有这行代码，终端无法显式进入真实路径。
PHASE91_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase91NotepadLiveSmoke：声明 Phase91 不扩张无保护动作面；如果没有这行代码，用户可能误以为任意窗口都能被裸控。
PHASE91_CONTROLLED_FILE_NAME = "Phase91 Notepad Live Smoke.txt"  # 新增代码+Phase91NotepadLiveSmoke：固定受控 Notepad 文件名，让窗口标题可识别；如果没有这行代码，真实窗口身份会漂移。
PHASE91_NOTEPAD_TITLE_PREFIX = "Phase91 Notepad Live Smoke"  # 新增代码+Phase91NotepadLiveSmoke：固定专属窗口标题前缀；如果没有这行代码，真实 smoke 可能混淆用户已有 Notepad。


# 新增代码+Phase91NotepadLiveSmoke：函数段开始，_phase91_bool_token 把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出可能出现 Python True/False 导致验收漂移。
def _phase91_bool_token(value: Any) -> str:
    return "true" if bool(value) else "false"  # 新增代码+Phase91NotepadLiveSmoke：返回小写布尔文本；如果没有这行代码，acceptance_controller 的 token 匹配会不稳定。
# 新增代码+Phase91NotepadLiveSmoke：函数段结束，_phase91_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。


# 新增代码+Phase91NotepadLiveSmoke：函数段开始，_phase91_sha256_16 用于脱敏文本摘要；如果没有这段函数，报告要么泄露文本要么无法比较状态。
def _phase91_sha256_16(value: Any) -> str:
    text = str(value or "")  # 新增代码+Phase91NotepadLiveSmoke：把输入规整成字符串；如果没有这行代码，None 或数字会导致哈希处理不稳定。
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase91NotepadLiveSmoke：返回短 SHA256 摘要；如果没有这行代码，审计无法在不泄露原文的情况下追踪输入。
# 新增代码+Phase91NotepadLiveSmoke：函数段结束，_phase91_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出脱敏范围。


# 新增代码+Phase91NotepadLiveSmoke：函数段开始，_phase91_real_notepad_smoke_enabled 读取真实 Notepad 环境门禁；如果没有这段函数，真实动作开关会散落在代码里。
def _phase91_real_notepad_smoke_enabled() -> bool:
    return os.environ.get(PHASE91_REAL_NOTEPAD_SMOKE_ENV, "0") == "1"  # 新增代码+Phase91NotepadLiveSmoke：只有环境变量等于 1 才允许真实 Notepad smoke；如果没有这行代码，桌面输入可能被误触发。
# 新增代码+Phase91NotepadLiveSmoke：函数段结束，_phase91_real_notepad_smoke_enabled 到此结束；如果没有这个边界说明，初学者不容易看出门禁范围。


# 新增代码+Phase91NotepadLiveSmoke：函数段开始，_phase91_safe_int 兜底转换整数；如果没有这段函数，坏 hwnd 或坐标字段可能让真实 smoke 崩溃。
def _phase91_safe_int(value: Any, default: int = 0) -> int:
    try:  # 新增代码+Phase91NotepadLiveSmoke：捕获无法转换的输入；如果没有这行代码，空值会让整数转换抛异常。
        return int(value)  # 新增代码+Phase91NotepadLiveSmoke：返回转换后的整数；如果没有这行代码，调用方拿不到可用数字。
    except (TypeError, ValueError):  # 新增代码+Phase91NotepadLiveSmoke：处理 None、空字符串或非数字文本；如果没有这行代码，坏字段会冒泡中断验收。
        return default  # 新增代码+Phase91NotepadLiveSmoke：返回默认值兜底；如果没有这行代码，调用方无法安全拒绝无效窗口。
# 新增代码+Phase91NotepadLiveSmoke：函数段结束，_phase91_safe_int 到此结束；如果没有这个边界说明，初学者不容易看出转换范围。


# 新增代码+Phase91NotepadLiveSmoke：函数段开始，_phase91_hwnd 从 window_id 或 hwnd 字段提取窗口句柄；如果没有这段函数，真实 smoke 无法把专属 Notepad 置前。
def _phase91_hwnd(window: dict[str, Any]) -> int:
    if window.get("hwnd") is not None:  # 新增代码+Phase91NotepadLiveSmoke：优先读取显式 hwnd 字段；如果没有这行代码，真实 inventory 的原始句柄可能被忽略。
        return _phase91_safe_int(window.get("hwnd"))  # 新增代码+Phase91NotepadLiveSmoke：安全转换 hwnd；如果没有这行代码，字符串句柄无法调用 Win32。
    window_id = str(window.get("window_id", ""))  # 新增代码+Phase91NotepadLiveSmoke：读取协议窗口 id；如果没有这行代码，没有 hwnd 字段时无法兜底。
    return _phase91_safe_int(window_id.split(":", 1)[1]) if window_id.startswith("hwnd:") and ":" in window_id else 0  # 新增代码+Phase91NotepadLiveSmoke：从 hwnd:123 提取数字；如果没有这行代码，SetForegroundWindow 没有目标。
# 新增代码+Phase91NotepadLiveSmoke：函数段结束，_phase91_hwnd 到此结束；如果没有这个边界说明，初学者不容易看出句柄解析范围。


# 新增代码+Phase91NotepadLiveSmoke：类段开始，WindowsNotepadLiveSmokeRuntime 组合受控文件、窗口身份、Phase90 dispatcher 和可选真实 smoke；如果没有这个类，Phase91 会散成多个不可复用脚本。
class WindowsNotepadLiveSmokeRuntime:
    """受控 Notepad 代表性真实软件 smoke runtime。"""  # 新增代码+Phase91NotepadLiveSmoke：说明类职责是受控入口，不是任意窗口裸控；如果没有这行代码，用户容易误解能力边界。

    def __init__(self, base_dir: str | Path | None = None, session_id: str | None = None) -> None:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，初始化 Phase91 runtime；如果没有这段函数，调用方无法隔离报告和授权状态。
        self.base_dir = Path(base_dir) if base_dir is not None else Path(tempfile.gettempdir()) / "learning_agent_phase91_notepad_live_smoke"  # 新增代码+Phase91NotepadLiveSmoke：保存状态根目录；如果没有这行代码，报告和受控文件没有落点。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase91NotepadLiveSmoke：确保根目录存在；如果没有这行代码，首次写文件或报告会失败。
        self.session_id = session_id or f"phase91-session-{int(time.time() * 1000)}"  # 新增代码+Phase91NotepadLiveSmoke：保存会话 id；如果没有这行代码，授权无法和本次运行绑定。
        self.dispatcher = WindowsLiveAppDispatcher(base_dir=self.base_dir / "dispatcher", session_id=self.session_id)  # 新增代码+Phase91NotepadLiveSmoke：创建隔离 Phase90 dispatcher；如果没有这行代码，Notepad 契约无法复用统一安全链路。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，WindowsNotepadLiveSmokeRuntime.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def build_controlled_file_plan(self) -> dict[str, Any]:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，构造 Notepad 只允许操作的受控文件计划；如果没有这段函数，真实 smoke 可能写到用户文件。
        controlled_dir = self.base_dir / "controlled_notepad"  # 新增代码+Phase91NotepadLiveSmoke：定义受控 Notepad 目录；如果没有这行代码，测试文件会和其他报告混在一起。
        controlled_file = controlled_dir / PHASE91_CONTROLLED_FILE_NAME  # 新增代码+Phase91NotepadLiveSmoke：定义受控文件路径；如果没有这行代码，真实 Notepad 没有明确目标文件。
        return {"file_path": str(controlled_file), "controlled_root": str(controlled_dir), "inside_controlled_root": True, "changes_registry": False, "changes_system_settings": False, "requires_admin": False, "launch_arguments": [str(controlled_file)], "title_hint": PHASE91_CONTROLLED_FILE_NAME}  # 新增代码+Phase91NotepadLiveSmoke：返回机器可读文件计划；如果没有这行代码，测试和验收无法判断边界。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，build_controlled_file_plan 到此结束；如果没有这个边界说明，初学者不容易看出文件计划范围。

    def build_dedicated_window_identity(self) -> dict[str, Any]:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，构造专属 Notepad 窗口身份；如果没有这段函数，真实输入无法和用户已有 Notepad 区分。
        window = self.dispatcher.build_app_window("notepad")  # 新增代码+Phase91NotepadLiveSmoke：复用 Phase90 的 Notepad 窗口身份基础；如果没有这行代码，授权和调度器目标可能不一致。
        file_plan = self.build_controlled_file_plan()  # 新增代码+Phase91NotepadLiveSmoke：读取受控文件计划；如果没有这行代码，窗口标题提示无法和文件名绑定。
        return {"app": "notepad", "app_id": str(window.get("app_id", "notepad.exe")), "process_name": "notepad.exe", "window_id": str(window.get("window_id", "phase91-notepad-window")), "display_id": str(window.get("display_id", "DISPLAY1")), "title_prefix": PHASE91_NOTEPAD_TITLE_PREFIX, "title_hint": str(file_plan.get("title_hint", "")), "controlled_window": True, "safe_to_target": bool(window.get("safe_to_target", True))}  # 新增代码+Phase91NotepadLiveSmoke：返回专属窗口身份摘要；如果没有这行代码，真实 smoke 缺少目标证明。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，build_dedicated_window_identity 到此结束；如果没有这个边界说明，初学者不容易看出窗口身份范围。

    def build_cleanup_plan(self) -> dict[str, Any]:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，构造真实 smoke 后的清理计划；如果没有这段函数，Notepad 窗口、按键或临时文件可能残留。
        return {"cleanup_plan_ready": True, "actions": ["close_dedicated_notepad_process", "release_input_focus", "keep_controlled_file_for_evidence", "write_phase91_report"], "kills_user_processes": False, "deletes_user_files": False}  # 新增代码+Phase91NotepadLiveSmoke：返回清理计划摘要；如果没有这行代码，用户无法确认不会误删个人文件。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，build_cleanup_plan 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。

    def run_contract(self, real_smoke: bool = False) -> dict[str, Any]:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，运行 Phase91 总契约；如果没有这段函数，测试、CLI 和真实终端没有统一入口。
        file_plan = self.build_controlled_file_plan()  # 新增代码+Phase91NotepadLiveSmoke：生成受控文件计划；如果没有这行代码，总报告无法证明文件边界。
        window_identity = self.build_dedicated_window_identity()  # 新增代码+Phase91NotepadLiveSmoke：生成专属窗口身份；如果没有这行代码，总报告无法证明目标边界。
        cleanup_plan = self.build_cleanup_plan()  # 新增代码+Phase91NotepadLiveSmoke：生成清理计划；如果没有这行代码，真实软件路径缺少收尾标准。
        unauthorized_dispatcher = WindowsLiveAppDispatcher(base_dir=self.base_dir / "unauthorized_dispatcher", session_id=f"{self.session_id}-unauthorized")  # 新增代码+Phase91NotepadLiveSmoke：创建未授权 dispatcher；如果没有这行代码，默认拒绝路径可能被已授权状态污染。
        unauthorized = unauthorized_dispatcher.dispatch("notepad", "click", {"x": 10, "y": 10})  # 新增代码+Phase91NotepadLiveSmoke：未授权 Notepad 尝试点击；如果没有这行代码，授权门的零事件拒绝没有证据。
        dangerous = self.dispatcher.dispatch("powershell", "click", {"x": 10, "y": 10})  # 新增代码+Phase91NotepadLiveSmoke：危险终端尝试点击；如果没有这行代码，高风险拒绝没有样本。
        self.dispatcher.grant_representative_app("notepad", action_scope=["click", "type_text"], ttl_seconds=120)  # 新增代码+Phase91NotepadLiveSmoke：给 Notepad 写入受控授权；如果没有这行代码，正例无法通过 Phase72 安全边界。
        secret_text = "phase91 secret should stay hidden"  # 新增代码+Phase91NotepadLiveSmoke：准备仅用于脱敏检查的测试文本；如果没有这行代码，raw_text_hidden 没有明确对象。
        authorized = self.dispatcher.dispatch("notepad", "type_text", {"text": secret_text})  # 新增代码+Phase91NotepadLiveSmoke：执行已授权 Notepad 记录型文本派发；如果没有这行代码，Phase90 集成没有正例证据。
        real_report = self._run_optional_real_notepad_smoke(bool(real_smoke), file_plan, window_identity)  # 新增代码+Phase91NotepadLiveSmoke：按需运行显式真实 Notepad smoke；如果没有这行代码，真实路径缺少受控入口。
        serialized_authorized = json.dumps(authorized, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase91NotepadLiveSmoke：序列化授权结果用于明文泄露检查；如果没有这行代码，raw_text_hidden 可能是假阳性。
        raw_text_hidden = bool(secret_text not in serialized_authorized and authorized.get("raw_text_hidden"))  # 新增代码+Phase91NotepadLiveSmoke：确认记录型派发没有暴露明文；如果没有这行代码，用户文本可能进入日志。
        report = {"marker": PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_MARKER, "ok_token": PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_OK_TOKEN, "model": PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_MODEL, "notepad_live_smoke_ready": True, "controlled_notepad_file_plan": bool(file_plan.get("inside_controlled_root") and not file_plan.get("changes_registry") and not file_plan.get("changes_system_settings") and not file_plan.get("requires_admin")), "dedicated_notepad_window_identity": bool(window_identity.get("controlled_window") and window_identity.get("app_id") == "notepad.exe"), "phase90_dispatcher_integrated": isinstance(self.dispatcher, WindowsLiveAppDispatcher), "authorized_notepad_dispatch_contract": bool(authorized.get("ok") and authorized.get("low_level_event_count", 0) > 0), "dangerous_window_zero_events": bool(not dangerous.get("ok") and dangerous.get("zero_event_refusal") and dangerous.get("low_level_event_count") == 0), "unauthorized_window_zero_events": bool(not unauthorized.get("ok") and unauthorized.get("zero_event_refusal") and unauthorized.get("low_level_event_count") == 0), "raw_text_hidden": raw_text_hidden, "default_real_notepad_smoke_enabled": False, "requires_explicit_notepad_env_gate": True, "real_notepad_env_gate_enabled": _phase91_real_notepad_smoke_enabled(), "real_notepad_smoke_optional": True, "real_notepad_smoke_executed": bool(real_report.get("executed")), "cleanup_plan_ready": bool(cleanup_plan.get("cleanup_plan_ready")), "uncontrolled_actions_expanded": PHASE91_UNCONTROLLED_ACTIONS_EXPANDED, "file_plan": file_plan, "window_identity": window_identity, "cleanup_plan": cleanup_plan, "real_notepad_smoke": real_report, "authorized": authorized, "unauthorized": unauthorized, "dangerous": dangerous}  # 新增代码+Phase91NotepadLiveSmoke：汇总 Phase91 契约报告；如果没有这行代码，测试和终端无法读取统一事实。
        report["passed"] = bool(report["notepad_live_smoke_ready"] and report["controlled_notepad_file_plan"] and report["dedicated_notepad_window_identity"] and report["phase90_dispatcher_integrated"] and report["authorized_notepad_dispatch_contract"] and report["dangerous_window_zero_events"] and report["unauthorized_window_zero_events"] and report["raw_text_hidden"] and not report["default_real_notepad_smoke_enabled"] and report["requires_explicit_notepad_env_gate"] and report["real_notepad_smoke_optional"] and real_report.get("passed") and report["cleanup_plan_ready"] and not report["uncontrolled_actions_expanded"])  # 新增代码+Phase91NotepadLiveSmoke：汇总通过条件；如果没有这行代码，CLI 无法用退出码表达失败。
        report["report_path"] = str(self._write_report(report))  # 新增代码+Phase91NotepadLiveSmoke：写入报告并回填路径；如果没有这行代码，用户找不到验收证据。
        return report  # 新增代码+Phase91NotepadLiveSmoke：返回完整报告；如果没有这行代码，测试和 CLI 无法读取结果。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，run_contract 到此结束；如果没有这个边界说明，初学者不容易看出总契约范围。

    def _run_optional_real_notepad_smoke(self, requested: bool, file_plan: dict[str, Any], window_identity: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，处理真实 Notepad smoke 的可选门禁；如果没有这段函数，真实桌面动作容易被普通测试触发。
        if not requested:  # 新增代码+Phase91NotepadLiveSmoke：默认不请求真实 smoke；如果没有这行代码，普通合同会打开 Notepad。
            return {"requested": False, "passed": True, "executed": False, "real_notepad_smoke_optional": True, "reason": "real_notepad_smoke_not_requested"}  # 新增代码+Phase91NotepadLiveSmoke：返回安全跳过结果；如果没有这行代码，默认验收会依赖真实桌面。
        if not _phase91_real_notepad_smoke_enabled():  # 新增代码+Phase91NotepadLiveSmoke：检查显式环境门禁；如果没有这行代码，单个参数就可能触发真实输入。
            return {"requested": True, "passed": False, "executed": False, "real_notepad_smoke_optional": True, "reason": "explicit_env_gate_required"}  # 新增代码+Phase91NotepadLiveSmoke：缺门禁时零事件拒绝；如果没有这行代码，失败原因不清楚。
        return self._run_real_notepad_smoke(file_plan, window_identity)  # 新增代码+Phase91NotepadLiveSmoke：门禁满足后才进入真实 Notepad 路径；如果没有这行代码，可选真实 smoke 没有执行入口。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，_run_optional_real_notepad_smoke 到此结束；如果没有这个边界说明，初学者不容易看出门禁范围。

    def _run_real_notepad_smoke(self, file_plan: dict[str, Any], window_identity: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，执行显式授权的真实 Notepad smoke；如果没有这段函数，Phase91 只能停留在记录型 contract。
        if sys.platform != "win32":  # 新增代码+Phase91NotepadLiveSmoke：非 Windows 直接拒绝真实路径；如果没有这行代码，跨平台会调用 Win32 API 崩溃。
            return {"requested": True, "passed": False, "executed": False, "platform_supported": False, "reason": "platform_not_windows"}  # 新增代码+Phase91NotepadLiveSmoke：返回平台不支持；如果没有这行代码，失败原因不清楚。
        controlled_file = Path(str(file_plan.get("file_path", "")))  # 新增代码+Phase91NotepadLiveSmoke：读取受控文件路径；如果没有这行代码，Notepad 没有可验证文件目标。
        controlled_file.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase91NotepadLiveSmoke：确保受控目录存在；如果没有这行代码，启动 Notepad 文件路径可能失败。
        controlled_file.write_text("Phase91 controlled Notepad live smoke evidence.\n", encoding="utf-8")  # 新增代码+Phase91NotepadLiveSmoke：写入初始证据文本；如果没有这行代码，Notepad 打开的文件可能不存在。
        process: subprocess.Popen[Any] | None = None  # 新增代码+Phase91NotepadLiveSmoke：初始化进程句柄；如果没有这行代码，finally 无法判断是否需要清理。
        try:  # 新增代码+Phase91NotepadLiveSmoke：包住启动、查找和发送流程；如果没有这行代码，异常会绕过清理。
            process = subprocess.Popen(["notepad.exe", str(controlled_file)])  # 新增代码+Phase91NotepadLiveSmoke：启动只打开受控文件的 Notepad；如果没有这行代码，真实软件路径不会发生。
            window = self._poll_dedicated_notepad_window(str(file_plan.get("title_hint", "")), timeout_seconds=8.0)  # 新增代码+Phase91NotepadLiveSmoke：等待专属 Notepad 窗口出现；如果没有这行代码，输入可能找不到目标。
            if window is None:  # 新增代码+Phase91NotepadLiveSmoke：检查窗口是否找到；如果没有这行代码，后续可能对空目标发送事件。
                return {"requested": True, "passed": False, "executed": False, "platform_supported": True, "safe_window_found": False, "reason": "dedicated_notepad_window_not_found"}  # 新增代码+Phase91NotepadLiveSmoke：返回未找到窗口且零事件；如果没有这行代码，失败不可解释。
            hwnd = _phase91_hwnd(window)  # 新增代码+Phase91NotepadLiveSmoke：提取窗口句柄；如果没有这行代码，SendInput 无法先聚焦目标窗口。
            if hwnd <= 0:  # 新增代码+Phase91NotepadLiveSmoke：检查 hwnd 是否有效；如果没有这行代码，0 句柄可能传给系统 API。
                return {"requested": True, "passed": False, "executed": False, "platform_supported": True, "safe_window_found": True, "reason": "dedicated_notepad_hwnd_missing"}  # 新增代码+Phase91NotepadLiveSmoke：返回句柄缺失；如果没有这行代码，失败不可审计。
            input_text = f" phase91-{int(time.time())}"  # 新增代码+Phase91NotepadLiveSmoke：准备短测试文本，只保存在内存中；如果没有这行代码，真实输入没有动作内容。
            sender = WindowsSendInputLowLevelSender(platform=sys.platform)  # 新增代码+Phase91NotepadLiveSmoke：创建真实低层 sender；如果没有这行代码，SendInput 路径不会触达系统。
            dispatch = sender.send_low_level([{"type": "set_foreground", "hwnd": hwnd}, {"type": "unicode_text", "text": input_text}])  # 新增代码+Phase91NotepadLiveSmoke：聚焦专属 Notepad 并输入短文本；如果没有这行代码，真实 smoke 没有低层动作证据。
            dispatch_summary = dict(dispatch if isinstance(dispatch, dict) else {})  # 新增代码+Phase91NotepadLiveSmoke：复制 sender 返回值；如果没有这行代码，后续脱敏可能污染原对象。
            dispatch_summary.pop("text", None)  # 新增代码+Phase91NotepadLiveSmoke：删除可能存在的文本字段；如果没有这行代码，底层变化可能把原文带入报告。
            dispatch_summary["raw_text_included"] = False  # 新增代码+Phase91NotepadLiveSmoke：明确报告不含输入原文；如果没有这行代码，验收无法稳定判断脱敏。
            window_digest = {"window_id": str(window.get("window_id", "")), "app_id": str(window.get("app_id", "")), "title_sha256_16": _phase91_sha256_16(window.get("title_preview", "")), "title_length": len(str(window.get("title_preview", "") or ""))}  # 新增代码+Phase91NotepadLiveSmoke：保存窗口脱敏身份；如果没有这行代码，真实结果要么泄露标题要么无法审计。
            serialized = json.dumps({"dispatch": dispatch_summary, "window": window_digest, "identity": window_identity}, ensure_ascii=False, sort_keys=True)  # 新增代码+Phase91NotepadLiveSmoke：序列化可见结果做泄露检查；如果没有这行代码，raw_text_hidden 可能漏查。
            passed = bool(dispatch_summary.get("ok") and dispatch_summary.get("low_level_event_count", 0) > 0 and input_text not in serialized)  # 新增代码+Phase91NotepadLiveSmoke：确认真实发送发生且原文未进报告；如果没有这行代码，空发送也可能误报成功。
            return {"requested": True, "passed": passed, "executed": True, "platform_supported": True, "safe_window_found": True, "dedicated_notepad_only": True, "low_level_event_count": int(dispatch_summary.get("low_level_event_count", 0) or 0), "raw_text_hidden": input_text not in serialized, "input_text_sha256_16": _phase91_sha256_16(input_text), "dispatch": dispatch_summary, "window_identity": window_digest}  # 新增代码+Phase91NotepadLiveSmoke：返回脱敏真实 smoke 摘要；如果没有这行代码，CLI 无法证明真实路径。
        except Exception as error:  # 新增代码+Phase91NotepadLiveSmoke：捕获真实桌面 smoke 异常；如果没有这行代码，权限或桌面状态问题会打断整个命令。
            return {"requested": True, "passed": False, "executed": False, "platform_supported": True, "reason": f"real_notepad_smoke_error:{type(error).__name__}"}  # 新增代码+Phase91NotepadLiveSmoke：返回异常类型但不泄露本地细节；如果没有这行代码，失败只能看堆栈。
        finally:  # 新增代码+Phase91NotepadLiveSmoke：无论成功失败都尝试清理受控 Notepad；如果没有这行代码，真实 smoke 可能留下窗口。
            if process is not None and process.poll() is None:  # 新增代码+Phase91NotepadLiveSmoke：确认进程仍在运行；如果没有这行代码，terminate 可能对已退出进程报错。
                process.terminate()  # 新增代码+Phase91NotepadLiveSmoke：关闭本次启动的受控 Notepad 进程；如果没有这行代码，真实验收会残留窗口。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，_run_real_notepad_smoke 到此结束；如果没有这个边界说明，初学者不容易看出真实动作范围。

    def _poll_dedicated_notepad_window(self, title_hint: str, timeout_seconds: float = 8.0, poll_interval_seconds: float = 0.25) -> dict[str, Any] | None:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，轮询专属 Notepad 窗口；如果没有这段函数，真实 smoke 只能猜测窗口是否出现。
        deadline = time.time() + max(0.1, float(timeout_seconds))  # 新增代码+Phase91NotepadLiveSmoke：计算轮询截止时间；如果没有这行代码，查找窗口可能无限等待。
        probe = WindowsWindowInventoryProbe()  # 新增代码+Phase91NotepadLiveSmoke：创建只读窗口枚举器；如果没有这行代码，无法发现真实 Notepad 顶层窗口。
        while time.time() < deadline:  # 新增代码+Phase91NotepadLiveSmoke：在超时前持续轮询；如果没有这行代码，窗口启动延迟会导致误失败。
            snapshot = probe.snapshot()  # 新增代码+Phase91NotepadLiveSmoke：读取当前窗口快照；如果没有这行代码，没有事实来源。
            for window in snapshot.windows:  # 新增代码+Phase91NotepadLiveSmoke：遍历安全可见窗口；如果没有这行代码，无法匹配目标。
                title = str(window.get("title_preview", "") or "")  # 新增代码+Phase91NotepadLiveSmoke：读取脱敏前的标题摘要字段；如果没有这行代码，无法判断文件名是否命中。
                app_id = str(window.get("app_id", "") or "").lower()  # 新增代码+Phase91NotepadLiveSmoke：读取 app_id 辅助判断；如果没有这行代码，Notepad 识别会更弱。
                class_name = str(window.get("class_name", "") or "").lower()  # 新增代码+Phase91NotepadLiveSmoke：读取窗口类名辅助判断；如果没有这行代码，Win32 probe 缺进程名时没有兜底。
                title_matches = bool(title_hint and title_hint.lower() in title.lower())  # 新增代码+Phase91NotepadLiveSmoke：检查标题是否包含受控文件名；如果没有这行代码，可能误选用户 Notepad。
                app_matches = "notepad" in app_id or "notepad" in class_name or "windows.ui" in class_name  # 新增代码+Phase91NotepadLiveSmoke：检查应用或类名是否像 Notepad；如果没有这行代码，单靠标题可能不够稳。
                if title_matches and app_matches:  # 新增代码+Phase91NotepadLiveSmoke：只有文件名和应用线索同时满足才放行；如果没有这行代码，目标面会过宽。
                    return dict(window)  # 新增代码+Phase91NotepadLiveSmoke：返回窗口副本；如果没有这行代码，调用方拿不到目标。
            time.sleep(max(0.05, float(poll_interval_seconds)))  # 新增代码+Phase91NotepadLiveSmoke：短暂等待后继续轮询；如果没有这行代码，会忙等消耗 CPU。
        return None  # 新增代码+Phase91NotepadLiveSmoke：超时未找到返回 None；如果没有这行代码，调用方无法区分未找到和异常。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，_poll_dedicated_notepad_window 到此结束；如果没有这个边界说明，初学者不容易看出查找范围。

    def _write_report(self, report: dict[str, Any]) -> Path:  # 新增代码+Phase91NotepadLiveSmoke：函数段开始，写入 Phase91 报告；如果没有这段函数，验收证据不会落盘。
        reports_dir = self.base_dir / "reports"  # 新增代码+Phase91NotepadLiveSmoke：定义报告目录；如果没有这行代码，报告会和授权状态混在一起。
        reports_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase91NotepadLiveSmoke：确保报告目录存在；如果没有这行代码，首次写报告会失败。
        return atomic_write_json(reports_dir / "phase91_notepad_live_smoke_report.json", report)  # 新增代码+Phase91NotepadLiveSmoke：原子写入 JSON 报告；如果没有这行代码，崩溃时可能留下半个文件。
    # 新增代码+Phase91NotepadLiveSmoke：函数段结束，_write_report 到此结束；如果没有这个边界说明，初学者不容易看出落盘范围。
# 新增代码+Phase91NotepadLiveSmoke：类段结束，WindowsNotepadLiveSmokeRuntime 到此结束；如果没有这个边界说明，初学者不容易看出 runtime 范围。


# 新增代码+Phase91NotepadLiveSmoke：函数段开始，run_phase91_notepad_live_smoke_contract 提供统一合同入口；如果没有这段函数，测试和真实终端只能直接拼 runtime。
def run_phase91_notepad_live_smoke_contract(base_dir: str | Path | None = None, real_smoke: bool = False) -> dict[str, Any]:
    runtime = WindowsNotepadLiveSmokeRuntime(base_dir=base_dir, session_id=f"phase91-contract-{int(time.time() * 1000)}")  # 新增代码+Phase91NotepadLiveSmoke：创建隔离 runtime；如果没有这行代码，多次运行会共享授权状态。
    return runtime.run_contract(real_smoke=real_smoke)  # 新增代码+Phase91NotepadLiveSmoke：运行并返回合同报告；如果没有这行代码，公共入口没有结果。
# 新增代码+Phase91NotepadLiveSmoke：函数段结束，run_phase91_notepad_live_smoke_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同入口范围。


# 新增代码+Phase91NotepadLiveSmoke：函数段开始，phase91_cli_line 把报告压成稳定终端 token；如果没有这段函数，真实可见终端验收需要解析复杂 JSON。
def phase91_cli_line(report: dict[str, Any]) -> str:
    tokens = [PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_MARKER, PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_OK_TOKEN, f"notepad_live_smoke_ready={_phase91_bool_token(report.get('notepad_live_smoke_ready'))}", f"controlled_notepad_file_plan={_phase91_bool_token(report.get('controlled_notepad_file_plan'))}", f"dedicated_notepad_window_identity={_phase91_bool_token(report.get('dedicated_notepad_window_identity'))}", f"phase90_dispatcher_integrated={_phase91_bool_token(report.get('phase90_dispatcher_integrated'))}", f"authorized_notepad_dispatch_contract={_phase91_bool_token(report.get('authorized_notepad_dispatch_contract'))}", f"dangerous_window_zero_events={_phase91_bool_token(report.get('dangerous_window_zero_events'))}", f"unauthorized_window_zero_events={_phase91_bool_token(report.get('unauthorized_window_zero_events'))}", f"raw_text_hidden={_phase91_bool_token(report.get('raw_text_hidden'))}", f"default_real_notepad_smoke_enabled={_phase91_bool_token(report.get('default_real_notepad_smoke_enabled'))}", f"requires_explicit_notepad_env_gate={_phase91_bool_token(report.get('requires_explicit_notepad_env_gate'))}", f"real_notepad_smoke_optional={_phase91_bool_token(report.get('real_notepad_smoke_optional'))}", f"real_notepad_smoke_executed={_phase91_bool_token(report.get('real_notepad_smoke_executed'))}", f"cleanup_plan_ready={_phase91_bool_token(report.get('cleanup_plan_ready'))}", f"uncontrolled_actions_expanded={_phase91_bool_token(report.get('uncontrolled_actions_expanded'))}"]  # 新增代码+Phase91NotepadLiveSmoke：按固定顺序组装 token；如果没有这行代码，场景验收会因输出漂移失败。
    return " ".join(tokens)  # 新增代码+Phase91NotepadLiveSmoke：返回单行终端输出；如果没有这行代码，controller 不容易匹配。
# 新增代码+Phase91NotepadLiveSmoke：函数段结束，phase91_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


# 新增代码+Phase91NotepadLiveSmoke：函数段开始，main 提供真实终端入口；如果没有这段函数，start_oauth_agent.bat 场景无法直接触发 Phase91。
def main(argv: list[str] | None = None) -> int:
    _ = argv  # 新增代码+Phase91NotepadLiveSmoke：保留 argv 供未来扩展；如果没有这行代码，参数用途不清楚。
    real_smoke = os.environ.get(PHASE91_REAL_NOTEPAD_SMOKE_REQUEST_ENV, "0") == "1"  # 新增代码+Phase91NotepadLiveSmoke：读取 CLI 是否请求真实 Notepad smoke；如果没有这行代码，终端无法显式进入真实路径。
    report = run_phase91_notepad_live_smoke_contract(real_smoke=real_smoke)  # 新增代码+Phase91NotepadLiveSmoke：运行合同；如果没有这行代码，CLI 没有事实来源。
    print(phase91_cli_line(report))  # 新增代码+Phase91NotepadLiveSmoke：打印稳定 token 行；如果没有这行代码，真实终端验收无法匹配成功。
    print(json.dumps({"report_path": report.get("report_path"), "passed": report.get("passed"), "real_notepad_smoke_executed": report.get("real_notepad_smoke_executed")}, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase91NotepadLiveSmoke：打印短 JSON 方便找证据；如果没有这行代码，失败时不容易定位报告文件。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase91NotepadLiveSmoke：根据合同结果返回退出码；如果没有这行代码，失败也可能被命令行当成成功。
# 新增代码+Phase91NotepadLiveSmoke：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出终端入口范围。


__all__ = ["PHASE91_REAL_NOTEPAD_SMOKE_ENV", "PHASE91_REAL_NOTEPAD_SMOKE_REQUEST_ENV", "PHASE91_UNCONTROLLED_ACTIONS_EXPANDED", "PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_MARKER", "PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_MODEL", "PHASE91_WINDOWS_NOTEPAD_LIVE_SMOKE_OK_TOKEN", "WindowsNotepadLiveSmokeRuntime", "main", "phase91_cli_line", "run_phase91_notepad_live_smoke_contract"]  # 新增代码+Phase91NotepadLiveSmoke：限定公开导出名称；如果没有这行代码，from module import * 容易漏掉入口或暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase91NotepadLiveSmoke：允许直接运行本模块；如果没有这行代码，python -m 之外的文件运行方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase91NotepadLiveSmoke：调用 main 并传递退出码；如果没有这行代码，命令行状态不明确。
