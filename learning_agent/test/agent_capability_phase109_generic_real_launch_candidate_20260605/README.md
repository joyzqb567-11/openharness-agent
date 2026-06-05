# Phase109 Generic Real Launch Candidate Backup

这个目录保存 Phase109 本次新增和修改的关键文件，方便学习和复盘。

## Files

- `generic_real_launch_candidate.py`：Phase109 通用真实启动候选、身份验证、窗口身份、清理和残留检查模型。
- `interactive.py`：接入 `/computer launch <app>` 的真实交互输出路径。
- `test_windows_computer_use_generic_real_launch_candidate_phase109.py`：Phase109 红绿测试。
- `agent_capability_phase109_generic_real_launch_candidate.json`：真实可见终端验收场景。
- `visible_terminal_result.json`：真实可见终端验收结果。
- `visible_terminal_latest_run_readable.md`：真实可见终端验收可读日志。

## Final Token

`PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_READY PHASE109_GENERIC_REAL_LAUNCH_CANDIDATE_OK generic_real_launch_candidate_ready=true uses_phase108_generic_discovery=true hardcoded_app_whitelist_required=false per_app_patch_required=false real_launch_default_disabled=true default_off_backend_not_called=true recording_backend_reaches_launcher=true process_identity_verified=true window_identity_verified=true cleanup_completed=true residual_process_check_completed=true residual_owned_process=false high_risk_refused=true real_desktop_touched=false uncontrolled_actions_expanded=false`
