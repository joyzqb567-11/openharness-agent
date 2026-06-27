# OpenHarness Desktop Real Agent Harness Adapter Blueprint V2

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` before implementing this blueprint task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking once this blueprint is converted into execution work.

**Goal:** Turn OpenHarness Desktop GUI from a real-model chat shell into a Codex-style agent workbench by connecting it to the real `LearningAgent` run loop in `learning_agent/core/agent.py`.

**Architecture:** Preserve the proven Direct SSE chat route, then add a separate `agent_harness` route. The first deliverable is not a full tool-enabled workbench; it is one tiny real vertical slice: GUI prompt -> `RealHarnessGuiAgentAdapter` -> `LearningAgent.run(...)` -> `LearningAgent.run_events(...)` -> GUI `message_completed`. Tooling, permissions, recovery, and Computer Use are added only after that path is observable and testable.

**Tech Stack:** Electron, React, TypeScript, Vite, Python standard-library HTTP bridge, `LearningAgent.run_events()`, `run_agent_with_harness_session()`, `StatusEventStore`, `HarnessStore`, GUI V2 event protocol, pytest/unittest, Vitest, PowerShell launch and release gates.

---

## 0. V2 Upgrade Summary

This V2 blueprint upgrades the original plan according to the engineering review:

- Start with a Phase 0 evidence spike before adding new runtime surface area.
- Make model factory compatibility a blocking question, not an implementation detail.
- Build the first real agent slice without tools, shell, MCP, file writes, or Computer Use.
- Derive GUI event mapping from recorded `AgentEvent` JSONL traces, not from guessed event names.
- Move the GUI permission handshake before any write-capable action.
- Treat Computer Use as the final controlled phase, because it touches the real desktop.
- Add explicit stop conditions so a long agent task does not keep building on a false assumption.

The important product judgment stays the same: if Desktop GUI never reaches `core/agent.py`, it is a chat shell, not a mature agent workbench.

## 1. Current Non-Negotiable Facts

These facts are already true in the current project and must not be regressed:

- The Electron/React shell exists in `apps/desktop`.
- The local authenticated bridge exists in `learning_agent/app/gui_bridge.py`.
- The current GUI adapter exists in `learning_agent/app/gui_agent_adapter.py`.
- Real OpenAI/ChatGPT OAuth Direct SSE replies are working.
- GUI context compaction through `learning_agent/app/gui_context.py` is working.
- Real model observability events are already visible in GUI.
- The one-click OAuth launcher `start_openharness_desktop_oauth.bat` is the preferred manual GUI startup path.
- `DefaultHarnessGuiAgentAdapter(enabled=False)` is still a disabled shell and returns `adapter_unavailable`.
- The Direct SSE path calls `ChatGptCodexSseClient.stream_responses(..., tools=None, ...)`, so it is a real model chat path but not the full OpenHarness agent loop.

The missing real-agent path is:

```text
GUI prompt
  -> RealHarnessGuiAgentAdapter
  -> LearningAgent.run(...)
  -> run_agent_with_harness_session(...)
  -> LearningAgent.run_events(...)
  -> AgentEvent stream
  -> GUI V2 event stream
