"""Computer Use MCP v2 旧能力内部 facade 围栏测试。"""  # 新增代码+ComputerUseMcpV2InternalAdapterFence：说明本文件只验证旧状态/观察/发现/执行能力已经被内部 facade 隔离；如果没有这行代码，后续读者不容易理解为什么要检查源码接线。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2InternalAdapterFence：延迟解析类型注解，避免测试导入阶段因类型顺序失败；如果没有这行代码，老运行方式可能提前求值类型。

import unittest  # 新增代码+ComputerUseMcpV2InternalAdapterFence：使用标准 unittest 框架；如果没有这行代码，本测试文件不会被正常发现。
from pathlib import Path  # 新增代码+ComputerUseMcpV2InternalAdapterFence：用于定位生产源码文件；如果没有这行代码，测试只能依赖脆弱字符串路径。

from learning_agent.computer_use_mcp_v2.windows_runtime import internal_adapter_tools  # 新增代码+ComputerUseMcpV2InternalAdapterFence：导入新增内部 facade 模块；如果没有这行代码，测试无法证明旧能力有新的内部边界。
from learning_agent.tests.test_computer_use_mcp_session_adapter import _make_adapter  # 新增代码+ComputerUseMcpV2InternalAdapterFence：复用已有 fake controller 装配；如果没有这行代码，测试会重复构造大量回调样板。


class ComputerUseMcpV2InternalAdapterFenceTests(unittest.TestCase):  # 新增代码+ComputerUseMcpV2InternalAdapterFence：函数段开始，验证旧工具名只作为内部实现被复用；如果没有这段测试，接线层可能重新直接依赖旧公开工具名。
    def test_session_adapter_uses_internal_facade_instead_of_direct_agent_tools_import(self) -> None:  # 新增代码+ComputerUseMcpV2InternalAdapterFence：验证 session adapter 源码不再直接导入 agent_tools；如果没有这行测试，旧公开工具名会再次污染接线层。
        source_path = Path(__file__).resolve().parents[1] / "computer_use_mcp_v2" / "windows_runtime" / "mcp_session_adapter.py"  # 新增代码+ComputerUseMcpV2InternalAdapterFence：定位被测 session adapter 源码；如果没有这行代码，测试不知道要检查哪个文件。
        source_text = source_path.read_text(encoding="utf-8")  # 新增代码+ComputerUseMcpV2InternalAdapterFence：读取源码文本用于围栏检查；如果没有这行代码，测试无法发现导入回归。
        self.assertIn("internal_adapter_tools as computer_use_internal_adapter_tools", source_text)  # 新增代码+ComputerUseMcpV2InternalAdapterFence：确认接线层依赖内部 facade；如果没有这行代码，只看行为无法知道命名边界是否收紧。
        self.assertNotIn("agent_tools as computer_use_agent_tools", source_text)  # 新增代码+ComputerUseMcpV2InternalAdapterFence：确认不再直接把旧工具模块作为接线依赖；如果没有这行代码，旧工具名会继续造成误判。
        self.assertNotIn("computer_use_agent_tools.", source_text)  # 新增代码+ComputerUseMcpV2InternalAdapterFence：确认源码里没有旧别名方法调用；如果没有这行代码，局部调用回归不会被发现。

    def test_internal_facade_exports_only_internal_adapter_names(self) -> None:  # 新增代码+ComputerUseMcpV2InternalAdapterFence：验证 facade 暴露的是内部命名；如果没有这行测试，facade 可能直接重导出旧工具名。
        expected_names = {"internal_request_access", "internal_status_snapshot", "internal_discover_applications", "internal_observe_desktop", "internal_execute_desktop_action"}  # 新增代码+ComputerUseMcpV2InternalAdapterFence：列出内部 facade 应有能力；如果没有这行代码，断言会散落难维护。
        for name in expected_names:  # 新增代码+ComputerUseMcpV2InternalAdapterFence：逐项检查内部能力存在；如果没有这行代码，缺某个 facade 函数不会被发现。
            self.assertTrue(callable(getattr(internal_adapter_tools, name, None)), name)  # 新增代码+ComputerUseMcpV2InternalAdapterFence：断言内部能力可调用；如果没有这行代码，导入存在但函数不可用也会漏掉。
        self.assertFalse(hasattr(internal_adapter_tools, "computer_status"))  # 新增代码+ComputerUseMcpV2InternalAdapterFence：确认 facade 不直接暴露旧状态工具名；如果没有这行代码，旧名可能从 facade 再次泄露。
        self.assertFalse(hasattr(internal_adapter_tools, "computer_action"))  # 新增代码+ComputerUseMcpV2InternalAdapterFence：确认 facade 不直接暴露旧动作工具名；如果没有这行代码，旧 action 名称可能继续被误当公开接口。

    def test_internal_status_facade_still_preserves_mature_status_chain(self) -> None:  # 新增代码+ComputerUseMcpV2InternalAdapterFence：验证改名后旧状态能力仍能被内部调用；如果没有这行测试，命名隔离可能误伤成熟状态链。
        adapter, _controller, recorder = _make_adapter()  # 新增代码+ComputerUseMcpV2InternalAdapterFence：创建带 fake controller 和回调的 adapter；如果没有这行代码，测试无法执行内部状态能力。
        result = adapter.call_atomic_tool("computer_status", {"reason": "internal fence smoke"})  # 新增代码+ComputerUseMcpV2InternalAdapterFence：用内部兼容名触发状态快照；如果没有这行代码，无法证明 facade 仍能到达旧状态链。
        self.assertTrue(result["ok"], result)  # 新增代码+ComputerUseMcpV2InternalAdapterFence：确认状态快照仍成功；如果没有这行代码，命名隔离导致的功能断裂不会被发现。
        self.assertEqual("mcp__computer-use__observe", result["payload"]["legacy_internal_tool"])  # 新增代码+ComputerUseMcpV2InternalAdapterFence：确认对模型呈现的是 v2 observe 入口；如果没有这行代码，状态返回可能再次泄露旧工具名。
        self.assertIn("computer_status", [kind for kind, _payload in recorder.traces])  # 新增代码+ComputerUseMcpV2InternalAdapterFence：确认内部仍保留旧成熟 trace 事件；如果没有这行代码，状态证据链可能被命名隔离切断。
    # 新增代码+ComputerUseMcpV2InternalAdapterFence：函数段结束，ComputerUseMcpV2InternalAdapterFenceTests 到此结束；如果没有这个边界说明，用户不容易看出内部 facade 测试范围。


if __name__ == "__main__":  # 新增代码+ComputerUseMcpV2InternalAdapterFence：允许直接运行本测试文件；如果没有这行代码，手动调试只能通过模块名运行。
    unittest.main()  # 新增代码+ComputerUseMcpV2InternalAdapterFence：启动 unittest 主程序；如果没有这行代码，直接运行文件不会执行测试。
