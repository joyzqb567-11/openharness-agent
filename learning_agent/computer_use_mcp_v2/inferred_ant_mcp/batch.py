"""Computer Use MCP v2 批量动作。"""  # 新增代码+ComputerUseMcpV2：说明本文件处理 computer_batch；如果没有这行代码，批量安全边界会混入 runtime。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型引用可能提前求值。

from typing import Any, Callable  # 新增代码+ComputerUseMcpV2：导入通用类型和分发回调类型；如果没有这行代码，batch helper 边界不清楚。

from .build_tools import FORBIDDEN_LEGACY_RAW_TOOL_NAMES  # 新增代码+ComputerUseMcpV2：导入禁止旧名清单；如果没有这行代码，batch 可能成为旧接口后门。
from .errors import error_result  # 新增代码+ComputerUseMcpV2：导入统一失败结果；如果没有这行代码，batch 拒绝格式会漂移。
from .result_blocks import success_result  # 新增代码+ComputerUseMcpV2：导入统一成功结果；如果没有这行代码，batch 成功格式会漂移。
from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入上下文；如果没有这行代码，batch 无法复用会话状态。


def run_batch(context: ComputerUseMcpV2Context, arguments: dict[str, Any], dispatch: Callable[[str, dict[str, Any], ComputerUseMcpV2Context], dict[str, Any]]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，顺序执行 batch；如果没有这段函数，computer_batch 没有安全实现。
    actions = arguments.get("actions", [])  # 新增代码+ComputerUseMcpV2：读取 actions 列表；如果没有这行代码，batch 不知道要执行哪些步骤。
    stop_on_error = bool(arguments.get("stop_on_error", True))  # 新增代码+ComputerUseMcpV2：读取失败停止策略；如果没有这行代码，batch 失败策略不可控。
    if not isinstance(actions, list):  # 新增代码+ComputerUseMcpV2：校验 actions 必须是列表；如果没有这行代码，坏参数会在遍历时崩溃。
        return error_result("computer_batch", "actions_must_be_list", error_class="invalid_arguments")  # 新增代码+ComputerUseMcpV2：返回参数错误；如果没有这行代码，模型不知道怎么修正。
    results: list[dict[str, Any]] = []  # 新增代码+ComputerUseMcpV2：准备保存每步结果；如果没有这行代码，最终报告没有明细。
    for index, raw_action in enumerate(actions):  # 新增代码+ComputerUseMcpV2：按顺序遍历动作；如果没有这行代码，batch 不会执行任何步骤。
        action = raw_action if isinstance(raw_action, dict) else {}  # 新增代码+ComputerUseMcpV2：容错非字典步骤；如果没有这行代码，坏步骤会触发属性错误。
        tool_name = str(action.get("tool") or action.get("tool_name") or action.get("name") or "").removeprefix("mcp__computer-use__")  # 新增代码+ComputerUseMcpV2：读取并规范化工具名；如果没有这行代码，batch 无法同时接受前缀名和原始名。
        if tool_name in FORBIDDEN_LEGACY_RAW_TOOL_NAMES:  # 新增代码+ComputerUseMcpV2：拦截旧名和蓝图外工具；如果没有这行代码，旧接口会通过 batch 后门复活。
            return error_result("computer_batch", f"legacy_or_forbidden_tool_in_batch:{tool_name}", error_class="legacy_tool_forbidden")  # 新增代码+ComputerUseMcpV2：返回 legacy 拒绝；如果没有这行代码，测试无法确认拒绝原因。
        step_arguments = action.get("arguments", {}) if isinstance(action.get("arguments", {}), dict) else {}  # 新增代码+ComputerUseMcpV2：读取步骤参数；如果没有这行代码，工具会丢失输入。
        step_result = dispatch(tool_name, step_arguments, context)  # 新增代码+ComputerUseMcpV2：复用单工具分发；如果没有这行代码，batch 会绕过 trace 和权限。
        step_result["batch_index"] = index  # 新增代码+ComputerUseMcpV2：标记步骤序号；如果没有这行代码，失败时难以定位哪一步。
        results.append(step_result)  # 新增代码+ComputerUseMcpV2：保存步骤结果；如果没有这行代码，最终报告为空。
        if stop_on_error and not bool(step_result.get("ok")):  # 新增代码+ComputerUseMcpV2：按策略遇错停止；如果没有这行代码，失败后可能继续真实动作。
            break  # 新增代码+ComputerUseMcpV2：停止后续步骤；如果没有这行代码，stop_on_error 不生效。
    all_steps_ok = all(bool(step.get("ok")) for step in results)  # 修改代码+ClaudeCodeParity：汇总已执行步骤是否全部成功；如果没有这行代码，失败步骤会被 batch 顶层成功掩盖。
    batch_result = success_result("computer_batch", {"results": results, "step_count": len(results), "all_steps_ok": all_steps_ok})  # 修改代码+ClaudeCodeParity：保留原有 payload 形状并加入整体步骤状态；如果没有这行代码，调用方拿不到 step 明细和整体判断。
    if not all_steps_ok:  # 新增代码+ClaudeCodeParity：检查是否存在失败步骤；如果没有这行代码，顶层 ok 不会随步骤失败变成 false。
        batch_result["ok"] = False  # 新增代码+ClaudeCodeParity：把顶层 ok 改为失败；如果没有这行代码，runtime 会记录 batch 成功从而误导模型。
        batch_result["reason"] = "batch_step_failed"  # 新增代码+ClaudeCodeParity：给顶层失败明确原因；如果没有这行代码，用户只看到 ok false 却不知道是哪类失败。
        batch_result["error_class"] = "batch_step_failed"  # 新增代码+ClaudeCodeParity：给顶层失败明确错误类别；如果没有这行代码，调用方无法稳定分流 batch 步骤失败。
    return batch_result  # 修改代码+ClaudeCodeParity：返回按步骤状态修正后的 batch 结果；如果没有这行代码，computer_batch 没有最终输出。
# 新增代码+ComputerUseMcpV2：函数段结束，run_batch 到此结束；如果没有这个边界说明，用户不容易看出批量执行范围。
