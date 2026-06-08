# Agent Capability Completion Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `learning_agent` 从“已经有浏览器和 harness 基础”推进到“具备生产级 Chrome 插件生态、全局工具执行器、OS 级控制、终端状态 UI 和真实端到端验收闭环”的成熟 agent。

**Architecture:** 本计划采用“主控路线图 + 阶段子计划”的方式推进，避免一次性横跨七个子系统导致任务跑偏。每个阶段先写独立 TDD 子计划，再改代码，再跑自动化测试，最后通过 `learning_agent/start_oauth_agent.bat` 做真实可见终端验收。

**Tech Stack:** Python standard library, unittest, Playwright/CDP, Chrome Manifest V3 extension, Windows native messaging host, JSON/JSONL durable runtime, existing `learning_agent` status/SDK/HTTP/CLI/harness modules.

---

## Success Criteria

- [ ] 生产级 Chrome extension 安装器可以生成 native host manifest、写入 Windows registry、检测安装状态、卸载/禁用注册项，并能给出可读修复建议。
- [ ] Chrome extension 配对和 session sync 可以建立 device/session 身份，支持 tab context push，并允许浏览器侧任务进入 `learning_agent` 主循环或 durable queue。
- [ ] 高层浏览器工具至少覆盖 `browser_form_input`、`browser_shortcuts_list`、`browser_shortcuts_execute` 和更强的语义定位。
- [ ] 全局 StreamingToolExecutor 不只服务浏览器工具，而是统一管理工具校验、权限、hook、并发安全、进度事件、结果截断和失败恢复。
- [ ] OS 级 Computer Use 在 Windows 上具备截图、鼠标、键盘、剪贴板、窗口/显示器状态、安全 allowlist、Escape 中止和可见审批边界。
- [ ] 类似 `/chrome` 的终端状态 UI 可以展示 extension、native host、active tab、site permission、pending command、recent action、recording/GIF 和 View Tab 信息。
- [ ] 每个阶段都有自动化测试、py_compile 或等价语法验证、学习备份、agent_memory 记录和真实可见终端验收证据。

## Scope Boundary

- In scope: 生产安装、配对同步、高层浏览器工具、全局工具执行、Windows Computer Use、终端状态 UI、真实验收矩阵。
- Out of scope for this master plan: 直接复制 ClaudeCode 私有外部包内部实现、绕过用户权限、保存明文密码、无提示控制敏感网站、一次性重写整个 agent。
- Stop condition: 任一阶段涉及权限、真实账号、注册表写入、安全策略或产品决策不明确时，必须停下来汇报，不允许猜测推进。
- Evidence rule: 不能把历史验收当作当前通过证据；每阶段完成时都要重新验证当前代码。

## Existing Baseline

- 已有可见 Chromium、真实 Chrome CDP、Chrome extension provider scaffold、native host 协议、origin/action 权限、runtime store、recording/GIF、fallback/recovery、status snapshot 和 acceptance controller。
- 已完成浏览器双轨 Stage 5-10：readonly extension、write actions、site permissions、status ecosystem、visual evidence、fallback recovery。
- 尚未完成本计划中的生产级安装/配对、浏览器发起任务、全局 StreamingToolExecutor、Windows OS 级 Computer Use 和成熟 `/chrome` 风格终端 UI。

---

## Phase 0: Planning And Safety Baseline

**Files:**
- Create: `agent_memory/agent_capability_completion_roadmap_20260601.md`
- Create: `docs/superpowers/plans/2026-06-01-agent-capability-completion-roadmap.md`
- Create: `learning_agent/test/agent_capability_completion_20260601/plan.md`
- Modify: `task_plan.md`
- Modify: `agent_memory/progress.md`

- [ ] **Step 1: Confirm baseline source evidence**

Read these files before implementation begins:

```powershell
Get-Content learning_agent\zqbcontext.md
Get-Content agent_memory\context.md -Tail 160
Get-Content agent_memory\progress.md -Tail 160
Get-Content findings.md -Tail 220
```

Expected: current agent has Stage 5-10 browser work completed, and this roadmap starts after that baseline.

