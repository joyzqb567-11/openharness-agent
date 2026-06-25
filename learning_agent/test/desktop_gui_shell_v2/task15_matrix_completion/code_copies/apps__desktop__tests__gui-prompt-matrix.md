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
- [x] Visible GUI release-row execution now covers the user-visible behaviors represented by the V2 golden traces; exact fixture shape remains covered by backend and frontend automated tests. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/` and `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/layer_a_round2_completion_result.json`.

## V2 Visible GUI Release Rows

These rows are generated into `learning_agent/test/desktop_gui_shell_v2/visible_gui_smoke/` by `apps/desktop/scripts/visible-gui-smoke.ps1`. They are checked only after the real Electron window is visible and the UI state has screenshot/JSON evidence.

- [x] V2 visible GUI: streaming Chinese answer. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/layer_a_cdp_smoke_result.json`.
- [x] V2 visible GUI: streaming English answer. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/layer_a_round2_result.json` and `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/english_streaming.png`.
- [x] V2 visible GUI: safety refusal as assistant message. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/layer_a_round2_completion_result.json` and `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/safety_refusal_visible_final.png`.
- [x] V2 visible GUI: multiline Chinese persistence. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/layer_a_cdp_smoke_result.json`.
- [x] V2 visible GUI: Shift+Enter newline. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/layer_a_round2_completion_result.json` and `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/shift_enter_newline_final.png`.
- [x] V2 visible GUI: structured token rejection GUI error. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/layer_a_round2_completion_result.json` and `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/token_rejection_error_final.png`.
- [x] V2 visible GUI: structured unknown route GUI error. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/layer_a_round2_completion_result.json` and `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/unknown_route_gui_error_final.png`.
- [x] V2 visible GUI: bridge offline banner. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/layer_a_round2_completion_result.json` and `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/bridge_offline_banner_final.png`.
- [x] V2 visible GUI: tool trace row. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/layer_a_cdp_smoke_result.json`.
- [x] V2 visible GUI: permission approve/deny. Evidence: approve in `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/layer_a_cdp_smoke_result.json`, deny visible in `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/electron_initial.png`.
- [x] V2 visible GUI: browser panel degraded state. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/layer_a_round2_completion_result.json` and `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/browser_computer_panel_final.png`.
- [x] V2 visible GUI: Computer Use panel safe unavailable state. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/layer_a_round2_completion_result.json` and `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/browser_computer_panel_final.png`.
- [x] V2 visible GUI: settings panel opens. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/layer_a_round2_completion_result.json` and `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/settings_panel_final.png`.
- [x] V2 visible GUI: diagnostics panel opens with safe diagnostic status. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/electron_cdp_after_smoke.png`.
- [x] V2 visible GUI: window restart restores latest V2 session. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/electron_initial.png`.

## Completed Follow-Up Matrix Items

- [x] Safety refusal appears as an assistant message and event. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/safety_refusal_visible_final.png`.
- [x] Chinese multiline input preserves newlines in the persisted session. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance/layer_a_cdp_smoke_result.json`.
- [x] Shift+Enter inserts newline with visible caret behavior. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/shift_enter_newline_final.png`.
- [x] Bridge token rejection shows a polished in-thread GUI error state. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/token_rejection_error_final.png`.
- [x] Unknown route shows a polished in-thread GUI error state. Evidence: `learning_agent/test/desktop_gui_shell_v2/layer_a_visible_acceptance_round2/unknown_route_gui_error_final.png`.

## Acceptance Note

The checked V1 and V2 items validate the mature GUI shell vertical slice: launch, prompt, lifecycle, tool card, browser panel, Computer Use safe unavailable panel, permissions, cancel, retry, failure text, safety refusal, structured GUI errors, offline banner, settings, diagnostics, and resume.

Layer A visible evidence is archived under `learning_agent/test/desktop_gui_shell_v2/`, while Layer B automated release gate coverage remains in the Python GUI tests and frontend Vitest suite.
