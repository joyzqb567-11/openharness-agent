"""长任务 harness 的持久化、队列、阶段验收、恢复和状态输出测试。"""  # 新增代码+LongTaskHarness: 说明本测试文件锁定长任务 harness 能力；若没有这行代码，维护者不清楚这里验证什么。

from __future__ import annotations  # 新增代码+LongTaskHarness: 延迟解析类型注解；若没有这行代码，后续前向引用类型更容易受定义顺序影响。

import io  # 新增代码+LongTaskHarness: 捕获 CLI 输出需要内存文本缓冲区；若没有这行代码，测试无法检查 status 命令打印内容。
import tempfile  # 新增代码+LongTaskHarness: 创建临时 harness 存储目录；若没有这行代码，测试会污染真实 memory/harness。
import unittest  # 新增代码+LongTaskHarness: 使用项目现有 unittest 框架；若没有这行代码，测试无法被 discover 发现。
from contextlib import redirect_stdout  # 新增代码+LongTaskHarness: 临时接管 stdout；若没有这行代码，CLI 测试只能肉眼观察输出。
from pathlib import Path  # 新增代码+LongTaskHarness: 用 Path 管理临时目录和 artifact 路径；若没有这行代码，路径拼接会更脆弱。

from learning_agent.harness import HarnessQueue, HarnessRun, HarnessStage, HarnessStore, RecoveryPolicy, StageVerifier, render_harness_status  # 新增代码+LongTaskHarness: 导入长任务 harness 公开 API；若没有这行代码，红灯无法证明 harness 包缺失。
from learning_agent.harness.agent_executor import AgentStageExecutor  # 新增代码+HarnessCliAgentExecution: 导入真实 agent 阶段执行适配器；若没有这行代码，无法证明 harness 能接入 LearningAgent.run。
from learning_agent.harness.cli import main as harness_cli_main  # 新增代码+LongTaskHarness: 导入 CLI 入口；若没有这行代码，外部 agent 无法通过命令检查状态。
from learning_agent.harness.runner import HarnessRunner  # 新增代码+LongTaskHarness: 导入阶段 runner；若没有这行代码，测试无法验证失败后自动继续。


