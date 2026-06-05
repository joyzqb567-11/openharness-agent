"""Generic Windows application launch backend for Computer Use full maturity."""  # 新增代码+GenericLaunchBackendMaturity：说明本模块负责普通应用的通用启动后端；如果没有这一行，读者容易把这里误解成逐应用 controller。
from __future__ import annotations  # 新增代码+GenericLaunchBackendMaturity：启用延迟类型注解解析；如果没有这一行，类之间互相引用时更容易出现导入顺序问题。

import json  # 新增代码+GenericLaunchBackendMaturity：导入 JSON 工具用于 CLI 输出完整报告；如果没有这一行，失败排查只能看短 token。
import sys  # 新增代码+GenericLaunchBackendMaturity：导入 sys 用于生产后端判断当前平台；如果没有这一行，非 Windows 环境可能误走真实启动分支。
from dataclasses import dataclass, field  # 新增代码+GenericLaunchBackendMaturity：导入 dataclass 和 field 表达结构化请求结果；如果没有这一行，请求和结果会退回松散字典不利于学习。
from typing import Any  # 新增代码+GenericLaunchBackendMaturity：导入 Any 表示 JSON 风格动态字段；如果没有这一行，报告接口对代码小白不够清楚。

PHASE110_GENERIC_LAUNCH_BACKEND_MARKER = "PHASE110_GENERIC_LAUNCH_BACKEND_READY"  # 新增代码+GenericLaunchBackendMaturity：定义 Task 2 通用启动后端 ready marker；如果没有这一行，真实终端和矩阵无法稳定定位该能力。
PHASE110_GENERIC_LAUNCH_BACKEND_OK_TOKEN = "PHASE110_GENERIC_LAUNCH_BACKEND_OK"  # 新增代码+GenericLaunchBackendMaturity：定义 Task 2 通用启动后端 OK token；如果没有这一行，成功输出和普通日志不容易区分。
PHASE110_GENERIC_LAUNCH_BACKEND_MODEL = "phase110_generic_launch_backend"  # 新增代码+GenericLaunchBackendMaturity：定义报告模型名；如果没有这一行，后续成熟矩阵无法区分通用启动后端版本。
PHASE110_REAL_LAUNCH_DEFAULT_DISABLED = True  # 新增代码+GenericLaunchBackendMaturity：声明真实启动默认关闭；如果没有这一行，用户可能误以为 full 模式默认打开任意应用。
PHASE110_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+GenericLaunchBackendMaturity：声明本任务没有扩张无边界动作；如果没有这一行，full 模式可能被误读成无限控制。

@dataclass(frozen=True)  # 新增代码+GenericLaunchBackendMaturity：使用不可变 dataclass 描述启动请求；如果没有这一行，请求字段容易在后端中途被误改。
class GenericLaunchRequest:  # 新增代码+GenericLaunchBackendMaturity：类段开始，表示进入通用启动后端的唯一请求形状；如果没有这个类，后端可能重新接收 shell 字符串。
    canonical_target: str  # 新增代码+GenericLaunchBackendMaturity：保存规范化目标名；如果没有这一行，窗口身份绑定无法知道用户原本要启动哪个普通应用。
    executable: str  # 新增代码+GenericLaunchBackendMaturity：保存可执行程序名或路径；如果没有这一行，后端没有明确启动目标。
    arguments: tuple[str, ...] = ()  # 新增代码+GenericLaunchBackendMaturity：保存 argv 参数元组；如果没有这一行，参数可能被拼成高风险 shell 字符串。
    launch_plan: dict[str, Any] = field(default_factory=dict)  # 新增代码+GenericLaunchBackendMaturity：保存 Phase108/Phase69 安全计划副本；如果没有这一行，后端无法复核无 shell、无提权、无系统修改。
    raw_phase108_report: dict[str, Any] = field(default_factory=dict)  # 新增代码+GenericLaunchBackendMaturity：保存原始发现报告副本；如果没有这一行，失败排查无法追溯候选来源。
    high_risk_refused: bool = False  # 新增代码+GenericLaunchBackendMaturity：保存高风险拒绝标志；如果没有这一行，PowerShell 等目标可能绕过后端复核。
    real_launch_authorized: bool = False  # 新增代码+GenericLaunchBackendMaturity：保存是否经过显式真实启动授权；如果没有这一行，生产后端无法阻止默认启动。
    request_id: str = "phase110-generic-launch-request"  # 新增代码+GenericLaunchBackendMaturity：保存请求 id 便于审计；如果没有这一行，多次启动记录不容易追踪。

    def argv(self) -> list[str]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，把请求转成 argv 数组；如果没有这个函数，调用方可能重复拼接命令。
        return [self.executable, *list(self.arguments)]  # 新增代码+GenericLaunchBackendMaturity：返回可直接交给 Popen 的无 shell 参数列表；如果没有这一行，后端可能退回 shell 字符串。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，GenericLaunchRequest.argv 到此结束；如果没有这个边界说明，代码小白不容易看出 argv 生成范围。

    def to_report(self) -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，把请求转成可序列化报告；如果没有这个函数，测试和 CLI 无法稳定检查请求形状。
        return {"canonical_target": self.canonical_target, "executable": self.executable, "arguments": list(self.arguments), "argv": self.argv(), "command_shape": "argv_no_shell", "uses_shell_string": False, "high_risk_refused": self.high_risk_refused, "real_launch_authorized": self.real_launch_authorized, "request_id": self.request_id, "launch_plan": dict(self.launch_plan)}  # 新增代码+GenericLaunchBackendMaturity：返回请求摘要；如果没有这一行，后端审计无法证明自己收到的是 argv 而不是 shell 字符串。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，GenericLaunchRequest.to_report 到此结束；如果没有这个边界说明，读者不容易看出请求报告范围。
