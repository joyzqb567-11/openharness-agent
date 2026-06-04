# Phase97 Controlled Notepad Live Edit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a controlled visible Notepad workflow that proves the agent can use the existing Computer Use stack to edit and save a real local application file under explicit gates.

**Architecture:** Add one focused Phase97 runtime module that composes existing SendInput, safety, runtime-file, and acceptance-controller patterns. Keep real desktop input disabled by default and require both request and enable gates for the live path.

**Tech Stack:** Python `unittest`, Windows `notepad.exe`, existing `learning_agent.computer_use` modules, existing acceptance controller JSON scenarios, PowerShell visible-terminal harness.

---

### Task 1: Add Phase97 Failing Tests

**Files:**
- Create: `learning_agent/tests/test_windows_computer_use_controlled_notepad_live_edit_phase97.py`

- [ ] **Step 1: Write tests for safe default, explicit gated run, CLI tokens, and raw-text hiding**

Create `learning_agent/tests/test_windows_computer_use_controlled_notepad_live_edit_phase97.py` with imports for the planned Phase97 API. The initial expected failure is `ModuleNotFoundError` because the runtime does not exist yet.

```python
import json
import tempfile
import unittest
from pathlib import Path

from learning_agent.computer_use.controlled_notepad_live_edit import (
    PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MARKER,
    PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK_TOKEN,
    PHASE97_REAL_NOTEPAD_LIVE_EDIT_ENV,
    PHASE97_REAL_NOTEPAD_LIVE_EDIT_REQUEST_ENV,
    phase97_cli_line,
    run_phase97_controlled_notepad_live_edit_contract,
)


class FakePhase97NotepadDriver:
    def __init__(self) -> None:
        self.calls = []

    def run(self, *, run_root: Path, expected_text: str, target_file: Path) -> dict[str, object]:
        self.calls.append({"run_root": str(run_root), "target_file": str(target_file), "text_length": len(expected_text)})
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(expected_text, encoding="utf-8")
        return {
            "ok": True,
            "driver": "fake_phase97_notepad_driver",
            "notepad_process_verified": True,
            "target_rechecked_before_input": True,
            "target_rechecked_before_save": True,
            "saved_file_exists": True,
            "saved_file_sha256_16": "fakehashphase97",
            "real_desktop_touched": True,
            "raw_text_included": False,
        }


class Phase97ControlledNotepadLiveEditTests(unittest.TestCase):
    def test_default_contract_does_not_touch_desktop(self) -> None:
        driver = FakePhase97NotepadDriver()
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = run_phase97_controlled_notepad_live_edit_contract(
                base_dir=Path(temporary_directory),
                real_edit=False,
                allow_real_gate=False,
                notepad_driver=driver,
            )
        self.assertTrue(report["passed"])
        self.assertFalse(report["real_notepad_edit_executed"])
        self.assertFalse(report["real_desktop_touched"])
        self.assertEqual(driver.calls, [])
        self.assertTrue(report["default_off_zero_physical_events"])
        self.assertTrue(report["unsafe_target_zero_physical_events"])

    def test_explicit_gated_contract_edits_controlled_file(self) -> None:
        driver = FakePhase97NotepadDriver()
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = run_phase97_controlled_notepad_live_edit_contract(
                base_dir=Path(temporary_directory),
                real_edit=True,
                allow_real_gate=True,
                notepad_driver=driver,
            )
            target_file = Path(str(report["target_file"]))
            saved_text = target_file.read_text(encoding="utf-8")
        self.assertTrue(report["passed"])
        self.assertTrue(report["real_notepad_edit_executed"])
        self.assertTrue(report["real_desktop_touched"])
        self.assertTrue(report["notepad_process_verified"])
        self.assertTrue(report["target_rechecked_before_input"])
        self.assertTrue(report["target_rechecked_before_save"])
        self.assertIn("PHASE97 controlled Notepad live edit", saved_text)
        self.assertEqual(len(driver.calls), 1)

    def test_cli_line_contains_tokens_and_hides_raw_prompt_text(self) -> None:
        driver = FakePhase97NotepadDriver()
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = run_phase97_controlled_notepad_live_edit_contract(
                base_dir=Path(temporary_directory),
                real_edit=True,
                allow_real_gate=True,
                notepad_driver=driver,
            )
        line = phase97_cli_line(report)
        serialized = json.dumps(report, ensure_ascii=False, sort_keys=True, default=str)
        self.assertIn(PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_MARKER, line)
        self.assertIn(PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK_TOKEN, line)
        self.assertIn("real_notepad_edit_executed=true", line)
        self.assertIn("saved_file_verified=true", line)
        self.assertIn(PHASE97_REAL_NOTEPAD_LIVE_EDIT_ENV, serialized)
        self.assertIn(PHASE97_REAL_NOTEPAD_LIVE_EDIT_REQUEST_ENV, serialized)
        self.assertNotIn("user secret prompt", serialized.lower())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify red**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_controlled_notepad_live_edit_phase97
```

Expected: FAIL with `ModuleNotFoundError: No module named 'learning_agent.computer_use.controlled_notepad_live_edit'`.

### Task 2: Implement Phase97 Contract Runtime

**Files:**
- Create: `learning_agent/computer_use/controlled_notepad_live_edit.py`
- Modify: `learning_agent/computer_use/__init__.py`

