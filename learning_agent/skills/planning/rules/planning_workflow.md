# Planning Workflow Rule

使用场景：
- 多步骤任务、多文件改动、公开接口、运行时逻辑、高风险操作或跨轮工作。

规则：
- 先写成功标准、范围边界、停止条件和验证方式。
- 已有任务清单先 todo_read，再 todo_write 写回完整更新列表。
- 需要用户确认计划时先进入计划模式，确认后再执行副作用。
- 执行后用 verify_plan_execution 或等价检查对照计划。
- 大范围改动需要隔离状态时记录 enter_worktree 和 exit_worktree。

关键词：todo_read、todo_write、任务清单、enter_plan_mode、exit_plan_mode、verify_plan_execution、enter_worktree、exit_worktree、计划模式、工作区隔离。
