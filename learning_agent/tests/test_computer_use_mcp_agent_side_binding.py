from __future__ import annotations  # 新增代码+McpAgentBindingRedTest: 让类型注解延迟解析；如果没有这一行，测试 fake 类型在导入时可能提前求值失败。

import json  # 新增代码+ComputerUseMcpV2HostAdapter: 解析 v2 wrapper 返回的 JSON 文本；如果没有这一行，新测试只能用脆弱字符串判断执行结果。
import tempfile  # 新增代码+McpAgentBindingRedTest: 创建临时 workspace；如果没有这一行，fake agent 没有安全的工作目录。
import unittest  # 新增代码+McpAgentBindingRedTest: 使用标准库测试框架；如果没有这一行，测试不会被 unittest 发现。
from pathlib import Path  # 新增代码+McpAgentBindingRedTest: 用 Path 表示 workspace；如果没有这一行，fake agent 路径字段不稳定。
from typing import Any  # 新增代码+McpAgentBindingRedTest: 标注 fake payload 的动态类型；如果没有这一行，测试对象边界不清楚。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.actions import perform_action  # 新增代码+McpHostFailureRedTest: 直接测试 v2 action 包装层；如果没有这一行，host 内部失败被顶层改成成功的回归无法被单测抓住。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.types import ComputerUseMcpV2Context  # 新增代码+McpHostFailureRedTest: 创建最小 v2 context；如果没有这一行，测试无法注入拒绝型 host。
from learning_agent.computer_use_mcp_v2.windows_runtime.controller import ComputerUseController, MemoryComputerUseBackend  # 修改代码+ComputerUseMcpV2ImportCutover: 改从 v2 Windows runtime 导入真实 controller 和内存后端；如果没有这一行，删除旧 computer_use 包后测试会误以为生产接入断开。
from learning_agent.core.messages import ToolCall  # 新增代码+McpAgentBindingRedTest: 导入正式工具调用对象；如果没有这一行，测试不会覆盖真实 execute_mcp_tool 入参。
from learning_agent.mcp.agent_adapter import execute_mcp_tool  # 新增代码+McpAgentBindingRedTest: 导入待验证的 agent-side MCP 执行入口；如果没有这一行，测试无法证明绑定缺口。


