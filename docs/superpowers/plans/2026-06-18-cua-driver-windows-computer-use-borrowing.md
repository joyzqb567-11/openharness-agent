# Cua Driver Windows Computer Use Borrowing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep OpenHarness ClaudeCode-compatible Computer Use tool surface unchanged, while borrowing the high-value Windows execution ideas from Hermes' `cua-driver` source to improve OpenHarness Windows Computer Use reliability.

**Architecture:** OpenHarness remains ClaudeCode-facing at the MCP/tool layer. The `cua-driver` ideas are absorbed only into the internal Windows runtime layer: element-indexed observation cache, UIA/MSAA action dispatch, strict window identity, coordinate contracts, background dispatch diagnostics, and stronger observe-act-verify evidence.

**Tech Stack:** Python OpenHarness runtime, Windows UIA/Win32/SendInput integration, OpenHarness MCP v2 compatibility layer, CodeGraph, `unittest`, visible `learning_agent/start_oauth_agent.bat` terminal acceptance.

---

## 1. Why This Blueprint Exists

The user wants OpenHarness Computer Use to stay aligned with ClaudeCode as much as possible, but OpenHarness is primarily a Windows agent. ClaudeCode's missing external Computer Use package cannot be inspected locally, while Hermes' `cua-driver` is now present in `D:\hermes-agent-main\cua-driver\libs\cua-driver` and indexed by CodeGraph.

This plan prevents the long task from drifting in three ways:

- It keeps the ClaudeCode-compatible OpenHarness tool names and model-facing schema as the primary contract.
- It borrows only Windows runtime techniques that are visible in `cua-driver` source.
- It defines phase gates, stop conditions, tests, and real visible terminal acceptance before any phase can be called complete.

## 2. Source Evidence Baseline

### 2.1 Hermes And Cua Driver Evidence

- `D:\hermes-agent-main\tools\computer_use\cua_backend.py` shows Hermes starts `cua-driver mcp` over stdio.
- `D:\hermes-agent-main\tools\computer_use\tool.py` wraps Computer Use approval, capture-after behavior, and multimodal responses.
- `D:\hermes-agent-main\cua-driver\libs\cua-driver\rust\crates\cua-driver-core\src\protocol.rs` defines MCP JSON-RPC request, response, tool result, image content, `structuredContent`, and agent instructions.
- `D:\hermes-agent-main\cua-driver\libs\cua-driver\rust\crates\cua-driver-core\src\server.rs` implements the stdio MCP server loop.
- `D:\hermes-agent-main\cua-driver\libs\cua-driver\rust\crates\cua-driver-core\src\tool.rs` implements `ToolDef`, `Tool`, `ToolRegistry`, tool annotations, session tools, recording tools, and invocation hooks.
- `D:\hermes-agent-main\cua-driver\libs\cua-driver\rust\crates\platform-windows\src\tools\impl_.rs` implements Windows tools such as `get_window_state`, `click`, `type_text`, `set_value`, `scroll`, `launch_app`, `list_windows`, `check_permissions`, config, recording, and session helpers.
- `D:\hermes-agent-main\cua-driver\libs\cua-driver\rust\crates\platform-windows\src\uia\cache.rs` implements a per-window element cache for UIA/MSAA targets.
- `D:\hermes-agent-main\cua-driver\libs\cua-driver\rust\crates\platform-windows\src\input\mod.rs` implements Win32 input dispatch concepts and UIPI diagnostics.

### 2.2 OpenHarness Evidence

- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/build_tools.py` is the ClaudeCode-compatible 24-tool surface and must remain the model-facing baseline.
- `learning_agent/computer_use/uia_tree.py` currently provides Windows UIA tree data and is a likely source for element snapshot metadata.
- `learning_agent/computer_use_mcp_v2/windows_runtime/universal_real_observation.py` currently fuses real Windows observation evidence and is the likely place to attach element-index metadata.
- `learning_agent/computer_use_mcp_v2/windows_runtime/real_sendinput_guard.py` currently owns low-level Windows input sending and cleanup.
- `learning_agent/computer_use_mcp_v2/windows_runtime/mode_session.py` and `learning_agent/computer_use/mode_session.py` currently enforce mode, permission, and action class boundaries.
- `learning_agent/computer_use_mcp_v2/windows_runtime/session_runtime.py`, `turn_cleanup.py`, permission modules, and MCP adapter files must be rechecked with CodeGraph before implementation because they sit in the live action path.

## 3. Main Decision

Borrow `cua-driver` as a Windows runtime reference, not as a replacement runtime.

OpenHarness must not replace its ClaudeCode-compatible tool names with `cua-driver` tool names. Instead, OpenHarness should keep tools like `observe`, `screenshot`, `left_click`, `type`, `key`, `scroll`, `open_application`, `request_access`, and `computer_batch`, then use Cua-inspired internals to make those tools more reliable on Windows.

## 4. In Scope

- Element-indexed observation snapshots similar to `cua-driver` `get_window_state`.
- Stable per-window element cache scoped by target process and target window.
- Strict `pid + window_id` validation before action dispatch.
- Window-local screenshot coordinate contract and conversion to physical screen coordinates.
- UIA/MSAA-first action dispatch before low-level SendInput fallback.
- `set_value` and text input improvements through UIA ValuePattern and RangeValuePattern when available.
- Background/no-focus-steal dispatch diagnostics where Windows APIs make it possible.
- UIPI/integrity-level diagnostics when Windows blocks cross-integrity input.
- Stronger action evidence: before observation, chosen target, dispatch path, fallback path, after observation, verification result.
- Tests, learning backup, project memory updates, and visible terminal acceptance.

## 5. Out Of Scope

- Replacing OpenHarness MCP v2 ClaudeCode-compatible tool surface.
- Making `cua-driver` a mandatory runtime dependency.
- Copying macOS Swift/SkyLight behavior into the Windows runtime.
- Bypassing OpenHarness permission UI, target guard, abort, cleanup, or audit rules.
- Claiming ClaudeCode hidden external package behavior is fully known.
- Claiming `cua-driver` screenshot tool parity until the actual built Windows tool list is verified, because the source currently contains signs that `screenshot` may have moved behind `get_window_state(capture_mode="vision")` while some examples still reference screenshot parity.

## 6. Success Criteria

- OpenHarness still exposes the ClaudeCode-compatible 24 Computer Use tool names.
- No existing permission, lock, cleanup, abort, and dangerous target behavior regresses.
- Real Windows observation can return element-indexed targets that actions can reference through the internal runtime.
- `left_click` can prefer UIA/MSAA element action over raw coordinate click when an element index is available.
- `type` and `set_value` can use semantic UIA value paths for editable controls when available.
- Coordinate conversion is explicitly labeled as screenshot-local, window-local, or screen-physical.
- Action results identify the dispatch path, fallback path, target identity, and verification status.
- Cross-integrity failures return understandable diagnostics instead of silent success.
- Focused tests pass.
- Relevant Windows Computer Use regression tests pass.
- `python -m compileall learning_agent` or a narrower agreed compile gate passes.
- `learning_agent/start_oauth_agent.bat` visible terminal acceptance passes before any implementation phase is called complete.
- All new or modified code is copied to `learning_agent/test/<phase-name>/` according to the project rules.

## 7. Stop Conditions

Stop and report before coding further if any condition appears:

- The implementation requires installing a system driver, Windows service, global hook, registry edit, UAC policy change, or security-policy change.
- The target action would interact with passwords, payment, OTP, tokens, administrator prompts, security settings, terminal dangerous commands, or private user data.
- The new internal action path would bypass `request_access`, action mode checks, lock ownership, abort flag, or turn cleanup.
- CodeGraph shows that the current OpenHarness action path differs materially from the file map in this plan.
- A test can pass only by weakening existing safety checks.
- Visible terminal acceptance cannot be completed. In that case the final answer must say: “真实可见终端交互验收未完成，不能声明开发完成。”

## 8. File Map

### Create

- `learning_agent/computer_use/windows_element_cache.py`  
  Owns a Python-side per-window element snapshot cache inspired by `cua-driver` `ElementCache`.

- `learning_agent/computer_use/windows_coordinate_contract.py`  
  Owns coordinate labels and conversion helpers for screenshot-local, window-local, and screen-physical coordinates.

- `learning_agent/computer_use/windows_uia_patterns.py`  
  Owns semantic UIA action attempts such as Invoke, Toggle, SelectionItem, ExpandCollapse, ValuePattern, and RangeValuePattern.

- `learning_agent/computer_use/windows_integrity.py`  
  Owns process integrity and UIPI diagnostic helpers.

- `learning_agent/tests/test_computer_use_windows_element_cache.py`  
  Tests element cache scoping, replacement, lookup, and expiry behavior.

- `learning_agent/tests/test_computer_use_windows_coordinate_contract.py`  
  Tests coordinate labeling and conversion invariants.

- `learning_agent/tests/test_computer_use_windows_uia_patterns.py`  
  Tests semantic action dispatch order with fake UIA controls.

- `learning_agent/tests/test_computer_use_windows_integrity.py`  
  Tests UIPI diagnostic decisions with fake process metadata.

- `learning_agent/tests/test_computer_use_cua_driver_borrowing_matrix.py`  
  Tests the final borrowing matrix and safety boundary.

- `scenarios/agent_capability_cua_driver_borrowing_visible_terminal.json`  
  Visible terminal acceptance scenario for the final phase.

### Modify

- `learning_agent/computer_use/uia_tree.py`  
  Add or expose stable element metadata needed by the element cache. Do not leak sensitive text beyond existing filtering rules.

- `learning_agent/computer_use_mcp_v2/windows_runtime/universal_real_observation.py`  
  Attach element-index metadata and cache update calls to real observation frames.

- `learning_agent/computer_use_mcp_v2/windows_runtime/real_sendinput_guard.py`  
  Add dispatch-path reporting, coordinate contract validation, and optional semantic-dispatch fallback boundaries.

- `learning_agent/computer_use_mcp_v2/windows_runtime/session_runtime.py`  
  Route action requests through element cache and semantic dispatch when available.

- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/runtime.py`  
  Preserve ClaudeCode-compatible tool inputs while passing internal element references into the Windows runtime when the observation has them.

