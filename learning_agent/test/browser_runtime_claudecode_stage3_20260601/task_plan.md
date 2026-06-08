# Active Plan: Browser Runtime ClaudeCode Alignment

> 当前执行计划以 `agent_memory/browser_runtime_claudecode_upgrade_plan_20260601.md` 为准。
> 用户已确认计划，当前已进入代码改造；截至 2026-06-01 已完成 Stage 1 和 Stage 2 的持久化 store + 浏览器 MCP server 工具执行入口接入 + agent/status 事件镜像，专用 browser status snapshot/CLI/API 仍待 Stage 11 完成。

## Active Success Criteria

- [x] 基于 ClaudeCode 源码证据制定计划，不把 README 当关键证据。
- [x] 区分 ClaudeCode 源码可确认能力和外部 Chrome 扩展/外部包无法确认能力。
- [x] 明确 learning_agent 当前浏览器能力基线和主要缺口。
- [x] 制定 Browser Protocol、Runtime Store、Session Manager、Observation Engine、Locator Engine、Action Executor、Recovery/Replay/Verifier、Status Ecosystem 八层架构。
- [x] 将计划保存到 `agent_memory/browser_runtime_claudecode_upgrade_plan_20260601.md`。
- [x] 将实施计划保存到 `docs/superpowers/plans/2026-06-01-browser-runtime-claudecode-alignment.md`。
- [x] 将学习备份保存到 `learning_agent/test/browser_runtime_claudecode_upgrade_plan_20260601/plan.md`。
- [x] 等用户确认后，从阶段 1：Browser Runtime 协议层开始执行。
- [x] Stage 1 协议层自动化测试通过，并备份到 `learning_agent/test/browser_runtime_claudecode_stage1_20260601/`。
- [x] Stage 2 持久化 store 自动化测试通过，并备份到 `learning_agent/test/browser_runtime_claudecode_stage2_20260601/`。
- [x] Stage 2 生产接入第一步：真实浏览器工具开始/完成/失败事件写入 BrowserRuntimeStore。
- [x] Stage 2 生产接入第二步：browser run 镜像到 `browser_runtime_event` 统一 status event。
- [ ] Stage 11 仍需状态生态：status snapshot/CLI/API 增加专门 browser section。
- [ ] 最终实现后必须通过自动化测试和 `learning_agent/start_oauth_agent.bat` 真实可见终端验收。

## Active Stages

- [x] Stage 0: 建立计划、源码证据和范围边界。
- [x] Stage 1: Browser Runtime 协议层。
- [x] Stage 2: Browser Runtime Store 和 harness 事件接入。（store、MCP server 工具事件、agent/status event 镜像已完成；专门状态视图放到 Stage 11）
- [ ] Stage 3: Browser session manager。
- [ ] Stage 4: Observation Engine。
- [ ] Stage 5: Locator Engine。
- [ ] Stage 6: Action Executor 和流式工具执行。
- [ ] Stage 7: Recovery Manager。
- [ ] Stage 8: Browser Flow Runtime。
- [ ] Stage 9: Secret Vault 和登录态安全。
- [ ] Stage 10: Replay + Acceptance Verifier 2.0。
- [ ] Stage 11: 浏览器状态生态。
- [ ] Stage 12: 真实可见终端和真实浏览器验收矩阵。

---

# Historical Plan: ClaudeCode-Aligned Learning Agent Harness Runtime

> 当前执行计划以 `agent_memory/harness_claudecode_alignment_plan_20260531.md` 为准。
> 旧的 8 阶段独立 harness 已完成；本轮目标是把 harness 接入真实主循环、持久任务、通知回灌、恢复和真实终端验收。

## Active Success Criteria

- [x] 真实终端输入 prompt 后会创建 durable harness run 和 runtime command event。
- [x] `agent.run()` 兼容旧调用，但内部事件会被 session runtime/harness runtime 持久化。
- [x] interrupted run 能检测并重新入队。
- [x] task/background command 状态不只存在内存里，而是进入 durable task registry。
- [x] 后台任务完成后能生成 task notification 并回灌下一轮上下文。
- [x] task output 支持 append、tail、delta、flush、evict。
- [x] harness store/queue/runtime queue/task registry 使用原子写入和锁保护。
- [x] CLI 能查看 queue、tasks、events、resume、poll。
- [x] verifier 支持 marker、artifact、JSON schema、command exit code、event sequence、acceptance result。
- [x] 代码修改备份到 `learning_agent/test/harness_claudecode_alignment_20260531/`。
- [x] 自动化测试、compileall 和真实可见终端验收全部通过。

