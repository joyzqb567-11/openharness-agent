"""Windows 受控应用启动候选层。"""  # 新增代码+Phase103ControlledAppLaunch：说明本模块负责把 full 模式 launch_app 接到受控启动候选；如果没有这行代码，读者不清楚本文件不是任意命令执行器。
from __future__ import annotations  # 新增代码+Phase103ControlledAppLaunch：启用延迟类型解析；如果没有这行代码，类之间的类型注解更容易遇到导入顺序问题。

import json  # 新增代码+Phase103ControlledAppLaunch：导入 JSON 用于合同报告和 CLI 结构化输出；如果没有这行代码，验收结果无法稳定序列化。
import os  # 新增代码+Phase103ControlledAppLaunch：导入 os 读取显式真实启动环境门；如果没有这行代码，真实启动开关会变得不可审计。
import sys  # 新增代码+Phase103ControlledAppLaunch：导入 sys 判断当前平台；如果没有这行代码，非 Windows 环境可能误尝试 Windows 启动。
import time  # 新增代码+Phase103ControlledAppLaunch：导入 time 生成隔离合同目录；如果没有这行代码，多次验收报告可能互相覆盖。
from pathlib import Path  # 新增代码+Phase103ControlledAppLaunch：导入 Path 统一处理 Windows 路径；如果没有这行代码，报告落盘路径会更脆弱。
from typing import Any  # 新增代码+Phase103ControlledAppLaunch：导入 Any 描述 JSON 风格动态字典；如果没有这行代码，接口边界对初学者不清晰。

try:  # 新增代码+Phase103ControlledAppLaunch：优先按 learning_agent 包路径导入项目组件；如果没有这段代码，单元测试和真实终端入口不能共享同一实现。
    from learning_agent.computer_use.app_window_control import build_launch_plan  # 新增代码+Phase103ControlledAppLaunch：复用 Phase69 安全启动计划；如果没有这行代码，Phase103 可能直接信任用户命令。
    from learning_agent.computer_use.mode_session import ComputerUseModeSessionStore  # 新增代码+Phase103ControlledAppLaunch：复用 mode store 走真实 full 确认流程；如果没有这行代码，合同可能绕过用户授权。
    from learning_agent.computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # 新增代码+Phase103ControlledAppLaunch：复用 Computer Use 默认 memory 根；如果没有这行代码，验收证据会散落。
    from learning_agent.runtime.files import atomic_write_json  # 新增代码+Phase103ControlledAppLaunch：复用原子 JSON 写入工具；如果没有这行代码，报告可能半写损坏。
except ModuleNotFoundError as error:  # 新增代码+Phase103ControlledAppLaunch：兼容 start_oauth_agent.bat 从 learning_agent 目录直接运行；如果没有这段代码，真实可见终端可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.app_window_control", "learning_agent.computer_use.mode_session", "learning_agent.computer_use.persistent_grants", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+Phase103ControlledAppLaunch：只对包路径缺失做 fallback；如果没有这行代码，内部真实 bug 可能被误吞。
        raise  # 新增代码+Phase103ControlledAppLaunch：重新抛出非路径类导入错误；如果没有这行代码，底层模块问题会被隐藏。
    from computer_use.app_window_control import build_launch_plan  # type: ignore  # 新增代码+Phase103ControlledAppLaunch：脚本模式复用 Phase69 安全启动计划；如果没有这行代码，bat 入口无法构造安全启动计划。
    from computer_use.mode_session import ComputerUseModeSessionStore  # type: ignore  # 新增代码+Phase103ControlledAppLaunch：脚本模式复用 mode store；如果没有这行代码，bat 合同无法验证 full 状态。
    from computer_use.persistent_grants import DEFAULT_PERSISTENT_GRANTS_ROOT  # type: ignore  # 新增代码+Phase103ControlledAppLaunch：脚本模式复用默认 memory 根；如果没有这行代码，报告目录无法稳定定位。
    from runtime.files import atomic_write_json  # type: ignore  # 新增代码+Phase103ControlledAppLaunch：脚本模式复用原子写入；如果没有这行代码，bat 验收报告可能写坏。

