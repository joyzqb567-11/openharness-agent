# Agent Capability Phase 25 Real Extension Native Connect

## Goal

- Turn Phase 24 from diagnostic-only evidence into a live native messaging proof with a real local Chromium extension process.
- Verify that the native host launcher works when started by Chrome/Chromium, not only by Python tests.
- Strengthen visible terminal acceptance so `real_extension_e2e=false` cannot pass merely because `chrome_status_printed` appeared.

## Work Completed

- Confirmed Google Chrome stable ignored local unpacked extension command-line loading in this environment.
- Loaded `learning_agent/chrome_extension` in local visible Playwright Chromium with extensions enabled.
- Captured real extension id `lepnefooepbnjbcnhooiccpnafalfbdk`.
- Ran `/chrome install-confirm lepnefooepbnjbcnhooiccpnafalfbdk I_UNDERSTAND_WRITE_REGISTRY` through the required visible terminal controller.
- Confirmed and fixed native host launcher import failure by adding repo root to `PYTHONPATH`.
- Added event payload assertion support to `learning_agent/acceptance_controller/controller.ps1`.
- Added `/chrome` output capture to `chrome_status_printed.payload.output_text`.
- Added independent verifier support for `event_payload_contains`.
- Added a strict Phase 24 scenario requiring all five true values: connected, paired, prompt queued, workspace locked, and final E2E.
- Added a visible Chromium holder script under the learning backup directory to keep the real extension connected during terminal acceptance.

## Final Evidence

- Strict visible terminal run: `learning_agent\acceptance_controller\runs\agent_capability_phase24_real_chrome_extension_e2e-20260602_224404`.
- Result JSON: `completed=true`, `assertion.passed=true`, `permission_sent_count=0`.
- Event payload checks:
  - `real_extension_connected=true`
  - `paired=true`
  - `browser_prompt_queued=true`
  - `workspace_lock_ok=true`
  - `real_extension_e2e=true`
- Independent verifier replay also passed with all five event payload checks true.
- Full regression: `python -m unittest discover -s learning_agent\tests` ran 613 tests OK, skipped=1.

## Boundary

- The automated proof uses real local Chromium plus real Chrome extension/native messaging host.
- It does not prove Google Chrome stable currently has a persistent manual extension window open after the holder script exits.
- Current Google Chrome stable may need manual unpacked-extension loading; if its extension id differs, native host registration must be repeated for that id.
