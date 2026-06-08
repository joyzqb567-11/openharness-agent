# 2026-06-02 Agent Capability Phase 15 Chrome Pairing Trigger

## 目标

- 新增安全的终端侧配对触发链路。
- `/chrome pairing-preview` 只读预览请求形状，不写 bridge 文件。
- `/chrome pairing-start-confirm I_UNDERSTAND_PAIR_CHROME` 写入本地 bridge 的 `pending_pairing_request`，不写 Windows registry。
- native host 在 `poll_commands` 响应中下发 pending pairing request。
- Chrome extension 收到 `pairing_request` 后回传 `pair_device`，并携带 `request_id` 和 `request_nonce`。

## 成功标准

- 预览命令输出 `chrome_pairing_preview`、`dry_run=true`、`pairing_request_id`，且不创建 bridge 文件。
- 确认命令输出 `chrome_pairing_start_confirm`、`pending_pairing_request_status=pending`。
- `/chrome` 状态页显示 `pending_pairing_request_status=pending`。
- bridge 在收到匹配的 `record_pairing()` 后把 request 标记为 `completed`。
- 扩展脚本包含 `pairing_request` 和 `request_nonce` 处理逻辑。

## 验证结果

- `python -m unittest learning_agent.tests.test_chrome_pairing_trigger_phase15`：4 tests OK。
- 相关回归：`python -m unittest learning_agent.tests.test_chrome_pairing_trigger_phase15 learning_agent.tests.test_chrome_pairing_diagnose_phase14 learning_agent.tests.test_chrome_extension_pairing_stage14 learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_status_snapshot_phase12 learning_agent.tests.test_chrome_terminal_subcommands_phase9`：24 tests OK。
- `python -m py_compile learning_agent\app\interactive.py learning_agent\browser_extension_host\bridge_server.py learning_agent\browser_extension_host\native_host.py learning_agent\runtime\status_snapshot.py learning_agent\app\chrome_status_renderer.py learning_agent\tests\test_chrome_pairing_trigger_phase15.py`：退出码 0。
- `node --check learning_agent\chrome_extension\background.js`：退出码 0。
- `python -m unittest discover -s learning_agent\tests`：591 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 `/chrome pairing-start-confirm I_UNDERSTAND_PAIR_CHROME`。
- 真实验收 run：`learning_agent/acceptance_controller/runs/agent_capability_phase15_chrome_pairing_trigger-20260602_201148`。
- `result.json`：`completed=true`，`assertion.passed=true`，`chrome_status_printed=true`，`permission_sent_count=0`。
- 独立 verifier：`completed=true`，`assertion.passed=true`，截图和事件日志 artifact 均存在。
- 截图确认终端输出包含 `chrome_pairing_start_confirm`、`dry_run=false`、`pending_pairing_request_status=pending` 和下一步说明。

## 风险边界

- Phase 15 负责触发和可见状态，不要求证明真实 Chrome extension 已完成 session sync；真实闭环放到 Phase 16。
- `pairing-start-confirm` 只写 bridge 文件，不写 registry，不修改浏览器 profile。

## 结论

- Phase 15 已完成代码修改、自动化测试、真实可见终端交互验收和学习备份。
- 下一阶段进入 Phase 16：session sync 真实闭环。
