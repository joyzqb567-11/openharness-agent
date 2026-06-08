# Phase 41 Windows Image Results

## Status

Completed on 2026-06-03.

## What Changed

- Added Phase41 image result protocol constants and helpers in `learning_agent/computer_use/evidence.py`.
- `ComputerUseEvidenceStore.save_window_state(...)` now returns `image_results` and `image_result_count`, and writes the same safe image result metadata to the evidence JSON.
- `ComputerUseActionResult.to_text(...)` now appends a short `Computer Use Image Results` block whenever result data contains image_result blocks.
- `WindowsComputerUseBackend.get_window_state` now exposes image results at both `state.image_results` and top-level `data.image_results`.
- `LearningAgent._computer_observe(...)` and `_computer_action(...)` now register Computer Use screenshot artifact paths into `active_artifacts`.
- Added Phase41 focused tests and visible terminal scenario.

## Verification

- Red test first failed as expected because `PHASE41_IMAGE_RESULT_MODEL` and related evidence helpers did not exist.
- Focused test passed: `python -m unittest learning_agent.tests.test_windows_computer_use_image_results_phase41`, 4 tests OK.
- Syntax check passed: `python -m py_compile` for Phase41 touched Python files.
- CLI selftest passed: `PHASE41_WINDOWS_IMAGE_RESULTS_READY PHASE41_WINDOWS_IMAGE_RESULTS_OK artifact=true image_block=true agent_artifact=true sensitive_text_hidden=true actions_expanded=false`.
- Scenario JSON validated with `python -m json.tool`.
- Windows Computer Use regression passed: `python -m unittest discover -s .\learning_agent\tests -p "test_windows_computer_use_*.py"`, 70 tests OK.
- Full regression passed: `python -m unittest discover -s .\learning_agent\tests`, 683 tests OK, skipped=1.
- Real visible terminal acceptance passed through `learning_agent/start_oauth_agent.bat`: `learning_agent/acceptance_controller/runs/agent_capability_phase41_windows_image_results-20260603_114516`.
- Independent verifier replay passed with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.

## Safety Boundary

- Phase41 does not add or expand real desktop actions.
- `actions_expanded=false` remains part of the CLI and terminal acceptance marker.
- Image result blocks intentionally exclude raw UIA text and carry `sensitive_text_included=false`.
- Sensitive UIA test value `phase41-secret-must-not-leak` is checked across direct evidence blocks, controller result text, and agent output.

## Next Step

Proceed to Phase42 final Windows Computer Use E2E matrix.
