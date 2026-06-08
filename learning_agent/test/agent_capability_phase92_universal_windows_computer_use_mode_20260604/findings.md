# 2026-06-03 ClaudeCode Computer Use vs learning_agent Windows Computer Use Gap Review

- ClaudeCode source reviewed from `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\`: `executor.ts`, `wrapper.tsx`, `computerUseLock.ts`, `cleanup.ts`, `escHotkey.ts`, `mcpServer.ts`, `hostAdapter.ts`, `gates.ts`, and `toolRendering.tsx`.
- ClaudeCode `executor.ts` explicitly refuses non-macOS platforms with `process.platform !== 'darwin'`, so its local Computer Use executor is a mature macOS implementation, not a directly reusable Windows backend.
- ClaudeCode mature areas confirmed in source: `@ant/computer-use-mcp` session binding, app allowlist callbacks, React `ComputerUseApproval`, AppState persistence, file lock with stale recovery, global Escape abort, turn-end cleanup/unhide, OS notification, screenshot/image/text result mapping, app enumeration, display targeting, clipboard, mouse, keyboard, and app opening.
- learning_agent current Windows Computer Use reviewed from Phase43-52 modules: `production_matrix.py`, `native_host.py`, `screenshot_runtime.py`, `uia_tree.py`, `sendinput_dispatcher.py`, `security_policy.py`, `tool_surface.py`, `session_runtime.py`, `controller.py`, and `app/computer_status_renderer.py`.
- learning_agent Phase52 evidence confirms `native_capability=true`, `native_host=true`, `screenshot_runtime=true`, `uia_tree=true`, `sendinput_dispatcher=true`, `security_policy=true`, `tool_surface=true`, `recovery_runtime=true`, `status_ui=true`, `dispatcher_actions_expanded=true`, and `actions_expanded=false`.
- Fair estimate: learning_agent is about 80%-85% aligned with ClaudeCode at architecture/contract/harness level, leaving about 15%-20% gap.
- Stricter production-polish estimate: learning_agent is about 70%-75% aligned with ClaudeCode when counting hidden/native package maturity, graphical approval UX, real native dependency availability, and fully polished lifecycle integration, leaving about 25%-30% gap.
- Recommended single-number summary for user communication: learning_agent Windows Computer Use is currently around 80% of ClaudeCode computer-use maturity, with about 20% remaining gap.
- Main remaining gaps: real Windows dependency validation beyond injected/fake providers, fully wired native WGC/UIA/SendInput production path, richer approval UI/AppState persistence, deeper streaming/abort cleanup hooks, pixel/crop/coordinate verification, and polished product rendering comparable to ClaudeCode.

# Phase 35-42 Windows Computer Use ClaudeCode Alignment Findings

- Phase38 已完成 Windows ComputerUseApproval 模型：新增 `WindowsComputerUseApprovalModel`，覆盖 session app allowlist、grant flags、禁止目标分类、终端状态摘要和稳定 CLI 合同。
- Phase38 controller 接入点位于 `ComputerUseController._reject_unapproved_action()`：动作通过 confirm/text 长度检查后、进入未知窗口校验和后端执行前，会先执行 approval 拦截。
- Phase38 禁止目标边界：PowerShell、cmd、Windows Terminal、Codex UI、安全设置、密码管理器、认证/验证码/OTP 等窗口会返回 `denied_forbidden_target`，不会进入后端执行。
- Phase38 grant flag 边界：`ctrl+alt+delete` 等系统级组合键需要 `systemKeyCombos=true`，否则返回 `missing_grant_flags`。
- Phase38 终端 UI：`/computer status` 现在追加 `Computer Use Approval` 摘要，显示 `approval_model=phase38_windows_computer_approval`、授权 app 数、grant flags 和 `actions_expanded=false`。
- Phase38 验证证据：聚焦 6 tests OK、py_compile OK、scenario JSON OK、CLI 自检 OK、Phase30-38 邻近回归 45 OK、全量 670 OK skipped=1、真实可见终端 run `learning_agent/acceptance_controller/runs/agent_capability_phase38_windows_computer_approval-20260603_105641` 和独立 verifier 均通过。
- Phase38 边界：本阶段不是图形化审批弹窗，也不证明真实 `ctypes.SendInput`、真实 UIA 或真实 WGC 已成熟；动作面仍明确 `actions_expanded=false`。

- Phase37 已完成 SendInput executor 合同实现：新增 `WindowsSendInputExecutor`，把真实写动作统一收口到可注入执行器，而不是继续在 Windows 后端里直接调用旧 `SetCursorPos + mouse_event`。
- Phase37 接入点在 `WindowsComputerUseBackend`：动作仍先经过 Phase30/31 的确认、可信窗口、持锁、abort、窗口相对坐标和 evidence 门禁，随后才进入 action executor。
- Phase37 默认安全边界：没有显式启用、不是 Windows、或没有注入底层实现时，执行器会拒绝并返回“未触碰鼠标键盘”的结构化结果。
- Phase37 已支持动作合同集合 `click/double_click/move_mouse/press_key/scroll/type_text`，但 `actions_expanded=false` 表示当前阶段不扩大上层工具暴露范围。
- Phase37 脱敏结论：`type_text` 生成事件和执行结果只保留长度、短哈希和 `text_redacted=true`，不把原始文本交给可见日志或 fake dispatch 结果。
- Phase37 当前证据：聚焦测试 5 OK、`py_compile` OK、场景 JSON OK、CLI 自检 OK、Phase30-37 邻近回归 39 OK、全量回归 664 OK skipped=1、真实可见终端 run `learning_agent/acceptance_controller/runs/agent_capability_phase37_windows_sendinput_executor-20260603_104221` 和独立 verifier 均通过。
- Phase37 边界：这不是底层 `ctypes.SendInput` 已成熟，也不是允许 broad desktop automation；Phase38 应继续补 approval 模型，而不是直接放宽真实动作范围。
- Phase36 已完成：新增 `WindowsGraphicsCaptureProvider` 合同、WGC 依赖诊断、capture result coercion，并把 diagnostics 的 WGC 项接到 Phase36 provider.status。
- Phase36 验收结论：当前机器没有 WGC Python 绑定，正确输出 `fallback_required=true`；自动化测试、全量回归和真实可见终端 run `learning_agent/acceptance_controller/runs/agent_capability_phase36_windows_wgc_provider-20260603_102321` 均通过。
- Phase36 边界：未安装 WGC 依赖、未接入真实 WGC helper、未扩大鼠标键盘动作；Phase37 只能在既有 lock/abort/target/evidence 门禁内补 SendInput executor。
- Phase35 已完成：新增真实安全窗口 UIA smoke harness，默认先报告 `uiautomation` 依赖状态；当前环境依赖缺失时不会启动窗口，也不会用 fake provider 冒充真实 UIA。
- Phase35 验收结论：自动化测试、全量回归和真实可见终端 run `learning_agent/acceptance_controller/runs/agent_capability_phase35_windows_real_uia_smoke-20260603_101422` 均通过。
- Phase35 边界：`real_uia_verified=false` 是当前依赖缺失环境下的诚实结果，不代表 UIA 真实读取已在本机完成；Phase36 不应把 Phase35 误读成完整 native helper 成熟。
- 已完成源码级复核：ClaudeCode `computer-use` 是成熟 macOS 集成路线，包含 MCP 包装、app allowlist、权限弹窗、display state、file lock、Escape abort、cleanup、OS notification 和 image/text result mapping。
- 关键边界：ClaudeCode 本地 `executor.ts` 明确 `process.platform !== 'darwin'` 时拒绝，因此它不是可直接复制到 Windows 的执行器。
- learning_agent 当前已完成 Phase 27-34：协议、Windows 只读 inventory、evidence store、动作门禁、lock/abort、native helper、diagnostics、UIA-first text provider。
- 当前最大缺口：schema 暴露 `double_click/type_text/press_key/scroll`，但 Windows backend 真实执行层只实现 `move_mouse`、`click` 和 `screenshot` 尺寸占位。
- 本机依赖探测结果：`uiautomation=False`、`comtypes=False`、`winrt/winsdk Windows.Graphics.Capture` 不可用、`platform=win32`。
- 结论：Phase 35 应先做真实安全窗口 UIA smoke harness 和依赖缺失诚实诊断，不能继续用 fake provider 冒充真实 UIA 验收。
- 新蓝图文件：`docs/superpowers/plans/2026-06-03-phase35-42-windows-computer-use-claudecode-alignment.md`。

---

# Phase 32 Windows OS Computer Use Native Observation Helper Findings

- TDD 红灯确认当前缺口：`COMPUTER_USE_NATIVE_OBSERVE_OPT_IN_ENV_VAR` 和 `learning_agent.computer_use.native_helper` 原本不存在，默认 Windows 后端没有 native helper 生产入口。
- Phase32 新增 `WindowsNativeWindowObservationHelper`，把截图 provider 和文本 provider 合并为 Phase29 已有的 `WindowObservationPayload`，因此无需新增旁路 evidence 格式。
- helper 支持 provider 注入，自动化测试和真实终端验收可以使用 fake provider 证明合同，不读取真实桌面。
- 默认生产后端新增独立 opt-in：`LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE=1`；只开 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE=1` 不会自动读取截图或文本。
- `Win32GdiWindowCaptureProvider` 可以在真实 Windows 上尝试 GDI `PrintWindow` / `BitBlt` 只读截图，并把结果保存为 BMP artifact。
- `Win32WindowTextProvider` 可以读取 Win32 标题和子控件文本，作为 Phase32 文本 fallback；它不是完整 UIAutomationClient 文本树。
- 仍需 Phase33+ 继续补 Windows.Graphics.Capture、UIAutomationClient、DPI/多显示器、窗口遮挡/最小化和 helper 权限诊断。
- Phase32 仍不扩大真实鼠标键盘动作；真实动作继续依赖 Phase30/31 的 lock、abort、窗口目标和 evidence chain。

