"""终端过程摘要测试，确保用户看到 Codex 风格的安全进度，而不是隐藏推理。"""  # 新增代码+ProcessSummaryUX: 说明本文件专门保护过程摘要体验；若没有这行代码，维护者可能把它误认为普通日志测试。

from __future__ import annotations  # 新增代码+ProcessSummaryUX: 延迟解析类型注解；若没有这行代码，后续前向引用类型更容易受定义顺序影响。

import io  # 新增代码+ProcessSummaryUX: 使用内存文本流捕获终端输出；若没有这行代码，测试只能污染真实 stdout。
import tempfile  # 新增代码+ProcessSummaryUX: 使用临时目录隔离 agent workspace；若没有这行代码，测试会污染真实 learning_agent memory。
import unittest  # 新增代码+ProcessSummaryUX: 使用项目现有 unittest 测试框架；若没有这行代码，测试类无法被 unittest 收集。
from contextlib import redirect_stdout  # 修改代码+ProcessSummaryNoiseControl: 捕获权限提示打印内容；若没有这行代码，危险调试提示去重无法自动断言。
from pathlib import Path  # 新增代码+ProcessSummaryUX: 使用 Path 包装临时工作区；若没有这行代码，路径拼接会更脆弱。
from unittest.mock import patch  # 修改代码+ProcessSummaryNoiseControl: 临时替换权限审计函数避免测试污染真实验收日志；若没有这行代码，权限提示测试会写入外部状态。

import learning_agent.core.agent as core_agent  # 修改代码+ProcessSummaryNoiseControl: 导入 agent 模块本身以重置去重标记；若没有这行代码，测试无法精确验证模块级提示状态。
from learning_agent.app.process_summary import TerminalProcessSummaryRenderer  # 新增代码+ProcessSummaryUX: 导入待实现终端摘要渲染器；若没有这行代码，测试无法锁定生产入口。
from learning_agent.core.agent import LearningAgent, ToolCallingFakeModel  # 新增代码+ProcessSummaryUX: 导入真实 agent 和假模型；若没有这行代码，回调接线测试无法运行真实 run。
from learning_agent.core.events import create_agent_event  # 新增代码+ProcessSummaryUX: 导入事件工厂来构造稳定事件；若没有这行代码，渲染器测试会依赖完整主循环。
from learning_agent.core.messages import ModelMessage  # 新增代码+ProcessSummaryUX: 导入模型消息对象；若没有这行代码，假模型没有可返回的最终回答。


