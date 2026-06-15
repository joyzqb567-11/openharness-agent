"""Computer Use MCP v2 状态、观察、执行闭环测试。"""  # 新增代码+ComputerUseMcpV2StateLoop：说明本文件验证 observe 后 action 能共享状态并保留审计证据；如果没有这行代码，后续维护者不容易知道这里锁的是闭环能力。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2StateLoop：延迟解析类型注解，避免测试导入阶段因类型顺序失败；如果没有这行代码，老运行方式可能提前求值类型。

import json  # 新增代码+ComputerUseMcpV2StateLoop：用于解析工具返回 JSON；如果没有这行代码，测试只能靠不稳定的文本包含判断。
import tempfile  # 新增代码+ComputerUseMcpV2StateLoop：用于创建临时 workspace；如果没有这行代码，fake agent 可能污染真实项目目录。
import unittest  # 新增代码+ComputerUseMcpV2StateLoop：使用标准 unittest 框架；如果没有这行代码，本测试不会被测试系统发现。
from pathlib import Path  # 新增代码+ComputerUseMcpV2StateLoop：用 Path 表示临时目录；如果没有这行代码，fake agent workspace 类型会和真实代码不一致。

from learning_agent.computer_use_mcp_v2.windows_runtime.controller import ComputerUseController, MemoryComputerUseBackend  # 新增代码+ComputerUseMcpV2StateLoop：导入无副作用 controller 和内存后端；如果没有这行代码，测试可能需要触碰真实桌面。
from learning_agent.core.messages import ToolCall  # 新增代码+ComputerUseMcpV2StateLoop：使用真实工具调用对象；如果没有这行代码，测试无法覆盖 agent 顶层执行入口。
from learning_agent.mcp.agent_adapter import execute_mcp_tool  # 新增代码+ComputerUseMcpV2StateLoop：导入真实 MCP 执行入口；如果没有这行代码，闭环测试只能测底层函数。
from learning_agent.tests.test_computer_use_mcp_agent_side_binding import _FakeAgent  # 新增代码+ComputerUseMcpV2StateLoop：复用带阻断 registry 的 fake agent；如果没有这行代码，测试无法证明闭环不走外部 registry。


