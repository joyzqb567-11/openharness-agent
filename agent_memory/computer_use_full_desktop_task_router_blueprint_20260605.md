# Computer Use Full Desktop Task Router Blueprint Summary

Date: 2026-06-05

Status: formal root-cause blueprint written.

Core finding:
- `/computer use --full` currently opens a mode/permission state, but ordinary natural-language desktop prompts still reach the normal tool surface.
- The Paint Pikachu user trial proved the prompt was received, but the task used `bash + System.Drawing + Start-Process mspaint.exe` instead of Computer Use GUI actions.
- The root fix is a Desktop Task Router that sends local-app prompts into the Computer Use observe-plan-act-verify loop.

Blueprint:
- Main spec: `docs/superpowers/specs/2026-06-05-computer-use-full-desktop-task-router-blueprint.md`.
- Backup: `learning_agent/test/computer_use_full_desktop_task_router_blueprint_20260605/2026-06-05-computer-use-full-desktop-task-router-blueprint.md`.

Success boundary:
- Full mode must route local desktop prompts to Computer Use.
- Script-generated final artifacts must be rejected for desktop GUI tasks.
- The strict Paint Pikachu acceptance must prove real GUI actions, owned Paint window identity, after-action screenshots, canvas change evidence, and `/computer stop`.

Stop boundary:
- Stop and report if the work requires system-level hooks, registry/UAC/security-policy changes, sensitive credentials, or cannot prove target-window-safe GUI actions.
