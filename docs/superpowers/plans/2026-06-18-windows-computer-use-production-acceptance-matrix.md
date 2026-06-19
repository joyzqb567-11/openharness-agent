# Windows Computer Use Production Acceptance Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable Windows Computer Use production acceptance matrix that uses the OpenHarness acceptance controller to drive real visible terminal prompts, real agent execution, and controlled Windows desktop evidence across the main Computer Use workflows.

**Architecture:** Keep each acceptance scenario as a small, controlled, visible-terminal contract. Add one matrix manifest and one PowerShell runner that execute the existing controller scenario-by-scenario, collect `result.json`, screenshots, readable logs, and token evidence, then write a single matrix report that can be used before any future Computer Use release claim.

**Tech Stack:** OpenHarness Python runtime, PowerShell acceptance controller, `learning_agent/start_oauth_agent.bat`, Windows controlled app smoke modules, JSON scenario files, `unittest`, CodeGraph, visible terminal screenshots.

---

## 1. Why This Blueprint Exists

The current project has proven one important fact: `learning_agent/acceptance_controller/controller.ps1` can open a real visible Windows terminal, input a real prompt into the agent, let the agent call the local terminal tool, and verify controlled desktop evidence. The latest proof is:

- Scenario: `learning_agent/acceptance_controller/scenarios/agent_capability_cua_driver_real_windows_production_visible_terminal.json`
- Latest passing run: `learning_agent/acceptance_controller/runs/agent_capability_cua_driver_real_windows_production_visible_terminal-20260618_173128/result.json`
- Key passing facts: `completed=true`, `assertion.passed=true`, `marker_passed=true`, `permission_sent_count=0`, `real_notepad_edit_executed=true`, `saved_file_verified=true`, `real_desktop_touched=true`

The next maturity step is not another isolated feature. The next maturity step is a stable production acceptance matrix, so future Computer Use changes can be judged by repeatable Windows evidence instead of memory or optimism.

## 2. Non-Negotiable Boundaries

- Do not open login pages, payment pages, password managers, private documents, registry tools, installers, system settings, or administrator prompts.
- Do not add any scenario that needs UAC approval, registry edits, Windows service install, global hooks, or security policy changes.
- Do not bypass `learning_agent/start_oauth_agent.bat`; production acceptance must use the same visible terminal path the user cares about.
- Do not replace unit tests with visible terminal tests. The matrix is an additional production gate.
- Do not claim all Windows apps are covered. The first matrix covers controlled representative app families.
- Do not leave stale scenario tokens such as `real_gui_backing=true` unless the exact CLI command actually prints that token in the current source.

## 3. Source Evidence Baseline

### 3.1 Controller Capabilities Confirmed

`learning_agent/acceptance_controller/controller.ps1` currently supports:

- `visible_terminal_gate`
- `screenshot_artifacts_required`
- `required_event_states`
- `debug_log_contains`
- `event_answer_contains`
- `event_payload_contains`
- `event_payload_regex`
- `permission_policy.default_response`
- `permission_policy.allow_contains`
- `permission_policy.deny_contains`
- `permission_policy.allow_tool_names`
- `permission_policy.deny_tool_names`
- `permission_policy.allow_url_prefixes`
- `max_permission_sent_count`
- `ACCEPTANCE_CONTROLLER_COMPLETED=<true|false>`
- `RESULT_JSON=<path>`

This means the matrix can use the existing controller without inventing a second terminal automation layer.

### 3.2 Existing Controlled Scenario Families

The current repository already has these visible terminal scenario files:

- `learning_agent/acceptance_controller/scenarios/agent_capability_cua_driver_real_windows_production_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_permission_ui_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_single_app_text_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_single_app_calculation_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_local_file_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_local_browser_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_multi_app_transfer_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_failure_recovery_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_long_task_resume_visible_terminal.json`

The current source also has controlled runtime modules under:

- `learning_agent/computer_use_mcp_v2/windows_runtime/controlled_notepad_live_edit.py`
- `learning_agent/computer_use_mcp_v2/windows_runtime/controlled_calculator_live_sum.py`
- `learning_agent/computer_use_mcp_v2/windows_runtime/controlled_explorer_live_file_roundtrip.py`
- `learning_agent/computer_use_mcp_v2/windows_runtime/controlled_browser_live_local_page.py`
- `learning_agent/computer_use_mcp_v2/windows_runtime/controlled_multi_app_transfer.py`
- `learning_agent/computer_use_mcp_v2/windows_runtime/controlled_failure_recovery.py`
- `learning_agent/computer_use_mcp_v2/windows_runtime/controlled_long_task_resume.py`

## 4. Main Decision

Create a production acceptance matrix around existing controlled Windows contracts first. Do not start by adding new desktop automation logic.

The matrix should answer five questions:

1. Can the acceptance controller still drive the real visible terminal?
2. Can the real agent receive a user-like prompt and call the local terminal tool?
3. Can controlled Windows app actions produce durable evidence?
4. Can permission UI and denial paths be verified without touching unsafe targets?
5. Can one command produce a readable pass/fail report with evidence paths?

## 5. In Scope

