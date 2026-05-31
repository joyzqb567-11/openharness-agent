# Prompt Surface Rule

使用场景：
- 用户询问模型每轮看到什么、为什么上下文大、提示词如何加载、工具 schema 如何影响预算。

规则：
- 每轮常驻入口是 `staticprompt/staticprompt.md`、`memory.md` 索引和用户输入。
- 动态入口是 `dynamicprompt/dynamicprompt.md`、`learning_agent/skills/tool_list.md`、`skills/*/SKILL.md` 和 `skills/*/rules/*.md`。
- 读取第三层子规则前，应先读取总索引和父 SKILL。
- prompt_surface_report 可用于审计已加载 prompt blocks。
- token_budget_report 可用于审计 prompt、tool schema 和上下文预算。
- 设计目标是极简提示词、按需加载和证据边界清楚。

关键词：Prompt Surface Architecture v2、Prompt Architecture v1、Prompt Registry、Context Assembler、prompt_surface_report、token_budget_report、dynamicprompt.md、staticprompt.md、三层动态规则树。
