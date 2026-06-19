"""Computer Use MCP v2 stdio server bridge."""  # 修改代码+ClaudeCodeLifecycleParity：说明本文件对应 ClaudeCode mcpServer 入口；如果没有这行代码，读者不容易知道 standalone tools/list 在这里处理。
from __future__ import annotations  # 修改代码+ClaudeCodeLifecycleParity：延迟类型注解解析；如果没有这行代码，导入阶段更容易被循环类型引用影响。

import argparse  # 修改代码+ClaudeCodeLifecycleParity：导入命令行参数解析；如果没有这行代码，--selftest 入口无法工作。
import json  # 修改代码+ClaudeCodeLifecycleParity：导入 JSON 编解码；如果没有这行代码，JSON-RPC 和 selftest 输出无法实现。
import sys  # 修改代码+ClaudeCodeLifecycleParity：导入 stdin/stdout；如果没有这行代码，stdio server 无法作为 MCP 子进程运行。
from queue import Empty, Queue  # 修改代码+ClaudeCodeLifecycleParity：导入线程安全队列和超时异常；如果没有这行代码，tools/list inventory 超时无法实现。
from threading import Thread  # 修改代码+ClaudeCodeLifecycleParity：导入后台线程；如果没有这行代码，慢速 Windows app 枚举会卡住主 stdio 线程。
from time import perf_counter  # 修改代码+ClaudeCodeLifecycleParity：导入高精度计时；如果没有这行代码，inventory trace 无法记录耗时。
from typing import Any, TextIO  # 修改代码+ClaudeCodeLifecycleParity：导入通用 JSON 类型和文本流类型；如果没有这行代码，server helper 边界不清楚。

from learning_agent.computer_use_mcp_v2.claudecode_bridge.hostAdapter import WindowsHostAdapter  # 修改代码+ClaudeCodeLifecycleParity：导入默认 Windows host；如果没有这行代码，独立 server 没有桌面宿主对象。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import COMPUTER_USE_MCP_READY_MARKER, COMPUTER_USE_MCP_SERVER_NAME, assert_no_shell_surface, computer_use_mcp_tools  # 修改代码+ClaudeCodeLifecycleParity：导入 v2 工具面和 ready marker；如果没有这行代码，tools/list 和 selftest 无法生成正确 schema。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.result_blocks import mcp_content_from_result  # 修改代码+ClaudeCodeLifecycleParity：导入 MCP content 包装器；如果没有这行代码，tools/call 输出格式不稳定。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import ComputerUseMcpV2Context, dispatch_computer_use_mcp_v2_tool  # 修改代码+ClaudeCodeLifecycleParity：导入统一 runtime 和 context；如果没有这行代码，server 无法执行工具。

WINDOWS_APP_INVENTORY_TIMEOUT_SECONDS = 1.0  # 修改代码+ClaudeCodeLifecycleParity：限制 tools/list 动态应用清单最多等待 1 秒；如果没有这行代码，坏 inventory 可能拖死工具发现。
WINDOWS_APP_INVENTORY_MAX_HINTS = 8  # 修改代码+ClaudeCodeLifecycleParity：限制注入 request_access 描述的候选数量；如果没有这行代码，tools/list 描述可能过长浪费上下文。


def _response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:  # 修改代码+ClaudeCodeLifecycleParity：函数段开始，生成 JSON-RPC 成功响应；如果没有这段函数，响应结构会重复且容易漂移。
    return {"jsonrpc": "2.0", "id": request_id, "result": result}  # 修改代码+ClaudeCodeLifecycleParity：返回标准成功响应；如果没有这行代码，MCP client 无法匹配请求结果。
