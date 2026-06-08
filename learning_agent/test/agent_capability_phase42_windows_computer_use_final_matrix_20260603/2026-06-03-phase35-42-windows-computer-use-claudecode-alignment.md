# Phase 35-42 Windows Computer Use ClaudeCode Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move `learning_agent` Windows OS Computer Use from a safe read-only/native-helper foundation toward a ClaudeCode-grade production control stack, while staying honest about Windows-specific dependencies and real visible terminal acceptance.

**Architecture:** Keep the existing `computer_status` / `computer_observe` / `computer_action` split. Add missing Windows-native providers and action execution behind explicit opt-in, durable lock, trusted window references, before/after evidence, and visible terminal acceptance gates. Each phase must be independently testable and must not silently expand the real desktop action surface.

**Tech Stack:** Python standard library, `ctypes`, optional Windows UIA/WGC dependencies when present, existing `learning_agent.computer_use` modules, `unittest`, existing acceptance controller, `start_oauth_agent.bat` visible terminal workflow.

---

## Source Evidence Baseline

- ClaudeCode local `computer-use` is mature but macOS-only: [D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse/executor.ts](D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse/executor.ts).
- ClaudeCode uses app allowlist, permission UI, display state, lock, Escape abort, cleanup, OS notifications, and image/text result mapping through [D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse/wrapper.tsx](D:/ClaudeCode-main/ClaudeCode-main/utils/computerUse/wrapper.tsx).
- `learning_agent` already has Windows protocol, inventory, evidence, lock/abort, GDI fallback, UIA-first text provider, diagnostics, and visible terminal acceptance through Phase 34.
- Current Windows dependency probe on this machine: `uiautomation=False`, `comtypes=False`, `winrt/winsdk Windows.Graphics.Capture` unavailable, `platform=win32`.

## Global Success Criteria

- [ ] Each phase has a written agent_memory report.
- [ ] Each runtime phase starts with a failing test and then minimal implementation.
- [ ] Each new or modified source file is copied to `learning_agent/test/<phase-name>/`.
- [ ] Each phase runs focused tests, neighboring Computer Use regression, syntax checks, full test suite when feasible, scenario JSON validation, visible terminal acceptance, and independent verifier replay.
- [ ] No phase claims Windows real action maturity without real SendInput/WGC/UIA evidence.
- [ ] Terminal, Codex UI, security/privacy settings, password managers, authentication dialogs, captcha/OTP windows, and Windows Run remain forbidden automation targets.

## Stop Conditions

- Stop if a phase requires installing system dependencies, writing registry keys, or changing Windows security settings without explicit user confirmation.
- Stop if the target window is terminal/Codex/security/password/auth related.
- Stop if real visible terminal acceptance cannot be completed; report: `真实可见终端交互验收未完成，不能声明开发完成。`
- Stop if the same technical blocker repeats three times; record it in `agent_memory/bugs.md` and ask for user input.

---

## Phase 35: Real Safe-Window UIA Smoke Harness

**Goal:** Add a real safe-window smoke harness that attempts UIA against a self-owned safe Notepad target when the dependency exists, and otherwise reports dependency-missing honestly instead of using fake providers.

**Files:**
- Create: `learning_agent/computer_use/real_uia_smoke.py`
- Modify: `learning_agent/computer_use/__init__.py`
- Create: `learning_agent/tests/test_windows_computer_use_real_uia_smoke_phase35.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase35_windows_real_uia_smoke.json`
- Create: `agent_memory/agent_capability_phase35_windows_real_uia_smoke_20260603.md`
- Backup: `learning_agent/test/agent_capability_phase35_windows_real_uia_smoke_20260603/`

**Steps:**
- [ ] Write failing tests that import the Phase 35 smoke module and verify it reports dependency-missing without fake injection.
- [ ] Run the focused test and confirm it fails because `real_uia_smoke.py` does not exist.
- [ ] Implement a side-effect-safe smoke helper with injectable launcher/inventory/provider seams.
- [ ] Add a CLI selftest path that prints a stable marker and does not claim success when UIA dependency is missing.
- [ ] Add a visible terminal scenario that asks the agent to run the smoke check and report the stable marker.
- [ ] Run focused tests, neighboring Computer Use regression, `py_compile`, scenario JSON validation, full regression, visible terminal acceptance, and independent verifier.

**Acceptance Marker:** `PHASE35_WINDOWS_REAL_UIA_SMOKE_READY`

---

## Phase 36: Windows.Graphics.Capture Provider Contract

**Goal:** Add a WGC provider contract and dependency-gated implementation path, while keeping GDI fallback active and explicit.

**Files:**
- Modify: `learning_agent/computer_use/native_helper.py`
- Modify: `learning_agent/computer_use/native_diagnostics.py`
- Modify: `learning_agent/computer_use/__init__.py`
- Create: `learning_agent/tests/test_windows_computer_use_wgc_provider_phase36.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase36_windows_wgc_provider.json`
- Create: `agent_memory/agent_capability_phase36_windows_wgc_provider_20260603.md`
- Backup: `learning_agent/test/agent_capability_phase36_windows_wgc_provider_20260603/`

**Acceptance Marker:** `PHASE36_WINDOWS_WGC_PROVIDER_READY`

---

## Phase 37: SendInput Action Executor

**Goal:** Replace the current minimal `SetCursorPos + mouse_event` path with a gated SendInput executor covering `click`, `double_click`, `move_mouse`, `press_key`, `type_text`, and `scroll`.

