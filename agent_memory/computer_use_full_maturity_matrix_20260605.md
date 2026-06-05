# Computer Use Full Maturity Task 7 Final Matrix

Date: 2026-06-05

Scope:
- Added the final `/computer use --full` maturity matrix.
- Added `/computer maturity` as a read-only terminal command.
- Added maturity preview output to `/computer use --full` before activation.

Key decisions:
- The matrix is a no-desktop-touch aggregation layer, not a new desktop controller.
- Generic maturity is proven by reusable contracts and representative samples, not by adding every installed app to a hardcoded whitelist.
- `visible_terminal_acceptance=true` means the final visible-terminal gate is part of the maturity definition; Task 8 still has to execute it before completion can be claimed.

Verification:
- `python -m unittest learning_agent.tests.test_windows_computer_use_full_maturity_matrix`
- `python -m py_compile learning_agent\computer_use\full_maturity_matrix.py learning_agent\app\interactive.py learning_agent\tests\test_windows_computer_use_full_maturity_matrix.py`
- `python -m unittest learning_agent.tests.test_windows_computer_use_full_maturity_contract learning_agent.tests.test_windows_computer_use_generic_launch_backend_maturity learning_agent.tests.test_windows_computer_use_target_identity_maturity learning_agent.tests.test_windows_computer_use_cleanup_recovery_maturity learning_agent.tests.test_windows_computer_use_interactive_generic_launch_maturity learning_agent.tests.test_windows_computer_use_verified_window_actions_maturity learning_agent.tests.test_windows_computer_use_full_maturity_matrix`

Boundary:
- Task 7 does not complete final visible terminal acceptance.
- Completion still requires Task 8 with `start_oauth_agent.bat` in a real visible terminal.
