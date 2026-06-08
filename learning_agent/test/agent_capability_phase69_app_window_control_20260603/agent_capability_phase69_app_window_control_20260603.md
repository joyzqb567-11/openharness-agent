# 2026-06-03 Phase69 App Window Control

## Status

Completed.

## Summary

Phase69 added the app launch, focus, and target window identity contract layer for Windows Computer Use. It builds safe `Start-Process` style launch plans, uses recording launch/focus adapters for contract acceptance, and blocks target drift by comparing window identity before and after focus.

## Files

- Added `learning_agent/computer_use/app_window_control.py`.
- Added `learning_agent/tests/test_windows_computer_use_app_window_control_phase69.py`.
- Added `learning_agent/acceptance_controller/scenarios/agent_capability_phase69_app_window_control.json`.
- Modified `learning_agent/computer_use/__init__.py` to export Phase69 APIs.
- Updated `task_plan.md`.
- Updated `docs/superpowers/plans/2026-06-03-phase65-75-humanlike-windows-operator.md`.

## Contract

Stable token line:

```text
PHASE69_APP_WINDOW_CONTROL_READY PHASE69_APP_WINDOW_CONTROL_OK app_launch=true window_focus=true target_window_identity=true target_drift_blocked=true actions_expanded=false
```

Key public APIs:

- `build_launch_plan(...)`
- `Phase69RecordingLauncher`
- `Phase69RecordingFocuser`
- `WindowsAppWindowControlRuntime`
- `WindowsAppWindowControlRuntime.launch_app(...)`
- `WindowsAppWindowControlRuntime.focus_window(...)`
- `WindowsAppWindowControlRuntime.verify_target_identity(...)`
- `run_phase69_app_window_control_contract(...)`
- `phase69_cli_line(...)`

## Verification

- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.app_window_control'`.
- Focused Phase69 tests passed: 5 OK.
- Adjacent Phase68/69 regression passed: 9 OK.
- `py_compile` passed for `app_window_control.py`, `computer_use/__init__.py`, and the Phase69 test file.
- Real visible `start_oauth_agent.bat` terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`.
- Phase69 visible terminal evidence: `learning_agent/acceptance_controller/runs/agent_capability_phase69_app_window_control-20260603_223344/result.json`.
- Independent verifier passed for the same run with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.

## Boundary

- Phase69 does not expand the real desktop action surface.
- Phase69 uses recording launch/focus adapters for contract acceptance and does not open real user applications during tests or visible terminal acceptance.
- Phase69 does not click, type, drag, draw, save files, control Paint, change registry, change Windows settings, or request administrator permission.
- Phase70 must add generic click, type, and control actions while staying behind target guards, closed-loop verification, and later safety gates.

## Next

Continue with Phase70: Generic Click, Type, And Control Actions.
