# Compact/Resume 与 UI/SDK 状态生态对齐 ClaudeCode 计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 learning_agent 的长任务会话压缩、恢复、终端状态和外部 SDK 状态能力，对齐 ClaudeCode 的核心工程能力。

**Architecture:** 本计划不照搬 ClaudeCode 的 TypeScript/Ink 实现，而是在 learning_agent 的 Python 运行时里实现同等职责：append-only transcript、compact boundary、resume loader、状态事件总线、状态快照、终端状态视图和外部 API/SDK 读取入口。

**Tech Stack:** Python standard library, JSONL, existing `learning_agent/core/events.py`, `learning_agent/core/session.py`, `learning_agent/runtime/*`, `learning_agent/harness/*`, `learning_agent/app/http_bridge.py`, `learning_agent/acceptance_controller/*`.

---

## 源码证据基线

ClaudeCode 可参考的源码点：
- `D:\ClaudeCode-main\ClaudeCode-main\QueryEngine.ts`：会话生命周期、SDK 消息输出、compact boundary 写入、用户消息先落盘再请求模型。
- `D:\ClaudeCode-main\ClaudeCode-main\query.ts`：snip compact、microcompact、autocompact、reactive compact、预算追踪和 prompt-too-long 恢复。
- `D:\ClaudeCode-main\ClaudeCode-main\utils\sessionStorage.ts`：transcript JSONL、compact commit/snapshot、resume loader、resume consistency check、进度消息桥接。
- `D:\ClaudeCode-main\ClaudeCode-main\utils\task\framework.ts`：task_started SDK 事件、任务输出 delta、任务状态轮询和 evict。
- `D:\ClaudeCode-main\ClaudeCode-main\components\tasks\*.tsx`：终端里的任务状态 UI，不是网页 UI。
- `D:\ClaudeCode-main\ClaudeCode-main\tools\TaskListTool\TaskListTool.ts` 和 `tools\TaskOutputTool\TaskOutputTool.tsx`：模型可调用的任务状态读取工具。

learning_agent 当前基础：
- `learning_agent/core/events.py`：已有 `AgentEvent`。
- `learning_agent/core/session.py`：已有最小 `SessionStore` 和 `compact_messages_for_session()`。
- `learning_agent/runtime/session_runtime.py`：真实 `run()` 已经接入 harness session runtime。
- `learning_agent/runtime/command_queue.py`：已有 durable prompt/task/resume command queue。
- `learning_agent/runtime/task_registry.py`：已有 durable task registry。
- `learning_agent/harness/*`：已有 run/stage/attempt/store/queue/verifier/cli 基础。
- `learning_agent/app/http_bridge.py` 和 `learning_agent/acceptance_controller/controller.ps1`：已有外部控制和真实终端验收基础。

---

## 成功标准

- 真实终端输入 prompt 后，用户消息必须在模型调用前同步落盘；模型请求前崩溃也能 resume。
- 会话 transcript 必须是 append-only JSONL，包含 uuid、parent_uuid、session_id、run_id、turn_id、event_type、payload。
- compact 后必须写入 compact boundary 事件，保留摘要、被压缩范围、保留尾段、token 估算和证据路径。
- resume 必须从 compact boundary 后重建模型上下文，不重放已完成工具，不重复发送已完成 task notification。
- resume 必须有一致性检查：实际恢复消息数量、最后 checkpoint、compact boundary、未完成 turn 状态都要可审计。
- 终端状态生态必须能显示 run、turn、compact/resume 状态、任务、工具、队列、输出文件和 verifier 结果。
- SDK/API 必须能读取状态快照和事件流；外部 agent 不需要解析截图就能知道当前状态。
- 所有新增能力必须有单元测试、集成测试、CLI/API 测试和真实 `start_oauth_agent.bat` 可见终端验收。

---

## 阶段 1：写源码对齐红线测试

**目标：** 先用失败测试锁住 ClaudeCode 同类能力，避免只写文件不接主循环。

**涉及文件：**
- 新增：`learning_agent/tests/test_compact_resume_alignment.py`
- 新增：`learning_agent/tests/test_status_ecosystem_alignment.py`
- 修改：`agent_memory/progress.md`
- 备份：`learning_agent/test/compact_resume_status_ecosystem_20260531/`

**验收点：**
- 测试证明用户 prompt 在模型调用前已经落盘。
- 测试证明 compact boundary 会进入 transcript 和 harness event。
- 测试证明 resume 不会重跑已完成阶段。
- 测试证明 status snapshot 同时包含 run、turn、task、queue、verifier。

---

## 阶段 2：Transcript v2 和 Turn Ledger

**目标：** 把当前最小 session summary 升级为 ClaudeCode 类似的 append-only 会话证据链。

**涉及文件：**
- 新增：`learning_agent/core/transcript_v2.py`
- 新增：`learning_agent/core/turn_ledger.py`
- 修改：`learning_agent/core/session.py`
- 修改：`learning_agent/core/agent.py`

