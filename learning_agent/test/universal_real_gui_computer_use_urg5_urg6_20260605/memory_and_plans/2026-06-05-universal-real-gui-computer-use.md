# Universal Real GUI Computer Use Implementation Plan

> **For agentic workers:** Execute this plan task by task. Do not convert representative applications into per-app controllers. Paint, Notepad, Calculator, and Browser are acceptance samples only.

## Goal

Build `/computer use --full` into a universal real Windows GUI Computer Use loop:

`observe -> target identity -> plan -> generic action DSL -> SendInput -> observe -> verify -> cleanup`

The mature result must prove real desktop execution through visible terminal acceptance, while still refusing high-risk windows and never requiring one controller or allowlist entry per local application.

## Architectural Rules

1. No `PaintController`, `NotepadController`, `CalculatorController`, or app-specific controller class.
2. No `if app == "mspaint"` execution branch for product logic.
3. No generated PNG/SVG/JPG artifact may be used as a fake final drawing result.
4. No hardcoded per-app coordinate recipe may be used as product logic.
5. All representative app tests must use the same universal runtime.
6. Every real action must recheck target identity, abort state, session state, and safety boundary.
7. Every stage must produce automated tests, `py_compile`, visible-terminal evidence, progress memory, and `learning_agent/test/...` backups.

## Success Tokens

The final maturity command must eventually emit:

```text
UNIVERSAL_REAL_GUI_COMPUTER_USE_READY
single_universal_real_gui_loop=true
per_app_controller_required=false
hardcoded_app_whitelist_required=false
ordinary_apps_controlled_by_generic_runtime=true
representative_apps_are_acceptance_only=true
real_window_observation=true
real_uia_or_vision_targeting=true
real_sendinput_dispatch=true
target_identity_rechecked_before_each_action=true
observe_plan_act_verify_loop=true
paint_pikachu_real_acceptance=true
notepad_real_acceptance=true
calculator_real_acceptance=true
browser_real_acceptance=true
script_artifact_route_blocked=true
real_desktop_execution_mature=true
uncontrolled_high_risk_actions_allowed=false
```

## Task List

### URG-1 Real ObservationFrame

Implement a universal read-only `ObservationFrame` that composes:

- real window inventory
- active or selected target window identity
- real screenshot artifact with pixel guard
- real UIA tree or available visual fallback slot
- DPI and display metadata where available
- no mouse or keyboard actions

Files expected:

- `learning_agent/computer_use/universal_real_observation.py`
- `learning_agent/tests/test_windows_computer_use_universal_real_observation_frame.py`
- `learning_agent/acceptance_controller/scenarios/agent_capability_universal_real_gui_observation_frame.json`
- package export updates if needed

Verification:

- focused unit tests
- adjacent Phase56, Phase57, Phase66 regression
- `py_compile`
- real visible `start_oauth_agent.bat` terminal acceptance in safe read-only mode

### URG-2 Universal Target Session And Identity Guard

Implement a target session that can launch or focus ordinary apps through generic discovery, record target identity, and refuse drift before action.

Required facts:

- `generic_target_session=true`
- `per_app_controller_required=false`
- `target_identity_rechecked_before_each_action=true`
- `target_drift_zero_events=true`
- `agent_owned_or_user_authorized_window=true`

Representative samples:

- Notepad
- Paint
- Calculator

### URG-3 Generic Real Action DSL To SendInput

Implement the first real action bridge from generic DSL to SendInput.

Supported actions:

- `focus_window`
- `click_point`
- `double_click_point`
- `drag_path`
- `type_text`
- `press_key`
- `hotkey`
- `scroll`
- `wait`
- `observe`

Required facts:

- no app-specific execution branch
- low-level events are counted and audited
- `type_text` stores only length and hash
- stop or abort prevents remaining events
- default unsafe and unauthorized windows send zero events

### URG-4 Observe-Plan-Act-Verify Loop

Build the universal loop around the ObservationFrame, target identity guard, generic planner, DSL dispatcher, and verifier.

Required facts:

- every action has before and after observation
- visual or UIA verification determines next step
- retry is bounded
- failure exits with evidence and cleanup
- same loop handles Notepad, Calculator, and Paint sample tasks

### URG-5 Paint Pikachu Real Acceptance

Status: completed on 2026-06-05.

Evidence:

- Module: `learning_agent/computer_use/universal_paint_pikachu_acceptance.py`
- Test: `learning_agent/tests/test_windows_computer_use_universal_paint_pikachu_acceptance.py`
- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_universal_paint_pikachu_acceptance.json`
- Visible terminal run: `learning_agent/acceptance_controller/runs/agent_capability_universal_paint_pikachu_acceptance-20260605_223720/result.json`

Run the exact representative user workflow:

```text
/computer use --full
请使用本地电脑的画图软件画一个皮卡丘。
```

The result must prove:

- Paint is acceptance-only
- Paint window is real and observed
- canvas region is detected by generic observation
- real drag path events are dispatched
- canvas pixels change after real actions
- no generated image file is used as the result

### URG-6 Cross-App Final Maturity Matrix

Status: completed on 2026-06-05.

Evidence:

- Module: `learning_agent/computer_use/universal_final_maturity_matrix.py`
- Test: `learning_agent/tests/test_windows_computer_use_universal_final_maturity_matrix.py`
- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_universal_real_gui_final_matrix.json`
- Visible terminal run: `learning_agent/acceptance_controller/runs/agent_capability_universal_real_gui_final_matrix-20260605_223813/result.json`
- Backup: `learning_agent/test/universal_real_gui_computer_use_urg5_urg6_20260605/`

Create the final universal real GUI maturity matrix.

Representative acceptance minimum:

- Paint real drag drawing
- Notepad real text input
- Calculator real input and result observation
- Browser or ordinary third-party app real click and observation

Final gate:

- full automated regression
- `py_compile`
- final visible-terminal scenario
- evidence backup
- `agent_memory` and root planning files updated

## Stop Conditions

Stop and report a root-cause design blocker if any of these prevents progress for three consecutive attempts:

- real screenshot artifact is not reliable
- UIA and visual fallback are both unavailable
- SendInput cannot reliably target the verified window
- DPI or multi-display coordinate conversion is inconsistent
- target identity guard cannot prevent drift
- visible terminal controller cannot observe or type into `start_oauth_agent.bat`

## Current Execution Choice

The user explicitly requested continuous execution. Work will continue in the current project workspace, with backups under `learning_agent/test/`, because the existing branch already contains the current Computer Use history and acceptance evidence.