class LongTaskHarnessTests(unittest.TestCase):  # 新增代码+LongTaskHarness: 定义长任务 harness 测试类；若没有这行代码，测试方法没有统一容器。
    def test_store_persists_run_queue_and_events_across_restarts(self) -> None:  # 新增代码+LongTaskHarness: 验证状态、队列和事件能跨 store 重建；若没有这行代码，重启恢复能力没有测试。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+LongTaskHarness: 使用临时目录隔离持久化文件；若没有这行代码，真实 harness 状态会被测试污染。
            base_dir = Path(raw_dir)  # 新增代码+LongTaskHarness: 转成 Path 传给 store；若没有这行代码，路径类型不统一。
            store = HarnessStore(base_dir)  # 新增代码+LongTaskHarness: 创建第一份 store；若没有这行代码，无法写入初始状态。
            run = HarnessRun.create(run_id="run-store", prompt="完成长任务", stages=[HarnessStage(name="stage-a", prompt="第一阶段")])  # 新增代码+LongTaskHarness: 创建带阶段的 run；若没有这行代码，队列没有可持久化对象。
            queue = HarnessQueue(store)  # 新增代码+LongTaskHarness: 创建队列管理器；若没有这行代码，无法测试 enqueue/lease。
            queue.enqueue(run)  # 新增代码+LongTaskHarness: 把 run 写入持久队列；若没有这行代码，重启后没有任务可恢复。
            store.append_event("run-store", "planned", {"stage_count": 1})  # 新增代码+LongTaskHarness: 写入一条事件；若没有这行代码，事件回放能力没有测试输入。
            restarted_store = HarnessStore(base_dir)  # 新增代码+LongTaskHarness: 模拟进程重启后重新创建 store；若没有这行代码，测试只证明内存可用。
            restarted_queue = HarnessQueue(restarted_store)  # 新增代码+LongTaskHarness: 使用重启后的 store 创建队列；若没有这行代码，无法证明队列从磁盘恢复。
            leased = restarted_queue.lease_next(worker_id="worker-1", lease_seconds=60)  # 新增代码+LongTaskHarness: 租约领取下一个任务；若没有这行代码，不能证明任务可继续执行。
            self.assertIsNotNone(leased)  # 新增代码+LongTaskHarness: 断言重启后仍能领到任务；若没有这行代码，状态丢失不会被发现。
            self.assertEqual(leased.run_id, "run-store")  # 新增代码+LongTaskHarness: 断言领取的是原任务；若没有这行代码，队列可能返回错误任务。
            event_types = [event["event_type"] for event in restarted_store.read_events("run-store")]  # 修改代码+LongTaskHarness: 收集重启后能回放出来的全部事件类型；若没有这行代码，测试会错误假设事件只能有一条且顺序固定。
            self.assertIn("planned", event_types)  # 修改代码+LongTaskHarness: 断言手动写入的 planned 事件没有在重启后丢失；若没有这行代码，审计证据丢失也可能不被发现。

    def test_stage_verifier_requires_marker_and_artifact(self) -> None:  # 新增代码+LongTaskHarness: 验证阶段验收可以检查文本标记和 artifact；若没有这行代码，阶段性验收只剩口头描述。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+LongTaskHarness: 使用临时目录保存验收 artifact；若没有这行代码，测试会污染真实文件。
            base_dir = Path(raw_dir)  # 新增代码+LongTaskHarness: 转成 Path 传给 verifier；若没有这行代码，artifact 路径不清楚。
            stage = HarnessStage(name="verify", prompt="生成结果", success_markers=["PASS"], required_artifacts=["done.txt"])  # 新增代码+LongTaskHarness: 定义验收规则；若没有这行代码，verifier 没有检查目标。
            verifier = StageVerifier(base_dir)  # 新增代码+LongTaskHarness: 创建阶段验证器；若没有这行代码，无法执行确定性断言。
            failed = verifier.verify(stage, "PASS")  # 新增代码+LongTaskHarness: 只给文本标记但不给文件；若没有这行代码，无法证明缺 artifact 会失败。
            self.assertFalse(failed.passed)  # 新增代码+LongTaskHarness: 断言缺文件时不通过；若没有这行代码，artifact 门禁可能形同虚设。
            (base_dir / "done.txt").write_text("ok", encoding="utf-8")  # 新增代码+LongTaskHarness: 创建必需 artifact；若没有这行代码，后续通过分支没有真实文件。
            passed = verifier.verify(stage, "输出包含 PASS")  # 新增代码+LongTaskHarness: 同时满足文本和文件断言；若没有这行代码，无法证明通过路径。
            self.assertTrue(passed.passed)  # 新增代码+LongTaskHarness: 断言满足条件后通过；若没有这行代码，verifier 可能一直失败。
            self.assertIn("marker:PASS", passed.checks)  # 新增代码+LongTaskHarness: 断言报告包含标记检查；若没有这行代码，审计报告缺少细节。
            self.assertIn("artifact:done.txt", passed.checks)  # 新增代码+LongTaskHarness: 断言报告包含文件检查；若没有这行代码，artifact 审计不可追踪。

    def test_queue_lease_heartbeat_complete_and_fail_are_persistent(self) -> None:  # 新增代码+LongTaskHarness: 验证队列租约、心跳、完成和失败都会落盘；若没有这行代码，长任务队列安全边界缺少测试。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+LongTaskHarness: 用临时目录隔离队列状态；若没有这行代码，测试可能污染真实 harness 队列。
            base_dir = Path(raw_dir)  # 新增代码+LongTaskHarness: 转成 Path 供 store 使用；若没有这行代码，路径类型不统一。
            store = HarnessStore(base_dir)  # 新增代码+LongTaskHarness: 创建持久化 store；若没有这行代码，队列没有落盘位置。
            queue = HarnessQueue(store)  # 新增代码+LongTaskHarness: 创建队列管理器；若没有这行代码，测试不能调用 lease/heartbeat。
            run = HarnessRun.create(run_id="run-lease", prompt="租约测试", stages=[HarnessStage(name="one", prompt="执行")])  # 新增代码+LongTaskHarness: 创建一个可排队任务；若没有这行代码，队列没有可领取对象。
            queue.enqueue(run)  # 新增代码+LongTaskHarness: 把任务放入队列；若没有这行代码，lease_next 应该找不到任务。
            leased = queue.lease_next(worker_id="worker-a", lease_seconds=60)  # 新增代码+LongTaskHarness: 第一个 worker 领取任务；若没有这行代码，租约逻辑没有起点。
            self.assertIsNotNone(leased)  # 新增代码+LongTaskHarness: 断言第一个 worker 能领取；若没有这行代码，排队失败不会被发现。
            self.assertIsNone(queue.lease_next(worker_id="worker-b", lease_seconds=60))  # 新增代码+LongTaskHarness: 断言第二个 worker 不能重复领取未过期任务；若没有这行代码，重复执行风险不会被测试发现。
            heartbeat = queue.heartbeat(run_id="run-lease", worker_id="worker-a", lease_seconds=120)  # 新增代码+LongTaskHarness: 同一 worker 刷新租约；若没有这行代码，长阶段可能被误判为超时。
            self.assertEqual(heartbeat.lease_worker, "worker-a")  # 新增代码+LongTaskHarness: 断言租约仍属于原 worker；若没有这行代码，心跳可能错误改 owner。
            completed = queue.complete(heartbeat)  # 新增代码+LongTaskHarness: 标记任务完成；若没有这行代码，终态落盘没有测试。
            self.assertEqual(completed.status, "completed")  # 新增代码+LongTaskHarness: 断言完成状态正确；若没有这行代码，完成后仍可能被重新领取。
            self.assertEqual(store.load_run("run-lease").status, "completed")  # 新增代码+LongTaskHarness: 断言完成状态已落盘；若没有这行代码，只在内存完成的问题不会暴露。
            failed_run = HarnessRun.create(run_id="run-fail", prompt="失败测试", stages=[HarnessStage(name="one", prompt="执行")])  # 新增代码+LongTaskHarness: 创建第二个任务用于失败路径；若没有这行代码，fail 方法没有独立测试对象。
            queue.enqueue(failed_run)  # 新增代码+LongTaskHarness: 把失败路径任务放入队列；若没有这行代码，fail 只能作用在未保存对象上。
            failed = queue.fail(failed_run, "人工失败")  # 新增代码+LongTaskHarness: 标记任务失败并写入原因；若没有这行代码，失败终态无法验证。
            self.assertEqual(failed.status, "failed")  # 新增代码+LongTaskHarness: 断言失败状态正确；若没有这行代码，失败任务可能继续运行。
            self.assertEqual(store.load_run("run-fail").failure_reason, "人工失败")  # 新增代码+LongTaskHarness: 断言失败原因已持久化；若没有这行代码，用户看不到为什么停下。

    def test_runner_retries_recoverable_failure_and_resumes_from_checkpoint(self) -> None:  # 新增代码+LongTaskHarness: 验证可恢复失败会自动重试且不重跑已完成阶段；若没有这行代码，长任务恢复能力没有行为证明。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+LongTaskHarness: 使用临时目录隔离 runner 状态；若没有这行代码，测试会污染真实 harness。
            base_dir = Path(raw_dir)  # 新增代码+LongTaskHarness: 转成 Path 供 store 使用；若没有这行代码，路径操作不稳定。
            store = HarnessStore(base_dir)  # 新增代码+LongTaskHarness: 创建持久 store；若没有这行代码，runner 无处保存 checkpoint。
            queue = HarnessQueue(store)  # 新增代码+LongTaskHarness: 创建持久队列；若没有这行代码，runner 无法领取任务。
            run = HarnessRun.create(run_id="run-retry", prompt="两阶段任务", endpoints=["primary", "backup"], stages=[HarnessStage(name="collect", prompt="收集", success_markers=["COLLECTED"], max_attempts=2), HarnessStage(name="verify", prompt="验证", success_markers=["VERIFIED"], max_attempts=1)])  # 新增代码+LongTaskHarness: 创建需要重试和继续的两阶段任务；若没有这行代码，恢复场景没有输入。
            queue.enqueue(run)  # 新增代码+LongTaskHarness: 把任务放入队列；若没有这行代码，runner 没有可执行任务。
            calls: list[str] = []  # 新增代码+LongTaskHarness: 记录 executor 被调用的阶段；若没有这行代码，无法证明已完成阶段没有重复。

            def executor(active_run: HarnessRun, stage: HarnessStage) -> str:  # 新增代码+LongTaskHarness: 定义测试 executor；若没有这行代码，runner 无法模拟模型/工具执行。
                calls.append(stage.name)  # 新增代码+LongTaskHarness: 记录本次阶段名；若没有这行代码，测试无法观察执行顺序。
                if stage.name == "collect" and calls.count("collect") == 1:  # 新增代码+LongTaskHarness: 第一次 collect 故意模拟端点超时；若没有这行代码，恢复分支不会触发。
                    raise RuntimeError("endpoint timeout")  # 新增代码+LongTaskHarness: 抛出可恢复错误；若没有这行代码，RecoveryPolicy 没有真实错误输入。
                if stage.name == "collect":  # 新增代码+LongTaskHarness: collect 第二次返回成功标记；若没有这行代码，重试后无法通过验收。
                    return f"{active_run.current_endpoint()} COLLECTED"  # 新增代码+LongTaskHarness: 返回带 endpoint 和成功标记的输出；若没有这行代码，测试无法验证端点轮换。
                return "VERIFIED"  # 新增代码+LongTaskHarness: 第二阶段直接返回成功标记；若没有这行代码，整条 run 无法完成。

            runner = HarnessRunner(store=store, executor=executor, verifier=StageVerifier(base_dir), recovery_policy=RecoveryPolicy())  # 新增代码+LongTaskHarness: 创建 runner 并注入 executor/verifier/recovery；若没有这行代码，无法执行端到端长任务。
            result = runner.run_once(worker_id="worker-2")  # 新增代码+LongTaskHarness: 执行一次队列任务；若没有这行代码，测试不会触发自动继续。
            self.assertIsNotNone(result)  # 新增代码+LongTaskHarness: 断言 runner 返回执行结果；若没有这行代码，空执行不会被发现。
            self.assertEqual(result.status, "completed")  # 新增代码+LongTaskHarness: 断言最终完成；若没有这行代码，自动继续可能失败却未被发现。
            self.assertEqual(calls, ["collect", "collect", "verify"])  # 新增代码+LongTaskHarness: 断言只重试失败阶段；若没有这行代码，runner 可能重跑全部阶段。
            self.assertEqual(result.endpoint_index, 1)  # 新增代码+LongTaskHarness: 断言 recoverable failure 后切到备用端点；若没有这行代码，端点恢复能力没有验证。
            self.assertEqual(len(result.stages[0].attempts), 2)  # 新增代码+LongTaskHarness: 断言失败阶段有两次尝试记录；若没有这行代码，审计无法看到重试历史。
            self.assertTrue(result.stages[1].acceptance.passed)  # 新增代码+LongTaskHarness: 断言最后阶段验收通过；若没有这行代码，完成状态可能不可信。

    def test_status_renderer_and_cli_expose_auditable_state(self) -> None:  # 新增代码+LongTaskHarness: 验证状态文本和 CLI 可被外部 agent 读取；若没有这行代码，任务状态可视化没有回归保护。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+LongTaskHarness: 使用临时目录隔离 CLI store；若没有这行代码，测试会读取真实 harness 状态。
            base_dir = Path(raw_dir)  # 新增代码+LongTaskHarness: 转成 Path 传给 store；若没有这行代码，状态路径不清楚。
            store = HarnessStore(base_dir)  # 新增代码+LongTaskHarness: 创建 store；若没有这行代码，CLI 没有数据来源。
            run = HarnessRun.create(run_id="run-status", prompt="状态测试", stages=[HarnessStage(name="only", prompt="执行", success_markers=["OK"])])  # 新增代码+LongTaskHarness: 创建测试 run；若没有这行代码，状态输出没有对象。
            run.status = "running"  # 新增代码+LongTaskHarness: 设置运行中状态；若没有这行代码，状态输出无法展示 active run。
            run.stages[0].status = "completed"  # 新增代码+LongTaskHarness: 设置阶段完成；若没有这行代码，阶段状态展示没有内容。
            run.stages[0].acceptance = StageVerifier(base_dir).verify(run.stages[0], "OK")  # 新增代码+LongTaskHarness: 写入验收结果；若没有这行代码，状态输出缺少 acceptance。
            store.save_run(run)  # 新增代码+LongTaskHarness: 保存 run 供渲染和 CLI 读取；若没有这行代码，CLI 无法跨进程查看。
            store.append_event("run-status", "stage_completed", {"stage": "only"})  # 新增代码+LongTaskHarness: 保存最后事件；若没有这行代码，状态输出无法显示最近动作。
            rendered = render_harness_status(store.load_run("run-status"), store.read_events("run-status"))  # 新增代码+LongTaskHarness: 渲染人类可读状态；若没有这行代码，无法验证可视化文本。
            self.assertIn("run-status", rendered)  # 新增代码+LongTaskHarness: 断言状态里包含 run id；若没有这行代码，用户无法定位任务。
            self.assertIn("only", rendered)  # 新增代码+LongTaskHarness: 断言状态里包含阶段名；若没有这行代码，用户不知道跑到哪一步。
            self.assertIn("acceptance=passed", rendered)  # 新增代码+LongTaskHarness: 断言状态里包含验收结论；若没有这行代码，任务完成可信度不可见。
            output = io.StringIO()  # 新增代码+LongTaskHarness: 创建 stdout 捕获缓冲区；若没有这行代码，CLI 输出无法断言。
            with redirect_stdout(output):  # 新增代码+LongTaskHarness: 临时捕获 CLI 打印；若没有这行代码，测试会把输出打到真实终端。
                exit_code = harness_cli_main(["status", "--store", str(base_dir), "--run-id", "run-status"])  # 新增代码+LongTaskHarness: 调用 status CLI；若没有这行代码，外部控制入口没有测试。
            self.assertEqual(exit_code, 0)  # 新增代码+LongTaskHarness: 断言 CLI 成功退出；若没有这行代码，外部 agent 可能拿到失败码。
            self.assertIn("run-status", output.getvalue())  # 新增代码+LongTaskHarness: 断言 CLI 输出包含 run id；若没有这行代码，命令可能打印了空状态。

    def test_cli_enqueue_creates_persisted_run_with_stages_and_markers(self) -> None:  # 新增代码+HarnessCliAgentExecution: 验证 enqueue 命令能创建带阶段和 marker 的持久任务；若没有这行代码，外部 agent 仍只能写 Python 创建任务。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+HarnessCliAgentExecution: 使用临时目录隔离 CLI 创建的状态；若没有这行代码，测试会污染真实 harness store。
            base_dir = Path(raw_dir)  # 新增代码+HarnessCliAgentExecution: 转成 Path 供 store 和 CLI 使用；若没有这行代码，路径类型不统一。
            output = io.StringIO()  # 新增代码+HarnessCliAgentExecution: 准备捕获 enqueue 的 stdout；若没有这行代码，测试无法断言命令输出。
            with redirect_stdout(output):  # 新增代码+HarnessCliAgentExecution: 捕获 CLI 输出；若没有这行代码，run id 会直接打到测试终端。
                exit_code = harness_cli_main(["enqueue", "--store", str(base_dir), "--run-id", "run-cli", "--prompt", "总任务", "--stage", "plan::写计划", "--stage", "verify::做验证", "--success-marker", "plan=PLAN_OK", "--success-marker", "verify=VERIFY_OK"])  # 新增代码+HarnessCliAgentExecution: 调用目标 enqueue 命令；若没有这行代码，红灯不会覆盖新 CLI 行为。
            stored = HarnessStore(base_dir).load_run("run-cli")  # 新增代码+HarnessCliAgentExecution: 从磁盘读回任务；若没有这行代码，无法证明 CLI 真正持久化。
            self.assertEqual(exit_code, 0)  # 新增代码+HarnessCliAgentExecution: 断言 enqueue 命令成功退出；若没有这行代码，外部 agent 可能拿到错误码却未被发现。
            self.assertIn("run-cli", output.getvalue())  # 新增代码+HarnessCliAgentExecution: 断言命令输出 run id；若没有这行代码，外部 agent 不知道后续查哪个任务。
            self.assertEqual([stage.name for stage in stored.stages], ["plan", "verify"])  # 新增代码+HarnessCliAgentExecution: 断言阶段顺序持久化；若没有这行代码，长任务可能丢阶段或乱序。
            self.assertEqual(stored.stages[0].success_markers, ["PLAN_OK"])  # 新增代码+HarnessCliAgentExecution: 断言第一阶段 marker 已写入；若没有这行代码，阶段验收可能没有门禁。
            self.assertEqual(stored.stages[1].success_markers, ["VERIFY_OK"])  # 新增代码+HarnessCliAgentExecution: 断言第二阶段 marker 已写入；若没有这行代码，后续 run 可能假完成。

    def test_cli_run_echo_executes_queued_run_and_status_reports_completed(self) -> None:  # 新增代码+HarnessCliAgentExecution: 验证 run 命令能执行队列中的任务并输出完成状态；若没有这行代码，CLI 只能查看不能推进任务。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+HarnessCliAgentExecution: 使用临时目录隔离执行状态；若没有这行代码，测试会污染真实 harness store。
            base_dir = Path(raw_dir)  # 新增代码+HarnessCliAgentExecution: 转成 Path 传给 store；若没有这行代码，路径操作不统一。
            enqueue_output = io.StringIO()  # 修改代码+HarnessCliAgentExecution: 捕获 enqueue 输出避免测试终端出现噪音；若没有这行代码，回归输出会混入 run id。
            with redirect_stdout(enqueue_output):  # 修改代码+HarnessCliAgentExecution: 临时接管 enqueue stdout；若没有这行代码，测试无法保持干净输出。
                enqueue_code = harness_cli_main(["enqueue", "--store", str(base_dir), "--run-id", "run-echo", "--prompt", "总任务", "--stage", "only::请输出 ECHO_OK", "--success-marker", "only=ECHO_OK"])  # 修改代码+HarnessCliAgentExecution: 先通过 CLI 创建一个 echo 可通过的任务；若没有这行代码，run 命令没有输入。
            self.assertEqual(enqueue_code, 0)  # 新增代码+HarnessCliAgentExecution: 断言 enqueue 成功；若没有这行代码，后续失败原因可能不是 run 命令。
            output = io.StringIO()  # 新增代码+HarnessCliAgentExecution: 准备捕获 run 输出；若没有这行代码，无法断言状态文本。
            with redirect_stdout(output):  # 新增代码+HarnessCliAgentExecution: 捕获 run 命令打印；若没有这行代码，测试输出会污染终端。
                run_code = harness_cli_main(["run", "--store", str(base_dir), "--executor", "echo", "--worker-id", "worker-cli"])  # 新增代码+HarnessCliAgentExecution: 执行目标 run 命令；若没有这行代码，红灯不会覆盖 CLI 执行入口。
            stored = HarnessStore(base_dir).load_run("run-echo")  # 新增代码+HarnessCliAgentExecution: 读取执行后的任务；若没有这行代码，无法验证状态已落盘。
            self.assertEqual(run_code, 0)  # 新增代码+HarnessCliAgentExecution: 断言 run 命令成功退出；若没有这行代码，外部 agent 可能误判执行结果。
            self.assertEqual(stored.status, "completed")  # 新增代码+HarnessCliAgentExecution: 断言任务最终完成；若没有这行代码，run 命令可能只领取不执行。
            self.assertTrue(stored.stages[0].acceptance.passed)  # 新增代码+HarnessCliAgentExecution: 断言阶段验收通过；若没有这行代码，完成状态可能缺少真实门禁。
            self.assertIn("acceptance=passed", output.getvalue())  # 新增代码+HarnessCliAgentExecution: 断言 run 输出可读验收状态；若没有这行代码，用户仍要手动翻 JSON。

    def test_agent_stage_executor_calls_learning_agent_run_with_stage_prompt(self) -> None:  # 新增代码+HarnessCliAgentExecution: 验证真实 agent executor 会调用 agent.run(stage.prompt)；若没有这行代码，harness 与 LearningAgent 的接入没有行为证明。
        class FakeAgent:  # 新增代码+HarnessCliAgentExecution: 定义轻量假 agent；若没有这个类，测试会误调用真实模型。
            def __init__(self) -> None:  # 新增代码+HarnessCliAgentExecution: 初始化调用记录；若没有这行代码，测试无法确认传入参数。
                self.calls: list[tuple[str, int | None]] = []  # 新增代码+HarnessCliAgentExecution: 保存 prompt 和 max_turns；若没有这行代码，executor 调用细节不可见。

            def run(self, prompt: str, max_turns: int | None = None) -> str:  # 新增代码+HarnessCliAgentExecution: 模拟 LearningAgent.run 接口；若没有这行代码，AgentStageExecutor 无法被隔离测试。
                self.calls.append((prompt, max_turns))  # 新增代码+HarnessCliAgentExecution: 记录调用参数；若没有这行代码，测试只能看返回值。
                return "AGENT_OK"  # 新增代码+HarnessCliAgentExecution: 返回成功标记；若没有这行代码，executor 没有输出。

        fake_agent = FakeAgent()  # 新增代码+HarnessCliAgentExecution: 创建假 agent；若没有这行代码，executor 没有可调用对象。
        executor = AgentStageExecutor(agent=fake_agent, max_turns=7)  # 新增代码+HarnessCliAgentExecution: 创建真实适配器但注入假 agent；若没有这行代码，无法验证适配器行为。
        run = HarnessRun.create(run_id="run-agent", prompt="总任务", stages=[HarnessStage(name="agent", prompt="阶段 prompt")])  # 新增代码+HarnessCliAgentExecution: 创建 run 参数；若没有这行代码，executor 调用缺少上下文对象。
        answer = executor(run, run.stages[0])  # 新增代码+HarnessCliAgentExecution: 调用 executor；若没有这行代码，测试不会覆盖 __call__ 行为。
        self.assertEqual(answer, "AGENT_OK")  # 新增代码+HarnessCliAgentExecution: 断言返回 agent.run 的回答；若没有这行代码，输出转发错误不会被发现。
        self.assertEqual(fake_agent.calls, [("阶段 prompt", 7)])  # 新增代码+HarnessCliAgentExecution: 断言使用阶段 prompt 和 max_turns；若没有这行代码，executor 可能误用总任务 prompt。


if __name__ == "__main__":  # 新增代码+LongTaskHarness: 支持直接运行本测试文件；若没有这行代码，单文件调试不方便。
    unittest.main()  # 新增代码+LongTaskHarness: 直接运行时启动 unittest；若没有这行代码，python 文件本身不会执行测试。
