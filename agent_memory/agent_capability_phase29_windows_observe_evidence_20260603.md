# Phase 29 Windows Computer Use Observe Evidence

## Goal

Add a read-only evidence chain for `computer_observe/get_window_state`: screenshot artifact path, metadata artifact path, bounded accessibility excerpt, and helper status, without expanding real mouse or keyboard actions.

## Completed

- Added `learning_agent/computer_use/evidence.py`.
- Added `learning_agent/computer_use/helper_client.py`.
- Extended `WindowsComputerUseBackend` to save window-state evidence in `get_window_state`.
- Exported Phase 29 helper and evidence types from `learning_agent/computer_use/__init__.py`.
- Added TDD tests in `learning_agent/tests/test_windows_computer_use_observe_phase29.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase29_windows_observe_evidence.json`.

## Verification

- Red test observed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.evidence'`.
- Focused Phase 29 tests: `python -m unittest learning_agent.tests.test_windows_computer_use_observe_phase29`, 3 tests OK.
- Phase 28/29 combined tests: 8 tests OK.
- Phase 29 + Phase 28 + Phase 27 + Phase 20 regression: 15 tests OK.
- `py_compile` passed for Phase 29 source and test files.
- Scenario JSON validation passed.
- Full regression: `python -m unittest discover -s learning_agent\tests`, 625 tests OK, skipped=1.
- Real visible terminal acceptance passed: `learning_agent/acceptance_controller/runs/agent_capability_phase29_windows_observe_evidence-20260603_062659/result.json`.
- Independent verifier passed for the same run.
- Evidence artifact check passed under `learning_agent/memory/computer_use/evidence_phase29_acceptance/`.

## Boundary

Phase 29 adds the evidence store and helper contract. The visible acceptance uses a static safe helper so the terminal test can prove artifact writing and UIA filtering without reading a real sensitive desktop window. The default helper still reports that native Windows screenshot/UI Automation capture is not configured. A future phase should add a real Windows native helper for Windows.Graphics.Capture and UIAutomationClient.

## Next Recommendation

Phase 30 should not jump straight to broad mouse/keyboard control. It should first add a durable computer-use lock, abort flag, and action evidence envelope, then add one narrow window-relative action against a safe test app.
