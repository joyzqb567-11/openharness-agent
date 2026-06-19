# ClaudeCode Inspired Computer Use Runtime Recovery And Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a generic, code-level Computer Use runtime recovery layer for OpenHarness so the agent can handle observe-before-action, old-window refusal, multi-window tasks, and turn cleanup through deterministic controller behavior instead of relying on dynamic prompt injection.

**Architecture:** Keep OpenHarness's FreshTarget + TargetLease policy as the hard safety boundary, and add a ClaudeCode-inspired runtime wrapper around the tool loop: one Computer Use session, one lock, explicit permission, bounded action preparation, automatic observe recovery when the runtime itself requires observation, and guaranteed cleanup on normal completion, abort, failure, timeout, or user stop. The implementation must remain application-agnostic: Notepad, Paint, browser, WPS, WeChat, Explorer, and unknown GUI apps use the same target and recovery protocol.

**Tech Stack:** Python 3.11+, pytest, existing `LearningAgent` tool loop, existing `convergence_controller`, existing `actionability_state`, existing `computer_use_mcp_v2` Windows runtime, existing acceptance controller PowerShell visible-terminal harness.

---

## Current Evidence From CodeGraph

ClaudeCode source shows the design direction but not a Windows-specific solution:

- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\wrapper.tsx` builds and binds a Computer Use session context before dispatch.
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\computerUseLock.ts` prevents multiple concurrent Computer Use sessions from controlling the desktop.
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\cleanup.ts` releases lock and restores hidden apps after a turn.
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\executor.ts` centralizes actual desktop actions and prepares the environment before click, key, typing, drag, screenshot, and open-app operations.
- `D:\ClaudeCode-main\ClaudeCode-main\utils\computerUse\appNames.ts` sanitizes application names so app metadata cannot become prompt-injection content.

OpenHarness already has several matching foundations:

- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\actionability_state.py` can parse `OPENHARNESS_DESKTOP_ACTION_REQUIRED`, persist `actionability_pending`, require `next_required_tool=observe`, and clear pending after the matching tool succeeds.
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\action_gates.py` emits `observe_before_action_required` when a write action is attempted without recent model-visible observation.
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\convergence_controller.py` blocks tools that bypass a pending action and injects model reminders.
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\agent.py` runs all tool calls through `decide_tool_call`, executes real tools through `execute_tool_calls_from_orchestrator`, then calls `record_tool_result`.
- `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\agent.py` already calls `_run_computer_use_turn_cleanup_if_needed(...)` in `finally`, so cleanup has an anchor point.

The missing piece is not target lease itself. The missing piece is runtime recovery:

- OpenHarness detects `observe_before_action_required`, but currently asks the model to call observe on the next round.
- When the model repeats `open_application`, `key`, or another action instead of `observe`, the convergence layer blocks or reminds, but the live task can still spiral into repeated retries.
- The right fix is a deterministic, bounded, controller-owned recovery step: when a tool result creates a desktop observe-required pending state, the runtime should synthesize exactly one protocol-valid `observe` tool call, execute it, feed the screenshot result back to the model, and only then let the model plan the next action.

## Root Problem

The recurring failures are caused by a boundary mismatch:

- Safety checks live in code, which is correct.
- Recovery after a safety check still depends too much on model compliance, which is weak under complex prompts.
- Dynamic prompt injection can guide behavior, but it cannot be the only mechanism because the model may still retry the wrong tool.
- A generic Computer Use agent must recover at the runtime level for predictable machine-checkable states such as "you must observe before any more action".

This plan does not special-case Notepad or Paint. Those apps are only acceptance samples. The runtime behavior must work for any GUI app.

## ClaudeCode-Inspired Design Rules

- Session ownership is a runtime object, not a sentence in the prompt.
- Permission is granted once per Computer Use session, then scoped to allowed apps and target leases.
- Before every action, the runtime prepares and verifies the target instead of trusting the model's next token.
- If a required preparation step is deterministic, the runtime may execute it directly with a bounded retry budget.
- Cleanup must run from `finally` paths, stop hooks, abort paths, and acceptance timeout paths.
- App names, window titles, and user-controlled app metadata must be sanitized before entering prompts, logs, or permission text.

## Product Policy

The policy for all applications is:

- Fresh target or explicit user grant is required before write actions.
- Existing user windows are never silently taken over.
- Single-instance apps may be used only when the user explicitly grants the existing window.
- Unknown apps use the same prelaunch and postlaunch classification as known apps.
- Multiple app windows can be active in one task, but every write action must resolve to exactly one `target_ref`.
- If a deterministic observe is required before action, the runtime performs a bounded automatic observe recovery.
- If user action is required, such as "close the existing app" or "authorize the existing window", the runtime must not auto-recover; it must stop tools and ask the user.