- Audit existing scenario tokens against the exact CLI output of their controlled runtime modules.
- Fix stale scenario assertions that require tokens not printed by the current command.
- Add a matrix manifest that lists each scenario, family, risk level, expected tokens, and evidence requirements.
- Add a PowerShell runner that executes `controller.ps1` sequentially for the matrix.
- Add a production matrix report in JSON and Markdown.
- Add one safe permission denial scenario using controller permission policy.
- Add tests that validate scenario JSON shape, manifest coverage, and matrix report parsing.
- Add learning backup under `learning_agent/test/`.
- Update `agent_memory/context.md`, `agent_memory/progress.md`, and `agent_memory/bugs.md`.

## 6. Out Of Scope

- Adding new Computer Use runtime capabilities.
- Replacing the existing acceptance controller.
- Creating a nested controller scenario that starts another controller from inside an already running visible terminal.
- Running against arbitrary user applications.
- Running against administrator windows.
- Changing OAuth model behavior.
- Changing ClaudeCode-compatible Computer Use tool schema.

## 7. Success Criteria

- One command can run the matrix:

```powershell
powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\run_windows_computer_use_acceptance.ps1
```

- The command writes:

```text
learning_agent/acceptance_controller/runs/windows_computer_use_production_matrix-<timestamp>/matrix_result.json
learning_agent/acceptance_controller/runs/windows_computer_use_production_matrix-<timestamp>/matrix_result.md
```

- Every included scenario result has:

```json
{
  "completed": true,
  "assertion": {
    "passed": true,
    "marker_passed": true
  }
}
```

- Every scenario has startup, prompt, and final screenshots when `screenshot_artifacts_required=true`.
- The final matrix report lists scenario id, family, pass/fail, run directory, result path, final screenshot, and failure reason.
- Permission denial scenario proves a denial can be handled and audited without executing desktop actions.
- `python -m unittest learning_agent.tests.test_windows_computer_use_acceptance_matrix_manifest -v` passes.
- JSON parsing checks pass for every new or modified scenario and manifest file.
- The real visible terminal matrix run passes before anyone claims production acceptance is complete.

## 8. Stop Conditions

Stop and report before further implementation if any of these happen:

- A scenario needs a private user file, browser login, password field, payment page, registry, system settings, installer, or admin prompt.
- A scenario can pass only by removing a safety check.
- A controlled CLI command does not print the token that its visible-terminal scenario requires.
- The acceptance controller cannot focus or type into the visible terminal.
- A test or scenario requires `LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS=1`.
- A failure leaves Notepad, Calculator, browser, Explorer, or temporary project files uncontrolled outside the scenario evidence folder.

## 9. File Map

### Create

- `learning_agent/acceptance_controller/windows_computer_use_production_matrix.json`  
  Matrix manifest. Lists scenario files, families, required tokens, and risk notes.

- `learning_agent/acceptance_controller/run_windows_computer_use_acceptance.ps1`  
  Sequential runner. Calls `controller.ps1` for each manifest entry and writes aggregate JSON/Markdown reports.

- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_permission_denial_visible_terminal.json`  
  Safe denial scenario. Confirms permission denial path is visible and audited.

- `learning_agent/tests/test_windows_computer_use_acceptance_matrix_manifest.py`  
  Unit tests for manifest and scenario consistency.

- `docs/computer_use_windows_production_acceptance.md`  
  User-readable instructions for running the matrix and interpreting results.

- `learning_agent/test/windows_computer_use_production_acceptance_matrix_20260618/`  
  Learning backup folder containing modified scenarios, new runner, manifest, docs, memory snapshots, and the final matrix run result.

### Modify

- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_single_app_text_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_single_app_calculation_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_local_file_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_local_browser_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_multi_app_transfer_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_failure_recovery_visible_terminal.json`
- `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_long_task_resume_visible_terminal.json`
- `agent_memory/context.md`
- `agent_memory/progress.md`
- `agent_memory/bugs.md`

Only modify Phase148C scenario token lists after direct CLI audit proves the token list is stale.

## 10. Matrix Families

| Family | Scenario | Purpose | Minimum Required Evidence |
|---|---|---|---|
| cua_driver_notepad_production | `agent_capability_cua_driver_real_windows_production_visible_terminal.json` | Cua-inspired runtime plus real Notepad save evidence | `CUA_DRIVER_WINDOWS_PRODUCTION_ACCEPTANCE_OK`, `saved_file_verified=true`, `real_desktop_touched=true` |
| permission_allow | `agent_capability_computer_use_permission_ui_visible_terminal.json` | Visible permission UI and status evidence | `COMPUTER_USE_PERMISSION_UI_VISIBLE_TERMINAL_OK`, `permission_prompt_version=windows-permission-ui-v1` |
| permission_deny | `agent_capability_computer_use_permission_denial_visible_terminal.json` | Safe denial path and audit evidence | `COMPUTER_USE_PERMISSION_DENIAL_VISIBLE_TERMINAL_OK`, `permission_answered`, `response=n` |
| single_app_text | `agent_capability_computer_use_phase148c_single_app_text_visible_terminal.json` | Notepad text entry and file save | `PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK`, `saved_file_verified=true` |
| single_app_calculation | `agent_capability_computer_use_phase148c_single_app_calculation_visible_terminal.json` | Calculator click/key path and observed result | `PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_OK`, `observed_result_matches_expected=true` |
| local_file | `agent_capability_computer_use_phase148c_local_file_visible_terminal.json` | Explorer controlled file/folder roundtrip | `PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_OK`, `filesystem_changed_after_real_actions=true` |
| local_browser | `agent_capability_computer_use_phase148c_local_browser_visible_terminal.json` | Local browser page click/input path | `PHASE139_CONTROLLED_BROWSER_LIVE_LOCAL_PAGE_OK`, `page_changed_after_real_click=true` |
| multi_app_transfer | `agent_capability_computer_use_phase148c_multi_app_transfer_visible_terminal.json` | Cross-app transfer through controlled targets | `PHASE150_CONTROLLED_MULTI_APP_TRANSFER_OK`, `source_and_target_apps_distinct=true` |
| failure_recovery | `agent_capability_computer_use_phase148c_failure_recovery_visible_terminal.json` | Recover after controlled failure | `PHASE150_CONTROLLED_FAILURE_RECOVERY_OK`, `recovery_plan_executed=true` |
| long_task_resume | `agent_capability_computer_use_phase148c_long_task_resume_visible_terminal.json` | Resume state and avoid repeating step 1 | `PHASE150_CONTROLLED_LONG_TASK_RESUME_OK`, `long_task_completed_after_resume=true` |

