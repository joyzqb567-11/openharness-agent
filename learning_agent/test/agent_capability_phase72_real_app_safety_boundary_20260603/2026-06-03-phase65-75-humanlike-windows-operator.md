# Phase65-75 Humanlike Windows Operator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-oriented Windows Computer Use layer that can operate normal user-authorized desktop applications through a humanlike observe, plan, act, verify, and recover loop.

**Architecture:** Reuse the existing Phase56-64 screenshot, UIA, SendInput, persistent grant, abort, high-level tool, controller, and matrix chain. Add focused modules for universal operator contracts, fused observation, prompt planning, closed-loop execution, app launch/focus, generic actions, real-app safety, app memory, representative E2E, and final matrix.

**Tech Stack:** Python standard library, `unittest`, existing `learning_agent.computer_use` modules, PowerShell/Win32 helpers already present in the repo, `learning_agent/acceptance_controller/controller.ps1`, and real visible `learning_agent/start_oauth_agent.bat` acceptance.

---

## Scope Lock

This plan implements the approved blueprint in `docs/superpowers/specs/2026-06-03-humanlike-windows-operator-blueprint.md`.

It must not install OCR, vision, drivers, global hooks, or system services without a separate user confirmation.

It must not write registry keys, change Windows settings, change UAC, change security policies, or operate real user private data.

It must keep high-risk windows blocked by default: password, payment, login, authentication, captcha, administrator, security, terminal, Codex UI, and private-data surfaces.

It must keep the final acceptance gate honest: automated tests and CLI self-checks do not replace `learning_agent/start_oauth_agent.bat` visible terminal interaction.

## File Structure

New production modules:
- `learning_agent/computer_use/humanlike_operator_contract.py`: Phase65 universal contract and stable token surface.
- `learning_agent/computer_use/observation_fusion.py`: Phase66 fused observation object from screenshot, UIA, inventory, OCR/vision slot, and safe metadata.
- `learning_agent/computer_use/prompt_task_planner.py`: Phase67 prompt-to-steps planner with expected results, risk levels, and checkpoints.
- `learning_agent/computer_use/closed_loop_executor.py`: Phase68 observe-decide-act-observe-verify-recover runtime with injected dependencies.
- `learning_agent/computer_use/app_window_control.py`: Phase69 app launch, focus, target identity, and target drift helpers.
- `learning_agent/computer_use/generic_control_actions.py`: Phase70 generic click/type/control action wrapper over existing locator and high-level tools.
- `learning_agent/computer_use/generic_input_actions.py`: Phase71 hotkey, menu, scroll, drag, and continuous mouse path event builder.
- `learning_agent/computer_use/real_app_safety_boundary.py`: Phase72 user-authorized real app window policy and zero-event refusal runtime.
- `learning_agent/computer_use/app_memory.py`: Phase73 non-secret app memory, revoke, and audit store.
- `learning_agent/computer_use/representative_e2e_matrix.py`: Phase74 Notepad, Explorer, Browser, window-style app, and Paint Pikachu representative matrix.
- `learning_agent/computer_use/humanlike_operator_matrix.py`: Phase75 final rollup matrix for Phase65-74.

Existing files to modify:
- `learning_agent/computer_use/__init__.py`: export public Phase65-75 APIs.
- `learning_agent/app/interactive.py`: add `/computer humanlike`, `/computer observation-fusion`, `/computer app-memory`, and final matrix status commands as phases land.
- `learning_agent/app/computer_status_renderer.py`: render concise Phase65-75 status sections.
- `task_plan.md`: mark each phase as it is completed.
- `agent_memory/context.md`, `agent_memory/progress.md`, `agent_memory/bugs.md`: maintain long-task memory.

New focused tests:
- `learning_agent/tests/test_windows_computer_use_humanlike_operator_phase65.py`
- `learning_agent/tests/test_windows_computer_use_observation_fusion_phase66.py`
- `learning_agent/tests/test_windows_computer_use_prompt_task_planner_phase67.py`
- `learning_agent/tests/test_windows_computer_use_closed_loop_executor_phase68.py`
- `learning_agent/tests/test_windows_computer_use_app_window_control_phase69.py`
- `learning_agent/tests/test_windows_computer_use_generic_control_actions_phase70.py`
- `learning_agent/tests/test_windows_computer_use_generic_input_actions_phase71.py`
- `learning_agent/tests/test_windows_computer_use_real_app_safety_boundary_phase72.py`
- `learning_agent/tests/test_windows_computer_use_app_memory_phase73.py`
- `learning_agent/tests/test_windows_computer_use_representative_e2e_phase74.py`
- `learning_agent/tests/test_windows_computer_use_humanlike_operator_matrix_phase75.py`