# 修改代码+ClaudeCodeLifecycleParity：函数段结束，_response 到此结束；如果没有这个边界说明，用户不容易看出响应构造范围。


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:  # 修改代码+ClaudeCodeLifecycleParity：函数段开始，生成 JSON-RPC 错误响应；如果没有这段函数，错误格式会重复且不稳定。
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": int(code), "message": str(message)}}  # 修改代码+ClaudeCodeLifecycleParity：返回标准错误响应；如果没有这行代码，client 难以识别失败。
# 修改代码+ClaudeCodeLifecycleParity：函数段结束，_error 到此结束；如果没有这个边界说明，用户不容易看出错误构造范围。


def _windows_app_inventory_hint_loader() -> str:  # 修改代码+ClaudeCodeLifecycleParity：函数段开始，读取 Windows 安全应用候选并格式化给模型；如果没有这段函数，tools/list 无法动态提示已安装应用。
    from learning_agent.computer_use_mcp_v2.windows_runtime.windows_app_inventory import build_windows_app_inventory, format_windows_app_inventory_for_model  # 修改代码+ClaudeCodeLifecycleParity：延迟导入 inventory 模块；如果没有这行代码，server 启动会为非 tools/list 路径也加载扫描依赖。
    apps = build_windows_app_inventory(max_count=WINDOWS_APP_INVENTORY_MAX_HINTS)  # 修改代码+ClaudeCodeLifecycleParity：读取经过安全过滤的应用候选；如果没有这行代码，request_access.description 没有真实 Windows 候选。
    return format_windows_app_inventory_for_model(apps)  # 修改代码+ClaudeCodeLifecycleParity：复用现有模型安全格式化；如果没有这行代码，可能泄露路径或输出不一致字段。
# 修改代码+ClaudeCodeLifecycleParity：函数段结束，_windows_app_inventory_hint_loader 到此结束；如果没有这个边界说明，用户不容易看出 inventory 读取范围。


def _load_windows_app_inventory_hint(timeout_seconds: float = WINDOWS_APP_INVENTORY_TIMEOUT_SECONDS, loader: Any | None = None) -> dict[str, Any]:  # 修改代码+ClaudeCodeLifecycleParity：函数段开始，带超时读取动态 app inventory；如果没有这段函数，tools/list 可能被慢枚举卡住。
    result_queue: Queue[tuple[bool, str]] = Queue(maxsize=1)  # 修改代码+ClaudeCodeLifecycleParity：创建单结果队列；如果没有这行代码，worker 线程无法安全传回结果。
    started_at = perf_counter()  # 修改代码+ClaudeCodeLifecycleParity：记录开始时间；如果没有这行代码，trace 无法计算耗时。
    safe_loader = loader if callable(loader) else _windows_app_inventory_hint_loader  # 修改代码+ClaudeCodeLifecycleParity：允许测试注入 loader；如果没有这行代码，timeout 测试会依赖真实系统环境。

    def worker() -> None:  # 修改代码+ClaudeCodeLifecycleParity：函数段开始，在线程中执行可能慢的 inventory loader；如果没有这段函数，主线程无法限时等待。
        try:  # 修改代码+ClaudeCodeLifecycleParity：捕获 loader 异常；如果没有这行代码，worker 异常会丢失且主线程只能超时。
            result_queue.put((True, str(safe_loader() or "")))  # 修改代码+ClaudeCodeLifecycleParity：把成功 hint 写入队列；如果没有这行代码，主线程拿不到动态描述。
        except Exception as error:  # 修改代码+ClaudeCodeLifecycleParity：捕获 inventory 读取错误；如果没有这行代码，错误无法进入 debug trace。
            result_queue.put((False, str(error)))  # 修改代码+ClaudeCodeLifecycleParity：把错误文本写入队列；如果没有这行代码，tools/list 不知道失败原因。
    # 修改代码+ClaudeCodeLifecycleParity：函数段结束，worker 到此结束；如果没有这个边界说明，用户不容易看出线程工作范围。

    Thread(target=worker, name="computer-use-tools-list-app-inventory", daemon=True).start()  # 修改代码+ClaudeCodeLifecycleParity：启动 daemon 线程防止慢枚举阻塞进程退出；如果没有这行代码，超时策略无法执行。
    safe_timeout = max(0.0, float(timeout_seconds))  # 修改代码+ClaudeCodeLifecycleParity：规范化超时秒数；如果没有这行代码，负数或坏参数可能让队列等待异常。
    try:  # 修改代码+ClaudeCodeLifecycleParity：等待 worker 在预算内返回；如果没有这行代码，timeout 不会被转换成结构化 fallback。
        ok, value = result_queue.get(timeout=safe_timeout)  # 修改代码+ClaudeCodeLifecycleParity：限时读取 worker 结果；如果没有这行代码，主线程无法拿到动态 hint 或错误。
    except Empty:  # 修改代码+ClaudeCodeLifecycleParity：处理超时；如果没有这行代码，慢 inventory 会让 tools/list 抛异常或卡住。
        return {"hint": "", "debug": {"status": "timeout", "timeout_seconds": safe_timeout, "elapsed_seconds": round(perf_counter() - started_at, 6)}}  # 修改代码+ClaudeCodeLifecycleParity：返回空 hint 和 timeout debug；如果没有这行代码，超时时无法回退静态 schema。
    elapsed_seconds = round(perf_counter() - started_at, 6)  # 修改代码+ClaudeCodeLifecycleParity：计算耗时；如果没有这行代码，ok/error trace 缺少性能证据。
    if ok:  # 修改代码+ClaudeCodeLifecycleParity：判断 worker 是否成功；如果没有这行代码，错误文本会被当作 hint 注入模型。
        return {"hint": value, "debug": {"status": "ok", "elapsed_seconds": elapsed_seconds, "hint_chars": len(value)}}  # 修改代码+ClaudeCodeLifecycleParity：返回成功 hint 和 debug；如果没有这行代码，tools/list 无法动态增强描述。
    return {"hint": "", "debug": {"status": "error", "elapsed_seconds": elapsed_seconds, "error": value}}  # 修改代码+ClaudeCodeLifecycleParity：返回空 hint 和错误 debug；如果没有这行代码，inventory 异常会破坏 tools/list。
