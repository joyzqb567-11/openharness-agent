from __future__ import annotations  # 新增代码+ClaudeCodeWrapperParityTests：延迟类型注解解析；如果没有这一行，fake 类型在导入时可能提前求值失败。

import base64  # 新增代码+ClaudeCodeWrapperParityTests：生成测试 PNG 字节；如果没有这一行，截图 content block 测试没有真实图片输入。
import json  # 新增代码+ClaudeCodeWrapperParityTests：解析 wrapper 返回的 JSON 文本；如果没有这一行，测试只能做脆弱字符串断言。
import tempfile  # 新增代码+ClaudeCodeWrapperParityTests：创建临时目录存放测试截图；如果没有这一行，测试会污染仓库目录。
import unittest  # 新增代码+ClaudeCodeWrapperParityTests：使用标准库测试框架；如果没有这一行，测试类不会被 unittest 发现。
from pathlib import Path  # 新增代码+ClaudeCodeWrapperParityTests：稳定处理临时截图路径；如果没有这一行，Windows 路径拼接容易出错。
from typing import Any  # 新增代码+ClaudeCodeWrapperParityTests：标注 fake payload 的动态类型；如果没有这一行，测试辅助对象边界不清楚。

from learning_agent.computer_use_mcp_v2.claudecode_bridge.toolRendering import render_tool_result, render_tool_use_message  # 新增代码+ClaudeCodeWrapperParityTests：导入 Python toolRendering 对齐函数；如果没有这一行，字段名渲染无法被测试保护。
from learning_agent.computer_use_mcp_v2.claudecode_bridge.wrapper import cleanup_agent_side_turn, current_tool_use_context, execute_agent_side_tool  # 新增代码+ClaudeCodeWrapperParityTests：导入 agent-side wrapper 入口和 cleanup hook；如果没有这一行，wrapper 行为没有自动化保护。

SAMPLE_PNG_BYTES = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=")  # 新增代码+ClaudeCodeWrapperParityTests：准备 1x1 PNG；如果没有这一行，测试无法证明 image block 携带真实 base64。


class _FakeHost:  # 新增代码+ClaudeCodeWrapperParityTests：类段开始，模拟 Windows host 的截图返回；如果没有这个类，wrapper 测试可能触碰真实桌面。
    def __init__(self, artifact_path: str = "") -> None:  # 新增代码+ClaudeCodeWrapperParityTests：函数段开始，保存可选截图路径；如果没有这段函数，fake host 不知道返回哪张图片。
        self.artifact_path = artifact_path  # 新增代码+ClaudeCodeWrapperParityTests：记录截图路径；如果没有这一行，observe/screenshot 返回无法包含 artifact。
    # 新增代码+ClaudeCodeWrapperParityTests：函数段结束，_FakeHost.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake host 初始化范围。

    def observe(self, _arguments: dict[str, Any]) -> dict[str, Any]:  # 新增代码+ClaudeCodeWrapperParityTests：函数段开始，模拟 screenshot/observe；如果没有这段函数，runtime 会认为 host 不支持观察。
        return {"captured": True, "image_results": [{"artifact_path": self.artifact_path, "mime_type": "image/png"}]}  # 新增代码+ClaudeCodeWrapperParityTests：返回结构化图片结果；如果没有这一行，wrapper 无法生成 image content block。
    # 新增代码+ClaudeCodeWrapperParityTests：函数段结束，_FakeHost.observe 到此结束；如果没有这个边界说明，用户不容易看出 fake 观察范围。
# 新增代码+ClaudeCodeWrapperParityTests：类段结束，_FakeHost 到此结束；如果没有这个边界说明，用户不容易看出 fake host 范围。