## Non-Goals

- Do not add Notepad-only, Paint-only, or per-application special branches.
- Do not solve every application's document freshness semantics in this plan.
- Do not let the agent close user windows automatically.
- Do not bypass the existing `TargetLease` or FreshTarget checks.
- Do not use PowerShell, Python scripts, or command-line file writes as a substitute for real Computer Use acceptance.

## Target Runtime Flow

Normal action flow:

1. Model requests a Computer Use tool.
2. `decide_tool_call(...)` checks FreshTarget, pending actionability, repeated tools, and target arguments.
3. The approved tool executes through the existing orchestrator.
4. `record_tool_result(...)` parses any actionability markers from the tool result.
5. If the tool result created a desktop observe-required pending state, the runtime immediately triggers auto observe recovery.
6. The synthetic observe tool call is appended to the message history as a protocol-valid assistant tool call.
7. The observe tool executes through the same Computer Use tool path as a model-requested observe.
8. The observe result is appended as a normal tool result plus screenshot image message.
9. `record_tool_result(...)` clears the pending state because the required observe was completed.
10. The next model round sees a real screenshot and plans the next action.

Blocked user-action flow:

1. FreshTarget or resource freshness detects an old app/window/document that needs user action.
2. Runtime stores `actionability_last_block` with `block_class=user_action_required`.
3. No automatic observe recovery runs.
4. `assess_before_model(...)` tells the model to stop tools and answer the user.
5. Final answer tells the user to close the existing app/window or explicitly authorize it.

Cleanup flow:

1. Any Computer Use tool use sets `computer_use_used_this_run=true`.
2. Normal final answer, `max_turns`, `stop_event`, exception, or acceptance timeout all enter cleanup.
3. Cleanup releases lock, clears abort/permission state, clears active target state where appropriate, and emits an audit event.
4. Residual owned windows/processes are reported; user-owned windows are not closed automatically.

## Implementation Tasks

### 1. Add pure auto-recovery helpers

