# Phase 57 Real UIA Control Tree And Semantic Locator

## Goal

Phase57 upgrades Windows Computer Use UIA from a contract or placeholder layer to a real, bounded, safe-window UIAutomationClient path with semantic locator output.

## Delivered

- Added `learning_agent/computer_use/real_uia_locator.py`.
- Added PowerShell/.NET UIAutomationClient probing and tree reading.
- Added dedicated temporary WinForms safe window smoke target with unique exact-title matching.
- Added sanitized UIA node normalization for name, role, automation_id, class_name, bounds, enabled, clickable, and editable.
- Added semantic locator output with `matched`, `candidate_count`, `confidence`, `reason`, and `control`.
- Integrated `WindowsNativeHelperV2Worker.read_uia_tree` with `WindowsRealUiaLocatorRuntime`.
- Added focused tests and a real visible terminal acceptance scenario.

## Verification Evidence

- TDD red: `ModuleNotFoundError: No module named 'learning_agent.computer_use.real_uia_locator'`.
- Focused test: `python -m unittest learning_agent.tests.test_windows_computer_use_real_uia_locator_phase57` produced 5 tests OK.
- Adjacent regression: `python -m unittest learning_agent.tests.test_windows_computer_use_native_helper_v2_phase55 learning_agent.tests.test_windows_computer_use_real_screenshot_phase56 learning_agent.tests.test_windows_computer_use_real_uia_locator_phase57` produced 13 tests OK.
- Compile check: `python -m py_compile learning_agent/computer_use/real_uia_locator.py learning_agent/computer_use/native_helper_v2.py learning_agent/computer_use/__init__.py learning_agent/tests/test_windows_computer_use_real_uia_locator_phase57.py` exited 0.
- CLI real smoke printed `PHASE57_WINDOWS_REAL_UIA_LOCATOR_OK real_uia_tree=true semantic_locator=true helper_v2_uia=true safe_window_only=true real_smoke=true raw_text_hidden=true actions_expanded=false marker=PHASE57_WINDOWS_REAL_UIA_LOCATOR_READY`.
- Real visible terminal acceptance: `learning_agent/acceptance_controller/runs/agent_capability_phase57_real_uia_locator-20260603_173235/result.json`.
- Independent verifier passed for the same run with `completed=true` and `assertion.passed=true`.

## Safety Boundary

- Phase57 is read-only.
- Phase57 does not click, type, move the mouse, change registry, install dependencies, or change Windows settings.
- Raw UIA text is not included in helper v2 summary.
- The next write phase is Phase58 and must require target guard, before/after observe, redacted text audit, and zero low-level events on forbidden targets.
