"""Generic Windows application launch backend for Computer Use full maturity."""  # 新增代码+GenericLaunchBackendMaturity：说明本模块负责普通应用的通用启动后端；如果没有这一行，读者容易把这里误解成逐应用 controller。
from __future__ import annotations  # 新增代码+GenericLaunchBackendMaturity：启用延迟类型注解解析；如果没有这一行，类之间互相引用时更容易出现导入顺序问题。

import json  # 新增代码+GenericLaunchBackendMaturity：导入 JSON 工具用于 CLI 输出完整报告；如果没有这一行，失败排查只能看短 token。
import os  # 新增代码+WindowsMultiBackendLaunchExecutor：导入 os 读取开始菜单环境变量；如果没有这一行，shortcut 真实后端无法在用户和公共开始菜单里找快捷方式。
import sys  # 新增代码+GenericLaunchBackendMaturity：导入 sys 用于生产后端判断当前平台；如果没有这一行，非 Windows 环境可能误走真实启动分支。
import time  # 新增代码+FullNaturalUserFlowCleanup：导入时间工具用于等待自有进程退出；如果没有这一行，cleanup 刚发出终止请求就可能误报成功。
from dataclasses import dataclass, field  # 新增代码+GenericLaunchBackendMaturity：导入 dataclass 和 field 表达结构化请求结果；如果没有这一行，请求和结果会退回松散字典不利于学习。
from pathlib import Path  # 新增代码+WindowsMultiBackendLaunchExecutor：导入 Path 处理开始菜单快捷方式路径；如果没有这一行，shortcut 后端只能靠脆弱字符串拼接。
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
    launch_backend: str = "argv_no_shell"  # 新增代码+WindowsMultiBackendLaunchExecutor：保存启动后端类型；如果没有这一行，Phase110 只能把所有应用误当成 exe/argv。
    command_shape: str = "argv_no_shell"  # 新增代码+WindowsMultiBackendLaunchExecutor：保存命令形状；如果没有这一行，终端和审计无法区分 argv、AUMID、shortcut。
    aumid: str = ""  # 新增代码+WindowsMultiBackendLaunchExecutor：保存 AppX/AUMID 身份；如果没有这一行，Calculator 等 UWP 应用无法被真实启动器定位。
    shortcut_id: str = ""  # 新增代码+WindowsMultiBackendLaunchExecutor：保存开始菜单快捷方式标识；如果没有这一行，Start Menu 应用只能被错误猜成 exe。
    launch_plan: dict[str, Any] = field(default_factory=dict)  # 新增代码+GenericLaunchBackendMaturity：保存 Phase108/Phase69 安全计划副本；如果没有这一行，后端无法复核无 shell、无提权、无系统修改。
    raw_phase108_report: dict[str, Any] = field(default_factory=dict)  # 新增代码+GenericLaunchBackendMaturity：保存原始发现报告副本；如果没有这一行，失败排查无法追溯候选来源。
    high_risk_refused: bool = False  # 新增代码+GenericLaunchBackendMaturity：保存高风险拒绝标志；如果没有这一行，PowerShell 等目标可能绕过后端复核。
    real_launch_authorized: bool = False  # 新增代码+GenericLaunchBackendMaturity：保存是否经过显式真实启动授权；如果没有这一行，生产后端无法阻止默认启动。
    request_id: str = "phase110-generic-launch-request"  # 新增代码+GenericLaunchBackendMaturity：保存请求 id 便于审计；如果没有这一行，多次启动记录不容易追踪。

    def argv(self) -> list[str]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，把请求转成 argv 数组；如果没有这个函数，调用方可能重复拼接命令。
        if self.launch_backend != "argv_no_shell":  # 新增代码+WindowsMultiBackendLaunchExecutor：非 argv 后端不生成 argv；如果没有这一行，AppX/shortcut 会再次被 Popen 误接。
            return []  # 新增代码+WindowsMultiBackendLaunchExecutor：返回空 argv 表示后端必须走专用启动器；如果没有这一行，空 executable 会变成 [""] 这种危险假命令。
        return [self.executable, *list(self.arguments)]  # 新增代码+GenericLaunchBackendMaturity：返回可直接交给 Popen 的无 shell 参数列表；如果没有这一行，后端可能退回 shell 字符串。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，GenericLaunchRequest.argv 到此结束；如果没有这个边界说明，代码小白不容易看出 argv 生成范围。

    def launch_identity(self) -> str:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，返回当前后端的审计身份；如果没有这段函数，registry 和报告会在 AppX/shortcut 上缺少可读目标。
        if self.launch_backend == "appx_aumid":  # 新增代码+WindowsMultiBackendLaunchExecutor：识别 AppX 后端；如果没有这一行，AUMID 会落到空 executable。
            return self.aumid  # 新增代码+WindowsMultiBackendLaunchExecutor：返回 AUMID 作为启动身份；如果没有这一行，后续窗口绑定无法知道启动的是哪个包。
        if self.launch_backend == "start_menu_shortcut":  # 新增代码+WindowsMultiBackendLaunchExecutor：识别 shortcut 后端；如果没有这一行，快捷方式身份会丢失。
            return self.shortcut_id  # 新增代码+WindowsMultiBackendLaunchExecutor：返回快捷方式标识；如果没有这一行，调试报告无法定位开始菜单入口。
        return self.executable  # 新增代码+WindowsMultiBackendLaunchExecutor：默认返回 exe；如果没有这一行，argv 后端报告会缺少进程名。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，GenericLaunchRequest.launch_identity 到此结束；如果没有这个边界说明，用户不容易看出身份选择范围。

    def to_report(self) -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，把请求转成可序列化报告；如果没有这个函数，测试和 CLI 无法稳定检查请求形状。
        return {"canonical_target": self.canonical_target, "executable": self.executable, "arguments": list(self.arguments), "argv": self.argv(), "launch_backend": self.launch_backend, "command_shape": self.command_shape, "aumid": self.aumid, "shortcut_id": self.shortcut_id, "launch_identity": self.launch_identity(), "uses_shell_string": False, "high_risk_refused": self.high_risk_refused, "real_launch_authorized": self.real_launch_authorized, "request_id": self.request_id, "launch_plan": dict(self.launch_plan)}  # 修改代码+WindowsMultiBackendLaunchExecutor：返回包含多后端身份的请求摘要；如果没有这一行，后端审计无法证明 AppX/shortcut 没有退回 shell 或 argv。
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
    launch_backend: str = "argv_no_shell"  # 新增代码+WindowsMultiBackendLaunchExecutor：保存实际使用的启动后端；如果没有这一行，最终报告无法证明走的是 AppX 还是 shortcut。
    command_shape: str = "argv_no_shell"  # 新增代码+WindowsMultiBackendLaunchExecutor：保存实际命令形状；如果没有这一行，终端无法审计是否绕开 shell 字符串。
    real_desktop_touched: bool = False  # 新增代码+GenericLaunchBackendMaturity：保存是否触碰真实桌面；如果没有这一行，记录后端和生产后端会被混淆。
    cleanup_registered: bool = False  # 新增代码+GenericLaunchBackendMaturity：保存是否登记清理责任；如果没有这一行，stop/abort 无法确认是否有收尾句柄。
    owned_process_registered: bool = False  # 新增代码+GenericLaunchBackendMaturity：保存进程是否登记为本 agent 自有；如果没有这一行，不能证明不会误关用户原有窗口。
    failure_reason: str = ""  # 新增代码+GenericLaunchBackendMaturity：保存结构化失败原因；如果没有这一行，启动失败会变成难懂异常。

    def to_report(self) -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，把结果转成 JSON 风格报告；如果没有这个函数，CLI 和测试需要手动理解 dataclass。
        return {"ok": self.ok, "decision": self.decision, "backend": self.backend, "backend_launch_performed": bool(self.process_started or self.ok), "backend_launch_reaches_launcher": bool(self.ok), "process_started": self.process_started, "process_id": self.process_id, "process_executable": self.process_executable, "process_identity_verified": bool(self.process_started and self.process_id > 0 and self.process_executable), "argv": list(self.argv), "launch_backend": self.launch_backend, "command_shape": self.command_shape, "uses_shell_string": False, "real_desktop_touched": self.real_desktop_touched, "cleanup_registered": self.cleanup_registered, "owned_process_registered": self.owned_process_registered, "failure_reason": self.failure_reason, "low_level_event_count": 0}  # 修改代码+WindowsMultiBackendLaunchExecutor：返回统一结果字段并暴露实际后端；如果没有这一行，上层无法确认 AppX/shortcut 是否走对执行器。
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

    def cleanup_owned_processes(self, reason: str = "cleanup", timeout_seconds: float = 2.0) -> dict[str, Any]:  # 新增代码+FullNaturalUserFlowCleanup：函数段开始，只终止本 registry 保存的自有进程对象；如果没有这段函数，Paint 等真实启动应用会在验收后残留。
        cleaned_count = 0  # 新增代码+FullNaturalUserFlowCleanup：初始化成功清理数量；如果没有这一行，报告无法说明清理了几个进程。
        failed_count = 0  # 新增代码+FullNaturalUserFlowCleanup：初始化清理失败数量；如果没有这一行，报告无法把失败和无资源区分开。
        deadline = time.time() + max(0.1, float(timeout_seconds))  # 新增代码+FullNaturalUserFlowCleanup：计算等待退出的截止时间；如果没有这一行，cleanup 可能无限等待卡住 agent。
        for process_object in list(self._process_objects):  # 新增代码+FullNaturalUserFlowCleanup：遍历本 agent 保存的真实进程对象；如果没有这一行，cleanup 不会处理任何启动的应用。
            try:  # 新增代码+FullNaturalUserFlowCleanup：保护单个进程清理异常；如果没有这一行，一个坏进程对象会中断全部清理。
                if hasattr(process_object, "poll") and process_object.poll() is None:  # 新增代码+FullNaturalUserFlowCleanup：只终止仍在运行的自有进程；如果没有这一行，已退出进程可能被重复处理。
                    process_object.terminate()  # 新增代码+FullNaturalUserFlowCleanup：请求终止本 agent 启动的进程；如果没有这一行，Paint 窗口会继续留在用户桌面。
                while hasattr(process_object, "poll") and process_object.poll() is None and time.time() < deadline:  # 新增代码+FullNaturalUserFlowCleanup：等待进程真实退出；如果没有这一行，刚发送 terminate 就可能误判清理成功。
                    time.sleep(0.05)  # 新增代码+FullNaturalUserFlowCleanup：短暂让出时间给系统关闭进程；如果没有这一行，循环会空转占用 CPU。
                if hasattr(process_object, "poll") and process_object.poll() is None:  # 新增代码+FullNaturalUserFlowCleanup：超时后检查是否仍存活；如果没有这一行，残留进程不会被发现。
                    failed_count += 1  # 新增代码+FullNaturalUserFlowCleanup：记录一个清理失败；如果没有这一行，报告会误称全部清理完成。
                else:  # 新增代码+FullNaturalUserFlowCleanup：进入已退出或无 poll 对象的成功分支；如果没有这一行，成功数量无法统计。
                    cleaned_count += 1  # 新增代码+FullNaturalUserFlowCleanup：记录一个已清理进程；如果没有这一行，用户看不到 cleanup 做了什么。
            except Exception:  # 新增代码+FullNaturalUserFlowCleanup：捕获 terminate/poll 异常；如果没有这一行，清理问题会让主任务崩溃。
                failed_count += 1  # 新增代码+FullNaturalUserFlowCleanup：异常也算清理失败；如果没有这一行，失败可能被吞掉。
        cleanup_completed = failed_count == 0  # 新增代码+FullNaturalUserFlowCleanup：只要没有失败就认为清理流程完成；如果没有这一行，上层没有稳定布尔字段。
        return {"cleanup_completed": cleanup_completed, "cleaned_process_count": cleaned_count, "cleanup_failed_count": failed_count, "registered_process_count": len(self.owned_processes), "reason": reason}  # 新增代码+FullNaturalUserFlowCleanup：返回清理摘要；如果没有这一行，Paint loop 无法把 cleanup 事实写入报告。
    # 新增代码+FullNaturalUserFlowCleanup：函数段结束，Phase110OwnedProcessRegistry.cleanup_owned_processes 到此结束；如果没有这个边界说明，初学者不容易看出清理范围。

    def residual_owned_processes(self) -> dict[str, Any]:  # 新增代码+FullNaturalUserFlowCleanup：函数段开始，检查本 registry 的自有进程对象是否仍存活；如果没有这段函数，报告可能再次把残留误判为已清理。
        residual_count = 0  # 新增代码+FullNaturalUserFlowCleanup：初始化残留数量；如果没有这一行，结果无法量化剩余进程。
        for process_object in list(self._process_objects):  # 新增代码+FullNaturalUserFlowCleanup：遍历本 agent 保存的进程对象；如果没有这一行，残留检查没有事实来源。
            try:  # 新增代码+FullNaturalUserFlowCleanup：保护单个 poll 调用；如果没有这一行，一个坏对象会中断检查。
                residual_count += 1 if hasattr(process_object, "poll") and process_object.poll() is None else 0  # 新增代码+FullNaturalUserFlowCleanup：仍在运行则计为残留；如果没有这一行，残留进程不会触发失败。
            except Exception:  # 新增代码+FullNaturalUserFlowCleanup：poll 异常按保守残留处理；如果没有这一行，无法确认状态的进程会被忽略。
                residual_count += 1  # 新增代码+FullNaturalUserFlowCleanup：记录未知状态残留；如果没有这一行，报告会过于乐观。
        return {"residual_owned_process": residual_count > 0, "residual_owned_process_count": residual_count, "registered_process_count": len(self.owned_processes)}  # 新增代码+FullNaturalUserFlowCleanup：返回残留摘要；如果没有这一行，上层无法证明清理后没有自有进程。
    # 新增代码+FullNaturalUserFlowCleanup：函数段结束，Phase110OwnedProcessRegistry.residual_owned_processes 到此结束；如果没有这个边界说明，初学者不容易看出残留检查范围。
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

