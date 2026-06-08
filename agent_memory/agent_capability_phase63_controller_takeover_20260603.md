# Phase 63 Windows Controller Takeover Debug Surface

Date: 2026-06-03

Status: completed.

Scope:
- Added an external agent controller takeover/debug surface for Windows Computer Use.
- The surface can build a `controller.ps1` launch plan, read acceptance run evidence, export evidence packages, and preview `/computer abort <reason>`.
- It does not bypass approval, lock, persistent grants, or visible terminal acceptance.

Files:
- `learning_agent/computer_use/controller_takeover.py`
- `learning_agent/tests/test_windows_computer_use_controller_takeover_phase63.py`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase63_controller_takeover.json`
- `learning_agent/app/interactive.py`
- `learning_agent/app/computer_status_renderer.py`
- `learning_agent/computer_use/__init__.py`

Verification:
- TDD red first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.controller_takeover'`.
- Focused tests: `python -m unittest learning_agent.tests.test_windows_computer_use_controller_takeover_phase63` -> 4 OK.
- Compile check passed for Phase63 module, package init, interactive entry, status renderer, and focused test.
- Scenario JSON validation printed `PHASE63_SCENARIO_JSON_OK`.
- CLI contract printed `PHASE63_WINDOWS_CONTROLLER_TAKEOVER_READY PHASE63_WINDOWS_CONTROLLER_TAKEOVER_OK controller_surface=true launches_visible_terminal=true reads_acceptance_run=true evidence_package=true can_abort=true http_loopback_only=true token_required=true approval_bypass_blocked=true visible_terminal_required=true actions_expanded=false`.
- `/computer controller` displayed the Phase63 marker, visible terminal requirement, controller.ps1 path, start_oauth_agent.bat path, loopback/token boundary, evidence package directory, abort command preview, and `approval_bypass_allowed=false`.
- `/computer status` displayed the `Computer Controller Takeover` section and `/computer controller` command.
- Adjacent regression passed: Phase61 + Phase62 + Phase63 -> 13 OK.
- Real visible terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`: `learning_agent/acceptance_controller/runs/agent_capability_phase63_controller_takeover-20260603_190537/result.json`.
- Independent verifier passed for the same run with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.

Boundary:
- HTTP/stdio control surfaces remain optional and cannot replace visible terminal acceptance.
- Controller takeover cannot write registry, install dependencies, change Windows settings, or expand real desktop actions.
- External agents must still use the same approval, lock, abort, target guard, and evidence chain.
