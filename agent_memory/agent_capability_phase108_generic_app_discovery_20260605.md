# Phase108 Generic App Discovery Memory

## Context

- 用户指出：本机可能有成千上万个应用，如果每个应用都要加入白名单或逐个打通，就不是通用 Computer Use。
- Phase108 因此改为通用应用发现路线，而不是继续扩展 Calculator/Paint 这类逐应用 smoke。
- 新模块是 `learning_agent/computer_use/generic_app_discovery.py`。
- 交互接入点是 `learning_agent/app/interactive.py` 的 `/computer launch <app>`。

## What Changed

- 新增 Phase108 marker：`PHASE108_GENERIC_APP_DISCOVERY_READY`。
- 新增 Phase108 OK token：`PHASE108_GENERIC_APP_DISCOVERY_OK`。
- 新增 `resolve_generic_app_launch_target()`，支持注入候选、开始菜单只读发现、fallback 候选。
- 普通目标输出 `hardcoded_app_whitelist_required=false` 和 `per_app_patch_required=false`。
- 高风险目标继续由 Phase107/Phase108 风险词拒绝，不进入真实启动计划。
- `/computer launch obsidian` 在 full 模式下可以走通用发现路径，但仍然 `real_full_launch_attempted=false`。
- 本机验收里 Obsidian 被 `candidate_source=start_menu` 发现，所以最终稳定字段使用 `generic_target_default_off=true`，不再要求它一定是 unknown fallback。

## Verification

- TDD red confirmed: Phase108 focused tests first failed because module missing and `/computer launch obsidian` still returned Phase107 unknown refusal.
- Focused tests passed: `python -m unittest learning_agent.tests.test_windows_computer_use_generic_app_discovery_phase108` -> 3 OK.
- Adjacent regression passed: Phase106 + Phase107 + Phase108 -> 9 OK.
- Phase105-108 regression passed: 12 OK.
- Compile passed: `python -m py_compile learning_agent/computer_use/generic_app_discovery.py learning_agent/app/interactive.py learning_agent/tests/test_windows_computer_use_generic_app_discovery_phase108.py`.
- Scenario JSON validation passed with `python -m json.tool`.
- Direct default smoke passed through `phase108_main()` with `real_desktop_touched=false`.
- Real visible terminal acceptance passed in `learning_agent/acceptance_controller/runs/agent_capability_phase108_generic_app_discovery-20260605_140739/result.json`.
- Independent verifier passed with `completed=true`, `assertion.passed=true`, `permission_sent_count=0`, and required screenshots/logs present.

## Boundary

- Phase108 does not claim arbitrary physical launch or arbitrary desktop control.
- It closes the per-app whitelist design gap for ordinary app target planning.
- Real app opening remains default-off.
- High-risk targets remain refused.
- Future real-launch expansion still needs target identity, visible-window verification, cleanup, residual-process checks, abort handling, and real visible terminal acceptance.
