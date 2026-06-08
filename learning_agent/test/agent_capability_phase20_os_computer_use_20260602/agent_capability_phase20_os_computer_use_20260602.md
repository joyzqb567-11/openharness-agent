# Agent Capability Phase 20 OS Computer Use

## 范围

- 目标：让 OS 级 Computer Use 默认更安全、状态更可见、动作结果可审计。
- 边界：本阶段不启用真实鼠标键盘动作，除非显式设置 `LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE`。
- 验收 prompt：检查 computer use 状态，不要移动鼠标。

## 已实现

- 默认不可用后端会明确输出 `real_actions_enabled=false`、`opt_in_env_var=LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE` 和未设置原因。
- 内存测试后端会明确说明只记录动作，不控制真实桌面。
- `screenshot` 内存动作会返回 `evidence.kind=screenshot`，并说明没有读取真实屏幕。
- `ComputerUseController` 新增审计日志摘要，拒绝动作和成功动作都会携带 `audit_id`。
- 审计事件只保存动作类型、是否允许、原因、后端、坐标/文本长度元数据，不保存原始输入文本。
- 新增真实可见终端验收场景：`learning_agent/acceptance_controller/scenarios/agent_capability_phase20_os_computer_use.json`。

## 验证记录

- 红灯：`python -m unittest learning_agent.tests.test_os_computer_use_phase20` 初次失败，确认缺少 `real_actions_enabled`、`audit_id` 和 `evidence`。
- 聚焦测试：`python -m unittest learning_agent.tests.test_os_computer_use_phase20 learning_agent.tests.test_os_computer_use_stage17` 通过，7 tests OK。
- 语法检查：`python -m py_compile learning_agent\computer_use\controller.py learning_agent\tests\test_os_computer_use_phase20.py` 通过。
- 场景 JSON：`python -m json.tool learning_agent\acceptance_controller\scenarios\agent_capability_phase20_os_computer_use.json > $null` 通过。
- 相关回归：`python -m unittest learning_agent.tests.test_os_computer_use_phase20 learning_agent.tests.test_os_computer_use_stage17 learning_agent.tests.test_streaming_tool_executor_stage16 learning_agent.tests.test_tool_executor_v2 learning_agent.tests.test_tool_protocol learning_agent.tests.test_tools_policy` 通过，99 tests OK。
- 全量测试：`python -m unittest discover -s learning_agent\tests` 通过，603 tests OK，skipped=1。
- 真实可见终端验收：controller 启动 `learning_agent/start_oauth_agent.bat`，run 为 `learning_agent/acceptance_controller/runs/agent_capability_phase20_os_computer_use-20260602_205824`。
- 验收结果：`result.json completed=true`、`assertion.passed=true`、`permission_sent_count=0`，debug/event 均包含 `PHASE20_COMPUTER_STATUS_OK`、`real_actions_enabled=false`、`opt_in_env_var=LEARNING_AGENT_ENABLE_WINDOWS_COMPUTER_USE`、`audit_count=0`。
- 独立 verifier：`python -m learning_agent.acceptance.verifier learning_agent\acceptance_controller\runs\agent_capability_phase20_os_computer_use-20260602_205824 learning_agent\acceptance_controller\scenarios\agent_capability_phase20_os_computer_use.json` 通过。
- 截图确认：`03_final.png` 显示真实 Windows 终端中输出 Phase 20 状态验收成功标记。
- 学习备份：`learning_agent/test/agent_capability_phase20_os_computer_use_20260602/`。
