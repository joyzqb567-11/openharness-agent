# 2026-06-02 Agent Capability Phase 14 Chrome Pairing Diagnose

## 目标

- 新增 `/chrome pairing-diagnose`，让用户在看到 `paired=false` 时能知道是 native host 未安装、bridge 文件缺失、extension 未连接，还是 session 字段缺失。
- 该命令必须只读，不写 Windows registry，不写 bridge 文件，不触发真实浏览器动作。

## 成功标准

- `/chrome pairing-diagnose` 输出 `pairing_diagnose`。
- 输出 `bridge_file_exists`、`connected`、`paired`、`extension_id`、`device_id`、`session_id`、`allowed_origin_count`、`last_seen_at`。
- 输出 `reason=...` 原因分类和 `next=...` 下一步建议。
- 自动化测试、py_compile、真实可见终端验收和独立 verifier 均通过后，Phase 14 才能关闭。

## 当前证据

- 已新增聚焦测试：`learning_agent/tests/test_chrome_pairing_diagnose_phase14.py`。
- 已实现终端入口：`learning_agent/app/interactive.py` 中的 `/chrome pairing-diagnose`。
- 已新增真实终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase14_chrome_pairing_diagnose.json`。

## 风险边界

- Phase 14 只解释配对状态，不负责触发配对；配对触发链路放到 Phase 15。
- 本机若没有真实 extension 配对，验收允许显示 `paired=false`，但必须能说明原因和下一步。

## 验证结果

- `python -m unittest learning_agent.tests.test_chrome_pairing_diagnose_phase14`：2 tests OK。
- `python -m unittest learning_agent.tests.test_chrome_pairing_diagnose_phase14 learning_agent.tests.test_chrome_terminal_subcommands_phase9 learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_status_snapshot_phase12`：18 tests OK。
- `python -m py_compile learning_agent\app\interactive.py learning_agent\tests\test_chrome_pairing_diagnose_phase14.py`：退出码 0。
- `python -m unittest discover -s learning_agent\tests`：587 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，输入 `/chrome pairing-diagnose`。
- 真实验收 run：`learning_agent/acceptance_controller/runs/agent_capability_phase14_chrome_pairing_diagnose-20260602_200019`。
- `result.json`：`completed=true`，`assertion.passed=true`，`chrome_status_printed=true`，`permission_sent_count=0`。
- 独立 verifier：`completed=true`，`assertion.passed=true`，截图和事件日志 artifact 均存在。
- 截图确认终端输出包含 `pairing_diagnose`、`paired=false`、`reason=bridge_file_missing`、`reason=device_id_missing`、`reason=session_id_missing`、`reason=allowed_origins_empty`、`next=/chrome install-confirm <extension_id> I_UNDERSTAND_WRITE_REGISTRY`。

## 结论

- Phase 14 已完成代码修改、自动化测试、真实可见终端交互验收和学习备份。
- 下一阶段进入 Phase 15：Chrome extension 配对触发链路。
