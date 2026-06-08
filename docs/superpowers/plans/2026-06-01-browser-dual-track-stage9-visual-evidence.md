# Stage 9 Visual Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add browser recording evidence so real browser tasks can produce auditable frame sequences and GIF artifacts, similar to ClaudeCode's browser visual evidence direction.

**Architecture:** Add a focused `BrowserRecordingStore` that owns recording manifests, frame paths, GIF export, and self-test artifact creation. Wire it into `BrowserAutomationServer` through unified tools (`browser_record_start`, `browser_record_stop`, `browser_gif_export`) and auto-capture frames after successful browser actions. Extend status snapshot and acceptance verifier so other agents can see and verify generated visual evidence.

**Tech Stack:** Python `unittest`, Pillow (`PIL.Image`) for GIF export, existing `BrowserRuntimeStore`, `BrowserScreenshotIndex`, `status_snapshot`, `acceptance.verifier`, and visible terminal acceptance controller.

---

### Task 1: Recording Store And GIF Export

**Files:**
- Create: `learning_agent/browser/recording.py`
- Modify: `learning_agent/browser/runtime_events.py`
- Test: `learning_agent/tests/test_browser_recording_stage9.py`

- [ ] **Step 1: Write failing tests**

Create tests that:
- Start a recording with `BrowserRecordingStore.start_recording()`.
- Add two small PNG frames using Pillow.
- Stop the recording.
- Export a GIF with `export_gif()`.
- Assert manifest exists, frame files exist, GIF exists, and manifest has `status=exported`.

- [ ] **Step 2: Run focused test and confirm RED**

Run: `python -m unittest learning_agent.tests.test_browser_recording_stage9`

Expected: fail because `learning_agent.browser.recording` does not exist.

- [ ] **Step 3: Implement recording store**

Implement:
- `BrowserRecordingStore`
- `start_recording(recording_id="", run_id="", page_id="", metadata=None)`
- `record_frame(recording_id, frame_path, tool_name="", action_id="", page_id="", url="", title="")`
- `stop_recording(recording_id)`
- `export_gif(recording_id, output_name="", duration_ms=700)`
- `list_recordings(limit=20)`
- `run_recording_selftest(workspace)`

Use Pillow only; do not introduce new dependencies.

- [ ] **Step 4: Run focused test and confirm GREEN**

Run: `python -m unittest learning_agent.tests.test_browser_recording_stage9`

Expected: pass.

### Task 2: Browser Tool Surface And Auto Frames

**Files:**
- Modify: `learning_agent/browser_automation_mcp_server.py`
- Test: `learning_agent/tests/test_browser_recording_stage9.py`

- [ ] **Step 1: Add failing server assertions**

Extend tests to assert:
- `browser_record_start`, `browser_record_stop`, and `browser_gif_export` exist in `TOOLS`.
- `BrowserAutomationServer.call("browser_record_start", {})` starts a recording.
- A fake page screenshot can be captured as a frame through the server helper.
- `browser_gif_export` returns a real GIF artifact path.

- [ ] **Step 2: Run focused test and confirm RED**

Run: `python -m unittest learning_agent.tests.test_browser_recording_stage9`

Expected: fail because the server tools and helper are missing.

- [ ] **Step 3: Implement server integration**

Add:
- Tool schemas for `browser_record_start`, `browser_record_stop`, `browser_gif_export`.
- Dispatch handlers.
- `self.browser_recording_store`.
- Active recording id/state.
- `_capture_recording_frame(tool_name, action_id="")` that saves PNG frames under `browser_artifacts/browser_recordings/<recording_id>/frames/`.
- A call from `on_attempt_success()` so successful browser actions auto-capture frames without the model choosing a second tool.

- [ ] **Step 4: Run focused test and confirm GREEN**

Run: `python -m unittest learning_agent.tests.test_browser_recording_stage9`

Expected: pass.

