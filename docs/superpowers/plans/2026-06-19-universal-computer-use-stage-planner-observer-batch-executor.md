# Universal Computer Use Stage Planner Observer Batch Executor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a universal Computer Use runtime for OpenHarness that can plan, observe, batch-execute, verify, and recover desktop tasks across ordinary Windows applications without hardcoding Notepad, Paint, browser, WeChat, WPS, or any single app as the product path.

**Architecture:** Keep ClaudeCode-style runtime governance as the lower layer: permission, session lock, target ownership, action safety, cleanup, and low-level executor. Add an OpenHarness upper layer: a generic `DesktopTaskPlan` made of `StagePlan` objects, stage-boundary observation, stage-level batch execution, stage verification, bounded repair, and a final gate that prevents incomplete desktop tasks from being reported as finished.

**Tech Stack:** Python 3.11+, pytest, OpenHarness `learning_agent.core.agent`, `learning_agent.core.convergence_controller`, `learning_agent.computer_use_mcp_v2.windows_runtime`, existing target lease/fresh target/resource freshness code, existing PowerShell acceptance controller visible-terminal harness.

---

## Product Boundary

This plan is for universal Computer Use, not an app-specific automation project.

The core implementation must not branch on application names such as `notepad`, `mspaint`, `paint`, `wechat`, `chrome`, `edge`, `wps`, `word`, or `explorer`.

Application names may appear only in:

- Representative acceptance scenarios.
- Unit test prompts that prove generic behavior.
- Existing app discovery aliases that map natural language to an application launch candidate.
- Logs or sanitized evidence returned by the desktop runtime.

The product behavior must be:

- Any supported ordinary Windows application is treated as a target window with capabilities, not as a special controller.
- Every write action is bound to one `target_ref`.
- Multiple-app tasks are represented as multiple target bindings and explicit stage ownership.
- Single-instance applications require explicit user authorization if an existing user window must be used.
- Unknown applications are handled through capability probing and conservative stages.
- Final answer is allowed only after the stage verifier marks all required stages complete.

## Current Evidence From CodeGraph

ClaudeCode source shows a strong runtime foundation:

- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\wrapper.tsx` binds Computer Use tools to a session context, permission state, allowed apps, screenshot state, and lock callbacks.
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\computerUseLock.ts` uses a lock file so two sessions cannot control the desktop at the same time.
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\cleanup.ts` releases the lock and restores the hidden environment after the turn.
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\executor.ts` centralizes screenshot, keyboard, mouse, drag, scroll, clipboard, app listing, and app opening.
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\appNames.ts` filters application metadata so app names cannot become prompt-injection text.

OpenHarness already has matching lower-layer pieces:

- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\controller.py` defines `ComputerUseBackend` with `status`, `observe`, and `execute`.
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\universal_real_observation.py` builds a real observation frame with screenshot, UIA, window inventory, and target evidence.
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\universal_target_session.py` establishes target sessions and target identity evidence.
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\universal_action_dsl.py` provides a generic DSL bridge to dispatch GUI actions.
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\universal_observe_plan_act_verify.py` already contains an observe-plan-act-verify loop, but it currently observes too often and plans actions at a primitive level.
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\universal_desktop_execution_loop.py` wires the current full-mode desktop runtime to the observe-plan-act-verify loop.

The root gap is upper-layer task organization:

- The agent can open a target and dispatch low-level events.
- The agent can observe before and after actions.
- The agent does not yet have a generic stage plan that keeps the whole desktop task alive until completion.
- The agent still lets primitive actions drive the loop, so a complex task may execute one stroke or one small action, then return `Next desktop action...` as if it were a final answer.

## Design Principles

### Universal Stage Model

The runtime must convert user intent into a `DesktopTaskPlan`.

`DesktopTaskPlan` contains:

- `objective`: the user goal in sanitized form.
- `task_kind`: a generic task kind such as `text_entry`, `drawing`, `form_fill`, `navigation`, `multi_app`, `file_operation`, `settings_change`, or `unknown_gui`.
- `targets`: one or more target descriptors, each resolved to a `target_ref` before write actions.
- `resources`: optional document/file/browser/resource descriptors.
- `success_criteria`: machine-checkable criteria extracted from the prompt.
- `stages`: ordered `StagePlan` items.

`StagePlan` contains:

- `stage_id`: stable id such as `stage_001_prepare_target`.
- `stage_kind`: generic kind such as `prepare_target`, `probe_capabilities`, `perform_content_work`, `commit_resource`, or `verify_result`.
- `target_ref`: the bound target window for this stage, or empty only for pre-target planning stages.
- `observation_policy`: when to observe.
- `batch`: one `ActionBatch` that can execute many primitive actions.
- `verifier`: the generic verification rule for this stage.
- `repair_policy`: bounded recovery rules.

`ActionBatch` contains:

- `batch_kind`: generic batch kind such as `text_entry_batch`, `pointer_path_batch`, `form_fill_batch`, `navigation_batch`, `menu_command_batch`, `file_save_batch`, `window_management_batch`, or `mixed_ui_batch`.
- `target_ref`: exactly one target binding for the batch.
- `actions`: generic DSL actions.
- `guardrails`: target identity, focus, bounds, event count, and abort limits.

### Observation Policy

The runtime must observe at stage boundaries, not before and after every primitive action by default.

Allowed observation policies:

- `none`: safe planning-only stage.
- `before_stage`: observe once before compiling the batch.
- `after_stage`: observe once after executing the batch.
- `before_and_after_stage`: default for write stages.
- `before_each_critical_action`: reserved for destructive or high-risk UI operations.

This is the compromise between speed and safety:

- Whole-task blind execution is unsafe.
- Primitive-action observation is too slow.
- Stage-level batch execution is the right default.

### Capability Profile Instead Of App-Specific Logic

The runtime must classify target windows by observed capabilities:

- `has_text_input`
- `has_canvas_like_region`
- `has_menu_bar`
- `has_toolbar`
- `has_file_save_surface`
- `has_browser_navigation_surface`
- `has_grid_or_table`
- `has_modal_dialog`
- `supports_keyboard_shortcuts_likely`
- `single_instance_suspected`
- `unknown_capabilities`

The planner must reason over these capabilities instead of app names.

Example:

- A text editor, chat box, browser textarea, WPS document, and Notepad all become `has_text_input=true`.
- A drawing app, whiteboard, canvas widget, and image editor become `has_canvas_like_region=true`.
- A browser, Electron app, and webview can become `has_browser_navigation_surface=true`.

### Final Gate

The final answer must be blocked when:

- any required stage is incomplete,
- the latest verified state says `next_step`, `next desktop action`, or `desktop_task_incomplete`,
- the final output contains a claimed success marker but the stage verifier did not mark all required stages complete,
- a resource save stage is required but save verification failed,
- the target window drifted and no explicit user grant exists.

This final gate is a backup. The main solution is the stage runtime.

## File Structure

Create focused files under:

`H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime`

New files:

- `stage_models.py`: dataclasses and JSON helpers for `DesktopTaskPlan`, `StagePlan`, `ActionBatch`, `StageResult`, and `DesktopTaskRunState`.
- `stage_planner.py`: universal prompt-to-stage planner using semantic task kinds and capabilities, not app-specific branches.
- `capability_profile.py`: converts observation frames into generic application/window capability profiles.
- `stage_batch_compiler.py`: compiles a `StagePlan` plus observation/capability profile into one `ActionBatch`.
- `batch_executor.py`: executes an `ActionBatch` through the existing `UniversalActionDslRuntime`, with target identity and event accounting.
- `stage_verifier.py`: verifies stage completion from observation frames, action results, and success criteria.
- `stage_task_loop.py`: orchestrates plan, target binding, stage observation, batch execution, verification, bounded repair, and cleanup.

Modify existing files:

- `universal_desktop_execution_loop.py`: route full-mode real desktop tasks through `UniversalStageTaskLoop`.
- `universal_observe_plan_act_verify.py`: keep existing contract loop, but stop using it as the primary complex task runtime once the stage loop is available.
- `universal_action_dsl.py`: add batch-compatible dispatch helpers only if the existing dispatch method cannot execute a list while preserving target identity checks.
- `controller.py`: expose batch execution only through generic action classes.
- `mcp_session_adapter.py`: surface stage-run evidence in the tool result payload.
- `convergence_controller.py`: add final gate checks for incomplete desktop stages.
- `agent.py`: read stage completion evidence before allowing a final answer for active Computer Use tasks.

New tests:

- `learning_agent/tests/test_universal_stage_models.py`
- `learning_agent/tests/test_universal_stage_planner.py`
- `learning_agent/tests/test_capability_profile.py`
- `learning_agent/tests/test_stage_batch_compiler.py`
- `learning_agent/tests/test_batch_executor.py`
- `learning_agent/tests/test_stage_task_loop.py`
- `learning_agent/tests/test_computer_use_stage_final_gate.py`

New acceptance scenarios:

- `learning_agent/acceptance_controller/scenarios/computer_use_universal_text_task_stage_batch_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/computer_use_universal_drawing_task_stage_batch_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/computer_use_universal_multi_app_stage_batch_visible_terminal.json`

The acceptance scenarios may use concrete installed apps as samples. The runtime implementation must remain app-agnostic.

## Implementation Tasks

### Task 1: Stage Data Model

**Files:**

- Create: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\stage_models.py`
- Test: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_universal_stage_models.py`

- [ ] **Step 1: Write failing model round-trip tests**

Test requirements:

- `DesktopTaskPlan` serializes to JSON-safe dict.
- `StagePlan` requires a stable `stage_id`.
- `ActionBatch` requires one `target_ref` for write batches.
- `StageResult` has explicit `status` values: `completed`, `needs_repair`, `needs_user`, `blocked`, `failed`.
- Invalid `status` raises `ValueError`.

Run:

```powershell
python -m pytest learning_agent/tests/test_universal_stage_models.py -q
```

Expected before implementation:

```text
ModuleNotFoundError: No module named 'learning_agent.computer_use_mcp_v2.windows_runtime.stage_models'
```

- [ ] **Step 2: Implement dataclasses**

Implementation shape:

```python
@dataclass(frozen=True)
class ActionBatch:
    batch_id: str
    batch_kind: str
    target_ref: str
    actions: tuple[dict[str, Any], ...]
    guardrails: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.batch_id.strip():
            raise ValueError("batch_id is required")
        if self.batch_kind.endswith("_batch") and not self.target_ref.strip():
            raise ValueError("target_ref is required for executable batches")