**设计：**
- 每条记录都有 `uuid` 和 `parent_uuid`，用于恢复时重建链。
- `turn_ledger.json` 保存 turn 状态：`accepted`、`model_running`、`tools_running`、`completed`、`failed`、`interrupted`。
- 用户输入进入模型前必须同步写入 transcript 和 turn ledger。
- 工具调用、工具结果、compact boundary、resume marker 也必须进入 transcript。

**验收点：**
- kill-mid-request 模拟测试中，resume 能看到已接受的用户 prompt。
- transcript 单行损坏不能拖垮整个 resume，需要隔离或跳过坏行。

---

## 阶段 3：Compact Boundary 与压缩策略

**目标：** 从“简单保留最近 N 条消息”升级为有边界、有证据、有恢复语义的 compact。

**涉及文件：**
- 新增：`learning_agent/core/compact.py`
- 新增：`learning_agent/runtime/compact_policy.py`
- 修改：`learning_agent/core/session.py`
- 修改：`learning_agent/core/agent.py`

**设计：**
- 支持三类 compact：
  - `tool_output_snip`：长工具输出落盘，模型上下文只保留摘要和文件路径。
  - `microcompact`：小范围压缩旧工具结果和中间推理。
  - `autocompact`：上下文接近预算上限时生成全局摘要。
- compact boundary 记录：
  - `summary`
  - `first_archived_uuid`
  - `last_archived_uuid`
  - `preserved_tail_uuid`
  - `artifact_paths`
  - `estimated_tokens_before`
  - `estimated_tokens_after`

**验收点：**
- 长上下文触发 autocompact 后，下一轮模型输入包含摘要和尾段，不包含被压缩的大段原文。
- 被压缩原文仍在 transcript 或 artifact 文件里可审计。

---

## 阶段 4：Resume Loader 与一致性检查

**目标：** 让恢复不是“拼一个 summary”，而是从 transcript、compact boundary、turn ledger、harness checkpoint 共同恢复。

**涉及文件：**
- 新增：`learning_agent/core/resume_loader.py`
- 修改：`learning_agent/runtime/resume.py`
- 修改：`learning_agent/runtime/session_runtime.py`
- 修改：`learning_agent/harness/store.py`

**设计：**
- resume loader 从最后一个有效 compact boundary 后开始重建上下文。
- 工具调用必须和工具结果成对恢复；缺结果的工具标记为 interrupted，不自动重放危险工具。
- 已完成 task notification 标记为 consumed，未消费的 queued notification 继续进入 runtime queue。
- 生成 `resume_consistency` 事件，记录 expected/actual delta。

**验收点：**
- 中断后恢复不会重跑已完成阶段。
- 如果 transcript 链断裂，状态页显示 `resume_needs_review`，不假装成功。

---

## 阶段 5：主循环接入 Compact/Resume

**目标：** 把 compact/resume 变成真实 `run_events()` 的一部分，而不是旁路工具。

**涉及文件：**
- 修改：`learning_agent/core/agent.py`
- 修改：`learning_agent/runtime/session_runtime.py`
- 修改：`learning_agent/runtime/command_queue.py`

**设计：**
- 每轮模型请求前检查 compact policy。
- compact 发生时，`run_events()` 产出 `compact_started`、`compact_completed`。
- `resume_interrupted` command 不只是文本块，还要调用 resume loader 重建上下文。
- 失败或异常时，turn ledger 标记 interrupted，并写入状态事件。

**验收点：**
- `agent.run()`、`run_events()`、harness event log、session transcript 四者看到同一个 run/turn。
- 真实终端 resume 场景能看到 compact/resume 状态。

---

## 阶段 6：状态事件协议

**目标：** 建立类似 ClaudeCode SDK event 的状态事件层。

**涉及文件：**
- 新增：`learning_agent/runtime/status_events.py`
- 新增：`learning_agent/runtime/status_store.py`
- 修改：`learning_agent/core/events.py`
- 修改：`learning_agent/runtime/task_registry.py`
- 修改：`learning_agent/harness/runner.py`

**事件类型：**
- `run_started`
- `turn_accepted`
- `model_request_started`
- `model_response_completed`
- `tool_started`
- `tool_progress`
- `tool_completed`
- `task_started`
- `task_progress`
- `task_completed`
- `compact_started`
- `compact_completed`
- `resume_started`
- `resume_completed`
- `verifier_result`
- `run_completed`
- `run_failed`

**验收点：**
- 每个事件 JSON schema 稳定。
- 外部 agent 可以只读 `memory/status/events.jsonl` 还原当前状态。

---

## 阶段 7：状态快照聚合器

**目标：** 把分散的 run、session、task、queue、event、verifier 汇总成一个可读快照。

**涉及文件：**
- 新增：`learning_agent/runtime/status_snapshot.py`
- 修改：`learning_agent/harness/status.py`
- 修改：`learning_agent/harness/cli.py`

**快照字段：**
- `runs`
- `current_turn`
- `sessions`
- `compact`
- `resume`
- `runtime_commands`
- `tasks`
- `background_commands`
- `team_peers`
- `latest_events`
- `verifier_results`
- `outputs`