PHASE103_CONTROLLED_APP_LAUNCH_MARKER = "PHASE103_CONTROLLED_APP_LAUNCH_READY"  # 新增代码+Phase103ControlledAppLaunch：定义 Phase103 ready marker；如果没有这行代码，真实终端验收没有稳定等待锚点。
PHASE103_CONTROLLED_APP_LAUNCH_OK_TOKEN = "PHASE103_CONTROLLED_APP_LAUNCH_OK"  # 新增代码+Phase103ControlledAppLaunch：定义 Phase103 OK token；如果没有这行代码，验收日志无法区分成功输出和普通日志。
PHASE103_CONTROLLED_APP_LAUNCH_MODEL = "phase103_controlled_app_launch"  # 新增代码+Phase103ControlledAppLaunch：定义报告模型名；如果没有这行代码，状态矩阵无法区分当前合同版本。
PHASE103_REAL_APP_LAUNCH_ENV = "LEARNING_AGENT_PHASE103_ENABLE_REAL_APP_LAUNCH"  # 新增代码+Phase103ControlledAppLaunch：定义真实应用启动环境门；如果没有这行代码，真实启动启用方式会漂移且难审计。
PHASE103_REAL_APP_LAUNCH_DEFAULT_DISABLED = True  # 新增代码+Phase103ControlledAppLaunch：声明真实应用启动默认关闭；如果没有这行代码，用户可能误以为 full 模式会自动打开应用。
PHASE103_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase103ControlledAppLaunch：声明本阶段没有开放无边界动作面；如果没有这行代码，full 模式可能被误读成任意命令执行。
DEFAULT_PHASE103_CONTROLLED_APP_LAUNCH_ROOT = DEFAULT_PERSISTENT_GRANTS_ROOT.parent / "phase103_controlled_app_launch"  # 新增代码+Phase103ControlledAppLaunch：定义默认报告根目录；如果没有这行代码，验收证据没有固定落点。


def _phase103_bool_token(value: Any) -> str:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会混用 True/False。
    return "true" if bool(value) else "false"  # 新增代码+Phase103ControlledAppLaunch：返回 true 或 false 文本；如果没有这行代码，真实终端场景匹配会不稳定。
# 新增代码+Phase103ControlledAppLaunch：函数段结束，_phase103_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。


def _phase103_env_enabled(name: str) -> bool:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，读取显式环境开关；如果没有这段函数，真实启动开关判断会散落。
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}  # 新增代码+Phase103ControlledAppLaunch：只接受明确真值；如果没有这行代码，模糊环境值可能误开启真实启动。
# 新增代码+Phase103ControlledAppLaunch：函数段结束，_phase103_env_enabled 到此结束；如果没有这个边界说明，初学者不容易看出环境开关范围。


def _phase103_real_launch_enabled(explicit_value: bool | None, default_value: bool | None) -> bool:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，统一判断是否允许进入启动后端；如果没有这段函数，启用逻辑会在调用方重复。
    if explicit_value is not None:  # 新增代码+Phase103ControlledAppLaunch：调用方显式传值时优先使用；如果没有这行代码，单测和上层 gate 无法精确控制。
        return bool(explicit_value)  # 新增代码+Phase103ControlledAppLaunch：返回显式布尔值；如果没有这行代码，显式启用或关闭不会生效。
    if default_value is not None:  # 新增代码+Phase103ControlledAppLaunch：实例默认值存在时使用实例默认值；如果没有这行代码，构造期配置会被忽略。
        return bool(default_value)  # 新增代码+Phase103ControlledAppLaunch：返回实例默认布尔值；如果没有这行代码，受控后端无法被稳定配置。
    return _phase103_env_enabled(PHASE103_REAL_APP_LAUNCH_ENV)  # 新增代码+Phase103ControlledAppLaunch：最后才读取环境门；如果没有这行代码，真实终端无法用受控环境变量启用候选路径。
# 新增代码+Phase103ControlledAppLaunch：函数段结束，_phase103_real_launch_enabled 到此结束；如果没有这个边界说明，初学者不容易看出启用规则。


def _phase103_safe_start_process_plan(plan: dict[str, Any]) -> bool:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，复核 Phase69 启动计划是否安全；如果没有这段函数，后端可能收到危险或未审计命令。
    return bool(plan.get("safe_to_launch") and plan.get("launch_verb") == "Start-Process" and not plan.get("changes_registry") and not plan.get("changes_system_settings") and not plan.get("requires_admin") and not plan.get("uses_shell_string") and not plan.get("actions_expanded"))  # 新增代码+Phase103ControlledAppLaunch：要求安全启动、不改系统、不提权、不走 shell；如果没有这行代码，powershell/admin/settings 等风险可能进入后端。
# 新增代码+Phase103ControlledAppLaunch：函数段结束，_phase103_safe_start_process_plan 到此结束；如果没有这个边界说明，初学者不容易看出安全计划范围。


