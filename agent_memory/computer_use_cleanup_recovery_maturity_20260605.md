# 2026-06-05 Computer Use Full Maturity Task 4 Owned Resource Registry

Status: implemented and automatically verified.

Scope:
- Added `learning_agent/computer_use/owned_resource_registry.py`.
- Added focused tests in `learning_agent/tests/test_windows_computer_use_cleanup_recovery_maturity.py`.
- Updated `learning_agent/computer_use/session_runtime.py` so cleanup/stop and abort paths call owned resource cleanup.

Verified behavior:
- Owned process registration records `session_id`, `process_id`, `created_at`, `cleanup_state`, and `residual_check_state`.
- Owned window registration records `session_id`, `process_id`, `window_id`, `created_at`, `cleanup_state`, and `residual_check_state`.
- Cleanup calls only owned resource callbacks.
- Preexisting user windows are preserved.
- Abort cleanup calls owned resource cleanup.
- Residual check fails when an owned process remains.
- Session runtime `cleanup_turn()` and `request_global_abort()` expose `owned_resource_cleanup_completed`.

Verification commands:
- `python -m py_compile learning_agent\computer_use\owned_resource_registry.py learning_agent\computer_use\session_runtime.py learning_agent\tests\test_windows_computer_use_cleanup_recovery_maturity.py`
- `python -m unittest learning_agent.tests.test_windows_computer_use_cleanup_recovery_maturity`
- `python learning_agent\computer_use\owned_resource_registry.py`
- `python -m unittest learning_agent.tests.test_windows_computer_use_session_runtime_phase40`
- `python -m unittest learning_agent.tests.test_windows_computer_use_recovery_phase50`
- `python -m unittest learning_agent.tests.test_windows_computer_use_cleanup_recovery_maturity learning_agent.tests.test_windows_computer_use_target_identity_maturity`

Boundary:
- Task 4 adds a registry and cleanup/residual state model.
- Task 4 does not expand uncontrolled desktop actions.
