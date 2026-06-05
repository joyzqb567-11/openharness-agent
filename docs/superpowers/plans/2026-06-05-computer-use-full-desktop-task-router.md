# Computer Use Full Desktop Task Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/computer use --full` route ordinary natural-language desktop tasks into the Computer Use GUI observe-plan-act-verify loop, blocking script-generated final artifacts.

**Architecture:** Add a Desktop Task Router in front of the normal model tool loop, then route matching local-app prompts into a dedicated Computer Use desktop task runtime. The runtime reuses the existing mode session, generic app discovery, owned target identity, verified action gate, representative drawing evidence, and acceptance controller instead of creating a Paint-only controller.

**Tech Stack:** Python `unittest`, `learning_agent/app/interactive.py`, `learning_agent/core/agent.py`, existing `learning_agent/computer_use/*` modules, PowerShell acceptance controller, Windows Paint as representative visible-terminal acceptance.

---

## Fixed Scope

This plan implements the root-cause blueprint in `docs/superpowers/specs/2026-06-05-computer-use-full-desktop-task-router-blueprint.md`.

This plan does not implement a Paint-only Pikachu script. The Paint Pikachu scenario is only the final representative acceptance case for the generic desktop task route.

All new and modified code must follow `AGENTS.md` comment rules: every new or modified code line needs a clear Chinese comment explaining purpose and consequence. Each implementation task must also copy the changed code files into a matching folder under `learning_agent/test/`.

## File Structure

New files:

- `learning_agent/computer_use/desktop_task_router.py`
  - Classifies ordinary user prompts as desktop tasks or non-desktop tasks.
- `learning_agent/computer_use/desktop_task_policy.py`
  - Blocks script-generated final artifacts during routed desktop tasks.
- `learning_agent/computer_use/desktop_task_runtime.py`
  - Runs routed desktop tasks through Computer Use evidence and GUI action contracts.
- `learning_agent/computer_use/desktop_task_acceptance.py`
  - Evaluates final evidence for strict acceptance, including forbidden-script checks.
- `learning_agent/computer_use/drawing_primitives.py`
  - Converts abstract drawing intents into generic drag paths, not Paint-specific scripts.
- `learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py`
  - Main focused unit suite for router, policy, runtime, and acceptance evidence.
- `learning_agent/acceptance_controller/scenarios/computer_use_full_paint_pikachu_strict.json`
  - Final visible-terminal controller scenario for the exact user flow.
- `agent_memory/computer_use_full_desktop_task_router_plan_20260605.md`
  - Project memory summary for this implementation plan.

Modified files:

- `learning_agent/core/agent.py`
  - Invoke Desktop Task Router before the normal LLM tool loop and enforce desktop task context in `_bash_atom`.
- `learning_agent/app/interactive.py`
  - Preserve `/computer` command behavior and expose final desktop-task maturity command/token if needed.
- `learning_agent/computer_use/full_maturity_matrix.py`
  - Add natural-language desktop task maturity fields.
- `learning_agent/acceptance_controller/controller.ps1`
  - Add token-capture support if the strict scenario needs to confirm dynamic `/computer use --full` tokens.
- `agent_memory/progress.md`
  - Record implementation progress and final boundaries.

---

## Task 1: Freeze The Failed Script Path As A Negative Regression

**Files:**
- Create: `learning_agent/computer_use/desktop_task_acceptance.py`
- Create: `learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py`
- Backup: `learning_agent/test/computer_use_full_desktop_task_router_task1_20260605/`

- [ ] **Step 1: Write the failing tests**

Add tests proving the previous Paint Pikachu run is not acceptable:

```python
def test_script_generated_paint_artifact_fails_desktop_task_acceptance(self) -> None:
    evidence = {
        "desktop_task_router_used": True,
        "computer_use_gui_route_used": False,
        "tool_calls": [
            {"tool_name": "bash", "command": "Add-Type -AssemblyName System.Drawing; Start-Process mspaint.exe pikachu_for_paint.png"}
        ],
        "gui_action_count": 0,
        "low_level_event_count": 0,
        "target_app": "mspaint",
    }
    result = evaluate_desktop_task_acceptance(evidence)
    self.assertFalse(result["passed"])
    self.assertTrue(result["forbidden_script_generation_used"])
    self.assertEqual(result["decision"], "forbidden_script_artifact_route")
```

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_full_desktop_task_router
```

Expected: fails because `desktop_task_acceptance.py` does not exist.

- [ ] **Step 2: Implement acceptance evaluator**

Implement `evaluate_desktop_task_acceptance(evidence)` with these required checks:

- `desktop_task_router_used=true`
- `computer_use_gui_route_used=true`
- `bash_final_artifact_route_used=false`
- `forbidden_script_generation_used=false`
- `owned_window_verified=true`
- `gui_action_count>0`
- `low_level_event_count>0`
- `post_action_screenshot_exists=true`

- [ ] **Step 3: Run focused tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_full_desktop_task_router
```

