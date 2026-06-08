# Phase58 Real SendInput Guard Backup

This directory is a learning copy required by the project rules.

## Files

- `real_sendinput_guard.py`: new Phase58 guarded real SendInput runtime.
- `real_uia_locator.py`: modified Phase57 safe-window launcher for configurable Phase58 titles and TextBox focus.
- `windows_backend.py`: modified title normalization so `title_preview` is preferred for drift checks.
- `__init__.py`: modified package exports for Phase58.
- `test_windows_computer_use_real_sendinput_phase58.py`: focused Phase58 tests.
- `agent_capability_phase58_real_sendinput_guard.json`: visible terminal acceptance scenario.
- `result.json`: real visible terminal acceptance result from `agent_capability_phase58_real_sendinput_guard-20260603_175339`.
- `memory_record.md`: phase summary and verification notes.

## Verification Summary

- Focused tests: 4 OK.
- Adjacent regression: 18 OK.
- CLI real smoke: `after_changed=true`, `real_smoke=true`, `actions_expanded=true`.
- Visible terminal acceptance and independent verifier: passed.