class Phase103RecordingLaunchBackend:  # 新增代码+Phase103ControlledAppLaunch：类段开始，定义安全记录型启动后端；如果没有这个类，合同测试可能误触真实 Windows 应用。
    def __init__(self) -> None:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，初始化记录型后端；如果没有这段函数，测试无法保存后端调用证据。
        self.launches: list[dict[str, Any]] = []  # 新增代码+Phase103ControlledAppLaunch：保存收到的启动计划副本；如果没有这行代码，后端是否被调用不可验证。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，Phase103RecordingLaunchBackend.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch(self, plan: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，记录一次启动计划而不打开真实应用；如果没有这段函数，合同没有安全后端替身。
        safe_plan = dict(plan)  # 新增代码+Phase103ControlledAppLaunch：复制计划避免调用方后续修改污染记录；如果没有这行代码，审计证据可能不稳定。
        self.launches.append(safe_plan)  # 新增代码+Phase103ControlledAppLaunch：保存启动计划副本；如果没有这行代码，测试无法检查调用次数和目标。
        return {"ok": bool(safe_plan.get("safe_to_launch")), "backend": "phase103_recording_launch_backend", "backend_launch_performed": bool(safe_plan.get("safe_to_launch")), "process_started": False, "process_id": 0, "real_desktop_touched": False, "cleanup_registered": True, "low_level_event_count": 0, "plan": safe_plan}  # 新增代码+Phase103ControlledAppLaunch：返回安全记录结果；如果没有这行代码，显式桥接路径需要真实启动才能验收。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，Phase103RecordingLaunchBackend.launch 到此结束；如果没有这个边界说明，初学者不容易看出记录启动范围。
# 新增代码+Phase103ControlledAppLaunch：类段结束，Phase103RecordingLaunchBackend 到此结束；如果没有这个边界说明，初学者不容易看出安全替身范围。


class Phase103SubprocessLaunchBackend:  # 新增代码+Phase103ControlledAppLaunch：类段开始，定义可选真实进程启动后端；如果没有这个类，Phase103 没有通往受控真实启动的候选实现。
    def __init__(self, platform: str | None = None) -> None:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，初始化真实后端平台和进程记录；如果没有这段函数，后续 cleanup 无法只管理自己启动的进程。
        self.platform = str(platform or sys.platform)  # 新增代码+Phase103ControlledAppLaunch：保存平台名用于 Windows 检查；如果没有这行代码，非 Windows 环境可能误启动。
        self.processes: list[Any] = []  # 新增代码+Phase103ControlledAppLaunch：保存本后端启动的进程对象；如果没有这行代码，cleanup 无法收尾自己的进程。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，Phase103SubprocessLaunchBackend.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch(self, plan: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，按安全计划启动真实进程；如果没有这段函数，受控真实启动候选没有最后一跳实现。
        if not self.platform.startswith("win"):  # 新增代码+Phase103ControlledAppLaunch：只允许 Windows 平台执行真实启动；如果没有这行代码，Linux/macOS 测试可能误走 Windows exe。
            return {"ok": False, "backend": "phase103_subprocess_launch_backend", "decision": "non_windows_platform_rejected", "backend_launch_performed": False, "real_desktop_touched": False, "cleanup_registered": False, "low_level_event_count": 0}  # 新增代码+Phase103ControlledAppLaunch：非 Windows 返回安全拒绝；如果没有这行代码，平台错误会变成难懂异常。
        if not _phase103_safe_start_process_plan(dict(plan)):  # 新增代码+Phase103ControlledAppLaunch：真实后端再复核安全计划；如果没有这行代码，调用方 bug 可能把危险计划送到 subprocess。
            return {"ok": False, "backend": "phase103_subprocess_launch_backend", "decision": "unsafe_launch_plan_rejected", "backend_launch_performed": False, "real_desktop_touched": False, "cleanup_registered": False, "low_level_event_count": 0}  # 新增代码+Phase103ControlledAppLaunch：危险计划零副作用拒绝；如果没有这行代码，高风险目标可能被启动。
        executable = str(plan.get("executable", ""))  # 新增代码+Phase103ControlledAppLaunch：读取已审核的 exe 名；如果没有这行代码，后端没有启动目标。
        arguments = [str(argument) for argument in list(plan.get("arguments", []) or [])]  # 新增代码+Phase103ControlledAppLaunch：把参数规范成字符串列表；如果没有这行代码，Popen 参数可能收到坏类型。
        command = [executable, *arguments]  # 新增代码+Phase103ControlledAppLaunch：构造无 shell 的参数数组；如果没有这行代码，命令可能被拼成高风险 shell 字符串。
        import subprocess  # 新增代码+Phase103ControlledAppLaunch：只在真实启动路径导入 subprocess；如果没有这行代码，后端无法启动受控进程。
        process = subprocess.Popen(command, shell=False)  # 新增代码+Phase103ControlledAppLaunch：用无 shell 模式启动安全计划；如果没有这行代码，显式真实启动候选无法真正打开应用。
        self.processes.append(process)  # 新增代码+Phase103ControlledAppLaunch：记录本后端启动的进程；如果没有这行代码，cleanup 无法只清理自己创建的对象。
        return {"ok": True, "backend": "phase103_subprocess_launch_backend", "backend_launch_performed": True, "process_started": True, "process_id": int(getattr(process, "pid", 0) or 0), "real_desktop_touched": True, "cleanup_registered": True, "low_level_event_count": 0, "command_shape": "argv_no_shell"}  # 新增代码+Phase103ControlledAppLaunch：返回真实启动摘要；如果没有这行代码，上层无法审计是否触碰桌面。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，Phase103SubprocessLaunchBackend.launch 到此结束；如果没有这个边界说明，初学者不容易看出真实启动范围。

    def cleanup(self) -> dict[str, Any]:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，清理本后端启动的进程；如果没有这段函数，真实 smoke 后可能留下测试窗口。
        cleaned = 0  # 新增代码+Phase103ControlledAppLaunch：记录成功发出终止的进程数；如果没有这行代码，清理结果不可见。
        for process in list(self.processes):  # 新增代码+Phase103ControlledAppLaunch：遍历本后端保存的进程；如果没有这行代码，cleanup 不知道处理哪些对象。
            if getattr(process, "poll", lambda: None)() is None:  # 新增代码+Phase103ControlledAppLaunch：只处理仍在运行的进程；如果没有这行代码，已退出进程可能触发无意义操作。
                getattr(process, "terminate")()  # 新增代码+Phase103ControlledAppLaunch：请求终止本后端启动的进程；如果没有这行代码，真实 smoke 可能残留窗口。
                cleaned += 1  # 新增代码+Phase103ControlledAppLaunch：累计清理数量；如果没有这行代码，报告无法说明清理效果。
        return {"cleanup_attempted": True, "processes_cleaned": cleaned}  # 新增代码+Phase103ControlledAppLaunch：返回清理摘要；如果没有这行代码，调用方无法确认是否已收尾。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，Phase103SubprocessLaunchBackend.cleanup 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。
