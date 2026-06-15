from __future__ import annotations  # 新增代码+McpBatchSafety: 延迟解析类型注解；如果没有这一行，fake 类型在导入时可能受定义顺序影响。

import unittest  # 新增代码+McpBatchSafety: 使用标准库测试框架；如果没有这一行，测试文件不会被 unittest 执行。
from typing import Any  # 新增代码+McpBatchSafety: 标注 fake controller 参数类型；如果没有这一行，测试对象边界不清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_executor import ComputerUseMcpExecutionContext, call_computer_use_mcp_tool  # 修改代码+ComputerUseMcpV2ImportCutover: 改从 v2 Windows runtime 导入内部 MCP executor；如果没有这一行，删除旧 computer_use 包后 batch 安全测试会失效。
from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import ComputerUseMcpSessionAdapter, ComputerUseMcpSessionState  # 修改代码+ComputerUseMcpV2ImportCutover: 改从 v2 Windows runtime 导入 session adapter 和共享状态；如果没有这一行，batch 状态复用测试仍会依赖旧包。


class _FakeControllerResult:  # 新增代码+McpBatchSafety: 函数段开始，模拟 controller 返回值；如果没有这个类，action 分支无法用 fake controller 返回结果。
    def __init__(self, ok: bool = True, message: str = "ok", data: dict[str, Any] | None = None) -> None:  # 新增代码+McpBatchSafety: 初始化结果字段；如果没有这一行，adapter 读取 ok/message/data 会失败。
        self.ok = ok  # 修改代码+ComputerUseMcpV2ResidualCleanup: 保存成功状态；如果没有这一行，v2 MCP adapter 无法判断 fake controller 结果是否成功。
        self.message = message  # 新增代码+McpBatchSafety: 保存消息；如果没有这一行，结果文本缺少摘要。
        self.data = data or {}  # 新增代码+McpBatchSafety: 保存结构化数据；如果没有这一行，trace 和 artifact helper 缺输入。

    def to_text(self, tool_name: str = "mcp__computer-use__computer_batch") -> str:  # 修改代码+ComputerUseMcpV2ResidualCleanup: 模拟 v2 MCP controller 结果文本化；如果没有这一行，session adapter 调用 result.to_text 会失败。
        return f'{{"ok": true, "tool_name": "{tool_name}", "message": "{self.message}"}}'  # 修改代码+ComputerUseMcpV2ResidualCleanup: 返回最小 JSON 文本并默认使用 v2 MCP 工具名；如果没有这一行，adapter 包装文本时会继续泄露旧 computer_action。
# 新增代码+McpBatchSafety: 函数段结束，_FakeControllerResult 到此结束；如果没有这个边界说明，用户不容易看出 fake 结果范围。


class _RecordingController:  # 新增代码+McpBatchSafety: 函数段开始，记录是否触达真实动作路径；如果没有这个类，测试无法证明 shell 拒绝没有碰 controller。
    def __init__(self) -> None:  # 新增代码+McpBatchSafety: 初始化记录容器；如果没有这一行，执行历史没有存放位置。
        self.executed: list[dict[str, Any]] = []  # 新增代码+McpBatchSafety: 保存 execute 参数；如果没有这一行，测试无法断言第二步未执行。

    def execute(self, arguments: dict[str, Any]) -> _FakeControllerResult:  # 新增代码+McpBatchSafety: 模拟 controller 动作执行；如果没有这一行，type/click 分支无法执行。
        self.executed.append(dict(arguments))  # 新增代码+McpBatchSafety: 记录动作参数；如果没有这一行，测试无法确认是否触达 controller。
        return _FakeControllerResult(True, "executed", {"low_level_event_count": 1})  # 修改代码+ComputerUseMcpV2ResidualCleanup: 返回成功结果；如果没有这一行，v2 原子 action 无法在 fake controller 路径完成。
# 新增代码+McpBatchSafety: 函数段结束，_RecordingController 到此结束；如果没有这个边界说明，用户不容易看出 fake controller 范围。