New visible terminal scenarios:
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase65_humanlike_operator_contract.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase66_observation_fusion.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase67_prompt_task_planner.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase68_closed_loop_executor.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase69_app_window_control.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase70_generic_control_actions.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase71_generic_input_actions.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase72_real_app_safety_boundary.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase73_app_memory.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase74_representative_e2e.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase75_humanlike_operator_matrix.json`

Backups:
- Each phase copies changed code, tests, scenario JSON, memory records, and acceptance evidence to `learning_agent/test/agent_capability_phaseNN_<name>_20260603/`.

---

## Task 1: Phase65 Universal Operator Contract

**Files:**
- Create: `learning_agent/computer_use/humanlike_operator_contract.py`
- Create: `learning_agent/tests/test_windows_computer_use_humanlike_operator_phase65.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase65_humanlike_operator_contract.json`
- Modify: `learning_agent/computer_use/__init__.py`
- Modify: `task_plan.md`
- Modify: `agent_memory/context.md`, `agent_memory/progress.md`, `agent_memory/bugs.md`
- Backup: `learning_agent/test/agent_capability_phase65_humanlike_operator_contract_20260603/`

- [x] **Step 1: Write the failing test**

Test content must import:

```python
from learning_agent.computer_use.humanlike_operator_contract import PHASE65_HUMANLIKE_OPERATOR_MARKER, PHASE65_HUMANLIKE_OPERATOR_OK_TOKEN, phase65_cli_line, run_phase65_humanlike_operator_contract
```

Test assertions:

```python
report = run_phase65_humanlike_operator_contract()
self.assertTrue(report["humanlike_operator_contract"])
self.assertTrue(report["prompt_to_normal_windows_app"])
self.assertFalse(report["per_app_scripts_required"])
self.assertTrue(report["high_risk_confirmation_required"])
self.assertTrue(report["direct_file_cheat_blocked"])
self.assertFalse(report["actions_expanded"])
self.assertIn("PHASE65_HUMANLIKE_OPERATOR_READY", phase65_cli_line(report))
```

- [x] **Step 2: Run the red test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_humanlike_operator_phase65
```

Expected: fail with `ModuleNotFoundError: No module named 'learning_agent.computer_use.humanlike_operator_contract'`.

- [x] **Step 3: Implement the Phase65 module**

Implement constants:

```python
PHASE65_HUMANLIKE_OPERATOR_MARKER = "PHASE65_HUMANLIKE_OPERATOR_READY"
PHASE65_HUMANLIKE_OPERATOR_OK_TOKEN = "PHASE65_HUMANLIKE_OPERATOR_OK"
PHASE65_HUMANLIKE_OPERATOR_MODEL = "phase65_humanlike_windows_operator_contract"
PHASE65_ACTIONS_EXPANDED = False
```

Implement:
- `run_phase65_humanlike_operator_contract() -> dict[str, Any]`
- `phase65_cli_line(report: dict[str, Any]) -> str`
- `main(argv: list[str] | None = None) -> int`

Required CLI line:

```text
PHASE65_HUMANLIKE_OPERATOR_READY PHASE65_HUMANLIKE_OPERATOR_OK humanlike_operator_contract=true prompt_to_normal_windows_app=true per_app_scripts_required=false high_risk_confirmation_required=true direct_file_cheat_blocked=true actions_expanded=false
```

- [x] **Step 4: Export and scenario**

Add Phase65 exports to `learning_agent/computer_use/__init__.py`.

Create scenario command:

```powershell
$env:PYTHONPATH='..'; python -c "from learning_agent.computer_use.humanlike_operator_contract import main; raise SystemExit(main())"
```

- [x] **Step 5: Verify Phase65**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_humanlike_operator_phase65
python -m py_compile learning_agent\computer_use\humanlike_operator_contract.py learning_agent\tests\test_windows_computer_use_humanlike_operator_phase65.py
python -c "from learning_agent.computer_use.humanlike_operator_contract import main; raise SystemExit(main())"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_phase65_humanlike_operator_contract.json
```

Expected: focused tests pass, compile exits 0, CLI emits Phase65 token, visible terminal controller run completes with assertion passed.

---

## Task 2: Phase66 Observation Fusion

**Files:**
- Create: `learning_agent/computer_use/observation_fusion.py`
- Create: `learning_agent/tests/test_windows_computer_use_observation_fusion_phase66.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase66_observation_fusion.json`
- Modify: `learning_agent/computer_use/__init__.py`
- Backup: `learning_agent/test/agent_capability_phase66_observation_fusion_20260603/`

- [x] **Step 1: Write the failing test**

Test imports:

```python
from learning_agent.computer_use.observation_fusion import PHASE66_OBSERVATION_FUSION_MARKER, phase66_cli_line, run_phase66_observation_fusion_contract
```

Test assertions:

```python
report = run_phase66_observation_fusion_contract()
self.assertTrue(report["screenshot_observation"])
self.assertTrue(report["uia_tree_observation"])
self.assertTrue(report["ocr_or_vision_slot"])
self.assertTrue(report["window_state_observation"])
self.assertTrue(report["sensitive_text_boundary"])
self.assertFalse(report["actions_expanded"])
self.assertIn("uia_ocr_vision_fusion=true", phase66_cli_line(report))
```

- [x] **Step 2: Run the red test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_observation_fusion_phase66
```

