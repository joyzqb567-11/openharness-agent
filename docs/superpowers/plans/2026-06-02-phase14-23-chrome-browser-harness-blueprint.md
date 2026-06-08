# Phase 14-23 Chrome / Browser / Harness Capability Blueprint

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans only after the user explicitly approves this blueprint. Do not implement before approval.

**Goal:** Complete the Chrome extension pairing, browser routing, OS computer use, and end-to-end harness chain from diagnostic visibility to real production acceptance.

**Architecture:** Continue the existing TDD-first phase pattern. Each phase must produce one independently testable capability, update `/chrome` or status surfaces where relevant, add focused unit tests, run full regression, create a real visible terminal acceptance scenario, and archive evidence under `learning_agent/test/`.

**Tech Stack:** Python `unittest`, PowerShell acceptance controller, `learning_agent` terminal app, Chrome native host/extension bridge files, browser runtime store, harness verifier, Windows visible terminal acceptance.

---

## Non-Negotiable Rules

- No production code before a failing test.
- Every phase must update `agent_memory/progress.md`.
- Every phase must create or update a phase report in `agent_memory/`.
- Every phase must copy changed files and acceptance evidence to `learning_agent/test/<phase-name-date>/`.
- Every phase must pass focused tests, py_compile, full `python -m unittest discover -s learning_agent\tests`, and real visible terminal acceptance.
- Do not claim “开发完成” unless `learning_agent/start_oauth_agent.bat` visible terminal acceptance passes.
- Commands that write or delete registry must remain behind explicit confirmation tokens.

---

## Current Baseline

Completed through Phase 13:

- `/chrome` can show native host installer state.
- `/chrome` can show pairing/session fields.
- `/chrome install-preview`, `install-confirm`, `uninstall-preview`, and `uninstall-confirm` exist.
- `install-confirm` and `uninstall-confirm` require explicit tokens.
- Current real terminal status shows `paired=false device_id= session_id= allowed_origin_count=0`.

Main current gap:

- The system can display that pairing is missing, but it cannot yet diagnose exactly why pairing is missing or guide the user through a real pairing workflow.

---

## Phase 14: `/chrome pairing-diagnose`

**Goal:** Add a diagnostic command that explains why `paired=false`.

**Scope:**

- Add `/chrome pairing-diagnose`.
- Inspect native host installer state.
- Inspect bridge file existence and readability.
- Inspect `connected`, `extension_id`, `pairing`, `device_id`, `session_id`, `allowed_origins`, `last_seen_at`.
- Report missing or stale fields with plain Chinese guidance.

**Likely Files:**

- Modify: `learning_agent/app/interactive.py`
- Modify: `learning_agent/app/chrome_status_renderer.py` if guide text needs new action listing.
- Modify: `learning_agent/runtime/status_snapshot.py` if more bridge diagnostics are needed.
- Test: `learning_agent/tests/test_chrome_terminal_subcommands_phase9.py`
- Test: likely new `learning_agent/tests/test_chrome_pairing_diagnose_phase14.py`
- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase14_chrome_pairing_diagnose.json`

**Success Criteria:**

- `/chrome pairing-diagnose` prints `pairing_diagnose`.
- It shows `paired=false` reason categories.
- It recommends the next concrete action.
- It never writes registry or modifies bridge state.

**Acceptance Prompt:**

`/chrome pairing-diagnose`

**Stop Condition:**

- Stop if diagnosis requires actual extension UI behavior that cannot be inferred from bridge/native host state.

---

## Phase 15: Chrome Extension Pairing Trigger Chain

**Goal:** Provide a safe terminal-side way to start or refresh pairing.

**Scope:**

- Add a pairing request model.
- Add `/chrome pairing-preview` or `/chrome pairing-start-preview`.
- Potentially add `/chrome pairing-start-confirm <token>` only if it writes durable state.
- Generate a pairing request id or nonce if needed.
- Display instructions for the Chrome extension side.

**Likely Files:**

- Create or modify: `learning_agent/browser_extension_host/pairing_store.py`
- Modify: `learning_agent/browser_extension_host/bridge_server.py`
- Modify: `learning_agent/browser_extension_host/native_host.py`
- Modify: `learning_agent/chrome_extension/background.js`
- Modify: `learning_agent/app/interactive.py`
- Test: `learning_agent/tests/test_chrome_extension_pairing_stage14.py`
- Test: new `learning_agent/tests/test_chrome_pairing_trigger_phase15.py`
- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase15_chrome_pairing_trigger.json`

**Success Criteria:**

- Pairing request is generated without secrets.
- Pairing data is sanitized before persistence.
- `/chrome` can show pending pairing request state.
- Existing pairing tests still pass.

**Acceptance Prompt:**

`/chrome pairing-diagnose`

or, if implemented safely:

`/chrome pairing-preview`