- [ ] Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\actionability_recovery.py`.
- [ ] Define a dataclass `ActionabilityRecoveryPlan` with fields:
  - `should_recover: bool`
  - `tool_name: str`
  - `arguments: dict[str, Any]`
  - `reason: str`
  - `recovery_key: str`
  - `max_attempts: int`
- [ ] Implement `build_desktop_observe_recovery_plan(pending: dict[str, str], runtime_state: dict[str, Any] | None) -> ActionabilityRecoveryPlan`.
- [ ] Recovery is allowed only when all conditions are true:
  - `pending["marker"] == "OPENHARNESS_DESKTOP_ACTION_REQUIRED"`
  - `pending["actionability_kind"] == "desktop_observe_before_action"`
  - `pending["next_required_tool"]` normalizes to `observe`
  - `pending["next_required_action"]` is missing or equals `get_window_state`
  - `pending["target_ref"]` is present when target binding is required
  - no `user_action_required` block is active
  - attempt count for this recovery key is below `max_attempts`
- [ ] Build observe arguments as:
  - `{"action": "get_window_state", "reason": "auto_recover_observe_before_action"}`
  - include `target_ref` if present in pending
  - include `confirm_desktop_control=True` only if existing tool schema already accepts it; otherwise omit it.
- [ ] Implement `record_recovery_attempt(runtime_state, recovery_plan)` to increment a runtime counter.
- [ ] Implement `clear_recovery_attempts_for_pending(runtime_state, recovery_key)` after observe succeeds or pending clears.
- [ ] Keep this file free of Win32 calls; it only decides whether to synthesize a tool call.

### 2. Preserve user-action blocks as hard stops

- [ ] Update `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\actionability_state.py`.
- [ ] Add any low-sensitive runtime fields needed for recovery attempt audit only if they must be parsed from tool output. Prefer keeping attempt counts in internal `runtime_state` keys instead of marker text.
- [ ] Ensure `DESKTOP_USER_ACTION_REQUIRED_MARKER` and `DESKTOP_RESOURCE_USER_ACTION_REQUIRED_MARKER` never become auto-recoverable pending states.
- [ ] Add a helper `actionability_user_action_block_active(runtime_state)` if needed so recovery code can avoid duplicating block logic.
- [ ] Do not weaken `pending_actionability_argument_mismatch(...)` or existing `target_ref` enforcement.

### 3. Add protocol-valid synthetic tool-call injection

- [ ] Update `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\agent.py`.
- [ ] Import `ActionabilityRecoveryPlan` and `build_desktop_observe_recovery_plan(...)`.
- [ ] Add a small private helper near the tool-loop methods:
  - `_build_synthetic_recovery_tool_call(recovery_plan: ActionabilityRecoveryPlan) -> ToolCall`
  - It creates a `ToolCall` with name `mcp__computer-use__observe` when that tool is loaded, otherwise `observe` only if the current tool catalog exposes that name.
  - It uses a stable generated call id prefix such as `call_auto_observe_`.
- [ ] Add a private helper:
  - `_append_synthetic_assistant_tool_call(messages, recovery_tool_call)`
  - It appends `message_builders_from_core.assistant_message_to_dict(ModelMessage(text="", tool_calls=[recovery_tool_call]))`.
  - This is required so the later tool result has a matching assistant tool call and does not break model API protocol.
- [ ] Insert the recovery hook after a real Computer Use tool result has been recorded and appended to `messages`, near current `agent.py` line 646 to line 658.
- [ ] The hook must:
  - read `get_pending_actionability(compact_runtime_state)`
  - build a recovery plan
  - append the synthetic assistant tool-call message
  - execute the observe call through `execute_tool_calls_from_orchestrator(self, [recovery_tool_call])`
  - offload long output with `_offload_tool_output_if_needed(...)`
  - call `record_tool_result(recovery_tool_call, context_recovery_output, task_state, compact_runtime_state)`
  - save `task_state`
  - emit `tool_use_seen`, `tool_call_started`, `tool_call_completed`, `tool_result_seen`, and a new `computer_use_auto_recovery_observe` event
  - append image-aware tool result messages using `tool_result_messages_to_dicts(...)` with raw output as `image_source_output`
  - record Computer Use trace entries for the synthetic call and result
- [ ] The hook must not run if the just-finished tool was itself the same recovery observe and pending cleared successfully.
- [ ] The hook must run at most once per newly created pending state by default; allow `max_attempts=2` only for transient observe tool failure.

### 4. Make observe-required recovery visible in logs and final evidence

- [ ] Update `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\runtime_trace.py` if needed.
- [ ] Add trace payload fields:
  - `auto_recovery=true`
  - `recovery_reason=observe_before_action_required`
  - `target_ref`
  - `recovery_attempt`
  - `screenshot_returned_to_model`
- [ ] Ensure final Computer Use evidence summary can mention `auto_observe_recovery=true` when recovery happened.
- [ ] Keep the final answer concise; do not expose raw window titles unless already sanitized.

### 5. Harden turn cleanup lifecycle

- [ ] Inspect current `_run_computer_use_turn_cleanup_if_needed(...)` implementation in `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\core\agent.py`.
- [ ] Verify it calls `cleanup_computer_use_mcp_v2_turn(...)` from `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\inferred_ant_mcp\runtime.py`.
- [ ] Ensure cleanup runs for:
  - final answer
  - `stop_event`
  - `max_turns`
  - exception
  - model context overflow failure
  - acceptance controller timeout
- [ ] Update `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\app\interactive.py` only if `/computer stop`, `exit`, or `quit` can bypass cleanup.
- [ ] Do not close user-owned windows automatically.
- [ ] Owned-resource cleanup may close only resources that the runtime can prove are agent-owned.

### 6. Keep app behavior generic

- [ ] Review `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\controller.py`.
- [ ] Ensure the recovery path does not branch on `notepad`, `mspaint`, `paint`, or any other specific app name.
- [ ] Ensure `open_application` still returns user-action-required for old windows when FreshTarget cannot prove a new target.
- [ ] Ensure single-instance and unknown apps remain blocked by default unless explicit user authorization exists.
- [ ] Ensure multi-target tasks keep separate `target_ref` values and do not let recovery observe the wrong target.

### 7. Add failing-first unit tests

- [ ] Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_actionability_auto_observe_recovery.py`.
- [ ] Test `build_desktop_observe_recovery_plan(...)` returns a recovery plan for:
  - marker `OPENHARNESS_DESKTOP_ACTION_REQUIRED`
  - `actionability_kind=desktop_observe_before_action`
  - `next_required_tool=mcp__computer-use__observe`
  - `next_required_action=get_window_state`
  - `target_ref=cu-target-test`
- [ ] Test it refuses recovery for:
  - user-action-required block
  - resource-user-action-required block
  - missing `target_ref` when target binding is required
  - non-observe pending tools
  - recovery attempt count over max