Expected: fail because `observation_fusion.py` is missing.

- [x] **Step 3: Implement fused observation**

Implement:
- `FusedComputerObservation` dictionary contract.
- `WindowsObservationFusionRuntime.observe(window, screenshot_result, uia_result, inventory_result, ocr_result=None)`.
- `run_phase66_observation_fusion_contract(real_smoke: bool = False)`.

Required behavior:
- Use injected fake screenshot and UIA results in tests.
- Keep `ocr_or_vision_slot=true` even when provider is unavailable.
- Return `ocr_provider_available=false` and `ocr_install_attempted=false` unless dependencies already exist and are explicitly enabled.
- Return `raw_text_included=false`.
- Keep `actions_expanded=false`.

Required CLI line:

```text
PHASE66_OBSERVATION_FUSION_READY PHASE66_OBSERVATION_FUSION_OK screenshot_observation=true uia_tree_observation=true ocr_or_vision_slot=true window_state_observation=true sensitive_text_boundary=true uia_ocr_vision_fusion=true actions_expanded=false
```

- [x] **Step 4: Verify Phase66**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_observation_fusion_phase66
python -m unittest learning_agent.tests.test_windows_computer_use_real_screenshot_phase56 learning_agent.tests.test_windows_computer_use_real_uia_locator_phase57 learning_agent.tests.test_windows_computer_use_observation_fusion_phase66
python -m py_compile learning_agent\computer_use\observation_fusion.py learning_agent\tests\test_windows_computer_use_observation_fusion_phase66.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_phase66_observation_fusion.json
```

Expected: all listed checks pass and no dependency installation occurs.

---

## Task 3: Phase67 Prompt Task Planner

**Files:**
- Create: `learning_agent/computer_use/prompt_task_planner.py`
- Create: `learning_agent/tests/test_windows_computer_use_prompt_task_planner_phase67.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase67_prompt_task_planner.json`
- Modify: `learning_agent/computer_use/__init__.py`
- Backup: `learning_agent/test/agent_capability_phase67_prompt_task_planner_20260603/`

- [x] **Step 1: Write the failing test**

Test imports:

```python
from learning_agent.computer_use.prompt_task_planner import WindowsPromptTaskPlanner, phase67_cli_line, run_phase67_prompt_task_planner_contract
```

Test scenarios:
- Notepad prompt produces launch, type, save, verify steps.
- Paint Pikachu prompt produces launch paint, identify canvas, select colors/tools, draw elements, save, verify steps.
- Password/payment/admin prompt is classified as high risk and requires confirmation.

Example assertion:

```python
plan = WindowsPromptTaskPlanner().plan("打开画图软件，画一个简化皮卡丘并保存")
self.assertEqual(plan["app"], "mspaint")
self.assertTrue(plan["prompt_task_plan"])
self.assertTrue(all("expected_result" in step for step in plan["steps"]))
self.assertTrue(all("risk_level" in step for step in plan["steps"]))
self.assertTrue(all("checkpoint" in step for step in plan["steps"]))
self.assertTrue(plan["representative_scenario"])
self.assertFalse(plan["per_app_script"])
```

- [x] **Step 2: Run the red test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_prompt_task_planner_phase67
```

Expected: fail because planner module is missing.

- [x] **Step 3: Implement planner**

Implement:
- `WindowsPromptTaskPlanner.plan(prompt: str) -> dict[str, Any]`
- `classify_risk(prompt: str) -> dict[str, Any]`
- `run_phase67_prompt_task_planner_contract()`
- `phase67_cli_line(report)`

The planner is deterministic and rule-based for contract tests. It must not call an LLM inside unit tests.

Required CLI line:

```text
PHASE67_PROMPT_TASK_PLANNER_READY PHASE67_PROMPT_TASK_PLANNER_OK prompt_task_plan=true expected_result_per_step=true risk_level_per_step=true checkpoint_per_step=true paint_pikachu_prompt=true high_risk_confirmation=true actions_expanded=false
```