# 新增代码+Phase103ControlledAppLaunch：类段结束，Phase103SubprocessLaunchBackend 到此结束；如果没有这个边界说明，初学者不容易看出真实后端范围。


class WindowsControlledAppLaunchCandidate:  # 新增代码+Phase103ControlledAppLaunch：类段开始，定义 full 模式应用启动受控候选；如果没有这个类，launch_app 只能停留在 Phase102 recording-only。
    def __init__(self, launch_backend: Any | None = None, default_enable_real_launch: bool | None = None) -> None:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，注入启动后端和默认启用状态；如果没有这段函数，测试和生产无法替换最后一跳。
        self.launch_backend = launch_backend if launch_backend is not None else Phase103RecordingLaunchBackend()  # 新增代码+Phase103ControlledAppLaunch：默认使用记录后端；如果没有这行代码，普通运行可能误触真实桌面。
        self.default_enable_real_launch = default_enable_real_launch  # 新增代码+Phase103ControlledAppLaunch：保存实例默认启用值；如果没有这行代码，上层配置无法传入。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，WindowsControlledAppLaunchCandidate.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def _refusal(self, decision: str, plan: dict[str, Any], reason: str) -> dict[str, Any]:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，生成统一零副作用拒绝结果；如果没有这段函数，拒绝字段会分散且容易漏零事件。
        return {"ok": False, "decision": decision, "reason": reason, "controlled_launch_candidate_ready": True, "safe_start_process_plan": False, "real_app_launch_default_disabled": PHASE103_REAL_APP_LAUNCH_DEFAULT_DISABLED, "backend_launch_reaches_launcher": False, "real_dispatch_performed": False, "real_desktop_touched": False, "low_level_event_count": 0, "unsafe_launch_zero_events": True, "uncontrolled_actions_expanded": PHASE103_UNCONTROLLED_ACTIONS_EXPANDED, "plan": dict(plan)}  # 新增代码+Phase103ControlledAppLaunch：返回完整拒绝报告；如果没有这行代码，危险计划可能无法被自动验收为零副作用。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，WindowsControlledAppLaunchCandidate._refusal 到此结束；如果没有这个边界说明，初学者不容易看出拒绝范围。

    def launch(self, app_name: str, enable_real_launch: bool | None = None, test_file: str | None = None) -> dict[str, Any]:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，执行受控应用启动候选；如果没有这段函数，full gate 没有统一入口。
        plan = build_launch_plan(app_name, test_file=test_file)  # 新增代码+Phase103ControlledAppLaunch：复用 Phase69 构造安全启动计划；如果没有这行代码，用户输入可能直接变成命令。
        safe_start_process_plan = _phase103_safe_start_process_plan(plan)  # 新增代码+Phase103ControlledAppLaunch：复核计划安全属性；如果没有这行代码，后端可能收到未审计计划。
        if not safe_start_process_plan:  # 新增代码+Phase103ControlledAppLaunch：危险或无效计划先拒绝；如果没有这行代码，powershell/cmd/settings 等目标可能进入后端。
            return self._refusal("unsafe_launch_plan_rejected", plan, str(plan.get("refusal_reason", "unsafe_launch_plan") or "unsafe_launch_plan"))  # 新增代码+Phase103ControlledAppLaunch：返回危险计划零副作用拒绝；如果没有这行代码，危险路径不可审计。
        launch_enabled = _phase103_real_launch_enabled(enable_real_launch, self.default_enable_real_launch)  # 新增代码+Phase103ControlledAppLaunch：计算是否允许进入启动后端；如果没有这行代码，默认关闭和显式开启无法区分。
        if not launch_enabled:  # 新增代码+Phase103ControlledAppLaunch：默认关闭时只返回候选报告；如果没有这行代码，普通 full gate 会直接调用后端。
            return {"ok": True, "decision": "real_app_launch_disabled_by_default", "controlled_launch_candidate_ready": True, "safe_start_process_plan": True, "real_app_launch_default_disabled": PHASE103_REAL_APP_LAUNCH_DEFAULT_DISABLED, "backend_launch_reaches_launcher": False, "real_dispatch_performed": False, "real_desktop_touched": False, "low_level_event_count": 0, "unsafe_launch_zero_events": False, "uncontrolled_actions_expanded": PHASE103_UNCONTROLLED_ACTIONS_EXPANDED, "plan": dict(plan)}  # 新增代码+Phase103ControlledAppLaunch：返回默认关闭零副作用报告；如果没有这行代码，用户无法确认只是受控候选而非已打开。
        launch_method = getattr(self.launch_backend, "launch", None)  # 新增代码+Phase103ControlledAppLaunch：读取注入后端的 launch 方法；如果没有这行代码，后端对象无法被调用。
        if not callable(launch_method):  # 新增代码+Phase103ControlledAppLaunch：检查后端接口是否可用；如果没有这行代码，错误后端会产生难懂异常。
            return self._refusal("launch_backend_missing", plan, "缺少可调用的受控启动后端。")  # 新增代码+Phase103ControlledAppLaunch：返回后端缺失拒绝；如果没有这行代码，用户不知道如何配置。
        raw_result = launch_method(dict(plan))  # 新增代码+Phase103ControlledAppLaunch：把安全计划送到后端；如果没有这行代码，Phase103 仍停在报告层。
        backend_result = dict(raw_result) if isinstance(raw_result, dict) else {"ok": bool(raw_result)}  # 新增代码+Phase103ControlledAppLaunch：规整后端返回值；如果没有这行代码，非 dict 后端会污染上层。
        backend_reaches_launcher = bool(backend_result.get("backend_launch_performed") or backend_result.get("ok"))  # 新增代码+Phase103ControlledAppLaunch：判断后端是否收到并处理计划；如果没有这行代码，桥接成功不可见。
        real_desktop_touched = bool(backend_result.get("real_desktop_touched"))  # 新增代码+Phase103ControlledAppLaunch：读取后端是否触碰真实桌面；如果没有这行代码，安全报告会过度承诺。
        return {"ok": bool(backend_result.get("ok") and backend_reaches_launcher), "decision": "controlled_app_launch_sent_to_backend", "controlled_launch_candidate_ready": True, "safe_start_process_plan": True, "real_app_launch_default_disabled": PHASE103_REAL_APP_LAUNCH_DEFAULT_DISABLED, "backend_launch_reaches_launcher": backend_reaches_launcher, "real_dispatch_performed": real_desktop_touched, "real_desktop_touched": real_desktop_touched, "low_level_event_count": int(backend_result.get("low_level_event_count", 0) or 0), "unsafe_launch_zero_events": False, "uncontrolled_actions_expanded": PHASE103_UNCONTROLLED_ACTIONS_EXPANDED, "plan": dict(plan), "backend_result": backend_result}  # 新增代码+Phase103ControlledAppLaunch：返回后端桥接摘要；如果没有这行代码，测试和终端拿不到统一事实。
    # 新增代码+Phase103ControlledAppLaunch：函数段结束，WindowsControlledAppLaunchCandidate.launch 到此结束；如果没有这个边界说明，初学者不容易看出启动候选范围。
