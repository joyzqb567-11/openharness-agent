# Task 6 Planning Panel Visible GUI Acceptance

日期：2026-06-27

工作树：`H:\codexworkplace\sofeware\OpenHarness-main\.worktrees\gui-toolchain-control-center`

## 自动化门禁

- `python -m unittest learning_agent.tests.test_gui_planning_panel_contract -v`：通过，2 tests。
- `npm --prefix apps/desktop run test -- planningPanel guiClient`：通过，20 tests。
- `npm --prefix apps/desktop run lint`：通过。
- `npm --prefix apps/desktop run build`：通过。

## 直接接口验收

请求：`GET http://127.0.0.1:8776/v2/gui/planning`

Header：`X-OpenHarness-Desktop-Token: openharness-desktop-dev-token`

结果摘要：

- `ok=True`
- `schema_version=2`
- `todo_count=0`
- `task_count=0`
- `active_task_count=0`
- `peer_count=0`
- `pending_peer_message_count=0`
- `tool_count=18`
- `available_tool_count=18`
- `status_degraded=False`
- `safe_error=""`

## Computer Use 真实 GUI 验收

使用 `computer-use` 读取并点击真实 `OpenHarness Desktop` 窗口右侧 `计划` 页签。

肉眼可见结果：

- 右侧页签出现 `计划协作` 面板。
- 顶部显示 `18/18 tools`。
- 摘要显示 `0 todos`、`0 active tasks`、`0 peers`、`0 pending messages`。
- `Todos` 区显示 `暂无 todo 数据。`
- `Tasks` 区显示 `暂无任务数据。`
- `Teams` 区显示 `暂无团队数据。`
- `Peer Messages` 区显示 `暂无消息数据。`
- `Tools` 区显示 `18`，并可见 `todo_read`、`todo_write`、`enter_plan_mode`、`exit_plan_mode`、`verify_plan_execution`、`task` 等工具条目。

截图：

![Planning Panel Visible GUI](H:/codexworkplace/sofeware/OpenHarness-main/.worktrees/gui-toolchain-control-center/learning_agent/test/gui_planning_panel_task6/planning_panel_visible_gui_20260627.png)

结论：Task 6 Planning/Todo/Subagent/Team 只读 GUI 接入通过真实 GUI 验收。