---

# Phase 31 Windows OS Computer Use Lock, Abort, Evidence Chain Findings

- TDD 红灯确认当前缺口：`run_computer_terminal_command` 不存在，真实终端没有 `/computer` abort/status 入口。
- Phase31 已把 Phase30 的 in-memory action evidence 扩展为可落盘 evidence chain：事件写入 JSONL，动作链路写入单独 JSON 文件。
- 成功动作现在同时返回 `before_evidence` 和 `after_evidence`，二者都补同一个 `audit_id`，便于单独复盘动作前后现场。
- `ComputerUseAuditStore` 在写盘前递归脱敏，能防止 `type_text` 原文进入 events/chains，同时保留 `text_sha256_16` 短哈希用于关联。
- `ComputerUseLockManager` 现在支持 stale lock TTL 和恢复旧 owner 证据，避免崩溃进程永久占用 desktop control lock。
- 本轮实测发现 UTC 解析 bug：用 `time.mktime(...)` 解析 `2026-...Z` 会受 Windows 本地时区影响，东八区把新锁误判为 8 小时旧；已改为 `calendar.timegm(...)`。
- 真实终端新增 `/computer status`、`/computer abort <reason>`、`/computer clear-abort`、`/computer release [session_id]`，并写 `computer_status_printed` acceptance event。
- Phase31 仍然不声明真实 Windows SendInput、真实截图 helper 或 UIAutomationClient 已完成；当前验证使用内存后端和临时目录，下一阶段应继续收窄真实 native helper 的安全边界。