class _RejectingHost:  # 新增代码+McpHostFailureRedTest: 类段开始，模拟旧成熟 adapter 明确拒绝桌面动作；如果没有这个类，顶层失败传播测试没有稳定 host。
    def left_click(self, _arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpHostFailureRedTest: 模拟 host 的 left_click 方法；如果没有这一行，perform_action 会走 no-op 而不是 host 返回路径。
        return {"ok": False, "legacy_adapter_used": True, "backend": "computer_use_mcp_session_adapter", "reason": "缺少可信 window", "error_class": "legacy_computer_use_rejected"}  # 新增代码+McpHostFailureRedTest: 返回旧门禁拒绝 payload；如果没有这一行，测试无法证明 ok=false 会不会被外层保留。
# 新增代码+McpHostFailureRedTest: 类段结束，_RejectingHost 到此结束；如果没有这个边界说明，用户不容易看出拒绝 host 的范围。


class _BlockingRegistry:  # 新增代码+McpAgentBindingRedTest: 函数段开始，模拟不应被调用的外部 MCP registry；如果没有这个类，测试无法证明 Computer Use 走内部 adapter。
    def __init__(self) -> None:  # 新增代码+McpAgentBindingRedTest: 初始化 registry 调用记录；如果没有这一行，测试无法断言 call_tool 是否被触发。
        self.sanitized: list[tuple[str, dict[str, Any]]] = []  # 新增代码+McpAgentBindingRedTest: 保存参数清洗记录；如果没有这一行，测试无法确认仍执行 schema 清洗。
        self.calls: list[tuple[str, dict[str, Any]]] = []  # 新增代码+McpAgentBindingRedTest: 保存外部调用记录；如果没有这一行，测试无法断言 registry 未被调用。

    def sanitize_tool_arguments(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+McpAgentBindingRedTest: 模拟 registry schema 参数清洗；如果没有这一行，execute_mcp_tool 会直接复制参数而少一条真实路径。
        clean_arguments = dict(arguments)  # 新增代码+McpAgentBindingRedTest: 复制参数避免污染原对象；如果没有这一行，测试不能确认安全参数快照。
        self.sanitized.append((tool_name, clean_arguments))  # 新增代码+McpAgentBindingRedTest: 记录清洗调用；如果没有这一行，测试无法证明清洗仍发生。
        return clean_arguments  # 新增代码+McpAgentBindingRedTest: 返回清洗后参数；如果没有这一行，execute_mcp_tool 拿不到 safe_arguments。

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:  # 新增代码+McpAgentBindingRedTest: 模拟外部 MCP 调用入口；如果没有这一行，旧路径无法被测试捕获。
        self.calls.append((tool_name, dict(arguments)))  # 新增代码+McpAgentBindingRedTest: 记录错误外部调用；如果没有这一行，测试无法定位回归。
        raise AssertionError("Computer Use MCP should be handled by the agent-side adapter")  # 新增代码+McpAgentBindingRedTest: 让旧 registry 路径显式失败；如果没有这一行，错误路径可能悄悄返回假结果。
# 新增代码+McpAgentBindingRedTest: 函数段结束，_BlockingRegistry 到此结束；如果没有这个边界说明，用户不容易看出 fake registry 范围。


class _FakeController:  # 新增代码+McpAgentBindingRedTest: 函数段开始，提供 Computer Use controller 占位；如果没有这个类，adapter 构造缺少 controller 字段。
    def status(self) -> dict[str, Any]:  # 新增代码+McpAgentBindingRedTest: 模拟状态读取；如果没有这一行，状态工具分支可能缺方法。
        return {"ok": True, "backend": "fake", "real_desktop_touched": False}  # 新增代码+McpAgentBindingRedTest: 返回安全状态；如果没有这一行，状态读取没有稳定输出。
# 新增代码+McpAgentBindingRedTest: 函数段结束，_FakeController 到此结束；如果没有这个边界说明，用户不容易看出 fake controller 范围。


class _FakeAgent:  # 新增代码+McpAgentBindingRedTest: 函数段开始，模拟 execute_mcp_tool 需要的 agent 字段；如果没有这个类，测试必须启动完整 LearningAgent。
    def __init__(self, workspace: Path) -> None:  # 新增代码+McpAgentBindingRedTest: 初始化 fake agent；如果没有这一行，测试无法注入 workspace 和依赖字段。
        self.workspace = workspace  # 新增代码+McpAgentBindingRedTest: 保存工作目录；如果没有这一行，状态镜像或 artifact helper 可能缺路径。
        self.mcp_tool_registry = _BlockingRegistry()  # 新增代码+McpAgentBindingRedTest: 注入不应被调用的 registry；如果没有这一行，execute_mcp_tool 无法进入 MCP 流程。
        self.mcp_tools_enabled = True  # 新增代码+McpAgentBindingRedTest: 模拟 MCP 已启用；如果没有这一行，catalog 生命周期刷新会因缺字段中断。
        self.mcp_start_error = ""  # 新增代码+McpAgentBindingRedTest: 模拟 MCP 启动无错误；如果没有这一行，不可用提示可能缺少稳定字段。
        self._tool_catalog_cache: list[Any] | None = []  # 新增代码+McpAgentBindingRedTest: 提供空工具 catalog 缓存；如果没有这一行，catalog scope 二次检查会因 fake agent 缺字段中断。
        self.real_chrome_requested = False  # 新增代码+McpAgentBindingRedTest: 关闭真实 Chrome 客户模式；如果没有这一行，浏览器自动授权判断会因 fake agent 缺字段中断。
        self.real_browser_information_task_requested = False  # 新增代码+McpAgentBindingRedTest: 关闭浏览器信息任务模式；如果没有这一行，浏览器客户模式判断无法完成。
        self.mcp_call_progress_events: list[dict[str, Any]] = []  # 新增代码+McpAgentBindingRedTest: 保存 MCP 调用进度；如果没有这一行，record_mcp_call_progress 会属性错误。
        self.observation_events: list[dict[str, Any]] = []  # 新增代码+McpAgentBindingRedTest: 保存 observation；如果没有这一行，run_helpers 无法记录证据。
        self.permission_denials: set[str] = set()  # 新增代码+McpAgentBindingRedTest: 保存权限拒绝指纹；如果没有这一行，通用 MCP 权限逻辑会属性错误。
        self.computer_use_controller = _FakeController()  # 新增代码+McpAgentBindingRedTest: 注入 Computer Use controller；如果没有这一行，agent-side adapter 没有后端对象。
        self.desktop_task_context: dict[str, Any] = {"active": False}  # 新增代码+McpAgentBindingRedTest: 保持 full GUI 门禁关闭；如果没有这一行，动作类测试可能被 full 模式门禁影响。
        self.active_artifacts: list[str] = []  # 新增代码+McpAgentBindingRedTest: 保存图片 artifact 列表；如果没有这一行，图片登记回调会缺状态字段。
        self.computer_use_runtime_trace_events: list[dict[str, Any]] = []  # 新增代码+McpAgentBindingRedTest: 保存 Computer Use trace；如果没有这一行，runtime trace 回调会惰性创建但测试不易断言。

    def ask_permission(self, action: str) -> bool:  # 新增代码+McpAgentBindingRedTest: 模拟用户授权入口；如果没有这一行，通用 MCP 权限或动作权限无法执行。
        self.observation_events.append({"kind": "permission_seen", "payload": {"action": action}})  # 新增代码+McpAgentBindingRedTest: 记录权限文本用于排查；如果没有这一行，测试失败时难以确认是否弹了通用权限。
        return True  # 新增代码+McpAgentBindingRedTest: 自动允许测试中的安全请求；如果没有这一行，旧路径会被权限拒绝掩盖。
# 新增代码+McpAgentBindingRedTest: 函数段结束，_FakeAgent 到此结束；如果没有这个边界说明，用户不容易看出 fake agent 范围。


class ComputerUseMcpAgentSideBindingTests(unittest.TestCase):  # 新增代码+McpAgentBindingRedTest: 函数段开始，验证 Computer Use MCP 在 agent 顶层绑定内部 adapter；如果没有这个测试类，回归后模型工具会再次外部直连。
    def test_host_adapter_rejection_is_not_wrapped_as_success(self) -> None:  # 新增代码+McpHostFailureRedTest: 函数段开始，验证 host 拒绝必须向 v2 顶层传播；如果没有这个测试，left_click 被旧门禁拒绝仍可能显示 ok=true。
        context = ComputerUseMcpV2Context(host=_RejectingHost())  # 新增代码+McpHostFailureRedTest: 注入拒绝型 host；如果没有这一行，perform_action 无法进入真实失败传播路径。
        result = perform_action(context, "left_click", {"x": 10, "y": 20, "reason": "unit test rejection"})  # 新增代码+McpHostFailureRedTest: 调用模型可见动作的内部执行函数；如果没有这一行，测试不会覆盖本次验收失败的包装层。
        self.assertFalse(result["ok"], result)  # 新增代码+McpHostFailureRedTest: 断言顶层 ok 必须是 False；如果没有这一行，host 拒绝被冒充成功不会被发现。
        self.assertEqual("legacy_computer_use_rejected", result["error_class"])  # 新增代码+McpHostFailureRedTest: 断言失败类别保留旧门禁语义；如果没有这一行，模型无法按错误类型恢复。
        self.assertTrue(result["legacy_adapter_used"], result)  # 新增代码+McpHostFailureRedTest: 断言旧成熟 adapter 来源仍被保留；如果没有这一行，失败路径审计会丢失是谁拒绝的证据。
    # 新增代码+McpHostFailureRedTest: 函数段结束，test_host_adapter_rejection_is_not_wrapped_as_success 到此结束；如果没有这个边界说明，用户不容易看出失败传播测试范围。

    def test_computer_use_mcp_request_access_bypasses_registry_call_tool(self) -> None:  # 新增代码+McpAgentBindingRedTest: 验证 request_access 由 agent-side adapter 执行；如果没有这个测试，registry 旧路径回归没人发现。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+McpAgentBindingRedTest: 创建临时目录隔离状态；如果没有这一行，测试可能污染真实 workspace。
            agent = _FakeAgent(Path(raw_dir))  # 新增代码+McpAgentBindingRedTest: 创建 fake agent；如果没有这一行，execute_mcp_tool 没有执行上下文。
            output = execute_mcp_tool(agent, ToolCall(name="mcp__computer-use__request_access", arguments={"applications": ["notepad"], "reason": "unit test"}))  # 新增代码+McpAgentBindingRedTest: 调用模型可见 Computer Use MCP 工具名；如果没有这一行，无法覆盖顶层路由。
            payload = __import__("json").loads(output)  # 修改代码+ComputerUseMcpV2: 把 v2 JSON 文本转成结构化对象；如果没有这行代码，测试无法区分旧文本成功和新运行时成功。
            self.assertTrue(payload["ok"], payload)  # 修改代码+ComputerUseMcpV2: 断言 request_access 在 v2 runtime 中执行成功；如果没有这行代码，失败结果也可能只因为返回了 JSON 而被误判通过。
            self.assertEqual("computer_use_mcp_v2", payload["runtime"])  # 修改代码+ComputerUseMcpV2: 断言本次调用确实进入 v2 独立运行时；如果没有这行代码，旧 adapter 悄悄接管也不会被发现。
            self.assertFalse(payload["legacy_adapter_used"])  # 修改代码+ComputerUseMcpV2: 断言没有使用旧兼容 adapter；如果没有这行代码，旧接口可能继续影响 Computer Use 工具执行。
            self.assertEqual(agent.mcp_tool_registry.calls, [])  # 新增代码+McpAgentBindingRedTest: 断言没有调用外部 registry.call_tool；如果没有这一行，agent-side binding 的核心目标无法保护。
            self.assertIn("completed", [event["state"] for event in agent.mcp_call_progress_events])  # 新增代码+McpAgentBindingRedTest: 断言 MCP 进度仍记录完成；如果没有这一行，内部 adapter 可能绕开 agent 顶层审计。
            self.assertTrue(any(event.get("phase") == "tool_completed" and event.get("payload", {}).get("tool_name") == "request_access" for event in agent.computer_use_runtime_trace_events))  # 修改代码+ComputerUseMcpV2: 按 v2 trace 真实结构断言运行证据已写入；如果没有这行代码，工具可能只返回文本但没有进入 agent 审计链。

    def test_computer_use_mcp_left_click_reuses_controller_adapter_instead_of_noop(self) -> None:  # 新增代码+ComputerUseMcpV2HostAdapter: 函数段开始，验证 v2 left_click 必须复用旧 controller 动作链；如果没有这段测试，no-op 假成功会继续冒充真实桌面动作。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseMcpV2HostAdapter: 创建临时工作区隔离 agent 状态；如果没有这一行，测试可能污染真实 workspace。
            agent = _FakeAgent(Path(raw_dir))  # 新增代码+ComputerUseMcpV2HostAdapter: 创建最小 agent；如果没有这一行，execute_mcp_tool 没有主循环上下文。
            backend = MemoryComputerUseBackend()  # 新增代码+ComputerUseMcpV2HostAdapter: 创建只记录动作的成熟 controller 后端；如果没有这一行，测试可能触碰真实鼠标。
            agent.computer_use_controller = ComputerUseController(backend)  # 新增代码+ComputerUseMcpV2HostAdapter: 把真实 controller 注入 v2 绑定入口；如果没有这一行，无法证明 v2 能复用旧成熟执行链。
            output = execute_mcp_tool(agent, ToolCall(name="mcp__computer-use__left_click", arguments={"x": 10, "y": 20, "reason": "unit test click"}))  # 新增代码+ComputerUseMcpV2HostAdapter: 从模型可见 MCP 名调用左键工具；如果没有这一行，测试不会覆盖 agent-side 路由。
            payload = json.loads(output)  # 新增代码+ComputerUseMcpV2HostAdapter: 解析 v2 JSON 文本；如果没有这一行，后续无法结构化检查后端来源。
            self.assertTrue(payload["ok"], payload)  # 新增代码+ComputerUseMcpV2HostAdapter: 断言工具调用整体成功；如果没有这一行，失败结果可能被后续断言误解。
            self.assertTrue(payload["legacy_adapter_used"], payload)  # 新增代码+ComputerUseMcpV2HostAdapter: 断言 v2 内部复用了旧成熟 adapter；如果没有这一行，测试无法区分 controller 路径和 v2 no-op。
            self.assertNotIn("computer_use_mcp_v2_noop_safe", output)  # 新增代码+ComputerUseMcpV2HostAdapter: 断言不允许 no-op 假成功；如果没有这一行，动作看似成功但真实后端没收到。
            self.assertEqual("click", backend.actions[0]["action"])  # 新增代码+ComputerUseMcpV2HostAdapter: 断言旧 controller 后端收到 click 动作；如果没有这一行，测试无法证明真实执行链被触达。
            self.assertEqual("left", backend.actions[0]["button"])  # 新增代码+ComputerUseMcpV2HostAdapter: 断言 left_click 映射成左键；如果没有这一行，按钮语义可能漂移。
    # 新增代码+ComputerUseMcpV2HostAdapter: 函数段结束，test_computer_use_mcp_left_click_reuses_controller_adapter_instead_of_noop 到此结束；如果没有这个边界说明，用户不容易看出 no-op 回归测试范围。

    def test_computer_use_mcp_observe_reuses_controller_observation_adapter(self) -> None:  # 新增代码+ComputerUseMcpV2HostAdapter: 函数段开始，验证 v2 observe 必须复用旧观察链且不抛类型错误；如果没有这段测试，screenshot/observe 可能继续在 ComputerUseActionResult 上崩溃。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ComputerUseMcpV2HostAdapter: 创建临时工作区隔离 agent 状态；如果没有这一行，测试可能污染真实 workspace。
            window = {"app_id": "notepad.exe", "window_id": "hwnd:100", "title_preview": "Untitled - Notepad"}  # 新增代码+ComputerUseMcpV2HostAdapter: 准备内存后端可观察窗口；如果没有这一行，旧 observe 自动选窗没有可信目标。
            backend = MemoryComputerUseBackend(windows=[window])  # 新增代码+ComputerUseMcpV2HostAdapter: 创建带窗口目录的内存后端；如果没有这一行，observe 只能返回无窗口失败。
            agent = _FakeAgent(Path(raw_dir))  # 新增代码+ComputerUseMcpV2HostAdapter: 创建最小 agent；如果没有这一行，execute_mcp_tool 没有主循环上下文。
            agent.computer_use_controller = ComputerUseController(backend)  # 新增代码+ComputerUseMcpV2HostAdapter: 把成熟 controller 注入 v2 绑定入口；如果没有这一行，observe 不能复用旧窗口状态能力。
            output = execute_mcp_tool(agent, ToolCall(name="mcp__computer-use__observe", arguments={"reason": "unit test observe"}))  # 新增代码+ComputerUseMcpV2HostAdapter: 从模型可见 MCP 名调用 observe；如果没有这一行，测试不会覆盖 v2 观察路径。
            payload = json.loads(output)  # 新增代码+ComputerUseMcpV2HostAdapter: 解析 v2 JSON 文本；如果没有这一行，后续无法检查观察来源。
            self.assertTrue(payload["ok"], payload)  # 新增代码+ComputerUseMcpV2HostAdapter: 断言观察成功；如果没有这一行，类型错误或旧 observe 失败不会被识别。
            self.assertTrue(payload["legacy_adapter_used"], payload)  # 新增代码+ComputerUseMcpV2HostAdapter: 断言 observe 复用内部成熟 adapter；如果没有这一行，观察链可能仍是 v2 空壳。
            self.assertIn("mcp__computer-use__observe", output)  # 修改代码+ComputerUseMcpV2ResidualCleanup：断言结果对模型和 adapter 汇报 v2 observe 名称；如果没有这一行，测试会继续接受旧 computer_observe 模型入口污染。
            self.assertNotIn("TypeError", output)  # 新增代码+ComputerUseMcpV2HostAdapter: 断言不再出现 ComputerUseActionResult 类型转换错误；如果没有这一行，回归会被 JSON 包装掩盖。
    # 新增代码+ComputerUseMcpV2HostAdapter: 函数段结束，test_computer_use_mcp_observe_reuses_controller_observation_adapter 到此结束；如果没有这个边界说明，用户不容易看出 observe 回归测试范围。
# 新增代码+McpAgentBindingRedTest: 函数段结束，ComputerUseMcpAgentSideBindingTests 到此结束；如果没有这个边界说明，用户不容易看出 agent 绑定测试范围。


if __name__ == "__main__":  # 新增代码+McpAgentBindingRedTest: 支持直接运行测试文件；如果没有这一行，手动调试只能通过模块名运行。
    unittest.main()  # 新增代码+McpAgentBindingRedTest: 启动 unittest；如果没有这一行，直接运行文件不会执行测试。
