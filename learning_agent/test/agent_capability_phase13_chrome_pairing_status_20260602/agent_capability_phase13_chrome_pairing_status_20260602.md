# Agent Capability Phase 13 - Chrome Pairing Status

## 目标
- 把 Chrome extension pairing / session sync 接入 `/chrome` 向导。
- 已注册 native host 后，用户能看到扩展是否已配对、session id、device id、最近同步时间和缺失项。

## 新增能力
- `build_status_snapshot()` 会从 `chrome_extension_bridge.json` 读取脱敏 pairing 摘要。
- `browser.provider_status.chrome_extension` 新增：
  - `paired`
  - `device_id`
  - `session_id`
  - `allowed_origin_count`
  - `last_browser_prompt_id`
  - `last_browser_prompt_url`
- `/chrome` 新增 pairing/session sync 摘要行。
- `/chrome` 在 native host 已注册且 pairing 已完成时提示 `session sync 已连接`。
- 修正 `learning_agent` 工作区下 bridge 状态路径，避免读取 `learning_agent\learning_agent\memory`。

## 自动化验证
- 红灯：渲染器缺少 `paired=true/session_id`，快照缺少 `paired`。
- 绿灯：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18.ChromeTerminalStatusUiStage18Tests.test_render_chrome_status_shows_pairing_and_session_sync`
- 绿灯：`python -m unittest learning_agent.tests.test_chrome_status_snapshot_phase12.ChromeStatusSnapshotPhase12Tests.test_status_snapshot_includes_extension_pairing_and_session_sync`
- 相关回归：`python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_status_snapshot_phase12 learning_agent.tests.test_chrome_extension_pairing_stage14 learning_agent.tests.test_chrome_extension_status_ecosystem_stage8 learning_agent.tests.test_status_ecosystem_deep_alignment`，Ran 14 tests OK。
- 编译检查：`python -m py_compile learning_agent\app\chrome_status_renderer.py learning_agent\runtime\status_snapshot.py learning_agent\tests\test_chrome_terminal_status_ui_stage18.py learning_agent\tests\test_chrome_status_snapshot_phase12.py`，退出码 0。
- 全量回归：`python -m unittest discover -s learning_agent\tests`，Ran 583 tests OK，skipped=1。

## 真实终端验收
- 场景文件：`learning_agent/acceptance_controller/scenarios/agent_capability_phase13_chrome_pairing_status.json`
- 验收策略：真实终端输入 `/chrome`，截图确认出现 `paired=`、`device_id=`、`session_id=`。
- 第一次真实终端验收 run：`learning_agent/acceptance_controller/runs/agent_capability_phase13_chrome_pairing_status-20260602_194201`
  - 失败原因：验收控制器重复输入成 `/chrome/chrome`，交互循环未识别该粘连命令，导致进入模型调用。
  - 修复：新增 `is_chrome_terminal_command()`，把 `/chrome/chrome` 视为 `/chrome` 状态命令。
- 第二次真实终端验收 run：`learning_agent/acceptance_controller/runs/agent_capability_phase13_chrome_pairing_status-20260602_194601`
- 结果：`completed=true`，`assertion.passed=true`，`permission_sent_count=0`。
- 截图确认：终端显示 `paired=false device_id= session_id= allowed_origin_count=0`。
- 结论：渲染和状态接入已完成；本机当前实际扩展配对尚未完成，下一阶段应做配对触发/诊断。
- 独立 verifier 复验：`completed=true`，截图、事件日志、权限次数和事件状态全部通过。
