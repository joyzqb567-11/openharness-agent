# Active Plan: Phase 53-64 Windows Computer Use Parity Plus

> 当前主控计划文件：`docs/superpowers/plans/2026-06-03-phase53-64-windows-computer-use-parity-plus.md`。
> 用户已确认从 Phase 53 执行到 Phase 64。当前按阶段执行中；每个运行时代码阶段必须完成自动化测试、学习备份和 `start_oauth_agent.bat` 真实可见终端验收。

## Active Success Criteria

- [x] 基于 ClaudeCode computer-use 源码核对结果和 learning_agent Phase43-52 现状，拆解剩余约 20% 差距。
- [x] 生成 Phase 53-64 正式升级蓝图。
- [x] 生成 agent_memory 阶段蓝图记录。
- [x] 生成 learning_agent/test 学习备份。
- [x] 用户已确认进入 Phase 53-64 执行。

## Phase 53-64 Scope

- [x] Phase 53：Parity gap lock and non-fake acceptance contract。
- [x] Phase 54：Windows native dependency and permission reality gate。
- [x] Phase 55：Out-of-process Windows native helper v2。
- [x] Phase 56：Real Windows screenshot pipeline with pixel guard。
- [x] Phase 57：Real UIA control tree and semantic locator。
- [x] Phase 58：Real SendInput action path with target guard。
- [x] Phase 59：ClaudeCode-style session context and AppState。
- [x] Phase 60：Approval UX and persistent grants。
- [ ] Phase 61：Global abort, hotkey, cleanup, and streaming hooks。
- [ ] Phase 62：High-level Computer Tool API and streaming integration。
- [ ] Phase 63：External agent controller takeover and debug surface。
- [ ] Phase 64：Final parity plus production matrix。

## Stop Conditions

- 未经用户明确确认，不安装系统依赖、不写注册表、不修改 Windows 安全设置。
- 目标窗口属于终端、Codex UI、安全设置、密码管理器、认证弹窗、验证码、Windows Run、管理员安全窗口时停止。
- fake provider 验收只能声明 contract passed，不能声明 real native passed。
- 运行时代码阶段未通过自动化测试和 `start_oauth_agent.bat` 真实可见终端验收时，不能声明开发完成。

---

# Active Plan: Phase 43-52 Windows Computer Use Production Alignment

> 当前主控计划文件：`docs/superpowers/plans/2026-06-03-phase43-52-windows-computer-use-production-alignment.md`。
> 用户已确认从 Phase 43 执行到 Phase 52。执行中必须维护 `agent_memory/context.md`、`agent_memory/progress.md`、`agent_memory/bugs.md`，并在代码修改后保存学习备份到 `learning_agent/test/`。

## Active Success Criteria

- [x] Phase 43：Windows 原生能力诊断升级。
- [x] Phase 44：Windows Native Host / Helper 架构。
- [x] Phase 45：真实 Windows 截图能力。
- [x] Phase 46：真实 UIA 窗口树观察。
- [x] Phase 47：真实 SendInput 动作执行。
- [x] Phase 48：权限审批和安全策略升级。
- [x] Phase 49：MCP / ClaudeCode 风格工具面兼容层。
- [x] Phase 50：全局 Abort / Cleanup / Lock 恢复。
- [x] Phase 51：类似 `/chrome` 的终端状态 UI。
- [x] Phase 52：自动化与真实可见终端端到端验收。

## Phase52 Current Status

- [x] Phase52 production matrix code and scenario added.
- [x] Phase52 TDD red confirmed before implementation.
- [x] Phase52 focused tests, Phase43-52 regression, `py_compile`, and CLI self-check passed.
- [x] Phase43/Phase51 `/computer status` compatibility regression fixed and verified.
- [x] Visible `learning_agent/start_oauth_agent.bat` launch attempted.
- [x] Real visible `learning_agent/start_oauth_agent.bat` terminal interaction acceptance passed through `learning_agent/acceptance_controller/controller.ps1`.
- [x] Phase52 visible terminal evidence: `learning_agent/acceptance_controller/runs/agent_capability_phase52_windows_production_matrix-20260603_143905/result.json`.

## Stop Conditions

- 未完成 `learning_agent/start_oauth_agent.bat` 真实可见终端交互验收时，不能声明开发完成。
- 未经用户另行确认，不安装系统依赖、不写注册表、不修改 Windows 安全策略。
- 目标窗口属于终端、Codex UI、安全/隐私设置、密码/认证、验证码/OTP、Windows Run 或管理员安全窗口时停止。
- 真实动作必须先通过 opt-in、allowlist、lock、abort、目标窗口校验、审批和 evidence。

