"""Phase109 通用 Windows 真实启动候选、身份验证与清理合同。"""  # 新增代码+Phase109GenericRealLaunchCandidate：说明本模块负责把 Phase108 通用发现推进到“可真实启动候选”模型；如果没有这行代码，读者容易误以为这里已经默认放开真实桌面控制。
from __future__ import annotations  # 新增代码+Phase109GenericRealLaunchCandidate：启用延迟类型注解解析；如果没有这行代码，类之间的类型提示在旧导入顺序下更容易解析失败。

import json  # 新增代码+Phase109GenericRealLaunchCandidate：导入 JSON 用于命令行输出完整合同报告；如果没有这行代码，失败排查只能看短 token 行。
from typing import Any  # 新增代码+Phase109GenericRealLaunchCandidate：导入 Any 描述 JSON 风格动态报告；如果没有这行代码，接口字段含义对初学者不清楚。

try:  # 新增代码+Phase109GenericRealLaunchCandidate：优先按标准包路径导入 Phase108 通用发现；如果没有这段代码，单元测试和真实终端无法共享同一发现事实。
    from learning_agent.computer_use.generic_app_discovery import PHASE108_GENERIC_APP_DISCOVERY_MODEL, resolve_generic_app_launch_target  # 新增代码+Phase109GenericRealLaunchCandidate：复用 Phase108 解析器和模型名；如果没有这行代码，Phase109 可能重新发明发现逻辑并退回逐应用补丁。
except ModuleNotFoundError as error:  # 新增代码+Phase109GenericRealLaunchCandidate：兼容 start_oauth_agent.bat 从 learning_agent 目录启动的脚本模式；如果没有这段代码，真实可见终端可能导入失败。
    if error.name not in {"learning_agent", "learning_agent.computer_use", "learning_agent.computer_use.generic_app_discovery"}:  # 新增代码+Phase109GenericRealLaunchCandidate：只兜底包路径缺失；如果没有这行代码，Phase108 内部 bug 可能被误吞。
        raise  # 新增代码+Phase109GenericRealLaunchCandidate：重新抛出真实内部错误；如果没有这行代码，排查发现链路会很困难。
    from computer_use.generic_app_discovery import PHASE108_GENERIC_APP_DISCOVERY_MODEL, resolve_generic_app_launch_target  # type: ignore  # 新增代码+Phase109GenericRealLaunchCandidate：脚本模式导入同一 Phase108 能力；如果没有这行代码，双击 bat 后 Phase109 不可用。

PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_MARKER = "PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_READY"  # 新增代码+Phase109GenericRealLaunchCandidate：定义 Phase109 ready marker；如果没有这行代码，测试和真实终端无法稳定定位通用启动候选输出。
PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_OK_TOKEN = "PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_OK"  # 新增代码+Phase109GenericRealLaunchCandidate：定义 Phase109 成功 token；如果没有这行代码，失败输出和成功输出不容易区分。
PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_MODEL = "phase109_generic_real_launch_candidate"  # 新增代码+Phase109GenericRealLaunchCandidate：定义报告模型名；如果没有这行代码，能力矩阵无法区分 Phase109 和 Phase108。
PHASE109_REAL_LAUNCH_DEFAULT_DISABLED = True  # 新增代码+Phase109GenericRealLaunchCandidate：声明通用真实启动默认关闭；如果没有这行代码，/computer use --full 容易被误解成自动打开任意应用。
PHASE109_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+Phase109GenericRealLaunchCandidate：声明本阶段没有扩张无边界动作面；如果没有这行代码，通用候选可能被误读为无限权限。


def _phase109_bool_token(value: Any) -> str:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，把布尔值转成稳定小写 token；如果没有这段函数，CLI 输出会混用 True/False 影响验收匹配。
    return "true" if bool(value) else "false"  # 新增代码+Phase109GenericRealLaunchCandidate：返回 true 或 false 文本；如果没有这行代码，真实终端场景匹配容易因大小写漂移失败。
# 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，_phase109_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出布尔格式化范围。


def _phase109_normalize_identity(value: Any) -> str:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，规范化进程和窗口身份文本；如果没有这段函数，Obsidian 与 Obsidian.exe 这类名称不容易稳定比对。
    text = str(value or "").strip().strip("\"'`").lower()  # 新增代码+Phase109GenericRealLaunchCandidate：清理空白、引号并转小写；如果没有这行代码，复制来的应用名会造成身份比对漂移。
    return text[:-4] if text.endswith(".exe") else text  # 新增代码+Phase109GenericRealLaunchCandidate：去掉 exe 后缀得到可比较短名；如果没有这行代码，进程名和 canonical target 可能无法匹配。