```

The real implementation must add Chinese comments on every new code line, following project rules.

- [ ] **Step 3: Add JSON helpers**

Required helpers:

- `desktop_task_plan_to_dict(plan: DesktopTaskPlan) -> dict[str, Any]`
- `desktop_task_plan_from_dict(payload: Mapping[str, Any]) -> DesktopTaskPlan`
- `stage_result_to_dict(result: StageResult) -> dict[str, Any]`

- [ ] **Step 4: Run model tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_universal_stage_models.py -q
```

Expected:

```text
passed
```

### Task 2: Capability Profile

**Files:**

- Create: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\capability_profile.py`
- Test: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_capability_profile.py`

- [ ] **Step 1: Write failing capability tests**

Test cases:

- Observation with UIA editable control returns `has_text_input=true`.
- Observation with canvas-like large empty visual region returns `has_canvas_like_region=true`.
- Observation with address/search input plus navigation buttons returns `has_browser_navigation_surface=true`.
- Observation with no useful UIA and no visual region returns `unknown_capabilities=true`.
- No test may require the observed app name to be Notepad, Paint, or browser.

- [ ] **Step 2: Implement `AppCapabilityProfile`**

Required fields:

- `has_text_input: bool`
- `has_canvas_like_region: bool`
- `has_menu_bar: bool`
- `has_toolbar: bool`
- `has_file_save_surface: bool`
- `has_browser_navigation_surface: bool`
- `has_modal_dialog: bool`
- `supports_keyboard_shortcuts_likely: bool`
- `single_instance_suspected: bool`
- `unknown_capabilities: bool`
- `evidence: tuple[str, ...]`

