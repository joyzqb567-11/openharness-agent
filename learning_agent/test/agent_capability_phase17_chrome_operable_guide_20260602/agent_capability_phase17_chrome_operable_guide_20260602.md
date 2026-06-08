# 2026-06-02 Agent Capability Phase 17 Chrome Operable Guide

## 目标

- 把 `/chrome` 从单纯状态列表升级为可操作向导。
- 在终端里直接显示当前 Chrome 状态、下一步建议、可用命令、风险等级和确认 token 要求。
- 让新手用户可以从 `/chrome` 一眼判断哪些命令只是预览，哪些命令会写 registry 或写入 bridge 状态。

## 成功标准

- `/chrome` 输出包含 `Chrome Current`，明确 `state=...`。
- `/chrome` 输出包含 `Chrome Guide`，给出下一条建议命令。
- `/chrome` 输出包含 `Chrome Actions`，每条命令都有 `risk=...` 和 `confirm=...`。
- registry 写入/删除命令标为 `risk=high confirm=yes`。
- pairing 写入请求命令标为 `risk=medium confirm=yes`。
- 只读预览、repair、自检命令标为 `risk=low confirm=no`。

## 修改内容

- 扩展 `learning_agent/app/chrome_status_renderer.py`：
  - 新增 `_chrome_current_state()`，把 installer、extension、pairing、pending request 合并成简短状态码。
  - `/chrome` 新增 `Chrome Current` 区块。
  - `Chrome Actions` 改为风险/确认/命令/说明的紧凑格式。
- 扩展 `learning_agent/tests/test_chrome_terminal_status_ui_stage18.py`：
  - 新增 Phase 17 测试，覆盖当前状态、低风险命令、高风险确认命令、中风险确认命令，以及单行长度边界。
- 新增真实终端验收场景：
  - `learning_agent/acceptance_controller/scenarios/agent_capability_phase17_chrome_operable_guide.json`

## 验证结果

- `python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18.ChromeTerminalStatusUiStage18Tests.test_render_chrome_status_labels_current_state_risk_and_confirmation`：1 test OK。
- `python -m unittest learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_session_sync_phase16 learning_agent.tests.test_chrome_pairing_trigger_phase15 learning_agent.tests.test_chrome_pairing_diagnose_phase14`：14 tests OK。
- `python -m py_compile learning_agent\app\chrome_status_renderer.py learning_agent\tests\test_chrome_terminal_status_ui_stage18.py`：退出码 0。
- `python -m unittest discover -s learning_agent\tests`：595 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 `/chrome`。
- 真实验收 run：`learning_agent/acceptance_controller/runs/agent_capability_phase17_chrome_operable_guide-20260602_202526`。
- `result.json`：`completed=true`，`assertion.passed=true`，`chrome_status_printed=true`，`permission_sent_count=0`。
- 独立 verifier：`completed=true`，`assertion.passed=true`，截图、事件日志和 result artifact 全部存在。
- 最终截图确认终端里可见 `Chrome Current`、`Chrome Guide`、`Chrome Actions`，并显示 `risk=` 与 `confirm=` 字段。

## 风险边界

- Phase 17 只改变 `/chrome` 文本呈现和测试场景，不写 registry、不操作浏览器页面、不改变 pairing 状态。
- 当前真实终端截图中仍显示本机 extension 未连接，这是 Phase 18 的真实 extension 端到端验收范围。

## 结论

- Phase 17 已完成代码修改、自动化测试、真实可见终端交互验收、独立 verifier 复验和学习备份。
- 下一阶段进入 Phase 18：真实 Chrome extension/native host/session sync 端到端验收。
