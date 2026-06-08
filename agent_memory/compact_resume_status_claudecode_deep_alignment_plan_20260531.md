# Compact/Resume 与 UI/SDK 状态生态深度对齐 ClaudeCode 方案

记录日期：2026-05-31

状态：等待用户确认后执行。本文档只规划，不修改运行时代码。

## 一句话结论

当前 `learning_agent` 已经有 compact/resume 和状态生态的基础骨架，但还没有达到 ClaudeCode 的复杂度。本计划的目标不是再补几个旁路工具，而是把这些能力接入真实主循环，并让异常、压缩、恢复、状态观察都能被源码、测试、事件日志和真实终端验收证明。

## 对齐口径

这里的“对齐 ClaudeCode”不是复制 ClaudeCode 的 TypeScript/Ink 代码，也不是做网页 UI。

这里的对齐是指：在 `learning_agent` 的 Python 架构中实现同等职责。

- compact/resume 对齐：长上下文能分层压缩；压缩边界可审计；prompt 过长或媒体过大错误能自动恢复；进程中断后能从 transcript、checkpoint、turn ledger 和 compact boundary 恢复；不能重跑已经完成的危险动作。
- UI/SDK 状态生态对齐：真实终端能看到状态；HTTP/API/SDK 能观察同一条事件流；模型自己也能调用状态工具查看当前 run、turn、task、event、compact、resume、verifier 结果。
- 验收对齐：单元测试、集成测试、状态文件、事件顺序和真实 `start_oauth_agent.bat` 可见终端验收必须同时通过。

## 源码基线

### ClaudeCode 已有能力

- `D:\ClaudeCode-main\ClaudeCode-main\query.ts` 第 396 行附近：先 snip，再 microcompact，再 context collapse，再 autocompact。说明 ClaudeCode 的 compact 是多层策略，不是只保留最近 N 条消息。
- `D:\ClaudeCode-main\ClaudeCode-main\query.ts` 第 1063 行附近：prompt-too-long 先尝试 context collapse drain，再尝试 reactive compact，然后重试模型请求。说明 ClaudeCode 能在模型拒绝长上下文后自动恢复。
- `D:\ClaudeCode-main\ClaudeCode-main\utils\conversationRecovery.ts` 第 456 行附近：`loadConversationForResume()` 会恢复消息、turn 中断状态、文件历史、context collapse commit、session 元数据、worktree/PR 信息。说明 ClaudeCode 的 resume 不是简单读取 summary。
- `D:\ClaudeCode-main\ClaudeCode-main\query.ts` 第 713 行附近：会对 orphaned messages 产生 tombstone，让 UI/transcript 删除错误悬挂消息。
- `D:\ClaudeCode-main\ClaudeCode-main\query.ts` 第 1412 行附近：会生成 ToolUseSummary，让下一轮和 SDK/UI 能理解上一轮工具执行摘要。

### learning_agent 当前已有能力

- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\agent.py`：`run()` 已经委托到 harness session runtime，`run_events()` 已经写入 transcript v2、turn ledger、status event。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\compact.py`：已有 `compact_messages_with_boundary()`，能产生基础 compact boundary。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\resume_loader.py`：已有 `ResumeLoader`，能从 summary、transcript v2、compact boundary 粗略重建模型上下文。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\runtime\status_snapshot.py`：已有统一状态快照，能聚合 run、task、command、session、status event。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\http_bridge.py`：已有 `/status` 和 `/events`。
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\sdk\status.py`：已有 SDK 状态读取和轮询。

### 当前缺口

- compact 仍偏单层：还缺 snip、microcompact、context collapse commit/snapshot、autocompact 预算追踪、reactive compact 错误恢复。
- resume 仍偏粗略：还缺未完成 tool_use/tool_result 修复、orphan message 清理、坏 transcript 行隔离、skill/plan/file history 恢复、session 元数据恢复。
- 状态生态仍偏快照：还缺 ClaudeCode 那种主循环事件、工具摘要、tombstone、compact/retry/resume 生命周期完全统一的事件协议。
- SDK/API 仍偏基础读取：还缺事件类型过滤、游标恢复、schema 版本、watch 断点续读、一致性报告和错误状态。
- 真实验收还不够硬：之前只证明基础结构能跑，没有覆盖 prompt-too-long reactive compact、坏 transcript、未完成工具、进程中断恢复等复杂场景。

## 成功标准

本计划完成后，才允许说“compact/resume 复杂度和 UI/SDK 状态生态已经对齐 ClaudeCode 核心能力”。

