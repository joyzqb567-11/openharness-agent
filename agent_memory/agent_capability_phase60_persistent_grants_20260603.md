# Phase 60 Persistent Grants Record

## Summary

Phase60 upgrades `/computer` approval UX from a terminal-only grant draft into a persistent, evaluable grant lifecycle. The new store supports app/window/display/action_scope/TTL/reason/grant_flags, explicit deny audit, revoke, status rendering, and default refusal for high-risk system key and clipboard scopes unless explicitly granted.

## Changed Files

- `learning_agent/computer_use/persistent_grants.py`
- `learning_agent/computer_use/__init__.py`
- `learning_agent/app/interactive.py`
- `learning_agent/app/computer_status_renderer.py`
- `learning_agent/tests/test_windows_computer_use_persistent_grants_phase60.py`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase60_persistent_grants.json`
- `task_plan.md`
- `agent_memory/progress.md`
- `agent_memory/bugs.md`
- `agent_memory/context.md`

## Verification

- Focused tests: `python -m unittest learning_agent.tests.test_windows_computer_use_persistent_grants_phase60` passed, 4 OK.
- Adjacent regression: `python -m unittest learning_agent.tests.test_windows_computer_use_approval_phase38 learning_agent.tests.test_windows_computer_use_security_policy_phase48 learning_agent.tests.test_windows_computer_use_terminal_ui_phase51 learning_agent.tests.test_windows_computer_use_session_context_phase59 learning_agent.tests.test_windows_computer_use_persistent_grants_phase60` passed, 21 OK.
- Compile: `python -m py_compile learning_agent\computer_use\persistent_grants.py learning_agent\computer_use\__init__.py learning_agent\app\interactive.py learning_agent\app\computer_status_renderer.py learning_agent\tests\test_windows_computer_use_persistent_grants_phase60.py` passed.
- Scenario JSON: `python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_phase60_persistent_grants.json` passed.
- CLI self-check emitted `PHASE60_WINDOWS_PERSISTENT_GRANTS_READY PHASE60_WINDOWS_PERSISTENT_GRANTS_OK approve=true unauthorized_denied=true expired_denied=true revoked_denied=true high_risk_default=true terminal_status=true actions_expanded=false`.
- Real visible terminal acceptance: `learning_agent/acceptance_controller/runs/agent_capability_phase60_persistent_grants-20260603_182033/result.json`.
- Independent verifier completed true with `permission_sent_count=0`.

## Boundary

Phase60 does not add new real desktop actions. It makes authorization persistent and auditable so Phase61-64 can safely wrap abort hooks, high-level tool APIs, controller takeover, and final parity matrix around a real grant lifecycle.
