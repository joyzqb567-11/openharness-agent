# Desktop GUI Shell V2 Agent Adapter Mapping

## Purpose

This document records the CodeGraph-based mapping for connecting the desktop GUI shell to the real OpenHarness agent/harness runtime later in V2-Trust.

V2-Core intentionally uses `FakeStreamingGuiAgentAdapter` first. That keeps the GUI protocol, stream reducer, recovery logic, and visible shell deterministic before real model calls, MCP startup, browser automation, Computer Use, and OAuth state enter the path.

## CodeGraph Investigation

Investigation date: 2026-06-25.

CodeGraph project path: `H:\codexworkplace\sofeware\OpenHarness-main`.

Queries used:

- `GUI prompt to real agent harness entrypoint cancellation status events permission flow task registry command queue run loop agent adapter mapping`
- `LearningAgent run method ask_permission StatusEventStore RuntimeCommandQueue HarnessRunner agent_executor HarnessQueue run_task_record cancellation stop_event`
- `run_agent_with_harness_session event_callback status events model loop tool calls cancellation stop_event RuntimeCommandQueue StatusEventStore`
- `LearningAgent run_events AgentEvent event_type run_started run_completed tool_started tool_finished permission denied model stream delta`

## Real Runtime Candidate

Primary future entrypoint:

- `learning_agent/core/agent.py`
- `LearningAgent.run(user_input, max_turns=None, event_callback=None, conversation_history=None)`

CodeGraph showed that `LearningAgent.run(...)` delegates to:

- `learning_agent/runtime/session_runtime.py`
- `run_agent_with_harness_session(agent, user_input, max_turns=None, event_callback=None, conversation_history=None)`

This is the best future adapter target because it already sits behind the real agent loop, durable runtime queue, harness run state, and event callback surface.

## Harness Session Flow

`run_agent_with_harness_session(...)` currently:

- creates `HarnessStore(agent.workspace / "memory" / "harness")`;
- creates `RuntimeCommandQueue(agent.workspace / "memory" / "runtime")`;
- enqueues the GUI/user prompt as a durable runtime command;
- drains queued runtime commands into model-visible input;
- creates a `HarnessRun` with an `interactive_turn` stage;
- calls `agent.run_events(...)`;
- mirrors each `AgentEvent` into harness events;
- forwards each `AgentEvent` to `event_callback` if one is provided;
- saves `run_completed` or `run_failed` state back into the harness store.

Implication for GUI V2:

The future real adapter should not reinvent a harness loop. It should instantiate/configure `LearningAgent`, call `agent.run(...)` or `run_agent_with_harness_session(...)`, and convert `event_callback` events into GUI V2 events.

## Agent Event Source

`LearningAgent.run_events(...)` is the real model/tool event generator.

CodeGraph showed these important facts:

- it creates a `StatusEventStore(self.workspace / "memory" / "status")`;
- its local `emit(event_type, payload)` writes transcript events, transcript v2 entries, and status events;
- `emit(...)` calls `status_event_store.append(event_type, {"sequence": sequence, "payload": payload}, session_id=session_id, run_id=run_id, turn_id=transcript_turn_id)`;
- it yields `AgentEvent` objects to callers;
- it emits `run_started`;
- it emits `turn_accepted`;
- it emits `run_completed` with a payload containing final text;
- it emits `run_failed` on failure paths.

Implication for GUI V2:

The bridge can consume real runtime events through either `event_callback` or the existing `StatusEventStore`. The adapter boundary should prefer `event_callback` for low-latency streaming and keep `StatusEventStore` as the recovery/audit source.

## Event Mapping Draft

Initial `AgentEvent -> GUI V2` mapping for V2-Trust:

| Real event source | GUI V2 event | Notes |
| --- | --- | --- |
| `run_started` | `turn_started` | Marks visible turn start. |
| `turn_accepted` | `turn_started` or diagnostic payload | Useful for recovery/checkpoint, not necessarily a user-visible duplicate. |
| model text stream event | `message_delta` | Needs a narrow test around `stream_chat_events`/`ModelStreamEvent` before real wiring. |
| `run_completed` | `message_completed` | Payload text becomes `final_text`. |
| `run_failed` | `turn_failed` | Failure text becomes user-visible error message. |
| tool start/hook event | `tool_started` | Needs V2-Trust contract tests for exact payload. |
| tool result/hook event | `tool_finished` | Must redact sensitive args before UI display. |
| permission request path | `permission_requested` | Requires async GUI approval bridge, not just sync `ask_permission`. |
| permission decision path | `permission_answered` | Must be recorded in both GUI and runtime audit trail. |
| stop/cancel result | `turn_cancelled` | Should be driven by `stop_event` or runtime command queue cancellation. |