Expected: all Task 1 tests pass.

- [ ] **Step 4: Back up changed files**

Copy:

- `learning_agent/computer_use/desktop_task_acceptance.py`
- `learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py`

to:

`learning_agent/test/computer_use_full_desktop_task_router_task1_20260605/`

- [ ] **Step 5: Commit**

```powershell
git add learning_agent/computer_use/desktop_task_acceptance.py learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py learning_agent/test/computer_use_full_desktop_task_router_task1_20260605
git commit -m "test: freeze desktop task script bypass regression"
```

---

## Task 2: Add Desktop Task Intent Router

**Files:**
- Create: `learning_agent/computer_use/desktop_task_router.py`
- Modify: `learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py`
- Backup: `learning_agent/test/computer_use_full_desktop_task_router_task2_20260605/`

- [ ] **Step 1: Write failing router tests**

Add tests:

```python
def test_chinese_paint_prompt_routes_to_desktop_task(self) -> None:
    intent = classify_desktop_task("请使用本地电脑的画图软件画一个皮卡丘。")
    self.assertTrue(intent.is_desktop_task)
    self.assertEqual(intent.target_app_hint, "画图")
    self.assertTrue(intent.requires_gui_actions)

def test_code_question_does_not_route_to_desktop_task(self) -> None:
    intent = classify_desktop_task("请解释这个 Python 函数为什么报错")
    self.assertFalse(intent.is_desktop_task)
```

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_full_desktop_task_router
```

Expected: fails because router module does not exist.

- [ ] **Step 2: Implement router**

Implement:

- `DesktopTaskIntent`
- `classify_desktop_task(prompt: str) -> DesktopTaskIntent`
- Chinese and English local-app keywords.
- False-positive protection for code, docs, git, test, and explanation requests.

Required output fields:

- `is_desktop_task`
- `reason`
- `target_app_hint`
- `task_goal`
- `requires_gui_actions`
- `raw_prompt_included=false`

- [ ] **Step 3: Run focused tests**

Run the same unittest command.

Expected: all Task 1-2 tests pass.

- [ ] **Step 4: Back up changed files**

Copy changed router and test files to the Task 2 backup folder.

- [ ] **Step 5: Commit**

```powershell
git add learning_agent/computer_use/desktop_task_router.py learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py learning_agent/test/computer_use_full_desktop_task_router_task2_20260605
git commit -m "feat: classify natural language desktop tasks"
```

---

## Task 3: Add Desktop Task Tool Policy

**Files:**
- Create: `learning_agent/computer_use/desktop_task_policy.py`
- Modify: `learning_agent/core/agent.py`
- Modify: `learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py`
- Backup: `learning_agent/test/computer_use_full_desktop_task_router_task3_20260605/`

- [ ] **Step 1: Write failing policy tests**

Add tests:

```python
def test_policy_blocks_system_drawing_final_artifact(self) -> None:
    result = evaluate_desktop_bash_command(
        command="Add-Type -AssemblyName System.Drawing; $bmp.Save('x.png'); Start-Process mspaint.exe x.png",
        desktop_task_active=True,
    )
    self.assertFalse(result["allowed"])
    self.assertEqual(result["decision"], "desktop_task_requires_gui_route")

def test_policy_allows_diagnostic_where_command(self) -> None:
    result = evaluate_desktop_bash_command(
        command="where.exe mspaint",
        desktop_task_active=True,
    )
    self.assertTrue(result["allowed"])
    self.assertEqual(result["decision"], "diagnostic_command_allowed")