# 修改代码+ClaudeCodeLifecycleParity：函数段结束，_load_windows_app_inventory_hint 到此结束；如果没有这个边界说明，用户不容易看出超时回退范围。


def _record_tools_list_inventory_trace(context: ComputerUseMcpV2Context, debug: dict[str, Any]) -> None:  # 修改代码+ClaudeCodeLifecycleParity：函数段开始，记录 tools/list 动态 inventory 或 disabled 状态；如果没有这段函数，失败回退或禁用原因无法审计。
    if callable(context.record_runtime_trace):  # 修改代码+ClaudeCodeLifecycleParity：只有绑定 trace 回调时才记录；如果没有这行代码，独立测试 context 会因 None 回调崩溃。
        context.record_runtime_trace({"event": "computer_use_tools_list_app_inventory", **dict(debug)})  # 修改代码+ClaudeCodeLifecycleParity：写入状态、耗时、错误或禁用原因；如果没有这行代码，timeout/error/disabled 不会留下调试证据。
# 修改代码+ClaudeCodeLifecycleParity：函数段结束，_record_tools_list_inventory_trace 到此结束；如果没有这个边界说明，用户不容易看出 trace 写入范围。


def _computer_use_tools_list_disabled_state(context: ComputerUseMcpV2Context) -> dict[str, Any]:  # 新增代码+ClaudeCodeLifecycleParity：函数段开始，计算 tools/list 是否应返回空工具列表；如果没有这段函数，disabled 逻辑会散落在 JSON-RPC 分支里。
    mode_disabled = False  # 新增代码+ClaudeCodeLifecycleParity：预置模式级禁用为否；如果没有这一行，后续异常路径可能引用未定义变量。
    context_disabled = False  # 新增代码+ClaudeCodeLifecycleParity：预置上下文禁用为否；如果没有这一行，后续异常路径可能引用未定义变量。
    disabled_errors: list[str] = []  # 新增代码+ClaudeCodeLifecycleParity：保存禁用判断异常摘要；如果没有这一行，失败关闭时没有审计原因。
    if callable(context.is_computer_use_disabled):  # 新增代码+ClaudeCodeLifecycleParity：只在绑定模式禁用回调时调用；如果没有这一行，None 回调会导致异常。
        try:  # 新增代码+ClaudeCodeLifecycleParity：保护禁用判断回调；如果没有这一行，状态读取异常会破坏工具发现。
            mode_disabled = bool(context.is_computer_use_disabled())  # 新增代码+ClaudeCodeLifecycleParity：读取模式级禁用状态；如果没有这一行，ClaudeCode adapter.isDisabled 语义无法对齐。
        except Exception as error:  # 新增代码+ClaudeCodeLifecycleParity：捕获模式禁用判断异常；如果没有这一行，坏状态会让 tools/list 崩溃。
            mode_disabled = True  # 新增代码+ClaudeCodeLifecycleParity：禁用判断异常时失败关闭；如果没有这一行，异常状态下可能继续暴露桌面工具。
            disabled_errors.append(f"mode:{type(error).__name__}:{error}")  # 新增代码+ClaudeCodeLifecycleParity：记录模式禁用异常；如果没有这一行，排查时不知道为什么 tools/list 为空。
    if callable(context.is_computer_use_context_disabled):  # 新增代码+ClaudeCodeLifecycleParity：只在绑定上下文禁用回调时调用；如果没有这一行，None 回调会导致异常。
        try:  # 新增代码+ClaudeCodeLifecycleParity：保护上下文禁用判断回调；如果没有这一行，状态读取异常会破坏工具发现。
            context_disabled = bool(context.is_computer_use_context_disabled())  # 新增代码+ClaudeCodeLifecycleParity：读取当前上下文禁用状态；如果没有这一行，单轮禁用不会生效。
        except Exception as error:  # 新增代码+ClaudeCodeLifecycleParity：捕获上下文禁用判断异常；如果没有这一行，坏状态会让 tools/list 崩溃。
            context_disabled = True  # 新增代码+ClaudeCodeLifecycleParity：上下文判断异常时失败关闭；如果没有这一行，异常状态下可能继续暴露桌面工具。
            disabled_errors.append(f"context:{type(error).__name__}:{error}")  # 新增代码+ClaudeCodeLifecycleParity：记录上下文禁用异常；如果没有这一行，排查时不知道为什么 tools/list 为空。
    disabled = bool(mode_disabled or context_disabled)  # 新增代码+ClaudeCodeLifecycleParity：汇总是否禁用；如果没有这一行，调用方要重复判断两个字段。
    return {"disabled": disabled, "mode_disabled": mode_disabled, "context_disabled": context_disabled, "disabled_errors": disabled_errors}  # 新增代码+ClaudeCodeLifecycleParity：返回稳定禁用状态对象；如果没有这一行，tools/list 分支拿不到判断结果。
