# Phase90 Live App Dispatcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a controlled Windows live app dispatcher that composes existing authorization, safety, app-window, and input-event layers.

**Architecture:** Add a focused `live_app_dispatcher.py` module that routes representative app operations through Phase60 grants, Phase69 app/window identity, Phase72 safety checks, and Phase71 input-event recording. Keep real desktop dispatch disabled by default and verify the feature with tests plus real visible terminal acceptance.

**Tech Stack:** Python, unittest, PowerShell acceptance controller, existing `learning_agent.computer_use` modules.

---

### Task 1: Add Red Tests

**Files:**
- Create: `learning_agent/tests/test_windows_computer_use_live_app_dispatcher_phase90.py`

- [x] **Step 1: Write failing tests**

Tests must import `learning_agent.computer_use.live_app_dispatcher` and assert the Phase90 marker, OK token, dispatcher contract, authorization refusal, dangerous-window refusal, text redaction, and scenario tokens.

- [x] **Step 2: Run tests to verify red**

Run: `python -m unittest learning_agent.tests.test_windows_computer_use_live_app_dispatcher_phase90`

Expected: fail with `ModuleNotFoundError: No module named 'learning_agent.computer_use.live_app_dispatcher'`.

### Task 2: Implement Dispatcher

**Files:**
- Create: `learning_agent/computer_use/live_app_dispatcher.py`
- Modify: `learning_agent/computer_use/__init__.py`

- [x] **Step 1: Add `WindowsLiveAppDispatcher`**

The dispatcher must create an isolated Phase60 grant store, Phase72 safety boundary, Phase69 recording app/window runtime, and Phase71 recording input runtime.

- [x] **Step 2: Add safe dispatch behavior**

`dispatch(app, operation, payload)` must reject unsafe launch plans, reject missing grants through Phase72, record authorized events through Phase71, and never perform real dispatch by default.

- [x] **Step 3: Add Paint Pikachu live plan**

Reuse Phase74 `WindowsRepresentativeE2EMatrix.build_paint_pikachu_scenario(real_smoke=False)` and require humanlike strokes with `direct_image_file_cheat=false`.

- [x] **Step 4: Add CLI contract**

Expose `run_phase90_live_app_dispatcher_contract(...)`, `phase90_cli_line(...)`, and `main(...)`.

### Task 3: Acceptance Scenario

**Files:**
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase90_live_app_dispatcher.json`

- [x] **Step 1: Add visible terminal scenario**

The scenario must instruct the agent to run:

```powershell
$env:PYTHONPATH='..'; python -c "from learning_agent.computer_use.live_app_dispatcher import main; raise SystemExit(main())"
```

- [x] **Step 2: Require stable tokens**

The scenario must require `PHASE90_WINDOWS_LIVE_APP_DISPATCHER_READY`, `PHASE90_WINDOWS_LIVE_APP_DISPATCHER_OK`, `notepad_live_dispatch_contract=true`, `dangerous_window_zero_events=true`, and `uncontrolled_actions_expanded=false`.

### Task 4: Verification And Records

**Files:**
- Modify: `agent_memory/context.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`
- Modify: `task_plan.md`
- Create: `agent_memory/agent_capability_phase90_live_app_dispatcher_20260604.md`

- [x] **Step 1: Run automated verification**

Run focused tests, Phase76-90 regression, Windows Computer Use discovery tests, and compileall.

- [x] **Step 2: Run visible terminal acceptance**

Run `learning_agent/acceptance_controller/controller.ps1` with the Phase90 scenario and verify `completed=True`, `assertion_passed=True`, `final_printed=True`, and `permission_sent_count=0`.

- [x] **Step 3: Back up changed files**

Copy the Phase90 code, tests, scenario, docs, and memory records to `learning_agent/test/agent_capability_phase90_live_app_dispatcher_20260604/`.