## 11. Implementation Tasks

### Task 1: CodeGraph And Scenario Output Audit

**Files:**

- Read: `learning_agent/acceptance_controller/controller.ps1`
- Read: `learning_agent/acceptance_controller/scenarios/*.json`
- Read: `learning_agent/computer_use_mcp_v2/windows_runtime/controlled_*.py`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`

- [ ] **Step 1: Confirm CodeGraph state**

Run:

```powershell
codegraph status .
```

Expected:

```text
[OK] Index is up to date
```

- [ ] **Step 2: Explore controlled runtime modules**

Run with CodeGraph MCP or shell fallback:

```powershell
codegraph explore "controlled_notepad_live_edit controlled_calculator_live_sum controlled_explorer_live_file_roundtrip controlled_browser_live_local_page controlled_multi_app_transfer controlled_failure_recovery controlled_long_task_resume"
```

Expected: current source paths and marker constants are visible.

- [ ] **Step 3: Directly audit each controlled CLI output**

Run each command from the repository root `H:\codexworkplace\sofeware\OpenHarness-main`:

```powershell
$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE97_RUN_REAL_NOTEPAD_EDIT='1'; $env:LEARNING_AGENT_PHASE97_ENABLE_REAL_NOTEPAD_EDIT='1'; python -c "from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_notepad_live_edit import main; raise SystemExit(main())"
```

```powershell
$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE137_RUN_REAL_CALCULATOR_SUM='1'; $env:LEARNING_AGENT_PHASE137_ENABLE_REAL_CALCULATOR_SUM='1'; python -c "from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_calculator_live_sum import main; raise SystemExit(main())"
```

```powershell
$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE149_RUN_REAL_EXPLORER_FILE_ROUNDTRIP='1'; $env:LEARNING_AGENT_PHASE149_ENABLE_REAL_EXPLORER_FILE_ROUNDTRIP='1'; python -c "from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_explorer_live_file_roundtrip import main; raise SystemExit(main())"
```

```powershell
$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE139_RUN_REAL_BROWSER_LOCAL_PAGE='1'; $env:LEARNING_AGENT_PHASE139_ENABLE_REAL_BROWSER_LOCAL_PAGE='1'; python -c "from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_browser_live_local_page import main; raise SystemExit(main())"
```

```powershell
$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE150_RUN_REAL_MULTI_APP_TRANSFER='1'; $env:LEARNING_AGENT_PHASE150_ENABLE_REAL_MULTI_APP_TRANSFER='1'; python -c "from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_multi_app_transfer import main; raise SystemExit(main())"
```

```powershell
$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE150_RUN_REAL_FAILURE_RECOVERY='1'; $env:LEARNING_AGENT_PHASE150_ENABLE_REAL_FAILURE_RECOVERY='1'; python -c "from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_failure_recovery import main; raise SystemExit(main())"
```

```powershell
$env:PYTHONPATH='..'; $env:LEARNING_AGENT_PHASE150_RUN_REAL_LONG_TASK_RESUME='1'; $env:LEARNING_AGENT_PHASE150_ENABLE_REAL_LONG_TASK_RESUME='1'; python -c "from learning_agent.computer_use_mcp_v2.windows_runtime.controlled_long_task_resume import main; raise SystemExit(main())"
```

Expected: each command exits `0` before its scenario is allowed into the matrix.

- [ ] **Step 4: Record stale-token findings**

If a scenario expects a token that the CLI does not print, write the exact mismatch into `agent_memory/bugs.md`.

Example record:

```markdown
## 2026-06-18 Windows Computer Use production matrix token audit
- Scenario: agent_capability_computer_use_phase148c_single_app_text_visible_terminal
- CLI: controlled_notepad_live_edit
- Stale token: real_gui_backing=true
- Actual proof tokens: PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK, saved_file_verified=true, real_desktop_touched=true
- Decision: update scenario token list to actual CLI output before matrix inclusion.
```

### Task 2: Repair Scenario Token Lists

**Files:**

- Modify: the seven Phase148C scenario JSON files listed in section 9
- Test: `learning_agent/tests/test_windows_computer_use_acceptance_matrix_manifest.py`

- [ ] **Step 1: Write the JSON validation test**

Create `learning_agent/tests/test_windows_computer_use_acceptance_matrix_manifest.py` with this first test:

```python
from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = REPO_ROOT / "learning_agent" / "acceptance_controller" / "scenarios"


