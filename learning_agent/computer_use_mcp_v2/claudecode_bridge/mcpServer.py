"""Computer Use MCP v2 stdio server 桥接。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode mcpServer.ts；如果没有这行代码，stdio server 入口没有同构文件。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

import argparse  # 新增代码+ComputerUseMcpV2：导入参数解析用于 --selftest；如果没有这行代码，server 无法提供自检入口。
import json  # 新增代码+ComputerUseMcpV2：导入 JSON 用于 JSON-RPC 和 selftest 输出；如果没有这行代码，stdio 协议无法实现。
import sys  # 新增代码+ComputerUseMcpV2：导入 sys 访问 stdin/stdout；如果没有这行代码，server 无法作为 stdio 进程运行。
from typing import Any, TextIO  # 新增代码+ComputerUseMcpV2：导入通用类型和文本流类型；如果没有这行代码，server helper 边界不清楚。

from learning_agent.computer_use_mcp_v2.claudecode_bridge.hostAdapter import WindowsHostAdapter  # 新增代码+ComputerUseMcpV2：导入默认 Windows host；如果没有这行代码，独立 server 没有 host 对象。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import COMPUTER_USE_MCP_READY_MARKER, COMPUTER_USE_MCP_SERVER_NAME, assert_no_shell_surface, computer_use_mcp_tools  # 新增代码+ComputerUseMcpV2：导入 v2 工具面和 marker；如果没有这行代码，server 会回到旧 schema。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.result_blocks import mcp_content_from_result  # 新增代码+ComputerUseMcpV2：导入 MCP 结果包装；如果没有这行代码，tools/call 输出格式不稳定。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import ComputerUseMcpV2Context, dispatch_computer_use_mcp_v2_tool  # 新增代码+ComputerUseMcpV2：导入统一 runtime；如果没有这行代码，server 无法执行工具。


def _response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，生成 JSON-RPC 成功响应；如果没有这段函数，响应结构会重复。
    return {"jsonrpc": "2.0", "id": request_id, "result": result}  # 新增代码+ComputerUseMcpV2：返回标准响应；如果没有这行代码，MCP client 无法匹配结果。
# 新增代码+ComputerUseMcpV2：函数段结束，_response 到此结束；如果没有这个边界说明，用户不容易看出响应构造范围。


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，生成 JSON-RPC 错误响应；如果没有这段函数，错误格式会重复。
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": int(code), "message": str(message)}}  # 新增代码+ComputerUseMcpV2：返回标准错误；如果没有这行代码，client 会难以识别失败。
# 新增代码+ComputerUseMcpV2：函数段结束，_error 到此结束；如果没有这个边界说明，用户不容易看出错误构造范围。


def handle_json_rpc_message(message: dict[str, Any], context: ComputerUseMcpV2Context) -> dict[str, Any] | None:  # 新增代码+ComputerUseMcpV2：函数段开始，处理一条 JSON-RPC 消息；如果没有这段函数，stdio loop 会混入业务逻辑。
    request_id = message.get("id")  # 新增代码+ComputerUseMcpV2：读取请求 id；如果没有这行代码，响应无法和请求对应。
    method = str(message.get("method", ""))  # 新增代码+ComputerUseMcpV2：读取方法名；如果没有这行代码，server 不知道要执行什么。
    params = message.get("params", {}) if isinstance(message.get("params", {}), dict) else {}  # 新增代码+ComputerUseMcpV2：安全读取参数；如果没有这行代码，坏 params 会崩溃。
    if request_id is None and method.startswith("notifications/"):  # 新增代码+ComputerUseMcpV2：识别无需响应的通知；如果没有这行代码，initialized 通知会被错误响应。
        return None  # 新增代码+ComputerUseMcpV2：通知不返回响应；如果没有这行代码，MCP 协议会收到多余消息。
    if method == "initialize":  # 新增代码+ComputerUseMcpV2：处理初始化；如果没有这行代码，client 无法完成握手。
        return _response(request_id, {"protocolVersion": params.get("protocolVersion", "2025-11-25"), "capabilities": {"tools": {}}, "serverInfo": {"name": COMPUTER_USE_MCP_SERVER_NAME, "version": "0.2.0"}})  # 新增代码+ComputerUseMcpV2：返回 server 能力；如果没有这行代码，client 不知道支持 tools。
    if method == "tools/list":  # 新增代码+ComputerUseMcpV2：处理工具列表；如果没有这行代码，模型无法发现工具。
        return _response(request_id, {"tools": computer_use_mcp_tools()})  # 新增代码+ComputerUseMcpV2：返回 v2 工具面；如果没有这行代码，旧工具面会继续暴露。
    if method == "tools/call":  # 新增代码+ComputerUseMcpV2：处理工具调用；如果没有这行代码，工具只能列出不能执行。
        tool_name = str(params.get("name", ""))  # 新增代码+ComputerUseMcpV2：读取工具名；如果没有这行代码，runtime 不知道目标工具。
        arguments = params.get("arguments", {}) if isinstance(params.get("arguments", {}), dict) else {}  # 新增代码+ComputerUseMcpV2：读取参数对象；如果没有这行代码，模型参数会丢失。
        result = dispatch_computer_use_mcp_v2_tool(tool_name, arguments, context)  # 修改代码+ComputerUseMcpV2PrimaryPath：先拿到工具原始结果再补充通道标记；如果没有这行代码，下面无法区分独立 stdio 诊断调用和 agent-side 主路径调用。
        result["execution_channel"] = "standalone_stdio_diagnostic"  # 修改代码+ComputerUseMcpV2PrimaryPath：声明独立 server 的 tools/call 只作为诊断通道；如果没有这行代码，后续排查会误以为 stdio callTool 是生产主执行路径。
        return _response(request_id, mcp_content_from_result(result))  # 修改代码+ComputerUseMcpV2PrimaryPath：把带诊断标记的结果包装成标准 MCP content；如果没有这行代码，client 拿不到带通道信息的响应。
    return _error(request_id, -32601, f"unknown method: {method}")  # 新增代码+ComputerUseMcpV2：返回未知方法错误；如果没有这行代码，client 会等待超时。
# 新增代码+ComputerUseMcpV2：函数段结束，handle_json_rpc_message 到此结束；如果没有这个边界说明，用户不容易看出 JSON-RPC 分发范围。


def run_stdio_loop(input_stream: TextIO, output_stream: TextIO, context: ComputerUseMcpV2Context | None = None) -> None:  # 新增代码+ComputerUseMcpV2：函数段开始，运行 stdio 主循环；如果没有这段函数，server 无法作为 MCP 子进程。
    runtime_context = context or ComputerUseMcpV2Context(host=WindowsHostAdapter())  # 新增代码+ComputerUseMcpV2：创建默认 v2 上下文；如果没有这行代码，独立 server 没有 host 和状态。
    for raw_line in input_stream:  # 新增代码+ComputerUseMcpV2：逐行读取 JSON-RPC；如果没有这行代码，server 收不到请求。
        line = raw_line.strip()  # 新增代码+ComputerUseMcpV2：清理空白和换行；如果没有这行代码，空白会干扰 JSON 解析。
        if not line:  # 新增代码+ComputerUseMcpV2：跳过空行；如果没有这行代码，空行会触发解析错误。
            continue  # 新增代码+ComputerUseMcpV2：等待下一条消息；如果没有这行代码，空行会中断服务。
        try:  # 新增代码+ComputerUseMcpV2：保护单条消息处理；如果没有这行代码，坏消息会杀死 server。
            response = handle_json_rpc_message(json.loads(line), runtime_context)  # 新增代码+ComputerUseMcpV2：解析并分发消息；如果没有这行代码，server 不会响应。
        except Exception as error:  # 新增代码+ComputerUseMcpV2：捕获处理异常；如果没有这行代码，错误会冒泡导致进程退出。
            response = _error(None, -32000, str(error))  # 新增代码+ComputerUseMcpV2：把异常转成 JSON-RPC 错误；如果没有这行代码，client 只会超时。
        if response is None:  # 新增代码+ComputerUseMcpV2：通知没有响应；如果没有这行代码，None 会被写成 JSON 污染协议。
            continue  # 新增代码+ComputerUseMcpV2：继续等待下一条消息；如果没有这行代码，通知后会输出多余内容。
        output_stream.write(json.dumps(response, ensure_ascii=False) + "\n")  # 新增代码+ComputerUseMcpV2：写出单行 JSON；如果没有这行代码，client 收不到响应。
        output_stream.flush()  # 新增代码+ComputerUseMcpV2：立即刷新输出；如果没有这行代码，client 可能等待超时。
# 新增代码+ComputerUseMcpV2：函数段结束，run_stdio_loop 到此结束；如果没有这个边界说明，用户不容易看出 stdio 循环范围。


def run_selftest() -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，运行 v2 server 自检；如果没有这段函数，自动化验收无法快速确认工具面。
    tools = computer_use_mcp_tools()  # 新增代码+ComputerUseMcpV2：读取 v2 工具清单；如果没有这行代码，自检没有输入。
    tool_names = [str(tool.get("name", "")) for tool in tools]  # 新增代码+ComputerUseMcpV2：提取工具名；如果没有这行代码，自检无法报告工具面。
    return {"marker": COMPUTER_USE_MCP_READY_MARKER, "server": COMPUTER_USE_MCP_SERVER_NAME, "tool_count": len(tool_names), "tool_names": tool_names, "no_shell_surface": assert_no_shell_surface(tools), "passed": bool(tool_names and assert_no_shell_surface(tools))}  # 新增代码+ComputerUseMcpV2：返回完整自检报告；如果没有这行代码，验收无法判断通过。
# 新增代码+ComputerUseMcpV2：函数段结束，run_selftest 到此结束；如果没有这个边界说明，用户不容易看出自检范围。


def main(argv: list[str] | None = None) -> int:  # 新增代码+ComputerUseMcpV2：函数段开始，命令行入口；如果没有这段函数，server 文件不能直接运行。
    parser = argparse.ArgumentParser(description="OpenHarness Computer Use MCP v2 server")  # 新增代码+ComputerUseMcpV2：创建参数解析器；如果没有这行代码，--selftest 无法识别。
    parser.add_argument("--selftest", action="store_true", help="run v2 schema selftest")  # 新增代码+ComputerUseMcpV2：注册自检开关；如果没有这行代码，自动化验证不能快速退出。
    args = parser.parse_args(argv)  # 新增代码+ComputerUseMcpV2：解析命令行参数；如果没有这行代码，main 不知道运行模式。
    if args.selftest:  # 新增代码+ComputerUseMcpV2：判断是否执行自检；如果没有这行代码，selftest 会进入 stdio 阻塞。
        report = run_selftest()  # 新增代码+ComputerUseMcpV2：运行自检；如果没有这行代码，命令没有报告。
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))  # 新增代码+ComputerUseMcpV2：打印 JSON 报告；如果没有这行代码，自动化无法读取详情。
        print(COMPUTER_USE_MCP_READY_MARKER)  # 新增代码+ComputerUseMcpV2：打印稳定 marker；如果没有这行代码，验收脚本缺少简单匹配点。
        return 0 if bool(report.get("passed")) else 1  # 新增代码+ComputerUseMcpV2：用退出码表达自检结果；如果没有这行代码，失败也可能返回成功。
    run_stdio_loop(sys.stdin, sys.stdout)  # 新增代码+ComputerUseMcpV2：进入 stdio server；如果没有这行代码，MCP 子进程会立刻退出。
    return 0  # 新增代码+ComputerUseMcpV2：正常结束返回成功；如果没有这行代码，退出码不稳定。
# 新增代码+ComputerUseMcpV2：函数段结束，main 到此结束；如果没有这个边界说明，用户不容易看出 CLI 范围。


if __name__ == "__main__":  # 新增代码+ComputerUseMcpV2：允许直接运行本文件；如果没有这行代码，python mcpServer.py 不会启动。
    raise SystemExit(main())  # 新增代码+ComputerUseMcpV2：用 main 退出码结束进程；如果没有这行代码，CLI 退出状态不可控。