def phase110_contract_appx_phase108_report() -> dict[str, Any]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，构造稳定的 AppX/AUMID 安全样本；如果没有这个函数，合同只能证明 exe 后端而不能证明商店应用路线。
    plan = {"safe_to_launch": True, "launch_backend": "appx_aumid", "launch_verb": "ShellExecuteAppUserModelId", "command_shape": "aumid_no_shell", "aumid": "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App", "executable": "", "arguments": [], "changes_registry": False, "changes_system_settings": False, "requires_admin": False, "uses_shell_string": False, "actions_expanded": False}  # 新增代码+WindowsMultiBackendLaunchExecutor：构造无 shell 的 AppX 启动计划；如果没有这一行，AUMID 后端没有安全正例。
    return {"passed": True, "canonical_target": "calculator", "best_candidate_executable": "", "safe_start_process_plan": True, "high_risk_refused": False, "hardcoded_app_whitelist_required": False, "per_app_patch_required": False, "launch_plan": plan}  # 新增代码+WindowsMultiBackendLaunchExecutor：返回 Phase108 形状的 AppX 报告；如果没有这一行，Phase110 合同无法复用发现层接口。
# 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，phase110_contract_appx_phase108_report 到此结束；如果没有这个边界说明，读者不容易看出 AppX 样本范围。

