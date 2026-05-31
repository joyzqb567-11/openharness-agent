"""Stage 15A 运行时事件和 transcript 测试。"""  # 新增代码+Stage15A: 说明本文件只测试事件记录地基；若没有这行代码，后续维护者不清楚这个测试文件的边界。

from __future__ import annotations  # 新增代码+Stage15A: 延迟解析类型注解；若没有这行代码，未来添加前向引用类型时更容易受定义顺序影响。

import json  # 新增代码+Stage15A: 用标准库解析 JSONL 内容；若没有这行代码，测试无法确认 transcript 写出的文本真的是 JSON。
import tempfile  # 新增代码+Stage15A: 用临时目录隔离 transcript 写入；若没有这行代码，测试会污染真实项目的 memory 目录。
import unittest  # 新增代码+Stage15A: 使用项目现有 unittest 风格；若没有这行代码，测试类无法被 unittest discover 发现。
from pathlib import Path  # 新增代码+Stage15A: 使用 Path 处理临时目录和事件文件路径；若没有这行代码，路径拼接会更容易出错。

from learning_agent.core.agent import LearningAgent, ToolCallingFakeModel  # 新增代码+Stage15C: 导入 agent 和离线假模型；若没有这行代码，run_events 集成测试无法创建真实主循环。
from learning_agent.core.events import AgentEvent, agent_event_to_json_line, create_agent_event  # 新增代码+Stage15A: 导入事件类型和序列化入口；若没有这行代码，红灯无法证明事件模块缺失。
from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+Stage15C: 导入模型消息和工具调用对象；若没有这行代码，测试无法模拟模型要求工具调用。
from learning_agent.observability.transcript import TranscriptWriter  # 新增代码+Stage15A: 导入 transcript writer；若没有这行代码，红灯无法证明 transcript 模块缺失。


