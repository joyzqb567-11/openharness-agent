# Agent Capability Phase 21 Terminal Status UI

## 范围

- 目标：让 `/status` 和 `/chrome` 更像成熟 coding agent 的终端状态面板。
- 重点：第一屏可读、紧凑摘要、下一步命令、最近问题。
- 边界：不新增危险动作，不把实现细节堆进 UI。

## 已实现

- `/status` 新增 `Status Summary` 区块：
  - `connection=...` 汇总 native host、Chrome extension、paired 和 health。
  - `next=...` 给出首选下一步命令。
  - `recent_error=...` 把最近健康警告或错误事件提升到第一屏。
- `/chrome` 新增 `Chrome Summary` 区块：
  - `connection=...` 汇总 native host、extension、paired 和 pending commands。
  - `next=...` 根据当前 Chrome 状态生成具体命令。
  - `recent_issue=...` 汇总 provider 不可用原因或最近浏览器错误事件。
- 保留原有详细状态区块，避免破坏既有调试信息。
- 新增测试：`learning_agent/tests/test_terminal_status_ui_phase21.py`。
- 新增真实终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase21_terminal_status_ui.json`。

## 当前验证记录

- 红灯：初次运行 `python -m unittest learning_agent.tests.test_terminal_status_ui_phase21` 失败，确认旧 UI 缺少 `Status Summary` 和 `Chrome Summary`。
- 聚焦测试：`python -m unittest learning_agent.tests.test_terminal_status_ui_phase21` 通过，2 tests OK。
- 语法检查：`python -m py_compile learning_agent\app\status_renderer.py learning_agent\app\chrome_status_renderer.py learning_agent\tests\test_terminal_status_ui_phase21.py` 通过。
- 场景 JSON：`python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_phase21_terminal_status_ui.json > $null` 通过。
- 相关回归：`python -m unittest learning_agent.tests.test_terminal_status_ui_phase21 learning_agent.tests.test_compact_resume_status_ecosystem learning_agent.tests.test_status_ecosystem_deep_alignment learning_agent.tests.test_chrome_terminal_status_ui_stage18 learning_agent.tests.test_chrome_terminal_subcommands_phase9` 通过，26 tests OK。
- 全量测试：`python -m unittest discover -s learning_agent\tests` 通过，605 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，run 为 `learning_agent/acceptance_controller/runs/agent_capability_phase21_terminal_status_ui-20260602_210605`。
- 验收结果：`result.json completed=true`、`assertion.passed=true`、`permission_sent_count=0`，debug/event 均包含 `PHASE21_STATUS_UI_OK`、`status_summary=true`、`chrome_summary=true`、`next=/chrome_pairing_diagnose`、`max_line_ok=true`。
- 独立 verifier：`python -m learning_agent.acceptance.verifier learning_agent\acceptance_controller\runs\agent_capability_phase21_terminal_status_ui-20260602_210605 learning_agent\acceptance_controller\scenarios\agent_capability_phase21_terminal_status_ui.json` 通过。
- 截图确认：`03_final.png` 显示真实 Windows 终端中输出 Phase 21 状态 UI 验收成功标记。
- 学习备份：`learning_agent/test/agent_capability_phase21_terminal_status_ui_20260602/`。
