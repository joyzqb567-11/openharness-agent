# Learning Agent Progress

## 2026-06-03 Phase 38 Windows ComputerUseApproval Model

- Implemented `learning_agent/computer_use/approval.py` with session app allowlist, grant flags, forbidden target classification, terminal status lines, and stable Phase38 CLI tokens.
- Updated `learning_agent/computer_use/controller.py` so an injected approval model rejects forbidden targets, missing app grants, and missing grant flags before backend execution.
- Updated `learning_agent/app/interactive.py` so `/computer status` includes a terminal-safe `Computer Use Approval` summary.
- Added `learning_agent/tests/test_windows_computer_use_approval_phase38.py` and `learning_agent/acceptance_controller/scenarios/agent_capability_phase38_windows_computer_approval.json`.
- Verification passed: focused Phase38 6 tests OK, py_compile OK, scenario JSON OK, CLI self-check OK, Phase30-38 neighbor regression 45 tests OK, full regression 670 tests OK skipped=1.
- Real visible terminal acceptance passed in `learning_agent/acceptance_controller/runs/agent_capability_phase38_windows_computer_approval-20260603_105641`; independent verifier passed with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Boundary: Phase38 proves approval contract and controller pre-dispatch rejection, not graphical approval UI or real low-level Windows SendInput/WGC/UIA maturity.

---

## 2026-06-03 Phase 37 Windows SendInput action executor contract

- Implemented `learning_agent/computer_use/sendinput_executor.py` with a default-disabled Windows SendInput executor contract, injectable low-level implementation hook, stable Phase37 CLI tokens, and raw-text redaction for `type_text`.
- Updated `learning_agent/computer_use/controller.py` so `WindowsComputerUseBackend` accepts an `action_executor`, reports action-executor status, keeps `screenshot` as a read-only dimension path, and routes mouse/keyboard write actions through the Phase37 executor contract instead of the old `SetCursorPos + mouse_event` path.
- Exported Phase37 APIs from `learning_agent/computer_use/__init__.py`.
- Added tests in `learning_agent/tests/test_windows_computer_use_sendinput_phase37.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase37_windows_sendinput_executor.json`.
- Added memory report `agent_memory/agent_capability_phase37_windows_sendinput_executor_20260603.md`.
- Verification passed: TDD red test first failed on missing `learning_agent.computer_use.sendinput_executor`; focused Phase37 tests run 5 tests OK; `py_compile` OK; scenario JSON OK; CLI self-check prints `PHASE37_WINDOWS_SENDINPUT_EXECUTOR_OK contract_ready=true real_input_default=false fake_impl_exercised=true raw_text_hidden=true actions_expanded=false marker=PHASE37_WINDOWS_SENDINPUT_EXECUTOR_READY`; Phase30-37 neighbor regression runs 39 tests OK; full `python -m unittest discover -s learning_agent\tests` ran 664 tests OK with 1 skipped.
- Current boundary: Phase37 proves the executor contract, safe routing, injected fake implementation path, and redaction. It does not prove a real `ctypes.SendInput` implementation is installed or safe for broad desktop control.
- Real visible terminal acceptance passed in run `learning_agent/acceptance_controller/runs/agent_capability_phase37_windows_sendinput_executor-20260603_104221`.
- Independent verifier passed with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`, final marker `PHASE37_WINDOWS_SENDINPUT_EXECUTOR_READY PHASE37_WINDOWS_SENDINPUT_EXECUTOR_OK contract_ready=true real_input_default=false fake_impl_exercised=true raw_text_hidden=true actions_expanded=false`.
- Current next action: begin Phase38 Windows ComputerUseApproval model.

---

## 2026-06-03 Phase 36 Windows.Graphics.Capture provider contract

- Implemented `learning_agent/computer_use/wgc_capture.py` with `WindowsGraphicsCaptureProvider`, WGC dependency diagnostics, capture result coercion, and stable CLI tokens.
- Updated `learning_agent/computer_use/native_diagnostics.py` so the WGC diagnostics entry comes from the Phase36 provider contract.
- Exported Phase36 APIs from `learning_agent/computer_use/__init__.py`.
- Added tests in `learning_agent/tests/test_windows_computer_use_wgc_provider_phase36.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase36_windows_wgc_provider.json`.
- Added memory report `agent_memory/agent_capability_phase36_windows_wgc_provider_20260603.md`.
- Backed up Phase36 files under `learning_agent/test/agent_capability_phase36_windows_wgc_provider_20260603/`.
- Current environment honestly reports no WGC Python bindings, so `dependency_available=false`, `capture_contract_ready=true`, and `fallback_required=true`.
- Verification passed: `py_compile` OK, scenario JSON OK, focused Phase36 tests 5 OK, Phase33-36 regression 18 OK, full `python -m unittest discover -s learning_agent\tests` ran 659 tests OK with 1 skipped.
- Real visible terminal acceptance passed in run `learning_agent/acceptance_controller/runs/agent_capability_phase36_windows_wgc_provider-20260603_102321`.
- Independent verifier passed with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`, final marker `PHASE36_WINDOWS_WGC_PROVIDER_READY PHASE36_WINDOWS_WGC_PROVIDER_OK dependency_reported=true capture_contract_ready=true fallback_required=true actions_expanded=false`.
- Current next action: begin Phase37 SendInput executor with strict safe-action gate and no broad desktop automation.

---

## 2026-06-03 Phase 35 Windows real UIA safe-window smoke harness

- Implemented `learning_agent/computer_use/real_uia_smoke.py` with dependency diagnostics, safe Notepad-window smoke target, structured result output, and stable CLI tokens.
- Exported Phase35 APIs from `learning_agent/computer_use/__init__.py`.
- Added focused tests in `learning_agent/tests/test_windows_computer_use_real_uia_smoke_phase35.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase35_windows_real_uia_smoke.json`.
- Added memory report `agent_memory/agent_capability_phase35_windows_real_uia_smoke_20260603.md`.
- Backed up Phase35 files under `learning_agent/test/agent_capability_phase35_windows_real_uia_smoke_20260603/`.
- Current environment honestly reports `uiautomation` missing, so CLI output has `dependency_available=false`, `real_uia_attempted=false`, `real_uia_verified=false`, and `fake_provider_used=false`.
- Verification passed: `py_compile` OK, scenario JSON OK, focused Phase35 tests 4 OK, Phase32-35 regression 19 OK, full `python -m unittest discover -s learning_agent\tests` ran 654 tests OK with 1 skipped.
- Real visible terminal acceptance passed in run `learning_agent/acceptance_controller/runs/agent_capability_phase35_windows_real_uia_smoke-20260603_101422`.
- Independent verifier passed with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`, final marker `PHASE35_WINDOWS_REAL_UIA_SMOKE_READY PHASE35_WINDOWS_REAL_UIA_SMOKE_OK dependency_reported=true fake_provider_used=false actions_expanded=false safe_window_only=true`.
- Current next action: begin Phase 36 Windows.Graphics.Capture provider contract without installing system dependencies or claiming WGC is available on this machine.

---

## 2026-06-03 Phase 35-42 Windows Computer Use ClaudeCode alignment blueprint

- User asked to put the recommended next Windows Computer Use phases into an upgrade blueprint first, then execute phase by phase.
- Used planning-with-files and writing-plans workflow.
- Re-read `learning_agent/zqbcontext.md`, root `task_plan.md`, `findings.md`, `progress.md`, and agent_memory context/progress/bugs.
- Ran planning-with-files session catchup; Codex session parsing is not implemented, so catchup was skipped by the helper.
- Confirmed current Python environment dependency state: `uiautomation=False`, `comtypes=False`, WGC Python bindings unavailable, `platform=win32`.
- Recorded two shell syntax/tooling mistakes for future avoidance: Bash heredoc does not work in PowerShell, and this PowerShell `New-Item` does not support `-LiteralPath`.
- Created Phase 35-42 blueprint at `docs/superpowers/plans/2026-06-03-phase35-42-windows-computer-use-claudecode-alignment.md`.
- Created agent_memory blueprint at `agent_memory/agent_capability_phase35_42_windows_computer_use_upgrade_blueprint_20260603.md`.
- Created learning backup at `learning_agent/test/agent_capability_phase35_42_windows_computer_use_upgrade_blueprint_20260603/phase35_42_blueprint.md`.
- Updated root `task_plan.md` so the active plan is now Phase 35-42 Windows Computer Use ClaudeCode alignment.
- Phase35 has now been completed; current next action is Phase36 Windows.Graphics.Capture provider contract.

---

## 2026-06-03 Phase 30 Windows OS Computer Use safe action gate

- User asked to continue with the next recommended Windows Computer Use phase after Phase 29.
- Used TDD and added `learning_agent/tests/test_windows_computer_use_actions_phase30.py`.
- Red test was confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.lock'`.
- Added `learning_agent/computer_use/lock.py` with durable desktop control lock state, owner session checks, release, abort request, abort clear, and status output.
- Added `learning_agent/computer_use/action_policy.py` with window-relative coordinate conversion, sensitive text redaction, short text hash, target-window evidence summaries, and `phase30_window_relative_action_gate_v1`.
- Extended `learning_agent/computer_use/controller.py` so injected lock managers require the current session lock, abort blocks the next action before backend execution, window-relative x/y converts to screen x/y, and successful actions return `action_evidence`.
- Updated `MemoryComputerUseBackend` and `LearningAgent._computer_action()` so raw `type_text` content is not stored in action logs, audit logs, action evidence, permission text, or denied-action observations.
- Updated `learning_agent/computer_use/__init__.py` exports and `learning_agent/tools/schemas.py` coordinate descriptions.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase30_windows_action_gate.json`.
- Verification passed: focused Phase 30 tests 5 OK, related Phase 17/20/27/28/29 regression 24 OK, `py_compile` OK, scenario JSON OK, full `python -m unittest discover -s learning_agent\tests` ran 630 tests OK with 1 skipped.
- Real visible terminal acceptance passed in run `learning_agent/acceptance_controller/runs/agent_capability_phase30_windows_action_gate-20260603_065937`.
- Independent verifier passed with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`, and final marker `PHASE30_WINDOWS_ACTION_GATE_READY PHASE30_WINDOWS_ACTION_GATE_OK no_lock_blocked=true coord=15,27 abort_blocked=true raw_text_hidden=true evidence=true`.
- Current boundary: Phase 30 proves action gates and evidence envelope with a safe memory backend; real native SendInput/UIA/capture work remains future Phase 31+.