# 新增代码+GenericLaunchBackendMaturity：类段结束，GenericLaunchRequest 到此结束；如果没有这个边界说明，代码小白不容易看出启动请求结构范围。

@dataclass(frozen=True)  # 新增代码+GenericLaunchBackendMaturity：使用不可变 dataclass 描述启动结果；如果没有这一行，结果字段可能被调用方意外改写。
class GenericLaunchResult:  # 新增代码+GenericLaunchBackendMaturity：类段开始，表示通用启动后端的统一返回形状；如果没有这个类，失败和成功结果会继续散成不同字典。
    ok: bool  # 新增代码+GenericLaunchBackendMaturity：保存后端是否成功处理；如果没有这一行，上层无法区分成功和失败。
    decision: str  # 新增代码+GenericLaunchBackendMaturity：保存稳定决策码；如果没有这一行，调用方无法按原因分类恢复。
    backend: str  # 新增代码+GenericLaunchBackendMaturity：保存后端名称；如果没有这一行，报告无法区分 recording 和 production。
    process_started: bool = False  # 新增代码+GenericLaunchBackendMaturity：保存是否启动了进程；如果没有这一行，cleanup 不知道是否需要处理进程。
    process_id: int = 0  # 新增代码+GenericLaunchBackendMaturity：保存进程 id；如果没有这一行，窗口身份绑定没有 pid 基准。
    process_executable: str = ""  # 新增代码+GenericLaunchBackendMaturity：保存进程可执行名；如果没有这一行，进程身份无法和目标应用比对。
    argv: tuple[str, ...] = ()  # 新增代码+GenericLaunchBackendMaturity：保存后端使用的 argv；如果没有这一行，无法审计是否绕过 shell。
    real_desktop_touched: bool = False  # 新增代码+GenericLaunchBackendMaturity：保存是否触碰真实桌面；如果没有这一行，记录后端和生产后端会被混淆。
    cleanup_registered: bool = False  # 新增代码+GenericLaunchBackendMaturity：保存是否登记清理责任；如果没有这一行，stop/abort 无法确认是否有收尾句柄。
    owned_process_registered: bool = False  # 新增代码+GenericLaunchBackendMaturity：保存进程是否登记为本 agent 自有；如果没有这一行，不能证明不会误关用户原有窗口。
    failure_reason: str = ""  # 新增代码+GenericLaunchBackendMaturity：保存结构化失败原因；如果没有这一行，启动失败会变成难懂异常。

    def to_report(self) -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，把结果转成 JSON 风格报告；如果没有这个函数，CLI 和测试需要手动理解 dataclass。
        return {"ok": self.ok, "decision": self.decision, "backend": self.backend, "backend_launch_performed": bool(self.process_started or self.ok), "backend_launch_reaches_launcher": bool(self.ok), "process_started": self.process_started, "process_id": self.process_id, "process_executable": self.process_executable, "process_identity_verified": bool(self.process_started and self.process_id > 0 and self.process_executable), "argv": list(self.argv), "command_shape": "argv_no_shell", "uses_shell_string": False, "real_desktop_touched": self.real_desktop_touched, "cleanup_registered": self.cleanup_registered, "owned_process_registered": self.owned_process_registered, "failure_reason": self.failure_reason, "low_level_event_count": 0}  # 新增代码+GenericLaunchBackendMaturity：返回统一结果字段；如果没有这一行，上层候选和成熟矩阵无法共享同一事实。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，GenericLaunchResult.to_report 到此结束；如果没有这个边界说明，读者不容易看出结果报告范围。
# 新增代码+GenericLaunchBackendMaturity：类段结束，GenericLaunchResult 到此结束；如果没有这个边界说明，代码小白不容易看出启动结果结构范围。

class Phase110OwnedProcessRegistry:  # 新增代码+GenericLaunchBackendMaturity：类段开始，记录本 agent 启动的自有进程；如果没有这个类，cleanup 无法区分 agent 进程和用户原本打开的进程。
    def __init__(self) -> None:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，初始化自有进程登记表；如果没有这个函数，登记记录没有保存位置。
        self.owned_processes: list[dict[str, Any]] = []  # 新增代码+GenericLaunchBackendMaturity：保存可序列化的自有进程记录；如果没有这一行，测试无法验证 process ownership。
        self._process_objects: list[Any] = []  # 新增代码+GenericLaunchBackendMaturity：保存生产后端真实进程对象供后续清理扩展；如果没有这一行，未来 cleanup 只能靠 pid 猜测。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，Phase110OwnedProcessRegistry.__init__ 到此结束；如果没有这个边界说明，读者不容易看出登记表初始化范围。

    def register(self, process_id: int, executable: str, argv: list[str], process_object: Any | None = None) -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，登记一次本 agent 自有进程；如果没有这个函数，启动后无法生成 cleanup 责任记录。
        record = {"process_id": int(process_id), "process_executable": str(executable or ""), "argv": list(argv), "owned_by_agent": True, "cleanup_registered": True}  # 新增代码+GenericLaunchBackendMaturity：构造可审计登记记录；如果没有这一行，报告无法证明只管理本次启动的进程。
        self.owned_processes.append(record)  # 新增代码+GenericLaunchBackendMaturity：保存登记记录；如果没有这一行，后续 residual/cleanup 检查没有自有资源清单。
        if process_object is not None:  # 新增代码+GenericLaunchBackendMaturity：只有真实进程对象存在时才保存；如果没有这一行，记录型后端会把空对象也塞进清理列表。
            self._process_objects.append(process_object)  # 新增代码+GenericLaunchBackendMaturity：保存真实进程对象供未来 cleanup 使用；如果没有这一行，生产后端无法可靠终止自己启动的进程。
        return record  # 新增代码+GenericLaunchBackendMaturity：返回登记记录给启动结果引用；如果没有这一行，调用方拿不到 cleanup_registered 字段。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，Phase110OwnedProcessRegistry.register 到此结束；如果没有这个边界说明，代码小白不容易看出登记范围。
