# current_tool_pool 删除迁移记录

## 目标

- 用户要求删除旧名字 `current_tool_pool()`，只保留和 ClaudeCode 更容易对照的 `filteredTools()`。
- 目标不是改变工具过滤行为，而是减少同一功能两个名字造成的小白理解负担。

## CodeGraph 审计结论

- `codegraph callers current_tool_pool --limit 80` 返回：`No callers found for "current_tool_pool"`。
- 这说明 active 生产代码里，`current_tool_pool` 没有外部调用者；剩余主要是兼容包装定义和测试引用。

## 需要删除或替换的 active 位置

- `learning_agent/tools/pool.py`：删除 `current_tool_pool(catalog, decision_for_tool)` 兼容包装，只保留 `filteredTools(catalog, decision_for_tool)`。
- `learning_agent/tools/catalog_runtime.py`：删除 `current_tool_pool(agent)` 兼容包装，只保留 `filteredTools(agent)`。
- `learning_agent/tests/test_filtered_tools_naming.py`：把“旧入口兼容”断言改成“旧入口已经消失，新入口是唯一当前工具过滤入口”。
- `learning_agent/tests/test_tools_policy.py`：把 `current_tool_pool` 的测试导入和调用改成 `filteredTools`。
- `learning_agent/acceptance_controller/scenarios/agent_capability_filtered_tools_entry_visible_terminal.json`：把验收要求从“旧入口兼容存在”改成“旧入口已删除，只保留 filteredTools”。
- `agent_memory/context.md`、`agent_memory/progress.md`、`agent_memory/bugs.md`：记录本轮删除旧名的原因、验证和风险边界。

## 不作为 active 调用处理的位置

- `learning_agent/test/**` 下的历史学习备份和验收日志保留原样；这些文件是历史证据，不是当前生产链路。
- `agent_memory/archive/**` 下的旧归档保留原样；这些文件用于追溯历史，不参与运行。
- 本轮完成后会新建新的学习备份目录，保存删除旧名字后的源码、测试、场景和验收结果。

## 替换规则

- 所有 active 生产路径只使用 `filteredTools`。
- 不再提供 `current_tool_pool` 兼容包装。
- 验证方式以 active 路径为准：`learning_agent/tools/**`、`learning_agent/tests/**`、`learning_agent/acceptance_controller/scenarios/**`、`agent_memory/**`。

## 成功标准

- `learning_agent.tools.pool` 不再公开 `current_tool_pool`。
- `learning_agent.tools.catalog_runtime` 不再公开 `current_tool_pool`。
- `filteredTools` 行为保持不变：只返回策略决策中 `visible=True` 的工具。
- 首轮工具面仍为 `read,write,edit,bash,tool_search`。
- 真实可见终端验收必须确认旧名已删除、新名可用。