---

## 2026-06-03 Phase 29 Windows OS Computer Use observe evidence

- User asked to execute the next recommended phase after Phase 28.
- Used TDD and added `learning_agent/tests/test_windows_computer_use_observe_phase29.py`.
- Red test was confirmed: `learning_agent.computer_use.evidence` did not exist.
- Added `learning_agent/computer_use/evidence.py` with evidence root handling, screenshot artifact writing, metadata JSON writing, UIA sensitive-line filtering, and bounded accessibility excerpts.
- Added `learning_agent/computer_use/helper_client.py` with `WindowObservationPayload`, `StaticWindowObservationHelper`, and `NullWindowObservationHelper`.
- Extended `WindowsComputerUseBackend` so `get_window_state` saves evidence artifacts and returns `screenshot_id`, `screenshot_path`, `evidence_path`, bounded UIA summary fields, helper fields, and filtering counters.
- Updated `learning_agent/computer_use/__init__.py` exports for Phase 29 types.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase29_windows_observe_evidence.json`.
- Verification passed: focused Phase 29 tests 3 OK, Phase 28/29 tests 8 OK, Phase 29/28/27/20 regression 15 OK, `py_compile` OK, scenario JSON OK, full `python -m unittest discover -s learning_agent\tests` ran 625 tests OK with 1 skipped.
- Real visible terminal acceptance passed in run `learning_agent/acceptance_controller/runs/agent_capability_phase29_windows_observe_evidence-20260603_062659`.
- Acceptance result: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`, final marker `PHASE29_WINDOWS_OBSERVE_READY PHASE29_WINDOWS_OBSERVE_OK screenshot=true metadata=true width=123 filtered=1 truncated=true password_hidden=true`.
- Evidence artifact check confirmed files under `learning_agent/memory/computer_use/evidence_phase29_acceptance/`, and latest metadata had `contains_password=False`.
- Current boundary: Phase 29 proves evidence store/helper contract with static safe helper; real Windows.Graphics.Capture and UIAutomationClient native helper remain future work.

---

## 2026-06-02 Phase 28 Windows OS Computer Use read-only inventory

- User confirmed continuing after Phase 27 protocol work.
- Added TDD coverage in `learning_agent/tests/test_windows_computer_use_inventory_phase28.py`.
- Red tests were confirmed first: `learning_agent.computer_use.windows_backend` did not exist, then default status did not expose the new observe opt-in field.
- Added `learning_agent/computer_use/windows_backend.py` with static inventory, optional Win32 ctypes enumeration, safe title filtering, rect normalization, app grouping, active-window lookup, and process-path hashing.
- Extended `learning_agent/computer_use/controller.py` so `WindowsComputerUseBackend.observe()` supports `list_windows`, `list_apps`, `get_active_window`, and `get_window_state`.
- Added `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_OBSERVE` as a read-only observation opt-in separate from `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE`.
- Kept real desktop actions blocked in read-only mode, with an explicit Chinese refusal message for mouse, keyboard, and window actions.
- Exported the new inventory helpers from `learning_agent/computer_use/__init__.py`.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase28_windows_inventory.json`.
- Added memory report `agent_memory/agent_capability_phase28_windows_inventory_20260602.md`.
- Verification passed: focused Phase 28 tests 5 OK, Phase 27/17/20 regression 16 OK, `py_compile` OK, full `python -m unittest discover -s learning_agent\tests` ran 622 tests OK with 1 skipped.
- Real visible terminal acceptance passed in run `learning_agent/acceptance_controller/runs/agent_capability_phase28_windows_inventory-20260602_234801`.
- Acceptance result: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`, final marker `PHASE28_WINDOWS_INVENTORY_READY PHASE28_WINDOWS_INVENTORY_OK windows=1 filtered=1 apps=1 width=300 actions_blocked=true`.
- Current boundary: Phase 28 provides read-only app/window inventory and placeholder window state evidence; real screenshots and UI Automation text remain Phase 29 work.

---

## 2026-06-02 Phase 27 Windows OS Computer Use protocol

- User confirmed execution after the Phase 26 Windows Computer Use blueprint.
- Added TDD coverage in `learning_agent/tests/test_windows_computer_use_protocol_phase27.py`.
- Red test was confirmed: `computer_observe` was missing and memory backend had no window directory protocol.
- Added `learning_agent/computer_use/models.py` with typed window reference helpers.
- Extended `learning_agent/computer_use/controller.py` with `observe()` actions, memory window listing/state observation, and unknown-window rejection before action execution.
- Added `computer_observe` to tool schema, capability pack mapping, catalog read-only metadata, executor routing, and `LearningAgent._computer_observe()`.
- Updated `computer_action` schema with optional trusted `window` target.
- Fixed `learning_agent/acceptance_controller/controller.ps1` so missing optional assertion lists do not create null dictionary keys.
- Added visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase27_windows_computer_use_protocol.json`.
- Verification passed: Phase 27 focused tests 4 OK, Phase 17/20 Computer Use regression 7 OK, `py_compile` OK, full `python -m unittest discover -s learning_agent\tests` ran 617 tests OK with 1 skipped.
- Real visible terminal acceptance passed in run `learning_agent/acceptance_controller/runs/agent_capability_phase27_windows_computer_use_protocol-20260602_233224`.
- Acceptance result: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`, final marker `PHASE27_COMPUTER_PROTOCOL_READY PHASE27_COMPUTER_PROTOCOL_OK observe=true reject_unknown=true backend_actions=0`.
- Current boundary: Phase 27 defines and verifies protocol only; real Windows window enumeration, screenshots, UI Automation, and SendInput expansion remain Phase 28+ work.

---

## 2026-06-02 Phase 26 Windows OS Computer Use blueprint

- Read Codex Computer Use plugin skill and confirmed the Windows reference route: app/window targeting, UI Automation, SendInput, Windows.Graphics.Capture, and strict Windows safety boundaries.
- Re-read existing learning_agent Computer Use baseline and Phase 20 notes.
- Detected that Phase 25 is already used by real extension/native-host connection follow-up, so the Windows Computer Use blueprint is numbered Phase 26.
- Created formal blueprint: `docs/superpowers/plans/2026-06-02-phase26-windows-os-computer-use-blueprint.md`.
- Created memory record: `agent_memory/agent_capability_phase26_windows_computer_use_blueprint_20260602.md`.
- Created learning backup: `learning_agent/test/agent_capability_phase26_windows_computer_use_blueprint_20260602/phase26_blueprint.md`.
- No runtime code changed in this phase; no tests or real visible terminal acceptance were required for the blueprint-only step.
- Next action after user approval: Phase 27 typed Computer Use protocol and tests.

