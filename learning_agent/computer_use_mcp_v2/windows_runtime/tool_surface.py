"""Computer Use MCP v2 工具面合同。"""  # 修改代码+ComputerUseMcpV2ResidualCleanup：说明本文件只验证 v2 工具面；如果没有这行代码，读者会继续误以为 Phase49 还在维护旧 computer_action 入口。
from __future__ import annotations  # 修改代码+ComputerUseMcpV2ResidualCleanup：允许类型注解延迟解析；如果没有这行代码，旧 Python 解释顺序可能影响导入稳定性。
import json  # 修改代码+ComputerUseMcpV2ResidualCleanup：用于输出稳定 JSON 报告；如果没有这行代码，CLI 自检失败时不容易定位字段。
from typing import Any  # 修改代码+ComputerUseMcpV2ResidualCleanup：标注动态 JSON 字段类型；如果没有这行代码，函数边界对读者不清楚。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import COMPUTER_USE_MCP_TOOL_NAMES, computer_use_mcp_tools  # 修改代码+ComputerUseMcpV2ResidualCleanup：直接读取 v2 MCP 工具事实源；如果没有这行代码，Phase49 可能继续从旧内置 schema 推断工具面。
from learning_agent.tools.tool_scope import COMPUTER_USE_COMPAT_BUILTIN_TOOL_NAMES  # 修改代码+ComputerUseMcpV2ResidualCleanup：复用执行层阻断清单；如果没有这行代码，旧入口隐藏检查和真实阻断规则可能分裂。

PHASE49_COMPUTER_USE_TOOL_SURFACE_MARKER = "PHASE49_COMPUTER_USE_TOOL_SURFACE_READY"  # 修改代码+ComputerUseMcpV2ResidualCleanup：保留旧验收 marker 名称以兼容调用链；如果没有这行代码，Phase52 和旧场景会找不到稳定锚点。
PHASE49_COMPUTER_USE_TOOL_SURFACE_OK_TOKEN = "PHASE49_COMPUTER_USE_TOOL_SURFACE_OK"  # 修改代码+ComputerUseMcpV2ResidualCleanup：保留旧 OK token 名称但改变含义为 v2 通过；如果没有这行代码，命令行验收缺少成功标记。
PHASE49_TOOL_SURFACE_CONTRACT = "phase49_computer_use_mcp_v2_tool_surface"  # 修改代码+ComputerUseMcpV2ResidualCleanup：声明当前合同已经从 compat 改为 v2；如果没有这行代码，报告无法区分新旧工具面。
PHASE49_ACTIONS_EXPANDED = False  # 修改代码+ComputerUseMcpV2ResidualCleanup：声明本合同不额外扩大动作能力；如果没有这行代码，安全矩阵无法确认 Phase49 没有偷偷放开新动作。
PHASE49_LEGACY_TOOL_NAMES: tuple[str, ...] = tuple(sorted(COMPUTER_USE_COMPAT_BUILTIN_TOOL_NAMES))  # 修改代码+ComputerUseMcpV2ResidualCleanup：集中列出必须隐藏或阻断的旧名；如果没有这行代码，旧入口污染扫描会散落到多个文件。
PHASE49_RAW_DUPLICATE_FORBIDDEN_TOOL_NAMES: tuple[str, ...] = tuple(name for name in PHASE49_LEGACY_TOOL_NAMES if name != "request_access")  # 修改代码+ComputerUseMcpV2ResidualCleanup：MCP raw request_access 是 ClaudeCode 风格合法工具名，所以只禁止其它旧 raw 名重复；如果没有这行代码，v2 合同会把正确的授权工具误判为旧污染。
PHASE49_MCP_TOOL_NAMES: tuple[str, ...] = tuple(COMPUTER_USE_MCP_TOOL_NAMES)  # 修改代码+ComputerUseMcpV2ResidualCleanup：保存 v2 raw MCP 工具名；如果没有这行代码，合同无法核对独立 MCP server 真实工具面。
PHASE49_MCP_MODEL_TOOL_NAMES: tuple[str, ...] = tuple(f"mcp__computer-use__{name}" for name in PHASE49_MCP_TOOL_NAMES)  # 修改代码+ComputerUseMcpV2ResidualCleanup：保存模型侧前缀工具名；如果没有这行代码，报告无法确认模型应该看到哪一组名字。

def _bool_token(value: bool) -> str:  # 修改代码+ComputerUseMcpV2ResidualCleanup：函数段开始，把布尔值转为验收脚本稳定读取的小写文本；如果没有这段代码，CLI 输出会混用 True/False 和 true/false。本段到 return 结束。
    return "true" if bool(value) else "false"  # 修改代码+ComputerUseMcpV2ResidualCleanup：返回小写布尔 token；如果没有这行代码，场景断言容易因为大小写漂移失败。

