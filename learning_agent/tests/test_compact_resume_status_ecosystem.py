"""Compact/resume 与状态生态对齐 ClaudeCode 的行为测试。"""  # 新增代码+CompactResumeStatus: 说明本测试文件锁定本轮 12 阶段任务；若没有这行代码，维护者不清楚这些测试为何存在。

from __future__ import annotations  # 新增代码+CompactResumeStatus: 延迟解析类型注解；若没有这行代码，未来添加前向引用时更容易受定义顺序影响。

import io  # 新增代码+CompactResumeStatus: 捕获终端状态命令输出；若没有这行代码，测试只能污染真实 stdout。
import http.client  # 新增代码+CompactResumeStatus: 通过真实 HTTP 协议验证 bridge 状态 API；若没有这行代码，SDK/API 端点只能靠手工检查。
import json  # 新增代码+CompactResumeStatus: 解析 HTTP/SDK JSON 结构；若没有这行代码，测试无法验证结构化状态数据。
import subprocess  # 新增代码+CompactResumeStatus: 通过 python -m 验证真实 CLI 入口；若没有这行代码，测试只能调用函数而不能覆盖命令行。
import sys  # 新增代码+CompactResumeStatus: 获取当前 Python 可执行文件；若没有这行代码，子进程可能用错解释器。
import tempfile  # 新增代码+CompactResumeStatus: 创建隔离工作区；若没有这行代码，测试会污染真实 memory 目录。
import threading  # 新增代码+CompactResumeStatus: 后台启动 HTTP bridge server；若没有这行代码，测试会卡在 serve_forever。
import unittest  # 新增代码+CompactResumeStatus: 使用项目现有 unittest 框架；若没有这行代码，测试不会被 discover 发现。
from contextlib import redirect_stdout  # 新增代码+CompactResumeStatus: 临时捕获 CLI 输出；若没有这行代码，状态 CLI 测试无法断言文本。
from pathlib import Path  # 新增代码+CompactResumeStatus: 使用 Path 管理跨平台路径；若没有这行代码，Windows 路径拼接更脆弱。
from unittest import mock  # 新增代码+CompactResumeStatus: 模拟交互终端 input；若没有这行代码，/status 测试会卡在真实输入。

from learning_agent.app.interactive import run_interactive_session  # 新增代码+CompactResumeStatus: 导入真实交互入口；若没有这行代码，终端状态 UI 无法被测试锁定。
from learning_agent.app.http_bridge import create_command_bridge_server  # 新增代码+CompactResumeStatus: 导入真实 HTTP bridge server；若没有这行代码，状态 API 没有测试入口。
from learning_agent.core.agent import LearningAgent  # 新增代码+CompactResumeStatus: 导入真实 agent 类；若没有这行代码，状态工具和主循环无法覆盖。
from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+CompactResumeStatus: 导入模型消息和工具调用对象；若没有这行代码，测试无法驱动模型和工具。
from learning_agent.core.session import SessionRecord, SessionStore  # 新增代码+CompactResumeStatus: 导入旧 summary store 作为 resume 输入；若没有这行代码，恢复测试缺少摘要证据。
from learning_agent.harness.cli import main as harness_cli_main  # 新增代码+CompactResumeStatus: 导入 harness CLI；若没有这行代码，状态生态 CLI 入口无法验收。
from learning_agent.harness.models import HarnessRun, HarnessStage  # 新增代码+CompactResumeStatus: 构造持久 harness run；若没有这行代码，状态快照没有 run 输入。
from learning_agent.harness.store import HarnessStore  # 新增代码+CompactResumeStatus: 写入 harness 状态；若没有这行代码，聚合器无法读取 run。
from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+CompactResumeStatus: 写入 runtime queue；若没有这行代码，状态快照无法显示命令队列。
from learning_agent.runtime.task_registry import TaskRegistry  # 新增代码+CompactResumeStatus: 写入持久 task；若没有这行代码，状态快照无法显示后台任务。
from learning_agent.tests.support import RecordingToolNameFakeModel  # 新增代码+CompactResumeStatus: 使用离线假模型；若没有这行代码，测试可能调用真实模型。
from learning_agent.tools.schemas import TOOL_SCHEMAS  # 新增代码+CompactResumeStatus: 读取模型可见工具 schema；若没有这行代码，状态工具 schema 无法验证。


