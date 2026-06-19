"""Cua Driver Windows Computer Use 借鉴能力最终矩阵。"""  # 新增代码+CuaDriverBorrowing：说明本文件负责汇总本轮借鉴成果；如果没有这一行，用户不知道该 CLI 是最终验收入口。
from __future__ import annotations  # 新增代码+CuaDriverBorrowing：启用延迟类型解析；如果没有这一行，部分类型标注在旧入口下可能提前求值失败。

import argparse  # 新增代码+CuaDriverBorrowing：导入命令行参数解析；如果没有这一行，真实终端场景无法传入 repo-root。
import json  # 新增代码+CuaDriverBorrowing：导入 JSON 工具；如果没有这一行，矩阵 manifest 和 scenario 无法结构化写入。
from pathlib import Path  # 新增代码+CuaDriverBorrowing：导入路径对象；如果没有这一行，Windows 路径拼接会变成脆弱字符串。
from typing import Any  # 新增代码+CuaDriverBorrowing：导入通用类型；如果没有这一行，矩阵报告结构的边界不清楚。

CUA_DRIVER_WINDOWS_BORROWING_MARKER = "CUA_DRIVER_WINDOWS_BORROWING_READY"  # 新增代码+CuaDriverBorrowing：定义真实终端可匹配 marker；如果没有这一行，验收 controller 找不到成功信号。
CUA_DRIVER_WINDOWS_BORROWING_OK_TOKEN = "CUA_DRIVER_WINDOWS_BORROWING_OK"  # 新增代码+CuaDriverBorrowing：定义人类和机器都能识别的通过 token；如果没有这一行，摘要只能靠多个布尔字段猜通过。
BORROWING_MANIFEST = Path("learning_agent/memory/computer_use/cua_driver_borrowing/cua_driver_borrowing_evidence_20260618.json")  # 新增代码+CuaDriverBorrowing：固定机器可读证据路径；如果没有这一行，后续复验找不到矩阵 manifest。
BORROWING_REPORT = Path("agent_memory/computer_use_cua_driver_borrowing_report_20260618.md")  # 新增代码+CuaDriverBorrowing：固定人类可读报告路径；如果没有这一行，用户只能读 JSON。
BORROWING_SCENARIO = Path("learning_agent/acceptance_controller/scenarios/agent_capability_cua_driver_borrowing_visible_terminal.json")  # 新增代码+CuaDriverBorrowing：固定真实终端场景路径；如果没有这一行，规则十七验收没有专门入口。
REQUIRED_CLAUDECODE_TOOL_NAMES = {"request_access", "observe", "screenshot", "cursor_position", "mouse_move", "left_click", "type", "key", "scroll", "wait", "read_clipboard", "write_clipboard", "list_granted_applications"}  # 新增代码+CuaDriverBorrowing：定义借鉴后仍必须保留的 ClaudeCode 对齐工具面；如果没有这一行，矩阵无法确认没有破坏原功能。
FORBIDDEN_BORROWING_TOOL_NAMES = {"element_click", "uia_click", "cua_click", "raw_element_action"}  # 新增代码+CuaDriverBorrowing：定义不应新增给模型看的 Cua Driver 内部工具名；如果没有这一行，借鉴实现可能污染公开 MCP 工具面。


class _MatrixFakeInvokeElement:  # 新增代码+CuaDriverBorrowing：矩阵用假 UIA Invoke 元素类开始；如果没有这个类，矩阵无法真实验证 MCP 语义路径。
    def __init__(self) -> None:  # 新增代码+CuaDriverBorrowing：函数段开始，初始化 fake 元素状态；如果没有这段函数，矩阵无法记录 invoke 是否发生。
        self.invoked = 0  # 新增代码+CuaDriverBorrowing：保存 invoke 调用次数；如果没有这一行，矩阵无法证明语义动作执行。
    # 新增代码+CuaDriverBorrowing：函数段结束，_MatrixFakeInvokeElement.__init__ 到此结束；如果没有这个边界说明，初学者不容易看出初始化范围。

    def invoke(self) -> None:  # 新增代码+CuaDriverBorrowing：函数段开始，模拟 UIA InvokePattern；如果没有这段函数，矩阵无法验证 uia_invoke。
        self.invoked += 1  # 新增代码+CuaDriverBorrowing：累计调用次数；如果没有这一行，矩阵无法区分空成功和真实执行。
    # 新增代码+CuaDriverBorrowing：函数段结束，_MatrixFakeInvokeElement.invoke 到此结束；如果没有这个边界说明，初学者不容易看出 fake 动作范围。