```

## 2. Product Principle

Desktop GUI should become an agent cockpit, not a second agent brain.

That means:

- The renderer never imports `LearningAgent`.
- The renderer never reads backend memory files directly.
- The renderer consumes GUI V2 events only.
- `core/agent.py` remains the agent loop source of truth.
- The new adapter translates between GUI concepts and core agent concepts.

This is the "Iron Man suit" shape: the user stays in control, the GUI shows what the agent is doing, and the core loop does the real work.

## 3. Runtime Modes

### Mode A: `chat_direct_sse`

Purpose:

- Normal text chat.
- Context recall.
- OAuth model health checks.
- Low-risk model interaction.

Capabilities:

- Real model streaming.
- Model call status.
- GUI context compaction.
- Provider and model settings.

Limits:

- No tool loop.
- No MCP.
- No file edits through `LearningAgent`.
- No Computer Use.
- No harness stage execution.

### Mode B: `agent_harness`

Purpose:

- Codex-style agent work.
- Code editing after permission.
- Tool execution after event mapping is proven.
- MCP usage after permission is proven.
- Computer Use after controlled safety gates.
- Long-task harness and resumable runs.

Capabilities:

- `LearningAgent.run(...)`.
- `run_agent_with_harness_session(...)`.
- `LearningAgent.run_events(...)`.
- Tool events.
- Permission events.
- Cancellation through `stop_event`.
- Durable status, harness, runtime queue, transcript, and turn ledger.

Safety rule:

- The mode starts behind a feature flag.
- It does not silently fall back to fake streaming.
- It does not expose write, shell, MCP, or Computer Use until GUI permission is shipping.

## 4. Evidence-First Delivery Shape

The implementation must move through these phases in order:

```text
Phase 0: Model factory and AgentEvent probe
Phase 1: Minimal real core loop in GUI, no tools
Phase 2: Event mapper from recorded JSONL traces
Phase 3: One read-only tool trace
Phase 4: GUI permission handshake for write-capable actions
Phase 5: Cancellation and recovery hardening
Phase 6: Controlled Computer Use agent mode
```

The first two phases are intentionally small. A tiny real loop that works is more valuable than a large adapter surface that has never entered `LearningAgent.run_events()`.

### Mandatory Visible GUI Acceptance Rule

Every visible GUI acceptance in this blueprint is a hard gate:

User-facing requirement in Chinese:

> 验收需要使用肉眼可见的真实 GUI 界面进行验收，使用 `computer-use` 技能确认和验证。如果验收时出现 bug 或发现 bug，请使用 `superpowers:systematic-debugging` 技能，修复 bug，并重新测试；测试通过后继续执行下一个任务。

- Acceptance must use the real, human-visible OpenHarness Desktop GUI window, not only backend API calls, screenshots from hidden runs, unit tests, or simulated renderer state.
- Acceptance must use the `computer-use` skill to observe and confirm the visible GUI state, including the message timeline, right inspector events, runtime path, permission prompts, and final answer where applicable.
- If any bug, visual defect, stuck state, wrong event, missing permission prompt, layout break, or unexpected behavior appears during acceptance, stop the current task immediately.
- When a bug appears, use the `superpowers:systematic-debugging` skill before fixing: reproduce the issue, gather evidence, identify the root cause, implement the smallest root-cause fix, and then retest.
- After a fix, rerun the same visible GUI acceptance with `computer-use` and only continue to the next blueprint task after the visible GUI acceptance passes.
- Do not mark a phase complete when only automated tests pass; the phase is complete only when its required visible GUI acceptance also passes.

## 5. Phase 0: Model Factory And AgentEvent Probe

Goal:

- Prove whether GUI provider credentials can create a `ChatModel` that `LearningAgent` can use.
- Record the actual `AgentEvent` stream from a controlled run.
- Replace guessed event names with evidence.

Files to inspect before implementation:

- `learning_agent/app/gui_agent_adapter.py`
- `learning_agent/app/gui_bridge.py`
- `learning_agent/app/gui_context.py`
- `learning_agent/runtime/session_runtime.py`
- `learning_agent/core/agent.py`
- existing model adapter files under `learning_agent/models/`
- existing OAuth provider files under `learning_agent/app/`

Artifacts to create during implementation:

- `learning_agent/test/gui_agent_harness_probe/agent_events_smoke.jsonl`
- `learning_agent/test/gui_agent_harness_probe/model_factory_probe_result.json`
- `learning_agent/test/gui_agent_harness_probe/redaction_probe_result.json`

Required probe behavior:

- Run one controlled `LearningAgent` call outside the GUI with the same provider/model credentials path the GUI would use.
- Capture each emitted `AgentEvent` as JSONL after redacting tokens and absolute sensitive paths.
- Record whether the model path used `CodexOAuthChatModel` or a new thin GUI OAuth `ChatModel` adapter.
- Record whether the call reached `LearningAgent.run_events()`.
- Record final answer text and terminal status.

Blocking questions:

- Can the GUI OpenAI OAuth provider state create a `ChatModel` without copying Direct SSE request code?
- Does the selected `ChatModel` emit internal model messages that preserve tool calls?
- Does `LearningAgent.run(...)` accept enough hooks for GUI event callback, stop event, and permission wrapper without editing `core/agent.py`?
- Which `AgentEvent` names and payload shapes are actually emitted?

Stop conditions:

- If no compatible `ChatModel` can be created, stop and document the required model adapter work before building GUI runtime UI.
- If the event stream contains sensitive payloads that cannot be safely redacted centrally, stop and build redaction first.
- If entering `LearningAgent.run_events()` requires a risky `core/agent.py` rewrite, stop and propose a smaller public hook instead.

Validation commands:

```powershell
python -m py_compile learning_agent\core\agent.py learning_agent\runtime\session_runtime.py
python learning_agent\scripts\assert_no_real_provider_secret_leaks.py
```

Exit criteria:

- There is a real JSONL event trace from a controlled `LearningAgent` run.
- The trace proves whether the plan can reuse an existing `ChatModel` or needs a thin GUI OAuth adapter.
- The next phase has actual event names to map.

## 6. Phase 1: Minimal Real Core Loop In GUI, No Tools

Goal:

- Make one GUI Agent-mode prompt enter the real core loop and return a visible answer.

Strict scope:

- No file writes.
- No shell.
- No MCP.
- No Computer Use.
- No permission prompts yet.
- No broad recovery system yet.

New backend files:

```text
learning_agent/app/gui_harness_adapter.py
learning_agent/app/gui_model_factory.py
```

Backend responsibilities:

- Lazily import `LearningAgent` inside the harness adapter run path.
- Build a `ChatModel` through `gui_model_factory.py`.
- Create one `threading.Event` per GUI turn for future cancellation.
- Emit `runtime_path` with `runtime=agent_harness`.
- Call `LearningAgent.run(...)` through a narrow adapter boundary.
- Convert final completion into the existing `GuiAgentRunResult`.
- Refuse agent mode with `adapter_unavailable` when the feature flag is disabled.

Feature flags:

```text
OPENHARNESS_GUI_AGENT_RUNTIME=disabled|enabled
OPENHARNESS_GUI_AGENT_DEFAULT_MODE=chat|agent
OPENHARNESS_GUI_AGENT_PERMISSION_TIMEOUT_SECONDS=300
```

Rules:

- Missing `OPENHARNESS_GUI_AGENT_RUNTIME` means disabled.
- Agent mode disabled path returns a clear GUI event and does not fake success.
- Agent mode enabled path must prove it reached `LearningAgent.run_events()`.
- Direct SSE chat remains unchanged.

Backend tests:

```text
learning_agent/tests/test_gui_harness_adapter_contract.py
learning_agent/tests/test_gui_agent_model_factory.py
```

Required assertions:

- Disabled agent mode returns stable `adapter_unavailable`.
- Enabled agent mode emits `runtime_path runtime=agent_harness`.
- The adapter imports core lazily inside the run path.
- The model factory returns a structured unsupported-provider error instead of a raw exception.
- Direct SSE tests still pass with agent runtime disabled.

Visible GUI smoke:

This smoke must follow the Mandatory Visible GUI Acceptance Rule.

```text
Prompt: 请只回复 AGENT_HARNESS_SMOKE_OK
Mode: Agent
Expected GUI events:
  runtime_path runtime=agent_harness
  turn_started
  message_completed
  gui_turn_completed
