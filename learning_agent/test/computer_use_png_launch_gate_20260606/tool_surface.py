"""Windows Computer Use Phase49 兼容工具面。"""  # 新增代码+Phase49ComputerUseToolSurface: 标明本文件负责 ClaudeCode/MCP 风格兼容工具入口；如果没有这行代码，读者不知道统一工具面适配层在哪里。
from __future__ import annotations  # 新增代码+Phase49ComputerUseToolSurface: 启用延迟类型解析；如果没有这行代码，旧入口遇到前向类型注解时更容易导入失败。

import json  # 新增代码+Phase49ComputerUseToolSurface: 导入 JSON 工具用于 CLI 自检输出；如果没有这行代码，验收器难以读取完整报告。
import hashlib  # 新增代码+Phase92UniversalComputerUse：导入哈希库用于 mode prompt 脱敏审计；如果没有这行代码，compat dispatch 只能记录 prompt 原文或完全不可追踪。
from typing import Any  # 新增代码+Phase49ComputerUseToolSurface: 导入 Any 表示模型工具参数的动态 JSON 值；如果没有这行代码，适配接口类型边界不清楚。

PHASE49_COMPUTER_USE_TOOL_SURFACE_MARKER = "PHASE49_COMPUTER_USE_TOOL_SURFACE_READY"  # 新增代码+Phase49ComputerUseToolSurface: 定义 Phase49 ready marker；如果没有这行代码，真实终端验收无法稳定匹配本阶段。
PHASE49_COMPUTER_USE_TOOL_SURFACE_OK_TOKEN = "PHASE49_COMPUTER_USE_TOOL_SURFACE_OK"  # 新增代码+Phase49ComputerUseToolSurface: 定义 Phase49 OK token；如果没有这行代码，debug log 无法区分自检通过和普通输出。
PHASE49_TOOL_SURFACE_CONTRACT = "phase49_computer_use_compat_tool_surface"  # 新增代码+Phase49ComputerUseToolSurface: 定义兼容工具面合同名称；如果没有这行代码，状态和报告无法说明当前工具面版本。
PHASE49_ACTIONS_EXPANDED = False  # 新增代码+Phase49ComputerUseToolSurface: 明确 Phase49 只增加兼容工具名不扩大真实动作能力；如果没有这行代码，用户可能误解为动作面扩大。
PHASE49_LEGACY_TOOL_NAMES: tuple[str, ...] = ("computer_status", "computer_observe", "computer_action")  # 新增代码+Phase49ComputerUseToolSurface: 固定旧工具名清单；如果没有这行代码，自检无法确认旧入口仍保留。
PHASE49_COMPAT_TOOL_NAMES: tuple[str, ...] = ("computer_use", "computer-use")  # 新增代码+Phase49ComputerUseToolSurface: 固定新增兼容工具名清单；如果没有这行代码，schema/catalog/执行器可能配置不一致。
PHASE49_OPERATION_VALUES: tuple[str, ...] = ("status", "observe", "action", "mode", "run_prompt")  # 修改代码+Phase92UniversalComputerUse：把通用 Computer Use mode 加入兼容入口枚举；如果没有这行代码，用户 prompt 无法通过旧 computer_use 工具进入新运行时。


def _bool_token(value: bool) -> str:  # 新增代码+Phase49ComputerUseToolSurface: 函数段开始，把布尔值转成小写 token；如果没有这段函数，CLI 输出容易出现 True/False 大小写漂移。
    return "true" if bool(value) else "false"  # 新增代码+Phase49ComputerUseToolSurface: 返回验收器期望的 true/false 文本；如果没有这行代码，场景断言会因为大小写不一致失败。
# 新增代码+Phase49ComputerUseToolSurface: 函数段结束，_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化 helper 范围。


def _safe_text(value: Any, limit: int = 120) -> str:  # 新增代码+Phase49ComputerUseToolSurface: 函数段开始，规范化短文本参数；如果没有这段函数，operation/action 可能被空白或换行污染。
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()  # 新增代码+Phase49ComputerUseToolSurface: 把任意输入压成单行；如果没有这行代码，工具名和操作名可能不稳定。
    return text[:limit]  # 新增代码+Phase49ComputerUseToolSurface: 限制文本长度；如果没有这行代码，异常长参数会污染报告和日志。