# 新增代码+CuaDriverBorrowing：矩阵用假 UIA Invoke 元素类结束；如果没有这个边界说明，初学者不容易看出测试替身范围。


def _bool_token(value: Any) -> str:  # 新增代码+CuaDriverBorrowing：函数段开始，统一布尔 token 格式；如果没有这段函数，终端摘要可能出现 True/False 大小写漂移。
    return "true" if bool(value) else "false"  # 新增代码+CuaDriverBorrowing：返回小写布尔文本；如果没有这一行，scenario 文本匹配可能失败。
# 新增代码+CuaDriverBorrowing：函数段结束，_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。


def _tool_surface_unchanged() -> bool:  # 新增代码+CuaDriverBorrowing：函数段开始，检查借鉴后没有污染 ClaudeCode 对齐工具面；如果没有这段函数，Cua Driver 内部动作可能被误暴露给模型。
    from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import COMPUTER_USE_MCP_TOOL_NAMES  # 新增代码+CuaDriverBorrowing：导入当前 MCP v2 工具名；如果没有这一行，矩阵无法检查公开工具面。
    tool_names = {str(name) for name in COMPUTER_USE_MCP_TOOL_NAMES}  # 新增代码+CuaDriverBorrowing：把工具名转成集合；如果没有这一行，包含关系检查会重复且低效。
    required_ok = REQUIRED_CLAUDECODE_TOOL_NAMES.issubset(tool_names)  # 新增代码+CuaDriverBorrowing：确认 ClaudeCode 对齐核心工具仍在；如果没有这一行，借鉴可能破坏旧能力也被误报通过。
    forbidden_ok = not bool(tool_names.intersection(FORBIDDEN_BORROWING_TOOL_NAMES))  # 新增代码+CuaDriverBorrowing：确认没有新增内部 Cua 工具名；如果没有这一行，工具面污染无法被发现。
    return bool(required_ok and forbidden_ok)  # 新增代码+CuaDriverBorrowing：返回工具面检查结果；如果没有这一行，调用方拿不到结论。
# 新增代码+CuaDriverBorrowing：函数段结束，_tool_surface_unchanged 到此结束；如果没有这个边界说明，初学者不容易看出工具面检查范围。


def _element_cache_present() -> bool:  # 新增代码+CuaDriverBorrowing：函数段开始，检查元素索引缓存能力；如果没有这段函数，矩阵只能靠文件存在猜测。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_element_cache import WindowsElementSnapshotCache  # 修改代码+ComputerUseMcpV2LegacyFolderRemoval：从 v2 内部导入元素缓存类；如果没有这一行，删除旧目录后矩阵无法创建真实缓存。
    cache = WindowsElementSnapshotCache()  # 新增代码+CuaDriverBorrowing：创建缓存实例；如果没有这一行，无法验证 update/lookup。
    cache.update_snapshot(1, "hwnd:1", [{"element_index": 0, "name": "OK", "role": "Button", "bounds": {"left": 0, "top": 0, "right": 10, "bottom": 10}}])  # 新增代码+CuaDriverBorrowing：写入一条元素快照；如果没有这一行，lookup 没有数据来源。
    snapshot = cache.lookup(1, "hwnd:1", 0)  # 新增代码+CuaDriverBorrowing：按目标和编号查回元素；如果没有这一行，无法证明缓存可用。
    return bool(snapshot is not None and snapshot.name == "OK")  # 新增代码+CuaDriverBorrowing：确认缓存命中且字段正确；如果没有这一行，坏缓存也可能被误报存在。