# 新增代码+Phase103ControlledAppLaunch：类段结束，WindowsControlledAppLaunchCandidate 到此结束；如果没有这个边界说明，初学者不容易看出受控候选范围。


def run_phase103_controlled_app_launch_contract(base_dir: str | Path | None = None) -> dict[str, Any]:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，运行 Phase103 总合同；如果没有这段函数，测试和真实终端没有同一事实源。
    root = Path(base_dir) if base_dir is not None else DEFAULT_PHASE103_CONTROLLED_APP_LAUNCH_ROOT / f"contract-{int(time.time() * 1000)}"  # 新增代码+Phase103ControlledAppLaunch：选择隔离合同目录；如果没有这行代码，多次验收会互相污染。
    root.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase103ControlledAppLaunch：确保合同根目录存在；如果没有这行代码，报告写入会失败。
    default_backend = Phase103RecordingLaunchBackend()  # 新增代码+Phase103ControlledAppLaunch：创建默认关闭路径后端；如果没有这行代码，无法证明默认关闭不会调用后端。
    default_runtime = WindowsControlledAppLaunchCandidate(launch_backend=default_backend)  # 新增代码+Phase103ControlledAppLaunch：创建默认关闭 runtime；如果没有这行代码，安全默认值没有被测对象。
    default_off = default_runtime.launch("notepad", enable_real_launch=False)  # 新增代码+Phase103ControlledAppLaunch：执行默认关闭启动候选；如果没有这行代码，default_off 事实缺失。
    enabled_backend = Phase103RecordingLaunchBackend()  # 新增代码+Phase103ControlledAppLaunch：创建显式启用记录后端；如果没有这行代码，后端桥接没有安全替身。
    enabled_runtime = WindowsControlledAppLaunchCandidate(launch_backend=enabled_backend)  # 新增代码+Phase103ControlledAppLaunch：创建显式启用 runtime；如果没有这行代码，正向桥接没有主体。
    enabled = enabled_runtime.launch("notepad", enable_real_launch=True)  # 新增代码+Phase103ControlledAppLaunch：显式启用并送到记录后端；如果没有这行代码，最后一跳候选没有证据。
    unsafe_backend = Phase103RecordingLaunchBackend()  # 新增代码+Phase103ControlledAppLaunch：创建危险路径后端；如果没有这行代码，无法证明拒绝前没有调用后端。
    unsafe_runtime = WindowsControlledAppLaunchCandidate(launch_backend=unsafe_backend)  # 新增代码+Phase103ControlledAppLaunch：创建危险路径 runtime；如果没有这行代码，unsafe_zero 没有被测对象。
    unsafe = unsafe_runtime.launch("powershell", enable_real_launch=True)  # 新增代码+Phase103ControlledAppLaunch：尝试危险 powershell 启动；如果没有这行代码，高风险拒绝没有样本。
    from learning_agent.computer_use.universal_live_execution import UniversalWindowsLiveExecutionGate  # 新增代码+Phase103ControlledAppLaunch：函数内导入避免和 live gate 形成顶层循环；如果没有这行代码，合同无法验证 full gate 接入。
    full_store = ComputerUseModeSessionStore(base_dir=root / "full_mode_sessions")  # 新增代码+Phase103ControlledAppLaunch：创建隔离 full mode store；如果没有这行代码，合同会污染真实用户权限状态。
    full_request = full_store.request_full_mode(reason="Phase103 contract requests full mode")  # 新增代码+Phase103ControlledAppLaunch：按真实流程申请 full token；如果没有这行代码，合同会绕过二次确认。
    full_store.confirm_full_mode(full_request["confirmation_token"], reason="Phase103 contract confirms full mode")  # 新增代码+Phase103ControlledAppLaunch：用 token 确认 full 模式；如果没有这行代码，launch_app 应该被 mode gate 拦截。
    universal_backend = Phase103RecordingLaunchBackend()  # 新增代码+Phase103ControlledAppLaunch：创建 full gate 注入后端；如果没有这行代码，无法证明 gate 默认关闭不调用后端。
    universal_candidate = WindowsControlledAppLaunchCandidate(launch_backend=universal_backend)  # 新增代码+Phase103ControlledAppLaunch：创建 full gate 受控候选；如果没有这行代码，Phase103 不能证明接入真实入口。
    universal_runtime = UniversalWindowsLiveExecutionGate(base_dir=root / "universal_live_gate", mode_store=full_store, controlled_launch_candidate=universal_candidate)  # 新增代码+Phase103ControlledAppLaunch：创建注入候选的 live gate；如果没有这行代码，合同只验证底层模块。
    universal_report = universal_runtime.run_prompt("请使用 full 模式启动 notepad，只做受控启动候选合同，不要真实打开。", request_real_actions=True)  # 新增代码+Phase103ControlledAppLaunch：运行真实用户风格 full 启动 prompt；如果没有这行代码，full gate 接入没有事实。
    universal_actions = [event.get("action_result", {}) for event in universal_report.get("loop", {}).get("events", []) if event.get("state") == "acted"]  # 新增代码+Phase103ControlledAppLaunch：提取 full gate 动作报告；如果没有这行代码，无法检查 launch_app 是否接入候选。
    universal_launch = next((action for action in universal_actions if isinstance(action, dict) and action.get("action_class") == "launch_app"), {})  # 新增代码+Phase103ControlledAppLaunch：定位 launch_app 动作报告；如果没有这行代码，observe/verify 报告会干扰判断。
    default_off_zero_events = bool(default_off.get("decision") == "real_app_launch_disabled_by_default" and len(default_backend.launches) == 0 and not default_off.get("real_desktop_touched"))  # 新增代码+Phase103ControlledAppLaunch：判断默认关闭是否零副作用；如果没有这行代码，安全默认值不可量化。
    enabled_backend_reaches = bool(enabled.get("backend_launch_reaches_launcher") and len(enabled_backend.launches) == 1 and enabled.get("safe_start_process_plan"))  # 新增代码+Phase103ControlledAppLaunch：判断显式启用是否到达后端；如果没有这行代码，Phase103 可能没有推进到最后一跳。
    unsafe_launch_zero_events = bool(unsafe.get("decision") == "unsafe_launch_plan_rejected" and len(unsafe_backend.launches) == 0 and unsafe.get("unsafe_launch_zero_events"))  # 新增代码+Phase103ControlledAppLaunch：判断危险启动是否零事件；如果没有这行代码，高风险拦截不可量化。
    universal_full_gate_uses_controlled_launcher = bool(universal_report.get("full_mode_session_used") and universal_report.get("full_mode_action_ready") and universal_launch.get("controlled_launch_candidate_ready") and universal_launch.get("controlled_launch_result", {}).get("decision") == "real_app_launch_disabled_by_default" and len(universal_backend.launches) == 0)  # 新增代码+Phase103ControlledAppLaunch：判断 full gate 是否接入默认关闭候选；如果没有这行代码，底层能力可能没接到入口。
    real_desktop_touched = bool(default_off.get("real_desktop_touched") or enabled.get("real_desktop_touched") or unsafe.get("real_desktop_touched") or universal_report.get("real_desktop_touched"))  # 新增代码+Phase103ControlledAppLaunch：汇总是否触碰真实桌面；如果没有这行代码，合同可能过度承诺安全。
    report_path = root / "reports" / "phase103_controlled_app_launch_report.json"  # 新增代码+Phase103ControlledAppLaunch：定义报告路径；如果没有这行代码，验收证据没有固定文件。
    passed = bool(default_off_zero_events and enabled_backend_reaches and unsafe_launch_zero_events and universal_full_gate_uses_controlled_launcher and not real_desktop_touched and not PHASE103_UNCONTROLLED_ACTIONS_EXPANDED)  # 新增代码+Phase103ControlledAppLaunch：汇总合同通过条件；如果没有这行代码，main 无法用退出码表达失败。
    report = {"marker": PHASE103_CONTROLLED_APP_LAUNCH_MARKER, "ok_token": PHASE103_CONTROLLED_APP_LAUNCH_OK_TOKEN, "model": PHASE103_CONTROLLED_APP_LAUNCH_MODEL, "passed": passed, "controlled_launch_candidate_ready": True, "real_app_launch_default_disabled": PHASE103_REAL_APP_LAUNCH_DEFAULT_DISABLED, "default_off_zero_events": default_off_zero_events, "enabled_backend_reaches_launcher": enabled_backend_reaches, "unsafe_launch_zero_events": unsafe_launch_zero_events, "universal_full_gate_uses_controlled_launcher": universal_full_gate_uses_controlled_launcher, "real_desktop_touched": real_desktop_touched, "real_app_launch_env_gate": PHASE103_REAL_APP_LAUNCH_ENV, "uncontrolled_actions_expanded": PHASE103_UNCONTROLLED_ACTIONS_EXPANDED, "report_path": str(report_path), "default_off_report": default_off, "enabled_report": enabled, "unsafe_report": unsafe, "universal_report": universal_report}  # 新增代码+Phase103ControlledAppLaunch：构造完整合同报告；如果没有这行代码，测试和真实终端拿不到统一事实。
    atomic_write_json(report_path, report)  # 新增代码+Phase103ControlledAppLaunch：原子写入合同报告；如果没有这行代码，失败时可能留下半个 JSON。
    return report  # 新增代码+Phase103ControlledAppLaunch：返回合同报告；如果没有这行代码，调用方无法读取验收结果。
