# Agent Capability Phase 26 Windows OS Computer Use Blueprint

## Status

- Phase 26 is a written blueprint only.
- No runtime Computer Use implementation was changed in this phase.
- Phase 25 already exists as the real extension/native-host connection follow-up, so the Windows OS Computer Use blueprint is numbered Phase 26 to avoid history collision.

## Blueprint Files

- Formal plan: `docs/superpowers/plans/2026-06-02-phase26-windows-os-computer-use-blueprint.md`
- Learning backup: `learning_agent/test/agent_capability_phase26_windows_computer_use_blueprint_20260602/phase26_blueprint.md`

## Key Decisions

- Use ClaudeCode as the architecture reference for MCP/tool wrapping, permission approval, lock ownership, abort, session state, and audit evidence.
- Use Codex Computer Use as the Windows design reference for app/window targeting, UI Automation, SendInput, Windows.Graphics.Capture, window-relative coordinates, and strict Windows safety boundaries.
- Do not depend on the Codex plugin as a production dependency. `learning_agent` needs an independent Windows-native backend.
- Keep model-facing tools compact: `computer_status`, future `computer_observe`, and `computer_action`.
- Real desktop actions remain disabled by default and must require explicit opt-in plus action confirmation.

## Proposed Implementation Phases

- Phase 27: typed Computer Use protocol and tests.
- Phase 28: read-only Windows app/window inventory.
- Phase 29: window screenshot and UI Automation observation.
- Phase 30: safe window-relative actions.
- Phase 31: lock, abort, and evidence chain.
- Phase 32: `/computer` terminal status UI.
- Phase 33: real visible terminal end-to-end acceptance.

## Stop Conditions

- Stop before native helper implementation until the user approves this blueprint.
- Stop before any real mouse or keyboard action unless the opt-in gate, permission gate, lock, and safe target validation all pass.
- Stop if the target is a terminal, Codex UI, security/privacy app, password manager, or authentication dialog.
- Stop if real visible terminal acceptance cannot be completed.

## Verification For This Phase

- This phase modifies documentation and memory only.
- No runtime tests were required because no production code changed.
- Future implementation phases must include automated tests plus `start_oauth_agent.bat` visible terminal acceptance.