## Cancellation Mapping

`LearningAgent.__init__(...)` accepts `stop_event: threading.Event | None`.

`run_events(...)` checks `_stop_requested()` and can return a stopped result before continuing. Task sub-agents also use stop events in their `TaskRun` records.

Future GUI real adapter should:

- create one `threading.Event` per GUI turn;
- pass that event into `LearningAgent(..., stop_event=cancel_event)`;
- set the event when `/v1/gui/turns/{turn_id}/cancel` or the V2 cancel path fires;
- convert the resulting stopped/cancelled event into `turn_cancelled`;
- keep the existing `GuiRunManager.cancel_events` as the GUI-level source of cancellation intent.

## Permission Mapping

Current real agent construction receives `ask_permission: Callable[[str], bool]`.

For the GUI, a synchronous terminal-style `ask_permission(...)` is not enough. The real adapter should wrap it with a GUI permission handshake:

- call `GuiRunManager.record_permission_required(...)` or a future `gui_permissions.py` helper;
- emit `permission_requested`;
- wait for GUI `approve` or `deny`;
- return `True` or `False` to the real agent;
- emit `permission_answered`;
- fail or continue the run according to the decision.

This is intentionally left for V2-Trust because it changes real runtime permission behavior and can trigger Layer C.

## Status And Recovery Mapping

There are two recovery sources:

- GUI-local state in `memory/gui_bridge/state.json`;
- real runtime/harness/status facts in `memory/status`, `memory/harness`, and `memory/runtime`.

V2-Core currently keeps GUI-local fake adapter state deterministic.

V2-Trust should define one reconciliation rule:

- the real agent/harness event stream is the durable fact source for real runs;
- GUI-local state is a projection for fast renderer recovery;
- after crash/restart, GUI should replay `StatusEventStore` and session summaries before trusting stale local projection.

## Why The Real Adapter Is Feature-Flagged For Now

The current implementation includes `DefaultHarnessGuiAgentAdapter(enabled=False)`.

It returns `adapter_unavailable` on explicit real-harness prompts and performs no runtime import at module import time.

Reasons:

- importing/configuring `LearningAgent` can start MCP setup logic depending on registry state;
- real model calls are not deterministic enough for V2-Core golden traces;
- real browser and Computer Use paths have visible permission and safety implications;
- GUI permission handoff must be designed before bridging sync `ask_permission`;
- Layer C terminal acceptance may be triggered once real agent runtime, MCP routing, browser automation, Computer Use, or backend permission enforcement changes.

## V2-Trust Implementation Checklist

Before enabling a real harness adapter:

- Add contract tests for `AgentEvent -> GUI V2` mapping.
- Add tests for cancellation through `stop_event`.
- Add tests for GUI permission approve/deny wrapping `ask_permission`.
- Add tests that real adapter imports are lazy and do not run at module import time.
- Add tests that token, local secret paths, and raw tracebacks are not emitted to GUI payloads.
- Add a visible GUI acceptance case for one real or controlled fake-real prompt.
- Record Layer C trigger decision.

## Current Task 3 Result

Implemented in V2-Core:

- `learning_agent/app/gui_agent_adapter.py`
- `FakeStreamingGuiAgentAdapter`
- `DefaultHarnessGuiAgentAdapter(enabled=False)`
- `GuiRunManager` default path now uses fake streaming adapter when no explicit V1 `answer_runner` is injected.
- Adapter events are persisted into `StatusEventStore` as V2 event kinds such as `message_delta`.
- V1 lifecycle events such as `gui_turn_completed` are still emitted for compatibility.

Not implemented in V2-Core:

- real model invocation from GUI;
- real MCP/tool/browser/Computer Use execution from GUI adapter;
- async GUI permission bridge into `ask_permission`;
- token-level model streaming from `ModelStreamEvent`.
