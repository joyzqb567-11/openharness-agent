# 2026-06-07 Phase137 Computer Use structured action acceptance

- 问题：`computer_use_full_open_wechat_probe.json` 过去把真实启动证据写在 `debug_log_contains`，包括 `real_launch_performed=True`、`visible_window_verified=True`、`launch_backend=start_menu_shortcut` 和 `display_name=微信`。这在开发调试期有用，但产品关闭调试日志后会失去正式验收证据。
- 根因：`LearningAgent._computer_action()` 执行真实 `computer_action` 后只记录 observation/runtime trace，没有向 `LEARNING_AGENT_ACCEPTANCE_EVENT_LOG` 写正式结构化动作结果事件。
- 修复：新增 `computer_action_result` acceptance event，payload 使用 `computer_action_structured_evidence` 模型，包含 `real_launch_performed`、`visible_window_verified`、`launch_backend`、`display_name`、`target_window_present`、`real_desktop_touched` 等字段。
- 场景迁移：微信 full 模式真实验收场景已清空 `debug_log_contains`，改为检查 `event_payload_contains` 里的正式 `computer_action_result` 结构化字段。
- 额外修复：完整 Windows Computer Use 回归暴露旧 Phase74/75 代表性 E2E 矩阵仍只认可 `executable == explorer.exe/msedge.exe`。当前 launch resolver 已支持 `start_menu_shortcut`，所以 Phase74 已改为通过安全 resolver 计划和目标身份匹配来认可 exe、快捷方式等多后端。
- 验证：新增红测先复现 debug log 依赖和缺少 payload helper；修复后 `test_observability_acceptance`、Phase74/75、完整 `test_windows_computer_use_*.py` 共 463 个测试通过。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，运行 `computer_use_full_open_wechat_probe-20260607_160958`，`result.json` 显示 `completed=true`、`assertion.passed=true`、`debug_log_checks={}`，并且 event payload 检查全部为 true。
- 学习副本：本轮代码副本已保存到 `learning_agent/test/computer_use_structured_action_acceptance_phase137_20260607/`。
