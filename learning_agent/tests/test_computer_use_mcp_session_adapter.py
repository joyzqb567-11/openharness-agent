from __future__ import annotations  # 新增代码+McpSessionAdapterRedTest: 让类型注解延迟解析；如果没有这一行，前向类型在老解释器或导入顺序变化时可能提前求值失败。

import json  # 新增代码+McpSessionAdapterRedTest: 用来解析 adapter 返回的 JSON 文本；如果没有这一行，测试只能做脆弱的字符串包含判断。
import unittest  # 新增代码+McpSessionAdapterRedTest: 使用标准库测试框架；如果没有这一行，红灯测试无法被 unittest 发现和执行。
from typing import Any  # 新增代码+McpSessionAdapterRedTest: 标注 fake 回调 payload 的通用类型；如果没有这一行，测试意图不够清楚。

from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import ComputerUseMcpSessionAdapter, ComputerUseMcpSessionCallbacks, ComputerUseMcpSessionState, _wrap_legacy_text  # 修改代码+ComputerUseMcpV2ImportCutover: 改从 v2 Windows runtime 导入内部 session adapter；如果没有这一行，删除旧 computer_use 包后 adapter 迁移测试无法运行。


class _FakeControllerResult:  # 新增代码+McpSessionAdapterRedTest: 函数段开始，模拟 Computer Use controller 返回值；如果没有这个类，测试会误碰真实桌面后端。
    def __init__(self, ok: bool = True, message: str = "ok", data: dict[str, Any] | None = None) -> None:  # 新增代码+McpSessionAdapterRedTest: 保存 fake 结果字段；如果没有这一行，旧 agent_tools 无法读取 ok/message/data。
        self.ok = ok  # 新增代码+McpSessionAdapterRedTest: 记录成功状态；如果没有这一行，adapter 无法判断旧动作是否成功。
        self.message = message  # 新增代码+McpSessionAdapterRedTest: 记录返回消息；如果没有这一行，工具结果缺少可读摘要。
        self.data = data or {}  # 新增代码+McpSessionAdapterRedTest: 记录结构化数据；如果没有这一行，截图计数和低层事件计数无法验证。

    def to_text(self, tool_name: str = "computer_action") -> str:  # 新增代码+McpSessionAdapterRedTest: 模拟旧结果文本化入口；如果没有这一行，agent_tools 返回文本时会属性错误。
        return json.dumps({"ok": self.ok, "tool_name": tool_name, "message": self.message, "data": self.data}, ensure_ascii=False, sort_keys=True)  # 新增代码+McpSessionAdapterRedTest: 返回稳定 JSON 文本；如果没有这一行，adapter 无法包裹旧工具输出。
# 新增代码+McpSessionAdapterRedTest: 函数段结束，_FakeControllerResult 到此结束；如果没有这个边界说明，用户不容易看出 fake 结果范围。