```

Run focused tests. Expected: fails because policy module does not exist.

- [ ] **Step 2: Implement policy module**

Implement:

- `evaluate_desktop_bash_command(command: str, desktop_task_active: bool) -> dict`
- Forbidden patterns:
  - `System.Drawing`
  - `PIL`
  - `ImageMagick`
  - `magick`
  - `.Save(` for image artifacts
  - `Start-Process mspaint` with an existing image path
  - direct creation of `.png`, `.jpg`, `.bmp`, `.gif`, `.webp` as final artifact
- Allowed diagnostics:
  - `where.exe`
  - `Get-Command`
  - read-only process/window inspection

- [ ] **Step 3: Wire policy into `_bash_atom`**

Modify `LearningAgent` so a desktop-task run can set a desktop task context before tool execution. `_bash_atom` must call the policy when the context is active and return a clear refusal string containing `desktop_task_requires_gui_route`.

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_full_desktop_task_router
```

Expected: all Task 1-3 tests pass.

- [ ] **Step 5: Back up changed files and commit**

```powershell
git add learning_agent/computer_use/desktop_task_policy.py learning_agent/core/agent.py learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py learning_agent/test/computer_use_full_desktop_task_router_task3_20260605
git commit -m "feat: block script artifact route for desktop tasks"
```

---

## Task 4: Build Desktop Task Runtime

**Files:**
- Create: `learning_agent/computer_use/desktop_task_runtime.py`
- Modify: `learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py`
- Backup: `learning_agent/test/computer_use_full_desktop_task_router_task4_20260605/`

- [ ] **Step 1: Write failing runtime tests**

Add tests:

```python
def test_runtime_requires_full_mode_for_gui_task(self) -> None:
    runtime = ComputerUseDesktopTaskRuntime.for_test(full_mode=False)
    report = runtime.run_prompt("请使用本地电脑的画图软件画一个皮卡丘。", real_actions=False)
    self.assertFalse(report["passed"])
    self.assertEqual(report["decision"], "computer_use_full_mode_required")

def test_runtime_builds_gui_route_evidence_in_recording_mode(self) -> None:
    runtime = ComputerUseDesktopTaskRuntime.for_test(full_mode=True)
    report = runtime.run_prompt("请使用本地电脑的画图软件画一个皮卡丘。", real_actions=False)
    self.assertTrue(report["desktop_task_router_used"])
    self.assertTrue(report["computer_use_gui_route_used"])
    self.assertFalse(report["forbidden_script_generation_used"])
```

Expected: fails because runtime module does not exist.

- [ ] **Step 2: Implement runtime**

Implement `ComputerUseDesktopTaskRuntime` that reuses:

- `ComputerUseModeSessionStore`
- `generic_app_discovery.resolve_generic_target`
- `generic_real_launch_candidate.prepare_phase109_candidate`
- `target_identity.build_owned_target_identity`
- `representative_e2e_matrix.WindowsRepresentativeE2EMatrix` for recording-mode Paint Pikachu evidence

The first implementation may be recording-mode only. It must not touch the real desktop in unit tests.

- [ ] **Step 3: Add stable CLI token line**

Runtime report must include:

```text
COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_READY
COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK
desktop_task_router=true
natural_language_desktop_tasks_route_to_computer_use=true
computer_use_gui_route_used=true
forbidden_script_artifact_route_blocked=true
```

- [ ] **Step 4: Run focused tests**

Run focused tests. Expected: all Task 1-4 tests pass.

- [ ] **Step 5: Back up changed files and commit**

```powershell
git add learning_agent/computer_use/desktop_task_runtime.py learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py learning_agent/test/computer_use_full_desktop_task_router_task4_20260605
git commit -m "feat: add computer use desktop task runtime"
```

---

## Task 5: Route Ordinary Prompts Before The Normal Tool Loop

**Files:**
- Modify: `learning_agent/core/agent.py`
- Modify: `learning_agent/app/interactive.py`
- Modify: `learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py`
- Backup: `learning_agent/test/computer_use_full_desktop_task_router_task5_20260605/`

- [ ] **Step 1: Write failing integration tests**

Add tests proving the exact prompt is intercepted before the normal model can choose `bash`:

```python
def test_agent_routes_paint_prompt_to_desktop_runtime_before_bash(self) -> None:
    agent = build_test_agent_with_desktop_runtime(full_mode=True)
    answer = agent.run("请使用本地电脑的画图软件画一个皮卡丘。")
    self.assertIn("COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK", answer)
    self.assertIn("computer_use_gui_route_used=true", answer)
    self.assertNotIn("System.Drawing", answer)
```

Expected: fails because `LearningAgent.run` does not route desktop tasks yet.

- [ ] **Step 2: Modify `LearningAgent.run`**

Before the normal model message loop:

1. Call `classify_desktop_task(user_input)`.
2. If not a desktop task, continue existing behavior unchanged.
3. If desktop task, create `ComputerUseDesktopTaskRuntime` with the current workspace.
4. If full mode is missing, return a clear message requiring `/computer use --full`.
5. If full mode is valid, run the desktop task runtime.
6. Return the runtime answer without exposing the normal `bash` path as the final executor.

- [ ] **Step 3: Preserve `/computer` command behavior**

Ensure `app/interactive.py` still sends `/computer use --full`, `/computer use --full-confirm`, `/computer stop`, and `/computer maturity` through `run_computer_terminal_command`.

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_full_desktop_task_router
```

Expected: all Task 1-5 tests pass.

- [ ] **Step 5: Back up changed files and commit**

```powershell
git add learning_agent/core/agent.py learning_agent/app/interactive.py learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py learning_agent/test/computer_use_full_desktop_task_router_task5_20260605
git commit -m "feat: route desktop prompts to computer use runtime"
```

---

## Task 6: Add Generic Drawing Primitive Evidence

**Files:**
- Create: `learning_agent/computer_use/drawing_primitives.py`
- Modify: `learning_agent/computer_use/generic_input_actions.py`
- Modify: `learning_agent/computer_use/sendinput_dispatcher.py`
- Modify: `learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py`
- Backup: `learning_agent/test/computer_use_full_desktop_task_router_task6_20260605/`

- [ ] **Step 1: Write failing drawing tests**

Add tests:

```python
def test_pikachu_plan_uses_drag_paths_not_image_file(self) -> None:
    plan = build_pikachu_drag_plan(canvas_rect={"left": 100, "top": 100, "right": 900, "bottom": 700})
    self.assertGreaterEqual(len(plan["drag_paths"]), 12)
    self.assertFalse(plan["direct_image_file_cheat"])
    self.assertIn("yellow", {path["color"] for path in plan["drag_paths"]})

def test_drag_path_expands_to_mouse_events(self) -> None:
    events = expand_drag_path_to_low_level_events([(10, 10), (20, 20), (30, 25)])
    self.assertEqual(events[0]["type"], "mouse_move")
    self.assertIn("mouse_down", {event["type"] for event in events})
    self.assertIn("mouse_up", {event["type"] for event in events})
```

Expected: fails because drawing primitive module does not exist.

- [ ] **Step 2: Implement drawing primitives**

Implement:

- `build_pikachu_drag_plan(canvas_rect: dict) -> dict`
- `expand_drag_path_to_low_level_events(points: list[tuple[int, int]]) -> list[dict]`
- Color and path metadata for yellow body, black ears/eyes, red cheeks.

No function may write an image file.

- [ ] **Step 3: Wire `drag_path` through generic input action layer**

Add generic support so `drag_path` is a GUI action made of mouse events. It must still pass verified window action gates before dispatch.

- [ ] **Step 4: Run focused tests**

Run focused tests. Expected: all Task 1-6 tests pass.

- [ ] **Step 5: Back up changed files and commit**

```powershell
git add learning_agent/computer_use/drawing_primitives.py learning_agent/computer_use/generic_input_actions.py learning_agent/computer_use/sendinput_dispatcher.py learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py learning_agent/test/computer_use_full_desktop_task_router_task6_20260605
git commit -m "feat: add generic drawing drag paths"
```

---

## Task 7: Strict Visible-Terminal Paint Pikachu Acceptance

**Files:**
- Create: `learning_agent/acceptance_controller/scenarios/computer_use_full_paint_pikachu_strict.json`
- Modify: `learning_agent/acceptance_controller/controller.ps1`
- Modify: `learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py`
- Backup: `learning_agent/test/computer_use_full_desktop_task_router_task7_20260605/`

- [ ] **Step 1: Add controller token-capture tests**

If the controller cannot already reuse dynamic confirmation tokens, add tests or a dry-run scenario proving:

- `/computer use --full` output can capture `confirmation_token=<token>`.
- A later prompt line can use `/computer use --full-confirm ${confirmation_token}`.

- [ ] **Step 2: Implement controller token capture**

Extend scenario JSON with:

```json
{
  "capture_event_payload_regex": {
    "confirmation_token": "confirmation_token=([^\\r\\n]+)"
  },
  "prompt_lines": [
    "/computer use --full",
    "/computer use --full-confirm ${confirmation_token}",
    "请使用本地电脑的画图软件画一个皮卡丘。",
    "/computer stop"
  ]
}
```

If controller architecture cannot support multi-line dynamic prompts safely, create a deterministic `/computer desktop-task-final-acceptance` command that internally runs the same sequence, but the preferred route is real prompt lines.

- [ ] **Step 3: Create strict scenario**

Scenario must assert:

- `COMPUTER_USE_FULL_DESKTOP_TASK_ROUTER_OK`
- `desktop_task_router=true`
- `natural_language_desktop_tasks_route_to_computer_use=true`
- `computer_use_gui_route_used=true`
- `bash_final_artifact_route_used=false`
- `forbidden_script_generation_used=false`
- `owned_window_verified=true`
- `gui_action_count>0`
- `low_level_event_count>0`
- `canvas_changed_after_actions=true`
- `post_action_screenshot_exists=true`
- `Computer Use Stop`
- `stopped=true`

- [ ] **Step 4: Run visible terminal controller**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\computer_use_full_paint_pikachu_strict.json"
```

Expected:

```text
ACCEPTANCE_CONTROLLER_COMPLETED=True
```

- [ ] **Step 5: Back up artifacts and commit**

Back up:

- strict scenario JSON
- result JSON
- events JSONL
- screenshots
- latest readable log

to:

`learning_agent/test/computer_use_full_desktop_task_router_task7_20260605/`

Commit:

```powershell
git add learning_agent/acceptance_controller/controller.ps1 learning_agent/acceptance_controller/scenarios/computer_use_full_paint_pikachu_strict.json learning_agent/tests/test_windows_computer_use_full_desktop_task_router.py learning_agent/test/computer_use_full_desktop_task_router_task7_20260605
git commit -m "test: add strict desktop task visible acceptance"
```

---

## Task 8: Update Final Maturity Matrix

**Files:**
- Modify: `learning_agent/computer_use/full_maturity_matrix.py`
- Modify: `learning_agent/tests/test_windows_computer_use_full_maturity_matrix.py`
- Modify: `agent_memory/progress.md`
- Backup: `learning_agent/test/computer_use_full_desktop_task_router_task8_20260605/`

- [ ] **Step 1: Write failing maturity tests**

Add required tokens:

```python
"desktop_task_router=true",
"natural_language_desktop_tasks_route_to_computer_use=true",
"forbidden_script_artifact_route_blocked=true",
"owned_window_gui_actions_verified=true",
"paint_pikachu_visible_terminal_acceptance=true",
```

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_full_maturity_matrix
```

Expected: fails until matrix is updated.

- [ ] **Step 2: Update matrix**

Add the new fields to the structured report and CLI line:

- `desktop_task_router`
- `natural_language_desktop_tasks_route_to_computer_use`
- `forbidden_script_artifact_route_blocked`
- `owned_window_gui_actions_verified`
- `paint_pikachu_visible_terminal_acceptance`

- [ ] **Step 3: Run focused tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_full_maturity_matrix learning_agent.tests.test_windows_computer_use_full_desktop_task_router
```

Expected: all tests pass.

- [ ] **Step 4: Back up changed files and commit**

```powershell
git add learning_agent/computer_use/full_maturity_matrix.py learning_agent/tests/test_windows_computer_use_full_maturity_matrix.py agent_memory/progress.md learning_agent/test/computer_use_full_desktop_task_router_task8_20260605
git commit -m "feat: report desktop task router maturity"
```

---

## Final Verification

Run these before claiming completion:

```powershell
python -m py_compile .\learning_agent\core\agent.py .\learning_agent\app\interactive.py .\learning_agent\computer_use\desktop_task_router.py .\learning_agent\computer_use\desktop_task_policy.py .\learning_agent\computer_use\desktop_task_runtime.py .\learning_agent\computer_use\desktop_task_acceptance.py .\learning_agent\computer_use\drawing_primitives.py .\learning_agent\computer_use\full_maturity_matrix.py
```

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_full_desktop_task_router learning_agent.tests.test_windows_computer_use_full_maturity_matrix
```

```powershell
python -m unittest discover -s learning_agent\tests -p "test_windows_computer_use*.py"
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\computer_use_full_paint_pikachu_strict.json"
```

## Final Completion Rule

Do not say the feature is mature unless the strict visible-terminal result proves:

- `completed=true`
- `assertion.passed=true`
- `desktop_task_router=true`
- `natural_language_desktop_tasks_route_to_computer_use=true`
- `computer_use_gui_route_used=true`
- `bash_final_artifact_route_used=false`
- `forbidden_script_generation_used=false`
- `owned_window_verified=true`
- `gui_action_count>0`
- `low_level_event_count>0`
- `canvas_changed_after_actions=true`
- `post_action_screenshot_exists=true`
- `/computer stop` passed

If any item fails, the honest status is:

```text
/computer use --full is usable, but natural-language desktop task mode is not mature yet.
```