---

# Active Plan: Phase 35-42 Windows Computer Use ClaudeCode Alignment

> 当前主控计划文件：`docs/superpowers/plans/2026-06-03-phase35-42-windows-computer-use-claudecode-alignment.md`。  
> 本轮先把 Phase 35-42 制作到升级蓝图中，再按阶段逐项执行；每个运行时代码阶段必须先 TDD 红灯，再实现，再做自动化测试和真实可见终端验收。

## Active Success Criteria

- [x] 读取 `learning_agent/zqbcontext.md`、根计划文件、agent_memory 上下文、ClaudeCode computer-use 源码比较结论和 learning_agent 当前 computer_use 源码状态。
- [x] 生成 Phase 35-42 正式升级蓝图。
- [x] 生成 agent_memory 阶段蓝图记录。
- [x] 生成 learning_agent/test 学习备份。
- [x] Phase 35：真实安全窗口 UIA smoke harness。
- [x] Phase 36：Windows.Graphics.Capture provider 合同。
- [x] Phase 37：SendInput 动作执行器。
- [x] Phase 38：Windows ComputerUseApproval 模型。
- [x] Phase 39：DPI、多显示器和坐标模型。
- [x] Phase 40：全局 abort、cleanup 和通知。
- [x] Phase 41：截图结果 artifact / image result。
- [x] Phase 42：最终 Windows Computer Use E2E 矩阵。

## Stop Conditions

- 未经用户确认，不安装系统依赖、不写注册表、不调整 Windows 安全设置。
- 未完成真实可见终端验收时，不能声明对应运行时代码阶段开发完成。
- 目标窗口是终端、Codex UI、安全/隐私设置、密码管理器、认证弹窗、验证码/OTP 或 Windows Run 时停止。
- 不能把 fake provider 验收结果说成真实 Windows UIA/WGC/SendInput 已成熟。

---

# Historical Plan: Phase 30 Windows OS Computer Use Safe Action Gate

> 当前阶段已完成：durable lock、abort flag、窗口相对坐标转换、敏感文本脱敏、action evidence envelope、自动化测试和真实可见终端验收。  
> 本阶段仍使用安全内存后端验收，不扩大真实鼠标键盘范围，不声称已完成 Windows native SendInput/UIA/GPU capture。

## Active Success Criteria

- [x] 按 TDD 新增 Phase 30 红灯测试，确认 `learning_agent.computer_use.lock` 缺失。
- [x] 新增 `learning_agent/computer_use/lock.py`，提供 durable desktop lock、owner session、release、abort request 和 abort clear。
- [x] 新增 `learning_agent/computer_use/action_policy.py`，提供窗口相对坐标转换、文本短哈希脱敏、目标窗口摘要和 action evidence envelope。
- [x] 修改 `ComputerUseController`：显式锁管理器时动作必须持当前锁，abort flag 阻止下一次动作，结果携带 `action_evidence`。
- [x] 修改 `MemoryComputerUseBackend` 和 `LearningAgent._computer_action()`，避免把 `type_text` 原始文本写入可见日志/审计。
- [x] 修改 `computer_action` schema，说明提供 `window` 时 x/y 是窗口相对坐标。
- [x] 新增真实可见终端验收场景 `agent_capability_phase30_windows_action_gate.json`。
- [x] 自动化验证通过：Phase 30 聚焦 5 tests OK，Phase 17/20/27/28/29 回归 24 tests OK，完整 `learning_agent\tests` 630 tests OK，skipped=1。
- [x] 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/agent_capability_phase30_windows_action_gate-20260603_065937/result.json`。

## Stop Conditions

- Phase 30 不直接扩大真实鼠标、键盘、窗口动作，只为后续真实动作建立门禁和证据。
- 本阶段验收必须使用内存后端和临时锁目录，不允许误触真实桌面。
- 文本动作审计、内存后端日志、权限提示和 action evidence 都不能保存原始 `text`。
- 若真实可见终端验收无法完成，不能声明开发完成。

---

# Active Plan: Phase 29 Windows OS Computer Use Observe Evidence

> 当前阶段已完成：`get_window_state` 证据落盘合同、截图 artifact 路径、metadata artifact、bounded UIA 摘要、敏感 UIA 行过滤、helper/status 边界、自动化测试和真实可见终端验收。  
> 下一步建议进入 Phase 30 前先补 lock/abort/action evidence，再做极窄的窗口相对动作，不要直接扩大真实鼠标键盘自动化。

## Active Success Criteria

- [x] 按 TDD 新增 Phase 29 红灯测试，确认 `evidence.py`/`helper_client.py` 缺失。
- [x] 新增 `learning_agent/computer_use/evidence.py`，把窗口状态 metadata 和截图 bytes 保存到 evidence 目录。
- [x] 新增 `learning_agent/computer_use/helper_client.py`，提供静态 helper、空 helper 和统一 payload 合同。
- [x] 修改 `WindowsComputerUseBackend.get_window_state`，返回 `screenshot_id`、`screenshot_path`、`evidence_path`、bounded `accessibility_excerpt` 和过滤统计。
- [x] 状态输出新增 `evidence_root`、`evidence_mode`、`observation_helper`、`observation_helper_available`。
- [x] 新增真实可见终端验收场景 `agent_capability_phase29_windows_observe_evidence.json`。
- [x] 自动化验证通过：Phase 29 聚焦 3 tests OK，相关回归 15 tests OK，完整 `learning_agent\tests` 625 tests OK，skipped=1。
- [x] 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/agent_capability_phase29_windows_observe_evidence-20260603_062659/result.json`。

