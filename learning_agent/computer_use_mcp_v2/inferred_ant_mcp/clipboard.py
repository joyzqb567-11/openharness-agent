"""Computer Use MCP v2 剪贴板工具。"""  # 新增代码+ComputerUseMcpV2：说明本文件管理受控剪贴板；如果没有这行代码，剪贴板读写会混入 runtime。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型引用可能提前求值。

from .result_blocks import success_result  # 新增代码+ComputerUseMcpV2：导入统一成功结果；如果没有这行代码，剪贴板工具会手写不同结果格式。
from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入上下文；如果没有这行代码，剪贴板工具拿不到会话状态。


def read_clipboard(context: ComputerUseMcpV2Context) -> dict[str, object]:  # 新增代码+ComputerUseMcpV2：函数段开始，读取受控剪贴板；如果没有这段函数，read_clipboard 无法执行。
    return success_result("read_clipboard", {"text": context.clipboard_text, "text_length": len(context.clipboard_text), "backend": "computer_use_mcp_v2_context"})  # 新增代码+ComputerUseMcpV2：返回剪贴板文本和长度；如果没有这行代码，模型无法确认读取结果。
# 新增代码+ComputerUseMcpV2：函数段结束，read_clipboard 到此结束；如果没有这个边界说明，用户不容易看出读取范围。


def write_clipboard(context: ComputerUseMcpV2Context, text: str) -> dict[str, object]:  # 新增代码+ComputerUseMcpV2：函数段开始，写入受控剪贴板；如果没有这段函数，write_clipboard 无法执行。
    context.clipboard_text = str(text)  # 新增代码+ComputerUseMcpV2：保存文本到上下文；如果没有这行代码，后续 read_clipboard 读不到本次写入。
    return success_result("write_clipboard", {"text_length": len(context.clipboard_text), "backend": "computer_use_mcp_v2_context"})  # 新增代码+ComputerUseMcpV2：返回写入摘要而不强制展开长文本；如果没有这行代码，模型无法确认写入状态。
# 新增代码+ComputerUseMcpV2：函数段结束，write_clipboard 到此结束；如果没有这个边界说明，用户不容易看出写入范围。