Expected visible answer:
  AGENT_HARNESS_SMOKE_OK
```

Exit criteria:

- One real GUI turn reaches `LearningAgent.run_events()`.
- The visible answer appears in the existing thread timeline.
- Direct SSE chat still works.
- No write-capable action is exposed.

## 7. Phase 2: Event Mapper From Recorded JSONL Traces

Goal:

- Build GUI event mapping from actual core event traces.

New backend file:

```text
learning_agent/app/gui_agent_event_mapper.py
```

Trace fixture directory:

```text
learning_agent/tests/fixtures/gui_agent_traces/
```

Initial trace files:

```text
no_tool_success.jsonl
model_failure.jsonl
cancel_mid_stream.jsonl
permission_denied.jsonl
read_only_tool_success.jsonl
```

Mapper responsibilities:

- Convert one `AgentEvent` into zero, one, or more GUI V2 events.
- Redact sensitive fields before events leave the backend.
- Preserve `session_id`, `run_id`, and `turn_id`.
- Normalize stable frontend event kinds.
- Keep unknown safe events as diagnostics instead of crashing the GUI.

Initial mapping policy:

| Core evidence | GUI V2 event | Rule |
| --- | --- | --- |
| Run starts | `turn_started` | Emit once per visible turn. |
| Runtime route chosen | `runtime_path` | Must include `runtime=agent_harness`. |
| Model call starts | `model_call_started` | Reuse current model status UI shape. |
| First model text arrives | `model_first_delta` or `message_delta` | Use actual trace payload shape. |
| Final answer arrives | `message_completed` | Use safe final text. |
| Run failure arrives | `turn_failed` | Emit stable error code and safe message. |
| Cancellation observed | `turn_cancelled` | Only when user cancellation flag is set. |
| Context compact event arrives | `context_budget` or `compact_completed` | Never emit raw compact summary. |
| Unknown safe event arrives | `agent_diagnostic` | Redacted, capped payload. |

Redaction rules:

- Hide raw access tokens, refresh tokens, ID tokens, authorization codes, bearer headers, API keys, PKCE verifiers, and secret refs.
- Replace absolute workspace paths with project-relative paths when possible.
- Cap long stdout and stderr previews.
- Show tool names and safe summaries, not raw secret-bearing commands.

Backend tests:

```text
learning_agent/tests/test_gui_agent_event_mapper.py
```

Required assertions:

- Each fixture maps to deterministic GUI events.
- Secret-like strings are redacted.
- Unknown events do not crash mapping.
- Final answer maps to exactly one `message_completed`.

Exit criteria:

- Event mapping is driven by fixture traces.
- GUI can show a stable minimal agent timeline.
- The redaction scanner passes.

## 8. Phase 3: One Read-Only Tool Trace

Goal:

- Prove that Agent mode can show one low-risk tool call without enabling writes.

Allowed tool behavior:

- Read-only project inspection.
- No file modification.
- No shell command that mutates state.
- No MCP server startup.
- No Computer Use.

Expected GUI events:

```text
tool_started
tool_finished
message_completed
```

Frontend work:

- Extend existing trace reducer rather than creating a second side panel.
- Render tool name, status, duration, safe argument preview, and safe result summary.
- Keep the 1024x720 layout stable.

Frontend tests:

```text
apps/desktop/tests/agentTraceReducer.test.ts
apps/desktop/tests/statusInspectorAgentRun.test.tsx
```

Visible GUI smoke:

This smoke must follow the Mandatory Visible GUI Acceptance Rule.

```text
Prompt: 请列出当前项目根目录的文件名，只读，不修改任何文件。
Mode: Agent
Expected:
  runtime_path runtime=agent_harness
  tool_started for read/list behavior
  tool_finished with redacted safe summary
  message_completed with answer
  no permission bypass