class _RecordingAdapter:  # 新增代码+McpBatchSafety: 函数段开始，记录 executor 是否把危险单步交给 adapter；如果没有这个类，单步 shell 拒绝顺序无法验证。
    def __init__(self) -> None:  # 新增代码+McpBatchSafety: 初始化 adapter 调用记录；如果没有这一行，测试无法检查调用次数。
        self.calls: list[tuple[str, dict[str, Any]]] = []  # 新增代码+McpBatchSafety: 保存 adapter 收到的调用；如果没有这一行，危险参数是否进入 adapter 不可见。

    def call_atomic_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpBatchSafety: 模拟 adapter 执行入口；如果没有这一行，mcp_executor 无法委托 fake adapter。
        self.calls.append((tool_name, dict(arguments)))  # 新增代码+McpBatchSafety: 记录本次调用；如果没有这一行，测试无法断言拒绝发生在 adapter 之前。
        return {"ok": True, "tool_name": tool_name, "error_class": "", "payload": {"adapter_called": True}, "text": "adapter called"}  # 新增代码+McpBatchSafety: 返回成功结果；如果没有这一行，正常委托路径没有输出。
# 新增代码+McpBatchSafety: 函数段结束，_RecordingAdapter 到此结束；如果没有这个边界说明，用户不容易看出 fake adapter 范围。


def _session_context(controller: _RecordingController) -> ComputerUseMcpExecutionContext:  # 新增代码+McpBatchSafety: 函数段开始，构造带真实 session adapter 的 executor context；如果没有这段函数，每个测试会重复装配状态。
    state = ComputerUseMcpSessionState()  # 新增代码+McpBatchSafety: 创建共享状态；如果没有这一行，剪贴板 batch 不能证明同一状态复用。
    adapter = ComputerUseMcpSessionAdapter(controller=controller, state=state)  # 新增代码+McpBatchSafety: 创建 session adapter；如果没有这一行，executor 只能走独立 controller 路径。
    return ComputerUseMcpExecutionContext(controller_factory=lambda: controller, session_adapter=adapter)  # 新增代码+McpBatchSafety: 返回带 adapter 的执行上下文；如果没有这一行，call_computer_use_mcp_tool 不会启用 agent-side batch 逻辑。
# 新增代码+McpBatchSafety: 函数段结束，_session_context 到此结束；如果没有这个边界说明，用户不容易看出测试装配范围。


