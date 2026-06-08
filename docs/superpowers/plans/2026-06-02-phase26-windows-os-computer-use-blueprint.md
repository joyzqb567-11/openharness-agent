# Phase 26: Windows OS-Level Computer Use Blueprint

> **For agentic workers:** This is a blueprint only. Do not implement Windows desktop control code until the user explicitly approves the next implementation phase. Future implementation must use TDD, update `agent_memory/`, copy changed code to `learning_agent/test/`, and complete real visible terminal acceptance before claiming development completion.

**Goal:** Upgrade `learning_agent` from a safe Computer Use shell into a production-grade Windows OS Computer Use system that can observe and control real Windows application windows with strict safety, audit, and harness verification.

**Numbering Note:** Phase 25 is already used by the real Chrome extension/native-host connection follow-up. To avoid overwriting project history, this Windows Computer Use blueprint is Phase 26.

**Architecture:** Combine three proven ideas: ClaudeCode's permission, lock, MCP, and audit structure; Codex Computer Use's Windows concepts of app/window targeting, UI Automation, SendInput, and Windows.Graphics.Capture; and `learning_agent`'s existing safe `computer_status` / `computer_action`, harness, verifier, and visible terminal acceptance system.

**Tech Stack:** Python `unittest`, existing `learning_agent` tool protocol, a future Windows native helper preferably written in C#/.NET for UI Automation and Windows.Graphics.Capture, `SendInput` for input injection, JSON-RPC or stdio between Python and the helper, PowerShell acceptance controller for real visible terminal proof.

---

## Current Baseline

- `learning_agent/computer_use/controller.py` already has a safety controller, memory backend, unavailable backend, audit ids, and opt-in gate `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE`.
- `computer_status` and `computer_action` already exist, but the current Windows backend is still minimal and cannot match Codex-level app/window screenshots, UI Automation text trees, or robust window-relative actions.
- Phase 20 deliberately kept real OS actions disabled by default and verified only safe status behavior.
- The next implementation must preserve that default safety while adding a real Windows-native observation and action backend.

---

## Reference Principles

### From ClaudeCode Source

- Treat OS Computer Use as a dedicated capability with a controlled tool surface, not as scattered mouse/keyboard helper functions.
- Use session state, app allowlists, permission approval, action evidence, and lock ownership.
- Prevent multiple sessions from controlling the desktop at the same time.
- Provide a fast abort path and clear cleanup behavior.
- Convert screenshot/image/text tool results into model-readable evidence blocks.

### From Codex Computer Use Plugin

- Start from `list_apps`, select an app, then select one of its returned windows before acting.
- Prefer window-relative coordinates over full-screen coordinates.
- Use window state snapshots as point-in-time evidence, not as a live view.
- Use UI Automation text only when it helps the next action; keep large trees filtered and bounded.
- Use Windows.Graphics.Capture for window snapshots because it can capture target windows more reliably than foreground-only screenshots.
- Use SendInput for click, drag, scroll, type, and key actions.
- Do not automate terminal apps, security/privacy settings, password managers, authentication dialogs, or Codex itself.

### From learning_agent

- Keep the model's visible tool surface small.
- Keep real actions opt-in.
- Every action needs structured audit metadata.
- Every production feature needs a real visible terminal acceptance scenario through `learning_agent/start_oauth_agent.bat`.
- Every phase must have focused tests, full regression, phase report, and learning backup.

---

## Target Tool Surface

The model-facing surface should stay compact:

1. `computer_status`
   - Shows backend availability, platform, opt-in state, lock state, forbidden app policy, last audit event, and last evidence path.

2. `computer_observe`
   - Read-only desktop observation.
   - Actions: `list_apps`, `list_windows`, `get_window_state`, `get_active_window`, `read_clipboard` only if policy permits.
   - Returns app/window ids, titles with length limits, screenshot ids, screenshot dimensions, and optional UI Automation excerpts.

3. `computer_action`
   - Write/action tool.
   - Actions: `activate_window`, `click`, `double_click`, `type_text`, `press_key`, `scroll`, `drag`, `set_value`, `open_app`, `write_clipboard`.
   - Requires explicit `confirm_desktop_control=true`, policy approval, lock ownership, and safe target validation.

Internal backend actions can be more granular, but the model should not need a dozen first-round tools.

---

## Core Data Contracts

