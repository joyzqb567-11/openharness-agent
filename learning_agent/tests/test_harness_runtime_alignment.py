"""ClaudeCode 对齐版 harness runtime 的源码行为测试。"""  # 新增代码+HarnessRuntimeAlignment: 说明本文件专门锁定 ClaudeCode 等价 harness 能力；若没有这行代码，维护者不清楚这些测试为什么存在。

from __future__ import annotations  # 新增代码+HarnessRuntimeAlignment: 延迟解析类型注解；若没有这行代码，后续测试辅助类型在旧解释顺序下更容易出错。

import copy  # 新增代码+HarnessQueueDrainRed: 深拷贝模型收到的 messages；若没有这行代码，测试无法稳定证明模型当时看到了什么上下文。
import io  # 新增代码+HarnessRuntimeAlignment: 捕获 CLI 输出需要内存文本缓冲区；若没有这行代码，测试无法断言状态命令输出。
import re  # 新增代码+HarnessRuntimeAlignment: 从工具返回文本提取 task_id；若没有这行代码，测试只能脆弱地按固定行号切割。
import tempfile  # 新增代码+HarnessRuntimeAlignment: 为每个测试创建隔离目录；若没有这行代码，测试会污染真实 memory/harness。
import unittest  # 新增代码+HarnessRuntimeAlignment: 使用项目现有 unittest 测试框架；若没有这行代码，测试不会被 discover 发现。
from contextlib import redirect_stdout  # 新增代码+HarnessRuntimeAlignment: 临时捕获 CLI print；若没有这行代码，CLI 测试无法检查输出文本。
from pathlib import Path  # 新增代码+HarnessRuntimeAlignment: 用 Path 管理测试工作区和持久化目录；若没有这行代码，Windows 路径拼接会更脆弱。

from learning_agent.core.agent import LearningAgent  # 新增代码+HarnessRuntimeAlignment: 导入真实 agent 类；若没有这行代码，无法证明真实主循环接入 harness。
from learning_agent.core.messages import ModelMessage, ToolCall  # 新增代码+HarnessRuntimeAlignment: 导入模型消息和工具调用对象；若没有这行代码，测试无法驱动 agent 和工具路径。
from learning_agent.harness.cli import main as harness_cli_main  # 新增代码+HarnessRuntimeAlignment: 导入 harness CLI 入口；若没有这行代码，状态/API 对齐能力没有测试。
from learning_agent.harness.models import HarnessAttempt, HarnessRun, HarnessStage  # 修改代码+HarnessStatusAudit: 导入尝试记录、run/stage 模型；若没有这行代码，状态 CLI 无法被测试锁定阶段输出可见性。
from learning_agent.harness.store import HarnessStore  # 新增代码+HarnessRuntimeAlignment: 导入 harness store；若没有这行代码，测试无法检查真实落盘状态。
from learning_agent.harness.verifier import StageVerifier  # 新增代码+HarnessRuntimeAlignment: 导入阶段验收器；若没有这行代码，增强 verifier 无法被行为锁定。
from learning_agent.runtime.command_queue import RuntimeCommandQueue  # 新增代码+HarnessRuntimeAlignment: 导入运行时命令队列；若没有这行代码，ClaudeCode messageQueueManager 对齐测试会失败。
from learning_agent.runtime.poller import TaskPoller  # 新增代码+HarnessRuntimeAlignment: 导入任务轮询器；若没有这行代码，watchdog 和通知回灌没有测试入口。
from learning_agent.runtime.resume import InterruptedRunResumer  # 新增代码+HarnessRuntimeAlignment: 导入中断恢复器；若没有这行代码，interrupted turn resume 无法测试。
from learning_agent.runtime.task_output import TaskOutputStore  # 新增代码+HarnessRuntimeAlignment: 导入任务输出文件管理器；若没有这行代码，长输出治理没有测试入口。
from learning_agent.runtime.task_registry import TaskRegistry  # 新增代码+HarnessRuntimeAlignment: 导入持久任务登记表；若没有这行代码，task 只能停留在内存表。
from learning_agent.tests.support import RecordingToolNameFakeModel  # 新增代码+HarnessRuntimeAlignment: 导入固定回答假模型；若没有这行代码，测试会误调用真实模型。


class RecordingMessagesFakeModel:  # 新增代码+HarnessQueueDrainRed: 记录真实主循环传给模型的 messages；若没有这个类，测试只能看队列文件而不能证明模型是否看见通知。
    def __init__(self, response_text: str = "QUEUE_DRAIN_OK") -> None:  # 新增代码+HarnessQueueDrainRed: 初始化固定回答文本；若没有这行代码，agent.run 无法稳定结束。
        self.response_text = response_text  # 新增代码+HarnessQueueDrainRed: 保存模型最终回答；若没有这行代码，chat 无法返回可断言文本。
        self.received_messages: list[list[dict[str, object]]] = []  # 新增代码+HarnessQueueDrainRed: 保存每次模型请求看到的消息快照；若没有这行代码，测试无法检查上下文。

    def chat(self, messages: list[dict[str, object]], tools: list[dict[str, object]]) -> ModelMessage:  # 新增代码+HarnessQueueDrainRed: 模拟模型 chat 接口；若没有这行代码，LearningAgent 无法调用假模型。
        del tools  # 新增代码+HarnessQueueDrainRed: 本测试只关心消息上下文而不是工具列表；若没有这行代码，未使用参数的意图不清楚。
        self.received_messages.append(copy.deepcopy(messages))  # 新增代码+HarnessQueueDrainRed: 记录本轮模型看到的完整 messages；若没有这行代码，后续断言会被后续追加消息污染。
        return ModelMessage(text=self.response_text)  # 新增代码+HarnessQueueDrainRed: 返回固定最终回答让 run 正常收束；若没有这行代码，测试会卡在模型层。


