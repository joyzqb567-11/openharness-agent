# Phase107 Interactive Launch Target Resolver

Date: 2026-06-05

Status: completed and accepted.

## Completed

- Added `learning_agent/computer_use/interactive_launch_target.py`.
- Added Phase107 marker `PHASE107_INTERACTIVE_LAUNCH_TARGET_READY` and OK token `PHASE107_INTERACTIVE_LAUNCH_TARGET_OK`.
- Added `resolve_interactive_launch_target()` to normalize ordinary aliases such as `记事本`, `calc`, `calculator`, `mspaint`, and `paint`.
- Added high-risk target refusal for terminal, shell, registry, settings, admin, credential, and security-related targets.
- Updated `/computer launch <target>` in `learning_agent/app/interactive.py` to use Phase107 target parsing before Phase106/Phase105 launch routing.
- Kept real controlled launch support limited to `notepad`; `calc` and `mspaint` are recognized ordinary targets but remain real-launch default-off.
- Added `phase107_main()` to run a visible-terminal command-path acceptance that confirms full mode, checks `/computer launch calc`, checks `/computer launch powershell`, and stops Computer Use.
- Added focused tests in `learning_agent/tests/test_windows_computer_use_interactive_launch_target_phase107.py`.
- Added visible-terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase107_interactive_launch_target.json`.
- Added learning backup under `learning_agent/test/agent_capability_phase107_interactive_launch_target_20260605/`.

## Verification

- TDD red confirmed first: Phase107 tests failed because `learning_agent.computer_use.interactive_launch_target` did not exist.
- Phase107 focused tests passed: 3 OK.
- Phase106 + Phase107 adjacent regression passed: 6 OK.
- Compile check passed for `learning_agent/app/interactive.py`, `learning_agent/computer_use/interactive_launch_target.py`, and the Phase107 test file.
- Scenario JSON validation passed.
- Direct `phase107_main()` smoke passed with `calc_recognized_default_off=true`, `high_risk_refused=true`, `powershell_zero_side_effect=true`, `real_desktop_touched=false`, and `uncontrolled_actions_expanded=false`.
- Real visible `start_oauth_agent.bat` terminal acceptance passed through controller run `learning_agent/acceptance_controller/runs/agent_capability_phase107_interactive_launch_target-20260605_123842/result.json`.
- Independent verifier passed with `completed=true`, `assertion.passed=true`, required screenshots/log/result artifacts present, and `permission_sent_count=0`.
- Post-acceptance process check found no Notepad, Calculator, or Calc process created by this phase.

## Boundary

- Phase107 proves target parsing and high-risk refusal for the actual `/computer launch <target>` command path.
- Phase107 does not add real launch support for Calculator or Paint yet.
- Phase107 does not mean arbitrary app discovery, arbitrary app launch, arbitrary app input, or unrestricted desktop control.
- Future broader support should add target identity, per-app launch smoke, cleanup, audit evidence, high-risk refusal, and real visible terminal acceptance per app family.