class _FakeController:  # 新增代码+McpSessionAdapterRedTest: 函数段开始，模拟 Computer Use controller；如果没有这个类，测试可能触发真实鼠标键盘。
    def __init__(self) -> None:  # 新增代码+McpSessionAdapterRedTest: 初始化 fake controller 状态；如果没有这一行，测试无法记录执行历史。
        self.executed: list[dict[str, Any]] = []  # 新增代码+McpSessionAdapterRedTest: 保存动作执行记录；如果没有这一行，测试无法证明路由到旧 computer_action。
        self.observed: list[dict[str, Any]] = []  # 新增代码+McpSessionAdapterRedTest: 保存观察执行记录；如果没有这一行，测试无法证明路由到旧 computer_observe。

    def status(self) -> dict[str, Any]:  # 新增代码+McpSessionAdapterRedTest: 模拟状态读取；如果没有这一行，status 分支无法在 adapter 中复用旧工具。
        return {"ok": True, "backend": "fake", "real_desktop_touched": False}  # 新增代码+McpSessionAdapterRedTest: 返回安全状态；如果没有这一行，状态工具没有可断言输出。

    def observe(self, arguments: dict[str, Any]) -> _FakeControllerResult:  # 新增代码+McpSessionAdapterRedTest: 模拟只读观察；如果没有这一行，observe 分支会失败。
        self.observed.append(dict(arguments))  # 新增代码+McpSessionAdapterRedTest: 记录观察参数；如果没有这一行，测试无法确认 observe 映射。
        if arguments.get("action") == "get_active_window":  # 新增代码+McpObserveMapping: 模拟真实 adapter 先解析活动安全窗口；如果没有这一行，测试覆盖不到无 window 的 observe 自动补窗。
            return _FakeControllerResult(True, "active", {"window": {"app_id": "fake-app.exe", "window_id": "hwnd:100", "title_preview": "Fake App"}})  # 新增代码+McpObserveMapping: 返回可信窗口引用；如果没有这一行，get_window_state 没有目标。
        if arguments.get("action") == "list_windows":  # 新增代码+McpObserveMapping: 模拟活动窗口缺失时的列表降级路径；如果没有这一行，默认窗口解析的备用路线没有 fake 输出。
            return _FakeControllerResult(True, "windows", {"windows": [{"app_id": "fake-app.exe", "window_id": "hwnd:100", "title_preview": "Fake App"}]})  # 新增代码+McpObserveMapping: 返回安全窗口列表；如果没有这一行，列表降级无法测试。
        return _FakeControllerResult(True, "observed", {"image_result_count": 1, "screenshot_captured": True, "uia_tree_observation": True})  # 修改代码+McpObserveMapping: 返回窗口状态的截图证据；如果没有这一行，旧 observe actionability 可能生成阻塞。

    def execute(self, arguments: dict[str, Any]) -> _FakeControllerResult:  # 新增代码+McpSessionAdapterRedTest: 模拟真实动作执行；如果没有这一行，click/type 等动作无法测试。
        self.executed.append(dict(arguments))  # 新增代码+McpSessionAdapterRedTest: 记录动作参数；如果没有这一行，测试无法确认 MCP 名字映射到 controller action。
        return _FakeControllerResult(True, "executed", {"low_level_event_count": 1, "image_result_count": 1, "real_desktop_touched": True})  # 新增代码+McpSessionAdapterRedTest: 返回动作证据；如果没有这一行，验收事件无法生成稳定 payload。
# 新增代码+McpSessionAdapterRedTest: 函数段结束，_FakeController 到此结束；如果没有这个边界说明，用户不容易看出 fake controller 范围。


class _CallbackRecorder:  # 新增代码+McpSessionAdapterRedTest: 函数段开始，收集 adapter 注入的 agent 回调；如果没有这个类，测试无法证明 agent-side binding 生效。
    def __init__(self) -> None:  # 新增代码+McpSessionAdapterRedTest: 初始化回调记录容器；如果没有这一行，回调结果没有地方保存。
        self.permissions: list[str] = []  # 新增代码+McpSessionAdapterRedTest: 保存权限请求文本；如果没有这一行，测试无法确认动作仍走权限链。
        self.observations: list[tuple[str, dict[str, Any]]] = []  # 新增代码+McpSessionAdapterRedTest: 保存 observation 事件；如果没有这一行，旧状态/观察/动作证据无法断言。
        self.traces: list[tuple[str, dict[str, Any]]] = []  # 新增代码+McpSessionAdapterRedTest: 保存 runtime trace；如果没有这一行，adapter 是否复用旧 trace 链不可见。
        self.images: list[tuple[dict[str, Any], str]] = []  # 新增代码+McpSessionAdapterRedTest: 保存图片 artifact 事件；如果没有这一行，截图证据链无法验证。
        self.acceptance_events: list[tuple[str, dict[str, Any]]] = []  # 新增代码+McpSessionAdapterRedTest: 保存验收事件；如果没有这一行，动作结果是否进入正式验收流无法验证。

    def ask_permission(self, action: str) -> bool:  # 新增代码+McpSessionAdapterRedTest: 模拟用户授权；如果没有这一行，computer_action 会保守拒绝。
        self.permissions.append(action)  # 新增代码+McpSessionAdapterRedTest: 记录权限文本；如果没有这一行，测试无法检查权限链是否被保留。
        return True  # 新增代码+McpSessionAdapterRedTest: 自动同意 fake 动作；如果没有这一行，测试无法进入 controller.execute。

    def record_observation(self, kind: str, payload: dict[str, Any]) -> None:  # 新增代码+McpSessionAdapterRedTest: 模拟 agent observation 回调；如果没有这一行，旧 agent_tools 写日志会失败。
        self.observations.append((kind, payload))  # 新增代码+McpSessionAdapterRedTest: 保存 observation；如果没有这一行，测试无法验证证据链。

    def record_runtime_trace(self, kind: str, payload: dict[str, Any]) -> None:  # 新增代码+McpSessionAdapterRedTest: 模拟 runtime trace 回调；如果没有这一行，旧 agent_tools trace 会失败。
        self.traces.append((kind, payload))  # 新增代码+McpSessionAdapterRedTest: 保存 trace；如果没有这一行，测试无法断言 action/observe 走旧链。

    def record_image_artifacts(self, payload: dict[str, Any], source: str) -> None:  # 新增代码+McpSessionAdapterRedTest: 模拟图片 artifact 回调；如果没有这一行，observe/action 截图登记会失败。
        self.images.append((payload, source))  # 新增代码+McpSessionAdapterRedTest: 保存图片登记；如果没有这一行，测试无法证明截图链路未丢。

    def emit_acceptance_event(self, event_name: str, payload: dict[str, Any]) -> None:  # 新增代码+McpSessionAdapterRedTest: 模拟验收事件输出；如果没有这一行，computer_action 验收链无法被测试。
        self.acceptance_events.append((event_name, payload))  # 新增代码+McpSessionAdapterRedTest: 保存验收事件；如果没有这一行，测试无法证明动作结果可被终端验收消费。
