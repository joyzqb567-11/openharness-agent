"""独立 computer-use MCP stdio server 的 v2 兼容入口。"""  # 修改代码+ComputerUseMcpV2：说明本文件只是保留旧路径的 v2 转发入口；如果没有这一行，读者会误以为这里仍然维护旧 server 主逻辑。
from __future__ import annotations  # 修改代码+ComputerUseMcpV2：延迟解析类型注解以兼容脚本启动；如果没有这一行，部分类型注解在导入阶段可能提前求值失败。

from pathlib import Path  # 修改代码+ComputerUseMcpV2：导入 Path 用来定位项目根目录；如果没有这一行，直接运行本文件时可能找不到 learning_agent 包。
import sys  # 修改代码+ComputerUseMcpV2：导入 sys 用来修正导入路径和传递 argv；如果没有这一行，stdio server 无法稳定作为脚本入口运行。
from typing import Any, TextIO  # 修改代码+ComputerUseMcpV2：导入公共类型给 wrapper 函数标注边界；如果没有这一行，调用方不容易看懂输入输出形态。

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # 修改代码+ComputerUseMcpV2：计算 OpenHarness 项目根目录；如果没有这一行，python learning_agent\mcp\servers\computer_use_server.py 会因包路径不同而导入失败。
if str(PROJECT_ROOT) not in sys.path:  # 修改代码+ComputerUseMcpV2：检查项目根目录是否已经在导入路径中；如果没有这一行，重复插入会污染 sys.path 顺序。
    sys.path.insert(0, str(PROJECT_ROOT))  # 修改代码+ComputerUseMcpV2：把项目根目录放到导入路径最前面；如果没有这一行，独立 stdio 启动时可能找不到 v2 包。


# 修改代码+ComputerUseMcpV2：函数段开始，_configure_stdio_encoding 固定 Windows stdio 为 UTF-8；如果没有这段函数，registry 读取中文 JSON-RPC 响应时可能 UnicodeDecodeError。
def _configure_stdio_encoding() -> None:  # 修改代码+ComputerUseMcpV2：声明 stdio 编码修复入口；如果没有这一行，main 和导入阶段无法复用同一设置。
    for stream in (sys.stdin, sys.stdout):  # 修改代码+ComputerUseMcpV2：同时处理输入和输出流；如果没有这一行，stdin/stdout 编码可能一边修了一边没修。
        reconfigure = getattr(stream, "reconfigure", None)  # 修改代码+ComputerUseMcpV2：读取 Python 文本流的 reconfigure 方法；如果没有这一行，旧式测试流可能因缺属性崩溃。
        if callable(reconfigure):  # 修改代码+ComputerUseMcpV2：只在当前流支持重配置时执行；如果没有这一行，fake stream 会被错误调用。
            reconfigure(encoding="utf-8")  # 修改代码+ComputerUseMcpV2：把 stdio 编码固定为 UTF-8；如果没有这一行，Windows 默认代码页会污染 MCP 协议输出。
# 修改代码+ComputerUseMcpV2：函数段结束，_configure_stdio_encoding 到此结束；如果没有这个边界说明，用户不容易看出编码修复范围。


_configure_stdio_encoding()  # 修改代码+ComputerUseMcpV2：导入阶段立即固定 stdio 编码；如果没有这一行，tools/list 的中文 schema 可能先用本地编码输出。

from learning_agent.computer_use_mcp_v2.claudecode_bridge.mcpServer import handle_json_rpc_message as _v2_handle_json_rpc_message  # 修改代码+ComputerUseMcpV2：复用 v2 JSON-RPC 分发函数；如果没有这一行，旧 server 会继续走旧 executor。
from learning_agent.computer_use_mcp_v2.claudecode_bridge.mcpServer import main as _v2_main  # 修改代码+ComputerUseMcpV2：复用 v2 CLI 入口；如果没有这一行，--selftest 和 stdio 入口会出现两套实现。
from learning_agent.computer_use_mcp_v2.claudecode_bridge.mcpServer import run_selftest as _v2_run_selftest  # 修改代码+ComputerUseMcpV2：复用 v2 自检；如果没有这一行，server 自检可能仍报告旧工具面。
from learning_agent.computer_use_mcp_v2.claudecode_bridge.mcpServer import run_stdio_loop as _v2_run_stdio_loop  # 修改代码+ComputerUseMcpV2：复用 v2 stdio 主循环；如果没有这一行，tools/call 仍可能触达旧实现。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.types import ComputerUseMcpV2Context  # 修改代码+ComputerUseMcpV2：导入 v2 上下文类型；如果没有这一行，公开 wrapper 函数的 context 边界不清楚。