---

# Learning Agent Long-Task Harness Progress

## 2026-06-01 Browser Runtime ClaudeCode alignment planning

- Read current root planning files and synchronized the active plan away from the completed harness pass.
- Created `agent_memory/browser_runtime_claudecode_upgrade_plan_20260601.md`.
- Created `docs/superpowers/plans/2026-06-01-browser-runtime-claudecode-alignment.md`.
- Created backup copy `learning_agent/test/browser_runtime_claudecode_upgrade_plan_20260601/plan.md`.
- Updated `task_plan.md` so future agents start from Browser Runtime alignment rather than the historical harness alignment plan.
- Updated `findings.md` with ClaudeCode source evidence and learning_agent browser runtime gap summary.
- Updated `agent_memory/progress.md` and `agent_memory/context.md` with the new plan location and next step.
- Current phase: planning complete, waiting for user confirmation before code implementation.

## 2026-06-01 Browser Runtime ClaudeCode alignment execution: Stage 1-2

- User confirmed the written browser runtime alignment plan.
- Used TDD for Stage 1 and observed the expected red failure: `learning_agent.browser.runtime_models` did not exist.
- Added `learning_agent/browser/runtime_models.py` with browser run/session/tab/action/observation/locator/recovery/assertion/capability models plus redaction helpers.
- Stage 1 focused tests now pass: `python -m unittest learning_agent.tests.test_browser_runtime_models`.
- Used TDD for Stage 2 and observed the expected red failure: `learning_agent.browser.runtime_store` did not exist.
- Added `learning_agent/browser/runtime_events.py` and `learning_agent/browser/runtime_store.py`.
- Store tests now prove run/action/observation/event persistence and restart recovery for completed stages.
- Added a red test proving `BrowserAutomationServer.call()` did not yet create durable browser runtime runs; the red failure was an empty run directory.
- Updated `learning_agent/browser_automation_mcp_server.py` so the unified tool call wrapper creates a top-level browser run and writes started/completed/failed action events.
- Added a red test proving `LearningAgent._execute_tool()` did not yet mirror browser runtime runs into unified status events; the red failure was no `browser_runtime_event`.
- Updated `learning_agent/core/agent.py` to scan the latest browser runtime run after browser_automation MCP tool completion/failure and write `browser_runtime_event`.
- Added `browser_runtime_event` to `learning_agent/runtime/status_schema.py`.
- Focused verification passed: `python -m unittest learning_agent.tests.test_browser_runtime_models learning_agent.tests.test_browser_runtime_store learning_agent.tests.test_browser_runtime_alignment learning_agent.tests.test_core_run_loop learning_agent.tests.test_status_ecosystem_deep_alignment` ran 67 tests OK.
- Syntax verification passed for the new source, server, agent, status schema, and test files via `python -m py_compile ...`.
- Backups were copied to `learning_agent/test/browser_runtime_claudecode_stage1_20260601/` and `learning_agent/test/browser_runtime_claudecode_stage2_20260601/`.
- Current phase: Stage 1 plus core Stage 2 are complete; dedicated browser status snapshot/CLI/API, later stages, and visible terminal acceptance remain pending.

## 2026-06-02 Agent Capability Phase 24 Real Chrome Extension E2E

