# Learning Agent Progress

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
- Current boundary: Phase34 is read-only UIA text observation only; it does not expand real mouse or keyboard actions.
- Current phase: verification in progress.

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
