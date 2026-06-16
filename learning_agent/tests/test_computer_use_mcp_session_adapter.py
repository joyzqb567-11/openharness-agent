from __future__ import annotations  # 新增代码+McpSessionAdapterRedTest: 让类型注解延迟解析；如果没有这一行，前向类型在老解释器或导入顺序变化时可能提前求值失败。

import json  # 新增代码+McpSessionAdapterRedTest: 用来解析 adapter 返回的 JSON 文本；如果没有这一行，测试只能做脆弱的字符串包含判断。
import tempfile  # 新增代码+ClaudeCodeZoom: 用临时目录保存可裁剪的测试截图；如果没有这一行，zoom 红灯测试会污染项目目录或依赖固定路径。
import unittest  # 新增代码+McpSessionAdapterRedTest: 使用标准库测试框架；如果没有这一行，红灯测试无法被 unittest 发现和执行。
from pathlib import Path  # 新增代码+ClaudeCodeZoom: 用 Path 稳定检查 zoom 生成的图片 artifact；如果没有这一行，测试只能用脆弱字符串处理文件路径。
from typing import Any  # 新增代码+McpSessionAdapterRedTest: 标注 fake 回调 payload 的通用类型；如果没有这一行，测试意图不够清楚。

from PIL import Image  # 新增代码+ClaudeCodeZoom: 生成并检查真实 PNG 像素尺寸；如果没有这一行，测试无法证明 zoom 真的裁剪了截图。
from learning_agent.computer_use_mcp_v2.windows_runtime.action_gates import COMPUTER_USE_COMPLETION_CHANGE_ACTIONS, COMPUTER_USE_MOUSE_KEYBOARD_ACTIONS, computer_use_full_mode_requires_agent_owned_launch, computer_use_full_mode_requires_model_visible_observation  # 新增代码+ClaudeCodeParity: 导入 full 模式门禁集合和判断函数；如果没有这一行，测试无法证明新增 parity 动作会被盲动和完成门管住。
from learning_agent.computer_use_mcp_v2.windows_runtime.action_policy import COORDINATE_ACTIONS, prepare_action_arguments  # 新增代码+ClaudeCodeParity: 导入坐标动作集合和策略入口；如果没有这一行，测试无法证明新增鼠标动作会进入坐标转换证据链。
from learning_agent.computer_use_mcp_v2.windows_runtime.coordinates import build_screenshot_coordinate_mapping  # 新增代码+ClaudeCodeZoom: 复用正式截图坐标映射合同；如果没有这一行，测试会手写一份容易漂移的 scale 数据。
from learning_agent.computer_use_mcp_v2.windows_runtime.controller import ComputerUseController, MemoryComputerUseBackend  # 新增代码+ClaudeCodeParity: 导入真实 v2 controller 和内存后端；如果没有这一行，测试只能覆盖 fake controller 而漏掉真实 allowed_actions 门禁。
from learning_agent.computer_use_mcp_v2.windows_runtime.image_messages import extract_computer_use_image_specs_from_tool_output  # 新增代码+ClaudeCodeZoom: 验证 zoom 结果能被模型图片回灌解析器读到；如果没有这一行，测试只能检查 JSON 而不能证明模型可见。
from learning_agent.computer_use_mcp_v2.windows_runtime.mcp_session_adapter import ComputerUseMcpSessionAdapter, ComputerUseMcpSessionCallbacks, ComputerUseMcpSessionState, _wrap_legacy_text  # 修改代码+ClaudeCodeParity: 改从 v2 Windows runtime 导入内部 session adapter；如果没有这一行，删除旧 computer_use 包后 adapter 迁移测试无法运行。


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

    def test_zoom_returns_cropped_model_visible_image_result(self) -> None:  # 新增代码+ClaudeCodeZoom: 函数段开始，验证 zoom 是只读观察并返回裁剪后的模型可见图片；如果没有这个测试，zoom 可能只返回全屏截图或误走动作链。
        with tempfile.TemporaryDirectory() as temp_dir:  # 新增代码+ClaudeCodeZoom: 为测试截图创建隔离目录；如果没有这一行，生成的 artifact 可能残留在仓库里。
            source_path = Path(temp_dir) / "zoom-source.png"  # 新增代码+ClaudeCodeZoom: 定义原始全窗口截图路径；如果没有这一行，后续无法比较 zoom 是否生成了新裁剪图。
            Image.new("RGB", (4, 4), (255, 0, 0)).save(source_path)  # 新增代码+ClaudeCodeZoom: 写入 4x4 有效 PNG；如果没有这一行，生产裁剪逻辑无法打开图片验证尺寸。
            trusted_window = {"app_id": "fake-app.exe", "window_id": "hwnd:zoom", "title_preview": "Zoom App", "rect": {"left": 10, "top": 20, "right": 12, "bottom": 22}}  # 新增代码+ClaudeCodeZoom: 构造 2x2 逻辑窗口；如果没有这一行，scale=2 的坐标映射没有窗口来源。
            mapping = build_screenshot_coordinate_mapping(trusted_window, 4, 4)  # 新增代码+ClaudeCodeZoom: 生成逻辑坐标到截图像素的 2 倍映射；如果没有这一行，zoom 裁剪无法证明复用正式 scale 合同。
            image_result = {"type": "image_result", "model": "phase41_model_visible_image_results", "source": "window_state", "artifact_path": str(source_path), "image_path": str(source_path), "mime_type": "image/png", "width": 4, "height": 4, "sensitive_text_included": False, "text_redacted": True, "screenshot_coordinate_model": mapping["model"], "screenshot_coordinate_mapping": mapping, "marker": "phase41_windows_image_results"}  # 修改代码+ClaudeCodeZoom: 使用正式 mapping.model 作为图片块坐标模型名；如果没有这一行，测试会错读不存在字段而不是验证 zoom 生产缺口。
            state = {"window": trusted_window, "screenshot_captured": True, "screenshot_path": str(source_path), "screenshot_width": 4, "screenshot_height": 4, "screenshot_format": "png", "screenshot_coordinate_model": mapping["model"], "screenshot_coordinate_mapping": mapping, "image_results": [image_result], "image_result_count": 1}  # 修改代码+ClaudeCodeZoom: 使用正式 mapping.model 放入窗口状态；如果没有这一行，测试输入会偏离生产坐标合同。
            backend = MemoryComputerUseBackend(windows=[trusted_window], window_states={("fake-app.exe", "hwnd:zoom"): state})  # 新增代码+ClaudeCodeZoom: 创建不会触碰真实桌面的可观察后端；如果没有这一行，测试可能误碰真实 Windows 桌面。
            recorder = _CallbackRecorder()  # 新增代码+ClaudeCodeZoom: 创建回调记录器；如果没有这一行，测试无法确认图片 artifact 是否登记。
            callbacks = ComputerUseMcpSessionCallbacks(ask_permission=recorder.ask_permission, observe_before_action_rejection=lambda _action, _arguments: None, agent_owned_launch_rejection=lambda _action, _arguments: None, completion_signal_for_action=lambda _action, _arguments: None, record_observation=recorder.record_observation, record_runtime_trace=recorder.record_runtime_trace, record_image_artifacts=recorder.record_image_artifacts, emit_acceptance_event=recorder.emit_acceptance_event)  # 新增代码+ClaudeCodeZoom: 注入 adapter 所需回调；如果没有这一行，旧 observe 链无法记录截图和 trace。
            adapter = ComputerUseMcpSessionAdapter(controller=ComputerUseController(backend=backend), callbacks=callbacks, state=ComputerUseMcpSessionState())  # 新增代码+ClaudeCodeZoom: 用真实 controller 包住内存后端；如果没有这一行，测试不能覆盖真实 adapter 到 controller 路径。
            result = adapter.call_atomic_tool("zoom", {"x": 10, "y": 20, "width": 1, "height": 1, "window": trusted_window, "reason": "unit test zoom"})  # 修改代码+ClaudeCodeZoom: 请求窗口左上 1x1 逻辑区域并显式带入可信窗口 rect；如果没有这一行，Memory 后端精简窗口引用会让测试偏离裁剪目标。
            self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodeZoom: 断言 zoom 工具成功；如果没有这一行，后续字段断言可能掩盖 observe 失败。
            self.assertEqual([], backend.actions)  # 新增代码+ClaudeCodeZoom: 断言 zoom 没有执行任何桌面动作；如果没有这一行，read_only 工具可能悄悄触碰鼠标键盘。
            self.assertEqual(1, result["payload"].get("zoom_image_result_count", 0), result)  # 新增代码+ClaudeCodeZoom: 断言 adapter 明确生成一张 zoom 图片；如果没有这一行，旧全图结果可能被误判对齐。
            zoom_results = result["payload"].get("zoom_image_results", [])  # 新增代码+ClaudeCodeZoom: 读取 zoom 专属图片块；如果没有这一行，后续无法检查裁剪 artifact。
            self.assertEqual(1, len(zoom_results), result)  # 新增代码+ClaudeCodeZoom: 断言只有一张裁剪图；如果没有这一行，多图或空图都可能混过。
            zoom_path = Path(str(zoom_results[0]["artifact_path"]))  # 新增代码+ClaudeCodeZoom: 转成 Path 方便检查文件；如果没有这一行，路径存在性只能靠字符串猜。
            self.assertNotEqual(source_path, zoom_path)  # 新增代码+ClaudeCodeZoom: 断言 zoom 生成新裁剪图而不是复用全图；如果没有这一行，模型仍可能只看到整张截图。
            self.assertTrue(zoom_path.is_file(), zoom_path)  # 新增代码+ClaudeCodeZoom: 断言裁剪图真实落盘；如果没有这一行，image_result 可能指向不存在路径。
            with Image.open(zoom_path) as zoom_image:  # 新增代码+ClaudeCodeZoom: 打开裁剪图检查像素尺寸；如果没有这一行，无法证明 scale 后的 crop 真执行。
                self.assertEqual((2, 2), zoom_image.size)  # 新增代码+ClaudeCodeZoom: 断言 1x1 逻辑区域按 scale=2 变成 2x2 像素；如果没有这一行，坐标映射可能没被使用。
            specs = extract_computer_use_image_specs_from_tool_output(result["text"])  # 新增代码+ClaudeCodeZoom: 从最终工具文本解析模型会回灌的图片路径；如果没有这一行，JSON 有图不代表模型能看见。
            self.assertEqual(str(zoom_path), specs[0]["artifact_path"])  # 新增代码+ClaudeCodeZoom: 断言模型回灌的是裁剪图而不是原始全图；如果没有这一行，zoom 语义可能只停留在 payload。
    # 新增代码+ClaudeCodeZoom: 函数段结束，test_zoom_returns_cropped_model_visible_image_result 到此结束；如果没有这个边界说明，用户不容易看出 zoom 图片回归测试范围。

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
            adapter.call_atomic_tool("left_mouse_up", {"x": 3, "y": 4, "reason": "unit test release"}),  # 修改代码+ClaudeCodeParity: 按 Task 1 schema 用 required x/y 调用左键释放；如果没有这一行，adapter 可能继续丢掉释放坐标证据。
            adapter.call_atomic_tool("hold_key", {"keys": ["shift"], "duration_seconds": 0.1}),  # 新增代码+ClaudeCodeParity: 调用 required keys 数组形态的 hold_key；如果没有这一行，Task 1 新 schema 和 adapter 可能不一致。
        ]  # 新增代码+ClaudeCodeParity: 结束工具调用列表；如果没有这一行，Python 列表语法不完整。
        self.assertTrue(all(result["ok"] for result in results), results)  # 新增代码+ClaudeCodeParity: 断言所有新增工具都返回成功；如果没有这一行，单个 unsupported 可能被遗漏。
        self.assertEqual(["click", "triple_click", "mouse_down", "mouse_up", "hold_key"], [item["action"] for item in controller.executed])  # 新增代码+ClaudeCodeParity: 断言每个工具按顺序映射到 controller action；如果没有这一行，工具名和动作名漂移不会被发现。
        self.assertEqual("middle", controller.executed[0]["button"])  # 新增代码+ClaudeCodeParity: 断言 middle_click 固定使用中键；如果没有这一行，中键可能被默认左键吞掉。
        self.assertEqual("left", controller.executed[1]["button"])  # 新增代码+ClaudeCodeParity: 断言 triple_click 使用左键；如果没有这一行，三击按钮语义可能缺失。
        self.assertEqual("left", controller.executed[2]["button"])  # 新增代码+ClaudeCodeParity: 断言 mouse_down 使用左键；如果没有这一行，按下事件可能没有按钮字段。
        self.assertEqual("left", controller.executed[3]["button"])  # 新增代码+ClaudeCodeParity: 断言 mouse_up 使用左键；如果没有这一行，释放事件可能不知道释放哪个按钮。
        self.assertEqual(3, controller.executed[3]["x"])  # 新增代码+ClaudeCodeParity: 断言 mouse_up 保留 schema 要求的 x 坐标；如果没有这一行，坐标证据和未来 move-before-up 实现会缺入口。
        self.assertEqual(4, controller.executed[3]["y"])  # 新增代码+ClaudeCodeParity: 断言 mouse_up 保留 schema 要求的 y 坐标；如果没有这一行，坐标证据和未来 move-before-up 实现会缺入口。
        self.assertEqual(["shift"], controller.executed[4]["keys"])  # 新增代码+ClaudeCodeParity: 断言 hold_key 保留 keys 数组；如果没有这一行，ClaudeCode parity schema 的数组字段可能丢失。
        self.assertEqual("shift", controller.executed[4]["key"])  # 新增代码+ClaudeCodeParity: 断言 hold_key 也提供兼容 key 字符串；如果没有这一行，旧 controller 只读 key 时可能失效。
        self.assertTrue(all(item.get("window") == {"app_id": "fake-app.exe", "window_id": "hwnd:100"} for item in controller.executed))  # 新增代码+ClaudeCodeParity: 断言每个可复用动作都带上最近观察窗口；如果没有这一行，新动作可能在真实 full 模式被缺 window 门禁拦住。
    # 新增代码+ClaudeCodeParity: 函数段结束，test_new_mouse_tools_map_to_controller_actions 到此结束；如果没有这个边界说明，用户不容易看出新增工具映射测试范围。

    def test_new_session_actions_pass_through_real_v2_controller(self) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，验证 adapter 到真实 v2 controller 的端到端路径；如果没有这个测试，fake controller 通过也可能在 allowed_actions 处失败。
        trusted_window = {"app_id": "fake-app.exe", "window_id": "hwnd:100", "title_preview": "Fake App", "rect": {"left": 100, "top": 200, "right": 500, "bottom": 600}}  # 新增代码+ClaudeCodeParity: 准备带 rect 的可信内存窗口；如果没有这一行，controller 无法校验窗口或生成坐标转换证据。
        backend = MemoryComputerUseBackend(windows=[trusted_window])  # 新增代码+ClaudeCodeParity: 创建不会触碰真实桌面的 v2 内存后端；如果没有这一行，测试可能误用真实 Windows 后端。
        recorder = _CallbackRecorder()  # 新增代码+ClaudeCodeParity: 创建 adapter 回调记录器；如果没有这一行，真实 agent_tools 权限和 trace 回调没有实现。
        callbacks = ComputerUseMcpSessionCallbacks(ask_permission=recorder.ask_permission, observe_before_action_rejection=lambda _action, _arguments: None, agent_owned_launch_rejection=lambda _action, _arguments: None, completion_signal_for_action=lambda _action, _arguments: None, record_observation=recorder.record_observation, record_runtime_trace=recorder.record_runtime_trace, record_image_artifacts=recorder.record_image_artifacts, emit_acceptance_event=recorder.emit_acceptance_event)  # 新增代码+ClaudeCodeParity: 注入真实 v2 action path 所需回调；如果没有这一行，adapter 端到端调用会在 agent_tools 层缺依赖。
        adapter = ComputerUseMcpSessionAdapter(controller=ComputerUseController(backend=backend), callbacks=callbacks, state=ComputerUseMcpSessionState())  # 新增代码+ClaudeCodeParity: 用真实 v2 controller 创建 adapter；如果没有这一行，测试仍只能证明 fake controller 行为。
        adapter.state.last_observed_window = dict(trusted_window)  # 新增代码+ClaudeCodeParity: 模拟 observe 后保存的窗口上下文；如果没有这一行，新动作会缺少真实 controller 要求的可信 window。
        results = [  # 新增代码+ClaudeCodeParity: 顺序收集新增 controller action 的 adapter 调用结果；如果没有这一行，无法统一断言不再被 unsupported/allowed_actions 拒绝。
            adapter.call_atomic_tool("triple_click", {"x": 3, "y": 4}),  # 新增代码+ClaudeCodeParity: 通过 adapter 调三击；如果没有这一行，triple_click 的真实 controller allowlist 缺口不会被发现。
            adapter.call_atomic_tool("left_mouse_down", {"x": 5, "y": 6}),  # 新增代码+ClaudeCodeParity: 通过 adapter 调左键按下；如果没有这一行，mouse_down 的真实 controller allowlist 缺口不会被发现。
            adapter.call_atomic_tool("left_mouse_up", {"x": 7, "y": 8}),  # 新增代码+ClaudeCodeParity: 通过 adapter 调左键释放并带坐标；如果没有这一行，mouse_up 坐标保留和真实 controller allowlist 缺口不会被发现。
            adapter.call_atomic_tool("hold_key", {"keys": ["shift"], "duration_seconds": 0.1}),  # 新增代码+ClaudeCodeParity: 通过 adapter 调按住按键；如果没有这一行，hold_key 的真实 controller allowlist 缺口不会被发现。
        ]  # 新增代码+ClaudeCodeParity: 结束端到端调用列表；如果没有这一行，Python 列表语法不完整。
        self.assertTrue(all(result["ok"] for result in results), results)  # 新增代码+ClaudeCodeParity: 断言所有新增动作都通过真实 v2 controller；如果没有这一行，allowed_actions 拒绝仍可能漏进生产路径。
        self.assertEqual(["triple_click", "mouse_down", "mouse_up", "hold_key"], [item["action"] for item in backend.actions])  # 新增代码+ClaudeCodeParity: 断言内存后端收到 controller action 名；如果没有这一行，adapter 可能只返回成功但没有派发到真实后端。
        self.assertEqual(107, backend.actions[2]["x"])  # 新增代码+ClaudeCodeParity: 断言 mouse_up x 经过窗口相对坐标转换；如果没有这一行，释放动作坐标证据可能仍为空或未转换。
        self.assertEqual(208, backend.actions[2]["y"])  # 新增代码+ClaudeCodeParity: 断言 mouse_up y 经过窗口相对坐标转换；如果没有这一行，释放动作坐标证据可能仍为空或未转换。
    # 新增代码+ClaudeCodeParity: 函数段结束，test_new_session_actions_pass_through_real_v2_controller 到此结束；如果没有这个边界说明，用户不容易看出端到端 controller 回归范围。

    def test_new_session_actions_are_in_policy_and_gate_sets(self) -> None:  # 新增代码+ClaudeCodeParity: 函数段开始，验证新增 parity 动作进入坐标策略和 full 模式门禁集合；如果没有这个测试，安全门禁和证据链会再次与 adapter 映射漂移。
        self.assertTrue({"triple_click", "mouse_down", "mouse_up"}.issubset(COORDINATE_ACTIONS))  # 新增代码+ClaudeCodeParity: 断言坐标型新鼠标动作进入 action_policy；如果没有这一行，坐标转换和证据 envelope 会漏掉它们。
        self.assertTrue({"triple_click", "mouse_down", "mouse_up", "hold_key"}.issubset(COMPUTER_USE_MOUSE_KEYBOARD_ACTIONS))  # 新增代码+ClaudeCodeParity: 断言新动作进入盲动/先启动门禁集合；如果没有这一行，full 模式可能允许它们绕过观察和 agent-owned 目标要求。
        self.assertTrue({"triple_click", "mouse_down", "mouse_up", "hold_key"}.issubset(COMPUTER_USE_COMPLETION_CHANGE_ACTIONS))  # 新增代码+ClaudeCodeParity: 断言新动作进入完成门改变类集合；如果没有这一行，任务已该收束时仍可能继续三击、按下、释放或按住键。
        context = {"active": True, "requires_gui_actions": True, "target_app_hint": "fake-app"}  # 新增代码+ClaudeCodeParity: 构造 full GUI 本机应用上下文；如果没有这一行，门禁函数不会进入真实 full 模式判断分支。
        self.assertTrue(computer_use_full_mode_requires_model_visible_observation("mouse_down", context))  # 新增代码+ClaudeCodeParity: 断言 mouse_down 前必须先有模型可见观察；如果没有这一行，盲按鼠标可能绕过观察门。
        self.assertTrue(computer_use_full_mode_requires_agent_owned_launch("hold_key", context))  # 新增代码+ClaudeCodeParity: 断言 hold_key 前必须先绑定 agent-owned 目标；如果没有这一行，按键动作可能打到用户旧窗口。
        prepared = prepare_action_arguments("mouse_up", {"window": {"app_id": "fake-app.exe", "window_id": "hwnd:100", "rect": {"left": 10, "top": 20, "right": 100, "bottom": 120}}, "x": 3, "y": 4})  # 新增代码+ClaudeCodeParity: 准备一次 mouse_up 坐标转换；如果没有这一行，测试无法证明释放动作实际进入坐标策略。
        self.assertEqual("window_relative", prepared["coordinate_used"]["source"])  # 新增代码+ClaudeCodeParity: 断言 mouse_up 使用窗口相对坐标来源；如果没有这一行，策略可能仍把释放动作当无坐标动作。
    # 新增代码+ClaudeCodeParity: 函数段结束，test_new_session_actions_are_in_policy_and_gate_sets 到此结束；如果没有这个边界说明，用户不容易看出策略和门禁测试范围。

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