def phase110_contract_shortcut_phase108_report() -> dict[str, Any]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，构造稳定的开始菜单快捷方式安全样本；如果没有这个函数，合同不能证明 shortcut 路线。
    plan = {"safe_to_launch": True, "launch_backend": "start_menu_shortcut", "launch_verb": "ShellExecuteShortcut", "command_shape": "shortcut_no_shell", "shortcut_id": "Obsidian.lnk", "executable": "", "arguments": [], "changes_registry": False, "changes_system_settings": False, "requires_admin": False, "uses_shell_string": False, "actions_expanded": False}  # 新增代码+WindowsMultiBackendLaunchExecutor：构造无 shell 的 shortcut 启动计划；如果没有这一行，快捷方式后端没有安全正例。
    return {"passed": True, "canonical_target": "obsidian", "best_candidate_executable": "", "safe_start_process_plan": True, "high_risk_refused": False, "hardcoded_app_whitelist_required": False, "per_app_patch_required": False, "launch_plan": plan}  # 新增代码+WindowsMultiBackendLaunchExecutor：返回 Phase108 形状的 shortcut 报告；如果没有这一行，Phase110 合同无法证明快捷方式身份被保留。
# 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，phase110_contract_shortcut_phase108_report 到此结束；如果没有这个边界说明，读者不容易看出 shortcut 样本范围。

def build_generic_launch_request(phase108_report: GenericLaunchRequest | dict[str, Any], real_launch_authorized: bool = False, request_id: str = "phase110-generic-launch-request") -> GenericLaunchRequest:  # 修改代码+WindowsMultiBackendLaunchExecutor：函数段开始，把 Phase108 报告转换成支持 argv/AppX/shortcut 的唯一启动请求；如果没有这个函数，后端会直接吃松散字典并再次误接非 exe 应用。
    if isinstance(phase108_report, GenericLaunchRequest):  # 新增代码+GenericLaunchBackendMaturity：如果已经是结构化请求就直接处理；如果没有这一行，二次调用会丢失请求内的授权和 argv。
        return phase108_report  # 新增代码+GenericLaunchBackendMaturity：返回原请求对象；如果没有这一行，已有请求会被错误重建。
    report = dict(phase108_report or {})  # 新增代码+GenericLaunchBackendMaturity：复制 Phase108 报告避免污染调用方对象；如果没有这一行，后续规范化可能改动原始报告。
    plan = dict(report.get("launch_plan", {}) or {})  # 新增代码+GenericLaunchBackendMaturity：读取安全启动计划副本；如果没有这一行，后端无法复核安全字段。
    launch_backend = str(plan.get("launch_backend") or "argv_no_shell").strip() or "argv_no_shell"  # 新增代码+WindowsMultiBackendLaunchExecutor：读取 resolver 选择的真实启动后端；如果没有这一行，Phase110 仍会把 AppX/shortcut 当成普通 exe。
    command_shape = str(plan.get("command_shape") or launch_backend).strip() or launch_backend  # 新增代码+WindowsMultiBackendLaunchExecutor：读取命令形状用于审计；如果没有这一行，终端无法解释当前请求到底是不是 argv。
    executable = str(plan.get("executable") or report.get("best_candidate_executable") or report.get("canonical_target") or "").strip() if launch_backend == "argv_no_shell" else ""  # 修改代码+WindowsMultiBackendLaunchExecutor：只有 argv_no_shell 计划才允许回填 executable；如果没有这一行，AppX/shortcut 会被错误塞进 Popen 可执行槽。
    arguments = tuple(str(argument) for argument in list(plan.get("arguments", []) or []))  # 新增代码+GenericLaunchBackendMaturity：把参数规范成字符串元组；如果没有这一行，Popen 可能收到坏类型或被拼成 shell 字符串。
    aumid = str(plan.get("aumid") or "").strip()  # 新增代码+WindowsMultiBackendLaunchExecutor：读取 AppX/AUMID 的真实身份；如果没有这一行，商店应用启动器拿不到包入口。
    shortcut_id = str(plan.get("shortcut_id") or plan.get("launch_id") or "").strip()  # 新增代码+WindowsMultiBackendLaunchExecutor：读取开始菜单快捷方式标识；如果没有这一行，shortcut 后端无法找到对应入口。
    canonical_target = str(report.get("canonical_target") or executable).strip().lower()  # 新增代码+GenericLaunchBackendMaturity：确定规范目标名；如果没有这一行，后续窗口身份绑定没有稳定目标。
    authorized = bool(real_launch_authorized or report.get("real_launch_authorized", False))  # 新增代码+GenericLaunchBackendMaturity：合并显式授权标志；如果没有这一行，生产后端无法确认 full gate 是否放行。
    return GenericLaunchRequest(canonical_target=canonical_target, executable=executable, arguments=arguments, launch_backend=launch_backend, command_shape=command_shape, aumid=aumid, shortcut_id=shortcut_id, launch_plan=plan, raw_phase108_report=report, high_risk_refused=bool(report.get("high_risk_refused", False)), real_launch_authorized=authorized, request_id=request_id)  # 修改代码+WindowsMultiBackendLaunchExecutor：返回包含多后端身份的结构化请求；如果没有这一行，后端无法统一处理 exe、AppX 和快捷方式。
# 修改代码+WindowsMultiBackendLaunchExecutor：函数段结束，build_generic_launch_request 到此结束；如果没有这个边界说明，代码小白不容易看出请求构造范围。

def phase110_safe_launch_request(request: GenericLaunchRequest) -> bool:  # 修改代码+WindowsMultiBackendLaunchExecutor：函数段开始，按 argv/AppX/shortcut 三种后端复核真实启动安全条件；如果没有这个函数，危险计划可能进入生产后端。
    plan = dict(request.launch_plan or {})  # 新增代码+GenericLaunchBackendMaturity：读取启动计划副本；如果没有这一行，下面的安全字段没有来源。
    common_safe = bool(not request.high_risk_refused and plan.get("safe_to_launch") and not plan.get("changes_registry") and not plan.get("changes_system_settings") and not plan.get("requires_admin") and not plan.get("uses_shell_string") and not plan.get("actions_expanded"))  # 新增代码+WindowsMultiBackendLaunchExecutor：先复核所有后端共享的安全底线；如果没有这一行，每个分支容易漏掉无 shell、无提权、无系统修改约束。
    if not common_safe:  # 新增代码+WindowsMultiBackendLaunchExecutor：共享安全底线失败时立即拒绝；如果没有这一行，危险计划可能继续进入后端分支。
        return False  # 新增代码+WindowsMultiBackendLaunchExecutor：返回不安全；如果没有这一行，后续分支会把危险计划误判成可启动。
    if request.launch_backend == "argv_no_shell":  # 新增代码+WindowsMultiBackendLaunchExecutor：识别普通 Win32 argv 后端；如果没有这一行，exe 应用无法保持原有安全路径。
        return bool(request.executable and request.argv() and plan.get("launch_verb") == "Start-Process")  # 修改代码+WindowsMultiBackendLaunchExecutor：要求 exe、argv 和 Start-Process 计划一致；如果没有这一行，空 exe 或错误 verb 可能进入 Popen。
    if request.launch_backend == "appx_aumid":  # 新增代码+WindowsMultiBackendLaunchExecutor：识别 AppX/AUMID 后端；如果没有这一行，商店应用会继续被后端前置拒绝。
        return bool(request.aumid and plan.get("launch_verb") == "ShellExecuteAppUserModelId")  # 新增代码+WindowsMultiBackendLaunchExecutor：要求 AUMID 和专用 ShellExecute 计划一致；如果没有这一行，未知 AppX 身份可能被放行。
    if request.launch_backend == "start_menu_shortcut":  # 新增代码+WindowsMultiBackendLaunchExecutor：识别开始菜单快捷方式后端；如果没有这一行，shortcut 应用会继续停在不可执行状态。
        return bool(request.shortcut_id and plan.get("launch_verb") == "ShellExecuteShortcut")  # 新增代码+WindowsMultiBackendLaunchExecutor：要求 shortcut 标识和专用 ShellExecute 计划一致；如果没有这一行，空快捷方式可能被误启动。
    return False  # 新增代码+WindowsMultiBackendLaunchExecutor：未知后端一律拒绝；如果没有这一行，新字段拼错可能绕过安全复核。
