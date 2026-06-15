---
name: memory
description: Use when stable user preferences or long-term agent facts should affect future runs.
---

# Memory

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

本 skill 只判断是否应该写入长期记忆。需要细节时，再读取：

- `learning_agent/skills/memory/rules/stable_memory.md`

边界：
- 目标 agent 默认只关联 `memory.md`，不关联 Codex 开发用 `agent_memory` 三件套。
- 不保存秘密、临时过程、未确认猜测或一次性任务细节。
- 实际执行默认通过 `read / write / edit` 完成；命令执行需要先按需加载 execution 能力后再使用 bash 或运行时已接入的工具桥完成。