class WindowsComputerUseAcceptanceMatrixManifestTests(unittest.TestCase):
    def test_phase148c_scenarios_are_valid_json(self) -> None:
        scenario_names = [
            "agent_capability_computer_use_phase148c_single_app_text_visible_terminal.json",
            "agent_capability_computer_use_phase148c_single_app_calculation_visible_terminal.json",
            "agent_capability_computer_use_phase148c_local_file_visible_terminal.json",
            "agent_capability_computer_use_phase148c_local_browser_visible_terminal.json",
            "agent_capability_computer_use_phase148c_multi_app_transfer_visible_terminal.json",
            "agent_capability_computer_use_phase148c_failure_recovery_visible_terminal.json",
            "agent_capability_computer_use_phase148c_long_task_resume_visible_terminal.json",
        ]
        for scenario_name in scenario_names:
            with self.subTest(scenario_name=scenario_name):
                data = json.loads((SCENARIOS_DIR / scenario_name).read_text(encoding="utf-8-sig"))
                self.assertTrue(data["visible_terminal_gate"])
                self.assertTrue(data["screenshot_artifacts_required"])
                self.assertIn("agent_ready_for_user_prompt", data["required_event_states"])
                self.assertIn("user_prompt_received", data["required_event_states"])
                self.assertIn("final_answer_printed", data["required_event_states"])
```

Project rule for implementation: add the required Chinese line comments to every new or modified code line when actually creating this file.

- [ ] **Step 2: Run the test and confirm the baseline**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_acceptance_matrix_manifest -v
```

Expected: pass after the test file is valid. If import fails because of unrelated historical test support, record the blocker in `agent_memory/bugs.md`.

- [ ] **Step 3: Remove or replace stale tokens only after CLI proof**

For each scenario, replace any stale `debug_log_contains` or `event_answer_contains` token with the actual token printed by the CLI. For example, if `controlled_notepad_live_edit` does not print `real_gui_backing=true`, remove that token and keep:

```json
[
  "PHASE148C_FRESH_BENCHMARK_READY",
  "PHASE148C_FRESH_BENCHMARK_OK",
  "family=single_app_text",
  "PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK",
  "saved_file_verified=true",
  "real_desktop_touched=true"
]
```

- [ ] **Step 4: Validate all modified JSON**

Run:

```powershell
@'
import json
from pathlib import Path
root = Path(r"H:\codexworkplace\sofeware\OpenHarness-main")
for path in (root / "learning_agent" / "acceptance_controller" / "scenarios").glob("agent_capability_computer_use_phase148c_*_visible_terminal.json"):
    json.loads(path.read_text(encoding="utf-8-sig"))
    print(f"json_ok {path.name}")
'@ | python -
```

Expected: every modified scenario prints `json_ok <name>`.

### Task 3: Add The Matrix Manifest

**Files:**

- Create: `learning_agent/acceptance_controller/windows_computer_use_production_matrix.json`
- Modify: `learning_agent/tests/test_windows_computer_use_acceptance_matrix_manifest.py`

- [ ] **Step 1: Create manifest JSON**

Create `learning_agent/acceptance_controller/windows_computer_use_production_matrix.json`:

```json
{
  "matrix_id": "windows_computer_use_production_matrix_v1",
  "visible_terminal_required": true,
  "runner": "learning_agent/acceptance_controller/run_windows_computer_use_acceptance.ps1",
  "scenarios": [
    {
      "id": "cua_driver_notepad_production",
      "family": "cua_driver_notepad_production",
      "scenario_path": "scenarios/agent_capability_cua_driver_real_windows_production_visible_terminal.json",
      "required_tokens": [
        "CUA_DRIVER_WINDOWS_PRODUCTION_ACCEPTANCE_OK",
        "CUA_DRIVER_WINDOWS_BORROWING_OK",
        "PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK",
        "saved_file_verified=true",
        "real_desktop_touched=true"
      ],
      "risk_note": "Controlled Notepad target and project evidence files only."
    },
    {
      "id": "permission_allow",
      "family": "permission_allow",
      "scenario_path": "scenarios/agent_capability_computer_use_permission_ui_visible_terminal.json",
      "required_tokens": [
        "COMPUTER_USE_PERMISSION_UI_VISIBLE_TERMINAL_OK",
        "permission_prompt_version=windows-permission-ui-v1"
      ],
      "risk_note": "Permission prompt only; no desktop action."
    },
    {
      "id": "single_app_text",
      "family": "single_app_text",
      "scenario_path": "scenarios/agent_capability_computer_use_phase148c_single_app_text_visible_terminal.json",
      "required_tokens": [
        "PHASE97_CONTROLLED_NOTEPAD_LIVE_EDIT_OK",
        "saved_file_verified=true",
        "real_desktop_touched=true"
      ],
      "risk_note": "Controlled Notepad save roundtrip."
    },
    {
      "id": "single_app_calculation",
      "family": "single_app_calculation",
      "scenario_path": "scenarios/agent_capability_computer_use_phase148c_single_app_calculation_visible_terminal.json",
      "required_tokens": [
        "PHASE137_CONTROLLED_CALCULATOR_LIVE_SUM_OK",
        "observed_result_matches_expected=true",
        "real_desktop_touched=true"
      ],
      "risk_note": "Controlled Calculator arithmetic only."
    },
    {
      "id": "local_file",
      "family": "local_file",
      "scenario_path": "scenarios/agent_capability_computer_use_phase148c_local_file_visible_terminal.json",
      "required_tokens": [
        "PHASE149_CONTROLLED_EXPLORER_LIVE_FILE_ROUNDTRIP_OK",
        "controlled_folder_created=true",
        "filesystem_changed_after_real_actions=true",
        "real_desktop_touched=true"
      ],
      "risk_note": "Controlled Explorer folder inside project evidence root only."
    },
    {
      "id": "local_browser",
      "family": "local_browser",
      "scenario_path": "scenarios/agent_capability_computer_use_phase148c_local_browser_visible_terminal.json",
      "required_tokens": [
        "PHASE139_CONTROLLED_BROWSER_LIVE_LOCAL_PAGE_OK",
        "page_changed_after_real_click=true",
        "real_desktop_touched=true"
      ],
      "risk_note": "Controlled local page only."
    },
    {
      "id": "multi_app_transfer",
      "family": "multi_app_transfer",
      "scenario_path": "scenarios/agent_capability_computer_use_phase148c_multi_app_transfer_visible_terminal.json",
      "required_tokens": [
        "PHASE150_CONTROLLED_MULTI_APP_TRANSFER_OK",
        "transfer_text_copied_from_source=true",
        "transferred_text_observed_in_target=true",
        "source_and_target_apps_distinct=true",
        "real_desktop_touched=true"
      ],
      "risk_note": "Controlled Notepad and controlled local browser targets only."
    },
    {
      "id": "failure_recovery",
      "family": "failure_recovery",
      "scenario_path": "scenarios/agent_capability_computer_use_phase148c_failure_recovery_visible_terminal.json",
      "required_tokens": [
        "PHASE150_CONTROLLED_FAILURE_RECOVERY_OK",
        "controlled_failure_injected=true",
        "recovery_plan_executed=true",
        "target_reacquired_after_failure=true",
        "real_desktop_touched=true"
      ],
      "risk_note": "Controlled local recovery target only."
    },
    {
      "id": "long_task_resume",
      "family": "long_task_resume",
      "scenario_path": "scenarios/agent_capability_computer_use_phase148c_long_task_resume_visible_terminal.json",
      "required_tokens": [
        "PHASE150_CONTROLLED_LONG_TASK_RESUME_OK",
        "checkpoint_written_before_interruption=true",
        "resume_state_loaded=true",
        "long_task_completed_after_resume=true",
        "real_desktop_touched=true"
      ],
      "risk_note": "Controlled local resume target only."
    }
  ]
}
```

- [ ] **Step 2: Extend the manifest test**

Add this test to `learning_agent/tests/test_windows_computer_use_acceptance_matrix_manifest.py`:

```python
def test_matrix_manifest_points_to_existing_visible_terminal_scenarios(self) -> None:
    manifest_path = REPO_ROOT / "learning_agent" / "acceptance_controller" / "windows_computer_use_production_matrix.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    self.assertEqual(manifest["matrix_id"], "windows_computer_use_production_matrix_v1")
    self.assertTrue(manifest["visible_terminal_required"])
    scenarios = manifest["scenarios"]
    self.assertGreaterEqual(len(scenarios), 9)
    seen_ids: set[str] = set()
    for scenario in scenarios:
        with self.subTest(scenario=scenario["id"]):
            self.assertNotIn(scenario["id"], seen_ids)
            seen_ids.add(scenario["id"])
            scenario_path = REPO_ROOT / "learning_agent" / "acceptance_controller" / scenario["scenario_path"]
            self.assertTrue(scenario_path.exists(), str(scenario_path))
            scenario_data = json.loads(scenario_path.read_text(encoding="utf-8-sig"))
            self.assertTrue(scenario_data["visible_terminal_gate"])
            self.assertTrue(scenario_data["screenshot_artifacts_required"])
            for token in scenario["required_tokens"]:
                self.assertIn(token, scenario_data.get("debug_log_contains", []) + scenario_data.get("event_answer_contains", []))
```

Project rule for implementation: add Chinese line comments to every new or modified Python line.