**验收点：**
- CLI 能输出文本和 JSON 两种格式。
- 状态中必须看得见 output path 和最近 output tail。

---

## 阶段 8：终端状态 UI

**目标：** 对齐 ClaudeCode 的“终端内 UI”，不是做网页。

**涉及文件：**
- 修改：`learning_agent/app/interactive.py`
- 新增：`learning_agent/app/status_renderer.py`
- 修改：`learning_agent/acceptance_controller/scenarios/*.json`

**设计：**
- 在终端中支持 `/status`、`/tasks`、`/sessions`、`/resume`。
- 长任务运行时打印紧凑状态块，不刷屏、不破坏输入提示符。
- 状态块显示：
  - 当前 run/turn
  - 是否 compact
  - 是否 resume
  - 正在运行的工具和后台任务
  - 最近 verifier 结果
  - 输出文件路径

**验收点：**
- 真实可见终端输入 `/status` 后能看到 compact/resume/task/run 信息。
- controller 能通过事件和最终截图断言状态块存在。

---

## 阶段 9：SDK/API 状态生态

**目标：** 让 Codex、其他 agent、脚本或桌面壳可以不靠截图读取 learning_agent 状态。

**涉及文件：**
- 新增：`learning_agent/sdk/status.py`
- 修改：`learning_agent/app/http_bridge.py`
- 新增：`learning_agent/tests/test_status_api.py`

**接口：**
- Python SDK：
  - `get_status_snapshot(workspace)`
  - `list_status_events(workspace, since_sequence=None)`
  - `watch_status_events(workspace)`
- HTTP bridge：
  - `GET /status`
  - `GET /events?since=N`
  - `GET /runs`
  - `GET /tasks`
  - `GET /sessions`

**验收点：**
- HTTP/API 返回 JSON 可被其他 agent 直接消费。
- 事件游标 `since` 不重复、不漏新事件。

---

## 阶段 10：模型可调用状态工具

**目标：** 对齐 ClaudeCode 的 TaskList/TaskOutput 思路，让 learning_agent 自己也能读状态。

**涉及文件：**
- 修改：`learning_agent/tools/schemas.py`
- 修改：`learning_agent/core/agent.py`
- 新增：`learning_agent/tests/test_status_tools.py`

**工具：**
- `status_snapshot`
- `session_list`
- `session_resume`
- `compact_status`
- `task_status`
- `event_tail`

**验收点：**
- 模型不用用户解释，也能主动查询“我现在跑到哪一步了”。
- 工具结果有最大长度限制，长输出走文件路径。

---

## 阶段 11：验收控制器和真实终端场景

**目标：** 所有能力都必须经真实可见终端验收，而不是只跑单测。

**涉及文件：**
- 新增：`learning_agent/acceptance_controller/scenarios/compact_resume_status.json`
- 新增：`learning_agent/acceptance_controller/scenarios/status_sdk_api.json`
- 修改：`learning_agent/acceptance/verifier.py`

**真实验收场景：**
- 场景 A：制造长上下文，触发 compact，终端 `/status` 显示 compact boundary。
- 场景 B：制造 interrupted run，重启后 resume，不重跑已完成阶段。
- 场景 C：启动后台任务，状态 UI/API 同时显示 running/completed/output。

**验收点：**
- `result.json` 必须 `completed=true` 且 `assertion.passed=true`。
- 独立 verifier 必须复验通过。

---

## 阶段 12：文档、备份和最终回归

**目标：** 让用户和后续 agent 都能理解、复查和继续开发。

**涉及文件：**
- 修改：`learning_agent/README.md`
- 修改：`learning_agent/AGENT_ARCHITECTURE_INDEX.md`
- 修改：`agent_memory/context.md`
- 修改：`agent_memory/progress.md`
- 备份：`learning_agent/test/compact_resume_status_ecosystem_20260531/`

**最终命令：**
- `python -m py_compile learning_agent\core\agent.py`
- `python -m unittest learning_agent.tests.test_compact_resume_alignment`
- `python -m unittest learning_agent.tests.test_status_ecosystem_alignment`
- `python -m unittest discover learning_agent`
- `python -m compileall learning_agent`
- `python learning_agent\learning_agent.py mcp-doctor`
- `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath <absolute scenario path>`
- `python -m learning_agent.acceptance.verifier <run_dir> <scenario.json>`

---

## 范围边界

本计划包含：
- compact/resume 对齐。
- 终端状态 UI。
- 状态 SDK/API。
- 模型可调用状态工具。
- 真实可见终端验收。

本计划暂不包含：
- 远程任务系统。
- 工具流式并发执行升级。
- 完整网页 UI。
- 复制 ClaudeCode 的产品专有云服务。

---

## 推荐执行顺序

先执行阶段 1 到阶段 5，完成 compact/resume 主链路。

再执行阶段 6 到阶段 10，完成状态生态。

最后执行阶段 11 到阶段 12，完成真实终端验收和文档备份。