- `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py`  
  Add internal-only structured result fields if needed. Do not break the external schema.

- `learning_agent/computer_use_mcp_v2/windows_runtime/turn_cleanup.py`  
  Ensure any new cursor, cache lease, pressed key, or temporary state is cleaned after each turn.

- `agent_memory/context.md`, `agent_memory/progress.md`, and `agent_memory/bugs.md`  
  Record phase status, decisions, risks, and failures.

## 9. Phase Plan

### Phase 0: Reconfirm CodeGraph And Lock Scope

**Purpose:** Prevent stale assumptions before touching code.

- [ ] Run `codegraph status .` in `H:\codexworkplace\sofeware\OpenHarness-main`.
- [ ] Run `codegraph status .` in `D:\hermes-agent-main`.
- [ ] Use `codegraph_explore` on OpenHarness action path files listed in section 8.
- [ ] Use `codegraph_explore` on the Cua driver evidence files listed in section 2.
- [ ] Write a short evidence note to `agent_memory/progress.md`.
- [ ] Stop if CodeGraph is missing, stale, or shows the file map is no longer accurate.

**Acceptance:** The implementer can point to current source for both the OpenHarness target path and the Cua reference path.

### Phase 1: Data Contract For Element-Indexed Observation

**Purpose:** Add a safe internal contract before changing real actions.

- [ ] Write failing tests for `WindowsElementSnapshot`, `WindowsElementSnapshotCache`, and per-window replacement semantics.
- [ ] Implement `learning_agent/computer_use/windows_element_cache.py`.
- [ ] The cache key must include process identity and window identity.
- [ ] A new observation for the same target must replace old indices for that target.
- [ ] A lookup with a mismatched process or window must fail closed.
- [ ] No sensitive raw text may be stored beyond the existing UIA filtering boundary.
- [ ] Run `python -m unittest learning_agent.tests.test_computer_use_windows_element_cache -v`.
- [ ] Copy new and modified files to `learning_agent/test/cua_driver_borrowing_phase1_element_cache_20260618/`.

**Acceptance:** Element indices are useful only inside the exact target window snapshot that produced them.

### Phase 2: Attach Element Cache To Observation

**Purpose:** Make observation produce action-addressable targets without changing public tool names.

- [ ] Write failing tests proving an observation frame can update the element cache.
- [ ] Modify `learning_agent/computer_use/uia_tree.py` only if existing UIA nodes lack required stable fields.
- [ ] Modify `learning_agent/computer_use_mcp_v2/windows_runtime/universal_real_observation.py` to update the cache after successful observation.
- [ ] The result must include a bounded, non-sensitive element summary for audit.
- [ ] The model-facing ClaudeCode-compatible schema must remain unchanged.
- [ ] Run the new observation/cache tests.
- [ ] Run existing observation-related Windows Computer Use tests.
- [ ] Copy new and modified files to `learning_agent/test/cua_driver_borrowing_phase2_observation_cache_20260618/`.

**Acceptance:** OpenHarness can observe a window and produce an internal element-index map that a later action can use.

### Phase 3: Coordinate Contract And Strict Window Identity