- [ ] **Step 3: Run manifest tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_acceptance_matrix_manifest -v
```

Expected: pass.

### Task 4: Add The Matrix Runner

**Files:**

- Create: `learning_agent/acceptance_controller/run_windows_computer_use_acceptance.ps1`
- Modify: `learning_agent/tests/test_windows_computer_use_acceptance_matrix_manifest.py`

- [ ] **Step 1: Create the runner**

Create `learning_agent/acceptance_controller/run_windows_computer_use_acceptance.ps1` with these responsibilities:

```powershell
param(
    [string]$ManifestPath = "learning_agent\acceptance_controller\windows_computer_use_production_matrix.json",
    [string]$RunRoot = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ManifestFullPath = if ([System.IO.Path]::IsPathRooted($ManifestPath)) { $ManifestPath } else { Join-Path $RepoRoot $ManifestPath }
$Manifest = Get-Content -LiteralPath $ManifestFullPath -Raw | ConvertFrom-Json
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$MatrixRunDir = if ([string]::IsNullOrWhiteSpace($RunRoot)) { Join-Path $RepoRoot "learning_agent\acceptance_controller\runs\windows_computer_use_production_matrix-$Timestamp" } else { $RunRoot }
New-Item -ItemType Directory -Force -Path $MatrixRunDir | Out-Null
$Rows = @()

foreach ($Scenario in @($Manifest.scenarios)) {
    $ScenarioPath = [string]$Scenario.scenario_path
    $CommandOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "learning_agent\acceptance_controller\controller.ps1") -ScenarioPath $ScenarioPath 2>&1
    $ResultLine = @($CommandOutput | Where-Object { [string]$_ -like "RESULT_JSON=*" }) | Select-Object -Last 1
    $ResultJson = if ($ResultLine) { ([string]$ResultLine).Substring("RESULT_JSON=".Length) } else { "" }
    $Result = if ($ResultJson -and (Test-Path -LiteralPath $ResultJson)) { Get-Content -LiteralPath $ResultJson -Raw | ConvertFrom-Json } else { $null }
    $Assertion = if ($Result -and $Result.assertion) { $Result.assertion } else { $null }
    $Passed = [bool]($Result -and $Result.completed -and $Assertion -and $Assertion.passed)
    $Rows += [ordered]@{
        id = [string]$Scenario.id
        family = [string]$Scenario.family
        passed = $Passed
        result_json = $ResultJson
        run_dir = if ($Result) { [string]$Result.run_dir } else { "" }
        final_screenshot = if ($Result) { [string]$Result.final_screenshot } else { "" }
        command_output = @($CommandOutput)
    }
}

$AllPassed = -not (@($Rows | Where-Object { -not $_.passed }).Count)
$MatrixResult = [ordered]@{
    matrix_id = [string]$Manifest.matrix_id
    completed = $AllPassed
    scenario_count = @($Rows).Count
    passed_count = @($Rows | Where-Object { $_.passed }).Count
    failed_count = @($Rows | Where-Object { -not $_.passed }).Count
    rows = $Rows
}
$MatrixResultPath = Join-Path $MatrixRunDir "matrix_result.json"
$MatrixMarkdownPath = Join-Path $MatrixRunDir "matrix_result.md"
$MatrixResult | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $MatrixResultPath -Encoding UTF8
@(
    "# Windows Computer Use Production Matrix Result",
    "",
    "- matrix_id=$($MatrixResult.matrix_id)",
    "- completed=$($MatrixResult.completed)",
    "- scenario_count=$($MatrixResult.scenario_count)",
    "- passed_count=$($MatrixResult.passed_count)",
    "- failed_count=$($MatrixResult.failed_count)",
    "",
    "| Scenario | Family | Passed | Result |",
    "|---|---|---:|---|"
) + @($Rows | ForEach-Object { "| $($_.id) | $($_.family) | $($_.passed) | $($_.result_json) |" }) | Set-Content -LiteralPath $MatrixMarkdownPath -Encoding UTF8
Write-Host "WINDOWS_COMPUTER_USE_PRODUCTION_MATRIX_COMPLETED=$AllPassed"
Write-Host "MATRIX_RESULT_JSON=$MatrixResultPath"
if (-not $AllPassed) { exit 1 }
```

Project rule for implementation: add Chinese comments to every new or modified PowerShell line explaining what the line does and why it exists.

- [ ] **Step 2: Add a runner file existence test**

Add this test:

```python
def test_matrix_runner_exists(self) -> None:
    runner_path = REPO_ROOT / "learning_agent" / "acceptance_controller" / "run_windows_computer_use_acceptance.ps1"
    text = runner_path.read_text(encoding="utf-8-sig")
    self.assertIn("WINDOWS_COMPUTER_USE_PRODUCTION_MATRIX_COMPLETED", text)
    self.assertIn("MATRIX_RESULT_JSON", text)
    self.assertIn("controller.ps1", text)
```

- [ ] **Step 3: Run the unit test**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_acceptance_matrix_manifest -v
```

Expected: pass.

### Task 5: Add Safe Permission Denial Scenario

**Files:**

- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_permission_denial_visible_terminal.json`
- Modify: `learning_agent/acceptance_controller/windows_computer_use_production_matrix.json`
- Modify: `learning_agent/tests/test_windows_computer_use_acceptance_matrix_manifest.py`

- [ ] **Step 1: Create denial scenario JSON**

Create this scenario:

```json
{
  "id": "agent_capability_computer_use_permission_denial_visible_terminal",
  "name": "agent_capability_computer_use_permission_denial_visible_terminal",
  "output_prefix": "agent_capability_computer_use_permission_denial_visible_terminal",
  "window_title_prefix": "LearningAgent-ComputerUsePermissionDeny",
  "entrypoint": "learning_agent/start_oauth_agent.bat",
  "visible_terminal_gate": true,
  "screenshot_artifacts_required": true,
  "max_seconds": 540,
  "final_log_wait_seconds": 120,
  "post_success_wait_seconds": 4,
  "environment": {
    "LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS": "0"
  },
  "permission_policy": {
    "default_response": "deny",
    "deny_contains": [
      "Visible terminal permission denial acceptance"
    ]
  },
  "success_marker": "COMPUTER_USE_PERMISSION_DENIAL_VISIBLE_TERMINAL_OK",
  "multi_prompt_lines": true,
  "prompt": "Open Computer Use full mode, trigger one safe request_access permission panel for Notepad, deny it, inspect status, then print the final marker.",
  "prompt_lines": [
    "/computer use --full",
    "Use Computer Use safely. Call exactly one mcp__computer-use__request_access for apps [\"notepad.exe\"] with grantFlags observe=true, desktopAction=true, clipboardRead=false, clipboardWrite=false, systemKeyCombos=false, and reason \"Visible terminal permission denial acceptance\". Do not click the screen, do not type into any app, do not open login pages, do not change system settings, and do not touch private files. After the tool result returns, reply exactly: COMPUTER_USE_PERMISSION_DENIAL_REQUEST_DONE",
    "/computer status",
    "Reply exactly: COMPUTER_USE_PERMISSION_DENIAL_VISIBLE_TERMINAL_OK"
  ],
  "required_event_states": [
    "agent_ready_for_user_prompt",
    "computer_status_printed",
    "user_prompt_received",
    "permission_required",
    "permission_answered",
    "computer_use_mcp_v2_tool",
    "final_answer_printed"
  ],
  "debug_log_contains": [
    "mcp__computer-use__request_access",
    "COMPUTER_USE_PERMISSION_DENIAL_VISIBLE_TERMINAL_OK"
  ],
  "event_answer_contains": [
    "COMPUTER_USE_PERMISSION_DENIAL_VISIBLE_TERMINAL_OK"
  ],
  "event_payload_contains": [
    "Computer Use Mode",
    "full_mode=true",
    "Visible terminal permission denial acceptance",
    "request_access",
    "permission_prompt_version=windows-permission-ui-v1"
  ],
  "max_permission_sent_count": 2
}
```

- [ ] **Step 2: Add denial scenario to manifest**

Add this manifest entry after `permission_allow`:

```json
{
  "id": "permission_deny",
  "family": "permission_deny",
  "scenario_path": "scenarios/agent_capability_computer_use_permission_denial_visible_terminal.json",
  "required_tokens": [
    "COMPUTER_USE_PERMISSION_DENIAL_VISIBLE_TERMINAL_OK",
    "Visible terminal permission denial acceptance"
  ],
  "risk_note": "Permission request only; controller denies the request; no desktop action."
}
```

- [ ] **Step 3: Extend test for permission policy**

Add this assertion in the manifest test when `scenario["id"] == "permission_deny"`:

```python
if scenario["id"] == "permission_deny":
    self.assertEqual(scenario_data["permission_policy"]["default_response"], "deny")
    self.assertIn("permission_required", scenario_data["required_event_states"])
    self.assertIn("permission_answered", scenario_data["required_event_states"])
```

- [ ] **Step 4: Run the denial scenario alone**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\controller.ps1 -ScenarioPath scenarios\agent_capability_computer_use_permission_denial_visible_terminal.json
```

Expected:

```text
ACCEPTANCE_CONTROLLER_COMPLETED=True
```

Then read the emitted `RESULT_JSON` and verify:

```json
{
  "completed": true,
  "permission_sent_count": 1
}
```

If the controller sends two answers because `/computer use --full` also prompts for confirmation, keep `max_permission_sent_count=2` and record the reason in `agent_memory/progress.md`.

### Task 6: Run The Production Matrix

**Files:**

- Run: `learning_agent/acceptance_controller/run_windows_computer_use_acceptance.ps1`
- Output: `learning_agent/acceptance_controller/runs/windows_computer_use_production_matrix-<timestamp>/matrix_result.json`
- Output: `learning_agent/acceptance_controller/runs/windows_computer_use_production_matrix-<timestamp>/matrix_result.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`

- [ ] **Step 1: Run the matrix**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\run_windows_computer_use_acceptance.ps1
```

Expected:

```text
WINDOWS_COMPUTER_USE_PRODUCTION_MATRIX_COMPLETED=True
MATRIX_RESULT_JSON=H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\windows_computer_use_production_matrix-<timestamp>\matrix_result.json
```

- [ ] **Step 2: Read matrix JSON**

Run:

```powershell
$path = "<MATRIX_RESULT_JSON_FROM_STEP_1>"
Get-Content -LiteralPath $path -Raw | ConvertFrom-Json | ConvertTo-Json -Depth 20
```

Expected:

```json
{
  "completed": true,
  "failed_count": 0
}
```

- [ ] **Step 3: If a scenario fails, do not continue silently**

For each failed row, read:

```powershell
Get-Content -LiteralPath "<row.result_json>" -Raw
Get-Content -LiteralPath "<row.run_dir>\latest_run_readable.md" -Raw
```

Record the exact failure in `agent_memory/bugs.md`.

### Task 7: Add User-Readable Documentation

**Files:**

- Create: `docs/computer_use_windows_production_acceptance.md`

- [ ] **Step 1: Write the documentation**

Create a concise doc with these sections:

```markdown
# Windows Computer Use Production Acceptance

## What This Checks

This matrix checks real visible terminal control, real agent prompt input, controlled Windows app actions, permission UI, permission denial, failure recovery, and resume behavior.

## How To Run

```powershell
powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\run_windows_computer_use_acceptance.ps1
```

## What Passing Means

Passing means every included controlled scenario produced `completed=true` and `assertion.passed=true` in its `result.json`.

## What Passing Does Not Mean

Passing does not mean OpenHarness can safely control every arbitrary Windows app. New app families need their own controlled scenario.

## Where Evidence Is Stored

Each scenario run stores `result.json`, `events.jsonl`, `latest_run_readable.md`, and visible terminal screenshots under `learning_agent/acceptance_controller/runs/`.
```

- [ ] **Step 2: Link the latest matrix run**

After the first full matrix pass, append:

```markdown
## Latest Known Passing Run

