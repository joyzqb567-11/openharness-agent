# Phase90 Windows Live App Dispatcher Record

Date: 2026-06-04

Status: completed.

## Goal

把 Phase76-89 的生产闭环继续推进到 Phase90：新增一个受控 live app dispatcher，把 Phase60 持久授权、Phase69 应用启动/聚焦、Phase71 输入事件、Phase72 真实应用安全边界、Phase74 Paint 皮卡丘计划和 Phase58 安全窗口真实 smoke 路径串起来。

## Implemented Files

- `learning_agent/computer_use/live_app_dispatcher.py`
- `learning_agent/tests/test_windows_computer_use_live_app_dispatcher_phase90.py`
- `learning_agent/acceptance_controller/scenarios/agent_capability_phase90_live_app_dispatcher.json`
- `learning_agent/computer_use/__init__.py`

## Key Tokens

- Marker: `PHASE90_WINDOWS_LIVE_APP_DISPATCHER_READY`
- OK token: `PHASE90_WINDOWS_LIVE_APP_DISPATCHER_OK`
- CLI success line includes: `live_dispatcher_ready=true`, `real_app_dispatch_path=true`, `default_real_dispatch_enabled=false`, `requires_explicit_live_env_gate=true`, `notepad_live_dispatch_contract=true`, `mspaint_pikachu_live_plan=true`, `dangerous_window_zero_events=true`, `unauthorized_window_zero_events=true`, `raw_text_hidden=true`, `uncontrolled_actions_expanded=false`

## Verification

- TDD red confirmed first: `ModuleNotFoundError: No module named 'learning_agent.computer_use.live_app_dispatcher'`
- `py_compile` passed for the Phase90 module and focused test.
- Focused Phase90 tests passed: 4 OK.
- Phase76-90 regression passed: 8 OK.
- Windows Computer Use test discovery passed: 209 OK.
- `python -m compileall learning_agent` passed.
- CLI self-check printed the fixed Phase90 token line.
- Real visible `start_oauth_agent.bat` terminal acceptance passed through `learning_agent/acceptance_controller/controller.ps1`: `learning_agent/acceptance_controller/runs/agent_capability_phase90_live_app_dispatcher-20260604_093939/result.json`.
- Independent result JSON assertion passed with `completed=True`, `assertion_passed=True`, `final_printed=True`, and `permission_sent_count=0`.

## Boundary

Phase90 creates a real app dispatch path, but default execution remains safe contract / recording dispatch mode. It does not perform uncontrolled arbitrary-app live dispatch, does not open Paint live in automated tests, and does not bypass permission gates. True desktop dispatch is still behind explicit environment gates and existing safety layers.