class ComputerUseMcpBatchSafetyTests(unittest.TestCase):  # 新增代码+McpBatchSafety: 函数段开始，验证 batch 状态复用和 shell 拒绝边界；如果没有这个测试类，批量原子工具容易回归成危险旁路。
    def test_batch_with_session_adapter_preserves_clipboard_state(self) -> None:  # 新增代码+McpBatchSafety: 验证 batch 内步骤共享同一 adapter 状态；如果没有这个测试，write_clipboard/read_clipboard 可能跨步骤断开。
        controller = _RecordingController()  # 新增代码+McpBatchSafety: 创建 fake controller；如果没有这一行，context 缺少 controller。
        context = _session_context(controller)  # 新增代码+McpBatchSafety: 创建带 session adapter 的执行上下文；如果没有这一行，batch 不会走共享 state。
        result = call_computer_use_mcp_tool("computer_batch", {"steps": [{"tool_name": "write_clipboard", "arguments": {"text": "shared text"}}, {"tool_name": "read_clipboard", "arguments": {}}]}, context)  # 新增代码+McpBatchSafety: 执行写后读 batch；如果没有这一行，无法证明状态跨步骤复用。
        self.assertTrue(result["ok"])  # 新增代码+McpBatchSafety: 断言 batch 成功；如果没有这一行，失败批量也可能被误认为通过。
        self.assertEqual("shared text", result["payload"]["results"][1]["payload"]["text"])  # 新增代码+McpBatchSafety: 断言第二步读到第一步写入文本；如果没有这一行，共享状态断开不会暴露。
        self.assertEqual([], controller.executed)  # 新增代码+McpBatchSafety: 断言剪贴板 batch 没有碰 controller；如果没有这一行，只读状态工具可能误触真实动作后端。

    def test_batch_shell_rejection_stops_before_second_step_and_controller(self) -> None:  # 新增代码+McpBatchSafety: 验证 batch shell 拒绝会停止后续步骤；如果没有这个测试，危险参数后仍可能继续输入文字。
        controller = _RecordingController()  # 新增代码+McpBatchSafety: 创建 fake controller；如果没有这一行，无法断言是否触达动作。
        context = _session_context(controller)  # 新增代码+McpBatchSafety: 创建带 session adapter 的执行上下文；如果没有这一行，batch 逐步拒绝路径不会被覆盖。
        result = call_computer_use_mcp_tool("computer_batch", {"steps": [{"tool_name": "left_click", "arguments": {"x": 1, "y": 2, "command": "whoami"}}, {"tool_name": "type", "arguments": {"text": "should not run"}}], "stop_on_error": True}, context)  # 新增代码+McpBatchSafety: 构造第一步危险参数和第二步输入；如果没有这一行，停止策略没有输入。
        self.assertFalse(result["ok"])  # 新增代码+McpBatchSafety: 断言 batch 失败；如果没有这一行，危险拒绝可能被包装成成功。
        self.assertEqual("shell_argument_forbidden", result["payload"]["results"][0]["error_class"])  # 新增代码+McpBatchSafety: 断言第一步被 shell 参数拒绝；如果没有这一行，拒绝类别可能漂移。
        self.assertEqual(1, result["payload"]["step_count"])  # 新增代码+McpBatchSafety: 断言第二步未执行；如果没有这一行，stop_on_error 回归不会暴露。
        self.assertEqual([], controller.executed)  # 新增代码+McpBatchSafety: 断言危险 batch 没有触达 controller；如果没有这一行，真实桌面可能仍被操作。

    def test_single_shell_argument_is_rejected_before_session_adapter(self) -> None:  # 新增代码+McpBatchSafety: 验证单步危险参数在 adapter 前被拒绝；如果没有这个测试，shell 字段可能进入 agent-side adapter。
        adapter = _RecordingAdapter()  # 新增代码+McpBatchSafety: 创建记录型 fake adapter；如果没有这一行，无法检查 adapter 是否被调用。
        context = ComputerUseMcpExecutionContext(controller_factory=_RecordingController, session_adapter=adapter)  # 新增代码+McpBatchSafety: 构造带 fake adapter 的 executor context；如果没有这一行，测试无法覆盖拒绝优先级。
        result = call_computer_use_mcp_tool("left_click", {"x": 1, "y": 2, "command": "whoami"}, context)  # 新增代码+McpBatchSafety: 传入危险 command 参数；如果没有这一行，shell 参数拒绝没有输入。
        self.assertFalse(result["ok"])  # 新增代码+McpBatchSafety: 断言调用失败；如果没有这一行，危险参数放行不会暴露。
        self.assertEqual("shell_argument_forbidden", result["error_class"])  # 新增代码+McpBatchSafety: 断言失败类别明确；如果没有这一行，模型无法根据错误恢复。
        self.assertEqual([], adapter.calls)  # 新增代码+McpBatchSafety: 断言拒绝发生在 adapter 前；如果没有这一行，危险字段可能污染 agent-side 回调链。
# 新增代码+McpBatchSafety: 函数段结束，ComputerUseMcpBatchSafetyTests 到此结束；如果没有这个边界说明，用户不容易看出 batch safety 测试范围。


if __name__ == "__main__":  # 新增代码+McpBatchSafety: 支持直接运行测试文件；如果没有这一行，手动调试只能通过模块名运行。
    unittest.main()  # 新增代码+McpBatchSafety: 启动 unittest；如果没有这一行，直接运行文件不会执行测试。