---

# Phase 30 Windows OS Computer Use Safe Action Gate Findings

- TDD 红灯确认 Phase 30 的第一缺口是真实存在的：`learning_agent.computer_use.lock` 原本不存在。
- Phase 30 已把锁和动作策略拆成独立模块，避免继续把 OS 控制安全逻辑堆进 `controller.py`。
- `ComputerUseLockManager` 使用 durable JSON 文件记录当前 owner session 和 abort flag；显式注入锁管理器时，动作必须先由当前 session 持锁。
- 默认生产 controller 会带锁管理器，并可在无人持锁时自动获取当前 session 锁；测试注入后端默认保持旧兼容，避免历史 Phase 20 内存测试被锁门禁误伤。
- `action_policy.py` 现在把窗口相对坐标转换为屏幕坐标，并在 evidence 中记录 `source=window_relative`、原始相对坐标和窗口原点。
- `type_text` 的原始文本现在不会进入 controller audit、内存后端 action log、action evidence 或 `_computer_action` 权限提示/拒绝观察；只保留长度、短哈希和 `text_redacted=true`。
- Phase 30 仍不声明真实 Windows SendInput、Windows.Graphics.Capture 或 UIAutomationClient native helper 已完成；本阶段只补动作门禁和证据 envelope。
- 真实可见终端验收场景使用内存后端和临时锁目录验证，不会移动鼠标或点击真实桌面。

---

# Phase 29 Windows OS Computer Use Observe Evidence Findings

- TDD 红灯确认 Phase 29 的缺口不是测试写错：`learning_agent.computer_use.evidence` 原本不存在。
- `get_window_state` 现在不再只返回 Phase 28 几何占位；它会通过 helper payload 生成截图 artifact、metadata artifact 和 bounded UIA 摘要。
- 新的 evidence store 会把截图字节保存为独立文件，把窗口身份、helper 状态、截图尺寸和过滤后的 UIA 摘要保存为 JSON metadata。
- UIA 文本按行过滤 `password`、`token`、`credential`、`验证码`、`密码` 等敏感关键词，响应和 metadata 都不保存这些敏感行。
- 工具响应中的 `accessibility_excerpt` 被限制在 600 字符以内，并返回 `accessibility_truncated` 和 `accessibility_filtered_line_count`。
- `StaticWindowObservationHelper` 让测试和可见终端验收可以证明证据链，不读取真实桌面敏感窗口。
- `NullWindowObservationHelper` 让默认后端在没有 native helper 时仍能保存 metadata，并诚实说明没有读取真实截图/UIA。
- 真实可见终端验收已证明目标 agent 能在真实交互提示符中触发 Phase 29 evidence 保存，并输出固定验收 marker。