**Purpose:** Remove ambiguity between screenshot pixels, window coordinates, and screen coordinates.

- [ ] Write failing tests for coordinate labels and rejected mixed-coordinate payloads.
- [ ] Implement `learning_agent/computer_use/windows_coordinate_contract.py`.
- [ ] Require every low-level action candidate to state whether coordinates are screenshot-local, window-local, or screen-physical.
- [ ] Add target identity validation before coordinate conversion.
- [ ] Ensure `pid + window_id` mismatch fails closed.
- [ ] Preserve current safe behavior for actions that already carry verified target identity.
- [ ] Run `python -m unittest learning_agent.tests.test_computer_use_windows_coordinate_contract -v`.
- [ ] Run relevant target identity regression tests.
- [ ] Copy new and modified files to `learning_agent/test/cua_driver_borrowing_phase3_coordinate_identity_20260618/`.

**Acceptance:** A click cannot silently drift to another window or another coordinate space.

### Phase 4: UIA/MSAA Semantic Action Dispatch

**Purpose:** Improve Windows control reliability by using semantic actions before raw input.

- [ ] Write failing tests for dispatch order: Invoke, Toggle, SelectionItem, ExpandCollapse, ValuePattern, RangeValuePattern, then existing fallback.
- [ ] Implement `learning_agent/computer_use/windows_uia_patterns.py` with fakeable interfaces so tests do not require a live desktop.
- [ ] Connect element-indexed `left_click` to semantic click attempts when the cached element has a supported control pattern.
- [ ] Connect `type` or internal text entry to ValuePattern when the target is editable and safe.
- [ ] Connect `set_value`-style internal behavior to ValuePattern and RangeValuePattern where appropriate.
- [ ] Keep raw SendInput fallback behind the existing permission, target, lock, and abort gates.
- [ ] Record `dispatch_path` and `fallback_path` in action evidence.
- [ ] Run `python -m unittest learning_agent.tests.test_computer_use_windows_uia_patterns -v`.
- [ ] Run relevant Windows action regression tests.
- [ ] Copy new and modified files to `learning_agent/test/cua_driver_borrowing_phase4_uia_patterns_20260618/`.

**Acceptance:** Standard Windows controls can be operated semantically when available, and the action result says exactly which path was used.

### Phase 5: Background Dispatch Diagnostics And UIPI

**Purpose:** Make Windows failure reasons clear instead of pretending success.

- [ ] Write failing tests for lower-integrity sender to higher-integrity target diagnostics.
- [ ] Implement `learning_agent/computer_use/windows_integrity.py`.
- [ ] Add structured result fields for `background_unavailable`, `integrity_blocked`, `target_not_accessible`, and `semantic_pattern_unavailable`.
- [ ] Do not elevate, change UAC, change registry, or request administrator privileges automatically.
- [ ] Ensure failed background dispatch can recommend a safe foreground-confirmed fallback only if existing permissions allow it.
- [ ] Run `python -m unittest learning_agent.tests.test_computer_use_windows_integrity -v`.
- [ ] Run safety policy regression tests.
- [ ] Copy new and modified files to `learning_agent/test/cua_driver_borrowing_phase5_uipi_diagnostics_20260618/`.

**Acceptance:** When Windows blocks the action, the user gets a truthful reason and OpenHarness does not claim success.

### Phase 6: Observe-Act-Verify Integration

**Purpose:** Make the borrowed runtime behavior useful in the full agent loop.

- [ ] Write failing tests showing an observed element index can drive one safe action and then produce after-evidence.
- [ ] Modify runtime routing so internal element references can flow from observation to action without exposing an incompatible public tool schema.
- [ ] Require before/after evidence for any real desktop action.
- [ ] Preserve lock ownership, abort flag, cleanup, sensitive text redaction, and permission decision fields.
- [ ] Add verification result fields: `verified`, `verification_method`, `before_evidence`, `after_evidence`, `target_still_same`.
- [ ] Run focused observe-act-verify tests.
- [ ] Run Windows Computer Use regression tests.
- [ ] Copy new and modified files to `learning_agent/test/cua_driver_borrowing_phase6_observe_act_verify_20260618/`.

**Acceptance:** A real action can be explained as: observed target, selected element, chosen dispatch path, executed action, verified result.

### Phase 7: Optional Session Cursor And Recording Inspiration

**Purpose:** Borrow only the user-visible debugging ideas that are safe after the core runtime works.