# 修改代码+WindowsMultiBackendLaunchExecutor：函数段结束，phase110_safe_launch_request 到此结束；如果没有这个边界说明，读者不容易看出安全复核范围。

def _phase110_refusal_report(request: GenericLaunchRequest, decision: str, failure_reason: str) -> dict[str, Any]:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，构造统一拒绝报告；如果没有这个函数，默认关闭、危险拒绝和失败路径字段会不一致。
    base = request.to_report()  # 新增代码+GenericLaunchBackendMaturity：读取请求摘要；如果没有这一行，拒绝报告无法展示 argv 和计划。
    base.update({"marker": PHASE110_GENERIC_LAUNCH_BACKEND_MARKER, "ok_token": PHASE110_GENERIC_LAUNCH_BACKEND_OK_TOKEN, "model": PHASE110_GENERIC_LAUNCH_BACKEND_MODEL, "ok": False, "passed": False, "decision": decision, "backend_launch_reaches_launcher": False, "backend_launch_performed": False, "process_started": False, "process_id": 0, "process_executable": request.launch_identity(), "process_identity_verified": False, "cleanup_registered": False, "owned_process_registered": False, "real_desktop_touched": False, "default_off_backend_not_called": decision == "generic_real_launch_disabled_by_default", "high_risk_refused": bool(request.high_risk_refused), "failure_reason": failure_reason, "uncontrolled_actions_expanded": PHASE110_UNCONTROLLED_ACTIONS_EXPANDED})  # 修改代码+WindowsMultiBackendLaunchExecutor：合并拒绝字段并使用多后端审计身份；如果没有这一行，AppX/shortcut 拒绝报告会显示空 executable。
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
        owned_record = self.registry.register(process_id, request.launch_identity(), request.argv())  # 修改代码+WindowsMultiBackendLaunchExecutor：按当前后端身份登记自有资源；如果没有这一行，AppX/shortcut 会登记成空 executable。
        result = GenericLaunchResult(ok=True, decision="generic_launch_recording_backend_started_owned_process", backend="phase110_recording_generic_launch_backend", process_started=True, process_id=process_id, process_executable=request.launch_identity(), argv=tuple(request.argv()), launch_backend=request.launch_backend, command_shape=request.command_shape, real_desktop_touched=False, cleanup_registered=bool(owned_record.get("cleanup_registered")), owned_process_registered=True)  # 修改代码+WindowsMultiBackendLaunchExecutor：构造带真实后端类型的记录型成功结果；如果没有这一行，上层拿不到 AppX/shortcut 分发摘要。
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
        return GenericLaunchResult(ok=False, decision="generic_launch_backend_failed", backend="phase110_failing_generic_launch_backend", process_started=False, process_id=0, process_executable=request.launch_identity(), argv=tuple(request.argv()), launch_backend=request.launch_backend, command_shape=request.command_shape, real_desktop_touched=False, cleanup_registered=False, owned_process_registered=False, failure_reason=self.failure_reason).to_report()  # 修改代码+WindowsMultiBackendLaunchExecutor：返回包含多后端身份的结构化失败结果；如果没有这一行，AppX/shortcut 失败会丢失目标身份。
    # 新增代码+GenericLaunchBackendMaturity：函数段结束，Phase110FailingGenericLaunchBackend.launch 到此结束；如果没有这个边界说明，读者不容易看出失败后端范围。
# 新增代码+GenericLaunchBackendMaturity：类段结束，Phase110FailingGenericLaunchBackend 到此结束；如果没有这个边界说明，代码小白不容易看出失败后端范围。