# 新增代码+ClaudeCodeLifecycleParity：函数段结束，_computer_use_tools_list_disabled_state 到此结束；如果没有这个边界说明，用户不容易看出 disabled 判断范围。


def handle_json_rpc_message(message: dict[str, Any], context: ComputerUseMcpV2Context) -> dict[str, Any] | None:  # 修改代码+ClaudeCodeLifecycleParity：函数段开始，处理一条 JSON-RPC 消息；如果没有这段函数，stdio loop 会混入业务逻辑。
    request_id = message.get("id")  # 修改代码+ClaudeCodeLifecycleParity：读取请求 id；如果没有这行代码，响应无法和请求对应。
    method = str(message.get("method", ""))  # 修改代码+ClaudeCodeLifecycleParity：读取方法名；如果没有这行代码，server 不知道要执行什么。
    params = message.get("params", {}) if isinstance(message.get("params", {}), dict) else {}  # 修改代码+ClaudeCodeLifecycleParity：安全读取参数；如果没有这行代码，坏 params 会崩溃。
    if request_id is None and method.startswith("notifications/"):  # 修改代码+ClaudeCodeLifecycleParity：识别无需响应的通知；如果没有这行代码，initialized 通知会被错误响应。
        return None  # 修改代码+ClaudeCodeLifecycleParity：通知不返回响应；如果没有这行代码，MCP 协议会收到多余消息。
    if method == "initialize":  # 修改代码+ClaudeCodeLifecycleParity：处理初始化；如果没有这行代码，client 无法完成握手。
        return _response(request_id, {"protocolVersion": params.get("protocolVersion", "2025-11-25"), "capabilities": {"tools": {}}, "serverInfo": {"name": COMPUTER_USE_MCP_SERVER_NAME, "version": "0.2.0"}})  # 修改代码+ClaudeCodeLifecycleParity：返回 server 能力；如果没有这行代码，client 不知道支持 tools。
    if method == "tools/list":  # 修改代码+ClaudeCodeLifecycleParity：处理工具列表；如果没有这行代码，模型无法发现工具。
        disabled_state = _computer_use_tools_list_disabled_state(context)  # 新增代码+ClaudeCodeLifecycleParity：先判断 Computer Use 是否被禁用；如果没有这一行，禁用状态下仍会加载 inventory 并暴露工具。
        if bool(disabled_state.get("disabled", False)):  # 新增代码+ClaudeCodeLifecycleParity：命中任一禁用状态时走空工具列表；如果没有这一行，adapter.isDisabled 语义不会生效。
            _record_tools_list_inventory_trace(context, {"status": "disabled", **disabled_state})  # 新增代码+ClaudeCodeLifecycleParity：记录禁用原因 trace；如果没有这一行，工具为空时无法审计原因。
            return _response(request_id, {"tools": []})  # 新增代码+ClaudeCodeLifecycleParity：返回 ClaudeCode-style 空工具列表；如果没有这一行，禁用状态仍会暴露 computer use 工具。
        try:  # 修改代码+ClaudeCodeLifecycleParity：保护动态 inventory 读取；如果没有这行代码，测试注入或真实枚举异常会让 tools/list 崩溃。
            inventory_result = _load_windows_app_inventory_hint()  # 修改代码+ClaudeCodeLifecycleParity：读取最多等待 1 秒的安全应用候选提示；如果没有这行代码，request_access.description 不会动态包含 Windows app inventory。
        except Exception as error:  # 修改代码+ClaudeCodeLifecycleParity：兜底捕获 helper 级异常；如果没有这行代码，patch 或未知错误可能破坏工具发现。
            inventory_result = {"hint": "", "debug": {"status": "error", "error": str(error)}}  # 修改代码+ClaudeCodeLifecycleParity：构造静态 schema 回退结果；如果没有这行代码，异常路径没有可返回对象。
        _record_tools_list_inventory_trace(context, dict(inventory_result.get("debug", {})))  # 修改代码+ClaudeCodeLifecycleParity：记录 ok/timeout/error 状态；如果没有这行代码，动态注入失败没有 debug trace。
        return _response(request_id, {"tools": computer_use_mcp_tools(str(inventory_result.get("hint", "") or ""))})  # 修改代码+ClaudeCodeLifecycleParity：返回带可选 app inventory 描述的 v2 工具面；如果没有这行代码，旧工具面会继续暴露且 request_access 缺动态提示。
    if method == "tools/call":  # 修改代码+ClaudeCodeLifecycleParity：处理工具调用；如果没有这行代码，工具只能列出不能执行。
        tool_name = str(params.get("name", ""))  # 修改代码+ClaudeCodeLifecycleParity：读取工具名；如果没有这行代码，runtime 不知道目标工具。
        arguments = params.get("arguments", {}) if isinstance(params.get("arguments", {}), dict) else {}  # 修改代码+ClaudeCodeLifecycleParity：读取参数对象；如果没有这行代码，模型参数会丢失。
        result = dispatch_computer_use_mcp_v2_tool(tool_name, arguments, context)  # 修改代码+ClaudeCodeLifecycleParity：先拿到工具原始结果再补充通道标记；如果没有这行代码，server 无法执行真实工具。
        result["execution_channel"] = "standalone_stdio_diagnostic"  # 修改代码+ClaudeCodeLifecycleParity：声明独立 server 的 tools/call 只作为诊断通道；如果没有这行代码，排查会误以为 stdio callTool 是生产主路径。
        return _response(request_id, mcp_content_from_result(result))  # 修改代码+ClaudeCodeLifecycleParity：把带诊断标记的结果包装成标准 MCP content；如果没有这行代码，client 拿不到带通道信息的响应。
    return _error(request_id, -32601, f"unknown method: {method}")  # 修改代码+ClaudeCodeLifecycleParity：返回未知方法错误；如果没有这行代码，client 会等待超时。
