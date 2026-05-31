"""Stage 15G 会话保存、恢复和 compact 测试。"""  # 新增代码+Stage15G: 说明本文件锁定 session resume/compact 最小能力；若没有这行代码，维护者不清楚测试目标。

from __future__ import annotations  # 新增代码+Stage15G: 延迟解析类型注解；若没有这行代码，前向引用更容易受定义顺序影响。

import tempfile  # 新增代码+Stage15G: 创建临时 session 根目录；若没有这行代码，测试会污染真实 memory/sessions。
import unittest  # 新增代码+Stage15G: 使用项目现有 unittest 框架；若没有这行代码，测试类无法运行。
from pathlib import Path  # 新增代码+Stage15G: 使用 Path 管理测试路径；若没有这行代码，路径拼接会更脆弱。

from learning_agent.core.events import create_agent_event  # 新增代码+Stage15G: 创建标准运行事件；若没有这行代码，测试无法生成 transcript 输入。
from learning_agent.core.session import SessionRecord, SessionStore, compact_messages_for_session  # 新增代码+Stage15G: 导入新增 session 层；若没有这行代码，红灯无法证明 session 模块缺失。
from learning_agent.observability.transcript import TranscriptWriter, read_transcript_events  # 新增代码+Stage15G: 导入 transcript 写入和读取入口；若没有这行代码，无法验证从 events.jsonl 恢复。


