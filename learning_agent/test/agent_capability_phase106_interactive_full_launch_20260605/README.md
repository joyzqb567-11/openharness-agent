# Phase106 交互式 Full 启动接入备份

本目录保存 Phase106 新增和修改过的代码副本，方便后续学习和对照。

- `interactive.py`：包含 `/computer launch notepad`、Phase106 marker、Phase106 格式化输出和 `phase106_main()` 验收入口。
- `test_windows_computer_use_interactive_full_launch_phase106.py`：包含 Phase106 红测和回归测试。
- `agent_capability_phase106_interactive_full_launch.json`：包含真实可见终端验收场景。

关键验收 token：

```text
PHASE106_INTERACTIVE_FULL_LAUNCH_READY PHASE106_INTERACTIVE_FULL_LAUNCH_OK target_app=notepad full_mode_session_used=true controlled_launch_candidate_ready=true controlled_real_launch_gate_passed=true real_full_launch_attempted=true visible_window_verified=true cleanup_completed=true verified_window_cleanup_completed=true residual_owned_process=false real_desktop_touched=true uncontrolled_actions_expanded=false
```