class HarnessRuntimeAlignmentTests(unittest.TestCase):  # 新增代码+HarnessRuntimeAlignment: 定义 ClaudeCode 对齐测试集合；若没有这行代码，测试方法没有统一容器。
    def _flatten_model_messages(self, model: RecordingMessagesFakeModel) -> str:  # 新增代码+HarnessQueueDrainRed: 把模型收到的消息内容合并成便于断言的文本；若没有这行代码，每个测试都会重复遍历 messages。
        return "\n".join(str(message.get("content", "")) for batch in model.received_messages for message in batch)  # 新增代码+HarnessQueueDrainRed: 返回所有模型输入文本；若没有这行代码，断言很难直接检查 task/resume 是否可见。

    def test_runtime_command_queue_merges_prompts_and_survives_restart(self) -> None:  # 新增代码+RuntimeCommandQueue: 验证 prompt 合并、优先级和磁盘恢复；若没有这行代码，主队列能力没有红线。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RuntimeCommandQueue: 创建临时 runtime 目录；若没有这行代码，队列状态会写进真实项目。
            queue_dir = Path(raw_dir) / "runtime"  # 新增代码+RuntimeCommandQueue: 给命令队列单独目录；若没有这行代码，测试文件会和其他状态混在一起。
            queue = RuntimeCommandQueue(queue_dir)  # 新增代码+RuntimeCommandQueue: 创建第一份队列实例；若没有这行代码，无法写入初始命令。
            queue.enqueue_prompt("第一条用户输入")  # 新增代码+RuntimeCommandQueue: 写入第一条 prompt；若没有这行代码，合并行为缺少输入。
            queue.enqueue_task_notification({"task_id": "task-1", "status": "completed"})  # 新增代码+RuntimeCommandQueue: 写入 later 级任务通知；若没有这行代码，优先级排序没有对照项。
            queue.enqueue_prompt("第二条用户输入")  # 新增代码+RuntimeCommandQueue: 写入第二条 prompt；若没有这行代码，无法证明 prompt 会批量合并。
            restarted = RuntimeCommandQueue(queue_dir)  # 新增代码+RuntimeCommandQueue: 重新创建队列模拟进程重启；若没有这行代码，只能证明内存行为。
            prompt_command = restarted.dequeue_next()  # 新增代码+RuntimeCommandQueue: 取下一条应该优先执行的命令；若没有这行代码，无法验证调度结果。
            self.assertIsNotNone(prompt_command)  # 新增代码+RuntimeCommandQueue: 断言重启后仍有命令；若没有这行代码，持久化丢失不会暴露。
            self.assertEqual(prompt_command.mode, "prompt")  # 新增代码+RuntimeCommandQueue: 断言用户 prompt 优先于 later 通知；若没有这行代码，通知可能饿死用户输入。
            self.assertIn("第一条用户输入", prompt_command.payload["text"])  # 新增代码+RuntimeCommandQueue: 断言第一条 prompt 被合并；若没有这行代码，合并漏项不会被发现。
            self.assertIn("第二条用户输入", prompt_command.payload["text"])  # 新增代码+RuntimeCommandQueue: 断言第二条 prompt 被合并；若没有这行代码，批量 prompt 能力不可信。
            restarted.mark_completed(prompt_command.command_id)  # 新增代码+RuntimeCommandQueue: 标记 prompt 命令完成；若没有这行代码，事件生命周期无法验收。
            notification_command = restarted.dequeue_next()  # 新增代码+RuntimeCommandQueue: 再取下一条命令；若没有这行代码，任务通知分支没有验证。
            self.assertIsNotNone(notification_command)  # 新增代码+RuntimeCommandQueue: 断言通知命令仍在队列；若没有这行代码，later 命令可能被 prompt 合并误删。
            self.assertEqual(notification_command.mode, "task_notification")  # 新增代码+RuntimeCommandQueue: 断言第二条是任务通知；若没有这行代码，通知回灌顺序没有证明。
            event_types = [event["event_type"] for event in restarted.read_events()]  # 新增代码+RuntimeCommandQueue: 读取队列事件类型；若没有这行代码，ack/started/completed 事件不可审计。
            self.assertIn("command_queued", event_types)  # 新增代码+RuntimeCommandQueue: 断言入队事件存在；若没有这行代码，排查时不知道命令何时进入。
            self.assertIn("command_started", event_types)  # 新增代码+RuntimeCommandQueue: 断言开始事件存在；若没有这行代码，运行时无法追踪命令是否被消费。
            self.assertIn("command_completed", event_types)  # 新增代码+RuntimeCommandQueue: 断言完成事件存在；若没有这行代码，命令生命周期无法收束。

    def test_real_run_drains_task_notification_into_next_model_turn_without_task_output(self) -> None:  # 新增代码+HarnessQueueDrainRed: 锁定后台任务通知必须自动进入下一轮模型上下文；若没有这行代码，回灌缺口会再次被普通队列单测掩盖。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+HarnessQueueDrainRed: 创建隔离工作区；若没有这行代码，测试会污染真实 memory/runtime。
            workspace = Path(raw_dir)  # 新增代码+HarnessQueueDrainRed: 规范化工作区路径；若没有这行代码，agent 和 registry 可能写到不同位置。
            queue = RuntimeCommandQueue(workspace / "memory" / "runtime")  # 新增代码+HarnessQueueDrainRed: 创建真实 runtime 队列；若没有这行代码，任务通知没有回灌通道。
            registry = TaskRegistry(workspace / "memory" / "tasks", command_queue=queue)  # 新增代码+HarnessQueueDrainRed: 创建带队列的任务登记表；若没有这行代码，complete_task 不会写 task_notification。
            registry.create_task(task_id="task_notify_red", prompt="生成通知", status="running")  # 新增代码+HarnessQueueDrainRed: 创建运行中任务记录；若没有这行代码，完成通知没有任务来源。
            registry.complete_task("task_notify_red", output="TASK_NOTIFY_VISIBLE", usage={"tokens": 3})  # 新增代码+HarnessQueueDrainRed: 完成任务并写入通知；若没有这行代码，下一轮没有待消费通知。
            model = RecordingMessagesFakeModel(response_text="NOTIFICATION_TURN_DONE")  # 新增代码+HarnessQueueDrainRed: 创建会记录模型输入的假模型；若没有这行代码，无法证明模型是否看见通知。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+HarnessQueueDrainRed: 创建真实 agent 走真实 run 入口；若没有这行代码，测试无法覆盖主循环。
            answer = agent.run("请根据后台任务结果继续。", max_turns=1)  # 新增代码+HarnessQueueDrainRed: 触发下一轮真实 run；若没有这行代码，队列不会有机会被主循环消费。
            flattened_messages = self._flatten_model_messages(model)  # 新增代码+HarnessQueueDrainRed: 汇总模型收到的上下文；若没有这行代码，后续断言无法读取输入文本。
            self.assertEqual(answer, "NOTIFICATION_TURN_DONE")  # 新增代码+HarnessQueueDrainRed: 确认 run 仍返回模型最终文本；若没有这行代码，主循环兼容性可能被破坏。
            self.assertIn("TASK_NOTIFY_VISIBLE", flattened_messages)  # 新增代码+HarnessQueueDrainRed: 断言后台任务输出自动进入模型上下文；若没有这行代码，手动 task_output 缺口不会暴露。
            self.assertIn("task_notify_red", flattened_messages)  # 新增代码+HarnessQueueDrainRed: 断言模型能看到 task_id；若没有这行代码，通知不可追踪到具体任务。

    def test_real_run_consumes_resume_interrupted_command(self) -> None:  # 新增代码+HarnessQueueDrainRed: 锁定恢复命令必须被真实 run 消费；若没有这行代码，resume 只入队不执行的问题会被遗漏。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+HarnessQueueDrainRed: 创建隔离目录；若没有这行代码，恢复状态会污染真实 memory。
            workspace = Path(raw_dir)  # 新增代码+HarnessQueueDrainRed: 规范化测试工作区；若没有这行代码，store 和 queue 路径可能不一致。
            store = HarnessStore(workspace / "memory" / "harness")  # 新增代码+HarnessQueueDrainRed: 创建真实 harness store；若没有这行代码，无法模拟 interrupted run。
            queue = RuntimeCommandQueue(workspace / "memory" / "runtime")  # 新增代码+HarnessQueueDrainRed: 创建真实 runtime queue；若没有这行代码，恢复器没有命令写入位置。
            run = HarnessRun.create(run_id="resume-red-run", prompt="原始长任务 RESUME_ORIGINAL", stages=[HarnessStage(name="done", prompt="已完成"), HarnessStage(name="pending", prompt="未完成")])  # 新增代码+HarnessQueueDrainRed: 构造含已完成阶段的中断 run；若没有这行代码，无法验证恢复上下文和阶段语义。
            run.status = "running"  # 新增代码+HarnessQueueDrainRed: 模拟崩溃时 run 仍在运行；若没有这行代码，恢复器不会处理。
            run.current_stage_index = 1  # 新增代码+HarnessQueueDrainRed: 指向第二个未完成阶段；若没有这行代码，恢复器无法知道从哪里继续。
            run.stages[0].status = "completed"  # 新增代码+HarnessQueueDrainRed: 标记第一阶段已完成；若没有这行代码，恢复测试无法保护不重跑语义。
            run.stages[1].status = "running"  # 新增代码+HarnessQueueDrainRed: 标记第二阶段中断；若没有这行代码，恢复命令缺少 needs_review 目标。
            store.save_run(run)  # 新增代码+HarnessQueueDrainRed: 保存中断状态；若没有这行代码，恢复器扫描不到 run。
            InterruptedRunResumer(store=store, command_queue=queue).enqueue_interrupted_runs()  # 新增代码+HarnessQueueDrainRed: 把 interrupted run 写入恢复命令；若没有这行代码，真实 run 没有 resume 命令可消费。
            model = RecordingMessagesFakeModel(response_text="RESUME_TURN_DONE")  # 新增代码+HarnessQueueDrainRed: 创建记录输入的假模型；若没有这行代码，无法证明恢复上下文进入模型。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+HarnessQueueDrainRed: 创建真实 agent；若没有这行代码，恢复命令不会走真实 run 入口。
            answer = agent.run("继续处理恢复队列。", max_turns=1)  # 新增代码+HarnessQueueDrainRed: 触发真实 run 消费恢复命令；若没有这行代码，恢复命令只会停在队列。
            flattened_messages = self._flatten_model_messages(model)  # 新增代码+HarnessQueueDrainRed: 汇总模型收到的上下文；若没有这行代码，无法断言 resume 内容。
            self.assertEqual(answer, "RESUME_TURN_DONE")  # 新增代码+HarnessQueueDrainRed: 确认 run 仍正常返回；若没有这行代码，恢复接入可能破坏兼容 API。
            self.assertIn("resume-red-run", flattened_messages)  # 新增代码+HarnessQueueDrainRed: 断言恢复 run_id 进入模型上下文；若没有这行代码，模型不知道恢复哪个任务。
            self.assertIn("RESUME_ORIGINAL", flattened_messages)  # 新增代码+HarnessQueueDrainRed: 断言原始任务目标进入模型上下文；若没有这行代码，模型无法继续原任务。

    def test_runtime_commands_are_attached_before_completion_event(self) -> None:  # 新增代码+HarnessQueueDrainRed: 锁定命令必须先进入模型上下文再标记完成；若没有这行代码，队列可能假完成。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+HarnessQueueDrainRed: 创建隔离工作区；若没有这行代码，事件日志会污染真实 memory。
            workspace = Path(raw_dir)  # 新增代码+HarnessQueueDrainRed: 规范化路径；若没有这行代码，agent 和 harness store 可能写到不同目录。
            model = RecordingMessagesFakeModel(response_text="ATTACHMENT_DONE")  # 新增代码+HarnessQueueDrainRed: 创建固定回答模型；若没有这行代码，run 无法稳定结束。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+HarnessQueueDrainRed: 创建真实 agent；若没有这行代码，测试不会覆盖真实 runtime。
            agent.run("验证命令 attach 顺序。", max_turns=1)  # 新增代码+HarnessQueueDrainRed: 执行一次真实 run；若没有这行代码，harness 事件不会产生。
            store = HarnessStore(workspace / "memory" / "harness")  # 新增代码+HarnessQueueDrainRed: 打开 harness store；若没有这行代码，无法读取事件顺序。
            run_id = store.list_run_ids()[0]  # 新增代码+HarnessQueueDrainRed: 取得本次 run id；若没有这行代码，read_events 不知道读哪个 run。
            event_types = [event["event_type"] for event in store.read_events(run_id)]  # 新增代码+HarnessQueueDrainRed: 读取 harness 事件类型序列；若没有这行代码，无法检查 attach 事件。
            self.assertIn("runtime_commands_attached", event_types)  # 新增代码+HarnessQueueDrainRed: 断言命令被附加到模型上下文的证据存在；若没有这行代码，命令完成可能只是队列状态变化。
            self.assertLess(event_types.index("runtime_commands_attached"), event_types.index("run_completed"))  # 新增代码+HarnessQueueDrainRed: 断言 attach 发生在完成前；若没有这行代码，事件顺序不能证明模型先看见命令。

    def test_learning_agent_run_creates_durable_harness_session(self) -> None:  # 新增代码+HarnessSessionRuntime: 验证真实 agent.run 会进入 durable harness；若没有这行代码，真实终端仍可能绕过 harness。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+HarnessSessionRuntime: 创建隔离工作区；若没有这行代码，测试会污染真实 memory 目录。
            workspace = Path(raw_dir)  # 新增代码+HarnessSessionRuntime: 规范化工作区路径；若没有这行代码，agent 初始化路径不稳定。
            model = RecordingToolNameFakeModel(ModelMessage(text="ALIGNMENT_READY"))  # 新增代码+HarnessSessionRuntime: 创建直接回答的假模型；若没有这行代码，测试会依赖真实模型。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+HarnessSessionRuntime: 创建真实 agent 并允许权限；若没有这行代码，无法覆盖 agent.run 入口。
            answer = agent.run("请返回 ALIGNMENT_READY", max_turns=1)  # 新增代码+HarnessSessionRuntime: 调用兼容 run 入口；若没有这行代码，测试不会触发真实主循环。
            self.assertEqual(answer, "ALIGNMENT_READY")  # 新增代码+HarnessSessionRuntime: 断言旧 run 返回值保持兼容；若没有这行代码，接入 runtime 可能破坏调用方。
            harness_store = HarnessStore(workspace / "memory" / "harness")  # 新增代码+HarnessSessionRuntime: 打开默认 harness 状态目录；若没有这行代码，无法检查是否落盘。
            run_ids = harness_store.list_run_ids()  # 新增代码+HarnessSessionRuntime: 列出真实 run id；若没有这行代码，无法证明主循环创建了 durable run。
            self.assertEqual(len(run_ids), 1)  # 新增代码+HarnessSessionRuntime: 断言一次 agent.run 只创建一个 harness run；若没有这行代码，重复落盘或未落盘都不易发现。
            stored_run = harness_store.load_run(run_ids[0])  # 新增代码+HarnessSessionRuntime: 读取刚才的 run；若没有这行代码，只知道有文件不知道状态。
            self.assertEqual(stored_run.status, "completed")  # 新增代码+HarnessSessionRuntime: 断言 run 已收束；若没有这行代码，中断恢复可能误判已完成任务。
            self.assertEqual(stored_run.prompt, "请返回 ALIGNMENT_READY")  # 新增代码+HarnessSessionRuntime: 断言用户输入被持久化；若没有这行代码，resume 后不知道原任务。
            self.assertEqual(stored_run.stages[0].status, "completed")  # 修改代码+HarnessSessionRuntime: 断言落盘阶段也完成；若没有这行代码，真实终端可能出现 run 完成但 stage 仍 pending 的假完成。
            self.assertTrue(stored_run.stages[0].acceptance.passed)  # 修改代码+HarnessSessionRuntime: 断言阶段验收结果随 run 一起落盘；若没有这行代码，状态页无法证明阶段是真的通过。
            self.assertIn("ALIGNMENT_READY", stored_run.stages[0].checkpoint)  # 修改代码+HarnessSessionRuntime: 断言阶段 checkpoint 保存最终回答摘要；若没有这行代码，恢复和审计缺少阶段结果。
            event_types = [event["event_type"] for event in harness_store.read_events(stored_run.run_id)]  # 新增代码+HarnessSessionRuntime: 读取 harness 事件流；若没有这行代码，无法证明 run_events 已桥接到 harness。
            self.assertIn("runtime_command_queued", event_types)  # 新增代码+HarnessSessionRuntime: 断言主循环 prompt 进入 runtime queue；若没有这行代码，真实入口仍没有队列。
            self.assertIn("agent_event", event_types)  # 新增代码+HarnessSessionRuntime: 断言 AgentEvent 被镜像到 harness；若没有这行代码，transcript 和 harness 仍是两套系统。
            self.assertIn("run_completed", event_types)  # 新增代码+HarnessSessionRuntime: 断言完成事件进入 harness；若没有这行代码，状态页无法知道 run 已结束。

    def test_interrupted_run_resumer_requeues_running_harness_run(self) -> None:  # 新增代码+InterruptedResume: 验证 running 状态可被下次启动恢复；若没有这行代码，中断恢复只能停留在计划里。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+InterruptedResume: 创建隔离目录；若没有这行代码，恢复测试会污染真实 harness 状态。
            base_dir = Path(raw_dir)  # 新增代码+InterruptedResume: 转成 Path 供 store 使用；若没有这行代码，路径传参不稳定。
            store = HarnessStore(base_dir / "harness")  # 新增代码+InterruptedResume: 创建 harness store；若没有这行代码，无法保存 interrupted run。
            queue = RuntimeCommandQueue(base_dir / "runtime")  # 新增代码+InterruptedResume: 创建 runtime 命令队列；若没有这行代码，恢复器没有入队目标。
            run = HarnessRun.create(run_id="run-interrupted", prompt="长任务", stages=[HarnessStage(name="turn", prompt="继续执行")])  # 新增代码+InterruptedResume: 构造一个模拟中断的 run；若没有这行代码，恢复器没有输入。
            run.status = "running"  # 新增代码+InterruptedResume: 模拟进程崩溃前任务仍在 running；若没有这行代码，恢复器不应处理。
            run.stages[0].status = "running"  # 新增代码+InterruptedResume: 模拟当前阶段未完成；若没有这行代码，needs_review 标记没有目标。
            store.save_run(run)  # 新增代码+InterruptedResume: 把中断状态落盘；若没有这行代码，恢复器重启后看不到任务。
            restored_count = InterruptedRunResumer(store=store, command_queue=queue).enqueue_interrupted_runs()  # 新增代码+InterruptedResume: 执行恢复扫描；若没有这行代码，测试不会触发重入队。
            self.assertEqual(restored_count, 1)  # 新增代码+InterruptedResume: 断言找到一个 interrupted run；若没有这行代码，恢复漏扫不会暴露。
            resumed_command = RuntimeCommandQueue(base_dir / "runtime").dequeue_next()  # 新增代码+InterruptedResume: 从重启后的队列取恢复命令；若没有这行代码，无法证明恢复命令持久化。
            self.assertIsNotNone(resumed_command)  # 新增代码+InterruptedResume: 断言恢复命令存在；若没有这行代码，入队失败不会被发现。
            self.assertEqual(resumed_command.mode, "resume_interrupted")  # 新增代码+InterruptedResume: 断言命令类型是恢复中断；若没有这行代码，队列无法区分普通 prompt。
            restored_run = store.load_run("run-interrupted")  # 新增代码+InterruptedResume: 重新读取 run 状态；若没有这行代码，无法检查恢复器是否更新状态。
            self.assertEqual(restored_run.status, "queued")  # 新增代码+InterruptedResume: 断言 run 已重新入队；若没有这行代码，任务可能仍卡在 running。
            self.assertEqual(restored_run.stages[0].status, "needs_review")  # 新增代码+InterruptedResume: 断言未完成阶段需要审查；若没有这行代码，副作用工具可能被自动重放。

    def test_task_registry_persists_agent_task_and_enqueues_notification(self) -> None:  # 新增代码+DurableTaskRegistry: 验证 task 工具写入持久 registry 和通知队列；若没有这行代码，子任务仍可能只在内存。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DurableTaskRegistry: 创建隔离工作区；若没有这行代码，任务记录会污染真实 memory。
            workspace = Path(raw_dir)  # 新增代码+DurableTaskRegistry: 规范化工作区；若没有这行代码，registry 默认路径不稳定。
            model = RecordingToolNameFakeModel(ModelMessage(text="子任务结果 TASK_DONE"))  # 新增代码+DurableTaskRegistry: 创建子 agent 会返回的固定结果；若没有这行代码，task 工具会依赖真实模型。
            agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+DurableTaskRegistry: 创建真实 agent；若没有这行代码，无法覆盖 _task 集成。
            task_text = agent._execute_tool(ToolCall(name="task", arguments={"prompt": "生成 TASK_DONE", "allowed_tools": ["read_file"], "max_turns": 1}))  # 新增代码+DurableTaskRegistry: 通过真实工具分发创建子任务；若没有这行代码，registry 集成不会被触发。
            task_match = re.search(r"task_id=(task_[A-Za-z0-9]+)", task_text)  # 新增代码+DurableTaskRegistry: 从工具输出提取 task_id；若没有这行代码，后续无法定位记录。
            self.assertIsNotNone(task_match)  # 新增代码+DurableTaskRegistry: 断言 task 输出包含 id；若没有这行代码，工具返回格式破坏不会被发现。
            task_id = task_match.group(1)  # 新增代码+DurableTaskRegistry: 保存提取出来的 task_id；若没有这行代码，registry 查询没有 key。
            registry = TaskRegistry(workspace / "memory" / "tasks")  # 新增代码+DurableTaskRegistry: 打开默认任务登记表；若没有这行代码，无法检查持久记录。
            restored_record = TaskRegistry(workspace / "memory" / "tasks").get_task(task_id)  # 新增代码+DurableTaskRegistry: 用新实例读取任务模拟重启；若没有这行代码，只能证明内存表存在。
            self.assertEqual(restored_record.status, "completed")  # 新增代码+DurableTaskRegistry: 断言任务完成状态已落盘；若没有这行代码，新 agent 无法恢复旧任务。
            self.assertIn("TASK_DONE", restored_record.output)  # 新增代码+DurableTaskRegistry: 断言任务输出已落盘；若没有这行代码，完成任务仍不可审计。
            self.assertIn(task_id, [record.task_id for record in registry.list_tasks()])  # 新增代码+DurableTaskRegistry: 断言 list 也能发现任务；若没有这行代码，状态可视化无法列任务。
            notification_command = RuntimeCommandQueue(workspace / "memory" / "runtime").dequeue_next()  # 新增代码+DurableTaskRegistry: 读取任务完成通知；若没有这行代码，回灌能力没有验证。
            self.assertIsNotNone(notification_command)  # 新增代码+DurableTaskRegistry: 断言通知已经入队；若没有这行代码，后台结果只能手动 task_output。
            self.assertEqual(notification_command.mode, "task_notification")  # 新增代码+DurableTaskRegistry: 断言通知命令类型正确；若没有这行代码，模型无法区分任务结果和普通 prompt。
            self.assertEqual(notification_command.payload["task_id"], task_id)  # 新增代码+DurableTaskRegistry: 断言通知指向同一 task；若没有这行代码，主 agent 可能收到无法定位的通知。
    def test_task_tools_read_durable_registry_after_agent_restart(self) -> None:  # 新增代码+DurableTaskToolsRed: 验证 task_list/task_get/task_update 在新 agent 实例中仍能读取旧任务；若没有这行代码，任务工具可能仍被内存字典假象掩盖。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DurableTaskToolsRed: 创建隔离工作区；若没有这行代码，重启验收会污染真实 memory。
            workspace = Path(raw_dir)  # 新增代码+DurableTaskToolsRed: 统一 workspace 路径；若没有这行代码，两个 agent 可能读写不同目录。
            model = RecordingToolNameFakeModel(ModelMessage(text="跨实例任务结果 DURABLE_TASK_DONE"))  # 新增代码+DurableTaskToolsRed: 准备确定性子任务结果；若没有这行代码，测试可能调用真实模型。
            first_agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+DurableTaskToolsRed: 创建第一个 agent 来产生任务；若没有这行代码，持久 registry 没有初始记录。
            task_text = first_agent._execute_tool(ToolCall(name="task", arguments={"prompt": "生成 DURABLE_TASK_DONE", "allowed_tools": ["read_file"], "max_turns": 1}))  # 新增代码+DurableTaskToolsRed: 通过真实 task 工具创建并完成任务；若没有这行代码，无法验证工具链落盘。
            task_match = re.search(r"task_id=(task_[A-Za-z0-9]+)", task_text)  # 新增代码+DurableTaskToolsRed: 从工具输出提取 task_id；若没有这行代码，后续无法指定旧任务。
            self.assertIsNotNone(task_match)  # 新增代码+DurableTaskToolsRed: 断言 task 输出包含 task_id；若没有这行代码，返回格式破坏不会被发现。
            task_id = task_match.group(1)  # 新增代码+DurableTaskToolsRed: 保存 task_id 供重启后的 agent 查询；若没有这行代码，测试无法定位目标任务。
            restarted_agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+DurableTaskToolsRed: 创建第二个 agent 模拟进程重启；若没有这行代码，测试仍可能只证明内存可用。
            list_output = restarted_agent._execute_tool(ToolCall(name="task_list", arguments={"status": "completed", "max_results": 10}))  # 新增代码+DurableTaskToolsRed: 用新 agent 列出已完成任务；若没有这行代码，task_list 跨实例缺口不会暴露。
            self.assertIn(task_id, list_output)  # 新增代码+DurableTaskToolsRed: 断言旧任务出现在新 agent 的列表里；若没有这行代码，内存旁路不会被卡住。
            get_output = restarted_agent._execute_tool(ToolCall(name="task_get", arguments={"task_id": task_id, "max_chars": 2000}))  # 新增代码+DurableTaskToolsRed: 用新 agent 读取旧任务详情；若没有这行代码，task_get 跨实例缺口不会暴露。
            self.assertIn("DURABLE_TASK_DONE", get_output)  # 新增代码+DurableTaskToolsRed: 断言旧任务输出可读；若没有这行代码，只有状态没有结果也可能误判通过。
            update_output = restarted_agent._execute_tool(ToolCall(name="task_update", arguments={"task_id": task_id, "label": "跨实例标签", "notes": "跨实例备注"}))  # 新增代码+DurableTaskToolsRed: 用新 agent 修改旧任务元信息；若没有这行代码，task_update 仍可能只依赖内存。
            self.assertIn("task_update 成功", update_output)  # 新增代码+DurableTaskToolsRed: 断言跨实例更新成功；若没有这行代码，失败文本可能被后续断言误读。
            updated_output = restarted_agent._execute_tool(ToolCall(name="task_get", arguments={"task_id": task_id, "max_chars": 2000}))  # 新增代码+DurableTaskToolsRed: 再次读取任务确认更新已保存；若没有这行代码，更新只返回成功但不落盘不会暴露。
            self.assertIn("跨实例标签", updated_output)  # 新增代码+DurableTaskToolsRed: 断言 label 被持久保存；若没有这行代码，任务管理元信息会在重启后丢失。
            self.assertIn("跨实例备注", updated_output)  # 新增代码+DurableTaskToolsRed: 断言 notes 被持久保存；若没有这行代码，任务交接说明会在重启后丢失。
    def test_team_peer_state_survives_agent_restart(self) -> None:  # 新增代码+DurableTeamRed: 验证 team peer 创建、消息和列表能跨 agent 实例恢复；若没有这行代码，team 仍可能只是内存演示功能。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+DurableTeamRed: 创建隔离工作区；若没有这行代码，team 状态会污染真实项目。
            workspace = Path(raw_dir)  # 新增代码+DurableTeamRed: 统一 workspace 路径；若没有这行代码，重启前后可能读写不同位置。
            model = RecordingToolNameFakeModel(ModelMessage(text="TEAM_OK"))  # 新增代码+DurableTeamRed: 准备确定性模型；若没有这行代码，测试可能调用真实模型。
            first_agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+DurableTeamRed: 创建第一个 agent 来创建 peer；若没有这行代码，持久 team registry 没有初始记录。
            create_output = first_agent._execute_tool(ToolCall(name="team_create", arguments={"name": "跨实例队友", "role": "worker", "notes": "负责持久化验证"}))  # 新增代码+DurableTeamRed: 通过真实 team_create 创建 peer；若没有这行代码，无法验证工具链落盘。
            peer_id = next(line for line in create_output.splitlines() if line.startswith("peer_id=")).split("=", 1)[1].strip()  # 新增代码+DurableTeamRed: 提取 peer_id 供新 agent 查询；若没有这行代码，后续无法指定目标 peer。
            restarted_agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+DurableTeamRed: 创建第二个 agent 模拟进程重启；若没有这行代码，测试仍可能只证明内存可用。
            list_output = restarted_agent._execute_tool(ToolCall(name="list_peers", arguments={"max_results": 10}))  # 新增代码+DurableTeamRed: 用新 agent 查看 peer 列表；若没有这行代码，peer 列表跨实例缺口不会暴露。
            self.assertIn(peer_id, list_output)  # 新增代码+DurableTeamRed: 断言旧 peer 出现在新 agent 列表里；若没有这行代码，team 内存依赖不会被发现。
            self.assertIn("跨实例队友", list_output)  # 新增代码+DurableTeamRed: 断言 peer 名称被恢复；若没有这行代码，只恢复 id 而丢元信息也可能误判通过。
            send_output = restarted_agent._execute_tool(ToolCall(name="send_message", arguments={"peer_id": peer_id, "content": "请继续验证持久 inbox"}))  # 新增代码+DurableTeamRed: 用新 agent 给旧 peer 发消息；若没有这行代码，send_message 跨实例缺口不会暴露。
            self.assertIn("send_message 成功", send_output)  # 新增代码+DurableTeamRed: 断言跨实例发送成功；若没有这行代码，失败文本可能被忽略。
            third_agent = LearningAgent(model=model, workspace=workspace, ask_permission=lambda action: True, debug_enabled=False)  # 新增代码+DurableTeamRed: 创建第三个 agent 验证消息也已落盘；若没有这行代码，只能证明第二个实例内存可用。
            message_output = third_agent._execute_tool(ToolCall(name="read_peer_messages", arguments={"peer_id": peer_id, "include_acknowledged": True, "max_results": 10}))  # 新增代码+DurableTeamRed: 用第三个 agent 读取 peer inbox；若没有这行代码，消息持久化缺口不会暴露。
            self.assertIn("请继续验证持久 inbox", message_output)  # 新增代码+DurableTeamRed: 断言 inbox 内容跨实例可读；若没有这行代码，team 消息仍可能只是进程内队列。

    def test_task_output_store_supports_tail_delta_and_evict(self) -> None:  # 新增代码+TaskOutput: 验证任务输出文件支持增量读取和清理；若没有这行代码，长输出治理没有红线。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TaskOutput: 创建隔离输出目录；若没有这行代码，测试会写入真实任务输出。
            output_store = TaskOutputStore(Path(raw_dir))  # 新增代码+TaskOutput: 创建输出文件管理器；若没有这行代码，无法测试 append/delta/tail。
            output_store.append("task-output", "alpha\n")  # 新增代码+TaskOutput: 写入第一段输出；若没有这行代码，delta 起点没有内容。
            first_delta = output_store.read_delta("task-output", 0)  # 新增代码+TaskOutput: 从 offset 0 读取增量；若没有这行代码，无法验证 offset 语义。
            output_store.append("task-output", "beta\n")  # 新增代码+TaskOutput: 写入第二段输出；若没有这行代码，后续增量没有新增内容。
            second_delta = output_store.read_delta("task-output", first_delta.next_offset)  # 新增代码+TaskOutput: 从上次 offset 继续读；若没有这行代码，无法验证只读新增部分。
            self.assertEqual(first_delta.text, "alpha\n")  # 新增代码+TaskOutput: 断言第一次读到第一段；若没有这行代码，offset 0 行为可能错误。
            self.assertEqual(second_delta.text, "beta\n")  # 新增代码+TaskOutput: 断言第二次只读到新增段；若没有这行代码，模型可能反复吃旧输出。
            self.assertEqual(output_store.tail("task-output", max_chars=4), "eta\n")  # 新增代码+TaskOutput: 断言 tail 可限制返回最后字符；若没有这行代码，状态页可能被长输出撑爆。
            output_store.evict("task-output")  # 新增代码+TaskOutput: 删除输出文件；若没有这行代码，清理路径没有测试。
            self.assertFalse(output_store.output_path("task-output").exists())  # 新增代码+TaskOutput: 断言 evict 后文件不存在；若没有这行代码，旧输出会无限堆积。

    def test_task_poller_turns_stalled_prompt_output_into_needs_input_notification(self) -> None:  # 新增代码+TaskPoller: 验证卡在交互提示的后台任务会通知主 agent；若没有这行代码，watchdog 能力不可验。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+TaskPoller: 创建隔离目录；若没有这行代码，poller 测试会污染真实任务状态。
            base_dir = Path(raw_dir)  # 新增代码+TaskPoller: 转成 Path；若没有这行代码，多个 runtime 组件路径不一致。
            output_store = TaskOutputStore(base_dir / "outputs")  # 新增代码+TaskPoller: 创建任务输出管理器；若没有这行代码，poller 无法检查 tail。
            registry = TaskRegistry(base_dir / "tasks", output_store=output_store)  # 新增代码+TaskPoller: 创建任务登记表并注入输出 store；若没有这行代码，任务和输出无法关联。
            queue = RuntimeCommandQueue(base_dir / "runtime")  # 新增代码+TaskPoller: 创建通知队列；若没有这行代码，poller 没有回灌通道。
            record = registry.create_task(task_id="task-stalled", prompt="等待确认", kind="background_shell", status="running")  # 新增代码+TaskPoller: 创建一个运行中的后台任务；若没有这行代码，poller 没有扫描目标。
            output_store.append(record.task_id, "Continue?")  # 新增代码+TaskPoller: 模拟后台命令卡在交互提示；若没有这行代码，needs_input 检测没有证据。
            changed = TaskPoller(task_registry=registry, command_queue=queue).poll_once()  # 新增代码+TaskPoller: 执行一次 poll；若没有这行代码，状态不会更新。
            self.assertEqual(changed, 1)  # 新增代码+TaskPoller: 断言 poller 发现一个需要输入的任务；若没有这行代码，watchdog 漏报不会暴露。
            updated = registry.get_task("task-stalled")  # 新增代码+TaskPoller: 读取更新后的任务；若没有这行代码，只能看通知无法看状态。
            self.assertEqual(updated.status, "needs_input")  # 新增代码+TaskPoller: 断言状态变成 needs_input；若没有这行代码，状态可视化仍显示 running。
            command = queue.dequeue_next()  # 新增代码+TaskPoller: 读取回灌通知；若没有这行代码，主 agent 无法自动看到卡住状态。
            self.assertEqual(command.mode, "task_notification")  # 新增代码+TaskPoller: 断言 poller 生成任务通知；若没有这行代码，watchdog 只能内部改变状态。
            self.assertEqual(command.payload["status"], "needs_input")  # 新增代码+TaskPoller: 断言通知说明需要用户输入；若没有这行代码，模型不知道下一步该问用户。

    def test_stage_verifier_supports_schema_command_event_and_acceptance_result(self) -> None:  # 新增代码+VerifierUpgrade: 验证增强验收器能检查真实验收证据；若没有这行代码，harness 只能看 marker。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+VerifierUpgrade: 创建隔离验收目录；若没有这行代码，artifact 检查会污染真实项目。
            base_dir = Path(raw_dir)  # 新增代码+VerifierUpgrade: 转成 Path 供 verifier 使用；若没有这行代码，路径检查不稳定。
            (base_dir / "note.txt").write_text("NOTE_OK", encoding="utf-8")  # 新增代码+VerifierUpgrade: 写入 artifact 内容；若没有这行代码，artifact_contains 没有真实文件。
            (base_dir / "acceptance.json").write_text('{"completed": true, "assertion": {"passed": true}}', encoding="utf-8")  # 新增代码+VerifierUpgrade: 写入 acceptance_controller 风格结果；若没有这行代码，真实验收回放没有证据。
            stage = HarnessStage(name="verify", prompt="验收", success_markers=["TEXT_OK"], required_artifacts=["acceptance.json"])  # 新增代码+VerifierUpgrade: 创建基础阶段；若没有这行代码，verifier 没有检查对象。
            stage.artifact_contains = {"note.txt": "NOTE_OK"}  # 新增代码+VerifierUpgrade: 要求 artifact 包含指定文本；若没有这行代码，文件内容错误不会被发现。
            stage.json_schema_artifacts = {"acceptance.json": {"required": ["completed", "assertion"]}}  # 新增代码+VerifierUpgrade: 要求 JSON 文件有关键字段；若没有这行代码，坏 result.json 可能误通过。
            stage.expected_command_exit_codes = {"compileall": 0}  # 新增代码+VerifierUpgrade: 要求命令退出码符合预期；若没有这行代码，自动化检查失败也可能被忽略。
            stage.expected_event_sequence = ["run_started", "run_completed"]  # 新增代码+VerifierUpgrade: 要求事件顺序出现；若没有这行代码，事件流缺口不会被 verifier 发现。
            stage.acceptance_result_artifacts = ["acceptance.json"]  # 新增代码+VerifierUpgrade: 要求真实验收 result.json 通过；若没有这行代码，controller 结果无法纳入阶段门禁。
            result = StageVerifier(base_dir).verify(stage, "TEXT_OK", command_results={"compileall": 0}, events=[{"event_type": "run_started"}, {"event_type": "run_completed"}])  # 新增代码+VerifierUpgrade: 执行增强 verifier；若没有这行代码，新增验收类型没有行为证明。
            self.assertTrue(result.passed)  # 新增代码+VerifierUpgrade: 断言所有证据满足时通过；若没有这行代码，增强检查可能永远失败。
            self.assertIn("artifact_contains:note.txt", result.checks)  # 新增代码+VerifierUpgrade: 断言内容检查进入审计明细；若没有这行代码，用户无法知道检查了什么。
            self.assertIn("json_schema:acceptance.json", result.checks)  # 新增代码+VerifierUpgrade: 断言 JSON schema 检查进入明细；若没有这行代码，结构验收不可审计。
            self.assertIn("command_exit_code:compileall=0", result.checks)  # 新增代码+VerifierUpgrade: 断言命令退出码检查进入明细；若没有这行代码，自动化结果没有审计标签。
            self.assertIn("event_sequence:run_started>run_completed", result.checks)  # 新增代码+VerifierUpgrade: 断言事件顺序检查进入明细；若没有这行代码，事件门禁不可追踪。
            self.assertIn("acceptance_result:acceptance.json", result.checks)  # 新增代码+VerifierUpgrade: 断言真实验收结果检查进入明细；若没有这行代码，controller 验真证据不会被展示。

    def test_harness_cli_exposes_queue_tasks_events_resume_and_poll(self) -> None:  # 新增代码+HarnessCliUpgrade: 验证 CLI 能审计队列、任务、事件、恢复和 poll；若没有这行代码，外部 agent 状态入口不完整。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+HarnessCliUpgrade: 创建隔离 CLI store；若没有这行代码，CLI 测试会读取真实状态。
            base_dir = Path(raw_dir)  # 新增代码+HarnessCliUpgrade: 转成 Path 供多个组件共用；若没有这行代码，路径参数容易写错。
            store_dir = base_dir / "harness"  # 新增代码+HarnessCliUpgrade: 定义 harness store 路径；若没有这行代码，CLI 参数缺少清晰目标。
            task_dir = base_dir / "tasks"  # 新增代码+HarnessCliUpgrade: 定义 task registry 路径；若没有这行代码，tasks 命令没有数据源。
            runtime_dir = base_dir / "runtime"  # 新增代码+HarnessCliUpgrade: 定义 runtime queue 路径；若没有这行代码，queue/resume/poll 命令无法共用队列。
            store = HarnessStore(store_dir)  # 新增代码+HarnessCliUpgrade: 创建 harness store；若没有这行代码，无法准备 CLI 状态。
            run = HarnessRun.create(run_id="cli-run", prompt="CLI 审计", stages=[HarnessStage(name="stage", prompt="prompt")])  # 新增代码+HarnessCliUpgrade: 构造测试 run；若没有这行代码，queue/events/resume 没有目标。
            run.status = "running"  # 新增代码+HarnessCliUpgrade: 让 resume 命令可以发现 interrupted run；若没有这行代码，恢复命令没有效果。
            run.stages[0].success_markers.append("VERIFIER_OK")  # 新增代码+HarnessStatusAudit: 给阶段增加 verifier marker；若没有这行代码，status 输出无法证明具体检查项可见。
            run.stages[0].attempts.append(HarnessAttempt(attempt_number=1, status="completed", output="STAGE_OUTPUT_TAIL"))  # 新增代码+HarnessStatusAudit: 写入阶段尝试输出摘要；若没有这行代码，status CLI 无法测试 output 可见性。
            run.stages[0].acceptance = StageVerifier(store_dir).verify(run.stages[0], "VERIFIER_OK")  # 新增代码+HarnessStatusAudit: 写入真实 verifier 结果；若没有这行代码，status CLI 没有验收明细可展示。
            store.save_run(run)  # 新增代码+HarnessCliUpgrade: 保存测试 run；若没有这行代码，CLI 无法读取状态。
            store.append_event("cli-run", "run_started", {})  # 新增代码+HarnessCliUpgrade: 写入事件供 events 命令展示；若没有这行代码，events 命令输出为空。
            output_store = TaskOutputStore(base_dir / "outputs")  # 新增代码+HarnessCliUpgrade: 创建任务输出 store；若没有这行代码，poll 命令无法检查任务 tail。
            registry = TaskRegistry(task_dir, output_store=output_store)  # 新增代码+HarnessCliUpgrade: 创建任务登记表；若没有这行代码，tasks/poll 命令没有任务源。
            registry.create_task(task_id="cli-task", prompt="等待输入", kind="background_shell", status="running")  # 新增代码+HarnessCliUpgrade: 创建运行中任务；若没有这行代码，tasks 命令没有内容。
            output_store.append("cli-task", "Continue?")  # 新增代码+HarnessCliUpgrade: 写入卡住输出供 poll 命令识别；若没有这行代码，poll 命令无法生成 needs_input。
            queue_output = io.StringIO()  # 新增代码+HarnessCliUpgrade: 准备捕获 queue 命令输出；若没有这行代码，无法断言 CLI 文本。
            with redirect_stdout(queue_output):  # 新增代码+HarnessCliUpgrade: 捕获 stdout；若没有这行代码，测试输出会混入终端。
                queue_code = harness_cli_main(["queue", "--store", str(store_dir), "--runtime", str(runtime_dir)])  # 新增代码+HarnessCliUpgrade: 调用 queue 命令；若没有这行代码，队列状态 CLI 没有测试。
            self.assertEqual(queue_code, 0)  # 新增代码+HarnessCliUpgrade: 断言 queue 命令成功；若没有这行代码，CLI 失败可能被忽略。
            self.assertIn("cli-run", queue_output.getvalue())  # 新增代码+HarnessCliUpgrade: 断言 queue 输出 run id；若没有这行代码，用户无法发现运行中任务。
            tasks_output = io.StringIO()  # 新增代码+HarnessCliUpgrade: 准备捕获 tasks 命令输出；若没有这行代码，无法检查任务状态文本。
            with redirect_stdout(tasks_output):  # 新增代码+HarnessCliUpgrade: 捕获 tasks 输出；若没有这行代码，测试会污染终端。
                tasks_code = harness_cli_main(["tasks", "--tasks", str(task_dir)])  # 新增代码+HarnessCliUpgrade: 调用 tasks 命令；若没有这行代码，持久任务 CLI 没有测试。
            self.assertEqual(tasks_code, 0)  # 新增代码+HarnessCliUpgrade: 断言 tasks 命令成功；若没有这行代码，任务状态入口失败不会暴露。
            self.assertIn("cli-task", tasks_output.getvalue())  # 新增代码+HarnessCliUpgrade: 断言任务 id 出现在输出里；若没有这行代码，用户无法定位后台任务。
            self.assertIn("Continue?", tasks_output.getvalue())  # 新增代码+HarnessStatusAudit: 断言 tasks CLI 直接展示任务输出尾巴；若没有这行代码，用户仍要手动打开 output_path 才能审计。
            status_output = io.StringIO()  # 新增代码+HarnessStatusAudit: 准备捕获 status 命令输出；若没有这行代码，无法断言 run/stage/verifier/output 是否同屏可见。
            with redirect_stdout(status_output):  # 新增代码+HarnessStatusAudit: 捕获 status 输出避免污染测试终端；若没有这行代码，断言只能靠真实 stdout。
                status_code = harness_cli_main(["status", "--store", str(store_dir), "--run-id", "cli-run"])  # 新增代码+HarnessStatusAudit: 调用 status 命令；若没有这行代码，状态可视化入口没有被测试。
            self.assertEqual(status_code, 0)  # 新增代码+HarnessStatusAudit: 断言 status 命令成功；若没有这行代码，后续文本断言可能掩盖 CLI 失败。
            self.assertIn("marker:VERIFIER_OK", status_output.getvalue())  # 新增代码+HarnessStatusAudit: 断言 verifier 检查项在状态输出里可见；若没有这行代码，验收通过原因仍不可审计。
            self.assertIn("STAGE_OUTPUT_TAIL", status_output.getvalue())  # 新增代码+HarnessStatusAudit: 断言阶段尝试输出尾巴在状态输出里可见；若没有这行代码，用户看不到阶段实际产出。
            events_output = io.StringIO()  # 新增代码+HarnessCliUpgrade: 准备捕获 events 命令输出；若没有这行代码，无法验证事件审计入口。
            with redirect_stdout(events_output):  # 新增代码+HarnessCliUpgrade: 捕获 events 输出；若没有这行代码，事件文本无法断言。
                events_code = harness_cli_main(["events", "--store", str(store_dir), "--run-id", "cli-run"])  # 新增代码+HarnessCliUpgrade: 调用 events 命令；若没有这行代码，事件查看 CLI 没有测试。
            self.assertEqual(events_code, 0)  # 新增代码+HarnessCliUpgrade: 断言 events 命令成功；若没有这行代码，事件入口失败不会暴露。
            self.assertIn("run_started", events_output.getvalue())  # 新增代码+HarnessCliUpgrade: 断言事件类型出现；若没有这行代码，CLI 可能只打印空白。
            resume_output = io.StringIO()  # 新增代码+HarnessCliUpgrade: 准备捕获 resume 命令输出；若没有这行代码，无法验证恢复入口。
            with redirect_stdout(resume_output):  # 新增代码+HarnessCliUpgrade: 捕获 resume 输出；若没有这行代码，测试无法读取恢复数量。
                resume_code = harness_cli_main(["resume", "--store", str(store_dir), "--runtime", str(runtime_dir)])  # 新增代码+HarnessCliUpgrade: 调用 resume 命令；若没有这行代码，中断恢复 CLI 没有测试。
            self.assertEqual(resume_code, 0)  # 新增代码+HarnessCliUpgrade: 断言 resume 命令成功；若没有这行代码，恢复入口失败不会暴露。
            self.assertIn("restored=1", resume_output.getvalue())  # 新增代码+HarnessCliUpgrade: 断言恢复了一个 run；若没有这行代码，resume 可能静默无效。
            poll_output = io.StringIO()  # 新增代码+HarnessCliUpgrade: 准备捕获 poll 命令输出；若没有这行代码，无法验证 watchdog CLI。
            with redirect_stdout(poll_output):  # 新增代码+HarnessCliUpgrade: 捕获 poll 输出；若没有这行代码，测试输出会混入终端。
                poll_code = harness_cli_main(["poll", "--tasks", str(task_dir), "--runtime", str(runtime_dir), "--outputs", str(base_dir / "outputs")])  # 新增代码+HarnessCliUpgrade: 调用 poll 命令；若没有这行代码，watchdog CLI 没有测试。
            self.assertEqual(poll_code, 0)  # 新增代码+HarnessCliUpgrade: 断言 poll 命令成功；若没有这行代码，卡住任务通知入口失败不会暴露。
            self.assertIn("changed=1", poll_output.getvalue())  # 新增代码+HarnessCliUpgrade: 断言 poll 发现一个变化；若没有这行代码，needs_input 可能没有生成。

    def test_harness_queue_skips_corrupt_run_state_and_quarantines_bad_json(self) -> None:  # 新增代码+RuntimeFileSafety: 验证坏 run JSON 不会拖垮队列恢复；若没有这行代码，半写状态会让所有长任务不可用。
        with tempfile.TemporaryDirectory() as raw_dir:  # 新增代码+RuntimeFileSafety: 创建隔离 harness store；若没有这行代码，腐坏文件测试会污染真实状态。
            store = HarnessStore(Path(raw_dir) / "harness")  # 新增代码+RuntimeFileSafety: 创建 harness store；若没有这行代码，无法写入 run 状态。
            bad_path = store.run_path("aaa_bad")  # 新增代码+RuntimeFileSafety: 计算一个排序靠前的坏 run 路径；若没有这行代码，queue 可能先读好文件绕过坏文件。
            bad_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+RuntimeFileSafety: 确保 runs 目录存在；若没有这行代码，写坏文件会失败。
            bad_path.write_text("{", encoding="utf-8")  # 新增代码+RuntimeFileSafety: 写入半截 JSON 模拟崩溃；若没有这行代码，腐坏恢复分支没有输入。
            good_run = HarnessRun.create(run_id="zzz_good", prompt="正常任务", stages=[HarnessStage(name="stage", prompt="prompt")])  # 新增代码+RuntimeFileSafety: 创建一个正常 queued run；若没有这行代码，queue 没有可领取目标。
            store.save_run(good_run)  # 新增代码+RuntimeFileSafety: 保存正常任务；若没有这行代码，腐坏文件后没有恢复目标。
            leased = __import__("learning_agent.harness.queue", fromlist=["HarnessQueue"]).HarnessQueue(store).lease_next(worker_id="worker-safe")  # 新增代码+RuntimeFileSafety: 从队列领取任务；若没有这行代码，无法证明坏文件被跳过。
            self.assertIsNotNone(leased)  # 新增代码+RuntimeFileSafety: 断言队列仍能领取正常任务；若没有这行代码，坏 JSON 拖垮整体不会被发现。
            self.assertEqual(leased.run_id, "zzz_good")  # 新增代码+RuntimeFileSafety: 断言领取的是正常 run；若没有这行代码，队列可能返回坏状态对象。
            quarantine_dir = store.base_dir / "quarantine"  # 新增代码+RuntimeFileSafety: 定位坏文件隔离目录；若没有这行代码，无法验证坏状态是否保留证据。
            self.assertTrue(any(quarantine_dir.glob("aaa_bad.json.*.bad")))  # 新增代码+RuntimeFileSafety: 断言坏文件被移动隔离；若没有这行代码，下一次启动仍会反复读坏文件。


if __name__ == "__main__":  # 新增代码+HarnessRuntimeAlignment: 支持直接运行本测试文件；若没有这行代码，单文件调试不方便。
    unittest.main()  # 新增代码+HarnessRuntimeAlignment: 直接运行时启动 unittest；若没有这行代码，python 文件不会自动执行测试。
