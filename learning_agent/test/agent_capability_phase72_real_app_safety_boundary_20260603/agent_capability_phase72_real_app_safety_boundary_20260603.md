# Phase72 Real App Safety Boundary

Date: 2026-06-03

Status: completed.

## What Changed

- Added `learning_agent/computer_use/real_app_safety_boundary.py`.
- Added `learning_agent/tests/test_windows_computer_use_real_app_safety_boundary_phase72.py`.
- Added `learning_agent/acceptance_controller/scenarios/agent_capability_phase72_real_app_safety_boundary.json`.
- Exported Phase72 APIs from `learning_agent/computer_use/__init__.py`.
- Marked Phase72 complete in `task_plan.md`.
- Marked Phase72 Step 1-4 complete in `docs/superpowers/plans/2026-06-03-phase65-75-humanlike-windows-operator.md`.

## Capability

Phase72 adds the final safety boundary for controlling ordinary real Windows apps. The boundary:

- Allows normal real-app actions only when Phase60 persistent grants approve the current session, app, window/display, and action scope.
- Refuses terminal windows, Codex UI, password/auth/captcha/payment/admin/security/private-data windows, Windows Run, and system management tools by default.
- Blocks approval-bypass hints such as `approval_bypass=True` or stale `previous_approval={"allowed": true}` when no active persistent grant exists.
- Checks a Phase61-compatible abort gate after authorization and immediately before low-level send.
- Returns `low_level_event_count=0` for every refusal path.

## Verification

- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.real_app_safety_boundary'`.
- Focused Phase72 tests passed: 5 OK.
- Phase60/61/72 regression passed: 13 OK.
- `py_compile` passed for `learning_agent/computer_use/real_app_safety_boundary.py`.
- CLI self-check printed:
  `PHASE72_REAL_APP_SAFETY_BOUNDARY_READY PHASE72_REAL_APP_SAFETY_BOUNDARY_OK authorized_real_app_actions=true unauthorized_window_zero_events=true high_risk_default_refusal=true abort_before_low_level_send=true approval_bypass_blocked=true controlled_actions_expansion=true uncontrolled_actions_expanded=false`
- Real visible `start_oauth_agent.bat` terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`.
- Acceptance result:
  `learning_agent/acceptance_controller/runs/agent_capability_phase72_real_app_safety_boundary-20260603_231727/result.json`
- Result JSON showed `completed=true`, `assertion.passed=true`, `final_printed=true`, and `permission_sent_count=0`.

## Boundary

- Phase72 expands only controlled real-app action eligibility.
- Phase72 does not expand uncontrolled actions.
- Phase72 does not directly send real input; it decides whether a downstream sender may proceed.
- Phase72 does not operate terminal, Codex UI, login/auth/captcha/payment/admin/security/private-data, Windows Run, or system management windows.
- Phase72 does not implement app memory, Paint Pikachu E2E, or final Phase75 matrix.

## Next

Next implementation phase is Phase73 App Memory And Self-Learning.