- Added Phase 24 plan in `agent_memory/agent_capability_phase24_real_chrome_extension_e2e_20260602.md`.
- Added focused tests in `learning_agent/tests/test_real_chrome_extension_e2e_phase24.py`.
- Updated native host launcher generation so Chrome receives `OPENHARNESS_LEARNING_AGENT_WORKSPACE`.
- Updated `native_host.py` to resolve bridge state and runtime queue from the stable workspace instead of relying only on `Path.cwd()`.
- Added `/chrome real-extension-e2e-check` as a real-bridge, read-only terminal check.
- Added the Phase 24 command to `/chrome` actions.
- Added real visible terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase24_real_chrome_extension_e2e.json`.
- Copied Phase 24 learning backup to `learning_agent/test/agent_capability_phase24_real_chrome_extension_e2e_20260602/`.
- Phase 24 verification passed: focused tests 4 OK, related Chrome regression 19 OK, full `learning_agent\tests` regression 611 OK with 1 skipped, Python compile OK, JSON check OK, and `node --check` OK.
- Real visible terminal acceptance passed through `start_oauth_agent.bat` controller run `agent_capability_phase24_real_chrome_extension_e2e-20260602_221135`, and independent verifier reported `completed=true`.
- Current live evidence is intentionally honest: `browser_prompt_queued=true`, `workspace_lock_ok=true`, `real_extension_connected=false`, `paired=false`, `real_extension_e2e=false`; Chrome extension installation/connection still needs a later user-side Chrome step.

## 2026-06-02 Phase 24/25 real extension connection follow-up

- Loaded the local Chrome extension in a visible local Playwright Chromium process and captured extension id `lepnefooepbnjbcnhooiccpnafalfbdk`.
- Registered the native host through visible terminal `/chrome install-confirm lepnefooepbnjbcnhooiccpnafalfbdk I_UNDERSTAND_WRITE_REGISTRY`.
- Fixed the native host launcher by adding repo root `PYTHONPATH`, resolving the confirmed `ModuleNotFoundError: No module named 'learning_agent'`.
- Strengthened terminal acceptance so `/chrome real-extension-e2e-check` must include true payload evidence, not merely a `chrome_status_printed` event.
- Strict visible terminal acceptance passed in run `learning_agent/acceptance_controller/runs/agent_capability_phase24_real_chrome_extension_e2e-20260602_224404`.
- Verified true fields: `real_extension_connected=true`, `paired=true`, `browser_prompt_queued=true`, `workspace_lock_ok=true`, `real_extension_e2e=true`.
- Full regression passed: `python -m unittest discover -s learning_agent\tests` ran 613 tests OK, skipped=1.
- Boundary: the proof uses real visible local Chromium plus real extension/native host. Google Chrome stable manual loading may need a separate extension id registration if its id differs.

## 2026-05-31 ClaudeCode alignment execution

- Switched current workspace to branch `feature/harness-claudecode-alignment` without reverting existing dirty files.
- Activated the 12-stage plan from `agent_memory/harness_claudecode_alignment_plan_20260531.md`.
- Updated root `task_plan.md` so future agents do not confuse the completed 8-stage independent harness pass with the current ClaudeCode-alignment runtime pass.
- Added `learning_agent/tests/test_harness_runtime_alignment.py` with red tests for runtime command queue, harness session runtime, interrupted resume, durable task registry, task output, poller/watchdog, advanced verifier, and upgraded CLI status commands.
- Red test confirmed: `python -m unittest learning_agent.tests.test_harness_runtime_alignment` fails with `ModuleNotFoundError: No module named 'learning_agent.runtime'`, proving the new runtime package is still missing.
- Implemented `learning_agent/runtime/` with command queue, file safety helpers, session runtime, interrupted resume, durable task registry, task output store, and task poller.
- Updated `LearningAgent.run()` so the old API now delegates through `run_events()` and mirrors every run into durable harness state.
- Updated task and background command paths so task records and output now persist under `memory/tasks`.
- Upgraded `StageVerifier` and `HarnessStage` for artifact content, JSON schema, command exit code, event sequence, and acceptance result checks.
- Upgraded `python -m learning_agent.harness` with `queue`, `tasks`, `events`, `resume`, and `poll`.
- Added red/green coverage for corrupt harness JSON quarantine and queue recovery.
- Focused verification passed: `python -m unittest learning_agent.tests.test_harness_runtime_alignment` ran 9 tests OK.
- Regression verification passed: `python -m unittest learning_agent.tests.test_core_run_loop` ran 40 tests OK; `python -m unittest learning_agent.tests.test_runtime_events` ran 4 tests OK; `python -m unittest learning_agent.tests.test_harness_long_task` ran 8 tests OK.
- Full regression verification passed: `python -m unittest discover learning_agent` ran 407 tests OK, skipped=1.
- Compile verification passed: `python -m compileall learning_agent` exited 0.
- MCP doctor passed: `python learning_agent\learning_agent.py mcp-doctor` exited 0 and reported 30 model-visible MCP tools; Chrome real-profile status was `needs_user_action` because Chrome was already running.
- Learning backup copied to `learning_agent/test/harness_claudecode_alignment_20260531/` and cleaned so it contains source/docs/tests, not Python cache files.
- Real visible terminal acceptance first exposed a stage-level persistence bug: `runtime_0b61bcfb0c2589c2.json` had top-level `status=completed` but `stages[0].status=pending`.
- Added a focused regression assertion, confirmed the red failure, then fixed `learning_agent/runtime/session_runtime.py` to update `run.stages[0]` after `HarnessRun.create(...)`.
- Re-run verification passed after the fix: focused harness runtime suite 9 OK; core run loop 40 OK; runtime events 4 OK; long-task harness 8 OK; full `python -m unittest discover learning_agent` 407 OK skipped=1; `python -m compileall learning_agent` exit 0; `mcp-doctor` exit 0 with 30 MCP tools.
- Real visible terminal acceptance passed: `learning_agent/acceptance_controller/runs/harness_runtime_alignment_status-20260531_165630/result.json` has `completed=true`, `assertion.passed=true`, and final marker `HARNESS_RUNTIME_ALIGNMENT_READY`.
- Independent acceptance verifier replay passed for `harness_runtime_alignment_status-20260531_165630`.
- Durable runtime evidence passed: latest `learning_agent/memory/harness/runs/runtime_275e3c33ad6ec332.json` has `status=completed`, `stages[0].status=completed`, `stages[0].acceptance.passed=true`, and runtime command events include `command_queued` then `command_completed`.
- Current phase: complete.

## 2026-05-31

- Created persistent planning files for the eight-stage harness implementation.
- Current phase: Stage 1 planning and inventory.
- Next action: write failing harness tests before production code.
- Added `learning_agent/tests/test_harness_long_task.py` as the TDD red test suite.
- Red test confirmed: `python -m unittest learning_agent.tests.test_harness_long_task` fails because `learning_agent.harness` does not exist yet.
- Implemented `learning_agent/harness/` with models, store, queue, verifier, recovery, runner, status renderer, CLI, and `python -m learning_agent.harness` entry point.
- Added queue lease, heartbeat, complete, fail, marker/artifact verifier, retry/recovery, checkpoint resume, and status CLI coverage.
- Focused green test confirmed: `python -m unittest learning_agent.tests.test_harness_long_task` passes with 5 tests OK.
- Documentation updated in `learning_agent/harness/README.md`, `learning_agent/README.md`, and `learning_agent/AGENT_ARCHITECTURE_INDEX.md`.
- Learning backup copied to `learning_agent/test/long_task_harness_20260531/`.
- Automated verification passed: focused harness tests 5 OK, full `python -m unittest discover learning_agent` 395 OK skipped=1, `python -m compileall learning_agent` passed, and `mcp-doctor` exited 0 with 30 MCP tools visible.
- Real visible terminal acceptance passed through `learning_agent/acceptance_controller/scenarios/long_task_harness_status.json`.
- Acceptance evidence: `learning_agent/acceptance_controller/runs/long_task_harness_status-20260531_152707/result.json` shows `completed=true`, `assertion.passed=true`, and the visible terminal answer contains `LONG_TASK_HARNESS_READY`.
- Final screenshot visually confirmed: `learning_agent/acceptance_controller/runs/long_task_harness_status-20260531_152707/03_final.png`.
- Current phase: complete.
## 2026-06-03 Phase 32 Windows OS Computer Use Native Observation Helper

- Added `learning_agent/computer_use/native_helper.py` with `WindowsNativeWindowObservationHelper`, injectable capture/text providers, Win32 GDI screenshot fallback, and Win32 window-text fallback.
- Added `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_NATIVE_OBSERVE` as a separate native helper opt-in, so read-only inventory does not automatically read screen pixels or text.
- Updated `build_default_computer_use_backend(...)` to inject the native helper only when the native opt-in is explicitly enabled on Windows.
- Added Phase32 focused tests and visible terminal scenario.
- Verification passed: Phase32 focused suite 6 OK; neighboring Computer Use regression 35 OK; `py_compile` OK; scenario JSON OK; full regression 641 tests OK, skipped=1.
- Visible terminal acceptance passed through `start_oauth_agent.bat` in run `learning_agent/acceptance_controller/runs/agent_capability_phase32_windows_native_helper-20260603_081430`.
- Independent verifier replay passed with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Final marker: `PHASE32_WINDOWS_NATIVE_HELPER_READY PHASE32_WINDOWS_NATIVE_HELPER_OK screenshot=true raw_text_hidden=true helper=windows_native_observation helper_available=true optin_guard=true parsed=true width=222`.
- Learning backup copied to `learning_agent/test/agent_capability_phase32_windows_native_helper_20260603/`.

---

## 2026-06-03 Phase 33 Windows OS Computer Use Native Diagnostics

- Added `learning_agent/computer_use/native_diagnostics.py` for structured provider diagnostics.
- Updated `WindowsNativeWindowObservationHelper.status()` to expose `diagnostics`.
- Updated `WindowsComputerUseBackend.status()` to expose `native_observation_diagnostics`.
- Added Phase33 focused tests and visible terminal scenario.
- Red test failed for the expected missing fields: `diagnostics` and `native_observation_diagnostics`.
- Focused test now passes: `python -m unittest learning_agent.tests.test_windows_computer_use_native_diagnostics_phase33`, 3 tests OK.
- Neighbor regression passed: 38 tests OK.
- `py_compile` and scenario JSON validation passed.
- Full regression passed: `python -m unittest discover -s learning_agent\tests`, 644 tests OK, skipped=1.
- Visible terminal acceptance passed through `start_oauth_agent.bat` in run `learning_agent/acceptance_controller/runs/agent_capability_phase33_windows_native_diagnostics-20260603_082834`.
- Independent verifier replay passed with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Final marker: `PHASE33_WINDOWS_NATIVE_DIAGNOSTICS_READY PHASE33_WINDOWS_NATIVE_DIAGNOSTICS_OK phase=phase33_windows_native_diagnostics wgc_known=true uia_known=true active_capture=visible_fake_capture active_text=visible_fake_text safe=true actions_expanded=false`.
- Learning backup copied to `learning_agent/test/agent_capability_phase33_windows_native_diagnostics_20260603/`.
- Current boundary: Phase33 is read-only diagnostics only; it does not expand real mouse or keyboard actions.
- Current phase: complete.

---

## 2026-06-03 Phase 34 Windows OS Computer Use UIAutomation Text Provider

- Added `WindowsUiautomationTextProvider` in `learning_agent/computer_use/native_helper.py`.
- Added `FallbackNativeWindowTextProvider` so UIA failures fall back to Win32 text.
- Updated default `WindowsNativeWindowObservationHelper` text provider to UIA-first fallback.
- Updated package exports in `learning_agent/computer_use/__init__.py`.
- Added Phase34 focused tests and visible terminal scenario.
- Red test failed for the expected missing provider class.
- Focused test now passes: `python -m unittest learning_agent.tests.test_windows_computer_use_uia_provider_phase34`, 6 tests OK.
- Phase32/33 compatibility tests pass: 9 tests OK.
- Scenario JSON validation passed.
- Neighbor regression passed: 44 tests OK.
- `py_compile` passed.
- Full regression passed: `python -m unittest discover -s learning_agent\tests`, 650 tests OK, skipped=1.
- Visible terminal acceptance passed through `start_oauth_agent.bat` in run `learning_agent/acceptance_controller/runs/agent_capability_phase34_windows_uia_text_provider-20260603_090056`.
- Independent verifier replay passed with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Final marker: `PHASE34_WINDOWS_UIA_TEXT_PROVIDER_READY PHASE34_WINDOWS_UIA_TEXT_PROVIDER_OK uia=true fallback=true raw_text_hidden=true actions_expanded=false`.
- Learning backup copied to `learning_agent/test/agent_capability_phase34_windows_uia_text_provider_20260603/`.
- Current boundary: Phase34 is read-only UIA text observation only; it does not expand real mouse or keyboard actions.
- Current phase: complete.

---

## 2026-06-03 Phase 31 Windows OS Computer Use Lock, Abort, Evidence Chain

- Added `ComputerUseAuditStore` for disk-backed Computer Use audit events and evidence chains.
- Extended `ComputerUseLockManager` with stale lock recovery and fixed UTC parsing so new locks are not misclassified as stale on Asia/Shanghai systems.
- Extended `ComputerUseController` so successful actions collect before/after window evidence and persist action chains with one shared `audit_id`.
- Added `/computer status`, `/computer abort`, `/computer clear-abort`, and `/computer release` terminal commands in `learning_agent/app/interactive.py`.
- Added Phase31 focused tests and visible terminal scenario.
- Verification passed: Phase31 focused suite 5 OK; neighboring Computer Use regression 24 OK; `py_compile` OK; scenario JSON OK; full regression 635 tests OK, skipped=1.
- Visible terminal acceptance passed through `start_oauth_agent.bat` in run `learning_agent/acceptance_controller/runs/agent_capability_phase31_windows_lock_abort_evidence-20260603_075659`.
- Independent verifier replay passed with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Final marker: `PHASE31_WINDOWS_LOCK_ABORT_EVIDENCE_READY PHASE31_WINDOWS_LOCK_ABORT_EVIDENCE_OK recovered=true chain=true before=true after=true abort_blocked=true raw_text_hidden=true terminal_abort=true terminal_clear=true coord=34,48`.
- Learning backup copied to `learning_agent/test/agent_capability_phase31_windows_lock_abort_evidence_20260603/`.

---

# 当前任务进度：真实浏览器能力对齐 ClaudeCode（2026-05-31）

- [x] 明确本轮任务范围：真实浏览器能力增强。
- [x] 初步阅读 learning_agent 浏览器相关源码。
- [x] 初步阅读 ClaudeCode Chrome、computer-use、权限、工具执行、恢复和插件相关源码。
- [x] 建立书面计划文档：`agent_memory/browser_claudecode_alignment_plan_20260531.md`。
- [x] 编写浏览器能力缺口测试。
- [x] 实现浏览器动作轨迹和回放。
- [x] 实现页面失败恢复和统一异常重试。
- [x] 实现视觉定位和坐标点击。
- [x] 实现复杂网站流程执行器。
- [x] 实现登录态安全增强和插件兼容状态。
- [x] 备份所有修改到 `learning_agent/test/browser_runtime_alignment_20260531/`。
- [x] 运行自动化测试。
- [x] 执行真实可见终端交互验收：`browser_runtime_alignment-20260531_204032` 通过。

## 2026-06-01 Browser Runtime ClaudeCode alignment execution: Stage 3

- [x] Added `learning_agent/browser/tab_registry.py` for stable tab ids, page_key mapping, active tab switching, and close cleanup.
- [x] Added `learning_agent/browser/session_manager.py` for independent Chromium, visible Chromium, and real Chrome CDP session state.
- [x] Added `learning_agent/tests/test_browser_session_manager.py` with red/green coverage for tab id isolation, profile path redaction, health report fields, and `browser_plugin_status` integration.
- [x] Updated `learning_agent/browser_automation_mcp_server.py` so browser launch, real Chrome connect/disconnect, page register/forget, open, tab new/switch, plugin status, and profile status all sync with `BrowserSessionManager`.
- [x] Copied Stage 3 code/test backups to `learning_agent/test/browser_runtime_claudecode_stage3_20260601/`.
- [x] Verification passed: `python -m unittest learning_agent.tests.test_browser_session_manager` ran 4 tests OK.
- [x] Verification passed: browser/runtime/status focused regression ran 68 tests OK.
- [x] Verification passed: broader browser/status regression ran 126 tests OK, skipped=1.
- [x] Verification passed: `py_compile` for Stage 3 files.
- [x] Real visible terminal acceptance through `learning_agent/start_oauth_agent.bat` passed with run `browser_visible_runtime_acceptance-20260601_105840`.
- [x] Independent verifier passed for `browser_visible_runtime_acceptance-20260601_105840`.
- [x] Debug log confirmed Stage 3 session fields: `session_mode=visible_chromium`, `connected=true`, `visible=true`, `tab_count=1`, `active_tab_id=browser_session_1_fa131c86-tab-1`.
---

## 2026-06-03 Phase 39 Windows OS Computer Use DPI And Multi-Monitor Coordinates

- Added `learning_agent/computer_use/coordinates.py` as the Phase39 coordinate model.
- Updated `learning_agent/computer_use/action_policy.py` so window-relative actions are converted through logical screen, display-relative logical, and physical screen coordinates before backend execution.
- Updated `learning_agent/computer_use/windows_backend.py` and `learning_agent/computer_use/controller.py` so window state can carry display metadata, DPI scale, and a reusable coordinate context.
- Added Phase39 focused tests and a real visible terminal acceptance scenario.
- Red test failed for the expected missing `learning_agent.computer_use.coordinates` module.
- Focused test passed: `python -m unittest learning_agent.tests.test_windows_computer_use_coordinates_phase39`, 5 tests OK.
- Phase30-39 regression passed: 50 tests OK.
- Full regression passed: `python -m unittest discover -s .\learning_agent\tests`, 675 tests OK, skipped=1.
- Real visible terminal acceptance passed through `start_oauth_agent.bat` in run `learning_agent/acceptance_controller/runs/agent_capability_phase39_windows_coordinates-20260603_111521`.
- Independent verifier replay passed with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- Final marker: `PHASE39_WINDOWS_COORDINATES_READY PHASE39_WINDOWS_COORDINATES_OK dpi=true multi_monitor=true action_policy=true window_state=true actions_expanded=false`.
- Learning backup copied to `learning_agent/test/agent_capability_phase39_windows_coordinates_20260603/`.
- Current boundary: Phase39 normalizes coordinates and preserves display metadata; it does not expand the real action surface, and `actions_expanded=false` remains intentional.
---

## 2026-06-03 Phase 40 Windows OS Computer Use Abort, Cleanup, And Notifications

- Added `learning_agent/computer_use/session_runtime.py` for Phase40 session runtime semantics.
- Added durable runtime notifications for global abort and turn cleanup.
- Updated `/computer status` to include a `Computer Runtime` section with runtime model, marker, notification count, cleanup count, last notification, and `actions_expanded=false`.
- Updated `/computer abort <reason>` so it writes the durable abort flag and records a `computer_use_abort_requested` notification.
- Added `/computer cleanup [session_id]` and `/computer notifications`.
- Added Phase40 focused tests and a real visible terminal acceptance scenario.
- Red test failed for the expected missing `learning_agent.computer_use.session_runtime` module.
- Focused test passed: `python -m unittest learning_agent.tests.test_windows_computer_use_session_runtime_phase40`, 4 tests OK.
- Phase30-40 regression passed: 54 tests OK.
- Full regression passed: `python -m unittest discover -s .\learning_agent\tests`, 679 tests OK, skipped=1.
- Real visible terminal acceptance passed through `start_oauth_agent.bat` in run `learning_agent/acceptance_controller/runs/agent_capability_phase40_windows_abort_cleanup-20260603_112730`.
- Independent verifier replay passed with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- Final marker: `PHASE40_WINDOWS_ABORT_CLEANUP_READY PHASE40_WINDOWS_ABORT_CLEANUP_OK abort=true cleanup=true notifications=true terminal_status=true actions_expanded=false`.
- Learning backup copied to `learning_agent/test/agent_capability_phase40_windows_abort_cleanup_20260603/`.
- Current boundary: Phase40 adds runtime safety semantics only; it does not expand real desktop actions.

---

## 2026-06-03 Phase 41 Windows OS Computer Use Model-Visible Image Results

- Added Phase41 image result protocol helpers to `learning_agent/computer_use/evidence.py`.
- `ComputerUseEvidenceStore.save_window_state(...)` now returns and persists `image_results` plus `image_result_count`.
- `ComputerUseActionResult.to_text(...)` now appends a concise `Computer Use Image Results` block for model-readable screenshot artifact references.
- `WindowsComputerUseBackend.get_window_state` now exposes image results at both top-level result data and inside `state`.
- `LearningAgent` now records Computer Use screenshot artifact paths into `active_artifacts`.
- Added Phase41 focused tests and a real visible terminal acceptance scenario.
- Red test failed for the expected missing Phase41 evidence constants/helpers.
- Focused test passed: `python -m unittest learning_agent.tests.test_windows_computer_use_image_results_phase41`, 4 tests OK.
- Windows Computer Use regression passed: 70 tests OK.
- Full regression passed: `python -m unittest discover -s .\learning_agent\tests`, 683 tests OK, skipped=1.
- Real visible terminal acceptance passed through `start_oauth_agent.bat` in run `learning_agent/acceptance_controller/runs/agent_capability_phase41_windows_image_results-20260603_114516`.
- Independent verifier replay passed with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- Final marker: `PHASE41_WINDOWS_IMAGE_RESULTS_READY PHASE41_WINDOWS_IMAGE_RESULTS_OK artifact=true image_block=true agent_artifact=true sensitive_text_hidden=true actions_expanded=false`.
- Learning backup copied to `learning_agent/test/agent_capability_phase41_windows_image_results_20260603/`.
- Current boundary: Phase41 only makes screenshots model-visible as safe artifact references; it does not expand real desktop actions.

---

## 2026-06-03 Phase 42 Windows OS Computer Use Final E2E Matrix

- Added `learning_agent/computer_use/final_matrix.py` as the Phase42 safe contract runner.
- Added `learning_agent/acceptance_controller/final_acceptance_matrix_phase42_windows_computer_use.json`.
- Added Phase42 focused tests and a real visible terminal acceptance scenario.
- The final matrix covers Phase35-41: UIA dependency/safe window, WGC provider contract, SendInput safe fake action, approval/forbidden target, coordinates/window state, abort/cleanup/notifications, and image artifact visibility.
- Red test failed for the expected missing `learning_agent.computer_use.final_matrix` module.
- Focused test passed: `python -m unittest learning_agent.tests.test_windows_computer_use_final_matrix_phase42`, 3 tests OK.
- Windows Computer Use regression passed: 73 tests OK.
- Full regression passed: `python -m unittest discover -s .\learning_agent\tests`, 686 tests OK, skipped=1.
- Real visible terminal acceptance passed through `start_oauth_agent.bat` in run `learning_agent/acceptance_controller/runs/agent_capability_phase42_windows_computer_use_final_matrix-20260603_115600`.
- Independent verifier replay passed with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- Final marker: `PHASE42_WINDOWS_COMPUTER_USE_FINAL_READY PHASE42_WINDOWS_COMPUTER_USE_FINAL_OK phase_count=7 matrix=true observe=true evidence=true approval=true gated_refusal=true safe_action=true abort_cleanup=true artifact_visibility=true actions_expanded=false`.
- Learning backup copied to `learning_agent/test/agent_capability_phase42_windows_computer_use_final_matrix_20260603/`.
- Current boundary: Phase42 is a safe final matrix and does not expand real desktop actions.
- Current status: Phase35-42 blueprint is complete.
---

## 2026-06-03 Phase 43-52 Windows OS Computer Use Production Alignment Started

- User confirmed execution from Phase 43 through Phase 52 without stopping until the blueprint is complete.
- Created persistent plan: `docs/superpowers/plans/2026-06-03-phase43-52-windows-computer-use-production-alignment.md`.
- Created agent memory note: `agent_memory/agent_capability_phase43_52_windows_computer_use_production_20260603.md`.
- Created learning backup: `learning_agent/test/agent_capability_phase43_52_windows_computer_use_production_20260603/phase43_52_blueprint.md`.
- Current phase: Phase 43 Windows native capability diagnostics upgrade.
- Boundary: no production code has been changed yet in this Phase 43-52 run.

---

## 2026-06-03 Phase 43 Windows Native Capability Matrix

- Added Phase43 native capability matrix helpers to `learning_agent/computer_use/native_diagnostics.py`.
- Updated `WindowsComputerUseBackend.status()` so backend status includes `native_capability_matrix`.
- Updated `/computer status` so the visible terminal UI includes `Computer Native Capability Matrix`.
- Added Phase43 focused tests and visible-terminal scenario JSON.
- Red test failed for the expected missing `PHASE43_WINDOWS_NATIVE_CAPABILITY_MARKER`.
- Focused test passed: `python -m unittest learning_agent.tests.test_windows_computer_use_native_capability_matrix_phase43`, 4 tests OK.
- Phase33/42/43 regression passed: 10 tests OK.
- Py compile passed for Phase43 edited Python files.
- CLI selftest passed with marker `PHASE43_WINDOWS_NATIVE_CAPABILITY_READY` and token `PHASE43_WINDOWS_NATIVE_CAPABILITY_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase43_windows_native_capability_matrix_20260603/`.
- Current boundary: Phase43 adds diagnostics and terminal status only; it does not expand real desktop actions.

---

## 2026-06-03 Phase 44 Windows Native Host / Helper Architecture

- Added `learning_agent/computer_use/native_host.py` as an in-process Windows native host/client boundary.
- Added safe message contracts for `status`, `observe`, `capture`, `action`, and `cleanup`.
- Kept Phase44 real actions disabled by default; `action` requests are explicitly refused with `real_action_refused_by_native_host`.
- Added Phase44 focused tests and a visible-terminal scenario JSON.
- Red test failed for the expected missing `learning_agent.computer_use.native_host` module.
- Focused test passed: `python -m unittest learning_agent.tests.test_windows_computer_use_native_host_phase44`, 4 tests OK.
- Phase32/43/44 regression passed: 14 tests OK.
- Py compile passed for `native_host.py` and the Phase44 test file.
- CLI selftest passed with marker `PHASE44_WINDOWS_NATIVE_HOST_READY` and token `PHASE44_WINDOWS_NATIVE_HOST_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase44_windows_native_host_20260603/`.
- Current boundary: Phase44 adds host/client architecture only; it does not execute real mouse, keyboard, or window actions.

---

## 2026-06-03 Phase 45 Windows Screenshot Runtime

- Added `learning_agent/computer_use/screenshot_runtime.py` to coordinate WGC-first, GDI-fallback screenshot capture, evidence artifact saving, and stable CLI self-check tokens.
- Updated `learning_agent/computer_use/native_host.py` so `capture` can use an injected Phase45 screenshot runtime while still returning no raw screenshot bytes.
- Added focused Phase45 tests and visible-terminal scenario `agent_capability_phase45_windows_screenshot_runtime.json`.
- Red test failed first for the expected missing `learning_agent.computer_use.screenshot_runtime` module.
- Verification passed: focused Phase45 tests 4 OK, py_compile OK, Phase32/36/44/45 regression 19 OK, CLI selftest OK.
- Learning backup copied to `learning_agent/test/agent_capability_phase45_windows_screenshot_runtime_20260603/`.
- Boundary: Phase45 proves screenshot runtime wiring and evidence artifact handling with safe injected providers; broad real desktop actions remain gated and not expanded.

---

## 2026-06-03 Phase 46 Windows UIA Control Tree Runtime

- Added `learning_agent/computer_use/uia_tree.py` with structured UIA control tree observation, bounded depth/node output, bounds extraction, clickable/editable hints, and sensitive text redaction.
- Updated `learning_agent/computer_use/native_host.py` so injected UIA tree runtimes can serve `observe` messages.
- Added Phase46 focused tests and visible-terminal scenario `agent_capability_phase46_windows_uia_tree.json`.
- Red test failed first for the expected missing `learning_agent.computer_use.uia_tree` module.
- Verification passed: focused Phase46 tests 4 OK, py_compile OK, Phase34/44/45/46 regression 18 OK, CLI selftest OK.
- Learning backup copied to `learning_agent/test/agent_capability_phase46_windows_uia_tree_20260603/`.
- Boundary: Phase46 is structured, read-only UIA observation; real desktop write actions remain gated and not expanded.

---

## 2026-06-03 Phase 47 Windows SendInput Dispatcher

- Added `learning_agent/computer_use/sendinput_dispatcher.py` with Phase47 dispatcher, low-level event expansion, target-before-send verification, recording sender, and stable CLI self-check tokens.
- Updated `learning_agent/computer_use/native_host.py` so `action` can use an injected action executor only when `real_actions_enabled=True`.
- Added Phase47 focused tests and visible-terminal scenario `agent_capability_phase47_windows_sendinput_dispatcher.json`.
- Red test failed first for the expected missing `learning_agent.computer_use.sendinput_dispatcher` module.
- Verification passed: focused Phase47 tests 4 OK, py_compile OK, Phase37/44/47 regression 13 OK, CLI selftest OK.
- Learning backup copied to `learning_agent/test/agent_capability_phase47_windows_sendinput_dispatcher_20260603/`.
- Boundary: Phase47 proves full action dispatch through safe injected low-level sender; production still requires upstream opt-in, allowlist, lock, abort, approval, target verification, and evidence.

---

## 2026-06-03 Phase 48 Windows Security Policy

- Added `learning_agent/computer_use/security_policy.py` with observe/action/system_key/clipboard grant classification, high-risk default refusal, readable Chinese refusal reasons, and stable Phase48 CLI tokens.
- Updated `learning_agent/computer_use/approval.py` so a caller can inject the Phase48 policy without breaking the Phase38 default approval contract.
- Updated `/computer status` in `learning_agent/app/interactive.py` so the visible terminal can show Phase48 `grant_classes` and high-risk default policy status.
- Added Phase48 focused tests and visible-terminal scenario `agent_capability_phase48_windows_security_policy.json`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.security_policy'`.
- Verification passed: focused Phase48 tests 4 OK; Phase38/48 regression 10 OK; `py_compile` OK; CLI self-check emitted `PHASE48_WINDOWS_SECURITY_POLICY_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase48_windows_security_policy_20260603/`.
- Boundary: Phase48 upgrades approval policy and terminal visibility only; real desktop write actions remain gated and not expanded.