# 修改代码+ClaudeCodeLifecycleParity：函数段结束，handle_json_rpc_message 到此结束；如果没有这个边界说明，用户不容易看出 JSON-RPC 分发范围。


def run_stdio_loop(input_stream: TextIO, output_stream: TextIO, context: ComputerUseMcpV2Context | None = None) -> None:  # 修改代码+ClaudeCodeLifecycleParity：函数段开始，运行 stdio 主循环；如果没有这段函数，server 无法作为 MCP 子进程。
    runtime_context = context or ComputerUseMcpV2Context(host=WindowsHostAdapter())  # 修改代码+ClaudeCodeLifecycleParity：创建默认 v2 上下文；如果没有这行代码，独立 server 没有 host 和状态。
    for raw_line in input_stream:  # 修改代码+ClaudeCodeLifecycleParity：逐行读取 JSON-RPC；如果没有这行代码，server 收不到请求。
        line = raw_line.strip()  # 修改代码+ClaudeCodeLifecycleParity：清理空白和换行；如果没有这行代码，空白会干扰 JSON 解析。
        if not line:  # 修改代码+ClaudeCodeLifecycleParity：跳过空行；如果没有这行代码，空行会触发解析错误。
            continue  # 修改代码+ClaudeCodeLifecycleParity：等待下一条消息；如果没有这行代码，空行会中断服务。
        try:  # 修改代码+ClaudeCodeLifecycleParity：保护单条消息处理；如果没有这行代码，坏消息会杀死 server。
            response = handle_json_rpc_message(json.loads(line), runtime_context)  # 修改代码+ClaudeCodeLifecycleParity：解析并分发消息；如果没有这行代码，server 不会响应。
        except Exception as error:  # 修改代码+ClaudeCodeLifecycleParity：捕获处理异常；如果没有这行代码，错误会冒泡导致进程退出。
            response = _error(None, -32000, str(error))  # 修改代码+ClaudeCodeLifecycleParity：把异常转成 JSON-RPC 错误；如果没有这行代码，client 只会超时。
        if response is None:  # 修改代码+ClaudeCodeLifecycleParity：通知没有响应；如果没有这行代码，None 会被写成 JSON 污染协议。
            continue  # 修改代码+ClaudeCodeLifecycleParity：继续等待下一条消息；如果没有这行代码，通知后会输出多余内容。
        output_stream.write(json.dumps(response, ensure_ascii=False) + "\n")  # 修改代码+ClaudeCodeLifecycleParity：写出单行 JSON；如果没有这行代码，client 收不到响应。
        output_stream.flush()  # 修改代码+ClaudeCodeLifecycleParity：立即刷新输出；如果没有这行代码，client 可能等待超时。
