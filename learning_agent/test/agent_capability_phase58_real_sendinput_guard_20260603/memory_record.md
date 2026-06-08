# Phase58 Real SendInput Target Guard

Date: 2026-06-03

## Scope

- Add the first real Windows SendInput action path for the learning agent.
- Keep the action path narrowly scoped to a dedicated self-owned safe window.
- Prove that forbidden or drifting targets send zero low-level events.
- Prove real `type_text` changes the safe window state through before/after observation.

## Implemented Files

- `learning_agent/computer_use/real_sendinput_guard.py`
- `learning_agent/computer_use/real_uia_locator.py`
- `learning_agent/computer_use/windows_backend.py`
- `learning_agent/computer_use/__init__.py`
- `learning_agent/tests/test_windows_computer_use_real_sendinput_phase58.py`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase58_real_sendinput_guard.json`

## Key Design

- Only `LearningAgent-Phase58-*` windows are allowed.
- Forbidden keywords include terminal, Codex, auth, password, captcha, security, and admin related targets.
- Every action runs target guard, before observe, low-level dispatch, after observe, and sanitized result reporting.
- Text input reports only length and short hash, never raw text.
- Denied targets return before low-level event construction.

## Important Fix

The first real smoke showed mouse and foreground events succeeded, but Unicode text events returned 0 and the TextBox state did not change.

Root cause: the keyboard `SendInput` path declared a union containing only `KEYBDINPUT`, so the INPUT structure size was too small on 64-bit Windows.

Fix: declare the full union size by including the mouse branch alongside the keyboard branch.

## Verification

- Focused Phase58 tests: 4 OK.
- Phase28/47/57/58 adjacent regression: 18 OK.
- `py_compile` passed for Phase58 related files.
- Scenario JSON validation passed.
- CLI real smoke passed with:

```text
PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_READY PHASE58_WINDOWS_REAL_SENDINPUT_GUARD_OK target_guard=true low_level_events=true forbidden_zero_events=true before_after=true after_changed=true raw_text_hidden=true safe_window_only=true real_smoke=true actions_expanded=true
```

- Real visible terminal acceptance:

```text
learning_agent/acceptance_controller/runs/agent_capability_phase58_real_sendinput_guard-20260603_175339/result.json
```

- Independent verifier passed with `completed=true` and `assertion.passed=true`.

## Boundary

Phase58 does not grant broad desktop control. It proves tightly guarded real input inside a self-owned safe window only.
