from __future__ import annotations  # 新增代码+ClipboardSystemBridge：延迟解析类型注解；如果没有这行代码，测试里的类型注解可能在导入时提前求值。

import unittest  # 新增代码+ClipboardSystemBridge：导入 unittest 测试框架；如果没有这行代码，本文件无法声明和运行测试用例。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.clipboard import read_clipboard, write_clipboard  # 新增代码+ClipboardSystemBridge：导入待验证的剪贴板工具；如果没有这行代码，测试无法证明工具是否走系统后端。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.types import ComputerUseMcpV2Context  # 新增代码+ClipboardSystemBridge：导入 v2 上下文；如果没有这行代码，测试无法给工具注入授权和后端。
from learning_agent.computer_use_mcp_v2.windows_runtime.system_clipboard import MemoryClipboardBackend  # 新增代码+ClipboardSystemBridge：导入内存剪贴板后端；如果没有这行代码，自动化测试会污染用户真实剪贴板。


class ComputerUseMcpV2ClipboardSystemBridgeTests(unittest.TestCase):  # 新增代码+ClipboardSystemBridge：类段开始，集中验证 v2 剪贴板系统桥接；如果没有这段类，剪贴板对齐缺少自动化保护。
    def test_write_then_read_uses_bound_clipboard_backend(self) -> None:  # 新增代码+ClipboardSystemBridge：函数段开始，验证写入后读取走绑定后端；如果没有这段测试，context-only 回退可能悄悄复发。
        backend = MemoryClipboardBackend(initial_text="")  # 新增代码+ClipboardSystemBridge：创建不会触碰真实系统的测试后端；如果没有这行代码，测试可能读写用户真实剪贴板。
        context = ComputerUseMcpV2Context(clipboard_backend=backend)  # 新增代码+ClipboardSystemBridge：把测试后端注入 v2 上下文；如果没有这行代码，工具无法证明使用的是绑定后端。
        context.grant_flags["clipboardRead"] = True  # 新增代码+ClipboardSystemBridge：授予剪贴板读取权限；如果没有这行代码，读取工具应按安全策略拒绝。
        context.grant_flags["clipboardWrite"] = True  # 新增代码+ClipboardSystemBridge：授予剪贴板写入权限；如果没有这行代码，写入工具应按安全策略拒绝。

        write_result = write_clipboard(context, "ClaudeCode parity text")  # 新增代码+ClipboardSystemBridge：执行写入动作；如果没有这行代码，测试无法建立读回事实。
        read_result = read_clipboard(context)  # 新增代码+ClipboardSystemBridge：执行读取动作；如果没有这行代码，测试无法确认写入是否进入同一个后端。

        self.assertTrue(write_result["ok"])  # 新增代码+ClipboardSystemBridge：确认写入成功；如果没有这行断言，错误结果也可能被误当通过。
        self.assertEqual(write_result["payload"]["backend"], "memory_system_clipboard")  # 新增代码+ClipboardSystemBridge：确认写入使用后端名称；如果没有这行断言，工具可能仍返回 context-only backend。
        self.assertEqual(read_result["payload"]["text"], "ClaudeCode parity text")  # 新增代码+ClipboardSystemBridge：确认读取内容等于写入内容；如果没有这行断言，读写闭环可能是假成功。
        self.assertEqual(read_result["payload"]["backend"], "memory_system_clipboard")  # 新增代码+ClipboardSystemBridge：确认读取使用同一后端；如果没有这行断言，读取可能仍走旧内存字段。
    # 新增代码+ClipboardSystemBridge：函数段结束，test_write_then_read_uses_bound_clipboard_backend 到此结束；如果没有这个边界说明，用户不容易看出读写闭环测试范围。

    def test_read_clipboard_requires_grant_flag(self) -> None:  # 新增代码+ClipboardSystemBridge：函数段开始，验证读取必须先有 grantFlag；如果没有这段测试，未授权读取可能泄露系统剪贴板。
        backend = MemoryClipboardBackend(initial_text="secret from test")  # 新增代码+ClipboardSystemBridge：准备含敏感字样的测试内容；如果没有这行代码，测试无法证明拒绝时没有读取后端。
        context = ComputerUseMcpV2Context(clipboard_backend=backend)  # 新增代码+ClipboardSystemBridge：创建注入后端的 v2 上下文；如果没有这行代码，工具无法被独立验证。
        context.grant_flags["clipboardRead"] = False  # 新增代码+ClipboardSystemBridge：显式关闭读取授权；如果没有这行代码，默认值变化会让测试不稳定。

        result = read_clipboard(context)  # 新增代码+ClipboardSystemBridge：执行未授权读取；如果没有这行代码，拒绝路径不会被触发。

        self.assertFalse(result["ok"])  # 新增代码+ClipboardSystemBridge：确认未授权读取返回失败；如果没有这行断言，成功泄露也可能被忽略。
        self.assertEqual(result["error_class"], "permission_denied")  # 新增代码+ClipboardSystemBridge：确认错误类别是权限拒绝；如果没有这行断言，调用方无法稳定处理授权失败。
        self.assertEqual(backend.read_count, 0)  # 新增代码+ClipboardSystemBridge：确认拒绝时没有触碰后端；如果没有这行断言，工具可能先读取再报错。
    # 新增代码+ClipboardSystemBridge：函数段结束，test_read_clipboard_requires_grant_flag 到此结束；如果没有这个边界说明，用户不容易看出读取拒绝测试范围。

    def test_write_clipboard_requires_grant_flag(self) -> None:  # 新增代码+ClipboardSystemBridge：函数段开始，验证写入必须先有 grantFlag；如果没有这段测试，未授权写入可能污染用户剪贴板。
        backend = MemoryClipboardBackend(initial_text="original")  # 新增代码+ClipboardSystemBridge：准备原始剪贴板值；如果没有这行代码，无法确认拒绝后内容没有被改写。
        context = ComputerUseMcpV2Context(clipboard_backend=backend)  # 新增代码+ClipboardSystemBridge：创建注入后端的 v2 上下文；如果没有这行代码，工具无法访问测试后端。
        context.grant_flags["clipboardWrite"] = False  # 新增代码+ClipboardSystemBridge：显式关闭写入授权；如果没有这行代码，默认授权变化会让测试不稳定。

        result = write_clipboard(context, "blocked")  # 新增代码+ClipboardSystemBridge：执行未授权写入；如果没有这行代码，拒绝路径不会被触发。

        self.assertFalse(result["ok"])  # 新增代码+ClipboardSystemBridge：确认未授权写入返回失败；如果没有这行断言，污染剪贴板也可能被误判成功。
        self.assertEqual(result["error_class"], "permission_denied")  # 新增代码+ClipboardSystemBridge：确认错误类别是权限拒绝；如果没有这行断言，模型无法理解失败原因。
        self.assertEqual(backend.text, "original")  # 新增代码+ClipboardSystemBridge：确认拒绝后原内容不变；如果没有这行断言，工具可能先写入再报错。
    # 新增代码+ClipboardSystemBridge：函数段结束，test_write_clipboard_requires_grant_flag 到此结束；如果没有这个边界说明，用户不容易看出写入拒绝测试范围。


if __name__ == "__main__":  # 新增代码+ClipboardSystemBridge：允许直接运行本测试文件；如果没有这行代码，手动调试时需要额外记住 unittest 参数。
    unittest.main()  # 新增代码+ClipboardSystemBridge：启动 unittest 主程序；如果没有这行代码，直接运行文件不会执行测试。
