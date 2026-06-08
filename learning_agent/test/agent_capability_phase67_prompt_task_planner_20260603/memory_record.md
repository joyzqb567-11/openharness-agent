# Phase67 Windows Computer Use Prompt Task Planner

Date: 2026-06-03

Status: completed with TDD red, focused tests, adjacent Phase66/67 regression, compile checks, CLI contract, real visible terminal acceptance, and independent verifier.

## What Changed

- Added `learning_agent/computer_use/prompt_task_planner.py`.
- Added `PHASE67_PROMPT_TASK_PLANNER_READY`.
- Added `PHASE67_PROMPT_TASK_PLANNER_OK`.
- Added `WindowsPromptTaskPlanner.plan(...)`.
- Added `classify_risk(...)`.
- Added `run_phase67_prompt_task_planner_contract(...)`.
- Added `phase67_cli_line(...)`.
- Added `learning_agent/tests/test_windows_computer_use_prompt_task_planner_phase67.py`.
- Added `learning_agent/acceptance_controller/scenarios/agent_capability_phase67_prompt_task_planner.json`.
- Exported Phase67 APIs from `learning_agent/computer_use/__init__.py`.
- Marked Phase67 complete in `task_plan.md`.
- Marked Phase67 Step 1-4 complete in `docs/superpowers/plans/2026-06-03-phase65-75-humanlike-windows-operator.md`.

## Production Meaning

Phase67 creates the deterministic prompt-to-task-plan layer for later closed-loop execution.

It verifies:

- `prompt_task_plan=true`.
- `expected_result_per_step=true`.
- `risk_level_per_step=true`.
- `checkpoint_per_step=true`.
- `paint_pikachu_prompt=true`.
- `high_risk_confirmation=true`.
- `actions_expanded=false`.

## Verification

- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.prompt_task_planner'`.
- Focused Phase67 tests passed: 5 OK.
- Adjacent Phase66/67 regression passed: 8 OK.
- `py_compile` passed for the Phase67 module, package init, and focused test.
- CLI self-check emitted:

```text
PHASE67_PROMPT_TASK_PLANNER_READY PHASE67_PROMPT_TASK_PLANNER_OK prompt_task_plan=true expected_result_per_step=true risk_level_per_step=true checkpoint_per_step=true paint_pikachu_prompt=true high_risk_confirmation=true actions_expanded=false
```

- Real visible `start_oauth_agent.bat` terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`.
- Acceptance result: `learning_agent/acceptance_controller/runs/agent_capability_phase67_prompt_task_planner-20260603_212145/result.json`.
- Independent verifier passed for the same run with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.

## Boundary

- Phase67 does not expand the desktop action surface.
- Phase67 does not call an LLM in unit tests or contract self-checks.
- Phase67 does not launch, click, type, draw, save, or inspect real app windows.
- Paint Pikachu output is a generic task plan, not an app-specific coordinate script.
- High-risk prompts are stopped at `request_user_confirmation` before any real action.
