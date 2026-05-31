---
name: prompt_architecture
description: Use when prompt surface, token budget, context assembly, static prompts, or dynamic prompt layering are being inspected.
---

# Prompt Architecture

入口顺序：先 read `learning_agent/skills/tool_list.md`，再 read 本文件。

本 skill 只判断是否进入提示词架构分析。需要细节时，再读取：

- `learning_agent/skills/prompt_architecture/rules/prompt_surface.md`

边界：
- `staticprompt/staticprompt.md` 是每轮常驻入口。
- `dynamicprompt/dynamicprompt.md` 和 `skills/*/rules/*.md` 是按需入口。
- 目标是减少 token、保持注意力稳定，并保留可审计边界。
