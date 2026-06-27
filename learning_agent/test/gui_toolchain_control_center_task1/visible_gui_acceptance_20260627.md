# Desktop GUI Toolchain Control Center Task 1 Visible Acceptance

- Date: 2026-06-27
- Window: `OpenHarness Desktop`
- Worktree: `.worktrees/gui-toolchain-control-center`
- Branch: `codex/gui-toolchain-control-center`
- Bridge: `http://127.0.0.1:8776`
- Renderer: `http://127.0.0.1:5177`
- Toolchain endpoint: `GET /v2/gui/toolchain`

## Automatic Gates

- Backend contract: `python -m unittest discover -s learning_agent/tests -p test_gui_toolchain_contract.py -v` passed, 2 tests.
- Frontend unit tests: `npm --prefix apps/desktop run test` passed, 20 files and 84 tests.
- Frontend type gate: `npm --prefix apps/desktop run lint` passed.
- Desktop build: `npm --prefix apps/desktop run build` passed.

## Computer-Use Visible Gate

- Confirmed real Electron window title: `OpenHarness Desktop`.
- Confirmed right inspector tabs include `状态`, `工具`, `链路`, `浏览器`, `任务`, `设置`, `诊断`.
- Opened `链路` tab in the real GUI.
- Confirmed panel heading: `工具链`.
- Confirmed summary: `65 tools`, `11 groups`, `schema 2`.
- Confirmed grouped tool entries render, including `Core Tools`, `read_last_observation`, and repeated reuse source labels `learning_agent.tools.catalog`.
- Confirmed panel was not blank and had no obvious text overlap in the visible right inspector.

## Debugging Note

- Initial visible smoke connected to stale `8776` bridge and stale `5177` renderer, so the GUI first showed no `链路` tab or later `0 tools`.
- Root cause was stale fixed-port processes, not Task 1 code.
- Resolution was to stop the stale processes and restart the current worktree bridge and renderer.
