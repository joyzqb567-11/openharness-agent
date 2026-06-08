# learning_agent Harness 对齐 ClaudeCode 方案

记录日期：2026-05-31

## 结论

当前 `learning_agent` 已经有独立 `learning_agent/harness/` 长任务底座，但还没有达到 ClaudeCode 的长任务运行时能力。

源码确认的关键事实：

- `learning_agent/harness/store.py` 已有 JSON run 状态和 JSONL event log。
- `learning_agent/harness/queue.py` 已有 enqueue、lease、heartbeat、complete、fail。
- `learning_agent/harness/runner.py` 已有阶段执行、checkpoint、失败重试和 endpoint recovery。
- `learning_agent/harness/verifier.py` 已有 marker 和 artifact 阶段验收。
- `learning_agent/harness/agent_executor.py` 已能把阶段交给 `LearningAgent.run(stage.prompt)`。
- 入口链路源码显示 `learning_agent/learning_agent.py` 进入 `learning_agent/app/cli.py`，交互式路径再进入 `learning_agent/app/interactive.py`，最终调用的是 `agent.run(...)`；这些入口文件没有导入或调用 `learning_agent.harness`，所以真实终端主循环当前不是 harness 驱动。
- `learning_agent/core/agent.py` 已有 `run_events()`、transcript、session summary、工具事件流和并发工具编排，但这些还没有和 `harness/` 合并成默认长任务运行时。
- ClaudeCode 的长任务能力分散在 `QueryEngine.ts`、`cli/print.ts`、`utils/messageQueueManager.ts`、`tasks/LocalAgentTask`、`tasks/RemoteAgentTask`、`tasks/LocalShellTask`、`utils/task/framework.ts`、`utils/sessionStorage.ts` 等文件，不是单独一个 harness 类。

因此，目标不是再加一个小模块，而是把 `learning_agent/harness` 升级成主循环、任务队列、后台任务、恢复、验收、状态可视化、控制器验收共同使用的运行时。

## 硬门禁

以下门禁没有全部通过前，不允许声明已经对齐 ClaudeCode core harness：

