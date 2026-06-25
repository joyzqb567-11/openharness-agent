# Desktop GUI Shell V2 Acceptance

This document defines the V2 acceptance layers for the Codex-style OpenHarness desktop shell.

## Layer A: Visible GUI Smoke

Layer A is the human-visible Electron window check. It is required before saying the desktop GUI shell is visually accepted.

Generate the visible smoke checklist:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\visible-gui-smoke.ps1
```

Launch the GUI for manual smoke:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\visible-gui-smoke.ps1 -Launch
```

The script writes a timestamped checklist to `learning_agent/test/desktop_gui_shell_v2/visible_gui_smoke/`. It does not mark the GUI as passed automatically. The operator must confirm the Electron window visibly satisfies each row.

## Layer B: Automated Release Gate

Layer B is the automated contract gate:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\release-gate.ps1
```

The V2 release gate runs:

- Python GUI V1 and V2 tests through `unittest discover -p "test_gui*.py"`.
- Frontend TypeScript lint.
- Frontend Vitest.
- Frontend production build.
- Visible GUI smoke instruction generation.
- Layer C trigger decision printout.

Expected success markers:

```text
Python GUI tests OK.
Frontend lint passed.
Frontend unit tests passed.
Frontend production build passed.
Layer A visible GUI smoke instructions generated.
Layer C trigger decision printed.
```

## Layer C: Conditional Backend Agent Terminal Gate

Layer C is the real backend-agent terminal gate using `learning_agent/start_oauth_agent.bat`.

Layer C is required when a change modifies agent runtime behavior, MCP routing, model calls, browser automation, Computer Use, or backend permission enforcement.

Layer C is not a replacement for Layer A. A task that only changes the Electron shell still needs visible GUI smoke for visual acceptance.

## Current V2 Status

The V2 release gate can prove automated contracts and build health. It cannot prove visual correctness by itself.

The current visible GUI rows are listed in `apps/desktop/tests/gui-prompt-matrix.md` under `V2 Visible GUI Release Rows`.