- [ ] **Step 3: Implement `build_capability_profile(observation_frame)`**

Rules:

- Use UIA roles, control types, bounds, and screenshot/window metadata.
- Do not branch on app name.
- Sanitize window text before storing evidence.
- Keep evidence short and non-sensitive.

- [ ] **Step 4: Run capability tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_capability_profile.py -q
```

Expected:

```text
passed
```

### Task 3: Universal Stage Planner

**Files:**

- Create: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\stage_planner.py`
- Modify: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\natural_language_semantic_planner.py`
- Test: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_universal_stage_planner.py`

- [ ] **Step 1: Write failing stage planner tests**

Test prompts:

```text
请使用本机任意可用文本编辑软件，输入 hello everyone，并保存到桌面。
请使用本机绘图软件，绘制一个彩色人物，并保存图片。
请打开本机浏览器，搜索 OpenHarness computer use，并查看结果。
请同时使用一个文本窗口和一个浏览窗口，把浏览到的标题整理到文本窗口。
请使用一个我没说名字的本地软件完成一个未知 GUI 操作。
```

Assertions:

- Every output has `DesktopTaskPlan`.
- Planner emits generic `task_kind`, not app-specific controller names.
- Text task contains stages: `prepare_target`, `probe_capabilities`, `perform_content_work`, `commit_resource`, `verify_result`.
- Drawing task contains stages: `prepare_target`, `probe_capabilities`, `perform_content_work`, `commit_resource`, `verify_result`.
- Multi-app task contains at least two target descriptors and no shared write `target_ref`.
- Unknown task ends in `needs_user` or `probe_capabilities`, not app-specific fallback.

- [ ] **Step 2: Implement `UniversalDesktopStagePlanner`**

Required public method:

```python
class UniversalDesktopStagePlanner:
    def plan(self, prompt: str, semantic_intent: Mapping[str, Any] | None = None) -> DesktopTaskPlan:
        ...
```

Planning rules:

- Extract generic task kind from the prompt.
- Extract required target count.
- Extract success criteria.
- Create stages without assuming a specific app.
- Use app launch aliases only as target discovery hints.
- Store a sanitized prompt signature, not the full prompt, unless an existing safe path already preserves prompt text.

- [ ] **Step 3: Keep old planner as compatibility path**

`WindowsPromptTaskPlanner` may continue to exist for old contract tests.

New full-mode runtime must use `UniversalDesktopStagePlanner` for live Computer Use tasks.

- [ ] **Step 4: Run planner tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_universal_stage_planner.py -q
```

Expected:

```text
passed
```

### Task 4: Stage Batch Compiler

**Files:**

- Create: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\stage_batch_compiler.py`
- Test: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_stage_batch_compiler.py`

- [ ] **Step 1: Write failing compiler tests**

Tests:

- Text content stage compiles one `text_entry_batch` with focus plus type actions.
- Drawing content stage compiles one `pointer_path_batch` with multiple `drag_path` actions.
- Save stage compiles `file_save_batch` using generic save command strategy.
- Compiler refuses to compile a write batch without `target_ref`.
- Compiler never checks for a hardcoded app name.

- [ ] **Step 2: Implement `compile_stage_to_batch(...)`**

Required signature:

```python
def compile_stage_to_batch(
    stage: StagePlan,
    observation_frame: Mapping[str, Any],
    capability_profile: AppCapabilityProfile,
) -> ActionBatch:
    ...
