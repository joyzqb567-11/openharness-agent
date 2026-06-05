# Phase109 Generic Real Launch Candidate - 2026-06-05

## Goal

继续落实“/computer use --full 后不走逐应用白名单”的设计，但仍保持默认不真实打开任意应用。

## Scope

- 新增 `learning_agent/computer_use/generic_real_launch_candidate.py`。
- 修改 `learning_agent/app/interactive.py`，让 `/computer launch obsidian` 的 Phase108 通用发现结果继续生成 Phase109 默认关闭候选证据。
- 新增 `learning_agent/tests/test_windows_computer_use_generic_real_launch_candidate_phase109.py`。
- 新增真实可见终端验收 scenario：`learning_agent/acceptance_controller/scenarios/agent_capability_phase109_generic_real_launch_candidate.json`。

## Result

Phase109 建立了通用真实启动候选模型：

- 默认关闭真实启动，后端不被调用。
- 显式记录型路径能证明 launcher 桥接、进程身份、窗口身份、清理和残留检查已串联。
- 继续拒绝 PowerShell 等高风险目标。
- 没有触碰真实桌面，没有扩张无边界动作。
- 不要求硬编码应用白名单，也不要求每个 app 单独补丁。

## Verification

- `python -m py_compile .\learning_agent\computer_use\generic_real_launch_candidate.py .\learning_agent\app\interactive.py .\learning_agent\tests\test_windows_computer_use_generic_real_launch_candidate_phase109.py`
- `python -m unittest learning_agent.tests.test_windows_computer_use_generic_app_discovery_phase108 learning_agent.tests.test_windows_computer_use_generic_real_launch_candidate_phase109`
- `python -m unittest learning_agent.tests.test_windows_computer_use_full_mode_controlled_real_launch_phase105 learning_agent.tests.test_windows_computer_use_interactive_full_launch_phase106 learning_agent.tests.test_windows_computer_use_interactive_launch_target_phase107 learning_agent.tests.test_windows_computer_use_generic_app_discovery_phase108 learning_agent.tests.test_windows_computer_use_generic_real_launch_candidate_phase109`
- `python -c "from learning_agent.app.interactive import phase109_main; raise SystemExit(phase109_main())"`
- 真实可见终端验收通过：`learning_agent/acceptance_controller/runs/agent_capability_phase109_generic_real_launch_candidate-20260605_143538/result.json`

## Final Token

`PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_READY PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_OK generic_real_launch_candidate_ready=true uses_phase108_generic_discovery=true hardcoded_app_whitelist_required=false per_app_patch_required=false real_launch_default_disabled=true default_off_backend_not_called=true recording_backend_reaches_launcher=true process_identity_verified=true window_identity_verified=true cleanup_completed=true residual_process_check_completed=true residual_owned_process=false high_risk_refused=true real_desktop_touched=false uncontrolled_actions_expanded=false`