class CompactResumeStatusEcosystemTests(unittest.TestCase):  # 新增代码+CompactResumeStatus: 定义本轮对齐测试集合；若没有这行代码，测试方法没有统一容器。
    def test_transcript_v2_and_turn_ledger_are_durable_and_replayable(self) -> None:  # 新增代码+CompactResumeStatus: 验证 transcript v2 与 turn ledger 可持久回放；若没有这行代码，恢复只能靠旧 summary。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CompactResumeStatus: 创建隔离目录；若没有这行代码，测试会写入真实项目状态。
            base_dir = Path(raw_dir) / "sessions"  # 新增代码+CompactResumeStatus: 设置 session 存储根目录；若没有这行代码，store 没有固定位置。
            from learning_agent.core.transcript_v2 import TranscriptV2Store  # 新增代码+CompactResumeStatus: 延迟导入目标模块制造红测；若没有这行代码，测试不会锁定新 transcript v2。
            from learning_agent.core.turn_ledger import TurnLedger  # 新增代码+CompactResumeStatus: 延迟导入目标模块制造红测；若没有这行代码，测试不会锁定 turn ledger。
            transcript_store = TranscriptV2Store(base_dir)  # 新增代码+CompactResumeStatus: 创建 transcript v2 store；若没有这行代码，无法写入可回放条目。
            first_entry = transcript_store.append_entry(session_id="session_v2", run_id="run_v2", turn_id="turn_1", event_type="user_message", payload={"content": "真实 prompt"})  # 新增代码+CompactResumeStatus: 在模型前持久化用户输入；若没有这行代码，崩溃后 prompt 会丢失。
            second_entry = transcript_store.append_entry(session_id="session_v2", run_id="run_v2", turn_id="turn_1", event_type="model_request", payload={"message_count": 1}, parent_uuid=first_entry.uuid)  # 新增代码+CompactResumeStatus: 写入父子关联事件；若没有这行代码，事件链无法审计顺序。
            replayed_entries = transcript_store.list_entries("session_v2")  # 新增代码+CompactResumeStatus: 从磁盘回放条目；若没有这行代码，测试只证明内存可用。
            self.assertEqual([entry.event_type for entry in replayed_entries], ["user_message", "model_request"])  # 新增代码+CompactResumeStatus: 断言事件顺序可恢复；若没有这行代码，恢复可能乱序。
            self.assertEqual(replayed_entries[1].parent_uuid, second_entry.parent_uuid)  # 新增代码+CompactResumeStatus: 断言父节点关系保留；若没有这行代码，审计链可能断开。
            ledger = TurnLedger(base_dir)  # 新增代码+CompactResumeStatus: 创建 turn ledger；若没有这行代码，轮次状态没有持久入口。
            ledger.accept_turn(session_id="session_v2", run_id="run_v2", turn_id="turn_1", user_input="真实 prompt")  # 新增代码+CompactResumeStatus: 记录用户 turn 已接收；若没有这行代码，恢复不知道哪一轮已经开始。
            ledger.update_status(session_id="session_v2", turn_id="turn_1", status="model_running", checkpoint_uuid=first_entry.uuid)  # 新增代码+CompactResumeStatus: 更新模型运行状态和 checkpoint；若没有这行代码，中断后无法定位恢复点。
            restored_turn = TurnLedger(base_dir).get_turn("session_v2", "turn_1")  # 新增代码+CompactResumeStatus: 用新实例读取 turn；若没有这行代码，测试无法模拟重启。
            self.assertEqual(restored_turn.status, "model_running")  # 新增代码+CompactResumeStatus: 断言状态跨实例保留；若没有这行代码，turn ledger 可能只是内存。
            self.assertEqual(restored_turn.checkpoint_uuid, first_entry.uuid)  # 新增代码+CompactResumeStatus: 断言 checkpoint 跨实例保留；若没有这行代码，恢复点会丢失。

    def test_compact_boundary_and_resume_loader_reconstruct_context_without_rerun(self) -> None:  # 新增代码+CompactResumeStatus: 验证 compact 边界和 resume loader；若没有这行代码，恢复可能重跑已完成阶段。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CompactResumeStatus: 创建隔离目录；若没有这行代码，测试会污染真实 session。
            base_dir = Path(raw_dir) / "sessions"  # 新增代码+CompactResumeStatus: 设置 session 根目录；若没有这行代码，各 store 路径不一致。
            from learning_agent.core.compact import compact_messages_with_boundary  # 新增代码+CompactResumeStatus: 延迟导入 compact 目标模块；若没有这行代码，测试不会锁定 compact boundary。
            from learning_agent.core.resume_loader import ResumeLoader  # 新增代码+CompactResumeStatus: 延迟导入 resume loader；若没有这行代码，恢复入口不会被测试。
            from learning_agent.core.transcript_v2 import TranscriptV2Store  # 新增代码+CompactResumeStatus: 导入 transcript v2 store；若没有这行代码，compact boundary 没有原始证据。
            messages = [{"role": "user", "content": f"old-{index}"} for index in range(6)]  # 新增代码+CompactResumeStatus: 构造会触发 compact 的长消息；若没有这行代码，compact 分支不会执行。
            compacted_messages, boundary = compact_messages_with_boundary(messages, session_id="session_compact_v2", run_id="run_compact_v2", turn_id="turn_2", max_messages=3)  # 新增代码+CompactResumeStatus: 执行带边界的 compact；若没有这行代码，无法得到可审计边界。
            transcript_store = TranscriptV2Store(base_dir)  # 新增代码+CompactResumeStatus: 创建 transcript store；若没有这行代码，边界无法落盘。
            transcript_store.append_entry(session_id="session_compact_v2", run_id="run_compact_v2", turn_id="turn_2", event_type="compact_boundary", payload=boundary.to_dict())  # 新增代码+CompactResumeStatus: 写入 compact boundary 证据；若没有这行代码，resume loader 无法判断压缩点。
            SessionStore(base_dir).save_summary(SessionRecord(session_id="session_compact_v2", run_id="run_compact_v2", user_input="继续", messages=compacted_messages, final_answer="未完成"))  # 新增代码+CompactResumeStatus: 保存压缩后的 summary；若没有这行代码，resume loader 没有模型上下文入口。
            resume_context = ResumeLoader(base_dir).load("session_compact_v2")  # 新增代码+CompactResumeStatus: 加载恢复上下文；若没有这行代码，测试不会覆盖重启恢复。
            rendered_messages = "\n".join(str(message.get("content", "")) for message in resume_context.model_messages)  # 新增代码+CompactResumeStatus: 合并恢复消息文本；若没有这行代码，断言会重复遍历。
            self.assertTrue(resume_context.consistency["has_compact_boundary"])  # 新增代码+CompactResumeStatus: 断言恢复器识别 compact 边界；若没有这行代码，压缩恢复证据可能丢失。
            self.assertEqual(resume_context.last_boundary.boundary_uuid, boundary.boundary_uuid)  # 新增代码+CompactResumeStatus: 断言边界 id 可追踪；若没有这行代码，无法对应原始 transcript。
            self.assertIn("old-5", rendered_messages)  # 新增代码+CompactResumeStatus: 断言最新消息保留；若没有这行代码，恢复会丢最新上下文。
            self.assertIn("old-0", rendered_messages)  # 新增代码+CompactDeep: 断言旧消息可以进入压缩摘要；若没有这行代码，测试会把“可审计摘要”误判成 compact 失败。
            self.assertNotIn({"role": "user", "content": "old-0"}, resume_context.model_messages)  # 新增代码+CompactDeep: 断言旧消息没有作为独立历史消息重放；若没有这行代码，compact 可能把旧 turn 又塞回上下文。

    def test_status_snapshot_renderer_sdk_and_cli_share_one_state_source(self) -> None:  # 新增代码+CompactResumeStatus: 验证状态聚合、渲染、SDK、CLI 使用同一事实源；若没有这行代码，状态生态会分裂。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CompactResumeStatus: 创建隔离工作区；若没有这行代码，测试会污染真实 memory。
            workspace = Path(raw_dir)  # 新增代码+CompactResumeStatus: 规范化工作区路径；若没有这行代码，多个组件可能读写不同目录。
            from learning_agent.app.status_renderer import render_status_snapshot  # 新增代码+CompactResumeStatus: 导入终端状态渲染器；若没有这行代码，状态 UI 没有测试入口。
            from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+CompactResumeStatus: 导入状态事件 store；若没有这行代码，状态事件协议无法验收。
            from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+CompactResumeStatus: 导入状态快照聚合器；若没有这行代码，状态生态没有统一事实源。
            from learning_agent.sdk.status import get_status_snapshot, list_status_events  # 新增代码+CompactResumeStatus: 导入 SDK 状态函数；若没有这行代码，外部 agent 无法稳定读取状态。
            harness_store = HarnessStore(workspace / "memory" / "harness")  # 新增代码+CompactResumeStatus: 创建 harness store；若没有这行代码，快照没有 run 数据。
            harness_run = HarnessRun.create(run_id="status-run", prompt="状态验收", stages=[HarnessStage(name="阶段一", prompt="执行")])  # 新增代码+CompactResumeStatus: 构造测试 run；若没有这行代码，快照无法显示 run。
            harness_store.save_run(harness_run)  # 新增代码+CompactResumeStatus: 保存测试 run；若没有这行代码，聚合器读不到状态。
            RuntimeCommandQueue(workspace / "memory" / "runtime").enqueue_prompt("排队 prompt")  # 新增代码+CompactResumeStatus: 写入 runtime 命令；若没有这行代码，快照无法显示队列。
            TaskRegistry(workspace / "memory" / "tasks").create_task(task_id="status-task", prompt="后台任务", status="running")  # 新增代码+CompactResumeStatus: 写入任务状态；若没有这行代码，快照无法显示 task。
            status_event_store = StatusEventStore(workspace / "memory" / "status")  # 新增代码+CompactResumeStatus: 创建状态事件 store；若没有这行代码，事件协议没有落盘入口。
            status_event_store.append("status_probe", {"run_id": "status-run"})  # 新增代码+CompactResumeStatus: 写入状态事件；若没有这行代码，SDK list_events 没有数据。
            snapshot = build_status_snapshot(workspace)  # 新增代码+CompactResumeStatus: 聚合状态快照；若没有这行代码，后续渲染和 SDK 没有输入。
            rendered = render_status_snapshot(snapshot)  # 新增代码+CompactResumeStatus: 渲染人类可读状态；若没有这行代码，终端 UI 无法验收。
            sdk_snapshot = get_status_snapshot(workspace)  # 新增代码+CompactResumeStatus: 通过 SDK 读取同一快照；若没有这行代码，外部 agent 无法复用状态源。
            sdk_events = list_status_events(workspace, since_sequence=0)  # 新增代码+CompactResumeStatus: 通过 SDK 读取状态事件；若没有这行代码，外部 agent 无法增量观察。
            self.assertIn("status-run", json.dumps(snapshot, ensure_ascii=False))  # 新增代码+CompactResumeStatus: 断言 run 出现在结构化快照；若没有这行代码，run 可视化可能缺失。
            self.assertIn("status-task", rendered)  # 新增代码+CompactResumeStatus: 断言任务出现在终端文本；若没有这行代码，用户看不到后台任务。
            self.assertEqual(sdk_snapshot["workspace"], str(workspace))  # 新增代码+CompactResumeStatus: 断言 SDK 返回同一工作区；若没有这行代码，SDK 可能读错目录。
            self.assertEqual(sdk_events[-1]["event_type"], "status_probe")  # 新增代码+CompactResumeStatus: 断言 SDK 能读状态事件；若没有这行代码，事件订阅能力缺失。
            cli_output = io.StringIO()  # 新增代码+CompactResumeStatus: 准备捕获 CLI 输出；若没有这行代码，无法检查 snapshot 命令文本。
            with redirect_stdout(cli_output):  # 新增代码+CompactResumeStatus: 捕获 stdout；若没有这行代码，测试输出会被污染。
                exit_code = harness_cli_main(["snapshot", "--workspace", str(workspace)])  # 新增代码+CompactResumeStatus: 调用新增快照 CLI；若没有这行代码，CLI 状态生态没有验收。
            self.assertEqual(exit_code, 0)  # 新增代码+CompactResumeStatus: 断言 CLI 成功；若没有这行代码，后续文本断言可能掩盖失败。
            self.assertIn("LearningAgent Status", cli_output.getvalue())  # 新增代码+CompactResumeStatus: 断言 CLI 输出状态标题；若没有这行代码，用户可能看不到可读状态页。

    def test_status_tools_and_interactive_status_command_are_available(self) -> None:  # 新增代码+CompactResumeStatus: 验证模型状态工具和终端 /status 命令；若没有这行代码，状态生态只停留在 SDK。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CompactResumeStatus: 创建隔离工作区；若没有这行代码，测试会污染真实 agent 状态。
            workspace = Path(raw_dir)  # 新增代码+CompactResumeStatus: 规范化工作区路径；若没有这行代码，agent 和渲染器可能读写不同目录。
            from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+TerminalStatusUI: 导入状态事件 store；若没有这行代码，/events 终端命令没有可验证输入。
            schema_names = [str(schema.get("function", {}).get("name", "")) for schema in TOOL_SCHEMAS if isinstance(schema.get("function", {}), dict)]  # 新增代码+CompactResumeStatus: 提取全量内置 schema 名；若没有这行代码，无法确认模型可调用工具定义存在。
            self.assertIn("status_snapshot", schema_names)  # 新增代码+CompactResumeStatus: 断言状态快照工具进入 schema；若没有这行代码，模型无法调用状态快照。
            self.assertIn("session_resume", schema_names)  # 新增代码+CompactResumeStatus: 断言 session 恢复工具进入 schema；若没有这行代码，模型无法读取恢复上下文。
            self.assertIn("resume_report", schema_names)  # 新增代码+StatusToolsV2: 断言精简恢复报告工具进入 schema；若没有这行代码，模型无法自查 resume 是否安全。
            self.assertIn("run_status", schema_names)  # 新增代码+StatusToolsV2: 断言 run 状态工具进入 schema；若没有这行代码，模型无法直接定位长期任务阶段。
            self.assertIn("health_status", schema_names)  # 新增代码+StatusToolsV2: 断言健康状态工具进入 schema；若没有这行代码，模型无法自查 warning/verifier 风险。
            SessionStore(workspace / "memory" / "sessions").save_summary(SessionRecord(session_id="status-ui-session", run_id="status-ui-run", user_input="终端 UI 验收", messages=[{"role": "user", "content": "终端 UI 验收"}], final_answer="等待继续"))  # 新增代码+TerminalStatusUI: 写入可恢复 session；若没有这行代码，/sessions 和 /resume 终端命令只能显示空状态。
            StatusEventStore(workspace / "memory" / "status").append("status_probe", {"source": "terminal_ui"})  # 新增代码+TerminalStatusUI: 写入可见事件；若没有这行代码，/events 命令没有事件可显示。
            model = RecordingToolNameFakeModel(ModelMessage(text="STATUS_READY"))  # 新增代码+CompactResumeStatus: 创建确定性假模型；若没有这行代码，agent 可能请求真实模型。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+CompactResumeStatus: 创建真实 agent；若没有这行代码，工具执行和终端入口无法覆盖。
            tool_output = agent._execute_tool(ToolCall(name="status_snapshot", arguments={"format": "text"}))  # 新增代码+CompactResumeStatus: 直接执行状态快照工具；若没有这行代码，schema 存在但实现缺失不会暴露。
            self.assertIn("LearningAgent Status", tool_output)  # 新增代码+CompactResumeStatus: 断言工具返回可读状态；若没有这行代码，状态工具可能只返回空文本。
            resume_report_output = agent._execute_tool(ToolCall(name="resume_report", arguments={"session_id": "status-ui-session"}))  # 新增代码+StatusToolsV2: 执行精简恢复报告工具；若没有这行代码，resume_report 路由缺失不会暴露。
            self.assertIn("resume_state", resume_report_output)  # 新增代码+StatusToolsV2: 断言恢复报告包含决策状态；若没有这行代码，模型无法判断继续还是等待用户。
            run_status_output = agent._execute_tool(ToolCall(name="run_status", arguments={}))  # 新增代码+StatusToolsV2: 执行 run 状态工具；若没有这行代码，run_status 可能只是 schema 空壳。
            self.assertIn("current_turn", run_status_output)  # 新增代码+StatusToolsV2: 断言 run_status 返回当前 turn；若没有这行代码，模型仍要解析完整快照。
            health_status_output = agent._execute_tool(ToolCall(name="health_status", arguments={}))  # 新增代码+StatusToolsV2: 执行健康状态工具；若没有这行代码，health_status 路由缺失不会暴露。
            self.assertIn("health", health_status_output)  # 新增代码+StatusToolsV2: 断言健康报告包含 health；若没有这行代码，模型无法自查风险状态。
            terminal_output = io.StringIO()  # 新增代码+CompactResumeStatus: 准备捕获交互终端输出；若没有这行代码，/status 文本无法断言。
            with mock.patch("builtins.input", side_effect=["/status", "/events", "/sessions", "/resume status-ui-session", "/compact", "exit"]):  # 修改代码+TerminalStatusUI: 模拟用户执行全部状态命令后退出；若没有这行代码，新增终端命令不会被测试覆盖。
                with redirect_stdout(terminal_output):  # 新增代码+CompactResumeStatus: 捕获终端输出；若没有这行代码，测试会污染控制台。
                    run_interactive_session(agent=agent, workspace=workspace, visible_tools=["read"], max_turns=1, prompt_soft_token_limit=1000)  # 新增代码+CompactResumeStatus: 运行真实交互入口；若没有这行代码，/status 命令不会被生产路径验证。
            self.assertIn("LearningAgent Status", terminal_output.getvalue())  # 新增代码+CompactResumeStatus: 断言 /status 输出状态页；若没有这行代码，终端用户仍看不到状态生态。
            self.assertIn("Status Events", terminal_output.getvalue())  # 新增代码+TerminalStatusUI: 断言 /events 输出事件区块；若没有这行代码，事件流终端 UI 可能失效。
            self.assertIn("session_id=status-ui-session", terminal_output.getvalue())  # 新增代码+TerminalStatusUI: 断言 /sessions 输出可恢复 session；若没有这行代码，用户无法复制 resume id。
            self.assertIn("Resume Report", terminal_output.getvalue())  # 新增代码+TerminalStatusUI: 断言 /resume 输出恢复报告；若没有这行代码，恢复审计命令可能失效。
            self.assertIn("Compact / Resume", terminal_output.getvalue())  # 新增代码+TerminalStatusUI: 断言 /compact 输出压缩恢复状态；若没有这行代码，compact 状态无法真实终端查看。

    def test_http_bridge_exposes_status_snapshot_and_event_tail(self) -> None:  # 新增代码+CompactResumeStatus: 验证 HTTP bridge 暴露统一状态和事件流；若没有这行代码，外部 agent 只能读本地文件。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CompactResumeStatus: 创建隔离工作区；若没有这行代码，HTTP API 测试会污染真实 memory。
            workspace = Path(raw_dir)  # 新增代码+CompactResumeStatus: 规范化工作区路径；若没有这行代码，agent 和事件 store 可能读写不同目录。
            from learning_agent.sdk.status import get_health, get_sessions, load_resume_report  # 新增代码+StatusAPIV2: 导入 SDK v2 读取函数；若没有这行代码，HTTP 和 SDK 是否同源无法一起验收。
            from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+CompactResumeStatus: 导入状态事件 store；若没有这行代码，HTTP /events 没有可验证输入。
            SessionStore(workspace / "memory" / "sessions").save_summary(SessionRecord(session_id="http-session", run_id="http-run", user_input="HTTP 恢复验收", messages=[{"role": "user", "content": "HTTP 恢复验收"}], final_answer="等待继续"))  # 新增代码+StatusAPIV2: 写入真实 session summary；若没有这行代码，/sessions 和 /resume 没有可验证数据。
            status_store = StatusEventStore(workspace / "memory" / "status")  # 新增代码+StatusAPIV2: 创建状态事件 store 变量；若没有这行代码，后续多条事件写入会重复构造对象。
            status_store.append("status_probe", {"source": "http_test"})  # 新增代码+CompactResumeStatus: 写入一条事件作为 HTTP API 证据；若没有这行代码，/events 可能空结果也会误判成功。
            status_store.append("compact_started", {"source": "http_test"})  # 新增代码+StatusAPIV2: 写入另一类事件测试过滤；若没有这行代码，event_type 过滤可能只在单事件下误判通过。
            model = RecordingToolNameFakeModel(ModelMessage(text="HTTP_STATUS_READY"))  # 新增代码+CompactResumeStatus: 创建离线假模型；若没有这行代码，server 构造可能依赖真实模型。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+CompactResumeStatus: 创建真实 agent；若没有这行代码，bridge 没有 workspace 和工具池来源。
            server = create_command_bridge_server(agent=agent, host="127.0.0.1", port=0)  # 新增代码+CompactResumeStatus: 使用随机本机端口启动 bridge；若没有这行代码，测试可能和真实服务端口冲突。
            thread = threading.Thread(target=server.serve_forever, daemon=True)  # 新增代码+CompactResumeStatus: 准备后台 server 线程；若没有这行代码，测试会阻塞在 HTTP 服务。
            thread.start()  # 新增代码+CompactResumeStatus: 启动 HTTP bridge；若没有这行代码，client 无法连接状态端点。
            self.addCleanup(server.server_close)  # 新增代码+CompactResumeStatus: 测试结束关闭 socket；若没有这行代码，端口资源可能泄露。
            self.addCleanup(server.shutdown)  # 新增代码+CompactResumeStatus: 测试结束停止 server loop；若没有这行代码，后台线程可能残留。
            host, port = server.server_address  # 新增代码+CompactResumeStatus: 读取实际监听地址；若没有这行代码，client 不知道连接哪个随机端口。
            status_connection = http.client.HTTPConnection(host, port, timeout=5)  # 新增代码+CompactResumeStatus: 创建 /status 连接；若没有这行代码，无法验证真实 HTTP 协议。
            status_connection.request("GET", "/status")  # 新增代码+CompactResumeStatus: 请求状态快照端点；若没有这行代码，/status 端点不会被测试覆盖。
            status_response = status_connection.getresponse()  # 新增代码+CompactResumeStatus: 读取状态响应；若没有这行代码，无法断言状态码。
            status_payload = json.loads(status_response.read().decode("utf-8"))  # 新增代码+CompactResumeStatus: 解析状态 JSON；若没有这行代码，无法验证结构化输出。
            self.assertEqual(status_response.status, 200)  # 新增代码+CompactResumeStatus: 断言 /status 成功；若没有这行代码，404/500 可能被正文掩盖。
            self.assertEqual(status_payload["snapshot"]["workspace"], str(workspace))  # 新增代码+CompactResumeStatus: 断言状态快照来自同一工作区；若没有这行代码，API 可能读错目录。
            events_connection = http.client.HTTPConnection(host, port, timeout=5)  # 新增代码+CompactResumeStatus: 创建 /events 连接；若没有这行代码，无法验证事件流端点。
            events_connection.request("GET", "/events?since_sequence=0&limit=5")  # 新增代码+CompactResumeStatus: 请求增量事件端点；若没有这行代码，外部 watcher 场景没有测试覆盖。
            events_response = events_connection.getresponse()  # 新增代码+CompactResumeStatus: 读取事件响应；若没有这行代码，无法断言状态码。
            events_payload = json.loads(events_response.read().decode("utf-8"))  # 新增代码+CompactResumeStatus: 解析事件 JSON；若没有这行代码，无法检查事件内容。
            self.assertEqual(events_response.status, 200)  # 新增代码+CompactResumeStatus: 断言 /events 成功；若没有这行代码，事件 API 失败可能被忽略。
            self.assertEqual(events_payload["events"][-1]["event_type"], "compact_started")  # 修改代码+StatusAPIV2: 断言 API 返回最新事件事实源；若没有这行代码，/events 可能返回旁路数据。
            filtered_connection = http.client.HTTPConnection(host, port, timeout=5)  # 新增代码+StatusAPIV2: 创建过滤事件连接；若没有这行代码，event_type 参数没有真实 HTTP 验收。
            filtered_connection.request("GET", "/events?since_sequence=0&limit=5&event_type=status_probe")  # 新增代码+StatusAPIV2: 请求单类型事件过滤；若没有这行代码，外部 watcher 只能拿全量噪声。
            filtered_response = filtered_connection.getresponse()  # 新增代码+StatusAPIV2: 读取过滤事件响应；若没有这行代码，无法断言过滤端点状态码。
            filtered_payload = json.loads(filtered_response.read().decode("utf-8"))  # 新增代码+StatusAPIV2: 解析过滤事件 JSON；若没有这行代码，无法检查过滤结果。
            self.assertEqual(filtered_response.status, 200)  # 新增代码+StatusAPIV2: 断言过滤事件端点成功；若没有这行代码，过滤失败可能被内容掩盖。
            self.assertEqual([event["event_type"] for event in filtered_payload["events"]], ["status_probe"])  # 新增代码+StatusAPIV2: 断言只返回目标事件；若没有这行代码，SDK/API watcher 仍可能收到无关事件。
            sessions_connection = http.client.HTTPConnection(host, port, timeout=5)  # 新增代码+StatusAPIV2: 创建 /sessions 连接；若没有这行代码，session 列表端点没有真实验收。
            sessions_connection.request("GET", "/sessions")  # 新增代码+StatusAPIV2: 请求 session 列表；若没有这行代码，外部 agent 不能发现可恢复会话。
            sessions_response = sessions_connection.getresponse()  # 新增代码+StatusAPIV2: 读取 session 响应；若没有这行代码，无法确认端点是否成功。
            sessions_payload = json.loads(sessions_response.read().decode("utf-8"))  # 新增代码+StatusAPIV2: 解析 session JSON；若没有这行代码，无法检查 session 内容。
            self.assertEqual(sessions_response.status, 200)  # 新增代码+StatusAPIV2: 断言 /sessions 成功；若没有这行代码，404 可能被忽略。
            self.assertIn("http-session", sessions_payload["sessions"])  # 新增代码+StatusAPIV2: 断言 session 出现在 HTTP 列表；若没有这行代码，恢复入口可能不可发现。
            resume_connection = http.client.HTTPConnection(host, port, timeout=5)  # 新增代码+StatusAPIV2: 创建 /resume 连接；若没有这行代码，恢复报告端点没有真实验收。
            resume_connection.request("GET", "/resume?session_id=http-session")  # 新增代码+StatusAPIV2: 请求指定 session 的恢复报告；若没有这行代码，HTTP API 不能审计 resume。
            resume_response = resume_connection.getresponse()  # 新增代码+StatusAPIV2: 读取恢复响应；若没有这行代码，无法断言恢复端点状态码。
            resume_payload = json.loads(resume_response.read().decode("utf-8"))  # 新增代码+StatusAPIV2: 解析恢复 JSON；若没有这行代码，无法检查 repair report。
            self.assertEqual(resume_response.status, 200)  # 新增代码+StatusAPIV2: 断言 /resume 成功；若没有这行代码，恢复报告失败可能被忽略。
            self.assertEqual(resume_payload["resume"]["session_id"], "http-session")  # 新增代码+StatusAPIV2: 断言恢复报告来自目标 session；若没有这行代码，API 可能读错会话。
            runs_connection = http.client.HTTPConnection(host, port, timeout=5)  # 新增代码+StatusAPIV2: 创建 /runs 连接；若没有这行代码，run 观察端点没有真实验收。
            runs_connection.request("GET", "/runs")  # 新增代码+StatusAPIV2: 请求 run 列表；若没有这行代码，外部 agent 只能拉完整状态页。
            runs_response = runs_connection.getresponse()  # 新增代码+StatusAPIV2: 读取 run 响应；若没有这行代码，无法确认端点状态。
            runs_payload = json.loads(runs_response.read().decode("utf-8"))  # 新增代码+StatusAPIV2: 解析 run JSON；若没有这行代码，无法检查结构。
            self.assertEqual(runs_response.status, 200)  # 新增代码+StatusAPIV2: 断言 /runs 成功；若没有这行代码，run API 可能静默失效。
            self.assertTrue(runs_payload["ok"])  # 新增代码+StatusAPIV2: 断言 /runs 返回明确成功标记；若没有这行代码，调用方难以区分空列表和失败。
            health_connection = http.client.HTTPConnection(host, port, timeout=5)  # 新增代码+StatusAPIV2: 创建 /health 连接；若没有这行代码，健康端点 v2 没有验收。
            health_connection.request("GET", "/health")  # 新增代码+StatusAPIV2: 请求健康状态；若没有这行代码，外部监控无法确认状态生态健康。
            health_response = health_connection.getresponse()  # 新增代码+StatusAPIV2: 读取健康响应；若没有这行代码，无法断言健康端点状态码。
            health_payload = json.loads(health_response.read().decode("utf-8"))  # 新增代码+StatusAPIV2: 解析健康 JSON；若没有这行代码，无法检查 v2 health 字段。
            self.assertEqual(health_response.status, 200)  # 新增代码+StatusAPIV2: 断言 /health 成功；若没有这行代码，健康 API 失败可能被漏过。
            self.assertIn("health", health_payload)  # 新增代码+StatusAPIV2: 断言健康块出现在响应里；若没有这行代码，/health 只能证明进程活着。
            self.assertIn("http-session", get_sessions(workspace))  # 新增代码+StatusAPIV2: 断言 SDK sessions 与 HTTP 使用同一事实源；若没有这行代码，SDK 可能和 API 分裂。
            self.assertEqual(load_resume_report(workspace, "http-session")["resume"]["session_id"], "http-session")  # 新增代码+StatusAPIV2: 断言 SDK resume 报告可读取同一 session；若没有这行代码，外部 agent 不能稳定审计恢复。
            self.assertIn("state", get_health(workspace))  # 新增代码+StatusAPIV2: 断言 SDK health 返回结构化状态；若没有这行代码，控制方无法判断风险。

    def test_harness_cli_module_entrypoint_prints_status_snapshot(self) -> None:  # 新增代码+CompactResumeStatus: 验证 python -m 真实 CLI 入口输出状态；若没有这行代码，函数测试可能掩盖模块入口缺失。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+CompactResumeStatus: 创建隔离工作区；若没有这行代码，CLI 测试会污染真实 memory。
            workspace = Path(raw_dir)  # 新增代码+CompactResumeStatus: 规范化工作区路径；若没有这行代码，子进程参数可能不稳定。
            result = subprocess.run([sys.executable, "-m", "learning_agent.harness.cli", "snapshot", "--workspace", str(workspace)], cwd=Path(__file__).resolve().parents[2], text=True, capture_output=True, timeout=10)  # 新增代码+CompactResumeStatus: 运行真实模块入口；若没有这行代码，无法发现 __main__ 缺失。
            self.assertEqual(result.returncode, 0, result.stderr)  # 新增代码+CompactResumeStatus: 断言 CLI 退出成功；若没有这行代码，命令失败可能只表现为空输出。
            self.assertIn("LearningAgent Status", result.stdout)  # 新增代码+CompactResumeStatus: 断言 CLI 输出人类可读状态；若没有这行代码，空 stdout 会误判通过。


if __name__ == "__main__":  # 新增代码+CompactResumeStatus: 支持直接运行本测试文件；若没有这行代码，单文件排查不方便。
    unittest.main()  # 新增代码+CompactResumeStatus: 直接运行时启动 unittest；若没有这行代码，python 文件本身不会执行测试。