- [x] **Step 4: Verify Phase67**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_prompt_task_planner_phase67
python -m py_compile learning_agent\computer_use\prompt_task_planner.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_phase67_prompt_task_planner.json
```

Expected: planner contract passes and Paint prompt is represented without app-specific controller code.

---

## Task 4: Phase68 Closed-Loop Executor

**Files:**
- Create: `learning_agent/computer_use/closed_loop_executor.py`
- Create: `learning_agent/tests/test_windows_computer_use_closed_loop_executor_phase68.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase68_closed_loop_executor.json`
- Modify: `learning_agent/computer_use/__init__.py`
- Backup: `learning_agent/test/agent_capability_phase68_closed_loop_executor_20260603/`

- [x] **Step 1: Write the failing test**

Test imports:

```python
from learning_agent.computer_use.closed_loop_executor import WindowsClosedLoopComputerExecutor, phase68_cli_line, run_phase68_closed_loop_executor_contract
```

Test a fake environment:

```python
report = run_phase68_closed_loop_executor_contract()
self.assertTrue(report["closed_loop_execution"])
self.assertTrue(report["post_action_verification"])
self.assertTrue(report["failure_recovery"])
self.assertTrue(report["blind_coordinate_chain_blocked"])
self.assertFalse(report["actions_expanded"])
```

- [x] **Step 2: Run the red test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_closed_loop_executor_phase68
```

Expected: fail because executor module is missing.

- [x] **Step 3: Implement executor**

Implement:
- `WindowsClosedLoopComputerExecutor.run(task_plan, observer, actor, verifier, recoverer, max_steps=12)`.
- Enforce one observation before every action.
- Enforce one verification after every write action.
- Reject action sequences that contain two write actions without an intervening observation.
- Record loop events: `observed`, `decided`, `acted`, `verified`, `recovered`, `stopped`.

Required CLI line:

```text
PHASE68_CLOSED_LOOP_EXECUTOR_READY PHASE68_CLOSED_LOOP_EXECUTOR_OK closed_loop_execution=true post_action_verification=true failure_recovery=true blind_coordinate_chain_blocked=true actions_expanded=false
```

- [x] **Step 4: Verify Phase68**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_closed_loop_executor_phase68
python -m unittest learning_agent.tests.test_windows_computer_use_prompt_task_planner_phase67 learning_agent.tests.test_windows_computer_use_closed_loop_executor_phase68
python -m py_compile learning_agent\computer_use\closed_loop_executor.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_phase68_closed_loop_executor.json
```

Expected: fake closed-loop scenario demonstrates recovery and blocked blind action chain.

---

## Task 5: Phase69 App Launch, Focus, And Window Switching

**Files:**
- Create: `learning_agent/computer_use/app_window_control.py`
- Create: `learning_agent/tests/test_windows_computer_use_app_window_control_phase69.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase69_app_window_control.json`
- Modify: `learning_agent/computer_use/__init__.py`
- Backup: `learning_agent/test/agent_capability_phase69_app_window_control_20260603/`

- [x] **Step 1: Write the failing test**

Test imports:

```python
from learning_agent.computer_use.app_window_control import WindowsAppWindowControlRuntime, phase69_cli_line, run_phase69_app_window_control_contract
```

Test assertions:

```python
report = run_phase69_app_window_control_contract(real_smoke=False)
self.assertTrue(report["app_launch"])
self.assertTrue(report["window_focus"])
self.assertTrue(report["target_window_identity"])
self.assertTrue(report["target_drift_blocked"])
self.assertFalse(report["actions_expanded"])
```

- [x] **Step 2: Run the red test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_app_window_control_phase69
```

Expected: fail because app window control module is missing.

- [x] **Step 3: Implement app/window control**

Implement:
- `build_launch_plan(app_name: str, test_file: str | None = None)`.
- `WindowsAppWindowControlRuntime.launch_app(plan)`.
- `WindowsAppWindowControlRuntime.focus_window(window)`.
- `WindowsAppWindowControlRuntime.verify_target_identity(before, after)`.
- Recording launcher for tests.
- Production launcher must use safe commands like `Start-Process` and never change system settings.

Required CLI line:

```text
PHASE69_APP_WINDOW_CONTROL_READY PHASE69_APP_WINDOW_CONTROL_OK app_launch=true window_focus=true target_window_identity=true target_drift_blocked=true actions_expanded=false
```

- [x] **Step 4: Verify Phase69**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_app_window_control_phase69
python -m py_compile learning_agent\computer_use\app_window_control.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_phase69_app_window_control.json
```

Expected: contract passes with recording launcher and no broad desktop writes.

---

## Task 6: Phase70 Generic Click, Type, And Control Actions

**Files:**
- Create: `learning_agent/computer_use/generic_control_actions.py`
- Create: `learning_agent/tests/test_windows_computer_use_generic_control_actions_phase70.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase70_generic_control_actions.json`
- Modify: `learning_agent/computer_use/__init__.py`
- Backup: `learning_agent/test/agent_capability_phase70_generic_control_actions_20260603/`

- [x] **Step 1: Write the failing test**

Test imports:

```python
from learning_agent.computer_use.generic_control_actions import WindowsGenericControlActionRuntime, phase70_cli_line, run_phase70_generic_control_actions_contract
```

Assertions:

```python
report = run_phase70_generic_control_actions_contract()
self.assertTrue(report["generic_click"])
self.assertTrue(report["generic_type"])
self.assertTrue(report["control_locator"])
self.assertTrue(report["visual_fallback"])
self.assertTrue(report["before_after_evidence"])
self.assertFalse(report["actions_expanded"])
```

- [x] **Step 2: Run the red test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_generic_control_actions_phase70
```