class Phase110WindowsNativeLauncher:  # 新增代码+WindowsMultiBackendLaunchExecutor：类段开始，封装 Windows 原生最后一跳启动 API；如果没有这个类，生产后端会继续把 AppX/shortcut 错接到 Popen。
    def launch_argv(self, argv: list[str]) -> dict[str, Any]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，启动普通 Win32 argv 应用；如果没有这段函数，exe 应用会失去原有无 shell 启动能力。
        import subprocess  # 新增代码+WindowsMultiBackendLaunchExecutor：在 argv 分支导入 subprocess；如果没有这一行，普通 exe 后端无法创建进程。
        process = subprocess.Popen(list(argv), shell=False)  # 修改代码+WindowsMultiBackendLaunchExecutor：使用 argv 且 shell=False 启动 Win32 应用；如果没有这一行，普通 exe 应用不能真实打开。
        return {"ok": True, "process_started": True, "process_id": int(getattr(process, "pid", 0) or 0), "process_object": process}  # 新增代码+WindowsMultiBackendLaunchExecutor：返回进程对象和 pid；如果没有这一行，窗口绑定和 cleanup 没有事实来源。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，Phase110WindowsNativeLauncher.launch_argv 到此结束；如果没有这个边界说明，读者不容易看出 argv 启动范围。

    def _shell_execute_with_process(self, file_name: str) -> dict[str, Any]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，用 ShellExecuteEx 尝试拿到进程句柄；如果没有这段函数，AppX/shortcut 只能粗糙打开而缺少 pid 线索。
        import ctypes  # 新增代码+WindowsMultiBackendLaunchExecutor：导入 Windows ctypes API；如果没有这一行，Python 无法调用 ShellExecuteExW。
        from ctypes import wintypes  # 新增代码+WindowsMultiBackendLaunchExecutor：导入 Windows 基础类型；如果没有这一行，ShellExecuteExW 结构体字段会不清晰。
        class SHELLEXECUTEINFO(ctypes.Structure):  # 新增代码+WindowsMultiBackendLaunchExecutor：结构体段开始，描述 ShellExecuteExW 需要的参数；如果没有这个结构体，无法请求 NOCLOSEPROCESS 句柄。
            _fields_ = [("cbSize", wintypes.DWORD), ("fMask", wintypes.ULONG), ("hwnd", wintypes.HWND), ("lpVerb", wintypes.LPCWSTR), ("lpFile", wintypes.LPCWSTR), ("lpParameters", wintypes.LPCWSTR), ("lpDirectory", wintypes.LPCWSTR), ("nShow", ctypes.c_int), ("hInstApp", wintypes.HINSTANCE), ("lpIDList", ctypes.c_void_p), ("lpClass", wintypes.LPCWSTR), ("hkeyClass", wintypes.HKEY), ("dwHotKey", wintypes.DWORD), ("hIconOrMonitor", wintypes.HANDLE), ("hProcess", wintypes.HANDLE)]  # 新增代码+WindowsMultiBackendLaunchExecutor：列出 ShellExecuteExW 字段；如果没有这一行，Windows API 调用会读错内存。
        # 新增代码+WindowsMultiBackendLaunchExecutor：结构体段结束，SHELLEXECUTEINFO 到此结束；如果没有这个边界说明，读者不容易看出 Windows API 参数范围。
        see_mask_nocloseprocess = 0x00000040  # 新增代码+WindowsMultiBackendLaunchExecutor：请求系统保留进程句柄；如果没有这一行，AppX/shortcut 启动后通常拿不到 pid。
        info = SHELLEXECUTEINFO()  # 新增代码+WindowsMultiBackendLaunchExecutor：创建 ShellExecuteExW 参数对象；如果没有这一行，无法向 Windows 传入启动请求。
        info.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)  # 新增代码+WindowsMultiBackendLaunchExecutor：写入结构体大小；如果没有这一行，ShellExecuteExW 会拒绝或误读参数。
        info.fMask = see_mask_nocloseprocess  # 新增代码+WindowsMultiBackendLaunchExecutor：启用返回进程句柄；如果没有这一行，后续窗口身份绑定缺少 pid 线索。
        info.lpVerb = "open"  # 新增代码+WindowsMultiBackendLaunchExecutor：声明执行打开动作；如果没有这一行，Windows 可能使用不稳定默认 verb。
        info.lpFile = str(file_name)  # 新增代码+WindowsMultiBackendLaunchExecutor：写入要打开的 AppX shell 路径或快捷方式路径；如果没有这一行，ShellExecuteExW 不知道启动目标。
        info.nShow = 1  # 新增代码+WindowsMultiBackendLaunchExecutor：要求正常显示窗口；如果没有这一行，应用可能最小化或不可见。
        ok = bool(ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(info)))  # 新增代码+WindowsMultiBackendLaunchExecutor：调用真实 Windows ShellExecuteExW；如果没有这一行，非 argv 后端不会真正触碰桌面。
        if not ok:  # 新增代码+WindowsMultiBackendLaunchExecutor：检查启动 API 是否失败；如果没有这一行，失败会被误报为成功。
            return {"ok": False, "process_started": False, "process_id": 0, "process_object": None, "failure_reason": f"ShellExecuteExW_failed:{ctypes.GetLastError()}"}  # 新增代码+WindowsMultiBackendLaunchExecutor：返回结构化 Windows 错误；如果没有这一行，用户看不到非 argv 启动失败原因。
        process_id = int(ctypes.windll.kernel32.GetProcessId(info.hProcess)) if info.hProcess else 0  # 新增代码+WindowsMultiBackendLaunchExecutor：从进程句柄读取 pid；如果没有这一行，窗口身份绑定只能靠猜。
        if info.hProcess:  # 新增代码+WindowsMultiBackendLaunchExecutor：只有拿到句柄时才关闭句柄；如果没有这一行，空句柄关闭会造成无意义 API 调用。
            ctypes.windll.kernel32.CloseHandle(info.hProcess)  # 新增代码+WindowsMultiBackendLaunchExecutor：关闭本地句柄避免泄漏；如果没有这一行，agent 多次启动应用可能积累句柄资源。
        return {"ok": True, "process_started": True, "process_id": process_id, "process_object": None}  # 新增代码+WindowsMultiBackendLaunchExecutor：返回非 argv 启动结果；如果没有这一行，生产后端拿不到统一结果。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，Phase110WindowsNativeLauncher._shell_execute_with_process 到此结束；如果没有这个边界说明，读者不容易看出 ShellExecute 范围。

    def launch_appx_aumid(self, aumid: str) -> dict[str, Any]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，按 AUMID 启动 AppX/UWP 应用；如果没有这段函数，计算器等商店应用无法走真实后端。
        return self._shell_execute_with_process(f"shell:AppsFolder\\{str(aumid)}")  # 新增代码+WindowsMultiBackendLaunchExecutor：把 AUMID 转成 Windows AppsFolder 路径并启动；如果没有这一行，AUMID 只是字符串不会打开应用。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，Phase110WindowsNativeLauncher.launch_appx_aumid 到此结束；如果没有这个边界说明，读者不容易看出 AppX 启动范围。

    def launch_start_menu_shortcut(self, shortcut_id: str) -> dict[str, Any]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，按开始菜单快捷方式启动应用；如果没有这段函数，只存在快捷方式的应用会继续打不开。
        shortcut_path = _phase110_find_start_menu_shortcut(shortcut_id)  # 新增代码+WindowsMultiBackendLaunchExecutor：解析快捷方式真实路径；如果没有这一行，ShellExecuteExW 只能拿到不可靠的短名称。
        if not shortcut_path:  # 新增代码+WindowsMultiBackendLaunchExecutor：检查是否找到了快捷方式；如果没有这一行，空路径可能被误交给 Windows API。
            return {"ok": False, "process_started": False, "process_id": 0, "process_object": None, "failure_reason": "start_menu_shortcut_not_found"}  # 新增代码+WindowsMultiBackendLaunchExecutor：返回快捷方式未找到原因；如果没有这一行，用户看不到为什么 shortcut 启动失败。
        return self._shell_execute_with_process(str(shortcut_path))  # 新增代码+WindowsMultiBackendLaunchExecutor：用 ShellExecuteExW 打开快捷方式；如果没有这一行，shortcut 后端不会真正触碰桌面。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，Phase110WindowsNativeLauncher.launch_start_menu_shortcut 到此结束；如果没有这个边界说明，读者不容易看出 shortcut 启动范围。
# 新增代码+WindowsMultiBackendLaunchExecutor：类段结束，Phase110WindowsNativeLauncher 到此结束；如果没有这个边界说明，代码小白不容易看出 Windows 原生启动器范围。

def _phase110_start_menu_roots() -> list[Path]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，列出 Windows 用户和公共开始菜单目录；如果没有这段函数，shortcut 后端不知道去哪里找快捷方式。
    roots = [Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs", Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"]  # 新增代码+WindowsMultiBackendLaunchExecutor：构造两个常见开始菜单根目录；如果没有这一行，只能覆盖当前用户或公共目录之一。
    return [root for root in roots if str(root) and root.exists()]  # 新增代码+WindowsMultiBackendLaunchExecutor：过滤不存在的目录；如果没有这一行，递归扫描会产生无意义路径错误。
# 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，_phase110_start_menu_roots 到此结束；如果没有这个边界说明，读者不容易看出目录来源范围。

