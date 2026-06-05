"""Computer Use full 模式的自有资源注册、清理和残留检查。"""  # 新增代码+CleanupRecoveryMaturity：说明本模块只管理 agent 自己登记的资源；如果没有这一行，用户不容易区分自有资源和用户已有窗口。
from __future__ import annotations  # 新增代码+CleanupRecoveryMaturity：启用延迟类型注解解析；如果没有这一行，回调类型在旧导入顺序下更容易出问题。

import json  # 新增代码+CleanupRecoveryMaturity：用于 CLI 自检输出完整 JSON；如果没有这一行，失败排查只能看短 token。
import time  # 新增代码+CleanupRecoveryMaturity：用于默认生成 UTC 创建时间；如果没有这一行，注册记录缺少审计时间。
from typing import Any, Callable  # 新增代码+CleanupRecoveryMaturity：描述动态记录和清理/残留回调；如果没有这一行，接口输入输出类型不清楚。

PHASE112_OWNED_RESOURCE_REGISTRY_MARKER = "PHASE112_OWNED_RESOURCE_REGISTRY_READY"  # 新增代码+CleanupRecoveryMaturity：定义 Task 4 ready marker；如果没有这一行，终端验收无法稳定定位注册表输出。
PHASE112_OWNED_RESOURCE_REGISTRY_OK_TOKEN = "PHASE112_OWNED_RESOURCE_REGISTRY_OK"  # 新增代码+CleanupRecoveryMaturity：定义 Task 4 成功 token；如果没有这一行，脚本和人工验收难以区分通过与普通输出。
PHASE112_OWNED_RESOURCE_REGISTRY_MODEL = "phase112_owned_resource_registry"  # 新增代码+CleanupRecoveryMaturity：定义报告模型名；如果没有这一行，最终矩阵无法区分清理注册表版本。
PHASE112_UNCONTROLLED_ACTIONS_EXPANDED = False  # 新增代码+CleanupRecoveryMaturity：声明注册表不扩大真实动作面；如果没有这一行，用户可能误以为清理模块可以任意关闭窗口。
CleanupCallback = Callable[[dict[str, Any]], Any]  # 新增代码+CleanupRecoveryMaturity：定义清理回调类型；如果没有这一行，注册方法参数含义不清楚。
ResidualCheckCallback = Callable[[dict[str, Any]], bool]  # 新增代码+CleanupRecoveryMaturity：定义残留检查回调类型；如果没有这一行，残留检查接口含义不清楚。


# 新增代码+CleanupRecoveryMaturity：函数段落开始，phase112_utc_timestamp 生成注册时间；如果没有这个函数，记录创建时间会散落重复。
def phase112_utc_timestamp() -> str:  # 新增代码+CleanupRecoveryMaturity：定义 UTC 时间 helper；如果没有这一行，注册表无法默认生成 created_at。
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # 新增代码+CleanupRecoveryMaturity：返回稳定 UTC 字符串；如果没有这一行，审计记录没有时间戳。
# 新增代码+CleanupRecoveryMaturity：函数段落结束，phase112_utc_timestamp 到此结束；如果没有这个边界说明，用户不容易看出时间 helper 范围。


# 新增代码+CleanupRecoveryMaturity：函数段落开始，_phase112_bool_token 格式化布尔输出；如果没有这个函数，CLI token 可能出现 True/False 漂移。
def _phase112_bool_token(value: Any) -> str:  # 新增代码+CleanupRecoveryMaturity：定义布尔 token helper；如果没有这一行，多个 CLI 字段会重复格式化。
    return "true" if bool(value) else "false"  # 新增代码+CleanupRecoveryMaturity：返回小写 true/false；如果没有这一行，终端验收不易稳定匹配。
# 新增代码+CleanupRecoveryMaturity：函数段落结束，_phase112_bool_token 到此结束；如果没有这个边界说明，用户不容易看出布尔格式化范围。


