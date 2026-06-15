"""Computer Use MCP v2 安全哨兵应用清单。"""  # 新增代码+ComputerUseMcpV2：说明本文件保存不可随意控制的高风险目标提示；如果没有这行代码，应用边界会分散。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，导入阶段可能提前求值类型。

SENTINEL_APP_NAMES = {"terminal", "powershell", "cmd", "windows security", "credential manager"}  # 新增代码+ComputerUseMcpV2：集中保存高风险应用名称片段；如果没有这行代码，安全判断没有统一名单。


def is_sentinel_app(app_name: str) -> bool:  # 新增代码+ComputerUseMcpV2：函数段开始，判断应用名是否高风险；如果没有这段函数，调用方会重复写字符串判断。
    lowered = str(app_name or "").strip().lower()  # 新增代码+ComputerUseMcpV2：规范化应用名；如果没有这行代码，大小写和空格会影响判断。
    return any(name in lowered for name in SENTINEL_APP_NAMES)  # 新增代码+ComputerUseMcpV2：返回是否命中哨兵应用；如果没有这行代码，高风险目标可能被误放行。
# 新增代码+ComputerUseMcpV2：函数段结束，is_sentinel_app 到此结束；如果没有这个边界说明，用户不容易看出哨兵应用判断范围。