- 长上下文必须能触发多层 compact，并能在状态事件中看到 `snip_compact`、`microcompact`、`context_collapse`、`autocompact`。
- 模型返回 prompt-too-long 或媒体过大错误时，必须能触发 `reactive_compact_retry`，并且最多重试一次，失败后明确暴露错误。
- resume 必须能识别 interrupted turn、未完成 tool_use、缺失 tool_result、坏 transcript 行，并给出 `resume_safe`、`resume_needs_review` 或 `resume_blocked`。
- `agent.run()`、`run_events()`、harness event log、status event log、session transcript 必须共享同一条 run/turn 事实链。
- `/status`、`/events`、SDK、CLI、模型状态工具必须来自同一套状态事件和快照聚合器。
- 真实终端输入 `/status` 时，必须能看到 compact、resume、run、turn、task、queue、verifier 的关键状态。
- 所有新增和修改代码必须按项目规则写逐行中文注释，并备份到 `learning_agent/test/compact_resume_status_claudecode_deep_alignment_20260531/`。
- 最终必须通过自动化测试、compileall、真实 `start_oauth_agent.bat` 可见终端验收和独立 verifier 复验。

## 阶段 1：红线测试与差距固化

目标：先用失败测试锁住 ClaudeCode 级能力，避免再次只完成文件和接口。

拟修改/新增：

- 新增 `learning_agent/tests/test_compact_deep_alignment.py`
- 新增 `learning_agent/tests/test_resume_deep_alignment.py`
- 新增 `learning_agent/tests/test_status_ecosystem_deep_alignment.py`
- 更新 `agent_memory/progress.md`

验收：

- 测试必须覆盖多层 compact、reactive compact、坏 transcript、未完成 tool_use、status event schema、SDK watch 游标。
- 初始红测必须能证明当前确实还没对齐。
- 每个红测断言都要对应 ClaudeCode 源码能力点，不能只测自己想象的行为。

## 阶段 2：状态事件协议 v2

目标：先建立统一事件语言，让主循环、compact、resume、SDK、终端 UI 说同一种话。

拟修改/新增：

- 修改 `learning_agent/runtime/status_events.py`
- 修改 `learning_agent/core/events.py`
- 修改 `learning_agent/runtime/status_snapshot.py`
- 新增 `learning_agent/runtime/status_schema.py`

事件类型：

- `run_started`
- `turn_accepted`
- `model_request_started`
- `model_message_delta`
- `model_response_completed`
- `tool_use_seen`
- `tool_result_seen`
- `tool_use_summary_created`
- `tombstone_created`
- `compact_started`
- `compact_completed`
- `reactive_compact_retry`
- `resume_started`
- `resume_completed`
- `resume_needs_review`
- `resume_blocked`
- `status_snapshot_created`
- `verifier_result`

验收：

- 每个事件必须有 `schema_version`、`sequence`、`timestamp`、`session_id`、`run_id`、`turn_id`、`event_type`、`payload`。
- `/events?since_sequence=N` 不能重复旧事件，也不能漏掉新事件。
- SDK watch 断开后能从 sequence 继续。

## 阶段 3：多层 Compact 策略

目标：从“简单保留最近消息”升级为 ClaudeCode 式多层压缩。

拟修改/新增：

- 修改 `learning_agent/core/compact.py`
- 新增 `learning_agent/core/compact_policy.py`
- 新增 `learning_agent/core/context_collapse.py`
- 新增 `learning_agent/core/compact_artifacts.py`

能力：

- `tool_output_snip`：长工具输出只给模型保留摘要和 artifact 路径，完整内容落盘。
- `microcompact`：压缩旧的工具结果和中间 assistant 消息，保留关键事实。
- `context_collapse`：维护 collapse commit log 和 snapshot，下次进入主循环时按 commit 投影视图。
- `autocompact`：模型请求前根据消息数、字符数和估算 token 触发全局摘要。

验收：

- 长工具输出不会把模型上下文撑爆。
- compact boundary 必须包含 archived 范围、preserved tail、artifact paths、估算压缩前后大小。
- 原始证据必须仍能从 transcript 或 artifact 找回。

## 阶段 4：Reactive Compact 与错误恢复

目标：模型已经报“上下文太长”时，agent 能自己补救，而不是直接失败。

拟修改/新增：

- 新增 `learning_agent/core/reactive_compact.py`
- 修改 `learning_agent/core/agent.py`
- 修改 `learning_agent/models/*` 中模型错误归一化入口

能力：

- 识别 prompt-too-long 错误。
- 识别媒体过大错误。
- 先尝试 context collapse drain。
- 再尝试 reactive compact。
- 最多重试一次，避免无限循环。
- 重试、失败、放弃都写入 status event。

验收：

