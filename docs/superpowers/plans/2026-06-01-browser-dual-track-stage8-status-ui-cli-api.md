# Stage 8 Status UI CLI API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the dual-track browser provider ecosystem visible through one status surface so other agents can audit provider health, Chrome extension connection, native host state, tabs, permissions, and recent browser evidence.

**Architecture:** Keep the model-facing browser tools unified while adding a provider status block to the existing status snapshot. The snapshot remains the single source for terminal rendering, CLI JSON, SDK helpers, HTTP endpoints, and acceptance scenarios.

**Tech Stack:** Python `unittest`, existing `BrowserProviderRegistry`, `ChromeExtensionBridgeState`, `BrowserRuntimeStore`, `render_status_snapshot`, `learning_agent.harness.cli`, HTTP command bridge.

---

### Task 1: Provider Status Snapshot

**Files:**
- Modify: `learning_agent/runtime/status_snapshot.py`
- Test: `learning_agent/tests/test_chrome_extension_status_ecosystem_stage8.py`

- [ ] **Step 1: Write failing test**

Create a test that writes `learning_agent/memory/chrome_extension_bridge.json` with connected extension state, tabs, pending command, command result, and permission event. Assert `build_status_snapshot(root)["browser"]["provider_status"]` contains `providers`, `chrome_extension`, `tabs`, `permissions`, `native_host`, and `recent_actions`.

- [ ] **Step 2: Run focused test and confirm RED**

Run: `python -m unittest learning_agent.tests.test_chrome_extension_status_ecosystem_stage8`

Expected: fail because `provider_status` is missing.

- [ ] **Step 3: Implement minimal snapshot aggregation**

Add helper functions in `status_snapshot.py` to locate `chrome_extension_bridge.json`, safely load it, derive provider health, tab context, active tab, permission event counts, pending command counts, and recent browser actions/observations.

- [ ] **Step 4: Run focused test and confirm GREEN**

Run: `python -m unittest learning_agent.tests.test_chrome_extension_status_ecosystem_stage8`

Expected: pass.

### Task 2: Terminal Renderer And SDK

**Files:**
- Modify: `learning_agent/app/status_renderer.py`
- Modify: `learning_agent/sdk/status.py`
- Test: `learning_agent/tests/test_chrome_extension_status_ecosystem_stage8.py`

- [ ] **Step 1: Add failing renderer and SDK assertions**

Assert `render_status_snapshot(snapshot)` includes `Browser Providers`, `chrome_extension`, `pending_command_count`, `permission_event_count`, and active tab URL. Assert SDK helper `get_browser_provider_status(root)` returns the same provider block from the snapshot.

- [ ] **Step 2: Run focused test and confirm RED**

Run: `python -m unittest learning_agent.tests.test_chrome_extension_status_ecosystem_stage8`

Expected: fail because renderer text and SDK helper are missing.

- [ ] **Step 3: Implement renderer and SDK**

Render a compact provider section below Browser Runtime. Add SDK helper that reads `snapshot["browser"]["provider_status"]` with type safety.

- [ ] **Step 4: Run focused test and confirm GREEN**

Run: `python -m unittest learning_agent.tests.test_chrome_extension_status_ecosystem_stage8`

Expected: pass.

### Task 3: Tool And HTTP API Entrypoints

**Files:**
- Modify: `learning_agent/browser_automation_mcp_server.py`
- Modify: `learning_agent/app/http_bridge.py`
- Modify: `learning_agent/harness/cli.py`
- Test: `learning_agent/tests/test_chrome_extension_status_ecosystem_stage8.py`

- [ ] **Step 1: Add failing API assertions**

Assert `BrowserAutomationServer.call("browser_provider_status", {})` returns provider health and extension status. Assert HTTP GET `/browser/providers` and `/v1/browser/providers` return the provider status block. Assert CLI `provider-status --workspace <root>` prints provider and extension fields.

- [ ] **Step 2: Run focused test and confirm RED**

Run: `python -m unittest learning_agent.tests.test_chrome_extension_status_ecosystem_stage8`

Expected: fail because tool, HTTP route, and CLI command are missing.

- [ ] **Step 3: Implement tool/API/CLI**

Add schema and dispatch for `browser_provider_status`, HTTP routes `/browser/providers` and `/v1/browser/providers`, and CLI `provider-status`. Keep all outputs backed by `build_status_snapshot()`.

- [ ] **Step 4: Run focused test and confirm GREEN**

Run: `python -m unittest learning_agent.tests.test_chrome_extension_status_ecosystem_stage8`

Expected: pass.

### Task 4: Acceptance And Documentation Backup

**Files:**
- Create: `learning_agent/acceptance_controller/scenarios/chrome_extension_status_ecosystem_stage8_acceptance.json`
- Create: `learning_agent/test/browser_dual_track_stage8_20260601/modified_snippets.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`

- [ ] **Step 1: Create acceptance scenario**

Scenario prompt must call or inspect `browser_provider_status` and require marker `CHROME_EXTENSION_STAGE8_READY STAGE8_STATUS_ECOSYSTEM_OK`.

- [ ] **Step 2: Back up modified code snippets and plan**

Write a learning copy under `learning_agent/test/browser_dual_track_stage8_20260601/`.

- [ ] **Step 3: Run regression suite**

Run focused Stage 8 test, related Stage 5-8 provider tests, `py_compile` on touched Python files, and full `python -m unittest discover -s learning_agent\tests`.

- [ ] **Step 4: Run visible terminal/controller acceptance**

Run the Stage 8 acceptance controller and independent verifier. Only mark Stage 8 complete if both automation and real visible terminal acceptance pass.

