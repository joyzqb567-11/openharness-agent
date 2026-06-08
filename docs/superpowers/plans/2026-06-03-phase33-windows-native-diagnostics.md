# Phase33 Windows Native Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe, read-only diagnostics layer for Windows native Computer Use observation so the agent can explain whether Graphics Capture, UI Automation, GDI fallback, and Win32 text fallback are available.

**Architecture:** Keep Phase32 observation behavior intact. Add a small diagnostics module that reports provider priority, active fallback, opt-in boundary, permission guidance, and whether real input actions were expanded. Surface that diagnostics object through `WindowsNativeWindowObservationHelper.status()` and `WindowsComputerUseBackend.status()`.

**Tech Stack:** Python `unittest`, existing `learning_agent.computer_use` modules, existing acceptance controller/verifier.

---

### Task 1: Red Test For Native Diagnostics

**Files:**
- Create: `learning_agent/tests/test_windows_computer_use_native_diagnostics_phase33.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase33_windows_native_diagnostics.json`

- [ ] **Step 1: Write the failing test**

Add tests that expect:

- `WindowsNativeWindowObservationHelper.status()["diagnostics"]` exists.
- Diagnostics contains `phase33_windows_native_diagnostics`.
- Diagnostics lists `windows_graphics_capture` and `uiautomation_client` as known preferred providers.
- Diagnostics reports active fallback providers from injected fake providers.
- Diagnostics states `safe_observe_only=true` and `real_input_actions_expanded=false`.
- `WindowsComputerUseBackend.status()` exposes the same diagnostics object.

- [ ] **Step 2: Run the test and verify red**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_native_diagnostics_phase33
```

Expected:

```text
FAIL or ERROR because Phase33 diagnostics are not implemented yet.
```

### Task 2: Implement Diagnostics Module

**Files:**
- Create: `learning_agent/computer_use/native_diagnostics.py`
- Modify: `learning_agent/computer_use/native_helper.py`
- Modify: `learning_agent/computer_use/controller.py`
- Modify: `learning_agent/computer_use/__init__.py`

- [ ] **Step 1: Add diagnostics data model**

Create a small module that builds dictionaries instead of changing existing payload contracts.

- [ ] **Step 2: Wire helper status**

`WindowsNativeWindowObservationHelper.status()` should add a `diagnostics` field without changing `observe_window()`.

- [ ] **Step 3: Wire backend status**

`WindowsComputerUseBackend.status()` should add `native_observation_diagnostics`.

- [ ] **Step 4: Export public diagnostics helpers**

Expose the new diagnostics builder from `learning_agent.computer_use`.

### Task 3: Verification And Acceptance

**Files:**
- Modify: `agent_memory/context.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`
- Create: `agent_memory/agent_capability_phase33_windows_native_diagnostics_20260603.md`
- Copy changed files to `learning_agent/test/agent_capability_phase33_windows_native_diagnostics_20260603/`

- [ ] **Step 1: Green unit test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_native_diagnostics_phase33
```

- [ ] **Step 2: Neighbor regression**

Run Phase27-33 Computer Use tests together.

- [ ] **Step 3: Full regression**

Run:

```powershell
python -m unittest discover -s learning_agent\tests
```

- [ ] **Step 4: Real visible terminal acceptance**

Run acceptance controller with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\agent_capability_phase33_windows_native_diagnostics.json
```

- [ ] **Step 5: Independent verifier**

Run:

```powershell
python -m learning_agent.acceptance.verifier <run_dir> .\learning_agent\acceptance_controller\scenarios\agent_capability_phase33_windows_native_diagnostics.json
```
