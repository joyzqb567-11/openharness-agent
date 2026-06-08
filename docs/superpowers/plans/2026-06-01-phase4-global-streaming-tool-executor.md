# Phase 4 全局 StreamingToolExecutor 计划

## 目标

新增一个全局工具执行器，让普通内置工具、MCP 工具、浏览器工具都能通过同一套 started/chunk/completed/failed 事件语义执行。现有并发 orchestrator 继续决定串行/并发，具体单工具执行交给 StreamingToolExecutor 包裹。

## 成功标准

1. 新增 `learning_agent/tools/streaming_executor.py`。
2. 普通字符串结果生成 started/completed 事件。
3. generator/list 等分段结果生成 result_chunk 事件并拼接最终文本。
4. 异常生成 failed 事件并返回可读失败文本，不中断整批工具。
5. `tools/orchestrator.py` 使用全局 executor 执行每个工具。
6. 自动化测试覆盖直接 executor 和 orchestrator 集成。

## 实施步骤

1. 新增红灯测试 `learning_agent/tests/test_streaming_tool_executor_stage16.py`。
2. 实现 `ToolExecutionEvent`、`StreamingToolExecutor`、`execute_tool_call_with_streaming()`。
3. 修改 `tools/orchestrator.py` 的单工具执行路径，统一接入 streaming executor。
4. 复制新增/修改文件到 `learning_agent/test/agent_capability_completion_20260601/phase4/`。
5. 运行 Phase 4 测试、工具编排回归和语法检查。

## 边界

本阶段只统一执行事件和分段结果，不改变工具权限策略、不改变模型 streaming、不新增后台长期 listener。
