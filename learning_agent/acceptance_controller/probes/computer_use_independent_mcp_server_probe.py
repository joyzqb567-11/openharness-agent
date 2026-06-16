"""独立 computer-use MCP server 自检探针。"""  # 新增代码+ComputerUseMCPProbe：说明本文件只负责运行安全自检；如果没有这一行，用户会误以为它会操作桌面。
from __future__ import annotations  # 新增代码+ComputerUseMCPProbe：延迟类型解析保持脚本启动稳定；如果没有这一行，旧运行方式可能受类型注解影响。

from pathlib import Path  # 新增代码+ComputerUseMCPProbe：导入 Path 用来定位项目根目录；如果没有这一行，探针容易在不同 cwd 下找错 server。
import subprocess  # 新增代码+ComputerUseMCPProbe：导入 subprocess 用来启动独立 MCP server 自检；如果没有这一行，探针无法验证真实脚本入口。
import sys  # 新增代码+ComputerUseMCPProbe：导入 sys 用当前 Python 解释器启动子进程；如果没有这一行，探针可能调用到错误 Python。

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # 新增代码+ComputerUseMCPProbe：计算 OpenHarness 项目根目录；如果没有这一行，后续路径都无法稳定拼接。
SERVER_PATH = PROJECT_ROOT / "learning_agent" / "mcp" / "servers" / "computer_use_server.py"  # 新增代码+ComputerUseMCPProbe：定位独立 computer-use MCP server；如果没有这一行，探针不知道要验证哪个入口。


# 新增代码+ComputerUseMCPProbe：函数段开始，main 运行 server 自检并透传输出；如果没有这段函数，可见终端场景没有稳定可复用的探针入口。
def main() -> int:  # 新增代码+ComputerUseMCPProbe：声明命令行入口；如果没有这一行，脚本只能在 import 时执行，测试不容易控制。
    completed = subprocess.run([sys.executable, str(SERVER_PATH), "--selftest"], cwd=str(PROJECT_ROOT), text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=20, check=False)  # 新增代码+ComputerUseMCPProbe：运行独立 server 自检；如果没有这一行，探针无法证明 server 可启动且能输出 ready marker。
    if completed.stdout:  # 新增代码+ComputerUseMCPProbe：检查 stdout 是否有内容；如果没有这一行，空输出和有输出会被同样处理，不利于排查。
        sys.stdout.write(completed.stdout)  # 新增代码+ComputerUseMCPProbe：透传自检 stdout 给验收器；如果没有这一行，场景看不到 COMPUTER_USE_MCP_V2_READY。
    if completed.stderr:  # 新增代码+ComputerUseMCPProbe：检查 stderr 是否有内容；如果没有这一行，失败原因可能被吞掉。
        sys.stderr.write(completed.stderr)  # 新增代码+ComputerUseMCPProbe：透传错误输出；如果没有这一行，probe 失败时用户不知道原因。
    return int(completed.returncode)  # 新增代码+ComputerUseMCPProbe：用 server 自检退出码作为 probe 退出码；如果没有这一行，失败自检也可能被当成成功。
# 新增代码+ComputerUseMCPProbe：函数段结束，main 到此结束；如果没有这个边界说明，用户不容易看出探针只做自检。


if __name__ == "__main__":  # 新增代码+ComputerUseMCPProbe：允许直接运行探针文件；如果没有这一行，真实终端场景无法通过 python 路径启动。
    raise SystemExit(main())  # 新增代码+ComputerUseMCPProbe：把 main 的退出码交给系统；如果没有这一行，失败状态不会传给测试和验收器。