def _phase110_find_start_menu_shortcut(shortcut_id: str) -> Path | None:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，按名称或路径查找开始菜单快捷方式；如果没有这段函数，shortcut 启动器只能依赖外部传绝对路径。
    candidate_text = str(shortcut_id or "").strip()  # 新增代码+WindowsMultiBackendLaunchExecutor：规范化快捷方式标识；如果没有这一行，空格或 None 会干扰匹配。
    if not candidate_text:  # 新增代码+WindowsMultiBackendLaunchExecutor：空标识直接失败；如果没有这一行，后续 Path 可能指向当前目录。
        return None  # 新增代码+WindowsMultiBackendLaunchExecutor：返回未找到；如果没有这一行，空 shortcut 可能被误启动。
    direct_path = Path(candidate_text)  # 新增代码+WindowsMultiBackendLaunchExecutor：允许 resolver 未来直接传入完整快捷方式路径；如果没有这一行，已知路径也要重新扫描。
    if direct_path.exists():  # 新增代码+WindowsMultiBackendLaunchExecutor：检查完整路径是否存在；如果没有这一行，直接路径不会被优先使用。
        return direct_path  # 新增代码+WindowsMultiBackendLaunchExecutor：返回已存在路径；如果没有这一行，真实快捷方式可能被扫描阶段错过。
    wanted_names = {candidate_text.lower(), Path(candidate_text).name.lower(), Path(candidate_text).stem.lower()}  # 新增代码+WindowsMultiBackendLaunchExecutor：准备大小写无关匹配名；如果没有这一行，Obsidian 和 Obsidian.lnk 不能统一匹配。
    for root in _phase110_start_menu_roots():  # 新增代码+WindowsMultiBackendLaunchExecutor：遍历用户和公共开始菜单；如果没有这一行，shortcut 后端没有搜索范围。
        for extension in ("*.lnk", "*.appref-ms"):  # 新增代码+WindowsMultiBackendLaunchExecutor：覆盖常见快捷方式扩展；如果没有这一行，ClickOnce 类 appref-ms 应用会漏掉。
            for shortcut in root.rglob(extension):  # 新增代码+WindowsMultiBackendLaunchExecutor：递归查找快捷方式文件；如果没有这一行，子目录应用无法被发现。
                names = {shortcut.name.lower(), shortcut.stem.lower()}  # 新增代码+WindowsMultiBackendLaunchExecutor：生成当前快捷方式的匹配名；如果没有这一行，只能做脆弱字符串比较。
                if names & wanted_names:  # 新增代码+WindowsMultiBackendLaunchExecutor：判断是否命中目标名称；如果没有这一行，扫描结果不会选中任何快捷方式。
                    return shortcut  # 新增代码+WindowsMultiBackendLaunchExecutor：返回匹配快捷方式路径；如果没有这一行，找到后仍会继续失败。
    return None  # 新增代码+WindowsMultiBackendLaunchExecutor：没有匹配时返回 None；如果没有这一行，调用方无法结构化报告未找到。
# 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，_phase110_find_start_menu_shortcut 到此结束；如果没有这个边界说明，读者不容易看出 shortcut 查找范围。

class Phase110ProductionGenericLaunchBackend:  # 修改代码+WindowsMultiBackendLaunchExecutor：类段开始，定义显式授权后的生产多后端真实启动器；如果没有这个类，成熟版永远停在记录型候选。
    def __init__(self, registry: Phase110OwnedProcessRegistry | None = None, platform: str | None = None, native_launcher: Any | None = None) -> None:  # 修改代码+WindowsMultiBackendLaunchExecutor：函数段开始，初始化生产后端依赖并允许测试注入原生启动器；如果没有这个函数，测试无法隔离真实 Windows API。
        self.registry = registry if registry is not None else Phase110OwnedProcessRegistry()  # 新增代码+GenericLaunchBackendMaturity：保存自有进程登记表；如果没有这一行，真实启动后无法登记 cleanup 责任。
        self.platform = str(platform or sys.platform)  # 新增代码+GenericLaunchBackendMaturity：保存平台名；如果没有这一行，非 Windows 环境无法安全拒绝。
        self.native_launcher = native_launcher if native_launcher is not None else Phase110WindowsNativeLauncher()  # 新增代码+WindowsMultiBackendLaunchExecutor：保存多后端原生启动器；如果没有这一行，生产后端无法分发 AppX/shortcut。
    # 修改代码+WindowsMultiBackendLaunchExecutor：函数段结束，Phase110ProductionGenericLaunchBackend.__init__ 到此结束；如果没有这个边界说明，读者不容易看出初始化范围。

    def _dispatch_native_launch(self, request: GenericLaunchRequest) -> dict[str, Any]:  # 新增代码+WindowsMultiBackendLaunchExecutor：函数段开始，把请求分发到 argv/AppX/shortcut 对应原生启动器；如果没有这段函数，生产后端会继续只有单一路径。
        if request.launch_backend == "argv_no_shell":  # 新增代码+WindowsMultiBackendLaunchExecutor：识别普通 argv 后端；如果没有这一行，exe 应用无法启动。
            return dict(self.native_launcher.launch_argv(request.argv()))  # 新增代码+WindowsMultiBackendLaunchExecutor：调用 argv 原生启动器；如果没有这一行，普通 Win32 应用没有最后一跳。
        if request.launch_backend == "appx_aumid":  # 新增代码+WindowsMultiBackendLaunchExecutor：识别 AppX/AUMID 后端；如果没有这一行，商店应用不会进入正确启动器。
            return dict(self.native_launcher.launch_appx_aumid(request.aumid))  # 新增代码+WindowsMultiBackendLaunchExecutor：调用 AUMID 原生启动器；如果没有这一行，Calculator 等应用会继续失败。
        if request.launch_backend == "start_menu_shortcut":  # 新增代码+WindowsMultiBackendLaunchExecutor：识别开始菜单快捷方式后端；如果没有这一行，快捷方式应用不会进入正确启动器。
            return dict(self.native_launcher.launch_start_menu_shortcut(request.shortcut_id))  # 新增代码+WindowsMultiBackendLaunchExecutor：调用 shortcut 原生启动器；如果没有这一行，只有快捷方式入口的应用无法启动。
        return {"ok": False, "process_started": False, "process_id": 0, "process_object": None, "failure_reason": f"unsupported_launch_backend:{request.launch_backend}"}  # 新增代码+WindowsMultiBackendLaunchExecutor：未知后端结构化失败；如果没有这一行，拼错后端会变成难懂异常。
    # 新增代码+WindowsMultiBackendLaunchExecutor：函数段结束，Phase110ProductionGenericLaunchBackend._dispatch_native_launch 到此结束；如果没有这个边界说明，读者不容易看出分发范围。

    def launch(self, request_like: GenericLaunchRequest | dict[str, Any]) -> dict[str, Any]:  # 修改代码+WindowsMultiBackendLaunchExecutor：函数段开始，按多后端形状真实启动普通应用；如果没有这个函数，生产路径没有最后一跳。
        request = build_generic_launch_request(request_like)  # 新增代码+GenericLaunchBackendMaturity：统一请求形状；如果没有这一行，生产后端可能收到松散字典。
        if not request.real_launch_authorized:  # 新增代码+GenericLaunchBackendMaturity：真实启动必须有显式授权；如果没有这一行，默认路径可能直接启动应用。
            return _phase110_refusal_report(request, "generic_real_launch_requires_authorization", "real_launch_not_authorized")  # 新增代码+GenericLaunchBackendMaturity：无授权零副作用拒绝；如果没有这一行，full gate 会被绕过。
        if not self.platform.startswith("win"):  # 新增代码+GenericLaunchBackendMaturity：只允许 Windows 平台真实启动；如果没有这一行，Linux/macOS 测试可能误跑 exe。
            return _phase110_refusal_report(request, "generic_real_launch_non_windows_rejected", "non_windows_platform_rejected")  # 新增代码+GenericLaunchBackendMaturity：非 Windows 返回结构化拒绝；如果没有这一行，平台错误会变成异常。
        if not phase110_safe_launch_request(request):  # 修改代码+WindowsMultiBackendLaunchExecutor：生产后端再次复核多后端安全计划；如果没有这一行，调用方 bug 可能触发危险启动。
            return _phase110_refusal_report(request, "unsafe_generic_launch_plan_rejected", "unsafe_launch_plan_rejected_by_backend")  # 新增代码+GenericLaunchBackendMaturity：危险计划零副作用拒绝；如果没有这一行，高风险目标可能进入启动器。
        try:  # 新增代码+GenericLaunchBackendMaturity：捕获真实启动异常并转成结构化失败；如果没有这一行，启动失败会打断整个 agent。
            launcher_result = self._dispatch_native_launch(request)  # 新增代码+WindowsMultiBackendLaunchExecutor：调用多后端原生启动器；如果没有这一行，安全请求不会真正发给 Windows。
        except Exception as error:  # 新增代码+GenericLaunchBackendMaturity：捕获所有启动异常并保留类型；如果没有这一行，文件不存在等错误会直接冒泡。
            return GenericLaunchResult(ok=False, decision="generic_launch_backend_failed", backend="phase110_production_generic_launch_backend", process_started=False, process_id=0, process_executable=request.launch_identity(), argv=tuple(request.argv()), launch_backend=request.launch_backend, command_shape=request.command_shape, real_desktop_touched=False, cleanup_registered=False, owned_process_registered=False, failure_reason=f"{type(error).__name__}:{error}").to_report()  # 修改代码+WindowsMultiBackendLaunchExecutor：返回包含后端身份的结构化异常原因；如果没有这一行，用户看不到为什么非 argv 启动失败。
        if not launcher_result.get("ok"):  # 新增代码+WindowsMultiBackendLaunchExecutor：检查原生启动器是否报告失败；如果没有这一行，ShellExecute 失败可能被误认为启动成功。
            return GenericLaunchResult(ok=False, decision="generic_launch_backend_failed", backend="phase110_production_generic_launch_backend", process_started=False, process_id=0, process_executable=request.launch_identity(), argv=tuple(request.argv()), launch_backend=request.launch_backend, command_shape=request.command_shape, real_desktop_touched=False, cleanup_registered=False, owned_process_registered=False, failure_reason=str(launcher_result.get("failure_reason", "native_launcher_failed"))).to_report()  # 新增代码+WindowsMultiBackendLaunchExecutor：返回原生启动器失败原因；如果没有这一行，AppX/shortcut 失败会没有诊断。
        process_id = int(launcher_result.get("process_id", 0) or 0)  # 修改代码+WindowsMultiBackendLaunchExecutor：从统一 launcher 结果读取 pid；如果没有这一行，窗口身份绑定没有进程基准。
        process_object = launcher_result.get("process_object")  # 新增代码+WindowsMultiBackendLaunchExecutor：读取可选进程对象；如果没有这一行，argv 后端无法继续用 Popen 对象做 cleanup。
        owned_record = self.registry.register(process_id, request.launch_identity(), request.argv(), process_object=process_object) if process_id > 0 else {}  # 修改代码+WindowsMultiBackendLaunchExecutor：只有拿到 pid 才登记自有资源；如果没有这一行，pid 为 0 的 ShellExecute 结果会伪造成可清理进程。
        return GenericLaunchResult(ok=True, decision="generic_launch_production_backend_started_owned_process", backend="phase110_production_generic_launch_backend", process_started=bool(launcher_result.get("process_started", False)), process_id=process_id, process_executable=request.launch_identity(), argv=tuple(request.argv()), launch_backend=request.launch_backend, command_shape=request.command_shape, real_desktop_touched=True, cleanup_registered=bool(owned_record.get("cleanup_registered")), owned_process_registered=bool(owned_record)).to_report()  # 修改代码+WindowsMultiBackendLaunchExecutor：返回生产启动摘要并暴露实际启动后端；如果没有这一行，上层无法知道真实桌面已被触碰以及 AppX/shortcut 是否接通。
    # 修改代码+WindowsMultiBackendLaunchExecutor：函数段结束，Phase110ProductionGenericLaunchBackend.launch 到此结束；如果没有这个边界说明，读者不容易看出生产启动范围。
