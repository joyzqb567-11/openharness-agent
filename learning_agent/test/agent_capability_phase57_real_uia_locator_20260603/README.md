# Phase 57 Real UIA Locator Learning Backup

This folder stores the Phase57 code, tests, scenario, and visible-terminal acceptance result copied for learning and later review.

Files:
- `real_uia_locator.py`: Phase57 real PowerShell/.NET UIA tree provider, safe-window smoke runtime, and semantic locator.
- `native_helper_v2.py`: helper v2 integration copy showing how `read_uia_tree` delegates to Phase57.
- `__init__.py`: package export copy for Phase57 public symbols.
- `test_windows_computer_use_real_uia_locator_phase57.py`: focused Phase57 TDD test file.
- `agent_capability_phase57_real_uia_locator.json`: visible terminal acceptance scenario.
- `result.json`: successful visible terminal acceptance evidence from `agent_capability_phase57_real_uia_locator-20260603_173235`.

Safety note:
- Phase57 is read-only UIA observation and semantic location only.
- It does not click, type, move the mouse, install dependencies, write registry, or change Windows settings.
