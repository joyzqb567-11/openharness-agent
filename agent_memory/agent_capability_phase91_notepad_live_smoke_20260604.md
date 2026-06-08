# Phase91 Controlled Notepad Live Smoke - 2026-06-04

## Status

Completed in safe contract mode.

## What Changed

- Added `learning_agent/computer_use/notepad_live_smoke.py`.
- Added `learning_agent/tests/test_windows_computer_use_notepad_live_smoke_phase91.py`.
- Added `learning_agent/acceptance_controller/scenarios/agent_capability_phase91_notepad_live_smoke.json`.
- Exported Phase91 APIs from `learning_agent/computer_use/__init__.py`.

## Capability

- Phase91 adds a controlled Notepad representative-app smoke runtime.
- The runtime builds a controlled file plan under an isolated root.
- The runtime builds a dedicated Notepad window identity tied to `notepad.exe` and the Phase91 file title hint.
- The default contract reuses the Phase90 dispatcher, Phase60 grants, Phase72 safety boundary, and Phase71 recording input events.
- Unauthorized Notepad and dangerous PowerShell targets stay zero-event refusals.
- Raw text is checked to remain hidden from the structured report.
- A real Notepad smoke path exists only behind `real_smoke=True` plus `LEARNING_AGENT_PHASE91_ENABLE_REAL_NOTEPAD_SMOKE=1`.

## Verification Completed

- TDD red was confirmed first with `ModuleNotFoundError: No module named 'learning_agent.computer_use.notepad_live_smoke'`.
- Focused Phase91 tests passed: 4 OK.
- CLI self-check printed the fixed Phase91 token line.
- Package-level Phase91 import succeeded.
- `py_compile` passed for the Phase91 module and test.
- Phase90 + Phase91 regression passed: 8 OK.
- Windows Computer Use discovery passed: 213 OK.
- `python -m compileall -q learning_agent` passed.
- Real visible `start_oauth_agent.bat` terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`: `learning_agent/acceptance_controller/runs/agent_capability_phase91_notepad_live_smoke-20260604_100730/result.json`.
- Independent result JSON assertion passed with `completed=True`, `assertion_passed=True`, `final_printed=True`, and `permission_sent_count=0`.

## Boundary

- Phase91 does not claim arbitrary control of all Windows apps.
- Phase91 default acceptance does not open real Notepad and does not send real desktop input.
- The real Notepad path is deliberately gated and must be validated separately before it is described as live-control proven.
- This phase proves the controlled Notepad contract, identity plan, authorization integration, refusal behavior, and terminal tokens.

## Next Useful Step

- Consider a Phase92 real Notepad smoke that executes the gated path with user-visible desktop observation and confirms cleanup.