---

# Phase 28 Windows OS Computer Use Read-Only Inventory Findings

- TDD 红灯确认了真实缺口：项目没有 `windows_backend.py`，默认 Computer Use 状态也没有只读观察 opt-in 字段。
- Phase 28 已把 Windows Computer Use 从“只有协议占位”推进到“可枚举 app/window 的只读 inventory”，但仍没有扩大鼠标键盘能力。
- 新的 `WindowsWindowInventoryProbe` 使用 Win32 ctypes 做只读枚举；如果不是 Windows 或 Win32 API 不可用，会返回结构化不可用原因，而不是假装成功。
- 新的 `StaticWindowsWindowInventory` 让测试和验收可以使用安全样例窗口，避免真实桌面标题泄露到日志或验收记录。
- 标题过滤现在会排除空标题、终端、PowerShell、Codex、安全/密码/认证相关窗口，降低误控高风险窗口的概率。
- `get_window_state` 现在能返回窗口矩形换算出的截图尺寸和原点，但 screenshot_id、UIA 文本和 evidence_path 仍是 Phase 29 占位。
- `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE` 与真实动作开关分离；只读观察可以独立开启，真实动作仍需要更高门槛。
- 真实可见终端验收已证明目标 agent 能在真实交互提示符中完成 Phase 28 inventory 检查，并且拒绝只读模式下的动作请求。

---

# Phase 27 Windows OS Computer Use Protocol Findings

- TDD 红灯确认当前缺口：`computer_observe` 不存在，`MemoryComputerUseBackend` 不能注入窗口目录，`ComputerUseController` 没有 observe 入口，也不会拒绝带未知 `window` 的动作。
- 已确认并实现协议分层：`computer_observe` 是低风险只读工具，`computer_action` 仍是高风险动作工具。
- 已确认并实现窗口身份最小合同：窗口目标必须包含 `app_id` 与 `window_id`，动作如果声明 `window`，控制器会先用只读 `get_window_state` 验证目标可信。
- 已保持 Phase 20 兼容：旧的 confirmed 内存动作不带 `window` 时仍可执行，避免一次协议升级破坏既有测试。
- 已确认真实 Windows 后端仍只是占位：Phase 27 只定义 typed observe/action 合同，不声明真实窗口枚举、真实截图、UIA 或 SendInput 成熟可用。
- 已确认验收控制器边界 bug：缺省 `event_payload_contains` 会产生 null 检查项并触发 PowerShell 字典 null key 异常；已在 controller 源头过滤空断言项。
- 真实可见终端验收通过后，Phase 28 可以继续做只读窗口枚举、窗口截图和 UI Automation 摘要。

---

# Phase 26 Windows OS Computer Use Findings

- Codex Computer Use 插件说明确认 Windows 路线应以 app/window 为目标，而不是默认全屏坐标。
- Codex Computer Use 插件说明确认 Windows 后端核心概念包括 SendInput、UI Automation 和 Windows.Graphics.Capture。
- Codex Computer Use 插件说明要求优先 `list_apps`，选择 app/window，再 `get_window_state`，随后批量执行动作并重新观察。
- Codex Computer Use 插件说明强调禁止自动化终端、安全/隐私设置、认证弹窗、密码管理器、Codex UI 和 Windows Run 等高风险入口。
- ClaudeCode 源码参考价值主要在架构层：MCP 工具包装、权限审批、app allowlist、session state、锁、abort、截图/文本结果映射。
- learning_agent 当前已有 `computer_status` / `computer_action`、默认安全关闭、`LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE`、audit_id 和 evidence，但还没有 Codex 级别的窗口截图、UI Automation 文本树和窗口相对动作后端。
- 决策：Phase 26 只写蓝图。后续实现从 Phase 27 协议层开始，不能直接写真实鼠标键盘动作。

---

# Learning Agent Long-Task Harness Findings

## Browser Runtime ClaudeCode Alignment Findings 2026-06-01