- 测试模拟 prompt-too-long，必须看到 `reactive_compact_retry`。
- 如果重试仍失败，状态必须是 `resume_blocked` 或 `run_failed`，不能假装成功。
- 真实终端验收必须能看到对应恢复状态。

## 阶段 5：Resume Loader v2

目标：让 resume 从“读取上下文”升级为“恢复会话状态并修复不完整消息链”。

拟修改/新增：

- 修改 `learning_agent/core/resume_loader.py`
- 修改 `learning_agent/core/transcript_v2.py`
- 修改 `learning_agent/core/turn_ledger.py`
- 新增 `learning_agent/core/resume_repair.py`

能力：

- 跳过或隔离损坏 JSONL 行。
- 修复 assistant tool_use 没有 tool_result 的情况。
- 识别 orphan assistant/tool message 并产生 tombstone。
- 识别 interrupted turn，并生成可审计恢复计划。
- 恢复 context collapse commit/snapshot。
- 恢复 skill 状态、计划状态和文件历史引用。
- 输出 `resume_consistency` 报告。

验收：

- 坏 transcript 行不会拖垮整个 resume。
- 未完成工具不会被静默重跑。
- 需要人工确认的危险恢复必须标为 `resume_needs_review`。
- 已完成 turn/stage 不得重跑。

## 阶段 6：真实主循环接管

目标：把 compact/resume v2 接入 `run_events()`，不能做成旁路系统。

拟修改/新增：

- 修改 `learning_agent/core/agent.py`
- 修改 `learning_agent/runtime/session_runtime.py`
- 修改 `learning_agent/runtime/command_queue.py`

能力：

- 每轮模型请求前执行 compact policy。
- 捕获模型上下文错误后执行 reactive compact。
- `resume_interrupted` command 触发 ResumeLoader v2，而不是只拼一段提示词。
- `run_events()` 发出的事件和 status event/harness event 同步。

验收：

- `agent.run()`、`run_events()`、harness event log、status event log、transcript v2 中的 run_id/turn_id 必须一致。
- 进程中断后恢复，不重跑已完成阶段。
- 真实终端输入 prompt 后必须自动创建 durable run，并产生统一状态事件。

## 阶段 7：状态快照 v2

目标：让状态快照不只是统计数量，而是能给人和外部 agent 判断“现在卡在哪里”。

拟修改/新增：

- 修改 `learning_agent/runtime/status_snapshot.py`
- 修改 `learning_agent/app/status_renderer.py`
- 修改 `learning_agent/harness/status.py`

快照字段：

- `current_run`
- `current_turn`
- `compact`
- `resume`
- `model`
- `tools`
- `tasks`
- `commands`
- `sessions`
- `verifiers`
- `outputs`
- `latest_events`
- `health`

验收：

- 快照必须能显示最近一次 compact boundary。
- 快照必须能显示最近一次 resume consistency。
- 快照必须能显示是否有 `resume_needs_review`。
- 快照必须能显示 verifier 最近结果。

## 阶段 8：HTTP API 与 SDK 对齐

目标：让 Codex、其他 agent、脚本和桌面壳都能稳定观察 `learning_agent`。

拟修改/新增：

- 修改 `learning_agent/app/http_bridge.py`
- 修改 `learning_agent/sdk/status.py`
- 新增 `learning_agent/sdk/events.py`
- 新增 `learning_agent/tests/test_status_api_deep_alignment.py`

接口：

- `GET /status`
- `GET /events?since_sequence=N`
- `GET /sessions`
- `GET /sessions/{session_id}/resume`
- `GET /runs`
- `GET /runs/{run_id}`
- `GET /health`

SDK：

- `get_status_snapshot(workspace)`
- `list_status_events(workspace, since_sequence=0, event_type=None)`
- `watch_status_events(workspace, since_sequence=0, event_types=None)`
- `load_resume_report(workspace, session_id)`

验收：

- HTTP 和 SDK 读取同一份 status event store。
- SDK watch 不能靠解析终端输出。
- API 返回 JSON schema 稳定，坏数据要进入 `health.warnings`。

## 阶段 9：真实终端 UI 状态生态

目标：对齐 ClaudeCode 的“终端内状态生态”，不是做网页。

拟修改/新增：

- 修改 `learning_agent/app/interactive.py`
- 修改 `learning_agent/app/status_renderer.py`
- 修改 `learning_agent/acceptance_controller/scenarios/*.json`

终端命令：

- `/status`
- `/events`
- `/sessions`
- `/resume <session_id>`
- `/compact`

验收：