# 新增代码+GenericLaunchBackendMaturity：类段结束，Phase110OwnedProcessRegistry 到此结束；如果没有这个边界说明，读者不容易看出自有资源登记范围。

def _phase110_bool_token(value: Any) -> str:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，把布尔值转成稳定小写 token；如果没有这个函数，CLI 输出可能因 True/False 大小写漂移失败。
    return "true" if bool(value) else "false"  # 新增代码+GenericLaunchBackendMaturity：返回 true 或 false 文本；如果没有这一行，真实终端验收不容易稳定匹配。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，_phase110_bool_token 到此结束；如果没有这个边界说明，读者不容易看出布尔格式化范围。

def phase110_contract_safe_phase108_report() -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，构造稳定的普通应用安全发现样本；如果没有这个函数，测试会依赖用户本机是否安装某个应用。
    plan = {"safe_to_launch": True, "launch_verb": "Start-Process", "executable": "Obsidian.exe", "arguments": ["--phase110-safe-sample"], "changes_registry": False, "changes_system_settings": False, "requires_admin": False, "uses_shell_string": False, "actions_expanded": False}  # 新增代码+GenericLaunchBackendMaturity：构造无 shell、无提权、无系统修改的启动计划；如果没有这一行，后端没有安全正例。
    return {"passed": True, "canonical_target": "obsidian", "best_candidate_executable": "Obsidian.exe", "safe_start_process_plan": True, "high_risk_refused": False, "hardcoded_app_whitelist_required": False, "per_app_patch_required": False, "launch_plan": plan}  # 新增代码+GenericLaunchBackendMaturity：返回 Phase108 形状的安全报告；如果没有这一行，Task 2 测试不能复用已有发现模型。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，phase110_contract_safe_phase108_report 到此结束；如果没有这个边界说明，读者不容易看出安全样本范围。

def phase110_contract_unsafe_phase108_report() -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，构造稳定的高风险拒绝样本；如果没有这个函数，危险拒绝只能依赖真实 PowerShell 发现结果。
    plan = {"safe_to_launch": False, "launch_verb": "Start-Process", "executable": "powershell.exe", "arguments": ["-NoProfile"], "changes_registry": False, "changes_system_settings": False, "requires_admin": False, "uses_shell_string": True, "actions_expanded": False, "refusal_reason": "high_risk_target_refused"}  # 新增代码+GenericLaunchBackendMaturity：构造带 shell 风险和高风险目标的计划；如果没有这一行，后端前置拒绝没有危险样本。
    return {"passed": False, "canonical_target": "powershell", "best_candidate_executable": "powershell.exe", "safe_start_process_plan": False, "high_risk_refused": True, "hardcoded_app_whitelist_required": False, "per_app_patch_required": False, "launch_plan": plan}  # 新增代码+GenericLaunchBackendMaturity：返回 Phase108 形状的危险报告；如果没有这一行，测试无法证明拒绝发生在后端调用前。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，phase110_contract_unsafe_phase108_report 到此结束；如果没有这个边界说明，读者不容易看出危险样本范围。

def build_generic_launch_request(phase108_report: GenericLaunchRequest | dict[str, Any], real_launch_authorized: bool = False, request_id: str = "phase110-generic-launch-request") -> GenericLaunchRequest:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，把 Phase108 报告转换成唯一启动请求；如果没有这个函数，后端会直接吃松散字典。
    if isinstance(phase108_report, GenericLaunchRequest):  # 新增代码+GenericLaunchBackendMaturity：如果已经是结构化请求就直接处理；如果没有这一行，二次调用会丢失请求内的授权和 argv。
        return phase108_report  # 新增代码+GenericLaunchBackendMaturity：返回原请求对象；如果没有这一行，已有请求会被错误重建。
    report = dict(phase108_report or {})  # 新增代码+GenericLaunchBackendMaturity：复制 Phase108 报告避免污染调用方对象；如果没有这一行，后续规范化可能改动原始报告。
    plan = dict(report.get("launch_plan", {}) or {})  # 新增代码+GenericLaunchBackendMaturity：读取安全启动计划副本；如果没有这一行，后端无法复核安全字段。
    executable = str(plan.get("executable") or report.get("best_candidate_executable") or report.get("canonical_target") or "").strip()  # 新增代码+GenericLaunchBackendMaturity：确定可执行目标；如果没有这一行，argv 第一个元素会缺失。
    arguments = tuple(str(argument) for argument in list(plan.get("arguments", []) or []))  # 新增代码+GenericLaunchBackendMaturity：把参数规范成字符串元组；如果没有这一行，Popen 可能收到坏类型或被拼成 shell 字符串。
    canonical_target = str(report.get("canonical_target") or executable).strip().lower()  # 新增代码+GenericLaunchBackendMaturity：确定规范目标名；如果没有这一行，后续窗口身份绑定没有稳定目标。
    authorized = bool(real_launch_authorized or report.get("real_launch_authorized", False))  # 新增代码+GenericLaunchBackendMaturity：合并显式授权标志；如果没有这一行，生产后端无法确认 full gate 是否放行。
    return GenericLaunchRequest(canonical_target=canonical_target, executable=executable, arguments=arguments, launch_plan=plan, raw_phase108_report=report, high_risk_refused=bool(report.get("high_risk_refused", False)), real_launch_authorized=authorized, request_id=request_id)  # 新增代码+GenericLaunchBackendMaturity：返回结构化请求；如果没有这一行，后端无法统一处理 Phase108 和测试输入。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，build_generic_launch_request 到此结束；如果没有这个边界说明，代码小白不容易看出请求构造范围。