- ClaudeCode 源码可确认：真实浏览器能力通过 `claude-in-chrome` MCP/Chrome 扩展桥接进入主工具系统，而不是在普通工具目录里写一个单独 Playwright 脚本。
- ClaudeCode 源码可确认：`utils/claudeInChrome/mcpServer.ts` 支持 bridge/native socket、OAuth token、设备配对、`CLAUDE_CHROME_PERMISSION_MODE=skip_all_permission_checks`。
- ClaudeCode 源码可确认：`skills/bundled/claudeInChrome.ts` 把 Chrome 自动化作为 skill 激活，并要求先读取当前 tab 上下文。
- ClaudeCode 源码可确认：`utils/claudeInChrome/toolRendering.tsx` 的浏览器工具包括 `navigate`、`read_page`、`find`、`form_input`、`computer`、`gif_creator`、`read_console_messages`、`read_network_requests`、`tabs_context_mcp`。
- ClaudeCode 源码可确认：`services/tools/toolOrchestration.ts` 和 `services/tools/StreamingToolExecutor.ts` 提供并发安全分批、流式工具执行、进度、中断和失败取消。
- ClaudeCode 当前本地源码无法确认：外部包 `@ant/claude-for-chrome-mcp` 和 Chrome 扩展内部如何实现视觉定位、页面恢复、browser_task/lightning_turn 细节。
- learning_agent 当前具备真实 Chrome 连接、可见 Chromium、浏览器 MCP 工具、`browser_type_secret`、`browser_flow_run`、`browser_replay`、acceptance verifier，但浏览器任务仍缺少独立 Browser Runtime 状态机。
- 新计划结论：先做 Browser Protocol 和 Runtime Store，再做 session/observation/locator/executor/recovery/verifier/status；不要继续只在 `browser_automation_mcp_server.py` 里堆零散工具。

## Current Learning Agent Findings

- `learning_agent/acceptance_controller/controller.ps1` can drive a real visible terminal and collect screenshots, events, and `result.json`.
- `learning_agent/acceptance/verifier.py` can replay a real acceptance run and verify events, debug log, screenshots, and success markers.
- `learning_agent/core/agent.py` already has `run_events()` and writes session events through `TranscriptWriter`.
- `learning_agent/core/session.py` has a minimal `SessionStore`, `SessionRecord`, and compact helper.
- `learning_agent/core/agent.py` stores `task_runs`, `cron_records`, `monitor_records`, and `background_commands` in process memory, so they are not durable long-task infrastructure.

## ClaudeCode Harness Findings

- `D:\ClaudeCode-main\ClaudeCode-main\QueryEngine.ts` owns query lifecycle and records transcript data early enough for resume after interruption.
- `D:\ClaudeCode-main\ClaudeCode-main\utils\sessionStorage.ts` persists transcripts, session metadata, remote-agent sidecars, and flushes session storage before result delivery.
- `D:\ClaudeCode-main\ClaudeCode-main\utils\messageQueueManager.ts` centralizes queued commands and task notifications with priority.
- `D:\ClaudeCode-main\ClaudeCode-main\tasks\LocalAgentTask\LocalAgentTask.tsx` manages local background agents, pending messages, abort, and task notifications.
- `D:\ClaudeCode-main\ClaudeCode-main\tasks\RemoteAgentTask\RemoteAgentTask.tsx` persists remote task identity and restores polling after `--resume`.
- `D:\ClaudeCode-main\ClaudeCode-main\services\tools\*` implements validation, permissions, hooks, progress, streaming tool execution, and concurrency control.
- `D:\ClaudeCode-main\ClaudeCode-main\components\tasks\*` provides user-visible task state and progress.

## Design Decision

- Build a focused, independent `learning_agent/harness/` module first.
- Do not replace the main agent loop in this pass.
- Make every long-task state transition durable and auditable.
- Treat stage verification as a first-class gate, not an optional log message.
# 当前任务发现：真实浏览器能力对齐 ClaudeCode（2026-05-31）

## ClaudeCode 已确认源码能力

1. `commands/chrome/chrome.tsx`：Chrome 扩展入口、安装状态、站点级权限管理。
2. `skills/bundled/claudeInChrome.ts`：Chrome 浏览器自动化 skill 和当前 tab 上下文入口。
3. `hooks/usePromptsFromClaudeInChrome.tsx`：从 Chrome 扩展接收 prompt、图片和 tabId，并进入消息队列。
4. `utils/computerUse/mcpServer.ts`：computer-use MCP 层支持桌面和坐标类交互。
5. `components/permissions/ComputerUseApproval/ComputerUseApproval.tsx`：computer-use 权限审批和系统权限恢复提示。
6. `services/tools/StreamingToolExecutor.ts`：流式、并发安全的工具执行。
7. `services/tools/toolExecution.ts`：权限决策、hook、MCP 错误状态和工具结果处理。
8. `utils/conversationRecovery.ts`：会话恢复和未完成工具调用清理。
9. `plugins/builtinPlugins.ts`：插件启用、工具允许、hooks 和 MCP server 配置。