# 新增代码+McpSessionAdapterRedTest: 函数段结束，_CallbackRecorder 到此结束；如果没有这个边界说明，用户不容易看出回调记录范围。


def _make_adapter() -> tuple[ComputerUseMcpSessionAdapter, _FakeController, _CallbackRecorder]:  # 新增代码+McpSessionAdapterRedTest: 函数段开始，统一创建 adapter 测试对象；如果没有这段函数，每个测试会重复组装回调。
    controller = _FakeController()  # 新增代码+McpSessionAdapterRedTest: 创建 fake controller；如果没有这一行，测试会误用真实桌面 controller。
    recorder = _CallbackRecorder()  # 新增代码+McpSessionAdapterRedTest: 创建回调记录器；如果没有这一行，测试无法观察 adapter 侧效应。
    callbacks = ComputerUseMcpSessionCallbacks(ask_permission=recorder.ask_permission, observe_before_action_rejection=lambda _action, _arguments: None, agent_owned_launch_rejection=lambda _action, _arguments: None, completion_signal_for_action=lambda _action, _arguments: None, record_observation=recorder.record_observation, record_runtime_trace=recorder.record_runtime_trace, record_image_artifacts=recorder.record_image_artifacts, emit_acceptance_event=recorder.emit_acceptance_event)  # 新增代码+McpSessionAdapterRedTest: 注入旧 action 所需全部 agent 回调；如果没有这一行，MCP 原子工具仍无法复用成熟门禁和审计链。
    adapter = ComputerUseMcpSessionAdapter(controller=controller, callbacks=callbacks, state=ComputerUseMcpSessionState())  # 新增代码+McpSessionAdapterRedTest: 创建被测 adapter；如果没有这一行，测试没有执行对象。
    return adapter, controller, recorder  # 新增代码+McpSessionAdapterRedTest: 返回三件测试对象；如果没有这一行，测试无法同时断言输出和副作用。
# 新增代码+McpSessionAdapterRedTest: 函数段结束，_make_adapter 到此结束；如果没有这个边界说明，用户不容易看出测试装配边界。


