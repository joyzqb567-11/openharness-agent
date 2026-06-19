"""Computer Use MCP v2 自然语言桌面任务工具。"""  # 新增代码+DesktopTaskMcpTool: 说明本文件承载高层桌面任务入口；如果没有这行代码，读者会把它误认为普通原子动作。
from __future__ import annotations  # 新增代码+DesktopTaskMcpTool: 延迟类型注解解析；如果没有这行代码，跨模块类型引用更容易在导入时出错。

from typing import Any  # 新增代码+DesktopTaskMcpTool: 导入通用 JSON 类型；如果没有这行代码，工具参数和 payload 边界不清楚。

from .errors import error_result  # 新增代码+DesktopTaskMcpTool: 复用 MCP v2 统一错误格式；如果没有这行代码，失败结果会和其它工具不一致。
from .result_blocks import success_result  # 新增代码+DesktopTaskMcpTool: 复用 MCP v2 统一成功格式；如果没有这行代码，工具结果会缺少标准 payload 外壳。
from .types import ComputerUseMcpV2Context  # 新增代码+DesktopTaskMcpTool: 引入共享上下文；如果没有这行代码，工具拿不到 host adapter 和验收事件链路。

DESKTOP_TASK_STAGE_EVIDENCE_KEYS = (  # 新增代码+DesktopTaskMcpTool: 函数段开始，集中列出可写入验收事件的低敏阶段证据字段；如果没有这段常量，事件摘要会散落硬编码。
    "universal_stage_task_loop_used",  # 新增代码+DesktopTaskMcpTool: 暴露是否进入通用 Stage Loop；如果没有这一项，真实终端验收看不出新主路径是否启用。
    "desktop_task_plan_created",  # 新增代码+DesktopTaskMcpTool: 暴露是否生成 DesktopTaskPlan；如果没有这一项，验收无法确认不是原子动作临时拼凑。
    "stage_count",  # 新增代码+DesktopTaskMcpTool: 暴露总阶段数；如果没有这一项，最终门禁无法复核阶段完整性。
    "completed_stage_count",  # 新增代码+DesktopTaskMcpTool: 暴露已完成阶段数；如果没有这一项，未完成任务可能被误报完成。
    "desktop_task_completed",  # 新增代码+DesktopTaskMcpTool: 暴露桌面任务完成标志；如果没有这一项，验收只能读最终自然语言。
    "desktop_task_incomplete",  # 新增代码+DesktopTaskMcpTool: 暴露桌面任务未完成标志；如果没有这一项，final gate 难以解释阻断原因。
    "stage_boundary_observation_used",  # 新增代码+DesktopTaskMcpTool: 暴露是否使用阶段边界观察；如果没有这一项，用户无法确认不是每步原子 observe。
    "batch_execution_used",  # 新增代码+DesktopTaskMcpTool: 暴露是否使用批执行；如果没有这一项，压力测试无法证明耗时问题被架构处理。
    "primitive_action_count",  # 新增代码+DesktopTaskMcpTool: 暴露 primitive 数量；如果没有这一项，动作规模不可审计。
    "low_level_event_count",  # 新增代码+DesktopTaskMcpTool: 暴露低层事件数量；如果没有这一项，真实桌面触达不可证明。
    "target_ref_one_to_one",  # 新增代码+DesktopTaskMcpTool: 暴露目标绑定是否一对一；如果没有这一项，多窗口安全不可审计。
)  # 新增代码+DesktopTaskMcpTool: 阶段证据字段列表结束；如果没有这行代码，Python 元组语法不完整。


def _desktop_task_payload(value: Any) -> dict[str, Any]:  # 新增代码+DesktopTaskMcpTool: 函数段开始，把 host 返回值规范成 dict payload；如果没有这段函数，host 返回坏形状会污染 MCP 结果。
    return dict(value) if isinstance(value, dict) else {"result": value}  # 新增代码+DesktopTaskMcpTool: 字典直接复制，非字典包进 result；如果没有这一行，调用方可能收到不可 JSON 化的裸对象。