---

## 2026-06-03 Phase 49 Computer Use Tool Surface Compatibility

- Added `learning_agent/computer_use/tool_surface.py` with `computer_use` / `computer-use` compatibility normalization and Phase49 CLI tokens.
- Updated tool schemas, catalog metadata, executor routing, and `LearningAgent._computer_use_compat()` so compatibility aliases dispatch through the existing `computer_status`, `computer_observe`, and `computer_action` controller path.
- Added visible-terminal scenario `agent_capability_phase49_windows_tool_surface.json`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.tool_surface'`.
- Verification passed: focused Phase49 tests 4 OK; Phase27/48/49 regression 12 OK; `py_compile` OK; CLI self-check emitted `PHASE49_COMPUTER_USE_TOOL_SURFACE_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase49_windows_tool_surface_20260603/`.
- Boundary: Phase49 adds tool-name compatibility only; real desktop write actions remain gated and not expanded.

---

## 2026-06-03 Phase 50 Windows Recovery Runtime

- Upgraded `learning_agent/computer_use/session_runtime.py` with Phase50 recovery tokens, explicit stale-lock recovery, cleanup state clearing for abort, and action journal replay from `ComputerUseAuditStore`.
- Updated `/computer` terminal commands in `learning_agent/app/interactive.py` with `/computer recover` and `/computer journal`; `/computer cleanup` now also prints a Phase50 recovery summary.
- Added focused tests and visible-terminal scenario `agent_capability_phase50_windows_recovery_runtime.json`.
- TDD red confirmed first: `ImportError: cannot import name 'PHASE50_WINDOWS_RECOVERY_MARKER'`.
- Verification passed: focused Phase50 tests 5 OK; Phase31/40/50 regression 14 OK; `py_compile` OK; CLI self-check emitted `PHASE50_WINDOWS_RECOVERY_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase50_windows_recovery_runtime_20260603/`.
- Boundary: Phase50 strengthens recovery, cleanup and journal visibility only; real desktop write actions remain gated and not expanded.

