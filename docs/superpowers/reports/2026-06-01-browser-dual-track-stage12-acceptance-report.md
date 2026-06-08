# Browser Dual Track Stage 12 Acceptance Report

日期：2026-06-01

## 结论

Stage 8 到 Stage 12 已按蓝图完成本轮闭环验收。当前 learning_agent 的真实浏览器双轨架构已经具备：

1. 可见 Chromium 公开网页轨道。
2. Real Chrome CDP 调试轨道。
3. Chrome extension provider 只读/权限/状态轨道。
4. 统一 `browser_*` 工具表面，由 router/provider 决策，不让模型直接在多套重复工具中选择。
5. `browser_tabs_context` 合同。
6. action executor、observation store、recording/GIF、replay、fallback/recovery。
7. browser runtime 到 harness run/stage/event/verifier 的同 id 投影。
8. CLI/API/SDK/status snapshot 可见 provider、tab、permission、run、action、observation、verifier。
9. `start_oauth_agent.bat` 真实可见终端验收通过。

## 自动化测试证据

- `python -m py_compile learning_agent\browser\harness_integration.py learning_agent\browser_automation_mcp_server.py learning_agent\runtime\status_snapshot.py learning_agent\tests\test_browser_harness_integration_stage11.py`：通过。
- `python -m unittest learning_agent.tests.test_browser_harness_integration_stage11`：Ran 2 tests，OK。
- Stage 8-11 相关回归：Ran 36 tests，OK。
- `python -m unittest discover -s learning_agent\tests`：Ran 546 tests，OK，skipped=1。

## 真实终端验收证据

### Stage 11 Harness 接入

- 场景：`learning_agent/acceptance_controller/scenarios/browser_harness_integration_stage11_acceptance.json`
- 运行目录：`learning_agent/acceptance_controller/runs/browser_harness_integration_stage11_acceptance-20260601_193242`
- controller：`ACCEPTANCE_CONTROLLER_COMPLETED=True`
- verifier：`completed=true`，`assertion.passed=true`
- 最终标记：`BROWSER_HARNESS_STAGE11_READY STAGE11_BROWSER_HARNESS_OK`

### Stage 12 真实可见浏览器总验收

- 场景：`learning_agent/acceptance_controller/scenarios/browser_dual_track_stage12_acceptance.json`
- 运行目录：`learning_agent/acceptance_controller/runs/browser_dual_track_stage12_acceptance-20260601_193735`
- controller：`ACCEPTANCE_CONTROLLER_COMPLETED=True`
- verifier：`completed=true`，`assertion.passed=true`
- 最终标记：`BROWSER_DUAL_TRACK_STAGE12_READY STAGE12_VISIBLE_BROWSER_OK`
- debug log 确认：
  - `mcp__browser_automation__browser_launch_visible`
  - `browser_launch_visible 成功`
  - `visible_browser=true`
  - `headless=false`
  - `mcp__browser_automation__browser_open`
  - `mcp__browser_automation__browser_snapshot`
  - `observation_id=`
  - `mcp__browser_automation__browser_screenshot`
  - `mcp__browser_automation__browser_flow_run`
  - `mcp__browser_automation__browser_plugin_status`
  - `observation_engine`
  - `flow_checkpoint`
  - `status_browser_runtime`
  - `browser_runtime_store=`
  - `compatible=true`

## 说明

旧的 `browser_visible_runtime_acceptance.json` 场景曾出现一次失败，原因是最终回答没有逐字复制长验收行；debug log 已证明浏览器动作实际完成。为避免把“最终回答格式问题”误判为“浏览器功能失败”，新增 Stage 12 专用场景，把真实浏览器动作交给 debug log 断言，把最终回答收敛为短标记。

## 剩余边界

本轮已完成双轨真实浏览器架构的核心闭环，但仍建议后续继续增强：

1. 更复杂的真实 Chrome extension 写动作端到端网站验收。
2. 更细的远程任务 UI/SDK 展示。
3. 多 provider 同页面切换时的互斥冻结策略。
4. 更完整的远程任务生态与队列 worker 调度。