# 新增代码+Phase103ControlledAppLaunch：函数段结束，run_phase103_controlled_app_launch_contract 到此结束；如果没有这个边界说明，初学者不容易看出合同范围。


def phase103_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，把报告转成真实终端稳定 token 行；如果没有这段函数，验收器需要解析复杂 JSON。
    return f"{PHASE103_CONTROLLED_APP_LAUNCH_MARKER} {PHASE103_CONTROLLED_APP_LAUNCH_OK_TOKEN} controlled_launch_candidate_ready={_phase103_bool_token(report.get('controlled_launch_candidate_ready'))} real_app_launch_default_disabled={_phase103_bool_token(report.get('real_app_launch_default_disabled'))} default_off_zero_events={_phase103_bool_token(report.get('default_off_zero_events'))} enabled_backend_reaches_launcher={_phase103_bool_token(report.get('enabled_backend_reaches_launcher'))} unsafe_launch_zero_events={_phase103_bool_token(report.get('unsafe_launch_zero_events'))} universal_full_gate_uses_controlled_launcher={_phase103_bool_token(report.get('universal_full_gate_uses_controlled_launcher'))} real_desktop_touched={_phase103_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase103_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+Phase103ControlledAppLaunch：返回固定顺序 token；如果没有这行代码，真实终端验收容易因输出漂移失败。