### Window Identity

Every actionable request must target a known window returned by a previous observation:

```text
app_id
window_id
title_preview
process_path_hash
captured_at
```

Do not let the model invent a window id. If a window handle becomes stale, the controller must rehydrate it from the backend or ask for a fresh observation.

### Window State

`get_window_state` should return:

```text
window
screenshot_id
screenshot_width
screenshot_height
screenshot_origin
accessibility_excerpt
focused_element
selected_text_preview
document_text_preview
evidence_path
audit_id
```

Large screenshots and UI trees should be saved as evidence artifacts, while the tool response returns bounded summaries.

### Action Evidence

Every action should record:

```text
audit_id
action
target_window
allowed
reason
before_evidence_id
after_evidence_id
text_length
coordinate_used
timestamp
```

Never store raw sensitive text in audit logs. Store length, hash, or preview only when safe.

---

## Windows Native Helper Design

The production helper should be a separate Windows-native process. Recommended implementation:

- C#/.NET helper for:
  - `UIAutomationClient` app/window/control tree.
  - `Windows.Graphics.Capture` window screenshots.
  - Win32 window enumeration and activation.
  - `SendInput` for mouse and keyboard.
  - DPI-aware coordinate conversion.

- Python `learning_agent` side for:
  - Tool schema and policy.
  - Permission gating.
  - Audit and evidence storage.
  - Harness integration.
  - Visible terminal commands.

- Protocol:
  - JSON-RPC or simple JSON-over-stdio.
  - Every helper request includes `request_id`, `action`, `target_window`, and safety metadata.
  - Every helper response includes `ok`, `error`, `window`, `evidence`, and timing.

Do not make the Codex Computer Use plugin a production dependency. It is a reference and comparison baseline; `learning_agent` must remain independently runnable.

---

## Safety Policy

### Default State

- Real Windows actions are disabled unless `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE=1`.
- Read-only observation may be enabled separately, but it must still avoid sensitive app categories.
- Tests use memory/fake backends and must never move the real mouse.

### Forbidden Targets

The controller must refuse to automate:

- Windows Terminal, Command Prompt, PowerShell, and terminal-like apps.
- Codex desktop UI, Codex CLI, and this agent's own visible terminal.
- Windows Security, Defender, firewall, privacy, permission, credential, and account settings.
- Password managers and password manager websites.
- Authentication dialogs, OTP forms, CAPTCHA, payment confirmation, password changes, and security interstitials.

### Confirmation Rules

Always require action-time confirmation or user handoff for:

- Deleting data.
- Installing software or extensions.
- Sending messages, submitting forms, uploading files, or transmitting sensitive data.
- Changing permissions, account settings, system settings, or financial/medical/legal state.

### Lock And Abort

- Add a durable computer-use lock under `learning_agent/memory/computer_use/lock.json`.
- A session must acquire the lock before action tools can run.
- Lock must include `session_id`, `pid`, `acquired_at`, `last_heartbeat`, and `owner_label`.
- A stop flag under `learning_agent/memory/computer_use/abort.flag` should be checked before every action.
- Later phases can add a global hotkey, but the first production version should at least support cooperative abort.

---

## Implementation Roadmap After This Blueprint

### Phase 27: Protocol And Tests

**Goal:** Replace the current loose `computer_action` shape with typed observe/action contracts.

**Likely files:**

- `learning_agent/computer_use/models.py`
- `learning_agent/computer_use/controller.py`
- `learning_agent/tools/schemas.py`
- `learning_agent/tests/test_windows_computer_use_protocol_phase27.py`

**Success criteria:**

- Unknown windows cannot be targeted.
- `computer_observe` exists as read-only schema.
- Existing Phase 20 tests still pass.

### Phase 28: Read-Only Windows Inventory

**Goal:** Add read-only app/window discovery with a fake backend and optional Windows backend probe.

**Likely files:**

- `learning_agent/computer_use/windows_backend.py`
- `learning_agent/computer_use/fake_backend.py`
- `learning_agent/runtime/status_snapshot.py`
- `learning_agent/tests/test_windows_computer_use_inventory_phase28.py`

**Success criteria:**

- `list_apps` and `list_windows` work in fake backend.
- Real backend status explains missing helper or platform constraints.
- No mouse/keyboard actions are possible.

### Phase 29: Window Screenshot And UI Automation Observation

