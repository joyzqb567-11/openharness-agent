"""Computer Use MCP v2 剪贴板工具。"""  # 新增代码+ComputerUseMcpV2：说明本文件管理受控剪贴板；如果没有这行代码，剪贴板读写会混入 runtime。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型引用可能提前求值。

from typing import Any  # 新增代码+ClipboardSystemBridge：导入通用 JSON 类型；如果没有这行代码，剪贴板返回值类型无法表达 payload 和错误信息。

from .errors import error_result  # 新增代码+ClipboardSystemBridge：导入统一错误结果；如果没有这行代码，未授权或后端失败会返回漂移格式。
from .result_blocks import success_result  # 新增代码+ComputerUseMcpV2：导入统一成功结果；如果没有这行代码，剪贴板工具会手写不同结果格式。
from .types import ComputerUseMcpV2Context  # 新增代码+ComputerUseMcpV2：导入上下文；如果没有这行代码，剪贴板工具拿不到会话状态。


def _clipboard_backend(context: ComputerUseMcpV2Context) -> Any | None:  # 新增代码+ClipboardSystemBridge：函数段开始，读取上下文中的剪贴板后端；如果没有这段函数，读写工具会重复写 getattr 和空值判断。
    return getattr(context, "clipboard_backend", None)  # 新增代码+ClipboardSystemBridge：返回真实或测试剪贴板后端；如果没有这行代码，工具无法区分系统后端和旧内存字段。
# 新增代码+ClipboardSystemBridge：函数段结束，_clipboard_backend 到此结束；如果没有这个边界说明，用户不容易看出后端读取范围。


def _backend_name(backend: Any) -> str:  # 新增代码+ClipboardSystemBridge：函数段开始，读取后端名称；如果没有这段函数，payload 可能因为后端缺字段而崩溃。
    return str(getattr(backend, "backend_name", "unknown_clipboard_backend") or "unknown_clipboard_backend")  # 新增代码+ClipboardSystemBridge：返回稳定后端名称；如果没有这行代码，错误和成功结果缺少来源说明。
# 新增代码+ClipboardSystemBridge：函数段结束，_backend_name 到此结束；如果没有这个边界说明，用户不容易看出名称兜底范围。


def read_clipboard(context: ComputerUseMcpV2Context) -> dict[str, Any]:  # 修改代码+ClipboardSystemBridge：函数段开始，按授权读取系统剪贴板；如果没有这段函数，read_clipboard 无法执行 ClaudeCode-style 系统读取。
    if not context.grant_flags.get("clipboardRead", False):  # 新增代码+ClipboardSystemBridge：检查剪贴板读取授权；如果没有这行代码，未授权模型可能读取用户系统剪贴板。
        return error_result("read_clipboard", "clipboard_read_not_granted", error_class="permission_denied")  # 新增代码+ClipboardSystemBridge：返回权限拒绝错误；如果没有这行代码，调用方无法知道缺少 clipboardRead。
    backend = _clipboard_backend(context)  # 新增代码+ClipboardSystemBridge：读取绑定的剪贴板后端；如果没有这行代码，工具不知道该访问真实后端还是测试后端。
    if backend is None:  # 新增代码+ClipboardSystemBridge：检查后端是否存在；如果没有这行代码，空后端会导致属性错误。
        return error_result("read_clipboard", "clipboard_backend_unavailable", error_class="unavailable")  # 新增代码+ClipboardSystemBridge：返回后端不可用错误；如果没有这行代码，模型无法区分权限问题和运行时缺后端。
    try:  # 新增代码+ClipboardSystemBridge：保护真实系统读取调用；如果没有这行代码，Windows 剪贴板异常会中断整个工具链。
        text = str(backend.read_text())  # 新增代码+ClipboardSystemBridge：从后端读取文本并规范化为字符串；如果没有这行代码，工具无法拿到系统剪贴板内容。
    except Exception as error:  # 新增代码+ClipboardSystemBridge：捕获后端读取异常；如果没有这行代码，剪贴板被占用时会让 agent 主循环崩溃。
        result = error_result("read_clipboard", f"clipboard_read_failed:{error}", error_class="clipboard_backend_error")  # 新增代码+ClipboardSystemBridge：生成后端读取失败结果；如果没有这行代码，调用方看不到失败原因。
        result["payload"] = {"backend": _backend_name(backend)}  # 新增代码+ClipboardSystemBridge：附加后端名称；如果没有这行代码，排查时不知道哪个后端失败。
        return result  # 新增代码+ClipboardSystemBridge：返回读取失败结果；如果没有这行代码，函数会继续返回未定义文本。
    context.clipboard_text = text  # 新增代码+ClipboardSystemBridge：同步旧兼容字段；如果没有这行代码，历史调试状态看不到最近一次系统读取。
    return success_result("read_clipboard", {"text": text, "text_length": len(text), "backend": _backend_name(backend)})  # 修改代码+ClipboardSystemBridge：返回系统剪贴板文本、长度和后端；如果没有这行代码，模型无法确认读取结果。
