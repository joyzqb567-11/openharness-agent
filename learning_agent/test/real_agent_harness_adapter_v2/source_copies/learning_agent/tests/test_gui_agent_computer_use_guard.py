import tempfile  # 新增代码+RealHarnessComputerUseGuardTest：创建隔离 workspace；如果没有这一行，测试会污染真实项目 memory。
import unittest  # 新增代码+RealHarnessComputerUseGuardTest：使用标准库 unittest 编写 Phase 6 合同；如果没有这一行，测试不会被收集。

from learning_agent.app.gui_agent_adapter import DefaultHarnessGuiAgentAdapter, GuiAgentRunRequest  # 新增代码+RealHarnessComputerUseGuardTest：导入真实 adapter shell 和请求对象；如果没有这一行，Computer Use 门禁无法走 GUI adapter。
from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+RealHarnessComputerUseGuardTest：构造假模型桌面工具调用；如果没有这一行，测试需要真实模型。
from learning_agent.models.fake import ToolCallingFakeModel  # 新增代码+RealHarnessComputerUseGuardTest：使用离线假模型；如果没有这一行，测试需要联网。


class GuiAgentComputerUseGuardTest(unittest.TestCase):  # 新增代码+RealHarnessComputerUseGuardTest：测试类段开始，验证 Computer Use 默认受控；如果没有这个类，Phase 6 没有自动验收。
    def test_default_real_harness_rejects_forged_computer_use_tool_call(self) -> None:  # 新增代码+RealHarnessComputerUseGuardTest：测试函数开始，验证模型伪造桌面工具也不会执行；如果没有这段，GUI agent 可能绕过 Computer Use 门禁。
        with tempfile.TemporaryDirectory() as directory:  # 新增代码+RealHarnessComputerUseGuardTest：创建隔离 workspace；如果没有这一行，agent 会写真实 memory。
            forged_call = ToolCall(name="mcp__computer-use__click", arguments={"x": 10, "y": 20}, call_id="call_computer_1")  # 新增代码+RealHarnessComputerUseGuardTest：构造伪造桌面点击工具；如果没有这一行，测试无法验证拦截。
            fake_model = ToolCallingFakeModel([ModelMessage(tool_calls=[forged_call]), ModelMessage(text="COMPUTER_USE_GUARD_OK")])  # 新增代码+RealHarnessComputerUseGuardTest：安排假模型先尝试桌面工具再总结；如果没有这一行，主循环不会进入工具守卫。
            request = GuiAgentRunRequest(session_id="session_cu", turn_id="turn_cu", run_id="run_cu", prompt="尝试点击屏幕", workspace=directory, provider_id="test-fake")  # 新增代码+RealHarnessComputerUseGuardTest：构造真实 adapter 请求；如果没有这一行，adapter 没有运行身份。
            events: list[dict[str, object]] = []  # 新增代码+RealHarnessComputerUseGuardTest：保存 GUI 事件；如果没有这一行，无法检查门禁证据。
            adapter = DefaultHarnessGuiAgentAdapter(enabled=True, model_factory=lambda _request: fake_model, max_turns=2)  # 新增代码+RealHarnessComputerUseGuardTest：使用默认无工具 real harness；如果没有这一行，Computer Use 可能被显式白名单放行。
            result = adapter.run(request, events.append, lambda: False)  # 新增代码+RealHarnessComputerUseGuardTest：运行真实主循环；如果没有这一行，工具守卫不会执行。
        runtime_event = next(event for event in events if event.get("kind") == "runtime_path")  # 新增代码+RealHarnessComputerUseGuardTest：读取运行路径事件；如果没有这一行，无法确认工具默认关闭。
        tool_finished = next(event for event in events if event.get("kind") == "tool_finished")  # 新增代码+RealHarnessComputerUseGuardTest：读取工具完成事件；如果没有这一行，无法确认拒绝结果可见。
        output_text = str(tool_finished["payload"].get("output", ""))  # 新增代码+RealHarnessComputerUseGuardTest：读取工具结果文本；如果没有这一行，断言会混在 payload 访问里。
        self.assertEqual("completed", result.status)  # 新增代码+RealHarnessComputerUseGuardTest：确认 agent 能从拒绝结果恢复；如果没有这一行，守卫拒绝可能让主循环崩溃。
        self.assertFalse(runtime_event["payload"]["tools_enabled"])  # 新增代码+RealHarnessComputerUseGuardTest：确认默认 real harness 不暴露工具；如果没有这一行，Computer Use 门禁证据不足。
        self.assertIn("tool_started", [str(event.get("kind", "")) for event in events])  # 新增代码+RealHarnessComputerUseGuardTest：确认伪造尝试进入可见轨迹；如果没有这一行，用户看不到模型尝试了什么。
        self.assertIn("不在当前 agent 的 allowed_tools 范围内", output_text)  # 新增代码+RealHarnessComputerUseGuardTest：确认执行层因白名单拒绝；如果没有这一行，桌面动作可能绕过默认锁。
    # 新增代码+RealHarnessComputerUseGuardTest：测试函数结束，test_default_real_harness_rejects_forged_computer_use_tool_call 到此结束；如果没有这个边界说明，用户不容易看出 Computer Use 默认门禁范围。
# 新增代码+RealHarnessComputerUseGuardTest：测试类段结束，GuiAgentComputerUseGuardTest 到此结束；如果没有这个边界说明，用户不容易看出本文件覆盖 Phase 6。


if __name__ == "__main__":  # 新增代码+RealHarnessComputerUseGuardTest：允许直接运行本测试文件；如果没有这一行，手动排查时不会启动 unittest。
    unittest.main()  # 新增代码+RealHarnessComputerUseGuardTest：执行测试主程序；如果没有这一行，直接运行文件不会跑测试。
