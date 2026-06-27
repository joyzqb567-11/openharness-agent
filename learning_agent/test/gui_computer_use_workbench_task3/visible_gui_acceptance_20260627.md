# OpenHarness Desktop GUI Computer Use Workbench Task 3 Visible Acceptance

- Date: 2026-06-27
- Worktree: `H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\gui-toolchain-control-center`
- GUI window: `OpenHarness Desktop`
- Bridge: `http://127.0.0.1:8776`
- Renderer: `http://127.0.0.1:5177`
- Tool used: `computer-use`

## Checks

- Opened the real OpenHarness Desktop GUI window with Computer Use and selected the right-side `浏览器` tab.
- Confirmed the Browser panel was visible with provider rows and the new `Computer Use` workbench section.
- Confirmed the workbench showed the `申请权限`, `观察`, and `中止` buttons, plus `目标状态`, lock, abort, permission, recent observation, recent action, and low-level event feedback.
- Clicked `观察` in the real GUI. After restarting the stale bridge process, the visible main thread showed `Computer Use 观察：已刷新只读观察状态，未触发任何低层桌面动作。`
- Confirmed accessibility text showed `最近观察` and `最近动作` as `gui_computer_use_action · observe · observe · 已刷新只读观察状态，未触发任何低层桌面动作。`
- Confirmed `低层事件：0` was visible through UI Automation as adjacent text nodes `低层事件：` and `0`.
- Clicked `申请权限` in the real GUI. The visible main thread showed `Computer Use 申请权限：已申请只读观察权限，未执行鼠标、键盘或窗口控制。`
- Confirmed the workbench recent action showed `request-access` and `低层事件：0`.
- Clicked `中止` in the real GUI. The visible main thread showed `Computer Use 中止：Computer Use 已中止，后续低层动作会被停止状态挡住。`
- Confirmed the workbench mode changed to `stopped`, recent action showed `abort`, and `低层事件：0`.

## Bug Found And Fixed During Acceptance

- Symptom: first `观察` click returned `GuiClientError: 未知 GUI bridge POST 路径。`
- Root cause: port `8776` was already owned by an older bridge process that had started before Task 3 routes were added, so the real GUI was connected to stale backend code.
- Evidence: `POST /v2/gui/computer-use/observe` returned unknown route before bridge restart; after stopping PID `27712` and restarting `apps/desktop/scripts/start-backend.ps1`, the same POST returned schema version `2`, status `observed`, and `low_level_event_count=0`.
- Fix applied: no source code change was needed; restarted the current worktree bridge so it loaded the new route table.
- Retest: repeated `观察`, `申请权限`, and `中止` in the same real GUI window; all three passed.

## Result

PASS: Task 3 visible GUI acceptance passed after systematic debugging of the stale bridge process.