- 用户在真实终端输入 `/status`，能看到 run、turn、compact、resume、task、queue、verifier。
- 状态输出不能破坏交互提示符。
- controller 和 verifier 能从真实终端 run 里证明状态块出现过。

## 阶段 10：模型可调用状态工具升级

目标：让 `learning_agent` 自己也能查询自己的状态，支持长任务不跑偏。

拟修改/新增：

- 修改 `learning_agent/tools/schemas.py`
- 修改 `learning_agent/tools/executor.py`
- 修改 `learning_agent/tools/catalog.py`
- 修改 `learning_agent/core/agent.py`

工具：

- `status_snapshot`
- `event_tail`
- `session_resume`
- `compact_status`
- `resume_report`
- `run_status`

验收：

- 工具输出有长度限制，大结果返回 artifact path。
- 模型能根据 `resume_report` 判断是否继续、等待用户、还是停止。
- 状态工具只读，不允许产生副作用。

## 阶段 11：兼容迁移与旧数据处理

目标：不能因为升级破坏已有 memory/session/harness 数据。

拟修改/新增：

- 新增 `learning_agent/runtime/migrations.py`
- 修改 `learning_agent/core/session.py`
- 修改 `learning_agent/core/transcript_v2.py`

能力：

- 旧 summary 可继续读取。
- 旧 transcript 没有 schema_version 时能兼容。
- 损坏文件进入 quarantine，不影响其他 session。
- 迁移结果写入 status event。

验收：

- 旧测试仍通过。
- 手工构造旧格式 session 后，`/status` 不崩溃。
- 迁移不删除原文件。

## 阶段 12：验收控制器与真实场景

目标：用真实终端验证复杂能力，而不是只用单元测试。

拟修改/新增：

- 新增 `learning_agent/acceptance_controller/scenarios/compact_reactive_recovery.json`
- 新增 `learning_agent/acceptance_controller/scenarios/resume_interrupted_turn_v2.json`
- 新增 `learning_agent/acceptance_controller/scenarios/status_ecosystem_v2.json`
- 修改 `learning_agent/acceptance/verifier.py`

真实场景：

- 场景 A：长上下文触发 autocompact，`/status` 显示 compact boundary。
- 场景 B：模拟 prompt-too-long，触发 reactive compact retry。
- 场景 C：模拟 interrupted turn，重启后 resume，不重跑已完成阶段。
- 场景 D：损坏 transcript 单行，状态显示 warning，但仍能恢复安全部分。
- 场景 E：SDK watch 读取事件，真实终端同时显示状态。

验收：

- `result.json` 必须 `completed=true` 且 `assertion.passed=true`。
- 独立 verifier 必须复验通过。
- 真实可见终端验收未完成时，不能声明开发完成。

## 阶段 13：文档、备份与最终评估

目标：让用户和后续 agent 能看懂改了什么、为什么改、如何验收。

拟修改/新增：

- 更新 `agent_memory/context.md`
- 更新 `agent_memory/progress.md`
- 更新 `agent_memory/bugs.md`
- 更新 `learning_agent/AGENT_ARCHITECTURE_INDEX.md`
- 备份到 `learning_agent/test/compact_resume_status_claudecode_deep_alignment_20260531/`

验收：

- 文档必须明确说明哪些能力已对齐，哪些能力仍未对齐。
- 如果只完成 compact/resume 和 UI/SDK 状态生态，不能顺手声称工具流式并发、远程任务也已对齐。
- 最终给出新的源码对比百分比，并列出证据文件。

## 不在本计划范围内

这些能力也很重要，但不放进本轮，避免任务失焦。

- ClaudeCode 级 StreamingToolExecutor。
- 完整远程任务/sidecar。
- 完整团队 teammate 任务协议。
- 图形化网页 UI。
- 复制 ClaudeCode 私有云服务。

本计划完成后，`compact/resume` 和 `UI/SDK 状态生态` 应该能从当前大约 55%-70% 提升到 85%-90%。但整个 agent harness 是否全面对齐 ClaudeCode，还要另算工具流式执行、远程任务和团队协作能力。

## 停止条件

出现以下情况必须暂停并汇报：

- 需要改变真实终端交互习惯，可能影响用户使用。
- 需要引入第三方依赖或后台服务。
- 无法启动或观察真实 `start_oauth_agent.bat` 终端。
- 模型 provider 无法稳定模拟 prompt-too-long 或媒体错误，需要改用 fake model 测试。
- 发现 ClaudeCode 源码能力理解有误，需要重写计划。

## 执行前确认

等待用户确认后，才能开始改运行时代码。

建议确认语：

“确认，按 `agent_memory/compact_resume_status_claudecode_deep_alignment_plan_20260531.md` 执行。”
