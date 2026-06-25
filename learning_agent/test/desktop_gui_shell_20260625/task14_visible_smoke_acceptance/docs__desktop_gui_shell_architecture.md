# Desktop GUI Shell Architecture

The OpenHarness desktop shell lives in `apps/desktop`.

The backend remains in `learning_agent`.

The bridge boundary is `learning_agent/app/gui_bridge.py`.

The renderer never reads backend memory files directly.

The renderer uses bridge endpoints and event polling to update UI state.

V1 readiness means the GUI prompt matrix passes, not only that the window opens.

`learning_agent/start_oauth_agent.bat` is the conditional backend-agent terminal gate. It is not the visible desktop GUI acceptance gate.

## Runtime Boundary

The desktop GUI is a client of the backend bridge. It should treat the backend as the source of truth for project metadata, sessions, turn lifecycle, browser provider status, permission decisions, and event history.

The GUI may optimistically render local interaction state when useful, but durable state must be confirmed through bridge responses or bridge events.

## Layered Acceptance

Layer A is visible desktop GUI acceptance. It proves that the Electron shell opens and the user can inspect sidebar, thread panel, composer, status timeline, browser provider panel, permissions, cancel, retry, and resume behavior.

Layer B is automated contract and build acceptance. It proves the backend bridge tests, frontend tests, lint, and production build pass.

Layer C is the conditional backend-agent terminal gate. It is required only when a task changes agent runtime behavior, MCP routing, model calls, browser automation, Computer Use, or backend permission enforcement.

Layer C does not replace Layer A.

## V1 Bridge Behavior

The GUI bridge is intentionally bridge-first:

- `POST /v1/gui/messages` creates a GUI turn and appends lifecycle events.
- `GET /v1/gui/events` is the renderer polling source of truth.
- `POST /v1/gui/turns/{turn_id}/cancel` requests cancellation through the backend manager.
- `POST /v1/gui/turns/{turn_id}/retry` creates a linked retry turn.
- `POST /v1/gui/sessions/{session_id}/resume` restores persisted GUI messages.
- `GET /v1/gui/sessions` returns GUI bridge sessions from `GuiRunManager`, so the sidebar shows conversations created in the desktop shell.
- `GET /v1/gui/browser/providers` returns provider status and degrades gracefully if the runtime snapshot is temporarily unreadable.

The renderer remains a client. It does not read `memory/`, lock files, cookies, browser storage, or backend private files directly.

## Degraded Snapshot Policy

Runtime snapshot reads can temporarily fail on Windows when lock files are unavailable.

The GUI bridge must not traceback in that case.

Current degraded payload rules:

- Bootstrap returns `snapshot_degraded: true` and a safe empty snapshot.
- Browser provider status returns `degraded: true`, empty `providers`, and a generic error string.
- Degraded responses must not expose local filesystem paths.

This keeps the desktop shell visible and debuggable even when a runtime status file is locked.

## V1 Acceptance Result

The 2026-06-25 V1 vertical slice has visible GUI evidence for launch, prompt completion, status timeline, tool card, browser provider panel, permission approve/deny, cancel, retry, failure text, session sidebar, and resume.

The remaining prompt-matrix items are follow-up GUI polish and backend integration work:

- Safety refusal rendered as a first-class assistant message.
- Multiline Chinese persistence and Shift+Enter caret behavior.
- In-thread polished renderer errors for token rejection and unknown routes.

Those items are recorded in `apps/desktop/tests/gui-prompt-matrix.md` instead of being silently marked complete.
