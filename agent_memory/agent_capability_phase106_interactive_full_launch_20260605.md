# Phase106 Interactive Full Launch

Date: 2026-06-05

Status: completed and accepted.

## Completed

- Added user-facing `/computer launch notepad` command in `learning_agent/app/interactive.py`.
- Added Phase106 marker `PHASE106_INTERACTIVE_FULL_LAUNCH_READY` and OK token `PHASE106_INTERACTIVE_FULL_LAUNCH_OK`.
- Added `_run_phase106_interactive_full_launch()` to bridge the current `ComputerUseModeSessionStore` into `UniversalWindowsLiveExecutionGate`.
- Reused `Phase105ControlledNotepadSmokeLaunchCandidate` so the real path still delegates to Phase104 visible Notepad smoke for unique file, visible-window verification, cleanup, and residual-process checks.
- Added `phase106_main()` to run the full user command sequence: `/computer use --full`, `/computer use --full-confirm <token>`, `/computer launch notepad`, and `/computer stop`.
- Added tests in `learning_agent/tests/test_windows_computer_use_interactive_full_launch_phase106.py`.
- Added visible-terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase106_interactive_full_launch.json`.
- Added learning backup under `learning_agent/test/agent_capability_phase106_interactive_full_launch_20260605/`.

## Verification

- TDD red confirmed first: Phase106 tests failed because `PHASE106_INTERACTIVE_FULL_LAUNCH_MARKER` did not exist in `learning_agent.app.interactive`.
- Phase106 focused tests passed: 3 OK.
- Phase105 + Phase106 adjacent regression passed: 6 OK.
- Compile check passed for `learning_agent/app/interactive.py` and the Phase106 test file.
- Scenario JSON validation passed.
- Default safe `phase106_main()` smoke passed with `controlled_real_launch_gate_passed=false`, `real_full_launch_attempted=false`, and `real_desktop_touched=false`.
- Direct real Phase106 smoke passed with `controlled_real_launch_gate_passed=true`, `real_full_launch_attempted=true`, `visible_window_verified=true`, `cleanup_completed=true`, `verified_window_cleanup_completed=true`, `residual_owned_process=false`, and `real_desktop_touched=true`.
- Real visible `start_oauth_agent.bat` terminal acceptance passed through controller run `learning_agent/acceptance_controller/runs/agent_capability_phase106_interactive_full_launch-20260605_120333/result.json`.
- Independent verifier passed with `completed=true`, `assertion.passed=true`, required screenshots/log/result artifacts present, and `permission_sent_count=0`.
- Post-acceptance process check passed with `notepad_process_count=0`.

## Boundary

- Phase106 proves the real user command path can reach one controlled Notepad real launch after explicit `/computer use --full` and `/computer use --full-confirm`.
- Phase106 still does not mean arbitrary local app launch or unrestricted desktop control.
- Broader application support must be added in later phases with target identity, classification, cleanup, audit evidence, high-risk refusal, and visible terminal acceptance.
