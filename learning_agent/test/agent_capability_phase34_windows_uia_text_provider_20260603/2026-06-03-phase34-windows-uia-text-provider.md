# Phase34 Windows UIAutomation Text Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional, read-only UIAutomationClient text-tree provider for Windows Computer Use observation.

**Architecture:** Keep Phase32/33 screenshot behavior unchanged. Add a UIA text provider that can use an injected or installed `uiautomation` module, walk a bounded control tree, and return the existing `NativeWindowTextResult`. Wrap it with a fallback provider so missing UIA dependencies or runtime failures automatically fall back to `Win32WindowTextProvider`.

**Tech Stack:** Python `unittest`, existing `learning_agent.computer_use.native_helper`, existing evidence store and acceptance controller.

---

### Task 1: Red Test

**Files:**
- Create: `learning_agent/tests/test_windows_computer_use_uia_provider_phase34.py`
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase34_windows_uia_text_provider.json`

- [ ] **Step 1: Write tests for wished-for API**

Tests expect:

- `WindowsUiautomationTextProvider` can walk a fake UIA control tree.
- Invalid hwnd and non-Windows platforms are safely refused.
- `FallbackNativeWindowTextProvider` falls back to Win32-style provider when UIA is unavailable.
- Default `WindowsNativeWindowObservationHelper` uses the UIA-first fallback provider.
- Evidence store still filters sensitive UIA text.

- [ ] **Step 2: Run red test**

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_uia_provider_phase34
```

Expected: failure because the new provider classes do not exist yet.

### Task 2: Implementation

**Files:**
- Modify: `learning_agent/computer_use/native_helper.py`
- Modify: `learning_agent/computer_use/__init__.py`

- [ ] **Step 1: Add `WindowsUiautomationTextProvider`**

Use optional `uiautomation` module, with injectable module for tests. Do not require the dependency for import-time success.

- [ ] **Step 2: Add bounded tree walking**

Limit depth and node count. Extract safe fields: name, role, automation id, class name.

- [ ] **Step 3: Add `FallbackNativeWindowTextProvider`**

Try UIA first. If not captured, use `Win32WindowTextProvider`.

- [ ] **Step 4: Make default helper use fallback**

Only when no explicit text provider is injected.

### Task 3: Verification

**Files:**
- Modify: `agent_memory/context.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`
- Create: `agent_memory/agent_capability_phase34_windows_uia_text_provider_20260603.md`
- Copy changed files to `learning_agent/test/agent_capability_phase34_windows_uia_text_provider_20260603/`

- [ ] **Step 1: Run focused test**

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_uia_provider_phase34
```

- [ ] **Step 2: Run neighboring Computer Use regression**

Run Phase27-34 tests together.

- [ ] **Step 3: Run full regression**

```powershell
python -m unittest discover -s learning_agent\tests
```

- [ ] **Step 4: Run visible terminal acceptance**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\agent_capability_phase34_windows_uia_text_provider.json
```

- [ ] **Step 5: Run independent verifier**

```powershell
python -m learning_agent.acceptance.verifier <run_dir> .\learning_agent\acceptance_controller\scenarios\agent_capability_phase34_windows_uia_text_provider.json
```