---

## 2026-06-03 Phase 51 Computer Status UI

- Added `learning_agent/app/computer_status_renderer.py` with a `/computer`-focused `Computer Summary`, next command, recent action, grant, runtime, native capability, and command sections.
- Added `learning_agent/computer_use/terminal_grants.py` for terminal UI grant/revoke draft state with explicit `terminal_ui_only` scope.
- Updated `learning_agent/app/interactive.py` so `/computer status` uses the compact renderer and `/computer observe`, `/computer grant`, and `/computer revoke` are available.
- Added focused tests and visible-terminal scenario `agent_capability_phase51_computer_status_ui.json`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.app.computer_status_renderer'`.
- Verification passed: focused Phase51 tests 4 OK; Phase21/38/48/50/51 regression 21 OK; `py_compile` OK; CLI self-check emitted `PHASE51_COMPUTER_STATUS_UI_OK`.
- Learning backup copied to `learning_agent/test/agent_capability_phase51_computer_status_ui_20260603/`.
- Boundary: Phase51 upgrades terminal UI and command visibility only; terminal grants are UI drafts and do not bypass controller approval.

---

## 2026-06-03 Phase 52 Windows Production Matrix

- Added `learning_agent/computer_use/production_matrix.py` as the Phase43-51 production aggregate contract.
- Added focused Phase52 tests and visible-terminal scenario `agent_capability_phase52_windows_production_matrix.json`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.production_matrix'`.
- Fixed a Phase43/Phase51 compatibility regression in `learning_agent/app/computer_status_renderer.py`: `/computer status` now keeps `Computer Native Capability Matrix`, the Phase43 marker, and `windows_sendinput` visible while preserving the compact Phase51 panel.
- Verification passed: Phase52 focused tests 2 OK; Phase43-52 regression 39 OK; `py_compile` OK; CLI self-check emitted `PHASE52_WINDOWS_PRODUCTION_MATRIX_OK phase_count=9 native_capability=true native_host=true screenshot_runtime=true uia_tree=true sendinput_dispatcher=true security_policy=true tool_surface=true recovery_runtime=true status_ui=true dispatcher_actions_expanded=true actions_expanded=false`.
- Learning backup copied to `learning_agent/test/agent_capability_phase52_windows_production_matrix_20260603/`.
- Visible terminal launch attempt made with `learning_agent/start_oauth_agent.bat`; process check showed `cmd`/`powershell`/`WindowsTerminal` processes present.
- Real visible terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`: `learning_agent/acceptance_controller/runs/agent_capability_phase52_windows_production_matrix-20260603_143905/result.json` recorded `completed=true`, `prompt_sent=true`, `prompt_received=true`, `final_printed=true`, and all Phase52 answer/log token checks passed.

---

## 2026-06-04 Phase92 Universal Windows Computer Use Mode Blueprint

- User corrected the architecture direction: Computer Use must not become one controller per local software application.
- Read current `task_plan.md`, `findings.md`, `progress.md`, `learning_agent/zqbcontext.md`, Phase65-75 blueprint, Phase90 plan, Phase91 record, and relevant Computer Use source summaries.
- Created product blueprint: `docs/superpowers/specs/2026-06-04-phase92-universal-windows-computer-use-mode-blueprint.md`.
- Created implementation plan: `docs/superpowers/plans/2026-06-04-phase92-universal-windows-computer-use-mode.md`.
- Updated root `task_plan.md` so Phase92 is now the active plan.
- Updated `findings.md` with Phase92 architecture findings.
- Boundary: this step is a written blueprint/implementation plan only. It does not yet implement the Phase92 runtime or expand real desktop actions.

---

## 2026-06-04 Phase92 Universal Windows Computer Use Mode Implementation

- Added `learning_agent/computer_use/universal_mode.py` as the single generic Windows Computer Use mode runtime.
- Added `learning_agent/tests/test_windows_computer_use_universal_mode_phase92.py`.
- Updated `learning_agent/computer_use/tool_surface.py`, `learning_agent/core/agent.py`, `learning_agent/computer_use/__init__.py`, `learning_agent/tools/schemas.py`, and `learning_agent/tests/test_windows_computer_use_tool_surface_phase49.py`.
- Added visible-terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase92_universal_windows_computer_use_mode.json`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.universal_mode'`.
- Focused Phase92 tests passed: 4 OK.
- Phase49/90/91/92 regression passed: 16 OK.
- Windows Computer Use test discovery passed: 217 OK.
- `python -m compileall learning_agent` passed with exit code 0.
- Real visible `start_oauth_agent.bat` terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`: `learning_agent/acceptance_controller/runs/agent_capability_phase92_universal_windows_computer_use_mode-20260604_112311/result.json`.
- Independent result JSON check passed with `completed=true`, `prompt_sent=true`, `prompt_received=true`, `final_printed=true`, `assertion_passed=true`, and `permission_sent_count=0`.
- Learning backup copied to `learning_agent/test/agent_capability_phase92_universal_windows_computer_use_mode_20260604/`, with terminal artifacts under `acceptance_run/`.
- Boundary: Phase92 creates one universal prompt-driven mode and keeps real desktop actions disabled by default; it does not add per-app controllers or uncontrolled input.

---

## 2026-06-04 Phase93 Universal Live Execution Gate

- Added `learning_agent/computer_use/universal_live_execution.py` as the Phase93 universal live execution gate over Phase92.
- Added `learning_agent/tests/test_windows_computer_use_universal_live_execution_phase93.py`.
- Added visible-terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase93_universal_live_execution_gate.json`.
- Exported Phase93 APIs through `learning_agent/computer_use/__init__.py`.
- TDD red confirmed first: package import failed before `UniversalWindowsLiveExecutionGate` existed.
- Focused Phase93 tests passed: 4 OK.
- Phase92 + Phase93 regression passed: 8 OK.
- Windows Computer Use test discovery passed: 221 OK.
- Source-directory compileall passed; full-tree compileall hit historical `learning_agent/test/.../__pycache__` permission errors in backup folders.
- Sandboxed CLI self-check failed because the shell sandbox rejects rename/delete operations used by atomic writes; escalated Phase93 CLI passed and printed the full Phase93 token line.
- Real visible `start_oauth_agent.bat` terminal acceptance was attempted through `learning_agent/acceptance_controller/controller.ps1`: `learning_agent/acceptance_controller/runs/agent_capability_phase93_universal_live_execution_gate-20260604_202037/result.json`.
- The visible terminal run reached `prompt_sent=true`, `prompt_received=true`, and `final_printed=true`, but `completed=false` because the agent model call failed with `OAuth state 不匹配`.
- Boundary: Phase93 code and automated contract are implemented, but Rule 17 visible terminal acceptance has not passed, so this phase must not be called fully complete yet.