## Active Stages

- [x] Stage 1: 源码基线和测试红线。
- [x] Stage 2: RuntimeCommandQueue。
- [x] Stage 3: HarnessSessionRuntime。
- [x] Stage 4: Interrupted Turn Resume。
- [x] Stage 5: Durable Task Registry。
- [x] Stage 6: Task Notification 回灌。
- [x] Stage 7: Task Poller 和 Watchdog。
- [x] Stage 8: 输出文件、增量读取和结果限制。
- [x] Stage 9: 文件锁和原子写入。
- [x] Stage 10: 状态 CLI/API 升级。
- [x] Stage 11: 确定性验收器升级。
- [x] Stage 12: 真实终端验收闭环。

---

# Historical Plan: Learning Agent Long-Task Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an independent durable long-task harness for `learning_agent` so long work can survive interruption, resume from checkpoints, run staged acceptance, and expose visible status.

**Architecture:** Build a new `learning_agent/harness/` package around durable JSON state, append-only JSONL events, queue leases, stage checkpoints, retry/recovery policy, stage verifiers, and status rendering. Keep the first version independent from the main interactive loop, then expose a CLI/API surface that Codex or another controller can inspect.

**Tech Stack:** Python standard library, `unittest`, JSON/JSONL files, existing `learning_agent` package style, real visible terminal acceptance through `learning_agent/start_oauth_agent.bat`.

---

## Success Criteria

- The project contains a dedicated `learning_agent/harness/` module.
- Harness task state is persisted under `learning_agent/memory/harness/` or a caller-provided store path.
- The queue can enqueue, lease, heartbeat, complete, and retry tasks without losing state across process restarts.
- A task can be split into named stages, and each stage records attempts, checkpoints, acceptance status, failure reason, and timestamps.
- Stage verification can fail or pass using deterministic assertions.
- Recoverable failures can trigger automatic retry/continue without restarting successful earlier stages.
- Status rendering shows task id, current stage, status, attempts, last event, and acceptance state in a human-readable form.
- A command/API entry point allows another agent to inspect harness state.
- All new code has Chinese comments explaining intent and consequence.
- New/modified code is backed up under `learning_agent/test/long_task_harness_20260531/`.
- Final completion requires automated tests, compile check, and real visible `learning_agent/start_oauth_agent.bat` interaction acceptance.

## Scope Boundary

- In scope: independent harness package, durable store, queue, runner, verifier, recovery policy, status renderer, CLI, tests, docs, backups, visible terminal smoke acceptance.
- Out of scope for this first pass: replacing the existing `LearningAgent.run()` loop, building a full TUI dashboard, remote cloud execution, or changing OAuth/model provider behavior.

## Eight Stages

### Stage 1: Planning And Inventory

- [x] Confirm current `learning_agent` has acceptance harness pieces but not an independent durable long-task harness.
- [x] Record this task plan before implementation.
- [x] Keep `agent_memory/progress.md` updated after each major phase.

### Stage 2: Durable State Schema

- [x] Add tests for run/task/stage/attempt/event serialization.
- [x] Implement `learning_agent/harness/models.py`.
- [x] Implement stable statuses and timestamps.

### Stage 3: Persistent Store And Event Log

- [x] Add tests for JSON state persistence and JSONL event replay.
- [x] Implement `learning_agent/harness/store.py`.
- [x] Ensure writes create parent directories and preserve evidence.

### Stage 4: Durable Queue With Leases

- [x] Add tests for enqueue, lease, heartbeat, complete, retry, and restart reload.
- [x] Implement `learning_agent/harness/queue.py`.
- [x] Prevent two workers from claiming the same task through lease state.

### Stage 5: Stage Verifier And Acceptance Gates

- [x] Add tests for marker checks and artifact checks.
- [x] Implement `learning_agent/harness/verifier.py`.
- [x] Ensure failed verification records auditable reasons.

### Stage 6: Runner, Checkpoint, And Recovery