```

Compilation rules:

- `has_text_input=true` plus text stage becomes `text_entry_batch`.
- `has_canvas_like_region=true` plus drawing stage becomes `pointer_path_batch`.
- Browser-like navigation becomes `navigation_batch`.
- Generic form input becomes `form_fill_batch`.
- Save/commit stage becomes `file_save_batch`.
- Unknown capability returns a `StageResult` path of `needs_user` or a probe batch, not a fake success.

- [ ] **Step 3: Make drawing generic**

Drawing batches must express generic primitives:

- outline paths,
- fill or color selection actions if available,
- repeated pointer paths,
- save command.

The compiler must not know what an Ultraman, Pikachu, house, or cat is. It only receives a symbolic drawing plan from the planner and converts it into path/color batches.

- [ ] **Step 4: Run compiler tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_stage_batch_compiler.py -q
```

Expected:

```text
passed
```

### Task 5: Batch Executor

**Files:**

- Create: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\batch_executor.py`
- Modify: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\universal_action_dsl.py`
- Test: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_batch_executor.py`

- [ ] **Step 1: Write failing executor tests**

Fake runtime tests:

- Batch executor calls target identity verification once before batch start.
- Batch executor refuses when `target_ref` drift is reported.
- Batch executor dispatches all primitive actions in the batch when the target is stable.
- Batch executor reports `primitive_action_count`, `successful_action_count`, and `low_level_event_count`.
- Batch executor aborts the remaining batch if a critical primitive fails.

- [ ] **Step 2: Implement `UniversalActionBatchExecutor`**

Required public method:

```python
class UniversalActionBatchExecutor:
    def execute_batch(self, session: Mapping[str, Any], batch: ActionBatch) -> StageResult:
        ...
```

Execution rules:

- All primitives in a batch share one `target_ref`.
- Verify target identity before batch.
- For destructive or file-affecting actions, verify target identity again before the critical primitive.
- Use existing `UniversalActionDslRuntime.dispatch(...)`.
- Preserve existing low-level sender and FreshTarget gates.
- Do not introduce a direct PowerShell, Python, or file-system shortcut for task completion.

- [ ] **Step 3: Run executor tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_batch_executor.py -q
```

Expected:

```text
passed
```

### Task 6: Stage Verifier

**Files:**

- Create: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\stage_verifier.py`
- Test: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_stage_verifier.py`

- [ ] **Step 1: Write failing verifier tests**

Test cases:

- Text stage verifies when post-observation contains the expected text summary or editable content evidence.
- Drawing stage verifies when canvas changed and expected visual primitives exist at a basic level.
- Save stage verifies when the app reports saved state, save dialog completed, or saved resource evidence exists.
- Incomplete stage returns `needs_repair`, not success.
- Ambiguous target returns `blocked` or `needs_user`.

- [ ] **Step 2: Implement `UniversalStageVerifier`**

Required public method:

```python
class UniversalStageVerifier:
    def verify_stage(
        self,
        plan: DesktopTaskPlan,
        stage: StagePlan,
        before_frame: Mapping[str, Any],
        after_frame: Mapping[str, Any],
        execution_result: StageResult,
    ) -> StageResult:
        ...
```

Verification rules:

- Use generic stage kind and success criteria.
- Use observation evidence first.
- Use execution event counts only as supporting evidence.
- Never mark completion only because events were sent.
- Return `needs_repair` when the result is close but incomplete.
- Return `needs_user` when user authorization or manual app closing is required.

- [ ] **Step 3: Run verifier tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_stage_verifier.py -q
```

Expected:

```text
passed
```

### Task 7: Universal Stage Task Loop

**Files:**

- Create: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\stage_task_loop.py`
- Modify: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\universal_desktop_execution_loop.py`
- Test: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_stage_task_loop.py`

- [ ] **Step 1: Write failing loop tests**

Tests:

- A fake text task observes at stage boundaries and not before every primitive.
- A fake drawing task executes one batch containing multiple pointer paths.
- A failed stage enters bounded repair and stops after the configured limit.
- A `needs_user` stage stops tool execution and returns a user-facing reason.
- All completed stages produce `desktop_task_completed=true`.
- Any incomplete stage produces `desktop_task_incomplete=true`.

- [ ] **Step 2: Implement `UniversalStageTaskLoop`**