## learning_agent 已确认源码能力

1. `learning_agent/browser_automation_mcp_server.py`：基础浏览器工具、真实 Chrome 连接、profile 状态。
2. `learning_agent/browser_real_chrome.py`：真实 Chrome profile 校验、敏感脚本阻断和审计。
3. `learning_agent/browser/harness.py`：公开搜索场景的真实浏览器任务 harness。
4. `learning_agent/browser/permissions.py`：公开 Google 搜索场景的自动权限批准。

## 待补齐缺口

1. 页面失败恢复还不够系统。
2. 视觉定位和坐标点击能力不足。
3. 复杂网站多阶段流程缺少持久轨迹。
4. 登录态安全缺少站点级授权和回放限制。
5. 插件兼容状态不可见。
6. 异常重试缺少统一封装。
7. 浏览器任务缺少安全回放能力。
## 2026-06-01 ClaudeCode 本地真实浏览器能力对比结论

- ClaudeCode 的本地真实浏览器能力不是单个 Playwright 脚本，而是两层架构：`claude-in-chrome` Chrome 扩展/MCP/native host/bridge，以及 `computer-use` OS 级鼠标键盘截图 MCP。
- ClaudeCode 源码可确认的优势包括：Chrome 扩展安装检测、Windows native host 注册、bridge/native socket、OAuth/user/device 配对、站点权限、`/chrome` 状态 UI、View Tab 渲染、MCP 工具覆盖、StreamingToolExecutor 并发流式执行、pre/post hook、权限决策和工具失败恢复。
- ClaudeCode 的核心 Chrome 工具细节有一部分在外部包 `@ant/claude-for-chrome-mcp` 和 `@ant/computer-use-mcp` 中，本地源码只能确认集成方式和工具表面，不能把外部包内部算法当作已读源码证据。
- learning_agent 当前已具备可见 Chromium、真实 Chrome CDP、Chrome extension provider scaffold、native host 协议、provider router、tabs context、site permission、action executor、runtime store、flow checkpoint/replay、recording/GIF/status/verifier/controller 验收等能力。
- 估算：learning_agent 的本地真实浏览器能力整体约为 ClaudeCode 的 70% 到 78%，中位数约 72%。最大未对齐点不是能否点网页，而是生产级插件/native-host 生态、OS 级 computer-use、成熟流式工具执行器、Chrome 发起任务和终端 UI/SDK 状态生态。
---

## 2026-06-03 Phase 39 Windows Coordinates Findings

- Phase39 adds a dedicated coordinate model instead of leaving DPI and monitor math inside scattered action code.
- `build_coordinate_context(...)` now records window-relative input, logical screen coordinates, display-relative logical coordinates, physical screen coordinates, DPI scale, and selected display metadata.
- `prepare_action_arguments(...)` still preserves Phase30-compatible `coordinate_used` fields while adding Phase39 physical coordinate evidence for newer callers.
- `WindowsComputerUseBackend.get_window_state` can now expose the same coordinate context at both top-level response data and inside `state`, so other agents do not need to reimplement coordinate math.
- Negative monitor positions are covered by tests, so multi-monitor layouts with a display left of the primary monitor no longer silently collapse into positive-only assumptions.
- Current evidence: focused tests 5 OK, Phase30-39 regression 50 OK, full regression 675 OK skipped=1, visible terminal run `learning_agent/acceptance_controller/runs/agent_capability_phase39_windows_coordinates-20260603_111521`, and independent verifier passed.
- Boundary: Phase39 does not expand real desktop actions; it only makes the coordinate contract safer before later action execution phases.
---

## 2026-06-03 Phase 40 Windows Abort Cleanup Findings

- Phase40 adds `WindowsComputerUseSessionRuntime` so global abort, turn cleanup, and notifications share one runtime layer instead of staying scattered across terminal commands.
- `/computer abort <reason>` now writes the existing durable abort flag and records a durable `computer_use_abort_requested` notification.
- `/computer cleanup [session_id]` releases the selected session lock and records `computer_use_turn_cleanup_completed`.
- `/computer notifications` exposes recent abort/cleanup events across terminal commands because notifications are stored in `session_runtime_notifications.json` under the Computer Use lock root.
- `/computer status` now includes `Computer Runtime`, making the runtime model, marker, notification count, cleanup count, latest notification, and `actions_expanded=false` visible to the user.
- Current evidence: focused tests 4 OK, Phase30-40 regression 54 OK, full regression 679 OK skipped=1, visible terminal run `learning_agent/acceptance_controller/runs/agent_capability_phase40_windows_abort_cleanup-20260603_112730`, and independent verifier passed.
- Boundary: Phase40 is a safety/runtime layer and does not make broad Windows automation available.