# 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，_phase109_normalize_identity 到此结束；如果没有这个边界说明，初学者不容易看出身份规范化范围。


class Phase109RecordingGenericLaunchBackend:  # 新增代码+Phase109GenericRealLaunchCandidate：类段开始，定义记录型通用启动后端；如果没有这个类，合同测试可能需要真的打开用户本机应用才能证明最后一跳。
    def __init__(self) -> None:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，初始化记录型后端；如果没有这段函数，测试无法保存后端是否被调用的证据。
        self.launches: list[dict[str, Any]] = []  # 新增代码+Phase109GenericRealLaunchCandidate：保存收到的 Phase108 报告副本；如果没有这行代码，默认关闭是否真的没进后端不可验证。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，Phase109RecordingGenericLaunchBackend.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def launch(self, phase108_report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，记录一次通用启动请求但不打开真实应用；如果没有这段函数，显式启用路径没有安全替身。
        safe_report = dict(phase108_report)  # 新增代码+Phase109GenericRealLaunchCandidate：复制 Phase108 报告避免调用方后续修改污染记录；如果没有这行代码，审计证据可能不稳定。
        self.launches.append(safe_report)  # 新增代码+Phase109GenericRealLaunchCandidate：保存本次启动请求；如果没有这行代码，测试无法确认后端调用次数。
        executable = str(safe_report.get("best_candidate_executable", "") or safe_report.get("canonical_target", ""))  # 新增代码+Phase109GenericRealLaunchCandidate：读取 Phase108 发现到的可执行身份；如果没有这行代码，后续进程身份没有目标来源。
        process_id = 10900 + len(self.launches)  # 新增代码+Phase109GenericRealLaunchCandidate：生成稳定的记录型进程 id；如果没有这行代码，窗口归属无法和进程身份对应。
        return {"ok": bool(executable), "backend": "phase109_recording_generic_launch_backend", "backend_launch_performed": bool(executable), "process_started": True, "process_id": process_id, "process_handle_id": f"phase109-process:{process_id}", "process_executable": executable, "process_identity_verified": bool(executable), "real_desktop_touched": False, "phase108_report": safe_report}  # 新增代码+Phase109GenericRealLaunchCandidate：返回记录型进程摘要；如果没有这行代码，启用路径无法继续验证窗口身份和清理。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，Phase109RecordingGenericLaunchBackend.launch 到此结束；如果没有这个边界说明，初学者不容易看出记录启动范围。
# 新增代码+Phase109GenericRealLaunchCandidate：类段结束，Phase109RecordingGenericLaunchBackend 到此结束；如果没有这个边界说明，初学者不容易看出记录后端范围。


class Phase109RecordingWindowIdentityProbe:  # 新增代码+Phase109GenericRealLaunchCandidate：类段开始，定义记录型窗口身份探针；如果没有这个类，启动后无法证明窗口属于刚才的目标进程。
    def __init__(self) -> None:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，初始化窗口探针记录；如果没有这段函数，测试无法保存探测过的窗口证据。
        self.windows: list[dict[str, Any]] = []  # 新增代码+Phase109GenericRealLaunchCandidate：保存生成的窗口身份记录；如果没有这行代码，窗口探针是否运行不可审计。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，Phase109RecordingWindowIdentityProbe.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def wait_for_verified_window(self, process_report: dict[str, Any], phase108_report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，等待并验证目标窗口身份；如果没有这段函数，后续自动化可能误操作别的窗口。
        process_id = int(process_report.get("process_id", 0) or 0)  # 新增代码+Phase109GenericRealLaunchCandidate：读取记录型进程 id；如果没有这行代码，窗口归属没有进程基准。
        executable = str(process_report.get("process_executable", "") or phase108_report.get("best_candidate_executable", ""))  # 新增代码+Phase109GenericRealLaunchCandidate：读取进程可执行名；如果没有这行代码，窗口 app_id 没有目标身份。
        canonical_target = str(phase108_report.get("canonical_target", "") or "")  # 新增代码+Phase109GenericRealLaunchCandidate：读取 Phase108 canonical target；如果没有这行代码，窗口身份无法和用户目标比对。
        same_target = bool(process_id and _phase109_normalize_identity(executable) == _phase109_normalize_identity(canonical_target))  # 新增代码+Phase109GenericRealLaunchCandidate：确认进程名与用户目标一致；如果没有这行代码，错误应用也可能被当成成功启动。
        window = {"window_id": f"phase109-window:{process_id}", "window_process_id": process_id, "window_executable": executable, "app_id": executable, "title_preview": f"{canonical_target} - Phase109 recording", "safe_to_target": same_target}  # 新增代码+Phase109GenericRealLaunchCandidate：构造记录型窗口身份；如果没有这行代码，窗口探针没有可验证对象。
        self.windows.append(dict(window))  # 新增代码+Phase109GenericRealLaunchCandidate：保存窗口身份副本；如果没有这行代码，测试无法确认探针生成过窗口。
        return {"ok": same_target, "visible_window_verified": same_target, "window_identity_verified": same_target, "target_identity_verified": same_target, "process_identity_verified": bool(process_report.get("process_identity_verified", False)), "real_desktop_touched": False, "window": window}  # 新增代码+Phase109GenericRealLaunchCandidate：返回窗口验证摘要；如果没有这行代码，上层无法决定是否继续清理和验收。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，Phase109RecordingWindowIdentityProbe.wait_for_verified_window 到此结束；如果没有这个边界说明，初学者不容易看出窗口验证范围。