```

Exit criteria:

- User can see what tool ran.
- Tool summary is safe and short.
- No write-capable path is available.

## 9. Phase 4: GUI Permission Handshake Before Write-Capable Actions

Goal:

- Make the GUI permission route real before any write, shell, MCP, or Computer Use action can ship.

Backend flow:

```text
LearningAgent asks permission
  -> RealHarnessGuiAgentAdapter.ask_permission()
  -> GuiRunManager creates GuiPermissionRequest
  -> StatusEventStore receives permission_requested
  -> React displays PermissionBanner or PermissionDialog
  -> user approves or denies
  -> bridge records decision
  -> ask_permission() unblocks
  -> LearningAgent continues or refuses
  -> StatusEventStore receives permission_answered
```

Backend files:

```text
learning_agent/app/gui_permissions.py
learning_agent/app/gui_bridge.py
learning_agent/app/gui_harness_adapter.py
```

Backend requirements:

- Permission wait has a timeout.
- Cancellation while waiting returns `False`.
- Denial returns `False`.
- Approval returns `True`.
- Repeated answers are ignored.
- Each permission request links to `session_id`, `run_id`, and `turn_id`.
- Permission text is normalized and redacted.

Frontend requirements:

- Permission banner/dialog shows action, reason, risk, and target.
- Approve and deny buttons disable while submitting.
- Answered permission requests disappear from the active prompt area but remain visible in trace/history.
- The right inspector shows recent permission decisions.

Tests:

```text
learning_agent/tests/test_gui_agent_permission_handshake.py
apps/desktop/tests/permissionDialogAgentMode.test.tsx
```

Visible GUI smoke:

This smoke must follow the Mandatory Visible GUI Acceptance Rule.

```text
Prompt: 请在工作区创建一个测试文件，内容为 AGENT_PERMISSION_OK。
Mode: Agent
Expected:
  permission_requested
  user approves
  permission_answered
  tool_started
  tool_finished
  message_completed
