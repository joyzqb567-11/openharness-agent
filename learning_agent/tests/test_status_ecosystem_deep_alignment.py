"""ClaudeCode 级状态生态深度对齐红线测试。"""  # 新增代码+DeepStatus: 说明本文件锁定状态协议、SDK watch 和快照 v2；若没有这行代码，维护者可能只看基础 /status。

from __future__ import annotations  # 新增代码+DeepStatus: 延迟解析类型注解；若没有这行代码，复杂类型引用更容易受顺序影响。

import tempfile  # 新增代码+DeepStatus: 创建隔离工作区；若没有这行代码，测试会污染真实状态事件。
import json  # 新增代码+MigrationCompat: 手工写入旧 JSONL 事件；若没有这行代码，测试无法构造旧格式迁移样本。
import unittest  # 新增代码+DeepStatus: 使用项目现有 unittest 框架；若没有这行代码，测试无法被 discover 发现。
from pathlib import Path  # 新增代码+DeepStatus: 用 Path 管理工作区；若没有这行代码，路径拼接更脆弱。

from learning_agent.core.compact import CompactBoundary  # 新增代码+MigrationCompat: 导入 compact boundary 兼容解析器；若没有这行代码，旧 compact 数据无法被测试覆盖。
from learning_agent.core.resume_loader import ResumeLoader  # 新增代码+MigrationCompat: 导入真实恢复加载器；若没有这行代码，迁移测试无法证明 resume 链路能读取旧数据。
from learning_agent.core.session import SessionRecord, SessionStore  # 新增代码+MigrationCompat: 导入 session summary store；若没有这行代码，迁移测试无法构造可恢复会话。
from learning_agent.core.transcript_v2 import TranscriptV2Store  # 新增代码+MigrationCompat: 导入 transcript v2 store；若没有这行代码，旧 compact boundary 无法落入恢复证据链。
from learning_agent.runtime.status_events import StatusEventStore  # 新增代码+DeepStatus: 导入状态事件事实源；若没有这行代码，测试无法验证事件协议 v2。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+DeepStatus: 导入状态快照聚合器；若没有这行代码，测试无法验证统一状态视图。
from learning_agent.sdk.status import list_status_events, watch_status_events  # 新增代码+DeepStatus: 导入 SDK 事件读取入口；若没有这行代码，外部 agent 观察能力无法被测试。


