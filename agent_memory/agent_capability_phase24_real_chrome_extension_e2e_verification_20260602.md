# Phase 24/25 Real Chrome Extension E2E Verification

## Verification Commands

- `python -m unittest learning_agent.tests.test_real_chrome_extension_e2e_phase24`
  - Result: passed, 5 tests OK.
- `python -m unittest learning_agent.tests.test_acceptance_verifier`
  - Result: passed, 5 tests OK.
- `python -m unittest learning_agent.tests.test_real_chrome_extension_e2e_phase24 learning_agent.tests.test_observability_acceptance`
  - Result: passed, 14 tests OK.
- `python -m unittest learning_agent.tests.test_chrome_extension_installer_stage13 learning_agent.tests.test_chrome_terminal_subcommands_phase9`
  - Result: passed, 14 tests OK.
- `python -m unittest discover -s learning_agent\tests`
  - Result: passed, 613 tests OK, 1 skipped.
- `python -m py_compile learning_agent\acceptance\verifier.py learning_agent\tests\test_acceptance_verifier.py learning_agent\browser_extension_host\manifest_installer.py learning_agent\app\interactive.py learning_agent\browser_automation_mcp_server.py learning_agent\tests\test_real_chrome_extension_e2e_phase24.py learning_agent\tests\test_observability_acceptance.py learning_agent\tests\test_chrome_extension_installer_stage13.py`
  - Result: passed.
- `python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_phase24_real_chrome_extension_e2e.json`
  - Result: passed.
- `python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_phase25_install_real_extension_native_host.json`
  - Result: passed.
- `node --check learning_agent\chrome_extension\background.js`
  - Result: passed.

## Native Host Registration

- Real install-confirm visible terminal run: `learning_agent\acceptance_controller\runs\agent_capability_phase25_install_real_extension_native_host-20260602_222940`.
- Controller result: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Registered extension id: `lepnefooepbnjbcnhooiccpnafalfbdk`.
- Native host manifest: `learning_agent\memory\chrome_native_host\com.openharness.learning_agent.json`.
- Launcher now sets `OPENHARNESS_LEARNING_AGENT_WORKSPACE=H:\codexworkplace\sofeware\OpenHarness-main\learning_agent`.
- Launcher now sets `PYTHONPATH=H:\codexworkplace\sofeware\OpenHarness-main;%PYTHONPATH%`, fixing the confirmed `ModuleNotFoundError: No module named 'learning_agent'` native host failure.

## Strict Visible Terminal Acceptance

- Browser holder: `learning_agent\test\agent_capability_phase24_real_chrome_extension_e2e_20260602\phase25_hold_real_chromium_extension.py`.
- Holder evidence: loaded worker `chrome-extension://lepnefooepbnjbcnhooiccpnafalfbdk/background.js`.
- Controller command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\learning_agent\acceptance_controller\controller.ps1 -ScenarioPath H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\agent_capability_phase24_real_chrome_extension_e2e.json`.
- Strict run directory: `learning_agent\acceptance_controller\runs\agent_capability_phase24_real_chrome_extension_e2e-20260602_224404`.
- Controller result: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Controller payload checks all passed:
  - `real_extension_connected=true`
  - `paired=true`
  - `browser_prompt_queued=true`
  - `workspace_lock_ok=true`
  - `real_extension_e2e=true`
- Independent verifier now also replays `event_payload_contains`; latest verifier result includes all five `event_payload_checks=true`.
- Final screenshot: `learning_agent\acceptance_controller\runs\agent_capability_phase24_real_chrome_extension_e2e-20260602_224404\03_final.png`.

## Boundary

- This is a real local Chromium extension/native messaging E2E check, not a fake bridge write.
- The visible browser used for automated extension loading was local Playwright Chromium, because current Google Chrome stable ignored command-line local extension loading in this environment.
- After the holder script exits, bridge state can return to `connected=false` with `disconnect_reason=chrome_native_host_eof`; the successful proof is the strict visible terminal run while the extension was open.
- If the extension is later loaded manually in Google Chrome stable and Chrome gives a different extension id, `/chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY` must be rerun for that id.