```

Exit criteria:

- Deny blocks the action.
- Approve allows the action.
- Cancellation while waiting denies safely.
- Write-capable action never runs without visible GUI permission.

## 10. Phase 5: Cancellation And Recovery Hardening

Goal:

- Make agent runs safe to stop and safe to recover after bridge or window restart.

Cancellation design:

```text
GuiRunManager.cancel_events[turn_id] -> threading.Event
```

Adapter behavior:

- Construct or configure `LearningAgent` with the same cancel event.
- GUI cancel endpoint sets the event.
- Cancellation maps to `turn_cancelled` when user initiated cancellation is true.
- Late cancellation after normal completion records a diagnostic event and keeps the completed answer.

Recovery rules for `agent_harness`:

- `memory/status` is the event replay source.
- `memory/harness` is the run state source.
- `memory/runtime` is the queued command source.
- GUI local state is a projection.

Startup reconciliation:

1. Load GUI bridge state.
2. Load `StatusEventStore` tail.
3. Load recent harness runs.
4. If GUI says running but harness says terminal, trust harness.
5. If harness says running but no worker owns it and lease expired, show interrupted state.
6. If facts are incomplete, show safe degraded diagnostics.

Tests:

```text
learning_agent/tests/test_gui_harness_adapter_contract.py
learning_agent/tests/test_gui_agent_recovery.py
apps/desktop/tests/agentRuntimeMode.test.tsx
```

Exit criteria:

- Cancel during a run leaves no permanently running turn.
- Restarted GUI does not show stale infinite running state.
- Completed harness run is reflected as completed in GUI.
- Interrupted run is shown as interrupted, not silently lost.

## 11. Phase 6: Controlled Computer Use Agent Mode

Goal:

- Allow mature GUI-controlled Computer Use only after permission, trace, and cancellation foundations work.

Hard safety gates:

- Computer Use remains disabled in Agent mode until Phase 4 and Phase 5 pass.
- Every mutating Computer Use action requires visible GUI permission.
- Emergency stop is visible.
- Target application and action summary are visible.
- Result is represented as a safe trace row.

Backend responsibilities:

- Reuse existing Computer Use MCP v2 permission and runtime facts.
- Map observe/action events into trace rows.
- Show lock, abort, and selected display state in the existing inspector.
- Avoid raw screenshot or private window text leakage in logs and diagnostics.

Visible acceptance:

- This acceptance must follow the Mandatory Visible GUI Acceptance Rule.
- Use `computer-use` or the existing visible GUI acceptance controller.
- Run only controlled, low-risk desktop actions.
- Store evidence in `learning_agent/test/gui_agent_harness_computer_use/`.

Exit criteria:

- User sees target app, action, risk, approval state, and result.
- No Computer Use action runs without clear permission route.
- Emergency stop behavior is visible and auditable.

## 12. Frontend UI Boundary

Composer runtime selector:

- Add `Chat` and `Agent` modes near provider/model controls.
- Hide `Agent` unless backend feature flag says it is enabled.
- Default remains `Chat` until Phase 1 visible smoke passes.

Thread timeline:

- Show agent running state.
- Show tool cards.
- Show permission cards.
- Show compact/context budget events.
- Show final answer.
- Show failure and cancellation states.

Right inspector:

- Reuse the existing `StatusInspector`.
- Extend current tabs instead of adding a second sidebar.
- Add agent run summary, harness summary, runtime queue status, tool trace, permissions, and diagnostics.

Layout rule:

- Keep 1024x720 usable.
- Do not let tool cards or permission text overflow their containers.
- Do not hide the right inspector to make new content fit.

## 13. Release Gates

Backend gate:

```powershell
python -m pytest learning_agent\tests\test_gui_harness_adapter_contract.py learning_agent\tests\test_gui_agent_event_mapper.py learning_agent\tests\test_gui_agent_permission_handshake.py learning_agent\tests\test_gui_agent_model_factory.py -q
python learning_agent\scripts\assert_no_real_provider_secret_leaks.py
python -m py_compile learning_agent\app\gui_harness_adapter.py learning_agent\app\gui_agent_event_mapper.py learning_agent\app\gui_model_factory.py
```

Frontend gate:

```powershell
npm --prefix apps/desktop test -- --run
npm --prefix apps/desktop run lint
npm --prefix apps/desktop run build
```

Visible GUI gate:

```powershell
.\start_openharness_desktop_oauth.bat
```

The visible GUI gate must follow the Mandatory Visible GUI Acceptance Rule.

Visible acceptance must prove:

- Runtime path is `agent_harness`.
- Runtime path is not `direct_sse`.
- Runtime path is not fake streaming.
- The GUI visibly receives the final agent answer.
- Any write-capable action shows a permission request first.

## 14. Risk Register

### Risk: Direct SSE Chat Regresses

Mitigation:

- Keep `chat_direct_sse` route unchanged.
- Run existing Direct SSE tests with agent feature flag disabled.

### Risk: Model Factory Blocks The Harness Path

Mitigation:

- Treat Phase 0 as blocking.
- Prefer existing `CodexOAuthChatModel` when compatible.
- Add a thin GUI OAuth token-source adapter only if compatibility evidence requires it.
- Do not copy Direct SSE request logic into the harness adapter.

### Risk: Event Mapping Is Based On Guesswork

Mitigation:

- Record JSONL traces first.
- Build mapper tests from trace fixtures.
- Keep unknown safe events as diagnostics.

### Risk: GUI Hangs On Permission

Mitigation:

- Permission waits have timeout.
- Cancellation unblocks wait.
- Denial is the safe default.

### Risk: Agent Mode Starts Tools Too Early

Mitigation:

- No write, shell, MCP, or Computer Use before GUI permission.
- Read-only tool trace comes before write-capable action.

### Risk: Two Fact Sources Fight

Mitigation:

- For agent runs, `memory/status` and `memory/harness` win.
- GUI state is a projection.
- Reconciliation rules are tested.

### Risk: Sensitive Data Leaks To Renderer

Mitigation:

- Central redaction in `gui_agent_event_mapper.py`.
- Provider secret scanner in release gate.
- Tests include token-like strings and local secret paths.

### Risk: `core/agent.py` Is Too Large To Safely Touch

Mitigation:

- Do not modify `core/agent.py` in Phase 1 unless a test proves a missing hook.
- Prefer adapter and mapper modules.
- If a core hook is required, add a small public hook with targeted tests.

## 15. Success Definition

This blueprint is successful when OpenHarness Desktop can truthfully present itself as an agent workbench:

- User can select Agent mode.
- GUI run enters `LearningAgent.run_events()`.
- Tool progress appears in the GUI.
- Permissions are handled in GUI before risky actions.
- Cancellation works.
- Harness/status facts persist and recover.
- Direct SSE chat still works.
- Real GUI acceptance proves the runtime path is `agent_harness`.

## 16. Explicit Non-Goals

This blueprint does not:

- remove Direct SSE chat;
- redesign the entire Electron shell;
- rewrite `core/agent.py`;
- enable unrestricted Computer Use by default;
- bypass provider OAuth or existing secret storage;
- make renderer read backend memory files directly;
- claim production readiness before visible GUI acceptance.

## 17. Self-Review

Spec coverage:

- The upgraded blueprint covers why `core/agent.py` must be connected, how to prove model compatibility first, how to preserve Direct SSE, how to map events from evidence, how to wire GUI permission, how to cancel and recover, how to stage Computer Use, and how to validate the final runtime path.

Placeholder scan:

- The plan avoids unresolved placeholder sections and gives each phase files, behavior, gates, and exit criteria.

Boundary consistency:

- `RealHarnessGuiAgentAdapter`, `gui_agent_event_mapper.py`, and `gui_model_factory.py` are consistently named.
- Runtime names are consistently `chat_direct_sse` and `agent_harness`.
- Durable fact sources are consistently `memory/status`, `memory/harness`, `memory/runtime`, transcript v2, and turn ledger.

Scope check:

- The work is large but cohesive: one subsystem, the real GUI-to-agent runtime bridge. Computer Use production behavior is intentionally staged after permission, trace, and cancellation foundations are proven.