# 修改代码+ComputerUseMcpV2：函数段开始，handle_json_rpc_message 保留旧模块公开函数名并转发到 v2；如果没有这段函数，既有测试和 registry 入口会找不到原函数。
def handle_json_rpc_message(message: dict[str, Any], context: ComputerUseMcpV2Context) -> dict[str, Any] | None:  # 修改代码+ComputerUseMcpV2：声明 JSON-RPC 单消息处理入口；如果没有这一行，外部仍需直接依赖 v2 内部路径。
    return _v2_handle_json_rpc_message(message, context)  # 修改代码+ComputerUseMcpV2：把请求交给 v2 server 处理；如果没有这一行，旧路径无法获得 v2 工具列表和执行结果。
# 修改代码+ComputerUseMcpV2：函数段结束，handle_json_rpc_message 到此结束；如果没有这个边界说明，用户不容易看出旧入口只是转发。


# 修改代码+ComputerUseMcpV2：函数段开始，run_stdio_loop 保留旧模块 stdio 入口并转发到 v2；如果没有这段函数，mcp_servers.json 指向旧路径时无法启动 v2。
def run_stdio_loop(input_stream: TextIO, output_stream: TextIO, context: ComputerUseMcpV2Context | None = None) -> None:  # 修改代码+ComputerUseMcpV2：声明 stdio 主循环兼容入口；如果没有这一行，测试和实际 MCP client 无法用旧路径启动。
    _v2_run_stdio_loop(input_stream, output_stream, context)  # 修改代码+ComputerUseMcpV2：执行 v2 stdio 主循环；如果没有这一行，server 只会有函数壳而不处理消息。
# 修改代码+ComputerUseMcpV2：函数段结束，run_stdio_loop 到此结束；如果没有这个边界说明，用户不容易看出 stdio 逻辑来自 v2。


# 修改代码+ComputerUseMcpV2：函数段开始，run_selftest 保留旧模块自检入口并转发到 v2；如果没有这段函数，验收脚本无法确认 v2 工具面。
def run_selftest() -> dict[str, Any]:  # 修改代码+ComputerUseMcpV2：声明自检入口；如果没有这一行，python server.py --selftest 之外的代码无法直接调用。
    return _v2_run_selftest()  # 修改代码+ComputerUseMcpV2：返回 v2 自检报告；如果没有这一行，自检结果会与真实 server 工具面分裂。
# 修改代码+ComputerUseMcpV2：函数段结束，run_selftest 到此结束；如果没有这个边界说明，用户不容易看出自检转发范围。


# 修改代码+ComputerUseMcpV2：函数段开始，main 保留旧文件命令行入口并转发到 v2；如果没有这段函数，旧启动命令会失效。
def main(argv: list[str] | None = None) -> int:  # 修改代码+ComputerUseMcpV2：声明 CLI 入口；如果没有这一行，__main__ 无法委托到 v2。
    return _v2_main(argv)  # 修改代码+ComputerUseMcpV2：执行 v2 命令行逻辑；如果没有这一行，server 不会响应 --selftest 或 stdio。
# 修改代码+ComputerUseMcpV2：函数段结束，main 到此结束；如果没有这个边界说明，用户不容易看出命令行逻辑来自 v2。


if __name__ == "__main__":  # 修改代码+ComputerUseMcpV2：允许直接运行旧 server 路径；如果没有这一行，mcp_servers.json 的脚本入口不会启动服务。
    raise SystemExit(main())  # 修改代码+ComputerUseMcpV2：用 v2 main 的退出码结束进程；如果没有这一行，失败自检也可能被当成成功。
