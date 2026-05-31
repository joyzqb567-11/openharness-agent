# Stage 15 Event Runtime and Tool Executor v2 Plan Backup

记录日期：2026-05-31

备份来源：`agent_memory/stage15_event_runtime_plan.md`

## 目标

Stage 15 计划把 learning_agent 补齐五个核心短板：

1. 主循环事件流。
2. 工具协议。
3. 工具执行器。
4. 权限 hook。
5. 会话恢复。

## 总阶段数

建议分 8 个阶段完成。

| 阶段 | 名称 | 主要目标 |
|---|---|---|
| 15A | 事件类型和 transcript 基础 | 定义统一事件，写入 JSONL transcript。 |
| 15B | 流式模型接口 | 增加 `stream_chat()` 兼容层。 |
| 15C | 主循环事件流 | 新增 `run_events()`，旧 `run()` 保持兼容。 |
| 15D | 工具协议 v3 | 补齐工具安全、并发、权限和结果策略元数据。 |
| 15E | Tool Executor v2 和权限 hook | 建立执行前后 hook、权限决策和统一事件。 |
| 15F | 安全并发工具批处理 | 只让只读且并发安全的工具并行。 |
| 15G | 会话保存、恢复和最小 compact | 保存 session，支持 resume 和 compact summary。 |
| 15H | 集成验收和文档更新 | 跑完整测试、真实终端验收、更新文档。 |

## 最重要的执行原则

- 先新增 `run_events()`，不要直接破坏旧 `run()`。
- 先扩展工具元数据，不要直接做并发。
- 默认所有工具都不并发，只有明确只读且安全的工具可以并发。
- 权限 hook 先做最小版本，不要一开始做复杂插件系统。
- transcript 和 compact 不能删除原始证据。
- 涉及运行时代码后，最终必须做 `start_oauth_agent.bat` 真实可见终端交互验收。

## 推荐下一步

正式执行前，先创建 git 基线提交：

- `git status --short`
- `git add AGENTS.md agent_memory learning_agent memory.md`
- `git commit -m "chore: establish learning agent baseline"`

完整计划请读取：

- `agent_memory/stage15_event_runtime_plan.md`