1. 真实终端输入 prompt 后，必须自动创建或续接 durable harness run。
2. `LearningAgent.run()`、`LearningAgent.run_events()`、session transcript 和 harness event log 必须共享同一轮运行证据，不能只是互相旁路镜像。
3. `RuntimeCommandQueue` 必须被真实主循环消费，不能只被 CLI 或单元测试消费。
4. task notification 必须在下一轮真实模型调用前转成模型可见上下文，不能要求用户或 agent 手动调用 `task_output`。
5. `resume_interrupted` 命令必须被真实主循环消费并驱动继续执行，不能只写入队列。
6. `task`、background command、team peer 状态不能只依赖 `self.task_runs` 和 `self.background_commands` 这类内存字典；内存字典只能作为运行期缓存。
7. 进程中断后，必须能从 durable checkpoint、session、queue 恢复，不重跑已完成阶段。
8. 状态 CLI/API 必须能看见 run、stage、task、event、output、verifier 结果。
9. 最终必须通过 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat` 真实可见终端验收，且至少覆盖 task notification 回灌和 interrupted resume。
10. README 或说明文字不能作为完成证据；必须使用源码、自动化测试、durable 状态文件和真实终端 `result.json` 作为证据。

## 对齐目标

最终能力目标：

1. 用户在真实终端输入一个长任务后，任务自动进入 durable harness run，而不是只存在当前 Python 调用栈里。
2. 每轮模型请求、流式输出、工具调用、权限决策、阶段完成、失败恢复都写入统一事件流。
3. 进程中断后，可以从 durable session 和 harness checkpoint 恢复，不重跑已完成阶段。
4. 后台子 agent、后台 shell、team peer 任务不再只存在内存里，而是有 durable task registry。
5. 任务完成、失败、卡住、需要用户输入时，会以 task-notification 形式回灌给主 agent。
6. 状态 CLI/API 能展示 run、stage、task、worker、事件、最后输出和验收结果。
7. 每个阶段都有确定性验收器，支持 marker、artifact、JSON schema、命令退出码和真实终端 acceptance controller。
8. 所有实现必须通过单元测试、集成测试、compileall，以及真实可见终端 `start_oauth_agent.bat` 验收。

## ClaudeCode 源码对应能力

| ClaudeCode 能力 | 源码证据 | learning_agent 当前状态 | 需要补齐 |
|---|---|---|---|
| 主循环提前持久化用户消息，防止中断后 resume 丢失 | `QueryEngine.ts` 在进入 API loop 前 `recordTranscript(messages)` | `run_events()` 会写事件，但普通 `run()` 仍不是 harness 驱动 | 把交互入口改成优先走 `run_events()` + durable session |
| compact 边界持久化 | `QueryEngine.ts` 对 `compact_boundary` 前的 preserved segment flush | 有 prompt compact summary，但未和 harness checkpoint 绑定 | 加 `compact_boundary` harness event 和 resume tail 校验 |
| 自动恢复中断 turn | `cli/print.ts` 会移除 interrupted sentinel 并 re-enqueue | 当前没有主队列级 interrupted-turn requeue | 增加 interrupted run detector 和 resume command |
| 统一命令队列 | `messageQueueManager.ts` 统一处理 prompt、task-notification、permission | 只有 harness queue；不处理用户 prompt 和 task notification | 新增 runtime command queue |
| 后台 agent 完成通知回灌模型 | `LocalAgentTask.tsx` enqueue task notification，`print.ts` 再喂给 ask | task 子 agent 结果只能 tool 查询，不能自动回灌 | 新增 durable task notification queue |
| 远程 agent sidecar 恢复和轮询 | `RemoteAgentTask.tsx` persist sidecar、restore、poll | 当前没有 remote sidecar 任务模型 | 设计 external/remote task adapter 接口 |
| 后台 shell 输出和卡住检测 | `LocalShellTask.tsx` stall watchdog，`ShellCommand.ts` output file/task id | 有后台命令内存表和 reader thread，但不 durable | 后台命令 task 化、输出落盘、恢复状态 |
| 全局任务 polling framework | `utils/task/framework.ts` poll running tasks and enqueue notification | 当前无统一 task poller | 增加 harness task poller |
| 输出文件和进度轮询 | `TaskOutput.ts` file-mode output poller | 有 tool result offload 和 harness checkpoint 摘要 | 统一 task output 文件和增量读取 |
| session sidecar 和写入队列 | `sessionStorage.ts` remote-agents sidecar、writeQueues、flush | 有 summary/events，但缺统一 flush 和多进程锁 | 增加 file lock / atomic write / flush barrier |

## 分阶段方案

### 阶段 1：源码基线和测试红线

目标：先写失败测试，明确“当前不具备 ClaudeCode 等价能力”的边界。

要做：

- 新增 `learning_agent/tests/test_harness_runtime_alignment.py`。
- 测试当前主循环是否能产出 durable harness run。
- 测试任务完成通知是否能进入下一轮模型输入。
- 测试后台 task 是否跨 agent 实例恢复。
- 测试 interrupted run 是否能重新入队。

验收：

- 初始测试应失败，证明差距真实存在。
- 测试名和失败断言要能直接对应 ClaudeCode 能力项。

### 阶段 2：RuntimeCommandQueue

目标：补上 ClaudeCode `messageQueueManager.ts` 对应能力。

新增文件：

- `learning_agent/runtime/command_queue.py`

核心对象：

- `RuntimeCommand`
- `RuntimeCommandQueue`
- priority：`now`、`next`、`later`
- mode：`prompt`、`task_notification`、`permission_response`、`resume_interrupted`

行为：

- prompt 可以批量合并。
- task notification 默认 later，避免淹没用户输入。
- queue 必须持久化到磁盘。
- queue 必须支持 ack、started、completed 事件。

验收：

- 多条 prompt 能合并成一次后续 turn。
- task notification 不会饿死用户 prompt。
- 重启后 queue 仍能恢复未处理命令。

### 阶段 3：HarnessSessionRuntime

目标：让 `learning_agent` 的真实交互入口进入 harness runtime，而不是旁路执行。

新增文件：

- `learning_agent/runtime/session_runtime.py`

修改文件：

- `learning_agent/core/agent.py`
- `learning_agent/app/interactive.py`

行为：

- `run()` 保留兼容，但内部优先消费 `run_events()`。
- 交互式终端每个用户 prompt 创建或续接一个 `HarnessRun`。
- 每轮 run_id、session_id、command_id 要统一。
- `run_events()` 事件同时写入 transcript 和 harness event log。

验收：

- 真实 agent 输入普通 prompt 后，memory 中出现 session events、harness run、command queue event。
- `python -m learning_agent.harness status` 能看到当前真实终端任务。

### 阶段 4：Interrupted Turn Resume

目标：补上 ClaudeCode 自动恢复中断 turn 的能力。

新增文件：

- `learning_agent/runtime/resume.py`

行为：

- 模型请求前先落盘 user input。
- 工具执行前后写入 durable checkpoint。
- 如果进程在 run_completed 前退出，下次启动检测到 interrupted run。
- interrupted run 自动生成 `Continue from where you left off.` 或中文等价续跑 prompt。
- 已完成阶段不重跑，未确认副作用工具不自动重放。

验收：

- 测试模拟写入 running 状态后重启，resume 能重新入队。
- 已完成 stage 不重复执行。
- 未完成 tool_call 显示 `needs_review`，等待用户确认。

### 阶段 5：Durable Task Registry

目标：把 task、team、background command 接入 durable harness。

新增文件：

- `learning_agent/runtime/task_registry.py`
- `learning_agent/runtime/task_output.py`

修改文件：

- `learning_agent/core/agent.py`
- `learning_agent/tasks/task_runs.py`
- `learning_agent/tasks/background.py`

行为：

- `task` 创建 durable task record。
- `task_output/task_list/task_get/task_stop` 从 registry 读取，不只读内存。
- 后台 shell 输出写入 task output 文件。
- task 有 status、notified、output_path、last_offset、owner_run_id。

验收：

- 新 agent 实例能读取旧 task 记录。
- 后台命令结束后状态从 running 变 completed/failed。
- task_stop 能把 durable 状态标为 stopped。

### 阶段 6：Task Notification 回灌

目标：补上 ClaudeCode 后台任务完成后自动进入模型下一轮的能力。

行为：

- task 完成、失败、停止时，生成 XML 或 JSON task notification。
- notification 写入 RuntimeCommandQueue，mode=`task_notification`。
- 下一轮模型调用前，queue drain 会把 notification 转为 user/tool context。
- 已通知任务标记 `notified=true`，避免重复回灌。

验收：

- 后台子 agent 完成后，主 agent 不需要手动 task_output，也能在下一轮看到结果。
- 同一任务不会重复通知。
- notification 包含 task_id、status、summary、output_file、usage。

### 阶段 7：Task Poller 和 Watchdog

目标：补上 ClaudeCode task framework、remote polling、stall watchdog 的能力。

新增文件：

- `learning_agent/runtime/poller.py`

行为：

- 定期扫描 running task。
- 本地线程任务检查 thread alive。
- 后台 shell 检查 process poll。
- 输出长时间不增长且像交互提示时，生成 `needs_input` notification。
- 支持外部/远程任务 adapter：`poll_status()`、`fetch_events()`、`restore()`

验收：

- 模拟后台命令输出停在 `Continue?`，poller 生成 needs_input。
- 模拟 remote adapter 返回 completed，任务状态更新并通知。
- poller 错误不会让整个 agent 崩溃。

### 阶段 8：输出文件、增量读取和结果限制

目标：对齐 ClaudeCode `TaskOutput` 和长输出治理。

新增/修改：

- `learning_agent/runtime/task_output.py`
- `learning_agent/core/agent.py` 的 `_offload_tool_output_if_needed`

行为：

- 每个 task 有 output file。
- 支持 append、tail、delta offset、flush、evict。
- 大输出不直接塞回模型，只回传摘要和 output file。
- harness checkpoint 保存 output file 引用，而不是只保存 500 字符。

验收：

- 大输出不会撑爆 prompt。
- status 能展示 output_path 和 tail 摘要。
- task_output 支持 `since_offset` 增量读取。

### 阶段 9：文件锁和原子写入

目标：补上多 worker 和崩溃恢复安全。

修改文件：

- `learning_agent/harness/store.py`
- `learning_agent/harness/queue.py`
- `learning_agent/runtime/command_queue.py`
- `learning_agent/runtime/task_registry.py`

行为：

- JSON 状态写入使用 temp file + replace。
- queue lease 使用 lock file 保护。
- event append 保证单行完整。
- corrupt state 文件不拖垮整体恢复，要进入 quarantine。

验收：

- 两个 worker 同时 lease，不会拿到同一个 run。
- 半写 JSON 文件被跳过并记录风险。
- 单元测试模拟并发领取。

### 阶段 10：状态 CLI/API 升级

目标：让 Codex、controller、用户都能审计长任务状态。

修改文件：

- `learning_agent/harness/cli.py`
- `learning_agent/harness/status.py`

新增命令：

- `python -m learning_agent.harness queue`
- `python -m learning_agent.harness tasks`
- `python -m learning_agent.harness events`
- `python -m learning_agent.harness resume`
- `python -m learning_agent.harness poll`

验收：

- 一个命令能看到所有 running run/task。
- 一个命令能打印最近 N 条事件。
- 一个命令能恢复 interrupted run。

### 阶段 11：确定性验收器升级

目标：让 harness 不只是“跑完”，而是可审计、可复现、能验真。

修改文件：

- `learning_agent/harness/verifier.py`
- `learning_agent/harness/models.py`

新增验收类型：

- marker
- artifact exists
- artifact contains
- JSON schema
- command exit code
- event sequence
- real terminal acceptance scenario

验收：

- 每个 stage 可以配置多个 verifier。
- verifier 结果全部写入 `VerificationResult.checks`。
- acceptance_controller 的 result.json 可以被 verifier 读取并判定。

### 阶段 12：真实终端验收闭环

目标：满足项目规则十七，不能只靠单元测试。

新增场景：

- `learning_agent/acceptance_controller/scenarios/harness_runtime_resume.json`
- `learning_agent/acceptance_controller/scenarios/harness_task_notification.json`
- `learning_agent/acceptance_controller/scenarios/harness_background_shell_watchdog.json`

最终验收：

- `python -m unittest discover learning_agent`
- `python -m compileall learning_agent`
- MCP doctor 如仍适用则运行。
- 启动真实可见 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`。
- 在真实终端输入测试 prompt。
- 观察 agent 输出、harness status、task notification、resume 行为。
- 真实终端验收通过前，不允许声明开发完成。

## 停止条件

如果出现以下情况，必须暂停并汇报：

- 需要决定任务 notification 使用 XML 还是 JSON，而已有测试或用户偏好冲突。
- 需要改动真实终端交互方式，可能影响用户现有使用习惯。
- 需要引入第三方锁库或后台服务。
- 无法打开或观察真实可见终端。

## 推荐执行顺序

先执行阶段 1 到 4，因为它们决定主循环和恢复骨架。

再执行阶段 5 到 8，因为它们把子任务、后台命令和输出治理纳入 harness。

最后执行阶段 9 到 12，因为它们提升并发安全、CLI 可视化和真实验收闭环。

每个阶段完成后都要：

1. 更新 `agent_memory/progress.md`。
2. 更新相关 README 或架构索引。
3. 运行对应单元测试。
4. 如果改到真实 agent 功能，执行真实可见终端验收。