## Stop Conditions

- Phase 29 不扩大真实鼠标、键盘、窗口动作。
- Phase 29 的真实终端验收使用静态安全 helper 验证 artifact 和过滤合同，不声称已完成 Windows.Graphics.Capture 或 UIAutomationClient native helper。
- UIA 文本必须过滤敏感行并限制长度；metadata 也不能保存原始 password/token 行。
- 后续进入动作前必须先补 durable lock、abort flag、目标确认和动作前后 evidence。

---

# Active Plan: Phase 28 Windows OS Computer Use Read-Only Inventory

> 当前阶段已完成：Windows 只读 app/window inventory、静态测试后端、可选 Win32 只读探针、`list_windows/list_apps/get_active_window/get_window_state` 观察入口、只读动作拒绝、自动化测试和真实可见终端验收。  
> 下一步建议进入 Phase 29：补齐截图证据文件与 UI Automation 文本摘要，让 `get_window_state` 不只返回尺寸和占位说明，而能生成可审计 evidence artifact。

## Active Success Criteria

- [x] 按 TDD 新增 Phase 28 红灯测试，覆盖静态窗口枚举、应用聚合、窗口状态、只读动作拒绝和默认 opt-in 状态。
- [x] 新增 `learning_agent/computer_use/windows_backend.py`，提供静态 inventory、Win32 ctypes 只读探针、安全标题过滤、窗口矩形归一化和进程路径哈希。
- [x] 扩展 `learning_agent/computer_use/controller.py`，让 Windows backend 支持 `list_windows`、`list_apps`、`get_active_window`、`get_window_state`。
- [x] 默认仍不启用真实桌面观察；只有 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE` 明确开启且运行在 Windows 时，才进入只读 Windows backend。
- [x] 在只读模式下明确拒绝鼠标、键盘、窗口动作，避免 Phase 28 越界执行真实 OS 操作。
- [x] 新增真实可见终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase28_windows_inventory.json`。
- [x] 自动化验证通过：Phase 28 聚焦 5 tests OK，Phase 27/17/20 回归 16 tests OK，完整 `learning_agent\tests` 622 tests OK，skipped=1。
- [x] 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/agent_capability_phase28_windows_inventory-20260602_234801/result.json`。

## Stop Conditions

- Phase 28 只做只读 inventory，不保存真实屏幕截图，不读取 UI Automation 文本树，不扩展 SendInput 鼠标键盘动作。
- 真实窗口标题需要经过安全过滤；终端、Codex UI、安全设置、密码/认证相关窗口仍不能作为自动化目标。
- 未进入 Phase 29 前，`get_window_state` 的 screenshot/UIA 字段只能表达占位状态，不能声称已具备真实视觉证据链。
- 未完成 opt-in、权限、锁、证据链和目标窗口确认前，不允许把真实鼠标键盘动作扩展为生产可用。

---

# Active Plan: Phase 27 Windows OS Computer Use Protocol

> 当前阶段已完成：typed Computer Use observe/action 协议层、只读 `computer_observe` 工具、窗口身份校验和真实可见终端验收。
> 下一步建议进入 Phase 28：Windows 只读窗口枚举、窗口截图和 UI Automation 摘要，不直接扩大真实鼠标键盘动作。

## Active Success Criteria

- [x] 按 TDD 先写 Phase 27 红灯测试，覆盖 `computer_observe` schema/catalog、只读观察无需桌面控制确认、未知窗口动作拒绝。
- [x] 新增 `learning_agent/computer_use/models.py`，定义强类型窗口引用和身份键。
- [x] 扩展 `ComputerUseController.observe()`，把只读观察和高风险动作分开审计。
- [x] 扩展 `MemoryComputerUseBackend.observe()`，支持 `list_apps`、`list_windows`、`get_active_window`、`get_window_state`。
- [x] 扩展 `computer_action` 可选 `window` 目标，并在动作前拒绝未知窗口。
- [x] 新增 `computer_observe` schema、catalog 低风险只读元数据、executor 路由和 `LearningAgent._computer_observe()`。
- [x] 修复 acceptance controller 对缺省 `event_payload_contains` 的 null 断言项崩溃。
- [x] 自动化测试通过：Phase 27 聚焦 4 tests OK，Phase 17/20 回归 7 tests OK，完整 `learning_agent\tests` 617 tests OK，skipped=1。
- [x] 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/agent_capability_phase27_windows_computer_use_protocol-20260602_233224/result.json`。

