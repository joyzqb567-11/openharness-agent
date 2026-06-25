# Desktop GUI Shell Learning Archive

This archive records the files, tests, smoke evidence, and acceptance notes for the Codex-style desktop GUI shell.

## Scope

This archive belongs to the 2026-06-25 long-running desktop GUI shell implementation.

The active implementation worktree is `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\desktop-gui-shell-v1`.

The active branch is `codex/desktop-gui-shell-v1`.

## Task Archives

- `task04_bootstrap/`
- `task05_gui_client/`
- `task06_shell_layout/`
- `task07_thread_state/`
- `task08_chat_lifecycle/`
- `task09_status_timeline/`
- `task10_project_session_sidebar/`
- `task11_browser_provider_panel/`
- `task12_permission_surfaces/`
- `task13_launch_scripts/`
- `task14_visible_smoke_acceptance/`
- `task15_release_gate/`

## Layer A Visible Desktop GUI Evidence

Status: passed for the V1 vertical slice.

Evidence commands:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\start-backend.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\start-desktop-dev.ps1
```

Visible screenshots:

- `desktop_gui_prompt_completed_cors_20260625.png`
- `desktop_gui_running_bottom_cancel_20260625.jpg`
- `desktop_gui_cancelled_bottom_button_20260625.jpg`
- `desktop_gui_permission_dialog_20260625.jpg`
- `desktop_gui_permission_approved_20260625.jpg`
- `desktop_gui_permission_denied_20260625.jpg`
- `desktop_gui_failed_error_text_20260625.jpg`
- `desktop_gui_retry_after_failed_20260625.jpg`
- `desktop_gui_tool_card_20260625.jpg`
- `desktop_gui_sidebar_session_restore_20260625.jpg`
- `desktop_gui_resume_session_clicked_20260625.jpg`
- `desktop_gui_english_prompt_20260625.jpg`
- `desktop_gui_english_prompt_bottom_20260625.jpg`

Verified visible checks:

- Real Electron desktop window opens and is not blank.
- Sidebar, thread panel, composer, status inspector, and browser provider panel are visible.
- GUI bridge bootstrap and event polling work through token-protected loopback HTTP.
- Chinese and English prompts can be entered from the GUI and complete.
- Running, completed, failed, cancelled, retried, and resumed states are visible.
- Tool events render as a visible tool card.
- Permission approval and denial are visible GUI flows backed by backend events.
- Cancel during a slow turn reaches a visible cancelled terminal state.
- Retry after failure creates a new linked turn.
- Sidebar recent conversation list restores real GUI sessions.
- Clicking a recent conversation resumes historical messages.
- Browser provider snapshot failures now degrade instead of crashing the bridge.

## Layer B Automated Verification Evidence

Status: passed.

Commands already run:

```powershell
python -m unittest learning_agent.tests.test_gui_bridge_contract learning_agent.tests.test_gui_bridge_events_contract learning_agent.tests.test_gui_bridge_security_contract learning_agent.tests.test_gui_bridge_lifecycle_contract learning_agent.tests.test_gui_bridge_permission_contract
cd apps\desktop
npm run lint
npm test -- --run
npm run lint
```

Latest observed results:

```text
Python GUI bridge groups: 24 tests OK.
Frontend lint: passed.
Frontend unit tests: 16 tests passed.
```

Release gate command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\apps\desktop\scripts\release-gate.ps1
```

Release gate result:

```text
24 Python GUI bridge tests OK.
Frontend lint passed.
Frontend unit tests: 16 passed.
Frontend production build passed.
```

## Layer C Conditional Backend-Agent Terminal Gate

Status: not triggered.

Layer C is not the GUI visual acceptance gate. Run `learning_agent/start_oauth_agent.bat` only if the implementation changes agent runtime behavior, MCP routing, model calls, browser automation, Computer Use, or backend permission enforcement.

If this task only changes GUI documentation or visual shell behavior, record:

```text
未触发：本次只改 GUI 视觉/交互层，没有修改后端 agent 行为。
```

2026-06-25 record:

```text
未触发：本次新增的是 Electron GUI 外壳、GUI bridge 生命周期、GUI smoke hooks、前端可见权限/取消/重试/恢复和验收门禁；没有修改模型调用、MCP 工具执行、真实浏览器自动化、Computer Use 执行或 backend agent runtime 行为。
```