# 新增代码+CleanupRecoveryMaturity：函数段落开始，_phase112_int 安全读取 pid；如果没有这个函数，坏 pid 字段会让清理注册崩溃。
def _phase112_int(value: Any, default: int = 0) -> int:  # 新增代码+CleanupRecoveryMaturity：定义容错整数转换；如果没有这一行，字符串 pid 不能稳定参与记录。
    try:  # 新增代码+CleanupRecoveryMaturity：尝试执行 int 转换；如果没有这一行，转换失败无法兜底。
        return int(value)  # 新增代码+CleanupRecoveryMaturity：返回转换后的整数；如果没有这一行，调用方拿不到数字 pid。
    except (TypeError, ValueError):  # 新增代码+CleanupRecoveryMaturity：捕获 None、空串和非数字文本；如果没有这一行，坏输入会中断注册流程。
        return default  # 新增代码+CleanupRecoveryMaturity：失败时返回默认值；如果没有这一行，注册表无法用 0 表示缺失 pid。
# 新增代码+CleanupRecoveryMaturity：函数段落结束，_phase112_int 到此结束；如果没有这个边界说明，用户不容易看出 pid 转换范围。


# 新增代码+CleanupRecoveryMaturity：类段落开始，OwnedResourceRegistry 管理本 session 自有进程和窗口；如果没有这个类，stop/abort 无法知道只清理谁。
class OwnedResourceRegistry:  # 新增代码+CleanupRecoveryMaturity：定义自有资源注册表；如果没有这一行，蓝图 Task 4 没有核心实现。
    # 新增代码+CleanupRecoveryMaturity：函数段落开始，__init__ 初始化注册表状态；如果没有这段函数，注册表没有 session、时间源和记录容器。
    def __init__(self, session_id: str = "learning-agent-default-session", clock: Callable[[], str] | None = None) -> None:  # 新增代码+CleanupRecoveryMaturity：定义注册表初始化入口；如果没有这一行，测试和 runtime 不能创建 registry。
        self.session_id = str(session_id or "learning-agent-default-session")  # 新增代码+CleanupRecoveryMaturity：保存默认 session id；如果没有这一行，跨会话清理无法隔离。
        self.clock = clock if clock is not None else phase112_utc_timestamp  # 新增代码+CleanupRecoveryMaturity：保存可注入时间源；如果没有这一行，测试无法稳定断言 created_at。
        self.records: list[dict[str, Any]] = []  # 新增代码+CleanupRecoveryMaturity：保存所有资源记录；如果没有这一行，注册表没有主体状态。
        self._cleanup_callbacks: dict[str, CleanupCallback] = {}  # 新增代码+CleanupRecoveryMaturity：保存清理回调；如果没有这一行，cleanup 只能改状态不能调用真实或测试清理。
        self._residual_callbacks: dict[str, ResidualCheckCallback] = {}  # 新增代码+CleanupRecoveryMaturity：保存残留检查回调；如果没有这一行，registry 无法证明资源是否仍存在。
        self.model = PHASE112_OWNED_RESOURCE_REGISTRY_MODEL  # 新增代码+CleanupRecoveryMaturity：保存模型名；如果没有这一行，报告无法说明注册表版本。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，OwnedResourceRegistry.__init__ 到此结束；如果没有这个边界说明，用户不容易看出初始化范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，_next_registry_id 生成资源记录 id；如果没有这个函数，回调映射没有稳定 key。
    def _next_registry_id(self, resource_type: str) -> str:  # 新增代码+CleanupRecoveryMaturity：定义资源 id 生成 helper；如果没有这一行，记录和回调无法可靠关联。
        return f"{resource_type}:{len(self.records) + 1}"  # 新增代码+CleanupRecoveryMaturity：按记录顺序生成 id；如果没有这一行，回调映射会缺少 key。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，_next_registry_id 到此结束；如果没有这个边界说明，用户不容易看出 registry id 规则。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，_register_resource 统一登记进程、窗口和受保护用户窗口；如果没有这个函数，三个登记入口会重复且容易字段不一致。
    def _register_resource(self, *, resource_type: str, session_id: str | None = None, process_id: int = 0, window_id: str = "", owned_by_agent: bool = True, executable: str = "", title_preview: str = "", cleanup_callback: CleanupCallback | None = None, residual_check_callback: ResidualCheckCallback | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+CleanupRecoveryMaturity：定义统一登记入口；如果没有这一行，必需字段无法集中保证。
        registry_id = self._next_registry_id(resource_type)  # 新增代码+CleanupRecoveryMaturity：生成本条记录 id；如果没有这一行，回调无法与记录对应。
        record = {"registry_id": registry_id, "model": self.model, "session_id": str(session_id or self.session_id), "resource_type": str(resource_type), "process_id": _phase112_int(process_id), "window_id": str(window_id or ""), "created_at": self.clock(), "cleanup_state": "registered" if owned_by_agent else "preserved_user_resource", "residual_check_state": "unchecked" if owned_by_agent else "not_owned", "owned_by_agent": bool(owned_by_agent), "executable": str(executable or ""), "title_preview": str(title_preview or ""), "metadata": dict(metadata or {})}  # 新增代码+CleanupRecoveryMaturity：构造完整资源记录；如果没有这一行，注册表缺少蓝图要求字段。
        self.records.append(record)  # 新增代码+CleanupRecoveryMaturity：保存记录到注册表；如果没有这一行，后续 cleanup/check 找不到资源。
        if cleanup_callback is not None and owned_by_agent:  # 新增代码+CleanupRecoveryMaturity：只给自有资源保存清理回调；如果没有这一行，用户已有窗口也可能被清理。
            self._cleanup_callbacks[registry_id] = cleanup_callback  # 新增代码+CleanupRecoveryMaturity：登记清理回调；如果没有这一行，cleanup 无法触发实际收尾。
        if residual_check_callback is not None and owned_by_agent:  # 新增代码+CleanupRecoveryMaturity：只给自有资源保存残留检查；如果没有这一行，用户已有窗口可能参与失败判断。
            self._residual_callbacks[registry_id] = residual_check_callback  # 新增代码+CleanupRecoveryMaturity：登记残留检查回调；如果没有这一行，check_residuals 无法获得真实状态。
        return record  # 新增代码+CleanupRecoveryMaturity：返回记录供调用方保存或断言；如果没有这一行，测试和上层拿不到登记结果。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，_register_resource 到此结束；如果没有这个边界说明，用户不容易看出统一登记范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，register_owned_process 登记 agent 自己启动的进程；如果没有这个函数，进程级 cleanup 没有入口。
    def register_owned_process(self, process_id: int, executable: str = "", *, session_id: str | None = None, cleanup_callback: CleanupCallback | None = None, residual_check_callback: ResidualCheckCallback | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+CleanupRecoveryMaturity：定义自有进程登记入口；如果没有这一行，启动后端无法登记清理责任。
        return self._register_resource(resource_type="process", session_id=session_id, process_id=process_id, window_id="", owned_by_agent=True, executable=executable, cleanup_callback=cleanup_callback, residual_check_callback=residual_check_callback, metadata=metadata)  # 新增代码+CleanupRecoveryMaturity：返回自有进程记录；如果没有这一行，进程不会进入 cleanup/residual 流程。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，register_owned_process 到此结束；如果没有这个边界说明，用户不容易看出进程登记范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，register_owned_window 登记 agent 自己创建或验证的窗口；如果没有这个函数，窗口级 cleanup 没有入口。
    def register_owned_window(self, window_id: str, process_id: int = 0, *, session_id: str | None = None, cleanup_callback: CleanupCallback | None = None, residual_check_callback: ResidualCheckCallback | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+CleanupRecoveryMaturity：定义自有窗口登记入口；如果没有这一行，目标窗口无法进入清理责任。
        return self._register_resource(resource_type="window", session_id=session_id, process_id=process_id, window_id=window_id, owned_by_agent=True, cleanup_callback=cleanup_callback, residual_check_callback=residual_check_callback, metadata=metadata)  # 新增代码+CleanupRecoveryMaturity：返回自有窗口记录；如果没有这一行，窗口不会进入 cleanup/residual 流程。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，register_owned_window 到此结束；如果没有这个边界说明，用户不容易看出窗口登记范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，register_user_preexisting_window 标记用户已有窗口应被保护；如果没有这个函数，同应用旧窗口可能被当成可清理对象。
    def register_user_preexisting_window(self, window_id: str, process_id: int = 0, *, session_id: str | None = None, title_preview: str = "", metadata: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+CleanupRecoveryMaturity：定义用户已有窗口登记入口；如果没有这一行，保护窗口没有结构化记录。
        return self._register_resource(resource_type="window", session_id=session_id, process_id=process_id, window_id=window_id, owned_by_agent=False, title_preview=title_preview, metadata=metadata)  # 新增代码+CleanupRecoveryMaturity：返回受保护用户窗口记录；如果没有这一行，cleanup 无法报告保留了用户窗口。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，register_user_preexisting_window 到此结束；如果没有这个边界说明，用户不容易看出用户窗口保护范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，records_for_session 读取某个 session 的记录；如果没有这个函数，stop/abort 可能跨会话清理。
    def records_for_session(self, session_id: str | None = None) -> list[dict[str, Any]]:  # 新增代码+CleanupRecoveryMaturity：定义按 session 过滤入口；如果没有这一行，调用方需要重复写过滤逻辑。
        target_session_id = str(session_id or self.session_id)  # 新增代码+CleanupRecoveryMaturity：确定目标 session；如果没有这一行，None session 会造成匹配混乱。
        return [record for record in self.records if record.get("session_id") == target_session_id]  # 新增代码+CleanupRecoveryMaturity：返回该 session 的记录列表；如果没有这一行，cleanup 无法隔离会话。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，records_for_session 到此结束；如果没有这个边界说明，用户不容易看出会话过滤范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，cleanup_owned_resources 清理本 session 自有资源；如果没有这个函数，stop 只能清锁不能清进程/窗口。
    def cleanup_owned_resources(self, session_id: str | None = None, reason: str = "cleanup") -> dict[str, Any]:  # 新增代码+CleanupRecoveryMaturity：定义自有资源清理入口；如果没有这一行，session runtime 没有 registry cleanup API。
        target_records = self.records_for_session(session_id)  # 新增代码+CleanupRecoveryMaturity：读取本 session 记录；如果没有这一行，清理范围可能跨会话。
        cleaned_count = 0  # 新增代码+CleanupRecoveryMaturity：初始化清理数量；如果没有这一行，结果无法汇总清理了多少资源。
        failed_count = 0  # 新增代码+CleanupRecoveryMaturity：初始化失败数量；如果没有这一行，结果无法判断是否全部完成。
        preserved_count = 0  # 新增代码+CleanupRecoveryMaturity：初始化用户资源保留数量；如果没有这一行，报告无法证明保护了用户窗口。
        for record in target_records:  # 新增代码+CleanupRecoveryMaturity：遍历目标 session 记录；如果没有这一行，cleanup 不会处理任何资源。
            if not record.get("owned_by_agent", False):  # 新增代码+CleanupRecoveryMaturity：跳过非自有资源；如果没有这一行，用户已有窗口可能被关闭。
                record["cleanup_state"] = "preserved_user_resource"  # 新增代码+CleanupRecoveryMaturity：标记用户资源被保留；如果没有这一行，保护结果不可见。
                preserved_count += 1  # 新增代码+CleanupRecoveryMaturity：累计保留数量；如果没有这一行，汇总无法显示保护了多少窗口。
                continue  # 新增代码+CleanupRecoveryMaturity：继续处理下一条记录；如果没有这一行，非自有资源可能继续落入清理回调。
            if record.get("cleanup_state") == "cleanup_completed":  # 新增代码+CleanupRecoveryMaturity：跳过已清理资源；如果没有这一行，重复 stop 可能重复关闭同一资源。
                continue  # 新增代码+CleanupRecoveryMaturity：继续处理下一条记录；如果没有这一行，已清理资源会被重复调用回调。
            callback = self._cleanup_callbacks.get(str(record.get("registry_id", "")))  # 新增代码+CleanupRecoveryMaturity：读取该资源清理回调；如果没有这一行，cleanup 不能触发实际收尾。
            try:  # 新增代码+CleanupRecoveryMaturity：保护清理回调异常；如果没有这一行，一个失败回调会中断全部清理。
                callback_result = callback(record) if callback is not None else True  # 新增代码+CleanupRecoveryMaturity：调用回调或默认视为可清理；如果没有这一行，自有资源状态不会推进。
                record["cleanup_state"] = "cleanup_completed" if callback_result is not False else "cleanup_failed"  # 新增代码+CleanupRecoveryMaturity：根据回调结果更新状态；如果没有这一行，清理成功/失败不可审计。
            except Exception as error:  # 新增代码+CleanupRecoveryMaturity：捕获清理异常；如果没有这一行，清理失败会变成未结构化崩溃。
                record["cleanup_state"] = "cleanup_failed"  # 新增代码+CleanupRecoveryMaturity：异常时标记清理失败；如果没有这一行，残留风险不可见。
                record["cleanup_error"] = f"{type(error).__name__}:{error}"  # 新增代码+CleanupRecoveryMaturity：保存结构化错误摘要；如果没有这一行，用户不知道清理为什么失败。
            cleaned_count += 1 if record.get("cleanup_state") == "cleanup_completed" else 0  # 新增代码+CleanupRecoveryMaturity：累计成功清理数量；如果没有这一行，结果无法量化清理效果。
            failed_count += 1 if record.get("cleanup_state") == "cleanup_failed" else 0  # 新增代码+CleanupRecoveryMaturity：累计失败数量；如果没有这一行，结果无法判断是否有风险。
        cleanup_completed = failed_count == 0  # 新增代码+CleanupRecoveryMaturity：只要没有失败就认为 cleanup 流程完成；如果没有这一行，上层没有单一成功字段。
        return {"marker": PHASE112_OWNED_RESOURCE_REGISTRY_MARKER, "model": self.model, "decision": "owned_resource_cleanup_completed" if cleanup_completed else "owned_resource_cleanup_failed", "cleanup_completed": cleanup_completed, "cleaned_resource_count": cleaned_count, "cleanup_failed_count": failed_count, "preexisting_user_windows_preserved": preserved_count > 0, "preserved_user_window_count": preserved_count, "reason": reason, "records": [dict(record) for record in target_records], "real_desktop_touched": False, "uncontrolled_actions_expanded": PHASE112_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+CleanupRecoveryMaturity：返回清理摘要；如果没有这一行，runtime 和终端无法展示清理事实。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，cleanup_owned_resources 到此结束；如果没有这个边界说明，用户不容易看出自有清理范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，check_residuals 检查自有资源是否仍残留；如果没有这个函数，cleanup 后无法证明没有留下自己启动的进程。
    def check_residuals(self, session_id: str | None = None) -> dict[str, Any]:  # 新增代码+CleanupRecoveryMaturity：定义残留检查入口；如果没有这一行，上层无法触发 residual gate。
        target_records = self.records_for_session(session_id)  # 新增代码+CleanupRecoveryMaturity：读取本 session 记录；如果没有这一行，残留检查可能跨会话。
        residual_owned_process = False  # 新增代码+CleanupRecoveryMaturity：初始化进程残留标记；如果没有这一行，结果无法区分进程残留。
        residual_owned_window = False  # 新增代码+CleanupRecoveryMaturity：初始化窗口残留标记；如果没有这一行，结果无法区分窗口残留。
        for record in target_records:  # 新增代码+CleanupRecoveryMaturity：遍历目标记录；如果没有这一行，残留检查不会处理任何资源。
            if not record.get("owned_by_agent", False):  # 新增代码+CleanupRecoveryMaturity：跳过用户已有资源；如果没有这一行，用户窗口可能被误判为 agent 残留。
                record["residual_check_state"] = "not_owned"  # 新增代码+CleanupRecoveryMaturity：标记非自有资源不参与检查；如果没有这一行，审计状态不清楚。
                continue  # 新增代码+CleanupRecoveryMaturity：继续下一条记录；如果没有这一行，非自有资源可能进入残留回调。
            callback = self._residual_callbacks.get(str(record.get("registry_id", "")))  # 新增代码+CleanupRecoveryMaturity：读取残留检查回调；如果没有这一行，registry 无法知道资源是否仍存在。
            residual_present = bool(callback(record)) if callback is not None else False  # 新增代码+CleanupRecoveryMaturity：调用回调或默认无残留；如果没有这一行，残留状态不会被计算。
            record["residual_check_state"] = "residual_present" if residual_present else "residual_absent"  # 新增代码+CleanupRecoveryMaturity：更新残留状态；如果没有这一行，哪个资源残留不可见。
            residual_owned_process = residual_owned_process or bool(residual_present and record.get("resource_type") == "process")  # 新增代码+CleanupRecoveryMaturity：汇总自有进程残留；如果没有这一行，进程残留不会触发失败。
            residual_owned_window = residual_owned_window or bool(residual_present and record.get("resource_type") == "window")  # 新增代码+CleanupRecoveryMaturity：汇总自有窗口残留；如果没有这一行，窗口残留不会触发失败。
        residual_check_passed = not residual_owned_process and not residual_owned_window  # 新增代码+CleanupRecoveryMaturity：计算残留检查是否通过；如果没有这一行，上层没有单一通过字段。
        return {"marker": PHASE112_OWNED_RESOURCE_REGISTRY_MARKER, "model": self.model, "decision": "residual_check_passed" if residual_check_passed else "residual_check_failed", "residual_check_passed": residual_check_passed, "residual_owned_process": residual_owned_process, "residual_owned_window": residual_owned_window, "records": [dict(record) for record in target_records], "real_desktop_touched": False, "uncontrolled_actions_expanded": PHASE112_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+CleanupRecoveryMaturity：返回残留检查摘要；如果没有这一行，cleanup 后无法给出成熟度证据。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，check_residuals 到此结束；如果没有这个边界说明，用户不容易看出残留检查范围。

    # 新增代码+CleanupRecoveryMaturity：函数段落开始，abort_cleanup 封装急停清理；如果没有这个函数，abort 只能置 flag 不能收尾自有资源。
    def abort_cleanup(self, session_id: str | None = None, reason: str = "abort") -> dict[str, Any]:  # 新增代码+CleanupRecoveryMaturity：定义 abort 清理入口；如果没有这一行，runtime 急停没有 registry API。
        cleanup = self.cleanup_owned_resources(session_id=session_id, reason=reason)  # 新增代码+CleanupRecoveryMaturity：先清理自有资源；如果没有这一行，急停后可能留下 agent 自己启动的进程。
        residual = self.check_residuals(session_id=session_id)  # 新增代码+CleanupRecoveryMaturity：再检查是否残留；如果没有这一行，abort 无法证明清理结果。
        cleanup_completed = bool(cleanup.get("cleanup_completed") and residual.get("residual_check_passed"))  # 新增代码+CleanupRecoveryMaturity：合并清理和残留检查结果；如果没有这一行，上层可能只看清理调用忽略残留。
        return {"marker": PHASE112_OWNED_RESOURCE_REGISTRY_MARKER, "model": self.model, "decision": "abort_cleanup_completed" if cleanup_completed else "abort_cleanup_failed", "cleanup_completed": cleanup_completed, "owned_resource_cleanup": cleanup, "owned_resource_residual_check": residual, "residual_owned_process": bool(residual.get("residual_owned_process")), "real_desktop_touched": False, "uncontrolled_actions_expanded": PHASE112_UNCONTROLLED_ACTIONS_EXPANDED}  # 新增代码+CleanupRecoveryMaturity：返回 abort 清理摘要；如果没有这一行，session runtime 无法上浮急停清理状态。
    # 新增代码+CleanupRecoveryMaturity：函数段落结束，abort_cleanup 到此结束；如果没有这个边界说明，用户不容易看出急停清理范围。
# 新增代码+CleanupRecoveryMaturity：类段落结束，OwnedResourceRegistry 到此结束；如果没有这个边界说明，用户不容易看出注册表结构范围。


# 新增代码+CleanupRecoveryMaturity：函数段落开始，run_phase112_owned_resource_registry_contract 提供无副作用自检；如果没有这个函数，测试和终端没有统一 Task 4 报告。
def run_phase112_owned_resource_registry_contract() -> dict[str, Any]:  # 新增代码+CleanupRecoveryMaturity：定义 Task 4 合同入口；如果没有这一行，CLI 无法生成成熟度事实。
    cleanup_calls: list[str] = []  # 新增代码+CleanupRecoveryMaturity：记录自检清理调用；如果没有这一行，合同无法证明只清理自有资源。
    registry = OwnedResourceRegistry(session_id="phase112-session", clock=lambda: "2026-06-05T00:00:00Z")  # 新增代码+CleanupRecoveryMaturity：创建固定时间注册表；如果没有这一行，自检没有状态容器。
    process = registry.register_owned_process(7007, "Obsidian.exe", cleanup_callback=lambda record: cleanup_calls.append(f"process:{record['process_id']}"), residual_check_callback=lambda record: False)  # 新增代码+CleanupRecoveryMaturity：登记自有进程成功样本；如果没有这一行，合同没有进程路径证据。
    window = registry.register_owned_window("hwnd:7007", process_id=7007, cleanup_callback=lambda record: cleanup_calls.append(f"window:{record['window_id']}"), residual_check_callback=lambda record: False)  # 新增代码+CleanupRecoveryMaturity：登记自有窗口成功样本；如果没有这一行，合同没有窗口路径证据。
    preexisting = registry.register_user_preexisting_window("hwnd:8008", process_id=8008, title_preview="User Window")  # 新增代码+CleanupRecoveryMaturity：登记用户已有窗口保护样本；如果没有这一行，合同无法证明保护边界。
    cleanup = registry.cleanup_owned_resources(reason="contract cleanup")  # 新增代码+CleanupRecoveryMaturity：执行自有资源清理；如果没有这一行，清理合同没有结果。
    residual = registry.check_residuals()  # 新增代码+CleanupRecoveryMaturity：执行残留检查；如果没有这一行，残留合同没有结果。
    lingering = OwnedResourceRegistry(session_id="phase112-lingering", clock=lambda: "2026-06-05T00:00:00Z")  # 新增代码+CleanupRecoveryMaturity：创建残留失败样本 registry；如果没有这一行，合同无法证明残留会失败。
    lingering.register_owned_process(9009, "Calc.exe", residual_check_callback=lambda record: True)  # 新增代码+CleanupRecoveryMaturity：登记仍存活的进程样本；如果没有这一行，residual failed 路径没有证据。
    lingering_residual = lingering.check_residuals()  # 新增代码+CleanupRecoveryMaturity：执行残留失败检查；如果没有这一行，合同无法捕获残留风险。
    passed = bool(process["process_id"] == 7007 and window["window_id"] == "hwnd:7007" and cleanup_calls == ["process:7007", "window:hwnd:7007"] and cleanup.get("cleanup_completed") and preexisting.get("cleanup_state") == "preserved_user_resource" and residual.get("residual_check_passed") and not lingering_residual.get("residual_check_passed") and lingering_residual.get("residual_owned_process") and not PHASE112_UNCONTROLLED_ACTIONS_EXPANDED)  # 新增代码+CleanupRecoveryMaturity：计算 Task 4 合同通过条件；如果没有这一行，CLI 不能用退出码表达失败。
    return {"marker": PHASE112_OWNED_RESOURCE_REGISTRY_MARKER, "ok_token": PHASE112_OWNED_RESOURCE_REGISTRY_OK_TOKEN, "model": PHASE112_OWNED_RESOURCE_REGISTRY_MODEL, "passed": passed, "owned_resource_registry_ready": True, "owned_process_registered": process["process_id"] == 7007, "owned_window_registered": window["window_id"] == "hwnd:7007", "cleanup_only_owned_resources": cleanup_calls == ["process:7007", "window:hwnd:7007"], "preexisting_user_windows_preserved": preexisting.get("cleanup_state") == "preserved_user_resource", "residual_check_fails_if_owned_process_remains": bool(lingering_residual.get("residual_owned_process") and not lingering_residual.get("residual_check_passed")), "real_desktop_touched": False, "uncontrolled_actions_expanded": PHASE112_UNCONTROLLED_ACTIONS_EXPANDED, "cleanup_report": cleanup, "residual_report": residual, "lingering_residual_report": lingering_residual}  # 新增代码+CleanupRecoveryMaturity：返回完整合同报告；如果没有这一行，测试、CLI 和最终矩阵无法共享事实。
# 新增代码+CleanupRecoveryMaturity：函数段落结束，run_phase112_owned_resource_registry_contract 到此结束；如果没有这个边界说明，用户不容易看出合同范围。


# 新增代码+CleanupRecoveryMaturity：函数段落开始，phase112_cli_line 把合同转成稳定 token 行；如果没有这个函数，真实终端验收只能解析复杂 JSON。
def phase112_cli_line(report: dict[str, Any]) -> str:  # 新增代码+CleanupRecoveryMaturity：定义 CLI 行格式化入口；如果没有这一行，验收输出没有固定格式。
    ok_token = f" {PHASE112_OWNED_RESOURCE_REGISTRY_OK_TOKEN}" if bool(report.get("passed", False)) else ""  # 新增代码+CleanupRecoveryMaturity：只在通过时追加 OK；如果没有这一行，失败输出可能被误判成功。
    return f"{PHASE112_OWNED_RESOURCE_REGISTRY_MARKER}{ok_token} owned_resource_registry_ready={_phase112_bool_token(report.get('owned_resource_registry_ready'))} owned_process_registered={_phase112_bool_token(report.get('owned_process_registered'))} owned_window_registered={_phase112_bool_token(report.get('owned_window_registered'))} cleanup_only_owned_resources={_phase112_bool_token(report.get('cleanup_only_owned_resources'))} preexisting_user_windows_preserved={_phase112_bool_token(report.get('preexisting_user_windows_preserved'))} residual_check_fails_if_owned_process_remains={_phase112_bool_token(report.get('residual_check_fails_if_owned_process_remains'))} real_desktop_touched={_phase112_bool_token(report.get('real_desktop_touched'))} uncontrolled_actions_expanded={_phase112_bool_token(report.get('uncontrolled_actions_expanded'))}"  # 新增代码+CleanupRecoveryMaturity：返回固定顺序 token 行；如果没有这一行，场景断言容易因输出漂移失败。
# 新增代码+CleanupRecoveryMaturity：函数段落结束，phase112_cli_line 到此结束；如果没有这个边界说明，用户不容易看出 CLI 输出范围。


# 新增代码+CleanupRecoveryMaturity：函数段落开始，main 提供命令行自检入口；如果没有这个函数，用户不能直接运行模块查看 Task 4 合同。
def main(argv: list[str] | None = None) -> int:  # 新增代码+CleanupRecoveryMaturity：定义 CLI main；如果没有这一行，python 文件方式运行没有明确入口。
    _ = argv  # 新增代码+CleanupRecoveryMaturity：保留未来参数扩展位；如果没有这一行，读者可能误以为 argv 被漏掉。
    report = run_phase112_owned_resource_registry_contract()  # 新增代码+CleanupRecoveryMaturity：运行无真实桌面副作用合同；如果没有这一行，CLI 不会产生验收事实。
    print(phase112_cli_line(report))  # 新增代码+CleanupRecoveryMaturity：打印稳定 token 行；如果没有这一行，终端验收不能快速匹配。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+CleanupRecoveryMaturity：打印完整 JSON；如果没有这一行，失败排查缺少细节。
    print(PHASE112_OWNED_RESOURCE_REGISTRY_MARKER)  # 新增代码+CleanupRecoveryMaturity：单独打印 ready marker；如果没有这一行，可见终端不容易发现阶段标识。
    return 0 if bool(report.get("passed", False)) else 1  # 新增代码+CleanupRecoveryMaturity：按合同结果返回退出码；如果没有这一行，失败也可能被自动化当成成功。
# 新增代码+CleanupRecoveryMaturity：函数段落结束，main 到此结束；如果没有这个边界说明，用户不容易看出命令行入口范围。


__all__ = ["PHASE112_OWNED_RESOURCE_REGISTRY_MARKER", "PHASE112_OWNED_RESOURCE_REGISTRY_MODEL", "PHASE112_OWNED_RESOURCE_REGISTRY_OK_TOKEN", "PHASE112_UNCONTROLLED_ACTIONS_EXPANDED", "OwnedResourceRegistry", "main", "phase112_cli_line", "phase112_utc_timestamp", "run_phase112_owned_resource_registry_contract"]  # 新增代码+CleanupRecoveryMaturity：公开 Task 4 稳定 API；如果没有这一行，后续模块和学习备份不容易确认正式接口。


if __name__ == "__main__":  # 新增代码+CleanupRecoveryMaturity：文件入口段开始，允许直接运行模块；如果没有这一行，python 文件方式不会启动自检。
    raise SystemExit(main())  # 新增代码+CleanupRecoveryMaturity：用 main 的返回码退出；如果没有这一行，命令行状态不明确。
# 新增代码+CleanupRecoveryMaturity：文件入口段结束，直接运行模块到此结束；如果没有这个边界说明，用户不容易看出入口范围。