# 修改代码+ClipboardSystemBridge：函数段结束，read_clipboard 到此结束；如果没有这个边界说明，用户不容易看出授权读取范围。


def write_clipboard(context: ComputerUseMcpV2Context, text: str) -> dict[str, Any]:  # 修改代码+ClipboardSystemBridge：函数段开始，按授权写入系统剪贴板；如果没有这段函数，write_clipboard 无法执行 ClaudeCode-style 系统写入。
    if not context.grant_flags.get("clipboardWrite", False):  # 新增代码+ClipboardSystemBridge：检查剪贴板写入授权；如果没有这行代码，未授权模型可能覆盖用户系统剪贴板。
        return error_result("write_clipboard", "clipboard_write_not_granted", error_class="permission_denied")  # 新增代码+ClipboardSystemBridge：返回权限拒绝错误；如果没有这行代码，调用方无法知道缺少 clipboardWrite。
    backend = _clipboard_backend(context)  # 新增代码+ClipboardSystemBridge：读取绑定的剪贴板后端；如果没有这行代码，工具不知道该写入真实后端还是测试后端。
    if backend is None:  # 新增代码+ClipboardSystemBridge：检查后端是否存在；如果没有这行代码，空后端会导致属性错误。
        return error_result("write_clipboard", "clipboard_backend_unavailable", error_class="unavailable")  # 新增代码+ClipboardSystemBridge：返回后端不可用错误；如果没有这行代码，模型无法区分权限问题和运行时缺后端。
    value = str(text)  # 新增代码+ClipboardSystemBridge：把写入内容规范化为字符串；如果没有这行代码，非字符串输入可能导致后端失败。
    try:  # 新增代码+ClipboardSystemBridge：保护真实系统写入调用；如果没有这行代码，Windows 剪贴板异常会中断整个工具链。
        backend.write_text(value)  # 新增代码+ClipboardSystemBridge：把文本写入绑定后端；如果没有这行代码，系统剪贴板不会更新。
    except Exception as error:  # 新增代码+ClipboardSystemBridge：捕获后端写入异常；如果没有这行代码，剪贴板被占用时会让 agent 主循环崩溃。
        result = error_result("write_clipboard", f"clipboard_write_failed:{error}", error_class="clipboard_backend_error")  # 新增代码+ClipboardSystemBridge：生成后端写入失败结果；如果没有这行代码，调用方看不到失败原因。
        result["payload"] = {"backend": _backend_name(backend), "text_length": len(value)}  # 新增代码+ClipboardSystemBridge：附加后端和长度摘要；如果没有这行代码，排查时不知道失败发生在哪个后端。
        return result  # 新增代码+ClipboardSystemBridge：返回写入失败结果；如果没有这行代码，函数会继续假装成功。
    context.clipboard_text = value  # 修改代码+ClipboardSystemBridge：同步旧兼容字段；如果没有这行代码，历史调试和旧状态读取看不到最近一次写入。
    return success_result("write_clipboard", {"text_length": len(value), "backend": _backend_name(backend)})  # 修改代码+ClipboardSystemBridge：返回写入摘要和后端；如果没有这行代码，模型无法确认写入状态。
# 修改代码+ClipboardSystemBridge：函数段结束，write_clipboard 到此结束；如果没有这个边界说明，用户不容易看出授权写入范围。

