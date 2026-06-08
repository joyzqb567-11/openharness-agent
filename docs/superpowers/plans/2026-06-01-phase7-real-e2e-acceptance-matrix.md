# Phase 7：真实端到端验收矩阵书面计划

## 目标
- 把 Phase 1-6 的自动化测试、编译检查、学习备份和真实可见终端验收统一成一份可复查矩阵。
- 增加一个真实终端 `/chrome` 状态 UI 场景，证明新增终端命令能在 `start_oauth_agent.bat` 的可见窗口中运行。
- 保留最终门禁：没有真实可见终端截图和 `result.json` 通过，就不能声明开发完成。

## 范围
- 新增验收矩阵 JSON。
- 新增 `/chrome` 真实终端场景。
- 让 acceptance controller 支持“事件型命令验收”，即 `/chrome` 这类不会产生模型最终回答的终端命令。
- 增加自动化测试检查矩阵、场景和 controller 支持。

## 成功标准
- 矩阵覆盖 Phase 1-7。
- `/chrome` 场景要求 `agent_ready_for_user_prompt` 和 `chrome_status_printed`。
- controller 可以在无需 `final_answer_printed` 的情况下，基于必需事件直接完成验收。
- 自动化测试、py_compile 和真实可见终端 controller 验收通过。

## 验证
- `python -m unittest learning_agent.tests.test_agent_capability_acceptance_matrix_stage19`
- `python -m py_compile learning_agent\acceptance_controller\controller.ps1` 不适用于 PowerShell；改用自动化文本测试和真实 controller 运行。
- 真实可见终端：`powershell.exe -NoProfile -ExecutionPolicy Bypass -File learning_agent\acceptance_controller\controller.ps1 -ScenarioPath learning_agent\acceptance_controller\scenarios\agent_capability_completion_phase7_chrome_status.json`