Required constructor dependencies:

- `planner`
- `observation_runtime`
- `target_runtime`
- `capability_profile_builder`
- `batch_compiler`
- `batch_executor`
- `stage_verifier`
- `max_stage_repairs`

Required method:

```python
class UniversalStageTaskLoop:
    def run_desktop_task(self, prompt: str, target_hint: str = "") -> dict[str, Any]:
        ...
```

Runtime flow:

1. Build `DesktopTaskPlan`.
2. Acquire or create target sessions through existing target lease/fresh target runtime.
3. For each stage, observe according to `observation_policy`.
4. Build capability profile.
5. Compile one `ActionBatch`.
6. Execute the batch.
7. Observe after the stage when required.
8. Verify the stage.
9. Repair bounded failures.
10. Stop on `needs_user`, `blocked`, or unrecoverable failure.
11. Return structured stage evidence.

- [ ] **Step 3: Wire into `UniversalDesktopExecutionLoopAdapter`**

Rules:

- Production full mode uses `UniversalStageTaskLoop`.
- Existing contract tests can still invoke the old `UniversalObservePlanActVerifyLoop`.
- The adapter report must include:
  - `universal_stage_task_loop_used`
  - `desktop_task_plan_created`
  - `stage_count`
  - `completed_stage_count`
  - `desktop_task_completed`
  - `desktop_task_incomplete`
  - `stage_boundary_observation_used`
  - `batch_execution_used`
  - `primitive_action_count`
  - `low_level_event_count`

- [ ] **Step 4: Run loop tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_stage_task_loop.py -q
```

Expected:

```text
passed
```

### Task 8: Final Gate For Incomplete Desktop Tasks

**Files:**

- Modify: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\convergence_controller.py`
- Modify: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\agent.py`
- Test: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_computer_use_stage_final_gate.py`

- [ ] **Step 1: Write failing final-gate tests**

Tests:

- Final answer containing `Next desktop action` is blocked when `desktop_task_incomplete=true`.
- Final success marker is blocked when `completed_stage_count < stage_count`.
- Final answer is allowed when `desktop_task_completed=true`.
- `needs_user` allows a final answer only if it asks the user for the required action.

- [ ] **Step 2: Implement final gate**

Rules:

- The gate reads structured stage evidence from runtime state and tool results.
- It does not rely only on prompt text.
- Text pattern checks such as `Next desktop action` are backup signals.
- The gate returns a clear reason such as `desktop_task_incomplete`.

- [ ] **Step 3: Run final-gate tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_computer_use_stage_final_gate.py -q
```

Expected:

```text
passed
```

### Task 9: Generic Multi-Target Handling

**Files:**

- Modify: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\stage_models.py`
- Modify: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\stage_task_loop.py`
- Modify: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\universal_target_session.py`
- Test: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_computer_use_multi_target_stage_loop.py`

- [ ] **Step 1: Write failing multi-target tests**

Tests:

- Planner can represent two target descriptors.
- Each write batch has exactly one target ref.
- Switching targets requires an observation or focus verification stage.
- A write intended for target A cannot execute on target B.
- User-owned existing windows require explicit grant before reuse.

- [ ] **Step 2: Implement target map in run state**

Run state must contain:

- `target_sessions_by_ref`
- `active_target_ref`
- `stage_target_ref`
- `user_granted_existing_target_refs`
- `blocked_target_refs`

- [ ] **Step 3: Run multi-target tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_computer_use_multi_target_stage_loop.py -q
```

Expected:

```text
passed
```

### Task 10: Acceptance Controller Scenarios

**Files:**

- Create: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\computer_use_universal_text_task_stage_batch_visible_terminal.json`
- Create: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\computer_use_universal_drawing_task_stage_batch_visible_terminal.json`
- Create: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\computer_use_universal_multi_app_stage_batch_visible_terminal.json`
- Test: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_computer_use_stage_acceptance_scenarios.py`

- [ ] **Step 1: Write scenario schema tests**

Assertions:

- All three scenarios are valid JSON.
- All three start by entering `/computer use --full`.
- All three use `LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS=1` only for the acceptance run, because the user explicitly accepted the risk.
- No scenario instruction tells the agent to use PowerShell, Python, or direct file generation to fake GUI completion.
- Expected markers check stage evidence, not just final prose.

- [ ] **Step 2: Add representative prompts**

Text task prompt:

```text
请使用本机任意可用文本编辑软件，打开一个新的可编辑窗口，输入 hello everyone，并通过软件界面保存到桌面。不要用 PowerShell、Python 或命令行直接写文件。最后输出 UNIVERSAL_TEXT_STAGE_BATCH_OK desktop_task_completed=true stage_boundary_observation_used=true batch_execution_used=true
```

Drawing task prompt:

```text
请使用本机任意可用绘图软件，绘制一个简单彩色人物，至少包含轮廓、头部、身体和两种颜色，并通过软件界面保存图片。不要用 PowerShell、Python 或命令行直接生成图片。最后输出 UNIVERSAL_DRAWING_STAGE_BATCH_OK desktop_task_completed=true stage_boundary_observation_used=true batch_execution_used=true
```

Multi-app task prompt:

```text
请使用两个本机普通应用窗口完成一个简单任务：一个窗口用于查找或展示短文本信息，另一个窗口用于整理并保存该信息。每个写入动作都必须绑定对应窗口。不要用 PowerShell、Python 或命令行直接写文件。最后输出 UNIVERSAL_MULTI_APP_STAGE_BATCH_OK desktop_task_completed=true target_ref_one_to_one=true batch_execution_used=true
```

These prompts are representative samples only. They must not create app-specific runtime branches.

- [ ] **Step 3: Run visible terminal acceptance**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File learning_agent/acceptance_controller/controller.ps1 -Scenario computer_use_universal_text_task_stage_batch_visible_terminal
powershell -ExecutionPolicy Bypass -File learning_agent/acceptance_controller/controller.ps1 -Scenario computer_use_universal_drawing_task_stage_batch_visible_terminal
```

Expected:

```text
ACCEPTANCE_CONTROLLER_COMPLETED=True
```

The multi-app scenario may be marked pressure-only if the local environment lacks safe app choices.

### Task 11: Documentation And Evidence

**Files:**

- Modify: `H:\codexworkplace\sofeware\OpenHarness-main\docs\computer_use_mcp_v2_architecture.md`
- Modify: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\README.md`
- Modify: `H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\progress.md`
- Modify: `H:\codexworkplace\sofeware\OpenHarness-main\agent_memory\experience.md`

- [ ] **Step 1: Document the universal architecture**

Document sections:

- Runtime layer inspired by ClaudeCode.
- Universal stage planner layer.
- Capability profile layer.
- Stage-boundary observation policy.
- Batch execution layer.
- Stage verifier and final gate.
- Acceptance requirements.

- [ ] **Step 2: Record the repeated failure lesson**

Add to `experience.md`:

```text
Computer Use complex GUI tasks must not rely on primitive tool-loop convergence. The stable design is generic stage planning, stage-boundary observation, batch execution, and stage verification. App-specific samples are acceptance fixtures, not architecture.
```

- [ ] **Step 3: Save learning copies for changed code**

For every modified `.py`, `.ps1`, or `.json` file in implementation, copy the modified content or patch summary into:

```text
H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\test
```

Use dated filenames such as:

```text
20260619_universal_stage_planner_stage_models.py
20260619_universal_stage_planner_test_stage_models.py
```

### Task 12: Full Verification

**Files:**