# 修改代码+WindowsMultiBackendLaunchExecutor：类段结束，Phase110ProductionGenericLaunchBackend 到此结束；如果没有这个边界说明，代码小白不容易看出生产后端范围。

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
    appx_registry = Phase110OwnedProcessRegistry()  # 新增代码+WindowsMultiBackendLaunchExecutor：创建 AppX 记录型 registry；如果没有这一行，AUMID 后端无法验证 ownership。
    appx_backend = Phase110RecordingGenericLaunchBackend(registry=appx_registry)  # 新增代码+WindowsMultiBackendLaunchExecutor：创建 AppX 记录型后端；如果没有这一行，合同可能真的触碰用户计算器。
    appx_enabled = run_generic_launch_backend(phase110_contract_appx_phase108_report(), enable_real_launch=True, backend=appx_backend)  # 新增代码+WindowsMultiBackendLaunchExecutor：运行授权 AppX 样本；如果没有这一行，AUMID 路线不会进入成熟矩阵。
    shortcut_registry = Phase110OwnedProcessRegistry()  # 新增代码+WindowsMultiBackendLaunchExecutor：创建 shortcut 记录型 registry；如果没有这一行，快捷方式后端无法验证 ownership。
    shortcut_backend = Phase110RecordingGenericLaunchBackend(registry=shortcut_registry)  # 新增代码+WindowsMultiBackendLaunchExecutor：创建 shortcut 记录型后端；如果没有这一行，合同可能真的打开用户应用。
    shortcut_enabled = run_generic_launch_backend(phase110_contract_shortcut_phase108_report(), enable_real_launch=True, backend=shortcut_backend)  # 新增代码+WindowsMultiBackendLaunchExecutor：运行授权 shortcut 样本；如果没有这一行，快捷方式路线不会进入成熟矩阵。
    default_off_zero_events = bool(default_off.get("default_off_backend_not_called") and len(default_backend.launches) == 0 and not default_off.get("real_desktop_touched"))  # 新增代码+GenericLaunchBackendMaturity：汇总默认关闭零副作用；如果没有这一行，默认安全无法量化。
    authorized_argv_backend = bool(enabled.get("backend_launch_reaches_launcher") and len(enabled_backend.launches) == 1 and enabled_backend.launches[0].get("command_shape") == "argv_no_shell")  # 新增代码+GenericLaunchBackendMaturity：汇总授权 argv 后端路径；如果没有这一行，最后一跳安全形状不清楚。
    authorized_appx_backend = bool(appx_enabled.get("backend_launch_reaches_launcher") and len(appx_backend.launches) == 1 and appx_backend.launches[0].get("launch_backend") == "appx_aumid" and appx_backend.launches[0].get("argv") == [])  # 新增代码+WindowsMultiBackendLaunchExecutor：汇总授权 AppX 后端路径；如果没有这一行，矩阵无法发现 AUMID 被退回 argv。
    authorized_shortcut_backend = bool(shortcut_enabled.get("backend_launch_reaches_launcher") and len(shortcut_backend.launches) == 1 and shortcut_backend.launches[0].get("launch_backend") == "start_menu_shortcut" and shortcut_backend.launches[0].get("argv") == [])  # 新增代码+WindowsMultiBackendLaunchExecutor：汇总授权 shortcut 后端路径；如果没有这一行，矩阵无法发现快捷方式被退回 argv。
    unsafe_refused_before_backend = bool(unsafe.get("decision") == "unsafe_generic_launch_plan_rejected" and len(unsafe_backend.launches) == 0 and not unsafe.get("real_desktop_touched"))  # 新增代码+GenericLaunchBackendMaturity：汇总危险路径后端前拒绝；如果没有这一行，拒绝是否零副作用不可见。
    owned_process_registered = bool(enabled.get("owned_process_registered") and len(enabled_registry.owned_processes) == 1 and enabled_registry.owned_processes[0].get("cleanup_registered") and appx_enabled.get("owned_process_registered") and shortcut_enabled.get("owned_process_registered"))  # 修改代码+WindowsMultiBackendLaunchExecutor：汇总三种后端都登记自有资源；如果没有这一行，AppX/shortcut 可能没有 cleanup 责任还被误判成熟。
    launch_failure_structured_reason = bool(not failure.get("ok") and failure.get("decision") == "generic_launch_backend_failed" and failure.get("failure_reason"))  # 新增代码+GenericLaunchBackendMaturity：汇总结构化失败原因；如果没有这一行，启动失败可能沉默。
    multi_backend_dispatch_ready = bool(authorized_argv_backend and authorized_appx_backend and authorized_shortcut_backend)  # 新增代码+WindowsMultiBackendLaunchExecutor：汇总三种后端分发是否都通过；如果没有这一行，终端只能看到零散字段。
    passed = bool(default_off_zero_events and multi_backend_dispatch_ready and unsafe_refused_before_backend and owned_process_registered and launch_failure_structured_reason and not PHASE110_UNCONTROLLED_ACTIONS_EXPANDED)  # 修改代码+WindowsMultiBackendLaunchExecutor：计算多后端合同是否通过；如果没有这一行，CLI 无法用退出码表达 AppX/shortcut 失败。
    return {"marker": PHASE110_GENERIC_LAUNCH_BACKEND_MARKER, "ok_token": PHASE110_GENERIC_LAUNCH_BACKEND_OK_TOKEN, "model": PHASE110_GENERIC_LAUNCH_BACKEND_MODEL, "passed": passed, "generic_launch_backend_ready": True, "generic_real_launch_default_enabled": False, "generic_real_launch_enabled_when_authorized": multi_backend_dispatch_ready, "default_off_zero_events": default_off_zero_events, "authorized_argv_backend": authorized_argv_backend, "authorized_appx_backend": authorized_appx_backend, "authorized_shortcut_backend": authorized_shortcut_backend, "multi_backend_dispatch_ready": multi_backend_dispatch_ready, "unsafe_refused_before_backend": unsafe_refused_before_backend, "owned_process_registered": owned_process_registered, "launch_failure_structured_reason": launch_failure_structured_reason, "real_desktop_touched": False, "uncontrolled_actions_expanded": PHASE110_UNCONTROLLED_ACTIONS_EXPANDED, "default_off_report": default_off, "enabled_report": enabled, "appx_report": appx_enabled, "shortcut_report": shortcut_enabled, "unsafe_report": unsafe, "failure_report": failure}  # 修改代码+WindowsMultiBackendLaunchExecutor：返回完整多后端合同报告；如果没有这一行，测试、CLI 和最终矩阵无法共享 AppX/shortcut 事实。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，run_phase110_generic_launch_backend_contract 到此结束；如果没有这个边界说明，代码小白不容易看出合同范围。