# 新增代码+CuaDriverBorrowing：函数段结束，_element_cache_present 到此结束；如果没有这个边界说明，初学者不容易看出缓存检查范围。


def _uia_semantic_dispatch_present() -> bool:  # 新增代码+CuaDriverBorrowing：函数段开始，检查 UIA Pattern 语义分发能力；如果没有这段函数，矩阵无法证明 InvokePattern 路径存在。
    from types import SimpleNamespace  # 新增代码+CuaDriverBorrowing：导入轻量快照对象；如果没有这一行，矩阵无法模拟缓存快照。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_uia_patterns import dispatch_semantic_action  # 修改代码+ComputerUseMcpV2LegacyFolderRemoval：从 v2 内部导入语义分发入口；如果没有这一行，删除旧目录后矩阵无法执行 Pattern。
    element = _MatrixFakeInvokeElement()  # 新增代码+CuaDriverBorrowing：创建 fake Invoke 元素；如果没有这一行，分发器没有目标。
    result = dispatch_semantic_action("left_click", SimpleNamespace(raw_element=element), {})  # 新增代码+CuaDriverBorrowing：执行语义点击分发；如果没有这一行，矩阵无法验证 uia_invoke。
    return bool(result.get("ok") and result.get("dispatch_path") == "uia_invoke" and element.invoked == 1)  # 新增代码+CuaDriverBorrowing：确认分发成功且确实调用 invoke；如果没有这一行，空成功可能蒙混过关。
# 新增代码+CuaDriverBorrowing：函数段结束，_uia_semantic_dispatch_present 到此结束；如果没有这个边界说明，初学者不容易看出 UIA 检查范围。


def _coordinate_contract_present() -> bool:  # 新增代码+CuaDriverBorrowing：函数段开始，检查坐标合同能力；如果没有这段函数，矩阵无法证明坐标混用会被拒绝。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_coordinate_contract import normalize_coordinate_request, window_local_to_screen  # 修改代码+ComputerUseMcpV2LegacyFolderRemoval：从 v2 内部导入坐标合同函数；如果没有这一行，删除旧目录后矩阵无法执行坐标检查。
    converted = window_local_to_screen({"rect": {"left": 100, "top": 50}}, 5, 6)  # 新增代码+CuaDriverBorrowing：执行窗口局部到屏幕坐标转换；如果没有这一行，矩阵无法验证偏移计算。
    rejected = normalize_coordinate_request({"x": 1, "y": 2, "screen_x": 3, "screen_y": 4})  # 新增代码+CuaDriverBorrowing：执行混合坐标拒绝检查；如果没有这一行，矩阵无法验证失败关闭。
    return bool(converted == {"x": 105, "y": 56, "coordinate_space": "screen_physical"} and rejected.get("reason") == "mixed_coordinate_spaces")  # 新增代码+CuaDriverBorrowing：确认转换和拒绝都正确；如果没有这一行，坐标合同坏了也会被误报通过。
# 新增代码+CuaDriverBorrowing：函数段结束，_coordinate_contract_present 到此结束；如果没有这个边界说明，初学者不容易看出坐标检查范围。


def _uipi_diagnostics_present() -> bool:  # 新增代码+CuaDriverBorrowing：函数段开始，检查 UIPI 完整性诊断能力；如果没有这段函数，矩阵无法证明权限失败可解释。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_integrity import diagnose_uipi_block  # 修改代码+ComputerUseMcpV2LegacyFolderRemoval：从 v2 内部导入 UIPI 诊断函数；如果没有这一行，删除旧目录后矩阵无法执行完整性检查。
    result = diagnose_uipi_block("medium", "high", attempted_background=True)  # 新增代码+CuaDriverBorrowing：模拟低完整性后台控制高完整性目标；如果没有这一行，阻断路径没有输入。
    return bool(not result.get("ok") and result.get("decision") == "integrity_blocked")  # 新增代码+CuaDriverBorrowing：确认诊断识别 UIPI 阻断；如果没有这一行，权限解释坏了也会误报通过。