Retest update:
- After the `start_oauth_agent.bat` OAuth/model chain repair, the Phase93 visible-terminal scenario was rerun successfully: `learning_agent/acceptance_controller/runs/agent_capability_phase93_universal_live_execution_gate-20260604_203855/result.json`.
- Independent result JSON check passed with `completed=True`, `prompt_sent=True`, `prompt_received=True`, `final_printed=True`, `assertion_passed=True`, and `permission_sent_count=0`.
- Fresh Phase93 focused test passed: 4 OK.
- Fresh Windows Computer Use test discovery passed: 221 OK.
- Phase93 is now accepted under the Rule 17 visible terminal gate.

---

## 2026-06-04 Phase94 Authorized Real Dispatch Candidate

- Added `learning_agent/computer_use/authorized_real_dispatch.py` as the authorized low-level dispatch candidate layer after Phase93.
- Added `learning_agent/tests/test_windows_computer_use_authorized_real_dispatch_phase94.py`.
- Added visible-terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_phase94_authorized_real_dispatch_candidate.json`.
- Exported Phase94 APIs through `learning_agent/computer_use/__init__.py`.
- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.authorized_real_dispatch'`.
- Focused Phase94 tests passed: 4 OK.
- Phase93 + Phase94 regression passed: 8 OK.
- Phase90-94 discovery passed: 20 OK.
- Windows Computer Use test discovery passed: 225 OK.
- Source compile check passed: `python -m compileall -q learning_agent\computer_use learning_agent\tests`.
- Phase94 CLI self-check printed the fixed success token line.
- Scenario JSON validation passed.
- Real visible `start_oauth_agent.bat` terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`: `learning_agent/acceptance_controller/runs/agent_capability_phase94_authorized_real_dispatch_candidate-20260604_210234/result.json`.
- Independent result JSON check passed with `completed=true`, `prompt_sent=true`, `prompt_received=true`, `final_printed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- Learning backup copied to `learning_agent/test/agent_capability_phase94_authorized_real_dispatch_20260604/`, with terminal artifacts under `acceptance_run/`.
- Boundary: Phase94 proves authorized low-level events reach an injected recording sender after safety and target checks. It keeps `real_dispatch_performed=false` and does not claim unrestricted physical control of all Windows apps.
---