Expected: fail because generic control action module is missing.

- [x] **Step 3: Implement generic control runtime**

Implement:
- `click_by_query(window, observation, query)`.
- `type_by_query(window, observation, query, text)`.
- `click_by_visual_point(window, point, reason)`.
- Use Phase57 locator for UIA controls.
- Use Phase62 high-level tools for click/type.
- Return before/after fingerprints and zero-event refusal on missing target.

Required CLI line:

```text
PHASE70_GENERIC_CONTROL_ACTIONS_READY PHASE70_GENERIC_CONTROL_ACTIONS_OK generic_click=true generic_type=true control_locator=true visual_fallback=true before_after_evidence=true zero_event_refusal=true actions_expanded=false
```

- [x] **Step 4: Verify Phase70**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_generic_control_actions_phase70
python -m unittest learning_agent.tests.test_windows_computer_use_real_uia_locator_phase57 learning_agent.tests.test_windows_computer_use_high_level_tools_phase62 learning_agent.tests.test_windows_computer_use_generic_control_actions_phase70
python -m py_compile learning_agent\computer_use\generic_control_actions.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_phase70_generic_control_actions.json
```

Expected: click/type generic wrapper passes without direct low-level bypass.

---

## Task 7: Phase71 Generic Hotkey, Menu, Scroll, And Drag

**Files:**
- Create: `learning_agent/computer_use/generic_input_actions.py`
- Create: `learning_agent/tests/test_windows_computer_use_generic_input_actions_phase71.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase71_generic_input_actions.json`
- Modify: `learning_agent/computer_use/__init__.py`
- Backup: `learning_agent/test/agent_capability_phase71_generic_input_actions_20260603/`

- [x] **Step 1: Write the failing test**

Test imports:

```python
from learning_agent.computer_use.generic_input_actions import WindowsGenericInputActionRuntime, phase71_cli_line, run_phase71_generic_input_actions_contract
```

Assertions:

```python
report = run_phase71_generic_input_actions_contract()
self.assertTrue(report["hotkey_action"])
self.assertTrue(report["menu_navigation"])
self.assertTrue(report["scroll_action"])
self.assertTrue(report["drag_action"])
self.assertTrue(report["continuous_mouse_path"])
self.assertFalse(report["actions_expanded"])
```

- [x] **Step 2: Run the red test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_generic_input_actions_phase71
```

Expected: fail because generic input action module is missing.

- [x] **Step 3: Implement input action runtime**

Implement:
- `build_hotkey_events(keys: list[str])`.
- `build_scroll_events(x: int, y: int, delta: int)`.
- `build_drag_path(points: list[dict[str, int]])`.
- `build_menu_sequence(menu_path: list[str])`.
- Recording sender tests for event shapes.
- Real dispatch remains gated by Phase72 policy.

Forbidden combinations:
- `ctrl+alt+delete`
- `win+r`
- `win+x`
- `ctrl+shift+esc`
- Any system-level combo unless a later explicit high-risk grant is present.

Required CLI line:

```text
PHASE71_GENERIC_INPUT_ACTIONS_READY PHASE71_GENERIC_INPUT_ACTIONS_OK hotkey_action=true menu_navigation=true scroll_action=true drag_action=true continuous_mouse_path=true forbidden_system_hotkeys_blocked=true actions_expanded=false
```

- [x] **Step 4: Verify Phase71**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_generic_input_actions_phase71
python -m py_compile learning_agent\computer_use\generic_input_actions.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_phase71_generic_input_actions.json
```

Expected: event builder passes, system hotkeys are blocked, and no real app action is expanded in this phase.

---

## Task 8: Phase72 Safety Boundary For Real Apps

**Files:**
- Create: `learning_agent/computer_use/real_app_safety_boundary.py`
- Create: `learning_agent/tests/test_windows_computer_use_real_app_safety_boundary_phase72.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase72_real_app_safety_boundary.json`
- Modify: `learning_agent/computer_use/__init__.py`
- Backup: `learning_agent/test/agent_capability_phase72_real_app_safety_boundary_20260603/`

- [x] **Step 1: Write the failing test**

Test imports:

```python
from learning_agent.computer_use.real_app_safety_boundary import WindowsRealAppSafetyBoundary, phase72_cli_line, run_phase72_real_app_safety_boundary_contract
```

Assertions:

```python
report = run_phase72_real_app_safety_boundary_contract()
self.assertTrue(report["authorized_real_app_actions"])
self.assertTrue(report["unauthorized_window_zero_events"])
self.assertTrue(report["high_risk_default_refusal"])
self.assertTrue(report["abort_before_low_level_send"])
self.assertTrue(report["approval_bypass_blocked"])
self.assertTrue(report["controlled_actions_expansion"])
self.assertFalse(report["uncontrolled_actions_expanded"])
```

- [x] **Step 2: Run the red test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_real_app_safety_boundary_phase72
```