def normalize_computer_use_compat_arguments(arguments: dict[str, Any]) -> dict[str, Any]:  # 修改代码+ComputerUseMcpV2ResidualCleanup：函数段开始，保留旧函数名但只返回迁移阻断结果；如果没有这段代码，旧测试或旧调用会以为还能转发到 computer_action。本段到 return 结束。
    raw_arguments = dict(arguments or {})  # 修改代码+ComputerUseMcpV2ResidualCleanup：复制输入参数用于安全审计；如果没有这行代码，调用方传入的原始字典可能被误修改。
    operation = str(raw_arguments.get("operation", raw_arguments.get("op", "")) or "").strip().lower()  # 修改代码+ComputerUseMcpV2ResidualCleanup：读取旧 operation 只用于错误说明；如果没有这行代码，迁移提示无法指出旧调用想做什么。
    return {"ok": False, "blocked_legacy_entry": True, "operation": operation, "error": "旧 computer_use/computer-use 兼容入口已停用；请使用 mcp__computer-use__* v2 MCP 工具。", "replacement_tools": list(PHASE49_MCP_MODEL_TOOL_NAMES), "tool_surface": PHASE49_TOOL_SURFACE_CONTRACT}  # 修改代码+ComputerUseMcpV2ResidualCleanup：返回显式阻断和替代工具清单；如果没有这行代码，旧入口可能悄悄绕过 v2 MCP 工具面。

def run_phase49_tool_surface_contract() -> dict[str, Any]:  # 修改代码+ComputerUseMcpV2ResidualCleanup：函数段开始，验证旧入口已隐藏且 v2 MCP 工具齐全；如果没有这段代码，Phase52 无法继续复用同一自检入口。本段到 return 结束。
    from learning_agent.tools.catalog import build_builtin_tool_catalog  # 修改代码+ComputerUseMcpV2ResidualCleanup：延迟导入内置目录用于检查旧名是否还在 catalog；如果没有这行代码，隐藏检查只能看 schema 不看目录。
    from learning_agent.tools.schemas import TOOL_SCHEMAS  # 修改代码+ComputerUseMcpV2ResidualCleanup：延迟导入内置 schema 用于检查旧名是否模型可见；如果没有这行代码，旧工具可能在 schema 中复活而不被发现。
    schema_names = {str(schema.get("function", {}).get("name", "")) for schema in TOOL_SCHEMAS if isinstance(schema.get("function", {}), dict)}  # 修改代码+ComputerUseMcpV2ResidualCleanup：收集内置模型工具名；如果没有这行代码，无法证明旧入口没有直接暴露给大模型。
    catalog_names = {tool.name for tool in build_builtin_tool_catalog()}  # 修改代码+ComputerUseMcpV2ResidualCleanup：收集内置 catalog 工具名；如果没有这行代码，tool_search 侧旧入口污染无法被发现。
    mcp_raw_names = {str(tool.get("name", "")) for tool in computer_use_mcp_tools()}  # 修改代码+ComputerUseMcpV2ResidualCleanup：读取独立 MCP server raw 工具名；如果没有这行代码，v2 工具面是否完整只能靠记忆。
    legacy_tools_hidden = not bool(set(PHASE49_LEGACY_TOOL_NAMES).intersection(schema_names))  # 修改代码+ComputerUseMcpV2ResidualCleanup：确认旧名不在内置 schema；如果没有这行代码，大模型可能继续直接看到旧 computer_action。
    catalog_clean = not bool(set(PHASE49_LEGACY_TOOL_NAMES).intersection(catalog_names))  # 修改代码+ComputerUseMcpV2ResidualCleanup：确认旧名不在内置 catalog；如果没有这行代码，deferred 工具搜索仍可能发现旧接口。
    mcp_tools_present = set(PHASE49_MCP_TOOL_NAMES).issubset(mcp_raw_names)  # 修改代码+ComputerUseMcpV2ResidualCleanup：确认 v2 raw MCP 工具齐全；如果没有这行代码，删除旧接口后可能缺少替代工具。
    duplicate_raw_names_absent = not bool(set(PHASE49_RAW_DUPLICATE_FORBIDDEN_TOOL_NAMES).intersection(mcp_raw_names))  # 修改代码+ComputerUseMcpV2ResidualCleanup：确认除合法 request_access 外没有旧 raw 名进入 MCP；如果没有这行代码，旧 computer_action 等可能在独立 MCP 内复活。
    compat_dispatch = normalize_computer_use_compat_arguments({"operation": "action"})  # 修改代码+ComputerUseMcpV2ResidualCleanup：抽样检查旧 compat 分发是否被阻断；如果没有这行代码，旧 adapter 可能继续把 action 转给旧 handler。
    compat_dispatch_blocked = bool(compat_dispatch.get("blocked_legacy_entry")) and not bool(compat_dispatch.get("ok"))  # 修改代码+ComputerUseMcpV2ResidualCleanup：把阻断结果转成验收布尔值；如果没有这行代码，报告无法判断旧兼容入口是否真正停用。
    passed = bool(legacy_tools_hidden and catalog_clean and mcp_tools_present and duplicate_raw_names_absent and compat_dispatch_blocked and not PHASE49_ACTIONS_EXPANDED)  # 修改代码+ComputerUseMcpV2ResidualCleanup：汇总 Phase49 新通过条件；如果没有这行代码，单项通过会被误当成整体通过。
    return {"marker": PHASE49_COMPUTER_USE_TOOL_SURFACE_MARKER, "ok_token": PHASE49_COMPUTER_USE_TOOL_SURFACE_OK_TOKEN if passed else "", "contract": PHASE49_TOOL_SURFACE_CONTRACT, "passed": passed, "legacy_tools_hidden": legacy_tools_hidden, "catalog_clean": catalog_clean, "mcp_tools_present": mcp_tools_present, "duplicate_raw_names_absent": duplicate_raw_names_absent, "compat_dispatch_blocked": compat_dispatch_blocked, "actions_expanded": PHASE49_ACTIONS_EXPANDED, "legacy_tool_names": list(PHASE49_LEGACY_TOOL_NAMES), "mcp_model_tool_names": list(PHASE49_MCP_MODEL_TOOL_NAMES)}  # 修改代码+ComputerUseMcpV2ResidualCleanup：返回完整结构化报告；如果没有这行代码，测试和真实终端看不到旧入口是否清干净。