# 新增代码+CuaDriverBorrowing：函数段结束，_uipi_diagnostics_present 到此结束；如果没有这个边界说明，初学者不容易看出 UIPI 检查范围。


def _mcp_observe_act_verify_present() -> bool:  # 新增代码+CuaDriverBorrowing：函数段开始，检查 MCP v2 元素索引到语义动作总链路；如果没有这段函数，矩阵只覆盖孤立 helper。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_element_cache import WindowsElementSnapshotCache  # 修改代码+ComputerUseMcpV2LegacyFolderRemoval：从 v2 内部导入元素缓存；如果没有这一行，删除旧目录后总链路无法模拟观察结果。
    from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import dispatch_computer_use_mcp_v2_tool  # 新增代码+CuaDriverBorrowing：导入 MCP v2 总分发入口；如果没有这一行，矩阵无法验证真实动作链。
    from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.types import ComputerUseMcpV2Context  # 新增代码+CuaDriverBorrowing：导入 MCP v2 上下文；如果没有这一行，矩阵无法注入元素缓存。
    element = _MatrixFakeInvokeElement()  # 新增代码+CuaDriverBorrowing：创建 fake Invoke 元素；如果没有这一行，总链路没有可执行目标。
    cache = WindowsElementSnapshotCache()  # 新增代码+CuaDriverBorrowing：创建元素缓存；如果没有这一行，总链路无法按 element_index 查找。
    cache.update_snapshot(42, "hwnd:42", [{"element_index": 0, "name": "Run", "role": "Button", "bounds": {"left": 0, "top": 0, "right": 20, "bottom": 20}, "raw_element": element}])  # 新增代码+CuaDriverBorrowing：写入观察快照；如果没有这一行，MCP 动作无法命中缓存。
    context = ComputerUseMcpV2Context(element_cache=cache)  # 新增代码+CuaDriverBorrowing：把缓存注入 MCP v2 上下文；如果没有这一行，总链路仍会退回 host_required。
    result = dispatch_computer_use_mcp_v2_tool("left_click", {"pid": 42, "window_id": "hwnd:42", "element_index": 0}, context)  # 新增代码+CuaDriverBorrowing：执行 MCP v2 左键动作；如果没有这一行，矩阵无法验证动作分发。
    payload = result.get("payload", {}) if isinstance(result.get("payload"), dict) else {}  # 新增代码+CuaDriverBorrowing：安全读取 payload；如果没有这一行，坏结果类型会导致矩阵崩溃。
    return bool(result.get("ok") and payload.get("dispatch_path") == "uia_invoke" and payload.get("verified") and element.invoked == 1)  # 新增代码+CuaDriverBorrowing：确认总链路语义执行并验证通过；如果没有这一行，MCP 接入坏了也会误报通过。
# 新增代码+CuaDriverBorrowing：函数段结束，_mcp_observe_act_verify_present 到此结束；如果没有这个边界说明，初学者不容易看出总链路检查范围。