### Task 3: Status Snapshot And Verifier Artifact Gate

**Files:**
- Modify: `learning_agent/runtime/status_snapshot.py`
- Modify: `learning_agent/app/status_renderer.py`
- Modify: `learning_agent/acceptance/verifier.py`
- Test: `learning_agent/tests/test_browser_recording_stage9.py`
- Test: `learning_agent/tests/test_acceptance_verifier.py`

- [ ] **Step 1: Add failing assertions**

Tests must assert:
- `build_status_snapshot(workspace)["browser"]["recordings"]` lists recent recordings.
- `render_status_snapshot()` includes `Browser Recordings`, `recording_id`, `frame_count`, and GIF path.
- The acceptance verifier can check `required_artifact_globs` with `{project_root}` and `{run_dir}` placeholders.

- [ ] **Step 2: Run focused tests and confirm RED**

Run: `python -m unittest learning_agent.tests.test_browser_recording_stage9 learning_agent.tests.test_acceptance_verifier`

Expected: fail because status and verifier do not know recordings or required globs yet.

- [ ] **Step 3: Implement status and verifier support**

Add:
- `_load_browser_recordings(root)` in `status_snapshot.py`.
- A `Browser Recordings` renderer block.
- `required_artifact_globs` support in `acceptance/verifier.py`, where each glob can use `{project_root}` and `{run_dir}`.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run: `python -m unittest learning_agent.tests.test_browser_recording_stage9 learning_agent.tests.test_acceptance_verifier`

Expected: pass.

### Task 4: Acceptance, Backup, And Regression

**Files:**
- Create: `learning_agent/acceptance_controller/scenarios/browser_visual_evidence_stage9_acceptance.json`
- Create: `learning_agent/test/browser_dual_track_stage9_20260601/plan.md`
- Create: `learning_agent/test/browser_dual_track_stage9_20260601/modified_snippets.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`

- [ ] **Step 1: Create acceptance scenario**

The scenario must require the visible-terminal agent to run:
- `python -m unittest learning_agent.tests.test_browser_recording_stage9`
- `python -m learning_agent.browser.recording --selftest --workspace H:\codexworkplace\sofeware\OpenHarness-main`

The scenario must require final marker:
`BROWSER_VISUAL_EVIDENCE_STAGE9_READY STAGE9_VISUAL_EVIDENCE_OK`

The scenario must include `required_artifact_globs` for:
- `{project_root}/browser_artifacts/browser_recordings/stage9_selftest_*/recording_manifest.json`
- `{project_root}/browser_artifacts/browser_recordings/stage9_selftest_*/frames/*.png`
- `{project_root}/browser_artifacts/browser_recordings/stage9_selftest_*/stage9_selftest.gif`

- [ ] **Step 2: Run regression suite**

Run:
- `python -m unittest learning_agent.tests.test_browser_recording_stage9`
- `python -m unittest learning_agent.tests.test_browser_recording_stage9 learning_agent.tests.test_chrome_extension_status_ecosystem_stage8 learning_agent.tests.test_browser_status_ecosystem`
- `python -m py_compile` on touched Python files.
- `python -m unittest discover -s learning_agent\tests`

- [ ] **Step 3: Run visible terminal/controller acceptance**

Run:
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath <absolute scenario path>`

- [ ] **Step 4: Run independent verifier**

Run:
`python -m learning_agent.acceptance.verifier <run_dir> <scenario_path>`

Expected: `completed=true`, `assertion.passed=true`, and `required_artifact_globs` all true.

### Self-Review

- Stage 9 blueprint coverage: tools, frame sequence, GIF export, action-linked frames, status visibility, and verifier artifact gate are all covered.
- Placeholder scan: no TBD/TODO/later placeholders remain.
- Type consistency: all public names use `BrowserRecordingStore`, `browser_record_start`, `browser_record_stop`, `browser_gif_export`, and `required_artifact_globs`.