def phase49_cli_line(report: dict[str, Any]) -> str:  # 修改代码+ComputerUseMcpV2ResidualCleanup：函数段开始，把 Phase49 v2 报告压成一行稳定 token；如果没有这段代码，验收器需要解析完整 JSON。本段到 return 结束。
    ok_token = str(report.get("ok_token") or "PHASE49_COMPUTER_USE_TOOL_SURFACE_FAILED")  # 修改代码+ComputerUseMcpV2ResidualCleanup：失败时不再输出 OK token；如果没有这行代码，真实终端日志会把失败合同误判为通过。
    return f"{ok_token} legacy_tools_hidden={_bool_token(report.get('legacy_tools_hidden'))} catalog_clean={_bool_token(report.get('catalog_clean'))} mcp_tools_present={_bool_token(report.get('mcp_tools_present'))} duplicate_raw_names_absent={_bool_token(report.get('duplicate_raw_names_absent'))} compat_dispatch_blocked={_bool_token(report.get('compat_dispatch_blocked'))} actions_expanded={_bool_token(report.get('actions_expanded'))} marker={PHASE49_COMPUTER_USE_TOOL_SURFACE_MARKER}"  # 修改代码+ComputerUseMcpV2ResidualCleanup：输出 v2 合同 token；如果没有这行代码，验收日志会继续被历史合同文案误导。

def main() -> int:  # 修改代码+ComputerUseMcpV2ResidualCleanup：函数段开始，提供命令行自检入口；如果没有这段代码，真实终端无法单独运行工具面合同。本段到 return 结束。
    report = run_phase49_tool_surface_contract()  # 修改代码+ComputerUseMcpV2ResidualCleanup：执行 v2 工具面合同；如果没有这行代码，CLI 输出没有事实来源。
    print(phase49_cli_line(report))  # 修改代码+ComputerUseMcpV2ResidualCleanup：打印稳定 token 行；如果没有这行代码，验收脚本难以快速判断结果。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 修改代码+ComputerUseMcpV2ResidualCleanup：打印结构化报告；如果没有这行代码，失败时不容易看出哪个门禁没过。
    print(PHASE49_COMPUTER_USE_TOOL_SURFACE_MARKER)  # 修改代码+ComputerUseMcpV2ResidualCleanup：单独打印 ready marker；如果没有这行代码，旧场景可能无法等待到阶段输出。
    return 0 if bool(report.get("passed")) else 1  # 修改代码+ComputerUseMcpV2ResidualCleanup：按合同通过情况返回退出码；如果没有这行代码，失败也可能被当作成功。

if __name__ == "__main__":  # 修改代码+ComputerUseMcpV2ResidualCleanup：允许直接运行本文件；如果没有这行代码，手动排查需要额外写 Python 调用。
    raise SystemExit(main())  # 修改代码+ComputerUseMcpV2ResidualCleanup：把 main 的退出码传给进程；如果没有这行代码，命令行自检不会真正执行。
