"""ClaudeCode 级 resume 深度对齐红线测试。"""  # 新增代码+DeepResume: 说明本文件锁定恢复修复能力；若没有这行代码，维护者可能把普通 summary 读取误认为完成。

from __future__ import annotations  # 新增代码+DeepResume: 延迟解析类型注解；若没有这行代码，后续类型引用更容易受顺序影响。

import json  # 新增代码+DeepResume: 手写 JSONL transcript 行；若没有这行代码，测试无法构造坏行和特殊事件。
import tempfile  # 新增代码+DeepResume: 创建隔离 session 目录；若没有这行代码，测试会污染真实 memory。
import unittest  # 新增代码+DeepResume: 使用项目现有 unittest 框架；若没有这行代码，测试无法被 discover 发现。
from pathlib import Path  # 新增代码+DeepResume: 用 Path 管理测试文件；若没有这行代码，Windows 路径拼接更脆弱。

from learning_agent.core.resume_loader import ResumeLoader  # 新增代码+DeepResume: 导入待升级恢复器；若没有这行代码，测试不能证明 resume v2 能力。
from learning_agent.core.turn_ledger import TurnLedger  # 新增代码+DeepResume: 导入 turn ledger 构造 interrupted turn；若没有这行代码，恢复器无法看到中断状态。


class ResumeDeepAlignmentTests(unittest.TestCase):  # 新增代码+DeepResume: 定义 resume 深度对齐测试集合；若没有这行代码，测试方法没有容器。
    def test_resume_loader_repairs_bad_lines_missing_tool_results_and_interrupted_turn(self) -> None:  # 新增代码+DeepResume: 验证坏 transcript、缺工具结果和中断 turn 都进入恢复报告；若没有这行代码，resume 仍可能盲目成功。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DeepResume: 创建临时根目录；若没有这行代码，测试会写入真实 session。
            base_dir = Path(raw_dir) / "sessions"  # 新增代码+DeepResume: 指定 session store 根目录；若没有这行代码，恢复器和账本路径可能不一致。
            session_dir = base_dir / "session_resume_v2"  # 新增代码+DeepResume: 指定测试 session 目录；若没有这行代码，无法直接写 transcript_v2.jsonl。
            session_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+DeepResume: 创建 session 目录；若没有这行代码，写 transcript 会失败。
            transcript_path = session_dir / "transcript_v2.jsonl"  # 新增代码+DeepResume: 定位 transcript v2 文件；若没有这行代码，测试无法构造恢复输入。
            valid_user = {"uuid": "entry_user", "session_id": "session_resume_v2", "run_id": "run_resume_v2", "turn_id": "turn_0", "event_type": "user_message", "payload": {"content": "请继续长任务"}, "parent_uuid": "", "timestamp": "2026-05-31T00:00:00Z"}  # 新增代码+DeepResume: 构造已落盘用户消息；若没有这行代码，恢复没有用户起点。
            missing_tool = {"uuid": "entry_model", "session_id": "session_resume_v2", "run_id": "run_resume_v2", "turn_id": "turn_0", "event_type": "model_message", "payload": {"text": "", "tool_calls": [{"name": "write", "call_id": "call_missing", "arguments": {"path": "danger.txt"}}]}, "parent_uuid": "entry_user", "timestamp": "2026-05-31T00:00:01Z"}  # 新增代码+DeepResume: 构造没有 tool_result 的危险工具调用；若没有这行代码，resume_needs_review 无法触发。
            orphan_tool = {"uuid": "entry_orphan", "session_id": "session_resume_v2", "run_id": "run_resume_v2", "turn_id": "turn_0", "event_type": "tool_result", "payload": {"call_id": "call_orphan", "output": "孤儿结果"}, "parent_uuid": "missing_parent", "timestamp": "2026-05-31T00:00:02Z"}  # 新增代码+DeepResume: 构造没有对应 tool_use 的孤儿结果；若没有这行代码，tombstone 修复无法验证。
            transcript_path.write_text(json.dumps(valid_user, ensure_ascii=False) + "\n{坏的 JSON 行\n" + json.dumps(missing_tool, ensure_ascii=False) + "\n" + json.dumps(orphan_tool, ensure_ascii=False) + "\n", encoding="utf-8")  # 新增代码+DeepResume: 写入有效行、坏行和不完整工具链；若没有这行代码，恢复器没有复杂输入。
            ledger = TurnLedger(base_dir)  # 新增代码+DeepResume: 创建 turn ledger；若没有这行代码，中断状态没有持久入口。
            ledger.accept_turn(session_id="session_resume_v2", run_id="run_resume_v2", turn_id="turn_0", user_input="请继续长任务")  # 新增代码+DeepResume: 记录 turn 已接收；若没有这行代码，恢复器看不到轮次起点。
            ledger.update_status(session_id="session_resume_v2", turn_id="turn_0", status="interrupted", checkpoint_uuid="entry_model", metadata={"reason": "process_exit_mid_tool"})  # 新增代码+DeepResume: 标记 turn 在工具阶段中断；若没有这行代码，恢复器会误判自然完成。
            context = ResumeLoader(base_dir).load("session_resume_v2")  # 新增代码+DeepResume: 加载恢复上下文；若没有这行代码，测试不会覆盖目标代码。
            consistency = context.consistency  # 新增代码+DeepResume: 提取一致性报告；若没有这行代码，后续断言会重复访问。
            self.assertEqual(consistency.get("resume_state"), "resume_needs_review")  # 新增代码+DeepResume: 断言危险恢复需要人工复核；若没有这行代码，未完成工具可能被静默重跑。
            self.assertGreaterEqual(consistency.get("bad_transcript_line_count", 0), 1)  # 新增代码+DeepResume: 断言坏 JSONL 行被计数；若没有这行代码，坏证据会被无声吞掉。
            self.assertEqual(consistency.get("missing_tool_result_count"), 1)  # 新增代码+DeepResume: 断言缺失 tool_result 被发现；若没有这行代码，危险副作用可能重复执行。
            self.assertEqual(consistency.get("orphan_tool_result_count"), 1)  # 新增代码+DeepResume: 断言孤儿 tool_result 被发现；若没有这行代码，消息链错误无法清理。
            self.assertEqual(consistency.get("interrupted_turn_count"), 1)  # 新增代码+DeepResume: 断言 interrupted turn 被识别；若没有这行代码，恢复器不知道任务中断。
            self.assertTrue(context.repair_report.tombstones)  # 新增代码+DeepResume: 断言产生 tombstone 修复记录；若没有这行代码，UI/SDK 不知道哪些消息无效。
            self.assertIn("Continue from where you left off", "\n".join(str(message.get("content", "")) for message in context.model_messages))  # 新增代码+DeepResume: 断言恢复上下文包含继续提示；若没有这行代码，下一轮模型不知道要续做。


if __name__ == "__main__":  # 新增代码+DeepResume: 支持直接运行本测试；若没有这行代码，单文件排查不方便。
    unittest.main()  # 新增代码+DeepResume: 直接运行时启动 unittest；若没有这行代码，python 文件本身不会执行测试。
