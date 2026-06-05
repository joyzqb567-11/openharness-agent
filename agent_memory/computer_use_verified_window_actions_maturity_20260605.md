# Computer Use Verified Window Actions Maturity 2026-06-05

## 背景

本次执行蓝图 Task 6：让通用桌面动作在派发前必须绑定已验证的 agent 自有窗口身份，避免同名窗口、漂移窗口或用户原本打开的应用被误控。

## 已完成

- 新增 `phase114_verified_action_gate(...)`，统一输出 `before_identity`、`after_identity`、`same_target`、`blocked`、`decision`、`low_level_event_count`。
- `WindowsClosedLoopComputerExecutor.run(...)` 在调用 actor 前先执行身份门禁，门禁阻断时不会继续调用 actor。
- `WindowsGenericControlActionRuntime` 的 `click_by_query`、`type_by_query`、`click_by_visual_point` 已接入身份门禁。
- `WindowsGenericInputActionRuntime` 的 `send_hotkey`、`navigate_menu`、`scroll_at`、`drag_path` 已接入身份门禁。
- 新增 Task6 测试 `test_windows_computer_use_verified_window_actions_maturity.py`，覆盖缺身份阻断、已验证放行、漂移阻断、abort 派发前归零。
- 已将本次修改文件复制到 `learning_agent/test/computer_use_verified_window_actions_maturity_20260605/` 供用户学习。

## 验证

- `python -m py_compile learning_agent\computer_use\closed_loop_executor.py learning_agent\computer_use\generic_control_actions.py learning_agent\computer_use\generic_input_actions.py learning_agent\tests\test_windows_computer_use_verified_window_actions_maturity.py`
- `python -m unittest learning_agent.tests.test_windows_computer_use_verified_window_actions_maturity learning_agent.tests.test_windows_computer_use_closed_loop_executor_phase68 learning_agent.tests.test_windows_computer_use_generic_control_actions_phase70 learning_agent.tests.test_windows_computer_use_generic_input_actions_phase71 learning_agent.tests.test_windows_computer_use_target_identity_maturity`

## 风险

- 当前 Task6 仍是记录型动作验证，真实可见终端最终验收必须等 Task7/Task8 汇总后执行。