- [ ] **Step 2: Freeze safety rules**

Record these non-negotiable rules in the active task plan:

```text
1. 不保存明文密码。
2. 不静默写注册表；写入前必须有明确阶段计划和回滚方式。
3. 不静默降级真实 Chrome provider。
4. 不把 CLI/selftest/stdin 当作真实可见终端验收。
5. 每个阶段完成前必须备份新改代码到 learning_agent/test。
```

Expected: later agents can read `task_plan.md` and immediately知道边界。

- [ ] **Step 3: Split into child implementation plans**

Create one detailed child plan per phase before editing code:

```text
Phase 1 child plan: Chrome extension installer/native host registry
Phase 2 child plan: Pairing and session sync
Phase 3 child plan: High-level browser tools
Phase 4 child plan: Global StreamingToolExecutor
Phase 5 child plan: Windows Computer Use
Phase 6 child plan: /chrome-like terminal status UI
Phase 7 child plan: End-to-end acceptance matrix
```

Expected: no phase starts from this master roadmap alone; each phase gets its own implementation plan and test list.

---

## Phase 1: Production Chrome Extension Install And Native Host Registry

**Files likely involved:**
- Modify: `learning_agent/browser_extension_host/manifest_installer.py`
- Modify: `learning_agent/browser_extension_host/native_host.py`
- Modify: `learning_agent/browser_extension_host/bridge_server.py`
- Modify: `learning_agent/browser/providers/chrome_extension.py`
- Modify: `learning_agent/browser_automation_mcp_server.py`
- Create/Modify tests under: `learning_agent/tests/`

- [ ] **Step 1: Write installer status tests**

Add tests proving the installer can report:

```text
not_installed
manifest_created
registry_registered
registry_missing
native_host_unreachable
extension_unpaired
```

Expected red result: current installer only generates manifest and cannot prove registry lifecycle.

- [ ] **Step 2: Implement Windows registry adapter behind a safe abstraction**

Design requirement:

```text
Registry operations must support dry_run, install, uninstall, status.
All write operations must produce reversible audit records.
No test should touch the real registry by default.
```

Expected: unit tests use a fake registry adapter; manual acceptance may use real Windows registry only when explicitly chosen.

- [ ] **Step 3: Add install/uninstall/status tools**

Expose model-visible or CLI-visible commands only after tests pass:

```text
browser_extension_install
browser_extension_uninstall
browser_extension_status
browser_extension_repair_hint
```

Expected: user can see exactly whether native host registration is ready.

- [ ] **Step 4: Verify**

Run:

```powershell
python -m unittest learning_agent.tests.test_chrome_extension_installer_stage13
python -m unittest discover -s learning_agent\tests
python -m py_compile learning_agent\browser_extension_host\manifest_installer.py
```

Expected: all pass before real terminal acceptance.

---

## Phase 2: Chrome Extension Pairing And Session Sync

**Files likely involved:**
- Modify: `learning_agent/browser_extension_host/pairing_store.py`
- Modify: `learning_agent/browser_extension_host/message_protocol.py`
- Modify: `learning_agent/browser_extension_host/bridge_server.py`
- Modify: `learning_agent/chrome_extension/background.js`
- Modify: `learning_agent/chrome_extension/content_script.js`
- Modify: `learning_agent/core/agent.py`
- Modify: `learning_agent/runtime/command_queue.py`

- [ ] **Step 1: Define pairing contract**

Required fields:

```json
{
  "device_id": "stable local device id",
  "session_id": "current agent session id",
  "extension_id": "chrome extension id when available",
  "paired_at": "iso timestamp",
  "last_seen_at": "iso timestamp",
  "allowed_origins": ["https://example.com"]
}
```

Expected: pairing record does not contain passwords, cookies, OAuth tokens or raw local profile paths.

- [ ] **Step 2: Add browser-to-agent prompt queue**

Design requirement:

```text
Chrome extension may push tab context, selected text, URL, screenshot reference, and user prompt.
The host must enqueue it into RuntimeCommandQueue instead of bypassing durable runtime.
```