def phase110_safe_launch_request(request: GenericLaunchRequest) -> bool:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，复核请求是否满足真实启动安全条件；如果没有这个函数，危险计划可能进入生产后端。
    plan = dict(request.launch_plan or {})  # 新增代码+GenericLaunchBackendMaturity：读取启动计划副本；如果没有这一行，下面的安全字段没有来源。
    return bool(request.executable and request.argv() and not request.high_risk_refused and plan.get("safe_to_launch") and plan.get("launch_verb") == "Start-Process" and not plan.get("changes_registry") and not plan.get("changes_system_settings") and not plan.get("requires_admin") and not plan.get("uses_shell_string") and not plan.get("actions_expanded"))  # 新增代码+GenericLaunchBackendMaturity：要求无 shell、无提权、无系统修改、非高风险；如果没有这一行，full 模式可能放行危险启动。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，phase110_safe_launch_request 到此结束；如果没有这个边界说明，读者不容易看出安全复核范围。

def _phase110_refusal_report(request: GenericLaunchRequest, decision: str, failure_reason: str) -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，构造统一拒绝报告；如果没有这个函数，默认关闭、危险拒绝和失败路径字段会不一致。
    base = request.to_report()  # 新增代码+GenericLaunchBackendMaturity：读取请求摘要；如果没有这一行，拒绝报告无法展示 argv 和计划。
    base.update({"marker": PHASE110_GENERIC_LAUNCH_BACKEND_MARKER, "ok_token": PHASE110_GENERIC_LAUNCH_BACKEND_OK_TOKEN, "model": PHASE110_GENERIC_LAUNCH_BACKEND_MODEL, "ok": False, "passed": False, "decision": decision, "backend_launch_reaches_launcher": False, "backend_launch_performed": False, "process_started": False, "process_id": 0, "process_executable": request.executable, "process_identity_verified": False, "cleanup_registered": False, "owned_process_registered": False, "real_desktop_touched": False, "default_off_backend_not_called": decision == "generic_real_launch_disabled_by_default", "high_risk_refused": bool(request.high_risk_refused), "failure_reason": failure_reason, "uncontrolled_actions_expanded": PHASE110_UNCONTROLLED_ACTIONS_EXPANDED})  # 新增代码+GenericLaunchBackendMaturity：合并拒绝字段；如果没有这一行，调用方无法稳定判断零副作用拒绝。
    return base  # 新增代码+GenericLaunchBackendMaturity：返回拒绝报告；如果没有这一行，调用方拿不到结构化失败信息。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，_phase110_refusal_report 到此结束；如果没有这个边界说明，代码小白不容易看出拒绝报告范围。

class Phase110RecordingGenericLaunchBackend:  # 新增代码+GenericLaunchBackendMaturity：类段开始，定义无真实桌面副作用的记录型通用启动后端；如果没有这个类，自动测试可能需要真的打开用户应用。
    def __init__(self, registry: Phase110OwnedProcessRegistry | None = None) -> None:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，初始化记录型后端；如果没有这个函数，测试无法注入自有进程登记表。
        self.registry = registry if registry is not None else Phase110OwnedProcessRegistry()  # 新增代码+GenericLaunchBackendMaturity：保存或创建自有进程登记表；如果没有这一行，记录型启动无法验证 ownership。
        self.launches: list[dict[str, Any]] = []  # 新增代码+GenericLaunchBackendMaturity：保存收到的请求副本；如果没有这一行，测试无法证明后端调用次数和 argv 形状。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，Phase110RecordingGenericLaunchBackend.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def launch(self, request_like: GenericLaunchRequest | dict[str, Any]) -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，记录一次授权启动请求但不触碰真实桌面；如果没有这个函数，通用后端没有安全替身。
        request = build_generic_launch_request(request_like, real_launch_authorized=True)  # 新增代码+GenericLaunchBackendMaturity：把输入统一成结构化请求；如果没有这一行，Phase109 传来的 Phase108 报告无法复用新后端。
        if not phase110_safe_launch_request(request):  # 新增代码+GenericLaunchBackendMaturity：后端内部再次复核安全计划；如果没有这一行，调用方 bug 可能把危险计划送进后端。
            return _phase110_refusal_report(request, "unsafe_generic_launch_plan_rejected", "unsafe_launch_plan_rejected_by_backend")  # 新增代码+GenericLaunchBackendMaturity：危险请求零副作用拒绝；如果没有这一行，记录后端会误登记危险目标。
        request_report = request.to_report()  # 新增代码+GenericLaunchBackendMaturity：生成请求报告副本；如果没有这一行，launches 不能保存稳定 argv 证据。
        self.launches.append(dict(request_report))  # 新增代码+GenericLaunchBackendMaturity：保存请求副本；如果没有这一行，测试无法确认后端正好被调用一次。
        process_id = 11000 + len(self.launches)  # 新增代码+GenericLaunchBackendMaturity：生成稳定的记录型 pid；如果没有这一行，窗口身份绑定没有模拟进程基准。
        owned_record = self.registry.register(process_id, request.executable, request.argv())  # 新增代码+GenericLaunchBackendMaturity：登记本 agent 自有进程；如果没有这一行，cleanup 责任无法被证明。
        result = GenericLaunchResult(ok=True, decision="generic_launch_recording_backend_started_owned_process", backend="phase110_recording_generic_launch_backend", process_started=True, process_id=process_id, process_executable=request.executable, argv=tuple(request.argv()), real_desktop_touched=False, cleanup_registered=bool(owned_record.get("cleanup_registered")), owned_process_registered=True)  # 新增代码+GenericLaunchBackendMaturity：构造记录型成功结果；如果没有这一行，上层拿不到统一启动摘要。
        report = result.to_report()  # 新增代码+GenericLaunchBackendMaturity：把结果转成报告；如果没有这一行，调用方无法按字典读取字段。
        report.update({"request": request_report, "owned_process_record": owned_record})  # 新增代码+GenericLaunchBackendMaturity：附加请求和登记证据；如果没有这一行，失败排查无法看到 argv 和 cleanup 记录。
        return report  # 新增代码+GenericLaunchBackendMaturity：返回记录型启动报告；如果没有这一行，Phase109 和测试无法获得结果。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，Phase110RecordingGenericLaunchBackend.launch 到此结束；如果没有这个边界说明，读者不容易看出记录启动范围。
