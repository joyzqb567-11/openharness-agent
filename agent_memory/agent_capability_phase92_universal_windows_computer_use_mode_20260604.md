# Phase92 Universal Windows Computer Use Mode

Date: 2026-06-04

Status: implemented and accepted.

## Goal

Phase92 fixes the product direction for Windows Computer Use: the agent should expose one generic prompt-driven Computer Use mode, not one controller per local application.

The runtime is designed around:

- observe
- plan
- act
- verify
- recover

Representative apps such as Notepad, Paint, Explorer, Browser, and Calculator remain acceptance samples only.

## Implemented Files

- `learning_agent/computer_use/universal_mode.py`
- `learning_agent/tests/test_windows_computer_use_universal_mode_phase92.py`
- `learning_agent/computer_use/tool_surface.py`
- `learning_agent/core/agent.py`
- `learning_agent/computer_use/__init__.py`
- `learning_agent/tools/schemas.py`
- `learning_agent/tests/test_windows_computer_use_tool_surface_phase49.py`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase92_universal_windows_computer_use_mode.json`

## Runtime Contract

`UniversalWindowsComputerUseRuntime` composes existing generic layers:

- `WindowsObservationFusionRuntime`
- `WindowsPromptTaskPlanner`
- `WindowsGenericControlActionRuntime`
- `WindowsGenericInputActionRuntime`
- `WindowsRealAppSafetyBoundary`
- `WindowsProductionComputerUseHostAdapter`
- `WindowsComputerUsePersistentGrantStore`

The Phase92 contract prints and verifies:

- `PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_READY`
- `PHASE92_UNIVERSAL_WINDOWS_COMPUTER_USE_OK`
- `single_universal_runtime=true`
- `prompt_to_any_normal_app=true`
- `per_app_controller_required=false`
- `representative_apps_are_acceptance_only=true`
- `generic_observe_plan_act_verify_loop=true`
- `uses_observation_fusion=true`
- `uses_prompt_task_planner=true`
- `uses_generic_action_layer=true`
- `uses_real_app_safety_boundary=true`
- `uses_production_host_adapter=true`
- `high_risk_requires_confirmation=true`
- `unauthorized_window_zero_events=true`
- `target_drift_blocks_action=true`
- `raw_text_hidden=true`
- `default_real_actions_enabled=false`
- `uncontrolled_actions_expanded=false`

## Verification

TDD red evidence:

- Initial Phase92 test failed first with `ModuleNotFoundError: No module named 'learning_agent.computer_use.universal_mode'`.
- After partial implementation, the mode route failed before `tool_surface.py`, `core/agent.py`, and schemas were connected.

Automated verification:

- `python -m unittest learning_agent.tests.test_windows_computer_use_universal_mode_phase92`
  - 4 tests passed.
- `python -m unittest learning_agent.tests.test_windows_computer_use_tool_surface_phase49 learning_agent.tests.test_windows_computer_use_live_app_dispatcher_phase90 learning_agent.tests.test_windows_computer_use_notepad_live_smoke_phase91 learning_agent.tests.test_windows_computer_use_universal_mode_phase92`
  - 16 tests passed.
- `python -m unittest discover -s learning_agent\tests -p "test_windows_computer_use*.py"`
  - 217 tests passed.
- `python -m compileall learning_agent`
  - exit code 0.

Real visible terminal acceptance:

- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase92_universal_windows_computer_use_mode.json`
- Result: `learning_agent/acceptance_controller/runs/agent_capability_phase92_universal_windows_computer_use_mode-20260604_112311/result.json`
- Learning backup: `learning_agent/test/agent_capability_phase92_universal_windows_computer_use_mode_20260604/`
- Backed-up acceptance run: `learning_agent/test/agent_capability_phase92_universal_windows_computer_use_mode_20260604/acceptance_run/result.json`
- Independent result fields:
  - `completed=true`
  - `prompt_sent=true`
  - `prompt_received=true`
  - `final_printed=true`
  - `assertion_passed=true`
  - `permission_sent_count=0`

## Boundary

Phase92 implements the universal Computer Use mode and its safety contract.

It does not claim unrestricted physical control of every Windows app. By design, real desktop actions remain off by default and must pass explicit safety, authorization, target identity, abort, and verification gates.

Future real-app smoke tests should prove they enter through `UniversalWindowsComputerUseRuntime`, not through app-specific shortcuts.
