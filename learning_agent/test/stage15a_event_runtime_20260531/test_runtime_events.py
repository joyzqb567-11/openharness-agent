"""Stage 15A 运行时事件和 transcript 测试。"""  # 新增代码+Stage15A: 说明本文件只测试事件记录地基；若没有这行代码，后续维护者不清楚这个测试文件的边界。

from __future__ import annotations  # 新增代码+Stage15A: 延迟解析类型注解；若没有这行代码，未来添加前向引用类型时更容易受定义顺序影响。

import json  # 新增代码+Stage15A: 用标准库解析 JSONL 内容；若没有这行代码，测试无法确认 transcript 写出的文本真的是 JSON。
import tempfile  # 新增代码+Stage15A: 用临时目录隔离 transcript 写入；若没有这行代码，测试会污染真实项目的 memory 目录。
import unittest  # 新增代码+Stage15A: 使用项目现有 unittest 风格；若没有这行代码，测试类无法被 unittest discover 发现。
from pathlib import Path  # 新增代码+Stage15A: 使用 Path 处理临时目录和事件文件路径；若没有这行代码，路径拼接会更容易出错。

from learning_agent.core.events import AgentEvent, agent_event_to_json_line, create_agent_event  # 新增代码+Stage15A: 导入事件类型和序列化入口；若没有这行代码，红灯无法证明事件模块缺失。
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


if __name__ == "__main__":  # 新增代码+Stage15A: 允许直接运行本测试文件；若没有这行代码，单文件排查需要额外 unittest 参数。
    unittest.main()  # 新增代码+Stage15A: 直接运行时启动 unittest；若没有这行代码，双击或直接 python 文件不会执行测试。