# 新增代码+GenericLaunchBackendMaturity：类段结束，Phase110RecordingGenericLaunchBackend 到此结束；如果没有这个边界说明，代码小白不容易看出记录后端范围。

class Phase110FailingGenericLaunchBackend:  # 新增代码+GenericLaunchBackendMaturity：类段开始，定义可预测失败后端；如果没有这个类，测试只能依赖真实系统异常来覆盖失败路径。
    def __init__(self, failure_reason: str) -> None:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，保存模拟失败原因；如果没有这个函数，失败测试无法指定可读原因。
        self.failure_reason = str(failure_reason or "generic_launch_backend_failed")  # 新增代码+GenericLaunchBackendMaturity：规范失败原因文本；如果没有这一行，空原因会让用户看不懂失败。
        self.launches: list[dict[str, Any]] = []  # 新增代码+GenericLaunchBackendMaturity：保存失败后端收到的请求；如果没有这一行，测试无法确认失败发生在后端内部。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，Phase110FailingGenericLaunchBackend.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def launch(self, request_like: GenericLaunchRequest | dict[str, Any]) -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，返回结构化失败而不抛异常；如果没有这个函数，失败路径可能中断整个 agent。
        request = build_generic_launch_request(request_like, real_launch_authorized=True)  # 新增代码+GenericLaunchBackendMaturity：统一失败请求形状；如果没有这一行，失败报告缺少 argv 和目标。
        self.launches.append(request.to_report())  # 新增代码+GenericLaunchBackendMaturity：记录失败请求；如果没有这一行，后端调用证据会丢失。
        return GenericLaunchResult(ok=False, decision="generic_launch_backend_failed", backend="phase110_failing_generic_launch_backend", process_started=False, process_id=0, process_executable=request.executable, argv=tuple(request.argv()), real_desktop_touched=False, cleanup_registered=False, owned_process_registered=False, failure_reason=self.failure_reason).to_report()  # 新增代码+GenericLaunchBackendMaturity：返回结构化失败结果；如果没有这一行，用户无法知道启动失败原因。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，Phase110FailingGenericLaunchBackend.launch 到此结束；如果没有这个边界说明，读者不容易看出失败后端范围。
# 新增代码+GenericLaunchBackendMaturity：类段结束，Phase110FailingGenericLaunchBackend 到此结束；如果没有这个边界说明，代码小白不容易看出失败后端范围。