- [ ] **Step 1: Add the runtime module with AGENTS.md Chinese line comments**

Implement the public constants, gate helpers, expected text builder, default-off checks, injected-driver path, real driver placeholder, report writer, CLI line, and `main()`.

Every new code line must include the required Chinese comment prefix such as `新增代码+Phase97ControlledNotepadLiveEdit：...`.

- [ ] **Step 2: Export Phase97 API**

Add Phase97 exports to `learning_agent/computer_use/__init__.py` without removing existing exports.

- [ ] **Step 3: Run focused tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_controlled_notepad_live_edit_phase97
```

Expected: 3 tests OK.

### Task 3: Add Real Notepad Driver

**Files:**
- Modify: `learning_agent/computer_use/controlled_notepad_live_edit.py`
- Test: `learning_agent/tests/test_windows_computer_use_controlled_notepad_live_edit_phase97.py`

- [ ] **Step 1: Add driver tests with injected safe subprocess/input shims**

Extend the focused test file with a fake launcher, fake focus checker, fake sender, and fake save verifier. The tests must prove the driver refuses non-Notepad targets and rechecks target identity before input and save.

- [ ] **Step 2: Implement `Phase97WindowsNotepadLiveEditDriver`**

The driver should launch Notepad with a controlled target file, recheck the target, use the controlled SendInput sender for fixed text and save shortcut, verify the file, and return a sanitized report.

- [ ] **Step 3: Run focused tests again**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_controlled_notepad_live_edit_phase97
```

Expected: all Phase97 tests OK.

### Task 4: Add Acceptance Scenario

**Files:**
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_phase97_controlled_notepad_live_edit.json`

- [ ] **Step 1: Create scenario JSON**

The scenario must instruct the visible terminal agent to run:

```powershell
$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE97_RUN_REAL_NOTEPAD_EDIT='1'; $env:LEARNING_AGENT_PHASE97_ENABLE_REAL_NOTEPAD_EDIT='1'; python -c "from learning_agent.computer_use.controlled_notepad_live_edit import main; raise SystemExit(main())"
```

Expected final token line:

```text
PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_READY PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK default_off_zero_physical_events=true unsafe_target_zero_physical_events=true real_enable_gate_required=true real_notepad_edit_executed=true notepad_process_verified=true target_rechecked_before_input=true target_rechecked_before_save=true saved_file_verified=true raw_text_hidden=true real_desktop_touched=true uncontrolled_actions_expanded=false
```

- [ ] **Step 2: Validate scenario JSON**

Run:

```powershell
python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_phase97_controlled_notepad_live_edit.json
```

Expected: pretty-printed JSON and exit code 0.

### Task 5: Update Memory And Learning Backup

**Files:**
- Create: `agent_memory/agent_capability_phase97_controlled_notepad_live_edit_20260604.md`
- Modify: `agent_memory/context.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`
- Create: `learning_agent/test/agent_capability_phase97_controlled_notepad_live_edit_20260604/`

- [ ] **Step 1: Write memory record**

Record scope, files, verification commands, acceptance result path, and boundaries.

- [ ] **Step 2: Append context/progress/bugs**

Keep entries concise and include the remaining risk that Notepad behavior varies by Windows version.

- [ ] **Step 3: Copy changed code/test/scenario snippets to learning backup**

Copy the changed Phase97 code, test, scenario, and memory record into the Phase97 backup folder.

### Task 6: Run Automated Verification

**Files:**
- No file edits.

- [ ] **Step 1: Run focused test**

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_controlled_notepad_live_edit_phase97
```

Expected: OK.

- [ ] **Step 2: Run adjacent regression**

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_controlled_physical_sendinput_phase95 learning_agent.tests.test_windows_computer_use_controlled_notepad_live_edit_phase97
```

Expected: OK.

- [ ] **Step 3: Run compile check**

```powershell
python -m compileall -q learning_agent\computer_use learning_agent\tests learning_agent\acceptance_controller
```

Expected: exit code 0.

### Task 7: Run Rule 17 Visible Terminal Acceptance

**Files:**
- No code edits unless evidence reveals a real bug.

- [ ] **Step 1: Launch visible terminal acceptance**

Run the existing controller against:

```text
learning_agent/acceptance_controller/scenarios/agent_capability_phase97_controlled_notepad_live_edit.json
```

This must start `learning_agent/start_oauth_agent.bat` in a real visible terminal window.

- [ ] **Step 2: Verify result JSON**

Expected fields:

```json
{
  "completed": true,
  "prompt_sent": true,
  "prompt_received": true,
  "final_printed": true
}
```

The assertion must pass and the final answer must include the full Phase97 token line.

- [ ] **Step 3: Record final acceptance**

Update `agent_memory/agent_capability_phase97_controlled_notepad_live_edit_20260604.md` and `agent_memory/progress.md` with the visible-terminal result path.

### Self-Review

Spec coverage: The plan covers runtime, tests, safety gates, scenario, memory, backup, automated verification, and Rule 17 visible terminal acceptance.

Placeholder scan: The plan contains no unresolved placeholder markers. The only flexible part is the real driver implementation detail, bounded by explicit tests and required fields.

Type consistency: Public names use `phase97`, `controlled_notepad_live_edit`, and stable marker/token names consistently across spec, plan, tests, runtime, and scenario.