Expected: browser-originated tasks survive restart and appear in status.

- [ ] **Step 3: Add session sync status**

Expose:

```text
paired/unpaired
last_seen
active_tab_url
pending_browser_prompts
last_browser_prompt_id
```

Expected: `/status` and provider status can show whether Chrome is truly connected.

---

## Phase 3: High-Level Browser Tools

**Files likely involved:**
- Modify: `learning_agent/browser/locator.py`
- Modify: `learning_agent/browser/action_executor.py`
- Modify: `learning_agent/browser/observation.py`
- Modify: `learning_agent/browser/providers/tool_surface.py`
- Modify: `learning_agent/browser_automation_mcp_server.py`
- Create tests under: `learning_agent/tests/test_browser_high_level_tools_stage15.py`

- [ ] **Step 1: Add `browser_form_input` plan and tests**

Required behavior:

```text
Input can target label, placeholder, aria name, selector, or semantic field name.
It must support text fields, textareas, selects, checkboxes and submit buttons.
It must refuse password-like fields unless secret input path is used.
```

Expected red result: current low-level click/type cannot reliably fill full forms in one audited action.

- [ ] **Step 2: Add browser shortcuts**

Expose:

```text
browser_shortcuts_list
browser_shortcuts_execute
```

Minimum shortcuts:

```text
refresh
back
forward
new_tab
close_tab
focus_address_bar
find_in_page
copy_page_url
```

Expected: shortcuts run through the same permission/audit path as other browser actions.

- [ ] **Step 3: Strengthen semantic locator**

Locator ranking must combine:

```text
visible text
aria label
placeholder
role
nearby label
stable selector
screenshot/coordinate fallback
```

Expected: tests prove ambiguous targets return multiple candidates instead of clicking blindly.

---

## Phase 4: Global StreamingToolExecutor

**Files likely involved:**
- Create: `learning_agent/tools/streaming_executor.py`
- Create: `learning_agent/tools/tool_contracts.py`
- Create: `learning_agent/tools/permission_runtime.py`
- Modify: `learning_agent/core/agent.py`
- Modify: `learning_agent/runtime/status_schema.py`
- Modify: `learning_agent/runtime/status_snapshot.py`
- Create tests under: `learning_agent/tests/test_global_streaming_tool_executor_stage16.py`

- [ ] **Step 1: Write red tests for global execution lifecycle**

Lifecycle states:

```text
received
validated
permission_requested
permission_granted
started
progress
completed
failed
denied
aborted
truncated
```

Expected red result: current execution is not centralized for all tools.

- [ ] **Step 2: Implement read/write concurrency policy**

Policy:

```text
Read-only tools may run concurrently.
Write tools run serially when they touch shared state.
Exclusive tools block sibling tools until complete.
```

Expected: browser writes, filesystem writes and OS control cannot race each other.

- [ ] **Step 3: Add hook and permission gates**

Required gates:

```text
pre_tool_hook
permission_decision
post_tool_hook
post_failure_hook
result_limit
audit_event
```

Expected: tool execution becomes auditable like ClaudeCode-style lifecycle, without copying private internals.

---

## Phase 5: Windows OS-Level Computer Use

**Files likely involved:**
- Create: `learning_agent/computer_use/`
- Create: `learning_agent/computer_use/models.py`
- Create: `learning_agent/computer_use/windows_backend.py`
- Create: `learning_agent/computer_use/permissions.py`
- Create: `learning_agent/computer_use/mcp_server.py`
- Modify: `learning_agent/mcp_servers.json`
- Modify: `learning_agent/runtime/status_snapshot.py`

- [ ] **Step 1: Define capability boundary**

Minimum capabilities:

```text
screenshot
mouse_move
mouse_click
mouse_drag
keyboard_type
key_press
clipboard_read
clipboard_write
window_list
window_focus
display_info
escape_abort
```

Expected: dangerous actions require allowlist and visible audit.

- [ ] **Step 2: Implement fake backend first**

Expected: all tests pass with fake backend before touching real Windows APIs.