class ComputerUseMcpV2StateObserveActionLoopTests(unittest.TestCase):  # 新增代码+ComputerUseMcpV2StateLoop：函数段开始，验证 agent-side observe/action 状态闭环；如果没有这段测试，observe 写状态和 action 复用状态的回归不容易被发现。
    def test_agent_side_observe_then_left_click_reuses_observed_window_and_records_trace(self) -> None:  # 新增代码+ComputerUseMcpV2StateLoop：验证 observe 后 left_click 可以复用可信窗口并记录 trace；如果没有这行测试，状态、观察、执行三段可能再次断开。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseMcpV2StateLoop：创建临时目录隔离 fake agent；如果没有这行代码，测试会污染真实 workspace。
            window = {"app_id": "notepad.exe", "window_id": "hwnd:state-loop", "title_preview": "Untitled - Notepad"}  # 新增代码+ComputerUseMcpV2StateLoop：准备可信窗口引用；如果没有这行代码，observe 没有可返回的目标窗口。
            backend = MemoryComputerUseBackend(windows=[window])  # 新增代码+ComputerUseMcpV2StateLoop：创建只记录动作的内存后端；如果没有这行代码，测试可能触发真实鼠标键盘。
            agent = _FakeAgent(Path(raw_dir))  # 新增代码+ComputerUseMcpV2StateLoop：创建 fake agent；如果没有这行代码，execute_mcp_tool 没有主循环上下文。
            agent.computer_use_controller = ComputerUseController(backend)  # 新增代码+ComputerUseMcpV2StateLoop：把成熟 controller 注入 agent-side v2 绑定；如果没有这行代码，v2 工具不会复用旧状态/观察/执行链。
            observe_output = execute_mcp_tool(agent, ToolCall(name="mcp__computer-use__observe", arguments={"reason": "state loop observe"}))  # 新增代码+ComputerUseMcpV2StateLoop：先通过模型可见 observe 工具读取桌面状态；如果没有这行代码，后续 click 没有可信窗口状态可复用。
            click_output = execute_mcp_tool(agent, ToolCall(name="mcp__computer-use__left_click", arguments={"x": 10, "y": 20, "reason": "state loop click"}))  # 新增代码+ComputerUseMcpV2StateLoop：再通过模型可见 left_click 工具执行动作；如果没有这行代码，闭环测试无法覆盖执行阶段。
            observe_payload = json.loads(observe_output)  # 新增代码+ComputerUseMcpV2StateLoop：解析 observe 结果；如果没有这行代码，测试无法结构化确认成功和 runtime。
            click_payload = json.loads(click_output)  # 新增代码+ComputerUseMcpV2StateLoop：解析 click 结果；如果没有这行代码，测试无法结构化确认成功和 adapter 来源。
            self.assertTrue(observe_payload["ok"], observe_payload)  # 新增代码+ComputerUseMcpV2StateLoop：确认观察成功；如果没有这行代码，失败观察也可能被后续动作掩盖。
            self.assertTrue(click_payload["ok"], click_payload)  # 新增代码+ComputerUseMcpV2StateLoop：确认动作成功；如果没有这行代码，闭环断开不会被发现。
            self.assertEqual("computer_use_mcp_v2", observe_payload["runtime"])  # 新增代码+ComputerUseMcpV2StateLoop：确认 observe 来自 v2 runtime；如果没有这行代码，旧入口回归可能混进来。
            self.assertEqual("computer_use_mcp_v2", click_payload["runtime"])  # 新增代码+ComputerUseMcpV2StateLoop：确认 left_click 来自 v2 runtime；如果没有这行代码，旧入口或外部 registry 可能混进来。
            self.assertEqual([], agent.mcp_tool_registry.calls)  # 新增代码+ComputerUseMcpV2StateLoop：确认整个闭环没有调用外部 registry；如果没有这行代码，agent-side 主路径可能再次被绕开。
            self.assertEqual("click", backend.actions[0]["action"])  # 新增代码+ComputerUseMcpV2StateLoop：确认 left_click 最终映射到成熟 controller 的 click 动作；如果没有这行代码，动作语义可能漂移。
            self.assertEqual("notepad.exe", backend.actions[0]["window"]["app_id"])  # 新增代码+ComputerUseMcpV2StateLoop：确认动作自动复用 observe 得到的窗口；如果没有这行代码，Phase 30 缺窗口拒绝可能回归。
            self.assertIn("tool_started", [event["phase"] for event in agent.computer_use_runtime_trace_events])  # 新增代码+ComputerUseMcpV2StateLoop：确认 trace 记录工具开始；如果没有这行代码，长任务审计看不到动作起点。
            self.assertIn("tool_completed", [event["phase"] for event in agent.computer_use_runtime_trace_events])  # 新增代码+ComputerUseMcpV2StateLoop：确认 trace 记录工具完成；如果没有这行代码，长任务审计看不到动作结果。
            self.assertTrue(any(event.get("payload", {}).get("tool_name") == "observe" for event in agent.computer_use_runtime_trace_events))  # 新增代码+ComputerUseMcpV2StateLoop：确认 observe trace 存在；如果没有这行代码，观察阶段可能没有进入证据链。
            self.assertTrue(any(event.get("payload", {}).get("tool_name") == "left_click" for event in agent.computer_use_runtime_trace_events))  # 新增代码+ComputerUseMcpV2StateLoop：确认 left_click trace 存在；如果没有这行代码，执行阶段可能没有进入证据链。
    # 新增代码+ComputerUseMcpV2StateLoop：函数段结束，ComputerUseMcpV2StateObserveActionLoopTests 到此结束；如果没有这个边界说明，用户不容易看出闭环测试范围。


if __name__ == "__main__":  # 新增代码+ComputerUseMcpV2StateLoop：允许直接运行本测试文件；如果没有这行代码，手动调试只能通过模块名运行。
    unittest.main()  # 新增代码+ComputerUseMcpV2StateLoop：启动 unittest 主程序；如果没有这行代码，直接运行文件不会执行测试。
