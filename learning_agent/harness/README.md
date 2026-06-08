# learning_agent Long-Task Harness

`learning_agent/harness/` 是给长任务准备的独立 harness 模块。它的目标不是替换现有 `LearningAgent.run()`，而是先提供一套可被 Codex、其他 agent 或后续主循环接入的“长任务外骨架”：任务能排队、能落盘、能分阶段验收、失败后能按策略继续、状态能被外部读取。

## 它解决什么问题

- 断点恢复：`HarnessRun.current_stage_index` 和每个阶段的 `checkpoint` 会落盘，进程重启后可以跳过已完成阶段。
- 任务队列：`HarnessQueue` 支持 `enqueue`、`lease_next`、`heartbeat`、`complete`、`fail`，避免长任务只活在内存里。
- 阶段性验收：`StageVerifier` 可以检查模型输出里的成功标记，也可以检查指定 artifact 文件是否存在。
- 失败后继续：`RecoveryPolicy` 会识别 timeout、endpoint、rate limit、connection 等临时错误，并在有多个 endpoint 时切换到下一个 endpoint。
- 状态可视化：`render_harness_status()` 和 `python -m learning_agent.harness status` 可以输出人类和外部 agent 都能看懂的任务状态。
- 可审计事件：`HarnessStore.append_event()` 会把排队、领取、阶段开始、重试、完成、失败等事件写入 JSONL。
- CLI 创建和执行：`python -m learning_agent.harness enqueue/run` 可以从命令行创建任务并推进队列。
- 真实 agent 接入：`AgentStageExecutor` 可以把每个阶段交给 `LearningAgent.run(stage.prompt)` 执行。

## 推荐存储目录

生产或真实任务建议使用：

```text
learning_agent/memory/harness/
```

测试或一次性实验可以传入临时目录。所有状态由调用方显式指定 store 路径，避免误写到不该写的位置。

## 最小 Python 用法

```python
from pathlib import Path

from learning_agent.harness import HarnessQueue, HarnessRun, HarnessStage, HarnessStore

store = HarnessStore(Path("learning_agent/memory/harness"))
queue = HarnessQueue(store)
run = HarnessRun.create(
    run_id="demo-long-task",
    prompt="完成一个三阶段任务",
    stages=[
        HarnessStage(name="plan", prompt="先写计划", success_markers=["PLAN_OK"]),
        HarnessStage(name="implement", prompt="实现功能", success_markers=["IMPLEMENT_OK"]),
        HarnessStage(name="verify", prompt="运行验收", success_markers=["VERIFY_OK"]),
    ],
)
queue.enqueue(run)
```

## 查看状态

创建一个两阶段任务：

```powershell
python -m learning_agent.harness enqueue --store learning_agent/memory/harness --run-id demo-long-task --prompt "完成一个两阶段任务" --stage "plan::输出 PLAN_OK" --stage "verify::输出 VERIFY_OK" --success-marker "plan=PLAN_OK" --success-marker "verify=VERIFY_OK"
```

用无模型的 echo executor 做本地 smoke：

```powershell
python -m learning_agent.harness run --store learning_agent/memory/harness --executor echo
```

用真实 `LearningAgent` 执行阶段：

```powershell
python -m learning_agent.harness run --store learning_agent/memory/harness --executor agent --workspace H:\codexworkplace\sofeware\OpenHarness-main\learning_agent
```

```powershell
python -m learning_agent.harness status --store learning_agent/memory/harness --run-id demo-long-task
```

列出已有任务：

```powershell
python -m learning_agent.harness list --store learning_agent/memory/harness
```

## 当前边界

- 这是第一版独立 harness，还没有把现有交互式 agent 主循环强制迁入 harness。
- 当前 CLI 已提供 `enqueue`、`run`、`status`、`list`；更高级的多 worker 文件锁、UI dashboard 和主循环深度改造仍在后续阶段。
- 真正声明任务完成前，仍必须走项目规定的三重门禁：代码和文档完成、自动化测试通过、`start_oauth_agent.bat` 真实可见终端交互验收通过。
