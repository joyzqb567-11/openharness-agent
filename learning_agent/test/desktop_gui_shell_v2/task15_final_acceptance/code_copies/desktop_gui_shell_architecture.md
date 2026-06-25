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

Layer B release gate command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\release-gate.ps1
```

## Windows Packaging And Startup

Task 13 adds a Windows development packaging flow, not a signed installer.

The packaging command is:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\package-windows.ps1
```

The script runs the production desktop build, creates `apps/desktop/dist/package-windows/openharness-desktop-windows-dev`, writes `package-manifest.json`, and writes `learning_agent/test/desktop_gui_shell_v2/package_summary.txt`.

The package artifact is intentionally explicit about its boundary: it contains the built Electron main process, built renderer assets, and package metadata. It does not claim to be a signed Windows installer.

Startup is split into two scripts:

- `apps/desktop/scripts/start-backend.ps1` starts the GUI bridge and prints bridge URL plus evidence folder.
- `apps/desktop/scripts/start-desktop-dev.ps1` starts the renderer dev server and Electron shell, then prints bridge URL, renderer URL, and evidence folder.

Both startup scripts fail early with a clear message if their owned port is already occupied. The backend script owns bridge port `8776`; the desktop dev script owns renderer port `5177`.

## V2 Acceptance Result

The 2026-06-25 V2 automated release gate passes on branch `codex/desktop-gui-shell-v1`.

Layer B evidence:

- Python GUI tests: 58 tests OK.
- Frontend lint: passed.
- Frontend Vitest: 45 tests passed.
- Frontend production build: passed.
- Visible GUI smoke instructions: generated.
- Layer C trigger decision: printed.

Layer A visible Electron smoke evidence is archived in `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/`.

The observed visible Electron flows include Chinese streaming completion, multiline Chinese prompt completion, tool trace card rendering, permission approve, cancel, retry, diagnostics panel visibility, and latest-session restore after launch.

Current limitation: not every V2 visible GUI matrix row is checked yet. Negative/error rows such as safety refusal, invalid-token GUI error, unknown-route GUI error, and bridge-offline banner remain listed in `apps/desktop/tests/gui-prompt-matrix.md` until they receive their own visible-window evidence.

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