**Stop Condition:**

- Stop before writing browser secrets, cookies, localStorage, or sessionStorage.

---

## Phase 16: Session Sync Real Closure

**Goal:** Verify browser-side prompts can become durable agent runtime commands.

**Scope:**

- Ensure browser prompt messages enqueue into `RuntimeCommandQueue`.
- `/chrome` should show `last_browser_prompt_id` and source URL.
- Add terminal or verifier path to prove the queued command exists.

**Likely Files:**

- Modify: `learning_agent/browser_extension_host/bridge_server.py`
- Modify: `learning_agent/browser_extension_host/native_host.py`
- Modify: `learning_agent/chrome_extension/background.js`
- Modify: `learning_agent/runtime/status_snapshot.py`
- Modify: `learning_agent/app/chrome_status_renderer.py`
- Test: `learning_agent/tests/test_chrome_extension_pairing_stage14.py`
- Test: new `learning_agent/tests/test_chrome_session_sync_phase16.py`
- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase16_session_sync.json`

**Success Criteria:**

- Browser prompt creates a durable command.
- Command contains prompt, URL, title, tab id, and selected text with length limits.
- `/chrome` displays last browser prompt evidence.

**Acceptance Prompt:**

`/chrome`

and potentially a browser-side simulated prompt scenario.

**Stop Condition:**

- Stop if real Chrome extension is unavailable and only simulation can be performed; report real-browser gap clearly.

---

## Phase 17: `/chrome` Operable Guide Enhancement

**Goal:** Make `/chrome` a compact operational guide, not just a status dump.

**Scope:**

- Show current state.
- Show next recommended command.
- Show safe available commands.
- Show risk level for each command.
- Show whether command needs confirmation token.

**Likely Files:**

- Modify: `learning_agent/app/chrome_status_renderer.py`
- Modify: `learning_agent/app/interactive.py`
- Test: `learning_agent/tests/test_chrome_terminal_status_ui_stage18.py`
- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase17_chrome_operable_guide.json`

**Success Criteria:**

- `/chrome` has a readable `Chrome Guide` and `Chrome Actions`.
- Risky commands are labeled clearly.
- No long text wrapping breaks readability in visible terminal.

**Acceptance Prompt:**

`/chrome`

**Stop Condition:**

- Stop if the UI becomes too verbose; preserve a concise terminal surface.

---

## Phase 18: Real Chrome Extension End-to-End Acceptance

**Goal:** Run a true end-to-end chain involving native host, extension pairing, and browser prompt/session sync.

**Scope:**

- Validate native host manifest and launcher.
- Validate extension pairing status.
- Validate browser-side prompt enqueue.
- Validate `/chrome` shows final evidence.
- Use screenshots and events as proof.

**Likely Files:**

- Modify: `learning_agent/acceptance_controller/controller.ps1`
- Modify: `learning_agent/acceptance/verifier.py`
- Add scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase18_chrome_extension_e2e.json`
- Test: new `learning_agent/tests/test_chrome_extension_e2e_matrix_phase18.py`

**Success Criteria:**

- Real visible terminal starts.
- Chrome extension/native host status is visible.
- Pairing/session sync evidence is visible.
- Verifier passes.

**Acceptance Prompt:**

`/chrome`

and possibly a second prompt after browser-side action.

**Stop Condition:**

- Stop and ask user for manual browser action if Codex cannot control or inspect the extension UI.

---

## Phase 19: Browser Tool Routing 강화

**Goal:** Let the agent choose between chrome_extension, real Chrome CDP, and visible Chromium more intelligently.

**Scope:**

- Define routing policy.
- Prefer extension when paired and command supported.
- Prefer real Chrome CDP when connected and extension unavailable.
- Prefer visible Chromium when real Chrome is blocked.
- Expose route decision in browser runtime events.

**Likely Files:**

- Modify: `learning_agent/browser_automation_mcp_server.py`
- Modify: `learning_agent/browser/providers/`
- Modify: `learning_agent/browser/action_policy.py`
- Modify: `learning_agent/browser/action_executor.py`
- Test: existing browser provider/router tests
- Test: new `learning_agent/tests/test_browser_routing_phase19.py`
- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase19_browser_routing.json`

**Success Criteria:**

- Routing decision is deterministic and visible.
- User-facing answer can explain which browser provider was used.
- Existing browser tools continue to pass.

**Acceptance Prompt:**

“打开一个网页并截图，然后告诉我你用了哪个浏览器 provider。”

**Stop Condition:**

- Stop if provider selection requires product policy decisions that are not encoded in current requirements.

---

## Phase 20: OS Computer Use Productionization

**Goal:** Make Windows OS computer use safer, observable, and more production-ready.

**Scope:**

- Strengthen permission gates.
- Add `/computer` or status visibility if needed.
- Add screenshot evidence and action audit.
- Keep real OS actions disabled unless explicit env/config enables them.