---

## 2026-06-03 Phase 41 Windows Image Results Findings

- Phase41 adds a stable `image_result` block for Computer Use screenshots, instead of leaving screenshot paths buried inside generic result dictionaries.
- `image_result` blocks include artifact path, image path, MIME type, width, height, screenshot id, evidence path, marker, and explicit `sensitive_text_included=false`.
- `ComputerUseActionResult.to_text(...)` appends a short `Computer Use Image Results` section only when image blocks exist.
- `LearningAgent` now records Computer Use image artifacts into `active_artifacts`, which keeps screenshot files discoverable during long task summaries and resume.
- The recursive image block collector deduplicates by `artifact_path`; this avoids duplicate display when the same block is synchronized at both top-level `data.image_results` and nested `state.image_results`.
- Current evidence: focused tests 4 OK, Windows Computer Use regression 70 OK, full regression 683 OK skipped=1, visible terminal run `learning_agent/acceptance_controller/runs/agent_capability_phase41_windows_image_results-20260603_114516`, and independent verifier passed.
- Boundary: Phase41 improves model-visible screenshot references only; it does not expand real desktop actions.

---

## 2026-06-03 Phase 42 Windows Final Matrix Findings

- Phase42 adds a safe final matrix runner that composes Phase35-41 selftests without touching the real desktop.
- The final matrix JSON explicitly lists Phase35-41 markers, OK tokens, covered capabilities, and `actions_expanded=false` for every phase.
- Dynamic Phase42 coverage includes observe, evidence, approval, gated refusal, safe fake action, abort cleanup, and artifact visibility.
- Phase42 forces Phase35/36 dependency paths through safe injected dependency-missing checks, so the final matrix does not launch real UIA or WGC capture during this aggregate run.
- Phase42 uses Phase37 fake SendInput implementation coverage as the safe action proof and still confirms real input is disabled by default.
- Current evidence: focused tests 3 OK, Windows Computer Use regression 73 OK, full regression 686 OK skipped=1, visible terminal run `learning_agent/acceptance_controller/runs/agent_capability_phase42_windows_computer_use_final_matrix-20260603_115600`, and independent verifier passed.
- Boundary: Phase42 proves the safety contracts are wired together; it does not prove production-grade real WGC/UIA dependencies are installed or that broad Windows automation is enabled.
---

## 2026-06-03 Phase 43 Windows Native Capability Matrix Findings

- Phase43 moved native status from scattered `native_observation_diagnostics` fields into a normalized capability matrix.
- The matrix records `name`, `category`, `available`, `enabled`, `reason`, and `next_step` for platform, read-only inventory, native helper, WGC, GDI fallback, UIA, Win32 text fallback, SendInput, and evidence store.
- `/computer status` now shows `Computer Native Capability Matrix`, so users can see WGC/UIA/SendInput gaps without reading raw JSON.
- Phase43 deliberately keeps `actions_expanded=false`; no real mouse, keyboard, or window action scope was expanded.
- Evidence: focused tests 4 OK, Phase33/42/43 regression 10 OK, py_compile OK, CLI token `PHASE43_WINDOWS_NATIVE_CAPABILITY_OK`.

---

## 2026-06-03 Phase 44 Windows Native Host Findings

- Phase44 adds a dedicated in-process native host boundary instead of letting the controller call native helpers directly everywhere.
- The host exposes a stable protocol name, host id, supported message list, health check, and safe observe/capture summaries.
- Screenshot bytes are summarized but not returned in raw JSON; the response includes byte count and `screenshot_bytes_included=false`.
- The `action` message is intentionally present but refused by default, which gives later Phase47 a stable route without silently expanding behavior early.
- `cleanup` stops the host session and returns a machine-readable cleanup summary.
- Evidence: focused tests 4 OK, Phase32/43/44 regression 14 OK, py_compile OK, CLI token `PHASE44_WINDOWS_NATIVE_HOST_OK`.
- Boundary: Phase44 proves host/client architecture and message contracts; it does not enable real desktop actions.

---

## 2026-06-03 Phase 45 Windows Screenshot Runtime Findings

