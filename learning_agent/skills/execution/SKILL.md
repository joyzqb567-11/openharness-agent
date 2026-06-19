---
name: execution
description: Use when commands, tests, dev servers, or long-running process checks are needed.
---

# Execution

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

本 skill 只判断是否进入命令执行能力。需要细节时，再读取：

- `learning_agent/skills/execution/rules/background_commands.md`

边界：
- 执行命令前核对工作目录、命令副作用和超时。
- 长命令优先设计为可观察、可停止。
- 实际执行默认通过 `read / write / edit / bash / tool_search` 完成；后台命令生命周期等更高级执行能力需要按需加载 execution 能力或运行时已接入的工具桥完成。