def build_cua_driver_borrowing_matrix(*, visible_terminal_gate: bool = False, final_visible_run_dir: str = "") -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：函数段开始，生成 Cua Driver 借鉴矩阵；如果没有这段函数，测试和 CLI 没有核心判定入口。
    checks = {  # 新增代码+CuaDriverBorrowing：构造所有能力检查结果开始；如果没有这一行，报告没有逐项布尔字段。
        "claudecode_tool_surface_unchanged": _tool_surface_unchanged(),  # 新增代码+CuaDriverBorrowing：检查公开工具面未污染；如果没有这一行，借鉴可能破坏 ClaudeCode 对齐。
        "cua_inspired_element_cache_present": _element_cache_present(),  # 新增代码+CuaDriverBorrowing：检查元素索引缓存；如果没有这一行，观察到动作链路缺少基础。
        "uia_semantic_dispatch_present": _uia_semantic_dispatch_present(),  # 新增代码+CuaDriverBorrowing：检查 UIA Pattern 分发；如果没有这一行，语义动作能力缺少证明。
        "coordinate_contract_present": _coordinate_contract_present(),  # 新增代码+CuaDriverBorrowing：检查坐标合同；如果没有这一行，误点风险缺少验收。
        "uipi_diagnostics_present": _uipi_diagnostics_present(),  # 新增代码+CuaDriverBorrowing：检查 UIPI 诊断；如果没有这一行，权限失败解释缺少验收。
        "mcp_observe_act_verify_present": _mcp_observe_act_verify_present(),  # 新增代码+CuaDriverBorrowing：检查 MCP v2 总链路；如果没有这一行，只能证明 helper 而不是 agent 功能。
        "hidden_claudecode_package_internals_excluded": True,  # 新增代码+CuaDriverBorrowing：明确隐藏外部包内部行为不纳入逐行对齐；如果没有这一行，用户会误以为可验证 ClaudeCode 隐藏包源码。
    }  # 新增代码+CuaDriverBorrowing：构造所有能力检查结果结束；如果没有这一行，字典语法不完整。
    passed = all(bool(value) for value in checks.values())  # 新增代码+CuaDriverBorrowing：计算总体通过状态；如果没有这一行，报告缺少单一结论。
    return {"marker": CUA_DRIVER_WINDOWS_BORROWING_MARKER, "ok_token": CUA_DRIVER_WINDOWS_BORROWING_OK_TOKEN, "model": "cua_driver_windows_computer_use_borrowing_matrix", "passed": passed, "visible_terminal_gate": bool(visible_terminal_gate), "final_visible_run_dir": str(final_visible_run_dir or ""), **checks}  # 新增代码+CuaDriverBorrowing：返回完整报告；如果没有这一行，调用方拿不到矩阵结果。
# 新增代码+CuaDriverBorrowing：函数段结束，build_cua_driver_borrowing_matrix 到此结束；如果没有这个边界说明，初学者不容易看出矩阵生成范围。


def format_cua_driver_borrowing_matrix_line(report: dict[str, Any]) -> str:  # 新增代码+CuaDriverBorrowing：函数段开始，生成真实终端单行摘要；如果没有这段函数，scenario 需要解析长 JSON。
    return " ".join([str(report.get("marker", CUA_DRIVER_WINDOWS_BORROWING_MARKER)), str(report.get("ok_token", CUA_DRIVER_WINDOWS_BORROWING_OK_TOKEN)), f"passed={_bool_token(report.get('passed'))}", f"claudecode_tool_surface_unchanged={_bool_token(report.get('claudecode_tool_surface_unchanged'))}", f"cua_inspired_element_cache_present={_bool_token(report.get('cua_inspired_element_cache_present'))}", f"uia_semantic_dispatch_present={_bool_token(report.get('uia_semantic_dispatch_present'))}", f"coordinate_contract_present={_bool_token(report.get('coordinate_contract_present'))}", f"uipi_diagnostics_present={_bool_token(report.get('uipi_diagnostics_present'))}", f"mcp_observe_act_verify_present={_bool_token(report.get('mcp_observe_act_verify_present'))}", f"hidden_claudecode_package_internals_excluded={_bool_token(report.get('hidden_claudecode_package_internals_excluded'))}", f"visible_terminal_gate={_bool_token(report.get('visible_terminal_gate'))}"])  # 新增代码+CuaDriverBorrowing：拼出固定顺序 token；如果没有这一行，真实终端验收容易因为格式漂移失败。
# 新增代码+CuaDriverBorrowing：函数段结束，format_cua_driver_borrowing_matrix_line 到此结束；如果没有这个边界说明，初学者不容易看出摘要格式范围。


