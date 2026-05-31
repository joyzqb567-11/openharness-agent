---
name: diagnostics
description: Use when code understanding, symbol lookup, diagnostics, or safe read-only checks are needed.
---

# Diagnostics

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

本 skill 只判断是否进入诊断能力。需要细节时，再读取：

- `learning_agent/skills/diagnostics/rules/code_diagnostics.md`

边界：
- 先用 `read` 和 `bash` 的搜索命令确认事实，再下结论。
- 诊断只证明原因，不自动扩大修改范围。
- 实际执行仍通过 `read / write / edit / bash` 以及运行时已接入的工具桥完成。