class Phase110ProductionGenericLaunchBackend:  # 新增代码+GenericLaunchBackendMaturity：类段开始，定义显式授权后的生产真实启动后端；如果没有这个类，成熟版永远停在记录型候选。
    def __init__(self, registry: Phase110OwnedProcessRegistry | None = None, platform: str | None = None) -> None:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，初始化生产后端依赖；如果没有这个函数，测试无法注入平台和登记表。
        self.registry = registry if registry is not None else Phase110OwnedProcessRegistry()  # 新增代码+GenericLaunchBackendMaturity：保存自有进程登记表；如果没有这一行，真实启动后无法登记 cleanup 责任。
        self.platform = str(platform or sys.platform)  # 新增代码+GenericLaunchBackendMaturity：保存平台名；如果没有这一行，非 Windows 环境无法安全拒绝。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，Phase110ProductionGenericLaunchBackend.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def launch(self, request_like: GenericLaunchRequest | dict[str, Any]) -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，按 argv 形状真实启动普通应用；如果没有这个函数，生产路径没有最后一跳。
        request = build_generic_launch_request(request_like)  # 新增代码+GenericLaunchBackendMaturity：统一请求形状；如果没有这一行，生产后端可能收到松散字典。
        if not request.real_launch_authorized:  # 新增代码+GenericLaunchBackendMaturity：真实启动必须有显式授权；如果没有这一行，默认路径可能直接启动应用。
            return _phase110_refusal_report(request, "generic_real_launch_requires_authorization", "real_launch_not_authorized")  # 新增代码+GenericLaunchBackendMaturity：无授权零副作用拒绝；如果没有这一行，full gate 会被绕过。
        if not self.platform.startswith("win"):  # 新增代码+GenericLaunchBackendMaturity：只允许 Windows 平台真实启动；如果没有这一行，Linux/macOS 测试可能误跑 exe。
            return _phase110_refusal_report(request, "generic_real_launch_non_windows_rejected", "non_windows_platform_rejected")  # 新增代码+GenericLaunchBackendMaturity：非 Windows 返回结构化拒绝；如果没有这一行，平台错误会变成异常。
        if not phase110_safe_launch_request(request):  # 新增代码+GenericLaunchBackendMaturity：生产后端再次复核安全计划；如果没有这一行，调用方 bug 可能触发危险启动。
            return _phase110_refusal_report(request, "unsafe_generic_launch_plan_rejected", "unsafe_launch_plan_rejected_by_backend")  # 新增代码+GenericLaunchBackendMaturity：危险计划零副作用拒绝；如果没有这一行，高风险目标可能进入 Popen。
        try:  # 新增代码+GenericLaunchBackendMaturity：捕获真实启动异常并转成结构化失败；如果没有这一行，启动失败会打断整个 agent。
            import subprocess  # 新增代码+GenericLaunchBackendMaturity：只在真实生产路径导入 subprocess；如果没有这一行，后端无法启动进程。
            process = subprocess.Popen(request.argv(), shell=False)  # 新增代码+GenericLaunchBackendMaturity：使用 argv 且 shell=False 启动；如果没有这一行，生产后端不能真正打开普通应用。
        except Exception as error:  # 新增代码+GenericLaunchBackendMaturity：捕获所有启动异常并保留类型；如果没有这一行，文件不存在等错误会直接冒泡。
            return GenericLaunchResult(ok=False, decision="generic_launch_backend_failed", backend="phase110_production_generic_launch_backend", process_started=False, process_id=0, process_executable=request.executable, argv=tuple(request.argv()), real_desktop_touched=False, cleanup_registered=False, owned_process_registered=False, failure_reason=f"{type(error).__name__}:{error}").to_report()  # 新增代码+GenericLaunchBackendMaturity：返回结构化异常原因；如果没有这一行，用户看不到为什么启动失败。
        process_id = int(getattr(process, "pid", 0) or 0)  # 新增代码+GenericLaunchBackendMaturity：读取真实进程 pid；如果没有这一行，窗口身份绑定没有进程基准。
        owned_record = self.registry.register(process_id, request.executable, request.argv(), process_object=process)  # 新增代码+GenericLaunchBackendMaturity：登记真实自有进程和清理责任；如果没有这一行，stop/abort 可能误关用户原有窗口。
        return GenericLaunchResult(ok=True, decision="generic_launch_production_backend_started_owned_process", backend="phase110_production_generic_launch_backend", process_started=True, process_id=process_id, process_executable=request.executable, argv=tuple(request.argv()), real_desktop_touched=True, cleanup_registered=bool(owned_record.get("cleanup_registered")), owned_process_registered=True).to_report()  # 新增代码+GenericLaunchBackendMaturity：返回生产启动摘要；如果没有这一行，上层无法知道真实桌面已被触碰。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，Phase110ProductionGenericLaunchBackend.launch 到此结束；如果没有这个边界说明，读者不容易看出生产启动范围。
# 新增代码+GenericLaunchBackendMaturity：类段结束，Phase110ProductionGenericLaunchBackend 到此结束；如果没有这个边界说明，代码小白不容易看出生产后端范围。

def run_generic_launch_backend(phase108_report: dict[str, Any], enable_real_launch: bool = False, backend: Any | None = None) -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，编排默认关闭、安全复核和后端调用；如果没有这个函数，测试和 Phase109 需要手写启动流程。
    request = build_generic_launch_request(phase108_report, real_launch_authorized=enable_real_launch)  # 新增代码+GenericLaunchBackendMaturity：构造结构化请求并写入授权状态；如果没有这一行，后端无法知道 full gate 是否放行。
    if not enable_real_launch:  # 新增代码+GenericLaunchBackendMaturity：默认关闭时不调用任何后端；如果没有这一行，普通 /computer launch 可能触发真实启动。
        return _phase110_refusal_report(request, "generic_real_launch_disabled_by_default", "real_launch_default_disabled")  # 新增代码+GenericLaunchBackendMaturity：返回零副作用默认关闭报告；如果没有这一行，用户看不到为什么没有启动。
    if not phase110_safe_launch_request(request):  # 新增代码+GenericLaunchBackendMaturity：授权后仍要先检查安全计划；如果没有这一行，危险计划会进入后端。
        return _phase110_refusal_report(request, "unsafe_generic_launch_plan_rejected", "high_risk_or_unsafe_launch_plan")  # 新增代码+GenericLaunchBackendMaturity：危险计划在后端前拒绝；如果没有这一行，PowerShell 等目标可能有副作用。
    selected_backend = backend if backend is not None else Phase110RecordingGenericLaunchBackend()  # 新增代码+GenericLaunchBackendMaturity：默认使用记录型后端；如果没有这一行，测试路径可能触碰真实桌面。
    launch_method = getattr(selected_backend, "launch", None)  # 新增代码+GenericLaunchBackendMaturity：读取后端 launch 方法；如果没有这一行，坏后端会产生难懂属性错误。
    if not callable(launch_method):  # 新增代码+GenericLaunchBackendMaturity：后端缺少 launch 时结构化失败；如果没有这一行，配置错误会打断整个 agent。
        return _phase110_refusal_report(request, "generic_launch_backend_missing", "launch_backend_missing")  # 新增代码+GenericLaunchBackendMaturity：返回后端缺失原因；如果没有这一行，用户不知道该修什么。
    raw_result = launch_method(request)  # 新增代码+GenericLaunchBackendMaturity：把结构化请求送入后端；如果没有这一行，通用启动永远停在计划层。
    result = dict(raw_result) if isinstance(raw_result, dict) else {"ok": bool(raw_result)}  # 新增代码+GenericLaunchBackendMaturity：规范后端返回值；如果没有这一行，非 dict 后端会污染上层。
    request_report = request.to_report()  # 新增代码+GenericLaunchBackendMaturity：生成请求摘要；如果没有这一行，最终报告缺少 argv 证据。
    result.update({"marker": PHASE110_GENERIC_LAUNCH_BACKEND_MARKER, "ok_token": PHASE110_GENERIC_LAUNCH_BACKEND_OK_TOKEN, "model": PHASE110_GENERIC_LAUNCH_BACKEND_MODEL, "passed": bool(result.get("ok") and result.get("backend_launch_reaches_launcher") and result.get("cleanup_registered") and result.get("owned_process_registered")), "request": request_report, "high_risk_refused": bool(request.high_risk_refused), "default_off_backend_not_called": False, "real_launch_default_disabled": PHASE110_REAL_LAUNCH_DEFAULT_DISABLED, "uncontrolled_actions_expanded": PHASE110_UNCONTROLLED_ACTIONS_EXPANDED})  # 新增代码+GenericLaunchBackendMaturity：补齐统一矩阵字段；如果没有这一行，成熟矩阵无法直接读取 Task 2 结果。
    return result  # 新增代码+GenericLaunchBackendMaturity：返回通用启动报告；如果没有这一行，调用方拿不到后端事实。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，run_generic_launch_backend 到此结束；如果没有这个边界说明，代码小白不容易看出编排范围。

