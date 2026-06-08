# Agent Capability Phase 22 Browser Harness Fusion

## 范围

- 目标：把浏览器任务和长任务 harness 更紧密融合，形成可恢复、可验收、可见的证据链。
- 重点：browser action 级证据进入 harness；重复同步不制造重复事件；`/status` 和 `/chrome` 能直接显示 harness 链接。
- 边界：本阶段不改变真实浏览器执行语义，不引入新的真实网页操作。

## 已实现

- `BrowserHarnessMirror.append_action_evidence()`：
  - 把 `BrowserAction` 映射为 `browser_action_evidence` harness event。
  - 按 `action_id` 去重，避免 resume/retry 重复展示已完成动作。
  - 只保留 verifier 友好的短字段：`action_id`、`stage_id`、`tool_name`、`status`、`observation_id`。
- `BrowserAutomationServer`：
  - 在真实 action 结束回调中调用 `append_action_evidence()`，让生产工具执行也进入 harness 证据链。
- `build_status_snapshot()`：
  - 在 `browser.runs[*].harness` 中增加 `action_evidence_count` 和 `latest_action_evidence`。
- `/status`：
  - `Browser Runtime` 区块新增 `harness_run_id`、`harness_verifier_passed`、`harness_action_evidence_count`、`harness_latest_action`。
- `/chrome`：
  - 最近 browser run 存在 harness 投影时显示同样的 harness/action 证据链接。
- 新增测试：`learning_agent/tests/test_browser_harness_fusion_phase22.py`。
- 新增真实终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase22_browser_harness_fusion.json`。

## 当前验证记录

- 红灯：初次运行 `python -m unittest learning_agent.tests.test_browser_harness_fusion_phase22` 失败，确认 `BrowserHarnessMirror` 缺少 `append_action_evidence()`。
- 聚焦测试：`python -m unittest learning_agent.tests.test_browser_harness_fusion_phase22` 通过，1 test OK。
- 语法检查：`python -m py_compile learning_agent\browser\harness_integration.py learning_agent\browser_automation_mcp_server.py learning_agent\runtime\status_snapshot.py learning_agent\app\status_renderer.py learning_agent\app\chrome_status_renderer.py learning_agent\tests\test_browser_harness_fusion_phase22.py` 通过。
- 场景 JSON：`python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_phase22_browser_harness_fusion.json > $null` 通过。
- 相关回归：`python -m unittest learning_agent.tests.test_browser_harness_fusion_phase22 learning_agent.tests.test_browser_harness_integration_stage11 learning_agent.tests.test_browser_action_executor learning_agent.tests.test_browser_status_ecosystem learning_agent.tests.test_terminal_status_ui_phase21` 通过，16 tests OK。
- 全量测试：`python -m unittest discover -s learning_agent\tests` 通过，606 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，run 为 `learning_agent/acceptance_controller/runs/agent_capability_phase22_browser_harness_fusion-20260602_211420`。
- 验收结果：`result.json completed=true`、`assertion.passed=true`、`permission_sent_count=0`，debug/event 均包含 `PHASE22_BROWSER_HARNESS_OK`、`harness_run_id=phase22_visible_browser_run`、`verifier_passed=true`、`action_evidence_count=1`、`dedupe_ok=true`。
- 独立 verifier：`python -m learning_agent.acceptance.verifier learning_agent\acceptance_controller\runs\agent_capability_phase22_browser_harness_fusion-20260602_211420 learning_agent\acceptance_controller\scenarios\agent_capability_phase22_browser_harness_fusion.json` 通过。
- 截图确认：`03_final.png` 显示真实 Windows 终端中输出 Phase 22 浏览器 harness 融合成功标记。
- 学习备份：`learning_agent/test/agent_capability_phase22_browser_harness_fusion_20260602/`。
