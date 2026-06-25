# Desktop GUI Prompt Matrix

This matrix is Layer A visible desktop GUI acceptance for the 2026-06-25 V1 vertical slice.

Each checked scenario has visible Electron-window evidence archived in `learning_agent/test/desktop_gui_shell_20260625/`.

## Passed In The Visible GUI

- [x] Basic Chinese project-analysis prompt completes with a final answer.
- [x] Basic English project-analysis prompt completes with a final answer.
- [x] Long task prompt shows running state and tool/status events.
- [x] Tool progress appears as at least one tool card.
- [x] Browser provider status appears without renderer reading backend memory files.
- [x] Permission approval request appears and approve intent reaches backend.
- [x] Permission denial request appears and deny intent reaches backend.
- [x] Cancel during running turn reaches visible cancelled state.
- [x] Retry after failed turn creates a new linked turn.
- [x] Retry after completed turn creates a new linked turn.
- [x] Window restart resumes the latest session.
- [x] Failed tool event appears with readable error details.
- [x] Enter sends prompt.
- [x] Empty prompt cannot be sent.

## Automated Contract Coverage

- [x] Backend busy response returns structured `agent_busy`.
- [x] Bridge token rejection returns structured `unauthorized`.
- [x] Unknown route returns structured JSON error.
- [x] Browser provider snapshot failure degrades without traceback or path leakage.
- [x] V2 Composer: Enter sends one non-empty prompt.
- [x] V2 Composer: Shift+Enter keeps native newline and caret behavior.
- [x] V2 Composer: Chinese multiline prompt preserves newline and punctuation exactly.
- [x] V2 Composer: whitespace-only prompt cannot be sent.
- [x] V2 Composer: running state disables send and exposes a concise reason.

## V2 Golden Trace Baseline

- [x] `GT-001` through `GT-020` are defined in `docs/desktop_gui_shell_v2_golden_traces.md`.
- [x] `apps/desktop/tests/fixtures/gui-v2-golden-events.json` stores the machine-readable event fixture for all 20 traces.
- [x] Backend contract coverage validates fixture shape and secret redaction.
- [x] Frontend Vitest coverage validates renderer-side fixture consumption and secret redaction.
- [ ] Visible GUI execution for each V2 golden trace is still gated by the later V2-Core, V2-Trust, and V2-Product tasks.

## V2 Visible GUI Release Rows

These rows are generated into `learning_agent/test/desktop_gui_shell_v2/visible_gui_smoke/` by `apps/desktop/scripts/visible-gui-smoke.ps1`. They remain unchecked until a human or agent can actually see the Electron window and confirm the UI state.

- [x] V2 visible GUI: streaming Chinese answer. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/layer_a_cdp_smoke_result.json`.
- [ ] V2 visible GUI: streaming English answer.
- [ ] V2 visible GUI: safety refusal as assistant message.
- [x] V2 visible GUI: multiline Chinese persistence. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/layer_a_cdp_smoke_result.json`.
- [ ] V2 visible GUI: Shift+Enter newline.
- [ ] V2 visible GUI: structured token rejection GUI error.
- [ ] V2 visible GUI: structured unknown route GUI error.
- [ ] V2 visible GUI: bridge offline banner.
- [x] V2 visible GUI: tool trace row. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/layer_a_cdp_smoke_result.json`.
- [x] V2 visible GUI: permission approve/deny. Evidence: approve in `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/layer_a_cdp_smoke_result.json`, deny visible in `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/electron_initial.png`.
- [ ] V2 visible GUI: browser panel degraded state.
- [ ] V2 visible GUI: Computer Use panel safe unavailable state.
- [ ] V2 visible GUI: settings panel opens.
- [x] V2 visible GUI: diagnostics panel opens with safe diagnostic status. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/electron_cdp_after_smoke.png`.
- [x] V2 visible GUI: window restart restores latest V2 session. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/electron_initial.png`.

## Follow-Up Matrix Items

- [ ] Safety refusal appears as an assistant message and terminal event.
- [ ] Chinese multiline input preserves newlines in the persisted session.
- [ ] Shift+Enter inserts newline with visible caret behavior.
- [ ] Bridge token rejection shows a polished in-thread GUI error state.
- [ ] Unknown route shows a polished in-thread GUI error state.

## Acceptance Note

The checked V1 items validate the mature GUI shell vertical slice: launch, prompt, lifecycle, tool card, browser panel, permissions, cancel, retry, failure text, and resume.

The follow-up items are intentionally not checked because they require either backend safety-refusal integration or additional renderer error-surface work beyond the current V1 slice.