## Stop Conditions

- Phase 27 不实现真实 Windows 窗口枚举、真实截图保存、UI Automation 文本树或真实 SendInput 动作扩展。
- 后续 Phase 28 只能先做只读窗口发现和窗口状态观察。
- 未完成 app/window 目标、权限、锁和证据链前，不允许把真实鼠标键盘动作扩展到生产可用。
- 终端、Codex UI、安全/隐私设置、密码管理器、认证弹窗和 Windows Run 仍是 Computer Use 禁止自动化目标。

---

# Historical Plan: Phase 26 Windows OS Computer Use Blueprint

> 当前主控计划文件：`docs/superpowers/plans/2026-06-02-phase26-windows-os-computer-use-blueprint.md`。
> 本轮只生成 Windows OS Computer Use 蓝图，不实现真实桌面控制代码。

## Active Success Criteria

- [x] 读取现有 Phase 20 Computer Use 安全壳、Phase 14-23 蓝图、Codex Computer Use 插件说明和项目记忆。
- [x] 确认 Phase 25 编号已被真实 Chrome extension/native-host 连接后续占用。
- [x] 将 Windows OS Computer Use 蓝图编号为 Phase 26，避免污染既有历史。
- [x] 生成正式蓝图：`docs/superpowers/plans/2026-06-02-phase26-windows-os-computer-use-blueprint.md`。
- [x] 生成 agent_memory 记录：`agent_memory/agent_capability_phase26_windows_computer_use_blueprint_20260602.md`。
- [x] 生成学习备份：`learning_agent/test/agent_capability_phase26_windows_computer_use_blueprint_20260602/phase26_blueprint.md`。
- [x] 用户已确认，Phase 27 已按 TDD 完成协议层，不直接跳到真实鼠标键盘动作。

## Stop Conditions

- 未经用户确认，不实现 Windows native helper。
- 未经显式 opt-in、权限、锁和安全目标校验，不执行真实鼠标键盘动作。
- 目标是终端、Codex UI、安全/隐私设置、密码管理器或认证弹窗时停止。
- 未来任何运行时功能未完成 `start_oauth_agent.bat` 真实可见终端验收时，不能声明开发完成。

---

# Historical Plan: Agent Capability Completion Roadmap

> 当前主控计划以 `docs/superpowers/plans/2026-06-01-agent-capability-completion-roadmap.md` 为准。
> 本轮用户要求先生成书面计划，防止复杂任务跑偏；当前未开始改运行时代码。

## Active Success Criteria

- [x] 读取 `learning_agent/zqbcontext.md` 并理解当前上下文。
- [x] 读取现有 `task_plan.md`、`findings.md`、`progress.md` 和 `agent_memory/progress.md`。
- [x] 确认旧 baseline：浏览器双轨 Stage 5-10 已有历史完成记录，新的差距集中在生产安装、配对同步、高层工具、全局执行器、OS 级 Computer Use、终端 UI 和端到端验收。
- [x] 生成主控计划：`docs/superpowers/plans/2026-06-01-agent-capability-completion-roadmap.md`。
- [x] 生成 agent_memory 记录：`agent_memory/agent_capability_completion_roadmap_20260601.md`。
- [x] 生成学习备份：`learning_agent/test/agent_capability_completion_20260601/plan.md`。
- [x] 已按用户确认从 Phase 1 执行到 Phase 7，并为每个阶段保存子计划、测试、学习备份和真实验收证据。

