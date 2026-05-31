---
name: file_operations
description: Use when workspace files need to be inspected, created, overwritten, or edited.
---

# File Operations

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

本 skill 只判断是否进入文件操作能力。需要细节时，再读取：

- `learning_agent/skills/file_operations/rules/text_edits.md`

边界：
- 修改前先读取相关文件。
- 小范围修改优先 `edit`，全量创建或覆盖才用 `write`。
- 不要声称已读写文件，除非对应工具结果已经确认。