# 新增代码+Phase109GenericRealLaunchCandidate：类段结束，Phase109RecordingWindowIdentityProbe 到此结束；如果没有这个边界说明，初学者不容易看出窗口探针范围。


class Phase109RecordingCleanupManager:  # 新增代码+Phase109GenericRealLaunchCandidate：类段开始，定义记录型清理管理器；如果没有这个类，未来真实启动后可能没有统一收尾模型。
    def __init__(self) -> None:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，初始化清理记录；如果没有这段函数，测试无法保存清理调用证据。
        self.cleanups: list[dict[str, Any]] = []  # 新增代码+Phase109GenericRealLaunchCandidate：保存清理请求摘要；如果没有这行代码，清理是否执行不可验证。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，Phase109RecordingCleanupManager.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def cleanup(self, process_report: dict[str, Any], window_report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，清理本候选拥有的记录型进程和窗口；如果没有这段函数，通用真实启动没有残留检查闭环。
        cleanup_record = {"process_id": int(process_report.get("process_id", 0) or 0), "window_id": str(dict(window_report.get("window", {}) or {}).get("window_id", ""))}  # 新增代码+Phase109GenericRealLaunchCandidate：构造清理对象身份；如果没有这行代码，清理范围无法证明只覆盖自己拥有的目标。
        self.cleanups.append(dict(cleanup_record))  # 新增代码+Phase109GenericRealLaunchCandidate：保存清理记录；如果没有这行代码，测试无法确认 cleanup 被调用。
        return {"ok": bool(cleanup_record["process_id"] and cleanup_record["window_id"]), "cleanup_attempted": True, "cleanup_completed": True, "owned_process_only": True, "owned_window_only": True, "verified_window_cleanup_completed": True, "residual_process_check_completed": True, "residual_owned_process": False, "real_desktop_touched": False, "cleanup_record": cleanup_record}  # 新增代码+Phase109GenericRealLaunchCandidate：返回清理与残留检查摘要；如果没有这行代码，上层无法证明没有留下本候选拥有的进程。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，Phase109RecordingCleanupManager.cleanup 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。
# 新增代码+Phase109GenericRealLaunchCandidate：类段结束，Phase109RecordingCleanupManager 到此结束；如果没有这个边界说明，初学者不容易看出清理管理器范围。