## Active Stages

- [x] Phase 0: 主控计划和安全边界。
- [x] Phase 1: 生产级 Chrome extension 安装/native host 注册。
- [x] Phase 2: Chrome extension 配对和 session sync。
- [x] Phase 3: 高层浏览器工具。
- [x] Phase 4: 全局 StreamingToolExecutor。
- [x] Phase 5: OS 级 Computer Use。
- [x] Phase 6: 类似 `/chrome` 的终端状态 UI。
- [x] Phase 7: 真实端到端验收矩阵。

## Stop Conditions

- 涉及真实 Windows registry 写入前，必须有明确回滚方案和用户确认。
- 涉及真实账号、密码、cookie、token 时，必须停止并走脱敏/secret 工具路径。
- 未完成 `start_oauth_agent.bat` 真实可见终端验收时，不能声明对应开发阶段完成。

---

# Historical Plan: Browser Runtime ClaudeCode Alignment

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

# 当前任务：Phase 32 Windows OS Computer Use Native Observation Helper（2026-06-03）

## 本阶段目标

把 Windows OS Computer Use 的窗口状态证据从静态 helper 推进到只读 native helper 桥接：支持截图 provider、文本 provider、provider 注入、磁盘 evidence 复用和独立 native opt-in。

## Phase 32 验收标准

- [x] 有 `WindowsNativeWindowObservationHelper`，能合并截图 provider 和文本 provider。
- [x] 有 `parse_hwnd_from_window()`，能解析 Phase28 的 `window_id="hwnd:<id>"`。
- [x] 有 Win32 GDI 截图 fallback provider，但测试和验收不读取真实桌面。
- [x] 有 Win32 标题/子控件文本 fallback provider，但不声明完整 UIAutomationClient。
- [x] native helper 输出进入现有 `ComputerUseEvidenceStore`，截图 artifact 落盘，敏感文本过滤。
- [x] 默认后端必须显式设置 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE=1` 才启用 native helper。
- [x] Phase32 聚焦测试通过。
- [x] Computer Use 相邻回归通过。
- [x] 新增/修改文件备份到 `learning_agent/test/agent_capability_phase32_windows_native_helper_20260603/`。
- [x] `py_compile`、场景 JSON、全量回归通过。
- [x] `learning_agent/start_oauth_agent.bat` 真实可见终端验收通过。
- [x] 独立 verifier 复验通过。

## 当前停止条件

Phase32 已完成；后续若继续扩大 native helper，必须先重新建立 Phase33 级别成功标准和真实可见终端验收。

---

# 当前任务：Phase 31 Windows OS Computer Use Lock, Abort, Evidence Chain（2026-06-03）

## 本阶段目标

把 Phase30 的安全动作门禁补成可恢复、可中断、可审计的桌面控制层：stale lock 恢复、abort 终端入口、before/after evidence chain、磁盘审计脱敏和真实终端验收。

## Phase 31 验收标准

- [x] stale desktop lock 可被新 session 恢复，并保留旧 owner 证据。
- [x] abort flag 在后端动作前阻断下一次桌面动作。
- [x] 成功动作包含 `before_evidence` 和 `after_evidence`，并且二者绑定同一个 `audit_id`。
- [x] 审计事件和 evidence chain 可落盘，且不保存原始敏感 `type_text` 文本。
- [x] 真实终端支持 `/computer status`、`/computer abort <reason>`、`/computer clear-abort`。
- [x] Phase31 聚焦测试通过。
- [x] Computer Use 相邻回归通过。
- [x] 新增/修改文件备份到 `learning_agent/test/agent_capability_phase31_windows_lock_abort_evidence_20260603/`。
- [x] `py_compile`、场景 JSON、全量回归通过。
- [x] `learning_agent/start_oauth_agent.bat` 真实可见终端验收通过。
- [x] 独立 verifier 复验通过。

## 当前停止条件

Phase31 已完成；后续若继续扩大真实 Windows native helper，必须先重新建立 Phase32 级别成功标准和真实可见终端验收。

---

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
