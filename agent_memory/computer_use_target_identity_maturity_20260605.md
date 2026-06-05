# 2026-06-05 Computer Use Full Maturity Task 3 Target Identity Binding

Status: implemented and automatically verified.

Scope:
- Added `learning_agent/computer_use/target_identity.py`.
- Added focused tests in `learning_agent/tests/test_windows_computer_use_target_identity_maturity.py`.
- Updated `learning_agent/computer_use/windows_backend.py` to emit `hwnd`, `window_process_id`, `title_sha256_16`, `process_path_sha256_16`, and `target_identity_candidate`.
- Updated `learning_agent/computer_use/generic_real_launch_candidate.py` to use structured target identity verification and expose `target_drift_blocks_action`.

Verified behavior:
- pid is bound to hwnd.
- process path is hashed and raw local path is not exposed in reports.
- long window titles are summarized and full titles are represented by short hashes.
- target drift blocks action.
- same title from a different pid is not accepted.
- preexisting same-app user windows are preserved and are not accepted as owned targets.
- Phase109 stable candidate path now emits `target_drift_blocks_action=false`.

Verification commands:
- `python -m py_compile learning_agent\computer_use\target_identity.py learning_agent\computer_use\windows_backend.py learning_agent\computer_use\generic_real_launch_candidate.py learning_agent\tests\test_windows_computer_use_target_identity_maturity.py`
- `python -m unittest learning_agent.tests.test_windows_computer_use_target_identity_maturity`
- `python -m unittest learning_agent.tests.test_windows_computer_use_generic_real_launch_candidate_phase109`
- `python -m unittest learning_agent.tests.test_windows_computer_use_generic_launch_backend_maturity`
- `python -m unittest learning_agent.tests.test_windows_computer_use_full_maturity_contract`
- `python -m unittest learning_agent.tests.test_windows_computer_use_inventory_phase28`
- `python -m unittest learning_agent.tests.test_windows_computer_use_observe_phase29`
- `python -m unittest learning_agent.tests.test_windows_computer_use_coordinates_phase39`
- `python learning_agent\computer_use\target_identity.py`

Boundary:
- Task 3 adds identity records and drift blocking evidence only.
- Task 3 still does not expand uncontrolled desktop actions.