# 新增代码+Phase103ControlledAppLaunch：函数段结束，phase103_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 格式范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase103ControlledAppLaunch：函数段开始，提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase103 合同。
    _ = argv  # 新增代码+Phase103ControlledAppLaunch：保留 argv 扩展位；如果没有这行代码，读者可能误以为参数被遗漏。
    report = run_phase103_controlled_app_launch_contract()  # 新增代码+Phase103ControlledAppLaunch：运行无真实桌面副作用合同；如果没有这行代码，CLI 不会产生验收事实。
    print(phase103_cli_line(report))  # 新增代码+Phase103ControlledAppLaunch：打印稳定 token 行；如果没有这行代码，验收脚本无法快速匹配成功条件。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase103ControlledAppLaunch：打印结构化报告；如果没有这行代码，失败时不易复盘。
    print(PHASE103_CONTROLLED_APP_LAUNCH_MARKER)  # 新增代码+Phase103ControlledAppLaunch：单独打印 ready marker；如果没有这行代码，人工观察终端时容易漏标识。
    return 0 if bool(report.get("passed")) else 1  # 新增代码+Phase103ControlledAppLaunch：按合同结果返回退出码；如果没有这行代码，失败也可能被自动化当成成功。
# 新增代码+Phase103ControlledAppLaunch：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["DEFAULT_PHASE103_CONTROLLED_APP_LAUNCH_ROOT", "PHASE103_CONTROLLED_APP_LAUNCH_MARKER", "PHASE103_CONTROLLED_APP_LAUNCH_MODEL", "PHASE103_CONTROLLED_APP_LAUNCH_OK_TOKEN", "PHASE103_REAL_APP_LAUNCH_DEFAULT_DISABLED", "PHASE103_REAL_APP_LAUNCH_ENV", "PHASE103_UNCONTROLLED_ACTIONS_EXPANDED", "Phase103RecordingLaunchBackend", "Phase103SubprocessLaunchBackend", "WindowsControlledAppLaunchCandidate", "main", "phase103_cli_line", "run_phase103_controlled_app_launch_contract"]  # 新增代码+Phase103ControlledAppLaunch：限定公开导出名称；如果没有这行代码，from module import * 会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase103ControlledAppLaunch：允许直接运行模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase103ControlledAppLaunch：用 main 返回码退出；如果没有这行代码，命令行状态不明确。
