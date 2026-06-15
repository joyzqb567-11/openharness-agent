"""Computer Use MCP v2 应用启动工具。"""  # 新增代码+ComputerUseMcpV2：说明本文件管理 open_application；如果没有这行代码，应用启动会和鼠标键盘动作混杂。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型引用可能提前求值。

import subprocess  # 新增代码+ComputerUseMcpV2：导入子进程模块用于打开安全映射应用；如果没有这行代码，open_application 无法启动系统应用。
from typing import Any  # 新增代码+ComputerUseMcpV2：导入通用 JSON 类型；如果没有这行代码，参数边界不清楚。

from .errors import error_result  # 新增代码+ComputerUseMcpV2：导入统一失败结果；如果没有这行代码，启动失败格式会漂移。
from .result_blocks import success_result  # 新增代码+ComputerUseMcpV2：导入统一成功结果；如果没有这行代码，启动成功格式会漂移。
from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入上下文；如果没有这行代码，host 启动能力无法注入。

SAFE_APPLICATION_COMMANDS = {"notepad": ["notepad.exe"], "记事本": ["notepad.exe"], "calculator": ["calc.exe"], "calc": ["calc.exe"], "chrome": ["chrome.exe"], "edge": ["msedge.exe"]}  # 新增代码+ComputerUseMcpV2：集中保存保守应用名映射；如果没有这行代码，模型输入可能被直接当成可执行命令。


def open_application(context: ComputerUseMcpV2Context, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ComputerUseMcpV2：函数段开始，打开本地应用；如果没有这段函数，open_application 工具无法执行。
    app_name = str(arguments.get("app_name", "") or "").strip()  # 新增代码+ComputerUseMcpV2：读取并清理应用名；如果没有这行代码，空白和 None 会进入启动逻辑。
    host_method = getattr(context.host, "open_application", None) if context.host is not None else None  # 新增代码+ComputerUseMcpV2：优先读取注入 host 的启动能力；如果没有这行代码，测试和成熟 Windows host 无法接管。
    if callable(host_method):  # 新增代码+ComputerUseMcpV2：检查 host 是否可启动应用；如果没有这行代码，调用 None 会崩溃。
        payload = dict(host_method(app_name, arguments) or {})  # 修改代码+ComputerUseMcpV2HostAdapter：保存 host 启动结果用于同步来源标记；如果没有这一行，open_application 的旧 adapter 证据无法透到顶层。
        return success_result("open_application", payload, legacy_adapter_used=bool(payload.get("legacy_adapter_used", False)))  # 修改代码+ComputerUseMcpV2HostAdapter：返回 host 启动结果并透出旧 adapter 来源；如果没有这一行，应用启动是否复用旧 launch_app 无法被审计。
    command = SAFE_APPLICATION_COMMANDS.get(app_name.lower())  # 新增代码+ComputerUseMcpV2：只从安全映射中取命令；如果没有这行代码，应用名可能变成任意命令执行。
    if command is None:  # 新增代码+ComputerUseMcpV2：检查是否支持该应用名；如果没有这行代码，未知应用会进入 Popen。
        return error_result("open_application", f"unsupported_application:{app_name}", error_class="unsupported_application")  # 新增代码+ComputerUseMcpV2：返回不支持应用结果；如果没有这行代码，模型不知道要换应用名。
    process = subprocess.Popen(command)  # 新增代码+ComputerUseMcpV2：启动安全映射命令；如果没有这行代码，应用不会真正打开。
    return success_result("open_application", {"app_name": app_name, "pid": process.pid, "command": command[0]})  # 新增代码+ComputerUseMcpV2：返回启动摘要；如果没有这行代码，模型无法知道启动是否发生。
# 新增代码+ComputerUseMcpV2：函数段结束，open_application 到此结束；如果没有这个边界说明，用户不容易看出应用启动范围。