- [ ] Decide whether to implement this phase after Phases 1-6 pass.
- [ ] If implemented, write tests for session-scoped cursor state that never replaces the real permission gate.
- [ ] If implemented, add a debug-only cursor/trace surface that can be disabled and cleaned per turn.
- [ ] If implemented, add recording metadata only for action summaries, never raw secrets.
- [ ] If skipped, record the reason in `agent_memory/progress.md`.

**Acceptance:** This phase is allowed to be skipped without blocking core reliability. It must not delay P0 runtime fixes.

### Phase 8: Final Matrix And Visible Terminal Acceptance

**Purpose:** Prove the borrowing work is complete without confusing it with full ClaudeCode hidden package parity.

- [ ] Add `learning_agent/tests/test_computer_use_cua_driver_borrowing_matrix.py`.
- [ ] Matrix must report ClaudeCode-compatible tool surface unchanged.
- [ ] Matrix must report Cua-inspired element cache present.
- [ ] Matrix must report UIA semantic dispatch present.
- [ ] Matrix must report coordinate contract present.
- [ ] Matrix must report UIPI diagnostics present.
- [ ] Matrix must report hidden ClaudeCode package internals still excluded.
- [ ] Add `scenarios/agent_capability_cua_driver_borrowing_visible_terminal.json`.
- [ ] Run focused tests from Phases 1-8.
- [ ] Run the relevant Windows Computer Use regression suite.
- [ ] Run compile check.
- [ ] Start `learning_agent/start_oauth_agent.bat` through the real visible terminal acceptance controller.
- [ ] Confirm final visible output includes a clear success token such as `CUA_DRIVER_WINDOWS_BORROWING_OK`.
- [ ] Copy final modified files to `learning_agent/test/cua_driver_borrowing_final_20260618/`.
- [ ] Update `agent_memory/progress.md`, `agent_memory/context.md`, and `agent_memory/bugs.md`.

**Acceptance:** OpenHarness has borrowed the valuable Windows implementation ideas while staying ClaudeCode-compatible at the public Computer Use interface.

## 10. Verification Commands

Use the exact commands after implementation, adjusting only test names if CodeGraph shows files were renamed:

```powershell
python -m unittest learning_agent.tests.test_computer_use_windows_element_cache -v
python -m unittest learning_agent.tests.test_computer_use_windows_coordinate_contract -v
python -m unittest learning_agent.tests.test_computer_use_windows_uia_patterns -v
python -m unittest learning_agent.tests.test_computer_use_windows_integrity -v
python -m unittest learning_agent.tests.test_computer_use_cua_driver_borrowing_matrix -v
python -m compileall learning_agent
powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_cua_driver_borrowing_visible_terminal.json
```

## 11. Expected Final Report Shape

The final report after implementation must include:

- What changed.
- Which Cua driver ideas were borrowed.
- Which ClaudeCode-compatible OpenHarness tool contracts stayed unchanged.
- Which tests passed.
- The visible terminal acceptance result path.
- Any skipped optional phase and why it was skipped.
- A clear statement if visible terminal acceptance was not completed.

## 12. Recommended Execution Order

Execute Phases 0 through 6 first. Phase 7 is intentionally optional and must not block the core reliability work. Phase 8 is mandatory before claiming completion.

The most important invariant is: OpenHarness should become better at Windows Computer Use internally, while still behaving like the ClaudeCode-compatible Computer Use server externally.

## 13. Execution Result 2026-06-18

- Phase 0 completed: CodeGraph freshness was checked for OpenHarness and Hermes/Cua driver sources.
- Phase 1 completed: Windows element index cache was implemented and tested.
- Phase 2 completed: Universal real observation now updates and exposes element cache summaries.
- Phase 3 completed: Windows coordinate-space and strict target identity contract was implemented and tested.
- Phase 4 completed: UIA Invoke/Toggle/Value/RangeValue semantic dispatch was implemented and tested.
- Phase 5 completed: UIPI/integrity diagnostic helpers were implemented and tested.
- Phase 6 completed: MCP v2 `element_index` observe-act-verify path now uses cached UIA semantic dispatch before host fallback when safe.
- Phase 7 skipped by design: cursor heatmap/recording is optional UX/debug surface and not required for core reliability.
- Phase 8 completed: final matrix, manifest, report, scenario, automated tests, py_compile, and real visible terminal acceptance passed.
- Visible terminal run: `learning_agent/acceptance_controller/runs/agent_capability_cua_driver_borrowing_visible_terminal-20260618_170814`.
- Final success token observed: `CUA_DRIVER_WINDOWS_BORROWING_OK`.
