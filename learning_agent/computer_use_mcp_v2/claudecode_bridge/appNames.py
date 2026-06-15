"""Computer Use MCP v2 应用名桥接。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode appNames.ts；如果没有这行代码，应用名映射职责没有固定位置。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，导入时类型求值可能出错。

WINDOWS_APP_NAME_ALIASES = {"notepad": "notepad", "记事本": "notepad", "calculator": "calculator", "chrome": "chrome", "edge": "edge"}  # 新增代码+ComputerUseMcpV2：保存保守应用别名；如果没有这行代码，open_application 无法统一用户自然语言名称。

