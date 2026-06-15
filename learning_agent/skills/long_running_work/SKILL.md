---
name: long_running_work
description: Use when reminders, monitors, recurring checks, or ongoing observation records are requested.
---

# Long Running Work

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

本 skill 只判断是否进入长期任务记录能力。需要细节时，再读取：

- `learning_agent/skills/long_running_work/rules/records.md`

边界：
- 先确认用户要的是提醒、监控、后台进程，还是仅记录后续检查点。
- 进程内记录不等于系统级定时任务或真实通知。
- 实际执行默认通过 `read / write / edit` 完成；命令执行需要先按需加载 execution 能力后再使用 bash 或运行时已接入的工具桥完成。