def phase110_cli_line(report: dict[str, Any]) -> str:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，把 Task 2 报告转成稳定 token 行；如果没有这个函数，真实终端验收只能解析复杂 JSON。
    ok_token = f" {PHASE110_GENERIC_LAUNCH_BACKEND_OK_TOKEN}" if bool(report.get("passed", False)) else ""  # 新增代码+GenericLaunchBackendMaturity：只在合同通过时展示 OK token；如果没有这一行，失败报告可能被误判为成功。
    return f"{PHASE110_GENERIC_LAUNCH_BACKEND_MARKER}{ok_token} generic_launch_backend_ready={_phase110_bool_token(report.get('generic_launch_backend_ready', False))} generic_real_launch_default_enabled={_phase110_bool_token(report.get('generic_real_launch_default_enabled', True))} generic_real_launch_enabled_when_authorized={_phase110_bool_token(report.get('generic_real_launch_enabled_when_authorized', False))} default_off_zero_events={_phase110_bool_token(report.get('default_off_zero_events', False))} authorized_argv_backend={_phase110_bool_token(report.get('authorized_argv_backend', False))} authorized_appx_backend={_phase110_bool_token(report.get('authorized_appx_backend', False))} authorized_shortcut_backend={_phase110_bool_token(report.get('authorized_shortcut_backend', False))} multi_backend_dispatch_ready={_phase110_bool_token(report.get('multi_backend_dispatch_ready', False))} unsafe_refused_before_backend={_phase110_bool_token(report.get('unsafe_refused_before_backend', False))} owned_process_registered={_phase110_bool_token(report.get('owned_process_registered', False))} launch_failure_structured_reason={_phase110_bool_token(report.get('launch_failure_structured_reason', False))} real_desktop_touched={_phase110_bool_token(report.get('real_desktop_touched', False))} uncontrolled_actions_expanded={_phase110_bool_token(report.get('uncontrolled_actions_expanded', False))}"  # 修改代码+WindowsMultiBackendLaunchExecutor：返回固定顺序多后端 token 行；如果没有这一行，真实终端无法稳定断言 AppX/shortcut 后端接通。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，phase110_cli_line 到此结束；如果没有这个边界说明，代码小白不容易看出 CLI 输出范围。

def main(argv: list[str] | None = None) -> int:  # 新增代码+GenericLaunchBackendMaturity：函数段开始，提供命令行自检入口；如果没有这个函数，用户不能直接运行模块查看 Task 2 合同。
    _ = argv  # 新增代码+GenericLaunchBackendMaturity：保留 argv 扩展位；如果没有这一行，读者可能误以为参数被遗漏。
    report = run_phase110_generic_launch_backend_contract()  # 新增代码+GenericLaunchBackendMaturity：运行无真实桌面副作用合同；如果没有这一行，CLI 没有事实来源。
    print(phase110_cli_line(report))  # 新增代码+GenericLaunchBackendMaturity：打印稳定 token 行；如果没有这一行，真实终端验收无法快速匹配。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+GenericLaunchBackendMaturity：打印完整 JSON 报告；如果没有这一行，失败排查缺少细节。
    return 0 if bool(report.get("passed", False)) else 1  # 新增代码+GenericLaunchBackendMaturity：按合同结果返回退出码；如果没有这一行，自动化无法区分成功和失败。
# 新增代码+GenericLaunchBackendMaturity：函数段结束，main 到此结束；如果没有这个边界说明，代码小白不容易看出命令行入口范围。

__all__ = ["GenericLaunchRequest", "GenericLaunchResult", "PHASE110_GENERIC_LAUNCH_BACKEND_MARKER", "PHASE110_GENERIC_LAUNCH_BACKEND_MODEL", "PHASE110_GENERIC_LAUNCH_BACKEND_OK_TOKEN", "PHASE110_REAL_LAUNCH_DEFAULT_DISABLED", "PHASE110_UNCONTROLLED_ACTIONS_EXPANDED", "Phase110FailingGenericLaunchBackend", "Phase110OwnedProcessRegistry", "Phase110ProductionGenericLaunchBackend", "Phase110RecordingGenericLaunchBackend", "Phase110WindowsNativeLauncher", "build_generic_launch_request", "main", "phase110_cli_line", "phase110_contract_appx_phase108_report", "phase110_contract_safe_phase108_report", "phase110_contract_shortcut_phase108_report", "phase110_contract_unsafe_phase108_report", "phase110_safe_launch_request", "run_generic_launch_backend", "run_phase110_generic_launch_backend_contract"]  # 修改代码+WindowsMultiBackendLaunchExecutor：限定公开导出名称并暴露多后端样本和原生启动器；如果没有这一行，测试和后续模块无法稳定复用新执行器。

if __name__ == "__main__":  # 新增代码+GenericLaunchBackendMaturity：文件入口段开始，允许直接运行本模块；如果没有这一行，python 文件方式不会执行自检。
    raise SystemExit(main())  # 新增代码+GenericLaunchBackendMaturity：用 main 返回码退出；如果没有这一行，命令行状态不明确。
# 新增代码+GenericLaunchBackendMaturity：文件入口段结束，直接运行模块到此结束；如果没有这个边界说明，读者不容易看出脚本入口范围。