# 修改代码+ClaudeCodeLifecycleParity：函数段结束，run_stdio_loop 到此结束；如果没有这个边界说明，用户不容易看出 stdio 循环范围。


def run_selftest() -> dict[str, Any]:  # 修改代码+ClaudeCodeLifecycleParity：函数段开始，运行 v2 server 自检；如果没有这段函数，自动化验收无法快速确认工具面。
    tools = computer_use_mcp_tools()  # 修改代码+ClaudeCodeLifecycleParity：读取 v2 工具清单；如果没有这行代码，自检没有输入。
    tool_names = [str(tool.get("name", "")) for tool in tools]  # 修改代码+ClaudeCodeLifecycleParity：提取工具名；如果没有这行代码，自检无法报告工具面。
    return {"marker": COMPUTER_USE_MCP_READY_MARKER, "server": COMPUTER_USE_MCP_SERVER_NAME, "tool_count": len(tool_names), "tool_names": tool_names, "no_shell_surface": assert_no_shell_surface(tools), "passed": bool(tool_names and assert_no_shell_surface(tools))}  # 修改代码+ClaudeCodeLifecycleParity：返回完整自检报告；如果没有这行代码，验收无法判断通过。
# 修改代码+ClaudeCodeLifecycleParity：函数段结束，run_selftest 到此结束；如果没有这个边界说明，用户不容易看出自检范围。


