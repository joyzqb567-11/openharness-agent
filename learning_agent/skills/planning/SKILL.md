---
name: planning
description: Use when multi-step, risky, public-interface, or long-running work needs explicit planning and verification.
---

# Planning

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

本 skill 只判断是否进入计划能力。需要细节时，再读取：

- `learning_agent/skills/planning/rules/planning_workflow.md`

边界：
- 多文件、运行时逻辑、公开接口或高风险改动先列成功标准和验证方式。
- 计划不是拖延；它要帮助缩小范围和减少返工。
- 实际执行默认通过 `read / write / edit` 完成；命令执行需要先按需加载 execution 能力后再使用 bash 或运行时已接入的工具桥完成。
