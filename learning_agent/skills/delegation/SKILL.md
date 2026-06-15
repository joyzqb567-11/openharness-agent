---
name: delegation
description: Use when work can be split into bounded sub-agent tasks or teaching peer records.
---

# Delegation

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

本 skill 只判断是否需要委派或记录多 agent 教学流程。需要细节时，再读取：

- `learning_agent/skills/delegation/rules/task_lifecycle.md`

边界：
- 子任务必须有清楚目标、输入、输出和停止条件。
- 不要为了简单顺手工作启动子 agent。
- 实际执行默认通过 `read / write / edit` 完成；命令执行需要先按需加载 execution 能力后再使用 bash 或运行时已接入的工具桥完成。