- [ ] Create `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_agent_auto_observe_recovery_loop.py`.
- [ ] Use a fake model and fake tool executor to simulate:
  - first tool output returns `observe_before_action_required`
  - runtime auto-executes observe
  - observe output clears pending
  - next model call receives screenshot/image-capable tool result context
- [ ] Assert the model is not responsible for manually calling observe in this test.
- [ ] Assert the synthetic observe has a matching assistant tool-call message before its tool result.
- [ ] Create or update cleanup tests to prove cleanup fires on `max_turns`, exception, and user stop.

### 8. Add acceptance controller scenarios

- [ ] Add a visible-terminal scenario file:
  - `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\computer_use_auto_observe_recovery_paint_visible_terminal.json`
- [ ] Scenario step 1 input:
  - `/computer use --full`
- [ ] Scenario step 2 input:
  - `请使用本机真实画图软件，打开一个新的空白画布，先观察窗口，再用鼠标在画布上画一条黑色横线，最后不要使用 PowerShell、Python 或命令行写文件；如果动作被要求先观察，必须继续使用真实 Computer Use 工具完成观察和动作。完成后最后一行输出：COMPUTER_USE_AUTO_OBSERVE_RECOVERY_OK real_paint_used=true auto_observe_recovery=true low_level_event_count_gt_zero=true`
- [ ] The scenario must verify terminal output contains:
  - `COMPUTER_USE_AUTO_OBSERVE_RECOVERY_OK`
  - `real_paint_used=true`
  - `auto_observe_recovery=true`
  - `low_level_event_count`
- [ ] Add a negative visible-terminal scenario for old-window blocking:
  - Launch Paint manually before the run.
  - Ask the agent to use Paint without authorizing the existing window.
  - Verify it asks the user to close or authorize the existing window and does not send low-level events.
- [ ] Acceptance controller must send `/computer stop` during teardown if the scenario fails or times out.

### 9. Verification commands

- [ ] Run focused unit tests:

```powershell
python -m pytest learning_agent/tests/test_actionability_auto_observe_recovery.py -v
python -m pytest learning_agent/tests/test_agent_auto_observe_recovery_loop.py -v
```

- [ ] Run relevant existing regression tests:

```powershell
python -m pytest learning_agent/tests/test_fresh_target_user_action_required_convergence.py -v
python -m pytest learning_agent/tests -k "computer_use or actionability or fresh_target or cleanup" -v
```

- [ ] Run syntax validation:

```powershell
python -m compileall learning_agent/core learning_agent/computer_use_mcp_v2 learning_agent/app
```

- [ ] Sync CodeGraph after code changes:

```powershell
codegraph sync "H:\codexworkplace\sofeware\OpenHarness-main"
codegraph status "H:\codexworkplace\sofeware\OpenHarness-main"
```

- [ ] Run visible terminal acceptance through the acceptance controller:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\controller.ps1" -ScenarioPath "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\computer_use_auto_observe_recovery_paint_visible_terminal.json"
```

- [ ] If the environment cannot open, observe, and type into the real visible terminal window, do not claim completion. Say exactly:

```text
真实可见终端交互验收未完成，不能声明开发完成。
```

## Success Criteria

- A desktop action that returns `observe_before_action_required` is followed by a bounded runtime-owned observe, not by repeated `open_application` retries.
- The synthetic observe is protocol-valid: assistant tool call first, matching tool result second.
- The observe result returns model-visible screenshot evidence.
- Pending actionability clears after successful observe.
- User-action-required FreshTarget blocks are not auto-recovered.
- Old existing windows are still refused unless explicitly authorized.
- Multi-app tasks do not lose `target_ref` boundaries.
- No implementation branch is app-specific to Notepad or Paint.
- Cleanup runs on normal completion, stop, failure, timeout, and max-turn stop.
- Unit tests and visible-terminal acceptance both pass before the work is declared complete.

## Stop Conditions

- Stop and report if the current tool loop cannot safely append a synthetic assistant tool call before a synthetic tool result.
- Stop and report if the Computer Use observe tool is not available in the active tool pool after `/computer use --full`.
- Stop and report if the recovery observe would need to bypass TargetLease or FreshTarget checks.
- Stop and report if acceptance controller cannot perform real visible-terminal interaction on the user's machine.

## Notes For The Implementing Agent

- Follow `H:\codexworkplace\sofeware\OpenHarness-main\AGENTS.md`: every new or modified code line must include clear Chinese comments explaining intent and consequence.
- For every modified code file, save a copy of the modified code and Chinese comments under `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\test`.
- Use CodeGraph before reading or editing related source files.
- Use failing-first tests before implementation.
- Do not call the work complete until code changes, automated tests, and real visible-terminal acceptance all pass.