class Phase109GenericRealLaunchCandidate:  # 新增代码+Phase109GenericRealLaunchCandidate：类段开始，定义通用真实启动候选编排器；如果没有这个类，发现、启动、窗口验证和清理会散落到交互层。
    def __init__(self, launch_backend: Any | None = None, window_probe: Any | None = None, cleanup_manager: Any | None = None) -> None:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，允许注入后端、窗口探针和清理器；如果没有这段函数，测试和未来真实后端无法复用同一编排逻辑。
        self.launch_backend = launch_backend if launch_backend is not None else Phase109RecordingGenericLaunchBackend()  # 新增代码+Phase109GenericRealLaunchCandidate：保存启动后端并默认使用记录型替身；如果没有这行代码，默认测试可能触碰真实桌面。
        self.window_probe = window_probe if window_probe is not None else Phase109RecordingWindowIdentityProbe()  # 新增代码+Phase109GenericRealLaunchCandidate：保存窗口身份探针；如果没有这行代码，启动后无法验证目标窗口。
        self.cleanup_manager = cleanup_manager if cleanup_manager is not None else Phase109RecordingCleanupManager()  # 新增代码+Phase109GenericRealLaunchCandidate：保存清理管理器；如果没有这行代码，显式路径无法验证残留清理。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，Phase109GenericRealLaunchCandidate.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出依赖注入范围。

    def _base_report(self, phase108_report: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，构造 Phase109 通用基础报告；如果没有这段函数，默认关闭和启用路径会重复拼接大量字段。
        uses_phase108 = bool(phase108_report.get("model") == PHASE108_GENERIC_APP_DISCOVERY_MODEL and phase108_report.get("dynamic_discovery_used", False))  # 新增代码+Phase109GenericRealLaunchCandidate：确认来源是 Phase108 动态发现；如果没有这行代码，硬编码目标可能冒充通用发现。
        return {"marker": PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_MARKER, "ok_token": PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_OK_TOKEN, "model": PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_MODEL, "canonical_target": str(phase108_report.get("canonical_target", "")), "generic_real_launch_candidate_ready": False, "uses_phase108_generic_discovery": uses_phase108, "hardcoded_app_whitelist_required": bool(phase108_report.get("hardcoded_app_whitelist_required", True)), "per_app_patch_required": bool(phase108_report.get("per_app_patch_required", True)), "safe_start_process_plan": bool(phase108_report.get("safe_start_process_plan", False)), "high_risk_refused": bool(phase108_report.get("high_risk_refused", False)), "real_launch_default_disabled": PHASE109_REAL_LAUNCH_DEFAULT_DISABLED, "default_off_backend_not_called": True, "backend_launch_reaches_launcher": False, "recording_backend_reaches_launcher": False, "process_identity_model_ready": True, "window_identity_model_ready": True, "cleanup_model_ready": True, "process_identity_verified": False, "window_identity_verified": False, "target_identity_verified": False, "visible_window_verified": False, "cleanup_completed": False, "verified_window_cleanup_completed": False, "residual_process_check_completed": False, "residual_owned_process": False, "real_desktop_touched": False, "uncontrolled_actions_expanded": PHASE109_UNCONTROLLED_ACTIONS_EXPANDED, "phase108_discovery_report": dict(phase108_report)}  # 新增代码+Phase109GenericRealLaunchCandidate：返回公共字段；如果没有这行代码，CLI、测试和交互入口会拿到不一致事实。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，_base_report 到此结束；如果没有这个边界说明，初学者不容易看出基础报告范围。

    def prepare(self, raw_target: Any | None = None, candidates: list[dict[str, Any]] | None = None, generic_report: dict[str, Any] | None = None, enable_real_launch: bool = False) -> dict[str, Any]:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，准备通用真实启动候选；如果没有这段函数，交互层无法从任意 app 发现结果生成候选模型。
        phase108_report = dict(generic_report) if isinstance(generic_report, dict) else resolve_generic_app_launch_target(raw_target or "", candidates=candidates)  # 新增代码+Phase109GenericRealLaunchCandidate：优先复用交互层已有 Phase108 报告，否则按目标重新发现；如果没有这行代码，Phase109 会和 Phase108 事实分裂。
        base_report = self._base_report(phase108_report)  # 新增代码+Phase109GenericRealLaunchCandidate：生成公共报告字段；如果没有这行代码，后续分支会重复且容易漏字段。
        candidate_ready = bool(phase108_report.get("passed", False) and base_report["uses_phase108_generic_discovery"] and base_report["safe_start_process_plan"] and not base_report["high_risk_refused"] and not base_report["hardcoded_app_whitelist_required"] and not base_report["per_app_patch_required"])  # 新增代码+Phase109GenericRealLaunchCandidate：判断是否可进入通用真实启动候选；如果没有这行代码，高风险或非通用目标可能进入后端。
        if not candidate_ready:  # 新增代码+Phase109GenericRealLaunchCandidate：候选不满足时直接零副作用返回；如果没有这行代码，PowerShell 等目标可能继续进入启动模型。
            base_report["decision"] = "phase108_target_not_generic_real_launch_candidate"  # 新增代码+Phase109GenericRealLaunchCandidate：记录拒绝原因；如果没有这行代码，用户看不出为什么没有进入通用候选。
            base_report["passed"] = False  # 新增代码+Phase109GenericRealLaunchCandidate：标记本候选未通过；如果没有这行代码，高风险拒绝可能被误当成功。
            return base_report  # 新增代码+Phase109GenericRealLaunchCandidate：返回零副作用拒绝报告；如果没有这行代码，拒绝路径可能继续执行后端逻辑。
        if not bool(enable_real_launch):  # 新增代码+Phase109GenericRealLaunchCandidate：默认关闭时不调用任何启动后端；如果没有这行代码，full 模式会默认打开普通应用。
            base_report["decision"] = "generic_real_launch_candidate_default_off"  # 新增代码+Phase109GenericRealLaunchCandidate：记录默认关闭决策；如果没有这行代码，用户不知道这是候选就绪而不是失败。
            base_report["passed"] = True  # 新增代码+Phase109GenericRealLaunchCandidate：默认关闭候选合同通过；如果没有这行代码，安全默认路径无法验收。
            base_report["generic_real_launch_candidate_ready"] = True  # 新增代码+Phase109GenericRealLaunchCandidate：标记候选已经准备好；如果没有这行代码，输出会像仍停在 Phase108。
            return base_report  # 新增代码+Phase109GenericRealLaunchCandidate：返回默认关闭报告；如果没有这行代码，默认路径会错误进入后端。
        launch_result = dict(self.launch_backend.launch(phase108_report))  # 新增代码+Phase109GenericRealLaunchCandidate：显式启用时把安全发现报告送到后端；如果没有这行代码，最后一跳永远没有桥接证据。
        window_result = dict(self.window_probe.wait_for_verified_window(launch_result, phase108_report))  # 新增代码+Phase109GenericRealLaunchCandidate：验证启动结果对应的窗口身份；如果没有这行代码，后续可能操作错误窗口。
        cleanup_result = dict(self.cleanup_manager.cleanup(launch_result, window_result))  # 新增代码+Phase109GenericRealLaunchCandidate：清理本候选拥有的进程和窗口；如果没有这行代码，真实启动模型没有收尾闭环。
        backend_reaches = bool(launch_result.get("backend_launch_performed", False) and launch_result.get("ok", False))  # 新增代码+Phase109GenericRealLaunchCandidate：判断后端是否收到并处理启动请求；如果没有这行代码，桥接成功不可见。
        process_identity_verified = bool(launch_result.get("process_identity_verified", False))  # 新增代码+Phase109GenericRealLaunchCandidate：读取进程身份验证结果；如果没有这行代码，进程身份字段不会上浮。
        window_identity_verified = bool(window_result.get("window_identity_verified", False))  # 新增代码+Phase109GenericRealLaunchCandidate：读取窗口身份验证结果；如果没有这行代码，窗口身份字段不会上浮。
        cleanup_completed = bool(cleanup_result.get("cleanup_completed", False))  # 新增代码+Phase109GenericRealLaunchCandidate：读取清理完成结果；如果没有这行代码，收尾状态无法参与通过条件。
        real_desktop_touched = bool(launch_result.get("real_desktop_touched", False) or window_result.get("real_desktop_touched", False) or cleanup_result.get("real_desktop_touched", False))  # 新增代码+Phase109GenericRealLaunchCandidate：汇总是否触碰真实桌面；如果没有这行代码，记录型合同可能过度承诺安全。
        base_report.update({"decision": "generic_real_launch_candidate_recording_backend_verified", "passed": bool(backend_reaches and process_identity_verified and window_identity_verified and cleanup_completed and cleanup_result.get("residual_process_check_completed", False) and not cleanup_result.get("residual_owned_process", True) and not real_desktop_touched), "generic_real_launch_candidate_ready": True, "default_off_backend_not_called": False, "backend_launch_reaches_launcher": backend_reaches, "recording_backend_reaches_launcher": backend_reaches, "process_identity_verified": process_identity_verified, "window_identity_verified": window_identity_verified, "target_identity_verified": bool(window_result.get("target_identity_verified", False)), "visible_window_verified": bool(window_result.get("visible_window_verified", False)), "cleanup_completed": cleanup_completed, "verified_window_cleanup_completed": bool(cleanup_result.get("verified_window_cleanup_completed", False)), "residual_process_check_completed": bool(cleanup_result.get("residual_process_check_completed", False)), "residual_owned_process": bool(cleanup_result.get("residual_owned_process", False)), "real_desktop_touched": real_desktop_touched, "launch_result": launch_result, "window_result": window_result, "cleanup_result": cleanup_result})  # 新增代码+Phase109GenericRealLaunchCandidate：合并显式记录路径报告；如果没有这行代码，合同无法证明身份验证和清理模型已经串起来。
        return base_report  # 新增代码+Phase109GenericRealLaunchCandidate：返回显式记录路径报告；如果没有这行代码，调用方拿不到 Phase109 候选结果。
    # 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，Phase109GenericRealLaunchCandidate.prepare 到此结束；如果没有这个边界说明，初学者不容易看出候选准备范围。
# 新增代码+Phase109GenericRealLaunchCandidate：类段结束，Phase109GenericRealLaunchCandidate 到此结束；如果没有这个边界说明，初学者不容易看出编排器范围。


def prepare_phase109_generic_real_launch_candidate(raw_target: Any | None = None, candidates: list[dict[str, Any]] | None = None, generic_report: dict[str, Any] | None = None, enable_real_launch: bool = False, launch_backend: Any | None = None, window_probe: Any | None = None, cleanup_manager: Any | None = None) -> dict[str, Any]:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，提供轻量函数入口；如果没有这段函数，交互层必须手动创建类实例。
    candidate = Phase109GenericRealLaunchCandidate(launch_backend=launch_backend, window_probe=window_probe, cleanup_manager=cleanup_manager)  # 新增代码+Phase109GenericRealLaunchCandidate：创建通用候选编排器；如果没有这行代码，函数入口没有执行主体。
    return candidate.prepare(raw_target=raw_target, candidates=candidates, generic_report=generic_report, enable_real_launch=enable_real_launch)  # 新增代码+Phase109GenericRealLaunchCandidate：返回候选准备报告；如果没有这行代码，调用方无法得到 Phase109 事实。
# 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，prepare_phase109_generic_real_launch_candidate 到此结束；如果没有这个边界说明，初学者不容易看出函数入口范围。


def run_phase109_generic_real_launch_candidate_contract() -> dict[str, Any]:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，运行 Phase109 总合同；如果没有这段函数，单元测试和真实终端没有统一验收入口。
    ordinary_candidates = [{"display_name": "Obsidian", "executable": "Obsidian.exe", "source": "injected_start_menu", "installed_app_verified": True}]  # 新增代码+Phase109GenericRealLaunchCandidate：注入普通应用候选保持测试稳定；如果没有这行代码，测试会依赖本机是否安装 Obsidian。
    high_risk_candidates = [{"display_name": "Windows PowerShell", "executable": "powershell.exe", "source": "injected_start_menu", "installed_app_verified": True}]  # 新增代码+Phase109GenericRealLaunchCandidate：注入高风险候选验证拒绝路径；如果没有这行代码，PowerShell 风险只测输入不测发现结果。
    default_backend = Phase109RecordingGenericLaunchBackend()  # 新增代码+Phase109GenericRealLaunchCandidate：创建默认关闭路径后端记录器；如果没有这行代码，无法证明默认关闭没有调用后端。
    default_off = prepare_phase109_generic_real_launch_candidate("Obsidian", candidates=ordinary_candidates, enable_real_launch=False, launch_backend=default_backend)  # 新增代码+Phase109GenericRealLaunchCandidate：运行默认关闭候选；如果没有这行代码，安全默认值没有证据。
    enabled_backend = Phase109RecordingGenericLaunchBackend()  # 新增代码+Phase109GenericRealLaunchCandidate：创建显式启用记录后端；如果没有这行代码，最后一跳桥接没有可检查对象。
    enabled = prepare_phase109_generic_real_launch_candidate("Obsidian", candidates=ordinary_candidates, enable_real_launch=True, launch_backend=enabled_backend)  # 新增代码+Phase109GenericRealLaunchCandidate：运行显式记录型启动路径；如果没有这行代码，身份验证和清理模型不会被执行。
    unsafe_backend = Phase109RecordingGenericLaunchBackend()  # 新增代码+Phase109GenericRealLaunchCandidate：创建高风险路径后端记录器；如果没有这行代码，无法证明拒绝前没有调用后端。
    unsafe = prepare_phase109_generic_real_launch_candidate("PowerShell", candidates=high_risk_candidates, enable_real_launch=True, launch_backend=unsafe_backend)  # 新增代码+Phase109GenericRealLaunchCandidate：运行高风险目标拒绝样本；如果没有这行代码，通用候选可能放行系统终端。
    default_off_backend_not_called = bool(default_off.get("passed", False) and len(default_backend.launches) == 0 and not default_off.get("real_desktop_touched", False))  # 新增代码+Phase109GenericRealLaunchCandidate：汇总默认关闭零后端调用；如果没有这行代码，默认安全无法被量化。
    recording_backend_reaches_launcher = bool(enabled.get("recording_backend_reaches_launcher", False) and len(enabled_backend.launches) == 1)  # 新增代码+Phase109GenericRealLaunchCandidate：汇总记录型后端是否收到启动请求；如果没有这行代码，最后一跳是否接通不可见。
    high_risk_refused = bool(unsafe.get("high_risk_refused", False) and len(unsafe_backend.launches) == 0 and not unsafe.get("real_desktop_touched", False))  # 新增代码+Phase109GenericRealLaunchCandidate：汇总高风险拒绝零副作用；如果没有这行代码，PowerShell 拦截没有证据。
    real_desktop_touched = bool(default_off.get("real_desktop_touched", False) or enabled.get("real_desktop_touched", False) or unsafe.get("real_desktop_touched", False))  # 新增代码+Phase109GenericRealLaunchCandidate：汇总整个合同是否触碰真实桌面；如果没有这行代码，自动验收可能误打开应用也不自知。
    passed = bool(default_off_backend_not_called and recording_backend_reaches_launcher and enabled.get("process_identity_verified", False) and enabled.get("window_identity_verified", False) and enabled.get("target_identity_verified", False) and enabled.get("cleanup_completed", False) and enabled.get("verified_window_cleanup_completed", False) and enabled.get("residual_process_check_completed", False) and not enabled.get("residual_owned_process", True) and high_risk_refused and not real_desktop_touched and not PHASE109_UNCONTROLLED_ACTIONS_EXPANDED)  # 新增代码+Phase109GenericRealLaunchCandidate：计算总合同通过条件；如果没有这行代码，main 无法用退出码表达失败。
    return {"marker": PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_MARKER, "ok_token": PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_OK_TOKEN, "model": PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_MODEL, "passed": passed, "generic_real_launch_candidate_ready": bool(default_off.get("generic_real_launch_candidate_ready", False) and enabled.get("generic_real_launch_candidate_ready", False)), "uses_phase108_generic_discovery": bool(default_off.get("uses_phase108_generic_discovery", False) and enabled.get("uses_phase108_generic_discovery", False)), "hardcoded_app_whitelist_required": False, "per_app_patch_required": False, "real_launch_default_disabled": PHASE109_REAL_LAUNCH_DEFAULT_DISABLED, "default_off_backend_not_called": default_off_backend_not_called, "recording_backend_reaches_launcher": recording_backend_reaches_launcher, "backend_launch_reaches_launcher": recording_backend_reaches_launcher, "process_identity_model_ready": True, "window_identity_model_ready": True, "cleanup_model_ready": True, "process_identity_verified": bool(enabled.get("process_identity_verified", False)), "window_identity_verified": bool(enabled.get("window_identity_verified", False)), "target_identity_verified": bool(enabled.get("target_identity_verified", False)), "visible_window_verified": bool(enabled.get("visible_window_verified", False)), "cleanup_completed": bool(enabled.get("cleanup_completed", False)), "verified_window_cleanup_completed": bool(enabled.get("verified_window_cleanup_completed", False)), "residual_process_check_completed": bool(enabled.get("residual_process_check_completed", False)), "residual_owned_process": bool(enabled.get("residual_owned_process", False)), "high_risk_refused": high_risk_refused, "real_desktop_touched": real_desktop_touched, "uncontrolled_actions_expanded": PHASE109_UNCONTROLLED_ACTIONS_EXPANDED, "default_off_report": default_off, "enabled_report": enabled, "unsafe_report": unsafe}  # 新增代码+Phase109GenericRealLaunchCandidate：返回总合同报告；如果没有这行代码，测试和真实终端无法共享同一事实。
# 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，run_phase109_generic_real_launch_candidate_contract 到此结束；如果没有这个边界说明，初学者不容易看出总合同范围。


def phase109_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，把 Phase109 报告转成稳定 token 行；如果没有这段函数，真实可见终端验收只能解析复杂 JSON。
    ok_token = f" {PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_OK_TOKEN}" if bool(report.get("passed", False)) else ""  # 新增代码+Phase109GenericRealLaunchCandidate：只在报告通过时追加 OK；如果没有这行代码，高风险拒绝子报告也可能被误判成功。
    return f"{PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_MARKER}{ok_token} generic_real_launch_candidate_ready={_phase109_bool_token(report.get('generic_real_launch_candidate_ready', False))} uses_phase108_generic_discovery={_phase109_bool_token(report.get('uses_phase108_generic_discovery', False))} hardcoded_app_whitelist_required={_phase109_bool_token(report.get('hardcoded_app_whitelist_required', True))} per_app_patch_required={_phase109_bool_token(report.get('per_app_patch_required', True))} real_launch_default_disabled={_phase109_bool_token(report.get('real_launch_default_disabled', True))} default_off_backend_not_called={_phase109_bool_token(report.get('default_off_backend_not_called', False))} recording_backend_reaches_launcher={_phase109_bool_token(report.get('recording_backend_reaches_launcher', False))} process_identity_model_ready={_phase109_bool_token(report.get('process_identity_model_ready', False))} window_identity_model_ready={_phase109_bool_token(report.get('window_identity_model_ready', False))} cleanup_model_ready={_phase109_bool_token(report.get('cleanup_model_ready', False))} process_identity_verified={_phase109_bool_token(report.get('process_identity_verified', False))} window_identity_verified={_phase109_bool_token(report.get('window_identity_verified', False))} target_identity_verified={_phase109_bool_token(report.get('target_identity_verified', False))} cleanup_completed={_phase109_bool_token(report.get('cleanup_completed', False))} residual_process_check_completed={_phase109_bool_token(report.get('residual_process_check_completed', False))} residual_owned_process={_phase109_bool_token(report.get('residual_owned_process', False))} high_risk_refused={_phase109_bool_token(report.get('high_risk_refused', False))} real_desktop_touched={_phase109_bool_token(report.get('real_desktop_touched', False))} uncontrolled_actions_expanded={_phase109_bool_token(report.get('uncontrolled_actions_expanded', False))}"  # 新增代码+Phase109GenericRealLaunchCandidate：返回固定顺序 token；如果没有这行代码，单元测试和真实终端会因输出漂移不稳定。
# 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，phase109_cli_line 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 输出范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+Phase109GenericRealLaunchCandidate：函数段开始，提供命令行自检入口；如果没有这段函数，真实终端无法直接运行 Phase109 合同。
    _ = argv  # 新增代码+Phase109GenericRealLaunchCandidate：保留 argv 扩展位；如果没有这行代码，读者可能误以为参数被遗漏。
    report = run_phase109_generic_real_launch_candidate_contract()  # 新增代码+Phase109GenericRealLaunchCandidate：运行无真实桌面副作用的总合同；如果没有这行代码，CLI 不会产生验收事实。
    print(phase109_cli_line(report))  # 新增代码+Phase109GenericRealLaunchCandidate：打印稳定 token 行；如果没有这行代码，验收脚本无法快速匹配成功条件。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase109GenericRealLaunchCandidate：打印完整 JSON 供失败排查；如果没有这行代码，调试只能看短字段。
    print(PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_MARKER)  # 新增代码+Phase109GenericRealLaunchCandidate：单独打印 ready marker 便于人工观察；如果没有这行代码，可见终端里不容易发现阶段标识。
    return 0 if bool(report.get("passed", False)) else 1  # 新增代码+Phase109GenericRealLaunchCandidate：按合同结果返回退出码；如果没有这行代码，失败也可能被自动化当成功。
# 新增代码+Phase109GenericRealLaunchCandidate：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出命令入口范围。


__all__ = ["PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_MARKER", "PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_MODEL", "PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_OK_TOKEN", "PHASE109_REAL_LAUNCH_DEFAULT_DISABLED", "PHASE109_UNCONTROLLED_ACTIONS_EXPANDED", "Phase109GenericRealLaunchCandidate", "Phase109RecordingCleanupManager", "Phase109RecordingGenericLaunchBackend", "Phase109RecordingWindowIdentityProbe", "main", "phase109_cli_line", "prepare_phase109_generic_real_launch_candidate", "run_phase109_generic_real_launch_candidate_contract"]  # 新增代码+Phase109GenericRealLaunchCandidate：限定公开导出名称；如果没有这行代码，通配导入会暴露内部 helper。


if __name__ == "__main__":  # 新增代码+Phase109GenericRealLaunchCandidate：文件入口段开始，允许直接运行模块；如果没有这行代码，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+Phase109GenericRealLaunchCandidate：用 main 的返回码退出；如果没有这行代码，命令行状态不明确。
# 新增代码+Phase109GenericRealLaunchCandidate：文件入口段结束，直接运行模块到此结束；如果没有这个边界说明，初学者不容易看出入口范围。
