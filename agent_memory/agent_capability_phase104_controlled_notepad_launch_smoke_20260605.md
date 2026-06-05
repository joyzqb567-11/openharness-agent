# Phase104 Controlled Notepad Launch Smoke

Date: 2026-06-05

Status: completed and accepted.

## Scope

- Add one controlled real Notepad launch smoke on top of Phase103 controlled app launch.
- Keep real launch default-off.
- Require two explicit environment gates for real desktop touch.
- Verify the visible Notepad window is for a unique controlled project file.
- Clean up the verified controlled window and prove no Phase104 Notepad window remains.

## Files

- `learning_agent/computer_use/controlled_notepad_launch_smoke.py`
- `learning_agent/tests/test_windows_computer_use_controlled_notepad_launch_smoke_phase104.py`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase104_controlled_notepad_launch_smoke.json`
- `learning_agent/test/controlled_notepad_launch_smoke_phase104_20260605/`

## Key Design

- Default mode reports safe contract status and does not open Notepad.
- Real mode requires:
  - `LEARNING_AGENT_PHASE104_RUN_REAL_NOTEPAD_LAUNCH_SMOKE=1`
  - `LEARNING_AGENT_PHASE104_ENABLE_REAL_NOTEPAD_LAUNCH_SMOKE=1`
- Each real run writes a unique controlled file name to prevent stale-window confusion.
- The window probe records startup baseline window keys.
- A visible Notepad window is accepted if it either matches the launch pid or is a new post-launch Notepad window whose title contains the unique controlled file name.
- If the visible window pid differs from the launch pid, Phase104 closes the verified window by exact hwnd/title guard and reports `verified_window_cleanup_completed=true`.

## Verification

- Phase104 focused tests: 5 OK.
- Adjacent regression Phase97/102/103/104: 21 OK.
- Windows Computer Use phase discovery: 282 OK.
- Compile check: passed.
- Default CLI self-check: passed with `real_desktop_touched=false`.
- Direct real CLI smoke: passed with `real_notepad_launch_attempted=true`, `visible_window_verified=true`, `cleanup_completed=true`, `verified_window_cleanup_completed=true`.
- Real visible terminal acceptance:
  - Run: `learning_agent/acceptance_controller/runs/agent_capability_phase104_controlled_notepad_launch_smoke-20260605_110809/result.json`
  - Result: `completed=true`, `prompt_sent=true`, `prompt_received=true`, `final_printed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Independent verifier: passed.
- Post-acceptance window inventory: `phase104_notepad_windows=0`.

## Boundary

- Phase104 proves a controlled Notepad launch smoke only.
- It does not prove unrestricted app launch.
- It does not expand arbitrary window close, arbitrary input, registry changes, system settings changes, or admin behavior.