**Goal:** Add `get_window_state` with screenshot evidence and optional UI Automation text.

**Likely files:**

- `learning_agent/computer_use/helper_client.py`
- `learning_agent/computer_use/evidence.py`
- `learning_agent/computer_use/windows_helper/`
- `learning_agent/tests/test_windows_computer_use_observe_phase29.py`

**Success criteria:**

- Evidence artifacts are saved under `learning_agent/memory/computer_use/evidence/`.
- Tool responses return bounded summaries.
- UI Automation text is filtered, not dumped unbounded.

### Phase 30: Safe Window-Relative Actions

**Goal:** Add action injection against a selected window.

**Likely files:**

- `learning_agent/computer_use/action_policy.py`
- `learning_agent/computer_use/windows_backend.py`
- `learning_agent/tools/executor.py`
- `learning_agent/tests/test_windows_computer_use_actions_phase30.py`

**Success criteria:**

- Actions require `confirm_desktop_control=true`.
- Actions require known window id and current lock.
- Coordinates are window-relative.
- Text action logs never store raw sensitive text.

### Phase 31: Lock, Abort, And Evidence Chain

**Goal:** Make desktop control serial, interruptible, and auditable.

**Likely files:**

- `learning_agent/computer_use/lock.py`
- `learning_agent/computer_use/audit.py`
- `learning_agent/computer_use/evidence.py`
- `learning_agent/tests/test_windows_computer_use_lock_abort_phase31.py`

**Success criteria:**

- Two sessions cannot both own the desktop lock.
- Abort flag prevents the next action.
- Before/after evidence is linked by `audit_id`.

### Phase 32: `/computer` Terminal Status UI

**Goal:** Add a beginner-readable terminal status command.

**Likely files:**

- `learning_agent/app/computer_status_renderer.py`
- `learning_agent/app/interactive.py`
- `learning_agent/runtime/status_snapshot.py`
- `learning_agent/tests/test_windows_computer_terminal_ui_phase32.py`

**Success criteria:**

- `/computer` shows backend, opt-in state, lock, last audit, last evidence, and safe next actions.
- It does not show raw sensitive text.
- It remains compact in visible terminal screenshots.

### Phase 33: Real Visible Terminal End-To-End Acceptance

**Goal:** Prove a safe real Windows app scenario end to end.

**Suggested safe scenario:**

- Use a controlled test app or Notepad.
- Launch/select the window.
- Observe screenshot/UIA state.
- Type a harmless marker such as `WINDOWS_COMPUTER_USE_OK`.
- Observe again and verify marker.
- Do not automate terminal apps or security-sensitive apps.

**Likely files:**

- `learning_agent/acceptance_controller/scenarios/agent_capability_phase33_windows_computer_use_e2e.json`
- `learning_agent/tests/test_windows_computer_use_acceptance_matrix_phase33.py`
- `agent_memory/agent_capability_phase33_windows_computer_use_e2e_20260602.md`

**Success criteria:**

- Focused tests pass.
- Full `python -m unittest discover -s learning_agent\tests` passes.
- `learning_agent/start_oauth_agent.bat` visible terminal acceptance passes.
- Independent verifier passes.
- Screenshot evidence proves the real Windows app interaction.

---

## Stop Conditions

- Stop before implementing the native helper until the user approves this blueprint.
- Stop if the helper cannot distinguish the target window from terminal/Codex/security apps.
- Stop if screenshots expose sensitive content that cannot be redacted or scoped.
- Stop if action targeting would require guessed full-screen coordinates.
- Stop if real visible terminal acceptance cannot be completed; report that development cannot be declared complete.

---

## Verification Strategy

Every implementation phase must run:

- Focused phase tests.
- Existing Phase 17/20 Computer Use tests.
- Tool schema/catalog/executor regression tests.
- Full `python -m unittest discover -s learning_agent\tests`.
- `py_compile` or helper build validation.
- Real visible terminal acceptance for any phase that changes runtime behavior.

For this Phase 26 blueprint only, no runtime tests or real visible terminal acceptance are required because no production code is changed.

---

## Approval Gate

If the user approves, start with Phase 27. Do not jump directly to real mouse/keyboard automation.

Suggested confirmation:

`确认，按 Phase 27 到 Phase 33 逐阶段实现 Windows OS Computer Use。`