- [x] Add tests for multi-stage execution.
- [x] Add tests for recoverable failure retry and checkpoint resume.
- [x] Implement `learning_agent/harness/recovery.py`.
- [x] Implement `learning_agent/harness/runner.py`.

### Stage 7: Status API And CLI

- [x] Add tests for human-readable status output.
- [x] Implement `learning_agent/harness/status.py`.
- [x] Implement `learning_agent/harness/cli.py` and `learning_agent/harness/__main__.py`.

### Stage 8: Documentation, Backups, And Real Acceptance

- [x] Update docs with how another agent should control and inspect the harness.
- [x] Copy all new/modified code to `learning_agent/test/long_task_harness_20260531/`.
- [x] Run focused harness tests.
- [x] Run full `python -m unittest discover learning_agent`.
- [x] Run `python -m compileall learning_agent`.
- [x] Start real visible `learning_agent/start_oauth_agent.bat`, input a harness-status prompt, observe output, and only then mark the task complete.

## Final Gate

The task is not truly complete until all three are true:

1. Code and docs are implemented.
2. Automated tests and compile checks pass.
3. Real visible terminal interaction with `learning_agent/start_oauth_agent.bat` verifies the installed `learning_agent` can answer about the new harness.
# 当前任务：真实浏览器能力对齐 ClaudeCode（2026-05-31）

## 任务目标

把 `learning_agent` 的真实浏览器能力补强到更接近 ClaudeCode 源码中可确认的浏览器生态能力，重点覆盖页面失败恢复、视觉定位、复杂网站流程、登录态安全、插件兼容、异常重试和任务回放。

## 执行阶段

1. 建立源码证据和书面计划。
2. 先写失败测试覆盖浏览器缺口。
3. 实现浏览器动作轨迹和安全回放。
4. 实现页面失败恢复和统一异常重试。
5. 实现视觉定位和坐标点击。
6. 实现复杂网站流程执行器。
7. 加强登录态安全边界。
8. 增加插件兼容状态报告。
9. 备份修改、运行自动化测试、完成真实可见终端验收。

## 验收标准

1. 所有结论必须有源码证据。
2. 新增或修改代码必须有中文注释并备份到 `learning_agent/test/`。
3. 自动化测试必须覆盖新增浏览器能力。
4. 必须尝试 `learning_agent/start_oauth_agent.bat` 真实可见终端交互验收。

# 当前任务：Browser Runtime ClaudeCode 对齐 Stage 3（2026-06-01）

## 本阶段目标

把浏览器 session 和 tab 生命周期从 `browser_automation_mcp_server.py` 的零散字段里抽出，形成可被状态生态、回放、恢复和后续 verifier 复用的 `BrowserSessionManager`。

## Stage 3 验收标准

- [x] 有独立 `BrowserTabRegistry`，tab id 不跨 session 复用。
- [x] 有独立 `BrowserSessionManager`，能表示无头独立 Chromium、肉眼可见 Chromium、真实 Chrome CDP。
- [x] 真实 Chrome profile 摘要不保存完整本地 User Data 路径。
- [x] `BrowserAutomationServer` 生产入口拥有 `session_manager`。
- [x] 页面登记、关闭、切换、打开成功后同步 session manager。
- [x] `browser_plugin_status` 输出 session_mode、connected、visible、headless、tab_count。
- [x] 新增/修改文件备份到 `learning_agent/test/browser_runtime_claudecode_stage3_20260601/`。
- [x] 自动化测试通过。
- [x] 真实可见终端交互验收通过。

## 当前停止条件

Stage 3 已完成，但整套 Browser Runtime ClaudeCode 对齐仍有 Stage 4-12 未执行；不能把 Stage 3 完成误报为 12 阶段全部完成。

## Stage 3 真实可见终端证据

- 验收 run：`learning_agent/acceptance_controller/runs/browser_visible_runtime_acceptance-20260601_105840`。
- `result.json`：`completed=true`、`assertion.passed=true`、`permission_sent_count=0`。
- 独立 verifier：同一 run 复验通过。
- 调试日志：`browser_plugin_status` 输出 `session_mode=visible_chromium`、`connected=true`、`visible=true`、`tab_count=1`、`active_tab_id=browser_session_1_fa131c86-tab-1`。