Expected: fail because safety boundary module is missing.

- [x] **Step 3: Implement real-app boundary**

Implement:
- `WindowsRealAppSafetyBoundary.evaluate(window, action, grant_store, session_id)`.
- Allow only normal user-authorized apps.
- Deny terminal, Codex UI, password, auth, captcha, payment, admin, security, Windows Run, and private-data windows.
- Require active Phase60 persistent grant for write actions.
- Check Phase61 abort immediately before low-level send.
- Return `low_level_event_count=0` for every refusal.

Required CLI line:

```text
PHASE72_REAL_APP_SAFETY_BOUNDARY_READY PHASE72_REAL_APP_SAFETY_BOUNDARY_OK authorized_real_app_actions=true unauthorized_window_zero_events=true high_risk_default_refusal=true abort_before_low_level_send=true approval_bypass_blocked=true controlled_actions_expansion=true uncontrolled_actions_expanded=false
```

- [x] **Step 4: Verify Phase72**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_real_app_safety_boundary_phase72
python -m unittest learning_agent.tests.test_windows_computer_use_persistent_grants_phase60 learning_agent.tests.test_windows_computer_use_abort_streaming_hooks_phase61 learning_agent.tests.test_windows_computer_use_real_app_safety_boundary_phase72
python -m py_compile learning_agent\computer_use\real_app_safety_boundary.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_phase72_real_app_safety_boundary.json
```

Expected: authorized normal-app path is classified as controlled, and every unsafe path sends zero events.

---

## Task 9: Phase73 App Memory And Self-Learning

**Files:**
- Create: `learning_agent/computer_use/app_memory.py`
- Create: `learning_agent/tests/test_windows_computer_use_app_memory_phase73.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase73_app_memory.json`
- Modify: `learning_agent/computer_use/__init__.py`
- Backup: `learning_agent/test/agent_capability_phase73_app_memory_20260603/`

- [ ] **Step 1: Write the failing test**

Test imports:

```python
from learning_agent.computer_use.app_memory import WindowsComputerUseAppMemoryStore, phase73_cli_line, run_phase73_app_memory_contract
```

Assertions:

```python
report = run_phase73_app_memory_contract()
self.assertTrue(report["app_memory"])
self.assertTrue(report["non_secret_memory"])
self.assertTrue(report["memory_assists_not_scripts"])
self.assertTrue(report["memory_can_be_revoked"])
self.assertFalse(report["actions_expanded"])
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_app_memory_phase73
```

Expected: fail because app memory module is missing.

- [ ] **Step 3: Implement app memory**

Implement:
- `remember_app_hint(app, hint_type, hint_value, source, confidence)`.
- `list_app_hints(app)`.
- `revoke_app_memory(app)`.
- Store only non-secret data: app name, window class, role hints, safe control names, menu labels, last successful non-sensitive strategy.
- Reject and redact password, token, cookie, private text, payment, authentication, and terminal command content.

Required CLI line:

```text
PHASE73_APP_MEMORY_READY PHASE73_APP_MEMORY_OK app_memory=true non_secret_memory=true memory_assists_not_scripts=true memory_can_be_revoked=true actions_expanded=false
```

- [ ] **Step 4: Verify Phase73**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_app_memory_phase73
python -m py_compile learning_agent\computer_use\app_memory.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_phase73_app_memory.json
```

Expected: memory stores useful hints, rejects secrets, and supports revoke.

---

## Task 10: Phase74 Representative Real App E2E Matrix

**Files:**
- Create: `learning_agent/computer_use/representative_e2e_matrix.py`
- Create: `learning_agent/tests/test_windows_computer_use_representative_e2e_phase74.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase74_representative_e2e.json`
- Modify: `learning_agent/computer_use/__init__.py`
- Backup: `learning_agent/test/agent_capability_phase74_representative_e2e_20260603/`

- [ ] **Step 1: Write the failing test**

Test imports:

```python
from learning_agent.computer_use.representative_e2e_matrix import PHASE74_REPRESENTATIVE_E2E_MARKER, phase74_cli_line, run_phase74_representative_e2e_contract
```

Assertions with safe contract mode:

