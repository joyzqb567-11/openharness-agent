# Phase94 Authorized Real Dispatch Candidate - 2026-06-04

## Scope

- Phase94 adds `learning_agent/computer_use/authorized_real_dispatch.py`.
- It closes the Phase93 `recording_dispatch_only` gap by adding an authorized low-level dispatch candidate layer.
- It composes Phase60 persistent grants, Phase72 real-app safety boundary, Phase28 static inventory target recheck, and an injected low-level sender.
- The default sender is `Phase94RecordingLowLevelSender`, so the safe contract reaches a low-level sender without physical desktop input.
- Real physical dispatch remains disabled by default and is gated by `LEARNING_AGENT_PHASE94_ENABLE_REAL_DISPATCH`.

## Files

- `learning_agent/computer_use/authorized_real_dispatch.py`
- `learning_agent/tests/test_windows_computer_use_authorized_real_dispatch_phase94.py`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase94_authorized_real_dispatch_candidate.json`
- `learning_agent/computer_use/__init__.py`
- Learning backup: `learning_agent/test/agent_capability_phase94_authorized_real_dispatch_20260604/`

## Verification

- TDD red was confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.authorized_real_dispatch'`.
- Focused Phase94 tests passed: 4 OK.
- Phase93 + Phase94 regression passed: 8 OK.
- Phase90-94 discovery passed: 20 OK.
- Full Windows Computer Use test discovery passed: 225 OK.
- Source compile check passed: `python -m compileall -q learning_agent\computer_use learning_agent\tests`.
- Phase94 CLI contract passed and printed `PHASE94_AUTHORIZED_REAL_DISPATCH_READY PHASE94_AUTHORIZED_REAL_DISPATCH_OK ... uncontrolled_actions_expanded=false`.
- Scenario JSON was validated with `python -m json.tool`.
- Real visible `start_oauth_agent.bat` terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`.
- Passing visible-terminal evidence: `learning_agent/acceptance_controller/runs/agent_capability_phase94_authorized_real_dispatch_candidate-20260604_210234/result.json`.
- The accepted result recorded `completed=true`, `prompt_sent=true`, `prompt_received=true`, `final_printed=true`, `assertion.passed=true`, and `permission_sent_count=0`.

## Boundary

- Phase94 does not claim unrestricted physical control of all Windows apps.
- Phase94 proves that an explicitly authorized, safe, stable target can produce low-level events and reach an injected sender.
- The default contract intentionally keeps `real_dispatch_performed=false`.
- Future physical dispatch work must still preserve explicit authorization, current target identity recheck, high-risk window refusal, abort, cleanup, raw-text hiding, and visible terminal proof.