## 2026-06-05 Universal Real GUI Computer Use Implementation

Status: active.

Completed:
- Created `docs/superpowers/plans/2026-06-05-universal-real-gui-computer-use.md`.
- Added root task tracking for URG-1 through URG-6.
- Confirmed URG-1 will be a read-only real `ObservationFrame` task with zero mouse and keyboard events.

Next:
- Add URG-1 tests first.
- Implement `learning_agent/computer_use/universal_real_observation.py`.
- Add visible-terminal acceptance scenario for the read-only observation frame.
- Back up new and modified files under `learning_agent/test/`.

Boundary:
- This progress entry does not claim real GUI execution maturity.
- Current mature matrix still says `maturity_known_limit_real_desktop_execution=false` until URG-1 through URG-6 are completed and visibly accepted.

URG-1 update:
- Implemented `learning_agent/computer_use/universal_real_observation.py`.
- Added `learning_agent/tests/test_windows_computer_use_universal_real_observation_frame.py`.
- Added `learning_agent/acceptance_controller/scenarios/agent_capability_universal_real_gui_observation_frame.json`.
- Rewrote `learning_agent/computer_use/__init__.py` as a readable multiline export file while preserving existing Phase98 and Phase93 exports.
- Red test first failed with `ModuleNotFoundError: No module named 'learning_agent.computer_use.universal_real_observation'`.
- Focused URG-1 tests passed: 3 OK.
- Phase56/57/66 adjacent regression passed: 13 OK.
- Windows Computer Use discovery passed: 366 OK.
- `py_compile` and source compileall passed.
- Scenario JSON validation passed.
- Real visible `start_oauth_agent.bat` terminal acceptance passed: `learning_agent/acceptance_controller/runs/agent_capability_universal_real_gui_observation_frame-20260605_213157/result.json`.
- Offline verifier replay passed with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- Backup completed under `learning_agent/test/universal_real_gui_computer_use_urg1_20260605/`.
- URG-1 is complete as a read-only ObservationFrame stage. It does not claim real desktop action maturity.

Next:
- Start URG-2: universal target session and identity guard.

URG-2 update:
- Implemented `learning_agent/computer_use/universal_target_session.py`.
- Added `learning_agent/tests/test_windows_computer_use_universal_target_session.py`.
- Added `learning_agent/acceptance_controller/scenarios/agent_capability_universal_target_session_identity_guard.json`.
- Red test first failed with `ModuleNotFoundError: No module named 'learning_agent.computer_use.universal_target_session'`.
- Focused URG-2 tests passed: 4 OK.
- URG-2 + Phase108 + Phase111 adjacent regression passed: 14 OK.
- Windows Computer Use discovery passed: 370 OK.
- `py_compile`, compileall, and scenario JSON validation passed.
- Real visible `start_oauth_agent.bat` terminal acceptance passed: `learning_agent/acceptance_controller/runs/agent_capability_universal_target_session_identity_guard-20260605_213836/result.json`.
- Offline verifier replay passed with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.
- Boundary: URG-2 proves a generic target session and identity guard with zero desktop input events. It does not yet dispatch real SendInput actions.

Next:
- Start URG-3: generic real action DSL to SendInput.

URG-3 update:
- Implemented `learning_agent/computer_use/universal_action_dsl.py`.
- Added `learning_agent/tests/test_windows_computer_use_universal_action_dsl.py`.
- Added visible-terminal scenario `learning_agent/acceptance_controller/scenarios/agent_capability_universal_action_dsl_sendinput_bridge.json`.
- Rewrote `learning_agent/computer_use/__init__.py` as a clean package export file and added URG-2/URG-3 exports.
- Extended `learning_agent/computer_use/sendinput_dispatcher.py` so `hotkey` expands through the same dispatcher as other actions.
- Red test first failed with `ModuleNotFoundError: No module named 'learning_agent.computer_use.universal_action_dsl'`.
- Focused URG-3 tests passed: 4 OK.
- URG-3 + URG-2 + Phase47 + Phase37 adjacent regression passed: 17 OK.
- Windows Computer Use discovery passed: 374 OK.
- `py_compile`, source compileall, and scenario JSON validation passed.
- Real visible `start_oauth_agent.bat` terminal acceptance passed: `learning_agent/acceptance_controller/runs/agent_capability_universal_action_dsl_sendinput_bridge-20260605_214901/result.json`.
- Result JSON check passed with `completed=true`, `assertion.passed=true`, and `permission_sent_count=0`.

Boundary after URG-3:
- `generic_action_dsl_ready=true`.
- `generic_action_to_sendinput_bridge=true`.
- `normal_actions_reach_low_level_sender=true`.
- `low_level_event_count=22`.
- `target_drift_zero_events=true`.
- `abort_zero_events=true`.
- `type_text_raw_hidden=true`.
- `real_dispatch_performed=false`.
- `real_desktop_touched=false`.
- This is mature for the safe recording-sender DSL-to-SendInput bridge only. It does not yet claim mature physical desktop dispatch.

Next:
- Start URG-4: universal observe-plan-act-verify loop.