class StatusEcosystemDeepAlignmentTests(unittest.TestCase):  # 新增代码+DeepStatus: 定义状态生态深度对齐测试集合；若没有这行代码，测试方法没有容器。
    def test_status_events_have_v2_identity_fields_and_sdk_filters_by_type(self) -> None:  # 新增代码+DeepStatus: 验证事件带 run/session/turn/schema 且 SDK 可过滤；若没有这行代码，状态生态仍只是无上下文日志。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DeepStatus: 创建临时工作区；若没有这行代码，测试会写入真实 memory。
            workspace = Path(raw_dir)  # 新增代码+DeepStatus: 规范化工作区路径；若没有这行代码，各组件可能读错目录。
            store = StatusEventStore(workspace / "memory" / "status")  # 新增代码+DeepStatus: 创建状态事件 store；若没有这行代码，无法写入测试事件。
            first_event = store.append("model_request_started", {"message_count": 3}, session_id="session_status", run_id="run_status", turn_id="turn_0")  # 新增代码+DeepStatus: 写入带身份字段的模型事件；若没有这行代码，事件协议 v2 无法验证。
            store.append("compact_completed", {"boundary_uuid": "compact_1"}, session_id="session_status", run_id="run_status", turn_id="turn_0")  # 新增代码+DeepStatus: 写入 compact 事件；若没有这行代码，事件类型过滤没有第二类输入。
            payload = first_event.to_dict()  # 新增代码+DeepStatus: 转成 JSON dict；若没有这行代码，断言会访问实现细节。
            self.assertEqual(payload["schema_version"], 2)  # 新增代码+DeepStatus: 断言事件协议版本；若没有这行代码，外部 SDK 无法兼容演进。
            self.assertEqual(payload["session_id"], "session_status")  # 新增代码+DeepStatus: 断言 session_id 顶层可见；若没有这行代码，外部 agent 要解析 payload。
            self.assertEqual(payload["run_id"], "run_status")  # 新增代码+DeepStatus: 断言 run_id 顶层可见；若没有这行代码，状态事件无法和 run 对齐。
            self.assertEqual(payload["turn_id"], "turn_0")  # 新增代码+DeepStatus: 断言 turn_id 顶层可见；若没有这行代码，恢复分析无法定位轮次。
            filtered_events = list_status_events(workspace, since_sequence=0, event_type="compact_completed")  # 新增代码+DeepStatus: 用 SDK 过滤 compact 事件；若没有这行代码，SDK 只能全量读取。
            self.assertEqual([event["event_type"] for event in filtered_events], ["compact_completed"])  # 新增代码+DeepStatus: 断言过滤结果只包含目标类型；若没有这行代码，watcher 还要自己过滤。
            watched_events = list(watch_status_events(workspace, since_sequence=0, event_types={"model_request_started"}, poll_interval_seconds=0.01, max_polls=1))  # 新增代码+DeepStatus: 用 SDK watch 过滤模型事件；若没有这行代码，断点续读能力无法被测试。
            self.assertEqual([event["event_type"] for event in watched_events], ["model_request_started"])  # 新增代码+DeepStatus: 断言 watch 也支持过滤；若没有这行代码，长任务观察会收到无关事件。

    def test_status_snapshot_v2_exposes_current_sections_and_health(self) -> None:  # 新增代码+DeepStatus: 验证快照 v2 有 current/compact/resume/health；若没有这行代码，状态页无法判断卡在哪里。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DeepStatus: 创建隔离工作区；若没有这行代码，状态快照会读取真实项目。
            workspace = Path(raw_dir)  # 新增代码+DeepStatus: 规范化工作区路径；若没有这行代码，各 store 路径可能不一致。
            store = StatusEventStore(workspace / "memory" / "status")  # 新增代码+DeepStatus: 创建状态事件 store；若没有这行代码，快照没有事件输入。
            store.append("run_started", {"user_input": "状态生态验收"}, session_id="session_current", run_id="run_current", turn_id="run")  # 新增代码+DeepStatus: 写入当前 run 起点；若没有这行代码，current_run 无法推导。
            store.append("turn_accepted", {"checkpoint_uuid": "entry_user"}, session_id="session_current", run_id="run_current", turn_id="turn_0")  # 新增代码+DeepStatus: 写入当前 turn 事件；若没有这行代码，current_turn 无法推导。
            store.append("compact_completed", {"boundary": {"boundary_uuid": "compact_latest"}}, session_id="session_current", run_id="run_current", turn_id="turn_0")  # 新增代码+DeepStatus: 写入 compact 事件；若没有这行代码，compact 区块无法展示最新边界。
            store.append("resume_needs_review", {"reason": "missing_tool_result"}, session_id="session_current", run_id="run_current", turn_id="turn_0")  # 新增代码+DeepStatus: 写入恢复风险事件；若没有这行代码，resume 区块无法显示需复核状态。
            snapshot = build_status_snapshot(workspace)  # 新增代码+DeepStatus: 构建状态快照；若没有这行代码，测试无法覆盖聚合器。
            self.assertEqual(snapshot["current_run"]["run_id"], "run_current")  # 新增代码+DeepStatus: 断言 current_run 从事件流推导；若没有这行代码，外部 agent 不知道当前任务。
            self.assertEqual(snapshot["current_turn"]["turn_id"], "turn_0")  # 新增代码+DeepStatus: 断言 current_turn 从事件流推导；若没有这行代码，恢复分析不知道轮次。
            self.assertEqual(snapshot["compact"]["latest_boundary_uuid"], "compact_latest")  # 新增代码+DeepStatus: 断言 compact 区块显示最新边界；若没有这行代码，状态页只能显示事件尾巴。
            self.assertEqual(snapshot["resume"]["state"], "resume_needs_review")  # 新增代码+DeepStatus: 断言 resume 区块显示风险状态；若没有这行代码，用户不知道是否可安全继续。
            self.assertIn("warnings", snapshot["health"])  # 新增代码+DeepStatus: 断言 health 区块存在 warnings；若没有这行代码，坏数据和迁移风险没有落点。

    def test_legacy_status_event_and_compact_boundary_remain_readable(self) -> None:  # 新增代码+MigrationCompat: 验证旧状态事件和旧 compact boundary 可读取；若没有这行代码，升级可能破坏历史 memory。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+MigrationCompat: 创建隔离工作区；若没有这行代码，兼容测试会污染真实状态。
            workspace = Path(raw_dir)  # 新增代码+MigrationCompat: 规范化工作区路径；若没有这行代码，各 store 可能读写不同目录。
            status_dir = workspace / "memory" / "status"  # 新增代码+MigrationCompat: 定位状态事件目录；若没有这行代码，旧 events.jsonl 没有固定位置。
            status_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+MigrationCompat: 创建状态目录；若没有这行代码，手工写旧事件会失败。
            legacy_event = {"sequence": 1, "timestamp": "legacy-time", "event_type": "compact_completed", "payload": {"session_id": "legacy-session", "run_id": "legacy-run", "turn_id": "turn_0", "boundary": {"boundary_uuid": "legacy-boundary"}}}  # 新增代码+MigrationCompat: 构造没有顶层 v2 身份字段的旧事件；若没有这行代码，兼容路径没有输入。
            (status_dir / "events.jsonl").write_text(json.dumps(legacy_event, ensure_ascii=False) + "\n", encoding="utf-8")  # 新增代码+MigrationCompat: 写入旧格式事件；若没有这行代码，StatusEvent.from_dict 兼容逻辑不会被验证。
            events = StatusEventStore(status_dir).list_events(since_sequence=0)  # 新增代码+MigrationCompat: 通过新 store 读取旧事件；若没有这行代码，测试只写不读。
            self.assertEqual(events[0].session_id, "legacy-session")  # 新增代码+MigrationCompat: 断言 session_id 可从旧 payload 回填；若没有这行代码，旧事件会失去会话归属。
            self.assertEqual(events[0].run_id, "legacy-run")  # 新增代码+MigrationCompat: 断言 run_id 可从旧 payload 回填；若没有这行代码，旧事件无法对齐 run。
            snapshot = build_status_snapshot(workspace)  # 新增代码+MigrationCompat: 用统一快照读取旧事件；若没有这行代码，UI/SDK 兼容没有被覆盖。
            self.assertEqual(snapshot["compact"]["latest_boundary_uuid"], "legacy-boundary")  # 新增代码+MigrationCompat: 断言旧 compact 事件仍能显示边界；若没有这行代码，状态页可能漏掉历史 compact。
            old_boundary = CompactBoundary.from_dict({"boundary_uuid": "old-boundary", "session_id": "legacy-session", "run_id": "legacy-run", "turn_id": "turn_0", "original_message_count": 4, "removed_message_count": 2, "retained_message_count": 2, "summary_text": "旧摘要"})  # 新增代码+MigrationCompat: 构造缺少 v2 字段的旧 compact boundary；若没有这行代码，旧边界解析不会被验证。
            self.assertEqual(old_boundary.schema_version, 1)  # 新增代码+MigrationCompat: 断言旧边界默认 v1；若没有这行代码，新旧数据无法区分。
            session_base = workspace / "memory" / "sessions"  # 新增代码+MigrationCompat: 定位 session 根目录；若没有这行代码，summary 和 transcript 路径不统一。
            TranscriptV2Store(session_base).append_entry(session_id="legacy-session", run_id="legacy-run", turn_id="turn_0", event_type="compact_boundary", payload=old_boundary.to_dict())  # 新增代码+MigrationCompat: 把旧边界写入 transcript；若没有这行代码，ResumeLoader 旧边界链路没有证据。
            SessionStore(session_base).save_summary(SessionRecord(session_id="legacy-session", run_id="legacy-run", user_input="继续旧任务", messages=[{"role": "system", "content": "旧摘要"}], final_answer="未完成"))  # 新增代码+MigrationCompat: 写入最小旧 session summary；若没有这行代码，ResumeLoader 没有恢复入口。
            context = ResumeLoader(session_base).load("legacy-session")  # 新增代码+MigrationCompat: 用新恢复器读取旧 session；若没有这行代码，迁移兼容不会覆盖 resume。
            self.assertTrue(context.consistency["has_compact_boundary"])  # 新增代码+MigrationCompat: 断言恢复器识别旧 compact boundary；若没有这行代码，旧会话恢复可能丢压缩点。
            self.assertEqual(context.last_boundary.boundary_uuid, "old-boundary")  # 新增代码+MigrationCompat: 断言旧边界 id 保留；若没有这行代码，审计链可能断开。


if __name__ == "__main__":  # 新增代码+DeepStatus: 支持直接运行本测试；若没有这行代码，单文件排查不方便。
    unittest.main()  # 新增代码+DeepStatus: 直接运行时启动 unittest；若没有这行代码，python 文件本身不会执行测试。