- [ ] **Step 3: Add real Windows backend carefully**

Candidate libraries may include Python standard `ctypes` and existing environment packages only after inspection.

Expected: no external dependency is added without checking project pattern and user benefit.

- [ ] **Step 4: Add status and acceptance**

Expected: status shows computer-use enabled/disabled, backend, active window, last screenshot path, permission mode and abort state.

---

## Phase 6: `/chrome`-Like Terminal Status UI

**Files likely involved:**
- Modify: `learning_agent/app/status_renderer.py`
- Modify: `learning_agent/core/agent.py`
- Modify: `learning_agent/app/http_bridge.py`
- Modify: `learning_agent/sdk/status.py`
- Modify: `learning_agent/harness/cli.py`
- Create: `learning_agent/app/chrome_status.py`

- [ ] **Step 1: Define terminal commands**

Commands:

```text
/chrome
/chrome status
/chrome install
/chrome reconnect
/chrome permissions
/chrome tab
/chrome recording
/chrome diagnose
```

Expected: commands are status-first and explain next action in plain Chinese.

- [ ] **Step 2: Render actionable status**

UI sections:

```text
Extension
Native Host
Pairing
Active Tab
Site Permissions
Pending Commands
Recent Actions
Recordings
Repair Hints
```

Expected: user can understand what is broken without reading logs.

- [ ] **Step 3: Link UI to SDK/HTTP/CLI**

Expected: terminal, SDK, HTTP and CLI all read the same status snapshot instead of each inventing its own truth.

---

## Phase 7: Real End-To-End Acceptance Matrix

**Files likely involved:**
- Create/Modify: `learning_agent/acceptance_controller/scenarios/*.json`
- Modify: `learning_agent/acceptance/verifier.py`
- Create: `docs/superpowers/reports/2026-06-01-agent-capability-completion-acceptance.md`

- [ ] **Step 1: Create scenario matrix**

Required scenarios:

```text
extension install/status dry run
native host registration status
extension pairing status
browser-originated prompt sync
form input on local test page
shortcut execution on local test page
global executor concurrency audit
computer-use screenshot/status fake backend
/chrome status visible terminal command
full visible browser task with recording and verifier
```

Expected: each scenario has success marker, artifact checks and independent verifier replay.

- [ ] **Step 2: Run automated verification**

Minimum command set:

```powershell
python -m unittest discover -s learning_agent\tests
python -m compileall learning_agent
python learning_agent\learning_agent.py mcp-doctor
```

Expected: all pass before claiming implementation status.

- [ ] **Step 3: Run real visible terminal acceptance**

Required:

```powershell
H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat
```

Then type realistic user prompts into the visible terminal:

```text
请检查 /chrome 状态，告诉我 Chrome 插件、native host、当前标签页和权限是否正常。
请用浏览器打开一个本地测试表单，填写姓名和备注，然后生成录屏证据。
请展示当前 computer-use 状态，说明是否允许控制鼠标键盘。
```

Expected: final answer contains phase success markers, and verifier confirms `completed=true` and `assertion.passed=true`.

---

## Execution Order

1. Phase 1: Chrome extension installer/native host registry.
2. Phase 2: Pairing and session sync.
3. Phase 3: High-level browser tools.
4. Phase 4: Global StreamingToolExecutor.
5. Phase 5: Windows Computer Use.
6. Phase 6: `/chrome` terminal status UI.
7. Phase 7: Real end-to-end acceptance matrix.

Reason: 安装和配对是 Chrome 生态的地基；高层浏览器工具依赖稳定连接；全局执行器再统一所有工具；Computer Use 风险最高，放在权限和执行器成熟之后；最后用 `/chrome` UI 和真实验收把能力闭环展示出来。

## Final Gate

This roadmap is not complete until all are true:

1. All phase child plans exist and are marked complete.
2. Code changes are backed up under `learning_agent/test/`.
3. Automated tests and compile checks pass on current code.
4. `learning_agent/start_oauth_agent.bat` real visible terminal acceptance passes.
5. Independent verifier replays the acceptance runs successfully.