- Phase45 adds a `WindowsScreenshotCaptureRuntime` above individual providers so WGC and GDI are no longer scattered across host/helper call sites.
- The runtime tries providers in order, records provider attempts, saves successful screenshots through `ComputerUseEvidenceStore`, and returns model-visible `image_results`.
- Native host `capture` now accepts an injected screenshot runtime and still strips `screenshot_bytes`/`raw_bytes` before responding over the host protocol.
- The Phase45 CLI self-check uses safe injected providers: WGC intentionally fails, GDI succeeds, and native host integration is exercised without touching the real desktop.
- Evidence: focused tests 4 OK, py_compile OK, Phase32/36/44/45 regression 19 OK, CLI token `PHASE45_WINDOWS_SCREENSHOT_RUNTIME_OK`.
- Boundary: Phase45 proves screenshot runtime architecture and artifact flow; it does not claim WGC bindings are installed or that real desktop actions are expanded.

---

## 2026-06-03 Phase 46 Windows UIA Control Tree Findings

- Phase46 adds `WindowsUiaControlTreeRuntime`, which returns structured UIA nodes rather than only flattened accessibility text.
- Each node includes name, role, automation id, class name, bounds, enabled state, clickable hint, editable hint, node id, depth, and children.
- The runtime enforces `max_depth`, `max_nodes`, and `max_text_length`, and it redacts sensitive node names/ids through the existing Phase29 accessibility filter.
- Native host `observe` can now use an injected UIA tree runtime, while `capture` remains owned by the Phase45 screenshot runtime.
- Evidence: focused tests 4 OK, py_compile OK, Phase34/44/45/46 regression 18 OK, CLI token `PHASE46_WINDOWS_UIA_TREE_OK`.
- Boundary: Phase46 is read-only structure observation; it does not claim broad real Windows UI automation actions are enabled.

---

## 2026-06-03 Phase 47 Windows SendInput Dispatcher Findings

- Phase47 adds `WindowsSendInputDispatcher`, separating low-level event dispatch from the Phase37 executor contract.
- The dispatcher expands move, click, double_click, scroll, press_key, and type_text into low-level mouse/key/text events, while keeping `type_text` as length/hash only.
- `target_verifier` runs before low-level send; if the target changed, dispatcher returns `target_changed_before_send` and sends zero low-level events.
- Native host `action` remains refused by default, but can route through an injected action executor when explicitly enabled.
- Evidence: focused tests 4 OK, py_compile OK, Phase37/44/47 regression 13 OK, CLI token `PHASE47_WINDOWS_SENDINPUT_DISPATCHER_OK`.
- Boundary: Phase47 proves dispatcher behavior with a recording low-level sender; real desktop use still requires opt-in, approval, lock, abort, trusted window target, and evidence.

---

## 2026-06-04 Phase92 Universal Windows Computer Use Mode Findings

- User corrected the Phase90/91 direction: representative apps such as Notepad and Paint must remain acceptance samples, not one-controller-per-app product architecture.
- The existing Phase65-75 blueprint already states the correct principle: do not build one script per app; build a generic observe -> plan -> act -> verify -> recover loop.
- Existing modules that should be composed rather than duplicated:
  - `observation_fusion.py`: screenshot/UIA/window/OCR slot fusion.
  - `prompt_task_planner.py`: prompt-to-step planning and high-risk classification.
  - `closed_loop_executor.py`: observe/act/verify/recover contract.
  - `app_window_control.py`: app launch, focus, and window identity.
  - `generic_control_actions.py`: click/type/control actions.
  - `generic_input_actions.py`: hotkey/menu/scroll/drag.
  - `real_app_safety_boundary.py`: Phase60 grants, Phase72 risk refusal, abort before low-level send.
  - `production_live_control.py`: production host adapter, permission gate, clipboard guard, observe-act-verify loop.
  - `live_app_dispatcher.py` and `notepad_live_smoke.py`: useful as representative evidence, but must not become the main architecture.
- Phase92 should introduce one `UniversalWindowsComputerUseRuntime` and one `computer_use_mode` style contract that turns a natural prompt into a generic Windows control session.
- Success must be measured by generic capability tokens such as `single_universal_runtime=true`, `per_app_controller_required=false`, `prompt_to_any_normal_app=true`, and `representative_apps_are_acceptance_only=true`.
- Safety boundary remains mandatory: UAC, passwords, payment, captcha, login secrets, terminal dangerous commands, Windows security/settings, and administrator-sensitive actions must stop or ask confirmation.

Implementation finding:

- `UniversalWindowsComputerUseRuntime` now exists and composes observation fusion, prompt task planning, generic control actions, generic input actions, real app safety boundary, persistent grants, and production host adapter.
- `computer_use` and `computer-use` now accept `operation=mode` and `operation=run_prompt`, while audit logs keep only prompt hash and length.
- High-risk Chinese and English prompts are treated as confirmation-required, and raw prompt text is kept out of Phase92 reports and agent observation logs.
- Unauthorized window and target drift checks both return zero low-level events.
- The runtime proves the universal architecture with representative tokens; default real actions remain disabled.
