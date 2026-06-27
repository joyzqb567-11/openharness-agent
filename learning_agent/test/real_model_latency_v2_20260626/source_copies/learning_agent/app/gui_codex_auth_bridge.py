"""Official Codex CLI login bridge for OpenHarness Desktop."""  # 新增代码+CodexLoginBridge：说明本模块只桥接官方 Codex CLI 登录；如果没有这行，后续维护者可能误把它当 token 读取模块。

from __future__ import annotations  # 新增代码+CodexLoginBridge：启用现代类型注解语法；如果没有这行，list[str] 和 | None 在旧解析行为下更脆弱。

import subprocess  # 新增代码+CodexLoginBridge：调用官方 codex CLI；如果没有这行，OpenHarness 无法启动或检查 Codex 登录。
from dataclasses import dataclass  # 新增代码+CodexLoginBridge：定义不可变登录状态对象；如果没有这行，状态只能用松散 dict 表达。
from typing import Callable  # 新增代码+CodexLoginBridge：定义可注入 runner/starter 类型；如果没有这行，测试无法替换真实命令。


CommandRunner = Callable[[list[str], float], tuple[int, str, str]]  # 新增代码+CodexLoginBridge：定义 status 命令 runner 合同；如果没有这行，测试和实现对命令返回形状会分裂。
CommandStarter = Callable[[list[str]], object]  # 新增代码+CodexLoginBridge：定义登录进程 starter 合同；如果没有这行，测试无法安全阻止真实浏览器打开。


@dataclass(frozen=True)  # 新增代码+CodexLoginBridge：生成不可变状态对象；如果没有这行，调用方可能在传递中改坏连接状态。
class CodexAuthStatus:  # 新增代码+CodexLoginBridge：类段开始，描述 Codex CLI 登录状态；如果没有这个类，provider catalog 只能解析不稳定字符串。
    available: bool  # 新增代码+CodexLoginBridge：表示 Codex CLI 是否可执行；如果没有这行，UI 无法区分“未安装”和“未登录”。
    connected: bool  # 新增代码+CodexLoginBridge：表示 ChatGPT/Codex 登录是否有效；如果没有这行，真实模型路径无法判断是否可用。
    message: str  # 新增代码+CodexLoginBridge：保存安全短消息；如果没有这行，用户和测试看不到失败原因。
# 新增代码+CodexLoginBridge：类段结束，CodexAuthStatus 到此结束；如果没有边界说明，初学者不易看出状态字段范围。


def _default_runner(command: list[str], timeout_seconds: float) -> tuple[int, str, str]:  # 新增代码+CodexLoginBridge：函数段开始，执行短生命周期 Codex CLI 命令；如果没有这段，status 无法调用官方 CLI。
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds)  # 新增代码+CodexLoginBridge：运行命令并捕获输出；如果没有这行，status 结果无法被结构化判断。
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()  # 新增代码+CodexLoginBridge：返回退出码和清理后的输出；如果没有这行，调用方要直接依赖 subprocess 对象。
# 新增代码+CodexLoginBridge：函数段结束，_default_runner 到此结束；如果没有边界说明，用户不易看出它只负责同步 status 命令。


def _default_starter(command: list[str]) -> object:  # 新增代码+CodexLoginBridge：函数段开始，启动官方 codex login；如果没有这段，设置页无法打开浏览器登录。
    return subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # 新增代码+CodexLoginBridge：后台启动登录进程并丢弃输出；如果没有这行，GUI bridge 线程可能被登录流程阻塞。
# 新增代码+CodexLoginBridge：函数段结束，_default_starter 到此结束；如果没有边界说明，用户不易看出它只负责启动而不等待。


