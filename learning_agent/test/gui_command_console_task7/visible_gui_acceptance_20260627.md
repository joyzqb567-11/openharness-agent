# Task 7 Visible GUI Acceptance

- Date: 2026-06-27
- Window: OpenHarness Desktop
- Panel: 右侧检查器 -> 命令
- Evidence screenshot: `command_panel_visible_gui_20260627.jpg`
- Visible checks:
  - `后台命令` panel title is visible.
  - `GUI acceptance command` card is visible.
  - Command text shows `[REDACTED]` instead of the seeded secret.
  - Tail output shows `visible command output line one` and `visible command output line two`.
  - Stop button is visible but disabled, matching the current no-live-process-handle backend contract.