```python
report = run_phase74_representative_e2e_contract(real_smoke=False)
self.assertTrue(report["notepad_scenario"])
self.assertTrue(report["explorer_scenario"])
self.assertTrue(report["browser_scenario"])
self.assertTrue(report["window_style_scenario"])
self.assertTrue(report["mspaint_pikachu_scenario"])
self.assertTrue(report["real_paint_app_control"])
self.assertTrue(report["humanlike_drawing_actions"])
self.assertFalse(report["direct_image_file_cheat"])
self.assertTrue(report["representative_real_apps_passed"])
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_representative_e2e_phase74
```

Expected: fail because representative E2E module is missing.

- [ ] **Step 3: Implement representative matrix contract**

Implement scenario definitions:
- Notepad: launch, type, save to `learning_agent/memory/computer_use/e2e_notepad/`.
- Explorer: launch, create or verify controlled file under `learning_agent/memory/computer_use/e2e_explorer/`.
- Browser: use existing browser visible flow when available and avoid cookies/tokens/private profile content.
- Window-style app: use a safe dialog or built-in app flow that does not change system settings.
- Paint Pikachu: launch `mspaint.exe`, identify canvas, draw simplified yellow face/body, black ear tips, red cheeks, eyes, mouth, lightning tail, save evidence under `learning_agent/memory/computer_use/e2e_paint/`.

Paint scenario proof fields:
- `process_name=mspaint.exe`
- `canvas_observed=true`
- `draw_action_count>=12`
- `continuous_mouse_path=true`
- `saved_visual_artifact=true`
- `paint_canvas_not_blank=true`
- `pikachu_visual_elements=true`
- `direct_image_file_cheat=false`

The matrix can use `real_smoke=False` in unit tests. The visible terminal scenario must run the safe contract command first and then, when implementation supports it, run the real visible representative smoke on controlled files only.

Required CLI line:

```text
PHASE74_REPRESENTATIVE_E2E_READY PHASE74_REPRESENTATIVE_E2E_OK notepad_scenario=true explorer_scenario=true browser_scenario=true window_style_scenario=true mspaint_pikachu_scenario=true real_paint_app_control=true humanlike_drawing_actions=true direct_image_file_cheat=false paint_canvas_not_blank=true pikachu_visual_elements=true representative_real_apps_passed=true
```

- [ ] **Step 4: Verify Phase74**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_representative_e2e_phase74
python -m unittest learning_agent.tests.test_windows_computer_use_prompt_task_planner_phase67 learning_agent.tests.test_windows_computer_use_closed_loop_executor_phase68 learning_agent.tests.test_windows_computer_use_app_window_control_phase69 learning_agent.tests.test_windows_computer_use_generic_control_actions_phase70 learning_agent.tests.test_windows_computer_use_generic_input_actions_phase71 learning_agent.tests.test_windows_computer_use_real_app_safety_boundary_phase72 learning_agent.tests.test_windows_computer_use_app_memory_phase73 learning_agent.tests.test_windows_computer_use_representative_e2e_phase74
python -m py_compile learning_agent\computer_use\representative_e2e_matrix.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_phase74_representative_e2e.json
```

Expected: contract matrix passes and visible terminal acceptance does not touch real user data.

---

## Task 11: Phase75 Humanlike Windows Operator Final Matrix

**Files:**
- Create: `learning_agent/computer_use/humanlike_operator_matrix.py`
- Create: `learning_agent/tests/test_windows_computer_use_humanlike_operator_matrix_phase75.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase75_humanlike_operator_matrix.json`
- Modify: `learning_agent/computer_use/__init__.py`
- Modify: `task_plan.md`
- Modify: `agent_memory/context.md`, `agent_memory/progress.md`, `agent_memory/bugs.md`
- Backup: `learning_agent/test/agent_capability_phase75_humanlike_operator_matrix_20260603/`

- [ ] **Step 1: Write the failing test**

Test imports:

```python
from learning_agent.computer_use.humanlike_operator_matrix import PHASE75_HUMANLIKE_WINDOWS_OPERATOR_MARKER, phase75_cli_line, run_phase75_humanlike_operator_matrix_contract
```

Assertions:

```python
report = run_phase75_humanlike_operator_matrix_contract()
self.assertTrue(report["prompt_to_any_normal_app"])
self.assertTrue(report["humanlike_observe_act_verify_loop"])
self.assertTrue(report["generic_windows_app_control"])
self.assertFalse(report["per_app_scripts_required"])
self.assertTrue(report["uia_ocr_vision_fusion"])
self.assertTrue(report["mouse_keyboard_window_control"])
self.assertTrue(report["failure_recovery"])
self.assertTrue(report["representative_real_apps_passed"])
self.assertTrue(report["mspaint_pikachu_scenario"])
self.assertTrue(report["real_paint_app_control"])
self.assertTrue(report["humanlike_drawing_actions"])
self.assertFalse(report["direct_image_file_cheat"])
self.assertTrue(report["abort_safety"])
self.assertTrue(report["high_risk_confirmation"])
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_humanlike_operator_matrix_phase75
```

Expected: fail because final matrix module is missing.

- [ ] **Step 3: Implement final matrix**

Aggregate Phase65-74 contracts and produce the exact final token:

```text
PHASE75_HUMANLIKE_WINDOWS_OPERATOR_READY
prompt_to_any_normal_app=true
humanlike_observe_act_verify_loop=true
generic_windows_app_control=true
per_app_scripts_required=false
uia_ocr_vision_fusion=true
mouse_keyboard_window_control=true
failure_recovery=true
representative_real_apps_passed=true
mspaint_pikachu_scenario=true
real_paint_app_control=true
humanlike_drawing_actions=true
direct_image_file_cheat=false
abort_safety=true
high_risk_confirmation=true
```

The final matrix must include:
- `phase_count=10` for Phase65-74 inputs.
- `visible_terminal_gate=true`.
- `approval_bypass_blocked=true`.
- `uncontrolled_actions_expanded=false`.

- [ ] **Step 4: Verify Phase75**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_humanlike_operator_matrix_phase75
python -m unittest learning_agent.tests.test_windows_computer_use_humanlike_operator_phase65 learning_agent.tests.test_windows_computer_use_observation_fusion_phase66 learning_agent.tests.test_windows_computer_use_prompt_task_planner_phase67 learning_agent.tests.test_windows_computer_use_closed_loop_executor_phase68 learning_agent.tests.test_windows_computer_use_app_window_control_phase69 learning_agent.tests.test_windows_computer_use_generic_control_actions_phase70 learning_agent.tests.test_windows_computer_use_generic_input_actions_phase71 learning_agent.tests.test_windows_computer_use_real_app_safety_boundary_phase72 learning_agent.tests.test_windows_computer_use_app_memory_phase73 learning_agent.tests.test_windows_computer_use_representative_e2e_phase74 learning_agent.tests.test_windows_computer_use_humanlike_operator_matrix_phase75
python -m py_compile learning_agent\computer_use\humanlike_operator_matrix.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_phase75_humanlike_operator_matrix.json
```

