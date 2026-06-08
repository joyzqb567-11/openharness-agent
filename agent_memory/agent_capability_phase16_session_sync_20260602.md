# 2026-06-02 Agent Capability Phase 16 Session Sync Real Closure

## 目标

- 证明浏览器侧 prompt 可以进入 durable `RuntimeCommandQueue`。
- durable command 必须保留机器可读的 `browser_prompt` 字段，包括 prompt、URL、title、tab_id、selected_text。
- `/chrome` 必须展示最近浏览器 prompt 的 command id 和来源 URL。
- 新增真实终端可执行的 `/chrome session-sync-selftest`，用于验收 session sync 入队闭环。

## 成功标准

- `bridge.enqueue_browser_prompt()` 创建 `mode=prompt` 的 durable command。
- command payload 包含 `text` 和结构化 `browser_prompt`。
- `selected_text` 限长到 2000 字符以内。
- `/chrome` 显示 `last_browser_prompt_id` 和 `last_browser_prompt_url`。
- `/chrome session-sync-selftest` 输出 `chrome_session_sync_selftest`、`queue_command_exists=true`、`last_browser_prompt_url=https://session-sync.local/selftest`。

## 验证结果

- `python -m unittest learning_agent.tests.test_chrome_session_sync_phase16`：3 tests OK。
- 相关回归：`python -m unittest learning_agent.tests.test_chrome_session_sync_phase16 learning_agent.tests.test_chrome_pairing_trigger_phase15 learning_agent.tests.test_chrome_pairing_diagnose_phase14 learning_agent.tests.test_chrome_extension_pairing_stage14 learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_status_snapshot_phase12 learning_agent.tests.test_chrome_terminal_subcommands_phase9`：27 tests OK。
- `python -m py_compile learning_agent\app\interactive.py learning_agent\browser_extension_host\bridge_server.py learning_agent\app\chrome_status_renderer.py learning_agent\tests\test_chrome_session_sync_phase16.py`：退出码 0。
- `python -m unittest discover -s learning_agent\tests`：594 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 `/chrome session-sync-selftest`。
- 真实验收 run：`learning_agent/acceptance_controller/runs/agent_capability_phase16_session_sync-20260602_201954`。
- `result.json`：`completed=true`，`assertion.passed=true`，`chrome_status_printed=true`，`permission_sent_count=0`。
- 独立 verifier：`completed=true`，`assertion.passed=true`，截图和事件日志 artifact 均存在。
- 截图确认终端输出包含 `chrome_session_sync_selftest`、`last_browser_prompt_url=https://session-sync.local/selftest`、`queue_command_exists=true`。

## 风险边界

- Phase 16 已证明 durable queue 入队闭环；真实 Chrome extension 手动安装后的完整端到端动作仍放到后续 Phase 18。
- `/chrome session-sync-selftest` 是验收自检命令，会写入本地 runtime queue 和 bridge 状态，但不写 registry、不操作真实浏览器页面。

## 结论

- Phase 16 已完成代码修改、自动化测试、真实可见终端交互验收和学习备份。
- 下一阶段进入 Phase 17：`/chrome` 可操作向导增强。