def run_phase110_generic_launch_backend_contract() -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，运行 Task 2 无真实桌面副作用合同；如果没有这个函数，CLI 和矩阵没有统一自检入口。
    default_backend = Phase110RecordingGenericLaunchBackend()  # 新增代码+GenericLaunchBackendMaturity：创建默认关闭路径后端；如果没有这一行，无法证明默认关闭没有调用后端。
    default_off = run_generic_launch_backend(phase110_contract_safe_phase108_report(), enable_real_launch=False, backend=default_backend)  # 新增代码+GenericLaunchBackendMaturity：运行默认关闭样本；如果没有这一行，安全默认值没有证据。
    enabled_registry = Phase110OwnedProcessRegistry()  # 新增代码+GenericLaunchBackendMaturity：创建授权路径 registry；如果没有这一行，owned process 登记无法被合同检查。
    enabled_backend = Phase110RecordingGenericLaunchBackend(registry=enabled_registry)  # 新增代码+GenericLaunchBackendMaturity：创建授权记录型后端；如果没有这一行，正向后端调用没有安全替身。
    enabled = run_generic_launch_backend(phase110_contract_safe_phase108_report(), enable_real_launch=True, backend=enabled_backend)  # 新增代码+GenericLaunchBackendMaturity：运行授权安全样本；如果没有这一行，argv 和登记路径没有证据。
    unsafe_backend = Phase110RecordingGenericLaunchBackend()  # 新增代码+GenericLaunchBackendMaturity：创建危险路径后端；如果没有这一行，无法证明危险拒绝前未调用后端。
    unsafe = run_generic_launch_backend(phase110_contract_unsafe_phase108_report(), enable_real_launch=True, backend=unsafe_backend)  # 新增代码+GenericLaunchBackendMaturity：运行危险样本；如果没有这一行，高风险拒绝没有证据。
    failure = run_generic_launch_backend(phase110_contract_safe_phase108_report(), enable_real_launch=True, backend=Phase110FailingGenericLaunchBackend("simulated_create_process_failure"))  # 新增代码+GenericLaunchBackendMaturity：运行结构化失败样本；如果没有这一行，失败原因没有合同覆盖。
    default_off_zero_events = bool(default_off.get("default_off_backend_not_called") and len(default_backend.launches) == 0 and not default_off.get("real_desktop_touched"))  # 新增代码+GenericLaunchBackendMaturity：汇总默认关闭零副作用；如果没有这一行，默认安全无法量化。
    authorized_argv_backend = bool(enabled.get("backend_launch_reaches_launcher") and len(enabled_backend.launches) == 1 and enabled_backend.launches[0].get("command_shape") == "argv_no_shell")  # 新增代码+GenericLaunchBackendMaturity：汇总授权 argv 后端路径；如果没有这一行，最后一跳安全形状不清楚。
    unsafe_refused_before_backend = bool(unsafe.get("decision") == "unsafe_generic_launch_plan_rejected" and len(unsafe_backend.launches) == 0 and not unsafe.get("real_desktop_touched"))  # 新增代码+GenericLaunchBackendMaturity：汇总危险路径后端前拒绝；如果没有这一行，拒绝是否零副作用不可见。
    owned_process_registered = bool(enabled.get("owned_process_registered") and len(enabled_registry.owned_processes) == 1 and enabled_registry.owned_processes[0].get("cleanup_registered"))  # 新增代码+GenericLaunchBackendMaturity：汇总自有进程登记；如果没有这一行，cleanup 责任没有成熟证据。
    launch_failure_structured_reason = bool(not failure.get("ok") and failure.get("decision") == "generic_launch_backend_failed" and failure.get("failure_reason"))  # 新增代码+GenericLaunchBackendMaturity：汇总结构化失败原因；如果没有这一行，启动失败可能沉默。
    passed = bool(default_off_zero_events and authorized_argv_backend and unsafe_refused_before_backend and owned_process_registered and launch_failure_structured_reason and not PHASE110_UNCONTROLLED_ACTIONS_EXPANDED)  # 新增代码+GenericLaunchBackendMaturity：计算 Task 2 合同是否通过；如果没有这一行，CLI 无法用退出码表达失败。
    return {"marker": PHASE110_GENERIC_LAUNCH_BACKEND_MARKER, "ok_token": PHASE110_GENERIC_LAUNCH_BACKEND_OK_TOKEN, "model": PHASE110_GENERIC_LAUNCH_BACKEND_MODEL, "passed": passed, "generic_launch_backend_ready": True, "generic_real_launch_default_enabled": False, "generic_real_launch_enabled_when_authorized": authorized_argv_backend, "default_off_zero_events": default_off_zero_events, "authorized_argv_backend": authorized_argv_backend, "unsafe_refused_before_backend": unsafe_refused_before_backend, "owned_process_registered": owned_process_registered, "launch_failure_structured_reason": launch_failure_structured_reason, "real_desktop_touched": False, "uncontrolled_actions_expanded": PHASE110_UNCONTROLLED_ACTIONS_EXPANDED, "default_off_report": default_off, "enabled_report": enabled, "unsafe_report": unsafe, "failure_report": failure}  # 新增代码+GenericLaunchBackendMaturity：返回完整合同报告；如果没有这一行，测试、CLI 和最终矩阵无法共享事实。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，run_phase110_generic_launch_backend_contract 到此结束；如果没有这个边界说明，代码小白不容易看出合同范围。