# 新增代码+Phase49ComputerUseToolSurface: 函数段结束，_safe_text 到此结束；如果没有这个边界说明，读者不容易看出文本规整范围。


# 新增代码+Phase92UniversalComputerUse：函数段开始，_phase92_compat_sha256_16 给 mode prompt 生成审计短哈希；如果没有这段函数，compat 层无法既隐藏原文又保留可追踪性。
def _phase92_compat_sha256_16(value: Any) -> str:  # 新增代码+Phase92UniversalComputerUse：定义兼容层短哈希函数；如果没有这行代码，mode audit_arguments 无法稳定生成指纹。
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)  # 新增代码+Phase92UniversalComputerUse：稳定序列化任意 JSON 值；如果没有这行代码，同一 prompt 在不同顺序下可能哈希不一致。
    return hashlib.sha256(serialized.encode("utf-8", errors="replace")).hexdigest()[:16]  # 新增代码+Phase92UniversalComputerUse：返回 SHA256 前 16 位；如果没有这行代码，短哈希没有真实内容来源。
# 新增代码+Phase92UniversalComputerUse：函数段结束，_phase92_compat_sha256_16 到此结束；如果没有这个边界说明，初学者不容易看出 prompt 审计哈希范围。


def normalize_computer_use_compat_arguments(arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+Phase49ComputerUseToolSurface: 函数段开始，把兼容工具参数转成旧三工具调用；如果没有这段函数，兼容工具只能另写旁路逻辑。
    raw_arguments = dict(arguments or {})  # 新增代码+Phase49ComputerUseToolSurface: 复制模型参数避免修改调用方对象；如果没有这行代码，适配过程可能污染原始参数。
    operation = _safe_text(raw_arguments.get("operation", raw_arguments.get("op", "status"))).lower()  # 新增代码+Phase49ComputerUseToolSurface: 读取 operation/op 并默认 status；如果没有这行代码，ClaudeCode 风格 op 字段无法兼容。
    if operation in {"mode", "run_prompt"}:  # 新增代码+Phase92UniversalComputerUse：识别通用 Computer Use mode；如果没有这行代码，用户自然语言 prompt 会被当成未知 operation 拒绝。
        prompt_text = _safe_text(raw_arguments.get("prompt", raw_arguments.get("task", "")), limit=1000)  # 新增代码+Phase92UniversalComputerUse：读取并限制 mode prompt；如果没有这行代码，新运行时拿不到用户任务文本。
        mode_arguments = {"prompt": prompt_text, "real_actions": bool(raw_arguments.get("real_actions", False))}  # 新增代码+Phase92UniversalComputerUse：构造新运行时参数且默认不执行真实动作；如果没有这行代码，mode 路由没有稳定入参。
        audit_arguments = {"prompt_sha256_16": _phase92_compat_sha256_16(prompt_text), "prompt_length": len(prompt_text), "prompt_text_included": False, "real_actions": bool(mode_arguments["real_actions"])}  # 新增代码+Phase92UniversalComputerUse：构造脱敏审计参数；如果没有这行代码，dispatch 日志可能记录 prompt 原文。
        return {"ok": True, "target_tool": "computer_use_mode", "arguments": mode_arguments, "audit_arguments": audit_arguments, "operation": operation, "tool_surface": PHASE49_TOOL_SURFACE_CONTRACT, "action_like": bool(mode_arguments["real_actions"])}  # 新增代码+Phase92UniversalComputerUse：返回通用 mode 调用描述；如果没有这行代码，agent 无法从兼容入口分发到 Phase92。
    if operation == "status":  # 新增代码+Phase49ComputerUseToolSurface: 识别状态查询；如果没有这行代码，统一工具无法转发到 computer_status。
        return {"ok": True, "target_tool": "computer_status", "arguments": {}, "operation": operation, "tool_surface": PHASE49_TOOL_SURFACE_CONTRACT}  # 新增代码+Phase49ComputerUseToolSurface: 返回旧状态工具调用描述；如果没有这行代码，status operation 没有转发目标。
    if operation == "observe":  # 新增代码+Phase49ComputerUseToolSurface: 识别只读观察；如果没有这行代码，统一工具无法转发到 computer_observe。
        observe_arguments = {"action": _safe_text(raw_arguments.get("action", raw_arguments.get("observe_action", "list_windows")))}  # 新增代码+Phase49ComputerUseToolSurface: 构造 observe 参数并兼容 observe_action；如果没有这行代码，兼容工具不知道观察哪类状态。
        if "window" in raw_arguments:  # 新增代码+Phase49ComputerUseToolSurface: 只有用户提供窗口时才传递 window；如果没有这行代码，空 window 会污染 list_windows 等无窗口观察。
            observe_arguments["window"] = raw_arguments.get("window")  # 新增代码+Phase49ComputerUseToolSurface: 透传可信窗口引用；如果没有这行代码，get_window_state 无法指定目标窗口。
        return {"ok": True, "target_tool": "computer_observe", "arguments": observe_arguments, "operation": operation, "tool_surface": PHASE49_TOOL_SURFACE_CONTRACT}  # 新增代码+Phase49ComputerUseToolSurface: 返回旧观察工具调用描述；如果没有这行代码，observe operation 没有转发目标。
    if operation == "action":  # 新增代码+Phase49ComputerUseToolSurface: 识别桌面动作；如果没有这行代码，统一工具无法转发到 computer_action。
        action_arguments: dict[str, Any] = {"action": _safe_text(raw_arguments.get("action", "")), "confirm_desktop_control": bool(raw_arguments.get("confirm_desktop_control", raw_arguments.get("confirmed", False)))}  # 新增代码+Phase49ComputerUseToolSurface: 构造动作名和显式确认字段；如果没有这行代码，高风险动作可能绕过 confirm_desktop_control 门禁。
        for field_name in ("x", "y", "text", "key", "delta", "points", "window", "app_name", "target_app", "app", "target"):  # 修改代码+ModelLoopLaunchAppTool: 遍历动作工具允许的坐标、路径、窗口和启动应用字段；如果没有这行代码，launch_app 目标或 drag_path 路径会在兼容入口丢失。
            if field_name in raw_arguments:  # 新增代码+Phase49ComputerUseToolSurface: 只透传模型实际提供的字段；如果没有这行代码，缺省 None 字段会污染旧 schema 语义。
                action_arguments[field_name] = raw_arguments[field_name]  # 新增代码+Phase49ComputerUseToolSurface: 写入旧动作参数；如果没有这行代码，兼容动作无法到达 controller。
        return {"ok": True, "target_tool": "computer_action", "arguments": action_arguments, "operation": operation, "tool_surface": PHASE49_TOOL_SURFACE_CONTRACT}  # 新增代码+Phase49ComputerUseToolSurface: 返回旧动作工具调用描述；如果没有这行代码，action operation 没有转发目标。
    return {"ok": False, "error": f"不支持的 computer_use operation：{operation}", "allowed_operations": list(PHASE49_OPERATION_VALUES), "operation": operation, "tool_surface": PHASE49_TOOL_SURFACE_CONTRACT}  # 新增代码+Phase49ComputerUseToolSurface: 返回未知 operation 错误；如果没有这行代码，坏参数会落到不可预测路径。
# 新增代码+Phase49ComputerUseToolSurface: 函数段结束，normalize_computer_use_compat_arguments 到此结束；如果没有这个边界说明，读者不容易看出适配范围。


def run_phase49_tool_surface_contract() -> dict[str, Any]:  # 新增代码+Phase49ComputerUseToolSurface: 函数段开始，运行无副作用合同自检；如果没有这段函数，真实终端无法快速验收 Phase49。
    from learning_agent.tools.catalog import build_builtin_tool_catalog  # 新增代码+Phase49ComputerUseToolSurface: 延迟导入工具目录避免底层循环；如果没有这行代码，自检无法检查 catalog 元数据。
    from learning_agent.tools.executor import _builtin_tool_handlers  # 新增代码+Phase49ComputerUseToolSurface: 延迟导入执行器分发表；如果没有这行代码，自检无法证明兼容名有执行路由。
    from learning_agent.tools.schemas import TOOL_SCHEMAS  # 新增代码+Phase49ComputerUseToolSurface: 延迟导入工具 schema；如果没有这行代码，自检无法证明模型可见工具名。
    schema_names = {schema.get("function", {}).get("name", "") for schema in TOOL_SCHEMAS if isinstance(schema.get("function", {}), dict)}  # 新增代码+Phase49ComputerUseToolSurface: 收集内置 schema 工具名；如果没有这行代码，无法检查旧名和兼容名是否暴露。
    catalog = {tool.name: tool for tool in build_builtin_tool_catalog()}  # 新增代码+Phase49ComputerUseToolSurface: 构建并索引工具目录；如果没有这行代码，无法检查风险和能力包元数据。
    class _FakeAgent:  # 新增代码+Phase49ComputerUseToolSurface: 类段开始，构造最小 agent 用于检查执行器分发表；如果没有这个类，自检需要启动真实 agent。
        def __getattr__(self, name: str) -> Any:  # 修改代码+Phase49ComputerUseToolSurface: 为执行器分发表里未显式关心的私有方法提供占位；如果没有这行代码，自检会因为 unrelated 工具 handler 缺属性而失败。
            if name.startswith("_"):  # 修改代码+Phase49ComputerUseToolSurface: 只给私有工具 handler 名称兜底；如果没有这行代码，普通属性拼写错误也会被误吞。
                def _stub(arguments: dict[str, Any]) -> str:  # 修改代码+Phase49ComputerUseToolSurface: 定义无副作用占位 handler；如果没有这行代码，分发表需要的非 Phase49 工具无法被绑定。
                    return str(arguments)  # 修改代码+Phase49ComputerUseToolSurface: 返回参数文本即可；如果没有这行代码，占位 handler 调用时没有稳定结果。
                return _stub  # 修改代码+Phase49ComputerUseToolSurface: 返回可调用占位函数；如果没有这行代码，执行器仍会拿到缺失属性错误。
            raise AttributeError(name)  # 修改代码+Phase49ComputerUseToolSurface: 非私有属性保持标准 AttributeError；如果没有这行代码，真实拼写错误会被隐藏。
        def _computer_use_compat(self, arguments: dict[str, Any]) -> str:  # 新增代码+Phase49ComputerUseToolSurface: 提供兼容工具 handler 占位；如果没有这行代码，分发表无法绑定该方法。
            return str(arguments)  # 新增代码+Phase49ComputerUseToolSurface: 返回参数文本即可；如果没有这行代码，handler 占位不是可调用函数。
        def _computer_status(self, arguments: dict[str, Any]) -> str:  # 新增代码+Phase49ComputerUseToolSurface: 提供旧状态工具 handler 占位；如果没有这行代码，分发表构建会缺属性。
            return str(arguments)  # 新增代码+Phase49ComputerUseToolSurface: 返回参数文本即可；如果没有这行代码，handler 占位不是可调用函数。
        def _computer_observe(self, arguments: dict[str, Any]) -> str:  # 新增代码+Phase49ComputerUseToolSurface: 提供旧观察工具 handler 占位；如果没有这行代码，分发表构建会缺属性。
            return str(arguments)  # 新增代码+Phase49ComputerUseToolSurface: 返回参数文本即可；如果没有这行代码，handler 占位不是可调用函数。
        def _computer_action(self, arguments: dict[str, Any]) -> str:  # 新增代码+Phase49ComputerUseToolSurface: 提供旧动作工具 handler 占位；如果没有这行代码，分发表构建会缺属性。
            return str(arguments)  # 新增代码+Phase49ComputerUseToolSurface: 返回参数文本即可；如果没有这行代码，handler 占位不是可调用函数。
    handlers = _builtin_tool_handlers(_FakeAgent())  # 新增代码+Phase49ComputerUseToolSurface: 构建执行器分发表；如果没有这行代码，无法确认兼容名能被路由。
    observe_dispatch = normalize_computer_use_compat_arguments({"operation": "observe", "action": "list_windows"})  # 新增代码+Phase49ComputerUseToolSurface: 自检 observe 参数规范化；如果没有这行代码，same_controller 证据缺 observe 样本。
    action_dispatch = normalize_computer_use_compat_arguments({"operation": "action", "action": "click", "confirm_desktop_control": True})  # 新增代码+Phase49ComputerUseToolSurface: 自检 action 参数规范化；如果没有这行代码，same_controller 证据缺 action 样本。
    legacy_tools = all(name in schema_names for name in PHASE49_LEGACY_TOOL_NAMES)  # 新增代码+Phase49ComputerUseToolSurface: 检查旧工具名仍在 schema 中；如果没有这行代码，报告无法证明没有破坏兼容。
    compat_tools = all(name in schema_names and name in handlers for name in PHASE49_COMPAT_TOOL_NAMES)  # 新增代码+Phase49ComputerUseToolSurface: 检查兼容工具既暴露又可执行；如果没有这行代码，schema 空壳不会被发现。
    same_controller = bool(observe_dispatch.get("target_tool") == "computer_observe" and action_dispatch.get("target_tool") == "computer_action")  # 新增代码+Phase49ComputerUseToolSurface: 检查适配目标仍是旧三工具；如果没有这行代码，旁路实现无法被发现。
    catalog_ok = all(catalog.get(name) is not None and catalog[name].capability_pack == "computer_use" and catalog[name].risk_level == "high" for name in PHASE49_COMPAT_TOOL_NAMES)  # 新增代码+Phase49ComputerUseToolSurface: 检查兼容工具元数据高风险且归入 computer_use 包；如果没有这行代码，工具池和权限策略可能失真。
    return {"marker": PHASE49_COMPUTER_USE_TOOL_SURFACE_MARKER, "ok_token": PHASE49_COMPUTER_USE_TOOL_SURFACE_OK_TOKEN, "legacy_tools": legacy_tools, "compat_tools": compat_tools, "same_controller": same_controller, "catalog": catalog_ok, "actions_expanded": PHASE49_ACTIONS_EXPANDED}  # 新增代码+Phase49ComputerUseToolSurface: 返回完整合同自检结果；如果没有这行代码，CLI 无法拼接稳定 token。
# 新增代码+Phase49ComputerUseToolSurface: 函数段结束，run_phase49_tool_surface_contract 到此结束；如果没有这个边界说明，读者不容易看出自检范围。


def phase49_cli_line(report: dict[str, Any]) -> str:  # 新增代码+Phase49ComputerUseToolSurface: 函数段开始，把报告转成稳定单行；如果没有这段函数，真实终端验收需要解析完整 JSON。
    return f"{PHASE49_COMPUTER_USE_TOOL_SURFACE_OK_TOKEN} legacy_tools={_bool_token(bool(report.get('legacy_tools')))} compat_tools={_bool_token(bool(report.get('compat_tools')))} same_controller={_bool_token(bool(report.get('same_controller')))} catalog={_bool_token(bool(report.get('catalog')))} actions_expanded={_bool_token(bool(report.get('actions_expanded')))} marker={PHASE49_COMPUTER_USE_TOOL_SURFACE_MARKER}"  # 新增代码+Phase49ComputerUseToolSurface: 返回固定顺序 token；如果没有这行代码，场景断言容易因为输出漂移失败。
# 新增代码+Phase49ComputerUseToolSurface: 函数段结束，phase49_cli_line 到此结束；如果没有这个边界说明，读者不容易看出 CLI 行格式范围。


def main() -> int:  # 新增代码+Phase49ComputerUseToolSurface: 函数段开始，提供命令行自检入口；如果没有这段函数，真实终端场景无法直接运行 Phase49 检查。
    report = run_phase49_tool_surface_contract()  # 新增代码+Phase49ComputerUseToolSurface: 运行合同自检；如果没有这行代码，CLI 没有真实报告。
    print(phase49_cli_line(report))  # 新增代码+Phase49ComputerUseToolSurface: 打印验收器优先匹配的单行 token；如果没有这行代码，debug log 缺少稳定成功行。
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+Phase49ComputerUseToolSurface: 打印结构化报告便于人工复盘；如果没有这行代码，失败时难以定位哪个合同条件不成立。
    print(PHASE49_COMPUTER_USE_TOOL_SURFACE_MARKER)  # 新增代码+Phase49ComputerUseToolSurface: 单独打印阶段 marker；如果没有这行代码，验收器可能只看到 OK token 看不到 ready marker。
    return 0  # 新增代码+Phase49ComputerUseToolSurface: 返回成功退出码；如果没有这行代码，命令可能被误判失败。
# 新增代码+Phase49ComputerUseToolSurface: 函数段结束，main 到此结束；如果没有这个边界说明，读者不容易看出 CLI 主入口范围。


if __name__ == "__main__":  # 新增代码+Phase49ComputerUseToolSurface: 允许直接运行本模块；如果没有这行代码，初学者双击或命令行运行不会执行自检。
    raise SystemExit(main())  # 新增代码+Phase49ComputerUseToolSurface: 用 main 的退出码结束进程；如果没有这行代码，脚本入口没有稳定退出状态。
