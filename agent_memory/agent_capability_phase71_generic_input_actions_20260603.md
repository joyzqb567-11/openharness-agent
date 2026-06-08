# 2026-06-03 Phase71 Generic Input Actions

Status: completed.

## Scope

- Added `learning_agent/computer_use/generic_input_actions.py`.
- Added `learning_agent/tests/test_windows_computer_use_generic_input_actions_phase71.py`.
- Added `learning_agent/acceptance_controller/scenarios/agent_capability_phase71_generic_input_actions.json`.
- Exported Phase71 APIs from `learning_agent/computer_use/__init__.py`.
- Updated `task_plan.md`.
- Updated `docs/superpowers/plans/2026-06-03-phase65-75-humanlike-windows-operator.md`.

## Capability

- `build_hotkey_events(...)` creates ordered `key_down` and reverse `key_up` events.
- `build_menu_sequence(...)` creates `menu_open`, `menu_item`, and `menu_commit` events.
- `build_scroll_events(...)` creates a `mouse_move` followed by `mouse_wheel`.
- `build_drag_path(...)` creates a continuous mouse path with `mouse_move`, `mouse_down`, intermediate moves, and `mouse_up`.
- `WindowsGenericInputActionRuntime` records hotkey, menu, scroll, and drag actions through `Phase71RecordingInputSender`.
- All Phase71 events carry `real_dispatch_allowed=false`; real dispatch remains gated by Phase72.
- Forbidden system hotkeys return zero-event refusal: `ctrl+alt+delete`, `win+r`, `win+x`, `ctrl+shift+esc`, and any Windows-key combo.

## Verification

- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.generic_input_actions'`.
- Focused Phase71 tests passed: 5 OK.
- Phase70/71 regression passed: 10 OK.
- Phase68/69/70/71 regression passed: 19 OK.
- Phase58/62/71 regression passed: 14 OK.
- `py_compile` passed for the Phase71 module, package init, and focused test.
- CLI self-check printed: `PHASE71_GENERIC_INPUT_ACTIONS_READY PHASE71_GENERIC_INPUT_ACTIONS_OK hotkey_action=true menu_navigation=true scroll_action=true drag_action=true continuous_mouse_path=true forbidden_system_hotkeys_blocked=true actions_expanded=false`.
- Real visible `start_oauth_agent.bat` terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`: `learning_agent/acceptance_controller/runs/agent_capability_phase71_generic_input_actions-20260603_230243/result.json`.
- Result JSON independent assertion passed with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.

## Boundary

- Phase71 does not send real keyboard or mouse input.
- Phase71 does not authorize real app control.
- Phase71 does not draw in Paint; it only builds continuous drag event paths needed by later real-app phases.
- Next implementation phase is Phase72 real-app safety boundary.