- Matrix result: `learning_agent/acceptance_controller/runs/windows_computer_use_production_matrix-<timestamp>/matrix_result.json`
- Matrix report: `learning_agent/acceptance_controller/runs/windows_computer_use_production_matrix-<timestamp>/matrix_result.md`
```

### Task 8: Verification And Learning Backup

**Files:**

- Modify: `agent_memory/context.md`
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md`
- Create: `learning_agent/test/windows_computer_use_production_acceptance_matrix_20260618/`

- [ ] **Step 1: Run focused tests**

Run:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_acceptance_matrix_manifest -v
```

Expected: all tests pass.

- [ ] **Step 2: Parse all new JSON files**

Run:

```powershell
@'
import json
from pathlib import Path
root = Path(r"H:\codexworkplace\sofeware\OpenHarness-main")
paths = [
    root / "learning_agent" / "acceptance_controller" / "windows_computer_use_production_matrix.json",
    root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_computer_use_permission_denial_visible_terminal.json",
]
for path in paths:
    json.loads(path.read_text(encoding="utf-8-sig"))
    print(f"json_ok {path}")
'@ | python -
```

Expected: both files print `json_ok`.

- [ ] **Step 3: Run the real visible terminal matrix**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\run_windows_computer_use_acceptance.ps1
```

Expected: `WINDOWS_COMPUTER_USE_PRODUCTION_MATRIX_COMPLETED=True`.

- [ ] **Step 4: Copy learning backup**

Copy these files into `learning_agent/test/windows_computer_use_production_acceptance_matrix_20260618/`:

```text
learning_agent/acceptance_controller/windows_computer_use_production_matrix.json
learning_agent/acceptance_controller/run_windows_computer_use_acceptance.ps1
learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_permission_denial_visible_terminal.json
learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_single_app_text_visible_terminal.json
learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_single_app_calculation_visible_terminal.json
learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_local_file_visible_terminal.json
learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_local_browser_visible_terminal.json
learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_multi_app_transfer_visible_terminal.json
learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_failure_recovery_visible_terminal.json
learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_phase148c_long_task_resume_visible_terminal.json
docs/computer_use_windows_production_acceptance.md
docs/superpowers/plans/2026-06-18-windows-computer-use-production-acceptance-matrix.md
agent_memory/context.md
agent_memory/progress.md
agent_memory/bugs.md
<latest matrix_result.json>
<latest matrix_result.md>
```

- [ ] **Step 5: Update project memory**

Append to `agent_memory/progress.md`:

```markdown
## 2026-06-18 Windows Computer Use Production Acceptance Matrix
- Matrix runner created: learning_agent/acceptance_controller/run_windows_computer_use_acceptance.ps1.
- Manifest created: learning_agent/acceptance_controller/windows_computer_use_production_matrix.json.
- Latest matrix result: <matrix_result.json>.
- Verification: focused unittest passed, JSON parse passed, visible terminal matrix passed.
```

Append to `agent_memory/context.md`:

```markdown
## 2026-06-18 Windows Computer Use Production Acceptance Matrix Context
- Use run_windows_computer_use_acceptance.ps1 as the production gate before claiming Windows Computer Use release readiness.
- Passing matrix means controlled representative workflows passed, not arbitrary Windows app coverage.
```

Append to `agent_memory/bugs.md` only if a scenario fails or stale tokens were found.

## 12. Verification Commands Summary

Use these commands before final completion:

```powershell
python -m unittest learning_agent.tests.test_windows_computer_use_acceptance_matrix_manifest -v
```

```powershell
@'
import json
from pathlib import Path
root = Path(r"H:\codexworkplace\sofeware\OpenHarness-main")
paths = [
    root / "learning_agent" / "acceptance_controller" / "windows_computer_use_production_matrix.json",
    root / "learning_agent" / "acceptance_controller" / "scenarios" / "agent_capability_computer_use_permission_denial_visible_terminal.json",
]
for path in paths:
    json.loads(path.read_text(encoding="utf-8-sig"))
    print(f"json_ok {path}")
'@ | python -
```

```powershell
powershell -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\run_windows_computer_use_acceptance.ps1
```

## 13. Final Completion Gate

Do not say this task is complete unless all of these are true:

- Focused unittest passed.
- JSON parse check passed.
- Matrix runner completed with `WINDOWS_COMPUTER_USE_PRODUCTION_MATRIX_COMPLETED=True`.
- Latest `matrix_result.json` has `completed=true` and `failed_count=0`.
- Every scenario run used `learning_agent/start_oauth_agent.bat` through `controller.ps1`.
- Evidence screenshots exist for every scenario that requires screenshots.
- Learning backup exists under `learning_agent/test/windows_computer_use_production_acceptance_matrix_20260618/`.
- Project memory files were updated.

## 14. Recommended Execution Strategy

Use `superpowers:subagent-driven-development` if the implementer wants parallel review of scenario audit, manifest tests, and runner design. Use `superpowers:executing-plans` if one agent is executing this plan end to end in the current session.

The safest sequence is:

1. Audit CLI tokens.
2. Repair stale scenario token lists.
3. Add manifest tests.
4. Add manifest.
5. Add runner.
6. Add denial scenario.
7. Run focused tests.
8. Run full visible terminal matrix.
9. Backup evidence and update memory.