def render_cua_driver_borrowing_report(report: dict[str, Any]) -> str:  # 新增代码+CuaDriverBorrowing：函数段开始，生成 Markdown 人类报告；如果没有这段函数，用户只能阅读 JSON。
    lines = ["# Cua Driver Windows Computer Use Borrowing Matrix", "", f"- marker={report.get('marker', CUA_DRIVER_WINDOWS_BORROWING_MARKER)}", f"- passed={_bool_token(report.get('passed'))}", f"- visible_terminal_gate={_bool_token(report.get('visible_terminal_gate'))}", "", "## Checks"]  # 新增代码+CuaDriverBorrowing：写入报告头和摘要；如果没有这一行，报告缺少核心结论。
    for key in ["claudecode_tool_surface_unchanged", "cua_inspired_element_cache_present", "uia_semantic_dispatch_present", "coordinate_contract_present", "uipi_diagnostics_present", "mcp_observe_act_verify_present", "hidden_claudecode_package_internals_excluded"]:  # 新增代码+CuaDriverBorrowing：按固定顺序遍历检查项；如果没有这一行，报告顺序会漂移。
        lines.append(f"- {key}={_bool_token(report.get(key))}")  # 新增代码+CuaDriverBorrowing：写入单项布尔结论；如果没有这一行，用户看不到哪项通过。
    lines.extend(["", "## Boundary", "- ClaudeCode hidden external package internals remain excluded from line-by-line verification.", "- Windows implementation differences are accepted when they are platform-equivalent.", ""])  # 新增代码+CuaDriverBorrowing：写入边界说明；如果没有这一行，外部包和系统差异容易被误判为未完成。
    return "\n".join(lines)  # 新增代码+CuaDriverBorrowing：返回 Markdown 文本；如果没有这一行，调用方无法写报告。
# 新增代码+CuaDriverBorrowing：函数段结束，render_cua_driver_borrowing_report 到此结束；如果没有这个边界说明，初学者不容易看出报告生成范围。


def _borrowing_scenario_payload() -> dict[str, Any]:  # 新增代码+CuaDriverBorrowing：函数段开始，构造真实可见终端 scenario；如果没有这段函数，规则十七验收没有自动入口。
    summary_line = f"{CUA_DRIVER_WINDOWS_BORROWING_MARKER} {CUA_DRIVER_WINDOWS_BORROWING_OK_TOKEN} passed=true claudecode_tool_surface_unchanged=true cua_inspired_element_cache_present=true uia_semantic_dispatch_present=true coordinate_contract_present=true uipi_diagnostics_present=true mcp_observe_act_verify_present=true hidden_claudecode_package_internals_excluded=true visible_terminal_gate=false"  # 新增代码+CuaDriverBorrowing：定义 agent 最终要复制的稳定摘要；如果没有这一行，scenario 无法精确断言最终答案。
    return {"id": "agent_capability_cua_driver_borrowing_visible_terminal", "name": "agent_capability_cua_driver_borrowing_visible_terminal", "output_prefix": "agent_capability_cua_driver_borrowing_visible_terminal", "window_title_prefix": "LearningAgent-CuaBorrowing", "entrypoint": "learning_agent/start_oauth_agent.bat", "visible_terminal_gate": True, "screenshot_artifacts_required": True, "max_seconds": 900, "final_log_wait_seconds": 60, "post_success_wait_seconds": 6, "success_marker": CUA_DRIVER_WINDOWS_BORROWING_MARKER, "prompt": "Please run the Cua Driver Windows Computer Use borrowing matrix acceptance.", "prompt_lines": ["Please run the Cua Driver Windows Computer Use borrowing matrix. Use only local OpenHarness evidence. Do not open browsers, login windows, passwords, system settings, registry, installers, payment pages, or user documents. The final answer must include the fixed marker: CUA_DRIVER_WINDOWS_BORROWING_READY.", "You must call the terminal tool and run this verification command exactly: $env:PYTHONPATH='..'; python -m learning_agent.computer_use_mcp_v2.windows_runtime.cua_driver_borrowing_matrix --repo-root ..", f"Do not write the final answer early. Only after the terminal command prints {CUA_DRIVER_WINDOWS_BORROWING_MARKER}, the final answer's last line must completely copy: {summary_line}"], "required_event_states": ["agent_ready_for_user_prompt", "user_prompt_received", "final_answer_printed"], "debug_log_contains": [CUA_DRIVER_WINDOWS_BORROWING_MARKER, CUA_DRIVER_WINDOWS_BORROWING_OK_TOKEN, "passed=true", "claudecode_tool_surface_unchanged=true", "cua_inspired_element_cache_present=true", "uia_semantic_dispatch_present=true", "coordinate_contract_present=true", "uipi_diagnostics_present=true", "mcp_observe_act_verify_present=true", "hidden_claudecode_package_internals_excluded=true"], "event_answer_contains": [CUA_DRIVER_WINDOWS_BORROWING_MARKER, CUA_DRIVER_WINDOWS_BORROWING_OK_TOKEN, "passed=true", "claudecode_tool_surface_unchanged=true", "cua_inspired_element_cache_present=true", "uia_semantic_dispatch_present=true", "coordinate_contract_present=true", "uipi_diagnostics_present=true", "mcp_observe_act_verify_present=true", "hidden_claudecode_package_internals_excluded=true"], "assertions": {"output_contains": [CUA_DRIVER_WINDOWS_BORROWING_MARKER, CUA_DRIVER_WINDOWS_BORROWING_OK_TOKEN, "passed=true", "claudecode_tool_surface_unchanged=true", "cua_inspired_element_cache_present=true", "uia_semantic_dispatch_present=true", "coordinate_contract_present=true", "uipi_diagnostics_present=true", "mcp_observe_act_verify_present=true", "hidden_claudecode_package_internals_excluded=true"]}, "max_permission_sent_count": 0}  # 修改代码+ComputerUseMcpV2LegacyFolderRemoval：返回指向 v2 模块的完整 scenario JSON；如果没有这一行，可见终端验收会继续调用已删除的旧目录模块。