# 新增代码+DesktopTaskMcpTool: 函数段结束，_desktop_task_payload 到此结束；如果没有这个边界说明，用户不容易看出 payload 规范化范围。


def _desktop_task_target_hint_from_context(context: ComputerUseMcpV2Context, explicit_hint: str) -> str:  # 新增代码+DesktopTaskMcpTool: 函数段开始，从显式参数或当前授权应用推导通用目标提示；如果没有这段函数，desktop_task 可能拿不到刚刚 request_access 授权的应用。
    clean_hint = str(explicit_hint or "").strip()  # 新增代码+DesktopTaskMcpTool: 先清理模型显式传入的 target_hint；如果没有这一行，空格会让后续错误认为已有目标。
    if clean_hint:  # 新增代码+DesktopTaskMcpTool: 如果模型已经给了目标提示，就优先相信显式参数；如果没有这一行，授权列表可能覆盖用户更具体的目标。
        return clean_hint  # 新增代码+DesktopTaskMcpTool: 返回显式目标提示；如果没有这一行，调用方无法使用模型给出的目标。
    for app in reversed(list(getattr(context, "allowed_apps", []) or [])):  # 新增代码+DesktopTaskMcpTool: 倒序读取当前会话最近授权的应用；如果没有这一行，desktop_task 无法复用 request_access 的通用授权上下文。
        if not isinstance(app, dict):  # 新增代码+DesktopTaskMcpTool: 跳过坏格式授权记录；如果没有这一行，字符串或 None 会让 get 调用崩溃。
            continue  # 新增代码+DesktopTaskMcpTool: 继续检查其它授权应用；如果没有这一行，一个坏记录会阻断整个工具。
        for key in ("bundleId", "id", "name", "displayName"):  # 新增代码+DesktopTaskMcpTool: 按可执行身份优先、显示名兜底读取应用提示；如果没有这一行，不同授权结构会丢目标。
            candidate = str(app.get(key, "") or "").strip()  # 新增代码+DesktopTaskMcpTool: 清理当前候选字段；如果没有这一行，空字段或空格会污染目标提示。
            if candidate:  # 新增代码+DesktopTaskMcpTool: 只接受非空候选；如果没有这一行，可能返回空字符串导致启动层无目标。
                return candidate  # 新增代码+DesktopTaskMcpTool: 返回最近授权应用的通用目标提示；如果没有这一行，Stage Runtime 会退回 desktop_app 抽象目标。
    return ""  # 新增代码+DesktopTaskMcpTool: 没有任何目标线索时返回空；如果没有这一行，函数会返回 None 并增加下游判空复杂度。
# 新增代码+DesktopTaskMcpTool: 函数段结束，_desktop_task_target_hint_from_context 到此结束；如果没有这个边界说明，用户不容易看出目标提示来源。