class ComputerUseMcpSessionAdapterTests(unittest.TestCase):  # 新增代码+McpSessionAdapterRedTest: 函数段开始，验证 MCP 原子工具复用旧成熟能力；如果没有这个测试类，adapter 迁移没有红灯保护。
    def test_left_click_uses_legacy_computer_action_callbacks(self) -> None:  # 新增代码+McpSessionAdapterRedTest: 验证点击工具走旧 computer_action；如果没有这个测试，click 可能继续绕开权限和 trace。
        adapter, controller, recorder = _make_adapter()  # 新增代码+McpSessionAdapterRedTest: 创建被测 adapter 和 fake 依赖；如果没有这一行，测试无法运行。
        result = adapter.call_atomic_tool("left_click", {"x": 10, "y": 20, "reason": "unit test click"})  # 新增代码+McpSessionAdapterRedTest: 调用 ClaudeCode 风格原子点击；如果没有这一行，无法验证路由。
        self.assertTrue(result["ok"])  # 新增代码+McpSessionAdapterRedTest: 断言 adapter 认为动作成功；如果没有这一行，失败也可能被误当通过。
        self.assertEqual("mcp__computer-use__computer_batch", result["payload"]["legacy_internal_tool"])  # 修改代码+ComputerUseMcpV2ResidualCleanup：断言 adapter 汇报 v2 batch/原子动作入口；如果没有这一行，测试会继续把旧 computer_action 当成模型可见入口。
        self.assertEqual("click", controller.executed[0]["action"])  # 新增代码+McpSessionAdapterRedTest: 断言左键映射到旧 click action；如果没有这一行，坐标点击语义可能漂移。
        self.assertEqual("left", controller.executed[0]["button"])  # 新增代码+McpSessionAdapterRedTest: 断言左键按钮语义保留；如果没有这一行，左键可能被当普通未知点击。
        self.assertTrue(recorder.permissions)  # 新增代码+McpSessionAdapterRedTest: 断言旧权限链被调用；如果没有这一行，adapter 可能绕过用户确认。
        self.assertIn("computer_action", [kind for kind, _payload in recorder.traces])  # 新增代码+McpSessionAdapterRedTest: 断言旧 trace 被写入；如果没有这一行，agent 主循环无法回看动作证据。
        self.assertIn("computer_action_result", [name for name, _payload in recorder.acceptance_events])  # 新增代码+McpSessionAdapterRedTest: 断言验收事件被发出；如果没有这一行，真实终端验收缺少动作完成证据。

    def test_observe_uses_legacy_computer_observe_callbacks(self) -> None:  # 新增代码+McpSessionAdapterRedTest: 验证 observe 走旧 computer_observe；如果没有这个测试，截图链路可能丢掉 artifact。
        adapter, controller, recorder = _make_adapter()  # 新增代码+McpSessionAdapterRedTest: 创建被测 adapter 和 fake 依赖；如果没有这一行，测试无法运行。
        result = adapter.call_atomic_tool("observe", {"reason": "unit test observe"})  # 新增代码+McpSessionAdapterRedTest: 调用 MCP 观察工具；如果没有这一行，无法验证 observe 映射。
        self.assertTrue(result["ok"])  # 新增代码+McpSessionAdapterRedTest: 断言观察成功；如果没有这一行，失败结果可能被忽略。
        self.assertEqual("mcp__computer-use__observe", result["payload"]["legacy_internal_tool"])  # 修改代码+ComputerUseMcpV2ResidualCleanup：断言 adapter 汇报 v2 observe 入口；如果没有这一行，测试会继续把旧 computer_observe 当成模型可见入口。
        self.assertEqual("get_active_window", controller.observed[0]["action"])  # 修改代码+McpObserveMapping: 断言 adapter 先解析活动窗口；如果没有这一行，模型无 window 的 observe 可能直接失败。
        self.assertEqual("get_window_state", controller.observed[1]["action"])  # 修改代码+McpObserveMapping: 断言 observe 最终走旧 controller 支持的窗口状态观察；如果没有这一行，旧 screenshot 错配会回归。
        self.assertEqual("fake-app.exe", controller.observed[1]["window"]["app_id"])  # 新增代码+McpObserveMapping: 断言自动解析的窗口传入 get_window_state；如果没有这一行，截图观察可能仍缺目标。
        self.assertIn("computer_observe", [kind for kind, _payload in recorder.traces])  # 新增代码+McpSessionAdapterRedTest: 断言旧 observe trace 被写入；如果没有这一行，观察证据不可审计。
        self.assertEqual("computer_observe", recorder.images[0][1])  # 新增代码+McpSessionAdapterRedTest: 断言截图 artifact 来源保留；如果没有这一行，图片链路可能掉线。

    def test_observed_window_is_reused_by_following_left_click(self) -> None:  # 新增代码+McpObservedWindowRedTest: 函数段开始，验证 observe 后 click 自动复用可信窗口；如果没有这个测试，模型必须手动传旧 window 才能动作。
        adapter, controller, _recorder = _make_adapter()  # 新增代码+McpObservedWindowRedTest: 创建同一个 session adapter；如果没有这一行，observe 和 click 不能共享状态。
        observe_result = adapter.call_atomic_tool("observe", {"reason": "unit test observe before click"})  # 新增代码+McpObservedWindowRedTest: 先执行观察写入窗口上下文；如果没有这一行，后续 click 没有可复用目标。
        self.assertTrue(observe_result["ok"], observe_result)  # 新增代码+McpObservedWindowRedTest: 确认观察成功；如果没有这一行，观察失败时 click 注入窗口没有意义。
        click_result = adapter.call_atomic_tool("left_click", {"x": 10, "y": 20, "reason": "unit test click after observe"})  # 新增代码+McpObservedWindowRedTest: 再执行不带 window 的左键点击；如果没有这一行，测试不能覆盖真实终端失败路径。
        self.assertTrue(click_result["ok"], click_result)  # 新增代码+McpObservedWindowRedTest: 确认 click 仍能成功；如果没有这一行，动作失败可能被后续断言掩盖。
        self.assertEqual("fake-app.exe", controller.executed[0]["window"]["app_id"])  # 新增代码+McpObservedWindowRedTest: 断言动作参数自动带上 observe 得到的窗口；如果没有这一行，Phase 30 缺 window 回归不会被发现。
        self.assertEqual("hwnd:100", controller.executed[0]["window"]["window_id"])  # 新增代码+McpObservedWindowRedTest: 断言窗口身份保持稳定；如果没有这一行，可能只注入了不完整目标。
    # 新增代码+McpObservedWindowRedTest: 函数段结束，test_observed_window_is_reused_by_following_left_click 到此结束；如果没有这个边界说明，用户不容易看出窗口复用测试范围。

    def test_left_click_drag_maps_to_drag_path(self) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，验证 ClaudeCode 风格拖拽工具会映射到旧 drag_path；如果没有这个测试，拖拽可能只在表面 schema 存在却不能复用 controller。
        adapter, controller, _recorder = _make_adapter()  # 新增代码+ClaudeCodeParity: 创建被测 adapter 和 fake controller；如果没有这一行，测试没有可观察的执行记录。
        adapter.state.last_observed_window = {"app_id": "fake-app.exe", "window_id": "hwnd:100"}  # 新增代码+ClaudeCodeParity: 模拟已经观察到可信窗口；如果没有这一行，测试无法证明拖拽动作会复用 session 窗口。
        result = adapter.call_atomic_tool("left_click_drag", {"start_x": 1, "start_y": 2, "end_x": 9, "end_y": 10, "duration_seconds": 0.2})  # 新增代码+ClaudeCodeParity: 调用模型可见的左键拖拽原子工具；如果没有这一行，映射行为不会被真正执行。
        self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodeParity: 断言 adapter 返回成功；如果没有这一行，unsupported 或执行失败可能被后续字段断言遮住。
        self.assertEqual("drag_path", controller.executed[0]["action"])  # 新增代码+ClaudeCodeParity: 断言工具名被转换成 controller 支持的 drag_path；如果没有这一行，旧 controller 可能收到不认识的 left_click_drag。
        self.assertEqual([{"x": 1, "y": 2}, {"x": 9, "y": 10}], controller.executed[0]["points"])  # 新增代码+ClaudeCodeParity: 断言起点终点被转换为路径点数组；如果没有这一行，拖拽坐标可能丢失或顺序反了。
        self.assertEqual({"app_id": "fake-app.exe", "window_id": "hwnd:100"}, controller.executed[0]["window"])  # 新增代码+ClaudeCodeParity: 断言拖拽复用了最近观察窗口；如果没有这一行，真实 full 模式可能因缺 window 被门禁拒绝。
    # 新增代码+ClaudeCodeParity: 函数段结束，test_left_click_drag_maps_to_drag_path 到此结束；如果没有这个边界说明，用户不容易看出拖拽映射测试范围。

    def test_new_mouse_tools_map_to_controller_actions(self) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，验证新增 parity 鼠标和 hold_key 工具映射到旧 controller action；如果没有这个测试，Task 1 暴露的工具可能继续返回 unsupported。
        adapter, controller, _recorder = _make_adapter()  # 新增代码+ClaudeCodeParity: 创建同一个 adapter 会话；如果没有这一行，多工具顺序和窗口复用无法一起验证。
        adapter.state.last_observed_window = {"app_id": "fake-app.exe", "window_id": "hwnd:100"}  # 新增代码+ClaudeCodeParity: 模拟 observe 后的可信窗口状态；如果没有这一行，测试无法确认新动作加入窗口复用集合。
        results = [  # 新增代码+ClaudeCodeParity: 收集每个工具调用结果；如果没有这一行，后续无法统一断言所有新工具都成功。
            adapter.call_atomic_tool("middle_click", {"x": 3, "y": 4}),  # 新增代码+ClaudeCodeParity: 调用中键点击；如果没有这一行，middle_click 的 button=middle 兼容映射不会被覆盖。
            adapter.call_atomic_tool("triple_click", {"x": 3, "y": 4}),  # 新增代码+ClaudeCodeParity: 调用三击；如果没有这一行，unsupported 分支移除与否无法被测试发现。
            adapter.call_atomic_tool("left_mouse_down", {"x": 3, "y": 4}),  # 新增代码+ClaudeCodeParity: 调用左键按下；如果没有这一行，mouse_down 映射可能继续缺失。
            adapter.call_atomic_tool("left_mouse_up", {"reason": "unit test release"}),  # 新增代码+ClaudeCodeParity: 调用左键释放且不传坐标；如果没有这一行，释放动作可能错误要求 x/y。
            adapter.call_atomic_tool("hold_key", {"keys": ["shift"], "duration_seconds": 0.1}),  # 新增代码+ClaudeCodeParity: 调用 required keys 数组形态的 hold_key；如果没有这一行，Task 1 新 schema 和 adapter 可能不一致。
        ]  # 新增代码+ClaudeCodeParity: 结束工具调用列表；如果没有这一行，Python 列表语法不完整。
        self.assertTrue(all(result["ok"] for result in results), results)  # 新增代码+ClaudeCodeParity: 断言所有新增工具都返回成功；如果没有这一行，单个 unsupported 可能被遗漏。
        self.assertEqual(["click", "triple_click", "mouse_down", "mouse_up", "hold_key"], [item["action"] for item in controller.executed])  # 新增代码+ClaudeCodeParity: 断言每个工具按顺序映射到 controller action；如果没有这一行，工具名和动作名漂移不会被发现。
        self.assertEqual("middle", controller.executed[0]["button"])  # 新增代码+ClaudeCodeParity: 断言 middle_click 固定使用中键；如果没有这一行，中键可能被默认左键吞掉。
        self.assertEqual("left", controller.executed[1]["button"])  # 新增代码+ClaudeCodeParity: 断言 triple_click 使用左键；如果没有这一行，三击按钮语义可能缺失。
        self.assertEqual("left", controller.executed[2]["button"])  # 新增代码+ClaudeCodeParity: 断言 mouse_down 使用左键；如果没有这一行，按下事件可能没有按钮字段。
        self.assertEqual("left", controller.executed[3]["button"])  # 新增代码+ClaudeCodeParity: 断言 mouse_up 使用左键；如果没有这一行，释放事件可能不知道释放哪个按钮。
        self.assertEqual(["shift"], controller.executed[4]["keys"])  # 新增代码+ClaudeCodeParity: 断言 hold_key 保留 keys 数组；如果没有这一行，ClaudeCode parity schema 的数组字段可能丢失。
        self.assertEqual("shift", controller.executed[4]["key"])  # 新增代码+ClaudeCodeParity: 断言 hold_key 也提供兼容 key 字符串；如果没有这一行，旧 controller 只读 key 时可能失效。
        self.assertTrue(all(item.get("window") == {"app_id": "fake-app.exe", "window_id": "hwnd:100"} for item in controller.executed))  # 新增代码+ClaudeCodeParity: 断言每个可复用动作都带上最近观察窗口；如果没有这一行，新动作可能在真实 full 模式被缺 window 门禁拦住。
    # 新增代码+ClaudeCodeParity: 函数段结束，test_new_mouse_tools_map_to_controller_actions 到此结束；如果没有这个边界说明，用户不容易看出新增工具映射测试范围。

    def test_legacy_gate_rejection_text_is_wrapped_as_failure(self) -> None:  # 新增代码+McpObserveMapping: 验证旧门禁普通文本会被 MCP 包装为失败；如果没有这个测试，observe_before_action_required 可能再次被误标 ok=true。
        result = _wrap_legacy_text("mouse_move", "computer_action", "Computer Use full 模式已拒绝盲目桌面动作：observe_before_action_required")  # 新增代码+McpObserveMapping: 构造真实 full 模式盲动拒绝文本；如果没有这一行，测试没有失败文本输入。
        self.assertFalse(result["ok"])  # 新增代码+McpObserveMapping: 断言包装结果失败；如果没有这一行，模型可能把被拒绝动作当成功。
        self.assertEqual("legacy_computer_use_rejected", result["error_class"])  # 新增代码+McpObserveMapping: 断言失败类别稳定；如果没有这一行，模型无法按错误类型恢复。

    def test_request_access_uses_legacy_request_access_callbacks(self) -> None:  # 新增代码+McpSessionAdapterRedTest: 验证授权申请走旧 request_access；如果没有这个测试，MCP 申请可能和旧安全提示分裂。
        adapter, _controller, recorder = _make_adapter()  # 新增代码+McpSessionAdapterRedTest: 创建被测 adapter 和回调记录器；如果没有这一行，测试没有执行环境。
        result = adapter.call_atomic_tool("request_access", {"applications": ["notepad"], "reason": "unit test access"})  # 新增代码+McpSessionAdapterRedTest: 调用 MCP 授权申请；如果没有这一行，无法验证参数归一化。
        self.assertTrue(result["ok"])  # 新增代码+McpSessionAdapterRedTest: 断言申请工具返回成功报告；如果没有这一行，错误报告可能被误放过。
        self.assertEqual("agent-side adapter", result["payload"]["execution_route"])  # 新增代码+McpSessionAdapterEvidence: 断言工具结果带 agent-side adapter 路由证据；如果没有这一行，真实终端 debug log 可能再次缺少绑定证明。
        self.assertEqual("request_access", result["payload"]["legacy_internal_tool"])  # 新增代码+McpSessionAdapterRedTest: 断言复用旧申请入口；如果没有这一行，adapter 可能使用旁路纯函数。
        self.assertEqual(["notepad"], result["payload"]["legacy_payload"]["requested_apps"])  # 新增代码+McpSessionAdapterRedTest: 断言 applications 已转成 requested_apps；如果没有这一行，申请目标会丢失。
        self.assertIn("computer_request_access", [kind for kind, _payload in recorder.traces])  # 新增代码+McpSessionAdapterRedTest: 断言申请 trace 被写入；如果没有这一行，授权申请无运行证据。
        self.assertIn("computer_use_request_access", [kind for kind, _payload in recorder.observations])  # 新增代码+McpSessionAdapterRedTest: 断言申请 observation 被写入；如果没有这一行，调试时看不到模型申请了什么。

    def test_batch_stops_before_second_step_when_first_step_is_shell_rejected(self) -> None:  # 新增代码+McpSessionAdapterRedTest: 验证 batch 失败停止且不触碰 controller；如果没有这个测试，危险参数可能在批量步骤里漏过。
        adapter, controller, _recorder = _make_adapter()  # 新增代码+McpSessionAdapterRedTest: 创建被测 adapter 和 fake controller；如果没有这一行，测试没有执行环境。
        result = adapter.call_atomic_tool("computer_batch", {"steps": [{"tool_name": "left_click", "arguments": {"x": 1, "y": 2, "command": "whoami"}}, {"tool_name": "type", "arguments": {"text": "should not run"}}], "stop_on_error": True})  # 新增代码+McpSessionAdapterRedTest: 构造第一步带 command 的危险批量；如果没有这一行，无法证明 shell 面硬拒绝。
        self.assertFalse(result["ok"])  # 新增代码+McpSessionAdapterRedTest: 断言批量整体失败；如果没有这一行，危险拒绝可能被包装成成功。
        self.assertEqual("shell_argument_forbidden", result["payload"]["results"][0]["error_class"])  # 新增代码+McpSessionAdapterRedTest: 断言第一步被 shell 参数拒绝；如果没有这一行，拒绝原因不可见。
        self.assertEqual(1, result["payload"]["step_count"])  # 新增代码+McpSessionAdapterRedTest: 断言 stop_on_error 阻止第二步；如果没有这一行，失败后仍可能继续输入文字。
        self.assertEqual([], controller.executed)  # 新增代码+McpSessionAdapterRedTest: 断言危险步骤没有触碰 controller；如果没有这一行，测试无法证明真实桌面安全。
# 新增代码+McpSessionAdapterRedTest: 函数段结束，ComputerUseMcpSessionAdapterTests 到此结束；如果没有这个边界说明，用户不容易看出 adapter 红灯测试范围。


if __name__ == "__main__":  # 新增代码+McpSessionAdapterRedTest: 支持单文件直接运行；如果没有这一行，开发者只能通过模块方式启动测试。
    unittest.main()  # 新增代码+McpSessionAdapterRedTest: 启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
