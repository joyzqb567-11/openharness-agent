# 2026-06-02 Agent Capability Phase 18 Chrome Extension E2E

## 目标

- 在真实可见终端里提供一条可审计的 Chrome extension/native host/session sync 端到端证据命令。
- 验证 native host manifest 和 launcher 是否可生成并可读。
- 验证 pairing request 能从 pending 闭合为 completed。
- 验证浏览器侧 prompt 能进入 durable `RuntimeCommandQueue`。
- 明确区分本地协议自检和真实 Chrome extension 已连接，避免把模拟链路说成真实扩展已连。

## 修改内容

- 新增 `/chrome extension-e2e-check`。
- 命令输出 `manifest_ok`、`launcher_ok`、`pairing_completed`、`browser_prompt_queued`、`real_extension_connected`、`real_extension_e2e` 和 `e2e_level`。
- 自检 bridge 使用隔离文件 `memory/chrome_extension_e2e_selftest/chrome_extension_bridge.json`，不会污染真实 `chrome_extension_bridge.json` 连接状态。
- `/chrome` 的 `Chrome Actions` 新增低风险无确认入口：`/chrome extension-e2e-check`。
- 新增 Phase 18 自动化测试 `learning_agent/tests/test_chrome_extension_e2e_matrix_phase18.py`。
- 新增真实终端验收场景 `learning_agent/acceptance_controller/scenarios/agent_capability_phase18_chrome_extension_e2e.json`。

## 验证结果

- 红灯验证：新增测试首次失败，原因是 `/chrome extension-e2e-check` 仍是未知子命令。
- 绿灯验证：`python -m unittest learning_agent.tests.test_chrome_extension_e2e_matrix_phase18`：2 tests OK。
- 相关回归：`python -m unittest learning_agent.tests.test_chrome_extension_e2e_matrix_phase18 learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_session_sync_phase16 learning_agent.tests.test_chrome_pairing_trigger_phase15 learning_agent.tests.test_chrome_pairing_diagnose_phase14 learning_agent.tests.test_chrome_extension_pairing_stage14 learning_agent.tests.test_chrome_extension_installer_stage13`：22 tests OK。
- `python -m py_compile learning_agent\app\interactive.py learning_agent\app\chrome_status_renderer.py learning_agent\tests\test_chrome_extension_e2e_matrix_phase18.py`：退出码 0。
- `node --check learning_agent\chrome_extension\background.js`：退出码 0。
- `python -m unittest discover -s learning_agent\tests`：597 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 `/chrome extension-e2e-check`。
- 真实验收 run：`learning_agent/acceptance_controller/runs/agent_capability_phase18_chrome_extension_e2e-20260602_203303`。
- `result.json`：`completed=true`，`assertion.passed=true`，`chrome_status_printed=true`，`permission_sent_count=0`。
- 独立 verifier：`completed=true`，`assertion.passed=true`，截图、事件日志和 result artifact 全部存在。
- 最终截图确认终端输出包含 `manifest_ok=true`、`launcher_ok=true`、`pairing_completed=true`、`browser_prompt_queued=true`。

## 真实扩展边界

- 当前真实终端截图显示 `real_extension_connected=false`。
- 因此本次不能声称真实 Chrome extension UI 已经实际连接 native host。
- 本阶段已完成可审计 local protocol selftest，并把真实扩展连接状态显式暴露为门禁字段。
- 后续若用户在 Chrome 里加载扩展并完成 native host 连接，再次运行 `/chrome extension-e2e-check` 应显示 `real_extension_connected=true`，届时 `real_extension_e2e` 才可能为 true。

## 结论

- Phase 18 已完成代码修改、TDD、自动化测试、真实可见终端交互验收、独立 verifier 复验和学习备份。
- 当前机器真实扩展未连接这一事实已经被明确记录，不作为失败隐藏。
- 下一阶段进入 Phase 19：Browser Tool Routing 强化。