def run_desktop_task(context: ComputerUseMcpV2Context, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopTaskMcpTool: 函数段开始，执行高层自然语言桌面任务；如果没有这段函数，模型只能手搓 open/type/click 原子链。
    prompt = str(arguments.get("prompt") or arguments.get("task") or arguments.get("objective") or "").strip()  # 新增代码+DesktopTaskMcpTool: 读取并清理自然语言任务；如果没有这一行，Stage Runtime 不知道用户到底要完成什么。
    target_hint = _desktop_task_target_hint_from_context(context, str(arguments.get("target_hint") or arguments.get("target_app") or ""))  # 修改代码+DesktopTaskMcpTool: 优先读取显式目标，缺省时复用最近授权应用；如果没有这一行，真实验收会在 request_access 后仍丢目标 hint。
    if not prompt:  # 新增代码+DesktopTaskMcpTool: 校验 prompt 不为空；如果没有这一行，空任务可能触发真实桌面副作用。
        return error_result("desktop_task", "prompt_is_required", error_class="invalid_arguments")  # 新增代码+DesktopTaskMcpTool: 返回稳定缺参错误；如果没有这一行，模型不知道该补哪个字段。
    host_method = getattr(context.host, "desktop_task", None) if context.host is not None else None  # 新增代码+DesktopTaskMcpTool: 从 host adapter 查找高层任务方法；如果没有这一行，工具无法接到真实 OpenHarness runtime。
    if not callable(host_method):  # 新增代码+DesktopTaskMcpTool: 检查 host 是否支持高层任务；如果没有这一行，None 调用会抛异常。
        return error_result("desktop_task", "host_desktop_task_unavailable", error_class="host_method_unavailable")  # 新增代码+DesktopTaskMcpTool: 返回可恢复的 host 不可用错误；如果没有这一行，stdio selftest 或假 host 会崩溃。
    try:  # 新增代码+DesktopTaskMcpTool: 捕获 host 执行异常；如果没有这一行，真实桌面运行时异常会破坏 MCP 协议返回。
        host_result = host_method(prompt, {"prompt": prompt, "target_hint": target_hint})  # 新增代码+DesktopTaskMcpTool: 调用 host 高层任务入口；如果没有这一行，Stage Runtime 永远不会被真实 MCP 工具触发。
    except Exception as error:  # 新增代码+DesktopTaskMcpTool: 捕获真实 runtime 异常；如果没有这一行，用户只能看到裸 Python 堆栈。
        return error_result("desktop_task", str(error), error_class="desktop_task_host_failed")  # 新增代码+DesktopTaskMcpTool: 把异常转成稳定工具失败；如果没有这一行，acceptance controller 无法按错误分类判断。
    payload = _desktop_task_payload(host_result)  # 新增代码+DesktopTaskMcpTool: 规范化 host 返回 payload；如果没有这一行，后续字段读取可能失败。
    payload.setdefault("desktop_task_prompt_length", len(prompt))  # 新增代码+DesktopTaskMcpTool: 写入 prompt 长度而不是原文；如果没有这一行，验收缺少任务存在证据且可能泄露原始 prompt。
    payload.setdefault("target_hint", target_hint)  # 新增代码+DesktopTaskMcpTool: 保留脱敏目标提示；如果没有这一行，排查时不知道目标来自哪里。
    result = success_result("desktop_task", payload, legacy_adapter_used=True)  # 新增代码+DesktopTaskMcpTool: 生成标准 MCP 成功外壳；如果没有这一行，工具结果字段和其它 v2 工具不兼容。
    task_completed = bool(payload.get("desktop_task_completed") or payload.get("passed") or (payload.get("ok") and not payload.get("desktop_task_incomplete")))  # 新增代码+DesktopTaskMcpTool: 用结构化字段判断高层任务是否真的完成；如果没有这一行，未完成阶段可能顶层 ok=true。
    result["ok"] = task_completed  # 新增代码+DesktopTaskMcpTool: 顶层 ok 跟随任务完成事实；如果没有这一行，模型会把需要用户处理的报告当成功。
    if not task_completed:  # 新增代码+DesktopTaskMcpTool: 未完成时补充稳定失败字段；如果没有这一行，final gate 和验收器看不到失败类别。
        result["reason"] = str(payload.get("decision") or payload.get("reason") or "desktop_task_incomplete")  # 新增代码+DesktopTaskMcpTool: 记录未完成原因；如果没有这一行，用户不知道该继续工具还是请求人工处理。
        result["error_class"] = str(payload.get("error_class") or "desktop_task_incomplete")  # 新增代码+DesktopTaskMcpTool: 记录稳定错误类别；如果没有这一行，controller 无法区分普通失败和未完成任务。
    return result  # 新增代码+DesktopTaskMcpTool: 返回最终工具结果；如果没有这一行，调用方拿不到 Stage Runtime 报告。
# 新增代码+DesktopTaskMcpTool: 函数段结束，run_desktop_task 到此结束；如果没有这个边界说明，用户不容易看出高层工具执行范围。


__all__ = ["DESKTOP_TASK_STAGE_EVIDENCE_KEYS", "run_desktop_task"]  # 新增代码+DesktopTaskMcpTool: 公开高层工具入口和证据字段；如果没有这一行，测试和 runtime 无法稳定导入。