**Files:**
- Create: `learning_agent/computer_use/sendinput_executor.py`
- Modify: `learning_agent/computer_use/controller.py`
- Modify: `learning_agent/computer_use/__init__.py`
- Create: `learning_agent/tests/test_windows_computer_use_sendinput_phase37.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase37_windows_sendinput_executor.json`
- Create: `agent_memory/agent_capability_phase37_windows_sendinput_executor_20260603.md`
- Backup: `learning_agent/test/agent_capability_phase37_windows_sendinput_executor_20260603/`

**Acceptance Marker:** `PHASE37_WINDOWS_SENDINPUT_EXECUTOR_READY`

---

## Phase 38: Windows ComputerUseApproval Model

**Goal:** Add a Windows approval/session grant model similar to ClaudeCode's app allowlist and grant flags, using terminal-safe status first before any UI expansion.

**Files:**
- Create: `learning_agent/computer_use/approval.py`
- Modify: `learning_agent/computer_use/controller.py`
- Modify: `learning_agent/app/interactive.py`
- Create: `learning_agent/tests/test_windows_computer_use_approval_phase38.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase38_windows_computer_approval.json`
- Create: `agent_memory/agent_capability_phase38_windows_computer_approval_20260603.md`
- Backup: `learning_agent/test/agent_capability_phase38_windows_computer_approval_20260603/`

**Acceptance Marker:** `PHASE38_WINDOWS_COMPUTER_APPROVAL_READY`

---

## Phase 39: DPI, Multi-Monitor, And Coordinate Model

**Goal:** Add a stable coordinate model that records logical, physical, window-relative, and display-relative coordinates.

**Files:**
- Create: `learning_agent/computer_use/coordinates.py`
- Modify: `learning_agent/computer_use/action_policy.py`
- Modify: `learning_agent/computer_use/windows_backend.py`
- Create: `learning_agent/tests/test_windows_computer_use_coordinates_phase39.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase39_windows_coordinates.json`
- Create: `agent_memory/agent_capability_phase39_windows_coordinates_20260603.md`
- Backup: `learning_agent/test/agent_capability_phase39_windows_coordinates_20260603/`

**Acceptance Marker:** `PHASE39_WINDOWS_COORDINATES_READY`

---

## Phase 40: Global Abort, Cleanup, And Notifications

**Goal:** Add Windows-safe global abort and turn cleanup semantics comparable to ClaudeCode's Escape hotkey, cleanup, and OS notification path.

**Files:**
- Create: `learning_agent/computer_use/session_runtime.py`
- Modify: `learning_agent/computer_use/lock.py`
- Modify: `learning_agent/app/interactive.py`
- Create: `learning_agent/tests/test_windows_computer_use_session_runtime_phase40.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase40_windows_abort_cleanup.json`
- Create: `agent_memory/agent_capability_phase40_windows_abort_cleanup_20260603.md`
- Backup: `learning_agent/test/agent_capability_phase40_windows_abort_cleanup_20260603/`

**Acceptance Marker:** `PHASE40_WINDOWS_ABORT_CLEANUP_READY`

---

## Phase 41: Model-Visible Screenshot Result Blocks

**Goal:** Improve computer-use result handling so screenshots are available as stable artifacts and model-readable image references, without dumping sensitive UI text.

**Files:**
- Modify: `learning_agent/computer_use/evidence.py`
- Modify: `learning_agent/computer_use/controller.py`
- Modify: `learning_agent/core/agent.py`
- Create: `learning_agent/tests/test_windows_computer_use_image_results_phase41.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase41_windows_image_results.json`
- Create: `agent_memory/agent_capability_phase41_windows_image_results_20260603.md`
- Backup: `learning_agent/test/agent_capability_phase41_windows_image_results_20260603/`

**Acceptance Marker:** `PHASE41_WINDOWS_IMAGE_RESULTS_READY`

**Status:** Completed on 2026-06-03 with focused tests, Windows Computer Use regression, full unittest regression, real visible terminal acceptance, independent verifier replay, and learning backup.

---

## Phase 42: Final Windows Computer Use E2E Matrix

**Goal:** Build a final acceptance matrix for Phase 35-41 and run a safe Windows end-to-end scenario covering observe, evidence, approval, gated action refusal/safe action, abort, cleanup, and artifact visibility.

**Files:**
- Create: `learning_agent/acceptance_controller/final_acceptance_matrix_phase42_windows_computer_use.json`
- Create: `learning_agent/tests/test_windows_computer_use_final_matrix_phase42.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase42_windows_computer_use_final_matrix.json`
- Create: `agent_memory/agent_capability_phase42_windows_computer_use_final_matrix_20260603.md`
- Backup: `learning_agent/test/agent_capability_phase42_windows_computer_use_final_matrix_20260603/`

**Acceptance Marker:** `PHASE42_WINDOWS_COMPUTER_USE_FINAL_READY`

**Status:** Completed on 2026-06-03 with final matrix JSON, safe Phase35-41 contract runner, focused tests, Windows Computer Use regression, full unittest regression, real visible terminal acceptance, independent verifier replay, and learning backup.

---

## Execution Notes

- Execute Phase 35 first. Do not start Phase 36 until Phase 35 has tests, backup, memory report, and visible terminal acceptance.
- If a dependency is missing, the phase should pass only if it reports the missing dependency honestly and records the exact next action.
- Do not use fake providers as proof of real native maturity; fake providers are allowed only to prove contracts.
- Every final phase report must state what was actually proven and what remains unproven.