class TerminalProcessSummaryTests(unittest.TestCase):  # 新增代码+ProcessSummaryUX: 定义终端过程摘要测试类；若没有这行代码，unittest 无法组织这些断言。
    def test_renderer_prints_safe_tool_progress_without_raw_tool_output(self) -> None:  # 新增代码+ProcessSummaryUX: 函数段开始，验证摘要显示工具进度但不泄露原始工具输出；若没有这段测试，终端可能把长日志或敏感内容刷给用户。
        stream = io.StringIO()  # 新增代码+ProcessSummaryUX: 创建内存输出流模拟真实终端；若没有这行代码，无法检查渲染文本。
        renderer = TerminalProcessSummaryRenderer(stream=stream)  # 新增代码+ProcessSummaryUX: 创建待测摘要渲染器；若没有这行代码，事件不会被翻译成人类可读文本。
        renderer.handle_event(create_agent_event("run_started", run_id="run_summary", sequence=1, session_id="session_summary", timestamp="2026-06-06T12:00:00Z", payload={"user_input": "请使用画图画树"}))  # 新增代码+ProcessSummaryUX: 模拟运行开始事件；若没有这行代码，无法确认用户能看到任务已接收。
        renderer.handle_event(create_agent_event("tool_call_started", run_id="run_summary", sequence=2, session_id="session_summary", timestamp="2026-06-06T12:00:01Z", payload={"tool_call": {"name": "computer_action", "arguments": {"action": "launch_app", "app_name": "mspaint"}}}))  # 新增代码+ProcessSummaryUX: 模拟准备启动 Paint 的工具调用；若没有这行代码，无法确认工具计划摘要是否可读。
        renderer.handle_event(create_agent_event("tool_call_completed", run_id="run_summary", sequence=3, session_id="session_summary", timestamp="2026-06-06T12:00:02Z", payload={"tool_name": "computer_action", "output": "SECRET_RAW_TOOL_OUTPUT_SHOULD_NOT_APPEAR " + ("x" * 500), "raw_output_chars": 900}))  # 新增代码+ProcessSummaryUX: 模拟包含敏感长输出的工具结果；若没有这行代码，无法防止摘要泄露原始结果。
        output = stream.getvalue()  # 新增代码+ProcessSummaryUX: 读取渲染后的终端文本；若没有这行代码，后续断言没有检查对象。
        self.assertIn("我已收到任务", output)  # 新增代码+ProcessSummaryUX: 断言用户能看到任务已进入 agent；若没有这行代码，启动阶段可能没有过程感。
        self.assertIn("准备调用 computer_action", output)  # 新增代码+ProcessSummaryUX: 断言用户能看到即将调用的工具名；若没有这行代码，工具使用仍像黑盒。
        self.assertIn("启动应用", output)  # 新增代码+ProcessSummaryUX: 断言工具参数被压缩成安全意图摘要；若没有这行代码，用户不知道调用工具为了什么。
        self.assertIn("已完成 computer_action", output)  # 新增代码+ProcessSummaryUX: 断言用户能看到工具完成；若没有这行代码，长任务中间仍像卡住。
        self.assertNotIn("SECRET_RAW_TOOL_OUTPUT_SHOULD_NOT_APPEAR", output)  # 新增代码+ProcessSummaryUX: 断言原始工具输出不会直接展示；若没有这行代码，日志或敏感字段可能泄露到终端。
        # 新增代码+ProcessSummaryUX: 函数段结束，锁定“显示摘要、不显示隐藏推理或原始工具输出”的安全边界；若没有这段注释，用户不容易理解测试意图。

    def test_renderer_uses_production_tool_name_field(self) -> None:  # 修改代码+ProcessSummaryNoiseControl: 函数段开始，验证真实事件的 tool_name 字段能显示成具体工具；若没有这段测试，终端可能继续显示泛化的 tool。本段复现用户左图中的“准备调用 tool”问题，段落到断言结束。
        stream = io.StringIO()  # 修改代码+ProcessSummaryNoiseControl: 创建内存终端输出；若没有这行代码，无法检查渲染器具体文案。
        renderer = TerminalProcessSummaryRenderer(stream=stream)  # 修改代码+ProcessSummaryNoiseControl: 创建待测过程摘要渲染器；若没有这行代码，事件不会被转换成可读摘要。
        renderer.handle_event(create_agent_event("tool_call_started", run_id="run_summary", sequence=1, session_id="session_summary", timestamp="2026-06-06T12:00:01Z", payload={"tool_call": {"tool_name": "computer_action", "arguments": {"action": "drag_path"}}}))  # 修改代码+ProcessSummaryNoiseControl: 模拟生产主循环发出的 tool_name 形态；若没有这行代码，无法覆盖真实 bug 形状。
        output = stream.getvalue()  # 修改代码+ProcessSummaryNoiseControl: 读取渲染后的终端文本；若没有这行代码，断言没有检查对象。
        self.assertIn("准备调用 computer_action", output)  # 修改代码+ProcessSummaryNoiseControl: 断言真实工具名被显示；若没有这行代码，回归时用户仍会看到“tool”。
        self.assertNotIn("准备调用 tool", output)  # 修改代码+ProcessSummaryNoiseControl: 断言泛化工具名不再出现；若没有这行代码，错误文案可能悄悄回归。
        # 修改代码+ProcessSummaryNoiseControl: 函数段结束，锁定 tool_name 兼容边界；若没有这段注释，维护者不容易理解它对应真实截图问题。

    def test_renderer_reads_nested_model_tool_calls_without_false_final_draft(self) -> None:  # 修改代码+ProcessSummaryNoiseControl: 函数段开始，验证生产事件 message.tool_calls 不会被误判成最终回复；若没有这段测试，模型正在用工具时终端会错误显示“回复草案”。本段覆盖 agent.py 当前真实 payload 结构，段落到断言结束。
        stream = io.StringIO()  # 修改代码+ProcessSummaryNoiseControl: 创建内存输出流；若没有这行代码，无法捕获过程摘要。
        renderer = TerminalProcessSummaryRenderer(stream=stream)  # 修改代码+ProcessSummaryNoiseControl: 创建过程摘要渲染器；若没有这行代码，测试没有被测对象。
        renderer.handle_event(create_agent_event("model_message_completed", run_id="run_summary", sequence=1, session_id="session_summary", timestamp="2026-06-06T12:00:01Z", payload={"turn": 0, "message": {"tool_calls": [{"tool_name": "computer_observe", "arguments": {}}]}}))  # 修改代码+ProcessSummaryNoiseControl: 模拟真实模型完成事件中嵌套工具调用；若没有这行代码，无法复现误显示回复草案的根因。
        output = stream.getvalue()  # 修改代码+ProcessSummaryNoiseControl: 读取渲染输出；若没有这行代码，后续断言没有文本来源。
        self.assertIn("computer_observe", output)  # 修改代码+ProcessSummaryNoiseControl: 断言嵌套工具名能被提取；若没有这行代码，真实工具选择仍可能不可见。
        self.assertNotIn("回复草案", output)  # 修改代码+ProcessSummaryNoiseControl: 断言工具调用阶段不会显示最终草案；若没有这行代码，用户会误以为 agent 已经收束。
        # 修改代码+ProcessSummaryNoiseControl: 函数段结束，锁定生产 payload 的模型工具调用读取方式；若没有这段注释，后续容易只测旧字段。

    def test_renderer_throttles_repeated_desktop_loop_events(self) -> None:  # 修改代码+ProcessSummaryNoiseControl: 函数段开始，验证长 Computer Use 循环不会一事件一行刷屏；若没有这段测试，绘图任务会再次出现左图那种重复事件墙。本段模拟多轮 observe/action 事件，段落到断言结束。
        stream = io.StringIO()  # 修改代码+ProcessSummaryNoiseControl: 创建内存终端输出；若没有这行代码，无法统计输出行数。
        renderer = TerminalProcessSummaryRenderer(stream=stream)  # 修改代码+ProcessSummaryNoiseControl: 创建待测渲染器；若没有这行代码，多轮事件无法被处理。
        renderer.handle_event(create_agent_event("run_started", run_id="run_summary", sequence=1, session_id="session_summary", timestamp="2026-06-06T12:00:00Z", payload={"user_input": "请使用画图画水果拼盘"}))  # 修改代码+ProcessSummaryNoiseControl: 模拟任务开始；若没有这行代码，输出统计缺少真实起点。
        for turn in range(12):  # 修改代码+ProcessSummaryNoiseControl: 构造 12 轮桌面循环；若没有这行代码，无法模拟真实绘图任务中的重复事件。
            renderer.handle_event(create_agent_event("model_request_started", run_id="run_summary", sequence=10 + turn, session_id="session_summary", timestamp="2026-06-06T12:00:01Z", payload={"turn": turn}))  # 修改代码+ProcessSummaryNoiseControl: 模拟每轮模型规划开始；若没有这行代码，无法验证模型轮次节流。
            renderer.handle_event(create_agent_event("model_message_completed", run_id="run_summary", sequence=30 + turn, session_id="session_summary", timestamp="2026-06-06T12:00:02Z", payload={"turn": turn, "message": {"tool_calls": [{"tool_name": "computer_action", "arguments": {"action": "drag_path"}}]}}))  # 修改代码+ProcessSummaryNoiseControl: 模拟每轮模型选择桌面动作；若没有这行代码，无法验证嵌套工具调用和节流组合。
            renderer.handle_event(create_agent_event("tool_call_started", run_id="run_summary", sequence=50 + turn, session_id="session_summary", timestamp="2026-06-06T12:00:03Z", payload={"tool_call": {"tool_name": "computer_action", "arguments": {"action": "drag_path"}}}))  # 修改代码+ProcessSummaryNoiseControl: 模拟每轮鼠标拖拽开始；若没有这行代码，无法复现重复“准备调用”刷屏。
            renderer.handle_event(create_agent_event("tool_call_completed", run_id="run_summary", sequence=70 + turn, session_id="session_summary", timestamp="2026-06-06T12:00:04Z", payload={"tool_name": "computer_action", "raw_output_chars": 200}))  # 修改代码+ProcessSummaryNoiseControl: 模拟每轮桌面动作完成；若没有这行代码，无法复现重复“已完成”刷屏。
        output_lines = [line for line in stream.getvalue().splitlines() if line.strip()]  # 修改代码+ProcessSummaryNoiseControl: 统计实际显示的非空行；若没有这行代码，无法量化刷屏是否下降。
        self.assertLessEqual(len(output_lines), 16)  # 修改代码+ProcessSummaryNoiseControl: 断言 12 轮循环不会膨胀成 40 多行；若没有这行代码，终端噪声回归无法被发现。
        self.assertIn("第 10 轮", "\n".join(output_lines))  # 修改代码+ProcessSummaryNoiseControl: 断言节流后仍保留周期性进度；若没有这行代码，修复可能变成完全静默。
        # 修改代码+ProcessSummaryNoiseControl: 函数段结束，锁定“少刷屏但仍有进度”的用户体验；若没有这段注释，后续可能误把节流改成全静默。

    def test_dangerous_permission_notice_prints_once_per_process(self) -> None:  # 修改代码+PermissionNoticeNoiseControl: 函数段开始，验证危险调试提示在同一进程只出现一次；若没有这段测试，Computer Use 每次自动授权都会重复提示。本段只测试终端提示去重，不改变自动授权审计，段落到断言结束。
        core_agent._DANGEROUS_PERMISSION_NOTICE_PRINTED = False  # 修改代码+PermissionNoticeNoiseControl: 重置模块级去重标记；若没有这行代码，测试会受前面用例或真实运行状态影响。
        stream = io.StringIO()  # 修改代码+PermissionNoticeNoiseControl: 创建内存 stdout 捕获区；若没有这行代码，无法统计提示出现次数。
        with patch.object(core_agent, "dangerously_skip_permissions_enabled", return_value=True), patch.object(core_agent, "emit_acceptance_event", lambda *_args, **_kwargs: None), redirect_stdout(stream):  # 修改代码+PermissionNoticeNoiseControl: 固定危险模式开启并屏蔽真实审计写入；若没有这行代码，测试会依赖外部环境或污染验收日志。
            self.assertTrue(core_agent.ask_permission_from_terminal_customer_mode("第一次桌面动作"))  # 修改代码+PermissionNoticeNoiseControl: 第一次自动授权应允许并打印提示；若没有这行代码，无法验证首次提示存在。
            self.assertTrue(core_agent.ask_permission_from_terminal_customer_mode("第二次桌面动作"))  # 修改代码+PermissionNoticeNoiseControl: 第二次自动授权仍允许但不应重复提示；若没有这行代码，无法验证去重。
        self.assertEqual(stream.getvalue().count("危险调试模式已开启"), 1)  # 修改代码+PermissionNoticeNoiseControl: 断言危险提示只出现一次；若没有这行代码，重复刷屏问题可能回归。
        core_agent._DANGEROUS_PERMISSION_NOTICE_PRINTED = False  # 修改代码+PermissionNoticeNoiseControl: 测试结束后恢复标记；若没有这行代码，后续测试或真实运行可能少打印首次提示。
        # 修改代码+PermissionNoticeNoiseControl: 函数段结束，锁定危险调试提示的去重行为；若没有这段注释，维护者可能误以为自动授权也被去重。

    def test_agent_run_can_stream_events_to_terminal_summary_callback(self) -> None:  # 新增代码+ProcessSummaryUX: 函数段开始，验证旧 run API 可选事件回调；若没有这段测试，interactive.py 无法在保留 harness 的同时显示过程摘要。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+ProcessSummaryUX: 创建临时工作区隔离 memory/harness 输出；若没有这行代码，测试会写入真实项目状态。
            workspace = Path(raw_dir)  # 新增代码+ProcessSummaryUX: 把临时目录转为 Path；若没有这行代码，LearningAgent 构造参数不清楚。
            seen_event_types: list[str] = []  # 新增代码+ProcessSummaryUX: 保存回调收到的事件类型；若没有这行代码，无法证明事件真的流到终端层。
            model = ToolCallingFakeModel([ModelMessage(text="最终完成")])  # 新增代码+ProcessSummaryUX: 构造直接最终回答的假模型；若没有这行代码，run 无法稳定完成。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+ProcessSummaryUX: 创建关闭调试落盘噪音的 agent；若没有这行代码，无法测试真实 run 包装路径。
            answer = agent.run("ping", max_turns=1, event_callback=lambda event: seen_event_types.append(event.event_type))  # 新增代码+ProcessSummaryUX: 通过新增回调运行 agent；若没有这行代码，无法证明 run 能把 run_events 透传给 UI。
        self.assertEqual(answer, "最终完成")  # 新增代码+ProcessSummaryUX: 断言旧 run 返回值保持兼容；若没有这行代码，过程摘要可能破坏现有调用方。
        self.assertIn("model_request_started", seen_event_types)  # 新增代码+ProcessSummaryUX: 断言回调能看到模型请求开始；若没有这行代码，用户无法看到 agent 正在规划。
        self.assertIn("run_completed", seen_event_types)  # 新增代码+ProcessSummaryUX: 断言回调能看到运行完成；若没有这行代码，终端层无法在最终回答前收束摘要。
        # 新增代码+ProcessSummaryUX: 函数段结束，锁定 run API 的可选事件回调不会改变最终回答语义；若没有这段注释，后续维护者可能误删回调接线。


if __name__ == "__main__":  # 新增代码+ProcessSummaryUX: 允许直接运行本测试文件；若没有这行代码，单文件排查不方便。
    unittest.main()  # 新增代码+ProcessSummaryUX: 直接运行时启动 unittest；若没有这行代码，python 文件不会执行测试。