class _FakeCleanupRuntime:  # 新增代码+ClaudeCodeWrapperParityTests：类段开始，模拟不会碰真实锁文件的 cleanup runtime；如果没有这个类，测试可能创建真实 Windows lock runtime。
    def __init__(self) -> None:  # 新增代码+ClaudeCodeWrapperParityTests：函数段开始，初始化 cleanup 记录；如果没有这段函数，测试无法断言 cleanup 被调用。
        self.lock_manager = None  # 新增代码+ClaudeCodeWrapperParityTests：显式禁用真实 lock manager；如果没有这一行，绑定层可能尝试真实锁操作。
        self.session_id = "wrapper-test-session"  # 新增代码+ClaudeCodeWrapperParityTests：提供稳定 session id；如果没有这一行，context 会使用默认值且测试证据不清楚。
        self.cleanup_reasons: list[str] = []  # 新增代码+ClaudeCodeWrapperParityTests：保存 cleanup 原因；如果没有这一行，无法确认 cleanup hook 的 reason。
    # 新增代码+ClaudeCodeWrapperParityTests：函数段结束，_FakeCleanupRuntime.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 cleanup runtime 初始化范围。

    def cleanup_turn(self, reason: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeWrapperParityTests：函数段开始，模拟 turn-end cleanup；如果没有这段函数，cleanup hook 没有可调用目标。
        self.cleanup_reasons.append(str(reason))  # 新增代码+ClaudeCodeWrapperParityTests：记录 cleanup 原因；如果没有这一行，测试无法证明 hook 传参正确。
        return {"cleanup_completed": True, "lock_released": True, "reason": str(reason), "runtime": "fake"}  # 新增代码+ClaudeCodeWrapperParityTests：返回稳定 cleanup 结果；如果没有这一行，wrapper 无法把结果写回 agent。
    # 新增代码+ClaudeCodeWrapperParityTests：函数段结束，_FakeCleanupRuntime.cleanup_turn 到此结束；如果没有这个边界说明，用户不容易看出 cleanup 调用范围。
# 新增代码+ClaudeCodeWrapperParityTests：类段结束，_FakeCleanupRuntime 到此结束；如果没有这个边界说明，用户不容易看出 fake cleanup runtime 范围。


class _FakeAgent:  # 新增代码+ClaudeCodeWrapperParityTests：类段开始，模拟 bind_session_context 需要的最小 agent；如果没有这个类，测试必须启动完整 LearningAgent。
    def __init__(self, workspace: Path, host: _FakeHost | None = None) -> None:  # 新增代码+ClaudeCodeWrapperParityTests：函数段开始，初始化 fake agent 字段；如果没有这段函数，wrapper 没有 agent 上下文。
        self.workspace = workspace  # 新增代码+ClaudeCodeWrapperParityTests：保存工作目录；如果没有这一行，observation helper 和 artifact 逻辑缺少路径事实源。
        self.computer_use_mcp_v2_host = host or _FakeHost()  # 新增代码+ClaudeCodeWrapperParityTests：注入 fake host；如果没有这一行，bind_session_context 会构造真实 legacy host。
        self.computer_use_turn_cleanup_runtime = _FakeCleanupRuntime()  # 新增代码+ClaudeCodeWrapperParityTests：注入 fake cleanup runtime；如果没有这一行，cleanup 测试可能触碰真实锁目录。
        self.observation_events: list[dict[str, Any]] = []  # 新增代码+ClaudeCodeWrapperParityTests：保存 observation 事件；如果没有这一行，safe_record_observation 可能缺少容器。
        self.active_artifacts: list[str] = []  # 新增代码+ClaudeCodeWrapperParityTests：保存 artifact 记录；如果没有这一行，图片登记逻辑可能缺少字段。
        self.computer_use_runtime_trace_events: list[dict[str, Any]] = []  # 新增代码+ClaudeCodeWrapperParityTests：保存 v2 runtime trace；如果没有这一行，trace 回调无法被测试观察。
    # 新增代码+ClaudeCodeWrapperParityTests：函数段结束，_FakeAgent.__init__ 到此结束；如果没有这个边界说明，用户不容易看出 fake agent 初始化范围。

    def ask_permission(self, _action: str) -> bool:  # 新增代码+ClaudeCodeWrapperParityTests：函数段开始，模拟用户授权；如果没有这段函数，request_access 无法通过权限回调。
        return True  # 新增代码+ClaudeCodeWrapperParityTests：测试中默认同意安全授权申请；如果没有这一行，request_access 会被拒绝而无法覆盖 wrapper 成功路径。
    # 新增代码+ClaudeCodeWrapperParityTests：函数段结束，_FakeAgent.ask_permission 到此结束；如果没有这个边界说明，用户不容易看出 fake 授权范围。
# 新增代码+ClaudeCodeWrapperParityTests：类段结束，_FakeAgent 到此结束；如果没有这个边界说明，用户不容易看出 fake agent 范围。


class ComputerUseMcpV2BridgeWrapperTests(unittest.TestCase):  # 新增代码+ClaudeCodeWrapperParityTests：类段开始，锁住 ClaudeCode bridge wrapper parity；如果没有这个测试类，任务 9 的 wrapper 行为可能回归。
    def test_wrapper_records_current_tool_use_context_with_call_id(self) -> None:  # 新增代码+ClaudeCodeWrapperParityTests：函数段开始，验证每次调用写入 current tool use context；如果没有这个测试，call_id 可能再次丢失。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ClaudeCodeWrapperParityTests：创建临时 workspace；如果没有这一行，fake agent 状态会污染项目目录。
            agent = _FakeAgent(Path(raw_dir))  # 新增代码+ClaudeCodeWrapperParityTests：创建 fake agent；如果没有这一行，wrapper 没有上下文对象。
            output = execute_agent_side_tool(agent, "mcp__computer-use__request_access", {"apps": [{"displayName": "Notepad", "bundleId": "notepad.exe"}]}, call_id="call-wrapper")  # 新增代码+ClaudeCodeWrapperParityTests：执行安全 request_access；如果没有这一行，current context 没有真实调用输入。
            payload = json.loads(output)  # 新增代码+ClaudeCodeWrapperParityTests：解析 wrapper JSON；如果没有这一行，后续无法结构化断言 wrapper 字段。
        self.assertTrue(payload["ok"], payload)  # 新增代码+ClaudeCodeWrapperParityTests：断言工具成功；如果没有这一行，失败结果可能被字段断言掩盖。
        self.assertEqual("claudecode_wrapper", payload["wrapper"]["bridge"])  # 新增代码+ClaudeCodeWrapperParityTests：断言结果经过 wrapper；如果没有这一行，runtime 可能绕过 wrapper 直接返回。
        self.assertEqual("call-wrapper", current_tool_use_context()["call_id"])  # 新增代码+ClaudeCodeWrapperParityTests：断言模块 current context 保存 call_id；如果没有这一行，ClaudeCode per-call ref 对齐缺口不会失败。
        self.assertEqual("call-wrapper", agent.computer_use_mcp_v2_current_tool_use_context["call_id"])  # 新增代码+ClaudeCodeWrapperParityTests：断言 agent 上也保存 call_id；如果没有这一行，主循环状态页无法读取当前工具。
        self.assertGreaterEqual(payload["agent_model_block_count"], 1)  # 新增代码+ClaudeCodeWrapperParityTests：断言 wrapper 至少生成一个 agent block；如果没有这一行，content block 映射可能没执行。
    # 新增代码+ClaudeCodeWrapperParityTests：函数段结束，test_wrapper_records_current_tool_use_context_with_call_id 到此结束；如果没有这个边界说明，用户不容易看出 current context 测试范围。

    def test_wrapper_maps_screenshot_content_to_agent_blocks_without_duplicate_public_base64(self) -> None:  # 新增代码+ClaudeCodeWrapperParityTests：函数段开始，验证 screenshot content 映射并避免公开 JSON 重复图片；如果没有这个测试，图片块可能再次膨胀工具文本。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ClaudeCodeWrapperParityTests：创建临时目录；如果没有这一行，测试截图没有安全位置。
            artifact_path = Path(raw_dir) / "screen.png"  # 新增代码+ClaudeCodeWrapperParityTests：定义测试截图路径；如果没有这一行，fake host 无法返回 artifact。
            artifact_path.write_bytes(SAMPLE_PNG_BYTES)  # 新增代码+ClaudeCodeWrapperParityTests：写入真实 PNG；如果没有这一行，image content block 无法生成 base64。
            agent = _FakeAgent(Path(raw_dir), host=_FakeHost(str(artifact_path)))  # 新增代码+ClaudeCodeWrapperParityTests：创建带截图 host 的 fake agent；如果没有这一行，screenshot 会缺少图片来源。
            output = execute_agent_side_tool(agent, "mcp__computer-use__screenshot", {}, call_id="call-shot")  # 新增代码+ClaudeCodeWrapperParityTests：执行 screenshot wrapper；如果没有这一行，图片映射路径没有输入。
            payload = json.loads(output)  # 新增代码+ClaudeCodeWrapperParityTests：解析 wrapper JSON；如果没有这一行，后续无法检查 public block 摘要。
        image_blocks = [block for block in agent.computer_use_mcp_v2_last_agent_model_blocks if block.get("type") == "image"]  # 新增代码+ClaudeCodeWrapperParityTests：读取完整内存 image blocks；如果没有这一行，无法证明完整 block 已写回 agent。
        public_image_blocks = [block for block in payload["agent_model_blocks"] if block.get("type") == "image"]  # 新增代码+ClaudeCodeWrapperParityTests：读取公开 JSON 图片摘要；如果没有这一行，无法检查去 base64 逻辑。
        self.assertEqual(1, len(image_blocks))  # 新增代码+ClaudeCodeWrapperParityTests：断言完整内存块有一张图；如果没有这一行，图片映射漏掉不会失败。
        self.assertTrue(image_blocks[0]["source"]["data"])  # 新增代码+ClaudeCodeWrapperParityTests：断言完整内存块保留 base64；如果没有这一行，未来多模态 tool result 无法直接使用。
        self.assertEqual(1, len(public_image_blocks))  # 新增代码+ClaudeCodeWrapperParityTests：断言公开摘要也知道有一张图；如果没有这一行，模型文本看不到图片存在。
        self.assertIn("base64_chars", public_image_blocks[0]["source"])  # 新增代码+ClaudeCodeWrapperParityTests：断言公开 JSON 只保留长度；如果没有这一行，输出可能重复携带大 base64。
        self.assertNotIn("data", public_image_blocks[0]["source"])  # 新增代码+ClaudeCodeWrapperParityTests：断言公开 JSON 不重复图片数据；如果没有这一行，工具输出可能继续膨胀。
    # 新增代码+ClaudeCodeWrapperParityTests：函数段结束，test_wrapper_maps_screenshot_content_to_agent_blocks_without_duplicate_public_base64 到此结束；如果没有这个边界说明，用户不容易看出图片 block 测试范围。

    def test_cleanup_agent_side_turn_calls_same_bound_context(self) -> None:  # 新增代码+ClaudeCodeWrapperParityTests：函数段开始，验证 wrapper cleanup hook 复用同一 context；如果没有这个测试，turn-end cleanup 可能释放不到同一会话。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ClaudeCodeWrapperParityTests：创建临时 workspace；如果没有这一行，fake agent 状态会污染项目目录。
            agent = _FakeAgent(Path(raw_dir))  # 新增代码+ClaudeCodeWrapperParityTests：创建 fake agent；如果没有这一行，cleanup 没有上下文。
            execute_agent_side_tool(agent, "mcp__computer-use__request_access", {"apps": [{"displayName": "Notepad"}]}, call_id="call-before-cleanup")  # 新增代码+ClaudeCodeWrapperParityTests：先执行一次工具以绑定 context；如果没有这一行，cleanup 不能证明复用已有 context。
            cleanup = cleanup_agent_side_turn(agent, reason="unit cleanup")  # 新增代码+ClaudeCodeWrapperParityTests：调用 wrapper cleanup hook；如果没有这一行，cleanup 行为没有输入。
        self.assertTrue(cleanup["cleanup_completed"], cleanup)  # 新增代码+ClaudeCodeWrapperParityTests：断言 cleanup 完成；如果没有这一行，失败 cleanup 可能被忽略。
        self.assertEqual("unit cleanup", cleanup["reason"])  # 新增代码+ClaudeCodeWrapperParityTests：断言 cleanup reason 保留；如果没有这一行，abort/turn-end 原因可能丢失。
        self.assertEqual("unit cleanup", agent.computer_use_mcp_v2_last_cleanup["reason"])  # 新增代码+ClaudeCodeWrapperParityTests：断言结果写回 agent；如果没有这一行，状态页无法显示最后 cleanup 证据。
    # 新增代码+ClaudeCodeWrapperParityTests：函数段结束，test_cleanup_agent_side_turn_calls_same_bound_context 到此结束；如果没有这个边界说明，用户不容易看出 cleanup 测试范围。

    def test_tool_rendering_uses_claudecode_field_names(self) -> None:  # 新增代码+ClaudeCodeWrapperParityTests：函数段开始，验证 toolRendering 使用蓝图字段名；如果没有这个测试，字段名可能回退成旧 x/y/app_name。
        message = render_tool_use_message("open_application", {"coordinate": [1, 2], "start_coordinate": [3, 4], "region": [1, 2, 3, 4], "direction": "down", "amount": 2, "text": "hello world", "duration": 1.5, "bundle_id": "notepad.exe", "apps": [{"displayName": "Notepad"}], "actions": [{"tool_name": "left_click"}]})  # 新增代码+ClaudeCodeWrapperParityTests：构造包含所有 ClaudeCode 字段的渲染输入；如果没有这一行，字段覆盖不完整。
        for field_name in ("coordinate", "start_coordinate", "region", "direction", "amount", "text", "duration", "bundle_id", "apps", "actions"):  # 新增代码+ClaudeCodeWrapperParityTests：逐项检查蓝图要求字段；如果没有这一行，漏字段不会被定位。
            self.assertIn(f"{field_name}=", message)  # 新增代码+ClaudeCodeWrapperParityTests：断言字段名出现在摘要中；如果没有这一行，字段名对齐回归不会失败。
        self.assertEqual("Clicked", render_tool_result({"ok": True, "tool_name": "left_click"}))  # 新增代码+ClaudeCodeWrapperParityTests：断言结果摘要对齐 ClaudeCode；如果没有这一行，非 verbose 结果提示可能漂移。
    # 新增代码+ClaudeCodeWrapperParityTests：函数段结束，test_tool_rendering_uses_claudecode_field_names 到此结束；如果没有这个边界说明，用户不容易看出渲染测试范围。
# 新增代码+ClaudeCodeWrapperParityTests：类段结束，ComputerUseMcpV2BridgeWrapperTests 到此结束；如果没有这个边界说明，用户不容易看出 wrapper parity 测试范围。


if __name__ == "__main__":  # 新增代码+ClaudeCodeWrapperParityTests：允许直接运行本测试文件；如果没有这一行，手动调试只能通过模块名。
    unittest.main()  # 新增代码+ClaudeCodeWrapperParityTests：启动 unittest；如果没有这一行，直接运行文件不会执行测试。