class CodexAuthBridge:  # 新增代码+CodexLoginBridge：类段开始，封装 Codex CLI 登录命令；如果没有这个类，provider/auth attempt 会散落 subprocess 调用。
    def __init__(self, command: str = "codex", runner: CommandRunner | None = None, starter: CommandStarter | None = None, timeout_seconds: float = 15.0) -> None:  # 新增代码+CodexLoginBridge：初始化函数开始，允许测试注入命令执行器；如果没有这段，测试会依赖真实 Codex CLI。
        self.command = command  # 新增代码+CodexLoginBridge：保存 CLI 命令名；如果没有这行，Windows 或测试无法替换 codex 路径。
        self.runner = runner or _default_runner  # 新增代码+CodexLoginBridge：保存 status 命令执行器；如果没有这行，login_status 无法运行或被测试替换。
        self.starter = starter or _default_starter  # 新增代码+CodexLoginBridge：保存登录启动器；如果没有这行，start_login 无法启动官方登录流程。
        self.timeout_seconds = timeout_seconds  # 新增代码+CodexLoginBridge：保存 status 超时；如果没有这行，Codex CLI 卡住会拖死 GUI bridge。
    # 新增代码+CodexLoginBridge：初始化函数结束，CodexAuthBridge.__init__ 到此结束；如果没有边界说明，用户不易看出依赖注入范围。

    def login_status(self) -> CodexAuthStatus:  # 新增代码+CodexLoginBridge：函数段开始，查询官方 Codex 登录状态；如果没有这段，provider catalog 不知道是否真实可用。
        try:  # 新增代码+CodexLoginBridge：捕获命令缺失和超时；如果没有这行，CLI 异常会变成 bridge 500。
            code, stdout, stderr = self.runner([self.command, "login", "status"], self.timeout_seconds)  # 新增代码+CodexLoginBridge：调用官方 status 命令；如果没有这行，登录状态无法来自官方边界。
        except FileNotFoundError:  # 新增代码+CodexLoginBridge：处理 Codex CLI 未安装；如果没有这行，用户只会看到 Python 异常。
            return CodexAuthStatus(available=False, connected=False, message="codex_cli_not_found")  # 新增代码+CodexLoginBridge：返回稳定缺 CLI 状态；如果没有这行，前端无法显示安装提示。
        except subprocess.TimeoutExpired:  # 新增代码+CodexLoginBridge：处理 status 命令超时；如果没有这行，GUI 会卡住或返回泛化失败。
            return CodexAuthStatus(available=True, connected=False, message="codex_login_status_timeout")  # 新增代码+CodexLoginBridge：返回稳定超时状态；如果没有这行，用户无法判断是卡住而不是未安装。
        message = stdout or stderr  # 新增代码+CodexLoginBridge：优先使用 stdout，失败时使用 stderr；如果没有这行，状态文案会丢失。
        return CodexAuthStatus(available=True, connected=(code == 0), message=message)  # 新增代码+CodexLoginBridge：根据退出码生成连接状态；如果没有这行，provider catalog 无法判断真实 connected。
    # 新增代码+CodexLoginBridge：函数段结束，login_status 到此结束；如果没有边界说明，用户不易看出它只查官方 status。

    def start_login(self) -> dict[str, object]:  # 新增代码+CodexLoginBridge：函数段开始，启动官方 Codex ChatGPT 登录；如果没有这段，OpenAI browser 方法只能停在 mock。
        try:  # 新增代码+CodexLoginBridge：捕获命令缺失；如果没有这行，未安装 Codex 时会抛到 HTTP 500。
            self.starter([self.command, "login"])  # 新增代码+CodexLoginBridge：启动官方登录流程；如果没有这行，浏览器不会打开 ChatGPT OAuth。
        except FileNotFoundError:  # 新增代码+CodexLoginBridge：处理 Codex CLI 未安装；如果没有这行，前端无法显示可读失败。
            return {"ok": False, "mode": "codex_cli_login", "error_code": "codex_cli_not_found", "message": "Codex CLI was not found."}  # 新增代码+CodexLoginBridge：返回脱敏失败 payload；如果没有这行，失败可能暴露堆栈或无状态。
        return {"ok": True, "mode": "codex_cli_login", "message": "Codex login started."}  # 新增代码+CodexLoginBridge：返回启动成功 payload；如果没有这行，前端无法进入等待授权页。
    # 新增代码+CodexLoginBridge：函数段结束，start_login 到此结束；如果没有边界说明，用户不易看出它不读取 token。
# 新增代码+CodexLoginBridge：类段结束，CodexAuthBridge 到此结束；如果没有边界说明，用户不易看出这个类只是官方 CLI 薄桥。
