# Desktop GUI Toolchain Control Center Final Gate - 2026-06-28

## Automatic Gates

- Frontend unit tests: `npm --prefix apps/desktop run test` passed with `29 passed` test files and `105 passed` tests.
- Frontend lint/type gate: `npm --prefix apps/desktop run lint` passed.
- Frontend build gate: `npm --prefix apps/desktop run build` passed; Vite transformed `1621 modules` and completed production build.
- Backend GUI contract gate: all discovered `test_gui_*contract/workbench` modules passed with `95 tests`.

## Visible GUI Smoke

- `powershell -NoProfile -ExecutionPolicy Bypass -File apps/desktop/scripts/visible-gui-smoke.ps1` generated instructions at `learning_agent/test/desktop_gui_shell_v2/visible_gui_smoke/visible_gui_smoke_20260628_033622.txt`.
- `powershell -NoProfile -ExecutionPolicy Bypass -File apps/desktop/scripts/visible-gui-smoke.ps1 -Launch` opened the real desktop GUI and generated instructions at `learning_agent/test/desktop_gui_shell_v2/visible_gui_smoke/visible_gui_smoke_20260628_033638.txt`.
- The real window title was `OpenHarness Desktop`.
- The visible smoke prompt `集成门禁 smoke：请只回复 OK` completed in the chat path and emitted `turn_started`, `message_delta`, `message_completed`, and `gui_turn_completed` events.

## Computer-Use Visual Verification

- Chat remained usable: the prompt appeared in the conversation, the assistant response completed, and the event stream showed the completed turn.
- Tool trace tab was visible as `工具轨迹` and showed an empty safe state when no tool calls were present.
- Toolchain inventory was visible under the right-side `链路` tab as `工具链控制中心`, showing `65 tools`, `11 groups`, schema `2`, and real catalog entries such as `ask_user_question`, `bash`, `edit`, and `prompt_surface_report`.
- Harness controls were visible under the right-side `任务` tab as `长任务 Harness`, showing a running goal, queue, checkpoints, and visible `暂停`, `恢复`, `停止`, and `Checkpoint` buttons.
- MCP panel was visible as `MCP 管理中心`, showing `servers`, `resources`, `prompts`, and the empty configuration state.
- Memory panel was visible as `记忆与预算`, showing `Context`, `Progress`, `Bugs`, `prompt_surface_report`, `token_budget_report`, `notebook_read`, and `notebook_edit`.
- Planning panel was visible as `计划协作控制中心`, showing todos, active tasks, peer message sections, and planning tools.
- Command panel was visible as `后台命令`, showing command counts and a safe empty state.
- Acceptance panel was visible as `验收控制器`, showing `160 scenarios`, `controller ready`, `visible gate`, scenario rows, evidence status, and `运行` buttons.
- Browser panel was visible as `浏览器状态`, showing `visible chromium`, `real chrome cdp`, `chrome extension`, console/network/download/replay sections, and safe unavailable states.
- Computer Use workbench was visible inside the browser workbench as `Computer Use 工作台`, with `申请权限`, `观察`, and `中止` controls.
- Settings panel was visible as `设置`, showing provider/bridge state and feature surfaces.
- Diagnostics panel was visible as `诊断`, showing `Release Gate`, `Trace`, `Trace Tail`, `Compact`, `Resume`, `Health`, `LSP`, `REPL`, and `复制诊断包`.
- No blank major panel, crash screen, or obvious unreadable overlap was observed during the final visible pass.

## Result

- Final integration gate passed.