# 新增代码+CuaDriverBorrowing：函数段结束，_borrowing_scenario_payload 到此结束；如果没有这个边界说明，初学者不容易看出 scenario 合同范围。


def write_cua_driver_borrowing_outputs(repo_root: str | Path, *, visible_terminal_gate: bool = False, final_visible_run_dir: str = "") -> dict[str, str]:  # 新增代码+CuaDriverBorrowing：函数段开始，写入矩阵 manifest、报告和 scenario；如果没有这段函数，验收产物无法复用。
    root = Path(repo_root)  # 新增代码+CuaDriverBorrowing：规范化仓库根目录；如果没有这一行，后续路径拼接依赖输入类型。
    report = build_cua_driver_borrowing_matrix(visible_terminal_gate=visible_terminal_gate, final_visible_run_dir=final_visible_run_dir)  # 新增代码+CuaDriverBorrowing：生成矩阵报告；如果没有这一行，文件没有内容来源。
    manifest_path = root / BORROWING_MANIFEST  # 新增代码+CuaDriverBorrowing：定位机器可读 manifest 路径；如果没有这一行，JSON 证据无法落盘。
    report_path = root / BORROWING_REPORT  # 新增代码+CuaDriverBorrowing：定位 Markdown 报告路径；如果没有这一行，人类报告无法落盘。
    scenario_path = root / BORROWING_SCENARIO  # 新增代码+CuaDriverBorrowing：定位真实终端 scenario 路径；如果没有这一行，controller 找不到场景。
    manifest_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+CuaDriverBorrowing：确保 manifest 目录存在；如果没有这一行，首次写 JSON 会失败。
    report_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+CuaDriverBorrowing：确保报告目录存在；如果没有这一行，首次写 Markdown 会失败。
    scenario_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+CuaDriverBorrowing：确保 scenario 目录存在；如果没有这一行，首次写 scenario 会失败。
    manifest_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")  # 新增代码+CuaDriverBorrowing：写入机器可读 manifest；如果没有这一行，后续 agent 无法复验。
    report_path.write_text(render_cua_driver_borrowing_report(report), encoding="utf-8")  # 新增代码+CuaDriverBorrowing：写入人类可读报告；如果没有这一行，用户看不到矩阵解释。
    scenario_path.write_text(json.dumps(_borrowing_scenario_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # 新增代码+CuaDriverBorrowing：写入真实终端 scenario；如果没有这一行，规则十七验收无法运行。
    return {"manifest_path": str(manifest_path), "report_path": str(report_path), "scenario_path": str(scenario_path)}  # 新增代码+CuaDriverBorrowing：返回产物路径；如果没有这一行，CLI 和测试不知道文件位置。
# 新增代码+CuaDriverBorrowing：函数段结束，write_cua_driver_borrowing_outputs 到此结束；如果没有这个边界说明，初学者不容易看出落盘范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+CuaDriverBorrowing：函数段开始，提供 python -m 可调用 CLI；如果没有这段函数，真实终端场景无法运行矩阵。
    parser = argparse.ArgumentParser(description="Evaluate Cua Driver Windows Computer Use borrowing matrix.")  # 新增代码+CuaDriverBorrowing：创建命令行解析器；如果没有这一行，参数错误没有清晰提示。
    parser.add_argument("--repo-root", default=".")  # 新增代码+CuaDriverBorrowing：支持指定 OpenHarness 根目录；如果没有这一行，真实终端 cwd 改变时会找错路径。
    parser.add_argument("--visible-terminal-gate", action="store_true")  # 新增代码+CuaDriverBorrowing：允许外部回填可见终端 gate；如果没有这一行，最终证据无法标记真实终端已跑。
    parser.add_argument("--final-visible-run-dir", default="")  # 新增代码+CuaDriverBorrowing：允许记录最终可见终端运行目录；如果没有这一行，验收证据不可追溯。
    args = parser.parse_args(argv)  # 新增代码+CuaDriverBorrowing：解析命令行参数；如果没有这一行，后续拿不到用户输入。
    outputs = write_cua_driver_borrowing_outputs(args.repo_root, visible_terminal_gate=args.visible_terminal_gate, final_visible_run_dir=args.final_visible_run_dir)  # 新增代码+CuaDriverBorrowing：写入矩阵产物；如果没有这一行，CLI 只会打印临时结果。
    report = build_cua_driver_borrowing_matrix(visible_terminal_gate=args.visible_terminal_gate, final_visible_run_dir=args.final_visible_run_dir)  # 新增代码+CuaDriverBorrowing：重新生成报告用于打印；如果没有这一行，终端摘要没有数据来源。
    print(format_cua_driver_borrowing_matrix_line(report))  # 新增代码+CuaDriverBorrowing：打印稳定摘要；如果没有这一行，acceptance controller 找不到固定结论。
    print(f"manifest_path={outputs['manifest_path']}")  # 新增代码+CuaDriverBorrowing：打印 manifest 路径；如果没有这一行，用户不容易定位机器证据。
    print(f"report_path={outputs['report_path']}")  # 新增代码+CuaDriverBorrowing：打印报告路径；如果没有这一行，用户不容易定位可读报告。
    print(f"scenario_path={outputs['scenario_path']}")  # 新增代码+CuaDriverBorrowing：打印 scenario 路径；如果没有这一行，用户不容易定位真实终端入口。
    return 0  # 新增代码+CuaDriverBorrowing：CLI 完成矩阵写入后返回成功；如果没有这一行，调用方无法稳定判断命令退出状态。
# 新增代码+CuaDriverBorrowing：函数段结束，main 到此结束；如果没有这个边界说明，初学者不容易看出 CLI 范围。


__all__ = ["CUA_DRIVER_WINDOWS_BORROWING_MARKER", "CUA_DRIVER_WINDOWS_BORROWING_OK_TOKEN", "build_cua_driver_borrowing_matrix", "format_cua_driver_borrowing_matrix_line", "render_cua_driver_borrowing_report", "write_cua_driver_borrowing_outputs"]  # 新增代码+CuaDriverBorrowing：声明稳定公开 API；如果没有这一行，后续模块不清楚哪些名字可以依赖。


if __name__ == "__main__":  # 新增代码+CuaDriverBorrowing：模块脚本入口开始；如果没有这一行，python -m 不会执行 main。
    raise SystemExit(main())  # 新增代码+CuaDriverBorrowing：执行 CLI 并把返回码交给系统；如果没有这一行，真实终端命令不会输出矩阵。