def main(argv: list[str] | None = None) -> int:  # 修改代码+ClaudeCodeLifecycleParity：函数段开始，命令行入口；如果没有这段函数，server 文件不能直接运行。
    parser = argparse.ArgumentParser(description="OpenHarness Computer Use MCP v2 server")  # 修改代码+ClaudeCodeLifecycleParity：创建参数解析器；如果没有这行代码，--selftest 无法识别。
    parser.add_argument("--selftest", action="store_true", help="run v2 schema selftest")  # 修改代码+ClaudeCodeLifecycleParity：注册自检开关；如果没有这行代码，自动化验证不能快速退出。
    args = parser.parse_args(argv)  # 修改代码+ClaudeCodeLifecycleParity：解析命令行参数；如果没有这行代码，main 不知道运行模式。
    if args.selftest:  # 修改代码+ClaudeCodeLifecycleParity：判断是否执行自检；如果没有这行代码，selftest 会进入 stdio 阻塞。
        report = run_selftest()  # 修改代码+ClaudeCodeLifecycleParity：运行自检；如果没有这行代码，命令没有报告。
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 修改代码+ClaudeCodeLifecycleParity：打印 JSON 报告；如果没有这行代码，自动化无法读取详情。
        print(COMPUTER_USE_MCP_READY_MARKER)  # 修改代码+ClaudeCodeLifecycleParity：打印稳定 marker；如果没有这行代码，验收脚本缺少简单匹配点。
        return 0 if bool(report.get("passed")) else 1  # 修改代码+ClaudeCodeLifecycleParity：用退出码表达自检结果；如果没有这行代码，失败也可能返回成功。
    run_stdio_loop(sys.stdin, sys.stdout)  # 修改代码+ClaudeCodeLifecycleParity：进入 stdio server；如果没有这行代码，MCP 子进程会立刻退出。
    return 0  # 修改代码+ClaudeCodeLifecycleParity：正常结束返回成功；如果没有这行代码，退出码不稳定。
# 修改代码+ClaudeCodeLifecycleParity：函数段结束，main 到此结束；如果没有这个边界说明，用户不容易看出 CLI 范围。


if __name__ == "__main__":  # 修改代码+ClaudeCodeLifecycleParity：允许直接运行本文件；如果没有这行代码，python mcpServer.py 不会启动。
    raise SystemExit(main())  # 修改代码+ClaudeCodeLifecycleParity：用 main 退出码结束进程；如果没有这行代码，CLI 退出状态不可控。