class SessionTests(unittest.TestCase):  # 新增代码+Stage15G: 定义 session 测试类；若没有这行代码，测试方法没有统一容器。
    def test_transcript_reader_loads_jsonl_events(self) -> None:  # 新增代码+Stage15G: 验证 transcript 可以读回事件；若没有这行代码，resume 只能写不能读。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Stage15G: 使用临时目录隔离测试；若没有这行代码，events.jsonl 会写到真实项目。
            base_dir = Path(raw_dir)  # 新增代码+Stage15G: 转成 Path 传给 writer；若没有这行代码，路径类型不统一。
            writer = TranscriptWriter(base_dir=base_dir, session_id="session_read")  # 新增代码+Stage15G: 创建测试 transcript writer；若没有这行代码，无法生成 events.jsonl。
            writer.write_event(create_agent_event("run_started", run_id="run_1", sequence=1, session_id="session_read", payload={"input": "ping"}))  # 新增代码+Stage15G: 写入开始事件；若没有这行代码，reader 没有第一条输入。
            writer.write_event(create_agent_event("run_completed", run_id="run_1", sequence=2, session_id="session_read", payload={"text": "pong"}))  # 新增代码+Stage15G: 写入完成事件；若没有这行代码，reader 无法证明多行读取。
            events = read_transcript_events(base_dir / "session_read" / "events.jsonl")  # 新增代码+Stage15G: 读回 transcript 事件；若没有这行代码，测试不会覆盖恢复入口。
            self.assertEqual([event.event_type for event in events], ["run_started", "run_completed"])  # 新增代码+Stage15G: 断言事件顺序稳定；若没有这行代码，恢复上下文可能乱序。
            self.assertEqual(events[-1].payload["text"], "pong")  # 新增代码+Stage15G: 断言事件载荷保留；若没有这行代码，最终回答可能丢失。

    def test_session_store_saves_loads_and_lists_summary_without_deleting_events(self) -> None:  # 新增代码+Stage15G: 验证 session 摘要保存、读取和列出；若没有这行代码，resume 索引可能只存在内存里。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+Stage15G: 使用临时目录隔离 session 文件；若没有这行代码，测试会污染真实 memory/sessions。
            base_dir = Path(raw_dir)  # 新增代码+Stage15G: 转成 Path；若没有这行代码，后续路径拼接不清楚。
            writer = TranscriptWriter(base_dir=base_dir, session_id="session_store")  # 新增代码+Stage15G: 创建 transcript writer；若没有这行代码，测试无法证明 summary 不删除 events。
            events_path = writer.write_event(create_agent_event("run_completed", run_id="run_2", sequence=1, session_id="session_store", payload={"text": "done"}))  # 新增代码+Stage15G: 写入原始事件证据；若没有这行代码，无法检查 compact/resume 不删证据。
            store = SessionStore(base_dir=base_dir)  # 新增代码+Stage15G: 创建 session store；若没有这行代码，测试无法保存 summary。
            record = SessionRecord(session_id="session_store", run_id="run_2", user_input="ping", messages=[{"role": "user", "content": "ping"}], tool_calls=[], tool_results=[], permission_decisions=[], final_answer="done", artifacts=["artifact.txt"])  # 新增代码+Stage15G: 构造完整 session 摘要；若没有这行代码，保存接口没有真实数据。
            summary_path = store.save_summary(record)  # 新增代码+Stage15G: 保存 session 摘要；若没有这行代码，summary.json 不会生成。
            loaded = store.load_summary("session_store")  # 新增代码+Stage15G: 读取 session 摘要；若没有这行代码，无法验证恢复入口。
            self.assertEqual(summary_path, base_dir / "session_store" / "summary.json")  # 新增代码+Stage15G: 断言摘要路径稳定；若没有这行代码，后续 resume 找不到固定文件。
            self.assertEqual(loaded.final_answer, "done")  # 新增代码+Stage15G: 断言最终回答可恢复；若没有这行代码，恢复上下文缺少关键结果。
            self.assertEqual(store.list_recent_sessions(), ["session_store"])  # 新增代码+Stage15G: 断言可以列出最近 session；若没有这行代码，用户无法发现可恢复会话。
            self.assertTrue(events_path.exists())  # 新增代码+Stage15G: 断言原始 events.jsonl 仍存在；若没有这行代码，compact/summary 可能误删证据也不会被发现。

    def test_compact_messages_keeps_summary_and_tail_without_mutating_original(self) -> None:  # 新增代码+Stage15G: 验证 compact 只生成摘要加尾部消息；若没有这行代码，长会话压缩可能丢掉上下文尾部。
        messages = [{"role": "user", "content": f"message-{index}"} for index in range(5)]  # 新增代码+Stage15G: 构造超过阈值的消息列表；若没有这行代码，compact 分支不会触发。
        compacted = compact_messages_for_session(messages, session_id="session_compact", max_messages=3)  # 新增代码+Stage15G: 执行最小 compact；若没有这行代码，测试不会覆盖压缩 helper。
        self.assertEqual(len(compacted), 3)  # 新增代码+Stage15G: 断言压缩后只保留摘要加尾部两条；若没有这行代码，压缩可能没有控制长度。
        self.assertEqual(compacted[0]["role"], "system")  # 新增代码+Stage15G: 断言第一条是系统摘要；若没有这行代码，模型可能无法识别 compact 背景。
        self.assertIn("Compact Summary", compacted[0]["content"])  # 新增代码+Stage15G: 断言摘要标识存在；若没有这行代码，后续排查不知道这是压缩上下文。
        self.assertIn("session_compact", compacted[0]["content"])  # 新增代码+Stage15G: 断言摘要记录 session id；若没有这行代码，恢复时无法追踪原始 transcript。
        self.assertEqual([message["content"] for message in compacted[1:]], ["message-3", "message-4"])  # 新增代码+Stage15G: 断言保留最新尾部消息；若没有这行代码，模型会丢失最近对话。
        self.assertEqual(messages[0]["content"], "message-0")  # 新增代码+Stage15G: 断言原始消息没有被修改；若没有这行代码，compact 可能污染调用方历史。


if __name__ == "__main__":  # 新增代码+Stage15G: 支持直接运行本测试文件；若没有这行代码，单文件排查不方便。
    unittest.main()  # 新增代码+Stage15G: 直接运行时启动 unittest；若没有这行代码，python 文件本身不会执行测试。
