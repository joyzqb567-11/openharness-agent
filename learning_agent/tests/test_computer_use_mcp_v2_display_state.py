from __future__ import annotations  # 新增代码+ClaudeCodeDisplayParityTests：延迟类型注解解析；如果没有这行代码，测试导入时类型注解可能提前求值。
import unittest  # 新增代码+ClaudeCodeDisplayParityTests：使用标准 unittest 框架；如果没有这行代码，测试类不会被发现和执行。
from typing import Any  # 新增代码+ClaudeCodeDisplayParityTests：为 fake host 和 fake agent 标注通用 JSON 类型；如果没有这行代码，测试边界不清楚。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.bind_session_context import bind_session_context  # 新增代码+ClaudeCodeDisplayParityTests：导入真实 agent-side context 绑定入口；如果没有这行代码，display 初始状态绑定无法测试。
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.runtime import ComputerUseMcpV2Context, cleanup_computer_use_mcp_v2_turn, dispatch_computer_use_mcp_v2_tool  # 新增代码+ClaudeCodeDisplayParityTests：导入真实 runtime、context 和 cleanup helper；如果没有这行代码，测试无法覆盖实际分发链路。
from learning_agent.computer_use_mcp_v2.windows_runtime.coordinates import claudecode_display_state_from_payload  # 新增代码+ClaudeCodeDisplayParityTests：导入 display state 抽取器；如果没有这行代码，坐标层薄适配无法单独锁定。