class RuntimeEventsTests(unittest.TestCase):  # 新增代码+Stage15A: 定义运行时事件测试类；若没有这行代码，测试方法没有统一容器。
    def test_agent_event_serializes_to_stable_json_line(self) -> None:  # 新增代码+Stage15A: 验证事件可以稳定转成一行 JSON；若没有这行代码，事件格式回归不会被发现。
        event = create_agent_event(  # 新增代码+Stage15A: 创建一个固定字段的测试事件；若没有这行代码，无法验证工厂函数输出。
            event_type="run_started",  # 新增代码+Stage15A: 指定事件类型；若没有这行代码，测试无法确认 event_type 会被保留。
            run_id="run_stage15a",  # 新增代码+Stage15A: 指定运行编号；若没有这行代码，测试无法确认事件能串起同一次运行。
            sequence=1,  # 新增代码+Stage15A: 指定事件顺序；若没有这行代码，测试无法确认 transcript 可以按顺序恢复。
            session_id="session_stage15a",  # 新增代码+Stage15A: 指定会话编号；若没有这行代码，测试无法确认事件属于哪个 session。
            timestamp="2026-05-31T09:00:00Z",  # 新增代码+Stage15A: 固定时间戳；若没有这行代码，测试结果会因为当前时间变化而不稳定。
            payload={"user_input": "ping"},  # 新增代码+Stage15A: 放入事件载荷；若没有这行代码，测试无法确认业务数据会被写入。
        )  # 新增代码+Stage15A: 结束事件工厂调用；若没有这行代码，Python 语法不完整。
        self.assertIsInstance(event, AgentEvent)  # 新增代码+Stage15A: 确认工厂返回统一事件对象；若没有这行代码，调用方可能收到普通字典导致类型边界漂移。
        json_line = agent_event_to_json_line(event)  # 新增代码+Stage15A: 把事件转成 JSONL 的一行文本；若没有这行代码，无法验证落盘前的序列化格式。
        parsed = json.loads(json_line)  # 新增代码+Stage15A: 解析 JSON 行；若没有这行代码，测试只会比较字符串而不能证明 JSON 有效。
        self.assertEqual(parsed["event_type"], "run_started")  # 新增代码+Stage15A: 断言事件类型保留；若没有这行代码，事件消费者无法按类型过滤。
        self.assertEqual(parsed["run_id"], "run_stage15a")  # 新增代码+Stage15A: 断言运行编号保留；若没有这行代码，多轮运行无法串联。
        self.assertEqual(parsed["sequence"], 1)  # 新增代码+Stage15A: 断言顺序号保留；若没有这行代码，恢复 transcript 时无法排序。
        self.assertEqual(parsed["session_id"], "session_stage15a")  # 新增代码+Stage15A: 断言会话编号保留；若没有这行代码，resume 无法定位会话事件。
        self.assertEqual(parsed["timestamp"], "2026-05-31T09:00:00Z")  # 新增代码+Stage15A: 断言时间戳保留；若没有这行代码，审计时无法知道事件发生时间。
        self.assertEqual(parsed["payload"], {"user_input": "ping"})  # 新增代码+Stage15A: 断言载荷保留；若没有这行代码，事件会丢失业务数据。
        self.assertTrue(json_line.endswith("\n"))  # 新增代码+Stage15A: 断言 JSONL 每条事件独占一行；若没有这行代码，多个事件可能粘在一起无法逐行读取。

    def test_transcript_writer_writes_jsonl_events_in_session_directory(self) -> None:  # 新增代码+Stage15A: 验证 transcript writer 会写入 session 目录；若没有这行代码，会话落盘路径回归不会被发现。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Stage15A: 创建临时目录；若没有这行代码，测试会污染真实 memory/sessions。
            base_dir = Path(raw_dir)  # 新增代码+Stage15A: 把临时路径转成 Path；若没有这行代码，TranscriptWriter 调用会缺少清晰路径类型。
            writer = TranscriptWriter(base_dir=base_dir, session_id="session_001")  # 新增代码+Stage15A: 创建指定 session 的 writer；若没有这行代码，测试无法验证 session 目录。
            first_event = create_agent_event("run_started", run_id="run_001", sequence=1, session_id="session_001", timestamp="2026-05-31T09:00:00Z", payload={"text": "开始"})  # 新增代码+Stage15A: 构造第一条事件；若没有这行代码，无法验证第一行写入。
            second_event = create_agent_event("run_completed", run_id="run_001", sequence=2, session_id="session_001", timestamp="2026-05-31T09:00:01Z", payload={"text": "结束"})  # 新增代码+Stage15A: 构造第二条事件；若没有这行代码，无法验证追加写入。
            first_path = writer.write_event(first_event)  # 新增代码+Stage15A: 写入第一条事件；若没有这行代码，events.jsonl 不会被创建。
            second_path = writer.write_event(second_event)  # 新增代码+Stage15A: 写入第二条事件；若没有这行代码，无法验证 writer 追加而不是覆盖。
            self.assertEqual(first_path, second_path)  # 新增代码+Stage15A: 断言两次写入同一个 events.jsonl；若没有这行代码，writer 可能每条事件写到不同文件。
            self.assertEqual(first_path, base_dir / "session_001" / "events.jsonl")  # 新增代码+Stage15A: 断言路径符合 session 目录约定；若没有这行代码，resume 后续找不到固定文件。
            lines = first_path.read_text(encoding="utf-8").splitlines()  # 新增代码+Stage15A: 读取 JSONL 并按行拆分；若没有这行代码，无法验证写入数量和顺序。
            self.assertEqual(len(lines), 2)  # 新增代码+Stage15A: 断言写入两行；若没有这行代码，覆盖写入或漏写不会被发现。
            parsed_events = [json.loads(line) for line in lines]  # 新增代码+Stage15A: 把两行 JSON 解析成字典；若没有这行代码，无法断言事件字段。
            self.assertEqual([event["event_type"] for event in parsed_events], ["run_started", "run_completed"])  # 新增代码+Stage15A: 断言事件类型顺序稳定；若没有这行代码，恢复时可能乱序。
            self.assertEqual([event["sequence"] for event in parsed_events], [1, 2])  # 新增代码+Stage15A: 断言事件顺序号稳定；若没有这行代码，长任务 transcript 无法可靠回放。
            self.assertEqual(parsed_events[1]["payload"], {"text": "结束"})  # 新增代码+Stage15A: 断言第二条载荷没有丢失；若没有这行代码，最终事件可能缺少业务结果。

    def test_learning_agent_run_events_records_final_answer_and_transcript(self) -> None:  # 新增代码+Stage15C: 验证 run_events 能记录最终回答和 transcript；若没有这行代码，主循环事件流可能只停留在独立 helper。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Stage15C: 创建临时工作区；若没有这行代码，测试会污染真实项目 memory/sessions。
            workspace = Path(raw_dir)  # 新增代码+Stage15C: 把临时目录转成 Path；若没有这行代码，LearningAgent 构造路径不清楚。
            model = ToolCallingFakeModel([ModelMessage(text="pong")])  # 新增代码+Stage15C: 构造直接最终回答的假模型；若没有这行代码，run_events 无法结束。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+Stage15C: 创建关闭调试日志的 agent；若没有这行代码，无法测试真实主循环事件。
            events = list(agent.run_events("ping", max_turns=1))  # 新增代码+Stage15C: 运行事件流主循环；若没有这行代码，无法观察事件序列。
            event_types = [event.event_type for event in events]  # 新增代码+Stage15C: 提取事件类型序列；若没有这行代码，断言会重复解析事件对象。
            self.assertIn("run_started", event_types)  # 新增代码+Stage15C: 断言运行开始事件存在；若没有这行代码，UI 无法知道任务何时开始。
            self.assertIn("model_request_started", event_types)  # 新增代码+Stage15C: 断言模型请求事件存在；若没有这行代码，用户无法看到 agent 正在请求模型。
            self.assertIn("model_message_completed", event_types)  # 新增代码+Stage15C: 断言模型完成事件存在；若没有这行代码，主循环无法记录模型返回。
            self.assertIn("run_completed", event_types)  # 新增代码+Stage15C: 断言运行完成事件存在；若没有这行代码，旧 run() 无法从事件里拿最终回答。
            self.assertEqual(events[-1].payload["text"], "pong")  # 新增代码+Stage15C: 断言最后事件携带最终回答；若没有这行代码，旧 run() 兼容包装拿不到文本。
            session_id = events[0].session_id  # 新增代码+Stage15C: 读取事件会话编号；若没有这行代码，测试无法定位 transcript 目录。
            transcript_path = workspace / "memory" / "sessions" / session_id / "events.jsonl"  # 新增代码+Stage15C: 计算预期 transcript 路径；若没有这行代码，无法验证落盘位置。
            transcript_lines = transcript_path.read_text(encoding="utf-8").splitlines()  # 新增代码+Stage15C: 读取 transcript JSONL；若没有这行代码，无法确认事件已经写入磁盘。
            self.assertEqual(len(transcript_lines), len(events))  # 新增代码+Stage15C: 断言 transcript 行数等于事件数；若没有这行代码，事件可能只 yield 没落盘。
            self.assertEqual(json.loads(transcript_lines[-1])["event_type"], "run_completed")  # 新增代码+Stage15C: 断言最后落盘事件是完成事件；若没有这行代码，恢复时可能找不到最终回答。

    def test_learning_agent_run_events_records_tool_call_events_and_run_stays_compatible(self) -> None:  # 新增代码+Stage15C: 验证工具调用事件和旧 run 兼容；若没有这行代码，run_events 可能破坏原有工具循环。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Stage15C: 创建临时工作区；若没有这行代码，文件工具测试会污染真实项目。
            workspace = Path(raw_dir)  # 新增代码+Stage15C: 把临时目录转成 Path；若没有这行代码，后续写文件路径不清楚。
            (workspace / "sample.txt").write_text("hello", encoding="utf-8")  # 新增代码+Stage15C: 准备 read 工具要读取的文件；若没有这行代码，工具调用会因为文件不存在失败。
            event_model = ToolCallingFakeModel([ModelMessage(tool_calls=[ToolCall(name="read", arguments={"path": "sample.txt"})]), ModelMessage(text="done")])  # 新增代码+Stage15C: 构造先读文件再最终回答的模型；若没有这行代码，测试无法覆盖工具事件。
            event_agent = LearningAgent(model=event_model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+Stage15C: 创建事件流 agent；若没有这行代码，无法运行工具事件场景。
            events = list(event_agent.run_events("read sample", max_turns=3))  # 新增代码+Stage15C: 执行事件流工具循环；若没有这行代码，无法观察 tool_call 事件。
            event_types = [event.event_type for event in events]  # 新增代码+Stage15C: 提取事件类型序列；若没有这行代码，工具事件断言会重复读取对象。
            self.assertIn("tool_call_started", event_types)  # 新增代码+Stage15C: 断言工具开始事件存在；若没有这行代码，UI 无法显示工具正在执行。
            self.assertIn("tool_call_completed", event_types)  # 新增代码+Stage15C: 断言工具完成事件存在；若没有这行代码，transcript 无法记录工具结果。
            tool_completed = next(event for event in events if event.event_type == "tool_call_completed")  # 新增代码+Stage15C: 找到工具完成事件；若没有这行代码，无法检查工具输出载荷。
            self.assertIn("hello", tool_completed.payload["output"])  # 新增代码+Stage15C: 断言工具输出进入事件载荷；若没有这行代码，工具 transcript 不能帮助恢复上下文。
            run_model = ToolCallingFakeModel([ModelMessage(text="旧 run 仍然返回文本")])  # 新增代码+Stage15C: 构造旧 run 兼容测试模型；若没有这行代码，无法验证 run 返回值。
            run_agent = LearningAgent(model=run_model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+Stage15C: 创建旧 run 兼容 agent；若没有这行代码，无法调用 run。
            self.assertEqual(run_agent.run("ping", max_turns=1), "旧 run 仍然返回文本")  # 新增代码+Stage15C: 断言旧 run 返回最终文本；若没有这行代码，外部 CLI 和交互入口可能被事件流改破。


if __name__ == "__main__":  # 新增代码+Stage15A: 允许直接运行本测试文件；若没有这行代码，单文件排查需要额外 unittest 参数。
    unittest.main()  # 新增代码+Stage15A: 直接运行时启动 unittest；若没有这行代码，双击或直接 python 文件不会执行测试。
