"""终端过程摘要测试，确保用户看到 Codex 风格的安全进度，而不是隐藏推理。"""  # 新增代码+ProcessSummaryUX: 说明本文件专门保护过程摘要体验；若没有这行代码，维护者可能把它误认为普通日志测试。

from __future__ import annotations  # 新增代码+ProcessSummaryUX: 延迟解析类型注解；若没有这行代码，后续前向引用类型更容易受定义顺序影响。

import io  # 新增代码+ProcessSummaryUX: 使用内存文本流捕获终端输出；若没有这行代码，测试只能污染真实 stdout。
import tempfile  # 新增代码+ProcessSummaryUX: 使用临时目录隔离 agent workspace；若没有这行代码，测试会污染真实 learning_agent memory。
import unittest  # 新增代码+ProcessSummaryUX: 使用项目现有 unittest 测试框架；若没有这行代码，测试类无法被 unittest 收集。
from pathlib import Path  # 新增代码+ProcessSummaryUX: 使用 Path 包装临时工作区；若没有这行代码，路径拼接会更脆弱。

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