def phase110_cli_line(report: dict[str, Any]) -> str:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，把 Task 2 报告转成稳定 token 行；如果没有这个函数，真实终端验收只能解析复杂 JSON。
    ok_token = f" {PHASE110_GENERIC_LAUNCH_BACKEND_OK_TOKEN}" if bool(report.get("passed", False)) else ""  # 新增代码+GenericLaunchBackendMaturity：只在合同通过时展示 OK token；如果没有这一行，失败报告可能被误判为成功。
    return f"{PHASE110_GENERIC_LAUNCH_BACKEND_MARKER}{ok_token} generic_launch_backend_ready={_phase110_bool_token(report.get('generic_launch_backend_ready', False))} generic_real_launch_default_enabled={_phase110_bool_token(report.get('generic_real_launch_default_enabled', True))} generic_real_launch_enabled_when_authorized={_phase110_bool_token(report.get('generic_real_launch_enabled_when_authorized', False))} default_off_zero_events={_phase110_bool_token(report.get('default_off_zero_events', False))} authorized_argv_backend={_phase110_bool_token(report.get('authorized_argv_backend', False))} unsafe_refused_before_backend={_phase110_bool_token(report.get('unsafe_refused_before_backend', False))} owned_process_registered={_phase110_bool_token(report.get('owned_process_registered', False))} launch_failure_structured_reason={_phase110_bool_token(report.get('launch_failure_structured_reason', False))} real_desktop_touched={_phase110_bool_token(report.get('real_desktop_touched', False))} uncontrolled_actions_expanded={_phase110_bool_token(report.get('uncontrolled_actions_expanded', False))}"  # 新增代码+GenericLaunchBackendMaturity：返回固定顺序 token 行；如果没有这一行，场景断言容易因输出漂移失败。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，phase110_cli_line 到此结束；如果没有这个边界说明，代码小白不容易看出 CLI 输出范围。

def main(argv: list[str] | None = None) -> int:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，提供命令行自检入口；如果没有这个函数，用户不能直接运行模块查看 Task 2 合同。
    _ = argv  # 新增代码+GenericLaunchBackendMaturity：保留 argv 扩展位；如果没有这一行，读者可能误以为参数被遗漏。
    report = run_phase110_generic_launch_backend_contract()  # 新增代码+GenericLaunchBackendMaturity：运行无真实桌面副作用合同；如果没有这一行，CLI 没有事实来源。
    print(phase110_cli_line(report))  # 新增代码+GenericLaunchBackendMaturity：打印稳定 token 行；如果没有这一行，真实终端验收无法快速匹配。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+GenericLaunchBackendMaturity：打印完整 JSON 报告；如果没有这一行，失败排查缺少细节。
    return 0 if bool(report.get("passed", False)) else 1  # 新增代码+GenericLaunchBackendMaturity：按合同结果返回退出码；如果没有这一行，自动化无法区分成功和失败。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，main 到此结束；如果没有这个边界说明，代码小白不容易看出命令行入口范围。

__all__ = ["GenericLaunchRequest", "GenericLaunchResult", "PHASE110_GENERIC_LAUNCH_BACKEND_MARKER", "PHASE110_GENERIC_LAUNCH_BACKEND_MODEL", "PHASE110_GENERIC_LAUNCH_BACKEND_OK_TOKEN", "PHASE110_REAL_LAUNCH_DEFAULT_DISABLED", "PHASE110_UNCONTROLLED_ACTIONS_EXPANDED", "Phase110FailingGenericLaunchBackend", "Phase110OwnedProcessRegistry", "Phase110ProductionGenericLaunchBackend", "Phase110RecordingGenericLaunchBackend", "build_generic_launch_request", "main", "phase110_cli_line", "phase110_contract_safe_phase108_report", "phase110_contract_unsafe_phase108_report", "phase110_safe_launch_request", "run_generic_launch_backend", "run_phase110_generic_launch_backend_contract"]  # 新增代码+GenericLaunchBackendMaturity：限定公开导出名称；如果没有这一行，通配导入会暴露内部 helper。

if __name__ == "__main__":  # 新增代码+GenericLaunchBackendMaturity：文件入口段开始，允许直接运行本模块；如果没有这一行，python 文件方式不会执行自检。
    raise SystemExit(main())  # 新增代码+GenericLaunchBackendMaturity：用 main 返回码退出；如果没有这一行，命令行状态不明确。
# 新增代码+GenericLaunchBackendMaturity：文件入口段结束，直接运行模块到此结束；如果没有这个边界说明，读者不容易看出脚本入口范围。