- No new files.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_universal_stage_models.py learning_agent/tests/test_capability_profile.py learning_agent/tests/test_universal_stage_planner.py learning_agent/tests/test_stage_batch_compiler.py learning_agent/tests/test_batch_executor.py learning_agent/tests/test_stage_verifier.py learning_agent/tests/test_stage_task_loop.py learning_agent/tests/test_computer_use_stage_final_gate.py -q
```

Expected:

```text
passed
```

- [ ] **Step 2: Run existing Computer Use regression tests**

Run:

```powershell
python -m pytest learning_agent/tests/test_actionability_auto_observe_recovery.py learning_agent/tests/test_agent_auto_observe_recovery_loop.py learning_agent/tests/test_computer_use_controller_fresh_target_gate.py learning_agent/tests/test_computer_use_mcp_v2_runtime_acceptance_event.py learning_agent/tests/test_computer_use_multi_target_registry.py learning_agent/tests/test_computer_use_pressure_readiness.py learning_agent/tests/test_mcp_session_adapter_observe_target_ref.py learning_agent/tests/test_universal_computer_use_fresh_target_policy.py learning_agent/tests/test_universal_computer_use_target_lease.py learning_agent/tests/test_universal_target_session_fresh_proxy_binding.py -q
```

Expected:

```text
passed
```

- [ ] **Step 3: Run full project tests if runtime permits**

Run:

```powershell
python -m pytest learning_agent/tests -q
```

Expected:

```text
passed
```

- [ ] **Step 4: Validate acceptance scenario JSON**

Run:

```powershell
python - <<'PY'
import json
from pathlib import Path
root = Path(r"H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios")
for path in root.glob("*.json"):
    json.loads(path.read_text(encoding="utf-8"))
print("scenario_json_ok")
PY
```

Expected:

```text
scenario_json_ok
```

- [ ] **Step 5: Run required visible-terminal acceptance**

Run the acceptance controller with visible terminal scenarios from Task 10.

Required evidence:

- `ACCEPTANCE_CONTROLLER_COMPLETED=True`
- `desktop_task_completed=true`
- `stage_boundary_observation_used=true`
- `batch_execution_used=true`
- low-level event count greater than zero
- no direct PowerShell/Python/file-system artifact shortcut

- [ ] **Step 6: Refresh CodeGraph**

Run:

```powershell
codegraph sync "H:\codexworkplace\sofeware\OpenHarness-main"
codegraph status "H:\codexworkplace\sofeware\OpenHarness-main"
```

Expected:

```text
[OK]
```

## Stop Conditions

Stop and report to the user before continuing if:

- The implementation requires app-specific branches in the production planner.
- A target window cannot be bound one-to-one to a `target_ref`.
- The runtime needs to close a user-owned window automatically.
- The visible-terminal acceptance repeatedly opens or writes to an old user window without explicit user grant.
- A complex GUI task still returns `Next desktop action` as final answer.
- Full verification cannot run in the local environment.

## Self-Review

Spec coverage:

- Universal software design is covered by capability profile, generic stage kinds, generic batch kinds, and no app-name branching.
- ClaudeCode inspiration is covered by lower-layer runtime governance rather than copied app behavior.
- OpenHarness current architecture is respected by building on target sessions, observation frames, action DSL, and acceptance controller.
- User concern about slow primitive observation is addressed by stage-boundary observation.
- User concern about unfinished tasks finalizing early is addressed by stage verifier and final gate.

Placeholder scan:

- No task uses unresolved placeholder wording or an unspecified "add tests" instruction.
- Every task has concrete files, behavior, commands, and expected result.

Type consistency:

- `DesktopTaskPlan`, `StagePlan`, `ActionBatch`, `StageResult`, and `DesktopTaskRunState` are introduced in Task 1 and reused consistently.
- `UniversalStageTaskLoop` is introduced in Task 7 and wired through `UniversalDesktopExecutionLoopAdapter`.
- Stage evidence fields are named consistently: `desktop_task_completed`, `desktop_task_incomplete`, `stage_boundary_observation_used`, and `batch_execution_used`.

## Execution Recommendation

Use `superpowers:subagent-driven-development` for implementation because tasks can be split cleanly:

- One worker for data models and planner.
- One worker for capability profile and compiler.
- One worker for batch executor and verifier.
- One worker for final gate and acceptance scenarios.

Use `superpowers:executing-plans` if strict sequential review is preferred.
