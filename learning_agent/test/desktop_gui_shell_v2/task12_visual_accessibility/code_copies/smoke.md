# Desktop GUI Smoke Checklist

This checklist is Layer A visible desktop GUI acceptance. It validates the Electron shell, not the terminal agent.

## Scope

Layer A is passed only when the operator can see the real Electron desktop window and confirm the shell behaves like a usable Codex-style GUI surface.

Layer A does not replace backend unit tests, TypeScript checks, or the conditional terminal agent gate.

## Checklist

- [x] Start GUI bridge on localhost.
- [x] Start desktop renderer and Electron shell.
- [x] Confirm a real desktop window opens on the user's machine.
- [x] Confirm the window is not blank.
- [x] Confirm sidebar renders.
- [x] Confirm thread panel renders.
- [x] Confirm composer accepts text.
- [x] Confirm bootstrap payload loads.
- [x] Confirm event polling returns without error.
- [x] Confirm browser provider panel handles empty provider state and snapshot degradation.
- [x] Confirm permission banner can render from a backend permission event.
- [x] Confirm cancel button changes a running turn into a visible cancelling/cancelled state.
- [x] Confirm retry creates a new linked turn.
- [x] Confirm resume restores the last session after window restart.

## V2 Visual Acceptance Checklist

- [x] 1280x800 desktop window has no text overlap.
- [x] 1024x720 compact window remains usable.
- [x] Buttons have icon labels, visible text, or accessible labels.
- [x] Right inspector tabs remain visible in compact mode.
- [x] Composer keeps stable height within min/max bounds.
- [x] Tool cards do not resize the surrounding layout unexpectedly.
- [x] Keyboard focus is visible on sidebar, tabs, composer, and copy buttons.
- [x] Settings and diagnostics panels scroll internally without pushing the shell.

## Evidence Rule

Record screenshots, screen recording, or explicit manual notes in `learning_agent/test/desktop_gui_shell_YYYYMMDD/README.md`.

Do not mark this checklist complete from automated tests alone.

## 2026-06-25 Result

Layer A visible GUI smoke passed for the V1 vertical slice.

Evidence is archived under `learning_agent/test/desktop_gui_shell_20260625/`.

## 2026-06-25 V2 Task 12 Result

V2 visual accessibility pass completed with visible Electron screenshots at `learning_agent/test/desktop_gui_shell_v2/task12_visual_accessibility/`.