Expected: final matrix passes, visible terminal acceptance passes, and independent verifier confirms `completed=true` and `assertion.passed=true`.

---

## Cross-Phase Verification

After every phase:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_<phase_test_name>
python -m py_compile <changed_python_files>
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\<phase_scenario>.json
```

Before claiming Phase75 completion:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_humanlike_operator_phase65 learning_agent.tests.test_windows_computer_use_observation_fusion_phase66 learning_agent.tests.test_windows_computer_use_prompt_task_planner_phase67 learning_agent.tests.test_windows_computer_use_closed_loop_executor_phase68 learning_agent.tests.test_windows_computer_use_app_window_control_phase69 learning_agent.tests.test_windows_computer_use_generic_control_actions_phase70 learning_agent.tests.test_windows_computer_use_generic_input_actions_phase71 learning_agent.tests.test_windows_computer_use_real_app_safety_boundary_phase72 learning_agent.tests.test_windows_computer_use_app_memory_phase73 learning_agent.tests.test_windows_computer_use_representative_e2e_phase74 learning_agent.tests.test_windows_computer_use_humanlike_operator_matrix_phase75
python -m unittest learning_agent.tests.test_windows_computer_use_parity_plus_matrix_phase64
python -m py_compile learning_agent\computer_use\humanlike_operator_contract.py learning_agent\computer_use\observation_fusion.py learning_agent\computer_use\prompt_task_planner.py learning_agent\computer_use\closed_loop_executor.py learning_agent\computer_use\app_window_control.py learning_agent\computer_use\generic_control_actions.py learning_agent\computer_use\generic_input_actions.py learning_agent\computer_use\real_app_safety_boundary.py learning_agent\computer_use\app_memory.py learning_agent\computer_use\representative_e2e_matrix.py learning_agent\computer_use\humanlike_operator_matrix.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_phase75_humanlike_operator_matrix.json
```

The final answer for any implemented phase must state whether visible terminal acceptance was completed. If it was not completed, the answer must say that development cannot be claimed complete for that phase.

## Self-Review Result

Spec coverage:
- Phase65 covers universal contract.
- Phase66 covers observation fusion.
- Phase67 covers prompt planning.
- Phase68 covers closed-loop execution.
- Phase69 covers app launch and focus.
- Phase70 covers generic click/type/control actions.
- Phase71 covers hotkey/menu/scroll/drag.
- Phase72 covers real-app safety.
- Phase73 covers app memory.
- Phase74 covers representative real apps and Paint Pikachu.
- Phase75 covers final humanlike matrix.

Placeholder scan:
- This plan uses concrete file paths, commands, tokens, and expected outcomes.
- No empty requirement slots are intentionally left in the plan.

Type consistency:
- Public contract functions use `run_phaseNN_<name>_contract`.
- CLI formatters use `phaseNN_cli_line`.
- Final matrix token names follow the existing Phase64 pattern.