class FakeDisplayHost:  # 新增代码+ClaudeCodeDisplayParityTests：类段开始，伪造 Windows host 的观察 payload；如果没有这段类，测试会依赖真实桌面截图。
    def observe(self, _arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeDisplayParityTests：函数段开始，模拟 screenshot/observe 返回；如果没有这段函数，runtime 分发没有可控观察输入。
        return {"captured": True, "image_results": [{"width": 640, "height": 480}], "display": {"display_id": "display-2"}, "target_window": {"app_id": "notepad.exe", "window_id": "hwnd:42", "title_preview": "Untitled - Notepad"}}  # 新增代码+ClaudeCodeDisplayParityTests：返回含尺寸、display 和窗口的 payload；如果没有这行代码，displayState 四个字段没有事实来源。
    # 新增代码+ClaudeCodeDisplayParityTests：函数段结束，observe 到此结束；如果没有这个边界说明，用户不容易看出 fake 观察范围。
# 新增代码+ClaudeCodeDisplayParityTests：类段结束，FakeDisplayHost 到此结束；如果没有这个边界说明，用户不容易看出 fake host 范围。


class FakeAgent:  # 新增代码+ClaudeCodeDisplayParityTests：类段开始，伪造 agent 主循环保存过的 display 状态；如果没有这段类，bind_session_context 的初始状态读取无法测试。
    def __init__(self) -> None:  # 新增代码+ClaudeCodeDisplayParityTests：函数段开始，初始化 fake agent 字段；如果没有这段函数，绑定层没有可读取的 display 状态。
        self.computer_use_mcp_v2_host = FakeDisplayHost()  # 新增代码+ClaudeCodeDisplayParityTests：注入显式 v2 host；如果没有这行代码，绑定层会尝试构造真实 legacy host。
        self.computer_use_selected_display_id = "display-7"  # 新增代码+ClaudeCodeDisplayParityTests：预置 selected display；如果没有这行代码，context 无法证明能恢复 selectedDisplayId。
        self.computer_use_display_pinned_by_model = True  # 新增代码+ClaudeCodeDisplayParityTests：预置模型 pin；如果没有这行代码，context 无法证明能恢复 displayPinnedByModel。
        self.computer_use_display_resolved_for_apps = [{"appId": "notepad.exe", "displayId": "display-7", "windowId": "hwnd:7"}]  # 新增代码+ClaudeCodeDisplayParityTests：预置 app-display 解析；如果没有这行代码，context 无法证明能恢复 displayResolvedForApps。
        self.computer_use_last_screenshot_dims = {"width": 111, "height": 222}  # 新增代码+ClaudeCodeDisplayParityTests：预置最近截图尺寸；如果没有这行代码，context 无法证明能恢复 lastScreenshotDims。
    # 新增代码+ClaudeCodeDisplayParityTests：函数段结束，__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake agent 初始化范围。
# 新增代码+ClaudeCodeDisplayParityTests：类段结束，FakeAgent 到此结束；如果没有这个边界说明，用户不容易看出 fake agent 范围。


class ComputerUseMcpV2DisplayStateTests(unittest.TestCase):  # 新增代码+ClaudeCodeDisplayParityTests：类段开始，锁定 ClaudeCode display state parity；如果没有这段类，display 对齐缺少自动化保护。
    def test_screenshot_updates_context_and_returns_camel_case_display_state(self) -> None:  # 新增代码+ClaudeCodeDisplayParityTests：函数段开始，验证截图后写入 context 并返回 camelCase；如果没有这段测试，模型可见字段可能悄悄漂移。
        context = ComputerUseMcpV2Context(host=FakeDisplayHost())  # 新增代码+ClaudeCodeDisplayParityTests：创建带 fake host 的真实 context；如果没有这行代码，runtime 会走无 host 回退。
        result = dispatch_computer_use_mcp_v2_tool("screenshot", {"selectedDisplayId": "display-2"}, context)  # 新增代码+ClaudeCodeDisplayParityTests：执行真实 screenshot 分发；如果没有这行代码，display state 集成链路没有输入。
        display_state = result["payload"]["displayState"]  # 新增代码+ClaudeCodeDisplayParityTests：读取模型可见 displayState；如果没有这行代码，后续断言无法定位字段。
        self.assertTrue(result["ok"], result)  # 新增代码+ClaudeCodeDisplayParityTests：断言工具成功；如果没有这行代码，失败结果可能掩盖 display 字段问题。
        self.assertEqual("display-2", context.selected_display_id)  # 新增代码+ClaudeCodeDisplayParityTests：断言 context 保存 selected display；如果没有这行代码，跨工具状态丢失不会失败。
        self.assertTrue(context.display_pinned_by_model)  # 新增代码+ClaudeCodeDisplayParityTests：断言模型显式选择 display 会临时 pin；如果没有这行代码，cleanup 语义无从验证。
        self.assertEqual({"width": 640, "height": 480}, context.last_screenshot_dims)  # 新增代码+ClaudeCodeDisplayParityTests：断言最近截图尺寸写入；如果没有这行代码，lastScreenshotDims 丢失不会失败。
        self.assertEqual("display-2", display_state["selectedDisplayId"])  # 新增代码+ClaudeCodeDisplayParityTests：断言返回 camelCase selectedDisplayId；如果没有这行代码，模型端字段名错误不会失败。
        self.assertTrue(display_state["displayPinnedByModel"])  # 新增代码+ClaudeCodeDisplayParityTests：断言返回 camelCase displayPinnedByModel；如果没有这行代码，pin 状态不可见不会失败。
        self.assertEqual({"width": 640, "height": 480}, display_state["lastScreenshotDims"])  # 新增代码+ClaudeCodeDisplayParityTests：断言返回 camelCase lastScreenshotDims；如果没有这行代码，截图尺寸不可见不会失败。
        self.assertEqual("notepad.exe", display_state["displayResolvedForApps"][0]["appId"])  # 新增代码+ClaudeCodeDisplayParityTests：断言 app-display 解析写入；如果没有这行代码，displayResolvedForApps 缺失不会失败。
    # 新增代码+ClaudeCodeDisplayParityTests：函数段结束，test_screenshot_updates_context_and_returns_camel_case_display_state 到此结束；如果没有这个边界说明，用户不容易看出截图 display 测试范围。

    def test_backend_display_resolve_records_app_without_model_pin(self) -> None:  # 新增代码+ClaudeCodeDisplayParityTests：函数段开始，验证后端自动 display resolve 不会误设模型 pin；如果没有这段测试，displayPinnedByModel 可能被错误置真。
        context = ComputerUseMcpV2Context(host=FakeDisplayHost())  # 新增代码+ClaudeCodeDisplayParityTests：创建空 display 状态 context；如果没有这行代码，测试会复用前一条状态。
        result = dispatch_computer_use_mcp_v2_tool("screenshot", {}, context)  # 新增代码+ClaudeCodeDisplayParityTests：执行没有 selectedDisplayId 的截图；如果没有这行代码，自动解析路径没有输入。
        display_state = result["payload"]["displayState"]  # 新增代码+ClaudeCodeDisplayParityTests：读取返回 displayState；如果没有这行代码，后续断言无法比较模型可见字段。
        self.assertEqual("display-2", context.selected_display_id)  # 新增代码+ClaudeCodeDisplayParityTests：断言后端 display 解析可回填 selected display；如果没有这行代码，自动落屏信息丢失不会失败。
        self.assertFalse(context.display_pinned_by_model)  # 新增代码+ClaudeCodeDisplayParityTests：断言未显式请求时不设置模型 pin；如果没有这行代码，临时状态可能跨 turn 残留。
        self.assertFalse(display_state["displayPinnedByModel"])  # 新增代码+ClaudeCodeDisplayParityTests：断言返回值也保持未 pin；如果没有这行代码，模型会误读屏幕选择来源。
        self.assertEqual("display-2", context.display_resolved_for_apps[0]["displayId"])  # 新增代码+ClaudeCodeDisplayParityTests：断言 app-display 解析记录使用后端 display；如果没有这行代码，应用落屏信息可能不完整。
    # 新增代码+ClaudeCodeDisplayParityTests：函数段结束，test_backend_display_resolve_records_app_without_model_pin 到此结束；如果没有这个边界说明，用户不容易看出自动解析测试范围。

    def test_cleanup_clears_pinned_state_but_keeps_last_screenshot_dims(self) -> None:  # 新增代码+ClaudeCodeDisplayParityTests：函数段开始，验证 cleanup 清 pin 不清尺寸；如果没有这段测试，turn 结束可能错误清掉 lastScreenshotDims。
        context = ComputerUseMcpV2Context(selected_display_id="display-2", display_pinned_by_model=True, last_screenshot_dims={"width": 640, "height": 480})  # 新增代码+ClaudeCodeDisplayParityTests：构造带 pin 和截图尺寸的 context；如果没有这行代码，cleanup 行为没有前置状态。
        result = cleanup_computer_use_mcp_v2_turn(context, reason="display cleanup test")  # 新增代码+ClaudeCodeDisplayParityTests：执行真实 cleanup helper；如果没有这行代码，cleanup display 语义没有被覆盖。
        self.assertTrue(result["cleanup_completed"], result)  # 新增代码+ClaudeCodeDisplayParityTests：断言 cleanup 成功返回；如果没有这行代码，失败路径可能掩盖状态断言。
        self.assertFalse(context.display_pinned_by_model)  # 新增代码+ClaudeCodeDisplayParityTests：断言临时 pin 被清理；如果没有这行代码，displayPinnedByModel 残留不会失败。
        self.assertEqual({"width": 640, "height": 480}, context.last_screenshot_dims)  # 新增代码+ClaudeCodeDisplayParityTests：断言最近截图尺寸保留；如果没有这行代码，lastScreenshotDims 被误清不会失败。
    # 新增代码+ClaudeCodeDisplayParityTests：函数段结束，test_cleanup_clears_pinned_state_but_keeps_last_screenshot_dims 到此结束；如果没有这个边界说明，用户不容易看出 cleanup 测试范围。

    def test_coordinate_helper_extracts_nested_legacy_display_state(self) -> None:  # 新增代码+ClaudeCodeDisplayParityTests：函数段开始，验证坐标层能从 legacy payload 抽取 display state；如果没有这段测试，旧 adapter 包装兼容可能回退。
        payload = {"legacy_result": {"payload": {"coordinate_mapping": {"screenshot_pixel_size": {"width": 320, "height": 240}}, "display": {"display_id": "legacy-display"}, "target_window": {"app_id": "calc.exe", "window_id": "hwnd:9", "title_preview": "Calculator"}}}}  # 新增代码+ClaudeCodeDisplayParityTests：构造嵌套 legacy payload；如果没有这行代码，递归抽取路径没有输入。
        state = claudecode_display_state_from_payload(payload)  # 新增代码+ClaudeCodeDisplayParityTests：执行 display state 抽取 helper；如果没有这行代码，无法断言坐标层返回形状。
        self.assertEqual("legacy-display", state["selectedDisplayId"])  # 新增代码+ClaudeCodeDisplayParityTests：断言 selectedDisplayId 从嵌套 display 读取；如果没有这行代码，legacy display 丢失不会失败。
        self.assertEqual({"width": 320, "height": 240}, state["lastScreenshotDims"])  # 新增代码+ClaudeCodeDisplayParityTests：断言 lastScreenshotDims 从 coordinate_mapping 读取；如果没有这行代码，截图尺寸回流问题不会失败。
        self.assertEqual("calc.exe", state["displayResolvedForApps"][0]["appId"])  # 新增代码+ClaudeCodeDisplayParityTests：断言 app-display 解析从嵌套窗口读取；如果没有这行代码，legacy app resolve 丢失不会失败。
    # 新增代码+ClaudeCodeDisplayParityTests：函数段结束，test_coordinate_helper_extracts_nested_legacy_display_state 到此结束；如果没有这个边界说明，用户不容易看出 helper 测试范围。

    def test_bind_session_context_reads_agent_display_state(self) -> None:  # 新增代码+ClaudeCodeDisplayParityTests：函数段开始，验证 agent 初始 display 状态绑定进 context；如果没有这段测试，主循环重建 context 时可能丢状态。
        agent = FakeAgent()  # 新增代码+ClaudeCodeDisplayParityTests：创建带预置 display 字段的 fake agent；如果没有这行代码，绑定层没有测试输入。
        context = bind_session_context(agent)  # 新增代码+ClaudeCodeDisplayParityTests：执行真实绑定入口；如果没有这行代码，display 初始状态不会进入 context。
        self.assertEqual("display-7", context.selected_display_id)  # 新增代码+ClaudeCodeDisplayParityTests：断言 selected display 被恢复；如果没有这行代码，selectedDisplayId 丢失不会失败。
        self.assertTrue(context.display_pinned_by_model)  # 新增代码+ClaudeCodeDisplayParityTests：断言 pin 状态被恢复；如果没有这行代码，displayPinnedByModel 丢失不会失败。
        self.assertEqual({"width": 111, "height": 222}, context.last_screenshot_dims)  # 新增代码+ClaudeCodeDisplayParityTests：断言截图尺寸被恢复；如果没有这行代码，lastScreenshotDims 丢失不会失败。
        self.assertEqual("notepad.exe", context.display_resolved_for_apps[0]["appId"])  # 新增代码+ClaudeCodeDisplayParityTests：断言 app-display 记录被恢复；如果没有这行代码，displayResolvedForApps 丢失不会失败。
    # 新增代码+ClaudeCodeDisplayParityTests：函数段结束，test_bind_session_context_reads_agent_display_state 到此结束；如果没有这个边界说明，用户不容易看出绑定测试范围。
# 新增代码+ClaudeCodeDisplayParityTests：类段结束，ComputerUseMcpV2DisplayStateTests 到此结束；如果没有这个边界说明，用户不容易看出 display parity 测试范围。


if __name__ == "__main__":  # 新增代码+ClaudeCodeDisplayParityTests：允许直接运行本测试文件；如果没有这行代码，手动调试不方便。
    unittest.main()  # 新增代码+ClaudeCodeDisplayParityTests：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