**Likely Files:**

- Modify: `learning_agent/computer_use/controller.py`
- Modify: `learning_agent/tools/executor.py`
- Modify: `learning_agent/tools/schemas.py`
- Modify: `learning_agent/tools/catalog.py`
- Test: `learning_agent/tests/test_os_computer_use_stage17.py`
- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase20_os_computer_use.json`

**Success Criteria:**

- Default backend remains safe.
- Real Windows backend remains opt-in.
- Status explains why OS control is enabled or unavailable.
- No accidental desktop action in tests.

**Acceptance Prompt:**

“检查 computer use 状态，不要移动鼠标。”

**Stop Condition:**

- Stop before performing real mouse/keyboard actions unless explicit user approval is given.

---

## Phase 21: ClaudeCode-Style Terminal Status UI

**Goal:** Make terminal status surfaces feel closer to mature coding agents.

**Scope:**

- Improve `/chrome`, `/status`, `/events`, `/sessions`, `/compact`.
- Keep outputs compact and actionable.
- Add recent errors and next command hints.

**Likely Files:**

- Modify: `learning_agent/app/status_renderer.py`
- Modify: `learning_agent/app/chrome_status_renderer.py`
- Modify: `learning_agent/app/interactive.py`
- Test: terminal UI tests
- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase21_terminal_status_ui.json`

**Success Criteria:**

- Terminal UI is concise.
- It exposes connection, errors, and next actions.
- It remains readable in visible terminal screenshots.

**Acceptance Prompt:**

`/status`

and

`/chrome`

**Stop Condition:**

- Stop if adding UI text starts duplicating implementation details or overwhelming beginner users.

---

## Phase 22: Long-Task Harness and Browser Task Fusion

**Goal:** Attach browser tasks to durable harness runs with verifier evidence.

**Scope:**

- Browser runs should map to harness stages.
- Browser actions should produce verifier-friendly events.
- `/status` and `/chrome` should expose harness links.

**Likely Files:**

- Modify: `learning_agent/browser/harness_integration.py`
- Modify: `learning_agent/browser_automation_mcp_server.py`
- Modify: `learning_agent/harness/`
- Modify: `learning_agent/runtime/status_snapshot.py`
- Test: `learning_agent/tests/test_browser_harness_integration_stage11.py`
- Test: new `learning_agent/tests/test_browser_harness_fusion_phase22.py`
- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_phase22_browser_harness_fusion.json`

**Success Criteria:**

- Browser task creates or updates a harness run.
- Verifier result is visible from status.
- Resume/retry does not duplicate completed browser actions.

**Acceptance Prompt:**

“执行一个可见浏览器任务，并显示 harness 证据。”

**Stop Condition:**

- Stop if retry semantics become ambiguous; document exact resume boundary first.

---

## Phase 23: Final End-to-End Acceptance Matrix Upgrade

**Goal:** Consolidate Phase 14-22 into one final real acceptance matrix.

**Scope:**

- Add one matrix file listing all Phase 14-22 tests, scenarios, backup directories, and acceptance artifacts.
- Add a matrix test.
- Add a final report.
- Run full regression and real visible terminal acceptance.

**Likely Files:**

- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase23_matrix.json`
- Create: `learning_agent/tests/test_agent_capability_phase23_matrix.py`
- Create: `agent_memory/agent_capability_phase23_matrix_20260602.md`
- Create: `docs/superpowers/reports/2026-06-02-agent-capability-phase14-23-final-report.md`

**Success Criteria:**

- Matrix references every phase.
- Every referenced scenario exists.
- Every referenced backup directory exists.
- Full tests pass.
- At least one final visible terminal acceptance run passes.

**Acceptance Prompt:**

`/chrome`

or a final combined prompt defined after Phase 18-22 capabilities are real.

**Stop Condition:**

- Stop if any previous phase lacks real terminal evidence.

---

## Recommended Execution Order

1. Phase 14 first, because current real state is `paired=false` and users need diagnosis before pairing.
2. Phase 15 second, because diagnosis should lead to a pairing trigger.
3. Phase 16 third, because pairing needs to prove session sync.
4. Phase 17 after the core flow exists, to polish the guide.
5. Phase 18 after pairing/session sync exists, to run true extension E2E.
6. Phase 19 after extension E2E, to route tools intelligently.
7. Phase 20 can run in parallel only if a separate worker handles OS safety boundaries.
8. Phase 21 after status surfaces have enough data to polish.
9. Phase 22 after browser routing and harness data are stable.
10. Phase 23 last, as the final acceptance matrix.

---

## Approval Gate

Implementation must not start until the user confirms this blueprint.

Suggested confirmation phrase:

`确认，按 Phase 14 到 Phase 23 逐阶段执行。`
